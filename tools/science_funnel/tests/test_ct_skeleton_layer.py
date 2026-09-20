"""Tests for the CT skeleton VISUAL layer (lane buffy/ct-skeleton-visual-20260919).

Rule 0: the falsifier was stated before the build; these tests measure it at the
pinned source state and refuse to let the registration drift silently.
Boundaries: no gait-lane file is written; the engine (if live) is only POSTed to.
"""
import json
import struct
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from tools.science_funnel import ct_skeleton_layer as csl
from tools.science_funnel.ct_skeleton_layer import (
    FEMUR_ANGLE_DEG,
    SKULL_TOL_M,
    apply_registration,
    ct_registration,
    femur_sagittal_angles,
    hat_pelvis_axis_residuals,
    load_obj_vertices,
    measure_falsifier,
    splats_for_mesh,
    trunk_axis,
)

ROOT = Path(__file__).resolve().parents[3]
COMPOSITE = ROOT / "tools/science_funnel/data/morphosource_ct/meshes_preview/bone_01_4737869vox_lo.obj"


class TrunkAxisContract(unittest.TestCase):
    def test_trunk_axis_is_head_positive_and_skull_end_is_broader(self):
        composite = load_obj_vertices(COMPOSITE)
        axis, span_mm = trunk_axis(composite)
        self.assertAlmostEqual(float(np.linalg.norm(axis)), 1.0, places=9)
        self.assertGreater(axis[0], 0.0, "skull (+x) side must carry the +sign")
        self.assertGreater(span_mm, 100.0, "infant composite trunk span ~149 mm")
        self.assertLess(span_mm, 170.0)

    def test_registration_is_rigid_documented_and_proper(self):
        composite = load_obj_vertices(COMPOSITE)
        scale, R, translation, diag = ct_registration(composite, 0.482, -0.08977588222411312)
        self.assertAlmostEqual(float(np.linalg.det(R)), 1.0, places=9)
        np.testing.assert_allclose(R @ R.T, np.eye(3), atol=1e-9)
        # the trunk PCA axis maps to scene up (+Y)
        np.testing.assert_allclose(R @ np.asarray(diag["trunk_axis_ct"]),
                                   np.array([0.0, 1.0, 0.0]), atol=1e-6)
        # scale is uniform and derived from the pinned HAT length
        self.assertAlmostEqual(scale, 0.482 / (diag["trunk_span_mm"] / 1000.0), places=4,
                               msg="scale must equal HAT/span at the rounded span")
        # documented values match the returned transform
        self.assertEqual(diag["rotation_ct_to_walker"],
                         [[round(float(v), 8) for v in row] for row in R])
        self.assertEqual(diag["translation_m"], [round(float(v), 6) for v in translation])

    def test_registration_maps_trunk_midpoint_to_seat_height(self):
        composite = load_obj_vertices(COMPOSITE)
        seat = -0.08977588222411312
        scale, R, translation, _ = ct_registration(composite, 0.482, seat)
        c = composite.mean(axis=0)
        axis, _ = trunk_axis(composite)
        t = (composite - c) @ axis
        lo, hi = np.percentile(t, csl.SPAN_PCT)
        mid = c + axis * (0.5 * (lo + hi))
        scene = apply_registration(mid[None, :], scale, R, translation)[0]
        self.assertAlmostEqual(float(scene[1]), seat, places=9)
        self.assertAlmostEqual(float(scene[0]), 0.0, places=9)
        self.assertAlmostEqual(float(scene[2]), 0.0, places=9)


class FalsifierMeasurement(unittest.TestCase):
    def test_skull_end_within_15mm_on_trunk_axis(self):
        receipt = measure_falsifier()
        self.assertLessEqual(receipt["falsifier"]["skull_axis_residual_m"], SKULL_TOL_M,
                             "pre-registered skull-landmark residual must sit inside 15 mm")

    def test_femur_angles_measured_and_reported_either_way(self):
        receipt = measure_falsifier()
        angles = receipt["falsifier"]["femur_angles_deg"]
        self.assertEqual(len(angles), 2, "both femur-class axes are measured")
        in_band = [a for a in angles if FEMUR_ANGLE_DEG[0] <= a <= FEMUR_ANGLE_DEG[1]]
        # honest report either way: the band membership is RECORDED, not assumed
        self.assertEqual(in_band, receipt["falsifier"]["femur_angles_in_band_30_80"])
        self.assertTrue(receipt["falsifier"]["femur_band_report"])
        # the identification file's own low-confidence flag is carried through
        for f in receipt["femora"]:
            self.assertIn(f["confidence"], ("low(mirror 4.1mm)", "low(mirror 4.07mm)"),
                          msg=f["confidence"])

    def test_femur_sagittal_angle_math(self):
        # axis along CT trunk (+x): 0 deg; axis along dorsal (+y): 90 deg
        fake = {"specimens": {csl.SPECIMEN: {"bones": [
            {"rank": 1, "identified_as": "femur_class", "side": "left",
             "confidence": "c", "length_mm": 9.0, "axis_unit": [0.5, 0.8660254, 0.0]},
            {"rank": 2, "identified_as": "femur_class", "side": "right",
             "confidence": "c", "length_mm": 10.0, "axis_unit": [1.0, 0.0, 0.0]},
            {"rank": 3, "identified_as": "unpaired", "side": "?",
             "confidence": "unpaired", "axis_unit": [0.0, 0.0, 1.0]},
        ]}}}
        rows = femur_sagittal_angles(fake)
        self.assertEqual([r["sagittal_angle_deg"] for r in rows], [0.0, 60.0])
        self.assertEqual(rows[0]["in_band_30_80"], False)
        self.assertEqual(rows[1]["in_band_30_80"], True)

    def test_residuals_report_secondary_landmark_not_gated(self):
        composite = load_obj_vertices(COMPOSITE)
        scale, R, translation, _ = ct_registration(composite, 0.482, -0.08977588222411312)
        res = hat_pelvis_axis_residuals(composite, scale, R, translation, 0.482)
        self.assertLess(res["skull_axis_residual_m"], res["skull_landmark_residual_m"],
                        "the harsher breadth-weighted landmark must be looser, and it is reported")
        self.assertIn("FORELIMBS", res["caveat_whole_body_proportion"])

    def test_walker_pin_drift_refuses(self):
        with mock.patch.object(csl, "WALKER_DERIVED_SHA256", "0" * 64):
            with self.assertRaises(csl.SkeletonLayerRefusal) as ctx:
                measure_falsifier()
        self.assertIn("pin", str(ctx.exception))


