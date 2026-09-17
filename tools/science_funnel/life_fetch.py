"""Idempotent fetch + derivation for the three life-science sources of the
2026-09-17 intake-life lane (PanTHERIA 1.0, NCBI taxdmp Macaca subtree, Rhea).

Rule 0 admission (stated before the run):
  STATEMENT: these three authless, license-clear sources can be admitted as
  pinned byte-exact bundles whose adapters convert units and resolve names
  mechanically.
  PREDICTION (not yet measured): PanTHERIA Macaca BMR records pass with units
  converted (mLO2/hr -> W via the 20.1 J/mL O2 calorific equivalent, declared
  as an assumption on every record) and their species names resolve against
  the NCBI taxdmp Macaca subtree.
  FALSIFIER (named before the run): a -999 sentinel reaching a measurement
  record refuses the class; any upstream byte drift refuses this fetch.

Idempotency law: with the bytes on disk and every pin verified, a re-run
re-derives the Macaca subtree and rewrites it byte-identically, and leaves
each download receipt untouched. A changed upstream artifact refuses loudly
(pin_drift) -- receipts are never silently re-pinned.

Run:  python -B -m tools.science_funnel.life_fetch
"""
import hashlib
import io
import json
import re
import ssl
import urllib.request
import zipfile
from pathlib import Path

from .common import VERSION, Refusal, canonical, require, sha

DATA_ROOT = Path(__file__).resolve().parent / 'data'

# Task-pinned expectations (lane brief 2026-09-17, probe-verified by
# docs/research/20260917_dbhunt_phys.md the same day).
PANTHERIA_URL = 'https://ndownloader.figshare.com/files/5604752'
PANTHERIA_SHA256 = 'fe84274a39ba73b3c9b6950b78ba44c545852db9809d1549b0071cfdde46df9f'
TAXDMP_URL = 'https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdmp.zip'
TAXDMP_MD5_URL = TAXDMP_URL + '.md5'
TAXDMP_BYTES = 79535405
RHEA_BASE = 'https://ftp.expasy.org/databases/rhea/'
RHEA_TSV_URL = RHEA_BASE + 'tsv/rhea-chebi-smiles.tsv'
RHEA_LICENSE_URL = RHEA_BASE + 'LICENSE.txt'
RHEA_RELEASE_URL = RHEA_BASE + 'rhea-release.properties'

UA = {'User-Agent': 'chimera-intake-life/1.0 (pinned byte-exact source fetch)'}


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


def producer_pin():
    """sha256 of this module: the recorded derivation producer for subtree files."""
    return sha(Path(__file__).read_bytes())


# ---------------------------------------------------------------- PanTHERIA

def fetch_pantheria():
    folder = DATA_ROOT / 'pantheria'
    raw, downloaded = fetch(PANTHERIA_URL, folder / 'ECOL_90_184.zip',
                            expect_sha256=PANTHERIA_SHA256)
    require(len(raw) == 2950934, 'pin_drift',
            f'PanTHERIA zip: {len(raw)} bytes != probe-measured 2950934')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        require('PanTHERIA_1-0_WR05_Aug2008.txt' in names, 'pantheria_layout_changed', names)
        rows = archive.read('PanTHERIA_1-0_WR05_Aug2008.txt')
    require(rows.decode('utf-8').count('\n') >= 5417, 'pantheria_row_count_changed')
    receipt = {
        'source': 'PanTHERIA 1.0 (Jones et al. 2009, ECOL 90(184)): mammal '
                  'life-history traits incl. 18-1_BasalMetRate_mLO2hr, '
                  '5-2_BasalMetRateMass_g, 5-1_AdultBodyMass_g; 5,417 species rows',
        'retrieved_utc': '2026-09-17T00:00:00+00:00',
        'license': 'CC0 (figshare API license field for article 3531875, '
                   'probe-verified 2026-09-17 by docs/research/20260917_dbhunt_phys.md)',
        'sentinel_law': '-999 cells are nodata with an explicit unknown, '
                        'never measurements',
        'files': [{'path': 'ECOL_90_184.zip', 'url': PANTHERIA_URL,
                   'bytes': len(raw), 'sha256': sha(raw),
                   'inner_file': 'PanTHERIA_1-0_WR05_Aug2008.txt',
                   'inner_sha256': sha(rows)}],
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': downloaded, 'receipt_written': wrote,
            'bytes': len(raw), 'sha256': sha(raw)}


