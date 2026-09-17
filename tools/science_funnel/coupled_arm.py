"""Analytic SI multibody reference for admitted ordered anatomical transforms.

Returns force ingredients, not a time integrator. No contact, muscle actuation,
free root, empirical validation or GPU claim follows from these arrays.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from .common import canonical, require
from .macaque_anatomy import ROOT, parse_source, pose_frames, frame, rotation
from tools.creature_graph.store import CreatureGraph


def skew(v):
    x, y, z = v
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def axial(a):
    return np.array([a[2, 1]-a[1, 2], a[0, 2]-a[2, 0], a[1, 0]-a[0, 1]])/2


def fixed(t, n):
    return (t, np.zeros((n, 4, 4)), np.zeros((4, 4)), np.zeros((4, 4)))


def product(a, b):
    # T, all coordinate derivatives, time derivative, second time derivative.
    return (a[0]@b[0], a[1]@b[0]+a[0]@b[1],
            a[2]@b[0]+a[0]@b[2], a[3]@b[0]+2*a[2]@b[2]+a[0]@b[3])


class Assembly:
    def __init__(self, model, values=None, rates=None, gravity=(0., -9.81, 0.)):
        pose_frames(model, values)  # Existing strict range/hierarchy/lock contract.
        self.coordinates = sorted(k for k, v in model['coordinates'].items() if not v['locked'])
        slots = {k: i for i, k in enumerate(self.coordinates)}
        self.n = n = len(slots)
        require(n > 0, 'no_dynamic_coordinates')
        rates = rates or {}
        require(set(rates) <= set(slots), 'unknown_or_locked_rate')
        self.velocity = np.array([float(rates.get(k, 0.)) for k in self.coordinates])
        self.gravity = np.asarray(gravity, dtype=float)
        require(np.isfinite(self.velocity).all() and self.gravity.shape == (3,) and np.isfinite(self.gravity).all(), 'nonfinite_dynamics_input')
        values = values or {}
        q = {k: float(values.get(k, v['default_rad'])) for k, v in model['coordinates'].items()}
        bodies = {b['name']: b for b in model['bodies']}
        self.frames = {'ground': fixed(np.eye(4), n)}
        pending = set(bodies)-{'ground'}
        while pending:
            ready = [k for k in sorted(pending) if bodies[k]['joint']['parent'] in self.frames]
            require(ready, 'cyclic_body_hierarchy')
            for name in ready:
                j = bodies[name]['joint']; motion = fixed(np.eye(4), n)
                translation = np.zeros(3); jt = np.zeros((n, 3)); vt = np.zeros(3)
                for ax in j['axes']:
                    f = ax['function']; coef = f['coefficients']; coord = ax['coordinate']
                    require(f['type'] in ('Constant', 'LinearFunction'), 'unsupported_transform_function')
                    slope = 0. if f['type'] == 'Constant' else coef[0]
                    value = coef[0] if f['type'] == 'Constant' else slope*q[coord]+coef[1]
                    index = slots.get(coord); rate = 0. if index is None else slope*self.velocity[index]
                    axis = np.asarray(ax['axis'], dtype=float)
                    if ax['name'].startswith('rotation'):
                        t = np.eye(4); t[:3, :3] = rotation(axis, value)
                        d = np.zeros((n, 4, 4)); td = np.zeros((4, 4)); tdd = td.copy()
                        dr = skew(axis)@t[:3, :3]
                        if index is not None: d[index, :3, :3] = slope*dr
                        td[:3, :3] = rate*dr; tdd[:3, :3] = rate*rate*skew(axis)@dr
                        motion = product(motion, (t, d, td, tdd))
                    elif ax['name'].startswith('translation'):
                        translation += axis*value; vt += axis*rate
                        if index is not None: jt[index] += axis*slope
                    else:
                        require(False, 'unsupported_transform_axis')
                # Source translation axes are in the parent joint frame, not the rotated body frame.
                motion[0][:3, 3] = translation; motion[1][:, :3, 3] = jt; motion[2][:3, 3] = vt
                parent = frame(j['parent_location_m'], j['parent_orientation_rad'])
                child = np.linalg.inv(frame(j['child_location_m'], j['child_orientation_rad']))
                self.frames[name] = product(product(product(self.frames[j['parent']], fixed(parent, n)), motion), fixed(child, n))
                pending.remove(name)
        self.mass_matrix = np.zeros((n, n)); self.gravity_force = np.zeros(n)
        self.bias_force = np.zeros(n); self.potential_J = 0.
        for body in model['bodies']:
            name = body['name']; m = float(body['mass_kg'])
            xx, yy, zz, xy, xz, yz = body['inertia_kg_m2']
            ic = np.array([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]], dtype=float)
            require(np.isfinite(m) and m >= 0 and np.isfinite(ic).all(), 'invalid_body_inertia')
            eigen = np.linalg.eigvalsh(ic)
            require(eigen[0] >= -1e-14 and eigen[-1] <= sum(eigen[:-1])+1e-14 and (m > 0 or not np.any(ic)), 'nonphysical_body_inertia')
            t, d, td, tdd = self.frames[name]; r = t[:3, :3]; iw = r@ic@r.T
            position, jv = self.point(name, body['mass_center_m'])
            jw = np.array([axial(di[:3, :3]@r.T) for di in d]).T
            omega = axial(td[:3, :3]@r.T)
            alpha = axial(tdd[:3, :3]@r.T + td[:3, :3]@td[:3, :3].T)
            acceleration = (tdd@np.r_[body['mass_center_m'], 1.])[:3]
            self.mass_matrix += m*jv.T@jv + jw.T@iw@jw
            self.gravity_force += jv.T@(m*self.gravity)
            self.bias_force += jv.T@(m*acceleration) + jw.T@(iw@alpha + np.cross(omega, iw@omega))
            self.potential_J -= m*np.dot(self.gravity, position)
        require(np.isfinite(self.mass_matrix).all() and np.isfinite(self.bias_force).all() and np.isfinite(self.gravity_force).all() and np.isfinite(self.potential_J), 'nonfinite_assembly')

    def point(self, body, local_m):
        require(body in self.frames, 'unknown_attachment_body')
        p = np.asarray(local_m, dtype=float)
        require(p.shape == (3,) and np.isfinite(p).all(), 'invalid_attachment_point')
        t, d, _, _ = self.frames[body]; homogeneous = np.r_[p, 1.]
        return (t@homogeneous)[:3], (d@homogeneous)[:, :3].T

    def point_force(self, body, local_m, force_N):
        f = np.asarray(force_N, dtype=float)
        require(f.shape == (3,) and np.isfinite(f).all(), 'invalid_point_force')
        return self.point(body, local_m)[1].T@f

    def acceleration(self, torque_N_m):
        tau = np.asarray(torque_N_m, dtype=float)
        require(tau.shape == (self.n,) and np.isfinite(tau).all(), 'invalid_generalized_force')
        eigen = np.linalg.eigvalsh(self.mass_matrix)
        require(eigen[0] > 0 and eigen[-1]/eigen[0] < 1e12, 'singular_or_ill_conditioned_mass_matrix')
        return np.linalg.solve(self.mass_matrix, tau+self.gravity_force-self.bias_force)

    def record(self):
        return {'schema': 'chimera.coupled_arm_reference.v1', 'coordinate_order': self.coordinates,
                'units': {'q': 'rad', 'rate': 'rad/s', 'mass_matrix': 'kg m^2', 'generalized_force': 'N m'},
                'mass_matrix': self.mass_matrix.tolist(), 'gravity_force_N_m': self.gravity_force.tolist(),
                'bias_force_N_m': self.bias_force.tolist(), 'potential_J': self.potential_J,
                'velocity_rad_s': self.velocity.tolist(), 'gravity_m_s2': self.gravity.tolist(),
                'mass_eigenvalues_kg_m2': np.linalg.eigvalsh(self.mass_matrix).tolist(),
                'scope': 'Offline force ingredients for a fixed-root assembly; no time integration, contact, actuation or GPU qualification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'.tmp/coupled-arm/reference.json')
    args = parser.parse_args(); graph = CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
    model = graph.get('model.anatomy.macaque_arm')['physical']['model']
    require(model == parse_source()[0], 'coupled_arm_source_model_drift')
    result = Assembly(model, gravity=model["gravity_m_s2"]).record(); result.update(graph_hash=graph.graph_hash(), source_revision=model['source_revision'])
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_bytes(canonical(result))
    print(json.dumps({'output': str(args.output), 'coordinates': len(result['coordinate_order']), 'mass_eigenvalues_kg_m2': result['mass_eigenvalues_kg_m2']}))


if __name__ == '__main__':
    main()
