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
  s=self.compile();self.assertEqual(s['coupled_dynamics']['recipe']['coordinates'],['shoulder_flexion','elbow_flexion']);self.assertIn('optional frictionless-to-Coulomb hand contact plane',s['scope'])
 def test_contact_defaults_preserve_free_mode(self):
  s=self.compile();r=s['coupled_dynamics']['recipe'];self.assertIs(r['defaults']['contact_enabled'],False);self.assertEqual(r['defaults']['contact_friction'],0.0);self.assertTrue(isinstance(r['contact_plane_height_m'],float))
 def test_friction_out_of_range_refused(self):
  self.g.get(MODEL)['physical']['contract']['defaults']['contact_friction']=1.5
  with self.assertRaises(Refusal) as x:self.compile()
  self.assertEqual(x.exception.code,'coupled_friction_flag_invalid')
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

 # ---- terrain-derived contact plane (work.environment.terrain wiring_20260918) ----
 # Reference identity of the DEFAULT scene. The scene bundle bakes absolute
 # output-dir and worktree paths AND a self-referential scene_sha256 (a
 # function of those paths, not of physics); the honest identity drops the
 # self-hash and normalizes both paths before canonical digesting. The
 # falsifier it pins: the wiring code must not move the default world.
 # Re-pin ONLY deliberately, when an admitted record legitimately advances
 # the scene, and cite it, re-proving exact same-dir byte identity pre-code
 # vs post-code. Verification lineage: byte-identical at the original base
 # (scene.json sha256 9947d074... at store 319fe2af...) and re-proven after
 # the second upstream integration (7c784f09... at store ca68dc9c..., master
 # 0b8d80d5), whose graph_hash is the ONLY delta in the scene.
 # Re-pinned 2026-09-18 by lane seven-coord-complete (GLM 5.3): admission of
 # model.dynamics.coupled_arm7 (the work.dynamics.seven_coordinate_lift_packet
 # implementation) rebuilt the graph; the normalized diff of the scene
 # compiled pre- vs post-admission shows the ONLY deltas are graph_hash
 # (also inside the graph_file name) and the self-referential scene_sha256
 # -- no physics, recipe, model or source bytes moved. Old pin: a7b36b53
 # 1f20e64da4119ad09ebb40448c17dfbc2c2d31489ac0160fb2513a52.
 DEFAULT_SCENE_PORTABLE_SHA256='ea6dc08b77773fb286ac930940566c3fbe833782ebf3df160107068d15615521'
 CAYO_H_ELLIPSOIDAL_M=-42.82679794555668
 def portable_digest(self,bundle,out_dir):
  from tools.science_funnel.common import digest
  root=str(ROOT.resolve());out=str(Path(out_dir).resolve())
  def norm(v):
   if isinstance(v,str):return v.replace(out,'<OUT>').replace(root,'<ROOT>')
   if isinstance(v,list):return [norm(x) for x in v]
   if isinstance(v,dict):return {k:norm(x) for k,x in v.items() if k!='scene_sha256'}
   return v
  return digest(norm(bundle))
 def opt_in(self,height=CAYO_H_ELLIPSOIDAL_M,source='terrain_cayo_20260917',coherent=True):
  r=self.g.get(MODEL)['physical']['contract'];r['contact_plane_height_source']=source
  if coherent:self.g.get(r['contact_plane_id'])['physical']['height_world_up_m']=height
 def test_default_scene_bit_identical(self):
  with tempfile.TemporaryDirectory() as d:
   s=compile_coupled(self.g,Path(d))
   self.assertEqual(self.portable_digest(s,d),self.DEFAULT_SCENE_PORTABLE_SHA256)
 def test_terrain_source_unknown_refused(self):
  self.opt_in(source='terrain_luquillo_20260917',coherent=False)
  with self.assertRaises(Refusal) as x:self.compile()
  self.assertEqual(x.exception.code,'coupled_contact_plane_source_unknown')
 def test_terrain_source_opts_in_and_sets_plane(self):
  self.opt_in()
  with tempfile.TemporaryDirectory() as d:
   s=compile_coupled(self.g,Path(d));r=s['coupled_dynamics']['recipe']
   self.assertEqual(r['contact_plane_height_m'],self.CAYO_H_ELLIPSOIDAL_M)
   p=s['coupled_dynamics']['contact_plane_terrain_provenance']
   self.assertEqual(p['source'],'terrain_cayo_20260917');self.assertEqual(p['patch'],'cayo_santiago_patch');self.assertEqual(p['height_world_up_m'],self.CAYO_H_ELLIPSOIDAL_M)
   self.assertIs(p['plane_reachable'],False);self.assertIn('reset_gap_m',p['gap_scan_m'])
   self.assertNotEqual(self.portable_digest(s,d),self.DEFAULT_SCENE_PORTABLE_SHA256)
 def test_terrain_opt_in_coherence_required(self):
  # key set but the surface entity left authored: the incoherent graph refuses
  self.opt_in(coherent=False)
  with self.assertRaises(Refusal) as x:self.compile()
  self.assertEqual(x.exception.code,'coupled_contact_surface_drift')
 def test_terrain_opt_in_stored_recipe_not_mutated(self):
  contract=self.g.get(MODEL)['physical']['contract'];self.opt_in()
  self.compile()
  self.assertIs(contract['defaults']['contact_enabled'],False)
  self.assertEqual(contract['contact_plane_height_m'],0.35) # the compile copy changed, the store did not
 def test_terrain_pin_and_value_resolve_live(self):
  # the pinned reduction result on disk hashes to its receipt pin right now,
  # and the resolver returns exactly the recorded Cayo ellipsoidal height
  import hashlib
  from tools.science_funnel import coupled_scene as cs
  value,spec,receipt=cs.terrain_plane_height('terrain_cayo_20260917')
  self.assertEqual(value,self.CAYO_H_ELLIPSOIDAL_M)
  raw=(cs.TERRAIN_RECEIPT_DIR/'reduction_result.json').read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),receipt['artifacts']['reduction_result.json'])
 if __name__=='__main__':unittest.main()
