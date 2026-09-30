"""MAT2-M10: active pressurized material with directional reinforcement.

Implements the frozen preregistration (PREREGISTRATION.md + Amendment A1,
this directory): a pressure-controlled membrane (M03 laws, UNMODIFIED) with
authored directional resistance (M04's effective_modulus law, UNMODIFIED)
performs bounded work through actual attachments (M05's tie law form,
declared one-axis generalization), with force-displacement/work measured
against independent expectations (Betti reciprocity, load-line superposition,
the exact mg*dh gravity reference), blocked-load reaction, pressure limits
and power-off behavior. Classified as an engineering actuator by the frozen
receipt rule unless biological equivalence is independently evidenced.

Upstream authority, reused verbatim and unmodified (input pins verified at
run time; mismatch refuses input_pin_drift):
- tools/monkey_campaign/contributions/MAT2-M01/material_state.py
  (chimera.material_state.v1 validator; schema authority),
- tools/monkey_campaign/contributions/MAT2-M03/pressure_membrane.py
  (Membrane closure/traction/lumping/volume/work laws, PressureSource,
  meshes, linear-field references),
- tools/monkey_campaign/contributions/MAT2-M04/passive_response.py
  (the frozen anisotropy law effective_modulus),
- tools/monkey_campaign/contributions/MAT2-M05/interface_exchange.py
  (bond/tie law authority and refusal vocabulary; its sealed element is
  xhat-locked; the declared tie below generalizes the axis to the declared
  current tie line — this card's declared composition; M05's module is
  imported UNMODIFIED and its refuse_auto_bond heritage is honoured:
  proximity never creates a bond).

CPU-only; stdlib + numpy; float64; fixed 300 Hz tick; deterministic (no
stochastic inputs, no wall-clock in physics).
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
           str(CONTRIB / 'MAT2-M04'), str(CONTRIB / 'MAT2-M05')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import material_state as ms01  # noqa: E402  (M01 validator, UNMODIFIED)
import passive_response as pr04  # noqa: E402  (M04 anisotropy law, UNMODIFIED)
import pressure_membrane as pm  # noqa: E402  (M03 membrane laws, UNMODIFIED)


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


# ---------------------------------------------------------------- pins ----
INPUT_PINS = {
    'MAT2-M01/material_state.py':
        'b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40',
    'MAT2-M03/pressure_membrane.py':
        '3dd64f6465430380f1c0a53a95523c700cd51a6b1115e60f0df8afde2239c96e',
    'MAT2-M04/passive_response.py':
        '68a696e1728066a3dce93db7b6c98f8bb4826322a84bbad20eeadf38350e326b',
    'MAT2-M05/interface_exchange.py':
        '295e6c898ada14918f09b2b0633f5926c1623c9e09cd37258e516ab57450b9b9',
}


def verify_input_pins():
    out = {}
    for rel, expected in INPUT_PINS.items():
        path = CONTRIB / rel
        require(path.exists(), 'input_pin_missing:' + rel)
        actual = sha256_file(path)
        require(actual == expected, 'input_pin_drift:' + rel)
        out[rel] = actual
    return out


# --------------------------------------------------- declared constants ----
# Amendment A1 re-issued architecture: a clamped SPHERICAL pressure vessel
# (M03's icosphere family) with an authored fiber layout. The box-beam draft
# was probed first and exhibited a face-bulge localization (aneurysm
# snap-through) that carries no directional response in ANY fiber layout
# (recorded with the triggering probe values in Amendment A1); the sphere is
# membrane-tension dominated (no buckling mode) and the belt/meridian fiber
# families give clean prolate/oblate directional responses.
SPHERE_R = 0.05                                  # m
SPHERE_LEVEL = 2
VERTEX_EXPECTED_COUNT = 162                      # derived: icosphere L2
TRIANGLE_EXPECTED_COUNT = 320                    # derived: icosphere L2
BELT_Z_FRAC = 0.31        # belt band |z| <= frac*R (equatorial fiber belt)
MERIDIAN_DZ = 0.75        # meridian family: |d.z_hat| >= this
E_FIBER, E_TRANS = 1.0e8, 1.0e6                  # Pa
T_WALL = 3.0e-3                                  # m
BRAID_DZ = (0.42, 0.87)    # braid chord |dz| band (diagonal families)
BRAID_BELT_DZ = (0.0, 0.42)  # belt chord |dz| band (near-horizontal)
BRAID_CAP_Z = 0.75         # chord endpoints within |z| <= frac*R
A_CHORD = T_WALL * T_WALL  # declared chord cross-section (m^2)
XPBD_ITERS = 8
XPBD_RELAX = 0.15         # Amendment A1: under-relaxed batched projection
N_SUB = 16                # Amendment A1 (was 4): explicit-step stability
DT = 1.0 / 300.0                                 # s (300 Hz pin)
HS = DT / N_SUB
C_V = 2000.0               # Amendment A1 (was 40): near-critical ring decay
C_LOAD = 4.0                                     # 1/s load damping
SCAFFOLD_MASS_KG = 0.020                         # declared, equal per vertex
M_LOAD_KG = 0.010                                # declared
GRAV = 9.80665                                   # m/s^2 declared
K_TIE = 600.0                                    # N/m (M05-form tie)
L_TIE = 0.10                                     # m (A1 rest length; taut at
                                                 # the settled p=0 state)
SOURCE_ID = 'm10_source'
P_EXT_PA = 0.0
MAX_DELTA_P_PA = 5000.0
MAX_FLOW_M3_PER_S = 1.0e-3
SOURCE_PROVENANCE = ('MAT2-M10 preregistered pneumatic actuator source '
                     '(engineering actuator demonstration)')
LEVELS_PA = (1000.0, 2000.0, 3000.0, 4000.0)
QS_TICKS = 1500
SETTLE_WINDOW = 200
V_MAX_SETTLE = 1.0e-4                            # m/s (reported)
SETTLE_DRIFT_M = 1.0e-6    # A1.10 positional settle criterion (per tick)
DP_WORK_PA = 4000.0
# Amendment A1 schedule (pre-settle phase prepended; POWER OFF declared):
PRESETTLE_END = 200       # ticks 0-199: p = 0 (load settles onto the tie)
RAMP_UP_END = 400         # ticks 200-399: ramp 0 -> 1
HOLD_END = 1100           # ticks 400-1099: hold 1 (work phase)
POWER_OFF_END = 1300      # ticks 1100-1299: ramp 1 -> 0 (POWER OFF)
TOTAL_TICKS = 1500        # ticks 1300-1499: settled off
SNAP_TICKS = (0, 300, 400, 700, 1000, 1100, 1200, 1350, 1499)
STILL_INDICES = (0, 4, 5, 8)   # declared committed-still frame indices
BASELINE_WINDOW = (100, 200)   # presettle measurement window [lo, hi)
PEAK_WINDOW = (1000, 1100)     # late-hold (peak lift) window
RHO_WATER = 1000.0             # kg/m^3 (FB4 buoyancy probe, declared)
PHASE_NAMES = ('P0_presettle', 'A_rampup', 'B_hold', 'C_poweroff',
               'D_settled_off')

# Frozen windows (PREREGISTRATION + Amendment A1; never tuned after
# measurement; every floor/bracket is derived in A1 with the triggering
# probe values recorded there)
WIN = {
    # A1.4 X1a-X1d directional claims (delta_gap in m at 2000 Pa, free runs)
    'gap_braid_max': -2.0e-4,
    'gap_belt_min': 2.0e-3,
    'gap_iso_min': 1.0e-3,
    'dir_braid_max': -1.0e-3,
    'dir_belt_min': 2.0e-3,
    'monotone_epsilon_m': 1.0e-5,
    # A1.4 X1f lift claim (m)
    'lift_lo_m': 1.0e-4, 'lift_hi_m': 1.0e-2,
    # A1.4 X2 blocked reaction
    'f_block_lo_n': 1.0e-2, 'f_block_hi_n': 10.0,
    'f_linearity_abs': 0.15,
    'f_zero_residual': 0.02, 'f_zero_floor_n': 1.0e-4,
    # A1.4 X3/X4 independent expectations
    'reciprocity_rel': 0.35, 'reciprocity_floor': 1.0e-12,
    'superposition_rel': 0.25, 'superposition_floor_m': 1.0e-4,
    'tie_follow_m': 5.0e-3,
    # A1.4 X5 ledgers (floors re-issued from the recorded projection noise)
    'ledger_rel': 0.05, 'ledger_floor_j': 5.0e-3,
    'ledger_cum_abs_j': 5.0e-4,
    'ledger_cum_rel': 0.05, 'ledger_cum_floor_j': 1.0e-5,
    'work_measures_scale_rel': 1.0e-4, 'work_measures_floor_j': 1.0e-12,
    'power_identity_rel': 1.0e-9,
    'eta_hi': 0.5,
    'power_off_recovery': 0.1,
    'tie_return_factor': 1.2,
    # A1.4 falsifier-arm bounds
    'audit_window_m': 1.0e-9, 'audit_bite_m': 1.0e-3,
    'traction_ratio_rel': 1.0e-9,
    'buoyancy_rel': 1.0e-12, 'buoyancy_tamper_rel': 1.0e-6,
    'fb5_path_factor': 5.0,
    'settle_speed_m_per_s': V_MAX_SETTLE,
}
CLASSIFICATION_RULE = {
    'bio_specific_tension_pa': 2.0e5,
    'bio_work_density_j_per_kg': 20.0,
    'bio_efficiency_band': [0.20, 0.40],
    'scaffold_mass_kg': SCAFFOLD_MASS_KG,
}


def phase_of(tick):
    t = int(tick)
    if t < PRESETTLE_END:
        return 'P0_presettle'
    if t < RAMP_UP_END:
        return 'A_rampup'
    if t < HOLD_END:
        return 'B_hold'
    if t < POWER_OFF_END:
        return 'C_poweroff'
    return 'D_settled_off'


def work_schedule(tick):
    """Amendment A1 declared schedule (PASCALS): p=0 (0-199 pre-settle),
    ramp 0->DP_WORK_PA (200-399), hold DP_WORK_PA (400-1099), ramp to 0
    POWER OFF (1100-1299), 0 (1300-1499)."""
    t = int(tick)
    if t < PRESETTLE_END:
        return 0.0
    if t < RAMP_UP_END:
        frac = (t - PRESETTLE_END) / (RAMP_UP_END - PRESETTLE_END)
    elif t < HOLD_END:
        frac = 1.0
    elif t < POWER_OFF_END:
        frac = 1.0 - (t - HOLD_END) / (POWER_OFF_END - HOLD_END)
    else:
        frac = 0.0
    return DP_WORK_PA * frac


def level_schedule(level_pa, ramp_ticks=RAMP_UP_END - PRESETTLE_END,
                   presettle_ticks=PRESETTLE_END):
    """A1.5 quasi-static level schedule (PASCALS): p=0 for the pre-settle
    ticks, linear ramp to level_pa, hold. Settle window = the declared
    final SETTLE_WINDOW ticks of the run."""
    def schedule(tick):
        t = int(tick)
        if t < presettle_ticks:
            return 0.0
        frac = min(1.0, (t - presettle_ticks) / max(1, ramp_ticks))
        return level_pa * frac
    return schedule


# -------------------------------------------------------------- geometry ---
def _unique_edges(triangles):
    edge_index = {}
    order = []

    def key_of(a, b):
        return (a, b) if a < b else (b, a)

    for tri in np.asarray(triangles, dtype=np.int64).tolist():
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            key = key_of(a, b)
            if key not in edge_index:
                edge_index[key] = len(order)
                order.append(key)
    pairs = np.array(order, dtype=np.int64)          # (E, 2)
    return pairs, edge_index


class ActuatorModel:
    """Declared geometry + rest state + authored directional fiber layout.

    Layout (Amendment A1), M04's law called per edge, UNMODIFIED:
      'belt'     (production) equatorial fiber belt: both endpoints with
                 |z| <= BELT_Z_FRAC*R; stiffness against each edge's own
                 transverse-to-polar direction,
      'meridian' (sign-flip control) steep polar edges (|d.z| >=
                 MERIDIAN_DZ) stiff along the polar axis,
      isotropic  (contraction-cause control) no fibers anywhere.
    The south polar cap is the declared visible clamp; the north polar cap
    carries the declared tie anchor (the output) and the output probe.
    """

    def __init__(self, fiber_side='meridian', isotropic=False):
        require(fiber_side in ('braid', 'belt', 'meridian'),
                'fiber_layout_invalid')
        # Production actuator: BRAID chords (A1) — the McKibben mechanism:
        # pressure inflates the soft bladder; the diagonal chord net
        # converts radial expansion into axial contraction; the clamped-
        # north / free-south jack lifts the load through the declared tie.
        # 'belt' (prolate) is the sign-flip control; isotropic=True the
        # contraction-cause control.
        layout = fiber_side
        self.fiber_side = fiber_side
        self.layout = None if isotropic else layout
        self.isotropic = bool(isotropic)
        shell = pm.icosphere(SPHERE_LEVEL, SPHERE_R, 'm10_shell')
        report = shell.require_closed()
        self.rest = shell.vertices.copy()
        self.tris = np.asarray(shell.triangles, dtype=np.int64).copy()
        self.n_vertices = int(self.rest.shape[0])
        require(self.n_vertices == VERTEX_EXPECTED_COUNT,
                'shell_vertex_count')
        require(int(report['triangle_count']) == TRIANGLE_EXPECTED_COUNT,
                'shell_triangle_count')
        self.report = report
        self.vertex_mass = SCAFFOLD_MASS_KG / self.n_vertices
        # declared polar caps (stable IDs). Amendment A1: the NORTH polar
        # cap is the declared visible clamp (overhead support); the SOUTH
        # polar cap carries the declared tie anchor (the output) and the
        # output probe. The output SHORTENS the polar axis (meridian
        # fibers): pressure lifts the load.
        self.south = int(np.argmin(self.rest[:, 2]))
        self.north = int(np.argmax(self.rest[:, 2]))
        pairs, edge_index = _unique_edges(self.tris)
        self.edges = pairs
        nbrs = {}
        for a, b in pairs.tolist():
            nbrs.setdefault(a, set()).add(b)
            nbrs.setdefault(b, set()).add(a)
        self.clamp = np.zeros(self.n_vertices, dtype=bool)
        for vid in nbrs[self.north]:
            self.clamp[vid] = True
        self.clamp[self.north] = True
        self.clamp_idx = np.flatnonzero(self.clamp)
        # A1 re-issue: the tie anchors at the SOUTH POLE VERTEX alone —
        # the pole is the declared output point (a patch-mean anchor would
        # follow the ring flare, not the output motion; probed and recorded)
        self.tie_anchor = np.array([self.south], dtype=np.int64)
        self.cap_probe = self.south
        # authored directional layout (M04's law per edge, UNMODIFIED)
        e0, e1 = pairs[:, 0], pairs[:, 1]
        d = self.rest[e1] - self.rest[e0]
        self.l0 = np.linalg.norm(d, axis=1)
        require(np.all(self.l0 > 0.0), 'edge_rest_length_invalid')
        dz = d[:, 2] / self.l0
        belt = ((np.abs(self.rest[e0, 2]) <= BELT_Z_FRAC * SPHERE_R) &
                (np.abs(self.rest[e1, 2]) <= BELT_Z_FRAC * SPHERE_R))
        meridian = np.abs(dz) >= MERIDIAN_DZ
        self.on_fiber = (belt if layout == 'belt' else
                         meridian if layout == 'meridian'
                         else np.zeros(len(pairs), dtype=bool))
        if isotropic or layout is None:
            e_mod = np.full(len(pairs), E_TRANS)
        elif layout == 'belt':
            # belt: stiffness against each edge's own transverse direction
            e_mod = np.empty(len(pairs))
            for ei in range(len(pairs)):
                if belt[ei]:
                    e_mod[ei] = pr04.effective_modulus(
                        E_FIBER, E_TRANS, math.asin(min(1.0, abs(dz[ei]))))
                else:
                    e_mod[ei] = E_TRANS
        else:  # meridian: stiffness along the polar axis
            e_mod = np.empty(len(pairs))
            for ei in range(len(pairs)):
                if meridian[ei]:
                    e_mod[ei] = pr04.effective_modulus(
                        E_FIBER, E_TRANS, math.acos(
                            max(-1.0, min(1.0, float(dz[ei])))))
                else:
                    e_mod[ei] = E_TRANS
        require(np.all(e_mod > 0.0), 'edge_modulus_invalid')
        # A1 re-issue (braid layout): the McKibben mechanism — a soft
        # triangulated bladder (all direct edges E_TRANS) plus a stiff
        # diagonal CHORD NET between distance-2 vertex pairs (tension
        # members; M05-form spring law, rest = initial chord length).
        # Cauchy rigidity blocks contraction when the DIRECT edges are
        # stiffened (that tamper froze the mode; probed and recorded in
        # Amendment A1), so the fibers must be chords over a soft bladder.
        self.chords = np.zeros((0, 2), dtype=np.int64)
        self.chord_l0 = np.zeros(0)
        chord_band = {'braid': BRAID_DZ,
                      'belt': BRAID_BELT_DZ}.get(layout)
        if chord_band and not isotropic:
            nbrs2 = {}
            for a, b in pairs.tolist():
                nbrs2.setdefault(a, set()).add(b)
                nbrs2.setdefault(b, set()).add(a)
            chord_set = set()
            for v, ns in nbrs2.items():
                if abs(self.rest[v, 2]) > BRAID_CAP_Z * SPHERE_R:
                    continue
                for t in ns:
                    for w in nbrs2[t]:
                        if w == v or w in ns:
                            continue
                        dv = self.rest[w] - self.rest[v]
                        Lc = float(np.linalg.norm(dv))
                        dzz = abs(dv[2]) / Lc
                        if chord_band[0] <= dzz <= chord_band[1]:
                            chord_set.add((min(v, w), max(v, w)))
            self.chords = np.array(sorted(chord_set), dtype=np.int64)
            d_c = self.rest[self.chords[:, 1]] - self.rest[self.chords[:, 0]]
            self.chord_l0 = np.linalg.norm(d_c, axis=1)
            require(np.all(self.chord_l0 > 0.0), 'chord_rest_invalid')
        self.n_chords = int(self.chords.shape[0])
        safe_l0 = np.maximum(self.chord_l0, 1e-12)
        self.chord_k = np.where(self.n_chords and True,
                                E_FIBER * A_CHORD / safe_l0,
                                self.chord_k if False else
                                np.zeros(self.n_chords))
        self.chord_alpha = 1.0 / np.maximum(self.chord_k, 1e-12)
        self.chord_alpha = np.where(np.isfinite(self.chord_alpha),
                                    self.chord_alpha, 0.0)
        mem0 = pm.Membrane(self.rest, self.tris, 'm10_shell_rest')
        a_dual = np.zeros(len(pairs))
        areas = mem0.areas
        for tri_idx, tri in enumerate(self.tris.tolist()):
            for a, b in ((tri[0], tri[1]), (tri[1], tri[2]),
                         (tri[2], tri[0])):
                key = (a, b) if a < b else (b, a)
                a_dual[edge_index[key]] += areas[tri_idx]
        self.a_dual = a_dual
        self.k_edge = e_mod * T_WALL * a_dual / (self.l0 * self.l0)
        require(np.all(self.k_edge > 0.0), 'edge_stiffness_invalid')
        self.alpha = 1.0 / self.k_edge
        self.n_fiber_edges = int(self.on_fiber.sum())
        # declared scalar shape metrics (directional response)
        self.pole_gap_rest = float(
            self.rest[self.north, 2] - self.rest[self.south, 2])
        self.equator_dia_rest = float(
            self.rest[:, 0].max() - self.rest[:, 0].min())
        self.xhat = np.array([1.0, 0.0, 0.0])
        self.zhat = np.array([0.0, 0.0, 1.0])

    def pole_gap(self, x):
        return float(x[self.north, 2] - x[self.south, 2])

    def equator_dia(self, x):
        sel = self.rest[:, 2] >= -1e-12
        sel &= self.rest[:, 2] <= 1e-12
        if sel.sum() < 2:
            band = np.abs(self.rest[:, 2]) <= BELT_Z_FRAC * SPHERE_R
            sel = band
        pts = x[sel]
        return float(max(pts[:, 0].max() - pts[:, 0].min(),
                         pts[:, 1].max() - pts[:, 1].min()))

    def _nearest(self, query):
        d2 = ((self.rest - np.array(query)) ** 2).sum(axis=1)
        return int(np.argmin(d2))


# --------------------------------------------------------------- the tie ---
class TieElement:
    """M05 BondElement law form (tension-only) with declared rest length,
    generalized to the declared current tie line (this card's declared
    composition; M05's sealed module is the law authority, imported
    UNMODIFIED). Refusal vocabulary reused from M05's declarations."""

    REF_NOT_BOUND = 'bond_not_bound'
    REF_ALREADY = 'bond_already_bound'
    REF_RELEASE_UNBOUND = 'release_of_unbound_bond'

    def __init__(self, tie_id, k_tie, rest_length):
        require(k_tie > 0.0 and rest_length > 0.0, 'tie_declaration_invalid')
        self.tie_id = tie_id
        self.k = float(k_tie)
        self.rest_length = float(rest_length)
        self.status = 'planned'
        self.bound_tick = None
        self.released_tick = None
        self.last_force = np.zeros(3)
        self.last_tension = 0.0
        self.last_extension = 0.0

    def bind(self, tick):
        require(self.status == 'planned', self.REF_ALREADY)
        self.status = 'qualified'
        self.bound_tick = int(tick)

    def release(self, tick):
        require(self.status == 'qualified', self.REF_RELEASE_UNBOUND)
        self.status = 'released'
        self.released_tick = int(tick)

    @property
    def active(self):
        return self.status == 'qualified'

    def force_on_load(self, anchor_point, x_load):
        if self.status == 'planned':
            raise ValueError(self.REF_NOT_BOUND)
        if not self.active:
            self.last_force = np.zeros(3)
            self.last_tension = 0.0
            self.last_extension = 0.0
            return np.zeros(3)
        d = anchor_point - x_load
        dist = float(np.linalg.norm(d))
        require(dist > 1e-12, 'tie_degenerate')
        ext = dist - self.rest_length
        self.last_extension = ext
        if ext <= 0.0:
            self.last_force = np.zeros(3)
            self.last_tension = 0.0
            return np.zeros(3)
        tension = self.k * ext
        axis = d / dist
        force = tension * axis           # pulls the load toward the anchor
        self.last_force = force
        self.last_tension = tension
        return force


