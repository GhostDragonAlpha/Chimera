# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real Blender + private native GPU, existing three-film construction."""
import copy,hashlib,json,sys,time,traceback
from pathlib import Path
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
import chimera_studio
from chimera_studio import gpu_workspace as w,gpu_native as g,blocks,blocks_ui as ui
report={'scope':'Blender authoring and rendering of existing apex-weld films; one world-Z rail, fixed rims, uniform gamma. No water, game or general solid-material qualification.', 'checks':[],'runtime':g.identity()}

def check(name,fn):
    try:
        details=fn();report['checks'].append({'name':name,'pass':True,'details':details});print('PASS',name,flush=True)
    except Exception as exc:
        report['checks'].append({'name':name,'pass':False,'error':str(exc),'traceback':traceback.format_exc()});print('FAIL',name,repr(exc),flush=True)

def pump():
    until=time.monotonic()+60
    while w.busy() and time.monotonic()<until:w.poll();time.sleep(.01)
    assert not w.busy(),'Native operation deadline'
    assert not w._message.startswith('GPU call failed'),w._message

def refused(fn):
    try:fn()
    except (ValueError,RuntimeError):return
    raise AssertionError('Invalid input accepted')

def load(value):
    bpy.context.scene.chimera_gpu.load=value
    assert bpy.ops.chimera.gpu_load()=={'FINISHED'};pump()

chimera_studio.register()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def construct():
    assert bpy.ops.chimera.add_membrane_assembly()=={'FINISHED'}
    bpy.context.view_layer.update()
    sources=ui.editable(bpy.context)
    assert len(sources)==3 and len(json.loads(bpy.context.scene.chimera_blocks.connections))==2
    assert bpy.ops.chimera.assign_membrane_material()=={'FINISHED'}
    edges=json.loads(bpy.context.scene.chimera_blocks.connections)
    bpy.context.scene.chimera_blocks.connections='[]'
    for edge in edges:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in sources:obj.select_set(obj['chimera_block_id'] in edge)
        assert bpy.ops.chimera.connect_membrane_apices()=={'FINISHED'}
    assert bpy.ops.chimera.disconnect_membrane_apices()=={'FINISHED'}
    assert len(json.loads(bpy.context.scene.chimera_blocks.connections))==1
    assert bpy.ops.chimera.connect_membrane_apices()=={'FINISHED'}
    for obj in sources:obj.select_set(True)
    assert bpy.ops.chimera.build_membrane_assembly()=={'FINISHED'};pump()
    r=w.current();assert len(r.spec['positions'])==601 and len(r.spec['triangles'])==600
    assert len(r.spec['assembly']['regions'])==3
    load(.8)
    assert float(r.state['centre_load_N'])==float(np.float32(.8))
    return {'pieces':3,'connections':2,'vertices':601,'triangles':600,'energy_J':r.state['energy_J'],'loaded_apex_m':np.asarray(r.state['positions_f32'],dtype='<f4').astype(float).reshape(-1,3)[0].tolist()}
check('Existing three-film construction, material assignment, native load',construct)

def physical_render():
    r=w.current();a,p=g.validate_render(r.render,r.spec,r.state);faces=np.asarray(r.spec['triangles'])
    actual=np.asarray(r.state['positions_f32'],dtype='<f4').astype(float).reshape(-1,3)
    assert np.array_equal(p,actual)
    # Independent area/energy and finite-difference force from 3-D edge lengths.
    def energy(points):
        v=points[faces];ab=np.linalg.norm(v[:,1]-v[:,0],axis=1);bc=np.linalg.norm(v[:,2]-v[:,1],axis=1);ca=np.linalg.norm(v[:,0]-v[:,2],axis=1)
        s=(ab+bc+ca)*.5
        return np.sqrt(np.maximum(0,s*(s-ab)*(s-bc)*(s-ca))).sum()*r.spec['gamma']
    plus=actual.copy();minus=actual.copy();h=1e-5;plus[0,2]+=h;minus[0,2]-=h
    force=-(energy(plus)-energy(minus))/(2*h)
    assert abs(energy(actual)-r.state['energy_J'])<3e-4
    assert abs(force-r.state['centre_load_N'])<1e-4,(force,r.state['centre_load_N'])
    normals=[]
    for v in range(len(actual)):
        first=next(face for face in faces if v in face)
        normal=np.cross(actual[first[1]]-actual[first[0]],actual[first[2]]-actual[first[0]]);normal/=np.linalg.norm(normal)
        normals.append([normal[0],normal[2],-normal[1]])
    assert np.allclose(a[:,3:6],normals,atol=2e-6),'Kernel CSR normal does not belong to this vertex'
    col=bpy.data.collections[w.COLLECTION]
    for region in r.spec['assembly']['regions']:
        obj=next(o for o in col.objects if o.get('chimera_block_preview')==region['id'])
        visible=np.asarray([list(v.co) for v in obj.data.vertices],dtype='<f4')
        assert np.array_equal(visible,p[region['vertices']])
        assert obj['render_state_id']==r.render['render_state_id'] and not obj.hide_select
    return {'force_N':force,'energy_residual_J':abs(energy(actual)-r.state['energy_J']),'render_hash':r.render['render_state_id'],'native_CSR_normals_checked':len(normals),'computed_piece_views':3}
check('Kernel output, actual Blender vertices/normals, independent equilibrium',physical_render)

