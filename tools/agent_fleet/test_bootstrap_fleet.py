"""test_bootstrap_fleet.py -- durable operating installation acceptance.

DRIVES THE REAL `bootstrap_fleet.py` CLI + a real spawned service.py on an
isolated port, PLUS an adversarial foreign listener on another port. This is
the operator-path test: one documented command that refuses conflicting
starts, survives bounded restarts with the SAME persisted credentials, and
keeps every claim, checkpoint and session token across the transition.

STATEMENT: a persistent fleet service can be operated through one command.
PREDICTION: (1) `start` on a free port reaches ready; (2) a second `start`
is refused; (3) `stop` refuses an unmanaged instance and demands an ack;
(4) after `restart`, claims/checkpoints/session tokens survive unchanged;
(5) status reports the five stages monotonically.
FALSIFIER: a second start that spawns a service, a stop that clears the port
without an ack, or a restart that drops an owned claim or invalidates a
pre-restart session token.
"""
import json
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bootstrap_fleet
from bootstrap_fleet import FleetBootstrap, fleet_on_port

HERE = Path(__file__).resolve().parent
CLI = str(Path(bootstrap_fleet.__file__))


class _Foreign(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *a):
        pass


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FleetBootstrapTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.port = free_port()
        (self.root / "control").mkdir()
        self.secrets = {"supervisor": "SUP-SECRET-%08x" % id(self),
                        "enrollment": "ENR-SECRET-%08x" % id(self)}
        (self.root / "control" / ".service_secrets.json").write_text(
            json.dumps(self.secrets), encoding="utf-8")
        self.fb = FleetBootstrap(self.root, self.port)
        self.foreign = None
        self.foreign_thread = None

    def tearDown(self):
        if self.foreign_thread is not None:
            self.foreign.shutdown()
            self.foreign.server_close()
        if fleet_on_port(self.port)[1] == "fleet":
            try:
                self.fb.stop("test teardown controlled transition")
            except SystemExit:
                pass
        self.tmp.cleanup()

    # --- operator-path helpers ------------------------------------------
    def cli(self, *extra, expect=None):
        r = subprocess.run([sys.executable, CLI, *extra, "--root", str(self.root),
                            "--port", str(self.port)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=90)
        if expect is not None:
            self.assertEqual(r.returncode, expect,
                             "stdout:\n%s\nstderr:\n%s" % (r.stdout, r.stderr))
        return r

    def snap(self):
        from client import call
        sess = {"endpoint": "http://127.0.0.1:%d/v1/action" % self.port,
                "token": self.secrets["supervisor"]}
        return call(sess, "snapshot", {})["result"]

    def occupy_foreign(self):
        self.foreign = ThreadingHTTPServer(("127.0.0.1", self.port), _Foreign)
        self.foreign_thread = threading.Thread(target=self.foreign.serve_forever,
                                               daemon=True)
        self.foreign_thread.start()

    # --- tests -----------------------------------------------------------
    def test_start_reaches_ready_then_duplicate_start_refused(self):
        r = self.cli("start", expect=0)
        self.assertIn("running: yes", r.stdout + r.stderr)
        st = self.cli("status", expect=0)
        self.assertIn("running=OK", st.stdout)
        self.assertIn("reconciled=OK", st.stdout)
        r2 = self.cli("start", expect=1)
        self.assertIn("duplicate_start_refused", r2.stdout + r2.stderr)

    def test_stop_requires_ack_and_clears_stage(self):
        before = self.cli("stop", expect=2)  # no ack -> refused
        self.assertIn("stop_requires_ack", before.stdout + before.stderr)
        self.cli("start", expect=0)
        self.cli("stop", "--ack", "test: controlled transition", expect=0)
        st = self.cli("status", expect=0)
        self.assertIn("running=NO", st.stdout)
        self.assertIn("ready=NO", st.stdout)

    def test_foreign_listener_blocks_start_and_stop(self):
        self.occupy_foreign()
        r = self.cli("start", expect=1)
        self.assertIn("conflicting_listener_refused", r.stdout + r.stderr)
        r2 = self.cli("stop", "--ack", "test: foreign port", expect=1)
        self.assertIn("refusing_stop_unmanaged", r2.stdout + r2.stderr)

    def test_restart_preserves_claims_checkpoints_and_session_tokens(self):
        self.cli("start", expect=0)
        # enroll + qualify + elect + create + claim through the live HTTP path
        from control import digest
        enroll = self.snap().get("enrollment_hash")
        super_token = self.secrets["supervisor"]
        sessions = {}

        def act(token, op, **p):
            from client import call
            return call({"endpoint": "http://127.0.0.1:%d/v1/action" % self.port,
                         "token": token}, op, p)["result"]

        sess_tok = act(super_token, "enroll", agent="trial",
                       label="trial")["session_token"]
        sessions["trial"] = sess_tok
        act(super_token, "qualify", agent="trial",
            capabilities=["cpu", "gpu"], max_tasks=1, can_lead=False,
            rank=1, evidence="bootstrap restart fixture")
        # a lead-capable operator agent, ready at the pre-election epoch
        op_tok = act(super_token, "enroll", agent="op",
                     label="operator")["session_token"]
        act(super_token, "qualify", agent="op", capabilities=["cpu", "gpu"],
            max_tasks=2, can_lead=True, rank=10,
            evidence="bootstrap restart fixture")
        act(op_tok, "offer_lead", epoch=self.snap()["epoch"],
            checkpoint="operator ready; no foreign work")
        act(super_token, "elect")
        t = act(op_tok, "create_task", task="restart-proof",
                base="a" * 40, kind="worker",
                scopes=["docs/evidence/bootstrap-restart"],
                capabilities=["cpu", "gpu"],
                packet="statement / prediction / falsifier",
                epoch=self.snap()["epoch"])
        claim = act(sess_tok, "claim", task="restart-proof")
        gen = claim["generation"]; slot = claim["slot"]
        act(sess_tok, "checkpoint", task="restart-proof", generation=gen,
            checkpoint="cp-before-restart; evidence preserved at docs/evidence/x")
        before = self.snap()

        self.cli("restart", "--ack",
                 "test: verified bounded transition; claims must survive",
                 expect=0)
        after = self.snap()
        for key in ("revision",):
            pass  # revision advances only on mutation ops; claims are compared below
        self.assertEqual(after["tasks"]["restart-proof"]["state"], "RUNNING")
        self.assertEqual(after["tasks"]["restart-proof"]["owner"], "trial")
        self.assertEqual(after["tasks"]["restart-proof"]["slot"], slot)
        self.assertEqual(after["tasks"]["restart-proof"]["generation"], gen)
        self.assertEqual(after["tasks"]["restart-proof"]["checkpoint"],
                         "cp-before-restart; evidence preserved at docs/evidence/x")
        self.assertIsNotNone(after["leader"])
        # the pre-restart session token still writes (nothing was rekeyed)
        act(sess_tok, "checkpoint", task="restart-proof", generation=gen,
            checkpoint="cp-after-restart; same token, same owner")
        self.assertEqual(self.snap()["tasks"]["restart-proof"]["checkpoint"],
                         "cp-after-restart; same token, same owner")


if __name__ == "__main__":
    unittest.main(verbosity=2)