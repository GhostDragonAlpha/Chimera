"""Render measured AP01 snapshots through the existing private native engine."""
import shutil
import socket
import subprocess
import time
from pathlib import Path
import numpy as np
from tools.python_control.client import EngineControl
from tools.membrane_demo_client import md01_packet
from tools.membrane_scale_lab.surface_energy_reference import build_vertex_corner_adjacency, evaluate_surface
from .core import geometry,require,file_hash

def accepted_hash(positions):
    # Match the existing engine's documented FNV seed (not the standard FNV offset).
    h=1469598103934665603
    for b in np.asarray(positions,dtype='<f4').tobytes():h=((h^b)*1099511628211)&0xffffffffffffffff
    return h

def capture(recipes, output, executable, port=8829):
    with socket.socket() as sock:
        require(sock.connect_ex(('127.0.0.1',port))!=0,'native_port_occupied')
    native=output/'native'
    if native.exists():native=output/f'native-retry-{time.time_ns()}'
    native.mkdir(exist_ok=False)
    executable=executable.resolve();exe=native/executable.name
    shutil.copy2(executable,exe);shutil.copytree(executable.parent/'shaders',native/'shaders')
    records=[];proc=None
    try:
        with (native/'stdout.log').open('wb') as out,(native/'stderr.log').open('wb') as err:
            proc=subprocess.Popen([str(exe),str(port),'--hidden','1280','720','--no-restore'],cwd=native,stdout=out,stderr=err,
                                  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            engine=EngineControl(f'http://127.0.0.1:{port}',timeout=15)
            for _ in range(100):
                require(proc.poll() is None,'private_engine_exited')
                try:engine.telemetry();break
                except OSError:time.sleep(.2)
            else:raise RuntimeError('private_engine_readiness_timeout')
            for r in recipes:
                pos,faces=geometry(r,.217);pos=pos.astype('<f4');faces=faces.astype('<u4')
                offsets,corners=build_vertex_corner_adjacency(faces.astype(np.int64),len(pos))
                packet={'pos':pos.ravel(),'idx':faces.ravel(),'csr_off':offsets.astype('<u4'),
                        'csr_cor':corners.astype('<u4'),'gamma_face':np.ones(len(faces),dtype='<f4')}
                ref=evaluate_surface(pos.astype(float),faces.astype(np.int64),1.)
                engine.membrane.upload(md01_packet(packet,1.));engine.membrane.pause()
                status=engine.membrane.state();status=status.get('status',status)
                require(abs(status['energy']-ref.energy)<=3e-5 and abs(status['centre_force'][2]-ref.vertex_forces[6,2])<=3e-5,'native_snapshot_physics_mismatch')
                engine.request('POST','/camera',{'cam_radius':4.,'cam_theta':.4,'cam_phi':.6})
                require(status['accepted_state_id']==accepted_hash(pos),'native_upload_identity_mismatch')
                frame=engine.frame()
                rendered=engine.membrane.state();rendered=rendered.get('status',rendered)
                require(rendered['accepted_state_id']==status['accepted_state_id'],'native_state_changed_during_capture')
                status=rendered
                name=native.name+'/'+r['id']+'-native.png';(output/name).write_bytes(frame)
                records.append({'recipe_id':r['id'],'status':status,'capture':name,'capture_sha256':file_hash(output/name)})
        return {'scope':'native physical-state upload and numerical response verified; captures observational only',
                'render_binding':'UNQUALIFIED: rendered-byte hash is not populated by this native build; it is also a different hash schema from accepted positions',
                'native_executable':str(executable),'native_sha256':file_hash(executable),
                'shader_hashes':{str(p.relative_to(native)):file_hash(p) for p in (native/'shaders').rglob('*.spv')},'records':records}
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
