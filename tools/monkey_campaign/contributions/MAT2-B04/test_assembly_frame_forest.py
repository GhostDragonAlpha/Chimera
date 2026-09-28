"""MAT2-B04 tests: authored roots, C01 checks, separation, refusals, packets."""
from __future__ import annotations

import copy
import json
import math
import pathlib
import unittest

import assembly_frame_forest as aff

HERE = pathlib.Path(__file__).resolve().parent
LIVE_CHIMANOID = pathlib.Path(r"E:\PythonChimera\.tmp\chimanoid.xml")
LIVE_PACKET = pathlib.Path(r"E:\PythonChimera\.tmp\anatomy_compiler\runs\actual_monkey_fit.json")
LIVE_OSIM = pathlib.Path(r"E:\PythonChimera") / aff.OSIM_PATH


class AuthoredRoots(unittest.TestCase):
    def setUp(self):
        self.doc = aff.build_document()
        self.receipt = aff.validate_document(self.doc)

    def test_document_validates(self):
        self.assertEqual(self.receipt["status"], "PASS")
        self.assertEqual(self.receipt["authored_root_frames"],
                         ["root_pelvis", "root_thorax", "root_ulna", "root_ulna_l"])
        self.assertEqual(self.receipt["components"], 4)

    def test_predicted_transforms_exact(self):
        expected = {
            "root_pelvis": [0.0, 0.73, 6.12323e-17],
            "root_thorax": [-0.08, 1.19, 6.12323e-17],
            "root_ulna": [-0.0915, 0.83455, 0.1577],
            "root_ulna_l": [-0.0915, 0.8345, -0.1577],
        }
        for key, want in expected.items():
            got = self.doc["frames"][key]["origin_m"]
            for g, w in zip(got, want):
                self.assertLessEqual(abs(g - w), 1e-15, key)
            rows = self.doc["frames"][key]["basis_rows"]
            self.assertEqual(rows, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], key)

    def test_every_root_pins_its_full_chain(self):
        for key, chain in aff.ROOT_CHAINS.items():
            frame = self.doc["frames"]["root_" + key]
            self.assertEqual(tuple(h["body"] for h in frame["chain"]), chain)
            for hop in frame["chain"]:
                self.assertEqual(hop["sha256"], aff.CHIMANOID_SHA256)
                self.assertTrue(hop["line"] > 0)
                self.assertIn("body[@pos,@quat]", hop["field"])

    def test_roots_reconcile_packet(self):
        declared = {row[0] for row in aff.SEGMENTS}
        referenced = {row[1] for row in aff.SEGMENTS}
        self.assertEqual(referenced - declared, {"pelvis", "thorax", "ulna", "ulna_l"})
        for root in referenced - declared:
            self.assertTrue(self.doc["frames"]["root_" + root]["component_root"])

    def test_live_source_pins_resolve(self):
        if not LIVE_CHIMANOID.exists():
            self.skipTest("chimanoid.xml not present on this host")
        checks = aff.verify_live_source(
            str(LIVE_CHIMANOID),
            str(LIVE_PACKET) if LIVE_PACKET.exists() else None,
            str(LIVE_OSIM) if LIVE_OSIM.exists() else None)
        self.assertEqual(checks["chimanoid_sha256"], aff.CHIMANOID_SHA256)
        if "packet_sha256" in checks:
            self.assertEqual(checks["packet_sha256"], aff.PACKET_SHA256)
        if "osim_sha256" in checks:
            self.assertEqual(checks["osim_sha256"], aff.OSIM_SHA256)


class C01Checks(unittest.TestCase):
    def setUp(self):
        self.doc = aff.build_document()

    def test_round_trip_handedness_orthonormal(self):
        results = aff.c01_checks(self.doc)
        for key, row in results.items():
            self.assertGreater(row["determinant"], 1.0 - 1e-12, key)
            self.assertLessEqual(row["round_trip_max_error"], 1e-12, key)
            self.assertLessEqual(row["orthonormality_max_error"], 1e-12, key)

    def test_invert_compose_identity(self):
        for key in ("root_pelvis", "root_thorax", "root_ulna", "root_ulna_l"):
            frame = self.doc["frames"][key]
            t = frame["origin_m"]
            r = [list(row) for row in frame["basis_rows"]]
            t_inv, r_inv = aff.invert_transform(t, r)
            t_back, r_back = aff.compose_transform(t, r, t_inv, r_inv)
            for i in range(3):
                self.assertAlmostEqual(t_back[i], 0.0, places=12, msg=key)
                for j in range(3):
                    self.assertAlmostEqual(r_back[i][j], 1.0 if i == j else 0.0,
                                           places=12, msg=key)


class SeparationOfContainmentAndBonds(unittest.TestCase):
    def setUp(self):
        self.doc = aff.build_document()

    def test_relation_lists_disjoint(self):
        edges = {e["child_frame_id"] for e in self.doc["containment_edges"]}
        bonds = {b["bond_id"] for b in self.doc["bonds"]}
        self.assertFalse(edges & bonds)

    def test_mutation_does_not_cross(self):
        self.assertTrue(aff.separation_check(self.doc)["bonds_unchanged_without_containment"])
        self.assertTrue(aff.separation_check(self.doc)["containment_unchanged_without_bonds"])

    def test_four_components_disconnected(self):
        components = self.doc["components"]
        self.assertEqual(len(components), 4)
        seen = []
        for component in components:
            self.assertTrue(component["disconnected_from_other_components"])
            seen.extend(component["bodies"])
        self.assertEqual(len(seen), len(set(seen)))

    def test_no_declared_bond_crosses_components(self):
        body_component = {}
        for component in self.doc["components"]:
            for body in component["bodies"]:
                body_component[body] = component["component_id"]
        for bond in self.doc["bonds"]:
            body, parent = bond["body"], bond["parent_body_declared"]
            if body in body_component and parent in body_component:
                self.assertEqual(body_component[body], body_component[parent], bond["bond_id"])

    def test_unresolved_roots_keep_admission_status(self):
        unresolved = {row["body"]: row for row in self.doc["unresolved_bodies"]}
        for body in ("thorax", "ulna", "ulna_l", "hand_r", "hand_l", "talus_r", "talus_l"):
            self.assertEqual(unresolved[body]["admission_status"], "unresolved", body)
            self.assertEqual(unresolved[body]["geometry_mass_status"],
                             "unresolved (unchanged from admission ledger)")
        self.assertEqual(self.doc["matter_boundary"]["counted_mass_kg"], 0.0)


