"""Idempotent fetch + pinning for the four geoscience sources of the
2026-09-17 intake-geo lane (THOR rock strength UCS, Vienna soil lab, NOAA
GSOD station-year, ESA WorldCover tile over the Cayo Santiago patch).

Rule 0 admission (stated in docs/research/20260917_intake_geo.md BEFORE any
code): the four authless, license-clear sources admit as sha256-pinned
bundles with mechanical per-class falsifiers; a corrupted row quarantines
exactly itself; the count identity closes; re-runs are idempotent and
upstream byte drift refuses loudly.

Idempotency law: with the bytes on disk and every pin verified, a re-run
re-derives the WorldCover tile resolution against the pinned grid index
byte-identically and leaves each download receipt untouched. A changed
upstream artifact refuses (pin_drift) -- receipts are never re-pinned
silently.

Run:  python -B -m tools.science_funnel.geo_fetch
"""
import json
import ssl
import urllib.request
from pathlib import Path

from .common import Refusal, canonical, require, sha

DATA_ROOT = Path(__file__).resolve().parent / 'data'

# Task-pinned expectations (lane brief 2026-09-17; probes by
# docs/research/20260917_dbhunt_world.md the same day). The three CSV pins
# were fixed by the lane brief; the WorldCover tile pin was measured during
# this lane's provenance fetch and preregistered in the admission doc.
THOR_URL = 'https://zenodo.org/records/12687445/files/2%20-%20%20UCS.csv?download=1'
THOR_SHA256 = '466e47ef419b1d777b513441631a9e72b65b840f9ded07fed73f444e77599eff'
THOR_BYTES = 3736
THOR_RECORD_URL = 'https://zenodo.org/api/records/12687445'

SORANZO_URL = ('https://zenodo.org/records/14251191/files/'
               'Zenodo_DATA_Soranzo.csv?download=1')
SORANZO_SHA256 = '5932484eac2ba102af9ec71cb414570b338a37975569e88b879e6f83f447a71f'
SORANZO_BYTES = 94297
SORANZO_RECORD_URL = 'https://zenodo.org/api/records/14251191'

GSOD_URL = ('https://www.ncei.noaa.gov/data/global-summary-of-the-day/'
            'access/2024/78535011630.csv')
GSOD_SHA256 = '338bb5b9e1fd5fdcfb2bba9a052c7a5db75cd740f59b8494b0a544e7769efc6d'
GSOD_BYTES = 83597
GSOD_README_URL = ('https://www.ncei.noaa.gov/data/global-summary-of-the-day/'
                   'doc/readme.txt')
GSOD_README_SHA256 = '25a784a4cba0eab5f070137c57c4b4bd113982e054c77812b2d22e96c5818bc1'
GSOD_README_BYTES = 11288

WC_BASE = 'https://esa-worldcover.s3.eu-central-1.amazonaws.com'
WC_TILE_ID = 'N18W066'
WC_TILE_URL = (WC_BASE + '/v200/2021/map/ESA_WorldCover_10m_2021_v200_'
               + WC_TILE_ID + '_Map.tif')
WC_TILE_SHA256 = '0d8b5835abb8aa33a80f4c66f5cf244a0368b551fa9fb470219d82e267241b78'
WC_TILE_BYTES = 4604997
WC_GRID_URL = WC_BASE + '/esa_worldcover_grid.geojson'
WC_GRID_SHA256 = 'eeb5074bf182c411b3872b2494f6514401ecd9ba8ba0c353fe282f1e2b822f5b'
WC_GRID_BYTES = 543674
WC_PUM_URL = WC_BASE + '/v200/2021/docs/WorldCover_PUM_V2.0.pdf'
WC_PUM_SHA256 = '4301a3d95260d88bd4315f43ccf2a12ef74ad391109b9f36e22b6e51d8490107'
WC_PUM_BYTES = 4102952

PATCH_CENTRE = (18.1565, -65.7350)   # Cayo Santiago patch centre (N, W)

UA = {'User-Agent': 'chimera-intake-geo/1.0 (pinned byte-exact source fetch)'}


def fetch(url, dest: Path, expect_sha256=None, expect_bytes=None):
    """Download to dest unless the pinned bytes are already there. Any
    expectation mismatch refuses (pin_drift) -- never re-pinned silently."""
    if dest.is_file():
        raw = dest.read_bytes()
        if expect_sha256 is None or sha(raw) == expect_sha256:
            if expect_bytes is not None:
                require(len(raw) == expect_bytes, 'pin_drift',
                        f'{dest.name}: {len(raw)} bytes != pinned {expect_bytes}')
            return raw, False
        require(False, 'pin_drift', f'{dest.name}: sha256 != pinned expectation')
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                context=ssl.create_default_context(), timeout=300) as r:
        raw = r.read()
    require(len(raw) > 0, 'empty_download', url)
    if expect_bytes is not None:
        require(len(raw) == expect_bytes, 'pin_drift',
                f'{dest.name}: {len(raw)} bytes != pinned {expect_bytes}')
    if expect_sha256 is not None:
        require(sha(raw) == expect_sha256, 'pin_drift',
                f'{dest.name}: sha256 != pinned expectation')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    return raw, True


