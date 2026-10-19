# SPDX-License-Identifier: AGPL-3.0-or-later
import sys,json,time,traceback,copy,hashlib,base64,struct
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
    final=copy.deepcopy(r.state);assert final['volumes']==[90288,0,2813,6899], 'Native six-step baseline changed'
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

def long_water():
    r=w.current();checkpoint=copy.deepcopy(r.state)
    raw=base64.b64decode(checkpoint['full_state']);n=len(r.spec['triangles']);e=len(r.spec['eij'])
    flow=np.frombuffer(raw,dtype='<f8',count=e,offset=80+4*n)
    assert np.any(flow!=0),'Replay test must save nonzero hidden flow'
    # A non-equilibrium checkpoint: batched vs one-at-a-time and volume-only reset sensitivity.
    r.advance(8);expected=copy.deepcopy(r.state)
    r.restore_state(checkpoint)
    for _ in range(8):r.advance()
    assert r.state==expected,'Batch partition changed physical state bits'
    modified=bytearray(raw);modified[80+4*n:80+4*n+8*e]=bytes(8*e)
    struct.pack_into('<Q',modified,len(modified)-8,g.fnv64(modified[:-8]))
    r.engine.request('POST','/water_restore',bytes(modified));r.advance(8)
    assert r.state!=expected,'Test is insensitive to omitted persistent edge flow'
    r.restore_state(checkpoint)
    # Advance through multiple native history wraps using actual Blender controls.
    bpy.context.scene.chimera_gpu.ca_steps=64
    for _ in range(4):bpy.ops.chimera.gpu_step();pump()
    assert r.state['steps']==checkpoint['steps']+256
    saved=copy.deepcopy(r.state);doc=w.document();pid=r.engine.proc.pid
    blob=base64.b64decode(saved['full_state']);assert len(blob)==len(raw)
    trial=ROOT/'evidence/gpu-ca-continuation.matter.json'
    blend=ROOT/'evidence/gpu-ca-continuation.blend'
    bpy.ops.chimera.gpu_save(filepath=str(trial));bpy.ops.wm.save_as_mainfile(filepath=str(blend),check_existing=False)
    # Reference continuation before teardown. Resume must restore bytes, not rerun prior steps.
    r.advance(64);future=copy.deepcopy(r.state)
    bpy.ops.wm.open_mainfile(filepath=str(blend));assert w._session is None
    assert w.document()==doc
    bpy.ops.chimera.gpu_resume();pump();r=w.current()
    assert r.engine.proc.pid!=pid and r.state==saved
    r.advance(64);assert r.state==future,'Fresh process continuation is not bit exact'
    bpy.ops.chimera.gpu_release();bpy.ops.chimera.gpu_open(filepath=str(trial))
    assert w._session is None and w.document()==doc
    bpy.ops.chimera.gpu_resume();pump();r=w.current();assert r.state==saved
    # Many more physical steps, without a growing GPU readback allocation.
    started=time.perf_counter()
    for _ in range(32):r.advance(64)
    assert r.state['steps']==saved['steps']+2048
    history=r.engine.request('GET','/water_state',binary=True)
    ns,nc=struct.unpack_from('<2I',history)
    assert ns==65 and nc==n and len(history)==8+65*n*4
    assert list(np.frombuffer(history,dtype='<i4',offset=len(history)-4*n))==r.state['volumes']
    final=copy.deepcopy(r.state);r.seek(len(r.history)-2);r.advance(64);assert r.state==final
    assert len(base64.b64decode(final['full_state']))==len(blob)
    w.save_pre(None)
    return {'saved_step':saved['steps'],'final_step':final['steps'],'seconds':final['simulated_seconds'],
            'native_history_states':ns,'full_checkpoint_bytes':len(blob),'nonzero_flow_sensitive':True,
            'fresh_process_next_64_bit_exact':True,'batch_partition_bit_exact':True,
            'extra_2048_steps_wall_seconds':time.perf_counter()-started,'blend':str(blend),'trial':str(trial)}
check('Blender beyond 64: full-flow .blend/trial restore, batching and bounded native history',long_water)

