"""k-forensics-20260921 tests: input sha pins, determinism (subprocess),
k-table reproduction, no source changes outside the lane dir, mesh
provenance, and the pre-registered check verdicts as measured."""
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parent
REPO = LANE.parents[3]
BOOK = LANE / "k_forensics_book.json"
DERIVE = LANE / "derive_k_forensics.py"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class KForensics(unittest.TestCase):
    def test_inputs_match_receipt_pins(self):
        receipt = json.loads((LANE / "receipt.json").read_text())
        for name, pin in receipt["pre_registration"]["inputs_pinned"].items():
            if "sha256" not in pin:
                continue
            self.assertEqual(sha256_file(REPO / pin["path"]), pin["sha256"], name)

    def test_derive_subprocess_reproducible(self):
        """A subprocess rerun must reproduce the committed deliverable bytes."""
        before = sha256_file(BOOK)
        r = subprocess.run(
            [sys.executable, "-B", str(DERIVE)],
            capture_output=True,
            text=True,
            timeout=1200,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        after = sha256_file(BOOK)
        self.assertEqual(before, after, "subprocess rerun changed the deliverable bytes")

    def test_determinism_two_runs_byte_identical(self):
        out = subprocess.run(
            [sys.executable, "-B", str(DERIVE)],
            capture_output=True,
            text=True,
            timeout=1200,
        )
        self.assertIn("byte-identical): True", out.stdout, out.stdout + out.stderr)
        self.assertNotIn("determinism (two in-process runs byte-identical): False", out.stdout)

    def test_k_table_reproduces_published_constants(self):
        book = json.loads(BOOK.read_text())
        krep = book["k_table_reproduction"]
        self.assertTrue(krep["mtp_class"]["within_tol"])
        self.assertTrue(krep["ankle_point_class"]["within_tol"])
        self.assertTrue(krep["knee_class"]["within_published_bound"])
        self.assertTrue(krep["all_within_tolerance"])
        # the three-joint k table, pinned against the published constants
        t = krep["the_three_joints_table"]
        self.assertAlmostEqual(t["mtp_flexion"]["k"], 0.11975394, places=8)
        self.assertAlmostEqual(t["ankle_flexion"]["k"], 0.11976026, places=8)
        self.assertLessEqual(t["knee_extension"]["post_k_residual_bound_mm"], 0.089)

    def test_mesh_provenance_verified(self):
        book = json.loads(BOOK.read_text())
        prov = book["mesh_provenance"]
        self.assertTrue(len(prov["meshes"]) == 4)
        for key, m in prov["meshes"].items():
            self.assertTrue(m["sha256"], key)
            self.assertEqual(m["sha256"], sha256_file(m["file"]), key)

    def test_check1_anatomical_verdicts_as_measured(self):
        book = json.loads(BOOK.read_text())
        c1 = book["check1_anatomical_scale"]
        dl = c1["deposit_vs_literature"]
        self.assertIn("ADULT", dl["femur_class"], "pre-registered falsifier (a) FIRED")
        self.assertIn("ADULT", dl["tibia_class"], "pre-registered falsifier (a) FIRED")
        self.assertLessEqual(c1["left_right_consistency"]["femur"]["rel_diff_pct"], 2.0)
        self.assertLessEqual(c1["left_right_consistency"]["tibia"]["rel_diff_pct"], 2.0)
        # stray-vertex guard: diameter must not be inflated over PCA extent
        for m in c1["mesh_measures"].values():
            self.assertLessEqual(m["diameter_minus_pca1_mm"], 5.0)

    def test_check2_angle_invariance_and_no_anchor(self):
        book = json.loads(BOOK.read_text())
        c2 = book["check2_consistency"]
        self.assertEqual(c2["angle_invariance"]["mismatches"], [])
        self.assertTrue(c2["angle_invariance"]["all_scan_ranges_inside_model_coordinate_ranges"])
        self.assertGreaterEqual(c2["angle_invariance"]["si_jrange_vs_committed_scans_checked"], 26)
        self.assertFalse(c2["si2_sheet"]["absolute_scale_anchor_present"])
        self.assertEqual(c2["si1_docx"]["absolute_scale_anchor_hits"], [])
        k = c2["cross_taxon_single_artifact_check"]["committed_cross_taxon_k"]
        self.assertNotAlmostEqual(k["macaque"], k["gorilla"], places=3)
        self.assertNotAlmostEqual(k["macaque"], k["gibbon"], places=3)

    def test_no_source_changes_outside_lane_dir(self):
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=120,
        )
        offenders = []
        for line in r.stdout.splitlines():
            path = line[3:].strip().strip('"')
            if path and not path.replace("\\", "/").startswith(
                "tools/science_funnel/validation/k_forensics_20260921/"
            ):
                offenders.append(line)
        self.assertEqual(offenders, [], "files changed outside the lane dir:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
