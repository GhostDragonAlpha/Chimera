"""MAT2-M01 reusable material state: one versioned schema, distinct relation types.

Implements the frozen preregistration (PREREGISTRATION.md, this directory):
regions/shells with rest/current geometry, single-owner mass with explicit
references, material direction/history, pressure/deformation law, and two DISTINCT
mechanical relation kinds -- contact (surface interaction) and bond (explicit
mechanical connection). Containment never creates a bond; mass is counted once;
every identity is a stable ID. Read-only validation and display: no solver, no
engine, no physics execution. CPU-only, stdlib-only.

Validation style follows tools/membrane_ontology/model.py (strict JSON, named
refusal codes, canonical digests, matter_claims owner/reference roles).
"""
from __future__ import annotations

import hashlib
import json
import math
import re

SCHEMA = 'chimera.material_state.v1'
_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}')
REGION_KINDS = ('region', 'shell')
LAW_KINDS = ('pressure_deformation',)
BOND_STATUS = ('planned', 'source_declared', 'qualified')
CONTACT_STATES = ('separated', 'touching', 'loaded')


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
    require(isinstance(raw, (bytes, bytearray, str)), 'decode_requires_bytes_or_text')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def identity(value, label):
    require(isinstance(value, str) and _ID.fullmatch(value) is not None,
            'invalid_id:' + label)
    return value


def _finite(value, label):
    require(type(value) is float or type(value) is int, 'invalid_number:' + label)
    require(math.isfinite(value), 'nonfinite_number:' + label)
    return float(value)


def _vec3(value, label):
    require(isinstance(value, list) and len(value) == 3, 'invalid_vec3:' + label)
    return [_finite(v, label) for v in value]


def _rows(value, label):
    require(isinstance(value, list), 'invalid_list:' + label)
    return value


def _matter_claims(row, key, owners):
    claims = row.get('matter_claims', [])
    require(isinstance(claims, list), 'invalid_matter_claims:' + key)
    for claim in claims:
        require(isinstance(claim, dict) and set(claim) == {'matter_id', 'role'},
                'invalid_matter_claim:' + key)
        identity(claim['matter_id'], 'matter_id:' + key)
        require(claim['role'] in ('owner', 'reference'), 'invalid_matter_role:' + key)
        if claim['role'] == 'owner':
            require(claim['matter_id'] not in owners,
                    'duplicate_matter_owner:' + claim['matter_id'])
            owners[claim['matter_id']] = key


