"""Pinned, replayable intake bundles. Parallel writers never edit the project graph."""
from collections import defaultdict
from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET
from .adapters import ADAPTERS
from .common import VERSION, Refusal, canonical, digest, local_file, loads, require, sha, text

MAX_ARTIFACT_BYTES = 64 * 1024 * 1024  # intake resource limit, not a physical constant
MAX_BUNDLE_BYTES = 256 * 1024 * 1024


def implementation():
    root = Path(__file__).resolve().parent
    files = {p.name: sha(p.read_bytes()) for p in sorted(root.glob('*.py'))
             if not p.name.startswith('test_')}
    parser = root.parent / 'reference_data' / 'parsers.py'
    files['reference_data/parsers.py'] = sha(parser.read_bytes())
    return {'version': VERSION, 'files': files}


def validate_manifest(manifest):
    require(isinstance(manifest, dict) and manifest.get('schema_version') == VERSION,
            'manifest_schema_unsupported')
    require(manifest.get('adapter') in ADAPTERS, 'adapter_unsupported', manifest.get('adapter'))
    source = manifest.get('source', {})
    require(isinstance(source, dict), 'source_required')
    for key in ('id', 'release', 'license', 'url'):
        text(source.get(key), 'source.' + key)
    require(isinstance(manifest.get('artifacts'), list) and manifest['artifacts'], 'artifacts_required')
    ids = []
    for art in manifest['artifacts']:
        require(isinstance(art, dict), 'artifact_record_required')
        ids.append(text(art.get('id'), 'artifact.id'))
        text(art.get('path'), 'artifact.path')
        pin = art.get('sha256')
        require(isinstance(pin, str) and len(pin) == 64 and
                all(c in '0123456789abcdef' for c in pin), 'artifact_pin_required')
        require(art.get('role', 'data') in ('data', 'attachment'), 'artifact_role_unsupported')
    require(len(set(ids)) == len(ids), 'duplicate_artifact_id')
    require(any(a.get('role', 'data') == 'data' for a in manifest['artifacts']), 'data_artifact_required')
    for key in ('conditions', 'condition_columns', 'columns', 'constants', 'quantity_map', 'unit_map'):
        require(isinstance(manifest.get(key, {}), dict), 'manifest_mapping_required', key)
    return manifest


def transform(manifest, blobs, producer, manifest_pin):
    """Source-local IDs are revisioned; conflicting rows retain both raw inputs in quarantine."""
    validate_manifest(manifest)
    accepted, quarantine = [], []
    source = manifest['source']
    # Include the exact manifest bytes as well as its semantics. Otherwise two
    # bundles with differently formatted manifests can accidentally share record
    # IDs but point those records at different immutable bundle source nodes.
    source_version = digest({'manifest': manifest, 'manifest_sha256': manifest_pin})
    with tempfile.TemporaryDirectory(prefix='chimera-funnel-parse-') as temp:
        # Materialize EVERY pinned artifact before parsing any: adapters may
        # read declared companions (a second list named by sha256) that are
        # listed after the data artifact they belong to.
        for art in manifest['artifacts']:
            raw = blobs[art['sha256']]
            require(sha(raw) == art['sha256'], 'pin_drift', art['id'])
            (Path(temp) / art['sha256']).write_bytes(raw)
        for art in manifest['artifacts']:
            if art.get('role') == 'attachment':
                continue
            raw = blobs[art['sha256']]
            path = Path(temp) / art['sha256']
            try:
                rows = ADAPTERS[manifest['adapter']](raw, manifest, path)
                require(rows, 'empty_capture', art['id'])
                # Force strict JSON validation before accepting any part of an artifact.
                rows = loads(canonical(rows))
            except (Refusal, ValueError, TypeError, KeyError, UnicodeError, ET.ParseError) as exc:
                rows = [{'location': 'artifact', 'refusal': {
                    'code': exc.code if isinstance(exc, Refusal) else 'parse_failed',
                    'detail': str(exc)}}]
            for row in rows:
                if 'refusal' in row:
                    quarantine.append({'artifact': art['id'], 'sha256': art['sha256'], **row})
                    continue
                record = {**row, 'schema_version': VERSION,
                          'authority': 'external_assertion', 'runtime_ready': False,
                          'source': source, 'source_version': source_version,
                          'artifact': {'id': art['id'], 'sha256': art['sha256']},
                          'adapter': manifest['adapter'], 'producer_hash': digest(producer)}
                record['id'] = 'data.assertion.' + digest(record)
                accepted.append(record)
    groups = defaultdict(list)
    for record in accepted:
        groups[record['external_id']].append(record)
    accepted = []
    for external, records in groups.items():
        if len(records) > 1:
            quarantine.append({'location': 'source:' + external, 'refusal': {
                'code': 'duplicate_source_identity',
                'detail': 'All competing records withheld; no greedy first-match selection.'},
                'records': records})
        else:
            accepted.append(records[0])
    return sorted(accepted, key=lambda r: r['id']), sorted(quarantine, key=canonical)


