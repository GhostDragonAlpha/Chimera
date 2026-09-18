"""Intake-appearance lane tests (2026-09-18): the preregistered falsifiers on
the REAL pinned bytes, before and independent of the qualifying run.

Falsifier 1 (Goldenberg): a corrupted cell quarantines exactly its row; NA
cells never become measurements; the percent->fraction conversion is flagged
by the class contract if the /100 law is ever dropped.
Falsifier 2 (PHYLACINE): re-extracting the trait table from the pinned zip is
byte-identical (idempotent derivation); a binomial disagreeing with its tags
quarantines exactly that row; mass never admits missing or out-of-envelope.
Falsifier 3 (USGS): a spectrum without a wavelength pairing provable from the
pinned bytes quarantines (never guessed); the -1.23e34 sentinel never becomes
a value; a non-monotonic axis quarantines exactly the spectra on that grid;
the deferred full bundle never counts as data.
"""
import csv
import io
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path

from tools.science_funnel.adapters import ADAPTERS
from tools.science_funnel.appearance_fetch import extract_phylacine_trait_table
from tools.science_funnel.batch import connectors as C
from tools.science_funnel.batch.contract import load_registry, run_contract
from tools.science_funnel.common import sha

DATA = Path(__file__).resolve().parents[1] / 'data'

GOLD_PIN = sha((DATA / 'goldenberg_reflectance' / 'total_dataset.csv').read_bytes())
PHY_PIN = sha((DATA / 'phylacine' / 'phylacine_trait_table.csv').read_bytes())
CTX = {'blob_pins': {GOLD_PIN, PHY_PIN},
       'known_ids': {'data.source.' + 'c' * 64}}


def goldenberg_records(csv_bytes):
    return ADAPTERS['goldenberg_rows'](csv_bytes, {'source': {}}, Path('.'))


def phylacine_records(csv_bytes):
    return ADAPTERS['phylacine_species'](csv_bytes, {'source': {}}, Path('.'))


def splib_records(zip_bytes, chapters):
    manifest = {'source': {}, 'constants': {'chapters': chapters,
                                            'deferred': {
                                                'path': 'usgs_splib07.zip',
                                                'bytes': 5479324354,
                                                'url': 'https://example.invalid',
                                                'cause': 'test'}}}
    return ADAPTERS['splib07_chapter_spectra'](zip_bytes, manifest, Path('.'))


class GoldenbergOnRealBytes(unittest.TestCase):
    def setUp(self):
        raw = (DATA / 'goldenberg_reflectance' / 'total_dataset.csv').read_bytes()
        self.rows = goldenberg_records(raw)
        self.records = [r for r in self.rows if 'refusal' not in r]
        self.quarantined = [r for r in self.rows if 'refusal' in r]

    def test_counts_and_zero_silent_drops(self):
        entities = [r for r in self.records if r['record_type'] == 'entity']
        measurements = [r for r in self.records if r['record_type'] == 'measurement']
        self.assertEqual(len(entities), 441)
        self.assertEqual(len(measurements), 1781)
        self.assertEqual(self.quarantined, [])
        self.assertEqual(len(self.records) + len(self.quarantined), len(self.rows))

    def test_mammals_are_the_fur_anchor(self):
        mammals = [r for r in self.records if r['record_type'] == 'entity'
                   and r['payload']['taxon_class'] == 'Mammalia']
        self.assertEqual(len(mammals), 94)
        for record in mammals:
            self.assertIn('goldenberg:', record['external_id'])

    def test_na_cells_never_become_measurements(self):
        for record in self.records:
            if record['record_type'] == 'measurement':
                self.assertIsNotNone(record['payload']['value_si'])
        egg = [r for r in self.records if r['record_type'] == 'measurement'
               and r['payload']['conditions']['cell_kind'] == 'egg']
        self.assertEqual(len(egg), 76 * 4)
        na_entities = [r for r in self.records if r['record_type'] == 'entity'
                       and any(u.startswith('nodata:B2.')
                               for u in r['unknowns'])]
        self.assertTrue(na_entities)

    def test_fractions_carry_the_declared_law(self):
        one = next(r for r in self.records if r['record_type'] == 'measurement')
        payload = one['payload']
        self.assertEqual(payload['unit_si'], '1')
        self.assertAlmostEqual(payload['value_si'],
                               payload['original']['value'] / 100.0, places=12)
        self.assertEqual(payload['conversion']['law'], 'fraction = percent / 100')

    def test_corrupted_cell_quarantines_exactly_its_row(self):
        raw = (DATA / 'goldenberg_reflectance' / 'total_dataset.csv') \
            .read_bytes().decode('utf-8-sig')
        lines = raw.splitlines(keepends=True)
        good = lines[1]
        corrupted = good.replace(good.split(',')[4], '1e6', 1)
        rows = goldenberg_records(
            ('\n'.join([','.join(raw.splitlines()[:1]), good, corrupted, good])
             + '\n').encode())
        quarantined = [r for r in rows if 'refusal' in r]
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0]['refusal']['code'],
                         'reflectance_outside_envelope')
        entities = [r for r in rows if 'refusal' not in r
                    and r['record_type'] == 'entity']
        self.assertEqual(len(entities), 2)  # the two good rows only

    def test_unknown_class_quarantines_its_row(self):
        raw = (DATA / 'goldenberg_reflectance' / 'total_dataset.csv') \
            .read_bytes().decode('utf-8-sig')
        lines = raw.splitlines()
        header, good = lines[0], lines[1]
        cells = good.split(',')
        cells[12] = 'Aves_from_space'
        rows = goldenberg_records(('\n'.join([header, good, ','.join(cells)])
                                   + '\n').encode())
        quarantined = [r for r in rows if 'refusal' in r]
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0]['refusal']['code'],
                         'goldenberg_class_outside_vocabulary')
        admitted = [r for r in rows if 'refusal' not in r]
        single_row = goldenberg_records(
            ('\n'.join([lines[0], good]) + '\n').encode())
        self.assertEqual(len(admitted), len(single_row))


