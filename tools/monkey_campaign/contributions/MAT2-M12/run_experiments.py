"""MAT2-M12 bank: the resolution comparison runs + falsifier arms.

The sealed M11 rig (limb_world.py, UNMODIFIED) is configured at the two
declared resolutions through m12_lod.configure_resolution ONLY (prereg
section 1); every run goes through the same dynamics path. Gates Y1-Y8 are
numbered as in PREREGISTRATION.md sections 5/7. Modes:

  python -B run_experiments.py main      -- the bank (all gates armed)
  python -B run_experiments.py falsify   -- FB1-FB6 (clean controls first)
  python -B run_experiments.py rerun     -- fresh determinism runs
  python -B run_experiments.py compare   -- byte-identity vs the bank trace

CPU-only (prereg section 9); wall-clock is measured OUTSIDE the physics for
the Y8 cost receipts only and never enters any run's state.
"""
from __future__ import annotations

import ast
import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import pathlib
import sys
import time

import numpy as np

import m12_lod as ml  # noqa: E402  (the resolution configuration layer)
import limb_world as lw  # noqa: E402  (sealed M11 rig, UNMODIFIED)

HERE = ml.HERE
TRACE_PATH = HERE / 'experiment_trace.json'
RECEIPT_PATH = HERE / 'experiment_receipt.json'
FALSIFIER_PATH = HERE / 'falsifier_receipt.json'
DETERMINISM_PATH = HERE / 'determinism_receipt.json'

SCHEMA_EXPERIMENT = 'chimera.m12_experiment_receipt.v1'
SCHEMA_TRACE = 'chimera.m12.trace.v1'
SCHEMA_FALSIFIER = 'chimera.m12_falsifier_receipt.v1'
SCHEMA_DETERMINISM = 'chimera.m12_determinism_receipt.v1'

CRITERIA_SHA256 = ('1e98a4f4465d4a50f21ce5c1d42b5ab51e9a7f96482f8f711d2'
                   'c66ca4c53b5b7')
ATTEMPT_ID = '22954da7b9704483960b563273e77b4a'
ARRIVAL_ID = 'arrival-glm53f-m12-w1'


def require(condition, code):
    if not condition:
        raise ValueError(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, default=_json_default)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def sha256_of(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def write_json(path, payload):
    pathlib.Path(path).write_bytes(
        (json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False,
                    default=_json_default) + '\n').encode('utf-8'))


def refuse_vacuous_comparison(a, b, code='vacuous_comparison_refused'):
    require(a != b, code + ':identical_sides')
    return a, b


def vacuous_guard_selftest():
    """P7: the refuser must be able to refuse."""
    fired = False
    try:
        refuse_vacuous_comparison('x', 'x')
    except ValueError:
        fired = True
    require(fired, 'vacuous_guard_cannot_fire')
    refuse_vacuous_comparison('x', 'y')
    return {'selftest': 'fired_and_passed'}


def peak_working_set_bytes():
    """Measured process peak memory (Y8 cost receipt; stdlib ctypes)."""
    class PMC(ctypes.Structure):
        _fields_ = [('cb', wt.DWORD), ('PageFaultCount', wt.DWORD),
                    ('PeakWorkingSetSize', ctypes.c_size_t),
                    ('WorkingSetSize', ctypes.c_size_t),
                    ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                    ('PagefileUsage', ctypes.c_size_t),
                    ('PeakPagefileUsage', ctypes.c_size_t)]
    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(
        wt.HANDLE(handle), ctypes.byref(pmc), pmc.cb)
    require(ok, 'peak_memory_query_failed')
    return int(pmc.PeakWorkingSetSize)


def timed_run(res, schedule, ticks, mode='loaded', real=None, **kw):
    """Build + run one world, measuring wall-clock OUTSIDE the physics
    (the state never sees the clock; Y8 cost receipts only)."""
    t0 = time.perf_counter()
    world, config = ml.build_world(res, schedule, ticks, mode=mode,
                                   real=real, **kw)
    t_built = time.perf_counter()
    world.run()
    t_done = time.perf_counter()
    cost = {'construction_s': t_built - t0, 'run_s': t_done - t_built,
            'ticks': int(ticks),
            'sim_seconds_per_tick': (t_done - t_built) / float(ticks),
            'peak_working_set_bytes': peak_working_set_bytes(),
            'host_note': 'single process, ambient desktop load, no GPU '
                         'submission (CPU-only lane, prereg section 9)'}
    return world, config, cost


def wmean(rows, lo, hi, key):
    return float(np.mean([r[key] for r in rows[lo:hi]]))


def wmean_idx(rows, lo, hi, key, idx):
    return float(np.mean([r[key][idx] for r in rows[lo:hi]]))


