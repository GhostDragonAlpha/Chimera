"""Read-only membrane containment and port-contract validation. No physics execution."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re

MAX_DEFINITION = 2 * 1024 * 1024
MAX_SOURCE = 32 * 1024 * 1024
SCHEMA = 'chimera.membrane_ontology.v1'


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
    require(len(raw) <= MAX_DEFINITION, 'definition_size_limit')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), 'invalid_text:' + label)


def identity(value, label):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value),
            'invalid_id:' + label)


def source_path(value):
    text(value, 'source')
    require('\\' not in value and ':' not in value and not value.startswith('/')
            and not PureWindowsPath(value).is_absolute()
            and all(p not in ('', '.', '..') for p in value.split('/')),
            'unsafe_source_path:' + value)


def endpoint(value, nodes):
    require(isinstance(value, dict) and set(value) == {'node', 'port'}, 'invalid_endpoint')
    identity(value['node'], 'endpoint_node')
    identity(value['port'], 'endpoint_port')
    require(value['node'] in nodes, 'missing_endpoint_node:' + value['node'])
    ports = {p['id']: p for p in nodes[value['node']]['ports']}
    require(value['port'] in ports, 'missing_endpoint_port:' + value['node'] + ':' + value['port'])
    return ports[value['port']]


def compatible(a, b):
    require(a['protocol'] == b['protocol'], 'port_protocol_mismatch')
    require(a['unit'] == b['unit'], 'port_unit_mismatch')


def validate(definition):
    require(isinstance(definition, dict) and definition.get('schema') == SCHEMA,
            'unsupported_ontology_schema')
    require(set(definition) == {'schema', 'revision', 'root', 'authority', 'nodes'},
            'unexpected_definition_fields')
    require(type(definition['revision']) is int and definition['revision'] > 0, 'invalid_revision')
    identity(definition['root'], 'root')
    text(definition['authority'], 'authority')
    rows = definition['nodes']
    require(isinstance(rows, list) and 0 < len(rows) <= 5000, 'invalid_nodes')
    nodes = {}
    required = {'id', 'name', 'parent', 'kind', 'description', 'boundary', 'physics',
                'validation', 'ports', 'sources', 'gaps'}
    allowed = required | {'endpoints', 'connection_status', 'matter_claims'}
    owners = {}
    for original in rows:
        require(isinstance(original, dict) and required <= set(original) <= allowed, 'invalid_node_fields')
        row = deepcopy(original)
        key = row['id']
        identity(key, 'node')
        require(key not in nodes, 'duplicate_node:' + key)
        for field in ('name', 'kind', 'description'):
            text(row[field], key + ':' + field)
        if row['parent'] is not None:
            identity(row['parent'], key + ':parent')
        for field in ('boundary', 'physics', 'validation'):
            require(isinstance(row[field], dict), 'invalid_' + field + ':' + key)
        text(row['boundary'].get('description'), key + ':boundary_description')
        text(row['physics'].get('status'), key + ':physics_status')
        for field in ('status', 'statement', 'prediction', 'falsifier'):
            text(row['validation'].get(field), key + ':validation_' + field)
        for field in ('sources', 'gaps'):
            require(isinstance(row[field], list) and all(isinstance(s, str) for s in row[field]),
                    'invalid_' + field + ':' + key)
        for path in row['sources']:
            source_path(path)
        require(isinstance(row['ports'], list), 'invalid_ports:' + key)
        port_ids = set()
        for port in row['ports']:
            require(isinstance(port, dict) and {'id', 'protocol', 'unit', 'description'} <= set(port)
                    <= {'id', 'protocol', 'unit', 'description', 'delegates_to'}, 'invalid_port:' + key)
            identity(port['id'], 'port')
            require(port['id'] not in port_ids, 'duplicate_port:' + key + ':' + port['id'])
            port_ids.add(port['id'])
            for field in ('protocol', 'unit', 'description'):
                text(port[field], key + ':port_' + field)
        require(isinstance(row.get('matter_claims', []), list), 'invalid_matter_claims:' + key)
        for claim in row.get('matter_claims', []):
            require(isinstance(claim, dict) and set(claim) == {'matter_id', 'role'}, 'invalid_matter_claim')
            identity(claim['matter_id'], 'matter_id')
            require(claim['role'] in ('owner', 'reference'), 'invalid_matter_role')
            if claim['role'] == 'owner':
                require(claim['matter_id'] not in owners, 'duplicate_matter_owner:' + claim['matter_id'])
                owners[claim['matter_id']] = key
        row.update(children=[], path=[], connections=[])
        nodes[key] = row
    root = definition['root']
    require(root in nodes, 'root_missing')
    require([key for key, row in nodes.items() if row['parent'] is None] == [root], 'root_count_or_identity')
    for key, row in nodes.items():
        parent = row['parent']
        require(parent is None or parent in nodes, 'missing_parent:' + key)
        if parent is not None:
            nodes[parent]['children'].append(key)
    for key, row in nodes.items():
        seen, cursor, chain = set(), key, []
        while cursor is not None:
            require(cursor not in seen, 'containment_cycle:' + key)
            require(len(chain) < 256, 'containment_depth_limit')
            seen.add(cursor)
            chain.append(cursor)
            cursor = nodes[cursor]['parent']
        require(chain[-1] == root, 'disconnected_node:' + key)
        row['path'] = list(reversed(chain))
    for key, row in nodes.items():
        for port in row['ports']:
            if 'delegates_to' in port:
                target = port['delegates_to']
                other = endpoint(target, nodes)
                require(key in nodes[target['node']]['path'][:-1], 'port_exposure_not_descendant:' + key)
                compatible(port, other)
        if row['kind'] == 'connection':
            ends = row.get('endpoints')
            require(isinstance(ends, list) and 2 <= len(ends) <= 64, 'invalid_connection_endpoints:' + key)
            require(row.get('connection_status') in ('planned', 'source_declared', 'qualified'),
                    'invalid_connection_status:' + key)
            seen = set()
            first = None
            for end in ends:
                p = endpoint(end, nodes)
                pair = (end['node'], end['port'])
                require(pair not in seen, 'duplicate_connection_endpoint:' + key)
                seen.add(pair)
                if first is not None:
                    compatible(first, p)
                first = p
                if key not in nodes[end['node']]['connections']:
                    nodes[end['node']]['connections'].append(key)
        else:
            require('endpoints' not in row and 'connection_status' not in row, 'endpoints_on_nonconnection:' + key)
    # Also detects non-finite Python callers' numbers; no numeric inference/repair.
    canonical(definition)
    return nodes


def inspect_source(root, relative):
    source_path(relative)
    target = (root / relative).resolve()
    require(target.is_relative_to(root), 'source_link_escape:' + relative)
    result = dict(path=relative, status='missing', raw_sha256=None, bytes=None)
    try:
        before = target.stat()
        require(target.is_file(), 'source_not_file')
        require(before.st_size <= MAX_SOURCE, 'source_size_limit')
        with target.open('rb') as stream:
            raw = stream.read(MAX_SOURCE + 1)
        after = target.stat()
        require(len(raw) <= MAX_SOURCE, 'source_size_limit')
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'source_changed_during_read')
        result.update(status='present', raw_sha256=digest(raw), bytes=len(raw))
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as exc:
        result.update(status='unreadable', reason=str(exc))
    return result


def snapshot(definition_path, source_root):
    path = Path(definition_path)
    with path.open('rb') as stream:
        raw = stream.read(MAX_DEFINITION + 1)
    definition = decode(raw)
    nodes = validate(definition)
    root = Path(source_root).resolve()
    sources = [inspect_source(root, ref) for ref in sorted({s for n in nodes.values() for s in n['sources']})]
    warnings = [dict(code='source_' + s['status'], node=None, detail=s['path'])
                for s in sources if s['status'] != 'present']
    warnings += [dict(code='binding_gap', node=n['id'], detail=gap) for n in nodes.values() for gap in n['gaps']]
    payload = dict(schema='chimera.membrane_ontology.snapshot.v1', revision=definition['revision'],
                   root=definition['root'], authority=definition['authority'],
                   definition_raw_sha256=digest(raw), nodes=list(nodes.values()), sources=sources,
                   checks=dict(structural_valid=True, membranes=len(nodes),
                               ports=sum(len(n['ports']) for n in nodes.values()),
                               connections=sum(n['kind'] == 'connection' for n in nodes.values()),
                               missing_sources=sum(s['status'] != 'present' for s in sources)),
                   warnings=warnings,
                   limits=['Authored composition; runtime readiness is not evaluated.',
                           'Present sources and reported qualification labels are not independently verified physics.',
                           'Source files are read individually, not as an atomic repository snapshot.',
                           'Hashes detect content changes; they do not authenticate an author.',
                           'No engine, model, training, task registry or material compiler is executed.'])
    payload['snapshot_sha256'] = digest(canonical(payload))
    return payload
