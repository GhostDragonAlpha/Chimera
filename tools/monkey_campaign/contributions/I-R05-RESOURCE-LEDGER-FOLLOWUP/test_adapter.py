"""test_adapter.py -- I-R05-RESOURCE-LEDGER-FOLLOWUP: bounded restart/close
tests connecting the ACCEPTED resource ledger to the EXISTING session teardown
hooks (pinned session_flow.py / forest_loader.py at 9afbddcd).

PREREGISTRATION.md (frozen BEFORE this file) predicts:
  P1 the adapter imports the ACCEPTED ledger bytes (sha256 05cf6218...) and
     the existing session_flow_tests suite runs green on the pinned hooks;
  P2 restart/exit close exactly the generations the frozen transitions end;
  P3 a deliberate unreleased resource is named ledger_live_at_close and FAILS
     its cycle, not launderable by any ceiling;
  P4 a wrong-generation release claim is recorded (ledger_wrong_generation)
     and leaves the current record live and releasable by its true generation;
  P5 the ForestScene mirror keeps the scene's zero-live audit and the ledger's
     live ids in agreement, and a raising release leaves a named leak;
  P6 the suite is green CPU-only well under 120 s; the adapter has no process
     discovery/termination, no wall clock, no network.

Falsifiers: F1 stand-in instead of accepted module; F2 a leak passes;
F3 a wrong-generation claim mutates the current record; F4 a production edit;
F5 a native/VRAM qualification claim (none is made anywhere).

Run:  python -B -m unittest -v test_adapter      (CPU-only, stdlib only)
"""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import adapter                                                  # noqa: E402
from adapter import (                                           # noqa: E402
    AdapterRefusal, ACCEPTED_RESOURCE_LEDGER_SHA256, LedgeredForestScene,
    LedgeredSessionFlow, PINNED_HOOK_SHA256, REFERENCE_ROOT,
    forest_loader, resource_ledger, session_flow,
)

ACCEPTED_SHA = "05cf62184931d6443188cd9b72aa9e88821cc8a9063a351a7e4d658d6690da6c"
SESSION_FLOW_SHA = PINNED_HOOK_SHA256["tools/monkey_campaign/product/session_flow.py"]
FOREST_LOADER_SHA = PINNED_HOOK_SHA256["tools/monkey_campaign/data/monkey_forest/forest_loader.py"]

LIVE_AT_CLOSE = resource_ledger.LIVE_AT_CLOSE
WRONG_GENERATION = resource_ledger.WRONG_GENERATION
WRONG_OWNER = resource_ledger.WRONG_OWNER


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ── world doubles: the pinned module's own, plus one raising resource ───────────
class _BoomResource:
    """A registered resource whose release RAISES (the f08_teardown_leak path)."""

    def release(self):
        raise RuntimeError("release failed")


class _FakeLedger:
    """A duck-typed stand-in: MUST be refused everywhere (falsifier F1)."""

    def __init__(self):
        self.calls = []

    def acquire(self, *a, **k):
        self.calls.append(("acquire", a, k))

    def release(self, *a, **k):
        self.calls.append(("release", a, k))

    def close_generation(self, *a, **k):
        self.calls.append(("close_generation", a, k))

    def close(self, *a, **k):
        self.calls.append(("close", a, k))


def make_flow(teardown=None, restart=None, ledger=None, ceilings=None):
    """The existing teardown-test wiring: a REAL SessionFlow subclass over the
    pinned module's own doubles, injected exactly as the live wiring will
    (world.boot / world.shutdown_engine as bound methods)."""
    mapper = session_flow.CountingMapper()
    restart = restart if restart is not None else session_flow.RecordingRestart()
    teardown = teardown if teardown is not None else session_flow.TeardownDouble()
    flow = LedgeredSessionFlow(mapper, restart.boot, teardown.shutdown_engine,
                               ledger=ledger, ceilings=ceilings)
    return flow, mapper, restart, teardown


def play_and_pause(flow, t0=0):
    flow.key("Return", down=1, now_ms=t0)            # attract -> playing
    flow.key("Escape", down=1, now_ms=t0 + 10)       # playing -> paused


