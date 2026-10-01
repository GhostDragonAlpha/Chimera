"""Idempotent fetch + derivation for the three appearance-family sources of
the 2026-09-18 intake-appearance lane (Goldenberg et al. color+NIR reflectance,
Zenodo 15084543; PHYLACINE 1.2.1, GitHub release; USGS Spectral Library v7,
ScienceBase ASCII channel).

RULE 0 ADMISSION (stated before the run; probe evidence:
docs/research/20260917_dbhunt_phys.md, all probes re-verified 2026-09-18):
  STATEMENT: three authless, license-clear appearance sources -- Goldenberg et
  al. CC BY 4.0 (Zenodo license field), PHYLACINE 1.2.1 CC0 (README quote), USGS
  SPLib v7 CC0 1.0 (usgs.gov rights field) -- can be admitted as sha256-pinned
  byte-exact artifacts whose adapters reduce rows/spectra to graph records
  mechanically, with no human-taste step anywhere.
  PREDICTION (not yet measured): (a) the PHYLACINE trait table derives from the
  pinned release zip byte-identically and every body mass lands inside the
  mammal envelope [1e-3, 1e8] g; (b) the Goldenberg total_dataset.csv parses
  fully (no ragged rows) and its reflectance columns sit inside [0, 1];
  (c) the USGS ASCII channel parses into spectra whose wavelength axes are
  strictly increasing inside [0.2, 200] micrometers with reflectance values
  inside [0, 2]; the deferred full bundle never downloads.
  FALSIFIER (named before the run): any upstream byte drift refuses this fetch
  loudly (pin_drift, receipts never silently re-pinned); a PHYLACINE
  re-extraction that is not byte-identical refuses; any single corrupted row or
  spectrum quarantines EXACTLY ITSELF at admission while its neighbours admit;
  the count identity fetched == admitted + quarantined closes with zero silent
  drops; a second full run creates zero new bytes and leaves every receipt
  untouched.

Ceiling law (lane brief): no single committed file may approach the 100 MB
git ceiling. The PHYLACINE zip (106,362,537 bytes, HEAD-verified) exceeds it,
so the zip is pinned by receipt only (never committed) and the admitted
artifact is the DERIVED deterministic trait-table extraction; the USGS full
bundle (5,479,324,354 bytes) is never downloaded -- the ASCII channel zips
(21,812,828 + 43,438,594 bytes) are the per-spectrum metadata/ASCII data, and
the full library is admitted as a deferred identity record with cause.

Idempotency law: with the bytes on disk and every pin verified, a re-run
re-derives the derived files byte-identically and leaves each download receipt
untouched. A changed upstream artifact refuses (pin_drift).

Run:  python -B -m tools.science_funnel.appearance_fetch
"""
import hashlib
import json
import re
import ssl
import urllib.request
import zipfile
from pathlib import Path

from .common import VERSION, canonical, require, sha

DATA_ROOT = Path(__file__).resolve().parent / 'data'

RETRIEVED_UTC = '2026-09-18T00:00:00+00:00'

# ---------------------------------------------------------------- Goldenberg
# Probe-verified from https://zenodo.org/api/records/15084543 (fetched and
# pinned 2026-09-18): license cc-by-4.0, access_right open, per-file md5
# checksums as served by Zenodo.
ZENODO_RECORD_URL = 'https://zenodo.org/api/records/15084543'
GOLDENBERG_FILE_URL = ('https://zenodo.org/api/records/15084543/files/'
                       '{name}/content')
GOLDENBERG_MD5 = {
    'total_dataset.csv': '5f4507858f69aaa4cae60d0b4e2f5314',
    'mammals.tree': '6e11710328f8d1aacb034c904fa435c0',
}
GOLDENBERG_BYTES = {'total_dataset.csv': 47737, 'mammals.tree': 137855}

# ----------------------------------------------------------------- PHYLACINE
# Probe-verified (dossier P2; HEAD re-verified 2026-09-18: 200, 106362537
# bytes, redirect to release-assets.githubusercontent.com).
PHYLACINE_URL = ('https://github.com/MegaPast2Future/PHYLACINE_1.2/releases/'
                 'download/v1.2.1/PHYLACINE_1.2.1.zip')
