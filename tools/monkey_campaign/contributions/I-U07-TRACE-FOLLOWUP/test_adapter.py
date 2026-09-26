"""test_adapter.py -- I-U07-TRACE-FOLLOWUP falsifiers, measured.

Card falsifier (brief): "The adapter uses a rewritten stand-in instead of the
accepted module, or claims native qualification from a fixture."  Operationalized
below (PREREGISTRATION.md frozen before implementation):

  F1  ACCEPTED MODULE   the adapter imports the sibling accepted input_trace.py
                        (merged PR #138); its bytes match the accepted sha256
                        pin; no vendored copy exists in this directory.
  F2  REAL SEAM         every input/command event derives from the pinned REAL
                        InputMapper/CommandRecord sources (reference/ pins
                        hash-asserted); payloads are the actual emitted records
                        (source "u01_input_mapper"); issued_tick matches the
                        mapper's own derivation (t_ms*300)//1000 exactly.
  F3  NO INVENTED       the adapter itself never emits a native stage; the
      NATIVE STAGE      camera harness yields an ordering fact (armed_after),
                        never a presentation timestamp; the mock's DECLARED
                        deadlines are never turned into timestamps.
  F4  NO FABRICATED     the Python-only 2-stage trace is REFUSED by the
      LATENCY           accepted module (missing_stage) with latency_output
                        null; fixture-completed chains are labeled fixtures and
                        claim nothing native.
  F5  P06 LAW           limits are caller data only; absent/empty limits give
                        unqualified through the adapter, never pass.
  F6  NO REGRESSION     the pinned existing seam suites (input_mapper_tests,
                        follow_camera_tests) and the accepted module's own 26
                        tests all pass unmodified; adapter runs are
                        deterministic and headless (import allowlist).

Run:  python -B test_adapter.py          (from this directory)
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import adapter as A                                          # noqa: E402

IT = A.load_accepted_trace_module()

# The accepted module's own pin (PR #138 head 4d2ececc bytes) -- the falsifier
# F1 reads this file's bytes, not its name.
SIBLING = HERE.parent / "I-U07-TRACE" / "input_trace.py"


class _Clock:
    """The injected monotonic integer-ms clock (the mapper's own contract),
    stepped at the seam's 50 ms decision interval so the mapper's boundaries
    actually fire (a held key RE-ISSUES every interval -- the R4 rule)."""

    def __init__(self, start=1000, step=50):
        self.t = start
        self.step = step

    def __call__(self):
        t = self.t
        self.t += self.step
        return t


def make_tracer(clock=None, **kw):
    return A.SeamTracer(clock=clock or _Clock(), clock_name="injected_ms",
                        run="run-fixture", build="build-fixture", **kw)


def run_walking_scenario(tr):
    """A scripted actual-play-shaped scenario ON THE SEAM (fixture driving,
    real mapper): press W, hold with steering, release with the decay tail,
    then S's live zero-advance target, then idle."""
    tr.press("W")                      # t=1000 input transition
    tr.tick()                          # t=1050 grid starts -> first record
    tr.press("A")                      # steering held alongside speed
    tr.tick()                          # yaw-carrying re-issue
    tr.tick()                          # held key re-issues (the R4 rule)
    tr.release("W")                    # the decay tail starts
    tr.tick()                          # decay sample v0*(1 - 50/100)
    tr.tick()                          # the deadline: EXACTLY 0.0
    tr.release("A")
    tr.press("S")                      # the LIVE ZERO-advance target
    tr.tick()
    tr.tick()
    tr.release_all()                   # everything off
    before = len(tr.causal_pairs())
    tr.tick()                          # idle: the grid dissolves, no record
    tr.tick()
    assert len(tr.causal_pairs()) == before, "idle emitted a record"
    return tr


# ── F1 the accepted module is imported, never vendored ────────────────────────
class TestAcceptedModuleIdentity(unittest.TestCase):

    def test_f1_imports_the_sibling_accepted_module(self):
        mod = A.load_accepted_trace_module()
        self.assertEqual(Path(mod.__file__).resolve(), SIBLING.resolve(),
                         "the adapter must import ../I-U07-TRACE/input_trace.py")
        self.assertIs(mod, IT)

    def test_f1_no_vendored_copy_in_this_contribution(self):
        self.assertFalse((HERE / "input_trace.py").exists(),
                         "a local copy of the accepted module is the falsifier")

    def test_f1_accepted_bytes_match_the_pr138_pin(self):
        import hashlib
        got = hashlib.sha256(SIBLING.read_bytes()).hexdigest()
        self.assertEqual(got, A.ACCEPTED_SHA256,
                         "the loaded module's bytes are not the accepted "
                         "PR #138 merge (4d2ececc)")

    def test_f1_stage_law_is_declared_from_the_accepted_module(self):
        self.assertEqual(tuple(IT.STAGES),
                         A.PYTHON_STAGES + A.NATIVE_STAGES)
        self.assertEqual(A.PYTHON_STAGES, ("input", "command_emitted"))
        self.assertEqual(A.NATIVE_STAGES, ("simulation_consumed", "presented"))


# ── F2 the events are the REAL seam's events ──────────────────────────────────
class TestRealSeamEvents(unittest.TestCase):

    def setUp(self):
        self.tr = run_walking_scenario(make_tracer())
        self.chains = self.tr.causal_pairs()
        self.events = self.tr.events()
        self.records = self.tr.inner_sink.records   # the ACTUAL emissions

    def test_f2_payloads_are_the_actual_emitted_records(self):
        self.assertEqual(len(self.chains), len(self.records))
        self.assertGreater(len(self.chains), 0)
        for chain, record in zip(self.chains, self.records):
            self.assertEqual(chain["record"], {
                "v_forward": record.v_forward,
                "yaw_rate": record.yaw_rate,
                "issued_tick": record.issued_tick,
                "source": record.source,
            })

    def test_f2_seam_identity_and_bounds_hold_on_every_chain(self):
        im = sys.modules["tools.monkey_campaign.product.input_mapper"]
        for chain in self.chains:
            rec = chain["record"]
            self.assertEqual(rec["source"], "u01_input_mapper")
            self.assertEqual(rec["source"], im.SOURCE_ID)
            self.assertGreaterEqual(rec["v_forward"], 0.0)
            self.assertLessEqual(rec["v_forward"], im.V_MAX_IN_BAND_M_S)
            self.assertLessEqual(abs(rec["yaw_rate"]), im.OMEGA_MAX_RAD_S)

    def test_f2_issued_tick_is_the_mappers_own_derivation(self):
        for chain in self.chains:
            self.assertEqual(chain["record"]["issued_tick"],
                             (chain["command_t_ms"] * 300) // 1000,
                             f"seq={chain['seq']}")

    def test_f2_causal_matching_on_one_injected_clock(self):
        for chain in self.chains:
            self.assertLessEqual(chain["antecedent"]["t_ms"],
                                 chain["command_t_ms"],
                                 f"seq={chain['seq']}: input after command")
            self.assertIn(chain["antecedent"]["kind"],
                          ("press", "release", "release_all"))
        for e in self.events:
            self.assertIsInstance(e["t"], int)
            self.assertEqual(e["unit"], "ms")
            self.assertEqual(e["clock"], "injected_ms")
            self.assertEqual(e["run"], "run-fixture")
            self.assertEqual(e["build"], "build-fixture")

    def test_f2_both_seam_states_and_bounds_are_traced(self):
        records = [c["record"] for c in self.chains]
        self.assertTrue(any(r["v_forward"] > 0.0 for r in records),
                        "the forward demand never reached the seam")
        self.assertTrue(any(r["v_forward"] == 0.0 for r in records),
                        "the live zero-advance state never reached the seam")
        self.assertTrue(any(abs(r["yaw_rate"]) > 0.0 for r in records),
                        "the carried yaw never reached the seam")

    def test_f2_decay_and_reissue_share_the_press_antecedent(self):
        # the re-issued commands lawfully share one press transition
        ante = [c["antecedent"]["transition_index"] for c in self.chains]
        self.assertEqual(ante[0], 0)
        self.assertGreaterEqual(len(set(ante)), 2,
                                "expected press- and release-antecedent chains")

    def test_f2_adapter_refuses_command_without_antecedent(self):
        tr = make_tracer()
        tr.boundary_t = 1000
        class _Fake:                      # never emitted by the real mapper here
            v_forward = 0.0; yaw_rate = 0.0; issued_tick = 300; source = "x"
        with self.assertRaises(A.SeamTraceRefused) as ctx:
            tr._record_command(_Fake())
        self.assertEqual(ctx.exception.reason, "command_without_input_antecedent")

    def test_f2_pinned_sources_are_byte_exact(self):
        for repo_path, want in A.PINNED_SHA256.items():
            import hashlib
            got = hashlib.sha256(
                (HERE / "reference" / repo_path).read_bytes()).hexdigest()
            self.assertEqual(got, want, repo_path)


# ── the adapter's own refusal laws (F6 clause) ─────────────────────────────────
class TestAdapterRefusals(unittest.TestCase):

    def test_f6_non_integer_clock_refused(self):
        with self.assertRaises(A.SeamTraceRefused) as ctx:
            tr = make_tracer(clock=lambda: 1000.5)
            tr.press("W")                  # the first clock read refuses
        self.assertEqual(ctx.exception.reason, "non_integer_clock")

    def test_f6_clock_regression_refused(self):
        vals = iter([1000, 1001, 999])
        with self.assertRaises(A.SeamTraceRefused) as ctx:
            tr = make_tracer(clock=lambda: next(vals))
            tr.press("W"); tr.release("W"); tr.press("S")
        self.assertEqual(ctx.exception.reason, "clock_regression")

    def test_f6_bad_identity_and_clock_refused(self):
        with self.assertRaises(A.SeamTraceRefused) as ctx:
            A.SeamTracer(clock=_Clock(), clock_name="", run="r", build="b")
        self.assertEqual(ctx.exception.reason, "bad_identity")
        with self.assertRaises(A.SeamTraceRefused) as ctx:
            A.SeamTracer(clock=5, clock_name="c", run="r", build="b")
        self.assertEqual(ctx.exception.reason, "bad_clock")

    def test_f6_python_stages_cannot_be_attached(self):
        tr = make_tracer()
        with self.assertRaises(A.SeamTraceRefused) as ctx:
            tr.attach_native_stage(0, "input", 1000)
        self.assertEqual(ctx.exception.reason, "not_a_native_stage")
        with self.assertRaises(A.SeamTraceRefused) as ctx:
            tr.attach_native_stage(99, "presented", 1000)
        self.assertEqual(ctx.exception.reason, "unknown_seq")


# ── F4/F5 the accepted law applied to the seam trace ───────────────────────────
class TestAcceptedLawOnSeamTrace(unittest.TestCase):

    def setUp(self):
        self.tr = run_walking_scenario(make_tracer())

    def test_f4_two_stage_trace_is_refused_missing_stage(self):
        result = self.tr.analyze()
        self.assertFalse(result["complete"])
        self.assertEqual(result["refused"], "missing_stage")
        self.assertEqual(sorted(result["details"]["missing"]),
                         ["presented", "simulation_consumed"])
        self.assertIsNone(result["latency_output"])
        self.assertNotIn("summary", result)

    def test_f4_refusal_output_carries_no_latency_numbers(self):
        text = json.dumps(self.tr.analyze())
        for banned in ("end_to_end_ms", "seg_", "p50_ms", "p95_ms", "mean_ms"):
            self.assertNotIn(banned, text)

    def test_f3_fixture_completed_chains_are_exact_and_labeled(self):
        FIXTURE = "fixture-planted-native (NOT native evidence)"
        chains = self.tr.causal_pairs()
        for c in chains:
            cmd_t = c["command_t_ms"]
            self.tr.attach_native_stage(c["seq"], "simulation_consumed",
                                        cmd_t + 5, {"note": FIXTURE})
            self.tr.attach_native_stage(c["seq"], "presented",
                                        cmd_t + 37, {"note": FIXTURE})
        result = self.tr.analyze()
        self.assertTrue(result["complete"])
        summary = result["summary"]
        self.assertEqual(summary["schema"], "chimera.input_trace.summary.v1")
        for chain_out, c in zip(summary["chains"], chains):
            seg_ic = c["command_t_ms"] - c["antecedent"]["t_ms"]
            self.assertEqual(chain_out["seg_input_to_command_ms"], seg_ic)
            self.assertEqual(chain_out["seg_command_to_consumed_ms"], 5.0)
            self.assertEqual(chain_out["seg_consumed_to_presented_ms"], 32.0)
            self.assertEqual(chain_out["end_to_end_ms"], seg_ic + 37.0)

    def test_f5_no_p06_limits_means_unqualified_through_the_adapter(self):
        for c in self.tr.causal_pairs():
            self.tr.attach_native_stage(c["seq"], "simulation_consumed",
                                        c["command_t_ms"] + 5)
            self.tr.attach_native_stage(c["seq"], "presented",
                                        c["command_t_ms"] + 37)
        q = self.tr.analyze()["summary"]["qualification"]
        self.assertEqual(q["status"], "unqualified")
        self.assertEqual(q["reason"], "p06_limits_absent")

    def test_f5_empty_limits_are_unqualified_too(self):
        for c in self.tr.causal_pairs():
            self.tr.attach_native_stage(c["seq"], "simulation_consumed",
                                        c["command_t_ms"] + 5)
            self.tr.attach_native_stage(c["seq"], "presented",
                                        c["command_t_ms"] + 37)
        q = self.tr.analyze(limits={})["summary"]["qualification"]
        self.assertEqual((q["status"], q["reason"]),
                         ("unqualified", "p06_limits_empty"))

    def test_f5_limits_are_caller_data_and_nothing_else(self):
        for c in self.tr.causal_pairs():
            self.tr.attach_native_stage(c["seq"], "simulation_consumed",
                                        c["command_t_ms"] + 5)
            self.tr.attach_native_stage(c["seq"], "presented",
                                        c["command_t_ms"] + 37)
        e2e = [c["end_to_end_ms"] for c in
               self.tr.analyze()["summary"]["chains"]]
        caller_cap = max(e2e)
        q_pass = self.tr.analyze(limits={"end_to_end_ms": caller_cap})
        q_fail = self.tr.analyze(limits={"end_to_end_ms": caller_cap - 1.0})
        self.assertEqual(q_pass["summary"]["qualification"]["status"], "pass")
        self.assertEqual(q_fail["summary"]["qualification"]["status"], "fail")
        # unknown limit keys refuse (the accepted module's own law, unchanged)
        result = self.tr.analyze(limits={"made_up_ms": 10.0})
        self.assertFalse(result["complete"])
        self.assertEqual(result["refused"], "unknown_limit_key")
        self.assertIsNone(result["latency_output"])


# ── F3 the camera test seam: ordering, never a timestamp ───────────────────────
class TestCameraSeamFacts(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root = A.materialize_pinned_seam()
        cls.root = root
        cls.saved_cwd = os.getcwd()
        os.chdir(root)
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        import tools.monkey_campaign.product.follow_camera_tests as fct
        cls.fct = fct

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.saved_cwd)

    def test_f3_freshness_contract_is_an_ordering_fact_without_a_timestamp(self):
        mock, _rec, fcam = self.fct.make_camera((self.fct.TRUNK,))
        wrote = False
        for _ in range(5):
            rep = fcam.tick()
            wrote = wrote or rep.wrote
        self.assertTrue(wrote, "scenario produced no camera write to arm /frame")
        acks_before = mock.ack_count
        status, body, _ct = mock.get("/frame")
        self.assertEqual(status, 200)
        doc = json.loads(body.decode())
        self.assertIn("armed_after", doc)
        self.assertGreaterEqual(doc["armed_after"], acks_before,
                                "the freshness contract broke")
        self.assertEqual(set(doc.keys()), {"armed_after"},
                         "the camera harness exposed a timestamp-like field")

    def test_f3_mock_deadlines_are_declared_not_measured(self):
        # They are the mock's DECLARED constants; this test pins that the
        # adapter never converts them into a `presented` timestamp.
        self.assertEqual(self.fct.MockEngine.APPLY_DEADLINE_S, 1.0 / 60.0)
        self.assertEqual(self.fct.MockEngine.FRAME_PERIOD_S, 1.0 / 30.0)
        tr = run_walking_scenario(make_tracer())
        stages = {e["stage"] for e in tr.events()}
        self.assertEqual(stages, set(A.PYTHON_STAGES),
                         "the adapter emitted a stage the seam cannot observe")

    def test_f4_camera_clock_domain_mixed_into_the_trace_refuses(self):
        # A REAL host-wall-clock reading from the camera harness' clock domain
        # (perf_counter), honestly measured but on a DIFFERENT clock identity:
        # merged into a seam trace it must refuse as mixed_clock -- the naive
        # "one trace from both harnesses" is exactly what the law forbids.
        camera_domain_t = time.perf_counter()      # the camera harness' clock
        events = run_walking_scenario(make_tracer()).events()
        merged = events + [{"seq": len(events) // 2, "stage": "presented",
                            "t": camera_domain_t, "unit": "s",
                            "clock": "perf_counter_host",
                            "run": "run-fixture", "build": "build-fixture",
                            "payload": {"note": "camera-harness clock domain "
                                                "(fixture merge probe)"}}]
        with self.assertRaises(IT.TraceRefused) as ctx:
            IT.parse_trace(merged)
        self.assertEqual(ctx.exception.reason, "mixed_clock")


# ── F6 determinism, headlessness, and no regression of the existing suites ─────
class TestDeterminismHeadlessRegression(unittest.TestCase):

    def test_f6_identical_runs_are_byte_identical(self):
        a = json.dumps(run_walking_scenario(make_tracer()).events(),
                       sort_keys=True).encode()
        b = json.dumps(run_walking_scenario(make_tracer()).events(),
                       sort_keys=True).encode()
        self.assertEqual(a, b)

    def test_f6_adapter_import_allowlist_is_headless(self):
        tree = ast.parse((HERE / "adapter.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imported.add((node.module or "").split(".")[0])
        allowed = {"__future__", "importlib", "shutil", "sys", "tempfile",
                   "pathlib", "typing", "hashlib"}
        self.assertEqual(imported, allowed,
                         "adapter.py imports outside the declared headless set")

    def test_f6_pinned_input_mapper_tests_still_green(self):
        root = A.materialize_pinned_seam()
        script = root / "tools/monkey_campaign/product/input_mapper_tests.py"
        proc = subprocess.run([sys.executable, "-B", str(script)],
                              capture_output=True, text=True, timeout=110)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("VERDICT: GREEN", proc.stdout)

    def test_f6_pinned_follow_camera_tests_still_green(self):
        root = A.materialize_pinned_seam()
        env = dict(os.environ, PYTHONPATH=str(root))
        proc = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "-q",
             "tools.monkey_campaign.product.follow_camera_tests"],
            capture_output=True, text=True, timeout=110, env=env, cwd=root)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("OK", proc.stderr)

    def test_f6_accepted_module_suite_still_green(self):
        proc = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "-q",
             "test_input_trace", "test_correction"],
            capture_output=True, text=True, timeout=110, cwd=str(SIBLING.parent))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("OK", proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
