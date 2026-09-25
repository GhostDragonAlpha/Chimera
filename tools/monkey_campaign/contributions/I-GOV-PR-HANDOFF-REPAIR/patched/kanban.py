"""Ten task cards, competing PR attempts, and persistent task-addressed feedback."""
from copy import deepcopy
import hashlib
import json
import re
import uuid
from agent_slots import require

LEAD='astra-codex'
REPO='GhostDragonAlpha/Chimera'
BASE='astra/gait-capture'

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def lead(a):
    require(a.get('actor')==LEAD,'lead_action_required')

def board(state):
    require('kanban' in state,'kanban_not_initialized')
    return state['kanban']

def refill(b):
    for spec in b['backlog']:
        tid=spec['id']
        if tid in b['cards']:continue
        free=next((i for i in range(1,11) if i not in {c['slot'] for c in b['cards'].values() if c['state']!='DONE'}),None)
        if free is None:break
        if not all(b['cards'].get(d,{}).get('state')=='DONE' for d in spec.get('depends_on',[])):continue
        b['cards'][tid]={'id':tid,'slot':free,'state':'OPEN','spec':deepcopy(spec),
            'criteria_sha256':digest(spec),'attempts':{},'prs':{},'messages':[], 'winner':None}

def validate_specs(specs):
    require(isinstance(specs,list) and len(specs)<=200,'invalid_card_backlog')
    ids=set()
    for s in specs:
        require(re.fullmatch(r'[A-Za-z0-9_-]+',s.get('id','')) is not None,'invalid_card_id')
        require(s['id'] not in ids,'duplicate_card_id');ids.add(s['id'])
        require(s.get('objective') and s.get('falsifier') and s.get('steps') and s.get('completion'),'incomplete_card')
    by={s['id']:s for s in specs};visiting=set();seen=set()
    def visit(tid):
        require(tid in by,'unknown_card_dependency');require(tid not in visiting,'card_dependency_cycle')
        if tid in seen:return
        visiting.add(tid)
        for dep in by[tid].get('depends_on',[]):visit(dep)
        visiting.remove(tid);seen.add(tid)
    for tid in by:visit(tid)

def initialize(registry,specs,actor,workers_stopped=False):
    lead({'actor':actor});validate_specs(specs)
    with registry.transaction() as state:
        if 'kanban' in state:return summary(state['kanban'])
        active={s['task_id'].removesuffix('::review') for s in state['slots'] if s['agent_id']}
        require(active<={s['id'] for s in specs},'legacy_tasks_missing_from_board')
        require(len(active)<=10,'legacy_tasks_exceed_ten_preserve_before_migration')
        ordered=sorted(specs,key=lambda s:0 if s['id'] in active else 1)
        b={'schema':'chimera.kanban.v1','backlog':deepcopy(ordered),'cards':{},'policy':'TEN_TASKS_FIRST_QUALIFYING_MERGED_PR_NO_TIMERS'}
        refill(b)
        require(active<={k for k,c in b['cards'].items() if c['state']!='DONE'},'legacy_dependency_prevents_migration')
        state['kanban']=b
        for slot in state['slots']:
            if slot['agent_id']:
                tid=slot['task_id'].removesuffix('::review')
                b['cards'][tid].setdefault('legacy_work',[]).append({k:deepcopy(slot.get(k))
                    for k in ('agent_id','workspace','ownership_reference','checkpoint','evidence_reference')})
                slot['legacy_lease_state']=slot.get('lease_state')
                slot['lease_state']='ACTIVE'
                slot['timer_policy']='REMOVED_BY_OPERATOR; legacy ownership preserved'
                if workers_stopped:
                    handoff=deepcopy(slot);number,generation=slot['slot'],slot['generation']
                    handoff['operator_stop_reference']='Operator confirmed all agents stopped before Kanban migration'
                    slot.clear();slot.update(slot=number,generation=generation,agent_id=None,
                        phase='unregistered',last_handoff=handoff)
        if workers_stopped:
            for record in state.get('diagnostic_claims',{}).values():
                if record.get('state') in ('CLAIMED','REVIEW_CLAIMED'):
                    record['pre_stop_state']=record['state'];record['state']='PAUSED_BY_OPERATOR'
        state['heartbeat_policy']='NO_TIMERS; ten active task cards; reviewed and verified merged PR closes card'
        registry.event(state,'kanban_enabled',{'cards':len(b['cards']),'legacy_tasks':sorted(active)})
        result=summary(b)
    registry.snapshot();return result

