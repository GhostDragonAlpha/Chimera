"""ONT-A02 CPU tests: falsifiable re-verification + capture structural checks.

Run: python -B -m unittest test_ota02_radioulnar -v
Everything is offline, deterministic, CPU-only. The canonical campaign validator
is imported read-only (python -B prevents bytecode writes) from
E:/PythonChimera/tools/monkey_campaign so tests exercise the SAME visual gate
the reviewer runs.

Falsifier discipline (PREREGISTRATION FA/FC/FE): the adversarial demos here
FAIL FIRST by construction - the clipped-subject guard, the tampered-value
detectors and the wrong-owner discrimination are exercised in their FIRING
configuration and asserted to fire, then the real artifact is asserted clean.
"""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ota02_radioulnar as core  # noqa: E402

EVIDENCE = HERE / "evidence"

STATE, RECEIPT = core.write_receipts()
MAP = RECEIPT["before_after_radius_map"]
REC08 = core.load_json("i7_receipts/08_radius_before_after.json")


def _manifest():
    return json.loads((EVIDENCE / "capture_manifest.json").read_text())


class TestInputIdentities(unittest.TestCase):
    def test_pinned_inputs_match_expect_sha(self):
        self.assertEqual(hashlib.sha256(core.INPUT_BIRTH.read_bytes()).hexdigest(),
                         core.EXPECT_SHA["birth"])
        self.assertEqual(hashlib.sha256(core.INPUT_PACK.read_bytes()).hexdigest(),
                         core.EXPECT_SHA["pack"])

    def test_extraction_manifest_hashes_match_files(self):
        ext = json.loads((HERE / "reference" / "EXTRACTION.json").read_text())
        for rel, meta in ext["files"].items():
            p = HERE / "reference" / rel
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                             meta["sha256"], rel)
            self.assertEqual(p.stat().st_size, meta["bytes"], rel)


class TestP1P2SourceRadioulnar(unittest.TestCase):
    def test_probe_verdict_and_frozen_numbers(self):
        p = RECEIPT["radioulnar_definition"]
        self.assertTrue(p["verdict"])
        self.assertAlmostEqual(p["offset_norm_mm"], 23.0746, delta=5e-4)
        self.assertAlmostEqual(p["source_forearm_ulna_to_hand_mm"], 305.7922,
                               delta=1e-3)
        self.assertAlmostEqual(p["source_radius_edge_radius_to_hand_mm"],
                               292.0294, delta=1e-3)
        self.assertAlmostEqual(p["authored_fraction_pct"], 7.5459, delta=1e-3)
        self.assertAlmostEqual(p["obliquity_deg"], 51.63, delta=0.05)
        self.assertAlmostEqual(p["axial_component_mm"], 14.324, delta=5e-3)
        self.assertAlmostEqual(p["lateral_component_mm"], 18.088, delta=5e-3)

    def test_wrong_owners_do_not_reproduce(self):
        """Falsifier FE: the offset must NOT reproduce from wrong owners."""
        p = RECEIPT["radioulnar_definition"]
        self.assertFalse(any(p["wrong_owner_reproductions"].values()))
        for name, val in p["wrong_owner_norms_mm"].items():
            self.assertGreater(abs(val - p["offset_norm_mm"]), 1.0, name)

    def test_declared_source_landmarks_bound_to_xml(self):
        p = RECEIPT["radioulnar_definition"]
        self.assertTrue(p["declared_source_binding_ok"])
        self.assertLessEqual(p["declared_source_binding_max_diff_m"],
                             core.TOL_LANDMARK_M)


