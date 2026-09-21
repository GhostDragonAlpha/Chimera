import unittest
from pathlib import Path
from tools.science_funnel import wiseman_osim as W
from tools.science_funnel.wiseman_osim import *
from tools.science_funnel.common import Refusal,canonical
from tools.science_funnel.macaque_anatomy import pose_frames,parse_source
from tools.creature_graph.store import CreatureGraph

class WisemanOsim4(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.models={t:parse_wiseman(t) for t in TAXA} # one parser, zero taxon branches
  cls.macaque=cls.models['Macaque']
 def test_every_taxon_reconciles_against_its_own_inventory(self): # falsifier A
  for t,m in self.models.items():self.assertEqual(reconcile(m)['match'],'exact')
  mac=reconcile(self.macaque)['parsed']
  self.assertEqual((mac['muscle_count'],mac['path_points'],mac['wrap_surfaces'],mac['body_count'],mac['joint_count']),(36,125,14,10,10))
 def test_round_trip_accounts_every_record(self):
  m=self.macaque;file_bodies=[b for b in m['bodies'] if b.get('origin')!='synthesized_ground']
  self.assertEqual(len(file_bodies)+1,len(m['bodies'])) # exactly one marked synthesized ground, nothing else added
  self.assertEqual(sum(len(b['wrap_objects']) for b in m['bodies']),len(INVENTORY['models']['Macaque']['wrap_surfaces']))
  self.assertEqual(sum(len(mm['points']) for mm in m['muscles']),125)
  self.assertEqual(sum(1 for mm in m['muscles'] if mm['wraps']),INVENTORY['models']['Macaque']['total_wrapped_muscles']) # 14 wrapped muscles (R_RF carries 2 pathwraps -> 15 pathwrap records)
  self.assertEqual(sum(len(b['joint']['axes']) for b in m['bodies'] if b['joint']),3*6+7*1) # pelvis+2 hips: rotation1-3 AND translation1-3 each; 7 pin joints: 1 each
 def test_parse_is_deterministic(self): # falsifier B
  for t,m in self.models.items():self.assertEqual(canonical(m),canonical(parse_wiseman(t)))
 def test_no_taxon_conditionals(self): # falsifier E: every taxon name occurs exactly once, in the TAXA data table, never in a branch
  lines=Path(W.__file__).read_text().splitlines()
  for banned in TAXA:
   hits=[i for i,l in enumerate(lines) if banned in l]
   self.assertEqual(len(hits),1,banned);self.assertTrue(lines[hits[0]].startswith('TAXA='),banned)
 def test_store_proposal_passes_intake_checks(self): # falsifier C
  g=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
  a,fragment=build_proposal(g,self.macaque);b,again=build_proposal(a,self.macaque)
  self.assertEqual(a.check(),[]);self.assertEqual(a.graph_hash(),b.graph_hash());self.assertEqual(again,{'objects':[],'relations':[]})
  self.assertEqual(len(fragment['objects']),1+1+len(self.macaque['bodies'])+len(self.macaque['muscles']))
  self.assertTrue(a.out_edges('ref.wiseman.macaque.muscle.R_AM','attached_to'))
 def test_converted_hierarchy_validated_by_unmodified_3x_kinematics(self):
  frames=pose_frames(self.macaque,{'r_knee_flexion':-.5,'hip_flexion_r':.4})
  pelvis=next(b for b in self.macaque['bodies'] if b['name']=='Pelvis')
  self.assertEqual(pelvis['joint']['type'],'CustomJoint');self.assertEqual(pelvis['joint']['parent'],'ground')
  shank=next(b for b in self.macaque['bodies'] if b['name']=='shank_r')
  self.assertEqual(shank['joint']['type'],'PinJoint');self.assertEqual(shank['joint']['axes'][0]['axis'],[1.,0.,0.])
 def test_placeholder_forces_never_runtime_ready(self):
  for mm in self.macaque['muscles']:
   self.assertTrue(mm['force_all_source_placeholder']);self.assertFalse(mm['force_runtime_ready'])
   self.assertEqual(mm['force_placeholder'],{'max_isometric_force':1.,'optimal_fiber_length':1.,'tendon_slack_length':1.,'pennation_angle_at_optimal':0.})
 def test_guimaraes_name_pairing_matches_preregistration(self):
  report=pairing_report('Macaque');c=report['counts']
  self.assertEqual((c['wiseman_muscles'],c['exact'],c['split_homolog_deferred'],c['unmatched']),(36,28,8,0))
  self.assertEqual(set(report['guimaraes_without_wiseman_record']),{'GemInf','GemSup','ObtExt','ObtInt','PLANT','POP'})
  self.assertEqual({p['guimaraes'] for p in report['split_homolog_deferred']},{'EDL','FDL'})
 def test_muscle_name_set_identical_across_taxa(self):
  sets=[set(mm['name'] for mm in self.models[t]['muscles']) for t in TAXA]
  self.assertTrue(all(s==sets[0] for s in sets))
 def test_pin_drift_and_dispatch_refuse(self):
  with self.assertRaisesRegex(Refusal,'unknown_taxon'):parse_wiseman('Human')
  original=MANIFEST['files'][0]['sha256'];MANIFEST['files'][0]['sha256']='0'*64
  try:
   with self.assertRaisesRegex(Refusal,'source_pin_drift'):pinned_bytes(MANIFEST['files'][0]['path'])
  finally:MANIFEST['files'][0]['sha256']=original
  with self.assertRaisesRegex(Refusal,'unsupported_anatomy_layout'):parse_anatomy(ROOT/'tools/science_funnel/data/macaque_arm')
 def test_parser_lanes_do_not_cross(self):
  with self.assertRaises((Refusal,KeyError)):parse_source(data=DATA) # the 3.x gate still refuses the 4.x deposit (it pins revision 4fb7ddee)
 def test_deposited_noise_is_normalized_on_the_record(self):
  norm=self.macaque['coordinate_normalizations']
  self.assertEqual([n['coordinate'] for n in norm],['r_knee_flexion'])
  self.assertGreater(norm[0]['violation_rad'],0);self.assertEqual(norm[0]['clamped_to_rad'],0.)
  orang=self.models['Orangutan']['coordinates']
  self.assertEqual(orang['hallux_FE_l']['range_source'],'opensim4_class_default_-10pi_10pi')

if __name__=='__main__':unittest.main()
