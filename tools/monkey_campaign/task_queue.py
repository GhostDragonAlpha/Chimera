"""Bounded diagnostic assignments through the existing shared slot registry."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import time
from agent_slots import Registry, PHASES, local_time, require


def claim_next(registry, briefs, agent_id, revision, bundle):
    """One transaction chooses both a task and a free slot. No native identity implied."""
    require(isinstance(agent_id,str) and agent_id.strip(), 'agent_id_required')
    with registry.transaction() as state:
        # The direct lead-issued queue is a bounded authorization, not a bootstrap reset.
        require(state['mode']=='ACTIVE','coordinator_reconciliation_required')
        for slot in state['slots']:
            if slot['agent_id']==agent_id:
                return {'state':'RECOVER_OWNED_ASSIGNMENT','slot':deepcopy(slot),
                        'next_action':'Read and resume this existing assignment; expired leases require recovery, not new work.'}
        queue=state.setdefault('diagnostic_claims',{})
        ready=[b for b in briefs if b['id'] not in queue]
        free=[s for s in state['slots'] if s['agent_id'] is None]
        if not ready: return {'state':'NO_UNCLAIMED_AUTHORIZED_TASK','next_action':'Coordinator must review current results and publish the next scoped brief. Continue an existing owned task; do not invent work.'}
        if not free: return {'state':'CAPACITY_FULL','next_action':'Wait for a confirmed slot release; preserve this arrival.'}
        brief=ready[0]
        require(brief['kind']=='bounded_diagnostic','unsupported_queue_task_kind')
        require(brief['source_edit_allowed'] is False and brief['gpu_allowed'] is False,'diagnostic_authority_violation')
        slot=free[0]; generation=slot['generation']+1; stamp=registry.clock()
        deadline=int(stamp//3600)*3600+3600
        slot.update(agent_id=agent_id,task_id=brief['id'],generation=generation,phase='derive',
                    ownership_reference='Lead-authored EXECUTION_QUEUE.json; transactional diagnostic claim',
                    workspace=brief['output_directory'],checkpoint='Read the complete assigned brief before action',
                    next_action=brief['steps'][0],last_action='Atomic task+slot claim',memory={'brief':deepcopy(brief)},
                    instruction_revision=revision,instruction_bundle_sha256=bundle,last_report_utc=datetime.now(timezone.utc).isoformat(),
                    lease_state='ACTIVE',heartbeat_window_start_unix=int(stamp//3600)*3600,
                    heartbeat_window_utc=datetime.fromtimestamp(int(stamp//3600)*3600,timezone.utc).isoformat(),
                    deadline_unix=deadline,deadline_utc=datetime.fromtimestamp(deadline,timezone.utc).isoformat(),
                    deadline_local=local_time(deadline))
        queue[brief['id']]={'state':'CLAIMED','agent_id':agent_id,'slot':slot['slot'],'generation':generation,
                           'brief':deepcopy(brief),'claimed_at_utc':slot['last_report_utc']}
        registry.event(state,'diagnostic_task_claim',{'task':brief['id'],'agent_id':agent_id,'slot':slot['slot'],'generation':generation})
        result={'state':'ASSIGNED','slot':deepcopy(slot),'brief':deepcopy(brief),
                'native_enrollment_claimed':False,
                'next_action':'Execute the brief now. Read-only sources; write only assigned report outputs. No GPU or production source edits.'}
    registry.snapshot()
    return result
