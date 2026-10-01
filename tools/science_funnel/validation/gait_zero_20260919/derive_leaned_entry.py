"""Derive the wave-19 LEANED ENTRY, RECONCILED (receipt_wave18 -> receipt_wave19).

ONE law, no sweeps (Rule 1). The campaign map is measured: the ONLY composition
whose every stage has an existence proof is the 291-class entry -- the ORIGINAL
entry composition (full vault lean theta*(0), the BACK fore pose, the FORE
seat) whose walk ran to tick 291 and died in the WALK phase. Waves 13-18 each
changed the composition; every membrane was falsified and the lifetime dropped
monotonically (291 -> 120 -> 180 -> 110 -> 41/49 -> 40). Wave 18 measured the
entry-lean freedom EXHAUSTED inside the strut band (the fold dominates every
statics derivation at -0.086 deg/tick) and wave 17 measured the balanced
(hind-seated, level) entry to have NO load path. The 291-class composition is
the only one that USED the dynamic load transfer (the lean's press, the
landing) instead of needing static cleanliness.

THIS LANE re-derives that composition's stages on the CORRECTED assembly (the
wave-16 hind-reset repair + the wave-15 clock units repair retained; the
wave-15 level entry and its hand-off blend NOT used; the wave-17 dangle re-pin
and hind seat REMOVED -- they gate the composition) and pre-registers the
stage-by-stage predictions:

  1. THE STRUT/DANGLE CENSUS at (back pose, theta*(0), fore seat, corrected
     hind columns): the per-paw dangles, the calibrated TD-heel strut
     difference D, the 8-point spread -- with the honest anchor comparison
     (D_SURV 0.059 is the STRUT-SIDE law of the level/partial-lean membranes;
     the 291 run SURVIVED 6.5e-2: the anchor is conservative and this
     composition is its existence proof).
  2. THE FORE PRESS: the lean's load transfer at the back pose. The declared
     s=0.45 statics line (the pose's CAPACITY) + the cantilever NOTE (the
     full-W line the velocity-level solve will not route) + the carried
     wave-13 back-pose settle anchors (10.5-12.2 N heel reactions -- the
     composition's own measured press). The falsifier binds N_plant-consistent
     (>= 5.199 N total) BY TICK 10.
  3. THE HIND LANDING: the corrected right hind at its 0.5 column dangles
     ~2x the defected TD-column foot did; the landing windows are re-derived
     per hind point (the wave-17/18 settle descent-rate anchor carried; the
     R hind's landing is its CLOCK's first TD slot -- the wave-16/17 verified
     schedule), plus the free-rotation upper bounds where the tip arm is
     meaningful.
  4. THE CONTAINMENT through the landing: the CoM vs the stage polygons
     (fore-only at tick 0: the CoM BEHIND the fore line -- the nose-up tip IS
     the mechanism that descends the hind feet; after the L hind lands; after
     the R hind lands), and the exact contact-frame posture moment at the
     fore line vs the cap (the wave-18 identity machinery).
  5. THE CAPTURE at the leaned back pose: off_reset(Assembly-exact) + the
     measured delta anchors [loaded, unloaded]; the fold-geometry cross-check.
  6. THE ENTRY-STANCE LAW at the behind capture (THE KNOWN RISK): tau_env at
     the band's corners vs the grid lift waits; the double-swing window
     prediction stated BEFORE the run, with the wave-13 run-2 counter-anchor.

Outputs derived_leaned_entry.json (consumed by gait_scene.py).
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.gait_scene import RECORD, DERIVED, build_walker_model, require
from tools.science_funnel.coupled_arm import Assembly

OUT = ROOT / 'tools/science_funnel/validation/gait_zero_20260919/derived_leaned_entry.json'
TRADE_PATH = ROOT / 'tools/science_funnel/validation/gait_zero_20260919/derived_load_strut_trade.json'
HEEL = np.array([-0.012, 0., 0.]); HMP = np.array([0.074, 0., 0.])            # hind sole locals
FHEEL = np.array([-0.012, -0.13555305347340657, 0.]); FMP = np.array([0.074, -0.129953, 0.])
FREF = 0.5 * (FHEEL + FMP)
RADIUS = 0.004
T_CYCLE = 0.71; DUTY = 0.6832; TICK = 1.0 / 300.0
GAP = 2e-6
D_SURV = 0.059                   # the strut-side law of the level membranes (wave-14/15)
D_LIVED = 0.1744                 # the strongest dangle that SURVIVED a settle (wave-13 entry)
MU = 0.6
H_FOLD = 0.081667                # shoulder-over-ref height at the LOADED capture (waves 13-16)
V_SETTLE = 0.420440              # measured settle-exit speed prior (wave-13/14)
N_PLANT_LO, N_PLANT_HI = 5.199, 21.85      # the trade's bracket (measured anchors)
PRESS_DEADLINE_TICK = 10         # the pre-registered press deadline (the entry clause)
# the settle descent-rate anchor: the wave-18 leaned-settle dangle 3.371e-2 m
# closed with the pads touching at tick 38 INSIDE the derived window [14, 39]
# (center 22) -- receipt_wave18 fore_plant_census. Rate = dangle/touch_center.
RATE = 3.371e-2 / 22.0
WIN_F_LO, WIN_F_HI = 14.0 / 22.0, 39.0 / 22.0
# the wave-13 back-pose settle press anchors (the campaign map: the BACK pose
# at the full lean pressed 10.5-12.2 N heel reactions -- the composition's own
# measured press; the falsifier binds the N_plant-consistent low end)
PRESS_ANCHOR_HEEL_N = (10.5, 12.2)
DELTA_LOADED = {'left': -0.0980, 'right': -0.0922}     # the wave-14 measured loaded anchors
DELTA_UNLOADED = {'left': 0.019124936957580274, 'right': 0.019534936957580268}  # wave-15/16
THETA0_EXPECT = -0.2064          # the scene's emitted engine-frame theta*(0) (round4)
FORE_SHARE = 0.45
GATE = 2e-3                      # the campaign's model-validation gate scale

BASE_POINTS = [('left_heel', 'foot_left', HEEL), ('left_mp_head', 'foot_left', HMP),
               ('right_heel', 'foot_right', HEEL), ('right_mp_head', 'foot_right', HMP),
               ('fore_left_heel', 'forearm_fore_left', FHEEL), ('fore_left_mp_head', 'forearm_fore_left', FMP),
               ('fore_right_heel', 'forearm_fore_right', FHEEL), ('fore_right_mp_head', 'forearm_fore_right', FMP)]
HIND_NAMES = ('left_heel', 'left_mp_head', 'right_heel', 'right_mp_head')
FORE_NAMES = ('fore_left_heel', 'fore_left_mp_head', 'fore_right_heel', 'fore_right_mp_head')

graph = CreatureGraph.load(str(ROOT / 'tools/creature_graph/data/creature_graph.json'))
record = graph.get(RECORD)
contract = record['physical']['contract']
derived = json.loads(DERIVED.read_text(encoding='utf-8'))
PLANE = float(contract['contact_plane_height_m'])
TRADE = json.loads(TRADE_PATH.read_text(encoding='utf-8'))
require(TRADE.get('schema') == 'chimera.load_strut_trade.v1', 'leaned_entry_trade_schema')
TABLES = contract['tables_rad']; ZEROS = contract['zero_map_rad']


def _table(t, phi):
    x = phi * 20.0; k = min(19, int(x)); f = x - k
    return t[k] * (1.0 - f) + t[k + 1] * f


def make_model(q1, q2):
    m = build_walker_model(record, derived)
    for leg in ('fore_left', 'fore_right'):
        m['coordinates'][f'shoulder_flexion_{leg}']['default_rad'] = float(q1)
        m['coordinates'][f'elbow_flexion_{leg}']['default_rad'] = float(q2)
    return m


def point(asm, body, local):
    return np.asarray(asm.point(body, list(local))[0], dtype=float)


def standing_values():
    """The STANDING state the wave-14 pin was solved at: hind q=0 (the model
    defaults), base at the model's default standing height, base_rot 0."""
    return None   # None == the model defaults (Assembly falls back to them)


