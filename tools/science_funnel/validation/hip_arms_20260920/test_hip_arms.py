"""Tests for the hip-arms lane (2026-09-20): pins, geometry finding, recomputation
of every consumed number from the deliverable's own bytes, containment (F5)."""

import json
import subprocess
import unittest
from pathlib import Path

LANE_DIR = Path(__file__).resolve().parent
REPO = LANE_DIR.parents[3]
sys_path0 = str(REPO / "tools/science_funnel/validation/pulley_rederivation_20260920")

BOOK_PATH = LANE_DIR / "hip_arms_book.json"
RECEIPT_PATH = LANE_DIR / "receipt.json"
K_FILL = REPO / "tools/science_funnel/validation/k_fill_20260920/k_fill_book.json"
DERIVED_NUMBERS = REPO / "tools/science_funnel/validation/hind_torque_book_20260921/inputs/derived_numbers.snapshot.json"

CLASS = ["R_BFL", "R_GMax", "R_SM", "R_ST"]
CSTAR_TOP = 33.6


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class TestHipArms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = load(BOOK_PATH)
        cls.receipt = load(RECEIPT_PATH)
        cls.kfill = load(K_FILL)

    def test_01_input_pins_hold(self):
        import sys
        sys.path.insert(0, str(LANE_DIR))
        import derive_hip_arms as dh
        got = dh.verify_inputs()  # raises SystemExit on any drift
        self.assertEqual(got["model"],
                         "d5c65cbc0a72bd2d5c2258c6bd018fe850ae25cce6fb07c1f268b91e598c88e9")

    def test_02_geometry_f1_class_wrap_free(self):
        ga = self.book["geometry_audit"]
        self.assertTrue(ga["f1_no_geometry_class"])
        for n in CLASS:
            self.assertEqual(ga["f1_class_wraps"][n], [])
        self.assertIn("rIschium_Cylinder", ga["referenced_wraps_audited"])
        self.assertIn("rFemoralneck", ga["referenced_wraps_audited"])

    def test_03_p0_anatomical_sign_check_held(self):
        p0 = self.book["p0_anatomical_sign_check"]["verdict"]
        self.assertTrue(p0["held"])
        self.assertTrue(p0["R_ILI_positive_flexor"])
        self.assertTrue(p0["class_negative_extensor"])

    def test_04_forces_byte_equal_to_kfill_force_set(self):
        self.assertTrue(self.book["comparison"]["forces_byte_equal_to_kfill_set"])
        for row in self.book["comparison"]["per_muscle_mid_stance"]:
            self.assertTrue(row["force_byte_equal_to_force_set"])
            full = self.kfill["derived_force_set"]["muscles"][row["muscle"]]["force_N"]
            self.assertEqual(self.book["forces_N"][row["muscle"]], full)

    def test_05_windows_match_pinned_inputs(self):
        hip = load(DERIVED_NUMBERS)["oku_before_alteration"]["angles"]["hip"]
        w = self.book["method"]["windows"]
        self.assertEqual(w["walk"]["lo_rad"], hip["min_rad"])
        self.assertEqual(w["walk"]["hi_rad"], hip["max_rad"])
        self.assertEqual(w["rearup"]["lo_rad"], -1.5708)
        self.assertEqual(w["rearup"]["hi_rad"], 0.0)
        self.assertEqual(self.book["method"]["scan_samples"], 2001)
        self.assertEqual(self.book["method"]["fd_step_rad"], 1.0e-4)

    def test_06_class_curves_artifact_free_and_full(self):
        for n in CLASS:
            d = self.book["directions"][n]
            self.assertEqual(d["valid_samples"], 2001)
            self.assertIsNone(d["scan_stop"])
            self.assertEqual(d["artifact_flag"]["count"], 0)
            self.assertEqual(len(d["arm_samples_m"]), 2001)

    def test_07_capability_recomputes_from_stored_curve(self):
        import math
        import numpy as np
        forces = self.book["forces_N"]
        for block in ("walk_window", "rearup_window"):
            cap_b = self.book["hip_book_derived"][block]
            lo_i, hi_i = cap_b["window_grid_indices"]
            best, arg = None, None
            for k in range(lo_i, hi_i + 1):
                tau = 0.0
                for n in CLASS:
                    r = self.book["directions"][n]["arm_samples_m"][k]
                    if not math.isnan(r) and r < 0.0:
                        tau += forces[n] * (-r)
                if best is None or tau > best:
                    best, arg = tau, k
            self.assertAlmostEqual(best, cap_b["cap_N_m"], places=6,
                                   msg="%s cap recomputation" % block)
            self.assertEqual(arg, cap_b["argmax_index"])

    def test_08_verdict_recomputes(self):
        v = self.book["rearup_verdict"]
        primary = v["primary_max_capability_N_m"]
        self.assertEqual(v["verdict"], "COVERED" if primary > CSTAR_TOP else "NOT COVERED")
        self.assertEqual(v["covered"], primary > CSTAR_TOP)
        cons_caps = v["conservative_caps_N_m"]
        self.assertAlmostEqual(max(cons_caps.values()),
                               v["conservative_max_capability_N_m"], places=9)
        self.assertAlmostEqual(
            self.kfill["capabilities_deposit_arms"]["knee_extension"]["cap_N_m"],
            cons_caps["knee_extension"], places=9)
        changed = (primary > CSTAR_TOP) != (v["prior_verdict"]["primary_max_capability_N_m"] > CSTAR_TOP)
        self.assertEqual(v["verdict_changed"], changed)

    def test_09_side_by_side_book_present(self):
        comp = self.book["comparison"]
        self.assertAlmostEqual(comp["kfill_context_book_consumed"]["hip_extension_context_N_m"],
                               26.58202, places=6)
        self.assertIn("derived_same_pose_mid_stance_sum_N_m", comp)
        for row in comp["per_muscle_mid_stance"]:
            self.assertLess(abs(row["derived_arm_mm_at_mid_stance"]),
                            row["record_arm_mm"],
                            "every derived mid-stance arm below the record scalar (P1 fired)")

    def test_10_named_gaps_never_admitted(self):
        for n in ("R_RF", "R_SAR", "R_AB"):
            gap = self.book["named_gaps"][n]
            self.assertIsNone(gap["force_N"])
            self.assertNotIn(n, self.book["directions"])
            self.assertNotIn(n, self.book["forces_N"])

    def test_11_f5_no_source_changes_outside_lane_dir(self):
        out = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain"],
                             capture_output=True, text=True, check=True).stdout
        offenders = []
        for line in out.splitlines():
            path = line[3:].strip().strip('"')
            if path and not path.startswith(
                    "tools/science_funnel/validation/hip_arms_20260920/"):
                offenders.append(path)
        self.assertEqual(offenders, [], "F5 containment violated: %r" % offenders)

    def test_12_determinism_recorded_in_receipt(self):
        f4 = self.receipt["measured"]["falsifier_verdicts"]["F4_determinism"]
        self.assertEqual(f4["verdict"], "HELD")
        shas = set(f4["sha256_runs"])
        self.assertEqual(len(shas), 1, "three runs must agree on one sha")
        import hashlib
        deliverable = hashlib.sha256(BOOK_PATH.read_bytes()).hexdigest()
        self.assertEqual(shas.pop(), deliverable)


if __name__ == "__main__":
    unittest.main()
