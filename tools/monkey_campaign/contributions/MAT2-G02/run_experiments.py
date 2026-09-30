"""{{CARD_FULL}} frozen experiments (PREREGISTRATION.md) - card-kit template.

Copy-adapted from the merged MAT2-M08 trio (PR #267 lineage) by the card-kit
lane. Replace every {{PLACEHOLDER}}; keep the pattern. When done, delete this
banner's FILL list and keep the lessons.

Modes (one process each; all GPU work goes through the mailbox jobs,
E:/ChimeraWork/gpu-queue per PROTOCOL.md):
  main       X1 GPU/direct-reference agreement on the frozen fixture;
             writes experiment_trace.json + experiment_receipt.json
             (physics-only, byte-identical on rerun) and gpu_profile.json
             (timings; NEVER byte-compared).
  rerun      second fresh run for X2 byte-identity (writes *_rerun2.json).
  compare    X2 scoped determinism: byte-identity of the DECLARED unit
             (the trace), with the receipt delta scoped to mode_main's
             augmentation keys; writes determinism_receipt.json.
  profile    X3 residency/profile run (steady-state, cyclic schedule);
             writes profile_receipt.json.
  bharm      X4 far-field arm (only if the card has a hierarchy pass):
             its own eligible law, error window and theta=0 near-field
             reference; writes bh_receipt.json. DELETE if not applicable -
             do not ship an arm the card does not declare.
  falsify    F-arms, each tamper with its passing CLEAN CONTROL run FIRST,
             in the same executable; writes falsifier_receipt.json.
  regression the declared upstream suite re-run unmodified on the exact
             candidate revision; writes regression_receipt.json.

FILL LIST (search for '{{'):
  {{CARD_FULL}} {{CARD_ID}} {{CARD_TITLE}} {{DATE}}
  {{PIN_TABLE}} {{WORLD_IMPORTS}} {{ORACLE_IMPORT}} {{COMPARABLE_TABLE}}
  {{FIXTURE_COMPS}} {{TICKS}} {{WINDOWS}} {{PROFILE_COMPS}} {{PROFILE_TICKS}}
  {{CYCLIC_SCHEDULE}} {{F_ARMS}} {{REGRESSION_SUITE}}
Laws this file already enforces (do NOT remove):
  - CPU-FIRST: validate the kernel logic as a pure mirror against the sealed
    oracle on CPU (see local rehearsal pattern) BEFORE any GPU job; the GPU
    bank confirms physics, it does not debug it.
  - No RNG; no wall-clock in trace/receipt (timings live only in the profile
    receipt, excluded from byte-identity by declaration).
  - Refusals are named codes; vacuous comparisons are REFUSED.
  - Device state is released on EVERY exit path (try/finally).
  - Job JSONs to the GPU queue use FORWARD SLASHES ONLY (a single-backslash
    JSON escape corrupted M08 job m08h: '\\c' -> U+0002, '\\t' -> TAB in
    the workdir). Mode names must be verified against the dispatch table
    in main() below - job writers: copy the mode token from MODES.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import subprocess
import sys
import time

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
# FILL {{WORLD_IMPORTS}}: add sys.path entries for each sibling card dir
# this card imports from (M08 pattern: MAT2-M01/M03/M04/M06/M07).
for _p in (str(HERE),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# FILL {{ORACLE_IMPORT}}: the sealed CPU oracle (M08 used the M07
# integrated_step UNMODIFIED, with a frozen sha256 pin below).
# import integrated_step as iw        # noqa: E402  (sealed CPU oracle)
# import kernel_mirror as km          # noqa: E402  (CPU mirror of kernels)
# import resident_gpu_world as rgw    # noqa: E402  (the CUDA resident world)

# LAW (CPU-first, M08 origin): kernel_mirror.py is the statement-level pure
# numpy mirror of every CUDA kernel. Its logic is validated BITWISE against
# the sealed oracle on CPU BEFORE the CUDA port runs on the GPU box. Keep
# that file and its rehearsal; never debug physics through GPU jobs.

CARD_ID = '{{CARD_ID}}'          # SHORT registry form: 'M09', NOT 'MAT2-M09'
CARD_FULL = '{{CARD_FULL}}'      # dir/PR form: 'MAT2-M09'

DT0 = 1.0 / 300.0                # FILL {{TICKS}}/{{WINDOWS}} block below
TICKS = 80                       # FILL: frozen main-fixture tick count
CAPTURE_TICKS = (0, 10, 20, 30, 40, 50, 60, 70, 79)   # FILL: declared
AGREE_POS_WINDOW_M = 1e-12       # FILL {{WINDOWS}}: frozen position window
AGREE_SCALAR_WINDOW = 1e-9       # FILL {{WINDOWS}}: frozen relative window
PROFILE_COMPS = 16               # FILL {{PROFILE_COMPS}}
PROFILE_TICKS = 240              # FILL {{PROFILE_TICKS}}
TELEMETRY_BUDGET_UP_PER_TICK = 256      # FILL: declared command budget
TELEMETRY_BUDGET_DOWN_PER_COMP = 1024   # FILL: declared diagnostics budget

if CARD_ID.startswith('{{'):
    raise SystemExit(
        'run_experiments_template.py is UNFILLED: replace the {{...}} '
        'placeholders (see the FILL LIST in the module docstring) before '
        'running anything. Templates never run as-is.')

MODES = ('main', 'rerun', 'compare', 'profile', 'bharm', 'falsify',
         'regression')
# Job writers: the GPU-queue command mode token MUST be one of MODES.
# (M08 lesson: job 'm08g' sent mode 'x1'; the dispatch refused with
# 'unknown mode' and burned a mailbox round trip.)


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _numpy_json_default(o):
    """Numpy scalars reaching json (np.bool_ from == on numpy values,
    np.floating/np.integer from kernel-adjacent arithmetic) serialize as
    their plain counterparts. Only invoked for otherwise-unserializable
    objects, so every receipt that serialized before stays byte-identical.
    (Verbatim from M08: keep exactly; receipts depend on it.)"""
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    raise TypeError(f'Object of type {o.__class__.__name__} '
                    f'is not JSON serializable')


def canonical(value):
    """The one serializer for trace/receipt bytes: sorted keys, no spaces,
    UTF-8, NaN refused. Byte-identity (X2) is defined on these bytes."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False,
                      default=_numpy_json_default).encode('utf-8')


