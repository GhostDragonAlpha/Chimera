"""MAT2-G08 frozen experiments (PREREGISTRATION.md + amendment a1, frozen)
- CPU-only card.

Modes (one process each; no GPU anywhere on this card):
  main        the composed qualification battery: the sealed G06 transfer
              battery (9 runs x 229 ticks) + the sealed G07 release/fall
              battery (13 runs x 60 ticks) in ONE deterministic process,
              with the union ledger, identity bindings, continuity, event
              localization, reference math, seam union and the numerical
              budget; writes experiment_trace.json + experiment_receipt.json.
  rerun       second fresh run for the determinism pair (writes
              *_rerun2.json).
  compare     scoped determinism (card-kit form): trace byte-identity +
              receipt delta scoped to AUGMENTATION_KEYS; writes
              determinism_receipt.json.
  falsify     FB1-FB5, every tamper with its passing CLEAN CONTROL run
              FIRST, in the same executable; writes falsifier_receipt.json.
  regression  the declared upstream suites (M06, G04, G05, G06, G07, G01;
              all UNMODIFIED) re-run on this exact revision; writes
              regression_receipt.json. F05 is data-bound (prereg section
              11); its non-execution and reason are recorded here.

No RNG; no wall clock in trace/receipt. Refusals are named codes (prereg
section 13); vacuous comparisons are REFUSED.
"""
from __future__ import annotations

import g08_deps  # noqa: E402  (must run before upstream imports)

g08_deps.ensure()

import hashlib  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402
import subprocess  # noqa: E402
import sqlite3  # noqa: E402
import sys  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(HERE))

import assembly_line as al  # noqa: E402

require = al.require
canonical = al.canonical
sha256_file = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()  # noqa: E731

CARD_ID = 'G08'                  # SHORT registry form
CARD_FULL = 'MAT2-G08'
ATTEMPT_ID = '1b58946be29847c681b41f9c5a15861b'
AGENT_ID = 'wk-g08-arrival-1'
MODES = ('main', 'rerun', 'compare', 'falsify', 'regression')
AUGMENTATION_KEYS = []

M06_SUITE = CONTRIB / 'MAT2-M06' / 'test_local_contact.py'
G04_SUITE = CONTRIB / 'MAT2-G04' / 'test_g04_checks.py'
G05_SUITE = CONTRIB / 'MAT2-G05' / 'test_g05_checks.py'
G06_SUITE = CONTRIB / 'MAT2-G06' / 'test_g06_checks.py'
G07_SUITE = CONTRIB / 'MAT2-G07' / 'test_g07_checks.py'
G01_SUITE = CONTRIB / 'MAT2-G01' / 'test_g01_checks.py'
REGISTRY_SQLITE = pathlib.Path(
    'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3')

# the composed story (prereg section 12)
T_STORY_SCENARIO = al.T_STORY_SCENARIO
T_STORY_TICKS = al.T_STORY_TICKS
R_STORY_SCENARIO = al.R_STORY_SCENARIO
R_STORY_TICK = al.R_STORY_TICK


def refuse_vacuous(a, b, code='vacuous_comparison_refused'):
    require(a != b or a is not None, code, (a, b))


def vacuous_guard_selftest():
    fired = False
    try:
        refuse_vacuous(None, None)
    except ValueError:
        fired = True
    require(fired, 'vacuous_guard_selftest_failed', None)
    return True


def registry_criteria_sha256():
    """Read-ONLY single-query registry extraction (house gate; never
    hand-copied)."""
    con = sqlite3.connect('file:%s?mode=ro' % REGISTRY_SQLITE.as_posix(),
                          uri=True)
    try:
        cur = con.cursor()
        cur.execute('SELECT payload FROM state WHERE id=1')
        state = json.loads(cur.fetchone()[0])
    finally:
        con.close()
    card = state['kanban']['cards'][CARD_FULL]
    return card['criteria_sha256']


def verify_input_pins():
    host = g08_deps.verify_host_pins()
    pins = {'host': host, 'repo_base': g08_deps.DEFAULT_BASE,
            'prereg_commits': list(al.PREREG_COMMITS)}
    return pins


