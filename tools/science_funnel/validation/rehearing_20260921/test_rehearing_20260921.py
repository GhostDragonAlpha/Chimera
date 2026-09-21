"""Unittests for the re-hearing lane (wave-10 collocation at the measured caps).

Asserts, per the receipt's falsifiers_pre_registered:
  - traceability: every pinned input's sha256 equals the receipt pin at run time
  - git-object pins: the vendored wave-10 machinery traces to 4198dbdc
    (generator blob f3f65483..., statics module blob 5319bc26... IDENTICAL at
    the wave-10 base 54472e63, deliverable byte-equal to the banked json,
    derived_numbers byte-equal to blob 8b6d75fb...)
  - instrument reproduction (PR1): the vendored generator reproduces the banked
    optimum in the pre-registered bands
  - reprice chain (PR2): the lane's (d) wall re-price equals the statics chain's
    committed D wall block field-for-field
  - maximin bound + verdict direction (PR3): the bound in band, the over-unity
    node set as registered, every run respecting the bound, the CLOSED verdict
  - shift bands (PR4) and the S2 inversion bracket (PR5)
  - determinism (PR6): a subprocess rerun of the derive script reproduces the
    deliverable sha256 byte-for-byte
  - no_source_changes (PR7): git status --porcelain names nothing outside this
    lane dir

Run:  python -B -m unittest tools.science_funnel.validation.rehearing_20260921.test_rehearing_20260921
"""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parent
REPO = LANE.parents[3]
DERIVE = LANE / "derive_rehearing_collocation.py"
DELIVERABLE = LANE / "rehearing_20260921.json"
RECEIPT = LANE / "receipt.json"


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class TestRehearingCollocation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads(RECEIPT.read_text(encoding="utf-8"))
        cls.d = json.loads(DELIVERABLE.read_text(encoding="utf-8"))

    # ---- traceability ----

    def test_01_input_shas_match_receipt_pins(self):
        for name, (path, want) in {
            "wave10_generator": (LANE / "inputs/vendored_gait_zero/derive_reachable_vault.py",
                                 "0c722cffae81268c2a4933ed3f482e7af6c942afe66e35f9d6380893d1acf2a5"),
            "wave10_statics_module": (LANE / "inputs/vendored_gait_zero/derive_trunk_pitch.py",
                                      "5be624d304f029d6de92559650a438bca531c30b6eaf111c1459d0e9374fac16"),
            "wave10_deliverable": (LANE / "inputs/vendored_gait_zero/trunk_vault_reachable.wave10.json",
                                   "e922153318778e4cd8c1891f59454261c6d5be0a77aebdc5f78d2758ccd2faa7"),
            "derived_numbers": (LANE / "inputs/run_env/tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json",
                                "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173"),
            "ankle_arms_book": (LANE / "inputs/ankle_arms_book.json",
                                "7ce03069c1e033b52db0fb315d218eb2223e79a67a9018123da206d68adcb6f6"),
            "hind_torque_book": (REPO / "tools/science_funnel/validation/hind_torque_book_20260921/hind_torque_book.json",
                                 "9fc5c0ba09f6ec183d5348bb21cc5dc18b5987240406ccdcdbb34e514e26f01c"),
            "statics_lane_committed_deliverable": (LANE / "inputs/statics_lane_committed_deliverable.json",
                                                   "21d3dbbe2a477d67f7d7d5572f0171cd0c2e8cfe34a6cd1770ccd81abf06908a"),
            "ankle_lane_committed_deliverable": (LANE / "inputs/ankle_lane_committed_deliverable.json",
                                                 "31c6e3fb717c310086e0bf023b8b45f6cf2335692e15e9794eaa325f402184ea"),
        }.items():
            self.assertEqual(sha256(path), want, name)

    def test_02_wave10_machinery_git_object_pinned(self):
        """The vendored generator is the blob banked beside the wave-10
        deliverable and receipt; the statics module did not drift across the
        wave-10 lineage (identical blob at the wave-10 base and at 4198dbdc)."""
        for ref, want in (
            ("4198dbdc:tools/science_funnel/validation/gait_zero_20260919/derive_reachable_vault.py",
             "f3f65483b477b98bcb73bc9490ffbac538df8a33"),
            ("4198dbdc:tools/science_funnel/validation/gait_zero_20260919/derive_trunk_pitch.py",
             "5319bc2649c042dd2a482ea105a3150a2255d10d"),
            ("54472e63:tools/science_funnel/validation/gait_zero_20260919/derive_trunk_pitch.py",
             "5319bc2649c042dd2a482ea105a3150a2255d10d"),
            ("4198dbdc:tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json",
             "8b6d75fbd408a8e1e2db31cdf15fc4a104b9a36a"),
        ):
            res = subprocess.run(["git", "rev-parse", ref], capture_output=True, text=True,
                                 timeout=120, cwd=str(REPO))
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertEqual(res.stdout.strip(), want, ref)
        res = subprocess.run(
            ["git", "rev-parse",
             "b15ff31e:tools/science_funnel/validation/ankle_arms_20260921/ankle_arms_book.json"],
            capture_output=True, text=True, timeout=120, cwd=str(REPO))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "f55ebe5f94109fe3c659c13cc6d46598591b9595")

    def test_03_receipt_pre_registered_before_script(self):
        pre = self.rec["pre_registration"]
        self.assertTrue(pre["written_before_first_verdict_computation"])
        self.assertIn("PR3_maximin_bound_and_verdict_direction", pre["pre_registered_predictions"])
        # the receipt pins the deliverable (never the reverse: the receipt's
        # measured block is appended after the derive, so the deliverable only
        # carries the receipt's derivation-time sha)
        self.assertEqual(self.d["receipt"]["path"],
                         "tools/science_funnel/validation/rehearing_20260921/receipt.json")
        self.assertEqual(self.rec["measured"]["deliverable"]["sha256"], sha256(DELIVERABLE))
        self.assertEqual(self.d["derived_from_commit"], "906368142212a5ff18b13bf4b0e5088e36a1a81d")

    # ---- PR1 instrument ----

    def test_04_instrument_reproduction_in_bands(self):
        ck = self.d["instrument_reproduction"]["checks"]
        self.assertTrue(ck["held"], ck)
        for f in ("max_ratio_to_cap", "max_posture_ratio_to_cap", "objective"):
            self.assertTrue(ck[f]["in_band"], f)
        self.assertTrue(ck["success"]["equal"] and ck["feasible"]["equal"] and ck["verdict_class"]["equal"])

    def test_05_wrapper_drift_exact(self):
        self.assertTrue(self.d["wrapper_drift_check"]["exact"])
        self.assertEqual(self.d["wrapper_drift_check"]["n_mismatches"], 0)

    # ---- PR2 reprice chain ----

    def test_06_reprice_d_chain_field_for_field(self):
        r = self.d["reprice_D_chain"]
        self.assertTrue(r["field_for_field_equal"], r["field_diffs"])
        self.assertEqual(r["committed_ref_sha256"],
                         "31c6e3fb717c310086e0bf023b8b45f6cf2335692e15e9794eaa325f402184ea")
        self.assertEqual(r["wall"]["max_combined_ratio"], 1.157587)
        self.assertEqual(r["wall"]["max_binder"], {"joint": "ankle", "phi": 0.5})
        self.assertEqual(r["wall"]["binder_histogram"], {"ankle": 9, "hip": 1, "knee": 4, "posture": 7})

    # ---- PR3 maximin bound + verdict direction ----

    def test_07_maximin_bound_in_band(self):
        b = self.d["maximin_bound"]["D"]
        self.assertGreaterEqual(b["maximin_lower_bound"], 1.040)
        self.assertLessEqual(b["maximin_lower_bound"], 1.048)
        self.assertEqual(b["binding_node_phi"], 0.4)
        self.assertEqual(b["over_unity_lb_phis"], [0.3, 0.35, 0.4, 0.45])
        s2 = self.d["maximin_bound"]["S2"]
        self.assertGreaterEqual(s2["maximin_lower_bound"], 8.40)
        self.assertLessEqual(s2["maximin_lower_bound"], 8.51)

    def test_08_bound_respected_by_every_D_run(self):
        self.assertTrue(self.d["verdict"]["bound_respected_by_every_run"])
        lb = self.d["verdict"]["maximin_bound_D"]
        for run in self.d["collocation_runs"]["D"]["runs"]:
            self.assertGreaterEqual(run["wall_max_combined"], lb - 1e-9, run["start"])
            self.assertTrue(run["posture_constraint_holds"], run["start"])

    def test_09_closed_verdict(self):
        v = self.d["verdict"]
        self.assertFalse(v["crosses_1_0"])
        self.assertGreaterEqual(v["achievable_wall_D"], 1.0)
        self.assertLessEqual(v["achievable_wall_D"], 1.20)
        self.assertGreaterEqual(v["achievable_wall_D"], 1.0439 - 1e-9)
        self.assertIn("CLOSED", v["verdict"])

    # ---- PR4 shift bands ----

    def test_10_shift_bands(self):
        """PR4 as MEASURED: the wall band held; the theta-shift sub-prediction
        FIRED and is recorded in the receipt's falsifier verdicts (never
        absorbed) - the test asserts the fire is on the table."""
        best = self.d["verdict"]["achieving_run"]
        run = next(r for r in self.d["collocation_runs"]["D"]["runs"] if r["start"] == best)
        wall = run["wall_max_combined"]
        self.assertGreaterEqual(wall, 1.0439 - 1e-9)
        self.assertLessEqual(wall, 1.16)
        node = next(n for n in self.d["trajectory_shift"]["per_node"] if n["phi"] == 0.4)
        measured_delta = node["theta_delta_rad"]
        band_lo, band_hi = -1.0, -0.3
        fired = not (band_lo <= measured_delta <= band_hi)
        self.assertTrue(fired, "the registered theta-shift band held - update the receipt's PR4 letter")
        self.assertIn("FIRED", self.rec["measured"]["falsifier_verdicts"]["PR4_shift_prediction"])
        self.assertIn("-0.075119694", self.rec["measured"]["falsifier_verdicts"]["PR4_shift_prediction"])
        self.assertEqual(measured_delta, -0.075119694)

    # ---- PR5 S2 bracket ----

    def test_11_s2_inversion_bracket(self):
        for run in self.d["collocation_runs"]["S2"]["runs"]:
            self.assertGreaterEqual(run["wall_max_combined"], 8.40, run["start"])
        self.assertIn("inverts", self.d["verdict"]["scale_gate"])

    # ---- PR6 determinism (subprocess rerun, byte-for-byte) ----

    def test_12_determinism_subprocess_rerun(self):
        before = sha256(DELIVERABLE)
        res = subprocess.run([sys_exec(), "-B", str(DERIVE)], capture_output=True, text=True,
                             timeout=14400, cwd=str(REPO))
        self.assertEqual(res.returncode, 0, res.stderr[-4000:])
        self.assertEqual(sha256(DELIVERABLE), before)

    # ---- PR7 no source changes ----

    def test_13_no_source_changes_outside_lane(self):
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                             timeout=120, cwd=str(REPO))
        self.assertEqual(res.returncode, 0, res.stderr)
        offenders = []
        for line in res.stdout.splitlines():
            path = line[3:].strip().strip('"')
            if path and not path.startswith("tools/science_funnel/validation/rehearing_20260921/"):
                offenders.append(path)
        self.assertEqual(offenders, [])


def sys_exec():
    import sys
    return sys.executable


if __name__ == "__main__":
    unittest.main()