def validate_material_state(document):
    """Validate one material_state document; returns a normalized summary dict.

    Refusals are named codes (ValueError). No numeric inference or repair.
    """
    require(isinstance(document, dict), 'document_not_object')
    require(document.get('schema') == SCHEMA, 'unsupported_material_state_schema')
    required = {'schema', 'revision', 'object_id', 'regions', 'matter',
                'directions', 'laws', 'contacts', 'bonds'}
    allowed = required | {'renames', 'provenance'}
    require(required <= set(document) <= allowed, 'unexpected_material_state_fields')
    require(type(document['revision']) is int and document['revision'] > 0,
            'invalid_revision')
    identity(document['object_id'], 'object_id')

    # ---- regions and shells (containment via parent; never a bond)
    regions = {}
    owners = {}
    for row in _rows(document['regions'], 'regions'):
        require(isinstance(row, dict), 'invalid_region_row')
        require({'id', 'kind', 'parent', 'rest_geometry', 'current_geometry'}
                <= set(row) <= {'id', 'kind', 'parent', 'rest_geometry',
                                'current_geometry', 'matter_claims', 'sources',
                                'ports'},
                'invalid_region_fields')
        key = identity(row['id'], 'region')
        require(key not in regions, 'duplicate_region:' + key)
        require(row['kind'] in REGION_KINDS, 'invalid_region_kind:' + key)
        parent = row['parent']
        if parent is not None:
            identity(parent, 'parent:' + key)
        require(isinstance(row['rest_geometry'], dict), 'invalid_rest_geometry:' + key)
        require(isinstance(row['current_geometry'], dict), 'invalid_current_geometry:' + key)
        _matter_claims(row, key, owners)
        regions[key] = row
    for key, row in regions.items():
        parent = row['parent']
        require(parent is None or parent in regions, 'missing_region_parent:' + key)
        if parent is not None:
            require(parent != key, 'region_self_containment:' + key)
    # containment acyclicity + shell/region role: a shell may enclose, a region
    # may nest under either kind; cycles are refused either way.
    for key in regions:
        seen = set()
        cursor = key
        while cursor is not None:
            require(cursor not in seen, 'containment_cycle:' + key)
            seen.add(cursor)
            cursor = regions[cursor]['parent']

    # ---- matter with exactly one owner each; references never re-own
    matter = {}
    for row in _rows(document['matter'], 'matter'):
        require(isinstance(row, dict), 'invalid_matter_row')
        require(set(row) == {'id', 'mass_kg', 'provenance'}, 'invalid_matter_fields')
        key = identity(row['id'], 'matter')
        require(key not in matter, 'duplicate_matter:' + key)
        mass = _finite(row['mass_kg'], 'mass_kg:' + key)
        require(mass >= 0.0, 'negative_mass:' + key)
        require(isinstance(row['provenance'], str) and row['provenance'].strip(),
                'invalid_matter_provenance:' + key)
        require(key in owners, 'unowned_matter:' + key)
        matter[key] = row
    for claimed in owners:
        require(claimed in matter, 'owner_claim_without_matter:' + claimed)

    # ---- material direction/history (distinct from geometry and law)
    directions = {}
    for row in _rows(document['directions'], 'directions'):
        require(isinstance(row, dict), 'invalid_direction_row')
        require({'id', 'region_id', 'axis', 'history'} <= set(row)
                <= {'id', 'region_id', 'axis', 'history', 'frame'},
                'invalid_direction_fields')
        key = identity(row['id'], 'direction')
        require(key not in directions, 'duplicate_direction:' + key)
        region_id = identity(row['region_id'], 'direction_region:' + key)
        require(region_id in regions, 'missing_direction_region:' + key)
        axis = _vec3(row['axis'], 'axis:' + key)
        norm = math.sqrt(axis[0] ** 2 + axis[1] ** 2 + axis[2] ** 2)
        require(norm > 0.0, 'zero_material_direction:' + key)
        history = _rows(row['history'], 'history:' + key)
        last = None
        for entry in history:
            require(isinstance(entry, dict) and set(entry) == {'revision', 'state'},
                    'invalid_history_entry:' + key)
            require(type(entry['revision']) is int and entry['revision'] >= 0,
                    'invalid_history_revision:' + key)
            require(isinstance(entry['state'], str) and entry['state'].strip(),
                    'invalid_history_state:' + key)
            require(last is None or entry['revision'] >= last,
                    'history_not_monotonic:' + key)
            last = entry['revision']
        directions[key] = row

    # ---- pressure/deformation law (declared parameters, never inferred)
    laws = {}
    for row in _rows(document['laws'], 'laws'):
        require(isinstance(row, dict), 'invalid_law_row')
        require({'id', 'kind', 'regions', 'parameters', 'provenance'} <= set(row),
                'invalid_law_fields')
        key = identity(row['id'], 'law')
        require(key not in laws, 'duplicate_law:' + key)
        require(row['kind'] in LAW_KINDS, 'invalid_law_kind:' + key)
        region_ids = _rows(row['regions'], 'law_regions:' + key)
        require(len(region_ids) > 0, 'law_without_regions:' + key)
        for rid in region_ids:
            identity(rid, 'law_region:' + key)
            require(rid in regions, 'missing_law_region:' + key)
        params = row['parameters']
        require(isinstance(params, dict) and len(params) > 0, 'invalid_law_parameters:' + key)
        for pname, pvalue in params.items():
            identity(pname, 'law_parameter:' + key)
            if isinstance(pvalue, (int, float)) and not isinstance(pvalue, bool):
                _finite(pvalue, 'law_parameter:' + key + ':' + pname)
            else:
                require(isinstance(pvalue, str) and pvalue.strip(),
                        'invalid_law_parameter:' + key + ':' + pname)
        require(isinstance(row['provenance'], str) and row['provenance'].strip(),
                'invalid_law_provenance:' + key)
        laws[key] = row

    # ---- relation endpoints: every mechanical edge names existing region ports
    ports = {}
    for key, row in regions.items():
        for port in row.get('ports', []):
            require(isinstance(port, dict) and {'id', 'protocol', 'unit'} <= set(port),
                    'invalid_port:' + key)
            pid = identity(port['id'], 'port:' + key)
            require((key, pid) not in ports, 'duplicate_port:' + key + ':' + pid)
            require(isinstance(port['protocol'], str) and port['protocol'].strip(),
                    'invalid_port_protocol:' + key + ':' + pid)
            require(isinstance(port['unit'], str) and port['unit'].strip(),
                    'invalid_port_unit:' + key + ':' + pid)
            ports[(key, pid)] = port

    def endpoints(rows, label):
        require(isinstance(rows, list) and len(rows) >= 1, 'invalid_' + label)
        seen = set()
        resolved = []
        for end in rows:
            require(isinstance(end, dict) and set(end) == {'region_id', 'port'},
                    'invalid_endpoint:' + label)
            rid = identity(end['region_id'], 'endpoint_region:' + label)
            pid = identity(end['port'], 'endpoint_port:' + label)
            require((rid, pid) in ports, 'missing_endpoint_port:' + rid + ':' + pid)
            pair = (rid, pid)
            require(pair not in seen, 'duplicate_endpoint:' + label)
            seen.add(pair)
            resolved.append(end)
        return resolved

    # ---- contact: surface interaction relation (distinct type)
    contacts = {}
    for row in _rows(document['contacts'], 'contacts'):
        require(isinstance(row, dict), 'invalid_contact_row')
        require({'id', 'endpoints', 'state'} <= set(row) <= {'id', 'endpoints', 'state',
                                                             'interface'},
                'invalid_contact_fields')
        key = identity(row['id'], 'contact')
        require(key not in contacts, 'duplicate_contact:' + key)
        endpoints(row['endpoints'], 'contact_endpoints:' + key)
        require(row['state'] in CONTACT_STATES, 'invalid_contact_state:' + key)
        contacts[key] = row

    # ---- bond: explicit mechanical connection (distinct type; never implied)
    bonds = {}
    for row in _rows(document['bonds'], 'bonds'):
        require(isinstance(row, dict), 'invalid_bond_row')
        require({'id', 'endpoints', 'status'} <= set(row) <= {'id', 'endpoints',
                                                              'status', 'transfers'},
                'invalid_bond_fields')
        key = identity(row['id'], 'bond')
        require(key not in bonds, 'duplicate_bond:' + key)
        resolved = endpoints(row['endpoints'], 'bond_endpoints:' + key)
        require(len(resolved) >= 2, 'bond_requires_explicit_endpoints:' + key)
        require(row['status'] in BOND_STATUS, 'invalid_bond_status:' + key)
        transfers = row.get('transfers', 'force_moment')
        require(transfers in ('force', 'force_moment'), 'invalid_bond_transfers:' + key)
        bonds[key] = row

    # ---- declared renames keep region identity stable across revisions
    renames = document.get('renames', {})
    require(isinstance(renames, dict), 'invalid_renames')
    for old, new in renames.items():
        identity(old, 'rename_old')
        identity(new, 'rename_new')
        require(old not in regions, 'rename_of_live_region:' + old)
        require(new in regions, 'rename_target_missing:' + old)
        require(old != new, 'rename_identity:' + old)

    require(bool(renames) is False or 'provenance' in document,
            'renames_require_provenance')
    # Canonical round-trip must be stable (no NaN/inf, no duplicate-key input).
    reloaded = decode(canonical(document))
    require(canonical(reloaded) == canonical(document), 'canonical_round_trip_broken')

    total_mass = 0.0
    for row in matter.values():
        total_mass += float(row['mass_kg'])
    return {
        'object_id': document['object_id'],
        'revision': document['revision'],
        'region_count': len(regions),
        'shell_count': sum(1 for r in regions.values() if r['kind'] == 'shell'),
        'region_ids': sorted(regions),
        'matter_count': len(matter),
        'owner_count': len(owners),
        'reference_count': sum(1 for r in regions.values()
                               for c in r.get('matter_claims', [])
                               if c['role'] == 'reference'),
        'total_mass_kg': total_mass,
        'direction_count': len(directions),
        'law_count': len(laws),
        'contact_count': len(contacts),
        'bond_count': len(bonds),
        'port_count': len(ports),
        'renames': dict(renames),
        'schema': SCHEMA,
    }


