"""MAT2-A06 tests: frozen preregistration predictions P1-P8 + falsifiers.

Runs against the pinned sources live (read-only). Every tamper probe must fire
exactly its named refusal; determinism requires byte-identical rebuilds.
CPU-only, stdlib-only, bounded runtime.
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import attachment_ownership as ao  # noqa: E402


class AttachmentOwnershipTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = ao.build_document()
        cls.receipt = ao.validate_document(cls.doc)

    # ---- P1 pins -------------------------------------------------------------
    def test_p1_live_pins_verified(self):
        self.assertEqual(self.receipt["live_pins"]["osim_sha256"], ao.OSIM_SHA256)
        self.assertEqual(self.receipt["live_pins"]["hand_vtp_sha256"],
                         ao.HAND_VTP_SHA256)
        self.assertEqual(self.receipt["live_pins"]["a05_structure_sha256"],
                         ao.A05_STRUCT_SHA256)

    def test_p1_preregistration_freeze_bound(self):
        self.assertEqual(self.doc["preregistration_sha256"],
                         ao.preregistration_sha256())
        self.assertEqual(ao.sha256_file(HERE / "PREREGISTRATION.md"),
                         self.doc["preregistration_sha256"])

    # ---- P2 scope ------------------------------------------------------------
    def test_p2_frozen_counts(self):
        records = self.doc["path_records"]
        self.assertEqual(len(records), 48)
        self.assertEqual(len({r["muscle"] for r in records}), 13)
        self.assertEqual(
            sorted({r["muscle"] for r in records}), sorted(ao.GRASP_MUSCLES))
        self.assertEqual(sum(1 for r in records if r["on_hand_body"]), 17)
        self.assertEqual(
            sum(1 for r in records
                if r["role"] in ("origin_attachment", "insertion_attachment")), 26)
        self.assertEqual(
            sum(1 for r in records if r["role"].endswith("waypoint")), 22)
        conditional = [r for r in records if r["conditional"] is not None]
        self.assertEqual(len(conditional), 1)
        row = conditional[0]
        self.assertEqual(row["muscle"], "flex_digit_profundus")
        self.assertEqual(row["declared_name"], "flex_digit_profundus-P2")
        self.assertEqual(row["owner_body"], "radius")
        self.assertEqual(row["conditional"]["coordinate"], "radial_pronation")
        self.assertEqual(row["conditional"]["range_rad"], [-1.5708, 0.352382])

    def test_p2_origin_body_distribution(self):
        origins = [r for r in self.doc["path_records"]
                   if r["role"] == "origin_attachment"]
        counts = {}
        for row in origins:
            counts[row["owner_body"]] = counts.get(row["owner_body"], 0) + 1
        self.assertEqual(counts, {"humerus": 8, "ulna": 4, "radius": 1})

    def test_p2_repeated_declared_names_kept_verbatim(self):
        # ext_digitorum declares two points named 'ext_digitorum-P2'
        names = [(r["index"], r["declared_name"]) for r in self.doc["path_records"]
                 if r["muscle"] == "ext_digitorum"]
        self.assertEqual(names, [(0, "ext_digitorum-P1"), (1, "ext_digitorum-P2"),
                                 (2, "ext_digitorum-P3"), (3, "ext_digitorum-P2")])
        # abd_poll_longus carries the literal 'default' name at index 1
        abd = [(r["index"], r["declared_name"]) for r in self.doc["path_records"]
               if r["muscle"] == "abd_poll_longus"]
        self.assertEqual(abd, [(0, "abd_poll_longus-P1"), (1, "default"),
                               (2, "abd_poll_longus-P3"), (3, "abd_poll_longus-P4"),
                               (4, "abd_poll_longus-P3")])

    # ---- P3 ownership --------------------------------------------------------
    def test_p3_every_record_owned_and_role_assigned(self):
        for row in self.doc["path_records"]:
            self.assertTrue(row["owner_body"])
            self.assertIn(row["role"], ao.ROLES)
            self.assertEqual(row["approved_by"]["sha256"], ao.OSIM_SHA256)
        for row in self.doc["grasp_endpoints"]:
            self.assertTrue(row["owner_body"])
            self.assertIn(row["role"], ("grasp_contact_endpoint",
                                        "grasp_palm_reference"))

    def test_p3_grasp_endpoints_match_a05_record(self):
        a05 = json.loads(ao.A05_STRUCT_PATH.read_text(encoding="utf-8"))
        tips = a05["envelope_check"]["fingertip_positions_m"]
        by_id = {r["endpoint_id"]: r for r in self.doc["grasp_endpoints"]}
        self.assertEqual(len(by_id), 6)
        for key, owner, role in ao.GRASP_ENDPOINT_OWNERS:
            row = by_id["grasp.fingertip." + key]
            self.assertEqual(row["owner_body"],
                             "ref.macaque_arm_hand_mutation.body." + owner)
            self.assertEqual(row["role"], role)
            self.assertEqual(row["position_m"], tips[key])
        palm = by_id["grasp.palm_anchor"]
        self.assertEqual(palm["owner_body"],
                         "ref.macaque_arm_hand_mutation.body.macaque_hand_anchor")
        self.assertEqual(palm["role"], "grasp_palm_reference")

    def test_p3_mutant_mapping_honest(self):
        mapped = [r for r in self.doc["path_records"]
                  if r["mutant_mapping"].get("status") == "mapped"]
        pending = [r for r in self.doc["path_records"]
                   if r["mutant_mapping"].get("status")
                   == "pending_assembly_mapping"]
        self.assertEqual(len(mapped), 3)
        self.assertEqual(len(pending), 14)
        self.assertEqual(
            sorted((r["muscle"], r["declared_name"],
                    r["mutant_mapping"]["mutant_body"]) for r in mapped),
            [("ext_digitorum", "ext_digitorum-P2", "proxph3"),
             ("ext_digitorum", "ext_digitorum-P3", "macaque_hand_anchor"),
             ("flex_digit_profundus", "flex_digit_profundus-P4", "fifthmc")])

    # ---- P4 waypoints are never attachment ports -----------------------------
    def test_p4_waypoints_carry_no_interface_or_bond(self):
        hand_waypoints = [r for r in self.doc["path_records"]
                          if r["role"].endswith("waypoint") and r["on_hand_body"]]
        # abd_poll_longus index 4 ('P3') and the three insertion-shadowed
        # hand points (ext_carp_rad_brevis P3, ext_digitorum P3, ext_digiti P3)
        # are hand-body waypoints: on the bone, yet NOT attachment ports
        self.assertEqual(len(hand_waypoints), 4)
        for row in hand_waypoints:
            self.assertIsNone(row.get("interface_id"))
            self.assertIsNone(row.get("bond"))
        for row in self.doc["path_records"]:
            if row["role"].endswith("waypoint"):
                self.assertIsNone(row.get("interface_id"))
                self.assertIsNone(row.get("bond"))

    # ---- P5 explicit attachments ----------------------------------------------
    def test_p5_attachments_explicit_and_disjoint(self):
        attachments = self.doc["attachments"]
        self.assertEqual(len(attachments), 26)
        interfaces = [a["interface_id"] for a in attachments]
        self.assertEqual(len(set(interfaces)), 26)
        self.assertTrue(all(i.startswith("iface:tendon-") for i in interfaces))
        insertions = [a for a in attachments
                      if a["role"] == "insertion_attachment"]
        self.assertEqual(len(insertions), 13)
        self.assertTrue(all(a["bone"] == "hand" for a in insertions))
        containment_ids = {e["edge_id"] for e in self.doc["containment_edges"]}
        bond_ids = {b["bond_id"] for b in self.doc["bonds"]}
        attachment_ids = {a["attachment_id"] for a in attachments}
        self.assertFalse(containment_ids & bond_ids)
        self.assertFalse(containment_ids & attachment_ids)
        self.assertFalse(attachment_ids & bond_ids)

    # ---- P6 no silent bonds ---------------------------------------------------
    def test_p6_all_bonds_and_attachments_explicitly_declared(self):
        for bond in self.doc["bonds"]:
            self.assertEqual(bond["provenance"]["kind"], "explicit_declaration")
            self.assertEqual(bond["provenance"]["criteria_sha256"],
                             ao.A05_CRITERIA_SHA256)
        self.assertEqual(len(self.doc["bonds"]), 22)
        for attachment in self.doc["attachments"]:
            self.assertEqual(attachment["provenance"]["kind"],
                             "explicit_declaration")
            self.assertEqual(attachment["provenance"]["sha256"], ao.OSIM_SHA256)

    def test_p6_separation_check(self):
        result = ao.separation_check(self.doc)
        self.assertTrue(result["containment_unchanged_without_mechanics"])
        self.assertTrue(result["mechanics_unchanged_without_containment"])

    def test_falsifier_t1_rig_parentage_bond_refused(self):
        with self.assertRaisesRegex(ValueError, "^" + ao.REF_PARENTAGE_BOND):
            ao.validate_document(ao.tamper_rig_parentage(self.doc),
                                 verify_live_pins=False)

    def test_falsifier_t1b_containment_attachment_refused(self):
        with self.assertRaisesRegex(ValueError, "^" + ao.REF_PARENTAGE_BOND):
            ao.validate_document(ao.tamper_containment_bond(self.doc),
                                 verify_live_pins=False)

    def test_falsifier_t2_unowned_refused_not_defaulted(self):
        with self.assertRaisesRegex(ValueError, "^" + ao.REF_NO_OWNER):
            ao.validate_document(ao.tamper_unowned(self.doc),
                                 verify_live_pins=False)
        with self.assertRaisesRegex(ValueError, "^" + ao.REF_NO_ROLE):
            ao.validate_document(ao.tamper_role(self.doc),
                                 verify_live_pins=False)

    def test_falsifier_t4_owner_default_refused(self):
        with self.assertRaisesRegex(ValueError, "^" + ao.REF_OWNER_DEFAULT):
            ao.resolve_owner({"record_id": "path.x.0", "owner_body": None})
        with self.assertRaisesRegex(ValueError, "^" + ao.REF_OWNER_DEFAULT):
            ao.resolve_owner({"record_id": "path.x.1", "owner_body": ""})

    def test_falsifier_t3_waypoint_port_refused(self):
        with self.assertRaisesRegex(ValueError,
                                    "^" + ao.REF_WAYPOINT_PORT):
            ao.validate_document(ao.tamper_waypoint_port(self.doc),
                                 verify_live_pins=False)

    def test_falsifier_t5_wrong_pin_refused(self):
        with self.assertRaisesRegex(ValueError, "^" + ao.REF_BAD_PIN):
            ao.extract_osim_scope(osim_path=str(HERE / "PREREGISTRATION.md"))

    # ---- P7 determinism -------------------------------------------------------
    def test_p7_byte_determinism(self):
        first = ao.canonical(ao.build_document())
        second = ao.canonical(ao.build_document())
        self.assertEqual(first, second)
        r1 = ao.validate_document(self.doc)
        r2 = ao.validate_document(self.doc)
        self.assertEqual(r1["document_sha256"], r2["document_sha256"])

    # ---- P8 C17 honesty -------------------------------------------------------
    def test_p8_no_invented_mechanics(self):
        for attachment in self.doc["attachments"]:
            mech = attachment["mechanics_c17"]
            self.assertEqual(mech["status"],
                             "inputs_unavailable_in_pinned_sources")
            self.assertEqual(tuple(mech["required_inputs"]),
                             ao.C17_REQUIRED_INPUTS)
            numeric = [k for k, v in mech.items()
                       if isinstance(v, (int, float))
                       and not isinstance(v, bool)]
            self.assertEqual(numeric, [])

    def test_falsifier_t6_stiffness_claim_refused(self):
        with self.assertRaisesRegex(ValueError, "^" + ao.REF_STIFFNESS):
            ao.validate_document(ao.tamper_stiffness(self.doc),
                                 verify_live_pins=False)

    # ---- emitted artifact agreement -------------------------------------------
    def test_emitted_document_matches_build(self):
        emitted = HERE / "attachment_ownership.json"
        if not emitted.exists():
            self.skipTest("attachment_ownership.json not emitted yet")
        loaded = json.loads(emitted.read_text(encoding="utf-8"))
        self.assertEqual(ao.canonical(loaded), ao.canonical(self.doc))
        self.assertEqual(ao.validate_document(loaded)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
