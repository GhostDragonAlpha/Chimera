"""test_resources.py -- integrated fleet resource scheduler contract.

Covers the five-slot resource layer on an ISOLATED registry (never the live
one). The law: machine-readable task declarations, ALL-OR-NOTHING grouped
grants, strict same-resource FIFO (priority is a stamp, aging is recorded),
a benchmark reservation class, and memory admission with explicit
unknown/allocation-failure states.

PREREGISTRATION:
- STATEMENT: a fair, deadlock-free resource scheduler can be layered onto
  the existing five-slot controller without touching schema-1 semantics.
- PREDICTION:
  (1) a grouped request for rtx4090+dyad_eye+memory grants atomically and
      never partially;
  (2) same-resource FIFO holds: a later high-priority request never jumps an
      earlier request that wants the same resource;
  (3) benchmark class requires an empty GPU and, while held, excludes every
      other GPU-family use;
  (4) memory admission refuses over-budget grants (allocation_failed) and
      admits declared/unknown memory states explicitly;
  (5) legacy resource_acquire/release still work unchanged;
  (6) pending requests die with their owner (fail) and task (recover).
- FALSIFIER: a partial grouped grant, a queue-jump on the same resource,
  a benchmark coexisting with interactive GPU use, an over-budget memory
  grant, or a zombie request surviving its owner's recorded failure.
"""
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import Control, Refusal

BASE = 'a' * 40


class ResourceSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.c = Control(self.root / 'state.sqlite', 'SUP', 'ENR',
                         self.root / 'slots', memory_budget_mb=8192)
        self.tok = {}
        for aid in ('lead', 'worker', 'other'):
            self.tok[aid] = self.c.call('enroll', 'ENR', agent=aid,
                                        label=aid)['result']['session_token']
            self.c.call('qualify', 'SUP', agent=aid, capabilities=['cpu', 'gpu'],
                        max_tasks=3, can_lead=aid == 'lead', rank=5 if aid == 'lead' else 1,
                        evidence='resource suite fixture')
        self.c.call('offer_lead', self.tok['lead'], epoch=0,
                    checkpoint='ready; no foreign work')
        self.c.call('elect', 'SUP')

    def tearDown(self):
        self.tmp.cleanup()

    def snap(self):
        return self.c.call('snapshot', 'SUP')['result']

    def call(self, op, actor='lead', **p):
        return self.c.call(op, self.tok.get(actor, actor), **p)['result']

    def task(self, tid, **kw):
        p = dict(task=tid, epoch=self.snap()['epoch'], base=BASE,
                 scopes=['docs/evidence/sched-' + tid] if not kw.get('scopes') else kw.pop('scopes'),
                 packet='statement / prediction / falsifier', kind='worker')
        p.update(kw)
        return self.call('create_task', **p)

    def claim(self, tid, actor):
        return self.call('claim', actor, task=tid)

    def request(self, tid, actor, wants, priority=5, generation=None):
        g = generation if generation is not None else self.snap()['tasks'][tid]['generation']
        return self.call('resource_request', actor, task=tid, generation=g,
                         wants=wants, priority=priority)

    # (1) grouped all-or-nothing grant --------------------------------
    def test_grouped_grant_is_atomic(self):
        self.task('g')
        self.claim('g', 'worker')
        r = self.request('g', 'worker', [
            {'name': 'rtx4090', 'class': 'gpu_functionality'},
            {'name': 'dyad_eye'},
            {'name': 'memory', 'memory_mb': 2048}])
        self.assertTrue(r['granted'], r)
        res = self.snap()['resources']
        g = res['rtx4090']; self.assertEqual(g['task'], 'g')
        self.assertEqual(g['generation'], 1)
        self.assertIn('dyad_eye', res)
        self.assertTrue(any(k.startswith('memory.') for k in res))
        mem_keys = [k for k in res if k.startswith('memory.')]
        self.assertEqual(res[mem_keys[0]]['memory_mb'], 2048)
        self.assertEqual(self.snap()['memory']['admitted_mb'], 2048)
        # all entries carry generation 1 — nothing partial, nothing stale
        self.assertEqual(len(res), 3)

    def test_grouped_grant_never_partial_on_conflict(self):
        self.task('a'); self.task('b')
        self.claim('a', 'worker'); self.claim('b', 'other')
        self.request('a', 'worker', [{'name': 'rtx4090'}])
        r = self.request('b', 'other', [{'name': 'rtx4090'},
                                        {'name': 'memory', 'memory_mb': 1024}])
        # rtx4090 held by a -> whole group refused; memory must NOT be granted
        self.assertFalse(r['granted'])
        self.assertEqual(r['stalled'], 'contended:rtx4090')
        self.assertIn('rtx4090', self.snap()['resources'])
        self.assertFalse(any(k.startswith('memory.') for k in self.snap()['resources']))

    # (2) strict same-resource FIFO -----------------------------------
    def test_same_resource_fifo_priority_is_a_stamp(self):
        self.task('p1'); self.task('p2')
        self.claim('p1', 'worker'); self.claim('p2', 'other')
        self.task('h'); self.claim('h', 'lead')
        self.request('h', 'lead', [{'name': 'rtx4090'}])
        r1 = self.request('p1', 'worker', [{'name': 'rtx4090'}], priority=1)
        r2 = self.request('p2', 'other', [{'name': 'rtx4090'}], priority=9)
        self.assertFalse(r1['granted']); self.assertFalse(r2['granted'])
        self.assertEqual(r2['enqueued_revision'] > r1['enqueued_revision'], True)
        # release the holder: queues must serve p1 (FIFO), NOT p2 despite priority 9
        self.call('resource_release', 'lead', task='h',
                  generation=self.snap()['tasks']['h']['generation'],
                  resource='rtx4090', evidence='drained')
        res = self.snap()['resources']
        self.assertEqual(res['rtx4090']['task'], 'p1',
                         'a later high-priority request must not jump FIFO')
        self.assertEqual(self.snap()['tasks']['p1']['generation'],
                         res['rtx4090']['generation'])
        # p2 still queued, with recorded waiting (aging) time
        q = self.call('resource_queue', 'other', task='p2',
                      generation=self.snap()['tasks']['p2']['generation'])
        self.assertEqual(len(q['queued']), 1)
        self.assertGreaterEqual(q['queued'][0]['waiting_revisions'], 0)

    def test_different_resources_can_progress_independently(self):
        self.task('a'); self.task('b')
        self.claim('a', 'worker'); self.claim('b', 'other')
        self.request('a', 'worker', [{'name': 'rtx4090'}])
        r = self.request('b', 'other', [{'name': 'memory', 'memory_mb': 4096}])
        self.assertTrue(r['granted'], 'memory is independent of the GPU')

    # (3) benchmark reservation class --------------------------------
    def test_benchmark_class_excludes_all_gpu_use(self):
        self.task('bench'); self.claim('bench', 'worker')
        self.task('gpu'); self.claim('gpu', 'other')
        self.request('gpu', 'other', [{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        r = self.request('bench', 'worker', [{'name': 'rtx4090', 'class': 'gpu_benchmark'}])
        self.assertFalse(r['granted'])
        self.assertEqual(r['stalled'], 'benchmark_exclusive:gpu_held')
        # clear the interactive holder -> the PENDING benchmark grants via promotion
        self.call('resource_release', 'other', task='gpu',
                  generation=self.snap()['tasks']['gpu']['generation'],
                  resource='rtx4090', evidence='drained')
        res = self.snap()['resources']
        self.assertEqual(res['rtx4090']['task'], 'bench')
        self.assertEqual(res['rtx4090']['class'], 'gpu_benchmark')
        # interactive GPU blocked while the benchmark holds the GPU
        rr = self.request('gpu', 'other', [{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        self.assertFalse(rr['granted'], 'interactive GPU blocked while benchmark holds GPU')
        self.assertEqual(rr['stalled'], 'benchmark_exclusive:gpu_held')

    def test_benchmark_requires_empty_gpu_even_from_same_task(self):
        self.task('mix'); self.claim('mix', 'worker')
        self.request('mix', 'worker', [{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        r = self.request('mix', 'worker', [{'name': 'rtx4090', 'class': 'gpu_benchmark'}])
        self.assertFalse(r['granted'], 'benchmark must not coexist with a functionality hold')

    # (4) memory admission --------------------------------------------
    def test_memory_admission_refuses_over_budget(self):
        self.task('m1'); self.claim('m1', 'worker')
        self.task('m2'); self.claim('m2', 'other')
        self.request('m1', 'worker', [{'name': 'memory', 'memory_mb': 6000}])
        r = self.request('m2', 'other', [{'name': 'memory', 'memory_mb': 3000}])
        self.assertFalse(r['granted'])
        self.assertTrue(r['allocation_failed'])
        self.assertEqual(r['stalled'], 'memory_allocation_refused')
        # freeing m1's memory admits m2 (retry via a fresh request)
        self.call('resource_release', 'worker', task='m1',
                  generation=self.snap()['tasks']['m1']['generation'],
                  resource='memory', evidence='drained')
        r = self.request('m2', 'other', [{'name': 'memory', 'memory_mb': 3000}])
        self.assertTrue(r['granted'])

    def test_unknown_memory_is_explicit_state(self):
        self.task('u'); self.claim('u', 'worker')
        r = self.request('u', 'worker', [{'name': 'rtx4090'},
                                         {'name': 'memory', 'memory_mb': None}])
        self.assertTrue(r['granted'], 'unknown memory is admitted, not refused')
        g = self.snap()['resources']
        self.assertIn('rtx4090', g)
        self.assertFalse(any(k.startswith('memory.') for k in g),
                         'unknown memory is not charged against the budget')

    def test_invalid_wants_refused(self):
        self.task('bad'); self.claim('bad', 'worker')
        # unknown resource name and duplicate wants are refused; an omitted
        # memory_mb is the EXPLICIT unknown state and stays legal.
        for wants in ([{'name': 'nope'}],
                      [{'name': 'rtx4090'}, {'name': 'rtx4090'}]):
            with self.assertRaises(Refusal):
                self.request('bad', 'worker', wants)
        self.assertEqual([r for r in self.snap()['resource_queues'] if not r['served']], [])

    # (5) legacy path unchanged ---------------------------------------
    def test_legacy_acquire_release_unchanged(self):
        self.task('leg'); self.claim('leg', 'worker')
        args = dict(task='leg', generation=self.snap()['tasks']['leg']['generation'])
        self.call('resource_acquire', 'worker', resource='rtx4090', **args)
        with self.assertRaises(Refusal):
            self.call('resource_acquire', 'other', resource='dyad_eye',
                      task='leg', generation=args['generation'])
        self.call('resource_acquire', 'worker', resource='dyad_eye', **args)
        with self.assertRaises(Refusal):
            self.call('resource_release', 'worker', resource='rtx4090', evidence='x', **args)
        self.call('resource_release', 'worker', resource='dyad_eye', evidence='x', **args)
        self.call('resource_release', 'worker', resource='rtx4090', evidence='x', **args)
        self.assertEqual(self.snap()['resources'], {})

    # (6) pending requests die with owner and with recover -------------
    def test_pending_requests_vanish_on_fail_and_recover(self):
        self.task('h'); self.claim('h', 'lead')
        self.task('v'); self.claim('v', 'worker')
        self.request('h', 'lead', [{'name': 'rtx4090'}])
        self.request('v', 'worker', [{'name': 'rtx4090'}])
        q = [r for r in self.snap()['resource_queues'] if not r['served']]
        self.assertEqual(len(q), 1)  # only v is pending (h granted)
        self.c.call('fail', 'SUP', agent='worker', reason='PROCESS_EXIT',
                    evidence='gone')
        self.assertEqual([r for r in self.snap()['resource_queues']
                          if r['task'] == 'v' and not r['served']], [])
        # a live agent works on after fail; recovery-generation bump drops requeues
        self.task('g2'); self.claim('g2', 'other')
        self.request('g2', 'other', [{'name': 'rtx4090'}])
        self.task('g3'); self.claim('g3', 'other')
        self.request('g3', 'other', [{'name': 'memory', 'memory_mb': 1000}])
        # fail the live agent -> tasks held; recover g2 (no resource hold) drops its pending
        self.c.call('fail', 'SUP', agent='other', reason='PROCESS_EXIT',
                    evidence='gone')
        self.c.call('recover', 'SUP', task='g2',
                    evidence='writer stopped; worktree preserved')
        self.assertEqual([r for r in self.snap()['resource_queues']
                          if r['task'] == 'g2' and not r['served']], [])

    def test_revoke_pending(self):
        self.task('h'); self.claim('h', 'lead')
        self.task('x'); self.claim('x', 'worker')
        self.request('h', 'lead', [{'name': 'rtx4090'}])
        self.request('x', 'worker', [{'name': 'rtx4090'}])
        r = self.call('resource_revoke_pending', 'worker', task='x',
                      generation=self.snap()['tasks']['x']['generation'])
        self.assertEqual(r['revoked'], 1)
        self.assertEqual([r for r in self.snap()['resource_queues']
                          if r['task'] == 'x' and not r['served']], [])


if __name__ == '__main__':
    unittest.main(verbosity=2)