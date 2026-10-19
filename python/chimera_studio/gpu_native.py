# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small controls around the pinned existing Vulkan engine. No Python physics solver."""
import atexit
import base64
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import socket
import struct
import subprocess
import time
import uuid
import numpy as np
from .native import ROOT

_spec=importlib.util.spec_from_file_location('chimera_pinned_control',ROOT/'vendor/gpu/control_client.py')
_control=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_control)
MAX_VERTS=1024;MAX_FACES=2048;MAX_DOC=8*1024*1024

def identity(): return hashlib.sha256((ROOT/'GPU_SOURCE_LOCK.json').read_bytes()).hexdigest()
def digest(data): return hashlib.sha256(data).hexdigest()
def number(x,name,low,high): return _control.number(x,name,low,high)
def verify_runtime():
    for f in json.loads((ROOT/'GPU_SOURCE_LOCK.json').read_text())['files']:
        if f['copy'].replace('\\','/').startswith('runtime/gpu/') or f['copy'].endswith('control_client.py'):
            if digest((ROOT/f['copy']).read_bytes())!=f['sha256']:raise ValueError('Pinned GPU runtime changed: '+f['copy'])

def geometry(positions,triangles):
    p=np.asarray(positions,dtype=np.float64);t=np.asarray(triangles)
    if p.ndim!=2 or p.shape[1]!=3 or not 3<=len(p)<=MAX_VERTS or not np.isfinite(p).all() or np.abs(p).max()>1000:
        raise ValueError('Use 3–1024 finite vertices within 1000 meters')
    if t.ndim!=2 or t.shape[1]!=3 or not 1<=len(t)<=MAX_FACES or t.dtype.kind not in 'iu' or t.min()<0 or t.max()>=len(p):raise ValueError('Invalid triangle topology')
    p=p.astype('<f4');t=t.astype('<u4')
    area=np.linalg.norm(np.cross(p[t[:,1]].astype(float)-p[t[:,0]],p[t[:,2]].astype(float)-p[t[:,0]]),axis=1)*.5
    if (area<1e-10).any():raise ValueError('Degenerate triangle after float32 conversion')
    if len({tuple(sorted(x)) for x in t.tolist()})!=len(t):raise ValueError('Duplicate triangles')
    if len(np.unique(t))!=len(p):raise ValueError('Unused vertices')
    return p,t,area

def membrane_spec(positions,triangles,centre,gamma=1.):
    p,t,_=geometry(positions,triangles);number(gamma,'Surface tension J/m²',1e-6,1000)
    if type(centre)!=int or not 0<=centre<len(p):raise ValueError('Select exactly one free center vertex')
    # Existing GPU demonstration law: ONE z-rail free node; all others pinned.
    if not np.all(np.sum(t==centre,axis=1)==1):raise ValueError('Existing membrane law needs a triangle fan about the selected center')
    rim={i:[] for i in range(len(p)) if i!=centre}
    for face in t:
        a,b=[int(i) for i in face if i!=centre];rim[a].append(b);rim[b].append(a)
    if any(len(v)!=2 for v in rim.values()):raise ValueError('Fan rim must be one closed boundary')
    seen=set();todo=[next(iter(rim))]
    while todo:
        i=todo.pop()
        if i in seen:continue
        seen.add(i);todo.extend(rim[i])
    if len(seen)!=len(rim):raise ValueError('Disconnected fan rim')
    return {'mode':'membrane','positions':p.tolist(),'triangles':t.tolist(),'centre':centre,'gamma':float(gamma)}

def membrane_packet(spec):
    spec=validate_spec(spec)
    p=np.asarray(spec['positions'],dtype='<f4');t=np.asarray(spec['triangles'],dtype='<u4');flat=t.ravel()
    corners=np.argsort(flat,kind='stable').astype('<u4');offsets=np.concatenate(([0],np.cumsum(np.bincount(flat,minlength=len(p))))).astype('<u4')
    return struct.pack('<IIIIdfI',0x3130444D,len(p),len(t),spec['centre'],spec['gamma'],0.,0)+p.tobytes()+t.tobytes()+offsets.tobytes()+corners.tobytes()+np.full(len(t),spec['gamma'],dtype='<f4').tobytes()

def fixture_spec():
    f=ROOT/'vendor/gpu/fixture/b2'
    return membrane_spec(np.load(f/'geometry/positions_f32.npy').reshape(-1,3),np.load(f/'geometry/indices_u32.npy').reshape(-1,3),6)

