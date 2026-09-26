"""Run the frozen ONT-P04 correction probe battery and record exact results.

Final verification pass (after PREREGISTRATION.md freeze). CPU-only, offline,
isolated temporary fixtures; no GPU, no live registry, no live handoff.
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

WS = Path(__file__).resolve().parent
PINNED = WS / 'pinned'

SUITES = [
    ('pinned:agent_fleet:test_resources', PINNED, 'tools/agent_fleet', 'test_resources.py'),
    ('pinned:agent_fleet:test_resource_lifecycle', PINNED, 'tools/agent_fleet', 'test_resource_lifecycle.py'),
    ('pinned:agent_fleet:test_review_handoff', PINNED, 'tools/agent_fleet', 'test_review_handoff.py'),
    ('pinned:agent_fleet:test_review_handoff_claim', PINNED, 'tools/agent_fleet', 'test_review_handoff_claim.py'),
    ('pinned:agent_fleet:test_run_queue', PINNED, 'tools/agent_fleet', 'test_run_queue.py'),
    ('probe:test_p04_contract', WS, None, 'test_p04_contract.py'),
    ('probe:test_p04_records', WS, None, 'test_p04_records.py'),
    ('probe:test_gpu_handoff', WS, None, 'test_gpu_handoff.py'),
    ('probe:test_correction_records', WS, None, 'test_correction_records.py'),
    ('probe:test_correction_fencing', WS, None, 'test_correction_fencing.py'),
]

CARRIED_FROM_PRIOR = {
    'test_p04_contract.py': 'e9b8b62d0af01821b0d6a370b5ddee47eb078e69033734ec0793b862956f77a0',
    'test_p04_records.py': '153dd91c56f06f2f90b63a2b6cc7faab552a7544e65e0810d5875a2e978e924c',
}


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


results = []
all_ok = True
for name, cwd, discover, pattern in SUITES:
    if discover:
        cmd = [sys.executable, '-B', '-m', 'unittest', 'discover',
               '-s', discover, '-p', pattern]
    else:
        cmd = [sys.executable, '-B', '-m', 'unittest', pattern[:-3]]
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          timeout=600)
    dt = round(time.time() - t0, 3)
    lines = ((proc.stdout or '') + '\n' + (proc.stderr or '')).splitlines()
    summary = ''
    for line in lines:
        ls = line.strip()
        if ls.startswith('Ran ') or ls == 'OK' or ls.startswith('FAILED'):
            summary = ls
    ok = proc.returncode == 0 and 'OK' in summary and 'FAILED' not in summary
    counts = ''
    for line in lines:
        if line.strip().startswith('Ran '):
            counts = line.strip()
    results.append({
        'suite': name,
        'command': ' '.join(cmd[1:]),
        'cwd': str(cwd),
        'exit_code': proc.returncode,
        'unittest_summary': counts or f'(exit {proc.returncode})',
        'ok': ok,
        'seconds': dt,
    })
    all_ok = all_ok and ok

total = 0
for r in results:
    m = re.search(r'Ran (\d+) tests?', r['unittest_summary'])
    r['tests'] = int(m.group(1)) if m else 0
    total += r['tests']

out = {
    'schema': 'chimera.monkey.p04.correction.probe_run.v2',
    'task_id': 'ONT-P04',
    'attempt_id': '06792d79c3704ac29df519055aabbc57',
    'corrects_publication_request': 'publication-a6c5aa2fbd4446dfa94852038d3fea1b',
    'prior_attempt_id': '4f4df57ef3d54c0996cf969e8a599d1b',
    'prior_head': '68290bec4ab84238e00e9190748402177fd55937',
    'pinned_attempt_head': 'c525b82c7c3ce0128565424764293a3c85811ab3',
    'criteria_sha256': '6191e11ce3098cf90190c88a658267676e01163106dadaf883b0c48b7dc072db',
    'lead_ruling': 'CHANGES_REQUIRED msg-5feabcb2d57f49e9a70d8e366b62095e: '
                   'foreign enrolled gamer could mutate training drain '
                   'evidence and unload accepted a different restoration '
                   'config; fence mutations by live request '
                   'owner/generation/instance or supervisor authority, '
                   'require registered restore configuration, add '
                   'foreign/stale/config regressions',
    'preregistration_addendum_sha256': sha256_file(
        WS / 'PREREGISTRATION-CORRECTION-ADDENDUM.md'),
    'profile': 'records (offline); CPU-only fixtures; no GPU; no live registry; '
               'no live handoff; no process launches beyond python -B tests; '
               'loopback-only servers inside pinned fixtures',
    'python': sys.version,
    'suites': results,
    'total_tests': total,
    'all_ok': all_ok,
    'carried_forward_hash_verified': {
        f: {'expected': h, 'actual': sha256_file(WS / f),
            'identical': sha256_file(WS / f) == h}
        for f, h in CARRIED_FROM_PRIOR.items()
    },
    'deliverable_hashes': {
        'PREREGISTRATION.md': sha256_file(WS / 'PREREGISTRATION.md'),
        'PREREGISTRATION-CORRECTION-ADDENDUM.md': sha256_file(
            WS / 'PREREGISTRATION-CORRECTION-ADDENDUM.md'),
        'gpu_handoff.py': sha256_file(WS / 'gpu_handoff.py'),
        'test_gpu_handoff.py': sha256_file(WS / 'test_gpu_handoff.py'),
        'test_correction_records.py': sha256_file(WS / 'test_correction_records.py'),
        'test_correction_fencing.py': sha256_file(WS / 'test_correction_fencing.py'),
        'pinned_file_hashes.json': sha256_file(WS / 'pinned_file_hashes.json'),
    },
}
with open(WS / 'probe_run_results.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)
print(json.dumps({k: out[k] for k in ('total_tests', 'all_ok')}, indent=2))
for r in results:
    print(('PASS' if r['ok'] else 'FAIL'), r['suite'], r['unittest_summary'],
          f"{r['seconds']}s")
carried_ok = all(v['identical'] for v in out['carried_forward_hash_verified'].values())
print('carried-forward probes byte-identical to prior verified copies:', carried_ok)
sys.exit(0 if (all_ok and carried_ok) else 1)
