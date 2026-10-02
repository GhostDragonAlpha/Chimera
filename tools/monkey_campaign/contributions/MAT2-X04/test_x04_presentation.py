#!/usr/bin/env python3
"""MAT2-X04: the NAMED-CHECK suite (the falsifier arms at the unit level)
in the gate-visible test_*.py form (card-kit law).

Fast, analytic where possible; the certified-line machinery is exercised
through the SAME byte-verified extraction the driver uses. Every check is
named; skipped tests are NOT allowed (no KNOWN_SKIPS exists for this card).

Run:  python -B -m unittest test_x04_presentation -v
(or through run_checks.py, which writes checks_receipt.json)
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

vi4 = ch = sr = vzmod = f04 = geom = None


def setUpModule():
    global vi4, ch, sr, vzmod, f04, geom
    import verify_inputs_x04 as _vi4
    import presentation_harness as _ch
    import state_readout as _sr
    vi4, ch, sr = _vi4, _ch, _sr
    vi4.verify()
    vi4.verify_registry()
    vi4.verify_prereg_commit()
    vi4.extract_x04_tree()
    vi4.w10_layer()
    vzmod = vi4.load_pinned_module(
        "x04_visualization_checks",
        ("tools", "monkey_campaign", "contributions", "MAT2-W10",
         "visualization.py"))
    f04 = vzmod.load_f04_module()
    geom = vzmod.gait_geometry()


def synthetic_row(tick=4400, phase=0.31):
    return {"tick": tick, "com_v_m_s": 0.42, "com_x_m": 1.7,
            "phase_left": phase, "phase_right": (phase + 0.5) % 1.0,
            "yaw_rate_rad_s": 0.0, "contact_count": 5,
            "foot_contacts": [1.0, 1.0, 1.0, 1.0, 1.0, 0.0],
            "foot_forces": [0.25, 0.25, 0.25, 0.25, 0.2, 0.0],
            "pad_gaps": {"hl": [0.0, 0.0], "hr": [0.02, 0.02]},
            "applied_cmd": [0.0] * 8, "saturation": [0.0] * 8,
            "trip_l": 0, "trip_r": 0, "state_sha256": "synthetic" * 8}


class GlyphLawChecks(unittest.TestCase):
    """The declared font's measured-geometry law (P9's instrument)."""

    def test_expected_metrics(self):
        m = sr.expected_text_metrics("LINK L5/5 R5/5")
        self.assertEqual(m["height_px"], 10)
        self.assertEqual(m["width_px"], (14 * 4 - 1) * 2)
        self.assertEqual(m["pixel_count"],
                         sum(sr.GLYPH_ON_COUNT[c] for c in "LINK L5/5 R5/5")
                         * 4)

    def test_drawn_bbox_equals_expected(self):
        buf = [[(0, 0, 0) for _ in range(400)] for _ in range(40)]
        text = "CT L1 R0 0.25N 0.00N"
        sr.draw_text(buf, text, 10, 10, 2, sr.L1_TEXT)
        arr = np.asarray(buf, dtype=np.uint8)
        mask = np.all(arr == np.array(sr.L1_TEXT, dtype=np.uint8), axis=2)
        ys, xs = np.nonzero(mask)
        m = sr.expected_text_metrics(text)
        self.assertEqual([int(xs.min()), int(ys.min()),
                          int(xs.max()), int(ys.max())],
                         [10, 10, 10 + m["width_px"] - 1,
                          10 + m["height_px"] - 1])
        self.assertEqual(int(mask.sum()), m["pixel_count"])

    def test_glyph_coverage_complete(self):
        needed = set("LINKCTRMBONEWALK+-/:. 0123456789V")
        self.assertTrue(needed <= set(sr._GLYPHS),
                        "x04_glyph_missing:" + str(needed - set(sr._GLYPHS)))


class PaletteLawChecks(unittest.TestCase):
    """X04 layer palettes are disjoint from every W10 render color."""

    def test_palettes_disjoint_from_w10_colors(self):
        w10_colors = {(168, 198, 150), (120, 80, 60), (200, 60, 50),
                      (60, 90, 200), (180, 30, 30), (20, 20, 20),
                      (30, 90, 200), (210, 210, 210), (0, 255, 0),
                      (255, 140, 0)}
        mine = set(sr.ALL_PALETTES)
        self.assertFalse(mine & w10_colors,
                         "x04_palette_collision:" + str(mine & w10_colors))


class SchemaAuditChecks(unittest.TestCase):
    """The climb schema audit over the pinned scene bytes (P3)."""

    def _source(self):
        return ch.scene_source_bytes()

    def test_clean_schema_derives_absent(self):
        got = sr.derive_climb_state(self._source())
        self.assertEqual(got["climb_state"], sr.CLIMB_ABSENT)
        self.assertEqual(got["climb_keys"], [])
        self.assertGreater(got["observation_key_count"], 10)

    def test_injected_climb_key_flips(self):
        src = self._source().decode("utf-8")
        marker = '            "pad_pair_ordering": {"hl": "heel_mp", "hr": "heel_mp"},'
        self.assertEqual(src.count(marker), 1)
        tampered = src.replace(
            marker, marker + '\n            "climb_state_probe": 0,')
        got = sr.derive_climb_state(tampered.encode("utf-8"))
        self.assertEqual(got["climb_state"], "schema_climb_key_present")
        self.assertEqual(got["climb_keys"], ["climb_state_probe"])


class ChainAuditChecks(unittest.TestCase):
    """The material-mapping law at the unit level (P5/FB2/FB5)."""

    def test_audit_bitwise_zero_on_pinned_law(self):
        row = synthetic_row()
        pose = vzmod.pose_at(row, geom, 0.0, (row["com_x_m"], 0.0))
        audit = sr.audit_chain(pose, vzmod, geom, row)
        for side in ("left", "right"):
            self.assertEqual(audit[side]["max_deviation_m"], 0.0)
            self.assertEqual(audit[side]["connected_sites"], 5)
            self.assertEqual(audit[side]["sites"], 5)

    def test_audit_refuses_canned_pose(self):
        row = synthetic_row()
        canned = {"legs": {"left": {"hip": (0.0, 0.5), "knee": (0.1, 0.45),
                                    "ankle": (0.2, 0.4), "mp": (0.3, 0.35),
                                    "heel": (0.05, 0.35)},
                           "right": {"hip": (0.04, 0.5), "knee": (0.14, 0.45),
                                     "ankle": (0.24, 0.4), "mp": (0.34, 0.35),
                                     "heel": (0.09, 0.35)}}}
        audit = sr.audit_chain(canned, vzmod, geom, row)
        worst = max(audit[s]["max_deviation_m"] for s in ("left", "right"))
        self.assertGreater(worst, 0.0)

    def test_audit_refuses_stale_row(self):
        a, b = synthetic_row(phase=0.31), synthetic_row(phase=0.62)
        self.assertNotEqual(a["phase_left"], b["phase_left"])
        pose_a = vzmod.pose_at(a, geom, 0.0, (a["com_x_m"], 0.0))
        stale = sr.audit_chain(pose_a, vzmod, geom, b)
        fresh = sr.audit_chain(pose_a, vzmod, geom, a)
        self.assertGreater(max(stale[s]["max_deviation_m"]
                               for s in ("left", "right")), 0.0)
        self.assertEqual(max(fresh[s]["max_deviation_m"]
                             for s in ("left", "right")), 0.0)


class BindingAuditChecks(unittest.TestCase):
    """The FB1 refusal law: receipts bind their row; placeholders refuse."""

    def test_binding_audit_passes_on_derived_receipt(self):
        climb = sr.derive_climb_state(ch.scene_source_bytes())
        row = synthetic_row()
        state = sr.derive_state(row, None, climb, vzmod, geom)
        buf = [[(0, 0, 0) for _ in range(960)] for _ in range(540)]
        receipt = sr.draw_layers(buf, state)
        got = sr.binding_audit(receipt, row, None, climb, vzmod, geom)
        self.assertTrue(got["ok"])

    def test_binding_audit_refuses_placeholder(self):
        climb = sr.derive_climb_state(ch.scene_source_bytes())
        row = synthetic_row()          # contact_r = 0, force 0.0
        state = sr.derive_state(row, None, climb, vzmod, geom)
        buf = [[(0, 0, 0) for _ in range(960)] for _ in range(540)]
        receipt = sr.draw_layers(buf, state)
        fake = dict(receipt)
        fake["state"] = dict(receipt["state"])
        fake["state"]["contact_r"] = 1          # a placeholder override
        fake["state"]["force_r_n"] = 0.25
        with self.assertRaises(sr.Refusal) as cm:
            sr.binding_audit(fake, row, None, climb, vzmod, geom)
        self.assertTrue(str(cm.exception).startswith("x04_state_binding"))


class CleanProbeChecks(unittest.TestCase):
    """P7's instrument: zero layer pixels on clean frames; a planted pixel
    is caught."""

    def test_planted_pixel_is_caught(self):
        buf = np.zeros((540, 960, 3), dtype=np.uint8)
        probe = sr.probe_clean_frame(buf)
        self.assertTrue(probe["clean_ok"])
        buf[sr.L1_RECT[1] + 1, sr.L1_RECT[0] + 1] = sr.L1_TEXT
        probe2 = sr.probe_clean_frame(buf)
        self.assertFalse(probe2["clean_ok"])
        self.assertEqual(probe2["layer_pixels_total"], 1)


class CertifiedLineConstantChecks(unittest.TestCase):
    """The pinned certified-line constants this card's window rides."""

    def test_scene_cycle_ticks(self):
        from tools.policy_compat import scene_cpu as SC
        self.assertEqual(SC.CYCLE_TICKS, ch.CYCLE_TICKS)
        self.assertEqual(ch.PW0, 20 * ch.CYCLE_TICKS)
        self.assertEqual(ch.PW1 - ch.PW0, 2 * ch.CYCLE_TICKS)

    def test_seam_constants_unchanged(self):
        from tools.monkey_campaign.product.input_mapper import (  # pinned
            INTERVAL_MS, EXPIRY_TICKS)
        self.assertEqual(INTERVAL_MS, 50)
        self.assertEqual(EXPIRY_TICKS, 30)

    def test_horizon_is_w10_r1(self):
        import command_model as cm
        self.assertEqual(ch.HORIZON_A1, cm.HORIZON)
        self.assertEqual(ch.SEED, 20260920)


