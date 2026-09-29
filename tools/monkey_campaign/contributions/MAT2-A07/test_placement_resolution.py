"""MAT2-A07 tests: frozen preregistration predictions P1-P9 + falsifiers.

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

import placement_resolution as pr  # noqa: E402


class PlacementResolutionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = pr.build_document()
        cls.receipt = pr.validate_document(cls.doc)

    # ---- P1 pins -------------------------------------------------------------
    def test_p1_a06_registry_pinned(self):
        self.assertEqual(pr.sha256_file(pr.registry_path()),
                         pr.A06_REGISTRY_SHA256)
        self.assertEqual(self.doc["depends_on"]["MAT2-A06"]["registry_sha256"],
                         pr.A06_REGISTRY_SHA256)
        self.assertEqual(self.doc["depends_on"]["MAT2-A06"]["merge_commit"],
                         pr.BASE_HEAD)

    def test_p1_live_pins_verified(self):
        self.assertEqual(self.receipt["live_pins"]["osim_sha256"],
                         pr.OSIM_SHA256)
        self.assertEqual(self.receipt["live_pins"]["hand_vtp_sha256"],
                         pr.HAND_VTP_SHA256)
        live = self.doc["live_pin_verification"]["a05_structure"]
        self.assertTrue(live["present"])
        self.assertEqual(live["sha256"], pr.A05_STRUCT_SHA256)

    def test_p1_preregistration_freeze_bound(self):
        self.assertEqual(self.doc["preregistration_sha256"],
                         pr.preregistration_sha256())
        self.assertEqual(pr.sha256_file(HERE / "PREREGISTRATION.md"),
                         self.doc["preregistration_sha256"])

    def test_p1_criteria_bound(self):
        self.assertEqual(self.doc["criteria_sha256"],
                         "c4d4ae430027d489d58007cae3895b81dcbfa604c045aa35"
                         "049c3ecf333373f8")
        self.assertEqual(self.doc["done_when"],
                         "Attachment validity is supported or explicitly "
                         "unresolved; any new fitting experiment is separately "
                         "authorized")

    # ---- P2 inventory conservation ------------------------------------------
    def test_p2_frozen_counts(self):
        for key, expected in pr.FROZEN_COUNTS.items():
            self.assertEqual(self.doc["counts"][key], expected, key)
        self.assertEqual(len(self.doc["path_resolutions"]), 48)
        self.assertEqual(len(self.doc["attachment_resolutions"]), 26)
        self.assertEqual(len(self.doc["waypoint_resolutions"]), 22)
        self.assertEqual(len(self.doc["grasp_endpoint_resolutions"]), 6)

    def test_p2_outside_set_exact(self):
        outside = sorted(r["record_id"] for r in self.doc["path_resolutions"]
                         if r["placement_failed_outside"])
        self.assertEqual(outside, sorted(pr.FROZEN_OUTSIDE))
        insertions = sorted(r["record_id"] for r in self.doc["path_resolutions"]
                            if r["placement_failed_outside"]
                            and r["role"] == "insertion_attachment")
        self.assertEqual(insertions, sorted(pr.FROZEN_OUTSIDE_INSERTIONS))
        waypoints = sorted(r["record_id"] for r in self.doc["path_resolutions"]
                           if r["placement_failed_outside"]
                           and r["role"].endswith("waypoint"))
        self.assertEqual(waypoints, sorted(pr.FROZEN_OUTSIDE_WAYPOINTS))

    def test_p2_outside_excesses_exact(self):
        # preregistration section 3: exact per-axis signed excesses
        expected = {
            "path.abd_poll_longus.3": ("z", "above_hi", 0.002449869999999999),
            "path.ext_carpi_rad_longus.3": ("z", "above_hi",
                                            7.276999999999978e-05),
            "path.ext_carp_rad_brevis.2": ("z", "above_hi",
                                           0.0007133999999999995),
            "path.ext_digitorum.2": ("z", "above_hi", 0.0013102099999999992),
            "path.ext_digiti.2": ("z", "above_hi", 0.0011906899999999995),
            "path.ext_indicis.3": ("z", "above_hi", 0.001892819999999999),
            "path.flex_carpi_ulnaris.2": ("z", "below_lo",
                                          -0.00039575000000000005),
            "path.palmaris_longus.3": ("z", "below_lo",
                                       -0.0004272500000000001),
        }
        seen = {}
        for row in self.doc["path_resolutions"]:
            if row["placement_failed_outside"]:
                axes = row["envelope_measurement"]["outside_axes"]
                self.assertEqual(len(axes), 1, row["record_id"])
                seen[row["record_id"]] = (axes[0]["axis"], axes[0]["kind"],
                                          axes[0]["excess_m"])
        self.assertEqual(seen, expected)

    # ---- P3 totality + vocabulary --------------------------------------------
    def test_p3_every_row_has_exactly_one_terminal_state(self):
        for rows in (self.doc["path_resolutions"],
                     self.doc["attachment_resolutions"],
                     self.doc["waypoint_resolutions"],
                     self.doc["grasp_endpoint_resolutions"]):
            for row in rows:
                self.assertIn(row["resolution"], pr.STATES)
                if row["resolution"] == pr.SUPPORTED:
                    self.assertIsNone(row["missing_evidence"])
                    self.assertIsInstance(row["evidence"], dict)
                else:
                    self.assertIsNone(row["evidence"])
                    self.assertIsInstance(row["missing_evidence"], dict)
                    self.assertTrue(row["missing_evidence"]["detail"])
                    self.assertTrue(
                        row["missing_evidence"]["authorization_required"])

    def test_p3_pending_mappings_unresolved_with_named_missing_evidence(self):
        pending = [r for r in self.doc["path_resolutions"]
                   if r["mutant_mapping_status"] == "pending_assembly_mapping"]
        self.assertEqual(len(pending), 14)
        for row in pending:
            self.assertEqual(row["resolution"], pr.UNRESOLVED)
            self.assertEqual(row["missing_evidence"]["kind"],
                             "recorded_assembly_mapping_decision")
            self.assertIn("recorded lead or captain",
                          row["missing_evidence"]["authorization_required"])
        inside_pending = [r for r in pending
                          if r["envelope_measurement"]["outcome"] == "inside"]
        self.assertEqual(len(inside_pending), 7)
        # envelope presence does NOT create ownership (B04 law)
        for row in inside_pending:
            self.assertEqual(row["resolution"], pr.UNRESOLVED)

    def test_p3_forearm_unresolved_but_osim_supported(self):
        forearm = [r for r in self.doc["path_resolutions"]
                   if not r["on_hand_body"]]
        self.assertEqual(len(forearm), 31)
        for row in forearm:
            self.assertEqual(row["resolution"], pr.UNRESOLVED)
            self.assertEqual(row["missing_evidence"]["kind"],
                             "forearm_assembly_correspondence_record")
            self.assertEqual(
                row["osim_reference_placement"]["validity"], pr.SUPPORTED)
            self.assertEqual(
                row["osim_reference_placement"]["evidence"]["sha256"],
                pr.OSIM_SHA256)

    def test_p3_mapped_supported_by_a05_record(self):
        mapped = [r for r in self.doc["path_resolutions"]
                  if r["mutant_mapping_status"] == "mapped"]
        self.assertEqual(len(mapped), 3)
        for row in mapped:
            self.assertEqual(row["resolution"], pr.SUPPORTED)
            evidence = row["evidence"]
            self.assertEqual(evidence["decision"], pr.A05_DECISION_ID)
            self.assertEqual(evidence["criteria_sha256"],
                             pr.A05_CRITERIA_SHA256)
            self.assertEqual(evidence["sha256"], pr.A05_STRUCT_SHA256)
            self.assertIsInstance(evidence["recorded_distance_m"], float)

    def test_p3_grasp_endpoints_supported(self):
        for row in self.doc["grasp_endpoint_resolutions"]:
            self.assertEqual(row["resolution"], pr.SUPPORTED)
            self.assertEqual(row["evidence"]["decision"], pr.A05_DECISION_ID)

    def test_p3_carried_observation_unresolved_and_unauthorized_to_fit(self):
        carried = self.doc["carried_observation"]
        self.assertEqual(carried["text"], pr.CARRIED_OBSERVATION)
        self.assertEqual(carried["resolution"], pr.UNRESOLVED)
        self.assertEqual(carried["missing_evidence"]["kind"],
                         "separately_authorized_fitting_experiment")
        self.assertEqual(carried["recorded_authorization_state"],
                         pr.CARRIED_AUTHORIZATION)
        self.assertIn("new fitting candidate is authorized",
                      carried["recorded_authorization_state"])

    # ---- P4 supported claims carry their pin ----------------------------------
    def test_p4_supported_shas_in_pinned_set(self):
        for rows in (self.doc["path_resolutions"],
                     self.doc["attachment_resolutions"],
                     self.doc["waypoint_resolutions"],
                     self.doc["grasp_endpoint_resolutions"]):
            for row in rows:
                if row["resolution"] == pr.SUPPORTED:
                    self.assertIn(row["evidence"]["sha256"], pr.PINNED_SHAS)

    # ---- P5 no unauthorized fitting -------------------------------------------
    def test_p5_no_fitted_keys_in_document(self):
        def scan(node, path=""):
            if isinstance(node, dict):
                for key, value in node.items():
                    self.assertNotIn("fitted", key.lower(), path + "/" + key)
                    self.assertNotIn("optimized", key.lower(), path + "/" + key)
                    if key != "law_statement":  # declared prose exemption
                        scan(value, path + "/" + key)
            elif isinstance(node, list):
                for item in node:
                    scan(item, path)

        scan(self.doc)

    # ---- P6 measured honesty (recompute) --------------------------------------
    def test_p6_validator_recomputes_measurement(self):
        with self.assertRaises(ValueError) as ctx:
            pr.validate_document(pr.tamper_measured_flip(self.doc),
                                 verify_live_pins=False)
        self.assertTrue(str(ctx.exception).startswith(pr.REF_MEASURE),
                        str(ctx.exception))

    def test_p6_bounds_frozen_match_live_a05(self):
        # build_document already refused on mismatch; here assert values
        self.assertEqual(pr.FROZEN_ENVELOPE_LO, [-0.0124375, -0.0837075,
                                                 -0.00152775])
        self.assertEqual(pr.FROZEN_ENVELOPE_HI,
                         [0.020731000000000003, -0.00010125000000000001,
                          0.004639750000000001])

    # ---- P7 registry conservation ---------------------------------------------
    def test_p7_registry_bytes_unchanged(self):
        self.assertEqual(pr.sha256_file(pr.registry_path()),
                         pr.A06_REGISTRY_SHA256)
        separation = pr.separation_check(self.doc)
        self.assertTrue(separation["registry_pin_carried"])
        self.assertTrue(separation["carried_blocks_independent_of_rows"])

    # ---- P8 C17 honesty inherited ---------------------------------------------
    def test_p8_c17_open_and_unsourced_numbers_refused(self):
        self.assertEqual(self.doc["c17"]["status"], "open")
        for row in self.doc["attachment_resolutions"]:
            mech = row["mechanics_c17"]
            self.assertEqual(mech["status"],
                             "inputs_unavailable_in_pinned_sources")
            numeric = [k for k, v in mech.items()
                       if isinstance(v, (int, float))
                       and not isinstance(v, bool)]
            self.assertEqual(numeric, [])
        with self.assertRaises(ValueError) as ctx:
            pr.validate_document(pr.tamper_stiffness(self.doc),
                                 verify_live_pins=False)
        self.assertTrue(str(ctx.exception).startswith(pr.REF_C17),
                        str(ctx.exception))

    def test_p8_waypoints_never_ports(self):
        for row in self.doc["waypoint_resolutions"]:
            self.assertIsNone(row["interface_id"])
            self.assertIs(row["bond"], False)

    # ---- P9 determinism --------------------------------------------------------
    def test_p9_byte_determinism(self):
        again = pr.build_document()
        self.assertEqual(pr.canonical(again), pr.canonical(self.doc))
        self.assertEqual(pr.digest(again), pr.digest(self.doc))

    # ---- falsifier probes: each must fire its exact named refusal --------------
    def test_falsifier_supported_pin_refused(self):
        with self.assertRaises(ValueError) as ctx:
            pr.validate_document(pr.tamper_supported_pin(self.doc),
                                 verify_live_pins=False)
        self.assertTrue(str(ctx.exception).startswith(pr.REF_SUPPORTED_PIN),
                        str(ctx.exception))

    def test_falsifier_silent_default_refused(self):
        with self.assertRaises(ValueError) as ctx:
            pr.validate_document(pr.tamper_silent_default(self.doc),
                                 verify_live_pins=False)
        self.assertTrue(str(ctx.exception).startswith(pr.REF_STATE),
                        str(ctx.exception))

    def test_falsifier_unauthorized_fit_refused(self):
        with self.assertRaises(ValueError) as ctx:
            pr.validate_document(pr.tamper_unauthorized_fit(self.doc),
                                 verify_live_pins=False)
        self.assertTrue(str(ctx.exception).startswith(pr.REF_FIT),
                        str(ctx.exception))

    def test_falsifier_registry_pin_refused(self):
        mutated = pr.tamper_registry(pr.registry_path().read_bytes())
        scratch = HERE / ".tamper_registry_scratch.json"
        scratch.write_bytes(mutated)
        try:
            with self.assertRaises(ValueError) as ctx:
                pr.validate_document(self.doc, registry_path_override=scratch,
                                     verify_live_pins=False)
            self.assertTrue(str(ctx.exception).startswith(pr.REF_REGISTRY_PIN),
                            str(ctx.exception))
        finally:
            scratch.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
