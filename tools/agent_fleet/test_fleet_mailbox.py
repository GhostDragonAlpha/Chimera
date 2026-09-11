"""Fleet mailbox tests (CPU only; temp roots exclusively).

The LIVE fleet-space mailbox (fleet_mailbox.ROOT, E:\\ChimeraWork\\mailbox) is in
production — every test here runs against its own tempfile root via the root= seam or
the FLEET_MAILBOX_ROOT environment override, and the suite carries a guard asserting
the live tree was never written (no test-specific agent name appears in it before or
after). Pins the preregistered predictions of fleet-mailbox-hardening-01: the
atomicity probe (100 posts / 4 processes / zero lost), idempotent take, append-only
served history, name-safety refusals that write nothing, unreadable-message retention.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import fleet_mailbox as fm  # noqa: E402

LIVE_ROOT = Path(r"E:\ChimeraWork\mailbox")
PROBE_RECIPIENT = "unit-probe-inbox"
PROBE_SENDERS = ["unit-probe-p0", "unit-probe-p1", "unit-probe-p2", "unit-probe-p3"]
TEST_AGENT_NAMES = set(PROBE_SENDERS) | {PROBE_RECIPIENT, "unit-target",
                                         "unit-take-agent", "..evil", "a/b",
                                         ".hidden", "a:b", "a<b>"}


def _inbox_listing(root):
    """Names of every file under a mailbox root (relative), read-only."""
    root = Path(root)
    out = set()
    if not root.exists():
        return out
    for p in root.rglob("*"):
        if p.is_file():
            out.add(str(p.relative_to(root)))
    return out


class MailboxTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "mailbox"
        self._live_before = _inbox_listing(LIVE_ROOT)

    def tearDown(self):
        live_now = _inbox_listing(LIVE_ROOT)
        for name in live_now:
            for agent in TEST_AGENT_NAMES:
                self.assertNotIn(agent, name,
                                 "test artifact leaked into the LIVE mailbox: %s" % name)

    def post(self, sender, recipient, subject, body="b", correlation=""):
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):  # fm.post prints; keep output clean
            fm.post(sender, recipient, subject, body, correlation, root=self.root)

    def read(self, agent, take=False):
        buf = {}
        # capture stdout of fm.read without touching the live tree
        import contextlib, io
        buf["io"] = io.StringIO()
        with contextlib.redirect_stdout(buf["io"]):
            fm.read(agent, take=take, root=self.root)
        buf["data"] = json.loads(buf["io"].getvalue())
        return buf["data"]


class AtomicityProbeTests(MailboxTestBase):
    """Prediction 1 / falsifier 1: 100 concurrent posts from 4 OS processes —
    zero lost, zero partial."""

    def test_100_posts_from_4_processes_lose_nothing(self):
        n_per_proc, n_procs = 25, 4
        driver = (
            "import sys, json\n"
            "sys.path.insert(0, %r)\n"
            "import fleet_mailbox as m\n"
            "me = sys.argv[1]\n"
            "for i in range(%d):\n"
            "    m.post(me, %r, 'msg-%%s-%%04d' %% (me, i),\n"
            "           'body', correlation='atomicity', root=%r)\n"
        ) % (str(TOOLS), n_per_proc, PROBE_RECIPIENT, str(self.root))
        procs = [subprocess.Popen([sys.executable, "-c", driver, s],
                                  env=dict(os.environ),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                 for s in PROBE_SENDERS]
        outs = [p.communicate() for p in procs]
        for i, (out, err) in enumerate(outs):
            self.assertEqual(procs[i].returncode, 0,
                             "probe process %d failed: %s" % (i, err.decode()))
            self.assertEqual(len(out.decode().strip().splitlines()), n_per_proc)

        inbox = self.root / "inbox" / PROBE_RECIPIENT
        files = sorted(inbox.glob("*.json"))
        self.assertEqual(len(files), n_per_proc * n_procs, "lost messages")
        self.assertEqual(list(inbox.glob(".tmp-*")), [], "partial post survived")
        ids, subjects = set(), []
        per_sender = {s: 0 for s in PROBE_SENDERS}
        for f in files:
            msg = json.loads(f.read_text(encoding="utf-8"))  # every file parses
            ids.add(msg["id"])
            subjects.append(msg["subject"])
            per_sender[msg["from"]] += 1
        self.assertEqual(len(ids), n_per_proc * n_procs, "duplicate message ids")
        self.assertEqual(len(subjects), n_per_proc * n_procs)
        self.assertEqual(per_sender, {s: n_per_proc for s in PROBE_SENDERS})


class TakeAndServedTests(MailboxTestBase):
    """Predictions 2 / falsifier 2: take idempotent; served append-only."""

    def test_take_idempotent_and_append_only(self):
        agent = "unit-take-agent"
        self.post("unit-probe-p0", agent, "first-wave-1")
        self.post("unit-probe-p0", agent, "first-wave-2")
        first = self.read(agent, take=True)
        self.assertEqual(first["count"], 2)
        inbox = self.root / "inbox" / agent
        served = self.root / "served" / agent
        self.assertEqual(list(inbox.glob("*.json")), [])
        first_served = {p.name: p.read_bytes() for p in sorted(served.glob("*.json"))}
        self.assertEqual(len(first_served), 2)

        # second take on an empty inbox: clean no-op, history untouched
        second = self.read(agent, take=True)
        self.assertEqual(second["count"], 0)
        self.assertEqual({p.name: p.read_bytes() for p in sorted(served.glob("*.json"))},
                         first_served, "served history changed without new mail")

        # new mail arrives; take appends (never deletes)
        self.post("unit-probe-p1", agent, "second-wave-1")
        self.post("unit-probe-p2", agent, "second-wave-2")
        third = self.read(agent, take=True)
        self.assertEqual(third["count"], 2)
        served_now = {p.name: p.read_bytes() for p in sorted(served.glob("*.json"))}
        self.assertEqual(len(served_now), 4)
        for name, body in first_served.items():
            self.assertEqual(served_now.get(name), body,
                             "append-only violated for %s" % name)

        # third take on empty inbox: still idempotent
        self.assertEqual(self.read(agent, take=True)["count"], 0)
        self.assertEqual(len(list(served.glob("*.json"))), 4)

    def test_unreadable_message_retained_and_taken(self):
        agent = "unit-take-agent"
        self.post("unit-probe-p0", agent, "valid")
        bad = self.root / "inbox" / agent / "broken.json"
        bad.write_text("{not json", encoding="utf-8")
        data = self.read(agent, take=True)
        self.assertEqual(data["count"], 2)
        unreadable = [m for m in data["messages"] if "unreadable" in m]
        self.assertEqual(len(unreadable), 1, "corrupt file silently dropped")
        served = self.root / "served" / agent
        self.assertEqual(len(list(served.glob("*.json"))), 2,
                        "unreadable message not moved to served (history loss)")


class NameSafetyTests(MailboxTestBase):
    """Prediction 3 / falsifier 4: refusals fire and write NOTHING."""

    def test_refused_post_writes_nothing(self):
        bad_recipients = ["../evil", "a/b", "a\\b", ".hidden", "a:b", "a<b>", ""]
        for rcpt in bad_recipients:
            with self.assertRaises(SystemExit):
                self.post("unit-probe-p0", rcpt, "s")
        bad_senders = ["../evil", "a/b", ".hidden", "a:b"]
        for sender in bad_senders:
            with self.assertRaises(SystemExit):
                self.post(sender, "unit-target", "s")
        # nothing was created anywhere in the temp root
        self.assertEqual(_inbox_listing(self.root), set(),
                         "a refused post still wrote to the tree")

    def test_read_refuses_bad_agent(self):
        for agent in ("../evil", "a/b", ".hidden"):
            with self.assertRaises(SystemExit):
                self.read(agent)


class RootSeamTests(MailboxTestBase):
    """Prediction 5: default is the live instance; the seam never touches it."""

    def test_default_root_is_live_instance(self):
        self.assertEqual(fm._root(), LIVE_ROOT)
        self.assertEqual(fm._root(None), LIVE_ROOT)
        self.assertEqual(fm._root("X"), Path("X"))
        old = os.environ.get("FLEET_MAILBOX_ROOT")
        os.environ["FLEET_MAILBOX_ROOT"] = str(self.root)
        try:
            self.assertEqual(fm._root(), self.root)
        finally:
            if old is None:
                del os.environ["FLEET_MAILBOX_ROOT"]
            else:
                os.environ["FLEET_MAILBOX_ROOT"] = old

    def test_missing_inbox_shape(self):
        # v0 contract: reading an agent with no inbox prints no count key
        data = self.read("never-posted-agent")
        self.assertEqual(data, {"agent": "never-posted-agent", "messages": []})


class CliSurfaceTests(MailboxTestBase):
    """Prediction 5: the CLI surface and output JSON are the live v0's."""

    def _run(self, *args):
        env = dict(os.environ)
        env["FLEET_MAILBOX_ROOT"] = str(self.root)
        return subprocess.run([sys.executable, str(TOOLS / "fleet_mailbox.py")] + list(args),
                              env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True)

    def test_post_and_read_via_cli(self):
        r = self._run("post", "--from", "unit-probe-p0", "--to", "unit-target",
                      "--subject", "cli-1", "--body", "b", "--correlation", "c1")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(sorted(out), ["id", "posted"])
        self.assertEqual(len(out["id"]), 12)  # secrets.token_hex(6)

        r = self._run("read", "--agent", "unit-target")
        data = json.loads(r.stdout)
        self.assertEqual(sorted(data), ["agent", "count", "messages"])
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["messages"][0]["subject"], "cli-1")
        self.assertEqual(data["messages"][0]["correlation"], "c1")
        self.assertEqual(data["messages"][0]["from"], "unit-probe-p0")
        self.assertEqual(data["messages"][0]["to"], "unit-target")

        r = self._run("read", "--agent", "unit-target", "--take")
        self.assertEqual(json.loads(r.stdout)["count"], 1)
        served = self.root / "served" / "unit-target"
        self.assertEqual(len(list(served.glob("*.json"))), 1)

    def test_cli_post_refusal_exit(self):
        r = self._run("post", "--from", "unit-probe-p0", "--to", "../evil",
                      "--subject", "s", "--body", "b")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(_inbox_listing(self.root), set())


class LiveTreeGuardTests(MailboxTestBase):
    """Falsifier 3: the suite never touches the live mailbox."""

    def test_live_tree_has_no_test_artifacts(self):
        # read-only observation of the live instance (production may contain real
        # traffic; we assert only that OUR names are absent, before and after)
        live = _inbox_listing(LIVE_ROOT)
        for name in live:
            for agent in TEST_AGENT_NAMES:
                self.assertNotIn(agent, name)
        # and the seam cannot be tricked into the live root by an explicit root=
        self.assertNotEqual(Path(fm._root(self.root)), LIVE_ROOT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
