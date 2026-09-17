"""INTAKE-GAIT lane tests: the two new check kinds (pass + fail), the lane
adapters on their real pinned bytes, and the preregistered stride falsifiers
(one corrupted row quarantines exactly itself, at adapter level, at bundle
level, and at contract level; the count identity closes)."""
import tempfile
import unittest
from pathlib import Path

from tools.science_funnel.adapters import ADAPTERS
from tools.science_funnel.batch import connectors as C
from tools.science_funnel.batch.contract import CHECKS, load_registry, run_contract
from tools.science_funnel.common import VERSION, canonical, sha
from tools.science_funnel.pipeline import ingest as bundle_ingest

DATA = Path(__file__).resolve().parents[1] / 'data'
JANISCH_CSV = DATA / 'janisch_kinematics' / 'wildprimate_kin.csv'


def record(**over):
    base = {
        'id': 'data.assertion.' + 'a' * 64,
        'source': {'id': 'fixture.source', 'release': 'r', 'license': 'l', 'url': 'u'},
        'artifact': {'id': 'f.csv', 'sha256': 'b' * 64},
        'provenance': {'source_id': 'data.source.' + 'c' * 64},
        'payload': {'species': 'Papio_anubis', 'sex': 'f', 'age': 'adult',
                    'substrate': {'diameter_m': 0.05, 'orientation_deg': 12.0},
                    'body_mass_kg': 8.0,
                    'joint_angles_deg': {'hipTD': 40.0, 'kneeLO': 120.5},
                    'mean_angles_deg': {}, 'yields_deg': {'kneeYld': -6.5},
                    'excursions_deg': {'hipExcur': 80.0}},
        'label': 'fixture stride',
    }
    base.update(over)
    return base


CTX = {'blob_pins': {'b' * 64}, 'known_ids': {'data.source.' + 'c' * 64}}


class GaitCheckKinds(unittest.TestCase):
    def test_field_in(self):
        params = {'field': 'payload.species', 'vocabulary': ['Papio_anubis']}
        self.assertIsNone(CHECKS['field_in'](record(), params, None))
        self.assertTrue(CHECKS['field_in'](record(
            payload={'species': 'Pan_corruptus'}), params, None))
        self.assertTrue(CHECKS['field_in'](record(payload={'species': ''}), params, None))
        self.assertTrue(CHECKS['field_in'](record(payload={}), params, None))

    def test_numeric_tree_range(self):
        params = {'path': 'payload.joint_angles_deg', 'min': 0.0, 'max': 360.0}
        self.assertIsNone(CHECKS['numeric_tree_range'](record(), params, None))
        deep = record(payload={'joint_angles_deg': {'hipTD': {'nested': [10.0, 350.0]}}})
        self.assertIsNone(CHECKS['numeric_tree_range'](deep, params, None))
        self.assertTrue(CHECKS['numeric_tree_range'](record(
            payload={'joint_angles_deg': {'hipTD': 999.0}}), params, None))
        self.assertTrue(CHECKS['numeric_tree_range'](record(
            payload={'joint_angles_deg': {'hipTD': -1.0}}), params, None))
        # absent or empty subtree passes: presence is the adapter's job
        self.assertIsNone(CHECKS['numeric_tree_range'](record(payload={}), params, None))
        self.assertIsNone(CHECKS['numeric_tree_range'](record(
            payload={'joint_angles_deg': {}}), params, None))


class JanischAdapterOnRealBytes(unittest.TestCase):
    def setUp(self):
        self.connector = C.CONNECTORS['janisch_wildprimate_kin']
        self.manifest = {'constants': self.connector['constants'], 'source': {}}
        self.raw = JANISCH_CSV.read_bytes()

    def rows(self):
        return ADAPTERS['janisch_strides'](self.raw, self.manifest, Path('.'))

    def test_count_identity_386_plus_1(self):
        rows = self.rows()
        accepted = [r for r in rows if 'refusal' not in r]
        refused = [r for r in rows if 'refusal' in r]
        self.assertEqual(len(rows), 387)  # fetched
        self.assertEqual(len(accepted), 386)  # admitted
        self.assertEqual(len(refused), 1)  # quarantined: the all-NA row
        self.assertEqual(refused[0]['location'], 'csv_record:28')

    def test_every_record_carries_species_and_substrate_tags(self):
        for row in self.rows():
            if 'refusal' in row:
                continue
            payload = row['payload']
            self.assertIn(payload['species'], self.connector['constants']['species_vocabulary'])
            self.assertIsInstance(payload['substrate']['diameter_m'], float)
            self.assertIsInstance(payload['substrate']['orientation_deg'], float)
            self.assertGreaterEqual(payload['n_measured_values'], 1)
            self.assertEqual(row['class_contract']['class_id'],
                             'batch.observation.janisch_stride')

    def test_species_counts_match_the_dossier(self):
        counts = {}
        for row in self.rows():
            if 'refusal' not in row:
                counts[row['payload']['species']] = counts.get(row['payload']['species'], 0) + 1
        self.assertEqual(counts['Lophocebus_albigena'], 58)
        self.assertEqual(counts['Chlorocebus_aethiops'], 43)
        self.assertEqual(counts['Papio_anubis'], 29)
        self.assertEqual(len(counts), 14)

    def test_external_ids_unique(self):
        ids = [r['external_id'] for r in self.rows() if 'refusal' not in r]
        self.assertEqual(len(ids), len(set(ids)))


