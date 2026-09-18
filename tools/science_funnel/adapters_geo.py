"""Geoscience lane funnels (INTAKE-GEO, 2026-09-17).

Four adapters, one lane:
  thor_ucs_stats          -- THOR rock strength database (Zenodo 12687445,
                             CC BY 4.0): 47 lithologic-group sigma_UCS summary
                             rows -> measurement records in SI Pa.
  vienna_soil_specimens   -- Austrian geotechnical lab dataset (Zenodo
                             14251191, CC BY 4.0): 1,066 specimen rows ->
                             observation records, one per specimen, families
                             keyed by the source-conventional unit.
  gsod_daily              -- NOAA GSOD station-year 78535011630 2024 (US Gov):
                             359 station-days -> observation records; the
                             missing-data law is PARSED from the pinned
                             readme.txt, never hardcoded.
  worldcover_centre_class -- ESA WorldCover v200 2021 tile N18W066 (CC BY 4.0,
                             declared in the tile itself): the land-cover
                             class at the Cayo Santiago patch centre through
                             terrain.sample_grid_int (uint8/int16 reader;
                             float bands refuse).

Lane adapters are merged into the shared ADAPTERS dict by the adapters_*
auto-load in adapters.py (GEO_ADAPTERS below); the shared module is never
edited by a lane.

RULE 0 for this lane (preregistered in docs/research/20260917_intake_geo.md
BEFORE this file existed; the per-class contracts in the authored store
restate it mechanically):
  STATEMENT -- a geoscience record is admittable only with pinned-byte
  provenance, source-declared (or source-anchored) units, values inside a
  declared physical envelope, and explicit nodata; a categorical class must
  sit inside the legend the source itself declares.
  PREDICTION -- 47 THOR rows, 1,066 soil specimens, 359 GSOD days and the one
  WorldCover centre class admit clean (1,477 records, 0 quarantined); the
  count identity closes for every connector.
  FALSIFIER -- one corrupted row quarantines exactly itself; the count
  identity fetched == admitted + quarantined closes with zero silent drops;
  the integer TIFF reader refuses float bands and out-of-legend classes.
"""
import csv
import io
import re
from datetime import date

from .adapters import ADAPTERS, rejection
from .common import Refusal, draft, loads, number, require, text
from .terrain import (SAMPLE_FORMAT_UINT, gdal_metadata_items, geotransform,
                      geokeys, int_grid_info, rowcol_area, sample_grid_int)
from .units import convert

# ------------------------------------------------------------------- THOR

THOR_COLUMNS = ['Class', 'Lithologic group', 'n', 'Mean', 'Std', '10th',
                '25th', 'Median', '75th', '90th', '75/25', '90/10']
THOR_ROW = re.compile(r'^Class (I|II|III)$')
UCS_ENVELOPE_MPA = (0.1, 1000.0)

THOR_UNKNOWNS = (
    'ucs_unit_megapascal_assumed_source_csv_carries_no_unit_column_'
    'unit_per_companion_paper_haag_schoenbohm_2025',
    'ratio_columns_75_25_and_90_10_omitted_recomputable_from_admitted_'
    'percentiles',
)