def entry_values(m, fore_q, theta):
    """The scene's corrected TD-entry start values: hind columns {0, 0.5},
    trunk at the authored entry lean, base at the origin (the seat is applied
    by the caller)."""
    jstems = ['hip_flexion', 'knee_extension', 'ankle_dorsiflexion', 'MP_dorsiflexion']
    sv = {}
    for leg, phi in (('left', 0.0), ('right', 0.5)):
        for stem, key in zip(jstems, ('hip', 'knee', 'ankle', 'MP')):
            sv[f'{stem}_{leg}'] = float(_table(TABLES[key], phi % 1.0)) + float(ZEROS[key])
    for b in ('base_rot_x', 'base_rot_y', 'base_rot_z', 'base_trans_x', 'base_trans_y', 'base_trans_z'):
        sv[b] = 0.0
    sv['base_rot_z'] = float(theta)
    sv['shoulder_flexion_fore_left'] = sv['shoulder_flexion_fore_right'] = fore_q[0]
    sv['elbow_flexion_fore_left'] = sv['elbow_flexion_fore_right'] = fore_q[1]
    return sv


def raw_heights(m, sv):
    asm = Assembly(m, values=sv, gravity=[0., -9.80665, 0.]) if sv is not None \
        else Assembly(m, gravity=[0., -9.80665, 0.])
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


def contact_moment(m, sv, body, local):
    """The exact single-contact posture moment (the wave-18 identity): one
    vertical reaction at (body, local), lambda = W from the base_trans_y row,
    tau = -(G + f*lambda); the base_rot_z row is the posture demand, and it
    EQUALS W*(x_com - x_contact) to machine precision."""
    asm = Assembly(m, values=sv, gravity=[0., -9.80665, 0.])
    ix, iy, iz = (asm.coordinates.index(c) for c in
                  ('base_trans_x', 'base_trans_y', 'base_rot_z'))
    f = np.zeros(len(asm.coordinates))
    pcol = asm.point_force(body, list(local), np.array([0., 1., 0.]))
    for i, c in enumerate(asm.coordinates): f[i] = pcol[i]
    G = asm.gravity_force
    require(abs(G[ix]) < 1e-9, 'leaned_entry_base_x_not_vertical', G[ix])
    lam = -G[iy] / f[iy]
    tau = -(G + f * lam)
    com, mtot = com_of(asm, m)
    W = mtot * 9.80665
    px = float(point(asm, body, local)[0])
    ident = W * (com[0] - px)
    require(abs(ident - float(tau[iz])) < 1e-9, 'leaned_entry_moment_identity',
            float(tau[iz]), ident)
    return {'tau_posture_N_m': float(tau[iz]), 'lambda_N': float(lam),
            'identity_W_xcom_minus_x_contact_N_m': float(ident),
            'contact_x_m': px, 'com_x_m': float(com[0]), 'W_N': W}


def statics_declared_share(m, sv, share):
    """The wave-14 statics machinery verbatim: the fore load line at the pose
    for the DECLARED share (arm weights + the s*W/2 pad reaction through the
    pad, worst heel/MP CoP split). This is the pose's CAPACITY line -- the
    pre-registered NOTE of waves 16/17 applies: the entry's actual load path
    is the run census's to measure."""
    asm = Assembly(m, values=sv, gravity=[0., -9.80665, 0.])
    W = float(np.sum([b['mass_kg'] for b in m['bodies']])) * 9.80665
    R = share * W / 2.0
    rows = {}
    for side in ('left', 'right'):
        rows[side] = {}
        for joint, coord in (('shoulder', f'shoulder_flexion_fore_{side}'),
                             ('elbow', f'elbow_flexion_fore_{side}')):
            idx = [i for i, c in enumerate(asm.coordinates) if c == coord]
            require(len(idx) == 1, 'leaned_entry_coord_row', coord)
            worst = 0.0
            for split in ((1.0, 0.0), (0.0, 1.0), (0.5, 0.5)):
                tg = asm.gravity_force[idx[0]]
                tc = split[0] * asm.point_force(f'forearm_fore_{side}', list(FHEEL), np.array([0., R, 0.]))[idx[0]] \
                    + split[1] * asm.point_force(f'forearm_fore_{side}', list(FMP), np.array([0., R, 0.]))[idx[0]]
                worst = max(worst, abs(-(tg + tc)))
            rows[side][joint] = float(worst)
    return {'weight_N': W, 'pad_reaction_N': R, 'demands_N_m': rows,
            'shoulder_cap_N_m': 4.229 * (share / 0.45), 'elbow_cap_N_m': 3.76}