PHYLACINE_BYTES = 106362537
# Layout probed from the downloaded release zip 2026-09-18 (the first fetch
# refused on phylacine_layout_changed -- the falsifier working as named).
PHYLACINE_MEMBER = 'Data/Traits/Trait_data.csv'
PHYLACINE_RELEASE_NOTES = 'Data/PHYLACINE_1.2.1_Release_notes.pdf'
# Members that stay inside the pinned zip, never extracted (per-file git
# ceiling; not needed for the trait-table admission):
PHYLACINE_DEFERRED_MEMBERS = {
    'Data/Phylogenies/Complete_phylogeny.nex': 132041786,
    'Data/Phylogenies/Small_phylogeny.nex': 95990596,
    'Data/Ranges/': '11,668 species range-map GeoTIFFs (Current + '
                    'Present_natural), not part of the trait-table admission',
    'Data/Taxonomy/Synonymy_table_valid_species_only.csv': 1421700,
    'Data/Taxonomy/Synonymy_table_with_unaccepted_species.csv': 1472852,
    'Data/PHYLACINE_1.2_Metadata.pdf': 324083,
}

# -------------------------------------------------------------- USGS SPLib v7
# ScienceBase item 5807a2a2e4b0841e59e3a18d (USGS Spectral Library Version 7
# Data); ASCII child item 586e8c88e4b0f5ce109fccae; HTML-metadata child item
# 586e8d4de4b0f5ce109fccbb. File URLs as served by the item JSON 2026-09-18.
SB_ITEM_ID = '5807a2a2e4b0841e59e3a18d'
SB_ITEM_URL = ('https://www.sciencebase.gov/catalog/item/'
               + SB_ITEM_ID + '?format=json')
SB_ASCII_ITEM_ID = '586e8c88e4b0f5ce109fccae'
SB_ASCII_ITEM_URL = ('https://www.sciencebase.gov/catalog/item/'
                     + SB_ASCII_ITEM_ID + '?format=json')
USGS_ASCII_A_URL = ('https://www.sciencebase.gov/catalog/file/get/'
                    '586e8c88e4b0f5ce109fccae?f=__disk__a7%2F4f%2F91%2F'
                    'a74f913e0b7d1b8123ad059e52506a02b75a2832')
USGS_ASCII_A_BYTES = 21812828
USGS_ASCII_B_URL = ('https://www.sciencebase.gov/catalog/file/get/'
                    '586e8c88e4b0f5ce109fccae?f=__disk__61%2Fd1%2F3f%2F'
                    '61d13f11fafae0e37aadf700eff1bde6e236165b')
USGS_ASCII_B_BYTES = 43438594
USGS_ASCII_XML_URL = ('https://www.sciencebase.gov/catalog/file/get/'
                      '586e8c88e4b0f5ce109fccae?f=__disk__16%2F2d%2F23%2F'
                      '162d23dc18d9885b308b7275314a87ddab73a37f')
USGS_ASCII_XML_BYTES = 41159
USGS_FGDC_URL = ('https://www.sciencebase.gov/catalog/file/get/'
                 + SB_ITEM_ID + '?f=__disk__e4%2Fb4%2Fd2%2F'
                 'e4b4d23310705802a6a90bf67643a4df65516975')
USGS_FGDC_BYTES = 66785
USGS_FULL_ZIP_URL = ('https://www.sciencebase.gov/catalog/file/get/'
                     + SB_ITEM_ID + '?name=usgs_splib07.zip')
USGS_FULL_ZIP_BYTES = 5479324354
USGS_DEFERRAL = {
    'path': 'usgs_splib07.zip',
    'bytes': USGS_FULL_ZIP_BYTES,
    'url': USGS_FULL_ZIP_URL,
    'cause': 'The full v7 bundle is 5,479,324,354 bytes (ScienceBase item JSON, '
             'HEAD+item-JSON verified 2026-09-18) -- far above the 256 MB '
             'intake-bundle ceiling and the 100 MB git per-file ceiling. The '
             'bundle adds SPECPR binaries, GIF plots and photo-laden HTML '
             'metadata on top of the ASCII channel that IS admitted. The '
             'smallest per-spectrum artifacts the item offers are the two '
             'ASCII channel zips (the ASCII child item carries NO per-chapter '
             'zips -- its full 30-file list is pinned as probe evidence); '
             'admission selects the appearance-relevant chapters from those '
             'pinned bytes by a recorded rule.',
    'probed_utc': RETRIEVED_UTC,
}

