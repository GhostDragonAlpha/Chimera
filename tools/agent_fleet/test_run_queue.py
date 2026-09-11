import unittest

from tools.agent_fleet.run_queue import QueueRefusal, RunQueue


class RunQueueTests(unittest.TestCase):
    def test_priority_and_dependency_dispatch(self):
        q = RunQueue(); q.enqueue("base", priority=1); q.enqueue("child", dependencies=["base"], priority=9); q.enqueue("peer", priority=5)
        picked = q.dispatch(owner="a", capacity=2, now=0, lease_seconds=10)
        self.assertEqual([r.task for r in picked], ["peer", "base"])
        q.submit_review("base", owner="a", generation=1, now=1, head="h", evidence="test")
        q.acknowledge_integration("base", head="h")
        picked = q.dispatch(owner="b", capacity=1, now=1, lease_seconds=10)
        self.assertEqual([r.task for r in picked], ["child"])

    def test_review_releases_capacity_but_requires_exact_integration_head(self):
        q = RunQueue(); q.enqueue("one"); q.enqueue("two")
        run = q.dispatch(owner="a", capacity=1, now=0, lease_seconds=10)[0]
        q.submit_review("one", owner="a", generation=run.generation, now=1, head="abc", evidence="independent")
        self.assertEqual(q.dispatch(owner="a", capacity=1, now=1, lease_seconds=10)[0].task, "two")
        with self.assertRaisesRegex(QueueRefusal, "review_head_mismatch"):
            q.acknowledge_integration("one", head="changed")

    def test_expired_lease_holds_owner_until_evidenced_recovery(self):
        q = RunQueue(); q.enqueue("one")
        run = q.dispatch(owner="a", capacity=1, now=0, lease_seconds=3)[0]
        expired = q.expire(now=3)
        self.assertEqual([r.task for r in expired], ["one"])
        self.assertEqual((expired[0].state, expired[0].owner, expired[0].generation),
                         ("RECOVERY_HOLD", "a", 1))
        with self.assertRaisesRegex(QueueRefusal, "task_not_running"):
            q.heartbeat("one", owner="a", generation=run.generation, now=3, lease_seconds=3)
        # The former expectation dispatched owner b immediately after timeout.
        # That is unsafe because timeout is not evidence that owner a drained.
        self.assertEqual(q.dispatch(owner="b", capacity=1, now=4, lease_seconds=3), [])
        with self.assertRaisesRegex(QueueRefusal, "preserved_and_drained_evidence_required"):
            q.recover("one", preserved_evidence="workspace preserved", drained_evidence="")
        recovered = q.recover("one", preserved_evidence="workspace preserved",
                              drained_evidence="writer and runtime stopped")
        self.assertEqual(recovered.generation, 1)
        fresh = q.dispatch(owner="b", capacity=1, now=4, lease_seconds=3)[0]
        self.assertEqual(fresh.generation, 2)

    def test_no_fabricated_dependency_or_duplicate_dispatch(self):
        q = RunQueue(); q.enqueue("child", dependencies=["missing"])
        self.assertEqual(q.dispatch(owner="a", capacity=2, now=0, lease_seconds=1), [])
        with self.assertRaisesRegex(QueueRefusal, "duplicate_or_empty_task"):
            q.enqueue("child")

    def test_expired_review_and_nonfinite_lease_are_refused(self):
        q = RunQueue(); q.enqueue("one")
        with self.assertRaisesRegex(QueueRefusal, "invalid_dispatch_parameters"):
            q.dispatch(owner="a", capacity=1, now=0, lease_seconds=float("nan"))
        run = q.dispatch(owner="a", capacity=1, now=0, lease_seconds=2)[0]
        with self.assertRaisesRegex(QueueRefusal, "lease_expired"):
            q.submit_review("one", owner="a", generation=run.generation, now=2, head="h", evidence="e")

    def test_numeric_boundaries_are_refused(self):
        q = RunQueue(); q.enqueue("one")
        for capacity in (True, 1.5, -1):
            with self.subTest(capacity=capacity), self.assertRaisesRegex(QueueRefusal, "invalid_dispatch_parameters"):
                q.dispatch(owner="a", capacity=capacity, now=0, lease_seconds=1)
        for now, duration in ((float("inf"), 1), (0, float("nan")), (1e308, 1e308)):
            with self.subTest(now=now, duration=duration), self.assertRaisesRegex(QueueRefusal, "invalid_dispatch_parameters"):
                q.dispatch(owner="a", capacity=1, now=now, lease_seconds=duration)
        for now in (float("nan"), float("inf"), True):
            with self.subTest(expiry=now), self.assertRaisesRegex(QueueRefusal, "invalid_expiry_time"):
                q.expire(now=now)
        run = q.dispatch(owner="a", capacity=1, now=0, lease_seconds=2)[0]
        with self.assertRaisesRegex(QueueRefusal, "nonfinite_lease_parameters"):
            q.heartbeat("one", owner="a", generation=run.generation,
                        now=True, lease_seconds=1)
        with self.assertRaisesRegex(QueueRefusal, "lease_expired"):
            q.submit_review("one", owner="a", generation=run.generation,
                            now=True, head="h", evidence="e")

    def test_heartbeat_rejects_overflow_without_mutating_lease(self):
        q = RunQueue(); q.enqueue("one")
        run = q.dispatch(owner="a", capacity=1, now=0, lease_seconds=10)[0]
        with self.assertRaisesRegex(QueueRefusal, "lease_overflow"):
            q.heartbeat("one", owner="a", generation=run.generation,
                        now=1e308, lease_seconds=1e308)
        self.assertEqual(q.expire(now=9), [])

    def test_returned_runs_are_defensive_views(self):
        q = RunQueue(); q.enqueue("one")
        run = q.dispatch(owner="a", capacity=1, now=0, lease_seconds=2)[0]
        run.state = "INTEGRATED"; run.history.append("forged")
        self.assertEqual(q.snapshot()[0]["state"], "RUNNING")

        expired = q.expire(now=2)
        expired[0].state = "READY"; expired[0].owner = None
        expired[0].history.append("forged expiry")
        held = q.snapshot()[0]
        self.assertEqual((held["state"], held["owner"]), ("RECOVERY_HOLD", "a"))
        with self.assertRaisesRegex(QueueRefusal, "task_not_running"):
            q.heartbeat("one", owner="a", generation=1, now=1, lease_seconds=1)
        recovered = q.recover("one", preserved_evidence="files retained",
                              drained_evidence="process stopped")
        recovered.state = "INTEGRATED"; recovered.history.append("forged recovery")
        self.assertEqual(q.snapshot()[0]["state"], "READY")


if __name__ == "__main__":
    unittest.main()
