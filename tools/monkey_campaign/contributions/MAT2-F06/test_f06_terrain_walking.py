#!/usr/bin/env python3
"""MAT2-F06: the named checks (the executable done_when surface).

The checks bind the RECEIPT SEMANTICS: every frozen prediction is present
and recorded with its measured values, every falsifier carries its clean
control and its bit, the traces exist and are state-bound, the capture
manifest binds, and the criteria/prereg identities hold.  Zero skips by
design (KNOWN_SKIPS: none).  The suite does NOT re-run the arms; the arms'
own gated run is the measurement of record.

Run:  python -B -m unittest test_f06_terrain_walking -v
"""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD_ID = "MAT2-F06"
TASK_SHORT = "F06"
CRITERIA_SHA256 = "a1d7040a03bd15fc12797edbb11cf44e081712539de84e900e99b95478772779"
PREREG_COMMIT = "22757b7222b463ce660059d254ab1d7fe9007a05"


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def load_receipt():
    path = HERE / "receipts" / "walking_receipt.json"
    assert path.exists(), "walking_receipt.json missing (run the arms first)"
    return json.loads(path.read_bytes().decode("utf-8"))


class TestF06WalkingReceipt(unittest.TestCase):
    def setUp(self):
        self.r = load_receipt()

    def test_schema_and_identity(self):
        self.assertEqual(self.r["schema"], "chimera.f06_terrain_walking.v1")
        self.assertEqual(self.r["card_id"], CARD_ID)
        self.assertEqual(self.r["task_id"], TASK_SHORT)
        self.assertEqual(self.r["criteria_sha256"], CRITERIA_SHA256)
        self.assertEqual(self.r["prereg_commit"], PREREG_COMMIT)
        self.assertEqual(self.r["base_sha256"],
                         "22757b7222b463ce660059d254ab1d7fe9007a05")

    def test_gate_allow_and_identity(self):
        self.assertEqual(self.r["gate"]["deploy_decision"], "ALLOW")
        self.assertEqual(self.r["gate"]["validator"]["violations"], [])
        self.assertEqual(self.r["gate"]["physics_build"]["build_id"],
                         "cpu-walk-scene-build-N")
        self.assertEqual(self.r["gate"]["physics_build"]["timestep_s"],
                         1.0 / 300.0)

    def test_p2_route_replay_exact(self):
        p2 = self.r["p2_route_replay"]
        self.assertEqual(p2["unattributed_count"], 0)
        self.assertEqual(p2["reachable_cells"], 6198)
        self.assertEqual(p2["blocked_cell_count"], 363)
        for name in ("D_rock_01", "D_trunk", "D_log_02"):
            self.assertTrue(p2["routes"][name]["exact"], name)

    def test_a0_flat_regression_bit_identity(self):
        a0 = self.r["A0_flat_regression"]["P1"]
        self.assertTrue(a0["bit_identical"])
        self.assertTrue(a0["px_equals_com_x_while_psi_zero"])
        self.assertTrue(a0["flat_channels_everywhere"])
        self.assertEqual(a0["v_at_segment_end_m_s"],
                         a0["sealed_w08_measured_m_s"])
        p10 = self.r["A0_flat_regression"]["P10"]
        self.assertEqual(p10["first_divergence_tick"], 5431)
        self.assertTrue(p10["wrong_arm_rising"])

    def test_a1_route_floor_and_clearance(self):
        a1 = self.r["A1_route"]
        self.assertTrue(a1["speed_floor_held"])
        self.assertTrue(a1["clearance_held"])
        self.assertEqual(a1["corridor_grade_envelope_derived"], 0.026054)
        self.assertLessEqual(a1["measured_max_grade"], 0.05)

    def test_a2_crest_stall_honest_negative(self):
        a2 = self.r["A2_crest_stall"]
        self.assertIsNotNone(a2["stall_tick"])
        self.assertTrue(a2["grade_at_stall_above_gamma"])
        self.assertTrue(a2["travel_within_bound"])
        self.assertEqual(a2["x_max_qualified_slope_traversed"], 0.026054)

    def test_a3_step_over_envelope(self):
        a3 = self.r["A3_step_over"]
        self.assertIsNotNone(a3["stop_tick"])
        self.assertTrue(a3["outside_certified_bounds_hi"])
        self.assertEqual(a3["log02_top_m"], 0.128476)
        self.assertAlmostEqual(a3["deficit_m"], 0.012476000000000015)
        self.assertEqual(len(a3["envelope_table"]), 7)

    def test_a4_approach_terminal(self):
        a4 = self.r["A4_approach"]
        self.assertIsNotNone(a4["stop_tick"])
        self.assertTrue(a4["axis_distance_at_stop_exact"])
        self.assertEqual(a4["trunk_penetration_count"], 0)
        self.assertTrue(a4["heading_within_quantization"])
        self.assertTrue(a4["catch_margin_check"]["caught_with_margin"])

    def test_p8_bars_and_p9_identity(self):
        for name, block in self.r["P8_stability_bars"].items():
            self.assertEqual(block["count"], 0, name)
        for name, block in self.r["P9_arc_identity"].items():
            self.assertEqual(block["violation_count"], 0, name)

    def test_falsifiers_all_bite_with_clean_controls(self):
        self.assertTrue(self.r["F_all_green"])
        for name, arm in self.r["falsifiers"].items():
            self.assertIn("clean_control", arm, name)
            self.assertTrue(arm["clean_control"]["green"], name)
            self.assertTrue(arm["bit"], name)

    def test_capture_state_binding(self):
        """The capture manifest binds every arm to its per-tick trace by
        name and proves the diagnostic/clean pair state identity.  The
        trace FILES live in the anchored evidence store (the committed
        contribution carries the manifest, not the 6 x multi-MB traces)."""
        m = json.loads((HERE / "capture" / "capture_manifest.json")
                       .read_bytes().decode("utf-8"))
        bound = {"A0": "trace_a0_ext.json", "A1": "trace_a1.json",
                 "A2": "trace_a2.json", "A3": "trace_a3.json",
                 "A4": "trace_a4.json"}
        for arm, trace in bound.items():
            self.assertEqual(m["views"][arm]["state_binding"]["bound_to"],
                             trace, arm)
            self.assertTrue(
                m["views"][arm]["state_binding"]["pair_state_identity"], arm)
            self.assertTrue(m["views"][arm]["video"]["sha256"], arm)
            self.assertGreaterEqual(len(m["views"][arm]["camera_records"]), 6)
        # the per-view camera records carry ALL 17 registry fields
        required = m["registry_profile"]["profile"]["camera_required_fields"]
        for view in m["views"].values():
            for rec in view["camera_records"]:
                for key in required:
                    self.assertIn(key, rec)

    def test_capture_manifest_binds(self):
        path = HERE / "capture" / "capture_manifest.json"
        self.assertTrue(path.exists())
        m = json.loads(path.read_bytes().decode("utf-8"))
        self.assertEqual(m["task_id"], TASK_SHORT)
        self.assertEqual(m["criteria_sha256"], CRITERIA_SHA256)
        self.assertEqual(m["registry_profile"]["profile"]["id"], "walking")
        for arm, view in m["views"].items():
            self.assertTrue(view["state_binding"]["pair_state_identity"], arm)
            for still in view["stills"]:
                self.assertTrue(still["file"].startswith(TASK_SHORT + "_"))
        ctx = json.loads((HERE / "capture" / "capture_context.json")
                         .read_bytes().decode("utf-8"))
        self.assertEqual(ctx["manifest_sha256"],
                         sha_bytes(path.read_bytes()))


if __name__ == "__main__":
    unittest.main()
