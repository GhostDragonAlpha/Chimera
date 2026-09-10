"""Desired invariants for the independently reproduced resource lifecycle defects.

Preregistered in docs/evidence/agent_fleet/RESOURCE_FIX_20260910/PREREGISTRATION.md.
All fixtures are temporary registries and loopback services, never real GPUs.
"""
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import test_resources as fixtures
from control import Refusal
from service import Server


class ResourceLifecycleTests(unittest.TestCase):
    setUp = fixtures.ResourceSchedulerTests.setUp
    tearDown = fixtures.ResourceSchedulerTests.tearDown
    snap = fixtures.ResourceSchedulerTests.snap
    call = fixtures.ResourceSchedulerTests.call
    task = fixtures.ResourceSchedulerTests.task
    claim = fixtures.ResourceSchedulerTests.claim
    request = fixtures.ResourceSchedulerTests.request

    def prepare(self):
        self.task('a'); self.claim('a', 'worker')
        self.task('b'); self.claim('b', 'other')

    def release(self, task, actor, resource):
        return self.call('resource_release', actor, task=task, generation=1,
                         resource=resource, evidence='synthetic fixture drained')

    def test_gpu_release_preserves_engine_owner_until_drained(self):
        self.prepare()
        self.request('a', 'worker', [{'name': 'rtx4090'}, {'name': 'engine_demo'}])
        before = self.snap()
        with self.assertRaisesRegex(Refusal, 'release_engine_first'):
            self.release('a', 'worker', 'rtx4090')
        self.assertEqual(self.snap(), before)
        pending = self.request('b', 'other', [{'name': 'rtx4090'}, {'name': 'engine_demo'}])
        self.assertFalse(pending['granted'])
        self.release('a', 'worker', 'engine_demo')
        self.release('a', 'worker', 'rtx4090')
        self.assertEqual(self.snap()['resources']['engine_demo']['task'], 'b')

    def test_supervisor_clear_requires_engine_drain(self):
        self.prepare()
        self.request('a', 'worker', [{'name': 'rtx4090'}, {'name': 'engine_demo'}])
        with self.assertRaisesRegex(Refusal, 'release_engine_first'):
            self.call('resource_clear', 'SUP', resource='rtx4090', evidence='fixture')
        self.call('resource_clear', 'SUP', resource='engine_demo', evidence='fixture')
        self.call('resource_clear', 'SUP', resource='rtx4090', evidence='fixture')
        self.assertEqual(self.snap()['resources'], {})

    def test_legacy_engine_requires_parent(self):
        self.prepare()
        with self.assertRaisesRegex(Refusal, 'engine_requires_gpu_reservation'):
            self.call('resource_acquire', 'worker', task='a', generation=1, resource='engine_demo')
        self.call('resource_acquire', 'worker', task='a', generation=1, resource='rtx4090')
        self.call('resource_acquire', 'worker', task='a', generation=1, resource='engine_demo')
        self.assertEqual(self.snap()['resources']['engine_demo']['task'], 'a')

    def test_stale_registry_hold_cannot_be_overwritten(self):
        self.prepare()
        # Persist the exact old-source state (GPU released, child retained).
        self.request('a', 'worker', [{'name': 'rtx4090'}, {'name': 'engine_demo'}])
        con = self.c.connect()
        try:
            state = json.loads(con.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            del state['resources']['rtx4090']
            con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(state),))
        finally:
            con.close()
        r = self.request('b', 'other', [{'name': 'rtx4090'}, {'name': 'engine_demo'}])
        self.assertFalse(r['granted'])
        gpu_only = self.request('b', 'other', [{'name': 'rtx4090'}])
        self.assertFalse(gpu_only['granted'])
        with self.assertRaisesRegex(Refusal, 'retained_gpu_child'):
            self.call('resource_acquire', 'other', task='b', generation=1, resource='rtx4090')
        self.assertEqual(self.snap()['resources']['engine_demo']['task'], 'a')
        self.assertNotIn('rtx4090', self.snap()['resources'])

    def test_same_owner_benchmark_class_requires_release(self):
        self.prepare()
        self.request('a', 'worker', [{'name': 'rtx4090', 'class': 'gpu_benchmark'}])
        before = dict(self.snap()['resources']['rtx4090'])
        r = self.request('a', 'worker', [{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        self.assertFalse(r['granted'])
        self.assertTrue(r['served'])
        self.assertEqual(r['dropped_reason'], 'release_required')
        self.assertEqual(self.snap()['resources']['rtx4090'], before)

    def test_memory_total_release_and_clear(self):
        self.prepare()
        self.request('a', 'worker', [{'name': 'memory', 'memory_mb': 1024}])
        self.release('a', 'worker', 'memory')
        self.assertEqual(self.snap()['memory']['admitted_mb'], 0)
        self.request('a', 'worker', [{'name': 'memory', 'memory_mb': 1024}])
        key = next(iter(self.snap()['resources']))
        self.call('resource_clear', 'SUP', resource=key, evidence='fixture')
        self.assertEqual(self.snap()['memory']['admitted_mb'], 0)

    def test_split_acquisition_is_terminal_not_pending(self):
        self.prepare()
        self.request('a', 'worker', [{'name': 'rtx4090'}])
        self.request('b', 'other', [{'name': 'memory', 'memory_mb': 8192}])
        for tid, actor, wants in [('a', 'worker', [{'name': 'memory', 'memory_mb': 8192}]),
                                  ('b', 'other', [{'name': 'rtx4090'}])]:
            r = self.request(tid, actor, wants)
            self.assertFalse(r['granted'])
            self.assertTrue(r['served'])
            self.assertEqual(r['dropped_reason'], 'release_required')
        self.assertFalse([q for q in self.snap()['resource_queues'] if not q['served']])
        self.assertEqual(self.snap()['resources']['rtx4090']['task'], 'a')
        self.release('a', 'worker', 'rtx4090')
        self.release('b', 'other', 'memory')
        r = self.request('a', 'worker', [{'name': 'rtx4090'}, {'name': 'memory', 'memory_mb': 8192}])
        self.assertTrue(r['granted'])

    def test_available_child_acquisition_still_works(self):
        self.prepare()
        self.request('a', 'worker', [{'name': 'rtx4090'}])
        r = self.request('a', 'worker', [{'name': 'dyad_eye'}, {'name': 'engine_demo'}])
        self.assertTrue(r['granted'])
        self.assertEqual(len(self.snap()['resources']), 3)

    def test_old_pending_holder_is_terminal_on_promotion(self):
        self.prepare()
        self.request('a', 'worker', [{'name': 'rtx4090'}])
        self.request('b', 'other', [{'name': 'memory', 'memory_mb': 8192}])
        request = self.request('a', 'worker', [{'name': 'memory', 'memory_mb': 8192}])
        # A pre-repair registry kept this holder's blocked request pending.
        con = self.c.connect()
        try:
            state = json.loads(con.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            queued = next(q for q in state['resource_queues'] if q['id'] == request['id'])
            queued.update(served=False, dropped_reason=None)
            con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(state),))
        finally:
            con.close()
        self.task('c'); self.claim('c', 'lead')
        self.call('resource_revoke_pending', 'lead', task='c', generation=1)
        queued = next(q for q in self.snap()['resource_queues'] if q['id'] == request['id'])
        self.assertTrue(queued['served'])
        self.assertEqual(queued['dropped_reason'], 'release_required')
        self.assertEqual(self.snap()['resources']['rtx4090']['task'], 'a')

    def test_nonholder_stays_queued_and_auto_promotes(self):
        self.prepare()
        self.request('a', 'worker', [{'name': 'memory', 'memory_mb': 8192}])
        r = self.request('b', 'other', [{'name': 'memory', 'memory_mb': 1}])
        self.assertFalse(r['served'])
        self.release('a', 'worker', 'memory')
        q = next(q for q in self.snap()['resource_queues'] if q['id'] == r['id'])
        self.assertTrue(q['granted'])
        self.assertEqual(self.snap()['memory']['admitted_mb'], 1)

    def test_malformed_resource_returns_json_and_preserves_state(self):
        self.prepare()
        server = Server(('127.0.0.1', 0), self.c)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            before = self.snap()
            for value in (None, 42, [], {}):
                body = {'operation': 'resource_acquire', 'arguments':
                        {'task': 'a', 'generation': 1, 'resource': value}}
                req = Request(f'http://127.0.0.1:{server.server_port}/v1/action',
                              data=json.dumps(body).encode(),
                              headers={'Authorization': 'Bearer ' + self.tok['worker']})
                with self.assertRaises(HTTPError) as caught:
                    urlopen(req, timeout=3)
                with caught.exception as response:
                    self.assertEqual(response.code, 409)
                    self.assertEqual(json.load(response)['error'], 'invalid_resource_name')
                self.assertEqual(self.snap(), before)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_legacy_memory_has_named_refusal(self):
        self.prepare()
        with self.assertRaisesRegex(Refusal, 'use_resource_request_for_memory'):
            self.call('resource_acquire', 'worker', task='a', generation=1, resource='memory')


if __name__ == '__main__':
    unittest.main(verbosity=2)
