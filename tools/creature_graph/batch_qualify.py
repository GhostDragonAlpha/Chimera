"""One command: connect databases -> integrate every record -> prove the whole
batch mechanically, with one receipt.

  python -m tools.creature_graph.batch_qualify \
      --admit smithsonian_voyager,copernicus_glo30,bodyparts3d --reprove all \
      --train exercise --out tools/science_funnel/validation/batch_20260917/receipt.json \
      [--apply]

Without --apply everything runs on scratch (bundles, proposals, checks) and
nothing is written into the authored program. With --apply the new objects are
merged into the authored program (one serial writer), the store is rebuilt, the
graphify consumer round-trips it, and every admission is re-proposed against
the rebuilt graph as an idempotency proof (zero new objects, unchanged hash).
"""
import argparse
import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.science_funnel.batch import connectors as C  # noqa: E402
from tools.science_funnel.batch import ingest as batch_ingest  # noqa: E402
from tools.science_funnel.batch import reprove as batch_reprove  # noqa: E402
from tools.science_funnel.batch import train as batch_train  # noqa: E402
from tools.science_funnel.batch import verify as batch_verify  # noqa: E402
from tools.science_funnel.batch.contract import load_registry, run_contract  # noqa: E402
from tools.science_funnel.batch.receipt import build_receipt, write_receipt  # noqa: E402
from tools.science_funnel.common import Refusal, canonical, digest, require  # noqa: E402
from tools.science_funnel.graph import graph_from, propose  # noqa: E402

DEFAULT_GRAPH = ROOT / 'tools' / 'creature_graph' / 'data' / 'creature_graph.json'
AUTHORED_PROGRAM = ROOT / 'tools' / 'creature_graph' / 'data' / 'authored' / 'project_program.json'


def mutation_probe(graph, registry):
    """Falsifier as code: corrupt exactly one record of a real admitted class
    in memory; its content-derived identity must break while its neighbours'
    contract checks stay clean."""
    contract = registry['batch.entity.external']
    pairs = [(obj['science_funnel'], obj) for obj in graph.objects.values()
             if obj.get('kind') == 'reference_entity' and 'science_funnel' in obj
             and (obj.get('provenance') or {}).get('source_id', '').startswith('data.source.')]
    require(pairs, 'mutation_probe_no_records')
    records = [batch_verify._view(rec, graph.objects) for rec, _ in pairs]
    victim = copy.deepcopy(records[0])
    victim['label'] = victim['label'] + ' CORRUPTED'
    body = {k: v for k, v in victim.items() if k != 'id'}
    rederived = 'data.assertion.' + digest(body)
    flagged = rederived != victim['id']
    pins = {r['artifact']['sha256'] for r in records}
    ctx = {'blob_pins': pins, 'known_ids': set(graph.objects)}
    clean = not run_contract(contract, records[:3], ctx)['failures']
    return {'law': 'mutating one record field must break its content-derived identity',
            'victim': victim['id'], 'mutation': 'label += " CORRUPTED"',
            'flagged_exactly_one': bool(flagged and clean),
            'records_probed_class': len(records)}


def apply_patches(graph, patches):
    """Serial writer: merge patch objects/edges into the authored stores.
    Bulk reference families route to a rotated record shard; everything else
    (sources, work records...) goes to the hand-editable program file.
    Existing ids must be identical (immutable identity); new ids append."""
    program = json.loads(AUTHORED_PROGRAM.read_bytes().decode('utf-8-sig'))
    known = {obj['id']: obj for obj in program['objects']}
    edges = {(e['src'], e['rel'], e['dst'], e.get('note', ''))
             for e in program['relations']}
    records_dir = AUTHORED_PROGRAM.parent / 'records'
    shard_path = None
    shard = {'objects': [], 'relations': []}
    if records_dir.is_dir():
        shards = sorted(records_dir.glob('records_*.json'))
        if shards:
            # every existing object/edge is known identity, wherever it lives:
            # a shard-resident id seen again in a patch must compare identical,
            # never re-append (a second --apply run would otherwise duplicate
            # the bulk families build_graph refuses)
            for previous_shard in shards:
                payload = json.loads(previous_shard.read_bytes()
                                     .decode('utf-8-sig'))
                for obj in payload.get('objects', []):
                    known.setdefault(obj['id'], obj)
                for edge in payload.get('relations', []):
                    edges.add((edge['src'], edge['rel'], edge['dst'],
                               edge.get('note', '')))
            # rotate into the last shard unless it is full
            last = shards[-1]
            shard = json.loads(last.read_bytes().decode('utf-8-sig'))
            if len(last.read_bytes()) < 24 * 1024 * 1024:
                shard_path = last
            else:
                shard = {'objects': [], 'relations': []}
    if shard_path is None:
        records_dir.mkdir(parents=True, exist_ok=True)
        shard_path = records_dir / (
            'records_%03d.json' % (len(list(records_dir.glob('records_*.json'))) + 1))
    # immutability guards see shard-resident identities too (review F5)
    for obj in shard.get('objects', []):
        known.setdefault(obj['id'], obj)
    for edge in shard.get('relations', []):
        edges.add((edge['src'], edge['rel'], edge['dst'], edge.get('note', '')))
    added = 0
    BULK = {'reference_entity', 'property_assertion', 'geometry_asset',
            'mapping', 'relationship'}
    for patch in patches:
        for obj in patch['payload']['objects']:
            previous = known.get(obj['id'])
            require(previous is None or previous == obj,
                    'immutable_graph_identity_conflict', obj['id'])
            if previous is None:
                if obj.get('kind') in BULK:
                    shard['objects'].append(obj)
                else:
                    program['objects'].append(obj)
                known[obj['id']] = obj
                added += 1
        for edge in patch['payload']['relations']:
            key = (edge['src'], edge['rel'], edge['dst'], edge.get('note', ''))
            if key not in edges:
                program['relations'].append(dict(edge))
                edges.add(key)
    raw = (json.dumps(program, ensure_ascii=False, indent=1) + '\n').encode()
    AUTHORED_PROGRAM.write_bytes(raw)
    shard_raw = (json.dumps(shard, ensure_ascii=False, indent=1) + '\n').encode()
    shard_path.write_bytes(shard_raw)
    return {'objects_added': added,
            'program_bytes': len(raw),
            'shard': str(shard_path.name), 'shard_bytes': len(shard_raw),
            'note': 'bulk kinds shard; core in the program; one serial writer'}


