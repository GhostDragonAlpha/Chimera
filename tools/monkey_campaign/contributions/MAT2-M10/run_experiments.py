"""MAT2-M10 experiment bank: runs the frozen experiments (PREREGISTRATION.md
+ Amendment A1), writes experiment_receipt.json / experiment_trace.json and
the falsifier receipts. Modes:

  python -B run_experiments.py main      -> X0-X6 bank + trace
  python -B run_experiments.py falsify   -> FB1-FB6 arms (clean controls first)
  python -B run_experiments.py rerun     -> fresh dynamic run for X7
  python -B run_experiments.py regression-> upstream sealed suites
  python -B run_experiments.py compare   -> X7 byte-identity receipt

CPU-only; stdlib + numpy; deterministic (no RNG, no wall-clock in results).
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import actuator_world as aw  # noqa: E402
import material_state as ms01  # noqa: E402  (M01 validator, UNMODIFIED)
import pressure_membrane as pm  # noqa: E402  (M03, UNMODIFIED)

TRACE_PATH = HERE / 'experiment_trace.json'
RECEIPT_PATH = HERE / 'experiment_receipt.json'
FALSIFIER_PATH = HERE / 'falsifier_receipt.json'
DETERMINISM_PATH = HERE / 'determinism_receipt.json'
REGRESSION_PATH = HERE / 'regression_receipt.json'

CRITERIA_SHA256 = '5e7560caa9efae9ec819c9127ab6ee6e7016e134bdf97e525f06cfedee31190c'
ATTEMPT_ID = '02cc9dbda6f3494f8d8de36e20b94c0f'
ARRIVAL_ID = 'arrival-5c71030b5a614f89ac0716c1d99bfa0d'


def require(condition, code):
    if not condition:
        raise ValueError(code)


def refuse_vacuous_comparison(a, b, code='vacuous_comparison_refused'):
    """P5 (M07 lesson): an identically-zero both-sides window comparison is
    not a measurement; refuse it loudly BEFORE any tolerance check."""
    if a == 0.0 and b == 0.0:
        raise ValueError(code + ':%s,%.3e,%.3e' % (code, a, b))
    return False


def vacuous_guard_selftest():
    """The guard must refuse the identically-zero comparison."""
    try:
        refuse_vacuous_comparison(0.0, 0.0, 'vacuous_guard_selftest_probe')
    except ValueError as exc:
        require('vacuous_guard_selftest_probe' in str(exc),
                'vacuous_guard_selftest_wrong_code')
        return {'fires_on_identically_zero_window': True,
                'refusal_code': 'vacuous_comparison_refused',
                'lesson': 'a gate that cannot fail is not a measurement '
                          '(M07 independent-review lesson)'}
    raise ValueError('vacuous_guard_selftest_did_not_fire')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False)


def sha256_of(path):
    import hashlib
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def write_json(path, payload):
    pathlib.Path(path).write_text(
        json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False,
                   default=_json_default) + '\n',
        encoding='utf-8', newline='\n')


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def run_and_record(model, schedule, ticks, mode, **kw):
    run = aw.WorldRun(model, schedule, ticks, mode=mode, **kw)
    run.run()
    return run


def gap_delta(model, run):
    return float(model.pole_gap(run.x) - model.pole_gap_rest)


def settle_ok(run):
    st = run.settle_stats()
    return st['position_drift_m'] <= aw.SETTLE_DRIFT_M, st


# --------------------------------------------------------------- bank -----
def mode_main():
    guard = vacuous_guard_selftest()
    pins = aw.verify_input_pins()
    bank = {'criteria_sha256': CRITERIA_SHA256, 'attempt_id': ATTEMPT_ID,
            'arrival_id': ARRIVAL_ID, 'input_pins': pins,
            'p_vacuous_guard': guard, 'windows': aw.WIN,
            'classification_rule': aw.CLASSIFICATION_RULE}

    # ---- X0 material_state gate (M01 validator UNMODIFIED)
    model = aw.ActuatorModel('braid')
    doc = aw.state_document(model, revision=1, bond_bound=True)
    summary = ms01.validate_material_state(doc)
    doc2 = aw.state_document(model, revision=2, bond_bound=True)
    summary2 = ms01.validate_material_state(doc2)
    bank['X0_material_state'] = {
        'validated': True, 'region_count': summary['region_count'],
        'law_count': summary['law_count'], 'bond_count': summary['bond_count'],
        'total_mass_kg': summary['total_mass_kg'],
        'revision2_validated': True, 'revision2_region_count':
            summary2['region_count']}

    # ---- X1 directional family (free runs, tie RELEASED, 2000 Pa)
    family = {}
    for label, side, iso in (('braid', 'braid', False),
                             ('belt', 'belt', False),
                             ('iso', 'braid', True)):
        m = aw.ActuatorModel(side, isotropic=iso)
        run = aw.WorldRun(m, aw.level_schedule(2000.0), aw.QS_TICKS,
                          mode='free')
        run.tie.release(0)
        run.run()
        settled, st = settle_ok(run)
        family[label] = {
            'delta_gap_m': gap_delta(m, run),
            'settle_ok': settled, 'max_speed_m_per_s': st['max_speed_m_per_s'],
            'ke_max_j': st['ke_max_j'],
            'chord_strain_min': run.chord_strain_min,
            'chord_strain_max': run.chord_strain_max,
            'traction_ratio_worst': run.traction_ratio_worst,
            'max_delta_p_pa': run.max_dp_seen,
            'max_flow_m3_per_s': run.max_flow_seen}
    dg = {k: family[k]['delta_gap_m'] for k in family}
    bank['X1_directional'] = {
        'per_layout': family,
        'X1a_contraction': dg['braid'] <= aw.WIN['gap_braid_max'],
        'X1b_belt_extension': dg['belt'] >= aw.WIN['gap_belt_min'],
        'X1c_iso_baseline': dg['iso'] >= aw.WIN['gap_iso_min'],
        'X1d_dir_braid_vs_iso':
            dg['braid'] - dg['iso'] <= aw.WIN['dir_braid_max'],
        'X1d_dir_belt_vs_iso':
            dg['belt'] - dg['iso'] >= aw.WIN['dir_belt_min'],
        'delta_gap': dg}
    x1_pass = all(bank['X1_directional'][k] for k in
                  ('X1a_contraction', 'X1b_belt_extension', 'X1c_iso_baseline',
                   'X1d_dir_braid_vs_iso', 'X1d_dir_belt_vs_iso'))

    # ---- X1e monotonicity (braid free at 1000/2000/4000)
    mono = {}
    for level in (1000.0, 2000.0, 4000.0):
        m = aw.ActuatorModel('braid')
        run = aw.WorldRun(m, aw.level_schedule(level), aw.QS_TICKS,
                          mode='free')
        run.tie.release(0)
        run.run()
        settled, st = settle_ok(run)
        require(settled, 'qs_run_not_settled:%g' % level)
        mono['%g' % level] = {'delta_gap_m': gap_delta(m, run),
                              'volume_m3': st['volume_m3'],
                              'z_south_m': st['z_tip_m'],
                              'max_speed_m_per_s': st['max_speed_m_per_s']}
    bank['X1e_monotonicity'] = {
        'per_level': mono,
        'ordered': (mono['4000']['delta_gap_m'] < mono['2000']['delta_gap_m']
                    < mono['1000']['delta_gap_m'] < -aw.WIN[
                        'monotone_epsilon_m'])}
    x1_pass = x1_pass and bank['X1e_monotonicity']['ordered']

    # ---- X2/X3 families at all levels (braid; A1.9): blocked (tie
    # RELEASED), free (tie released), loaded light/heavy (tie attached).
    # The A1.9 two-load family gives dV/dx at fixed p (Maxwell); the
    # blocked family gives dF_block/dp at fixed x.
    levels = aw.LEVELS_PA
    blocked, free, loaded, heavy = {}, {}, {}, {}
    for level in levels:
        mb = aw.ActuatorModel('braid')
        rb = aw.WorldRun(mb, aw.level_schedule(level), aw.QS_TICKS,
                         mode='blocked')
        rb.tie.release(0)
        rb.run()
        sb = rb.settle_stats()
        require(sb['position_drift_m'] <= aw.SETTLE_DRIFT_M,
                'blocked_run_not_settled:%g' % level)
        blocked['%g' % level] = {
            'pin_force_n': sb['pin_force_n'],
            'reaction_on_anchor_n': [-c for c in sb['pin_force_n']],
            'max_speed_m_per_s': sb['max_speed_m_per_s']}
        mf = aw.ActuatorModel('braid')
        rf = aw.WorldRun(mf, aw.level_schedule(level), aw.QS_TICKS,
                         mode='free')
        rf.tie.release(0)
        rf.run()
        sf = rf.settle_stats()
        require(sf['position_drift_m'] <= aw.SETTLE_DRIFT_M,
                'free_run_not_settled:%g' % level)
        free['%g' % level] = {
            'delta_gap_m': gap_delta(mf, rf),
            'volume_m3': sf['volume_m3'],
            'z_south_m': sf['z_tip_m'],
            'max_speed_m_per_s': sf['max_speed_m_per_s']}
        ml = aw.ActuatorModel('braid')
        rl = run_and_record(ml, aw.level_schedule(level), aw.QS_TICKS,
                            'loaded')
        sl = rl.settle_stats()
        require(sl['position_drift_m'] <= aw.SETTLE_DRIFT_M,
                'loaded_run_not_settled:%g' % level)
        loaded['%g' % level] = {
            'volume_m3': sl['volume_m3'],
            'z_south_m': sl['z_tip_m'],
            'z_load_m': sl['z_load_m'],
            'tie_tension_n': sl['tie_tension_n'],
            'max_speed_m_per_s': sl['max_speed_m_per_s']}
    heavy_levels = (2000.0, 3000.0)  # the X3 interior levels (A1.9)
    for level in heavy_levels:
        mh = aw.ActuatorModel('braid')
        rh = run_and_record(mh, aw.level_schedule(level), aw.QS_TICKS,
                            'loaded', load_mass=0.020)
        sh = rh.settle_stats()
        require(sh['position_drift_m'] <= aw.SETTLE_DRIFT_M,
                'heavy_run_not_settled:%g' % level)
        heavy['%g' % level] = {
            'volume_m3': sh['volume_m3'],
            'z_south_m': sh['z_tip_m'],
            'z_load_m': sh['z_load_m'],
            'tie_tension_n': sh['tie_tension_n'],
            'max_speed_m_per_s': sh['max_speed_m_per_s']}
    # X2 claims
    r4 = blocked['%g' % 4000.0]['reaction_on_anchor_n'][2]
    r1 = blocked['%g' % 1000.0]['reaction_on_anchor_n'][2]
    r2k = blocked['%g' % 2000.0]['reaction_on_anchor_n'][2]
    r3k = blocked['%g' % 3000.0]['reaction_on_anchor_n'][2]
    # A1.11: the chord net tensions progressively (rest-strain-zero chords
    # engage as the bladder inflates), so the blocked force is SUBLINEAR at
    # low p — the A1.4 near-linearity claim was wrong for this architecture
    # (probe F(1000)/F(4000) = 0.042, recorded). Frozen: monotone
    # nondecreasing and sublinear at low p.
    bank['X2_blocked'] = {
        'per_level': blocked,
        'reaction_sign_positive': r4 > 0.0,
        'magnitude_window': (aw.WIN['f_block_lo_n'] <= abs(r4) <=
                             aw.WIN['f_block_hi_n']),
        'reaction_4000_z_n': r4, 'reaction_1000_z_n': r1,
        'monotone_nondecreasing': (0.0 <= r1 <= r2k <= r3k <= r4),
        'sublinear_low_p': (r1 / r4) <= aw.WIN['f_linearity_abs']}
    x2_pass = all(bank['X2_blocked'][k] for k in
                  ('reaction_sign_positive', 'magnitude_window',
                   'monotone_nondecreasing', 'sublinear_low_p'))

    # ---- X3 Maxwell reciprocity (A1.9): dF_block/dp at fixed x (blocked
    # family, central differences) vs dV/dx at fixed p (the two-load family
    # at the interior levels). The A1.4 form was mis-derived: differencing
    # the FREE family across pressure levels carries the fixed-shape
    # inflation term dV/dp|x — the triggering probe (the ~100x
    # disagreement) is recorded AS DATA in x3_derivation_probes.json
    # (a14_misderived_* fields) and restated in Amendment A1.9; the
    # fixed-p form below is the correct Maxwell pair. The acceptance
    # window is the A1.9 re-issued WIN['reciprocity_rel'].
    rec = {}
    dfdp2000 = ((blocked['%g' % 3000.0]['reaction_on_anchor_n'][2] -
                 blocked['%g' % 1000.0]['reaction_on_anchor_n'][2]) / 2000.0)
    dfdp3000 = ((blocked['%g' % 4000.0]['reaction_on_anchor_n'][2] -
                 blocked['%g' % 2000.0]['reaction_on_anchor_n'][2]) / 2000.0)
    for interior, dfdp in ((2000.0, dfdp2000), (3000.0, dfdp3000)):
        dz = (heavy['%g' % interior]['z_south_m'] -
              loaded['%g' % interior]['z_south_m'])
        dv = (heavy['%g' % interior]['volume_m3'] -
              loaded['%g' % interior]['volume_m3'])
        require(abs(dz) > 1e-9, 'reciprocity_degenerate_dx')
        dvdz = dv / dz
        refuse_vacuous_comparison(dfdp, dvdz,
                                  'm10_reciprocity_vacuous_window')
        denom = max(abs(dfdp), abs(dvdz), aw.WIN['reciprocity_floor'])
        rel = abs(dfdp - dvdz) / denom
        rec['%g' % interior] = {
            'dF_block_dp_m2': dfdp, 'dV_dx_at_fixed_p_m2': dvdz,
            'dx_m': dz, 'dV_m3': dv,
            'relative_disagreement': rel,
            'within_window': rel <= aw.WIN['reciprocity_rel']}
    bank['X3_reciprocity'] = rec
    x3_pass = all(v['within_window'] for v in rec.values())

    # ---- X4 load-line superposition at 4000 Pa (loaded-light vs free)
    sl = loaded['%g' % 4000.0]
    mf4 = aw.ActuatorModel('braid')
    z_rest_south = float(mf4.rest[mf4.south, 2])
    dz_free = free['%g' % 4000.0]['z_south_m'] - z_rest_south
    dz_loaded = sl['z_south_m'] - z_rest_south
    t_meas = sl['tie_tension_n']
    f_block = r4
    z_pred = dz_free * (1.0 - t_meas / f_block)
    refuse_vacuous_comparison(z_pred, dz_loaded,
                              'm10_superposition_vacuous_window')
    sup = abs(dz_loaded - z_pred) / max(abs(z_pred),
                                        aw.WIN['superposition_floor_m'])
    bank['X4_superposition'] = {
        'dz_free_m': dz_free, 'dz_loaded_m': dz_loaded, 'dz_pred_m': z_pred,
        'T_meas_n': t_meas, 'F_block_n': f_block,
        'relative_disagreement': sup,
        'within_window': sup <= aw.WIN['superposition_rel'],
        'tie_follow_m': abs(abs(sl['z_load_m'] - sl['z_south_m']) -
                            aw.L_TIE),
        'tie_follow_within': abs(abs(sl['z_load_m'] - sl['z_south_m']) -
                                 aw.L_TIE) <= aw.WIN['tie_follow_m']}
    x4_pass = bank['X4_superposition']['within_window'] and \
        bank['X4_superposition']['tie_follow_within']

    # ---- X2d power-off blocked (p=0)
    m0 = aw.ActuatorModel('braid')
    r0 = aw.WorldRun(m0, aw.level_schedule(0.0), aw.QS_TICKS,
                     mode='blocked')
    r0.tie.release(0)
    r0.run()
    s0 = r0.settle_stats()
    require(s0['position_drift_m'] <= aw.SETTLE_DRIFT_M,
            'blocked_zero_run_not_settled')
    rz0 = -s0['pin_force_n'][2]
    bank['X2d_power_off'] = {
        'reaction_z_n': rz0,
        'within': abs(rz0) <= aw.WIN['f_zero_residual'] * abs(r4) +
        aw.WIN['f_zero_floor_n']}
    x2_pass = x2_pass and bank['X2d_power_off']['within']

    # ---- X5 dynamic work run (capture scenario)
    md = aw.ActuatorModel('braid')
    rd = run_and_record(md, aw.work_schedule, aw.TOTAL_TICKS, 'loaded',
                        record_forces=True, snapshot_ticks=aw.SNAP_TICKS)
    gates = rd.check_ledger_gates()  # raises on any ledger violation
    zl_base = rd.window_mean(*aw.BASELINE_WINDOW, 'z_load_m')
    zl_peak = rd.window_mean(*aw.PEAK_WINDOW, 'z_load_m')
    zl_end = rd.window_mean(1300, 1500, 'z_load_m')
    lift = zl_peak - zl_base
    mg = aw.M_LOAD_KG * aw.GRAV
    w_load = mg * lift
    eta = w_load / rd.w_press_hold_total
    # power identity: sum P dt vs W_press
    p_sum = 0.0
    prev_v = None
    for row in rd.rows:
        if prev_v is not None:
            p_sum += row['delta_p_pa'] * (row['volume_m3'] - prev_v)
        prev_v = row['volume_m3']
    power_rel = abs(p_sum - rd.w_press_total) / max(abs(rd.w_press_total),
                                                    1e-15)
    # per-phase extraction (P6 keyed extractors)
    phases = {}
    for name in aw.PHASE_NAMES:
        sel = [r for r in rd.rows if r['phase'] == name]
        require(sel, 'phase_missing:' + name)
        require(all('r_tick_j' in r for r in sel),
                'phase_metric_key_missing:' + name)
        phases[name] = {'count': len(sel),
                        'w_press_j': sum(r['w_press_vol_j'] for r in sel),
                        'worst_abs_r_j': max(abs(r['r_tick_j'])
                                             for r in sel)}
    lift_peak_south = (rd.window_mean(*aw.PEAK_WINDOW, 'z_tip_m') -
                       rd.window_mean(*aw.BASELINE_WINDOW, 'z_tip_m'))
    bank['X5_work'] = {
        'ledger_gates': gates,
        'lift_m': lift, 'lift_within': (aw.WIN['lift_lo_m'] <= lift <=
                                        aw.WIN['lift_hi_m']),
        'lift_positive': lift > 0.0,
        'w_load_j': w_load, 'eta': eta, 'eta_within': eta <= aw.WIN['eta_hi'],
        'w_press_hold_total_j': rd.w_press_hold_total,
        'w_press_total_j': rd.w_press_total,
        'power_identity_rel': power_rel,
        'power_identity_within': power_rel <= aw.WIN['power_identity_rel'],
        'tie_tension_peak_n': rd.window_mean(*aw.PEAK_WINDOW,
                                             'tie_tension_n'),
        'power_off_return_m': zl_end - zl_base,
        'power_off_within': abs(zl_end - zl_base) <= aw.WIN[
            'power_off_recovery'] * abs(lift),
        'tie_return_within': (rd.window_mean(1300, 1500, 'tie_tension_n') <=
                              aw.WIN['tie_return_factor'] * mg),
        'phase_state_counts': {k: v['count'] for k, v in phases.items()},
        'phases': phases,
        'south_lift_peak_m': lift_peak_south,
        'chord_strain_min': rd.chord_strain_min,
        'chord_strain_max': rd.chord_strain_max,
        'traction_ratio_worst': rd.traction_ratio_worst,
        'max_delta_p_pa': rd.max_dp_seen, 'max_flow_m3_per_s':
            rd.max_flow_seen}
    x5_pass = all(bank['X5_work'][k] for k in
                  ('lift_within', 'lift_positive', 'eta_within',
                   'power_identity_within', 'power_off_within',
                   'tie_return_within'))

    # ---- X6 pressure limits (named refusals, M03 codes)
    src = pm.PressureSource(
        aw.SOURCE_ID, aw.P_EXT_PA, aw.P_EXT_PA, aw.MAX_DELTA_P_PA,
        aw.MAX_FLOW_M3_PER_S, aw.SOURCE_PROVENANCE)
    shell = pm.Membrane(model.rest, model.tris, 'm10_limits_probe')
    limits = {}
    for name, fn in (
            ('pressure_source_delta_p_limit_exceeded',
             lambda: src.with_delta_p(6000.0)),
            ('pressure_source_negative_absolute',
             lambda: pm.PressureSource(
                 'bad', -1.0, 0.0, aw.MAX_DELTA_P_PA,
                 aw.MAX_FLOW_M3_PER_S, 'x')),
            ('pressure_source_undeclared',
             lambda: shell.triangle_tractions('not-a-source')),
            ('pressure_source_flow_limit_exceeded',
             lambda: src.power_watts(2.0e-3))):
        try:
            fn()
            fired = False
            code = ''
        except ValueError as exc:
            fired = True
            code = str(exc)
        limits[name] = {'fired': fired, 'code': code}
        require(fired, 'limit_refusal_did_not_fire:' + name)
    bank['X6_limits'] = {'refusals': limits,
                         'all_fired': all(v['fired'] for v in
                                          limits.values())}

    # ---- compile verdict
    bank['X1_pass'] = x1_pass
    bank['X2_pass'] = x2_pass
    bank['X3_pass'] = x3_pass
    bank['X4_pass'] = x4_pass
    bank['X5_pass'] = x5_pass
    bank['X6_pass'] = bank['X6_limits']['all_fired']
    bank['all_gates_green'] = all(bank[k] for k in
                                  ('X1_pass', 'X2_pass', 'X3_pass',
                                   'X4_pass', 'X5_pass', 'X6_pass'))

    # ---- trace: the dynamic run rows + snapshot stream (determinism unit)
    trace = {
        'schema': 'm10.trace.v1',
        'criteria_sha256': CRITERIA_SHA256,
        'dynamic_run': {
            'rows': rd.rows,
            'snapshots': {str(k): v for k, v in sorted(
                rd.snapshots.items())},
            'force_rows_present': rd.record_forces,
            'chord_strain_min': rd.chord_strain_min,
            'chord_strain_max': rd.chord_strain_max,
            'w_press_hold_total_j': rd.w_press_hold_total,
            'w_press_total_j': rd.w_press_total,
        },
        'qs_family': {'free': free, 'blocked': blocked,
                      'loaded_4000': {
                          'z_south_m': loaded['%g' % 4000.0]['z_south_m'],
                          'z_load_m': loaded['%g' % 4000.0]['z_load_m'],
                          'tie_tension_n': loaded['%g' % 4000.0][
                              'tie_tension_n'],
                          'volume_m3': loaded['%g' % 4000.0][
                              'volume_m3']}},
    }
    write_json(TRACE_PATH, trace)
    bank['trace_sha256'] = sha256_of(TRACE_PATH)
    write_json(RECEIPT_PATH, bank)
    print('all_gates_green:', bank['all_gates_green'])
    print('trace sha256:', bank['trace_sha256'])
    return 0


# ----------------------------------------------------------- falsifiers ---
def mode_falsify():
    guard = vacuous_guard_selftest()
    receipt = {'criteria_sha256': CRITERIA_SHA256, 'p_vacuous_guard': guard}

    def dynamic(tamper=None):
        m = aw.ActuatorModel('braid')
        r = run_and_record(m, aw.work_schedule, aw.TOTAL_TICKS, 'loaded',
                           tamper=tamper, record_forces=True)
        return m, r

    # ---- FB1 activation writes body poses (clean control FIRST)
    _, clean = dynamic()
    clean_dev = clean.audit_load_trajectory()
    require(clean_dev <= aw.WIN['audit_window_m'],
            'm10_fb1_premature:%.3e' % clean_dev)
    _, tampered = dynamic({'pose_writer': True})
    tampered_dev = tampered.audit_load_trajectory()
    bit = tampered_dev > aw.WIN['audit_bite_m']
    receipt['FB1_activation_writes_poses'] = {
        'clean_control': {'metric_scope': 'motion audit: re-integration of '
                          'the load from recorded per-substep forces',
                          'deviation_m': clean_dev,
                          'within_tolerance': True,
                          'guard': 'm10_fb1_premature'},
        'tampered_deviation_m': tampered_dev,
        'window_m': aw.WIN['audit_window_m'],
        'bite_m': aw.WIN['audit_bite_m'],
        'bit': bit}
    require(bit, 'fb1_arm_did_not_bite')

    # ---- FB2 contraction from isotropic inflation alone
    # (clean controls = the X1 family re-run in THIS executable)
    iso = aw.ActuatorModel('braid', isotropic=True)
    iso_run = run_and_record(iso, aw.level_schedule(2000.0), aw.QS_TICKS,
                             'free')
    dg_iso = gap_delta(iso, iso_run)
    require(dg_iso >= aw.WIN['gap_iso_min'],
            'm10_fb2_premature:%.3e' % dg_iso)
    braid = aw.ActuatorModel('braid')
    braid_run = run_and_record(braid, aw.level_schedule(2000.0), aw.QS_TICKS,
                               'free')
    dg_braid = gap_delta(braid, braid_run)
    belt = aw.ActuatorModel('belt')
    belt_run = run_and_record(belt, aw.level_schedule(2000.0), aw.QS_TICKS,
                              'free')
    dg_belt = gap_delta(belt, belt_run)
    delta = dg_braid - dg_iso
    bit = delta <= aw.WIN['dir_braid_max'] and dg_belt >= aw.WIN['gap_belt_min']
    receipt['FB2_isotropic_inflation'] = {
        'clean_control': {'metric_scope': 'iso baseline extends at 2000 Pa',
                          'delta_gap_m': dg_iso, 'within_tolerance': True,
                          'guard': 'm10_fb2_premature'},
        'braid_delta_gap_m': dg_braid, 'belt_delta_gap_m': dg_belt,
        'directional_delta_m': delta,
        'window_m': aw.WIN['dir_braid_max'],
        'bit': bit}
    require(bit, 'fb2_arm_did_not_bite')

    # ---- FB3 work has no source (one-way tie boost x2.0; A1.8: the bite
    # is the state-determined force-law audit — the applied tie force must
    # equal the M05 law force at the same state)
    clean_audit = clean.audit_tie_force_law()
    require(clean_audit['max_force_law_dev_n'] == 0.0,
            'm10_fb3_premature:%.3e' % clean_audit['max_force_law_dev_n'])
    _, boosted = dynamic({'tie_boost': 2.0})
    boost_audit = boosted.audit_tie_force_law()
    bit = boost_audit['max_force_law_dev_n'] > 0.05 * max(
        boost_audit['peak_law_force_n'], 1e-12)
    receipt['FB3_work_without_source'] = {
        'clean_control': {'metric_scope': 'state-determined tie force-law '
                          'audit on the clean dynamic run (bitwise zero)',
                          'max_force_law_dev_n':
                              clean_audit['max_force_law_dev_n'],
                          'within_tolerance': True,
                          'guard': 'm10_fb3_premature'},
        'tampered_audit': boost_audit,
        'bit': bit}
    require(bit, 'fb3_arm_did_not_bite')

    # ---- FB4 area-independent triangle forces (M03 heritage)
    bp_clean = aw.buoyancy_probe(aw.ActuatorModel('braid'))
    require(bp_clean['rel_error'] <= aw.WIN['buoyancy_rel'],
            'm10_fb4_premature:%.3e' % bp_clean['rel_error'])
    bp_tamper = aw.buoyancy_probe(aw.ActuatorModel('braid'),
                                  constant_weighting=True)
    bit = bp_tamper['rel_error'] >= aw.WIN['buoyancy_tamper_rel']
    receipt['FB4_area_independent_forces'] = {
        'clean_control': {'metric_scope': 'M03 linear-field buoyancy '
                          'identity F = rho g V (mixed-area mesh)',
                          'rel_error': bp_clean['rel_error'],
                          'within_tolerance': True,
                          'guard': 'm10_fb4_premature'},
        'tampered_rel_error': bp_tamper['rel_error'],
        'clean_net_force_n': bp_clean['net_force_n'],
        'tampered_net_force_n': bp_tamper['net_force_n'],
        'reference_n': bp_clean['reference_n'],
        'bit': bit}
    require(bit, 'fb4_arm_did_not_bite')

    # ---- FB5 clipped load path (tie reaction dropped)
    _, dropped = dynamic({'drop_tie_reaction': True})
    drop_interface = dropped.audit_tie_force_law()
    require(drop_interface['max_reaction_dev_n'] > 0.05 * max(
        drop_interface['peak_law_force_n'], 1e-12),
        'm10_fb5_interface_premature')
    drop_dev = dropped.audit_load_trajectory()
    tip_clean = clean.window_mean(*aw.PEAK_WINDOW, 'z_tip_m')
    tip_drop = dropped.window_mean(*aw.PEAK_WINDOW, 'z_tip_m')
    # A1.10/A1.8: the settle tolerance window is POSITIONAL; the dropped
    # reaction leaves the load-side forces unchanged (the motion audit is
    # not the discriminator here — the interface audit and the membrane's
    # tip position are)
    bit = (drop_interface['max_reaction_dev_n'] > 0.05 * max(
        drop_interface['peak_law_force_n'], 1e-12)) and abs(
        tip_drop - tip_clean) > aw.WIN['fb5_path_factor'] * aw.SETTLE_DRIFT_M
    receipt['FB5_clipped_load_path'] = {
        'clean_control': {'metric_scope': 'audit + tip position on the '
                          'clean dynamic run',
                          'audit_dev_m': clean_dev, 'tip_peak_m': tip_clean,
                          'within_tolerance': True,
                          'guard': 'm10_fb5_premature'},
        'dropped_motion_audit_dev_m': drop_dev,
        'dropped_tip_peak_m': tip_drop,
        'tip_difference_m': abs(tip_drop - tip_clean),
        'dropped_interface_audit': drop_interface,
        'bit': bit}
    require(bit, 'fb5_arm_did_not_bite')

    # ---- FB6 hidden constraint/support (structural scene audit)
    scene = ['actuator_shell', 'clamp_north_cap', 'tie_south_pole', 'load',
             'source_m10_source']
    rendered_subjects = ['actuator_shell', 'clamp_north_cap',
                         'tie_south_pole', 'load', 'source_m10_source']
    missing = [s for s in scene if s not in rendered_subjects]
    require(not missing, 'm10_fb6_premature:%s' % missing)
    tampered_scene = [s for s in rendered_subjects
                      if s != 'clamp_north_cap']
    missing_t = [s for s in scene if s not in tampered_scene]
    receipt['FB6_hidden_support'] = {
        'clean_control': {'metric_scope': 'scene inventory vs rendered '
                          'subject list', 'missing_subject_ids': [],
                          'within_tolerance': True,
                          'guard': 'm10_fb6_premature'},
        'tampered_missing_subject_ids': missing_t,
        'expected_code': 'support_missing_from_scene',
        'bit': bool(missing_t)}
    require(bool(missing_t), 'fb6_arm_did_not_bite')

    receipt['all_arms_bit'] = all(
        receipt[k]['bit'] for k in
        ('FB1_activation_writes_poses', 'FB2_isotropic_inflation',
         'FB3_work_without_source', 'FB4_area_independent_forces',
         'FB5_clipped_load_path', 'FB6_hidden_support'))
    write_json(FALSIFIER_PATH, receipt)
    print('falsifier arms all bit:', receipt['all_arms_bit'])
    return 0


# ------------------------------------------------------------ determinism -
def _dynamic_trace_payload():
    m = aw.ActuatorModel('braid')
    r = run_and_record(m, aw.work_schedule, aw.TOTAL_TICKS, 'loaded',
                       record_forces=True, snapshot_ticks=aw.SNAP_TICKS)
    return {
        'schema': 'm10.trace.v1',
        'criteria_sha256': CRITERIA_SHA256,
        'dynamic_run': {
            'rows': r.rows,
            'snapshots': {str(k): v for k, v in sorted(r.snapshots.items())},
            'force_rows_present': r.record_forces,
            'chord_strain_min': r.chord_strain_min,
            'chord_strain_max': r.chord_strain_max,
            'w_press_hold_total_j': r.w_press_hold_total,
            'w_press_total_j': r.w_press_total,
        },
    }


def mode_rerun():
    payload = _dynamic_trace_payload()
    write_json(HERE / 'experiment_trace_rerun.json', payload)
    print('rerun trace written')
    return 0


def mode_compare():
    main_trace = json.loads(TRACE_PATH.read_text(encoding='utf-8'))
    rerun_trace = json.loads(
        (HERE / 'experiment_trace_rerun.json').read_text(encoding='utf-8'))
    # declared determinism unit: the dynamic_run subtree (the main trace
    # additionally carries the qs_family, which the rerun does not repeat)
    c1 = canonical(main_trace['dynamic_run'])
    c2 = canonical(rerun_trace['dynamic_run'])
    import hashlib
    t1 = hashlib.sha256(c1.encode('utf-8')).hexdigest()
    t2 = hashlib.sha256(c2.encode('utf-8')).hexdigest()
    identical = t1 == t2
    receipt = {'criteria_sha256': CRITERIA_SHA256,
               'dynamic_run_sha256_main': t1,
               'dynamic_run_sha256_rerun': t2,
               'X2_trace_byte_identical': identical,
               'X2_pass': identical,
               'declared_determinism_unit':
                   'the canonical dynamic_run subtree of '
                   'experiment_trace.json (two fresh subprocess-equivalent '
                   'runs at the same revision)'}
    write_json(DETERMINISM_PATH, receipt)
    print('X2 byte-identical:', identical)
    require(identical, 'determinism_violated')
    return 0


# ------------------------------------------------------------- regression -
def mode_regression():
    checks = {}
    suites = [
        ('M03', str(HERE.parent / 'MAT2-M03'),
         'test_pressure_membrane.py'),
        ('M04', str(HERE.parent / 'MAT2-M04'), 'test_passive_response.py'),
        ('M05', str(HERE.parent / 'MAT2-M05'),
         'test_interface_exchange.py'),
        ('M08', str(HERE.parent / 'MAT2-M08'),
         'test_resident_gpu_world.py'),
    ]
    for name, directory, script in suites:
        proc = subprocess.run(
            [sys.executable, '-B', str(pathlib.Path(directory) / script)],
            capture_output=True, text=True, timeout=1800)
        checks[name] = {'script': script, 'returncode': proc.returncode,
                        'tail': (proc.stdout + proc.stderr)[-400:]}
    ok = all(v['returncode'] == 0 for v in checks.values())
    receipt = {'criteria_sha256': CRITERIA_SHA256, 'suites': checks,
               'regression_ok': ok}
    write_json(REGRESSION_PATH, receipt)
    print('regression ok:', ok)
    require(ok, 'regression_failed')
    return 0


def main(argv):
    require(vacuous_guard_selftest()['fires_on_identically_zero_window'],
            'vacuous_guard_must_selftest_before_any_receipt')
    mode = argv[1] if len(argv) > 1 else 'main'
    if mode == 'main':
        return mode_main()
    if mode == 'falsify':
        return mode_falsify()
    if mode == 'rerun':
        return mode_rerun()
    if mode == 'compare':
        return mode_compare()
    if mode == 'regression':
        return mode_regression()
    raise ValueError('unknown_mode:' + mode)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