class StrideCorruptionFalsifier(unittest.TestCase):
    """One corrupted stride row must quarantine exactly itself (three
    corruption modes), neighbours unchanged, count identity still closing."""

    def setUp(self):
        self.connector = C.CONNECTORS['janisch_wildprimate_kin']
        self.manifest = {'constants': self.connector['constants'], 'source': {}}
        self.lines = JANISCH_CSV.read_text(encoding='utf-8-sig').splitlines(True)

    def corrupt(self, column, value):
        header = self.lines[0].rstrip('\r\n').split(',')
        index = header.index(column)
        lines = list(self.lines)
        fields = lines[3].rstrip('\r\n').split(',')  # file line 4: a real stride
        fields[index] = value
        lines[3] = ','.join(fields) + '\n'
        return ''.join(lines).encode()

    def assert_exactly_one_new_quarantine(self, raw, expected_code):
        rows = ADAPTERS['janisch_strides'](raw, self.manifest, Path('.'))
        accepted = [r for r in rows if 'refusal' not in r]
        refused = [r for r in rows if 'refusal' in r]
        self.assertEqual(len(rows), 387)  # fetched unchanged
        self.assertEqual(len(accepted), 385)  # 386 - the corrupted row
        self.assertEqual(len(refused), 2)  # the all-NA row + the corrupted row
        codes = {r['refusal']['code'] for r in refused}
        self.assertIn(expected_code, codes)
        self.assertEqual({r['location'] for r in refused},
                         {'csv_record:4', 'csv_record:28'})

    def test_corrupted_species_quarantines_exactly_itself(self):
        self.assert_exactly_one_new_quarantine(
            self.corrupt('Species', 'Pan_corruptus'), 'species_outside_vocabulary')

    def test_corrupted_angle_quarantines_exactly_itself(self):
        self.assert_exactly_one_new_quarantine(
            self.corrupt('hipTD', '999'), 'value_outside_envelope')

    def test_corrupted_substrate_quarantines_exactly_itself(self):
        self.assert_exactly_one_new_quarantine(
            self.corrupt('subs_diam', '-5'), 'value_outside_envelope')

    def test_corrupted_rowcount_refuses_whole_artifact(self):
        raw = ''.join(self.lines[:-1]).encode()  # drop one row
        with self.assertRaises(Exception) as caught:
            ADAPTERS['janisch_strides'](raw, self.manifest, Path('.'))
        self.assertIn('stride_row_count_changed', str(caught.exception))


class StrideContractFalsifier(unittest.TestCase):
    def test_contract_flags_exactly_the_corrupted_record(self):
        registry = load_registry()
        contract = registry['batch.observation.janisch_stride']
        good = record()
        bad_id = 'data.assertion.' + 'd' * 64
        bad = record(id=bad_id, payload={**record()['payload'],
                                         'species': 'Pan_corruptus'})
        result = run_contract(contract, [good, bad], dict(CTX))
        self.assertEqual(result['records'], 2)
        self.assertEqual({f['id'] for f in result['failures']}, {bad_id})
        self.assertEqual(result['passed'], 1)

    def test_admitted_records_pass_their_contract(self):
        registry = load_registry()
        contract = registry['batch.observation.janisch_stride']
        rows = ADAPTERS['janisch_strides'](
            JANISCH_CSV.read_bytes(),
            {'constants': C.CONNECTORS['janisch_wildprimate_kin']['constants'], 'source': {}},
            Path('.'))
        records = []
        for row in rows:
            if 'refusal' in row:
                continue
            view = dict(row)
            view['id'] = 'data.assertion.' + 'e' * 64
            view['source'] = {'id': 'janisch.wildprimate_kinematics', 'release': 'r',
                              'license': 'l', 'url': 'u'}
            view['provenance'] = {'source_id': 'data.source.' + 'c' * 64}
            view['artifact'] = {'id': 'wildprimate_kin.csv', 'sha256': 'b' * 64}
            records.append(view)
        result = run_contract(contract, records, dict(CTX))
        self.assertEqual(result['records'], 386)
        self.assertEqual(result['failures'], [])


