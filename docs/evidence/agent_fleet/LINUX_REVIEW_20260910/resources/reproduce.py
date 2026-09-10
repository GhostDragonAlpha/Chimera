"""Offline defect reproductions; assertions confirm current behavior, not acceptance."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/agent_fleet'))
from control import Control

class Reproductions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='fleet-resource-review-')
        root = Path(self.tmp.name)
        self.c = Control(root/'review.sqlite', 'isolated-sup', 'isolated-enr', root/'slots', memory_budget_mb=1024)
        self.tokens = {}
        for a in ['lead', 'a', 'b', 'c']:
            self.tokens[a] = self.c.call('enroll', 'isolated-enr', agent=a, label=a)['result']['session_token']
            self.c.call('qualify', 'isolated-sup', agent=a, capabilities=['cpu', 'gpu'], max_tasks=1, can_lead=a=='lead', evidence='isolated review fixture')
        self.call('offer_lead', 'lead', epoch=0, checkpoint='isolated review')
        self.c.call('elect', 'isolated-sup')
        for a in ['a', 'b', 'c']:
            self.call('create_task', 'lead', epoch=1, task=a, base='a'*40, scopes=['review/'+a], packet='preregistered in PREREGISTRATION.md', kind='worker')
            self.call('claim', a, task=a)
    def tearDown(self):
        self.tmp.cleanup()
    def call(self, op, actor, **p):
        return self.c.call(op, self.tokens[actor], **p)['result']
    def op(self, op, a, **p):
        return self.call(op, a, task=a, generation=1, **p)
    def request(self, a, *wants):
        return self.op('resource_request', a, wants=list(wants))
    def snap(self):
        return self.c.call('snapshot', 'isolated-sup')['result']
    def evidence(self, **details):
        print(json.dumps({'case': self.id().split('.')[-1], **details}, sort_keys=True))
    def test_chained_holder_overwritten(self):
        self.request('a', {'name':'rtx4090'}, {'name':'engine_demo'})
        self.op('resource_release', 'a', resource='rtx4090', evidence='GPU drained; engine_demo remains reserved')
        before = self.snap()['resources']['engine_demo']
        result = self.request('b', {'name':'rtx4090'}, {'name':'engine_demo'})
        after = self.snap()['resources']['engine_demo']
        self.assertTrue(result['granted'])
        self.assertEqual(before['task'], 'a')
        self.assertEqual(after['task'], 'b')
        self.evidence(before=before, after=after, granted=result['granted'])
    def test_fifo_bypass_on_memory_blocked_group(self):
        self.request('a', {'name':'memory', 'memory_mb':1024})
        older = self.request('b', {'name':'rtx4090'}, {'name':'memory', 'memory_mb':1024})
        newer = self.request('c', {'name':'rtx4090'})
        self.assertFalse(older['granted'])
        self.assertTrue(newer['granted'])
        self.assertEqual(self.snap()['resources']['rtx4090']['task'], 'c')
        self.evidence(older_stalled=older['stalled'], later_granted=newer['granted'], gpu_owner='c')
    def test_memory_total_stale_after_release(self):
        self.request('a', {'name':'memory', 'memory_mb':1024})
        self.op('resource_release', 'a', resource='memory', evidence='isolated simulated drained allocation')
        s=self.snap()
        actual=sum(r.get('memory_mb') or 0 for r in s['resources'].values())
        self.assertEqual(actual, 0)
        self.assertEqual(s['memory']['admitted_mb'], 1024)
        self.evidence(reported=s['memory']['admitted_mb'], actual=actual)
    def test_split_acquisition_cycle(self):
        self.request('a', {'name':'rtx4090'})
        self.request('b', {'name':'memory', 'memory_mb':1024})
        self.request('a', {'name':'memory', 'memory_mb':1024})
        self.request('b', {'name':'rtx4090'})
        for _ in range(2):
            self.op('resource_revoke_pending', 'c')
        q=[q for q in self.snap()['resource_queues'] if not q['served']]
        self.assertEqual({q['task'] for q in q}, {'a','b'})
        self.evidence(pending=[{'task':q['task'], 'stalled':q['stalled']} for q in q])
    def test_benchmark_class_downgrade_without_drain(self):
        self.request('a', {'name':'rtx4090', 'class':'gpu_benchmark'})
        result=self.request('a', {'name':'rtx4090', 'class':'gpu_functionality'})
        self.assertTrue(result['granted'])
        self.assertEqual(self.snap()['resources']['rtx4090']['class'], 'gpu_functionality')
        self.evidence(granted=result['granted'], class_after='gpu_functionality', drain_calls=0)
    def test_positive_memory_capacity_and_auto_promotion(self):
        self.request('a', {'name':'memory', 'memory_mb':1024})
        pending=self.request('b', {'name':'memory', 'memory_mb':1})
        self.assertFalse(pending['granted'])
        self.op('resource_release', 'a', resource='memory', evidence='isolated simulated drained allocation')
        s=self.snap()
        q=next(q for q in s['resource_queues'] if q['id']==pending['id'])
        self.assertTrue(q['granted'])
        self.assertEqual(sum(r.get('memory_mb') or 0 for r in s['resources'].values()),1)
        self.evidence(auto_promoted=q['granted'], admitted_mb=s['memory']['admitted_mb'])

if __name__=='__main__':
    unittest.main(verbosity=2)
