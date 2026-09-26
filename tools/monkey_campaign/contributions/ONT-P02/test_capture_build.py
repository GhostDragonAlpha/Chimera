"""test_capture_build.py -- ONT-P02 visible_static correction falsifier tests.

python -B -m unittest test_capture_build -v

Re-derives the frozen predictions from the pinned subject blob, re-validates
the committed capture manifest with the campaign's own visual_capture /
visual_gate validators, and asserts the preregistered falsifier properties
(P1-P6).  Heavy mesh work runs once per class.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

import capture_build as cb                                   # noqa: E402
CAPTURE = HERE / "evidence" / "capture.png"
MANIFEST = HERE / "evidence" / "capture_manifest.json"


def sha256_file(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


class TestVisibleStaticCapture(unittest.TestCase):
    an = None
    manifest = None

    @classmethod
    def setUpClass(cls):
        cls.an = cb.load_anatomy(HERE.parents[4] / "scratch"
                                 / "ont-p02-capture-tests")
        if MANIFEST.is_file():
            cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # ── frozen predictions from the pinned bytes (P6) ────────────────────
    def test_subject_identity(self):
        raw = (HERE.parents[4] / "scratch" / "ont-p02-capture-tests"
               / "standing_body.obj").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), cb.SUBJECT_SHA256)
        self.assertEqual(len(raw), cb.SUBJECT_BYTES)

    def test_frozen_predictions(self):
        V = self.an["V"]
        self.assertEqual(len(V), 249743)
        self.assertEqual(len(self.an["F"]), 499976)
        for got, want in zip(V.min(0), cb.PRED_BBOX_MIN):
            self.assertAlmostEqual(float(got), want, delta=5e-7)
        for got, want in zip(V.max(0), cb.PRED_BBOX_MAX):
            self.assertAlmostEqual(float(got), want, delta=5e-7)
        self.assertEqual(int(((V[:, 1] <= float(V[:, 1].min()) + 0.005)).sum()),
                         cb.PRED_BAND_N)

    # ── manifest + camera falsifier structure (P1, P4, P5) ───────────────
    def test_manifest_structure_and_gate(self):
        self.assertTrue(MANIFEST.is_file(), "capture not built yet")
        self.assertTrue(CAPTURE.is_file(), "capture not built yet")
        capture_sha = sha256_file(CAPTURE)
        self.assertEqual(self.manifest["capture_sha256"], capture_sha)
        self.assertEqual(self.manifest["subject_sha256"], cb.SUBJECT_SHA256)
        sys.path.insert(0, str(cb.validator_dir()))
        for stale in ("visual_gate", "visual_capture", "integrity"):
            sys.modules.pop(stale, None)
        import visual_gate
        contract = json.loads((HERE / "card_task.json").read_text(
            encoding="utf-8"))
        receipt = {
            "evidence": {
                "camera": {"reference": str(MANIFEST.resolve()),
                           "raw_sha256": sha256_file(MANIFEST)},
                "visual": {"reference": str(CAPTURE.resolve()),
                           "raw_sha256": capture_sha},
            },
            "capture_context": {
                "task_id": "P02",
                "subject_sha256": cb.SUBJECT_SHA256,
                "run_id": self.manifest["run_id"],
                "capture_sha256": capture_sha,
                "tick_interval": self.manifest["tick_interval"],
            },
        }
        structural = visual_gate.verify(receipt, contract)
        self.assertTrue(structural["structurally_valid"])
        self.assertEqual(structural["capture_kind"], "image")

    def test_all_profile_views_and_layers_covered(self):
        profile = json.loads((HERE / "card_task.json").read_text(
            encoding="utf-8"))["task"]["verification_profile"]
        rows = self.manifest["views"]
        seen = {(r["view_id"], r["mode"]) for r in rows}
        for v in profile["views"]:
            self.assertIn((v, "diagnostic"), seen)
            self.assertIn((v, "clean"), seen)
        layers_seen = set()
        for r in rows:
            if r["mode"] == "diagnostic":
                layers_seen.update(r["visibility"]["layers"])
        self.assertTrue(set(profile["diagnostic_layers"]) <= layers_seen)

    def test_state_binding_constant_across_views(self):
        # P5: view toggles preserve the physical state hash
        for r in self.manifest["views"]:
            self.assertEqual(r["state_binding"],
                             {"kind": "state", "sha256": cb.SUBJECT_SHA256})

    def test_label_bindings_one_to_one(self):
        # P4: no label ambiguity
        for r in self.manifest["views"]:
            vis = r["visibility"]
            labels = [b["label_id"] for b in vis["tag_bindings"]]
            self.assertEqual(len(labels), len(set(labels)))
            self.assertEqual(set(labels), set(vis["label_ids"]))

    def test_clean_views_carry_no_diagnostics(self):
        for r in self.manifest["views"]:
            if r["mode"] == "clean":
                self.assertEqual(r["visibility"]["layers"], [])
                self.assertEqual(r["visibility"]["label_ids"], [])
                self.assertEqual(r["visibility"]["tag_bindings"], [])
                self.assertEqual(r["visibility"]["occlusion_mode"],
                                 "depth_tested")

    def test_artifact_rects_inside_sheet(self):
        from PIL import Image
        with Image.open(CAPTURE) as im:
            w, h = im.size
        self.assertEqual((w, h), (cb.SHEET_W, cb.SHEET_H))
        for r in self.manifest["views"]:
            rect = r["artifact_locator"]["pixel_rectangle"]
            self.assertEqual(r["artifact_locator"]["kind"], "image")
            self.assertEqual(r["artifact_locator"]["region"],
                             "pixel_rectangle")
            self.assertGreaterEqual(rect[0], 0)
            self.assertGreaterEqual(rect[1], 0)
            self.assertGreater(rect[2], 0)
            self.assertGreater(rect[3], 0)
            self.assertLessEqual(rect[0] + rect[2], w)
            self.assertLessEqual(rect[1] + rect[3], h)

    # ── camera falsifier math (P2/P3 geometry) ───────────────────────────
    def test_full_views_frustum_contains_all_verts(self):
        rows, cams = cb.build_manifest(self.an)
        for key in ("overview", "side", "oblique"):
            ok, n_in, n = cb.in_frame(cams[key], self.an["V"])
            self.assertTrue(ok, "%s frustum check failed" % key)
            self.assertEqual(n_in, 249743)

    def test_closeup_anchors_in_frame(self):
        import numpy as np
        rows, cams = cb.build_manifest(self.an)
        anchors = np.array([self.an["band_centroid"], self.an["joint"],
                            self.an["cents"][2], self.an["cents"][6]],
                           dtype=np.float64)
        ok, n_in, n = cb.in_frame(cams["closeup"], anchors)
        self.assertTrue(ok)
        self.assertEqual(n_in, 4)

    def test_fixed_bookmarks_identical(self):
        rows, cams = cb.build_manifest(self.an)
        for key in ("overview", "closeup"):
            s = cams[key].sample(0), cams[key].sample(1)
            for k in ("position", "target", "distance_to_target",
                      "orientation"):
                self.assertEqual(s[0][k], s[1][k])


if __name__ == "__main__":
    unittest.main(verbosity=2)
