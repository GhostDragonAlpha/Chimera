# SPDX-License-Identifier: AGPL-3.0-or-later
"""CPU-only Blender persistence/format checks. Synthetic data is NOT physics evidence."""
import base64,copy,json,struct,sys,traceback
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
import chimera_studio
from chimera_studio import gpu_native as g,gpu_workspace as w
points=[[0,0,.1],[.1,0,.08],[0,.1,.1],[.1,.1,.08],[.2,0,.06],[.2,.1,.06]]
faces=[[0,1,2],[1,3,2],[1,4,3],[4,5,3]]
spec=g.water_spec(points,faces);n=len(faces);e=len(spec['eij'])
# Deliberately synthetic, beyond uint32; include signed zero and a subnormal flow.
steps=2**40+73
raw=struct.pack('<4I3Q2dIiiId',0x31534357,1,n,e,g.fnv64(g.water_packet(spec,spec['volumes'])),steps,0,steps*.01,.01,1,-1,0,0,.01)
raw+=struct.pack('<4i',*spec['volumes'])+struct.pack('<3d',-0.0,5e-324,.125)+struct.pack('<4d',.1,.2,.3,.4)
raw+=struct.pack('<Q',g.fnv64(raw))
state=g.water_state(raw,spec)
doc={'schema':'chimera.studio.gpu-trial.v2','source_lock':g.identity(),'spec':spec,'state':state,'authoring_visibility':{}}
results=[]
def check(name,fn):
    try:fn();results.append({'name':name,'pass':True});print('PASS',name,flush=True)
    except Exception as exc:results.append({'name':name,'pass':False,'error':str(exc),'traceback':traceback.format_exc()});print('FAIL',name,exc,flush=True)
def refused(fn):
    try:fn()
    except (ValueError,RuntimeError):return
    raise AssertionError('Expected refusal')
original=g.PrivateEngine.__init__
def no_gpu(*args,**kwargs):raise AssertionError('Offline test attempted a GPU launch')
g.PrivateEngine.__init__=no_gpu
chimera_studio.register()
def codec():
    assert g.validate_water_state(state,spec)==raw
    assert g.validate_document(json.loads(json.dumps(doc)))['state']['steps']==steps
    assert g.validate_water_state(json.loads(json.dumps(state)),spec)==raw
check('64-bit counter and raw float64 flow bits survive JSON',codec)
def bad_docs():
    for key,value in [('steps',64),('volumes',[0]*n),('sha256','bad')]:
        bad=copy.deepcopy(doc);bad['state'][key]=value;refused(lambda:g.validate_document(bad))
    for damaged in (raw[:-1],raw+b'x',bytes(len(raw))):
        refused(lambda:g.water_state(damaged,spec))
    for off,value,fmt in ((16,0,'<Q'),(80,-1,'<i'),(80+4*n,float('nan'),'<d'),(72,-1.,'<d')):
        damaged=bytearray(raw);struct.pack_into(fmt,damaged,off,value)
        struct.pack_into('<Q',damaged,len(damaged)-8,g.fnv64(damaged[:-8]))
        refused(lambda:g.water_state(bytes(damaged),spec))
check('Damaged, mismatched and nonfinite checkpoint data refused offline',bad_docs)
def file_save():
    w.load_document(doc);assert w._session is None and w.document()==doc
    assert bpy.context.scene.chimera_gpu.ca_steps==1
    bpy.context.scene.chimera_gpu.ca_steps=64
    path=ROOT/'.user/ca-offline-synthetic.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path),check_existing=False)
    bpy.ops.wm.open_mainfile(filepath=str(path))
    assert w._session is None and w.document()==doc
    assert base64.b64decode(w.document()['state']['full_state'])==raw
    assert bpy.context.scene.chimera_gpu.ca_steps==64
check('Actual .blend save/reopen retains full checkpoint without GPU allocation',file_save)
def exchange():
    path=ROOT/'.user/ca-offline-synthetic.matter.json'
    assert bpy.ops.chimera.gpu_save(filepath=str(path))=={'FINISHED'}
    assert bpy.ops.chimera.gpu_open(filepath=str(path))=={'FINISHED'}
    assert w._session is None and w.document()==doc
    bad=copy.deepcopy(doc);bad['state']['steps']=7
    refused(lambda:w.load_document(bad));assert w.document()==doc
check('Matter-trial exchange and failed load preserve accepted offline document',exchange)
chimera_studio.unregister();g.PrivateEngine.__init__=original
(ROOT/'evidence/ca-checkpoint-offline.json').write_text(json.dumps({'scope':'Synthetic format/persistence only, no GPU execution or physical replay claim','runtime_identity':g.identity(),'passed':sum(x['pass'] for x in results),'total':len(results),'tests':results},indent=2)+'\n',encoding='utf-8')
if not all(x['pass'] for x in results):raise RuntimeError('Offline checkpoint tests failed')
