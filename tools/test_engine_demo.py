import importlib.util
import json
import subprocess
import sys
import threading
import time
import unittest
import tempfile
import types
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("engine_demo", ROOT / "engine_demo.py")
demo = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = demo
spec.loader.exec_module(demo)


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()
        self.step_started = threading.Event()
        self.release_step = threading.Event()

    def initialize(self):
        self.calls.append(("initialize", {}))
        return {"status": {"iteration": 0, "energy": 2.625, "centre": [0, 0, .125]}}

    def status(self):
        self.calls.append(("status", {}))
        return {"status": {"iteration": 0, "energy": 2.625, "centre": [0, 0, .125]}}

    def control(self, op, **values):
        with self.lock:
            self.calls.append((op, values))
        if op == "step":
            self.step_started.set()
            self.release_step.wait(1)
        return {"status": {"iteration": 1, "energy": 2.624, "centre": [0, 0, .124],
                            "terminal_state": "", "last_control": op}}


class FakeProcess:
    def __init__(self):
        self.terminated = False
        self.killed = False
        self.pid = 424242

    def poll(self):
        return None if not self.terminated else 0

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True


class SlowExitProcess(FakeProcess):
    def wait(self, timeout=None):
        if not self.killed:
            raise subprocess.TimeoutExpired("fake", timeout)
        return 0


class DemoSessionTests(unittest.TestCase):
    def test_read_only_pid_probe_does_not_kill_process(self):
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(2)"])
        try:
            image = demo._pid_image(proc.pid)
            self.assertTrue(image)
            self.assertIsNone(proc.poll())
        finally:
            proc.terminate()
            proc.wait(timeout=3)

    def test_pause_prevents_next_scheduled_step(self):
        transport = FakeTransport()
        messages = []
        session = demo.DemoSession(transport, Path("."), callback=messages.append)
        session.run(3)
        self.assertTrue(transport.step_started.wait(1))
        session.pause()
        transport.release_step.set()
        time.sleep(.12)
        steps = [call for call in transport.calls if call[0] == "step"]
        self.assertEqual(len(steps), 1)
        session.close()

    def test_close_terminates_only_owned_process(self):
        process = FakeProcess()
        session = demo.DemoSession(FakeTransport(), Path("."), process=process)
        session.close()
        self.assertTrue(process.terminated)
        self.assertFalse(process.killed)

    def test_stop_owned_kills_and_reaps_after_terminate_timeout(self):
        process = SlowExitProcess()
        demo._stop_owned(process)
        self.assertTrue(process.terminated)
        self.assertTrue(process.killed)

    def test_stale_zero_schedule_cannot_clear_newer_run(self):
        session = demo.DemoSession(FakeTransport(), Path("."))
        session.running = True
        session._run_generation = 2
        session._schedule_step(0, 1)
        self.assertTrue(session.running)
        session.close()

    def test_stale_step_error_cannot_clear_newer_run(self):
        session = demo.DemoSession(FakeTransport(), Path("."))
        session.running = True
        session._run_generation = 2
        session._step_worker(1, 1)
        self.assertTrue(session.running)
        session.close()

    def test_manifest_write_failure_stops_owned_child(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            exe = root / "engine.exe"
            exe.write_bytes(b"fake")
            (root / "shaders").mkdir()
            (root / "shaders" / "x.spv").write_bytes(b"shader")
            process = FakeProcess()
            with patch.object(demo.subprocess, "Popen", return_value=process), \
                 patch.object(demo, "_write_manifest", side_effect=OSError("disk")):
                with self.assertRaises(OSError):
                    demo._launch(exe, 54321, root / "runtime")
            self.assertTrue(process.terminated)

    def test_tk_construction_failure_stops_owned_child(self):
        process = FakeProcess()
        fake_tk = types.SimpleNamespace(Tk=lambda: (_ for _ in ()).throw(RuntimeError("tk")))
        with tempfile.TemporaryDirectory() as td:
            manifest = Path(td) / "manifest.json"
            manifest.write_text("{}", encoding="utf-8")
            with patch.object(demo, "_launch", return_value=(process, manifest)), \
                 patch.object(demo, "_wait_ready"), \
                 patch.dict(sys.modules, {"tkinter": fake_tk}):
                with self.assertRaises(RuntimeError):
                    demo.main(["--exe", "engine.exe", "--port", "54321"])
            self.assertTrue(process.terminated)

    def test_status_line_contains_b2_observables(self):
        line = demo._status_line({"status": {"iteration": 0, "energy": 2.625,
                                                 "centre": [0, 0, .125],
                                                 "terminal_state": "stationary",
                                                 "last_control": "init"}})
        self.assertIn("it=0", line)
        self.assertIn("z=0.125", line)
        self.assertIn("terminal=stationary", line)

    def test_status_line_surfaces_refusal_and_uninitialized_state(self):
        self.assertEqual(demo._status_line({"ok": False, "error": "not active"}),
                         "ERROR: not active")
        self.assertIn("not initialized", demo._status_line({"active": False}))

    def test_closed_session_drops_queued_control_before_transport(self):
        transport = FakeTransport()
        session = demo.DemoSession(transport, Path("."))
        session.close()
        session.reset()
        time.sleep(.05)
        self.assertEqual(transport.calls, [])


if __name__ == "__main__":
    unittest.main()
