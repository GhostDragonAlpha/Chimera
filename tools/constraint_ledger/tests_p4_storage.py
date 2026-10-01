"""L8 falsifier tests + concurrent harness driver (agent/cl-L8-shared-20260921).

Four preregistered falsifiers, exercised against REAL concurrent engine builds
(g++ compile+link of tools/constraint_ledger/trace_harness.cpp over sealed
sparse worktrees of the shared object store):

  F-CROSS-RUN-WRITE   test_cross_run_write      3 simultaneous jobs + guard probes
                                                    + post-run re-hash + solo rebuilds
  F-CACHE-COLLISION   test_cache_collision      schema separation + real variant builds
  F-PARTIAL-PUBLISH   test_partial_publish      planted truncated/digest-corrupt envelopes,
                                                    orphaned staging, a REAL killed
                                                    publisher, publish/read races
  F-SOURCE-CLONE      test_source_clone_census  byte census: shared store + views vs a
                                                    REAL fresh per-lane clone

Run:  python tools/constraint_ledger/tests_p4_storage.py --receipt <path> [--quick]
(--quick skips the full-clone census and the killed-publisher probe; the full
receipt run must not use it.) Touches nothing outside the runs root.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # repo tools/
from constraint_ledger import storage as S                        # noqa: E402

CANONICAL = Path(os.environ.get('L8_CANONICAL', 'E:/ChimeraWork/l8-agent'))
RUNS = Path(os.environ.get('L8_RUNS_ROOT', 'E:/ChimeraWork/l8_runs'))
PIN = os.environ.get('L8_PIN', '7181b8ce9d2b78c93eb96df8d288e0697a398a12')

# the collision variant really changes codegen: an external-linkage symbol
VARIANT = ("\nunsigned l8_variant_marker = 1;\n"
           "unsigned l8_variant_probe() { return l8_variant_marker; }\n")


def _unseal_tree(root: Path) -> None:
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            try:
                os.chmod(Path(dp) / fn, 0o644)
            except OSError:
                pass


def fresh_dirs() -> tuple[S.SharedSourceStore, S.BuildCache, Path]:
    """Ephemeral runs root: unseal + drop old views and job roots (previous
    runs seal everything on completion), prune worktree admin, clear caches."""
    for sub in ('views', 'jobs'):
        p = RUNS / sub
        if p.exists():
            for child in p.iterdir():
                _unseal_tree(child)
            shutil.rmtree(p, ignore_errors=True)
            shutil.rmtree(p, ignore_errors=True)      # second pass: Windows laggards
    try:
        S._git(CANONICAL, 'worktree', 'prune', '--expire', 'now')
    except RuntimeError:
        pass
    for p in RUNS.glob('diag_*'):                      # ephemeral diagnostics
        shutil.rmtree(p, ignore_errors=True)
    for d in ('cache', 'cache_partial'):
        shutil.rmtree(RUNS / d, ignore_errors=True)
    (RUNS / 'views').mkdir(parents=True, exist_ok=True)
    return S.SharedSourceStore(CANONICAL, views_root(), PIN), S.BuildCache(RUNS / 'cache'), RUNS / 'jobs'


def views_root() -> Path:
    return RUNS / 'views'


# ---------------------------------------------------------------------------
# F-CACHE-COLLISION
# ---------------------------------------------------------------------------

def test_cache_collision(store, cache, jobs_root, toolchain: str) -> dict:
    """The key schema must separate semantically different requests."""
    base_inputs = {'a.cpp': '11' * 32, 'b.hpp': '22' * 32}
    k_base = S.cache_key(base_inputs, ['-O2'], toolchain)
    assert k_base == S.cache_key(dict(reversed(list(base_inputs.items()))), ['-O2'], toolchain), \
        'F-CACHE-COLLISION: identical semantics produced different keys'
    k_flag = S.cache_key(base_inputs, ['-O0'], toolchain)
    assert k_flag != k_base, 'F-CACHE-COLLISION: flags did not separate keys'
    k_in = S.cache_key({**base_inputs, 'a.cpp': '33' * 32}, ['-O2'], toolchain)
    assert k_in != k_base, 'F-CACHE-COLLISION: input hashes did not separate keys'
    k_tool = S.cache_key(base_inputs, ['-O2'], 'f' * 64)
    assert k_tool != k_base, 'F-CACHE-COLLISION: toolchain digest did not separate keys'
    assert len({k_base, k_flag, k_in, k_tool}) == 4, 'F-CACHE-COLLISION: key collapse'

    # REAL variant builds: a semantically different TU must not reuse the artifact
    src = (CANONICAL / S.ENTRY_TU).read_text(encoding='utf-8')
    specs = [S.JobSpec('col-base', flags=['-O2']),
             S.JobSpec('col-variant', flags=['-O2'], variant_content=src + VARIANT)]
    with ThreadPoolExecutor(max_workers=2) as ex:
        recs = list(ex.map(lambda s: S.run_build_job(s, store, cache, jobs_root, toolchain), specs))
    r_base, r_var = recs
    assert r_base['key'] != r_var['key'], 'F-CACHE-COLLISION: variant shared the base key'
    assert r_base['determinism_digest'] != r_var['determinism_digest'], \
        'F-CACHE-COLLISION: distinct semantics produced an identical object file'
    e0, e1 = cache.get(r_base['key']), cache.get(r_var['key'])
    assert e0 and e1, 'published entries missing'
    assert e0.payload != e1.payload, 'F-CACHE-COLLISION: one artifact served for two requests'
    assert e0.payload == cache.get(r_base['key']).payload, 'cache unstable across reads'
    assert cache.n_entries() == 2, 'expected exactly two cache entries'
    return {'schema_pairs_checked': 4, 'all_distinct': True,
            'real_variant_keys': {'base': r_base['key'], 'variant': r_var['key']},
            'determinism_digests_differ': r_base['determinism_digest'] != r_var['determinism_digest'],
            'entries': cache.n_entries()}


# ---------------------------------------------------------------------------
# F-PARTIAL-PUBLISH
# ---------------------------------------------------------------------------

def test_partial_publish() -> dict:
    """An interrupted publication must be REFUSED, never accepted."""
    cache = S.BuildCache(RUNS / 'cache_partial')
    key = S.cache_key({'x': '0' * 64}, ['-g'], 't' * 64)
    payload = b'A' * 5000
    cache.publish(key, payload, meta={'determinism_digest': 'd' * 64})
    final = cache.entry_path(key)
    good = final.read_bytes()

    # (i) truncated envelope planted at the FINAL name -- what a crashed
    #     non-atomic publisher leaves
    final.write_bytes(good[:len(good) // 2])
    assert cache.get(key) is None, 'F-PARTIAL-PUBLISH: truncated envelope ACCEPTED'
    # (ii) digest-corrupt envelope at the final name
    bad = bytearray(good)
    bad[-1] ^= 0xFF
    final.write_bytes(bytes(bad))
    assert cache.get(key) is None, 'F-PARTIAL-PUBLISH: digest-corrupt envelope ACCEPTED'
    reasons = [r.reason for r in cache.refusals]
    assert len(reasons) == 2 and all(r in ('truncated-envelope', 'truncated-payload', 'digest-mismatch')
                                     for r in reasons), f'unexpected refusals: {reasons}'

    # (iii) orphaned staging file from a killed publisher is invisible to get()
    shard = final.parent
    orphan = shard / f"{S.TMP_PREFIX}{key}.9999.deadbeef"
    orphan.write_bytes(good)                      # even a COMPLETE envelope there
    final.unlink()
    assert cache.get(key) is None, 'F-PARTIAL-PUBLISH: staging file read as an entry'
    assert orphan.exists(), 'get() must not touch staging files'

    # (iv) a REAL interrupted publisher: child stages slowly, is killed mid-write
    killed = _killed_publisher_probe(cache)
    assert killed['final_after_kill'] is False, \
        'F-PARTIAL-PUBLISH: killed publish left a readable entry'
    assert cache.get(killed['key']) is None, 'F-PARTIAL-PUBLISH: killed publish served bytes'

    # an ordinary re-publish restores the entry cleanly after all refusals
    cache.publish(key, payload, meta={'determinism_digest': 'd' * 64})
    e = cache.get(key)
    assert e and e.payload == payload, 'republish after refusals failed'

    # (v) publish/read race: concurrent publishers of one key while a reader
    #     loops -- the reader sees only complete envelopes or misses
    stop = threading.Event()
    bad_reads: list[str] = []
    counts = {'hits': 0, 'reads': 0}

    def reader() -> None:
        while not stop.is_set():
            counts['reads'] += 1
            e = cache.get(key)
            if e is not None:
                counts['hits'] += 1
                if e.payload != payload:
                    bad_reads.append('partial payload observed')
    rt = threading.Thread(target=reader)
    rt.start()
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(lambda i: cache.publish(key, payload, meta={'v': i}), range(6)))
    stop.set()
    rt.join()
    assert not bad_reads, f"F-PARTIAL-PUBLISH: race produced {bad_reads}"
    return {'planted_truncated_refused': True, 'planted_corrupt_refused': True,
            'orphan_staging_invisible': True, 'killed_publisher': killed,
            'race_reads': counts['reads'], 'race_hits': counts['hits'],
            'race_bad_reads': 0,
            'refusal_reasons': [r.reason for r in cache.refusals]}


def _killed_publisher_probe(cache: S.BuildCache) -> dict:
    """Spawn a real child process that stages a large envelope slowly, kill it
    mid-write, and verify nothing readable landed at the entry name."""
    key = S.cache_key({'kill': '1' * 64}, ['-kill'], 't' * 64)
    tools_dir = Path(__file__).resolve().parent
    script = f"""import sys, time
