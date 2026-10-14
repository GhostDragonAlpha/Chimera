"""Content-addressed graph proposals; no importer owns a graph commit."""
import copy
from pathlib import Path
from .common import VERSION, canonical, digest, loads, require
from .pipeline import verify

KINDS = {'entity': 'reference_entity', 'relation': 'relationship',
         'unit_definition': 'reference_entity', 'measurement': 'property_assertion',
         'series': 'property_assertion', 'geometry': 'geometry_asset', 'model': 'model_definition'}


def graph_from(path):
    from tools.creature_graph.store import CreatureGraph
    from tools.creature_graph.schema import SCHEMA_VERSION
    raw = loads(Path(path).read_bytes())
    # Accept a native file or the result (or service response) of graph_snapshot.
    raw = raw.get('result', raw)
    if 'graph' not in raw:
        g = CreatureGraph.load(str(path))
        require(not g.check(), 'graph_invalid')
        return g
    payload = raw['graph']
    require(payload.get('meta', {}).get('schema_version') == SCHEMA_VERSION, 'graph_schema_unsupported')
    g = CreatureGraph()
    g.objects = copy.deepcopy(payload['objects'])
    g.relations = copy.deepcopy(payload['relations'])
    g.layout = copy.deepcopy(payload.get('layout', {}))
    g.meta = copy.deepcopy(payload.get('meta', {}))
    require(not g.check(), 'graph_invalid')
    require(raw.get('graph_hash') == g.graph_hash(), 'snapshot_hash_mismatch')
    return g


def propose(bundle, graph):
    data = verify(bundle)
    receipt, manifest = data['receipt'], data['manifest']
    require(data['records'], 'no_accepted_records')
    bundle_id = receipt['bundle_id']
    source_id = 'data.source.' + bundle_id
    source = {'id': source_id, 'kind': 'source', 'name': manifest['source']['id'],
              'status': 'extracted', 'science_funnel': {'schema_version': VERSION,
              'bundle_id': bundle_id, 'manifest': manifest, 'receipt': receipt,
              'quarantine': data['quarantine'],
              'storage': 'chimera-intake:' + bundle_id,
              'authority': 'external_assertion', 'runtime_ready': False}}
    objects, edges = [source], []
    for rec in data['records']:
        obj = {'id': rec['id'], 'kind': KINDS[rec['record_type']], 'name': rec['label'],
               'status': 'extracted', 'provenance': {'source_id': source_id,
               'external_id': rec['external_id'], 'source_version': rec['source_version']},
               'science_funnel': rec, 'unknowns': rec['unknowns'],
               'spatial': None, 'geometry': None, 'physical': None,
               'notes': 'Source assertion; explicit reduction and instance binding required.'}
        if rec['record_type'] == 'measurement':
            obj.update(value=rec['payload']['value_si'], units=rec['payload']['unit_si'],
                       applicability=rec['payload']['conditions'])
        if rec.get('class_contract'):
            obj['class_contract'] = rec['class_contract']
        objects.append(obj)
        edges.append({'src': obj['id'], 'rel': 'derived_from', 'dst': source_id,
                      'note': 'Pinned intake bundle ' + bundle_id})
    # Reify source relations as assertion nodes: anatomy concepts stay concepts,
    # never accidentally become physical attachments between creature instances.
    by_external = {r['external_id']: r['id'] for r in data['records']}
    for rec in data['records']:
        claims = []
        payload = rec['payload']
        if manifest['adapter'] == 'uberon_obo':
            claims.extend(('is_a', target) for target in payload.get('is_a', []))
            claims.extend(tuple(pair) for pair in payload.get('relationships', []))
        elif manifest['adapter'] == 'qudt_ttl':
            claims.extend(('qudt:hasQuantityKind', 'quantitykind:' + name)
                          for name in payload.get('quantity_kinds', []))
            claims.extend(('qudt:applicableUnit', 'unit:' + name)
                          for name in payload.get('applicable_units', []))
        for ordinal, (predicate, target) in enumerate(claims):
            target_id = by_external.get(target)
            assertion = {'subject': rec['id'], 'predicate': predicate,
                         'object_external_id': target, 'object': target_id,
                         'ordinal': ordinal, 'bundle_id': bundle_id,
                         'authority': 'external_assertion', 'runtime_ready': False}
            obj = {'id': 'data.relation.' + digest(assertion), 'kind': 'mapping',
                   'name': rec['external_id'] + ' ' + predicate + ' ' + target,
                   'status': 'extracted', 'mapping_type': 'source_relation',
                   'provenance': {'source_id': source_id}, 'science_funnel': assertion,
                   'unknowns': [] if target_id else ['relation_target_outside_intake:' + target]}
            objects.append(obj)
            for role, endpoint in [('source', source_id), ('subject', rec['id']), ('object', target_id)]:
                if endpoint:
                    edges.append({'src': obj['id'], 'rel': 'derived_from', 'dst': endpoint,
                                  'note': 'Source relation ' + role})
    return checked_patch(objects, edges, graph, bundle_id=bundle_id)


def checked_patch(objects, edges, graph, **metadata):
    from tools.creature_graph.schema import validate_object
    # Native storage is JSON. Normalize tuple/list and numeric representations
    # before identity comparisons so readback and re-admission are identical.
    objects = loads(canonical(objects))
    edges = loads(canonical(edges))
    candidate = copy.deepcopy(graph)
    for obj in objects:
        require(not validate_object(obj), 'proposal_object_invalid', obj['id'])
        previous = candidate.objects.get(obj['id'])
        require(previous is None or previous == obj, 'immutable_graph_identity_conflict', obj['id'])
        candidate.objects[obj['id']] = copy.deepcopy(obj)
    for edge in edges:
        require(edge['rel'] == 'derived_from', 'proposal_relation_unsupported')
        if not any(all(old.get(k) == v for k, v in edge.items()) for old in candidate.relations):
            candidate.relate(**edge)
    require(not candidate.check(), 'proposal_graph_invalid')
    return {'operation': 'graph_apply', 'payload': {'expected_hash': graph.graph_hash(),
             'objects': objects, 'relations': edges}, 'metadata': {
             **metadata, 'authority': 'proposal_only', 'runtime_ready': False,
             'candidate_graph_hash': candidate.graph_hash()}}


def reduction_proposal(result, graph):
    for oid in result['input_ids']:
        require(oid in graph.objects, 'reduction_input_not_admitted', oid)
    require(result['target_id'] in graph.objects, 'reduction_target_missing')
    obj = {'id': result['id'], 'kind': 'mapping', 'name': result['law'] + ' candidate',
           'status': 'extracted', 'provenance': {'source_id': 'local:derived'},
           'mapping_type': 'derived_candidate', 'science_funnel': result,
           'unknowns': result['blockers'], 'value': result['result']['value_si'],
           'units': result['result']['unit_si'], 'source': result['input_ids'],
           'applicability': result['request'].get('context', {})}
    edges = [{'src': obj['id'], 'rel': 'derived_from', 'dst': oid,
              'note': 'Explicit selected reduction input'} for oid in result['input_ids']]
    return checked_patch([obj], edges, graph, reduction=result['id'])
