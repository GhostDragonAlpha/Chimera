"""Preregistered adverse controls plus independent unit/geometric/physical oracles."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import tempfile
import unittest

from tools.science_funnel.common import Refusal, canonical, digest, loads, sha
from tools.science_funnel.pipeline import ingest, verify
from tools.science_funnel.graph import propose, graph_from
from tools.science_funnel.units import convert
from tools.science_funnel.adapters import two_point_frame
from tools.science_funnel.reductions import LAWS, reduce
from tools.science_funnel.__main__ import main
from tools.creature_graph.store import CreatureGraph


class FunnelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.out = self.root / 'bundles'

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self, raw, adapter='measurements_csv', **fields):
        (self.root/'input').write_bytes(raw)
        self.m = {'schema_version': '1.0.0', 'adapter': adapter,
                  'source': {'id': 'synthetic.fixture', 'release': '1',
                             'license': 'CC0', 'url': 'local:synthetic-not-scientific-data'},
                  'artifacts': [{'id': 'input', 'path': 'input', 'sha256': sha(raw)}],
                  **fields}
        return self.save_manifest()

    def save_manifest(self):
        path = self.root / 'manifest.json'
        path.write_bytes(canonical(self.m))
        return path

    def csv(self, rows='a,fixture,pressure,0,Pa\n', **fields):
        return self.manifest(('id,subject,quantity,value,unit\n' + rows).encode(), **fields)

    def run_intake(self, path):
        bundle = ingest(path, self.out)
        return bundle, verify(bundle)

    def test_zero_preserved_and_no_promotion(self):
        bundle, data = self.run_intake(self.csv())
        record = data['records'][0]
        self.assertEqual(record['payload']['value_si'], 0)
        self.assertFalse(record['runtime_ready'])
        graph = CreatureGraph()
        original = graph.graph_hash()
        patch = propose(bundle, graph)
        self.assertEqual(graph.graph_hash(), original)
        self.assertTrue(all(o['status'] == 'extracted' for o in patch['payload']['objects']))
        self.assertEqual(len(patch['payload']['relations']), 1)

    def test_affine_temperature_uncertainty(self):
        v = convert(0, 'degC', 'temperature', .5)
        self.assertEqual(v['value_si'], 273.15)
        self.assertEqual(v['uncertainty_si'], .5)

    def test_units_and_semantics_refused(self):
        for args in [(1, 'N', 'pressure'), (1, 'banana', 'mass'),
                     (1, 'J', 'torque'), (1, '1', 'angle'), (1, 'rad', 'strain')]:
            with self.subTest(args=args), self.assertRaises(Refusal):
                convert(*args)

    def test_nonfinite_refused(self):
        for value in ('nan', 'inf', float('nan'), True):
            with self.subTest(value=value), self.assertRaises(Refusal):
                convert(value, 'Pa', 'pressure')
        with self.assertRaises(Refusal):
            loads('{"x":1e999}')

    def test_duplicate_json_refused(self):
        with self.assertRaisesRegex(Refusal, 'duplicate_json_key'):
            loads('{"a":1,"a":2}')

    def test_missing_pin_refused(self):
        self.csv()
        self.m['artifacts'][0].pop('sha256')
        with self.assertRaisesRegex(Refusal, 'artifact_pin_required'):
            ingest(self.save_manifest(), self.out)
        self.assertFalse(self.out.exists())

    def test_source_drift_refused_before_publish(self):
        path = self.csv()
        (self.root/'input').write_bytes(b'changed')
        with self.assertRaisesRegex(Refusal, 'pin_drift'):
            ingest(path, self.out)
        self.assertFalse(self.out.exists())

    def test_nested_scientific_assertion_changes_evidence_version(self):
        from tools.creature_graph.store import content_version
        bundle, _ = self.run_intake(self.csv())
        node = propose(bundle, CreatureGraph())['payload']['objects'][1]
        before = content_version(node)
        changed = copy.deepcopy(node)
        changed['science_funnel']['payload']['quantity'] = 'young_modulus'
        self.assertNotEqual(content_version(changed), before)

    def test_future_schema_refused(self):
        self.csv()
        self.m['schema_version'] = '100.0.0'
        with self.assertRaisesRegex(Refusal, 'schema_unsupported'):
            ingest(self.save_manifest(), self.out)

    def test_path_escape_refused(self):
        self.csv()
        self.m['artifacts'][0]['path'] = '../escape'
        with self.assertRaisesRegex(Refusal, 'path_escape'):
            ingest(self.save_manifest(), self.out)

    def test_empty_capture_quarantined(self):
        _, data = self.run_intake(self.csv(''))
        self.assertFalse(data['records'])
        self.assertEqual(data['quarantine'][0]['refusal']['code'], 'empty_capture')

    def test_partial_capture_preserves_good_and_bad(self):
        _, data = self.run_intake(self.csv('a,fixture,pressure,1,Pa\nb,fixture,pressure,2,kg\n'))
        self.assertEqual(len(data['records']), 1)
        self.assertEqual(data['quarantine'][0]['refusal']['code'], 'unit_dimension_mismatch')

    def test_duplicate_ids_never_greedily_selected(self):
        _, data = self.run_intake(self.csv('a,one,pressure,1,Pa\na,two,pressure,2,Pa\n'))
        self.assertFalse(data['records'])
        self.assertEqual(data['quarantine'][0]['refusal']['code'], 'duplicate_source_identity')
        self.assertEqual(len(data['quarantine'][0]['records']), 2)

    def test_explicit_database_column_map(self):
        path = self.manifest(b'row,spec,property,reading,units,protocol\nx,polymer,E,3,MPa,static\n',
                             columns={'id': 'row', 'subject': 'spec', 'quantity': 'property',
                                      'value': 'reading', 'unit': 'units'},
                             quantity_map={'E': 'young_modulus'}, condition_columns={'loading': 'protocol'})
        _, data = self.run_intake(path)
        value = data['records'][0]['payload']
        self.assertEqual(value['value_si'], 3_000_000)
        self.assertEqual(value['conditions']['loading'], 'static')

    def test_parallel_identical_imports_are_idempotent(self):
        path = self.csv()
        with ThreadPoolExecutor(max_workers=4) as pool:
            paths = list(pool.map(lambda _: ingest(path, self.out), range(4)))
        self.assertEqual(len(set(paths)), 1)
        self.assertEqual(len(list(self.out.iterdir())), 1)
        verify(paths[0])

    def test_source_versions_coexist(self):
        path = self.csv()
        first, old = self.run_intake(path)
        self.m['source']['release'] = '2'
        second, new = self.run_intake(self.save_manifest())
        self.assertNotEqual(first, second)
        self.assertNotEqual(old['records'][0]['id'], new['records'][0]['id'])
        self.assertEqual(verify(first), old)

    def test_reformatted_manifest_cannot_collide_graph_provenance(self):
        path = self.csv()
        first, _ = self.run_intake(path)
        path.write_text(json.dumps(self.m, indent=2), encoding='utf-8')
        second, _ = self.run_intake(path)
        graph = CreatureGraph()
        patch1 = propose(first, graph)
        for obj in patch1['payload']['objects']:
            graph.add(obj)
        for edge in patch1['payload']['relations']:
            graph.relate(**edge)
        patch2 = propose(second, graph)
        old_ids = {o['id'] for o in patch1['payload']['objects']}
        new_ids = {o['id'] for o in patch2['payload']['objects']}
        self.assertFalse(old_ids & new_ids)

    def test_blank_uncertainty_means_unknown(self):
        path = self.manifest(b'id,subject,quantity,value,unit,uncertainty\na,s,pressure,1,Pa,\n')
        _, data = self.run_intake(path)
        self.assertIsNone(data['records'][0]['payload']['uncertainty_si'])

    def test_tampered_bundle_refused(self):
        bundle, _ = self.run_intake(self.csv())
        (bundle/'records.json').write_bytes(b'[]')
        with self.assertRaisesRegex(Refusal, 'bundle_bytes_changed'):
            verify(bundle)

    def test_forged_output_and_rehashed_receipt_still_fails_replay(self):
        bundle, data = self.run_intake(self.csv())
        records = data['records']
        records[0]['payload']['value_si'] = 123
        (bundle/'records.json').write_bytes(canonical(records))
        receipt = data['receipt']
        receipt['files']['records.json'] = sha(canonical(records))
        receipt['bundle_id'] = digest({k: v for k, v in receipt.items() if k != 'bundle_id'})
        (bundle/'receipt.json').write_bytes(canonical(receipt))
        renamed = bundle.with_name(receipt['bundle_id'])
        bundle.rename(renamed)
        with self.assertRaisesRegex(Refusal, 'intake_replay_mismatch'):
            verify(renamed)

    def test_obo_uses_existing_parser_without_equivalence(self):
        _, data = self.run_intake(self.manifest(b'format-version: 1.2\n[Term]\nid: X:1\nname: femur\nis_a: X:0\n', 'uberon_obo'))
        record = data['records'][0]
        self.assertEqual(record['payload']['is_a'], ['X:0'])
        self.assertFalse(record['runtime_ready'])

    def test_ro_uses_existing_parser(self):
        raw = b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"><rdf:Description rdf:about="http://purl.obolibrary.org/obo/BFO_0000050"><rdfs:label>part of</rdfs:label></rdf:Description></rdf:RDF>'
        _, data = self.run_intake(self.manifest(raw, 'ro_owl'))
        self.assertEqual(data['records'][0]['payload']['short'], 'part_of')

    def test_ontology_relations_are_queryable_and_missing_targets_explicit(self):
        raw = b'[Term]\nid: X:1\nname: one\nis_a: X:0\nrelationship: part_of X:9\n[Term]\nid: X:0\nname: zero\n'
        bundle, _ = self.run_intake(self.manifest(raw, 'uberon_obo'))
        patch = propose(bundle, CreatureGraph())
        claims = [o for o in patch['payload']['objects'] if o.get('mapping_type') == 'source_relation']
        self.assertEqual(len(claims), 2)
        parent = next(o for o in claims if o['science_funnel']['predicate'] == 'is_a')
        self.assertTrue(parent['science_funnel']['object'])
        missing = next(o for o in claims if o['science_funnel']['predicate'] == 'part_of')
        self.assertEqual(missing['unknowns'], ['relation_target_outside_intake:X:9'])
        self.assertTrue(all(e['rel'] == 'derived_from' for e in patch['payload']['relations']))

    def test_ontology_reimport_after_json_storage_is_idempotent(self):
        raw = b'[Term]\nid: X:1\nname: one\nrelationship: part_of X:0\n[Term]\nid: X:0\nname: zero\n'
        bundle, _ = self.run_intake(self.manifest(raw, 'uberon_obo'))
        graph = CreatureGraph()
        patch = propose(bundle, graph)
        for obj in patch['payload']['objects']:
            graph.add(obj)
        for edge in patch['payload']['relations']:
            graph.relate(**edge)
        path = self.root/'stored.json'
        graph.save(str(path))
        restored = graph_from(path)
        replay = propose(bundle, restored)
        self.assertEqual(replay['metadata']['candidate_graph_hash'], graph.graph_hash())

    def test_qudt_definition_not_executable_conversion(self):
        _, data = self.run_intake(self.manifest(b'unit:PA\n rdfs:label "pascal" ;\n qudt:conversionMultiplier "1.0" ;\n', 'qudt_ttl'))
        self.assertEqual(data['records'][0]['external_id'], 'unit:PA')
        self.assertIn('conversion_offset_not_projected', data['records'][0]['unknowns'])

    def test_opensim_model_definition_not_executed(self):
        raw = b'<OpenSimDocument Version="40000"><Model name="test"><Thelen2003Muscle name="m"><max_isometric_force>42</max_isometric_force></Thelen2003Muscle></Model></OpenSimDocument>'
        _, data = self.run_intake(self.manifest(raw, 'opensim_xml'))
        self.assertEqual(len(data['records']), 2)
        measurement = next(r for r in data['records'] if r['record_type'] == 'measurement')
        self.assertEqual(measurement['payload']['value_si'], 42)

    def test_xml_entity_rejected(self):
        _, data = self.run_intake(self.manifest(b'<!DOCTYPE x [<!ENTITY y "bad">]><x/>', 'opensim_xml'))
        self.assertEqual(data['quarantine'][0]['refusal']['code'], 'xml_doctype_refused')

    def test_series_preserves_irregular_time(self):
        raw = b'id,subject,x,x_quantity,x_unit,value,quantity,unit\na,s,0,time,ms,1,force,N\na,s,3,time,ms,2,force,N\na,s,8,time,ms,1,force,N\n'
        _, data = self.run_intake(self.manifest(raw, 'series_csv'))
        self.assertEqual([s['x'] for s in data['records'][0]['payload']['samples']], [0, .003, .008])

    def test_series_nonmonotonic_withheld(self):
        raw = b'id,subject,x,x_quantity,x_unit,value,quantity,unit\na,s,1,time,s,1,force,N\na,s,0,time,s,2,force,N\n'
        _, data = self.run_intake(self.manifest(raw, 'series_csv'))
        self.assertFalse(data['records'])
        self.assertEqual(data['quarantine'][0]['refusal']['code'], 'axis_not_increasing')

    def test_two_points_frame_geometric_oracle(self):
        f = two_point_frame([[10, 20, 30], [10, 23, 34]], 'cm')
        self.assertAlmostEqual(f['length_m'], .05)
        basis = f['basis_columns']
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(sum(a*b for a, b in zip(basis[i], basis[j])), int(i == j))
        self.assertTrue(all(abs(f['origin_m'][i] + f['length_m'] * basis[2][i] - f['anchors_m'][1][i]) < 1e-14 for i in range(3)))
        x, y, z = basis
        det = x[0]*(y[1]*z[2]-y[2]*z[1])-y[0]*(x[1]*z[2]-x[2]*z[1])+z[0]*(x[1]*y[2]-x[2]*y[1])
        self.assertAlmostEqual(det, 1)

    def test_coincident_anchors_refused(self):
        with self.assertRaisesRegex(Refusal, 'coincident_anchors'):
            two_point_frame([[0, 0, 0], [0, 0, 0]], 'm')

    def test_geometry_unknown_frame_withheld(self):
        _, data = self.run_intake(self.manifest(canonical([{'id': 'x', 'anchors': [[0, 0, 0], [1, 0, 0]], 'length_unit': 'm'}]), 'geometry_json'))
        self.assertFalse(data['records'])
        self.assertTrue(data['quarantine'])

    def test_declarative_model_keeps_program_text_inert(self):
        rec = {'id': 'x', 'equations': 'raise SystemExit(99)',
               'ports': [{'name': 'F', 'quantity': 'force', 'unit': 'N'}],
               'assumptions': ['fixture'], 'validity_domain': 'fixture'}
        _, data = self.run_intake(self.manifest(canonical([rec]), 'model_json'))
        self.assertFalse(data['records'][0]['payload']['executable'])

    def reduction_inputs(self, law, rows):
        _, data = self.run_intake(self.csv(rows, conditions={'specimen': 'synthetic.fixture'}))
        records = {r['id']: r for r in data['records']}
        by_external = {r['external_id']: r['id'] for r in data['records']}
        request = {'law': law, 'target_id': 'model.test',
                   'inputs': {k: {'record': by_external[k]} for k in LAWS[law]['inputs']},
                   'context': {'specimen': 'synthetic.fixture'},
                   'assumptions': {k: 'exact synthetic construction' for k in LAWS[law]['assumptions']},
                   'validation': {'observable': 'response', 'falsifier': 'wrong response', 'acceptance_rule': 'analytic equality'}}
        return request, records

    def test_elastic_bar_physical_oracle(self):
        request, records = self.reduction_inputs('axial_stiffness', 'E,s,young_modulus,2,MPa\nA,s,area,10,mm2\nL,s,length,200,mm\n')
        result = reduce(request, records)
        # 1 N acting on 10 mm2 produces 100 kPa stress; strain .05;
        # extension of a 200 mm bar is 10 mm. k=1N/.01m=100 N/m.
        self.assertAlmostEqual(result['result']['value_si'], 100)
        self.assertFalse(result['runtime_ready'])

    def test_hydraulic_linearization(self):
        request, records = self.reduction_inputs('hydraulic_compliance', 'kappa,s,compressibility,4.6e-10,1/Pa\nV0,s,volume,0.002,m3\n')
        result = reduce(request, records)
        self.assertAlmostEqual(result['result']['value_si'] * 1e6, .002 * 4.6e-4)

    def test_signal_delay(self):
        request, records = self.reduction_inputs('propagation_delay', 'L,s,length,200,mm\nv,s,speed,20,m/s\n')
        self.assertAlmostEqual(reduce(request, records)['result']['value_si'], .01)

    def test_context_mismatch_refused(self):
        request, records = self.reduction_inputs('propagation_delay', 'L,s,length,200,mm\nv,s,speed,20,m/s\n')
        request['context']['specimen'] = 'different organism'
        with self.assertRaisesRegex(Refusal, 'applicability_mismatch'):
            reduce(request, records)

    def test_missing_assumptions_remain_blockers(self):
        request, records = self.reduction_inputs('propagation_delay', 'L,s,length,200,mm\nv,s,speed,20,m/s\n')
        request['assumptions'] = {}
        result = reduce(request, records)
        self.assertIn('assumption_unjustified:path_length_is_traveled_route', result['blockers'])

    def test_same_dimensions_wrong_quantity_refused(self):
        request, records = self.reduction_inputs('axial_stiffness', 'E,s,pressure,2,MPa\nA,s,area,10,mm2\nL,s,length,200,mm\n')
        with self.assertRaisesRegex(Refusal, 'reduction_quantity_mismatch'):
            reduce(request, records)

    def test_partial_proposal_requires_choice(self):
        bundle, _ = self.run_intake(self.csv('a,s,pressure,1,Pa\nb,s,pressure,2,kg\n'))
        graph = CreatureGraph()
        graph_path = self.root/'graph.json'
        graph.save(str(graph_path))
        result = main(['propose', str(bundle), '--graph', str(graph_path), '--output', str(self.root/'proposal.json')])
        self.assertEqual(result, 2)
        self.assertFalse((self.root/'proposal.json').exists())


if __name__ == '__main__':
    unittest.main()
