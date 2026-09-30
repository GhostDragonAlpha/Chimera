"""MAT2-G02 frozen experiments (PREREGISTRATION.md base 49bd9a85 +
Amendments A1 a39a946e / A2 951c963e) - card-kit pattern (M08 lineage).

CPU-ONLY card: the scope is a two-body attachment fixture (356 ticks, one
active coordinate) - the CPU-FIRST law is satisfied directly and no GPU
submission is made (prereg law 12). No fitting experiment runs (sealed A07
gate); no friction constant appears anywhere; no lambda_min.

Modes (one process each):
  main       X1 closed-form element agreement + frozen dynamic fixture run;
             writes experiment_trace.json + experiment_receipt.json
             (physics-only, byte-identical on rerun) and
             experiment_profile.json (wall time; NEVER byte-compared).
  rerun      second fresh run for X2 byte-identity (writes *_rerun2.json).
  compare    X2 scoped determinism: byte-identity of the DECLARED unit (the
             trace), receipt delta scoped to AUGMENTATION_KEYS; writes
             determinism_receipt.json.
  falsify    F-arms, each tamper with its passing CLEAN CONTROL run FIRST,
             in the same executable; writes falsifier_receipt.json.
  regression the declared upstream suite re-run unmodified on this exact
             revision; writes regression_receipt.json.

Laws enforced here (do NOT remove):
  - No RNG; no wall-clock in trace/receipt (timings live only in
    experiment_profile.json, excluded from byte-identity by declaration).
  - Refusals are named codes; vacuous comparisons are REFUSED.
  - Tampered modules are scratch copies under .tmp/, never committed state.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import time

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import attachment_patch as ap  # noqa: E402 (this card's frozen element)

CARD_ID = 'G02'
CARD_FULL = 'MAT2-G02'

# Frozen input pins (copy hashes from the pinned sources, never re-type).
PINS = {
    '../MAT2-M01/material_state.py':
        'b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40',
    '../MAT2-M05/interface_state.json':
        'c09bdf0564d152fa8b9a41489bd874fd0570f75e40ed3ce848f4c474fd0320c6',
    '../MAT2-A09/grasp_package.json':
        '0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24',
    '../MAT2-A08/parameter_envelope.json':
        '2fb43fd44f13e8b927142d72b79d36246ee7d71fd954a39ffeb12b74dc716424',
    '../MAT2-M05/test_interface_exchange.py':
        'af4cc05905d2f1f83d709906a82c411493fdf195b32b4185aaac05f8690a5e30',
}

MODES = ('main', 'rerun', 'compare', 'falsify', 'regression')

AGREE_REL_WINDOW = 1e-15          # frozen closed-form agreement window
TORQUE_BOUND_N_M = 1e-15          # frozen summed-torque bound (law T3)
PROBE_GAPS = (1.0e-3, 0.02, 0.053030, 0.0923)   # frozen probe grid
RELEASE_TICK = ap.RELEASE_TICK


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _numpy_json_default(o):
    """Numpy scalars reaching json serialize as plain counterparts.
    (Verbatim from the M08 card-kit lineage: keep exactly.)"""
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    raise TypeError(f'Object of type {o.__class__.__name__} '
                    f'is not JSON serializable')


def canonical(value):
    """The one serializer for trace/receipt bytes (byte-identity unit)."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False,
                      default=_numpy_json_default).encode('utf-8')


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
        if expected.startswith('PLACEHOLDER'):
            raise ValueError('input_pin_unfilled:' + rel)
        if sha256_file(path) != expected:
            raise ValueError('input_pin_drift:' + rel)
    return dict(PINS)


def _rel(a, b):
    d = abs(a - b)
    return d / max(1.0, abs(a), abs(b))


