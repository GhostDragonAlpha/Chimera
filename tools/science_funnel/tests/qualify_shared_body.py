"""Qualify only the private shared-body reference scene created by run_creature.ps1."""
import argparse, json, struct, time, urllib.request
from pathlib import Path
import numpy as np

def qualify(runtime):
    info=json.loads(Path(runtime).read_text(encoding='utf-8-sig'))
    base='http://127.0.0.1:'+str(info['engine_port'])
    game='http://127.0.0.1:'+str(info['game_port'])
    def request(route, data=None, binary=False, host=base):
        req=urllib.request.Request(host+route,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=12) as r: raw=r.read()
        return raw if binary else json.loads(raw)
    def verts():
        raw=request('/verts',binary=True);n,=struct.unpack_from('<I',raw)
        assert len(raw)==4+36*n
        return np.frombuffer(raw,dtype='<f4',offset=4).reshape(n,9).copy()
    def advance():
        tick=request('/tick_state')['ticks'];end=time.monotonic()+6
        while time.monotonic()<end:
            if request('/tick_state')['ticks']>=tick+2:return
            time.sleep(.02)
        raise AssertionError('native tick stalled')
    checks=[]
    def check(name,ok,**detail):
        checks.append(dict(name=name,pass_=bool(ok),detail=detail))
        if not ok:raise AssertionError(name)
    state=request('/tick_state')
    check('private_shared_body',state['body_model']=='JNT3_hierarchical' and state['n_cells']==2)
    check('proxy_uses_selected_engine',request('/api/state',host=game)['body_model']==state['body_model'])
    request('/tick_touch_clear',{});request('/tick_pose',{'joint':'hip_L','deg':0});request('/tick_pose',{'joint':'knee_L','deg':0});advance()
    rest=verts();inventory=state['w_sum']
    try:
        for name,angle in [('hip_L',20),('knee_L',25)]:
            check('pose_'+name,request('/api/pose',{'joint':name,'deg':angle},host=game)['ok'])
        advance();posed=verts();dist=np.linalg.norm(posed[:,:3]-rest[:,:3],axis=1);i=int(dist.argmax())
        check('surface_moves_through_api',dist[i]>.15,max_displacement_m=float(dist[i]))
        check('pose_inventory',request('/tick_state')['w_sum']==inventory)
        refused=request('/joint',{'joint':13,'deg':0})
        check('competing_writer_refused',refused.get('ok') is False and refused.get('error')=='shared_body_owns_surface')
        advance();check('refusal_preserves_pose',np.array_equal(verts()[:,:3],posed[:,:3]))
        check('touch_current_surface',request('/api/touch_hit',{'hit':posed[i,:3].tolist(),'force_n':200},host=game)['ok'])
        advance();pressed=verts();inward=float(-np.dot(pressed[i,:3]-posed[i,:3],posed[i,3:6]));expected=200/(4*np.pi*4000)
        check('native_press_displacement',abs(inward-expected)<2e-6,inward_m=inward,expected_m=float(expected))
        check('press_inventory',request('/tick_state')['w_sum']==inventory)
        # Restore the private snapshot to test replay and leave an unpressed rest body.
        reply=request('/session',{'op':'restore'});advance();after=request('/tick_state')
        check('private_snapshot_restore',reply.get('ok') is True and after['body_model']==state['body_model'] and after['n_cells']==state['n_cells'] and after['w_sum']==inventory,response=reply)
        check('restored_geometry',np.max(np.abs(verts()[:,:3]-rest[:,:3]))<2e-6)
    finally:
        request('/tick_touch_clear',{})
        request('/tick_pose',{'joint':'hip_L','deg':0});request('/tick_pose',{'joint':'knee_L','deg':0})
    return {'scope':'Private reference scene: live geometry, routing, pose, touch, binding/seal replay; no dynamic actuation or locomotion qualification.','runtime':info,'checks':checks}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--runtime',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    result=qualify(a.runtime);Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':len(result['checks']),'output':a.output}))
if __name__=='__main__':main()
