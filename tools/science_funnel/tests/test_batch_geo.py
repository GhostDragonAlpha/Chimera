"""Intake-geo lane tests (2026-09-17): the preregistered falsifiers on the
REAL pinned bytes, before and independent of the qualifying run
(docs/research/20260917_intake_geo.md).

Falsifier 1: a corrupted row quarantines exactly itself (one bad THOR mean,
one bad soil fraction, one wrong-code GSOD sentinel, one out-of-legend
WorldCover class).
Falsifier 2: the count identity closes per connector with zero silent drops.
Falsifier 3: the integer TIFF reader refuses float bands and out-of-legend
classes; the float reader's behavior is untouched.
Falsifier 4: geo_fetch is idempotent (re-run re-verifies pins, never
re-writes receipts; the tile resolution hits exactly one grid feature).
"""
import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.science_funnel.adapters import ADAPTERS
from tools.science_funnel.batch import connectors as C
from tools.science_funnel.batch.contract import load_registry, run_contract
from tools.science_funnel.common import Refusal, sha
from tools.science_funnel.geo_fetch import PATCH_CENTRE, fetch_gsod, fetch_soranzo, \
    fetch_thor, fetch_worldcover, resolve_tile
from tools.science_funnel import terrain as T

DATA = Path(__file__).resolve().parents[1] / 'data'
THOR_CSV = DATA / 'thor_ucs' / '2 -  UCS.csv'
SORANZO_CSV = DATA / 'vienna_soil' / 'Zenodo_DATA_Soranzo.csv'
GSOD_CSV = DATA / 'noaa_gsod' / '78535011630.csv'
GSOD_README = DATA / 'noaa_gsod' / 'readme.txt'
WC_TIF = DATA / 'esa_worldcover' / 'ESA_WorldCover_10m_2021_v200_N18W066_Map.tif'
WC_GRID = DATA / 'esa_worldcover' / 'esa_worldcover_grid.geojson'


def bundle(file_map):
    """Pipeline-style companion layout: every artifact materialized in one
    dir under its sha256 name; returns (workdir, {name: sha_path})."""
    work = Path(tempfile.mkdtemp(prefix='geo-test-'))
    sha_paths = {}
    for name, src in file_map.items():
        raw = Path(src).read_bytes()
        dest = work / sha(raw)
        dest.write_bytes(raw)
        sha_paths[name] = dest
    return work, sha_paths


LICENSE = ('CC BY 4.0 (Zenodo API metadata license.id=cc-by-4.0, '
           'pinned as artifact)')


def run_thor(csv_bytes):
    work, p = bundle({'csv': THOR_CSV, 'record': DATA / 'thor_ucs'
                      / 'zenodo_record_12687445.json'})
    (work / 'csv').write_bytes(csv_bytes)
    p['csv'].write_bytes(csv_bytes)
    manifest = {'source': {'license': LICENSE}, 'constants': {
        'expected_rows': 48, 'zenodo_record_sha256': p['record'].name}}
    rows = ADAPTERS['thor_ucs_stats'](csv_bytes, manifest, p['csv'])
    return rows


def run_soranzo(csv_bytes):
    work, p = bundle({'csv': SORANZO_CSV, 'record': DATA / 'vienna_soil'
                      / 'zenodo_record_14251191.json'})
    p['csv'].write_bytes(csv_bytes)
    manifest = {'source': {'license': LICENSE}, 'constants': {
        'expected_rows': 1066,
        'zenodo_record_sha256': p['record'].name}}
    return ADAPTERS['vienna_soil_specimens'](csv_bytes, manifest, p['csv'])


def run_gsod(csv_bytes):
    work, p = bundle({'csv': GSOD_CSV, 'readme': GSOD_README})
    p['csv'].write_bytes(csv_bytes)
    manifest = {'source': {}, 'constants': {
        'expected_rows': 359, 'station_id': '78535011630',
        'readme_sha256': p['readme'].name}}
    return ADAPTERS['gsod_daily'](csv_bytes, manifest, p['csv'])


def run_worldcover(tif_path, constants=None):
    manifest = {'source': {'license': 'CC-BY 4.0'}, 'constants': constants or {
        'tile_id': 'N18W066', 'centre_lat': 18.1565, 'centre_lon': -65.735,
        'expected_pixels': 36000}}
    return ADAPTERS['worldcover_centre_class'](tif_path.read_bytes(), manifest,
                                               tif_path)