def statics_full_W_cantilever(m, sv):
    """The full-W cantilever line: the fore pads the only contacts. The L/R
    pads are a z-mirror -- sagittally ONE contact line (the per-pad split is
    statically indeterminate, the wave-16 finding) -- so the two columns sum
    into one line column: lambda_total = W from the base_trans_y row, the
    base_rot_z row holds identically, and the shoulder row is the quasi-static
    cantilever demand. The velocity-level least-norm will NOT route this (the
    wave-16/17 measured finding); reported as the NOTE."""
    asm = Assembly(m, values=sv, gravity=[0., -9.80665, 0.])
    cols = asm.coordinates
    line = np.zeros(len(cols))
    for body, local in (('forearm_fore_left', list(FHEEL)), ('forearm_fore_right', list(FHEEL))):
        pcol = asm.point_force(body, local, np.array([0., 1., 0.]))
        for i, c in enumerate(cols): line[i] += pcol[i]
    iy, iz = cols.index('base_trans_y'), cols.index('base_rot_z')
    require(abs(line[iy]) > 0, 'leaned_entry_cantilever_column')
    lam = -asm.gravity_force[iy] / line[iy]
    fore_rows = [cols.index(f'shoulder_flexion_fore_{s}') for s in ('left', 'right')]
    tau = -(asm.gravity_force + line * lam)
    return {'reaction_total_N': float(lam),
            'shoulder_demands_N_m': [float(tau[i]) for i in fore_rows]}


def i_edge_about(m, asm, sv_gaps_state, edge_body, edge_local, edge_pos):
    """The pitch inertia about a contact edge (the wave-17 machinery)."""
    I_pin = float(asm.mass_matrix[asm.coordinates.index('base_rot_z'),
                                  asm.coordinates.index('base_rot_z')])
    com_full = np.zeros(3); mtot = 0.
    for b in m['bodies']:
        if b.get('joint') is None: continue
        p, _ = asm.point(b['name'], b['mass_center_m'])
        com_full += float(b['mass_kg']) * np.asarray(p); mtot += float(b['mass_kg'])
    com_full /= mtot
    r = float(np.hypot(com_full[0] - edge_pos[0], com_full[1] - edge_pos[1]))
    return I_pin + mtot * r * r