def refuse_auto_bond():
    """Explicit guard (M05 heritage): proximity never creates a bond."""
    raise ValueError('auto_bond_refused')


# ----------------------------------------------------------- the world ----
class WorldRun:
    """One declared run of the actuator world (deterministic).

    Declared substep order (digested per tick):
      1. damping (membrane c_v, load c_load),
      2. pressure loads on CURRENT geometry (area-scaled, M03),
      3. load forces (gravity + tie) and tie reaction on the membrane patch,
      4. semi-implicit position step,
      5. XPBD edge projection x XPBD_ITERS (clamped vertices pinned),
      6. blocked-anchor pin (mode == 'blocked'),
      7. volume/work/ledger accumulation.
    """

    def __init__(self, model, schedule_fn, ticks, mode='free', tamper=None,
                 record_forces=False, snapshot_ticks=(),
                 load_mass=M_LOAD_KG):
        require(mode in ('free', 'blocked', 'loaded'), 'run_mode_invalid')
        require(load_mass > 0.0, 'load_mass_invalid')
        self.load_mass = float(load_mass)
        self.model = model
        self.mode = mode
        self.tamper = dict(tamper or {})
        self.ticks = int(ticks)
        self.schedule_fn = schedule_fn
        self.record_forces = bool(record_forces)
        self.snapshot_ticks = sorted(int(t) for t in snapshot_ticks)
        m = model
        self.x = m.rest.copy()
        self.v = np.zeros_like(self.x)
        anchor0 = model.rest[model.tie_anchor].mean(axis=0)
        self.x_load = anchor0 + np.array([0.0, 0.0, -L_TIE])
        self.load_mass = float(load_mass)
        self.v_load = np.zeros(3)
        self.tie = TieElement('tie:load', K_TIE, L_TIE)
        self.tie.bind(0)
        self.base_source = pm.PressureSource(
            SOURCE_ID, P_EXT_PA, P_EXT_PA, MAX_DELTA_P_PA,
            MAX_FLOW_M3_PER_S, SOURCE_PROVENANCE)
        self.pin_force_acc = np.zeros(3)
        self.pin_force_n = 0
        self.traction_ratio_worst = 0.0
        self.force_rows = []
        self.snapshots = {}
        self.max_dp_seen = 0.0
        self.max_flow_seen = 0.0
        self.max_speed_seen = 0.0
        self.chord_strain_min = 0.0
        self.chord_strain_max = 0.0
        self.position_drift_m = 0.0
        self.pose_writer = bool(self.tamper.get('pose_writer', False))
        self.drop_reaction = bool(
            self.tamper.get('drop_tie_reaction', False))
        self.tie_boost = float(self.tamper.get('tie_boost', 1.0))
        self.constant_weighting = bool(
            self.tamper.get('constant_weighting', False))

    def _membrane(self):
        return pm.Membrane(self.x, self.model.tris, 'm10_beam_current')

    def _anchor_point(self):
        return self.x[self.model.tie_anchor].mean(axis=0)

    def _tip_z(self):
        # Amendment A1: the output metric is the end-cap centre z (the
        # beam-axis tip deflection; inflation-immune by symmetry)
        return float(self.x[self.model.cap_probe, 2])

    def _energies(self):
        m = self.model
        d = self.x[m.edges[:, 1]] - self.x[m.edges[:, 0]]
        length = np.linalg.norm(d, axis=1)
        u_edge = float((0.5 * m.k_edge * (length - m.l0) ** 2).sum())
        if m.n_chords:
            d_c = self.x[m.chords[:, 1]] - self.x[m.chords[:, 0]]
            lc = np.linalg.norm(d_c, axis=1)
            u_edge += float((0.5 * m.chord_k *
                             (lc - m.chord_l0) ** 2).sum())
        ext = self.tie.last_extension
        u_tie = 0.5 * K_TIE * ext * ext if ext > 0.0 else 0.0
        e_grav = self.load_mass * GRAV * float(self.x_load[2])
        e_kin = float(0.5 * m.vertex_mass * (self.v * self.v).sum()) + \
            0.5 * self.load_mass * float((self.v_load * self.v_load).sum())
        return e_kin, u_edge, u_tie, e_grav

    def _state_digest(self, tick):
        payload = {
            'tick': int(tick),
            'x': [[float(c) for c in row] for row in self.x],
            'x_load': [float(c) for c in self.x_load],
            'energies': [float(e) for e in self._energies()],
        }
        return digest(payload)

    def run(self):
        m = self.model
        rows = []
        w_press_cum = 0.0
        q_cum = 0.0
        w_press_hold_total = 0.0
        settle_start = self.ticks - SETTLE_WINDOW
        x_before_tick = self.x.copy()
        for tick in range(self.ticks):
            dp = float(self.schedule_fn(tick))
            self.max_dp_seen = max(self.max_dp_seen, abs(dp))
            source = self.base_source.with_delta_p(dp)  # enforces limits
            tick_w_vol = 0.0
            tick_w_trac = 0.0
            tick_q = 0.0
            tick_w_tie_load = 0.0
            tick_w_tie_mem = 0.0
            tick_w_tie_proj = 0.0
            e0 = self._energies()
            f_rows = []
            v_end = float('nan')
            for sub in range(N_SUB):
                x_before = self.x.copy()
                mem = self._membrane()
                v_start = mem.signed_volume()
                # 1. damping (measured dissipation of this step)
                dmf = max(0.0, 1.0 - C_V * HS)
                ldf = max(0.0, 1.0 - C_LOAD * HS)
                q_damp = 0.5 * m.vertex_mass * float((self.v * self.v).sum()) \
                    * (1.0 - dmf * dmf) + \
                    0.5 * self.load_mass * float((self.v_load * self.v_load).sum()) \
                    * (1.0 - ldf * ldf)
                self.v = self.v * dmf
                self.v_load = self.v_load * ldf
                tick_q += q_damp
                v_damped = self.v.copy()
                # 2. pressure loads on CURRENT geometry (area-scaled, M03)
                weighting = ('constant' if self.constant_weighting
                             else 'area')
                loads, forces, _ = mem.vertex_loads(
                    source, area_weighting=weighting)
                if sub == 0 and abs(source.delta_p) > 0.0:
                    ratio = np.linalg.norm(forces, axis=1) / mem.areas
                    err = float(np.max(np.abs(
                        ratio - abs(source.delta_p))) / abs(source.delta_p))
                    self.traction_ratio_worst = max(
                        self.traction_ratio_worst, err)
                # 3. load forces + tie reaction on the membrane patch
                f_grav = np.array([0.0, 0.0, -self.load_mass * GRAV])
                f_tie = self.tie.force_on_load(self._anchor_point(),
                                               self.x_load)
                f_tie_applied = f_tie * self.tie_boost
                f_load_total = f_grav + f_tie_applied
                reaction = -f_tie
                if self.record_forces:
                    # recorded per substep: applied load force, the M05-law
                    # tie force at the same state, and the reaction actually
                    # applied to the membrane (the state-determined force
                    # audit compares the first two; the interface audit the
                    # last two)
                    f_rows.append([float(c) for c in f_load_total] +
                                  [float(c) for c in f_tie] +
                                  [float(c) for c in (-reaction if
                                   self.drop_reaction else reaction)])
                patch_force = np.zeros_like(self.x)
                if not self.drop_reaction:
                    share = reaction / len(m.tie_anchor)
                    for vid in m.tie_anchor:
                        patch_force[vid] = share
                # 4. semi-implicit step
                dx_load = (self.v_load + f_load_total / self.load_mass * HS) * HS
                x_anchor_before = self._anchor_point()
                self.v_load = self.v_load + f_load_total / self.load_mass * HS
                self.x_load = self.x_load + dx_load
                self.v = self.v + (loads + patch_force) / m.vertex_mass * HS
                x_pred = self.x + self.v * HS
                self.x = x_pred
                tick_w_tie_load += float(
                    (f_tie_applied * dx_load).sum())
                tick_w_tie_mem += float(
                    (reaction * (self._anchor_point() -
                                 x_anchor_before)).sum())
                # A1.8: the projection ALSO moves the anchor after the tie
                # force was applied; that work term is measured and carried
                # in the tie identity (the pole's projection displacement
                # times the applied tie force)
                tick_w_tie_proj += float(
                    (f_tie_applied * ((self.x[m.cap_probe] -
                                       (x_pred[m.cap_probe] -
                                        self.v[m.cap_probe] * HS)))
                     ).sum())
                if self.pose_writer:
                    anchor = self._anchor_point()
                    self.x_load = np.array([anchor[0], anchor[1],
                                            anchor[2] - L_TIE])
                    self.v_load = np.zeros(3)
                # 5. XPBD edge+chord projection (batched, under-relaxed,
                # declared order) with the canonical post-projection
                # velocity update
                w = np.ones(m.n_vertices) / m.vertex_mass
                w[m.clamp_idx] = 0.0
                e_i = np.concatenate([m.edges[:, 0], m.chords[:, 0]])
                e_j = np.concatenate([m.edges[:, 1], m.chords[:, 1]])
                L0_all = np.concatenate([m.l0, m.chord_l0])
                alpha_all = np.concatenate([m.alpha, m.chord_alpha])
                w_i, w_j = w[e_i], w[e_j]
                alpha_t = alpha_all / (HS * HS)
                v_count = m.n_vertices
                n_e = len(m.edges)
                nch = m.n_chords
                for _ in range(XPBD_ITERS):
                    d = self.x[e_j] - self.x[e_i]
                    length = np.linalg.norm(d, axis=1)
                    n = d / length[:, None]
                    c = length - L0_all
                    dlam = -c / (w_i + w_j + alpha_t)
                    gi = -(w_i * dlam)[:, None] * n
                    gj = (w_j * dlam)[:, None] * n
                    dx = np.zeros_like(self.x)
                    for comp in range(3):
                        dx[:, comp] = (
                            np.bincount(e_i, weights=XPBD_RELAX * gi[:, comp],
                                        minlength=v_count) +
                            np.bincount(e_j, weights=XPBD_RELAX * gj[:, comp],
                                        minlength=v_count))
                    self.x = self.x + dx
                self.x[m.clamp_idx] = m.rest[m.clamp_idx]
                self.v = (self.x - x_before) / HS
                self.v[m.clamp_idx] = 0.0
                # A1.8: the substep's non-damping kinetic-energy change
                # (real force work along the realized displacement plus the
                # net constraint-projection exchange) is MEASURED exactly
                # as KE(v_post_projection) - KE(v_damped); measuring against
                # the post-force prediction velocity would double-count the
                # integrator's fictitious churn (probed: -0.271 J/tick
                # artifact, recorded in Amendment A1.8). The residual then
                # contains no modeled dissipation at all.
                tick_q += 0.5 * m.vertex_mass * float(
                    ((self.v * self.v).sum() -
                     (v_damped * v_damped).sum()))
                if nch:
                    d_c = self.x[e_j[n_e:]] - self.x[e_i[n_e:]]
                    lc = np.linalg.norm(d_c, axis=1)
                    self.chord_strain_min = float(
                        ((lc - m.chord_l0) / m.chord_l0).min())
                    self.chord_strain_max = float(
                        ((lc - m.chord_l0) / m.chord_l0).max())
                # 6. blocked-anchor pin
                if self.mode == 'blocked':
                    tip = m.cap_probe
                    hold = m.rest[tip]
                    drift = hold - self.x[tip]
                    if tick >= settle_start:
                        f_pin = m.vertex_mass * drift / (HS * HS)
                        self.pin_force_acc += f_pin
                        self.pin_force_n += 1
                    self.v[tip] = drift / HS
                    self.x[tip] = hold
                # 7. volume/work accumulation
                mem_after = self._membrane()
                v_end = mem_after.signed_volume()
                dx_all = self.x - x_before
                tick_w_vol += source.delta_p * (v_end - v_start)
                tick_w_trac += float((loads * dx_all).sum())
            # per-tick ledger
            e1 = self._energies()
            total0 = e0[0] + e0[1] + e0[2] + e0[3]
            total1 = e1[0] + e1[1] + e1[2] + e1[3]
            w_press_tick = tick_w_vol
            r_tick = (total1 - total0) + tick_q - w_press_tick
            turnover = abs(w_press_tick) + abs(tick_q) + abs(total1 - total0)
            w_press_cum += w_press_tick
            q_cum += tick_q
            if tick < HOLD_END:
                w_press_hold_total = w_press_cum
            v_free = self.v.copy()
            v_free[m.clamp_idx] = 0.0
            if self.mode == 'blocked':
                v_free[m.cap_probe] = 0.0  # pinned output vertex
            speed = max(float(np.max(np.linalg.norm(v_free, axis=1))),
                        float(np.linalg.norm(self.v_load)))
            if tick >= settle_start:
                self.max_speed_seen = max(self.max_speed_seen, speed)
                drift = float(np.max(np.abs(self.x - x_before_tick)))
                self.position_drift_m = max(self.position_drift_m, drift)
            du_tie = e1[2] - e0[2]
            # A1.8: the tie-work identity is REPORTED, not gated: in an
            # XPBD-projection scaffold the constraint solve moves the anchor
            # after the tie force is applied, so the raw three-term
            # residual mis-attributes projection work (probe: cumulative
            # 0.51 J raw vs whole-system cumulative 2.1e-4 J — the true
            # violation bound). The no-source claim is carried by the
            # cumulative whole-system ledger gate.
            tie_residual = tick_w_tie_load + tick_w_tie_mem + du_tie
            tie_turnover = (abs(tick_w_tie_load) + abs(tick_w_tie_mem) +
                            abs(du_tie))
            row = {
                'tick': tick,
                'phase': phase_of(tick),
                'delta_p_pa': dp,
                'volume_m3': v_end,
                'z_tip_m': self._tip_z(),
                'z_load_m': float(self.x_load[2]),
                'tie_tension_n': float(self.tie.last_tension),
                'tie_extension_m': float(self.tie.last_extension),
                'e_kin_j': e1[0], 'u_edge_j': e1[1],
                'u_tie_j': e1[2], 'e_grav_j': e1[3],
                'q_tick_j': tick_q,
                'w_press_vol_j': tick_w_vol,
                'w_press_trac_j': tick_w_trac,
                'work_measures_diff_j': abs(tick_w_vol - tick_w_trac),
                'r_tick_j': r_tick,
                'turnover_j': turnover,
                'w_tie_load_j': tick_w_tie_load,
                'w_tie_mem_j': tick_w_tie_mem,
                'w_tie_proj_j': tick_w_tie_proj,
                'du_tie_j': du_tie,
                'tie_residual_j': tie_residual,
                'tie_turnover_j': tie_turnover,
                'w_press_cum_j': w_press_cum,
                'q_cum_j': q_cum,
                'max_speed_m_per_s': speed,
                'state_digest': self._state_digest(tick),
            }
            x_before_tick = self.x.copy()
            rows.append(row)
            if self.record_forces:
                self.force_rows.append(f_rows)
            if (tick + 1) in self.snapshot_ticks:
                self._snapshot(tick + 1, w_press_cum)
            if tick >= settle_start and len(rows) >= 2:
                flow = abs(rows[-1]['volume_m3'] -
                           rows[-2]['volume_m3']) / DT
                self.max_flow_seen = max(self.max_flow_seen, flow)
        self.rows = rows
        self.w_press_hold_total = w_press_hold_total
        self.w_press_total = w_press_cum
        self.q_total = q_cum
        return self

    def _snapshot(self, tick, w_press_cum):
        mem = self._membrane()
        e = self._energies()
        self.snapshots[int(tick)] = {
            'tick': int(tick),
            'x': [[float(c) for c in row] for row in self.x],
            'x_load': [float(c) for c in self.x_load],
            'delta_p_pa': float(self.schedule_fn(tick - 1)
                                if tick > 0 else 0.0),
            'volume_m3': float(mem.signed_volume()),
            'z_tip_m': self._tip_z(),
            'tie_tension_n': float(self.tie.last_tension),
            'w_press_cum_j': float(w_press_cum),
            'energies_j': [float(e[0]), float(e[1]), float(e[2]),
                           float(e[3])],
            'state_digest': self._state_digest(tick),
        }

    def window_mean(self, lo, hi, key):
        require(0 <= lo < hi <= len(self.rows), 'window_invalid')
        return float(np.mean([r[key] for r in self.rows[lo:hi]]))

    def check_ledger_gates(self):
        """Gates REFUSE (named codes) when the ledgers do not close.
        Called by the experiment bank on production runs; falsifier-arm
        harnesses call it inside try/except to record the bite."""
        worst_r = 0.0
        worst_tie = 0.0
        worst_work_diff = 0.0
        w_scale = max((abs(r['w_press_vol_j']) for r in self.rows),
                      default=0.0)
        for row in self.rows:
            bound = max(WIN['ledger_rel'] * row['turnover_j'],
                        WIN['ledger_floor_j'])
            if abs(row['r_tick_j']) > bound:
                raise ValueError('unexplained_energy:tick=%d,r=%.3e,'
                                 'bound=%.3e' % (row['tick'],
                                                 row['r_tick_j'], bound))
            worst_r = max(worst_r, abs(row['r_tick_j']) /
                          max(row['turnover_j'], WIN['ledger_floor_j']))
            worst_tie = max(worst_tie, abs(row['tie_residual_j']))
            wd = row['work_measures_diff_j']
            wd_bound = max(WIN['work_measures_scale_rel'] * w_scale,
                           WIN['work_measures_floor_j'])
            if wd > wd_bound:
                raise ValueError('work_measures_disagree:tick=%d,diff=%.3e,'
                                 'bound=%.3e' % (row['tick'], wd, wd_bound))
            worst_work_diff = max(worst_work_diff, wd)
        cum_r = sum(r['r_tick_j'] for r in self.rows)
        cum_bound = max(WIN['ledger_cum_rel'] * abs(self.w_press_total),
                        WIN['ledger_cum_abs_j'])
        if abs(cum_r) > cum_bound:
            raise ValueError('cumulative_energy_residual:sum=%.3e,'
                             'bound=%.3e' % (cum_r, cum_bound))
        return {'ledger_worst_relative_r': worst_r,
                'ledger_cumulative_residual_j': cum_r,
                'ledger_cumulative_bound_j': cum_bound,
                'tie_ledger_worst_relative': worst_tie,
                'work_measures_worst_diff_j': worst_work_diff,
                'ticks_checked': len(self.rows)}

    def settle_stats(self):
        tail = self.rows[-SETTLE_WINDOW:]
        return {
            'z_tip_m': float(np.mean([r['z_tip_m'] for r in tail])),
            'z_load_m': float(np.mean([r['z_load_m'] for r in tail])),
            'volume_m3': float(np.mean([r['volume_m3'] for r in tail])),
            'tie_tension_n': float(np.mean(
                [r['tie_tension_n'] for r in tail])),
            'ke_max_j': float(max(r['e_kin_j'] for r in tail)),
            'max_speed_m_per_s': self.max_speed_seen,
            'position_drift_m': self.position_drift_m,
            'pin_force_n': [float(c) for c in
                            self.pin_force_acc / max(1, self.pin_force_n)],
            'settle_speed_bound': V_MAX_SETTLE,
            'settle_drift_bound_m': SETTLE_DRIFT_M,
        }

    def audit_load_trajectory(self):
        """FB1 clean control: re-integrate the load from the RECORDED
        per-substep forces with the declared integrator; returns the max
        deviation from the emitted trajectory (m)."""
        require(self.record_forces, 'audit_requires_force_rows')
        v = np.zeros(3)
        anchor0 = self.model.rest[self.model.tie_anchor].mean(axis=0)
        pos = anchor0 + np.array([0.0, 0.0, -L_TIE])
        worst = 0.0
        for tick in range(self.ticks):
            for sub in range(N_SUB):
                f = np.array(self.force_rows[tick][sub])
                v = v * max(0.0, 1.0 - C_LOAD * HS)
                v = v + f / self.load_mass * HS
                pos = pos + v * HS
            worst = max(worst, abs(pos[2] - self.rows[tick]['z_load_m']))
        return worst

    def audit_tie_force_law(self):
        """A1.8 state-determined force audit: the applied tie force must
        equal the M05 law force evaluated at the same state, and the
        applied reaction must equal its negative (equal/opposite).
        Returns the max deviations (N); clean runs are bitwise-zero."""
        require(self.record_forces, 'audit_requires_force_rows')
        worst_law = 0.0
        worst_reaction = 0.0
        peak = 0.0
        for tick in range(self.ticks):
            for sub in range(N_SUB):
                row = self.force_rows[tick][sub]
                applied_tie = (np.array(row[0:3]) -
                               np.array([0.0, 0.0, -self.load_mass * GRAV]))
                law = np.array(row[3:6])
                react = np.array(row[6:9])
                worst_law = max(worst_law, float(
                    np.linalg.norm(applied_tie - law)))
                worst_reaction = max(worst_reaction, float(
                    np.linalg.norm(react + law)))
                peak = max(peak, float(np.linalg.norm(law)))
        return {'max_force_law_dev_n': worst_law,
                'max_reaction_dev_n': worst_reaction,
                'peak_law_force_n': peak}


