"""test_focus_policy_probe.py -- unittest suite for the ONT-U03 candidate.

Runs the pinned-subject laws on reduced workloads (the FULL frozen
measurements live in focus_policy_probe.py: 5000 schedules, the complete
scripted timeline, the expiry-floor sub-probe, the release_all consistency
run and the gate-validated capture). CPU-only, headless.

    python -B -m unittest test_focus_policy_probe -v
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMPAIGN_TOOLS = Path("E:/PythonChimera/tools/monkey_campaign")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = load("ont_u03_probe", HERE / "focus_policy_probe.py")
capture = load("ont_u03_capture", HERE / "capture_build.py")

sys.path.insert(0, str(CAMPAIGN_TOOLS))
sys.dont_write_bytecode = True
import visual_capture                                        # noqa: E402


class PinnedLineage(unittest.TestCase):
    def test_pinned_hashes_hold(self):
        # raises SystemExit on any drift
        probe.assert_pins()

    def test_subject_is_the_u03_policy(self):
        self.assertEqual(probe.SUBJECT_SHA256,
                         "e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30"
                         "a73ee8ef0f9d0")

    def test_mapper_is_the_qualified_u01_mapper(self):
        self.assertEqual(probe.MAPPER_SHA256,
                         "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720"
                         "ac970b42cfe6b44")


class ScriptedRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scripted = probe.run_scripted()

    def test_grid_records_and_bounds(self):
        rows = self.scripted["rows"]
        self.assertEqual(len(rows), 69)
        for r in rows:
            self.assertLessEqual(r["emitted"], 1)
            self.assertTrue(r["policy_state"] in
                            ("focused", "blurred", "disconnected"))
            for rec in r["records"]:
                self.assertEqual(rec["issued_tick"],
                                 (r["t_ms"] * 300) // 1000)
                self.assertGreaterEqual(rec["v_forward"], 0.0)
                self.assertLessEqual(rec["v_forward"], 0.763625)
                self.assertLessEqual(abs(rec["yaw_rate"]), 1.6)

    def test_blur_clears_and_decay_lands_zero(self):
        rows = self.scripted["rows"]
        by_t = {r["t_ms"]: r for r in rows}
        self.assertEqual(by_t[1600]["held"], [])
        self.assertEqual(by_t[1600]["policy_state"], "blurred")
        self.assertEqual([r["v_forward"] for r in by_t[1600]["records"]],
                         [0.763625])
        self.assertEqual([r["v_forward"] for r in by_t[1650]["records"]],
                         [0.0])
        for r in rows:
            if 1700 <= r["t_ms"] < 1900:
                self.assertEqual(r["emitted"], 0)

    def test_press_and_mouse_dropped_while_blurred(self):
        rows = self.scripted["rows"]
        by_t = {r["t_ms"]: r for r in rows}
        drops = by_t[1700]["policy_trace"].get("dropped_blurred", [])
        self.assertEqual(len(drops), 2)
        self.assertEqual(by_t[1700]["emitted"], 0)
        self.assertEqual(by_t[1700]["held"], [])

    def test_disconnect_dominates_and_drops_named(self):
        rows = self.scripted["rows"]
        by_t = {r["t_ms"]: r for r in rows}
        self.assertEqual(by_t[2550]["policy_state"], "disconnected")
        self.assertEqual(by_t[2650]["policy_state"], "disconnected")
        drops = by_t[2650]["policy_trace"].get("dropped_disconnected", [])
        self.assertTrue(drops and drops[0][0] == "S")
        self.assertEqual(by_t[2700]["policy_state"], "focused")

    def test_recovery_rearm_empty_and_fresh_grid(self):
        rows = self.scripted["rows"]
        by_t = {r["t_ms"]: r for r in rows}
        rearm = by_t[1800]["policy_trace"].get("rearmed", [])
        self.assertTrue(rearm and rearm[0][2] == [])
        self.assertEqual([r["v_forward"] for r in by_t[1900]["records"]],
                         [0.763625])

    def test_camera_only_window_silent_and_still(self):
        rows = [r for r in self.scripted["rows"]
                if 3100 <= r["t_ms"] <= 3400]
        self.assertTrue(rows)
        self.assertEqual(sum(r["emitted"] for r in rows), 0)
        self.assertEqual(sum(len(r["events_this_tick"]) for r in rows), 0)
        b0 = rows[0]["body"]
        self.assertTrue(all(r["body"] == b0 for r in rows))

    def test_body_is_the_delivered_record_integral(self):
        replay = probe.replay_body(self.scripted["sink"].records)
        for r in self.scripted["rows"]:
            if r["t_ms"] in replay:
                rx, rz = replay[r["t_ms"]]
                self.assertEqual((rx, rz),
                                 (r["body"][0], r["body"][2]))

    def test_obstruction_ray_blocked_every_tick(self):
        for r in self.scripted["rows"]:
            self.assertTrue(r["cam_obstructed"]["ray_blocked"])
            self.assertGreaterEqual(r["cam_obstructed"]["distance_to_target"],
                                    1.5)
            self.assertLessEqual(r["cam_obstructed"]["distance_to_target"],
                                 3.0)


class ReducedFuzz(unittest.TestCase):
    def test_bounds_and_no_stuck(self):
        out = probe.run_fuzz(schedules=25, seed=20260926)
        self.assertEqual(out["violations"], [])
        self.assertEqual(out["non_emit_sink_calls"], 0)
        self.assertGreater(out["records_checked"], 0)


class ExpiryFloor(unittest.TestCase):
    def test_stalled_clock_drops_named_healthy_clock_drops_none(self):
        out = probe.run_expiry_floor()
        self.assertEqual(out["delivered_at"], [1000, 1050, 1100])
        self.assertEqual(out["delivery_ages_physics_ticks"], [0, 15, 30])
        self.assertEqual(len(out["drops_named"]), 3)
        self.assertEqual(out["gate_stats"]["expired_at_gate"], 3)
        self.assertEqual(out["healthy_clock_expired_at_gate"], 0)
        self.assertTrue(all(out["frozen_number_identity"].values()))
        self.assertEqual(out["duplicated_frozen_literals"], [])

    def test_expired_strictly_after_two_intervals(self):
        rec = probe.CommandRecord(v_forward=0.5, yaw_rate=0.0,
                                  issued_tick=(1000 * 300) // 1000)
        self.assertFalse(probe.InputMapper.is_expired(rec, 1000))
        self.assertFalse(probe.InputMapper.is_expired(rec, 1095))
        self.assertTrue(probe.InputMapper.is_expired(rec, 1105))


class ConsistencyWithU01(unittest.TestCase):
    def test_blur_stream_is_release_all_byte_identical(self):
        out = probe.run_consistency()
        self.assertTrue(out["streams_byte_identical"])
        self.assertTrue(out["source_is_u01_mapper"])
        self.assertEqual(out["policy_source_ids"], ["u01_input_mapper"])


class ManifestStructure(unittest.TestCase):
    @staticmethod
    def _mini_manifest():
        rows = probe.run_scripted()["rows"][:3]
        trace_sha = "a" * 64
        cam_specs = [
            ("normal follow-camera distance", "cam_follow",
             capture.camera_block("sampled_trajectory",
                                  [capture.sample_from(r["cam_follow"], i)
                                   for i, r in enumerate(rows)],
                                  interpolation="recorded_each_tick")),
            ("obstructed and close-target views", "cam_obstructed",
             capture.camera_block("sampled_trajectory",
                                  [capture.sample_from(r["cam_obstructed"], i)
                                   for i, r in enumerate(rows)],
                                  interpolation="recorded_each_tick")),
            ("repeatable inspection side view", "cam_side",
             capture.camera_block("fixed_bookmark",
                                  [capture.sample_from(rows[0]["cam_side"], i)
                                   for i in range(3)])),
        ]
        views = []
        for view_id, key, block in cam_specs:
            for mode in ("diagnostic", "clean"):
                diag = mode == "diagnostic"
                views.append({
                    "view_id": view_id, "mode": mode, "pair_id": key,
                    "state_binding": {"kind": "trace", "sha256": trace_sha},
                    "artifact_locator": {"kind": "video",
                                         "seconds": [0.0, 0.15]},
                    "camera": block,
                    "visibility": {
                        "layers": list(capture.LAYERS) if diag else [],
                        "label_ids": [l for l, _ in capture.LABELS]
                                     if diag else [],
                        "selected_ids": ["player_anchor"] if diag else [],
                        "required_subject_ids": ["player_anchor"],
                        "observed_subject_ids": ["player_anchor",
                                                 "ground_grid"],
                        "missing_subject_ids": [],
                        "occlusion_mode": "depth_tested",
                        "tag_bindings": [{"label_id": l, "subject_id": s}
                                         for l, s in capture.LABELS]
                                        if diag else []}})
        manifest = {"schema": "chimera.visual_capture_manifest.v1",
                    "task_id": "U03", "run_id": "mini",
                    "subject_sha256": probe.SUBJECT_SHA256,
                    "capture_sha256": "b" * 64,
                    "profile_id": "controls",
                    "tick_interval": [0, 2], "views": views}
        context = {"task_id": "U03", "run_id": "mini",
                   "subject_sha256": probe.SUBJECT_SHA256,
                   "capture_sha256": "b" * 64, "tick_interval": [0, 2]}
        return manifest, context

    def test_mini_manifest_validates(self):
        manifest, context = self._mini_manifest()
        card = json.loads((HERE / "card_task.json").read_text(
            encoding="utf-8"))
        result = visual_capture.validate_manifest(
            manifest, context, card["task"]["verification_profile"])
        self.assertTrue(result["structurally_valid"])
        self.assertEqual(result["profile_id"], "controls")
        # a clean row carrying diagnostics must be REFUSED
        manifest["views"][1]["visibility"]["layers"] = list(capture.LAYERS)
        with self.assertRaises(ValueError):
            visual_capture.validate_manifest(
                manifest, context,
                card["task"]["verification_profile"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
