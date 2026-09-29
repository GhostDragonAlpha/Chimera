"""MAT2-M07: one state owner integrating pressure, material and contact.

Implements the frozen PREREGISTRATION.md (Amendments A1, A2) exactly: a
single `IntegratedWorld.step()` is the ONLY writer of any physical state.
Each tick executes the DECLARED order

    1. pressure  (M03 declared-source traction, area-scaled, lumped)
    2. material  (M04 Maxwell element, exact exponential update/integrals)
    3. contact   (M06 sweep candidates -> local gap -> impulse solve, GS)

at the declared tick dt = 1/300 s with N_SUB = 4 declared substeps per tick
(each substep runs the same declared order), a declared Gauss-Seidel
convergence gate on the contact solve, and XPBD edge projection whose
exchange is kept in the MEASURED residual. Every tick records external work
(pressure, gravity), passive energy (Maxwell U/Q, scaffold elastic),
boundary reactions (ground anchor, wall anchor), bitwise-reciprocal contact
impulses and the measured residual R_tick (never hidden).

Upstream authority, reused verbatim and unmodified:
- tools/monkey_campaign/contributions/MAT2-M01/material_state.py
  (chimera.material_state.v1 validator; schema authority),
- tools/monkey_campaign/contributions/MAT2-M03/pressure_membrane.py
  (Membrane closure/traction/lumping, PressureSource schedule, icosphere),
- tools/monkey_campaign/contributions/MAT2-M04/passive_response.py
  (exact Maxwell update/integrals, stored_energy, check_ledger),
- tools/monkey_campaign/contributions/MAT2-M06/local_contact.py
  (sweep-and-prune, triangle-triangle closest features, solve_contact).

CPU-only; stdlib + numpy; deterministic (no stochastic inputs, no
wall-clock). Refusals are named codes; nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))
sys.path.insert(0, str(HERE.parent / 'MAT2-M03'))
sys.path.insert(0, str(HERE.parent / 'MAT2-M04'))
sys.path.insert(0, str(HERE.parent / 'MAT2-M06'))

import material_state  # noqa: E402  (M01 validator, unmodified)
import pressure_membrane as pm  # noqa: E402  (M03, unmodified)
import passive_response as pr  # noqa: E402  (M04, unmodified)
import local_contact as lc  # noqa: E402  (M06, unmodified)

# ---- frozen declarations (PREREGISTRATION.md + Amendments A1/A2) ------------
SCHEMA = 'chimera.integrated_step.v1'
G_M_S2 = 9.80665                  # M03's declared constant, along -z
DT_S = 1.0 / 300.0                # req.teddy_gpu_matter_kernel 300 Hz pin
N_SUB = 4                         # declared substeps per tick
GS_TOL_N_S = 1e-12                # contact Gauss-Seidel convergence gate
GS_CAP = 32                       # iteration cap
XPBD_TOL_M = 1e-10                # A6: projection tolerance (algebraic
# error below the O(h^2) truncation scale, per Astra round-6 R3)
XPBD_ITERATIONS_CAP = 100         # A6: adaptive iteration cap
XPBD_COMPLIANCE_M_PER_N = 1.0e-5  # M03/M05 scaffold heritage
THICKNESS_M = 0.002               # M06/M02 shell thickness pin
CONTACT_MARGIN_M = 1e-5           # M6 slop/margin pin
MEMBRANE_MU = (0.5, 0.35)         # declared surface friction (mu_s, mu_k)
PLATE_MU = (0.3, 0.2)
GROUND_MU = (0.7, 0.5)
MEMBRANE_RADIUS_M = 0.06
MEMBRANE_MASS_KG = 0.02
MEMBRANE_CENTER_Z_M = 0.062       # 1 mm initial gap to own ground (prereg)
PLATE_SIZE_M = 0.12
PLATE_MASS_KG = 0.02
PLATE_X0_M = 0.062                # plate midsurface plane (A2: gap 0)
PLATE_Z0_M = 0.001                # plate bottom midsurface (ground gap 0, A2)
PLATE_Z1_M = 0.121                # plate top midsurface (A2)
GROUND_HALF_M = 0.15
GROUND_Z_M = -0.001               # ground midsurface plane
WALL_K_N_PER_M = 20.0             # Maxwell element stiffness (declared)
WALL_C_N_S_PER_M = 8.0            # Maxwell element damping (declared)
PRESS_SCHEDULE = {tick: 60.0 for tick in range(1, 41)}   # Pa, ticks 1..40


def cyclic_press_schedule(tick):
    """A5 X4 long-duration schedule: the frozen X1 cycle repeated
    (press at tick mod 80 in 1..40, relax otherwise)."""
    phase = tick % 80
    return 60.0 if 1 <= phase <= 40 else 0.0


TICKS = 80
RESIDUAL_TURNOVER_FRACTION = 5e-2

DECLARED_ORDER = ('pressure', 'material', 'contact')

DECLARATION = {
    'schema': SCHEMA,
    'order': list(DECLARED_ORDER),
    'gravity_application': 'with_pressure_stage_external_loads',
    'dt_s': DT_S,
    'substeps_per_tick': N_SUB,
    'contact_gauss_seidel_tol_N_s': GS_TOL_N_S,
    'contact_gauss_seidel_cap': GS_CAP,
    'xpbd_tolerance_m': XPBD_TOL_M,
    'xpbd_iteration_cap': XPBD_ITERATIONS_CAP,
    'xpbd_compliance_m_per_N': XPBD_COMPLIANCE_M_PER_N,
    'thickness_m': THICKNESS_M,
    'contact_margin_m': CONTACT_MARGIN_M,
    'g_m_per_s2': G_M_S2,
    'membrane_radius_m': MEMBRANE_RADIUS_M,
    'membrane_mass_kg': MEMBRANE_MASS_KG,
    'plate_mass_kg': PLATE_MASS_KG,
    'wall_k_N_per_m': WALL_K_N_PER_M,
    'wall_c_N_s_per_m': WALL_C_N_S_PER_M,
    'friction_mu_s_k': {'membrane': list(MEMBRANE_MU), 'plate': list(PLATE_MU),
                        'ground': list(GROUND_MU)},
    'residual_bound': '5e-2*turnover + U_mat + U_mat_prev + U_scaff + '
                      'U_scaff_prev + 1e-9 (Amendment A1)',
    'upstream': 'M01 validator; M03 traction/source/icosphere; M04 Maxwell; '
                'M06 sweep/closest-features/solve_contact (verbatim)',
}


def require(condition, code):
    """Named refusal; no numeric inference or repair."""
    if not condition:
        raise ValueError(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


DECLARED_DIGEST = digest(DECLARATION)


# ---- frozen input pins (PREREGISTRATION.md; refuse drift) -------------------

INPUT_PINS = {
    '../MAT2-M01/material_state.py':
        'b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40',
    '../MAT2-M03/pressure_membrane.py':
        '3dd64f6465430380f1c0a53a95523c700cd51a6b1115e60f0df8afde2239c96e',
    '../MAT2-M04/passive_response.py':
        '68a696e1728066a3dce93db7b6c98f8bb4826322a84bbad20eeadf38350e326b',
    '../MAT2-M05/interface_exchange.py':
        '295e6c898ada14918f09b2b0633f5926c1623c9e09cd37258e516ab57450b9b9',
    '../MAT2-M06/local_contact.py':
        '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc',
}


def verify_input_pins(contrib_dir=None):
    """Refuse `input_pin_drift` if any pinned upstream file changed."""
    root = pathlib.Path(contrib_dir) if contrib_dir else HERE
    for rel, expected in INPUT_PINS.items():
        path = (root / rel).resolve()
        require(path.exists(), 'input_pin_missing:' + rel)
        require(sha256_file(path) == expected, 'input_pin_drift:' + rel)
    return dict(INPUT_PINS)


# ---- geometry builders (A2 coordinates) ---------------------------------------

def build_membrane(component_id, x_offset):
    base = pm.icosphere(1, MEMBRANE_RADIUS_M,
                        name=f'membrane_{component_id}')
    center = np.array([x_offset, 0.0, MEMBRANE_CENTER_Z_M])
    return pm.Membrane(base.vertices + center, base.triangles,
                       f'membrane_{component_id}')


def build_plate_vertices(x0):
    """Vertical 2-triangle shell; midsurface plane x = x0 (prereg/A2)."""
    half = PLATE_SIZE_M / 2.0
    return np.array([
        [x0, -half, PLATE_Z0_M],
        [x0, +half, PLATE_Z0_M],
        [x0, +half, PLATE_Z1_M],
        [x0, -half, PLATE_Z1_M]], dtype=np.float64)


def build_ground_vertices(x0):
    """Horizontal 2-triangle pinned shell; midsurface z = -0.001 (prereg)."""
    half = GROUND_HALF_M
    return np.array([
        [x0 - half, -half, GROUND_Z_M],
        [x0 - half, +half, GROUND_Z_M],
        [x0 + half, +half, GROUND_Z_M],
        [x0 + half, -half, GROUND_Z_M]], dtype=np.float64)


PLATE_TRIS = [(0, 1, 2), (0, 2, 3)]
GROUND_TRIS = [(0, 1, 2), (0, 2, 3)]


# ---- bodies -------------------------------------------------------------------

class ShellBody:
    """Rigid translating shell (plate or pinned ground).

    Declared view plus the rigid velocity scalar state; BOTH the vertex
    array and the velocity are written only by IntegratedWorld.step.
    """

    def __init__(self, body_id, matter_id, rest_vertices, triangles,
                 mass_kg, mu, pinned):
        self.id = body_id
        self.matter_id = matter_id
        self.rest = np.array(rest_vertices, dtype=np.float64)
        self.triangles = [tuple(int(i) for i in t) for t in triangles]
        self.mass_kg = None if pinned else float(mass_kg)
        require(self.mass_kg is None or self.mass_kg > 0.0, 'body_mass_invalid')
        self.mu_s, self.mu_k = (float(mu[0]), float(mu[1]))
        require(0.0 <= self.mu_k <= self.mu_s <= 1.0, 'bad_friction')
        self.thickness_m = THICKNESS_M
        self.pinned = bool(pinned)
        self.x = self.rest.copy()
        self.velocity = np.zeros(3, dtype=np.float64)

    def inv_mass(self):
        return 0.0 if self.pinned else 1.0 / self.mass_kg


class MembranePort:
    """M06-compatible adapter for one membrane triangle (declared port).

    The port is the rigid cluster of the triangle's 3 lumped vertices (M03
    equal-thirds heritage): its velocity is the mean of the three vertex
    velocities (exact for the declared equal masses); an applied impulse
    delta is written THROUGH to the three world-owned vertices equally.
    This write-through, called only from IntegratedWorld._phase_contact,
    is the world's write path for port impulses (P-single-owner).
    """

    def __init__(self, comp, tri_index):
        self._comp = comp
        self.tri_index = int(tri_index)
        self.vids = comp.membrane.triangles[self.tri_index]
        self.mass_kg = float(comp.masses[self.vids].sum())
        require(self.mass_kg > 0.0, 'port_mass_invalid')
        self.mu_s, self.mu_k = MEMBRANE_MU
        self.thickness_m = THICKNESS_M
        self.id = f'{comp.component_id}/port:t{self.tri_index}'
        self.matter_id = f'mat_{comp.component_id}_membrane'

    @property
    def velocity(self):
        return self._comp.v[self.vids].mean(axis=0)

    @velocity.setter
    def velocity(self, value):
        delta = np.asarray(value, dtype=np.float64) - self.velocity
        self._comp.v[self.vids] += delta

    def inv_mass(self):
        return 1.0 / self.mass_kg


class _PairBody:
    """Thin view exposing exactly what M06's solve_contact reads/mutates."""

    def __init__(self, holder):
        self._holder = holder

    @property
    def id(self):
        return self._holder.id

    @property
    def mu_s(self):
        return self._holder.mu_s

    @property
    def mu_k(self):
        return self._holder.mu_k

    @property
    def velocity(self):
        return self._holder.velocity

    @velocity.setter
    def velocity(self, value):
        self._holder.velocity = np.asarray(value, dtype=np.float64)

    def inv_mass(self):
        return self._holder.inv_mass()


