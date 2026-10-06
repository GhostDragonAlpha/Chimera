"""test_climb_intent_candidate.py -- ONT-U05 candidate conformance suite.

Runs the pinned-subject laws on the RECOVERED candidate bytes (this
directory) plus fresh full-suite subprocess runs. The FULL frozen
measurements live in the recovered suites themselves (73 + 4 checks,
run byte-exact; receipts in evidence/). CPU-only, headless, stdlib.

    python -B -m unittest test_climb_intent_candidate -v

Frozen in PREREGISTRATION.md (prediction (a)-(e)) BEFORE any run in this
attempt. Every subject byte is hash-pinned; any drift fails the first
test class (falsifier F-R1).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ── the pinned identities (PREREGISTRATION.md, frozen before any edit) ──────
PINNED = {
    "climb_intent.py":
        "586cb1c541afdc391ac14ce989cf2d2561a9ee79e25e874f7fbfc2312fd3c5a2",
    "climb_intent_tests.py":
        "291eb0b60e754e497d425dada1dffdf0839ea3f8a91f16fd0239ab3f9fdc9895",
    "climb_intent_amr_tests.py":
        "7ff7f3ba2678d6533e6f40666b5faf9f102751377bc4f89bf68846d2df3b7538",
    "reference/tools/monkey_campaign/product/input_mapper.py":
        "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
    "reference/tools/monkey_campaign/product/focus_policy.py":
        "e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0",
    "reference/tools/monkey_campaign/product/session_flow.py":
        "30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf",
    "reference/tools/science_funnel/typeb_export/command_record.py":
        "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
}
SEAM_SHA = PINNED["reference/tools/science_funnel/typeb_export/command_record.py"]


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_mirror(root: Path) -> Path:
    """A runnable repo-shaped tree of byte-exact recovered files."""
    prod = root / "tools" / "monkey_campaign" / "product"
    seam = root / "tools" / "science_funnel" / "typeb_export"
    prod.mkdir(parents=True)
    seam.mkdir(parents=True)
    for name in ("climb_intent.py", "climb_intent_tests.py",
                 "climb_intent_amr_tests.py"):
        shutil.copyfile(HERE / name, prod / name)
    for rel in ("reference/tools/monkey_campaign/product/input_mapper.py",
                "reference/tools/monkey_campaign/product/focus_policy.py",
                "reference/tools/monkey_campaign/product/session_flow.py"):
        shutil.copyfile(HERE / rel, prod / Path(rel).name)
    shutil.copyfile(
        HERE / "reference/tools/science_funnel/typeb_export/command_record.py",
        seam / "command_record.py")
    return root


class PinnedLineage(unittest.TestCase):
    """F-R1: every recovered byte is the pinned byte."""

    def test_pinned_hashes_hold(self):
        for rel, want in PINNED.items():
            self.assertEqual(sha256_file(HERE / rel), want, rel)

    def test_original_author_receipt_numbers_reproduced(self):
        # The original green receipt (77/77, recovered, hash-pinned) records
        # the seeded fuzz totals; this attempt's fresh run reproduced them
        # bit-identically (evidence/suite_main_20260926.txt). Pinned here so
        # any future drift of seed/mix is visible.
        receipt = (HERE / "recovered/U05b_amendments_U06/receipts/"
                          "climb_intent_tests_77of77_with_amr_20260924.txt")
        text = receipt.read_text(encoding="utf-8")
        for token in ("events=354, accepted=354", "let_go=185",
                      "named_drops=1089", "repeat=416, no_op=744"):
            self.assertIn(token, text)


class MirrorCase(unittest.TestCase):
    """Base: a fresh mirror per test, imports cleaned up after."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="ont_u05_mirror_")
        self.mirror = build_mirror(Path(self._tmp))
        self._added = [str(self.mirror),
                       str(self.mirror / "tools/monkey_campaign/product")]
        for p in reversed(self._added):
            sys.path.insert(0, p)
        sys.dont_write_bytecode = True

    def tearDown(self):
        for p in self._added:
            try:
                sys.path.remove(p)
            except ValueError:
                pass
        for mod in [m for m in list(sys.modules)
                    if m == "climb_intent" or m.startswith(
                        ("tools.", "tools", "input_mapper", "focus_policy",
                         "session_flow", "command_record"))]:
            sys.modules.pop(mod, None)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def load_channel(self):
        import climb_intent as CI  # the candidate bytes, from the mirror
        return CI


