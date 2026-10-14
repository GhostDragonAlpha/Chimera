"""Stopped-fleet scope replacement. Archives evidence; never inherits qualification."""
from copy import deepcopy
from agent_slots import require
from kanban import digest, refill, validate_specs
from ontology_queue import generate


def migrate(state, projection, *, actor, workers_stopped, expected_revision, archive_reference):
    require(actor == 'astra-codex', 'lead_action_required')
    require(workers_stopped is True, 'operator_stopped_fleet_required')
    require(state['revision'] == expected_revision, 'migration_state_changed')
    require(archive_reference, 'durable_backup_required')
    old = state['kanban']
    prior = old['ontology_scheduler']['scope_sha256']
    target = projection['scope_sha256']
    require(prior != target, 'scope_already_installed')
    specs = generate(projection)
    validate_specs(specs)
    require(not (set(old['cards']) & {s['id'] for s in specs}), 'new_namespace_required')
    require(prior not in state.get('scope_archives', {}), 'scope_archive_exists')
    # The complete former board, including pending PRs, findings and attempts,
    # remains retrievable. No worker artifacts or GitHub branches are deleted.
    state.setdefault('scope_archives', {})[prior] = dict(
        board=deepcopy(old), slots=deepcopy(state['slots']),
        diagnostic_claims=deepcopy(state.get('diagnostic_claims', {})),
        coordinator_report=deepcopy(state.get('coordinator_report')),
        instruction_ack=deepcopy(state.get('instruction_ack')),
        reconciliation=deepcopy(state.get('reconciliation')),
        backup_reference=archive_reference, board_sha256=digest(old),
        reason='Captain stopped all workers and authorized material-first scope migration')
    b = {k: deepcopy(v) for k, v in old.items() if k in (
        'schema', 'policy', 'branch_policy', 'continuous_cycle',
        'operational_takeover', 'separate_review_lane', 'merge_service')}
    b.update(cards={}, backlog=specs, operational_lead=None,
             operational_history=[], coordination_deferrals={},
             ontology_scheduler=dict(scope_sha256=target, policy='VERSIONED_QUALIFICATION_V2'),
             migration=dict(previous_scope=prior, current_scope=target,
                            archive_reference=archive_reference,
                            evidence_policy='Read archived receipts; no automatic qualification carry-forward'))
    b['migration']['prior_tasks'] = {
        t['id']: [dict(task_id=c['id'], criteria_sha256=c['criteria_sha256'],
                      state=c['state'], read_command='kanban_cli.py inbox --task '+c['id'])
                  for c in old['cards'].values() if t['id'] in c['spec'].get('planning_ids', [])]
        for t in projection['tasks']}
    # Migration does not claim that old workers checkpointed themselves.
    state['slots'] = [dict(slot=s['slot'], generation=s.get('generation', 0)+1,
                           agent_id=None, phase='unregistered',
                           operator_stop_reference=archive_reference) for s in state['slots']]
    state['diagnostic_claims'] = {}
    state['coordinator_report'] = None
    state['instruction_ack'] = None
    state['reconciliation'] = {'status':'OPERATOR_STOP_MIGRATED', 'archive_reference':archive_reference}
    state['mode'] = 'ACTIVE'
    state['kanban'] = b
    refill(b)
    for c in b['cards'].values():
        c['messages'].append(dict(id='material-scope-start', author='astra-codex', status='RESOLVED',
            body='Read MATERIAL_PLAN_ADOPTION.md. Prior evidence is archived and reusable after scoped verification. The Captain authorized this material-first plan; do not ask for a new goal. Recover the existing prototype before rebuilding. This is instruction, not a finding blocking acceptance.'))
    return {'previous_scope':prior, 'scope_sha256':target,
            'archived_cards':len(old['cards']), 'ready_cards':list(b['cards']),
            'new_task_count':len(specs)}


def historical_card(state, task_id):
    for scope, archive in state.get('scope_archives', {}).items():
        if task_id in archive['board']['cards']:
            return {'state':'HISTORICAL_SCOPE_READ_ONLY', 'scope_sha256':scope,
                    'card':deepcopy(archive['board']['cards'][task_id]),
                    'next_action':'Preserve evidence. Run canonical startup with your existing arrival ID for a current-scope task; never resume old writes.'}
    raise KeyError(task_id)
