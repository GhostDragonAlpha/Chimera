import copy
import unittest
import numpy as np
from tools.science_funnel.coupled_arm import Assembly
from tools.science_funnel.macaque_anatomy import parse_source, pose_frames
from tools.science_funnel.common import Refusal


def planar_model():
    def body(name, mass, com, inertia, parent=None, origin=(0., 0., 0.), coordinate=None):
        joint = None if parent is None else {'parent': parent, 'parent_location_m': list(origin), 'parent_orientation_rad': [0., 0., 0.], 'child_location_m': [0., 0., 0.], 'child_orientation_rad': [0., 0., 0.], 'axes': [{'name': 'rotation1', 'axis': [0., 0., 1.], 'coordinate': coordinate, 'function': {'type': 'LinearFunction', 'coefficients': [1., 0.]}}]}
        return {'name': name, 'mass_kg': mass, 'mass_center_m': [com, 0., 0.], 'inertia_kg_m2': [inertia, inertia, inertia, 0., 0., 0.], 'joint': joint}
    return {'coordinates': {k: {'default_rad': v, 'range_rad': [-3., 3.], 'locked': False} for k, v in [('a', .3), ('b', -.6)]}, 'bodies': [body('ground', 0., 0., 0.), body('upper', 2., .35, .11, 'ground', coordinate='a'), body('lower', 1.5, .25, .05, 'upper', (.7, 0., 0.), 'b')]}