class DryadAdapterOnRealBytes(unittest.TestCase):
    def run_connector(self, connector_id):
        connector = C.CONNECTORS[connector_id]
        data_file = connector['artifacts'][0]['id']
        dataset_file = data_file.replace('_files.json', '_dataset.json')
        with tempfile.TemporaryDirectory() as tmp:
            pin = connector['constants']['dataset_sha256']
            Path(tmp, pin).write_bytes((DATA / connector['data_dir'] / dataset_file).read_bytes())
            rows = ADAPTERS['dryad_files_meta'](
                (DATA / connector['data_dir'] / data_file).read_bytes(),
                {'constants': connector['constants'], 'source': {}}, Path(tmp, 'data'))
        return rows

    def test_granatosky_twelve_files_video_excluded(self):
        rows = self.run_connector('granatosky_gait')
        by_path = {r['payload']['file_path']: r for r in rows}
        self.assertEqual(len(rows), 12)
        self.assertEqual(by_path['Gait_Videos.zip']['payload']['status'],
                         'excluded_by_policy')
        self.assertEqual(by_path['mammal_gait.txt']['payload']['status'], 'deferred')
        self.assertEqual(by_path['tetrapod_gait.txt']['payload']['status'], 'deferred')
        for row in rows:
            self.assertEqual(row['class_contract']['class_id'], 'batch.deferred.dryad_file')
            self.assertIn('bearer token', row['payload']['cause'])

    def test_higurashi_two_files_deferred(self):
        rows = self.run_connector('higurashi_gait')
        by_path = {r['payload']['file_path']: r for r in rows}
        self.assertEqual(len(rows), 2)
        self.assertEqual(by_path['Dataset_macaque-gait.xlsx']['payload']['sha256_digest'],
                         'eb75067157e57ddedc1a672124083899362e69773f713e021dff70ece3726fc3')
        for row in rows:
            self.assertEqual(row['payload']['status'], 'deferred')

    def test_deferred_records_pass_their_contract(self):
        registry = load_registry()
        contract = registry['batch.deferred.dryad_file']
        records = []
        for row in self.run_connector('granatosky_gait') + self.run_connector('higurashi_gait'):
            view = dict(row)
            view['id'] = 'data.assertion.' + 'e' * 64
            view['source'] = {'id': 'dryad.fixture', 'release': 'r', 'license': 'l',
                              'url': 'u'}
            view['provenance'] = {'source_id': 'data.source.' + 'c' * 64}
            view['artifact'] = {'id': 'files.json', 'sha256': 'b' * 64}
            records.append(view)
        result = run_contract(contract, records, dict(CTX))
        self.assertEqual(result['records'], 14)
        self.assertEqual(result['failures'], [])


class GaitConnectorDeclarations(unittest.TestCase):
    def test_lane_connectors_declared_with_classes(self):
        for cid in ('janisch_wildprimate_kin', 'granatosky_gait', 'higurashi_gait'):
            connector = C.CONNECTORS[cid]
            self.assertEqual(connector['mode'], 'admit')
            self.assertTrue(connector['artifacts'], cid)
            for artifact in connector['artifacts']:
                self.assertRegex(artifact['sha256'], '^[0-9a-f]{64}$')
            self.assertTrue(connector['classes'], cid)

    def test_lane_does_not_extend_reprove_sources(self):
        self.assertEqual(len(C.REPROVE_SOURCES), 5)

    def test_search_dirs_cover_lane_data_dirs(self):
        from tools.science_funnel.batch import reprove
        for data_dir in ('janisch_kinematics', 'dryad_granatosky', 'dryad_higurashi'):
            self.assertIn(data_dir, reprove._SEARCH_DIRS)


class BundleCorruptionFalsifier(unittest.TestCase):
    """End to end through the intake pipeline: the real manifest with one
    corrupted CSV byte-stream must yield 385 accepted + 2 quarantined and
    close the count identity inside the bundle receipt."""

    def test_bundle_count_identity_with_one_corrupted_row(self):
        connector = C.CONNECTORS['janisch_wildprimate_kin']
        lines = JANISCH_CSV.read_text(encoding='utf-8-sig').splitlines(True)
        header = lines[0].rstrip('\r\n').split(',')
        fields = lines[3].rstrip('\r\n').split(',')
        fields[header.index('hipTD')] = '999'
        lines[3] = ','.join(fields) + '\n'
        raw = ''.join(lines).encode()
        pin = sha(raw)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'artifacts').mkdir()
            (root / 'artifacts' / pin).write_bytes(raw)
            manifest = {'schema_version': VERSION, 'adapter': 'janisch_strides',
                        'source': connector['source'],
                        'artifacts': [{'id': 'wildprimate_kin.csv',
                                       'path': 'artifacts/' + pin, 'sha256': pin,
                                       'role': 'data'}],
                        'constants': connector['constants']}
            (root / 'manifest.json').write_bytes(canonical(manifest))
            bundle = bundle_ingest(str(root / 'manifest.json'), str(root / 'bundles'))
            receipt = __import__('json').loads(
                (bundle / 'receipt.json').read_bytes())
            self.assertEqual(receipt['accepted'], 385)
            self.assertEqual(receipt['quarantined'], 2)
            self.assertEqual(receipt['accepted'] + receipt['quarantined'], 387)


if __name__ == '__main__':
    unittest.main()