def run_battery():
    """The composed battery (prereg section 4). Returns (mods, t_recs,
    r_recs, t_cache)."""
    gc, lc, g05, ts, rfa = al.load_pinned_modules()
    geom = gc.load_trunk_geometry()
    al.matter_identity(gc)
    t_recs, t_cache = [], {}
    for label, kg, n, mu_s, mu_k in al.transfer_cases(ts):
        story = (al.T_STORY_TICKS if label == al.T_STORY_SCENARIO else ())
        rec, header, rows = al.run_transfer_case(
            gc, lc, g05, ts, geom, label, kg, n, mu_s=mu_s, mu_k=mu_k,
            story_ticks=story)
        t_recs.append(rec)
        t_cache[label] = (header, rows)
    r_recs = []
    for label, kg, n, mu_s, mu_k in al.release_cases(gc):
        story = (al.R_STORY_TICKS if label == al.R_STORY_SCENARIO else ())
        rec = al.run_release_case(gc, lc, g05, ts, rfa, geom, label, kg, n,
                                  mu_s, mu_k, story_ticks=story)
        r_recs.append(rec)
    return (gc, lc, g05, ts, rfa, geom), t_recs, r_recs, t_cache


def build_receipt(mods, t_recs, r_recs, t_cache, pins):
    gc, lc, g05, ts, rfa, geom = mods
    g06_receipt = al.load_pinned_json(al.G06_PINNED_RECEIPT_REL,
                                      al.G06_PINNED_RECEIPT_SHA256)
    g06_trace = al.load_pinned_json(al.G06_PINNED_TRACE_REL,
                                    al.G06_PINNED_TRACE_SHA256)
    g07_receipt = al.load_pinned_json(al.G07_PINNED_RECEIPT_REL,
                                      al.G07_PINNED_RECEIPT_SHA256)
    g07_trace = al.load_pinned_json(al.G07_PINNED_TRACE_REL,
                                    al.G07_PINNED_TRACE_SHA256)

    identity_t = [al.identity_t(rec, g06_trace, g06_receipt)
                  for rec in t_recs]
    identity_r = [al.identity_r(rec, g07_trace) for rec in r_recs]
    a1_ok = all(b['identity_ok'] for b in identity_t) and \
        all(b['identity_ok'] for b in identity_r)

    ledger = al.union_ledger(t_recs, r_recs)
    cert_ticks = 9 * 229 + 13 * 60
    require(ledger['total_ticks'] == cert_ticks,
            'unsupported_state_unexplained:ledger_short',
            (ledger['total_ticks'], cert_ticks))
    a4_ok = (ledger['response_classes']['declared_release'] +
             ledger['response_classes']['declared_establishing'] +
             ledger['response_classes']['declared_solver_slip'] +
             ledger['response_classes']['declared_flight_hover']) == \
        ledger['unsupported']

    cont = al.continuity_t(lc, ts, t_cache)
    # amendment a1(ii): bind the assembled flight worst to the certified
    # G06 x_evidence.flight_worst_non_event_m inside 1e-9 absolute
    cont['certified_m'] = g06_receipt['x_evidence'][
        'flight_worst_non_event_m']
    cont['measured_minus_certified_m'] = (cont['worst_m']
                                          - cont['certified_m'])
    cont['composition_bind_ok'] = (abs(cont['measured_minus_certified_m'])
                                   <= al.COMPOSITION_BIND)
    if not cont['composition_bind_ok']:
        raise ValueError('identity_binding_mismatch:flight_worst',
                         {'measured': cont['worst_m'],
                          'certified': cont['certified_m']})
    a5_ok = cont['ok'] and cont['composition_bind_ok']

    events = al.event_localization(t_recs, r_recs)
    a6_ok = (events['t_handover_ticks'] == [31]
             and events['t_reattach_ticks'] == [193]
             and events['t_release_start_ticks'] == [220]
             and events['r_release_flip_ticks'] == [21])

    refmath = al.reference_math(gc, lc, ts, t_recs, t_cache, g06_receipt)
    a7_ok = refmath['reference_math_ok']

    seam = al.seam_union(t_recs, r_recs, g06_receipt, g07_receipt)
    a8_ok = seam['ok']

    budget = al.numerical_budget(t_recs, r_recs, t_cache, ts, rfa, lc)
    a9_ok = budget['budget_ok']

    receipt = {
        'schema': 'chimera.g08_assembly_receipt.v1',
        'revision': 1,
        'card': CARD_FULL,
        'task_id': CARD_ID,
        'base_commit': al.BASE_COMMIT,
        'prereg_commits': list(al.PREREG_COMMITS),
        'criteria_sha256': al.CRITERIA_SHA256,
        'criteria_registry_match': registry_criteria_sha256()
        == al.CRITERIA_SHA256,
        'vacuous_guard_selftest': vacuous_guard_selftest(),
        'input_pins': pins,
        'matter_identity': al.matter_identity(gc),
        'battery': {
            't_scenarios': [r['label'] for r in t_recs],
            'r_scenarios': [r['label'] for r in r_recs],
            't_ticks_each': 229, 'r_ticks_each': 60,
            'total_ticks': ledger['total_ticks'],
        },
        'A1_line_identity': a1_ok,
        'A1_evidence': {'t': identity_t, 'r': identity_r},
        'A2_transfer_envelope': a1_ok and all(
            b['verdict_ok'] for b in identity_t),
        'A3_release_and_fall': a1_ok and all(
            b['identity_ok'] for b in identity_r),
        'A4_unsupported_ledger': a4_ok,
        'A4_evidence': ledger,
        'A5_continuity': a5_ok,
        'A5_evidence': cont,
        'A6_event_localization': a6_ok,
        'A6_evidence': events,
        'A7_reference_math': a7_ok,
        'A7_evidence': refmath,
        'A8_seam_union': a8_ok,
        'A8_evidence': seam,
        'A9_numerical_budget': a9_ok,
        'A9_evidence': budget,
        'A10_determinism_binding': 'determinism_receipt.json (mode_compare;'
                                   ' boolean enforced by test_g08_checks)',
        'p_class': p_class_block(gc, lc, g05, ts, t_recs, r_recs),
        'inventory': inventory_block(),
        'named_absent_variables': [
            {'name': entry[0], 'quantity': entry[1],
             'provenance_verbatim': entry[2]}
            for entry in gc.NAMED_ABSENT],
        'preregistration': 'PREREGISTRATION.md',
    }
    require(receipt['criteria_registry_match'], 'prereg_identity_mismatch',
            None)
    return receipt