image_before=None
def native_image():
    global image_before
    assert bpy.ops.chimera.native_render_frame()=={'FINISHED'};pump()
    im=bpy.data.images['Chimera Native Render'];pixels=np.asarray(im.pixels[:]).reshape(-1,4)
    assert im.size[:]==(384,256) and np.ptp(pixels[:,:3],axis=0).max()>.1
    image_before=(ROOT/'.user/native-render.png').read_bytes()
    (ROOT/'evidence/membrane-native-render.png').write_bytes(image_before)
    load(1.6);bpy.ops.chimera.native_render_frame();pump()
    assert (ROOT/'.user/native-render.png').read_bytes()!=image_before,'Render failed to reflect native deformation'
    w.current().seek(1);bpy.ops.chimera.native_render_frame();pump()
    assert (ROOT/'.user/native-render.png').read_bytes()==image_before,'Re-solved geometry/raster differs'
    return {'image_size':list(im.size),'native_image_loaded_in_Blender':True,'changed_after_load':True,'identical_on_return':True}
check('Native raster kernel image in Blender follows physical deformation',native_image)

def failures():
    before=copy.deepcopy(w.document());s=before['spec'];a=s['assembly']
    refused(lambda:blocks.compile_parts(a['parts'],[]))
    bad=copy.deepcopy(a['parts']);bad[1]['gamma']=2
    refused(lambda:blocks.compile_parts(bad,a['connections']))
    bad=copy.deepcopy(a['parts']);bad[1]['positions'][bad[1]['centre']][0]+=.001
    refused(lambda:blocks.compile_parts(bad,a['connections']))
    bad=copy.deepcopy(a['parts']);bad[1]['id']=bad[0]['id']
    refused(lambda:blocks.compile_parts(bad,a['connections']))
    bad=copy.deepcopy(before);bad['render']['vertices9_f32_hex']='ff'+bad['render']['vertices9_f32_hex'][2:]
    refused(lambda:w.load_document(bad))
    assert w.document()==before,'Refusal changed the accepted trial'
    return {'disconnected_mixed_material_misaligned_forged_render':'refused with previous state preserved'}
check('Invalid topology/material/attachment/render data preserve current work',failures)

def save_replay():
    r=w.current();saved=copy.deepcopy(w.document());pid=r.engine.proc.pid
    r.seek(0);r.deform(float(np.float32(.8)));assert r.state['accepted_state_id']==saved['state']['accepted_state_id']
    assert r.render==saved['render']
    # Restore the last confirmed document then exercise actual Blender persistence.
    w._saved=w.document()
    trial=ROOT/'evidence/membrane-assembly.matter.json';blend=ROOT/'evidence/membrane-assembly.blend'
    bpy.ops.chimera.gpu_save(filepath=str(trial));bpy.ops.wm.save_as_mainfile(filepath=str(blend),check_existing=False)
    before=w.document();bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert w._session is None and w.document()==before
    assert len(json.loads(bpy.context.scene.chimera_blocks.connections))==2
    assert len([o for o in bpy.data.objects if o.get('chimera_block_id')])==3
    bpy.ops.chimera.gpu_resume();pump();r=w.current();assert r.engine.proc.pid!=pid
    assert r.state['accepted_state_id']==before['state']['accepted_state_id'] and r.render==before['render']
    load(1.2);expected=copy.deepcopy(r.state);expected_render=copy.deepcopy(r.render)
    r.seek(0);r.deform(float(np.float32(1.2)))
    assert {k:v for k,v in r.state.items() if k!='material_snapshot'}=={k:v for k,v in expected.items() if k!='material_snapshot'} and r.render==expected_render
    w.return_to_authoring()
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.context.scene.chimera_blocks.connections='[]'
    bpy.ops.chimera.gpu_open(filepath=str(trial));assert w._session is None
    assert len([o for o in bpy.data.objects if o.get('chimera_block_id')])==3
    assert len(json.loads(bpy.context.scene.chimera_blocks.connections))==2
    return {'fresh_process':True,'blend':str(blend),'trial':str(trial),'continued_state_and_render_exact':True}
check('Save/reopen .blend and trial; fresh process exact physical/render continuation',save_replay)


def material_effect():
    doc=copy.deepcopy(w.document());initial=doc['state']
    sources=[o for o in bpy.data.objects if o.get('chimera_block_id')]
    for i,o in enumerate(sources):o.name='Renamed editable film '+str(i)
    w.return_to_authoring()
    assert all(not o.hide_get() for o in sources),'Stable source identity lost during rename'
    bpy.ops.object.select_all(action='DESELECT')
    for o in sources:o.select_set(True)
    bpy.context.view_layer.objects.active=sources[0]
    bpy.context.scene.chimera_blocks.gamma=2.
    bpy.ops.chimera.assign_membrane_material();bpy.ops.chimera.build_membrane_assembly();pump();load(.8)
    st=w.current().state;assert st['gamma_admitted_f64']==2.
    assert st['accepted_state_id']!=initial['accepted_state_id']
    assert st['energy_J']>initial['energy_J']
    changed={'old_gamma':1.,'new_gamma':2.,'different_native_state':True}
    # Restore the recorded trial; material properties in that document remain authoritative.
    w.load_document(doc);bpy.ops.chimera.gpu_resume();pump()
    assert w.current().state['gamma_admitted_f64']==1.
    return changed
check('Changing surface assignment changes native response; saved material restores',material_effect)

try:w.return_to_authoring()
finally:
    chimera_studio.unregister()
    report['pass']=all(c['pass'] for c in report['checks'])
    (ROOT/'evidence/membrane-assembly-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if not report['pass']:raise RuntimeError('Membrane assembly integration failed; see evidence')
