import unittest,copy,tempfile
from pathlib import Path
from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.coupled_scene import compile_coupled,ROOT,MODEL
from tools.science_funnel.common import Refusal

class CoupledScene(unittest.TestCase):
 def setUp(self):self.g=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
 def compile(self):
  with tempfile.TemporaryDirectory() as d:return compile_coupled(self.g,Path(d))
 def test_source_recipe_compiles(self):
  s=self.compile();self.assertEqual(s['coupled_dynamics']['recipe']['coordinates'],['shoulder_flexion','elbow_flexion']);self.assertIn('optional frictionless rigid hand contact plane',s['scope'])
 def test_contact_defaults_preserve_free_mode(self):
  s=self.compile();r=s['coupled_dynamics']['recipe'];self.assertIs(r['defaults']['contact_enabled'],False);self.assertTrue(isinstance(r['contact_plane_height_m'],float))
 def test_source_mass_mutation_refused(self):
  self.g.get('model.anatomy.macaque_arm')['physical']['model']['bodies'][1]['mass_kg']+=1
  with self.assertRaises(Refusal):self.compile()
 def test_hand_attachment_drift_refused(self):
  r=self.g.get(MODEL)['physical']['contract'];self.g.get(r['attachment_id'])['physical']['local_point_m'][0]+=.01
  with self.assertRaises(Refusal):self.compile()
 def test_unsupported_coordinates_refused(self):
  self.g.get(MODEL)['physical']['contract']['coordinates'].reverse()
  with self.assertRaises(Refusal):self.compile()
 def test_unsupported_timestep_refused(self):
  self.g.get(MODEL)['physical']['contract']['tick_hz']=60
  with self.assertRaises(Refusal):self.compile()
 def test_initial_penetration_refused(self):
  self.g.get(MODEL)['physical']['contract']['contact_plane_height_m']=0.55
  self.g.get('world.earth.patch.coupled_arm_contact_plane')['physical']['height_world_up_m']=0.55
  with self.assertRaises(Refusal) as x:self.compile()
  self.assertEqual(x.exception.code,'coupled_contact_initial_penetration')
 def test_unreachable_plane_refused(self):
  self.g.get(MODEL)['physical']['contract']['contact_plane_height_m']=0.15
  self.g.get('world.earth.patch.coupled_arm_contact_plane')['physical']['height_world_up_m']=0.15
  with self.assertRaises(Refusal) as x:self.compile()
  self.assertEqual(x.exception.code,'coupled_contact_plane_unreachable')
 def test_surface_entity_drift_refused(self):
  self.g.get('world.earth.patch.coupled_arm_contact_plane')['physical']['height_world_up_m']=0.30
  with self.assertRaises(Refusal):self.compile()
if __name__=='__main__':unittest.main()
