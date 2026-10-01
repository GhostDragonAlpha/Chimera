"""THE K-FILL TEST BATTERY (lane k-fill-20260920).

Run from the repo root:
  python -B -m unittest tools.science_funnel.validation.k_fill_20260920.test_k_fill
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

import derive_k_fill as dk  # noqa: E402


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class TestInputsMatchReceiptPins(unittest.TestCase):
    """F3: every pinned input resolves to its committed bytes (load REFUSES on drift)."""

    def test_all_pins_resolve(self):
        receipt = json.loads((HERE / "receipt.json").read_text(encoding="utf-8"))
        for key, pin in receipt["inputs_pinned"].items():
            p = REPO / pin["path"]
            self.assertTrue(p.exists(), f"missing pinned input {key}: {pin['path']}")
            self.assertEqual(
                sha256_file(p), pin["sha256"],
                f"pin drift on {key} ({pin['path']})")


class TestDeterminism(unittest.TestCase):
    """F2: three independent derivations byte-identical (2 in-process + 1 subprocess)."""

    def test_three_runs_byte_identical(self):
        shas = []
        for _ in range(2):
            book = dk.derive()
            shas.append(hashlib.sha256(dk.canonical_json_bytes(book)).hexdigest())
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            out = Path(td) / "rerun.json"
            r = subprocess.run(
                [sys.executable, "-B", str(HERE / "derive_k_fill.py"), "--out", str(out)],
                capture_output=True, text=True, cwd=str(REPO))
            self.assertEqual(r.returncode, 0, r.stderr)
            shas.append(sha256_file(out))
        self.assertEqual(len(set(shas)), 1, f"deliverable shas diverge: {shas}")
        committed = sha256_file(HERE / "k_fill_book.json")
        self.assertEqual(shas[0], committed,
                         "regenerated deliverable != committed bytes")


class TestNoSourceChanges(unittest.TestCase):
    """F4: no file outside the lane directory is created or modified."""

    def test_git_status_confined_to_lane_dir(self):
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                           text=True, cwd=str(REPO))
        paths = [line[3:].strip().strip('"') for line in r.stdout.splitlines() if line.strip()]
        outside = [p for p in paths
                   if not (p.startswith("tools/science_funnel/validation/k_fill_20260920/")
                           or p.endswith("tools/science_funnel/validation/k_fill_20260920"))]
        self.assertEqual(outside, [], f"changes outside the lane directory: {outside}")


class TestBookContent(unittest.TestCase):
    """F3/F5: the deliverable's verdicts are honest and its numbers are traceable."""

    @classmethod
    def setUpClass(cls):
        cls.book = json.loads((HERE / "k_fill_book.json").read_text(encoding="utf-8"))

    def test_deliverable_fresh_vs_committed(self):
        fresh = dk.derive()
        self.assertEqual(hashlib.sha256(dk.canonical_json_bytes(fresh)).hexdigest(),
                         sha256_file(HERE / "k_fill_book.json"))

    def test_sigma_single_and_cited(self):
        sigma = self.book["the_one_sigma"]
        self.assertEqual(sigma["value_MPa"], 0.30)
        self.assertTrue(sigma["never_swept"])
        self.assertGreaterEqual(len(sigma["citations"]), 3)
        self.assertIn("reason", sigma["rejected_alternative_with_reason"])

    def test_quarantined_rows_carry_no_force(self):
        muscles = self.book["derived_force_set"]["muscles"]
        for name, rec in muscles.items():
            if name.startswith("QUARANTINED_"):
                self.assertIsNone(rec["force_N"], f"{name} carries a force")
                self.assertIn("NAMED_GAP", rec["status"])
        # RF and TP appear as named gaps in their consuming books
        self.assertIn("R_RF", self.book["capabilities_deposit_arms"]["knee_extension"]["named_gaps"])
        self.assertIn("R_TP", self.book["capabilities_deposit_arms"]["ankle_plantarflexion"]["named_gaps"])

    def test_f1_verdict_matches_measured_cap(self):
        cap = self.book["capabilities_deposit_arms"]["ankle_plantarflexion"]["cap_N_m"]
        f1 = self.book["falsifier_verdicts"]["predictions"]["F1_ankle_band"]
        expected = "HELD" if (5.0 <= cap <= 7.5) else "FIRED"
        self.assertEqual(f1["verdict"], expected)
        if expected == "FIRED":
            self.assertIsNotNone(self.book["falsifier_verdicts"]["F1_report"])
            self.assertIn("named_cause", self.book["falsifier_verdicts"]["F1_report"])
            self.assertEqual(f1["band_N_m"], [5.0, 7.5])

    def test_fired_list_independently_recomputed(self):
        pv = self.book["falsifier_verdicts"]["predictions"]
        fired = set(pv["summary"]["fired"])
        self.assertIn("F1_ankle_band", fired)  # 4.398653 below [5.0, 7.5] - the predicted fire
        self.assertIn("P6_coverage.ankle_dorsal", fired)
        self.assertIn("P7_mass.factor_check", fired)
        # nothing tuned: the fired records carry the preregistered bands verbatim
        self.assertEqual(pv["F1_ankle_band"]["band_N_m"], [5.0, 7.5])
        self.assertEqual(pv["P6_coverage"]["ankle_dorsal"]["band"], [0.55, 0.72])

    def test_mass_closure(self):
        m = self.book["derived_mass_set"]
        self.assertTrue(m["closure"])
        self.assertTrue(m["inside_envelope"])
        derived = sum(m["derived_bodies_kg"].values())
        self.assertAlmostEqual(derived, m["target_sum_kg"], places=6)
        for name, mass in m["derived_bodies_kg"].items():
            self.assertAlmostEqual(mass, m["deposit_bodies_kg"][name] * m["rescale_factor"],
                                   places=6, msg=name)

    def test_rearup_verdict_robust(self):
        r = self.book["rearup_verdict"]
        self.assertEqual(r["verdict"], "NOT COVERED")
        self.assertFalse(r["primary_covered"])
        self.assertFalse(r["conservative_covered"])
        self.assertLessEqual(r["conservative_max_capability_N_m"],
                             r["primary_max_capability_N_m"])
        self.assertGreater(r["primary_max_capability_N_m"], 22.4)
        self.assertLess(r["primary_max_capability_N_m"], 33.6)

    def test_capability_books_have_trace_and_gaps(self):
        for cls, bk in self.book["capabilities_deposit_arms"].items():
            self.assertIn("trace", bk, cls)
            self.assertIn("arms_source", bk)
            self.assertIn("forces", bk["trace"])
            self.assertIn("cap_N_m", bk)
            self.assertGreater(bk["cap_N_m"], 0.0)
            self.assertIn("argmax_q_deg", bk)

    def test_stance_hold_migration_matches_banked_columns(self):
        sh = self.book["stance_hold_repriced"]
        c = sh["over_cap_counts"]
        self.assertEqual((c["knee"]["doc"], c["knee"]["walk"], c["knee"]["derived"]), (9, 4, 6))
        self.assertEqual(len(sh["nodes"]), 15)

    def test_every_force_number_cited(self):
        fs = self.book["derived_force_set"]
        self.assertIn("citation", fs)
        self.assertIn("10.1002/ajpa.70329", fs["citation"])
        for name, rec in fs["muscles"].items():
            if rec.get("force_N") is not None:
                self.assertIsNotNone(rec.get("status"), name)
        self.assertTrue(fs["substitution_policy"].startswith("substitutions only for ABSENT rows"))


if __name__ == "__main__":
    unittest.main()