def _pair_adapter(holder):
    if isinstance(holder, MembranePort):
        return holder
    return _PairBody(holder)


# ---- component ----------------------------------------------------------------

class Component:
    """One pressurized membrane + loose plate + Maxwell mount + own ground.

    Rig variants (A5): plate_x0 moves the plate/mount anchor (smooth and
    impact rigs); initial_velocity gives the plate a declared launch speed
    (impact rig); membrane_center_z pre-settles the membrane onto its
    ground (zero initial gap).
    """

    def __init__(self, component_id, x_offset=0.0, plate_x0=PLATE_X0_M,
                 initial_velocity=(0.0, 0.0, 0.0),
                 membrane_center_z=MEMBRANE_CENTER_Z_M):
        require(isinstance(component_id, str) and component_id.strip(),
                'component_id_invalid')
        self.component_id = component_id
        off = np.array([x_offset, 0.0, 0.0])
        base = pm.icosphere(1, MEMBRANE_RADIUS_M,
                            name=f'membrane_{component_id}')
        center = np.array([x_offset, 0.0, float(membrane_center_z)])
        self.membrane = pm.Membrane(base.vertices + center, base.triangles,
                                    f'membrane_{component_id}')
        n = self.membrane.vertices.shape[0]
        self.rest = self.membrane.vertices.copy()
        self.masses = np.full(n, MEMBRANE_MASS_KG / n)
        self.inv_masses = 1.0 / self.masses
        edges = {}
        for a, b, c in self.membrane.triangles.tolist():
            for u, w in ((a, b), (b, c), (c, a)):
                edges[(min(u, w), max(u, w))] = True
        self.edge_list = sorted(edges)
        self.edge_arr = np.array(self.edge_list, dtype=np.int64)
        self.rest_lengths = np.array([
            float(np.linalg.norm(self.rest[b] - self.rest[a]))
            for a, b in self.edge_list])
        self.x = self.membrane.vertices.copy()
        self.v = np.zeros_like(self.x)
        self.plate = ShellBody(
            f'plate_{component_id}', f'mat_{component_id}_plate',
            build_plate_vertices(float(plate_x0)) + off, PLATE_TRIS,
            PLATE_MASS_KG, PLATE_MU, pinned=False)
        self.plate.velocity = np.array(initial_velocity, dtype=np.float64)
        self.ground = ShellBody(
            f'ground_{component_id}', f'mat_{component_id}_ground',
            build_ground_vertices(x_offset), GROUND_TRIS, None, GROUND_MU,
            pinned=True)
        self.wall_anchor = self.plate.rest.mean(axis=0).copy()
        self.F = 0.0                       # Maxwell element force state
        self.U_mat = 0.0                   # cumulative stored energy (J)
        self.Q_mat = 0.0                   # cumulative dissipation (J)
        self.W_in_mat = 0.0                # cumulative element work in (J)
        self.source = pm.PressureSource(
            f'source_{component_id}', 0.0, 0.0, 5000.0, 1e-3,
            f'MAT2-M07 declared membrane pressure source ({component_id}); '
            'scheduled via with_delta_p sibling sources')
        self.ground_anchor_impulse = np.zeros(3)   # cumulative (boundary)
        self.wall_reaction_impulse = np.zeros(3)   # cumulative (boundary)

    def maxwell_element(self):
        return WALL_K_N_PER_M, WALL_C_N_S_PER_M


