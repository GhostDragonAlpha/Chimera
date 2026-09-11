import unittest

from tools.agent_fleet.run_queue_worker import WorkerQueue


class WorkerQueueTests(unittest.TestCase):
    def test_claim_race_advances_to_next_ready_task(self):
        calls = []
        snapshot = {"result": {"tasks": {
            "a": {"id": "a", "state": "READY", "priority": 9},
            "b": {"id": "b", "state": "READY", "priority": 1},
        }}}

        def call(op, args):
            calls.append((op, args))
            if op == "snapshot": return snapshot
            if args["task"] == "a": raise ValueError("task_not_ready")
            return {"result": {"state": "RUNNING", "generation": 1}}

        got = WorkerQueue(call).claim_once()
        self.assertEqual(got["task"], "b")
        self.assertEqual([x[1]["task"] for x in calls[1:]], ["a", "b"])

    def test_empty_queue_does_not_fabricate_work(self):
        calls = []
        got = WorkerQueue(lambda op, args: calls.append((op, args)) or {"result": {"tasks": {}}}).claim_once()
        self.assertIsNone(got)
        self.assertEqual(calls[0][0], "snapshot")

    def test_loop_reads_fresh_snapshot_each_cycle(self):
        snapshots = iter([
            {"result": {"tasks": {"a": {"id": "a", "state": "READY"}}}},
            {"result": {"tasks": {"b": {"id": "b", "state": "READY"}}}},
        ])
        seen = []

        def call(op, args):
            if op == "snapshot": return next(snapshots)
            seen.append(args["task"]); return {"result": {"state": "RUNNING"}}

        WorkerQueue(call, sleep=lambda _: None).run_forever(max_cycles=2)
        self.assertEqual(seen, ["a", "b"])

    def test_no_secret_or_whole_response_is_required(self):
        result = WorkerQueue(lambda op, args: {"result": {"tasks": {"a": {"id": "a", "state": "READY"}}}} if op == "snapshot" else {"result": {"token": "must-not-be-used"}}).claim_once()
        self.assertEqual(result["task"], "a")
        self.assertNotIn("token", result)

    def test_authentication_and_transport_failures_are_not_masked(self):
        def call(op, args):
            if op == "snapshot":
                return {"result": {"tasks": {"a": {"id": "a", "state": "READY"}}}}
            raise ValueError('{"error":"session_revoked"}')
        with self.assertRaisesRegex(ValueError, "session_revoked"):
            WorkerQueue(call).claim_once()


if __name__ == "__main__":
    unittest.main()
