from pathlib import Path
import hashlib,json,shutil,subprocess,sys
tree=Path(r'E:\ChimeraWork\codex-graph-contracts-20260915')
gd=tree/'tools/creature_graph'; ev=tree/'agent_logs/codex/graph_contracts_20260915';bench=Path(__file__).parent
def git(*args): return subprocess.run(['git','-c','safe.directory='+str(tree),'-C',str(tree),*args],check=True,capture_output=True).stdout
for name in ['REPORT.md','KILO_HANDOFF.md','validate_integration.py','close_graph_task.py','finalize_evidence.py']:
    shutil.copy2(bench/name,ev/name)
# Existing authored records are immutable; this repair only appends two records.
for name in ('mechanisms.json','requirements_tasks.json'):
    relative='tools/creature_graph/data/authored/'+name
    old=json.loads(git('show','728e7280:'+relative));now=json.loads((tree/relative).read_bytes())
    byid={o['id']:o for o in now}
    assert all(byid[o['id']]==o for o in old),name
# Keep saved diagnostic artifacts; move only our three untracked first-demo outputs.
archive=tree/'.tmp/graph_contract_first_bridge'; archive.mkdir(exist_ok=True)
for name in ('creature_graph_projection.json','dna_consumer_demo.db','dna_consumer_demo_snapshot.json'):
    src=gd/'data/graphify_demo'/name;dst=archive/name
    if src.exists():
        assert not dst.exists(); src.rename(dst)
attr=tree/'.gitattributes';s=attr.read_text();rule='agent_logs/codex/graph_contracts_20260915/** -text'
if rule not in s: attr.write_text(s+'\n# Immutable graph-contract measurement bytes across Windows checkouts.\n'+rule+'\n')
sys.path.insert(0,str(gd));import build_graph,graphify_consumer,graphify_projection
g=build_graph.build(with_reference=True)
assert len(g.objects)==1488 and len(g.relations)==144
assert not g.stale_evidence('ev.graph_contracts_20260915')
captured=g.get('work.graph_contract_repairs_20260915')['physical']['source_hashes']
for name,digest in captured.items():
    assert hashlib.sha256((gd/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,name
proj=json.loads((gd/'data/graphify_projection/creature_graph_projection.json').read_bytes())
graphify_consumer.validate_projection(proj,g)
(ev/'final_checks.json').write_text(json.dumps({'historical_authored_records_unchanged':True,'current_source_matches_new_capture':True,'committed_projection_matches_graph':True,'graph_hash':g.graph_hash(),'objects':len(g.objects),'relations':len(g.relations),'native_source_diff_since_a12bfbcc':git('diff','a12bfbcc','--','ChimeraEngine/engine').decode()},indent=2))
assert not git('diff','a12bfbcc','--','ChimeraEngine/engine')
print('FINAL_CHECKS_PASS')
