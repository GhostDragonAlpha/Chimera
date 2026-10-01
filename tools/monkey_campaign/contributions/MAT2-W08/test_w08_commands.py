#!/usr/bin/env python3
"""MAT2-W08 named-check suite (prereg section 7).

Every FB arm carries a clean control AND a bite: the detector must stay
green on the clean run and must FIRE on the tampered input (a falsifier
that cannot fail is refused by the house standard). The heavy shared
fixture (pins -> gate -> load -> R1/R2/R3 -> evaluate) runs ONCE per suite
and is cached; the bites are pure arithmetic on synthetic rows or on the
cached objects.
"""
from __future__ import annotations

import ast
import copy
import json
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi            # noqa: E402
import command_model as cm            # noqa: E402
import run_command_verification as rc  # noqa: E402

_FIXTURE = {}


def fixture():
    """The clean pipeline, run once: pins -> gate -> load -> R1/R2/R3 ->
    evaluate. The gate ORDER itself is under test (test_02)."""
    if _FIXTURE:
        return _FIXTURE
    pins, reg = rc.stage_pins()
    (cert, req, allow, bundle, build_id, params,
     scene_const, bounds, gate) = rc.gate_and_load()
    adapter = cm.CommandAdapter(bundle["manifest"], scene_const)
    res1 = rc.run_commanded(adapter, build_id, params, horizon=rc.HORIZON_R1)
    adapter2 = cm.CommandAdapter(bundle["manifest"], scene_const)
    res2 = rc.run_commanded(adapter2, build_id, params, horizon=rc.HORIZON_R1)
    adapter3 = cm.CommandAdapter(bundle["manifest"], scene_const)
    res3 = rc.run_commanded(adapter3, build_id, params, wrong_override=True,
                            horizon=rc.HORIZON_R3)
    ev = rc.evaluate(res1, res2, res3, bounds, gate)
    _FIXTURE.update(pins=pins, reg=reg, cert=cert, req=req, allow=allow,
                    bundle=bundle, build_id=build_id, params=params,
                    scene_const=scene_const, bounds=bounds, gate=gate,
                    res1=res1, res2=res2, res3=res3, ev=ev)
    return _FIXTURE


# ---- isolated detectors (the bite targets; clean rows pass, bites fire) ----

def bounds_detector(rows):
    """Every applied channel within the manifest bounds (FB3)."""
    bad = []
    for row in rows:
        for ch, val in enumerate(row["applied"]):
            if not (row["lo"][ch] - 1e-9 <= val <= row["hi"][ch] + 1e-9):
                bad.append((row.get("tick", 0), ch))
    return bad


def envelope_detector(v_series, env):
    """|v| <= the derived envelope at every tick (FB4a)."""
    return [t for t, v in enumerate(v_series) if abs(v) > env]


def gap_detector(pad_rows):
    """Every pad gap strictly positive (FB4b)."""
    return [r["tick"] for r in pad_rows
            if any(g <= 0 for pair in r["pad_gaps"].values() for g in pair)]


def x_monotone_detector(xs):
    """x never decreases (FB4c)."""
    return [t for t in range(1, len(xs)) if xs[t] < xs[t - 1] - 1e-15]


def chain_detector(chain, reference):
    """The per-tick state chain must equal the reference chain (FB6)."""
    return [t for t in range(min(len(chain), len(reference)))
            if chain[t] != reference[t]]


def yaw_route_detector(rows, expect):
    """|yaw_observed - expected| <= 1e-6 on every row (FB7)."""
    return [r["tick"] for r in rows if abs(r["yaw_obs"] - expect) > 1e-6]


def tracking_band_detector(value, v_cmd, bound):
    """|measured - commanded| <= the derived bound (FB8)."""
    return abs(value - v_cmd) > bound


