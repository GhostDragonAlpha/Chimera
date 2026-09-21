"""Register wiseman2026's gitignored raw corpus (+ the 7 in-git DERIVED models)
into the content-addressed store, per the design's phase-1 pilot.

Sources, every byte receipt-pinned BEFORE registration:
  zip       E:/ChimeraData/tmp/Primate_models.zip
            (re-fetched 2026-09-21 from the download_receipt.json Zenodo route;
            sha256 6cb8e29a... + md5 330b8e8a... + bytes 20,510,615 verified at fetch;
            the local acquisition-lane copies were lost to the worktree janitor,
            so this registration IS the design's receipt-driven rebuild, exercised)
  extracted E:/ChimeraData/tmp/wiseman2026_extract/<member>
            (extracted from that zip; 272/272 entries verified byte-exact against
            wiseman2026/sha256_manifest.json before this script runs)
  models    tools/science_funnel/data/wiseman2026/models/<Taxon>_model.osim
            (in-git DERIVED blobs, re-verified against the manifest here; git
            remains their origin -- registration enables uniform store resolution)

Writes: blobs under $CHIMERA_DATA_STORE/store/<aa>/<bb>/<sha256> (atomic, idempotent)
and the committed append-only index tools/science_funnel/chimera_data_index.json.
Idempotent: re-running appends nothing for logical names already active with the
same sha256.
"""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
os.environ.setdefault('CHIMERA_DATA_STORE', 'E:/ChimeraData')

from tools.science_funnel import data_store as DS  # noqa: E402

DATASET = 'wiseman2026'
MANIFEST = json.loads((REPO / 'tools/science_funnel/data/wiseman2026/sha256_manifest.json').read_text(encoding='utf-8'))
STORE = Path(os.environ['CHIMERA_DATA_STORE'])
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
BY = 'agent/data-store-pilot-20260921 (GLM 5.3)'

ZIP_PROV = ('re-fetched 2026-09-21 from Zenodo record 20041122 via download_receipt.json '
            '(sha256 6cb8e29ad6d7664beb19ed8f5f6aadeef0153f49dd0aea052135c846768f6181, '
            'md5 330b8e8a6af66ea22f4023ca60829cad, 20510615 B verified at fetch); '
            'local copies lost to worktree janitor - receipt-driven rebuild')
EXT_PROV = ('extracted from Primate_models.zip (sha256 6cb8e29a...) and verified byte-exact '
            'against wiseman2026/sha256_manifest.json (272/272 entries, bytes+sha256)')
MODEL_PROV = ('in-git DERIVED blob at registration; git remains origin; registered for '
              'uniform store resolution (design section 3.2)')


def main():
    entries = {e['path']: e for e in MANIFEST['files']}
    raw_zip = entries['Primate_models.zip']
    ext = [e for e in MANIFEST['files'] if e['path'].startswith('_extracted/')]
    models = [e for e in MANIFEST['files'] if e['path'].startswith('models/')]

    index = DS._read_index()
    already = {e['logical'] for e in index.get('entries', []) if e.get('status', 'active') == 'active'}
    registered, skipped = [], []

    def register(src, logical, manifest_entry, cls, prov, git_path):
        if logical in already:
            skipped.append(logical)
            return
        # pre-registration pin check: the bytes MUST equal the manifest pin before addressing
        data = Path(src).read_bytes()
        got = hashlib.sha256(data).hexdigest()
        if got != manifest_entry['sha256'] or len(data) != manifest_entry['bytes']:
            raise SystemExit(f'PIN FAIL before registration: {logical}')
        idx, ent = DS.register_file(src, logical, cls=cls, dataset=DATASET, provenance=prov,
                                    registered_by=BY, registered_utc=NOW,
                                    path_in_git_at_registration=git_path)
        index.update(idx)
        registered.append(ent)

    zip_src = STORE / 'tmp' / 'Primate_models.zip'
    register(zip_src, f'{DATASET}/Primate_models.zip', raw_zip, 'RAW', ZIP_PROV, None)
    for e in ext:
        member = e['path'][len('_extracted/'):]
        register(STORE / 'tmp' / 'wiseman2026_extract' / member, f'{DATASET}/{e["path"]}', e, 'RAW', EXT_PROV, None)
    for e in models:
        git_path = f'tools/science_funnel/data/wiseman2026/{e["path"]}'
        register(REPO / git_path, f'{DATASET}/{e["path"]}', e, 'DERIVED', MODEL_PROV, git_path)

    # write the committed index: append-only shaped, sorted by logical for reviewable diffs
    index['created_utc'] = index.get('created_utc', NOW)
    index['note'] = 'append-only: a wrong entry is superseded (status), never edited'
    index['entries'] = sorted(index.get('entries', []), key=lambda e: (e['logical'], e['registered_utc']))
    DS.INDEX.write_text(json.dumps(index, indent=1, sort_keys=True) + '\n', encoding='utf-8')

    # verify: every registered entry's store blob exists and sha-matches
    bad = []
    for e in index['entries']:
        if e['dataset'] != DATASET:
            continue
        blob = DS.blob_path(STORE, e['sha256'])
        if not blob.is_file() or hashlib.sha256(blob.read_bytes()).hexdigest() != e['sha256']:
            bad.append(e['logical'])
    total_bytes = sum(e['bytes'] for e in index['entries'] if e['dataset'] == DATASET)
    print(f'registered now: {len(registered)} (skipped already-active: {len(skipped)})')
    print(f'index entries for {DATASET}: {sum(1 for e in index["entries"] if e["dataset"] == DATASET)}')
    print(f'registered bytes total: {total_bytes}')
    print(f'store blobs verified: {sum(1 for e in index["entries"] if e["dataset"] == DATASET) - len(bad)}/{sum(1 for e in index["entries"] if e["dataset"] == DATASET)}')
    if bad:
        print('BAD:', bad[:10]); return 1

    receipt = {
        'schema': 'chimera.data_store_pilot_registration.v1',
        'written_utc': NOW, 'registered_by': BY,
        'store_root': str(STORE),
        'index_file': 'tools/science_funnel/chimera_data_index.json',
        'registered_now': len(registered), 'skipped_already_active': len(skipped),
        'classes': {
            'RAW': {'files': 1 + len(ext), 'bytes': raw_zip['bytes'] + sum(x['bytes'] for x in ext)},
            'DERIVED': {'files': len(models), 'bytes': sum(x['bytes'] for x in models)}},
        'total_registered_bytes': total_bytes,
        'pin_prechecks': 'all passed (bytes+sha256 vs sha256_manifest.json, before addressing)',
        'store_blob_verify': f'{sum(1 for e in index["entries"] if e["dataset"] == DATASET) - len(bad)}/{sum(1 for e in index["entries"] if e["dataset"] == DATASET)}',
        'fetch_event': ZIP_PROV,
    }
    out = Path(__file__).resolve().parent / 'registration_receipt.json'
    out.write_text(json.dumps(receipt, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print('receipt:', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
