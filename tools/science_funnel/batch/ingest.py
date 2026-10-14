"""Admit path: stage pinned artifacts, build manifests, create intake bundles.
Parallel lanes over connectors (process fan-out); staging re-hashes every
artifact every run, so byte drift fails loud before any bundle is written."""
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ..common import VERSION, canonical, require, sha
from ..pipeline import ingest as bundle_ingest
from . import connectors as C

DATA_ROOT = Path(C.DATA_ROOT)


def _resolve_artifact(connector, art):
    """Artifacts live in the connector's own data dir; a CROSS-CONNECTOR pin
    (an artifact owned by another connector's data dir, e.g. the taxdmp names
    companion staged inside the pantheria bundle) resolves from another data
    dir only when the file's bytes match the pin exactly."""
    primary = DATA_ROOT / connector['data_dir'] / art['id']
    if primary.is_file():
        return primary
    for other in sorted(path for path in DATA_ROOT.iterdir() if path.is_dir()):
        candidate = other / art['id']
        if candidate.is_file() and sha(candidate.read_bytes()) == art['sha256']:
            return candidate
    return primary


def stage_connector(connector_id, work_root):
    """Copy pinned artifacts into the manifest workspace, re-hashing each file.

    A byte change on disk vs the recorded receipt pin refuses here (pin_drift)
    -- this is the batch's pin-refusal falsifier, before any parsing."""
    connector = C.CONNECTORS[connector_id]
    folder = Path(work_root) / connector_id
    (folder / 'artifacts').mkdir(parents=True, exist_ok=True)
    for art in connector['artifacts']:
        pinned = _resolve_artifact(connector, art)
        require(pinned.is_file(), 'connector_artifact_missing', art['id'])
        raw = pinned.read_bytes()
        require(sha(raw) == art['sha256'], 'pin_drift', art['id'])
        dest = folder / art['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            require(dest.read_bytes() == raw, 'stage_identity_collision', art['id'])
        else:
            dest.write_bytes(raw)
    manifest = {'schema_version': VERSION, 'adapter': connector['adapter'],
                'source': connector['source'], 'artifacts': connector['artifacts']}
    if connector.get('constants'):
        manifest['constants'] = connector['constants']
    path = folder / 'manifest.json'
    path.write_bytes(canonical(manifest))
    return path


def _lane(connector_id, work_root):
    manifest_path = stage_connector(connector_id, work_root)
    bundle = bundle_ingest(str(manifest_path), str(Path(work_root) / 'bundles'))
    return connector_id, str(bundle)


def admit_connectors(connector_ids, work_root, workers=None):
    """Run every admit connector in its own process lane; bundles are
    content-addressed so concurrent creation is safe."""
    require(connector_ids, 'no_connectors_selected')
    workers = workers or min(len(connector_ids), 4)
    results = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_lane, cid, str(work_root)) for cid in connector_ids]
        for future in futures:
            connector_id, bundle = future.result()
            results[connector_id] = bundle
    return results