def refuse_vacuous(a, b, code='vacuous_comparison_refused'):
    """A window gate whose two sides are identically zero cannot fail; such
    comparisons are REFUSED (M07/M08 law: a falsifier must be able to
    fail). Gate your FALSIFIABLE windows with this; a plain agreement
    comparison of two exact zeros is recorded as an exact-zero pair, not
    silently dropped."""
    if a == 0.0 and b == 0.0:
        raise ValueError(code)


def vacuous_guard_selftest():
    """Must be True in every receipt that uses refuse_vacuous (the guard
    itself is tested in the executable, every run)."""
    fired = False
    try:
        refuse_vacuous(0.0, 0.0)
    except ValueError as exc:
        fired = str(exc) == 'vacuous_comparison_refused'
    return fired


def verify_input_pins():
    """Frozen dependency inputs: refuse to run on drift. FILL {{PIN_TABLE}}:
    relative path -> sha256 of every upstream file this card depends on
    (the sealed oracle, the upstream suite, sibling modules). Copy the
    hashes from the PINNED sources, never re-type them."""
    pins = {
        # FILL {{PIN_TABLE}}  e.g.
        # '../MAT2-M07/integrated_step.py':
        #     '36c556dcf2cf0b3c9b7fe3c79dd42baae6489ad2c0b3093a5ac1bd550d8c66e4',
    }
    if not pins:
        raise ValueError('input_pins_empty: declare your frozen inputs')
    for rel, expected in pins.items():
        path = (HERE / rel).resolve()
        if not path.exists():
            raise ValueError('input_pin_missing:' + rel)
        if sha256_file(path) != expected:
            raise ValueError('input_pin_drift:' + rel)
    return pins


# FILL {{COMPARABLE_TABLE}}: every per-tick scalar the oracle row and the
# GPU diagnostic block must agree on, as (name, diagnostic-slot constant).
# M08 compared 21 scalars per component per tick under the relative window.
COMPARABLE = [
    # ('plate_x_m', km.D_PLX), ('F_N', km.D_F), ...
]