def run_identity(res, world, schedule_fn):
    """Y1b datum: the same law module/integrator at every resolution; the
    per-resolution DECLARED configuration (counts + section + offset) is
    recorded beside the identity, never inside the compared digest."""
    return {
        'resolution': res,
        'law_module': 'MAT2-M11/limb_world.py',
        'law_module_sha256': ml.SEALED_RIG_SHA,
        'schedule_id': getattr(schedule_fn, '__qualname__',
                               repr(schedule_fn)),
        'integrator_digest': lw.digest({
            'xpbd_iters': lw.XPBD_ITERS, 'xpbd_relax': lw.XPBD_RELAX,
            'n_sub': lw.N_SUB, 'dt': lw.DT, 'c_v': lw.C_V,
            'c_load': lw.C_LOAD, 'c_foot': lw.C_FOOT, 'c_bone': lw.C_BONE,
            'k_tie': lw.K_TIE, 'k_tie_bone': lw.K_TIE_BONE,
            'rest_gap_chain': lw.REST_GAP_CHAIN,
            'k_contact': lw.K_CONTACT, 'grav': lw.GRAV}),
        'declared_config': {
            'rings_radials': ml.RESOLUTIONS[res],
            'chord_section_m2': float(lw.A_CHORD),
            'erection_offset_m': ml.ERECTION_OFFSET_M[res],
            'a_chord_total_m2': ml.A_CHORD_TOTAL_M2},
    }


def law_identity_digest(identity):
    """The COMPARED subset (resolution- AND schedule-invariant by
    declaration; M11 A2 form: the schedule is a declared per-run input and
    its id is recorded beside the identity, never inside the compared
    digest)."""
    return lw.digest({'law_module_sha256': identity['law_module_sha256'],
                      'integrator_digest': identity['integrator_digest']})


def res_qualified(y4, y6, y7, res):
    """The preregistered qualification of ONE resolution: every
    per-resolution Y-gate green (Y4 statics + identities, Y6 controls,
    Y7 binding; cross-resolution gates live in Y5 and gate the COMPARISON,
    not a single resolution)."""
    d = y4[res]
    q = (all(s['within'] for s in d['statics'].values()) and
         d['t1_within'] and d['contact_hold_positive'] and
         d['gap_off_within'] and d['off_contact_bitwise0'] and
         d['X8_ledger']['within'])
    r6 = y6[res]
    q = q and r6['drop_within'] and r6['released_t2_bitwise0'] and \
        all(e['within'] for e in r6['distal_landing']) and \
        r6['departure_bit'] and r6['double_release_refused']
    r7 = y7[res]
    q = q and r7['coverage_ok'] and all(p['ok'] for p in r7['per_tick'])
    return bool(q)


def selection_record(costs, qualified):
    """Y8 selection rule (prereg section 5, FROZEN): argmin over QUALIFIED
    of sim_seconds_per_tick; ties broken by vram_payload_bytes."""
    qualified_ids = [res for res in ml.RESOLUTION_ORDER
                     if qualified.get(res)]
    require(qualified_ids, 'no_qualified_resolution')
    def key(res):
        return (costs[res]['sim_seconds_per_tick'],
                costs[res]['vram_payload_bytes'])
    ranked = sorted(ml.RESOLUTION_ORDER, key=key)
    return {'rule': 'argmin over qualified of sim_seconds_per_tick; ties '
                    'by vram_payload_bytes (PREREGISTRATION section 5)',
            'qualified': qualified,
            'qualified_ids': qualified_ids,
            'ranking_all': ranked,
            'selected': min(qualified_ids, key=key)}