class VersionLaw(MirrorCase):
    """F-R5 guard: the version rule is exactly v1 (spec section 4)."""

    def test_valid_v1_constructs(self):
        CI = self.load_channel()
        e = CI.IntentEvent(intent=CI.CLIMB_REQUEST, issued_tick=300,
                           now_ms=1000)
        self.assertEqual(e.intent_version, 1)
        self.assertEqual(e.source, "u05_climb_intent")
        self.assertEqual(
            e.canonical_fields(),
            {"intent_version": 1, "intent": "climb_request",
             "issued_tick": 300, "now_ms": 1000,
             "source": "u05_climb_intent"})

    def test_wrong_versions_refused(self):
        CI = self.load_channel()
        for bad in (2, True, False, "1", 1.0, None):
            with self.assertRaises(CI.IntentEventError, msg=repr(bad)):
                CI.IntentEvent(intent=CI.CLIMB_REQUEST, issued_tick=0,
                               now_ms=0, intent_version=bad)

    def test_unknown_intent_and_bad_stamps_refused(self):
        CI = self.load_channel()
        for intent in ("grab", "climb", "release", ""):
            with self.assertRaises(CI.IntentEventError, msg=intent):
                CI.IntentEvent(intent=intent, issued_tick=0, now_ms=0)
        for kwargs in ({"issued_tick": -1, "now_ms": 0},
                       {"issued_tick": 0, "now_ms": -1},
                       {"issued_tick": 1.0, "now_ms": 0},
                       {"issued_tick": 0, "now_ms": True}):
            with self.assertRaises(CI.IntentEventError, msg=repr(kwargs)):
                CI.IntentEvent(intent=CI.LET_GO, **kwargs)

    def test_forged_source_refused(self):
        CI = self.load_channel()
        with self.assertRaises(CI.IntentEventError):
            CI.IntentEvent(intent=CI.CLIMB_REQUEST, issued_tick=0, now_ms=0,
                           source="someone_else")


