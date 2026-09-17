import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
from tools.science_funnel.force_arm import *
from tools.science_funnel.common import Refusal

class ForceArmReduction(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'));cls.model=parse_source()[0];cls.bundle=compile_force_arm(cls.graph,cls.temp.name);cls.p=cls.bundle['arm_dynamics']['parameters']
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_effective_mass_excludes_fixed_upstream_bodies(self):
  p=self.p;self.assertAlmostEqual(p['mass_kg'],.203001,places=12)
  names={x['body_id'].split('.')[-1] for x in p['moving_bodies']};self.assertEqual(names,{'ulna1','ulna','radius_jcc','radius','radius1','hand'})
  self.assertNotIn('humerus',names);self.assertGreater(p['inertia_kg_m2'],.001)
 def test_source_inertia_matches_finite_difference_kinetic_energy(self):
  model=self.model;rest=model['coordinates']['elbow_flexion']['default_rad'];eps=1e-6
  for delta in (-1.,0.,.7):
   fs=[pose_frames(model,{'elbow_flexion':rest+delta+h}) for h in (-eps,0,eps)];K=0
   for b in model['bodies']:
    n=b['name'];cm=np.r_[b['mass_center_m'],1];v=((fs[2][n]@cm)-(fs[0][n]@cm))[:3]/(2*eps)
    R=fs[1][n][:3,:3];dR=(fs[2][n][:3,:3]-fs[0][n][:3,:3])/(2*eps);W=R.T@dR;omega=np.array([W[2,1],W[0,2],W[1,0]])
    xx,yy,zz,xy,xz,yz=b['inertia_kg_m2'];I=np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]])
    K+=.5*b['mass_kg']*np.dot(v,v)+.5*omega@I@omega
   self.assertLess(abs(2*K/self.p['inertia_kg_m2']-1),2e-9)
 def test_gravity_gradient_matches_source_COM_motion(self):
  rest=self.p['rest_rad'];a=np.array(self.p['axis']);S=np.array(self.p['first_moment_kg_m']);eps=1e-6
  for q in (-1.,0.,.7):
   U=[]
   for h in (-eps,eps):
    f=pose_frames(self.model,{'elbow_flexion':rest+q+h});U.append(sum(b['mass_kg']*(f[b['name']]@np.r_[b['mass_center_m'],1])[1] for b in self.model['bodies']))
   self.assertAlmostEqual((U[1]-U[0])/(2*eps),np.cross(a,rotation(a,q)@S)[1],places=10)
 def test_unknown_coordinate_and_boundary_drift_refuse(self):
  g=copy.deepcopy(self.graph);g.get(MODEL)['physical']['contract']['coordinate']='wrist_flexion'
  with self.assertRaisesRegex(Refusal,'unsupported_force_arm_coordinate'):compile_force_arm(g,self.temp.name)
  g=copy.deepcopy(self.graph);g.get('world.earth.patch.force_arm_proxy')['physical']['rest_offset_m']=[0,0,0]
  with self.assertRaisesRegex(Refusal,'force_arm_boundary_recipe_drift'):compile_force_arm(g,self.temp.name)
 def test_tensor_symmetric_and_positive(self):
  I=np.array(self.p['inertia_tensor_kg_m2']);a=np.array(self.p['axis']);np.testing.assert_allclose(I,I.T,atol=1e-18);self.assertGreater(np.linalg.eigvalsh(I).min(),0);self.assertAlmostEqual(float(a@I@a),self.p['inertia_kg_m2'],places=15)
 def test_mutated_anatomical_source_is_not_claimed_as_original(self):
  g=copy.deepcopy(self.graph);g.get('model.anatomy.macaque_arm')['physical']['model']['bodies'][-1]['mass_kg']*=2
  with self.assertRaisesRegex(Refusal,'force_arm_source_model_drift'):compile_force_arm(g,self.temp.name)
 def test_inertia_and_hand_proxy_have_correct_units_and_topology(self):
  p=self.p;self.assertGreater(np.linalg.norm(p['hand_offset_m']),.1);self.assertLess(np.linalg.norm(p['hand_offset_m']),.3)
  self.assertEqual(self.bundle['arm_dynamics']['recipe']['schema'],'chimera.force_arm.v1');self.assertEqual(self.graph.get(MODEL)['status'],'specified')
if __name__=='__main__':unittest.main()