class SplatLayerContract(unittest.TestCase):
    def test_splat_rows_follow_membrane_bin_layout(self):
        composite = load_obj_vertices(COMPOSITE)
        scale, R, translation, _ = ct_registration(composite, 0.482, -0.08977588222411312)
        buf = splats_for_mesh(composite, scale, R, translation, stride=97)
        self.assertEqual(buf.dtype, np.float32)
        self.assertEqual(buf.shape[1], 14)
        self.assertTrue(np.isfinite(buf).all())
        np.testing.assert_allclose(buf[:, 6], 1.0)          # alpha opaque
        np.testing.assert_allclose(buf[:, 10], 1.0)         # quat w (identity)
        np.testing.assert_allclose(buf[:, 11:14], 0.0)      # quat x,y,z
        self.assertTrue((buf[:, 7:10] > 0).all())           # positive sigma
        # rigid + uniform-scale invariance: pairwise distances scale by `scale`
        a, b, cc = buf[:3, 0:3].astype(np.float64)
        d_scene = np.linalg.norm(b - a) + np.linalg.norm(cc - b)
        idx = np.array([0, 97, 194])
        raw = composite[idx]
        d_ct = (np.linalg.norm(raw[1] - raw[0]) + np.linalg.norm(raw[2] - raw[1])) / 1000.0
        # f32 splat positions quantise at ~1e-8 m at these magnitudes
        self.assertAlmostEqual(d_scene, d_ct * scale, places=7)

    def test_layer_buffer_headers_pack(self):
        buf, record = csl.layer_splat_buffer(stride=211)
        self.assertEqual(record["bones"], 25)
        header = struct.pack("<I3f", int(buf.shape[0]), 1.2, 0.0, 0.35)
        self.assertEqual(len(header) + buf.astype(np.float32).tobytes().__len__(),
                         16 + int(buf.shape[0]) * 14 * 4,
                         "byte count must satisfy the engine's /membrane_bin validation")

    def test_bone_color_is_the_assembly_tint_not_a_semantic_label(self):
        self.assertEqual(csl.CT_BONE_COLOR, (0.82, 0.75, 0.60))


class MacaqueSceneBundle(unittest.TestCase):
    def test_bundle_carries_layer_record_without_changing_physics(self):
        # NOTE: compile_macaque currently refuses at the PRE-EXISTING
        # force-model replay drift (model_semantic_replay_mismatch) at the lane
        # base f7ddbd07 -- measured before this lane touched anything. That
        # drift belongs to the concurrent graph lane; this test therefore
        # verifies the ADDITIVE contract at the source level: the extension
        # appends the layer key downstream of the physics compilation and
        # mutates nothing the physics path reads. The moment the graph lane
        # repairs the replay drift, the live compile can be re-enabled here.
        import inspect
        import shutil
        import tempfile
        from tools.science_funnel import macaque_scene
        from tools.science_funnel.common import Refusal
        from tools.creature_graph.store import CreatureGraph
        graph = CreatureGraph.load(str(ROOT / "tools/creature_graph/data/creature_graph.json"))
        scratch = Path(tempfile.mkdtemp(prefix="ct_layer_bundle_"))
        try:
            with self.assertRaises((Refusal, csl.SkeletonLayerRefusal)) as ctx:
                macaque_scene.compile_macaque(graph, scratch)
            self.assertEqual(ctx.exception.code, "model_semantic_replay_mismatch",
                             "the compile must refuse at the PRE-EXISTING force-model replay "
                             "drift (measured at the lane base f7ddbd07), not at anything this "
                             "lane added")
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        source = inspect.getsource(macaque_scene.compile_macaque)
        self.assertIn('bundle["ct_skeleton_layer"]', source)
        self.assertIn('visual_only_no_physics_claim', source)
        # and the layer record itself is independently verified elsewhere
        layer = macaque_scene.measure_falsifier()
        self.assertEqual(layer["schema"], "chimera.ct_skeleton_layer.v1")


class LaneBoundary(unittest.TestCase):
    def test_no_gait_lane_file_is_written_by_this_module(self):
        import hashlib
        watched = [
            ROOT / "ChimeraEngine/engine/gait_controller.hpp",
            ROOT / "tools/science_funnel/gait_scene.py",
            ROOT / "tools/science_funnel/validation/gait_zero_20260919/derive_stance_hold.py",
        ]
        watched += sorted((ROOT / "tools/science_funnel/validation").glob("gait_*"))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in watched if p.is_file()}
        measure_falsifier()
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in watched if p.is_file()}
        self.assertEqual(before, after, "the lane reads gait-lane state, it never writes it")


if __name__ == "__main__":
    unittest.main()
