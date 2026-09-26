"""ONT-P04 contract probes (records profile, offline, CPU-only fixtures).

Frozen in PREREGISTRATION.md before any run. Every probe runs against the
byte-exact extraction of attempt head c525b82c in ./pinned/tools/agent_fleet
(isolated temporary registries; never the live registry, never a real GPU).

Clause map (done_when of P04):
  C1 every launched job uses existing ownership/broker rules
  C2 admitted training may interrupt gaming and local inference through a
     verified supervisor handoff  (records: implemented supervisor authority
     primitives + published handoff contract; the six-state machine itself is
     NOT implemented at this head -- named, not invented)
  C3 already-running protected training retains ownership until confirmed release
  C27 compute/memory budgets (memory admission slice owned by this controller)
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

PINNED = Path(__file__).resolve().parent / 'pinned' / 'tools' / 'agent_fleet'
sys.path.insert(0, str(PINNED))

from control import Control, Refusal            # noqa: E402
from review_handoff import ReviewHandoffControl  # noqa: E402
from run_queue import QueueRefusal, RunQueue     # noqa: E402

BASE = 'a' * 40
HEAD = 'b' * 40


class Harness:
    """Shared fixture: isolated Control registry, three qualified agents."""

    def setup(self, cls=Control, supervisor_token='SUP'):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.c = cls(self.root / 'state.sqlite', supervisor_token, 'ENR',
                     self.root / 'slots', memory_budget_mb=8192)
        self.tok = {}
        for aid in ('lead', 'gamer', 'trainer'):
            self.tok[aid] = self.c.call('enroll', 'ENR', agent=aid,
                                        label=aid)['result']['session_token']
            self.c.call('qualify', supervisor_token, agent=aid,
                        capabilities=['cpu', 'gpu'],
                        max_tasks=3, can_lead=aid == 'lead',
                        rank=5 if aid == 'lead' else 1,
                        evidence='ONT-P04 fixture qualification')
        self.c.call('offer_lead', self.tok['lead'], epoch=0,
                    checkpoint='ONT-P04 fixture; no foreign work')
        self.c.call('elect', supervisor_token)

    def teardown(self):
        self.tmp.cleanup()

    def snap(self):
        return self.c.call('snapshot', 'SUP')['result']

    def call(self, op, actor='lead', **p):
        return self.c.call(op, self.tok.get(actor, actor), **p)['result']

    def refused(self, op, actor, error, **p):
        with self.assertRaisesRegex(Refusal, error):
            self.call(op, actor, **p)

    def task(self, tid, **kw):
        p = dict(task=tid, epoch=self.snap()['epoch'], base=BASE,
                 scopes=kw.pop('scopes', None) or ['docs/evidence/p04-' + tid],
                 packet='statement / prediction / falsifier',
                 kind=kw.pop('kind', 'worker'))
        p.update(kw)
        return self.call('create_task', **p)

    def claim(self, tid, actor):
        return self.call('claim', actor, task=tid)

    def gen(self, tid):
        return self.snap()['tasks'][tid]['generation']

    def request(self, tid, actor, wants, priority=5):
        return self.call('resource_request', actor, task=tid,
                         generation=self.gen(tid), wants=wants,
                         priority=priority)

    def release(self, tid, actor, resource, evidence='drained: ONT-P04 fixture'):
        return self.call('resource_release', actor, task=tid,
                         generation=self.gen(tid), resource=resource,
                         evidence=evidence)


class C1LaunchOwnershipTests(Harness, unittest.TestCase):
    """C1: every launched job goes through the existing ownership rules."""

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def test_claim_requires_qualified_agent_and_ready_task(self):
        self.task('j1')
        # unqualified/foreign principal cannot launch a job at all
        foreign = self.c.call('enroll', 'ENR', agent='stranger',
                              label='stranger')['result']['session_token']
        with self.assertRaisesRegex(Refusal, 'qualified_agent_required'):
            self.c.call('claim', foreign, task='j1')
        # an already-owned (RUNNING) task cannot be claimed again
        self.claim('j1', 'gamer')
        with self.assertRaisesRegex(Refusal, 'task_not_ready'):
            self.call('claim', 'trainer', task='j1')
        # identity of the launched job is recorded: owner + generation
        t = self.snap()['tasks']['j1']
        self.assertEqual(t['owner'], 'gamer')
        self.assertEqual(t['state'], 'RUNNING')
        self.assertEqual(t['generation'], 1)

    def test_claim_refuses_unmet_dependencies_and_scope_conflict(self):
        self.task('dep')
        self.task('child', dependencies=['dep'])
        with self.assertRaisesRegex(Refusal, 'dependencies_not_integrated'):
            self.call('claim', 'gamer', task='child')
        # a second job whose write scope overlaps a live job is refused
        self.task('live', scopes=['docs/evidence/p04-shared'])
        self.task('intruder', scopes=['docs/evidence/p04-shared'])
        self.claim('live', 'gamer')
        with self.assertRaisesRegex(Refusal, 'write_scope_conflict'):
            self.call('claim', 'trainer', task='intruder')

    def test_resource_request_bound_to_owned_live_generation(self):
        self.task('w1')
        # stale generation identity is refused
        with self.assertRaisesRegex(Refusal, 'stale_or_foreign_claim'):
            self.call('resource_request', 'gamer', task='w1', generation=99,
                      wants=[{'name': 'rtx4090'}], priority=5)
        self.claim('w1', 'gamer')
        # unknown resource and malformed wants are refused by name
        with self.assertRaisesRegex(Refusal, 'unknown_resource'):
            self.request('w1', 'gamer', [{'name': 'not-a-resource'}])
        with self.assertRaisesRegex(Refusal, 'duplicate_resource_want'):
            self.request('w1', 'gamer', [{'name': 'rtx4090'}, {'name': 'rtx4090'}])
        # an admission without any launch (unclaimed task) is refused
        self.task('w2')
        with self.assertRaisesRegex(Refusal, 'stale_or_foreign_claim'):
            self.request('w2', 'trainer', [{'name': 'rtx4090'}])

    def test_no_double_grant_of_single_gpu(self):
        self.task('game'); self.task('train')
        self.claim('game', 'gamer'); self.claim('train', 'trainer')
        g = self.request('game', 'gamer', [{'name': 'rtx4090'}])
        self.assertTrue(g['granted'])
        t = self.request('train', 'trainer', [{'name': 'rtx4090'}])
        self.assertFalse(t['granted'])
        self.assertEqual(t['stalled'], 'contended:rtx4090')
        res = self.snap()['resources']
        self.assertEqual([k for k in res if k == 'rtx4090'], ['rtx4090'])
        self.assertEqual(res['rtx4090']['task'], 'game',
                         'the GPU is granted exactly once, to the first owner')


class C2TrainingSerializationTests(Harness, unittest.TestCase):
    """C2 records slice: an admitted training job obtains the GPU only through
    the supervisor-owned release/drain rules; queue discipline never lets an
    arbitrary priority number jump the queue. The six-state handoff itself is
    contract records at this head (test_p04_records.py), not implemented."""

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def test_training_waits_for_gaming_release_then_transfers(self):
        self.task('gaming'); self.task('training')
        self.claim('gaming', 'gamer'); self.claim('training', 'trainer')
        self.request('gaming', 'gamer', [{'name': 'rtx4090'}])
        req = self.request('training', 'trainer', [{'name': 'rtx4090'}])
        # admitted request waits; it cannot steal the resource
        self.assertFalse(req['granted'])
        self.assertEqual(self.snap()['resources']['rtx4090']['task'], 'gaming')
        # the only transfer path is the owner's evidenced release (the drain
        # boundary the supervisor handoff records build upon)
        with self.assertRaisesRegex(Refusal, 'resource_drained_evidence'):
            self.release('gaming', 'gamer', 'rtx4090', evidence='')
        self.release('gaming', 'gamer', 'rtx4090')
        res = self.snap()['resources']
        self.assertEqual(res['rtx4090']['task'], 'training')
        self.assertEqual(res['rtx4090']['generation'], self.gen('training'))

    def test_multiple_training_requests_serialize_in_arrival_order(self):
        self.task('game'); self.task('train-a'); self.task('train-b')
        self.claim('game', 'gamer')
        self.claim('train-a', 'trainer'); self.claim('train-b', 'lead')
        self.request('game', 'gamer', [{'name': 'rtx4090'}])
        first = self.request('train-a', 'trainer', [{'name': 'rtx4090'}],
                             priority=1)
        second = self.request('train-b', 'lead', [{'name': 'rtx4090'}],
                              priority=9)
        self.assertFalse(first['granted']); self.assertFalse(second['granted'])
        self.assertLess(first['enqueued_revision'], second['enqueued_revision'])
        # release of the gaming holder serves train-a (arrival order), NOT the
        # priority-9 later request: "do not let arbitrary worker priority
        # numbers jump the queue" (COORDINATION.md GPU handoff, rule 2)
        self.release('game', 'gamer', 'rtx4090')
        res = self.snap()['resources']
        self.assertEqual(res['rtx4090']['task'], 'train-a')
        still = self.call('resource_queue', 'lead', task='train-b',
                          generation=self.gen('train-b'))
        self.assertEqual(len(still['queued']), 1)

    def test_supervisor_clear_is_supervisor_only_and_needs_drain_evidence(self):
        self.task('held'); self.claim('held', 'gamer')
        self.request('held', 'gamer', [{'name': 'rtx4090'}])
        with self.assertRaisesRegex(Refusal, 'supervisor_only'):
            self.call('resource_clear', 'gamer', resource='rtx4090',
                      evidence='not the supervisor')
        with self.assertRaisesRegex(Refusal, 'actual_process_drained_evidence'):
            self.call('resource_clear', 'SUP', resource='rtx4090', evidence='')
        self.call('resource_clear', 'SUP', resource='rtx4090',
                  evidence='ONT-P04 fixture: actual process drained observed')
        self.assertNotIn('rtx4090', self.snap()['resources'])

    def test_local_inference_child_release_order_preserved(self):
        # dyad_eye (local-model inference path) is chained to the GPU: it
        # cannot exist without the same-task GPU and must drain first.
        self.task('infer'); self.claim('infer', 'trainer')
        self.request('infer', 'trainer', [{'name': 'rtx4090'}])
        self.request('infer', 'trainer', [{'name': 'dyad_eye'}])
        with self.assertRaisesRegex(Refusal, 'release_dyad_first'):
            self.release('infer', 'trainer', 'rtx4090')
        self.release('infer', 'trainer', 'dyad_eye')
        self.release('infer', 'trainer', 'rtx4090')
        self.assertEqual(self.snap()['resources'], {})


class C3ProtectedTrainingTests(Harness, unittest.TestCase):
    """C3: a running protected holder keeps ownership until confirmed release."""

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def test_holder_cannot_be_displaced_and_foreign_release_refused(self):
        self.task('prot'); self.task('raider')
        self.claim('prot', 'trainer'); self.claim('raider', 'gamer')
        self.request('prot', 'trainer', [{'name': 'rtx4090'}])
        before = self.snap()['resources']['rtx4090']
        # raider cannot release or overwrite someone else's hold
        with self.assertRaisesRegex(Refusal, 'stale_or_foreign_claim'):
            self.release('prot', 'gamer', 'rtx4090')
        # a same-name class change cannot replace the reservation
        r = self.request('prot', 'trainer',
                         [{'name': 'rtx4090', 'class': 'gpu_benchmark'}])
        self.assertEqual(r['dropped_reason'], 'release_required')
        self.assertEqual(self.snap()['resources']['rtx4090'], before)
        # confirmed release by the actual owner at the live generation works
        self.release('prot', 'trainer', 'rtx4090')
        self.assertNotIn('rtx4090', self.snap()['resources'])

    def test_release_requires_owner_and_live_generation(self):
        self.task('own'); self.claim('own', 'trainer')
        self.request('own', 'trainer', [{'name': 'rtx4090'}])
        with self.assertRaisesRegex(Refusal, 'stale_or_foreign_claim'):
            self.call('resource_release', 'trainer', task='own', generation=99,
                      resource='rtx4090', evidence='wrong generation')
        self.release('own', 'trainer', 'rtx4090')
        self.assertNotIn('rtx4090', self.snap()['resources'])

    def test_engine_owner_preserved_until_drained_then_bulk_transfer(self):
        self.task('a'); self.task('b')
        self.claim('a', 'trainer'); self.claim('b', 'gamer')
        self.request('a', 'trainer', [{'name': 'rtx4090'}, {'name': 'engine_demo'}])
        with self.assertRaisesRegex(Refusal, 'release_engine_first'):
            self.release('a', 'trainer', 'rtx4090')
        pending = self.request('b', 'gamer',
                               [{'name': 'rtx4090'}, {'name': 'engine_demo'}])
        self.assertFalse(pending['granted'])
        self.release('a', 'trainer', 'engine_demo')
        self.release('a', 'trainer', 'rtx4090')
        res = self.snap()['resources']
        self.assertEqual(res['engine_demo']['task'], 'b')
        self.assertEqual(res['rtx4090']['task'], 'b')


class C27MemoryBudgetTests(Harness, unittest.TestCase):
    """C27 slice owned by this controller: memory admission accounting."""

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def test_over_budget_refusal_is_all_or_nothing_and_accounted(self):
        self.task('m1'); self.task('m2')
        self.claim('m1', 'gamer'); self.claim('m2', 'trainer')
        self.request('m1', 'gamer', [{'name': 'memory', 'memory_mb': 6000}])
        self.assertEqual(self.snap()['memory']['admitted_mb'], 6000)
        r = self.request('m2', 'trainer', [{'name': 'memory', 'memory_mb': 3000}])
        self.assertFalse(r['granted'])
        self.assertTrue(r['allocation_failed'])
        self.assertEqual(r['stalled'], 'memory_allocation_refused')
        self.assertEqual(self.snap()['memory']['admitted_mb'], 6000,
                         'the refused job must not hold partial memory')
        self.assertFalse(any(k.startswith('memory.') for k in self.snap()['resources']
                             if self.snap()['resources'][k]['task'] == 'm2'))
        # freeing m1 admits the still-queued m2 request (recorded pending
        # requests auto-promote; a refused grant never held partial memory)
        self.release('m1', 'gamer', 'memory')
        self.assertEqual(self.snap()['memory']['admitted_mb'], 3000)
        mem_keys = [k for k in self.snap()['resources'] if k.startswith('memory.')]
        self.assertEqual(self.snap()['resources'][mem_keys[0]]['task'], 'm2')
        self.release('m2', 'trainer', 'memory')
        self.assertEqual(self.snap()['memory']['admitted_mb'], 0)


class BrokerRulesTests(Harness, unittest.TestCase):
    """C1 broker slice: release_review_slot through ReviewHandoffControl."""

    def setUp(self):
        self.setup(cls=ReviewHandoffControl)

    def tearDown(self):
        self.teardown()

    def review_ready(self, tid='reviewed'):
        self.task(tid)
        claimed = self.claim(tid, 'trainer')
        self.call('checkpoint', 'trainer', task=tid,
                  generation=claimed['generation'], checkpoint='kept')
        self.call('provision_slot', 'SUP', task=tid,
                  worktree_head=BASE, evidence='fixture provision receipt')
        self.call('submit_review', 'trainer', task=tid,
                  generation=claimed['generation'], branch=claimed['branch'],
                  head=HEAD, evidence='exact review evidence')
        return claimed

    def handoff_args(self, tid='reviewed', **over):
        t = self.snap()['tasks'][tid]
        args = dict(task=tid, owner=t['owner'], generation=t['generation'],
                    slot=t['slot'], head=t['head'], pushed_head=t['head'],
                    pr_head=t['head'], pr_identity='PR #fixture',
                    remote_verification_evidence='broker verified remote head',
                    preservation_evidence='artifacts preserved',
                    writer_stopped_evidence='writer stopped',
                    runtime_drained_evidence='runtime drained',
                    slot_reprovision_ready_evidence='slot drained')
        args.update(over)
        return args

    def test_broker_requires_supervisor_and_exact_head_identity(self):
        self.review_ready()
        with self.assertRaisesRegex(Refusal, 'supervisor_only'):
            self.call('release_review_slot', 'trainer', **self.handoff_args())
        with self.assertRaisesRegex(Refusal, 'review_head_identity_mismatch'):
            self.call('release_review_slot', 'SUP',
                      **self.handoff_args(pushed_head='c' * 40))

    def test_broker_refuses_stale_identity_and_held_resources(self):
        self.review_ready()
        with self.assertRaisesRegex(Refusal, 'stale_generation'):
            self.call('release_review_slot', 'SUP',
                      **self.handoff_args(generation=99))
        with self.assertRaisesRegex(Refusal, 'stale_slot'):
            self.call('release_review_slot', 'SUP',
                      **self.handoff_args(slot='no-such-slot'))
        # a REVIEW task cannot even acquire a NEW resource (promotions drop
        # stale-claim states): request while in REVIEW is dropped, not granted
        r = self.call('resource_request', 'trainer', task='reviewed',
                      generation=self.gen('reviewed'),
                      wants=[{'name': 'rtx4090'}], priority=5)
        self.assertEqual(r['dropped_reason'], 'stale_claim')
        self.assertNotIn('rtx4090', self.snap()['resources'])
        # a RUNNING task must drain before review at all (earlier gate, same law)
        self.task('holding'); self.claim('holding', 'trainer')
        self.request('holding', 'trainer', [{'name': 'rtx4090'}])
        with self.assertRaisesRegex(Refusal, 'release_resources_before_review'):
            self.call('submit_review', 'trainer', task='holding',
                      generation=self.gen('holding'),
                      branch=self.snap()['tasks']['holding']['branch'],
                      head=HEAD, evidence='must drain first')
        # defense-in-depth: the broker itself refuses if a hold exists anyway
        # (fixture surgery on the isolated registry, as the pinned lifecycle
        # suite does)
        con = self.c.connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            s = json.loads(con.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            s['resources']['rtx4090'] = {'task': 'reviewed',
                                         'owner': s['tasks']['reviewed']['owner'],
                                         'generation': s['tasks']['reviewed']['generation'],
                                         'class': 'gpu_functionality',
                                         'since_revision': s['revision'] + 1,
                                         'memory_mb': None, 'request': 'fixture'}
            con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(s),))
            con.execute('COMMIT')
        finally:
            con.close()
        with self.assertRaisesRegex(Refusal, 'resources_still_held'):
            self.call('release_review_slot', 'SUP', **self.handoff_args())

    def test_broker_emits_receipt_and_frees_capacity_on_success(self):
        self.review_ready()
        before_slot = self.snap()['tasks']['reviewed']['slot']
        out = self.call('release_review_slot', 'SUP',
                        **self.handoff_args())
        self.assertEqual(out['state'], 'REVIEW')
        self.assertEqual(out['slot_released'], before_slot)
        self.assertFalse(out['filesystem_deleted'])
        self.assertEqual(out['acceptance'], 'NOT_CLAIMED')
        t = self.snap()['tasks']['reviewed']
        self.assertEqual(t['state'], 'REVIEW')
        self.assertIsNone(t['slot'])
        handoffs = t.get('review_slot_handoffs') or []
        self.assertEqual(len(handoffs), 1)
        receipt = handoffs[0]
        self.assertEqual(receipt['head'], HEAD)
        self.assertEqual(receipt['pr_head'], HEAD)
        self.assertTrue(receipt['preservation_evidence'])
        self.assertTrue(receipt['runtime_drained_evidence'])
        # the released slot is free again with its provision retired to history
        slot = self.snap()['slots'][before_slot]
        self.assertIsNone(slot['task'])
        self.assertTrue(slot['engine'].get('preserved_provisions'))


class RunQueueDispatchTests(unittest.TestCase):
    """C1 dispatch-policy slice: fenced, dependency-gated job dispatch.

    The run queue is the in-memory reference dispatch model (never the durable
    authority); its lease fencing is the same retention law as C3: an expired
    lease alone never frees a job to a new owner.
    """

    def setUp(self):
        self.q = RunQueue()

    def test_dependency_gated_dispatch(self):
        self.q.enqueue('base', priority=5)
        self.q.enqueue('next', dependencies=('base',), priority=9)
        runs = self.q.dispatch(owner='w1', capacity=2, now=100.0,
                               lease_seconds=60.0)
        self.assertEqual([r.task for r in runs], ['base'],
                         'a higher-priority dependent job must wait for INTEGRATED')
        self.q.submit_review('base', owner='w1', generation=1, now=110.0,
                             head='h' * 40, evidence='review evidence')
        self.q.acknowledge_integration('base', head='h' * 40)
        runs = self.q.dispatch(owner='w1', capacity=2, now=120.0,
                               lease_seconds=60.0)
        self.assertEqual([r.task for r in runs], ['next'])

    def test_expired_lease_enters_recovery_hold_not_reassignment(self):
        self.q.enqueue('job')
        self.q.dispatch(owner='w1', capacity=1, now=100.0, lease_seconds=60.0)
        expired = self.q.expire(now=200.0)
        self.assertEqual([r.task for r in expired], ['job'])
        snap = {s['task']: s for s in self.q.snapshot()}['job']
        self.assertEqual(snap['state'], 'RECOVERY_HOLD')
        self.assertEqual(snap['owner'], 'w1',
                         'expiry alone must not free the fencing identity')
        # another owner still cannot take it; recovery needs BOTH evidences
        runs = self.q.dispatch(owner='w2', capacity=2, now=210.0,
                               lease_seconds=60.0)
        self.assertEqual(runs, [])
        with self.assertRaises(QueueRefusal):
            self.q.recover('job', preserved_evidence=' ',
                           drained_evidence='drained')
        run = self.q.recover('job', preserved_evidence='worktree preserved',
                             drained_evidence='processes drained')
        self.assertEqual(run.state, 'READY')
        self.assertIsNone(run.owner)


if __name__ == '__main__':
    unittest.main(verbosity=2)