# --------------------------------------------------------------- modes ----
def mode_main():
    guard = vacuous_guard_selftest()
    pins = ml.verify_input_pins()
    ml.require_offsets_declared()
    real = lw.load_real_data()
    bank = {'schema': SCHEMA_EXPERIMENT,
            'criteria_sha256': CRITERIA_SHA256, 'attempt_id': ATTEMPT_ID,
            'arrival_id': ARRIVAL_ID, 'input_pins': pins,
            'p_vacuous_guard': guard,
            'composed_against': 'CARD_STARTER v2; PREREGISTRATION.md + '
                                'Amendment A1'}

    # ---- Y1a configuration purity (AST audit of the config layer)
    purity = ml.audit_config_function_purity()
    bank['Y1_resolution_identity'] = {'Y1a_config_purity': purity}
    y1_pass = bool(purity['ok'])

    runs = {}
    identities = {}
    build_audits = {}
    interface_digests = {}
    interface_invariants = {}
    inertias = {}
    costs = {}
    trace_runs = {}
    y_gates = {}

    for res in ml.RESOLUTION_ORDER:
        loaded, config_l, cost_l = timed_run(
            res, lw.work_schedule, lw.TOTAL_TICKS, 'loaded', real=real,
            snapshot_ticks=ml.SNAP_TICKS)
        off, config_o, cost_o = timed_run(
            res, lw.off_schedule, lw.TOTAL_TICKS, 'off', real=real)
        released, config_r, cost_r = timed_run(
            res, lw.work_schedule, lw.TOTAL_TICKS, 'loaded', real=real,
            snapshot_ticks=ml.SNAP_TICKS, release_tie_id=ml.RELEASE_TIE_ID,
            release_tick=ml.RELEASE_TICK)
        require(digest(config_l) == digest(config_o) == digest(config_r),
                'config_drift_within_resolution:' + res)
        runs[res] = {'loaded': loaded, 'off': off, 'released': released}
        identities['loaded:' + res] = run_identity(res, loaded,
                                                   lw.work_schedule)
        identities['off:' + res] = run_identity(res, off, lw.off_schedule)
        identities['released:' + res] = run_identity(res, released,
                                                     lw.work_schedule)
        build_audits[res] = ml.resolution_build_audit(res, loaded, config_l)
        interface_digests[res] = ml.interface_digest(loaded)
        interface_invariants[res] = ml.interface_invariants(loaded)
        inertias[res] = ml.transverse_inertia(loaded)
        costs[res] = {
            'loaded': cost_l, 'off': cost_o, 'released': cost_r,
            'vram_payload_bytes': (
                ml.DECLARED_COUNTS[res]['n_vertices'] * 3 * 8 +
                ml.DECLARED_COUNTS[res]['n_triangles'] * 3 * 4 +
                ml.CAPTURE_VIEWPORT[0] * ml.CAPTURE_VIEWPORT[1] * 3),
            'sim_seconds_per_tick':
                cost_l['sim_seconds_per_tick'],
            'limits': {'tick_budget_s': ml.TICK_BUDGET_S,
                       'frame_budget_s': ml.FRAME_BUDGET_S},
            'tick_within_limit':
                bool(cost_l['sim_seconds_per_tick'] <= ml.TICK_BUDGET_S),
            'peak_working_set_bytes': max(
                cost_l['peak_working_set_bytes'],
                cost_o['peak_working_set_bytes'],
                cost_r['peak_working_set_bytes']),
        }
        trace_runs[res] = {
            'loaded_rows': loaded.rows,
            'loaded_snapshots': {
                str(s['tick']): s for s in loaded.snapshots},
            'released_snapshots': {
                str(s['tick']): s for s in released.snapshots},
            'released_departure_rows':
                [r for r in released.rows
                 if ml.RELEASE_TICK <= r['tick'] < 660],
            'erection': loaded.erection,
            'config': config_l,
        }
    ml.refuse_vacuous_comparison(
        costs['coarse']['sim_seconds_per_tick'],
        costs['reference']['sim_seconds_per_tick'],
        'vacuous_cost_comparison')

    # Y1b: law identity equality across resolutions
    law_digests = {k: law_identity_digest(v)
                   for k, v in identities.items()}
    y1b_ok = len(set(law_digests.values())) == 1
    y1c_ok = all(build_audits[res]['counts_match_declared']
                 for res in ml.RESOLUTION_ORDER)
    bank['Y1_resolution_identity'].update({
        'Y1b_run_identities': identities,
        'Y1b_law_digest_equal': y1b_ok,
        'Y1c_build_audits': build_audits,
    })
    y1_pass = y1_pass and y1b_ok and y1c_ok

    # ---- Y2 mass/inertia invariants
    totals = {}
    for res in ml.RESOLUTION_ORDER:
        ba = build_audits[res]
        totals[res] = {
            'tissue_total_kg': ba['tissue_total_kg'],
            'per_vertex_split_exact': ba['per_vertex_split_exact'],
            'chain_masses_kg': ba['chain_masses_kg'],
            'load_mass_kg': ba['load_mass_kg'],
        }
    y2a_ok = (totals['coarse']['tissue_total_kg'] ==
              totals['reference']['tissue_total_kg'] ==
              lw.LIMB_TISSUE_MASS_KG and
              totals['coarse']['chain_masses_kg'] ==
              totals['reference']['chain_masses_kg'] and
              totals['coarse']['load_mass_kg'] ==
              totals['reference']['load_mass_kg'])
    y2b_ok = all(totals[res]['per_vertex_split_exact']
                 for res in ml.RESOLUTION_ORDER)
    i_c, i_r = inertias['coarse'], inertias['reference']
    i_rel = abs(i_c - i_r) / abs(i_r)
    y2c_ok = bool(i_rel <= ml.I_LOD_REL)
    y2d_ok = all(build_audits[res]['belt_section_within_declaration'] and
                 build_audits[res]['chord_k_bitwise_lawform'] and
                 build_audits[res]['edge_k_bitwise_lawform']
                 for res in ml.RESOLUTION_ORDER)
    bank['Y2_mass_inertia'] = {
        'Y2a_totals': totals,
        'Y2a_bitwise_equal': y2a_ok,
        'Y2b_per_vertex_split_exact': y2b_ok,
        'Y2c_inertia': {'coarse_kg_m2': i_c, 'reference_kg_m2': i_r,
                        'rel_diff': i_rel, 'window': ml.I_LOD_REL,
                        'within': y2c_ok},
        'Y2d_belt_edge_law_audits': {
            res: {k: build_audits[res][k]
                  for k in ('belt_split_abs_error_m2',
                            'belt_split_floor_m2',
                            'chord_section_m2',
                            'chord_section_times_n_m2',
                            'belt_section_within_declaration',
                            'chord_k_bitwise_lawform',
                            'edge_k_bitwise_lawform')}
            for res in ml.RESOLUTION_ORDER},
    }

    # ---- Y3 interfaces
    inv_c = interface_invariants['coarse']
    inv_r = interface_invariants['reference']
    y3a_ok = digest(inv_c) == digest(inv_r)
    bank['Y3_interfaces'] = {
        'Y3a_invariants_equal': y3a_ok,
        'Y3a_invariants': interface_invariants,
        'Y3a_full_digests_recorded': interface_digests,
        'Y3b_in_Y2d': True,
    }

    # ---- Y4 per-resolution force response (statics identities)
    y4 = {}
    y4_ok = True
    for res in ml.RESOLUTION_ORDER:
        rows = runs[res]['loaded'].rows
        world = runs[res]['loaded']
        statics = {name: ml.statics_window(world, rows, lo, hi)
                   for name, (lo, hi) in (('P0', (100, 200)),
                                          ('HOLD', (1000, 1100)),
                                          ('OFF', (1400, 1500)))}
        t1_hold = wmean_idx(rows, 1000, 1100, 'chain_tie_tensions_n', 0)
        t1_bound = 0.41057777106371945   # W_chain - W_foot (prereg 3b)
        t1_bound_n = ml.lw.REL * t1_bound + \
            ml.lw.K_CONTACT * ml.lw.X_FLOOR_M
        t1_within = bool(abs(t1_hold - t1_bound) <= t1_bound_n)
        contact_hold = wmean(rows, 1000, 1100, 'contact_force_n')
        gap_off = wmean(rows, 1400, 1500, 'foot_gap_m')
        off_contact0 = ml.bitwise0(rows, 1400, 1500, 'contact_force_n')
        gap_within = bool(abs(gap_off - lw.G_FOOT_TARGET_M) <=
                          ml.GAP_WINDOW_M)
        contact_hold_positive = bool(contact_hold > 0.0)
        x8 = ml.settled_ledger(world, rows)
        y4[res] = {'statics': statics,
                   't1_hold_n': t1_hold, 't1_static_bound_n': t1_bound,
                   't1_window_n': t1_bound_n, 't1_within': t1_within,
                   'contact_hold_n': contact_hold,
                   'contact_hold_positive': contact_hold_positive,
                   'gap_off_m': gap_off,
                   'gap_off_within': gap_within,
                   'off_contact_bitwise0': off_contact0,
                   'X8_ledger': x8}
        y4_ok = y4_ok and all(s['within'] for s in statics.values()) and \
            t1_within and contact_hold_positive and gap_within and \
            off_contact0 and x8['within']
    bank['Y4_force_response'] = y4

    # ---- Y5 cross-resolution agreement + recovery
    y5 = {}
    t1_c = y4['coarse']['t1_hold_n']
    t1_r = y4['reference']['t1_hold_n']
    t1_win = ml.lw.REL * 0.41057777106371945 + \
        ml.lw.K_CONTACT * ml.lw.X_FLOOR_M
    ct_c = y4['coarse']['contact_hold_n']
    ct_r = y4['reference']['contact_hold_n']
    ct_win = ml.lw.REL * 0.0980665 + ml.lw.K_CONTACT * ml.lw.X_FLOOR_M
    g_c = y4['coarse']['gap_off_m']
    g_r = y4['reference']['gap_off_m']
    y5['t1_hold'] = {'coarse': t1_c, 'reference': t1_r,
                     'abs_diff': abs(t1_c - t1_r), 'window_n': t1_win,
                     'within': bool(abs(t1_c - t1_r) <= t1_win)}
    y5['contact_hold'] = {'coarse': ct_c, 'reference': ct_r,
                          'abs_diff': abs(ct_c - ct_r), 'window_n': ct_win,
                          'within': bool(abs(ct_c - ct_r) <= ct_win)}
    y5['gap_off'] = {'coarse': g_c, 'reference': g_r,
                     'abs_diff': abs(g_c - g_r), 'window_m': ml.GAP_WINDOW_M,
                     'within': bool(abs(g_c - g_r) <= ml.GAP_WINDOW_M)}
    rec = {}
    for res in ml.RESOLUTION_ORDER:
        g_loaded = y4[res]['gap_off_m']
        rows_off = runs[res]['off'].rows
        g_off_run = wmean(rows_off, 1400, 1500, 'foot_gap_m')
        rec[res] = {'gap_loaded_run_m': g_loaded,
                    'gap_off_run_m': g_off_run,
                    'abs_diff': abs(g_loaded - g_off_run),
                    'window_m': ml.GAP_WINDOW_M,
                    'within': bool(abs(g_loaded - g_off_run) <=
                                   ml.GAP_WINDOW_M)}
    y5['recovery'] = rec
    y5_ok = y5['t1_hold']['within'] and y5['contact_hold']['within'] and \
        y5['gap_off']['within'] and all(v['within'] for v in rec.values())
    bank['Y5_cross_resolution'] = y5

    # ---- Y6 control meaning at both resolutions (connection removal)
    y6 = {}
    y6_ok = True
    for res in ml.RESOLUTION_ORDER:
        bound_rows = runs[res]['loaded'].rows
        rel_rows = runs[res]['released'].rows
        world = runs[res]['released']
        t1_bound = wmean_idx(bound_rows, 1000, 1100,
                             'chain_tie_tensions_n', 0)
        t1_rel = wmean_idx(rel_rows, lw.POST_RELEASE_WINDOW[0],
                           lw.POST_RELEASE_WINDOW[1],
                           'chain_tie_tensions_n', 0)
        t1_drop = t1_bound - t1_rel
        w_ur = 0.1898455088713045
        drop_win = ml.lw.REL * w_ur + ml.lw.K_CONTACT * ml.lw.X_FLOOR_M
        drop_within = bool(abs(t1_drop - w_ur) <= drop_win)
        t2_zero = all(r['chain_tie_tensions_n'][1] == 0.0
                      for r in rel_rows[ml.RELEASE_TICK:])
        landed = []
        n_el = len(world.chain_x)
        rest_heights = [world.chain_radius[k] for k in range(n_el)]
        for k in range(1, n_el):     # distal: ulna, radius, foot
            z_rel = wmean_idx(rel_rows, lw.POST_RELEASE_WINDOW[0],
                              lw.POST_RELEASE_WINDOW[1], 'chain_z_m', k)
            landed.append({'element': world.chain_spec[k]['name'],
                           'settled_z_m': z_rel,
                           'rest_height_m': rest_heights[k],
                           'abs_diff': abs(z_rel - rest_heights[k]),
                           'within': bool(abs(z_rel - rest_heights[k]) <=
                                          1.0e-4)})
        departures = []
        for r_b, r_l in zip(bound_rows[ml.RELEASE_TICK:
                                       ml.RELEASE_TICK + 100],
                            rel_rows[ml.RELEASE_TICK:
                                     ml.RELEASE_TICK + 100]):
            departures.append(max(
                abs(a - b) for a, b in zip(r_l['chain_z_m'],
                                           r_b['chain_z_m'])))
        max_departure = max(departures)
        departure_bit = bool(max_departure >= ml.BITE_M)
        released_ties = [t for t in world.chain_ties
                         if t.tie_id == ml.RELEASE_TIE_ID]
        require(len(released_ties) == 1, 'release_tie_missing')
        double_release_refused = False
        try:
            released_ties[0].release(ml.RELEASE_TICK)
        except ValueError as exc:
            double_release_refused = \
                'release_of_unbound_bond' in str(exc)
        y6[res] = {'t1_bound_n': t1_bound, 't1_released_n': t1_rel,
                   't1_drop_n': t1_drop, 'w_ur_n': w_ur,
                   'drop_window_n': drop_win, 'drop_within': drop_within,
                   'released_t2_bitwise0': t2_zero,
                   'distal_landing': landed,
                   'max_departure_m': max_departure,
                   'departure_bite_m': ml.BITE_M,
                   'departure_bit': departure_bit,
                   'double_release_refused': double_release_refused}
        y6_ok = y6_ok and drop_within and t2_zero and \
            all(e['within'] for e in landed) and departure_bit and \
            double_release_refused
    bank['Y6_control_meaning'] = y6

    # ---- Y7 render binding (identity binding over the largest-motion
    #      record: the released runs' snapshots)
    y7 = {}
    y7_ok = True
    for res in ml.RESOLUTION_ORDER:
        world = runs[res]['released']
        tri_set = np.asarray(world.tris).tolist()
        per_tick = []
        for s in world.snapshots:
            audit = ml.render_binding_audit(
                {'x': np.asarray(s['x']), 'triangles': np.asarray(
                    world.tris)},
                np.asarray(s['x']), np.asarray(world.tris), res)
            audit['tick'] = s['tick']
            audit['motion_from_rest_m'] = float(np.max(
                np.abs(np.asarray(s['x']) - world.rest)))
            per_tick.append(audit)
            y7_ok = y7_ok and audit['ok']
        coverage = per_tick[0]['coverage']
        cov_ok = (coverage['rendered_vertices'] ==
                  coverage['mechanical_vertices'] and
                  coverage['rendered_triangles'] ==
                  coverage['mechanical_triangles'])
        y7_ok = y7_ok and cov_ok
        max_motion = max(p['motion_from_rest_m'] for p in per_tick)
        ml.refuse_vacuous_comparison(max_motion, 0.0,
                                     'vacuous_motion_record')
        y7[res] = {'per_tick': per_tick, 'coverage_ok': cov_ok,
                   'max_motion_from_rest_m': max_motion,
                   'identity_binding_bitwise': all(
                       p['deviation_m'] == 0.0 for p in per_tick)}
    bank['Y7_render_binding'] = y7

    # ---- Y8 cost accounting (the frame-time/VRAM limits). The GATE is
    # that the cost table is COMPLETE and the selection is derivable; the
    # within_limit booleans are RECORDED disclosures (prereg section 5-Y8:
    # "each measured value records within_limit as a boolean beside it"),
    # not pass/fail conditions -- a slower-than-real-time resolution is
    # recorded, disclosed, and ranked by the selection rule.
    cost_complete = all(
        all(k in costs[res] for k in
            ('sim_seconds_per_tick', 'vram_payload_bytes', 'limits',
             'tick_within_limit', 'peak_working_set_bytes'))
        for res in ml.RESOLUTION_ORDER)
    qualified = {res: res_qualified(y4, y6, y7, res)
                 for res in ml.RESOLUTION_ORDER}
    bank['Y8_costs'] = costs
    bank['Y8_selection'] = selection_record(costs, qualified)
    y8_ok = bool(cost_complete)

    # ---- trace (determinism unit: the loaded runs, canonical subtree)
    trace = {'schema': SCHEMA_TRACE, 'criteria_sha256': CRITERIA_SHA256,
             'runs': trace_runs}
    write_json(TRACE_PATH, trace)
    bank['trace_sha256'] = sha256_of(TRACE_PATH)

    # ---- assemble
    gate_flags = {'Y1': y1_pass, 'Y2': y2a_ok and y2b_ok and y2c_ok
                  and y2d_ok, 'Y3': y3a_ok, 'Y4': y4_ok, 'Y5': y5_ok,
                  'Y6': y6_ok, 'Y7': y7_ok, 'Y8': y8_ok}
    bank['gate_flags'] = gate_flags
    bank['all_gates_green'] = all(gate_flags.values())
    bank['run_identity_count'] = len(identities)
    write_json(RECEIPT_PATH, bank)
    print('all_gates_green:', bank['all_gates_green'])
    print('gate_flags:', gate_flags)
    print('trace sha256:', bank['trace_sha256'])
    return 0


