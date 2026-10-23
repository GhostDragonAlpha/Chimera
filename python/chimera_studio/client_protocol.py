# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small JSON file protocol. Importable by pinned external Python without bpy."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
SESSIONS = ROOT / '.user' / 'clients'
SCHEMA = 'chimera.studio.client.v1'
MAX_REQUEST = 128 * 1024
MAX_REPLY = 1024 * 1024
FRESH_SECONDS = 10
RETENTION_SECONDS = 60


def identity(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{32}', value):
        raise ValueError('Expected a 32-character session, request or operation identity')
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result: raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=_pairs,
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))


def _file_access(operation):
    # Atomic replacement can briefly collide with a Windows file handle.
    # Retry only the same I/O operation, never dispatch a Blender command again.
    for attempt in range(6):
        try: return operation()
        except PermissionError:
            if attempt == 5: raise
            time.sleep(.05)


def read(path, limit=MAX_REPLY):
    def load():
        with Path(path).open('rb') as stream: return stream.read(limit + 1)
    raw = _file_access(load)
    if len(raw) > limit: raise ValueError(f'JSON is {len(raw)} bytes; the limit is {limit} bytes')
    return parse(raw)


def atomic(path, value, limit=MAX_REPLY):
    path = Path(path)
    raw = canonical(value).encode('utf-8')
    if len(raw) > limit: raise ValueError(f'JSON is {len(raw)} bytes; the limit is {limit} bytes')
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream: stream.write(raw)
        _file_access(lambda: os.replace(temporary, path))
    finally:
        temporary.unlink(missing_ok=True)


def request(value, session, request_id):
    keys = {'schema', 'session', 'id', 'method', 'args', 'expires'}
    if not isinstance(value, dict) or set(value) != keys or value['schema'] != SCHEMA:
        raise ValueError('Unsupported request envelope')
    if identity(value['session']) != session or identity(value['id']) != request_id:
        raise ValueError('Request does not belong to this session or filename')
    if not isinstance(value['method'], str) or not isinstance(value['args'], dict):
        raise ValueError('Method must be a name and args an object')
    expires = value['expires']
    if type(expires) not in (int, float) or not math.isfinite(expires):
        raise ValueError('Invalid request deadline')
    if expires < time.time(): raise ValueError('Request expired without execution; inspect before retry')
    if expires > time.time() + 31: raise ValueError('Request deadline exceeds 30 seconds')
    return value


def oversize_reply(error, session, request_id, fingerprint=None):
    # Fixed, short text: the fallback itself must always fit in MAX_REPLY.
    return {'ok': False, 'schema': SCHEMA, 'session': session, 'id': request_id,
            'request_sha256': fingerprint,
            'error': 'ValueError: reply ' + error + '; the operation MAY HAVE EXECUTED.'
                     ' Retrieve current state via status or the operation history;'
                     ' do not repeat the request automatically.',
            'completed': time.time()}