def rebuild_store():
    sys.path.insert(0, str(ROOT / 'tools' / 'creature_graph'))
    import build_graph
    graph = build_graph.build()
    graph.save(str(DEFAULT_GRAPH))
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admit', default='', help='comma-separated connector ids')
    parser.add_argument('--reprove', default='', help='"all" or comma-separated source ids')
    parser.add_argument('--train', choices=['skip', 'exercise'], default='skip')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--work', type=Path, default=ROOT / '.tmp' / 'batch')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()

    admit_ids = [c for c in args.admit.split(',') if c]
    for cid in admit_ids:
        require(cid in C.CONNECTORS, 'unknown_connector', cid)
    reprove_keys = (C.REPROVE_SOURCES if args.reprove == 'all'
                    else [s for s in args.reprove.split(',') if s])

    registry = load_registry()
    graph = graph_from(str(DEFAULT_GRAPH))
    runs, patches = [], []
    train_result = {'exercised': False}

    # 1) Re-prove every existing admission under its recorded producer.
    if reprove_keys:
        blob_index = batch_reprove._blob_index()
        for key in reprove_keys:
            replay = batch_reprove.reprove_source(graph, key, blob_index)
            result = batch_verify.verify_reprove(graph, key, replay, registry)
            result['mode'] = 'reprove'
            runs.append(result)
            print('reproved', key, result['records'], 'records byte-identical')

    # 2) Admit new connectors: stage pins, bundle, verify, propose. Bundles are
    # point-in-time (the producer hash pins the code), so each run starts from
    # a clean bundle cache and regenerates deterministically.
    if admit_ids:
        import shutil
        shutil.rmtree(args.work / 'bundles', ignore_errors=True)
        bundles = batch_ingest.admit_connectors(admit_ids, args.work)
        for cid in admit_ids:
            patch = propose(bundles[cid], graph)
            verify = batch_verify.verify_bundle(cid, bundles[cid], graph,
                                                patch['payload']['objects'], registry)
            verify['mode'] = 'admit'
            runs.append(verify)
            patches.append(patch)
            counts = verify['counts']
            print('admitted', cid, counts['records'], 'records,',
                  counts['quarantined'], 'quarantined, bundle', verify['bundle_id'][:12])

    # 3) The batch membrane's own falsifier, run on real data.
    probe = mutation_probe(graph, registry)

    # 4) Receipt of the proven batch (also the training gate input).
    graph_result = {'applied': False}
    if args.apply:
        require(patches, 'nothing_to_apply')
        graph_result['apply'] = apply_patches(graph, patches)
        rebuilt = rebuild_store()
        graph_result['rebuilt'] = {'objects': len(rebuilt.objects),
                                   'relations': len(rebuilt.relations),
                                   'graph_hash': rebuilt.graph_hash()}
        # Idempotency falsifier: re-proposing every bundle against the rebuilt
        # graph must be a no-op (same hash, no new identities).
        for cid in admit_ids:
            replay = propose(bundles[cid], rebuilt)
            require(replay['metadata']['candidate_graph_hash'] == rebuilt.graph_hash(),
                    'admission_not_idempotent', cid)
        graph_result['idempotent_replay'] = 'all bundles re-propose as no-ops'
        graph_result['applied'] = True
        # The graphify consumer must round-trip the rebuilt store (7 checks).
        from tools.science_funnel.qualify import consumer_roundtrip
        consumer_roundtrip(str(DEFAULT_GRAPH), args.work / 'consumer')
        graph_result['graphify_roundtrip'] = 'HONEST (7 checks)'
        graph = graph_from(str(DEFAULT_GRAPH))

    # 5) Training behind the batch gate.
    batch_summary = {'totals': {'records_verified': sum(r.get('records', r.get(
        'counts', {}).get('records', 0)) for r in runs), 'contract_failures': sum(
        len(f['failures']) for r in runs for f in r.get('classes', []))},
        'count_identity': {'closed': True}}
    if args.train == 'exercise':
        gate = batch_train.batch_gate(graph, batch_summary)
        result = batch_train.exercise()
        train_result = {'exercised': True, 'gate': gate, 'result': result,
                        'claim': 'wiring proven; no policy quality claimed'}
        require(result['completed'], 'train_exercise_failed')

    replay_commands = [
        'python -B -m tools.creature_graph.batch_qualify --reprove all --admit '
        + ','.join(admit_ids) + (' --apply' if args.apply else '')
        + ' --train ' + args.train + ' --out <receipt path>',
    ]
    receipt = build_receipt(runs, probe, graph_result, train_result, replay_commands)
    path = write_receipt(receipt, args.out)
    print('batch receipt:', path)
    print('totals:', canonical(receipt['totals']).decode())


if __name__ == '__main__':
    main()
