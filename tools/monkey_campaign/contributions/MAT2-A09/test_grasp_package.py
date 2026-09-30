"""MAT2-A09 named checks (executable done_when; house G1/G8, prereg P1-P12).

Run: python -B test_grasp_package.py
The suite asserts only frozen attempt-state values; it never asserts mutable
live registry state (F03 F-1 lesson): the criteria sha and profile id/kind it
checks against are the preregistered constants, and capture-time evidence
files carry the registry snapshot under evidence/.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import grasp_package as gp  # noqa: E402

DOC_PATH = HERE / "grasp_package.json"
MANIFEST_PATH = HERE / "evidence" / "capture_manifest.json"
CONTEXT_PATH = HERE / "evidence" / "capture_context.json"
VRECEIPT_PATH = HERE / "evidence" / "validation_receipt.json"
FALSIFIERS_PATH = HERE / "evidence" / "falsifier_receipt.json"
PNG_PATH = HERE / "capture" / "capture_mat2_a09_package_20260930.png"


def sha256_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


class P1Pins(unittest.TestCase):
    def test_all_pins_verify_live(self):
        P = gp.load_pins()  # refuses input_pin_drift on any mismatch
        self.assertEqual(len(P), len(gp.PINS))
        self.assertEqual(len(gp.PINS), 14)  # 12 repo + 2 host (Amendment A1)


class P2Conservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))

    def test_frozen_counts(self):
        for k, v in gp.FROZEN.items():
            self.assertEqual(self.doc["counts"][k], v, k)

    def test_roles_and_owners(self):
        roles = {}
        owners = {}
        for c in self.doc["interface_graph"]["connections"]:
            if c["kind"] == "tendon_path_record":
                roles[c["role"]] = roles.get(c["role"], 0) + 1
                owners[c["owner_body"]] = owners.get(c["owner_body"], 0) + 1
        self.assertEqual(roles["origin_attachment"], 13)
        self.assertEqual(roles["insertion_attachment"], 13)
        self.assertEqual(roles["path_waypoint"], 21)
        self.assertEqual(roles["conditional_waypoint"], 1)
        self.assertEqual(owners["osim.body.radius"], 18)
        self.assertEqual(owners["osim.body.hand"], 17)
        self.assertEqual(owners["osim.body.humerus"], 8)
        self.assertEqual(owners["osim.body.ulna"], 5)


class P3ProvenanceTotality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))

    def test_every_row_has_sealed_class(self):
        for n in self.doc["tissue_graph"]["nodes"]:
            self.assertIn(n["provenance_class"], gp.PROVENANCE_CLASSES)
        for r in self.doc["engineering_carriers"]["rows_carried"]:
            self.assertEqual(r["provenance"], "chosen_engineering")
            self.assertTrue(r["never_biological"])


class P4ParameterCarriage(unittest.TestCase):
    def test_document_validates_field_for_field(self):
        P = gp.load_pins()
        doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
        gp.validate_document(doc, P)  # refuses parameter_carriage_mismatch

    def test_known_placeholder_row_carried_verbatim(self):
        doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
        rows = {n["osim_muscle"]: n["parameter_row"]
                for n in doc["tissue_graph"]["nodes"]}
        fcu = rows["flex_carpi_ulnaris"]
        # Sealed A08 amended P3: the fiber-ceiling constant 0.122492 m is
        # carried AS the tendon_slack_length while the muscle's own
        # optimal_fiber_length differs (0.044632 m) - the documented slot
        # swap no measurement would produce; carried verbatim, never repaired.
        self.assertEqual(fcu["l0t_m"], 0.122492)
        self.assertEqual(fcu["l0m_m"], 0.044632)
        self.assertFalse(fcu["fingerprints"]["tsl_placeholder"])
        self.assertFalse(fcu["fingerprints"]["ofl_placeholder"])


class P5PlacementCarriage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
        cls.P = gp.load_pins()

    def test_outside_census_matches_frozen(self):
        outside = [c for c in self.doc["interface_graph"]["connections"]
                   if c["kind"] == "tendon_path_record"
                   and c["terminal_resolution"].get("placement_failed_outside")]
        self.assertEqual(len(outside),
                         self.doc["counts"]["a07_envelope_measured_outside"])
        self.assertEqual(len(outside), 8)
        for c in outside:
            axes = c["terminal_resolution"]["envelope_measurement"]["outside_axes"]
            self.assertTrue(axes)
            self.assertTrue(all(a["axis"] == "z" for a in axes))

    def test_attachment_join_keys_carried(self):
        for c in self.doc["interface_graph"]["connections"]:
            if c["kind"] == "attachment_interface":
                self.assertTrue(c.get("path_record_id"))


class P6OwnerFrameClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))

    def test_endpoints_in_mutation_frame(self):
        for e in self.doc["interface_graph"]["grasp_endpoints"]:
            self.assertEqual(e["frame_decl"], gp.MUTATION_FRAME)

    def test_no_dangling_full_package(self):
        self.assertTrue(gp.check_no_dangling(self.doc))


class P7RemovalClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))

    def test_degree_conservation(self):
        rc = self.doc["removal_closure"]
        deg = sum(d["path_records"] + d["attachment_interfaces"]
                  for d in rc["per_muscle"].values())
        self.assertEqual(deg, rc["connections_total"])
        self.assertEqual(rc["connections_total"], 74)
        self.assertEqual(len(rc["per_muscle"]), 13)

    def test_every_muscle_reduces_without_dangling(self):
        for m in gp.GRASP_MUSCLES:
            red = gp.reduced_package(self.doc, m)
            self.assertTrue(gp.check_no_dangling(red), m)
            before = len(self.doc["interface_graph"]["connections"])
            after = len(red["interface_graph"]["connections"])
            d = self.doc["removal_closure"]["per_muscle"][m]
            self.assertEqual(before - after,
                             d["path_records"] + d["attachment_interfaces"], m)

    def test_tampered_reduction_refused(self):
        red = gp.reduced_package(self.doc, "abd_poll_longus")
        keep = [c for c in self.doc["interface_graph"]["connections"]
                if c["muscle_node"] == "muscle.abd_poll_longus"][0]
        red["interface_graph"]["connections"].append(copy.deepcopy(keep))
        with self.assertRaises(gp.Refusal) as cm:
            gp.check_no_dangling(red)
        self.assertTrue(str(cm.exception).startswith(
            "dangling_connection_after_removal"))


class P8ReductionLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))

    def test_seven_reductions_with_removal_semantics(self):
        reds = self.doc["explicit_reductions"]
        self.assertEqual(len(reds), 7)
        for r in reds:
            self.assertTrue(r["removal_semantics"], r["id"])
            self.assertTrue(r["sealed_source"], r["id"])
        self.assertEqual([r["id"] for r in reds],
                         ["RED-1", "RED-2", "RED-3", "RED-4", "RED-5",
                          "RED-6", "RED-7"])

    def test_red3_carries_measured_release(self):
        red3 = self.doc["explicit_reductions"][2]
        self.assertTrue(red3["carried"]["t4_bitwise_zero_after_release"])
        self.assertEqual(red3["carried"]["t4_released_doc_bond_count"], 0)


class P9Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
        cls.P = gp.load_pins()

    def test_five_contracts_match_pinned_catalog(self):
        self.assertEqual(len(self.doc["calculation_contracts"]), 5)
        gp.validate_document(self.doc, self.P)  # refuses on any catalog drift

    def test_c17_block_carried_open(self):
        c17 = self.doc["interface_graph"]["c17_block"]
        self.assertEqual(c17["status"], "open")
        self.assertIn("patch area/shape", c17["required_inputs"])


class P10NoFitting(unittest.TestCase):
    def test_whole_document_scan(self):
        doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
        gp.scan_fitting(doc)  # raises fitting_unauthorized_refused on any hit

    def test_injected_fit_refused(self):
        doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
        doc["interface_graph"]["connections"][0]["fitted_origin_m"] = [0, 0, 0]
        with self.assertRaises(gp.Refusal) as cm:
            gp.scan_fitting(doc)
        self.assertTrue(str(cm.exception).startswith(
            "fitting_unauthorized_refused"))


class P11Determinism(unittest.TestCase):
    def test_two_full_builds_byte_identical(self):
        b1 = gp.canonical_bytes(gp.build_document())
        b2 = gp.canonical_bytes(gp.build_document())
        self.assertEqual(hashlib.sha256(b1).hexdigest(),
                         hashlib.sha256(b2).hexdigest())

    def test_committed_document_equals_rebuild(self):
        committed = sha256_file(DOC_PATH)
        rebuilt = hashlib.sha256(
            gp.canonical_bytes(gp.build_document())).hexdigest()
        self.assertEqual(committed, rebuilt)


class P12Capture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
        cls.doc_sha = sha256_file(DOC_PATH)
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.context = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
        cls.vreceipt = json.loads(VRECEIPT_PATH.read_text(encoding="utf-8"))

    def test_single_gate_bound_identity(self):
        disk = sha256_file(PNG_PATH)
        self.assertEqual(disk, self.manifest["capture_sha256"])
        self.assertEqual(disk, self.context["capture_sha256"])
        self.assertEqual(self.manifest["subject_sha256"], self.doc_sha)

    def test_view_toggles_preserve_state_hash(self):
        hashes = {v["state_binding"]["sha256"] for v in self.manifest["views"]}
        self.assertEqual(hashes, {self.doc_sha})

    def test_structurally_valid_with_short_task_id(self):
        self.assertTrue(self.vreceipt["structurally_valid"])
        self.assertEqual(self.manifest["task_id"], "A09")
        self.assertEqual(self.manifest["profile_id"], "anatomy")
        self.assertEqual(self.vreceipt["validated_profile_kind"],
                         "visible_static")

    def test_clean_rows_carry_no_diagnostics(self):
        for v in self.manifest["views"]:
            if v["mode"] == "clean":
                self.assertEqual(v["visibility"]["layers"], [])
                self.assertEqual(v["visibility"]["label_ids"], [])
                self.assertEqual(v["visibility"]["tag_bindings"], [])
                self.assertEqual(v["visibility"]["occlusion_mode"],
                                 "depth_tested")

    def test_every_view_id_has_diag_and_clean_pair(self):
        vids = {v["view_id"] for v in self.manifest["views"]}
        self.assertEqual(len(vids), 3)
        for vid in vids:
            modes = [v["mode"] for v in self.manifest["views"]
                     if v["view_id"] == vid]
            self.assertEqual(sorted(modes), ["clean", "diagnostic"])

    def test_numerical_evidence_carried(self):
        ne = self.manifest["numerical_evidence"]
        self.assertEqual(ne["outside_count"], 8)
        self.assertEqual(len(ne["records"]), 8)
        self.assertEqual(ne["document_sha256"], self.doc_sha)

    def test_falsifier_receipt_green(self):
        fals = json.loads(FALSIFIERS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(fals["schema"], "chimera.a09_falsifiers.v1")
        self.assertTrue(fals["F_all_green"])
        self.assertEqual(len(fals["arms"]), 7)
        for name, row in fals["arms"].items():
            self.assertTrue(row["bit"], name)
            self.assertTrue(row["clean_control"]["within_tolerance"], name)
            self.assertIn("_premature", row["clean_control"]["guard"], name)

    def test_fb8a_label_binding_guard(self):
        with self.assertRaises(ValueError) as cm:
            gp_capture_assert_binding({"label_id": "", "subject_id": ""})
        self.assertIn("label_ambiguity_refused", str(cm.exception))

    def test_fb8b_state_hash_guard(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["views"][0]["state_binding"]["sha256"] = "0" * 64
        import capture_package as cp
        with self.assertRaises(ValueError) as cm:
            cp.assert_uniform_state_hash(manifest)
        self.assertIn("view_toggle_state_hash_refused", str(cm.exception))


def gp_capture_assert_binding(binding):
    from capture_package import require_binding
    return require_binding("x", binding)


if __name__ == "__main__":
    unittest.main()
