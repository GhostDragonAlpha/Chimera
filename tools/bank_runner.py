"""bank_runner.py — card-lane bank runner: one-process sequential banking
with byte-equality certification hooks and [700]-class fault containment.

Repo-side adoption of the certified TEST-ACCELERATION banking (card-kit
coordination space, 2026-09-29/30; see tools/gpu-queue/PROTOCOL.md for the
queue-side law and the measured table):

  baseline    N fresh interpreters, one per fixture — the status quo bank
              arm; the isolation boundary for tamper/sanitizer/first-bank
              arms is exactly this process boundary (the [700] law).
  seq         ONE process, fixtures one after another (imports amortized).
              THE DEFAULT BANK MODE (GPU-certified 2.50x vs fresh-process;
              per-fixture completion records make the respawn boundary
              exact).
  batched     ONE process, ONE world with all fixtures' components
              concatenated (GPU-certified 3.15x; lawful for GLOBALLY-
              DISJOINT clean fixtures only — REFUSALS below).
  measure     CPU-mode certification + speedup receipt: baseline vs seq
              byte-equality (the hooks), optional --expect-sha pins,
              position-deconfounded timing (seq/baseline order alternates
              per repeat).

All modes drive the card's CPU oracle (kernel_mirror.MirrorWorld + the
M01/M03/M04/M06/M07 pin stack) READ-ONLY from --card-dir (default
MAT2-M08): sys.dont_write_bytecode is forced before imports and an output
path inside the card dir is refused. The GPU bank itself still runs through
the coordination gpu-queue per tools/gpu-queue/PROTOCOL.md (one job = ONE
process; no job spawns further GPU processes); seq/batched emit per-fixture
records shaped for the queue's done/<id>.result.json aggregation and for
certify-style byte-equality pairing (trace_sha256 + per_component_sha256 +
slice map). `measure` spawns baseline worker SUBPROCESSES and is a lane-host
utility, not a queue job shape.

REFUSALS (by design, exit 1 — a refusal is evidence, not a crash):
  batched_refused_far_field            the far-field direct-sum pass reads
                                       ALL states: concatenating fixtures
                                       changes every existing row (measured
                                       negative control, probe P3).
  batched_refused_overlapping_offsets  per-component decomposability is
                                       proven for globally DISTINCT x_offsets
                                       only (drained red ta-batch-b/c).
  batched_refused_maxwell_elements_differ  one world takes k_el/c_el from
                                       components[0]; mixed-constant fixtures
                                       would falsify each other.
  batched_refused_non_clean_arm        tamper/sanitizer/first_bank arms
                                       never batch.
  seq_refused_sanitizer_arm            sanitizer serializes and distorts
                                       timing: isolated worker jobs only.
  out_path_inside_card_dir_refused     the card dir stays read-only.
  fixture_spec_invalid / family_spec_invalid / unknown_arm / expect_sha
                                       malformed input pins.

FAULT CONTAINMENT (the [700] lessons: a poisoned context/process
invalidates everything scheduled after it in that process): in seq/batched,
ANY exception stops the run — each fixture's record is written to
<out>.<name>.json the moment it completes (the exact completion boundary),
the failure is recorded, and the process EXITS 3 immediately. Respawn = a
NEW job containing only the REMAINING fixtures (fresh process = fresh
context); nothing is silently skipped or double-run. Ordering law inside
one process: clean fixtures first, tamper arms last (stable reorder; both
orders are recorded in the receipt).

Usage (run with python -B from the repo root):
  python -B tools/bank_runner.py worker  --spec S.json --out R.json
  python -B tools/bank_runner.py seq     --specs S1.json,S2.json --out R.json
  python -B tools/bank_runner.py batched --specs S1.json,S2.json --out R.json
  python -B tools/bank_runner.py measure --fixtures F.json --out R.json
      [--repeat 1] [--expect-sha name=sha[,name=sha...]]

Fixture spec = {"name": str, "components": [[component_id, x_offset_m],
...]}; optional "arm": "clean"|"tamper"|"sanitizer"|"first_bank" (default
clean) and "far_field": bool (default false). A family file for measure =
{"fixtures": [spec, ...]}. Exit codes: 0 green (all byte-equality checks
true), 1 refusal/red, 2 usage, 3 fault-containment stop.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import pathlib
import subprocess
import sys
import time

SCHEMA = 'chimera.monkey_campaign.bank_runner.v1'
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CARD_DIR = (REPO_ROOT / 'tools' / 'monkey_campaign' /
                    'contributions' / 'MAT2-M08')
# The oracle code-identity stack: contribution cards whose bytes define
# oracle behavior (M01 material state, M03 pressure, M04 passive response,
# M06 local contact, M07 integrated step, M08 kernel mirror).
DEPENDENCY_CARDS = ('MAT2-M01', 'MAT2-M03', 'MAT2-M04', 'MAT2-M06',
                    'MAT2-M07')
ORACLE_CODE_IDS = {
    'MAT2-M01': 'material_state.py',
    'MAT2-M03': 'pressure_membrane.py',
    'MAT2-M04': 'passive_response.py',
    'MAT2-M06': 'local_contact.py',
    'MAT2-M07': 'integrated_step.py',
    'MAT2-M08': 'kernel_mirror.py',
}
TICKS_DEFAULT = 6  # M08 falsify-family tick count
TRACE_FORMAT_VERSION = 'bank.trace.v1'
CLEAN_ARM = 'clean'
KNOWN_ARMS = ('clean', 'tamper', 'sanitizer', 'first_bank')


# ------------------------------------------------------------ card loading --

def card_paths(card_dir):
    """Read-only card paths: the card dir plus its pinned dependency cards."""
    card_dir = pathlib.Path(card_dir).resolve()
    contrib = card_dir.parent
    require((card_dir / 'kernel_mirror.py').is_file(),
            'card_dir_missing_kernel_mirror')
    paths = [contrib / dep / ORACLE_CODE_IDS[dep] for dep in DEPENDENCY_CARDS]
    paths.append(card_dir / 'kernel_mirror.py')
    for p in paths:
        require(p.is_file(), f'oracle_code_file_missing:{p}')
    return card_dir, contrib, paths


def ensure_import_paths(card_dir, contrib):
    sys.dont_write_bytecode = True  # never drop __pycache__ into the cards
    dirs = [contrib / dep for dep in DEPENDENCY_CARDS] + [card_dir]
    for d in dirs:
        if str(d) not in sys.path:
            sys.path.insert(0, str(d))


def load_modules(card_dir, contrib):
    """Import (integrated_step, kernel_mirror) from the card stack."""
    ensure_import_paths(card_dir, contrib)
    t0 = time.perf_counter()
    iw = importlib.import_module('integrated_step')
    t_iw = time.perf_counter() - t0
    t0 = time.perf_counter()
    km = importlib.import_module('kernel_mirror')
    t_km = time.perf_counter() - t0
    return iw, km, {'import_integrated_step_s': t_iw,
                    'import_kernel_mirror_s': t_km}


def oracle_version_sha(paths):
    """Content sha binding certification to the exact oracle code bytes."""
    h = hashlib.sha256()
    for p in paths:
        b = pathlib.Path(p).read_bytes()
        h.update(p.name.encode('utf-8'))
        h.update(b'\x00')
        h.update(hashlib.sha256(b).digest())
    return h.hexdigest()


# ---------------------------------------------------------------- fixtures --

def require(condition, code):
    if not condition:
        raise SystemExit(f'bank_runner: {code}')


def arm_of(spec):
    return str(spec.get('arm', CLEAN_ARM)).strip().lower()


def read_json_file(path):
    p = pathlib.Path(path)
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except OSError:
        raise SystemExit(f'bank_runner: spec_file_unreadable:{path}')


def validate_spec(spec):
    require(isinstance(spec.get('name'), str)
            and isinstance(spec.get('components'), list)
            and spec['components'], 'fixture_spec_invalid')
    require(all(isinstance(c, (list, tuple)) and len(c) == 2
                for c in spec['components']), 'fixture_spec_invalid')
    require(arm_of(spec) in KNOWN_ARMS,
            f'unknown_arm:{arm_of(spec)}')
    # requester-side malformed input is a load-time refusal, not a mid-run
    # fault: offsets must convert to float HERE (the [700] fault-stop below
    # is reserved for genuine runtime faults)
    for _, off in spec['components']:
        try:
            float(off)
        except (TypeError, ValueError):
            raise SystemExit(f'bank_runner: fixture_spec_invalid_offset:'
                             f'{off!r}')


def load_spec(path):
    spec = read_json_file(path)
    validate_spec(spec)
    return spec


def load_specs(comma_paths):
    specs = [load_spec(p.strip()) for p in comma_paths.split(',') if p.strip()]
    require(bool(specs), 'no_specs_given')
    return specs


def load_family(path):
    obj = read_json_file(path)
    require(isinstance(obj.get('fixtures'), list) and obj['fixtures'],
            'family_spec_invalid')
    for spec in obj['fixtures']:
        validate_spec(spec)
    return obj['fixtures']


def check_out_path(out, card_dir):
    out = pathlib.Path(out).resolve()
    require(card_dir not in out.parents and out != card_dir,
            'out_path_inside_card_dir_refused')
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def write_json(path, obj):
    pathlib.Path(path).write_text(
        json.dumps(obj, indent=1, sort_keys=True), encoding='utf-8')


# ------------------------------------------------------------- oracle run --

def build_components(iw, spec):
    """iw.Component objects from a spec. Zero-mass components are NOT
    lawful (M07 Component fixes per-vertex masses); offsets are float()
    converted here, inside the caller's fault-containment boundary."""
    return [iw.Component(str(cid), float(off))
            for cid, off in spec['components']]


