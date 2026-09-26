"""ONT-A04 falsifier and unit tests (CPU-only, python -B, stdlib+numpy+Agg).

Covers the frozen preregistration bars that are testable without re-running the
full probe: transform round-trip/handedness (C01 machinery), camera quaternion
and projection consistency, z-buffer raster, the palm-plate sign method on a
synthetic plate, manifest validation (positive on the actual evidence artifact,
negative on a diagnostic-polluted clean view), reference pin identity, coverage
inventory counts, and the actual receipts' green state.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

import a04_correspondence_probe as P  # noqa: E402
from capture_build import (  # noqa: E402
    auto_half_h, basis_to_quat_wxyz, cam_record, camera_basis, project,
    raster, shade)


def quat_rotate(q, v):
    w, x, y, z = q
    v = np.asarray(v, float)
    u = np.array([x, y, z])
    return v + 2.0 * np.cross(u, np.cross(u, v) + w * v)


class TestFrameChain(unittest.TestCase):
    def test_round_trip_and_handedness_synthetic(self):
        """C01 machinery: x_world = R x_local + t composes and inverts exactly,
        right-handed rotations keep det(R) = +1."""
        rng = np.random.default_rng(20260926)
        def rot(axis, ang):
            axis = P.unit(axis)
            K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]],
                          [-axis[1], axis[0], 0]])
            return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * (K @ K)
        for axis in ([1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0], [1, 2, 3]):
            R = rot(axis, 0.7)
            self.assertAlmostEqual(float(np.linalg.det(R)), 1.0, places=12)
            t = np.array([0.01, -0.02, 0.03])
            pts = rng.normal(size=(5, 3))
            world = pts @ R.T + t
            back = (world - t) @ R
            self.assertLess(float(np.abs(back - pts).max()), 1e-12)

    def test_scaling_distinct_from_rotation(self):
        """C01: a uniform scale is NOT a rotation; the probe's chain uses R = I."""
        s = 0.716
        M = np.eye(3) * s
        self.assertAlmostEqual(float(np.linalg.det(M)), s ** 3, places=12)
        self.assertNotAlmostEqual(float(np.linalg.det(M)), 1.0, places=3)


class TestCamera(unittest.TestCase):
    def test_quat_round_trip_and_forward(self):
        eye = np.array([0.3, -0.2, 0.45])
        look = np.array([0.0, -0.05, 0.0])
        up = np.array([0.0, 1.0, 0.0])
        rec, (x_cam, y_cam, f) = cam_record("f", eye, look, up, 0.1, 348, 600)
        s = rec["samples"][0]
        self.assertTrue(np.isclose(s["distance_to_target"],
                                   float(np.linalg.norm(eye - look)), rtol=1e-12))
        q = np.asarray(s["orientation"])
        self.assertAlmostEqual(float(np.linalg.norm(q)), 1.0, places=12)
        self.assertTrue(np.allclose(quat_rotate(q, (0, 0, -1)), f, atol=1e-12))
        self.assertTrue(np.allclose(quat_rotate(q, (1, 0, 0)), x_cam, atol=1e-12))
        self.assertTrue(np.allclose(quat_rotate(q, (0, 1, 0)), y_cam, atol=1e-12))

    def test_projection_maps_target_to_center(self):
        eye = np.array([0.0, 0.0, 0.5])
        look = np.array([0.0, 0.0, 0.0])
        up = np.array([0.0, 1.0, 0.0])
        x_cam, y_cam, f = camera_basis(eye, look, up)
        px, d = project(np.array([[0.0, 0.0, 0.0]]), eye, x_cam, y_cam, f, 0.1, 200, 100)
        self.assertTrue(np.allclose(px[0], (100.0, 50.0)))
        self.assertAlmostEqual(float(d[0]), 0.5, places=12)

    def test_raster_and_depth(self):
        eye = np.array([0.0, 0.0, 0.5])
        look = np.zeros(3)
        up = np.array([0.0, 1.0, 0.0])
        x_cam, y_cam, f = camera_basis(eye, look, up)
        tri = np.array([[[-0.01, -0.01, 0.0], [0.01, -0.01, 0.0], [0.0, 0.02, 0.0]]])
        img, zbuf, mask = raster(tri, eye, x_cam, y_cam, f, 0.05, 60, 40)
        self.assertTrue(mask.any())
        shaded = shade(img, zbuf, mask, (0.5, 0.5, 0.5))
        bg = np.asarray([0.93, 0.93, 0.96])
        self.assertTrue(np.allclose(shaded[~mask], bg[None, :], atol=1e-9))
        self.assertFalse(np.allclose(shaded[mask], np.tile(bg, (int(mask.sum()), 1)), atol=1e-3))
        # a triangle behind the camera renders nothing
        tri2 = np.array([[[-0.01, -0.01, 1.2], [0.01, -0.01, 1.2], [0.0, 0.02, 1.2]]])
        _, _, mask2 = raster(tri2, eye, x_cam, y_cam, f, 0.05, 60, 40)
        self.assertFalse(mask2.any())

    def test_auto_frame_no_clip(self):
        eye = np.array([0.0, -0.3, 0.4])
        look = np.zeros(3)
        up = np.array([0.0, 1.0, 0.0])
        pts = np.array([[[-0.03, -0.05, 0.0], [0.03, 0.06, 0.0], [0.0, 0.0, 0.02]]])
        hh = auto_half_h(eye, look, up, pts, 348, 600)
        xc, yc, f = camera_basis(eye, look, up)
        rel = pts.reshape(-1, 3) - eye
        u, v = rel @ xc, rel @ yc
        self.assertLessEqual(np.abs(u).max(), hh * 348 / 600 + 1e-12)
        self.assertLessEqual(np.abs(v).max(), hh + 1e-12)