def split(records_rows):
    return ([r for r in records_rows if 'refusal' not in r],
            [r for r in records_rows if 'refusal' in r])


# ------------------------------------------------- terrain integer reader

def write_uint_tiff(path, grid, bits=8, predictor=1, tile=4, sample_format=1):
    """Encode a small tiled Deflate integer GeoTIFF (the inverse of the
    reader's decode path; predictor differencing is word-wise per sample,
    matching the TIFF 6.0 horizontal-differencing law libtiff/tifffile
    implement)."""
    rows, cols = len(grid), len(grid[0])
    bytes_per = bits // 8
    mask = (1 << bits) - 1
    tiles_across = (cols + tile - 1) // tile
    tiles_down = (rows + tile - 1) // tile
    blobs = []
    for tr in range(tiles_down):
        for tc in range(tiles_across):
            samples = []
            for r in range(tile):
                for c in range(tile):
                    rr, cc = tr * tile + r, tc * tile + c
                    samples.append(grid[rr][cc] if (rr < rows and cc < cols)
                                   else 0)
            if predictor == 2:
                for i in range(len(samples) - 1, 0, -1):
                    if i % tile:  # first sample of each row is absolute
                        samples[i] = (samples[i] - samples[i - 1]) & mask
            blobs.append(zlib.compress(
                struct.pack('<%d%s' % (len(samples), 'BH'[bytes_per - 1]),
                            *samples), 9))
    entries = []  # (tag, typ, count, inline_value_4bytes)
    scale = struct.pack('<3d', 1.0 / 12000, 1.0 / 12000, 1.0)
    tie = struct.pack('<6d', 0.0, 0.0, 0.0, -66.0, 21.0, 0.0)
    for tag, value in ((256, cols), (257, rows), (258, bits), (259, 8),
                       (277, 1), (284, 1), (317, predictor), (322, tile),
                       (323, tile), (339, sample_format)):
        entries.append((tag, 3, 1, struct.pack('<H', value) + b'\0\0'))
    if len(blobs) == 1:
        entries.append((324, 4, 1, struct.pack('<I', 0)))  # patched below
        entries.append((325, 4, 1, struct.pack('<I', len(blobs[0]))))
    ifd_size = 2 + 12 * (len(entries)
                         + (0 if len(blobs) == 1 else 2)) + 4
    extra_base = 8 + ifd_size
    if len(blobs) == 1:
        blob_base = extra_base + len(scale) + len(tie)
    else:
        blob_base = (extra_base + 8 * len(blobs) + len(scale) + len(tie))
    if len(blobs) > 1:
        offs, pos = [], blob_base
        for blob in blobs:
            offs.append(pos)
            pos += len(blob)
        entries.append((324, 4, len(offs), struct.pack('<I', extra_base)))
        entries.append((325, 4, len(blobs),
                        struct.pack('<I', extra_base + 4 * len(offs))))
        tile_offsets = struct.pack('<%dI' % len(offs), *offs)
        tile_counts = struct.pack('<%dI' % len(blobs),
                                  *[len(b) for b in blobs])
        tail = tile_offsets + tile_counts + scale + tie
    else:
        entries[-2] = (324, 4, 1, struct.pack('<I', blob_base))
        tail = scale + tie
    entries.sort(key=lambda e: e[0])
    raw = bytearray(b'II' + struct.pack('<HI', 42, 8))
    raw += struct.pack('<H', len(entries))
    for tag, typ, count, value in entries:
        raw += struct.pack('<HHI', tag, typ, count) + value
    raw += struct.pack('<I', 0)
    raw += tail
    for blob in blobs:
        raw += blob
    Path(path).write_bytes(bytes(raw))


