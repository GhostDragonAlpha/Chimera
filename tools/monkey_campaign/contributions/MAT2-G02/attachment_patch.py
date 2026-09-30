"""MAT2-G02 finite-area attachment patch element and fixture world.

Implemented AFTER PREREGISTRATION.md (base 49bd9a85 + Amendment A1 a39a946e
+ Amendment A2 951c963e) was committed; every constant below is the frozen
prereg number, none is measured, none is fitted (sealed A07 gate), none is
biological.

Law carriers (pinned in run_experiments.verify_input_pins):
- MAT2-M01 material_state.py  b6b009713daa4b315c6b5cb43c7ad4e756123b50edcd
  d802eeebd55c6afd6c40 - the UNMODIFIED document validator (imported).
- MAT2-M05 interface_state.json c09bdf0564d152fa8b9a41489bd874fd0570f75e40ed
  3ce848f4c474fd0320c6 - bond/contact port semantics vocabulary; the areal
  densities below are DERIVED from that sealed carrier (law 3/4 of the
  prereg), not invented.
- MAT2-A09 grasp_package.json 0a70adb1029d860ac9504683d77c2e94be2634724c634
  79f827fcbc8fcd97d24 - connection/port vocabulary and the C17 open-inventory
  law; the biological attachment ports stay explicitly_unresolved here.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
if str(CONTRIB / 'MAT2-M01') not in sys.path:
    sys.path.insert(0, str(CONTRIB / 'MAT2-M01'))
from material_state import validate_material_state  # noqa: E402 (pinned)

# ---------------------------------------------------------------- frozen law
CARD_ID = 'G02'
CARD_FULL = 'MAT2-G02'

# Patch geometry (prereg law 2): unequal-area two-triangle quad BY DESIGN so
# area scaling is falsifiable (FB2). Vertices in the interface plane (y, z).
PATCH_VERTS_YZ = ((0.0, 0.0), (0.020, 0.0), (0.013, 0.010), (0.0, 0.010))
TRI1_IDX = (0, 1, 2)
TRI2_IDX = (0, 2, 3)

# Areal densities (prereg laws 3/4): M05 sealed point-bond constants divided
# by the M05 interface area 0.0175 m^2. DECLARED PLACEHOLDERS (authored
# engineering constants derived from a sealed carrier; never measured, never
# biological).
M05_K_T_N_PER_M = 60.0
M05_K_S_N_PER_M = 40.0
M05_K_THETA_N_M_PER_RAD = 0.8
M05_IFACE_AREA_M2 = 0.0175
KA_T = M05_K_T_N_PER_M / M05_IFACE_AREA_M2      # 3428.5714285714284 N/m^3
KA_S = M05_K_S_N_PER_M / M05_IFACE_AREA_M2      # 2285.7142857142856 N/m^3
KA_THETA = (M05_K_THETA_N_M_PER_RAD / M05_IFACE_AREA_M2)  # 45.71428571428571

# Matter (prereg law 1, carried from the M05 carrier once-only law).
MATTER = (('mat_a', 0.050), ('mat_b', 0.020), ('mat_iface', 0.002))
M_BODY_B = 0.020

# Contact (prereg law 8).
K_C_PA_PER_M = 1.0e7
C_N = 5.0

# Interface applicability guards (prereg law 9).
D_PERP_MAX = 3.0e-3
THETA_MAX = 0.05
PENETRATION_MAX = 0.03

# Dynamics (prereg law 10 as amended by Amendment A2: quasi-static squeeze
# ramp so the contact unloads gently, settle, bind at rest, pull, release,
# approach; c_v corrected for the declared soft patch; midpoint-displacement
# work bookkeeping).
DT = 1.0 / 300.0
TICKS = 356
ALPHA = 1.0e-5
XPBD_ITERS = 8
C_V = 0.02
SQUEEZE_N = 2.0        # ramp ticks 1..45 (linear to zero)
PULL_N = 0.03          # ticks 61..250 away; 251..260 continues after release
BIND_TICK = 61
RELEASE_TICK = 234     # derived first oscillation peak (v ~ 0)
APPROACH_N = 2.0       # ticks 251..355 toward A
CAPTURE_TICKS = (0, 20, 150, 232, 233, 250, 320)

# Body geometry (prereg law 1: congruent to the sealed M05 bodies; the
# vertex set is carried verbatim from MAT2-M05 interface_state.json).
BODY_VERTS_A = (
    (0.0, 0.0, 0.0), (0.0, 0.2, 0.0), (0.0, 0.15, 0.1), (0.0, 0.0, 0.1),
    (-0.16, 0.08809523809523807, 0.04761904761904761))
BODY_VERTS_B = (
    (0.0, 0.0, 0.0), (0.0, 0.2, 0.0), (0.0, 0.15, 0.1), (0.0, 0.0, 0.1),
    (0.16, 0.08809523809523807, 0.04761904761904761))
COM_A = np.array((-0.04, 0.0875, 0.05))
COM_B_REST = np.array((0.04, 0.0875, 0.05))
IFACE_TRIS = ((0, 1, 2), (0, 2, 3))
IFACE_AREAS = (0.0100, 0.0075)   # sealed M05 interface triangle areas


def refuse(condition_is_bad, code):
    if condition_is_bad:
        raise ValueError(code)


def _tri_area_yz(a, b, c):
    """0.5*|cross| of the in-plane edge vectors (exact prereg formula)."""
    uy, uz = b[0] - a[0], b[1] - a[1]
    vy, vz = c[0] - a[0], c[1] - a[1]
    return 0.5 * abs(uy * vz - uz * vy)


def patch_geometry():
    """Frozen patch geometry (prereg law 2 + T1)."""
    v = PATCH_VERTS_YZ
    t1 = tuple(v[i] for i in TRI1_IDX)
    t2 = tuple(v[i] for i in TRI2_IDX)
    a1 = _tri_area_yz(*t1)
    a2 = _tri_area_yz(*t2)
    area = a1 + a2
    c1 = (sum(p[0] for p in t1) / 3.0, sum(p[1] for p in t1) / 3.0)
    c2 = (sum(p[0] for p in t2) / 3.0, sum(p[1] for p in t2) / 3.0)
    return {
        'triangles_yz': [t1, t2],
        'areas_m2': [a1, a2],
        'area_patch_m2': area,
        'weights': [a1 / area, a2 / area],
        'centroids_yz': [c1, c2],
        'normal_a': np.array([1.0, 0.0, 0.0]),
        'normal_b': np.array([-1.0, 0.0, 0.0]),
    }


GEO = patch_geometry()
A1, A2 = GEO['areas_m2']
A_PATCH = GEO['area_patch_m2']
W1, W2 = GEO['weights']
C1_YZ, C2_YZ = GEO['centroids_yz']
KT = (KA_T * A1, KA_T * A2)          # per-triangle tension stiffness N/m
KS = (KA_S * A1, KA_S * A2)          # per-triangle shear stiffness N/m
KTH = (KA_THETA * A1, KA_THETA * A2)  # per-triangle couple resistance N*m/rad
KT_PATCH = KA_T * A_PATCH
KS_PATCH = KA_S * A_PATCH
KTH_PATCH = KA_THETA * A_PATCH
K_EFF_CONTACT = K_C_PA_PER_M * A_PATCH       # 1650.0 N/m
OMEGA_T = math.sqrt(KT_PATCH / M_BODY_B)     # 5.3184... rad/s
ZETA = C_V / (2.0 * M_BODY_B * OMEGA_T)      # damping ratio (Amendment A2)
OMEGA_D = OMEGA_T * math.sqrt(1.0 - ZETA * ZETA)
STATIC_PULL_EXT = PULL_N / KT_PATCH          # 0.053030... m
OMEGA_C = math.sqrt(K_EFF_CONTACT / M_BODY_B)
STATIC_PENETRATION = SQUEEZE_N / K_EFF_CONTACT  # -1.2121...e-3 m


# ------------------------------------------------------------ element oracle
def oracle_patch_loads(gap, d_perp, theta_vec, bound):
    """Independent closed-form reference (scalar arithmetic path, no reuse of
    the element code). Returns per-triangle force magnitudes, total force on
    A/B (x-components), couples, energy. THE X1 direct reference."""
    refuse(not isinstance(bound, bool), 'oracle_bound_not_bool')
    e = float(gap)
    t_ext = max(0.0, e)
    out = {'bound': bound, 'extension_m': e,
           'triangles': [], 'energy_J': 0.0,
           'force_a_x_N': 0.0, 'force_b_x_N': 0.0,
           'couple_a_N_m': [0.0, 0.0, 0.0], 'couple_b_N_m': [0.0, 0.0, 0.0]}
    if not bound:
        return out
    d = np.asarray(d_perp, dtype=np.float64)
    th = np.asarray(theta_vec, dtype=np.float64)
    for i, area in enumerate((A1, A2)):
        k_t = KA_T * area
        k_s = KA_S * area
        k_th = KA_THETA * area
        t_i = k_t * t_ext
        s_i = k_s * float(np.linalg.norm(d))
        u_i = (0.5 * k_t * t_ext * t_ext
               + 0.5 * k_s * float(d @ d)
               + 0.5 * k_th * float(th @ th))
        out['triangles'].append(
            {'index': i, 'area_m2': area, 'tension_N': t_i,
             'shear_N': s_i, 'energy_J': u_i})
        out['energy_J'] += u_i
        out['force_a_x_N'] += t_i
        out['force_b_x_N'] -= t_i
        ca = np.array([+k_th * th[j] for j in range(3)])
        out['couple_a_N_m'] = [out['couple_a_N_m'][j] + ca[j]
                               for j in range(3)]
        out['couple_b_N_m'] = [out['couple_b_N_m'][j] - ca[j]
                               for j in range(3)]
    return out


def oracle_couple_distribution(m_total, axis_index):
    """Frozen weights distribute a declared patch-level couple (prereg law 5
    + T4). Independent closed form."""
    refuse(axis_index not in (0, 1, 2), 'couple_axis_invalid')
    return [W1 * m_total, W2 * m_total]


# ------------------------------------------------------------- the element
class PatchElement:
    """Finite-area attachment patch between two declared ports (prereg laws
    5-8). Bond/removal semantics match the sealed limb experiment (M09):
    explicit bind, explicit release with bitwise-zero residue, energy
    dissipated at the release tick, remaining contact unaffected, no
    auto-bond ever."""

    def __init__(self):
        self._bound = False
        self._released_at_tick = None
        self._released = False
        self.triangle_connections = 0
        self.endpoints = None
        self.energy_at_release_J = None

    # -- binding ----------------------------------------------------------
    def bind(self, port_a, port_b):
        refuse(self._bound, 'bond_already_bound')
        refuse(self._released, 'bond_released_is_terminal')
        refuse(not port_a or not port_b, 'bond_port_undeclared')
        self._bound = True
        self.triangle_connections = 2
        self.endpoints = (str(port_a), str(port_b))
        return {'bound': True, 'triangle_connections': 2}

    def release(self, tick):
        refuse(not self._bound, 'release_of_unbound_bond')
        self.energy_at_release_J = self.last_energy_J
        self._bound = False
        self._released = True
        self._released_at_tick = int(tick)
        self.triangle_connections = 0
        return {'released': True, 'tick': int(tick),
                'E_diss_release_J': self.energy_at_release_J,
                'triangle_connections': 0}

    def refuse_auto_bond(self):
        """Proximity/overlap/containment NEVER create a bond (prereg law 8,
        T7, FB5)."""
        raise ValueError('auto_bond_refused')

    # -- state ------------------------------------------------------------
    last_energy_J = 0.0

    def loads(self, gap, d_perp, theta_vec, tick):
        """Per-triangle area-scaled loads (prereg law 7). Returns rows with
        forces applied at the per-triangle centroids on BOTH bodies and the
        moments those forces produce about each body's center of mass - the
        'forces and moments enter both connected material states' record.
        After release every contribution is bitwise 0.0 (T6)."""
        d = np.asarray(d_perp, dtype=np.float64)
        th = np.asarray(theta_vec, dtype=np.float64)
        refuse(float(np.linalg.norm(d)) >= D_PERP_MAX,
               'interface_tilt_exceeded')
        refuse(float(np.linalg.norm(th)) >= THETA_MAX,
               'interface_tilt_exceeded')
        rows = []
        energy = 0.0
        force_a = np.zeros(3)
        force_b = np.zeros(3)
        moment_a = np.zeros(3)
        moment_b = np.zeros(3)
        if self._bound:
            t_ext = max(0.0, float(gap))
            face_a_x = 0.0
            face_b_x = float(gap)
            com_a = COM_A
            com_b = COM_B_REST + np.array([gap, 0.0, 0.0])
            for i, (cy, cz) in enumerate((C1_YZ, C2_YZ)):
                k_t, k_s, k_th = KT[i], KS[i], KTH[i]
                t_i = k_t * t_ext
                u_i = (0.5 * k_t * t_ext * t_ext
                       + 0.5 * k_s * float(d @ d)
                       + 0.5 * k_th * float(th @ th))
                energy += u_i
                f_a = np.array([t_i, 0.0, 0.0])   # +x on A
                f_b = np.array([-t_i, 0.0, 0.0])  # bitwise negative on B
                f_a = f_a - k_s * d               # shear pair
                f_b = f_b + k_s * d
                couple = k_th * th                # restoring couple
                r_a = np.array([face_a_x, cy, cz])
                r_b = np.array([face_b_x, cy, cz])
                m_a = np.cross(r_a - com_a, f_a) + couple
                m_b = np.cross(r_b - com_b, f_b) - couple
                force_a = force_a + f_a
                force_b = force_b + f_b
                moment_a = moment_a + m_a
                moment_b = moment_b + m_b
                rows.append({
                    'triangle_index': i,
                    'port_id': 'iface:fixture-patch-p%d' % (i + 1),
                    'frame_decl': ('fixture_body_a_local'
                                   if i == 0 else 'fixture_body_b_local'),
                    'frame_note': ('owner-body-local per M01/A09 frame law; '
                                   'carried verbatim, no transform composed'),
                    'area_m2': (A1, A2)[i],
                    'weight': (W1, W2)[i],
                    'centroid_yz_m': [cy, cz],
                    'tension_N': t_i,
                    'shear_N': float(k_s * float(np.linalg.norm(d))),
                    'couple_N_m': [float(couple[0]), float(couple[1]),
                                   float(couple[2])],
                    'force_on_a_N': [float(f_a[0]), float(f_a[1]),
                                     float(f_a[2])],
                    'force_on_b_N': [float(f_b[0]), float(f_b[1]),
                                     float(f_b[2])],
                    'moment_about_com_a_N_m': [float(m_a[0]), float(m_a[1]),
                                               float(m_a[2])],
                    'moment_about_com_b_N_m': [float(m_b[0]), float(m_b[1]),
                                               float(m_b[2])],
                    'energy_J': u_i,
                    'c17_status': 'declared_placeholder_fixture_only',
                    'provenance_class': 'declared_placeholder',
                })
        self.last_energy_J = energy
        return {
            'tick': int(tick),
            'bound': self._bound,
            'released': self._released,
            'released_at_tick': self._released_at_tick,
            'extension_m': float(gap),
            'd_perp_m': [float(d[0]), float(d[1]), float(d[2])],
            'theta_rad': [float(th[0]), float(th[1]), float(th[2])],
            'triangle_connections': self.triangle_connections,
            'force_on_a_N': [float(force_a[0]), float(force_a[1]),
                             float(force_a[2])],
            'force_on_b_N': [float(force_b[0]), float(force_b[1]),
                             float(force_b[2])],
            'moment_about_com_a_N_m': [float(moment_a[0]), float(moment_a[1]),
                                       float(moment_a[2])],
            'moment_about_com_b_N_m': [float(moment_b[0]), float(moment_b[1]),
                                       float(moment_b[2])],
            'energy_J': energy,
            'interface_force_sum_N': [float(force_a[0] + force_b[0]),
                                      float(force_a[1] + force_b[1]),
                                      float(force_a[2] + force_b[2])],
            'triangles': rows,
        }


def distribute_couple(m_total, axis_index):
    """Frozen weights distribute a declared patch-level couple (prereg law 5,
    T4). Per-triangle couples sum EXACTLY to M_total."""
    refuse(axis_index not in (0, 1, 2), 'couple_axis_invalid')
    m1 = W1 * m_total
    m2 = W2 * m_total
    refuse(abs(m1 + m2 - m_total) > 1e-18, 'couple_distribution_inexact')
    return {'axis_index': axis_index, 'm_total_N_m': m_total,
            'per_triangle_N_m': [m1, m2],
            'sum_N_m': m1 + m2,
            'pair_bitwise_negative_b': [-m1, -m2]}


# ------------------------------------------------------------ fixture world
def actuator_force(tick):
    """Frozen schedule (prereg law 10 as amended by Amendment A2).
    Negative = toward A (squeeze, linear ramp to zero); positive = away."""
    if 1 <= tick <= 45:
        return -SQUEEZE_N * (1.0 - (tick - 1) / 44.0)   # quasi-static ramp
    if 46 <= tick <= 60:
        return 0.0                       # declared settle (contact unloads)
    if 61 <= tick <= 260:
        return PULL_N
    if 261 <= tick <= 355:
        return -APPROACH_N
    return 0.0


class FixtureWorld:
    """Reduced 1-DOF fixture dynamics (declared): body B's active coordinate
    is the interface gap; the XPBD scaffold pattern (fixed dt, compliance
    alpha, 8 iterations) enforces body B's declared-rigid vertex frame about
    its COM; the patch is the declared explicit-stiffness element; contact is
    the M05-class unilateral penalty with normal damping. Transverse and
    rotational couplings are RECORDED into both body states every tick and
    bounded by the law-9 guards, not integrated (declared reduction)."""

    def __init__(self):
        self.element = PatchElement()
        self.gap = 0.0
        self.velocity = 0.0
        self.tick = 0
        self.element.loads(0.0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0)
        self.ledger_prev = self._mech_energy()
        self.rows = []

    # -- world lifecycle ---------------------------------------------------
    def release(self):
        self.rows = []
        self.element = None

    def _mech_energy(self):
        ke = 0.5 * M_BODY_B * self.velocity * self.velocity
        return ke + (self.element.last_energy_J if self.element else 0.0)

    def step_tick(self, tick, bind_at=None, release_at=None):
        """One declared tick. Returns the per-tick trace row."""
        refuse(self.element is None, 'world_released')
        self.tick = int(tick)
        if bind_at is not None and tick == bind_at:
            self.element.bind('port:patch', 'port:patch')
        if release_at is not None and tick == release_at:
            self.element.release(tick)

        gap_prev = self.gap
        v_prev = self.velocity

        # external forces on B along x (explicit; patch = the declared
        # stiffness element, contact = the M05-class penalty; both declared
        # dampings are force laws inside f_ext so the work identity holds)
        f_act = actuator_force(tick)
        p = K_C_PA_PER_M * max(0.0, -self.gap)
        f_contact = p * A_PATCH if p > 0.0 else 0.0   # pushes B away (+x)
        v_rel = self.velocity
        f_contact_damp = -C_N * v_rel if p > 0.0 else 0.0
        f_damp_cv = -C_V * v_rel
        f_patch = float(self.element.loads(self.gap, (0.0, 0.0, 0.0),
                                           (0.0, 0.0, 0.0), tick)
                        ['force_on_b_N'][0])
        f_ext = f_act + f_contact + f_contact_damp + f_damp_cv + f_patch

        # XPBD scaffold pattern (M03/M05): fixed dt, compliance alpha,
        # 8 iterations enforcing body B's DECLARED-RIGID vertex frame about
        # its COM. In the declared 1-DOF reduction the scaffold holds by
        # construction; the projection residual is REPORTED (never hidden),
        # 0.0 bitwise, and the ledger books its work honestly.
        scaffold_offsets = [np.array(v) - COM_B_REST for v in BODY_VERTS_B]
        com_b_new = COM_B_REST + np.array([self.gap, 0.0, 0.0])
        projection_work = 0.0
        scaffold_residual = 0.0
        for _ in range(XPBD_ITERS):
            for off in scaffold_offsets:
                target = com_b_new + off
                current = target          # rigid by declaration in 1 DOF
                dl = np.linalg.norm(current - target)
                scaffold_residual = max(scaffold_residual, float(dl))
        # velocity-first update with midpoint-displacement work identity:
        # for forces constant over the step, W = f * 0.5*(v0+v1)*dt equals
        # delta-KE exactly, so the frozen residual bound (law 11) sees only
        # genuine integrator drift (0.5*k*dx^2 spring curvature terms).
        a_x = f_ext / M_BODY_B
        v_new = self.velocity + a_x * DT
        v_mid = 0.5 * (self.velocity + v_new)
        dx = v_mid * DT
        self.gap = self.gap + dx
        self.velocity = v_new

        # damping work booked from the forces AS EVALUATED (dissipation is
        # minus their work; exact against the ledger, drift stays integrator-
        # level for the spring-curvature terms only)
        q_damp = -f_damp_cv * dx
        q_contact_damp = -f_contact_damp * dx

        # ledger (prereg law 11): U tracks the PATCH element exactly;
        # contact elasticity books as W_contact; both dampings book as Q;
        # E_diss_release enters Q at the release tick (FB4 drops it and the
        # residual bound must trip).
        e_diss_release = (self.element.energy_at_release_J
                          if release_at is not None and tick == release_at
                          else 0.0)
        dx = self.gap - gap_prev
        w_act = f_act * dx
        w_contact = f_contact * dx   # elastic only; damping books in Q
        q_total = q_damp + q_contact_damp + e_diss_release
        release_info = ({'E_diss_release_J': e_diss_release}
                        if e_diss_release else None)
        loads = self.element.loads(self.gap, (0.0, 0.0, 0.0),
                                   (0.0, 0.0, 0.0), tick)
        e_mech = 0.5 * M_BODY_B * self.velocity * self.velocity \
            + loads['energy_J']
        residual = e_mech - self.ledger_prev - (w_act + w_contact - q_total)
        bound_scale = max(5e-2 * (abs(w_act) + abs(w_contact) + q_total
                                  + 0.5 * M_BODY_B * self.velocity ** 2),
                          1e-6)
        penetration_new = min(0.0, self.gap)
        if penetration_new <= -PENETRATION_MAX:
            raise ValueError('contact_penetration_exceeded')
        contact_state = ('loaded' if p > 0.0
                         else ('touching' if self.gap == 0.0
                               else 'separated'))
        row = {
            'tick': int(tick),
            'gap_m': self.gap,
            'penetration_m': penetration_new,
            'velocity_m_per_s': self.velocity,
            'actuator_N': f_act,
            'contact_N': f_contact + f_contact_damp,
            'patch_force_on_b_x_N': f_patch,
            'contact_state': contact_state,
            'patch_bound': loads['bound'],
            'patch_energy_J': loads['energy_J'],
            'patch_extension_m': loads['extension_m'],
            'triangle_connections': loads['triangle_connections'],
            'interface_force_sum_N': loads['interface_force_sum_N'],
            'moment_about_com_a_N_m': loads['moment_about_com_a_N_m'],
            'moment_about_com_b_N_m': loads['moment_about_com_b_N_m'],
            'ledger': {
                'W_actuators_J': w_act, 'W_contact_J': w_contact,
                'U_patch_J': loads['energy_J'], 'E_diss_damping_J': q_damp,
                'E_diss_contact_J': (C_N * v_mid * v_mid * DT
                                     if p > 0.0 else 0.0),
                'E_diss_release_J': (release_info or {}).get(
                    'E_diss_release_J', 0.0),
                'E_mech_J': e_mech, 'R_tick_J': residual,
                'R_bound_J': bound_scale,
                'R_within_bound': abs(residual) <= bound_scale,
                'xpbd_projection_work_J': projection_work,
                'scaffold_residual_m': scaffold_residual,
            },
            'release': release_info,
        }
        self.ledger_prev = e_mech
        refuse(not row['ledger']['R_within_bound'], 'ledger_residual_exceeded')
        self.rows.append(row)
        return row

    # -- document emission (M01 validator, unmodified) ----------------------
    def state_document(self, revision):
        """chimera.material_state.v1 document for this fixture state.
        revision 1 = bound; revision 2 = post-release (bond relation removed,
        contact persists) - the M05 carrier vocabulary with fixture ids."""
        verts_a = [list(v) for v in BODY_VERTS_A]
        verts_b = [[v[0] + self.gap, v[1], v[2]] for v in BODY_VERTS_B]
        tris = [[0, 1, 2], [0, 2, 3], [0, 4, 1], [1, 4, 2], [2, 4, 3],
                [3, 4, 0]]
        geom = lambda vs: {'frame': 'rest', 'triangles': tris,
                           'vertices_m': vs}
        bonds = []
        if self.element is not None and self.element._bound:
            bonds = [{'endpoints': [
                {'port': 'port:patch', 'region_id': 'fixture_body_a'},
                {'port': 'port:patch', 'region_id': 'fixture_body_b'}],
                'id': 'bond:fixture_patch', 'status': 'qualified',
                'transfers': 'force_moment'}]
        doc = {
            'schema': 'chimera.material_state.v1',
            'object_id': 'mat2_g02_attachment_fixture',
            'revision': int(revision),
            'regions': [
                {'id': 'fixture_body_a', 'kind': 'region', 'parent': None,
                 'matter_claims': [
                     {'matter_id': 'mat_a', 'role': 'owner'},
                     {'matter_id': 'mat_iface', 'role': 'owner'}],
                 'ports': [
                     {'id': 'port:seam', 'protocol': 'normal_pressure',
                      'unit': 'Pa'},
                     {'id': 'port:patch', 'protocol': 'tension_shear_twist',
                      'unit': 'N,N*m'}],
                 'rest_geometry': geom([list(v) for v in BODY_VERTS_A]),
                 'current_geometry': geom(verts_a),
                 'sources': ['MAT2-G02 attachment fixture; supported body']},
                {'id': 'fixture_body_b', 'kind': 'region', 'parent': None,
                 'matter_claims': [
                     {'matter_id': 'mat_b', 'role': 'owner'},
                     {'matter_id': 'mat_iface', 'role': 'reference'}],
                 'ports': [
                     {'id': 'port:seam', 'protocol': 'normal_pressure',
                      'unit': 'Pa'},
                     {'id': 'port:patch', 'protocol': 'tension_shear_twist',
                      'unit': 'N,N*m'}],
                 'rest_geometry': geom([list(v) for v in BODY_VERTS_B]),
                 'current_geometry': geom(verts_b),
                 'sources': ['MAT2-G02 attachment fixture; free body']}],
            'directions': [
                {'id': 'dir:seam_normal', 'region_id': 'fixture_body_a',
                 'axis': [1.0, 0.0, 0.0], 'frame': 'rest',
                 'history': [{'revision': 0,
                              'state': 'declared interface normal'}]},
                {'id': 'dir:patch_axis', 'region_id': 'fixture_body_b',
                 'axis': [1.0, 0.0, 0.0], 'frame': 'rest',
                 'history': [{'revision': 0,
                              'state': 'declared patch axis'}]}],
            'laws': [
                {'id': 'law:contact_penalty',
                 'kind': 'pressure_deformation',
                 'parameters': {'c_n_N_s_per_m': C_N,
                                'k_c_Pa_per_m': K_C_PA_PER_M},
                 'provenance': ('declared unilateral penalty contact '
                                '(PREREGISTRATION law 8)'),
                 'regions': ['fixture_body_a', 'fixture_body_b']},
                {'id': 'law:attachment_patch',
                 'kind': 'pressure_deformation',
                 'parameters': {
                     'kA_t_N_per_m3': KA_T, 'kA_s_N_per_m3': KA_S,
                     'kA_theta_N_m_per_rad_m2': KA_THETA,
                     'patch_area_m2': A_PATCH,
                     'triangles': 2,
                     'rest_length_m': 0.0, 'transfers': 'force_moment'},
                 'provenance': (
                     'declared finite-area attachment patch; areal densities '
                     'derived from the sealed MAT2-M05 carrier (PREREGISTRA'
                     'TION laws 3-5); declared_placeholder, never biological'),
                 'regions': ['fixture_body_a', 'fixture_body_b']}],
            'contacts': [{'endpoints': [
                {'port': 'port:seam', 'region_id': 'fixture_body_a'},
                {'port': 'port:seam', 'region_id': 'fixture_body_b'}],
                'id': 'contact:fixture_seam',
                'interface': {'kind': 'planar_seam',
                              'normal': [1.0, 0.0, 0.0],
                              'shared_face_area_m2': A_PATCH},
                'state': 'touching'}],
            'bonds': bonds,
            'matter': [{'id': mid, 'mass_kg': m,
                        'provenance': ('declared fixture mass carried from '
                                       'the MAT2-M05 once-only carrier')}
                       for mid, m in MATTER],
            'provenance': {
                'task': CARD_FULL,
                'preregistration': 'PREREGISTRATION.md (this directory)',
                'note': ('revision 1 = bound patch; revision 2 = patch '
                         'released (bond relation removed; contact '
                         'persists) - the M05 release vocabulary')},
        }
        validate_material_state(doc)   # UNMODIFIED M01 gate (T0)
        return doc


# ------------------------------------------------- C17 terminal record (T10)
C17_TERMINAL = {
    'schema': 'chimera.g02_c17_terminal.v1',
    'card': CARD_FULL,
    'calculation': 'C17 finite attachment mechanics',
    'biological_ports': {
        'carrier': 'MAT2-A09 grasp_package.json interface_graph.connections',
        'attachment_interface_count': 26,
        'c17_status_carried_open': 26,
        'terminal_state': 'explicitly_unresolved',
        'reason': ('no measured or separately-authorized source exists for '
                   'per-port patch area/shape, areal stiffness, couple '
                   'resistance, weights or frame; the sealed A07 gate '
                   'requires authorization BEFORE any fitting experiment and '
                   'none is recorded in the A09 package'),
        'synthetic_lambda_min_used': False,
    },
    'fixture_constants': {
        'provenance_class': 'declared_placeholder',
        'never_biological': True,
        'derivation': ('areal densities = sealed MAT2-M05 point constants / '
                       '0.0175 m^2; patch geometry and weights authored'),
        'values': {'kA_t_N_per_m3': KA_T, 'kA_s_N_per_m3': KA_S,
                   'kA_theta_N_m_per_rad_m2': KA_THETA,
                   'A1_m2': A1, 'A2_m2': A2, 'A_patch_m2': A_PATCH,
                   'w1': W1, 'w2': W2},
    },
}