def run_agreement(ticks=TICKS, store_snapshots=True, profile=False,
                  tamper=False):
    """X1 wrapper: own the world here, release it on EVERY exit path.

    Wrapper/inner pattern (M08): the wrapper constructs the resident world
    and guarantees `finally: world.release()`; the inner body does the
    stepping and measurement. A raise (a budget gate, a named refusal, a
    CUDA fault) must never leak device state into the next world sharing
    this context.
    FILL: construction of the oracle + world over {{FIXTURE_COMPS}}."""
    # from numba import cuda
    raise SystemExit('FILL: run_agreement for this card')
    # --- shape to copy (M08): -----------------------------------------
    # comps_obj = [iw.Component(cid, off) for cid, off in FIXTURE_COMPS]
    # gpu = rgw.ResidentGpuWorld(comps_obj, gravity=True)
    # try:
    #     trace_rows, receipt = _run_agreement_body(gpu, comps_obj, ...)
    # finally:
    #     gpu.release()
    # return trace_rows, receipt


def _run_agreement_body(gpu, comps_obj, ticks=TICKS,
                        store_snapshots=True):
    """X1 inner: step oracle and world tick-by-tick on the SAME fixture;
    compare every comparable under the frozen windows; enforce telemetry
    budgets; record snapshots only at declared capture ticks."""
    raise SystemExit('FILL: _run_agreement_body for this card')
    # --- keep from M08 (verbatim structure): ---------------------------
    # - per tick: oracle.step; world.step_tick(tick, dp); budget check
    #   (up > TELEMETRY_BUDGET_UP_PER_TICK or down > per-comp budget ->
    #   raise E_BYTES)
    # - for name, slot in COMPARABLE: d = abs(a-b);
    #   rel = d / max(1.0, abs(a), abs(b)); window breach recorded by name
    #   with the offending [a, b, rel]; exact-zero pairs counted (A2 law)
    # - snapshots ONLY at CAPTURE_TICKS, then worst position diffs
    # - receipt: schema 'chimera.{{CARD_ID_LOWER}}_agreement.v1', fixture,
    #   windows, worsts, within_window booleans, telemetry block,
    #   order digests; snapshots attached only when store_snapshots


def p_single_writer():
    """AST scan template: device state is written only inside @cuda.jit
    kernels and the world's declared launch path; no other host method
    copies state to device. Keep the shape, set your class/method names."""
    src = (HERE / 'resident_gpu_world.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    class_methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_methods[node.name] = [
                item.name for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
    violations = []
    world = 'ResidentGpuWorld'          # FILL: your world class name
    allowed_host_writers = {'__init__', 'step_tick'}   # FILL: launch path
    for name, fn in _functions_of(tree, world):
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call) and isinstance(node.func,
                                                          ast.Attribute)
                    and node.func.attr == 'copy_to_device'
                    and name not in allowed_host_writers):
                violations.append(f'{name}:copy_to_device')
    return {'host_writer_methods': sorted(allowed_host_writers),
            'violations': violations, 'ok': not violations}


def _functions_of(tree, class_name):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef,
                                     ast.AsyncFunctionDef)):
                    yield item.name, item


def p_gates_declared():
    """The world refuses through the declared gate names. FILL: your E_*
    refusal codes (M08 declared 12)."""
    gates = []  # FILL: [rgw.E_ORDER, rgw.E_BYTES, ...]
    return {'gate_codes': sorted(gates), 'count': len(gates)}


def mode_main():
    pins = verify_input_pins()
    t0 = time.perf_counter()
    trace, receipt = run_agreement()
    t1 = time.perf_counter()
    receipt['input_pins'] = {k: 'ok' for k in pins}
    receipt['p_single_writer'] = p_single_writer()
    receipt['p_gates_declared'] = p_gates_declared()
    receipt['vacuous_guard_selftest'] = vacuous_guard_selftest()
    # FILL: X1_pass composition over YOUR receipt booleans
    receipt['X1_pass'] = bool(receipt['position_within_window']
                              and receipt['scalars_within_window']
                              and receipt['telemetry']['within_budget'])
    (HERE / 'experiment_trace.json').write_bytes(canonical({'rows': trace}))
    (HERE / 'experiment_receipt.json').write_bytes(canonical(receipt))
    (HERE / 'gpu_profile.json').write_bytes(canonical({
        'x1_wall_seconds': t1 - t0,     # profile receipt only, NEVER compared
    }))
    print(json.dumps({'X1_pass': receipt['X1_pass']}, indent=1))