def scheduled_flow():
    r=w.current();original=copy.deepcopy(r.state)
    packet=g.water_packet(r.spec,r.spec['volumes']);injections=[(0xffffffff,0)]*170
    injections[70]=(0,123);injections[145]=(1,77)
    scheduled=bytearray(packet);struct.pack_into('<I',scheduled,12,len(injections))
    scheduled+=b''.join(struct.pack('<2I',*pair) for pair in injections)
    def save():
        data=r.engine.request('GET','/water_save',binary=True)
        assert data[:4]==b'WCS1',data[:256]
        return data
    def run(n):return r.engine.request('POST','/water_step',{'n_macro':n,'dt_macro':.01})
    try:
        r.engine.request('POST','/water_bin',bytes(scheduled));run(70);before=save()
        result=run(80);future=save();assert result['sum']==100200
        assert struct.unpack_from('<Q',future,24)[0]==150
        r.engine.request('POST','/water_restore',before);run(80);assert save()==future
        # A history ring wrap must not recycle the scheduled injection cursor.
        r.engine.request('POST','/water_clock',{'on':True,'steps':1,'dt':.01})
        deadline=time.monotonic()+3
        clock=r.engine.request('GET','/water_clock')
        while clock['steps_total']==0 and time.monotonic()<deadline:
            time.sleep(.01);clock=r.engine.request('GET','/water_clock')
        assert clock['steps_total']>0,'CA-only helper clock stalled without a display mesh'
        refused(lambda:r.engine.request('POST','/water_step',{'n_macro':1,'dt_macro':.01}))
        blocked=r.engine.request('GET','/water_save',binary=True)
        assert json.loads(blocked)['error']=='pause_water_clock_before_checkpoint'
        r.engine.request('POST','/water_clock',{'on':False,'steps':1,'dt':.01})
        paused=save();auto=struct.unpack_from('<Q',paused,32)[0];total=struct.unpack_from('<Q',paused,24)[0]
        assert auto>0 and total==150+auto,(auto,total)
        run(3);after=save();r.engine.request('POST','/water_restore',paused);run(3);assert save()==after
        # Same dimensions, different immutable substrate/injection schedule: refused.
        r.engine.request('POST','/water_bin',packet)
        stable=save();refused(lambda:r.engine.request('POST','/water_restore',future));assert save()==stable
        return {'injection_cursor_across_65_state_ring':True,'scheduled_added_quanta':200,
                'paused_clock_steps':auto,'full_state_includes_clock':True,'different_substrate_refused':True}
    finally:
        r.engine.request('POST','/water_clock',{'on':False})
        r.engine.request('POST','/water_bin',packet);r.restore_state(original)
check('Native scheduled injections and paused automatic clock survive full-state replay',scheduled_flow)

def limits():
    r=w.current();state=copy.deepcopy(r.state);bad=copy.deepcopy(state);bad['volumes'][0]+=1
    refused(lambda:r.restore_state(bad));assert r.state==state
    good=base64.b64decode(state['full_state'])
    for malformed in (good[:-1],good+b'x',b'bad'):
        refused(lambda:r.engine.request('POST','/water_restore',malformed))
        assert r.snapshot()==state
    for offset,value,fmt in ((16,0,'<Q'),(80,-1,'<i'),(80+4*len(r.spec['triangles']),float('nan'),'<d')):
        badblob=bytearray(good);struct.pack_into(fmt,badblob,offset,value)
        struct.pack_into('<Q',badblob,len(badblob)-8,g.fnv64(badblob[:-8]))
        refused(lambda:r.engine.request('POST','/water_restore',bytes(badblob)))
        assert r.snapshot()==state,'Invalid native restore modified state'

    doc=w.document();bad=copy.deepcopy(doc);bad['source_lock']='wrong';refused(lambda:g.GpuSession.restore(bad))
    bad=copy.deepcopy(doc);bad['state']['volumes'][0]+=1;refused(lambda:w.load_document(bad));assert w.current() is r
    refused(lambda:r.advance(65));assert r.state==state
    refused(lambda:r.engine.request('POST','/water_step',{'n_macro':4097,'dt_macro':.01}))
    assert r.snapshot()==state,'Refused count must not partially advance'
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
