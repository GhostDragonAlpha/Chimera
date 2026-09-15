"""Positive contracts: a passing test means repaired behavior, not a live defect.
Run: python -B tools/creature_graph/tests/test_contracts.py
Only temporary fixture paths and in-memory stores are written.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_graph
import engine_live
import gaps
import graphify_consumer as consumer
import graphify_projection as projection
import schema
from store import CreatureGraph, content_version

def obj(oid, kind='region', **extra):
    return dict(id=oid, kind=kind, name=oid, status='specified', priority='P0', **extra)

def graph():
    g=CreatureGraph(); g.meta['schema_version']=schema.SCHEMA_VERSION
    g.add(obj('param','parameter',value=1,units='Pa',source='fixture',applicability='fixture'))
    g.add(obj('sensor','sensor')); g.add(obj('path','pathway')); g.add(obj('other'))
    g.relate('sensor','carries_signal_to','path')
    g.record_evidence(obj('ev','evidence',validation='passing',deps=['param','sensor','path'],captured_utc='2026-09-15T13:47:00Z'))
    return g

class Contracts(unittest.TestCase):
    def test_D1_selected_parameter_fields_stale(self):
        for field,value in [('value',2),('units','kPa'),('source','new source'),('applicability','new conditions')]:
            with self.subTest(field=field):
                g=graph(); before=content_version(g.get('param')); g.get('param')[field]=value
                self.assertNotEqual(before,content_version(g.get('param')))
                self.assertEqual(g.refresh_validation(),['ev'])
                self.assertEqual(g.get('ev')['last_result'],'passing')

    def test_D1_unaffected_hash_and_cosmetic_changes(self):
        g=graph(); o=g.get('sensor')
        old={k:o[k] for k in ('physical','spatial','geometry','status','attachments','unknowns') if k in o}
        self.assertEqual(content_version(o),hashlib.sha256(json.dumps(old,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16])
        g.get('param')['name']='readable name'; g.get('sensor')['notes']='annotation'
        self.assertEqual(g.refresh_validation(),[])

    def test_D2_relation_mutations_stale(self):
        for mutation in ('remove','reverse','type','add_parallel'):
            with self.subTest(mutation=mutation):
                g=graph()
                if mutation=='remove': g.relations.clear()
                elif mutation=='reverse': g.relations[0]['src'],g.relations[0]['dst']='path','sensor'
                elif mutation=='type': g.relations[0]['rel']='transmits_force_to'
                else: g.relate('sensor','carries_signal_to','path')
                self.assertEqual(g.refresh_validation(),['ev'])

    def test_D2_unrelated_relation_and_reordering_do_not_stale(self):
        g=graph(); g.add(obj('other2')); g.relate('other','inside','other2')
        g.relations.reverse()
        self.assertEqual(g.refresh_validation(),[])
        h=CreatureGraph()
        for o in g.objects.values(): h.add(copy.deepcopy(o))
        for r in reversed(g.relations): h.relate(r['src'],r['rel'],r['dst'],r['note'])
        self.assertEqual(g.relation_capture(g.get('ev')['deps']),h.relation_capture(h.get('ev')['deps']))

    def test_D3_empty_partial_and_changed_scope_are_unknown(self):
        for mutation in ('empty','partial','contract','scope','relations','time'):
            with self.subTest(mutation=mutation):
                g=graph(); ev=g.get('ev')
                if mutation=='empty': ev['captured']={}
                elif mutation=='partial': del ev['captured']['sensor']
                elif mutation=='contract': ev.pop('capture_contract')
                elif mutation=='scope': ev['deps'].append('other')
                elif mutation=='relations': ev.pop('captured_relations')
                else: ev.pop('captured_utc')
                self.assertEqual(g.refresh_validation(),['ev']); self.assertEqual(ev['last_result'],'passing')

    def test_D3_fully_captured_pass_and_failure_stay_current(self):
        g=graph(); self.assertEqual(g.refresh_validation(),[])
        g.get('ev')['validation']='failing'; self.assertEqual(g.refresh_validation(),[])
        g.get('param')['value']=2; g.refresh_validation()
        self.assertEqual(g.get('ev')['last_result'],'failing')

    def test_record_cannot_overwrite_history(self):
        g=graph(); old=copy.deepcopy(g.get('ev'))
        with self.assertRaises(ValueError): g.record_evidence(old)
        self.assertEqual(g.get('ev'),old)

    def test_D4_build_keeps_measurement_capture_and_time(self):
        g=graph(); historic=copy.deepcopy(g.get('ev'))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            for name in build_graph.AUTHORED_FILES: (p/name).write_text('[]')
            def write():
                (p/'mechanisms.json').write_text(json.dumps(list(g.objects.values())))
                (p/'relations.json').write_text(json.dumps(g.relations))
            write()
            with patch.object(build_graph,'AUTHORED_DIR',td):
                a=build_graph.build(); b=build_graph.build()
                self.assertEqual(a.graph_hash(),b.graph_hash()); self.assertEqual(a.get('ev'),historic)
                g.get('param')['value']=2; write()
                c=build_graph.build(); d=build_graph.build()
            self.assertEqual(c.graph_hash(),d.graph_hash())
            self.assertEqual(c.get('ev')['validation'],'stale')
            for key in ('captured','captured_utc','captured_relations'): self.assertEqual(c.get('ev')[key],historic[key])

    def test_D5_collision_refuses_before_overwrite(self):
        g=graph(); g.add(obj('probe/a.b')); g.add(obj('probe_a_b'))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'projection.json'; p.write_text('preserve')
            with patch.object(projection,'PROJ_DIR',td),patch.object(projection,'PROJ_PATH',str(p)):
                with self.assertRaisesRegex(ValueError,'collision'): projection.export(g)
            self.assertEqual(p.read_text(),'preserve')

    def test_D5_existing_map_and_native_rids_preserved(self):
        g=graph(); g.relate('sensor','carries_signal_to','path')
        p=projection.make_projection(g)
        self.assertEqual(p['id_map'],{oid:projection._sanitize(oid) for oid in g.objects})
        self.assertEqual({e['rid'] for e in p['edges']},{e['rid'] for e in g.relations})
        self.assertTrue(all(e['key']==e['rid'] for e in p['edges']))

    def test_D6_supported_roundtrip_and_foreign_refusal(self):
        g=graph()
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'store.json'; g.save(str(p)); raw=json.loads(p.read_text())
            for version in ('2.0.0','1.0.0-unversioned'):
                raw['schema_version']=version; p.write_text(json.dumps(raw))
                self.assertEqual(CreatureGraph.load(str(p)).graph_hash(),g.graph_hash())
            raw.pop('schema_version'); p.write_text(json.dumps(raw))
            self.assertEqual(CreatureGraph.load(str(p)).graph_hash(),g.graph_hash())
            raw['schema_version']='future'; p.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError,'future'): CreatureGraph.load(str(p))

    def test_D7_ambiguous_matches_never_assign_or_double_book(self):
        import test_d7_greedy_cell_matching as fixture
        g=CreatureGraph()
        for o in fixture.INSTANCES: g.add(copy.deepcopy(o))
        tick={'cells':copy.deepcopy(fixture.CELLS),'n_cells':2,'conserve_pct':0,'sealed':True,'V_whole':1}
        for cells in (tick['cells'],list(reversed(tick['cells'])),tick['cells'][:1]):
            tick['cells']=cells
            rows=engine_live.map_cells_to_instances(g,tick)
            self.assertTrue(all(r['engine_cell_index'] is None and 'ambiguous' in r['match'] for r in rows))
            self.assertTrue(any('ambiguous' in c['detail'] for c in engine_live.cross_check(g,tick)['checks']))

    def test_D7_distinct_bands_still_match(self):
        import test_d7_greedy_cell_matching as fixture
        g=CreatureGraph(); cells=copy.deepcopy(fixture.CELLS)
        for i,o in enumerate(fixture.INSTANCES):
            o=copy.deepcopy(o); o['spatial']['band_y']=[i,i+1]; g.add(o)
            cells[i].update(ylo=i,yhi=i+1,v0=o['spatial']['v0_m3'])
        tick={'cells':cells,'n_cells':2,'conserve_pct':0,'sealed':True,'V_whole':sum(c['v0'] for c in cells)}
        self.assertTrue(engine_live.cross_check(g,tick)['pass'])
        self.assertEqual([r['engine_cell_index'] for r in engine_live.map_cells_to_instances(g,tick)],[0,1])

    def test_D8_zero_and_missing_nonfinite(self):
        import test_d8_conservation_falsy_zero as fixture
        for value,expected in [(0.0,True),(1e-6,True),(None,False),(float('nan'),False),(float('inf'),False),('bad',False),(True,False)]:
            with self.subTest(value=value):
                checks=engine_live.cross_check(CreatureGraph(),fixture._tick(value))['checks']
                c=next(c for c in checks if c['check']=='conservation ~0')
                self.assertEqual(c['ok'],expected)
                if value is None: self.assertIn('missing',c['detail'])

    def test_D9_duplicate_wall_is_one_support(self):
        import test_d9_duplicate_boundary_closure as fixture
        g=CreatureGraph()
        for o in (fixture.WALL,fixture.COMPARTMENT,fixture.REGION_SOLO,fixture.REGION_OUTSIDE): g.add(copy.deepcopy(o))
        for _ in range(2): g.relate(fixture.WALL['id'],'bounds_region','region.solo')
        r=gaps.q_unsupported_boundaries(g)[0]
        self.assertEqual(len(r['bounding_membranes']),1); self.assertEqual(r['distinct_supported_membranes'],1)
        self.assertIsNone(r['closed_by_built_walls']); self.assertIn('closure unverified',r['verdict'])
        wall=copy.deepcopy(fixture.WALL); wall['id']='second.wall'; g.add(wall); g.relate(wall['id'],'bounds_region','region.solo')
        r=gaps.q_unsupported_boundaries(g)[0]
        self.assertEqual(r['distinct_supported_membranes'],2)
        self.assertIsNone(r['closed_by_built_walls']); self.assertIn('closure unverified',r['verdict'])

    def test_risk_query_discloses_no_evidence_and_incomplete_captures(self):
        g=CreatureGraph(); g.add(obj('x')); r=gaps.q_evidence_at_risk(g,'x')
        self.assertEqual(r['evidence_records_considered'],0); self.assertEqual(r['coverage'],'no evidence')
        g=graph(); g.get('ev')['captured']={}; r=gaps.q_evidence_at_risk(g,'param')
        self.assertEqual(r['coverage'],'incomplete'); self.assertEqual(len(r['unverifiable_captures']),1)

    def test_bridge_refuses_tamper_before_any_write(self):
        g=graph(); p=projection.make_projection(g)
        class NoWrite:
            def load_dna_graph(self): raise AssertionError('consumer read before validation')
        for edit in ('label','rid','reverse','map','graph_hash','node_count'):
            with self.subTest(edit=edit):
                q=copy.deepcopy(p)
                if edit=='label': q['nodes'][0]['label']='tampered'
                elif edit=='rid': q['edges'][0]['rid']='wrong'
                elif edit=='reverse': q['edges'][0]['source'],q['edges'][0]['target']=q['edges'][0]['target'],q['edges'][0]['source']
                elif edit=='map': q['nodes'][0]['_authored_id']='wrong'
                elif edit=='graph_hash': q['graph']['graph_hash']='old'
                else: q['nodes'].pop()
                with self.assertRaises(consumer.ProjectionRejected): consumer.ingest_projection(NoWrite(),q,g)

    def test_bridge_refuses_foreign_environment(self):
        with patch.dict(os.environ,{'CHIMERA_DNA_DB':'E:/not-the-demo.db'}):
            with self.assertRaisesRegex(RuntimeError,'scratch-only'): consumer.pin_scratch_store()

    def test_bridge_preserves_foreign_objects_and_refuses_id_overlap(self):
        class MemoryStore:
            def __init__(self): self.g={'nodes':[{'id':'foreign','origin':'other'}],'edges':[]}; self.writes=0
            def load_dna_graph(self): return copy.deepcopy(self.g)
            def save_dna_graph(self,g): self.g=g; self.writes+=1
        g=graph(); p=projection.make_projection(g); mem=MemoryStore()
        consumer.ingest_projection(mem,p,g); consumer.ingest_projection(mem,p,g)
        self.assertEqual(len(mem.g['nodes']),len(g.objects)+1)
        self.assertEqual(mem.g['nodes'][0]['id'],'foreign')
        mem.g['nodes'][0]['id']=p['nodes'][0]['id']; before=mem.writes
        with self.assertRaises(consumer.ProjectionRejected): consumer.ingest_projection(mem,p,g)
        self.assertEqual(mem.writes,before)

if __name__=='__main__': unittest.main(verbosity=2)
