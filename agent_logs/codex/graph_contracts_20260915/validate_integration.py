"""Task-local validation with preserved outputs and strictly pinned cache inputs."""
from pathlib import Path
import hashlib,importlib,json,os,shutil,subprocess,sys
tree=Path(r'E:\ChimeraWork\codex-graph-contracts-20260915')
graph=tree/'tools/creature_graph'
evidence=tree/'agent_logs/codex/graph_contracts_20260915'
sys.path.insert(0,str(graph));sys.path.insert(0,str(tree/'tools/reference_data'))
import fetch_cache
origin=Path(r'E:\ChimeraWork\slot-01\tools\reference_data\data')
pins=json.loads((tree/'tools/reference_data/data/pins.json').read_text())
cache=tree/'.tmp/pinned_reference_cache'
checked={}
for key,digest in pins.items():
    relative=key.split('::',1)[1];src=origin/'cache'/relative;data=src.read_bytes()
    assert hashlib.sha256(data).hexdigest()==digest,key
    dst=cache/relative; dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    checked[key]=digest
(evidence/'pinned_cache_inputs.json').write_text(json.dumps({'source':str(origin),'pins':checked},indent=2))
fetch_cache.CACHE_DIR=str(cache)
import acceptance
acceptance.EVIDENCE_DIR=str(evidence)
sys.argv=['acceptance.py','--offline']
result=acceptance.main()
if result: raise SystemExit(result)
# Preserve the originally committed F3 demonstration; new runs have new records.
historical='tools/creature_graph/data/graphify_demo/consumer_demo_report.json'
raw=subprocess.run(['git','-c','safe.directory='+str(tree),'-C',str(tree),'show','728e7280:'+historical],check=True,capture_output=True).stdout
(tree/historical).write_bytes(raw)
# A first and repeated invocation on the new scratch-only consumer.
import graphify_consumer as bridge
for attempt in (1,2):
    result=bridge.run_demo()
    shutil.copy2(bridge.DEMO_REPORT,evidence/f'bridge_final_{attempt}.json')
    if result: raise SystemExit(result)
# Snapshot next-action and truthful capture status; does not recapture old runs.
import build_graph,gaps
g=build_graph.build(with_reference=True)
summary={'graph_hash':g.graph_hash(),'objects':len(g.objects),'relations':len(g.relations),
         'evidence':[{'id':ev['id'],'validation':ev.get('validation'),'last_result':ev.get('last_result'),'captured':ev.get('captured'),'captured_utc':ev.get('captured_utc'),'reasons':ev.get('stale_reasons')} for ev in g.evidence_records()],
         'six_queries':gaps.run_all_six(g)}
(evidence/'graph_after.json').write_text(json.dumps(summary,indent=2))
print('FINAL_INTEGRATION_VALIDATION_PASS')
