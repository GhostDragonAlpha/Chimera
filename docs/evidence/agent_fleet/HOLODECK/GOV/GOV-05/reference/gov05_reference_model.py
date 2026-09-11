"""GOV-05 INDEPENDENT REFERENCE MODEL — crash recovery + serialized publication.

Written for holodeck-gov-05 (catalogue card GOV-05, "Recovery journal and
serialized integration procedure") as planning-independent reference text: a
small, self-contained, stdlib-only model of the INTENDED base contract of the
Chimera fleet controller (tools/agent_fleet/control.py and
tools/agent_fleet/publish.py at base 62b8e357): a recovery journal with an
atomic committed-blob persistence boundary, supervisor crash-recovery gates
(fail / recover / review_requeue), and the serialized integration procedure
(integration_request -> publish -> ack_integration).

Card mathematics realized here:
- event sourcing — every committed op appends its name + invocation arguments
  to an append-only journal (the deployed control.py:350 INSERT, seq =
  revision); `replay()` RE-EXECUTES the journal through the public gate chain
  from the empty registry, so "replay reconstructs accepted task state" is a
  real equivalence check against independently recomputed state, not a
  snapshot copy;
- content addressing — heads, commits and expected bases are 40-hex tokens
  compared by value at every identity gate;
- idempotence — publishing an already-published head reports
  `already_integrated` without a second push (publish.py:79-83) and a second
  ack is refused `integration_already_acknowledged` (control.py:718);
- the committed-blob persistence boundary — every mutating op builds its full
  next state in a STAGED copy that becomes visible only together with its
  journal event inside commit() (the model of the single SQLite transaction,
  control.py:308/350/351/356); arm_crash() + Crash models the process dying
  at the commit boundary (ROLLBACK, control.py:358-360): the staged state and
  its journal event are discarded together, so a kill mid-transaction can
  leave neither partial state nor a torn journal entry.

It deliberately models the INTENDED contract, not the known live deviation:
the deployed review-handoff interceptor's claim bind (review_handoff.py:90-91
at base) omits owner_instance; the intended control.py:553-554 bind carries
it. The deviation is MEASURED in the evidence lane (R8), not adopted here.

No I/O except the explicit save()/load() file and no imports beyond stdlib.
This file is evidence: the control runner imports it read-only.
"""


class Refusal(Exception):
    """A named refusal, mirroring the controller's require()/Refusal pair."""


class Crash(Exception):
    """The process died mid-transaction (between BEGIN IMMEDIATE and COMMIT,
    control.py:308/356). Raised by commit() when a crash was armed, AFTER the
    staged state and its journal event were discarded — the only externally
    observable consequence of the kill."""


def require(condition, reason, detail=''):
    if not condition:
        raise Refusal(reason if not detail else '%s (%s)' % (reason, detail))


def is_sha(value):
    return isinstance(value, str) and len(value) == 40 and all(
        c in '0123456789abcdef' for c in value)


def overlaps(a, b):
    """Casefolded prefix-overlap of path scopes (control.py:51-53)."""
    a, b = a.casefold(), b.casefold()
    return a == b or a.startswith(b + '/') or b.startswith(a + '/')


class Remote:
    """Minimal stand-in for the git remote: content-addressed linear history,
    branch refs, and a push counter (the duplicate-publication witness)."""

    def __init__(self):
        self.refs = {}        # branch -> sha
        self.parents = {}     # sha -> parent sha
        self.push_count = 0   # incremented ONLY by an actual push

    def add_commit(self, sha, parent=None):
        self.parents[sha] = parent
        return sha

    def set_ref(self, branch, sha):
        self.refs[branch] = sha

    def is_ancestor(self, ancestor, descendant):
        """git merge-base --is-ancestor semantics on linear history; true
        also when the two refs are equal (a ref is its own ancestor)."""
        if ancestor == descendant:
            return True
        cur = self.parents.get(descendant)
        seen = set()
        while cur is not None and cur not in seen:
            if cur == ancestor:
                return True
            seen.add(cur)
            cur = self.parents.get(cur)
        return False

    def base_is_merge_base_of(self, base_sha, head_sha):
        """publish.py:99-102 `merge-base(base, head) == base` on linear
        history: true iff base is an ancestor of head (or equal)."""
        return self.is_ancestor(base_sha, head_sha)


