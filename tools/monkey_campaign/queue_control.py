"""Existing coordinator's bounded-queue commands; labels are not authentication."""
import argparse
import json
from pathlib import Path
import sys
from agent_slots import Registry, DEFAULT_ROOT
from instruction_state import inspect, decode
from integrity import verify_catalog
from campaign import validate_catalog
from task_queue import publish, rework


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['status','publish','rework'])
    parser.add_argument('--arguments',type=Path)
    args=parser.parse_args()
    project=Path(__file__).resolve().parents[2]
    instructions=inspect(project)
    catalog,_=verify_catalog(project/'tools/monkey_campaign/monkey_completion_map.json',
        project/'tools/monkey_campaign/APPROVED_SCOPE.json',instructions['scope_sha256'],True)
    registry=Registry(DEFAULT_ROOT)
    if args.action=='status':
        state=registry.snapshot()
        result={'instruction_revision':instructions['revision_id'],
            'registered_agents':state['registered_agents'],
            'tasks':{k:{'state':v['state'],'agent_id':v.get('agent_id'),
                'submission':v.get('submission'),'review':v.get('review')}
                for k,v in state.get('diagnostic_claims',{}).items()},
            'commissioned_ids':list(state.get('commissioned_briefs',{})),
            'goal_complete':False,
            'next_action':'Review returned evidence and execute the first unmet native checkpoint from execution_plan.py. Publish bounded follow-up briefs here; production source/GPU tasks retain existing supervisor claims.'}
    else:
        if args.arguments is None: raise ValueError('arguments_file_required')
        with args.arguments.open('rb') as stream: raw=stream.read(65537)
        if len(raw)>65536: raise ValueError('arguments_size_limit')
        data=decode(raw)
        builtins=decode((project/'tools/monkey_campaign/EXECUTION_QUEUE.json').read_bytes())
        result=publish(registry,data,validate_catalog(catalog),[t['id'] for t in builtins['tasks']]) if args.action=='publish' else rework(registry,data)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    try: main()
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'refused':str(exc)}),file=sys.stderr);sys.exit(2)
