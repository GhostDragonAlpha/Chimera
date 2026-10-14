import json
import tempfile
import unittest
from pathlib import Path

from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.macaque_scene import TERRAIN_HEIGHT_M, compile_macaque

ROOT = Path(__file__).resolve().parents[3]


class MacaqueSceneContract(unittest.TestCase):
    def test_bundle_kind_terrain_and_support_contract(self):
        graph = CreatureGraph.load(str(ROOT / "tools/creature_graph/data/creature_graph.json"))
        with tempfile.TemporaryDirectory() as directory:
            bundle = compile_macaque(graph, directory)
            self.assertEqual(bundle["bundle_kind"], "coupled_macaque_scene")
            self.assertEqual(bundle["scene_kind"], "coupled_macaque_scene")
            self.assertEqual(bundle["terrain"]["height_world_up_m"], TERRAIN_HEIGHT_M)
            self.assertEqual(bundle["coupled_free_dynamics"]["recipe"]["contact_plane_height_m"], TERRAIN_HEIGHT_M)
            self.assertEqual(len(bundle["coupled_free_dynamics"]["recipe"]["contact_points"]), 3)
            geometry = list((ROOT / "tools/science_funnel/data/macaque_arm/Geometry").glob("*.vtp"))
            self.assertEqual(len(geometry), 7)
            self.assertTrue(Path(bundle["page_file"]).name == "earth.html")
            saved = json.loads((Path(directory) / "scene.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["scene_sha256"], bundle["scene_sha256"])

    def test_rule_zero_record_is_present(self):
        graph = CreatureGraph.load(str(ROOT / "tools/creature_graph/data/creature_graph.json"))
        record = graph.get("work.creature.macaque_scene")
        self.assertEqual(record["falsifier"]["status"], "untested")
        self.assertIn("standing", record["physical"]["prediction"])
        self.assertIn("knock", record["physical"]["prediction"])
        self.assertIn("gravity off", record["physical"]["prediction"])


if __name__ == "__main__":
    unittest.main()
