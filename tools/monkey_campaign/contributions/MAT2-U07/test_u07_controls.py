#!/usr/bin/env python3
"""MAT2-U07: the NAMED-CHECK suite (the falsifier arms at the seam/unit
level) in the gate-visible test_*.py form (card-kit law).

Fast, analytic where possible; the certified-line machinery is exercised
through the SAME byte-verified extraction the driver uses. Every check is
named; skipped tests are NOT allowed (no KNOWN_SKIPS exists for this card).

Run:  python -B -m unittest test_u07_controls -v
(or through run_checks.py, which writes checks_receipt.json)
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", HERE / "outputs"))


def setUpModule():
    global vi7, ch, cv
    import verify_inputs_u07 as _vi7
    vi7 = _vi7
    vi7.verify()
    vi7.verify_registry()
    vi7.extract_u07_tree()
    vi7.w10_layer()
    import controls_harness as _ch
    ch = _ch
    import camera_views as _cv
    cv = _cv


class TraceLawChecks(unittest.TestCase):
    """The accepted module's law re-proven on tampered fixtures (P12)."""

    def _accepted(self):
        it, ad = ch.load_accepted_modules()
        return it, ad

    def _events(self, n_chains=3, presented=True):
        it, ad = self._accepted()
        tracer = ad.SeamTracer(clock=lambda: 0, clock_name="injected_ms",
                               run="checks/run", build=ch.BUILD_ID)
        out = []
        for seq in range(n_chains):
            base = {
                "seq": seq, "unit": "ms", "clock": "injected_ms",
                "run": "checks/run", "build": ch.BUILD_ID,
            }
            out.append({**base, "stage": "input", "t": 1000 + 50 * seq,
                        "payload": {"transition_index": seq, "kind": "press",
                                    "key": "W", "action": None}})
            out.append({**base, "stage": "command_emitted",
                        "t": 1000 + 50 * seq,
                        "payload": {"v_forward": 0.5, "yaw_rate": 0.0,
                                    "issued_tick": 300 + 15 * seq,
                                    "source": "checks"}})
            out.append({**base, "stage": "simulation_consumed",
                        "t": 1003 + 50 * seq,
                        "payload": {"consumed_tick": 301 + 15 * seq,
                                    "issued_tick": 300 + 15 * seq}})
            if presented:
                out.append({**base, "stage": "presented",
                            "t": 1455 + 50 * seq,
                            "payload": {"frame_id": "checks",
                                        "presented_tick": 435 + 15 * seq}})
        return it, out

    def test_mixed_clock_refused(self):
        it, events = self._events()
        events[3]["clock"] = "wall_clock_probe"
        with self.assertRaises(it.TraceRefused) as cm:
            it.parse_trace(events)
        self.assertEqual(cm.exception.reason, "mixed_clock")

    def test_missing_stage_refused(self):
        it, events = self._events(presented=False)
        with self.assertRaises(it.TraceRefused) as cm:
            it.parse_trace(events)
        self.assertEqual(cm.exception.reason, "missing_stage")

    def test_reversed_stage_refused(self):
        it, events = self._events()
        # the same-boundary input/command pair is NOT reversed (equal t is
        # lawful); tamper the command time BELOW its input instead.
        events[1]["t"] = events[0]["t"] - 1
        with self.assertRaises(it.TraceRefused) as cm:
            it.parse_trace(events)
        self.assertEqual(cm.exception.reason, "reversed_stage_order")

    def test_unqualified_without_limits(self):
        it, events = self._events()
        parsed = it.parse_trace(events)
        summary = it.summarize(parsed, limits=None)
        self.assertEqual(summary["qualification"]["status"], "unqualified")
        self.assertEqual(summary["qualification"]["reason"],
                         "p06_limits_absent")

    def test_cadence_limit_is_caller_data(self):
        it, events = self._events()
        parsed = it.parse_trace(events)
        summary = it.summarize(parsed, limits={"seg_input_to_command_ms": 50.0})
        self.assertEqual(summary["qualification"]["status"], "pass")
        with self.assertRaises(it.TraceRefused) as cm:
            it.summarize(parsed, limits={"end_to_end_guess": 1.0})
        self.assertEqual(cm.exception.reason, "unknown_limit_key")


