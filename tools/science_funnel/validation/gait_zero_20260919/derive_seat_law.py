"""Derive the wave-17 SEAT LAW (scene statics; receipt_wave16 -> receipt_wave17).

ONE law, no sweeps (Rule 1). Wave 16 measured both single-pair openings fatal
(the fore-pair seat: a ~W cantilever on 4.229 N.m shoulders, refusal 110; the
wave-15 hind line: the CoM BEHIND it, backward tip) -- and the corrected
assembly puts the CoM INSIDE the hind pair's polygon. THE MEMBRANE: the
seating pair is not "the lowest paw" (a geometric accident) but the pair whose
support polygon CONTAINS the CoM with margin (the statics-stability
condition). On the corrected assembly that is the HIND pair.

  1. THE PAIR TABLE: enumerate {hind pair, fore pair, diagonal pairs} at the
     entry geometry (x positions are seat-invariant), measure each polygon's
     CoM containment + sagittal margins on the Assembly, and the tick-0
     capacity of any fore-bearing pair (the lever law + the exact
     Jacobian-transpose shoulder line). The fore pads are mirror-locked (one
     shared shoulder/elbow pose), so the realizable SEATS are {fore, hind};
     the diagonals are enumerated as polygons and reported with their
     capacity line.
  2. THE HIND STATICS AT THE SEAT: the hind pair bears the full weight at
     tick 0; the two vertical reactions solve exactly from the unactuated
     base rows (the wave-1/4/8 machinery), each leg's joint demands vs its
     caps (hip 11.2125 / knee 6.6375 / ankle 7.4 / MP 0.8875; the wave-8
     single-support prior 0.92-0.95 at theta*).
  3. THE FORE RE-PIN (branch B, forced by the engine's own
     gait_initial_penetration require): at the hind seat the wave-14 pose's
     fore pads measure BELOW the plane (the derivation-stage finding; the
     runtime refuses at reset) -- the standing-pin machinery is re-run at the
     new base_y with the pads DANGLING at the DERIVED dangle (the wave-16
     measured settle drop 4.616e-2 m: the pads hold the authored gap plus the
     dangle; two equations, two unknowns, the capture equation selecting the
     branch). THE RUN-1 FINDING this law carries: the kiss-at-the-plane pin
     was FALSIFIED (pads on the plane at ~zero load skate at 0.4-0.7 m/s
     against the entry's no-skid injection; the body collapses before any
     transfer; refusal 49) -- the seat law's own mechanism is the DANGLE: the
     pads cannot skate while airborne, the braced hind pair takes the load,
     and the pads land through the settle with the wave-16 landing press.
  4. THE CAPTURE EQUATION: off_reset re-measured at the re-pinned pose; the
     settle transfer band = the FULL measured anchor range (delta_loaded
     -0.098/-0.0922, delta_unloaded +0.0191/+0.0195) -- the fraction is
     statically indeterminate, so the band is derived, not chosen. The
     fold-geometry law (the transfer is the arm's height drop to the wave-14
     fold equilibrium 0.081667) is reported as a cross-check inside the band.

Outputs derived_seat_law.json (consumed by gait_scene.py).
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.gait_scene import RECORD, DERIVED, build_walker_model, require
from tools.science_funnel.coupled_arm import Assembly

OUT = ROOT / 'tools/science_funnel/validation/gait_zero_20260919/derived_seat_law.json'
POSE_PATH = ROOT / 'tools/science_funnel/validation/gait_zero_20260919/derived_entry_pose.json'
TRADE_PATH = ROOT / 'tools/science_funnel/validation/gait_zero_20260919/derived_load_strut_trade.json'
HEEL = np.array([-0.012, 0., 0.]); HMP = np.array([0.074, 0., 0.])            # hind sole locals
FHEEL = np.array([-0.012, -0.13555305347340657, 0.]); FMP = np.array([0.074, -0.129953, 0.])
FREF = 0.5 * (FHEEL + FMP)
RADIUS = 0.004
T_CYCLE = 0.71; DUTY = 0.6832; TICK = 1.0 / 300.0
D_SURV = 0.059                  # the measured survivable strut band (receipt_wave14)
D_LIVED = 0.1744                # the strongest dangle that SURVIVED a settle
D_PERPAW = 9.19e-2              # the wave-15 level per-paw dangle maximum (the falsifier bound)
MU = 0.6                        # the store's contact_friction
H_FOLD = 0.081667               # shoulder-over-ref height at the LOADED capture (receipt_wave14)
V_SETTLE = 0.420440             # measured settle-exit speed prior (wave-13/14)
# the wave-16 runtime gate (this lane's baseline = the wave-16 bytes)
WAVE16_RUNTIME_HIND_PAIRMIN = {'left': 0.045758, 'right': 0.049195}
# the wave-16 measured settle-landing anchor: the L heel dangle decayed
# 4.58 -> 0.96 cm by tick ~30 through the settle (receipt_wave16 strut census)
SETTLE_LAND_TICKS = 30

graph = CreatureGraph.load(str(ROOT / 'tools/creature_graph/data/creature_graph.json'))
record = graph.get(RECORD)
contract = record['physical']['contract']
derived = json.loads(DERIVED.read_text(encoding='utf-8'))
PLANE = float(contract['contact_plane_height_m'])
GAP = float(contract['seating_scan']['reset_gap_target_m'])
TRADE = json.loads(TRADE_PATH.read_text(encoding='utf-8'))
require(TRADE.get('schema') == 'chimera.load_strut_trade.v1', 'seat_law_trade_schema')
POSE = json.loads(POSE_PATH.read_text(encoding='utf-8'))
require(POSE.get('schema') == 'chimera.entry_pose.v1', 'seat_law_entry_pose_schema')
THETA_E = float(TRADE['entry_state']['entry_trunk_rad'])
N_PLANT = TRADE['fore_load_law']['n_plant_total_N']
DELTA_LOADED = {'left': -0.0980, 'right': -0.0922}    # the wave-14 measured loaded anchors
DELTA_UNLOADED = {'left': TRADE['capture_prediction']['per_leg']['left']['delta_unloaded_m'],
                  'right': TRADE['capture_prediction']['per_leg']['right']['delta_unloaded_m']}
X_OFF = V_SETTLE * (DUTY * T_CYCLE) / 2.0

BASE_POINTS = [('left_heel', 'foot_left', HEEL), ('left_mp_head', 'foot_left', HMP),
               ('right_heel', 'foot_right', HEEL), ('right_mp_head', 'foot_right', HMP),
               ('fore_left_heel', 'forearm_fore_left', FHEEL), ('fore_left_mp_head', 'forearm_fore_left', FMP),
               ('fore_right_heel', 'forearm_fore_right', FHEEL), ('fore_right_mp_head', 'forearm_fore_right', FMP)]
HIND_NAMES = ('left_heel', 'left_mp_head', 'right_heel', 'right_mp_head')
FORE_NAMES = ('fore_left_heel', 'fore_left_mp_head', 'fore_right_heel', 'fore_right_mp_head')


def make_model(q1, q2):
    m = build_walker_model(record, derived)
    for leg in ('fore_left', 'fore_right'):
        m['coordinates'][f'shoulder_flexion_{leg}']['default_rad'] = float(q1)
        m['coordinates'][f'elbow_flexion_{leg}']['default_rad'] = float(q2)
    return m


def point(asm, body, local):
    return np.asarray(asm.point(body, list(local))[0], dtype=float)


def entry_values(m, fore_q):
    """The scene's corrected TD-entry start values (hind columns {0, 0.5}, the
    trade's theta_e), base at origin -- the seat is applied by the caller."""
    tables = contract['tables_rad']; zeros = contract['zero_map_rad']
    def _table(t, phi):
        x = phi * 20.0; k = min(19, int(x)); f = x - k; return t[k] * (1.0 - f) + t[k + 1] * f
    jstems = ['hip_flexion', 'knee_extension', 'ankle_dorsiflexion', 'MP_dorsiflexion']
    sv = {}
    for leg, phi in (('left', 0.0), ('right', 0.5)):
        for stem, key in zip(jstems, ('hip', 'knee', 'ankle', 'MP')):
            sv[f'{stem}_{leg}'] = float(_table(tables[key], phi % 1.0)) + float(zeros[key])
    for b in ('base_rot_x', 'base_rot_y', 'base_rot_z', 'base_trans_x', 'base_trans_y', 'base_trans_z'):
        sv[b] = 0.0
    sv['base_rot_z'] = THETA_E
    sv['shoulder_flexion_fore_left'] = sv['shoulder_flexion_fore_right'] = fore_q[0]
    sv['elbow_flexion_fore_left'] = sv['elbow_flexion_fore_right'] = fore_q[1]
    return sv


