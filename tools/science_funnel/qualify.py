"""Reproduce the intake -> serial controller -> Graphify qualification on scratch.

Run with a direct Python interpreter for fleet PID tests. If Graphify dependencies
live in a venv, pass that interpreter via --consumer-python. No native engine runs.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from .common import canonical, loads, require, sha
from .__main__ import ROOT, DEFAULT_GRAPH, prepare_pinned
from .pipeline import ingest, verify, implementation
from .graph import propose, graph_from, reduction_proposal
from .reductions import LAWS, reduce


def consumer_roundtrip(graph_path, out):
    from tools.creature_graph import graphify_consumer as consumer
    from tools.creature_graph.graphify_projection import make_projection
    graph = graph_from(graph_path)
    consumer.DEMO_DIR = str(out/'consumer')
    consumer.DEMO_DB = str(out/'consumer/graph.db')
    consumer.DEMO_SNAPSHOT = str(out/'consumer/snapshot.json')
    projection = make_projection(graph)
    consumer.validate_projection(projection, graph)
    gi, db = consumer.load_graphify()
    receipt = consumer.ingest_projection(gi, projection, graph)
    checks, passed = consumer.verify(graph, projection, gi, db, receipt)
    (out/'consumer_checks.json').write_bytes(canonical(checks))
    require(passed, 'consumer_roundtrip_failed')
    print(canonical({'checks': checks, 'passed': passed}).decode())


def qualify(cache, out, consumer_python, targeted=False):
    out.mkdir(parents=True, exist_ok=False)
    report = {'captured_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'offline intake and scratch graph admission; no product physics or live controller claim',
              'implementation': implementation(), 'suites': {}, 'imports': [], 'completed': False}
    try:
        commands = {
            'intake': ['-m', 'unittest', 'discover', '-s', 'tools/science_funnel/tests', '-v'],
            'fleet': ['-m', 'unittest', 'discover', '-s', 'tools/agent_fleet', '-p', 'test_*.py'],
            'graph': ['tools/creature_graph/tests/test_contracts.py'],
        }
        if targeted:
            del commands['fleet']
            commands['workflow'] = ['tools/agent_fleet/test_graph_workflow.py']
        for name, args in commands.items():
            result = subprocess.run([sys.executable, '-B', *args], cwd=ROOT,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
            (out/(name + '.txt')).write_bytes(result.stdout)
            report['suites'][name] = {'exit_code': result.returncode,
                                      'log_sha256': sha(result.stdout), 'argv': args}
            print(name, 'exit', result.returncode, flush=True)
            require(result.returncode == 0, 'qualification_suite_failed', name)
        prepared = prepare_pinned(cache, out/'inputs')
        sys.path.insert(0, str(ROOT/'tools/agent_fleet'))
        from graph_workflow import GraphWorkflowControl, unpack
        graph = graph_from(DEFAULT_GRAPH)
        before = dict(graph.objects)
        graph.save(str(out/'seed.json'))
        controller = GraphWorkflowControl(out/'control.sqlite', 'scratch-admin', 'scratch-enroll',
                                           out/'slots', graph_path=out/'seed.json')
        accepted = {}
        manifests = prepared['manifests'] + [str(p) for p in sorted((ROOT/'tools/science_funnel/examples').glob('*.manifest.json'))]
        for manifest in manifests:
            bundle = ingest(manifest, out/'bundles')
            data = verify(bundle)
            accepted[data['manifest']['source']['id']] = data['records']
            require(not data['quarantine'], 'pinned_source_quarantined', manifest)
            snap = controller.call('graph_snapshot', 'scratch-admin')['result']
            patch = propose(bundle, unpack(snap['graph']))
            admitted = controller.call('graph_apply', 'scratch-admin', **patch['payload'])['result']
            require(admitted['graph_hash'] == patch['metadata']['candidate_graph_hash'], 'admission_hash_mismatch')
            restored = controller.call('graph_snapshot', 'scratch-admin')['result']
            replay = propose(bundle, unpack(restored['graph']))
            reimport = controller.call('graph_apply', 'scratch-admin', **replay['payload'])['result']
            require(reimport['graph_hash'] == admitted['graph_hash'], 'reimport_not_idempotent')
            report['imports'].append({'source': data['manifest']['source']['id'],
                                      'bundle': str(bundle), 'receipt': data['receipt'],
                                      'graph_objects': len(patch['payload']['objects']),
                                      'graph_edges': len(patch['payload']['relations']),
                                      'reimport_after_storage': 'identical_graph_hash'})
            print(data['manifest']['source']['id'], len(data['records']), 'records admitted', flush=True)
        # End-to-end synthetic oracle: properties + two-point geometry -> k=100 N/m.
        # These fixture numbers are never presented as real tissue measurements.
        if 'fixture.materials' in accepted:
            all_records = {r['id']: r for rows in accepted.values() for r in rows}
            material = {r['external_id']: r['id'] for r in accepted['fixture.materials']}
            axis = accepted['fixture.geometry'][0]['id']
            request = {'law': 'axial_stiffness', 'target_id': 'model.interface.shaped_connection',
                       'inputs': {'E': {'record': material['E']}, 'A': {'record': material['A']},
                                  'L': {'record': axis, 'field': 'length_m'}},
                       'context': {'specimen': 'synthetic_fixture', 'frame': 'synthetic_fixture_frame'},
                       'assumptions': {k: 'synthetic ideal bar constructed for this fixture' for k in LAWS['axial_stiffness']['assumptions']},
                       'validation': {'observable': 'force / extension', 'falsifier': '1 N fails to correspond to 10 mm extension in the ideal bar',
                                      'acceptance_rule': 'independent analytic oracle: stiffness = 100 N/m'}}
            reduction = reduce(request, all_records)
            require(abs(reduction['result']['value_si'] - 100) < 1e-12, 'synthetic_bar_oracle_failed')
            snap = controller.call('graph_snapshot', 'scratch-admin')['result']
            patch = reduction_proposal(reduction, unpack(snap['graph']))
            controller.call('graph_apply', 'scratch-admin', **patch['payload'])
            report['synthetic_reduction'] = reduction
        final = unpack(controller.call('graph_snapshot', 'scratch-admin')['result']['graph'])
        require(all(final.get(k) == v for k, v in before.items()), 'existing_graph_object_changed')
        require(not final.check(), 'final_graph_invalid')
        final.save(str(out/'admitted_graph.json'))
        report['graph'] = {'objects': len(final.objects), 'relations': len(final.relations),
                           'hash': final.graph_hash(), 'existing_objects_unchanged': len(before)}
        command = [consumer_python, '-B', '-m', 'tools.science_funnel.qualify',
                   '--consumer-graph', str(out/'admitted_graph.json'), '--output', str(out)]
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=120)
        (out/'consumer.txt').write_bytes(result.stdout)
        report['suites']['consumer'] = {'exit_code': result.returncode,
                                        'log_sha256': sha(result.stdout)}
        require(result.returncode == 0, 'consumer_roundtrip_failed')
        report['consumer_checks'] = loads((out/'consumer_checks.json').read_bytes())
        report['completed'] = True
        return report
    finally:
        (out/'report.json').write_bytes(canonical(report))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--consumer-python', default=sys.executable)
    ap.add_argument('--consumer-graph', type=Path)
    ap.add_argument('--targeted', action='store_true',
                    help='Use workflow suite instead of the whole fleet after unaffected fleet checks already passed')
    args = ap.parse_args()
    if args.consumer_graph:
        consumer_roundtrip(args.consumer_graph, args.output.resolve())
    else:
        require(args.cache is not None, 'cache_required')
        result = qualify(args.cache, args.output.resolve(), args.consumer_python, args.targeted)
        print(canonical({'completed': result['completed'], 'report': str(args.output/'report.json')}).decode())


if __name__ == '__main__':
    main()