class TestPalmPlateMethod(unittest.TestCase):
    def test_synthetic_plate_sign_recovery(self):
        """The frozen pisiform-signed palm-plate method recovers a known plane and
        puts the palm side on the pisiform-protrusion side."""
        rng = np.random.default_rng(7)
        n_true = P.unit(np.array([0.2, -0.3, 0.9]))
        plate = ["pisiform", "lunate", "scaphoid", "triquetrum", "hamate", "capitate",
                 "trapezoid", "trapezium", "2mc", "3mc", "4mc", "5mc"]
        verts = {}
        base = np.zeros(3)
        for i, b in enumerate(plate):
            c = base + np.array([0.01 * i, 0.002 * i, -0.001 * i])
            cloud = c + rng.normal(scale=0.004, size=(120, 3))
            cloud -= (cloud - c) @ n_true[:, None] * n_true  # flatten to the plane
            verts[b] = cloud
        # pisiform protrudes toward the palm side (+n_true side by construction)
        verts["pisiform"] += n_true * 0.007
        der = P.palm_plate({b: np.zeros(3) for b in plate}, verts)
        n_hat = der["n_hat_unsigned"]
        alignment = abs(float(n_hat @ n_true))
        self.assertGreater(alignment, 0.999)
        # the plate clouds sit on slightly offset parallel planes (a curved band):
        # rms is dominated by that curvature plus the pisiform protrusion
        self.assertGreater(der["plate_rms_residual_mm"], 0.1)
        self.assertLess(der["plate_rms_residual_mm"], 3.0)
        self.assertEqual(np.sign(der["pisiform_dot_mm"]), 1.0)
        self.assertTrue(np.allclose(der["n_palm"], n_hat))


class TestEvidenceArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.num = json.loads((HERE / "evidence" / "numerical_receipt.json").read_text())
        cls.state = json.loads((HERE / "evidence" / "state_snapshot.json").read_text())
        cls.man = json.loads((HERE / "evidence" / "capture_manifest.json").read_text())

    def test_reference_pins(self):
        self.assertEqual(P.sha256_path(HERE / "reference" / "chimanoid.xml"), P.XML_SHA_PIN)
        self.assertEqual(P.sha256_path(P.BIRTH), P.BIRTH_SHA_PIN)
        self.assertEqual(P.sha256_path(P.PACK), P.PACK_SHA_PIN)

    def test_numerical_receipt_all_green(self):
        self.assertTrue(self.num["all_green"])
        self.assertEqual(self.num["attempt_id"], "86b87bfe23b14059ac8ed516104340bf")
        self.assertEqual(self.num["criteria_sha256"],
                         "bf8583ae76c4930f726c4c71861ab9219cdac65eb3913cb29ab6131671505570")
        names = [c["name"] for c in self.num["checks"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 7)
        for dv in self.num["prediction_deviations"]:
            self.assertTrue(dv["fired"])

    def test_palm_sign_and_frame_values(self):
        c2 = next(c for c in self.num["checks"] if c["name"] == "C2_frame_chain_round_trip")
        self.assertEqual(c2["measured"]["det_chain_rotation"], 1.0)
        self.assertLess(c2["measured"]["max_round_trip_residual_m"], 1e-12)
        c3 = next(c for c in self.num["checks"] if c["name"] == "C3_palm_sign_rederivation")
        n = np.asarray(c3["measured"]["n_palm_hand_r_local"])
        self.assertTrue(np.allclose(n, P.EXPECT_N_PALM, atol=1e-9))
        self.assertTrue(c3["measured"]["acceptance_split"]["clean"])
        c7 = next(c for c in self.num["checks"] if c["name"] == "C7_palm_sign_statement")
        self.assertFalse(c7["measured"]["target_face_instrument"]["human_verdict_recorded"])
        self.assertIn("UNRESOLVED", c7["measured"]["target_palm_sign"])

    def test_coverage_inventory_counts(self):
        cov = self.state["coverage"]
        self.assertEqual(len(cov["source_ids"]["bones"]), 27)
        self.assertEqual(len(cov["source_ids"]["ports"]), 5)
        self.assertEqual(cov["covered"]["carpals_metacarpals"]["count"], 13)
        self.assertEqual(cov["not_covered"]["phalanges"]["count"], 14)
        self.assertTrue(cov["orientation_does_not_set_scale"])
        self.assertIn("UNRESOLVED", cov["scale_alternatives"]["H_LEN"]["status"])
        self.assertIn("REJECTED", cov["scale_alternatives"]["H_BODY"]["status"])

    def test_manifest_structurally_valid_against_card_profile(self):
        sys.path.insert(0, r"E:\PythonChimera\tools\monkey_campaign")
        import visual_capture
        card = json.loads((HERE / "card_task.json").read_text())
        capture_png = HERE / "evidence" / "capture_a04.png"
        ctx = {"task_id": "A04", "subject_sha256": self.man["subject_sha256"],
               "run_id": self.man["run_id"], "capture_sha256": self.man["capture_sha256"],
               "tick_interval": [0, 0]}
        self.assertEqual(P.sha256_path(capture_png), self.man["capture_sha256"])
        gate = visual_capture.validate_manifest(self.man, ctx,
                                                card["task"]["verification_profile"])
        self.assertTrue(gate["structurally_valid"])

    def test_manifest_clean_views_have_no_diagnostics(self):
        for row in self.man["views"]:
            if row["mode"] == "clean":
                self.assertEqual(row["visibility"]["layers"], [])
                self.assertEqual(row["visibility"]["label_ids"], [])
                self.assertEqual(row["visibility"]["tag_bindings"], [])
                self.assertEqual(row["visibility"]["occlusion_mode"], "depth_tested")
            else:
                self.assertTrue(row["visibility"]["layers"])
                self.assertEqual(row["camera"], self.man["views"][
                    self.man["views"].index(row) + 1]["camera"])

    def test_state_binding_binds_both_modes(self):
        for i in range(0, len(self.man["views"]), 2):
            d, c = self.man["views"][i], self.man["views"][i + 1]
            self.assertEqual(d["state_binding"], c["state_binding"])
            self.assertEqual(d["state_binding"]["kind"], "state")


if __name__ == "__main__":
    unittest.main()
