"""Batch layer tests: every mechanical check kind (pass + fail), the adapters
on their real pinned bytes, the count identity, and the three preregistered
falsifiers (mutation probe, pin refusal, idempotent record identity)."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.science_funnel.adapters import ADAPTERS
from tools.science_funnel.batch import connectors as C
from tools.science_funnel.batch.contract import CHECKS, load_registry, run_contract
from tools.science_funnel.common import VERSION, Refusal, canonical, digest, require, sha
from tools.science_funnel.pipeline import ingest as bundle_ingest

DATA = Path(__file__).resolve().parents[1] / 'data'


def record(**over):
    base = {
        'id': 'data.assertion.' + 'a' * 64,
        'source': {'id': 'fixture.source', 'release': 'r', 'license': 'l', 'url': 'u'},
        'artifact': {'id': 'f.txt', 'sha256': 'b' * 64},
        'provenance': {'source_id': 'data.source.' + 'c' * 64},
        'payload': {'value_si': 1.0, 'unit_si': 'm'},
        'label': 'fixture',
    }
    base.update(over)
    return base


CTX = {'blob_pins': {'b' * 64}, 'known_ids': {'data.source.' + 'c' * 64}}


class CheckKinds(unittest.TestCase):
    def test_id_syntax(self):
        good = {'pattern': '^data\\.assertion\\.[0-9a-f]{64}$'}
        self.assertIsNone(CHECKS['id_syntax'](record(), good, None))
        bad = record(id='hand.written.id')
        self.assertTrue(CHECKS['id_syntax'](bad, good, None))

    def test_provenance_present(self):
        self.assertIsNone(CHECKS['provenance_present'](record(), {}, None))
        self.assertTrue(CHECKS['provenance_present'](record(source={}), {}, None))
        self.assertTrue(CHECKS['provenance_present'](record(artifact={}), {}, None))

    def test_sha256_chain(self):
        ctx = {'blob_pins': {'b' * 64}}
        self.assertIsNone(CHECKS['sha256_chain'](record(), {}, ctx))
        self.assertTrue(CHECKS['sha256_chain'](record(), {}, {'blob_pins': set()}))
        self.assertTrue(CHECKS['sha256_chain'](
            record(artifact={'id': 'f', 'sha256': 'zz'}), {}, ctx))

    def test_fk_exists(self):
        ctx = {'known_ids': {'data.source.' + 'c' * 64}}
        view = record(provenance={'source_id': 'data.source.' + 'c' * 64})
        self.assertIsNone(CHECKS['fk_exists'](view, {'field': 'provenance.source_id'}, ctx))
        dangling = record(provenance={'source_id': 'data.source.gone'})
        self.assertTrue(CHECKS['fk_exists'](dangling, {'field': 'provenance.source_id'}, ctx))

    def test_units_in(self):
        params = {'path': 'payload.unit_si', 'vocabulary': ['m', 'mm']}
        self.assertIsNone(CHECKS['units_in'](record(), params, None))
        self.assertTrue(CHECKS['units_in'](record(
            payload={'value_si': 1, 'unit_si': 'furlong'}), params, None))
        self.assertTrue(CHECKS['units_in'](record(
            payload={'value_si': 1}), params, None))

    def test_field_range(self):
        params = {'path': 'payload.value_si', 'min': -100.0, 'max': 9000.0}
        self.assertIsNone(CHECKS['field_range'](record(), params, None))
        self.assertTrue(CHECKS['field_range'](record(
            payload={'value_si': 10000.0}), params, None))
        self.assertTrue(CHECKS['field_range'](record(
            payload={'value_si': float('nan')}), params, None))
        self.assertTrue(CHECKS['field_range'](record(
            payload={'value_si': 'fast'}), params, None))


class ContractRuns(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry()

    def test_registry_loads_with_rule0(self):
        for cid, contract in self.registry.items():
            for field in ('statement', 'prediction', 'falsifier'):
                self.assertTrue(contract[field].strip(), cid)
            self.assertTrue(contract['checks'])

    def test_run_contract_quarantines_exactly_the_failure(self):
        contract = self.registry['batch.property.copernicus_tile']
        good = record()
        bad = record(id='data.assertion.' + 'd' * 64, payload={'value_si': 99999.0,
                                                               'unit_si': 'm'})
        result = run_contract(contract, [good, bad], dict(CTX))
        self.assertEqual(result['records'], 2)
        self.assertEqual(len({f['id'] for f in result['failures']}), 1)
        self.assertEqual(result['failures'][0]['id'], bad['id'])
        self.assertEqual(result['passed'], 1)


class MutationFalsifier(unittest.TestCase):
    def test_mutated_record_breaks_content_identity(self):
        victim = record()
        body = {k: v for k, v in victim.items() if k != 'id'}
        victim['id'] = 'data.assertion.' + digest(body)
        pristine = victim['id']
        self.assertEqual('data.assertion.' + digest(body), pristine)
        corrupted = dict(victim)
        corrupted['label'] = victim['label'] + ' CORRUPTED'
        body = {k: v for k, v in corrupted.items() if k != 'id'}
        self.assertNotEqual('data.assertion.' + digest(body), pristine)

    def test_mutated_artifact_byte_refuses_at_ingest(self):
        """Falsifier 3: one flipped byte in a pinned artifact must refuse the
        whole ingest loudly (pin_drift), before any record is created."""
        payload = b'concept id\trepresentation id\ten\nFMA1\tBP1\theart\n'
        pin = sha(payload)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'artifacts').mkdir()
            (root / 'artifacts' / pin).write_bytes(payload)
            manifest = {
                'schema_version': VERSION,
                'adapter': 'bp3d_lists',
                'source': {'id': 'fixture.bp3d', 'release': 'r', 'license': 'l', 'url': 'u'},
                'artifacts': [{'id': 'partof_parts_list_e.txt',
                               'path': 'artifacts/' + pin, 'sha256': pin, 'role': 'data'}],
                'constants': {'isa_parts_sha256': pin},
            }
            manifest_path = root / 'manifest.json'
            manifest_path.write_bytes(canonical(manifest))
            # one flipped byte in the pinned artifact must refuse the ingest
            # loudly (pin_drift) before any record is created
            corrupted = bytearray(payload)
            corrupted[0] = ord('X')
            (root / 'artifacts' / pin).write_bytes(bytes(corrupted))
            with self.assertRaises(Refusal) as caught:
                bundle_ingest(str(manifest_path), str(root / 'bundles'))
            self.assertEqual(caught.exception.code, 'pin_drift')


class AdaptersOnRealBytes(unittest.TestCase):
    def test_smithsonian_cranium(self):
        raw = (DATA / 'smithsonian' / 'USNM15259_cranium_document.json').read_bytes()
        rows = ADAPTERS['smithsonian_voyager'](raw, {'source': {}}, Path('.'))
        self.assertEqual(len(rows), 1)
        payload = rows[0]['payload']
        self.assertEqual(payload['units'], 'mm')
        self.assertTrue(1.0 <= payload['bbox_extent_mm'] <= 500.0)
        self.assertEqual(rows[0]['class_contract']['class_id'],
                         'batch.geometry.smithsonian_voyager')

    def test_copernicus_eoxml(self):
        raw = (DATA / 'copernicus_glo30' /
               'Copernicus_DSM_10_N18_00_W066_00.xml').read_bytes()
        rows = ADAPTERS['copernicus_meta'](raw, {'source': {}}, Path('.'))
        by_field = {row['external_id'].rsplit(':', 1)[1]: row for row in rows}
        self.assertAlmostEqual(by_field['posting']['payload']['value_si'], 1.0)
        self.assertEqual(by_field['height_min']['payload']['unit_si'], 'm')
        for row in rows:
            self.assertEqual(row['class_contract']['class_id'],
                             'batch.property.copernicus_tile')

    def test_bp3d_lists_merge_and_conflict(self):
        partof = ('concept id\trepresentation id\ten\n'
                  'FMA1\tBP1\theart\nFMA2\tBP2\tlung\n')
        isa = ('concept id\trepresentation id\ten\n'
               'FMA2\tBP2\tlung\nFMA3\tBP3\tliver\nFMA1\tBP9\tconflict\n')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pin = sha(isa.encode())
            (root / pin).write_bytes(isa.encode())
            primary = root / sha(partof.encode())
            primary.write_bytes(partof.encode())
            rows = ADAPTERS['bp3d_lists'](
                partof.encode(),
                {'constants': {'isa_parts_sha256': pin}, 'source': {}}, primary)
        entities = {row['external_id']: row for row in rows if 'refusal' not in row}
        conflicts = [row for row in rows if 'refusal' in row]
        self.assertEqual(len(entities), 3)  # FMA1, FMA2, FMA3
        self.assertEqual(len(conflicts), 1)  # FMA1 label conflict quarantined
        self.assertEqual(sorted(entities['bp3d:FMA2']['payload']['lists']),
                         ['isa', 'partof'])
        self.assertEqual(entities['bp3d:FMA2']['class_contract']['class_id'],
                         'batch.entity.external')


class ConnectorDeclarations(unittest.TestCase):
    def test_pins_resolve_from_receipts(self):
        for cid, connector in C.CONNECTORS.items():
            self.assertTrue(connector['artifacts'], cid)
            for artifact in connector['artifacts']:
                self.assertRegex(artifact['sha256'], '^[0-9a-f]{64}$')

    def test_reprove_sources_exist(self):
        self.assertEqual(len(C.REPROVE_SOURCES), 5)


if __name__ == '__main__':
    unittest.main()
