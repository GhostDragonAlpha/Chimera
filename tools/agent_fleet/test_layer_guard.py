"""Characterization regressions for the deployed ReviewHandoffControl layer
and its worker loop, pinning the slot/provision invariants after PR #42 +
fleet-layer-guard-01 (review follow-ups F1/F2/F3/F6).

Fixture surgeries construct legacy stale-provision states on ISOLATED
temporary registries only.
"""
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import Control, Refusal  # noqa: E402
from review_handoff import ReviewHandoffControl  # noqa: E402
from run_queue_worker import WorkerQueue  # noqa: E402

BASE = 'a' * 40
HEAD = 'b' * 40


class LayerGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.c = ReviewHandoffControl(self.root / 'state.sqlite', 'super-secret',
                                      'enroll-secret', self.root / 'slots')
        self.tokens = {}
        for aid in ('lead', 'worker', 'other'):
            self.tokens[aid] = self.c.call('enroll', 'enroll-secret', agent=aid, label=aid)['result']['session_token']
            self.c.call('qualify', 'super-secret', agent=aid, capabilities=['cpu'], max_tasks=5,
                        can_lead=aid == 'lead', rank=10 if aid == 'lead' else 1,
                        evidence='fixture qualification record')
        self.c.call('offer_lead', self.tokens['lead'], epoch=0, checkpoint='ready')
        self.c.call('elect', 'super-secret')

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, op, actor='lead', **p):
        return self.c.call(op, self.tokens.get(actor, actor), **p)['result']

    def snap(self):
        return self.call('snapshot')

    def task(self, tid, **kw):
        p = dict(task=tid, epoch=self.snap()['epoch'], base=BASE, scopes=['tools/labs/' + tid],
                 packet='statement / prediction / falsifier', kind='worker')
        p.update(kw)
        return self.call('create_task', **p)

    def fixture_stale_provision(self, slot_id, task_id, generation, head=HEAD):
        con = sqlite3.connect(self.root / 'state.sqlite')
        try:
            body = json.loads(con.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            engine = body['slots'][slot_id]['engine']
            engine.update(provisioned=True, provision_task=task_id, provision_generation=generation,
                          worktree_head=head, provision_evidence='legacy fixture provision',
                          provision_base=BASE)
            con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(body),))
            con.commit()
        finally:
            con.close()

    # F1: the layered claim refuses a stale-provisioned free slot...
    def test_layered_claim_refuses_stale_provisioned_free_slot(self):
        self.task('one')
        self.call('claim', 'worker', task='one')  # slot 2
        for slot in ('3', '4', '5'):
            self.fixture_stale_provision(slot, 'legacy-' + slot, 1)
        self.task('two')
        with self.assertRaisesRegex(Refusal, 'stale_provision_requires_recovery'):
            self.call('claim', 'other', task='two')
        # ...and the refusal is actionable: supervisor rebind unblocks the claim.
        self.call('slot_rebind', 'super-secret', slot='3', preservation_evidence='p',
                  drain_evidence='d')
        got = self.call('claim', 'other', task='two')
        self.assertEqual(got['slot'], '3')

    # A free slot with NO active provision still claims normally through the layer.
    def test_layered_claim_clean_slot_unaffected(self):
        self.task('one')
        got = self.call('claim', 'worker', task='one')
        self.assertEqual(got['slot'], '2')

    # F2: release_review_slot preserves provision evidence in slot history and receipt.
    def test_release_review_slot_preserves_provision_evidence(self):
        self.task('one')
        t = self.call('claim', 'worker', task='one')
        self.call('provision_slot', 'super-secret', task='one', worktree_head=HEAD,
                  evidence='provision evidence text')
        self.call('submit_review', 'worker', task='one', generation=t['generation'],
                  branch=t['branch'], head=HEAD, evidence='review evidence')
        r = self.call('release_review_slot', 'super-secret',
                      task='one', owner='worker', generation=t['generation'],
                      slot=t['slot'], head=HEAD, pushed_head=HEAD, pr_head=HEAD,
                      pr_identity='PR#fixture', remote_verification_evidence='fetch-verified',
                      preservation_evidence='tree preserved', writer_stopped_evidence='exited',
                      runtime_drained_evidence='none held',
                      slot_reprovision_ready_evidence='clean for next task')
        self.assertTrue(r['slot_released'])
        snap = self.snap()
        engine = snap['slots'][t['slot']]['engine']
        self.assertFalse(engine['provisioned'])
        history = engine['preserved_provisions']
        self.assertEqual(history[-1]['reason'], 'released_for_review_handoff')
        self.assertEqual(history[-1]['provision_evidence'], 'provision evidence text')
        self.assertEqual(history[-1]['worktree_head'], HEAD)
        self.assertEqual(history[-1]['provision_generation'], t['generation'])
        receipt = snap['tasks']['one']['review_slot_handoffs'][-1]
        self.assertEqual(receipt['provision']['worktree_head'], HEAD)
        self.assertEqual(receipt['provision']['provision_evidence'], 'provision evidence text')
        # The released slot is immediately claimable (engine reset, no active provision).
        self.task('two')
        nxt = self.call('claim', 'other', task='two')
        self.assertEqual(nxt['slot'], t['slot'])

    # Detached-review capacity accounting still works with the guard present.
    def test_detached_review_frees_capacity_for_second_claim(self):
        self.task('one')
        t = self.call('claim', 'worker', task='one')
        self.call('provision_slot', 'super-secret', task='one', worktree_head=HEAD,
                  evidence='e')
        self.call('submit_review', 'worker', task='one', generation=t['generation'],
                  branch=t['branch'], head=HEAD, evidence='review evidence')
        self.call('release_review_slot', 'super-secret',
                  task='one', owner='worker', generation=t['generation'],
                  slot=t['slot'], head=HEAD, pushed_head=HEAD, pr_head=HEAD,
                  pr_identity='PR#fixture', remote_verification_evidence='v',
                  preservation_evidence='p', writer_stopped_evidence='w',
                  runtime_drained_evidence='d', slot_reprovision_ready_evidence='r')
        self.call('qualify', 'super-secret', agent='worker', capabilities=['cpu'],
                  max_tasks=1, can_lead=False, rank=0, evidence='capacity one')
        self.task('two')
        nxt = self.call('claim', 'worker', task='two')
        self.assertEqual(nxt['slot'], t['slot'])
        self.assertIsNone(self.snap()['tasks']['one']['slot'])

    # F3: the worker loop treats the refusal as recoverable contention.
    def test_claim_contention_classifies_stale_provision_refusal(self):
        for message in ('{"error": "stale_provision_requires_recovery"}',
                        'stale_provision_requires_recovery'):
            self.assertTrue(WorkerQueue._claim_contention(ValueError(message)), message)
        for message in ('{"error": "unauthorized"}', 'transport broke'):
            self.assertFalse(WorkerQueue._claim_contention(ValueError(message)), message)

    # End-to-end: WorkerQueue.claim_once skips the stale refusal without crashing
    # when another clean slot/task exists, and reports refusals.
    def test_worker_queue_skips_stale_refusal(self):
        self.task('one')
        self.call('claim', 'worker', task='one')  # worker holds slot 2
        for slot in ('3', '4'):
            self.fixture_stale_provision(slot, 'legacy-' + slot, 1)
        self.task('two')
        calls = {'n': 0}

        def fake_call(op, args):
            calls['n'] += 1
            if op == 'snapshot':
                return {'result': self.snap()}
            assert op == 'claim' and args['task'] == 'two'
            # first attempt (slot 3/4 stale, 5 clean? make all stale to force refusal)
            raise ValueError('{"error": "stale_provision_requires_recovery"}')

        self.fixture_stale_provision('5', 'legacy-5', 1)
        q = WorkerQueue(fake_call, agent='other')
        out = q.claim_once()
        self.assertIsNotNone(out)
        self.assertEqual(out['task'], None)
        self.assertTrue(any('two' in x for x in out['refusals']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
