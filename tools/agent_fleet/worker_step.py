"""worker_step.py -- the worker-side step runner of the universal entry point.

Executes one agent's bounded plan through its OWN private session file (the
same loop AGENT_START.md describes: orient -> claim -> context -> checkpoint).
This process IS the owned worker client: the SLOT01-E2E interruption drill
terminates it exactly as a lost session would be lost, and the controller's
fencing (revoked session + bumped generation) does the rest.

Plan file: JSON {"steps":[["claim",{"task":...}],["checkpoint",{...}],...,
["wait",{"stop_file":...,"poll":0.5}]]}
Supported steps: claim, checkpoint, resource_acquire, wait, release.
Credentials are never printed or logged. All calls go through client.call.
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from client import call  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--session', type=Path, required=True)
    ap.add_argument('--plan', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True,
                    help='step journal (JSON lines), one object per step')
    a = ap.parse_args()
    session = json.loads(a.session.read_text(encoding='utf-8'))
    plan = json.loads(a.plan.read_text(encoding='utf-8'))['steps']
    journal = a.out.open('w', encoding='utf-8')

    def emit(step, **data):
        journal.write(json.dumps({'step': step, 't': time.time(), **data}) + '\n')
        journal.flush()

    emit('start', pid=None, plan_steps=len(plan))
    try:
        for i, (op, args) in enumerate(plan):
            if op == 'wait':
                stop = Path(args['stop_file'])
                poll = float(args.get('poll', 0.5))
                emit('waiting', stop_file=str(stop))
                while not stop.exists():
                    time.sleep(poll)
                emit('stop_file_seen')
                continue
            if op == 'release':
                # cleanup step for graceful exits (not used by the drill)
                r = call(session, 'resource_release', **args)
                emit('released', revision=r.get('revision'))
                continue
            r = call(session, op, **args)
            emit(op, revision=r.get('revision'), result=r.get('result'))
        emit('plan_complete')
        return 0
    except Exception as e:  # noqa: BLE001 - the journal is the evidence
        emit('failed', error=repr(e))
        return 1
    finally:
        journal.close()


if __name__ == '__main__':
    sys.exit(main())
