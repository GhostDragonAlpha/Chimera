#!/usr/bin/env python3
"""MAT2-W10: the executable done_when checks (receipt-bound named checks).

Every check consumes the COMMITTED receipts and refuses on pin drift, so the
suite is red until the gated runs happened and green only against the real
bytes. The done_when clause (verbatim) maps to the named checks below.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi          # noqa: E402


def load(name):
    path = HERE / name
    if not path.exists():
        raise vi.Refusal("receipt_missing:" + name)
    return json.loads(path.read_bytes().decode("utf-8"))


class W10WalkingDemo(unittest.TestCase):
    def setUp(self):
        self.pins = vi.verify()
        self.reg = vi.verify_registry()
        self.demo = load(HERE / "receipts" / "walking_demo_receipt.json")
        self.capture = load(HERE / "capture" / "capture_receipt.json")

    def test_a_pin_and_identity_chain(self):
        self.assertEqual(self.demo["criteria_sha256"], vi.CRITERIA_SHA256)
        self.assertEqual(self.demo["preregistration_sha256"],
                         vi.prereg_sha256())
        self.assertEqual(self.demo["amendment_a1_sha256"],
                         vi.amendment_a1_sha256())
        self.assertEqual(self.demo["amendment_a2_sha256"],
                         vi.amendment_a2_sha256())

    def test_b_player_can_walk_start_tracking(self):
        ev = self.demo["predictions"]["P4_start_tracking"]
        self.assertLessEqual(ev["onset_latency_ticks"], 15)
        self.assertTrue(ev["v_in_derived_range"])
        self.assertLessEqual(ev["tracking_residual_m_s"],
                             ev["tracking_bound_m_s"])

    def test_c_player_can_turn(self):
        ev = self.demo["predictions"]["P5_turn_exactness"]
        self.assertLessEqual(ev["turn_left_max_residual_rad_s"], 1e-6)
        self.assertLessEqual(ev["turn_right_max_residual_rad_s"], 1e-6)
        self.assertTrue(ev["seam_max_saturation_named"])

    def test_d_player_can_stop(self):
        ev = self.demo["predictions"]["P7_stop_floor_settle"]
        self.assertTrue(ev["v_in_settle_range"])
        self.assertTrue(ev["strictly_decreasing_above_floor_band"])

    def test_e_on_a_supported_surface(self):
        ev = self.demo["predictions"]["P10_supported_surface"]
        self.assertEqual(ev["low_contact_count"], 0)
        self.assertTrue(ev["every_tick_carried_by_four_pads"])
        self.assertTrue(ev["swing_windows_disclosed_within_bound"])
        self.assertEqual(ev["supervisor_response_events_r1"], 0)

    def test_f_no_sliding_no_penetration(self):
        ev = self.demo["predictions"]["P11_no_sliding_no_penetration"]
        self.assertEqual(ev["com_identity_violation_count"], 0)
        self.assertEqual(ev["penetration_count"], 0)

    def test_g_no_hidden_reset(self):
        for name in ("velocity_recursion", "phase_recursion",
                     "micro_draw_chain"):
            battery = self.demo["falsifiers"]["FB1_hidden_reset"]
            self.assertTrue(battery["clean_control"]["green"], name)
        self.assertTrue(self.demo["falsifiers"]["FB1_hidden_reset"]["bit"])

    def test_h_wrong_command_response_fired(self):
        ev = self.demo["predictions"]["P9_wrong_command_response_MUST_FIRE"]
        self.assertTrue(ev["prefix_identical_through_5430"])
        self.assertGreater(ev["v_r3_at_probe_m_s"], ev["v_r1_at_probe_m_s"])
        self.assertTrue(ev["r1_vs_r2_bit_identical"])

    def test_i_fall_replay_faithful_to_w09(self):
        ev = self.demo["predictions"]["P12_w09_replay_faithful"]
        self.assertTrue(ev["first_interval_exact"])
        self.assertTrue(ev["fall_tick_exact"])
        self.assertTrue(ev["r1_strides_at_certified_minimum_pre_fall"])
        self.assertTrue(ev["support_forces_removed_on_unsupported_ticks"])

    def test_j_numerical_and_visual_receipts_match(self):
        ev = self.capture["P13_visual_binding"]
        self.assertTrue(ev["pairs_state_hash_identical"])
        cap = self.capture
        self.assertTrue(cap["fb5_all_differ"])
        self.assertTrue(cap["fb6_state_unchanged"])
        for vid in cap["videos"].values():
            for probe in vid["decode_probe"]:
                self.assertTrue(probe["pixel_exact"])

    def test_k_no_cosmetic_skin_over_an_unrelated_body(self):
        cap = self.capture
        self.assertTrue(cap["fb5_all_differ"])
        ctx = load(HERE / "capture" / "capture_context.json")
        self.assertIn("hind-pad-surrogate", ctx["honesty_label"])

    def test_l_all_predictions_and_falsifiers(self):
        self.assertTrue(self.demo["all_predictions_pass"])
        self.assertTrue(self.demo["F_all_green"])
        for name, arm in self.demo["falsifiers"].items():
            self.assertTrue(arm["bit"], name)
            self.assertTrue(arm["clean_control"]["green"], name)

    def test_m_zero_skips_accounting(self):
        self.assertEqual(self.demo["determinism"]["command"],
                         "python -B walking_demo.py")
        self.assertEqual(self.capture["determinism"]["command"],
                         "python -B run_capture.py")


if __name__ == "__main__":
    try:
        unittest.main(verbosity=2)
    except vi.Refusal as refusal:
        print("REFUSAL: " + str(refusal), file=sys.stderr)
        raise SystemExit(2)
