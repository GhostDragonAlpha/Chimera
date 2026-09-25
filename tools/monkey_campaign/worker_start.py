"""Automatic worker intake and bounded task assignment; no native enrollment impersonation."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid
import os

from instruction_state import inspect
from suggestion_box import SuggestionBox, DEFAULT_ROOT
from integrity import verify_catalog
from agent_slots import Registry
from task_queue import claim_next, finish, checkpoint
from instruction_state import decode
from execution_plan import build_plan
import kanban


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
    parser.add_argument('--task',help='Choose an active Kanban task ID, including one needing corrections.')
    action=parser.add_mutually_exclusive_group()
    action.add_argument('--finish',type=Path,help='Completion arguments JSON; submit evidence and take next work.')
    action.add_argument('--checkpoint',type=Path,help='Cessation/checkpoint arguments JSON; recover next window.')
    action.add_argument('--submit-pr',type=Path,help='Record PR arguments JSON, then take next card.')
    action.add_argument('--park',type=Path,help='Preserve attempt and cease writes, then take another card.')
    args=parser.parse_args()
    if args.check and (args.finish or args.checkpoint or args.submit_pr or args.park):
        raise ValueError('check_cannot_submit_handoff')
    project=Path(__file__).resolve().parents[2]
    instructions=inspect(project)
    catalog, scope_check = verify_catalog(project/'tools/monkey_campaign/monkey_completion_map.json',
        project/'tools/monkey_campaign/APPROVED_SCOPE.json', instructions['scope_sha256'], True)
    queue = json.loads((project/'tools/monkey_campaign/EXECUTION_QUEUE.json').read_text(encoding='utf-8'))
    run=subprocess.run([sys.executable,'-B',str(project/'tools/orient.py'),'--json'],
                       cwd=project,capture_output=True,text=True,timeout=30)
    if run.returncode != 0:
        raise ValueError('orientation_failed:'+str(run.returncode)+':'+run.stderr[:1000])
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
    out['execution_plan_command']='python -B E:/PythonChimera/tools/monkey_campaign/execution_plan.py --expected-scope '+instructions['scope_sha256']
    plan=build_plan(catalog)
    out['plan']['selected_count']=plan['selected_count']
    out['plan']['coverage']=[{'id':t['id'],'selected':t['selected'],'title':t['title'],
        'depends_on':t['depends_on'], 'ontology':t.get('ontology'),
        'dependency_layer':t.get('dependency_layer')} for t in plan['tasks']]
    out['plan']['ontology_plan']=plan.get('ontology_plan')
    out['orientation_identity_note'] = 'Engine current/next terms are scene hierarchy entries, never agent or authenticated session identities.'
    if not args.check:
        identity=args.arrival_id or os.environ.get('CHIMERA_WORKER_ID')
        if (args.finish or args.checkpoint or args.submit_pr or args.park) and not identity:
            raise ValueError('existing_arrival_id_required_for_handoff')
        identity=identity or 'arrival-'+uuid.uuid4().hex
        registry=Registry(DEFAULT_ROOT)
        kanban_enabled='kanban' in registry.readonly()
        if args.finish or args.checkpoint:
            path=args.finish or args.checkpoint
            with path.open('rb') as stream: raw=stream.read(65537)
            if len(raw)>65536: raise ValueError('handoff_arguments_size_limit')
            data=decode(raw)
            if data.get('agent_id')!=identity: raise ValueError('handoff_identity_mismatch')
            out['handoff']=(finish if args.finish else checkpoint)(registry,data)
        out['arrival_id']=identity
        if kanban_enabled:
            if args.submit_pr or args.park:
                with (args.submit_pr or args.park).open('rb') as stream:raw=stream.read(65537)
                if len(raw)>65536:raise ValueError('handoff_arguments_size_limit')
                data=decode(raw)
                if data.get('agent_id')!=identity:raise ValueError('handoff_identity_mismatch')
                out['handoff']=(kanban.submit if args.submit_pr else kanban.park)(registry,data)
            target=args.task or (out.get('handoff',{}).get('task') if args.finish else None)
            allocation=kanban.join(registry,identity,target)
            out.update(assignment=allocation,task_claimed=allocation['state']=='ASSIGNED',
                next_action=allocation['next_action'],board=kanban.read(registry),
                continuation='Read task inbox before edits and each PR update. Submit a PR with --submit-pr, then take another card. No timer or exclusive task lease. Lead closes the card only after review and verified merge.')
            if 'attempt' in allocation:
                planning_ids = allocation.get('brief', {}).get('planning_ids', [])
                out['ontology_task_packets'] = [t for t in plan['tasks'] if t['id'] in planning_ids]
                out['ontology_context_note'] = 'Reconcile amended plan requirements before new acceptance. Existing card criteria hashes and historical receipts are preserved; propose any missing card scope through its inbox.'
                out['pr_submission_template']={'agent_id':identity,'task_id':allocation['task_id'],
                    'attempt_id':allocation['attempt']['id'],'criteria_sha256':allocation['attempt']['criteria_sha256'],
                    'pr_url':'https://github.com/GhostDragonAlpha/Chimera/pull/NUMBER','head_sha':'<full 40-character PR head SHA>'}
            print(json.dumps(out,indent=2));return
        if args.submit_pr or args.park:raise ValueError('kanban_not_initialized')
        allocation = claim_next(registry,queue['tasks'],identity,instructions['revision_id'],instructions['bundle_sha256'])
        out['assignment'] = allocation
        out['task_claimed'] = allocation['state'] == 'ASSIGNED'
        out['next_action'] = allocation['next_action']
        fresh=registry.snapshot()
        out['registry_snapshot_mode']=fresh['mode']
        out['registry_snapshot_time']=fresh['snapshot_at_utc']
        out['registry_revision']=fresh['revision']
        out['continuation']='Keep this arrival ID. Execute the assignment, then run --finish <handoff.json> with --arrival-id to submit and receive next work. Use --checkpoint at the hour boundary after ceasing writes. Do not end at a status report while useful work remains.'
        if 'slot' in allocation:
            slot=allocation['slot']
            out['handoff_template']={k:slot[k] for k in ('agent_id','slot','generation')}
            out['handoff_template'].update(report_path='<absolute report file in assigned output directory>',worker_finished_confirmed=True)
            if allocation.get('brief',{}).get('review_of'):
                out['handoff_template'].update(reviewed_sha256=allocation['brief']['submission']['raw_sha256'],verdict='<PASS or CHANGES_REQUIRED>')
    else:
        out['next_action']='Startup checks only; no arrival created.'
    print(json.dumps(out,indent=2))


if __name__=='__main__':
    try: main()
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({'bootstrap_failed':str(exc),'task_claimed':False}),file=sys.stderr)
        sys.exit(2)