def run_fixture(iw, km, spec, ticks=TICKS_DEFAULT, far_field=False):
    """One solo world; trace = per-tick per-component diagnostic blocks,
    serialized little-endian C-order (the bytes a resident world would
    read back over the bus)."""
    import numpy as np
    t_fn0 = time.perf_counter()
    comps = build_components(iw, spec)
    t0 = time.perf_counter()
    world = km.MirrorWorld(comps, gravity=True, far_field=far_field)
    t_build = time.perf_counter() - t0
    per_tick = []
    t_first = None
    t0 = time.perf_counter()
    for tick in range(ticks):
        dp = float(iw.PRESS_SCHEDULE.get(tick, 0.0))
        world.step_tick(tick, dp)
        if t_first is None:
            t_first = time.perf_counter() - t0
        per_tick.append(np.stack([st['block'] for st in world.states]))
    t_step = time.perf_counter() - t0
    arr = np.concatenate(per_tick, axis=0)  # (ticks*n_comp, diag)
    n_comp = len(comps)
    return {'name': spec['name'], 'ticks': ticks,
            'far_field': bool(far_field), 'arm': arm_of(spec),
            'n_comp': n_comp,
            'x_offsets_m': [float(off) for _, off in spec['components']],
            'build_s': t_build, 'first_tick_s': t_first, 'step_s': t_step,
            'work_s': t_build + t_step,
            'wall_s': time.perf_counter() - t_fn0,
            'trace': arr,
            'diag_f64_per_comp': int(arr.shape[1]),
            'trace_sha256': sha256_bytes(
                np.ascontiguousarray(arr, dtype='<f8').tobytes()),
            'per_component_sha256': per_component_shas(
                arr, ticks, n_comp)}