def display(document):
    """Structured display of one object's actual regions and graph relations.

    Stable IDs only. Mass is summarized once per owned matter id; references are
    counted, never re-owned. Containment and mechanical relations are listed as
    separate relation kinds. CPU-only JSON, not pixels.
    """
    summary = validate_material_state(document)
    regions = {r['id']: r for r in document['regions']}
    containment = [{'child': r['id'], 'parent': r['parent']}
                   for r in document['regions'] if r['parent'] is not None]
    containment.sort(key=lambda e: (e['parent'], e['child']))
    owners = {}
    references = []
    for r in document['regions']:
        for claim in r.get('matter_claims', []):
            if claim['role'] == 'owner':
                owners[claim['matter_id']] = r['id']
            else:
                references.append({'matter_id': claim['matter_id'], 'region_id': r['id']})
    mass_rows = []
    for m in document['matter']:
        mass_rows.append({'matter_id': m['id'], 'owner_region': owners.get(m['id']),
                          'mass_kg': m['mass_kg'], 'provenance': m['provenance']})
    mass_rows.sort(key=lambda e: e['matter_id'])
    return {
        'schema': SCHEMA,
        'object_id': summary['object_id'],
        'revision': summary['revision'],
        'regions': [{'id': r['id'], 'kind': r['kind'], 'parent': r['parent'],
                     'rest_geometry': r['rest_geometry'],
                     'current_geometry': r['current_geometry']}
                    for r in sorted(document['regions'], key=lambda r: r['id'])],
        'relations': {
            'containment': containment,
            'contacts': sorted(({'id': c['id'], 'endpoints': c['endpoints'],
                                 'state': c['state']}
                                for c in document['contacts']),
                               key=lambda e: e['id']),
            'bonds': sorted(({'id': b['id'], 'endpoints': b['endpoints'],
                              'status': b['status'], 'transfers': b.get('transfers',
                                                                        'force_moment')}
                             for b in document['bonds']),
                            key=lambda e: e['id']),
            'note': 'containment is not a bond; bonds and contacts are distinct types',
        },
        'mass_summary': {
            'total_mass_kg': summary['total_mass_kg'],
            'owned_matter': mass_rows,
            'reference_claims': len(references),
            'note': 'each matter id is owned once; references never re-own mass',
        },
        'material_directions': sorted(({'id': d['id'], 'region_id': d['region_id'],
                                        'axis': d['axis'], 'history': d['history'],
                                        'frame': d.get('frame', 'rest')}
                                       for d in document['directions']),
                                      key=lambda e: e['id']),
        'laws': sorted(({'id': l['id'], 'kind': l['kind'], 'regions': l['regions'],
                         'parameters': l['parameters'], 'provenance': l['provenance']}
                        for l in document['laws']),
                       key=lambda e: e['id']),
        'counts': {k: summary[k] for k in ('region_count', 'shell_count', 'matter_count',
                                           'owner_count', 'reference_count',
                                           'direction_count', 'law_count',
                                           'contact_count', 'bond_count', 'port_count')},
        'canonical_sha256': digest(canonical(document)),
    }


