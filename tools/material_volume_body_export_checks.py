"""Analytic checks for isolated explicit rigid-body material-mass exports.

Run: python tools/material_volume_body_export_checks.py
"""
from __future__ import annotations

import copy
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import material_volume_admission as admission
import material_volume_body_export as exporter


ROOT = Path(__file__).resolve().parent


def read_examples():
    def read(name):
        return json.loads((ROOT / name).read_text(encoding="utf-8"))
    return (read("material_volume_body_export_manifest_example.json"),
            read("material_volume_body_export_partition_example.json"),
            read("material_volume_body_export_groups_example.json"))


def tet_integrals(vertices, tet, density):
    """Independent raw-origin simplex integral for one analytically authored tet."""
    x = np.asarray(vertices, dtype=np.float64)[np.asarray(tet)]
    volume = float(np.linalg.det((x[1:] - x[0]).T) / 6.0)
    if volume <= 0:
        raise AssertionError("analytic fixture tet must be positively oriented")
    mass = volume * float(density)
    sum_x = np.sum(x, axis=0)
    first = mass * sum_x / 4.0
    raw_second = mass * (x.T @ x + np.outer(sum_x, sum_x)) / 20.0
    return volume, mass, first, raw_second


def combine_oracle(vertices, cells, density_by_material):
    volume = mass = 0.0
    first = np.zeros(3)
    raw_second = np.zeros((3, 3))
    for cell in cells:
        v, m, f, q = tet_integrals(vertices, cell["vertex_ids"],
                                   density_by_material[cell["material_id"]])
        volume += v
        mass += m
        first += f
        raw_second += q
    center = first / mass
    central = raw_second - mass * np.outer(center, center)
    inertia = np.trace(central) * np.eye(3) - central
    return volume, mass, center, inertia


def exported_group(report, body_id):
    return next(row for row in report["body_groups"] if row["body_id"] == body_id)