def summary(b):
    return {'schema':b['schema'],'policy':b['policy'],'capacity':10,
        'cards':[{'id':c['id'],'slot':c['slot'],'state':c['state'],
            'objective':c['spec']['objective'],'attempt_count':len(c['attempts']),
            'open_messages':sum(m['status']=='OPEN' for m in c['messages']),
            'prs':list(c['prs']), 'winner':c['winner']} for c in b['cards'].values()],
        'backlog_count':sum(s['id'] not in b['cards'] for s in b['backlog']),
        'active_count':sum(c['state']!='DONE' for c in b['cards'].values()),'goal_complete':False}

def read(registry,task_id=None):
    b=board(registry.readonly())
    return deepcopy(b['cards'][task_id]) if task_id else summary(b)

def displace_working(b,agent_id,keep_task):
    """Checkpoint-park the SAME worker's other WORKING attempts when they
    explicitly select another task. Only own attempts transition; another
    worker's attempts are never touched."""
    for card in b['cards'].values():
        for attempt in card['attempts'].values():
            if (attempt['agent_id']==agent_id and attempt['state']=='WORKING'
                    and card['id']!=keep_task):
                attempt['state']='PAUSED'
                attempt['checkpoint']=('auto_displaced_by_explicit_task_selection:'
                                       +keep_task+'; workspace preserved')

def join(registry,agent_id,task_id=None):
    require(isinstance(agent_id,str) and 0<len(agent_id)<=200,'agent_id_required')
    with registry.transaction() as state:
        b=board(state)
        # An explicit task is an intentional selection: revisit an own attempt or
        # switch cards. It must resolve to the requested card, never another one.
        if task_id and task_id in b['cards']:
            c=b['cards'][task_id]
            for attempt in c['attempts'].values():
                if (c['state']!='DONE' and attempt['agent_id']==agent_id
                        and attempt['state'] in ('WORKING','PAUSED','PR_SUBMITTED',
                                                 'PUBLICATION_REQUESTED')):
                    # Resuming this card parks the worker's other WORKING attempts.
                    attempt['state']='WORKING'
                    displace_working(b,agent_id,task_id)
                    return packet(c,attempt,'RESUME_ATTEMPT')
        elif task_id is None:
            # Generic poll resumes the worker's single WORKING attempt, if any.
            for c in b['cards'].values():
                for a in c['attempts'].values():
                    if a['agent_id']==agent_id and a['state']=='WORKING':
                        return packet(c,a,'RESUME_ATTEMPT' if c['state']!='DONE' else 'TASK_ALREADY_WON')
        # Submitted and publication-requesting workers move to another card. Lead
        # feedback only prioritizes a card; it cannot override the submitted/requested
        # exclusion and spawn duplicates.
        candidates=[c for c in b['cards'].values() if c['state']!='DONE'
            and (task_id is None or c['id']==task_id)
            and (task_id is not None or not any(
                a['agent_id']==agent_id and a['state'] in ('PR_SUBMITTED','PUBLICATION_REQUESTED')
                for a in c['attempts'].values()))]
        if not candidates:return {'state':'NO_ELIGIBLE_CARD','next_action':'Read board and task inboxes; lead refills eligible cards after merge. Do not invent completion.'}
        candidates.sort(key=lambda c:(sum(a['state']=='WORKING' for a in c['attempts'].values()),
                                     -sum(m['status']=='OPEN' and m['author']==LEAD for m in c['messages']),c['slot']))
        c=candidates[0]
        require(len(c['attempts'])<200,'attempt_history_capacity_requires_preservation')
        # Assigning a new attempt checkpoint-parks the worker's own remaining WORKING
        # attempt (explicit card switch); a no-op when none exists.
        displace_working(b,agent_id,c['id'])
        attempt=uuid.uuid4().hex
        a={'id':attempt,'agent_id':agent_id,'state':'WORKING','criteria_sha256':c['criteria_sha256'],
           'workspace':str(registry.root/'kanban-attempts'/c['id']/attempt),
           'branch':'codex/monkey-'+c['id'].lower()+'-'+attempt[:10]}
        c['attempts'][attempt]=a
        registry.event(state,'kanban_join',{'task':c['id'],'attempt':attempt,'agent':agent_id})
        return packet(c,a,'ASSIGNED')