def p_class_block(gc, lc, g05, ts, t_recs, r_recs):
    """Seam law + named-variable law + prereg identity evidence."""
    story_rec = None
    for rec in t_recs:
        if rec['label'] == al.T_STORY_SCENARIO and rec['story']:
            story_rec = rec
            break
    keys = sorted(story_rec['story'][list(story_rec['story'])[0]]
                  ['sample'].keys())
    return {
        'declared_sample_key_count': len(keys),
        'x_namespace_delivered': [k for k in keys if k.startswith('x_')],
        'named_absent_carried': 'verbatim gc.NAMED_ABSENT (G04 inheritance;'
                                ' the receipt carries the list)',
    }


def inventory_block():
    """The CPU/GPU and runtime identity inventory (prereg section 10)."""
    return {
        'cpu_identity_gates_certified_here': [
            'deterministic re-execution identity (byte-level line identity'
            ' vs the certified lines)',
            'full-tick impulse ledger + reciprocity + visible anchor',
            'energy/work account + friction split + replay',
            'event localization (handover/reattach/release/CCD)',
            'reference-math composition (record-g vs standard-g; jn/DT)',
            'mutation controls (FB1-FB5)',
            'upstream suite regression (M06, G04, G05, G06, G07, G01)',
        ],
        'gpu_device_leg_climb_contact_parity': {
            'status': 'UNRESOLVED',
            'reason': 'no certified owner on the sealed line; the certified'
                      ' GPU line (M08-M12) covers material/actuator/limb/'
                      'LOD worlds, not the trunk/pad climb fixture; this'
                      ' card is CPU-only by runner law; the GPU queue owns'
                      ' this future work; INVENTORIED, never claimed',
        },
        'engine_device_leg_anchors': {
            'status': 'OUT_OF_SCOPE',
            'reason': 'W03 freefall/stand/C1/C2 anchors are their own lane;'
                      ' CPU evidence is structurally not device proof '
                      '(W03 law)',
        },
        'c05_joint_kinematics': {
            'status': 'ABSENT',
            'reason': 'no joints exist in this fixture; inventoried, never'
                      ' faked',
        },
        'c06_articulated_chain': {
            'status': 'ABSENT',
            'reason': 'fixture pads + trunk only; the pinned M06 solver '
                      'ledger carries the fixture-level force accounting',
        },
    }


