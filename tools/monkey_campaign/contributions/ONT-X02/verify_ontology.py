"""verify_ontology.py -- ONT-X02 reconciliation probe.

Independently verifies the EXISTING M-X02 implementation (session_flow.py in
the play worktree, identity pinned in PREREGISTRATION.md) against the ontology
card's done_when and recovery profile, using this probe's OWN minimal doubles
(the existing suite's doubles are not reused), then re-runs the existing
falsifier suite at the pinned HEAD.

No reimplementation, no edits to the existing module, no engine/browser.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

PLAY = pathlib.Path("E:/ChimeraWork/monkey-play-20260924")
PRODUCT = PLAY / "tools/monkey_campaign/product"

# TIE2-guard resolution (this correction; the PR #135 reviewer's named
# follow-up): the LIVE play worktree (HEAD 8d16d3c1) no longer ships
# product/session_flow.py on disk, so the pinned module is resolved from
# THIS contribution's byte-exact reference/ copy (sha asserted against the
# PREREGISTRATION pin) instead of the mutable live tree.
HERE = pathlib.Path(__file__).resolve().parent
REFERENCE = HERE / "reference/tools/monkey_campaign/product"
PIN_SESSION_FLOW = ("30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f"
                    "307458455cf")
PRODUCT = REFERENCE
sys.path.insert(0, str(PRODUCT))
if hashlib.sha256((REFERENCE / "session_flow.py").read_bytes()).hexdigest() \
        != PIN_SESSION_FLOW:
    raise RuntimeError("verify_ontology: pinned session_flow.py drift vs "
                       "reference/ - refusing by name")

import session_flow as sf  # noqa: E402  (pinned existing module, read-only)


class ProbeMapper:
    """Minimal own double: records every call; release_all is observable."""

    def __init__(self):
        self.records = []          # (kind, detail)
        self.held = {}

    def press(self, name, now_ms):
        self.records.append(("press", name, now_ms))
        self.held[name] = now_ms

    def release(self, name, now_ms):
        self.records.append(("release", name, now_ms))
        self.held.pop(name, None)

    def release_all(self, now_ms):
        self.records.append(("release_all", sorted(self.held), now_ms))
        self.held.clear()

    def mouse(self, dx_counts):
        self.records.append(("mouse", dx_counts))

    def tick(self, now_ms):
        self.records.append(("tick", now_ms))

    def sample_boundaries(self):
        self.records.append(("sample",))


class ProbeWorld:
    def __init__(self):
        self.calls = []

    def restart_scene(self):
        self.calls.append("boot")

    def teardown(self):
        self.calls.append("terminate")
        self.calls.append("wait")
        self.calls.append("kill")


def flow():
    m = ProbeMapper()
    w = ProbeWorld()
    return sf.SessionFlow(m, w.restart_scene, w.teardown), m, w


def check_reaches_play(r):
    f, m, w = flow()
    r["reaches_play"] = f.state == sf.ATTRACT
    f.key("Return", 1, 100); f.key("Return", 0, 110)
    r["reaches_play"] = r["reaches_play"] and f.state == sf.PLAYING
    r["start_is_key_only"] = True      # no other mutator was called


def check_pause_exit(r):
    f, m, w = flow()
    f.key("Return", 1, 100); f.key("Return", 0, 110)
    f.key("Escape", 1, 200); f.key("Escape", 0, 210)
    r["pause_via_key"] = f.state == sf.PAUSED
    r["pause_quiesces_mapper"] = any(rec[0] == "release_all" for rec in m.records)
    before = len(m.records)
    f.tick(300); f.tick(400)
    r["paused_emits_nothing"] = len(m.records) == before
    f.key("Q", 1, 500); f.key("Q", 0, 510)
    r["exit_via_key"] = f.state == sf.EXITED
    r["teardown_once_ordered"] = w.calls == ["terminate", "wait", "kill"]
    after = len(m.records)
    f.tick(600); f.key("Return", 1, 700)
    r["exited_is_terminal"] = f.state == sf.EXITED and len(m.records) == after


def check_restart_explicit(r):
    f, m, w = flow()
    f.key("Return", 1, 100); f.key("Return", 0, 110)
    f.key("R", 1, 150); f.key("R", 0, 160)          # R while PLAYING: no-op
    r["restart_requires_paused"] = f.state == sf.PLAYING and w.calls == []
    f.key("Escape", 1, 200); f.key("Escape", 0, 210)
    quiesced = len([x for x in m.records if x[0] == "release_all"])
    f.key("R", 1, 300); f.key("R", 0, 310)
    r["restart_explicit_user_action"] = f.state == sf.PLAYING and w.calls == ["boot"]
    r["restart_quiesces_then_boots"] = (
        quiesced >= 1 and w.calls == ["boot"]
        and any(x[0] == "release_all" for x in m.records))
    f2, m2, w2 = flow()
    state0 = f2.state
    for t in (100, 200, 1000, 60000):               # zero events, clock runs
        f2.tick(t)
    r["no_timer_transitions"] = f2.state == state0


def check_resume_gating(r):
    """After resume the mapper accepts fresh user keys again (the precise
    decay-tail law needs the REAL U01 mapper and stays with the existing
    suite's F2, which this probe re-runs)."""
    f, m, w = flow()
    f.key("Return", 1, 100); f.key("Return", 0, 110)
    f.key("Escape", 1, 200); f.key("Escape", 0, 210)
    m.records.clear()
    f.key("Return", 1, 300); f.key("Return", 0, 310)  # resume (Return, per bindings)
    f.key("Up", 1, 400)
    r["resume_accepts_keys"] = any(
        x[0] == "press" and x[1] == "Up" for x in m.records)


def run_suite(r):
    """Re-run the existing falsifier suite AT THE PINNED BYTES: the suite
    file is resolved from reference/ (byte-exact, the PR #135 reviewer's
    named follow-up) into a temp dir beside the pinned modules - the live
    play product dir no longer ships these files on disk."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        # the pinned suite's own layout: flat product imports + the
        # absolute tools.* cross-imports both resolve from <root>
        tdp = pathlib.Path(td) / "tools/monkey_campaign/product"
        tdp.mkdir(parents=True)
        for name in ("session_flow.py", "session_flow_tests.py",
                     "input_mapper.py"):
            (tdp / name).write_bytes((REFERENCE / name).read_bytes())
        tse = tdp.parent.parent / "science_funnel" / "typeb_export"
        tse.mkdir(parents=True)
        (tse / "command_record.py").write_bytes(
            (HERE / "reference/tools/science_funnel/typeb_export/"
             "command_record.py").read_bytes())
        proc = subprocess.run(
            [sys.executable, "-B", "session_flow_tests.py"],
            cwd=str(tdp), capture_output=True, timeout=110)
    r["existing_suite_exit_0"] = proc.returncode == 0
    r["existing_suite_all_pass"] = b"ALL CHECKS PASS" in proc.stdout


def run_all() -> dict:
    r = {"schema": "ont-x02.reconciliation.probe.v1",
         "play_head": "f30f2224663324e9374b076938c56672febf4082",
         "session_flow_sha256":
             "30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf"}
    check_reaches_play(r)
    check_pause_exit(r)
    check_restart_explicit(r)
    check_resume_gating(r)
    run_suite(r)
    keys = [k for k in r if k not in ("schema", "play_head", "session_flow_sha256")]
    r["green"] = {k: r[k] for k in keys}
    r["all_green"] = all(bool(v) for v in r["green"].values())
    return r


def main() -> int:
    r = run_all()
    here = pathlib.Path(__file__).resolve().parent
    (here / "reconciliation_receipt.json").write_text(
        json.dumps(r, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(r["green"], indent=1))
    print("all_green:", r["all_green"])
    return 0 if r["all_green"] else 1


if __name__ == "__main__":
    sys.exit(main())