def check_revision_compatibility(previous, current):
    """Region identity stability across revisions: an id may disappear only via a
    declared rename (the rename maps old -> an existing current id). Refuses
    region_identity_drift otherwise."""
    prev = validate_material_state(previous)
    curr = validate_material_state(current)
    lawfully_absent = set(prev['renames']) | set(curr['renames'])
    for rid in prev['region_ids']:
        if rid not in curr['region_ids'] and rid not in lawfully_absent:
            raise ValueError('region_identity_drift:' + rid)
    for old, new in curr['renames'].items():
        require(new in curr['region_ids'], 'rename_target_missing:' + old)
    for old, new in prev['renames'].items():
        require(new in curr['region_ids'] or new in lawfully_absent,
                'rename_chain_broken:' + old)
    return {'previous_revision': prev['revision'], 'current_revision': curr['revision'],
            'stable_region_ids': sorted(set(prev['region_ids'])
                                        & set(curr['region_ids'])),
            'renames_applied': sorted(curr['renames'].items())}


def total_mass_once(document):
    """Independent mass oracle: sum each matter id exactly once, keyed by owner.
    Used by tests to detect double counting through references or nesting."""
    owners = {}
    for r in document['regions']:
        for claim in r.get('matter_claims', []):
            if claim['role'] == 'owner':
                require(claim['matter_id'] not in owners,
                        'duplicate_matter_owner:' + claim['matter_id'])
                owners[claim['matter_id']] = r['id']
    masses = {m['id']: float(m['mass_kg']) for m in document['matter']}
    require(set(owners) == set(masses), 'matter_ownership_mismatch')
    total = 0.0
    for mid in sorted(masses):
        total += masses[mid]
    return total