def thor_ucs_stats(raw, manifest, path):
    """THOR '2 -  UCS.csv' -> one measurement record per lithologic group.

    The source CSV carries NO unit column: the megapascal attribution is a
    declared assumption on every record (the companion paper's unit and the
    only reading consistent with the 0.1-1000 MPa rock-strength envelope).
    value_si is the exact x1e6 conversion into pascals; the distribution
    (n, std, percentiles) rides on the record; the derived 75/25 and 90/10
    ratio columns are omitted with a recorded unknown."""
    constants = manifest.get('constants', {})
    expected_rows = constants.get('expected_rows')
    record_pin = constants.get('zenodo_record_sha256')
    require(record_pin, 'missing_text', 'constants.zenodo_record_sha256')
    record = loads(path.parent.joinpath(record_pin).read_bytes())
    license_id = (record.get('metadata') or {}).get('license', {}).get('id', '')
    require(license_id.lower() in manifest['source']['license'].lower(),
            'license_claim_unanchored', license_id)

    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    fields = reader.fieldnames
    require(fields == THOR_COLUMNS, 'csv_bad_header', str(fields))
    rows = list(reader)
    if expected_rows:
        require(len(rows) == expected_rows, 'thor_row_count_changed',
                str(len(rows)) + ' rows != pinned ' + str(expected_rows))

    def summary(row, column):
        value = number(row[column])
        require(UCS_ENVELOPE_MPA[0] <= value <= UCS_ENVELOPE_MPA[1],
                'value_outside_envelope', column + '=' + row[column].strip())
        return value

    out = []
    for index, row in enumerate(rows, 2):
        try:
            thor_class = text(row['Class'], 'Class')
            require(THOR_ROW.match(thor_class), 'thor_class_outside_vocabulary',
                    thor_class)
            group = text(row['Lithologic group'], 'Lithologic group')
            n = number(row['n'])
            require(n == int(n) and 1 <= n <= 1e6, 'thor_sample_count_invalid',
                    row['n'])
            mean = summary(row, 'Mean')
            std = summary(row, 'Std')
            percentiles = {name: summary(row, column) for name, column in
                           (('p10', '10th'), ('p25', '25th'), ('median', 'Median'),
                            ('p75', '75th'), ('p90', '90th'))}
            converted = convert(mean, 'MPa', 'stress')
            payload = {'value_si': converted['value_si'],
                       'unit_si': converted['unit_si'],
                       'source_value_mpa': mean, 'source_unit': 'MPa',
                       'std_mpa': std, 'percentiles_mpa': percentiles,
                       'n_samples': int(n),
                       'subject': 'lithology ' + group + ' (' + thor_class + ')',
                       'conditions': {
                           'database': 'THOR rock strength database '
                                       '(Zenodo 12687445)',
                           'quantity': 'sigma_UCS uniaxial compressive '
                                       'strength, lithologic-group summary',
                           'statistic': 'mean of published UCS measurements '
                                        '1980-2024, as compiled by the source'},
                       'unit_attribution': 'megapascal per the companion paper '
                                           '(Haag & Schoenbohm 2025, EPSL 660, '
                                           '119364); the pinned CSV bytes carry '
                                           'no unit column'}
            rec = draft('thor:ucs:' + thor_class + ':' + group, 'measurement',
                        payload, label='THOR sigma_UCS mean, ' + group
                        + ' (' + thor_class + ')',
                        unknowns=THOR_UNKNOWNS)
            rec['class_contract'] = {'class_id': 'batch.property.measurement',
                                    'version': 1}
            out.append(rec)
        except Refusal as exc:
            out.append(rejection('csv_record:' + str(index), exc))
    require(any('refusal' not in row for row in out), 'empty_capture',
            'all rows refused')
    return out


# ------------------------------------------------------------ Vienna soil

# quantity families keyed by the source-conventional unit; the envelopes are
# physical bounds, not tuned bounds (preregistered in the admission doc).
SORANZO_FAMILIES = {
    'gradation_percent': (('Co', 'Gr', 'Sa', 'Si', 'Cl'), 0.0, 100.0),
    'grain_sizes_mm': (('dmax', 'd10', 'd50'), 0.0, 150.0),
    'grading_indices': (('CU', 'CC'), 0.0, 5000.0),
    'proctor_g_per_cm3': (('RHS', 'RHPRUSP'), 0.5, 3.5),
    'proctor_percent': (('WPRUSP',), 0.0, 100.0),
    'atterberg_percent': (('wL', 'wP', 'wS', 'IP'), 0.0, 150.0),
    'state_percent': (('w',), 0.0, 100.0),
    'indices': (('IC', 'IA'), -2.0, 10.0),
    'permeability_m_per_s': (('k10',), 1e-13, 1e-1),
    'shear_kPa': (('c', 'cr'), 0.0, 200.0),
    'shear_deg': (('phi', 'phir'), 0.0, 90.0),
    'coord_lat_deg': (('Latitude',), 40.0, 55.0),
    'coord_lon_deg': (('Longitude',), 5.0, 25.0),
}
SORANZO_COLUMNS = ['Location'] + [c for cols, _, _ in SORANZO_FAMILIES.values()
                                  for c in cols]
SORANZO_UNKNOWNS = (
    'per_column_units_not_declared_in_pinned_source_bytes_families_carry_'
    'source_conventional_units_percent_mm_g_per_cm3_m_per_s_kpa_degree',
    'location_sparse_absent_where_unrecorded',
    'specimen_id_not_pinned_by_source_external_id_is_file_row_order',
)


