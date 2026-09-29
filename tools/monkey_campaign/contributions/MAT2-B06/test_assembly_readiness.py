"""MAT2-B06 frozen probes: P1-P9 confirmations + F1-F6 falsifier bites.

Run: python -B test_assembly_readiness.py
Every probe asserts an exact preregistered prediction; every falsifier tampers
a COPY, watches the named refusal, and discards the copy.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import assembly_readiness as ar

HERE = Path(__file__).resolve().parent
DOC_PATH = HERE / "assembly_readiness.json"


def load_doc() -> dict:
    return json.loads(DOC_PATH.read_text(encoding="utf-8"))


class FrozenProbes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = load_doc()
        cls.sealed = ar.load_sealed()
        cls.cheng = ar.load_cheng()
        cls.sv = ar.sealed_values(cls.sealed)

    def test_p1_sealed_pins_reverify(self):
        """Every sealed dependency document re-reads byte-exact at the tip."""
        for role, pin in self.doc["sealed_input_pins"].items():
            self.assertEqual(pin["blob_sha256"],
                             ar.SEALED_PINS[role][1], role)
        self.assertEqual(len(self.doc["sealed_input_pins"]), 8)

    def test_p2_frozen_counts_and_id_sets(self):
        counts = self.doc["counts"]
        self.assertEqual(counts["requirement_gate_rows"], 14)
        self.assertEqual(counts["gate_satisfied"], 4)
        self.assertEqual(counts["gate_gap"], 10)
        self.assertEqual(counts["measured_screen_rows"], 5)
        self.assertEqual(counts["gaps_by_domain"],
                         {"mass": 3, "ownership": 4, "frame": 2, "port": 1})
        ids = sorted(r["requirement_id"] for r in self.doc["requirements"])
        self.assertEqual(ids, sorted(
            ar.FROZEN_COUNTS["expected_satisfied_ids"]
            + ar.FROZEN_COUNTS["expected_gap_ids"]
            + ar.FROZEN_COUNTS["expected_screen_ids"]))

    def test_p3_every_gap_names_missing_evidence_and_rank(self):
        for row in self.doc["requirements"]:
            if row["kind"] == "requirement_gate" \
                    and row["status"] == ar.STATUS_GAP:
                me = row["missing_evidence"]
                self.assertTrue(me["detail"].strip(), row["requirement_id"])
                self.assertTrue(me["authorization_required"].strip(),
                                row["requirement_id"])

    def test_p4_satisfied_rows_reread_bitwise(self):
        """Validator V2/V3 passes on the committed document (re-read law)."""
        result = ar.validate_document(self.doc)
        self.assertTrue(result["valid"])
        self.assertEqual(result["gap"], 10)

    def test_p5_readiness_false_and_observation_verbatim(self):
        self.assertIs(self.doc["readiness"]["assembly_readiness"], False)
        self.assertEqual(self.doc["carried_observation"],
                         ar.CARRIED_OBSERVATION)
        reg = self.doc["registry_profile"]
        self.assertTrue(reg["available"])
        self.assertEqual(reg["task_id"], "B06")
        self.assertEqual(reg["profile_id"], "anatomy")
        self.assertEqual(reg["profile_kind"], "visible_static")
        self.assertEqual(reg["registry_criteria_sha256"], ar.CRITERIA_SHA256)

    def test_p6_screens_confirmed_with_exact_values(self):
        screens = {r["requirement_id"]: r for r in self.doc["requirements"]
                   if r["kind"] == "measured_screen"}
        for sid, row in screens.items():
            self.assertEqual(row["outcome"], "confirmed", sid)
            self.assertIs(row["gates"], False, sid)
        s5 = screens["S-MASS-05"]["computed"]
        self.assertTrue(all(c["inside_1sd"] for c in s5["comparisons"]))
        deltas = sorted(round(c["abs_delta_kg"], 9)
                        for c in s5["comparisons"])
        self.assertEqual(deltas, [0.008, 0.04, 0.091])
        s6 = screens["S-MASS-06"]["computed"]
        self.assertTrue(s6["all_implied_in_4_7_kg"])
        self.assertTrue(s6["ratio_gt_2"])
        implied = sorted(round(r["implied_body_weight_kg"], 9)
                         for r in s6["implied_body_weight"])
        self.assertEqual(implied, [4.909747292, 5.23255814, 6.09375])
        s7 = screens["S-MASS-07"]["computed"]
        self.assertTrue(s7["inside_0_3_1_5"])
        self.assertAlmostEqual(s7["bone_trace_over_measured_segment_sum"],
                               0.6977709058136352, places=12)
        self.assertEqual(screens["S-MASS-08"]["computed"]
                         ["m_fascicularis_verdict"], "inadmissible_species_law")
        self.assertTrue(screens["S-PORT-09"]["computed"]["coverage_ok"])

    def test_p7_determinism_double_derive_byte_identical(self):
        a = ar.canonical_json(ar.build_document())
        b = ar.canonical_json(ar.build_document())
        self.assertEqual(a, b)
        committed = DOC_PATH.read_text(encoding="utf-8")
        self.assertEqual(a, committed)

    def test_p8_cheng_pins_and_license_note(self):
        for role, pin in self.doc["cheng_source_pins"].items():
            self.assertEqual(pin["sha256"], ar.CHENG_PINS[role][1], role)
        self.assertIn("UNVERIFIED", self.doc["cheng_license_note"])
        m26 = self.cheng["m26_mulatta_inertials"]
        self.assertEqual(m26["segment_mass_g"]["upper_arm"][0] * ar.G_TO_KG,
                         0.294)
        self.assertEqual(m26["icg_mean_g_cm2"]["upper_arm"][0], 3240.0)

    def test_p9_vocabulary_lawful(self):
        for row in self.doc["requirements"]:
            if row["kind"] == "requirement_gate":
                self.assertIn(row["status"], ar.LAWFUL_GATE_STATUSES)
            else:
                self.assertIn(row["status"], ar.LAWFUL_SCREEN_STATUSES)
            ce = row.get("cheng_evaluation")
            if ce:
                self.assertIn(ce["verdict"], ar.CHENG_VERDICTS)


class FalsifierBites(unittest.TestCase):

    def test_f1_to_f6_all_bite(self):
        log = ar.run_falsifiers()
        self.assertEqual(len(log), 6, log)
        for entry in log:
            self.assertTrue(entry["bitten"],
                            f"{entry['arm']} did not bite: "
                            f"observed {entry['observed']}")
        codes = sorted(e["observed"] for e in log)
        self.assertEqual(codes, sorted([
            "unbound_input_refused",
            "satisfied_requires_pinned_evidence",
            "satisfied_requires_pinned_evidence",
            "cheng_source_pin_mismatch",
            "unlawful_status_refused",
            "sealed_pin_mismatch"]))
        # the real document must be untouched by the falsifier run
        self.assertEqual(ar.sha256_bytes(DOC_PATH.read_bytes()),
                         ar.sha256_bytes(ar.canonical_json(
                             ar.build_document()).encode("utf-8")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