def per_component_shas(arr, ticks, n_comp):
    import numpy as np
    out = []
    grid = arr.reshape(ticks, n_comp, -1)
    for i in range(n_comp):
        out.append(sha256_bytes(np.ascontiguousarray(
            grid[:, i, :], dtype='<f8').tobytes()))
    return out


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def public_record(r):
    """Receipt record — the trace array itself never leaves the process."""
    return {k: v for k, v in r.items() if k != 'trace'}


# ------------------------------------------------------------------ worker --

def cmd_worker(args):
    """One fixture in a fresh interpreter: the baseline unit AND the
    process-isolated arm (tamper/sanitizer/first_bank)."""
    spec = load_spec(args.spec)
    card_dir, contrib, code_ids = card_paths(args.card_dir)
    out = check_out_path(args.out, card_dir)
    t_start = time.perf_counter()
    iw, km, imp = load_modules(card_dir, contrib)
    t_imp = time.perf_counter() - t_start
    r = run_fixture(iw, km, spec, ticks=args.ticks,
                    far_field=bool(spec.get('far_field'))
                    or args.far_field)
    rec = public_record(r)
    out_rec = {'schema': SCHEMA, 'mode': 'worker', 'card_dir': str(card_dir),
               'oracle_version_sha': oracle_version_sha(code_ids),
               'import_s': t_imp, 'imports': imp,
               'total_s': time.perf_counter() - t_start, **rec}
    write_json(out, out_rec)
    print(json.dumps({'mode': 'worker', 'name': rec['name'],
                      'trace_sha256': rec['trace_sha256'][:16],
                      'total_s': round(out_rec['total_s'], 4)}))
    return 0


