"""Stateless campaign reader/admission planner. No launch, mutation, or deletion."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from integrity import verify_catalog

HERE = Path(__file__).resolve().parent
GIB = 1024**3
MAX_AGENTS = 10
MAX_SNAPSHOT_AGE = 120
DEFAULT_RESERVE = 100 * GIB
DEFAULT_GROWTH_BUDGET = 160 * GIB
STATES = {'READY', 'RUNNING', 'BLOCKED', 'REVIEW', 'RECOVERY_HOLD', 'INTEGRATED'}
BUSY = {'RUNNING', 'BLOCKED', 'REVIEW', 'RECOVERY_HOLD'}


class Refusal(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise Refusal(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def integer(value, name, minimum=0):
    require(type(value) is int and value >= minimum, 'invalid_' + name)
    return value


def validate_catalog(data):
    tasks = data.get('tasks')
    require(isinstance(tasks, list) and tasks, 'missing_tasks')
    by = {}
    for t in tasks:
        require(isinstance(t, dict), 'invalid_task')
        tid = t.get('id')
        require(isinstance(tid, str) and re.fullmatch(r'[A-Z][0-9]{2}', tid), 'invalid_task_id')
        require(tid not in by, 'duplicate_task_id:' + tid)
        require(t.get('scope') in {'core', 'recommended_product', 'conditional'}, 'invalid_scope:' + tid)
        require(isinstance(t.get('depends_on'), list), 'invalid_dependencies:' + tid)
        require(isinstance(t.get('title'), str) and t['title'], 'missing_title:' + tid)
        require(isinstance(t.get('done_when'), str) and t['done_when'], 'missing_acceptance:' + tid)
        by[tid] = t
    seen, visiting = set(), set()
    def visit(tid):
        require(tid in by, 'unknown_dependency:' + str(tid))
        require(tid not in visiting, 'dependency_cycle:' + tid)
        if tid in seen:
            return
        visiting.add(tid)
        for dep in by[tid]['depends_on']:
            visit(dep)
        visiting.remove(tid)
        seen.add(tid)
    for tid in by:
        visit(tid)
    return by


def selected_tasks(by, conditional=False):
    # Product decisions remain tasks; no task can disappear because it is inconvenient.
    selected = {i for i,t in by.items() if conditional or t['scope'] != 'conditional'}
    def include(i):
        for dep in by[i]['depends_on']:
            if dep not in selected:
                selected.add(dep)
                include(dep)
    for i in list(selected):
        include(i)
    return selected


def fetch_snapshot(session_path):
    """Only an explicitly supplied ordinary session; no secret discovery or printing."""
    session = read_json(session_path)
    endpoint = session.get('endpoint', '')
    u = urlparse(endpoint)
    require(u.scheme in {'http', 'https'} and u.hostname in {'127.0.0.1','localhost','::1'}
            and not u.username and not u.password, 'local_controller_endpoint_required')
    require(isinstance(session.get('token'), str) and session['token'], 'session_token_missing')
    req = Request(endpoint, data=json.dumps({'operation':'snapshot','arguments':{}}).encode(),
                  headers={'Authorization':'Bearer '+session['token'], 'Content-Type':'application/json'})
    try:
        with urlopen(req, timeout=15) as response:
            data = json.load(response)
    except Exception as exc:
        # Do not echo server bodies or session contents into model logs.
        raise Refusal('controller_snapshot_failed:' + type(exc).__name__) from None
    state = data.get('result', data)
    return {'captured_at_unix':time.time(), 'snapshot':state}


def snapshot_state(envelope, now=None):
    now = time.time() if now is None else now
    stamp = envelope.get('captured_at_unix')
    require(type(stamp) in (int,float) and math.isfinite(stamp), 'snapshot_timestamp_missing')
    require(-5 <= now-stamp <= MAX_SNAPSHOT_AGE, 'snapshot_stale_or_future')
    s = envelope.get('snapshot')
    require(isinstance(s, dict) and isinstance(s.get('tasks'),dict) and isinstance(s.get('slots'),dict),
            'invalid_controller_snapshot')
    for task in s['tasks'].values():
        require(isinstance(task,dict) and task.get('state') in STATES, 'unsupported_controller_task_state')
    return s


def normalized_scope(path):
    require(isinstance(path,str) and path.strip(), 'invalid_write_scope')
    s=path.replace('\\','/').strip('/').casefold()
    require(s not in ('','.') and not path.startswith(('/','\\')) and '..' not in s.split('/')
            and not re.match(r'^[a-z]:',s), 'scope_must_be_repo_relative')
    return s


def overlapping(a,b):
    a,b=normalized_scope(a),normalized_scope(b)
    return a==b or a.startswith(b+'/') or b.startswith(a+'/')


def integrated(t):
    value=t.get('integration') or {}
    return t.get('state')=='INTEGRATED' and bool(re.fullmatch(r'[0-9a-fA-F]{40}', str(value.get('commit','')))) \
        and isinstance(value.get('evidence'),str) and bool(value['evidence'].strip())


def plan(catalog, envelope, bindings, harness_limit, active_subagents, free_bytes,
         conditional=False, reserve_bytes=DEFAULT_RESERVE, growth_budget=DEFAULT_GROWTH_BUDGET,
         now=None):
    by=validate_catalog(catalog)
    s=snapshot_state(envelope,now)
    selected=selected_tasks(by,conditional)
    integer(harness_limit,'harness_limit',1)
    integer(active_subagents,'active_subagents')
    integer(free_bytes,'free_bytes')
    integer(reserve_bytes,'reserve_bytes')
    integer(growth_budget,'growth_budget')
    require(reserve_bytes>=DEFAULT_RESERVE, 'reserve_below_initial_floor')
    require(growth_budget<=DEFAULT_GROWTH_BUDGET, 'growth_budget_above_initial_ceiling')
    require(bindings.get('schema')=='chimera-monkey-controller-bindings-v1', 'unsupported_bindings_schema')
    mapping=bindings.get('bindings',{})
    require(isinstance(mapping,dict) and set(mapping)<=set(by), 'unknown_binding_task')
    ctl=s['tasks']; completed=set(); unresolved={}; mapped={}
    for tid in sorted(selected):
        entry=mapping.get(tid)
        if entry is None:
            unresolved[tid]='UNBOUND: reconcile existing work; do not duplicate it'
            continue
        require(isinstance(entry,dict), 'invalid_binding:'+tid)
        refs=entry.get('controller_tasks')
        require(isinstance(refs,list) and refs and len(refs)==len(set(refs))
                and all(isinstance(x,str) for x in refs), 'invalid_binding_refs:'+tid)
        require(isinstance(entry.get('mapping_receipt'),str) and entry['mapping_receipt'].strip(),
                'mapping_receipt_required:'+tid)
        if any(cid not in ctl for cid in refs):
            unresolved[tid]='MISSING_CONTROLLER_TASK: refresh/reconcile mapping'
            continue
        mapped[tid]=refs
        if all(integrated(ctl[c]) for c in refs):
            completed.add(tid)
        elif any(ctl[c]['state']=='INTEGRATED' and not integrated(ctl[c]) for c in refs):
            unresolved[tid]='INTEGRATION_EVIDENCE_MISSING'
    empty_slots=sum(1 for slot in s['slots'].values() if slot.get('kind')=='worker' and slot.get('task') is None)
    slots=min(max(0,min(harness_limit,MAX_AGENTS)-active_subagents),empty_slots)
    running_scopes=[]
    outstanding=0;unknown_forecasts=[]
    forecasts=bindings.get('active_growth_forecasts',{})
    require(isinstance(forecasts,dict),'invalid_active_growth_forecasts')
    for cid,t in ctl.items():
        if t['state'] in BUSY:
            running_scopes.extend(t.get('scopes',[]))
            f=forecasts.get(cid,{})
            if f.get('generation')!=t.get('generation') or type(f.get('remaining_bytes')) is not int \
                    or f['remaining_bytes']<0 or not f.get('evidence'):
                unknown_forecasts.append(cid)
            else:
                outstanding+=f['remaining_bytes']
    ready=[];waiting={};seen=set()
    for tid in sorted(selected):
        if tid in completed or tid not in mapped or tid in unresolved:
            continue
        missing=[d for d in by[tid]['depends_on'] if d not in completed]
        if missing:
            waiting[tid]={'reason':'PREREQUISITES_NOT_ACCEPTED','tasks':missing}
            continue
        for cid in mapped[tid]:
            t=ctl[cid]
            if cid in seen or integrated(t):continue
            seen.add(cid)
            if t['state']!='READY':
                waiting[tid]={'reason':t['state'],'controller_task':cid}
                continue
            if t.get('kind','worker')!='worker':
                waiting[tid]={'reason':'COORDINATOR_ACTION','controller_task':cid}
                continue
            deps=t.get('dependencies',[])
            if not all(d in ctl and integrated(ctl[d]) for d in deps):
                waiting[tid]={'reason':'CONTROLLER_DEPENDENCIES_NOT_INTEGRATED'}
                continue
            scopes=t.get('scopes',[])
            if not scopes:
                waiting[tid]={'reason':'WRITE_SCOPE_MISSING'}
                continue
            for scope in scopes:normalized_scope(scope)
            if any(overlapping(x,y) for x in scopes for y in running_scopes):
                waiting[tid]={'reason':'WRITE_SCOPE_CONFLICT'}
                continue
            forecast=mapping[tid].get('additional_peak_bytes')
            if type(forecast) is not int or forecast<0:
                waiting[tid]={'reason':'DISK_FORECAST_REQUIRED'}
                continue
            # Prefer named critical-path defects, then player implementation, then side branches.
            priority={'W':0,'U':1,'F':1,'A':2,'G':2,'K':2,'X':3,'R':3,'S':4,'B':5,'P':0}[tid[0]]
            ready.append((priority,tid,cid,scopes,forecast))
    recommendations=[];reserved=outstanding
    for _,tid,cid,scopes,forecast in sorted(ready):
        if len(recommendations)>=slots:
            waiting[tid]={'reason':'HARNESS_OR_CONTROLLER_CAPACITY'}
            continue
        if unknown_forecasts:
            waiting[tid]={'reason':'ACTIVE_DISK_FORECASTS_MISSING','controller_tasks':unknown_forecasts}
            continue
        if any(overlapping(x,y) for x in scopes for y in running_scopes):
            waiting[tid]={'reason':'BATCH_SCOPE_CONFLICT'}
            continue
        if reserved+forecast>growth_budget or free_bytes-reserved-forecast<reserve_bytes:
            waiting[tid]={'reason':'DISK_ADMISSION_DENIED'}
            continue
        reserved+=forecast;running_scopes.extend(scopes)
        recommendations.append({'planning_task':tid,'controller_task':cid,'additional_peak_bytes':forecast,
            'next_action':'Claim through existing controller; verify capabilities and resources; then use actual harness dispatch'})
    return {'mode':'ADVISORY_NOT_A_CLAIM','goal_complete':selected<=completed,
        'selected_tasks':len(selected),'integrated_with_receipts':sorted(completed),
        'unreconciled':unresolved,'waiting':waiting,'new_dispatch_recommendations':recommendations,
        'capacity':{'campaign_cap':MAX_AGENTS,'harness_limit':harness_limit,
            'active_subagents':active_subagents,'free_controller_worker_slots':empty_slots,'admission_slots':slots},
        'disk':{'free_bytes':free_bytes,'reserve_bytes':reserve_bytes,'new_batch_forecast_bytes':reserved-outstanding,
            'outstanding_growth_bytes':outstanding,'missing_active_forecasts':unknown_forecasts,
            'growth_budget_bytes':growth_budget},
        'next':('Verify final player acceptance receipt and report completion' if selected<=completed else
                'Continue/review/integrate active work; reconcile unbound items; refill ready slots'),
        'limitations':'Snapshot/forecasts are point-in-time. Coordinator serializes admissions and rechecks disk. This is not an OS quota or a process/worktree launcher.'}


def scan_storage(root, max_entries=200000):
    root=Path(root).absolute(); integer(max_entries,'max_entries',1)
    result={'path':str(root),'logical_bytes':0,'files':0,'links_skipped':0,'complete':True,'errors':[]}
    pending=[root];seen=0
    while pending:
        if seen>=max_entries:
            result['complete']=False;result['errors'].append('entry_limit');break
        p=pending.pop();seen+=1
        try:
            st=p.lstat()
            if stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:
                result['links_skipped']+=1;result['complete']=False;continue
            if stat.S_ISDIR(st.st_mode):
                with os.scandir(p) as entries:
                    for e in entries:
                        if len(pending)+seen>=max_entries:
                            result['complete']=False;result['errors'].append('entry_limit');break
                        pending.append(Path(e.path))
            elif stat.S_ISREG(st.st_mode):
                result['logical_bytes']+=st.st_size;result['files']+=1
        except OSError as exc:
            result['complete']=False;result['errors'].append(type(exc).__name__)
    result['measurement']='Logical bytes only; no deletion or deduplication claim'
    return result


def packet(catalog,tid):
    by=validate_catalog(catalog);require(tid in by,'unknown_task_id')
    t=by[tid]
    return {'task':t,'calculation_requirements':[c for c in catalog.get('calculations',[]) if c['id'] in t.get('calculation_ids',[])],
        'coordinator_must_supply':['controller claim/generation','exact base and receipt reconciliation',
            'owned files and reusable slot','preregistered gates','forecast and broker reservations',
            'reviewer and integration path'],
        'worker_instruction':'Complete this bounded implementation through evidence-backed handoff. Preserve failures. No baseline changes outside approved scope. Release resources after verified drainage; no deletion of unrelated files.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,default=HERE/'monkey_completion_map.json')
    p.add_argument('--lock',type=Path,default=HERE/'APPROVED_SCOPE.json')
    p.add_argument('--approved-sha256',default=os.environ.get('CHIMERA_MONKEY_APPROVED_SHA256'),
                   help='Human-pinned public digest; never replace it with the current file digest')
    sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('validate')
    q=sub.add_parser('packet');q.add_argument('task_id')
    q=sub.add_parser('storage');q.add_argument('path',type=Path);q.add_argument('--max-entries',type=int,default=200000)
    q=sub.add_parser('plan');source=q.add_mutually_exclusive_group(required=True)
    source.add_argument('--session',type=Path);source.add_argument('--snapshot',type=Path)
    q.add_argument('--bindings',type=Path,required=True)
    q.add_argument('--harness-limit',type=int,required=True);q.add_argument('--active-subagents',type=int,required=True)
    q.add_argument('--volume-path',type=Path,required=True);q.add_argument('--include-conditional',action='store_true')
    a=p.parse_args(argv)
    try:
        catalog,integrity=verify_catalog(a.catalog,a.lock,a.approved_sha256,a.action in {'plan','packet'})
        if a.action=='validate':
            by=validate_catalog(catalog); result={'tasks':len(by),'required_default':len(selected_tasks(by)),
                'validation':'IDs and dependency graph valid; physical gates not run; deployment not performed'}
        elif a.action=='packet':result=packet(catalog,a.task_id)
        elif a.action=='storage':result=scan_storage(a.path,a.max_entries)
        else:
            envelope=fetch_snapshot(a.session) if a.session else read_json(a.snapshot)
            result=plan(catalog,envelope,read_json(a.bindings),a.harness_limit,a.active_subagents,
                        shutil.disk_usage(a.volume_path).free,a.include_conditional)
        result['scope_integrity']=integrity
        print(json.dumps(result,indent=2));return 0
    except (Refusal,OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'refused':str(exc)}),file=sys.stderr);return 2


if __name__=='__main__':
    sys.exit(main())
