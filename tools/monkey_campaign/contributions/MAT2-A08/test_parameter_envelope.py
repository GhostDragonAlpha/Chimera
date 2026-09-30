#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAT2-A08 named checks (done_when executable form).

Runs from the card directory or a git-archive extraction of it, provided the
pinned host inputs exist (this host).  Every check recomputes from pinned
bytes; nothing trusts the committed document's word alone.
"""

import json
import hashlib
import unittest
from pathlib import Path

import parameter_envelope as pe

CARD_DIR = Path(__file__).resolve().parent


def sha(b):
    return hashlib.sha256(b).hexdigest()


class X0_Guards(unittest.TestCase):
    def test_vacuous_guard_required_and_fires(self):
        state = pe.vacuous_guard_selftest()
        self.assertTrue(state["fires_on_identically_zero_window"])
        with self.assertRaises(ValueError) as cm:
            pe.refuse_vacuous_comparison(0.0, 0.0, "a08_suite_probe")
        self.assertIn("vacuous_comparison_refused:a08_suite_probe", str(cm.exception))


class X1_DocumentIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc_bytes = (CARD_DIR / "parameter_envelope.json").read_bytes()
        cls.doc = json.loads(cls.doc_bytes.decode("utf-8"))
        cls.profile, cls.prov = pe.load_registry_profile()
        cls.src = pe.load_sources()

    def test_schema_and_task_id_short(self):
        self.assertEqual(self.doc["schema"], pe.SCHEMA)
        self.assertEqual(self.doc["identity"]["task_id_short"], "A08")
        self.assertEqual(self.doc["identity"]["task_id"], "MAT2-A08")

    def test_criteria_identity_dispatch_registry_document(self):
        self.assertEqual(self.doc["identity"]["criteria_sha256"], pe.CRITERIA_SHA256)
        con = pe.sqlite3.connect(
            "file:%s?mode=ro" % pe.REGISTRY_DB.as_posix(), uri=True, timeout=10)
        try:
            state = json.loads(
                con.execute("select payload from state where id='1'").fetchone()[0])
        finally:
            con.close()
        card = state["kanban"]["cards"]["MAT2-A08"]
        self.assertEqual(card["criteria_sha256"], pe.CRITERIA_SHA256)
        attempt = card["attempts"][pe.ATTEMPT_ID]
        self.assertEqual(attempt["criteria_sha256"], pe.CRITERIA_SHA256)
        self.assertEqual(attempt["agent_id"], pe.ARRIVAL_ID)
        snap = json.loads(
            (CARD_DIR / "evidence" / "registry_verification_profile.json")
            .read_bytes().decode("utf-8"))
        self.assertEqual(snap["criteria_sha256"], pe.CRITERIA_SHA256)
        self.assertEqual(snap["profile"]["id"], "records")
        self.assertEqual(snap["profile"]["kind"], "offline")

    def test_records_profile_declares_no_capture(self):
        vp = self.doc["verification_profile"]
        self.assertEqual(vp["id"], "records")
        self.assertEqual(vp["kind"], "offline")
        self.assertFalse(vp["clean_view_required"])
        self.assertEqual(vp["camera_required_fields"], [])
        self.assertEqual(vp["capture_status"],
                         "not_required_by_profile (records/offline)")


class X2_PreregisteredPredictions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(
            (CARD_DIR / "parameter_envelope.json").read_bytes().decode("utf-8"))

    def test_all_predictions_true(self):
        for k in ("P1_osim_parse_identity", "P2_placeholder_census",
                  "P3_fcu_slot_swap", "P4_screen_recomputation_agrees",
                  "P5_segment_screens", "P6_namespaces_disjoint",
                  "P7_geometry_inference_census_zero",
                  "P8_inheritance_census_zero"):
            self.assertIs(self.doc["checks"][k], True, k)

    def test_counts_match_sealed_expectations(self):
        for k, v in pe.EXPECTED_COUNTS.items():
            self.assertEqual(self.doc["counts"][k], v, k)

    def test_row_level_screen_agreement_with_sealed_atlas(self):
        src = pe.load_sources()
        fresh = pe.compute_bio_rows(src)
        atlas_rows = {r["osim_muscle"]: r for r in src["atlas"]["muscle_rows"]}
        for r in fresh:
            if r["mapping"]["kind"] != "1:1":
                continue
            a = atlas_rows[r["osim_muscle"]]
            for q in ("fiber_length", "tendon_length", "pennation"):
                self.assertEqual(r["screens"][q]["class"], a[q]["class"],
                                 (r["osim_muscle"], q))


class X3_RecomputeAndDeterminism(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile, _ = pe.load_registry_profile()
        cls.src = pe.load_sources()

    def test_committed_document_validates_by_recomputation(self):
        doc = json.loads(
            (CARD_DIR / "parameter_envelope.json").read_bytes().decode("utf-8"))
        res = pe.validate_document(doc, self.src)
        self.assertTrue(res["structurally_valid"], res["refusals"])
        self.assertEqual(res["refusals"], [])

    def test_rebuild_is_byte_identical_to_committed_bytes(self):
        rebuilt = pe.canonical_json(pe.build_document(self.src, self.profile))
        self.assertEqual(rebuilt.encode("utf-8"),
                         (CARD_DIR / "parameter_envelope.json").read_bytes())

    def test_two_consecutive_builds_byte_identical(self):
        a = pe.canonical_json(pe.build_document(self.src, self.profile))
        b = pe.canonical_json(pe.build_document(pe.load_sources(), self.profile))
        self.assertEqual(a.encode("utf-8"), b.encode("utf-8"))

    def test_no_wall_clock_in_document(self):
        blob = (CARD_DIR / "parameter_envelope.json").read_bytes().decode("utf-8")
        for token in ("2026-09-30T", "generated_at", "timestamp"):
            self.assertNotIn(token, blob)


class X4_FalsifierArms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile, _ = pe.load_registry_profile()
        cls.src = pe.load_sources()
        cls.doc = json.loads(
            (CARD_DIR / "parameter_envelope.json").read_bytes().decode("utf-8"))
        cls.fr = json.loads(
            (CARD_DIR / "evidence" / "falsifier_receipt.json").read_bytes()
            .decode("utf-8"))

    def test_receipt_schema_and_all_green(self):
        self.assertEqual(self.fr["schema"], pe.FALSIFIER_SCHEMA)
        self.assertIs(self.fr["F_all_green"], True)
        self.assertIs(self.fr["clean_document_valid"], True)

    def test_live_rerun_bites_with_named_refusals(self):
        fresh = pe.run_falsifiers(self.src, self.doc)
        self.assertIs(fresh["F_all_green"], True)
        by_name = {a["arm"]: a for a in fresh["arms"]}
        expected = {
            "FB1_geometry_only_inference": "geometry_only_inference_refused",
            "FB2_human_norm_substitution": "human_norm_substitution_refused",
            "FB3_namespace_mixing": "engineering_value_in_biological_registry",
            "FB4_unauthorized_fitting": "fitting_unauthorized_refused",
            "FB5_source_pin_mutation": "input_pin_drift",
            "FB6_screen_flip": "screen_classification_mismatch",
            "FB7_silent_default": "silent_default_refused",
        }
        for arm, code in expected.items():
            self.assertIn(arm, by_name, arm)
            a = by_name[arm]
            self.assertTrue(a["bit"], arm)
            self.assertIn(code, a["observed"], arm)
            self.assertTrue(a["clean_control"]["within_tolerance"], arm)
            self.assertTrue(a["clean_control"]["guard"].startswith("a08_fb"))

    def test_disk_receipt_agrees_with_live_rerun(self):
        fresh = pe.run_falsifiers(self.src, self.doc)
        self.assertEqual([a["arm"] for a in fresh["arms"]],
                         [a["arm"] for a in self.fr["arms"]])
        for a, b in zip(fresh["arms"], self.fr["arms"]):
            self.assertEqual(a["expected_refusal"], b["expected_refusal"])
            self.assertEqual(a["bit"], b["bit"])

    def test_no_arm_fires_on_clean_document(self):
        res = pe.validate_document(self.doc, self.src)
        self.assertTrue(res["structurally_valid"])


class X5_SeparationAndLaws(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(
            (CARD_DIR / "parameter_envelope.json").read_bytes().decode("utf-8"))

    def test_namespaces_disjoint(self):
        bio = {r["osim_muscle"]
               for r in self.doc["biological_registry"]["actuator_rows"]}
        eng = {r["id"] for r in self.doc["engineering_registry"]["rows"]}
        self.assertEqual(bio & eng, set())
        for r in self.doc["engineering_registry"]["rows"]:
            self.assertIs(r["never_biological"], True)
            self.assertEqual(r["provenance"], "chosen_engineering")

    def test_engineering_values_match_sealed_carriers(self):
        rows = {r["id"]: r for r in self.doc["engineering_registry"]["rows"]}
        self.assertEqual(rows["m03_damping_per_s"]["value"], 240.0)
        self.assertEqual(rows["m03_edge_compliance"]["value"], 0.025)
        self.assertEqual(rows["m03_max_delta_p"]["value"], 5000.0)
        self.assertEqual(rows["m03_max_dv_dt"]["value"], 0.001)
        self.assertEqual(rows["m03_p_int_peak"]["value"], 120.0)
        self.assertEqual(rows["m03_xpbd_iterations"]["value"], 8)
        self.assertEqual(rows["m03_membrane_mass"]["value"], 0.05)
        self.assertAlmostEqual(rows["m03_dt_s"]["value"], 1.0 / 300.0)
        for rid, r in rows.items():
            self.assertEqual(r["source_status"], "synthetic_authored", rid)

    def test_no_fitted_keys_anywhere(self):
        self.assertEqual(pe.scan_fitted_keys(self.doc), [])

    def test_no_geometry_inference_no_forbidden_sources(self):
        bio = self.doc["biological_registry"]["actuator_rows"]
        self.assertEqual(pe.scan_geometry_inference_rows(bio), [])
        self.assertEqual(pe.scan_forbidden_sources_rows(bio), [])

    def test_unresolved_entries_complete(self):
        for u in self.doc["unresolved_entries"]:
            self.assertEqual(u["status"], "explicitly_unresolved", u["id"])
            self.assertTrue(u.get("missing_evidence"), u["id"])
            self.assertTrue(u.get("authorizing_rank"), u["id"])
        classes = {u["parameter_class"] for u in self.doc["unresolved_entries"]}
        for needed in ("strength_measured_upgrade", "muscle_mass_and_pcsa",
                       "force_length_velocity_dynamics", "activation_dynamics",
                       "tendon_compliance_stiffness", "biological_rom_joint_limits"):
            self.assertIn(needed, classes, needed)

    def test_ct_operator_gate_named(self):
        blob = json.dumps(self.doc["unresolved_entries"])
        self.assertIn("066485ae", blob)
        self.assertIn("BLOCKED FOR SHIP", blob)

    def test_carrier_rows_keep_honest_class(self):
        for r in self.doc["biological_registry"]["actuator_rows"]:
            self.assertEqual(r["source_class"],
                             "declared_carrier_not_source_backed",
                             r["osim_muscle"])

    def test_two_mass_systems_registered(self):
        tm = self.doc["selected_animal"]["two_mass_systems"]
        self.assertEqual(tm["body_mass_reference_kg"], [5.4, 6.9])
        self.assertEqual(tm["walk_scene_dynamics_mass_kg"], 10.038)


class X6_CalculationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(
            (CARD_DIR / "parameter_envelope.json").read_bytes().decode("utf-8"))

    def test_c07_c18_registered_open_inventory(self):
        ids = {c["id"]: c for c in self.doc["calculation_contracts"]}
        self.assertEqual(set(ids), {"C07", "C18"})
        for cid, c in ids.items():
            self.assertIn("OPEN INVENTORY", c["status"], cid)
            self.assertIn("no new numerical result claimed", c["status"], cid)
            self.assertTrue(c["verification_still_required"], cid)

    def test_c18_a06_ownership_counts(self):
        c18 = [c for c in self.doc["calculation_contracts"]
               if c["id"] == "C18"][0]
        self.assertIn("48 path records", c18["input_status"]["endpoints_waypoints"])
        self.assertIn("26 attachments", c18["input_status"]["endpoints_waypoints"])

    def test_c07_no_human_norm_output_law(self):
        c07 = [c for c in self.doc["calculation_contracts"]
               if c["id"] == "C07"][0]
        self.assertIn("no human-norm torque", c07["output_law"])


class X7_ReceiptIdentity(unittest.TestCase):
    def test_receipt_binds_document_bytes(self):
        qr = json.loads(
            (CARD_DIR / "qualification_receipt.json").read_bytes().decode("utf-8"))
        self.assertEqual(qr["schema"], pe.RECEIPT_SCHEMA)
        self.assertEqual(qr["criteria_sha256"], pe.CRITERIA_SHA256)
        self.assertEqual(qr["document_sha256"], sha(
            (CARD_DIR / "parameter_envelope.json").read_bytes()))
        self.assertEqual(qr["falsifier_receipt_sha256"], sha(
            (CARD_DIR / "evidence" / "falsifier_receipt.json").read_bytes()))
        hist = qr["preregistration_commit_history"]
        self.assertGreaterEqual(len(hist), 2)  # freeze + Amendment A1
        for s in hist:
            self.assertEqual(len(s), 40)
        self.assertEqual(len(qr["candidate_head"]), 40)

    def test_input_pins_verified_flag_and_shape(self):
        doc = json.loads(
            (CARD_DIR / "parameter_envelope.json").read_bytes().decode("utf-8"))
        self.assertIs(doc["input_pins"]["verified"], True)
        pins = doc["input_pins"]["pins"]
        self.assertEqual(len(pins), 12)
        for k, v in pins.items():
            self.assertEqual(len(v), 64, k)
            int(v, 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