class TestP3P5BeforeAfterMap(unittest.TestCase):
    def test_scales_reproduce_receipt_exactly(self):
        for side, body in (("right", "radius"), ("left", "radius_l")):
            s = MAP[side]
            self.assertEqual(s["s_old"], REC08["before"][body]["scale"])
            self.assertLessEqual(abs(s["s_new"] - REC08["after"][body]["scale"]),
                                 core.TOL_SCALE_REL)
            self.assertEqual(s["s_new"], s["span_new_m"] / s["src_span_m"])
            self.assertEqual(s["src_span_m"],
                             REC08["before"][body]["source_span_m"])

    def test_scale_change_and_transcription_slip(self):
        for side, body in (("right", "radius"), ("left", "radius_l")):
            s = MAP[side]
            self.assertAlmostEqual(s["scale_change_pct"],
                                   REC08["after"][body]["scale_change_pct"],
                                   delta=core.TOL_PCT)
            # the recorded "-7.93 %" slip must NOT reproduce (I7 correction)
            self.assertGreater(abs(s["scale_change_pct"] + 7.93), 1e-3)
            self.assertTrue(MAP[side + "_checks"]["transcription_slip_rejected"])

    def test_endpoints_match_receipt_and_target_pack(self):
        joints = core.target_joints()
        for side, body in (("right", "radius"), ("left", "radius_l")):
            s = MAP[side]
            self.assertLessEqual(np.max(np.abs(np.array(s["P_old_m"])
                                              - np.array(REC08["before"][body]["P"]))),
                                 core.TOL_LANDMARK_M)
            self.assertLessEqual(np.max(np.abs(np.array(s["P_new_m"])
                                              - np.array(REC08["after"][body]["P"]))),
                                 core.TOL_LANDMARK_M)
            self.assertLessEqual(np.max(np.abs(np.array(s["t_new_m"])
                                              - np.array(REC08["after"][body]["t"]))),
                                 core.TOL_LANDMARK_M)
        # the RIGHT edge anchors are the pack elbow/wrist joints (binding)
        self.assertLessEqual(np.linalg.norm(np.array(MAP["right"]["P_old_m"])
                                            - joints["elbow_R"]),
                             core.TOL_LANDMARK_M)
        self.assertLessEqual(np.linalg.norm(np.array(MAP["right"]["P_d_old_m"])
                                            - joints["wrist_R"]),
                             core.TOL_LANDMARK_M)

    def test_structure_L_equals_sG_det_roundtrip(self):
        for side in ("right", "left"):
            s = MAP[side]
            ch = MAP[side + "_checks"]
            self.assertLessEqual(s["L_minus_sG_max"], core.TOL_ORTH)
            self.assertAlmostEqual(s["det_B_src"], 1.0, delta=core.TOL_ORTH)
            self.assertAlmostEqual(s["det_Bp_new"], 1.0, delta=core.TOL_ORTH)
            self.assertLessEqual(s["roundtrip_max"], core.TOL_ROUNDTRIP)
            self.assertTrue(ch["detL_equals_s_cubed"])
            self.assertTrue(ch["detL_receipt"])

    def test_G_unchanged_matches_receipt(self):
        for side, body in (("right", "radius"), ("left", "radius_l")):
            s = MAP[side]
            self.assertLessEqual(s["G_vs_packet_max_abs_diff"], core.TOL_ORTH)
            self.assertAlmostEqual(s["G_vs_packet_max_abs_diff"],
                                   REC08["after"][body]["G_vs_packet_max_abs_diff"],
                                   delta=core.TOL_ORTH)
            self.assertTrue(MAP[side + "_checks"]["G_unchanged"])

    def test_landmark_oracles_and_packet_reproduction(self):
        for side in ("right", "left"):
            s = MAP[side]
            self.assertLessEqual(s["landmark_oracle_after_D_m"],
                                 core.TOL_ROUNDTRIP)
            self.assertLessEqual(s["landmark_oracle_before_D_m"],
                                 core.TOL_ROUNDTRIP)
            self.assertLessEqual(s["packet_reconstruction_max_err_m"],
                                 core.TOL_RECON_M)
            self.assertTrue(MAP[side + "_checks"]["packet_sites_reproduced"])

    def test_site_deltas_reproduce_receipt(self):
        for side, body in (("right", "radius"), ("left", "radius_l")):
            rec = REC08["site_deltas"][body]
            deltas = MAP["site_deltas_" + side + "_m"]
            self.assertEqual(len(deltas), rec["n_sites"])
            self.assertEqual(MAP[side]["worst_site"], rec["worst_site"])
            self.assertLessEqual(abs(MAP[side]["worst_delta_m"]
                                     - rec["max_displacement_m"]), 1e-12)
            for name, d in rec["all"].items():
                self.assertLessEqual(abs(deltas[name] - d), 1e-12, name)

    def test_mechanism_gap_and_refusal(self):
        for side, body in (("right", "radius"), ("left", "radius_l")):
            s = MAP[side]
            self.assertGreater(s["gap_m"], core.JOINT_EPS)
            self.assertAlmostEqual(s["gap_m"],
                                   REC08["mechanism"][body]["gap_m"],
                                   delta=core.TOL_LANDMARK_M)
            self.assertTrue(s["refusal_would_fire"])
        # the closed-form derived distal point matches the forced-closure gap
        self.assertLessEqual(abs(MAP["fractions"]["derived_distal_point_mm"]
                                 / 1000.0 - MAP["right"]["gap_m"]),
                             core.TOL_DERIVED_GAP_M)

    def test_mirror_structural_and_overbroad_prediction_recorded(self):
        self.assertTrue(MAP["mirror_ok"])
        self.assertEqual(MAP["mirror_max_diffs"]["P_new"], 0.0)
        self.assertEqual(MAP["mirror_max_diffs"]["P_d_old"], 0.0)
        self.assertEqual(MAP["mirror_max_diffs"]["s_new"], 0.0)
        # the frozen over-broad mirror prediction (<=1e-9 m for ALL vectors)
        # FAILED for t_new and is RECORDED, never silently re-tuned (FA)
        self.assertGreater(MAP["mirror_max_diffs"]["t_new"], core.TOL_MIRROR_M)
        self.assertLessEqual(MAP["mirror_max_diffs"]["t_new"], 1e-4)
        rec_t_r = REC08["after"]["radius"]["t"]
        rec_t_l = REC08["after"]["radius_l"]["t"]
        rec_asym = float(np.max(np.abs(
            np.array([-rec_t_r[0], rec_t_r[1], rec_t_r[2]]) - np.array(rec_t_l))))
        self.assertLessEqual(abs(MAP["mirror_max_diffs"]["t_new"] - rec_asym),
                             1e-12)
        self.assertIn("P3:mirror_t_overbroad_prediction",
                      RECEIPT["fired_falsifiers"])


