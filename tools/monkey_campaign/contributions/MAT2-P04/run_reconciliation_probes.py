"""MAT2-P04 reconciliation battery (records profile).

Runs the frozen identity checks and the carried ONT-P04 probe battery at this
attempt's pinned head, per the attempt's frozen PREREGISTRATION.md. This
runner is the only new code authored by this attempt; the executed probe and
pinned suite files are the merged PR #175 blobs and the pinned tree,
byte-unmodified (identity-checked before execution).

CPU-only, offline, isolated temporary fixtures; no GPU, no live registry, no
live handoff, no writes outside this attempt workspace. This runner writes
only its two result JSONs and preserved failure logs inside its own directory.
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

WS = Path(__file__).resolve().parent          # .../contributions/MAT2-P04
# parents: [0]=contributions, [1]=monkey_campaign, [2]=tools, [3]=checkout, [4]=attempt ws
ATTEMPT = WS.parents[4]                        # .../kanban-attempts/MAT2-P04/<attempt>
REF = ATTEMPT / 'reference' / 'ONT-P04'
PINNED = REF / 'pinned'
CHECKOUT = WS.parents[3]                       # attempt checkout root (branch-2 worktree)
LEGACY_SOURCE = Path(r'E:/ChimeraWork/monkey-coordination/kanban-attempts/ONT-P04'
                     '/06792d79c3704ac29df519055aabbc57/pinned'
                     '/GPU_HANDOFF_PUBLICATION_RECEIPT.untracked.json')

MERGE_COMMIT = 'b7c4b79756d03aa26552273f6339495d419d19d5'
PR_HEAD = '16390061951fc139bae539bda819cd8260d729c1'
PR158_HEAD = '68290bec4ab84238e00e9190748402177fd55937'  # superseded prior PR; source of the byte-identical carried probes
PINNED_HEAD = 'c525b82c7c3ce0128565424764293a3c85811ab3'
MANIFEST_WHOLE_SHA = 'c79f248b5f75f38f2ae04f3b43de988801ae06ddfc1f8e1aee45c2125fbc0753'
CONTROL_PY_PREFIX = '39ff01dc'
ONTOLOGY_DIR = 'tools/monkey_campaign/contributions/ONT-P04'

CARRIED_FROM_PRIOR = {
    'test_p04_contract.py': 'e9b8b62d0af01821b0d6a370b5ddee47eb078e69033734ec0793b862956f77a0',
    'test_p04_records.py': '153dd91c56f06f2f90b63a2b6cc7faab552a7544e65e0810d5875a2e978e924c',
}

SUITES = [
    ('pinned:agent_fleet:test_resources', PINNED, 'tools/agent_fleet', 'test_resources.py'),
    ('pinned:agent_fleet:test_resource_lifecycle', PINNED, 'tools/agent_fleet', 'test_resource_lifecycle.py'),
    ('pinned:agent_fleet:test_review_handoff', PINNED, 'tools/agent_fleet', 'test_review_handoff.py'),
    ('pinned:agent_fleet:test_review_handoff_claim', PINNED, 'tools/agent_fleet', 'test_review_handoff_claim.py'),
    ('pinned:agent_fleet:test_run_queue', PINNED, 'tools/agent_fleet', 'test_run_queue.py'),
    ('referent:agent_fleet:test_layer_guard', PINNED, 'tools/agent_fleet', 'test_layer_guard.py'),
    ('probe:test_p04_contract', REF, None, 'test_p04_contract.py'),
    ('probe:test_p04_records', REF, None, 'test_p04_records.py'),
    ('probe:test_gpu_handoff', REF, None, 'test_gpu_handoff.py'),
    ('probe:test_correction_records', REF, None, 'test_correction_records.py'),
    ('probe:test_correction_fencing', REF, None, 'test_correction_fencing.py'),
]

PROBE_FILES = ['test_p04_contract.py', 'test_p04_records.py', 'test_gpu_handoff.py',
               'test_correction_records.py', 'test_correction_fencing.py', 'gpu_handoff.py',
               'run_all_probes.py']


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    return sha256_bytes(Path(p).read_bytes())


def git_blob(rev, path):
    proc = subprocess.run(['git', 'show', f'{rev}:{path}'], cwd=str(CHECKOUT),
                          capture_output=True)
    if proc.returncode != 0:
        return None
    return proc.stdout


def identity_checks():
    checks = {'schema': 'chimera.monkey.mat2_p04.reconciliation_checks.v1', 'items': []}

    def record(name, ok, detail):
        checks['items'].append({'check': name, 'ok': ok, 'detail': detail})

    manifest_bytes = (REF / 'pinned_file_hashes.json').read_bytes()
    whole = sha256_bytes(manifest_bytes)
    record('P1.manifest_whole_sha256', whole == MANIFEST_WHOLE_SHA,
           f'observed {whole} expected {MANIFEST_WHOLE_SHA}')
    manifest = json.loads(manifest_bytes.decode('utf-8'))

    mismatches = []
    for key, expected in sorted(manifest.items()):
        path = REF / key
        if not path.exists():
            mismatches.append({'key': key, 'error': 'missing'})
            continue
        observed = sha256_file(path)
        if observed != expected:
            mismatches.append({'key': key, 'observed': observed, 'expected': expected})
    record('P1.pinned_tree_52_files', not mismatches,
           f'{len(manifest)} entries checked; mismatches={mismatches}')

    control_key = 'pinned/tools/agent_fleet/control.py'
    control_sha = manifest.get(control_key, '')
    record('P1.control_py_frozen', control_sha.startswith(CONTROL_PY_PREFIX),
           f'{control_key} sha256 {control_sha} (expected prefix {CONTROL_PY_PREFIX})')

    listed = subprocess.run(['git', 'ls-tree', '-r', '--name-only', MERGE_COMMIT, ONTOLOGY_DIR],
                            cwd=str(CHECKOUT), capture_output=True, text=True)
    merged_paths = [l for l in listed.stdout.splitlines() if l.strip()]
    diffs = []
    for rel in merged_paths:
        at_merge = git_blob(MERGE_COMMIT, rel)
        at_head = git_blob(PR_HEAD, rel)
        if at_merge is None or at_head is None or at_merge != at_head:
            diffs.append(rel)
    record('P2.merge_commit_equals_pr_head',
           not diffs and len(merged_paths) == 20,
           f'{len(merged_paths)} merged paths byte-compared between {MERGE_COMMIT[:12]} and '
           f'{PR_HEAD[:12]}; diffs={diffs}')

    blob_identities = {}
    for name in [f for f in PROBE_FILES if f not in CARRIED_FROM_PRIOR]:
        rel = f'{ONTOLOGY_DIR}/{name}'
        at_merge = git_blob(MERGE_COMMIT, rel)
        on_disk = (REF / name).read_bytes()
        blob_identities[name] = {
            'sha256_disk': sha256_bytes(on_disk),
            'equal_to_merge_commit_blob': at_merge is not None and at_merge == on_disk,
        }
    record('P3.executed_probes_are_merged_blobs',
           all(v['equal_to_merge_commit_blob'] for v in blob_identities.values()),
           blob_identities)

    carried = {}
    for name, expected in CARRIED_FROM_PRIOR.items():
        on_disk = (REF / name).read_bytes()
        at_158 = git_blob(PR158_HEAD, f'{ONTOLOGY_DIR}/{name}')
        carried[name] = {
            'sha256_disk': sha256_bytes(on_disk),
            'expected_carried': expected,
            'equal_to_pr158_head_blob': at_158 is not None and at_158 == on_disk,
        }
    record('P3b.carried_probes_match_pr158_and_manifest',
           all(v['sha256_disk'] == v['expected_carried']
               and v['equal_to_pr158_head_blob'] for v in carried.values()),
           carried)

    src = sha256_file(LEGACY_SOURCE) if LEGACY_SOURCE.exists() else None
    dst = sha256_file(PINNED / 'GPU_HANDOFF_PUBLICATION_RECEIPT.untracked.json')
    record('P5.untracked_receipt_provenance', src is not None and src == dst,
           {'source': str(LEGACY_SOURCE), 'source_sha256': src, 'copy_sha256': dst})

    legacy_ws = LEGACY_SOURCE.parents[1]  # .../ONT-P04/06792d79.../
    qual_copy = REF / 'qualification_receipt.json'
    qual_src = legacy_ws / 'qualification_receipt.json'
    mirror_rel = 'checkout/tools/monkey_campaign/contributions/ONT-P04/gpu_handoff.py'
    mirror_copy = REF / mirror_rel
    mirror_src = legacy_ws / mirror_rel
    merged_machine = sha256_file(REF / 'gpu_handoff.py')
    p6 = {
        'qualification_receipt_copy_sha256': sha256_file(qual_copy),
        'qualification_receipt_source_sha256': sha256_file(qual_src),
        'mirror_copy_sha256': sha256_file(mirror_copy),
        'mirror_source_sha256': sha256_file(mirror_src),
        'merged_machine_sha256': merged_machine,
    }
    p6_ok = (p6['qualification_receipt_copy_sha256'] == p6['qualification_receipt_source_sha256']
             and p6['mirror_copy_sha256'] == p6['mirror_source_sha256']
             and p6['mirror_copy_sha256'] == merged_machine)
    record('P6.legacy_untracked_layout_provenance', p6_ok, p6)

    checks['all_ok'] = all(i['ok'] for i in checks['items'])
    return checks


def run_battery():
    results = []
    failures_dir = WS / 'first_run_failures'
    all_ok = True
    for name, cwd, discover, pattern in SUITES:
        if discover:
            cmd = [sys.executable, '-B', '-m', 'unittest', 'discover',
                   '-s', discover, '-p', pattern]
        else:
            cmd = [sys.executable, '-B', '-m', 'unittest', pattern[:-3]]
        t0 = time.time()
        try:
            proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                                  encoding='utf-8', errors='replace', timeout=600)
            out, err, code = proc.stdout or '', proc.stderr or '', proc.returncode
        except subprocess.TimeoutExpired as exc:
            out = (exc.stdout or b'').decode('utf-8', 'replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
            err = (exc.stderr or b'').decode('utf-8', 'replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
            code = 'TIMEOUT'
        dt = round(time.time() - t0, 3)
        lines = (out + '\n' + err).splitlines()
        counts = ''
        verdict = ''
        for line in lines:
            ls = line.strip()
            if ls.startswith('Ran '):
                counts = ls
            if ls == 'OK' or ls.startswith('FAILED') or ls.startswith('ERROR'):
                verdict = ls
        ok = code == 0 and counts and verdict == 'OK'
        entry = {
            'suite': name,
            'command': ' '.join(cmd[1:]),
            'cwd': str(cwd),
            'exit_code': code,
            'unittest_counts': counts,
            'unittest_verdict': verdict,
            'ok': ok,
            'seconds': dt,
        }
        if not ok:
            failures_dir.mkdir(exist_ok=True)
            tag = name.replace(':', '_')
            log = failures_dir / f'{tag}.log'
            log.write_text(f'command: {" ".join(cmd)}\ncwd: {cwd}\nexit: {code}\n'
                           f'--- stdout ---\n{out}\n--- stderr ---\n{err}', encoding='utf-8')
            entry['preserved_output'] = str(log)
        m = re.search(r'Ran (\d+) tests?', counts)
        entry['tests'] = int(m.group(1)) if m else 0
        results.append(entry)
        all_ok = all_ok and ok
    return results, all_ok


def main():
    started = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    checks = identity_checks()
    results, battery_ok = run_battery()
    total = sum(r['tests'] for r in results)
    out = {
        'schema': 'chimera.monkey.mat2_p04.reconciliation.probe_run.v1',
        'task_id': 'MAT2-P04',
        'attempt_id': '90d82bf414454bb7bf7cb4b38ee5dec8',
        'agent_id': 'arrival-b06f9edfa4f64d1b9834c47b943348fb',
        'criteria_sha256': '967f4062200c2b0448f8436d507d99fcbb0989a0dcca5c39f16bb9379ddf7020',
        'pinned_attempt_head': PINNED_HEAD,
        'carried_evidence_source': {
            'pr': 'https://github.com/GhostDragonAlpha/Chimera/pull/175',
            'pr_head': PR_HEAD,
            'merge_commit': MERGE_COMMIT,
            'legacy_card': 'ONT-P04',
            'legacy_criteria_sha256': '6191e11ce3098cf90190c88a658267676e01163106dadaf883b0c48b7dc072db',
        },
        'preregistration': 'PREREGISTRATION.md (this directory; frozen before any probe run)',
        'preregistration_sha256': sha256_file(WS / 'PREREGISTRATION.md'),
        'preregistration_addendum_sha256': sha256_file(WS / 'PREREGISTRATION-ADDENDUM.md'),
        'preregistration_addendum_2_sha256': sha256_file(WS / 'PREREGISTRATION-ADDENDUM-2.md'),
        'profile': 'records (offline); CPU-only fixtures; no GPU; no live registry; '
                   'no live handoff; no process launches beyond python -B test processes; '
                   'loopback-only servers inside pinned fixtures',
        'started_utc': started,
        'identity_checks': checks,
        'battery': results,
        'battery_total_tests': total,
        'battery_all_ok': battery_ok,
        'all_ok': bool(checks['all_ok'] and battery_ok),
    }
    (WS / 'probe_run_results.json').write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (WS / 'reconciliation_checks.json').write_text(
        json.dumps(checks, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'identity_all_ok': checks['all_ok'], 'battery_all_ok': battery_ok,
                      'battery_total_tests': total}, indent=1))
    return 0 if out['all_ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