class OcclusionGeometryChecks(unittest.TestCase):
    """The declared obstruction probe numerics (P9)."""

    def test_declared_ray_hits_declared_box(self):
        eye = tuple(cv.U07_VIEWS["C_V2_obstructed"]["position"])
        target = tuple(cv.U07_VIEWS["C_V2_obstructed"]["target"])
        hit, t0, t1 = cv.seg_box_intersect(eye, target, cv.OCCLUDER)
        self.assertTrue(hit)
        self.assertLess(t1, 1.0)
        self.assertLessEqual(t0, t1)

    def test_shifted_box_misses(self):
        eye = tuple(cv.U07_VIEWS["C_V2_obstructed"]["position"])
        target = tuple(cv.U07_VIEWS["C_V2_obstructed"]["target"])
        box = {"x": [5.0, 6.0], "y": [0.5, 1.0], "z": [0.4, 0.8]}
        hit, _t0, _t1 = cv.seg_box_intersect(eye, target, box)
        self.assertFalse(hit)

    def test_hull_containment_law(self):
        hull = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
        self.assertTrue(cv.point_in_hull((0.0, 0.0), hull))
        self.assertFalse(cv.point_in_hull((2.0, 0.0), hull))


class SeamLawChecks(unittest.TestCase):
    """The REAL seam: expiry, focus drops and release law (R4/R5 laws)."""

    def test_expiry_constant_is_pinned(self):
        from tools.monkey_campaign.product.input_mapper import EXPIRY_TICKS
        self.assertEqual(EXPIRY_TICKS, 30)

    def test_focus_window_law(self):
        import verify_inputs_u07 as v
        fp_path = v.PINNED_ROOT.joinpath(
            "tools", "monkey_campaign", "contributions", "MAT2-U02",
            "reference", "tools", "monkey_campaign", "product",
            "focus_policy.py")
        self.assertTrue(fp_path.exists())
        import importlib.util
        import sys as _sys
        from tools.monkey_campaign.product import input_mapper as pinned_im
        _sys.modules.setdefault("input_mapper", pinned_im)
        from tools.monkey_campaign.product.input_mapper import InputMapper
        spec = importlib.util.spec_from_file_location("u07_fp_checks",
                                                      fp_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["u07_fp_checks"] = mod
        spec.loader.exec_module(mod)
        sink = ch.RecordingSink()
        tick_holder = [300]   # the caller's tick source rides the harness law
        policy = mod.FocusPolicy(
            sink=sink,
            mapper_factory=lambda gate: InputMapper(
                gate, tick_source=lambda: tick_holder[0]))
        policy.press("W", now_ms=1000)
        emitted = policy.tick(1000)
        self.assertGreaterEqual(len(sink.records), 1)
        policy.on_blur(now_ms=2000)        # release_all: the decay runs
        for t, ms in ((315, 1050), (330, 1100), (345, 1150)):
            tick_holder[0] = t
            policy.tick(ms)
        policy.press("S", now_ms=3000)     # blurred intent: dropped, named
        self.assertEqual(policy.state, mod.BLURRED)
        self.assertGreaterEqual(
            len(policy.last_trace.get("dropped_blurred", [])), 1)
        policy.on_focus(now_ms=4000)
        tick_holder[0] = 1500
        policy.press("S", now_ms=5000)     # recovery: a NEW accepted intent
        policy.tick(5000)
        records = sink.records
        self.assertGreaterEqual(len(records), 2)
        self.assertEqual(
            len([r for r in records if r.issued_tick >= 1500]), 1)

    def test_wrong_command_response_detection(self):
        import types
        fake_cm = types.SimpleNamespace(WRONG_INJECT_TICK=5430)
        r1 = {"decisions": [{"issued_tick": 5500, "v_forward_m_s": 0.0,
                             "wrong_script": False}]}
        r3 = {"decisions": [{"issued_tick": 5500, "v_forward_m_s": 0.763625,
                             "wrong_script": True}]}
        got = ch.wrong_command_response(r1, r3)
        self.assertTrue(got["r3_all_wrong_flagged"])
        self.assertTrue(got["r3_demand_positive"])


if __name__ == "__main__":
    unittest.main()
