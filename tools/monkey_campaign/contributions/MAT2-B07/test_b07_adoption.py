#!/usr/bin/env python3
"""MAT2-B07 named checks: the executable done_when surface + falsifier arms.

Every falsifier arm carries its own passing clean control FIRST and a named
premature guard (G1); tampering happens on scratch copies only, never on the
pinned bytes or the card dir. The suite executes fully (no skips; G12).

Run:  python -B -m unittest discover -s . -p "test_*.py"   (from this dir)
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import adoption_record as adr  # noqa: E402
import ownership_mappings as own  # noqa: E402

CONVENTION_WINDOW_M = 1e-5


def refuse_vacuous_comparison(a, b, code):
    """P5/G5: a relative-window gate must refuse vacuous inputs up front."""
    if a is b:
        raise ValueError("vacuous_comparison:" + code + ":same_object")
    if a == 0 and b == 0:
        raise ValueError("vacuous_comparison:" + code + ":both_zero")


def vacuous_guard_selftest():
    for a, b in ((0.0, 0.0), (1.0, 1.0)):
        try:
            refuse_vacuous_comparison(a, b, "selftest")
        except ValueError:
            continue
        raise AssertionError("vacuous guard did not fire")
    refuse_vacuous_comparison(1.0, 2.0, "selftest")  # must pass
    return True


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_receipt(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def tampered_json(src_path, mutate):
    """Write a tampered copy to a scratch dir; return its path."""
    data = json.loads(Path(src_path).read_text(encoding="utf-8"))
    mutate(data)
    tmp = tempfile.mkdtemp(prefix="b07_falsifier_")
    out = Path(tmp) / Path(src_path).name
    out.write_bytes(json.dumps(data, sort_keys=True).encode("utf-8"))
    return out


class VacuousGuardSelftest(unittest.TestCase):
    def test_00_guard_selftest_runs_first(self):
        self.assertTrue(vacuous_guard_selftest())


class Pins(unittest.TestCase):
    def test_q1_input_pins_rehash(self):
        self.assertEqual(sha(own.A07_PATH), own.A07_SHA256)
        self.assertEqual(sha(own.A05_PATH), own.A05_SHA256)
        self.assertEqual(sha(own.OSIM_PATH), own.OSIM_SHA256)
        self.assertEqual(sha(adr.B04_PATH), adr.B04_SHA256)
        self.assertEqual(sha(adr.B05_PATH), adr.B05_SHA256)
        self.assertEqual(sha(adr.B06_RECEIPT_PATH), adr.B06_RECEIPT_SHA256)
        self.assertEqual(sha(adr.PRODUCER_PATH), adr.PRODUCER_SHA256)
        self.assertEqual(sha(adr.MASSREG_PATH), adr.MASSREG_SHA256)
        self.assertEqual(sha(adr.MASS_AUDIT_RECEIPT_PATH),
                         adr.MASS_AUDIT_RECEIPT_SHA256)
        self.assertEqual(sha(adr.OSIM_PATH), adr.OSIM_SHA256)

    def test_q1b_criteria_pin_matches_registry_ro(self):
        adr.check_registry_criteria()  # refuses (SystemExit 2) on drift
        own.check_registry_criteria()


class OwnershipMappings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a07, cls.a05 = own.load_inputs()
        cls.records = own.census(cls.a07)
        cls.bodies = own.a05_bodies(cls.a05)
        cls.joints = own.osim_joint_chain()
        cls.receipt = load_receipt("ownership_mappings.json")
        cls.hand = cls.receipt["records"]["hand_body_mappings"]
        cls.fore = cls.receipt["records"]["forearm_correspondences"]

    def test_q2_census_matches_sealed_bytes(self):
        counts = {"path_resolutions_total": len(self.records),
                  "mapped": 3, "pending_assembly_mapping": 14,
                  "not_on_hand_body": 31}
        for k, v in counts.items():
            got = (len(self.records) if k == "path_resolutions_total"
                   else sum(1 for r in self.records
                            if r.get("mutant_mapping_status") == k))
            self.assertEqual(got, v)

    def test_q2b_owner_body_census(self):
        owner = {}
        for r in self.records:
            owner[r["owner_body"]] = owner.get(r["owner_body"], 0) + 1
        self.assertEqual(owner, own.EXPECTED_CENSUS["owner_body"])

    def test_q3_f1_law_bit_exact_three_rows(self):
        rows = self.receipt["law_validation"]["captain_mapped_rows"]
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertTrue(row["bit_exact"])
        recomputed = own.verify_a05_law(self.a05)
        self.assertEqual(len(recomputed), 3)
        for row in recomputed:
            self.assertTrue(row["bit_exact"])

    def test_q4_hand_records_14_and_nearest_reproduces(self):
        self.assertEqual(len(self.hand), 14)
        self.assertEqual(self.receipt["counts"]["hand_records"], 14)
        for rec in self.hand:
            loc = rec["location_m"]
            nearest, distance = own.nearest_mutant_body(self.bodies, loc)
            self.assertEqual(nearest,
                             rec["decision"]["nearest_mutant_body"])
            self.assertEqual(distance,
                             rec["decision"]["recorded_distance_m"])
            self.assertGreater(distance, 0.0)
            self.assertEqual(rec["authorization"]["message_id"],
                             own.AUTH_MESSAGE_ID)
            self.assertEqual(rec["decision"]["kind"],
                             "recorded_assembly_mapping_decision")

    def test_q5_forearm_records_31_scope_and_distance(self):
        self.assertEqual(len(self.fore), 31)
        for rec in self.fore:
            own.check_mutation_scope(self.a05, rec["owner_body"])
            interface = own.wrist_origin_in(rec["owner_body"], self.joints)
            self.assertEqual(
                interface,
                rec["decision"]["mutation_interface"]["origin_in_owner_frame_m"])
            distance = math.dist(rec["location_m"], interface)
            self.assertEqual(distance,
                             rec["decision"]["recorded_distance_m"])
            self.assertGreater(distance, 0.0)
            note = rec["decision"]["euler_convention_note"]
            refuse_vacuous_comparison(note["alternative_max_delta_m"],
                                      CONVENTION_WINDOW_M,
                                      "convention_window")
            self.assertLess(note["alternative_max_delta_m"],
                            CONVENTION_WINDOW_M)
            self.assertEqual(rec["authorization"]["message_id"],
                             own.AUTH_MESSAGE_ID)

    def test_q5b_forearm_owner_split(self):
        got = {}
        for rec in self.fore:
            got[rec["owner_body"]] = got.get(rec["owner_body"], 0) + 1
        self.assertEqual(got, {"ulna": 5, "radius": 18, "humerus": 8})

    # ---- falsifier arms (clean control FIRST, then the bite) ----
    def test_fb1_hand_tamper_moves_distance(self):
        clean_loc = self.hand[0]["location_m"]
        clean_nearest = self.hand[0]["decision"]["nearest_mutant_body"]
        clean_d = math.dist(clean_loc,
                            own.a05_origin(self.bodies, clean_nearest))
        guard = abs(clean_d - self.hand[0]["decision"]
                    ["recorded_distance_m"])
        self.assertEqual(guard, 0.0)  # b07_fb1_premature guard: clean run bites nothing
        moved = list(clean_loc)
        moved[0] += 1e-3
        tampered_nearest, tampered_d = own.nearest_mutant_body(
            self.bodies, moved)
        changed = (tampered_nearest != clean_nearest
                   or tampered_d != clean_d)
        self.assertTrue(changed, "tampered point did not move the mapping")

    def test_fb2_scope_tamper_refuses(self):
        # tamper: pretend the mutation scope covers a forearm body
        fake = copy.deepcopy(self.a05)
        fake["bodies"] = list(fake["bodies"])
        fake["bodies"][0]["human_source"]["body"] = "radius"
        with self.assertRaises(SystemExit) as ctx:
            own.check_mutation_scope(fake, "radius")
        self.assertEqual(ctx.exception.code, 2)

    def test_fb2b_scope_tamper_clean_control(self):
        # clean control: the real scope check passes for all 3 forearm bodies
        for body in ("ulna", "radius", "humerus"):
            own.check_mutation_scope(self.a05, body)


class FrameBindings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b04 = json.loads(adr.B04_PATH.read_text(encoding="utf-8"))
        cls.producer = json.loads(
            adr.PRODUCER_PATH.read_text(encoding="utf-8"))
        cls.receipt = load_receipt("frame_bindings.json")

    def test_q6_binding_rows_stable_name(self):
        rows = self.receipt["r_frm_02"]["part_b_packet_to_forest_binding"][
            "binding_rows"]
        self.assertEqual(len(rows), 4)
        recomputed = adr.build_binding_rows(self.b04)  # refuses on mismatch
        self.assertEqual(len(recomputed), 4)
        for row in recomputed:
            self.assertEqual(row["authored_root_frame_body"],
                             adr.EXPECTED_ROOT_BODY[row["component_id"]])
            for fitted in row["fitted_frames_bound_by_stable_name"]:
                self.assertTrue(fitted.startswith("fitted_"))

    def test_q7_cross_record_agreement(self):
        agreement = self.receipt["r_frm_03"]["agreement_evidence"]
        self.assertTrue(agreement["equal"])
        self.assertEqual(agreement["counted_mass_kg"], 0.0)
        self.assertEqual(sorted(agreement["b04_unresolved"]),
                         sorted(adr.EXPECTED_UNRESOLVED))
        self.assertEqual(sorted(agreement["producer_unresolved"]),
                         sorted(adr.EXPECTED_UNRESOLVED))

    def test_q7b_ports_still_refused(self):
        b05 = json.loads(adr.B05_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(b05["ports"]), 8)
        for port in b05["ports"]:
            self.assertIs(port["mechanical_qualification"], False)

    # ---- falsifier arms ----
    def test_fb3_binding_name_tamper_refuses(self):
        def mutate(data):
            data["frames"]["root_pelvis"]["body"] = "pelvis_tampered"
        path = tampered_json(adr.B04_PATH, mutate)
        b04 = json.loads(path.read_text(encoding="utf-8"))
        with self.assertRaises(SystemExit) as ctx:
            adr.build_binding_rows(b04)
        self.assertEqual(ctx.exception.code, 2)

    def test_fb3_binding_clean_control(self):
        rows = adr.build_binding_rows(self.b04)
        self.assertEqual(len(rows), 4)  # b07_fb3_premature guard

    def test_fb4_agreement_tamper_refuses(self):
        def mutate(data):
            data["admission"]["bodies"]["unresolved"] = [
                b for b in data["admission"]["bodies"]["unresolved"]
                if b != "thorax"]
        path = tampered_json(adr.PRODUCER_PATH, mutate)
        producer = json.loads(path.read_text(encoding="utf-8"))
        with self.assertRaises(SystemExit) as ctx:
            adr.verify_cross_record_agreement(self.b04, producer)
        self.assertEqual(ctx.exception.code, 2)

    def test_fb4_agreement_clean_control(self):
        agreement = adr.verify_cross_record_agreement(self.b04, self.producer)
        self.assertTrue(agreement["equal"])  # b07_fb4_premature guard


class AdoptionRecord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = load_receipt("adoption_record.json")

    def test_q8_authorization_package_complete(self):
        items = self.receipt["authorization_package"]
        self.assertEqual([i["item"] for i in items], list(range(1, 9)))
        expected_rulings = {1: "R-MASS-04", 2: "R-MASS-02", 3: "R-MASS-03",
                            4: "R-OWN-02/03", 5: "R-OWN-04", 6: "R-OWN-05",
                            7: "R-FRM-02", 8: "R-FRM-03"}
        lawful = {"closed_by_work_with_receipt",
                  "closed_by_recorded_ruling",
                  "closed_by_recorded_ruling_with_work_receipt",
                  "refusal_stands", "authorized_lane_open",
                  "lane_evidence_delivered"}
        for item in items:
            self.assertEqual(item["ruling"], expected_rulings[item["item"]])
            self.assertIn(item["discharge"], lawful)

    def test_q8b_per_row_table_covers_the_sealed_rows(self):
        table = self.receipt["readiness_closure_table"]
        self.assertEqual(len(table["rows"]), 14)
        sealed_ids = {"R-MASS-01", "R-MASS-02", "R-MASS-03", "R-MASS-04",
                      "R-OWN-01", "R-OWN-02", "R-OWN-03", "R-OWN-04",
                      "R-OWN-05", "R-FRM-01", "R-FRM-02", "R-FRM-03",
                      "R-PRT-01", "R-PRT-02"}
        self.assertEqual({r["requirement_id"] for r in table["rows"]},
                         sealed_ids)

    def test_q8c_no_readiness_claim_no_port_claim(self):
        self.assertIs(
            self.receipt["readiness_closure_table"][
                "assembly_readiness_claimed"], False)
        self.assertEqual(self.receipt["mass_law_carried"]["admitted_here"],
                         0.0)
        self.assertEqual(
            self.receipt["mass_law_carried"]["transported_uncounted_kg"],
            5.262978509953907)
        self.assertEqual(self.receipt["mass_law_carried"]["pelvis_reference_kg"],
                         11.777)

    def test_q9_tc7_bind_present(self):
        bind = self.receipt["tc7_body_domain_bind"]
        self.assertTrue(bind["bound_as"]["body_digest"].startswith(
            "chimera.b07.adoption."))
        self.assertNotIn("UNBOUND_dummy",
                         bind["bound_as"]["body_digest"])
        self.assertIn("NOT runtime-qualified",
                      bind["bound_as"]["qualification_state"])
        self.assertEqual(bind["bound_as"]["mass_line"] != "", True)

    def test_q9b_tc12_rebind_names_prerequisites(self):
        tc12 = self.receipt["tc12_rebind_record"]
        self.assertEqual(len(tc12["reissue_prerequisites_named"]), 4)
        self.assertIn("not silently invalidated", tc12["symmetric_clause"])

    def test_q10_architect_reason_records_done_when_elements(self):
        reason = self.receipt["adoption_decision"]["architect_named_reason"]
        for needle in ("ADOPT-WITH-AUTHORIZATIONS", "M11",
                       "TC-7", "TC-12", "10.037998", "TC-8",
                       "Static export is not runtime qualification"):
            self.assertIn(needle, reason)

    def test_q11_pin_vs_disk_self(self):
        # G10 assist: the receipt pins that resolve on disk must match
        pins = self.receipt.get("input_pins") or {}
        checks = 0
        for _role, p in pins.items():
            disk = sha(Path(p["path"]))
            self.assertEqual(disk, p["sha256"],
                             "pin_vs_disk:" + p["path"])
            checks += 1
        self.assertGreaterEqual(checks, 10)

    def test_q11b_ownership_receipt_pins_self(self):
        pins = load_receipt("ownership_mappings.json")["input_pins"]
        for _role, p in pins.items():
            self.assertEqual(sha(Path(p["path"])), p["sha256"],
                             "pin_vs_disk:" + p["path"])


if __name__ == "__main__":
    unittest.main()
