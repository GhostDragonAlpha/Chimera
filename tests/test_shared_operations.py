# SPDX-License-Identifier: AGPL-3.0-or-later
"""Actual Blender mode/context, stale proposals, native results and save recovery."""
import bpy,bmesh
import sys,json,time,threading,hashlib,copy,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence/shared-operations';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'python'))
import chimera_studio
from chimera_studio import operations as op,gpu_workspace as w,gpu_native as g,blocks_ui as ui,blocks
chimera_studio.register()
class Checks(list):
    def append(self,item):
        super().append(item);print('PASS',item,flush=True)
checks=Checks()
projects={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT.parent/'Projects').rglob('*.blend')}

def propose(action,targets=None,params=None):
    return op.propose(action,targets,params,'Make a reusable supported construction visible and testable in Blender')
def run(action,targets=None,params=None):
    r=propose(action,targets,params)
    a=op.apply(r['id']);assert a['status']!='failed',a;return a

def wait(record):
    until=time.monotonic()+65
    while time.monotonic()<until:
        r=op.status(record['id'])
        if r['status'] in ('succeeded','failed','interrupted'):return r
        time.sleep(.01)
    raise AssertionError('Owned native test exceeded 65 seconds')

def select(objects):
    if bpy.context.mode=='EDIT_MESH':bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.selected_objects:o.select_set(False)
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0] if objects else None

