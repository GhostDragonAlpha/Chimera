"""Tests for the hip-quarantine-review lane (2026-09-20).

Asserts the five mission falsifiers in their measurable form:
F1 no law violation (no homolog verdict; no quarantined force admitted or consumed),
F2 sweep-ban (extended book constants byte-equal to the landed/k-fill inputs),
F3 traceability (every pinned input resolves at load; loader refuses on drift),
F4 determinism (a fresh subprocess derivation is byte-identical),
F5 containment (git status --porcelain clean outside the lane dir).
"""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parent
REPO = LANE.parents[3]
sys.path.insert(0, str(LANE))

import derive_extension_review as der  # noqa: E402


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class TestHipQuarantineReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = json.loads((LANE / "extended_hip_book.json").read_text(encoding="utf-8"))
        cls.adjudication = json.loads((LANE / "adjudication.json").read_text(encoding="utf-8"))
        cls.landed = json.loads(
            (REPO / "tools/science_funnel/validation/hip_arms_20260920/hip_arms_book.json")
            .read_text(encoding="utf-8"))
        cls.kfill = json.loads(
            (REPO / "tools/science_funnel/validation/k_fill_20260920/k_fill_book.json")
            .read_text(encoding="utf-8"))

    def test_f5_containment(self):
        out = subprocess.run(["git", "status", "--porcelain"],
                             cwd=str(REPO), capture_output=True, text=True, check=True).stdout
        offenders = []
        for line in out.splitlines():
            path = line[3:].strip().strip('"').replace("\\", "/")
            if path and not path.startswith(
                    "tools/science_funnel/validation/hip_quarantine_review_20260920"):
                offenders.append(line)
        self.assertEqual(offenders, [],
                         "changes outside the lane directory: %r" % offenders)

    def test_f4_determinism_subprocess_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "rerun.json"
            proc = subprocess.run(
                [sys.executable, "-B", str(LANE / "derive_extension_review.py"), str(out)],
                capture_output=True, text=True, cwd=str(REPO))
            self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
            deliverable = sha256_of(LANE / "extended_hip_book.json")
            self.assertEqual(sha256_of(out), deliverable,
                             "fresh subprocess derivation is not byte-identical (F4)")
        self.assertEqual(deliverable,
                         "ccca5cabd6b7d31fc89ab0ce98e90f5edccc2a71cdb390b78966932f68b65d79")

    def test_f3_input_pins_resolve(self):
        got = der.verify_inputs()  # REFUSES (SystemExit) on drift
        self.assertEqual(len(got), len(der.EXPECTED_SHA))
        self.assertIn("guimaraes_audit", got)

    def test_f1_no_law_violation_adjudication(self):
        lawful = {"QUARANTINE_STANDS", "RESOLVED_BY_SECOND_SOURCE", "RESOLVED_BY_HOMOLOG"}
        for name, row in self.adjudication["muscles"].items():
            self.assertIn(row["verdict"], lawful, name)
            self.assertTrue(row["defects"], "%s carries no restated defect" % name)
            self.assertTrue(row["why_no_second_source"], name)
        homolog = [n for n, r in self.adjudication["muscles"].items()
                   if r["verdict"] == "RESOLVED_BY_HOMOLOG"]
        self.assertEqual(homolog, [],
                         "homolog route used - the books' substitution law does not permit it (F1)")
        self.assertIn("CLOSED", self.adjudication["law"]["homolog_route"])
        # every STANDS row admits nothing
        for name, row in self.adjudication["muscles"].items():
            if row["verdict"] == "QUARANTINE_STANDS":
                self.assertIsNone(row["admitted_force_N"], name)
        # consistency of the admitted set
        second = {n for n, r in self.adjudication["muscles"].items()
                  if r["verdict"] == "RESOLVED_BY_SECOND_SOURCE"}
        self.assertEqual(second, set(self.adjudication["admitted_set"]))

    def test_f1_no_quarantined_force_consumed(self):
        ext_class = self.book["extended_book"]["class"]
        for quarantined in ("R_RF", "R_SAR", "R_AB", "R_BFS"):
            self.assertNotIn(quarantined, ext_class,
                             "a quarantined muscle entered the extended class (F1)")
            reading = self.book["quarantined_named_readings"][quarantined]
            self.assertIn("no_force_consumed", reading["status"])
            self.assertEqual(self.adjudication["muscles"][quarantined]["admitted_force_N"], None)
            self.assertEqual(self.kfill["derived_force_set"]["muscles"][quarantined]["force_N"],
                             None)
        cf = self.book["counterfactual_bounds_NEVER_CONSUMED"]
        for quarantined in ("R_RF", "R_SAR", "R_AB", "R_BFS"):
            self.assertIn("counterfactual_bound_NEVER_CONSUMED",
                          self.book["quarantined_named_readings"][quarantined])
            self.assertIn("consumed by no sum",
                          self.book["quarantined_named_readings"][quarantined]
                          ["counterfactual_bound_NEVER_CONSUMED"]["basis"])

    def test_f2_no_constant_moved(self):
        self.assertTrue(self.book["extended_vs_landed"]["extended_equal_landed"])
        # forces byte-equal to the k-fill set
        for name, force in self.book["extended_book"]["forces_N"].items():
            entry = self.kfill["derived_force_set"]["muscles"][name]
            self.assertEqual(force, float(entry["force_N"]), name)
        # class curves byte-equal to the landed book's stored samples
        for name, chk in self.book["class_crosscheck_vs_landed_book"].items():
            self.assertTrue(chk["byte_equal_to_landed_samples"], name)
        # verdict identical
        self.assertEqual(self.book["rearup_verdict"]["primary_max_capability_N_m"],
                         self.landed["hip_book_derived"]["rearup_window"]["cap_N_m"])
        self.assertEqual(self.book["rearup_verdict"]["verdict_vs_landed"], "UNCHANGED")

    def test_rearup_verdict_decisive_not_covered(self):
        v = self.book["rearup_verdict"]
        self.assertEqual(v["verdict"], "NOT COVERED")
        self.assertFalse(v["covered"])
        self.assertAlmostEqual(v["primary_max_capability_N_m"], 10.71803014, places=8)
        self.assertAlmostEqual(v["gap_to_floor_N_m"], 11.68196986, places=8)
        self.assertLess(v["gap_multiple_to_floor"], 2.091)
        # the counterfactual robustness bound also stays below the floor
        cf = self.book["counterfactual_bounds_NEVER_CONSUMED"]
        self.assertFalse(cf["counterfactual_crosses_floor"])
        self.assertLess(cf["counterfactual_total_N_m"], cf["cstar_floor_N_m"])

    def test_readings_measured(self):
        r = self.book["quarantined_named_readings"]
        for name, reading in r.items():
            self.assertEqual(reading["valid_samples"], 2001, name)
            self.assertIsNone(reading["scan_stop"], name)
        # RF and AB carry NO material extensor channel; SAR does (recorded honestly)
        self.assertFalse(r["R_RF"]["p2_material_extensor_channel"])
        self.assertFalse(r["R_AB"]["p2_material_extensor_channel"])
        self.assertTrue(r["R_SAR"]["p2_material_extensor_channel"])
        self.assertAlmostEqual(r["R_SAR"]["counterfactual_bound_NEVER_CONSUMED"]
                               ["counterfactual_max_rearup_add_N_m"], 0.3734177023230839, places=9)
        # BFS hip arm is exactly zero (float noise only)
        self.assertTrue(r["R_BFS"]["hip_arm_zero_check"]["zero_within_1e-6_m"])
        self.assertEqual(r["R_BFS"]["material_negative_samples_rearup_abs_gt_1e-6_m"], 0)


if __name__ == "__main__":
    unittest.main()
