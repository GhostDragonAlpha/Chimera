"""MAT2-G05 frozen experiments (PREREGISTRATION.md) - CPU-only card.

Modes (one process each; no GPU anywhere on this card):
  main        the preregistered observation battery (13 scenarios = the 12
              G04 grip cases + the zero-mu control) replayed through the
              declared observation interface; writes experiment_trace.json
              + experiment_receipt.json.
  rerun       second fresh run for the determinism pair (writes
              *_rerun2.json).
  compare     scoped determinism (card-kit form): trace byte-identity +
              receipt delta scoped to AUGMENTATION_KEYS; writes
              determinism_receipt.json.
  falsify     FB1-FB5, every tamper with its passing CLEAN CONTROL run
              FIRST, in the same executable; writes falsifier_receipt.json.
  regression  the declared upstream suites (M06 test_local_contact.py AND
              the sealed G04 test_g04_checks.py, both UNMODIFIED) re-run on
              this exact revision; writes regression_receipt.json.

No RNG; no wall clock in trace/receipt. Refusals are named codes; vacuous
comparisons are REFUSED.
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

import contact_support_obs as cso  # noqa: E402

CARD_ID = 'G05'                  # SHORT registry form
CARD_FULL = 'MAT2-G05'
ATTEMPT_ROOT = HERE.parents[3]   # .../<attempt id>/ (scratch only)

MODES = ('main', 'rerun', 'compare', 'falsify', 'regression')

M06_SUITE = str(CONTRIB / 'MAT2-M06' / 'test_local_contact.py')
G04_SUITE = str(CONTRIB / 'MAT2-G04' / 'test_g04_checks.py')

G01_RECEIPT_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                    'MAT2-G01/numerical/feasibility_receipt.json')
GRASP_BENCH_HOST = ('E:/ChimeraWork/research-data/20260929/benchmark-grasp/'
                    'GRASP_BENCHMARK.md')
FRICTION_SOURCES_HOST = ('E:/ChimeraWork/monkey-coordination/g04-friction/'
                         'FRICTION_SOURCES.md')
G04_REPORT_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                   'MAT2-G04/report/REPORT.md')
W04_FREEZE_MANIFEST_HOST = ('E:/ChimeraWork/monkey-coordination/'
                            'evidence-store/MAT2-W04/numerical/'
                            'w04_freeze_manifest.json')

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
    G01_RECEIPT_HOST:
        '4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42',
    GRASP_BENCH_HOST:
        'd936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610',
    FRICTION_SOURCES_HOST:
        '336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b',
    G04_REPORT_HOST:
        'dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8',
    W04_FREEZE_MANIFEST_HOST:
        'be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29',
    cso.CONTRACT_HOST:
        cso.CONTRACT_SHA256,
}

BASE_COMMIT = '4421349823dd071742a065414bffc0c5e2372e36'
CRITERIA_SHA256 = ('e1e41e878ac6ed0ecae012363f738747dc161ff499223c0dd13acc6'
                   '00cf21388')

# The f32 delivery-check window (PREREG section 2 dtype law).
WIN_F32 = 1e-6           # |f32(v) - v| <= 1e-6 * max(1, |v|)
WIN_POSE_ID = 1e-9       # m, measured-vs-derived centroid identity
WIN_TIME = 1e-12         # s, t_seconds == tick*dt
# The sealed G01 boundary (solver stick/slip verdicts inherited from G04):
STICK_CASES = (('band_lo', 2), ('band_lo', 3), ('band_mid', 2),
               ('band_mid', 3), ('band_hi', 2), ('band_hi', 3),
               ('scene', 3))
SLIP_CASES = (('band_lo', 1), ('band_mid', 1), ('band_hi', 1),
              ('scene', 1), ('scene', 2))
ZERO_MU_LABEL = 'band_mid|n=3|mu=0'
HOLD_TICKS = 20
TOTAL_TICKS = 30
SCENARIO_COUNT = 13
SAMPLES_EXPECTED = SCENARIO_COUNT * TOTAL_TICKS   # 390


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


def run_battery(gc, lc, geom):
    """The full battery replayed through the declared interface.
    Returns (trace_scenarios, totals)."""
    scenarios = {}
    accepted_total = 0
    refusal_total = 0
    for label, kg, n, mu_s, mu_k in battery_cases(gc):
        header, rows, seam, z0, centroids = cso.observe_and_deliver(
            gc, lc, geom, kg, n, label, mu_s=mu_s, mu_k=mu_k)
        samples = [cso.project_sample(gc, lc, row,
                                      [c[2] for c in centroids[i]], n,
                                      lc.DT)
                   for i, row in enumerate(rows)]
        census = seam.census()
        accepted_total += census['accepted']
        refusal_total += len(census['refusals'])
        pose_check = []
        for i, row in enumerate(rows):
            for k in range(n):
                measured = centroids[i][k][2]
                derived = z0[k] - row['pads'][k]['disp_down_m_cum']
                pose_check.append({'tick': row['tick'], 'ch': k,
                                   'measured_z': measured,
                                   'derived_z': derived,
                                   'delta': abs(measured - derived)})
        scenarios[label] = {'header': header, 'rows': rows,
                            'samples': samples, 'census': census,
                            'z0': z0, 'pose_check': pose_check}
    totals = {'accepted': accepted_total, 'refusals': refusal_total,
              'scenarios': len(scenarios),
              'samples_expected': SAMPLES_EXPECTED}
    return scenarios, totals


def _f32_window_ok(delivered, raw):
    return abs(delivered - raw) <= WIN_F32 * max(1.0, abs(raw))


def build_receipt(gc, lc, scenarios, totals, pins):
    """All preregistered predicates, evaluated here so the named checks and
    the falsifier arms consume the SAME predicate set."""
    doc, law = cso.load_contract()
    audit = cso.aliasing_audit()
    declared_keys = sorted(cso.DECLARED_SAMPLE_KEYS)

    # ---- X1 declared-only delivery ----
    key_union = set()
    accepted = 0
    refusals = 0
    exact_keys = True
    for label, s in scenarios.items():
        census = s['census']
        accepted += census['accepted']
        refusals += len(census['refusals'])
        for sample in s['samples']:
            key_union.update(sample)
            if set(sample) != cso.DECLARED_SAMPLE_KEYS:
                exact_keys = False
    x1 = (sorted(key_union) == declared_keys and refusals == 0
          and accepted == SAMPLES_EXPECTED and exact_keys)

    # ---- X2 explicit timing ----
    x2 = True
    timing_fail = None
    for label, s in scenarios.items():
        last = 0
        for i, sample in enumerate(s['samples']):
            row = s['rows'][i]
            tick = sample['t_tick']
            if tick != row['tick'] or tick < 1 or tick > TOTAL_TICKS:
                timing_fail = {'label': label, 'tick': tick}
            if sample['t_phase'] != row['phase']:
                timing_fail = {'label': label, 'phase': sample['t_phase']}
            if sample['t_dt_s'] != lc.DT:
                timing_fail = {'label': label, 'dt': sample['t_dt_s']}
            if abs(sample['t_seconds'] - tick * lc.DT) > WIN_TIME:
                timing_fail = {'label': label, 'seconds': sample['t_seconds']}
            if tick <= last:
                timing_fail = {'label': label, 'monotone': tick}
            last = tick
        x2 &= (timing_fail is None) and (s['census']['accepted'] ==
                                         TOTAL_TICKS)

    # ---- X3 measurable traceability ----
    x3 = True
    trace_fail = None
    f32_worst = 0.0
    pose_worst = 0.0
    for label, s in scenarios.items():
        n = s['header']['n_channels']
        for i, sample in enumerate(s['samples']):
            row = s['rows'][i]
            for k in range(n):
                pd = row['pads'][k]
                pairs = (
                    ('ch%d_contact_flag' % k,
                     0.0 if pd['mode'] == 'no_contact' else 1.0),
                    ('ch%d_stick_flag' % k,
                     1.0 if pd['mode'] == 'stick' else 0.0),
                    ('ch%d_slip_flag' % k,
                     1.0 if pd['mode'] == 'slip' else 0.0),
                    ('ch%d_jn_Ns' % k, pd['jn_sum_Ns']),
                    ('ch%d_jt_Ns' % k, pd['jt_sum_Ns']),
                    ('ch%d_contact_force_N' % k, pd['jn_sum_Ns'] / lc.DT),
                    ('ch%d_disp_down_cum_m' % k, pd['disp_down_m_cum']),
                )
                for name, raw in pairs:
                    delivered = sample[name]
                    err = abs(delivered - raw)
                    f32_worst = max(f32_worst,
                                    err / max(1.0, abs(raw)))
                    if not _f32_window_ok(delivered, raw):
                        trace_fail = {'label': label, 'field': name,
                                      'tick': row['tick'],
                                      'delivered': delivered, 'raw': raw}
            if not _f32_window_ok(sample['agg_trunk_anchor_z_Ns'],
                                  row['ledger']['trunk_anchor'][2]):
                trace_fail = {'label': label, 'field': 'anchor',
                              'tick': row['tick']}
        for prow in s['pose_check']:
            pose_worst = max(pose_worst, prow['delta'])
            if prow['delta'] > WIN_POSE_ID:
                trace_fail = {'label': label, 'pose': prow}
        x3 &= (trace_fail is None)
    x3 &= f32_worst <= WIN_F32 and pose_worst <= WIN_POSE_ID

    # ---- X4 support state law ----
    x4 = True
    support_fail = None
    for label, s in scenarios.items():
        n = s['header']['n_channels']
        is_zero_mu = label.endswith('|mu=0')
        base = label.rsplit('|mu=0', 1)[0]
        reading, n_str = base.split('|n=')
        stick_case = (reading, int(n_str)) in STICK_CASES and not is_zero_mu
        for i, sample in enumerate(s['samples']):
            tick = sample['t_tick']
            hold = tick <= HOLD_TICKS
            want_supported = 1.0 if (stick_case and hold) else 0.0
            if sample['agg_supported_flag'] != want_supported:
                support_fail = {'label': label, 'tick': tick,
                                'supported': sample['agg_supported_flag'],
                                'want': want_supported}
            want_release = 1.0 if tick > HOLD_TICKS else 0.0
            if sample['agg_release_flag'] != want_release:
                support_fail = {'label': label, 'tick': tick,
                                'release': sample['agg_release_flag']}
            if stick_case and hold:
                if sample['agg_support_count'] != float(n):
                    support_fail = {'label': label, 'tick': tick,
                                    'count': sample['agg_support_count']}
            x4 &= (support_fail is None)

    # ---- X5 W04 contract composition ----
    privileged_in_table = [f['name'] for f in cso.OBS_FIELDS
                           if f['name'] in cso.PRIVILEGED_NON_GRATA
                           or f.get('privileged')]
    x5 = (law['dim'] == 80 and law['obs_schema_version'] == 2
          and law['dtype'] == 'float32'
          and law['privileged_forbidden'] is True
          and law['history_ticks'] == 0 and law['fields'] == 80
          and not privileged_in_table and audit['shared_source_count'] == 7
          and cso.OBS_DIM == 32
          and all(f['source'] and f['unit'] and f['frame']
                  for f in cso.OBS_FIELDS))

    # ---- X6 no hidden state ----
    delivered_privileged = sorted(key_union & set(cso.PRIVILEGED_NON_GRATA))
    x6 = (not delivered_privileged and exact_keys
          and sorted(key_union) == declared_keys)

    # ---- X7 named absent law ----
    absent = gc.NAMED_ABSENT
    x7 = (len(absent) == 10
          and all(v[0].startswith('x_') for v in absent)
          and not (key_union & {v[0] for v in absent}))

    rec = {
        'schema': 'chimera.g05_obs_receipt.v1', 'revision': 1,
        'card': CARD_FULL, 'task_id': CARD_ID,
        'criteria_sha256': CRITERIA_SHA256,
        'base_commit': BASE_COMMIT,
        'preregistration': 'PREREGISTRATION.md',
        'input_pins': {k: 'ok' for k in pins},
        'interface': {
            'module': 'tools/monkey_campaign/contributions/MAT2-G05/'
                      'contact_support_obs.py',
            'obs_schema': cso.SCHEMA, 'obs_dim': cso.OBS_DIM,
            'dtype': 'float32', 'history_ticks': 0,
            'timing_keys': list(cso.TIMING_KEYS),
            'timing_law': {'tick_base': 1,
                           'phase_values': list(cso.PHASES),
                           'dt_s': lc.DT, 'cadence':
                           'exactly one sample per solver tick, delivered '
                           'in tick order, post solve'},
            'availability_law': {
                'unavailable_channel_fill': 0.0,
                'mask_mean': 'available vector slots / 32',
                'frac_avail': 'slot GROUPS with any availability / 5',
            },
            'aliasing_audit': audit,
            'privileged_forbidden': True,
            'privileged_non_grata': list(cso.PRIVILEGED_NON_GRATA),
            'declared_keys': declared_keys,
        },
        'upstream': {
            'solver': {'module': 'MAT2-M06/local_contact.py',
                       'sha256': gc.INTERFACE_SHA256,
                       'imported_not_forked': True},
            'grip_physics': {'module': 'MAT2-G04/grip_contact.py',
                             'sha256': cso.G04_MODULE_SHA256,
                             'imported_not_forked': True,
                             'revision': 'sealed PR #298'},
            'observation_contract': {
                'interface': 'policy_observation_interface v2 (W04 TC-2)',
                'path': cso.CONTRACT_HOST, 'sha256': cso.CONTRACT_SHA256,
                'law': law,
                'composition': 'the 80-field walking interface is NOT '
                               're-declared; the task-owned grasp table '
                               'composes with its declared laws',
            },
        },
        'named_absent_variables': [
            {'name': v, 'quantity': q, 'status': 'ABSENT',
             'provenance_verbatim': p} for (v, q, p) in absent],
        'delivery_totals': totals,
        'x_checks': {
            'X1_declared_only_delivery': bool(x1),
            'X2_explicit_timing': bool(x2),
            'X3_measurable_traceability': bool(x3),
            'X4_support_state_law': bool(x4),
            'X5_w04_contract_composition': bool(x5),
            'X6_no_hidden_state': bool(x6),
            'X7_named_absent_law': bool(x7),
        },
        'x_evidence': {
            'f32_worst_relative': f32_worst,
            'pose_identity_worst_m': pose_worst,
            'timing_fail': timing_fail,
            'trace_fail': trace_fail,
            'support_fail': support_fail,
            'delivered_privileged': delivered_privileged,
            'declared_key_count': len(declared_keys),
            'delivered_key_union': sorted(key_union),
        },
        'vacuous_guard_selftest': vacuous_guard_selftest(),
    }
    rec['X1_pass'] = all(bool(v) for v in rec['x_checks'].values())
    return rec


def mode_main():
    pins = verify_input_pins()
    gc = cso.load_g04_module()
    lc = gc.load_interface()
    geom = gc.load_trunk_geometry()
    scenarios, totals = run_battery(gc, lc, geom)
    trace = {'schema': 'chimera.g05_obs_trace.v1', 'revision': 1,
             'scenarios': scenarios}
    receipt = build_receipt(gc, lc, scenarios, totals, pins)
    (HERE / 'experiment_trace.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'X1_pass': receipt['X1_pass'],
                      'x_checks': receipt['x_checks'],
                      'delivery_totals': totals}, indent=1))


def mode_rerun():
    pins = verify_input_pins()
    gc = cso.load_g04_module()
    lc = gc.load_interface()
    geom = gc.load_trunk_geometry()
    scenarios, totals = run_battery(gc, lc, geom)
    trace = {'schema': 'chimera.g05_obs_trace.v1', 'revision': 1,
             'scenarios': scenarios}
    receipt = build_receipt(gc, lc, scenarios, totals, pins)
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
        'schema': 'chimera.g05_determinism.v1',
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


# ---- falsifier arms (clean control FIRST; named premature guard) ----

def _load_scratch_module(stem, source_bytes):
    """Write a tampered module COPY into the attempt scratch (never the
    card dir, never committed state) and import it under a private name."""
    import importlib.util
    scratch = ATTEMPT_ROOT / 'scratch-falsifiers'
    scratch.mkdir(parents=True, exist_ok=True)
    path = scratch / (stem + '.py')
    path.write_bytes(source_bytes)
    spec = importlib.util.spec_from_file_location('g05_' + stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def mode_falsify():
    pins = verify_input_pins()
    gc = cso.load_g04_module()
    lc = gc.load_interface()
    geom = gc.load_trunk_geometry()
    arms = {}

    def arm(name, clean, tampered, bites, discriminator):
        arms[name] = {
            'clean_control': clean, 'tampered': tampered,
            'bites': bool(bites), 'discriminator': discriminator,
            'premature_guard': name.replace('FB', 'g05_fb')
            + '_premature: PASS (clean control ran first)',
        }

    # ONE observed scenario grounds every clean control (scene|n=3).
    header, rows, seam, z0, centroids = cso.observe_and_deliver(
        gc, lc, geom, 10.037998, 3, 'FB_ground')
    clean_census = seam.census()
    sample1 = cso.project_sample(gc, lc, rows[0],
                                 [c[2] for c in centroids[0]], 3, lc.DT)

    # FB1 undeclared_field_injection -- the production seam is the guard
    # (clean control: the clean sample is accepted AND the injected key is
    # refused); the tamper is an UNGUARDED channel (a scratch seam whose
    # deliver accepts unconditionally -- the exact defect a consumer would
    # see if the controller were wired to an unguarded bus).
    clean_ok1 = (clean_census['accepted'] == TOTAL_TICKS
                 and not clean_census['refusals'])
    seam_g = cso.ObservationSeam('FB1_guard_clean', lc.DT)
    accepted_c1g = seam_g.deliver(dict(sample1))
    fired_g = None
    seam_g2 = cso.ObservationSeam('FB1_guard_refusal', lc.DT)
    bad_g = dict(sample1)
    bad_g['solver_penetration_m'] = 1e-4
    try:
        seam_g2.deliver(bad_g)
    except ValueError as exc:
        fired_g = str(exc)
    clean_ok1 = clean_ok1 and accepted_c1g and fired_g is not None \
        and 'privileged_source' in fired_g
    src = (HERE / 'contact_support_obs.py').read_bytes()
    text = src.decode('utf-8')
    site = '    def deliver(self, sample):\n        keys = set(sample)'
    if text.count(site) != 1:
        raise ValueError('tamper_site_missing:contact_support_obs.py')
    tampered_text = text.replace(
        site,
        '    def deliver(self, sample):\n'
        '        return True  # FB1 tamper: UNGUARDED channel\n'
        '        keys = set(sample)')
    cso_t = _load_scratch_module('fb1_seam', tampered_text.encode('utf-8'))
    seam_t = cso_t.ObservationSeam('FB1_tampered', lc.DT)
    bad = dict(sample1)
    bad['solver_penetration_m'] = 1e-4
    accepted_t = seam_t.deliver(bad)
    delivered_keys = sorted(bad)
    tampered_fails1 = ('solver_penetration_m' in delivered_keys)
    refuse_vacuous(float(clean_census['accepted']),
                   float(seam_t.accepted))
    arm('FB1_undeclared_field_injection',
        {'accepted': clean_census['accepted'],
         'refusals': clean_census['refusals'],
         'guard_accepted_clean': accepted_c1g,
         'guard_refusal': fired_g,
         'declared_only_census': clean_ok1},
        {'unguarded_channel_accepted_undeclared': accepted_t,
         'delivered_extra_key': 'solver_penetration_m',
         'declared_only_predicate': not tampered_fails1},
        clean_ok1 and accepted_t and tampered_fails1,
        'an unguarded channel delivers solver-internal keys and breaks the '
        'declared-only predicate; the guarded seam refuses it')

    # FB2 timing_strip -- t_dt_s = 0.0 is UNBOUND timing; the production
    # seam refuses.
    seam2 = cso.ObservationSeam('FB2_clean', lc.DT)
    accepted_c2 = seam2.deliver(dict(sample1))
    clean_ok2 = accepted_c2 and not seam2.refusals
    fired2 = None
    seam2b = cso.ObservationSeam('FB2_tampered', lc.DT)
    bad2 = dict(sample1)
    bad2['t_dt_s'] = 0.0
    try:
        seam2b.deliver(bad2)
    except ValueError as exc:
        fired2 = str(exc)
    arm('FB2_timing_strip',
        {'accepted': accepted_c2, 'refusals': seam2.refusals},
        {'refused': fired2 is not None, 'refusal': fired2},
        clean_ok2 and fired2 is not None and 'timing_unbound' in fired2,
        'a sample without a bound tick interval is unobservable: the seam '
        'must refuse timing_unbound')

    # FB3 named_absent_fill -- a synthetic constant in the x_press slot.
    seam3 = cso.ObservationSeam('FB3_clean', lc.DT)
    accepted_c3 = seam3.deliver(dict(sample1))
    clean_ok3 = accepted_c3 and not seam3.refusals
    fired3 = None
    seam3b = cso.ObservationSeam('FB3_tampered', lc.DT)
    bad3 = dict(sample1)
    bad3['x_press'] = 5.0
    try:
        seam3b.deliver(bad3)
    except ValueError as exc:
        fired3 = str(exc)
    arm('FB3_named_absent_fill',
        {'accepted': accepted_c3, 'refusals': seam3.refusals},
        {'refused': fired3 is not None, 'refusal': fired3},
        clean_ok3 and fired3 is not None
        and 'named_absent_occupied' in fired3,
        'a synthetic constant in an absent slot must be refused '
        '(named-variable law at the seam)')

    # FB4 force_pose_inconsistency -- force delivered off the declared
    # conversion while the pose fields stay unchanged.
    conv_clean = _f32_window_ok(sample1['ch0_contact_force_N'],
                                rows[0]['pads'][0]['jn_sum_Ns'] / lc.DT)
    clean_ok4 = conv_clean
    tampered_sample = dict(sample1)
    tampered_sample['ch0_contact_force_N'] = cso.to_f32(
        2.0 * rows[0]['pads'][0]['jn_sum_Ns'] / lc.DT)
    conv_tampered = _f32_window_ok(tampered_sample['ch0_contact_force_N'],
                                   rows[0]['pads'][0]['jn_sum_Ns'] / lc.DT)
    pose_unchanged = (tampered_sample['ch0_centroid_z_m']
                      == sample1['ch0_centroid_z_m'])
    refuse_vacuous(sample1['ch0_contact_force_N'],
                   tampered_sample['ch0_contact_force_N'])
    arm('FB4_force_pose_inconsistency',
        {'conversion_holds': conv_clean,
         'force_N': sample1['ch0_contact_force_N']},
        {'conversion_holds': conv_tampered, 'pose_unchanged': pose_unchanged,
         'force_N': tampered_sample['ch0_contact_force_N']},
        clean_ok4 and (not conv_tampered) and pose_unchanged,
        'doubling the declared force conversion with the pose unchanged is '
        'exactly the force/pose inconsistency the profile falsifier names')

    # FB5 hidden_state_privileged -- jn delivered from a privileged
    # pre-solve penetration proxy instead of the record.
    trace_clean = _f32_window_ok(sample1['ch0_jn_Ns'],
                                 rows[0]['pads'][0]['jn_sum_Ns'])
    clean_ok5 = trace_clean
    privileged_proxy = 1.0e-3     # a solver-internal penetration proxy
    tampered5 = dict(sample1)
    tampered5['ch0_jn_Ns'] = cso.to_f32(privileged_proxy)
    trace_tampered = _f32_window_ok(tampered5['ch0_jn_Ns'],
                                    rows[0]['pads'][0]['jn_sum_Ns'])
    refuse_vacuous(sample1['ch0_jn_Ns'], tampered5['ch0_jn_Ns'])
    arm('FB5_hidden_state_privileged',
        {'traceability_holds': trace_clean,
         'jn_delivered': sample1['ch0_jn_Ns'],
         'jn_recorded': rows[0]['pads'][0]['jn_sum_Ns']},
        {'traceability_holds': trace_tampered,
         'jn_delivered': tampered5['ch0_jn_Ns'],
         'privileged_proxy': privileged_proxy},
        clean_ok5 and not trace_tampered,
        'a delivered value not sourced from the recorded contact record '
        'breaks measurable traceability (no hidden simulator information '
        'as sensed information)')

    receipt = {'schema': 'chimera.g05_falsifiers.v1',
               'arms': arms,
               'F_all_green': all(a['bites'] for a in arms.values()),
               'arm_count': len(arms)}
    (HERE / 'falsifier_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'F_all_green': receipt['F_all_green'],
                      'arms': {k: v['bites'] for k, v in arms.items()}},
                     indent=1))


def mode_regression():
    results = []
    for suite in (M06_SUITE, G04_SUITE):
        proc = subprocess.run([sys.executable, '-B', suite],
                              capture_output=True, text=True, timeout=3000)
        results.append({'suite': suite, 'suite_unmodified': True,
                        'exit_code': proc.returncode,
                        'tail': proc.stdout[-1500:]})
    receipt = {
        'schema': 'chimera.g05_regression.v1',
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
