"""LOCAL-REFERENCES-INTAKE lane tests (work.data.local_refs_20260918).

Covers the preregistered falsifiers: a corrupted derived row quarantines
EXACTLY itself; the anchors' published aggregates reproduce from the derived
tables (Rule 0 gate); every record carries the Homo sapiens (comparative) tag;
admission is aggregate-only (no per-subject record exists); the mocap series
admit under batch.property.series with strictly increasing x; the muscle
inventory admits as one sha-pinned documentation entity.
"""
import csv
import hashlib
import io
import json
import unittest
from pathlib import Path

from tools.science_funnel.adapters import ADAPTERS
from tools.science_funnel.batch import connectors as C

ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parents[1] / 'data'
ANSUR = DATA / 'ansur2_derived_20260918'
MOCAP = DATA / 'mocap_walk_series_20260918'
DOC = DATA / 'muscle_inventory_doc_20260918'

MALE = ANSUR / 'ansur2_male_derived.csv'
FEMALE = ANSUR / 'ansur2_female_derived.csv'
HIP = MOCAP / 'mocap_cmus35_walk_hip_mean_cycle.csv'
MOCAP_REFERENCE = ROOT / 'research_references' / 'human' / 'mocap_walk_reference.json'
ANCHORS = ROOT / 'research_references' / 'human' / 'ansur_anchors.json'

HOMO_TAG = 'Homo sapiens (comparative)'
DOC_PIN = 'f16fde6da59c1e6ccf5214734957b6570cc120310b22959ef35c13caab121c71'


def _ansur_manifest(tmp):
    """Female table rides as companion; stage it under its pin inside tmp."""
    female = FEMALE.read_bytes()
    pin = hashlib.sha256(female).hexdigest()
    (tmp / pin).write_bytes(female)
    return {'source': {}, 'constants': {'female_derived_sha256': pin}}, tmp / pin


def _mocap_manifest():
    conn = C.CONNECTORS['mocap_walk_series_20260918']
    return {'source': {}, 'constants': dict(conn['constants'])}


class LaneConnectorDeclarations(unittest.TestCase):
    def test_lane_connectors_merge_by_id(self):
        for cid in ('ansur2_derived_20260918', 'mocap_walk_series_20260918',
                    'muscle_inventory_doc_20260918'):
            self.assertIn(cid, C.CONNECTORS)
            connector = C.CONNECTORS[cid]
            self.assertTrue(connector['artifacts'], cid)
            for artifact in connector['artifacts']:
                self.assertRegex(artifact['sha256'], '^[0-9a-f]{64}$')
                staged = DATA / connector['data_dir'] / artifact['id']
                self.assertTrue(staged.is_file(), staged)

    def test_adapters_self_registered(self):
        for name in ('ansur2_aggregates', 'mocap_walk_series',
                     'muscle_inventory_doc'):
            self.assertIn(name, ADAPTERS)

    def test_reprove_sources_untouched(self):
        self.assertEqual(len(C.REPROVE_SOURCES), 5)


class AnsurAggregates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp.name)
        manifest, _ = _ansur_manifest(tmp)
        cls.rows = ADAPTERS['ansur2_aggregates'](MALE.read_bytes(), manifest, tmp / 'staged')
        cls.records = [r for r in cls.rows if 'refusal' not in r]
        cls.rejections = [r for r in cls.rows if 'refusal' in r]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_record_shape_and_counts(self):
        self.assertEqual(self.rejections, [])
        self.assertEqual(len(self.records), 2 * 14 * 5)
        for row in self.records:
            self.assertEqual(row['record_type'], 'measurement')
            self.assertEqual(row['class_contract'],
                             {'class_id': 'batch.property.measurement', 'version': 1})
            payload = row['payload']
            self.assertIn(payload['unit_si'], ('m', 'kg', '1'))
            self.assertIn(payload['conditions']['statistic'],
                          ('median', 'p5', 'p95', 'mean', 'n'))

    def test_species_tag_on_every_record(self):
        for row in self.records:
            self.assertEqual(row['payload']['conditions']['subject_species'], HOMO_TAG)

    def test_aggregate_only_no_person_level_records(self):
        for row in self.records:
            self.assertIn('aggregate_only_person_level_rows_not_admitted',
                          row['unknowns'])

    def test_anchors_reproduce_from_derived_tables(self):
        """Rule 0 gate: the published anchors must reproduce field-by-field."""
        anchors = json.loads(ANCHORS.read_text(encoding='utf-8'))
        got = {}
        for row in self.records:
            sex = 'male' if ':male:' in row['external_id'] else 'female'
            _, _, column, stat = row['external_id'].split(':')
            got[(sex, column, stat)] = row['payload']['value_si']
        checked = 0
        for sex in ('male', 'female'):
            for column, published in anchors[sex].items():
                for stat in ('median', 'p5', 'p95', 'mean'):
                    value = got[(sex, column, stat)]
                    self.assertLessEqual(abs(value - published[stat]),
                                         1e-9 * max(1.0, abs(published[stat])),
                                         (sex, column, stat))
                    checked += 1
                self.assertEqual(int(got[(sex, column, 'n')]), published['n'])
                checked += 1
        self.assertEqual(checked, 2 * 13 * 5)

    def test_corrupted_row_quarantines_exactly_itself(self):
        """The preregistered falsifier: corrupt one derived cell in memory; the
        blast radius is exactly that subject row."""
        import tempfile
        rows = MALE.read_text(encoding='utf-8').split('\n')
        victim = rows[1].split(',')          # first subject row
        self.assertEqual(len(victim), 14)
        victim[0] = '-9.99'                  # stature -> nonpositive
        rows[1] = ','.join(victim)
        corrupted = ('\n'.join(rows)).encode('utf-8')
        with tempfile.TemporaryDirectory() as name:
            tmp = Path(name)
            manifest, _ = _ansur_manifest(tmp)
            out = ADAPTERS['ansur2_aggregates'](corrupted, manifest, tmp / 'staged')
        rejections = [r for r in out if 'refusal' in r]
        records = [r for r in out if 'refusal' not in r]
        self.assertEqual(len(rejections), 1)
        self.assertEqual(rejections[0]['location'], 'ansur2:male:row2')
        self.assertEqual(rejections[0]['refusal']['code'], 'nonpositive_derived_value')
        # AGGREGATE blast radius (recorded in the work record): the corrupted
        # subject row leaves the record set; its only trace is male n=4081 on
        # every male block, everything else identical. The corrupted row
        # quarantines exactly itself -- no other row is dropped or altered.
        self.assertEqual(len(records), 2 * 14 * 5)
        male_n = {r['payload']['conditions']['n_subjects']
                  for r in records if ':male:' in r['external_id']}
        female_n = {r['payload']['conditions']['n_subjects']
                    for r in records if ':female:' in r['external_id']}
        self.assertEqual(male_n, {4081})
        self.assertEqual(female_n, {1986})


