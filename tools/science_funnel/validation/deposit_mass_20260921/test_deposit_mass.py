"""deposit-mass-20260921 tests: input sha pins, determinism (in-process +
subprocess), packet-sum reproduction, pre-registered comparison verdicts,
placeholder signature adjudication, and no source changes outside the lane
dir. Mirrors test_k_forensics.py."""
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parent
REPO = LANE.parents[3]
BOOK = LANE / "deposit_mass_book.json"
DERIVE = LANE / "derive_deposit_mass_book.py"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class DepositMass(unittest.TestCase):
    def test_inputs_match_receipt_pins(self):
        receipt = json.loads((LANE / "receipt.json").read_text(encoding="utf-8"))
        pins = receipt["pre_registration"]["inputs_pinned"]
        # repin_20260921: the receipt's appended re-pin section supersedes the
        # pre-repair (autocrlf-smudged) pins per path on the repaired lineage.
        repins = {
            r["path"]: r["new_sha256"]
            for r in receipt.get("repin_20260921", {}).get("re_pins", [])
        }
        for name, pin in pins.items():
            if "sha256" not in pin and "sha256_manifest_entry" not in pin:
                continue
            want = pin.get("sha256") or pin.get("sha256_manifest_entry")
            if "path" not in pin:
                continue
            self.assertEqual(sha256_file(REPO / pin["path"]), want, name)
        for r in receipt.get("repin_20260921", {}).get("re_pins", []):
            self.assertEqual(
                sha256_file(REPO / r["path"]), r["new_sha256"], r["pin_name"]
            )
        # the k-lane book pin, quoted from the k-lane receipt (re-pinned
        # second-order: the k deliverable regenerated with its post-repair
        # provenance; see receipt repin_20260921 re_pins)
        kbook = REPO / "tools/science_funnel/validation/k_forensics_20260921/k_forensics_book.json"
        self.assertEqual(
            sha256_file(kbook),
            repins.get(
                "tools/science_funnel/validation/k_forensics_20260921/k_forensics_book.json",
                "0c2d8b397a158283f19a8ff81a8f6be5f6a787ac09c09b7394c70e5402166b4b",
            ),
        )

    def test_parse_refuses_on_sha_mismatch(self):
        """The load-refusal falsifier (f): a tampered manifest must stop the run."""
        import shutil
        import tempfile
        manifest = REPO / "tools/science_funnel/data/wiseman2026/sha256_manifest.json"
        backup = manifest.read_bytes()
        tmpdir = tempfile.mkdtemp()
        try:
            m = json.loads(backup.decode("utf-8"))
            for f in m["files"]:
                if f["path"] == "models/Macaque_model.osim":
                    f["sha256"] = "0" * 64
            manifest.write_text(json.dumps(m), encoding="utf-8")
            r = subprocess.run(
                [sys.executable, "-B", str(DERIVE)],
                capture_output=True, text=True, timeout=1200,
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("LOAD REFUSED", r.stdout + r.stderr)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            manifest.write_bytes(backup)
        self.assertEqual(sha256_file(manifest), hashlib.sha256(backup).hexdigest())

    def test_determinism_inprocess_two_runs(self):
        out = subprocess.run(
            [sys.executable, "-B", str(DERIVE)],
            capture_output=True, text=True, timeout=1200,
        )
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("determinism (two in-process runs byte-identical): True", out.stdout)
        self.assertNotIn("determinism (two in-process runs byte-identical): False", out.stdout)

    def test_derive_subprocess_reproducible(self):
        """A subprocess rerun must reproduce the committed deliverable bytes."""
        before = sha256_file(BOOK)
        r = subprocess.run(
            [sys.executable, "-B", str(DERIVE)],
            capture_output=True, text=True, timeout=1200,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sha256_file(BOOK), before, "subprocess rerun changed the bytes")

    def test_packet_sum_reproduced(self):
        book = json.loads(BOOK.read_text(encoding="utf-8"))
        mm = book["macaque_masses"]
        self.assertEqual(mm["n_bodies"], 10)
        self.assertTrue(mm["packet_reproduced"])
        self.assertLessEqual(mm["abs_diff_vs_packet_kg"], 0.0005)
        self.assertAlmostEqual(mm["sum_kg"], sum(b["mass_kg"] for b in mm["bodies"]), places=9)

    def test_comparison_verdicts_as_pre_registered(self):
        book = json.loads(BOOK.read_text(encoding="utf-8"))
        comp = book["comparison"]
        band = book["expected_band"]
        # expected envelope recomputed from the pinned constants
        self.assertAlmostEqual(band["expected_kg"]["min"], 0.99737, places=5)
        self.assertAlmostEqual(band["expected_kg"]["max"], 1.656, places=9)
        self.assertAlmostEqual(band["oku_model_total_kg"], 10.038, places=9)
        self.assertAlmostEqual(band["oku_hindlimb_chain_fraction"], 0.184698, places=5)
        # the anomaly verdicts
        self.assertTrue(comp["anomaly_real_at_conservative_bound"])
        self.assertFalse(comp["sum_inside_expected_envelope"])
        self.assertGreater(comp["deficit_factor_envelope"]["min"], 1.0)

    def test_scale_and_signature_adjudication(self):
        book = json.loads(BOOK.read_text(encoding="utf-8"))
        st = book["scale_tests"]
        self.assertFalse(st["linear_closure"]["closes"])
        self.assertFalse(st["cube_law_closure"]["closes"])
        self.assertAlmostEqual(st["linear_closure"]["required_source_pelvis_hindlimb_kg"],
                               0.7717839 / st["k"], places=5)
        sig = book["placeholder_signature"]
        self.assertFalse(sig["s1_uniformity"]["uniform_if_spread_le_1e9_rel"])
        self.assertFalse(sig["s3_cross_taxon_identity"]["all_taxa_identical_body_mass_sets"])
        # the lateral-inconsistency measurement: foot L/R 10.9x, foot_r ~= R_Hallux
        call = sig["s2_lateral_symmetry"]["lateral_inconsistency_callout"]
        self.assertGreater(call["foot_l_over_foot_r"], 10.0)
        self.assertLess(abs(call["foot_r_minus_R_Hallux_kg"]), 1e-6)
        # the pre-registered closure rule
        cl = book["hypothesis_closures"]
        self.assertFalse(cl["a_template_placeholder"]["closes"])
        self.assertFalse(cl["b_geometric_scaling"]["linear_k_closes"])
        self.assertFalse(cl["b_geometric_scaling"]["cube_law_k3_closes"])
        self.assertTrue(cl["c_genuinely_low"]["closes"])

    def test_no_source_changes_outside_lane_dir(self):
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO), capture_output=True, text=True, timeout=120,
        )
        offenders = []
        for line in r.stdout.splitlines():
            path = line[3:].strip().strip('"')
            if path and not path.replace("\\", "/").startswith(
                "tools/science_funnel/validation/deposit_mass_20260921/"
            ):
                offenders.append(line)
        self.assertEqual(offenders, [],
                         "files changed outside the lane dir:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
