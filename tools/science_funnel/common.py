"""Small strict data contract shared by source-specific adapters."""
import hashlib
import json
import math
from pathlib import Path

VERSION = '1.0.0'


class Refusal(ValueError):
    def __init__(self, code, detail=''):
        self.code, self.detail = code, str(detail)
        super().__init__(code + (': ' + self.detail if detail else ''))


def require(condition, code, detail=''):
    if not condition:
        raise Refusal(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(canonical(value))


def loads(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_json_key', key)
            result[key] = value
        return result
    def bad(value):
        raise Refusal('nonfinite_json', value)
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad, parse_float=number)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Refusal('invalid_json', exc) from exc


def number(value):
    require(not isinstance(value, bool) and value is not None, 'invalid_number', value)
    try:
        out = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise Refusal('invalid_number', value) from exc
    require(math.isfinite(out), 'nonfinite_number', value)
    return out


def text(value, field):
    require(isinstance(value, str) and value.strip(), 'missing_text', field)
    return value


def local_file(root, relative):
    text(relative, 'path')
    p = (Path(root) / relative).resolve()
    require(not Path(relative).is_absolute() and p.is_relative_to(Path(root).resolve()),
            'path_escape', relative)
    require(p.is_file(), 'artifact_missing', relative)
    return p


def draft(external_id, record_type, payload, *, unknowns=(), label=None):
    return {'external_id': text(external_id, 'external_id'),
            'record_type': record_type, 'label': label or external_id,
            'payload': payload, 'unknowns': sorted(set(unknowns))}