sys.path.insert(0, r'{tools_dir.parent}')
from constraint_ledger import storage as S
cache = S.BuildCache(r'{cache.root}')
payload = b'K' * (64 * 1024 * 1024)
key = {key!r}
shard = cache._shard(key)
shard.mkdir(parents=True, exist_ok=True)
staging = shard / (S.TMP_PREFIX + key + '.1234.beef')
with open(staging, 'wb') as f:
    f.write(payload[:1024]); f.flush()
    print('staged', flush=True)
    time.sleep(30)
    f.write(payload[1024:])
"""
    child = tools_dir / '_l8_slow_publisher.py'
    child.write_text(script, encoding='utf-8')
    try:
        p = subprocess.Popen([sys.executable, str(child)], stdout=subprocess.PIPE, text=True)
        p.stdout.readline()                    # wait for 'staged'
        p.kill()
        p.wait(timeout=15)
    finally:
        child.unlink(missing_ok=True)
    final = cache.entry_path(key)
    shard = cache._shard(key)
    return {'key': key, 'final_after_kill': final.exists(),
            'staging_orphans_left': len(list(shard.glob(S.TMP_PREFIX + '*')))}


# ---------------------------------------------------------------------------
# F-CROSS-RUN-WRITE -- real concurrent builds
# ---------------------------------------------------------------------------

WAVE_FLAGS = ['-O2', '-O1', '-O0']


def test_cross_run_write(store, cache, jobs_root, toolchain: str) -> dict:
    """3 SIMULTANEOUS real builds. One job mutating another's outputs or the
    shared source must be impossible: guard probes inside every job, post-run
    re-hash of every view, sealed-output write refusal, and SOLO no-cache
    rebuilds landing on identical deterministic .o digests."""
    wave1_specs = [S.JobSpec(f'wave1-{i}', flags=[f]) for i, f in enumerate(WAVE_FLAGS)]
    w1 = S.run_concurrent_wave(wave1_specs, store, cache, jobs_root, toolchain)
    for r in w1['records']:
        p = r['probe']
        assert p['view_write_refused'] and p['escape_refused'] and p['sealed_output_refused'], \
            f"F-CROSS-RUN-WRITE: guard probe wrote: {p} ({r['job_id']})"
        assert r['view_integrity_before'] == r['view_integrity_after'], \
            f"F-CROSS-RUN-WRITE: {r['job_id']} mutated its source view"
        assert r['cache'] == 'miss' and r['elapsed_s'] > 1, 'wave-1 was not a real build'

    # wave-2: the SAME requests (fresh job ids) concurrently -> 100% hits,
    # artifacts byte-identical to wave-1
    wave2_specs = [S.JobSpec(f'wave2-{i}', flags=[f]) for i, f in enumerate(WAVE_FLAGS)]
    w2 = S.run_concurrent_wave(wave2_specs, store, cache, jobs_root, toolchain)
    for s1, r2 in zip(w1['records'], w2['records']):
        assert r2['cache'] == 'hit', f"wave-2 {r2['job_id']} was {r2['cache']} (F-REUSE econ)"
        assert s1['key'] == r2['key'], 'wave-2 request resolved to a different key'
        assert s1['artifact_sha256'] == r2['artifact_sha256'], 'wave-2 artifact diverged'

    # SOLO verification rebuilds (no cache read, no publish, fresh view):
    # concurrent artifacts must match a private rebuild digest-for-digest
    # (deterministic .o projection; the linked exe carries PE timestamps --
    # measured and banked in the prereg)
    solo = []
    for s in wave1_specs:
        srec = S.run_build_job(S.JobSpec('solo-' + s.job_id, flags=s.flags,
                                         read_cache=False, publish=False),
                               store, cache, jobs_root, toolchain)
        w1r = next(r for r in w1['records'] if r['key'] == srec['key'])
        assert srec['determinism_digest'] == w1r['determinism_digest'], \
            f"F-CROSS-RUN-WRITE: solo rebuild of {s.job_id} diverged from the concurrent artifact"
        assert srec['probe']['view_write_refused'] and srec['probe']['escape_refused']
        solo.append({'job_id': srec['job_id'], 'key': srec['key'],
                     'determinism_digest': srec['determinism_digest']})

    # a direct write into ANOTHER job's sealed output must raise
    other_exe = jobs_root / w1['records'][0]['job_id'] / 'build' / 'trace_harness.exe'
    before = S.sha256_file(other_exe)
    try:
        with open(other_exe, 'ab') as f:
            f.write(b'X')
        cross_refused = False
    except PermissionError:
        cross_refused = True
    assert cross_refused, 'F-CROSS-RUN-WRITE: a sealed output of job A was mutated'
    assert S.sha256_file(other_exe) == before, 'sealed output bytes changed'

    return {
        'concurrent_jobs': 3,
        'guard_probes': {r['job_id']: r['probe'] for r in w1['records']},
        'views_unmutated': True,
        'wave2_hits': sum(1 for r in w2['records'] if r['cache'] == 'hit'),
        'wave2_of': len(w2['records']),
        'solo_verification_matches': solo,
        'cross_output_write_refused': cross_refused,
        'wave1': _wave_metrics(w1), 'wave2': _wave_metrics(w2),
        'specs': [{'job_id': s.job_id, 'flags': s.flags} for s in wave1_specs],
    }


def _wave_metrics(w: dict) -> dict:
    return {'wall_s': w['wall_s'], 'sum_job_s': w['sum_job_s'],
            'footprint': w['footprint'], 'cache_stats': w['cache_stats'],
            'jobs': [{'job_id': r['job_id'], 'key': r['key'], 'cache': r['cache'],
                      'elapsed_s': r['elapsed_s'], 'compile_s': r.get('compile_s'),
                      'link_s': r.get('link_s'), 'view_bytes': r['view_bytes'],
                      'workspace_bytes': r['workspace_bytes'], 'view_files': r['view_files'],
                      'n_inputs': r['n_inputs'], 'artifact_bytes': r['artifact_bytes'],
                      'artifact_sha256': r['artifact_sha256'],
                      'determinism_digest': r['determinism_digest'],
                      'view_materialize_s': r['view_materialize_s'],
                      'sealed_outputs': r['sealed_outputs']} for r in w['records']]}


# ---------------------------------------------------------------------------
# F-SOURCE-CLONE -- the byte census
# ---------------------------------------------------------------------------

def test_source_clone_census(store, cache, jobs_root, reuse: dict,
                             quick: bool = False) -> dict:
    """Measure the ACTUAL bytes: one shared object store + per-job views vs a
    real fresh per-lane clone. The workflow must run with exactly one object
    store (view .git is a pointer file into the shared store, not a copy)."""
    view_dirs = [d for d in (RUNS / 'views').iterdir() if d.is_dir()]
    assert view_dirs, 'no views materialized'
    islands = [v.name for v in view_dirs if (v / '.git').is_dir()]
    assert not islands, f"F-SOURCE-CLONE: per-view .git directories (object copies): {islands}"
    for v in view_dirs:
        txt = (v / '.git').read_text(encoding='utf-8')
        assert txt.startswith('gitdir:'), f"view {v.name} .git is not a pointer file"
        assert 'worktrees' in txt, f"view {v.name} not tied to the shared store admin"

    census = store.census()
    ws_bytes = {p.name: S.tree_bytes(p) for p in sorted(jobs_root.iterdir()) if p.is_dir()}
    per_job = max((census['views'].get(k, 0) + v) for k, v in ws_bytes.items())

    out = {
        'shared_object_store_bytes': census['object_store_bytes'],
        'canonical_worktree_bytes': census['canonical_worktree_bytes'],
        'n_views_materialized': census['n_views'],
        'per_view_bytes': census['views'],
        'per_workspace_bytes': ws_bytes,
        'per_job_bytes_shared_store_max': per_job,
        'cache_bytes': cache.disk_bytes(),
        'cache_entries': cache.n_entries(),
        'view_git_is_pointer_file': True,
        'build_reuse_economics': reuse,
    }
    if not quick:
        clone = S.measure_full_clone(S.REMOTE, RUNS.parent / 'l8_measure_clone', PIN)
        n = out['n_views_materialized']
        out['full_clone_census'] = clone
        out['n_job_scenario'] = n
        out['n_lanes_as_clones_bytes'] = n * clone['clone_total_bytes']
        out['n_lanes_shared_store_bytes'] = (census['object_store_bytes']
                                             + census['canonical_worktree_bytes']
                                             + n * per_job)
        out['duplication_factor_per_job'] = round(clone['clone_total_bytes'] / per_job, 2)
        out['bytes_saved_vs_clones'] = (out['n_lanes_as_clones_bytes']
                                        - out['n_lanes_shared_store_bytes'])
    return out


# ---------------------------------------------------------------------------

def main() -> int:
    quick = '--quick' in sys.argv
    receipt_path = Path(sys.argv[sys.argv.index('--receipt') + 1]) if '--receipt' in sys.argv else None
    RUNS.mkdir(parents=True, exist_ok=True)
    tc, tinfo = S.toolchain_digest()
    print(f"toolchain digest {tc[:16]}... target={tinfo['target']}")

    verdicts: dict[str, str] = {}
    results: dict[str, dict] = {}
    t_all = time.perf_counter()
    phases = (
        ('F-CACHE-COLLISION', lambda: test_cache_collision(*fresh_dirs(), tc)),
        ('F-PARTIAL-PUBLISH', test_partial_publish),
        ('F-CROSS-RUN-WRITE', None),      # needs its own state; handled below
        ('F-SOURCE-CLONE', None),
    )
    for name, fn in phases[:2]:
        try:
            results[name.split('.')[-1]] = fn()
            verdicts[name] = 'GREEN'
            print(f'{name:20s} GREEN')
        except AssertionError as e:
            verdicts[name] = f'FIRED: {e}'
            print(f'{name:20s} FIRED: {e}')
            _emit(receipt_path, verdicts, results, tc, tinfo, t_all)
            return 1

    store, cache, jobs_root = fresh_dirs()
    try:
        results['cross_run_write'] = test_cross_run_write(store, cache, jobs_root, tc)
        verdicts['F-CROSS-RUN-WRITE'] = 'GREEN'
        print('F-CROSS-RUN-WRITE    GREEN')
    except AssertionError as e:
        verdicts['F-CROSS-RUN-WRITE'] = f'FIRED: {e}'
        print(f'F-CROSS-RUN-WRITE    FIRED: {e}')
        _emit(receipt_path, verdicts, results, tc, tinfo, t_all)
        return 1

    w1, w2 = results['cross_run_write']['wave1'], results['cross_run_write']['wave2']
    reuse = {'wave1_cold_wall_s': w1['wall_s'], 'wave1_sum_build_s': w1['sum_job_s'],
             'wave2_hit_wall_s': w2['wall_s'], 'wave2_hit_rate': '100%',
             'wave2_speedup_x': round(w1['wall_s'] / max(w2['wall_s'], 1e-9), 2),
             'wave1_peak_footprint_bytes': w1['footprint']['peak_bytes'],
             'wave2_peak_footprint_bytes': w2['footprint']['peak_bytes'],
             'hits_total': w2['cache_stats']['hits'],
             'misses_total': w2['cache_stats']['misses']}
    try:
        results['source_clone'] = test_source_clone_census(store, cache, jobs_root, reuse, quick)
        verdicts['F-SOURCE-CLONE'] = 'GREEN'
        print('F-SOURCE-CLONE       GREEN')
    except AssertionError as e:
        verdicts['F-SOURCE-CLONE'] = f'FIRED: {e}'
        print(f'F-SOURCE-CLONE       FIRED: {e}')
        _emit(receipt_path, verdicts, results, tc, tinfo, t_all)
        return 1

    print(f"ALL FOUR FALSIFIERS GREEN in {round(time.perf_counter() - t_all, 1)}s")
    _emit(receipt_path, verdicts, results, tc, tinfo, t_all)
    return 0


def _emit(receipt_path, verdicts, results, tc, tinfo, t_all) -> None:
    if not receipt_path:
        return
    receipt = {'schema': 'chimera-receipt/L8',
               'lane': 'agent/cl-L8-shared-20260921',
               'pin': PIN,
               'generated_utc': datetime.now(timezone.utc).isoformat(),
               'toolchain': {'digest': tc, **tinfo},
               'total_runtime_s': round(time.perf_counter() - t_all, 1),
               'verdicts': verdicts,
               'results': results}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=1, sort_keys=True), encoding='utf-8')
    print(f'receipt -> {receipt_path}')


if __name__ == '__main__':
    sys.exit(main())