class MocapSeries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp.name)
        # stage the two companions under their pins (the bundle layout)
        for joint in ('knee', 'ankle'):
            blob = (MOCAP / ('mocap_cmus35_walk_%s_mean_cycle.csv' % joint)).read_bytes()
            (tmp / hashlib.sha256(blob).hexdigest()).write_bytes(blob)
        cls.rows = ADAPTERS['mocap_walk_series'](
            HIP.read_bytes(), _mocap_manifest(), tmp / 'staged')
        cls.records = [r for r in cls.rows if 'refusal' not in r]
        cls.rejections = [r for r in cls.rows if 'refusal' in r]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_three_series_under_series_contract(self):
        self.assertEqual(self.rejections, [])
        self.assertEqual(len(self.records), 3)
        for row in self.records:
            self.assertEqual(row['record_type'], 'series')
            self.assertEqual(row['class_contract'],
                             {'class_id': 'batch.property.series', 'version': 1})
            payload = row['payload']
            self.assertEqual(payload['unit_si'], 'rad')
            self.assertEqual(payload['x_unit_si'], '1')
            self.assertEqual(len(payload['samples']), 101)
            xs = [s['x'] for s in payload['samples']]
            self.assertEqual(xs[0], 0.0)
            self.assertEqual(xs[-1], 1.0)
            self.assertTrue(all(b > a for a, b in zip(xs, xs[1:])))
            self.assertEqual(payload['conditions']['subject_species'], HOMO_TAG)
            self.assertIn('duty_factor', payload['conditions']['spatiotemporal_scalars'])

    def test_curves_match_the_resident_reference_file(self):
        doc = json.loads(MOCAP_REFERENCE.read_text(encoding='utf-8'))
        by_joint = {r['external_id'].rsplit('_', 2)[0].replace(
            'mocap_cmus35_walk_', ''): r for r in self.records}
        import math
        for joint, block in doc['envelopes_deg'].items():
            row = by_joint[joint]
            for sample, deg in zip(row['payload']['samples'], block['mean']):
                self.assertAlmostEqual(sample['value'], math.radians(deg), places=12)

    def test_swapped_companion_pin_refuses_loudly(self):
        import tempfile
        manifest = _mocap_manifest()
        ankle_sha = hashlib.sha256(
            (MOCAP / 'mocap_cmus35_walk_ankle_mean_cycle.csv').read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as name:
            tmp = Path(name)
            (tmp / ankle_sha).write_bytes(
                (MOCAP / 'mocap_cmus35_walk_ankle_mean_cycle.csv').read_bytes())
            manifest['constants']['knee_curve_sha256'] = ankle_sha
            out = ADAPTERS['mocap_walk_series'](HIP.read_bytes(), manifest, tmp / 'staged')
        rejections = [r for r in out if 'refusal' in r]
        records = [r for r in out if 'refusal' not in r]
        self.assertEqual(len(rejections), 1)
        self.assertEqual(rejections[0]['refusal']['code'], 'mocap_series_id_mismatch')
        self.assertEqual(len(records), 2)


class MuscleInventoryDoc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = ADAPTERS['muscle_inventory_doc'](
            (DOC / 'MUSCLE_INVENTORY.md').read_bytes(),
            {'source': {}, 'constants': {'muscle_inventory_sha256': DOC_PIN}}, DOC)
        cls.records = [r for r in cls.rows if 'refusal' not in r]

    def test_one_sha_pinned_entity(self):
        self.assertEqual(len(self.records), 1)
        row = self.records[0]
        self.assertEqual(row['record_type'], 'entity')
        self.assertEqual(row['class_contract'],
                         {'class_id': 'batch.entity.external', 'version': 1})
        self.assertEqual(row['payload']['sha256'], DOC_PIN)
        self.assertEqual(row['payload']['subject_species'], HOMO_TAG)

    def test_drifted_bytes_refuse(self):
        pin = hashlib.sha256(b'not the document').hexdigest()
        from tools.science_funnel.common import Refusal
        with self.assertRaises(Refusal):
            ADAPTERS['muscle_inventory_doc'](b'not the document',
                                             {'source': {},
                                              'constants': {'muscle_inventory_sha256': pin}},
                                             DOC)


if __name__ == '__main__':
    unittest.main()
