"""Tests for the ONT-U02 camera-profile probe candidate.

Run: python -B -m unittest test_camera_profile_probe -v   (from this dir)
CPU-only; no engine, no GPU, no network; the pinned reference bytes are
hash-asserted (import of camera_profile_probe already enforces this).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import camera_profile_probe as P  # noqa: E402  (hash-asserts the references)


class TestPinnedReference(unittest.TestCase):
    def test_reference_bytes_match_pinned_hashes(self):
        for rel, want in P.PINNED_SHA.items():
            got = hashlib.sha256(
                (P.REFERENCE / rel).read_bytes()).hexdigest()
            self.assertEqual(got, want, rel)

    def test_constants_derived_from_pinned_formulas(self):
        # bind() laws recomputed independently, to the printed prereg values
        self.assertAlmostEqual(P.R_GROUND, 2.534924255014732, places=9)
        self.assertAlmostEqual(P.PHI_GROUND, 0.2563528611136915, places=9)
        self.assertAlmostEqual(
            P.TRUNK_ENTER,
            P.R_GROUND * math.cos(P.PHI_GROUND) + P.TRUNK.r, places=12)
        self.assertAlmostEqual(P.TRUNK_ENTER, 2.952086, places=5)


class TestDeterminism(unittest.TestCase):
    def test_trace_bytes_identical_across_runs(self):
        r1 = P.run_continuous()
        r2 = P.run_continuous()
        b1 = "".join(json.dumps(r, sort_keys=True) + "\n"
                     for r in r1["rows"]).encode("utf-8")
        b2 = "".join(json.dumps(r, sort_keys=True) + "\n"
                     for r in r2["rows"]).encode("utf-8")
        self.assertEqual(hashlib.sha256(b1).hexdigest(),
                         hashlib.sha256(b2).hexdigest())


class TestCameraMathLaws(unittest.TestCase):
    def test_quaternions_unit_and_forward_aligned(self):
        run = P.run_continuous()
        for row in run["rows"][::40]:
            for which in ("subject", "baseline", "inspection"):
                src = row[which]
                q = src["orientation"]
                self.assertAlmostEqual(math.hypot(*q), 1.0, places=12)
                eye = tuple(src["position"])
                tgt = tuple(src["target"])
                f = [tgt[i] - eye[i] for i in range(3)]
                n = math.sqrt(sum(c * c for c in f))
                f = [c / n for c in f]
                # rotate the camera-local +Z by q (camera->frame):
                # v' = v + w*t + qv x t  with  t = 2 * qv x v   (unit q)
                w, x, y, z = q
                v = (0.0, 0.0, 1.0)
                qv = (x, y, z)
                t = (2.0 * (qv[1] * v[2] - qv[2] * v[1]),
                     2.0 * (qv[2] * v[0] - qv[0] * v[2]),
                     2.0 * (qv[0] * v[1] - qv[1] * v[0]))
                cross_qv_t = (qv[1] * t[2] - qv[2] * t[1],
                              qv[2] * t[0] - qv[0] * t[2],
                              qv[0] * t[1] - qv[1] * t[0])
                rotated = tuple(v[i] + w * t[i] + cross_qv_t[i]
                                for i in range(3))
                dot = sum(rotated[i] * f[i] for i in range(3))
                self.assertGreater(dot, 1.0 - 1e-9,
                                   (row["tick"], which))

    def test_distance_field_matches_positions(self):
        run = P.run_continuous()
        for row in run["rows"][::40]:
            for which in ("subject", "baseline", "inspection"):
                src = row[which]
                self.assertAlmostEqual(
                    src["distance_to_target"],
                    math.dist(src["position"], src["target"]),
                    places=9)


class TestNeverMovesTheAnimal(unittest.TestCase):
    def test_command_stream_allowlist_pan_and_fields(self):
        run = P.run_continuous()
        for client in (run["subject_client"], run["baseline_client"]):
            self.assertEqual(client.allowlist_violations(), [])
            self.assertEqual(client.forbidden_hits(), [])
            for payload in client.camera_writes():
                self.assertEqual(len(payload), 8)
                self.assertEqual(payload["pan_x"], 0.0)
                self.assertEqual(payload["pan_y"], 0.0)
                self.assertEqual(client.inner.attempts, [])
        # the applied engine state is exactly the last written command (FG)
        for cam, client in ((run["subject"], run["subject_client"]),
                            (run["baseline"], run["baseline_client"])):
            echo = cam.verify_apply()
            self.assertTrue(echo.get("ok"), echo)
            self.assertLessEqual(echo["max_err"], 1e-3)


class TestManifestArtifacts(unittest.TestCase):
    EVIDENCE = HERE / "evidence"

    def test_manifest_samples_equal_trace_poses(self):
        manifest_path = self.EVIDENCE / "capture_manifest.json"
        trace_path = self.EVIDENCE / "trace.jsonl"
        if not manifest_path.is_file() or not trace_path.is_file():
            self.skipTest("evidence not built yet")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = {json.loads(l)["tick"]: json.loads(l)
                for l in trace_path.read_text(encoding="utf-8").splitlines()
                if l}
        self.assertEqual(manifest["schema"],
                         "chimera.visual_capture_manifest.v1")
        self.assertEqual(manifest["task_id"], "U02")
        self.assertEqual(manifest["tick_interval"],
                         [min(rows), max(rows)])
        src_for = {"normal follow-camera distance": "baseline",
                   "obstructed and close-target views": "subject",
                   "repeatable inspection side view": "inspection"}
        for view in manifest["views"]:
            src_name = src_for[view["view_id"]]
            for s in view["camera"]["samples"]:
                src = rows[s["tick"]][src_name]
                self.assertEqual(s["position"], src["position"])
                self.assertEqual(s["target"], src["target"])
                self.assertEqual(s["orientation"], src["orientation"])
                self.assertEqual(s["distance_to_target"],
                                 src["distance_to_target"])

    def test_state_binding_is_current_trace(self):
        manifest_path = self.EVIDENCE / "capture_manifest.json"
        trace_path = self.EVIDENCE / "trace.jsonl"
        if not manifest_path.is_file() or not trace_path.is_file():
            self.skipTest("evidence not built yet")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        trace_sha = hashlib.sha256(trace_path.read_bytes()).hexdigest()
        for view in manifest["views"]:
            self.assertEqual(view["state_binding"],
                             {"kind": "trace", "sha256": trace_sha})
        capture_sha = hashlib.sha256(
            (self.EVIDENCE / "capture.mp4").read_bytes()).hexdigest()
        self.assertEqual(manifest["capture_sha256"], capture_sha)


if __name__ == "__main__":
    unittest.main()
