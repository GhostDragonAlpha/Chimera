"""Adverse controls for the real downloaded-data -> graph -> native scene path."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.science_funnel.common import Refusal
from tools.science_funnel.graph import graph_from
from tools.science_funnel.surface_scene import DATA, build, compile_scene, frame3
from tools.science_funnel.adapters import coolprop_surface

class SurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.out=Path(cls.tmp.name)/"scene"
        cls.result=build(cls.out)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def graph(self): return graph_from(self.out/"surface_graph.json")
    def test_real_sources_compile_after_graph_reload(self):
        scene=compile_scene(self.graph())
        self.assertEqual(len(scene["vertices_m"]),441)
        self.assertEqual(len(scene["triangles"]),800)
        self.assertEqual(scene["graph_hash"],self.result["graph_hash"])
        values={m["name"]:m["gamma_N_m"] for m in scene["materials"]}
        self.assertAlmostEqual(values["Water"],0.07205503890847453,places=14)
        self.assertAlmostEqual(values["Ethanol"],0.021884404128241063,places=14)
    def test_source_byte_change_refuses_old_pin(self):
        import shutil
        fake=Path(self.tmp.name)/"tampered";shutil.copytree(DATA,fake,dirs_exist_ok=True)
        with (fake/"Water.json").open("ab") as f:f.write(b" ")
        with patch("tools.science_funnel.surface_scene.DATA",fake):
            with self.assertRaisesRegex(Refusal,"download_pin_drift"):build(Path(self.tmp.name)/"rejected")
    def test_missing_material_edge_refuses(self):
        g=self.graph();g.relations[:]=[r for r in g.relations if not(r["src"]=="surface.science_interface" and r["rel"]=="uses_material")]
        with self.assertRaisesRegex(Refusal,"missing_material_binding"):compile_scene(g)
    def test_missing_law_edge_refuses(self):
        g=self.graph();g.relations[:]=[r for r in g.relations if not(r["src"]=="surface.science_interface" and r["rel"]=="uses_model")]
        with self.assertRaisesRegex(Refusal,"missing_law_binding"):compile_scene(g)
    def test_collinear_anchors_refuse(self):
        with self.assertRaisesRegex(Refusal,"collinear_anchors"):frame3([[0,0,0],[1,0,0],[2,0,0]])
    def test_nonfinite_anchors_refuse(self):
        with self.assertRaisesRegex(Refusal,"nonfinite_anchor"):frame3([[0,0,0],[1,0,0],[0,float("inf"),0]])
    def test_semantic_units_refuse(self):
        g=self.graph();mid=g.get("material.science_surface.water")
        g.get(mid["physical"]["surface_tension_record"])["science_funnel"]["payload"]["quantity"]="stiffness"
        with self.assertRaisesRegex(Refusal,"surface_tension_units"):compile_scene(g)
    def test_changed_coefficient_refuses_original_record_id(self):
        g=self.graph();mid=g.get("material.science_surface.water")
        g.get(mid["physical"]["surface_tension_record"])["science_funnel"]["payload"]["value_si"]*=2
        with self.assertRaisesRegex(Refusal,"assertion_identity_mismatch"):compile_scene(g)
    def test_unqualified_temperature_refuses(self):
        with self.assertRaisesRegex(Refusal,"surface_temperature_not_qualified"):
            coolprop_surface((DATA/"Water.json").read_bytes(),{"temperature_K":280},DATA/"Water.json")
    def test_authored_triangle_frame(self):
        s=compile_scene(self.graph())
        self.assertEqual(s["normal"],[0,1,0])
        self.assertEqual(len(s["pinned"]),80)
        self.assertAlmostEqual(sum(s["probe_weights"]),1,places=14)
        self.assertTrue(all(s["probe_weights"][i]==0 for i in s["pinned"]))
        self.assertEqual(s["camera"],[2.8,.25,.72,0,1.15,0,0,0])
if __name__=="__main__":unittest.main()
