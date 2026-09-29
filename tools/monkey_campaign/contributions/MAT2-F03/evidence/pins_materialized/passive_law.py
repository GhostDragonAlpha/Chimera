"""MAT2-M04 passive law declaration: chimera.passive_law.v1.

M04-owned strict declaration document for PASSIVE material responses (rigid,
compliant_maxwell, fiber_reinforced). M01's material_state.v1 law vocabulary is
closed at kind 'pressure_deformation' (reserved by M03); this document carries
the passive constitutive declaration WITHOUT widening M01's schema, and pins
the M02 source documents by canonical sha256 so the laws cannot silently
attach to different inputs.

Validation style follows the M01 exemplar (tools/monkey_campaign/contributions/
MAT2-M01/material_state.py): strict fields, named refusal codes, canonical
digests, canonical round-trip. Read-only validation: no solving here.
CPU-only, stdlib-only.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

SCHEMA = 'chimera.passive_law.v1'
_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}')
PROFILE_IDS = ('rigid', 'compliant_maxwell', 'fiber_reinforced')
SOURCE_STATUSES = ('synthetic_authored', 'source_derived', 'geometry_pinned')
DAMPING_MODELS = ('maxwell_series_dashpot',)


def require(condition, code):
    if not condition:
        raise ValueError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key:' + key)
        result[key] = value
    return result


def nonfinite(value):
    raise ValueError('nonfinite_json:' + value)


def decode(raw):
    require(isinstance(raw, (bytes, bytearray, str)),
            'decode_requires_bytes_or_text')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def identity(value, label):
    require(isinstance(value, str) and _ID.fullmatch(value) is not None,
            'invalid_id:' + label)
    return value


def _finite(value, label):
    require(type(value) is float or type(value) is int,
            'invalid_number:' + label)
    require(math.isfinite(value), 'nonfinite_number:' + label)
    return float(value)


def _vec3(value, label):
    require(isinstance(value, list) and len(value) == 3,
            'invalid_vec3:' + label)
    return [_finite(v, label) for v in value]


def _unit_axis(value, label):
    axis = _vec3(value, label)
    norm = math.sqrt(axis[0] ** 2 + axis[1] ** 2 + axis[2] ** 2)
    require(norm > 0.0, 'invalid_fiber_axis:' + label)
    require(math.isclose(norm, 1.0, rel_tol=1e-9, abs_tol=1e-12),
            'invalid_fiber_axis:' + label + ':not_unit_norm')
    return axis


def _pin(value, label):
    require(isinstance(value, str)
            and re.fullmatch(r'[0-9a-f]{64}', value) is not None,
            'invalid_sha256_pin:' + label)
    return value


def validate_passive_law(document):
    """Validate one passive_law document; returns a normalized summary.

    Refusals are named codes (ValueError). No numeric inference or repair.
    """
    require(isinstance(document, dict), 'document_not_object')
    require(document.get('schema') == SCHEMA, 'unsupported_passive_law_schema')
    required = {'schema', 'revision', 'object_id', 'source_documents',
                'gauges', 'profiles', 'directions', 'assignments'}
    allowed = required | {'provenance'}
    require(required <= set(document) <= allowed,
            'unexpected_passive_law_fields')
    require(type(document['revision']) is int and document['revision'] > 0,
            'invalid_revision')
    identity(document['object_id'], 'object_id')

    # ---- pinned source documents (hashes, never coordinates)
    pins = {}
    for row in _rows(document['source_documents'], 'source_documents'):
        require(isinstance(row, dict), 'invalid_source_document_row')
        require(set(row) == {'id', 'path', 'object_id', 'canonical_sha256'},
                'invalid_source_document_fields')
        key = identity(row['id'], 'source_document_id')
        require(key not in pins, 'duplicate_source_document:' + key)
        require(isinstance(row['path'], str) and row['path'].strip(),
                'invalid_source_document_path:' + key)
        identity(row['object_id'], 'source_document_object_id:' + key)
        _pin(row['canonical_sha256'], 'source_document_pin:' + key)
        pins[key] = row
    require(len(pins) >= 1, 'passive_law_without_source_documents')

    # ---- gauges (declared load path; support explicit, never implied)
    gauges = {}
    for row in _rows(document['gauges'], 'gauges'):
        require(isinstance(row, dict), 'invalid_gauge_row')
        require(set(row) == {'id', 'region_id', 'kind', 'axis',
                             'rest_length_m', 'area_m2', 'support',
                             'load_application', 'provenance'},
                'invalid_gauge_fields')
        key = identity(row['id'], 'gauge')
        require(key not in gauges, 'duplicate_gauge:' + key)
        require(row['kind'] == 'uniaxial', 'invalid_gauge_kind:' + key)
        _unit_axis(row['axis'], 'gauge_axis:' + key)
        require(_finite(row['rest_length_m'], 'rest_length_m:' + key) > 0.0,
                'invalid_gauge_rest_length:' + key)
        require(_finite(row['area_m2'], 'area_m2:' + key) > 0.0,
                'invalid_gauge_area:' + key)
        support = row['support']
        require(isinstance(support, dict) and support.get('pinned') is True
                and isinstance(support.get('face'), str)
                and support['face'].strip(),
                'invalid_gauge_support:' + key)
        require(isinstance(row['load_application'], str)
                and row['load_application'].strip(),
                'invalid_gauge_load_application:' + key)
        require(isinstance(row['provenance'], str) and row['provenance'].strip(),
                'invalid_gauge_provenance:' + key)
        gauges[key] = row
    # a pure-rigid document legitimately declares no gauge (rigid takes
    # none); any deformable assignment below re-demands its gauge.

    # ---- profiles (constitutive declaration; parameters explicit)
    profiles = {}
    for row in _rows(document['profiles'], 'profiles'):
        require(isinstance(row, dict), 'invalid_profile_row')
        require(set(row) == {'id', 'constitutive_equation', 'parameters',
                             'source_status', 'damping', 'valid_strain_range',
                             'rest_state'},
                'invalid_profile_fields')
        key = identity(row['id'], 'profile')
        require(key in PROFILE_IDS, 'unknown_profile_kind:' + key)
        require(key not in profiles, 'duplicate_profile:' + key)
        require(isinstance(row['constitutive_equation'], str)
                and row['constitutive_equation'].strip(),
                'invalid_constitutive_equation:' + key)
        params = row['parameters']
        require(isinstance(params, dict), 'invalid_profile_parameters:' + key)
        for pname, pvalue in params.items():
            identity(pname, 'profile_parameter:' + key)
            if isinstance(pvalue, (int, float)) and not isinstance(pvalue, bool):
                _finite(pvalue, 'profile_parameter:' + key + ':' + pname)
            else:
                require(isinstance(pvalue, str) and pvalue.strip(),
                        'invalid_profile_parameter:' + key + ':' + pname)
        require(row['source_status'] in SOURCE_STATUSES,
                'invalid_source_status:' + key)
        damping = row['damping']
        if damping is not None:
            require(isinstance(damping, dict)
                    and damping.get('model') in DAMPING_MODELS,
                    'invalid_damping_model:' + key)
            require(_finite(damping.get('c_N_s_per_m'),
                            'damping_c:' + key) > 0.0,
                    'invalid_damping_c:' + key)
            require(_finite(damping.get('tau_s'), 'damping_tau:' + key) > 0.0,
                    'invalid_damping_tau:' + key)
        if key == 'compliant_maxwell':
            require(damping is not None, 'compliant_requires_damping:' + key)
        else:
            require(damping is None,
                    'damping_declared_only_on_compliant:' + key)
        band = row['valid_strain_range']
        require(isinstance(band, list) and len(band) == 2
                and math.isfinite(_finite(band[0], 'strain_low:' + key))
                and math.isfinite(_finite(band[1], 'strain_high:' + key)),
                'invalid_strain_range:' + key)
        if key == 'rigid':
            require(band == [0.0, 0.0],
                    'rigid_band_must_be_degenerate:' + key)
        else:
            require(band[0] < band[1] and band[0] <= 0.0 <= band[1],
                    'invalid_strain_range:' + key)
        require(isinstance(row['rest_state'], str) and row['rest_state'].strip(),
                'invalid_rest_state:' + key)
        profiles[key] = row

    # ---- directions (fiber axes; distinct from geometry)
    directions = {}
    for row in _rows(document['directions'], 'directions'):
        require(isinstance(row, dict), 'invalid_direction_row')
        require(set(row) == {'id', 'region_id', 'axis', 'frame', 'role'},
                'invalid_direction_fields')
        key = identity(row['id'], 'direction')
        require(key not in directions, 'duplicate_direction:' + key)
        identity(row['region_id'], 'direction_region:' + key)
        _unit_axis(row['axis'], 'direction_axis:' + key)
        require(row['frame'] == 'rest', 'invalid_direction_frame:' + key)
        require(row['role'] == 'fiber_axis', 'invalid_direction_role:' + key)
        directions[key] = row

    # ---- assignments (region -> profile, gauge, direction)
    assignments = {}
    for row in _rows(document['assignments'], 'assignments'):
        require(isinstance(row, dict), 'invalid_assignment_row')
        require({'region_id', 'profile_id', 'gauge_id',
                 'direction_id', 'provenance'} <= set(row) == set(row),
                'invalid_assignment_fields')
        rid = identity(row['region_id'], 'assignment_region')
        require(rid not in assignments, 'duplicate_assignment:' + rid)
        pid = identity(row['profile_id'], 'assignment_profile:' + rid)
        require(pid in profiles, 'assignment_unknown_profile:' + rid + ':' + pid)
        gid = row['gauge_id']
        if gid is not None:
            identity(gid, 'assignment_gauge:' + rid)
            require(gid in gauges, 'assignment_unknown_gauge:' + rid)
            require(gauges[gid]['region_id'] == rid,
                    'assignment_gauge_region_mismatch:' + rid)
        if pid == 'rigid':
            require(gid is None, 'rigid_assignment_takes_no_gauge:' + rid)
        else:
            require(gid is not None, 'deformable_assignment_requires_gauge:' + rid)
        did = row['direction_id']
        if did is not None:
            identity(did, 'assignment_direction:' + rid)
            require(did in directions, 'assignment_unknown_direction:' + rid)
            require(directions[did]['region_id'] == rid,
                    'assignment_direction_region_mismatch:' + rid)
            require(pid == 'fiber_reinforced',
                    'direction_on_non_fiber_profile:' + rid)
        require(isinstance(row['provenance'], str) and row['provenance'].strip(),
                'invalid_assignment_provenance:' + rid)
        assignments[rid] = row

    require(len(assignments) >= 1, 'passive_law_without_assignments')
    for rid, row in assignments.items():
        if row['profile_id'] != 'rigid':
            require(row['gauge_id'] in gauges,
                    'deformable_assignment_missing_gauge:' + rid)

    require('provenance' not in document
            or isinstance(document['provenance'], dict),
            'invalid_provenance')

    # Canonical round-trip must be stable (no NaN/inf, no duplicate keys).
    reloaded = decode(canonical(document))
    require(canonical(reloaded) == canonical(document),
            'canonical_round_trip_broken')

    return {
        'schema': SCHEMA,
        'object_id': document['object_id'],
        'revision': document['revision'],
        'source_documents': sorted(pins),
        'gauge_count': len(gauges),
        'gauge_ids': sorted(gauges),
        'profile_ids': sorted(profiles),
        'direction_count': len(directions),
        'direction_ids': sorted(directions),
        'assigned_regions': sorted(assignments),
        'assignment_count': len(assignments),
        'profile_counts': {
            pid: sum(1 for a in assignments.values() if a['profile_id'] == pid)
            for pid in PROFILE_IDS},
    }


def _rows(value, label):
    require(isinstance(value, list), 'invalid_' + label)
    return value


def summary(document):
    return validate_passive_law(document)


def display(document):
    """Structured display of the declared passive laws (stable ids only)."""
    s = validate_passive_law(document)
    return {
        'schema': SCHEMA,
        'object_id': s['object_id'],
        'revision': s['revision'],
        'source_documents': document['source_documents'],
        'gauges': sorted(document['gauges'], key=lambda g: g['id']),
        'profiles': sorted(document['profiles'], key=lambda p: p['id']),
        'directions': sorted(document['directions'], key=lambda d: d['id']),
        'assignments': sorted(document['assignments'],
                              key=lambda a: a['region_id']),
        'counts': {k: s[k] for k in ('gauge_count', 'direction_count',
                                     'assignment_count', 'profile_counts')},
        'canonical_sha256': digest(canonical(document)),
    }