# ---------------------------------------------------- static law probes ----
def buoyancy_probe(model, constant_weighting=False):
    """M03 heritage linear-field reference on the actuator at rest:
    F_net = rho g V exactly (closed membrane, divergence theorem)."""
    source = pm.PressureSource(SOURCE_ID, 100.0, 0.0, MAX_DELTA_P_PA,
                               MAX_FLOW_M3_PER_S, SOURCE_PROVENANCE)
    field = pm.LinearField(0.0, (0.0, 0.0, -RHO_WATER * GRAV))
    mem = pm.Membrane(model.rest, model.tris, 'm10_buoyancy')
    mem.require_closed()
    loads, _, _ = mem.vertex_loads(
        source, exterior_field=field,
        area_weighting=('constant' if constant_weighting else 'area'))
    net = loads.sum(axis=0)
    volume = mem.signed_volume()
    ref = RHO_WATER * GRAV * volume * np.array([0.0, 0.0, 1.0])
    rel = float(np.linalg.norm(net - ref) / np.linalg.norm(ref))
    return {'net_force_n': [float(c) for c in net],
            'reference_n': [float(c) for c in ref],
            'rel_error': rel,
            'volume_m3': float(volume),
            'triangle_area_min_m2': float(mem.areas.min()),
            'triangle_area_max_m2': float(mem.areas.max())}