# -------------------------------------------------------------------- seq --

def ordered_specs(specs):
    """Ordering law: clean first, non-clean last (stable); both orders
    recorded in the receipt."""
    executed = sorted(specs, key=lambda s: 0 if arm_of(s) == CLEAN_ARM else 1)
    return executed, {
        'requested': [s['name'] for s in specs],
        'executed': [s['name'] for s in executed],
        'law': 'clean fixtures first, tamper arms last ([700] F1 lesson)'}


def cmd_seq(args):
    """ONE process, fixtures one after another. THE DEFAULT BANK MODE."""
    specs = load_specs(args.specs)
    card_dir, contrib, code_ids = card_paths(args.card_dir)
    out = check_out_path(args.out, card_dir)
    for spec in specs:
        require(arm_of(spec) != 'sanitizer', 'seq_refused_sanitizer_arm')
    executed, order = ordered_specs(specs)
    iw, km, imp = load_modules(card_dir, contrib)
    t_all = time.perf_counter()
    results = []
    failure = None
    for spec in executed:
        try:
            r = run_fixture(iw, km, spec, ticks=args.ticks,
                            far_field=bool(spec.get('far_field'))
                            or args.far_field)
        except Exception as exc:  # noqa: BLE001  fail-stop ([700] law)
            failure = repr(exc)
            break  # a poisoned process invalidates everything after it
        rec = public_record(r)
        results.append(rec)
        # completion boundary file lands BEFORE anything else can fail
        write_json(str(out) + f'.{rec["name"]}.json',
                   {'schema': SCHEMA, 'mode': 'seq', 'name': rec['name'],
                    **rec})
    out_rec = {'schema': SCHEMA, 'mode': 'seq', 'card_dir': str(card_dir),
               'oracle_version_sha': oracle_version_sha(code_ids),
               'ticks': args.ticks, 'imports': imp, 'order': order,
               'results': results, 'failure': failure,
               'fixtures_completed': len(results),
               'fixtures_requested': len(specs),
               'wall_s': time.perf_counter() - t_all,
               'python': sys.version.split()[0]}
    write_json(out, out_rec)
    print(json.dumps({k: out_rec[k] for k in
                      ('mode', 'wall_s', 'fixtures_completed', 'failure')},
                     indent=1))
    if failure is not None:
        return 3
    return 0 if len(results) == len(specs) else 3


# ----------------------------------------------------------------- batched --

