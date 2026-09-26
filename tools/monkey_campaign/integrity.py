"""Named JSON-content hashing. No secret, signature, or human identity is implied."""
import hashlib
import json
from pathlib import Path
import re

ALGORITHM='sha256-chimera-json-v1'


def unique_object(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise ValueError('duplicate_json_key:'+key)
        out[key]=value
    return out


def reject_constant(value):
    raise ValueError('nonfinite_json_number:'+value)


def strict_load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=unique_object,parse_constant=reject_constant)


def content_digest(data):
    raw=json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,
                   allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def verify_catalog(path,lock_path,expected_digest=None,require_anchor=False):
    data=strict_load(path);lock=strict_load(lock_path)
    if lock.get('algorithm')!=ALGORITHM:raise ValueError('unsupported_integrity_algorithm')
    actual=content_digest(data)
    recorded=lock.get('scope_sha256')
    if recorded!=actual:raise ValueError('APPROVED_LIST_CHANGED: do not regenerate approval; submit a change proposal')
    if expected_digest is not None:
        if not re.fullmatch('[0-9a-f]{64}',expected_digest):raise ValueError('invalid_trusted_digest')
        if expected_digest!=actual:raise ValueError('TRUST_ANCHOR_MISMATCH: list and/or colocated lock were replaced')
    elif require_anchor:
        raise ValueError('TRUST_ANCHOR_REQUIRED: use the human-pinned digest, not a newly computed value')
    return data,{'algorithm':ALGORITHM,'scope_sha256':actual,
                 'external_digest_checked':expected_digest is not None,
                 'authentication':'No digital signature. Human approval is the externally pinned baseline, not this lock file.'}
