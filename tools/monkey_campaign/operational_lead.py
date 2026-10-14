"""Serialized operational coordination without inheriting architectural authority."""
from copy import deepcopy
import uuid
import hashlib,json

def queue_signature(work):
    rows=[{'task':r['task_id'],'requests':[(x['id'],x['status']) for x in r['requests']],
           'prs':[(url,p['head_sha'],(p.get('review') or {}).get('verdict')) for url,p in sorted(r['prs'].items())],
           'reviews':[(x.get('id'),x['state'],x.get('verdict'),x['head_sha']) for x in r['worker_reviews']]} for r in work]
    return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
from agent_slots import require

def pending(b):
    return [dict(task_id=c['id'],slot=c['slot'],publication_branch=c.get('publication_branch'),
                 criteria_sha256=c['criteria_sha256'],requests=deepcopy([x for x in c.get('publication_requests',[]) if x['status']=='PENDING']),
                 prs=deepcopy(c['prs']),attempts=deepcopy(c['attempts']),messages=deepcopy(c['messages']),worker_reviews=deepcopy(c.get('worker_reviews',[])))
            for c in sorted(b['cards'].values(),key=lambda c:c['slot']) if c['state']!='DONE' and
            (any(x['status']=='PENDING' for x in c.get('publication_requests',[])) or c['prs'])]

def assign(registry,state,agent):
    b=state['kanban']
    if not b.get('operational_takeover'):return None
    work=pending(b)
    from merge_service import coordination_actionable
    connected_only=b.get('merge_service',{}).get('mode')=='CONNECTED_LEAD_SESSION'
    actionable=any(coordination_actionable(row,connected_only) for row in work)
    if not actionable:return None
    deferred=b.get('coordination_deferrals',{}).get(agent)
    if deferred and deferred['queue_sha256']==queue_signature(work):return None
    current=b.get('operational_lead')
    if current and current['agent_id']!=agent:return None
    if not current:
        current={'agent_id':agent,'token':uuid.uuid4().hex,'role':'OPERATIONAL_LEAD'}
        b['operational_lead']=current
        registry.event(state,'operational_lead_acquired',{'agent_id':agent})
    return dict(state='OPERATIONAL_LEAD_ASSIGNED',operational_lead=deepcopy(current),queue=work,
        next_action='You are handling the Review queue, not taking architectural leadership. Read E:/PythonChimera/tools/monkey_campaign/OPERATIONAL_LEAD.md and execute publication and independent review; follow MERGE_SERVICE.md for connected-lead-only ready/merge execution. Use your own arrival identity and role token; never impersonate Astra. Architectural/scientific changes remain in the suggestion box. Release the role with a durable checkpoint before stopping or returning to worker work.')

def authority(state,a,c=None,approval=False):
    if a.get('actor')=='astra-codex':return
    role=state['kanban'].get('operational_lead') or {}
    require(role.get('agent_id')==a.get('actor') and role.get('token')==a.get('role_token') and bool(role.get('token')), 'operational_lead_required')
    if approval:
        pr=c['prs'][a['pr_url']];author=c['attempts'][pr['attempt_id']]['agent_id']
        reviews=[r for r in c.get('worker_reviews',[]) if r['state']=='COMPLETE' and r['head_sha']==a['head_sha'] and r['criteria_sha256']==c['criteria_sha256'] and r['pr_url']==a['pr_url']]
        require(not any(r['verdict']=='CHANGES_REQUIRED' for r in reviews),'independent_changes_unresolved')
        require(any(r['verdict']=='PASS' and r['agent_id']!=author for r in reviews),'separate_independent_review_required')

def release(registry,a):
    require(a.get('checkpoint') and a.get('writes_stopped') is True,'checkpoint_and_stopped_writes_required')
    with registry.transaction() as state:
        authority(state,a);b=state['kanban']
        b.setdefault('operational_history',[]).append(dict(role=deepcopy(b.get('operational_lead')),checkpoint=a['checkpoint']))
        if a.get('defer_unchanged_queue'):
            require(a.get('blocker_reason'), 'external_blocker_reason_required')
            b.setdefault('coordination_deferrals',{})[a['actor']]={'queue_sha256':queue_signature(pending(b)),'reason':a['blocker_reason'],'checkpoint':a['checkpoint']}
        b['operational_lead']=None
        registry.event(state,'operational_lead_released',{'actor':a['actor']})
    return {'state':'OPERATIONAL_LEAD_RELEASED'}

def record_pr(registry,a,github):
    # Publication records the original author as provenance. The executing actor
    # is the coordinator and is separately recorded; no worker identity is assumed.
    import kanban as k
    require(github.get('html_url')==a['pr_url'] and github.get('head',{}).get('sha')==a['head_sha'] and github.get('base',{}).get('ref')==k.BASE and github.get('state')=='open','publication_github_mismatch')
    with registry.transaction() as state:
        authority(state,a)
        c=state['kanban']['cards'][a['task_id']]
        require(github['head'].get('ref')==c.get('publication_branch'),'publication_wrong_slot_branch')
        req=next((r for r in c.get('publication_requests',[]) if r['id']==a['request_id']),None)
        require(req is not None and req['status'] in ('PENDING','PR_RECORDED'),'publication_request_missing')
        require(c['state']!='DONE' and a['criteria_sha256']==c['criteria_sha256']==req['criteria_sha256'],'criteria_changed')
        k.pr_identity(a['pr_url'],a['head_sha'])
        previous=c['prs'].get(a['pr_url'])
        if previous and previous['head_sha']==a['head_sha'] and previous['attempt_id']==req['attempt_id']:
            return {'state':'PR_ALREADY_RECORDED'}
        for other in state['kanban']['cards'].values():
            if a['pr_url'] in other['prs']:
                require(other['id']==c['id'] and other['prs'][a['pr_url']]['attempt_id']==req['attempt_id'],'pr_already_bound')
        c.setdefault('submission_history',[]).append({'pr_url':a['pr_url'],'head_sha':a['head_sha'],'attempt_id':req['attempt_id'],'supersedes_head':previous['head_sha'] if previous else None,'published_by':a['actor']})
        c['prs'][a['pr_url']]={'attempt_id':req['attempt_id'],'head_sha':a['head_sha'],'criteria_sha256':c['criteria_sha256'],'review':None,'published_by':a['actor']}
        c['attempts'][req['attempt_id']]['state']='PR_SUBMITTED'
        req.update(status='PR_RECORDED',pr_url=a['pr_url'],head_sha=a['head_sha'],published_by=a['actor'])
        c['state']='REVIEW'
        from review_lane import detach
        detach(state['kanban'],c);k.refill(state['kanban'])
        registry.event(state,'operational_pr_recorded',{'task':c['id'],'pr':a['pr_url'],'actor':a['actor']})
    return {'state':'PR_RECORDED'}
