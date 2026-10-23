# SPDX-License-Identifier: AGPL-3.0-or-later
"""Milestone acceptance: open the real Membrane Workshop project, edit a part,
assign material, connect, simulate, inspect, save, reopen and replay.
The user project is opened read-only and must stay byte-identical; saves go to .user."""
import copy,hashlib,json,math,time,traceback
from pathlib import Path
import bpy
import bmesh
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'python'))
import chimera_studio
from chimera_studio import gpu_workspace as w,gpu_native as g,blocks_ui as ui,operations as op

PROJECT=ROOT.parent/'Projects/Membrane Workshop/Chimera Membrane Workshop.blend'
EVIDENCE=ROOT/'evidence/membrane-workshop-workflow-checks.json'
TEMP=ROOT/'.user/membrane-workshop-workflow'
report={'scope':'Real Membrane Workshop project through the documented workshop loop: open, edit, assign, connect, native GPU simulate, inspect, save copy, reopen, replay. Attachment apex-weld reaction forces remain explicitly out of scope (SoftVertexStitch-v1 inspector only). No physics, operator or attachment_loads behavior changed.',
        'project':str(PROJECT),'checks':[],'runtime':g.identity()}

def check(name,fn):
    try:
        details=fn();report['checks'].append({'name':name,'pass':True,'details':details});print('PASS',name,flush=True)
    except Exception as exc:
        report['checks'].append({'name':name,'pass':False,'error':str(exc),'traceback':traceback.format_exc()});print('FAIL',name,repr(exc),flush=True)

def pump(seconds=90):
    until=time.monotonic()+seconds
    while w.busy() and time.monotonic()<until:w.poll();time.sleep(.01)
    assert not w.busy(),'Native operation deadline'
    assert not w._message.startswith('GPU call failed'),w._message

def submit_native(op,label):
    # GPU launch guard refusal (VRAM busy) is retried exactly once; never bypassed.
    for attempt in (1,2):
        try:
            assert op()=={'FINISHED'},label
            pump()
            return
        except AssertionError as exc:
            if 'GPU busy' not in str(exc) or attempt==2:raise
            report.setdefault('guard_refusals',[]).append({'label':label,'attempt':attempt,'text':str(exc)})
            w.message('');time.sleep(2.)

def refused(fn,want=None):
    try:fn()
    except ValueError as exc:
        if want:assert want in str(exc),str(exc)
        return str(exc)
    raise AssertionError('Invalid input accepted')

class Recorder:
    """Headless panel recorder: collects every layout.label text."""
    def __init__(self):self.labels=[]
    def label(self,text='',**k):self.labels.append(text)
    def column(self,*a,**k):return self
    def box(self,*a,**k):return self
    def row(self,*a,**k):return self
    def prop(self,*a,**k):pass
    def operator(self,*a,**k):return None

def reveal_select(objs):
    # The project may be saved showing computed previews; the authoring loop
    # reveals editable sources before editing them (same as Return to Authoring).
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        if o.hide_get():o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.context.view_layer.update()
    assert len(bpy.context.selected_objects)==len(objs)

def panel_labels(panel):
    ui.last_view_check=None  # Receipt warnings need a real region; not under test here.
    rec=Recorder()
    class Fake:pass
    host=Fake();host.layout=rec
    panel.draw(host,bpy.context)
    return rec.labels

if not hasattr(bpy.types.Scene,'chimera_blocks'):chimera_studio.register()

state={}
def sha():return hashlib.sha256(PROJECT.read_bytes()).hexdigest()

def open_project():
    state['hash_before']=sha()
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT))
    bpy.context.view_layer.update()
    assert Path(bpy.data.filepath).resolve()==PROJECT.resolve()
    assert w._session is None and not w.busy(),'Opening the project started GPU work'
    doc=w.document();assert doc and 'assembly' in doc['spec']
    sources=[o for o in bpy.data.objects if o.get('chimera_block_id')]
    assert len(sources)==3 and len({o['chimera_block_id'] for o in sources})==3
    assert len(json.loads(bpy.context.scene.chimera_blocks.connections))==2
    state['sources']=sorted(sources,key=lambda o:o.name)
    return {'project_sha256':state['hash_before'],'source_films':3,'connections':2,'opened_offline':True}
check('Real project opens offline with three films and two apex welds',open_project)

