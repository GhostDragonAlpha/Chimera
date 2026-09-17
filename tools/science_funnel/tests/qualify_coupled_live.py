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
 defaults=scene['coupled_dynamics']['recipe']['defaults']
 try:
  s=req();ck('owned_runtime_identity',s['scene_sha256']==info['scene_sha256'] and s['graph_hash']==info['graph_hash'] and s['mode']=='native_coupled_arm')
  send(dict(defaults,reset=True));s=send({'paused':True});pose=[(j['angle_deg'],j['speed_rad_s']) for j in s['joints']];s=send({'shoulder_target_deg':-40.,'elbow_target_deg':40.});ck('targets_are_intent',pose==[(j['angle_deg'],j['speed_rad_s']) for j in s['joints']])
  s=send({'reset':True,'power':False});s=until(lambda x:abs(x['joints'][0]['angle_deg'])>1 and x['joints'][1]['angle_deg']<80);ck('cut_power_preserves_passive_motion',s['energy']['actuator_work_J']==0 and abs(s['joints'][0]['angle_deg'])>1 and s['joints'][1]['angle_deg']<80)
  send(dict(defaults,reset=True,elbow_drive=False));s=until(lambda x:x['sim_time_s']>.1);ck('undriven_elbow_moves',s['joints'][1]['motor_torque_N_m']==0 and abs(s['joints'][1]['speed_rad_s'])>.01)
  send(dict(defaults,reset=True,shoulder_target_deg=60.,elbow_target_deg=130.));s=until(lambda x:x['joints'][0]['angle_deg']>5 and x['joints'][1]['angle_deg']>95);ck('both_coordinates_actually_move',s['energy']['battery_J']<2)
  for i in range(2):ck('torque_cap_'+str(i),abs(s['joints'][i]['motor_torque_N_m'])<=s['joints'][i]['torque_limit_N_m']+1e-12)
  snap=req(route='/earth_snapshot');s=snap['state'];native=np.array(snap['vertices']).reshape(-1,9);values={j['name']:np.deg2rad(j['angle_deg']) for j in s['joints']};expected=np.concatenate([part[2] for part in world_meshes(model,values=values)])+scene['scene']['arm_translation_m'];error=float(np.max(np.abs(native[:len(expected),:3]-expected)));ck('rendered_bones_match_independent_source_FK',error<2e-7,max_vertex_error_m=error,vertices=len(expected));error=float(np.max(np.abs(native[-1080:,:3].mean(axis=0)-s['body']['position_m'])));ck('force_marker_matches_native_hand',error<2e-7,max_error_m=error)
  ck('honest_contact_scope',s['contacts']=={'environment':False,'joint_limits':True})
  ck('energy_accounts',max(abs(s['energy'][k]) for k in ['balance_error_J','store_balance_error_J'])<1e-5)
  s=send({'paused':True});bad=req({'elbow_deg':0});ck('direct_pose_refused_atomically',bad.get('ok') is False and req()['joints']==s['joints'])
 finally:req(dict(defaults,reset=True))
 return {'runtime':info,'checks':checks,'scope':'Two coupled native coordinates, force intent, finite ideal actuator store, actual source geometry; fixed mount and no environment collision.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--output',required=True);a=p.parse_args();result=qualify(a.runtime);Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':len(result['checks']),'output':a.output}))
