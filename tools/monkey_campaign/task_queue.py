"""Bounded diagnostic assignments through the existing shared slot registry."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import time
import hashlib
import json
import stat
from agent_slots import Registry, PHASES, local_time, require


def validate_brief_authority(brief,registry):
    require(brief.get('gpu_allowed') is False,'gpu_authority_not_granted')
    if brief.get('kind')=='bounded_diagnostic':
        require(brief.get('source_edit_allowed') is False,'diagnostic_authority_violation')
    else:
        require(brief.get('kind')=='bounded_implementation','unsupported_queue_task_kind')
        require(brief.get('source_edit_allowed') is True and brief.get('production_edit_allowed') is False,
                'implementation_authority_violation')
        require(Path(brief['output_directory']).absolute()==(registry.root/'task-results'/brief['id']).absolute(),
                'implementation_workspace_mismatch')
        scopes=brief.get('owned_files')
        require(isinstance(scopes,list) and scopes and all(isinstance(x,str) and x and
                not Path(x).is_absolute() and '..' not in Path(x).parts and ':' not in x for x in scopes),
                'implementation_owned_files_required')
        require(brief.get('required_artifacts') and set(brief['required_artifacts'])<=set(scopes),
                'implementation_artifacts_required')


def assigned_brief(state,slot):
    tid=slot['task_id']; review=tid.endswith('::review');key=tid[:-8] if review else tid
    record=state.get('diagnostic_claims',{}).get(key)
    require(record is not None,'not_a_queue_assignment')
    b=deepcopy(record['brief'])
    if review:
        require(record.get('reviewer')==slot['agent_id'],'wrong_review_owner')
        b.update(id=tid,review_of=key,output_directory=str(Path(b['output_directory'])/'review'),
            submission=record['submission'],objective='Independently review '+key,
            kind='bounded_diagnostic',source_edit_allowed=False,
            steps=['Read the submitted evidence and reproduce its substantive checks independently. Record PASS or CHANGES_REQUIRED with reasons.'])
    else:
        require(record['agent_id']==slot['agent_id'] and record['generation']==slot['generation'],'wrong_task_owner')
    return b


def claim_next(registry, briefs, agent_id, revision, bundle):
    """One transaction chooses both a task and a free slot. No native identity implied."""
    require(isinstance(agent_id,str) and agent_id.strip(), 'agent_id_required')
    with registry.transaction() as state:
        # The direct lead-issued queue is a bounded authorization, not a bootstrap reset.
        require(state['mode']=='ACTIVE','coordinator_reconciliation_required')
        for slot in state['slots']:
            if slot['agent_id']==agent_id:
                result={'state':'RECOVER_OWNED_ASSIGNMENT','slot':deepcopy(slot),
                        'next_action':'Read and resume this existing assignment; expired leases require recovery, not new work.'}
                key=slot['task_id'].removesuffix('::review')
                if key in state.get('diagnostic_claims',{}):result['brief']=assigned_brief(state,slot)
                return result
        queue=state.setdefault('diagnostic_claims',{})
        candidates=list(briefs)+list(state.get('commissioned_briefs',{}).values())
        reviews=[]
        for tid, record in queue.items():
            if record['state']=='REVIEW' and record['agent_id']!=agent_id:
                b=deepcopy(record['brief'])
                b.update(id=tid+'::review',review_of=tid,
                    kind='bounded_diagnostic',
                    output_directory=str(Path(b['output_directory'])/'review'),
                    objective='Independently review '+tid,
                    steps=['Read the submitted evidence and reproduce its substantive checks independently. Record PASS or CHANGES_REQUIRED with reasons.'],
                    submission=record['submission'],source_edit_allowed=False,gpu_allowed=False)
                reviews.append(b)
        ready=reviews+[deepcopy(queue[b['id']]['brief']) if b['id'] in queue else b for b in candidates if (b['id'] not in queue or queue[b['id']]['state']=='READY')
            and all(queue.get(dep,{}).get('state')=='ACCEPTED' for dep in b.get('depends_on',[]))]
        free=[s for s in state['slots'] if s['agent_id'] is None]
        if not free: return {'state':'CAPACITY_FULL','next_action':'Wait for a confirmed slot release; preserve this arrival.'}
        if not ready: return {'state':'NO_UNCLAIMED_AUTHORIZED_TASK',
            'waiting':{tid:r['state'] for tid,r in queue.items()},
            'next_action':'Read queue_control.py status. Coordinator: review results, commission the first unmet production phase from execution_plan.py through existing claims, or publish a bounded follow-up. Worker: wait for real review/completion events or continue another existing owned task. This is not goal completion.'}
        brief=ready[0]
        validate_brief_authority(brief,registry)
        slot=free[0]; generation=slot['generation']+1; stamp=registry.clock()
        deadline=int(stamp//3600)*3600+3600
        slot.update(agent_id=agent_id,task_id=brief['id'],generation=generation,phase='derive',
                    ownership_reference='Lead-authorized bounded queue; exclusive named task output workspace',
                    workspace=brief['output_directory'],checkpoint='Read the complete assigned brief before action',
                    next_action=brief['steps'][0],last_action='Atomic task+slot claim',memory={'brief':deepcopy(brief)},
                    instruction_revision=revision,instruction_bundle_sha256=bundle,last_report_utc=datetime.now(timezone.utc).isoformat(),
                    lease_state='ACTIVE',heartbeat_window_start_unix=int(stamp//3600)*3600,
                    heartbeat_window_utc=datetime.fromtimestamp(int(stamp//3600)*3600,timezone.utc).isoformat(),
                    deadline_unix=deadline,deadline_utc=datetime.fromtimestamp(deadline,timezone.utc).isoformat(),
                    deadline_local=local_time(deadline))
        key=brief.get('review_of',brief['id'])
        if 'review_of' in brief:
            queue[key]['state']='REVIEW_CLAIMED'
            queue[key]['reviewer']=agent_id
        else:
            previous=queue.get(key,{})
            queue[key]={'state':'CLAIMED','agent_id':agent_id,'slot':slot['slot'],'generation':generation,
                           'brief':deepcopy(brief),'claimed_at_utc':slot['last_report_utc']}
            if previous:
                queue[key]['attempt_history']=(previous.get('attempt_history',[])+[
                    {k:previous[k] for k in ('agent_id','checkpoint','submission','review') if k in previous}])[-10:]
        registry.event(state,'diagnostic_task_claim',{'task':brief['id'],'agent_id':agent_id,'slot':slot['slot'],'generation':generation})
        result={'state':'ASSIGNED','slot':deepcopy(slot),'brief':deepcopy(brief),
                'native_enrollment_claimed':False,
                'next_action':'Execute the brief now, including code and tests when explicitly authorized. Write only the assigned workspace/owned files. No GPU or production checkout edits; submit for independent review, then take next work.'}
    registry.snapshot()
    return result


def evidence(path, directory):
    """Hash bounded report bytes, rejecting redirects and out-of-scope references."""
    target=Path(path).absolute(); root=Path(directory).absolute()
    require('..' not in Path(path).parts and '..' not in Path(directory).parts,'evidence_path_traversal')
    require(target.is_relative_to(root),'evidence_outside_assignment')
    for part in (target,*target.parents):
        info=part.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,
                'evidence_redirect')
    require(target.is_file(),'evidence_file_required')
    with target.open('rb') as f: raw=f.read(1024*1024+1)
    require(0<len(raw)<=1024*1024,'evidence_size_limit')
    return {'path':str(target),'raw_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


def clear_slot(slot, receipt):
    number,generation=slot['slot'],slot['generation']
    handoff={k:deepcopy(v) for k,v in slot.items() if k!='last_handoff'}
    handoff['preservation_reference']=receipt
    slot.clear();slot.update(slot=number,generation=generation,agent_id=None,
                            phase='unregistered',last_handoff=handoff)


def finish(registry, a):
    """Atomically preserve an evidence handoff and release only this owned worker."""
    require(a.get('worker_finished_confirmed') is True,'worker_completion_confirmation_required')
    with registry.transaction() as state:
        slot=registry.owned(state,a)
        require(slot.get('lease_state')=='ACTIVE','assignment_expired_use_checkpoint')
        brief=assigned_brief(state,slot)
        key=brief.get('review_of',brief['id']);record=state['diagnostic_claims'][key]
        report=evidence(a['report_path'],brief['output_directory'])
        if 'review_of' in brief:
            require(record['state']=='REVIEW_CLAIMED' and record['reviewer']==a['agent_id'], 'wrong_review_owner')
            require(a.get('reviewed_sha256')==record['submission']['raw_sha256'],'stale_review')
            source=record['submission']
            require(evidence(source['path'],record['brief']['output_directory'])==
                    {k:source[k] for k in ('path','raw_sha256','bytes')},'submission_changed')
            for artifact in source.get('artifacts',[]):
                require(evidence(artifact['path'],record['brief']['output_directory'])==artifact,'implementation_artifact_changed')
            require(a.get('verdict') in ('PASS','CHANGES_REQUIRED'),'review_verdict_required')
            record['review']={'report':report,'reviewer':a['agent_id'],'verdict':a['verdict']}
            record['state']='ACCEPTED' if a['verdict']=='PASS' else 'CHANGES_REQUIRED'
        else:
            require(record['state']=='CLAIMED' and record['agent_id']==a['agent_id'],'wrong_task_owner')
            if brief['kind']=='bounded_implementation':
                report['artifacts']=[evidence(Path(brief['output_directory'])/name,brief['output_directory'])
                    for name in brief['required_artifacts']]
            record.update(state='REVIEW',submission=report)
        clear_slot(slot,report)
        registry.event(state,'queue_finish',{'task':key,'state':record['state'],'agent_id':a['agent_id']})
        result={'task':key,'state':record['state'],'planning_acceptance_claimed':False}
    registry.snapshot()
    return result


def checkpoint(registry,a):
    """Explicit cessation + durable checkpoint enables same task recovery next window."""
    require(a.get('worker_finished_confirmed') is True,'worker_completion_confirmation_required')
    with registry.transaction() as state:
        slot=registry.owned(state,a)
        brief=assigned_brief(state,slot)
        key=brief.get('review_of',brief['id']);record=state['diagnostic_claims'][key]
        report=evidence(a['report_path'],brief['output_directory'])
        record['checkpoint']=report
        record['state']='REVIEW' if 'review_of' in brief else 'READY'
        record['brief']['recovery_checkpoint']=report
        clear_slot(slot,report)
        registry.event(state,'queue_checkpoint',{'task':key,'agent_id':a['agent_id']})
    return registry.snapshot()


def publish(registry,a,catalog,builtin_ids=()):
    """Coordinator adds a bounded follow-up; never edits the sealed feature plan."""
    brief=a['brief']
    require(brief.get('id') not in builtin_ids,'builtin_task_id_reserved')
    validate_brief_authority(brief,registry)
    require(brief.get('planning_ids') and set(brief['planning_ids'])<=set(catalog),'unknown_planning_id')
    require(all(catalog[t]['scope']!='conditional' for t in brief['planning_ids']), 'conditional_requires_separate_authority')
    for key in ('id','objective','falsifier','completion'):
        require(isinstance(brief.get(key),str) and brief[key].strip(),'missing_brief_'+key)
    require(brief.get('read_first') and brief.get('steps') and brief.get('deliverables'),'incomplete_brief')
    require(len(json.dumps(brief))<=12000,'brief_size_limit')
    require(type(brief.get('max_new_output_bytes')) is int and 0<brief['max_new_output_bytes']<=16*1024*1024,'output_budget_required')
    require(brief['id'].replace('-','').replace('_','').isalnum(),'invalid_task_id')
    expected=registry.root/'task-results'/brief['id']
    require(Path(brief['output_directory']).absolute()==expected.absolute(),'output_directory_must_match_task')
    with registry.transaction() as state:
        require(a.get('coordinator_id')==state.get('coordinator_report',{}).get('coordinator_id') and a.get('coordinator_id'), 'coordinator_identity_mismatch')
        records=state.setdefault('commissioned_briefs',{})
        require(brief['id'] not in records and brief['id'] not in state.get('diagnostic_claims',{}),'task_id_already_used')
        require(len(records)<160,'commissioned_queue_capacity')
        require(all(dep in state.get('diagnostic_claims',{}) for dep in brief.get('depends_on',[])),'unknown_queue_dependency')
        records[brief['id']]=deepcopy(brief)
        registry.event(state,'queue_publish',{'task':brief['id'],'coordinator_id':a['coordinator_id']})
    return {'published':brief['id'],'planning_acceptance_claimed':False}


def rework(registry,a):
    with registry.transaction() as state:
        require(a.get('coordinator_id')==state.get('coordinator_report',{}).get('coordinator_id') and a.get('coordinator_id'), 'coordinator_identity_mismatch')
        record=state['diagnostic_claims'][a['task_id']]
        require(record['state']=='CHANGES_REQUIRED','task_not_awaiting_correction')
        require(isinstance(a.get('correction'),str) and 0<len(a['correction'])<=2000,'correction_required')
        record['brief']['correction']=a['correction']
        record['brief']['previous_submission']=record['submission']
        record['brief']['previous_review']=record['review']
        record['state']='READY'
        registry.event(state,'queue_rework',{'task':a['task_id'],'correction':a['correction']})
    return {'state':'READY','task':a['task_id']}