class GoldenbergContractFalsifier(unittest.TestCase):
    def test_dropped_scaling_law_is_flagged(self):
        """If the /100 law is ever dropped, raw percents (4.5..116.5) land
        outside [-0.05, 1.2] and field_range flags exactly those records."""
        registry = load_registry()
        contract = registry['batch.property.goldenberg_reflectance']

        def record(value_si, rid='data.assertion.' + 'a' * 64):
            return {'id': rid,
                    'source': {'id': 'zenodo.goldenberg.15084543', 'release': 'r',
                               'license': 'CC BY 4.0', 'url': 'u'},
                    'artifact': {'id': 'total_dataset.csv', 'sha256': GOLD_PIN},
                    'provenance': {'source_id': 'data.source.' + 'c' * 64},
                    'payload': {'value_si': value_si, 'unit_si': '1'},
                    'label': 'fixture'}

        good = record(0.5214561301)
        dropped = record(52.14561301, 'data.assertion.' + 'd' * 64)
        result = run_contract(contract, [good, dropped], dict(CTX))
        self.assertEqual(result['records'], 2)
        self.assertEqual(result['passed'], 1)
        self.assertEqual([f['id'] for f in result['failures']], [dropped['id']])
        self.assertEqual(result['failures'][0]['check'], 'field_range')