# ---- the one state owner -------------------------------------------------------

class IntegratedWorld:
    """The single owner and single writer of the integrated physical state.

    Nothing outside `IntegratedWorld.step` writes component positions,
    velocities, the Maxwell force state or the ledgers (P-single-owner;
    asserted by the test suite through source inspection).
    """

    def __init__(self, components, dt_s=DT_S, n_sub=N_SUB, gravity=True,
                 schedule=None):
        require(isinstance(components, list) and components,
                'world_components_invalid')
        ids = [c.component_id for c in components]
        require(len(set(ids)) == len(ids), 'duplicate_component_id')
        require(float(dt_s) > 0.0 and float(dt_s) <= DT_S + 1e-15,
                'dt_invalid')
        require(int(n_sub) >= 1, 'substeps_invalid')
        self.components = list(components)
        self.dt_s = float(dt_s)
        self.n_sub = int(n_sub)
        self.gravity = bool(gravity)   # declared per-run experimental
        # condition (A5 regime rigs; M06 A3 heritage), NOT part of the
        # frozen order guard.
        self.schedule = schedule       # None -> frozen PRESS_SCHEDULE dict
        self.tick = 0
        self.ticks = []
        # The order guard anchors on the LITERAL frozen order; the run's dt
        # is a declared refinement parameter and is not part of the guard.
        self.order_digest = DECLARED_DIGEST
        declaration = dict(DECLARATION)
        declaration['dt_s'] = self.dt_s
        declaration['substeps_per_tick'] = self.n_sub
        self.declaration = declaration

    # -- phase 1: declared-source pressure + declared gravity -----------------
    def _phase_pressure_and_gravity(self, comp, dp_pa, h):
        scheduled = comp.source.with_delta_p(dp_pa)
        current = pm.Membrane(comp.x, comp.membrane.triangles,
                              comp.membrane.name)
        pressure_loads, forces, closure = current.vertex_loads(scheduled)
        grav = np.array([0.0, 0.0, -G_M_S2 * (1.0 if self.gravity else 0.0)])
        g_loads = comp.masses[:, None] * grav[None, :]
        loads = pressure_loads + g_loads
        v_pre = comp.v.copy()
        comp.v = comp.v + loads * comp.inv_masses[:, None] * h
        v_bar = 0.5 * (v_pre + comp.v)
        w_press = float((pressure_loads * v_bar).sum() * h)
        w_grav = float((g_loads * v_bar).sum() * h)
        g_impulse_mem = (g_loads * h).sum(axis=0)
        # rigid plate gravity (declared external load, recorded impulse)
        m = comp.plate.mass_kg
        g_impulse_plate = m * grav * h
        v_pre_p = comp.plate.velocity.copy()
        comp.plate.velocity = comp.plate.velocity \
            + g_impulse_plate * comp.plate.inv_mass()
        w_grav += float(np.dot(grav * m,
                               0.5 * (v_pre_p + comp.plate.velocity)) * h)
        return {'w_press_j': w_press, 'w_grav_j': w_grav,
                'gravity_impulse_mem': g_impulse_mem,
                'gravity_impulse_plate': g_impulse_plate,
                'pressure_tris_N': forces,
                'delta_p_pa': float(scheduled.delta_p)}

    # -- phase 2: M04 Maxwell material element ---------------------------------
    def _phase_material(self, comp, h):
        k, c = comp.maxwell_element()
        v1x = float(comp.plate.velocity[0])
        a = comp.F
        int_F_dt, int_F2_dt = pr.maxwell_tick_integrals(a, v1x, h, k, c)
        F_next = pr.maxwell_force_update(a, v1x, h, k, c)
        q_i = int_F2_dt / c
        u_i = pr.stored_energy(F_next, k)
        J = int_F_dt
        inv_m = comp.plate.inv_mass()
        v_pre = comp.plate.velocity.copy()
        comp.plate.velocity = comp.plate.velocity \
            - np.array([J * inv_m, 0.0, 0.0])
        w_on_plate = -J * float(0.5 * (v_pre[0] + comp.plate.velocity[0]))
        # element account (M04's own protocol, cumulative; UNMODIFIED check)
        comp.W_in_mat += v1x * J
        comp.Q_mat += q_i
        comp.U_mat = u_i
        pr.check_ledger(comp.W_in_mat, comp.U_mat, comp.Q_mat)
        sub_closure = abs((v1x * J)
                          - ((u_i - pr.stored_energy(a, k)) + q_i))
        require(sub_closure <= 1e-9, 'material_subledger_open')
        comp.F = F_next
        return {'w_mat_on_plate_j': w_on_plate, 'w_in_mat_j': v1x * J,
                'q_mat_j': q_i, 'u_mat_j': u_i, 'F_N': F_next,
                'mat_impulse_n_s': -J}   # impulse applied TO the plate

    # -- phase 3: M06 local contact through declared ports ---------------------
    def _phase_contact(self, comp, h):
        shells = (('membrane', comp.x, comp.membrane.triangles),
                  ('plate', comp.plate.x, comp.plate.triangles),
                  ('ground', comp.ground.x, comp.ground.triangles))
        speed_m = float(np.linalg.norm(comp.v, axis=1).max())
        speed_p = float(np.linalg.norm(comp.plate.velocity))
        motion = max(speed_m, speed_p) * h
        inflate = motion + THICKNESS_M + CONTACT_MARGIN_M
        entries = []
        for surface, verts, tris in shells:
            for ti, tri in enumerate(tris):
                corners = verts[list(tri)]
                entries.append((surface, ti,
                                tuple(corners.min(axis=0) - inflate),
                                tuple(corners.max(axis=0) + inflate)))
        cand = lc.sweep_prune(entries)

        def tri_points(surface, ti):
            for s, verts, tris in shells:
                if s == surface:
                    return [tuple(v) for v in verts[list(tris[ti])]]
            raise ValueError('surface_unknown')

        def holder_for(surface, ti):
            if surface == 'membrane':
                return MembranePort(comp, ti)
            if surface == 'plate':
                return comp.plate
            return comp.ground

        # narrow phase: local closest features -> midsurface gap (M06)
        active = []
        for (i, j) in cand:
            sa, ta = entries[i][0], entries[i][1]
            sb, tb = entries[j][0], entries[j][1]
            p, q, dist = lc.tri_tri_closest(*tri_points(sa, ta),
                                            *tri_points(sb, tb))
            gap = dist - THICKNESS_M          # (h_a + h_b)/2 = h
            if gap <= CONTACT_MARGIN_M + lc.CCD_TOL_M:
                normal = lc.vunit(lc.vsub(p, q)) if dist > 0.0 \
                    else (0.0, 0.0, 1.0)
                active.append((holder_for(sa, ta), holder_for(sb, tb),
                               gap, normal, (sa, ta, sb, tb)))
        # declared Gauss-Seidel convergence gate (M06 solve_contact verbatim)
        ke_pre = self._component_ke(comp)
        records = []
        max_jn = 0.0
        iterations = 0
        contact = {'membrane': np.zeros(3), 'plate': np.zeros(3),
                   'ground': np.zeros(3)}
        recip = (0.0, 0.0, 0.0)
        d_friction = 0.0
        d_impact_physical = 0.0
        impulse_trapezoid_work = 0.0
        jn_applied_total = 0.0
        for iteration in range(GS_CAP):
            iterations = iteration + 1
            records = []
            pass_max = 0.0
            for (body_a, body_b, gap, normal, key) in active:
                va_pre = np.asarray(body_a.velocity, dtype=np.float64).copy()
                vb_pre = np.asarray(body_b.velocity, dtype=np.float64).copy()
                rec = lc.solve_contact(_pair_adapter(body_a),
                                       _pair_adapter(body_b), gap,
                                       normal, key)
                va_post = np.asarray(body_a.velocity, dtype=np.float64)
                vb_post = np.asarray(body_b.velocity, dtype=np.float64)
                pass_max = max(pass_max, rec['jn_Ns'], abs(rec['jt_Ns']))
                records.append(rec)
                # EVERY applied impulse is accumulated (the ledger must
                # cover all passes, not just the converged one)
                ja = np.array(rec['impulse_on_a'])
                jb = np.array(rec['impulse_on_b'])
                for holder, impulse in ((body_a, ja), (body_b, jb)):
                    if isinstance(holder, MembranePort):
                        contact['membrane'] += impulse
                    elif holder is comp.ground:
                        contact['ground'] += impulse
                    else:
                        contact['plate'] += impulse
                recip = lc.vadd(recip, tuple(rec['impulse_on_a']))
                recip = lc.vadd(recip, tuple(rec['impulse_on_b']))
                # R3 impulse-work diagnostic: Delta_K = 0.5*(v- + v+)^T J
                impulse_trapezoid_work += float(
                    0.5 * np.dot(0.5 * (va_pre + va_post), ja)
                    + 0.5 * np.dot(0.5 * (vb_pre + vb_post), jb))
                d_friction += float(rec.get('w_f_ke_J', 0.0))
                jn_applied_total += abs(rec['jn_Ns'])
                # A7: PHYSICAL inelastic loss from the pre-solve normal
                # speed (restitution 0); the remainder of the contact-stage
                # KE change is the recorded stabilization exchange
                vn_pre = float(np.dot(va_pre - vb_pre,
                                      np.array(normal, dtype=np.float64)))
                if vn_pre < 0.0:
                    d_impact_physical += 0.5 * rec['m_eff'] * vn_pre * vn_pre
            max_jn = pass_max
            if pass_max <= GS_TOL_N_S:
                break
        require(max_jn <= GS_TOL_N_S, 'convergence_gate_not_met')
        w_contact_ke = -(self._component_ke(comp) - ke_pre)
        # reciprocity: every applied impulse bitwise two-sided (M05/M06 law)
        require(lc.vlen(recip) <= 1e-12, 'ledger_imbalance')
        # A5 contact residuals (post-solve, whole active set): normal
        # impulse nonnegativity, post-solve separation velocity, friction
        # cone, stick residual tangential speed
        min_jn = min((rec['jn_Ns'] for rec in records), default=0.0)
        min_vn_post = 0.0
        max_cone_violation = 0.0
        max_stick_vt_post = 0.0
        for rec, (body_a, body_b, gap, normal, key) in zip(records, active):
            va = np.asarray(body_a.velocity, dtype=np.float64)
            vb = np.asarray(body_b.velocity, dtype=np.float64)
            rv = va - vb
            vn_post = float(np.dot(rv, np.array(normal)))
            min_vn_post = min(min_vn_post, vn_post)
            mu = rec.get('mu_used', 0.0)
            if rec['jn_Ns'] > 0.0 and rec['mode'] != 'still':
                max_cone_violation = max(
                    max_cone_violation,
                    max(0.0, abs(rec['jt_Ns'])
                        - mu * rec['jn_Ns'] - 1e-15))
            if rec['mode'] == 'stick':
                vt = rv - vn_post * np.array(normal)
                max_stick_vt_post = max(max_stick_vt_post,
                                        float(np.linalg.norm(vt)))
        require(min_vn_post >= -1e-9, 'contact_separation_violation')
        require(max_stick_vt_post <= 1e-9, 'contact_stick_violation')
        anchor_tick = -contact['ground']
        comp.ground_anchor_impulse = comp.ground_anchor_impulse + anchor_tick
        e_stab = -w_contact_ke + d_friction + d_impact_physical
        return {'records': records, 'iterations': iterations,
                'gs_residual_N_s': max_jn, 'w_contact_ke_j': w_contact_ke,
                'd_friction_j': d_friction,
                'd_impact_physical_j': d_impact_physical,
                'e_stab_j': e_stab,
                'jn_applied_total_N_s': jn_applied_total,
                'impulse_trapezoid_work_j': impulse_trapezoid_work,
                'contact_residuals': {
                    'min_jn_N_s': min_jn,
                    'min_vn_post_m_per_s': min_vn_post,
                    'max_cone_violation_N_s': max_cone_violation,
                    'max_stick_vt_post_m_per_s': max_stick_vt_post},
                'active_pairs': len(active), 'contact': contact,
                'anchor_tick': anchor_tick}

    # -- snapshot bookkeeping ----------------------------------------------------
    def _component_ke(self, comp):
        ke = float((0.5 * comp.masses[:, None] * comp.v ** 2).sum())
        if not comp.plate.pinned:
            ke += 0.5 * comp.plate.mass_kg * float(np.dot(
                comp.plate.velocity, comp.plate.velocity))
        return ke

    def _scaffold_energy(self, comp):
        diff = comp.x[comp.edge_arr[:, 0]] - comp.x[comp.edge_arr[:, 1]]
        lengths = np.linalg.norm(diff, axis=1)
        return float(((lengths - comp.rest_lengths) ** 2).sum()
                     / (2.0 * XPBD_COMPLIANCE_M_PER_N))

    def _project(self, comp, h):
        """XPBD edge projection (M03 scaffold pattern); A6: the sweep loop
        is TOLERANCE-DRIVEN (max edge violation <= XPBD_TOL_M, cap
        XPBD_ITERATIONS_CAP) so the solver's algebraic error stays below
        the O(h^2) truncation scale and cannot floor the refinement study.
        Time never advances inside this loop."""
        alpha_tilde = XPBD_COMPLIANCE_M_PER_N / (h * h)
        lam = np.zeros(len(comp.edge_list))
        for _ in range(XPBD_ITERATIONS_CAP):
            max_c = 0.0
            for e, (a1, a2) in enumerate(comp.edge_list):
                d = comp.x[a2] - comp.x[a1]
                length = float(np.linalg.norm(d))
                if length == 0.0:
                    continue
                grad = d / length
                cc = length - comp.rest_lengths[e]
                max_c = max(max_c, abs(cc))
                w_sum = comp.inv_masses[a1] + comp.inv_masses[a2]
                dlam = (-cc - alpha_tilde * lam[e]) / (w_sum + alpha_tilde)
                lam[e] += dlam
                comp.x[a1] -= comp.inv_masses[a1] * dlam * grad
                comp.x[a2] += comp.inv_masses[a2] * dlam * grad
            if max_c <= XPBD_TOL_M:
                break

    # -- the single writer ---------------------------------------------------------
    def step(self, tick):
        # The order guard anchors on the FROZEN LITERAL (prereg: "1.
        # pressure -> 2. material -> 3. contact"); a copy that permutes its
        # own module constants is still caught by this literal.
        require(tuple(self.declaration['order'])
                == ('pressure', 'material', 'contact'),
                'declared_order_mismatch')
        require(digest({**self.declaration, 'dt_s': DT_S,
                        'substeps_per_tick': N_SUB}) == DECLARED_DIGEST,
                'declared_order_mismatch')
        require(tick == self.tick, 'tick_sequence_invalid')
        comp_rows = {}
        for comp in self.components:
            comp_rows[comp.component_id] = self._step_component(comp, tick)
        self.tick = tick + 1
        world_row = {'tick': tick, 'dt_s': self.dt_s,
                     'substeps': self.n_sub, 'order': list(DECLARED_ORDER),
                     'order_digest': self.order_digest,
                     'components': comp_rows}
        self.ticks.append(world_row)
        return world_row

    def _step_component(self, comp, tick):
        h = self.dt_s / self.n_sub
        if self.schedule is not None:
            dp = float(self.schedule(tick))
        else:
            dp = float(PRESS_SCHEDULE.get(tick, 0.0))
        v_mem_start = comp.v.copy()
        v_plate_start = comp.plate.velocity.copy()
        ke_start = self._component_ke(comp)
        e_prev = ke_start + self._scaffold_energy(comp) + comp.U_mat
        u_mat_prev = comp.U_mat
        u_scaff_prev = self._scaffold_energy(comp)
        agg = {'w_press_j': 0.0, 'w_grav_j': 0.0, 'w_mat_on_plate_j': 0.0,
               'w_in_mat_j': 0.0, 'q_mat_tick_j': 0.0, 'w_contact_ke_j': 0.0,
               'd_friction_j': 0.0, 'd_impact_physical_j': 0.0,
               'e_stab_j': 0.0, 'jn_applied_total_N_s': 0.0,
               'impulse_trapezoid_work_j': 0.0,
               'projection_exchange_j': 0.0,
               'g_imp_mem': np.zeros(3), 'g_imp_plate': np.zeros(3),
               'iterations': 0, 'gs_residual': 0.0, 'active_pairs': 0,
               'contact': {'membrane': np.zeros(3), 'plate': np.zeros(3),
                           'ground': np.zeros(3)},
               'anchor_tick': np.zeros(3), 'mat_imp': 0.0, 'contacts': [],
               'delta_p_pa': dp,
               'contact_residuals': None}
        for sub in range(self.n_sub):
            ph1 = self._phase_pressure_and_gravity(comp, dp, h)
            ph2 = self._phase_material(comp, h)
            ph3 = self._phase_contact(comp, h)
            ke_pre_proj = self._component_ke(comp)
            us_pre_proj = self._scaffold_energy(comp)
            # integrate positions with the post-contact velocity (ONE pass)
            x_pre = comp.x.copy()
            comp.x = comp.x + comp.v * h
            comp.plate.x = comp.plate.x + comp.plate.velocity * h
            # XPBD projection (declared constraint response): its energy
            # exchange is RECORDED as a first-class ledger term (A3)
            self._project(comp, h)
            comp.v = (comp.x - x_pre) / h
            proj_exchange = ((self._component_ke(comp) - ke_pre_proj)
                             + (self._scaffold_energy(comp) - us_pre_proj))
            agg['w_press_j'] += ph1['w_press_j']
            agg['w_grav_j'] += ph1['w_grav_j']
            agg['g_imp_mem'] += ph1['gravity_impulse_mem']
            agg['g_imp_plate'] += ph1['gravity_impulse_plate']
            agg['w_mat_on_plate_j'] += ph2['w_mat_on_plate_j']
            agg['w_in_mat_j'] += ph2['w_in_mat_j']
            agg['q_mat_tick_j'] += ph2['q_mat_j']
            agg['mat_imp'] += ph2['mat_impulse_n_s']
            agg['w_contact_ke_j'] += ph3['w_contact_ke_j']
            agg['d_friction_j'] += ph3['d_friction_j']
            agg['d_impact_physical_j'] += ph3['d_impact_physical_j']
            agg['e_stab_j'] += ph3['e_stab_j']
            agg['jn_applied_total_N_s'] += ph3['jn_applied_total_N_s']
            agg['impulse_trapezoid_work_j'] += \
                ph3['impulse_trapezoid_work_j']
            agg['projection_exchange_j'] += proj_exchange
            cr = ph3['contact_residuals']
            if agg['contact_residuals'] is None:
                agg['contact_residuals'] = cr
            else:
                agg['contact_residuals'] = {
                    'min_jn_N_s': min(agg['contact_residuals']['min_jn_N_s'],
                                      cr['min_jn_N_s']),
                    'min_vn_post_m_per_s':
                        min(agg['contact_residuals']['min_vn_post_m_per_s'],
                            cr['min_vn_post_m_per_s']),
                    'max_cone_violation_N_s':
                        max(agg['contact_residuals']['max_cone_violation_N_s'],
                            cr['max_cone_violation_N_s']),
                    'max_stick_vt_post_m_per_s':
                        max(agg['contact_residuals'][
                                'max_stick_vt_post_m_per_s'],
                            cr['max_stick_vt_post_m_per_s'])}
            agg['iterations'] += ph3['iterations']
            agg['gs_residual'] = max(agg['gs_residual'],
                                     ph3['gs_residual_N_s'])
            agg['active_pairs'] += ph3['active_pairs']
            for name in ('membrane', 'plate', 'ground'):
                agg['contact'][name] += ph3['contact'][name]
            agg['anchor_tick'] += ph3['anchor_tick']
            for rec in ph3['records']:
                agg['contacts'].append({
                    'pair_key': [str(k) for k in rec['pair_key']],
                    'jn_N_s': rec['jn_Ns'], 'jt_N_s': rec['jt_Ns'],
                    'mode': rec['mode'], 'gap_m': rec['gap_m'],
                    'normal': list(rec['normal'])})
        # end-of-tick snapshot (M05 A1 rule: energies at THIS configuration)
        ke = self._component_ke(comp)
        u_scaff = self._scaffold_energy(comp)
        u_mat = comp.U_mat
        e_mech = ke + u_scaff + u_mat
        turnover = (abs(agg['w_press_j']) + abs(agg['w_grav_j'])
                    + abs(agg['w_mat_on_plate_j'])
                    + abs(agg['w_contact_ke_j']) + ke)
        bound = (RESIDUAL_TURNOVER_FRACTION * turnover + u_mat + u_mat_prev
                 + u_scaff + u_scaff_prev + 1e-9)
        # Whole-system energy ledger (A5, Astra round-6 R3):
        # R_E = E_{n+1} - E_n - W_external + D_viscoelastic + D_friction
        #       + D_impact - projection_exchange
        # E includes ALL modeled reservoirs (kinetic + scaffold + Maxwell
        # stored); the declared source is an actuator (W_press external, no
        # modeled reservoir -> no double counting); fixed anchors do no
        # work; D_impact is the PHYSICAL inelastic normal loss (A7) and
        # E_stab the recorded numerical stabilization exchange (bias
        # (inelastic normal loss + declared bias injection, measured, never
        # injection/withdrawal) -- neither hides the other; projection_
        # exchange is the
        # recorded positional-correction energy term. Expected closure
        # scale: the declared Maxwell driver gap (~1e-9 J).
        d_impact = agg['d_impact_physical_j']
        e_stab = agg['e_stab_j']
        w_external = agg['w_press_j'] + agg['w_grav_j']
        residual = e_mech - e_prev - w_external + agg['q_mat_tick_j'] \
            + agg['d_friction_j'] + d_impact - e_stab \
            - agg['projection_exchange_j']
        require(abs(residual) <= bound, 'unexplained_energy')
        # momentum ledger (Amendment A1 (iii)): recorded terms, 1e-12 identity
        mem_dv = (comp.masses[:, None] * (comp.v - v_mem_start)).sum(axis=0)
        proj_delta_mem = mem_dv - (agg['g_imp_mem']
                                   + agg['contact']['membrane'])
        plate_dv = comp.plate.mass_kg * (comp.plate.velocity - v_plate_start)
        mat_imp_vec = np.array([agg['mat_imp'], 0.0, 0.0])
        plate_terms = (agg['g_imp_plate'] + agg['contact']['plate']
                       + mat_imp_vec)
        proj_delta_plate = plate_dv - plate_terms
        require(float(np.linalg.norm(proj_delta_plate)) <= 1e-12,
                'momentum_ledger_open')
        anchor_resid = float(np.linalg.norm(
            agg['anchor_tick'] + agg['contact']['ground']))
        require(anchor_resid <= 1e-12, 'anchor_reaction_imbalance')
        row = {
            'tick': tick,
            'delta_p_pa': dp,
            'membrane_volume_m3': pm.Membrane(
                comp.x, comp.membrane.triangles,
                comp.membrane.name).signed_volume(),
            'membrane_com_m': [float(c) for c in
                               (comp.x * comp.masses[:, None]).sum(axis=0)
                               / comp.masses.sum()],
            'plate_x_m': float(comp.plate.x[:, 0].mean()),
            'plate_v_m_per_s': [float(c) for c in comp.plate.velocity],
            'membrane_max_speed_m_per_s': float(np.abs(comp.v).max()),
            'F_N': comp.F, 'U_mat_j': u_mat, 'Q_mat_j': comp.Q_mat,
            'W_in_mat_j': comp.W_in_mat,
            'e_kinetic_j': ke, 'u_scaffold_j': u_scaff,
            'e_mechanical_j': e_mech,
            'w_press_j': agg['w_press_j'], 'w_grav_j': agg['w_grav_j'],
            'w_mat_on_plate_j': agg['w_mat_on_plate_j'],
            'w_in_mat_tick_j': agg['w_in_mat_j'],
            'q_mat_tick_j': agg['q_mat_tick_j'],
            'w_contact_ke_j': agg['w_contact_ke_j'],
            'projection_exchange_j': agg['projection_exchange_j'],
            'w_external_j': w_external,
            'D_viscoelastic_j': agg['q_mat_tick_j'],
            'D_friction_j': agg['d_friction_j'],
            'D_impact_j': d_impact,
            'E_stab_j': e_stab,
            'impulse_trapezoid_work_j': agg['impulse_trapezoid_work_j'],
            'jn_applied_total_N_s': agg['jn_applied_total_N_s'],
            'contact_residuals': agg['contact_residuals'],
            'residual_r_j': residual, 'residual_bound_j': bound,
            'residual_within_bound': bool(abs(residual) <= bound),
            'projection_delta_mem_N_s': [float(c) for c in proj_delta_mem],
            'ground_anchor_impulse_N_s': [float(c) for c in
                                          comp.ground_anchor_impulse],
            'wall_reaction_impulse_N_s': [float(c) for c in
                                          comp.wall_reaction_impulse
                                          + (-mat_imp_vec)],
            'contact_iterations': agg['iterations'],
            'contact_gs_residual_N_s': agg['gs_residual'],
            'contact_active_pairs': agg['active_pairs'],
            'contacts': agg['contacts'],
            'state_hash': None,
        }
        comp.wall_reaction_impulse = comp.wall_reaction_impulse \
            + (-mat_imp_vec)
        row['state_hash'] = digest({k: row[k] for k in sorted(row)
                                    if k != 'state_hash'})
        return row

    def run(self, ticks, store_geometry_from=None):
        for tick in range(ticks):
            row = self.step(tick)
            if store_geometry_from is not None \
                    and tick >= store_geometry_from:
                for cid, comp_row in row['components'].items():
                    comp = self._component(cid)
                    comp_row['membrane_positions_m'] = [
                        [float(c) for c in v] for v in comp.x]
                    comp_row['plate_vertices_m'] = [
                        [float(c) for c in v] for v in comp.plate.x]
        return self.ticks

    def _component(self, component_id):
        for comp in self.components:
            if comp.component_id == component_id:
                return comp
        raise ValueError('component_unknown')


