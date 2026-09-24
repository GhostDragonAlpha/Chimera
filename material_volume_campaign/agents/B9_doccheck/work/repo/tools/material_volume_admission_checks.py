"""Independent checks for fitting-manifest material-volume admission.

Run: python tools/material_volume_admission_checks.py

These tests exercise the standalone adapter and compiler as pure functions. No
Chimera runtime state or production integration is imported or mutated.
"""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import material_volume as mv
import material_volume_admission as admission


ROOT = Path(__file__).resolve().parent


def examples():
    manifest = json.loads((ROOT / "material_volume_admission_manifest_example.json")
                          .read_text(encoding="utf-8"))
    partition = json.loads((ROOT / "material_volume_admission_partition_example.json")
                           .read_text(encoding="utf-8"))
    return manifest, partition


def canonical(report):
    return admission.canonical_json(report)


def transform_positions(document, matrix, shift):
    for vertex in document["vertices"]:
        vertex["position"] = (matrix @ np.asarray(vertex["position"], dtype=np.float64)
                              + shift).tolist()


def subdivide_document(manifest, partition):
    """Centroid-split every parent tet into four positively oriented children."""
    outward = ((1, 2, 3), (0, 3, 2), (0, 1, 3), (0, 2, 1))
    manifest = copy.deepcopy(manifest)
    partition = copy.deepcopy(partition)
    m_vertices = {row["vertex_id"]: row["position"] for row in manifest["vertices"]}
    p_vertices = {row["vertex_id"]: row["position"] for row in partition["vertices"]}
    assert m_vertices == p_vertices
    new_m_vertices = list(manifest["vertices"])
    new_p_vertices = list(partition["vertices"])
    m_children, p_children = [], []
    cells_by_id = {row["cell_id"]: row for row in partition["cells"]}
    for parent in manifest["cells"]:
        ids = parent["vertex_ids"]
        center_id = f"{parent['cell_id']}-center"
        center = np.mean([m_vertices[vertex_id] for vertex_id in ids], axis=0).tolist()
        new_m_vertices.append({"vertex_id": center_id, "position": center})
        new_p_vertices.append({"vertex_id": center_id, "position": center})
        for child_i, face in enumerate(outward):
            child_ids = [center_id, *(ids[index] for index in face)]
            child_id = f"{parent['cell_id']}-child-{child_i}"
            m_children.append({"cell_id": child_id, "vertex_ids": child_ids,
                               "component_id": parent["component_id"]})
            p_children.append({"cell_id": child_id, "vertex_ids": child_ids,
                               "proposals": list(cells_by_id[parent["cell_id"]]["proposals"])})
    manifest["vertices"] = new_m_vertices
    partition["vertices"] = new_p_vertices
    manifest["cells"] = m_children
    partition["cells"] = p_children
    return manifest, partition