class MaterialVolumeBodyExportChecks(unittest.TestCase):
    def test_two_explicit_group_masses_recombine_to_partition_total(self):
        manifest, partition, groups = read_examples()
        report = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(report["export_status"], "complete")
        self.assertEqual(report["admission_status"], "validation_only_admissible")
        self.assertFalse(report["dynamics_readiness_claimed"])
        self.assertTrue(report["all_supplied_cells_assigned"])
        a = exported_group(report, "coupon-body-A")["mass_properties"]
        b = exported_group(report, "coupon-body-B")["mass_properties"]
        self.assertEqual(a["mass"]["value"], 2.0)
        self.assertEqual(b["mass"]["value"], 1.0)
        self.assertEqual(a["volume"]["value"], 1.0 / 6.0)
        self.assertEqual(b["volume"]["value"], 1.0 / 6.0)

        positions = np.asarray([row["position"] for row in partition["vertices"]])
        index = {row["vertex_id"]: i for i, row in enumerate(partition["vertices"])}
        region_material = {row["region_id"]: row["material_id"]
                           for row in partition["regions"]}
        cells = [{"cell_id": row["cell_id"],
                  "material_id": region_material[row["proposals"][0]],
                  "vertex_ids": [index[x] for x in row["vertex_ids"]]}
                 for row in partition["cells"]]
        density_by_material = {row["material_id"]: row["density_kg_m3"]
                               for row in partition["materials"]}
        volume, mass, center, inertia = combine_oracle(positions, cells, density_by_material)
        self.assertAlmostEqual(a["mass"]["value"] + b["mass"]["value"], mass, places=14)
        body_centers_domain = []
        body_inertias_domain = []
        for group in groups["body_groups"]:
            exported = exported_group(report, group["body_id"])["mass_properties"]
            props = exported
            R = np.asarray(group["body_frame"]["domain_from_body"]["rotation"])
            origin = np.asarray(group["body_frame"]["domain_from_body"]["origin_m"])
            center_body = np.asarray(props["center_of_mass"]["value"])
            I_body = np.asarray(props["inertia_tensor_about_com"]["value"])
            center_domain = R @ center_body + origin
            I_domain = R @ I_body @ R.T
            body_centers_domain.append((props["mass"]["value"], center_domain))
            body_inertias_domain.append((props["mass"]["value"], center_domain, I_domain))
        combined_center = sum(m * c for m, c in body_centers_domain) / mass
        np.testing.assert_allclose(combined_center, center, rtol=0.0, atol=1e-14)
        combined_inertia = np.zeros((3, 3))
        for m, c, local_inertia in body_inertias_domain:
            d = c - center
            combined_inertia += local_inertia + m * ((d @ d) * np.eye(3) - np.outer(d, d))
        np.testing.assert_allclose(combined_inertia, inertia, rtol=0.0, atol=2e-14)
        self.assertAlmostEqual(a["volume"]["value"] + b["volume"]["value"], volume, places=14)
        # Independent oracle gives coupon mass = 3 kg, COM=(7/12,-7/12,5/12)m.
        self.assertAlmostEqual(mass, 3.0, places=14)
        np.testing.assert_allclose(center, [13.0 / 12.0, -5.0 / 12.0, 7.0 / 12.0],
                                   rtol=0.0, atol=1e-14)

    def test_authored_translation_and_rotation_transform_com_and_full_tensor(self):
        manifest, partition, groups = read_examples()
        report = exporter.build_export_report(manifest, partition, groups)
        body_b = exported_group(report, "coupon-body-B")["mass_properties"]
        np.testing.assert_allclose(body_b["center_of_mass"]["value"], [0.25, 0.25, 0.25],
                                   rtol=0.0, atol=1e-15)
        tensor = np.asarray(body_b["inertia_tensor_about_com"]["value"])
        expected = np.full((3, 3), 0.0125)
        np.fill_diagonal(expected, 0.075)
        np.testing.assert_allclose(tensor, expected, rtol=0.0, atol=2e-16)
        metadata = body_b["inertia_tensor_about_com"]
        self.assertTrue(metadata["full_symmetric_tensor"])
        self.assertTrue(metadata["off_diagonal_terms_preserved"])
        self.assertFalse(metadata["principal_axis_transform_applied"])
        self.assertEqual(metadata["coordinate_frame"], "coupon-B-authored")
        self.assertEqual(body_b["center_of_mass"]["coordinate_frame"], "coupon-B-authored")
        self.assertEqual(body_b["mass"]["coordinate_frame"], "frame_invariant")

        # An alternate authored frame has x_domain = R*x_body + origin.
        group_b = groups["body_groups"][1]
        group_b["body_frame"]["domain_from_body"]["origin_m"] = [2.0, -2.0, 1.0]
        changed = exporter.build_export_report(manifest, partition, groups)
        center = exported_group(changed, "coupon-body-B")["mass_properties"]["center_of_mass"]
        np.testing.assert_allclose(center["value"], [0.25, -0.75, 0.25],
                                   rtol=0.0, atol=1e-15)
        self.assertNotEqual(report["input_hashes"]["body_groups_sha256"],
                            changed["input_hashes"]["body_groups_sha256"])

    def test_duplicate_cell_ownership_refuses_instead_of_double_counting(self):
        manifest, partition, groups = read_examples()
        groups["body_groups"][1]["cell_ids"].append("cell-A")
        report = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(report["export_status"], "refused")
        self.assertIn("duplicate_cell_ownership", report["reason_codes"])
        self.assertEqual(report["body_groups"], [])

    def test_unassigned_cells_are_reported_and_not_silently_included(self):
        manifest, partition, groups = read_examples()
        groups["body_groups"] = groups["body_groups"][:1]
        report = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(report["export_status"], "partial")
        self.assertEqual(report["unassigned_cell_ids"], ["cell-B"])
        self.assertFalse(report["all_supplied_cells_assigned"])
        self.assertEqual(len(report["body_groups"]), 1)
        self.assertEqual(report["body_groups"][0]["owned_cell_ids"], ["cell-A"])

    def test_missing_density_blocks_export_and_keeps_affected_cell(self):
        manifest, partition, groups = read_examples()
        material = next(row for row in partition["materials"]
                        if row["material_id"] == "tissue-B")
        material["density_kg_m3"] = None
        material["density_source"] = None
        material["conditions"] = None
        report = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(report["export_status"], "blocked")
        self.assertEqual(report["admission_status"], "not_admitted")
        self.assertIsNone(exported_group(report, "coupon-body-A")["mass_properties"])
        self.assertEqual(exported_group(report, "coupon-body-B")["blocking_cell_ids"], ["cell-B"])
        self.assertEqual(exported_group(report, "coupon-body-B")["blocking_assignment_statuses"],
                         [{"cell_id": "cell-B", "status": "missing_density"}])

    def test_source_effective_authority_returns_explicit_unsupported_without_mass_reads(self):
        manifest, partition, groups = read_examples()
        manifest["mass_authority"] = admission.AUTHORITY_EFFECTIVE_SEGMENT
        manifest["source_effective_segment_ids"] = ["segment-A", "segment-B"]
        manifest["matter_ownership"] = [
            {"matter_id": "source-A", "representation": "source_effective_segment",
             "mass_owner_id": "segment-A"},
            {"matter_id": "source-B", "representation": "source_effective_segment",
             "mass_owner_id": "segment-B"}]
        partition["mass_authority"] = admission.AUTHORITY_EFFECTIVE_SEGMENT
        # Prove no effective segment numeric mass field is needed or consumed.
        manifest["source_effective_segment_masses_kg"] = {"segment-A": 9999.0}
        # Unknown mass fields are rejected by admission, but unsupported authority
        # must remain explicit and must not emit/import any mass values.
        report = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(report["export_status"], "unsupported")
        self.assertEqual(report["admission_status"], "refused")
        self.assertFalse(report["source_effective_segment_payloads_consumed"])
        self.assertTrue(all(row["export_status"] == "not_exported"
                            for row in report["body_groups"]))
        self.assertTrue(all(row["mass_properties"] is None for row in report["body_groups"]))

        # With a valid explicit source authority, disposition is still unsupported.
        manifest.pop("source_effective_segment_masses_kg")
        valid = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(valid["export_status"], "unsupported")
        self.assertEqual(valid["admission_status"], "validation_only_admissible")
        self.assertFalse(valid["source_effective_segment_payloads_consumed"])
        self.assertTrue(all(row["mass_properties"] is None for row in valid["body_groups"]))

    def test_refuses_untrusted_passed_flag_and_nonrigid_or_reflected_frame(self):
        manifest, partition, groups = read_examples()
        groups["admission_status"] = "validation_only_admissible"
        report = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(report["export_status"], "refused")
        self.assertIn("bad_schema", report["reason_codes"])
        manifest, partition, groups = read_examples()
        groups["body_groups"][0]["body_frame"]["domain_from_body"]["rotation"][0][0] = 2.0
        report = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(report["export_status"], "refused")
        self.assertIn("invalid_authored_frame", report["reason_codes"])
        manifest, partition, groups = read_examples()
        groups["body_groups"][0]["body_frame"]["domain_from_body"]["rotation"] = [
            [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        report = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(report["export_status"], "refused")
        self.assertIn("invalid_authored_frame", report["reason_codes"])

    def test_report_hashes_and_cli_output_are_deterministic_and_finite(self):
        manifest, partition, groups = read_examples()
        a = exporter.build_export_report(manifest, partition, groups)
        b = exporter.build_export_report(manifest, partition, groups)
        self.assertEqual(exporter.canonical_json(a), exporter.canonical_json(b))
        self.assertEqual(a["schema_version"], exporter.EXPORT_SCHEMA)
        self.assertTrue(all(len(a["input_hashes"][name]) == 64
                            for name in exporter._HASH_NAMES))
        self.assertNotIn("NaN", exporter.canonical_json(a))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MaterialVolumeBodyExportChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
