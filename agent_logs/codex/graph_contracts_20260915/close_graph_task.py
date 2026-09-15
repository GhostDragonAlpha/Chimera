"""Record this new graph-contract measurement without re-capturing old runs."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
tree=Path(r'E:\ChimeraWork\codex-graph-contracts-20260915'); gd=tree/'tools/creature_graph'
evdir=tree/'agent_logs/codex/graph_contracts_20260915'
sys.path.insert(0,str(gd))
import build_graph,graphify_projection
source_files=['schema.py','store.py','build_graph.py','engine_live.py','gaps.py','graphify_projection.py','graphify_consumer.py','acceptance.py','tests/test_contracts.py']
source_hashes={p:hashlib.sha256((gd/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in source_files}
run=subprocess.run([sys.executable,'-B',str(gd/'tests/test_contracts.py')],capture_output=True)
(evdir/'contracts_recorded_measurement.log').write_bytes(run.stdout+run.stderr)
if run.returncode: raise SystemExit(run.returncode)
when=datetime.datetime.now(datetime.timezone.utc).isoformat()
g=build_graph.build(with_reference=True)
tid='work.graph_contract_repairs_20260915'; eid='ev.graph_contracts_20260915'
task={'id':tid,'kind':'work','name':'Repair graph evidence and projection contracts','status':'verified','priority':'P0','authored_priority':0,
      'physical':{'plan':'Repair D1-D9, preserve historical measurements, fail closed on identity ambiguity; qualify private Graphify consumer only.',
                  'source_hash_policy':'SHA256 of UTF-8 source bytes with CRLF normalized to LF','source_hashes':source_hashes},
      'dependencies':[],'enables':['experience.press_and_response','experience.local_withdrawal'],'evidence':[eid],
      'falsifier':{'statement':'A roadmap whose stale or ambiguous inputs pass as verified cannot reliably direct work.',
                   'acceptance_test':'tests/test_contracts.py plus offline acceptance and private consumer round trips; D9 does not infer closure from wall count.',
                   'status':'passing'},
      'notes':'Only this graph-contract repair task is completed. No native/player/production Graphify qualification is implied.'}
g.add(task)
measured={p:hashlib.sha256((evdir/p).read_bytes()).hexdigest() for p in ['contracts_recorded_measurement.log','acceptance_results.json','bridge_final_1.json','bridge_final_2.json']}
ev=g.record_evidence({'id':eid,'kind':'evidence','name':'Graph contract repair checks, isolated worktree','status':'specified','validation':'passing',
                     'deps':[tid],'captured_utc':when,'physical':{'source_hashes':source_hashes},
                     'provenance':{'evidence_directory':'agent_logs/codex/graph_contracts_20260915','artifact_sha256':measured},
                     'notes':'19 positive contract tests; 25 offline acceptance checks with live block NOT_TESTED; two private Graphify seven-check round trips. Historical captures were not repaired retroactively.'})
g.sync_dependencies()
assert not g.stale_evidence(eid)
for name,record in [('requirements_tasks.json',task),('mechanisms.json',ev)]:
    p=gd/'data/authored'/name; records=json.loads(p.read_text()); assert not any(o['id']==record['id'] for o in records)
    records.append(record); p.write_text(json.dumps(records,indent=1,ensure_ascii=False)+'\n')
g=build_graph.build(with_reference=True);g.save();graphify_projection.export(g)
assert not g.stale_evidence(eid)
# Discard only semantically identical importer reordering caused by the test.
for relative in ['tools/reference_data/data/import_provenance.json','tools/reference_data/data/pins.json','tools/reference_data/data/reference_store.json']:
    raw=subprocess.run(['git','-c','safe.directory='+str(tree),'-C',str(tree),'show','HEAD:'+relative],capture_output=True,check=True).stdout
    path=tree/relative;assert json.loads(path.read_bytes())==json.loads(raw),relative;path.write_bytes(raw)
import gaps,graphify_consumer as consumer
assert consumer.run_demo()==0
raw=Path(consumer.DEMO_REPORT).read_bytes();(evdir/'bridge_final_authored_graph.json').write_bytes(raw)
(evdir/'final_graph_state.json').write_text(json.dumps({'objects':len(g.objects),'relations':len(g.relations),'graph_hash':g.graph_hash(),
    'new_evidence':ev,'historical_validation':[{'id':e['id'],'validation':e.get('validation'),'last_result':e.get('last_result')} for e in g.evidence_records() if e['id']!=eid],
    'six_queries':gaps.run_all_six(g)},indent=2))
print('RECORDED_NEW_MEASUREMENT',tid,eid,len(g.objects),len(g.relations),gaps.q_next_ready_task(g)['next']['id'])