class TestW08Commanded(unittest.TestCase):
    # ------------------------------------------------------------- clean
    def test_01_pins_verified(self):
        fx = fixture()
        self.assertTrue(all(r["ok"] for r in fx["pins"]))
        self.assertEqual(len(fx["pins"]), len(vi.PINS))
        self.assertEqual(fx["reg"]["criteria_sha256"], vi.CRITERIA_SHA256)

    def test_02_gate_allow_before_load_identity(self):
        fx = fixture()
        self.assertEqual(fx["gate"]["validator"]["verdict"], "VALID")
        self.assertEqual(fx["gate"]["deploy_decision"], "ALLOW")
        self.assertEqual(fx["gate"]["bundle_identity"]["manifest_hash"],
                         fx["cert"]["relation"]["policy_bundle"]["manifest_hash"])
        self.assertEqual(fx["gate"]["physics_build"]["timestep_s"], 1.0 / 300.0)

    def test_03_port_seam_laws(self):
        fx = fixture()
        p2 = fx["ev"]["P2_port_seam_laws"]
        self.assertTrue(p2["interval_law_exact"])
        self.assertTrue(p2["decay_deadline_honored"])
        self.assertTrue(p2["no_teleport_law"])
        self.assertEqual(p2["idle_silence_decay_to_S_ticks"], [])
        self.assertEqual(p2["idle_silence_after_S_ticks"], [])

    def test_04_projection_bounds_and_named_saturation(self):
        fx = fixture()
        p3 = fx["ev"]["P3_projection_within_bounds"]
        self.assertEqual(p3["bounds_violations"], [])
        self.assertTrue(p3["floor_stride_saturation_named_every_tick"])
        self.assertTrue(p3["seam_max_yaw_saturation_named_every_tick"])

    def test_05_start_tracking(self):
        fx = fixture()
        p4 = fx["ev"]["P4_start_tracking"]
        self.assertLessEqual(p4["onset_latency_ticks"], 15)
        self.assertTrue(p4["v_in_derived_range"])
        self.assertLessEqual(p4["tracking_residual_m_s"],
                             p4["tracking_bound_m_s"])
        self.assertTrue(p4["monotone_rise_below_band"])

    def test_06_turn_exactness(self):
        fx = fixture()
        p5 = fx["ev"]["P5_turn_exactness"]
        self.assertLessEqual(p5["turn_left_residual_max_rad_s"], 1e-6)
        self.assertLessEqual(p5["turn_right_residual_max_rad_s"], 1e-6)
        self.assertLessEqual(p5["seam_max_residual_rad_s"], 1e-6)
        self.assertTrue(p5["seam_max_saturation_named_every_tick"])

    def test_07_decay_step(self):
        fx = fixture()
        self.assertTrue(fx["ev"]["P6_speed_step_decay"]["strictly_decreasing"])

    def test_08_stop_floor_settle(self):
        fx = fixture()
        p7 = fx["ev"]["P7_stop_floor_settle"]
        self.assertTrue(p7["v_in_derived_settle_range"])
        self.assertTrue(p7["tail_within_derived_range_through_horizon"])
        self.assertTrue(p7["strictly_decreasing_above_band_top"])
        self.assertTrue(p7["never_below_band_low"])

    def test_09_stability_bars_every_tick(self):
        fx = fixture()
        p8 = fx["ev"]["P8_stability_bars"]
        for key in ("envelope_violation_ticks", "contact_floor_violation_ticks",
                    "nonfinite_ticks", "intervention_violation_ticks",
                    "x_decrease_ticks", "nonpositive_gap_ticks"):
            self.assertEqual(p8[key], [], key)
        self.assertGreaterEqual(p8["contact_floor_min_observed"], 2)

    def test_10_wrong_command_must_fire_with_zero_control(self):
        fx = fixture()
        p9 = fx["ev"]["P9_wrong_command_response"]
        self.assertTrue(p9["zero_control_bit_identical"])
        self.assertTrue(p9["prefix_identical_through_injection"])
        self.assertEqual(p9["first_divergent_tick"], cm.WRONG_INJECT_TICK + 1)
        self.assertTrue(p9["physical_separation_proven"])

    # ------------------------------------------------------------- bites
    def test_11_fb1_pin_bite(self):
        bad = list(vi.PINS)
        row = bad[0]
        bad[0] = (row[0], row[1], "0" * 64)
        with self.assertRaises(vi.Refusal) as ctx:
            vi.verify(expect=bad)
        self.assertIn("input_pin_mismatch", str(ctx.exception))

    def test_12_fb2_gate_bites(self):
        fx = fixture()
        from tools.policy_compat.certificate import check_deploy  # pinned
        foreign = dict(fx["req"])
        foreign["policy_bundle"] = dict(fx["req"]["policy_bundle"],
                                        manifest_hash="0" * 64)
        self.assertEqual(check_deploy(foreign, fx["cert"])["decision"], "BLOCK")
        self.assertEqual(check_deploy(fx["req"], None)["decision"], "BLOCK")

    def test_13_fb3_bounds_bite(self):
        lo = [-0.25, 0.2, 0.2, 0.5, -0.25, 0.2, 0.2, 0.5]
        hi = [0.25, 1.8, 1.8, 2.0, 0.25, 1.8, 1.8, 2.0]
        clean = [{"tick": 0, "applied": [0.0, 0.4859, 1.0, 1.25,
                                         0.0, 0.4859, 1.0, 1.25],
                  "lo": lo, "hi": hi}]
        self.assertEqual(bounds_detector(clean), [])
        bite = [{"tick": 0, "applied": [0.0, 9.9, 1.0, 1.25,
                                        0.0, 0.4859, 1.0, 1.25],
                 "lo": lo, "hi": hi}]
        self.assertEqual(bounds_detector(bite), [(0, 1)])

    def test_14_fb4_envelope_penetration_bites(self):
        fx = fixture()
        env = fx["bounds"]["velocity_envelope_m_s"]
        self.assertEqual(envelope_detector([0.5, 1.0], env), [])
        self.assertEqual(envelope_detector([0.5, env + 0.001], env), [1])
        clean_gaps = [{"tick": 0, "pad_gaps": {"hl": [0.01, 0.02],
                                               "hr": [0.009, 0.03]}}]
        self.assertEqual(gap_detector(clean_gaps), [])
        bite_gaps = [{"tick": 0, "pad_gaps": {"hl": [0.01, -0.001],
                                              "hr": [0.009, 0.03]}}]
        self.assertEqual(gap_detector(bite_gaps), [0])
        self.assertEqual(x_monotone_detector([1.0, 1.5, 2.0]), [])
        self.assertEqual(x_monotone_detector([1.0, 1.5, 1.4]), [2])

    def test_15_fb6_chain_tamper_bite(self):
        fx = fixture()
        ref = fx["res1"]["state_chain"]
        self.assertEqual(chain_detector(ref, ref), [])
        tampered = list(ref)
        tampered[100] = "0" * 64
        self.assertEqual(chain_detector(tampered, ref), [100])

    def test_16_fb7_yaw_route_bite(self):
        rows = [{"tick": 0, "yaw_obs": 0.8}, {"tick": 1, "yaw_obs": 0.8}]
        self.assertEqual(yaw_route_detector(rows, 0.8), [])
        bite = [{"tick": 0, "yaw_obs": -0.8}]
        self.assertEqual(yaw_route_detector(bite, 0.8), [0])

    def test_17_fb8_tracking_band_bite(self):
        fx = fixture()
        v_cmd = fx["bounds"]["v_cmd_ceiling_m_s"]
        bound = fx["bounds"]["ceiling_tracking_bound_m_s"]
        self.assertFalse(tracking_band_detector(v_cmd + 0.01, v_cmd, bound))
        self.assertTrue(tracking_band_detector(v_cmd + bound + 0.01,
                                               v_cmd, bound))

    def test_18_fb10_expiry_revert_bite(self):
        """The pinned expiry contract: a stale record reverts the consumer
        to the idle floor; a fresh record keeps the command (clean)."""
        fx = fixture()
        adapter = cm.CommandAdapter(fx["bundle"]["manifest"],
                                    fx["scene_const"])
        idle, idle_sat = adapter.expiry_state()
        zero_vec = adapter.project(0.0, 0.0)          # the zero-demand row
        from tools.monkey_campaign.product.input_mapper import EXPIRY_TICKS
        self.assertFalse(adapter.expired(100, 100 + EXPIRY_TICKS, EXPIRY_TICKS))
        self.assertTrue(adapter.expired(100, 100 + EXPIRY_TICKS + 1,
                                        EXPIRY_TICKS))
        # the revert target is byte-identical to the zero-demand projection
        # (motion-neutral in this script) with its named saturation
        self.assertEqual([float(v) for v in idle],
                         [float(v) for v in zero_vec["applied"]])
        self.assertEqual(idle_sat, zero_vec["saturation"])
        # a held NONZERO command would differ from idle: the revert bites
        held = adapter.project(0.763625, 0.0)["applied"]
        self.assertNotEqual([float(v) for v in idle], [float(v) for v in held])

    def test_19_fb9_structural_scan(self):
        """The contribution launches no engine/simulation/training process;
        the only subprocess modules are source_access.py (the DECLARED
        read-only git cat-file access) and run_capture.py (the DECLARED
        ffmpeg capture-tool calls)."""
        violations = []
        for path in sorted(HERE.glob("*.py")):
            tree = ast.parse(path.read_bytes())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.split(".")[0]
                        if name == "subprocess" and path.name not in (
                                "source_access.py", "run_capture.py"):
                            violations.append("subprocess:" + path.name)
                        if name == "socket":
                            violations.append("socket:" + path.name)
                elif isinstance(node, ast.ImportFrom):
                    root = (node.module or "").split(".")[0]
                    if root == "socket":
                        violations.append("socket:" + path.name)
            engine_needle = b"chimera" b"_engine"
            if engine_needle in path.read_bytes():
                violations.append("engine-ref:" + path.name)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