def water_spec(positions,triangles,seed=0,volume=0.0001,pipe_height=.01):
    p,t,areas=geometry(positions,triangles);number(volume,'Water volume m³',1e-10,1);number(pipe_height,'Pipe height m',1e-6,1)
    if type(seed)!=int or not 0<=seed<len(t):raise ValueError('Select one water seed triangle')
    # Geometry and binary packing follow existing water_room/tri_water substrate.
    # Native water_color/depth/occ kernels alone update the CA field.
    p=p.astype(float);centers=p[t].mean(axis=1);primal={}
    for i,face in enumerate(t):
        for a,b in zip(face,np.roll(face,-1)):
            primal.setdefault(tuple(sorted((int(a),int(b)))),[]).append(i)
    if any(len(v)>2 for v in primal.values()):raise ValueError('Nonmanifold shared edge')
    edges=[]
    for (a,b),cells in sorted(primal.items()):
        if len(cells)==2:
            i,j=cells;length=float(np.linalg.norm(centers[i]-centers[j]));width=float(np.linalg.norm(p[a]-p[b]))
            if length<1e-8:raise ValueError('Coincident cell centers')
            edges.append((i,j,length,9.81*width*pipe_height/length))
    if not edges:raise ValueError('CA needs adjacent triangles sharing an edge')
    # Stable conflict-free color schedule; each edge touches two cells.
    used=[set() for _ in t];colored=[]
    for i,j,l,k in edges:
        c=0
        while c in used[i] or c in used[j]:c+=1
        used[i].add(c);used[j].add(c);colored.append((c,i,j,l,k))
    colored.sort(key=lambda e:e[0]);nc=1+max(e[0] for e in colored)
    q=volume/100000.;v=[0]*len(t);v[seed]=100000
    return {'mode':'water','positions':p.tolist(),'triangles':t.tolist(),'areas':areas.tolist(),'bed':centers[:,2].tolist(),
            'eij':[[e[1],e[2]] for e in colored],'lengths':[e[3] for e in colored],'conductance':[e[4] for e in colored],
            'colors':[0]+[sum(e[0]<c for e in colored) for c in range(1,nc+1)],'quantum':q,'gravity':9.81,'c_local':.05,
            'volumes':v,'seed':seed,'initial_volume':volume,'pipe_height':pipe_height,'dt':.01}

def validate_spec(s):
    if not isinstance(s,dict):raise ValueError('Expected GPU trial geometry')
    if s.get('mode')=='membrane':
        if 'assembly' in s:
            from .blocks import validate
            return validate(s)
        return membrane_spec(s['positions'],s['triangles'],s['centre'],s['gamma'])
    if s.get('mode')=='water':
        expected=water_spec(s['positions'],s['triangles'],s['seed'],s['initial_volume'],s['pipe_height'])
        if s!=expected:raise ValueError('CA geometry/coefficients differ from the declared substrate')
        return expected
    raise ValueError('Unknown native GPU mode')

def water_packet(s,volumes):
    v=np.asarray(volumes)
    n=len(s['triangles']);ne=len(s['eij']);nc=len(s['colors'])-1
    if v.shape!=(n,) or v.dtype.kind not in 'iu' or v.min()<0 or v.max()>2147483647:raise ValueError('Invalid integer CA volumes')
    # Same /water_bin protocol as the existing engine and water_room.pack_water_bin.
    return b''.join([struct.pack('<4I3d',n,ne,nc,0,s['quantum'],s['gravity'],s['c_local']),
                    np.asarray(s['areas'],dtype='<f8').tobytes(),np.asarray(s['bed'],dtype='<f8').tobytes(),v.astype('<i4').tobytes(),
                    np.zeros(n,dtype='<u4').tobytes(),np.asarray(s['eij'],dtype='<i4').tobytes(),
                    np.asarray(s['conductance'],dtype='<f8').tobytes(),np.asarray(s['lengths'],dtype='<f8').tobytes(),
                    np.ones(ne,dtype='<u4').tobytes(),np.asarray(s['colors'],dtype='<u4').tobytes()])

def fnv64(data):
    h=14695981039346656037
    for b in data:h=((h^b)*1099511628211)&0xffffffffffffffff
    return h