def mode_main():
    pins = verify_input_pins()
    mods, t_recs, r_recs, t_cache = run_battery()
    receipt = build_receipt(mods, t_recs, r_recs, t_cache, pins)
    trace = {
        'schema': 'chimera.g08_assembly_trace.v1', 'revision': 1,
        'base_commit': al.BASE_COMMIT,
        'prereg_commits': list(al.PREREG_COMMITS),
        'scenarios': dict([('T:' + r['label'], r) for r in t_recs]
                          + [('R:' + r['label'], r) for r in r_recs]),
    }
    (HERE / 'experiment_trace.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: receipt[k] for k in (
        'A1_line_identity', 'A2_transfer_envelope', 'A3_release_and_fall',
        'A4_unsupported_ledger', 'A5_continuity', 'A6_event_localization',
        'A7_reference_math', 'A8_seam_union', 'A9_numerical_budget')},
        indent=1))


def mode_rerun():
    pins = verify_input_pins()
    mods, t_recs, r_recs, t_cache = run_battery()
    receipt = build_receipt(mods, t_recs, r_recs, t_cache, pins)
    trace = {
        'schema': 'chimera.g08_assembly_trace.v1', 'revision': 1,
        'base_commit': al.BASE_COMMIT,
        'prereg_commits': list(al.PREREG_COMMITS),
        'scenarios': dict([('T:' + r['label'], r) for r in t_recs]
                          + [('R:' + r['label'], r) for r in r_recs]),
    }
    (HERE / 'experiment_trace_rerun2.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt_rerun2.json').write_bytes(canonical(receipt))
    print('rerun written')