def forest_objects(clearing=None):
    """Synthetic scene inputs: ForestScene validates nothing at construction;
    only the teardown contract runs (the forest DATA pipeline is not under
    test here and no native qualification is claimed from these fixtures)."""
    return {
        "clearing": clearing if clearing is not None else {"kind": "clearing"},
        "terrain": {"kind": "terrain"},
        "trunk": {"kind": "trunk"},
        "routes": {"kind": "routes"},
    }


class _RecordingShutdown:
    """The declared shutdown referent, recorded (terminate -> wait -> kill)."""

    def __init__(self):
        self.calls = []

    def __call__(self):
        self.calls.extend(["terminate", "wait", "kill"])
        return True


# ── P1/F1: the accepted source is really the module in use ──────────────────────
class TestAcceptedSourceIdentity(unittest.TestCase):
    def test_imported_ledger_is_the_accepted_module(self):
        self.assertEqual(adapter.RESOURCE_LEDGER_SHA256, ACCEPTED_SHA)
        self.assertEqual(adapter.ACCEPTED_RESOURCE_LEDGER_SHA256, ACCEPTED_SHA)
        # independent re-hash of the file the import actually loaded
        self.assertEqual(_sha(adapter.RESOURCE_LEDGER_SOURCE_PATH), ACCEPTED_SHA)
        self.assertEqual(resource_ledger.SCHEMA,
                         "chimera.monkey_campaign.resource_ledger.v1")
        self.assertIs(adapter.ResourceLedger, resource_ledger.ResourceLedger)
        self.assertIsInstance(make_flow()[0].ledger, resource_ledger.ResourceLedger)

    def test_pinned_hooks_are_the_extracted_bytes(self):
        self.assertEqual(_sha(Path(session_flow.__file__)), SESSION_FLOW_SHA)
        self.assertEqual(_sha(Path(forest_loader.__file__)), FOREST_LOADER_SHA)
        mapper = sys.modules["tools.monkey_campaign.product.input_mapper"]
        command = sys.modules["tools.science_funnel.typeb_export.command_record"]
        self.assertEqual(
            _sha(Path(mapper.__file__)),
            PINNED_HOOK_SHA256["tools/monkey_campaign/product/input_mapper.py"])
        self.assertEqual(
            _sha(Path(command.__file__)),
            PINNED_HOOK_SHA256["tools/science_funnel/typeb_export/command_record.py"])

    def test_extraction_ledger_agrees_with_disk(self):
        doc = json.loads(
            (REFERENCE_ROOT / "EXTRACTION_LEDGER.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["schema"], "chimera.monkey_campaign.extraction_ledger.v1")
        seen = set()
        for entry in doc["files"]:
            path = REFERENCE_ROOT / entry["path"]
            self.assertEqual(_sha(path), entry["sha256"], entry["path"])
            self.assertEqual(path.stat().st_size, entry["bytes"], entry["path"])
            seen.add(entry["path"])
        for rel in PINNED_HOOK_SHA256:
            self.assertIn(rel, seen)
        self.assertIn("resource_ledger.py", seen)

    def test_drift_guard_refuses_by_name(self):
        with self.assertRaises(AdapterRefusal) as caught:
            adapter._verify_file(Path(adapter.RESOURCE_LEDGER_SOURCE_PATH),
                                 "0" * 64, "adapter_accepted_source_drift")
        self.assertEqual(caught.exception.code, "adapter_accepted_source_drift")

    def test_adapter_source_has_no_governor_tokens(self):
        # AST check: the adapter's COMPLETE import set is exactly this -- no
        # process control, no clocks, no network transport can be reached
        import ast
        tree = ast.parse((_HERE / "adapter.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
        allowed = {"__future__", "hashlib", "importlib.util",
                   "sys", "pathlib"}
        self.assertEqual(imported, allowed,
                         "adapter must import nothing beyond stdlib plumbing")
        # and no governor identifier is even spelled anywhere
        source = (_HERE / "adapter.py").read_text(encoding="utf-8")
        for token in ("psutil", "subprocess", "ctypes", "socket", "urllib",
                      "taskkill", "TerminateProcess", "OpenProcess",
                      "EnumProcesses", "os.kill", "perf_counter",
                      "monotonic", "datetime", "urlopen", "Popen"):
            self.assertNotIn(token, source, token)


class TestStandInRefusal(unittest.TestCase):
    """F1: a duck-typed ledger stand-in is refused at both adapters."""

    def test_session_flow_refuses_fake_ledger(self):
        mapper = session_flow.CountingMapper()
        with self.assertRaises(AdapterRefusal) as caught:
            LedgeredSessionFlow(mapper, session_flow.RecordingRestart().boot,
                                session_flow.TeardownDouble().shutdown_engine,
                                ledger=_FakeLedger())
        self.assertEqual(caught.exception.code, "adapter_ledger_type")

    def test_forest_scene_refuses_fake_ledger(self):
        with self.assertRaises(AdapterRefusal) as caught:
            LedgeredForestScene(forest_objects(), object(), {}, {},
                                ledger=_FakeLedger())
        self.assertEqual(caught.exception.code, "adapter_ledger_type")

    def test_bad_ceilings_refused(self):
        with self.assertRaises(AdapterRefusal):
            make_flow(ceilings=["max_live", 4])         # not a mapping
        # an unknown ceiling KEY is refused by the ACCEPTED ledger at close
        # time -- a loud stop, never a silently disabled limit
        flow, _, _, _ = make_flow(ceilings={"not_a_ceiling": 1})
        play_and_pause(flow)
        with self.assertRaises(resource_ledger.LedgerRefusal) as caught:
            flow.key("Q", down=1, now_ms=30)
        self.assertEqual(caught.exception.code, "ledger_bad_ceiling")


# ── P2: restart/exit close exactly the generations the transitions end ──────────
class TestRestartClose(unittest.TestCase):
    def test_clean_two_generation_session_with_restart_close(self):
        flow, _, restart, teardown = make_flow()
        play_and_pause(flow)
        flow.acquire("engine:9347", now_ms=1)
        flow.acquire("scene:forest", now_ms=2)
        flow.release("scene:forest", now_ms=3)
        flow.release("engine:9347", now_ms=4)
        flow.key("R", down=1, now_ms=20)               # paused -> boot -> playing
        self.assertEqual(flow.generation, 1)
        receipt = flow.last_trace["restart_leaks"][-1]
        self.assertEqual(receipt["closed_generation"], 0)
        self.assertTrue(receipt["passed"])
        self.assertEqual(receipt["live_at_close"], 0)
        flow.acquire("engine:9350", now_ms=21)
        flow.release("engine:9350", now_ms=22)
        flow.key("Q", down=1, now_ms=30)               # exit from playing
        self.assertEqual(flow.state, session_flow.EXITED)
        self.assertEqual(teardown.calls, ["terminate", "wait", "kill"])
        self.assertEqual(len(teardown.calls), 3)        # exactly one teardown
        self.assertIsNotNone(flow.exit_summary)
        self.assertTrue(flow.exit_summary["passed"])
        self.assertEqual(flow.exit_summary["live_now"], 0)
        self.assertEqual(flow.last_trace["exit_leaks"][-1]["closed_generation"], 1)

    def test_generation_mirrors_boot_count(self):
        flow, _, restart, _ = make_flow()
        play_and_pause(flow)
        flow.key("R", down=1, now_ms=20)
        flow.key("Escape", down=1, now_ms=30)
        flow.key("R", down=1, now_ms=40)
        self.assertEqual(flow.generation, 2)
        self.assertEqual(restart.calls, [("boot",), ("boot",)])
        closes = [e for e in flow.ledger.events()
                  if e["kind"] == "generation_close"]
        self.assertEqual([e["generation"] for e in closes], [0, 1])

    def test_exit_releases_session_owned_and_closes_clean(self):
        flow, _, _, teardown = make_flow()
        play_and_pause(flow)
        flow.acquire("engine:9347", now_ms=1)
        flow.acquire("scene:forest", now_ms=2)
        flow.key("Q", down=1, now_ms=30)               # nothing released by hand
        self.assertTrue(flow.exit_summary["passed"])
        self.assertEqual(flow.exit_summary["live_now"], 0)
        self.assertEqual(teardown.calls, ["terminate", "wait", "kill"])
        releases = [e for e in flow.ledger.events() if e["kind"] == "release"]
        self.assertEqual([e["resource_id"] for e in releases],
                         ["scene:forest", "engine:9347"])   # reverse-acquire order

    def test_restart_leak_named_when_session_resource_unreleased(self):
        # a DELIBERATE UNRELEASED resource across restart (P3, flavor 1)
        flow, _, _, _ = make_flow()
        play_and_pause(flow)
        flow.acquire("engine:9347", now_ms=1)          # never released
        flow.key("R", down=1, now_ms=20)
        receipt = flow.last_trace["restart_leaks"][-1]
        self.assertFalse(receipt["passed"])
        self.assertEqual(receipt["live_at_close"], 1)
        self.assertEqual(receipt["leak_ids"], ["engine:9347"])
        self.assertEqual(flow.generation, 1)           # the boot still happened
        gen0 = flow.ledger.summary(generation=0)
        self.assertFalse(gen0["passed"])
        self.assertEqual(gen0["failures_by_code"][LIVE_AT_CLOSE], 1)

    def test_exit_deliberate_unreleased_operator_resource_fails_cycle(self):
        # a DELIBERATE UNRELEASED resource at exit (P3, flavor 2): the
        # operator-owned id is beyond the session's reach (F1 of the parent)
        flow, _, _, _ = make_flow()
        play_and_pause(flow)
        flow.acquire("operator:notebook", owner="operator", now_ms=1)
        flow.key("Q", down=1, now_ms=30)
        self.assertFalse(flow.exit_summary["passed"])
        self.assertEqual(flow.exit_summary["live_now"], 0)   # abandoned at close
        self.assertEqual(flow.exit_summary["failures_by_code"][LIVE_AT_CLOSE], 1)
        leaks = flow.last_trace["exit_leaks"][-1]
        self.assertEqual(leaks["leak_ids"], ["operator:notebook"])

    def test_leak_not_launderable_by_ceiling(self):
        flow, _, _, _ = make_flow(ceilings={"max_failures": 1000,
                                            "max_live": 100})
        play_and_pause(flow)
        flow.acquire("operator:notebook", owner="operator", now_ms=1)
        flow.key("Q", down=1, now_ms=30)
        self.assertFalse(flow.exit_summary["passed"])
        self.assertEqual(flow.exit_summary["failures_by_code"][LIVE_AT_CLOSE], 1)

    def test_ceilings_flow_through_adapter_closes(self):
        flow, _, _, _ = make_flow(ceilings={"max_acquires": 1})
        play_and_pause(flow)
        flow.acquire("engine:9347", now_ms=1)
        flow.acquire("scene:forest", now_ms=2)
        flow.release("scene:forest", now_ms=3)
        flow.release("engine:9347", now_ms=4)
        flow.key("R", down=1, now_ms=20)
        receipt = flow.last_trace["restart_leaks"][-1]
        self.assertFalse(receipt["passed"])            # 2 acquires > ceiling 1
        closed = flow.restart_summaries[0]["summary"]  # the close-time summary
        self.assertEqual(closed["ceiling_violations"],
                         [{"ceiling": "max_acquires", "measured": 2, "limit": 1}])

    def test_wrong_owner_keeps_record_live_until_close(self):
        flow, _, _, _ = make_flow()
        play_and_pause(flow)
        flow.acquire("operator:notebook", owner="operator", now_ms=1)
        event = flow.release("operator:notebook", now_ms=2)   # session claims it
        self.assertEqual(event["code"], WRONG_OWNER)
        self.assertEqual(flow.live_ids(), ["operator:notebook"])   # untouched
        released = flow.release("operator:notebook", owner="operator", now_ms=3)
        self.assertEqual(released["kind"], "release")  # its owner CAN release it
        flow.key("Q", down=1, now_ms=30)
        # no leak: the owner released it -- but the refused wrong-owner claim
        # stays in the ledger as evidence and fails the default (zero-budget)
        # cycle.  Named evidence is never free.
        self.assertEqual(flow.exit_summary["failures_by_code"][WRONG_OWNER], 1)
        self.assertEqual(flow.exit_summary["failures_by_code"][LIVE_AT_CLOSE], 0)
        self.assertFalse(flow.exit_summary["passed"])

    def test_second_exit_is_a_named_drop_and_reaccounts_nothing(self):
        flow, _, _, teardown = make_flow()
        play_and_pause(flow)
        flow.key("Q", down=1, now_ms=30)
        first_summary, first_events = flow.exit_summary, len(flow.ledger.events())
        first_trace = list(flow.last_trace["exit_leaks"])
        flow.key("Q", down=1, now_ms=40)
        self.assertIs(flow.state, session_flow.EXITED)
        self.assertEqual(len(teardown.calls), 3)        # still exactly one
        self.assertEqual(len(flow.ledger.events()), first_events)
        self.assertIs(flow.exit_summary, first_summary)
        self.assertEqual(flow.last_trace["exit_leaks"], first_trace)

    def test_raising_teardown_records_nothing_and_closes_nothing(self):
        class _OnceBoom(session_flow.TeardownDouble):
            def __init__(self):
                super().__init__()
                self.boomed = False

            def shutdown_engine(self):
                if not self.boomed:
                    self.boomed = True
                    raise RuntimeError("engine stuck")
                super().shutdown_engine()

        teardown = _OnceBoom()
        flow, _, _, _ = make_flow(teardown=teardown)
        play_and_pause(flow)
        flow.acquire("engine:9347", now_ms=1)
        flow.key("Q", down=1, now_ms=30)               # teardown raises
        self.assertEqual(flow.state, session_flow.PAUSED)   # no false exit claim
        self.assertIn("exit_failed", flow.last_trace)
        self.assertIsNone(flow.exit_summary)            # nothing closed ...
        self.assertFalse(any(e["kind"] == "generation_close"
                             for e in flow.ledger.events()))
        self.assertEqual(flow.live_ids(), ["engine:9347"])  # ... nothing claimed
        flow.key("Q", down=1, now_ms=40)               # a real teardown then does
        self.assertEqual(flow.state, session_flow.EXITED)
        self.assertTrue(flow.exit_summary["passed"])
        self.assertEqual(teardown.calls[-3:], ["terminate", "wait", "kill"])

    def test_raising_restart_closes_nothing(self):
        flow, _, restart, _ = make_flow(
            restart=session_flow.RecordingRestart(error=RuntimeError("no boot")))
        play_and_pause(flow)
        flow.acquire("engine:9347", now_ms=1)
        flow.key("R", down=1, now_ms=20)
        self.assertIn("restart_failed", flow.last_trace)
        self.assertEqual(flow.generation, 0)            # the old scene is still it
        self.assertFalse(any(e["kind"] == "generation_close"
                             for e in flow.ledger.events()))
        self.assertEqual(flow.live_ids(), ["engine:9347"])
        self.assertEqual(restart.calls, [("boot",)])


# ── P4/F3: a stale generation cannot close a current resource ───────────────────
class TestWrongGenerationRelease(unittest.TestCase):
    def test_stale_claim_refused_and_current_record_untouched(self):
        flow, _, _, _ = make_flow()
        play_and_pause(flow)
        flow.key("R", down=1, now_ms=20)               # now generation 1
        flow.acquire("scene:forest", now_ms=21)
        event = flow.release("scene:forest", generation=0, now_ms=22)
        self.assertEqual(event["code"], WRONG_GENERATION)
        self.assertEqual(flow.live_ids(), ["scene:forest"])   # untouched
        event = flow.release("scene:forest", generation=1, now_ms=23)
        self.assertEqual(event["kind"], "release")      # true generation works
        flow.key("Q", down=1, now_ms=30)
        self.assertTrue(flow.exit_summary["passed"])

    def test_stale_claim_leaves_a_named_failure_not_a_close(self):
        flow, _, _, _ = make_flow()
        play_and_pause(flow)
        flow.acquire("engine:9347", now_ms=1)
        event = flow.release("engine:9347", generation=5, now_ms=2)
        self.assertEqual(event["code"], WRONG_GENERATION)
        self.assertEqual(flow.live_ids(), ["engine:9347"])    # NOT closed by it
        flow.key("Q", down=1, now_ms=30)   # exit releases it by the TRUE generation
        # the failure event carries the CLAIM's generation (5), so it lives at
        # whole-ledger scope -- where the default zero budget makes the ledger
        # FAIL.  Named evidence is never laundered by scope.
        whole = flow.ledger.summary()
        self.assertEqual(whole["failures_by_code"][WRONG_GENERATION], 1)
        self.assertEqual(whole["failures_by_code"][LIVE_AT_CLOSE], 0)
        self.assertFalse(whole["passed"])


# ── P5: the ForestScene mirror (proposal B) ─────────────────────────────────────
class TestForestSceneMirror(unittest.TestCase):
    def test_registration_mirrors_and_clean_teardown_agrees(self):
        ledger = resource_ledger.ResourceLedger()
        shutdown = _RecordingShutdown()
        scene = LedgeredForestScene(forest_objects(), object(),
                                    {"scene_seed": 4598321}, {},
                                    engine_shutdown=shutdown,
                                    ledger=ledger, generation=5)
        self.assertEqual(scene.mirror_ids(), [
            "forest:clearing", "forest:engine_shutdown",
            "forest:initial_state", "forest:routes", "forest:terrain",
            "forest:terrain_surface", "forest:trunk"])
        self.assertEqual(len(ledger.live(5)), 7)
        receipt = scene.teardown()                      # the scene's own teardown
        self.assertFalse(receipt["already_torn_down"])
        self.assertEqual(receipt["released"], [
            "engine_shutdown", "initial_state", "terrain_surface", "routes",
            "trunk", "terrain", "clearing"])            # reverse-load order
        self.assertEqual(shutdown.calls, ["terminate", "wait", "kill"])  # engine FIRST
        self.assertEqual(receipt["live_after"], [])     # the scene's own audit ...
        self.assertEqual(ledger.live(5), [])            # ... agrees with the ledger
        summary = ledger.close_generation(5)
        self.assertTrue(summary["passed"])
        self.assertEqual(summary["acquires"], 7)
        self.assertEqual(summary["releases"], 7)

    def test_raising_release_stays_live_and_close_names_exact_id(self):
        ledger = resource_ledger.ResourceLedger()
        scene = LedgeredForestScene(forest_objects(clearing=_BoomResource()),
                                    object(), {}, {}, ledger=ledger,
                                    generation=0)
        with self.assertRaises(forest_loader.Refusal) as caught:
            scene.teardown()
        self.assertEqual(caught.exception.code, "f08_teardown_leak")
        self.assertEqual(scene.live_resources(), ["clearing"])
        self.assertEqual([r.resource_id for r in ledger.live(0)],
                         ["forest:clearing"])           # the record stays live
        summary = ledger.close_generation(0)
        self.assertFalse(summary["passed"])             # the leak FAILS the cycle
        self.assertEqual([d["resource_id"] for d in summary["failure_details"]
                          if d["code"] == LIVE_AT_CLOSE],
                         ["forest:clearing"])

    def test_second_teardown_is_a_noop_and_reaccounts_nothing(self):
        ledger = resource_ledger.ResourceLedger()
        scene = LedgeredForestScene(forest_objects(), object(), {}, {},
                                    ledger=ledger, generation=0)
        first = scene.teardown()
        events = len(ledger.events())
        second = scene.teardown()
        self.assertTrue(second["already_torn_down"])
        self.assertEqual(second["released"], [])
        self.assertEqual(len(ledger.events()), events)   # no mirror on the no-op

    def test_session_owner_scoping(self):
        ledger = resource_ledger.ResourceLedger()
        scene = LedgeredForestScene(forest_objects(), object(), {}, {},
                                    ledger=ledger, generation=3, owner="session")
        records = {r.resource_id: r for r in ledger.live(3)}
        self.assertTrue(records)
        for record in records.values():
            self.assertEqual(record.owner, "session")
            self.assertEqual(record.generation, 3)


# ── P6: determinism ──────────────────────────────────────────────────────────────
class TestDeterminism(unittest.TestCase):
    def test_identical_histories_byte_identical_summaries(self):
        digests = []
        for _ in range(2):
            flow, _, _, _ = make_flow()
            play_and_pause(flow)
            flow.acquire("engine:9347", now_ms=1)
            flow.key("R", down=1, now_ms=20)            # leak named at restart
            flow.acquire("engine:9350", now_ms=21)
            flow.key("Q", down=1, now_ms=30)            # gen 1 clean
            receipt = flow.last_trace["restart_leaks"][-1]
            digests.append(hashlib.sha256(
                resource_ledger.canonical_json(receipt)).hexdigest())
            digests.append(hashlib.sha256(
                resource_ledger.canonical_json(flow.exit_summary)).hexdigest())
        self.assertEqual(digests[0], digests[2])
        self.assertEqual(digests[1], digests[3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
