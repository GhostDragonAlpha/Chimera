"""Per-class mechanical falsifiers: the checks a class contract declares run
against every record of the class, every batch, with no silent drops."""
import json
import math
import os
import re

from ..common import VERSION, Refusal, canonical, require

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'creature_graph',
                             'data', 'authored', 'class_contracts.json')


def load_registry(path=None):
    """Load the authored class-contract store (the single authority)."""
    with open(path or REGISTRY_PATH, encoding='utf-8') as stream:
        payload = json.load(stream)
    require(payload.get('schema_version') == 'chimera.class_contracts.v1',
            'class_contract_schema_unsupported')
    contracts = {}
    for contract in payload['contracts']:
        cid = contract['class_id']
        require(cid not in contracts, 'class_contract_duplicate', cid)
        for field in ('statement', 'prediction', 'falsifier'):
            require(isinstance(contract.get(field), str) and contract[field].strip(),
                    'class_contract_rule0', cid + ':' + field)
        require(contract.get('checks'), 'class_contract_checks_required', cid)
        contracts[cid] = contract
    return contracts


def _resolve(record, dotted):
    node = record
    for part in dotted.split('.'):
        if not isinstance(node, dict) or part not in node:
            return None, False
        node = node[part]
    return node, True


def _check_id_syntax(record, params, ctx):
    if not re.match(params['pattern'], record.get('id', '')):
        return 'id fails syntax ' + params['pattern']
    return None


def _check_provenance_present(record, params, ctx):
    source = record.get('source') or {}
    for key in ('id', 'release', 'license', 'url'):
        if not isinstance(source.get(key), str) or not source[key].strip():
            return 'source.' + key + ' missing'
    artifact = record.get('artifact') or {}
    if not artifact.get('id') or not artifact.get('sha256'):
        return 'artifact pin missing'
    return None


def _check_sha256_chain(record, params, ctx):
    pin = (record.get('artifact') or {}).get('sha256', '')
    if not (isinstance(pin, str) and len(pin) == 64
            and all(c in '0123456789abcdef' for c in pin)):
        return 'artifact pin is not a sha256'
    if ctx is not None and pin not in ctx.get('blob_pins', set()):
        return 'artifact pin not present in the verified bundle bytes'
    return None


def _check_fk_exists(record, params, ctx):
    value, ok = _resolve(record, params['field'])
    if not ok or not isinstance(value, str) or not value:
        return params['field'] + ' missing'
    if ctx is not None and value not in ctx.get('known_ids', set()):
        return params['field'] + ' dangling: ' + value
    return None


SI_TOKENS = {'m', 'kg', 's', 'A', 'K', 'mol', 'cd', 'N', 'Pa', 'J', 'W', 'C', 'V', 'F',
             'ohm', 'S', 'T', 'Wb', 'Hz', 'kat', 'lm', 'lx', 'Bq', 'Gy', 'Sv', 'rad',
             'sr', 'degree', 'dimensionless'}


def _si_tokens_ok(unit):
    """Every alphabetic token of a compound SI unit string must be a known SI
    symbol (m3/(kg*s2) -> m, kg, s)."""
    token = ''
    for char in unit + ' ':
        if char.isalpha():
            token += char
        else:
            if token and token not in SI_TOKENS:
                return False
            token = ''
    return True


def _check_units_in(record, params, ctx):
    value, ok = _resolve(record, params.get('path', 'payload.unit_si'))
    if not ok or not isinstance(value, str) or not value.strip():
        return 'units missing at ' + params.get('path', 'payload.unit_si')
    vocabulary = params.get('vocabulary')
    if vocabulary is not None and value not in vocabulary:
        return 'unit ' + repr(value) + ' outside declared vocabulary'
    if params.get('si_tokens') and not _si_tokens_ok(value):
        return 'unit ' + repr(value) + ' contains non-SI tokens'
    return None


def _check_field_range(record, params, ctx):
    value, ok = _resolve(record, params['path'])
    if not ok or not isinstance(value, (int, float)) or isinstance(value, bool):
        return params['path'] + ' missing or non-numeric'
    if not math.isfinite(value):
        return params['path'] + ' non-finite'
    if not (params['min'] <= value <= params['max']):
        return (params['path'] + ' = ' + repr(value) + ' outside ['
                + repr(params['min']) + ', ' + repr(params['max']) + ']')
    return None


def _check_field_in(record, params, ctx):
    value, ok = _resolve(record, params['field'])
    if not ok or not isinstance(value, str) or not value.strip():
        return params['field'] + ' missing'
    if value not in params['vocabulary']:
        return params['field'] + ' = ' + repr(value) + ' outside declared vocabulary'
    return None


def _walk_numbers(node):
    if node is None or isinstance(node, bool):
        return
    if isinstance(node, (int, float)):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _walk_numbers(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_numbers(value)


def _check_numeric_tree_range(record, params, ctx):
    """Envelope every numeric leaf under a payload subtree. Absent or empty
    subtrees pass: presence is the adapter's job (a row with nothing measured
    must never become a record); this check is the envelope on what did."""
    value, ok = _resolve(record, params['path'])
    if not ok or not value:
        return None
    for leaf in _walk_numbers(value):
        if not (math.isfinite(leaf) and params['min'] <= leaf <= params['max']):
            return (params['path'] + ' value ' + repr(leaf) + ' outside ['
                    + repr(params['min']) + ', ' + repr(params['max']) + ']')
    return None


CHECKS = {
    'id_syntax': _check_id_syntax,
    'provenance_present': _check_provenance_present,
    'sha256_chain': _check_sha256_chain,
    'fk_exists': _check_fk_exists,
    'units_in': _check_units_in,
    'field_range': _check_field_range,
    'field_in': _check_field_in,
    'numeric_tree_range': _check_numeric_tree_range,
}


def run_contract(contract, records, ctx=None):
    """Run one class contract over its records. Any failing check quarantines
    exactly that record; nothing is dropped silently."""
    require(contract['checks'], 'class_contract_checks_required', contract['class_id'])
    failures = []
    for record in records:
        for check in contract['checks']:
            kind = check['kind']
            require(kind in CHECKS, 'class_contract_check_unknown', kind)
            try:
                failure = CHECKS[kind](record, check.get('params', {}), ctx)
            except Refusal as exc:
                failure = exc.code + ': ' + exc.detail
            if failure:
                failures.append({'id': record.get('id', '<no-id>'),
                                 'check': kind, 'detail': failure})
    return {'class_id': contract['class_id'], 'version': contract['version'],
            'records': len(records), 'failures': failures,
            'passed': len(records) - len({f['id'] for f in failures})}