# ---- versioned state document (validated by M01 UNMODIFIED) -------------------

def state_document(world, revision):
    """chimera.material_state.v1 snapshot of the owned world at a tick."""
    regions = []
    matter = []
    for comp in world.components:
        cid = comp.component_id
        regions.append({
            'id': f'membrane_{cid}', 'kind': 'region', 'parent': None,
            'rest_geometry': {'vertices_m': [[float(c) for c in v]
                                             for v in comp.rest],
                              'triangles': [[int(i) for i in t] for t in
                                            comp.membrane.triangles],
                              'frame': 'rest'},
            'current_geometry': {'vertices_m': [[float(c) for c in v]
                                                for v in comp.x],
                                 'triangles': [[int(i) for i in t] for t in
                                               comp.membrane.triangles],
                                 'frame': 'current'},
            'matter_claims': [{'matter_id': f'mat_{cid}_membrane',
                               'role': 'owner'}],
            'sources': [f'MAT2-M07 integrated world; membrane {cid}'],
            'ports': [{'id': 'port:contact_patch', 'protocol':
                       'normal_contact', 'unit': 'Pa'}]})
        regions.append({
            'id': f'plate_{cid}', 'kind': 'region', 'parent': None,
            'rest_geometry': {'vertices_m': [[float(c) for c in v]
                                             for v in comp.plate.rest],
                              'triangles': [list(t) for t in
                                            comp.plate.triangles],
                              'frame': 'rest'},
            'current_geometry': {'vertices_m': [[float(c) for c in v]
                                                for v in comp.plate.x],
                                 'triangles': [list(t) for t in
                                               comp.plate.triangles],
                                 'frame': 'current'},
            'matter_claims': [{'matter_id': f'mat_{cid}_plate',
                               'role': 'owner'}],
            'sources': [f'MAT2-M07 integrated world; plate {cid}'],
            'ports': [{'id': 'port:contact_patch', 'protocol':
                       'normal_contact', 'unit': 'Pa'},
                      {'id': 'port:maxwell_mount', 'protocol':
                       'tension_shear', 'unit': 'N'}]})
        regions.append({
            'id': f'ground_{cid}', 'kind': 'region', 'parent': None,
            'rest_geometry': {'vertices_m': [[float(c) for c in v]
                                             for v in comp.ground.rest],
                              'triangles': [list(t) for t in
                                            comp.ground.triangles],
                              'frame': 'rest'},
            'current_geometry': {'vertices_m': [[float(c) for c in v]
                                                for v in comp.ground.x],
                                 'triangles': [list(t) for t in
                                               comp.ground.triangles],
                                 'frame': 'current'},
            'matter_claims': [{'matter_id': f'mat_{cid}_ground',
                               'role': 'owner'}],
            'sources': [f'MAT2-M07 integrated world; pinned ground {cid}'],
            'ports': [{'id': 'port:support', 'protocol': 'normal_contact',
                       'unit': 'Pa'}]})
        matter.extend([
            {'id': f'mat_{cid}_membrane', 'mass_kg': MEMBRANE_MASS_KG,
             'provenance': 'declared membrane mass (PREREGISTRATION)'},
            {'id': f'mat_{cid}_plate', 'mass_kg': PLATE_MASS_KG,
             'provenance': 'declared plate mass (PREREGISTRATION)'},
            {'id': f'mat_{cid}_ground', 'mass_kg': 0.0,
             'provenance': 'pinned support shell; declared massless anchor'}])
    k, c = world.components[0].maxwell_element()
    doc = {
        'schema': material_state.SCHEMA,
        'revision': int(revision),
        'object_id': 'mat2_m07_integrated_world',
        'regions': regions,
        'matter': matter,
        'directions': [
            {'id': 'dir:maxwell_axis', 'region_id': 'plate_' +
             world.components[0].component_id,
             'axis': [1.0, 0.0, 0.0], 'frame': 'rest', 'history': [
                 {'revision': 0, 'state': 'declared Maxwell mount axis'}]},
            {'id': 'dir:gravity', 'region_id': 'membrane_' +
             world.components[0].component_id,
             'axis': [0.0, 0.0, -1.0], 'frame': 'rest', 'history': [
                 {'revision': 0, 'state': 'declared gravity direction'}]}],
        'laws': [
            {'id': 'law:pressure_source', 'kind': 'pressure_deformation',
             'regions': [f'membrane_{world.components[0].component_id}'],
             'parameters': {'schedule_pa_ticks_1_40': 60.0,
                            'max_delta_p_pa': 5000.0},
             'provenance': 'M03 declared-source traction (prereg)'},
            {'id': 'law:maxwell_mount', 'kind': 'pressure_deformation',
             'regions': [f'plate_{world.components[0].component_id}'],
             'parameters': {'k_N_per_m': k, 'c_N_s_per_m': c},
             'provenance': 'M04 exact Maxwell element (prereg)'},
            {'id': 'law:local_contact', 'kind': 'pressure_deformation',
             'regions': [f'membrane_{world.components[0].component_id}',
                         f'plate_{world.components[0].component_id}',
                         f'ground_{world.components[0].component_id}'],
             'parameters': {'thickness_m': THICKNESS_M,
                            'margin_m': CONTACT_MARGIN_M,
                            'restitution': lc.RESTITUTION},
             'provenance': 'M06 local contact solve (prereg)'}],
        'contacts': [
            {'id': f'contact:membrane_plate_'
                   f'{world.components[0].component_id}',
             'endpoints': [
                 {'region_id': f'membrane_'
                               f'{world.components[0].component_id}',
                  'port': 'port:contact_patch'},
                 {'region_id': f'plate_{world.components[0].component_id}',
                  'port': 'port:contact_patch'}],
             'state': 'touching' if world.ticks else 'separated'}],
        'bonds': [],
        'provenance': {
            'task': 'MAT2-M07',
            'preregistration': 'PREREGISTRATION.md (this directory)',
            'note': 'one state owner snapshot; contact state is the declared '
                    'final-tick declaration of the membrane-plate patch'},
    }
    material_state.validate_material_state(doc)
    return doc
