# SPDX-License-Identifier: AGPL-3.0-or-later
import sys,json,time,traceback,copy,hashlib
from pathlib import Path
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
import chimera_studio
from chimera_studio import gpu_workspace as w,gpu_native as g
results=[]
def check(name,fn):
    try:
        details=fn();results.append({'name':name,'pass':True,'details':details});print('PASS',name,flush=True)
    except Exception as exc:
        results.append({'name':name,'pass':False,'error':str(exc),'traceback':traceback.format_exc()});print('FAIL',name,exc,flush=True)
def pump():
    deadline=time.monotonic()+50
    while w.busy() and time.monotonic()<deadline:w.poll();time.sleep(.01)
    assert not w.busy(),'Blender GPU worker exceeded deadline'
    assert not w._message.startswith('GPU call failed'),w._message

def refused(fn):
    try:fn()
    except (ValueError,RuntimeError):return
    raise AssertionError('Expected refusal')
chimera_studio.register()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def membrane():
    assert bpy.ops.chimera.gpu_demo()=={'FINISHED'}
    bpy.context.view_layer.update()
    assert bpy.ops.chimera.gpu_membrane()=={'FINISHED'};pump();r=w.current()
    fixture=ROOT/'vendor/gpu/fixture/b2/case_gamma1/energy_f64.npy'
    reference=float(np.load(fixture).ravel()[0]);assert abs(r.state['energy_J']-reference)<2e-6
    initial=copy.deepcopy(r.state);bpy.context.scene.chimera_gpu.load=.5
    assert bpy.ops.chimera.gpu_load()=={'FINISHED'};pump()
    after=copy.deepcopy(r.state);assert after['accepted_state_id']!=initial['accepted_state_id']
    preview=next(o for o in bpy.data.collections[w.COLLECTION].objects if o.get('chimera_gpu_preview'))
    actual=np.array([list(v.co) for v in preview.data.vertices],dtype='<f4');expected=np.array(after['positions_f32'],dtype='<f4').reshape(-1,3)
    assert np.array_equal(actual,expected),'Blender vertices differ from native accepted state'
    bpy.context.scene.chimera_gpu.replay=0;bpy.ops.chimera.gpu_seek();pump();assert r.state['accepted_state_id']==initial['accepted_state_id']
    bpy.ops.chimera.gpu_load();pump();assert r.state['accepted_state_id']==after['accepted_state_id'],'Branch is not deterministic'
    return {'initial_energy_J':initial['energy_J'],'reference_J':reference,'loaded_state_id':after['accepted_state_id'],'native_vertices':len(actual),'center_displacement_m':float(expected[r.spec['centre'],2]-initial['positions_f32'][3*r.spec['centre']+2])}
check('Blender-authored membrane through native GPU; loaded geometry and exact replay',membrane)

def reopen():
    before=w.document();pid=w.current().engine.proc.pid
    trial=ROOT/'evidence/gpu-membrane.matter.json';bpy.ops.chimera.gpu_save(filepath=str(trial))
    blend=ROOT/'evidence/gpu-matter.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend),check_existing=False)
    bpy.ops.wm.open_mainfile(filepath=str(blend));assert w._session is None,'File load should not silently allocate GPU memory'
    assert w.document()==before
    bpy.ops.chimera.gpu_resume();pump();assert w.current().state['accepted_state_id']==before['state']['accepted_state_id']
    assert w.current().engine.proc.pid!=pid,'Reopen must use a new private native process'
    bpy.ops.chimera.gpu_release();assert w._session is None and w.document()['state']['accepted_state_id']==before['state']['accepted_state_id']
    bpy.ops.chimera.gpu_open(filepath=str(trial));assert w._session is None
    return {'blend':str(blend),'trial':str(trial),'fresh_process_restore':True,'automatic_gpu_start_on_open':False}
check('.blend and separate GPU trial survive native process teardown',reopen)

def water():
    w.close_session()
    # A small authored sloping strip, sharing the original native CA water kernels.
    points=[[0,0,.1],[.1,0,.08],[0,.1,.1],[.1,.1,.08],[.2,0,.06],[.2,.1,.06]]
    faces=[[0,1,2],[1,3,2],[1,4,3],[4,5,3]]
    mesh=bpy.data.meshes.new('CA authored strip');mesh.from_pydata(points,[],faces);mesh.update()
    obj=bpy.data.objects.new('CA test substrate',mesh);bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    for face in mesh.polygons:face.select=face.index==0
    bpy.context.view_layer.update();assert bpy.ops.chimera.gpu_water()=={'FINISHED'};pump();r=w.current()
    initial=copy.deepcopy(r.state);timings=[]
    for _ in range(6):
        bpy.ops.chimera.gpu_step();pump();timings.append(r.last_ms)
    final=copy.deepcopy(r.state);assert final['volumes']!=initial['volumes'],'CA did not redistribute water'
    assert sum(final['volumes'])==sum(initial['volumes']) and min(final['volumes'])>=0
    bpy.context.scene.chimera_gpu.replay=3;bpy.ops.chimera.gpu_seek();pump()
    for _ in range(3):bpy.ops.chimera.gpu_step();pump()
    assert r.state==final,'CA flux history lost during replay'
    doc=w.document();r.close();fresh=g.GpuSession.restore(doc)
    try:
        assert fresh.state==final
        fresh.advance();expected=copy.deepcopy(fresh.state)
        fresh.seek(0);fresh.advance();assert fresh.state==expected,'CA resume differs after restoring hidden flux state'
    finally:fresh.close()
    # Reconnect for deliberate error and persistence checks below.
    w.close_session();w.load_document(doc);bpy.ops.chimera.gpu_resume();pump()
    return {'initial':initial['volumes'],'after_six':final['volumes'],'sum_quanta':sum(final['volumes']),'step_wall_ms':timings,'replayed_hidden_flux':True}
check('Blender CA water: native redistribution, conservation, branch and fresh-process replay',water)

def limits():
    r=w.current();state=copy.deepcopy(r.state);bad=copy.deepcopy(state);bad['volumes'][0]+=1
    refused(lambda:r.restore_state(bad));assert r.state==state
    doc=w.document();bad=copy.deepcopy(doc);bad['source_lock']='wrong';refused(lambda:g.GpuSession.restore(bad))
    bad=copy.deepcopy(doc);bad['state']['volumes'][0]+=1;refused(lambda:w.load_document(bad));assert w.current() is r
    r.elapsed_steps=64
    refused(lambda:r.advance());assert r.state==state
    r.elapsed_steps=state['steps']
    # Stop ONLY our test child; an interrupted native call retains the last confirmed save.
    r.engine.proc.terminate();r.engine.proc.wait(timeout=5)
    refused(lambda:r.advance());assert r.document()['state']==state
    w.save_pre(None);assert json.loads(bpy.data.texts[w.TEXT].as_string())['state']==state
    return {'forged_state_refused':True,'runtime_mismatch_refused':True,'no_silent_step_loss':True,'checkpoint_saved_after_child_exit':True}
check('Refusal boundaries and checkpoint survival after owned GPU process exit',limits)
try:chimera_studio.unregister()
except Exception:traceback.print_exc()
(ROOT/'evidence/gpu-integration.json').write_text(json.dumps({'tests':results,'passed':sum(x['pass'] for x in results),'total':len(results),'runtime_identity':g.identity(),'scope':'Existing one-center membrane and closed CA water field; not coupled multiphysics'},indent=2))
if not all(x['pass'] for x in results):raise RuntimeError('GPU integration checks failed; see evidence/gpu-integration.json')
