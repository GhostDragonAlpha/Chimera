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
  s=self.compile();self.assertEqual(s['coupled_dynamics']['recipe']['coordinates'],['shoulder_flexion','elbow_flexion']);self.assertIn('no environment collision',s['scope'])
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
if __name__=='__main__':unittest.main()
