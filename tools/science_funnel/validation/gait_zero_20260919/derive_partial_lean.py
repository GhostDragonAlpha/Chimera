"""Derive the wave-18 PARTIAL-LEAN TIP (receipt_wave17 -> receipt_wave18).

ONE law, no sweeps (Rule 1). Wave 17 derived and built the SEAT LAW and the
run falsified its sufficiency: with the CoM centered (level trunk) the least-
norm leaves the effective support SINGLE-POINT (the R MP airborne 3 mm, the
fore pads dangling 3.478e-2), and the single-point trunk moment -- the exact
contact-frame gravity moment W*(x_heel - x_com), which the seat law itself
already measured as its free-tip torque 11.2024 N.m -- sits 0.09% under the
posture cap 11.2125 N.m. The run's geometry drift realized ~11.9 N.m (the
trace estimate): 6% OVER cap -- the posture servo rails from tick ~10, the
pitch runs through the 2 deg bound by ~tick 25, the struts fold, refusal 41.
The cap is NOT raisable (the provenance lane closed it: the muscle pool is
2.47-10.54 N.m; 11.2125 already exceeds physiology).

THE MEMBRANE: a small forward entry lean theta_e in (-0.0449, 0) -- the
load/strut trade's own corner, NEVER measured on the corrected assembly --
relieves the single-point trunk moment (the trunk CoM advances toward the
planted L heel) while the seat law holds (the CoM stays well inside the hind
polygon) and the strut stays in band (the dangles shrink forward, grow rear,
all inside the per-paw/spread bounds).

  1. trunk_moment(theta): the posture-servo demand at the seated entry state
     as a function of the entry lean, at the three prompt-mandated points
     theta in {0, -0.0225, -0.0449} (piecewise-linear standing; the curve is
     checked for closure at the mid-point). EXACT single-support statics on
     the Assembly: one vertical reaction at the L heel (the seat's lowest
     sole point -- the engine's own CoP rule), lambda = W from the
     base_trans_y row, tau = -(G + A^T lambda); the base_rot_z row is the
     posture demand. The composition is reported per subtree (the pelvis
     trunk + the hind chains + the fore arms) and against the heel reaction
     coupling, so WHICH term the 11.9 is, is named, not asserted.
  2. THE ADMISSIBLE WINDOW: {theta : trunk_moment(theta) <= cap -
     margin_derived} intersect {theta : hind-seat dangles in band} intersect
     {theta : CoM inside the hind polygon}. margin_derived = 11.9 - 11.2125 =
     0.6875 N.m -- the wave-17 run-realized excess above the cap (the trace
     estimate the prompt carries), i.e. the relief the lean must buy back so
     the same drift lands UNDER cap. If the window is empty: that is the
     derivation-stage falsification; bank it and execute the FORK (the
     staged trunk). theta_e = the moment clause's root -- the MINIMAL lean
     that clears the bound (the machine's own constraint selects; no sweep).
  3. THE CAPTURE/PRESS PREDICTIONS at theta_e: the dangle re-measured at the
     leaned seat scales the wave-17 touch window (the settle's descent-rate
     anchor carried), the R MP landing window is re-derived (the leaned gap
     is larger, the tip torque smaller: the free-rotation upper bound from
     the LEANED start), the capture band is off_reset(theta_e) + the
     measured anchor range, and the press bound stands at N_plant with the
     wave-17 run-2 anchor 14.5 N reported alongside.

Outputs derived_partial_lean.json (consumed by gait_scene.py).
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.gait_scene import RECORD, DERIVED, build_walker_model, require
from tools.science_funnel.coupled_arm import Assembly
import derive_seat_law as sl   # the wave-17 machinery: constants + Assembly helpers

OUT = ROOT / 'tools/science_funnel/validation/gait_zero_20260919/derived_partial_lean.json'
SEAT_PATH = ROOT / 'tools/science_funnel/validation/gait_zero_20260919/derived_seat_law.json'
SEAT = json.loads(SEAT_PATH.read_text(encoding='utf-8'))
require(SEAT.get('schema') == 'chimera.seat_law.v1', 'partial_lean_seat_schema')
TRADE_PATH = ROOT / 'tools/science_funnel/validation/gait_zero_20260919/derived_load_strut_trade.json'
TRADE = json.loads(TRADE_PATH.read_text(encoding='utf-8'))
require(TRADE.get('schema') == 'chimera.load_strut_trade.v1', 'partial_lean_trade_schema')

CAP_POST = 11.2125                  # the posture cap (NOT raisable; provenance lane closed)
MARGIN_DERIVED = 11.9 - CAP_POST    # 0.6875 N.m: the wave-17 run-realized excess above cap
THETAS = [0.0, -0.0225, -0.0449]    # the prompt-mandated three points (piecewise-linear standing)
THETA_STRUT_EDGE = -0.0449          # the wave-15 fore-seat strut anchor D=0.059 (the domain edge)
THETA_LEVEL = 0.0
N_PLANT = float(min(TRADE['fore_load_law']['n_plant_total_N']))
N_PINNED = float(max(TRADE['fore_load_law']['pinned_total_N'])) if 'pinned_total_N' in TRADE['fore_load_law'] \
    else float(TRADE['fore_load_law']['pinned_marker_total_N'])
PRESS_ANCHOR_N = 14.5               # the wave-17 run-2 measured landing press (receipt_wave17)
DANGLE0 = float(SEAT['seat']['fore_dangle_m'])
TOUCH_TICK0 = int(SEAT['fore_touch_law']['fore_touch_tick_derived'])       # 23
TOUCH_WINDOW0 = SEAT['fore_touch_law']['fore_touch_window_ticks']          # [15, 40]
RATE = DANGLE0 / TOUCH_TICK0        # the settle descent-rate anchor (m/tick), carried
TOUCH_LO_F = TOUCH_WINDOW0[0] / TOUCH_TICK0
TOUCH_HI_F = TOUCH_WINDOW0[1] / TOUCH_TICK0
DELTA_LOADED = {'left': -0.0980, 'right': -0.0922}     # the wave-14 measured loaded anchors
DELTA_UNLOADED = {'left': TRADE['capture_prediction']['per_leg']['left']['delta_unloaded_m'],
                  'right': TRADE['capture_prediction']['per_leg']['right']['delta_unloaded_m']}
PERPAW_B = float(SEAT['gait_bounds']['per_paw_dangle_m'])
SPREAD_B = float(SEAT['gait_bounds']['spread_m'])
FREF = sl.FREF

graph = CreatureGraph.load(str(ROOT / 'tools/creature_graph/data/creature_graph.json'))
record = graph.get(RECORD)
Q1W = float(SEAT['fore_pose']['shoulder_rad'])
Q2W = float(SEAT['fore_pose']['elbow_rad'])
MODEL = sl.make_model(Q1W, Q2W)


def entry_values_lean(m, fore_q, theta):
    """The scene's corrected TD-entry start values with an authored entry lean
    (the wave-17 machinery, the trunk state parameterized)."""
    tables = record['physical']['contract']['tables_rad']
    zeros = record['physical']['contract']['zero_map_rad']
    def _table(t, phi):
        x = phi * 20.0; k = min(19, int(x)); f = x - k; return t[k] * (1.0 - f) + t[k + 1] * f
    jstems = ['hip_flexion', 'knee_extension', 'ankle_dorsiflexion', 'MP_dorsiflexion']
    sv = {}
    for leg, phi in (('left', 0.0), ('right', 0.5)):
        for stem, key in zip(jstems, ('hip', 'knee', 'ankle', 'MP')):
            sv[f'{stem}_{leg}'] = float(_table(tables[key], phi % 1.0)) + float(zeros[key])
    for b in ('base_rot_x', 'base_rot_y', 'base_rot_z', 'base_trans_x', 'base_trans_y', 'base_trans_z'):
        sv[b] = 0.0
    sv['base_rot_z'] = float(theta)
    sv['shoulder_flexion_fore_left'] = sv['shoulder_flexion_fore_right'] = fore_q[0]
    sv['elbow_flexion_fore_left'] = sv['elbow_flexion_fore_right'] = fore_q[1]
    return sv


def hind_lows_of(m, sv):
    raw, _ = sl.raw_heights(m, sv)
    lows = [min(('left_heel', 'left_mp_head'), key=lambda n: raw[n]),
            min(('right_heel', 'right_mp_head'), key=lambda n: raw[n])]
    return lows, raw


def measure(m, theta):
    """The full seated entry state at an authored lean: gaps, CoM, the exact
    single-support trunk moment + composition, the pair statics, the strut
    quantities."""
    sv0 = entry_values_lean(m, (Q1W, Q2W), theta)
    lows, raw0 = hind_lows_of(m, sv0)
    sv, _ = sl.seated(m, sv0, lows)
    asm, gaps, pos, (com_x, com_z, W) = sl.gaps_at(m, sv)
    for n, _, _ in sl.BASE_POINTS:
        require(gaps[n] > 0.0, 'partial_lean_penetration', theta, n, gaps[n])
    # the SEAT is the L heel at every theta in the band (the seat law's own
    # object; the lean must not re-choose the seat)
    require(min(gaps, key=lambda k: gaps[k]) == 'left_heel', 'partial_lean_seat_moved', theta)
    # ── the exact SINGLE-SUPPORT trunk moment (the L heel the only contact) ──
    ix, iy, iz = (asm.coordinates.index(c) for c in
                  ('base_trans_x', 'base_trans_y', 'base_rot_z'))
    f = np.zeros(len(asm.coordinates))
    pcol = asm.point_force('foot_left', list(sl.HEEL), np.array([0., 1., 0.]))
    for i, c in enumerate(asm.coordinates): f[i] = pcol[i]
    G = asm.gravity_force
    require(abs(G[ix]) < 1e-9, 'partial_lean_base_x_not_vertical', G[ix])
    lam = -G[iy] / f[iy]                      # = W (the vertical equilibrium)
    tau = -(G + f * lam)
    tau_posture = float(tau[iz])
    # the identity: the trunk row IS the contact-frame gravity moment
    ident_heel = W * (pos['left_heel'][0] - com_x)
    ident_com = W * (com_x - pos['left_heel'][0])
    best = min([('W*(x_heel-x_com)', ident_heel), ('W*(x_com-x_heel)', ident_com)],
               key=lambda kv: abs(kv[1] - tau_posture))
    require(abs(best[1] - tau_posture) < 1e-9, 'partial_lean_moment_identity',
            tau_posture, best)
    # the composition: gravity moment per subtree about the hip axis, + the
    # heel reaction coupling
    subtrees = {'trunk_pelvis': ('pelvis',),
                'hind_legs': ('thigh_left', 'shank_left', 'foot_left', 'toe_left',
                              'thigh_right', 'shank_right', 'foot_right', 'toe_right'),
                'fore_arms': ('upperarm_fore_left', 'forearm_fore_left',
                              'upperarm_fore_right', 'forearm_fore_right')}
    grav_rows = {}
    for grp, names in subtrees.items():
        acc = 0.0
        for b in m['bodies']:
            if b.get('joint') is None or b['name'] not in names: continue
            gv = asm.point_force(b['name'], b['mass_center_m'],
                                 np.array([0., -float(b['mass_kg']) * 9.80665, 0.]))
            acc += float(gv[iz])
        grav_rows[grp] = acc
    grav_sum = sum(grav_rows.values())
    require(abs(grav_sum - G[iz]) < 1e-9, 'partial_lean_gravity_split', grav_sum, G[iz])
    react_row = float(-f[iz] * lam)           # the heel reaction's coupling moment
    require(abs(tau_posture - (-(G[iz]) - f[iz] * lam)) < 1e-12, 'partial_lean_row_recompose')
    # ── the pair statics (the compile require's number at the leaned seat) ──
    contacts = []
    for foot, lo, hi in (('left', 'left_heel', 'left_mp_head'),
                         ('right', 'right_heel', 'right_mp_head')):
        low = lo if gaps[lo] <= gaps[hi] else hi
        body = 'foot_left' if foot == 'left' else 'foot_right'
        contacts.append((body, sl.HEEL if low.endswith('heel') else sl.HMP))
    stat_rows = [f'{j}_{leg}' for leg in ('left', 'right')
                 for j in ('hip_flexion', 'knee_extension', 'ankle_dorsiflexion', 'MP_dorsiflexion')]
    st, asm_s = sl.statics_two_contacts(m, sv, contacts, stat_rows)
    caps = {'hip_flexion': 11.2125, 'knee_extension': 6.6375,
            'ankle_dorsiflexion': 7.4, 'MP_dorsiflexion': 0.8875}
    ratio, worst = 0.0, None
    for name, dem in st['demands_N_m'].items():
        stem = name.rsplit('_', 1)[0]
        if stem in caps:
            r = abs(dem) / caps[stem]
            if r > ratio: ratio, worst = r, name
    # ── the strut + containment quantities at the leaned seat ────────────────
    hx = [pos[n][0] for n in sl.HIND_NAMES]
    margins = {'rear_m': float(com_x - min(hx)), 'front_m': float(max(hx) - com_x)}
    perpaw = max(gaps.values())
    spread = max(gaps.values()) - min(gaps.values()) + sl.GAP
    d_td = gaps['left_heel'] - min(gaps.values()) + sl.GAP
    # the fore dangle + the capture offsets at the leaned state
    fore_dangle = min(gaps[n] for n in sl.FORE_NAMES) - sl.GAP
    off = {}
    for side in ('left', 'right'):
        sh = sl.point(asm, f'upperarm_fore_{side}', [0., 0., 0.])
        paw = sl.point(asm, f'forearm_fore_{side}', list(FREF))
        off[side] = float(paw[0] - sh[0])
    sh_y = float(sl.point(asm, 'upperarm_fore_left', [0., 0., 0.])[1])
    paw_y = float(sl.point(asm, 'forearm_fore_left', list(FREF))[1])
    hold_h = abs(sh_y - paw_y)
    # the R MP free-tip landing bound FROM THE LEANED START (the tip must
    # first rotate |theta| back to level, then theta_land: the rotation is
    # servo-resisted, so this is the UPPER bound on the landing tick)
    x_heel = pos['left_heel'][0]
    d_tip = x_heel - pos['right_mp_head'][0]
    theta_land = gaps['right_mp_head'] / d_tip
    tip_tau = W * (x_heel - com_x)            # == tau_posture (the identity)
    I_pin = float(asm_s.mass_matrix[asm_s.coordinates.index('base_rot_z'),
                                    asm_s.coordinates.index('base_rot_z')])
    com_full = np.zeros(3)
    for b in m['bodies']:
        if b.get('joint') is None: continue
        p, _ = asm.point(b['name'], b['mass_center_m'])
        com_full += float(b['mass_kg']) * np.asarray(p)
    com_full /= W / 9.80665
    r_edge = float(np.hypot(com_full[0] - x_heel, com_full[1] - pos['left_heel'][1]))
    I_edge = I_pin + (W / 9.80665) * r_edge * r_edge
    rot_needed = abs(theta) + theta_land      # from the leaned start, nose-up to the R MP
    alpha = tip_tau / I_edge
    t_land_ticks = math.sqrt(2.0 * rot_needed / alpha) / sl.TICK if alpha > 0 else float('inf')
    return {'theta_rad': float(theta), 'base_trans_y_m': float(sv['base_trans_y']),
            'W_N': W, 'com_x_m': com_x, 'x_heel_m': x_heel,
            'gaps_m': {n[0]: gaps[n[0]] for n in sl.BASE_POINTS},
            'tau_single_N_m': tau_posture, 'identity': best[0],
            'gravity_rows_N_m': grav_rows, 'gravity_total_N_m': float(G[iz]),
            'reaction_coupling_N_m': react_row, 'lambda_N': float(lam),
            'pair_statics': {'reactions_N': st['reactions_N'],
                             'reaction_fractions_of_W': [st['reactions_N'][0] / W,
                                                         st['reactions_N'][1] / W],
                             'worst_ratio': float(ratio), 'worst_joint': worst,
                             'base_rot_residual_N_m': st['base_rot_residual_N_m']},
            'hind_margins_m': margins, 'per_paw_dangle_m': float(perpaw),
            'spread_m': float(spread), 'd_td_m': float(d_td),
            'fore_dangle_m': float(fore_dangle), 'off_reset_m': off,
            'hold_height_m': hold_h,
            'r_mp': {'gap_at_seat_m': gaps['right_mp_head'], 'tip_arm_m': d_tip,
                     'theta_land_rad': theta_land, 'rotation_needed_rad': rot_needed,
                     'tip_torque_N_m': tip_tau, 'I_edge_kg_m2': I_edge,
                     'alpha_rad_s2': alpha, 'land_ticks_upper_bound': t_land_ticks}}


def main():
    out = {'schema': 'chimera.partial_lean.v1'}

    # ── 0. MODEL-VALIDATION GATE: this machinery reproduces the wave-17 seat
    #      at theta = 0 (the committed artifact) before any leaned measurement
    #      is trusted ─────────────────────────────────────────────────────────
    m0 = measure(MODEL, 0.0)
    dv_y = abs(m0['base_trans_y_m'] - float(SEAT['seat']['base_trans_y_m']))
    dv_g = max(abs(m0['gaps_m'][n] - float(SEAT['seat']['gaps_m'][n])) for n in m0['gaps_m'])
    dv_c = abs(m0['com_x_m'] - float(SEAT['seat']['com_x_at_seat_m']))
    require(dv_y < 1e-9 and dv_g < 1e-9 and dv_c < 1e-9, 'partial_lean_seat_gate',
            (dv_y, dv_g, dv_c))
    out['model_validation'] = {'seat_base_y_err_m': dv_y, 'seat_gaps_err_m': dv_g,
                               'seat_com_err_m': dv_c,
                               'note': 'the wave-18 machinery reproduces the committed '
                                       'wave-17 seat (derived_seat_law.json) at theta=0 '
                                       'to 1e-9 before any leaned measurement'}

    # ── 1. THE MOMENT CURVE at the three prompt-mandated points ─────────────
    points = [m0] + [measure(MODEL, t) for t in THETAS[1:]]
    curve = [{'theta_rad': p['theta_rad'], 'tau_single_N_m': p['tau_single_N_m'],
              'demand_magnitude_N_m': abs(p['tau_single_N_m']),
              'com_x_m': p['com_x_m'], 'x_heel_m': p['x_heel_m'],
              'gravity_rows_N_m': p['gravity_rows_N_m'],
              'reaction_coupling_N_m': p['reaction_coupling_N_m']} for p in points]
    # closure: is the mid-point on the chord? (the curvature over the band is
    # O(theta^2); if the mid-point deviates beyond 5% of the band's total
    # relief the three-point standing does not close and a quarter point must
    # be added -- state it, never taste it). The DEMAND is the magnitude.
    m_lo, m_mid, m_hi = (abs(p['tau_single_N_m']) for p in points)
    chord_mid = 0.5 * (m_lo + m_hi)
    dev = abs(m_mid - chord_mid)
    relief_total = m_lo - m_hi
    require(relief_total > 0.0, 'partial_lean_no_relief', relief_total)
    closes = dev <= 0.05 * relief_total
    out['trunk_moment_curve'] = {
        'law': 'tau(theta) = -(G + A^T lambda) base_rot_z row at the seated entry '
               'state, ONE vertical reaction at the L heel (the seat; the R MP is '
               'airborne 2.97e-3..1.4e-2 and the fore pads 3.2e-2..3.5e-2) -- the '
               'exact single-support posture-servo demand (judged in magnitude: '
               '|tau|). IDENTITY (machine-checked to 1e-9): tau == W*(x_com - '
               'x_heel), the contact-frame gravity moment (the Assembly torque '
               'sign is opposite the tip direction: the hold demand at level '
               'reacts the NOSE-UP tip W*(x_heel-x_com) = +11.2024 -- the seat '
               'law\'s own free-tip torque -- through the chain). THE WAVE-17 '
               '11.9 N.m IS THIS TERM at the run\'s drifted geometry; its exact '
               'level magnitude is 11.2024 N.m = 0.9992 of cap: the razor edge '
               'the run fell off.',
        'composition_note': 'MEASURED composition at level (Assembly rows): the '
                            'heel-reaction coupling dominates (%.3f N.m); the '
                            'gravity rows are the fore arms %.3f and the hind '
                            'chains %.3f; the PELVIS ROW IS EXACTLY 0.0 -- the '
                            'trunk CoM rides the base_rot_z axis, so the '
                            '"trunk+HAT gravitational moment" is nil at this pose '
                            'and the 11.2 is the CONTACT-FRAME moment itself. The '
                            'relief is lever geometry, not a CoM-forward push: '
                            'the nose-down rotation about the high base origin '
                            'RETREATS the planted heel toward the CoM (%.3f m/rad) '
                            'and advances the CoM (%.3f m/rad) -- together '
                            'W*(x_heel-x_com) shrinks at %.2f N.m/rad of |theta|.'
                            % (m0['reaction_coupling_N_m'],
                               -m0['gravity_rows_N_m']['fore_arms'],
                               -m0['gravity_rows_N_m']['hind_legs'],
                               (points[0]['x_heel_m'] - points[2]['x_heel_m']) / 0.0449,
                               (points[2]['com_x_m'] - points[0]['com_x_m']) / 0.0449,
                               relief_total / 0.0449),
        'points': curve,
        'midpoint_closure': {'chord_dev_N_m': dev, 'relief_total_N_m': relief_total,
                             'closes_three_points': bool(closes),
                             'law': 'the mid-point sits on the 0/-0.0449 demand chord '
                                    'to <= 5% of the band relief: three points close '
                                    'the piecewise-linear standing'},
        'margin_derived_N_m': MARGIN_DERIVED,
        'margin_provenance': 'the wave-17 run-realized single-point moment 11.9 N.m '
                             '(the trace estimate, receipt_wave17) minus the cap '
                             '11.2125: the relief the lean must buy back so the same '
                             'entry drift lands UNDER cap',
        'cap_N_m': CAP_POST,
        'bound_N_m': CAP_POST - MARGIN_DERIVED,
    }
    require(closes, 'partial_lean_curve_not_closed', dev, relief_total)

    # ── 2. THE ADMISSIBLE WINDOW (all three curves on the same Assembly) ────
    # (a) the moment clause: |tau(theta)| <= cap - margin_derived. The demand
    #     magnitude decreases in |theta| (relief): the clause binds
    #     |theta| >= |theta_root|. Root on the piecewise-linear interpolant
    #     through the three demand magnitudes.
    bound = CAP_POST - MARGIN_DERIVED
    thetas = [p['theta_rad'] for p in points]
    dems = [abs(p['tau_single_N_m']) for p in points]
    theta_root = None
    for (t1, y1), (t2, y2) in zip(zip(thetas, dems), zip(thetas[1:], dems[1:])):
        # the points run 0 -> -0.0449; the demand decreasing
        if (y1 - bound) * (y2 - bound) <= 0 and y1 >= bound >= y2:
            theta_root = t1 + (bound - y1) * (t2 - t1) / (y2 - y1)
            break
    require(theta_root is not None, 'partial_lean_no_moment_root', dems, bound)
    require(THETA_STRUT_EDGE < theta_root < THETA_LEVEL, 'partial_lean_root_outside_band',
            theta_root)
    # (b) the strut clause at the hind seat: every dangle + the spread inside
    #     the wave-15 bounds at ALL THREE points (the band edge included)
    for p in points:
        require(p['per_paw_dangle_m'] <= PERPAW_B, 'partial_lean_perpaw', p['theta_rad'],
                p['per_paw_dangle_m'])
        require(p['spread_m'] <= SPREAD_B, 'partial_lean_spread', p['theta_rad'],
                p['spread_m'])
        require(p['d_td_m'] <= float(SEAT['gait_bounds']['d_td_m']), 'partial_lean_d_td',
                p['theta_rad'], p['d_td_m'])
    # (c) the seat-law containment clause: the CoM strictly inside the hind
    #     polygon at ALL THREE points, with the measured margins reported
    for p in points:
        require(p['hind_margins_m']['rear_m'] > 0.0 and p['hind_margins_m']['front_m'] > 0.0,
                'partial_lean_com_outside', p['theta_rad'], p['hind_margins_m'])
    # (d) the pair statics stay under cap at ALL THREE points (the compile
    #     require's clause re-measured on the leaned seats)
    for p in points:
        require(p['pair_statics']['worst_ratio'] <= 1.0, 'partial_lean_statics_over_cap',
                p['theta_rad'], p['pair_statics']['worst_ratio'])
    # THE WINDOW IS NON-EMPTY: [strut edge, theta_root]; theta_e = theta_root,
    # the MINIMAL lean that clears the moment bound (the machine's own
    # constraint selects it; the seat keeps its maximum margin).
    theta_e = float(theta_root)
    out['window'] = {
        'moment_clause': 'tau(theta) <= %.4f N.m' % bound,
        'theta_root_rad': float(theta_root),
        'strut_clause': 'every paw dangle <= %.4f m and spread <= %.4f m at all '
                        'three points (the hind-seat strut curves; the fore-seat '
                        'D-law and its -0.0449 edge are the wave-15 measured '
                        'anchors this domain inherits)' % (PERPAW_B, SPREAD_B),
        'containment_clause': 'the CoM strictly inside the hind polygon at all '
                              'three points (margins reported per point)',
        'admissible_interval_rad': [THETA_STRUT_EDGE, float(theta_root)],
        'empty': False,
    }

    # ── 3. THE CHOSEN STATE at theta_e, measured directly (not interpolated) ─
    me = measure(MODEL, theta_e)
    require(abs(abs(me['tau_single_N_m']) - bound) <= 0.02, 'partial_lean_root_tau_mismatch',
            me['tau_single_N_m'], bound)
    require(abs(me['theta_rad'] - theta_e) < 1e-12, 'partial_lean_theta_roundtrip')
    # the re-derived capture band at theta_e (off_reset re-measured + the
    # measured anchor range carried)
    cap_bands = {}
    for s in ('left', 'right'):
        off = me['off_reset_m'][s]
        lo, hi = off + DELTA_LOADED[s], off + DELTA_UNLOADED[s]
        cap_bands[s] = {'reset_offset_m': off, 'band_m': [min(lo, hi), max(lo, hi)]}
    mean_lo = 0.5 * (cap_bands['left']['band_m'][0] + cap_bands['right']['band_m'][0])
    mean_hi = 0.5 * (cap_bands['left']['band_m'][1] + cap_bands['right']['band_m'][1])
    # the re-derived fore touch window (the settle descent-rate anchor carried;
    # the leaned dangle scales the touch tick; the wave-17 band factors kept)
    t_star = me['fore_dangle_m'] / RATE
    touch_window = [int(math.floor(TOUCH_LO_F * t_star)), int(math.ceil(TOUCH_HI_F * t_star))]
    fold_pred = -(me['hold_height_m'] - sl.H_FOLD)
    out['entry_state'] = {
        'theta_e_rad': theta_e,
        'predicted_single_point_moment_N_m': me['tau_single_N_m'],
        'predicted_moment_ratio_of_cap': abs(me['tau_single_N_m']) / CAP_POST,
        'relief_vs_level_N_m': m_lo - abs(me['tau_single_N_m']),
        'seat_base_trans_y_m': me['base_trans_y_m'],
        'com_x_m': me['com_x_m'], 'x_heel_m': me['x_heel_m'],
        'hind_margins_m': me['hind_margins_m'],
        'gaps_m': me['gaps_m'],
        'hind_pairmin_gaps_derived_m': {
            'left': min(me['gaps_m']['left_heel'], me['gaps_m']['left_mp_head']),
            'right': min(me['gaps_m']['right_heel'], me['gaps_m']['right_mp_head'])},
        'per_paw_dangle_m': me['per_paw_dangle_m'], 'spread_m': me['spread_m'],
        'd_td_m': me['d_td_m'], 'fore_dangle_m': me['fore_dangle_m'],
        'pair_statics': me['pair_statics'],
        'r_mp_landing': {**me['r_mp'], 'touch_window_ticks':
                         [0, int(math.ceil(me['r_mp']['land_ticks_upper_bound']))],
                         'note': 'free-rotation UPPER bound from the leaned start '
                                 '(the leaned gap is larger, the tip torque smaller: '
                                 'the single-support window WIDENS vs wave-17 and the '
                                 'moment relief must -- and does -- cover it)'},
        'fore_touch_prediction': {
            'dangle_m': me['fore_dangle_m'],
            'rate_anchor_m_per_tick': RATE,
            'derived_touch_tick': int(round(t_star)),
            'touch_window_ticks': touch_window,
            'window_factors_carried': [TOUCH_LO_F, TOUCH_HI_F],
            'note': 'the settle descent-rate anchor carried from the wave-17 '
                    'derivation (dangle0/23); the leaned dangle scales the tick; '
                    'the [15,40] band factors carried'},
        'capture_prediction': {
            'per_leg': cap_bands, 'mean_band_m': [mean_lo, mean_hi],
            'interpolation_law': 'delta_settle linear in the fore load fraction '
                                 'between the measured anchors (the wave-14/17 law, '
                                 'carried); off_reset re-measured at the leaned seat',
            'fold_geometry_cross_check': {'hold_height_m': me['hold_height_m'],
                                          'fold_equilibrium_m': sl.H_FOLD,
                                          'predicted_transfer_m': fold_pred,
                                          'inside_band': bool(
                                              cap_bands['left']['band_m'][0] <=
                                              cap_bands['left']['reset_offset_m'] + fold_pred <=
                                              cap_bands['left']['band_m'][1])}},
        'press_prediction': {
            'plant_bound_N': N_PLANT, 'pinned_marker_N': N_PINNED,
            'anchor_N': PRESS_ANCHOR_N,
            'note': 'the landing press >= the plant bound by the capture; predicted '
                    'on the wave-17 run-2 anchor %.1f N (the descent rate is '
                    'dangle-independent, the press scale carried); the exact peak '
                    'is the run\'s to measure' % PRESS_ANCHOR_N},
    }

    # ── 4. THE CENSUS BOUNDS the scene + the unit consume ────────────────────
    out['gait_bounds'] = {
        'trunk_moment_cap_N_m': CAP_POST,
        'trunk_moment_census_window_ticks': [0, 60],
        'hind_load_floor_N': 0.5 * me['W_N'],
        'fore_load_plant_N': N_PLANT,
        'fore_load_pinned_N': N_PINNED,
        'per_paw_dangle_m': PERPAW_B, 'spread_m': SPREAD_B, 'd_td_m': PERPAW_B * 0 + SPREAD_B * 0 + float(SEAT['gait_bounds']['d_td_m']),
        'fore_plant_slip_bound_m_s': 0.1,
        'capture_band_left_m': cap_bands['left']['band_m'],
        'capture_band_right_m': cap_bands['right']['band_m'],
        'capture_band_mean_m': [mean_lo, mean_hi],
        'fore_touch_window_ticks': touch_window,
        'r_mp_touch_window_ticks': [0, int(math.ceil(me['r_mp']['land_ticks_upper_bound']))],
        'vault_capture_bound_deg': 2.0,
    }
    out['provenance'] = {
        'script': 'tools/science_funnel/validation/gait_zero_20260919/derive_partial_lean.py',
        'law': 'THE PARTIAL-LEAN TIP: a small forward entry lean theta_e in '
               '(-0.0449, 0) relieves the single-point trunk moment (the trunk CoM '
               'advances toward the planted L heel) while the seat law holds and '
               'the dangles stay in band; theta_e is the MINIMAL lean clearing '
               'tau(theta) = cap - margin_derived (the machine\'s own constraint '
               'selects; no sweep). The fork (the staged trunk) is NOT executed: '
               'the window is non-empty.',
        'measured': {'cap_N_m': CAP_POST, 'margin_derived_N_m': MARGIN_DERIVED,
                     'wave17_level_moment_N_m': float(SEAT['fore_touch_law']['r_mp_landing']['tip_torque_N_m']),
                     'wave17_run_realized_moment_N_m': 11.9,
                     'press_anchor_N': PRESS_ANCHOR_N,
                     'dangle0_m': DANGLE0, 'touch_tick0': TOUCH_TICK0}}
    OUT.write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(json.dumps({
        'moment_curve': [(p['theta_rad'], round(p['tau_single_N_m'], 6)) for p in points],
        'identity': m0['identity'],
        'composition_at_0': m0['gravity_rows_N_m'],
        'reaction_coupling_at_0': m0['reaction_coupling_N_m'],
        'theta_root_rad': theta_root,
        'theta_e_rad': theta_e,
        'tau_at_theta_e': me['tau_single_N_m'],
        'relief_N_m': m_lo - abs(me['tau_single_N_m']),
        'seat_y_at_theta_e': me['base_trans_y_m'],
        'com_x_at_theta_e': me['com_x_m'],
        'margins_at_theta_e': me['hind_margins_m'],
        'fore_dangle_at_theta_e': me['fore_dangle_m'],
        'touch_window_at_theta_e': touch_window,
        'r_mp_window_at_theta_e': out['entry_state']['r_mp_landing']['touch_window_ticks'],
        'capture_mean_band_m': [mean_lo, mean_hi],
        'pair_ratio_at_theta_e': me['pair_statics']['worst_ratio'],
        'press_bound_N': N_PLANT,
    }, indent=1))


if __name__ == '__main__':
    main()