class TerrainIntegerReader(unittest.TestCase):
    """Falsifier 3: the integer reader refuses float assumptions and agrees
    bit-exactly with tifffile on integer bands; the float reader is frozen."""

    def test_uint8_predictor1_round_trip(self):
        grid = [[(r * 7 + c * 3) % 256 for c in range(10)] for r in range(9)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'u8.tif'
            write_uint_tiff(path, grid, bits=8, predictor=1)
            samples = [(r, c) for r in range(9) for c in range(10)]
            mine = T.sample_grid_int(str(path), samples)
            import tifffile
            with tifffile.TiffFile(str(path)) as tif:
                arr = tif.pages[0].asarray()
            for r, c in samples:
                self.assertEqual(mine[(r, c)], grid[r][c])
                self.assertEqual(mine[(r, c)], int(arr[r, c]))

    def test_uint8_predictor2_round_trip(self):
        grid = [[(r * 31 + c * 17) % 256 for c in range(9)] for r in range(9)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'u8p2.tif'
            write_uint_tiff(path, grid, bits=8, predictor=2)
            mine = T.sample_grid_int(str(path), [(r, c) for r in range(9)
                                                 for c in range(9)])
            import tifffile
            with tifffile.TiffFile(str(path)) as tif:
                arr = tif.pages[0].asarray()
            for r in range(9):
                for c in range(9):
                    self.assertEqual(mine[(r, c)], grid[r][c])
                    self.assertEqual(mine[(r, c)], int(arr[r, c]))

    def test_uint16_round_trip(self):
        grid = [[(r * 3000 + c * 555) % 65536 for c in range(7)] for r in range(6)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'u16.tif'
            write_uint_tiff(path, grid, bits=16, predictor=2)
            mine = T.sample_grid_int(str(path), [(r, c) for r in range(6)
                                                 for c in range(7)])
            import tifffile
            with tifffile.TiffFile(str(path)) as tif:
                arr = tif.pages[0].asarray()
            for r in range(6):
                for c in range(7):
                    self.assertEqual(mine[(r, c)], grid[r][c])
                    self.assertEqual(mine[(r, c)], int(arr[r, c]))

    def test_float_band_refuses(self):
        """A float32 GeoTIFF must REFUSE the integer reader: no float
        assumption is ever silently coerced into a class/integer value."""
        from tools.science_funnel.tests.test_terrain import write_tiff
        grid = [[1.5 * r + c for c in range(6)] for r in range(5)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'f32.tif'
            write_tiff(path, grid, tile=4)
            with self.assertRaises(Refusal) as caught:
                T.sample_grid_int(str(path), [(0, 0)])
            self.assertEqual(caught.exception.code,
                             'terrain_int_reader_refuses_float_band')
            # the float reader still reads it: untouched behavior
            values = T.sample_grid(str(path), [(0, 0)], (-1e6, 1e6))
            self.assertEqual(values[(0, 0)], 1.5 * 0 + 0)

    def test_outside_legend_refuses(self):
        grid = [[10, 20], [30, 250]]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'legend.tif'
            write_uint_tiff(path, grid, bits=8)
            with self.assertRaises(Refusal) as caught:
                T.sample_grid_int(str(path), [(1, 1)], allowed={10, 20, 30})
            self.assertEqual(caught.exception.code, 'terrain_class_outside_legend')
            self.assertEqual(T.sample_grid_int(str(path), [(0, 0)],
                                               allowed={10, 20, 30})[(0, 0)], 10)

    def test_rowcol_area_edge_snap(self):
        gt = {'lat0': 21.0, 'lon0': -66.0, 'd_lat': 1.0 / 12000,
              'd_lon': 1.0 / 12000}
        row, col, edge = T.rowcol_area(gt, 18.1565, -65.735)
        self.assertEqual((row, col), (34122, 3180))
        self.assertTrue(edge)   # the patch centre sits exactly on pixel edges


# ------------------------------------------------------------- THOR rocks

class ThorOnRealBytes(unittest.TestCase):
    def setUp(self):
        self.rows = run_thor(THOR_CSV.read_bytes())
        self.records, self.quarantined = split(self.rows)

    def test_count_identity_zero_drops(self):
        self.assertEqual(len(self.records), 48)
        self.assertEqual(len(self.quarantined), 0)
        self.assertEqual(len(self.records) + len(self.quarantined), 48)

    def test_value_is_exact_mpa_to_pa(self):
        import csv
        import io
        rows = list(csv.DictReader(io.StringIO(
            THOR_CSV.read_bytes().decode('utf-8-sig'), newline='')))
        by_id = {r['external_id']: r for r in self.records}
        for row in rows:
            record = by_id['thor:ucs:' + row['Class'] + ':' + row['Lithologic group']]
            mean = float(row['Mean'])
            self.assertEqual(record['payload']['value_si'], mean * 1e6)
            self.assertEqual(record['payload']['unit_si'], 'Pa')
            self.assertEqual(record['payload']['source_unit'], 'MPa')
            self.assertTrue(any('ucs_unit_megapascal_assumed' in u
                                for u in record['unknowns']))

    def test_corrupted_row_quarantines_exactly_itself(self):
        raw = THOR_CSV.read_bytes().decode('utf-8')
        needle = 'Class I,Sedimentary,3698,26.05'
        self.assertEqual(raw.count(needle), 1)
        rows = run_thor(raw.replace(needle, 'Class I,Sedimentary,3698,99900.0',
                                    1).encode())
        records, quarantined = split(rows)
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0]['location'], 'csv_record:2')
        self.assertEqual(quarantined[0]['refusal']['code'], 'value_outside_envelope')
        self.assertEqual(len(records), 47)
        self.assertNotIn('thor:ucs:Class I:Sedimentary',
                         [r['external_id'] for r in records])


# --------------------------------------------------------- Vienna soil lab

class SoranzoOnRealBytes(unittest.TestCase):
    def setUp(self):
        self.rows = run_soranzo(SORANZO_CSV.read_bytes())
        self.records, self.quarantined = split(self.rows)

    def test_count_identity_empty_rows_quarantine(self):
        self.assertEqual(len(self.records), 777)
        self.assertEqual(len(self.quarantined), 289)
        self.assertEqual({q['refusal']['code'] for q in self.quarantined},
                         {'no_measured_values'})
        self.assertEqual(len(self.records) + len(self.quarantined), 1066)

    def test_families_carry_source_units_and_absent_never_zero(self):
        by_id = {r['external_id']: r for r in self.records}
        specimen = by_id['soranzo:specimen:2']
        self.assertEqual(specimen['payload']['atterberg_percent']['wL'], 29.2)
        self.assertEqual(specimen['payload']['grading_indices'],
                         {'CU': 19.1, 'CC': 1.7})
        # tests not run on this specimen are absent, never zero
        self.assertNotIn('shear_kPa', specimen['payload'])
        self.assertNotIn('shear_deg', specimen['payload'])
        self.assertNotIn('permeability_m_per_s', specimen['payload'])
        self.assertTrue(any('per_column_units_not_declared_in_pinned_source_'
                            'bytes' in u for u in specimen['unknowns']))

    def test_corrupted_cell_quarantines_exactly_its_row(self):
        raw = SORANZO_CSV.read_bytes().decode('utf-8-sig')
        lines = raw.splitlines()
        target = None
        for index, line in enumerate(lines):
            if line.startswith(',0.0,2.5,49.0,43.0,5.5,'):
                target = index
                break
        self.assertIsNotNone(target)
        self.assertEqual(target, 1)  # the first data row
        lines[target] = lines[target].replace(',43.0,5.5,', ',43.0,150.0,', 1)
        rows = run_soranzo(('\r\n'.join(lines) + '\r\n').encode('utf-8'))
        records, quarantined = split(rows)
        self.assertEqual(len(quarantined), 290)  # 289 empty + this one
        self.assertEqual(quarantined[0]['location'], 'csv_record:%d' % (target + 1))
        self.assertEqual(quarantined[0]['refusal']['code'],
                         'value_outside_envelope')
        self.assertEqual(quarantined[0]['refusal']['detail'], 'Cl=150.0')
        self.assertEqual(len(records), 776)
        self.assertNotIn('soranzo:specimen:2',
                         [r['external_id'] for r in records])


# ------------------------------------------------------------------- GSOD

class GsodOnRealBytes(unittest.TestCase):
    def setUp(self):
        self.rows = run_gsod(GSOD_CSV.read_bytes())
        self.records, self.quarantined = split(self.rows)

    def test_count_identity_and_nodata_totals(self):
        self.assertEqual(len(self.records), 359)
        self.assertEqual(len(self.quarantined), 0)
        nodata = {}
        for record in self.records:
            for column in record['payload']['nodata']:
                nodata[column] = nodata.get(column, 0) + 1
        self.assertEqual(nodata, {'SNDP': 359, 'GUST': 106, 'STP': 31,
                                  'VISIB': 9, 'WDSP': 5, 'MXSPD': 5,
                                  'PRCP': 3, 'SLP': 1})
        self.assertEqual(sum(nodata.values()), 519)

    def test_unique_dates_station_and_units(self):
        dates = [r['payload']['date'] for r in self.records]
        self.assertEqual(len(set(dates)), 359)
        self.assertEqual(dates[0], '2024-01-01')
        self.assertEqual(dates[-1], '2024-12-24')
        for record in self.records:
            self.assertEqual(record['payload']['station_id'], '78535011630')
            self.assertRegex(record['payload']['flags']['FRSHTT'], r'^[01]{6}$')

    def test_stp_truncation_carried_as_asserted(self):
        stp_days = [r for r in self.records
                    if 'STP' in r['payload']['pressure_mb']]
        self.assertEqual(len(stp_days), 328)
        for record in stp_days:
            value = record['payload']['pressure_mb']['STP']
            self.assertLess(value, 100.0)
            self.assertTrue(any('stp_renders_below_100_mb' in u
                                for u in record['unknowns']))

    def test_wrong_code_sentinel_quarantines_exactly_itself(self):
        """TEMP = 99.99 is a canonical all-9s rendering of ANOTHER column's
        missing code: it must not nodata, not admit, just quarantine its row
        (preregistered falsifier, refined pre-run from TEMP 999.9 -- which is
        TEMP's own clipped rendering and correctly nodatas)."""
        raw = GSOD_CSV.read_bytes().decode('utf-8-sig')
        lines = raw.splitlines()
        import csv as _csv
        import io as _io
        for index, line in enumerate(lines):
            if '"2024-06-01"' in line:
                fields = next(_csv.reader(_io.StringIO(line, newline='')))
                self.assertEqual(fields[1], '2024-06-01')
                fields[6] = '99.99'
                out = _io.StringIO(newline='')
                _csv.writer(out, lineterminator='\r\n').writerow(fields)
                lines[index] = out.getvalue().rstrip('\r\n')
                break
        else:
            self.fail('2024-06-01 row not found')
        rows = run_gsod(('\r\n'.join(lines) + '\r\n').encode('utf-8'))
        records, quarantined = split(rows)
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0]['refusal']['code'],
                         'gsod_unrecognized_sentinel_code')
        self.assertEqual(len(records), 358)
        self.assertNotIn('gsod:78535011630:2024-06-01',
                         [r['external_id'] for r in records])

    def test_readme_law_accepted_sets(self):
        accepted, canonical = readme_law()
        self.assertEqual(canonical, {'99.99', '999.9', '9999.9'})
        self.assertEqual(accepted['TEMP'], {'9999.9', '999.9'})
        self.assertEqual(accepted['STP'], {'9999.9', '999.9'})
        self.assertEqual(accepted['PRCP'], {'99.99'})
        self.assertEqual(accepted['MXSPD'], {'999.9'})   # wrap-garbled '999.'
        self.assertEqual(accepted['VISIB'], {'999.9'})


