import unittest

from tools.agent_fleet.run_queue import QueueRefusal, RunQueue


class RunQueueTests(unittest.TestCase):
    def test_priority_and_dependency_dispatch(self):
        q = RunQueue(); q.enqueue("base", priority=1); q.enqueue("child", dependencies=["base"], priority=9); q.enqueue("peer", priority=5)
        picked = q.dispatch(owner="a", capacity=2, now=0, lease_seconds=10)
        self.assertEqual([r.task for r in picked], ["peer", "base"])
        q.submit_review("base", owner="a", generation=1, head="h", evidence="test")
        q.acknowledge_integration("base", head="h")
        picked = q.dispatch(owner="b", capacity=1, now=1, lease_seconds=10)
        self.assertEqual([r.task for r in picked], ["child"])

    def test_review_releases_capacity_but_requires_exact_integration_head(self):
        q = RunQueue(); q.enqueue("one"); q.enqueue("two")
        run = q.dispatch(owner="a", capacity=1, now=0, lease_seconds=10)[0]
        q.submit_review("one", owner="a", generation=run.generation, head="abc", evidence="independent")
        self.assertEqual(q.dispatch(owner="a", capacity=1, now=1, lease_seconds=10)[0].task, "two")
        with self.assertRaisesRegex(QueueRefusal, "review_head_mismatch"):
            q.acknowledge_integration("one", head="changed")

    def test_expired_lease_requeues_and_fences_old_worker(self):
        q = RunQueue(); q.enqueue("one")
        run = q.dispatch(owner="a", capacity=1, now=0, lease_seconds=3)[0]
        self.assertEqual([r.task for r in q.expire(now=3)], ["one"])
        with self.assertRaisesRegex(QueueRefusal, "task_not_running"):
            q.heartbeat("one", owner="a", generation=run.generation, now=3, lease_seconds=3)
        fresh = q.dispatch(owner="b", capacity=1, now=4, lease_seconds=3)[0]
        self.assertEqual(fresh.generation, 2)

    def test_no_fabricated_dependency_or_duplicate_dispatch(self):
        q = RunQueue(); q.enqueue("child", dependencies=["missing"])
        self.assertEqual(q.dispatch(owner="a", capacity=2, now=0, lease_seconds=1), [])
        with self.assertRaisesRegex(QueueRefusal, "duplicate_or_empty_task"):
            q.enqueue("child")


if __name__ == "__main__":
    unittest.main()