REGISTRY_FIELDS = ('agents', 'tasks', 'slots', 'requests', 'resources',
                   'leader', 'epoch', 'revision', 'journal')


class ReferenceModel:
    def __init__(self, base_branch='astra/gait-capture', forbidden='master',
                 remote=None):
        self.agents = {}     # id -> {qualified, capabilities, max_tasks, alive}
        self.tasks = {}      # id -> task dict
        self.slots = {}      # no -> {task, kind, engine{...}}
        self.requests = {}   # rid -> integration request
        self.resources = {}  # name -> {'task': id} (held resources)
        self.leader = None
        self.epoch = 0
        self.revision = 0
        self.journal = []    # append-only: [{'seq', 'kind', 'args'}]
        self.base_branch = base_branch
        self.forbidden = forbidden
        self.remote = remote if remote is not None else Remote()
        self._staged = None  # the in-flight transaction (None = quiescent)
        self._crash_armed = False  # kill armed for the next commit boundary

    # ---- fixtures (test-registry setup; not part of the modeled contract) --

    def add_agent(self, aid, capabilities, max_tasks=2, alive=True):
        self.agents[aid] = {'qualified': True, 'capabilities': set(capabilities),
                            'max_tasks': max_tasks, 'alive': alive}
        return self.agents[aid]

    def add_task(self, tid, scopes, capabilities=('cpu',), dependencies=(),
                 state='READY', kind='worker', base=None):
        self.tasks[tid] = {'state': state, 'owner': None, 'generation': 0,
                           'owner_instance': None, 'scopes': list(scopes),
                           'capabilities': set(capabilities),
                           'dependencies': list(dependencies), 'kind': kind,
                           'slot': None, 'checkpoint': None, 'head': None,
                           'branch': 'astra/tasks/' + tid,
                           'base': base, 'integration': None,
                           'review_slot_handoffs': []}
        return self.tasks[tid]

    def add_slot(self, number, kind='worker'):
        self.slots[str(number)] = {'task': None, 'kind': kind, 'engine': {}}
        return self.slots[str(number)]

    # ---- transaction boundary (control.py:305-361) -------------------------

    def _stage(self):
        """BEGIN: every mutating op works on a deep copy; the live registry is
        untouched until commit(). A refused op simply never commits (the next
        op re-stages), which is the model of ROLLBACK leaving no trace."""
        import copy
        self._staged = copy.deepcopy({f: getattr(self, f) for f in REGISTRY_FIELDS})
        return self._staged

    def commit(self, kind, args):
        """The atomic boundary: ONE journal event with seq=revision+1 becomes
        visible together with the whole staged state (the model of the event
        INSERT at control.py:350 and the state UPDATE at 351 sharing one
        transaction; COMMIT at 356). With a crash armed, the process dies
        HERE instead: the staged state and its not-yet-appended journal event
        are discarded together and Crash is raised — nothing partial ever
        becomes visible (the model of ROLLBACK at control.py:358-360 and of
        SQLite's atomicity under process death)."""
        staged = self._staged
        if self._crash_armed:
            self._crash_armed = False
            self._staged = None
            raise Crash('process_died_mid_transaction')
        new_rev = staged['revision'] + 1
        staged['revision'] = new_rev
        staged['journal'] = staged['journal'] + [
            {'seq': new_rev, 'kind': kind, 'args': args}]
        for f in REGISTRY_FIELDS:
            setattr(self, f, staged[f])
        self._staged = None

    def arm_crash(self):
        """Arm a kill for the NEXT commit boundary (the test harness's way of
        interrupting between BEGIN IMMEDIATE and COMMIT)."""
        self._crash_armed = True

    # ---- persistence boundary (committed blob; control.py:65-76) -----------

    def snapshot(self):
        """The committed state, as a comparable plain dict."""
        import copy
        return {f: copy.deepcopy(getattr(self, f)) for f in REGISTRY_FIELDS}

    def save(self, path):
        import json
        blob = {f: self._jsonable(getattr(self, f)) for f in REGISTRY_FIELDS}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(blob, f, sort_keys=True)

    @classmethod
    def load(cls, path, remote=None, **kw):
        """The deployed restart: the committed blob is authoritative
        (control.py:69-76), identity-checked by the caller."""
        import json
        with open(path, encoding='utf-8') as f:
            blob = json.load(f)
        m = cls(remote=remote, **kw)
        for f in REGISTRY_FIELDS:
            setattr(m, f, cls._from_json(blob[f]))
        return m

    @staticmethod
    def _jsonable(v):
        import copy
        v = copy.deepcopy(v)
        if isinstance(v, dict):
            if 'capabilities' in v and isinstance(v['capabilities'], set):
                v = dict(v, capabilities=sorted(v['capabilities']))
            return {k: ReferenceModel._jsonable(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [ReferenceModel._jsonable(x) for x in v]
        return v

    @classmethod
    def _from_json(cls, v):
        if isinstance(v, dict):
            if 'capabilities' in v and isinstance(v['capabilities'], list):
                v = dict(v, capabilities=set(v['capabilities']))
            return {k: cls._from_json(x) for k, x in v.items()}
        if isinstance(v, list):
            return [cls._from_json(x) for x in v]
        return v

    # ---- replay (card mathematics: event sourcing) -------------------------
    # The journal stores op + invocation arguments; replay re-EXECUTES each
    # event through the same public gate chain on a fresh registry sharing the
    # same content-addressed remote (a re-push of a published head is
    # detected as already_integrated — the deployed idempotence — so replay
    # never double-pushes). R6 compares the reconstructed registry with the
    # committed registry field by field.

    def replay(self, journal, baseline):
        """Re-execute the journal through the public gate chain. The fresh
        registry restarts from `baseline` — the captured fixture state taken
        BEFORE the first journaled op (add_agent/add_task/add_slot are
        test-registry setup, not contract ops) — and shares this model's
        content-addressed remote (a re-push of a published head is detected
        as already_integrated — the deployed idempotence — so replay never
        double-pushes). R6 compares the reconstructed registry with the
        committed registry field by field."""
        import copy
        fresh = ReferenceModel(base_branch=self.base_branch,
                               forbidden=self.forbidden, remote=self.remote)
        for f in REGISTRY_FIELDS:
            setattr(fresh, f, copy.deepcopy(baseline[f]))
        for event in journal:
            kind, args = event['kind'], dict(event['args'])
            if kind == 'claim':
                fresh.claim(args['actor'], args['task'], instance=args.get('instance'))
            elif kind == 'checkpoint':
                fresh.mutate(args['actor'], args['generation'], args['task'],
                             instance=args.get('instance'))
            elif kind == 'submit_review':
                fresh.submit_review(args['actor'], args['task'], args['head'])
            elif kind == 'fail':
                fresh.fail(args['agent'], args['reason'])
            elif kind == 'recover':
                fresh.recover(args['actor'], args['task'], args['evidence'])
            elif kind == 'review_requeue':
                fresh.review_requeue(args['actor'], args['epoch'], args['task'],
                                     args['evidence'])
            elif kind == 'integration_request':
                fresh.integration_request(args['actor'], args['epoch'],
                                          args['task'], args['head'],
                                          args['branch'], args['expected_base'])
            elif kind == 'publish':
                fresh.publish(args['request'])
            elif kind == 'ack_integration':
                fresh.ack(args['actor'], args['request'], args['commit'],
                          base_branch=args['base_branch'],
                          expected_base=args['expected_base'])
            else:
                raise Refusal('unknown_journal_kind')
        return fresh

    # ---- modeled ops (gate chains quoted from the base source) -------------

    def claim(self, actor, task_id, instance=None):
        """Claim per the INTENDED base contract — the bind carries
        owner_instance (control.py:553-554); the deployed interceptor
        deviation is measured in R8, not modeled."""
        s = self._stage()
        agent = s['agents'].get(actor)
        require(agent is not None and agent['qualified'], 'qualified_agent_required')
        task = s['tasks'].get(task_id)
        require(task is not None and task['state'] == 'READY', 'task_not_ready')
        require(set(task['capabilities']) <= agent['capabilities'],
                'capability_missing')
        active = [t for t in s['tasks'].values() if t['owner'] == actor
                  and t['state'] in ('RUNNING', 'BLOCKED', 'REVIEW', 'RECOVERY_HOLD')]
        require(len(active) < agent['max_tasks'], 'agent_capacity_reached')
        require(all(s['tasks'][d]['state'] == 'INTEGRATED'
                    for d in task['dependencies']), 'dependencies_not_integrated')
        for other in s['tasks'].values():
            if other['state'] in ('RUNNING', 'BLOCKED', 'REVIEW', 'RECOVERY_HOLD'):
                require(not any(overlaps(x, y) for x in task['scopes']
                                for y in other['scopes']), 'write_scope_conflict')
        available = [n for n, sl in s['slots'].items()
                     if sl['task'] is None and sl['kind'] == task['kind']
                     and not sl['engine'].get('provisioned')]
        require(bool(available), 'no_free_slot')
        number = available[0]
        s['slots'][number]['task'] = task_id
        task.update(owner=actor, slot=number, state='RUNNING',
                    generation=task['generation'] + 1, owner_instance=instance)
        self.commit('claim', {'actor': actor, 'task': task_id, 'instance': instance})

    def mutate(self, actor, generation, task_id, instance=None):
        """Owned mutation through the _task CAS gate (control.py:116-124)."""
        s = self._stage()
        task = s['tasks'].get(task_id)
        require(task is not None, 'unknown_task')
        require(task['owner'] == actor and task['generation'] == generation,
                'stale_or_foreign_claim')
        require(task['state'] in ('RUNNING', 'BLOCKED', 'REVIEW'),
                'task_not_owned_active')
        if task['owner_instance'] is not None:
            require(instance == task['owner_instance'], 'instance_not_bound')
        task['checkpoint'] = 'mutated@%d' % (s['revision'] + 1)
        self.commit('checkpoint', {'actor': actor, 'generation': generation,
                                   'task': task_id, 'instance': instance})

    def submit_review(self, actor, task_id, head):
        s = self._stage()
        task = s['tasks'].get(task_id)
        require(task is not None, 'unknown_task')
        require(task['owner'] == actor, 'stale_or_foreign_claim')
        require(task['state'] == 'RUNNING', 'task_not_running')
        require(is_sha(head), 'invalid_head')
        task['state'] = 'REVIEW'
        task['head'] = head
        self.commit('submit_review', {'actor': actor, 'task': task_id, 'head': head})

    # ---- crash recovery (control.py:134-149, 152-172, 631-648, 724-735) ----

    def _preserve_provision(self, s, engine, reason, evidence):
        """_preserve_provision (control.py:152-172): retire the ACTIVE
        provision into the bounded preserved_provisions history and clear the
        active fields, so no later task/generation can inherit source
        authority."""
        if not engine.get('provisioned'):
            return None
        record = {'reason': reason, 'evidence': evidence,
                  'cleared_revision': s['revision'] + 1,
                  'provision_task': engine.get('provision_task'),
                  'provision_generation': engine.get('provision_generation'),
                  'worktree_head': engine.get('worktree_head'),
                  'provision_base': engine.get('provision_base'),
                  'provision_evidence': engine.get('provision_evidence')}
        history = engine.setdefault('preserved_provisions', [])
        history.append(record)
        del history[:-20]                      # PRESERVED_PROVISION_LIMIT
        engine['provisioned'] = False
        for k in ('provision_task', 'provision_generation', 'worktree_head',
                  'provision_base', 'provision_evidence'):
            engine.pop(k, None)
        return record

    def provision_slot(self, supervisor, task_id, worktree_head, evidence):
        """provision_slot (control.py:737-751): supervisor-only, RUNNING-only,
        refuses an already-provisioned slot; binds provision_task/generation/
        base so stale authority is distinguishable from current."""
        s = self._stage()
        require(supervisor == 'SUPERVISOR', 'supervisor_only')
        t = s['tasks'].get(task_id)
        require(t is not None, 'unknown_task')
        require(t['slot'] is not None and s['slots'][t['slot']]['task'] == task_id,
                'task_has_no_slot')
        require(t['state'] == 'RUNNING', 'task_not_running')
        engine = s['slots'][t['slot']]['engine']
        require(not engine.get('provisioned'), 'slot_already_provisioned')
        engine['provisioned'] = True
        engine['worktree_head'] = worktree_head
        engine['provision_evidence'] = evidence
        engine['provision_task'] = task_id
        engine['provision_generation'] = t['generation']
        engine['provision_base'] = t['base']
        self.commit('provision_slot', {'actor': supervisor, 'task': task_id,
                                       'worktree_head': worktree_head,
                                       'evidence': evidence})

    def fail(self, aid, reason):
        """_fail (control.py:134-149): owned tasks -> RECOVERY_HOLD at
        generation+1; queues dropped; resource ownership INTENTIONALLY
        retained; leader re-election bumps the epoch."""
        s = self._stage()
        agent = s['agents'].get(aid)
        require(agent is not None and agent['alive'], 'not_live_agent')
        agent['alive'] = False
        for t in s['tasks'].values():
            if t['owner'] == aid and t['state'] in ('RUNNING', 'BLOCKED', 'REVIEW'):
                t['state'] = 'RECOVERY_HOLD'
                t['generation'] += 1
        if s['leader'] == aid:
            alive = sorted(a for a, v in s['agents'].items() if v['alive'])
            s['leader'] = alive[0] if alive else None
            s['epoch'] += 1
        self.commit('fail', {'agent': aid, 'reason': reason})

    def recover(self, supervisor, task_id, evidence):
        """recover (control.py:631-648): RECOVERY_HOLD-only; refuses while a
        resource is still held; provision preserved; slot freed; READY
        ownerless at generation+1."""
        s = self._stage()
        require(supervisor == 'SUPERVISOR', 'preservation_observer_required')
        require(is_sha(evidence) or (isinstance(evidence, str) and evidence),
                'evidence_required')
        t = s['tasks'].get(task_id)
        require(t is not None and t['state'] == 'RECOVERY_HOLD', 'not_recovery_hold')
        require(not any(r['task'] == task_id for r in s['resources'].values()),
                'resources_still_held')
        number = t['slot']
        if number is not None:
            engine = s['slots'][number]['engine']
            self._preserve_provision(s, engine, 'recovered_task_generation', evidence)
            s['slots'][number]['task'] = None
        t.update(state='READY', owner=None, slot=None, owner_instance=None,
                 generation=t['generation'] + 1)
        t['checkpoint'] = evidence
        self.commit('recover', {'actor': supervisor, 'task': task_id,
                                'evidence': evidence})

    def review_requeue(self, actor, epoch_value, task_id, evidence):
        """review_requeue (control.py:724-735): lead+epoch-only; REVIEW ->
        RUNNING, head cleared (review void), generation+1, worktree preserved
        (slot untouched)."""
        s = self._stage()
        require(actor == s['leader'] and epoch_value == s['epoch'],
                'not_leader_or_stale_epoch')
        t = s['tasks'].get(task_id)
        require(t is not None and t['state'] == 'REVIEW', 'not_in_review')
        require(isinstance(evidence, str) and evidence, 'evidence_required')
        t.update(state='RUNNING', head=None, generation=t['generation'] + 1)
        t['checkpoint'] = evidence
        self.commit('review_requeue', {'actor': actor, 'epoch': epoch_value,
                                       'task': task_id, 'evidence': evidence})

    # ---- serialized integration (control.py:695-721, publish.py) -----------

    def integration_request(self, actor, epoch_value, task_id, head, branch,
                            expected_base):
        """integration_request (control.py:695-712): lead+epoch-only,
        REVIEW-only, head+branch identity; ONE request in
        PENDING_EXTERNAL_BROKER carrying the content-addressed expected_base,
        epoch and leader."""
        s = self._stage()
        require(actor == s['leader'] and epoch_value == s['epoch'],
                'not_leader_or_stale_epoch')
        t = s['tasks'].get(task_id)
        require(t is not None and t['state'] == 'REVIEW', 'not_in_review')
        require(head == t['head'] and branch == t['branch'],
                'head_or_branch_mismatch')
        require(is_sha(expected_base), 'invalid_expected_base')
        rid = 'req-%06d' % (s['revision'] + 1)
        s['requests'][rid] = {'task': task_id, 'head': head, 'branch': branch,
                              'base_branch': self.base_branch,
                              'expected_base': expected_base, 'epoch': s['epoch'],
                              'leader': s['leader'],
                              'state': 'PENDING_EXTERNAL_BROKER'}
        self.commit('integration_request', {'actor': actor, 'epoch': epoch_value,
                                            'task': task_id, 'head': head,
                                            'branch': branch,
                                            'expected_base': expected_base,
                                            'request': rid})
        return rid

    def publish(self, request_id):
        """The publish.py adapter semantics (publish.py:50-124) against the
        modeled remote. Refusals are named and leave the remote untouched;
        `already_integrated` is the interrupted-integration reconciliation
        (a push that succeeded but was never acknowledged is detected, never
        repeated)."""
        s = self._stage()
        r = s['requests'].get(request_id)
        require(r is not None, 'unknown_integration_request')
        require(r['state'] == 'PENDING_EXTERNAL_BROKER',
                'integration_already_acknowledged')
        require(r['branch'] != self.forbidden and r['branch'].startswith('astra/'),
                'forbidden_branch')
        remote = self.remote
        # identity gate (publish.py:73-74)
        require(remote.refs.get(r['branch']) == r['head'],
                'task_head_mismatch_remote',
                'remote task branch is %s' % remote.refs.get(r['branch']))
        base_remote = remote.refs.get(self.base_branch)
        # interrupted-integration reconciliation (publish.py:79-83): comes
        # BEFORE base-rewrite detection — an already-merged task must report
        # as integrated, not as refusal.
        if remote.is_ancestor(r['head'], base_remote):
            self.commit('publish', {'request': request_id,
                                    'outcome': 'already_integrated'})
            return 'already_integrated'
        # base never rewritten since the fork (publish.py:92-94)
        require(remote.is_ancestor(r['expected_base'], base_remote),
                'base_rewritten_since_task_fork')
        # fast-forward proof at the remote heads (publish.py:99-102)
        require(remote.base_is_merge_base_of(base_remote, r['head']),
                'non_fast_forward_refused', 'base has diverged; rebase instead')
        # push the exact object, then RE-READ the remote (publish.py:104-121)
        remote.push_count += 1
        remote.set_ref(self.base_branch, r['head'])
        verified = remote.refs[self.base_branch]
        require(verified == r['head'], 'verification_failed_after_push',
                'remote base is %s' % verified)
        self.commit('publish', {'request': request_id, 'outcome': 'pushed',
                                'pushed_head': r['head'],
                                'push_count': remote.push_count})
        return 'pushed'

    def ack(self, supervisor, request_id, commit, base_branch=None,
            expected_base=None):
        """ack_integration (control.py:713-721): trusted-publisher-only;
        epoch+leader binding (`stale_integration_epoch`); idempotence
        (`integration_already_acknowledged`); review unchanged
        (`review_changed`); wrong base refused; -> INTEGRATED with a
        content-addressed commit."""
        s = self._stage()
        require(supervisor == 'SUPERVISOR', 'trusted_publisher_only')
        r = s['requests'].get(request_id)
        require(r is not None, 'unknown_integration_request')
        require(r['epoch'] == s['epoch'] and r['leader'] == s['leader'],
                'stale_integration_epoch')
        require(r['state'] == 'PENDING_EXTERNAL_BROKER',
                'integration_already_acknowledged')
        t = s['tasks'][r['task']]
        require(t['state'] == 'REVIEW' and t['head'] == r['head'], 'review_changed')
        require(base_branch == self.base_branch
                and expected_base == r['expected_base'], 'wrong_integration_base')
        require(is_sha(commit), 'invalid_commit_sha')
        t['state'] = 'INTEGRATED'
        t['integration'] = {'commit': commit}
        r['state'] = 'ACKNOWLEDGED'
        self.commit('ack_integration', {'actor': supervisor,
                                        'request': request_id, 'commit': commit,
                                        'base_branch': base_branch,
                                        'expected_base': expected_base})