class CameraFieldChecks(unittest.TestCase):
    """The profile's 15 camera_required_fields ride every camera record."""

    def test_camera_record_carries_profile_fields(self):
        reg = vi4.verify_registry()
        profile = reg["profile"]
        view = ch.X04_VIEWS["V1_normal_player_camera"]
        cam = f04.Camera({"position": list(view["position"]),
                          "target": list(view["target"]),
                          "vfov_deg": view["vfov_deg"],
                          "near_far": list(view["near_far"])})
        import run_capture_x04 as rc
        rec = rc.camera_view_record(cam, view, [1, 2], [], "fid", [1, 2])
        rec["sample_mode"] = "fixed_bookmark"
        rec["samples"] = [{"tick": 1, "position": list(view["position"]),
                           "target": list(view["target"]),
                           "distance_to_target": cam.distance_to_target,
                           "orientation": list(cam.quaternion_wxyz())},
                          {"tick": 2, "position": list(view["position"]),
                           "target": list(view["target"]),
                           "distance_to_target": cam.distance_to_target,
                           "orientation": list(cam.quaternion_wxyz())}]
        missing = [f for f in profile["camera_required_fields"]
                   if f not in rec]
        self.assertEqual(missing, [])
        # G7: the profile is CONSUMED live (mode=ro), never hand-copied; the
        # operative law is "ALL the profile's camera_required_fields". The
        # registry currently declares 16 (the frozen prereg text recorded 15
        # at freeze) — the live count is what binds, and the drift is
        # disclosed in the receipt/report, never silently reconciled.
        self.assertEqual(len(profile["camera_required_fields"]), 16)