def vienna_soil_specimens(raw, manifest, path):
    """Zenodo_DATA_Soranzo.csv -> one observation record per lab specimen.

    A row is a specimen: grain-size distribution, Atterberg limits, Proctor,
    permeability and direct-shear results co-measured on one sample. Empty
    cell = the test was not run on this specimen (absent, NEVER zero). The
    pinned bytes carry no unit column; each family key names its
    source-conventional unit and the assumption is declared on every
    record."""
    constants = manifest.get('constants', {})
    expected_rows = constants.get('expected_rows')
    record_pin = constants.get('zenodo_record_sha256')
    require(record_pin, 'missing_text', 'constants.zenodo_record_sha256')
    record = loads(path.parent.joinpath(record_pin).read_bytes())
    license_id = (record.get('metadata') or {}).get('license', {}).get('id', '')
    require(license_id.lower() in manifest['source']['license'].lower(),
            'license_claim_unanchored', license_id)

    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    fields = reader.fieldnames
    require(fields is not None and sorted(fields) == sorted(SORANZO_COLUMNS),
            'csv_bad_header', str(fields))
    rows = list(reader)
    if expected_rows:
        require(len(rows) == expected_rows, 'soranzo_row_count_changed',
                str(len(rows)) + ' rows != pinned ' + str(expected_rows))

    out = []
    for index, row in enumerate(rows, 2):
        try:
            families = {}
            measured = 0
            for family, (columns, low, high) in SORANZO_FAMILIES.items():
                values = {}
                for column in columns:
                    cell = row[column].strip()
                    if cell == '':
                        continue
                    value = number(cell)
                    require(low <= value <= high, 'value_outside_envelope',
                            column + '=' + cell)
                    values[column] = value
                    measured += 1
                if values:
                    families[family] = values
            require(measured >= 1, 'no_measured_values', 'row ' + str(index))
            location = row['Location'].strip()
            payload = {'n_measured_values': measured, **families,
                       'location': location or None}
            rec = draft('soranzo:specimen:' + str(index), 'entity', payload,
                        label='soil specimen, file row ' + str(index)
                        + (', ' + location if location else ''),
                        unknowns=SORANZO_UNKNOWNS)
            rec['class_contract'] = {'class_id': 'batch.observation.soil_specimen',
                                    'version': 1}
            out.append(rec)
        except Refusal as exc:
            out.append(rejection('csv_record:' + str(index), exc))
    require(any('refusal' not in row for row in out), 'empty_capture',
            'all rows refused')
    return out


# ------------------------------------------------------------------- GSOD

GSOD_STATION = '78535011630'
GSOD_GROUPS = {
    'air_temp_f': (('TEMP', 'DEWP', 'MAX', 'MIN'), -80.0, 150.0),
    'pressure_mb': (('SLP', 'STP'), 0.0, 1100.0),
    'wind_knots': (('WDSP', 'MXSPD', 'GUST'), 0.0, 250.0),
    'visibility_miles': (('VISIB',), 0.0, 100.0),
    'precip_inches': (('PRCP', 'SNDP'), 0.0, 30.0),
}
GSOD_COUNT_COLUMNS = ('TEMP', 'DEWP', 'SLP', 'STP', 'VISIB', 'WDSP')
GSOD_MEASURED_COLUMNS = tuple(c for cols, _, _ in GSOD_GROUPS.values()
                              for c in cols)
GSOD_UNIT_ANCHORS = {'TEMP': 'Fahrenheit', 'DEWP': 'Fahrenheit',
                     'MAX': 'Fahrenheit', 'MIN': 'Fahrenheit',
                     'SLP': 'millibars', 'STP': 'millibars',
                     'VISIB': 'miles', 'WDSP': 'knots', 'MXSPD': 'knots',
                     'GUST': 'knots', 'PRCP': 'inches', 'SNDP': 'inches'}
GSOD_FRSHIT = re.compile(r'^[01]{6}$')
GSOD_CANONICAL_CODES = ('99.99', '999.9', '9999.9')


