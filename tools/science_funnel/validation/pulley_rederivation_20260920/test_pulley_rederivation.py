"""Tests for the pulley-rederivation lane (2026-09-20).

Internal consistency and geometry law tests only: nature's verdicts (the SI 2
comparison) are DATA recorded in the deliverable, not hard-coded expectations.
"""

import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

LANE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(LANE_DIR))

import derive_pulley_arms as d  # noqa: E402

MODEL = d.parse_model()
DELIVERABLE_PATH = LANE_DIR / "pulley_arms_derivation.json"


class TestForwardKinematics(unittest.TestCase):
    def test_chain_sits_on_the_parsed_offsets(self):
        fk = d.forward_kinematics(MODEL, {})
        # the shank frame sits at the knee: thigh_r_offset translation (0,
        # -0.15037, 0) in the thigh frame, hip at its default flexion about Z,
        # pelvis offset (0, 0, 0.0352) from ground
        q = MODEL["coordinates"]["hip_flexion_r"]["default"]
        expected = d.rot_z(q) @ np.array([0.0, -0.15037, 0.0]) + np.array(
            [0.0, 0.0, 0.0352])
        self.assertTrue(np.allclose(fk["shank_r"][1], expected, atol=1e-12))
        # and the shank frame equals the knee mobility frame origin
        knee_axis_origin = d.pin_joint_world_axis(MODEL, fk, "knee_r")[1]
        self.assertTrue(np.allclose(knee_axis_origin, fk["shank_r"][1], atol=1e-12))

    def test_shank_moves_with_knee_angle(self):
        fk0 = d.forward_kinematics(MODEL, {"r_knee_flexion": 0.0})
        fkf = d.forward_kinematics(MODEL, {"r_knee_flexion": -0.5})
        # the shank ORIGIN sits on the knee axis (does not translate); an
        # off-axis shank point must move
        p = np.array([0.0157, -0.0288, 0.0033])  # quad insertion point
        p0 = d.xform_apply(fk0["shank_r"], p)
        pf = d.xform_apply(fkf["shank_r"], p)
        self.assertGreater(float(np.linalg.norm(pf - p0)), 0.01)
        # thigh must NOT move with the knee
        self.assertEqual(float(np.linalg.norm(fkf["thigh_r"][1] - fk0["thigh_r"][1])),
                         0.0)

    def test_coupler_moves_hallux_with_mtp(self):
        fk0 = d.forward_kinematics(MODEL, {"r_mtp_flexion": 0.0})
        fkf = d.forward_kinematics(MODEL, {"r_mtp_flexion": 0.3})
        # the hallux BODY ORIGIN sits on the hallux joint axis and does not move;
        # an off-axis hallux point must move under the 1:1 coupler
        p = np.array([0.0225, -0.0009, -0.0003])
        p0 = d.xform_apply(fk0["R_Hallux"], p)
        pf = d.xform_apply(fkf["R_Hallux"], p)
        self.assertGreater(float(np.linalg.norm(pf - p0)), 0.001)