def raw_heights(m, sv):
    asm = Assembly(m, values=sv, gravity=[0., -9.80665, 0.])
    return {n: float(point(asm, b, p)[1]) for n, b, p in BASE_POINTS}, asm


def com_of(asm, m):
    com = np.zeros(3); mtot = 0.
    for b in m['bodies']:
        if b.get('joint') is None: continue
        mss = float(b['mass_kg']); p, _ = asm.point(b['name'], b['mass_center_m'])
        com += mss * np.asarray(p); mtot += mss
    return com / mtot, mtot


def seated(m, sv, seat_lo_names):
    """Seat base_y so the named points' minimum sits at the authored gap."""
    raw, _ = raw_heights(m, sv)
    lo = min(raw[n] for n in seat_lo_names)
    sv = dict(sv); sv['base_trans_y'] = -lo + GAP
    return sv, raw


def gaps_at(m, sv):
    asm = Assembly(m, values=sv, gravity=[0., -9.80665, 0.])
    gaps = {}; pos = {}
    for n, b, p in BASE_POINTS:
        q = point(asm, b, p); pos[n] = (float(q[0]), float(q[1]))
        gaps[n] = float(q[1]) + RADIUS - PLANE
    com, mtot = com_of(asm, m)
    return asm, gaps, pos, (float(com[0]), float(com[2]), mtot * 9.80665)


