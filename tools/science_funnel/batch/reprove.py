"""Re-prove path: an existing admission is replayed under the producer recorded
in its own receipt and byte-compared against the records the graph holds today.

Current code NEVER rewrites history here: pipeline.verify() pins the live
implementation hash, so an old bundle cannot be re-verified after any code
change. The re-proof instead answers the batch question directly -- "do the
pinned artifacts still produce, byte-for-byte, exactly what the graph holds?" --
by replaying the deterministic transform with the RECORDED producer hash."""
import os
from pathlib import Path

from ..common import Refusal, canonical, require, sha
from ..pipeline import transform
from ..adapters import ADAPTERS
from . import connectors as C

DATA_ROOT = Path(C.DATA_ROOT)
# Legacy dirs plus every admitted connector's data dir (lane modules included,
# via the connectors auto-load): a future re-proof must find any admitted
# connector's pinned bytes without this list being edited again.
_SEARCH_DIRS = sorted(set(['force_sources', 'bodyparts3d', 'coolprop', 'earth',
                           'pubchem', 'macaque_arm', 'smithsonian', 'copernicus_glo30'])
                      | {c.get('data_dir') for c in C.CONNECTORS.values()
                         if c.get('mode') == 'admit' and c.get('data_dir')})


def _blob_index():
    """One pass over the data directories: sha256 -> path for every file."""
    index = {}
    for name in _SEARCH_DIRS:
        folder = DATA_ROOT / name
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                index[sha(path.read_bytes())] = path
    return index


def source_object(graph, source_key):
    """Find the data.source.* object for a manifest source id."""
    for obj in graph.objects.values():
        if obj.get('kind') != 'source':
            continue
        funnel = obj.get('science_funnel') or {}
        if funnel.get('manifest', {}).get('source', {}).get('id') == source_key:
            return obj
    raise Refusal('reprove_source_missing', source_key)


def reprove_source(graph, source_key, blob_index=None):
    obj = source_object(graph, source_key)
    funnel = obj['science_funnel']
    manifest, receipt = funnel['manifest'], funnel['receipt']
    raw_manifest = canonical(manifest)
    require(sha(raw_manifest) == receipt['files'].get('manifest.json'),
            'reprove_manifest_bytes_unrecoverable', source_key)
    require(manifest['adapter'] in ADAPTERS, 'reprove_adapter_missing', manifest['adapter'])
    blob_index = blob_index if blob_index is not None else _blob_index()
    blobs = {}
    for art in manifest['artifacts']:
        path = blob_index.get(art['sha256'])
        require(path is not None, 'reprove_artifact_missing', art['id'])
        blobs[art['sha256']] = path.read_bytes()
    # Replay under the RECORDED producer: record ids embed producer_hash, so
    # only the recorded producer can reproduce the admitted ids.
    records, quarantine = transform(manifest, blobs, receipt['implementation'],
                                    sha(raw_manifest))
    # The graph's records for this source are the science_funnel payloads of
    # objects whose provenance names this source object.
    expected = sorted((other['science_funnel'] for other in graph.objects.values()
                       if (other.get('provenance') or {}).get('source_id') == obj['id']
                       and 'science_funnel' in other),
                      key=lambda rec: rec['id'])
    records = sorted(records, key=lambda rec: rec['id'])
    require(canonical(records) == canonical(expected),
            'reprove_replay_mismatch', source_key)
    require(canonical(sorted(quarantine, key=lambda q: canonical(q).decode())) ==
            canonical(sorted(funnel.get('quarantine', []),
                             key=lambda q: canonical(q).decode())),
            'reprove_quarantine_mismatch', source_key)
    require(len(records) == receipt['accepted'], 'reprove_count_identity', source_key)
    require(len(quarantine) == receipt['quarantined'], 'reprove_quarantine_identity',
            source_key)
    return {'source': source_key, 'source_object': obj['id'],
            'records': len(records), 'quarantined': len(quarantine),
            'producer': receipt['implementation']['version'],
            'artifact_pins': [a['sha256'] for a in manifest['artifacts']],
            'records_reproduced_byte_identical': True}
