"""Convert probe output (.tmp/probe_results.txt) into the committed landing
scenario table (auditable JSON consumed by multidynamics_unit)."""
import json,math
from pathlib import Path
from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.coupled_scene7 import COORDINATES,ROOT

SRC=ROOT/'.tmp/probe_results.txt'
OUT=ROOT/'tools/science_funnel/validation/seven_coord_complete_20260918/landing_scenarios.json'


def bound_deg(model,name,code):
    lo,hi=model['coordinates'][name]['range_rad']
    return float((hi if code==1 else lo)*180/math.pi)


def main():
    graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
    model=graph.get('model.anatomy.macaque_arm')['physical']['model']
    scenarios=[]
    lines=[l.strip() for l in SRC.read_text(encoding='utf-8',errors='replace').splitlines() if l.strip()]
    for l in lines:
        parts=l.split()
        kind=parts[0]
        if kind=='NOLAND':
            continue # scan result; the STALL line that follows pins the pair
        fields=dict(p.split('=',1) for p in parts[1:] if '=' in p)
        stage=int(fields['stage']);side=int(fields['side']);diff=float(fields['diff'])
        coords=COORDINATES[:stage]
        if kind=='LAND':
            assert not any(s['stage']==stage and s['coord']==fields['coord'] and s['side']==side for s in scenarios),'duplicate LAND'
            enc=[int(x) for x in fields['scenario'].strip('[]').split(',')]
            # The scan always drives the target coordinate AT its own bound
            # (probe_mode's sc.targets[d]=bound) plus any reorienters.
            targets={fields['coord']:bound_deg(model,fields['coord'],side)}
            for i,c in enumerate(coords):
                if c!=fields['coord'] and enc[i]>=0:targets[c]=bound_deg(model,c,enc[i])
            scenarios.append({'stage':stage,'coord':fields['coord'],'side':side,
                              'targets':targets,'power':fields['power']=='1',
                              'load':0.0,'landed':True,'diff':diff})
        elif kind=='STALL':
            skip=diff>=1e9 # never engages its stop: Zeno-exhaustion regime, disclosed
            scenarios.append({'stage':stage,'coord':fields['coord'],'side':side,
                              'targets':{fields['coord']:bound_deg(model,fields['coord'],side)},
                              'power':True,'load':0.0,
                              'landed':False,'skip':skip,'diff':diff})
        else:
            raise SystemExit('unexpected line: '+l)
    payload={'schema':'chimera.coupled_arm7_landing_scenarios.v1',
             'note':'Pinned stop-landing scenarios for the seven-coordinate '
                    'qualification ladder (F4). landed=true entries are '
                    'verified stop landings: the wall clamp pins q within '
                    '1e-9 at a tick with a nonzero stop impulse and the '
                    'ledger closes on every tick. landed=false entries are '
                    'honestly-measured stalls: the bound is unreachable by '
                    'drive+gravity under the authored servo contract; the '
                    'verifier reproduces the stall distance deterministically. '
                    'targets are degrees; absent coordinates stay at defaults.',
             'scenarios':scenarios}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'written':str(OUT),'scenarios':len(scenarios),
                      'landed':sum(1 for s in scenarios if s['landed']),
                      'stalled':sum(1 for s in scenarios if not s['landed'])}))

if __name__=='__main__':
    main()
