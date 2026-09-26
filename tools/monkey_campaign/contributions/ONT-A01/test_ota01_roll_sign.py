"""ONT-A01 CPU tests: falsifiable re-verification + capture structural checks.

Run: python -B -m unittest test_ota01_roll_sign -v
Everything is offline, deterministic, CPU-only. The canonical campaign validator
is imported read-only (python -B prevents bytecode writes) from
E:/PythonChimera/tools/monkey_campaign so tests exercise the SAME visual gate the
reviewer runs.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ota01_roll_sign as core  # noqa: E402

EVIDENCE = HERE / "evidence"


def _build_cached():
    return core.write_receipts()


STATE, RECEIPT = _build_cached()


class TestInputIdentities(unittest.TestCase):
    def test_pinned_inputs_match_o1_expect_sha(self):
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


class TestP1SourceBone(unittest.TestCase):
    def test_olecranon_is_extreme_negative_x(self):
        p1 = RECEIPT["P1_source_bone"]
        self.assertLess(p1["olecranon_min_x_mm"], -20.0)
        self.assertAlmostEqual(p1["olecranon_min_x_mm"],
                               p1["receipt_olecranon_min_x_mm"], delta=core.TOL_MESH_MM)
        self.assertAlmostEqual(p1["distal_min_y_mm"],
                               p1["receipt_distal_min_y_mm"], delta=core.TOL_MESH_MM)

    def test_forearm_length_matches_record(self):
        p1 = RECEIPT["P1_source_bone"]
        # O1 cross-wave note: distal extent ~ full 305.8 mm forearm
        self.assertGreater(p1["distal_min_y_mm"], -305.0)
        self.assertLess(p1["distal_min_y_mm"], -290.0)


class TestP2TargetOlecranonTest(unittest.TestCase):
    def test_method_identity_basis_matches_receipt(self):
        p2 = RECEIPT["P2_target_olecranon_test"]
        self.assertTrue(p2["axis_matches_receipt"])
        self.assertTrue(p2["e1_matches_receipt"])
        self.assertTrue(p2["e2_matches_receipt"])

    def test_best_station_reproduces_record_exactly(self):
        p2 = RECEIPT["P2_target_olecranon_test"]
        self.assertAlmostEqual(p2["d_best_D_mm"], 0.0, delta=core.TOL_D_MM)
        self.assertAlmostEqual(p2["best_station"]["D_post_minus_ant_mm"], 3.2891597453,
                               delta=1e-6)
        self.assertTrue(p2["best_station"]["D_above_2mm"])

    def test_zone_dissent_is_the_records_own_not_drift(self):
        """The frozen strict-zone prediction fails at t=+8; this test pins that the
        failing value is byte-identical to the pinned receipt (no measurement
        drift) - the dissent belongs to the zone claim itself."""
        p2 = RECEIPT["P2_target_olecranon_test"]
        row8 = next(r for r in p2["zone_rows"] if r["t_mm"] == 8.0)
        self.assertAlmostEqual(row8["d_D_mm"], 0.0, delta=1e-9)
        self.assertAlmostEqual(row8["D_post_minus_ant_mm"], 1.8135108487, delta=1e-6)
        self.assertFalse(row8["D_above_2mm"])
        self.assertFalse(p2["zone_all_above_2mm"])
        self.assertFalse(p2["verdict"])


class TestP3SignLaw(unittest.TestCase):
    def test_unanimous_no_flip(self):
        p3 = RECEIPT["P3_sign_law"]
        self.assertTrue(p3["unanimous_no_flip"])
        self.assertTrue(p3["receipt_unanimous_no_flip"])
        for r in p3["per_candidate"]:
            self.assertLess(r["error_no_flip_deg"], r["error_flip_deg"], r)

    def test_law_is_plus_ninety(self):
        p3 = RECEIPT["P3_sign_law"]
        self.assertLess(p3["max_volar_law_residual_deg"], 90.0)
        trilat = next(r for r in p3["per_candidate"]
                      if r["roll_candidate"] == "TRIlat-P5")
        self.assertAlmostEqual(trilat["error_no_flip_deg"], 0.14938, delta=core.TOL_AZ_DEG)
        self.assertTrue(p3["verdict"])


class TestFrozenOutcomeRules(unittest.TestCase):
    def test_outcome_follows_frozen_rules_no_retuning(self):
        r = RECEIPT
        fired = set(r["fired_falsifiers"])
        self.assertIn("F2", fired)          # zone dissent (t=+8, D=1.81 <= 2)
        self.assertIn("F4", fired)          # P2 verdict False under frozen tolerance
        self.assertNotIn("F1", fired)       # source bone verified
        self.assertNotIn("F3", fired)       # flip refuted unanimously
        self.assertEqual(r["outcome"], "AMBIGUITY_RECORDED")
        self.assertEqual(r["done_when"],
                         "Records ambiguity (see fired falsifiers; both readings preserved)")

    def test_both_readings_preserved(self):
        r = RECEIPT
        self.assertIn("sign_statement", r)
        self.assertIn("source volar +x <-> target volar +z",
                      r["sign_statement"]["world_mapping"])
        p2 = r["P2_target_olecranon_test"]
        self.assertIn("receipt_D_mm", p2["zone_rows"][0])


class TestQuaternionAndCamera(unittest.TestCase):
    def test_mat_to_quat_round_trip(self):
        import ota01_render_views as rv
        rng = np.random.default_rng(0)
        for _ in range(20):
            A = rng.normal(size=(3, 3))
            Q, _ = np.linalg.qr(A)
            if np.linalg.det(Q) < 0:
                Q[:, 0] *= -1
            q = rv.mat_to_quat_wxyz(Q)
            self.assertAlmostEqual(float(np.sqrt(np.dot(q, q))), 1.0, places=9)
            w, x, y, z = q
            R = np.array([
                [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
            self.assertTrue(np.allclose(R, Q, atol=1e-9))

    def test_camera_distance_and_basis(self):
        import ota01_render_views as rv
        cam = rv.cam_sample([10, 0, 0], [0, 0, 0], [0, 1, 0])
        self.assertAlmostEqual(cam["distance_to_target"], 10.0, places=9)
        Xc, Yc, Zc, fwd = rv.camera_basis([10, 0, 0], [0, 0, 0], [0, 1, 0])
        self.assertTrue(np.allclose(fwd, [-1, 0, 0]))
        self.assertTrue(np.allclose(np.cross(Xc, Yc), Zc))


class TestCaptureManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")
        from visual_capture import validate_manifest
        cls.validate = staticmethod(validate_manifest)
        cls.manifest = json.loads((EVIDENCE / "capture_manifest.json").read_text())
        cls.context = json.loads((EVIDENCE / "capture_context.json").read_text())
        cls.profile = {
            "id": "anatomy", "kind": "visible_static",
            "views": ["whole-creature overview", "local attachment close-up",
                      "orthogonal side and oblique views"],
            "diagnostic_layers": ["outer envelope", "selected bones/joints",
                                  "muscle/tendon paths", "attachment sites",
                                  "frame axes", "stable 3D labels"],
            "clean_view_required": True}

    def test_hashes_bind_actual_files(self):
        cap = hashlib.sha256((EVIDENCE / "capture_sheet.png").read_bytes()).hexdigest()
        sub = hashlib.sha256((EVIDENCE / "state_snapshot.json").read_bytes()).hexdigest()
        self.assertEqual(self.manifest["capture_sha256"], cap)
        self.assertEqual(self.manifest["subject_sha256"], sub)
        self.assertEqual(self.context["capture_sha256"], cap)
        self.assertEqual(self.context["subject_sha256"], sub)

    def test_structurally_valid_against_canonical_validator(self):
        out = self.validate(self.manifest, self.context, self.profile)
        self.assertTrue(out["structurally_valid"])
        self.assertEqual(out["profile_id"], "anatomy")

    def test_pairs_share_state_binding_and_camera(self):
        rows = self.manifest["views"]
        self.assertEqual(len(rows), 6)
        by_pair = {}
        for r in rows:
            by_pair.setdefault(r["pair_id"], []).append(r)
        for pid, rs in by_pair.items():
            self.assertEqual({r["mode"] for r in rs}, {"diagnostic", "clean"}, pid)
            self.assertEqual(rs[0]["state_binding"], rs[1]["state_binding"], pid)
            self.assertEqual(rs[0]["camera"], rs[1]["camera"], pid)

    def test_clean_rows_declare_no_diagnostics(self):
        for r in self.manifest["views"]:
            if r["mode"] == "clean":
                v = r["visibility"]
                self.assertEqual(v["layers"], [])
                self.assertEqual(v["label_ids"], [])
                self.assertEqual(v["occlusion_mode"], "depth_tested")

    def test_all_six_declared_layers_appear(self):
        seen = set()
        for r in self.manifest["views"]:
            if r["mode"] == "diagnostic":
                seen.update(r["visibility"]["layers"])
        self.assertTrue(set(self.profile["diagnostic_layers"]) <= seen)

    def test_rectangles_inside_sheet(self):
        sheet = (1920, 1080)
        for r in self.manifest["views"]:
            rect = r["artifact_locator"]["pixel_rectangle"]
            left, top, w, h = rect
            self.assertGreaterEqual(left, 0)
            self.assertGreaterEqual(top, 0)
            self.assertLessEqual(left + w, sheet[0])
            self.assertLessEqual(top + h, sheet[1])
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)

    def test_honest_deterministic_cpu_label_present(self):
        render = self.manifest["render"]
        self.assertIn("numpy-zbuffer-software-raster-cpu", render["backend"])
        self.assertFalse(render["native_engine_frames"])
        self.assertTrue(render["deterministic"])
        self.assertFalse(render["gpu_used"])


class TestQualificationReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads(
            (EVIDENCE / "qualification_receipt.json").read_text())

    def test_identity_fields(self):
        r = self.receipt
        self.assertEqual(r["scope_sha256"],
                         "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6")
        self.assertEqual(r["task_id"], "A01")
        self.assertEqual(r["criteria_sha256"],
                         "2bcf59fa0b786b009b30711334e38fe374d9a2a2bdefdba9566a4018c4a9c775")
        self.assertIsNone(r["head_sha"])
        self.assertIn("invalidates", r["head_sha_binding_note"])
        self.assertTrue(r["done_when_verified"] and r["profile_verified"])

    def test_evidence_hashes_bind_actual_files(self):
        for kind, meta in self.receipt["evidence"].items():
            path = Path(meta["reference"])
            self.assertTrue(path.is_absolute() and path.is_file(), kind)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                             meta["raw_sha256"], kind)

    def test_passes_enforced_visual_gate(self):
        from visual_gate import verify
        contract = {"task_id": "A01", "scope_sha256": self.receipt["scope_sha256"],
                    "task": {"id": "A01", "verification_profile": {
                        "id": "anatomy", "kind": "visible_static",
                        "views": ["whole-creature overview",
                                  "local attachment close-up",
                                  "orthogonal side and oblique views"],
                        "diagnostic_layers": ["outer envelope", "selected bones/joints",
                                              "muscle/tendon paths", "attachment sites",
                                              "frame axes", "stable 3D labels"],
                        "clean_view_required": True}}}
        out = verify(self.receipt, contract)
        self.assertTrue(out["structurally_valid"])

    def test_outcome_matches_numerical_receipt(self):
        self.assertEqual(self.receipt["outcome"], RECEIPT["outcome"])
        self.assertEqual(self.receipt["honesty"]["native_engine_frames"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
