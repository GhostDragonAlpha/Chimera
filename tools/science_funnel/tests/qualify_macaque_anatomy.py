"""Compare live native bone motion to source-model frames, on an owned reference runtime."""
import argparse,json,struct,time,urllib.request,urllib.error
from pathlib import Path
import numpy as np
from tools.science_funnel.macaque_anatomy import parse_source,world_meshes

def qualify(runtime):
    info=json.loads(Path(runtime).read_text(encoding='utf-8-sig'))
    scene=json.loads(Path(info['scene']).read_text());assert scene['mode']=='anatomy'
    base='http://127.0.0.1:'+str(info['engine_port']);game='http://127.0.0.1:'+str(info['game_port'])
    def request(route,data=None,binary=False,host=base):
        req=urllib.request.Request(host+route,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=12) as r:raw=r.read()
        except urllib.error.HTTPError as e:raw=e.read()
        return raw if binary else json.loads(raw)
    def verts():
        raw=request('/verts',binary=True);n,=struct.unpack_from('<I',raw);assert len(raw)==4+36*n
        return np.frombuffer(raw,dtype='<f4',offset=4).reshape(n,9)[:,:3].copy()
    def advance():
        tick=request('/tick_state')['ticks'];end=time.monotonic()+6
        while time.monotonic()<end:
            if request('/tick_state')['ticks']>=tick+2:return
            time.sleep(.02)
        raise AssertionError('native tick stalled')
    checks=[]
    def check(name,ok,**detail):
        checks.append(dict(name=name,pass_=bool(ok),detail=detail))
        if not ok:raise AssertionError(name+': '+str(detail))
    model,receipt=parse_source()
    check('private_anatomy_scene',request('/api/scene',host=game)['mesh_sha256']==scene['mesh_sha256'])
    topology=request('/topology',binary=True);nt,=struct.unpack_from('<I',topology)
    source=(Path(info['scene']).parent/'mesh.bin').read_bytes();nv,ni=struct.unpack_from('<II',source)
    check('source_triangle_indices_preserved',nt*3==ni and topology[4:]==source[24+36*nv:])
    check('native_body_owner',request('/tick_state')['body_model']=='JNT3_hierarchical')
    def set_pose(q):
        for name,rec in model['coordinates'].items():
            deg=float(np.rad2deg(q.get(name,rec['default_rad'])-rec['default_rad']))
            assert request('/api/pose',{'joint':name,'deg':deg},host=game).get('ok'),name
        advance()
    poses=[{}, {'shoulder_adduction':np.deg2rad(-95),'shoulder_rotation':.35,'shoulder_flexion':.2,'elbow_flexion':1.1,'radial_pronation':-.4,'wrist_flexion':.3,'wrist_abduction':-.2}, {'shoulder_adduction':.4,'shoulder_rotation':-.5,'shoulder_flexion':-.45,'elbow_flexion':2.2,'radial_pronation':.7,'wrist_flexion':-.6,'wrist_abduction':.4}]
    try:
        for i,q in enumerate(poses):
            set_pose(q);actual=verts();meshes=world_meshes(model,values=q);expected=np.concatenate([m[2] for m in meshes])
            check('source_frames_pose_'+str(i),actual.shape==expected.shape and np.max(np.abs(actual-expected))<2e-7,max_error_m=float(np.max(np.abs(actual-expected))),vertices=len(actual))
            offset=0;max_edge_error=0.
            for b,g,xyz,tri,metrics in meshes:
                target=actual[offset:offset+len(xyz)];offset+=len(xyz)
                ae=np.linalg.norm(target[tri[:,0]]-target[tri[:,1]],axis=1);ee=np.linalg.norm(xyz[tri[:,0]]-xyz[tri[:,1]],axis=1)
                max_edge_error=max(max_edge_error,float(np.max(np.abs(ae-ee))))
            check('bone_dimensions_preserved_'+str(i),max_edge_error<2e-7,max_edge_error_m=max_edge_error)
        before=verts();bad=request('/api/pose',{'joint':'shoulder_adduction','deg':-110},host=game)
        check('outside_source_range_refused',bad.get('ok') is False)
        advance();check('refusal_preserves_surface',np.array_equal(before,verts()))
        bad=request('/api/touch_hit',{'hit':before[-1].tolist(),'force_n':200},host=game)
        check('unqualified_bone_press_refused_by_viewer',bad.get('ok') is False and bad.get('error')=='anatomical_reference_has_no_qualified_contact_material')
        advance();check('refused_press_preserves_surface',np.array_equal(before,verts()))
    finally:set_pose({})
    expected=np.concatenate([m[2] for m in world_meshes(model)])
    check('reset_to_source_pose',np.max(np.abs(verts()-expected))<2e-7)
    return {'scope':'Source-to-native kinematic geometry, dimensions and viewer routing; not muscle force, sealed bone material, full body or locomotion.','runtime':info,'source_revision':receipt['revision'],'checks':checks}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--runtime',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    result=qualify(a.runtime);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':len(result['checks']),'output':a.output}))
if __name__=='__main__':main()
