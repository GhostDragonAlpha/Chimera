"""Intake-life lane tests (2026-09-17): the preregistered falsifiers on the
REAL pinned bytes, before and independent of the qualifying run.

Falsifier 1: a -999 sentinel (any rendering) NEVER becomes a measurement --
the adapter quarantines/nodata-guards it, and the class contract's positive
field_range flags a sentinel-derived value if the guard is ever removed.
Falsifier 2: re-deriving the Macaca subtree from the pinned zip is
byte-identical (idempotent rebuild).
Falsifier 3: a Macaca binomial not resolving against the subtree quarantines
the row's records.
"""
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path

from tools.science_funnel.adapters import ADAPTERS
from tools.science_funnel.adapters_life import pantheria_cell
from tools.science_funnel.batch import connectors as C
from tools.science_funnel.batch.contract import load_registry, run_contract
from tools.science_funnel.common import Refusal, sha
from tools.science_funnel.life_fetch import extract_macaca_subtree

DATA = Path(__file__).resolve().parents[1] / 'data'


def trait_record(value_si, record_id='data.assertion.' + 'a' * 64):
    return {'id': record_id,
            'source': {'id': 'pantheria.1.0.wr05', 'release': 'r',
                       'license': 'CC0', 'url': 'u'},
            'artifact': {'id': 'ECOL_90_184.zip', 'sha256': 'b' * 64},
            'provenance': {'source_id': 'data.source.' + 'c' * 64},
            'payload': {'value_si': value_si, 'unit_si': 'W'},
            'label': 'fixture'}


CTX = {'blob_pins': {'b' * 64}, 'known_ids': {'data.source.' + 'c' * 64}}


def pantheria_records(zip_bytes, names_blob, workdir):
    names_pin = sha(names_blob)
    (workdir / names_pin).write_bytes(names_blob)
    manifest = {'source': {}, 'constants': {'o2_calorific_J_per_mL': 20.1,
                                            'macaca_names_sha256': names_pin}}
    primary = workdir / 'primary'
    primary.write_bytes(b'')
    return ADAPTERS['pantheria_traits'](zip_bytes, manifest, primary)


def build_zip(rows_text):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('PanTHERIA_1-0_WR05_Aug2008.txt', rows_text)
    return buffer.getvalue()


HEADER = ('MSW05_Order\tMSW05_Family\tMSW05_Genus\tMSW05_Species\tMSW05_Binomial\t'
          '5-1_AdultBodyMass_g\t18-1_BasalMetRate_mLO2hr\t5-2_BasalMetRateMass_g\n')

NAMES_TSV = ('tax_id\tname_txt\tunique_name\tname_class\n'
             '9539\tMacaca\t\tscientific name\n'
             '9544\tMacaca mulatta\t\tscientific name\n'
             '9544\trhesus macaque\t\tgenbank common name\n'
             '9545\tMacaca nemestrina\t\tscientific name\n'
             '9553\tMacaca silenus\t\tscientific name\n')

MEASURED_ROW = ('Primates\tCercopithecidae\tMacaca\tmulatta\tMacaca mulatta\t'
                '6455.19\t2241.85\t6225.0\n')
SENTINEL_ROW = ('Primates\tCercopithecidae\tMacaca\tnemestrina\tMacaca nemestrina\t'
                '7820.78\t-999.00\t-999.00\n')
SENTINEL_ROW_INT = ('Primates\tCercopithecidae\tMacaca\tsilenus\tMacaca silenus\t'
                    '5995.25\t-999\t-999\n')
UNRESOLVED_ROW = ('Primates\tCercopithecidae\tMacaca\tfictitia\tMacaca fictitia\t'
                  '5000.0\t100.0\t5000.0\n')


