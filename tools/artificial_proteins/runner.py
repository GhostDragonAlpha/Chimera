"""Reproducible AP01 discovery/characterization/composition batch, with resumable receipts."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
from tools.membrane_scale_lab.surface_energy_reference import evaluate_surface
from .core import (ROOT,Refusal,require,recipe,geometry,detailed,digest,file_hash,
                   source_hashes,table_from_samples,Response,equilibrium,validate_table)
from .verify import verify_samples,verify_assembly,analytic

SCHEMA='chimera.artificial_protein.run.v1'

def write(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.partial')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(path)

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def cases_for(recipes):
    cases=[]
    for r in recipes:
        for j,u in enumerate(np.linspace(-.4,.4,65)):
            cases.append({'id':f"{r['id']}_train_{j}",'recipe':r,'h':float(u),'scale':1.,'gamma':1.,'split':'train'})
        rng=np.random.default_rng(8100+r['seed'])
        for scale in [.5,1.,2.]:
            for j,u in enumerate(rng.uniform(-.39,.39,17)):
                cases.append({'id':f"{r['id']}_held_{scale}_{j}",'recipe':r,'h':float(u*scale),'scale':scale,'gamma':1.,'split':'heldout'})
        cases.append({'id':f"{r['id']}_zero",'recipe':r,'h':.125,'scale':1.,'gamma':0.,'split':'control'})
    return cases

def memory_snapshot():
    result={}
    try:
        p=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
        if p.returncode==0:result['gpu_used_total_mib']=p.stdout.strip()
    except (OSError,subprocess.TimeoutExpired):pass
    try:
        import psutil
        result['host_available_bytes']=psutil.virtual_memory().available
        result['python_rss_bytes']=psutil.Process().memory_info().rss
    except ImportError:pass
    return result

def run_gpu(cases,out,exe,resume):
    require(os.environ.get('CHIMERA_GPU_LEASE_PID') is not None,'managed_gpu_reservation_required')
    exe=exe.resolve();shader=exe.with_name('membrane.comp.spv')
    require(exe.is_file() and shader.is_file(),'gpu_build_missing')
    allpos=[];allfaces=[];gam=[];refs=[]
    for i,c in enumerate(cases):
        pos,faces=geometry(c['recipe'],c['h'],c['scale'])
        pos=pos.astype(np.float32).astype(float)
        ev=evaluate_surface(pos,faces,c['gamma'])
        refs.append(ev);allpos.extend(pos.tolist());allfaces.extend((faces+i*7).tolist());gam.extend([c['gamma']]*6)
    require(len(allpos)<=32768,'gpu_batch_budget_exceeded')
    text=f"1 {len(allpos)} {len(allfaces)}\n"
    text+=''.join(' '.join(format(x,'.9g') for x in row)+'\n' for row in allpos)
    text+=''.join(f'{row[0]} {row[1]} {row[2]} {g}\n' for row,g in zip(allfaces,gam))
    inp=out/'gpu-input.txt';inp.write_text(text,encoding='ascii')
    key={'input':file_hash(inp),'exe':file_hash(exe),'shader':file_hash(shader),'exe_path':str(exe),'shader_path':str(shader)}
    raw=out/'gpu-raw.json';meta=out/'gpu-checkpoint.json'
    before=memory_snapshot()
    if resume and raw.exists() and meta.exists():
        m=read(meta);require(m['inputs']==key and m['output']==file_hash(raw),'stale_gpu_checkpoint')
    else:
        proc=subprocess.run([str(exe),str(inp),str(raw),str(shader)],capture_output=True,text=True,timeout=120)
        (out/'gpu-stdout.txt').write_text(proc.stdout,encoding='utf-8');(out/'gpu-stderr.txt').write_text(proc.stderr,encoding='utf-8')
        require(proc.returncode==0,'gpu_execution_failed')
        write(meta,{'inputs':key,'output':file_hash(raw)})
    data=read(raw)
    forces=np.asarray(data['forces']);areas=np.asarray(data['areas'])
    require(forces.shape==(len(cases)*7,3) and areas.shape==(len(cases)*6,) and np.isfinite(forces).all() and np.isfinite(areas).all(),'invalid_gpu_output')
    values=[];worst=0.
    for i,(c,ref) in enumerate(zip(cases,refs)):
        f=forces[i*7:(i+1)*7];energy=float(np.sum(areas[i*6:(i+1)*6])*c['gamma'])
        norm=c['gamma']*c['scale'] if c['gamma'] else 1.
        ferr=float(np.max(np.abs(f-ref.vertex_forces)))/norm
        eerr=abs(energy-ref.energy)/(c['gamma']*c['scale']**2 if c['gamma'] else 1.)
        require(max(ferr,eerr)<=3e-5,'gpu_triangle_parity_failed')
        worst=max(worst,ferr,eerr)
        values.append({'energy':energy,'reaction':float(-f[6,2])})
    return values,{'device':data['device'],'setup_and_dispatch_s':data['setup_and_dispatch_s'],
                   'worst_triangle_parity_normalized':worst,'inputs':key,'memory_before':before,'memory_after_process_exit':memory_snapshot()}

def compose(recipes,artifacts):
    responses=[Response(a) for a in artifacts]
    a,b=recipes[:2];ra,rb=responses[:2]
    anchors=(-.1,.1);interval=(-.29,.29)
    report=[]
    pair=[(ra,anchors[0]),(rb,anchors[1])]
    for load in [-.4,.25]:
        measured=equilibrium(pair,load,interval)
        check=verify_assembly([(a,anchors[0]),(b,anchors[1])],load,interval,measured)
        report.append({'load_n':load,'result':measured,'verification':check})
    # External response of this specific pair retains its two anchors and child IDs.
    x=np.linspace(-.29,.29,65)
    values=[{'reaction':sum(fn(float(q-anchor))['reaction'] for fn,anchor in pair),
             'energy':sum(fn(float(q-anchor))['energy'] for fn,anchor in pair)} for q in x]
    composite=table_from_samples(x,[v['reaction'] for v in values],values[0]['energy'],
                  recipe_hash=digest({'children':[artifacts[0]['sha256'],artifacts[1]['sha256']],'anchors':anchors}),
                  lineage=[{'artifact':artifacts[i]['sha256'],'anchor_m':anchors[i]} for i in range(2)])
    cr=Response(composite);third=responses[2];rthird=recipes[2]
    reuse=[]
    for anchor,load in [(-.08,-.25),(.13,.35)]:
        measured=equilibrium([(cr,0.),(third,anchor)],load,(-.25,.25))
        detail=[(a,anchors[0]),(b,anchors[1]),(rthird,anchor)]
        check=verify_assembly(detail,load,(-.25,.25),measured,recursive=True)
        reuse.append({'frozen_composite':composite['sha256'],'third_anchor_m':anchor,'load_n':load,'result':measured,'verification':check})
    return composite,{'pair':report,'recursive_reuse':reuse,'scope':'one shared scalar rail DOF; fixed supports; no dynamics or general multiport qualification'}

def benchmark(r,a):
    response=Response(a);q=np.linspace(-.38,.38,200)
    results={}
    for name,fn in [('triangle_reference',lambda h:detailed(r,h)),('analytic',lambda h:analytic(r,h)),('table',response)]:
        times=[]
        for _ in range(3):
            start=time.perf_counter()
            for h in q:fn(float(h))
            times.append((time.perf_counter()-start)/len(q))
        results[name+'_median_seconds_per_call']=float(np.median(times))
    results['scope']='Python scalar call including validation/allocation; not game or GPU speedup'
    return results

def run(out,gpu_exe=None,resume=False,engine_exe=None):
    if not resume:out.mkdir(parents=True,exist_ok=False)
    require(out.is_dir(),'output_missing')
    recipes=[recipe(i) for i in range(3)];cases=cases_for(recipes)
    identity={'schema':SCHEMA,'source_hashes':source_hashes(),'case_manifest_hash':digest(cases),'backend':'vulkan' if gpu_exe else 'cpu','native_view_requested':engine_exe is not None}
    identity_path=out/'identity.json'
    if resume:
        require(read(identity_path)==identity,'stale_resume_inputs')
        if (out/'receipt.json').exists():
            check(out)
            return read(out/'receipt.json')
    else:write(identity_path,identity)
    write(out/'case-manifest.json',cases)
    start=time.perf_counter()
    try:
        if gpu_exe:values,gpu=run_gpu(cases,out,gpu_exe,resume)
        else:
            values=[{k:v for k,v in detailed(c['recipe'],c['h'],c['scale'],c['gamma']).items() if k in ('energy','reaction')} for c in cases];gpu=None
        reference=verify_samples(cases,values,'gpu' if gpu_exe else 'cpu')
        write(out/'measurements.json',values)
        artifacts=[];table_checks=[]
        for r in recipes:
            train=[(c,v) for c,v in zip(cases,values) if c['recipe']['id']==r['id'] and c['split']=='train']
            a=table_from_samples([c['h'] for c,v in train],[v['reaction'] for c,v in train],train[0][1]['energy'],recipe_hash=digest(r))
            fn=Response(a);held=[c for c in cases if c['recipe']['id']==r['id'] and c['split']=='heldout']
            result=verify_samples(held,[fn(c['h'],c['scale'],c['gamma']) for c in held],'table')
            write(out/(r['id']+'-table.json'),a);artifacts.append(a);table_checks.append(result)
        composite,assemblies=compose(recipes,artifacts);write(out/'composite-table.json',composite)
        write(out/'assembly-comparison.json',assemblies)
        functions=[]
        for r,a in zip(recipes,artifacts):
            fn=Response(a)
            functions.append({'recipe_id':r['id'],'artifact_sha256':a['sha256'],'function':'opposes normal port displacement under fixed rim and rail constraints',
                'response_at_0_2_m_n':fn(.2)['reaction'],'domain':a['x'][0:1]+a['x'][-1:],
                'not_supported':['inertia','damage','general folding','mass inventory','unconstrained assembly'],
                'new_question':'Does this function remain useful when a second independent port is introduced?'})
        write(out/'function-cards.json',functions)
        native_view=None
        if engine_exe:
            require(os.environ.get('CHIMERA_GPU_LEASE_PID') is not None,'managed_gpu_reservation_required')
            if resume and (out/'native-view.json').exists():
                native_view=read(out/'native-view.json')
                require(native_view['native_sha256']==file_hash(engine_exe),'stale_native_build')
                for rel,h in native_view['shader_hashes'].items():
                    require(file_hash(engine_exe.resolve().parent/rel)==h,'stale_native_shader')
                for record in native_view['records']:
                    require(file_hash(out/record['capture'])==record['capture_sha256'],'stale_native_capture')
            else:
                from .native_view import capture
                native_view=capture(recipes,out,engine_exe)
                write(out/'native-view.json',native_view)
        receipt={**identity,'status':'PASS','authority':'local numerical verification only; independent release review required',
                 'scope':'AP01 constrained fan response, response table and scalar coupled/reduced assembly',
                 'reference':reference,'tables':table_checks,'assembly':assemblies,'gpu':gpu,'native_view':native_view,
                 'benchmark':benchmark(recipes[0],artifacts[0]),'elapsed_s':time.perf_counter()-start,
                 'unimplemented':['Noether learned model','general multiport coupling','gameplay admission','controller attestation','dynamic physics']}
        files=['identity.json','case-manifest.json','measurements.json','composite-table.json','assembly-comparison.json','function-cards.json']+[r['id']+'-table.json' for r in recipes]
        if gpu_exe:files+=['gpu-input.txt','gpu-raw.json','gpu-checkpoint.json']
        if native_view:files+=['native-view.json']+[r['capture'] for r in native_view['records']]
        receipt['artifacts']={f:file_hash(out/f) for f in files}
        write(out/'receipt.json',receipt)
        return receipt
    except BaseException as e:
        write(out/'failure.json',{'status':'INTERRUPTED' if isinstance(e,KeyboardInterrupt) else 'FAIL','reason':str(e),'source_hashes':identity['source_hashes'],'elapsed_s':time.perf_counter()-start})
        raise

def check(out):
    receipt=read(out/'receipt.json')
    require(receipt.get('schema')==SCHEMA and receipt.get('source_hashes')==source_hashes(),'stale_sources')
    expected_cases=cases_for([recipe(i) for i in range(3)])
    require(read(out/'case-manifest.json')==expected_cases,'case_manifest_changed')
    expected_files={'identity.json','case-manifest.json','measurements.json','composite-table.json','assembly-comparison.json','function-cards.json'}|{f'ap01_{i}-table.json' for i in range(3)}
    if receipt['backend']=='vulkan':expected_files|={'gpu-input.txt','gpu-raw.json','gpu-checkpoint.json'}
    else:require(receipt['backend']=='cpu','unknown_backend')
    if receipt.get('native_view_requested'):
        native=read(out/'native-view.json')
        require(len(native['records'])==3 and {r['recipe_id'] for r in native['records']}=={f'ap01_{i}' for i in range(3)},'missing_native_cases')
        captures=set()
        for record in native['records']:
            rel=Path(record['capture'])
            require(not rel.is_absolute() and len(rel.parts)==2 and rel.parts[0].startswith('native') and rel.name==record['recipe_id']+'-native.png' and '..' not in rel.parts,'invalid_capture_path')
            captures.add(record['capture'])
        expected_files|={'native-view.json'}|captures
    require(set(receipt.get('artifacts',{}))==expected_files,'missing_receipt_artifacts')
    for name,h in receipt['artifacts'].items():require((out/name).is_file() and file_hash(out/name)==h,'artifact_changed:'+name)
    measurements=read(out/'measurements.json')
    verify_samples(expected_cases,measurements,'gpu' if receipt['backend']=='vulkan' else 'cpu')
    if receipt['backend']=='vulkan':
        checkpoint=read(out/'gpu-checkpoint.json');inputs=checkpoint['inputs'];raw=read(out/'gpu-raw.json')
        require(file_hash(out/'gpu-input.txt')==inputs['input'] and file_hash(out/'gpu-raw.json')==checkpoint['output'],'gpu_checkpoint_changed')
        require(file_hash(inputs['exe_path'])==inputs['exe'] and file_hash(inputs['shader_path'])==inputs['shader'],'stale_gpu_build')
        require(len(raw['forces'])==7*len(expected_cases) and len(raw['areas'])==6*len(expected_cases),'missing_gpu_cases')
        for i,(c,v) in enumerate(zip(expected_cases,measurements)):
            require(v['reaction']==-raw['forces'][7*i+6][2] and abs(v['energy']-sum(raw['areas'][6*i:6*(i+1)])*c['gamma'])<1e-12,'gpu_measurement_binding_failed')
    if receipt.get('native_view_requested'):
        native=read(out/'native-view.json')
        require(file_hash(native['native_executable'])==native['native_sha256'],'stale_native_build')
        for rel,h in native['shader_hashes'].items():
            require(file_hash(Path(native['native_executable']).parent/rel)==h,'stale_native_shader')
        for record in native['records']:
            require(file_hash(out/record['capture'])==record['capture_sha256'],'native_capture_changed')
            i=int(record['recipe_id'].split('_')[-1]);pos,faces=geometry(recipe(i),.217)
            ref=evaluate_surface(pos.astype(np.float32).astype(float),faces,1.)
            status=record['status']
            require(abs(status['energy']-ref.energy)<=3e-5 and abs(status['centre_force'][2]-ref.vertex_forces[6,2])<=3e-5,'native_reference_mismatch')
            from .native_view import accepted_hash
            require(status['accepted_state_id']==accepted_hash(pos),'native_upload_identity_mismatch')
        require(native.get('render_binding','').startswith('UNQUALIFIED:'),'unsupported_render_qualification')

    artifacts=[read(out/f'ap01_{i}-table.json') for i in range(3)]
    for i,a in enumerate(artifacts):
        require(a['recipe_hash']==digest(recipe(i)),'recipe_identity_mismatch')
        fn=Response(a);held=[c for c in expected_cases if c['recipe']['id']==f'ap01_{i}' and c['split']=='heldout']
        verify_samples(held,[fn(c['h'],c['scale'],c['gamma']) for c in held],'table')
    composite,assemblies=compose([recipe(i) for i in range(3)],artifacts)
    require(composite==read(out/'composite-table.json'),'composite_changed')
    require(assemblies==read(out/'assembly-comparison.json'),'assembly_changed')
    require(receipt['status']=='PASS','receipt_not_pass')
    return {'status':'PASS','scope':'freshness and independently recomputed scalar physics; no release attestation'}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run','check']);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--gpu-exe',type=Path);p.add_argument('--engine-exe',type=Path);p.add_argument('--resume',action='store_true');a=p.parse_args()
    try:
        result=run(a.out.resolve(),a.gpu_exe,a.resume,a.engine_exe) if a.action=='run' else check(a.out.resolve())
        print(json.dumps({k:result[k] for k in ['status','scope']},indent=2));return 0
    except (Refusal,OSError,ValueError,KeyError,subprocess.TimeoutExpired) as e:
        print(json.dumps({'status':'FAIL','reason':str(e)}));return 1
if __name__=='__main__':sys.exit(main())