def cmd_batched(args):
    """ONE process, ONE world with all fixtures' components concatenated.
    Lawful for globally-disjoint clean near-field fixtures only."""
    import numpy as np
    specs = load_specs(args.specs)
    card_dir, contrib, code_ids = card_paths(args.card_dir)
    out = check_out_path(args.out, card_dir)

    def refuse(code):
        write_json(out, {'schema': SCHEMA, 'mode': 'batched',
                         'card_dir': str(card_dir), 'refused': True,
                         'failure': code,
                         'fixtures_completed': 0,
                         'fixtures_requested': len(specs)})
        print(json.dumps({'mode': 'batched', 'refused': True,
                          'failure': code}, indent=1))
        return 1

    if args.far_field or any(spec.get('far_field') for spec in specs):
        return refuse('batched_refused_far_field')
    if any(arm_of(spec) != CLEAN_ARM for spec in specs):
        return refuse('batched_refused_non_clean_arm')
    merged = []
    fixture_slices = []
    idx = 0
    for spec in specs:
        for cid, off in spec['components']:
            merged.append([f'{cid}__{spec["name"]}', float(off)])
        k = len(spec['components'])
        fixture_slices.append({'name': spec['name'], 'start_comp': idx,
                               'n_comp': k})
        idx += k
    offsets = [float(off) for _, off in merged]
    dupes = sorted({o for o in offsets if offsets.count(o) > 1})
    if dupes:
        return refuse('batched_refused_overlapping_offsets:'
                      + repr(dupes))
    iw, km, imp = load_modules(card_dir, contrib)
    t_all = time.perf_counter()
    results = []
    whole_world = None
    failure = None
    try:
        comps = build_components(iw, {'name': 'batched',
                                      'components': merged})
        # one world takes k_el/c_el from components[0]
        elements = {tuple(map(float, c.maxwell_element())) for c in comps}
        if len(elements) != 1:
            return refuse('batched_refused_maxwell_elements_differ')
        world = km.MirrorWorld(comps, gravity=True, far_field=False)
        per_tick = []
        t_first = None
        t0 = time.perf_counter()
        for tick in range(args.ticks):
            dp = float(iw.PRESS_SCHEDULE.get(tick, 0.0))
            world.step_tick(tick, dp)
            if t_first is None:
                t_first = time.perf_counter() - t0
            per_tick.append(np.stack([st['block'] for st in world.states]))
        t_step = time.perf_counter() - t0
        arr = np.concatenate(per_tick, axis=0)
        diag = int(arr.shape[1])
        n_comp = len(merged)
        grid = arr.reshape(args.ticks, n_comp, -1)
        whole_world = {
            'trace_sha256': sha256_bytes(
                np.ascontiguousarray(arr, dtype='<f8').tobytes()),
            'n_comp': n_comp, 'diag_f64_per_comp': diag,
            'slice_map': {'layout': 'tick-major, comp-minor; one '
                                    'diag-wide f64 block per component '
                                    'per tick',
                          'source': 'world.states blocks, bank_runner '
                                    'CPU batched mode'},
            'fixture_slices': fixture_slices}
        for fs in fixture_slices:
            spec = next(s for s in specs if s['name'] == fs['name'])
            k = fs['n_comp']
            lo, hi = fs['start_comp'], fs['start_comp'] + k
            sub = np.ascontiguousarray(
                grid[:, lo:hi, :], dtype='<f8')
            slice_bytes = sub.reshape(args.ticks * k, -1).tobytes()
            rec = {
                'name': fs['name'], 'arm': CLEAN_ARM, 'n_comp': k,
                'x_offsets_m': [float(o) for _, o in spec['components']],
                'trace_sha256': sha256_bytes(slice_bytes),
                'per_component_sha256': [
                    sha256_bytes(np.ascontiguousarray(
                        grid[:, i, :], dtype='<f8').tobytes())
                    for i in range(lo, hi)],
                'slice_attribution': {'start_comp': lo, 'n_comp': k,
                                      'cols_per_fixture': k * diag},
                'step_s': t_step, 'first_tick_s': t_first,
            }
            rec['component_id_map'] = {
                f'{cid}__{spec["name"]}': rec['per_component_sha256'][j]
                for j, (cid, _) in enumerate(spec['components'])}
            results.append(rec)
            write_json(str(out) + f'.{rec["name"]}.json',
                       {'schema': SCHEMA, 'mode': 'batched', **rec})
    except Exception as exc:  # noqa: BLE001  fail-stop ([700] law)
        failure = repr(exc)
    out_rec = {'schema': SCHEMA, 'mode': 'batched',
               'card_dir': str(card_dir),
               'oracle_version_sha': oracle_version_sha(code_ids),
               'ticks': args.ticks, 'imports': imp, 'results': results,
               'whole_world': whole_world, 'failure': failure,
               'fixtures_completed': len(results),
               'fixtures_requested': len(specs),
               'wall_s': time.perf_counter() - t_all,
               'python': sys.version.split()[0]}
    write_json(out, out_rec)
    print(json.dumps({k: out_rec[k] for k in
                      ('mode', 'wall_s', 'fixtures_completed', 'failure')},
                     indent=1))
    if failure is not None:
        return 3
    return 0 if len(results) == len(specs) else 3


