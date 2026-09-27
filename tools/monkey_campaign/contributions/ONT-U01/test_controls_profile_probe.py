"""test_controls_profile_probe.py -- unittest suite for the ONT-U01 candidate.

Runs the pinned-subject laws on reduced workloads (the FULL frozen
measurements live in controls_profile_probe.py: 5000 schedules, the complete
scripted timeline and the gate-validated capture). CPU-only, headless.

    python -B -m unittest test_controls_profile_probe -v
"""
from __future__ import annotations

import importlib.util
import json
import math
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


probe = load("ont_u01_probe", HERE / "controls_profile_probe.py")
capture = load("ont_u01_capture", HERE / "capture_build.py")
sys.path.insert(0, str(CAMPAIGN_TOOLS))
sys.dont_write_bytecode = True
import visual_capture                                        # noqa: E402


class PinnedLineage(unittest.TestCase):
    def test_pinned_hashes_hold(self):
        # raises SystemExit on any drift
        probe.assert_pins()

    def test_subject_is_the_u01_mapper(self):
        self.assertEqual(probe.SUBJECT_SHA256,
                         "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720"
                         "ac970b42cfe6b44")


class ScriptedRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scripted = probe.run_scripted()

    def test_grid_and_records(self):
        rows = self.scripted["rows"]
        self.assertEqual(len(rows), 61)
        for r in rows:
            self.assertLessEqual(r["emitted"], 1)
            for rec in r["records"]:
                self.assertEqual(rec["issued_tick"],
                                 (r["t_ms"] * 300) // 1000)
                self.assertGreaterEqual(rec["v_forward"], 0.0)
                self.assertLessEqual(rec["v_forward"], 0.763625)
                self.assertLessEqual(abs(rec["yaw_rate"]), 1.6)

    def test_camera_only_window_silent_and_still(self):
        rows = [r for r in self.scripted["rows"] if 1500 <= r["t_ms"] <= 1800]
        self.assertTrue(rows)
        self.assertEqual(sum(r["emitted"] for r in rows), 0)
        self.assertEqual(sum(len(r["events_this_tick"]) for r in rows), 0)
        b0 = rows[0]["body"]
        self.assertTrue(all(r["body"] == b0 for r in rows))

    def test_body_is_the_record_integral(self):
        replay, _ = probe.replay_body(self.scripted["sink"].records)
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
    def test_bounds_and_no_teleport(self):
        out = probe.run_fuzz(schedules=25, seed=20260926)
        self.assertEqual(out["violations"], [])
        self.assertEqual(out["non_emit_sink_calls"], 0)
        self.assertGreater(out["records_checked"], 0)


class StallAndCadence(unittest.TestCase):
    def test_stall_one_record_no_burst(self):
        out = probe.run_stall_and_cadence()
        self.assertEqual(out["stall_records_at_press"], 1)
        self.assertEqual(out["stall_records_at_1500"], 1)
        self.assertEqual(out["reanchor_records_at_1550"], 1)
        self.assertEqual(out["dense_diffs"], [50])
        self.assertGreaterEqual(out["dense_records"], 10)


class RemapIsData(unittest.TestCase):
    def test_remap_values_and_projection_identical(self):
        out = probe.run_remap()
        self.assertTrue(out["same_values"])
        self.assertTrue(out["same_type_version"])
        self.assertTrue(out["same_constants"])
        self.assertTrue(out["projection_bits_equal"])
        self.assertTrue(out["imports_only_seam"])


class ExpiryContract(unittest.TestCase):
    def test_expired_strictly_after_two_intervals(self):
        rec = probe.CommandRecord(v_forward=0.5, yaw_rate=0.0,
                                  issued_tick=(1000 * 300) // 1000)
        self.assertFalse(probe.InputMapper.is_expired(rec, 1000))
        self.assertFalse(probe.InputMapper.is_expired(rec, 1095))
        self.assertTrue(probe.InputMapper.is_expired(rec, 1105))


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
                    "task_id": "U01", "run_id": "mini",
                    "subject_sha256": probe.SUBJECT_SHA256,
                    "capture_sha256": "b" * 64,
                    "profile_id": "controls",
                    "tick_interval": [0, 2], "views": views}
        context = {"task_id": "U01", "run_id": "mini",
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
            visual_capture.validate_manifest(manifest, context,
                                             card["task"]["verification_profile"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
