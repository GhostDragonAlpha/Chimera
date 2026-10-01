"""Write the S6 oracle fixture: the generated .tmp copy and the committed
audit copy (seed + permutation pinned for replay). Run from the repo root:
    python -B -m tools.science_funnel.tests.build_oracle7
"""
import json
from pathlib import Path
from tools.science_funnel.common import canonical
from tools.science_funnel.tests.test_coupled_arm7 import build_cases,COMMITTED,GENERATED

def main():
    cases=build_cases()
    GENERATED.parent.mkdir(parents=True,exist_ok=True)
    COMMITTED.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(cases,indent=1,allow_nan=False)+'\n'
    GENERATED.write_text(payload,encoding='utf-8')
    COMMITTED.write_text(payload,encoding='utf-8')
    print(json.dumps({'generated':str(GENERATED),'committed':str(COMMITTED),
                      'stages':[s['n'] for s in cases['stages']],
                      'poses_per_stage':cases['poses_per_stage']}))

if __name__=='__main__':
    main()
