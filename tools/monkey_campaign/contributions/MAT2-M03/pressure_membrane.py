"""MAT2-M03: pressure on a closed triangulated membrane.

Implements the frozen preregistration (PREREGISTRATION.md, this directory,
including correction A1): pressure traction F = (p_int - p_ext) * A_i * n_i per
triangle from a DECLARED pressure source, volume closure via the divergence
theorem, exact zero net force/torque from uniform pressure on any closed mesh,
exact linear-field external loading references (-V*q and -V*(x_bar x q)),
refinement families against analytic references, pressure-volume work with a
midpoint-rule traction account, declared source power and limits with named
refusals, and an XPBD-style inflate/deflate demonstration whose energy ledger
reports the constraint-projection residual per tick (never hidden).

Upstream authority, reused verbatim and unmodified:
- tools/monkey_campaign/contributions/MAT2-M01/material_state.py
  (chimera.material_state.v1 validator; schema authority),
- tools/monkey_campaign/contributions/MAT2-M02/ (compiled closed regions; the
  tetra mesh blob is byte-verified against its recorded sha256 before use).

Laws honoured (docs/THE_MEMBRANE_INVENTORY.md): "Triangles are not physical
weights" — declared mass is refinement-invariant; retessellation never changes
the mass or the net loading. XPBD heritage pin: docs/THE_MASTER_LIST.md
("XPBD gives the unconditionally-stable real-time solver"); fixed 300 Hz
physical tick pin: req.teddy_gpu_matter_kernel.

CPU-only; stdlib + numpy; deterministic (no stochastic inputs anywhere).
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib

import numpy as np

SCHEMA = 'chimera.material_state.v1'

# Recorded upstream identity (verified at load time, never trusted blindly).
M02_DIR_NAME = 'MAT2-M02'
M01_DIR_NAME = 'MAT2-M01'
M02_MESH_BLOB_NAME = 'monkey_arm_independent_meshes.json'
M02_TETRA_BLOB_SHA256 = '51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834'
M02_TETRA_RECORDED_VOLUME_M3 = 0.00016666666666666682
M02_TETRA_RECORDED_AREA_M2 = 0.023660254037844386

# Declared scenario constants (PREREGISTRATION.md; standard gravity, water).
RHO_KG_M3 = 1000.0
G_M_S2 = 9.80665


def require(condition, code):
    """Named refusal; no numeric inference or repair."""
    if not condition:
        raise ValueError(code)


def _finite(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)), 'nonfinite_' + label)
    return float(value)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


class LinearField:
    """Declared linear exterior pressure field p(x) = p0 + q . x (SI Pa, m)."""

    def __init__(self, p0_pa, gradient_pa_per_m):
        self.p0_pa = _finite(p0_pa, 'linear_field_p0')
        q = [ _finite(c, 'linear_field_q') for c in gradient_pa_per_m ]
        require(len(q) == 3, 'linear_field_q_size')
        self.gradient_pa_per_m = np.array(q, dtype=np.float64)

    def pressure_at(self, points):
        pts = np.asarray(points, dtype=np.float64)
        return self.p0_pa + pts @ self.gradient_pa_per_m

    def declare(self):
        return {'kind': 'linear_exterior_pressure',
                'p0_pa': self.p0_pa,
                'gradient_pa_per_m': [float(c) for c in self.gradient_pa_per_m]}


class PressureSource:
    """Declared pressure actuator with authored limits (never inferred).

    Refusals (named): pressure_source_negative_absolute,
    pressure_source_delta_p_limit_exceeded, pressure_source_flow_limit_exceeded.
    Requesting traction without a declared source raises
    pressure_source_undeclared (see Membrane.triangle_tractions).
    """

    def __init__(self, source_id, p_int_pa, p_ext_pa, max_delta_p_pa,
                 max_dv_dt_m3_per_s, provenance):
        require(isinstance(source_id, str) and source_id.strip(),
                'pressure_source_id_invalid')
        require(isinstance(provenance, str) and provenance.strip(),
                'pressure_source_provenance_invalid')
        p_int = _finite(p_int_pa, 'pressure_source_p_int')
        p_ext = _finite(p_ext_pa, 'pressure_source_p_ext')
        require(p_int >= 0.0, 'pressure_source_negative_absolute')
        require(p_ext >= 0.0, 'pressure_source_negative_absolute')
        max_dp = _finite(max_delta_p_pa, 'pressure_source_max_delta_p')
        max_flow = _finite(max_dv_dt_m3_per_s, 'pressure_source_max_flow')
        require(max_dp > 0.0 and max_flow > 0.0,
                'pressure_source_limits_nonpositive')
        self.source_id = source_id
        self.p_int_pa = p_int
        self.p_ext_pa = p_ext
        self.max_delta_p_pa = max_dp
        self.max_dv_dt_m3_per_s = max_flow
        self.provenance = provenance

    @property
    def delta_p(self):
        return self.p_int_pa - self.p_ext_pa

    def enforce_delta_p(self, value=None):
        value = self.delta_p if value is None else _finite(value, 'delta_p')
        require(abs(value) <= self.max_delta_p_pa,
                'pressure_source_delta_p_limit_exceeded')
        return value

    def enforce_flow(self, dv_dt):
        require(abs(_finite(dv_dt, 'dv_dt')) <= self.max_dv_dt_m3_per_s,
                'pressure_source_flow_limit_exceeded')
        return dv_dt

    def power_watts(self, dv_dt):
        """Power delivered by the source: P = delta_p * dV/dt (T6)."""
        self.enforce_flow(dv_dt)
        return self.delta_p * dv_dt

    def with_delta_p(self, value):
        """A scheduled sibling source: same declaration, scheduled pressures.
        Absolute interior pressure stays nonnegative; limits enforced."""
        value = _finite(value, 'delta_p')
        require(abs(value) <= self.max_delta_p_pa,
                'pressure_source_delta_p_limit_exceeded')
        p_ext = self.p_ext_pa
        p_int = p_ext + value
        require(p_int >= 0.0, 'pressure_source_negative_absolute')
        clone = PressureSource(
            self.source_id, p_int, p_ext, self.max_delta_p_pa,
            self.max_dv_dt_m3_per_s, self.provenance)
        return clone

    def declare(self):
        return {'source_id': self.source_id,
                'p_int_pa': self.p_int_pa,
                'p_ext_pa': self.p_ext_pa,
                'max_delta_p_pa': self.max_delta_p_pa,
                'max_dv_dt_m3_per_s': self.max_dv_dt_m3_per_s,
                'provenance': self.provenance}


class Membrane:
    """A triangulated surface with closure, traction, volume and work laws."""

    def __init__(self, vertices, triangles, name='membrane',
                 declared_mass_kg=None):
        v = np.asarray(vertices, dtype=np.float64)
        t = np.asarray(triangles, dtype=np.int64)
        require(v.ndim == 2 and v.shape[1] == 3 and v.size > 0, 'mesh_vertices')
        require(np.all(np.isfinite(v)), 'mesh_vertices_nonfinite')
        require(t.ndim == 2 and t.shape[1] == 3 and t.shape[0] > 0, 'mesh_triangles')
        require(t.min() >= 0 and t.max() < v.shape[0], 'mesh_index_out_of_range')
        self.name = name
        self.vertices = v
        self.triangles = t
        self.declared_mass_kg = (None if declared_mass_kg is None
                                 else _finite(declared_mass_kg, 'declared_mass'))
        tri = v[t]                                   # (m, 3, 3)
        e1 = tri[:, 1] - tri[:, 0]
        e2 = tri[:, 2] - tri[:, 0]
        cross = np.cross(e1, e2)
        self._two_area = np.linalg.norm(cross, axis=1)
        norm = self._two_area.copy()
        require(np.all(norm > 0.0), 'mesh_degenerate_triangle')
        self.normals = cross / norm[:, None]         # unit, winding-defined
        self.areas = 0.5 * self._two_area
        self.centroids = tri.mean(axis=1)

    # ---- topology / closure ------------------------------------------------
    def closure_report(self):
        undirected = {}
        directed = set()
        dup_directed = 0
        for a, b, c in self.triangles.tolist():
            for u, w in ((a, b), (b, c), (c, a)):
                key = (min(u, w), max(u, w))
                undirected[key] = undirected.get(key, 0) + 1
                d = (u, w)
                if d in directed:
                    dup_directed += 1
                directed.add(d)
        open_edges = sorted(k for k, n in undirected.items() if n != 2)
        return {'undirected_edge_count': len(undirected),
                'open_edge_count': len(open_edges),
                'open_edges': open_edges[:16],
                'duplicate_directed_edges': dup_directed,
                'signed_volume_m3': self.signed_volume(),
                'surface_area_m2': self.surface_area(),
                'vertex_count': int(self.vertices.shape[0]),
                'triangle_count': int(self.triangles.shape[0])}

    def require_closed(self):
        report = self.closure_report()
        require(report['open_edge_count'] == 0, 'closure_open_edges')
        require(report['duplicate_directed_edges'] == 0, 'orientation_inconsistent')
        require(report['signed_volume_m3'] > 0.0, 'closure_negative_volume')
        return report

    def signed_volume(self):
        """Divergence theorem: V = (1/6) sum det(v0, v1, v2)."""
        tri = self.vertices[self.triangles]
        return float(np.einsum('ij,ij->i', tri[:, 0],
                               np.cross(tri[:, 1], tri[:, 2])).sum() / 6.0)

    def surface_area(self):
        return float(self.areas.sum())

    def volume_centroid(self):
        """Exact polyhedron volume centroid (tetra decomposition about origin)."""
        v_total = self.signed_volume()
        require(v_total > 0.0, 'closure_negative_volume')
        tri = self.vertices[self.triangles]
        det6 = np.einsum('ij,ij->i', tri[:, 0], np.cross(tri[:, 1], tri[:, 2]))
        return (det6[:, None] * tri.sum(axis=1)).sum(axis=0) / (24.0 * v_total)

    # ---- pressure traction -------------------------------------------------
    def triangle_tractions(self, source, exterior_field=None):
        """Per-triangle resultant forces from a DECLARED source.

        F_i = delta_p * A_i * n_i (outward, from interior excess pressure);
        an optional declared linear exterior field pushes inward with the exact
        centroid pressure -p_ext(c_i) * A_i * n_i (midpoint rule is exact for a
        linear field on a flat triangle). Refuses undeclared sources (F3) and
        open/inconsistent meshes.
        """
        require(isinstance(source, PressureSource), 'pressure_source_undeclared')
        source.enforce_delta_p()
        report = self.require_closed()
        forces = source.delta_p * self.areas[:, None] * self.normals
        if exterior_field is not None:
            require(isinstance(exterior_field, LinearField),
                    'exterior_field_undeclared')
            p_ext = exterior_field.pressure_at(self.centroids)
            forces = forces - p_ext[:, None] * self.areas[:, None] * self.normals
        return forces, report

    def vertex_loads(self, source, exterior_field=None,
                     area_weighting='area'):
        """Equal-third lumped nodal loads; the lumping preserves each triangle
        resultant exactly, so net force and torque survive lumping at full
        precision.

        area_weighting='constant' is the FALSIFIER tamper only (F1/F2: an
        area-independent constant force per triangle); production callers must
        use the default.
        """
        forces, report = self.triangle_tractions(source, exterior_field)
        if area_weighting == 'constant':
            forces = forces * (float(self.areas.mean())
                               / self.areas)[:, None]
        elif area_weighting != 'area':
            raise ValueError('area_weighting_invalid')
        loads = np.zeros_like(self.vertices)
        np.add.at(loads, self.triangles[:, 0], forces / 3.0)
        np.add.at(loads, self.triangles[:, 1], forces / 3.0)
        np.add.at(loads, self.triangles[:, 2], forces / 3.0)
        return loads, forces, report

    def net_force_torque(self, forces, about=None):
        """Net force and torque of per-triangle resultants applied at centroids."""
        net_f = forces.sum(axis=0)
        lever = self.centroids if about is None else self.centroids - np.asarray(about, dtype=np.float64)
        net_tau = np.cross(lever, forces).sum(axis=0)
        return net_f, net_tau

    # ---- external-field references (independently derived) -----------------
    def linear_field_reference(self, field):
        """References for p_ext(x) = p0 + q . x on a closed mesh:
        F = -q*V is an exact identity (machine precision); uniform pressure
        (p0) alone gives zero net force/torque exactly (closed-surface
        identity; observed values are round-off only). Torque under the
        linear part is h^2-convergent quadrature, never claimed exact
        (correction A7): tau_origin -> -V*(x_bar x q) and the torque about
        the volume centroid -> 0 at that h^2 rate (measured 1.926e-2 ->
        4.816e-3 -> 1.204e-3 N m on the tetra family, exactly x4 per
        midpoint subdivision; refined members <= 1e-9 N m). Divergence
        theorem, no simulation."""
        v_total = self.signed_volume()
        x_bar = self.volume_centroid()
        q = field.gradient_pa_per_m
        force_ref = -v_total * q
        tau_ref = -v_total * np.cross(x_bar, q)
        return {'force_n': force_ref, 'torque_about_origin_nm': tau_ref,
                'volume_centroid_m': x_bar, 'volume_m3': v_total}

    # ---- pressure-volume work (T5, midpoint rule declared) -----------------
    def quasi_static_scaling_work(self, source, s_final=1.1, steps=2000):
        """Inflate the membrane by uniform scaling s in [1, s_final].

        Per step the traction work uses the declared midpoint rule: forces are
        evaluated at the midpoint configuration and the displacement rate is the
        midpoint vertex velocity delta_s * x_unit, so the per-step identity
        W_step = delta_p * delta-V_step holds exactly (both sides equal
        3 * delta_p * V_unit * s_mid^2 * delta_s algebraically). The volume side
        telescopes exactly to delta_p*(V1 - V0).
        """
        require(isinstance(source, PressureSource), 'pressure_source_undeclared')
        source.enforce_delta_p()
        self.require_closed()
        template = Membrane(self.vertices, self.triangles, self.name)
        x_unit = self.vertices
        v_unit = template.signed_volume()
        require(abs(s_final - 1.0) > 0.0 and steps > 0, 'work_path_invalid')
        delta_s = (s_final - 1.0) / steps
        total_traction = 0.0
        total_volume = 0.0
        max_step_diff = 0.0
        for k in range(1, steps + 1):
            s_prev = 1.0 + delta_s * (k - 1)
            s_k = 1.0 + delta_s * k
            s_mid = 0.5 * (s_prev + s_k)
            mid = Membrane(x_unit * s_mid, self.triangles, self.name)
            forces, _ = mid.triangle_tractions(source)
            loads = np.zeros_like(mid.vertices)
            np.add.at(loads, self.triangles[:, 0], forces / 3.0)
            np.add.at(loads, self.triangles[:, 1], forces / 3.0)
            np.add.at(loads, self.triangles[:, 2], forces / 3.0)
            dx = delta_s * x_unit                      # midpoint vertex velocity * delta_s
            w_traction = float((loads * dx).sum())
            v_prev = v_unit * s_prev ** 3
            v_k = v_unit * s_k ** 3
            dv = v_k - v_prev
            w_volume = source.delta_p * dv
            max_step_diff = max(max_step_diff, abs(w_traction - w_volume))
            total_traction += w_traction
            total_volume += w_volume
        v1 = v_unit * s_final ** 3
        closed_form = source.delta_p * (v1 - v_unit)
        return {'work_traction_j': total_traction,
                'work_volume_sum_j': total_volume,
                'work_closed_form_j': closed_form,
                'max_step_traction_volume_diff_j': max_step_diff,
                'volume_start_m3': v_unit, 'volume_final_m3': v1,
                'steps': steps,
                'delta_p_pa': source.delta_p}


# ---- refinement families (deterministic, no stochastic inputs) --------------

def right_tetra(leg, origin=(0.0, 0.0, 0.0), name='tetra'):
    """Right tetrahedron with mutually perpendicular legs; outward winding
    (same winding pattern as the M02 compiled tetra)."""
    o = np.array(origin, dtype=np.float64)
    v = np.array([o,
                  o + np.array([leg, 0.0, 0.0]),
                  o + np.array([0.0, leg, 0.0]),
                  o + np.array([0.0, 0.0, leg])], dtype=np.float64)
    t = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])
    return Membrane(v, t, name)


def subdivide(membrane, levels=1, project_to_radius=None):
    """Global midpoint subdivision (shared edge midpoints); orientation and
    closure are preserved. Optional re-projection to a radius (icospheres)."""
    v = membrane.vertices.copy()
    t = membrane.triangles
    for _ in range(int(levels)):
        midpoint = {}
        edges = []
        next_index = len(v)

        def mid_index(a, b):
            nonlocal next_index
            key = (min(a, b), max(a, b))
            if key not in midpoint:
                midpoint[key] = next_index
                next_index += 1
                edges.append(0.5 * (v[key[0]] + v[key[1]]))
            return midpoint[key]

        new_tris = []
        for a, b, c in t.tolist():
            ab, bc, ca = mid_index(a, b), mid_index(b, c), mid_index(c, a)
            new_tris.extend([[a, ab, ca], [b, bc, ab], [c, ca, bc],
                             [ab, bc, ca]])
        if edges:
            v = np.vstack([v, np.array(edges, dtype=np.float64)])
        t = np.array(new_tris, dtype=np.int64)
    out = Membrane(v, t, membrane.name)
    if project_to_radius is not None:
        out = Membrane(out.vertices / np.linalg.norm(
            out.vertices, axis=1)[:, None] * project_to_radius,
            out.triangles, membrane.name)
    return out


_ICOSAHEDRON_V, _ICOSAHEDRON_T = None, None


def _icosahedron():
    global _ICOSAHEDRON_V, _ICOSAHEDRON_T
    if _ICOSAHEDRON_V is None:
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        raw = [
            [-1.0, phi, 0.0], [1.0, phi, 0.0], [-1.0, -phi, 0.0],
            [1.0, -phi, 0.0],
            [0.0, -1.0, phi], [0.0, 1.0, phi], [0.0, -1.0, -phi],
            [0.0, 1.0, -phi],
            [phi, 0.0, -1.0], [phi, 0.0, 1.0], [-phi, 0.0, -1.0],
            [-phi, 0.0, 1.0],
        ]
        v = np.array(raw, dtype=np.float64)
        v = v / np.linalg.norm(v, axis=1)[:, None]
        # Canonical outward-wound icosahedron faces for this vertex order.
        faces = [
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
        ]
        probe = Membrane(v, np.array(faces, dtype=np.int64), 'icosahedron')
        report = probe.closure_report()
        require(report['open_edge_count'] == 0
                and report['duplicate_directed_edges'] == 0
                and report['signed_volume_m3'] > 0.0,
                'icosahedron_winding_invalid')
        _ICOSAHEDRON_V, _ICOSAHEDRON_T = v, np.array(faces, dtype=np.int64)
    return _ICOSAHEDRON_V, _ICOSAHEDRON_T


def icosphere(level, radius, name=None):
    """Icosphere: subdivided icosahedron projected to the given radius."""
    v, t = _icosahedron()
    base = Membrane(v, t, name or f'icosphere_L{level}')
    out = subdivide(base, levels=int(level), project_to_radius=float(radius))
    out.name = name or f'icosphere_L{level}'
    return out


def cube_grid(n, side=1.0, name=None):
    """Unit-cube surface with n x n quads per face (welded lattice vertices,
    outward winding; exact volume at every n)."""
    require(int(n) >= 1 and n == int(n), 'cube_grid_n_invalid')
    n = int(n)
    verts = {}
    index = []

    def vid(i, j, k):
        key = (i, j, k)
        if key not in verts:
            verts[key] = len(index)
            index.append([-0.5 + c / n for c in key])
        return verts[key]

    half = side / 2.0
    tris = []
    # faces: (fixed_axis, fixed_sign, u_axis, v_axis) with u x v = +normal
    faces = [(0, +1, 1, 2), (0, -1, 2, 1), (1, +1, 2, 0),
             (1, -1, 0, 2), (2, +1, 0, 1), (2, -1, 1, 0)]
    for axis, sign, ua, va in faces:
        def p(i, j, axis=axis, sign=sign, ua=ua, va=va):
            coord = [0, 0, 0]
            coord[axis] = n if sign > 0 else 0
            coord[ua] = i
            coord[va] = j
            return vid(*coord)
        for i in range(n):
            for j in range(n):
                v00, v10 = p(i, j), p(i + 1, j)
                v11, v01 = p(i + 1, j + 1), p(i, j + 1)
                tris.append([v00, v10, v11])
                tris.append([v00, v11, v01])
    out = Membrane(np.array(index, dtype=np.float64) * side,
                   np.array(tris, dtype=np.int64),
                   name or f'cube_n{n}')
    require(abs(out.signed_volume() - side ** 3) < 1e-12, 'cube_volume_invalid')
    return out


# ---- XPBD-style dynamic demonstration (T7/T9; motion profile) ---------------

class InflatableRun:
    """Explicit XPBD inflate/deflate of a closed membrane under the declared
    source. Deterministic; no stochastic inputs. Per-tick energy ledger reports
    pressure work, damping dissipation and the MEASURED constraint-projection
    residual R_tick (T9), which is never assumed away.

    load_mode='constant_per_triangle' is the FALSIFIER tamper (F2) only.
    """

    def __init__(self, membrane, source, total_mass_kg, compliance_m_per_n,
                 damping_per_s, iterations, dt_s, load_mode='area'):
        membrane.require_closed()
        self.membrane = membrane
        self.source = source
        self.load_mode = load_mode
        require(total_mass_kg > 0.0, 'run_mass_invalid')
        require(compliance_m_per_n > 0.0 and damping_per_s >= 0.0
                and iterations >= 1 and dt_s > 0.0, 'run_parameters_invalid')
        n = membrane.vertices.shape[0]
        self.masses = np.full(n, total_mass_kg / n)
        self.inv_masses = 1.0 / self.masses
        self.compliance = compliance_m_per_n
        self.damping = damping_per_s
        self.iterations = int(iterations)
        self.dt = dt_s
        edges = {}
        for a, b, c in membrane.triangles.tolist():
            for u, w in ((a, b), (b, c), (c, a)):
                edges[(min(u, w), max(u, w))] = True
        self.edges = sorted(edges)
        vec = membrane.vertices
        self.rest = np.array([np.linalg.norm(vec[a] - vec[b])
                              for a, b in self.edges])
        self.x = membrane.vertices.copy()
        self.v = np.zeros_like(self.x)

    def _pressure_tick(self, delta_p_value):
        scheduled = self.source.with_delta_p(delta_p_value)
        loads, _, _ = self.membrane.vertex_loads(
            scheduled,
            area_weighting=('constant' if self.load_mode ==
                            'constant_per_triangle' else 'area'))
        return loads

    def step(self, delta_p_value, tick):
        dp_source = self.source
        require(abs(delta_p_value) <= dp_source.max_delta_p_pa,
                'pressure_source_delta_p_limit_exceeded')
        x0 = self.x.copy()
        # damping first (measured dissipation)
        if self.damping > 0.0:
            kin_before = float((0.5 * self.masses[:, None]
                                * self.v ** 2).sum())
            self.v = self.v * (1.0 - self.damping * self.dt)
            kin_after = float((0.5 * self.masses[:, None]
                               * self.v ** 2).sum())
            e_diss = kin_before - kin_after
        else:
            e_diss = 0.0
        # loads and integration
        loads = self._pressure_tick(delta_p_value)
        self.v = self.v + loads * self.inv_masses[:, None] * self.dt
        x_prev = self.x.copy()
        self.x = self.x + self.v * self.dt
        w_press = float((loads * (self.x - x0)).sum())
        # XPBD edge projection
        alpha_tilde = self.compliance / (self.dt * self.dt)
        lam = np.zeros(len(self.edges))
        for _ in range(self.iterations):
            for e, (a, b) in enumerate(self.edges):
                pa, pb = self.x[a], self.x[b]
                d = pb - pa
                length = float(np.linalg.norm(d))
                if length == 0.0:
                    continue
                grad = d / length
                c = length - self.rest[e]
                w_sum = self.inv_masses[a] + self.inv_masses[b]
                dlam = (-c - alpha_tilde * lam[e]) / (w_sum + alpha_tilde)
                lam[e] += dlam
                self.x[a] -= self.inv_masses[a] * dlam * grad
                self.x[b] += self.inv_masses[b] * dlam * grad
        self.v = (self.x - x_prev) / self.dt
        # ledger (T9): R is the measured constraint-projection work
        kin = float((0.5 * self.masses[:, None] * self.v ** 2).sum())
        diff = self.x[self.tri_edge_array()[:, 0]] - \
            self.x[self.tri_edge_array()[:, 1]]
        lengths = np.linalg.norm(diff, axis=1)
        elastic = float(((lengths - self.rest) ** 2).sum() / (2.0 * self.compliance))
        current = self.current_membrane()
        e_mech = kin + elastic
        com = (self.x * self.masses[:, None]).sum(axis=0) / self.masses.sum()
        return {
            'tick': tick, 'delta_p_pa': float(delta_p_value),
            'w_pressure_j': w_press, 'e_diss_damping_j': e_diss,
            'e_kinetic_j': kin, 'e_elastic_j': elastic,
            'e_mechanical_j': e_mech,
            'residual_r_j': e_mech - w_press + e_diss
                            - getattr(self, '_e_mech_prev', 0.0),
            'volume_m3': current.signed_volume(),
            'surface_area_m2': current.surface_area(),
            'com_m': [float(c) for c in com],
            'com_drift_m': float(np.linalg.norm(com - (self.x0_com if
                                hasattr(self, 'x0_com') else com))),
            'max_speed_m_per_s': float(np.abs(self.v).max()),
        }

    def tri_edge_array(self):
        if not hasattr(self, '_edge_arr'):
            self._edge_arr = np.array(self.edges, dtype=np.int64)
        return self._edge_arr

    def run(self, schedule):
        self.x0_com = (self.x * self.masses[:, None]).sum(axis=0) \
            / self.masses.sum()
        self._e_mech_prev = 0.0
        ticks = []
        for tick, dp_value in enumerate(schedule):
            row = self.step(float(dp_value), tick)
            self._e_mech_prev = row['e_mechanical_j']
            ticks.append(row)
        return {'tick_count': len(ticks), 'ticks': ticks,
                'com_drift_final_m': ticks[-1]['com_drift_m'],
                'volume_start_m3': ticks[0]['volume_m3'],
                'volume_peak_m3': max(t['volume_m3'] for t in ticks),
                'volume_final_m3': ticks[-1]['volume_m3']}

    def current_membrane(self):
        return Membrane(self.x, self.membrane.triangles, self.membrane.name)


# ---- upstream byte-verified loading ----------------------------------------

def load_m02_tetra(contrib_dir):
    """Byte-verified load of the M02 compiled closed tetra (native frame)."""
    blob_path = (pathlib.Path(contrib_dir) / M02_DIR_NAME
                 / M02_MESH_BLOB_NAME)
    require(blob_path.exists(), 'm02_mesh_blob_missing')
    require(sha256_file(blob_path) == M02_TETRA_BLOB_SHA256,
            'm02_mesh_blob_sha_mismatch')
    blob = json.loads(blob_path.read_text(encoding='utf-8'))
    row = blob['regions']['tetra']
    membrane = Membrane(row['vertices_m'], row['triangles'], 'm02_tetra')
    report = membrane.require_closed()
    require(abs(report['signed_volume_m3']
                - M02_TETRA_RECORDED_VOLUME_M3) <= 1e-18,
            'm02_tetra_volume_mismatch')
    require(abs(report['surface_area_m2']
                - M02_TETRA_RECORDED_AREA_M2) <= 1e-18,
            'm02_tetra_area_mismatch')
    membrane.provenance = {
        'blob': M02_MESH_BLOB_NAME, 'blob_sha256': M02_TETRA_BLOB_SHA256,
        'region_key': 'tetra', 'frame': row['frame'],
        'source_sha256': row['source_sha256']}
    return membrane