class C12Stamps(MirrorCase):
    """C12: one timeline with the walk seam; the stamp chain is explicit."""

    def test_default_stamp_convention(self):
        CI = self.load_channel()
        e = CI.IntentEvent(intent=CI.CLIMB_REQUEST, issued_tick=300,
                           now_ms=1000)
        self.assertEqual(e.issued_tick, (1000 * 300) // 1000)

    def test_channel_stamps_with_injected_tick_source(self):
        CI = self.load_channel()
        sink = CI.MockIntentSink()
        ticks = iter([777, 888])
        chan = CI.ClimbIntentChannel(sink, tick_source=lambda: next(ticks))
        chan.press("Space", now_ms=1000)
        chan.release("Space", now_ms=1050)
        chan.press("C", now_ms=1100)
        self.assertEqual([e.issued_tick for e in sink.events], [777, 888])
        self.assertEqual([e.now_ms for e in sink.events], [1000, 1100])


class EdgeLaw(MirrorCase):
    """One explicit press = one event; holds are silence; release re-arms."""

    def test_press_hold_release_rearm(self):
        CI = self.load_channel()
        sink = CI.MockIntentSink()
        chan = CI.ClimbIntentChannel(sink)
        self.assertEqual(chan.press("Space", now_ms=1000), "climb_request")
        self.assertEqual(len(sink), 1)
        for ms in (1010, 1020, 1030):        # OS auto-repeat while held
            chan.press("Space", now_ms=ms)
        self.assertEqual(len(sink), 1)       # HOLD-SILENT
        self.assertEqual(chan.release("Space", now_ms=1100), "climb_request")
        self.assertEqual(len(sink), 1)       # a release NEVER emits
        chan.press("Space", now_ms=1200)     # the edge re-armed
        self.assertEqual(len(sink), 2)
        self.assertTrue(chan.last_trace["repeat_press"])  # named, not silent

    def test_two_independent_edges(self):
        CI = self.load_channel()
        sink = CI.MockIntentSink()
        chan = CI.ClimbIntentChannel(sink)
        chan.press("Space", now_ms=1000)
        chan.press("C", now_ms=1010)         # C held must not eat Space's edge
        self.assertEqual([e.intent for e in sink.events],
                         ["climb_request", "let_go"])
        self.assertEqual(len(sink), 2)


class GateLaw(MirrorCase):
    """Gates drop BY NAME, never arm; releases pass; dominance ordering."""

    def test_pause_drops_by_name_and_recovery_is_clean(self):
        CI = self.load_channel()
        sink = CI.MockIntentSink()
        chan = CI.ClimbIntentChannel(sink)
        chan.press("Space", now_ms=1000)
        chan.release("Space", now_ms=1010)
        chan.on_pause(now_ms=1020)
        self.assertEqual(chan.state, "paused")
        self.assertIsNone(chan.press("Space", now_ms=1030))
        self.assertEqual(len(sink), 1)
        drops = chan.last_trace["drops"]
        self.assertEqual(drops[0]["reason"], "dropped_paused")
        self.assertEqual(drops[0]["gates"], ["paused"])
        chan.on_resume(now_ms=1040)
        chan.press("Space", now_ms=1050)     # no phantom: fires exactly once
        self.assertEqual(len(sink), 2)

    def test_dominance_disconnected_blur_paused(self):
        CI = self.load_channel()
        sink = CI.MockIntentSink()
        chan = CI.ClimbIntentChannel(sink)
        chan.on_pause(now_ms=1000)
        chan.on_blur(now_ms=1001)
        chan.on_disconnect(now_ms=1002)
        self.assertEqual(chan.state, "disconnected")
        chan.press("C", now_ms=1003)
        self.assertEqual(chan.last_trace["drops"][0]["reason"],
                         "dropped_disconnected")
        self.assertEqual(chan.last_trace["drops"][0]["gates"],
                         ["blurred", "disconnected", "paused"])

    def test_release_passes_under_gates_and_never_emits(self):
        CI = self.load_channel()
        sink = CI.MockIntentSink()
        chan = CI.ClimbIntentChannel(sink)
        chan.press("Space", now_ms=1000)
        chan.on_blur(now_ms=1001)
        self.assertIsNotNone(chan.release("Space", now_ms=1002))  # passes
        self.assertEqual(len(sink), 1)
        chan.on_focus(now_ms=1003)
        chan.press("Space", now_ms=1004)     # release un-armed through the blur
        self.assertEqual(len(sink), 2)

    def test_no_fabricated_retract_under_gate_churn(self):
        CI = self.load_channel()
        sink = CI.MockIntentSink()
        chan = CI.ClimbIntentChannel(sink)
        for i, ev in enumerate(["pause", "blur", "disconnect", "focus",
                                "reconnect", "resume"] * 3):
            getattr(chan, "on_" + ev)(now_ms=1000 + i)
        self.assertEqual(len(sink), 0)       # zero events from policy churn
        self.assertEqual(sum(1 for e in sink.events
                             if e.intent == CI.LET_GO), 0)
        chan.press("C", now_ms=2000)         # the ONLY let_go is explicit
        self.assertEqual(sum(1 for e in sink.events
                             if e.intent == CI.LET_GO), 1)


class PureSignal(MirrorCase):
    """I5: imports, wire shape, walk-seam structural isolation."""

    def test_import_surface_is_exactly_declared(self):
        import ast
        src = (Path(self.mirror) / "tools/monkey_campaign/product/"
                                       "climb_intent.py").read_text(
                                                            encoding="utf-8")
        tree = ast.parse(src)
        externals = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and \
                    node.module.startswith("tools."):
                externals.append((node.module,
                                  [a.name for a in node.names]))
        self.assertEqual(externals,
                         [("tools.science_funnel.typeb_export.command_record",
                           ["PHYSICS_HZ"])])
        # the decisive structural fact: the class is never CONSTRUCTED.
        # (The NAME may appear in prose/docstrings -- naming the separation
        # law is not violating it; the module's own I5 note and the author's
        # REVISION A precedent both state this.)
        self.assertNotRegex(src, r"CommandRecord\s*\(")

    def test_event_wire_has_no_float_field(self):
        CI = self.load_channel()
        fields = CI.IntentEvent.__dataclass_fields__
        self.assertEqual(set(fields),
                         {"intent", "issued_tick", "now_ms",
                          "intent_version", "source"})
        e = CI.IntentEvent(intent=CI.CLIMB_REQUEST, issued_tick=0, now_ms=0)
        canonical = e.canonical_fields()
        self.assertTrue(all(isinstance(v, (str, int))
                            for v in canonical.values()))
        json.dumps(canonical)  # wire form round-trips

    def test_physics_hz_is_imported_not_redeclared(self):
        CI = self.load_channel()
        from tools.science_funnel.typeb_export import command_record as cr
        self.assertTrue(CI.PHYSICS_HZ is cr.PHYSICS_HZ)  # identity, not copy


class Integration(MirrorCase):
    """I7 (reduced): one feed, two declared channels, two sinks, no crossing."""

    def test_space_is_named_walk_refusal_and_one_climb_request(self):
        CI = self.load_channel()
        import input_mapper as M
        from tools.science_funnel.typeb_export.command_record import (
            CommandRecord)

        walk_sink = M.MockSink()
        intent_sink = CI.MockIntentSink()
        mapper = M.InputMapper(walk_sink)
        chan = CI.ClimbIntentChannel(intent_sink)

        ref = mapper.press("Space", now_ms=1000)     # walk side: named refusal
        chan.press("Space", now_ms=1000)             # intent side: delivered
        self.assertEqual(ref, "jump")                # U01's REFUSAL, unchanged
        self.assertEqual(len(walk_sink.records), 0)  # no walk record from it
        self.assertEqual(len(intent_sink.events), 1)
        self.assertEqual(intent_sink.events[0].intent, "climb_request")
        for rec in walk_sink.records:                # no crossing, either way
            self.assertIsInstance(rec, CommandRecord)
        for ev in intent_sink.events:
            self.assertNotIsInstance(ev, CommandRecord)


class FullRecoveredSuites(MirrorCase):
    """F-R2: the byte-exact recovered suites run GREEN end to end."""

    def run_suite(self, name):
        proc = subprocess.run(
            [sys.executable, "-B",
             f"tools/monkey_campaign/product/{name}"],
            cwd=str(self.mirror), capture_output=True, text=True,
            timeout=120)
        out = proc.stdout + proc.stderr
        return proc.returncode, out

    def test_main_suite_green_with_seam_hash_bound(self):
        code, out = self.run_suite("climb_intent_tests.py")
        self.assertEqual(code, 0, out[-2000:])
        self.assertIn("RESULT: GREEN", out)
        start = [l for l in out.splitlines()
                 if l.startswith("seam sha256 at start")]
        end = [l for l in out.splitlines()
               if l.startswith("seam sha256 at end")]
        self.assertEqual(len(start), 1)
        self.assertEqual(len(end), 1)
        self.assertIn(SEAM_SHA, start[0])
        self.assertIn(SEAM_SHA, end[0])      # falsifier I6, fresh tree
        self.assertEqual(out.count("[PASS]"), 73)
        self.assertNotIn("FIRED", out)

    def test_amr_suite_green(self):
        code, out = self.run_suite("climb_intent_amr_tests.py")
        self.assertEqual(code, 0, out[-2000:])
        self.assertIn("RESULT: GREEN", out)
        self.assertEqual(out.count("[PASS]"), 4)
        self.assertNotIn("FIRED", out)


if __name__ == "__main__":
    unittest.main()