class CoupledArm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = parse_source()[0]
        rng = np.random.default_rng(283)
        cls.cases = []
        for _ in range(6):
            q = {k: c['range_rad'][0]+rng.uniform(.15, .85)*np.ptp(c['range_rad']) for k, c in cls.model['coordinates'].items()}
            rates = {k: rng.uniform(-1., 1.) for k in q}
            cls.cases.append((q, rates))

    def test_closed_form_two_link_inertia_gravity_bias(self):
        a = Assembly(planar_model(), rates={'a': .8, 'b': -.4})
        q1, q2, v1, v2 = .3, -.6, .8, -.4
        cross = 1.5*.7*.25*np.cos(q2)
        m22 = .05+1.5*.25**2
        expected = [[.11+2*.35**2+1.5*.7**2+m22+2*cross, m22+cross], [m22+cross, m22]]
        np.testing.assert_allclose(a.mass_matrix, expected, rtol=2e-14, atol=1e-15)
        h = 1.5*.7*.25*np.sin(q2)
        np.testing.assert_allclose(a.bias_force, [-h*(2*v1*v2+v2*v2), h*v1*v1], atol=2e-16)
        gravity = -9.81*np.array([(2*.35+1.5*.7)*np.cos(q1)+1.5*.25*np.cos(q1+q2), 1.5*.25*np.cos(q1+q2)])
        np.testing.assert_allclose(a.gravity_force, gravity, atol=4e-15)
        np.testing.assert_allclose(a.mass_matrix@a.acceleration([.1, -.2])+a.bias_force-a.gravity_force, [.1, -.2], atol=4e-15)

    def test_coupling_changes_other_coordinate_acceleration(self):
        a = Assembly(planar_model(), gravity=[0., 0., 0.])
        accel = a.acceleration([1., 0.])
        self.assertGreater(accel[0], 0.)
        self.assertLess(accel[1], 0.)
        self.assertGreater(abs(a.mass_matrix[0, 1]), .1)

    def test_source_frames_and_energy_against_independent_FK_differences(self):
        eps = 2e-6
        for q, rates in self.cases:
            a = Assembly(self.model, q, rates)
            frames = pose_frames(self.model, q)
            plus = pose_frames(self.model, {k: v+eps*rates[k] for k, v in q.items()})
            minus = pose_frames(self.model, {k: v-eps*rates[k] for k, v in q.items()})
            energy = 0.
            for b in self.model['bodies']:
                name = b['name']; t = frames[name]; derivative = (plus[name]-minus[name])/(2*eps)
                np.testing.assert_allclose(a.frames[name][0], t, atol=4e-16)
                speed = (derivative@np.r_[b['mass_center_m'], 1.])[:3]
                w = t[:3, :3].T@derivative[:3, :3]; omega = np.array([w[2, 1], w[0, 2], w[1, 0]])
                xx, yy, zz, xy, xz, yz = b['inertia_kg_m2']; inertia = np.array([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]])
                energy += .5*b['mass_kg']*speed@speed+.5*omega@inertia@omega
            self.assertLess(abs(.5*a.velocity@a.mass_matrix@a.velocity-energy), 2e-11)
            np.testing.assert_allclose(a.mass_matrix, a.mass_matrix.T, atol=1e-17)
            self.assertGreater(np.linalg.eigvalsh(a.mass_matrix).min(), 0.)

    def test_gravity_is_negative_potential_gradient(self):
        q, rates = self.cases[0]; a = Assembly(self.model, q, rates); eps = 1e-6
        def potential(values):
            frames = pose_frames(self.model, values)
            return -sum(b['mass_kg']*a.gravity@(frames[b['name']]@np.r_[b['mass_center_m'], 1.])[:3] for b in self.model['bodies'])
        for i, name in enumerate(a.coordinates):
            plus = dict(q); minus = dict(q); plus[name] += eps; minus[name] -= eps
            self.assertAlmostEqual(a.gravity_force[i], -(potential(plus)-potential(minus))/(2*eps), delta=2e-8)

    def test_inertial_bias_obeys_kinetic_energy_power_identity(self):
        eps = 2e-6
        for q, rates in self.cases:
            a = Assembly(self.model, q, rates)
            plus = Assembly(self.model, {k: v+eps*rates[k] for k, v in q.items()})
            minus = Assembly(self.model, {k: v-eps*rates[k] for k, v in q.items()})
            mdot = (plus.mass_matrix-minus.mass_matrix)/(2*eps)
            self.assertAlmostEqual(a.velocity@a.bias_force, .5*a.velocity@mdot@a.velocity, delta=2e-11)

    def test_full_bias_vector_against_FK_accelerations(self):
        q, rates = self.cases[1]; a = Assembly(self.model, q, rates); eps = 2e-4
        f0 = pose_frames(self.model, q)
        fp = pose_frames(self.model, {k: v+eps*rates[k] for k, v in q.items()})
        fm = pose_frames(self.model, {k: v-eps*rates[k] for k, v in q.items()})
        partial = []
        for name in a.coordinates:
            p = dict(q); m = dict(q); p[name] += eps; m[name] -= eps
            partial.append((pose_frames(self.model, p), pose_frames(self.model, m)))
        expected = np.zeros(a.n)
        for b in self.model['bodies']:
            name = b['name']; r = f0[name][:3, :3]; cm = np.r_[b['mass_center_m'], 1.]
            first = (fp[name]-fm[name])/(2*eps); second = (fp[name]-2*f0[name]+fm[name])/(eps*eps)
            omega_matrix = first[:3, :3]@r.T
            alpha_matrix = second[:3, :3]@r.T+first[:3, :3]@first[:3, :3].T
            omega = np.array([omega_matrix[2, 1], omega_matrix[0, 2], omega_matrix[1, 0]])
            alpha = np.array([alpha_matrix[2, 1]-alpha_matrix[1, 2], alpha_matrix[0, 2]-alpha_matrix[2, 0], alpha_matrix[1, 0]-alpha_matrix[0, 1]])/2
            xx, yy, zz, xy, xz, yz = b['inertia_kg_m2']; iw = r@np.array([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]])@r.T
            force = b['mass_kg']*(second@cm)[:3]; moment = iw@alpha+np.cross(omega, iw@omega)
            for i, (plus, minus) in enumerate(partial):
                derivative = (plus[name]-minus[name])/(2*eps); w = derivative[:3, :3]@r.T
                angular = np.array([w[2, 1], w[0, 2], w[1, 0]])
                expected[i] += (derivative@cm)[:3]@force+angular@moment
        np.testing.assert_allclose(a.bias_force, expected, atol=2e-9, rtol=2e-6)

    def test_point_force_preserves_virtual_work(self):
        q, rates = self.cases[0]; a = Assembly(self.model, q, rates); f = np.array([2., -3., .5]); point = [.01, -.02, .03]
        torque = a.point_force('hand', point, f); eps = 1e-6
        p = pose_frames(self.model, {k: v+eps*rates[k] for k, v in q.items()})['hand']@np.r_[point, 1.]
        m = pose_frames(self.model, {k: v-eps*rates[k] for k, v in q.items()})['hand']@np.r_[point, 1.]
        self.assertAlmostEqual(torque@a.velocity, f@(p-m)[:3]/(2*eps), delta=2e-9)

    def test_elbow_entry_matches_qualified_scalar_inertia(self):
        a = Assembly(self.model); i = a.coordinates.index('elbow_flexion')
        self.assertAlmostEqual(a.mass_matrix[i, i], .0019939687829337097, delta=2e-17)
        np.testing.assert_array_equal(a.bias_force, np.zeros(7))

    def test_singular_chart_refuses_without_regularization(self):
        m = planar_model(); m['coordinates']['unused'] = {'default_rad': 0., 'range_rad': [-1., 1.], 'locked': False}
        a = Assembly(m); before = a.mass_matrix.copy()
        with self.assertRaisesRegex(Refusal, 'singular_or_ill_conditioned_mass_matrix'): a.acceleration([1., 0., 0.])
        np.testing.assert_array_equal(before, a.mass_matrix)

    def test_invalid_inputs_and_inertia_refuse(self):
        for rates in ({'tail': 0.}, {'elbow_flexion': float('nan')}):
            with self.assertRaises(Refusal): Assembly(self.model, rates=rates)
        bad = copy.deepcopy(self.model); bad['bodies'][-1]['inertia_kg_m2'][0] = -1.
        with self.assertRaisesRegex(Refusal, 'nonphysical_body_inertia'): Assembly(bad)
        bad = copy.deepcopy(self.model); bad['coordinates']['elbow_flexion']['locked'] = True
        with self.assertRaisesRegex(Refusal, 'unknown_or_locked_rate'): Assembly(bad, rates={'elbow_flexion': 1.})
        with self.assertRaises(Refusal): Assembly(self.model, gravity=[0., float('nan'), 0.])
        a = Assembly(self.model)
        with self.assertRaises(Refusal): a.point_force('hand', [0., 0., 0.], [0., float('inf'), 0.])


if __name__ == '__main__':
    unittest.main()
