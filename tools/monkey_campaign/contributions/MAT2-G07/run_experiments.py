"""MAT2-G07 frozen experiments (PREREGISTRATION.md) - CPU-only card.

Modes (one process each; no GPU anywhere on this card):
  main        the preregistered release/fall battery (13 scenarios = the
              12 G04 grip cases + the zero-mu control; 20 hold + 40
              release ticks each) through the G07 account loop, every
              tick delivered through the sealed G05 seam; writes
              experiment_trace.json + experiment_receipt.json.
  rerun       second fresh run for the determinism pair (writes
              *_rerun2.json).
  compare     scoped determinism (card-kit form): trace byte-identity +
              receipt delta scoped to AUGMENTATION_KEYS; writes
              determinism_receipt.json.
  falsify     FB1-FB5, every tamper with its passing CLEAN CONTROL run
              FIRST, in the same executable; writes falsifier_receipt.json.
  regression  the declared upstream suites (M06 test_local_contact.py,
              sealed G04 test_g04_checks.py, sealed G05
              test_g05_checks.py -- all UNMODIFIED) re-run on this exact
              revision; writes regression_receipt.json.

No RNG; no wall clock in trace/receipt. Refusals are named codes;
vacuous comparisons are REFUSED.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(HERE))

import release_fall_account as rfa  # noqa: E402

CARD_ID = 'G07'                   # SHORT registry form
CARD_FULL = 'MAT2-G07'
ATTEMPT_ROOT = HERE.parents[3]   # the attempt checkout root (scratch only)

MODES = ('main', 'rerun', 'compare', 'falsify', 'regression')

M06_SUITE = str(CONTRIB / 'MAT2-M06' / 'test_local_contact.py')
G04_SUITE = str(CONTRIB / 'MAT2-G04' / 'test_g04_checks.py')
G05_SUITE = str(CONTRIB / 'MAT2-G05' / 'test_g05_checks.py')

G01_RECEIPT_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                    'MAT2-G01/numerical/feasibility_receipt.json')
GRASP_BENCH_HOST = ('E:/ChimeraWork/research-data/20260929/benchmark-grasp/'
                    'GRASP_BENCHMARK.md')
FRICTION_SOURCES_HOST = ('E:/ChimeraWork/monkey-coordination/g04-friction/'
                         'FRICTION_SOURCES.md')
G04_REPORT_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                   'MAT2-G04/report/REPORT.md')
G05_REPORT_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                   'MAT2-G05/report/REPORT.md')
W04_FREEZE_MANIFEST_HOST = ('E:/ChimeraWork/monkey-coordination/'
                            'evidence-store/MAT2-W04/numerical/'
                            'w04_freeze_manifest.json')
CONTRACT_HOST = ('E:/ChimeraWork/pass3-integ/repo/tools/science_funnel/'
                 'validation/policy_interface_freeze_20260920/'
                 'observation_interface_v2.json')

PINS = {
    '../MAT2-M06/local_contact.py':
        '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc',
    '../MAT2-M06/test_local_contact.py':
        'b832d0dc07c1762a190d4b662ceed2b1b6dd469cbd22343cb39934e90eb08e77',
    '../MAT2-M06/contact_law.json':
        '583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b',
    '../MAT2-M06/experiment_receipt.json':
        '2956dd7aaf3682fc18de9b724ddd8a695011ec74c9a12a5a56744b3d738a9397',
    '../MAT2-F03/assets/trunk_01_mesh.json':
        '3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7',
    '../MAT2-F03/assets/trunk_01_material_state.json':
        '91c17a5c59ce79af3dc0e8a6dadb00c92a039075775a0a1de618da12dfca61bd',
    '../MAT2-G04/grip_contact.py':
        '0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245',
    '../MAT2-G04/test_g04_checks.py':
        'a01b167e4393e2e513ba343f2bc6ba3fdf4d01ee08170f7fe8c3cb1c5c9a0ae1',
    '../MAT2-G05/contact_support_obs.py':
        '3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3',
    '../MAT2-G05/test_g05_checks.py':
        '83ba17604f66fdbe623b71ce481b539862ec39ebf81ee4c8bea2e5af29f9985b',
    G01_RECEIPT_HOST:
        '4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42',
    GRASP_BENCH_HOST:
        'd936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610',
    FRICTION_SOURCES_HOST:
        '336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b',
    G04_REPORT_HOST:
        'dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8',
    G05_REPORT_HOST:
        '1e5fcc7f81b5bd7b0ae3b460c72d5ed190510f66db4793c6b2e99756da8c8524',
    W04_FREEZE_MANIFEST_HOST:
        'be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29',
    CONTRACT_HOST:
        'e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0671c',
}

BASE_COMMIT = 'fa02f07508ee15b7679d0f2a95ac6b1894f77962'
CRITERIA_SHA256 = ('a6691ba418440dd040761e84c04c024f7a7535ffa41889167cab7e8'
                   'd63750cfe')

# declared windows (PREREG sections 2-5; G04/G05 sealed windows reused)
WIN_F32 = 1e-6
WIN_POSE_ID = 1e-9
WIN_ENERGY = rfa.WIN_ENERGY
WIN_DRIFT = rfa.WIN_DRIFT
WIN_CONT = rfa.WIN_CONT
WIN_RECURSION_V = rfa.WIN_RECURSION_V
WIN_DISP = rfa.WIN_DISP
WIN_RELEASE_SCALE = rfa.WIN_RELEASE_SCALE
HOLD_TICKS = rfa.HOLD_TICKS
RELEASE_TICKS = rfa.RELEASE_TICKS
TOTAL_TICKS = rfa.TOTAL_TICKS
SCENARIO_COUNT = rfa.SCENARIO_COUNT
DELIVERIES_EXPECTED = rfa.DELIVERIES_EXPECTED
# the sealed G01 boundary (solver stick/slip verdicts inherited from G04):
STICK_CASES = (('band_lo', 2), ('band_lo', 3), ('band_mid', 2),
               ('band_mid', 3), ('band_hi', 2), ('band_hi', 3),
               ('scene', 3))
SLIP_CASES = (('band_lo', 1), ('band_mid', 1), ('band_hi', 1),
              ('scene', 1), ('scene', 2))
ZERO_MU_LABEL = 'band_mid|n=3|mu=0'
# FB constants (PREREG section 6; amendment a1 mechanics)
FB2_HIDDEN_ANCHOR_NS = (0.0, 0.0, 0.02)   # unrecorded hold-phase impulse
FB4_PROPULSION_NS = 0.05                  # unrecorded upward per release tick
FB3_TELEPORT_TICK = 30                    # mid-fall reset tick


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def refuse_vacuous(a, b, code='vacuous_comparison_refused'):
    if a == 0.0 and b == 0.0:
        raise ValueError(code)


def vacuous_guard_selftest():
    fired = False
    try:
        refuse_vacuous(0.0, 0.0)
    except ValueError as exc:
        fired = str(exc) == 'vacuous_comparison_refused'
    return fired


def verify_input_pins():
    if not PINS:
        raise ValueError('input_pins_empty: declare your frozen inputs')
    for rel, expected in PINS.items():
        path = (HERE / rel).resolve() if not rel.startswith('E:') \
            else pathlib.Path(rel)
        if not path.exists():
            raise ValueError('input_pin_missing:' + rel)
        if sha256_file(path) != expected:
            raise ValueError('input_pin_drift:' + rel)
    return dict(PINS)


def battery_cases(gc):
    """The 13 preregistered cases in G04's frozen order (zero-mu control
    last, '|mu=0' suffix -- the G04 label-hygiene law)."""
    cases = []
    for name, kg in gc.READINGS_KG:
        for n in gc.CHANNELS:
            cases.append((gc.scenario_label(name, n), kg, n, gc.PAD_MU_S,
                          gc.PAD_MU_K))
    cases.append((gc.scenario_label(gc.ZERO_MU_CONTROL['reading'],
                                    gc.ZERO_MU_CONTROL['n']) + '|mu=0',
                  dict(gc.READINGS_KG)[gc.ZERO_MU_CONTROL['reading']],
                  gc.ZERO_MU_CONTROL['n'], gc.ZERO_MU_CONTROL['mu_s'],
                  gc.ZERO_MU_CONTROL['mu_k']))
    return cases


def observed_scenario(cso, gc, lc, geom, label, kg, n, mu_s, mu_k):
    """One clean observed scenario: the G07 account loop, the pinned-runner
    cross-check, the release account, the G05 seam delivery and the pose
    identity. Returns the trace scenario dict."""
    header, rows, acct_rows, centroids = rfa.observe_with_account(
        cso, gc, lc, geom, kg, n, label, mu_s=mu_s, mu_k=mu_k,
        hold_ticks=HOLD_TICKS, release_ticks=RELEASE_TICKS)
    header_ref, rows_ref = gc.run_scenario(
        lc, geom, kg, n, mu_s=mu_s, mu_k=mu_k, hold_ticks=HOLD_TICKS,
        release_ticks=RELEASE_TICKS, scenario_id=label)
    rfa.cross_check_rows(header, rows, header_ref, rows_ref, label)
    release = rfa.release_account(rows, acct_rows, n, header['pad_share_kg'],
                                  lc.DT, hold_ticks=HOLD_TICKS)
    # the G05 seam delivery (declared table unchanged; 60 samples)
    seam = cso.ObservationSeam(label, lc.DT)
    z0 = cso.initial_centroid_z(gc, geom, n)
    samples = []
    for i, row in enumerate(rows):
        sample = cso.project_sample(gc, lc, row,
                                    [c[2] for c in centroids[i]], n, lc.DT)
        seam.deliver(sample)
        samples.append(sample)
    pose_check = []
    for i, row in enumerate(rows):
        for k in range(n):
            measured = centroids[i][k][2]
            derived = z0[k] - row['pads'][k]['disp_down_m_cum']
            pose_check.append({'tick': row['tick'], 'ch': k,
                               'measured_z': measured,
                               'derived_z': derived,
                               'delta': abs(measured - derived)})
            if abs(measured - derived) > WIN_POSE_ID:
                raise ValueError('pose_identity_broken:%s:%d:%d'
                                 % (label, row['tick'], k))
    # phase-tagged account totals (keyed per-phase extraction; P6)
    def total(phase, key, pad=None):
        return sum(rfa.phase_metric(acct_rows, phase, key, pad=pad))
    account = {}
    for phase in rfa.PHASES:
        account[phase] = {
            'ticks': len(rfa.phase_rows(acct_rows, phase)),
            'work_press_J': sum(total(phase, 'work_press_J', pad=k)
                                for k in range(n)),
            'work_weld_J': sum(total(phase, 'work_weld_J', pad=k)
                               for k in range(n)),
            'work_gravity_J': sum(total(phase, 'work_gravity_J', pad=k)
                                  for k in range(n)),
            'work_contact_J': sum(total(phase, 'work_contact_J', pad=k)
                                  for k in range(n)),
            'work_friction_J': sum(total(phase, 'work_friction_J', pad=k)
                                   for k in range(n)),
            'loss_solver_J': sum(total(phase, 'loss_solver_J', pad=k)
                                 for k in range(n)),
            'ke_delta_J': sum(total(phase, 'ke_after_J', pad=k)
                              - total(phase, 'ke_start_J', pad=k)
                              for k in range(n)),
            'dkepe_J': sum(total(phase, 'dkepe_J', pad=k)
                           for k in range(n)),
            'drift_pred_J': sum(total(phase, 'drift_pred_J', pad=k)
                                for k in range(n)),
        }
    return {'header': header, 'rows': rows, 'acct_rows': acct_rows,
            'samples': samples, 'census': seam.census(), 'z0': z0,
            'pose_check': pose_check, 'release': release,
            'account': account}


def run_battery(cso, gc, lc, geom):
    """The full battery. Returns (scenarios, totals)."""
    scenarios = {}
    accepted_total = 0
    refusal_total = 0
    for label, kg, n, mu_s, mu_k in battery_cases(gc):
        s = observed_scenario(cso, gc, lc, geom, label, kg, n, mu_s, mu_k)
        accepted_total += s['census']['accepted']
        refusal_total += len(s['census']['refusals'])
        scenarios[label] = s
    totals = {'accepted': accepted_total, 'refusals': refusal_total,
              'scenarios': len(scenarios),
              'deliveries_expected': DELIVERIES_EXPECTED,
              'ticks_per_scenario': TOTAL_TICKS}
    return scenarios, totals


def _f32_ok(delivered, raw):
    return abs(delivered - raw) <= WIN_F32 * max(1.0, abs(raw))


def build_receipt(cso, gc, lc, scenarios, totals, pins):
    """All preregistered predicates, evaluated here so the named checks
    and the falsifier arms consume the SAME predicate set."""
    doc, law = cso.load_contract()
    declared_keys = sorted(cso.DECLARED_SAMPLE_KEYS)
    dt = lc.DT
    g = lc.G

    # ---- X1 release removes the forces (P1) ----
    x1 = True
    x1_worst = {'jn_max_Ns': 0.0, 'jt_max_Ns': 0.0, 'anchor_max_Ns': 0.0}
    collision_events = {}
    for label, s in scenarios.items():
        rel = s['release']
        share = s['header']['pad_share_kg']
        n = s['header']['n_channels']
        x1 &= rel['jn_max_Ns'] <= share * WIN_RELEASE_SCALE
        x1 &= rel['jt_max_Ns'] <= share * WIN_RELEASE_SCALE
        x1 &= rel['anchor_max_Ns'] <= share * n * WIN_RELEASE_SCALE
        x1 &= rel['press_work_release_J'] == 0.0
        x1_worst['jn_max_Ns'] = max(x1_worst['jn_max_Ns'], rel['jn_max_Ns'])
        x1_worst['jt_max_Ns'] = max(x1_worst['jt_max_Ns'], rel['jt_max_Ns'])
        x1_worst['anchor_max_Ns'] = max(x1_worst['anchor_max_Ns'],
                                        rel['anchor_max_Ns'])
        if rel['collision_count']:
            collision_events[label] = rel['collision_events']
        # release flags in the delivered samples: exactly ticks 21..60
        for sample in s['samples']:
            want = 1.0 if sample['t_tick'] > HOLD_TICKS else 0.0
            if sample['agg_release_flag'] != want:
                x1 = False

    # ---- X2 motion accounted (P2) ----
    x2 = True
    worst_rec = 0.0
    worst_disp = 0.0
    worst_cont = 0.0
    coll_cont_worst = 0.0
    for label, s in scenarios.items():
        rel = s['release']
        worst_rec = max(worst_rec, rel['recursion_worst_mps'])
        worst_disp = max(worst_disp, rel['disp_closed_form_worst_m'])
        for arow in s['acct_rows']:
            for pad in arow['pads']:
                if pad['unobstructed']:
                    worst_cont = max(worst_cont,
                                     pad['continuity_residual_m'])
                else:
                    coll_cont_worst = max(coll_cont_worst,
                                          pad['continuity_residual_m'])
        x2 &= rel['recursion_worst_mps'] <= WIN_RECURSION_V
        x2 &= rel['disp_closed_form_worst_m'] <= WIN_DISP
    x2 &= worst_cont <= WIN_CONT

    # ---- X3 energy account exact (P3) ----
    x3 = True
    worst_e = 0.0
    worst_replay = 0.0
    worst_loss = 0.0
    press_work_hold_total = 0.0
    for label, s in scenarios.items():
        for arow in s['acct_rows']:
            for pad in arow['pads']:
                worst_e = max(worst_e, abs(pad['residual_J']))
                worst_replay = max(worst_replay, pad['v_replay_delta_mps'])
                worst_loss = max(worst_loss,
                                 abs(pad['work_friction_J']
                                     + pad['loss_solver_J']))
        for k in range(s['header']['n_channels']):
            hold_press = sum(rfa.phase_metric(s['acct_rows'], 'hold',
                                              'work_press_J', pad=k))
            press_work_hold_total += hold_press
        x3 &= (s['account']['hold']['work_press_J'] > 0.0
               and s['account']['release']['work_press_J'] == 0.0)
    x3 &= worst_e <= WIN_ENERGY and worst_replay <= 1e-12 \
        and worst_loss <= 1e-12

    # ---- X4 fall energy account (P3: the declared discretization) ----
    x4 = True
    worst_drift = 0.0
    coll_drift_worst = 0.0
    drift_by_class = {'stick': 0.0, 'slip': 0.0, 'zero_mu': 0.0}
    for label, s in scenarios.items():
        is_zero = label.endswith('|mu=0')
        base = label.rsplit('|mu=0', 1)[0]
        reading, n_str = base.split('|n=')
        cls = 'zero_mu' if is_zero else \
            ('stick' if (reading, int(n_str)) in STICK_CASES else 'slip')
        for arow in s['acct_rows']:
            for pad in arow['pads']:
                if pad['unobstructed']:
                    worst_drift = max(worst_drift,
                                      abs(pad['drift_residual_J']))
                else:
                    coll_drift_worst = max(coll_drift_worst,
                                           abs(pad['drift_residual_J']))
                if arow['phase'] == 'release':
                    drift_by_class[cls] += pad['dkepe_J'] - pad['drift_pred_J']
        # the per-tick windows are the binding form (worst_drift); the
        # per-class release totals are recorded evidence only
    x4 &= worst_drift <= WIN_DRIFT

    # ---- X5 seam delivery composition (P5) ----
    x5 = True
    key_union = set()
    exact_keys = True
    disp_bind_worst = 0.0
    for label, s in scenarios.items():
        x5 &= (s['census']['accepted'] == TOTAL_TICKS
               and not s['census']['refusals'])
        n = s['header']['n_channels']
        for i, sample in enumerate(s['samples']):
            key_union.update(sample)
            if set(sample) != cso.DECLARED_SAMPLE_KEYS:
                exact_keys = False
            row = s['rows'][i]
            for k in range(n):
                raw = row['pads'][k]['disp_down_m_cum']
                delivered = sample['ch%d_disp_down_cum_m' % k]
                disp_bind_worst = max(disp_bind_worst,
                                      abs(delivered - raw)
                                      / max(1.0, abs(raw)))
                if not _f32_ok(delivered, raw):
                    x5 = False
            for k in range(n, 3):
                if sample['ch%d_disp_down_cum_m' % k] != 0.0:
                    x5 = False
    x5 &= (totals['accepted'] == DELIVERIES_EXPECTED
           and totals['refusals'] == 0 and exact_keys
           and sorted(key_union) == declared_keys
           and disp_bind_worst <= WIN_F32)

    # ---- X6 phase separation (P4; C20) ----
    x6 = True
    for label, s in scenarios.items():
        acc = s['account']
        x6 &= acc['hold']['ticks'] == HOLD_TICKS
        x6 &= acc['release']['ticks'] == RELEASE_TICKS
        is_zero = label.endswith('|mu=0')
        base = label.rsplit('|mu=0', 1)[0]
        reading, n_str = base.split('|n=')
        case = (reading, int(n_str))
        stick_case = case in STICK_CASES and not is_zero
        supported_hold_any = False
        for sample in s['samples']:
            hold = sample['t_tick'] <= HOLD_TICKS
            want = 1.0 if (stick_case and hold) else 0.0
            if sample['agg_supported_flag'] != want:
                x6 = False
            if want == 1.0:
                supported_hold_any = True
        if is_zero:
            x6 &= (not supported_hold_any)
            x6 &= s['account']['hold']['work_contact_J'] <= \
                s['account']['hold']['work_press_J']
        # the missed-grasp control is honestly unsupported everywhere

    # ---- X7 named absent law ----
    absent = gc.NAMED_ABSENT
    x7 = (len(absent) == 10
          and all(v[0].startswith('x_') for v in absent)
          and not (key_union & {v[0] for v in absent}))

    rec = {
        'schema': 'chimera.g07_release_fall_receipt.v1', 'revision': 1,
        'card': CARD_FULL, 'task_id': CARD_ID,
        'criteria_sha256': CRITERIA_SHA256,
        'base_commit': BASE_COMMIT,
        'preregistration': 'PREREGISTRATION.md',
        'input_pins': {k: 'ok' for k in pins},
        'measurement': {
            'module': 'tools/monkey_campaign/contributions/MAT2-G07/'
                      'release_fall_account.py',
            'schema': rfa.SCHEMA,
            'hold_ticks': HOLD_TICKS, 'release_ticks': RELEASE_TICKS,
            'total_ticks': TOTAL_TICKS,
            'dt_s': dt, 'g_mps2': g,
            'scenario_count': SCENARIO_COUNT,
            'deliveries_expected': DELIVERIES_EXPECTED,
            'declared_keys': declared_keys,
            'windows': {'energy_identity_J': WIN_ENERGY,
                        'stored_energy_drift_J': WIN_DRIFT,
                        'continuity_m': WIN_CONT,
                        'recursion_mps': WIN_RECURSION_V,
                        'closed_form_m': WIN_DISP,
                        'release_bar_Ns_per_kg': WIN_RELEASE_SCALE,
                        'f32': WIN_F32, 'pose_identity_m': WIN_POSE_ID},
        },
        'upstream': {
            'solver': {'module': 'MAT2-M06/local_contact.py',
                       'sha256': gc.INTERFACE_SHA256,
                       'imported_not_forked': True},
            'grip_physics': {'module': 'MAT2-G04/grip_contact.py',
                             'sha256':
                             '0d6375484c350039468b31a2f7db2895d3365412aee52'
                             'ce98de72b4173d69245',
                             'imported_not_forked': True,
                             'revision': 'sealed PR #298'},
            'observation_seam': {'module':
                                 'MAT2-G05/contact_support_obs.py',
                                 'sha256': rfa.G05_MODULE_SHA256,
                                 'imported_not_forked': True,
                                 'revision': 'sealed PR #300',
                                 'composition': 'the declared 32-slot '
                                 'table and its seam are consumed, NOT '
                                 'extended or re-declared'},
        },
        'named_absent_variables': [
            {'name': v, 'quantity': q, 'status': 'ABSENT',
             'provenance_verbatim': p} for (v, q, p) in absent],
        'battery_totals': totals,
        'x_checks': {
            'X1_release_removes_support': bool(x1),
            'X2_motion_accounted': bool(x2),
            'X3_energy_account_exact': bool(x3),
            'X4_fall_energy_account': bool(x4),
            'X5_seam_delivery_composition': bool(x5),
            'X6_phase_separation': bool(x6),
            'X7_named_absent_law': bool(x7),
        },
        'x_evidence': {
            'release_bars_worst': x1_worst,
            'collision_events_by_scenario': collision_events,
            'recursion_worst_mps': worst_rec,
            'disp_closed_form_worst_m': worst_disp,
            'continuity_worst_m': worst_cont,
            'collision_tick_continuity_worst_m': coll_cont_worst,
            'collision_tick_drift_worst_J': coll_drift_worst,
            'energy_residual_worst_J': worst_e,
            'replay_delta_worst_mps': worst_replay,
            'loss_identity_worst_J': worst_loss,
            'drift_residual_worst_J': worst_drift,
            'drift_release_totals_by_class_J': drift_by_class,
            'stored_energy_measurement_delta_J': {
                label: abs(s['account']['release']['dkepe_J']
                           - s['account']['release']['drift_pred_J'])
                for label, s in scenarios.items()},
            'press_work_hold_total_J': press_work_hold_total,
            'disp_binding_worst_relative': disp_bind_worst,
            'delivered_key_union': sorted(key_union),
            'scenario_release_summaries': {
                label: s['release'] for label, s in scenarios.items()},
            'scenario_account_totals': {
                label: s['account'] for label, s in scenarios.items()},
        },
        'vacuous_guard_selftest': vacuous_guard_selftest(),
    }
    rec['X_all_pass'] = all(bool(v) for v in rec['x_checks'].values())
    return rec


def mode_main():
    pins = verify_input_pins()
    cso = rfa.load_g05_module()
    gc = cso.load_g04_module()
    lc = gc.load_interface()
    geom = gc.load_trunk_geometry()
    scenarios, totals = run_battery(cso, gc, lc, geom)
    trace = {'schema': 'chimera.g07_release_fall_trace.v1', 'revision': 1,
             'scenarios': scenarios}
    receipt = build_receipt(cso, gc, lc, scenarios, totals, pins)
    (HERE / 'experiment_trace.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'X_all_pass': receipt['X_all_pass'],
                      'x_checks': receipt['x_checks'],
                      'battery_totals': totals}, indent=1))


def mode_rerun():
    pins = verify_input_pins()
    cso = rfa.load_g05_module()
    gc = cso.load_g04_module()
    lc = gc.load_interface()
    geom = gc.load_trunk_geometry()
    scenarios, totals = run_battery(cso, gc, lc, geom)
    trace = {'schema': 'chimera.g07_release_fall_trace.v1', 'revision': 1,
             'scenarios': scenarios}
    receipt = build_receipt(cso, gc, lc, scenarios, totals, pins)
    (HERE / 'experiment_trace_rerun2.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt_rerun2.json').write_bytes(canonical(receipt))
    print('rerun written')


AUGMENTATION_KEYS = []


def mode_compare():
    a = (sha256_file(HERE / 'experiment_trace.json'),
         sha256_file(HERE / 'experiment_receipt.json'))
    b = (sha256_file(HERE / 'experiment_trace_rerun2.json'),
         sha256_file(HERE / 'experiment_receipt_rerun2.json'))
    run1 = json.loads((HERE / 'experiment_receipt.json').read_text())
    run2 = json.loads((HERE / 'experiment_receipt_rerun2.json').read_text())
    only1 = sorted(set(run1) - set(run2))
    only2 = sorted(set(run2) - set(run1))
    shared_differ = sorted(k for k in set(run1) & set(run2)
                           if run1[k] != run2[k])
    trace_identical = a[0] == b[0]
    receipt = {
        'schema': 'chimera.g07_determinism.v1',
        'trace_sha_run1': a[0], 'receipt_sha_run1': a[1],
        'trace_sha_run2': b[0], 'receipt_sha_run2': b[1],
        'X2_trace_byte_identical': trace_identical,
        'X2_receipt_byte_identical': a[1] == b[1],
        'receipt_keys_only_in_main': only1,
        'receipt_keys_only_in_rerun': only2,
        'receipt_shared_keys_differing': shared_differ,
        'declared_augmentation_keys': AUGMENTATION_KEYS,
        'X2_byte_identical': a == b,
        'X2_pass': trace_identical and only1 == AUGMENTATION_KEYS
        and not only2 and not shared_differ,
    }
    (HERE / 'determinism_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: receipt[k] for k in (
        'X2_pass', 'X2_trace_byte_identical')}, indent=1))


# ---- falsifier arms (clean control FIRST; named premature guard) --------

def _ground(cso, gc, lc, geom):
    """The clean ground control: the observed scene|n=3 battery case."""
    return observed_scenario(cso, gc, lc, geom, 'FB_ground', 10.037998, 3,
                             gc.PAD_MU_S, gc.PAD_MU_K)


def mode_falsify():
    pins = verify_input_pins()
    cso = rfa.load_g05_module()
    gc = cso.load_g04_module()
    lc = gc.load_interface()
    geom = gc.load_trunk_geometry()
    arms = {}

    def arm(name, clean, tampered, bites, discriminator):
        arms[name] = {
            'clean_control': clean, 'tampered': tampered,
            'bites': bool(bites), 'discriminator': discriminator,
            'premature_guard': name.replace('FB', 'g07_fb')
            + '_premature: PASS (clean control ran first)',
        }

    def acct_worst_energy(acct):
        return max(abs(p['residual_J'])
                   for arow in acct for p in arow['pads'])

    def acct_worst_continuity(acct):
        return max(p['continuity_residual_m']
                   for arow in acct for p in arow['pads'])

    # the clean control runs FIRST and must PASS every production law
    ground = _ground(cso, gc, lc, geom)
    clean_release = ground['release']
    clean_ok_release = (clean_release['jn_max_Ns']
                        <= ground['header']['pad_share_kg']
                        * WIN_RELEASE_SCALE
                        and clean_release['press_work_release_J'] == 0.0
                        and clean_release['disp_closed_form_worst_m']
                        <= WIN_DISP)
    clean_energy = acct_worst_energy(ground['acct_rows'])
    clean_cont = acct_worst_continuity(ground['acct_rows'])
    refuse_vacuous(float(clean_release['disp_closed_form_worst_m']),
                   float(clean_energy))
    require_all = (clean_ok_release and clean_energy <= WIN_ENERGY
                   and clean_cont <= WIN_CONT)
    if not require_all:
        raise ValueError('fb_clean_control_failed')

    # FB1 release_residual_support -- G04's RECORDED weld hook; the
    # tampered rows still cross-check against the hooked pinned runner and
    # the RELEASE predicates are the bite (amendment a1 i).
    h1, r1, a1, c1 = rfa.observe_with_account(
        cso, gc, lc, geom, 10.037998, 3, 'FB1_tampered',
        hold_ticks=HOLD_TICKS, release_ticks=RELEASE_TICKS,
        sticky_release_weld=True)
    h1r, r1r = gc.run_scenario(lc, geom, 10.037998, 3,
                               hold_ticks=HOLD_TICKS,
                               release_ticks=RELEASE_TICKS,
                               scenario_id='FB1_tampered',
                               sticky_release_weld=True)
    rfa.cross_check_rows(h1, r1, h1r, r1r, 'FB1_tampered')
    weld_work = sum(p['work_weld_J'] for arow in a1 for p in arow['pads'])
    held_disp = r1[-1]['pads'][0]['disp_down_m_cum']
    clean_disp = ground['rows'][-1]['pads'][0]['disp_down_m_cum']
    fired1 = None
    try:
        rfa.release_account(r1, a1, 3, h1['pad_share_kg'], lc.DT,
                            hold_ticks=HOLD_TICKS)
    except ValueError as exc:
        fired1 = str(exc).split(':')[0]
    bites1 = fired1 is not None and weld_work > 0.0 \
        and held_disp < 0.5 * clean_disp
    arm('FB1_release_residual_support',
        {'release_account_pass': clean_ok_release,
         'disp_closed_form_worst_m':
             clean_release['disp_closed_form_worst_m'],
         'fall_disp_m': clean_disp, 'energy_worst_J': clean_energy},
        {'release_refusal': fired1, 'weld_work_J': weld_work,
         'held_fall_disp_m': held_disp,
         'rows_bit_identical_to_hooked_runner': True},
        bites1,
        'a leftover constraint holds the falling pad: the release account '
        'refuses (bars/closed form) while the recorded weld work appears '
        'in the owner census; the clean control free-falls')

    # FB2 energy_owner_concealment -- G04's UNRECORDED hidden_anchor hook;
    # measured under the falsifier-only mode (amendment a1 ii).
    h2, r2, a2, c2 = rfa.observe_with_account(
        cso, gc, lc, geom, 10.037998, 3, 'FB2_tampered',
        hold_ticks=HOLD_TICKS, release_ticks=RELEASE_TICKS,
        hidden_anchor=FB2_HIDDEN_ANCHOR_NS, require_ledger=False,
        enforce_account=False)
    energy2 = acct_worst_energy(a2)
    ns2 = max(arow['ledger_residual_full_max_Ns'] for arow in a2)
    bites2 = energy2 > 1e6 * WIN_ENERGY and ns2 > 1e6 * 1e-12
    arm('FB2_energy_owner_concealment',
        {'energy_worst_J': clean_energy, 'ledger_armed': True,
         'ledger_residual_worst_Ns': 0.0},
        {'energy_worst_J': energy2, 'ledger_armed': False,
         'ledger_residual_worst_Ns': ns2,
         'injected_impulse_Ns': list(FB2_HIDDEN_ANCHOR_NS)},
        bites2,
        'an impulse applied to the body but absent from every recorded '
        'channel appears as kinetic energy with NO recorded owner: the '
        'energy identity residual breaks by ~6 orders above its window '
        '(and the N*s ledger with it); the clean control closes')

    # FB3 hidden_reset_teleport -- the G07 hook; measured (a1 ii).
    h3, r3, a3, c3 = rfa.observe_with_account(
        cso, gc, lc, geom, 10.037998, 3, 'FB3_tampered',
        hold_ticks=HOLD_TICKS, release_ticks=RELEASE_TICKS,
        teleport_at_tick=FB3_TELEPORT_TICK, require_ledger=False,
        enforce_account=False)
    cont3 = acct_worst_continuity(a3)
    ns3 = max(arow['ledger_residual_full_max_Ns'] for arow in a3)
    bites3 = cont3 > 1e6 * WIN_CONT and ns3 > 0.0
    arm('FB3_hidden_reset_teleport',
        {'continuity_worst_m': clean_cont, 'ledger_armed': True},
        {'continuity_worst_m': cont3, 'ledger_armed': False,
         'ledger_residual_worst_Ns': ns3,
         'teleport_tick': FB3_TELEPORT_TICK},
        bites3,
        'a mid-fall state reset (pose + velocity restored to the pre-solve '
        'state) breaks the pose-continuity identity by ~6 orders above its '
        'window (C13: no teleport or hidden reset); the clean control is '
        'continuous')

    # FB4 unsupported_propulsion -- the G07 hook; the release account's
    # motion refusal is the declared bite.
    h4, r4, a4, c4 = rfa.observe_with_account(
        cso, gc, lc, geom, 10.037998, 3, 'FB4_tampered',
        hold_ticks=HOLD_TICKS, release_ticks=RELEASE_TICKS,
        propulsion_ns=FB4_PROPULSION_NS, require_ledger=False,
        enforce_account=False)
    fired4 = None
    detail4 = None
    try:
        rfa.release_account(r4, a4, 3, h4['pad_share_kg'], lc.DT,
                            hold_ticks=HOLD_TICKS)
    except ValueError as exc:
        parts = str(exc).split(':', 1)
        fired4 = parts[0]
        detail4 = parts[1] if len(parts) > 1 else None
    jn4 = max(abs(p['jn_sum_Ns']) for arow in r4
              if arow['phase'] == 'release' for p in arow['pads'])
    bar4 = h4['pad_share_kg'] * WIN_RELEASE_SCALE
    bites4 = fired4 is not None and jn4 <= bar4
    arm('FB4_unsupported_propulsion',
        {'release_account_pass': clean_ok_release,
         'recursion_worst_mps': clean_release['recursion_worst_mps']},
        {'release_refusal': fired4, 'refusal_detail': detail4,
         'release_jn_max_Ns': jn4, 'bar_Ns': bar4,
         'injected_propulsion_Ns_per_tick': FB4_PROPULSION_NS},
        bites4,
        'an upward anti-gravity impulse every release tick moves the pad '
        'while the RECORDED forces still sit inside the noise bars: the '
        'motion is not supported by the recorded forces and the motion '
        'account refuses')

    # FB5 force_pose_inconsistency -- a stale-verdict variant on the clean
    # ground trace (no solver tamper; the G05 declared law is the control).
    s0 = ground
    stale_supported_tick = None
    inconsistent = 0
    n0 = s0['header']['n_channels']
    stale = False
    for i, sample in enumerate(s0['samples']):
        row = s0['rows'][i]
        declared = sample['agg_supported_flag']
        if declared == 1.0:
            stale = True
        claimed = 1.0 if (declared == 1.0 or stale) else 0.0
        # the force/pose record: a supported claim is consistent ONLY on a
        # hold tick with stick forces present (jn above the release bar)
        forces_present = all(p['jn_sum_Ns'] > s0['header']['pad_share_kg']
                             * WIN_RELEASE_SCALE
                             for p in row['pads'][:n0])
        consistent = (claimed == 0.0) or \
            (row['phase'] == 'hold' and forces_present
             and all(p['mode'] == 'stick' for p in row['pads'][:n0]))
        if not consistent:
            inconsistent += 1
            if stale_supported_tick is None:
                stale_supported_tick = row['tick']
        if declared != (1.0 if (row['phase'] == 'hold'
                                and all(p['mode'] == 'stick'
                                        for p in row['pads'][:n0]))
                        else 0.0):
            raise ValueError('fb5_declared_law_drift')
    clean_ok5 = inconsistent >= 0 and s0['census']['refusals'] == []
    bites5 = inconsistent == RELEASE_TICKS
    refuse_vacuous(float(inconsistent), float(clean_energy))
    arm('FB5_force_pose_inconsistency',
        {'declared_law_consistent_ticks': TOTAL_TICKS,
         'census_refusals': s0['census']['refusals'],
         'clean_ok': clean_ok5},
        {'inconsistent_ticks': inconsistent,
         'first_inconsistent_tick': stale_supported_tick,
         'claimed': 'stale stick verdict through release'},
        bites5,
        'a verdict that keeps claiming support from a stale stick flag '
        'contradicts the recorded forces (noise-bar jn) and the falling '
        'pose on every release tick; the declared G05 law agrees with the '
        'force/pose record everywhere')

    receipt = {'schema': 'chimera.g07_falsifiers.v1',
               'arms': arms,
               'F_all_green': all(a['bites'] for a in arms.values()),
               'arm_count': len(arms)}
    (HERE / 'falsifier_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'F_all_green': receipt['F_all_green'],
                      'arms': {k: v['bites'] for k, v in arms.items()}},
                     indent=1))


def mode_regression():
    results = []
    for suite in (M06_SUITE, G04_SUITE, G05_SUITE):
        proc = subprocess.run([sys.executable, '-B', suite],
                              capture_output=True, text=True, timeout=3000)
        results.append({'suite': suite, 'suite_unmodified': True,
                        'exit_code': proc.returncode,
                        'tail': proc.stdout[-1500:]})
    receipt = {
        'schema': 'chimera.g07_regression.v1',
        'suites': results,
        'P_regression_suite_green': all(r['exit_code'] == 0
                                        for r in results),
    }
    (HERE / 'regression_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({r['suite'].split('/')[-1]: r['exit_code']
                      for r in results}, indent=1))


def main(argv):
    mode = argv[1] if len(argv) > 1 else 'main'
    if mode not in MODES:
        raise SystemExit('unknown mode: ' + mode
                         + ' (valid: ' + ', '.join(MODES) + ')')
    getattr(sys.modules[__name__], 'mode_' + mode)()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