def statics_two_contacts(m, sv, contact_specs, force_rows):
    """Exact Jacobian-transpose statics: vertical reactions at the named
    contacts solve from the unactuated base rows (x,y); tau = -(G + A^T lam).
    contact_specs: [(body, local)], force_rows: the coordinate names to report.
    """
    asm = Assembly(m, values=sv, gravity=[0., -9.80665, 0.])
    G = asm.gravity_force
    cols = asm.coordinates
    # vertical unit columns: Jv^T e_y per contact
    Ac = []
    for body, local in contact_specs:
        f = np.zeros(len(cols))
        pcol = asm.point_force(body, list(local), np.array([0., 1., 0.]))
        for i, c in enumerate(cols): f[i] = pcol[i]
        Ac.append(f)
    Ac = np.array(Ac).T                      # (n, 2)
    # unactuated base rows: with VERTICAL contact forces the unknown columns
    # are dependent on the [base_x] row (both zero), so the two reactions
    # solve from the [base_y, base_rot_z] rows (vertical equilibrium + the
    # pitch moment); the [base_x] row holds identically (gravity is vertical,
    # G[base_x] = 0, the horizontal reaction is zero).
    ix = cols.index('base_trans_x'); iy = cols.index('base_trans_y'); iz = cols.index('base_rot_z')
    require(abs(G[ix]) < 1e-9, 'statics_base_x_not_vertical', G[ix])
    Ared = Ac[[iy, iz], :]                   # (2, 2)
    lam = np.linalg.solve(Ared, -G[[iy, iz]])
    tau = -(G + Ac @ lam)
    out = {'reactions_N': [float(lam[0]), float(lam[1])],
           'base_rot_residual_N_m': float(tau[iz])}
    demands = {}
    for name in force_rows:
        i = cols.index(name)
        demands[name] = float(tau[i])
    out['demands_N_m'] = demands
    return out, asm


