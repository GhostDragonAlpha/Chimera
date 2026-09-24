"""Integrated verification (package 3 of the body-export proof battery).

Reproduces the reported legacy suites (17 compiler + 21 admission + 8 export
checks), CLI determinism, and reader validation; runs both coupon proof
suites; and audits the coupons for shared implementation assumptions that
could make exporter and oracle agree incorrectly. This verifies bounded
export proofs only: no anatomical correctness, mechanical qualification, or
dynamics readiness.

Run: python tools/material_volume_export_proof_verify.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import material_volume_body_export as exporter
import material_volume_body_export_reader as reader

LEGACY_SUITES = {"material_volume_checks.py": 17,
                 "material_volume_admission_checks.py": 21,
                 "material_volume_body_export_checks.py": 8}
PROOF_SUITES = {"material_volume_shared_interface_proof.py": 5,
                "material_volume_frame_composition_proof.py": 8}
PROOF_FILES = tuple(PROOF_SUITES)

TOL = 1e-12


def run_suite(name):
    proc = subprocess.run([sys.executable, name], cwd=str(ROOT),
                          capture_output=True)
    text = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    count = re.search(r"Ran (\d+) tests?", text)
    return proc.returncode, (int(count.group(1)) if count else None), text


def run_cli(manifest, partition, groups):
    proc = subprocess.run(
        [sys.executable, "material_volume_body_export.py",
         "--manifest", manifest, "--partition", partition, "--groups", groups],
        cwd=str(ROOT), capture_output=True)
    return proc.returncode, proc.stdout


class ExportProofIntegratedVerification(unittest.TestCase):
    maxDiff = None

    def test_reproduced_legacy_suites_are_17_21_8(self):
        for name, expected_count in LEGACY_SUITES.items():
            code, count, text = run_suite(name)
            self.assertEqual(code, 0, f"{name} exit {code}:\n{text[-2000:]}")
            self.assertEqual(count, expected_count, name)
            self.assertIn("\nOK", text, name)

    def test_proof_suites_pass(self):
        for name, expected_count in PROOF_SUITES.items():
            code, count, text = run_suite(name)
            self.assertEqual(code, 0, f"{name} exit {code}:\n{text[-2000:]}")
            self.assertEqual(count, expected_count, name)
            self.assertIn("\nOK", text, name)

    def test_cli_determinism_and_saved_example_bytes(self):
        code1, out1 = run_cli("material_volume_body_export_manifest_example.json",
                              "material_volume_body_export_partition_example.json",
                              "material_volume_body_export_groups_example.json")
        code2, out2 = run_cli("material_volume_body_export_manifest_example.json",
                              "material_volume_body_export_partition_example.json",
                              "material_volume_body_export_groups_example.json")
        self.assertEqual(code1, 0)
        self.assertEqual(code2, 0)
        self.assertEqual(out1, out2, "CLI output must be byte-identical across runs")
        saved = (ROOT / "material_volume_body_export_example_report.json").read_bytes()
        self.assertEqual(out1, saved,
                         "saved example report must be the canonical CLI bytes")
        # Coupon runs are deterministic too.
        for manifest, partition, groups in (
                ("material_volume_shared_interface_manifest_example.json",
                 "material_volume_shared_interface_partition_example.json",
                 "material_volume_shared_interface_groups_example.json"),
                ("material_volume_frame_composition_manifest_example.json",
                 "material_volume_frame_composition_partition_example.json",
                 "material_volume_frame_composition_groups_shared_example.json"),
                ("material_volume_frame_composition_manifest_example.json",
                 "material_volume_frame_composition_partition_example.json",
                 "material_volume_frame_composition_groups_composed_example.json")):
            code_a, out_a = run_cli(manifest, partition, groups)
            code_b, out_b = run_cli(manifest, partition, groups)
            self.assertEqual(code_a, 0, f"{groups} exit {code_a}")
            self.assertEqual(out_a, out_b, f"{groups} not deterministic")
            self.assertEqual(json.loads(out_a)["export_status"], "complete", groups)

    def test_reader_accepts_example_and_coupon_reports(self):
        saved = json.loads((ROOT / "material_volume_body_export_example_report.json")
                           .read_text(encoding="utf-8"))
        reports = {"saved_example": saved}
        for label, manifest_name, partition_name, groups_name in (
                ("si_coupon",
                 "material_volume_shared_interface_manifest_example.json",
                 "material_volume_shared_interface_partition_example.json",
                 "material_volume_shared_interface_groups_example.json"),
                ("fc_shared",
                 "material_volume_frame_composition_manifest_example.json",
                 "material_volume_frame_composition_partition_example.json",
                 "material_volume_frame_composition_groups_shared_example.json"),
                ("fc_composed",
                 "material_volume_frame_composition_manifest_example.json",
                 "material_volume_frame_composition_partition_example.json",
                 "material_volume_frame_composition_groups_composed_example.json")):
            manifest = json.loads((ROOT / manifest_name).read_text(encoding="utf-8"))
            partition = json.loads((ROOT / partition_name).read_text(encoding="utf-8"))
            groups = json.loads((ROOT / groups_name).read_text(encoding="utf-8"))
            reports[label] = exporter.build_export_report(manifest, partition, groups)
        for label, report in reports.items():
            summary = reader.summarize_export_report(report)
            self.assertFalse(summary["dynamics_readiness_claimed"], label)
            self.assertFalse(summary["physical_state_mutated"], label)
            for body in summary["bodies"]:
                if body["export_status"] == "exported":
                    tensor = body["inertia_tensor_about_com"]
                    self.assertTrue(tensor["full_symmetric_tensor"], label)
                    self.assertTrue(tensor["off_diagonal_terms_preserved"], label)
                    self.assertFalse(tensor["principal_axis_transform_applied"], label)

    def test_audit_proof_oracles_do_not_import_shared_code(self):
        allowed_roots = {"__future__", "json", "math", "sys", "unittest", "copy",
                         "pathlib", "material_volume_body_export"}
        forbidden_tokens = (
            "tet_integrals", "combine_oracle", "oracle_simplex",
            "material_volume_checks", "material_volume_admission",
            "material_volume_body_export_checks", "material_volume_body_export_reader",
            "material_volume_export_proof_prereg_derivation",
            "material_volume_shared_interface_proof",
            "material_volume_frame_composition_proof",
            "numpy", "np.", "exporter.")
        oracle_prefixes = ("quadrature_", "combine_raw", "shared_face", "recombine",
                           "transform_points", "congruence_", "mat_", "vsub")
        for name in PROOF_FILES:
            src = (ROOT / name).read_text(encoding="utf-8")
            roots = set()
            for match in re.finditer(r"(?m)^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_.]*)",
                                     src):
                roots.add(match.group(1).split(".")[0])
            self.assertLessEqual(roots, allowed_roots,
                                 f"{name} imports outside the audit allowlist: "
                                 f"{sorted(roots - allowed_roots)}")
            for block in re.split(r"\n(?=def |class )", src):
                head = block.split("(", 1)[0].strip()
                is_oracle = head.endswith(oracle_prefixes) or any(
                    head.endswith("def " + p) or head == "def " + p or head.startswith("def " + p)
                    for p in oracle_prefixes)
                if not is_oracle:
                    continue
                for token in ("exporter.", "np.", "numpy"):
                    self.assertNotIn(token, block,
                                     f"{name} oracle block {head!r} uses {token}")
            for token in forbidden_tokens:
                if token == "exporter.":
                    continue  # allowed outside oracle blocks (component under test)
                if token in ("material_volume_shared_interface_proof",
                             "material_volume_frame_composition_proof"):
                    other = ("material_volume_frame_composition_proof.py"
                             if "shared_interface" in name
                             else "material_volume_shared_interface_proof.py")
                    self.assertNotIn(token, src.replace(name, ""),
                                     f"{name} references {token}")
                    continue
                self.assertNotIn(token, src, f"{name} contains forbidden token {token}")

    def test_audit_quadrature_oracles_are_file_local(self):
        for name in PROOF_FILES:
            src = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("(5.0 + 3.0 * math.sqrt(5.0)) / 20.0", src,
                          f"{name} lacks its own Hammer-Stroud point construction")
            self.assertIn("(5.0 - math.sqrt(5.0)) / 20.0", src,
                          f"{name} lacks its own Hammer-Stroud point construction")

    def test_audit_perturbation_tracking_agrees_with_quadrature(self):
        # A density perturbation must move exporter and oracle together, so
        # agreement with the frozen literals is not coincidental constants.
        manifest = json.loads(
            (ROOT / "material_volume_shared_interface_manifest_example.json")
            .read_text(encoding="utf-8"))
        partition = json.loads(
            (ROOT / "material_volume_shared_interface_partition_example.json")
            .read_text(encoding="utf-8"))
        groups = json.loads(
            (ROOT / "material_volume_shared_interface_groups_example.json")
            .read_text(encoding="utf-8"))
        for material in partition["materials"]:
            if material["material_id"] == "si-tissue-A":
                material["density_kg_m3"] = 13.0
        report = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(report["export_status"], "complete")
        row = next(r for r in report["body_groups"] if r["body_id"] == "si-body-A")
        observed_mass = row["mass_properties"]["mass"]["value"]
        self.assertLessEqual(abs(observed_mass - 13.0 / 6.0), TOL,
                             f"perturbed mass {observed_mass!r} vs 13/6")


if __name__ == "__main__":
    unittest.main()