def packet(c,a,status):
    spec=deepcopy(c['spec']);spec['output_directory']=a['workspace']
    return {'state':status,'task_id':c['id'],'card_slot':c['slot'],'attempt':deepcopy(a),'brief':spec,
        'task_inbox':deepcopy(c['messages']),'legacy_work':deepcopy(c.get('legacy_work',[])),'winner':c['winner'],
        'pr_repository':REPO,'pr_base':BASE,
        'next_action':'Read task inbox first. Work only in this attempt workspace/branch. Submit a PR with task ID, attempt ID and criteria hash. A report alone does not close the card; read KANBAN.md for commands.'}

def owned_attempt(b,a):
    c=b['cards'][a['task_id']];attempt=c['attempts'][a['attempt_id']]
    require(attempt['agent_id']==a['agent_id'],'wrong_attempt_owner')
    require(c['state']!='DONE','task_already_completed')
    return c,attempt

def pr_identity(url,head):
    require(re.fullmatch(r'https://github\.com/GhostDragonAlpha/Chimera/pull/[1-9][0-9]*',url or '') is not None,'invalid_project_pr')
    require(re.fullmatch('[0-9a-f]{40}',head or '') is not None,'full_pr_head_required')

def _record_pr(b,c,attempt,pr_url,head_sha,source):
    """Shared PR recording core for worker submission and lead fulfilment."""
    for other in b['cards'].values():
        if pr_url in other['prs']:
            require(other['id']==c['id'] and other['prs'][pr_url]['attempt_id']==attempt['id'],'pr_already_bound')
    previous=c['prs'].get(pr_url)
    if previous and previous['head_sha']==head_sha and previous.get('source')==source:
        return False
    require(len(c['prs'])<200 or previous,'pr_history_capacity')
    history=c.setdefault('submission_history',[]);require(len(history)<500,'submission_history_capacity')
    history.append({'pr_url':pr_url,'head_sha':head_sha,'attempt_id':attempt['id'],
                    'source':source,'supersedes_head':previous['head_sha'] if previous else None})
    c['prs'][pr_url]={'attempt_id':attempt['id'],'head_sha':head_sha,
        'criteria_sha256':c['criteria_sha256'],'review':None,'source':source}
    attempt['state']='PR_SUBMITTED';c['state']='REVIEW'
    return True

def submit(registry,a):
    pr_identity(a['pr_url'],a['head_sha'])
    with registry.transaction() as state:
        b=board(state);c,attempt=owned_attempt(b,a)
        require(a['criteria_sha256']==c['criteria_sha256'],'criteria_changed')
        # One PR belongs to one card/attempt; updates invalidate approval automatically.
        if not _record_pr(b,c,attempt,a['pr_url'],a['head_sha'],'worker_submit'):
            return {'state':'PR_ALREADY_RECORDED'}
        registry.event(state,'kanban_pr',{'task':c['id'],'pr':a['pr_url'],'head':a['head_sha']})
        return {'state':'PR_RECORDED','next_action':'Take another card or address task inbox feedback; this card remains open until lead-approved merge.'}

