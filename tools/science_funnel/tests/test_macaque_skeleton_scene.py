import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.common import digest
from tools.science_funnel.macaque_skeleton_scene import (
    SCHEMA,
    BUNDLE_KIND,
    CT_PREVIEW,
    FEMUR_BONES,
    FALSIFIER_TOL_M,
    THIGH_M,
    compile_skeleton,
    read_obj,
)

ROOT = Path(__file__).resolve().parents[3]


class SkeletonSceneContract(unittest.TestCase):
    graph = None

    @classmethod
    def setUpClass(cls):
        cls.graph = CreatureGraph.load(str(ROOT / "tools/creature_graph/data/creature_graph.json"))

    def compile_once(self):
        directory = tempfile.TemporaryDirectory()
        bundle = compile_skeleton(self.graph, Path(directory.name))
        return directory, bundle

    def test_bundle_kind_and_schema(self):
        directory, bundle = self.compile_once()
        try:
            self.assertEqual(bundle["schema"], SCHEMA)
            self.assertEqual(bundle["bundle_kind"], BUNDLE_KIND)
            saved = json.loads((Path(directory.name) / "scene.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["scene_sha256"], bundle["scene_sha256"])
            self.assertEqual(digest({k: v for k, v in bundle.items()
                                     if k != "scene_sha256"}),
                             bundle["scene_sha256"])
        finally:
            directory.cleanup()

    def test_twenty_five_bones_from_ct_receipt(self):
        directory, bundle = self.compile_once()
        try:
            self.assertEqual(len(bundle["bones"]), 25)
            self.assertEqual([b["bone"] for b in bundle["bones"]], list(range(1, 26)))
            self.assertEqual(len(bundle["femurs"]), 2)
            for b in bundle["bones"]:
                self.assertIn("preview_sha256", b)
                self.assertIn("full_res_sha256", b)
        finally:
            directory.cleanup()

    def test_mm_to_m_conversion(self):
        directory, bundle = self.compile_once()
        try:
            import json as _json
            receipt = _json.loads((ROOT / "tools/science_funnel/data/morphosource_ct/mesh_receipt.json")
                                  .read_text(encoding="utf-8-sig"))
            meshes = {m["bone"]: m for m in receipt["meshes"]}
            for b in bundle["bones"]:
                v_mm, _t = read_obj(CT_PREVIEW / meshes[b["bone"]]["preview"])
                # Compiler keeps mm source untouched; a scaled femur's span
                # must equal the thigh segment (0.163 m). Non-femur bones are
                # converted mm -> m by x0.001 and recorded with their source
                # mm landmarks; the falsifier confirms the mounted span.
                if b["role"] == "femur":
                    self.assertAlmostEqual(b["joint_span_mm"] / 1000.0 * b["segmental_scale"],
                                           THIGH_M, places=4)
                self.assertGreaterEqual(len(v_mm), b["vertices"])
        finally:
            directory.cleanup()

    def test_femur_falsifier_passes(self):
        directory, bundle = self.compile_once()
        try:
            self.assertTrue(bundle["falsifier"]["passed"])
            self.assertEqual(bundle["falsifier"]["tol_m"], FALSIFIER_TOL_M)
            self.assertEqual(sorted(bundle["falsifier"]["distances_m"]),
                             [str(b) for b in sorted(FEMUR_BONES)])
            for b in FEMUR_BONES:
                d = bundle["falsifier"]["distances_m"][str(b)]
                self.assertLessEqual(d["hip_m"], FALSIFIER_TOL_M)
                self.assertLessEqual(d["knee_m"], FALSIFIER_TOL_M)
                self.assertLessEqual(d["seating_knee_m"], FALSIFIER_TOL_M)
                self.assertLessEqual(d["seating_hip_m"], FALSIFIER_TOL_M)
        finally:
            directory.cleanup()

    def test_scaffold_standing_pose(self):
        directory, bundle = self.compile_once()
        try:
            scaffold = bundle["scaffold"]
            self.assertAlmostEqual(scaffold["hip_height_m"], 0.3307, places=3)
            hip = np.array(scaffold["joints_m"]["hip"])
            knee = np.array(scaffold["joints_m"]["knee"])
            span = float(np.linalg.norm(knee - hip))
            self.assertAlmostEqual(span, THIGH_M, places=6)
            # hip -> knee points forward and down at phi_thigh = 18.83 deg.
            self.assertAlmostEqual(np.degrees(np.arctan2(knee[0], -knee[1])),
                                   18.83, places=1)
        finally:
            directory.cleanup()

    def test_rule_zero_record_is_present_and_measured(self):
        record = self.graph.get("work.creature.macaque_skeleton_layer")
        self.assertIn(record["falsifier"]["status"], ("passing", "tested"))
        self.assertIn("joint span", record["physical"]["contract"]["declared_mappings"][1].lower())
        self.assertIn("condyle", record["physical"]["statement"])

    def test_compiler_emits_stable_sha(self):
        directory, bundle = self.compile_once()
        try:
            bundle2 = compile_skeleton(self.graph, Path(directory.name))
            self.assertEqual(bundle["scene_sha256"], bundle2["scene_sha256"])
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()