# ------------------------------------------------------------------ taxdmp

def _dmp_rows(archive, name):
    """Yield the '\t|\t'-separated fields of a taxdmp .dmp member."""
    with archive.open(name) as stream:
        for line in io.TextIOWrapper(stream, encoding='utf-8'):
            line = line.rstrip('\r\n')
            if line.endswith('\t|'):
                line = line[:-2]
            yield [field.strip() for field in line.split('\t|\t')]


def extract_macaca_subtree(zip_path: Path, out_dir: Path):
    """Deterministically derive the Macaca subtree from the pinned taxdmp zip.

    Extracts ONLY the genus Macaca and its descendants: nodes (tax_id, parent,
    rank) and every name record of those taxa (all name classes, so synonyms
    are resolution candidates). Same zip bytes -> same tsv bytes, always.
    """
    with zipfile.ZipFile(zip_path) as archive:
        require({'names.dmp', 'nodes.dmp'} <= set(archive.namelist()),
                'taxdmp_layout_changed', archive.namelist()[:5])
        genus_ids = [int(row[0]) for row in _dmp_rows(archive, 'names.dmp')
                     if row[1] == 'Macaca' and row[3] == 'scientific name']
        # sanity: the genus Macaca, not some other usage of the string
        genus_ids = [tax for tax in genus_ids
                     if any(r[0] == str(tax) and r[2] == 'genus'
                            for r in _dmp_rows(archive, 'nodes.dmp')
                            if r[0] == str(tax))]
        require(len(genus_ids) == 1, 'macaca_genus_not_unique', genus_ids)
        root = genus_ids[0]
        subtree, frontier, depth = {root}, {root}, 0
        node_rows = {}
        while frontier and depth < 8:
            nxt = set()
            for row in _dmp_rows(archive, 'nodes.dmp'):
                tax, parent = int(row[0]), int(row[1])
                if parent in frontier and tax not in subtree:
                    subtree.add(tax)
                    nxt.add(tax)
                    node_rows[tax] = (parent, row[2])
            frontier = nxt
            depth += 1
        for row in _dmp_rows(archive, 'nodes.dmp'):
            tax = int(row[0])
            if tax == root:
                node_rows[tax] = (int(row[1]), row[2])
        require(len(subtree) >= 5, 'macaca_subtree_suspiciously_small', len(subtree))
        names = [row for row in _dmp_rows(archive, 'names.dmp')
                 if int(row[0]) in subtree]

    nodes_lines = ['tax_id\tparent_tax_id\trank']
    for tax in sorted(node_rows):
        parent, rank = node_rows[tax]
        nodes_lines.append(f'{tax}\t{parent}\t{rank}')
    names_lines = ['tax_id\tname_txt\tunique_name\tname_class']
    for row in sorted(names, key=lambda r: (int(r[0]), r[3], r[1])):
        names_lines.append('\t'.join(row[:4]))
    nodes_bytes = ('\n'.join(nodes_lines) + '\n').encode('utf-8')
    names_bytes = ('\n'.join(names_lines) + '\n').encode('utf-8')
    (out_dir / 'macaca_nodes.tsv').write_bytes(nodes_bytes)
    (out_dir / 'macaca_names.tsv').write_bytes(names_bytes)
    ranks = sorted({rank for _, rank in node_rows.values()})
    return {'root_tax_id': root, 'taxa': len(node_rows), 'name_records': len(names),
            'ranks': ranks, 'nodes_sha256': sha(nodes_bytes),
            'names_sha256': sha(names_bytes)}