def readme_sentinel_law(readme_text):
    """Parse the missing-data codes and unit anchors out of the pinned GSOD
    readme: the sentinel law is source-anchored, not hardcoded.

    The README's data section gives one `<COL> - ... Missing = <code>` line
    per quantity (MXSPD's code is wrap-garbled to '999.' in the pinned bytes
    and resolves as the unique canonical all-9s code starting with that
    fragment). Documented 6-char codes (9999.9) additionally accept their
    leading-digit-clipped 5-char rendering (999.9): the file ships STP
    missing as 999.9 against a documented 9999.9, and STP's own real values
    render in a 4-wide field -- the README's general all-9s line licenses the
    clipping, but is NOT the operative law (the file carries real 9.9
    visibility/wind values, so a blanket all-9s rule would quarantine real
    rows). Returns ({column: accepted codes}, canonical set)."""
    require('indicates no report or insufficient data' in readme_text,
            'gsod_readme_general_law_missing', 'all-9s sentence')
    accepted_by_column = {}
    for column in GSOD_MEASURED_COLUMNS:
        starts = [m for m in re.finditer(r'^' + column + r' - ', readme_text,
                                         re.MULTILINE)]
        require(starts, 'gsod_readme_law_missing', column)
        window = readme_text[starts[-1].start():starts[-1].start() + 320]
        anchor = GSOD_UNIT_ANCHORS[column]
        require(anchor in window, 'gsod_readme_unit_anchor_missing',
                column + ': ' + anchor)
        match = (re.search(r'Missing\s*=\s*([0-9]+\.[0-9]+)', window)
                 or re.search(r'Missing\s*=\s*\r?\n([0-9]+\.)', window))
        require(match is not None, 'gsod_readme_code_missing', column)
        fragment = match.group(1)
        canonical = [code for code in GSOD_CANONICAL_CODES
                     if code == fragment or code.startswith(fragment)]
        require(len(canonical) == 1, 'gsod_readme_code_ambiguous',
                column + ':' + fragment)
        accepted = {canonical[0]}
        if len(canonical[0]) == 6:
            accepted.add(canonical[0][1:])
        require(accepted <= set(GSOD_CANONICAL_CODES), 'gsod_readme_code_set',
                column + ': ' + str(sorted(accepted)))
        accepted_by_column[column] = accepted
    return accepted_by_column, set(GSOD_CANONICAL_CODES)


