"""test_implementation.py -- focused suite for MAT2-F03 (attempt 865039032f81).

Runs against the pinned bytes and the frozen bars in PREREGISTRATION.md
(incl. Amendment A1). CPU-only, stdlib-only, no engine, no GPU. The full
evidence build is `python -B implementation.py build`; this suite re-checks
the frozen predicates independently and refuses drift.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import implementation as impl  # noqa: E402


def setUpModule():
    global PINS, RECIPE, DECLARATION, SURFACE, TRUNK, MS, LC, PL, VC, WOOD, GEOM
    PINS = impl.materialize_pins()
    (RECIPE, DECLARATION, SURFACE, TRUNK,
     MS, LC, PL, VC) = impl.load_sources(PINS)
    WOOD = impl.extract_wood_provenance(PINS)
    GEOM = impl.trunk_partition(TRUNK)


class TestPins(unittest.TestCase):
    def test_t01_all_pins_raw_match(self):
        for key, pin in PINS.items():
            raw = pathlib.Path(pin["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), pin["sha256"],
                             "pin drift: %s" % key)
            self.assertTrue(pin["raw_match"])

    def test_t02_trunk_asset_identity(self):
        self.assertEqual(TRUNK["schema"], "chimera.trunk_asset.v1")
        self.assertEqual(TRUNK["object_id"], "trunk_01")
        self.assertTrue(TRUNK["collision_representation"]["exact"])
        self.assertEqual(TRUNK["collision_representation"]["solid"]
                         ["radius_m"], 0.037)
        self.assertEqual(TRUNK["geometry"]["height_m"], 1.158)
        self.assertEqual([s["id"] for s in TRUNK["surface_ids"]],
                         list(impl.TRUNK_SURFACE_IDS))


class TestGeometry(unittest.TestCase):
    def test_t03_partition_and_closure(self):
        self.assertEqual(GEOM["counts"], {"trunk_01.lateral": 64,
                                          "trunk_01.base_cap": 32,
                                          "trunk_01.top_cap": 32})
        self.assertEqual(GEOM["raw_open_edge_count"], 128)
        self.assertEqual(GEOM["welded_open_edge_count"], 0)
        self.assertEqual(GEOM["distinct_position_count"], 66)
        self.assertEqual(GEOM["seam_weld_max_distance_m"], 0.0)
        self.assertGreater(GEOM["welded_volume_m3"], 0.0)

    def test_t04_volume_ratio_prediction(self):
        ratio = GEOM["mesh_over_analytic_ratio"]
        self.assertGreaterEqual(ratio, 0.99355)
        self.assertLessEqual(ratio, 0.99362)
        self.assertLess(abs(ratio - 0.99358685114420575) /
                        0.99358685114420575, 1e-5)
        self.assertLessEqual(GEOM["volume_ordering_relative_gap"], 1e-12)

    def test_t05_correspondence_bars(self):
        corr = impl.measure_correspondence(TRUNK, GEOM)
        self.assertLessEqual(corr["max_lateral_vertex_radial_gap_m"],
                             impl.VOLUME_TOL)
        self.assertLessEqual(corr["max_vertex_outside_solid_m"],
                             impl.VOLUME_TOL)


class TestProvenanceAndMass(unittest.TestCase):
    def test_t06_wood_provenance_frozen_numbers(self):
        self.assertEqual(WOOD["density_kg_m3"], 760.0)
        self.assertEqual(WOOD["band_kg_m3"], [650.0, 850.0])
        self.assertEqual(WOOD["source_raw_sha256"],
                         impl.PINS["wood_source_md"]["sha256"])
        library = json.loads(PINS["matter_library_json"]["bytes"])
        self.assertNotIn("wood", library["materials"])
        self.assertEqual(library["provenance_classes"]["researched"],
                         "cited external measurement with a cached source on "
                         "disk")

    def test_t07_mass_band_and_owner(self):
        mass = impl.RHO_KG_M3 * GEOM["analytic_solid_volume_m3"]
        lo = impl.RHO_BAND[0] * GEOM["analytic_solid_volume_m3"]
        hi = impl.RHO_BAND[1] * GEOM["analytic_solid_volume_m3"]
        self.assertGreaterEqual(mass, lo)
        self.assertLessEqual(mass, hi)
        self.assertAlmostEqual(mass, 3.7850835688601157, delta=1e-9)
        doc, mass2 = impl.build_material_doc(TRUNK, GEOM, WOOD, PINS, MS)
        self.assertEqual(mass2, mass)
        owners = [c["matter_id"] for r in doc["regions"]
                  for c in r["matter_claims"] if c["role"] == "owner"]
        self.assertEqual(owners, ["wood_trunk_01"])


class TestMaterialDocuments(unittest.TestCase):
    def test_t08_material_state_validates_m01(self):
        doc, _ = impl.build_material_doc(TRUNK, GEOM, WOOD, PINS, MS)
        blob = {"schema": "chimera.mat2_f03.mesh_blob.v1",
                "vertices": GEOM["vertices"]}
        doc = json.loads(json.dumps(doc))
        doc["regions"][0]["rest_geometry"]["mesh_blob_sha256"] = \
            hashlib.sha256(impl.canonical(blob)).hexdigest()
        doc["regions"][0]["rest_geometry"]["collision_representation"][
            "measured_correspondence"]["max_lateral_vertex_radial_gap_m"] = 0.0
        summary = MS.validate_material_state(doc)
        self.assertEqual(summary["region_count"], 1)
        self.assertEqual(summary["matter_count"], 1)
        self.assertEqual(summary["owner_count"], 1)
        self.assertEqual(summary["bond_count"], 0)
        self.assertEqual(summary["port_count"], 1)

    def test_t09_rigid_law_validates_m04(self):
        doc, _ = impl.build_material_doc(TRUNK, GEOM, WOOD, PINS, MS)
        doc["regions"][0]["rest_geometry"]["mesh_blob_sha256"] = "0" * 64
        doc["regions"][0]["rest_geometry"]["collision_representation"][
            "measured_correspondence"]["max_lateral_vertex_radial_gap_m"] = 0.0
        MS.validate_material_state(doc)
        rigid = impl.build_rigid_doc(
            PINS, hashlib.sha256(impl.canonical(doc)).hexdigest())
        out = PL.validate_passive_law(rigid)
        self.assertTrue(out)


class TestM06ContactBinding(unittest.TestCase):
    def test_t10_surface_id_flow_and_predicates(self):
        experiments = impl.run_contact_experiments(LC, GEOM)
        s1 = experiments["S1_grip_stick"]
        self.assertEqual(s1["surface_b"], "trunk_01.lateral")
        self.assertEqual(s1["mode"], "stick")
        self.assertAlmostEqual(s1["jn_Ns"], 0.30, delta=1e-9)
        self.assertLessEqual(s1["vt_post_mps"], 1e-12)
        self.assertAlmostEqual(s1["grip_capacity_kg"], 3.6697247706422016,
                               delta=1e-9)
        s2 = experiments["S2_counterfactual_slip"]
        self.assertEqual(s2["mode"], "slip")
        self.assertGreater(s2["vt_post_mps"], 0.0)
        s3 = experiments["S3_cap_rest"]
        self.assertEqual(s3["surface_b"], "trunk_01.top_cap")
        self.assertLessEqual(s3["max_displacement_m"], s3["bar_m"])

    def test_t11_bad_friction_refused(self):
        bite = impl.bite_bad_friction(LC, GEOM)
        self.assertEqual(bite["code"], "bad_friction")


class TestRegistryAndBites(unittest.TestCase):
    def test_t12_registry_profile_and_criteria(self):
        profile, receipt = impl.read_registry_profile()
        self.assertEqual(profile["id"], "forest")
        self.assertEqual(profile["kind"], "visible_static")
        self.assertEqual(receipt["canonical_sha256"],
                         impl.PROFILE_CANONICAL_SHA256)
        # attempt_state is mutable live-workspace lifecycle state (WORKING
        # advances to WON at acceptance), so its VALUE is out of scope for
        # this frozen suite (REGRESSION_MATRIX RED #2; the #240 docs-sync
        # lesson, registry edition). The read-only receipt must still
        # surface a non-empty state; the immutable pins above (profile
        # id/kind, canonical_sha256; impl also require()s criteria_sha256
        # and the attempt id) remain the frozen predicates.
        self.assertIsInstance(receipt["attempt_state"], str)
        self.assertTrue(receipt["attempt_state"])

    def test_t13_bites_bite(self):
        corr = impl.measure_correspondence(TRUNK, GEOM)
        views = {name: impl.Camera(spec)
                 for name, spec in impl.VIEW_SPECS.items()}
        base = GEOM["base_centre_m"]
        vs6 = [impl.to_m06_frame(p, base) for p in GEOM["vertices"]]
        cen, n = impl._facet_frame(vs6, GEOM["groups"]["trunk_01.lateral"])
        u, v = impl._orthobasis(n)
        tetra06 = impl._place_tetra(impl.vadd(cen, impl.vscale(n, 2e-5)),
                                    n, u, v)
        impl.FROZEN_GRIP_MARKER["f01"] = impl.from_m06_frame(tetra06[0], base)
        marker_tris = [(impl.from_m06_frame(tetra06[impl.TETRA_TRIS[k][0]],
                                            base),
                        impl.from_m06_frame(tetra06[impl.TETRA_TRIS[k][1]],
                                            base),
                        impl.from_m06_frame(tetra06[impl.TETRA_TRIS[k][2]],
                                            base),
                        "climb_grip_probe") for k in range(4)]
        mesh = impl.SceneMesh(SURFACE, TRUNK, GEOM, marker_tris)
        probes = impl.frozen_probes(SURFACE, TRUNK, GEOM,
                                    impl.FROZEN_GRIP_MARKER["f01"])
        self.assertEqual(len(probes), 47)
        experiments = impl.run_contact_experiments(LC, GEOM)
        bites = [impl.bite_ghost_support(TRUNK, GEOM, corr)["bite"],
                 impl.bite_provenance_fabrication(PINS, MS)["bite"],
                 impl.bite_missing_boundary(TRUNK, GEOM)["bite"],
                 impl.bite_off_frame(views, probes, mesh)["bite"],
                 impl.bite_bad_friction(LC, GEOM)["bite"],
                 impl.bite_ledger_tamper(LC, GEOM)["bite"],
                 impl.bite_understated_mu(experiments)["bite"]]
        self.assertEqual(len(bites), 7)
        self.assertEqual(len(set(bites)), 7)


if __name__ == "__main__":
    unittest.main()