class ValidatorLawChecks(unittest.TestCase):
    """The pinned validator's own laws, re-proven on minimal fixtures."""

    def _manifest(self, clean_labels=False):
        profile = vi4.verify_registry()["profile"]
        cam = {"frame_id": "f", "coordinate_unit": "m", "handedness": "right",
               "orientation_convention": "quaternion_wxyz_camera_to_frame",
               "forward_axis": "-Z", "up_axis": "+Y",
               "near_far_planes": [0.05, 50.0], "viewport_resolution": [960, 540],
               "aspect_ratio": 960 / 540, "projection": "perspective",
               "vertical_fov_degrees": 50.0, "sample_mode": "fixed_bookmark",
               "samples": [{"tick": 1, "position": [1.0, 2.0, 3.0],
                            "target": [0.0, 0.5, 0.0],
                            "distance_to_target": 3.5,
                            "orientation": [0.0, 0.0, 0.0, 1.0]},
                           {"tick": 2, "position": [1.0, 2.0, 3.0],
                            "target": [0.0, 0.5, 0.0],
                            "distance_to_target": 3.5,
                            "orientation": [0.0, 0.0, 0.0, 1.0]}]}
        layers = list(profile["diagnostic_layers"])
        labels = ["state_link_label"]
        vis_clean = {"layers": [], "label_ids": [],
                     "selected_ids": [], "required_subject_ids": ["m"],
                     "observed_subject_ids": ["m"], "missing_subject_ids": [],
                     "occlusion_mode": "depth_tested", "tag_bindings": []}
        vis_diag = {"layers": layers, "label_ids": labels,
                    "selected_ids": labels, "required_subject_ids": ["m"],
                    "observed_subject_ids": ["m", "state_link_label_subject"],
                    "missing_subject_ids": [],
                    "occlusion_mode": "depth_tested",
                    "tag_bindings": [{"label_id": labels[0],
                                      "subject_id":
                                      "state_link_label_subject"}]}
        rows = []
        for view in profile["views"]:
            row = {"view_id": view, "mode": "diagnostic", "pair_id": view,
                   "state_binding": {"kind": "trace", "sha256": "0" * 64},
                   "artifact_locator": {"kind": "video", "seconds": [0, 1]},
                   "camera": cam, "visibility": vis_diag}
            clean_row = dict(row)
            clean_row["mode"] = "clean"
            clean_row["visibility"] = dict(vis_clean)
            if clean_labels:
                clean_row["visibility"]["label_ids"] = list(labels)
                clean_row["visibility"]["layers"] = list(layers)
                # the binding-identity law precedes the clean law inside the
                # pinned validator; the fixture must violate ONLY the clean
                # law (labels/layers/bindings on a clean row), so the
                # bindings stay consistent with the label ids here.
                clean_row["visibility"]["tag_bindings"] = [
                    {"label_id": labels[0],
                     "subject_id": "state_link_label_subject"}]
            rows.extend([row, clean_row])
        manifest = {"schema": "chimera.visual_capture_manifest.v1",
                    "task_id": "X04", "run_id": "r",
                    "subject_sha256": "1" * 64, "capture_sha256": "2" * 64,
                    "profile_id": profile["id"],
                    "tick_interval": [1, 2], "views": rows}
        context = {"task_id": "X04", "run_id": "r",
                   "subject_sha256": "1" * 64, "capture_sha256": "2" * 64,
                   "tick_interval": [1, 2]}
        return manifest, context, profile

    def test_validator_accepts_conforming_pairs(self):
        vc = vi4.load_pinned_module(
            "visual_capture_checks",
            ("tools", "monkey_campaign", "visual_capture.py"))
        verdict = vc.validate_manifest(*self._manifest())
        self.assertTrue(verdict["structurally_valid"])
        self.assertFalse(verdict["visual_acceptance"])

    def test_validator_refuses_clean_with_diagnostics(self):
        vc = vi4.load_pinned_module(
            "visual_capture_checks2",
            ("tools", "monkey_campaign", "visual_capture.py"))
        with self.assertRaises(ValueError) as cm:
            vc.validate_manifest(*self._manifest(clean_labels=True))
        self.assertIn("clean_view_contains_diagnostics", str(cm.exception))