class PhylacineOnRealBytes(unittest.TestCase):
    def setUp(self):
        self.rows = phylacine_records(
            (DATA / 'phylacine' / 'phylacine_trait_table.csv').read_bytes())
        self.records = [r for r in self.rows if 'refusal' not in r]
        self.quarantined = [r for r in self.rows if 'refusal' in r]

    def test_counts_and_zero_silent_drops(self):
        self.assertEqual(len(self.records), 5831)
        self.assertEqual(self.quarantined, [])
        binomials = [r['payload']['binomial'] for r in self.records]
        self.assertEqual(len(set(binomials)), 5831)

    def test_masses_inside_envelope_and_converted(self):
        for record in self.records:
            payload = record['payload']
            self.assertGreater(payload['mass_g'], 0.0)
            self.assertAlmostEqual(payload['mass_kg'], payload['mass_g'] / 1000.0,
                                   places=12)
            self.assertLessEqual(payload['mass_kg'], 200000.0)

    def test_mulatta_row_derives_from_pinned_bytes(self):
        raw = (DATA / 'phylacine' / 'phylacine_trait_table.csv').read_bytes()
        rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline='')))
        mulatta = [r for r in rows if r['Binomial.1.2'] == 'Macaca_mulatta']
        self.assertEqual(len(mulatta), 1)
        record = next(r for r in self.records
                      if r['payload']['binomial'] == 'Macaca_mulatta')
        self.assertAlmostEqual(record['payload']['mass_kg'],
                               float(mulatta[0]['Mass.g']) / 1000.0, places=12)
        self.assertEqual(record['payload']['iucn_status'],
                         mulatta[0]['IUCN.Status.1.2'])

    def test_rebuild_is_byte_identical(self):
        """Falsifier 2: re-extracting the table from the pinned zip reproduces
        the pinned derived bytes (idempotent derivation)."""
        with tempfile.TemporaryDirectory() as tmp:
            result = extract_phylacine_trait_table(
                DATA / 'phylacine' / 'PHYLACINE_1.2.1.zip', Path(tmp))
        self.assertEqual(result['table_sha256'], sha(
            (DATA / 'phylacine' / 'phylacine_trait_table.csv').read_bytes()))
        self.assertEqual(result['notes_sha256'], sha(
            (DATA / 'phylacine' / 'phylacine_release_notes.pdf').read_bytes()))

    def test_binomial_disagreement_quarantines_exactly_its_row(self):
        raw = (DATA / 'phylacine' / 'phylacine_trait_table.csv').read_bytes() \
            .decode('utf-8-sig')
        lines = raw.splitlines()
        header, good = lines[0], lines[1]
        cells = good.split(',')
        cells[0] = 'Wrongus_wrongus'
        rows = phylacine_records(('\n'.join([header, good, ','.join(cells)])
                                  + '\n').encode())
        quarantined = [r for r in rows if 'refusal' in r]
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0]['refusal']['code'],
                         'binomial_disagrees_with_tags')
        admitted = [r for r in rows if 'refusal' not in r]
        good_records = phylacine_records(
            ('\n'.join([lines[0], good]) + '\n').encode())
        self.assertEqual(len(admitted), len(good_records))


class Splib07OnRealBytes(unittest.TestCase):
    def setUp(self):
        self.rows = splib_records(
            (DATA / 'usgs_splib07_subset' / 'ASCIIdata_splib07a.zip').read_bytes(),
            ['ChapterV_Vegetation', 'ChapterS_SoilsAndMixtures'])
        self.records = [r for r in self.rows if 'refusal' not in r]
        self.quarantined = [r for r in self.rows if 'refusal' in r]

    def test_counts_pairing_and_axis_law(self):
        spectra = [r for r in self.records
                   if r['class_contract']['class_id']
                   == 'batch.series.splib07_spectrum']
        deferred = [r for r in self.records
                    if r['class_contract']['class_id']
                    == 'batch.deferred.usgs_splib07_full']
        self.assertEqual(len(spectra) + len(self.quarantined), 495)
        self.assertEqual(len(deferred), 1)
        axis = [q for q in self.quarantined
                if q['refusal']['code'] == 'spectrum_axis_not_increasing']
        self.assertEqual(len(axis), 1)
        self.assertIn('Bacterial_mat_YNP-B1', axis[0]['location'])
        aviris = [r for r in spectra
                  if r['payload']['instrument_family'] == 'AVIRIS']
        self.assertEqual(len(aviris), 38)
        for record in aviris:
            self.assertTrue(any('aviris_1996_grid' in u
                                for u in record['unknowns']))
        for record in spectra:
            samples = record['payload']['samples']
            self.assertTrue(all(samples[i]['x'] < samples[i + 1]['x']
                                for i in range(len(samples) - 1)))

    def test_sentinel_never_becomes_a_value(self):
        for record in self.records:
            if record['record_type'] != 'series':
                continue
            for sample in record['payload']['samples']:
                self.assertNotEqual(sample['value'], -1.23e34)
                self.assertGreaterEqual(sample['value'], 0.0)
                self.assertLessEqual(sample['value'], 2.5)

    def test_nodata_channels_are_counted_not_interpolated(self):
        with_nodata = [r for r in self.records if r['record_type'] == 'series'
                       and r['payload']['nodata_channel_count'] > 0]
        self.assertTrue(with_nodata)
        record = with_nodata[0]['payload']
        self.assertLess(len(record['samples']),
                        record['channel_count'])
        self.assertTrue(record['nodata_wavelength_runs_um'])

    def test_deferred_full_bundle_never_counts_as_data(self):
        deferred = next(r for r in self.records
                        if r['class_contract']['class_id']
                        == 'batch.deferred.usgs_splib07_full')
        self.assertEqual(deferred['payload']['status'], 'deferred')
        self.assertEqual(deferred['payload']['license'], 'CC0 1.0')
        self.assertEqual(deferred['payload']['size_bytes'], 5479324354.0)
        self.assertIn('bytes_not_downloaded', deferred['unknowns'])