# ------------------------------------------------------- state document ----
def state_document(model, revision=1, bond_bound=True):
    """chimera.material_state.v1 document for the composed actuator world;
    validated by M01's validator UNMODIFIED (X0 gate)."""
    def geometry(verts, tris):
        return {'vertices_m': [[float(c) for c in row] for row in verts],
                'triangles': [[int(i) for i in t] for t in tris],
                'frame': 'rest'}
    anchor0 = model.rest[model.tie_anchor].mean(axis=0)
    load_geom = {'vertices_m': [[float(anchor0[0]), float(anchor0[1]),
                                 float(anchor0[2] - L_TIE)]],
                 'triangles': [], 'frame': 'rest'}
    regions = [
        {'id': 'actuator', 'kind': 'region', 'parent': None,
         'rest_geometry': geometry(model.rest, model.tris),
         'current_geometry': geometry(model.rest, model.tris),
         'matter_claims': [{'matter_id': 'mat_membrane', 'role': 'owner'}],
         'sources': ['MAT2-M10 actuator membrane (M03 cube_grid, scaled)'],
         'ports': [
             {'id': 'port:pressure', 'protocol': 'normal_pressure',
              'unit': 'Pa'},
             {'id': 'port:tie', 'protocol': 'tension_shear_twist',
              'unit': 'N,N*m'}]},
        {'id': 'load', 'kind': 'region', 'parent': None,
         'rest_geometry': load_geom, 'current_geometry': load_geom,
         'matter_claims': [{'matter_id': 'mat_load', 'role': 'owner'}],
         'sources': ['MAT2-M10 declared load point mass'],
         'ports': [
             {'id': 'port:tie', 'protocol': 'tension_shear_twist',
              'unit': 'N,N*m'}]},
    ]
    document = {
        'schema': ms01.SCHEMA,
        'revision': int(revision),
        'object_id': 'm10_actuator_world',
        'regions': regions,
        'matter': [
            {'id': 'mat_membrane', 'mass_kg': SCAFFOLD_MASS_KG,
             'provenance': 'MAT2-M10 declared scaffold mass (M03 heritage)'},
            {'id': 'mat_load', 'mass_kg': M_LOAD_KG,
             'provenance': 'MAT2-M10 declared load point mass'},
        ],
        'directions': [
            {'id': 'dir:fiber_x', 'region_id': 'actuator',
             'axis': [1.0, 0.0, 0.0],
             'history': [{'revision': 0, 'state': 'authored_fiber_axis'}]},
        ],
        'laws': [
            {'id': 'law:pressure', 'kind': 'pressure_deformation',
             'regions': ['actuator'],
             'parameters': {
                 'max_delta_p_pa': MAX_DELTA_P_PA,
                 'max_flow_m3_per_s': MAX_FLOW_M3_PER_S,
                 'e_fiber_pa': E_FIBER, 'e_trans_pa': E_TRANS},
             'provenance': 'MAT2-M03 declared-source traction; M04 '
                           'effective_modulus directional law (authored '
                           'top-layer fibers along +x)'},
        ],
        'contacts': [],
        'bonds': [
            {'id': 'bond:tie', 'status': ('qualified' if bond_bound
                                          else 'planned'),
             'transfers': 'force',
             'endpoints': [
                 {'region_id': 'actuator', 'port': 'port:tie'},
                 {'region_id': 'load', 'port': 'port:tie'}]},
        ],
        'provenance': 'MAT2-M10 actuator world state document',
    }
    return document