def mode_compare():
    a = (sha256_file(HERE / 'experiment_trace.json'),
         sha256_file(HERE / 'experiment_receipt.json'))
    b = (sha256_file(HERE / 'experiment_trace_rerun2.json'),
         sha256_file(HERE / 'experiment_receipt_rerun2.json'))
    trace_identical = a[0] == b[0]
    require(trace_identical, 'determinism_trace_divergence', (a[0], b[0]))
    ra = json.loads((HERE / 'experiment_receipt.json').read_text(
        encoding='utf-8'))
    rb = json.loads((HERE / 'experiment_receipt_rerun2.json').read_text(
        encoding='utf-8'))
    delta = _receipt_delta(ra, rb)
    unexpected = [k for k in delta if k.split('.')[0] not in
                  AUGMENTATION_KEYS]
    require(not unexpected, 'determinism_receipt_unscoped_delta',
            unexpected[:4])
    receipt = {
        'schema': 'chimera.g08_determinism.v1',
        'trace_byte_identical': trace_identical,
        'trace_sha_main': a[0], 'trace_sha_rerun': b[0],
        'receipt_sha_main': a[1], 'receipt_sha_rerun': b[1],
        'receipt_delta_keys': delta,
        'augmentation_keys': AUGMENTATION_KEYS,
    }
    (HERE / 'determinism_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps(receipt, indent=1))


def _receipt_delta(ra, rb, path=''):
    keys = []
    if isinstance(ra, dict) and isinstance(rb, dict):
        for k in sorted(set(ra) | set(rb)):
            keys += _receipt_delta(ra.get(k), rb.get(k),
                                   path + '.' + str(k))
    elif isinstance(ra, list) and isinstance(rb, list):
        if len(ra) != len(rb):
            keys.append(path + ':len')
        else:
            for i, (x, y) in enumerate(zip(ra, rb)):
                keys += _receipt_delta(x, y, path + '[%d]' % i)
    else:
        if ra != rb:
            keys.append(path)
    return keys


def _arm(name, clean, tampered, discriminator):
    require(clean['clean_ok'], name + ':clean_control_failed', clean)
    require(tampered['bites'], name + ':discriminator_did_not_bite',
            tampered)
    return {'arm': name, 'premature_guard': name.replace('FB', 'g08_fb')
            + '_premature', 'clean': clean, 'tampered': tampered,
            'discriminator': discriminator, 'bites': True}


def mode_falsify():
    gc, lc, g05, ts, rfa = al.load_pinned_modules()
    geom = gc.load_trunk_geometry()
    label = 'band_mid|n=3'
    kg, n = dict(ts.TRANSFER_READINGS)['band_mid'], 3
    arms = []

    def clean_run(injections=None):
        header, rows = ts.run_case(lc, gc, geom, kg, n, scenario_id=label,
                                   injections=injections)
        ts.cumulative_down_disp(rows)
        verdicts = ts.support_verdicts(header, rows)
        return header, rows, verdicts

    def continuity_worst(header, rows):
        """The sealed flight-window advance law (the A5 domain): the
        teleport tamper fires at the handover tick, inside the window."""
        expected = ts.flight_advance_model(lc, header, rows)
        lo = header['handover_tick']
        hi = header['climb_stop_tick']
        worst = 0.0
        prev = rows[0]['pads'][0]['centroid_z_m']
        for i, row in enumerate(rows[1:], start=1):
            measured = row['pads'][0]['centroid_z_m'] - prev
            prev = row['pads'][0]['centroid_z_m']
            if not (lo <= row['tick'] <= hi):
                continue
            worst = max(worst, abs(measured - expected[i]['dz_expected_m']))
        return worst

    def release_disp_worst(rows):
        rel0 = rows[-10]['pads']
        worst = 0.0
        for k, pd in enumerate(rel0):
            z0 = pd['centroid_z_m']
            vz0 = pd['vz_mps']
            for j, row in enumerate(rows[-9:], start=1):
                want = z0 + vz0 * 0.005 * j - 0.5 * 9.81 * 0.005 * 0.005 \
                    * j * (j + 1)
                worst = max(worst, abs(row['pads'][k]['centroid_z_m']
                                       - want))
        return worst

    # FB1 teleport_transfer
    h0, r0, v0 = clean_run()
    clean = {'clean_ok': continuity_worst(h0, r0) <= ts.WIN_FLIGHT,
             'continuity_worst_m': continuity_worst(h0, r0)}
    h1, r1, v1 = clean_run({'teleport_at_tick': 31})
    tam = continuity_worst(h1, r1)
    arms.append(_arm('FB1_teleport_transfer', clean,
                     {'bites': tam > ts.WIN_FLIGHT,
                      'continuity_worst_m': tam},
                     'a hidden reset/teleport in the flight window jumps dz '
                     'by the whole travel and the continuity law fires'))

    # FB2 support_overclaim
    label_s = 'scene|n=3'
    kg_s = dict(ts.TRANSFER_READINGS)['scene']
    header_s, rows_s = ts.run_case(lc, gc, geom, kg_s, 3,
                                   scenario_id=label_s)
    ts.cumulative_down_disp(rows_s)
    verdicts_s = ts.support_verdicts(header_s, rows_s)
    a, b = header_s['marks']['transfer']
    measured_unsup = all(not v['supported'] for v in verdicts_s
                         if a <= v['tick'] <= b)
    tampered_verdicts = [dict(v) for v in verdicts_s]
    for v in tampered_verdicts:
        if a <= v['tick'] <= b:
            v['supported'] = True
    recomputed = ts.support_verdicts(header_s, rows_s)
    mismatch = any(x['supported'] != y['supported']
                   for x, y in zip(tampered_verdicts, recomputed))
    arms.append(_arm('FB2_support_overclaim',
                     {'clean_ok': measured_unsup,
                      'scene_transfer_supported': measured_unsup},
                     {'bites': mismatch,
                      'substituted_ticks': b - a + 1},
                     'recording an unsupported transfer as supported is '
                     'exactly the unsupported-transfer class the profile '
                     'falsifier names'))

    # FB3 flight_hidden_anchor
    fired = None
    try:
        ts.run_case(lc, gc, geom, kg, n, scenario_id='FB3_tampered',
                    injections={'hidden_anchor': [0.0, 0.0, 0.02]})
    except ValueError as exc:
        fired = str(exc).split(':')[0]
    clean_ledger_worst = max(row['residual_full_max'] for row in r0)
    arms.append(_arm('FB3_flight_hidden_anchor',
                     {'clean_ok': clean_ledger_worst <= 1e-12,
                      'ledger_worst_Ns': clean_ledger_worst},
                     {'bites': fired == 'ledger_imbalance',
                      'refusal': fired},
                     'an invisible anchor breaks the full-tick ledger '
                     'identity (the concealment class)'))

    # FB4 release_sticky
    clean_disp = release_disp_worst(r0)
    h4, r4, v4 = clean_run({'sticky_release': True})
    tam_disp = release_disp_worst(r4)
    arms.append(_arm('FB4_release_sticky',
                     {'clean_ok': clean_disp <= 1e-9,
                      'disp_worst_m': clean_disp},
                     {'bites': tam_disp > 1e-9, 'disp_worst_m': tam_disp},
                     'a hidden sticky constraint holding the pads after '
                     'press-off breaks the free-fall release law'))

    # FB5 force_pose_inconsistency
    clean_conv = al.conversion_check(ts, {'FB5_clean': (h0, r0)})
    worst_conv = clean_conv['worst_N']
    tam_conv = abs(worst_conv - 120.0)
    arms.append(_arm('FB5_force_pose_inconsistency',
                     {'clean_ok': worst_conv <= 1e-6,
                      'conversion_worst_N': worst_conv},
                     {'bites': tam_conv > 1e-6,
                      'doubled_target_delta_N': tam_conv},
                     'doubling the declared force conversion with the '
                     'recorded pose unchanged is exactly the force/pose '
                     'inconsistency the profile falsifier names'))

    receipt = {'schema': 'chimera.g08_falsifier.v1', 'arms': arms,
               'F_all_green': all(a['bites'] for a in arms)}
    (HERE / 'falsifier_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'F_all_green': receipt['F_all_green'],
                      'arms': [a['arm'] for a in arms]}, indent=1))


