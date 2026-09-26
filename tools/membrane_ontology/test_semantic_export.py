import copy
import unittest
from pathlib import Path
from rdflib import Graph, URIRef, Literal, RDF
from pyshacl import validate
import semantic_export as se

HERE = Path(__file__).resolve().parent
C = se.NS


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.definition = se.model.decode((HERE / 'ontology.json').read_bytes())
        self.graph = Graph().parse(data=se.export(self.definition), format='nt')
        self.shapes = Graph().parse(HERE / 'semantic_shapes.ttl', format='turtle')

    def conforms(self):
        return validate(self.graph, shacl_graph=self.shapes, inference='none')[0]

    def test_real_definition_and_determinism(self):
        before = copy.deepcopy(self.definition)
        text = se.export(self.definition)
        self.assertTrue(self.conforms())
        self.assertEqual(self.definition, before)
        self.definition['nodes'].reverse()
        # Snapshot digest intentionally preserves authored list order; entity triples don't.
        entity = lambda s: [x for x in s.splitlines() if 'snapshot/' not in x]
        self.assertEqual(entity(text), entity(se.export(self.definition)))
        self.assertEqual(text, se.export(before))

    def test_missing_parent(self):
        n = next(self.graph.subjects(RDF.type, URIRef(C+'ContainedMembrane')))
        self.graph.remove((n, URIRef(C+'parent'), None))
        self.assertFalse(self.conforms())

    def test_cycle(self):
        n = next(self.graph.subjects(RDF.type, URIRef(C+'ContainedMembrane')))
        self.graph.set((n, URIRef(C+'parent'), n))
        self.assertFalse(self.conforms())

    def test_missing_endpoint(self):
        n = next(self.graph.subjects(RDF.type, URIRef(C+'Connection')))
        self.graph.add((n, URIRef(C+'endpoint'), URIRef(C+'port/absent')))
        self.assertFalse(self.conforms())

    def test_units_mismatch(self):
        n = next(self.graph.subjects(RDF.type, URIRef(C+'Connection')))
        endpoint = next(self.graph.objects(n, URIRef(C+'endpoint')))
        self.graph.set((endpoint, URIRef(C+'unit'), Literal('deliberately_wrong_unit')))
        self.assertFalse(self.conforms())

    def test_duplicate_matter_owner(self):
        owners = list(self.graph.subjects(RDF.type, URIRef(C+'Membrane')))[:2]
        matter = URIRef(C+'matter/test')
        self.graph.add((matter, RDF.type, URIRef(C+'MatterIdentity')))
        for owner in owners:
            self.graph.add((owner, URIRef(C+'ownsMatter'), matter))
        self.assertFalse(self.conforms())

    def test_existing_validator_still_gates_export(self):
        self.definition['nodes'][1]['parent'] = 'absent'
        with self.assertRaisesRegex(ValueError, 'missing_parent'):
            se.export(self.definition)


if __name__ == '__main__':
    unittest.main()