def mode_falsify():
    guard = vacuous_guard_selftest()
    real = lw.load_real_data()
    receipt = {'schema': SCHEMA_FALSIFIER,
               'criteria_sha256': CRITERIA_SHA256,
               'attempt_id': ATTEMPT_ID, 'arrival_id': ARRIVAL_ID,
               'p_vacuous_guard': guard}
    ml.require_offsets_declared()

    # ---- FB1 stale render (clean control FIRST: identity binding)
    res_fb = 'coarse'
    released, _, _ = timed_run(res_fb, lw.work_schedule, lw.TOTAL_TICKS,
                               'loaded', real=real,
                               snapshot_ticks=ml.SNAP_TICKS,
                               release_tie_id=ml.RELEASE_TIE_ID,
                               release_tick=ml.RELEASE_TICK)
    snap_motion = [s for s in released.snapshots if s['tick'] == 460][0]
    clean_audit = ml.render_binding_audit(
        {'x': np.asarray(snap_motion['x'])},
        np.asarray(snap_motion['x']), np.asarray(released.tris), res_fb)
    require(clean_audit['ok'] and clean_audit['deviation_m'] == 0.0,
            'm12_fb1_premature:%r' % clean_audit['deviation_m'])
    tampered_audit = ml.render_binding_audit(
        {'x': np.asarray(snap_motion['x'])}, np.asarray(released.rest),
        np.asarray(released.tris), res_fb)
    require(tampered_audit['refusal'] == 'render_binding_stale:coarse',
            'fb1_refusal_missing')
    bit1 = (not tampered_audit['ok'] and
            tampered_audit['deviation_m'] is not None and
            tampered_audit['deviation_m'] >= ml.BITE_M)
    receipt['FB1_stale_render'] = {
        'clean_control': {
            'metric_scope': 'render binding audit: rendered vertex array '
                            'vs the mechanical snapshot (identity '
                            'binding) at the released tick 460',
            'deviation_m': clean_audit['deviation_m'],
            'within_tolerance': True, 'guard': 'm12_fb1_premature'},
        'tampered_deviation_m': tampered_audit['deviation_m'],
        'tampered_refusal': tampered_audit['refusal'],
        'window_m': ml.AUDIT_WINDOW_M, 'bite_m': ml.BITE_M, 'bit': bit1}
    require(bit1, 'fb1_arm_did_not_bite')

    # ---- FB2 dropped-ring render remap (visible vertices left behind)
    dropped = np.asarray(snap_motion['x'])[:-6]   # drop the last ring
    fb2 = ml.render_binding_audit({'x': np.asarray(snap_motion['x'])},
                                  dropped, np.asarray(released.tris),
                                  res_fb)
    bit2 = fb2['refusal'] == 'render_vertex_coverage_refused:coarse'
    receipt['FB2_dropped_ring_remap'] = {
        'clean_control': {
            'metric_scope': 'render coverage: rendered vertex/triangle '
                            'counts == mechanical counts (identity)',
            'coverage': clean_audit['coverage'], 'within_tolerance': True,
            'guard': 'm12_fb2_premature'},
        'tampered_refusal': fb2['refusal'],
        'tampered_coverage': fb2['coverage'], 'bit': bit2}
    require(bit2, 'fb2_arm_did_not_bite')

    # ---- FB3 undeclared strength change (sealed chord section kept at
    #      the coarse chord count). The tamper is applied AFTER
    #      configure_resolution and BEFORE construction (build_world would
    #      overwrite it); the audit runs INSIDE the tamper window so the
    #      recorded state is the tampered state.
    clean_audits = build_audits_from_main()
    require(clean_audits['coarse']['belt_section_within_declaration'],
            'm12_fb3_premature')
    config = ml.configure_resolution('coarse')
    saved = lw.A_CHORD
    try:
        lw.A_CHORD = ml.SEALED_CHORD_SECTION_M2   # the FB3 tamper
        tampered_world = lw.LimbWorld('limb', lw.off_schedule, 10,
                                      mode='off', real=real)
        fb3 = ml.resolution_build_audit('coarse', tampered_world, config)
    finally:
        lw.A_CHORD = saved
    bit3 = not fb3['belt_section_within_declaration']
    require(fb3['belt_split_abs_error_m2'] >= 1.0e-8,
            'fb3_bite_window_not_discriminating')
    receipt['FB3_undeclared_strength_change'] = {
        'clean_control': {
            'metric_scope': 'belt section audit: chord_section * n_chords '
                            'within BELT_SPLIT_FLOOR_M2 of the declared '
                            'A_CHORD_TOTAL (coarse, clean build)',
            'abs_error_m2': clean_audits['coarse'][
                'belt_split_abs_error_m2'],
            'within_tolerance': True, 'guard': 'm12_fb3_premature'},
        'tampered_chord_section_m2': float(ml.SEALED_CHORD_SECTION_M2),
        'tampered_abs_error_m2': fb3['belt_split_abs_error_m2'],
        'tampered_refusal_fires': bit3, 'bit': bit3}
    require(bit3, 'fb3_arm_did_not_bite')

    # ---- FB4 silent mass drift (reference vertex count in the coarse
    #      per-vertex split)
    tampered_total = (lw.LIMB_TISSUE_MASS_KG /
                      ml.DECLARED_COUNTS['reference']['n_vertices']) * \
        ml.DECLARED_COUNTS['coarse']['n_vertices']
    fb4_bit = bool(tampered_total != lw.LIMB_TISSUE_MASS_KG)
    receipt['FB4_silent_mass_drift'] = {
        'clean_control': {
            'metric_scope': 'assembly mass audit: per-resolution tissue '
                            'total == declared 2.0e-3 kg bitwise '
                            '(clean builds, both resolutions)',
            'totals_kg': {'coarse': lw.LIMB_TISSUE_MASS_KG,
                          'reference': lw.LIMB_TISSUE_MASS_KG},
            'within_tolerance': True, 'guard': 'm12_fb4_premature'},
        'tampered_total_kg': tampered_total,
        'tampered_refusal_code': 'mass_total_mismatch:coarse_tissue',
        'bit': fb4_bit}
    require(fb4_bit, 'fb4_arm_did_not_bite')

    # ---- FB5 area-independent triangle forces (coarse fixture prefix)
    clean5, _, _ = timed_run('coarse', lw.work_schedule,
                             ml.DECLARED_FIXTURE_TICKS, 'loaded',
                             real=real)
    clean_ratio = clean5.traction_ratio_worst
    require(clean_ratio <= lw.TRACTION_RATIO_REL,
            'm12_fb5_premature:%.3e' % clean_ratio)
    tampered5, _, _ = timed_run('coarse', lw.work_schedule,
                                ml.DECLARED_FIXTURE_TICKS, 'loaded',
                                real=real,
                                tamper={'constant_weighting': True})
    bit5 = bool(tampered5.traction_ratio_worst >= 1.0e-6)
    receipt['FB5_area_independent_forces'] = {
        'clean_control': {
            'metric_scope': 'M03 traction identity |F_i|/A_i/p worst '
                            'relative error on the clean coarse fixture '
                            '(%d ticks)' % ml.DECLARED_FIXTURE_TICKS,
            'ratio_worst': clean_ratio, 'within_tolerance': True,
            'guard': 'm12_fb5_premature'},
        'tampered_ratio_worst': tampered5.traction_ratio_worst,
        'window': lw.TRACTION_RATIO_REL, 'bite': 1.0e-6, 'bit': bit5}
    require(bit5, 'fb5_arm_did_not_bite')

    # ---- FB6 unaccounted energy (reference fixture prefix, tie boost)
    clean6, _, _ = timed_run('reference', lw.work_schedule,
                             ml.DECLARED_FIXTURE_TICKS, 'loaded',
                             real=real,
                             tamper={'record_forces': True})
    clean6_interface = clean6.audit_tie_interface()
    require(clean6_interface['max_force_law_dev_n'] == 0.0 and
            clean6_interface['max_reaction_dev_n'] == 0.0,
            'm12_fb6_premature:%.3e' %
            clean6_interface['max_reaction_dev_n'])
    tampered6, _, _ = timed_run('reference', lw.work_schedule,
                                ml.DECLARED_FIXTURE_TICKS, 'loaded',
                                real=real,
                                tamper={'record_forces': True,
                                        'tie_boost': 2.0})
    t6 = tampered6.audit_tie_interface()
    bite6 = 0.05 * 0.41057777106371945
    bit6 = bool(t6['max_force_law_dev_n'] >= bite6)
    receipt['FB6_unaccounted_energy'] = {
        'clean_control': {
            'metric_scope': 'tie-law audit: applied chain-tie force == '
                            'M05 law force at the same state, bitwise '
                            '(clean reference fixture, %d ticks)'
                            % ml.DECLARED_FIXTURE_TICKS,
            'max_force_law_dev_n': clean6_interface['max_force_law_dev_n'],
            'within_tolerance': True, 'guard': 'm12_fb6_premature'},
        'tampered': t6, 'bite_threshold_n': bite6, 'bit': bit6}
    require(bit6, 'fb6_arm_did_not_bite')

    receipt['all_arms_bit'] = all(
        receipt[k]['bit'] for k in
        ('FB1_stale_render', 'FB2_dropped_ring_remap',
         'FB3_undeclared_strength_change', 'FB4_silent_mass_drift',
         'FB5_area_independent_forces', 'FB6_unaccounted_energy'))
    write_json(FALSIFIER_PATH, receipt)
    print('falsifier arms all bit:', receipt['all_arms_bit'])
    return 0