def water_state(raw,spec):
    # The native payload preserves raw float64 flow/depth bits, not decimal approximations.
    n=len(spec['triangles']);e=len(spec['eij'])
    if len(raw)!=88+12*n+8*e:raise ValueError('CA full checkpoint length mismatch')
    magic,version,nc,ne,substrate,steps,automatic,seconds,dt,csteps,target,count,flags,cdt=struct.unpack_from('<4I3Q2dIiiId',raw)
    if (magic,version,nc,ne)!=(0x31534357,1,n,e):raise ValueError('Unsupported CA full checkpoint')
    if substrate!=fnv64(water_packet(spec,spec['volumes'])):raise ValueError('CA checkpoint substrate mismatch')
    if struct.unpack_from('<Q',raw,len(raw)-8)[0]!=fnv64(raw[:-8]):raise ValueError('CA native checksum mismatch')
    if (automatic>steps or not math.isfinite(seconds) or seconds<0 or not math.isfinite(dt) or not 0<=dt<=1
        or (steps and (dt<=0 or seconds<=0)) or (not steps and (dt!=0 or seconds!=0))
        or not 1<=csteps<=4096 or not -1<=target<n or count<0 or flags!=0
        or not math.isfinite(cdt) or not 0<cdt<=1):raise ValueError('Invalid CA physical clock')
    v=np.frombuffer(raw,dtype='<i4',count=n,offset=80)
    flow=np.frombuffer(raw,dtype='<f8',count=e,offset=80+4*n)
    depth=np.frombuffer(raw,dtype='<f8',count=n,offset=80+4*n+8*e)
    if ((v<0).any() or int(v.sum())!=sum(spec['volumes']) or not np.isfinite(flow).all()
        or not np.isfinite(depth).all() or (depth<0).any()):raise ValueError('Invalid CA flow/depth or volume conservation')
    return {'format':'WCS1','volumes':v.tolist(),'steps':steps,'simulated_seconds':seconds,
            'full_state':base64.b64encode(raw).decode('ascii'),'sha256':digest(raw)}

def validate_water_state(state,spec):
    if not isinstance(state,dict) or not isinstance(state.get('full_state'),str):raise ValueError('Full native CA checkpoint required')
    try:raw=base64.b64decode(state['full_state'],validate=True)
    except Exception as exc:raise ValueError('Invalid CA checkpoint encoding') from exc
    expected=water_state(raw,spec)
    if state!=expected:raise ValueError('CA checkpoint fields/hash mismatch')
    return raw

def render_hash(data):
    h=1469598103934665603
    for b in data:h=((h^b)*1099511628211)&0xffffffffffffffff
    return str(h)


def validate_render(view,spec,state):
    if view.get('schema')!='chimera.studio.membrane-render.v1' or view.get('accepted_state_id')!=state['accepted_state_id']:
        raise ValueError('Render output belongs to a different physical state')
    a=np.frombuffer(bytes.fromhex(view['vertices9_f32_hex']),dtype='<f4')
    if a.shape!=(len(spec['positions'])*9,) or not np.isfinite(a).all():raise ValueError('Invalid native render vertex stream')
    if render_hash(a.tobytes())!=view['render_state_id']:raise ValueError('Render vertex hash mismatch')
    if view['indices']!=np.asarray(spec['triangles']).ravel().tolist():raise ValueError('Render topology mismatch')
    if view['lift_m']!=0:raise ValueError('Unexpected presentation lift')
    a=a.reshape(-1,9)
    # Exact inverse of the kernel's rigid axis mapping. No simulated motion here.
    physical=a[:,[0,2,1]].copy();physical[:,1]*=-1
    expected=np.asarray(state['positions_f32'],dtype='<f4').reshape(-1,3)
    if not np.array_equal(physical,expected):raise ValueError('Kernel render positions differ from accepted physics')
    return a,physical


