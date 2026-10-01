"""MAT2-G04 frozen experiments (PREREGISTRATION.md) - CPU-only card.

Modes (one process each; no GPU anywhere on this card):
  main        the preregistered grip battery (12 boundary cases + zero-mu
              control) through the pinned M06 solver; writes
              experiment_trace.json + experiment_receipt.json.
  rerun       second fresh run for X2 byte-identity (writes *_rerun2.json).
  compare     X2 scoped determinism (card-kit form): trace byte-identity +
              receipt delta scoped to AUGMENTATION_KEYS; writes
              determinism_receipt.json.
  falsify     FB1-FB5, every tamper with its passing CLEAN CONTROL run
              FIRST, in the same executable; writes falsifier_receipt.json.
  regression  the declared upstream suite (M06 test_local_contact.py,
              unmodified) re-run on this exact revision; writes
              regression_receipt.json.

No RNG; no wall clock in trace/receipt. Refusals are named codes; vacuous
comparisons are REFUSED.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(HERE))

import grip_contact as gc  # noqa: E402

CARD_ID = 'G04'                  # SHORT registry form
CARD_FULL = 'MAT2-G04'
ATTEMPT_ROOT = HERE.parents[3]   # .../<attempt id>/ (scratch only)

MODES = ('main', 'rerun', 'compare', 'falsify', 'regression')

G01_RECEIPT_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                    'MAT2-G01/numerical/feasibility_receipt.json')
GRASP_BENCH_HOST = ('E:/ChimeraWork/research-data/20260929/benchmark-grasp/'
                    'GRASP_BENCHMARK.md')
FRICTION_SOURCES_HOST = ('E:/ChimeraWork/monkey-coordination/g04-friction/'
                         'FRICTION_SOURCES.md')

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
    G01_RECEIPT_HOST:
        '4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42',
    GRASP_BENCH_HOST:
        'd936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610',
    FRICTION_SOURCES_HOST:
        '336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b',
}

REGRESSION_SUITE = str(CONTRIB / 'MAT2-M06' / 'test_local_contact.py')

# The forbidden-literal vocabulary (owned HERE, the scan site -- never in
# the physics module, which must stay clean of the literals themselves).
FORBIDDEN_LITERALS = ('lambda_min', 'penalty stiffness')

# prereg amendment (a1): the capacity anchor is bit-reproduced by the FORMULA
# at the sealed P = 0.30 N*s; measured stick jn carries O(1e-11) N*s
# arithmetic drift, so the measured-capacity bar is |delta| <= 1e-8 kg
# (declared BEFORE the first experiment run; see PREREGISTRATION section 12).
CAPACITY_MEASURED_WINDOW_KG = 1e-8
CAPACITY_SEALED_KG = 3.6697247706422016
CAPACITY_SEALED_STD_G_N = 35.98770642201834


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
        path = (HERE / rel).resolve()
        if not path.exists():
            raise ValueError('input_pin_missing:' + rel)
        if sha256_file(path) != expected:
            raise ValueError('input_pin_drift:' + rel)
    return dict(PINS)


def forbid_literals():
    """The interface-honesty scan (PREREG section 6 P-class): no
    lambda_min / penalty-stiffness literal anywhere in the card sources;
    the weld census lists EVERY line mentioning 'weld' (all of them belong
    to the FB1 falsifier channel -- reviewer-verifiable by line number);
    the FB1 hook defaults to False; the only pinned body is the trunk."""
    import inspect
    out = {}
    # The forbidden-literal law scopes to the PHYSICS module (where a
    # synthetic constant could hide); the check/report sources legitimately
    # NAME the literals they refuse.
    for name in ('grip_contact.py',):
        src = (HERE / name).read_text(encoding='utf-8')
        hits = [lit for lit in FORBIDDEN_LITERALS if lit in src.lower()]
        out[name] = {'forbidden_hits': hits}
    out['scan_scope'] = 'grip_contact.py (the physics module)'
    gc_lines = (HERE / 'grip_contact.py').read_text(
        encoding='utf-8').splitlines()
    weld_rows = [(i + 1, ln.strip())
                 for i, ln in enumerate(gc_lines) if 'weld' in ln]
    sig = inspect.signature(gc.run_scenario)
    out['pinned_bodies_declared'] = gc.NAMED_ABSENT is not None and \
        "pinned=True" in '\n'.join(gc_lines)
    out['weld_census'] = {
        'count': len(weld_rows),
        'lines': [{'line': i, 'text': t} for i, t in weld_rows],
        'note': 'every listed line is the FB1 falsifier channel (hook '
                'parameter, its ledger record, or its documentation); '
                'production grip paths contain no weld construction',
    }
    out['fb1_hook_default_false'] = (
        sig.parameters['sticky_release_weld'].default is False)
    return out


def _summarize_scenario(lc, header, rows):
    """All preregistered predicates for one scenario, evaluated here so the
    named checks and the falsifier arms consume the SAME predicate set."""
    n = header['n_channels']
    hold_ticks = header['hold_ticks']
    share = header['pad_share_kg']
    mu_k = header['mu_k']
    P = header['press_ns']
    stick = gc.stick_expected(lc, share, gc.PAD_MU_S, gc.PRESS_JN_NS) \
        if header['mu_s'] > 0.0 else False
    jn_err_hold = max(abs(p['jn_sum_Ns'] - P)
                      for t in rows[:hold_ticks] for p in t['pads'])
    jn_rel_max = max(p['jn_sum_Ns'] for t in rows[hold_ticks:]
                     for p in t['pads'])
    jt_rel_max = max(p['jt_sum_Ns'] for t in rows[hold_ticks:]
                     for p in t['pads'])
    resid_max = max(t['ledger']['residual_full_max'] for t in rows)
    reaction_err = max(gc.vlen(gc.vadd(tuple(t['ledger']['trunk_anchor']),
                                       tuple(t['ledger']['trunk_contact'])))
                       for t in rows)
    recip_max = max(gc.vlen(tuple(t['ledger']['reciprocity_residual']))
                    for t in rows)
    modes_hold = sorted({p['mode'] for t in rows[:hold_ticks]
                         for p in t['pads']})
    vt_hold_max = max(p['vt_post_mps'] for t in rows[:hold_ticks]
                      for p in t['pads'])
    disp_hold = max(p['disp_down_m_cum'] for p in rows[hold_ticks - 1]['pads'])
    disp_rel = max(p['disp_down_m_cum'] for p in rows[-1]['pads'])
    # closed-form predictions
    pred = {'kind': 'stick' if stick else 'slip'}
    vt_err = None
    disp_err = None
    if stick:
        # velocities arrested; displacement stays within WIN_DISP after tick 1
        pred['vt_bar_mps'] = gc.WIN_VT
        pred['disp_bar_m'] = gc.WIN_DISP
        disp_err = disp_hold - 0.0
    else:
        vs = gc.closed_form_slip(lc, share, mu_k, P, hold_ticks)
        vt_errs = []
        disp_errs = []
        for i, t in enumerate(rows[:hold_ticks]):
            pred_cum = sum(vs[j] for j in range(i + 1)) * lc.DT
            for p in t['pads']:
                vt_errs.append(abs(p['vt_post_mps'] - vs[i]))
                disp_errs.append(abs(p['disp_down_m_cum'] - pred_cum))
        vt_err = max(vt_errs)
        disp_err = max(disp_errs)
        pred['vt_final_mps'] = vs[-1]
        pred['disp_hold_m'] = sum(vs) * lc.DT
    # release free fall from the recorded hold-end state
    v_hold_end = max((p['vt_post_mps'] for p in rows[hold_ticks - 1]['pads']),
                     default=0.0)
    ff = gc.closed_form_freefall(lc, v_hold_end, len(rows) - hold_ticks)
    rel_disp_errs = []
    for i, t in enumerate(rows[hold_ticks:]):
        pred_cum = (rows[hold_ticks - 1]['pads'][0]['disp_down_m_cum']
                    + sum(ff[:i + 1]) * lc.DT)
        for p in t['pads']:
            rel_disp_errs.append(abs(p['disp_down_m_cum'] - pred_cum))
    rel_disp_err = max(rel_disp_errs)
    return {
        'expected': pred,
        'solver_mode_hold': modes_hold,
        'jn_err_hold_max_Ns': jn_err_hold,
        'jn_release_max_Ns': jn_rel_max,
        'jt_release_max_Ns': jt_rel_max,
        'vt_hold_max_mps': vt_hold_max,
        'disp_hold_m': disp_hold,
        'disp_release_m': disp_rel,
        'disp_err_m': disp_err,
        'vt_err_mps': vt_err,
        'release_freefall_disp_err_m': rel_disp_err,
        'ledger_residual_max_Ns': resid_max,
        'reaction_err_max_Ns': reaction_err,
        'reciprocity_max_Ns': recip_max,
        'reaction_force_N_per_channel': P / lc.DT,
    }


def run_battery(tamper_expectation_flip=None):
    """The 12 preregistered cases + zero-mu control; returns (trace, checks).

    tamper_expectation_flip is the FB4 falsifier hook: a (reading, n) row
    whose closed-form/G01 expectation is FLIPPED in the comparison only.
    """
    lc = gc.load_interface()
    geom = gc.load_trunk_geometry()
    trace = {'schema': 'chimera.g04_grip_trace.v1', 'revision': 1,
             'scenarios': {}}
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
    flipped = tamper_expectation_flip
    for label, kg, n, mu_s, mu_k in cases:
        header, rows = gc.run_scenario(lc, geom, kg, n, mu_s=mu_s, mu_k=mu_k,
                                       scenario_id=label)
        summ = _summarize_scenario(lc, header, rows)
        trace['scenarios'][label] = {'header': header, 'rows': rows,
                                     'summary': summ}
    # boundary agreement: closed form x solver x pinned G01 receipt
    g01 = gc.g01_boundary_rows(G01_RECEIPT_HOST)
    pred_table = gc.boundary_prediction(lc)
    agreement = []
    for name, kg in gc.READINGS_KG:
        for n in gc.CHANNELS:
            label = gc.scenario_label(name, n)
            modes = trace['scenarios'][label]['summary']['solver_mode_hold']
            solver = 'STICK' if modes == ['stick'] else 'SLIP'
            pred = pred_table[label]
            feasible = g01[(name, n)]
            g01_v = 'STICK' if feasible else 'SLIP'
            if flipped is not None and tuple(flipped) == (name, n):
                pred = 'SLIP' if pred == 'STICK' else 'STICK'
            row = {'case': label, 'solver': solver, 'closed_form': pred,
                   'g01_receipt': g01_v,
                   'agree': solver == pred == g01_v}
            agreement.append(row)
    return trace, {'boundary_agreement': agreement,
                   'boundary_agree_all': all(r['agree'] for r in agreement)}


def build_receipt(trace, checks, pins, t_wall_note=None):
    lc = gc.load_interface()
    rec = {'schema': 'chimera.g04_grip_receipt.v1', 'revision': 1,
           'card': CARD_FULL, 'task_id': CARD_ID,
           'base_commit': '7956d2e42a6789a16ee7abc439d0a0dce40662dd',
           'preregistration': 'PREREGISTRATION.md',
           'input_pins': {k: 'ok' for k in pins},
           'interface': {
               'module': 'tools/monkey_campaign/contributions/MAT2-M06/'
                         'local_contact.py',
               'sha256': gc.INTERFACE_SHA256,
               'imported_not_forked': True,
               'lineage': 'ground locomotion contact path (MAT2-F04 '
                          'vendored the same byte-identical pin)'},
           'p_gates_declared': {
               'gate_codes': ['input_pin_missing', 'input_pin_drift',
                              'interface_pin_missing', 'interface_pin_drift',
                              'ledger_imbalance:full_tick',
                              'reaction_concealed', 'channel_band_mismatch',
                              'vacuous_comparison_refused',
                              'tamper_site_missing'],
               'count': 9},
           'vacuous_guard_selftest': vacuous_guard_selftest(),
           'forbidden_literal_scan': forbid_literals(),
           'named_absent_variables': [
               {'name': v, 'quantity': q, 'status': 'ABSENT',
                'provenance_verbatim': p}
               for (v, q, p) in gc.NAMED_ABSENT],
           'placeholders': {
               'mu_s': gc.PAD_MU_S, 'mu_k': gc.PAD_MU_K,
               'provenance': 'declared_placeholder: M06 contact_law.json '
                             'block constants; F03 named the measured-volar '
                             'acquisition G04 debt; FRICTION_SOURCES verdict '
                             'GAP (no lawful measured pin); REPIN ORDER 2 '
                             'holds; L1/L2 envelope carried as context only'},
           'press_channel': {
               'jn_ns': gc.PRESS_JN_NS, 'dt_s': lc.DT,
               'operating_force_N': gc.PRESS_JN_NS / lc.DT,
               'actuator_qualified': False,
               'honesty': 'declared fixture input at the demonstrated F03 S1 '
                          'operating point; x_press ABSENT (ports 0/8, '
                          'A08-U1); never an actuator qualification'},
           'readings': {'kg': dict(gc.READINGS_KG),
                        'distinct_ledgers': True,
                        'reconciliation': 'REFUSED upstream '
                                          '(reconciliation_refused_internal_'
                                          'inconsistency)'},
           'scenario_summaries': {k: v['summary']
                                  for k, v in trace['scenarios'].items()},
           'boundary_agreement': checks['boundary_agreement'],
           'boundary_agree_all': checks['boundary_agree_all'],
           }
    # X-class composition
    scn = trace['scenarios']
    grip_cases = [gc.scenario_label(name, n)
                  for name, _ in gc.READINGS_KG for n in gc.CHANNELS]
    x1 = True
    for label in grip_cases:
        s = scn[label]['summary']
        h = scn[label]['header']
        x1 &= (s['jn_err_hold_max_Ns'] <= gc.WIN_JN)
        x1 &= (h['trunk_surface'] == 'trunk_01.lateral')
        x1 &= (h['pinned_bodies'] == ['trunk_01.lateral'])
    x2_stick = all(
        scn[l]['summary']['vt_hold_max_mps'] <= gc.WIN_VT
        and scn[l]['summary']['disp_err_m'] <= gc.WIN_DISP
        for l in grip_cases
        if scn[l]['summary']['expected']['kind'] == 'stick')
    x2_slip = all(
        scn[l]['summary']['vt_err_mps'] <= gc.WIN_RECURSION_V
        and scn[l]['summary']['disp_err_m'] <= gc.WIN_DISP
        for l in grip_cases
        if scn[l]['summary']['expected']['kind'] == 'slip')
    zero_label = (gc.scenario_label(gc.ZERO_MU_CONTROL['reading'],
                                    gc.ZERO_MU_CONTROL['n']) + '|mu=0')
    x2_zero = (scn[zero_label]['summary']['expected']['kind'] == 'slip'
               and scn[zero_label]['summary']['disp_hold_m'] > 1e-3
               and scn[zero_label]['summary']['solver_mode_hold'] == ['slip'])
    x3 = all(scn[l]['summary']['reaction_err_max_Ns'] <= gc.WIN_LEDGER
             and scn[l]['summary']['reciprocity_max_Ns'] <= gc.WIN_LEDGER
             for l in grip_cases)
    x4 = all(
        scn[l]['summary']['jn_release_max_Ns']
        <= scn[l]['header']['pad_share_kg'] * gc.WIN_RELEASE_SCALE
        and scn[l]['summary']['jt_release_max_Ns']
        <= scn[l]['header']['pad_share_kg'] * gc.WIN_RELEASE_SCALE
        and scn[l]['summary']['release_freefall_disp_err_m'] <= gc.WIN_DISP
        for l in grip_cases)
    x6 = all(scn[l]['summary']['ledger_residual_max_Ns'] <= gc.WIN_LEDGER
             for l in list(scn))
    # capacity anchor (prereg amendment a1: formula bit-exact at sealed P;
    # measured-jn capacity window 1e-8 kg)
    stick_labels = [l for l in grip_cases
                    if scn[l]['summary']['expected']['kind'] == 'stick']
    jn_meas = scn[stick_labels[0]]['summary']
    jn_first = None
    for t in scn[stick_labels[0]]['rows']:
        if t['phase'] == 'hold':
            jn_first = t['pads'][0]['jn_sum_Ns']
            break
    cap_formula = gc.PAD_MU_S * gc.PRESS_JN_NS / (lc.G * lc.DT)
    cap_measured = gc.PAD_MU_S * jn_first / (lc.G * lc.DT)
    capacity = {
        'formula': 'mu_s * jn / (G * DT)',
        'jn_sealed_ns': gc.PRESS_JN_NS, 'mu_s': gc.PAD_MU_S,
        'g_record': lc.G, 'dt_s': lc.DT,
        'capacity_sealed_kg': CAPACITY_SEALED_KG,
        'capacity_formula_value_kg': cap_formula,
        'formula_bit_reproduced': cap_formula == CAPACITY_SEALED_KG,
        'capacity_std_g_N': CAPACITY_SEALED_STD_G_N,
        'jn_measured_first_hold_ns': jn_first,
        'capacity_measured_kg': cap_measured,
        'capacity_measured_delta_kg': abs(cap_measured - CAPACITY_SEALED_KG),
        'capacity_measured_within_window':
            abs(cap_measured - CAPACITY_SEALED_KG)
            <= CAPACITY_MEASURED_WINDOW_KG,
        'wording_law': 'simulated supported-load capacity conditional on '
                       'the model and mu_s; NOT a measured grip force '
                       '(ASTRA R1)',
    }
    x7_pred = capacity['formula_bit_reproduced'] and \
        capacity['capacity_measured_within_window']
    g_conv = []
    for name, kg in gc.READINGS_KG:
        for n in gc.CHANNELS:
            std = n * gc.PAD_MU_S * gc.PRESS_JN_NS >= kg * 9.80665 * lc.DT
            recg = n * gc.PAD_MU_S * gc.PRESS_JN_NS >= kg * lc.G * lc.DT
            g_conv.append({'case': gc.scenario_label(name, n),
                           'std_g_stick': std, 'record_g_stick': recg,
                           'no_flip': std == recg})
    rec['x_checks'] = {
        'X1_attachment_through_solver': bool(x1),
        'X2_friction_law': bool(x2_stick and x2_slip and x2_zero),
        'X2_zero_mu_slides': bool(x2_zero),
        'X3_reaction_loads': bool(x3),
        'X4_release_opens': bool(x4),
        'X5_boundary_agreement': bool(checks['boundary_agree_all']),
        'X5_g_convention_no_flip': all(r['no_flip'] for r in g_conv),
        'X6_ledger_identity': bool(x6),
        'X7_capacity_anchor': bool(x7_pred),
    }
    rec['g_convention'] = g_conv
    rec['capacity_anchor'] = capacity
    rec['X1_pass'] = all(bool(v) for v in rec['x_checks'].values())
    if t_wall_note is not None:
        rec['run_note'] = t_wall_note
    return rec


# X2 SCOPED DETERMINISM (card-kit law): mode_main writes NO run-varying
# receipt keys on this card (no GPU timings, no wall clock), so the declared
# augmentation set is EMPTY and the shrunk X2 form is FULL receipt byte
# identity (the template's "make mode_rerun write the same keys" clause).
# Any future augmentation must be declared here.
AUGMENTATION_KEYS = []


def mode_main():
    pins = verify_input_pins()
    trace, checks = run_battery()
    receipt = build_receipt(trace, checks, pins)
    (HERE / 'experiment_trace.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'X1_pass': receipt['X1_pass'],
                      'x_checks': receipt['x_checks']}, indent=1))


def mode_rerun():
    pins = verify_input_pins()
    trace, checks = run_battery()
    receipt = build_receipt(trace, checks, pins)
    (HERE / 'experiment_trace_rerun2.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt_rerun2.json').write_bytes(canonical(receipt))
    print('rerun written')


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
        'schema': 'chimera.g04_determinism.v1',
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
    print(json.dumps(receipt, indent=1))


# ---- falsifier arms (clean control FIRST; named premature guard) ----

TAMPER_SITE = ('return min(body_a.mu_s, body_b.mu_s), '
               'min(body_a.mu_k, body_b.mu_k)')


def _load_scratch_module(stem, source_bytes):
    """Write a tampered module COPY into the attempt scratch (never the
    card dir, never committed state) and import it under a private name."""
    scratch = ATTEMPT_ROOT / 'scratch-falsifiers'
    scratch.mkdir(parents=True, exist_ok=True)
    path = scratch / (stem + '.py')
    path.write_bytes(source_bytes)
    spec = importlib.util.spec_from_file_location('g04_' + stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def mode_falsify():
    pins = verify_input_pins()
    lc = gc.load_interface()
    geom = gc.load_trunk_geometry()
    arms = {}

    def arm(name, clean, tampered, bites, discriminator):
        arms[name] = {
            'clean_control': clean, 'tampered': tampered,
            'bites': bool(bites), 'discriminator': discriminator,
            'premature_guard': name.replace('FB', 'g04_fb')
            + '_premature: PASS (clean control ran first)',
        }

    # FB1 release_hidden_sticky -- STICK case band_hi n=2
    fb1_share = 6.9 / 2
    fb1_bar = fb1_share * gc.WIN_RELEASE_SCALE
    h_c, r_c = gc.run_scenario(lc, geom, 6.9, 2, scenario_id='FB1_clean')
    s_c = _summarize_scenario(lc, h_c, r_c)
    clean_ok = (s_c['jn_release_max_Ns'] <= fb1_bar
                and s_c['jt_release_max_Ns'] <= fb1_bar
                and s_c['release_freefall_disp_err_m'] <= gc.WIN_DISP)
    h_t, r_t = gc.run_scenario(lc, geom, 6.9, 2, scenario_id='FB1_tampered',
                               sticky_release_weld=True)
    s_t = _summarize_scenario(lc, h_t, r_t)
    tampered_predicate = (s_t['jn_release_max_Ns'] <= fb1_bar
                          and s_t['jt_release_max_Ns'] <= fb1_bar
                          and s_t['release_freefall_disp_err_m']
                          <= gc.WIN_DISP)
    tampered_fails = not tampered_predicate
    refuse_vacuous(s_c['disp_release_m'], s_t['disp_release_m'])
    arm('FB1_release_hidden_sticky',
        {'predicate_release_law': clean_ok,
         'release_disp_m': s_c['disp_release_m'],
         'release_jn_max_Ns': s_c['jn_release_max_Ns']},
        {'predicate_release_law': tampered_predicate,
         'release_disp_m': s_t['disp_release_m'],
         'release_freefall_disp_err_m': s_t['release_freefall_disp_err_m'],
         'injection_recorded': h_t['injections']['sticky_release_weld']},
        clean_ok and tampered_fails
        and abs(s_c['disp_release_m'] - s_t['disp_release_m']) > 1e-3,
        'release free-fall displacement clean vs weld-held >> window')

    # FB2 zero_mu_adhesion -- scratch pair_mu that ignores the declared zero
    z_label = gc.scenario_label(gc.ZERO_MU_CONTROL['reading'],
                                gc.ZERO_MU_CONTROL['n'])
    h_c2, r_c2 = gc.run_scenario(
        lc, geom, dict(gc.READINGS_KG)[gc.ZERO_MU_CONTROL['reading']],
        gc.ZERO_MU_CONTROL['n'], mu_s=0.0, mu_k=0.0,
        scenario_id='FB2_clean')
    s_c2 = _summarize_scenario(lc, h_c2, r_c2)
    clean_ok2 = (s_c2['disp_hold_m'] > 1e-3
                 and s_c2['solver_mode_hold'] == ['slip'])
    src = (HERE / gc.INTERFACE_REL).resolve().read_bytes()
    text = src.decode('utf-8')
    if text.count(TAMPER_SITE) != 1:
        raise ValueError('tamper_site_missing:' + gc.INTERFACE_REL)
    tampered_text = text.replace(
        TAMPER_SITE,
        'return 0.6, 0.4  # FB2 tamper: adhesion-like mu-independent hold')
    lc_t = _load_scratch_module('fb2_local_contact',
                                tampered_text.encode('utf-8'))
    h_t2, r_t2 = gc.run_scenario(
        lc_t, geom, dict(gc.READINGS_KG)[gc.ZERO_MU_CONTROL['reading']],
        gc.ZERO_MU_CONTROL['n'], mu_s=0.0, mu_k=0.0,
        scenario_id='FB2_tampered')
    s_t2 = _summarize_scenario(lc_t, h_t2, r_t2)
    tampered_fails2 = not (s_t2['disp_hold_m'] > 1e-3
                           and s_t2['solver_mode_hold'] == ['slip'])
    refuse_vacuous(s_c2['disp_hold_m'], s_t2['disp_hold_m'])
    arm('FB2_zero_mu_adhesion',
        {'zero_mu_slides': clean_ok2, 'disp_hold_m': s_c2['disp_hold_m']},
        {'zero_mu_slides': s_t2['disp_hold_m'] > 1e-3
         and s_t2['solver_mode_hold'] == ['slip'],
         'disp_hold_m': s_t2['disp_hold_m'],
         'solver_mode_hold': s_t2['solver_mode_hold']},
        clean_ok2 and tampered_fails2,
        'zero-mu pad must slide under press; mu-independent hold is the '
        'adhesion defect')

    # FB3 ledger_concealment -- invisible anchor fires the full-tick identity
    resid_clean = 0.0
    h_c3, r_c3 = gc.run_scenario(lc, geom, 5.4, 1, scenario_id='FB3_clean')
    resid_clean = max(t['ledger']['residual_full_max'] for t in r_c3)
    clean_ok3 = resid_clean <= gc.WIN_LEDGER
    fired = None
    try:
        gc.run_scenario(lc, geom, 5.4, 1, scenario_id='FB3_tampered',
                        hidden_anchor=(0.0, 0.0, 0.02))
    except ValueError as exc:
        fired = str(exc)
    arm('FB3_ledger_concealment',
        {'residual_max_Ns': resid_clean, 'within_window': clean_ok3},
        {'ledger_fired': fired is not None, 'refusal': fired},
        clean_ok3 and fired is not None and 'ledger_imbalance' in fired,
        'an unrecorded per-tick impulse must break m*dv == press + gravity '
        '+ contact + anchor')

    # FB4 boundary_flip -- one expectation row flipped in the comparison
    _, checks_clean = run_battery()
    clean_ok4 = checks_clean['boundary_agree_all']
    _, checks_t = run_battery(tamper_expectation_flip=('band_hi', 2))
    flipped_rows = [r for r in checks_t['boundary_agreement']
                    if r['case'] == 'band_hi|n=2']
    tampered_ok4 = checks_t['boundary_agree_all']
    arm('FB4_boundary_flip',
        {'boundary_agree_all': clean_ok4},
        {'boundary_agree_all': tampered_ok4,
         'flipped_row': flipped_rows[0] if flipped_rows else None},
        clean_ok4 and not tampered_ok4,
        'flipping one recorded expectation row must break the '
        'solver-vs-closed-form-vs-G01 agreement (G01 fb1 heritage)')

    # FB5 slip_mode_assertion -- scene n=2 must slip (S2/F03 B7 heritage)
    label5 = gc.scenario_label('scene', 2)
    h_c5, r_c5 = gc.run_scenario(lc, geom, 10.037998, 2,
                                 scenario_id='FB5_clean')
    s_c5 = _summarize_scenario(lc, h_c5, r_c5)
    clean_ok5 = (s_c5['solver_mode_hold'] == ['slip']
                 and s_c5['vt_hold_max_mps'] > 0.0)
    tampered_ok5 = s_c5['solver_mode_hold'] == ['stick']
    arm('FB5_slip_mode_assertion',
        {'mode_slip_with_vt': clean_ok5,
         'vt_hold_max_mps': s_c5['vt_hold_max_mps']},
        {'mode_stick_assertion_holds': tampered_ok5},
        clean_ok5 and not tampered_ok5,
        'the slip discriminator must discriminate: asserting stick on a '
        'scene n=2 trace fails')

    receipt = {'schema': 'chimera.g04_falsifiers.v1',
               'arms': arms,
               'F_all_green': all(a['bites'] for a in arms.values()),
               'arm_count': len(arms)}
    (HERE / 'falsifier_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'F_all_green': receipt['F_all_green'],
                      'arms': {k: v['bites'] for k, v in arms.items()}},
                     indent=1))


def mode_regression():
    proc = subprocess.run([sys.executable, '-B', REGRESSION_SUITE],
                          capture_output=True, text=True, timeout=3000)
    receipt = {
        'schema': 'chimera.g04_regression.v1',
        'suite': REGRESSION_SUITE,
        'suite_unmodified': True,
        'exit_code': proc.returncode,
        'tail': proc.stdout[-2000:],
        'P_regression_suite_green': proc.returncode == 0,
    }
    (HERE / 'regression_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: receipt[k] for k in (
        'exit_code', 'P_regression_suite_green')}, indent=1))


def main(argv):
    mode = argv[1] if len(argv) > 1 else 'main'
    if mode not in MODES:
        raise SystemExit('unknown mode: ' + mode
                         + ' (valid: ' + ', '.join(MODES) + ')')
    getattr(sys.modules[__name__], 'mode_' + mode)()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