def mode_rerun():
    trace, receipt = run_agreement()
    (HERE / 'experiment_trace_rerun2.json').write_bytes(canonical(
        {'rows': trace}))
    (HERE / 'experiment_receipt_rerun2.json').write_bytes(canonical(receipt))
    print('rerun written')


# X2 SCOPED DETERMINISM (M08 lesson, keep verbatim in spirit): mode_main
# augments its receipt with run-mode keys mode_rerun does not write. Declare
# that augmentation key set HERE; X2_pass demands byte-identical traces (the
# declared determinism unit) AND a receipt delta scoped to exactly those
# keys with zero shared-key differences. Full-file receipt byte identity is
# then False BY DESIGN - never widen the window after the fact; shrink it
# only by making mode_rerun write the same keys.
AUGMENTATION_KEYS = ['X1_pass', 'input_pins', 'p_gates_declared',
                     'vacuous_guard_selftest']


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
        'schema': f'chimera.{{{{CARD_ID_LOWER}}}}_determinism.v1',
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


def _cyclic_schedule(tick):
    """FILL {{CYCLIC_SCHEDULE}}: the frozen steady-state drive schedule
    (M08: 60 Pa on phases 1..40 of 80)."""
    phase = tick % 80
    return 60.0 if 1 <= phase <= 40 else 0.0


def mode_profile():
    """X3: steady-state residency/profile run. CUDA-event per-tick device
    times, host byte accounting, VRAM before/after. Timings live ONLY in
    this receipt (never byte-compared)."""
    raise SystemExit('FILL: mode_profile for this card')
    # Keep from M08: per-tick event timing (record/synchronize/elapsed),
    # budget rows per tick, percentiles p50/p95/p99/max/mean,
    # residency_within_budget boolean, state bytes total + per component,
    # VRAM free before/after, cupy pool used start/end; world released.


def mode_falsify():
    """F-arms: each tampered copy with its passing CLEAN CONTROL run FIRST
    in the same executable; tampered copies are scratch (never committed
    state). Every arm embeds clean_control evidence and a named premature
    guard; refuse_vacuous ensures aggregation actually degrades before the
    bite is credited (the M08 F2a 'discriminating' discipline).

    LAWS for the arms (FILL {{F_ARMS}}):
    - clean control FIRST: a sticky CUDA fault from tamper teardown must
      never poison the clean measurement (observed on M08: [700]).
    - the tamper must fault the BUDGET/gate, not the CUDA context (M08's
      F1 roundtrip runs through SHADOW buffers, books its own bus bytes).
    - preflight fixtures on CPU: the tampered fixture must actually
      discriminate (M08: clustered 0.30 m spacing for the BH arm; the
      standard fixture could never bite - pre-fix err was 0.0 for EVERY
      theta because of the one-element pos local).
    """
    receipt = {'schema': f'chimera.{{{{CARD_ID_LOWER}}}}_falsifiers.v1',
               'arms': {}}
    raise SystemExit('FILL: mode_falsify arms for this card')
    # receipt['F_all_green'] = all(arms)  # the aggregate the suite asserts


def mode_regression():
    """Re-run the declared upstream suite UNMODIFIED on this exact
    revision (FILL {{REGRESSION_SUITE}}: path to the pinned suite)."""
    target = str(CONTRIB / '{{REGRESSION_SUITE}}')
    proc = subprocess.run([sys.executable, '-B', target],
                          capture_output=True, text=True, timeout=3000)
    receipt = {
        'schema': f'chimera.{{{{CARD_ID_LOWER}}}}_regression.v1',
        'suite': target,
        'exit_code': proc.returncode,
        'tail': proc.stdout[-2000:],
        'P_regression_suite_green': proc.returncode == 0,
    }
    (HERE / 'regression_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: receipt[k] for k in (
        'exit_code', 'P_regression_suite_green')}, indent=1))


def main(argv):
    mode = argv[1] if len(argv) > 1 else 'main'
    # Mode names verified against MODES (job writers: copy from MODES).
    if mode not in MODES:
        raise SystemExit('unknown mode: ' + mode
                         + ' (valid: ' + ', '.join(MODES) + ')')
    fn = getattr(sys.modules[__name__], 'mode_' + mode, None)
    if fn is None:
        raise SystemExit(f"mode '{mode}' has no implementation: either fill "
                         'mode_' + mode + ' or remove it from MODES '
                         '(do not ship an undeclared arm)')
    fn()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
