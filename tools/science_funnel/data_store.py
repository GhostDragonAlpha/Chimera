"""The data store resolution layer (design: validation/data_store_design_20260921/).

RAW acquired datasets live OUTSIDE git in a plain sha256-addressed store
($CHIMERA_DATA_STORE/store/<aa>/<bb>/<sha256>); the only mapping state is the
committed append-only index chimera_data_index.json next to this module
(a wrong entry is superseded, never edited -- the same discipline as receipts).

resolve(rel) -> Path, for rel as receipts cite it today: a path under
tools/science_funnel/data/, e.g. 'wiseman2026/Primate_models.zip'.

  CHIMERA_DATA_STORE unset  -> the in-repo file only: byte-identical behavior to
      pre-store code. This is the pre-migration NO-OP the design requires
      (landing this module cannot break a single gate; its falsifier is the pilot).
  CHIMERA_DATA_STORE set    -> the store blob when the committed index maps rel
      (the blob's address IS its sha256; the bytes are verified against that
      address before every hand-out); falls back to the in-repo file when the
      store is not seeded for rel (fresh machine) or rel is unregistered;
      refuses loudly naming the missing artifact when neither exists -- never a
      silent empty read. (Design section 3.2 lists in-repo first; same contract
      under the pilot's reading: the env var is what turns the store on, the
      in-repo path is the default fallback, and the 7/7 from-store pin
      verification is the preregistered falsifier.)

Pins stay pins: pin=<sha256> makes resolve verify the handed-over bytes against
the caller's pin (wiseman_osim.pinned_bytes keeps enforcing its own manifest pin
on top -- a store blob whose sha IS the address cannot drift; the check protects
the index mapping and the fallback path, not just the bytes).

DERIVED outputs keep landing in-repo first; the repo remains the origin of
derived proof bytes. register() is always an explicit step (receipt-carrying),
never a silent redirect of writes.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path

from .common import Refusal, require

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'tools/science_funnel/data'
INDEX = Path(__file__).resolve().parent / 'chimera_data_index.json'


def _read_index():
    if not INDEX.is_file():
        return {'schema': 'chimera.data_store_index.v1', 'entries': []}
    return json.loads(INDEX.read_text(encoding='utf-8'))


def active_entry(rel):
    """The latest active index entry for rel, or None."""
    hits = [e for e in _read_index().get('entries', [])
            if e.get('logical') == rel and e.get('status', 'active') == 'active']
    return hits[-1] if hits else None


def blob_path(store_root, sha256):
    """sha256 -> <store>/store/<aa>/<bb>/<sha256>: pure arithmetic, no database."""
    return Path(store_root) / 'store' / sha256[:2] / sha256[2:4] / sha256


def require_sha(p, pin, rel):
    require(hashlib.sha256(p.read_bytes()).hexdigest() == pin, 'source_pin_drift', rel)


def _in_repo(rel, must_exist, pin):
    p = (DATA / rel).resolve()
    require(not Path(rel).is_absolute() and p.is_relative_to(DATA.resolve()), 'path_escape', rel)
    if not p.is_file():
        require(not must_exist, 'artifact_missing', f'{rel} resolves to no in-repo file and no store blob')
        return p
    if pin is not None:
        require_sha(p, pin, rel)
    return p


def resolve(rel, must_exist=True, pin=None):
    store = os.environ.get('CHIMERA_DATA_STORE')
    entry = active_entry(rel) if store else None
    if entry is not None:
        blob = blob_path(store, entry['sha256'])
        if blob.is_file():
            require_sha(blob, entry['sha256'], rel)  # the index mapping must not lie
            require(pin is None or entry['sha256'] == pin, 'source_pin_drift',
                    f'{rel} store sha256 {entry["sha256"]} != pinned {pin}')
            return blob
        return _in_repo(rel, must_exist, pin)  # store not seeded: the repo copy still verifies
    return _in_repo(rel, must_exist, pin)


def register_file(src, rel, *, cls, dataset, provenance, registered_by,
                  path_in_git_at_registration=None, registered_utc=None):
    """Content-address one file into $CHIMERA_DATA_STORE; return its index entry.

    Store writes are atomic (tmp staging + rename into the addressed slot); an
    identical blob is never rewritten (duplication across logical names is free).
    register_file addresses the blob and returns the entry; appending it to the
    caller's in-memory index is the caller's move -- one writer per batch, which
    then writes chimera_data_index.json once and COMMITS it.
    """
    store = os.environ.get('CHIMERA_DATA_STORE')
    require(bool(store), 'store_unset', 'CHIMERA_DATA_STORE unset: registration has no store to address into')
    src = Path(src)
    data = src.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    dst = blob_path(store, sha)
    if not dst.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(store) / 'tmp' / (sha[:16] + '.staging')
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(data)
        os.replace(tmp, dst)
    return {'logical': rel, 'path_in_git_at_registration': path_in_git_at_registration,
            'sha256': sha, 'bytes': len(data), 'class': cls, 'dataset': dataset,
            'registered_utc': registered_utc or (datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')),
            'registered_by': registered_by, 'provenance': provenance, 'status': 'active'}
