"""Continuous card implementation, publication handoff and evidence review routing."""
from copy import deepcopy
from pathlib import Path
import hashlib
import uuid
from agent_slots import require

def _k():
    import kanban
    return kanban

def _artifacts(attempt, artifacts):
    require(isinstance(artifacts,list) and 0<len(artifacts)<=32,'artifacts_required')
    root=Path(attempt['workspace']).resolve()
    total=0
    for item in artifacts:
        p=Path(item['path']).resolve()
        require(p.is_relative_to(root) and p.is_file(),'artifact_outside_attempt_or_missing')
        total+=p.stat().st_size
        require(total<=16777216,'artifact_budget_exceeded')
        require(hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],'artifact_hash_mismatch')
    return deepcopy(artifacts)

def request_publication(registry,a):
    k=_k()
    require(a.get('writes_stopped') is True and a.get('checkpoint'),'checkpoint_and_stopped_writes_required')
    with registry.transaction() as state:
        c,attempt=k.owned_attempt(k.board(state),a)
        require(a.get('criteria_sha256')==c['criteria_sha256'],'criteria_changed')
        artifacts=_artifacts(attempt,a.get('artifacts'))
        request={'attempt_id':attempt['id'],'agent_id':a['agent_id'],'criteria_sha256':c['criteria_sha256'],
                 'artifacts':artifacts,'checkpoint':a['checkpoint'],'status':'PENDING'}
        requests=c.setdefault('publication_requests',[])
        existing=next((x for x in requests if x['attempt_id']==attempt['id'] and x['artifacts']==artifacts),None)
        if existing:return {'state':'PUBLICATION_ALREADY_REQUESTED','request_id':existing['id']}
        require(len(requests)<200,'publication_request_capacity')
        request['id']='publication-'+uuid.uuid4().hex
        requests.append(request)
        attempt.update(state='PUBLICATION_REQUESTED',checkpoint=a['checkpoint'])
        c['state']='PUBLICATION_PENDING'
        c['messages'].append({'id':'msg-'+uuid.uuid4().hex,'author':a['agent_id'],'status':'OPEN',
            'body':'PUBLICATION REQUEST '+request['id']+': '+a['checkpoint'],'request_id':request['id']})
        from review_lane import detach
        detach(k.board(state),c);k.refill(k.board(state))
        registry.event(state,'publication_requested',{'task':c['id'],'request':request['id']})
        return {'state':'PUBLICATION_REQUESTED','request_id':request['id'],'next_action':'Poll next slot now; lead publishes this preserved candidate.'}

def join(registry,agent_id,task_id=None):
    k=_k();require(isinstance(agent_id,str) and agent_id.strip(),'agent_id_required')
    with registry.transaction() as state:
        b=k.board(state);active=[c for c in b['cards'].values() if c['state']!='DONE']
        # Resume only work actually owned by this worker. Never expire other workers.
        working=[(c,a) for c in active for a in c['attempts'].values() if a['agent_id']==agent_id and a['state']=='WORKING']
        from review_lane import development, checkpoint_packet
        if working and b.get('separate_review_lane') and not development(working[0][0]):
            return checkpoint_packet(*working[0],agent_id)
        if task_id:
            exact=next(((c,a) for c,a in working if c['id']==task_id),None)
            if exact:return k.packet(*exact,'RESUME_ATTEMPT')
            require(not working,'checkpoint_active_work_before_switch')
        elif working:
            c,a=working[0]
            if (c.get('lane')=='REVIEW' or b.get('operational_takeover')) and any(r['status']=='PENDING' for r in c.get('publication_requests',[])):
                packet=k.packet(c,a,'CHECKPOINT_FOR_COORDINATION')
                packet['park_template']={'agent_id':agent_id,'task_id':c['id'],'attempt_id':a['id'],
                    'checkpoint':'REPLACE with exact saved work, or explicitly state no writes were made', 'writes_stopped':True}
                packet['next_action']='This card already has a publication candidate. Preserve your attempt, cease writes, fill park_template honestly, save it as JSON, and immediately run the canonical E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id '+agent_id+' --park PATH_TO_JSON. Execute the returned operational-lead or review assignment; do not wait for Astra or create another duplicate attempt.'
                return packet
            return k.packet(c,a,'RESUME_ATTEMPT')
        # Resume review work unless its head/criteria changed, in which case retain
        # the stale attempt and route a fresh review for the actual current head.
        for c in active:
            for review in c.get('worker_reviews',[]):
                if review['agent_id']==agent_id and review['state']=='WORKING':
                    pr=c['prs'].get(review['pr_url'],{})
                    if pr.get('head_sha')==review['head_sha'] and review['criteria_sha256']==c['criteria_sha256']:
                        return review_packet(c,review)
                    review['state']='STALE'
        if not task_id and not b.get('separate_review_lane'):
            from operational_lead import assign
            coordination=assign(registry,state,agent_id)
            if coordination:return coordination
        candidates=[]
        for c in active:
            from review_lane import development
            if not development(c):continue
            if task_id and c['id']!=task_id:continue
            correction=c['state']=='CHANGES_REQUESTED'
            if correction and b.get('separate_review_lane'):
                from review_lane import pending_review_prs
                if pending_review_prs(c):continue
            if c['prs'] and not correction:continue
            if any(x['status']=='PENDING' for x in c.get('publication_requests',[])):continue
            own=[a for a in c['attempts'].values() if a['agent_id']==agent_id]
            if any(a['state'] in ('PR_SUBMITTED','PUBLICATION_REQUESTED') for a in own) and not correction:continue
            candidates.append(c)
        if candidates:
            candidates.sort(key=lambda c:(sum(a['state']=='WORKING' for a in c['attempts'].values()),c['state']!='CHANGES_REQUESTED',c['slot']))
            c=candidates[0]
            require(len(c['attempts'])<200,'attempt_history_capacity_requires_preservation')
            ident=uuid.uuid4().hex
            a={'id':ident,'agent_id':agent_id,'state':'WORKING','criteria_sha256':c['criteria_sha256'],
               'workspace':str(registry.root/'kanban-attempts'/c['id']/ident),'branch':'branch-'+str(c['slot'])}
            c['attempts'][ident]=a
            registry.event(state,'cycle_implementation',{'task':c['id'],'attempt':ident})
            return k.packet(c,a,'ASSIGNED')
        if not task_id and b.get('separate_review_lane'):
            from operational_lead import assign
            coordination=assign(registry,state,agent_id)
            if coordination:return coordination
        for c in sorted(active,key=lambda c:c['slot']):
            from review_lane import pending_review_prs
            review_items=pending_review_prs(c) if b.get('separate_review_lane') else list(c['prs'].items())
            for url,pr in review_items:
                author=c['attempts'][pr['attempt_id']]['agent_id']
                if author==agent_id:continue
                history=c.setdefault('worker_reviews',[])
                if any(x['agent_id']==agent_id and x['pr_url']==url and x['head_sha']==pr['head_sha'] and x['state'] in ('WORKING','COMPLETE') for x in history):continue
                if (pr.get('review') or {}).get('verdict')=='ACCEPTED':continue
                require(len(history)<200,'review_history_capacity')
                ident=uuid.uuid4().hex
                review={'id':ident,'agent_id':agent_id,'state':'WORKING','pr_url':url,'head_sha':pr['head_sha'],
                        'criteria_sha256':c['criteria_sha256'],'workspace':str(registry.root/'kanban-reviews'/c['id']/ident)}
                history.append(review)
                registry.event(state,'cycle_review',{'task':c['id'],'review':ident})
                return review_packet(c,review)
        return {'state':'AWAITING_LEAD_ACTION','all_ten_have_prs':len(active)==10 and all(c['prs'] for c in active),
                'next_action':'No eligible implementation or independent review remains for this identity. Report pending publication/merge or author-only reviews to the lead. Preserve evidence; do not fabricate work, self-approve or busy-poll.'}