def readme_law():
    from tools.science_funnel.adapters_geo import readme_sentinel_law
    return readme_sentinel_law(GSOD_README.read_bytes().decode('cp1252'))


# ---------------------------------------------------------- ESA WorldCover

class WorldCoverOnRealBytes(unittest.TestCase):
    def setUp(self):
        self.rows = run_worldcover(WC_TIF)
        self.records, self.quarantined = split(self.rows)

    def test_count_identity(self):
        self.assertEqual(len(self.records), 5)
        self.assertEqual(len(self.quarantined), 0)
        by_id = {r['external_id']: r for r in self.records}
        self.assertEqual(set(by_id), {
            'worldcover:v200:2021:N18W066:grid_columns',
            'worldcover:v200:2021:N18W066:grid_rows',
            'worldcover:v200:2021:N18W066:pixel_scale_deg',
            'worldcover:v200:2021:N18W066:file_bytes',
            'worldcover:v200:2021:N18W066:centre'})

    def test_centre_class_and_window(self):
        centre = {r['external_id']: r for r in self.records}[
            'worldcover:v200:2021:N18W066:centre']
        payload = centre['payload']
        self.assertEqual(payload['class_code'], 80)
        self.assertEqual(payload['class_label'], 'Permanent water bodies')
        self.assertEqual((payload['pixel_row'], payload['pixel_col']),
                         (34122, 3180))
        self.assertTrue(payload['on_pixel_edge'])
        self.assertEqual(payload['window_3x3_class_codes'],
                         [[80, 80, 80], [80, 80, 80], [80, 80, 80]])
        self.assertEqual(payload['raster_type'], 'RasterPixelIsArea')
        self.assertEqual(payload['sample_format'], 'uint8')
        self.assertAlmostEqual(payload['pixel_scale_deg'],
                               8.333333333333333e-05, places=15)
        self.assertEqual(payload['tiepoint_lon_lat'], [-66.0, 21.0])

    def test_grid_metadata_records(self):
        by_id = {r['external_id']: r for r in self.records}
        self.assertEqual(by_id['worldcover:v200:2021:N18W066:grid_columns']
                         ['payload']['value_si'], 36000.0)
        self.assertEqual(by_id['worldcover:v200:2021:N18W066:file_bytes']
                         ['payload']['value_si'], 4604997.0)
        self.assertEqual(by_id['worldcover:v200:2021:N18W066:pixel_scale_deg']
                         ['payload']['unit_si'], 'degree')

    def test_nodata_pixel_refuses_legend(self):
        """A nodata pixel (class 0, the ocean) is NOT a class: the reader must
        refuse it against the legend, on the real bytes."""
        info = T.int_grid_info(str(WC_TIF))
        probes = [(r, c) for r in range(0, 400, 100) for c in range(0, 400, 100)]
        values = T.sample_grid_int(str(WC_TIF), probes)
        nodata = [pos for pos, value in values.items() if value == 0]
        self.assertTrue(nodata, 'expected ocean nodata pixels in the probes')
        with self.assertRaises(Refusal) as caught:
            T.sample_grid_int(str(WC_TIF), nodata[:1],
                              allowed=set(range(10, 101)))
        self.assertEqual(caught.exception.code, 'terrain_class_outside_legend')

    def test_tile_identity_mismatch_refuses(self):
        with self.assertRaises(Refusal) as caught:
            run_worldcover(WC_TIF, constants={
                'tile_id': 'N18W067', 'centre_lat': 18.1565,
                'centre_lon': -65.735, 'expected_pixels': 36000})
        self.assertEqual(caught.exception.code, 'worldcover_tile_identity')


