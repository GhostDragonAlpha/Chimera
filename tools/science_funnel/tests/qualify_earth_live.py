"""Live geometry and field check for the private run_earth.ps1 runtime."""
import argparse,json,time,urllib.request,urllib.error
from pathlib import Path
import numpy as np

def qualify(runtime):
 info=json.loads(Path(runtime).read_text(encoding='utf-8-sig'));base='http://127.0.0.1:'+str(info['port']);checks=[]
 def req(data=None,route='/earth_state',raw=None):
  request=urllib.request.Request(base+route,data=raw if raw is not None else None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(request,timeout=8) as r:return json.load(r)
  except urllib.error.HTTPError as e:return json.load(e)
 def check(name,ok,**detail):
  checks.append({'name':name,'pass':bool(ok),'detail':detail})
  if not ok:raise AssertionError(name+': '+str(detail))
 def until(predicate,seconds=3):
  deadline=time.monotonic()+seconds
  while time.monotonic()<deadline:
   s=req()
   if predicate(s):return s
   time.sleep(.025)
  raise AssertionError('native state deadline')
 def send(data):
  s=req(data);check('command_'+next(iter(data)),s.get('ok'),response_error=s.get('error'));return s
 try:
  s=send({'air':False,'slope_deg':0,'wind_m_s':0,'friction':.4,'altitude_m':0});check('private_scene_identity',s['scene_sha256']==info['scene_sha256'])
  initial=np.array(s['body']['position_m']);g=s['environment']['gravity_m_s2'];send({'release':True})
  snap=req(route='/earth_snapshot');s=snap['state'];t=s['sim_time_s'];expected=initial+np.array([0,-.5*g*t*t,0]);p=np.array(s['body']['position_m']);check('live_vacuum_freefall',s['phase']=='flight' and np.max(np.abs(p-expected))<1e-9,time_s=t,error_m=float(np.max(np.abs(p-expected))))
  mesh=np.array(snap['vertices']).reshape(-1,9);sphere=mesh[2761+12*12*6+6:,:3];center=sphere.mean(axis=0);check('native_mesh_matches_snapshot_body',np.max(np.abs(center-p))<2e-7,error_m=float(np.max(np.abs(center-p))))
  s=until(lambda s:s['phase']=='contact');impact_time=s['sim_time_s'];s=until(lambda s:s['sim_time_s']>=impact_time+.05);check('live_settled_support_load',abs(s['body']['normal_force_N']-s['body']['mass_kg']*g)<1e-12)
  check('live_energy_account',abs(s['energy']['balance_error_J'])<1e-12,error_J=s['energy']['balance_error_J']);check('vacuum_disables_convective_heat',s['body']['temperature_K']==295 and s['energy']['heat_to_air_J']==0)
  held=send({'reset':True});before=req();bad=req(raw=b'{"wind_m_s":1,"wind_m_s":2}');after=req();check('duplicate_control_refuses',bad.get('ok') is False and before['environment']==after['environment'] and before['body']==after['body'])
  bad=req({'altitude_m':11000});check('out_of_range_refuses',bad.get('ok') is False and req()['environment']==before['environment'])
  raised=send({'elbow_deg':20});check('live_hand_attachment_moves',np.linalg.norm(np.array(raised['body']['position_m'])-np.array(held['body']['position_m']))>.01)
  s=send({'air':True,'altitude_m':10000});check('altitude_changes_air_and_gravity',s['environment']['density_kg_m3']<.5 and s['environment']['gravity_m_s2']<g and s['held'] and s['sim_time_s']==0)
  send({'release':True});s=until(lambda s:s['sim_time_s']>.5);check('native_air_cools_sample',s['environment']['temperature_K']<s['body']['temperature_K']<295)
  check('live_heat_account',abs(s['energy']['heat_to_air_J']+s['energy']['thermal_energy_change_J'])<1e-10)
  s=send({'paused':True});time.sleep(.08);a=req();check('paused_preserves_simulation_time',s['sim_time_s']==a['sim_time_s'])
 finally:
  req({'reset':True});req({'elbow_deg':0});req({'air':True,'altitude_m':0,'slope_deg':0,'wind_m_s':0,'friction':.4})
 return {'runtime':info,'checks':checks,'scope':'Native Earth boundary reference, streamed geometry and controls; not whole planet, weather or force-driven monkey.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--output',required=True);a=p.parse_args();res=qualify(a.runtime);Path(a.output).write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':len(res['checks']),'output':a.output}))