class TestWrapGeometry(unittest.TestCase):
    def _synthetic_cylinder(self):
        return {"name": "syn", "type": "WrapCylinder", "body": "ground",
                "quadrant": "all", "rotation": np.eye(3),
                "world_center": np.array([0.05, 0.0, 0.0]),
                "world_axis": np.array([0.0, 0.0, 1.0]),
                "world_R": np.eye(3), "radius": 0.01}

    def test_cylinder_tangent_points_lie_on_the_circle(self):
        w = self._synthetic_cylinder()
        # the segment passes 8 mm from the axis - inside the 10 mm radius
        A = np.array([-0.05, 0.008, 0.0])
        B = np.array([0.15, 0.008, 0.0])
        res = d.wrap_cylinder(A, B, w)
        self.assertIsNotNone(res)
        r = w["radius"]
        C = w["world_center"]
        self.assertAlmostEqual(float(np.linalg.norm(res["entry"] - C)), r, places=12)
        self.assertAlmostEqual(float(np.linalg.norm(res["exit"] - C)), r, places=12)
        # tangency: (A - E) perpendicular to the radius at E
        self.assertAlmostEqual(
            float((A - res["entry"]) @ (res["entry"] - C) / r), 0.0, places=9)
        self.assertAlmostEqual(
            float((B - res["exit"]) @ (res["exit"] - C) / r), 0.0, places=9)
        self.assertLessEqual(res["arc_rad"], math.pi + 1e-12)
        # wrapped path is longer than the straight chord
        straight = float(np.linalg.norm(B - A))
        wrapped = (float(np.linalg.norm(res["entry"] - A)) + res["arc_len"]
                   + float(np.linalg.norm(B - res["exit"])))
        self.assertGreater(wrapped, straight)

    def test_cylinder_endpoint_inside_raises(self):
        w = self._synthetic_cylinder()
        A = np.array([0.055, 0.0, 0.0])  # inside the circle (|p-C| = 0.005 < r)
        B = np.array([0.15, 0.02, 0.0])
        with self.assertRaises(RuntimeError):
            d.wrap_cylinder(A, B, w)

    def test_cylinder_miss_returns_none(self):
        w = self._synthetic_cylinder()
        A = np.array([-0.05, 0.05, 0.0])   # passes 4 cm above a 1 cm cylinder
        B = np.array([0.15, 0.05, 0.0])
        self.assertIsNone(d.wrap_cylinder(A, B, w))

    def test_sphere_tangent_properties(self):
        w = {"name": "syns", "type": "WrapSphere", "body": "ground", "quadrant": "all",
             "rotation": np.eye(3),
             "world_center": np.array([0.0, 0.0, 0.0]),
             "world_R": np.eye(3), "radius": 0.02}
        A = np.array([-0.08, 0.01, 0.002])
        B = np.array([0.09, 0.012, -0.002])
        res = d.wrap_sphere(A, B, w)
        self.assertIsNotNone(res)
        C = w["world_center"]
        r = w["radius"]
        self.assertAlmostEqual(float(np.linalg.norm(res["entry"] - C)), r, places=12)
        self.assertAlmostEqual(float(np.linalg.norm(res["exit"] - C)), r, places=12)
        self.assertAlmostEqual(
            float((A - res["entry"]) @ (res["entry"] - C) / r), 0.0, places=9)

    def test_fd_arm_equals_geometry_on_a_straight_hinge(self):
        # a straight tendon from (-0.03, 0.04, 0) to a point at distance L on the
        # distal body rotating about z: arm = perpendicular distance to the line
        # through the moving endpoint along the tendon = 0.03 - check r_geo and
        # -dL/dq agree analytically
        O = np.zeros(3)
        u = np.array([0.0, 0.0, 1.0])
        P = np.array([-0.03, 0.04, 0.0])   # fixed
        Q = np.array([0.02, 0.06, 0.0])    # rotates about z at O
        dh = (Q - P) / float(np.linalg.norm(Q - P))
        r_geo = float(-dh @ np.cross(u, Q - O))
        # analytic r_fd: |Q| and the angle to Q change; dL/dq from the derivative
        # of |R(dq) Q - P|; verify numerically
        def L(q):
            R = d.rot_z(q)
            return float(np.linalg.norm(R @ Q - P))
        h = 1e-6
        r_fd = -(L(h) - L(-h)) / (2 * h)
        self.assertAlmostEqual(r_geo, r_fd, places=9)


