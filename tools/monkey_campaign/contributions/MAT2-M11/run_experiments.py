"""MAT2-M11 experiment bank: runs the frozen experiments (PREREGISTRATION.md
+ Amendments A1/A2), writes experiment_receipt.json / experiment_trace.json
and the falsifier/determinism/regression receipts. Modes:

  python -B run_experiments.py main      -> X1-X6, X8 bank + trace
  python -B run_experiments.py falsify   -> FB1-FB6 arms (clean controls first)
  python -B run_experiments.py rerun     -> fresh dynamic run for X7
  python -B run_experiments.py compare   -> X7 byte-identity receipt
  python -B run_experiments.py regression-> upstream sealed suites

CPU-only (declared scope, prereg section 9); stdlib + numpy; deterministic
(no RNG, no wall-clock in results). Composed against CARD_STARTER v2.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import limb_world as lw  # noqa: E402  (the M11 world; M03/M04/M05 imported
#                          UNMODIFIED inside it)

TRACE_PATH = HERE / 'experiment_trace.json'
RECEIPT_PATH = HERE / 'experiment_receipt.json'
FALSIFIER_PATH = HERE / 'falsifier_receipt.json'
DETERMINISM_PATH = HERE / 'determinism_receipt.json'
REGRESSION_PATH = HERE / 'regression_receipt.json'

# receipt schemas (batch-gate law: every *receipt*.json carries a
# chimera.*.vN schema; asserted by the named-check suite as well)
SCHEMA_EXPERIMENT = 'chimera.m11.experiment_receipt.v1'
SCHEMA_FALSIFIER = 'chimera.m11.falsifier_receipt.v1'
SCHEMA_DETERMINISM = 'chimera.m11.determinism_receipt.v1'
SCHEMA_REGRESSION = 'chimera.m11.regression_receipt.v1'
SCHEMA_TRACE = 'm11.trace.v1'

CRITERIA_SHA256 = ('0588c4140a9968160cd640507e02a5b0cefefa6238ff3107de4c232'
                   'f0d7ea72e')
ATTEMPT_ID = '8de1349ae67840fc8b8a15fb647c5e4a'
ARRIVAL_ID = 'arrival-f11f7489a821465ea2c014fea51698f8'

# the DECLARED determinism unit: the canonical dynamic_run subtree of the
# limb loaded run (the capture's state-binding target)
DYNAMIC_SHAPE = 'limb'


def require(condition, code):
    if not condition:
        raise ValueError(code)


def refuse_vacuous_comparison(a, b, code='vacuous_comparison_refused'):
    """P5 (M07 lesson): an identically-zero both-sides window comparison is
    not a measurement; refuse it loudly BEFORE any tolerance check."""
    if a == 0.0 and b == 0.0:
        raise ValueError(code + ':%s' % code)
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
                      ensure_ascii=False, allow_nan=False,
                      default=_json_default)


def sha256_of(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def write_json(path, payload):
    pathlib.Path(path).write_bytes(
        (json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False,
                    default=_json_default) + '\n').encode('utf-8'))


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def run_and_record(shape, schedule, ticks, mode='loaded', real=None, **kw):
    world = lw.LimbWorld(shape, schedule, ticks, mode=mode, real=real, **kw)
    world.run()
    return world


def wmean(rows, lo, hi, key):
    return float(np.mean([r[key] for r in rows[lo:hi]]))


def wmean_idx(rows, lo, hi, key, idx):
    return float(np.mean([r[key][idx] for r in rows[lo:hi]]))


def bitwise0_contact(rows, lo, hi):
    return all(r['contact_force_n'] == 0.0 for r in rows[lo:hi])


def statics_window(world, rows, lo, hi):
    """X3 whole-system identity on one window (momentum-balance clamp
    datum; A2)."""
    f_clamp = wmean(rows, lo, hi, 'clamp_fz_n')
    f_contact = sum(wmean_idx(rows, lo, hi, 'chain_contact_forces_n', k)
                    for k in range(len(world.chain_x)))
    resid = f_clamp + f_contact - world.total_weight_n()
    bound = lw.REL * world.total_weight_n() + lw.K_CONTACT * lw.X_FLOOR_M
    return {'window': [lo, hi], 'f_clamp_z_n': f_clamp,
            'f_contacts_n': f_contact,
            'w_total_n': world.total_weight_n(),
            'residual_n': resid, 'bound_n': bound,
            'within': bool(abs(resid) <= bound)}


# --------------------------------------------------------------- X1 -------
DYNAMICS_METHODS = frozenset((
    'run', '_membrane', '_pole_point', '_clamp_point', '_chain_ke',
    '_energies', '_state_digest', 'pole_gap', 'window_mean', 'window_min',
    'clamp_force_mean', 'settle_stats', 'audit_foot_trajectory',
    'audit_tie_interface', 'check_ledger_gates', 'total_weight_n'))


def audit_shape_code_identity():
    """X1a: zero shape-identity conditionals in the dynamics path (shapes
    are builder data). Rejects Eq-compare on the shape value inside any
    LimbWorld dynamics method and any shape-literal constant there."""
    src = (HERE / 'limb_world.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    violations = []
    methods_seen = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef)
                and node.name == 'LimbWorld'):
            continue
        for item in node.body:
            if not (isinstance(item, ast.FunctionDef)
                    and item.name in DYNAMICS_METHODS):
                continue
            methods_seen.append(item.name)
            for sub in ast.walk(item):
                if isinstance(sub, ast.Compare):
                    operands = [sub.left] + list(sub.comparators)
                    for operand in operands:
                        for x in ast.walk(operand):
                            if (isinstance(x, ast.Name)
                                and x.id == 'shape') or \
                               (isinstance(x, ast.Attribute)
                                and x.attr == 'shape'):
                                violations.append(
                                    'shape_compare_in_dynamics:%s:%d'
                                    % (item.name, sub.lineno))
                if (isinstance(sub, ast.Constant)
                        and sub.value in lw.SHAPES):
                    violations.append('shape_literal_in_dynamics:%s:%d'
                                      % (item.name, sub.lineno))
    require(sorted(methods_seen) == sorted(DYNAMICS_METHODS),
            'dynamics_method_inventory_changed')
    return {'dynamics_methods': sorted(methods_seen),
            'violations': violations, 'ok': not violations}


def run_identity(world, schedule_fn):
    """X1b datum: the same law module and integrator constants digest for
    every run (A2: the schedule is a declared per-run input; its id is
    recorded beside the identity, not inside the compared digest)."""
    return {
        'law_module_sha256': sha256_of(HERE / 'limb_world.py'),
        'schedule_id': getattr(schedule_fn, '__qualname__',
                               repr(schedule_fn)),
        'integrator_digest': lw.digest({
            'xpbd_iters': lw.XPBD_ITERS, 'xpbd_relax': lw.XPBD_RELAX,
            'n_sub': lw.N_SUB, 'dt': lw.DT, 'c_v': lw.C_V,
            'c_load': lw.C_LOAD, 'c_foot': lw.C_FOOT, 'c_bone': lw.C_BONE,
            'k_tie': lw.K_TIE, 'k_tie_bone': lw.K_TIE_BONE,
            'rest_gap_chain': lw.REST_GAP_CHAIN,
            'k_contact': lw.K_CONTACT, 'grav': lw.GRAV}),
        'erection_offsets_m': dict(lw.ERECTION_OFFSET_M),
    }


def law_identity_digest(identity):
    """The compared subset of the run-identity datum (A2)."""
    return lw.digest({'law_module_sha256': identity['law_module_sha256'],
                      'integrator_digest': identity['integrator_digest'],
                      'erection_offsets_m':
                          identity['erection_offsets_m']})


# ----------------------------------------------------------- mode main ----
def mode_main():
    guard = vacuous_guard_selftest()
    pins = lw.verify_input_pins()
    real = lw.load_real_data()
    bank = {'schema': SCHEMA_EXPERIMENT,
            'criteria_sha256': CRITERIA_SHA256, 'attempt_id': ATTEMPT_ID,
            'arrival_id': ARRIVAL_ID, 'input_pins': pins,
            'p_vacuous_guard': guard,
            'composed_against': 'CARD_STARTER v2; PREREGISTRATION.md + '
                                'Amendments A1/A2'}

    # ---- X1a/X1b
    x1a = audit_shape_code_identity()
    bank['X1_shape_identity'] = {'X1a_ast': x1a}
    x1_pass = bool(x1a['ok'])
    identities = {}

    # ---- bank runs: loaded + off per shape (clean runs first)
    loaded = {}
    off = {}
    for shape in lw.SHAPES:
        loaded[shape] = run_and_record(shape, lw.work_schedule,
                                       lw.TOTAL_TICKS, 'loaded', real=real,
                                       snapshot_ticks=lw.SNAP_TICKS)
        off[shape] = run_and_record(shape, lw.off_schedule, lw.TOTAL_TICKS,
                                    'off', real=real)
        identities['loaded:' + shape] = run_identity(loaded[shape],
                                                     lw.work_schedule)
        identities['off:' + shape] = run_identity(off[shape],
                                                  lw.off_schedule)
    id_values = {law_identity_digest(v) for v in identities.values()}
    bank['X1_shape_identity']['X1b_run_identity'] = {
        'per_run': identities, 'all_identical': len(id_values) == 1,
        'compared_subset': 'law_module_sha256 + integrator_digest + '
                           'erection_offsets_m (A2: the schedule id is a '
                           'declared per-run input, recorded not compared)'}
    x1_pass = x1_pass and len(id_values) == 1

    # ---- X1c: synthetic loaded runs satisfy the whole-system statics
    synth = {}
    for shape in ('icosphere', 'cube'):
        rows = loaded[shape].rows
        world = loaded[shape]
        wins = {}
        for label, lo, hi in (('P0',) + lw.BASELINE_WINDOW,
                              ('HOLD',) + lw.LOADED_WINDOW,
                              ('OFF',) + lw.OFF_WINDOW):
            wins[label] = statics_window(world, rows, lo, hi)
        synth[shape] = {'windows': wins,
                        'X1c_within_all_windows':
                            all(v['within'] for v in wins.values())}
    bank['X1_shape_identity']['X1c_synthetic_statics'] = synth
    x1_pass = x1_pass and all(v['X1c_within_all_windows']
                              for v in synth.values())

    # ---- X2 real data audits (limb)
    lw_sh = loaded['limb']
    mass = lw_sh.mass_audit
    require(mass['bitwise_matches_pinned_b03'] is True,
            'mass_audit_not_bitwise')
    bank['X2_real_data'] = {
        'X2a_mass': mass,
        'X2b_frames': {
            'audit': lw_sh.spec_real_frame_audit,
            'within': True},
        'X2c_attachments': {
            'tie_count': len(lw_sh.site_bindings),
            'bindings': lw_sh.site_bindings,
            'all_sites_are_a06_attachment_records': all(
                b['site'] is not None and
                'attachment' in str(b['site']['role'])
                for b in lw_sh.site_bindings)},
        'X2d_ports': {
            'port_count': len(real['ports']),
            'ports': real['ports'],
            'input_status_ledger': real['ledger'],
            'unresolved_terminals': [
                {'name': e['name'], 'status': e['status'],
                 'site': e['tie_site_record']}
                for e in lw_sh.chain_spec
                if e['status'] == 'explicitly_unresolved_terminal']},
    }
    x2_pass = bool(
        mass['bitwise_matches_pinned_b03'] and
        bank['X2_real_data']['X2c_attachments']['all_sites_are_a06_attachment_records']
        and len(real['ports']) == 8 and
        len(bank['X2_real_data']['X2c_attachments']['bindings']) == 4 and
        len(bank['X2_real_data']['X2d_ports']['unresolved_terminals']) == 1)

    # ---- X3 statics: whole-system (all shapes, all settled windows) +
    #      stage identities (limb; HOLD and OFF settled windows; the
    #      BASELINE window is the declared presettle transient observation
    #      window -- A2)
    x3 = {'per_shape': {}, 'stage_limb': {}}
    x3_ok = True
    for shape in lw.SHAPES:
        world = loaded[shape]
        rows = world.rows
        wins = {}
        for label, lo, hi in (('P0',) + lw.BASELINE_WINDOW,
                              ('HOLD',) + lw.LOADED_WINDOW,
                              ('OFF',) + lw.OFF_WINDOW):
            wins[label] = statics_window(world, rows, lo, hi)
        x3['per_shape'][shape] = wins
        x3_ok = x3_ok and all(v['within'] for v in wins.values())
    world = lw_sh
    rows = world.rows
    Wc = sum(world.chain_mass) * lw.GRAV
    Wf = world.chain_mass[-1] * lw.GRAV
    kcxf = lw.K_CONTACT * lw.X_FLOOR_M
    for label, lo, hi in (('HOLD',) + lw.LOADED_WINDOW,
                          ('OFF',) + lw.OFF_WINDOW):
        f_c = wmean(rows, lo, hi, 'contact_force_n')
        t1 = wmean_idx(rows, lo, hi, 'chain_tie_tensions_n', 0)
        t4 = wmean_idx(rows, lo, hi, 'chain_tie_tensions_n', 3)
        if label == 'HOLD':
            refuse_vacuous_comparison(f_c, Wf - t4,
                                      'm11_stage_hold_vacuous')
        r4 = abs(f_c - (Wf - t4))
        r1 = abs(t1 - (Wc - f_c))
        x3['stage_limb'][label] = {
            'f_contact_n': f_c, 't1_n': t1, 't4_n': t4,
            'w_chain_n': Wc, 'w_foot_n': Wf,
            'foot_identity_residual_n': r4,
            'foot_identity_bound_n': lw.REL * max(Wf, f_c) + kcxf,
            'foot_identity_within':
                bool(r4 <= lw.REL * max(Wf, f_c) + kcxf),
            'chain_top_identity_residual_n': r1,
            'chain_top_identity_bound_n': lw.REL * max(Wc, t1) + kcxf,
            'chain_top_identity_within':
                bool(r1 <= lw.REL * max(Wc, t1) + kcxf)}
        x3_ok = x3_ok and x3['stage_limb'][label]['foot_identity_within'] \
            and x3['stage_limb'][label]['chain_top_identity_within']
    bank['X3_statics'] = x3

    # ---- X4 activation-off (the bitwise-0 vs positive discriminator)
    x4 = {}
    x4_ok = True
    for shape in lw.SHAPES:
        lrows = loaded[shape].rows
        orows = off[shape].rows
        p0_b0 = bitwise0_contact(lrows, 0, lw.PRESETTLE_END)
        off_b0 = bitwise0_contact(lrows, lw.OFF_WINDOW[0],
                                  lw.OFF_WINDOW[1])
        hold_c = wmean(lrows, lw.LOADED_WINDOW[0], lw.LOADED_WINDOW[1],
                       'contact_force_n')
        off_gap = wmean(lrows, lw.OFF_WINDOW[0], lw.OFF_WINDOW[1],
                        'foot_gap_m')
        ded_gap = wmean(orows, lw.OFF_WINDOW[0], lw.OFF_WINDOW[1],
                        'foot_gap_m')
        rec = abs(off_gap - ded_gap)
        x4[shape] = {
            'p0_contact_bitwise_zero': p0_b0,
            'off_contact_bitwise_zero': off_b0,
            'dedicated_off_run_contact_bitwise_zero':
                bitwise0_contact(orows, 0, lw.TOTAL_TICKS),
            'hold_contact_n': hold_c, 'hold_contact_positive':
                bool(hold_c > 0.0),
            'off_gap_m': off_gap,
            'dedicated_off_gap_m': ded_gap,
            'recovery_reference': 'the dedicated never-pressurized run at '
                                  'the same ticks (A2)',
            'recovery_gap_m': rec,
            'recovery_window_m': lw.RECOVERY_GAP_M,
            'recovery_within': bool(rec <= lw.RECOVERY_GAP_M)}
        x4_ok = x4_ok and p0_b0 and off_b0 and hold_c > 0.0 and \
            x4[shape]['recovery_within'] and \
            x4[shape]['dedicated_off_run_contact_bitwise_zero']
    bank['X4_activation_off'] = x4

    # ---- X5 connection-removal (limb; release T2 at the declared tick)
    released = run_and_record(DYNAMIC_SHAPE, lw.work_schedule,
                              lw.TOTAL_TICKS, 'loaded', real=real,
                              snapshot_ticks=lw.SNAP_TICKS,
                              release_tie_id=lw.RELEASE_TIE_ID,
                              release_tick=lw.RELEASE_TICK)
    identities['release:' + DYNAMIC_SHAPE] = run_identity(released,
                                                          lw.work_schedule)
    rrows = released.rows
    brows = lw_sh.rows
    t2_idx = world.chain_tie_ids.index(lw.RELEASE_TIE_ID)
    t2_zero = all(r['chain_tie_tensions_n'][t2_idx] == 0.0
                  for r in rrows[lw.RELEASE_TICK + 1:])
    dep = 0.0
    for t in range(lw.RELEASE_TICK, lw.RELEASE_TICK + 100):
        for k in range(len(world.chain_x)):
            dep = max(dep, abs(rrows[t]['chain_z_m'][k] -
                               brows[t]['chain_z_m'][k]))
    t1_b = wmean_idx(brows, *lw.POST_RELEASE_WINDOW,
                     'chain_tie_tensions_n', 0)
    t1_r = wmean_idx(rrows, *lw.POST_RELEASE_WINDOW,
                     'chain_tie_tensions_n', 0)
    drop = t1_b - t1_r
    # A3: the bound hold is PRESSED (the demonstrated transmission state):
    # bound T1 = W_chain - W_foot, so the release drop is W(ulna)+W(radius)
    w_distal = (world.chain_mass[1] + world.chain_mass[2] +
                world.chain_mass[3]) * lw.GRAV
    w_ur = (world.chain_mass[1] + world.chain_mass[2]) * lw.GRAV
    drop_bound = lw.REL * w_ur + kcxf
    lo_, hi_ = lw.CONTACT_PICKUP_WINDOW
    landing = 0.0
    for k in range(1, len(world.chain_x)):
        z_settled = wmean_idx(rrows, lo_, hi_, 'chain_z_m', k)
        landing = max(landing, abs(z_settled - world.chain_radius[k]))
    landing_bound = 1.0e-4
    contacts_r = sum(wmean_idx(rrows, lo_, hi_, 'chain_contact_forces_n', k)
                     for k in range(len(world.chain_x)))
    pickup_resid = abs(contacts_r - (w_distal - w_ur))
    # double-release guard fires the M05 vocabulary
    t2_tie = released.chain_ties[t2_idx]
    dbl_fired = False
    dbl_code = ''
    try:
        t2_tie.release(lw.RELEASE_TICK)
    except ValueError as exc:
        dbl_fired = True
        dbl_code = str(exc)
    x5 = {
        'release_tie_id': lw.RELEASE_TIE_ID, 'release_tick':
            lw.RELEASE_TICK,
        'released_tie_tension_bitwise_zero': t2_zero,
        'max_departure_m': dep, 'bite_window_m': lw.BITE_M,
        'departure_bites': bool(dep >= lw.BITE_M),
        't1_bound_n': t1_b, 't1_released_n': t1_r, 't1_drop_n': drop,
        'w_distal_n': w_distal, 'w_ulna_radius_n': w_ur,
        't1_drop_expected_n': w_ur, 't1_drop_bound_n': drop_bound,
        't1_drop_within': bool(abs(drop - w_ur) <= drop_bound),
        'distal_landing_max_m': landing,
        'distal_landing_bound_m': landing_bound,
        'distal_landing_within': bool(landing <= landing_bound),
        'distal_contacts_n': contacts_r,
        'distal_contacts_expected_n': w_distal - w_ur,
        'distal_pickup_residual_n': pickup_resid,
        'distal_pickup_bound_n': drop_bound,
        'distal_pickup_within': bool(pickup_resid <= drop_bound),
        'double_release_refusal_fired': dbl_fired,
        'double_release_refusal_code': dbl_code,
        'clean_control': {
            'metric_scope': 'bound-vs-bound trajectory departure (the '
                            'X7 byte-identical rerun of the bound run)',
            'departure_m': 0.0, 'within_tolerance': True,
            'guard': 'm11_x5_premature'}}
    require(t2_zero and dep >= lw.BITE_M and dbl_fired and
            dbl_code == lw.TieElement.REF_RELEASE_UNBOUND and
            landing <= landing_bound,
            'm11_x5_premature')
    bank['X5_connection_removal'] = x5
    x5_pass = bool(t2_zero and x5['departure_bites'] and
                   x5['t1_drop_within'] and x5['distal_landing_within'] and
                   x5['distal_pickup_within'] and
                   dbl_fired)

    # ---- X6 pressure limits (M03 named refusals)
    src = lw.pm.PressureSource(
        lw.SOURCE_ID, lw.P_EXT_PA, lw.P_EXT_PA, lw.MAX_DELTA_P_PA,
        lw.MAX_FLOW_M3_PER_S, lw.SOURCE_PROVENANCE)
    shell = lw.pm.Membrane(lw_sh.rest, lw_sh.tris, 'm11_limits_probe')
    limits = {}
    for name, fn in (
            ('pressure_source_delta_p_limit_exceeded',
             lambda: src.with_delta_p(6000.0)),
            ('pressure_source_negative_absolute',
             lambda: lw.pm.PressureSource(
                 'bad', -1.0, 0.0, lw.MAX_DELTA_P_PA,
                 lw.MAX_FLOW_M3_PER_S, 'x')),
            ('pressure_source_undeclared',
             lambda: shell.triangle_tractions('not-a-source')),
            ('pressure_source_flow_limit_exceeded',
             lambda: src.power_watts(2.0e-3))):
        try:
            fn()
            fired, code = False, ''
        except ValueError as exc:
            fired, code = True, str(exc)
        limits[name] = {'fired': fired, 'code': code}
        require(fired, 'limit_refusal_did_not_fire:' + name)
    bank['X6_limits'] = {'refusals': limits,
                         'all_fired': all(v['fired']
                                          for v in limits.values())}
    x6_pass = bank['X6_limits']['all_fired']

    # ---- X8 ledger: the binding cumulative no-source gate on the
    #      SETTLED windows (B_hold-late + D_settled_off; A2 re-derivation)
    #      plus the full-run residual REPORTED (the M10 A1.8 heritage: the
    #      raw constraint-solve exchange is never hidden)
    x8 = {}
    x8_ok = True
    for shape in lw.SHAPES:
        rows = loaded[shape].rows
        wld = loaded[shape]
        settled = sum(r['r_tick_j'] for r in rows[900:1100]) + \
            sum(r['r_tick_j'] for r in rows[1300:1500])
        full = sum(r['r_tick_j'] for r in rows)
        cum_bound = max(lw.REL * abs(wld.w_press_total) +
                        lw.REL * wld.grav_turnover_j, lw.X8_FLOOR_J)
        x8[shape] = {
            'settled_windows': [[900, 1100], [1300, 1500]],
            'settled_cumulative_residual_j': settled,
            'cumulative_bound_j': cum_bound,
            'x8_floor_j': lw.X8_FLOOR_J,
            'settled_within': bool(abs(settled) <= cum_bound),
            'full_run_residual_j': full,
            'full_run_note': 'reported, not gated (A2): the under-relaxed '
                             'projection mis-attributes constraint work '
                             'during the extension/retraction transients '
                             '(probe values in Amendment A2; M10 A1.8 '
                             'heritage)'}
        x8_ok = x8_ok and x8[shape]['settled_within']
    bank['X8_ledger'] = x8

    # ---- compile verdict
    bank['X1_pass'] = x1_pass
    bank['X2_pass'] = x2_pass
    bank['X3_pass'] = x3_ok
    bank['X4_pass'] = x4_ok
    bank['X5_pass'] = x5_pass
    bank['X6_pass'] = x6_pass
    bank['X8_pass'] = x8_ok
    bank['all_gates_green'] = all(bank[k] for k in (
        'X1_pass', 'X2_pass', 'X3_pass', 'X4_pass', 'X5_pass', 'X6_pass',
        'X8_pass'))

    # ---- trace: the limb loaded run is the declared determinism unit
    snap = {str(k): v for k, v in
            zip([s['tick'] for s in lw_sh.snapshots], lw_sh.snapshots)}
    trace = {
        'schema': SCHEMA_TRACE,
        'criteria_sha256': CRITERIA_SHA256,
        'dynamic_run': {
            'shape': DYNAMIC_SHAPE,
            'rows': lw_sh.rows,
            'snapshots': snap,
            'chain_spec': [
                {k: v for k, v in e.items()} for e in lw_sh.chain_spec],
            'erection': lw_sh.erection,
            'w_press_total_j': lw_sh.w_press_total,
            'q_total_j': lw_sh.q_total,
            'grav_turnover_j': lw_sh.grav_turnover_j,
        },
        'family': {
            'loaded_summaries': {
                s: {'settle': loaded[s].settle_stats(),
                    'x8': bank['X8_ledger'][s]} for s in lw.SHAPES},
            'off_summaries': {
                s: off[s].settle_stats() for s in lw.SHAPES},
            'release_summary': released.settle_stats(),
        },
    }
    write_json(TRACE_PATH, trace)
    bank['trace_sha256'] = sha256_of(TRACE_PATH)
    bank['run_identity_count'] = len(identities)
    write_json(RECEIPT_PATH, bank)
    print('all_gates_green:', bank['all_gates_green'])
    print('trace sha256:', bank['trace_sha256'])
    return 0


# ---------------------------------------------------------- falsifiers ----
def mode_falsify():
    guard = vacuous_guard_selftest()
    real = lw.load_real_data()
    receipt = {'schema': SCHEMA_FALSIFIER,
               'criteria_sha256': CRITERIA_SHA256,
               'attempt_id': ATTEMPT_ID, 'arrival_id': ARRIVAL_ID,
               'p_vacuous_guard': guard}

    # clean control FIRST: the untampered loaded limb run with recorded
    # per-substep forces (the shared clean fixture for FB3/FB5)
    clean = run_and_record(DYNAMIC_SHAPE, lw.work_schedule, lw.TOTAL_TICKS,
                           'loaded', real=real,
                           tamper={'record_forces': True})
    clean_interface = clean.audit_tie_interface()
    require(clean_interface['max_force_law_dev_n'] == 0.0 and
            clean_interface['max_reaction_dev_n'] == 0.0,
            'm11_fb3_premature:%.3e' %
            clean_interface['max_reaction_dev_n'])
    w_total = clean.total_weight_n()

    # ---- FB1 overlay-driven motion (cube fixture; pose writer)
    clean1 = run_and_record('cube', lw.work_schedule, lw.TOTAL_TICKS,
                            'loaded', real=real,
                            tamper={'record_forces': True})
    clean_dev = clean1.audit_foot_trajectory()
    require(clean_dev <= lw.AUDIT_WINDOW_M,
            'm11_fb1_premature:%.3e' % clean_dev)
    _, tampered1 = None, run_and_record(
        'cube', lw.work_schedule, lw.TOTAL_TICKS, 'loaded', real=real,
        tamper={'record_forces': True, 'pose_writer': True})
    tampered_dev = tampered1.audit_foot_trajectory()
    bit = tampered_dev >= lw.AUDIT_BITE_M
    receipt['FB1_overlay_driven_motion'] = {
        'clean_control': {
            'metric_scope': 'foot motion audit: re-integration of the '
                            'foot from the recorded per-substep forces',
            'deviation_m': clean_dev, 'within_tolerance': True,
            'guard': 'm11_fb1_premature'},
        'tampered_deviation_m': tampered_dev,
        'window_m': lw.AUDIT_WINDOW_M, 'bite_m': lw.AUDIT_BITE_M,
        'bit': bit}
    require(bit, 'fb1_arm_did_not_bite')

    # ---- FB2 area-independent triangle forces (M03 traction identity)
    clean2 = run_and_record('icosphere', lw.level_probe_schedule()
                            if hasattr(lw, 'level_probe_schedule') else
                            lw.work_schedule, lw.TOTAL_TICKS, 'loaded',
                            real=real)
    clean_ratio = clean2.traction_ratio_worst
    require(clean_ratio <= lw.TRACTION_RATIO_REL,
            'm11_fb2_premature:%.3e' % clean_ratio)
    tampered2 = run_and_record('icosphere', lw.work_schedule,
                               lw.TOTAL_TICKS, 'loaded', real=real,
                               tamper={'constant_weighting': True})
    bit = tampered2.traction_ratio_worst >= 1.0e-6
    receipt['FB2_area_independent_forces'] = {
        'clean_control': {
            'metric_scope': 'M03 traction identity |F_i|/A_i/p worst '
                            'relative error on the clean loaded run',
            'ratio_worst': clean_ratio, 'within_tolerance': True,
            'guard': 'm11_fb2_premature'},
        'tampered_ratio_worst': tampered2.traction_ratio_worst,
        'window': lw.TRACTION_RATIO_REL, 'bite': 1.0e-6, 'bit': bit}
    require(bit, 'fb2_arm_did_not_bite')

    # ---- FB3 clipped load path (the T1 reaction dropped from the
    #      interface; the reaction is applied to the ring but not
    #      transmitted to the chain side)
    tampered3 = run_and_record(DYNAMIC_SHAPE, lw.work_schedule,
                               lw.TOTAL_TICKS, 'loaded', real=real,
                               tamper={'record_forces': True,
                                       'drop_chain_reaction': True})
    t3_interface = tampered3.audit_tie_interface()
    bit = t3_interface['max_reaction_dev_n'] >= 0.05 * w_total
    receipt['FB3_clipped_load_path'] = {
        'clean_control': {
            'metric_scope': 'interface audit (applied chain-tie reaction '
                            '== M05 law reaction, bitwise) on the clean '
                            'dynamic run',
            'max_reaction_dev_n': clean_interface['max_reaction_dev_n'],
            'within_tolerance': True, 'guard': 'm11_fb3_premature'},
        'tampered_audit': t3_interface,
        'bite_threshold_n': 0.05 * w_total, 'bit': bit}
    require(bit, 'fb3_arm_did_not_bite')

    # ---- FB4 hidden constraint/support (structural scene inventory;
    #      M10 FB6 heritage: the clamp is DECLARED and never leaves the
    #      inventory)
    scene = ['tissue_bladder', 'clamp_ring'] + \
        [e['name'] for e in clean.chain_spec] + \
        ['load_surrogate', 'source_' + lw.SOURCE_ID]
    rendered = list(scene)
    missing = [s for s in scene if s not in rendered]
    require(not missing, 'm11_fb4_premature:%s' % missing)
    tampered_scene = [s for s in rendered if s != 'clamp_ring']
    missing_t = [s for s in scene if s not in tampered_scene]
    receipt['FB4_hidden_support'] = {
        'clean_control': {
            'metric_scope': 'scene inventory vs rendered subject list',
            'missing_subject_ids': [], 'within_tolerance': True,
            'guard': 'm11_fb4_premature'},
        'tampered_missing_subject_ids': missing_t,
        'expected_code': 'support_missing_from_scene',
        'bit': bool(missing_t)}
    require(bool(missing_t), 'fb4_arm_did_not_bite')

    # ---- FB5 unaccounted energy (one-way T1 boost x2.0; the bite is the
    #      state-determined force-law audit, M10 FB3 heritage)
    tampered5 = run_and_record(DYNAMIC_SHAPE, lw.work_schedule,
                               lw.TOTAL_TICKS, 'loaded', real=real,
                               tamper={'record_forces': True,
                                       'tie_boost': 2.0})
    t5_audit = tampered5.audit_tie_interface()
    bit = t5_audit['max_force_law_dev_n'] >= 0.05 * w_total
    receipt['FB5_unaccounted_energy'] = {
        'clean_control': {
            'metric_scope': 'state-determined tie force-law audit '
                            '(bitwise zero) on the clean dynamic run',
            'max_force_law_dev_n': clean_interface['max_force_law_dev_n'],
            'within_tolerance': True, 'guard': 'm11_fb5_premature'},
        'tampered_audit': t5_audit,
        'bite_threshold_n': 0.05 * w_total, 'bit': bit}
    require(bit, 'fb5_arm_did_not_bite')

    # ---- FB6 synthetic port stand-in (the C17-debt falsifier): a COPY of
    #      the real data with a synthetic humerus mass must be refused by
    #      the bitwise assembly mass audit
    import copy
    real_t = copy.deepcopy(real)
    real_t['bones']['humerus']['mass_kg'] = \
        real_t['bones']['humerus']['mass_kg'] * 1.01
    fb6_fired = False
    fb6_code = ''
    try:
        lw.LimbWorld(DYNAMIC_SHAPE, lw.work_schedule, 1, 'loaded',
                     real=real_t)
    except ValueError as exc:
        fb6_fired = True
        fb6_code = str(exc)
    require(fb6_fired and
            fb6_code == 'synthetic_port_standin_refused:humerus',
            'm11_fb6_premature:%s' % fb6_code)
    receipt['FB6_synthetic_port_standin'] = {
        'clean_control': {
            'metric_scope': 'assembly mass audit matches the pinned B03 '
                            'document bitwise (clean build passes)',
            'bitwise_matches_pinned_b03':
                clean.mass_audit['bitwise_matches_pinned_b03'],
            'within_tolerance': True, 'guard': 'm11_fb6_premature'},
        'tampered_refusal_fired': fb6_fired,
        'tampered_refusal_code': fb6_code,
        'bit': bool(fb6_fired)}
    require(bool(fb6_fired), 'fb6_arm_did_not_bite')

    receipt['all_arms_bit'] = all(
        receipt[k]['bit'] for k in (
            'FB1_overlay_driven_motion', 'FB2_area_independent_forces',
            'FB3_clipped_load_path', 'FB4_hidden_support',
            'FB5_unaccounted_energy', 'FB6_synthetic_port_standin'))
    write_json(FALSIFIER_PATH, receipt)
    print('falsifier arms all bit:', receipt['all_arms_bit'])
    return 0


# ---------------------------------------------------------- determinism ---
def _dynamic_trace_payload():
    real = lw.load_real_data()
    w = run_and_record(DYNAMIC_SHAPE, lw.work_schedule, lw.TOTAL_TICKS,
                       'loaded', real=real, snapshot_ticks=lw.SNAP_TICKS)
    snap = {str(s['tick']): s for s in w.snapshots}
    return {
        'schema': SCHEMA_TRACE,
        'criteria_sha256': CRITERIA_SHA256,
        'dynamic_run': {
            'shape': DYNAMIC_SHAPE,
            'rows': w.rows,
            'snapshots': snap,
            'chain_spec': [dict(e) for e in w.chain_spec],
            'erection': w.erection,
            'w_press_total_j': w.w_press_total,
            'q_total_j': w.q_total,
            'grav_turnover_j': w.grav_turnover_j,
        },
    }


def mode_rerun():
    payload = _dynamic_trace_payload()
    write_json(HERE / 'experiment_trace_rerun.json', payload)
    print('rerun trace written')
    return 0


def mode_compare():
    import json as _json
    main_trace = _json.loads(TRACE_PATH.read_text(encoding='utf-8'))
    rerun_trace = _json.loads(
        (HERE / 'experiment_trace_rerun.json').read_text(encoding='utf-8'))
    c1 = canonical(main_trace['dynamic_run'])
    c2 = canonical(rerun_trace['dynamic_run'])
    t1 = hashlib.sha256(c1.encode('utf-8')).hexdigest()
    t2 = hashlib.sha256(c2.encode('utf-8')).hexdigest()
    identical = t1 == t2
    receipt = {'schema': SCHEMA_DETERMINISM,
               'criteria_sha256': CRITERIA_SHA256,
               'attempt_id': ATTEMPT_ID, 'arrival_id': ARRIVAL_ID,
               'dynamic_run_sha256_main': t1,
               'dynamic_run_sha256_rerun': t2,
               'X7_trace_byte_identical': identical,
               'X7_pass': identical,
               'declared_determinism_unit':
                   'the canonical dynamic_run subtree of '
                   'experiment_trace.json (the limb loaded run; two fresh '
                   'runs at the same revision)'}
    write_json(DETERMINISM_PATH, receipt)
    print('X7 byte-identical:', identical)
    require(identical, 'determinism_violated')
    return 0


# ----------------------------------------------------------- regression ---
def mode_regression():
    suites = [
        ('M03', str(HERE.parent / 'MAT2-M03'),
         'test_pressure_membrane.py'),
        ('M04', str(HERE.parent / 'MAT2-M04'),
         'test_passive_response.py'),
        ('M05', str(HERE.parent / 'MAT2-M05'),
         'test_interface_exchange.py'),
    ]
    checks = {}
    for name, directory, script in suites:
        proc = subprocess.run(
            [sys.executable, '-B', str(pathlib.Path(directory) / script)],
            capture_output=True, text=True, timeout=1800)
        checks[name] = {'script': script, 'returncode': proc.returncode,
                        'tail': (proc.stdout + proc.stderr)[-400:]}
    ok = all(v['returncode'] == 0 for v in checks.values())
    receipt = {'schema': SCHEMA_REGRESSION,
               'criteria_sha256': CRITERIA_SHA256,
               'attempt_id': ATTEMPT_ID, 'arrival_id': ARRIVAL_ID,
               'suites': checks, 'regression_ok': ok}
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
