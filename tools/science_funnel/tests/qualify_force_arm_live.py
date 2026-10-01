"""Qualify native force-bearing anatomy against source FK, loads and controls."""
import argparse,json,time,urllib.request,urllib.error
from pathlib import Path
import numpy as np
from tools.science_funnel.macaque_anatomy import parse_source,world_meshes,rotation

def qualify(runtime):
 info=json.loads(Path(runtime).read_text(encoding='utf-8-sig'));base='http://127.0.0.1:'+str(info['port']);checks=[];scene=json.loads(Path(info['scene']).read_text(encoding='utf-8-sig'));model=parse_source()[0]
 def req(data=None,route='/earth_state'):
  q=urllib.request.Request(base+route,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(q,timeout=8) as r:return json.load(r)
 def ck(name,yes,**d):
  checks.append({'name':name,'pass':bool(yes),'detail':d})
  if not yes:raise AssertionError(name+': '+str(d))
 def send(d):
  s=req(d);ck('command_'+next(iter(d)),s.get('ok'),error=s.get('error'));return s
 def until(test,seconds=4):
  deadline=time.monotonic()+seconds
  while time.monotonic()<deadline:
   s=req()
   if not s.get('ok'):raise AssertionError(s)
   if test(s):return s
   time.sleep(.02)
  raise AssertionError('native deadline: '+str(s))
 try:
  send({'reset':True,'support':True,'power':True,'target_deg':110.,'torque_limit_N_m':.3,'load_N':0.});s=send({'paused':True});q=s['joint']['angle_deg'];w=s['joint']['speed_rad_s'];changed=send({'target_deg':140.});ck('target_is_intent_not_pose',changed['joint']['angle_deg']==q and changed['joint']['speed_rad_s']==w)
  s=send({'reset':True,'support':False,'power':False});s=until(lambda s:s['joint']['angle_deg']<75);ck('cut_power_retains_passive_fall',s['energy']['actuator_work_J']==0 and s['joint']['support_reaction_N']==0)
  send({'reset':True,'support':True});s=until(lambda s:abs(s['joint']['angle_deg']-80)<1e-6);hit=s['ticks'];s=until(lambda s:s['ticks']>hit+20)
  p=scene['arm_dynamics']['parameters'];a=np.array(p['axis']);q=np.deg2rad(s['joint']['angle_deg'])-p['rest_rad'];S=rotation(a,q)@p['first_moment_kg_m'];r=rotation(a,q)@p['hand_offset_m'];g=s['environment']['gravity_m_s2'];expected=g*np.cross(a,S)[1]/np.cross(a,r)[1]
  ck('live_support_load',abs(s['joint']['support_reaction_N']-expected)<1e-8,expected_N=expected,observed_N=s['joint']['support_reaction_N'])
  ck('mount_reaction_closes_static_force',abs(s['exchange']['mount_reaction_force_N'][1]+s['joint']['support_reaction_N']-p['mass_kg']*g)<1e-8)
  s=send({'load_N':2.});old=s['ticks'];s=until(lambda s:s['ticks']>old+5);ck('downward_force_transmits_to_support',abs(s['joint']['support_reaction_N']-expected-2)<1e-8)
  send({'target_deg':20.,'power':True,'load_N':0.});s=until(lambda s:s['joint']['motor_torque_N_m']<-.29);ck('blocked_target_stalls_with_load',abs(s['joint']['angle_deg']-80)<1e-6 and s['joint']['support_reaction_N']>expected+1)
  send({'reset':True,'support':False,'target_deg':130.,'torque_limit_N_m':.03});s=until(lambda s:s['joint']['angle_deg']<60);ck('weak_drive_cannot_lift',abs(s['joint']['motor_torque_N_m'])<=.03+1e-12)
  send({'reset':True,'support':True,'torque_limit_N_m':.3});s=until(lambda s:s['joint']['angle_deg']>110);ck('strong_drive_lifts_same_mass',s['energy']['actuator_work_J']>0 and s['energy']['battery_J']<1)
  s=req();recipe=scene['arm_dynamics']['recipe'];ck('force_boundary_identity',s['attachment_id']==recipe['attachment_id'] and s['support_id']==recipe['support_id'])
  ck('native_energy_availability',s['energy']['battery_usable']==(s['energy']['battery_J']>1e-12))
  snap=req(route='/earth_snapshot');s=snap['state'];native=np.array(snap['vertices']).reshape(-1,9);expected_mesh=np.concatenate([part[2] for part in world_meshes(model,values={'elbow_flexion':np.deg2rad(s['joint']['angle_deg'])})])+scene['scene']['arm_translation_m'];error=np.max(np.abs(native[:len(expected_mesh),:3]-expected_mesh));ck('native_geometry_follows_solved_source_coordinate',error<2e-7,max_vertex_error_m=float(error))
  hand=native[-1080:,:3].mean(axis=0);ck('hand_proxy_matches_force_point',np.max(np.abs(hand-np.array(s['body']['position_m'])))<2e-7)
  ck('live_work_and_store_accounts',abs(s['energy']['balance_error_J'])<1e-9 and abs(s['energy']['store_balance_error_J'])<1e-9)
  s=send({'paused':True});bad=req({'elbow_deg':0});ck('direct_pose_write_refused',bad.get('ok') is False and req()['joint']==s['joint'])
  bad=req({'support':False});ck('moving_boundary_change_refused',bad.get('ok') is False and req()['joint']==s['joint'])
 finally:
  req({'reset':True,'support':True,'power':True,'target_deg':110.,'torque_limit_N_m':.3,'load_N':0.})
 return {'runtime':info,'checks':checks,'scope':'Native one-coordinate force-bearing anatomy, actual field/contact loads and source-geometry oracle; not whole animal or physiological actuation.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--output',required=True);a=p.parse_args();v=qualify(a.runtime);Path(a.output).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':len(v['checks']),'output':a.output}))