try:
    starter=run('create_films');ids=[p['id'] for p in op.inspect()['parts']]
    assert len(ids)==3 and starter['status']=='succeeded'
    objects=[o for o in bpy.context.scene.objects if op.target_id(o) in ids]
    checks.append('shared create command calls existing three-film recipe operator')
    select(objects[:1]);bpy.ops.object.mode_set(mode='EDIT')
    bm=bmesh.from_edit_mesh(objects[0].data);bm.verts.ensure_lookup_table()
    for f in bm.faces:f.select_set(False)
    for e in bm.edges:e.select_set(False)
    for v in bm.verts:v.select_set(v.index in (0,3))
    bm.select_flush_mode()
    bmesh.update_edit_mesh(objects[0].data)
    old_selection=[v.index for v in bm.verts if v.select]
    result=run('assign_surface',ids,{'gamma':1.25})
    assert result['status']=='succeeded' and bpy.context.mode=='EDIT_MESH' and bpy.context.object==objects[0]
    restored_selection=[v.index for v in bmesh.from_edit_mesh(objects[0].data).verts if v.select]
    assert restored_selection==old_selection,(old_selection,restored_selection)
    assert all(o['chimera_film_gamma']==1.25 for o in objects)
    checks.append('API assignment restores Edit Mode, active object and mesh selection')
    select(objects)
    expected=blocks.compile_parts([ui.part(o) for o in objects],json.loads(bpy.context.scene.chimera_blocks.connections))
    proposal=propose('build_films',ids)
    assert proposal['preview']['compiled_spec']==op.digest(expected)
    assert op.inspect()['native'] is None and not w.busy()
    op.discard(proposal['id'])
    checks.append('proposal previews exactly the existing human compiler input without starting GPU')
    stale=propose('assign_surface',ids,{'gamma':2.})
    original=objects[0].data.vertices[0].co.copy();objects[0].data.vertices[0].co.z+=.01
    failed=op.apply(stale['id']);assert failed['status']=='failed' and 'stale' in failed['error']
    assert all(o['chimera_film_gamma']==1.25 for o in objects)
    objects[0].data.vertices[0].co=original
    assert op.apply(stale['id'])['status']=='failed'
    checks.append('human geometry edit rejects stale proposal before material mutation; retry never reapplies it')
    previous=len(objects)
    assert op.apply(starter['id'])['status']=='succeeded'
    assert len(op.inspect()['parts'])==previous
    checks.append('duplicate delivery returns existing result instead of adding another construction')
    errors=[]
    def offthread():
        try:op.inspect()
        except RuntimeError as e:errors.append(str(e))
    thread=threading.Thread(target=offthread);thread.start();thread.join()
    assert errors==['Call Studio operations on Blender main thread']
    checks.append('off-main-thread API call refuses before accessing Blender data')
    # Native build and load use exactly the same operators as the human buttons.
    accepted=wait(run('build_films',ids));assert accepted['status']=='succeeded',accepted
    assert accepted['native_result']['accepted_state_id']==w.document()['state']['accepted_state_id']
    assert op.inspect()['source_matches_native'] is True
    checkpoint=copy.deepcopy(w.document()['state'])
    old_name=objects[0].name;objects[0].name='Renamed supported film'
    assert op.inspect()['source_matches_native'] is True
    objects[0].name=old_name
    prior=objects[0].data.vertices[3].co.copy();objects[0].data.vertices[3].co.z+=.01
    stale_state=op.inspect();assert stale_state['needs_rebuild'] and not stale_state['source_matches_native']
    assert w.document()['state']==checkpoint
    objects[0].data.vertices[3].co=prior
    assert op.inspect()['source_matches_native'] is True
    checks.append('renaming preserves physical correspondence; source edits flag rebuild without changing accepted checkpoint')
    # Connection inspection: name each apex weld's authored/accepted state
    # offline; flagging never rebuilds or touches the accepted checkpoint.
    authored_edges=sorted(sorted(e) for e in json.loads(bpy.context.scene.chimera_blocks.connections))
    accepted_edges=sorted(sorted(e) for e in w.document()['spec']['assembly']['connections'])
    report=op.inspect()['connections']
    assert [c['edge'] for c in report if c.get('authored')]==authored_edges
    assert [c['edge'] for c in report if c.get('accepted')]==accepted_edges
    assert not any(c['stale'] or c['missing'] for c in report)
    assert all(c['names'] and len(c['edge'])==2 for c in report)
    checks.append('inspect connections lists every authored and accepted apex weld with names')
    import itertools
    unaccepted=[p for p in (sorted(p) for p in itertools.combinations(sorted(ids),2)) if p not in authored_edges]
    removed=authored_edges[0]
    bpy.context.scene.chimera_blocks.connections=json.dumps([list(e) for e in authored_edges[1:]])
    report=op.inspect()['connections']
    flagged=[c for c in report if c['edge']==removed][0]
    assert flagged['missing'] and not flagged.get('authored') and not flagged['stale']
    assert all(not c['missing'] and not c['stale'] for c in report if c['edge']!=removed)
    assert w.document()['state']==checkpoint and not w.busy()
    checks.append('disconnecting one weld flags exactly that edge missing while inspect stays offline')
    bpy.context.scene.chimera_blocks.connections=json.dumps([list(e) for e in authored_edges]+[unaccepted[0]])
    report=op.inspect()['connections']
    stale=[c for c in report if c['edge']==unaccepted[0]][0]
    assert stale['stale'] and stale['authored'] and not stale.get('accepted')
    assert all(not c['stale'] for c in report if c['edge']!=unaccepted[0])
    checks.append('a newly authored weld outside the accepted build is flagged stale by edge identity')
    bpy.context.scene.chimera_blocks.connections=json.dumps(authored_edges)
    report=op.inspect()['connections']
    assert not any(c['stale'] or c['missing'] for c in report)
    checks.append('restoring the authored welds clears every stale/missing flag')
    # Per-film area/energy report: offline and fail-closed. Placed before the
    # pre-existing owned-helper-failure step so these checks always run.
    none_report=op._regions_report(None)
    assert none_report['available'] is False and set(none_report)=={'available','reason'},none_report
    forged=op._regions_report(copy.deepcopy(w.document())|{'state':{**w.document()['state'],'energy_J':float(w.document()['state']['energy_J'])+1.}})
    assert forged['available'] is False and set(forged)=={'available','reason'} and 'energy_J' in forged['reason'],forged
    live=op._regions_report(w.document())
    assert live['available'] is True and live['energy_residual_J']<=3e-4,live
    assert abs(sum(r['energy_J'] for r in live['regions'])-live['energy_sum_J'])<1e-9
    assert live['regions']==op.inspect()['regions']['regions']
    checks.append('region area/energy report is offline, exact and fail-closed against forged native energy_J')
    loaded=wait(run('apply_load',params={'load':.8}));assert loaded['status']=='succeeded',loaded
    state=copy.deepcopy(w.document()['state'])
    bpy.context.scene.chimera_gpu.load=.8
    assert bpy.ops.chimera.gpu_load()=={'FINISHED'}
    while w.busy():w.poll();time.sleep(.01)
    direct=copy.deepcopy(w.document()['state'])
    assert state['accepted_state_id']==direct['accepted_state_id']
    checks.append('native build/load finish explicitly; shared and original UI load yield the same physical state')
    # Existing owner's explicit checkpoint path remains authoritative.
    replayed=wait(run('replay',params={'checkpoint':0}));assert replayed['status']=='succeeded',replayed
    wait(run('apply_load',params={'load':.8}))
    before=copy.deepcopy(w.document())
    # Kill only this test's private helper, then observe an actual failed native call.
    w.current().engine.close()
    failure=wait(run('apply_load',params={'load':.9}));assert failure['status']=='failed',failure
    assert failure['error'] and w.document()['state']==before['state']
    recovered=wait(run('resume'));assert recovered['status']=='succeeded',recovered
    assert w.document()['state']['accepted_state_id']==before['state']['accepted_state_id']
    checks.append('owned-helper failure returns failed and retains checkpoint; explicit resume restores exact physical state')
    run('release');assert w._session is None
    # Save while a verified live future is pending; disk must not imply success.
    started=threading.Event();gate=threading.Event();original_restore=g.GpuSession.restore
    def held(doc):
        started.set();gate.wait(5);raise RuntimeError('Controlled held request ended')
    g.GpuSession.restore=staticmethod(held)
    pending=run('resume');assert started.wait(2) and w._future[0].running()
    saved=OUT/'Pending native operation.blend'
    try:bpy.ops.wm.save_as_mainfile(filepath=str(saved))
    finally:gate.set();g.GpuSession.restore=original_restore
    assert wait(pending)['status']=='failed'
    checks.append('save records a live pending command and the last confirmed checkpoint without claiming completion')
    snapshot={'pending_id':pending['id'],'purpose':pending['purpose'],'accepted_state_id':before['state']['accepted_state_id'],'project':str(saved)}
    (OUT/'pending-expected.json').write_text(json.dumps(snapshot,indent=2))
    for path,digest in projects.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    checks.append('all original user projects remain byte-identical')
    report={'passed':True,'checks':checks,'native_failure':failure['error'],'saved_pending':snapshot,'preserved_projects':projects,'runtime':g.identity()}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2));print('SHARED_OPERATIONS_PASS',json.dumps(report),flush=True)
except Exception as error:
    (OUT/'failure.json').write_text(json.dumps({'passed':False,'checks':checks,'error':str(error),'traceback':traceback.format_exc()},indent=2));raise
finally:w.close_session()