# ----------------------------------------------------------------- measure --

def cmd_measure(args):
    """CPU-mode certification + speedup: baseline (fresh processes) vs
    sequential (one process). Green REQUIRES per-fixture byte-identity
    and every --expect-sha pin."""
    fixtures = load_family(args.fixtures)
    require(all(arm_of(s) == CLEAN_ARM for s in fixtures),
            'measure_refused_non_clean_arm')
    card_dir, contrib, code_ids = card_paths(args.card_dir)
    out = check_out_path(args.out, card_dir)
    here = str(pathlib.Path(__file__).resolve())
    scratch = out.parent
    pins = parse_expect_sha(args.expect_sha)
    repeats = []
    all_identical = True
    pins_ok = True
    seq_last = {}
    for rep in range(max(1, int(args.repeat))):
        # position deconfound: alternate which arm goes first
        do_seq_first = bool(rep % 2)
        arms = {}
        for arm_name in (('seq', 'baseline') if do_seq_first
                         else ('baseline', 'seq')):
            if arm_name == 'baseline':
                arms['baseline'] = run_baseline(fixtures, args.ticks,
                                                scratch, here,
                                                str(card_dir))
            else:
                t0 = time.perf_counter()
                iw, km, imp = load_modules(card_dir, contrib)
                rows = []
                for spec in fixtures:
                    r = run_fixture(iw, km, spec, ticks=args.ticks,
                                    far_field=bool(spec.get('far_field')))
                    rows.append(public_record(r))
                arms['seq'] = {'rows': rows,
                               'wall_s': time.perf_counter() - t0,
                               'import_s_first_load': imp}
        base, seq = arms['baseline'], arms['seq']
        for row in seq['rows']:
            seq_last[row['name']] = row['trace_sha256']
        eq = {b['name']: b['trace_sha256'] == s['trace_sha256']
              for b, s in zip(base, seq['rows'])}
        all_identical = all_identical and all(eq.values())
        base_sum = sum(r['wall_s'] for r in base)
        seq_sum = sum(r['wall_s'] for r in seq['rows'])
        repeats.append({
            'rep': rep, 'n_fixtures': len(fixtures), 'ticks': args.ticks,
            'seq_ran_first': do_seq_first,
            'baseline': {'per_fixture': base, 'sum_s': base_sum},
            'sequential': {'per_fixture': seq['rows'],
                           'sum_s': seq_sum,
                           'import_s_first_load': seq['import_s_first_load']},
            'equivalence': {'baseline_vs_sequential': eq,
                            'all_byte_identical': all(eq.values())},
            'speedup': {'sequential_vs_baseline':
                        base_sum / seq_sum if seq_sum else None},
        })
    pin_rows = []
    for name, want in pins.items():
        got = seq_last.get(name)
        ok = bool(got) and got.startswith(want)
        pins_ok = pins_ok and ok
        pin_rows.append({'name': name, 'expected_sha256': want,
                         'actual_sha256': got, 'ok': ok})
    verdict = 'GREEN' if (all_identical and pins_ok) else 'RED'
    receipt = {'schema': SCHEMA, 'mode': 'measure',
               'backend': 'cpu_oracle_km_MirrorWorld',
               'card_dir': str(card_dir),
               'oracle_version_sha': oracle_version_sha(code_ids),
               'fixtures': [s['name'] for s in fixtures],
               'repeats': repeats,
               'byte_equality': {
                   'all_byte_identical_baseline_vs_sequential':
                       all_identical},
               'expect_sha_pins': pin_rows,
               'verdict': verdict,
               'trace_format': TRACE_FORMAT_VERSION,
               'python': sys.version.split()[0]}
    write_json(out, receipt)
    print(json.dumps({'verdict': verdict,
                      'all_byte_identical': all_identical,
                      'pins_ok': pins_ok,
                      'speedup_seq_vs_baseline_median':
                          _median([r['speedup']['sequential_vs_baseline']
                                   for r in repeats])}, indent=1))
    return 0 if verdict == 'GREEN' else 1