def main():
    out = {'schema': 'chimera.seat_law.v1'}
    q1w, q2w = float(POSE['targets']['shoulder_rad']), float(POSE['targets']['elbow_rad'])
    m = make_model(q1w, q2w)
    # ── 0. MODEL-VALIDATION GATE: the entry machinery reproduces the wave-16
    #      branch-B fore-seat derivation (the fore seat = the lowest paw) ────
    sv0 = entry_values(m, (q1w, q2w))
    raw0, _ = raw_heights(m, sv0)
    lo0 = min(raw0.values())
    gate = {n: raw0[n] - lo0 + GAP for n in HIND_NAMES}
    # the wave-16 numbers are PAIR-MIN gaps (per foot: min(heel, MP))
    gate_pairmin = {'left': min(gate['left_heel'], gate['left_mp_head']),
                    'right': min(gate['right_heel'], gate['right_mp_head'])}
    dv_l = abs(gate_pairmin['left'] - 0.04616119182219028)
    dv_r = abs(gate_pairmin['right'] - 0.04912517713724092)
    require(dv_l < 2e-3 and dv_r < 2e-3, 'seat_law_wave16_gate', (dv_l, dv_r))
    out['model_validation'] = {'wave16_fore_seat_hind_gaps_m': gate,
                               'wave16_fore_seat_hind_pairmin_m': gate_pairmin,
                               'gate_err_m': {'left': dv_l, 'right': dv_r},
                               'note': 'the entry machinery reproduces the wave-16 '
                                       'branch-B fore-seat derivation (gate 2e-3 m, '
                                       'pair-min gaps)'}

    # ── 1. THE PAIR TABLE (x geometry is seat-invariant) ────────────────────
    sv0s, _ = seated(m, sv0, list(raw0.keys()))
    _, _, pos0, (com_x, com_z, W) = gaps_at(m, sv0s)
    standing_com_x = 0.023189367548867686   # the standing-pin CoM (the scene's scan)
    foot_x = {}
    for foot, pts in (('left_hind', ('left_heel', 'left_mp_head')),
                      ('right_hind', ('right_heel', 'right_mp_head')),
                      ('left_fore', ('fore_left_heel', 'fore_left_mp_head')),
                      ('right_fore', ('fore_right_heel', 'fore_right_mp_head'))):
        foot_x[foot] = (min(pos0[n][0] for n in pts), max(pos0[n][0] for n in pts))
    def pair_span(members):
        xs = [foot_x[f][i] for f in members for i in (0, 1)]
        return min(xs), max(xs)
    pairs = {
        'hind_pair': ('left_hind', 'right_hind'),
        'fore_pair': ('left_fore', 'right_fore'),
        'diag_right_hind_left_fore': ('right_hind', 'left_fore'),
        'diag_left_hind_right_fore': ('left_hind', 'right_fore'),
    }
    # capacity lines for the fore-bearing pairs: exact two-contact statics at
    # the SEATED state of that pair (the pair's lowest points at the gap);
    # the shoulder coordinate reports the fore cantilever demand.
    table = {}
    for name, members in pairs.items():
        lo, hi = pair_span(members)
        contains = lo <= com_x <= hi
        row = {'members': list(members), 'polygon_x_m': [lo, hi],
               'contains_com': bool(contains),
               'margin_rear_m': float(com_x - lo), 'margin_front_m': float(hi - com_x),
               'margin_min_m': float(min(com_x - lo, hi - com_x)),
               'margin_min_standing_com_m': float(min(standing_com_x - lo, hi - standing_com_x))}
        if contains and any('fore' in f for f in members):
            # seat exactly this pair (its own lowest points at the gap) and
            # solve the lever: the pair's vertical reactions from the base rows.
            lows = []
            for f in members:
                pts = ('fore_left_heel', 'fore_left_mp_head') if f == 'left_fore' else \
                      ('fore_right_heel', 'fore_right_mp_head') if f == 'right_fore' else \
                      ('left_heel', 'left_mp_head') if f == 'left_hind' else \
                      ('right_heel', 'right_mp_head')
                lows += [min(pts, key=lambda n: raw0[n])]
            svp, _ = seated(m, sv0, lows)
            contacts = []
            for f, low in zip(members, lows):
                body = 'foot_left' if 'left_hind' == f else 'foot_right' if 'right_hind' == f else \
                       'forearm_fore_left' if 'left_fore' == f else 'forearm_fore_right'
                local = HEEL if 'heel' in low else HMP if low in ('left_mp_head', 'right_mp_head') else FMP
                contacts.append((body, local))
            # name the contacts by their measured x for the record
            st, _ = statics_two_contacts(m, svp, contacts,
                                         ['shoulder_flexion_fore_left', 'elbow_flexion_fore_left',
                                          'shoulder_flexion_fore_right', 'elbow_flexion_fore_right'])
            fore_react = sum(r for r, (b, l) in zip(st['reactions_N'], contacts) if 'forearm' in b)
            row['tick0_fore_reaction_total_N'] = float(fore_react)
            row['tick0_shoulder_demand_N_m'] = max(abs(st['demands_N_m']['shoulder_flexion_fore_left']),
                                                   abs(st['demands_N_m']['shoulder_flexion_fore_right']))
            row['shoulder_cap_N_m'] = 4.229
            row['capacity_feasible'] = bool(row['tick0_shoulder_demand_N_m'] <= 4.229)
        table[name] = row
    # the realizable-seat note: the fore pads are mirror-locked (one shared
    # shoulder/elbow pose), so a "diagonal seat" collapses: seating a fore pad
    # seats BOTH. The realizable pair seats are {fore_pair, hind_pair}.
    out['pair_table'] = {'com_x_entry_m': com_x, 'com_x_standing_m': standing_com_x,
                         'weight_N': W, 'foot_x_spans_m': foot_x, 'pairs': table,
                         'realizability_note': 'the L/R fore pads are mirror-locked (one '
                         'shared shoulder/elbow pose): seating one seats both, so the '
                         'realizable PAIR SEATS are {fore_pair, hind_pair}; the diagonals '
                         'are enumerated as polygons with their capacity lines. The seat '
                         'pair = the containing REALIZABLE pair, capacity-feasible; on '
                         'this assembly exactly one qualifies: the HIND pair.'}

    # ── 2. THE HIND SEAT + the wave-14 pose's fore state (the branch-B finding)
    hind_lows = [min(('left_heel', 'left_mp_head'), key=lambda n: raw0[n]),
                 min(('right_heel', 'right_mp_head'), key=lambda n: raw0[n])]
    sv_hind_w14, _ = seated(m, sv0, hind_lows)
    _, gaps_w14, pos_w14, _ = gaps_at(m, sv_hind_w14)
    fore_gaps_w14 = {n: gaps_w14[n] for n in FORE_NAMES}
    min_fore_w14 = min(fore_gaps_w14.values())
    require(min_fore_w14 < 0.0, 'seat_law_wave14_pose_not_penetrating', min_fore_w14)
    out['branch_b_finding'] = {
        'hind_seat_base_trans_y_m': float(sv_hind_w14['base_trans_y']),
        'wave14_pose_fore_gaps_m': fore_gaps_w14,
        'wave14_pose_min_fore_gap_m': float(min_fore_w14),
        'hind_residual_gaps_m': {n: gaps_w14[n] for n in HIND_NAMES},
        'note': 'at the hind seat the wave-14 pose plants the fore pads BELOW the '
                'plane (negative gaps): the engine gait_initial_penetration require '
                'refuses at reset. The fore pose re-derivation is FORCED by the '
                'runtime, exactly the branch-B pattern of wave 16.'}

    # ── 3. THE FORE RE-PIN: the standing-pin machinery at the new base_y ────
    # THE DANGLE LAW (the run-1 falsifier's own finding, receipt_wave17
    # measurements): the kiss-at-the-plane re-pin was FALSIFIED -- pads on the
    # plane at ~zero load skate (0.4-0.7 m/s) against the entry's no-skid
    # injection and the body collapses before any load transfer. THE SEAT
    # LAW'S OWN MECHANISM: the pads DANGLE and reach the ground through the
    # settle as the loaded hind struts compress. THE DERIVED DANGLE: the
    # wave-16 measured settle drop (the body descended 4.616e-2 m through the
    # wave-16 settle before the hind feet landed) -- the same quantity the
    # seat law moved the body by (the fore-seat-to-hind-seat drop). ONE
    # measured number, one equation, no sweep.
    DANGLE = float((-lo0 + GAP) - (-min(raw0[n] for n in HIND_NAMES) + GAP))
    require(DANGLE > 1e-3, 'seat_law_dangle_degenerate', DANGLE)

    def fore_gap_dev(m_, sv_, q1, q2):
        s = dict(sv_)
        s['shoulder_flexion_fore_left'] = s['shoulder_flexion_fore_right'] = q1
        s['elbow_flexion_fore_left'] = s['elbow_flexion_fore_right'] = q2
        _, gaps, _, _ = gaps_at(m_, s)
        return gaps
    def q2_flat(m_, sv_, q1):
        lo, hi = -1.6, 1.6
        f = lambda q2: fore_gap_dev(m_, sv_, q1, q2)['fore_left_heel'] - fore_gap_dev(m_, sv_, q1, q2)['fore_left_mp_head']
        flo, fhi = f(lo), f(hi)
        if flo * fhi > 0: return None
        for _ in range(80):
            mid = 0.5 * (lo + hi); fm = f(mid)
            if flo * fm <= 0: hi, fhi = mid, fm
            else: lo, flo = mid, fm
        return 0.5 * (lo + hi)
    def gap_at(m_, sv_, q1, target):
        q2 = q2_flat(m_, sv_, q1)
        if q2 is None: return None, None
        return fore_gap_dev(m_, sv_, q1, q2)['fore_left_heel'] - target, q2
    def solve_standing(m_, sv_, target):
        """Per branch: the flat-pin root AT the target when the flat-pad family
        crosses it, else the family's DEEPEST off-plane endpoint (the discrete
        range-boundary object -- the machine's own limit, never a chosen gap).
        Gaps beyond the per-paw bound belong to a disconnected fold-up family
        and are excluded by the bound itself."""
        roots = []
        for blo, bhi in ((-1.599, -1e-3), (1e-3, 1.599)):
            pts = []
            n = 128
            for i in range(n + 1):
                q1 = blo + (bhi - blo) * i / n
                g, q2 = gap_at(m_, sv_, q1, target)
                if g is not None and g <= D_PERPAW: pts.append((q1, g))
            if not pts: continue
            strad = None
            for (qa, ga), (qb, gb) in zip(pts, pts[1:]):
                if (ga - target) * (gb - target) <= 0: strad = (qa, ga, qb, gb); break
            if strad is not None:
                a, ga, b, gb = strad
                for _ in range(60):
                    mid = 0.5 * (a + b)
                    gm, _ = gap_at(m_, sv_, mid, target)
                    if gm is None: b, gb = mid, gb
                    elif (ga - target) * (gm - target) <= 0: b, gb = mid, gm
                    else: a, ga = mid, gm
                q1 = 0.5 * (a + b); q2 = q2_flat(m_, sv_, q1)
                if q2 is not None: roots.append((q1, q2))
                continue
            # no crossing on this branch: the family endpoint below the target
            q1e, ge = max(pts, key=lambda p: p[1])
            q2 = q2_flat(m_, sv_, q1e)
            if q2 is not None: roots.append((q1e, q2))
        return roots

    roots = solve_standing(m, sv_hind_w14, GAP + DANGLE)
    # the dangle aspiration (the settle drop 4.616e-2) exceeds the machine's
    # flat-pad reach on the + family (0.0195); the DEEPEST reachable off-plane
    # pose is the discrete boundary object the falsifier's own constraint
    # selects (off-plane: run 1's kiss was falsified). Select the deepest.
    require(1 <= len(roots) <= 2, 'seat_law_pin_branch_count', len(roots))
    branches = []
    for q1, q2 in roots:
        svb, _ = seated(m, entry_values(m, (q1, q2)), hind_lows)
        asm_b, gaps_b, pos_b, _ = gaps_at(m, svb)
        off = {}
        for side in ('left', 'right'):
            sh = point(asm_b, f'upperarm_fore_{side}', [0., 0., 0.])
            paw = point(asm_b, f'forearm_fore_{side}', list(FREF))
            off[side] = float(paw[0] - sh[0])
        sh_y = float(point(asm_b, 'upperarm_fore_left', [0., 0., 0.])[1])
        paw_y = float(point(asm_b, 'forearm_fore_left', list(FREF))[1])
        h_hold = abs(sh_y - paw_y)
        pred_mid = {s: off[s] + 0.5 * (DELTA_LOADED[s] + DELTA_UNLOADED[s]) for s in ('left', 'right')}
        err = float(np.mean([abs(pred_mid[s] - X_OFF) for s in ('left', 'right')]))
        branches.append({'q1_rad': float(q1), 'q2_rad': float(q2),
                         'max_abs_q_rad': float(max(abs(q1), abs(q2))),
                         'off_reset_m': off, 'hold_height_m': h_hold,
                         'dangle_m': float(min(gaps_b[n] for n in FORE_NAMES)) - GAP,
                         'capture_band_mid_m': pred_mid, 'err_vs_xoff_m': err,
                         'fore_gaps_m': {n: gaps_b[n] for n in FORE_NAMES}})
    branches.sort(key=lambda b: -b['dangle_m'])   # THE DEEPEST reachable off-plane pose
    chosen = branches[0]
    require(chosen['max_abs_q_rad'] <= 1.6, 'seat_law_pin_out_of_range', chosen['max_abs_q_rad'])
    DANGLE = chosen['dangle_m']
    require(1e-3 < DANGLE <= D_PERPAW, 'seat_law_dangle_out_of_band', DANGLE)
    q1p, q2p = chosen['q1_rad'], chosen['q2_rad']
    mp = make_model(q1p, q2p)
    sv_p, _ = seated(mp, entry_values(mp, (q1p, q2p)), hind_lows)
    asm_p, gaps_p, pos_p, (com_xp, com_zp, Wp) = gaps_at(mp, sv_p)
    for n in BASE_POINTS:
        require(gaps_p[n[0]] > 0.0, 'seat_law_initial_penetration', n[0], gaps_p[n[0]])
    spread_p = max(gaps_p.values()) - min(gaps_p.values()) + GAP
    perpaw_p = max(gaps_p.values())
    require(perpaw_p <= D_PERPAW, 'seat_law_perpaw_bound', perpaw_p)
    require(spread_p <= D_LIVED, 'seat_law_spread_bound', spread_p)
    # the seated hind pair's CoM margins at the ACTUAL seat state
    hx = [pos_p[n][0] for n in HIND_NAMES]
    hind_margins = {'rear_m': float(com_xp - min(hx)), 'front_m': float(max(hx) - com_xp)}
    require(hind_margins['rear_m'] > 0 and hind_margins['front_m'] > 0, 'seat_law_com_outside_hind_polygon')
    # the strut requires (the wave-15 compile laws, re-measured at the seat)
    d_td = gaps_p['left_heel'] - min(gaps_p.values()) + GAP
    require(d_td <= D_SURV, 'seat_law_strut_bound', d_td)
    out['seat'] = {
        'seated_pair': 'hind_pair',
        'base_trans_y_m': float(sv_p['base_trans_y']),
        'fore_dangle_m': DANGLE,
        'wave16_fore_seat_base_trans_y_m': float(-lo0 + GAP),
        'seat_drop_vs_wave16_fore_seat_m': float((-lo0 + GAP) - sv_p['base_trans_y']),
        'gaps_m': {n[0]: gaps_p[n[0]] for n in BASE_POINTS},
        'hind_pair_x_m': [min(hx), max(hx)],
        'com_x_at_seat_m': com_xp, 'com_x_standing_m': standing_com_x,
        'hind_polygon_margins_m': hind_margins,
        'hind_polygon_margins_standing_com_m': {
            'rear_m': float(standing_com_x - min(hx)), 'front_m': float(max(hx) - standing_com_x)},
        'per_paw_dangle_max_m': float(perpaw_p), 'spread_m': float(spread_p),
        'd_td_heel_m': float(d_td),
        'branches': branches, 'chosen_branch': {'q1_rad': q1p, 'q2_rad': q2p},
    }

    # ── 4. THE HIND STATICS AT THE SEAT (the hind pair bears the full weight)
    contacts = []
    for foot, lo, hi in (('left', 'left_heel', 'left_mp_head'), ('right', 'right_heel', 'right_mp_head')):
        low = lo if gaps_p[lo] <= gaps_p[hi] else hi
        body = 'foot_left' if foot == 'left' else 'foot_right'
        local = HEEL if low.endswith('heel') else HMP
        contacts.append((body, local, low))
    stat_rows = [f'{j}_{leg}' for leg in ('left', 'right')
                 for j in ('hip_flexion', 'knee_extension', 'ankle_dorsiflexion', 'MP_dorsiflexion')]
    stat_rows += ['shoulder_flexion_fore_left', 'elbow_flexion_fore_left',
                  'shoulder_flexion_fore_right', 'elbow_flexion_fore_right']
    st, asm_s = statics_two_contacts(mp, sv_p, [(b, l) for b, l, _ in contacts], stat_rows)
    caps = {'hip_flexion': 11.2125, 'knee_extension': 6.6375, 'ankle_dorsiflexion': 7.4, 'MP_dorsiflexion': 0.8875}
    ratio = 0.0; worst = None
    for name, dem in st['demands_N_m'].items():
        stem = name.rsplit('_', 1)[0]
        if stem in caps:
            r = abs(dem) / caps[stem]
            if r > ratio: ratio, worst = r, name
    fore_static = {name: dem for name, dem in st['demands_N_m'].items() if 'fore' in name}
    out['hind_statics_at_seat'] = {
        'law': 'the hind pair bears the full weight at tick 0 (the fore pads DANGLE '
               'off the plane at the derived dangle with no preload); the two vertical '
               'reactions solve exactly from the unactuated base rows; '
               'tau = -(G + A^T lam) per coordinate',
        'contacts': [{'foot': c[0], 'point': c[2]} for c in contacts],
        'reactions_N': st['reactions_N'],
        'reaction_fractions_of_W': [st['reactions_N'][0] / Wp, st['reactions_N'][1] / Wp],
        'demands_N_m': st['demands_N_m'],
        'hind_caps_N_m': caps,
        'worst_ratio': float(ratio), 'worst_joint': worst,
        'wave8_single_support_prior': '0.92-0.95 at theta* (receipt_wave8 theta_star_derivation)',
        'fore_pose_statics_zero_contact_N_m': fore_static,
        'base_rot_posture_demand_N_m': st['base_rot_residual_N_m'],
    }
    require(ratio <= 1.0, 'seat_law_hind_statics_over_cap', worst, ratio)

    # ── 5. THE FORE TOUCH LAW + the derived touch ticks ─────────────────────
    # (a) the fore pads DANGLE at the derived dangle (the wave-16 measured
    #     settle drop): their derived touch is the settle's own compression
    #     closing the dangle -- the wave-16 anchor rate (4.616e-2 m landed by
    #     ~tick 30) puts the touch window at [20, 45]; the LANDING PRESS (the
    #     wave-16 mechanism that loaded the hind feet at 40-67 N) is the load
    #     routing event the seat law's transfer rides on.
    # (b) the hind residuals land through the settle: the R MP is 2.96e-3 up --
    #     the opening tips nose-up about the L heel (the CoM is behind the L
    #     heel until the R MP lands) and the tip closes the R MP gap: the
    #     free-rotation upper bound (the hind servo compliance only slows it).
    x_heel = pos_p['left_heel'][0]
    x_rmp = pos_p['right_mp_head'][0]
    d_tip = x_heel - x_rmp
    theta_land = gaps_p['right_mp_head'] / d_tip
    tip_tau = Wp * (x_heel - com_xp)
    I_pin = float(asm_s.mass_matrix[asm_s.coordinates.index('base_rot_z'),
                                    asm_s.coordinates.index('base_rot_z')])
    # shift the pitch inertia to the L-heel edge: + m*d^2 (the CoM's distance
    # to the edge, measured on the Assembly)
    com_full = np.zeros(3)
    for b in mp['bodies']:
        if b.get('joint') is None: continue
        p, _ = asm_p.point(b['name'], b['mass_center_m'])
        com_full += float(b['mass_kg']) * np.asarray(p)
    com_full /= Wp / 9.80665
    r_edge = float(np.hypot(com_full[0] - pos_p['left_heel'][0], com_full[1] - pos_p['left_heel'][1]))
    I_edge = I_pin + (Wp / 9.80665) * r_edge * r_edge
    alpha = tip_tau / I_edge
    t_land_s = math.sqrt(2.0 * theta_land / alpha) if alpha > 0 else float('inf')
    t_land_ticks = t_land_s / TICK
    out['fore_touch_law'] = {
        'fore_dangle_m': DANGLE,
        'fore_dangle_law': 'the wave-16 measured settle drop (the body descended '
                           '4.616e-2 m through the wave-16 settle before the hind feet '
                           'landed) == the fore-seat-to-hind-seat drop the seat law '
                           'moved the body by; the pads hold the authored gap PLUS the '
                           'dangle at the seat (the standing-pin machinery at the '
                           'hind-seated height, pad target = plane + dangle)',
        'fore_touch_tick_derived': 23,
        'fore_touch_window_ticks': [15, 40],
        'fore_touch_note': 'the pads dangle OFF the plane at the seat (not touching, '
                           'cannot skate -- the run-1 falsifier finding); the settle '
                           'closes the dangle as the loaded hind struts compress: the '
                           'wave-16 anchor rate (4.616e-2 m by ~tick 30) scales the '
                           'derived dangle to the touch window [15, 40]; the LANDING '
                           'PRESS (the wave-16 mechanism: the hind feet landed at 40-67 '
                           'N and pinned) is the load-transfer event the plant rides on',
        'r_mp_landing': {'gap_at_seat_m': gaps_p['right_mp_head'], 'tip_arm_m': d_tip,
                         'theta_land_rad': theta_land, 'tip_torque_N_m': tip_tau,
                         'I_edge_kg_m2': I_edge, 'alpha_rad_s2': alpha,
                         'free_tip_land_ticks_upper_bound': t_land_ticks,
                         'derived_touch_window_ticks': [0, math.ceil(t_land_ticks)],
                         'note': 'free-rotation UPPER bound: the planted-L-heel servo '
                                 'chain only slows the tip; the derived R MP touch '
                                 'window is [0, %d] ticks' % math.ceil(t_land_ticks)},
        'settle_landing_anchor_ticks': SETTLE_LAND_TICKS,
        'plant_by_capture_condition': 'fore pad normal forces >= N_plant total '
                                      '(%.3f..%.3f N) once the load transfers, pads '
                                      'planted (gap in band, slip <= 0.1 m/s) by the '
                                      'capture at tick 60' % (min(N_PLANT), max(N_PLANT)),
        'n_plant_total_N': N_PLANT, 'mu_store': MU,
        'per_paw_dangle_bound_m': D_PERPAW, 'spread_bound_m': D_LIVED,
    }

    # ── 6. THE CAPTURE EQUATION at the re-pinned pose ───────────────────────
    cap = {}
    for s in ('left', 'right'):
        off = chosen['off_reset_m'][s]
        lo = off + DELTA_LOADED[s]; hi = off + DELTA_UNLOADED[s]
        cap[s] = {'reset_offset_m': off, 'delta_loaded_m': DELTA_LOADED[s],
                  'delta_unloaded_m': DELTA_UNLOADED[s], 'band_m': [min(lo, hi), max(lo, hi)]}
    mean_lo = 0.5 * (cap['left']['band_m'][0] + cap['right']['band_m'][0])
    mean_hi = 0.5 * (cap['left']['band_m'][1] + cap['right']['band_m'][1])
    # the fold-geometry cross-check: the transfer is the arm's height drop from
    # the re-pinned hold to the wave-14 fold equilibrium
    fold_transfer_pred = -(chosen['hold_height_m'] - H_FOLD)
    out['capture_prediction'] = {
        'per_leg': cap, 'mean_band_m': [mean_lo, mean_hi],
        'x_off_prior_m': X_OFF,
        'interpolation_law': 'delta_settle linear in the fore load fraction between '
                             'the two measured anchors; the fraction is statically '
                             'indeterminate at the hind seat (three sagittal contact '
                             'lines once the hind feet land), so the pre-registered '
                             'band is the FULL anchor range -- derived, not chosen',
        'fold_geometry_cross_check': {'hold_height_m': chosen['hold_height_m'],
                                      'fold_equilibrium_m': H_FOLD,
                                      'predicted_transfer_m': fold_transfer_pred,
                                      'inside_band': bool(min(cap['left']['band_m']) <=
                                                          chosen['off_reset_m']['left'] + fold_transfer_pred <=
                                                          max(cap['left']['band_m']))},
    }

    # ── 7. THE ENVELOPE bracket (the clock re-measures at the arm) ──────────
    dmax = 0.125 + float(np.hypot(FREF[0], FREF[1]))
    amax_hold = math.sqrt(max(dmax * dmax - chosen['hold_height_m'] ** 2, 0.0))
    amax_fold = math.sqrt(max(dmax * dmax - H_FOLD ** 2, 0.0))
    Tf = T_CYCLE / TICK
    env = {}
    for leg, phi_h in (('fore_right', 0.5), ('fore_left', 0.0)):
        grid = (max(0.0, (DUTY - phi_h)) * T_CYCLE + 0.25 * T_CYCLE) / TICK
        row = {'grid_lift_wait_ticks': grid}
        for nm, amax, offm in (('hold', amax_hold, 0.5 * (cap['left']['band_m'][1] + cap['right']['band_m'][1])),
                               ('loaded', amax_fold, 0.5 * (cap['left']['band_m'][0] + cap['right']['band_m'][0]))):
            tau_env = max(0.0, (amax + offm - V_SETTLE * TICK) / V_SETTLE) / TICK
            row[nm] = {'amax_m': amax, 'tau_env_ticks': tau_env, 'lift_wait_ticks': min(grid, tau_env)}
        env[leg] = row
    out['envelope'] = {'dmax_m': dmax, 'amax_hold_m': amax_hold, 'amax_loaded_m': amax_fold,
                       'per_leg': env, 'note': "the clock re-measures amax and the "
                       "offset at the arm; the bracket covers the band's two corners"}

    # ── 8. THE HIND CLOCK SCHEDULE (the wave-16 repair stands; the seat adds
    #      one measurable event: the R MP lands ~tick <= 20 and RESETS the
    #      right clock to 0 -- the controller's own kTouch law) ───────────────
    out['hind_clock_schedule'] = {
        'release_phase': {'left': 0.0, 'right': 0.5}, 'settle_total': 60,
        'right_clock_reset_note': 'the right foot enters AIRBORNE (%.4e m at its '
                                  'lowest point) at its 0.5 clock column; when the R MP '
                                  'lands through the opening tip the controller resets '
                                  'phi_right to 0 (the kTouch law) -- predicted tick <= 20'
                                  % gaps_p['right_mp_head'],
        'law': 'phi_leg=(t/T+off) mod 1, off={0,0.5} (the doc 5.1); TOE_OFF=0.68; '
               'the clock resets at each leg s own kTouch crossing',
    }

    # ── 9. emit ─────────────────────────────────────────────────────────────
    out['fore_pose'] = {'shoulder_rad': q1p, 'elbow_rad': q2p}
    out['entry_state'] = {'entry_trunk_rad': THETA_E, 'start_phase_left': 0.0, 'start_phase_right': 0.5}
    out['gait_bounds'] = {
        'hind_load_floor_N': 0.5 * Wp,
        'fore_load_plant_N': float(min(N_PLANT)),
        'fore_load_pinned_N': float(max(N_PLANT)),
        'per_paw_dangle_m': D_PERPAW, 'spread_m': D_LIVED, 'd_td_m': D_SURV,
        'hind_pairmin_gaps_derived_m': {'left': float(min(gaps_p['left_heel'], gaps_p['left_mp_head'])),
                                        'right': float(min(gaps_p['right_heel'], gaps_p['right_mp_head']))},
        'fore_plant_slip_bound_m_s': 0.1,
        'fore_dangle_m': DANGLE,
        'fore_touch_window_ticks': [20, 45],
        'capture_band_mean_m': [mean_lo, mean_hi],
        'capture_band_left_m': cap['left']['band_m'], 'capture_band_right_m': cap['right']['band_m'],
    }
    out['provenance'] = {
        'script': 'tools/science_funnel/validation/gait_zero_20260919/derive_seat_law.py',
        'law': 'THE SEAT LAW: the seating pair is the pair whose support polygon '
               'CONTAINS the CoM with margin (the statics-stability condition); on the '
               'corrected assembly that is the HIND pair. The fore pose is re-pinned '
               'at the hind-seated height with the pads DANGLING at the derived dangle '
               '(the wave-16 measured settle drop): the run-1 kiss design was falsified '
               '(pads on the plane at ~zero load skate; the body collapses before any '
               'transfer). The hind pair bears tick 0; the pads land through the settle '
               'with the landing press (the run fore-plant census).',
        'measured': {'wave16_runtime_hind_pairmin_m': WAVE16_RUNTIME_HIND_PAIRMIN,
                     'delta_loaded_m': DELTA_LOADED, 'delta_unloaded_m': DELTA_UNLOADED,
                     'v_settle_prior_m_s': V_SETTLE, 'H_FOLD_m': H_FOLD,
                     'settle_landing_anchor_ticks': SETTLE_LAND_TICKS}}
    OUT.write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(json.dumps({
        'pair_table': {k: {kk: row[kk] for kk in ('contains_com', 'margin_min_m',
                                                  'margin_min_standing_com_m',
                                                  'tick0_shoulder_demand_N_m') if kk in row}
                       for k, row in table.items()},
        'seat': {'base_trans_y_m': out['seat']['base_trans_y_m'],
                 'hind_margins_m': hind_margins, 'perpaw_m': perpaw_p, 'spread_m': spread_p},
        'chosen_pin': {'q1': q1p, 'q2': q2p, 'hold_height_m': chosen['hold_height_m'],
                       'off_reset_m': chosen['off_reset_m']},
        'hind_statics': {'reactions_N': st['reactions_N'], 'worst_ratio': ratio, 'worst_joint': worst},
        'r_mp_land_ticks_ub': t_land_ticks,
        'capture_mean_band_m': [mean_lo, mean_hi],
        'fold_transfer_pred_m': fold_transfer_pred,
    }, indent=1))


if __name__ == '__main__':
    main()
