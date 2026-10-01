"""python -m tools.science_funnel --help"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import sys
from .common import VERSION, Refusal, canonical, local_file, loads, require, sha
from .graph import graph_from, propose, reduction_proposal
from .pipeline import ingest, verify
from .reductions import reduce

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GRAPH = ROOT / 'tools/creature_graph/data/creature_graph.json'


def write_new(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as stream:
            stream.write(raw)
    except FileExistsError:
        require(path.read_bytes() == raw, 'output_exists_with_different_bytes', path)


def prepare_pinned(cache, output):
    """Reuse prior fetch pins and cached bytes. Never fetch, refresh or guess a pin."""
    registry = loads((ROOT / 'tools/reference_data/data/import_provenance.json').read_bytes())['sources']
    adapters = {'uberon.appendicular-minimal': 'uberon_obo', 'ro.base': 'ro_owl',
                'qudt.units': 'qudt_ttl', 'opensim.leg6dof9musc': 'opensim_xml'}
    prepared = []
    # Preflight ALL pinned source bytes before publishing any manifests.
    jobs = []
    for sid, adapter in adapters.items():
        source = registry[sid]
        artifacts, payloads = [], {}
        for relative, entry in sorted(source['artifacts'].items()):
            raw = local_file(cache, relative).read_bytes()
            require(sha(raw) == entry['sha256'], 'pin_drift', relative)
            destination = 'artifacts/' + entry['sha256']
            artifacts.append({'id': relative, 'path': destination,
                              'sha256': entry['sha256'], 'url': entry['url']})
            payloads[destination] = raw
        manifest = {'schema_version': VERSION, 'adapter': adapter,
                    'source': {'id': sid, 'release': source['release'],
                               'url': source['entry_url'], 'license': source['license'],
                               'license_evidence': source.get('license_evidence'),
                               'known_gaps': source.get('known_gaps')}, 'artifacts': artifacts}
        if sid.startswith('opensim.'):
            manifest['conditions'] = {'species': 'human', 'side': 'right',
                                      'measurement_kind': 'source_model_parameter'}
        jobs.append((sid, manifest, payloads))
    for sid, manifest, payloads in jobs:
        folder = Path(output) / sid
        for relative, raw in payloads.items():
            write_new(folder / relative, raw)
        path = folder / 'manifest.json'
        write_new(path, canonical(manifest))
        prepared.append(str(path.resolve()))
    return {'manifests': prepared, 'pins': 'reused_original_hashes', 'downloads': 0}


def main(argv=None):
    ap = argparse.ArgumentParser(description='Deterministic scientific intake and graph proposals')
    sub = ap.add_subparsers(dest='command', required=True)
    catalog = sub.add_parser('catalog', help='Read database families and connector gaps from the graph')
    catalog.add_argument('--graph', type=Path, default=DEFAULT_GRAPH)
    prepare = sub.add_parser('prepare-pinned', help='Package existing four source caches with ORIGINAL pins')
    prepare.add_argument('--cache', required=True, type=Path)
    prepare.add_argument('--output', required=True, type=Path)
    intake = sub.add_parser('ingest', help='Import one or more manifests in independent parallel lanes')
    intake.add_argument('--manifest', action='append', required=True, type=Path)
    intake.add_argument('--output', required=True, type=Path)
    check = sub.add_parser('verify', help='Check byte hashes AND reproduce adapter outputs')
    check.add_argument('bundle', type=Path)
    prop = sub.add_parser('propose', help='Produce a CAS graph_apply payload; does NOT mutate a graph')
    prop.add_argument('bundle', type=Path)
    prop.add_argument('--graph', type=Path, default=DEFAULT_GRAPH)
    prop.add_argument('--output', required=True, type=Path)
    prop.add_argument('--allow-partial', action='store_true')
    reduction = sub.add_parser('reduce', help='Derive a candidate from admitted scalar/geometry records')
    reduction.add_argument('--bundle', action='append', required=True, type=Path)
    reduction.add_argument('--request', required=True, type=Path)
    reduction.add_argument('--graph', type=Path)
    reduction.add_argument('--output', required=True, type=Path)
    args = ap.parse_args(argv)
    try:
        if args.command == 'catalog':
            result = graph_from(args.graph).get('model.scientific_intake')['funnel_catalog']
        elif args.command == 'prepare-pinned':
            result = prepare_pinned(args.cache, args.output)
        elif args.command == 'ingest':
            def run(path):
                try:
                    bundle = ingest(path, args.output)
                    receipt = verify(bundle)['receipt']
                    return {'manifest': str(path), 'bundle': str(bundle),
                            'accepted': receipt['accepted'], 'quarantined': receipt['quarantined']}
                except (Refusal, OSError) as exc:
                    return {'manifest': str(path), 'error': str(exc)}
            with ThreadPoolExecutor(max_workers=min(8, len(args.manifest))) as pool:
                result = list(pool.map(run, args.manifest))
            print(json.dumps(result, indent=2))
            return 2 if any(r.get('error') or r.get('quarantined') for r in result) else 0
        elif args.command == 'verify':
            result = verify(args.bundle)['receipt']
        elif args.command == 'propose':
            data = verify(args.bundle)
            require(args.allow_partial or not data['quarantine'], 'partial_intake_requires_explicit_choice')
            result = propose(args.bundle, graph_from(args.graph))
            result['metadata']['allow_partial'] = args.allow_partial
            write_new(args.output, canonical(result))
            result = {'proposal': str(args.output), 'objects': len(result['payload']['objects']),
                      'relations': len(result['payload']['relations']), 'graph_mutated': False}
        else:
            records = {}
            for bundle in args.bundle:
                for rec in verify(bundle)['records']:
                    require(rec['id'] not in records or records[rec['id']] == rec, 'record_identity_conflict')
                    records[rec['id']] = rec
            result = reduce(loads(args.request.read_bytes()), records)
            if args.graph:
                result = reduction_proposal(result, graph_from(args.graph))
            write_new(args.output, canonical(result))
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (Refusal, OSError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
