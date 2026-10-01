"""Read-only delivery priorities and honest stage/efficiency accounting."""
import argparse
import json
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def priorities():
    tasks = {t['id']: t for t in json.loads((HERE/'monkey_completion_map.json').read_text(encoding='utf-8'))['tasks']}
    result = {}
    def include(tid, stage):
        if tid in result: return
        result[tid] = stage
        for dep in tasks[tid]['depends_on']: include(dep, stage)
    # Dependency closure gives upstream work the same priority; actual dependency
    # admission stays exclusively with the existing ontology scheduler.
    for stage, goals in enumerate((['W10', 'U02', 'U03', 'X02'], ['F06', 'F08'], ['X07'])):
        for tid in goals: include(tid, stage)
    return result


def priority(spec):
    return min((priorities().get(i, 99) for i in spec.get('planning_ids', [])), default=99)


def report(board):
    rows = []
    first_pass = 0; reviewed = 0; duplicate = 0
    for c in board['cards'].values():
        reviews = c.get('worker_reviews', [])
        completed = [r for r in reviews if r['state'] == 'COMPLETE']
        if completed:
            reviewed += 1; first_pass += completed[0].get('verdict') == 'PASS'
        groups = {}
        for r in reviews:
            if r['state'] in ('WORKING', 'COMPLETE'):
                key = (r['pr_url'], r['head_sha'], r['criteria_sha256'])
                groups[key] = groups.get(key, 0) + 1
        duplicate += sum(max(0, n-1) for n in groups.values())
        winner = c.get('winner') or {}
        rows.append(dict(task_id=c['id'], priority=priority(c['spec']),
                         implementation=c['state'], candidate_merged=bool(winner),
                         qualification_recorded=bool(winner.get('ontology_qualification')),
                         integration='NOT_ESTABLISHED_BY_CARD_MERGE',
                         pr_url=winner.get('pr_url'),
                         correction_count=sum(r.get('verdict') == 'CHANGES_REQUIRED'
                                              for r in c.get('review_history', []))))
    return dict(schema='chimera.delivery_progress.v1', tasks=rows,
                metrics=dict(first_review_pass_rate=first_pass/reviewed if reviewed else None,
                             reviewed_cards=reviewed, excess_review_records=duplicate,
                             agent_hours_per_integrated_feature=None,
                             implementation_to_integration_seconds=None,
                             demonstrated_player_actions=None),
                limitations='Missing timing/runtime evidence is null, not zero. Review records are not live workers. '
                            'First-review PASS is a recommendation, not final acceptance. Excess records include '
                            'authorized additional reviews. Merged contribution is not runtime integration.')


def main():
    from agent_slots import Registry, DEFAULT_ROOT
    p = argparse.ArgumentParser(); p.add_argument('--registry', type=Path, default=DEFAULT_ROOT)
    args = p.parse_args()
    print(json.dumps(report(Registry(args.registry).readonly()['kanban']), indent=2))


if __name__ == '__main__': main()
