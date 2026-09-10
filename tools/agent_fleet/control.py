"""Five-slot, single-host control-plane reference. No Git/process mutation.

All state transitions execute inside one SQLite BEGIN IMMEDIATE transaction.
Only the controller opens the DB; clients use HTTP. Not a hostile-user sandbox.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import secrets
import sqlite3
from layout import slot_layout

class Refusal(ValueError):
    pass

def require(condition, reason):
    if not condition:
        raise Refusal(reason)

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def text(value, name):
    require(isinstance(value, str) and bool(value.strip()), 'missing_'+name)
    return value

def integer(value, lo, hi, name):
    require(type(value) is int and lo <= value <= hi, 'invalid_'+name)
    return value

def sha(value):
    require(isinstance(value,str) and re.fullmatch('[0-9a-f]{40}',value), 'invalid_commit')
    return value

def path_scope(value):
    value=text(value,'scope').replace('\\','/')
    p=PurePosixPath(value)
    require(not p.is_absolute() and ':' not in value and not any(x in ('.','..','') for x in value.split('/')), 'invalid_scope')
    require('.git' not in [x.casefold() for x in p.parts], 'git_metadata_scope')
    v=value.casefold()
    protected='chimeraengine/engine/build'
    require(not (v==protected or v.startswith(protected+'/') or protected.startswith(v+'/')), 'protected_build_scope')
    return value

def overlaps(a,b):
    a=a.casefold(); b=b.casefold()
    return a==b or a.startswith(b+'/') or b.startswith(a+'/')

class Control:
    def __init__(self, db, supervisor_token, enrollment_token, root,
                 memory_budget_mb=16384):
        require(supervisor_token and enrollment_token and supervisor_token!=enrollment_token,'distinct_service_tokens_required')
        self.db=str(db); self.supervisor=digest(supervisor_token);self.enrollment=digest(enrollment_token)
        self.memory_budget_mb=integer(memory_budget_mb,1024,2**40,'memory_budget_mb')
        root=str(Path(root).resolve())
        Path(db).parent.mkdir(parents=True,exist_ok=True)
        con=self.connect()
        try:
            con.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL)')
            initial={'schema':1,'revision':0,'root':root,'supervisor_hash':self.supervisor,'enrollment_hash':self.enrollment,
                     'leader':None,'epoch':0,'agents':{},'tasks':{},'resources':{},'requests':{},
                     'resource_queues':[],'memory':{'budget_mb':self.memory_budget_mb,'admitted_mb':0},
                     'slots':{str(i):{'task':None,**slot_layout(root,i)} for i in range(1,6)}}
            con.execute('INSERT OR IGNORE INTO state VALUES(1,?)',(json.dumps(initial),))
            saved=json.loads(con.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            require(saved['schema']==1 and saved['root']==root,'configuration_mismatch')
            require(saved['supervisor_hash']==self.supervisor and saved['enrollment_hash']==self.enrollment,'service_identity_mismatch')
        finally: con.close()

    def connect(self):
        return sqlite3.connect(self.db,timeout=10,isolation_level=None)

    def _actor(self,s,token):
        d=digest(token)
        if secrets.compare_digest(d,self.supervisor): return 'SUPERVISOR'
        if secrets.compare_digest(d,self.enrollment): return 'ENROLLMENT'
        for aid,a in s['agents'].items():
            if secrets.compare_digest(d,a['token_hash']):
                require(a['alive'],'session_revoked')
                return aid
        raise Refusal('unauthorized')

    def _lead(self,s,actor,epoch):
        require(actor==s['leader'] and epoch==s['epoch'],'stale_or_nonleader')

    def _task(self,s,actor,tid,generation):
        t=s['tasks'].get(tid)
        require(t is not None,'unknown_task')
        require(t['owner']==actor and t['generation']==generation,'stale_or_foreign_claim')
        require(t['state'] in ('RUNNING','BLOCKED','REVIEW'),'task_not_owned_active')
        return t

    def _elect(self,s):
        old=s['epoch']
        candidates=[(a['rank'],aid) for aid,a in s['agents'].items()
                    if a['alive'] and a['qualified'] and a['can_lead'] and a['ready_epoch']==old]
        s['epoch']+=1
        s['leader']=sorted(candidates,key=lambda x:(-x[0],x[1]))[0][1] if candidates else None
        return {'leader':s['leader'],'epoch':s['epoch']}

    def _fail(self,s,aid,reason,evidence):
        require(aid in s['agents'] and s['agents'][aid]['alive'],'not_live_agent')
        text(evidence,'failure_evidence')
        s['agents'][aid]['alive']=False
        for t in s['tasks'].values():
            if t['owner']==aid and t['state'] in ('RUNNING','BLOCKED','REVIEW'):
                t['state']='RECOVERY_HOLD';t['generation']+=1
        for q in s['resource_queues']:
            if q['owner']==aid and not q['served']:
                q['served']=True;q['dropped_reason']='owner_failed'
        # Resource ownership is intentionally retained until trusted process-drain evidence.
        if s['leader']==aid:self._elect(s)
        return {'leader':s['leader'],'epoch':s['epoch'],'reason':reason}

    PHYSICAL=('rtx4090',)
    CHAINED=('engine_demo','dyad_eye')
    MEMORY='memory'
    KNOWN_RESOURCES=PHYSICAL+CHAINED+(MEMORY,)
    CLASS_BY_NAME={'rtx4090':'gpu_functionality','engine_demo':'engine_demo',
                   'dyad_eye':'dyad_inference','memory':'memory'}

    def _declare_resources(self,resources,allow_unknown_memory=False):
        require(isinstance(resources,list),'invalid_resources')
        out=[]
        for item in resources:
            require(isinstance(item,dict) and set(item)-{'name','class','memory_mb'}==set(),'invalid_resource_declaration')
            name=text(item.get('name'),'resource_name')
            require(name in self.KNOWN_RESOURCES,'unknown_resource')
            klass=item.get('class') or self.CLASS_BY_NAME[name]
            require(isinstance(klass,str) and klass in ('gpu_functionality','gpu_benchmark',
                                                        'engine_demo','dyad_inference','memory'),'invalid_resource_class')
            mem=item.get('memory_mb')
            require(mem is None or (type(mem) is int and mem>0),'invalid_memory_mb')
            if name=='memory':
                require(type(mem) is int and mem>0,'memory_declares_no_mb') if not allow_unknown_memory else None
            out.append({'name':name,'class':klass,'memory_mb':mem})
        return out

    def _declare_wants(self,wants):
        require(isinstance(wants,list) and wants,'wants_required')
        seen=set();out=[]
        for item in self._declare_resources(wants,allow_unknown_memory=True):
            require(item['name'] not in seen,'duplicate_resource_want')
            seen.add(item['name']);out.append(item)
        return out

    def _queue_entry(self,s,req):
        return {'id':req['id'],'task':req['task'],'owner':req['owner'],
                'generation':req['generation'],'wants':req['wants'],
                'priority':req['priority'],'enqueued_revision':req['enqueued_revision'],
                'waiting_revisions':max(0,s['revision']-req['enqueued_revision']+1),
                'served':req['served'],'granted':req['granted'],
                'allocation_failed':req['allocation_failed'],'stalled':req['stalled'],
                'granted_revision':req['granted_revision'],'revoked':req.get('revoked',False),
                'dropped_reason':req.get('dropped_reason'),'grant_keys':req.get('grant_keys')}

    def _promote_one(self,s,req):
        """Satisfy one queued request all-or-nothing (atomic: caller holds the
        BEGIN IMMEDIATE transaction). Same-resource fairness is strict FIFO --
        a later request never jumps an earlier request that wants the SAME
        resource, regardless of priority (priority is a stamp, aging is the
        recorded waiting count)."""
        t=s['tasks'].get(req['task'])
        if t is None or t['owner']!=req['owner'] or t['generation']!=req['generation'] \
                or t['state'] not in ('RUNNING','BLOCKED'):
            req['served']=True;req['dropped_reason']='stale_claim'
            return 'dropped'
        held=s['resources']
        wants=req['wants'];names=[w['name'] for w in wants]
        rtx=held.get('rtx4090')
        gpu_blocked=rtx is not None and rtx['task']!=req['task']
        wants_bench=any(w.get('class')=='gpu_benchmark' for w in wants if w['name']=='rtx4090')
        if wants_bench:
            if rtx is not None:
                req['stalled']='benchmark_exclusive:gpu_held';return 'contended'
            if any(v['task']!=req['task'] for v in held.values()):
                req['stalled']='benchmark_exclusive:other_hold';return 'contended'
        if 'rtx4090' in names and gpu_blocked:
            if rtx.get('class') == 'gpu_benchmark':
                req['stalled'] = 'benchmark_exclusive:gpu_held'
            else:
                req['stalled'] = 'contended:rtx4090'
            return 'contended'
        if ('engine_demo' in names or 'dyad_eye' in names) and 'rtx4090' not in names:
            if rtx is None or rtx['task']!=req['task']:
                req['stalled']='chained_requires_gpu_same_task';return 'contended'
        mem_asked=0;undetermined=False
        for w in wants:
            if w['name']=='memory':
                if w['memory_mb'] is None:undetermined=True
                else:mem_asked+=w['memory_mb']
        held_mem=sum((r.get('memory_mb') or 0) for r in held.values())
        if mem_asked>0 and held_mem+mem_asked>s['memory']['budget_mb']:
            req['allocation_failed']=True;req['stalled']='memory_allocation_refused'
            return 'allocation_refused'
        now=s['revision']+1
        grant_keys=[]
        for w in wants:
            if w['name']=='memory':
                if not undetermined and mem_asked>0:
                    key='memory.'+req['id']
                    held[key]={'task':req['task'],'owner':req['owner'],'generation':req['generation'],
                               'class':'memory','since_revision':now,'memory_mb':mem_asked,'request':req['id']}
                    grant_keys.append(key)
            else:
                held[w['name']]={'task':req['task'],'owner':req['owner'],'generation':req['generation'],
                                 'class':w['class'] or self.CLASS_BY_NAME[w['name']],
                                 'since_revision':now,'memory_mb':None,'request':req['id']}
                grant_keys.append(w['name'])
        s['memory']['admitted_mb']=sum((r.get('memory_mb') or 0) for r in held.values())
        req['served']=True;req['granted']=True;req['granted_revision']=now
        req['grant_keys']=grant_keys;req['stalled']=None
        return 'granted'

    def _promote_queues(self,s):
        for _ in range(len(s['resource_queues'])+1):
            moved=False
            for req in s['resource_queues']:
                if req['served']:
                    continue
                if self._promote_one(s,req)=='granted':
                    moved=True
            if not moved:
                break

    def call(self,op,token,**p):
        con=self.connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            s=json.loads(con.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            # Schema-1 additive fields (present in registries created before the
            # resource scheduler extension).
            s.setdefault('resource_queues',[])
            s.setdefault('memory',{'budget_mb':self.memory_budget_mb,'admitted_mb':0})
            actor=self._actor(s,token)
            result=self._dispatch(s,actor,op,p)
            if op not in ('snapshot','events'):
                s['revision']+=1
                # Do not persist credentials or arbitrary request text in audit events.
                event={k:p[k] for k in ('task','agent','generation','epoch','reason','request') if k in p}
                event['actor']=actor
                con.execute('INSERT INTO events VALUES(?,?,?)',(s['revision'],op,json.dumps(event)))
                con.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(s),))
            if op=='events':
                cursor=integer(p.get('since',0),0,2**63-1,'cursor')
                rows=con.execute('SELECT seq,kind,body FROM events WHERE seq>? ORDER BY seq LIMIT 200',(cursor,)).fetchall()
                result={'events':[{'sequence':n,'kind':k,**json.loads(b)} for n,k,b in rows], 'revision':s['revision']}
            con.execute('COMMIT')
            return {'revision':s['revision'],'result':result}
        except Exception:
            if con.in_transaction:con.execute('ROLLBACK')
            raise
        finally: con.close()

    def _dispatch(self,s,actor,op,p):
        if op=='feedback_add':
            source=p.get('source')
            require(source in ('HUMAN','DYAD','AGENT'),'invalid_feedback_source')
            if source=='HUMAN':require(actor=='SUPERVISOR','trusted_human_adapter_required')
            else:require(actor=='SUPERVISOR' or actor in s['agents'],'agent_or_supervisor_required')
            categories=p.get('categories')
            allowed={'INTENT','APPEARANCE','USABILITY','PHYSICS_CLAIM','DEFECT',
                     'PERFORMANCE','ACCESSIBILITY','QUESTION','STOP','PERMISSION','SCOPE','UNCLASSIFIED'}
            require(isinstance(categories,list) and bool(categories) and
                    all(isinstance(x,str) and x in allowed for x in categories),'invalid_feedback_categories')
            tasks=p.get('tasks',[])
            require(isinstance(tasks,list) and all(isinstance(x,str) and x in s['tasks'] for x in tasks),'unknown_feedback_task')
            evidence=text(p.get('evidence'),'feedback_evidence')
            body=text(p.get('text'),'feedback_text')
            feedback=s.setdefault('feedback',{})
            fid=secrets.token_hex(12)
            feedback[fid]={'id':fid,'source':source,'submitted_by':actor,
                'categories':categories,'tasks':tasks,'text':body,'evidence':evidence,
                'revision':s['revision']+1,'dispositions':[],
                'authority_action_required':source=='HUMAN' and bool(set(categories)&{'STOP','PERMISSION','SCOPE'}),
                'acceptance':'NOT_CLAIMED'}
            return feedback[fid]
        if op=='feedback_disposition':
            self._lead(s,actor,p.get('epoch'))
            f=s.get('feedback',{}).get(p.get('feedback'))
            require(f is not None,'unknown_feedback')
            status=p.get('status')
            require(status in ('ACKNOWLEDGED','INVESTIGATE','TASK_PROPOSED','ADDRESSED',
                               'DEFERRED','DISAGREEMENT_RECORDED'),'invalid_feedback_disposition')
            item={'status':status,'reason':text(p.get('reason'),'disposition_reason'),
                  'evidence':text(p.get('evidence'),'disposition_evidence'),
                  'actor':actor,'epoch':s['epoch'],'revision':s['revision']+1}
            f['dispositions'].append(item)
            return {'feedback':f['id'],'disposition':item,'acceptance':'NOT_CLAIMED'}
        if op=='enroll':
            require(actor in ('ENROLLMENT','SUPERVISOR'),'enrollment_only')
            aid=text(p.get('agent'),'agent')
            require(re.fullmatch('[a-zA-Z0-9_-]{1,80}',aid) and aid not in s['agents'],'invalid_or_existing_agent')
            secret=secrets.token_urlsafe(32)
            s['agents'][aid]={'label':text(p.get('label'),'label'),'token_hash':digest(secret),'alive':True,
                'qualified':False,'capabilities':[],'max_tasks':1,'can_lead':False,'rank':0,'ready_epoch':None,'qualification':None}
            return {'agent':aid,'session_token':secret,'qualified':False}
        require(actor!='ENROLLMENT','enrollment_cannot_control')
        if op=='snapshot':
            out=json.loads(json.dumps(s));out.pop('supervisor_hash');out.pop('enrollment_hash')
            for a in out['agents'].values():a.pop('token_hash')
            return out
        if op=='events':return None
        if op=='qualify':
            require(actor=='SUPERVISOR','supervisor_only')
            a=s['agents'].get(p.get('agent'));require(a is not None and a['alive'],'unknown_or_failed_agent')
            caps=p.get('capabilities',[])
            require(isinstance(caps,list) and all(isinstance(x,str) and x for x in caps),'invalid_capabilities')
            require(type(p.get('can_lead',False)) is bool,'invalid_lead_flag')
            a.update(qualified=True,capabilities=sorted(set(caps)),max_tasks=integer(p.get('max_tasks',1),1,5,'capacity'),
                     can_lead=p.get('can_lead',False),rank=integer(p.get('rank',0),0,1000,'rank'),
                     qualification=text(p.get('evidence'),'qualification_evidence'))
            return {'qualified':p['agent']}
        if op=='offer_lead':
            require(actor in s['agents'],'agent_only');a=s['agents'][actor]
            require(a['qualified'] and a['can_lead'],'not_qualified_for_lead')
            require(p.get('epoch')==s['epoch'],'stale_offer')
            a['ready_epoch']=s['epoch'];a['recovery_offer']=text(p.get('checkpoint'),'recovery_checkpoint')
            # An offer is readiness, not self-appointment. Supervisor initializes;
            # qualified standby offers are used automatically upon confirmed failure.
            return {'offered_for_epoch':s['epoch']}
        if op=='elect':
            require(actor=='SUPERVISOR' and s['leader'] is None,'initial_or_vacant_supervisor_election_only')
            return self._elect(s)
        if op=='suspect':
            require(p.get('agent') in s['agents'],'unknown_agent')
            return {'investigation_required':True,'leader_unchanged':s['leader'],'reason':text(p.get('reason'),'suspicion')}
        if op=='fail':
            require(actor=='SUPERVISOR','trusted_failure_observer_required')
            require(p.get('reason') in ('PROCESS_EXIT','PROVIDER_TERMINAL_ERROR','OPERATOR_REVOKED','CORROBORATED_FAILURE'),'unsupported_failure_reason')
            return self._fail(s,p.get('agent'),p['reason'],p.get('evidence'))
        if op=='yield':
            require(actor in s['agents'],'agent_only')
            return self._fail(s,actor,'EXPLICIT_YIELD',text(p.get('checkpoint'),'preservation_checkpoint'))
        if op=='create_task':
            self._lead(s,actor,p.get('epoch'))
            tid=text(p.get('task'),'task')
            require(re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',tid) and tid not in s['tasks'],'invalid_or_duplicate_task')
            scopes=p.get('scopes');require(isinstance(scopes,list) and scopes,'scopes_required')
            scopes=[path_scope(x) for x in scopes]
            deps=p.get('dependencies',[]);require(isinstance(deps,list) and all(x in s['tasks'] for x in deps),'dependencies_must_exist')
            req=p.get('capabilities',[]);require(isinstance(req,list) and all(isinstance(x,str) for x in req),'invalid_capabilities')
            kind=p.get('kind','worker');require(kind in ('integration','worker'),'invalid_task_kind')
            resources=p.get('resources',[])
            resources=self._declare_resources(resources)
            s['tasks'][tid]={'id':tid,'state':'READY','owner':None,'slot':None,'generation':0,'kind':kind,
                'base':sha(p.get('base')),'branch':'astra/tasks/'+tid,'pr_base':'astra/gait-capture',
                'scopes':scopes,'dependencies':deps,'capabilities':req,'resources':resources,
                'packet':text(p.get('packet'),'packet'),
                'checkpoint':None,'head':None,'review':None,'integration':None}
            return s['tasks'][tid]
        if op=='claim':
            require(actor in s['agents'] and s['agents'][actor]['qualified'],'qualified_agent_required')
            a=s['agents'][actor]; t=s['tasks'].get(p.get('task'));require(t is not None and t['state']=='READY','task_not_ready')
            require(t['kind']!='integration' or actor==s['leader'],'integration_slot_lead_only')
            if any(overlaps(x,'docs/THE_MASTER_LIST.md') for x in t['scopes']):
                require(actor==s['leader'],'master_list_lead_only')
            require(set(t['capabilities']) <= set(a['capabilities']),'capability_missing')
            active=[v for v in s['tasks'].values() if v['owner']==actor and v['state'] in ('RUNNING','BLOCKED','REVIEW','RECOVERY_HOLD')]
            require(len(active)<a['max_tasks'],'agent_capacity_reached')
            require(all(s['tasks'][d]['state']=='INTEGRATED' for d in t['dependencies']),'dependencies_not_integrated')
            for other in s['tasks'].values():
                if other['state'] in ('RUNNING','BLOCKED','REVIEW','RECOVERY_HOLD'):
                    require(not any(overlaps(x,y) for x in t['scopes'] for y in other['scopes']),'write_scope_conflict')
            available=[(n,v) for n,v in s['slots'].items() if v['task'] is None and v['kind']==t['kind']]
            require(available,'no_free_slot')
            n,slot=available[0];slot['task']=t['id'];t.update(owner=actor,slot=n,state='RUNNING',generation=t['generation']+1)
            return {**t,'worktree':slot['path'],'engine':slot['engine'],'provisioning':'REQUIRED: claim metadata does not create or modify a worktree'}
        if op in ('checkpoint','submit_review','resource_acquire','resource_release'):
            t=self._task(s,actor,p.get('task'),p.get('generation'))
            if op=='checkpoint':
                require(t['state'] in ('RUNNING','BLOCKED'),'review_is_frozen')
                state=p.get('state','RUNNING');require(state in ('RUNNING','BLOCKED'),'invalid_checkpoint_state')
                t.update(checkpoint=text(p.get('checkpoint'),'checkpoint'),state=state)
                return {'saved':True}
            if op=='submit_review':
                require(t['state']=='RUNNING','task_not_running')
                require(p.get('branch')==t['branch'],'wrong_task_branch')
                require(not any(r['task']==t['id'] for r in s['resources'].values()),'release_resources_before_review')
                for q in s['resource_queues']:
                    if q['task']==t['id'] and not q['served']:
                        q['served']=True;q['dropped_reason']='reviewed'
                t.update(state='REVIEW',head=sha(p.get('head')),review=text(p.get('evidence'),'review_evidence'))
                return {'state':'REVIEW','acceptance':'NOT_CLAIMED'}
            name=p.get('resource');require((name in ('rtx4090','dyad_eye','engine_demo'))
                                           or name=='memory' or name.startswith('memory.'),'unknown_resource')
            if op=='resource_acquire':
                require(t['state']=='RUNNING' and name not in s['resources'],'resource_not_available')
                if name=='dyad_eye':require(s['resources'].get('rtx4090',{}).get('task')==t['id'],'dyad_requires_gpu_reservation')
                klass={'rtx4090':'gpu_functionality','dyad_eye':'dyad_inference','engine_demo':'engine_demo'}[name]
                s['resources'][name]={'task':t['id'],'owner':actor,'generation':t['generation'],
                                      'class':klass,'since_revision':s['revision']+1,'memory_mb':None}
            else:
                targets=[name] if name!='memory' else [k for k,r in s['resources'].items()
                                                       if k.startswith('memory.') and r['task']==t['id']]
                require(bool(targets),'resource_not_held')
                for k in targets:
                    r=s['resources'].get(k);require(r and r['task']==t['id'] and r['generation']==t['generation'],'foreign_resource')
                    require(not(k=='rtx4090' and s['resources'].get('dyad_eye',{}).get('task')==t['id']),'release_dyad_first')
                    text(p.get('evidence'),'resource_drained_evidence');del s['resources'][k]
                self._promote_queues(s)
            return {'resource':name,'action':op}
        if op=='resource_clear':
            require(actor=='SUPERVISOR','supervisor_only')
            name=p.get('resource');require(name in s['resources'],'resource_not_held')
            if name=='rtx4090':require('dyad_eye' not in s['resources'],'release_dyad_first')
            text(p.get('evidence'),'actual_process_drained_evidence');del s['resources'][name]
            self._promote_queues(s)
            return {'cleared':name}
        if op=='resource_request':
            t=self._task(s,actor,p.get('task'),p.get('generation'))
            wants=self._declare_wants(p.get('wants'))
            priority=integer(p.get('priority',5),0,9,'priority')
            req={'id':secrets.token_hex(8),'task':t['id'],'owner':actor,'generation':t['generation'],
                 'wants':wants,'priority':priority,'enqueued_revision':s['revision']+1,
                 'served':False,'granted':False,'allocation_failed':False,'stalled':None,
                 'granted_revision':None,'dropped_reason':None,'revoked':False}
            s['resource_queues'].append(req)
            self._promote_queues(s)
            return self._queue_entry(s,req)
        if op=='resource_queue':
            t=self._task(s,actor,p.get('task'),p.get('generation'))
            entries=[self._queue_entry(s,q) for q in s['resource_queues']
                     if q['task']==t['id'] and not q['served']]
            return {'queued':entries}
        if op=='resource_revoke_pending':
            t=self._task(s,actor,p.get('task'),p.get('generation'))
            n=0
            for q in s['resource_queues']:
                if q['task']==t['id'] and not q['served']:
                    q['served']=True;q['revoked']=True;q['dropped_reason']='revoked';n+=1
            self._promote_queues(s)
            return {'revoked':n}
        if op=='recover':
            require(actor=='SUPERVISOR','preservation_observer_required')
            t=s['tasks'].get(p.get('task'));require(t and t['state']=='RECOVERY_HOLD','not_recovery_hold')
            require(not any(r['task']==t['id'] for r in s['resources'].values()),'resources_still_held')
            for q in s['resource_queues']:
                if q['task']==t['id'] and not q['served']:
                    q['served']=True;q['dropped_reason']='recovered_generation'
            t['checkpoint']=text(p.get('evidence'),'preserved_and_writer_stopped_evidence')
            s['slots'][t['slot']]['task']=None
            t.update(state='READY',owner=None,slot=None,generation=t['generation']+1)
            self._promote_queues(s)
            return {'state':'READY','old_workspace':'must remain preserved until lead explicitly provisions replacement'}
        if op=='integration_request':
            self._lead(s,actor,p.get('epoch'))
            t=s['tasks'].get(p.get('task'));require(t and t['state']=='REVIEW','not_in_review')
            require(p.get('head')==t['head'] and p.get('branch')==t['branch'],'head_or_branch_mismatch')
            rid=secrets.token_hex(12)
            s['requests'][rid]={'task':t['id'],'head':t['head'],'branch':t['branch'],'base_branch':t['pr_base'],
                'expected_base':sha(p.get('expected_base')),'epoch':s['epoch'],'leader':actor,'review':text(p.get('review'),'independent_review'),
                'state':'PENDING_EXTERNAL_BROKER'}
            return {'request':rid,**s['requests'][rid],'publication_executed':False}
        if op=='ack_integration':
            require(actor=='SUPERVISOR','trusted_publisher_only')
            r=s['requests'].get(p.get('request'));require(r is not None,'unknown_integration_request')
            require(r['epoch']==s['epoch'] and r['leader']==s['leader'],'stale_integration_epoch')
            require(r['state']=='PENDING_EXTERNAL_BROKER','integration_already_acknowledged')
            t=s['tasks'][r['task']];require(t['state']=='REVIEW' and t['head']==r['head'],'review_changed')
            require(p.get('base_branch')=='astra/gait-capture' and p.get('expected_base')==r['expected_base'],'wrong_integration_base')
            t.update(state='INTEGRATED',integration={'commit':sha(p.get('commit')),'evidence':text(p.get('evidence'),'published_review_evidence')})
            r['state']='ACKNOWLEDGED'
            return {'state':'INTEGRATED','slot':'held until cleanup attestation'}
        if op=='review_requeue':
            # Stale-base reconciliation WITHOUT force-push: a REVIEW blocked by
            # a publication refusal (e.g. the base advanced legitimately while
            # the task ran) returns to RUNNING at a NEW generation. The review
            # is void (head cleared); the worktree, checkpoint history and
            # slot ownership are preserved. Lead-only, current epoch.
            self._lead(s,actor,p.get('epoch'))
            t=s['tasks'].get(p.get('task'));require(t is not None and t['state']=='REVIEW','not_in_review')
            t.update(state='RUNNING',head=None,generation=t['generation']+1,
                     checkpoint=text(p.get('evidence'),'requeue_reconciliation_evidence'))
            return {'state':'RUNNING','generation':t['generation'],'worktree_preserved':True}
        if op=='provision_slot':
            require(actor=='SUPERVISOR','supervisor_only')
            t=s['tasks'].get(p.get('task'));require(t is not None,'unknown_task')
            slot=s['slots'].get(str(t['slot']));require(slot is not None and slot['task']==t['id'],'task_has_no_slot')
            require(t['state']=='RUNNING','task_not_running')
            require(not slot['engine'].get('provisioned'),'slot_already_provisioned')
            slot['engine']['provisioned']=True
            slot['engine']['worktree_head']=sha(p.get('worktree_head'))
            slot['engine']['provision_evidence']=text(p.get('evidence'),'provision_evidence')
            return {'slot':t['slot'],'provisioned':True}
        if op=='release_slot':
            require(actor=='SUPERVISOR','supervisor_only')
            t=s['tasks'].get(p.get('task'));require(t and t['state']=='INTEGRATED' and t['slot'],'task_not_integrated_in_slot')
            text(p.get('evidence'),'preserved_clean_workspace_and_stopped_processes')
            require(not any(r['task']==t['id'] for r in s['resources'].values()),'resource_still_held')
            slot=s['slots'][t['slot']]
            if slot['engine'].get('provisioned'):
                slot['engine']['provisioned']=False
                slot['engine'].pop('worktree_head',None)
                slot['engine'].pop('provision_evidence',None)
            slot['task']=None;t['slot']=None
            return {'released':True,'filesystem_deleted':False}
        raise Refusal('unknown_operation')
