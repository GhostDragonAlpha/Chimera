"""Trusted, offline checklist runner. Never give its session to model workers.

Runs approved graph argv without a shell. Does not allocate engine resources;
the existing resource controller remains authoritative for runtime checks.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from client import call
from graph_workflow import candidate, file_hash, local_file, require


def execute(context, repo, output):
    root, output = Path(repo).resolve(), Path(output).resolve()
    require(root == Path(context['worktree']).resolve(), 'workflow_foreign_worktree')
    output.mkdir(parents=True, exist_ok=False)
    pins = context['contract']['verifier_inputs']
    require(pins == {name: file_hash(local_file(root, name)) for name in pins},
            'workflow_verifier_changed')
    before = candidate(root)
    checks = []
    for index, spec in enumerate(context['contract']['checks']):
        log = output / f'{index:03d}.log'
        start = time.time()
        # Never inherit broker credentials into the program being tested.
        env = {k: v for k, v in os.environ.items()
               if not any(word in k.upper() for word in ('TOKEN', 'SECRET', 'PASSWORD', 'API_KEY'))}
        with log.open('wb') as stream:
            try:
                result = subprocess.run(spec['argv'], cwd=root, env=env, stdout=stream,
                                        stderr=subprocess.STDOUT, timeout=spec['timeout_s'])
                code = result.returncode
            except subprocess.TimeoutExpired:
                stream.write(b'\nWORKFLOW_TIMEOUT\n')
                code = 124
            except OSError as error:
                stream.write(('\nWORKFLOW_LAUNCH_FAILED: ' + str(error)).encode())
                code = 127
        checks.append({'id': spec['id'], 'argv': spec['argv'], 'exit_code': code,
                       'log': str(log), 'log_sha256': file_hash(log),
                       'started_unix': start, 'finished_unix': time.time()})
    after = candidate(root)
    require(before == after, 'workflow_source_changed_during_checks')
    receipt = {'generation': context['generation'], 'input_hash': context['input_hash'],
               'candidate': before, 'verifier_inputs': pins, 'checks': checks}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    session = json.loads(args.session.read_bytes())
    context = call(session, 'workflow_context', {'task': args.task})['result']
    auxiliary = call(session, 'workflow_verifier_context', {'task': args.task})['result']
    receipt = execute(context, context['worktree'], args.out)
    from auxiliary_graph import run
    receipt['independent'] = run(auxiliary, context['worktree'], args.out/'internal')
    require(candidate(context['worktree']) == receipt['candidate'], 'workflow_source_changed_during_checks')
    (args.out/'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    result = call(session, 'workflow_attest', {'task': args.task, 'receipt': receipt})
    print(json.dumps(result, indent=2))
    return 0 if all(c['exit_code'] == 0 for c in receipt['checks'] + (receipt.get('independent') or {}).get('logs', [])) else 1


if __name__ == '__main__':
    raise SystemExit(main())
