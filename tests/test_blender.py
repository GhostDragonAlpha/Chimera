# SPDX-License-Identifier: AGPL-3.0-or-later
import json,sys,time,traceback,statistics,hashlib
import numpy as np
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
import chimera_studio
from chimera_studio import workspace as w
from chimera_studio.geometry import compile_convex,GeometryError
from chimera_studio.native import NativeScene,NativeError
results=[]
def check(name,fn):
    try:
        details=fn();results.append({'name':name,'pass':True,'details':details});print('PASS',name)
    except Exception as exc:
        results.append({'name':name,'pass':False,'error':str(exc),'traceback':traceback.format_exc()});print('FAIL',name,exc)
def expect_error(fn):
    try:fn()
    except (ValueError,RuntimeError):return
    raise AssertionError('Expected a named refusal')
chimera_studio.register()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.chimera.demo()
def build():
    bpy.context.view_layer.update()
    expected=sorted(abs(float(np.linalg.det(np.array(o.matrix_world,dtype=float)[:3,:3])))*o.chimera.density for o in bpy.context.selected_objects)
    assert bpy.ops.chimera.build()=={'FINISHED'}
    parts=w.current().native.call('parts')['parts'];m=sorted(p['mass_kg'] for p in parts)
    assert all(abs(a-b)<max(1e-8,abs(b)*1e-8) for a,b in zip(m,expected)),(m,expected)
    return {'masses_kg':m,'parts':len(parts)}
check('Blender geometry through original volume compiler and native admission',build)
def fall():
    r=w.current();r.native.call('support',False);before=r.native.call('parts')['parts'];initial=[x['pose_c_m'][1] for x in before]
    for _ in range(10):r.advance(80)
    after=r.native.call('parts')['parts'];errors=[]
    for h,p in zip(initial,after):
        expected=h-.5*9.81*.2**2;errors.append(abs(p['pose_c_m'][1]-expected))
        assert errors[-1]<.0005,(p,expected)
        obj=r.preview[p['id']];assert abs(obj.location.z-p['pose_c_m'][1])<1e-6
    return {'max_freefall_error_m':max(errors),'render_pose_matches_native':True}
check('All native steps execute and Blender displays native freefall',fall)
def replay():
    r=w.current();r.seek(3);expected=json.loads(r.history[3]);assert r.native.call('save')==expected
    n=len(r.history);r.advance(80);assert len(r.history)==5,(n,len(r.history))
    return {'branch_samples':len(r.history),'exact_restore':True}
check('Replay restores full state and continuation branches',replay)
def save_load():
    r=w.current();before=r.native.call('hash')['hash'];p=ROOT/'evidence/roundtrip.chimera.json'
    assert bpy.ops.chimera.save_trial(filepath=str(p))=={'FINISHED'}
    r.advance(80);assert r.native.call('hash')['hash']!=before
    assert bpy.ops.chimera.load_trial(filepath=str(p))=={'FINISHED'}
    assert w.current().native.call('hash')['hash']==before
    return {'state_hash':before}
check('Save and open physical trial preserves native state',save_load)
def refusal():
    r=w.current();before=r.native.call('hash')['hash'];expect_error(lambda:r.native.call('patch',{'id':'missing','mass_kg':-1}))
    assert r.native.call('hash')['hash']==before
    r.native.call('pause',True);expect_error(lambda:r.native.advance(1))
    expect_error(lambda:r.native.advance(1.25))
    return {'state_preserved':True}
check('Native refusals and invalid step requests preserve state',refusal)
def invalid_mesh():
    before=w.current().native.call('hash')['hash']
    expect_error(lambda:compile_convex('bad',[(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)],600,.3))
    assert w.current().native.call('hash')['hash']==before
    return {'open_mesh_refused':True}
check('Unsupported geometry does not mutate accepted physics',invalid_mesh)
def cost():
    r=w.current();r.native.call('restore',r.baseline);times=[]
    for i in range(30):r.advance(80);times.append(r.last_ms)
    start=r.native.call('state')['steps']
    for n in (1,17,199,200,401):r.advance(n)
    assert r.native.call('state')['steps']==start+818
    assert all(p['speed_m_s']<100 for p in r.native.call('state')['parts'])
    return {'batch_substeps':80,'simulated_ms':20,'native_batch_median_ms':statistics.median(times),'native_batch_p95_ms':sorted(times)[int(.95*(len(times)-1))],'scope':'2 parts, CPU native solver only, not GUI frame rate'}