# --------------------------------------------------- class contract checks

def contract_record(class_id, payload):
    return {'id': 'data.assertion.' + 'a' * 64,
            'source': {'id': 'x', 'release': 'r', 'license': 'l', 'url': 'u'},
            'artifact': {'id': 'f', 'sha256': 'b' * 64},
            'provenance': {'source_id': 'data.source.' + 'c' * 64},
            'payload': payload, 'label': 'fixture'}


CTX = {'blob_pins': {'b' * 64}, 'known_ids': {'data.source.' + 'c' * 64}}


class ClassContracts(unittest.TestCase):
    """The authored contracts refuse a corrupted record EXACTLY itself."""

    def test_soil_specimen_envelope(self):
        registry = load_registry()
        contract = registry['batch.observation.soil_specimen']
        good = contract_record('batch.observation.soil_specimen',
                               {'n_measured_values': 2,
                                'gradation_percent': {'Gr': 2.5, 'Cl': 5.5}})
        bad = contract_record('batch.observation.soil_specimen',
                              {'n_measured_values': 1,
                               'gradation_percent': {'Cl': 150.0}})
        bad['id'] = 'data.assertion.' + 'd' * 64
        result = run_contract(contract, [good, bad], dict(CTX))
        self.assertEqual(result['passed'], 1)
        self.assertEqual([f['id'] for f in result['failures']], [bad['id']])
        self.assertEqual(result['failures'][0]['check'], 'numeric_tree_range')

    def test_gsod_day_station_and_envelope(self):
        registry = load_registry()
        contract = registry['batch.observation.gsod_day']
        good = contract_record('batch.observation.gsod_day',
                               {'station_id': '78535011630',
                                'air_temp_f': {'TEMP': 79.1},
                                'latitude_deg': 18.2552,
                                'longitude_deg': -65.6411,
                                'elevation_m': 10.1})
        bad = contract_record('batch.observation.gsod_day',
                              {'station_id': '99999999999',
                               'air_temp_f': {'TEMP': 79.1},
                               'latitude_deg': 18.2552,
                               'longitude_deg': -65.6411,
                               'elevation_m': 10.1})
        bad['id'] = 'data.assertion.' + 'd' * 64
        result = run_contract(contract, [good, bad], dict(CTX))
        self.assertEqual(result['passed'], 1)
        self.assertEqual([f['id'] for f in result['failures']], [bad['id']])
        self.assertEqual(result['failures'][0]['check'], 'field_in')

    def test_worldcover_class_label_vocabulary(self):
        registry = load_registry()
        contract = registry['batch.property.worldcover_class']
        good = contract_record('batch.property.worldcover_class',
                               {'unit_si': 'dimensionless', 'class_code': 80,
                                'class_label': 'Permanent water bodies',
                                'sample_format': 'uint8', 'centre_lat': 18.1565,
                                'centre_lon': -65.735})
        bad = contract_record('batch.property.worldcover_class',
                              {'unit_si': 'dimensionless', 'class_code': 55,
                               'class_label': 'Ocean', 'sample_format': 'uint8',
                               'centre_lat': 18.1565, 'centre_lon': -65.735})
        bad['id'] = 'data.assertion.' + 'd' * 64
        result = run_contract(contract, [good, bad], dict(CTX))
        self.assertEqual(result['passed'], 1)
        self.assertEqual({f['check'] for f in result['failures']}, {'field_in'})
        self.assertEqual([f['id'] for f in result['failures']], [bad['id']])