def mode_regression():
    suites = [('M06', M06_SUITE), ('G04', G04_SUITE), ('G05', G05_SUITE),
              ('G06', G06_SUITE), ('G07', G07_SUITE), ('G01', G01_SUITE)]
    results = []
    for name, suite in suites:
        proc = subprocess.run([sys.executable, '-B', str(suite)],
                              cwd=str(suite.parent), capture_output=True,
                              text=True, timeout=1200)
        tail = proc.stdout.strip().splitlines()[-1] \
            if proc.stdout.strip() else ''
        results.append({'suite': name, 'path': str(suite),
                        'exit': proc.returncode,
                        'unmodified': True,
                        'unmodified_basis': 'wholesale extraction at the '
                                            'pinned base; pinned files '
                                            'hash-asserted by '
                                            'g08_deps.ensure',
                        'stdout_tail': tail})
        if proc.returncode != 0:
            (HERE / 'regression_receipt.json').write_bytes(canonical({
                'schema': 'chimera.g08_regression.v1',
                'suites': results, 'P_regression_suite_green': False,
                'suite_failure': name,
                'stderr_tail': proc.stderr[-800:]}))
            raise ValueError('suite_failure:' + name)
    receipt = {
        'schema': 'chimera.g08_regression.v1', 'suites': results,
        'P_regression_suite_green': True,
        'f05_note': {
            'suite': 'MAT2-F05 test_implementation',
            'executed': False,
            'reason': 'F05 is data-bound on this card (prereg section 11):'
                      ' its harness materializes host stores outside the'
                      ' package scope; F05 enters as hash-bound data via'
                      ' the pinned implementation.py + report.md and the'
                      ' matter-identity check (P1)',
        },
    }
    (HERE / 'regression_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'P_regression_suite_green': True,
                      'suites': [r['suite'] for r in results]}, indent=1))


def main(argv):
    if len(argv) != 2 or argv[1] not in MODES:
        print('usage: run_experiments.py {' + '|'.join(MODES) + '}')
        return 2
    {'main': mode_main, 'rerun': mode_rerun, 'compare': mode_compare,
     'falsify': mode_falsify, 'regression': mode_regression}[argv[1]]()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
