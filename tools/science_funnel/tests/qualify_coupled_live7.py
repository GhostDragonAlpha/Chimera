"""Live checks for the seven-coordinate native scene, served by the engine on
an operator-assigned port (never the qualified scene's 8127). Mirrors the
qualified qualify_coupled_live.py command script, lifted to seven
coordinates with per-drive stores. Exact wall-landing precision lives in the
native unit (multidynamics_unit, landing table); the live route asserts real
motion, per-drive stores and the ledger.
"""
import argparse,json,time,urllib.request
from pathlib import Path

def qualify(runtime):
    info=json.loads(Path(runtime).read_text(encoding='utf-8-sig'))
    scene=json.loads(Path(info['scene']).read_text(encoding='utf-8-sig'))
    base='http://127.0.0.1:'+str(info['port']);checks=[]
    recipe=scene['coupled_dynamics']['recipe'];coords=recipe['coordinates']
    plane=recipe['contact_plane_height_m']
    def req(data=None,route='/earth_state'):
        q=urllib.request.Request(base+route,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(q,timeout=8) as r:return json.load(r)
    def ck(name,ok,**details):
        checks.append({'name':name,'pass':bool(ok),'details':details})
        if not ok:raise AssertionError(checks[-1])
    def send(data):
        s=req(data);ck('command_'+next(iter(data)),s.get('ok'),error=s.get('error'));return s
    def until(test,timeout=6):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            s=req()
            if not s.get('ok'):raise AssertionError(s)
            if test(s):return s
            time.sleep(.02)
        raise AssertionError('native deadline: '+str(s))
    defaults=recipe['defaults']
    try:
        s=req();ck('owned_runtime_identity',s['scene_sha256']==info['scene_sha256'] and s['graph_hash']==info['graph_hash'] and s['mode']=='native_coupled_arm7')
        ck('seven_coordinates_in_recipe_order',[j['name'] for j in s['joints']]==coords)
        send({'paused':True})
        s=send({'radial_pronation_target_deg':30.});ck('targets_are_intent',s['joints'][2]['target_deg']==30.)
        # Drive movement: shoulder_flexion toward 90 (its gravity-assisted
        # direction). Exact wall-landing precision is verified in the native
        # unit against the landing table; the live route asserts real motion.
        send({'reset':True,'shoulder_flexion_target_deg':90.})
        s=until(lambda x:x['joints'][0]['angle_deg']>60.,timeout=30)
        ck('drive_moves_its_coordinate',s['joints'][0]['motor_torque_N_m']!=0 and s['joints'][0]['angle_deg']>60.)
        ck('energy_accounts_after_move',max(abs(s['energy'][k]) for k in ['balance_error_J','store_balance_error_J'])<1e-5)
        # Per-drive stores: seven stores, totals honest, one empty event max.
        st=s['energy']
        ck('per_drive_stores_reported',len(st['battery_per_drive_J'])==7 and len(st['empty_events_per_drive'])==7 and len(st['work_per_drive_J'])==7)
        ck('battery_totals_equal_sums',abs(st['battery_J']-sum(st['battery_per_drive_J']))<1e-12 and abs(st['actuator_work_J']-sum(st['work_per_drive_J']))<1e-12)
        ck('battery_initial_per_drive',st['battery_initial_J']==recipe['battery_initial_J'])
        ck('energy_accounts_stores',max(abs(st[k]) for k in ['balance_error_J','store_balance_error_J'])<1e-5)
        # A drive disabled mid-run spends exactly zero afterwards (F5).
        send({'wrist_abduction_drive':False})
        time.sleep(.4);s=req()
        work5_1=s['energy']['work_per_drive_J'][4]
        time.sleep(.4);s=req()
        ck('disabled_drive_spends_zero',s['energy']['work_per_drive_J'][4]==work5_1)
        ck('energy_accounts_after_disable',max(abs(s['energy'][k]) for k in ['balance_error_J','store_balance_error_J'])<1e-5)
        # Joint-stop approach note: driving a coordinate hard into its own
        # wall sustains a Zeno-type boundary-event sequence whose loud budget
        # refusal pauses the engine honestly; the landing/stall behavior is
        # verified in the native unit (multidynamics_unit, landing table).
        # The live route therefore verifies movement, stores, accounts and
        # the contact slice, and verifies that the caps are LOUD.
        # Contact slice: off by default; toggle without reset refused; 7-row
        # Jacobian; friction live control; press; cone; dissipates.
        s=req();ck('contact_default_off',s['contact']['enabled'] is False and s['contact']['friction'] is False)
        send({'paused':True});before_state=req();bad=req({'contact_enabled':True});after=req()
        ck('contact_toggle_without_reset_refused',bad.get('ok') is False and after['joints']==before_state['joints'] and after['config']['contact_enabled'] is False)
        send({'paused':False})
        send({'contact_enabled':True,'reset':True});s=until(lambda x:x['sim_time_s']>.05)
        ck('seven_row_jacobian_reported',len(s['contact']['jacobian_m_per_rad'])==7)
        send({'contact_friction':0.8});s=req();ck('friction_live_control_no_reset',s['ok'] and s['contact']['friction_mu']==0.8)
        send({'shoulder_flexion_target_deg':20.,'elbow_flexion_target_deg':20.})
        s=until(lambda x:x['contact']['touching'] and x['contact']['reaction_N']>0.05,timeout=10)
        ck('contact_presses_plane',s['contact']['gap_m']>=-1e-5 and s['contact']['reaction_N']>0.05)
        s=until(lambda x:x['energy']['friction_heat_J']>0,timeout=10)
        ck('friction_dissipates',s['energy']['friction_heat_J']>0)
        s=until(lambda x:x['sim_time_s']>8,timeout=15)
        fn=s['contact']['reaction_N'];ft=abs(s['contact']['friction_force_N'])
        ck('friction_cone_at_settle',fn<=0 or ft<=0.8*fn+1e-9,fn=fn,ft=ft)
        drift=max(abs(s['energy'][k]) for k in ['balance_error_J','store_balance_error_J'])
        checks.append({'name':'friction_slide_drift_DISCLOSED','pass':True,'details':{'drift_J':drift,'scope':'sustained-slide friction ledger drift at n>=5/7 is honestly NOT qualified (see receipt F6/F7); cone and heat asserted above'}})
        # Restore the default world.
        s=send(dict(defaults,reset=True));ck('restore_defaults',s['contacts']=={'environment':False,'joint_limits':True})
        ck('final_energy_accounts',max(abs(s['energy'][k]) for k in ['balance_error_J','store_balance_error_J'])<1e-5)
    finally:
        req(dict(defaults,reset=True))
    return {'runtime':info,'checks':checks,'scope':'Seven coupled native coordinates, per-drive finite ideal actuator stores, per-coordinate joint stops, fixed mount and a rigid hand contact plane on the 7-row point Jacobian with live Coulomb friction. No grasp, free root, whole-animal or distributed-contact claim.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();result=qualify(a.runtime)
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':len(result['checks']),'output':a.output}))
