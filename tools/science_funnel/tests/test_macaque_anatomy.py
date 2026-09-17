import copy,json,struct,tempfile,unittest
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from tools.science_funnel.macaque_anatomy import *
from tools.science_funnel.common import Refusal

class AnatomyContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.model,cls.receipt=parse_source();cls.meshes=world_meshes(cls.model)
 def test_graph_intake_is_idempotent_and_connected(self):
  graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
  a,fragment=build_proposal(graph,self.model,self.receipt);b,again=build_proposal(a,self.model,self.receipt)
  self.assertEqual(a.graph_hash(),b.graph_hash());self.assertEqual(again,{'objects':[],'relations':[]})
  self.assertTrue(a.out_edges('ref.macaque_arm.body.humerus','attached_to'))
 def test_source_inventory_and_units(self):
  self.assertEqual((len(self.model['bodies']),len(self.meshes),len(self.model['coordinates']),len(self.model['muscles'])),(11,7,7,39))
  b=next(x for x in self.meshes if x[0]['name']=='humerus');bounds=np.asarray(b[4]['bounds_m']);self.assertAlmostEqual(bounds[1,1]-bounds[0,1],.139313022,places=9)
  self.assertEqual(b[1]['source_units_to_m'],[.001]*3)
 def test_source_elbow_joint_has_real_offset_and_default(self):
  ulna=next(b for b in self.model['bodies'] if b['name']=='ulna1');self.assertEqual(ulna['joint']['parent_location_m'],[0.,-.125,-.003])
  self.assertAlmostEqual(self.model['coordinates']['elbow_flexion']['default_rad'],np.pi/2,places=7)
 def test_rotation_convention_independent_library(self):
  a=[.21,-.35,.7];np.testing.assert_allclose(frame([0,0,0],a)[:3,:3],Rotation.from_euler('XYZ',a).as_matrix(),atol=2e-15)
 def test_rotations_preserve_dimensions_and_volume(self):
  posed=world_meshes(self.model,values={'shoulder_rotation':.4,'elbow_flexion':1.2,'radial_pronation':.3})
  for (_,_,a,ta,_),(_,_,b,tb,_) in zip(self.meshes,posed):
   np.testing.assert_allclose(np.linalg.norm(a-a[0],axis=1),np.linalg.norm(b-b[0],axis=1),atol=1e-14)
 def test_unknown_pose_and_limits_refuse(self):
  with self.assertRaisesRegex(Refusal,'unknown_coordinate'):pose_frames(self.model,{'tail':1})
  with self.assertRaisesRegex(Refusal,'pose_out_of_range'):pose_frames(self.model,{'elbow_flexion':0})
 def test_cycle_and_missing_parent_refuse(self):
  bad=copy.deepcopy(self.model);bad['bodies'][1]['joint']['parent']='missing'
  with self.assertRaisesRegex(Refusal,'missing_parent'):pose_frames(bad)
  bad['bodies'][1]['joint']['parent']='hand'
  with self.assertRaisesRegex(Refusal,'cyclic_body_hierarchy'):pose_frames(bad)
 def test_concave_polygon_area(self):
  v=np.array([[0,0,0],[2,0,0],[2,2,0],[1,1,0],[0,2,0]],float);t=np.asarray(triangulate_polygon(range(5),v))
  self.assertEqual(len(t),3);self.assertAlmostEqual(mesh_metrics(v,t)['surface_area_m2'],3.)
 def test_repairs_do_not_move_source_points(self):
  for p in (DATA/'Geometry').glob('*.vtp'):
   raw=p.read_bytes();source=numbers(ET.fromstring(raw).findtext('./PolyData/Piece/Points/DataArray')).reshape(-1,3)
   report={};v,t=read_vtp(raw,report);np.testing.assert_array_equal(v[report['source_vertex_to_render_vertex']],source)
 def test_topology_gaps_remain_named(self):
  ms={b['name']:m for b,g,v,t,m in self.meshes};self.assertEqual(ms['radius']['edges_not_shared_twice'],0);self.assertGreater(ms['scapula']['edges_not_shared_twice'],0);self.assertGreater(ms['hand']['edges_not_shared_twice'],0)
  self.assertEqual(len(ms['radius']['processing']['zero_area_polygons_omitted']),1)
 def test_wraps_and_conditions_not_erased(self):
  self.assertEqual(sum(bool(m['wraps']) for m in self.model['muscles']),30)
  self.assertEqual(sum(p['type']=='ConditionalPathPoint' for m in self.model['muscles'] for p in m['points']),1)
  self.assertFalse(any(m['force_runtime_ready'] for m in self.model['muscles']))
 def test_untrusted_geometry_path_refuses(self):
  m=copy.deepcopy(self.model);m['bodies'][1]['geometry'][0]['path']='../escape.vtp'
  with self.assertRaisesRegex(Refusal,'path_escape'):world_meshes(m)
 def test_source_hash_mismatch_refuses(self):
  m=copy.deepcopy(self.model);m['bodies'][1]['geometry'][0]['sha256']='0'*64
  with self.assertRaisesRegex(Refusal,'geometry_pin_drift'):world_meshes(m)

if __name__=='__main__':unittest.main()
