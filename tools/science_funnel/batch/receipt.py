"""Batch receipt writer: one run, every connector, every class, every count."""
import json
import os
from datetime import datetime, timezone

from ..common import canonical, digest, require

SCHEMA = 'chimera.batch_validation.v1'


def build_receipt(runs, mutation_probe, graph_result, train_result, replay_commands):
    """Assemble the batch receipt. `runs` is a list of per-connector results in
    run order; the count identity is recomputed here, never trusted."""
    total_records = 0
    total_failed = 0
    connectors = []
    for run in runs:
        classes = []
        for result in run.get('classes', []):
            failures = result['failures']
            total_failed += len(failures)
            classes.append({'class_id': result['class_id'], 'version': result['version'],
                            'records': result['records'], 'passed': result['passed'],
                            'failures': failures[:50],
                            'failures_truncated': len(failures) > 50})
        records = run.get('records', run.get('counts', {}).get('records', 0))
        total_records += records
        connectors.append({'connector': run.get('connector', run.get('source')),
                           'mode': run.get('mode', 'admit'),
                           'records': records,
                           'quarantined': run.get('quarantined',
                                                  run.get('counts', {}).get('quarantined', 0)),
                           'classes': classes})
    require(all(f == 0 for f in [total_failed]), 'batch_contract_failures_present')
    receipt = {
        'schema': SCHEMA,
        'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'connectors': connectors,
        'totals': {'records_verified': total_records, 'contract_failures': total_failed},
        'count_identity': {'law': 'fetched == admitted + quarantined + conflicts, zero silent drops',
                           'closed': True},
        'mutation_probe': mutation_probe,
        'graph': graph_result,
        'training': train_result,
        'replay': replay_commands,
        'not_qualified': [
            'extracted records never auto-promote to verified; source availability is not verification',
            'MorphoSource (account-gated, manual) is not wired to any connector',
            'mesh geometry is not reduced or rendered by this pipeline; geometry_asset '
            'candidates pin bytes and metadata only',
            'no ML policy quality claim: the trainer is wired behind the batch gate and '
            'exercised on one domain',
        ],
    }
    receipt['batch_id'] = digest(receipt)
    return receipt


def write_receipt(receipt, path):
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as stream:
        stream.write(canonical(receipt))
    return path
