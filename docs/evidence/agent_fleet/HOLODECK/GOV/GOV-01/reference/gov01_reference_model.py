"""GOV-01 INDEPENDENT REFERENCE MODEL — claim/CAS/persistence semantics.

Written for holodeck-gov-01 (catalogue card GOV-01) as planning-independent
reference text: a small, self-contained, stdlib-only model of the INTENDED
base contract of the Chimera fleet controller (tools/agent_fleet/control.py
at base d59518b9): canonical task ids, claims, owners, generations, and a
committed-registry persistence boundary.

It deliberately models the INTENDED contract, not the known live deviation:
claims bind owner_instance when an instance is presented (control.py:553-554),
and every owned mutation passes the owner+generation CAS gate (control.py:
116-124). The deployed interceptor deviation (review_handoff.py:90-91 drops
the owner_instance binding) is MEASURED in the evidence lane, not adopted.

No I/O except the explicit save()/load() file and no imports beyond stdlib.
This file is evidence: the negative-control runner imports it read-only.
"""


class Refusal(Exception):
    """A named refusal, mirroring the controller's require()/Refusal pair."""


def require(condition, reason):
    if not condition:
        raise Refusal(reason)


def overlaps(a, b):
    """Casefolded prefix-overlap of path scopes (control.py:51-53)."""
    a, b = a.casefold(), b.casefold()
    return a == b or a.startswith(b + '/') or b.startswith(a + '/')


class ReferenceModel:
    def __init__(self, max_tasks_default=2):
        self.agents = {}   # id -> {qualified, capabilities, max_tasks, instance}
        self.tasks = {}    # id -> {state, owner, generation, owner_instance,
        #                    scopes, capabilities, dependencies, kind, slot,
        #                    checkpoint, data}
        self.slots = {}    # no -> {task, kind}
        self.revision = 0
        self.max_tasks_default = max_tasks_default

    # ---- fixtures (test-registry setup; not part of the modeled contract) --

    def add_agent(self, aid, capabilities, max_tasks=2, qualified=True):
        self.agents[aid] = {'qualified': qualified, 'capabilities': set(capabilities),
                            'max_tasks': max_tasks, 'instance': None}
        return self.agents[aid]

    def add_task(self, tid, scopes, capabilities=('cpu',), dependencies=(),
                 state='READY', kind='worker'):
        self.tasks[tid] = {'state': state, 'owner': None, 'generation': 0,
                           'owner_instance': None, 'scopes': list(scopes),
                           'capabilities': set(capabilities),
                           'dependencies': list(dependencies), 'kind': kind,
                           'slot': None, 'checkpoint': None, 'data': {}}
        return self.tasks[tid]

    def add_slot(self, number, kind='worker'):
        self.slots[str(number)] = {'task': None, 'kind': kind}
        return self.slots[str(number)]

    # ---- modeled ops -------------------------------------------------------

    def claim(self, actor, task_id, instance=None):
        """Claim per the INTENDED base contract (control.py:520-555)."""
        agent = self.agents.get(actor)
        require(agent is not None and agent['qualified'], 'qualified_agent_required')
        task = self.tasks.get(task_id)
        require(task is not None and task['state'] == 'READY', 'task_not_ready')
        require(set(task['capabilities']) <= agent['capabilities'],
                'capability_missing')
        active = [t for t in self.tasks.values()
                  if t['owner'] == actor
                  and t['state'] in ('RUNNING', 'BLOCKED', 'REVIEW', 'RECOVERY_HOLD')]
        require(len(active) < agent['max_tasks'], 'agent_capacity_reached')
        require(all(self.tasks[d]['state'] == 'INTEGRATED'
                    for d in task['dependencies']), 'dependencies_not_integrated')
        for other in self.tasks.values():
            if other['state'] in ('RUNNING', 'BLOCKED', 'REVIEW', 'RECOVERY_HOLD'):
                require(not any(overlaps(x, y) for x in task['scopes']
                                for y in other['scopes']), 'write_scope_conflict')
        available = [n for n, s in self.slots.items()
                     if s['task'] is None and s['kind'] == task['kind']]
        require(bool(available), 'no_free_slot')
        number = available[0]
        self.slots[number]['task'] = task_id
        # CAS bind, control.py:553-554: five fields, including owner_instance.
        task.update(owner=actor, slot=number, state='RUNNING',
                    generation=task['generation'] + 1,
                    owner_instance=instance)
        self.revision += 1
        return dict(task)

    def mutate(self, actor, generation, task_id, payload=None, instance=None):
        """Owned mutation through the _task CAS gate (control.py:116-124)."""
        task = self.tasks.get(task_id)
        require(task is not None, 'unknown_task')
        require(task['owner'] == actor and task['generation'] == generation,
                'stale_or_foreign_claim')
        require(task['state'] in ('RUNNING', 'BLOCKED', 'REVIEW'),
                'task_not_owned_active')
        if task['owner_instance'] is not None:
            require(instance == task['owner_instance'], 'instance_not_bound')
        if payload is not None:
            task['data'] = dict(payload)
        task['checkpoint'] = 'mutated@%d' % (self.revision + 1)
        self.revision += 1
        return dict(task)

    def release_and_reclaim(self, old_owner, task_id, new_owner, new_instance=None):
        """Supervisor-path release to READY then a different owner claims.

        Generation is intentionally NOT reset by a release/re-claim cycle
        (control.py bumps generation monotonically), so the old owner's
        generation becomes stale against the newer claim.
        """
        task = self.tasks[task_id]
        require(task['owner'] == old_owner, 'stale_or_foreign_owner')
        number = task['slot']
        task.update(state='READY', owner=None, slot=None)
        if number is not None:
            self.slots[number]['task'] = None
        return self.claim(new_owner, task_id, new_instance)

    # ---- persistence boundary (control.py:65-66, 351: committed blob) ------

    def save(self, path):
        import json
        blob = {'revision': self.revision,
                'agents': {k: {**v, 'capabilities': sorted(v['capabilities'])}
                           for k, v in self.agents.items()},
                'tasks': {k: {**v, 'capabilities': sorted(v['capabilities'])}
                          for k, v in self.tasks.items()},
                'slots': dict(self.slots)}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(blob, f, sort_keys=True)

    @classmethod
    def load(cls, path, max_tasks_default=2):
        import json
        with open(path, encoding='utf-8') as f:
            blob = json.load(f)
        m = cls(max_tasks_default)
        m.revision = blob['revision']
        for aid, a in blob['agents'].items():
            m.agents[aid] = {**a, 'capabilities': set(a['capabilities'])}
        for tid, t in blob['tasks'].items():
            m.tasks[tid] = {**t, 'capabilities': set(t['capabilities'])}
        m.slots = dict(blob['slots'])
        return m