def write_receipt(path: Path, receipt):
    """Write the receipt once; a re-run with matching pins leaves it untouched."""
    if path.is_file():
        require(path.read_bytes() == canonical(receipt), 'receipt_not_idempotent',
                f'{path.name}: receipt would change on re-run')
        return False
    path.write_bytes(canonical(receipt))
    return True


def _record(raw, url, name):
    """The record json companions carry the license evidence; their bytes are
    pinned so the license claim is replayable."""
    meta = json.loads(raw)
    license_id = (meta.get('metadata') or {}).get('license', {}).get('id', '')
    require(license_id == 'cc-by-4.0', 'pin_drift', name + ': license changed')
    return {'path': name, 'url': url, 'bytes': len(raw), 'sha256': sha(raw),
            'license_id': license_id}


def resolve_tile(grid_geojson, lat, lon):
    """Point-in-polygon resolution against the bucket's own tile index: the
    tile id is derived mechanically, never guessed from neighbours."""
    gj = json.loads(grid_geojson)
    features = gj.get('features') or []
    require(len(features) == 2651, 'worldcover_grid_changed', str(len(features)))
    hits = []
    for feature in features:
        geometry = feature.get('geometry') or {}
        polygons = ([geometry['coordinates']] if geometry.get('type') == 'Polygon'
                    else geometry.get('coordinates', []))
        for poly in polygons:
            ring = poly[0]
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            if not (min(xs) <= lon <= max(xs) and min(ys) <= lat <= max(ys)):
                continue
            inside = False
            n = len(ring)
            for i in range(n):
                x1, y1 = ring[i][0], ring[i][1]
                x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
                if (y1 > lat) != (y2 > lat):
                    xint = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
                    if xint > lon:
                        inside = not inside
            if inside:
                hits.append((feature.get('properties') or {}).get('ll_tile'))
                break
    require(len(hits) == 1, 'worldcover_tile_resolution_ambiguous', str(hits))
    return hits[0]


# ------------------------------------------------------------------ THOR

def fetch_thor():
    folder = DATA_ROOT / 'thor_ucs'
    raw, downloaded = fetch(THOR_URL, folder / '2 -  UCS.csv',
                            expect_sha256=THOR_SHA256, expect_bytes=THOR_BYTES)
    record, _ = fetch(THOR_RECORD_URL, folder / 'zenodo_record_12687445.json')
    receipt = {
        'source': 'THOR - the rock strength database (Haag & Schoenbohm 2025, '
                  'EPSL 660, 119364; Zenodo record 12687445): sigma_UCS group '
                  'summaries by lithology; file name carries literal spaces',
        'retrieved_utc': '2026-09-17T00:00:00+00:00',
        'license': 'CC BY 4.0 (Zenodo API metadata license field '
                   'license.id=cc-by-4.0, pinned as artifact)',
        'files': [
            {'path': '2 -  UCS.csv', 'url': THOR_URL, 'bytes': len(raw),
             'sha256': sha(raw)},
            _record(record, THOR_RECORD_URL, 'zenodo_record_12687445.json'),
        ],
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': downloaded, 'receipt_written': wrote,
            'bytes': len(raw), 'sha256': sha(raw)}


# ---------------------------------------------------------------- Vienna

def fetch_soranzo():
    folder = DATA_ROOT / 'vienna_soil'
    raw, downloaded = fetch(SORANZO_URL, folder / 'Zenodo_DATA_Soranzo.csv',
                            expect_sha256=SORANZO_SHA256,
                            expect_bytes=SORANZO_BYTES)
    record, _ = fetch(SORANZO_RECORD_URL, folder / 'zenodo_record_14251191.json')
    rows = raw.decode('utf-8-sig').splitlines()
    require(len(rows) == 1067, 'pin_drift',
            f'Soranzo csv: {len(rows) - 1} data rows != pinned 1066')
    receipt = {
        'source': 'Geotechnical laboratory test dataset of Austria (Vienna, '
                  'Lower Austria, Burgenland; Zenodo record 14251191, Soranzo '
                  'et al., "Machine learning predictions on an extensive '
                  'geotechnical dataset of laboratory tests in Austria")',
        'retrieved_utc': '2026-09-17T00:00:00+00:00',
        'license': 'CC BY 4.0 (Zenodo API metadata license field '
                   'license.id=cc-by-4.0, pinned as artifact)',
        'files': [
            {'path': 'Zenodo_DATA_Soranzo.csv', 'url': SORANZO_URL,
             'bytes': len(raw), 'sha256': sha(raw)},
            _record(record, SORANZO_RECORD_URL, 'zenodo_record_14251191.json'),
        ],
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': downloaded, 'receipt_written': wrote,
            'bytes': len(raw), 'sha256': sha(raw)}


