#!/usr/bin/env python3
"""Read-only roadmap browser. No claims, writes, publication, or gate execution.

Optional state JSON: {"tasks": {"GOV-01": {"status": "ACCEPTED",
"evidence": ["repo-path-and-commit-or-review-reference"]}}}.
Accepted means accepted at the scoped prerequisite level by the coordinator;
this tool does not independently certify evidence or available resources.
"""
import argparse
import json
from pathlib import Path
import sys

STATES = {'PROPOSED','READY','CLAIMED','RUNNING','BLOCKED','REVIEW','ACCEPTED','SUPERSEDED','RETIRED'}
DEFAULT = Path(__file__).resolve().parents[1] / 'docs/roadmap/holodeck_tasks.json'

def validate(data):
    errors=[]
    if data.get('schema') != 'chimera-holodeck-roadmap-v1': errors.append('Unsupported schema')
    tasks=data.get('tasks',[]); by={}
    domains={d['id'] for d in data.get('domains',[])}
    for t in tasks:
        tid=t.get('id')
        if not isinstance(tid,str) or not tid: errors.append('Missing task ID'); continue
        if tid in by: errors.append('Duplicate task ID: '+tid)
        by[tid]=t
        for k in ('title','statement','prediction','falsifier','threshold_policy','write_scope','dyad'):
            if not isinstance(t.get(k),str) or not t[k].strip(): errors.append(f'{tid}: empty {k}')
        if t.get('domain') not in domains: errors.append(f'{tid}: unknown domain')
        if t.get('status') not in STATES: errors.append(f'{tid}: invalid status')
        if t.get('status')=='ACCEPTED' and not t.get('evidence'): errors.append(f'{tid}: accepted without evidence')
    for tid,t in by.items():
        for dep in t.get('depends_on',[]):
            if dep not in by: errors.append(f'{tid}: unknown dependency {dep}')
    seen=set(); active=set()
    def visit(tid):
        if tid in active: errors.append('Dependency cycle at '+tid); return
        if tid in seen:return
        active.add(tid)
        for dep in by[tid].get('depends_on',[]):
            if dep in by:visit(dep)
        active.remove(tid);seen.add(tid)
    for tid in by: visit(tid)
    return errors

def load_state(path,by):
    raw=json.loads(Path(path).read_text(encoding='utf-8')) if path else {'tasks':{}}
    states=raw.get('tasks')
    if not isinstance(states,dict): raise ValueError('state.tasks must be a mapping')
    for tid,entry in states.items():
        if tid not in by: raise ValueError('Unknown state ID '+tid)
        if not isinstance(entry,dict) or entry.get('status') not in STATES:
            raise ValueError('Invalid state entry '+tid)
        if entry['status']=='ACCEPTED':
            e=entry.get('evidence')
            if not isinstance(e,list) or not e or any(not isinstance(x,str) or not x.strip() for x in e):
                raise ValueError('Accepted prerequisite lacks evidence references: '+tid)
    return states