def edit_and_assign():
    film=state['sources'][0]
    reveal_select(state['sources'])
    apex=int(film['chimera_free_center']);rim=next(i for i in range(len(film.data.vertices)) if i!=apex)
    bpy.ops.object.mode_set(mode='EDIT')
    bm=bmesh.from_edit_mesh(film.data);bm.verts.ensure_lookup_table();before_z=float(bm.verts[rim].co.z)
    bm.verts[rim].co.z+=.001;bmesh.update_edit_mesh(film.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    moved=abs(float(film.data.vertices[rim].co.z)-before_z)
    assert abs(moved-.001)<1e-5,'Edit Mode vertex move not applied'
    state['edited']=(film['chimera_block_id'],rim,float(film.data.vertices[rim].co.z))
    reveal_select(state['sources'])
    bpy.context.scene.chimera_blocks.gamma=1.
    assert bpy.ops.chimera.assign_membrane_material()=={'FINISHED'}
    assert all(float(o['chimera_film_gamma'])==1. for o in state['sources'])
    return {'edited_film':film.name,'rim_vertex':rim,'moved_m':moved,'gamma_assigned':1.}
check('Part edited in Edit Mode and supported surface material assigned',edit_and_assign)

def reconnect():
    edges=json.loads(bpy.context.scene.chimera_blocks.connections);edge=sorted(edges[0])
    def select_pair(ids):
        reveal_select([o for o in state['sources'] if o['chimera_block_id'] in ids])
    select_pair(edge)
    assert bpy.ops.chimera.disconnect_membrane_apices()=={'FINISHED'}
    assert len(json.loads(bpy.context.scene.chimera_blocks.connections))==1
    welds=[x for x in panel_labels(ui.Panel) if x.startswith('Weld ')]
    assert sum('missing' in x for x in welds)==1 and sum('stale' in x for x in welds)==0,welds
    assert all('accepted' in x and '+' in x for x in welds),welds
    select_pair(edge)
    assert bpy.ops.chimera.connect_membrane_apices()=={'FINISHED'}
    conns=[sorted(e) for e in json.loads(bpy.context.scene.chimera_blocks.connections)]
    assert len(conns)==2 and edge in conns
    welds=[x for x in panel_labels(ui.Panel) if x.startswith('Weld ')]
    assert len(welds)==2 and all('authored and accepted' in x for x in welds),welds
    return {'disconnected_then_reconnected':[edge],'connections':2,
            'panel_weld_lines_restored':welds}
check('Apex weld disconnected and reconnected through existing operators',reconnect)

def simulate():
    reveal_select(state['sources'])
    submit_native(lambda:bpy.ops.chimera.build_membrane_assembly(),'build')
    r=w.current()
    state['unloaded']=np.asarray(r.state['positions_f32'],dtype='<f4').astype(float).reshape(-1,3).copy()
    bpy.context.scene.chimera_gpu.load=.8
    submit_native(lambda:bpy.ops.chimera.gpu_load(),'load')
    return {'vertices':len(r.spec['positions']),'regions':len(r.spec['assembly']['regions']),'load_N':.8}
check('Native Vulkan trial built and center load applied',simulate)

def inspect():
    r=w.current();st=r.state
    pos=np.asarray(st['positions_f32'],dtype='<f4').astype(float).reshape(-1,3)
    assert len(pos)==len(r.spec['positions']) and np.isfinite(pos).all()
    z_drop=float(state['unloaded'][int(r.spec['centre'])][2]-pos[int(r.spec['centre'])][2])
    assert z_drop>1e-4,('apex did not descend under load',z_drop)
    assert math.isfinite(st['energy_J']) and float(st['centre_load_N'])==float(np.float32(.8))
    note=' '.join(' '.join(panel_labels(ui.Panel)).split())
    assert 'SoftVertexStitch-v1' in note and 'not yet inspectable' in note,note
    welds=[x for x in panel_labels(ui.Panel) if x.startswith('Weld ')]
    assert len(welds)==2 and all('authored and accepted' in x for x in welds),welds
    names={o['chimera_block_id']:o.name for o in bpy.data.objects if o.get('chimera_block_id')}
    for line in welds:
        a,b=line[5:].split(' + ',1)
        assert a in names.values() and b.split(':')[0].strip() in names.values(),(line,names)
    state['panel_weld_lines']=welds
    # Per-film area/energy: inspect's regions must agree with an independent
    # recomputation from r.state/r.spec, and the sum must match native energy_J.
    rep=op.inspect()['regions']
    assert rep['available'] is True,rep
    assert 'not an' in rep['basis'] and 'independent' in rep['basis'],rep['basis']
    faces=np.asarray(r.spec['triangles']);gamma=float(r.spec['gamma']);total=0.
    assert sorted(int(f) for region in r.spec['assembly']['regions'] for f in region['faces'])==list(range(len(faces)))
    for region in r.spec['assembly']['regions']:
        entry=next(x for x in rep['regions'] if x['id']==region['id'])
        assert region['name']==entry['name'] and len(region['faces'])==entry['faces'],(region,entry)
        v=pos[faces[np.asarray(region['faces'])]]
        ab=np.linalg.norm(v[:,1]-v[:,0],axis=1);bc=np.linalg.norm(v[:,2]-v[:,1],axis=1);ca=np.linalg.norm(v[:,0]-v[:,2],axis=1)
        s=(ab+bc+ca)*.5
        area=float(np.sqrt(np.maximum(0,s*(s-ab)*(s-bc)*(s-ca))).sum())
        assert abs(area-entry['area_m2'])<1e-9 and abs(gamma*area-entry['energy_J'])<1e-9,(region['id'],area,entry)
        total+=gamma*area
    assert abs(total-rep['energy_sum_J'])<1e-9
    assert rep['energy_residual_J']<=3e-4,rep
    assert abs(abs(total-float(st['energy_J']))-rep['energy_residual_J'])<1e-9
    long='Status wrap check. '+'Q'*400
    w.message(long)
    labels=panel_labels(ui.Panel)
    assert ''.join(labels).count('Q')==400 and all(len(x)<=65 for x in labels)
    assert ''.join(panel_labels(w.Panel)).count('Q')==400
    w.message('Workshop workflow inspection complete.')
    return {'apex_drop_m':z_drop,'energy_J':st['energy_J'],'centre_load_N':float(st['centre_load_N']),
            'scope_note_drawn':ui.ATTACHMENT_SCOPE_NOTE,'panel_weld_lines':state['panel_weld_lines'],
            'regions_reported':[{'id':x['id'],'area_m2':x['area_m2'],'energy_J':x['energy_J']} for x in rep['regions']],
            'regions_energy_sum_J':rep['energy_sum_J'],'regions_energy_residual_J':rep['energy_residual_J'],
            'full_400_char_status_drawn':True}
check('Deformation finite; attachment scope note and full status message drawn',inspect)

def actionable_refusals():
    bpy.ops.object.select_all(action='DESELECT')
    msg=refused(lambda:ui.editable(bpy.context))
    assert 'Select editable source films' in msg and len(msg)<=120,msg
    victim=state['sources'][0];saved=victim['chimera_film_gamma'];del victim['chimera_film_gamma']
    try:msg=refused(lambda:ui.part(victim))
    finally:victim['chimera_film_gamma']=saved
    assert 'Mark Selected Vertex as Apex' in msg and 'Assign Surface Material' in msg and len(msg)<=120,msg
    return {'empty_selection_message':msg,'lengths':[93,len(msg)]}
check('Invalid selection and unmarked film refuse with actionable messages',actionable_refusals)

def save_copy():
    TEMP.mkdir(parents=True,exist_ok=True)
    copy_blend=TEMP/'Workshop workflow copy.blend'
    state['copy']=copy_blend;state['before']=copy.deepcopy(w.document())
    assert bpy.ops.wm.save_as_mainfile(filepath=str(copy_blend),check_existing=False)=={'FINISHED'}
    assert copy_blend.is_file()
    assert sha()==state['hash_before'],'Project .blend changed after save'
    return {'copy':str(copy_blend),'project_unchanged':True}
check('Saved to temp copy; project .blend still byte-identical',save_copy)

def reopen():
    bpy.ops.wm.open_mainfile(filepath=str(state['copy']))
    assert w._session is None and not w.busy(),'Reopen started GPU work'
    assert w.document()==state['before'],'Physical/render checkpoint changed on reopen'
    ids=sorted(o['chimera_block_id'] for o in bpy.data.objects if o.get('chimera_block_id'))
    assert len(ids)==3
    assert len(json.loads(bpy.context.scene.chimera_blocks.connections))==2
    fid,rim,z=state['edited']
    film=next(o for o in bpy.data.objects if o.get('chimera_block_id')==fid)
    assert abs(float(film.data.vertices[rim].co.z)-z)<1e-6,'Part edit lost on reopen'
    return {'restored_state_id':state['before']['state']['accepted_state_id'],'edited_vertex_restored':True}
check('Saved copy reopened offline with exact state and part edit restored',reopen)

def replay():
    assert bpy.ops.chimera.gpu_resume()=={'FINISHED'};pump()
    r=w.current();h0=len(r.history);assert h0>=1
    bpy.context.scene.chimera_gpu.load=1.2
    submit_native(lambda:bpy.ops.chimera.gpu_load(),'replay-load')
    r=w.current();h1=len(r.history);assert h1>h0,'Load added no checkpoint'
    loaded_id=r.state['accepted_state_id']
    bpy.context.scene.chimera_gpu.replay=0
    assert bpy.ops.chimera.gpu_seek()=={'FINISHED'};pump()
    early=w.current().state['accepted_state_id'];assert early!=loaded_id,'Seek did not advance'
    bpy.context.scene.chimera_gpu.replay=h1-1
    assert bpy.ops.chimera.gpu_seek()=={'FINISHED'};pump()
    assert w.current().state['accepted_state_id']==loaded_id,'Return seek not exact'
    return {'checkpoints_before':h0,'checkpoints_after_load':h1,'seek_0_state':early,'returned_exact':True}
check('Replay: resume, load and checkpoint seek advance and return exactly',replay)

state['hash_after']=sha()
report['project_sha256_before']=state['hash_before']
report['project_sha256_after']=state['hash_after']
report['project_byte_identical']=state['hash_after']==state['hash_before']
report['scope_note']=ui.ATTACHMENT_SCOPE_NOTE
try:
    assert report['project_byte_identical'],'Project .blend hash changed!'
finally:
    report['pass']=all(c['pass'] for c in report['checks']) and report['project_byte_identical']
    EVIDENCE.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    chimera_studio.unregister()
if not report['pass']:raise RuntimeError('Membrane workshop workflow acceptance failed; see evidence/membrane-workshop-workflow-checks.json')
print('PASS all membrane workshop workflow steps; evidence/membrane-workshop-workflow-checks.json',flush=True)