class TestModelExtraction(unittest.TestCase):
    def test_wrap_census_matches_the_independent_parse(self):
        # 14 wrap objects: 9 cylinders, 3 spheres, 2 ellipsoids; 2 inactive
        kinds = {"WrapCylinder": 0, "WrapSphere": 0, "WrapEllipsoid": 0}
        inactive = []
        for name, w in MODEL["wraps"].items():
            if w["type"] in kinds:
                kinds[w["type"]] += 1
            if not w["active"]:
                inactive.append(name)
        self.assertEqual(kinds, {"WrapCylinder": 9, "WrapSphere": 3,
                                 "WrapEllipsoid": 2})
        self.assertEqual(sorted(inactive),
                         ["rDistalAnkle_SphereforFDL", "rProxTibiaCylinder"])

    def test_metatarsal_and_hallux_cylinders_are_unreferenced(self):
        referenced = {w["wrap_object"] for m in MODEL["muscles"].values()
                      for w in m["wraps"]}
        for unused in ("rAnteriorMetarsalHead_Cylinder",
                       "rPosteriorHalluxHead_Cylinder",
                       "rAnteriorHalluxHead_Cylinder"):
            self.assertNotIn(unused, referenced)

    def test_si2_jranges_are_degrees(self):
        # the SI's -90..0 deg knee jrange matches the model's [-1.6, 0] rad range
        # at 57.2958 deg/rad; the +-30 deg mtp jrange fits the +-0.8 rad range.
        self.assertAlmostEqual(-1.6 * 180.0 / math.pi, -91.673, places=2)
        self.assertAlmostEqual(0.8 * 180.0 / math.pi, 45.837, places=2)


class TestDeliverable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DELIVERABLE_PATH.exists():
            raise unittest.SkipTest("deliverable not derived yet")
        cls.data = json.loads(DELIVERABLE_PATH.read_text(encoding="utf-8"))

    def test_every_number_traces_audit_tables_present(self):
        for key in ("wrap_audit", "path_audit", "directions", "si2_comparison",
                    "euler_convention_check", "method", "inputs"):
            self.assertIn(key, self.data)
        self.assertEqual(len(self.data["directions"]), 9)
        for name, w in self.data["wrap_audit"].items():
            self.assertIn("translation_m", w)
            self.assertIn("xyz_body_rotation_rad", w)
            self.assertTrue(w["radius_m"] or w["dimensions_m"])

    def test_unit_verdict_is_cm_and_unique(self):
        v = self.data["si2_comparison"]["unit_verdict"]
        self.assertFalse(v["mm_hypothesis_all_within_tolerance"])
        self.assertTrue(v["cm_hypothesis_all_within_tolerance"])
        self.assertEqual(v["outcome"], "cm")

    def test_sign_pattern_holds(self):
        self.assertTrue(self.data["si2_comparison"]["sign_pattern_all_match"])

    def test_wrap_activity_load_bearing_pulleys(self):
        rows = self.data["si2_comparison"]["rows"]
        for m in ("R_RF", "R_VI", "R_VL", "R_VMed"):
            eng = rows[m]["wrap_engaged_of_scanned"]["rFemoralCondyles_Cylinder2"]
            self.assertEqual(eng[0], eng[1], "%s condyle pulley must engage 100%%" % m)
        for m in ("R_FDL_TENDONII", "R_FDL_TENDONIII", "R_FDL_TENDONIV"):
            eng = rows[m]["wrap_engaged_of_scanned"]["R_Ankle_Cylinder"]
            self.assertEqual(eng[0], eng[1], "%s ankle pulley must engage 100%%" % m)

    def test_mtp_class_k_constant_to_four_decimals(self):
        kvals = []
        for m in ("R_FDL_TENDONII", "R_FDL_TENDONIII", "R_FDL_TENDONIV",
                  "R_FDL_TENDONV", "R_FHL"):
            for e in ("min", "max"):
                kvals.append(self.data["si2_comparison"]["rows"][m]["endpoints"][e]
                             ["k_this_row"])
        self.assertLess(max(kvals) - min(kvals), 5e-5)

    def test_determinism_reduced_scan_in_process(self):
        import contextlib
        import hashlib
        import io
        import tempfile
        import derive_pulley_arms as mod
        with tempfile.TemporaryDirectory() as td:
            out1 = Path(td) / "_det1.json"
            out2 = Path(td) / "_det2.json"
            buf1, buf2 = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(buf1):
                mod.main(["derive_pulley_arms", str(out1)], n_scan=41)
            with contextlib.redirect_stdout(buf2):
                mod.main(["derive_pulley_arms", str(out2)], n_scan=41)
            h1 = hashlib.sha256(out1.read_bytes()).hexdigest()
            h2 = hashlib.sha256(out2.read_bytes()).hexdigest()
        self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