class DerivationChecks(unittest.TestCase):
    """The label-derivation law: transitions change labels; modes derive."""

    def test_transition_changes_labels(self):
        climb = sr.derive_climb_state(ch.scene_source_bytes())
        a = synthetic_row(phase=0.0)
        b = synthetic_row(phase=0.5)
        b["foot_contacts"] = [1.0, 1.0, 1.0, 1.0, 0.0, 1.0]
        b["foot_forces"] = [0.25, 0.25, 0.25, 0.25, 0.0, 0.2]
        sa = sr.derive_state(a, None, climb, vzmod, geom)
        sb = sr.derive_state(b, a, climb, vzmod, geom)
        self.assertNotEqual(sr.label_lines(sa), sr.label_lines(sb))
        self.assertEqual(sb["event"], "CON L-")
        self.assertEqual(sb["contact_l"], 0)

    def test_event_law(self):
        climb = sr.derive_climb_state(ch.scene_source_bytes())
        a = synthetic_row()
        b = synthetic_row()
        b["foot_contacts"] = [1.0, 1.0, 1.0, 1.0, 0.0, 1.0]
        sb = sr.derive_state(b, a, climb, vzmod, geom)
        self.assertEqual(sb["event"], "CON L-")
        c = synthetic_row()
        c["foot_contacts"] = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        sc = sr.derive_state(c, b, climb, vzmod, geom)
        self.assertEqual(sc["event"], "CON L+")


if __name__ == "__main__":
    unittest.main()
