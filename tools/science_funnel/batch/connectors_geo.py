"""INTAKE-GEO lane connectors (auto-loaded by batch.connectors).

Four connectors, one lane (2026-09-17):
  thor_rock_ucs           -- THOR rock strength database (Zenodo 12687445,
                             CC BY 4.0): 47 lithologic-group sigma_UCS
                             summaries; file name carries literal spaces.
  vienna_soil_lab         -- Austrian geotechnical lab dataset (Zenodo
                             14251191, CC BY 4.0): 1,066 soil specimens
                             (PSD, Atterberg, Proctor, permeability, shear).
  noaa_gsod_station_year  -- NOAA NCEI GSOD station 78535011630 (Roosevelt
                             Roads, PR US) 2024; readme.txt pins the units
                             and missing-data codes.
  esa_worldcover_n18w066  -- ESA WorldCover v200 2021 tile over the Cayo
                             Santiago patch (CC BY 4.0, declared in the
                             tile's own embedded metadata); tile id resolved
                             against the bucket's own tile index and
                             cross-checked against the tile's product_tile.

Pins resolve at load time from each data dir's download_receipt.json (written
by tools/science_funnel/geo_fetch.py, idempotent, byte-pinned); nothing is
hardcoded here. The class contracts these connectors map to live in the
authored class-contract store (batch.property.measurement reused;
batch.observation.soil_specimen, batch.observation.gsod_day and
batch.property.worldcover_class authored for this lane).
"""
from .. import adapters_geo  # noqa: F401  (registers lane adapter names)
from .connectors import _artifacts, _pins

_thor_receipt, _thor_pins = _pins('thor_ucs')
_sor_receipt, _sor_pins = _pins('vienna_soil')
_gsod_receipt, _gsod_pins = _pins('noaa_gsod')
_wc_receipt, _wc_pins = _pins('esa_worldcover')