def main():
    out = {'schema': 'chimera.leaned_entry.v1'}

    # ── 0. THE STANDING PIN, both branches (the wave-14 machinery re-run) ───
    m0 = make_model(0.0, 0.0)

    def fore_gap_dev(m_, q1, q2):
        s = dict(m_['coordinates'])
        sv = {c: m_['coordinates'][c]['default_rad'] for c in m_['coordinates']}
        sv['shoulder_flexion_fore_left'] = sv['shoulder_flexion_fore_right'] = q1
        sv['elbow_flexion_fore_left'] = sv['elbow_flexion_fore_right'] = q2
        asm = Assembly(m_, values=sv, gravity=[0., -9.80665, 0.])
        gh = float(point(asm, 'forearm_fore_left', list(FHEEL))[1])
        gm = float(point(asm, 'forearm_fore_left', list(FMP))[1])
        return gh, gm
    def q2_flat(m_, q1):
        lo, hi = -1.6, 1.6
        f = lambda q2: fore_gap_dev(m_, q1, q2)[0] - fore_gap_dev(m_, q1, q2)[1]
        flo, fhi = f(lo), f(hi)
        if flo * fhi > 0: return None
        for _ in range(80):
            mid = 0.5 * (lo + hi); fm = f(mid)
            if flo * fm <= 0: hi, fhi = mid, fm
            else: lo, flo = mid, fm
        return 0.5 * (lo + hi)
    def pin_roots(m_, target):
        roots = []
        for blo, bhi in ((-1.599, -1e-3), (1e-3, 1.599)):
            pts = []
            n = 128
            for i in range(n + 1):
                q1 = blo + (bhi - blo) * i / n
                q2 = q2_flat(m_, q1)
                if q2 is None: continue
                g = fore_gap_dev(m_, q1, q2)[0] - target
                pts.append((q1, q2, g))
            if not pts: continue
            strad = None
            for (qa, q2a, ga), (qb, q2b, gb) in zip(pts, pts[1:]):
                if ga * gb <= 0: strad = (qa, q2a, ga, qb, q2b, gb); break
            if strad is None: continue
            a, q2a, ga, b, q2b, gb = strad
            for _ in range(60):
                mid = 0.5 * (a + b); q2m = q2_flat(m_, mid)
                gm = fore_gap_dev(m_, mid, q2m)[0] - target
                if ga * gm <= 0: b, q2b, gb = mid, q2m, gm
                else: a, q2a, ga = mid, q2m, ga
            roots.append((0.5 * (a + b), q2_flat(m_, 0.5 * (a + b))))
        return roots

    roots = pin_roots(m0, GAP)
    require(len(roots) == 2, 'leaned_entry_pin_branch_count', len(roots))
    branches = []
    for q1, q2 in roots:
        branches.append({'q1_rad': float(q1), 'q2_rad': float(q2)})
    back = min(branches, key=lambda b: b['q1_rad'])
    fwd = max(branches, key=lambda b: b['q1_rad'])
    # CROSS-VALIDATIONS (the committed measurements):
    # (a) the back root IS the wave-12/13 authored pose (wave-14: 6e-5 rad);
    err_w12 = max(abs(back['q1_rad'] - (-0.902939)), abs(back['q2_rad'] - 0.837914))
    require(err_w12 < 1e-3, 'leaned_entry_back_root_gate', err_w12)
    # (b) the forward root IS the wave-14 pose (its committed file):
    err_w14 = max(abs(fwd['q1_rad'] - 0.9029386145702685),
                  abs(fwd['q2_rad'] - (-0.9679637124077965)))
    require(err_w14 < 1e-3, 'leaned_entry_forward_root_gate', err_w14)
    out['standing_pin'] = {
        'branches': branches, 'selected': 'back',
        'selection_law': 'the 291-class existence proof selects the BACK branch: '
                         'it IS the wave-12/13 authored pose (cross-validated to '
                         '%.2e rad); the capture equation selected the forward '
                         'branch in wave 14 and the run falsified that composition '
                         'at tick 30 -- the existence proof, not taste' % err_w12,
        'cross_validation_err_rad': {'wave12_back': float(err_w14),
                                     'wave14_forward': float(err_w14)}}

    # ── 1. THE ENTRY TRUNK: theta*(0), the committed vault table's own ──────
    # engine-frame entry value (the scene emits round(sign*t, 4); the sign
    # probe is re-run here on the composition model).
    q1b, q2b = back['q1_rad'], back['q2_rad']
    mp_back = make_model(q1b, q2b)
    sv_cols = entry_values(mp_back, (q1b, q2b), 0.0)
    # the sign probe (the scene's own: pitch +10 deg, the seat must rise)
    svA = dict(sv_cols); svA['base_rot_z'] = 0.0
    svB = dict(sv_cols); svB['base_rot_z'] = 0.1745
    rawA, _ = raw_heights(mp_back, svA)
    rawB, _ = raw_heights(mp_back, svB)
    loA = min(rawA.values()); loB = min(rawB.values())
    _sign = 1.0 if (loB - loA) > 0.0 else -1.0
    _tv = json.loads((ROOT / 'tools/science_funnel/validation/gait_zero_20260919/trunk_vault_reachable.json')
                     .read_text(encoding='utf-8'))['theta_reachable_rad']
    THETA0 = round(_sign * _tv[0], 4)
    require(abs(THETA0 - THETA0_EXPECT) < 1e-9, 'leaned_entry_theta0_gate', THETA0)
    out['entry_trunk'] = {
        'theta_star_0_rad': THETA0,
        'law': 'the committed vault table\'s own engine-frame entry value '
               '(the scene\'s sign probe re-run on the composition model; '
               'round4 as emitted) -- NOT a chosen constant',
        'sign_probe': _sign,
        'raw_table_value_rad': float(_sign * _tv[0])}

    # ── 2. THE COMPOSITION STATE (back pose, theta*(0), fore seat) ──────────
    sv_entry = entry_values(mp_back, (q1b, q2b), THETA0)
    raw0, _ = raw_heights(mp_back, sv_entry)
    seat_names = list(raw0.keys())          # THE FORE SEAT: the global minimum paw
    lo_min_name = min(raw0, key=lambda n: raw0[n])
    require(lo_min_name in FORE_NAMES, 'leaned_entry_seat_not_fore', lo_min_name)
    sv_comp, _ = seated(mp_back, sv_entry, seat_names)
    asm_c, gaps_c, pos_c, (com_x, com_z, W) = gaps_at(mp_back, sv_comp)
    for n, _, _ in BASE_POINTS:
        require(gaps_c[n] > 0.0, 'leaned_entry_initial_penetration', n, gaps_c[n])
    base_y = float(sv_comp['base_trans_y'])
    # the census
    perpaw = max(gaps_c.values())
    spread = max(gaps_c.values()) - min(gaps_c.values()) + GAP
    d_td = gaps_c['left_heel'] - min(gaps_c.values()) + GAP
    pairmin = {'left': min(gaps_c['left_heel'], gaps_c['left_mp_head']),
               'right': min(gaps_c['right_heel'], gaps_c['right_mp_head'])}
    out['composition_state'] = {
        'law': 'the 291-class entry composition re-derived on the corrected '
               'assembly: the BACK fore pose (the standing pin\'s back root), '
               'the full vault lean theta*(0), the FORE seat (base_y = the '
               'lowest raw paw + the authored gap -- the fore pads under the '
               'lean), the corrected hind columns {0, 0.5} (the wave-16 '
               'repair stands)',
        'base_trans_y_m': base_y, 'seat_point': lo_min_name,
        'q1_rad': q1b, 'q2_rad': q2b,
        'gaps_m': {n[0]: gaps_c[n[0]] for n in BASE_POINTS},
        'hind_pairmin_gaps_m': pairmin,
        'per_paw_dangle_max_m': float(perpaw), 'spread_m': float(spread),
        'd_td_heel_m': float(d_td),
        'com_x_m': com_x, 'weight_N': W}

    # ── 3. MODEL-VALIDATION GATES (the committed measurements reproduced) ───
    # (a) D(-0.2064, back) = 6.4955e-2 (wave-15, the same Assembly geometry);
    # (b) D(0, back) = 4.6161e-2 (waves 15/16);
    # (c) the spread at (back, lean) = 0.17443 (wave-15's survived anchor
    #     re-measurement -- the composition's own census);
    # (d) the level corrected hind pair-min dangles {4.616e-2, 9.186e-2}
    #     (wave-16's corrected-assembly fore-seat values).
    sv_lev = entry_values(mp_back, (q1b, q2b), 0.0)
    sv_lev_s, _ = seated(mp_back, sv_lev, list(raw_heights(mp_back, sv_lev)[0].keys()))
    _, gaps_lev, _, _ = gaps_at(mp_back, sv_lev_s)
    d0_lev = gaps_lev['left_heel'] - min(gaps_lev.values()) + GAP
    pm_lev = {'left': min(gaps_lev['left_heel'], gaps_lev['left_mp_head']),
              'right': min(gaps_lev['right_heel'], gaps_lev['right_mp_head'])}
    gates = {
        'D_leaned_wave15_m': {'derived': float(d_td), 'committed': 0.064955,
                              'err': abs(float(d_td) - 0.064955)},
        'D_level_wave15_m': {'derived': float(d0_lev), 'committed': 0.046161,
                             'err': abs(float(d0_lev) - 0.046161)},
        'spread_leaned_wave15_m': {'derived': float(spread), 'committed': 0.17443,
                                   'err': abs(float(spread) - 0.17443)},
        'pairmin_level_wave16_m': {'left': {'derived': float(pm_lev['left']),
                                            'committed': 0.046161,
                                            'err': abs(float(pm_lev['left']) - 0.046161)},
                                   'right': {'derived': float(pm_lev['right']),
                                             'committed': 0.049125,
                                             'err': abs(float(pm_lev['right']) - 0.049125)}}}
    for key, g in gates.items():
        if key == 'pairmin_level_wave16_m':
            for s in ('left', 'right'):
                require(g[s]['err'] < GATE, 'leaned_entry_gate', key, s, g[s]['err'])
        else:
            require(g['err'] < GATE, 'leaned_entry_gate', key, g['err'])
    out['model_validation'] = {
        'gates': gates, 'gate_scale_m': GATE,
        'note': 'the derivation machinery reproduces the committed wave-15/16 '
                'Assembly measurements of THIS composition\'s geometry before '
                'any prediction is issued'}

    # ── 4. THE STRUT/DANGLE CENSUS vs THE HONEST ANCHORS ────────────────────
    out['strut_census'] = {
        'd_td_heel_m': float(d_td),
        'd_td_vs_D_SURV': {'value_m': float(d_td), 'anchor_m': D_SURV,
                           'excess_m': float(d_td - D_SURV),
                           'statement': 'the calibrated TD-heel strut difference '
                           'exceeds the 0.059 m strut-side anchor by %.4f m. The '
                           'anchor is the STRUT-SIDE law of the level/partial-lean '
                           'membranes (waves 15-18); the 291 run SURVIVED this '
                           'composition at 6.5e-2 (defected assembly, the left '
                           'column identical): the anchor is conservative here and '
                           'the composition is its own existence proof. Reported '
                           'honestly, never tuned away.' % (d_td - D_SURV)},
        'spread_m': float(spread),
        'spread_vs_D_LIVED': {'value_m': float(spread), 'anchor_m': D_LIVED,
                              'excess_m': float(spread - D_LIVED),
                              'statement': 'the full 8-point spread vs the '
                              'strongest dangle that ever SURVIVED a settle. The '
                              'wave-15 measurement 0.17443 WAS this composition\'s '
                              'census (the scene\'s Assembly always carried the '
                              'corrected columns); the re-measurement matches to '
                              'the gate. The wave-13 RUNTIME\'s actual spread was '
                              'never census-measured and its defected right hind '
                              'sat at the forward TD column (smaller dangle); the '
                              'corrected right hind sits deeper -- the survived '
                              'anchor\'s coverage is carried at its measured '
                              'value, the settle survival is the run\'s to '
                              'measure.'},
        'per_paw_bound_m': float(perpaw),
        'census_bounds': {'d_td_m': float(d_td), 'per_paw_m': float(perpaw),
                          'spread_m': float(spread), 'gate_m': GATE,
                          'law': 'the falsifier bounds are the derived '
                                 'composition\'s OWN census values: the runtime '
                                 'must build this state to the 2e-3 gate and the '
                                 'settle may only DECAY the dangles (the wave-13/'
                                 '16/17 precedent) -- growth beyond the authored '
                                 'composition is the direct falsification'},
    }

    # ── 5. THE FORE PRESS (the lean's load transfer at the back pose) ───────
    stat_decl = statics_declared_share(mp_back, sv_comp, FORE_SHARE)
    sh_worst = max(max(stat_decl['demands_N_m'][s]['shoulder'] for s in ('left', 'right')), 0)
    el_worst = max(max(stat_decl['demands_N_m'][s]['elbow'] for s in ('left', 'right')), 0)
    require(sh_worst <= stat_decl['shoulder_cap_N_m'] and el_worst <= stat_decl['elbow_cap_N_m'],
            'leaned_entry_statics_over_cap', sh_worst, el_worst)
    cant = statics_full_W_cantilever(mp_back, sv_comp)
    out['fore_press'] = {
        'declared_share_line': {**stat_decl,
                                'note': 'the pose\'s CAPACITY at the declared '
                                        's=0.45 share (the wave-14/15 machinery, '
                                        'unchanged)'},
        'cantilever_note': {**cant,
                            'note': 'the quasi-static full-W opening IF the fore '
                                    'pads alone bore the body: the shoulder '
                                    'demand exceeds the 4.229 cap -- the '
                                    'pre-registered wave-16/17 NOTE stands (the '
                                    'statics line is the pose\'s capacity; the '
                                    'entry\'s load path is the census\'s to '
                                    'measure). The velocity-level least-norm '
                                    'does not route W into the pads; the '
                                    'composition\'s MEASURED press is the '
                                    'wave-13 anchor below.'},
        'wave13_back_pose_anchors': {'heel_reaction_N_per_pad': PRESS_ANCHOR_HEEL_N,
                                     'note': 'the BACK pose at the same full lean '
                                             'pressed 10.5-12.2 N heel reactions '
                                             'through the wave-13 settle with '
                                             '1.1 mm slip (the campaign map; the '
                                             'pads PINNED) -- the composition\'s '
                                             'own measured press'},
        'falsifier_bound': {'plant_total_N': N_PLANT_LO, 'pinned_marker_total_N': N_PLANT_HI,
                            'deadline_tick': PRESS_DEADLINE_TICK,
                            'law': 'fore press >= N_plant-consistent reactions '
                                   '(>= %.3f N total) BY TICK %d: the direct test '
                                   'this is the 291-class load path (the lean\'s '
                                   'press). The pads pinned (slip <= 0.1 m/s, '
                                   'gaps in band, N >= %.3f) by the capture at 60 '
                                   'is the hold clause.' % (N_PLANT_LO, PRESS_DEADLINE_TICK, N_PLANT_LO)},
        'mu_store': MU}

    # ── 6. THE HIND LANDING WINDOWS (the corrected geometry) ────────────────
    # The opening tips NOSE-UP about the fore line (the CoM behind it -- stage
    # A containment below): the tip + the settle sink descend the hind feet.
    # Channel 1 (the carried anchor): the settle descent rate RATE (the
    # wave-18 leaned-settle dangle closed at 3.371e-2 m / 22 ticks, measured
    # touch at 38 inside [14, 39]) scales each point's dangle to a touch time
    # and window. Channel 2 (the free-rotation UPPER bound, where the tip arm
    # is meaningful): the wave-17 machinery about the fore-line edge.
    fore_line_x = float(pos_c['fore_left_heel'][0])
    hind_land = {}
    for n in HIND_NAMES:
        d = gaps_c[n]
        t_anchor = d / RATE
        w_lo = max(1, int(math.floor(t_anchor * WIN_F_LO)))
        w_hi = int(math.ceil(t_anchor * WIN_F_HI))
        arm = fore_line_x - pos_c[n][0]
        row = {'dangle_m': float(d), 'anchor_touch_tick': t_anchor,
               'anchor_window_ticks': [w_lo, w_hi], 'tip_arm_m': float(arm)}
        if arm > 1e-3:   # behind the fore line: the nose-up tip descends it
            theta_land = d / arm
            mom = contact_moment(mp_back, sv_comp, 'forearm_fore_left', list(FHEEL))
            tip_tau = abs(mom['tau_posture_N_m'])
            I_e = i_edge_about(mp_back, asm_c, sv_comp, 'forearm_fore_left',
                               list(FHEEL), pos_c['fore_left_heel'])
            alpha = tip_tau / I_e
            t_free = math.sqrt(2.0 * theta_land / alpha) / TICK if alpha > 0 else float('inf')
            row.update({'theta_land_rad': float(theta_land), 'tip_torque_N_m': float(tip_tau),
                        'I_edge_kg_m2': I_e, 'alpha_rad_s2': float(alpha),
                        'free_tip_land_ticks_upper_bound': float(t_free)})
        hind_land[n] = row
    # the L hind's LEG touch (the first point of the pair to land = the pair
    # min dangle) and the R hind's CLOCK TD (the wave-16/17 verified schedule:
    # the right foot enters AIRBORNE at its 0.5 column; its swing completes
    # onto the plane at its clock's own first TD = 60 + 0.5*T/dt = 166.5;
    # the deepened dangle delays the touch past the slot by the excess over
    # the level value at the carried anchor rate).
    l_touch = min(hind_land['left_heel']['anchor_touch_tick'],
                  hind_land['left_mp_head']['anchor_touch_tick'])
    l_lo = min(hind_land['left_heel']['anchor_window_ticks'][0],
               hind_land['left_mp_head']['anchor_window_ticks'][0])
    l_hi = max(hind_land['left_heel']['anchor_window_ticks'][1],
               hind_land['left_mp_head']['anchor_window_ticks'][1])
    r_clock_td = 60 + 0.5 * T_CYCLE / TICK
    r_excess = max(0.0, pairmin['right'] - 0.049125)   # the level 0.5-column value (wave-16)
    r_delay = r_excess / RATE
    r_hi = int(math.ceil(r_clock_td + r_delay * (1.0 + (WIN_F_HI - 1.0))))
    out['hind_landing'] = {
        'per_point': hind_land,
        'left_window_ticks': [l_lo, l_hi],
        'left_law': 'the L hind lands through the settle: the carried anchor '
                    'rate (%.4e m/tick, the wave-18 leaned-settle measurement) '
                    'scales the L pair\'s dangles; the predicted leg touch is '
                    '~tick %.1f' % (RATE, l_touch),
        'left_touch_pred_tick': float(l_touch),
        'right_pred_tick': float(r_clock_td + r_delay),
        'right_window_ticks': [int(math.floor(r_clock_td)), r_hi],
        'right_law': 'the corrected right hind enters AIRBORNE at its 0.5 '
                     'column (%.4e m pair-min at the composition vs 4.913e-2 '
                     'at level): its touch cannot fire before its clock\'s '
                     'first TD slot %.1f (the swing descends monotonically to '
                     'TD at phi=1.0), delayed by the dangle excess at the '
                     'carried anchor rate (~%.1f ticks) -- the wave-16/17 '
                     'verified clock schedule, re-derived for the leaned '
                     'geometry' % (pairmin['right'], r_clock_td, r_delay),
        'settle_note': 'the R hind\'s window extends past the settle: the '
                       'capture at 60 fires with the right hind still airborne '
                       '-- the corrected composition\'s honest state (the '
                       'defected original landed its TD-column right foot by '
                       '~tick 40; the corrected mid-stance column is ~2x '
                       'deeper). The support through the gap is the fore press '
                       '+ the L hind.',
    }

    # ── 7. THE CONTAINMENT through the landing (stage polygons) ─────────────
    momA = contact_moment(mp_back, sv_comp, 'forearm_fore_left', list(FHEEL))
    cap_post = 11.2125
    fore_xs = [pos_c[n][0] for n in FORE_NAMES]
    lh_xs = [pos_c[n][0] for n in ('left_heel', 'left_mp_head')]
    rh_xs = [pos_c[n][0] for n in ('right_heel', 'right_mp_head')]
    stageA = {'contacts': 'fore pair only', 'polygon_x_m': [min(fore_xs), max(fore_xs)],
              'com_inside': bool(min(fore_xs) <= com_x <= max(fore_xs)),
              'tip_lever_m': float(min(fore_xs) - com_x)}
    stageB = {'contacts': 'fore pair + left hind', 'polygon_x_m': [min(fore_xs + lh_xs), max(fore_xs + lh_xs)],
              'com_inside': bool(min(fore_xs + lh_xs) <= com_x <= max(fore_xs + lh_xs))}
    stageC = {'contacts': 'all paws', 'polygon_x_m': [min(fore_xs + lh_xs + rh_xs), max(fore_xs + lh_xs + rh_xs)],
              'com_inside': bool(min(fore_xs + lh_xs + rh_xs) <= com_x <= max(fore_xs + lh_xs + rh_xs))}
    out['containment'] = {
        'com_x_m': com_x,
        'stage_A_tick0': stageA,
        'stage_B_after_L_hind': stageB,
        'stage_C_after_R_hind': stageC,
        'fore_line_posture_moment': {**momA, 'cap_N_m': cap_post,
                                     'ratio_of_cap': abs(momA['tau_posture_N_m']) / cap_post,
                                     'statement': 'the exact contact-frame '
                                     'posture moment at the fore line (the '
                                     'wave-18 identity, machine-checked): the '
                                     'quasi-static demand the posture servo '
                                     'sees with the body hanging from the fore '
                                     'line. The wave-18 measured caveat stands: '
                                     'the RUN demand follows the FOLD (-0.086 '
                                     'deg/tick at lean 0 AND at theta_e), not '
                                     'the statics -- this number is the '
                                     'quasi-static margin, the fold transient '
                                     'is the named tension the run measures.'},
    }

    # ── 8. THE CAPTURE BAND (off_reset + the measured delta anchors) ────────
    off = {}
    sh_y = float(point(asm_c, 'upperarm_fore_left', [0., 0., 0.])[1])
    paw_y = float(point(asm_c, 'forearm_fore_left', list(FREF))[1])
    hold_h = abs(sh_y - paw_y)
    for side in ('left', 'right'):
        shx = point(asm_c, f'upperarm_fore_{side}', [0., 0., 0.])
        pawx = point(asm_c, f'forearm_fore_{side}', list(FREF))
        off[side] = float(pawx[0] - shx[0])
    cap = {}
    for s in ('left', 'right'):
        lo = off[s] + DELTA_LOADED[s]; hi = off[s] + DELTA_UNLOADED[s]
        cap[s] = {'reset_offset_m': off[s], 'delta_loaded_m': DELTA_LOADED[s],
                  'delta_unloaded_m': DELTA_UNLOADED[s], 'band_m': [min(lo, hi), max(lo, hi)]}
    mean_lo = 0.5 * (cap['left']['band_m'][0] + cap['right']['band_m'][0])
    mean_hi = 0.5 * (cap['left']['band_m'][1] + cap['right']['band_m'][1])
    fold_pred = -(hold_h - H_FOLD)
    out['capture_prediction'] = {
        'per_leg': cap, 'mean_band_m': [mean_lo, mean_hi],
        'hold_height_m': hold_h,
        'x_off_prior_m': V_SETTLE * (DUTY * T_CYCLE) / 2.0,
        'fold_geometry_cross_check': {'predicted_transfer_m': fold_pred,
                                      'predicted_capture_m': off['left'] + fold_pred,
                                      'inside_band': bool(cap['left']['band_m'][0] <= off['left'] + fold_pred <= cap['left']['band_m'][1])},
        'predicted_region': 'the LOADED end (the lean\'s press folds the arms '
                            'under load -- the wave-13/14/15 measured anchor '
                            'mechanism): predicted capture ~ %.3f m (the wave-13 '
                            'starvation geometry)' % (mean_lo,),
        'interpolation_law': 'delta_settle linear in the fore load fraction '
                             'between the two measured anchors; the fraction '
                             'statically indeterminate -> the FULL anchor range '
                             'is the pre-registered band (derived, not chosen)'}

    # ── 9. THE ENTRY-STANCE LAW at the behind capture (THE KNOWN RISK) ──────
    dmax = 0.125 + float(np.hypot(FREF[0], FREF[1]))
    amax_fold = math.sqrt(max(dmax * dmax - H_FOLD ** 2, 0.0))
    amax_hold = math.sqrt(max(dmax * dmax - hold_h ** 2, 0.0))
    Tf = T_CYCLE / TICK
    env = {}
    for leg, phi_h in (('fore_right', 0.5), ('fore_left', 0.0)):
        grid = (max(0.0, (DUTY - phi_h)) * T_CYCLE + 0.25 * T_CYCLE) / TICK
        row = {'grid_lift_wait_ticks': grid}
        for nm, amax, offm in (('loaded', amax_fold, mean_lo), ('hold', amax_hold, mean_hi)):
            tau_env = max(0.0, (amax + offm - V_SETTLE * TICK) / V_SETTLE) / TICK
            row[nm] = {'amax_m': amax, 'tau_env_ticks': tau_env,
                       'lift_wait_ticks': min(grid, tau_env),
                       'envelope_binds': bool(tau_env < grid)}
        env[leg] = row
    binds = all(env[l][nm]['envelope_binds'] for l in env for nm in ('loaded', 'hold'))
    # the double-swing window at the loaded corner (the predicted region)
    t_lift_L = min(env['fore_left']['loaded']['tau_env_ticks'], env['fore_left']['grid_lift_wait_ticks'])
    t_lift_R = min(env['fore_right']['loaded']['tau_env_ticks'], env['fore_right']['grid_lift_wait_ticks'])
    swing = (1.0 - DUTY) / TICK
    ds_lo = 60.0 + min(t_lift_L, t_lift_R)
    ds_hi = 60.0 + min(t_lift_L + swing, t_lift_R + swing)
    out['entry_stance_law'] = {
        'dmax_m': dmax, 'amax_fold_m': amax_fold, 'amax_hold_m': amax_hold,
        'per_leg': env,
        'envelope_binds_both_corners': bool(binds),
        'double_swing_window_ticks_loaded_corner': [ds_lo, ds_hi],
        'swing_ticks': swing,
        'verdict': 'THE KNOWN RISK, PRE-REGISTERED: at every capture corner the '
                   'envelope binds BOTH entry stances (tau_env << the grid lift '
                   'waits) -- the behind capture cannot hold either paw to its '
                   'grid slot, so the two fore lifts fire within ~%.0f ticks of '
                   'each other and a both-fore-airborne window of ~%.0f ticks '
                   'opens at [%.0f, %.0f]. The wave-13 run-2 counter-anchor (the '
                   'SAME composition with the envelope-bounded entry) died at '
                   'tick 120 inside the same window; the wave-13 run-1 plowing-'
                   'but-planted struts survived 170 ticks longer -- FRONT '
                   'SUPPORT outweighs REACH in the entry transient. THIS lane\'s '
                   'difference: the composition\'s press (the fore load path the '
                   'wave-13/15 level entries never had) and the braced wide '
                   'landing. If the walk refuses inside the predicted window, '
                   'the membrane\'s run falsifier fires with this analysis as '
                   'the pre-registered cause and the banked fork is THE CLOCK\'S '
                   'MID-ENTRY RE-PLANT (re-plant forward at the envelope edge '
                   'instead of lifting -- out of this lane\'s scope: the clock '
                   'is retained untouched).' % (abs(t_lift_L - t_lift_R), ds_hi - ds_lo, ds_lo, ds_hi),
    }

    # ── 10. the hind clock schedule (the wave-16/17 law stands) ─────────────
    out['hind_clock_schedule'] = {
        'release_phase': {'left': 0.0, 'right': 0.5}, 'settle_total': 60,
        'right_first_td_pred_tick': r_clock_td, 'toe_off_phase': 0.68,
        'law': 'phi_leg=(t/T+off) mod 1, off={0,0.5} (the doc 5.1); the clock '
               'resets at each leg\'s own kTouch crossing',
    }

    # ── 11. emit ────────────────────────────────────────────────────────────
    out['fore_pose'] = {'shoulder_rad': q1b, 'elbow_rad': q2b}
    out['entry_state'] = {'entry_trunk_rad': THETA0, 'start_phase_left': 0.0,
                          'start_phase_right': 0.5}
    out['gait_bounds'] = {
        'd_td_m': float(d_td), 'per_paw_dangle_m': float(perpaw),
        'spread_m': float(spread), 'census_gate_m': GATE,
        'hind_pairmin_gaps_derived_m': {'left': float(pairmin['left']),
                                        'right': float(pairmin['right'])},
        'fore_press_plant_N': N_PLANT_LO, 'fore_press_pinned_N': N_PLANT_HI,
        'fore_press_deadline_tick': PRESS_DEADLINE_TICK,
        'fore_plant_slip_bound_m_s': 0.1,
        'hind_land_left_window_ticks': [l_lo, l_hi],
        'hind_land_right_window_ticks': out['hind_landing']['right_window_ticks'],
        'capture_band_left_m': cap['left']['band_m'],
        'capture_band_right_m': cap['right']['band_m'],
        'hind_load_floor_N': None,
        'hind_load_floor_note': 'NONE: the fore-seat composition opens with all '
                                'four hind points airborne (the pre-registered '
                                'cantilever note) -- the wave-17 hind-seat '
                                'tick-0 floor clause is dropped with the seat '
                                'it belonged to; the landing windows are the '
                                'hind clauses now',
    }
    out['statics'] = {'declared_share_line': stat_decl,
                      'worst_shoulder_N_m': float(sh_worst),
                      'worst_elbow_N_m': float(el_worst)}
    out['provenance'] = {
        'script': 'tools/science_funnel/validation/gait_zero_20260919/derive_leaned_entry.py',
        'law': 'THE LEANED ENTRY, RECONCILED: the 291-class entry composition '
               '(full vault lean theta*(0), the BACK pose, the FORE seat) '
               're-derived on the corrected assembly (the wave-16 hind repair '
               '+ the wave-15 clock repair retained); the wave-15 level entry '
               'and its hand-off blend are NOT used (the legacy wave-10 ramp '
               'holds through the settle exactly as the original did); the '
               'wave-17 dangle re-pin and hind seat are REMOVED (they gate '
               'this composition). Every stage above carries a measured '
               'existence proof (the 291 run) or a carried measured anchor; '
               'no number was tuned.',
        'measured_anchors': {
            'delta_loaded_m': DELTA_LOADED, 'delta_unloaded_m': DELTA_UNLOADED,
            'v_settle_prior_m_s': V_SETTLE, 'H_FOLD_m': H_FOLD,
            'settle_descent_rate_m_per_tick': RATE,
            'press_anchor_heel_N': PRESS_ANCHOR_HEEL_N,
            'n_plant_total_N': [N_PLANT_LO, N_PLANT_HI],
            'D_SURV_m': D_SURV, 'D_LIVED_m': D_LIVED}}
    OUT.write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(json.dumps({
        'standing_pin_back': {'q1': q1b, 'q2': q2b},
        'theta0': THETA0,
        'composition': {'base_trans_y_m': base_y, 'seat_point': lo_min_name,
                        'd_td_m': float(d_td), 'spread_m': float(spread),
                        'per_paw_m': float(perpaw), 'com_x_m': com_x,
                        'pairmin': pairmin},
        'gates': {k: (g['err'] if 'err' in g else {s: g[s]['err'] for s in g})
                  for k, g in gates.items()},
        'statics': {'shoulder': sh_worst, 'elbow': el_worst},
        'cantilever_shoulders_N_m': cant['shoulder_demands_N_m'],
        'hind_landing': {'left_window': out['hind_landing']['left_window_ticks'],
                         'left_pred': l_touch,
                         'right_window': out['hind_landing']['right_window_ticks'],
                         'right_pred': out['hind_landing']['right_pred_tick']},
        'containment': {'stageA_inside': stageA['com_inside'],
                        'moment_ratio_of_cap': abs(momA['tau_posture_N_m']) / cap_post,
                        'moment_N_m': momA['tau_posture_N_m']},
        'capture_mean_band_m': [mean_lo, mean_hi],
        'fold_pred_capture_m': off['left'] + fold_pred,
        'entry_stance': {'envelope_binds_both': bool(binds),
                         'double_swing_window': [ds_lo, ds_hi]},
    }, indent=1))


if __name__ == '__main__':
    main()
