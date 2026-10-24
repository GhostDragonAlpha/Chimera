# SPDX-License-Identifier: AGPL-3.0-or-later
"""Native trial save/open through the shared human/AI operations boundary.

Dedicated A1 check: a construction saved through the shared operations path
writes the same .matter.json document the human 'Save GPU Matter Trial'
operator writes, reopens offline into a fresh state with an equal accepted
physical state, and every refusal (corrupt file, oversized file, relative
path, foreign root) leaves the accepted native state untouched. Exercises
ONLY the save_trial/open_trial paths; it never starts a GPU session and
never touches the foreign alloy/matter-card branches.
"""
import bpy,json,sys,hashlib,traceback
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence/trial-persistence';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'python'))
import chimera_studio
from chimera_studio import operations as op,gpu_workspace as w,gpu_native as g
chimera_studio.register()
report={'pass':False,'scope':'Shared save_trial/open_trial boundary: owner document round-trip, offline reopen, refusal set with no accepted-state change'}
checks=[]
def check(name,ok,detail=None):
    checks.append({'check':name,'pass':bool(ok),**({'detail':str(detail)} if detail is not None else {})})
    print('PASS' if ok else 'FAIL',name,'' if ok else detail,flush=True)

def propose(action,params):
    return op.propose(action,[],params,'Keep a saved construction reopenable through the same path a human uses')

def apply_ok(action,params):
    record=propose(action,params);applied=op.apply(record['id'])
    assert applied['status']!='failed',applied
    return applied

def fresh():
    # Simulate reopening offline: the same owner reset the load_pre handler performs.
    w._saved=None;w._visibility={};w._authoring=False

def synthetic_document():
    """A document the unchanged native owner validates, without starting GPU.

    The state fields follow gpu_native.validate_membrane_state exactly (the
    same FNV-1a accepted_state_id convention the engine uses), so the open
    path's g.validate_document gate accepts it like a real checkpoint."""
    spec=g.fixture_spec()
    flat=np.asarray(spec['positions'],dtype=float).reshape(-1,3).astype('<f4').reshape(-1)
    h=1469598103934665603
    for byte in flat.tobytes():h=((h^byte)*1099511628211)&0xffffffffffffffff
    state={'schema':'chimera.membrane_demo_state.v1','n_verts':len(spec['positions']),'n_faces':len(spec['triangles']),
           'centre_index':spec['centre'],'positions_f32':[float(v) for v in flat],'accepted_state_id':str(h),
           'gamma_admitted_f64':spec['gamma'],'gamma_uploaded_f32':spec['gamma'],'centre_load_N':0.,
           'energy_J':0.,'energy_initial_J':0.,'iteration':0,'n_accepted':0,'n_trials':0}
    doc={'schema':'chimera.studio.gpu-trial.v2','source_lock':g.identity(),'spec':spec,'state':state}
    g.validate_document(doc)
    return doc

try:
    doc=synthetic_document()
    w._saved=doc  # Seeded confirmed checkpoint: the owner mirror after a build/release.
    saved_id=doc['state']['accepted_state_id']
    actions=op.inspect()['actions']
    check('inspect advertises save_trial/open_trial','save_trial' in actions and 'open_trial' in actions,actions)

    target=ROOT/'.user/trial-persistence-headless.matter.json'
    if target.exists():target.unlink()
    record=apply_ok('save_trial',{'path':str(target)})
    check('apply save_trial drives the existing chimera.gpu_save operator',record['status']=='succeeded')
    saved=json.loads(target.read_text(encoding='utf-8'))
    owner=w.document()
    check('saved document digest equals the owner document digest',op.digest(saved)==op.digest(owner))
    check('saved accepted_state_id matches the owner accepted_state_id',saved['state']['accepted_state_id']==saved_id==owner['state']['accepted_state_id'])
    check('saved spec equals the owner spec',saved['spec']==owner['spec'])
    check('proposal preview carries the resolved trial path',record['preview']['trial_path']==str(target))
    report['saved_file_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()

    fresh()
    check('fresh state starts without a saved trial',w.document() is None)
    reopened=apply_ok('open_trial',{'path':str(target)})
    check('apply open_trial drives the existing chimera.gpu_open operator',reopened['status']=='succeeded')
    doc2=w.document()
    check('reopened accepted_state_id equals the saved accepted_state_id',doc2['state']['accepted_state_id']==saved_id)
    check('reopened spec equals the saved spec',doc2['spec']==saved['spec'])
    check('open leaves no running GPU session',w._session is None and not w.busy())
    before=op.digest(w.document())

    corrupt=ROOT/'.user/trial-persistence-corrupt.matter.json'
    corrupt.write_text('{"schema":"chimera.studio.gpu-trial.v2","source_lock":',encoding='utf-8')
    failed=op.apply(propose('open_trial',{'path':str(corrupt)})['id'])
    # The operator reports the parse failure and Blender re-raises it to apply;
    # the shared record ends 'failed' and the accepted state is untouched.
    check('corrupt trial file refused at apply',failed['status']=='failed' and bool(failed.get('error')),failed.get('error'))
    check('corrupt refusal leaves the accepted state unchanged',op.digest(w.document())==before)
    corrupt.unlink()

    big=ROOT/'.user/trial-persistence-oversized.matter.json'
    big.write_bytes(b'x'*(g.MAX_DOC+1))
    try:
        propose('open_trial',{'path':str(big)})
        check('oversized trial file refused at propose',False,'proposal was created')
    except ValueError as error:
        check('oversized trial file refused at propose','8 MiB' in str(error),error)
    check('oversized refusal leaves the accepted state unchanged',op.digest(w.document())==before)
    big.unlink()

    for label,action,value,needle in (('relative path','open_trial','.user/relative.matter.json','absolute'),
                               ('foreign root','open_trial','C:/Windows/Temp/foreign.matter.json','foreign'),
                               ('sibling root','open_trial','D:/Chimera-Maintenance-elsewhere/x.matter.json','foreign'),
                               ('save_trial relative path','save_trial','save-relative.matter.json','absolute')):
        try:
            propose(action,{'path':value})
            check(label+' refused at propose with a named reason',False,'proposal was created')
        except ValueError as error:
            check(label+' refused at propose with a named reason',needle in str(error),error)
    check('path refusals leave the accepted state unchanged',op.digest(w.document())==before)
    report['pass']=all(c['pass'] for c in checks)
except Exception:
    traceback.print_exc();report['error']=traceback.format_exc()
finally:
    fresh()  # Leave no seeded owner state behind.
report['checks']=checks;report['runtime']=g.identity()
(OUT/'trial-persistence-headless.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'pass':report['pass'],'checks':len(checks)}),flush=True)
raise SystemExit(0 if report['pass'] else 1)
