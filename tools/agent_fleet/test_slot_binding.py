"""Slot/task/generation binding regressions for the fleet controller.

Covers the preregistered falsifiers of fleet-slot-binding-01
(docs/evidence/agent_fleet/SLOT_BINDING/PREREGISTRATION.md):
inherited provision accepted as current, worker-driven rebind, held-runtime
rebind, silent evidence deletion, claim-time adoption of a foreign active
provision, and collateral damage to unrelated state.

Legacy stale-provision slot states are constructed by direct surgery on the
ISOLATED TEMPORARY fixture registry only, simulating registries written before
the binding fix (the observed live condition); the live registry is never
touched by these tests.
"""
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import Control, Refusal  # noqa: E402

BASE = 'a' * 40
HEAD = 'b' * 40
MERGED = 'c' * 40


class SlotBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.c = Control(self.root / 'state.sqlite', 'super-secret', 'enroll-secret', self.root / 'slots')
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

    def provision(self, tid, head=HEAD):
        return self.call('provision_slot', 'super-secret', task=tid, worktree_head=head,
                         evidence='fixture provision evidence')

    def fixture_stale_provision(self, slot_id, task_id, generation, head=HEAD):
        """Simulate a pre-fix registry: an ACTIVE provision from an earlier
        task/generation. Fixture surgery on the temp registry only."""
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

    # T1: stale-generation provision refused; supervised rebind repairs it.
    def test_stale_generation_provision_refused_then_rebind_repairs(self):
        self.task('one')
        self.call('claim', 'worker', task='one')  # gen 1, slot 2
        self.fixture_stale_provision('2', 'one', 0)
        with self.assertRaisesRegex(Refusal, 'slot_already_provisioned'):
            self.provision('one')
        r = self.call('slot_rebind', 'super-secret', slot='2',
                      preservation_evidence='dirty tree preserved at evidence path',
                      drain_evidence='no processes; no resources held')
        self.assertTrue(r['rebound'])
        self.assertEqual(r['cleared']['provision_task'], 'one')
        self.assertEqual(r['cleared']['provision_generation'], 0)
        self.assertFalse(r['filesystem_touched'])
        p = self.provision('one')
        self.assertEqual((p['provision_task'], p['provision_generation'], p['provision_base']),
                         ('one', 1, BASE))
        engine = self.snap()['slots']['2']['engine']
        self.assertEqual((engine['provision_task'], engine['provision_generation']), ('one', 1))
        self.assertEqual(engine['preserved_provisions'][-1]['provision_generation'], 0)

    # T2: authority and attestation refusals.
    def test_rebind_authority_and_attestations(self):
        self.task('one')
        self.call('claim', 'worker', task='one')
        self.fixture_stale_provision('2', 'one', 0)
        for actor in ('worker', 'lead'):
            with self.assertRaisesRegex(Refusal, 'supervisor_only'):
                self.call('slot_rebind', actor, slot='2', preservation_evidence='x', drain_evidence='y')
        with self.assertRaisesRegex(Refusal, 'preservation_evidence'):
            self.call('slot_rebind', 'super-secret', slot='2', preservation_evidence='  ',
                      drain_evidence='y')
        with self.assertRaisesRegex(Refusal, 'drain_evidence'):
            self.call('slot_rebind', 'super-secret', slot='2', preservation_evidence='x',
                      drain_evidence='')
        # A slot with no active provision has nothing to rebind.
        self.task('two')
        with self.assertRaisesRegex(Refusal, 'no_stale_provision'):
            self.call('slot_rebind', 'super-secret', slot='3', preservation_evidence='x',
                      drain_evidence='y')
        with self.assertRaisesRegex(Refusal, 'unknown_slot'):
            self.call('slot_rebind', 'super-secret', slot='9', preservation_evidence='x',
                      drain_evidence='y')

    # T3: held runtime blocks rebind of the old provision task.
    def test_rebind_refused_while_old_task_holds_resources(self):
        self.task('one')
        t = self.call('claim', 'worker', task='one')
        self.fixture_stale_provision('2', 'one', 0)
        args = dict(task='one', generation=t['generation'])
        self.call('resource_acquire', 'worker', resource='rtx4090', evidence='gpu in use', **args)
        with self.assertRaisesRegex(Refusal, 'resources_still_held'):
            self.call('slot_rebind', 'super-secret', slot='2', preservation_evidence='x',
                      drain_evidence='claimed drained but registry disagrees')
        self.call('resource_release', 'worker', resource='rtx4090', evidence='process exited; drained', **args)
        self.assertTrue(self.call('slot_rebind', 'super-secret', slot='2',
                                  preservation_evidence='x', drain_evidence='drained')['rebound'])

    # T4: a slot bound to a non-RUNNING task is not rebindable.
    def test_rebind_refused_when_slot_task_not_running(self):
        self.task('one')
        t = self.call('claim', 'worker', task='one')
        self.provision('one')
        self.call('submit_review', 'worker', task='one', generation=t['generation'],
                  branch=t['branch'], head=HEAD, evidence='fixture review')
        with self.assertRaisesRegex(Refusal, 'slot_task_not_running'):
            self.call('slot_rebind', 'super-secret', slot='2', preservation_evidence='x',
                      drain_evidence='y')

    # T5: recover clears the active provision AND preserves the record.
    def test_recover_clears_and_preserves_provision(self):
        self.task('one')
        t = self.call('claim', 'worker', task='one')
        self.provision('one')
        self.call('fail', 'super-secret', agent='worker', reason='PROCESS_EXIT', evidence='exited')
        self.call('recover', 'super-secret', task='one', evidence='preserved tree; writer stopped')
        engine = self.snap()['slots']['2']['engine']
        self.assertFalse(engine['provisioned'])
        self.assertNotIn('worktree_head', engine)
        record = engine['preserved_provisions'][-1]
        self.assertEqual(record['reason'], 'recovered_task_generation')
        self.assertEqual(record['provision_task'], 'one')
        self.assertEqual(record['provision_generation'], t['generation'])
        self.assertEqual(record['worktree_head'], HEAD)
        # The next claimant provisions fresh at its own generation: no inheritance.
        n = self.call('claim', 'other', task='one')
        self.assertGreater(n['generation'], t['generation'])
        p = self.provision('one')
        self.assertEqual(p['provision_generation'], n['generation'])

    # T6: release_slot retires the provision into bounded history, not /dev/null.
    def test_release_slot_preserves_provision_record(self):
        self.task('one')
        t = self.call('claim', 'worker', task='one')
        self.provision('one')
        self.call('submit_review', 'worker', task='one', generation=t['generation'],
                  branch=t['branch'], head=HEAD, evidence='fixture review')
        r = self.call('integration_request', task=t['id'], head=HEAD, branch=t['branch'],
                      expected_base=BASE, epoch=self.snap()['epoch'], review='fixture review')
        self.call('ack_integration', 'super-secret', request=r['request'],
                  base_branch='astra/gait-capture', expected_base=BASE, commit=MERGED,
                  evidence='fixture publisher')
        self.call('release_slot', 'super-secret', task='one', evidence='clean; stopped')
        engine = self.snap()['slots']['2']['engine']
        self.assertFalse(engine['provisioned'])
        record = engine['preserved_provisions'][-1]
        self.assertEqual(record['reason'], 'released_after_integration')
        self.assertEqual(record['worktree_head'], HEAD)
        self.assertEqual(record['provision_evidence'], 'fixture provision evidence')

    # T7: claim never silently adopts a foreign active provision.
    def test_claim_refuses_stale_provisioned_free_slot(self):
        self.task('one')
        self.call('claim', 'worker', task='one')  # slot 2
        for slot in ('3', '4', '5'):
            self.fixture_stale_provision(slot, 'legacy-' + slot, 1)
        self.task('two')
        with self.assertRaisesRegex(Refusal, 'stale_provision_requires_recovery'):
            self.call('claim', 'other', task='two')
        self.call('slot_rebind', 'super-secret', slot='3', preservation_evidence='x',
                  drain_evidence='y')
        got = self.call('claim', 'other', task='two')
        self.assertEqual(got['slot'], '3')

    # T8: rebind leaves unrelated tasks/claims/slots untouched.
    def test_rebind_does_not_disturb_unrelated_state(self):
        self.task('one')
        a = self.call('claim', 'worker', task='one')
        self.provision('one')
        self.task('two')
        b = self.call('claim', 'other', task='two')
        self.fixture_stale_provision('4', 'legacy-4', 2)
        before = self.snap()
        self.call('slot_rebind', 'super-secret', slot='4', preservation_evidence='x',
                  drain_evidence='y')
        after = self.snap()
        self.assertEqual(after['tasks']['one'], before['tasks']['one'])
        self.assertEqual(after['tasks']['two'], before['tasks']['two'])
        self.assertEqual(after['slots']['2'], before['slots']['2'])
        self.assertEqual(after['slots']['3'], before['slots']['3'])
        self.assertEqual(after['revision'], before['revision'] + 1)
        self.assertFalse(after['slots']['4']['engine']['provisioned'])

    # T9: preserved history is bounded.
    def test_preserved_provision_history_bounded(self):
        self.task('one')
        self.call('claim', 'worker', task='one')
        for i in range(25):
            self.provision('one', head=('%040x' % i))
            self.call('slot_rebind', 'super-secret', slot='2',
                      preservation_evidence='cycle %d' % i, drain_evidence='cycle %d' % i)
        history = self.snap()['slots']['2']['engine']['preserved_provisions']
        self.assertEqual(len(history), 20)
        self.assertEqual(history[-1]['worktree_head'], '%040x' % 24)
        self.assertEqual(history[0]['worktree_head'], '%040x' % 5)

    # T10: the deployed ReviewHandoffControl layer inherits binding, rebind and
    # recover preservation (it does not override those operations).
    def test_review_handoff_layer_inherits_binding_and_rebind(self):
        from review_handoff import ReviewHandoffControl
        c = ReviewHandoffControl(self.root / 'state2.sqlite', 'super-secret', 'enroll-secret',
                                 self.root / 'slots2')
        lead_tok = c.call('enroll', 'enroll-secret', agent='l', label='l')['result']['session_token']
        tok = c.call('enroll', 'enroll-secret', agent='w', label='w')['result']['session_token']
        c.call('qualify', 'super-secret', agent='l', capabilities=['cpu'], max_tasks=5,
               can_lead=True, rank=10, evidence='fixture')
        c.call('qualify', 'super-secret', agent='w', capabilities=['cpu'], max_tasks=5,
               can_lead=False, rank=0, evidence='fixture')
        c.call('offer_lead', lead_tok, epoch=0, checkpoint='ready')
        c.call('elect', 'super-secret')
        epoch = c.call('snapshot', tok)['result']['epoch']
        c.call('create_task', lead_tok, task='one', epoch=epoch, base=BASE,
               scopes=['tools/labs/one'], packet='p', kind='worker')
        t = c.call('claim', tok, task='one')['result']
        p = c.call('provision_slot', 'super-secret', task='one', worktree_head=HEAD,
                   evidence='fixture')['result']
        self.assertEqual((p['provision_task'], p['provision_generation']), ('one', t['generation']))
        c.call('fail', 'super-secret', agent='w', reason='PROCESS_EXIT', evidence='exited')
        c.call('recover', 'super-secret', task='one', evidence='preserved; stopped')
        engine = c.call('snapshot', lead_tok)['result']['slots']['2']['engine']
        self.assertFalse(engine['provisioned'])
        self.assertEqual(engine['preserved_provisions'][-1]['provision_task'], 'one')

    # T11: rebind events carry the slot id for audit.
    def test_rebind_event_records_slot(self):
        self.task('one')
        self.call('claim', 'worker', task='one')
        self.fixture_stale_provision('2', 'one', 0)
        rev = self.snap()['revision']
        self.call('slot_rebind', 'super-secret', slot='2', preservation_evidence='x',
                  drain_evidence='y')
        events = self.call('events', since=rev)['events']
        self.assertEqual(events[-1]['kind'], 'slot_rebind')
        self.assertEqual(events[-1]['slot'], '2')
        self.assertEqual(events[-1]['actor'], 'SUPERVISOR')


if __name__ == '__main__':
    unittest.main(verbosity=2)