def gsod_daily(raw, manifest, path):
    """NOAA GSOD 78535011630 2024 -> one observation record per station-day.

    A cell equal to one of its column's accepted missing codes becomes an
    explicit nodata entry and never a value; a cell equal to a DIFFERENT
    canonical all-9s code (an unrecognized sentinel rendering) quarantines;
    a wrong-code value that is not an all-9s rendering at all quarantines
    only if the physical envelope refuses it. STP is carried as asserted
    with a truncation unknown: the file renders station pressures ~1015.9 mb
    as '015.9' and ships the documented-missing 9999.9 as '999.9'; asserted
    bytes are never 'repaired'."""
    constants = manifest.get('constants', {})
    expected_rows = constants.get('expected_rows')
    station_id = constants.get('station_id') or GSOD_STATION
    readme_pin = constants.get('readme_sha256')
    require(readme_pin, 'missing_text', 'constants.readme_sha256')
    readme = path.parent.joinpath(readme_pin).read_bytes().decode('cp1252')
    accepted_by_column, canonical_codes = readme_sentinel_law(readme)

    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    fields = reader.fieldnames
    require(fields and len(set(fields)) == len(fields), 'csv_bad_header')
    required = (['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'ELEVATION', 'NAME']
                + list(GSOD_MEASURED_COLUMNS)
                + [c + '_ATTRIBUTES' for c in GSOD_COUNT_COLUMNS]
                + ['MAX_ATTRIBUTES', 'MIN_ATTRIBUTES', 'PRCP_ATTRIBUTES',
                   'FRSHTT'])
    missing = [column for column in required if column not in fields]
    require(not missing, 'csv_bad_header', 'missing columns: ' + ','.join(missing))
    rows = list(reader)
    if expected_rows:
        require(len(rows) == expected_rows, 'gsod_row_count_changed',
                str(len(rows)) + ' rows != pinned ' + str(expected_rows))
    seen_dates = set()

    out = []
    for index, row in enumerate(rows, 2):
        try:
            station = text(row['STATION'], 'STATION')
            require(station == station_id, 'gsod_station_changed', station)
            day = text(row['DATE'], 'DATE')
            try:
                parsed = date.fromisoformat(day)
            except ValueError as exc:
                raise Refusal('gsod_bad_date', day) from exc
            require(parsed.isoformat() == day, 'gsod_bad_date', day)
            require(day not in seen_dates, 'duplicate_source_identity', day)
            seen_dates.add(day)
            name = text(row['NAME'], 'NAME')
            lat = number(row['LATITUDE'])
            require(-90.0 <= lat <= 90.0, 'value_outside_envelope', 'LATITUDE')
            lon = number(row['LONGITUDE'])
            require(-180.0 <= lon <= 180.0, 'value_outside_envelope', 'LONGITUDE')
            elevation = number(row['ELEVATION'])
            require(-500.0 <= elevation <= 9000.0, 'value_outside_envelope',
                    'ELEVATION')

            groups = {}
            nodata = {}
            for family, (columns, low, high) in GSOD_GROUPS.items():
                values = {}
                for column in columns:
                    cell = row[column].strip()
                    if cell in accepted_by_column[column]:
                        nodata[column] = 'sentinel_' + cell
                        continue
                    require(cell not in canonical_codes, 'gsod_unrecognized_'
                            'sentinel_code', column + '=' + cell)
                    value = number(cell)
                    require(low <= value <= high, 'value_outside_envelope',
                            column + '=' + cell)
                    values[column] = value
                if values:
                    groups[family] = values
            require(groups, 'no_measured_values', 'row ' + str(index))

            counts = {}
            for column in GSOD_COUNT_COLUMNS:
                cell = row[column + '_ATTRIBUTES'].strip()
                if cell == '':
                    continue
                value = number(cell)
                require(0 <= value <= 31, 'value_outside_envelope',
                        column + '_ATTRIBUTES=' + cell)
                counts[column] = int(value)

            frshtt = text(row['FRSHTT'], 'FRSHTT')
            require(GSOD_FRSHIT.match(frshtt), 'gsod_frshtt_outside_vocabulary',
                    frshtt)
            flags = {'FRSHTT': frshtt,
                     'MAX': row['MAX_ATTRIBUTES'].strip(),
                     'MIN': row['MIN_ATTRIBUTES'].strip(),
                     'PRCP': row['PRCP_ATTRIBUTES'].strip()}

            unknowns = ['gsod_missing_codes_parsed_from_pinned_readme',
                        'wmo_resolution_40_note_carried_from_readme_never_'
                        'resolved']
            stp = groups.get('pressure_mb', {}).get('STP')
            if stp is not None and stp < 100.0:
                unknowns.append('stp_renders_below_100_mb_consistent_with_'
                                'source_field_truncation_of_station_pressure_'
                                'carried_as_asserted')

            payload = {'station_id': station, 'name': name, 'date': day,
                       'latitude_deg': lat, 'longitude_deg': lon,
                       'elevation_m': elevation, **groups,
                       'obs_counts': counts, 'flags': flags,
                       'nodata': nodata, 'n_nodata': len(nodata)}
            rec = draft('gsod:' + station + ':' + day, 'entity', payload,
                        label=name + ' ' + day + ' GSOD daily summary',
                        unknowns=unknowns)
            rec['class_contract'] = {'class_id': 'batch.observation.gsod_day',
                                    'version': 1}
            out.append(rec)
        except Refusal as exc:
            out.append(rejection('csv_record:' + str(index), exc))
    require(any('refusal' not in row for row in out), 'empty_capture',
            'all rows refused')
    return out


# ------------------------------------------------------- ESA WorldCover

WORLDCOVER_LEGEND = {10: 'Tree cover', 20: 'Shrubland', 30: 'Grassland',
                     40: 'Cropland', 50: 'Built-up', 60: 'Bare/sparse vegetation',
                     70: 'Snow and ice', 80: 'Permanent water bodies',
                     90: 'Herbaceous wetland', 95: 'Mangroves',
                     100: 'Moss and lichen'}


def worldcover_centre_class(raw, manifest, path):
    """ESA WorldCover v200 2021 tile -> the land-cover class at the patch
    centre + tile grid metadata measurements.

    The tile id is NOT re-guessed here: it arrives from the connector
    constants (resolved by geo_fetch against the pinned bucket tile index)
    and must match the tile's own embedded product_tile metadata. The class
    legend is parsed from the pinned tile's GDAL metadata -- a class code
    outside that legend refuses at the reader (terrain.sample_grid_int).
    The band must be integer (uint8/int16): a float band refuses; the float
    reader (terrain.sample_grid) is never touched."""
    constants = manifest.get('constants', {})
    tile_id = text(constants.get('tile_id'), 'constants.tile_id')
    centre_lat = number(constants.get('centre_lat'))
    centre_lon = number(constants.get('centre_lon'))
    expected_pixels = constants.get('expected_pixels')

    info = int_grid_info(str(path))
    require(info['sample_format'] == SAMPLE_FORMAT_UINT,
            'worldcover_band_not_unsigned_int', str(info['sample_format']))
    if expected_pixels:
        require(info['width'] == info['height'] == expected_pixels,
                'worldcover_grid_changed', str(info['width']))
    keys = geokeys(str(path))
    require(keys.get(1025) == 1, 'worldcover_raster_type_not_area',
            str(keys.get(1025)))
    require(keys.get(2048) == 4326, 'worldcover_crs_not_epsg4326',
            str(keys.get(2048)))
    items = gdal_metadata_items(str(path))
    require(items.get('product_tile') == tile_id, 'worldcover_tile_identity',
            str(items.get('product_tile')) + ' != ' + tile_id)
    require(items.get('product_crs') == 'EPSG:4326', 'worldcover_crs_metadata',
            str(items.get('product_crs')))
    require(str(items.get('license', '')).startswith('CC-BY 4.0'),
            'worldcover_license_metadata', str(items.get('license')))
    legend = {}
    for line in items.get('legend', '').splitlines():
        match = re.match(r'^(\d+)\s+(.+)$', line.strip())
        if match:
            legend[int(match.group(1))] = match.group(2).strip()
    require(legend == WORLDCOVER_LEGEND, 'worldcover_legend_changed',
            str(sorted(legend.items())))

    gt = geotransform(str(path))
    row, col, on_edge = rowcol_area(gt, centre_lat, centre_lon)
    require(0 <= row < info['height'] and 0 <= col < info['width'],
            'terrain_sample_outside_grid', f'{row},{col}')
    window_rows = [(row + dr, col + dc)
                   for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                   if 0 <= row + dr < info['height'] and 0 <= col + dc < info['width']]
    values = sample_grid_int(str(path), window_rows, allowed=set(legend))
    class_code = values[(row, col)]
    window = [[values.get((row + dr, col + dc)) for dc in (-1, 0, 1)]
              for dr in (-1, 0, 1)]

    conditions = {'product': 'ESA WorldCover v200 2021 10 m land cover',
                  'tile': tile_id, 'crs': 'EPSG:4326',
                  'legend': '11 classes declared in the pinned tile'}
    subject = 'ESA_WorldCover_10m_2021_v200_' + tile_id + '_Map.tif'
    out = []
    for field, value, unit in (
            ('grid_columns', info['width'], 'dimensionless'),
            ('grid_rows', info['height'], 'dimensionless'),
            ('pixel_scale_deg', gt['d_lon'], 'degree'),
            ('file_bytes', info['file_bytes'], 'dimensionless')):
        payload = {'value_si': float(value), 'unit_si': unit,
                   'subject': subject, 'conditions': dict(conditions),
                   'note': 'grid header metadata; payload stays a pinned blob'}
        rec = draft('worldcover:v200:2021:' + tile_id + ':' + field,
                    'measurement', payload,
                    unknowns=['pixel_is_an_area_sample_10m_at_equator_'
                              'declared_by_source_not_a_point'])
        rec['class_contract'] = {'class_id': 'batch.property.measurement',
                                'version': 1}
        out.append(rec)

    payload = {'value_si': float(class_code), 'unit_si': 'dimensionless',
               'subject': 'land cover at the Cayo Santiago patch centre '
                          '(18.1565 N, 65.7350 W)',
               'conditions': dict(conditions),
               'tile_id': tile_id, 'class_code': class_code,
               'class_label': legend[class_code],
               'centre_lat': centre_lat, 'centre_lon': centre_lon,
               'pixel_row': row, 'pixel_col': col,
               'on_pixel_edge': on_edge,
               'sample_format': 'uint' + str(info['bits']),
               'bits_per_sample': info['bits'],
               'raster_type': 'RasterPixelIsArea',
               'pixel_scale_deg': gt['d_lon'],
               'tiepoint_lon_lat': [gt['lon0'], gt['lat0']],
               'nodata_declared': info['nodata'],
               'legend_source': 'embedded GDAL metadata of the pinned tile',
               'window_3x3_class_codes': window,
               'product_version': items.get('product_version'),
               'copyright': items.get('copyright')}
    rec = draft('worldcover:v200:2021:' + tile_id + ':centre', 'measurement',
                payload,
                label='WorldCover ' + legend[class_code] + ' at patch centre',
                unknowns=['single_pixel_class_sample_no_spatial_average',
                          'class_map_value_is_source_classification_not_'
                          'field_measurement'])
    rec['class_contract'] = {'class_id': 'batch.property.worldcover_class',
                            'version': 1}
    out.append(rec)
    return out


GEO_ADAPTERS = {'thor_ucs_stats': thor_ucs_stats,
                'vienna_soil_specimens': vienna_soil_specimens,
                'gsod_daily': gsod_daily,
                'worldcover_centre_class': worldcover_centre_class}
ADAPTERS.update(GEO_ADAPTERS)
