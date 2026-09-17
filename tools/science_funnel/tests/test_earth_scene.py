import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
from tools.science_funnel.earth_scene import *
from tools.science_funnel.common import Refusal

class EarthInputs(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.params,cls.receipt=source_parameters();cls.graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
 def test_source_units(self):
  self.assertEqual(self.params['datum']['semi_major_m'],6378137.)
  self.assertEqual(self.params['atmosphere']['pressure_scale_Pa'],101290.)
  self.assertEqual(self.params['atmosphere']['density_R_J_kg_K'],286.9)
 def test_datum_axes_and_origin(self):
  origin,frame=local_frame(self.params['datum'],0,0,0);np.testing.assert_array_equal(origin,[6378137,0,0]);np.testing.assert_array_equal(frame[:,0],[0,1,0]);np.testing.assert_array_equal(frame[:,1],[1,0,0]);np.testing.assert_array_equal(frame[:,2],[0,0,-1])
 def test_millimetres_survive_global_roundtrip(self):
  for lat in (-90,-35,0,60,90):
   origin,f=local_frame(self.params['datum'],lat,139.7,321.);np.testing.assert_allclose(f.T@f,np.eye(3),atol=4e-16);self.assertAlmostEqual(np.linalg.det(f),1,places=14)
   p=np.array([.0012,.0023,-.0045]);np.testing.assert_allclose(f.T@(origin+f@p-origin),p,atol=2e-9)
 def test_invalid_coordinate_refuses(self):
  for lat,lon,h in [(91,0,0),(0,181,0),(0,0,float('nan'))]:
   with self.assertRaisesRegex(Refusal,'earth_coordinate_range'):local_frame(self.params['datum'],lat,lon,h)
 def test_graph_parameter_tamper_refuses(self):
  g=copy.deepcopy(self.graph);g.get(SOURCE)['physical']['parameters']['atmosphere']['pressure_scale_Pa']=101.29
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(Refusal,'earth_graph_source_drift'):compile_scene(g,d)
 def test_compiler_reuses_force_library_and_arm(self):
  with tempfile.TemporaryDirectory() as d:
   b=compile_scene(self.graph,d);self.assertEqual(b['models']['schema'],'chimera.force_models.v1');self.assertIn('399',b['models']['gravity']);self.assertEqual(b['scene']['tick_hz'],300)
   self.assertEqual(sha(Path(b['arm']['mesh_file']).read_bytes()),b['arm']['mesh_sha256'])
   self.assertEqual(sha(Path(b['arm']['body_file']).read_bytes()),b['arm']['body_sha256'])
 def test_arm_and_environment_are_separate_identities(self):
  self.assertEqual(self.graph.get(RECIPE)['status'],'specified');self.assertEqual(self.graph.get(SOURCE)['status'],'extracted');self.assertEqual(self.graph.get('model.anatomy.macaque_arm')['status'],'extracted')
if __name__=='__main__':unittest.main()
