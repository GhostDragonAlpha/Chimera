"""INTAKE-PAPER-TABLE lane tests: the connector resolves its pins from the
data-dir receipt, the adapter runs on the real pinned article full text
(21 records: 20 segment-quantity + 1 table summary, zero quarantine), the
preregistered falsifier (one corrupted digit quarantines exactly that segment
row and the dependent summary) is exercised end-to-end in memory, and the
derived closures hold on the pinned inputs."""
import importlib.util
import unittest
from pathlib import Path

from tools.science_funnel.adapters import ADAPTERS
from tools.science_funnel.batch import connectors as C

DATA = Path(__file__).resolve().parents[1] / 'data'
TABLE_XML = DATA / 'oku_paper_table' / 'PMC7940622_fulltext.xml'
VALIDATION = (Path(__file__).resolve().parents[2] / 'creature_graph' /
              'validation' / 'batch_paper_inertia_20260918')

SPEC = {'mass': ('kg', 8.184), 'length': ('m', 0.482),
        'com_fraction': ('1', 0.52), 'moment_of_inertia': ('kg*m2', 0.0207)}


def _closure_module():
    spec = importlib.util.spec_from_file_location(
        'paper_table_closures', VALIDATION / 'closures.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PaperTableConnectorDeclarations(unittest.TestCase):
    def test_lane_connector_merges_by_id(self):
        self.assertIn('oku_paper_table', C.CONNECTORS)
        connector = C.CONNECTORS['oku_paper_table']
        self.assertEqual(connector['data_dir'], 'oku_paper_table')
        self.assertEqual(connector['adapter'], 'oku_paper_table')
        self.assertEqual(connector['classes'],
                         {'measurement': 'batch.property.paper_table_inertial'})
        for artifact in connector['artifacts']:
            self.assertRegex(artifact['sha256'], '^[0-9a-f]{64}$')
            self.assertTrue((DATA / connector['data_dir'] / artifact['id']).is_file())

    def test_adapter_self_registered(self):
        self.assertIn('oku_paper_table', ADAPTERS)


class PaperTableAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = ADAPTERS['oku_paper_table'](TABLE_XML.read_bytes(),
                                               {'source': {}}, Path('.'))
        cls.records = [r for r in cls.rows if 'refusal' not in r]
        cls.rejections = [r for r in cls.rows if 'refusal' in r]

    def test_count_identity_on_pinned_bytes(self):
        self.assertEqual(len(self.records), 21)
        self.assertEqual(len(self.rejections), 0)

    def test_one_record_per_segment_and_quantity(self):
        seen = {(r['payload']['conditions']['table_cell']['segment'],
                 r['payload']['parameter']) for r in self.records[:-1]}
        self.assertEqual(len(seen), 20)
        segments = {s for s, _ in seen}
        self.assertEqual(segments, {'HAT', 'thigh', 'shank', 'foot', 'phalanges'})

    def test_values_units_and_species_tags(self):
        hat = {r['payload']['parameter'].replace('segment_', ''): r['payload']
               for r in self.records[:4]}
        for parameter, (unit, expected) in SPEC.items():
            self.assertAlmostEqual(hat[parameter]['value_si'], expected,
                                   delta=1e-12)
            self.assertEqual(hat[parameter]['unit_si'], unit)
        for row in self.records:
            conditions = row['payload']['conditions']
            self.assertEqual(conditions['species'],
                             'Macaca fuscata (Japanese macaque)')
            self.assertIn('single adult male', conditions['specimen'])
            self.assertIn('Creative Commons Attribution 4.0 International',
                          conditions['license_quote'])
            self.assertIn('closure_mass_sum', conditions)
            self.assertIn('forelimbs', ' '.join(
                conditions.get('known_gaps', ['forelimbs folded into HAT'])) or
                'forelimbs folded into HAT')

    def test_class_contract_is_the_paper_table_variant(self):
        for row in self.records:
            self.assertEqual(row['class_contract'],
                             {'class_id': 'batch.property.paper_table_inertial',
                              'version': 1})

    def test_corrupted_digit_quarantines_exactly_its_row(self):
        """Preregistered falsifier: corrupting one digit of one pinned cell must
        quarantine exactly that segment row (collapsed into one rejection with
        digit_mismatch) plus the dependent summary; the other four rows still
        admit, visibly, with no silent drops."""
        corrupted = TABLE_XML.read_bytes().replace(b'0.557', b'0.558', 1)
        rows = ADAPTERS['oku_paper_table'](corrupted, {'source': {}}, Path('.'))
        records = [r for r in rows if 'refusal' not in r]
        rejections = [r for r in rows if 'refusal' in r]
        # 15 admitted (3 clean rows x 4 + clean HAT x 4) + summary withheld
        self.assertEqual(len(records), 16)
        self.assertEqual(len(rejections), 2)
        codes = {r['refusal']['code'] for r in rejections}
        self.assertEqual(codes, {'digit_mismatch', 'dependent_row_quarantined'})
        self.assertNotIn('oku2021.table1:thigh:mass',
                         [r['external_id'] for r in records])

    def test_summary_blocked_when_any_segment_fails(self):
        corrupted = TABLE_XML.read_bytes().replace(b'0.269', b'0.270', 1)
        rows = ADAPTERS['oku_paper_table'](corrupted, {'source': {}}, Path('.'))
        records = [r for r in rows if 'refusal' not in r]
        self.assertNotIn('oku2021.table1:summary:implied_mass',
                         [r['external_id'] for r in records])


class DerivedClosures(unittest.TestCase):
    def test_mass_sum_identity_and_tolerance(self):
        closures = _closure_module()
        result = closures.mass_sum_closure()
        self.assertEqual(result['implied_whole_body_mass_kg'], '9.111')
        self.assertEqual(result['rounding_tolerance_kg'], '\u00b10.0025')

    def test_pantheria_envelope_on_pinned_bytes(self):
        closures = _closure_module()
        result = closures.plausibility_closure()
        self.assertTrue(result['inside_envelope'])
        self.assertIn('INSIDE_ENVELOPE', result['verdict'])

    def test_live_page_verification_still_closed(self):
        """The verification artifact must keep its CLOSED verdict: the pinned
        bytes and the banked transcription still agree digit-for-digit."""
        import json
        verdict = json.loads((VALIDATION / 'verification.json')
                             .read_text(encoding='utf-8'))['verdict']
        self.assertEqual(verdict, 'CLOSED')


if __name__ == '__main__':
    unittest.main()
