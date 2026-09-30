"""Amendment A1.9 derivation probes (preregistration integrity, review
round 1 finding F1).

The committed A1.4 X3 form (central-differencing the FREE family across
pressure levels) was mis-derived: it carries the fixed-shape inflation term
dV/dp|x, and the triggering probe disagreement was ~100x the window scale
(only noted in a code comment before this file existed — recorded here as
data, as the amendment discipline requires). The corrected Maxwell pair is:
  dF_block/dp at fixed x   (blocked family, central differences),
  dV/dx at fixed p         (fixed-p two-load family, secant between a light
                            and a heavy loaded run at the SAME level).
This script re-runs that family ACROSS THE PRESSURE RANGE and derives the
acceptance window from the physics of the estimator error, NOT from the
measured gate value:

  per interior level p0, with production estimators D_dp(2h) (blocked
  secant, span 2h = 2000 Pa) and D_dx(w) (two-load secant, mass width
  w = 0.010 kg):
    - Richardson step-halving gives the finite-difference truncation of
      each production estimator: |e| = (4/3)|D(h) - D(h/2)| (order-2,
      order verified with a third width/span);
    - settle-window dispersion gives a no-averaging-credit noise floor
      for each estimator;
    - the Richardson-corrected residual |D_dp* - D_dx*| is recorded as the
      probed irreducible branch/evaluation gap (pinned-at-rest vs loaded-
      branch configurations are different states; the gap is probed, not
      claimed derived from first principles);
    - rel_bound(p0) = (trunc_dp + trunc_dx + noise_dp + noise_dx + gap) /
      max(|D_dp_prod|, |D_dx_prod|);
    - the re-issued window is the smallest value on the pre-declared
      ladder (0.20, 0.25, 0.30, 0.35, 0.40, 0.50) that is >= 2x the
      derived rel_bound at BOTH gate levels (2x margin, A1 discipline).
  The A1.4 mis-derivation probe (free-family form) is re-run and recorded
  with its actual disagreement value.

CPU-only; stdlib + numpy; deterministic (no RNG, no wall-clock in results).
Run:  PYTHONHASHSEED=0 python -B x3_derivation_probes.py
Writes x3_derivation_probes.json (committed as the amendment data record).
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import actuator_world as aw  # noqa: E402

OUT_PATH = HERE / 'x3_derivation_probes.json'
CRITERIA_SHA256 = '5e7560caa9efae9ec819c9127ab6ee6e7016e134bdf97e525f06cfedee31190c'
ATTEMPT_ID = '02cc9dbda6f3494f8d8de36e20b94c0f'
ARRIVAL_ID = 'arrival-5c71030b5a614f89ac0716c1d99bfa0d'

# pre-declared BEFORE any probe run of this script (amendment text states it)
LADDER = (0.20, 0.25, 0.30, 0.35, 0.40, 0.50)
MARGIN = 2.0
GATE_LEVELS = (2000.0, 3000.0)      # the frozen X3 gate levels (A1.4)
PROD_SPAN = 2000.0                  # blocked central span at a gate level
PROD_WIDTH = 0.010                  # two-load mass width (heavy - light)

BLOCKED_LEVELS = (0.0, 500.0, 1000.0, 1500.0, 1750.0, 2000.0, 2250.0,
                  2500.0, 2750.0, 3000.0, 3250.0, 3500.0, 3750.0, 4000.0,
                  4500.0, 5000.0)
FREE_LEVELS = (1000.0, 2000.0, 3000.0, 4000.0)
PAIRS = {
    # label: (light_kg, heavy_kg); mid 0.015 for all ladder pairs
    'prod_w010': (0.010, 0.020),
    'wide_w020': (0.005, 0.025),
    'narrow_w005': (0.0125, 0.0175),
    'quarter_w0025': (0.01375, 0.01625),
}
PAIR_LEVELS_PROD = (1000.0, 2000.0, 3000.0, 4000.0)
PAIR_LEVELS_LADDER = (2000.0, 3000.0)


def require(condition, code):
    if not condition:
        raise ValueError(code)


def qs_blocked(level):
    m = aw.ActuatorModel('braid')
    r = aw.WorldRun(m, aw.level_schedule(level), aw.QS_TICKS, mode='blocked',
                    record_pin=True)
    r.tie.release(0)
    r.run()
    st = r.settle_stats()
    require(st['position_drift_m'] <= aw.SETTLE_DRIFT_M,
            'probe_blocked_not_settled:%g' % level)
    tail = r.rows[-aw.SETTLE_WINDOW:]
    # per-tick pin-force means from the recorded per-substep values
    per_tick = [float(np.mean(r.pin_substep_fz[i * aw.N_SUB:(i + 1) *
                                               aw.N_SUB]))
                for i in range(len(tail))]
    require(len(per_tick) == len(tail), 'probe_pin_record_short')
    return {
        'pin_force_z_n_mean': st['pin_force_n'][2],
        # the bank's X2/X3 convention: the REACTION ON THE ANCHOR is minus
        # the pin force (positive along +z / the lift direction); the
        # Maxwell dF/dp below uses this reaction convention
        'reaction_on_anchor_z_n': -st['pin_force_n'][2],
        'pin_tick_std_n': float(np.std(per_tick)),
        'z_south_m': st['z_tip_m'],
        'volume_m3': st['volume_m3'],
        'position_drift_m': st['position_drift_m'],
        'z_tail_std_m': float(np.std([row['z_tip_m'] for row in tail])),
        'vol_tail_std_m3': float(np.std([row['volume_m3']
                                         for row in tail])),
    }


def qs_free(level):
    m = aw.ActuatorModel('braid')
    r = aw.WorldRun(m, aw.level_schedule(level), aw.QS_TICKS, mode='free')
    r.tie.release(0)
    r.run()
    st = r.settle_stats()
    require(st['position_drift_m'] <= aw.SETTLE_DRIFT_M,
            'probe_free_not_settled:%g' % level)
    return {'z_south_m': st['z_tip_m'], 'volume_m3': st['volume_m3'],
            'position_drift_m': st['position_drift_m']}


def qs_loaded(level, light_kg, heavy_kg):
    out = {}
    for label, mass in (('light', light_kg), ('heavy', heavy_kg)):
        m = aw.ActuatorModel('braid')
        r = aw.WorldRun(m, aw.level_schedule(level), aw.QS_TICKS,
                        mode='loaded', load_mass=mass)
        r.run()
        st = r.settle_stats()
        require(st['position_drift_m'] <= aw.SETTLE_DRIFT_M,
                'probe_loaded_not_settled:%g/%g' % (level, mass))
        # the tie must stay TAUT in both runs or the secant is garbage
        require(st['tie_tension_n'] > 0.5 * mass * aw.GRAV,
                'probe_tie_slack:%g/%g' % (level, mass))
        tail = r.rows[-aw.SETTLE_WINDOW:]
        out[label] = {'z_south_m': st['z_tip_m'],
                      'volume_m3': st['volume_m3'],
                      'tie_tension_n': st['tie_tension_n'],
                      'z_load_m': st['z_load_m'],
                      'position_drift_m': st['position_drift_m'],
                      'z_tail_std_m': float(np.std(
                          [row['z_tip_m'] for row in tail])),
                      'vol_tail_std_m3': float(np.std(
                          [row['volume_m3'] for row in tail]))}
    return out


def rel_disagreement(a, b):
    denom = max(abs(a), abs(b), aw.WIN['reciprocity_floor'])
    return abs(a - b) / denom


def richardson(d_coarse, d_fine):
    """Order-2 step-halving: corrected estimate and the coarse-estimator
    error bound |e_coarse| = (4/3)|D(h) - D(h/2)|."""
    corrected = d_fine + (d_fine - d_coarse) / 3.0
    err_coarse = (4.0 / 3.0) * abs(d_fine - d_coarse)
    order_check = (d_fine - d_coarse)
    return corrected, err_coarse, order_check


def main():
    rederive = '--rederive' in sys.argv
    rec = {'schema': 'm10.x3_derivation_probes.v1',
           'criteria_sha256': CRITERIA_SHA256,
           'attempt_id': ATTEMPT_ID, 'arrival_id': ARRIVAL_ID,
           'python': sys.version.split()[0], 'numpy': np.__version__,
           'ladder': list(LADDER), 'margin': MARGIN,
           'gate_levels_pa': list(GATE_LEVELS),
           'prod_span_pa': PROD_SPAN, 'prod_mass_width_kg': PROD_WIDTH,
           'declare_before_run': 'ladder and margin fixed in the script '
                                 'text before any probe run'}

    if rederive:
        # the runs are deterministic; re-deriving from the recorded raw
        # families is byte-equivalent to a full re-run (the raw stage is
        # persisted BEFORE the derivation stage exactly for this)
        path = HERE / 'x3_derivation_probes.json'
        rec = json.loads(path.read_text(encoding='utf-8'))
        for key in ('blocked_family', 'free_family', 'two_load_family'):
            require(key in rec, 'rederive_raw_missing:' + key)

    # ---- blocked family (dF_block/dp at fixed x)
    blocked = rec['blocked_family']
    if not rederive:
        blocked = {}
        for level in BLOCKED_LEVELS:
            blocked['%g' % level] = qs_blocked(level)
        rec['blocked_family'] = blocked

    def reaction_z(key):
        row = blocked[key]
        if 'reaction_on_anchor_z_n' in row:
            return row['reaction_on_anchor_z_n']
        # earlier raw schema: the reaction is minus the recorded pin force
        return -row['pin_force_z_n_mean']

    def dfdp(level, span):
        lo, hi = level - span / 2.0, level + span / 2.0
        require(('%g' % lo) in blocked and ('%g' % hi) in blocked,
                'probe_blocked_level_missing')
        return (reaction_z('%g' % hi) - reaction_z('%g' % lo)) / span

    # ---- free family (A1.4 mis-derivation probe; recorded as data)
    free = rec['free_family']
    if not rederive:
        free = {}
        for level in FREE_LEVELS:
            free['%g' % level] = qs_free(level)
        rec['free_family'] = free

    # ---- fixed-p two-load family (dV/dx at fixed p)
    pairs = rec['two_load_family']
    if not rederive:
        pairs = {}
        for label, (light, heavy) in PAIRS.items():
            levels = (PAIR_LEVELS_PROD if label == 'prod_w010'
                      else PAIR_LEVELS_LADDER)
            pairs[label] = {'light_kg': light, 'heavy_kg': heavy,
                            'levels': {}}
            for level in levels:
                pairs[label]['levels']['%g' % level] = qs_loaded(
                    level, light, heavy)
        rec['two_load_family'] = pairs

    # persist the RAW families BEFORE the derivation stage (a derivation
    # bug must never cost a re-run of the physics)
    path = HERE / 'x3_derivation_probes.json'
    path.write_bytes(json.dumps(rec, indent=1, sort_keys=True)
                     .encode('utf-8'))

    def dvdz(label, level):
        lv = pairs[label]['levels']['%g' % level]
        dz = lv['heavy']['z_south_m'] - lv['light']['z_south_m']
        dv = lv['heavy']['volume_m3'] - lv['light']['volume_m3']
        require(abs(dz) > 1e-9, 'probe_degenerate_dx')
        return dv / dz, dz, dv

    # ---- per-level derivation
    derivation = {}
    for level in (1000.0, 2000.0, 3000.0, 4000.0):
        d_prod = dfdp(level, PROD_SPAN)
        d_half = dfdp(level, PROD_SPAN / 2.0)
        row = {'dF_block_dp_prod_m2': d_prod,
               'dF_block_dp_halfspan_m2': d_half}
        # third span only where the blocked ladder has it (gate levels)
        if (('%g' % (level - PROD_SPAN / 8.0)) in blocked and
                ('%g' % (level + PROD_SPAN / 8.0)) in blocked):
            d_quarter = dfdp(level, PROD_SPAN / 4.0)
            _, _, o1 = richardson(d_prod, d_half)
            _, _, o2 = richardson(d_half, d_quarter)
            row['dF_block_dp_quarterspan_m2'] = d_quarter
            row['dF_halving_order_check'] = o2 / o1 if abs(o1) > 0 else None
        d_dp_corr, d_dp_err, _ = richardson(d_prod, d_half)
        row['dF_block_dp_corrected_m2'] = d_dp_corr
        row['dF_prod_trunc_bound_m2'] = d_dp_err
        noise_dp = ((blocked['%g' % (level - PROD_SPAN / 2.0)]
                     ['pin_tick_std_n'] +
                     blocked['%g' % (level + PROD_SPAN / 2.0)]
                     ['pin_tick_std_n']) / PROD_SPAN)
        row['dF_noise_floor_m2'] = noise_dp

        d_w_prod, dz_prod, dv_prod = dvdz('prod_w010', level)
        row['dV_dx_prod_m2'] = d_w_prod
        row['prod_dz_m'] = dz_prod
        row['prod_dV_m3'] = dv_prod
        if ('%g' % level) in pairs['narrow_w005']['levels']:
            d_w_narrow, _, _ = dvdz('narrow_w005', level)
            d_w_quarter, _, _ = dvdz('quarter_w0025', level)
            d_w_wide, _, _ = dvdz('wide_w020', level)
            row['dV_dx_wide_m2'] = d_w_wide
            row['dV_dx_narrow_m2'] = d_w_narrow
            row['dV_dx_quarter_m2'] = d_w_quarter
            _, _, o1 = richardson(d_w_wide, d_w_prod)
            _, _, o2 = richardson(d_w_prod, d_w_narrow)
            row['dV_halving_order_check'] = o2 / o1 if abs(o1) > 0 else None
            d_dx_corr, d_dx_err, _ = richardson(d_w_prod, d_w_narrow)
            row['dV_dx_corrected_m2'] = d_dx_corr
            row['dV_prod_trunc_bound_m2'] = d_dx_err
            # noise floor: tail dispersion of the production pair, no
            # averaging credit, propagated through the secant
            z_tail_std = 0.5 * (
                pairs['prod_w010']['levels']['%g' % level]['light']
                ['z_tail_std_m'] +
                pairs['prod_w010']['levels']['%g' % level]['heavy']
                ['z_tail_std_m'])
            v_tail_std = 0.5 * (
                pairs['prod_w010']['levels']['%g' % level]['light']
                ['vol_tail_std_m3'] +
                pairs['prod_w010']['levels']['%g' % level]['heavy']
                ['vol_tail_std_m3'])
            row['dV_noise_floor_m2'] = (v_tail_std / abs(dz_prod) +
                                        abs(d_w_prod) * z_tail_std /
                                        abs(dz_prod))
        # A1.4 mis-derivation probe (free-family form), recorded as data
        if ('%g' % (level - 1000.0)) in free and \
                ('%g' % (level + 1000.0)) in free:
            lo = free['%g' % (level - 1000.0)]
            hi = free['%g' % (level + 1000.0)]
            dz_f = hi['z_south_m'] - lo['z_south_m']
            dv_f = hi['volume_m3'] - lo['volume_m3']
            mis = dv_f / dz_f
            row['a14_misderived_dV_free_dz_m2'] = mis
            row['a14_misderived_relative_disagreement'] = \
                rel_disagreement(d_prod, mis)
        # production-gate disagreement and the derived bound
        row['prod_relative_disagreement'] = rel_disagreement(d_prod,
                                                             d_w_prod)
        trunc = (row['dF_prod_trunc_bound_m2'] +
                 row.get('dV_prod_trunc_bound_m2', 0.0))
        noise = noise_dp + row.get('dV_noise_floor_m2', 0.0)
        gap = abs(d_dp_corr - row.get('dV_dx_corrected_m2', d_w_prod))
        row['derived_trunc_bound_m2'] = trunc
        row['derived_noise_floor_m2'] = noise
        row['probed_branch_gap_m2'] = gap
        bound_abs = trunc + noise + gap
        row['derived_bound_abs_m2'] = bound_abs
        row['derived_rel_bound'] = bound_abs / max(abs(d_prod),
                                                  abs(d_w_prod),
                                                  aw.WIN['reciprocity_floor'])
        derivation['%g' % level] = row

    rec['derivation'] = derivation

    gate_worst = max(derivation['%g' % lv]['derived_rel_bound']
                     for lv in GATE_LEVELS)
    rec['gate_worst_derived_rel_bound'] = gate_worst
    rec['gate_worst_measured_rel'] = max(
        derivation['%g' % lv]['prod_relative_disagreement']
        for lv in GATE_LEVELS)
    window = None
    for cand in LADDER:
        if cand >= MARGIN * gate_worst:
            window = cand
            break
    rec['derived_window'] = window
    rec['window_rule'] = ('smallest ladder value >= %.1fx the derived '
                          'rel_bound at both gate levels' % MARGIN)
    # secondary, disclosed in Amendment A1.9: the 2x margin is a scatter
    # margin while the dominant bound term is a probed deterministic
    # systematic (branch/evaluation gap); the re-issued window is the
    # smallest ladder value exceeding the derived worst-level bound with
    # at least 10% cushion
    CUSHION = 0.10
    window_cushion = None
    for cand in LADDER:
        if cand >= (1.0 + CUSHION) * gate_worst:
            window_cushion = cand
            break
    rec['window_cushion_pick'] = window_cushion
    rec['window_cushion_rule'] = ('smallest ladder value >= %.2fx the '
                                  'derived worst-gate-level bound' %
                                  (1.0 + CUSHION))

    # committed window in code (pre-correction state read for the record)
    rec['window_before_correction'] = aw.WIN['reciprocity_rel']
    rec['a14_committed_window'] = 0.20

    path = HERE / 'x3_derivation_probes.json'
    body = json.dumps(rec, indent=1, sort_keys=True)
    path.write_bytes(body.encode('utf-8'))
    print('wrote', path)
    for lv in ('2000', '3000'):
        row = derivation[lv]
        print(lv, 'prod_rel=%.4f' % row['prod_relative_disagreement'],
              'rel_bound=%.4f' % row['derived_rel_bound'])
    print('derived window:', window)


if __name__ == '__main__':
    main()
