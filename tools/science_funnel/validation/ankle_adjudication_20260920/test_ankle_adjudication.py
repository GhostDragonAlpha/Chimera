"""THE ANKLE-ADJUDICATION TEST BATTERY (lane ankle-adjudication-20260920).

Run from the repo root:
  python -B -m unittest tools.science_funnel.validation.ankle_adjudication_20260920.test_ankle_adjudication
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))

import derive_adjudication as da  # noqa: E402


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class TestInputsMatchReceiptPins(unittest.TestCase):
    """F3: every pinned input resolves to its committed bytes (load REFUSES on drift)."""

    def test_all_pins_resolve(self):
        receipt = json.loads((HERE / "receipt.json").read_text(encoding="utf-8"))
        for key, pin in receipt["inputs_pinned"].items():
            p = REPO / pin["path"]
            self.assertTrue(p.exists(), f"missing pinned input {key}: {pin['path']}")
            self.assertEqual(sha256_file(p), pin["sha256"],
                             f"pin drift on {key} ({pin['path']})")


class TestDeterminism(unittest.TestCase):
    """F4: three independent derivations byte-identical (2 in-process + 1 subprocess)."""

    def test_three_runs_byte_identical(self):
        shas = []
        for _ in range(2):
            table = da.main()
            shas.append(hashlib.sha256(da.canonical_json_bytes(table)).hexdigest())
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            out = Path(td) / "rerun.json"
            r = subprocess.run(
                [sys.executable, "-B", str(HERE / "derive_adjudication.py"), "--out", str(out)],
                capture_output=True, text=True, cwd=str(REPO))
            self.assertEqual(r.returncode, 0, r.stderr)
            shas.append(sha256_file(out))
        self.assertEqual(len(set(shas)), 1, f"deliverable shas diverge: {shas}")
        committed = sha256_file(HERE / "adjudication_table.json")
        self.assertEqual(shas[0], committed,
                         "regenerated table != committed bytes")


class TestNoSourceChanges(unittest.TestCase):
    """F5: no file outside the lane directory is created or modified."""

    def test_git_status_confined_to_lane_dir(self):
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                           text=True, cwd=str(REPO))
        lane_prefix = "tools/science_funnel/validation/ankle_adjudication_20260920/"
        paths = [line[3:].strip().strip('"') for line in r.stdout.splitlines() if line.strip()]
        outside = [p for p in paths if not (p.startswith(lane_prefix))]
        self.assertEqual(outside, [], f"changes outside the lane directory: {outside}")


class TestTableContent(unittest.TestCase):
    """The table's verdicts are honest, traced, and match the pinned sources."""

    @classmethod
    def setUpClass(cls):
        cls.table = json.loads((HERE / "adjudication_table.json").read_text(encoding="utf-8"))
        cls.book = json.loads(
            (REPO / "tools/science_funnel/validation/k_fill_20260920/k_fill_book.json")
            .read_text(encoding="utf-8"))
        cls.snap = json.loads(
            (REPO / "tools/science_funnel/validation/hind_torque_book_20260921/inputs/"
                     "derived_numbers.snapshot.json").read_text(encoding="utf-8"))
        cls.arms = json.loads(
            (REPO / "tools/science_funnel/validation/ankle_arms_20260921/ankle_arms_book.json")
            .read_text(encoding="utf-8"))

    def test_all_pins_verified_true(self):
        self.assertTrue(all(self.table["inputs_verified"].values()))

    def test_sigma_diagnostic_never_adopted_and_nondiscriminating(self):
        s = self.table["sigma_diagnostic"]
        self.assertFalse(s["adopted"])
        self.assertEqual(s["assumed_sigma_MPa"], 0.30)
        self.assertEqual(s["verdict"], "NON_DISCRIMINATING")
        self.assertTrue(s["contained_in_reported_span"])
        # diagnostic == the gap factor times the assumed sigma, nothing adopted
        self.assertAlmostEqual(
            s["diagnostic_sigma_MPa"],
            0.30 * (s_gap := (self.table["the_finding_under_adjudication"]["plantar_demand_N_m"]
                              / self.table["the_finding_under_adjudication"]["plantar_cap_N_m"])),
            places=5)
        self.assertAlmostEqual(s["gap_factor"], s_gap, places=4)

    def test_concentration_held_per_prereg(self):
        c = self.table["concentration"]
        self.assertTrue(c["concentrated"])
        self.assertGreaterEqual(c["plantar_spread"], c["preregistered_threshold"])
        # the SOL outlier and the GAS match, against the pinned snapshot bytes
        sol = c["sol_row"]
        self.assertEqual(sol["oku_before_peak_N"], self.snap["oku_muscle_forces_N"]["before"]["SOL"]["peak_N"])
        self.assertAlmostEqual(sol["ratio_vs_before_peak"],
                               sol["derived_N"] / sol["oku_before_peak_N"], places=5)
        gas = c["gas_row"]
        self.assertEqual(gas["oku_before_peak_N"], self.snap["oku_muscle_forces_N"]["before"]["GAS"]["peak_N"])

    def test_arm_door_matches_banked_ankle_book(self):
        v1 = self.arms["cap_book"]["ankle_plantarflexion"]["V1_S1_oku_walk_peaks_deposit_arms"]
        tri = self.arms["cap_book"]["ankle_plantarflexion"]["triceps_only_subenvelope_V1_S1"]
        a = self.table["arm_door"]
        self.assertEqual(a["V1_S1_cap_N_m"], v1["cap_N_m"])
        self.assertEqual(a["triceps_only_subenvelope_N_m"], tri["cap_N_m"])
        self.assertAlmostEqual(a["V1_S1_reproduction_ratio"], v1["cap_N_m"] / 5.9171, places=5)

    def test_verdict_inputs(self):
        vi = self.table["verdict_inputs"]
        self.assertEqual(vi["C_arm_side"]["status"], "EXCLUDED")
        self.assertEqual(vi["B_demand_side"]["status"], "PRIMARY")
        self.assertEqual(vi["A_architecture_side"]["status"], "PARTIALLY_SUPPORTED_AS_SECONDARY")
        self.assertFalse(vi["A_architecture_side"]["method_asymmetry_found"])
        m = vi["B_demand_side"]["evidence"]["simulation_context"]
        self.assertEqual(m["speed_grade_flavor_of_B"].split()[0], "DEAD")
        self.assertTrue(m["subjects_flavor_of_B"].startswith("HELD"))
        self.assertTrue(m["peak_flavor_of_B"].startswith("HELD"))

    def test_mass_context_arithmetic(self):
        mc = self.table["mass_context"]
        self.assertEqual(mc["demand_source_animal_kg"], 10.038)
        self.assertEqual(mc["game_band_midpoint_kg"], 6.15)
        lin = 5.9171 * (6.15 / 10.038)
        geo = 5.9171 * (6.15 / 10.038) ** (4.0 / 3.0)
        self.assertAlmostEqual(mc["linear_mass_scaled_N_m"], lin, places=5)
        self.assertAlmostEqual(mc["geometric_scaled_torque_proportional_to_M_4_3_N_m"], geo, places=5)
        self.assertGreater(mc["coverage_linear_scaled"], 1.0)
        self.assertGreater(mc["coverage_geometric_scaled"], 1.0)

    def test_oku_context_is_the_pinned_simulation_paper(self):
        ctx = self.table["oku_2021_context"]
        self.assertEqual(ctx["doi"], "10.1038/s42003-021-01831-w")
        self.assertEqual(ctx["pmcid"], "PMC7940622")
        self.assertIn("Forward dynamic simulation", ctx["title"])

    def test_inherited_quarantined_rows_stay_gaps(self):
        mus = self.book["derived_force_set"]["muscles"]
        for name, rec in mus.items():
            if name.startswith("QUARANTINED_"):
                self.assertIsNone(rec["force_N"], f"{name} carries a force")

    def test_finding_matches_k_fill_book(self):
        f = self.table["the_finding_under_adjudication"]
        wc = self.book["walk_coverage"]
        self.assertEqual(f["plantar_cap_N_m"], wc["ankle_plantarflexion"]["cap_N_m"])
        self.assertEqual(f["plantar_demand_N_m"], wc["ankle_plantarflexion"]["oku_walk_demand_N_m"])
        self.assertAlmostEqual(f["plantar_coverage"],
                               wc["ankle_plantarflexion"]["coverage_ratio"], places=5)


if __name__ == "__main__":
    unittest.main()