check('Native bridge timing and finite repeated advancement',cost)
def mounts():
    bpy.ops.chimera.edit()
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    authored=[]
    for i,x in enumerate((-.125,.125)):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x,0,1))
        o=bpy.context.object;o.scale=(.25,.25,.25);o.chimera.profile='CUSTOM';o.chimera.density=1000.
        bpy.ops.chimera.assign_material()
        for f in o.data.polygons:f.select=False
        f=max(o.data.polygons,key=lambda f:f.normal.x*(1 if i==0 else -1));f.select=True
        assert bpy.ops.chimera.mark_mount()=={'FINISHED'}
        authored.append(o)
    for o in authored:o.select_set(True)
    bpy.context.view_layer.update();assert bpy.ops.chimera.build()=={'FINISHED'}
    r=w.current();r.native.call('gravity',False);r.native.call('support',False)
    initial=r.native.call('save');a,b=[o.chimera.part_id for o in authored]
    def loaded_motion():
        parts={p['id']:p for p in r.native.call('parts')['parts']};p=parts[a]['pose_c_m']
        r.native.call('load',{'part':a,'force_n':[-10,0,0],'point_world':[p[0],p[1]+.08,p[2]]})
        r.advance(800)
        return {p['id']:p for p in r.native.call('parts')['parts']}
    free=loaded_motion();r.native.call('restore',initial)
    assert bpy.ops.chimera.join_mounts()=={'FINISHED'}
    joined=r.native.call('save');assert len(joined['welds'])==1
    coupled=loaded_motion()
    movement=abs(coupled[b]['pose_c_m'][0]-free[b]['pose_c_m'][0])
    rotation=np.linalg.norm(np.asarray(coupled[b]['pose_q_wxyz'])[1:])
    assert movement>1e-5,(free,coupled)
    assert rotation>1e-5,(free,coupled)
    # Compare a rotated native vertex with the actual Blender object's world vertex.
    from mathutils import Quaternion
    saved={p['id']:p for p in r.native.call('save')['parts']}
    for pid,part in saved.items():
        shape=np.array(part['vertices_local_m']).reshape(-1,3);com=np.array(part['com_local_m'])
        rot=np.array(Quaternion(coupled[pid]['pose_q_wxyz']).to_matrix(),dtype=float)
        expected=(shape[0]-com)@rot.T+np.array(coupled[pid]['pose_c_m'])
        expected=expected@np.array(w._TO_BLENDER,dtype=float).T
        obj=r.preview[pid];displayed=np.array(obj.matrix_world@obj.data.vertices[0].co)
        assert np.linalg.norm(displayed-expected)<1e-6,(displayed,expected)

    # A mismatched face gap refuses before mutating the accepted native scene.
    before=r.native.call('hash')['hash']
    from chimera_studio.geometry import attachment_between
    expect_error(lambda:attachment_between(a,r.ports[a],b,(np.asarray(r.ports[b])+[.01,0,0]).tolist()))
    assert r.native.call('hash')['hash']==before
    path=ROOT/'evidence/connected-trial.chimera.json'
    assert bpy.ops.chimera.save_trial(filepath=str(path))=={'FINISHED'}
    assert bpy.ops.chimera.load_trial(filepath=str(path))=={'FINISHED'}
    assert w.current().native.call('hash')['hash']==before
    assert len(w.current().native.call('save')['welds'])==1
    return {'partner_translation_difference_m':movement,'partner_quaternion_vector_norm':float(rotation),'native_weld_roundtrip':True,'invalid_gap_preserves_state':True}
check('Authored face mounts transfer force and moment and survive save/load',mounts)

def blend_roundtrip():
    r=w.current();before=r.native.call('hash')['hash']
    file=ROOT/'evidence/workshop-roundtrip.blend'
    assert bpy.ops.wm.save_as_mainfile(filepath=str(file))=={'FINISHED'}
    r.advance(80);assert r.native.call('hash')['hash']!=before
    assert bpy.ops.wm.open_mainfile(filepath=str(file))=={'FINISHED'}
    assert w.current().native.call('hash')['hash']==before
    # Invalid metadata must fail before replacing this scene.
    malformed=w.trial_document(w.current())
    from copy import deepcopy
    malformed=deepcopy(malformed);next(iter(malformed['materials'].values()))['color']=[float('nan')]*4
    expect_error(lambda:w.restore_trial(malformed,bpy.context))
    assert w.current().native.call('hash')['hash']==before
    ids={p['id'] for p in w.current().native.call('parts')['parts']}
    bpy.ops.chimera.edit()
    authored=[o for o in bpy.context.scene.objects if not o.get('chimera_preview') and o.chimera.part_id in ids]
    assert len(authored)==2 and all(not o.hide_get() for o in authored)
    return {'exact_physical_state_in_blend':True,'authoring_visibility_restored':True,'bad_metadata_preserves_state':True}
check('Blender project save/reopen restores physics and authoring',blend_roundtrip)

def shutdown():
    assert bpy.ops.chimera.edit()=={'FINISHED'}
    chimera_studio.unregister();assert not hasattr(bpy.types.Object,'chimera')
    return 'Clean registration/unregistration'
check('Clean teardown',shutdown)
out={'blender':bpy.app.version_string,'blender_build_hash':bpy.app.build_hash.decode(),'binary':bpy.app.binary_path,'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*sorted((ROOT/'python/chimera_studio').glob('*.py')),ROOT/'native/bridge.cpp',ROOT/'build/native/Release/chimera_studio_bridge.dll']},'engine_source_lock':w.lock_identity(),'tests':results,'pass':all(x['pass'] for x in results)}
(ROOT/'evidence/headless_integration.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
if not out['pass']:raise RuntimeError('Integration checks failed; see evidence/headless_integration.json')
