"""MAT2-M09: loose bones assembled by physical connective matter.

Implements the frozen PREREGISTRATION.md (this directory) exactly: two
DIFFERENT bone-shaped XPBD scaffold bodies fall separately onto a declared
pinned ground (phase A), are assembled by AUTHORED connective material —
one ligament and one capsule created ONLY by explicit bind calls between
declared ports (the sealed M05 interface, subclassed for 3-D port
geometry), plus the UNMODIFIED M06 local triangle contact material between
their head faces — under a declared load schedule (phase B), and become
independent again when the explicit release removes ALL bond-type
connective material bitwise (phase C). Any reduced constraint is DERIVED
per tick from the active connections into a measurement-only restraint
record that never applies force (P-AST-restraint) and vanishes bitwise
with the connections. No joint, hinge, axis or pose-writer element exists
in this module (P-AST-no-joint).

Upstream authority, reused verbatim and unmodified:
- tools/monkey_campaign/contributions/MAT2-M01/material_state.py
  (chimera.material_state.v1 validator; schema authority),
- tools/monkey_campaign/contributions/MAT2-M03/pressure_membrane.py
  (Membrane closure/area/normal utilities for the bone scaffolds),
- tools/monkey_campaign/contributions/MAT2-M05/interface_exchange.py
  (the sealed contact/bond/release interface: bind/release status machine,
  named refusals, bitwise post-release zero, e_release capture, reciprocal
  load application, no-auto-bond guard — inherited via declared subclasses),
- tools/monkey_campaign/contributions/MAT2-M06/local_contact.py
  (sweep-and-prune, triangle-triangle closest features, Coulomb
  stick/slip solve, pinned anchor reactions — the contact material path).

CPU-only; stdlib + numpy; deterministic (no stochastic inputs, no
wall-clock). Refusals are named codes; nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M05'), str(CONTRIB / 'MAT2-M06')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import material_state  # noqa: E402  (M01 validator, unmodified)
import pressure_membrane as pm  # noqa: E402  (M03 Membrane, unmodified)
import local_contact as lc  # noqa: E402  (M06 local contact, unmodified)
import interface_exchange as m05  # noqa: E402  (M05 sealed interfaces)

# ---- frozen declarations (PREREGISTRATION.md) -------------------------------
SCHEMA = 'chimera.m09_assembly.v1'
G_M_S2 = 9.80665                   # M03/M07 declared constant, along -z
DT_S = 1.0 / 300.0                 # 300 Hz pin
N_SUB = 4                          # declared substeps per tick (M07 pin)
H_SUB = DT_S / N_SUB
GS_TOL_N_S = 1e-12                 # contact Gauss-Seidel convergence gate
GS_CAP = 32
XPBD_TOL_M = 1e-10
XPBD_ITERATIONS_CAP = 100
XPBD_COMPLIANCE_M_PER_N = 1.0e-5
THICKNESS_M = 0.002                # M06/M02 shell thickness pin
TICKS = 90                         # ticks 0..89
BIND_TICK = 45                     # explicit assembly act
RELEASE_TICK = 85                  # explicit removal act
PRESS_TICKS = range(60, 75)        # declared -3.0 N press on bone_b (-x)
PULL_TICKS = range(75, 90)         # declared +3.0 N pull on bone_b (+x)
PRESS_FORCE_N = 6.0
PULL_FORCE_N = 3.0
DAMPING_LOOSE_PER_S = 8.0          # declared damping, loose phase (M05
# heritage value; the free fall must stay near-ideal for the
# separate-falls evidence)
DAMPING_JOINT_PER_S = 120.0        # declared damping, bound/released
# phases (the declared assembly medium; limits the bind-driven approach
# to its ~2.8 m/s terminal speed) — Amendment A1 schedule


def damping_of_tick(tick):
    return DAMPING_LOOSE_PER_S if tick <= 44 else DAMPING_JOINT_PER_S
BONE_MU = (0.4, 0.3)
GROUND_MU = (0.7, 0.5)
MASS_A_KG = 0.030                  # bone_a (rod)
MASS_B_KG = 0.018                  # bone_b (tapered wedge)
LIG_REST_LENGTH_M = 0.02           # declared short check-rein ligament
LIG_K_T_N_PER_M = 60.0             # ligament axial (tension-only)
LIG_K_S_N_PER_M = 40.0             # ligament transverse shear
CAP_K_C_N_PER_M = 12.0             # capsule axial (tension AND compression)
CAP_K_S_N_PER_M = 8.0              # capsule transverse shear
RESTRAINT_THRESHOLD_N_PER_M = 1e-3
DECLARED_ORDER = ('gravity_damping', 'connective_elements', 'contact',
                  'integration_projection')
PHASE_OF_TICK = (('loose', 0, 44), ('bound', 45, 84), ('released', 85, 89))
DOC_TICKS = (0, 46, 70, 86, 89)    # frozen state-document ticks
RESIDUAL_FORM = ('R = E_mech(t) - E_mech(t-1) - (W_act + W_lig + W_cap '
                 '+ W_grav) + Q_damp + Q_contact + Q_proj + '
                 'E_diss_release; '
                 '|R| <= reservoirs + 5e-2*turnover + 1e-9; release tick: '
                 '|R| <= max(5e-2*E_diss_release, 1e-12)')

DECLARATION = {
    'schema': SCHEMA,
    'order': list(DECLARED_ORDER),
    'dt_s': DT_S, 'substeps_per_tick': N_SUB, 'ticks': TICKS,
    'bind_tick': BIND_TICK, 'release_tick': RELEASE_TICK,
    'press_ticks': [min(PRESS_TICKS), max(PRESS_TICKS)],
    'press_force_n': PRESS_FORCE_N,
    'pull_ticks': [min(PULL_TICKS), max(PULL_TICKS)],
    'pull_force_n': PULL_FORCE_N,
    'g_m_per_s2': G_M_S2,
    'damping_schedule_per_s': {'loose': DAMPING_LOOSE_PER_S,
                               'joint': DAMPING_JOINT_PER_S},
    'thickness_m': THICKNESS_M,
    'contact_gauss_seidel_tol_N_s': GS_TOL_N_S,
    'contact_gauss_seidel_cap': GS_CAP,
    'xpbd_tolerance_m': XPBD_TOL_M,
    'xpbd_iteration_cap': XPBD_ITERATIONS_CAP,
    'xpbd_compliance_m_per_N': XPBD_COMPLIANCE_M_PER_N,
    'ligament_rest_length_m': LIG_REST_LENGTH_M,
    'ligament_k_t_N_per_m': LIG_K_T_N_PER_M,
    'ligament_k_s_N_per_m': LIG_K_S_N_PER_M,
    'capsule_k_c_N_per_m': CAP_K_C_N_PER_M,
    'capsule_k_s_N_per_m': CAP_K_S_N_PER_M,
    'mass_bone_a_kg': MASS_A_KG, 'mass_bone_b_kg': MASS_B_KG,
    'bone_mu_s_k': list(BONE_MU), 'ground_mu_s_k': list(GROUND_MU),
    'restraint_threshold_N_per_m': RESTRAINT_THRESHOLD_N_PER_M,
    'residual_form': RESIDUAL_FORM,
    'ccd_declaration': 'per-substep static detection; end-of-substep '
                       'overlap resolved by the next substep narrow phase; '
                       'tunneling needs > 4.9 m/s (declared speed bound '
                       '4.0 m/s, T7)',
    'momentum_ledger': 'per body per substep over stages 1-3: m*(v-v0) == '
                       'gravity + damping + element_actuator + contact '
                       '(telescoping recorded deltas), <= 1e-12; the '
                       'projection impulse is internal and pairwise (its '
                       'work stays in R)',
    'upstream': 'M01 validator; M03 Membrane; M05 sealed bond/release '
                'interface (subclassed); M06 local contact (verbatim)',
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

INPUT_PINS = {
    '../MAT2-M01/material_state.py':
        'b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40',
    '../MAT2-M03/pressure_membrane.py':
        '3dd64f6465430380f1c0a53a95523c700cd51a6b1115e60f0df8afde2239c96e',
    '../MAT2-M05/interface_exchange.py':
        '295e6c898ada14918f09b2b0633f5926c1623c9e09cd37258e516ab57450b9b9',
    '../MAT2-M06/local_contact.py':
        '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc',
}


def verify_input_pins():
    for rel, expected in INPUT_PINS.items():
        path = (HERE / rel).resolve()
        if not path.exists():
            raise ValueError('input_pin_missing:' + rel)
        if sha256_file(path) != expected:
            raise ValueError('input_pin_drift:' + rel)
    return dict(INPUT_PINS)


# ---------------------------------------------------------------- geometry ---

def _quad_tris(a, b, c, d):
    return [[a, b, c], [a, c, d]]


def bone_a_vertices():
    """bone_a (rod): x in [-0.24, -0.06], head face at x = -0.06.

    Head/tail trapezoid (u, v): (0, 0), (0.05, 0), (0.035, 0.03), (0, 0.03)
    relative to (y0, z0) = (-0.025, 0.040). 8 vertices; head-face triangle
    areas derived 7.5e-4 / 5.25e-4 m^2 (unequal, ratio 10/7).
    """
    y0, z0 = -0.025, 0.040
    face = [(0.0, 0.0), (0.05, 0.0), (0.035, 0.03), (0.0, 0.03)]
    head = [(-0.06, y0 + u, z0 + v) for (u, v) in face]
    tail = [(-0.24, y0 + u, z0 + v) for (u, v) in face]
    return head + tail  # vertices 0..3 head, 4..7 tail


def bone_b_vertices():
    """bone_b (tapered wedge): head face at x = +0.06, tail at +0.18.

    Head trapezoid (0, 0), (0.04, 0), (0.028, 0.024), (0, 0.024) relative
    to (y0, z0) = (-0.02, 0.022); tail REDUCED trapezoid (0, 0),
    (0.028, 0), (0.02, 0.02), (0, 0.02) relative to (y0, z0) = (-0.014,
    0.022). DIFFERENT shape from bone_a (the two-independent-shapes clause).
    """
    hy0, hz0 = -0.02, 0.022
    ty0, tz0 = -0.014, 0.022
    hface = [(0.0, 0.0), (0.04, 0.0), (0.028, 0.024), (0.0, 0.024)]
    tface = [(0.0, 0.0), (0.028, 0.0), (0.02, 0.02), (0.0, 0.02)]
    head = [(0.06, hy0 + u, hz0 + v) for (u, v) in hface]
    tail = [(0.18, ty0 + u, tz0 + v) for (u, v) in tface]
    return head + tail


def bone_triangles():
    """12 triangles: head 2, tail 2, four side quads (0..3 head,
    4..7 tail)."""
    return (_quad_tris(0, 1, 2, 3) + _quad_tris(4, 5, 6, 7)
            + _quad_tris(0, 1, 5, 4) + _quad_tris(1, 2, 6, 5)
            + _quad_tris(2, 3, 7, 6) + _quad_tris(3, 0, 4, 7))


def ground_body():
    """The declared pinned support (visible in every whole/side view)."""
    verts = [(-0.30, -0.20, -0.001), (0.30, -0.20, -0.001),
             (0.30, 0.20, -0.001), (-0.30, 0.20, -0.001)]
    return lc.Body('ground', 'surface_ground', 'mat_ground', 0.0,
                   GROUND_MU[0], GROUND_MU[1], THICKNESS_M,
                   verts, [(0, 1, 2), (0, 2, 3)], pinned=True)


# ------------------------------------------------------------------- bones ---

class BoneBody:
    """A bone-shaped XPBD scaffold body (M05 Body heritage).

    8 vertices, 12 triangles, closed and outward-oriented (M03 closure);
    port anchors are MATERIAL POINTS at declared rest positions tracked by
    the mean body translation (M05 correction A1 heritage).
    """

    def __init__(self, body_id, vertices, mass_kg):
        require(isinstance(body_id, str) and body_id.strip(), 'body_id')
        self.body_id = body_id
        self.rest = np.array(vertices, dtype=np.float64)
        tris = []
        for tri in bone_triangles():
            v = self.rest[tri]
            n = np.cross(v[1] - v[0], v[2] - v[0])
            if float(np.dot(n, v.mean(axis=0) - self.rest.mean(axis=0))) \
                    < 0.0:
                tri = [tri[0], tri[2], tri[1]]   # outward winding (M05)
            tris.append(tri)
        tris = np.array(tris, dtype=np.int64)
        self.membrane = pm.Membrane(self.rest, tris, body_id)
        self.membrane.require_closed()
        self.triangles = tris
        self.x = self.rest.copy()
        self.v = np.zeros_like(self.x)
        n = self.rest.shape[0]
        self.masses = np.full(n, mass_kg / n)
        self.inv_masses = 1.0 / self.masses
        self.total_mass = float(mass_kg)
        edges = {}
        for a, b, c in tris.tolist():
            for u, w in ((a, b), (b, c), (c, a)):
                edges[(min(u, w), max(u, w))] = True
        # declared face-diagonal braces: both diagonals of each of the six
        # quads (head, tail, four sides) keep the scaffold near-rigid
        for (a, b, c, d) in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
                             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            edges[(min(a, c), max(a, c))] = True
            edges[(min(b, d), max(b, d))] = True
        self.edge_list = sorted(edges)
        self.rest_lengths = np.array([
            float(np.linalg.norm(self.rest[b] - self.rest[a]))
            for a, b in self.edge_list])
        self.rest_mean = self.rest.mean(axis=0)
        # declared ports: head anchor = head-face area centroid; capsule
        # anchor = shank point CAP_SHANK_OFFSET_M behind the head face
        areas = np.array([self.membrane.areas[0], self.membrane.areas[1]])
        cent = np.array([self.membrane.centroids[0],
                         self.membrane.centroids[1]])
        self.rest_head_anchor = (areas[0] * cent[0] + areas[1] * cent[1]) \
            / areas.sum()
        self.head_tri_vids = [tuple(int(i) for i in tris[0]),
                              tuple(int(i) for i in tris[1])]

    def mean_translation(self):
        return self.x.mean(axis=0) - self.rest_mean

    @property
    def head_anchor(self):
        return self.rest_head_anchor + self.mean_translation()

    def scaffold_energy(self):
        total = 0.0
        for (a1, a2), rest in zip(self.edge_list, self.rest_lengths):
            length = float(np.linalg.norm(self.x[a2] - self.x[a1]))
            total += (length - rest) ** 2 / (2.0 * XPBD_COMPLIANCE_M_PER_N)
        return total

    def distribute_to_head(self, force):
        """Point force at the head anchor -> per-vertex loads.

        Split across the two head triangles by CURRENT area share with an
        exact complement on the second share (bitwise resultant), then
        equal thirds per triangle (M05 distribute_to_iface heritage).
        """
        m = pm.Membrane(self.x, self.triangles, self.body_id)
        a = np.array([m.areas[0], m.areas[1]])
        total = float(a.sum())
        share0 = force * (a[0] / total)
        share1 = force - share0
        loads = np.zeros_like(self.x)
        for tri, share in zip(self.head_tri_vids, (share0, share1)):
            for vid in tri:
                loads[vid] += share / 3.0
        return loads

    def head_face_areas(self):
        m = pm.Membrane(self.x, self.triangles, self.body_id)
        return [float(m.areas[0]), float(m.areas[1])]

    def tri_area_now(self, tri_index):
        m = pm.Membrane(self.x, self.triangles, self.body_id)
        return float(m.areas[int(tri_index)])


class BoneTriPort:
    """M06-compatible adapter for one bone surface triangle (M07
    MembranePort heritage): the rigid cluster of the triangle's 3 lumped
    vertices; velocity = mean of the three; an applied impulse delta is
    written THROUGH to the three vertices equally. Written only from the
    declared contact stage (single-writer)."""

    def __init__(self, bone, tri_index):
        self._bone = bone
        self.tri_index = int(tri_index)
        self.vids = tuple(int(i) for i in bone.triangles[self.tri_index])
        self.mass_kg = float(bone.masses[list(self.vids)].sum())
        require(self.mass_kg > 0.0, 'port_mass_invalid')
        self.mu_s, self.mu_k = BONE_MU
        self.thickness_m = THICKNESS_M
        self.id = f'{bone.body_id}/port:t{self.tri_index}'
        self.matter_id = f'mat_{bone.body_id}'

    @property
    def velocity(self):
        return self._bone.v[list(self.vids)].mean(axis=0)

    @velocity.setter
    def velocity(self, value):
        delta = np.asarray(value, dtype=np.float64) - self.velocity
        self._bone.v[list(self.vids)] += delta

    def inv_mass(self):
        return 1.0 / self.mass_kg

    def verts(self):
        return [tuple(self._bone.x[i]) for i in self.vids]


class GroundPort:
    """M06-compatible view of one ground triangle (pinned; the reaction
    is recorded, never hidden — falsifier FB3's clean path)."""

    def __init__(self, ground, tri_index):
        self._ground = ground
        self.tri_index = int(tri_index)
        self.vids = tuple(int(i) for i in ground.triangles[self.tri_index])
        self.mu_s, self.mu_k = GROUND_MU
        self.thickness_m = THICKNESS_M
        self.id = f'ground/port:t{self.tri_index}'
        self.matter_id = 'mat_ground'
        self.mass_kg = 0.0

    @property
    def velocity(self):
        return np.zeros(3)

    @velocity.setter
    def velocity(self, value):
        pass  # pinned: the reaction is the recorded impulse itself

    def inv_mass(self):
        return 0.0

    def verts(self):
        return [tuple(self._ground.vertices[i]) for i in self.vids]


class _PairView:
    """Thin view exposing exactly what M06's solve_contact reads/mutates
    (M07 _PairBody heritage)."""

    def __init__(self, holder):
        self._holder = holder

    id = property(lambda self: self._holder.id)
    mu_s = property(lambda self: self._holder.mu_s)
    mu_k = property(lambda self: self._holder.mu_k)
    velocity = property(lambda self: self._holder.velocity,
                        lambda self, v: setattr(self._holder, 'velocity', v))

    def inv_mass(self):
        return self._holder.inv_mass()


# ------------------------------------------------- connective elements ------

class LigamentElement(m05.BondElement):
    """The sealed M05 bond interface, subclassed for 3-D port geometry.

    Inherited VERBATIM from the sealed class: bind/release status machine,
    refusal codes (bond_not_bound / bond_already_bound /
    release_of_unbound_bond), bitwise post-release zero, e_release capture
    at the release tick, force_on_a = -force_on_b reciprocity. Overridden
    (declared): the 3-D direction law — tension-only along the CURRENT
    port axis with the DECLARED rest length (a short check-rein: the
    assembly act pulls the bones together; Amendment A1) plus transverse
    shear.
    """

    def __init__(self, bond_id, bone_a, bone_b):
        super().__init__(bond_id, bone_a, bone_b,
                         {'body_a': 'port:head', 'body_b': 'port:head'},
                         transfers='force')
        self.bone_a = bone_a
        self.bone_b = bone_b
        self.k_t = LIG_K_T_N_PER_M
        self.k_s = LIG_K_S_N_PER_M
        self.rest_length_m = LIG_REST_LENGTH_M

    def delta(self):
        return self.bone_b.head_anchor - self.bone_a.head_anchor

    def axis(self):
        d = self.delta()
        n = float(np.linalg.norm(d))
        require(n > 0.0, 'degenerate_ligament_axis')
        return d / n

    def extension(self):
        return float(np.linalg.norm(self.delta())) - self.rest_length_m

    def shear_offset(self):
        d = self.delta()
        a = self.axis()
        return d - float(np.dot(d, a)) * a

    def tension(self):
        if self.status == 'planned':
            raise ValueError(m05.REFUSAL_BOND_NOT_BOUND)
        if not self.active:
            return 0.0
        return self.k_t * max(0.0, self.extension())

    def force_on_b(self):
        if self.status == 'planned':
            raise ValueError(m05.REFUSAL_BOND_NOT_BOUND)
        if not self.active:
            return np.zeros(3)
        t = self.tension()
        shear = self.k_s * self.shear_offset()
        return -t * self.axis() - shear

    def stored_energy(self, theta_rad=0.0):
        if self.status == 'planned':
            raise ValueError(m05.REFUSAL_BOND_NOT_BOUND)
        if not self.active:
            return 0.0
        e = max(0.0, self.extension())
        d = self.shear_offset()
        return (0.5 * self.k_t * e * e
                + 0.5 * self.k_s * float(np.dot(d, d)))


class CapsuleElement(m05.BondElement):
    """The sealed M05 bond interface with a declared BIDIRECTIONAL axial
    law (tension AND compression — the joint strut: a compressed strut
    between the head faces resists closure and passes load through the
    contact interface; Amendment A1). Inherited verbatim: the bind/release
    status machine, refusal codes, bitwise post-release zero, e_release
    capture, force_on_a = -force_on_b. Overridden (declared): the signed
    axial force and its exact energy; rest length frozen at bind."""

    def __init__(self, bond_id, bone_a, bone_b):
        super().__init__(bond_id, bone_a, bone_b,
                         {'body_a': 'port:head', 'body_b': 'port:head'},
                         transfers='force')
        self.bone_a = bone_a
        self.bone_b = bone_b
        self.k_c = CAP_K_C_N_PER_M
        self.k_s = CAP_K_S_N_PER_M
        self.rest_length_m = None

    def bind(self, tick):
        super().bind(tick)
        self.rest_length_m = float(np.linalg.norm(self.delta()))

    def delta(self):
        return self.bone_b.head_anchor - self.bone_a.head_anchor

    def axis(self):
        d = self.delta()
        n = float(np.linalg.norm(d))
        require(n > 0.0, 'degenerate_capsule_axis')
        return d / n

    def extension(self):
        return float(np.linalg.norm(self.delta())) - self.rest_length_m

    def shear_offset(self):
        d = self.delta()
        a = self.axis()
        return d - float(np.dot(d, a)) * a

    def axial_force_n(self):
        """Signed: positive = tension, negative = compression."""
        if self.status == 'planned':
            raise ValueError(m05.REFUSAL_BOND_NOT_BOUND)
        if not self.active:
            return 0.0
        return self.k_c * self.extension()

    def force_on_b(self):
        if self.status == 'planned':
            raise ValueError(m05.REFUSAL_BOND_NOT_BOUND)
        if not self.active:
            return np.zeros(3)
        f = self.axial_force_n()
        shear = self.k_s * self.shear_offset()
        return -f * self.axis() - shear

    def stored_energy(self, theta_rad=0.0):
        if self.status == 'planned':
            raise ValueError(m05.REFUSAL_BOND_NOT_BOUND)
        if not self.active:
            return 0.0
        e = self.extension()
        d = self.shear_offset()
        return (0.5 * self.k_c * e * e
                + 0.5 * self.k_s * float(np.dot(d, d)))


def refuse_auto_bond():
    """Explicit guard: proximity/containment must never create a bond
    (sealed M05 heritage)."""
    raise ValueError(m05.REFUSAL_AUTO_BOND)


# ------------------------------------------- derived restraint (measure) ----

def restraint_matrix(lig, cap):
    """MEASUREMENT ONLY (never a force law; P-AST-restraint probes that
    this function writes no physical state): the 3x3 relative-translation
    restraint matrix summed from the BOUND elements at their CURRENT port
    geometry (prereg law 7). Contact restraint is reported separately as
    the contact direction record (remaining contact, never a bond)."""
    k = np.zeros((3, 3))
    contrib = {}
    eye = np.eye(3)
    if lig is not None and lig.active:
        a = lig.axis()
        taut = 1.0 if lig.extension() > 0.0 else 0.0
        k_lig = lig.k_t * taut * np.outer(a, a) \
            + lig.k_s * (eye - np.outer(a, a))
        k = k + k_lig
        contrib['ligament'] = [float(c) for c in k_lig.ravel()]
    if cap is not None and cap.active:
        a = cap.axis()
        k_cap = cap.k_c * np.outer(a, a) + cap.k_s * (eye - np.outer(a, a))
        k = k + k_cap
        contrib['capsule'] = [float(c) for c in k_cap.ravel()]
    return k, contrib


def restraint_matrix_recomputed(lig, cap):
    """Independent second code path (different summation order) for the
    1e-15 cross-check (prereg law 7)."""
    terms = []
    if lig is not None and lig.active:
        a = lig.axis()
        outer = np.array([[a[i] * a[j] for j in range(3)] for i in range(3)])
        taut = 1.0 if lig.extension() > 0.0 else 0.0
        terms.append(lig.k_t * taut * outer
                     + lig.k_s * (np.eye(3) - outer))
    if cap is not None and cap.active:
        a = cap.axis()
        outer = np.array([[a[i] * a[j] for j in range(3)] for i in range(3)])
        terms.append(cap.k_c * outer + cap.k_s * (np.eye(3) - outer))
    total = np.zeros((3, 3))
    for t in terms:
        total = total + t
    return total


def restrained_direction_count(k):
    eig = np.linalg.eigvalsh(k)
    return int(sum(1 for v in eig if v > RESTRAINT_THRESHOLD_N_PER_M))


# ------------------------------------------------------------------ state ---

def _geometry_dict(bone):
    return {'vertices_m': [[float(c) for c in row] for row in bone.rest],
            'triangles': [[int(i) for i in t] for t in bone.triangles],
            'frame': 'rest'}


def state_document(revision, bone_a, bone_b, lig, cap, contact_state):
    """chimera.material_state.v1; validated by M01 UNMODIFIED. Bond
    relations exist ONLY while bound; the released document REMOVES them
    (not a zero-status row) while the contact relation persists."""
    def ports():
        return [
            {'id': 'port:head', 'protocol': 'connective_anchor',
             'unit': 'N'}]

    regions = [
        {'id': 'bone_a', 'kind': 'region', 'parent': None,
         'rest_geometry': _geometry_dict(bone_a),
         'current_geometry': _geometry_dict(bone_a),
         'matter_claims': [{'matter_id': 'mat_bone_a', 'role': 'owner'}],
         'sources': ['MAT2-M09 assembly experiment; rod bone (free)'],
         'ports': ports()},
        {'id': 'bone_b', 'kind': 'region', 'parent': None,
         'rest_geometry': _geometry_dict(bone_b),
         'current_geometry': _geometry_dict(bone_b),
         'matter_claims': [{'matter_id': 'mat_bone_b', 'role': 'owner'}],
         'sources': ['MAT2-M09 assembly experiment; tapered wedge bone '
                     '(free, manipulated)'],
         'ports': ports()},
    ]
    bonds = []
    if lig is not None and lig.bound_tick is not None \
            and lig.released_tick is None:
        bonds.append({'id': 'ligament:strap_l1',
                      'endpoints': [
                          {'region_id': 'bone_a', 'port': 'port:head'},
                          {'region_id': 'bone_b', 'port': 'port:head'}],
                      'status': 'qualified', 'transfers': 'force'})
    if cap is not None and cap.bound_tick is not None \
            and cap.released_tick is None:
        bonds.append({'id': 'capsule:sleeve_c1',
                      'endpoints': [
                          {'region_id': 'bone_a', 'port': 'port:head'},
                          {'region_id': 'bone_b', 'port': 'port:head'}],
                      'status': 'qualified', 'transfers': 'force'})
    doc = {
        'schema': material_state.SCHEMA,
        'revision': int(revision),
        'object_id': 'mat2_m09_assembly_rig',
        'regions': regions,
        'matter': [
            {'id': 'mat_bone_a', 'mass_kg': MASS_A_KG,
             'provenance': 'declared rod bone mass (PREREGISTRATION law 2)'},
            {'id': 'mat_bone_b', 'mass_kg': MASS_B_KG,
             'provenance': 'declared tapered wedge bone mass '
                           '(PREREGISTRATION law 3)'}],
        'directions': [
            {'id': 'dir:head_face_normal', 'region_id': 'bone_a',
             'axis': [1.0, 0.0, 0.0], 'frame': 'rest', 'history': [
                 {'revision': 0, 'state': 'declared head-face normal (a '
                                          'measured geometry record; no '
                                          'joint element uses it)'}]},
            {'id': 'dir:ligament_line', 'region_id': 'bone_b',
             'axis': [1.0, 0.0, 0.0], 'frame': 'rest', 'history': [
                 {'revision': 0, 'state': 'declared ligament axis at '
                                          'bind'}]}],
        'laws': [
            {'id': 'law:contact_material', 'kind': 'pressure_deformation',
             'regions': ['bone_a', 'bone_b'],
             'parameters': {'engine': 'MAT2-M06 local_contact unmodified',
                            'thickness_m': THICKNESS_M,
                            'bone_mu_s': BONE_MU[0], 'bone_mu_k': BONE_MU[1],
                            'ground_mu_s': GROUND_MU[0],
                            'ground_mu_k': GROUND_MU[1]},
             'provenance': 'the sealed M06 contact material IS the joint '
                           'contact material (card brief: M05 interfaces '
                           'through M06 contacts)'},
            {'id': 'law:ligament_l1', 'kind': 'pressure_deformation',
             'regions': ['bone_a', 'bone_b'],
             'parameters': {'k_t_N_per_m': LIG_K_T_N_PER_M,
                            'k_s_N_per_m': LIG_K_S_N_PER_M,
                            'rest_length_m': LIG_REST_LENGTH_M,
                            'tension_only': 'true'},
             'provenance': 'sealed M05 bond interface, subclassed for '
                           '3-D port geometry; declared short check-rein '
                           '(Amendment A1)'},
            {'id': 'law:capsule_c1', 'kind': 'pressure_deformation',
             'regions': ['bone_a', 'bone_b'],
             'parameters': {'k_c_N_per_m': CAP_K_C_N_PER_M,
                            'k_s_N_per_m': CAP_K_S_N_PER_M,
                            'axial': 'tension_and_compression',
                            'rest_frozen_at_bind': 'true'},
             'provenance': 'declared joint strut on the sealed M05 bond '
                           'interface, anchored at the head faces '
                           '(Amendment A1)'}],
        'contacts': [
            {'id': 'contact:joint_faces',
             'endpoints': [
                 {'region_id': 'bone_a', 'port': 'port:head'},
                 {'region_id': 'bone_b', 'port': 'port:head'}],
             'state': contact_state,
             'interface': {'kind': 'bone_head_faces',
                           'normal_axis': [1.0, 0.0, 0.0]}}],
        'bonds': bonds,
        'provenance': {
            'task': 'MAT2-M09',
            'preregistration': 'PREREGISTRATION.md (this directory)',
            'note': 'bond relations exist only while bound; the released '
                    'document REMOVES them (M01 bond_count 0) while the '
                    'contact relation persists (remaining contact)'},
    }
    return doc


def validate_state(doc):
    return material_state.validate_material_state(doc)


def phase_of(tick):
    for name, lo, hi in PHASE_OF_TICK:
        if lo <= tick <= hi:
            return name
    raise ValueError('tick_out_of_range')


def _body_of(port_id):
    head = port_id.split('/')[0]
    require(head in ('bone_a', 'bone_b', 'ground'), 'unknown_port_body')
    return head


# -------------------------------------------------------------------- run ---

class AssemblyRun:
    """One state owner; the declared substep order is the ONLY writer of
    physical state (single-writer, M07 heritage)."""

    def __init__(self):
        self.bone_a = BoneBody('bone_a', bone_a_vertices(), MASS_A_KG)
        self.bone_b = BoneBody('bone_b', bone_b_vertices(), MASS_B_KG)
        self.ground = ground_body()
        self.ground_ports = [GroundPort(self.ground, i)
                             for i in range(len(self.ground.triangles))]
        self.ports = {
            'bone_a': [BoneTriPort(self.bone_a, i)
                       for i in range(len(self.bone_a.triangles))],
            'bone_b': [BoneTriPort(self.bone_b, i)
                       for i in range(len(self.bone_b.triangles))],
            'ground': self.ground_ports,
        }
        self.lig = None
        self.cap = None
        self.e_diss_release = 0.0
        self.ticks = []
        self.documents = {}
        self.gs_residual_worst = 0.0

    # -- assembly acts (the ONLY paths that create/remove connections) -----
    def bind_connections(self, tick):
        require(self.lig is None and self.cap is None,
                'connections_already_exist')
        require(tick == BIND_TICK, 'bind_tick_mismatch')
        self.lig = LigamentElement('ligament:strap_l1', self.bone_a,
                                   self.bone_b)
        self.cap = CapsuleElement('capsule:sleeve_c1', self.bone_a,
                                  self.bone_b)
        self.lig.bind(tick)
        self.cap.bind(tick)

    def release_connections(self, tick):
        require(tick == RELEASE_TICK, 'release_tick_mismatch')
        require(self.lig is not None and self.cap is not None,
                m05.REFUSAL_RELEASE_UNBOUND)
        # e_release capture happens INSIDE the sealed release() (heritage)
        self.lig.release(tick)
        self.cap.release(tick)
        self.e_diss_release = self.lig.e_release_j + self.cap.e_release_j

    # -- element loads ------------------------------------------------------
    def _element_loads(self):
        zeros_a = np.zeros_like(self.bone_a.x)
        zeros_b = np.zeros_like(self.bone_b.x)
        lig_a = np.zeros_like(self.bone_a.x)
        lig_b = np.zeros_like(self.bone_b.x)
        cap_a = np.zeros_like(self.bone_a.x)
        cap_b = np.zeros_like(self.bone_b.x)
        if self.lig is not None and self.lig.active:
            f_b = self.lig.force_on_b()
            f_a = -f_b                       # inherited bitwise reciprocity
            lig_b = self.bone_b.distribute_to_head(f_b)
            lig_a = self.bone_a.distribute_to_head(f_a)
        if self.cap is not None and self.cap.active:
            f_b = self.cap.force_on_b()
            f_a = -f_b
            cap_b = self.bone_b.distribute_to_head(f_b)
            cap_a = self.bone_a.distribute_to_head(f_a)
        return {'loads_a': lig_a + cap_a, 'loads_b': lig_b + cap_b,
                'lig_a': lig_a, 'lig_b': lig_b, 'cap_a': cap_a,
                'cap_b': cap_b}

    def _actuator_load(self, tick):
        loads = np.zeros_like(self.bone_b.x)
        if tick in PRESS_TICKS:
            loads += (PRESS_FORCE_N / 8.0) * np.array([-1.0, 0.0, 0.0])
        elif tick in PULL_TICKS:
            loads += (PULL_FORCE_N / 8.0) * np.array([1.0, 0.0, 0.0])
        return loads

    def _kinetic(self):
        ka = float((0.5 * self.bone_a.masses[:, None]
                    * self.bone_a.v ** 2).sum())
        kb = float((0.5 * self.bone_b.masses[:, None]
                    * self.bone_b.v ** 2).sum())
        return ka + kb

    # -- contact stage (M06 unmodified arithmetic, M07 GS discipline) ------
    def _contact_stage(self):
        holders = (self.ports['bone_a'] + self.ports['bone_b']
                   + self.ports['ground'])
        motion = 0.0
        for b in holders:
            motion = max(motion, float(np.linalg.norm(_PairView(b).velocity))
                         * H_SUB)
        inflate = motion + THICKNESS_M + lc.MARGIN
        entries = []
        for bi, b in enumerate(holders):
            lo, hi = lc.tri_aabb(b.verts(), inflate)
            # first element = the BODY id (M06 sweep_prune excludes
            # same-body pairs by it; each holder IS one triangle)
            entries.append((b.id.split('/')[0], 0, lo, hi))
        cand = [pair for pair in lc.sweep_prune(entries)
                if not (holders[pair[0]].id.startswith('ground')
                        and holders[pair[1]].id.startswith('ground'))]
        active = []
        for (i, j) in cand:
            ba, bb = holders[i], holders[j]
            # canonical pair order: body_a carries the lexicographically
            # smaller body id, so the declared fallback normals below have
            # a fixed sign (deep-overlap guard, Amendment A1)
            if ba.id.split('/')[0] > bb.id.split('/')[0]:
                ba, bb = bb, ba
            tai, tbi = ba.verts(), bb.verts()
            p, q, dist = lc.tri_tri_closest(*tai, *tbi)
            gap = dist - 0.5 * (ba.thickness_m + bb.thickness_m)
            if gap <= lc.MARGIN + lc.CCD_TOL_M:
                if dist > 0.0:
                    normal = lc.vunit(lc.vsub(p, q))
                else:
                    # declared fallback (dist == 0): the declared axis
                    # from body_b's surface toward body_a's — +x for a
                    # bone-bone face pair (bone_a < bone_b), +z for a
                    # bone-ground pair
                    normal = (1.0, 0.0, 0.0) \
                        if ba.id.startswith('bone') \
                        and bb.id.startswith('bone') else (0.0, 0.0, 1.0)
                active.append((_PairView(ba), _PairView(bb), gap, normal,
                               (i, j)))
        ke_pre = self._kinetic()
        records = []
        max_jn = 0.0
        iterations = 0
        contact_impulse = {'bone_a': np.zeros(3), 'bone_b': np.zeros(3),
                           'ground': np.zeros(3)}
        recip = (0.0, 0.0, 0.0)
        d_friction = 0.0
        d_impact_physical = 0.0
        jn_applied_total = 0.0
        accum_jn = {}
        for iteration in range(GS_CAP):
            iterations = iteration + 1
            records = []
            pass_max = 0.0
            for (va, vb, gap, normal, key) in active:
                va_pre = np.asarray(va.velocity, dtype=np.float64).copy()
                vb_pre = np.asarray(vb.velocity, dtype=np.float64).copy()
                rec = lc.solve_contact(va, vb, gap, normal, key)
                va_post = np.asarray(va.velocity, dtype=np.float64)
                vb_post = np.asarray(vb.velocity, dtype=np.float64)
                # identities attached here (lc._tag is solve_tick's job;
                # this world declares them at its own port level)
                rec['body_a'] = va.id
                rec['body_b'] = vb.id
                rec['tri_a'] = va._holder.tri_index
                rec['tri_b'] = vb._holder.tri_index
                rec['area_a'] = va._holder._bone.tri_area_now(rec['tri_a']) \
                    if isinstance(va._holder, BoneTriPort) \
                    else lc.tri_area(*va._holder.verts())
                rec['area_b'] = vb._holder._bone.tri_area_now(rec['tri_b']) \
                    if isinstance(vb._holder, BoneTriPort) \
                    else lc.tri_area(*vb._holder.verts())
                pass_max = max(pass_max, rec['jn_Ns'], abs(rec['jt_Ns']))
                records.append(rec)
                accum_jn[key] = accum_jn.get(key, 0.0) + abs(rec['jn_Ns'])
                ja = np.array(rec['impulse_on_a'])
                jb = np.array(rec['impulse_on_b'])
                contact_impulse[_body_of(rec['body_a'])] += ja
                contact_impulse[_body_of(rec['body_b'])] += jb
                recip = lc.vadd(recip, tuple(rec['impulse_on_a']))
                recip = lc.vadd(recip, tuple(rec['impulse_on_b']))
                d_friction += float(rec.get('w_f_ke_J', 0.0))
                jn_applied_total += abs(rec['jn_Ns'])
                vn_pre = float(np.dot(va_pre - vb_pre,
                                      np.asarray(normal, dtype=np.float64)))
                if vn_pre < 0.0:
                    d_impact_physical += 0.5 * rec['m_eff'] * vn_pre * vn_pre
            max_jn = pass_max
            if pass_max <= GS_TOL_N_S:
                break
        require(max_jn <= GS_TOL_N_S, 'convergence_gate_not_met')
        self.gs_residual_worst = max(self.gs_residual_worst, max_jn)
        ke_after = self._kinetic()
        # joint (bone_a vs bone_b) summary: gap/normal/mode from the FINAL
        # pass (fixed across passes), impulses ACCUMULATED over all passes
        # (the final pass's jn is ~0 by the convergence gate — M07's
        # ledger-covers-all-passes discipline)
        joint_gap = None
        joint_normal = None
        joint_jn = 0.0
        patch = []
        ground_jn = {'bone_a': 0.0, 'bone_b': 0.0}
        bb_impulse_total = np.zeros(3)
        for rec, (va, vb, gap, normal, key) in zip(records, active):
            names = (rec['body_a'], rec['body_b'])
            heads = {n.split('/')[0] for n in names}
            if heads == {'bone_a', 'bone_b'}:
                joint_gap = float(gap)
                joint_normal = [float(c) for c in normal]
                jn_acc = accum_jn.get(key, 0.0)
                joint_jn += jn_acc
                patch.append((rec['body_a'], int(rec['tri_a']), jn_acc))
                patch.append((rec['body_b'], int(rec['tri_b']), jn_acc))
            elif 'ground' in heads:
                other = 'bone_a' if 'bone_a' in heads else 'bone_b'
                ground_jn[other] += accum_jn.get(key, 0.0)
        # bone-bone impulses (all passes) tracked separately so the anchor
        # consistency gate can isolate the ground-transmitted impulse
        for rec, (va, vb, gap, normal, key) in zip(records, active):
            heads = {rec['body_a'].split('/')[0], rec['body_b'].split('/')[0]}
            if heads == {'bone_a', 'bone_b'}:
                bb_impulse_total += (np.array(rec['impulse_on_a'])
                                     + np.array(rec['impulse_on_b']))
        return {
            'records_count': len(records), 'iterations': iterations,
            'gs_residual_N_s': max_jn,
            'contact_impulse': contact_impulse,
            'recip_residual': lc.vlen(recip),
            'w_contact_ke_j': -(ke_after - ke_pre),
            'd_friction_j': d_friction,
            'd_impact_physical_j': d_impact_physical,
            'jn_applied_total_N_s': jn_applied_total,
            'active_pairs': len(active),
            'joint_gap_m': joint_gap, 'joint_normal': joint_normal,
            'joint_jn_Ns': joint_jn, 'joint_patch': patch,
            'ground_jn_N_s': ground_jn,
            'bb_impulse': bb_impulse_total,
        }

    # -- one tick ----------------------------------------------------------
    def step(self, tick):
        bone_a, bone_b = self.bone_a, self.bone_b
        bones = (('bone_a', bone_a), ('bone_b', bone_b))
        acts = []
        if tick == BIND_TICK:
            self.bind_connections(tick)
            acts.append('bind')
        if tick == RELEASE_TICK:
            self.release_connections(tick)
            acts.append('release')
        e_rel_tick = self.e_diss_release if tick == RELEASE_TICK else 0.0
        gvec = np.array([0.0, 0.0, -G_M_S2])
        W = {'act': 0.0, 'lig': 0.0, 'cap': 0.0, 'grav': 0.0}
        Q_damp = 0.0
        Q_contact = 0.0
        Q_proj = 0.0
        ledger_worst = {b: 0.0 for b, _ in bones}
        v_start = {b: bone.v.copy() for b, bone in bones}
        contact_acc = {'bone_a': np.zeros(3), 'bone_b': np.zeros(3),
                       'ground': np.zeros(3)}
        recip_worst = 0.0
        n_active = 0
        joint_gap = None
        joint_normal = None
        joint_jn = 0.0
        gs_worst_tick = 0.0
        patch = {}
        d_friction = d_impact = jn_total = 0.0
        iters = 0
        imp_grav = {b: np.zeros(3) for b, _ in bones}
        imp_damp = {b: np.zeros(3) for b, _ in bones}
        imp_elem = {b: np.zeros(3) for b, _ in bones}
        bb_impulse_tick = np.zeros(3)
        ground_jn_tick = {'bone_a': 0.0, 'bone_b': 0.0}
        for _sub in range(N_SUB):
            # stage 1: gravity (work recorded), then declared damping (KE)
            v_grav = {}
            v_start_sub = {}
            for b, bone in bones:
                v0 = bone.v
                vg = v0 + gvec * H_SUB
                dx = 0.5 * (v0 + vg) * H_SUB
                W['grav'] += float((bone.masses[:, None] * gvec * dx).sum())
                kin0 = float((0.5 * bone.masses[:, None] * vg ** 2).sum())
                bone.v = vg * (1.0 - damping_of_tick(tick) * H_SUB)
                kin1 = float((0.5 * bone.masses[:, None] * bone.v ** 2).sum())
                Q_damp += kin0 - kin1
                v_start_sub[b] = v0
                v_grav[b] = vg
                imp_grav[b] += bone.total_mass * gvec * H_SUB
                imp_damp[b] += (bone.masses[:, None]
                                * (bone.v - vg)).sum(axis=0)
            # stage 2: connective elements + actuator (trapezoid work)
            el = self._element_loads()
            act_b = self._actuator_load(tick)
            for b, bone in bones:
                ld = el['loads_a'] if b == 'bone_a' \
                    else el['loads_b'] + act_b
                v_pre = bone.v
                bone.v = bone.v + ld * bone.inv_masses[:, None] * H_SUB
                dx = 0.5 * (v_pre + bone.v) * H_SUB
                W['lig'] += float((el['lig_a' if b == 'bone_a'
                                    else 'lig_b'] * dx).sum())
                W['cap'] += float((el['cap_a' if b == 'bone_a'
                                    else 'cap_b'] * dx).sum())
                if b == 'bone_b':
                    W['act'] += float((act_b * dx).sum())
                imp_elem[b] += (bone.masses[:, None]
                                * (bone.v - v_pre)).sum(axis=0)
            # stage 3: contact (M06 arithmetic; GS to the declared gate)
            v_pre_contact = {b: bone.v.copy() for b, bone in bones}
            st = self._contact_stage()
            n_active = st['active_pairs']
            gs_worst_tick = max(gs_worst_tick, st['gs_residual_N_s'])
            iters = st['iterations']
            d_friction += st['d_friction_j']
            d_impact += st['d_impact_physical_j']
            jn_total += st['jn_applied_total_N_s']
            Q_contact += st['w_contact_ke_j']
            recip_worst = max(recip_worst, st['recip_residual'])
            for body in contact_acc:
                contact_acc[body] += st['contact_impulse'][body]
            for b in ground_jn_tick:
                ground_jn_tick[b] += st['ground_jn_N_s'][b]
            bb_impulse_tick += st['bb_impulse']
            if st['joint_gap_m'] is not None:
                joint_gap = st['joint_gap_m']
                joint_normal = st['joint_normal']
                joint_jn = max(joint_jn, st['joint_jn_Ns'])
                for (pid, ti, jn) in st['joint_patch']:
                    key = (pid, ti)
                    patch[key] = patch.get(key, 0.0) + jn
            # per-substep momentum ledger over stages 1-3 (telescoping
            # recorded deltas: m*(v4-v0) == grav + damp + elem + contact)
            for b, bone in bones:
                v1 = v_grav[b]
                v2 = v1 * (1.0 - damping_of_tick(tick) * H_SUB)
                ld = el['loads_a'] if b == 'bone_a' \
                    else el['loads_b'] + act_b
                v3 = v2 + ld * bone.inv_masses[:, None] * H_SUB
                v4 = bone.v
                m = bone.masses
                lhs = (m[:, None] * (v4 - v_start_sub[b])).sum(axis=0)
                rhs = ((m[:, None] * (gvec * H_SUB)).sum(axis=0)
                       + (m[:, None] * (v2 - v1)).sum(axis=0)
                       + (m[:, None] * (v3 - v2)).sum(axis=0)
                       + (m[:, None] * (v4 - v_pre_contact[b])).sum(axis=0))
                err = float(np.abs(lhs - rhs).max())
                require(err <= 1e-12, 'ledger_imbalance')
                ledger_worst[b] = max(ledger_worst[b], err)
            # stage 4: position integration + tolerance-driven XPBD; the
            # projection's kinetic-energy exchange is MEASURED and enters
            # the ledger (M07 e_stab heritage; Amendment A1)
            ke_pre_proj = self._kinetic()
            for b, bone in bones:
                x_pre = bone.x.copy()
                bone.x = bone.x + bone.v * H_SUB
                self._project(bone)
                bone.v = (bone.x - x_pre) / H_SUB
            Q_proj += ke_pre_proj - self._kinetic()
        require(recip_worst <= 1e-12, 'ledger_imbalance')
        # FB3 clean gates (the declared visible support must be real and
        # recorded): (a) no bone sinks through the declared ground;
        # (b) the recorded anchor reaction closes against the bones'
        # measured tick momentum change minus all other recorded impulses
        # (a dropped/hidden support reaction refuses here).
        z_min = float(min(bone.x[:, 2].min() for _, bone in bones))
        require(z_min >= -THICKNESS_M - 2.5e-3, 'support_lost_or_hidden')
        dv_sys = {b: (bone.masses[:, None]
                      * (bone.v - v_start[b])).sum(axis=0)
                  for b, bone in bones}
        pred_anchor = np.zeros(3)
        for b, _ in bones:
            pred_anchor += (dv_sys[b] - imp_grav[b] - imp_damp[b]
                            - imp_elem[b])
        pred_anchor -= bb_impulse_tick
        anchor_err = float(np.abs(pred_anchor - (-contact_acc['ground']))
                           .max())
        require(anchor_err <= 1e-12, 'ledger_imbalance')
        # energies at the END-of-tick configuration
        u_lig = self.lig.stored_energy() if self.lig is not None else 0.0
        u_cap = self.cap.stored_energy() if self.cap is not None else 0.0
        u_scaff = bone_a.scaffold_energy() + bone_b.scaffold_energy()
        kin = self._kinetic()
        e_mech = kin + u_lig + u_cap + u_scaff
        q_total = Q_damp + Q_contact + Q_proj + e_rel_tick
        prev = self.ticks[-1] if self.ticks else None
        e_prev = prev['e_mechanical_j'] if prev else 0.0
        w_sum = W['act'] + W['lig'] + W['cap'] + W['grav']
        residual = e_mech - e_prev - w_sum + q_total
        turnover = abs(w_sum) + q_total + kin
        bound = 1e-9 + 5e-2 * turnover
        if prev:
            bound += (prev['u_ligament_j'] + u_lig + prev['u_capsule_j']
                      + u_cap + prev['u_scaffold_j'] + u_scaff)
        if e_rel_tick > 0.0:
            bound = min(bound, max(5e-2 * e_rel_tick, 1e-12))
        require(abs(residual) <= bound, 'unexplained_energy')
        gap_x = float(bone_b.head_anchor[0] - bone_a.head_anchor[0])
        if joint_gap is None or joint_gap > lc.MARGIN:
            contact_state = 'separated'
        elif joint_jn > 0.0:
            contact_state = 'loaded'
        else:
            contact_state = 'touching'
        k_mat, contrib = restraint_matrix(self.lig, self.cap)
        k_rec = restraint_matrix_recomputed(self.lig, self.cap)
        scale = max(1.0, float(np.abs(k_mat).max()))
        rel_err = float(np.abs(k_mat - k_rec).max()) / scale
        require(rel_err <= 1e-15, 'restraint_recompute_mismatch')
        # area-scaled contact-patch report (uniform pressure over the
        # contacted area: p = Jn_total / (DT_S * sum A_i); F_i = p * A_i —
        # M06 area_split heritage; the FB4 bite target)
        patch_report = {}
        if patch:
            by_body = {}
            for (pid, ti), jn in patch.items():
                by_body.setdefault(_body_of(pid), {})[ti] = jn
            for body, tris in by_body.items():
                bone = bone_a if body == 'bone_a' else bone_b
                areas = {ti: bone.tri_area_now(ti) for ti in tris}
                total_a = sum(areas.values())
                require(total_a > 0.0, 'zero_area_interface')
                p = sum(tris.values()) / (DT_S * total_a)
                patch_report[body] = {
                    'pressure_pa': p,
                    'per_triangle_area_m2': {str(t): a
                                             for t, a in sorted(areas.items())},
                    'per_triangle_load_n': {str(t): p * a
                                            for t, a in sorted(areas.items())},
                }
        row = {
            'tick': tick, 'phase': phase_of(tick), 'acts': acts,
            'gap_head_anchors_m': gap_x,
            'contact_state': contact_state,
            'joint_gap_m': joint_gap,
            'joint_normal': joint_normal,
            'joint_jn_Ns': joint_jn,
            'contact_active_pairs': n_active,
            'contact_iterations': iters,
            'gs_residual_N_s': gs_worst_tick,
            'jn_applied_total_N_s': jn_total,
            'd_friction_j': d_friction, 'd_impact_physical_j': d_impact,
            'lig_bound': bool(self.lig is not None
                              and self.lig.bound_tick is not None
                              and self.lig.released_tick is None),
            'lig_tension_n': (self.lig.tension()
                              if self.lig is not None
                              and self.lig.status != 'planned' else 0.0),
            'lig_force_n': [float(c) for c in
                            (self.lig.force_on_b()
                             if self.lig is not None
                             and self.lig.status != 'planned'
                             else np.zeros(3))],
            'lig_extension_m': (self.lig.extension()
                                if self.lig is not None
                                and self.lig.status != 'planned' else 0.0),
            'cap_bound': bool(self.cap is not None
                              and self.cap.bound_tick is not None
                              and self.cap.released_tick is None),
            'cap_axial_n': (self.cap.axial_force_n()
                            if self.cap is not None
                            and self.cap.status != 'planned' else 0.0),
            'cap_force_n': [float(c) for c in
                            (self.cap.force_on_b()
                             if self.cap is not None
                             and self.cap.status != 'planned'
                             else np.zeros(3))],
            'u_ligament_j': u_lig, 'u_capsule_j': u_cap,
            'u_scaffold_j': u_scaff, 'e_kinetic_j': kin,
            'e_mechanical_j': e_mech,
            'w_actuator_j': W['act'], 'w_ligament_j': W['lig'],
            'w_capsule_j': W['cap'], 'w_gravity_j': W['grav'],
            'q_damping_j': Q_damp, 'q_contact_j': Q_contact,
            'q_projection_j': Q_proj,
            'e_diss_release_j': e_rel_tick,
            'residual_r_j': residual, 'residual_bound_j': bound,
            'restraint_matrix': [float(c) for c in k_mat.ravel()],
            'restraint_contrib': contrib,
            'restrained_direction_count': restrained_direction_count(k_mat),
            'contact_patch_report': patch_report,
            'ground_anchor_impulse_N_s': [float(c) for c in
                                          (-contact_acc['ground'])],
            'ground_jn_N_s': {b: ground_jn_tick[b] for b in ground_jn_tick},
            'min_vertex_z_m': z_min,
            'anchor_consistency_err_N_s': anchor_err,
            'ledger_residual_worst_N_s': max(ledger_worst.values()),
            'com_a_m': [float(c) for c in bone_a.x.mean(axis=0)],
            'com_b_m': [float(c) for c in bone_b.x.mean(axis=0)],
            'max_speed_m_per_s': float(max(np.abs(bone_a.v).max(),
                                           np.abs(bone_b.v).max())),
            'state_hash': None,
        }
        row['state_hash'] = digest({k: row[k] for k in sorted(row)
                                    if k != 'state_hash'})
        self.ticks.append(row)
        if tick in DOC_TICKS:
            doc = state_document(tick + 1, bone_a, bone_b, self.lig,
                                 self.cap, contact_state)
            summary = validate_state(doc)
            self.documents[tick] = {'document': doc,
                                    'validator_summary': summary}
        return row

    def _project(self, bone):
        """Tolerance-driven XPBD edge projection (M07 A6 heritage)."""
        alpha_tilde = XPBD_COMPLIANCE_M_PER_N / (H_SUB * H_SUB)
        lam = np.zeros(len(bone.edge_list))
        for _ in range(XPBD_ITERATIONS_CAP):
            worst = 0.0
            for e, (a1, a2) in enumerate(bone.edge_list):
                pa, pb = bone.x[a1], bone.x[a2]
                d = pb - pa
                length = float(np.linalg.norm(d))
                if length == 0.0:
                    continue
                grad = d / length
                c = length - bone.rest_lengths[e]
                worst = max(worst, abs(c))
                w_sum = bone.inv_masses[a1] + bone.inv_masses[a2]
                dlam = (-c - alpha_tilde * lam[e]) / (w_sum + alpha_tilde)
                lam[e] += dlam
                bone.x[a1] -= bone.inv_masses[a1] * dlam * grad
                bone.x[a2] += bone.inv_masses[a2] * dlam * grad
            if worst <= XPBD_TOL_M:
                break

    def run(self, ticks=TICKS):
        for tick in range(ticks):
            self.step(tick)
        return self.ticks


# ------------------------------------------------- element tests (T3) ------

def element_tests():
    """Declared-input element laws (the signs/shapes the dynamic schedule
    does not visit are exercised here — M05 declared-absence heritage).
    Bitwise closed-form comparisons."""
    out = {}
    bones = (BoneBody('bone_a', bone_a_vertices(), MASS_A_KG),
             BoneBody('bone_b', bone_b_vertices(), MASS_B_KG))
    # align the head anchors on one x-parallel line so the declared probe
    # displacements are purely axial (the anchors themselves sit at
    # different rest y/z between the two DIFFERENT bone shapes)
    align = bones[0].head_anchor - bones[1].head_anchor
    bones[1].x[:, 1] += align[1]
    bones[1].x[:, 2] += align[2]
    lig = LigamentElement('lig:probe', bones[0], bones[1])
    lig.bind(0)
    bones[1].x[:, 0] += 0.024
    e = lig.extension()
    out['lig_tension_bitwise'] = lig.tension() == LIG_K_T_N_PER_M \
        * max(0.0, e)
    out['lig_energy_1e15'] = abs(lig.stored_energy() - 0.5
                                 * LIG_K_T_N_PER_M * max(0.0, e) ** 2) \
        <= 1e-15 * max(1.0, lig.stored_energy())
    out['lig_rel_axial_1e15'] = abs(lig.tension()
                                    - LIG_K_T_N_PER_M * max(0.0, e)) \
        <= 1e-15 * max(1.0, abs(lig.tension()))
    out['lig_reciprocal_bitwise'] = bool(np.all(
        lig.force_on_a() == -lig.force_on_b()))
    bones[1].x[:, 0] -= 0.13          # |delta| 0.014 < rest 0.02: slack
    f_slack = lig.force_on_b()
    # sealed law: slack ligament -> tension BITWISE zero and ZERO axial
    # force; the transverse shear term is a real restoring force (its
    # magnitude at the declared alignment precision is ~1e-17 N)
    f_slack = lig.force_on_b()
    axial = float(np.dot(f_slack, lig.axis()))
    out['lig_slack_zero_tension'] = (lig.tension() == 0.0
                                     and abs(axial) <= 1e-30
                                     and float(np.linalg.norm(f_slack))
                                     <= 1e-15)
    cap_bones = (BoneBody('bone_a', bone_a_vertices(), MASS_A_KG),
                 BoneBody('bone_b', bone_b_vertices(), MASS_B_KG))
    align2 = cap_bones[0].head_anchor - cap_bones[1].head_anchor
    cap_bones[1].x[:, 1] += align2[1]
    cap_bones[1].x[:, 2] += align2[2]
    cap = CapsuleElement('cap:probe', cap_bones[0], cap_bones[1])
    cap.bind(0)
    cap_bones[1].x[:, 0] += 0.05
    out['cap_tension_signed'] = cap.axial_force_n() \
        == CAP_K_C_N_PER_M * cap.extension()
    cap_bones[1].x[:, 0] -= 0.10
    out['cap_compression_signed'] = cap.axial_force_n() < 0.0 \
        and cap.axial_force_n() == CAP_K_C_N_PER_M * cap.extension()
    out['cap_energy_1e15'] = abs(cap.stored_energy() - 0.5
                                 * CAP_K_C_N_PER_M * cap.extension() ** 2) \
        <= 1e-15 * max(1.0, cap.stored_energy())
    out['cap_reciprocal_bitwise'] = bool(np.all(
        cap.force_on_a() == -cap.force_on_b()))
    fresh = LigamentElement('lig:fresh', bones[0], bones[1])
    refusals = {}
    try:
        fresh.tension()
    except ValueError as exc:
        refusals['bond_not_bound'] = str(exc) == m05.REFUSAL_BOND_NOT_BOUND
    fresh.bind(0)
    try:
        fresh.bind(0)
    except ValueError as exc:
        refusals['bond_already_bound'] = \
            str(exc) == m05.REFUSAL_BOND_ALREADY_BOUND
    fresh.release(0)
    try:
        fresh.release(0)
    except ValueError as exc:
        refusals['release_of_unbound_bond'] = \
            str(exc) == m05.REFUSAL_RELEASE_UNBOUND
    try:
        refuse_auto_bond()
    except ValueError as exc:
        refusals['auto_bond_refused'] = \
            str(exc) == m05.REFUSAL_AUTO_BOND
    out['refusals'] = refusals
    return out
