"""Contract verification fan-out: every record of every admitted or re-proven
class is checked against its class contract's mechanical falsifiers, in
process-parallel chunks, with the count identity asserted per connector."""
from concurrent.futures import ProcessPoolExecutor

from ..common import Refusal, canonical, require
from ..pipeline import verify as bundle_verify
from . import connectors as C
from .contract import load_registry, run_contract


def _chunk_run(class_id, contract_json, records, ctx_blob_pins, known_ids):
    import json as _json
    contract = _json.loads(contract_json)
    ctx = {'blob_pins': set(ctx_blob_pins), 'known_ids': set(known_ids)}
    return class_id, run_contract(contract, records, ctx)


def _view(record, objects_by_id):
    """Contract-check view: the record's own fields plus the graph object's
    provenance (provenance.source_id lives on the object, not the record)."""
    view = dict(record)
    obj = objects_by_id.get(record['id'])
    if obj is not None:
        view['provenance'] = obj.get('provenance', view.get('provenance', {}))
    return view


def verify_bundle(connector_id, bundle_path, graph, patch_objects, registry=None, workers=4):
    """Verify one admitted bundle: pipeline replay + contract checks + counts."""
    registry = registry or load_registry()
    data = bundle_verify(bundle_path)
    records, quarantine, receipt = data['records'], data['quarantine'], data['receipt']
    require(len(records) == receipt['accepted'], 'bundle_count_mismatch', connector_id)
    blob_pins = [a['sha256'] for a in data['manifest']['artifacts']]
    objects_by_id = dict(graph.objects)
    for obj in patch_objects:
        objects_by_id[obj['id']] = obj
    known_ids = set(objects_by_id)
    by_class = {}
    for record in records:
        class_id = record.get('class_contract', {}).get('class_id') \
            or C.class_for(connector_id, record['record_type'])
        require(class_id in registry, 'record_class_unmapped',
                record['id'] + ':' + str(record['record_type']))
        by_class.setdefault(class_id, []).append(_view(record, objects_by_id))
    results = []
    if by_class:
        jobs = [(cid, canonical(registry[cid]).decode(), recs, blob_pins, sorted(known_ids))
                for cid, recs in by_class.items()]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_chunk_run, cid, cjson, recs, pins, ids)
                       for cid, cjson, recs, pins, ids in jobs]
            results = [future.result()[1] for future in futures]
    counts = {'records': len(records), 'quarantined': len(quarantine),
              'accepted_claimed': receipt['accepted'],
              'quarantine_claimed': receipt['quarantined']}
    require(counts['records'] == counts['accepted_claimed']
            and counts['quarantined'] == counts['quarantine_claimed'],
            'count_identity_failed', connector_id)
    return {'connector': connector_id, 'bundle': str(bundle_path),
            'bundle_id': receipt['bundle_id'], 'counts': counts,
            'classes': results,
            'quarantine': [q.get('refusal', {}).get('code', 'unknown') for q in quarantine]}


def verify_reprove(graph, source_key, replay, registry=None):
    """Contract-check the re-proven records too (they predate class contracts;
    the default class mapping applies)."""
    registry = registry or load_registry()
    obj_id = replay['source_object']
    pairs = [(other['science_funnel'], other) for other in graph.objects.values()
             if (other.get('provenance') or {}).get('source_id') == obj_id
             and 'science_funnel' in other]
    by_class = {}
    for record, obj in pairs:
        class_id = record.get('class_contract', {}).get('class_id') \
            or C.class_for(None, record['record_type'])
        require(class_id in registry, 'record_class_unmapped', record['id'])
        by_class.setdefault(class_id, []).append(_view(record, graph.objects))
    ctx = {'blob_pins': set(replay['artifact_pins']), 'known_ids': set(graph.objects)}
    results = [run_contract(registry[cid], recs, ctx) for cid, recs in sorted(by_class.items())]
    return {'source': source_key, 'records': len(pairs), 'classes': results}