def packet(t,data):
    deps=', '.join(t['depends_on']) or 'none'
    return f'''PROPOSED AGENT PACKET — {t['id']}: {t['title']}
This proposal is not a claim or new authorization. Preserve all active tasks.
Inspected catalogue snapshot: {data['inspected_commit']}
Reconcile the actual source head and prerequisite evidence before implementation.
Minimum candidate dependencies: {deps}
Scope: {t['write_scope']}
Concepts: {t['mathematics']}

STATEMENT / DELIVERABLE: {t['statement']}
PREDICTION: {t['prediction']}
FALSIFIER: {t['falsifier']}
Threshold policy: {t['threshold_policy']}

Own the selected milestone end to end: inspect existing evidence, derive the
chosen law, preregister bounds and controls, implement within reserved paths,
build, test, diagnose, repair and rerun affected gates. Do not replace valid
existing work or count a self-consistency test as an independent oracle.
Preserve failed runs and report each actual evidence class separately.

DYAD: {t['dyad']}

Read docs/THE_MASTER_LIST.md and relevant law/protocol documents. Reserve
write scope and device access through the controller (task claim, scopes,
resources); no work in other actors' files. Use isolated checkouts and
git -C <explicit checkout>. No master push, force-push, protected
engine/build/ writes or control of Alan's live engine. Workers push their own
task-branch PRs targeting astra/gait-capture; only the slot-1 lead carries
reviewed PRs through authorized integration. No installations, external
actions or physical device control are granted by this packet. Python is not
the per-frame physical runtime. Human acceptance must come from the human.

Finish independent work if one portion is blocked. Return concrete files,
commands, actual test outcomes, source/artifact identity, limitations and
integration recommendations. After completion, continue other authorized
work or report an exact remaining blocker; do not wait idle for relay.
'''

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,default=DEFAULT)
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('validate');sub.add_parser('summary');sub.add_parser('render-book')
    q=sub.add_parser('search');q.add_argument('term')
    for name in ('show','packet'):
        q=sub.add_parser(name);q.add_argument('id')
    q=sub.add_parser('ready');q.add_argument('--state',type=Path)
    a=p.parse_args(argv)
    try:
        data=json.loads(a.catalog.read_text(encoding='utf-8'))
        errors=validate(data)
        if errors:
            print('\n'.join(errors),file=sys.stderr);return 2
        by={t['id']:t for t in data['tasks']}
        if a.cmd=='validate':
            print(f'VALID: {len(by)} task IDs; {len(data["domains"])} domains; dependency DAG; required fields. Physical gates NOT EXECUTED.')
        elif a.cmd=='render-book':
            bookpath=a.catalog.parent.parent / 'THE_HOLODECK_BLUEPRINT.md'
            book=bookpath.read_text(encoding='utf-8')
            first='\n### '+data['domains'][0]['id']+' — '
            prefix=book[:book.index(first)]
            suffix=book[book.index('\n## 11. Adoption and first execution'):]
            body=''
            for d in data['domains']:
                body+=f"\n### {d['id']} — {d['title']}\n\nDomain class: **{d['kind']}**. Candidate prerequisites: "+(', '.join(d['prerequisites']) or 'none; project-control entry point')+'.\n'
                for t in data['tasks']:
                    if t['domain']!=d['id']:continue
                    body+=f"\n#### {t['id']} · {t['title']}\n\n"
                    body+=f"**Mathematics/concepts:** {t['mathematics']}.\n\n"
                    body+='**Depends on:** '+(', '.join(t['depends_on']) or 'none')+'. **State:** proposed; not a reassignment.\n\n'
                    body+=f"**STATEMENT / deliverable:** {t['statement']}.\n\n**PREDICTION:** {t['prediction']}.\n\n**FALSIFIER:** {t['falsifier']}.\n"
            sys.stdout.write(prefix+body+suffix)
        elif a.cmd=='summary':
            print('REVIEW DRAFT. No new assignment or acceptance implied.')
            for d in data['domains']:
                n=sum(t['domain']==d['id'] for t in by.values())
                print(f'{d["id"]:7} {n:3}  {d["kind"]:12} {d["title"]}')
        elif a.cmd=='search':
            needle=a.term.casefold()
            for t in by.values():
                if needle in ' '.join(str(t[k]) for k in ('id','title','mathematics','statement','prediction','falsifier')).casefold():
                    print(t['id']+'  '+t['title'])
        elif a.cmd in ('show','packet'):
            t=by.get(a.id)
            if t is None:raise ValueError('Unknown task ID '+a.id)
            print(json.dumps(t,indent=2,ensure_ascii=False) if a.cmd=='show' else packet(t,data))
        elif a.cmd=='ready':
            states=load_state(a.state,by)
            print('ELIGIBLE PLANNING CANDIDATES ONLY: coordinator must check scopes, resources, prerequisite class and current claims.')
            for t in by.values():
                status=states.get(t['id'],{}).get('status',t['status'])
                if status not in ('PROPOSED','READY'):continue
                if all(states.get(d,{}).get('status')=='ACCEPTED' for d in t['depends_on']):
                    print(t['id']+'  '+t['title'])
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('REFUSED: '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