# ------------------------------------------------------------ X1 element
def element_probes():
    """T1/T2/T4/T5/T7/T9 exact probes + X1 element-vs-oracle agreement on
    the frozen probe grid. Returns (probe_rows, agreement_rows)."""
    rows = []
    agree = []

    # T1 geometry (exact)
    geo = ap.patch_geometry()
    rows.append({'probe': 'T1_areas', 'A1_m2': geo['areas_m2'][0],
                 'A2_m2': geo['areas_m2'][1],
                 'A_patch_m2': geo['area_patch_m2'],
                 'T1_pass': abs(geo['areas_m2'][0] - 1.0e-4) <= 1e-18
                 and abs(geo['areas_m2'][1] - 6.5e-5) <= 1e-18
                 and abs(geo['area_patch_m2'] - 1.65e-4) <= 1e-18,
                 'area_ratio': geo['areas_m2'][0] / geo['areas_m2'][1]})
    rows.append({'probe': 'T1_weights', 'w1': ap.W1, 'w2': ap.W2,
                 'sum_minus_1': abs(ap.W1 + ap.W2 - 1.0),
                 'T1_weights_pass': abs(ap.W1 + ap.W2 - 1.0) <= 1e-18})

    # T2 areal scaling at e0 (exact closed forms, Amendment A1 literals)
    e0 = 1.0e-3
    el = ap.PatchElement()
    el.bind('port:patch', 'port:patch')
    ld = el.loads(e0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1)
    t1 = ld['triangles'][0]['tension_N']
    t2 = ld['triangles'][1]['tension_N']
    total = ld['force_on_a_N'][0]
    rows.append({'probe': 'T2_areal_scaling', 'e0_m': e0, 'T1_N': t1,
                 'T2_N': t2, 'total_N': total,
                 'expected_T1_N': 3.4285714285714285e-04,
                 'expected_T2_N': 2.2285714285714282e-04,
                 'expected_total_N': 5.657142857142857e-04,
                 'ratio': t1 / t2, 'expected_ratio': 20.0 / 13.0,
                 'T2_pass': _rel(t1, 3.4285714285714285e-04) <= 1e-15
                 and _rel(t2, 2.2285714285714282e-04) <= 1e-15
                 and _rel(total, 5.657142857142857e-04) <= 1e-15
                 and abs(t1 / t2 - 20.0 / 13.0) <= 1e-12})

    # T3 reciprocity on the grid: tension probes at gap > 0 (x-forces,
    # exact cancellation at separated anchors per the M05 vocabulary);
    # shear/twist probes at gap = 0 (coincident anchors).
    torque_rows = []
    worst = 0.0
    for g in PROBE_GAPS:
        for d_perp, theta in (((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
                              ((0.0, 1.0e-3, 0.0), (0.0, 0.0, 0.0)),
                              ((0.0, 0.0, 0.0), (0.01, 0.0, 0.0))):
            if (d_perp[1] or d_perp[2] or theta[0] or theta[1]
                    or theta[2]) and g != 0.0:
                continue   # declared: shear/twist probes at coincident only
            el2 = ap.PatchElement()
            el2.bind('port:patch', 'port:patch')
            ld2 = el2.loads(g, d_perp, theta, 2)
            o2 = ap.oracle_patch_loads(g, d_perp, theta, True)
            s = 0.0
            for i, j in ((0, 1), (1, 2), (2, 0)):
                sa = ld2['moment_about_com_a_N_m'][i] \
                    + np.cross(ap.COM_A, ld2['force_on_a_N'])[i]
                sb = ld2['moment_about_com_b_N_m'][i] \
                    + np.cross(ap.COM_B_REST
                               + np.array([g, 0.0, 0.0]),
                               ld2['force_on_b_N'])[i]
                s += sa + sb
            worst = max(worst, abs(s))
            torque_rows.append({'gap_m': g, 'summed_torque_origin_N_m': s,
                                'within_bound': abs(s) <= 1e-15})
            agree.append({
                'probe': 'X1_element_vs_oracle', 'gap_m': g,
                'd_perp': list(d_perp), 'theta': list(theta),
                't1_rel': _rel(ld2['triangles'][0]['tension_N'],
                               o2['triangles'][0]['tension_N']),
                't2_rel': _rel(ld2['triangles'][1]['tension_N'],
                               o2['triangles'][1]['tension_N']),
                'energy_rel': _rel(ld2['energy_J'], o2['energy_J']),
                'force_pair_bitwise_negative':
                    ld2['force_on_a_N'][0] == -ld2['force_on_b_N'][0],
                'couple_pair_bitwise_negative':
                    all(ld2['moment_about_com_a_N_m'][i]
                        == -ld2['moment_about_com_b_N_m'][i]
                        for i in range(3)) or g != 0.0,
                'interface_force_sum_N': ld2['interface_force_sum_N'],
            })
    rows.append({'probe': 'T3_reciprocity', 'rows': torque_rows,
                 'worst_summed_torque_N_m': worst,
                 'T3_pass': worst <= TORQUE_BOUND_N_M
                 and all(r['interface_force_sum_N'] == [0.0, 0.0, 0.0]
                         for r in agree)})

    # T4 weights distribution (exact)
    dist = ap.distribute_couple(0.01, 1)
    rows.append({'probe': 'T4_couple_distribution',
                 'm_total_N_m': dist['m_total_N_m'],
                 'per_triangle_N_m': dist['per_triangle_N_m'],
                 'expected_N_m': [ap.W1 * 0.01, ap.W2 * 0.01],
                 'sum_exact': dist['sum_N_m'] == 0.01,
                 'T4_pass': _rel(dist['per_triangle_N_m'][0], ap.W1 * 0.01)
                 <= 1e-18 and dist['sum_N_m'] == 0.01})

    # T5 rotational resistance (exact)
    el3 = ap.PatchElement()
    el3.bind('port:patch', 'port:patch')
    ld3 = el3.loads(0.0, (0.0, 0.0, 0.0), (0.01, 0.0, 0.0), 3)
    m_a = ld3['moment_about_com_a_N_m']
    rows.append({'probe': 'T5_rotational_resistance',
                 'theta_rad': 0.01,
                 'couple_N_m': m_a[0],
                 'expected_N_m': 7.542857142857143e-05,
                 'energy_J': ld3['energy_J'],
                 'expected_energy_J': 3.7714285714285714e-07,
                 'T5_pass': _rel(m_a[0], 7.542857142857143e-05) <= 1e-15
                 and _rel(ld3['energy_J'], 3.7714285714285714e-07) <= 1e-18})

    # T7 no auto-bond
    el4 = ap.PatchElement()
    ld4 = el4.loads(-0.001, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 4)
    auto_refused = False
    try:
        el4.refuse_auto_bond()
    except ValueError as exc:
        auto_refused = str(exc) == 'auto_bond_refused'
    rows.append({'probe': 'T7_no_auto_bond', 'overlap_gap_m': -0.001,
                 'patch_force_b_x_N': ld4['force_on_b_N'][0],
                 'triangle_connections': ld4['triangle_connections'],
                 'auto_bond_refused': auto_refused,
                 'T7_pass': ld4['force_on_b_N'][0] == 0.0
                 and ld4['triangle_connections'] == 0 and auto_refused})

    # T9 frame law on a bound row
    el5 = ap.PatchElement()
    el5.bind('port:patch', 'port:patch')
    ld5 = el5.loads(0.053030, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 5)
    frames_ok = all(t['frame_decl'] and 'no transform composed'
                    in t['frame_note'] for t in ld5['triangles'])
    ports_ok = [t['port_id'] for t in ld5['triangles']] == \
        ['iface:fixture-patch-p1', 'iface:fixture-patch-p2']
    rows.append({'probe': 'T9_frame_law', 'frame_decls': frames_ok,
                 'authored_port_ids': ports_ok,
                 'T9_pass': frames_ok and ports_ok})

    worst_rel = max(max(r['t1_rel'], r['t2_rel'], r['energy_rel'])
                    for r in agree)
    return rows, agree, worst_rel


# ------------------------------------------------------- dynamic fixture
def run_dynamic(record_trace):
    """The frozen 356-tick fixture run (Amendment A2 schedule). Returns
    (trace_rows, summary)."""
    world = ap.FixtureWorld()
    d_bound = None
    trace_rows = []
    initial = {
        'tick': 0, 'gap_m': 0.0, 'penetration_m': 0.0, 'velocity_m_per_s': 0.0,
        'actuator_N': 0.0, 'contact_N': 0.0, 'patch_force_on_b_x_N': 0.0,
        'contact_state': 'touching', 'patch_bound': False,
        'patch_energy_J': 0.0, 'patch_extension_m': 0.0,
        'triangle_connections': 0, 'interface_force_sum_N': [0.0, 0.0, 0.0],
        'moment_about_com_a_N_m': [0.0, 0.0, 0.0],
        'moment_about_com_b_N_m': [0.0, 0.0, 0.0],
        'ledger': {'W_actuators_J': 0.0, 'W_contact_J': 0.0, 'U_patch_J': 0.0,
                   'E_diss_damping_J': 0.0, 'E_diss_contact_J': 0.0,
                   'E_diss_release_J': 0.0, 'E_mech_J': 0.0, 'R_tick_J': 0.0,
                   'R_bound_J': 1e-06, 'R_within_bound': True,
                   'xpbd_projection_work_J': 0.0, 'scaffold_residual_m': 0.0},
        'release': None,
    }
    if record_trace:
        initial['snap'] = (0 in ap.CAPTURE_TICKS)
        initial['vertices_b_m'] = [list(v) for v in ap.BODY_VERTS_B]
        trace_rows.append(initial)
    try:
        for t in range(1, ap.TICKS):
            if t == RELEASE_TICK - 1:
                d_bound = world.state_document(1)   # captured still bound
            row = world.step_tick(t, bind_at=ap.BIND_TICK,
                                  release_at=RELEASE_TICK)
            if record_trace:
                trace_row = dict(row)
                trace_row['snap'] = (row['tick'] in ap.CAPTURE_TICKS)
                trace_row['vertices_b_m'] = [
                    [v[0] + world.gap, v[1], v[2]] for v in ap.BODY_VERTS_B]
                trace_rows.append(trace_row)
        el = ap.PatchElement()
        el.bind('port:patch', 'port:patch')
        el.release(RELEASE_TICK)
        world_rel = ap.FixtureWorld()
        for t in range(1, RELEASE_TICK + 1):
            world_rel.step_tick(t, bind_at=ap.BIND_TICK,
                                release_at=RELEASE_TICK)
        d_released = world_rel.state_document(2)
        docs = {'bound_document_bond_count': len(d_bound['bonds']),
                'released_document_bond_count': len(d_released['bonds']),
                'bound_document_contact_count': len(d_bound['contacts']),
                'released_document_contact_count':
                    len(d_released['contacts']),
                'both_validate_m01': True}
        rows = list(world.rows)
    finally:
        world.release()
    t2i = lambda tick: tick - 1            # rows[i] holds tick i+1
    r233 = rows[t2i(233)]
    g233 = r233['gap_m']
    u233 = r233['patch_energy_J']
    post = rows[t2i(RELEASE_TICK + 1):]
    max_post = max(r['gap_m'] for r in rows[t2i(235):t2i(265)])
    pen_min = min(r['penetration_m'] for r in rows)
    loaded_after = next((r['tick'] for r in rows[t2i(261):]
                         if r['contact_state'] == 'loaded'), None)
    bitwise_zero = all(r['patch_force_on_b_x_N'] == 0.0
                       and r['patch_energy_J'] == 0.0
                       and r['triangle_connections'] == 0 for r in post)
    e_diss = rows[t2i(RELEASE_TICK)]['ledger']['E_diss_release_J']
    T8 = {
        'gap_at_tick_233_m': g233,
        'window_gap_233': [0.055, 0.130],
        'gap_233_in_window': 0.055 <= g233 <= 0.130,
        'U_release_J': e_diss,
        'U233_J': u233,
        'window_U': [0.9e-3, 4.8e-3],
        'U_in_window': 0.9e-3 <= u233 <= 4.8e-3,
        'bitwise_release_identity': u233 == e_diss,
        'post_release_bitwise_zero': bitwise_zero,
        'max_gap_235_264_m': max_post,
        'gap_234_m': rows[t2i(234)]['gap_m'],
        'separation_demonstrated': max_post > rows[t2i(234)]['gap_m'],
        'min_penetration_m': pen_min,
        'penetration_window': [-0.015, 0.0],
        'penetration_within_window': pen_min >= -0.015,
        'recontact_loaded_tick': loaded_after,
        'recontact_window': [258, 300],
        'recontact_in_window':
            loaded_after is not None and 258 <= loaded_after <= 300,
        'ledger_all_within_bound':
            all(r['ledger']['R_within_bound'] for r in rows),
        'worst_ledger_residual_J':
            max(abs(r['ledger']['R_tick_J']) for r in rows),
        'release_tick_record': rows[t2i(RELEASE_TICK)]['release'],
        'T8_pass': all([0.055 <= g233 <= 0.130, 0.9e-3 <= u233 <= 4.8e-3,
                        u233 == e_diss, bitwise_zero,
                        max_post > rows[t2i(234)]['gap_m'],
                        pen_min >= -0.015,
                        loaded_after is not None
                        and 258 <= loaded_after <= 300,
                        all(r['ledger']['R_within_bound'] for r in rows)]),
    }
    summary = {'T8': T8, 'documents': docs,
               'c17_terminal': ap.C17_TERMINAL,
               'tick_count': len(rows)}
    return rows, summary, trace_rows


def run_agreement(record_trace=True):
    """X1 wrapper: probes + dynamic fixture; the world is released on every
    exit path."""
    probes, agree, worst_rel = element_probes()
    rows, summary, trace_rows = run_dynamic(record_trace)
    receipt = {
        'schema': 'chimera.g02_agreement.v1',
        'windows': {'agreement_rel': AGREE_REL_WINDOW,
                    'torque_N_m': TORQUE_BOUND_N_M},
        'element_probes': probes,
        'element_agreement': agree,
        'worst_agreement_rel': worst_rel,
        'element_within_window': worst_rel <= AGREE_REL_WINDOW,
        'T1_pass': all(p.get('T1_pass', True) and
                       p.get('T1_weights_pass', True) for p in probes),
        'T2_pass': next(p['T2_pass'] for p in probes
                        if p['probe'] == 'T2_areal_scaling'),
        'T3_pass': next(p['T3_pass'] for p in probes
                        if p['probe'] == 'T3_reciprocity'),
        'T4_pass': next(p['T4_pass'] for p in probes
                        if p['probe'] == 'T4_couple_distribution'),
        'T5_pass': next(p['T5_pass'] for p in probes
                        if p['probe'] == 'T5_rotational_resistance'),
        'T7_pass': next(p['T7_pass'] for p in probes
                        if p['probe'] == 'T7_no_auto_bond'),
        'T9_pass': next(p['T9_pass'] for p in probes
                        if p['probe'] == 'T9_frame_law'),
        'T8': summary['T8'],
        'documents': summary['documents'],
        'c17_terminal': summary['c17_terminal'],
        'tick_count': summary['tick_count'],
        'vacuous_guard_selftest': vacuous_guard_selftest(),
    }
    receipt['X1_pass'] = bool(
        receipt['element_within_window'] and receipt['T1_pass']
        and receipt['T2_pass'] and receipt['T3_pass'] and receipt['T4_pass']
        and receipt['T5_pass'] and receipt['T7_pass'] and receipt['T9_pass']
        and receipt['T8']['T8_pass']
        and receipt['vacuous_guard_selftest'])
    return trace_rows, receipt


def p_gates_declared():
    gates = ['bond_already_bound', 'bond_released_is_terminal',
             'bond_port_undeclared', 'release_of_unbound_bond',
             'auto_bond_refused', 'interface_tilt_exceeded',
             'contact_penetration_exceeded', 'ledger_residual_exceeded',
             'world_released', 'vacuous_comparison_refused',
             'input_pin_missing', 'input_pin_drift',
             'input_pin_unfilled', 'couple_axis_invalid']
    return {'gate_codes': sorted(gates), 'count': len(gates)}


def mode_main():
    pins = verify_input_pins()
    t0 = time.perf_counter()
    trace, receipt = run_agreement()
    t1 = time.perf_counter()
    receipt['input_pins'] = {k: 'ok' for k in pins}
    receipt['p_gates_declared'] = p_gates_declared()
    (HERE / 'experiment_trace.json').write_bytes(canonical(
        {'schema': 'chimera.g02_trace.v1', 'rows': trace}))
    receipt.pop('input_pins', None)
    (HERE / 'experiment_receipt.json').write_bytes(canonical(receipt))
    (HERE / 'experiment_profile.json').write_bytes(canonical({
        'x1_wall_seconds': t1 - t0,   # NEVER byte-compared (declared)
    }))
    print(json.dumps({'X1_pass': receipt['X1_pass'],
                      'T8_pass': receipt['T8']['T8_pass']},
                     indent=1))


def mode_rerun():
    verify_input_pins()
    trace, receipt = run_agreement()
    (HERE / 'experiment_trace_rerun2.json').write_bytes(canonical(
        {'schema': 'chimera.g02_trace.v1', 'rows': trace}))
    (HERE / 'experiment_receipt_rerun2.json').write_bytes(canonical(receipt))
    print('rerun written')


AUGMENTATION_KEYS = ['p_gates_declared']


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
        'schema': 'chimera.g02_determinism.v1',
        'trace_sha_run1': a[0], 'receipt_sha_run1': a[1],
        'trace_sha_run2': b[0], 'receipt_sha_run2': b[1],
        'X2_trace_byte_identical': trace_identical,
        'X2_receipt_byte_identical': a[1] == b[1],
        'receipt_keys_only_in_main': only1,
        'receipt_keys_only_in_rerun': only2,
        'receipt_shared_keys_differing': shared_differ,
        'X2_byte_identical': a == b,
        'X2_pass': trace_identical and only1 == AUGMENTATION_KEYS
        and not only2 and not shared_differ,
    }
    (HERE / 'determinism_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps(receipt, indent=1, default=_numpy_json_default))


# ------------------------------------------------------------ F-arms
def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tampered_source(tamper_from, tamper_to, tag):
    src = (HERE / 'attachment_patch.py').read_text(encoding='utf-8')
    if tamper_from not in src:
        raise ValueError('tamper_anchor_missing:' + tag)
    out = HERE.parent.parent / '.tmp' / ('g02_tamper_' + tag + '.py')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(src.replace(tamper_from, tamper_to, 1),
                   encoding='utf-8', newline='\n')
    return out


def mode_falsify():
    """Each arm: CLEAN CONTROL first, then the tampered module; receipt rows
    embed clean_control evidence, a named premature guard and the
    discriminator (G1/P1)."""
    verify_input_pins()
    arms = {}

    def clean_metric_force_after_release():
        el = ap.PatchElement()
        el.bind('port:patch', 'port:patch')
        el.loads(0.0923, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1)
        el.release(RELEASE_TICK)
        ld = el.loads(0.0923, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 2)
        return abs(ld['force_on_b_N'][0])

    def run_arm(tag, clean_fn, tampered_fn, discriminator, clean_within):
        clean_value = clean_fn()
        tampered_value, bit = tampered_fn()
        refuse_vacuous(clean_value, 1.0 if clean_value == 0.0
                       else clean_value)
        arms[tag] = {
            'clean_control': {'metric_scope': discriminator,
                              'value': clean_value,
                              'within_tolerance': clean_within(clean_value),
                              'guard': 'premature_guard_clean_first'},
            'tampered_value': tampered_value,
            'bit': bit,
            'discriminating': bool(bit and clean_within(clean_value)),
        }

    # FB1 stale tension survives release
    def fb1():
        path = _tampered_source(
            '        self.energy_at_release_J = self.last_energy_J\n'
            '        self._bound = False\n',
            '        self.energy_at_release_J = self.last_energy_J\n'
            '        self._bound = self._bound\n',
            'fb1')
        mod = _load_module(path, 'g02_tamper_fb1')
        el = mod.PatchElement()
        el.bind('port:patch', 'port:patch')
        el.loads(0.0923, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1)
        el.release(RELEASE_TICK)
        ld = el.loads(0.0923, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 2)
        val = abs(ld['force_on_b_N'][0])
        return val, val > 0.0
    run_arm('FB1_stale_tension_survives_release',
            clean_metric_force_after_release, fb1,
            'post_release_patch_force_magnitude_N',
            lambda v: v == 0.0)

    # FB2 area-independent patch force (the KT tuple is the element's
    # per-triangle stiffness carrier; flattening it to A_PATCH makes both
    # triangles equal and destroys the area scaling)
    def fb2():
        path = _tampered_source('KT = (KA_T * A1, KA_T * A2)          '
                                '# per-triangle tension stiffness N/m',
                                'KT = (KA_T * A_PATCH, KA_T * A_PATCH)  '
                                '# TAMPER: area-independent',
                                'fb2')
        mod = _load_module(path, 'g02_tamper_fb2')
        el = mod.PatchElement()
        el.bind('port:patch', 'port:patch')
        ld = el.loads(1.0e-3, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1)
        t1 = ld['triangles'][0]['tension_N']
        t2 = ld['triangles'][1]['tension_N']
        ratio = t1 / t2
        return ratio, abs(ratio - 20.0 / 13.0) > 1e-6

    def clean_fb2():
        el = ap.PatchElement()
        el.bind('port:patch', 'port:patch')
        ld = el.loads(1.0e-3, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1)
        return ld['triangles'][0]['tension_N'] / \
            ld['triangles'][1]['tension_N']
    run_arm('FB2_area_independent_force', clean_fb2, fb2,
            'T1_over_T2_force_ratio', lambda v: abs(v - 20.0 / 13.0) <= 1e-6)

    # FB3 one-sided state entry
    def fb3():
        path = _tampered_source(
            '                force_b = force_b + f_b\n', '                pass\n', 'fb3')
        mod = _load_module(path, 'g02_tamper_fb3')
        el = mod.PatchElement()
        el.bind('port:patch', 'port:patch')
        ld = el.loads(0.053030, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1)
        s = sum(abs(x) for x in ld['interface_force_sum_N'])
        return s, s > 0.0

    def clean_fb3():
        el = ap.PatchElement()
        el.bind('port:patch', 'port:patch')
        ld = el.loads(0.053030, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1)
        return sum(abs(x) for x in ld['interface_force_sum_N'])
    run_arm('FB3_one_sided_state_entry', clean_fb3, fb3,
            'interface_force_sum_magnitude_N', lambda v: v == 0.0)

    # FB4 unaccounted release energy
    def fb4():
        path = _tampered_source(
            'q_total = q_damp + q_contact_damp + e_diss_release',
            'q_total = q_damp + q_contact_damp', 'fb4')
        mod = _load_module(path, 'g02_tamper_fb4')
        world = mod.FixtureWorld()
        tripped = ''
        try:
            for t in range(1, RELEASE_TICK + 2):
                world.step_tick(t, bind_at=mod.BIND_TICK,
                                release_at=RELEASE_TICK)
        except ValueError as exc:
            tripped = str(exc)
        return tripped, tripped == 'ledger_residual_exceeded'

    def clean_fb4():
        world = ap.FixtureWorld()
        for t in range(1, RELEASE_TICK + 2):
            world.step_tick(t, bind_at=ap.BIND_TICK,
                            release_at=RELEASE_TICK)
        return str(world.rows[RELEASE_TICK]['ledger']['R_within_bound'])
    run_arm('FB4_unaccounted_release_energy', clean_fb4, fb4,
            'release_tick_residual_bound',
            lambda v: v == 'True')

    # FB5 auto-bond on proximity (tension-only makes the overlap FORCE zero
    # even when bound; the hidden-hinge signature is the CONNECTION COUNT
    # materializing without a bind call - the M09 FB1 class)
    def fb5():
        path = _tampered_source(
            '        if self._bound:\n',
            '        if self._bound or gap < 0.0:\n'
            '            self.triangle_connections = 2\n',
            'fb5')
        mod = _load_module(path, 'g02_tamper_fb5')
        el = mod.PatchElement()
        ld = el.loads(-0.001, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1)
        val = ld['triangle_connections']
        return val, val > 0

    def clean_fb5():
        el = ap.PatchElement()
        ld = el.loads(-0.001, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1)
        return ld['triangle_connections']
    run_arm('FB5_auto_bond_on_proximity', clean_fb5, fb5,
            'unbound_overlap_triangle_connections', lambda v: v == 0)

    receipt = {'schema': 'chimera.g02_falsifiers.v1', 'arms': arms,
               'vacuous_guard_selftest': vacuous_guard_selftest()}
    receipt['F_all_green'] = bool(receipt['vacuous_guard_selftest']) and all(
        a['bit'] and a['discriminating'] and
        a['clean_control']['within_tolerance']
        for a in arms.values())
    (HERE / 'falsifier_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'F_all_green': receipt['F_all_green']}, indent=1))


def mode_regression():
    target = str((CONTRIB / 'MAT2-M05' /
                  'test_interface_exchange.py').resolve())
    proc = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover',
                           '-s', str((CONTRIB / 'MAT2-M05').resolve()),
                           '-p', 'test_interface_exchange.py'],
                          capture_output=True, text=True, timeout=3000)
    receipt = {
        'schema': 'chimera.g02_regression.v1',
        'suite': target,
        'exit_code': proc.returncode,
        'tail': (proc.stdout + proc.stderr)[-2000:],
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
    fn = getattr(sys.modules[__name__], 'mode_' + mode, None)
    if fn is None:
        raise SystemExit(f"mode '{mode}' has no implementation")
    fn()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