class Splib07SyntheticGrids(unittest.TestCase):
    """Falsifier 3 on constructed bytes: unpaired grids refuse, envelope
    violations poison exactly their spectrum, non-monotonic grids quarantine."""

    def setUp(self):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr(
                'ASCIIdata_splib07a/splib07a_Wavelengths_BECK_Beckman_0.2-'
                '3.0_microns.txt',
                ' splib07a Record=1: wavelengths\n' +
                '\n'.join(f'{w}' for w in (0.5, 1.0, 1.5, 2.0)) + '\n')
            archive.writestr(
                'ASCIIdata_splib07a/splib07a_Wavelengths_AVIRIS_1996_0.37-'
                '2.5_microns.txt',
                ' splib07a Record=2: wavelengths\n' +
                '\n'.join(f'{w}' for w in (0.5, 0.4, 0.6)) + '\n')
            archive.writestr(
                'ASCIIdata_splib07a/ChapterT_Test/'
                'splib07a_Good_Sample_BECKa_AREF.txt',
                ' splib07a Record=10: Good_Sample BECKa AREF\n'
                '0.1\n0.2\n0.3\n0.4\n')
            archive.writestr(
                'ASCIIdata_splib07a/ChapterT_Test/'
                'splib07a_Nodata_Sample_BECKa_AREF.txt',
                ' splib07a Record=11: Nodata_Sample BECKa AREF\n'
                '0.1\n-1.2300000e+034\n0.3\n0.4\n')
            archive.writestr(
                'ASCIIdata_splib07a/ChapterT_Test/'
                'splib07a_Hot_Sample_BECKa_AREF.txt',
                ' splib07a Record=12: Hot_Sample BECKa AREF\n'
                '0.1\n0.2\n9.9\n0.4\n')
            archive.writestr(
                'ASCIIdata_splib07a/ChapterT_Test/'
                'splib07a_Broken_Sample_BECKa_AREF.txt',
                ' splib07a Record=13: Broken_Sample BECKa AREF\n'
                '0.1\n0.2\n0.3\n0.4\n0.5\n')
            archive.writestr(
                'ASCIIdata_splib07a/ChapterT_Test/'
                'splib07a_Aviris_Sample_AVIRISb_AREF.txt',
                ' splib07a Record=14: Aviris_Sample AVIRISb AREF\n'
                '0.1\n0.2\n0.3\n')
        self.rows = splib_records(buffer.getvalue(), ['ChapterT_Test'])

    def test_pairing_envelope_and_axis_laws(self):
        records = [r for r in self.rows if 'refusal' not in r]
        quarantined = [r for r in self.rows if 'refusal' in r]
        codes = sorted(q['refusal']['code'] for q in quarantined)
        # hot (envelope) + broken (unpaired) + aviris (axis) quarantine
        self.assertEqual(codes, ['spectrum_axis_not_increasing',
                                 'spectrum_grid_unpaired',
                                 'spectrum_value_outside_envelope'])
        spectra = [r for r in records if r['record_type'] == 'series']
        self.assertEqual(len(spectra), 2)  # good + nodata
        good = next(r for r in spectra
                    if r['payload']['sample_name'] == 'Good_Sample')
        self.assertEqual(good['payload']['nodata_channel_count'], 0)
        nodata = next(r for r in spectra
                      if r['payload']['sample_name'] == 'Nodata_Sample')
        self.assertEqual(nodata['payload']['nodata_channel_count'], 1)
        self.assertEqual(nodata['payload']['nodata_wavelength_runs_um'],
                         [[1.0, 1.0]])
        self.assertEqual(len(nodata['payload']['samples']), 3)
        # plus exactly one deferred record
        deferred = [r for r in records if r['record_type'] == 'entity']
        self.assertEqual(len(deferred), 1)