def parse_expect_sha(arg):
    pins = {}
    if not arg:
        return pins
    for item in arg.split(','):
        require('=' in item, 'expect_sha_pin_invalid')
        name, sha = item.split('=', 1)
        sha = sha.strip().lower()
        require(8 <= len(sha) <= 64 and all(
            ch in '0123456789abcdef' for ch in sha),
            'expect_sha_pin_invalid')
        pins[name.strip()] = sha
    return pins


def run_baseline(fixtures, ticks, scratch, runner_path, card_dir):
    """N fresh interpreters; this parent wall-clocks each subprocess."""
    rows = []
    scratch = pathlib.Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    for i, spec in enumerate(fixtures):
        spec_p = scratch / f'_bank_baseline_spec_{i}.json'
        out_p = scratch / f'_bank_baseline_result_{i}.json'
        write_json(spec_p, spec)
        if out_p.exists():
            out_p.unlink()
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, '-B', runner_path, 'worker', '--spec',
             str(spec_p), '--ticks', str(ticks), '--out', str(out_p),
             '--card-dir', card_dir],
            capture_output=True, text=True)
        wall = time.perf_counter() - t0
        if proc.returncode != 0:
            raise SystemExit(f'baseline worker failed: '
                             f'{proc.stderr[-800:]}')
        res = json.loads(out_p.read_text(encoding='utf-8'))
        rows.append({'name': res['name'], 'wall_s': wall,
                     'import_s': res['import_s'],
                     'work_s': res['work_s'],
                     'trace_sha256': res['trace_sha256']})
    return rows


def _median(vals):
    vs = sorted(vals)
    m = len(vs) // 2
    return vs[m] if len(vs) % 2 else 0.5 * (vs[m - 1] + vs[m])


# -------------------------------------------------------------------- main --

def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Card-lane bank runner (sequential default; batched '
                    'for disjoint clean fixtures; [700] fault '
                    'containment). See module docstring.')
    sub = ap.add_subparsers(dest='cmd', required=True)

    def add_common(p, specs_mode):
        p.add_argument('--card-dir', default=str(DEFAULT_CARD_DIR),
                       help='read-only card dir providing kernel_mirror.py'
                            ' (default MAT2-M08)')
        if specs_mode:
            p.add_argument('--specs', required=True,
                           help='comma-separated fixture spec json files')
        p.add_argument('--out', required=True)
        p.add_argument('--ticks', type=int, default=TICKS_DEFAULT)

    w = sub.add_parser('worker', help='one fixture, fresh interpreter')
    add_common(w, specs_mode=False)
    w.add_argument('--spec', required=True)
    w.add_argument('--far-field', action='store_true')
    w.set_defaults(fn=cmd_worker)

    s = sub.add_parser('seq', help='ONE process, fixtures in order '
                                   '(default bank mode)')
    add_common(s, specs_mode=True)
    s.add_argument('--far-field', action='store_true')
    s.set_defaults(fn=cmd_seq)

    b = sub.add_parser('batched', help='ONE process, ONE world (disjoint '
                                       'clean fixtures only)')
    add_common(b, specs_mode=True)
    b.add_argument('--far-field', action='store_true')
    b.set_defaults(fn=cmd_batched)

    m = sub.add_parser('measure', help='baseline-vs-seq byte-equality '
                                       'certification + speedup')
    add_common(m, specs_mode=False)
    m.add_argument('--fixtures', required=True,
                   help='family file: {"fixtures": [spec, ...]}')
    m.add_argument('--repeat', type=int, default=1)
    m.add_argument('--expect-sha', default=None,
                   help='pins name=sha256 (16-hex prefix ok)')
    m.set_defaults(fn=cmd_measure)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == '__main__':
    sys.exit(main())