# ----------------------------------------------------------- fetch idempotency

class FetchIdempotency(unittest.TestCase):
    """Falsifier 4: re-running the fetch re-verifies every pin, downloads
    nothing and rewrites no receipt; the tile resolution hits exactly one
    grid feature."""

    def test_rerun_is_offline_idempotent(self):
        for fetch in (fetch_thor, fetch_soranzo, fetch_gsod, fetch_worldcover):
            result = fetch()
            self.assertFalse(result['downloaded'], fetch.__name__)
            self.assertFalse(result['receipt_written'], fetch.__name__)

    def test_tile_resolution_exactly_one_hit(self):
        import json
        gj = json.loads(WC_GRID.read_bytes())
        hits = []
        for feature in gj['features']:
            ring = feature['geometry']['coordinates'][0]
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            if (min(xs) <= PATCH_CENTRE[1] <= max(xs)
                    and min(ys) <= PATCH_CENTRE[0] <= max(ys)):
                hits.append(feature['properties']['ll_tile'])
        self.assertEqual(hits, ['N18W066'])
        self.assertEqual(resolve_tile(WC_GRID.read_bytes(), *PATCH_CENTRE),
                         'N18W066')


# ------------------------------------------------------------- lane wiring

class LaneWiring(unittest.TestCase):
    def test_connectors_merged_by_autoload(self):
        for cid in ('thor_rock_ucs', 'vienna_soil_lab', 'noaa_gsod_station_year',
                    'esa_worldcover_n18w066'):
            self.assertIn(cid, C.CONNECTORS)
            for artifact in C.CONNECTORS[cid]['artifacts']:
                self.assertRegex(artifact['sha256'], '^[0-9a-f]{64}$')

    def test_data_dirs_in_search_dirs_and_reprove_untouched(self):
        for folder in ('thor_ucs', 'vienna_soil', 'noaa_gsod', 'esa_worldcover'):
            self.assertIn(folder, C.SEARCH_DIRS)
        self.assertEqual(len(C.REPROVE_SOURCES), 5)

    def test_new_contracts_carry_rule0(self):
        registry = load_registry()
        for cid in ('batch.observation.soil_specimen',
                    'batch.observation.gsod_day',
                    'batch.property.worldcover_class'):
            for field in ('statement', 'prediction', 'falsifier'):
                self.assertTrue(registry[cid][field].strip(), f'{cid}:{field}')
            self.assertTrue(registry[cid]['checks'])

    def test_adapters_registered(self):
        for name in ('thor_ucs_stats', 'vienna_soil_specimens', 'gsod_daily',
                     'worldcover_centre_class'):
            self.assertIn(name, ADAPTERS)


class HeavyCrossCheck(unittest.TestCase):
    """The two decode orders must agree bit-exactly on the REAL tile. This
    decodes the full 36,000 x 36,000 page with tifffile (~1.3 GB); it ran
    once before the qualifying run and is re-runnable via
    CHIMERA_GEO_HEAVY=1. Default suite stays fast."""

    @unittest.skipUnless(os.environ.get('CHIMERA_GEO_HEAVY') == '1',
                         'full-page decode; run with CHIMERA_GEO_HEAVY=1')
    def test_stdlib_reader_matches_tifffile_full_decode(self):
        import tifffile
        window = [(34000 + r, 3000 + c) for r in range(300) for c in range(300)]
        mine = T.sample_grid_int(str(WC_TIF), window)
        with tifffile.TiffFile(str(WC_TIF)) as tif:
            arr = tif.pages[0].asarray()
        for r, c in window:
            self.assertEqual(mine[(r, c)], int(arr[r, c]), f'({r},{c})')


if __name__ == '__main__':
    unittest.main()