def validate_document(doc):
    if not isinstance(doc,dict) or doc.get('schema')!='chimera.studio.gpu-trial.v2' or doc.get('source_lock')!=identity():raise ValueError('GPU trial runtime identity mismatch')
    if len(json.dumps(doc,allow_nan=False))>MAX_DOC:raise ValueError('GPU trial exceeds size limit')
    spec=validate_spec(doc['spec']);state=doc.get('state')
    if not isinstance(state,dict):raise ValueError('Missing native checkpoint')
    if spec['mode']=='water':
        validate_water_state(state,spec)
    else:
        if state.get('schema')!='chimera.membrane_demo_state.v1' or state.get('n_verts')!=len(spec['positions']) or state.get('n_faces')!=len(spec['triangles']) or state.get('centre_index')!=spec['centre']:raise ValueError('Membrane checkpoint geometry mismatch')
        points=np.asarray(state['positions_f32'],dtype=float)
        if points.shape!=(3*len(spec['positions']),) or not np.isfinite(points).all() or np.abs(points).max()>1000:raise ValueError('Invalid membrane checkpoint positions')
        h=1469598103934665603  # Existing md_fnv1a / native_view.accepted_hash convention.
        for byte in points.astype('<f4').tobytes():h=((h^byte)*1099511628211)&0xffffffffffffffff
        if state.get('accepted_state_id')!=str(h):raise ValueError('Membrane checkpoint state hash mismatch')
        for key in ('gamma_admitted_f64','gamma_uploaded_f32','centre_load_N','energy_J','energy_initial_J'):number(state.get(key),key,0,1e12)
        for key in ('iteration','n_accepted','n_trials'):
            if type(state.get(key))!=int or not 0<=state[key]<=0xffffffff:raise ValueError('Invalid native counter')
    if 'assembly' in spec and 'render' not in doc:raise ValueError('Assembly requires a confirmed native render snapshot')
    if spec['mode']=='membrane' and 'render' in doc:validate_render(doc['render'],spec,state)
    return doc

class PrivateEngine:
    def __init__(self):
        self.proc=None;self.logs=[];self.job=None;verify_runtime()
        # Bounded small-scene launch; never unload a model to make room.
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        r=subprocess.run(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=8,creationflags=flags)
        if r.returncode or int(r.stdout.splitlines()[0])<384:raise RuntimeError('GPU busy: need 384 MiB free; models left running')
        with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
        self.folder=ROOT/'.user/gpu-runs'/uuid.uuid4().hex;self.folder.mkdir(parents=True)
        self.logs=[(self.folder/'stdout.log').open('wb'),(self.folder/'stderr.log').open('wb')]
        startup=None
        if os.name=='nt':
            startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
        # Working directory must contain the pinned shaders; state writes are confined to a per-run directory.
        import shutil
        shutil.copytree(ROOT/'runtime/gpu/shaders',self.folder/'shaders')
        self.proc=subprocess.Popen([str(ROOT/'runtime/gpu/chimera_engine.exe'),str(port),'--no-board','384','256','--no-restore','--hidden'],cwd=self.folder,stdout=self.logs[0],stderr=self.logs[1],creationflags=flags,startupinfo=startup,env={**os.environ,'CHIMERA_STUDIO_OFFSCREEN':'1'})
        from .owned_job import OwnedJob
        try:self.job=OwnedJob(self.proc)
        except BaseException:self.close();raise
        self.control=_control.EngineControl(f'http://127.0.0.1:{port}',timeout=12)
        try:
            deadline=time.monotonic()+25
            while time.monotonic()<deadline:
                if self.proc.poll() is not None:raise RuntimeError('Private GPU engine exited: '+str(self.folder))
                try:
                    # Verify port ownership before issuing a mutation to the engine.
                    result=subprocess.run(['powershell','-NoProfile','-Command',f'(Get-NetTCPConnection -State Listen -LocalPort {port} -ErrorAction SilentlyContinue).OwningProcess'],capture_output=True,text=True,timeout=5,creationflags=flags)
                    owners={int(x) for x in result.stdout.split() if x.isdigit()}
                    if owners and owners!={self.proc.pid}:raise RuntimeError('Private GPU port is owned by another process')
                    if owners=={self.proc.pid}:
                        self.control.telemetry();break
                except OSError:pass
                time.sleep(.1)
            else:raise TimeoutError('Private GPU startup timed out')
        except BaseException:self.close();raise
        atexit.register(self.close)
    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=5)
        if self.job:self.job.close();self.job=None
        for f in self.logs:f.close()
        self.logs=[]
        atexit.unregister(self.close)
    def request(self,*a,**kw):
        if not self.proc or self.proc.poll() is not None:raise RuntimeError('Private GPU engine closed; saved checkpoints remain available')
        try:return self.control.request(*a,**kw)
        except (OSError,TimeoutError):
            self.close();raise RuntimeError('Private GPU request failed/timed out; no automatic retry. Last confirmed checkpoint retained.') from None

