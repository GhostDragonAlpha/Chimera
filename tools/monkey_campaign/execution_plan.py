"""Read-only commissioning packets derived from the sealed completion catalog.

Packets explain the next phases; they neither allocate ownership nor assert that
historical UNRECONCILED items are missing. Live receipts remain authoritative.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from campaign import require, selected_tasks, validate_catalog
from integrity import content_digest, verify_catalog

HERE = Path(__file__).resolve().parent


def build_plan(catalog):
    """Return complete, deterministic packets without changing catalog or state."""
    by = validate_catalog(catalog)
    calculations = catalog.get('calculations')
    require(isinstance(calculations, list), 'missing_calculations')
    calc_by = {}
    for calculation in calculations:
        require(isinstance(calculation, dict), 'invalid_calculation')
        cid = calculation.get('id')
        require(isinstance(cid, str) and cid and cid not in calc_by,
                'invalid_or_duplicate_calculation_id')
        for field in ('title', 'required_inputs', 'calculation_or_contract', 'output', 'verification'):
            require(isinstance(calculation.get(field), str) and calculation[field].strip(),
                    'missing_calculation_' + field + ':' + cid)
        calc_by[cid] = calculation
    selected = selected_tasks(by)
    ontology = None
    if 'ontology_contract' in catalog:
        from ontology_plan import project
        ontology = project(catalog)
    ontology_tasks = {t['id']: t for t in ontology['tasks']} if ontology else {}
    packets = []
    for tid in sorted(by):
        source = by[tid]
        ids = source.get('calculation_ids')
        require(isinstance(ids, list) and all(isinstance(cid, str) for cid in ids),
                'invalid_calculation_ids:' + tid)
        require(len(ids) == len(set(ids)), 'duplicate_task_calculation:' + tid)
        require(all(cid in calc_by for cid in ids), 'unknown_calculation:' + tid)
        require(isinstance(source.get('kind'), str) and bool(source['kind']), 'missing_kind:' + tid)
        require(isinstance(source.get('catalog_refs'), list), 'missing_catalog_refs:' + tid)
        packet = deepcopy(source)
        decision = 'decision' in source['kind'].split('+')
        packet.update({
            'selected': tid in selected,
            'initial_state': 'NEEDS_RECONCILIATION' if tid in selected else 'CONDITIONAL_INACTIVE',
            'assignment_authorized': False,
            'source_edit_authorized': False,
            'calculation_contracts': [deepcopy(calc_by[cid]) for cid in ids],
            'source_references': {
                'catalog_task': 'tools/monkey_campaign/monkey_completion_map.json#tasks/' + tid,
                'catalog_refs': deepcopy(source['catalog_refs']),
                'source_classes': deepcopy(catalog.get('source_classes', {})),
                'current_directive': 'docs/MONKEY_RUN.md',
                'live_board': 'E:/ChimeraWork/monkey-play-20260924/tools/monkey_campaign/PLAY_BOARD.md',
                'live_bindings': 'E:/ChimeraWork/monkey-play-20260924/tools/monkey_campaign/bindings.json',
            },
            'commissioning_requirements': [
                'Reconcile current code, existing owner and receipts before creating work; reuse valid evidence.',
                'Use an active Kanban card, pinned revision, isolated attempt write paths and resource admission; no timer or exclusive task lease.',
                'Freeze statement, prediction and falsifier before implementation or experiment; derive before training.',
                'Commission only the first unmet phase. If a decision is missing, submit alternatives with evidence to the lead and continue another eligible task.',
            ],
            'phases': [
                {'id': 'reconcile', 'action': 'Read the live board and receipts for ' + tid +
                 '; map every clause of done_when to a current revision and evidence. Recover an existing claim instead of duplicating it.',
                 'deliverable': 'Clause-to-evidence map, current owner, first unmet clause and dependency verdicts.'},
                {'id': 'decide', 'required': decision,
                 'action': ('Find the recorded lead/operator ruling for this exact decision. If absent, provide the smallest evidence-backed alternatives; do not choose policy, geometry, thresholds or physical parameters by default.'
                            if decision else 'Reuse applicable recorded decisions; escalate only a genuinely missing decision.'),
                 'deliverable': 'Existing decision reference or a bounded unresolved decision request.'},
                {'id': 'implement', 'action': 'After commissioning, satisfy only the unmet clauses of: ' + source['done_when'],
                 'calculation_ids': deepcopy(ids),
                 'deliverable': 'Scoped code, derivation, measurement, or decision artifact appropriate to kind=' + source['kind'] + '; preserve all existing valid work.'},
                {'id': 'verify', 'action': 'Execute the frozen falsifier and relevant regressions; independently check each attached calculation contract using its required inputs and verification method.',
                 'deliverable': 'Exact commands, source/artifact identities, observed results, failures and limits; fixture results labeled as fixtures.'},
                {'id': 'runtime', 'action': 'For runtime-facing clauses, exercise the pinned native build and actual monkey/scene. For static-only clauses, record the justified applicability boundary without claiming runtime acceptance.',
                 'depends_on_for_final_acceptance': deepcopy(source['depends_on']),
                 'deliverable': 'Actual-run evidence for applicable clauses; resource-blocked phases remain pending, never passed by a fixture.'},
                {'id': 'visual', 'action': 'For visible player behavior, capture and inspect the actual run tied to its inputs and revision. For nonvisual clauses, record why visual verification does not apply. Human acceptance requires the actual operator receipt.',
                 'deliverable': 'Observed visual verdict and capture reference, or reviewed applicability explanation; no invented viewer or human approval.'},
                {'id': 'review', 'action': 'A non-author checks the changed artifact and evidence against every original done_when clause and calculation contract, including dependency acceptance.',
                 'deliverable': 'Named independent review receipt with unresolved findings preserved.'},
                {'id': 'integrate', 'action': 'Through the existing publisher/integration path, land only owned reviewed changes, recheck affected behavior, checkpoint the result and release owned resources. Then take the next eligible task.',
                 'deliverable': 'Integrated revision, clause-complete receipt, preserved recovery reference and confirmed slot handoff; unfinished clauses stay open.'},
            ],
        })
        if ontology:
            binding = ontology_tasks[tid]
            packet['dependency_layer'] = binding['dependency_layer']
            packet['verification_profile'] = binding['verification_profile']
            packet['visual_context_required'] = binding['verification_profile']['kind'] != 'offline'
            packet['integration_checkpoints'] = [c for c in ontology['checkpoints'] if tid in c['task_ids']]
            packet['phases'][5]['profile'] = binding['verification_profile']
            packet['phases'][5]['action'] += ' Follow this task profile; record numeric camera values, required views and matched debug/clean state in the camera manifest. Integration checkpoints are downstream milestones, not prerequisites for their constituent tasks.'
        packets.append(packet)
    return {
        'schema': 'chimera.execution_plan.v1',
        'scope_sha256': content_digest(catalog),
        'goal': catalog.get('finish_line'),
        'task_count': len(packets),
        'selected_count': len(selected),
        'conditional_policy': 'Inactive unless explicitly selected by the authorized lead; default selection preserves dependency closure.',
        'acceptance_policy': catalog.get('feature_complete_policy'),
        'dependency_policy': catalog.get('dependency_policy'),
        'assignment_authorized': False,
        'goal_complete': False,
        'tasks': packets,
        'ontology_plan': {k: v for k, v in ontology.items() if k != 'tasks'} if ontology else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=HERE / 'monkey_completion_map.json')
    parser.add_argument('--lock', type=Path, default=HERE / 'APPROVED_SCOPE.json')
    parser.add_argument('--expected-scope', required=True, help='Externally pinned approved scope digest')
    parser.add_argument('--task', help='Emit one commissioning packet by catalog ID')
    args = parser.parse_args()
    catalog, _ = verify_catalog(args.catalog, args.lock, args.expected_scope, require_anchor=True)
    plan = build_plan(catalog)
    if args.task:
        matches = [task for task in plan['tasks'] if task['id'] == args.task]
        if not matches:
            parser.error('unknown task: ' + args.task)
        plan = {'schema': 'chimera.execution_task_packet.v1',
                'scope_sha256': plan['scope_sha256'], 'goal': plan['goal'],
                'assignment_authorized': False, 'task': matches[0]}
    print(json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