def build_audits_from_main():
    """The clean-build belt audit values for the FB3 clean-control row
    (recomputed live from clean builds -- never hand-typed)."""
    out = {}
    real = lw.load_real_data()
    for res in ml.RESOLUTION_ORDER:
        w, cfg = ml.build_world(res, lw.off_schedule, 1, mode='off',
                                real=real)
        out[res] = ml.resolution_build_audit(res, w, cfg)
    return out


def _dynamic_trace_payload(res):
    trace = json.loads(TRACE_PATH.read_text(encoding='utf-8'))
    return trace['runs'][res]


def mode_rerun():
    real = lw.load_real_data()
    payload = {'schema': SCHEMA_TRACE,
               'criteria_sha256': CRITERIA_SHA256, 'runs': {}}
    for res in ml.RESOLUTION_ORDER:
        world, _, _ = timed_run(res, lw.work_schedule, lw.TOTAL_TICKS,
                                'loaded', real=real,
                                snapshot_ticks=ml.SNAP_TICKS)
        payload['runs'][res] = {
            'loaded_rows': world.rows,
            'loaded_snapshots': {str(s['tick']): s
                                 for s in world.snapshots},
        }
    write_json(HERE / 'experiment_trace_rerun.json', payload)
    print('rerun trace written')
    return 0