CONNECTORS = {
    'thor_rock_ucs': {
        'connector_id': 'thor_rock_ucs',
        'mode': 'admit',
        'data_dir': 'thor_ucs',
        'adapter': 'thor_ucs_stats',
        'source': {
            'id': 'zenodo.thor.12687445.ucs',
            'release': 'THOR - the rock strength database, Zenodo record '
                       '12687445 (companion paper Haag & Schoenbohm 2025, '
                       'EPSL 660, 119364); UCS.csv bytes sha256-verified '
                       '2026-09-17; a newer record version exists upstream '
                       '(10.5281/zenodo.12687444) -- THIS admission pins the '
                       'brief-pinned record 12687445',
            'url': 'https://zenodo.org/records/12687445/files/'
                   '2%20-%20%20UCS.csv?download=1',
            'license': 'CC BY 4.0 (Zenodo API metadata license.id=cc-by-4.0, '
                       'pinned as artifact); attribution: Haag, M.B., '
                       'Schoenbohm, L.M., 2025, Thor: a rock strength '
                       'database',
            'known_gaps': ['group summaries, not raw measurements (n, mean, '
                           'std, percentiles per lithology)',
                           'the source CSV carries no unit column; the '
                           'megapascal reading is declared on every record',
                           '75/25 and 90/10 ratio columns omitted '
                           '(recomputable from the admitted percentiles)',
                           'classes I/II/III overlap: group rows are '
                           'cross-cutting aggregations, never merged'],
        },
        'artifacts': _artifacts('thor_ucs', [
            ('2 -  UCS.csv', 'data'),
            ('zenodo_record_12687445.json', 'attachment'),
        ], _thor_pins),
        'constants': {
            'expected_rows': 48,
            'zenodo_record_sha256': _thor_pins['zenodo_record_12687445.json']['sha256'],
        },
        'classes': {'measurement': 'batch.property.measurement'},
    },
    'vienna_soil_lab': {
        'connector_id': 'vienna_soil_lab',
        'mode': 'admit',
        'data_dir': 'vienna_soil',
        'adapter': 'vienna_soil_specimens',
        'source': {
            'id': 'zenodo.soranzo.14251191.lab',
            'release': 'Geotechnical laboratory test dataset of Austria '
                       '(Vienna, Lower Austria, Burgenland; Zenodo record '
                       '14251191, dataset for "Machine learning predictions '
                       'on an extensive geotechnical dataset of laboratory '
                       'tests in Austria"); CSV bytes sha256-verified '
                       '2026-09-17',
            'url': 'https://zenodo.org/records/14251191/files/'
                   'Zenodo_DATA_Soranzo.csv?download=1',
            'license': 'CC BY 4.0 (Zenodo API metadata license.id=cc-by-4.0, '
                       'pinned as artifact)',
            'known_gaps': ['one record per specimen row; the source carries '
                           'no specimen id, so external ids are file row '
                           'order',
                           'per-column units are not declared in the pinned '
                           'bytes; families carry source-conventional units '
                           '(%, mm, g/cm3, m/s, kPa, degree) declared as an '
                           'assumption on every record',
                           'Location is sparse (711/1,066 rows) and '
                           'lat/lon sparser (646 rows)',
                           'a row admits only its measured cells: empty '
                           'means the test was not run, never zero'],
        },
        'artifacts': _artifacts('vienna_soil', [
            ('Zenodo_DATA_Soranzo.csv', 'data'),
            ('zenodo_record_14251191.json', 'attachment'),
        ], _sor_pins),
        'constants': {
            'expected_rows': 1066,
            'zenodo_record_sha256': _sor_pins['zenodo_record_14251191.json']['sha256'],
        },
        'classes': {'entity': 'batch.observation.soil_specimen'},
    },
    'noaa_gsod_station_year': {
        'connector_id': 'noaa_gsod_station_year',
        'mode': 'admit',
        'data_dir': 'noaa_gsod',
        'adapter': 'gsod_daily',
        'source': {
            'id': 'ncei.gsod.78535011630.2024',
            'release': 'NOAA NCEI Global Summary of the Day, station-year '
                       '2024 for station 78535011630 (ROOSEVELT ROADS, PR '
                       'US; 359 unique dates 2024-01-01..2024-12-24 -- the '
                       'source file itself carries 7 absent days); bytes '
                       'sha256-verified 2026-09-17',
            'url': 'https://www.ncei.noaa.gov/data/global-summary-of-the-day/'
                   'access/2024/78535011630.csv',
            'license': 'US Government work (17 USC 105). The pinned README '
                       'carries the WMO Resolution 40 note for non-US '
                       'locations (free and unrestricted for research, '
                       'education, non-commercial use; commercial re-export '
                       'restrictions for some countries) -- carried on every '
                       'record, never resolved silently',
            'known_gaps': ['documented missing codes become explicit nodata, '
                           'never values (519 cells in this file)',
                           'STP renders in a 4-wide field: real station '
                           'pressures ~1015.9 mb appear as 15.9 and missing '
                           '9999.9 ships as 999.9 -- carried as asserted '
                           'with a truncation unknown',
                           'MAX/MIN are summary extremes whose time of day '
                           'the README itself flags as varying by country',
                           'GSOD is a summary product of ISD, not the '
                           'underlying hourly observations'],
        },
        'artifacts': _artifacts('noaa_gsod', [
            ('78535011630.csv', 'data'),
            ('readme.txt', 'attachment'),
        ], _gsod_pins),
        'constants': {
            'expected_rows': 359,
            'station_id': '78535011630',
            'readme_sha256': _gsod_pins['readme.txt']['sha256'],
        },
        'classes': {'entity': 'batch.observation.gsod_day'},
    },
    'esa_worldcover_n18w066': {
        'connector_id': 'esa_worldcover_n18w066',
        'mode': 'admit',
        'data_dir': 'esa_worldcover',
        'adapter': 'worldcover_centre_class',
        'source': {
            'id': 'esa.worldcover.v200.2021.n18w066',
            'release': 'ESA WorldCover v200 2021 10 m land-cover tile '
                       'N18W066 (3x3 degree COG, EPSG:4326); tile id '
                       'resolved 2026-09-17 against the bucket\'s own tile '
                       'index (esa_worldcover_grid.geojson, 2,651 features; '
                       'exactly one contains the Cayo Santiago patch centre '
                       '18.1565 N 65.7350 W) and cross-checked against the '
                       'tile\'s embedded product_tile metadata; bytes '
                       'sha256-verified on download',
            'url': 'https://esa-worldcover.s3.eu-central-1.amazonaws.com/'
                   'v200/2021/map/ESA_WorldCover_10m_2021_v200_N18W066_Map.tif',
            'license': 'CC-BY 4.0 (declared inside the tile\'s embedded GDAL '
                       'metadata); copyright "ESA WorldCover project 2021 / '
                       'Contains modified Copernicus Sentinel data (2021) '
                       'processed by ESA WorldCover consortium"; PUM V2.0 '
                       'pinned as the class legend source',
            'known_gaps': ['one pixel sample at the patch centre plus a 3x3 '
                           'window: no spatial average, no regional '
                           'classification',
                           'the class is the source classification, not a '
                           'field measurement',
                           'only tile N18W066 is admitted, not the 2,651-'
                           'tile global product',
                           'the 10 m nominal resolution is the source '
                           'declaration (pixel scale 1/12000 degree)'],
        },
        'artifacts': _artifacts('esa_worldcover', [
            ('ESA_WorldCover_10m_2021_v200_N18W066_Map.tif', 'data'),
            ('esa_worldcover_grid.geojson', 'attachment'),
            ('WorldCover_PUM_V2.0.pdf', 'attachment'),
        ], _wc_pins),
        'constants': {
            'tile_id': 'N18W066',
            'centre_lat': 18.1565,
            'centre_lon': -65.735,
            'expected_pixels': 36000,
            'grid_index_sha256': _wc_pins['esa_worldcover_grid.geojson']['sha256'],
        },
        'classes': {'measurement': 'batch.property.measurement'},
    },
}
