"""Check the owned two-coordinate native scene, using source FK as an independent oracle."""
import argparse,json,time,urllib.request
from pathlib import Path
import numpy as np
from tools.science_funnel.macaque_anatomy import parse_source,world_meshes

def qualify(runtime):
 info=json.loads(Path(runtime).read_text(encoding='utf-8-sig'));scene=json.loads(Path(info['scene']).read_text(encoding='utf-8'));base='http://127.0.0.1:'+str(info['port']);checks=[];model=parse_source()[0]
 def req(data=None,route='/earth_state'):
  q=urllib.request.Request(base+route,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(q,timeout=8) as r:return json.load(r)
 def ck(name,ok,**details):
  checks.append({'name':name,'pass':bool(ok),'details':details})
  if not ok:raise AssertionError(checks[-1])
 def send(data):
  s=req(data);ck('command_'+next(iter(data)),s.get('ok'),error=s.get('error'));return s
 def until(test,timeout=4):
  deadline=time.monotonic()+timeout
  while time.monotonic()<deadline:
   s=req()
   if not s.get('ok'):raise AssertionError(s)
   if test(s):return s
   time.sleep(.02)
  raise AssertionError('native deadline: '+str(s))
 defaults=scene['coupled_dynamics']['recipe']['defaults'];plane=scene['coupled_dynamics']['recipe']['contact_plane_height_m']
 try:
  s=req();ck('owned_runtime_identity',s['scene_sha256']==info['scene_sha256'] and s['graph_hash']==info['graph_hash'] and s['mode']=='native_coupled_arm')
  send(dict(defaults,reset=True));s=send({'paused':True});pose=[(j['angle_deg'],j['speed_rad_s']) for j in s['joints']];s=send({'shoulder_target_deg':-40.,'elbow_target_deg':40.});ck('targets_are_intent',pose==[(j['angle_deg'],j['speed_rad_s']) for j in s['joints']])
  s=send({'reset':True,'power':False});s=until(lambda x:abs(x['joints'][0]['angle_deg'])>1 and x['joints'][1]['angle_deg']<80);ck('cut_power_preserves_passive_motion',s['energy']['actuator_work_J']==0 and abs(s['joints'][0]['angle_deg'])>1 and s['joints'][1]['angle_deg']<80)
  send(dict(defaults,reset=True,elbow_drive=False));s=until(lambda x:x['sim_time_s']>.1);ck('undriven_elbow_moves',s['joints'][1]['motor_torque_N_m']==0 and abs(s['joints'][1]['speed_rad_s'])>.01)
  send(dict(defaults,reset=True,shoulder_target_deg=60.,elbow_target_deg=130.));s=until(lambda x:x['joints'][0]['angle_deg']>5 and x['joints'][1]['angle_deg']>95);ck('both_coordinates_actually_move',s['energy']['battery_J']<2)
  for i in range(2):ck('torque_cap_'+str(i),abs(s['joints'][i]['motor_torque_N_m'])<=s['joints'][i]['torque_limit_N_m']+1e-12)

  # Contact slice: default off, toggle refuses without reset, presses and stalls with it on.
  s=req();ck('contact_default_off',s['contacts']=={'environment':False,'joint_limits':True} and s['contact']['enabled'] is False and s['contact']['friction'] is False and s['contact']['grasp'] is False)
  send({'paused':True});before=req();bad=req({'contact_enabled':True});after=req();ck('contact_toggle_without_reset_refused',bad.get('ok') is False and after['joints']==before['joints'] and after['config']['contact_enabled'] is False);send({'paused':False})
  send({'contact_enabled':True,'reset':True});s=until(lambda x:x['sim_time_s']>.05);ck('contact_mode_engaged',s['contacts']=={'environment':True,'joint_limits':True} and s['config']['contact_enabled'] is True and abs(s['contact']['plane_world_up_m']-plane)<1e-12)
  send({'shoulder_target_deg':20.,'elbow_target_deg':20.});s=until(lambda x:x['contact']['touching'] and x['contact']['reaction_N']>0.05,timeout=8)
  ck('contact_presses_plane',s['contact']['gap_m']>=-1e-5 and s['contact']['reaction_N']>0.05)
  ck('contact_obstructed_target_stalls',s['joints'][1]['angle_deg']>30. and abs(s['joints'][1]['angle_deg']-20.)>1.)
  ck('contact_energy_accounts',max(abs(s['energy'][k]) for k in ['balance_error_J','store_balance_error_J'])<1e-5)
  snap=req(route='/earth_snapshot');state=snap['state'];native=np.array(snap['vertices']).reshape(-1,9)
  on_plane=int(np.sum(np.abs(native[:,1]-plane)<1e-6));ck('contact_plane_rendered_at_recipe_height',on_plane>=10,vertices_on_plane=on_plane)
  values={j['name']:np.deg2rad(j['angle_deg']) for j in state['joints']};expected=np.concatenate([part[2] for part in world_meshes(model,values=values)])+scene['scene']['arm_translation_m'];error=float(np.max(np.abs(native[:len(expected),:3]-expected)));ck('rendered_bones_match_independent_source_FK',error<2e-7,max_vertex_error_m=error,vertices=len(expected));error=float(np.max(np.abs(native[-1080:,:3].mean(axis=0)-state['body']['position_m'])));ck('force_marker_matches_native_hand',error<2e-7,max_error_m=error)
  ck('contact_gap_matches_fk_hand',(state['body']['position_m'][1]-state['contact']['proxy_radius_m'])-plane-state['contact']['gap_m']<1e-9)

  send({'power':False,'reset':True});worst_gap=1.;deadline=time.monotonic()+8
  while time.monotonic()<deadline:
   s=req();worst_gap=min(worst_gap,s['contact']['gap_m'])
   if abs(s['joints'][0]['speed_rad_s'])<.02 and abs(s['joints'][1]['speed_rad_s'])<.02 and s['sim_time_s']>1.:break
   time.sleep(.02)
  ck('contact_powercut_lands_and_settles',worst_gap>=-1e-5 and s['contact']['gap_m']>=-1e-5 and abs(s['joints'][1]['speed_rad_s'])<.05 and s['contact']['touching'],worst_gap_m=worst_gap)
  ck('contact_passive_no_created_energy',s['energy']['actuator_work_J']==0 and s['energy']['contact_impact_heat_J']>0 and max(abs(s['energy'][k]) for k in ['balance_error_J','store_balance_error_J'])<1e-5,contact_impact_heat_J=s['energy']['contact_impact_heat_J'])

  # Coulomb friction: mu=0 inert; live mu control without reset; cone, heat, hold.
  send({'contact_enabled':True,'reset':True});s=until(lambda x:x['sim_time_s']>.05)
  ck('friction_zero_mu_inert',s['contact']['friction_mu']==0 and s['contact']['friction_force_N']==0 and s['energy']['friction_heat_J']==0)
  send({'contact_friction':0.8});s=req();ck('friction_live_control_no_reset',s['ok'] and s['config']['contact_friction']==0.8 and s['contact']['friction_mu']==0.8 and s['sim_time_s']>.05)
  send({'shoulder_target_deg':20.,'elbow_target_deg':20.});s=until(lambda x:x['contact']['touching'] and x['energy']['friction_heat_J']>0,timeout=8)
  ck('friction_press_slides_and_dissipates',s['contact']['mode'] in ('slide','stick') and s['energy']['friction_heat_J']>0)
  s=until(lambda x:abs(x['joints'][0]['speed_rad_s'])<.02 and abs(x['joints'][1]['speed_rad_s'])<.02 and x['sim_time_s']>1,timeout=8)
  ck('friction_cone_and_accounts',abs(s['contact']['friction_force_N'])<=s['contact']['friction_mu']*s['contact']['reaction_N']+1e-9 and max(abs(s['energy'][k]) for k in ['balance_error_J','store_balance_error_J'])<1e-5,friction_heat_J=s['energy']['friction_heat_J'])

  s=send(dict(defaults,reset=True));ck('contact_restore_free_mode',s['contacts']=={'environment':False,'joint_limits':True} and s['config']['contact_enabled'] is False and s['config']['contact_friction']==0)
  ck('honest_contact_scope',s['contacts']=={'environment':False,'joint_limits':True})
  ck('energy_accounts',max(abs(s['energy'][k]) for k in ['balance_error_J','store_balance_error_J'])<1e-5)
  s=send({'paused':True});bad=req({'elbow_deg':0});ck('direct_pose_refused_atomically',bad.get('ok') is False and req()['joints']==s['joints'])
 finally:req(dict(defaults,reset=True))
 return {'runtime':info,'checks':checks,'scope':'Two coupled native coordinates, force intent, finite ideal actuator store, actual source geometry, fixed mount and an optional frictionless rigid hand contact plane (off by default; toggle resets). No friction, grasp, free root or whole-animal claim.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--output',required=True);a=p.parse_args();result=qualify(a.runtime);Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':len(result['checks']),'output':a.output}))