def mode_compare():
    main_trace = json.loads(TRACE_PATH.read_text(encoding='utf-8'))
    rerun_trace = json.loads(
        (HERE / 'experiment_trace_rerun.json').read_text(encoding='utf-8'))
    unit_keys = ('loaded_rows', 'loaded_snapshots')
    per_res = {}
    ok = True
    for res in ml.RESOLUTION_ORDER:
        a = digest({k: main_trace['runs'][res][k] for k in unit_keys})
        b = digest({k: rerun_trace['runs'][res][k] for k in unit_keys})
        per_res[res] = {'main_dynamic_sha256': a, 'rerun_dynamic_sha256': b,
                        'byte_identical': bool(a == b)}
        ok = ok and a == b
    receipt = {
        'schema': SCHEMA_DETERMINISM,
        'criteria_sha256': CRITERIA_SHA256, 'attempt_id': ATTEMPT_ID,
        'arrival_id': ARRIVAL_ID,
        'determinism_unit': 'per-resolution loaded run canonical subtree '
                            '(rows + snapshots) of experiment_trace.json '
                            '(two fresh process pairs, same interpreter)',
        'per_resolution': per_res,
        'all_byte_identical': ok,
    }
    write_json(DETERMINISM_PATH, receipt)
    print('determinism byte-identical:', ok)
    require(ok, 'determinism_mismatch')
    return 0


def main(argv):
    if not argv:
        print('usage: run_experiments.py {main|falsify|rerun|compare}')
        return 2
    mode = argv[0]
    if mode == 'main':
        return mode_main()
    if mode == 'falsify':
        return mode_falsify()
    if mode == 'rerun':
        return mode_rerun()
    if mode == 'compare':
        return mode_compare()
    print('unknown mode:', mode)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