def request_publication(registry,a):
    """Durable PR-request handoff: the worker asks the lead to publish a preserved
    candidate. A request is evidence-preserving handoff only - never a PR submission,
    never a review, never a merge. Requires no GitHub/REST credentials."""
    require(re.fullmatch('[0-9a-f]{40}',a.get('head_sha') or '') is not None,'full_request_head_required')
    require(a.get('checkpoint') and a.get('writes_stopped') is True,
            'request_checkpoint_and_stopped_writes_required')
    require(isinstance(a.get('artifacts'),list) and len(a['artifacts'])<=200,
            'request_artifacts_required')
    with registry.transaction() as state:
        b=board(state);c,attempt=owned_attempt(b,a)
        require(a['criteria_sha256']==c['criteria_sha256'],'criteria_changed')
        require(attempt['state'] in ('WORKING','PAUSED','PUBLICATION_REQUESTED'),
                'attempt_state_cannot_request')
        requests=c.setdefault('publication_requests',{})
        require(len(requests)<200,'request_history_capacity')
        identity=digest({'task_id':c['id'],'attempt_id':attempt['id'],
                         'agent_id':a['agent_id'],'head_sha':a['head_sha'],
                         'branch':a.get('branch')})
        request_id='pub-'+identity[:16]
        existing=requests.get(request_id)
        if existing and existing['status']=='OPEN':
            return {'state':'REQUEST_ALREADY_RECORDED','request_id':request_id,
                'next_action':'Lead publication pending; poll the next card now.'}
        # A new head supersedes this attempt's earlier open requests (preserved, not erased).
        for other in requests.values():
            if other['attempt_id']==attempt['id'] and other['status']=='OPEN':
                other['status']='SUPERSEDED'
                other['superseded_by']=request_id
        requests[request_id]={'request_id':request_id,'task_id':c['id'],
            'attempt_id':attempt['id'],'agent_id':a['agent_id'],'head_sha':a['head_sha'],
            'branch':a.get('branch'),'criteria_sha256':c['criteria_sha256'],
            'checkpoint':a['checkpoint'],'artifacts':deepcopy(a['artifacts']),
            'status':'OPEN','requested_at':__import__('datetime').datetime.now(
                __import__('datetime').timezone.utc).isoformat()}
        attempt['state']='PUBLICATION_REQUESTED'
        attempt['publication_request_id']=request_id
        registry.event(state,'kanban_publication_request',
                       {'task':c['id'],'attempt':attempt['id'],'request':request_id,
                        'head':a['head_sha']})
        return {'state':'PUBLICATION_REQUESTED','request_id':request_id,
            'next_action':'Lead publishes this preserved candidate; poll the next card now. A request is never a submission or completion.'}

def fulfil_publication(registry,a):
    """Lead-only: record that a requested candidate was published as a real PR.
    Idempotent per request; the PR is recorded exactly like a worker submission."""
    lead(a);pr_identity(a['pr_url'],a['head_sha'])
    with registry.transaction() as state:
        b=board(state);c=b['cards'][a['task_id']]
        require(c['state']!='DONE','task_already_completed')
        attempt=c['attempts'][a['attempt_id']]
        require(attempt['agent_id']==a.get('agent_id'),'wrong_attempt_owner')
        request=c.get('publication_requests',{}).get(a['request_id'])
        require(request is not None,'unknown_publication_request')
        require(request['head_sha']==a['head_sha'],'request_head_changed')
        require(request['criteria_sha256']==c['criteria_sha256'],'criteria_changed')
        pr=c['prs'].get(a['pr_url'])
        if pr and pr.get('fulfilled_request')==a['request_id']:
            return {'state':'ALREADY_FULFILLED','request_id':a['request_id'],
                    'pr_url':a['pr_url']}
        require(_record_pr(b,c,attempt,a['pr_url'],a['head_sha'],'lead_fulfilment')
                or pr is not None,'pr_record_failed')
        c['prs'][a['pr_url']]['fulfilled_request']=a['request_id']
        request['status']='FULFILLED';request['pr_url']=a['pr_url']
        request['fulfilled_at']=__import__('datetime').datetime.now(
            __import__('datetime').timezone.utc).isoformat()
        registry.event(state,'kanban_publication_fulfilled',
                       {'task':c['id'],'request':a['request_id'],'pr':a['pr_url']})
        return {'state':'FULFILLED','request_id':a['request_id'],'pr_url':a['pr_url'],
                'next_action':'Review the exact head; this PR now follows the normal review/merge path.'}

def park(registry,a):
    require(a.get('checkpoint') and a.get('writes_stopped') is True,'checkpoint_and_stopped_writes_required')
    with registry.transaction() as state:
        c,attempt=owned_attempt(board(state),a)
        attempt.update(state='PAUSED',checkpoint=a['checkpoint'])
        registry.event(state,'kanban_park',{'task':c['id'],'attempt':attempt['id']})
        return {'state':'PAUSED','next_action':'Poll another card; your workspace and task messages remain preserved.'}

