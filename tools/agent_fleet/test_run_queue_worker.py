import unittest

from tools.agent_fleet.run_queue_worker import WorkerQueue

def worker(call, **kwargs):
    def authenticated(op, args):
        result = call(op, args)
        if op == 'snapshot':
            result['result']['agents'] = {'worker': {'alive': True, 'qualified': True}}
        return result
    return WorkerQueue(authenticated, agent='worker', **kwargs)


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

        got = worker(call).claim_once()
        self.assertEqual(got["task"], "b")
        self.assertEqual([x[1]["task"] for x in calls[1:]], ["a", "b"])

    def test_empty_queue_does_not_fabricate_work(self):
        calls = []
        got = worker(lambda op, args: calls.append((op, args)) or {"result": {"tasks": {}}}).claim_once()
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

        worker(call, sleep=lambda _: None).run_forever(max_cycles=2, on_assignment=lambda task: None)
        self.assertEqual(seen, ["a", "b"])

    def test_no_secret_or_whole_response_is_required(self):
        result = worker(lambda op, args: {"result": {"tasks": {"a": {"id": "a", "state": "READY"}}}} if op == "snapshot" else {"result": {"state": "RUNNING"}}).claim_once()
        self.assertEqual(result["task"], "a")
        self.assertNotIn("token", result)

    def test_authentication_and_transport_failures_are_not_masked(self):
        def call(op, args):
            if op == "snapshot":
                return {"result": {"tasks": {"a": {"id": "a", "state": "READY"}}}}
            raise ValueError('{"error":"session_revoked"}')
        with self.assertRaisesRegex(ValueError, "session_revoked"):
            worker(call).claim_once()

    def test_no_executor_refuses_before_claim(self):
        calls = []
        with self.assertRaisesRegex(ValueError, 'executor_required_before_claim'):
            WorkerQueue(lambda *args: calls.append(args), agent='worker').run_forever(max_cycles=1)
        self.assertEqual(calls, [])

    def test_owned_work_resumes_before_new_claim(self):
        calls = []
        state = {'result': {'tasks': {
            'old': {'id':'old','owner':'worker','state':'RUNNING','slot':'2','generation':3},
            'new': {'id':'new','state':'READY'}},
            'slots': {'2': {'path':'owned-path','engine':{'provisioned':False}}}}}
        def call(op, args):
            calls.append(op)
            return state
        assignment = worker(call).claim_once()
        self.assertEqual(assignment['task'], 'old')
        self.assertEqual(assignment['claim']['generation'], 3)
        self.assertEqual(calls, ['snapshot'])


if __name__ == "__main__":
    unittest.main()