class SentinelLaw(unittest.TestCase):
    """Falsifier 1: -999 never becomes a measurement, and the class refuses it
    even if the adapter guard is removed."""

    def test_cell_renderings(self):
        self.assertEqual(pantheria_cell('-999.00'), (None, 'sentinel_-999'))
        self.assertEqual(pantheria_cell('-999'), (None, 'sentinel_-999'))
        self.assertEqual(pantheria_cell('-999.0'), (None, 'sentinel_-999'))
        self.assertEqual(pantheria_cell(''), (None, 'empty'))
        value, status = pantheria_cell('6.12')
        self.assertEqual((value, status), (6.12, 'measured'))
        with self.assertRaises(Refusal):
            pantheria_cell('not-a-number')

    def test_sentinel_rows_never_emit_measurements(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = pantheria_records(
                build_zip(HEADER + MEASURED_ROW + SENTINEL_ROW + SENTINEL_ROW_INT),
                NAMES_TSV.encode(), Path(tmp))
        records = [r for r in rows if 'refusal' not in r]
        self.assertEqual(len(rows), len(records))  # nothing quarantined
        species = {r['external_id']: r for r in records
                   if r['record_type'] == 'entity'}
        measurements = {r['external_id']: r for r in records
                        if r['record_type'] == 'measurement'}
        # sentinel BMR columns emit NO BMR record; measured adult masses DO
        # admit -- a sentinel in one column never nodatas the whole row
        bmr_records = [ext for ext in measurements if ext.endswith(':basal_metabolic_rate')]
        self.assertEqual(bmr_records, ['pantheria:Macaca mulatta:basal_metabolic_rate'])
        self.assertEqual(set(measurements), {
            'pantheria:Macaca mulatta:adult_body_mass_g',
            'pantheria:Macaca mulatta:basal_metabolic_rate',
            'pantheria:Macaca nemestrina:adult_body_mass_g',
            'pantheria:Macaca silenus:adult_body_mass_g'})
        nemestrina = species['pantheria:Macaca nemestrina']
        self.assertIn('nodata:basal_met_rate_mLO2hr:sentinel_-999',
                      nemestrina['unknowns'])
        self.assertEqual(nemestrina['payload']['trait_status']
                         ['basal_met_rate_mLO2hr'], 'sentinel_-999')
        silenus = species['pantheria:Macaca silenus']
        self.assertIn('nodata:basal_met_rate_mLO2hr:sentinel_-999',
                      silenus['unknowns'])

    def test_contract_refuses_sentinel_derived_value(self):
        """If a -999 sentinel EVER reached a measurement record, its converted
        value (-5.58 W) must be flagged by the class contract -- exactly it."""
        registry = load_registry()
        contract = registry['batch.property.pantheria_trait']
        good = trait_record(12.5011)
        corrupted = trait_record(-999.0 * 20.1 / 3600.0, 'data.assertion.' + 'd' * 64)
        result = run_contract(contract, [good, corrupted], dict(CTX))
        self.assertEqual(result['records'], 2)
        self.assertEqual(result['passed'], 1)
        self.assertEqual([f['id'] for f in result['failures']], [corrupted['id']])
        self.assertEqual(result['failures'][0]['check'], 'field_range')

    def test_real_bytes_sentinel_never_reaches_measurement(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = pantheria_records(
                (DATA / 'pantheria' / 'ECOL_90_184.zip').read_bytes(),
                (DATA / 'ncbi_taxdmp' / 'macaca_names.tsv').read_bytes(),
                Path(tmp))
        records = [r for r in rows if 'refusal' not in r]
        measurements = [r for r in records if r['record_type'] == 'measurement']
        self.assertTrue(measurements)
        for record in measurements:
            self.assertGreater(record['payload']['value_si'], 0.0)


class PantheriaOnRealBytes(unittest.TestCase):
    def setUp(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.rows = pantheria_records(
                (DATA / 'pantheria' / 'ECOL_90_184.zip').read_bytes(),
                (DATA / 'ncbi_taxdmp' / 'macaca_names.tsv').read_bytes(),
                Path(tmp))
        self.records = [r for r in self.rows if 'refusal' not in r]
        self.quarantined = [r for r in self.rows if 'refusal' in r]

    def test_counts_and_zero_silent_drops(self):
        species = [r for r in self.records if r['record_type'] == 'entity']
        bmr = [r for r in self.records if r['external_id'].endswith(
            ':basal_metabolic_rate')]
        mass = [r for r in self.records if r['external_id'].endswith(
            ':adult_body_mass_g')]
        self.assertEqual(len(species), 5416)
        self.assertEqual(len(bmr), 573)
        self.assertEqual(len(mass), 3542)
        self.assertEqual(len(self.records) + sum(
            len(q.get('records', [1])) for q in self.quarantined), len(self.rows))

    def test_mulatta_bmr_converts_and_resolves(self):
        """The prediction's anchor: the one measured Macaca BMR record. The
        expected watts derive from the actual pinned cell, never a guess."""
        import csv
        import io
        with zipfile.ZipFile(DATA / 'pantheria' / 'ECOL_90_184.zip') as archive:
            table = archive.read('PanTHERIA_1-0_WR05_Aug2008.txt').decode('utf-8-sig')
        rows = list(csv.reader(io.StringIO(table, newline=''), delimiter='\t'))
        col = {name: i for i, name in enumerate(rows[0])}
        mulatta = [r for r in rows[1:]
                   if r[col['MSW05_Binomial']] == 'Macaca mulatta']
        self.assertEqual(len(mulatta), 1)
        cell = float(mulatta[0][col['18-1_BasalMetRate_mLO2hr']])
        self.assertNotEqual(cell, -999.0)

        bmr = [r for r in self.records
               if r['external_id'] == 'pantheria:Macaca mulatta:basal_metabolic_rate']
        self.assertEqual(len(bmr), 1)
        payload = bmr[0]['payload']
        self.assertAlmostEqual(payload['value_si'], cell * 20.1 / 3600.0, places=12)
        self.assertEqual(payload['unit_si'], 'W')
        self.assertEqual(payload['original']['value'], cell)
        self.assertEqual(payload['conversion']['o2_calorific_J_per_mL'], 20.1)
        self.assertIn('assumption', payload['conversion'])
        self.assertTrue(any('o2_calorific_assumed' in u
                            for u in bmr[0]['unknowns']))
        species = [r for r in self.records
                   if r['external_id'] == 'pantheria:Macaca mulatta']
        taxonomy = species[0]['payload']['taxonomy']
        self.assertEqual(taxonomy['provider'], 'ncbi_taxdmp.macaca_subtree')
        self.assertEqual(taxonomy['tax_id'], 9544)

    def test_every_macaca_resolves_against_subtree(self):
        macaca = [r for r in self.records if r['record_type'] == 'entity'
                  and r['payload']['species_tags']['MSW05_Genus'] == 'Macaca']
        self.assertEqual(len(macaca), 21)
        for record in macaca:
            self.assertIsNotNone(record['payload']['taxonomy'], record['external_id'])

    def test_mass_uses_convert(self):
        mass = [r for r in self.records
                if r['external_id'] == 'pantheria:Macaca mulatta:adult_body_mass_g']
        payload = mass[0]['payload']
        self.assertEqual(payload['unit_si'], 'kg')
        self.assertAlmostEqual(payload['value_si'], 6455.19e-3, places=9)


class UnresolvedNameQuarantines(unittest.TestCase):
    """Falsifier 3: a Macaca binomial outside the subtree quarantines."""

    def test_unresolved_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = pantheria_records(
                build_zip(HEADER + MEASURED_ROW + UNRESOLVED_ROW),
                NAMES_TSV.encode(), Path(tmp))
        quarantined = [r for r in rows if 'refusal' in r]
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0]['refusal']['code'], 'macaca_name_unresolved')
        records = [r for r in rows if 'refusal' not in r]
        self.assertEqual(len(records), 3)  # mulatta species + 2 measurements


class TaxdmpOnRealBytes(unittest.TestCase):
    def test_subtree_shape(self):
        manifest = {'source': {}, 'constants': {
            'macaca_names_sha256': sha(
                (DATA / 'ncbi_taxdmp' / 'macaca_names.tsv').read_bytes())}}
        with tempfile.TemporaryDirectory() as tmp:
            primary = Path(tmp) / 'nodes'
            primary.write_bytes((DATA / 'ncbi_taxdmp' / 'macaca_nodes.tsv').read_bytes())
            (Path(tmp) / manifest['constants']['macaca_names_sha256']).write_bytes(
                (DATA / 'ncbi_taxdmp' / 'macaca_names.tsv').read_bytes())
            rows = ADAPTERS['ncbi_taxdmp_macaca'](
                primary.read_bytes(), manifest, primary)
        self.assertEqual(len(rows), 43)
        ranks = {r['payload']['rank'] for r in rows}
        self.assertEqual(ranks, {'genus', 'species', 'subspecies', 'no rank'})
        roots = [r for r in rows if r['payload']['subtree_root']]
        self.assertEqual([r['payload']['scientific_name'] for r in roots], ['Macaca'])
        self.assertEqual(roots[0]['payload']['tax_id'], 9539)
        mulatta = [r for r in rows if r['payload']['scientific_name'] == 'Macaca mulatta']
        self.assertEqual(len(mulatta), 1)
        self.assertEqual(mulatta[0]['payload']['tax_id'], 9544)
        for row in rows:
            self.assertEqual(row['class_contract']['class_id'], 'batch.entity.ncbi_taxon')

    def test_rebuild_is_byte_identical(self):
        """Falsifier 2: re-deriving the subtree from the pinned zip reproduces
        the pinned derived bytes (idempotent rebuild)."""
        with tempfile.TemporaryDirectory() as tmp:
            result = extract_macaca_subtree(
                DATA / 'ncbi_taxdmp' / 'taxdmp.zip', Path(tmp))
        self.assertEqual(result['nodes_sha256'], sha(
            (DATA / 'ncbi_taxdmp' / 'macaca_nodes.tsv').read_bytes()))
        self.assertEqual(result['names_sha256'], sha(
            (DATA / 'ncbi_taxdmp' / 'macaca_names.tsv').read_bytes()))


class RheaOnRealBytes(unittest.TestCase):
    def test_species_map(self):
        rows = ADAPTERS['rhea_chebi_smiles'](
            (DATA / 'rhea' / 'rhea-chebi-smiles.tsv').read_bytes(), {'source': {}},
            Path('.'))
        self.assertEqual(len(rows), 14318)
        quarantined = [r for r in rows if 'refusal' in r]
        self.assertEqual(quarantined, [])
        external = [r['external_id'] for r in rows]
        self.assertEqual(len(set(external)), 14249)  # 69 duplicate identities
        for row in rows[:200]:
            self.assertEqual(row['class_contract']['class_id'],
                             'batch.entity.rhea_chebi_species')
            self.assertEqual(row['payload']['id_scheme'], 'chebi')

    def test_bad_rows_quarantine(self):
        rows = ADAPTERS['rhea_chebi_smiles'](
            b'CHEBI:7\tCCO\nnotachebi\tCCC\nCHEBI:20\t\n', {'source': {}}, Path('.'))
        quarantined = [r['refusal']['code'] for r in rows if 'refusal' in r]
        self.assertEqual(sorted(quarantined), ['chebi_id_syntax', 'missing_text'])


class LaneWiring(unittest.TestCase):
    def test_connectors_merged_by_autoload(self):
        for cid in ('pantheria_1_0', 'ncbi_taxdmp_macaca', 'rhea_reactions'):
            self.assertIn(cid, C.CONNECTORS)
            for artifact in C.CONNECTORS[cid]['artifacts']:
                self.assertRegex(artifact['sha256'], '^[0-9a-f]{64}$')

    def test_search_dirs_extended_reprove_untouched(self):
        for folder in ('pantheria', 'ncbi_taxdmp', 'rhea'):
            self.assertIn(folder, C.SEARCH_DIRS)
        self.assertEqual(len(C.REPROVE_SOURCES), 5)

    def test_new_contracts_carry_rule0(self):
        registry = load_registry()
        for cid in ('batch.entity.pantheria_species', 'batch.property.pantheria_trait',
                    'batch.entity.ncbi_taxon', 'batch.entity.rhea_chebi_species'):
            for field in ('statement', 'prediction', 'falsifier'):
                self.assertTrue(registry[cid][field].strip(), f'{cid}:{field}')
            self.assertTrue(registry[cid]['checks'])


if __name__ == '__main__':
    unittest.main()