def post(registry,a):
    require(a.get('author') and 0<len(a.get('body',''))<=8000,'message_author_and_body_required')
    with registry.transaction() as state:
        c=board(state)['cards'][a['task_id']]
        require(len(c['messages'])<500,'task_mailbox_capacity')
        if a.get('reply_to'):require(any(m['id']==a['reply_to'] for m in c['messages']),'unknown_message')
        m={'id':'msg-'+uuid.uuid4().hex,'author':a['author'],'body':a['body'],
            'pr_url':a.get('pr_url'),'head_sha':a.get('head_sha'),'reply_to':a.get('reply_to'),
            'status':'OPEN','at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
        c['messages'].append(m)
        registry.event(state,'kanban_message',{'task':c['id'],'message':m['id']})
        return deepcopy(m)

def review(registry,a):
    lead(a);require(a.get('verdict') in ('ACCEPTED','CHANGES_REQUIRED'),'invalid_review_verdict')
    require(a.get('evidence_reference') and a.get('body'),'review_evidence_and_reason_required')
    with registry.transaction() as state:
        c=board(state)['cards'][a['task_id']];require(c['state']!='DONE','task_already_completed')
        pr=c['prs'][a['pr_url']];require(pr['head_sha']==a['head_sha'],'review_head_changed')
        resolved=a.get('resolved_message_ids',[])
        require(set(resolved)<={m['id'] for m in c['messages']},'unknown_message_resolution')
        history=c.setdefault('review_history',[]);require(len(history)<500,'review_history_capacity')
        history.append({k:deepcopy(a.get(k)) for k in ('pr_url','head_sha','verdict','evidence_reference','body','resolved_message_ids')})
        for m in c['messages']:
            if m['id'] in resolved:m.update(status='RESOLVED',resolved_by=LEAD,resolution=a['body'])
        if a['verdict']=='ACCEPTED':
            require(not any(m['status']=='OPEN' and m['author']==LEAD and
                m.get('pr_url') in (None,a['pr_url']) for m in c['messages']),'unresolved_lead_feedback')
        pr['review']={'verdict':a['verdict'],'head_sha':a['head_sha'],'criteria_sha256':c['criteria_sha256'],
            'evidence_reference':a['evidence_reference'],'body':a['body']}
        if a['verdict']=='CHANGES_REQUIRED':
            require(len(c['messages'])<500,'task_mailbox_capacity')
            c['messages'].append({'id':'msg-'+uuid.uuid4().hex,'author':LEAD,'body':a['body'],
                'pr_url':a['pr_url'],'head_sha':a['head_sha'],'status':'OPEN'})
            c['state']='CHANGES_REQUESTED'
        registry.event(state,'kanban_review',{'task':c['id'],'pr':a['pr_url'],'verdict':a['verdict']})
        return deepcopy(pr)

def accept_merge(registry,a,github):
    """github is fetched from GitHub by CLI, never supplied by a worker arguments file."""
    lead(a)
    require(github.get('merged') is True and github.get('html_url')==a['pr_url'],'github_merge_not_verified')
    require(github.get('base',{}).get('ref')==BASE,'wrong_merge_base')
    head=github.get('head',{}).get('sha');merge=github.get('merge_commit_sha')
    pr_identity(a['pr_url'],head);require(re.fullmatch('[0-9a-f]{40}',merge or '') is not None,'merge_commit_required')
    with registry.transaction() as state:
        b=board(state);c=b['cards'][a['task_id']]
        if c['state']=='DONE':
            require(c['winner']['pr_url']==a['pr_url'] and c['winner']['head_sha']==head,'another_pr_already_won')
            return {'state':'ALREADY_COMPLETED','winner':deepcopy(c['winner'])}
        pr=c['prs'][a['pr_url']];r=pr.get('review') or {}
        require(pr['head_sha']==head and r.get('head_sha')==head and r.get('verdict')=='ACCEPTED'
                and r.get('criteria_sha256')==c['criteria_sha256'],'merged_head_not_approved')
        require(not any(m['status']=='OPEN' and m['author']==LEAD and m.get('pr_url') in (None,a['pr_url']) for m in c['messages']),'unresolved_lead_feedback')
        c.update(state='DONE',winner={'pr_url':a['pr_url'],'head_sha':head,'merge_commit_sha':merge,
            'merged_at':github.get('merged_at'),'criteria_sha256':c['criteria_sha256']})
        for attempt in c['attempts'].values():attempt['state']='WON' if attempt['id']==pr['attempt_id'] else 'SUPERSEDED'
        refill(b)
        registry.event(state,'kanban_complete_refill',{'task':c['id'],'winner':a['pr_url']})
        return {'state':'COMPLETED','board':summary(b),'winner':deepcopy(c['winner'])}

def enqueue(registry,a):
    lead(a)
    with registry.transaction() as state:
        b=board(state);spec=a['spec']
        validate_specs(b['backlog']+[spec]);b['backlog'].append(deepcopy(spec));refill(b)
        registry.event(state,'kanban_enqueue',{'task':spec['id']})
        return summary(b)
