"""MAT2-B05 frozen probe battery (P1-P10) + falsifier bites (F1-F6).

Run from this directory:
    python -B test_mechanical_port_requirements.py
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

import mechanical_port_requirements as m  # noqa: E402


def relerr(a, b):
    scale = max(abs(x) for x in b) or 1.0
    return max(abs(x - y) for x, y in zip(a, b)) / scale


class ProbeBattery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc_path, cls.receipt = m.write_outputs(m.derive())
        cls.doc = m.load_json(cls.doc_path)
        cls.falsifiers = m.falsifier_proofs()

    def test_P1_port_inventory(self):
        cand, ports, waypoints = m.extract_sites()
        self.assertEqual(len(ports), 8)
        self.assertEqual(len(waypoints), 24)
        expected = {
            "radius": {"BIClong-P11", "BICshort-P8", "BRD-P3", "PT-P5"},
            "radius_l": {"BIClong_l-P11", "BICshort_l-P8", "BRD_l-P3", "PT_l-P5"},
        }
        got = {}
        for p in ports:
            got.setdefault(p["source_body"], set()).add(p["site_id"])
        self.assertEqual(got, expected)
        cp = m.cross_check_cannot_produce(ports)
        self.assertEqual(cp["evidence"]["ports_identified"], 8)
        for row in cp["ports_missing_parameters"]:
            self.assertIn("patch_area_m2", row["missing_parameters"])
            self.assertIn("weights", row["missing_parameters"])
        # positions carried verbatim from the pinned document
        raw = m.load_json(HERE / "data" / "attachment_candidates_854f7097.json")
        raw_pos = {s["site_id"]: s["source_pos_local"]
                   for b in raw["bodies"].values() for s in b["candidates"]}
        for p in ports:
            self.assertEqual(p["source_pos_local"], raw_pos[p["site_id"]])

    def test_P2_input_pins(self):
        pins = m.check_input_pins()
        self.assertEqual(len(pins), len(m.INPUT_PINS))
        with self.assertRaises(m.Refusal) as ar:
            m.check_input_pins(root=self._one_byte_tamper_tree())
        self.assertEqual(ar.exception.code, "input_pin_mismatch")

    def _one_byte_tamper_tree(self):
        troot = m._tampered_copy(lambda tr: None)
        p = troot / "data" / "attachment_candidates_854f7097.json"
        b = bytearray(p.read_bytes())
        b[0] ^= 0x01
        p.write_bytes(bytes(b))
        return troot

    def test_P3_status_ledger(self):
        for port in self.doc["ports"]:
            rows = port["inputs"]
            self.assertEqual(rows["anchor_frame_id"]["status"], "blocked")
            self.assertEqual(rows["endpoints_local_frame_id"]["status"], "blocked")
            self.assertEqual(rows["patch_area_m2"]["status"], "blocked_as_measured")
            self.assertEqual(rows["kappa_areal_n_m3"]["status"], "blocked_as_measured")
            self.assertEqual(rows["k_couple_min_n_m_per_rad"]["status"], "blocked_as_measured")
            self.assertEqual(rows["weights"]["status"], "split")
            self.assertEqual(
                rows["kappa_areal_n_m3"]["authored_requirement"]["source_status"],
                "synthetic_authored")
            self.assertEqual(
                rows["k_couple_min_n_m_per_rad"]["authored_requirement"]["source_status"],
                "synthetic_authored")
            self.assertEqual(
                rows["patch_area_m2"]["authored_requirement"]["source_status"],
                "synthetic_authored")
        ledger = self.doc["input_status_ledger"]
        self.assertEqual(len(ledger["blocked"]), 6)
        self.assertEqual(len(ledger["qualified"]), 2)
        for row in ledger["blocked"]:
            self.assertTrue(row["missing_evidence"], "every blocked row names its evidence")

    def test_P4_all_ports_blocked(self):
        self.assertEqual(self.doc["counts"]["ports_mechanically_qualified"], 0)
        self.assertEqual(self.doc["counts"]["ports_remaining_blocked"], 8)
        self.assertFalse(any(p["mechanical_qualification"] for p in self.doc["ports"]))
        for port in self.doc["ports"]:
            self.assertFalse(port["inputs_all_qualified"])
            self.assertTrue(port["blocked_reasons"])

    def test_P5_c17_closed_forms(self):
        # (a) declared 3-anchor rim disc: lambda_min = k r^2 / 2 (exact)
        for port in self.doc["ports"]:
            gate = port["inputs"]["c17_requirement_check"]
            lam_cf = gate["lambda_min_closed_form_n_m_per_rad"]
            self.assertLessEqual(
                abs(gate["lambda_min_n_m_per_rad"] - lam_cf) / lam_cf, 1e-12)
            self.assertLessEqual(gate["matrix_identity_rel_err"], 1e-12)
            self.assertLessEqual(gate["eigen_solver_rel_err"], 1e-6)
        # (b) elongated rectangle closed form {k b^2, k a^2, k (a^2+b^2)}
        a, b, k = 0.02, 1e-5, 80.0
        anchors = [[x * a, y * b, 0.0] for x, y in
                   ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        gate = m.admission(anchors, [0.25] * 4, k, 1e-30)
        pred = [k * b * b, k * a * a, k * (a * a + b * b)]
        self.assertLessEqual(relerr(gate["eigenvalues_measured_n_m_per_rad"], pred), 1e-9)
        # (c) uniform scaling: lambda proportional to s^2
        s = 3.0
        gate_s = m.admission([[c * s for c in p] for p in anchors], [0.25] * 4, k, 1e-30)
        ratio = [x / y for x, y in zip(gate_s["eigenvalues_measured_n_m_per_rad"],
                                       gate["eigenvalues_measured_n_m_per_rad"])]
        for r in ratio:
            self.assertLessEqual(abs(r - s * s), 1e-9 * s * s)

    def test_P6_admission_gate_counterexample(self):
        anchors = [[.02, 1e-5, 0], [-.02, 1e-5, 0], [-.02, -1e-5, 0], [.02, -1e-5, 0]]
        gate = m.admission(anchors, [0.25] * 4, 80.0, 1e-30)
        pred = [80.0 * 1e-10, 80.0 * 4e-4, 80.0 * (4e-4 + 1e-10)]
        self.assertLessEqual(relerr(gate["eigenvalues_measured_n_m_per_rad"], pred), 1e-9)
        self.assertAlmostEqual(gate["lambda_min_n_m_per_rad"], 8e-9, delta=1e-12)
        self.assertFalse(m.admission(anchors, [0.25] * 4, 80.0, 1.0)["admitted"])
        self.assertTrue(m.admission(anchors, [0.25] * 4, 80.0, 1e-9,
                                    kappa_areal=1.0e8, patch_area=8.0e-7)["admitted"])

    def test_P7_anchor_convention_material_point(self):
        conv = m.resolve_anchor_convention("material_point")
        self.assertIn("rest anchor", conv["rule"])
        for port in self.doc["ports"]:
            self.assertEqual(port["anchor_convention"]["kind"], "material_point")
            self.assertIn("mean body translation", port["anchor_convention"]["rule"])
        with self.assertRaises(m.Refusal) as ar:
            m.resolve_anchor_convention("deformed_face_centroid")
        self.assertEqual(ar.exception.code, "deformed_centroid_anchor_refused")

    def test_P8_determinism(self):
        a = m.canonical_json(m.derive())
        b = m.canonical_json(m.derive())
        self.assertEqual(hashlib.sha256(a.encode("utf-8")).hexdigest(),
                         hashlib.sha256(b.encode("utf-8")).hexdigest())
        disk = (HERE / "mechanical_port_requirements.json").read_bytes()
        self.assertEqual(disk, b.encode("utf-8"))

    def test_P9_no_invented_measured_values(self):
        # every qualified row cites a pinned input; authored rows declare
        # synthetic_authored; blocked rows name missing evidence
        pins = {p["id"] for p in m.INPUT_PINS}
        for port in self.doc["ports"]:
            w = port["inputs"]["weights"]
            self.assertIn(w["qualified"].get("input_pin"), pins)
        ledger = self.doc["input_status_ledger"]
        for row in ledger["authored_engineering_requirements"]:
            self.assertEqual(row["source_status"], "synthetic_authored")
        # B03 counted mass bitwise
        b03 = m.read_b03_masses()
        self.assertEqual(b03["bone_radius"]["mass_kg"], 0.00910051480229847)
        first = self.doc["ports"][0]["inputs"]["weights"]["qualified"]
        self.assertEqual(first["counted_bone_mass_radius_kg"], 0.00910051480229847)

    def test_P10_pressure_limit_carried_and_enforced(self):
        m03 = m.read_m03_pressure_limits()
        self.assertEqual(m03["max_delta_p_pa"], 5000.0)
        self.assertEqual(m03["source_status"], "synthetic_authored")
        for port in self.doc["ports"]:
            pl = port["inputs"]["pressure_limits"]
            self.assertEqual(pl["limits"]["max_delta_p_pa"], 5000.0)
        m.max_delta_p_refusal(5000.0, 4999.9999)  # inside limit: no refusal
        with self.assertRaises(m.Refusal) as ar:
            m.max_delta_p_refusal(5000.0, 5000.0000001)
        self.assertEqual(ar.exception.code, "pressure_source_delta_p_limit_exceeded")

    def test_F_falsifiers_all_bite(self):
        by_id = {p["id"]: p for p in self.falsifiers}
        for fid in ("F1_input_pin_tamper", "F2_waypoint_promotion",
                    "F3a_qualification_promotion", "F3b_unprovenanced_qualified_value",
                    "F4_k_provenance_break", "F5_synthetic_lambda_min_transfer",
                    "F6_deformed_centroid_anchor"):
            self.assertIn(fid, by_id)
            self.assertTrue(by_id[fid]["bites"], f"{fid} did not bite: {by_id[fid]}")
            self.assertEqual(by_id[fid]["code"], by_id[fid]["expected_code"])
        self.assertIs(by_id["real_artifact_untouched"]["bites"], True)

    def test_waypoint_refusal_api(self):
        with self.assertRaises(m.Refusal) as ar:
            m.resolve_port("BIClong-P9")
        self.assertEqual(ar.exception.code, "waypoint_not_a_port")
        with self.assertRaises(m.Refusal) as ar:
            m.resolve_port("nonexistent-site")
        self.assertEqual(ar.exception.code, "site_not_found")

    def test_document_validator_green_on_real_doc(self):
        self.assertTrue(m.validate_requirements_document(self.doc))


if __name__ == "__main__":
    unittest.main(verbosity=2)