UA = {'User-Agent': 'chimera-intake-appearance/1.0 (pinned byte-exact fetch)'}


def _md5(raw):
    return hashlib.md5(raw).hexdigest()


def fetch(url, dest: Path, expect_sha256=None, expect_md5=None, expect_bytes=None):
    """Download to dest unless the pinned bytes are already there. Any
    expectation mismatch refuses (pin_drift) -- never re-pinned silently."""
    if dest.is_file():
        raw = dest.read_bytes()
        matches = ((expect_sha256 is None or sha(raw) == expect_sha256)
                   and (expect_md5 is None or _md5(raw) == expect_md5))
        require(matches, 'pin_drift',
                f'{dest.name}: bytes on disk do not match the pinned expectation')
        if expect_bytes is not None:
            require(len(raw) == expect_bytes, 'pin_drift',
                    f'{dest.name}: {len(raw)} bytes != pinned {expect_bytes}')
        return raw, False
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                context=ssl.create_default_context(),
                                timeout=600) as stream:
        raw = stream.read()
    require(len(raw) > 0, 'empty_download', url)
    if expect_bytes is not None:
        require(len(raw) == expect_bytes, 'pin_drift',
                f'{dest.name}: {len(raw)} bytes != pinned {expect_bytes}')
    if expect_sha256 is not None:
        require(sha(raw) == expect_sha256, 'pin_drift',
                f'{dest.name}: sha256 != pinned expectation')
    if expect_md5 is not None:
        require(_md5(raw) == expect_md5, 'pin_drift',
                f'{dest.name}: md5 != pinned upstream expectation')
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


def producer_pin():
    """sha256 of this module: the recorded derivation producer for derived files."""
    return sha(Path(__file__).read_bytes())


def _entry(path, url, raw, **extra):
    return {'path': path, 'url': url, 'bytes': len(raw), 'sha256': sha(raw),
            **extra}


# ---------------------------------------------------------------- Goldenberg

def fetch_goldenberg():
    folder = DATA_ROOT / 'goldenberg_reflectance'
    record, record_dl = fetch(ZENODO_RECORD_URL, folder / 'zenodo_record_15084543.json')
    payload = json.loads(record.decode('utf-8'))
    require(payload.get('doi') == '10.5281/zenodo.15084543', 'zenodo_record_changed')
    require(payload.get('metadata', {}).get('license', {}).get('id') == 'cc-by-4.0',
            'zenodo_license_changed', str(payload.get('metadata', {}).get('license')))
    served = {f['key']: f for f in payload.get('files', [])}
    files, downloaded = [_entry('zenodo_record_15084543.json', ZENODO_RECORD_URL,
                                record, role='record identity + license evidence')], record_dl
    for name, md5 in sorted(GOLDENBERG_MD5.items()):
        served_file = served.get(name)
        require(served_file is not None, 'zenodo_file_missing', name)
        require(served_file.get('checksum') == 'md5:' + md5, 'zenodo_md5_drift', name)
        require(served_file.get('size') == GOLDENBERG_BYTES[name],
                'zenodo_size_drift', name)
        raw, was_new = fetch(GOLDENBERG_FILE_URL.format(name=name), folder / name,
                             expect_md5=md5, expect_bytes=GOLDENBERG_BYTES[name])
        files.append(_entry(name, GOLDENBERG_FILE_URL.format(name=name), raw,
                            upstream_md5=md5,
                            role='data' if name == 'total_dataset.csv' else 'attachment'))
        downloaded = downloaded or was_new
    receipt = {
        'source': 'Goldenberg et al., replication data for "Color and '
                  'near-infrared reflectance covary in distinct ways across '
                  'taxa and time" (Zenodo 15084543, DOI '
                  '10.5281/zenodo.15084543): total_dataset.csv (reflectance '
                  '+ NIR measurements across taxa incl. mammals) + mammals '
                  'phylogeny (mammals.tree, Alvarez et al. 2022)',
        'retrieved_utc': RETRIEVED_UTC,
        'license': 'CC BY 4.0 (Zenodo record metadata license field '
                   '"cc-by-4.0", access_right "open"; record JSON pinned as '
                   'license evidence)',
        'files': files,
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': downloaded, 'receipt_written': wrote,
            'csv_bytes': GOLDENBERG_BYTES['total_dataset.csv'],
            'csv_sha256': sha((folder / 'total_dataset.csv').read_bytes())}