def ingest(manifest_path, output_root):
    """Copy a consistent snapshot, compare expected hashes, parse offline, publish atomically."""
    manifest_path = Path(manifest_path).resolve()
    raw_manifest = manifest_path.read_bytes()
    manifest = validate_manifest(loads(raw_manifest))
    blobs, total = {}, 0
    for art in manifest['artifacts']:
        path = local_file(manifest_path.parent, art['path'])
        require(path.stat().st_size <= MAX_ARTIFACT_BYTES, 'artifact_too_large', art['id'])
        raw = path.read_bytes()
        require(len(raw) <= MAX_ARTIFACT_BYTES, 'artifact_too_large', art['id'])
        total += len(raw)
        require(total <= MAX_BUNDLE_BYTES, 'bundle_too_large')
        require(sha(raw) == art['sha256'], 'pin_drift', art['id'])
        blobs[art['sha256']] = raw
    producer = implementation()
    records, quarantine = transform(manifest, blobs, producer, sha(raw_manifest))
    content = {'manifest.json': raw_manifest, 'records.json': canonical(records),
               'quarantine.json': canonical(quarantine)}
    content.update({'blobs/' + pin: raw for pin, raw in blobs.items()})
    receipt = {'schema_version': VERSION, 'implementation': producer,
               'files': {name: sha(raw) for name, raw in sorted(content.items())},
               'accepted': len(records), 'quarantined': len(quarantine)}
    receipt['bundle_id'] = digest(receipt)
    content['receipt.json'] = canonical(receipt)
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    dest = root / receipt['bundle_id']
    if dest.exists():
        verify(dest)
        require(all(local_file(dest, n).read_bytes() == b for n, b in content.items()),
                'bundle_identity_collision')
        return dest
    temp = Path(tempfile.mkdtemp(prefix='.intake-', dir=root))
    try:
        for name, raw in content.items():
            p = temp / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
        try:
            temp.rename(dest)
        except OSError:
            if not dest.exists():
                raise
            verify(dest)
            require(all(local_file(dest, n).read_bytes() == b for n, b in content.items()),
                    'bundle_identity_collision')
    finally:
        if temp.exists():
            require(temp.resolve().parent == root and temp.name.startswith('.intake-'),
                    'temporary_directory_escape')
            shutil.rmtree(temp)  # exact directory created above, never a supplied path
    return dest


def verify(bundle):
    root = Path(bundle).resolve()
    receipt = loads(local_file(root, 'receipt.json').read_bytes())
    require(receipt.get('schema_version') == VERSION, 'bundle_schema_unsupported')
    body = {k: v for k, v in receipt.items() if k != 'bundle_id'}
    require(digest(body) == receipt.get('bundle_id') == root.name, 'bundle_identity_mismatch')
    require(receipt['implementation'] == implementation(), 'producer_version_mismatch')
    for name, pin in receipt['files'].items():
        require(sha(local_file(root, name).read_bytes()) == pin, 'bundle_bytes_changed', name)
    manifest = validate_manifest(loads(local_file(root, 'manifest.json').read_bytes()))
    expected_files = {'manifest.json', 'records.json', 'quarantine.json'} | {
        'blobs/' + a['sha256'] for a in manifest['artifacts']}
    require(set(receipt['files']) == expected_files, 'bundle_file_inventory_mismatch')
    blobs = {a['sha256']: local_file(root, 'blobs/' + a['sha256']).read_bytes()
             for a in manifest['artifacts']}
    records, quarantine = transform(manifest, blobs, receipt['implementation'],
                                    sha(local_file(root, 'manifest.json').read_bytes()))
    require(canonical(records) == local_file(root, 'records.json').read_bytes() and
            canonical(quarantine) == local_file(root, 'quarantine.json').read_bytes(),
            'intake_replay_mismatch')
    require(receipt['accepted'] == len(records) and receipt['quarantined'] == len(quarantine),
            'bundle_count_mismatch')
    return {'receipt': receipt, 'manifest': manifest, 'records': records, 'quarantine': quarantine}
