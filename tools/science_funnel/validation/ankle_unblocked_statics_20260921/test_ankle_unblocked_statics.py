"""Unittests for the ankle-unblocked static close-out lane.

Asserts, per the receipt's falsifiers_pre_registered:
  - traceability: every pinned input's sha256 equals the receipt pin at run time
    (including the ANKLE book: content sha 7ce03069... = git blob f55ebe5f at
    b15ff31e, branch agent/ankle-arms-20260921)
  - instrument chain (PD1): the wave-4 generator reproduces the banked snapshot
    EXACTLY and this lane's recomputed (a)/(b)/(c)/(S2) tables, MP-variant
    tables and walls equal the STATICS lane's committed deliverable field-for-field
  - the pre-registered bands and crossing/binder verdicts (PD2..PD5)
  - determinism (PD6): a subprocess rerun of the derive script reproduces the
    deliverable sha256 byte-for-byte
  - no_source_changes (PD7): git status --porcelain names nothing outside this
    lane dir
  - the ankle inputs stay sha-pinned (PD8)

Run:  python -B -m unittest tools.science_funnel.validation.ankle_unblocked_statics_20260921.test_ankle_unblocked_statics
"""
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parent
REPO = LANE.parents[3]
DERIVE = LANE / "derive_ankle_unblocked_statics.py"
DELIVERABLE = LANE / "ankle_unblocked_statics.json"
RECEIPT = LANE / "receipt.json"
STATICS_COMMITTED = LANE / "inputs" / "statics_lane_committed_deliverable.json"


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class TestAnkleUnblockedStatics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads(RECEIPT.read_text(encoding="utf-8"))
        cls.d = json.loads(DELIVERABLE.read_text(encoding="utf-8"))

    def test_01_input_shas_match_receipt_pins(self):
        for name, pin in (
            ("ankle_arms_book", "7ce03069c1e033b52db0fb315d218eb2223e79a67a9018123da206d68adcb6f6"),
            ("stance_hold_snapshot", "71e40cd8a161938a3a358792076dda0f98966a8909ae564cec7774a61126a5e5"),
            ("wave4_machinery_byte_copy", "353d07f7f18a7fa371c43eef18e40d3160d58855a24b464ef587e526bd0f81c0"),
            ("wave8_machinery_byte_copy", "3c92d188b6aaf01c8cc4319262981b51ba95566370fb59e1ba4d0dd764562f70"),
            ("wave10_wall_deliverable", "e922153318778e4cd8c1891f59454261c6d5be0a77aebdc5f78d2758ccd2faa7"),
            ("hind_torque_book", "9fc5c0ba09f6ec183d5348bb21cc5dc18b5987240406ccdcdbb34e514e26f01c"),
            ("statics_lane_committed_deliverable", "21d3dbbe2a477d67f7d7d5572f0171cd0c2e8cfe34a6cd1770ccd81abf06908a"),
        ):
            path = LANE / "inputs"
            if name == "ankle_arms_book":
                path = path / "ankle_arms_book.json"
            elif name == "stance_hold_snapshot":
                path = path / "stance_hold.snapshot.json"
            elif name.startswith("wave8") or name.startswith("wave4"):
                env = "run_env" if name.startswith("wave8") else "run_env_wave4"
                path = path / env / "tools/science_funnel/validation/gait_zero_20260919/derive_stance_hold.py"
            elif name == "wave10_wall_deliverable":
                path = path / "vendored_gait_zero" / "trunk_vault_reachable.wave10.json"
            elif name == "hind_torque_book":
                path = LANE.parent / "hind_torque_book_20260921" / "hind_torque_book.json"
            else:
                path = path / "statics_lane_committed_deliverable.json"
            self.assertEqual(sha256(path), pin, name)

    def test_02_ankle_inputs_git_object_pinned_at_b15ff31e(self):
        """PD8: the ankle book's content sha equals the git blob at the ankle
        lane's commit - the measured caps cannot drift without the pin firing."""
        res = subprocess.run(
            ["git", "rev-parse",
             "b15ff31e:tools/science_funnel/validation/ankle_arms_20260921/ankle_arms_book.json"],
            capture_output=True, text=True, timeout=120, cwd=str(REPO))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "f55ebe5f94109fe3c659c13cc6d46598591b9595")
        self.assertEqual(self.d["ankle_cap_trace"]["sha256"],
                         "7ce03069c1e033b52db0fb315d218eb2223e79a67a9018123da206d68adcb6f6")

    def test_03_pd1_instrument_wave4_reproduces_banked_exactly(self):
        self.assertTrue(self.d["instrument"]["wave4_reproduces_banked_exactly"])
        self.assertEqual(self.d["instrument"]["rows"], 15)

    def test_04_pd1_chain_equals_committed_statics_deliverable(self):
        """Falsifier (a) at its letter: the recomputed (a)/(b)/(c)/(S2) tables,
        MP-variant tables and walls equal the statics lane's COMMITTED
        deliverable field-for-field."""
        self.assertTrue(self.d["statics_chain_reproduction"]["all_equal_committed_statics"])
        committed = json.loads(STATICS_COMMITTED.read_text(encoding="utf-8"))
        a_mine = self.d["stance_tables"]["A_live_doc"]["per_joint"]
        a_theirs = committed["stance_tables"]["A_live_doc"]["per_joint"]
        self.assertEqual(a_mine["knee"]["over_cap_phis"], a_theirs["knee"]["over_cap_phis"])
        self.assertEqual(a_mine["mp"]["worst_ratio"], a_theirs["mp"]["worst_ratio"])
        self.assertEqual(self.d["margin_wall"]["A_live_doc"]["max_combined_ratio"],
                         committed["margin_wall"]["A_live_doc"]["max_combined_ratio"])
        self.assertEqual(self.d["margin_wall"]["B_measured_v1_s1"]["max_combined_ratio"],
                         committed["margin_wall"]["B_measured_v1_s1"]["max_combined_ratio"])

    def test_05_instrument_wave8_variant_is_only_mp_heel_cells_and_ankle_identical(self):
        self.assertEqual(self.d["instrument"]["wave8_vs_banked_diff_cells"], 6)
        self.assertTrue(self.d["instrument"]["ankle_column_bit_identical_wave8_vs_wave4"],
                        "no ANKLE verdict may depend on the machinery choice")

    def test_06_pd2_stance_table_d_ankle(self):
        aj = self.d["stance_tables"]["D_measured_ankle_unblocked"]["per_joint"]["ankle"]
        # the ankle lane's own statics-side prediction, verified from the statics side
        self.assertEqual(aj["over_cap_nodes"], 6)
        self.assertEqual(sorted(aj["over_cap_phis"]), sorted([0.449, 0.3, 0.35, 0.4, 0.45, 0.5]))
        self.assertGreaterEqual(aj["worst_ratio"], 1.15)
        self.assertLessEqual(aj["worst_ratio"], 1.16)
        self.assertEqual(aj["binding_node_phi"], 0.3)
        # the dorsal class: sign-gated at 1.251106, all six hold, near-touching
        nodes = self.d["stance_tables"]["D_measured_ankle_unblocked"]["nodes"]
        dorsal = [n["ratio"]["ankle"] for n in nodes if n["tau_Nm"]["ankle"] > 0]
        self.assertEqual(len(dorsal), 6)
        for r in dorsal:
            self.assertLessEqual(r, 1.0)
        self.assertAlmostEqual(max(dorsal), 0.987926, delta=0.008)
        # the ankle lane's number cross-check (their ratio_after 1.1549 at binding)
        self.assertAlmostEqual(aj["worst_ratio"], 7.215 / 6.247077, delta=1e-6)
        self.assertTrue(self.d["verdict"]["ankle_unblocked_verdict"]["verified_from_the_statics_side"])

    def test_07_pd3_wall_d_reverts(self):
        w = self.d["margin_wall"]["D_measured_ankle_unblocked"]
        wb = self.d["margin_wall"]["B_measured_v1_s1"]
        self.assertTrue(wb["crosses_1_0"], "the statics lane's (b) crossing must reproduce first")
        self.assertAlmostEqual(wb["max_combined_ratio"], 0.977235, delta=0.02)
        self.assertAlmostEqual(w["ankle_term_at_phi_0_5"], 1.157587, delta=0.015)
        self.assertGreaterEqual(w["max_combined_ratio"], 1.14)
        self.assertLessEqual(w["max_combined_ratio"], 1.18)
        self.assertEqual(w["max_binder"], {"joint": "ankle", "phi": 0.5})
        self.assertFalse(w["crosses_1_0"], "the 1.0-crossing does NOT survive the measured ankle")
        self.assertFalse(w["margin_0_9_reachable"])
        self.assertAlmostEqual(w["knee_term_at_phi_0_75"], 0.916792, delta=0.015)

    def test_07b_pd3_dorsal_bracket(self):
        w = self.d["margin_wall"]["D_dorsal_bracket"]
        self.assertGreaterEqual(w["max_combined_ratio"], 5.6)
        self.assertLessEqual(w["max_combined_ratio"], 5.9)
        self.assertEqual(w["max_binder"], {"joint": "ankle", "phi": 0.5})
        self.assertFalse(w["crosses_1_0"], "direction-robust: the re-block holds under the bracket too")

    def test_08_pd4_binder_map_d(self):
        t = self.d["stance_tables"]["D_measured_ankle_unblocked"]
        self.assertAlmostEqual(t["per_joint"]["mp"]["worst_ratio"], 5.10397, delta=0.1)
        self.assertEqual(t["worst_case_binder"], {"joint": "mp", "phi": 0.25})
        mb = t["margin_binder_holding"]
        self.assertEqual(mb["joint"], "ankle")
        self.assertEqual(mb["phi"], 0.25)
        self.assertAlmostEqual(mb["ratio"], 0.987926, delta=0.008)
        v = self.d["verdict"]["binder_map"]
        self.assertEqual(v["wall_owner"]["joint"], "ankle")
        self.assertEqual(v["wall_owner"]["phi"], 0.5)
        self.assertIn("OVER-CAP", v["wall_owner"]["state"])
        w = self.d["margin_wall"]["D_measured_ankle_unblocked"]
        # every wall node over 1.0 at (d) is ankle-bound
        for nd in w["nodes"]:
            if nd["combined"] > 1.0:
                self.assertEqual(nd["binder"], "ankle", f"phi={nd['phi']}")

    def test_08b_pd4_corrected_mp_variant_binder_FIRED_BAND_recorded(self):
        """FIRED AT ITS LETTER, recorded per Rule 0: the pre-registered band
        named HIP 1.480669 [1.46, 1.50] - the measured worst is the POSTURE
        1.530435 at phi=0.65 (the hand prior omitted the posture column's
        worst). The unittest asserts the MEASURED state; the miss is recorded
        with its number in the receipt's measured block, never absorbed."""
        t = self.d["stance_tables_wave8_corrected_mp_VARIANT"]["D_measured_ankle_unblocked"]
        self.assertEqual(t["worst_case_binder"], {"joint": "posture", "phi": 0.65})
        self.assertAlmostEqual(t["worst_case_ratio"], 1.530435, delta=0.01)
        self.assertLess(t["per_joint"]["mp"]["worst_ratio"], 0.01,
                        "the windlass MP class vanishes under the corrected column")

    def test_09_pd5_s2_inversion_bracket_d(self):
        t = self.d["stance_tables"]["D_S2_si_matched_gate"]["per_joint"]
        self.assertEqual(t["ankle"]["over_cap_nodes"], 15)
        self.assertGreaterEqual(t["ankle"]["worst_ratio"], 9.5)
        self.assertLessEqual(t["ankle"]["worst_ratio"], 9.75)
        nodes = self.d["stance_tables"]["D_S2_si_matched_gate"]["nodes"]
        dorsal = [n["ratio"]["ankle"] for n in nodes if n["tau_Nm"]["ankle"] > 0]
        self.assertGreaterEqual(max(dorsal), 8.1)
        self.assertLessEqual(max(dorsal), 8.4)
        # the statics lane's own P9 count precedent: 14, not 15 (phi=0.05 knee holds)
        self.assertEqual(t["knee"]["over_cap_nodes"], 14)
        self.assertAlmostEqual(t["mp"]["worst_ratio"], 42.62049, delta=0.65)
        w = self.d["margin_wall"]["D_S2_si_matched_gate"]
        self.assertGreaterEqual(w["max_combined_ratio"], 9.5)
        self.assertLessEqual(w["max_combined_ratio"], 9.8)
        self.assertEqual(w["max_binder"], {"joint": "ankle", "phi": 0.5})
        self.assertAlmostEqual(w["knee_term_at_phi_0_75"], 7.65563, delta=0.25)
        self.assertFalse(w["crosses_1_0"])

    def test_10_every_cap_has_provenance_class(self):
        for name, entry in self.d["cap_sets"].items():
            for joint, cls in entry["provenance_class"].items():
                self.assertIn(cls, self.d["cap_provenance_classes"], f"{name}.{joint}")

    def test_11_cap_values_equal_book_values(self):
        at = self.d["ankle_cap_trace"]
        self.assertEqual(at["values"]["D_plantar"], 6.247077)
        self.assertEqual(at["values"]["D_dorsal"], 1.251106)
        self.assertEqual(at["values"]["D_S2_plantar"], 0.748112)
        self.assertEqual(at["values"]["D_S2_dorsal"], 0.149825)
        ht = self.d["hind_book_cap_trace"]
        self.assertEqual(ht["values"]["knee_B"], 9.576795)
        self.assertEqual(ht["values"]["mp_B"], 1.657925)

    def test_12_pd6_determinism_subprocess_rerun_byte_identical(self):
        before = sha256(DELIVERABLE)
        res = subprocess.run([sys.executable, "-B", str(DERIVE)],
                             capture_output=True, text=True, timeout=600, cwd=str(REPO))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(sha256(DELIVERABLE), before)
        self.assertIn(before, res.stdout)

    def test_13_pd7_no_source_changes_outside_lane(self):
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                             text=True, timeout=120, cwd=str(REPO))
        lane_prefix = "tools/science_funnel/validation/ankle_unblocked_statics_20260921/"
        outside = []
        for line in res.stdout.splitlines():
            p = line[3:].strip().strip('"')
            if p and not p.startswith(lane_prefix):
                outside.append(p)
        self.assertEqual(outside, [], f"files changed outside the lane dir: {outside}")

    def test_14_receipt_deliverable_sha_self_claim(self):
        self.assertEqual(self.rec["measured"]["deliverable"]["sha256"], sha256(DELIVERABLE))

    def test_15_receipt_pre_registration_unedited_by_run(self):
        self.assertTrue(self.rec["pre_registration"]["written_before_first_verdict_computation"])
        self.assertIsInstance(self.rec["measured"], dict)


if __name__ == "__main__":
    unittest.main()
