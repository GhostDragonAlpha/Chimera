"""INTAKE-MUSCLE lane tests: connector declarations resolve from receipts, the
two adapters run on their real pinned bytes (sha256-pinned by the download
receipts, so the magic victims below are deterministic), and the
preregistered falsifier (a corrupted row quarantines exactly itself) is
exercised end-to-end by patching one value inside the xlsx bytes in memory."""
import io
import re
import unittest
import zipfile
from pathlib import Path

from tools.science_funnel.adapters import ADAPTERS
from tools.science_funnel.batch import connectors as C

DATA = Path(__file__).resolve().parents[1] / 'data'
GUIMARAES = DATA / 'guimaraes_arch' / 'AJPA-190-e70329-s001.xlsx'
OKU = DATA / 'oku_bipedal' / '42003_2021_1831_MOESM2_ESM.xlsx'

GUIMARAES_SPECIES = {'Pan_troglodytes', 'Gorilla_gorilla', 'Pongo_abelii',
                     'Hylobates_lar', 'Symphalangus_syndactylus', 'Macaca_mulatta'}

# numeric <v> carrying a fraction or exponent; shared-string indexes are
# pure integers and must never be selected as corruption victims
_NUMERIC = re.compile(r'<v>(\d+\.\d+(?:[Ee][-+]?\d+)?|\d+[Ee][-+]?\d+)</v>')


def _patch_zip(source, member, mutator):
    """Rebuild the xlsx with one worksheet XML passed through `mutator`."""
    archive = zipfile.ZipFile(io.BytesIO(Path(source).read_bytes()))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as out:
        for name in archive.namelist():
            raw = archive.read(name)
            if name == member:
                raw = mutator(raw.decode('utf-8')).encode('utf-8')
            out.writestr(name, raw)
    return buffer.getvalue()


class MuscleConnectorDeclarations(unittest.TestCase):
    def test_lane_connectors_merge_by_id(self):
        for cid in ('guimaraes_arch', 'oku_bipedal'):
            self.assertIn(cid, C.CONNECTORS)
            connector = C.CONNECTORS[cid]
            self.assertTrue(connector['artifacts'], cid)
            for artifact in connector['artifacts']:
                self.assertRegex(artifact['sha256'], '^[0-9a-f]{64}$')
            staged = DATA / connector['data_dir'] / connector['artifacts'][0]['id']
            self.assertTrue(staged.is_file(), staged)

    def test_adapters_self_registered(self):
        self.assertIn('guimaraes_arch', ADAPTERS)
        self.assertIn('oku_bipedal_series', ADAPTERS)


class GuimaraesAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = ADAPTERS['guimaraes_arch'](GUIMARAES.read_bytes(),
                                              {'source': {}}, Path('.'))
        cls.records = [r for r in cls.rows if 'refusal' not in r]
        cls.rejections = [r for r in cls.rows if 'refusal' in r]

    def test_record_shape_and_counts(self):
        self.assertGreater(len(self.records), 1500)
        for row in self.records:
            self.assertEqual(row['record_type'], 'measurement')
            self.assertEqual(row['class_contract'],
                             {'class_id': 'batch.property.measurement', 'version': 1})
            payload = row['payload']
            self.assertIsInstance(payload['value_si'], float)
            self.assertIn(payload['unit_si'], ('m', 'm2', 'kg', 'rad'))

    def test_species_tags_preserved_on_every_record(self):
        for row in self.records:
            species = row['payload']['conditions']['species']
            self.assertIn(species, GUIMARAES_SPECIES)

    def test_macaca_mulatta_present_with_specimen(self):
        macaca = [r for r in self.records
                  if r['payload']['conditions']['species'] == 'Macaca_mulatta']
        self.assertGreater(len(macaca), 200)
        self.assertTrue(all(r['payload']['conditions']['specimen_id'].startswith('127')
                            for r in macaca))

    def test_source_typos_quarantine_visibly(self):
        codes = {r['refusal']['code'] for r in self.rejections}
        self.assertIn('pcsa_closure_violation', codes)
        self.assertIn('mass_additivity_violation', codes)
        # zero-PCSA Pongo rows refuse on positivity, never silently admit
        self.assertIn('nonpositive_value', codes)

    def test_corrupted_row_quarantines_exactly_itself(self):
        """Preregistered falsifier: corrupting one fascicle length (the first
        numeric cell of the Macaca sheet = FDL row 2, which carries pennation,
        so its row is worth 9 records on pinned bytes) must quarantine exactly
        that row; the row count is otherwise unchanged (no silent drops)."""
        corrupted = _patch_zip(
            GUIMARAES, 'xl/worksheets/sheet7.xml',
            lambda xml: xml.replace(
                '<v>' + _NUMERIC.search(xml).group(1) + '</v>',
                '<v>0.404040404</v>', 1))
        rows = ADAPTERS['guimaraes_arch'](corrupted, {'source': {}}, Path('.'))
        records = [r for r in rows if 'refusal' not in r]
        rejections = [r for r in rows if 'refusal' in r]
        # row-level count identity: the corrupted row's 9 records collapse
        # into exactly 1 rejection; admitted_rows + rejections is unchanged
        self.assertEqual(len(records), len(self.records) - 9)
        self.assertEqual(len(rejections), len(self.rejections) + 1)
        self.assertEqual([r['external_id'] for r in records
                          if ':Macaca_mulatta:FDL:R:' in r['external_id']], [])
        before = [r for r in self.rejections
                  if r['refusal']['code'] == 'pcsa_closure_violation']
        after = [r for r in rejections
                 if r['refusal']['code'] == 'pcsa_closure_violation']
        self.assertEqual(len(after), len(before) + 1)
        new_one = [r for r in after if r['location'] == 'guimaraes:Macaca mulatta:row2']
        self.assertEqual(len(new_one), 1)
        self.assertNotIn('guimaraes:Macaca mulatta:row2',
                         [r['location'] for r in before])


class OkuAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = ADAPTERS['oku_bipedal_series'](OKU.read_bytes(),
                                                  {'source': {}}, Path('.'))
        cls.records = [r for r in cls.rows if 'refusal' not in r]

    def test_series_shape(self):
        self.assertEqual(len(self.records), 40)
        for row in self.records:
            self.assertEqual(row['record_type'], 'series')
            self.assertEqual(row['class_contract'],
                             {'class_id': 'batch.property.series', 'version': 1})
            payload = row['payload']
            self.assertIn(payload['unit_si'], ('N', 'N*m', 'rad'))
            self.assertEqual(payload['x_unit_si'], '1')
            self.assertEqual(len(payload['samples']), 101)
            xs = [s['x'] for s in payload['samples']]
            self.assertTrue(all(b > a for a, b in zip(xs, xs[1:])))
            self.assertIn(payload['conditions']['block'],
                          ('before_alteration', 'after_alteration'))

    def test_units_match_signal_semantics(self):
        by_id = {r['external_id']: r for r in self.records}
        self.assertEqual(by_id['oku2021:Fig3ABC:before_alteration:GRF v']
                         ['payload']['unit_si'], 'N')
        self.assertEqual(by_id['oku2021:Fig3ABC:before_alteration:hip angle']
                         ['payload']['unit_si'], 'rad')
        self.assertEqual(by_id['oku2021:Fig3D:after_alteration:IL']
                         ['payload']['unit_si'], 'N')

    def test_corrupted_sample_quarantines_exactly_its_series(self):
        corrupted = _patch_zip(
            OKU, 'xl/worksheets/sheet1.xml',
            lambda xml: xml.replace(
                '<v>' + _NUMERIC.search(xml).group(1) + '</v>', '<v>NaN</v>', 1))
        rows = ADAPTERS['oku_bipedal_series'](corrupted, {'source': {}}, Path('.'))
        records = [r for r in rows if 'refusal' not in r]
        rejections = [r for r in rows if 'refusal' in r]
        self.assertEqual(len(records), 39)
        self.assertEqual(len(rejections), 1)
        self.assertEqual(rejections[0]['refusal']['code'], 'nonfinite_number')


if __name__ == '__main__':
    unittest.main()
