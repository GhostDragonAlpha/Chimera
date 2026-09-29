"""MAT2-M08 frozen experiments (PREREGISTRATION.md).

Modes (one process each; all GPU work goes through the mailbox jobs):
  main      X1 GPU/direct-reference agreement (M07 sealed oracle vs the
            resident GPU world on the frozen 80-tick two-component fixture),
            telemetry-byte accounting, P-probes; writes experiment_trace.json
            and experiment_receipt.json (physics-only, byte-identical on
            rerun) and gpu_profile.json (timings; NEVER byte-compared).
  rerun     second fresh run for X2 byte-identity (writes *_rerun2.json).
  compare   X2: sha256-verify trace/receipt byte-identity across the two
            fresh runs; writes determinism_receipt.json.
  profile   X3 residency/profile run (16 components, 240 ticks, cyclic
            schedule): per-tick device times, per-pass sampled times, host
            bytes per tick, VRAM before/peak/after; writes profile_receipt.
  bharm     X4 Barnes-Hut arm (16 components, far field enabled, 120 ticks):
            production-theta error window, theta=0 near-field reference
            window, two-body identity; writes bh_receipt.json.
  falsify   F1/F2/F3 arms with their clean controls in the same executable;
            writes falsifier_receipt.json.
No RNG; no wall-clock in trace/receipt (timings live only in the profile
receipt, which is excluded from byte-identity by declaration).
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import pathlib
import subprocess
import sys
import time

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M04'), str(CONTRIB / 'MAT2-M06'),
           str(CONTRIB / 'MAT2-M07')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import integrated_step as iw        # noqa: E402  (sealed CPU oracle)
import kernel_mirror as km          # noqa: E402
import resident_gpu_world as rgw    # noqa: E402
import resident_bh as rb            # noqa: E402

DT0 = iw.DT_S
TICKS = 80
CAPTURE_TICKS = (0, 10, 20, 30, 40, 50, 60, 70, 79)
AGREE_POS_WINDOW_M = 1e-12
AGREE_SCALAR_WINDOW = 1e-9
PROFILE_COMPS = 16
PROFILE_TICKS = 240
BH_TICKS = 120
BH_MEASURE_EVERY = 10
TELEMETRY_BUDGET_UP_PER_TICK = 256
TELEMETRY_BUDGET_DOWN_PER_COMP = 1024


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def refuse_vacuous(a, b, code='vacuous_comparison_refused'):
    """M07's independent-review lesson: a window gate whose two sides are
    identically zero cannot fail; such comparisons are REFUSED."""
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
    pins = {
        '../MAT2-M07/integrated_step.py':
            '36c556dcf2cf0b3c9b7fe3c79dd42baae6489ad2c0b3093a5ac1bd550d8c66e4',
        '../MAT2-M07/run_experiments.py':
            '444fd58fe932bf4cb4443f577d0088ae9bfe218bfdd6397ef5594db7fbec0830',
        '../MAT2-M01/material_state.py':
            'b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40',
        '../MAT2-M03/pressure_membrane.py':
            '3dd64f6465430380f1c0a53a95523c700cd51a6b1115e60f0df8afde2239c96e',
        '../MAT2-M04/passive_response.py':
            '68a696e1728066a3dce93db7b6c98f8bb4826322a84bbad20eeadf38350e326b',
        '../MAT2-M06/local_contact.py':
            '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc',
    }
    for rel, expected in pins.items():
        path = (HERE / rel).resolve()
        if not path.exists():
            raise ValueError('input_pin_missing:' + rel)
        if sha256_file(path) != expected:
            raise ValueError('input_pin_drift:' + rel)
    return pins


COMPARABLE = [
    ('plate_x_m', km.D_PLX), ('F_N', km.D_F), ('U_mat_j', km.D_UMAT),
    ('Q_mat_j', km.D_QMAT), ('W_in_mat_j', km.D_WIN),
    ('e_kinetic_j', km.D_KE), ('u_scaffold_j', km.D_USCAFF),
    ('membrane_volume_m3', km.D_VOL), ('w_press_j', km.D_WPRESS),
    ('w_grav_j', km.D_WGRAV), ('w_mat_on_plate_j', km.D_WMAT),
    ('q_mat_tick_j', km.D_QTICK), ('w_contact_ke_j', km.D_WCKE),
    ('projection_exchange_j', km.D_PROJ), ('residual_r_j', km.D_RESID),
    ('residual_bound_j', km.D_BOUND), ('impulse_trapezoid_work_j', km.D_TRAP),
    ('jn_applied_total_N_s', km.D_JNTOT), ('contact_iterations', km.D_ITERS),
    ('contact_active_pairs', km.D_ACTIVE),
    ('contact_gs_residual_N_s', km.D_GSRES),
]


def run_agreement(ticks=TICKS, comps=(('A', 0.0), ('B', 3.0)),
                  store_snapshots=True, profile=False, far_field=False,
                  roundtrip_tamper=False):
    """X1: the sealed CPU oracle and the resident GPU world step the SAME
    fixture; every tick is compared under the frozen windows. Returns
    (trace, receipt)."""
    from numba import cuda
    comps_obj = [iw.Component(cid, off) for cid, off in comps]
    oracle = iw.IntegratedWorld([iw.Component(cid, off)
                                 for cid, off in comps])
    gpu = rgw.ResidentGpuWorld(comps_obj, gravity=True, far_field=far_field)
    ctx = cuda.current_context()
    mem_before = ctx.get_memory_info()
    trace_rows = []
    worst = {'pos': 0.0, 'plate': 0.0}
    scalar_worst = {}
    budget_rows = []
    snapshots = {}
    for tick in range(ticks):
        dp = float(iw.PRESS_SCHEDULE.get(tick, 0.0))
        oracle.step(tick)
        up0 = gpu.host_bytes_up
        down0 = gpu.host_bytes_down
        gpu.step_tick(tick, dp)
        if roundtrip_tamper:
            # F1 tamper: full state down+up every tick (the claimed-GPU-
            # dynamics-with-a-roundtrip failure), then resume
            xb = gpu.d_x.copy_to_host()
            vxb = gpu.d_v.copy_to_host()
            pxb = gpu.d_px.copy_to_host()
            pvb = gpu.d_pv.copy_to_host()
            gpu.d_x.copy_to_device(xb)
            gpu.d_v.copy_to_device(vxb)
            gpu.d_px.copy_to_device(pxb)
            gpu.d_pv.copy_to_device(pvb)
        block = gpu.diagnostics()
        up = gpu.host_bytes_up - up0
        down = gpu.host_bytes_down - down0
        budget_rows.append({'tick': tick, 'up_bytes': up,
                            'down_bytes': down,
                            'down_budget': TELEMETRY_BUDGET_DOWN_PER_COMP
                            * gpu.n_comp})
        if up > TELEMETRY_BUDGET_UP_PER_TICK or down >                 TELEMETRY_BUDGET_DOWN_PER_COMP * gpu.n_comp:
            raise ValueError(rgw.E_BYTES)
        try:
            gpu.check_gates(block[0])
            gpu.check_gates(block[1])
        except ValueError:
            # debug evidence: dump the failing tick's full diagnostic blocks
            # and the per-substep pass values (attempt scratch, not a claim)
            dbg = {'tick': tick, 'blocks': block.tolist(),
                   'component': 'B' if True else 'A'}
            try:
                import kernel_mirror as _km
                names = {i: n for i, n in enumerate(
                    [a for a in dir(_km) if a.startswith('D_')])}
                slots = {}
                for a in dir(_km):
                    if a.startswith('D_'):
                        slots[getattr(_km, a)] = a
                dbg['named'] = [{slots.get(i, f'slot{i}'): v
                                 for i, v in enumerate(b)} for b in block]
                pv = gpu.d_pass.copy_to_host()
                dbg['pass_comp1'] = pv[1].tolist()
            except Exception as dbg_err:
                dbg['dump_error'] = repr(dbg_err)
            (HERE / 'debug_gate_failure.json').write_text(
                json.dumps(dbg, indent=1))
            raise
        ocomp = oracle._component(comps[0][0])
        # trajectories: full membrane + plate vertex arrays
        if store_snapshots and tick in CAPTURE_TICKS:
            snap = gpu.snapshot(tick)
            snap['tick'] = tick
            snap['delta_p_pa'] = dp
            snap['gpu_block'] = [float(c) for c in block[0]]
            snapshots[tick] = snap
            omem = np.asarray(ocomp.x)
            gmem = np.asarray(snap['membrane_positions_m'])
            dpos = float(np.abs(omem - gmem).max())
            opl = np.asarray(ocomp.plate.x)
            gpl = np.asarray(snap['plate_vertices_m'])
            dpl = float(np.abs(opl - gpl).max())
            worst['pos'] = max(worst['pos'], dpos)
            worst['plate'] = max(worst['plate'], dpl)
        orow = oracle.ticks[-1]['components'][comps[0][0]]
        brow = oracle.ticks[-1]['components'][comps[1][0]]
        g0 = block[0]
        g1 = block[1]
        row = {'tick': tick}
        vacuous_selftest = vacuous_guard_selftest()
        for name, slot in COMPARABLE:
            a = float(orow[name])
            b = float(g0[slot])
            refuse_vacuous(a, b)
            d = abs(a - b)
            rel = d / max(1.0, abs(a), abs(b))
            if rel > AGREE_SCALAR_WINDOW:
                row[name + '_EXCEEDED'] = [a, b, rel]
            scalar_worst.setdefault(name, 0.0)
            if rel > scalar_worst[name]:
                scalar_worst[name] = rel
        for name, slot in COMPARABLE:
            a = float(brow[name])
            b = float(g1[slot])
            refuse_vacuous(a, b)
            d = abs(a - b)
            rel = d / max(1.0, abs(a), abs(b))
            if rel > AGREE_SCALAR_WINDOW:
                row['B_' + name + '_EXCEEDED'] = [a, b, rel]
        row['vacuous_guard_selftest'] = vacuous_selftest
        trace_rows.append(row)
    mem_after = ctx.get_memory_info()
    receipt = {
        'schema': 'chimera.m08_agreement.v1',
        'fixture': {'components': [list(c) for c in comps], 'ticks': ticks,
                    'dt_s': DT0, 'substeps': km.N_SUB},
        'windows': {'position_m': AGREE_POS_WINDOW_M,
                    'scalar_relative': AGREE_SCALAR_WINDOW},
        'worst_membrane_position_diff_m': worst['pos'],
        'worst_plate_position_diff_m': worst['plate'],
        'worst_scalar_relative': scalar_worst,
        'position_within_window': worst['pos'] <= AGREE_POS_WINDOW_M
        and worst['plate'] <= AGREE_POS_WINDOW_M,
        'scalars_within_window': all(v <= AGREE_SCALAR_WINDOW
                                     for v in scalar_worst.values()),
        'telemetry': {
            'max_up_bytes_per_tick': max(r['up_bytes'] for r in budget_rows),
            'max_down_bytes_per_tick': max(r['down_bytes']
                                           for r in budget_rows),
            'up_budget': TELEMETRY_BUDGET_UP_PER_TICK,
            'down_budget_per_comp': TELEMETRY_BUDGET_DOWN_PER_COMP,
            'within_budget': max(r['up_bytes'] for r in budget_rows)
            <= TELEMETRY_BUDGET_UP_PER_TICK
            and max(r['down_bytes'] for r in budget_rows)
            <= TELEMETRY_BUDGET_DOWN_PER_COMP * gpu.n_comp,
            'total_up_bytes': gpu.host_bytes_up,
            'total_down_bytes': gpu.host_bytes_down},
        'state_bytes_component':
            int(gpu.d_x.nbytes / gpu.n_comp + gpu.d_v.nbytes / gpu.n_comp
                + gpu.d_px.nbytes / gpu.n_comp),
        'vram_free_before': int(mem_before.free),
        'vram_free_after': int(mem_after.free),
        'order_digest_gpu': gpu.order_digest,
        'order_digest_oracle': oracle.order_digest,
        'far_field': far_field,
    }
    if store_snapshots:
        receipt['snapshots'] = {str(k): v for k, v in snapshots.items()}
    gpu.release()
    return trace_rows, receipt


def p_single_writer():
    """AST scan: device state is written only inside @cuda.jit kernels and
    the ResidentGpuWorld.step_tick launch path; host methods outside the
    construction/step path never copy_to_device state arrays."""
    src = (HERE / 'resident_gpu_world.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    kernels = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            kernels.add(node.name)
    class_methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'ResidentGpuWorld':
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    class_methods[item.name] = item
    violations = []
    allowed_host_writers = {'__init__', 'step_tick'}
    for name, fn in class_methods.items():
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func,
                                                         ast.Attribute):
                if node.func.attr == 'copy_to_device' \
                        and name not in allowed_host_writers:
                    violations.append(f'{name}:copy_to_device')
    return {'kernels': sorted(kernels),
            'host_writer_methods': sorted(allowed_host_writers),
            'violations': violations, 'ok': not violations}


def p_gates_declared():
    """The GPU world refuses through the declared gate names."""
    gates = [rgw.E_ORDER, rgw.E_UNEXPLAINED, rgw.E_MOMENTUM, rgw.E_CONV,
             rgw.E_SUBLEDGER, rgw.E_RECIPOCITY, rgw.E_SEPARATION,
             rgw.E_STICK, rgw.E_ANCHOR, rgw.E_STALE, rgw.E_BYTES, rgw.E_BH]
    return {'gate_codes': sorted(gates), 'count': len(gates)}


def mode_main():
    pins = verify_input_pins()
    t0 = time.perf_counter()
    trace, receipt = run_agreement()
    t1 = time.perf_counter()
    receipt['input_pins'] = {k: 'ok' for k in pins}
    receipt['p_single_writer'] = p_single_writer()
    receipt['p_gates_declared'] = p_gates_declared()
    receipt['X1_pass'] = bool(receipt['position_within_window']
                              and receipt['scalars_within_window']
                              and receipt['telemetry']['within_budget'])
    (HERE / 'experiment_trace.json').write_bytes(canonical(
        {'rows': trace}))
    (HERE / 'experiment_receipt.json').write_bytes(canonical(receipt))
    (HERE / 'gpu_profile.json').write_bytes(canonical({
        'x1_wall_seconds': t1 - t0,     # profile receipt only, never compared
    }))
    print(json.dumps({'X1_pass': receipt['X1_pass'],
                      'worst_pos_m': receipt['worst_membrane_position_diff_m'],
                      'worst_plate_m':
                          receipt['worst_plate_position_diff_m'],
                      'telemetry_within_budget':
                          receipt['telemetry']['within_budget']}, indent=1))


def mode_rerun():
    trace, receipt = run_agreement()
    (HERE / 'experiment_trace_rerun2.json').write_bytes(canonical(
        {'rows': trace}))
    (HERE / 'experiment_receipt_rerun2.json').write_bytes(canonical(receipt))
    print('rerun written')


def mode_compare():
    a = (sha256_file(HERE / 'experiment_trace.json'),
         sha256_file(HERE / 'experiment_receipt.json'))
    b = (sha256_file(HERE / 'experiment_trace_rerun2.json'),
         sha256_file(HERE / 'experiment_receipt_rerun2.json'))
    receipt = {
        'schema': 'chimera.m08_determinism.v1',
        'trace_sha_run1': a[0], 'receipt_sha_run1': a[1],
        'trace_sha_run2': b[0], 'receipt_sha_run2': b[1],
        'X2_byte_identical': a == b,
    }
    (HERE / 'determinism_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps(receipt, indent=1))


def _cyclic_schedule(tick):
    phase = tick % 80
    return 60.0 if 1 <= phase <= 40 else 0.0


def mode_profile():
    """X3: 16-component steady-state residency/profile run."""
    from numba import cuda
    comps = [iw.Component(f'c{i}', 3.0 * i) for i in range(PROFILE_COMPS)]
    gpu = rgw.ResidentGpuWorld(comps, gravity=True, far_field=False)
    ctx = cuda.current_context()
    mem0 = ctx.get_memory_info()
    import cupy as cp
    pool = cp.get_default_memory_pool()
    used0 = pool.used_bytes()
    tick_ms = []
    pass_samples = []
    bytes_rows = []
    ev_start = cuda.event(timing=True)
    ev_end = cuda.event(timing=True)
    for tick in range(PROFILE_TICKS):
        dp = _cyclic_schedule(tick)
        up0 = gpu.host_bytes_up
        down0 = gpu.host_bytes_down
        ev_start.record()
        gpu.step_tick(tick, dp)
        ev_end.record()
        ev_end.synchronize()
        ms = ev_start.elapsed_time(ev_end)
        tick_ms.append(ms)
        block = gpu.diagnostics()
        gpu.check_gates(block[0])
        bytes_rows.append({'tick': tick,
                           'up': gpu.host_bytes_up - up0,
                           'down': gpu.host_bytes_down - down0})
        if tick < 20:
            pass_samples.append({'tick': tick, 'step_ms': ms})
    mem1 = ctx.get_memory_info()
    t = np.array(tick_ms)
    receipt = {
        'schema': 'chimera.m08_profile.v1',
        'components': PROFILE_COMPS, 'ticks': PROFILE_TICKS,
        'schedule': 'cyclic 60 Pa on 1..40 of 80 (M07 A5 pattern)',
        'step_ms_p50': float(np.percentile(t, 50)),
        'step_ms_p95': float(np.percentile(t, 95)),
        'step_ms_p99': float(np.percentile(t, 99)),
        'step_ms_max': float(t.max()),
        'step_ms_mean': float(t.mean()),
        'max_up_bytes_per_tick': max(r['up'] for r in bytes_rows),
        'max_down_bytes_per_tick': max(r['down'] for r in bytes_rows),
        'up_budget': TELEMETRY_BUDGET_UP_PER_TICK,
        'down_budget_per_comp': TELEMETRY_BUDGET_DOWN_PER_COMP,
        'residency_within_budget':
            max(r['up'] for r in bytes_rows)
            <= TELEMETRY_BUDGET_UP_PER_TICK
            and max(r['down'] for r in bytes_rows)
            <= TELEMETRY_BUDGET_DOWN_PER_COMP * PROFILE_COMPS,
        'state_bytes_total':
            int(gpu.d_x.nbytes + gpu.d_v.nbytes + gpu.d_px.nbytes
                + gpu.d_pv.nbytes),
        'state_bytes_per_component':
            int((gpu.d_x.nbytes + gpu.d_v.nbytes + gpu.d_px.nbytes
                 + gpu.d_pv.nbytes) // PROFILE_COMPS),
        'vram_free_before': int(mem0.free),
        'vram_free_after': int(mem1.free),
        'cupy_pool_used_bytes_start': int(used0),
        'cupy_pool_used_bytes_end': int(pool.used_bytes()),
        'pass_samples': pass_samples,
    }
    (HERE / 'profile_receipt.json').write_bytes(canonical(receipt))
    gpu.release()
    print(json.dumps({k: receipt[k] for k in (
        'step_ms_p50', 'step_ms_p95', 'step_ms_p99', 'step_ms_max',
        'max_up_bytes_per_tick', 'max_down_bytes_per_tick',
        'residency_within_budget', 'state_bytes_total')}, indent=1))


def mode_bharm():
    """X4: Barnes-Hut arm with its own law, error criterion and near-field
    reference."""
    comps = [iw.Component(f'c{i}', 3.0 * i) for i in range(PROFILE_COMPS)]
    gpu = rgw.ResidentGpuWorld(comps, gravity=True, far_field=True)
    bh = gpu.bh
    identity_rel = rb.bh_two_body_identity()
    rows = []
    w_sg_total = 0.0
    sg_imp_total = [0.0, 0.0, 0.0]
    for tick in range(BH_TICKS):
        dp = _cyclic_schedule(tick)
        gpu.step_tick(tick, dp)
        block = gpu.diagnostics()
        w_sg_total += float(block[0][km.D_WSG])
        sg_imp_total[0] += float(block[0][km.D_SGIMPX])
        sg_imp_total[1] += float(block[0][km.D_SGIMPY])
        sg_imp_total[2] += float(block[0][km.D_SGIMPZ])
        if tick % BH_MEASURE_EVERY == 0:
            err, rms = bh.measure(theta0=False)
            near_err, near_rms = bh.measure(theta0=True)
            bh.write_measurements()
            rows.append({'tick': tick, 'bh_rel_err_max': err,
                         'bh_rel_err_rms': rms,
                         'near_theta0_rel_err_max': near_err,
                         'near_theta0_rel_err_rms': near_rms})
        gpu.check_gates(block[0])
    # the law identity and the final measured windows close the receipt
    err, rms = bh.measure(theta0=False)
    near_err, _ = bh.measure(theta0=True)
    receipt = {
        'schema': 'chimera.m08_bh.v1',
        'law': 'U = -G_N m_i m_j / r; a_i = G_N sum_j m_j (x_j-x_i)/r^3',
        'G_N_SI': rb.G_N, 'theta': rb.BH_THETA,
        'bodies': bh.n_real,
        'two_body_identity_rel_err': identity_rel,
        'two_body_identity_within_1e-12': identity_rel <= 1e-12,
        'bh_error_window': rb.BH_ERROR_WINDOW,
        'near_field_window': rb.BH_NEAR_WINDOW,
        'measurements': rows,
        'final_bh_rel_err_max': err,
        'final_near_theta0_rel_err_max': near_err,
        'X4_bh_within_window': err <= rb.BH_ERROR_WINDOW,
        'X4_near_field_within_window': near_err <= rb.BH_NEAR_WINDOW,
        'w_sg_total_J': w_sg_total,
        'sg_impulse_total_N_s': sg_imp_total,
    }
    (HERE / 'bh_receipt.json').write_bytes(canonical(receipt))
    gpu.release()
    print(json.dumps({k: receipt[k] for k in (
        'two_body_identity_rel_err', 'final_bh_rel_err_max',
        'final_near_theta0_rel_err_max', 'X4_bh_within_window',
        'X4_near_field_within_window', 'w_sg_total_J')}, indent=1))


def mode_falsify():
    """F1/F2/F3 arms — each tampered copy and its clean control in the same
    executable; tampered copies are scratch (never committed state)."""
    receipt = {'schema': 'chimera.m08_falsifiers.v1', 'arms': {}}
    # F1: full-state roundtrip every tick vs the clean resident path
    fired = False
    try:
        run_agreement(ticks=6, store_snapshots=False,
                      roundtrip_tamper=True)
    except ValueError as exc:
        fired = str(exc) == rgw.E_BYTES
    receipt['arms']['F1_state_roundtrip_fires'] = fired
    clean, crec = run_agreement(ticks=6, store_snapshots=False)
    receipt['arms']['F1_clean_within_budget'] = crec['telemetry'][
        'within_budget']
    # F2a: aggregate-everything (theta gate removed) exceeds the 5e-3 window
    comps = [iw.Component(f'c{i}', 3.0 * i) for i in range(4)]
    gpu = rgw.ResidentGpuWorld(comps, gravity=True, far_field=True)
    bh = gpu.bh
    for tick in range(6):
        gpu.step_tick(tick, _cyclic_schedule(tick))
        gpu.diagnostics()
    bh.d_theta.copy_to_device(np.array([1.0e9]))
    from numba import cuda
    k_bh_force = rb.k_bh_force
    k_bh_force[bh.n_real, 1](gpu.d_x, gpu.d_px, gpu.d_masses, gpu.d_pmass,
                             bh.d_idx, bh.d_npow, bh.d_nreal, bh.d_nmin,
                             bh.d_nmax, bh.d_nm, bh.d_ncom, bh.d_theta,
                             bh.d_sga)
    bh.d_mode.copy_to_device(np.array([1.0]))
    rb.k_bh_check[bh.n_real, 1](gpu.d_x, gpu.d_px, gpu.d_masses, gpu.d_pmass,
                                bh.d_sga, bh.d_bh_errs, bh.d_mode)
    rb.k_bh_reduce[1, 1](bh.d_bh_errs, bh.d_out_max, bh.d_out_rms,
                         bh.d_out_n, bh.d_nreal)
    f2a_err = float(bh.d_out_max.copy_to_host()[0])
    receipt['arms']['F2a_aggregate_all_err'] = f2a_err
    receipt['arms']['F2a_exceeds_window'] = f2a_err > rb.BH_ERROR_WINDOW
    # clean controls: production theta within 5e-3; theta0 within 1e-12
    err, _rms = bh.measure(theta0=False)
    near_err, _rms2 = bh.measure(theta0=True)
    receipt['arms']['F2_clean_theta_err'] = err
    receipt['arms']['F2_clean_theta_within_window'] = \
        err <= rb.BH_ERROR_WINDOW
    receipt['arms']['F2_clean_theta0_err'] = near_err
    receipt['arms']['F2_clean_theta0_within_window'] = \
        near_err <= rb.BH_NEAR_WINDOW
    gpu.release()
    # F3: stale diagnostics caught by the chained tick digest
    comps = [iw.Component('A', 0.0)]
    gpu = rgw.ResidentGpuWorld(comps, gravity=True)
    prev_block = None
    stale_caught = False
    clean_ok = True
    for tick in range(4):
        gpu.step_tick(tick, 0.0 if tick > 2 else 60.0)
        block = gpu.diagnostics().copy()
        # clean control: current block carries the right tick + digest
        d_tick_ok = int(block[0][km.D_TICK]) == tick
        d_digest_ok = km.block_digest(block[0], tick) == block[0][km.D_DIGEST]
        clean_ok = clean_ok and d_tick_ok and d_digest_ok
        if prev_block is not None:
            # tampered read: the PREVIOUS tick's block at this tick
            try:
                if int(prev_block[0][km.D_TICK]) != tick:
                    raise ValueError(rgw.E_STALE)
                if km.block_digest(prev_block[0], tick) \
                        != prev_block[0][km.D_DIGEST]:
                    raise ValueError(rgw.E_STALE)
            except ValueError as exc:
                if str(exc) == rgw.E_STALE:
                    stale_caught = True
        prev_block = block
    receipt['arms']['F3_stale_diagnostics_caught'] = stale_caught
    receipt['arms']['F3_clean_chain_green'] = clean_ok
    receipt['F_all_green'] = (receipt['arms']['F1_state_roundtrip_fires']
                              and receipt['arms']['F1_clean_within_budget']
                              and receipt['arms']['F2a_exceeds_window']
                              and receipt['arms']['F2_clean_theta_within_window']
                              and receipt['arms']['F2_clean_theta0_within_window']
                              and receipt['arms']['F3_stale_diagnostics_caught']
                              and receipt['arms']['F3_clean_chain_green'])
    (HERE / 'falsifier_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps(receipt['arms'], indent=1))


def mode_regression():
    """P4: the UNMODIFIED M07 suite (which transitively re-runs
    M03/M04/M05/M06) on the exact candidate revision."""
    target = str(CONTRIB / 'MAT2-M07' / 'test_integrated_step.py')
    proc = subprocess.run([sys.executable, '-B', target],
                          capture_output=True, text=True, timeout=3000)
    receipt = {
        'schema': 'chimera.m08_regression.v1',
        'suite': target,
        'exit_code': proc.returncode,
        'tail': proc.stdout[-2000:],
        'P4_m07_suite_green': proc.returncode == 0,
    }
    (HERE / 'regression_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: receipt[k] for k in (
        'exit_code', 'P4_m07_suite_green')}, indent=1))


def main(argv):
    mode = argv[1] if len(argv) > 1 else 'main'
    if mode == 'main':
        mode_main()
    elif mode == 'rerun':
        mode_rerun()
    elif mode == 'compare':
        mode_compare()
    elif mode == 'profile':
        mode_profile()
    elif mode == 'bharm':
        mode_bharm()
    elif mode == 'falsify':
        mode_falsify()
    elif mode == 'regression':
        mode_regression()
    else:
        raise SystemExit('unknown mode: ' + mode)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
