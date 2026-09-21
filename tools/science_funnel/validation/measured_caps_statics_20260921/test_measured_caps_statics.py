"""Unittests for the measured-caps static verdict lane.

Asserts, per the receipt's falsifiers_pre_registered:
  - traceability: every pinned input's sha256 equals the receipt pin at run time
  - instrument: the wave-4 generator (724f2464 byte copy) reproduces the banked
    snapshot EXACTLY; the wave-8 variant differs ONLY in the 6 documented MP cells
  - the pre-registered bands and crossing/migration verdicts (P2..P9)
  - determinism: a subprocess rerun of the derive script reproduces the
    deliverable sha256 byte-for-byte
  - no_source_changes: git status --porcelain names nothing outside this lane dir

Run:  python -B -m unittest tools.science_funnel.validation.measured_caps_statics_20260921.test_measured_caps_statics
"""
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parent
REPO = LANE.parents[3]
DERIVE = LANE / "derive_measured_caps_statics.py"
DELIVERABLE = LANE / "measured_caps_statics.json"
RECEIPT = LANE / "receipt.json"


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class TestMeasuredCapsStatics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads(RECEIPT.read_text(encoding="utf-8"))
        cls.d = json.loads(DELIVERABLE.read_text(encoding="utf-8"))
        cls.rec_sha = sha256(RECEIPT)

    def test_01_input_shas_match_receipt_pins(self):
        for name, pin in (
            ("hind_torque_book", "9fc5c0ba09f6ec183d5348bb21cc5dc18b5987240406ccdcdbb34e514e26f01c"),
            ("stance_hold_snapshot", "71e40cd8a161938a3a358792076dda0f98966a8909ae564cec7774a61126a5e5"),
            ("derived_numbers_snapshot", "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173"),
            ("wave8_machinery_byte_copy", "3c92d188b6aaf01c8cc4319262981b51ba95566370fb59e1ba4d0dd764562f70"),
            ("wave4_machinery_byte_copy", "353d07f7f18a7fa371c43eef18e40d3160d58855a24b464ef587e526bd0f81c0"),
            ("wave10_wall_deliverable", "e922153318778e4cd8c1891f59454261c6d5be0a77aebdc5f78d2758ccd2faa7"),
        ):
            path = LANE / "inputs"
            if name == "hind_torque_book":
                path = LANE.parent / "hind_torque_book_20260921" / "hind_torque_book.json"
            elif name == "stance_hold_snapshot":
                path = path / "stance_hold.snapshot.json"
            elif name == "derived_numbers_snapshot":
                path = path / "derived_numbers.snapshot.json"
            elif name.startswith("wave8") or name.startswith("wave4"):
                env = "run_env" if name.startswith("wave8") else "run_env_wave4"
                path = path / env / "tools/science_funnel/validation/gait_zero_20260919/derive_stance_hold.py"
            else:
                path = path / "vendored_gait_zero" / "trunk_vault_reachable.wave10.json"
            self.assertEqual(sha256(path), pin, name)

    def test_02_instrument_wave4_reproduces_banked_exactly(self):
        self.assertTrue(self.d["instrument"]["wave4_reproduces_banked_exactly"])
        self.assertEqual(self.d["instrument"]["rows"], 15)
        self.assertEqual(self.d["verdict"]["instrument_valid"], True)

    def test_03_instrument_wave8_variant_is_only_mp_heel_cells(self):
        self.assertEqual(self.d["instrument"]["wave8_vs_banked_diff_cells"], 6)
        for row in self.d["instrument"]["wave8_vs_banked_diffs"]:
            self.assertLessEqual(row["phi"], 0.25)
            self.assertGreater(row["banked_mp"], 7.0)
            self.assertLess(row["wave8_corrected_mp"], 0.01)

    def test_04_receipt_pre_registration_unedited_by_run(self):
        self.assertEqual(self.rec["pre_registration"]["written_before_first_verdict_computation"], True)
        self.assertIsInstance(self.rec["measured"], dict)

    def test_05_p2_wall_identity_at_a(self):
        w = self.d["margin_wall"]["A_live_doc"]
        self.assertGreaterEqual(w["max_combined_ratio"], 1.3227)
        self.assertLessEqual(w["max_combined_ratio"], 1.3229)
        self.assertEqual(w["max_binder"], {"joint": "knee", "phi": 0.75})
        self.assertAlmostEqual(w["max_combined_ratio"], 1.3227763257041534, places=6)

    def test_06_p3_stance_table_a(self):
        t = self.d["stance_tables"]["A_live_doc"]["per_joint"]
        self.assertEqual(t["knee"]["over_cap_phis"], [0.449, 0.15, 0.2, 0.25, 0.45, 0.5, 0.55, 0.6, 0.65])
        self.assertAlmostEqual(t["knee"]["worst_ratio"], 2.071111, delta=0.02)
        self.assertEqual(t["knee"]["binding_node_phi"], 0.65)
        self.assertAlmostEqual(t["mp"]["worst_ratio"], 9.534648, delta=0.25)
        self.assertEqual(t["hip"]["over_cap_nodes"], 4)
        self.assertEqual(t["posture"]["over_cap_nodes"], 4)
        self.assertEqual(t["mp"]["over_cap_nodes"], 6)

    def test_07_p4_margin_binder_class_a(self):
        mb = self.d["stance_tables"]["A_live_doc"]["margin_binder_holding"]
        self.assertEqual(mb["joint"], "ankle")
        self.assertEqual(mb["phi"], 0.3)
        self.assertGreaterEqual(mb["ratio"], 0.90)
        self.assertLessEqual(mb["ratio"], 0.99)

    def test_08_p5_p6_stance_table_b_and_migration(self):
        t = self.d["stance_tables"]["B_measured_v1_s1"]["per_joint"]
        self.assertEqual(t["knee"]["over_cap_phis"], [0.25, 0.55, 0.6, 0.65])
        self.assertAlmostEqual(t["knee"]["worst_ratio"], 1.435449, delta=0.015)
        self.assertAlmostEqual(t["knee"]["worst_ratio"] * 1.0, 1.4354, delta=0.005)
        nodes = {n["phi"]: n for n in self.d["stance_tables"]["B_measured_v1_s1"]["nodes"]}
        self.assertAlmostEqual(nodes[0.449]["ratio"]["knee"], 0.759649, delta=0.01)
        self.assertAlmostEqual(nodes[0.25]["ratio"]["knee"], 1.100264, delta=0.01)
        self.assertAlmostEqual(t["mp"]["worst_ratio"], 5.10397, delta=0.1)
        self.assertEqual(t["ankle"]["over_cap_nodes"], 0)
        self.assertEqual(t["hip"]["over_cap_nodes"], 4)
        self.assertEqual(t["posture"]["over_cap_nodes"], 4)
        # P6: agreement with the book's own ratio_after column within rounding
        book = json.loads((LANE.parent / "hind_torque_book_20260921" / "hind_torque_book.json")
                          .read_text(encoding="utf-8"))
        book_nodes = {n["phi"]: n["ratio_new_vs_book"]
                      for n in book["consumption_map"]["hind_tier"]["nodes"]}
        for n in self.d["stance_tables"]["B_measured_v1_s1"]["nodes"]:
            self.assertLess(abs(n["ratio"]["knee"] - book_nodes[n["phi"]]) / book_nodes[n["phi"]], 1e-3)

    def test_09_p7_wall_b(self):
        w = self.d["margin_wall"]["B_measured_v1_s1"]
        self.assertAlmostEqual(w["knee_term_at_phi_0_75"], 0.916792, delta=0.015)
        self.assertGreaterEqual(w["max_combined_ratio"], 0.95)
        self.assertLessEqual(w["max_combined_ratio"], 0.995)
        self.assertEqual(w["max_binder"], {"joint": "ankle", "phi": 0.5})
        self.assertTrue(w["crosses_1_0"])
        self.assertFalse(w["margin_0_9_reachable"])
        self.assertEqual(w["nodes_over_1_0"], [])

    def test_10_p8_stance_and_wall_c(self):
        t = self.d["stance_tables"]["C_provisional_v2_s1"]["per_joint"]
        self.assertEqual(t["knee"]["over_cap_nodes"], 0)
        self.assertAlmostEqual(t["knee"]["worst_ratio"], 0.379251, delta=0.02)
        self.assertAlmostEqual(t["mp"]["worst_ratio"], 1.825019, delta=0.1)
        w = self.d["margin_wall"]["C_provisional_v2_s1"]
        self.assertAlmostEqual(w["knee_term_at_phi_0_75"], 0.24222, delta=0.012)
        self.assertAlmostEqual(w["max_combined_ratio"], 0.977235, delta=0.02)
        self.assertEqual(w["max_binder"], {"joint": "ankle", "phi": 0.5})
        self.assertTrue(w["crosses_1_0"])
        self.assertFalse(w["margin_0_9_reachable"])

    def test_11_p9_scale_gate_s2_inversion(self):
        t = self.d["stance_tables"]["S2_si_matched_gate"]["per_joint"]
        # FIRED AT ITS LETTER (14 vs the registered 15), BANDS HELD - recorded in
        # the receipt's measured block; the unittest asserts the MEASURED state.
        self.assertEqual(t["knee"]["over_cap_nodes"], 14)
        self.assertAlmostEqual(t["knee"]["worst_ratio"], 11.986652, delta=0.45)
        w = self.d["margin_wall"]["S2_si_matched_gate"]
        self.assertAlmostEqual(w["knee_term_at_phi_0_75"], 7.65563, delta=0.25)
        self.assertEqual(w["max_binder"], {"joint": "knee", "phi": 0.75})
        self.assertFalse(w["crosses_1_0"])

    def test_12_every_cap_has_provenance_class(self):
        for name, entry in self.d["cap_sets"].items():
            for joint, cls in entry["provenance_class"].items():
                self.assertIn(cls, self.d["cap_provenance_classes"], f"{name}.{joint}")

    def test_13_determinism_subprocess_rerun_byte_identical(self):
        before = sha256(DELIVERABLE)
        res = subprocess.run([sys.executable, "-B", str(DERIVE)],
                             capture_output=True, text=True, timeout=600, cwd=str(REPO))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(sha256(DELIVERABLE), before)
        self.assertIn(before, res.stdout)

    def test_14_no_source_changes_outside_lane(self):
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                             text=True, timeout=120, cwd=str(REPO))
        lane_prefix = "tools/science_funnel/validation/measured_caps_statics_20260921/"
        outside = []
        for line in res.stdout.splitlines():
            p = line[3:].strip().strip('"')
            if p and not p.startswith(lane_prefix):
                outside.append(p)
        self.assertEqual(outside, [], f"files changed outside the lane dir: {outside}")

    def test_15_receipt_deliverable_sha_self_claim(self):
        self.assertEqual(self.rec["measured"]["deliverable"]["sha256"], sha256(DELIVERABLE))


if __name__ == "__main__":
    unittest.main()