def review_packet(c,r):
    return {'state':'REVIEW_ASSIGNED','task_id':c['id'],'card_slot':c['slot'],'review':deepcopy(r),
            'brief':deepcopy(c['spec']),'task_inbox':deepcopy(c['messages']),
            'next_action':'Read task inbox and ontology packet. Review the exact PR head against criteria, rerun relevant numerical/runtime/visual checks within existing budgets, and write hash-bound evidence in your review workspace. Submit --review-result then continue. PASS is a recommendation; only lead approval and verified GitHub merge clear the slot.'}

def submit_review(registry,a):
    k=_k();require(a.get('verdict') in ('PASS','CHANGES_REQUIRED'),'invalid_worker_verdict')
    require(a.get('writes_stopped') is True and a.get('body'),'review_evidence_required')
    with registry.transaction() as state:
        c=k.board(state)['cards'][a['task_id']]
        r=next(x for x in c.get('worker_reviews',[]) if x['id']==a['review_id'])
        require(r['agent_id']==a['agent_id'],'wrong_reviewer')
        pr=c['prs'][r['pr_url']]
        require(c['state']!='DONE' and r['head_sha']==a.get('head_sha')==pr['head_sha'] and r['criteria_sha256']==a.get('criteria_sha256')==c['criteria_sha256'],'review_head_or_criteria_changed')
        require(c['attempts'][pr['attempt_id']]['agent_id']!=a['agent_id'],'author_cannot_independently_review')
        artifacts=_artifacts(r,a.get('artifacts'))
        if r['state']=='COMPLETE':
            require(r['verdict']==a['verdict'] and r['artifacts']==artifacts and r['body']==a['body'],'review_already_completed')
            return {'state':'REVIEW_ALREADY_RECORDED'}
        require(r['state']=='WORKING','review_not_active')
        r.update(state='COMPLETE',verdict=a['verdict'],artifacts=artifacts,body=a['body'])
        c['messages'].append({'id':'msg-'+uuid.uuid4().hex,'author':a['agent_id'],'status':'OPEN',
            'body':'WORKER REVIEW '+a['verdict']+': '+a['body'],'pr_url':r['pr_url'],'head_sha':r['head_sha'],'review_id':r['id']})
        if a['verdict']=='CHANGES_REQUIRED':
            c['state']='CHANGES_REQUESTED'
            from review_lane import corrections
            corrections(k.board(state),c);k.refill(k.board(state))
        registry.event(state,'cycle_review_result',{'task':c['id'],'verdict':a['verdict']})
        return {'state':'REVIEW_RECORDED','next_action':'Poll next slot; this evidence does not approve or merge the PR.'}
