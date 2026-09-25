"""Automatic worker intake and bounded task assignment; no native enrollment impersonation."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid

from instruction_state import inspect
from suggestion_box import SuggestionBox, DEFAULT_ROOT
from integrity import verify_catalog
from agent_slots import Registry
from task_queue import claim_next


def intake(box, instructions, identity, workspace, orientation):
    return box.submit({
        'agent_id':identity,'task_id':'UNASSIGNED:BOOTSTRAP',
        'subject':'ARRIVAL: worker requests next eligible playable task',
        'question':'Startup records this arrival and attempts a lead-authorized bounded queue claim. Inspect its returned assignment before dispatching additional work. This arrival alone is not a claim.',
        'evidence_reference':str(workspace),
        'attempts':'Automatic startup verified instruction bundle; orientation exit='+str(orientation),
        'recommendation':'Coordinator: match this arrival to the real harness session, inspect capabilities and recover existing ownership before assigning work.',
        'instruction_revision':instructions['revision_id'],'blocking':True})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arrival-id',help='Reuse the arrival identity printed on the first run.')
    parser.add_argument('--check',action='store_true',help='Verify startup without registering an arrival.')
    args=parser.parse_args()
    project=Path(__file__).resolve().parents[2]
    instructions=inspect(project)
    catalog, scope_check = verify_catalog(project/'tools/monkey_campaign/monkey_completion_map.json',
        project/'tools/monkey_campaign/APPROVED_SCOPE.json', instructions['scope_sha256'], True)
    queue = json.loads((project/'tools/monkey_campaign/EXECUTION_QUEUE.json').read_text(encoding='utf-8'))
    run=subprocess.run([sys.executable,'-B',str(project/'tools/orient.py'),'--json'],
                       cwd=project,capture_output=True,text=True,timeout=30)
    box=SuggestionBox(DEFAULT_ROOT)
    # Require the installed store; never silently initialize a replacement authority.
    mailbox=box.listing(pending=True)
    state_path=DEFAULT_ROOT/'STATUS.json'
    slots=json.loads(state_path.read_text(encoding='utf-8'))
    out={'instruction_revision':instructions['revision_id'],
         'bundle_sha256':instructions['bundle_sha256'],
         'orientation_exit':run.returncode,'orientation':run.stdout[:12000],
         'orientation_error':run.stderr[:2000],
         'registry_snapshot_mode':slots['mode'],'registry_snapshot_time':slots.get('snapshot_at_utc'),
         'pending_questions':len(mailbox['questions']),
         'native_enrollment_claimed':False,'task_claimed':False}
    out['plan'] = {'goal':queue['goal'], 'approved_task_count':len(catalog['tasks']),
                   'scope_integrity':scope_check, 'next_bounded_tasks':queue['tasks']}
    out['orientation_identity_note'] = 'Engine current/next terms are scene hierarchy entries, never agent or authenticated session identities.'
    if not args.check:
        identity=args.arrival_id or 'arrival-'+uuid.uuid4().hex
        result=intake(box,instructions,identity,Path.cwd(),run.returncode)
        out.update(arrival_id=identity,**result)
        allocation = claim_next(Registry(DEFAULT_ROOT),queue['tasks'],identity,instructions['revision_id'],instructions['bundle_sha256'])
        out['assignment'] = allocation
        out['task_claimed'] = allocation['state'] == 'ASSIGNED'
        out['next_action'] = allocation['next_action']
    else:
        out['next_action']='Startup checks only; no arrival created.'
    print(json.dumps(out,indent=2))


if __name__=='__main__':
    try: main()
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({'bootstrap_failed':str(exc),'task_claimed':False}),file=sys.stderr)
        sys.exit(2)