# ----------------------------------------------------------------- PHYLACINE

def extract_phylacine_trait_table(zip_path: Path, out_dir: Path):
    """Deterministically extract the trait table + the release notes (the
    zip-carried license-evidence artifact) from the pinned release zip. Pure
    stdlib function of the zip bytes: same bytes in, same bytes out, always."""
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        require(PHYLACINE_MEMBER in names, 'phylacine_layout_changed',
                sorted(names)[:10])
        require(PHYLACINE_RELEASE_NOTES in names, 'phylacine_layout_changed',
                PHYLACINE_RELEASE_NOTES)
        table = archive.read(PHYLACINE_MEMBER)
        notes = archive.read(PHYLACINE_RELEASE_NOTES)
    header = table.decode('utf-8-sig').splitlines()[0]
    require('Binomial' in header, 'phylacine_header_changed', header[:120])
    require(notes.startswith(b'%PDF'), 'phylacine_notes_not_pdf')
    table_path = out_dir / 'phylacine_trait_table.csv'
    notes_path = out_dir / 'phylacine_release_notes.pdf'
    table_path.write_bytes(table)
    notes_path.write_bytes(notes)
    return {'member': PHYLACINE_MEMBER, 'notes_member': PHYLACINE_RELEASE_NOTES,
            'table_sha256': sha(table), 'table_bytes': len(table),
            'notes_sha256': sha(notes), 'notes_bytes': len(notes),
            'header': header}


def fetch_phylacine():
    folder = DATA_ROOT / 'phylacine'
    raw, downloaded = fetch(PHYLACINE_URL, folder / 'PHYLACINE_1.2.1.zip',
                            expect_bytes=PHYLACINE_BYTES)
    derived = extract_phylacine_trait_table(folder / 'PHYLACINE_1.2.1.zip', folder)
    producer = producer_pin()
    receipt = {
        'source': 'PHYLACINE 1.2.1 (MegaPast2Future/PHYLACINE_1.2 GitHub '
                  'release v1.2.1; Dryad doi:10.5061/dryad.bp26v20): late '
                  'Quaternary mammal traits -- present/natural-range body '
                  'masses, diet, foraging stratum, extinction status, '
                  'phylogeny inclusion flags',
        'retrieved_utc': RETRIEVED_UTC,
        'license': 'CC0 (README quote captured by the probe dossier from the '
                   'release repo: "This work is licensed under a Creative '
                   'Commons 0 License"; the zip-carried release notes PDF is '
                   'pinned as the in-archive license-evidence artifact)',
        'derivation': {'producer_module': 'tools/science_funnel/appearance_fetch.py',
                       'producer_sha256': producer,
                       'law': 'zip bytes -> (phylacine_trait_table.csv, '
                              'phylacine_release_notes.pdf) is a pure stdlib '
                              'member extraction of the pinned zip; '
                              're-derivation must be byte-identical',
                       'member': derived['member'],
                       'notes_member': derived['notes_member'],
                       'deferred_members': PHYLACINE_DEFERRED_MEMBERS},
        'files': [
            {'path': 'PHYLACINE_1.2.1.zip', 'url': PHYLACINE_URL,
             'bytes': len(raw), 'sha256': sha(raw),
             'note': 'primary artifact; 106,362,537 bytes EXCEEDS the 100 MB '
                     'git per-file ceiling, so the zip is pinned by this '
                     'receipt only (never committed) and bundles pin the '
                     'derived trait table, per the ncbi_taxdmp precedent; the '
                     '132 MB complete phylogeny and 96 MB small phylogeny '
                     'members stay inside the pinned zip, never extracted'},
            {'path': 'phylacine_trait_table.csv', 'url': PHYLACINE_URL,
             'bytes': derived['table_bytes'], 'sha256': derived['table_sha256'],
             'role': 'derived', 'derived_by_sha256': producer},
            {'path': 'phylacine_release_notes.pdf', 'url': PHYLACINE_URL,
             'bytes': derived['notes_bytes'], 'sha256': derived['notes_sha256'],
             'role': 'license evidence', 'derived_by_sha256': producer},
        ],
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': downloaded, 'receipt_written': wrote,
            'table_bytes': derived['table_bytes'],
            'table_sha256': derived['table_sha256'],
            'header': derived['header']}