class TestP6Coverage(unittest.TestCase):
    def test_scenario_counts_match_receipt(self):
        cov = RECEIPT["coverage_topology"]
        self.assertTrue(cov["ok"])
        self.assertEqual(cov["scenario_counts"]["baseline"], 2)
        self.assertEqual(cov["scenario_counts"]["diagnostic_ulna_only"], 4)
        self.assertEqual(cov["scenario_counts"]["plus_hand"], 14)
        self.assertEqual(cov["receipt_counts"]["baseline"], 2)
        self.assertEqual(cov["receipt_counts"]["diagnostic_ulna_only"], 4)

    def test_newly_defined_and_blockers(self):
        cov = RECEIPT["coverage_topology"]
        self.assertEqual(sorted(cov["newly_defined_diagnostic"]),
                         ["PT_l_tendon", "PT_tendon"])
        self.assertEqual(len(cov["hand_blocked_baseline"]), 10)   # 8 + ECU x2
        self.assertEqual(len(cov["thorax_blocked_baseline"]), 4)  # BIC x4
        self.assertEqual(cov["joint_owner_elbow_flexion"], "ulna")
        self.assertEqual(cov["joint_owner_elbow_flexion_l"], "ulna_l")


class TestP7R1Retention(unittest.TestCase):
    def test_anatomical_refutation_retained(self):
        r1 = RECEIPT["r1_refutation"]
        self.assertEqual(r1["r1_refutation_status"], "RETAINED_FIRED")
        self.assertFalse(r1["anatomical_support"])
        self.assertTrue(r1["falsifier_fired"])
        self.assertTrue(r1["target_outside_primary_band"])
        self.assertTrue(r1["drift_law_consistent"])
        self.assertIn("UNAUTHORIZED", r1["bounds"])

    def test_fractions_reproduce_receipt(self):
        f = MAP["fractions"]
        self.assertTrue(f["ok"])
        self.assertAlmostEqual(f["derived_distal_point_mm"],
                               f["receipt"]["derived_distal_point_mm"],
                               delta=5e-4)
        self.assertAlmostEqual(f["target_per_edge_fraction_pct"],
                               f["receipt"]["target_per_edge_fraction_pct"],
                               delta=1e-6)
        t = f["receipt_truncated_input_reproduction"]
        self.assertTrue(t["derived_matches_receipt"])
        self.assertTrue(t["frac_matches_receipt"])

    def test_outcome_is_honest_discrepancy_recorded(self):
        self.assertEqual(RECEIPT["outcome"], "DISCREPANCY_RECORDED")
        self.assertEqual(RECEIPT["fired_falsifiers"],
                         ["P3:mirror_t_overbroad_prediction"])
        self.assertFalse(RECEIPT["honesty"]["supersession_executed"])
        self.assertFalse(RECEIPT["honesty"]["native_engine_run"])