def fetch_ncbi_taxdmp():
    folder = DATA_ROOT / 'ncbi_taxdmp'
    raw, downloaded = fetch(TAXDMP_URL, folder / 'taxdmp.zip',
                            expect_bytes=TAXDMP_BYTES)
    md5_raw, _ = fetch(TAXDMP_MD5_URL, folder / 'taxdmp.zip.md5')
    expect_md5 = re.match(rb'([0-9a-f]{32})', md5_raw.strip().lower())
    require(expect_md5 is not None, 'taxdmp_md5_sidecar_unparseable', md5_raw[:50])
    require(hashlib.md5(raw).hexdigest() == expect_md5.group(1).decode(),
            'pin_drift', 'taxdmp.zip md5 != sidecar')
    derived = extract_macaca_subtree(folder / 'taxdmp.zip', folder)
    producer = producer_pin()
    receipt = {
        'source': 'NCBI Taxonomy taxdmp (public domain, US Government work, '
                  '17 USC 105): Macaca subtree only (names + ranks), derived '
                  'deterministically from the pinned zip',
        'retrieved_utc': '2026-09-17T00:00:00+00:00',
        'license': 'public domain (US Government work); no copyright asserted '
                   'over the taxonomy dump',
        'derivation': {'producer_module': 'tools/science_funnel/life_fetch.py',
                       'producer_sha256': producer,
                       'law': 'zip bytes -> (macaca_nodes.tsv, macaca_names.tsv) '
                              'is a pure stdlib function of the pinned bytes; '
                              're-derivation must be byte-identical',
                       'root_tax_id': derived['root_tax_id'],
                       'ranks': derived['ranks']},
        'files': [
            {'path': 'taxdmp.zip', 'url': TAXDMP_URL, 'bytes': len(raw),
             'sha256': sha(raw), 'md5': expect_md5.group(1).decode(),
             'note': 'primary artifact; exceeds the 64 MB bundle artifact limit, '
                     'so bundles pin the derived subtree files, not the zip'},
            {'path': 'taxdmp.zip.md5', 'url': TAXDMP_MD5_URL, 'bytes': len(md5_raw),
             'sha256': sha(md5_raw), 'role': 'integrity sidecar'},
            {'path': 'macaca_nodes.tsv', 'url': TAXDMP_URL,
             'bytes': (folder / 'macaca_nodes.tsv').stat().st_size,
             'sha256': derived['nodes_sha256'], 'role': 'derived',
             'derived_by_sha256': producer},
            {'path': 'macaca_names.tsv', 'url': TAXDMP_URL,
             'bytes': (folder / 'macaca_names.tsv').stat().st_size,
             'sha256': derived['names_sha256'], 'role': 'derived',
             'derived_by_sha256': producer},
        ],
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': downloaded, 'receipt_written': wrote, **derived}


# -------------------------------------------------------------------- Rhea

def fetch_rhea():
    folder = DATA_ROOT / 'rhea'
    tsv, tsv_dl = fetch(RHEA_TSV_URL, folder / 'rhea-chebi-smiles.tsv')
    lic, lic_dl = fetch(RHEA_LICENSE_URL, folder / 'LICENSE.txt')
    rel, rel_dl = fetch(RHEA_RELEASE_URL, folder / 'rhea-release.properties')
    head = tsv.decode('utf-8-sig').splitlines()[0]
    require('\t' in head, 'rhea_tsv_layout_changed', head[:80])
    receipt = {
        'source': 'Rhea (Swiss Institute of Bioinformatics) reaction - ChEBI '
                  'participant - SMILES mapping, tsv/rhea-chebi-smiles.tsv',
        'retrieved_utc': '2026-09-17T00:00:00+00:00',
        'license': 'CC BY 4.0 (LICENSE.txt fetched verbatim 2026-09-17: "We '
                   'have chosen to apply the Creative Commons Attribution 4.0 '
                   'International (CC BY 4.0) License ... to all copyrightable '
                   'parts of the Rhea database."); LICENSE.txt is pinned as an '
                   'artifact because it IS the license evidence',
        'files': [
            {'path': 'rhea-chebi-smiles.tsv', 'url': RHEA_TSV_URL,
             'bytes': len(tsv), 'sha256': sha(tsv)},
            {'path': 'LICENSE.txt', 'url': RHEA_LICENSE_URL,
             'bytes': len(lic), 'sha256': sha(lic), 'role': 'license evidence'},
            {'path': 'rhea-release.properties', 'url': RHEA_RELEASE_URL,
             'bytes': len(rel), 'sha256': sha(rel), 'role': 'release identity'},
        ],
    }
    wrote = write_receipt(folder / 'download_receipt.json', receipt)
    return {'downloaded': tsv_dl or lic_dl or rel_dl, 'receipt_written': wrote,
            'tsv_bytes': len(tsv), 'tsv_sha256': sha(tsv)}


def main():
    results = {'schema_version': VERSION, 'pantheria': fetch_pantheria(),
               'ncbi_taxdmp': fetch_ncbi_taxdmp(), 'rhea': fetch_rhea()}
    print(json.dumps({'ok': True, **results}, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
