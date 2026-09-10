import importlib.util
import json
import sys
import threading
import time
import unittest
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

    def poll(self):
        return None if not self.terminated else 0

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True


class DemoSessionTests(unittest.TestCase):
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

    def test_status_line_contains_b2_observables(self):
        line = demo._status_line({"status": {"iteration": 0, "energy": 2.625,
                                                 "centre": [0, 0, .125],
                                                 "terminal_state": "stationary",
                                                 "last_control": "init"}})
        self.assertIn("it=0", line)
        self.assertIn("z=0.125", line)
        self.assertIn("terminal=stationary", line)


if __name__ == "__main__":
    unittest.main()