class RefusalsBite(unittest.TestCase):
    def setUp(self):
        self.doc = aff.build_document()

    def expect_refusal(self, mutate, code):
        broken = copy.deepcopy(self.doc)
        mutate(broken)
        with self.assertRaisesRegex(ValueError, code):
            aff.validate_document(broken)

    def test_tuned_digit_refused(self):
        def mutate(doc):
            doc["frames"]["root_ulna"]["origin_m"][1] += 0.01
        self.expect_refusal(mutate, "root_transform_not_source_composed:root_ulna")

    def test_swapped_basis_refused(self):
        def mutate(doc):
            doc["frames"]["root_pelvis"]["basis_rows"] = [
                [1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]
        self.expect_refusal(mutate, "frame_basis_not_proper:root_pelvis")

    def test_left_handed_unit_refused(self):
        def mutate(doc):
            doc["frames"]["root_thorax"]["handedness"] = "left"
        self.expect_refusal(mutate, "frame_handedness_invalid:root_thorax")

    def test_dropped_root_refused(self):
        def mutate(doc):
            del doc["frames"]["root_ulna_l"]
        self.expect_refusal(mutate, "authored_roots_missing")

    def test_bond_status_promotion_refused(self):
        def mutate(doc):
            doc["bonds"][26]["status"] = "qualified"
        self.expect_refusal(mutate, "bond_status_not_carried_verbatim")

    def test_identity_overlap_refused(self):
        def mutate(doc):
            doc["bonds"][0]["bond_id"] = doc["containment_edges"][0]["child_frame_id"]
        self.expect_refusal(mutate, "containment_bond_identity_overlap")

    def test_mass_counting_refused(self):
        def mutate(doc):
            doc["matter_boundary"]["counted_mass_kg"] = 17.04
        self.expect_refusal(mutate, "mass_counted_by_frame_document")

    def test_component_disconnect_claim_refused(self):
        def mutate(doc):
            doc["components"][2]["disconnected_from_other_components"] = False
        self.expect_refusal(mutate, "component_connectivity_asserted")

    def test_cross_component_bond_refused(self):
        def mutate(doc):
            doc["bonds"].append({"bond_id": "bond_author_bridge", "joint": "author_bridge",
                                 "body": "radius", "joint_type": "hinge",
                                 "status": "kinematically_preserved",
                                 "parent_body_declared": "humerus",
                                 "kind": "mechanical_bond"})
        self.expect_refusal(mutate, "bond_crosses_components:bond_author_bridge")


class SemanticPackets(unittest.TestCase):
    def setUp(self):
        self.packets = aff.semantic_packets()

    def test_both_ulna_packets_authored(self):
        self.assertEqual(sorted(self.packets), ["ulna_l", "ulna_r"])
        for tag, packet in self.packets.items():
            self.assertEqual(packet["schema"], "chimera.semantic_spatial_frame.v1")
            self.assertEqual(packet["source_head"], aff.SOURCE_HEAD)
            self.assertEqual(len(packet["landmarks"]), 3)
            self.assertEqual(len(packet["knowledge_claims"]), 5)

    def test_kinematic_witness_recomputed_independently(self):
        for tag, packet in self.packets.items():
            witness = packet["kinematic_witness"]
            origin = witness["reference_origin"]
            palm = packet["semantic_directions"]["palm"]
            progress = sum(
                sum((m[i] - origin[i]) * palm[i] for i in range(3))
                - sum((r[i] - origin[i]) * palm[i] for i in range(3))
                for r, m in zip(witness["rest_points"], witness["moved_points"])
            ) / len(witness["rest_points"])
            self.assertGreaterEqual(progress, witness["minimum_signed_progress"], tag)

    def test_emitted_packets_match_and_validator_passes(self):
        r_path = HERE / "semantic_frame_ulna_r.json"
        l_path = HERE / "semantic_frame_ulna_l.json"
        if not (r_path.exists() and l_path.exists()):
            self.skipTest("packets not emitted yet")
        self.assertEqual(json.loads(r_path.read_text(encoding="utf-8")),
                         self.packets["ulna_r"])
        self.assertEqual(json.loads(l_path.read_text(encoding="utf-8")),
                         self.packets["ulna_l"])


class EmittedDocument(unittest.TestCase):
    def test_emitted_document_matches_module_and_validates(self):
        path = HERE / "frame_forest.json"
        if not path.exists():
            self.skipTest("document not emitted yet")
        loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded, aff.build_document())
        self.assertEqual(aff.validate_document(loaded)["status"], "PASS")
        self.assertEqual(aff.digest(loaded), aff.digest(aff.build_document()))


if __name__ == "__main__":
    unittest.main()
