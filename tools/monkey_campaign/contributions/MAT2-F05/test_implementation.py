"""test_implementation -- MAT2-F05 done_when checks (executable).

The done_when clause is a DECLARATION: "Slope, obstacle size and
surface-friction envelope is declared from evidence". These checks prove the
declaration exists, is derived from the pinned evidence (pin wall + sealed
receipt values), carries its placeholder naming and named-absent debts,
refuses laundering, binds the walk plane to the authored plateau, and is
captured under the registry profile. Zero skips.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import unittest

import implementation as impl

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PreregistrationFreeze(unittest.TestCase):

    def test_prereg_frozen_markers(self):
        text = (HERE / "PREREGISTRATION.md").read_text(encoding="utf-8")
        flat = " ".join(text.split())
        self.assertIn('done_when (verbatim): **"Slope, obstacle size and '
                      'surface-friction envelope is declared from '
                      'evidence"**', flat)
        for marker in ("P1 pin wall", "P2 slope-envelope derivation",
                       "P3 obstacle-envelope derivation",
                       "P4 friction-envelope derivation",
                       "P5 walk-plane identity", "P6 render/collision",
                       "P7 capture", "P8 determinism"):
            self.assertIn(marker, text)
        for arm in ("FB1_slope_envelope_mute", "FB2_undeclared_blocker",
                    "FB3_unnamed_placeholder", "FB4_grid_plane_binding",
                    "FB5_off_frame_probe_subject",
                    "FB6_render_collision_decouple"):
            self.assertIn(arm, text)

    def test_prereg_amendment_a1_band(self):
        text = (HERE / "PREREGISTRATION.md").read_text(encoding="utf-8")
        self.assertIn("Amendment A1", text)
        self.assertIn("(0.25, 0.57)", text)

    def test_criteria_identity_frozen_constants(self):
        self.assertEqual(impl.CARD, "MAT2-F05")
        self.assertEqual(impl.TASK_SHORT, "F05")
        self.assertEqual(impl.CRITERIA_SHA256,
                         "cf28ed888e4020f15f00ddd071758e647a55e8dbd6597368"
                         "bda2a3f2a546dca5")
        self.assertEqual(impl.BASE_REVISION,
                         "fa02f07508ee15b7679d0f2a95ac6b1894f77962")


class PinWall(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pins = impl.materialize_pins()

    def test_every_pin_raw_match(self):
        for key, pin in self.pins.items():
            self.assertTrue(pin["raw_match"], key)
            self.assertEqual(pin["sha256"],
                             impl.sha_bytes(pin["bytes"]), key)

    def test_walk_scene_seal(self):
        scene = json.loads(self.pins["w03_scene_json"]["bytes"])
        recipe = scene["gait_controller"]["recipe"]
        self.assertEqual(recipe["contact_friction"], 0.6)
        self.assertEqual(recipe["contact_plane_height_m"], 0.004)
        self.assertEqual(recipe["tick_hz"], 300)
        self.assertEqual(recipe["substeps"], 4)

    def test_obstacle_declaration_seal(self):
        decl = json.loads(self.pins["obstacle_declaration_json"]["bytes"])
        self.assertEqual(len(decl["obstacles"]), 7)
        self.assertEqual(decl["self_sha256"],
                         "7164eaf7ef110a8259572526eed0f9e1a5433f95d585cd953"
                         "c3411634669b81b")


class Derivations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pins = impl.materialize_pins()
        cls.src = impl.load_sources(cls.pins)
        cls.p2 = impl.derive_slope_envelope(cls.src)
        cls.p3 = impl.derive_obstacle_envelope(cls.src)
        cls.rows = impl.friction_table(cls.src)
        cls.p4 = impl.derive_friction_envelope(cls.src, cls.rows)
        cls.p5 = impl.derive_plane_identity(cls.src)

    def test_slope_declared_bound_dominates_measured(self):
        self.assertEqual(self.p2["declared_bound_m_per_m"], 0.05)
        worst = self.p2["derived_scene_max_grade_m_per_m"]
        self.assertEqual(worst, 0.03795552514626025)
        route_max = self.p2["measured_route_max_slope_m_per_m"]
        self.assertEqual(route_max, 0.026054)
        self.assertLess(worst, self.p2["declared_bound_m_per_m"])
        self.assertLess(route_max, self.p2["declared_bound_m_per_m"])

    def test_slope_sealed_route_facts(self):
        self.assertEqual(len(self.p2["flat_routes"]), 8)
        clear = self.p3["measured_global_min_clearance_m"]
        self.assertEqual(clear, 0.257478)
        self.assertGreaterEqual(clear, 0.25 - 1e-9)
        self.assertEqual(self.p3["measured_unattributed_cells"], 0)

    def test_obstacle_envelope_complete(self):
        rows = self.p3["declared_obstacles"]
        self.assertEqual([r["id"] for r in rows],
                         ["rock_01", "rock_02", "rock_03", "log_01",
                          "log_02", "stand_01", "stand_02"])
        for row in rows:
            if row["kind"] == "rock":
                for v in row["extent_m"]:
                    self.assertTrue(0.25 < v < 0.57, row["id"])
            if row["kind"] == "log":
                self.assertIn(row["log_radius_m"], (0.141408, 0.128476))
            if row["kind"] == "stand":
                self.assertEqual(row["extent_m"][1], 1.6)

    def test_friction_rows_named_with_debts(self):
        self.assertTrue(impl.validate_friction_rows(self.rows))
        for row in self.rows:
            if row["class"] == "NAMED-PLACEHOLDER":
                self.assertTrue(row["debt_owner"], row["carrier"])
            if row["class"] == "MEASURED-CONTEXT":
                self.assertTrue(row["source_pin"], row["carrier"])

    def test_friction_laundering_refused(self):
        stripped = json.loads(json.dumps(self.rows))
        hit = False
        for row in stripped:
            if row["class"] == "NAMED-PLACEHOLDER":
                row["class"] = "MEASURED"
                row["debt_owner"] = None
                hit = True
                break
        self.assertTrue(hit)
        with self.assertRaises(impl.Refusal) as caught:
            impl.validate_friction_rows(stripped)
        self.assertEqual(caught.exception.code, "f05_unnamed_placeholder")

    def test_plane_identity_authored_not_grid(self):
        self.assertEqual(self.p5["walk_scene_plane_m"], 0.004)
        self.assertEqual(self.p5["authored_plateau_m"], 0.004)
        self.assertEqual(self.p5["walk_scene_plane_m"],
                         self.p5["authored_plateau_m"])
        self.assertLess(self.p5["terrain_grid_bilinear_at_centre_m"], -30.0)
        self.assertTrue(30.0 < self.p5["disagreement_m"] < 35.0)
        self.assertEqual(self.p5["flatten"]["plateau_r_m"], 6.0)
        self.assertEqual(self.p5["flatten"]["splice_r_m"], 18.0)

    def test_flat_ground_record_honoured(self):
        rec = self.p4["flat_ground_training_record"]
        self.assertEqual(rec["velocity_envelope_m_s"],
                         2.977443609022557)
        self.assertIn("unevidenced", rec["consequence"])

    def test_slope_friction_margin(self):
        cons = self.p4["slope_friction_consistency"]
        self.assertGreaterEqual(cons["margin_factor_mu_over_tan"],
                                12.0 - 1e-9)


class Falsifiers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pins = impl.materialize_pins()
        cls.src = impl.load_sources(cls.pins)
        cls.bites = impl.run_bites(cls.src)

    def test_all_six_arms_bite(self):
        self.assertTrue(self.bites["bites_all_bite"])
        arms = [b["arm"] for b in self.bites["falsifier_bites"]]
        self.assertEqual(len(arms), 6)
        self.assertEqual(len(set(arms)), 6)

    def test_every_arm_has_clean_control_and_guard(self):
        for b in self.bites["falsifier_bites"]:
            self.assertIn("clean_control", b, b["arm"])
            self.assertTrue(b["clean_control"].get("guard", "").startswith(
                "f05_fb"), b["arm"])


class Receipts(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.checks = json.loads(
            (HERE / "checks_receipt.json").read_text(encoding="utf-8"))
        cls.declaration = json.loads(
            (EVIDENCE / "terrain_envelope_declaration.json").read_text(
                encoding="utf-8"))

    def test_checks_identity_and_flags(self):
        self.assertEqual(self.checks["schema"],
                         "chimera.mat2_f05.terrain_envelope.v1")
        self.assertTrue(self.checks["all_ok"])
        self.assertTrue(self.checks["bites_all_bite"])
        ident = self.checks["identity"]
        self.assertEqual(ident["task_id"], "F05")
        self.assertEqual(ident["calculation_contract"], "C14")
        self.assertEqual(ident["base_revision"], impl.BASE_REVISION)

    def test_declaration_sections_and_absent_variables(self):
        self.assertEqual(self.declaration["schema"],
                         "chimera.mat2_f05.terrain_envelope.v1")
        for section in ("slope", "obstacles", "friction"):
            self.assertIn(section, self.declaration["walkable_scope_declared"])
        absent = self.declaration["named_absent_variables"]
        self.assertGreaterEqual(len(absent), 5)
        for row in absent:
            self.assertEqual(row["status"], "ABSENT")
            self.assertTrue(row["debt_owner"], row["variable"])

    def test_capture_manifest_binding(self):
        manifest = json.loads(
            (EVIDENCE / "capture_manifest.json").read_text(
                encoding="utf-8"))
        self.assertEqual(manifest["task_id"], "F05")
        self.assertEqual(manifest["profile_id"], "forest")
        v1 = EVIDENCE / "frame_V1_clearing_overview_clean.png"
        self.assertEqual(manifest["capture_sha256"], sha_file(v1))
        self.assertEqual(manifest["subject_sha256"],
                         self.checks["envelope_declaration_sha256"])
        state_hashes = {row["state_binding"]["sha256"]
                        for row in manifest["views"]}
        self.assertEqual(len(state_hashes), 1)
        validation = json.loads(
            (EVIDENCE / "validation_receipt.json").read_text(
                encoding="utf-8"))
        self.assertTrue(validation["structurally_valid"])
        self.assertEqual(validation["validated_profile_kind"],
                         "visible_static")


if __name__ == "__main__":
    unittest.main()