class GpuSession:
    def __init__(self,spec):
        self.spec=validate_spec(spec);self.engine=PrivateEngine();self.state=None;self.render=None;self.history=[];self.cursor=-1;self.elapsed_steps=0;self.batch_steps=0;self.last_ms=0
        try:
            if self.spec['mode']=='membrane':self.engine.request('POST','/membrane_demo_bin',membrane_packet(self.spec))
            else:self.engine.request('POST','/water_bin',water_packet(self.spec,self.spec['volumes']))
            self.snapshot();self.record()
        except BaseException:self.close();raise
    def close(self):self.engine.close()
    def snapshot(self):
        if self.spec['mode']=='membrane':
            state=self.engine.request('GET','/membrane_demo_save')
            if state.get('schema')!='chimera.membrane_demo_state.v1':raise RuntimeError('Native membrane save API unavailable')
        else:
            raw=self.engine.request('GET','/water_save',binary=True)
            state=water_state(raw,self.spec)
            self.elapsed_steps=state['steps'];self.batch_steps=self.elapsed_steps
        render=None
        if self.spec['mode']=='membrane':
            render=self.engine.request('GET','/membrane_demo_render')
            validate_render(render,self.spec,state)
        self.state=state;self.render=render;return state
    def record(self):
        raw=json.dumps(self.state,allow_nan=False,separators=(',',':'))
        self.history=self.history[:self.cursor+1];self.history.append(raw)
        while len(self.history)>240 or sum(map(len,self.history))>MAX_DOC:self.history.pop(0)
        self.cursor=len(self.history)-1
    def advance(self,count=1):
        limit=64 if self.spec['mode']=='water' else 8
        if type(count)!=int or not 1<=count<=limit:raise ValueError(f'Advance 1–{limit} explicit GPU iterations')
        t=time.perf_counter()
        if self.spec['mode']=='membrane':
            self.engine.request('POST','/membrane_demo',{'op':'step' if count==1 else 'run','n_steps':count})
        else:
            # Native ring storage is bounded; the physical clock and q_e continue.
            # One batch executes EVERY requested step, in the same color order.
            self.engine.request('POST','/water_step',{'n_macro':count,'dt_macro':self.spec['dt']})
        self.snapshot();self.record();self.last_ms=(time.perf_counter()-t)*1000
    def deform(self,load):
        if self.spec['mode']!='membrane':raise ValueError('Load applies to the membrane only')
        number(load,'Center load N',0,10)
        r=self.engine.request('POST','/membrane_demo',{'op':'deform','load_N':load})
        if any(x in r.get('status',r).get('last_control','').upper() for x in ('REJECTED','REFUSED')):raise ValueError('Native membrane refused load')
        self.snapshot();self.record()
    def restore_state(self,state):
        if self.spec['mode']=='membrane':
            self.engine.request('POST','/membrane_demo_restore',state)
        else:
            raw=validate_water_state(state,self.spec)  # All checks before any mutation.
            self.engine.request('POST','/water_restore',raw)
        restored=self.snapshot()
        # Native restore adds descriptive hex-placeholder fields to material_snapshot.
        # Compare every physical value/hash; descriptive enrichment is not physical state drift.
        keys=set(restored)|set(state)
        if any(restored.get(k)!=state.get(k) for k in keys-{'material_snapshot'}):raise ValueError('Native checkpoint did not round-trip exactly')
        for k,v in state.get('material_snapshot',{}).items():
            if restored.get('material_snapshot',{}).get(k)!=v:raise ValueError('Native material identity changed')
    def seek(self,index):
        if type(index)!=int or not 0<=index<len(self.history):raise ValueError('Checkpoint outside recorded range')
        self.restore_state(json.loads(self.history[index]));self.cursor=index
    def document(self):
        # Last confirmed checkpoint; safe to save even after native timeout.
        doc={'schema':'chimera.studio.gpu-trial.v2','source_lock':identity(),'spec':self.spec,'state':self.state}
        if self.render is not None:doc['render']=self.render
        return doc
    @classmethod
    def restore(cls,doc):
        validate_document(doc)
        obj=cls(doc['spec'])
        try:obj.restore_state(doc['state']);obj.history=[];obj.cursor=-1;obj.record();return obj
        except BaseException:obj.close();raise