class TestFalsifierDemos(unittest.TestCase):
    """Adversarial: detectors are exercised in their FIRING configuration."""

    def test_clipped_subject_guard_fires(self):
        """FC failing-first: a deliberately clipped camera must raise."""
        import ota02_render_views as R
        S = R.build_subjects()
        subj = R.declared_subject_points(S, "V3")
        pos, tgt, span = R.fit_camera(subj, subj.mean(0),
                                      core.unit([1.0, 0.0, 0.0]), 320.0,
                                      R.PANEL_W / R.PANEL_H)
        cam = R.cam_sample(pos, tgt, [0, 1, 0])
        R.assert_in_bounds(subj, cam, span, R.PANEL_W, R.PANEL_H)  # passes
        with self.assertRaises(AssertionError):
            R.assert_in_bounds(subj, cam, span * 0.5, R.PANEL_W, R.PANEL_H)
        with self.assertRaises(AssertionError):
            R.assert_in_bounds(subj, cam, span * 0.92, R.PANEL_W, R.PANEL_H)

    def test_tampered_state_hash_is_detected(self):
        """FC failing-first: any state mutation changes the binding hash."""
        raw = (EVIDENCE / "state_snapshot.json").read_bytes()
        good = hashlib.sha256(raw).hexdigest()
        needle = b'"outcome"'
        assert needle in raw
        tampered = hashlib.sha256(raw.replace(needle, b'"outcomeX"')).hexdigest()
        self.assertNotEqual(good, tampered)
        manifest = _manifest()
        self.assertEqual(manifest["subject_sha256"], good)
        self.assertTrue(manifest["render"]["state_hash_preserved_under_view_toggles"])
        self.assertEqual(manifest["render"]["state_hash_before_render"],
                         manifest["render"]["state_hash_after_render"])

    def test_tampered_after_scale_fails_exact_reproduction(self):
        """FA failing-first: an edited receipt value cannot pass the check."""
        rec = json.loads(json.dumps(REC08))
        rec["after"]["radius"]["scale"] = 0.2042  # a plausible-looking tamper
        s = MAP["right"]
        self.assertGreater(abs(s["s_new"] - rec["after"]["radius"]["scale"]),
                           core.TOL_SCALE_REL)

    def test_visual_manifest_structurally_valid(self):
        sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")
        from visual_capture import validate_manifest
        import ota02_render_views as R
        structural = validate_manifest(_manifest(),
                                       json.loads((EVIDENCE /
                                                   "capture_context.json")
                                                  .read_text()), R.PROFILE)
        self.assertTrue(structural["structurally_valid"])

    def test_camera_required_fields_present(self):
        required = ["frame_id", "coordinate_unit", "position", "target",
                    "distance_to_target", "orientation_convention_and_values",
                    "projection", "vertical_fov_or_orthographic_span",
                    "near_far_planes", "aspect_ratio", "viewport_resolution",
                    "camera_motion_or_bookmark_sequence", "state_or_tick_interval"]
        for row in _manifest()["views"]:
            cam = row["camera"]
            for key in required:
                self.assertIn(key, cam, (row["pair_id"], row["mode"], key))
            # the card's visibility/label/occlusion camera fields are carried
            # by the visibility block (pair-identical camera dicts are the
            # canonical validator's contract)
            vis = row["visibility"]
            for key in ("layers", "label_ids", "occlusion_mode"):
                self.assertIn(key, vis, (row["pair_id"], row["mode"], key))

    def test_declared_subjects_in_bounds_in_published_capture(self):
        import ota02_render_views as R
        manifest = _manifest()
        S = R.build_subjects()
        sys.path.insert(0, str(core.REFERENCE))
        from mesh_target_o1 import MonkeyTarget
        mtk = MonkeyTarget(birth_path=str(core.INPUT_BIRTH),
                           pack_path=str(core.INPUT_PACK))
        S["_mesh_V"], S["_mesh_F"] = mtk.V, mtk.F
        cams = {r["pair_id"]: r["camera"] for r in manifest["views"]}
        for pair in ("V1", "V2", "V3"):
            subj = R.declared_subject_points(S, pair)
            if pair == "V2":
                subj = subj / 1000.0  # renderer frames V2 in metres
            cam = cams[pair]
            R.assert_in_bounds(subj, cam["samples"][0],
                               cam["orthographic_span"],
                               R.PANEL_W, R.PANEL_H)

    def test_capture_pixels_present_and_hash_bound(self):
        png = EVIDENCE / "capture_sheet.png"
        manifest = _manifest()
        raw = png.read_bytes()
        self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         manifest["capture_sha256"])
        # non-blank: the sheet must contain non-white render content
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.image as mpimg
        import ota02_render_views as R
        img = mpimg.imread(png)
        self.assertEqual(img.shape[0], R.SHEET_H)
        self.assertEqual(img.shape[1], R.SHEET_W)
        self.assertLess(float(img[..., :3].min()), 0.98)


if __name__ == "__main__":
    unittest.main()