class LaneWiring(unittest.TestCase):
    def test_lane_adapters_register_under_connectors_first_import(self):
        """The circular-import trap: a fresh interpreter whose FIRST funnel
        import is the connectors package (the spawn-worker order) must still
        see the lane adapters in the shared registry."""
        import json
        import subprocess
        import sys
        code = ("from tools.science_funnel.batch import connectors as C; "
                "from tools.science_funnel.adapters import ADAPTERS; "
                "import json; print(json.dumps({'c': 'goldenberg_reflectance' "
                "in C.CONNECTORS, 'a': {'goldenberg_rows', 'phylacine_species',"
                " 'splib07_chapter_spectra'} <= set(ADAPTERS)}))")
        result = subprocess.run([sys.executable, '-B', '-c', code],
                                capture_output=True, text=True, timeout=120)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertTrue(payload['c'], result.stderr)
        self.assertTrue(payload['a'], result.stderr)

    def test_connectors_merged_by_autoload(self):
        for cid in ('goldenberg_reflectance', 'phylacine_1_2_1',
                    'usgs_splib07_subset'):
            self.assertIn(cid, C.CONNECTORS)
            for artifact in C.CONNECTORS[cid]['artifacts']:
                self.assertRegex(artifact['sha256'], '^[0-9a-f]{64}$')

    def test_new_contracts_carry_rule0(self):
        registry = load_registry()
        for cid in ('batch.observation.goldenberg_taxon',
                    'batch.property.goldenberg_reflectance',
                    'batch.entity.phylacine_species',
                    'batch.series.splib07_spectrum',
                    'batch.deferred.usgs_splib07_full'):
            for field in ('statement', 'prediction', 'falsifier'):
                self.assertTrue(registry[cid][field].strip(), f'{cid}:{field}')
            self.assertTrue(registry[cid]['checks'])

    def test_usgs_b_zip_is_attachment_not_data(self):
        connector = C.CONNECTORS['usgs_splib07_subset']
        roles = {a['id']: a.get('role', 'data') for a in connector['artifacts']}
        self.assertEqual(roles['ASCIIdata_splib07a.zip'], 'data')
        self.assertEqual(roles['ASCIIdata_splib07b.zip'], 'attachment')

    def test_apply_patches_rotates_shards_below_ceiling(self):
        """The 100 MB per-file ceiling falsifier on the serial writer: one
        batch carrying a bulk family far larger than the rotation target must
        rotate shards per object (start-of-run-only rotation wrote a 125 MB
        shard during this lane's first apply and was refused by push)."""
        import json as _json
        import tempfile
        from unittest.mock import patch as _patch
        from tools.creature_graph import batch_qualify as B

        def obj(index, fill):
            return {'id': 'data.assertion.' + f'{index:064x}',
                    'kind': 'reference_entity', 'name': 'f' * fill}

        patches = [{'payload': {
            'objects': [obj(i, 4096) for i in range(200)],
            'relations': []}}]
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / 'project_program.json'
            program.write_text(_json.dumps({'objects': [], 'relations': []}))
            (Path(td) / 'records').mkdir()
            with _patch.object(B, 'AUTHORED_PROGRAM', program), \
                    _patch.object(B, 'ROTATE_BYTES', 64 * 1024):
                result = B.apply_patches(object(), patches)
            self.assertEqual(result['objects_added'], 200)
            self.assertTrue(len(result['shards']) >= 2, result['shards'])
            sizes = [(p.name, p.stat().st_size)
                     for p in (Path(td) / 'records').glob('records_*.json')]
            for name, size in sizes:
                self.assertLess(size, 128 * 1024,
                                f'{name} at {size} bytes would breach rotation')
            stored = set()
            for shard in (Path(td) / 'records').glob('records_*.json'):
                payload = _json.loads(shard.read_text())
                stored.update(o['id'] for o in payload['objects'])
            self.assertEqual(len(stored), 200)
            # idempotent second apply: zero new objects, no shard growth
            before = {p.name: p.stat().st_size
                      for p in (Path(td) / 'records').glob('records_*.json')}
            with _patch.object(B, 'AUTHORED_PROGRAM', program), \
                    _patch.object(B, 'ROTATE_BYTES', 64 * 1024):
                result2 = B.apply_patches(object(), patches)
            self.assertEqual(result2['objects_added'], 0)
            after = {p.name: p.stat().st_size
                     for p in (Path(td) / 'records').glob('records_*.json')}
            self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