def two_component_fixture():
    points = np.asarray([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    shift = np.array([3., 0., 0.])
    frame = {"frame_id": "two-component-local", "handedness": "right",
             "coordinate_unit": "m", "scale_to_m": 1.0}
    manifest_vertices, partition_vertices = [], []
    manifest_cells, partition_cells = [], []
    for prefix, offset, component in (("a", np.zeros(3), "component-a"),
                                      ("b", shift, "component-b")):
        ids = [f"{prefix}{i}" for i in range(4)]
        for vertex_id, point in zip(ids, points + offset):
            vertex = {"vertex_id": vertex_id, "position": point.tolist()}
            manifest_vertices.append(copy.deepcopy(vertex))
            partition_vertices.append(copy.deepcopy(vertex))
        cell_id = f"cell-{prefix}"
        manifest_cells.append({"cell_id": cell_id, "vertex_ids": ids,
                               "component_id": component})
        partition_cells.append({"cell_id": cell_id, "vertex_ids": ids,
                                "proposals": ["whole"]})
    material_record = {"material_id": "tissue", "density_kg_m3": 2.0,
                       "density_source": "fixture", "conditions": "uniform"}
    region_record = {"region_id": "whole", "mass_owner_id": "whole-owner",
                     "material_id": "tissue"}
    manifest = {"schema_version": admission.MANIFEST_SCHEMA,
                "fitting_id": "two-component-fixture", "domain_id": "two-components",
                "domain_revision": "v1", "coordinate_frame": frame,
                "vertices": manifest_vertices, "cells": manifest_cells,
                "regions": [region_record],
                "mass_authority": admission.AUTHORITY_RECONSTRUCTED,
                "source_effective_segment_ids": [],
                "matter_ownership": [{"matter_id": "all-tissue",
                                       "representation": "tetrahedral_volume",
                                       "mass_owner_id": "whole-owner"}]}
    partition = {"schema_version": admission.PARTITION_SCHEMA,
                 "coordinate_frame": copy.deepcopy(frame), "vertices": partition_vertices,
                 "cells": partition_cells, "materials": [material_record],
                 "regions": [region_record],
                 "mass_authority": admission.AUTHORITY_RECONSTRUCTED}
    return manifest, partition


class MaterialVolumeAdmissionChecks(unittest.TestCase):
    def test_matching_manifest_admits_and_report_is_canonical_and_pure(self):
        manifest, partition = examples()
        original = (copy.deepcopy(manifest), copy.deepcopy(partition))
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "validation_only_admissible")
        self.assertFalse(report["physical_state_mutated"])
        self.assertFalse(report["production_wired"])
        self.assertFalse(report["anatomical_completeness_certified"])
        self.assertTrue(report["correspondence"]["intended_domain_fully_represented"])
        self.assertTrue(report["assignments"]["supplied_cells_accounted_for"])
        self.assertEqual(report["mass_authority"]["choice"],
                         admission.AUTHORITY_RECONSTRUCTED)
        self.assertEqual(report["mass_authority"]["reconstructed_mass_properties"]["mass_kg"],
                         1.0)
        self.assertEqual((manifest, partition), original)
        self.assertEqual(canonical(report), canonical(admission.build_admission_report(
            manifest, partition)))
        self.assertTrue(canonical(report).endswith("\n"))
        self.assertNotIn("NaN", canonical(report))

    def test_cell_and_vertex_list_reordering_preserves_entire_report(self):
        manifest, partition = examples()
        manifest["vertices"].reverse()
        partition["vertices"].reverse()
        manifest["cells"].reverse()
        partition["cells"].reverse()
        report_a = admission.build_admission_report(*examples())
        report_b = admission.build_admission_report(manifest, partition)
        self.assertEqual(canonical(report_a), canonical(report_b))
        self.assertEqual(report_b["decision"], "validation_only_admissible")

    def test_vertex_id_bijection_preserves_canonical_geometry_identity(self):
        manifest, partition = examples()
        baseline = admission.build_admission_report(manifest, partition)
        rename = {"v0": "node-z", "v1": "node-a", "v2": "node-q",
                  "v3": "node-c", "v4": "node-x"}
        for document in (manifest, partition):
            for vertex in document["vertices"]:
                vertex["vertex_id"] = rename[vertex["vertex_id"]]
            for cell in document["cells"]:
                cell["vertex_ids"] = [rename[value] for value in cell["vertex_ids"]]
        changed = admission.build_admission_report(manifest, partition)
        self.assertEqual(changed["decision"], "validation_only_admissible")
        self.assertEqual(changed["identity"]["expected_geometry_signature"],
                         baseline["identity"]["expected_geometry_signature"])
        self.assertEqual(changed["identity"]["supplied_geometry_signature"],
                         baseline["identity"]["supplied_geometry_signature"])

    def test_rigid_transform_preserves_mass_and_transforms_com_and_inertia(self):
        manifest, partition = examples()
        baseline = admission.build_admission_report(manifest, partition)
        base_props = baseline["mass_authority"]["reconstructed_mass_properties"]
        rotation = np.asarray([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
        shift = np.asarray([4.5, -2.25, 8.0])
        transform_positions(manifest, rotation, shift)
        transform_positions(partition, rotation, shift)
        changed = admission.build_admission_report(manifest, partition)
        self.assertEqual(changed["decision"], "validation_only_admissible")
        self.assertNotEqual(changed["identity"]["expected_geometry_signature"],
                            baseline["identity"]["expected_geometry_signature"])
        moved = changed["mass_authority"]["reconstructed_mass_properties"]
        self.assertAlmostEqual(moved["mass_kg"], base_props["mass_kg"], places=14)
        self.assertAlmostEqual(moved["volume_m3"], base_props["volume_m3"], places=14)
        expected_com = rotation @ np.asarray(base_props["center_of_mass_m"]) + shift
        np.testing.assert_allclose(moved["center_of_mass_m"], expected_com,
                                   rtol=0.0, atol=2e-14)
        base_inertia = np.asarray(base_props["inertia_com_kg_m2"])
        expected_inertia = rotation @ base_inertia @ rotation.T
        np.testing.assert_allclose(moved["inertia_com_kg_m2"], expected_inertia,
                                   rtol=0.0, atol=2e-14)

    def test_uniform_geometric_scale_changes_identity_and_obeys_mass_property_laws(self):
        manifest, partition = examples()
        baseline = admission.build_admission_report(manifest, partition)
        scale = 2.75
        for document in (manifest, partition):
            for vertex in document["vertices"]:
                vertex["position"] = (np.asarray(vertex["position"]) * scale).tolist()
        changed = admission.build_admission_report(manifest, partition)
        self.assertEqual(changed["decision"], "validation_only_admissible")
        self.assertNotEqual(changed["identity"]["expected_geometry_signature"],
                            baseline["identity"]["expected_geometry_signature"])
        base = baseline["mass_authority"]["reconstructed_mass_properties"]
        enlarged = changed["mass_authority"]["reconstructed_mass_properties"]
        self.assertAlmostEqual(enlarged["volume_m3"] / base["volume_m3"], scale ** 3,
                               delta=2e-12 * scale ** 3)
        self.assertAlmostEqual(enlarged["mass_kg"] / base["mass_kg"], scale ** 3,
                               delta=2e-12 * scale ** 3)
        np.testing.assert_allclose(np.asarray(enlarged["inertia_com_kg_m2"])
                                   / np.asarray(base["inertia_com_kg_m2"]),
                                   np.full((3, 3), scale ** 5), rtol=2e-12, atol=1e-11)

    def test_equivalent_coordinate_units_preserve_si_identity_and_mass_properties(self):
        manifest, partition = examples()
        baseline = admission.build_admission_report(manifest, partition)
        base_properties = baseline["mass_authority"]["reconstructed_mass_properties"]
        for document in (manifest, partition):
            frame = document["coordinate_frame"]
            frame["coordinate_unit"] = "half-metre"
            frame["scale_to_m"] = 0.5
            for vertex in document["vertices"]:
                vertex["position"] = (np.asarray(vertex["position"]) * 2.0).tolist()
        changed = admission.build_admission_report(manifest, partition)
        self.assertEqual(changed["decision"], "validation_only_admissible")
        self.assertTrue(changed["correspondence"]["coordinate_frame_matches"])
        self.assertTrue(changed["correspondence"]["scale_to_m_matches"])
        self.assertEqual(changed["identity"]["expected_geometry_signature"],
                         baseline["identity"]["expected_geometry_signature"])
        self.assertEqual(changed["identity"]["supplied_geometry_signature"],
                         baseline["identity"]["supplied_geometry_signature"])
        properties = changed["mass_authority"]["reconstructed_mass_properties"]
        self.assertAlmostEqual(properties["mass_kg"], base_properties["mass_kg"], places=14)
        self.assertAlmostEqual(properties["volume_m3"], base_properties["volume_m3"], places=14)
        np.testing.assert_allclose(properties["center_of_mass_m"],
                                   base_properties["center_of_mass_m"], rtol=0.0, atol=0.0)
        np.testing.assert_allclose(properties["inertia_com_kg_m2"],
                                   base_properties["inertia_com_kg_m2"], rtol=0.0, atol=0.0)

    def test_scale_declaration_is_compared_not_guessed_or_repaired(self):
        manifest, partition = examples()
        partition["coordinate_frame"]["scale_to_m"] = 0.5
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "not_admitted")
        self.assertFalse(report["correspondence"]["scale_to_m_matches"])
        self.assertIn("scale_mismatch", report["reason_codes"])

    def test_homogeneous_subdivision_preserves_mass_but_changes_cell_identity(self):
        manifest, partition = examples()
        coarse = admission.build_admission_report(manifest, partition)
        fine_manifest, fine_partition = subdivide_document(manifest, partition)
        fine = admission.build_admission_report(fine_manifest, fine_partition)
        self.assertEqual(fine["decision"], "validation_only_admissible")
        self.assertEqual(fine["correspondence"]["expected_cell_count"], 8)
        self.assertNotEqual(fine["identity"]["expected_geometry_signature"],
                            coarse["identity"]["expected_geometry_signature"])
        coarse_props = coarse["mass_authority"]["reconstructed_mass_properties"]
        fine_props = fine["mass_authority"]["reconstructed_mass_properties"]
        self.assertAlmostEqual(fine_props["volume_m3"], coarse_props["volume_m3"], places=14)
        self.assertAlmostEqual(fine_props["mass_kg"], coarse_props["mass_kg"], places=14)
        np.testing.assert_allclose(fine_props["center_of_mass_m"],
                                   coarse_props["center_of_mass_m"], rtol=0.0, atol=2e-15)
        np.testing.assert_allclose(fine_props["inertia_com_kg_m2"],
                                   coarse_props["inertia_com_kg_m2"], rtol=0.0, atol=3e-15)

    def test_shared_face_orientation_survives_positive_cell_permutation(self):
        manifest, partition = examples()
        baseline = admission.build_admission_report(manifest, partition)
        first_face = baseline["geometry"]["interfaces"][0]
        # A three-cycle of the upper tet vertices is even, so it preserves the
        # signed orientation while changing its local vertex order.
        upper = next(row for row in partition["cells"] if row["cell_id"] == "cell-upper")
        upper["vertex_ids"] = [upper["vertex_ids"][0], upper["vertex_ids"][2],
                               upper["vertex_ids"][3], upper["vertex_ids"][1]]
        permuted = admission.build_admission_report(manifest, partition)
        self.assertEqual(permuted["decision"], "validation_only_admissible")
        face = permuted["geometry"]["interfaces"][0]
        self.assertEqual(face["face_vertex_ids"], first_face["face_vertex_ids"])
        np.testing.assert_allclose(face["normal_a_to_b"], first_face["normal_a_to_b"],
                                   rtol=0.0, atol=0.0)
        self.assertEqual(face["oriented_vertex_ids_a_to_b"],
                         first_face["oriented_vertex_ids_a_to_b"])

    def test_region_relabeling_changes_interface_direction_not_geometry_identity(self):
        manifest, partition = examples()
        baseline = admission.build_admission_report(manifest, partition)
        for cell in partition["cells"]:
            cell["proposals"] = ["region-B" if cell["cell_id"] == "cell-upper"
                                 else "region-A"]
        relabeled = admission.build_admission_report(manifest, partition)
        self.assertEqual(relabeled["decision"], "validation_only_admissible")
        self.assertEqual(relabeled["identity"]["supplied_geometry_signature"],
                         baseline["identity"]["supplied_geometry_signature"])
        before = baseline["geometry"]["interfaces"][0]
        after = relabeled["geometry"]["interfaces"][0]
        self.assertEqual((before["region_a_id"], before["region_b_id"]),
                         ("region-A", "region-B"))
        self.assertEqual((after["region_a_id"], after["region_b_id"]),
                         ("region-A", "region-B"))
        np.testing.assert_allclose(after["normal_a_to_b"], [0., 0., 1.],
                                   rtol=0.0, atol=0.0)
        self.assertAlmostEqual(before["area_m2"], after["area_m2"], places=15)

    def test_touching_and_overlapping_tetrahedra_are_distinguished_across_scales(self):
        material = [mv.MaterialSpec("tissue", 1.0, "fixture", "uniform")]
        region = [mv.RegionSpec("whole", "owner", "tissue")]
        for scale in (1e-8, 1.0, 1e8):
            bipyramid = np.asarray([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                                    [0., 0., 1.], [0., 0., -1.]]) * scale
            touching = mv.compile_partition(bipyramid,
                np.asarray([[0, 1, 2, 3], [0, 2, 1, 4]], dtype=np.int64),
                material, region, [["whole"], ["whole"]])
            self.assertTrue(touching.complete)
            self.assertEqual(touching.connected_components, 1)

            unit = np.asarray([[0., 0., 0.], [1., 0., 0.],
                               [0., 1., 0.], [0., 0., 1.]]) * scale
            overlap = np.vstack([unit, unit + np.asarray([0.05, 0.05, 0.05]) * scale])
            tets = np.asarray([[0, 1, 2, 3], [4, 5, 6, 7]], dtype=np.int64)
            with self.subTest(scale=scale), self.assertRaises(mv.CompileError) as raised:
                mv.compile_partition(overlap, tets, material, region,
                                     [["whole"], ["whole"]])
            self.assertEqual(raised.exception.reason, mv.CompilerReason.OVERLAPPING_TETRAHEDRA)

    def test_missing_cell_is_reported_even_when_remaining_tet_is_watertight(self):
        manifest, partition = examples()
        partition["cells"] = [row for row in partition["cells"]
                              if row["cell_id"] == "cell-upper"]
        used = {vertex_id for cell in partition["cells"] for vertex_id in cell["vertex_ids"]}
        partition["vertices"] = [row for row in partition["vertices"]
                                 if row["vertex_id"] in used]
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "not_admitted")
        self.assertTrue(report["geometry"]["topology_valid"])
        self.assertTrue(report["assignments"]["supplied_cells_accounted_for"])
        self.assertFalse(report["correspondence"]["intended_domain_fully_represented"])
        self.assertEqual(report["correspondence"]["missing_cell_ids"], ["cell-lower"])
        self.assertIn("body-0", report["correspondence"]["incomplete_component_ids"])
        self.assertIn("missing_expected_cells", report["reason_codes"])

    def test_removed_component_is_detected_by_expected_manifest(self):
        manifest, partition = two_component_fixture()
        partition["cells"] = [row for row in partition["cells"] if row["cell_id"] == "cell-a"]
        partition["vertices"] = [row for row in partition["vertices"]
                                 if row["vertex_id"].startswith("a")]
        report = admission.build_admission_report(manifest, partition)
        self.assertTrue(report["geometry"]["topology_valid"])
        self.assertEqual(report["decision"], "not_admitted")
        self.assertEqual(report["correspondence"]["removed_component_ids"], ["component-b"])
        self.assertEqual(report["correspondence"]["missing_cell_ids"], ["cell-b"])
        self.assertTrue(report["assignments"]["supplied_cells_accounted_for"])
        self.assertFalse(report["anatomical_completeness_certified"])

    def test_duplicate_ownership_is_not_admitted(self):
        manifest, partition = examples()
        for document in (manifest, partition):
            document["regions"][1]["mass_owner_id"] = document["regions"][0]["mass_owner_id"]
        manifest["matter_ownership"][1]["mass_owner_id"] = "owner-A"
        report = admission.build_admission_report(manifest, partition)
        self.assertNotEqual(report["decision"], "validation_only_admissible")
        self.assertIn("duplicate_mass_owner_id", report["reason_codes"])
        self.assertIn("duplicate_mass_owner_claim_ids", report["ownership"])
        self.assertEqual(report["compiler_refusal"]["reason"],
                         mv.CompilerReason.DUPLICATE_MASS_OWNER_ID)

    def test_missing_density_preserves_cell_assignment_without_total_mass(self):
        manifest, partition = examples()
        lower_material = next(row for row in partition["materials"]
                              if row["material_id"] == "lower-tissue")
        lower_material["density_kg_m3"] = None
        lower_material["density_source"] = None
        lower_material["conditions"] = None
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "not_admitted")
        self.assertTrue(report["correspondence"]["intended_domain_fully_represented"])
        self.assertEqual(report["assignments"]["missing_density_cell_ids"], ["cell-lower"])
        self.assertEqual(report["cells"][0]["status"], "missing_density")
        self.assertIsNone(report["mass_authority"]["reconstructed_mass_properties"])
        self.assertIn("missing_density", report["reason_codes"])

    def test_unresolved_and_conflicted_proposals_are_retained(self):
        manifest, partition = examples()
        partition["cells"][0]["proposals"] = []
        partition["cells"][1]["proposals"] = ["region-A", "region-B"]
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "not_admitted")
        statuses = {row["cell_id"]: row["status"] for row in report["cells"]}
        self.assertEqual(statuses["cell-upper"], "unresolved")
        self.assertEqual(statuses["cell-lower"], "conflict")
        self.assertEqual(report["assignments"]["unresolved_cell_ids"], ["cell-upper"])
        self.assertEqual(report["assignments"]["conflicted_cell_ids"], ["cell-lower"])
        self.assertTrue(report["assignments"]["supplied_cells_accounted_for"])
        self.assertIsNone(report["mass_authority"]["reconstructed_mass_properties"])

    def test_surface_overlay_cannot_double_own_volumetric_membrane(self):
        manifest, partition = examples()
        manifest["matter_ownership"].append({
            "matter_id": "upper-tissue-matter", "representation": "surface_mass_overlay",
            "mass_owner_id": "surface-owner"})
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "not_admitted")
        self.assertIn("upper-tissue-matter",
                      report["ownership"]["volume_surface_ownership_collisions"])
        self.assertIn("volume_surface_ownership_collision", report["reason_codes"])
        self.assertIsNone(report["mass_authority"]["reconstructed_mass_properties"])

    def test_source_effective_authority_never_emits_reconstructed_mass(self):
        manifest, partition = examples()
        manifest["mass_authority"] = admission.AUTHORITY_EFFECTIVE_SEGMENT
        partition["mass_authority"] = admission.AUTHORITY_EFFECTIVE_SEGMENT
        manifest["source_effective_segment_ids"] = ["source-segment-1"]
        manifest["matter_ownership"] = [{"matter_id": "source-segment-1-matter",
            "representation": "source_effective_segment",
            "mass_owner_id": "source-segment-1"}]
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "validation_only_admissible")
        self.assertEqual(report["mass_authority"]["choice"],
                         admission.AUTHORITY_EFFECTIVE_SEGMENT)
        self.assertFalse(report["mass_authority"]["source_segment_payloads_consumed"])
        self.assertIsNone(report["mass_authority"]["reconstructed_mass_properties"])
        self.assertFalse(report["mass_authority"]["reconstructed_mass_properties_emitted"])

    def test_source_effective_authority_does_not_consume_or_require_density(self):
        manifest, partition = examples()
        manifest["mass_authority"] = admission.AUTHORITY_EFFECTIVE_SEGMENT
        partition["mass_authority"] = admission.AUTHORITY_EFFECTIVE_SEGMENT
        manifest["source_effective_segment_ids"] = ["source-segment-1"]
        manifest["matter_ownership"] = [{"matter_id": "source-segment-1-matter",
            "representation": "source_effective_segment",
            "mass_owner_id": "source-segment-1"}]
        for material in partition["materials"]:
            material["density_kg_m3"] = None
            material["density_source"] = None
            material["conditions"] = None
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "validation_only_admissible")
        self.assertEqual(report["assignments"]["missing_density_cell_ids"],
                         ["cell-lower", "cell-upper"])
        self.assertTrue(report["assignments"]["supplied_cells_accounted_for"])
        self.assertIn("missing_density_not_used_by_source_effective_authority",
                      report["warning_codes"])
        self.assertIsNone(report["mass_authority"]["reconstructed_mass_properties"])

    def test_manifest_requires_one_mass_authority_and_rejects_mixed_claims(self):
        manifest, partition = examples()
        del manifest["mass_authority"]
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "refused")
        self.assertIn("bad_schema", report["reason_codes"])
        manifest, partition = examples()
        manifest["source_effective_segment_ids"] = ["legacy-segment"]
        report = admission.build_admission_report(manifest, partition)
        self.assertEqual(report["decision"], "refused")
        self.assertIn("mixed_mass_authority", report["reason_codes"])

    def test_schema_and_examples_are_valid_json_with_both_schema_variants(self):
        schema = json.loads((ROOT / "material_volume_admission_schema.json")
                            .read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(len(schema["oneOf"]), 2)
        manifest, partition = examples()
        self.assertEqual(admission.build_admission_report(manifest, partition)["decision"],
                         "validation_only_admissible")
        self.assertEqual(manifest["schema_version"], admission.MANIFEST_SCHEMA)
        self.assertEqual(partition["schema_version"], admission.PARTITION_SCHEMA)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MaterialVolumeAdmissionChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
