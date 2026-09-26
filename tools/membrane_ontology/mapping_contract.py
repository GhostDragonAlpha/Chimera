"""Optional source-bound point mapping coupon. Never qualifies physics/runtime."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys

try:
    from .model import canonical, decode, digest, endpoint, require, source_path, text, validate
except ImportError:
    from model import canonical, decode, digest, endpoint, require, source_path, text, validate

SCHEMA = 'chimera.point_mapping.v1'
UNITS = {'m': 1.0, 'mm': 0.001}
LIMIT = 2 * 1024 * 1024


def fields(value, names, label):
    require(isinstance(value, dict) and set(value) == set(names.split()), 'invalid_fields:' + label)


def number(value):
    require(type(value) in (int, float), 'invalid_number')
    try:
        result = float(value)
    except OverflowError:
        raise ValueError('nonfinite_number') from None
    require(math.isfinite(result), 'nonfinite_number')
    require(type(value) is not int or int(result) == value, 'lossy_integer')
    return result


def vector(value):
    require(isinstance(value, list) and len(value) == 3, 'invalid_vector')
    return [number(v) for v in value]


def sha(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'invalid_sha256')


def read(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT, 'artifact_size_limit')
    return raw


def pinned(root, ref):
    fields(ref, 'path raw_sha256', 'artifact_reference')
    source_path(ref['path'])
    sha(ref['raw_sha256'])
    path = (root / ref['path']).resolve()
    require(path.is_relative_to(root), 'artifact_path_escape')
    raw = read(path)
    require(digest(raw) == ref['raw_sha256'], 'artifact_hash_mismatch:' + ref['path'])
    return decode(raw)


def points(root, binding, nodes):
    fields(binding, 'node port representation frame artifact', 'binding')
    port = endpoint({k: binding[k] for k in ('node', 'port')}, nodes)
    require(port['protocol'] == 'point-position-v1', 'unsupported_point_protocol')
    require(port['unit'] in UNITS, 'unsupported_point_unit')
    for key in ('frame', 'representation'):
        text(binding[key], key)
    artifact = pinned(root, binding['artifact'])
    fields(artifact, 'schema representation frame unit points', 'point_artifact')
    require(artifact['schema'] == 'chimera.point_samples.v1', 'unsupported_points_schema')
    for key in ('frame', 'representation'):
        require(artifact[key] == binding[key], key + '_mismatch')
    require(artifact['unit'] == port['unit'], 'point_unit_mismatch')
    require(isinstance(artifact['points'], list) and 0 < len(artifact['points']) <= 10000,
            'invalid_point_count')
    result = {}
    for p in artifact['points']:
        fields(p, 'id position', 'point')
        text(p['id'], 'point_id')
        require(p['id'] not in result, 'duplicate_point_id')
        result[p['id']] = vector(p['position'])
    return result, port['unit']


def check(contract_path, expected_contract_raw_sha256):
    """The caller's external raw-byte pin binds the mapping AND its thresholds."""
    sha(expected_contract_raw_sha256)
    path = Path(contract_path).resolve()
    raw = read(path)
    require(digest(raw) == expected_contract_raw_sha256, 'contract_pin_mismatch')
    contract = decode(raw)
    fields(contract, 'schema ontology source destination mapping validity properties oracle_basis', 'contract')
    require(contract['schema'] == SCHEMA, 'unsupported_mapping_schema')
    root = path.parent
    nodes = validate(pinned(root, contract['ontology']))
    source, source_unit = points(root, contract['source'], nodes)
    destination, destination_unit = points(root, contract['destination'], nodes)
    require(set(source) == set(destination), 'point_correspondence_mismatch')
    text(contract['oracle_basis'], 'oracle_basis')
    fields(contract['properties'], 'position unresolved', 'properties')
    require(contract['properties']['position'] == 'recomputed', 'unsupported_position_disposition')
    unresolved = contract['properties']['unresolved']
    require(isinstance(unresolved, list) and all(isinstance(x, str) and x.strip() for x in unresolved),
            'invalid_unresolved_properties')
    transform = contract['mapping']
    fields(transform, 'kind rotation translation_destination_unit scale', 'mapping')
    require(transform['kind'] == 'rigid_points_with_unit_conversion', 'unsupported_mapping_kind')
    scale = number(transform['scale'])
    require(scale == UNITS[source_unit] / UNITS[destination_unit], 'unit_scale_mismatch')
    rotation = transform['rotation']
    require(isinstance(rotation, list) and len(rotation) == 3, 'invalid_rotation')
    r = [vector(row) for row in rotation]
    # Representation check, never orthogonalize or repair the supplied matrix.
    for i in range(3):
        for j in range(3):
            require(abs(math.fsum(r[i][k] * r[j][k] for k in range(3)) - (i == j)) <= 1e-12,
                    'rotation_not_orthonormal')
    det = (r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])
           - r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])
           + r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0]))
    require(abs(det - 1.0) <= 1e-12, 'rotation_not_proper')
    translation = vector(transform['translation_destination_unit'])
    validity = contract['validity']
    fields(validity, 'source_min source_max max_abs_error_destination_unit', 'validity')
    lower, upper = vector(validity['source_min']), vector(validity['source_max'])
    require(all(a <= b for a, b in zip(lower, upper)), 'invalid_validity_bounds')
    tolerance = number(validity['max_abs_error_destination_unit'])
    require(tolerance >= 0, 'negative_tolerance')
    max_error = 0.0
    for key, point in source.items():
        require(all(lower[i] <= point[i] <= upper[i] for i in range(3)), 'outside_validity_envelope:' + key)
        mapped = [math.fsum(r[i][k] * scale * point[k] for k in range(3)) + translation[i] for i in range(3)]
        require(all(math.isfinite(v) for v in mapped), 'mapped_value_nonfinite')
        errors = [abs(mapped[i] - destination[key][i]) for i in range(3)]
        require(all(math.isfinite(v) for v in errors), 'error_nonfinite')
        max_error = max(max_error, *errors)
    status = 'UNQUALIFIED' if unresolved else ('PASS' if max_error <= tolerance else 'FAIL')
    return {'schema': 'chimera.point_mapping_receipt.v1', 'status': status,
            'contract_raw_sha256': digest(raw), 'ontology_raw_sha256': contract['ontology']['raw_sha256'],
            'source_raw_sha256': contract['source']['artifact']['raw_sha256'],
            'destination_raw_sha256': contract['destination']['artifact']['raw_sha256'],
            'samples': len(source), 'max_abs_error': max_error, 'error_unit': destination_unit,
            'tolerance': tolerance, 'unresolved': unresolved,
            'qualification_scope': 'declared point samples only; oracle independence requires review',
            'runtime_readiness_claimed': False, 'mechanical_qualification_claimed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract')
    parser.add_argument('--expected-contract-sha256', required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8', newline='\n')
    try:
        receipt = check(args.contract, args.expected_contract_sha256)
    except (OSError, ValueError, OverflowError, RecursionError) as exc:
        print(json.dumps({'status': 'REFUSED', 'reason': str(exc)}, ensure_ascii=False))
        return 2
    print(canonical(receipt).decode('utf-8'))
    return 0 if receipt['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