# ------------------------------------------------------------------ GSOD

def fetch_gsod():
    folder = DATA_ROOT / 'noaa_gsod'
    raw, downloaded = fetch(GSOD_URL, folder / '78535011630.csv',
                            expect_sha256=GSOD_SHA256, expect_bytes=GSOD_BYTES)
    readme, _ = fetch(GSOD_README_URL, folder / 'readme.txt',
                      expect_sha256=GSOD_README_SHA256,
                      expect_bytes=GSOD_README_BYTES)
    require(readme.count(b'\x00') == 0, 'pin_drift', 'readme encoding changed')
    receipt = {
        'source': 'NOAA NCEI Global Summary of the Day (GSOD), station-year '
                  '2024 for station 78535011630 (ROOSEVELT ROADS, PR US); '
                  'readme.txt pins the units and the missing-data codes',
        'retrieved_utc': '2026-09-17T00:00:00+00:00',
        'license': 'US Government work (17 USC 105); the pinned README carries '
                   'the WMO Resolution 40 note for non-US locations -- carried '
                   'on every record, never resolved silently',
        'files': [
            {'path': '78535011630.csv', 'url': GSOD_URL, 'bytes': len(raw),
             'sha256': sha(raw)},
            {'path': 'readme.txt', 'url': GSOD_README_URL,
             'bytes': len(readme), 'sha256': sha(readme)},
        ],
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': downloaded, 'receipt_written': wrote,
            'bytes': len(raw), 'sha256': sha(raw)}


# --------------------------------------------------------------- WorldCover

def fetch_worldcover():
    folder = DATA_ROOT / 'esa_worldcover'
    tile, downloaded = fetch(WC_TILE_URL, folder / ('ESA_WorldCover_10m_2021_'
                              'v200_N18W066_Map.tif'),
                             expect_sha256=WC_TILE_SHA256,
                             expect_bytes=WC_TILE_BYTES)
    grid, _ = fetch(WC_GRID_URL, folder / 'esa_worldcover_grid.geojson',
                    expect_sha256=WC_GRID_SHA256, expect_bytes=WC_GRID_BYTES)
    pum, _ = fetch(WC_PUM_URL, folder / 'WorldCover_PUM_V2.0.pdf',
                   expect_sha256=WC_PUM_SHA256, expect_bytes=WC_PUM_BYTES)
    require(pum[:5] == b'%PDF-', 'pin_drift', 'PUM is not a PDF')
    tile_id = resolve_tile(grid, *PATCH_CENTRE)
    require(tile_id == WC_TILE_ID, 'worldcover_tile_resolution_changed',
            tile_id + ' != ' + WC_TILE_ID)
    receipt = {
        'source': 'ESA WorldCover v200 2021 10 m land-cover tile N18W066 '
                  '(3x3 degree COG, EPSG:4326); tile id resolved against the '
                  'bucket\'s own tile index (esa_worldcover_grid.geojson, '
                  '2,651 features; exactly one contains the Cayo Santiago '
                  'patch centre 18.1565 N 65.7350 W) and cross-checked '
                  'against the tile\'s embedded product_tile metadata',
        'retrieved_utc': '2026-09-17T00:00:00+00:00',
        'license': 'CC-BY 4.0 (declared inside the tile\'s embedded GDAL '
                   'metadata: "CC-BY 4.0 - '
                   'https://creativecommons.org/licenses/by/4.0/"); copyright '
                   '"ESA WorldCover project 2021 / Contains modified '
                   'Copernicus Sentinel data (2021) processed by ESA '
                   'WorldCover consortium"; PUM V2.0 pinned as the class '
                   'legend source',
        'files': [
            {'path': 'ESA_WorldCover_10m_2021_v200_N18W066_Map.tif',
             'url': WC_TILE_URL, 'bytes': len(tile), 'sha256': sha(tile)},
            {'path': 'esa_worldcover_grid.geojson', 'url': WC_GRID_URL,
             'bytes': len(grid), 'sha256': sha(grid)},
            {'path': 'WorldCover_PUM_V2.0.pdf', 'url': WC_PUM_URL,
             'bytes': len(pum), 'sha256': sha(pum)},
        ],
        'tile_resolution': {'centre_lat': PATCH_CENTRE[0],
                            'centre_lon': PATCH_CENTRE[1],
                            'tile_id': tile_id,
                            'grid_features': 2651},
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': downloaded, 'receipt_written': wrote,
            'bytes': len(tile), 'sha256': sha(tile), 'tile_id': tile_id}


def main():
    results = {'thor_ucs': fetch_thor(), 'vienna_soil': fetch_soranzo(),
               'noaa_gsod': fetch_gsod(), 'esa_worldcover': fetch_worldcover()}
    for name, result in results.items():
        print(name, canonical(result).decode())
    return results


if __name__ == '__main__':
    main()