# ------------------------------------------------------------ USGS SPLib v7

def fetch_usgs_splib07():
    folder = DATA_ROOT / 'usgs_splib07_subset'
    item_json, item_dl = fetch(SB_ITEM_URL, folder / 'sciencebase_item.json')
    ascii_json, ascii_dl = fetch(SB_ASCII_ITEM_URL,
                                 folder / 'sciencebase_ascii_item.json')
    ascii_a, a_dl = fetch(USGS_ASCII_A_URL, folder / 'ASCIIdata_splib07a.zip',
                          expect_bytes=USGS_ASCII_A_BYTES)
    ascii_b, b_dl = fetch(USGS_ASCII_B_URL, folder / 'ASCIIdata_splib07b.zip',
                          expect_bytes=USGS_ASCII_B_BYTES)
    ascii_xml, xml_dl = fetch(USGS_ASCII_XML_URL, folder / 'ASCIIdata.xml',
                              expect_bytes=USGS_ASCII_XML_BYTES)
    fgdc, fgdc_dl = fetch(USGS_FGDC_URL, folder / 'USGS_Spectral_Library_Version_7_Data.xml',
                          expect_bytes=USGS_FGDC_BYTES)
    receipt = {
        'source': 'USGS Spectral Library Version 7 (ScienceBase item '
                  '5807a2a2e4b0841e59e3a18d, DOI 10.5066/F7RR1WDJ): the ASCII '
                  'channel only -- splib07a + splib07b per-spectrum ASCII '
                  'spectra and their ASCII file inventory -- fetched as a '
                  'targeted subset; the 5.1 GB full bundle is a named deferred '
                  'item (see deferred block)',
        'retrieved_utc': RETRIEVED_UTC,
        'license': 'CC0 1.0 Universal (usgs.gov data-release rights field, '
                   'quoted by the probe dossier; FGDC metadata XML pinned as '
                   'identity evidence)',
        'subset_rule': 'The ASCII child item (586e8c88e4b0f5ce109fccae) '
                       'carries NO per-chapter zips -- its full 30-file list '
                       'is pinned -- so the smallest per-spectrum metadata/'
                       'ASCII artifacts are the two whole-ASCII-channel zips; '
                       'both are pinned whole (21.8 + 43.4 MB, both far below '
                       'the ceilings) and ADMISSION selects the '
                       'appearance-relevant chapters from the pinned bytes by '
                       'the rule recorded on the connector',
        'deferred': dict(USGS_DEFERRAL),
        'files': [
            _entry('sciencebase_item.json', SB_ITEM_URL, item_json,
                   role='probe evidence: item identity + full-bundle size'),
            _entry('sciencebase_ascii_item.json', SB_ASCII_ITEM_URL, ascii_json,
                   role='probe evidence: full 30-file ASCII item listing'),
            _entry('ASCIIdata_splib07a.zip', USGS_ASCII_A_URL, ascii_a,
                   role='data'),
            _entry('ASCIIdata_splib07b.zip', USGS_ASCII_B_URL, ascii_b,
                   role='data'),
            _entry('ASCIIdata.xml', USGS_ASCII_XML_URL, ascii_xml,
                   role='attachment: ASCII file inventory'),
            _entry('USGS_Spectral_Library_Version_7_Data.xml', USGS_FGDC_URL,
                   fgdc, role='attachment: FGDC metadata / license evidence'),
        ],
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': item_dl or ascii_dl or a_dl or b_dl or xml_dl or fgdc_dl,
            'receipt_written': wrote, 'a_bytes': len(ascii_a),
            'b_bytes': len(ascii_b)}


def main():
    results = {'schema_version': VERSION,
               'goldenberg': fetch_goldenberg(),
               'phylacine': fetch_phylacine(),
               'usgs_splib07': fetch_usgs_splib07()}
    print(json.dumps({'ok': True, **results}, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
