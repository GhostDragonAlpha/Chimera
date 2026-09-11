from pathlib import Path
import tempfile, unittest
from tools.agent_fleet.launch_worker import launch_worker, load_secrets

class LauncherTests(unittest.TestCase):
    def test_enroll_qualify_start_removes_secrets_from_child(self):
        with tempfile.TemporaryDirectory() as d:
            session = Path(d) / "worker.json"; calls = {}; env = {}
            def enroll(endpoint, agent, label, output, token):
                calls["enroll"] = token; output.write_text("{}", encoding="utf-8")
            def qualify(endpoint, token, agent, caps, maximum): calls["qualify"] = token
            def popen(argv, **kwargs): env.update(kwargs["env"]); calls["argv"] = argv; return object()
            launch_worker(endpoint="http://127.0.0.1:8099/v1/action", agent="worker-1", label="worker",
                          session_path=session, supervisor_token="super", enrollment_token="enroll",
                          capabilities=["cpu"], worker_script=Path("worker.py"), enroll_runner=enroll,
                          qualify_call=qualify, process_runner=popen)
            self.assertEqual(calls["enroll"], "enroll"); self.assertEqual(calls["qualify"], "super")
            self.assertNotIn("CHIMERA_FLEET_SUPERVISOR_TOKEN", env)
            self.assertNotIn("CHIMERA_FLEET_ENROLLMENT_TOKEN", env)
            self.assertEqual(calls["argv"][-2:], ["--session", str(session)])

    def test_missing_secrets_and_existing_session_refuse(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "secrets.json"; p.write_text('{"supervisor_token":"x"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "distinct_launcher_secrets_required"): load_secrets(p)
            session = Path(d) / "worker.json"; session.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "session_path_already_exists"):
                launch_worker(endpoint="x", agent="a", label="l", session_path=session,
                              supervisor_token="s", enrollment_token="e", capabilities=["cpu"],
                              worker_script=Path("worker.py"), enroll_runner=lambda *x: None,
                              qualify_call=lambda *x: None, process_runner=lambda *x, **k: None)

if __name__ == "__main__": unittest.main()
