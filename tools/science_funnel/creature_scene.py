"""Graph-pinned creature binding -> one native membrane body -> existing game shell.
Setup only; all subsequent pose/press/deformation happens inside the native engine.
"""
from pathlib import Path
import argparse, hashlib, json, struct, urllib.request
from urllib.parse import urlparse
import numpy as np
from tools.creature_graph.store import CreatureGraph
from .common import require
ROOT = Path(__file__).resolve().parents[2]

def compile_scene(output):
    graph = CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
    require(not graph.check(), 'graph_invalid')
    work = graph.get('work.creature.unified_body')
    require('reference_stage' in work['physical']['contract'], 'missing_work_contract')
    asset = graph.get('req.creature_assembly')['physical']['contract']['current_asset']
    source = {}
    for key in ('mesh', 'binding'):
        data = (ROOT/asset[key]).read_bytes()
        require(hashlib.sha256(data).hexdigest() == asset[key+'_sha256'], 'asset_pin_drift', key)
        source[key] = data
    mesh = source['mesh']; nv, nf = struct.unpack_from('<II', mesh)
    require(len(mesh) == 8+12*nv+12*nf, 'mesh_length')
    xyz = np.frombuffer(mesh, dtype='<f4', count=3*nv, offset=8).reshape(nv, 3)
    triangles = np.frombuffer(mesh, dtype='<u4', count=3*nf, offset=8+12*nv).reshape(nf, 3)
    require(np.isfinite(xyz).all() and triangles.max() < nv, 'mesh_data')
    normals = np.zeros((nv, 3), dtype=np.float64)
    a, b, c = (xyz[triangles[:, i]].astype(np.float64) for i in range(3))
    face_normals = np.cross(b-a, c-a)
    for i in range(3): np.add.at(normals, triangles[:, i], face_normals)
    length = np.linalg.norm(normals, axis=1)
    normals[length>0] /= length[length>0, None]
    vertices = np.empty((nv, 9), dtype='<f4')
    vertices[:, :3] = xyz; vertices[:, 3:6] = normals
    vertices[:, 6:] = [0.65, 0.42, 0.25]  # presentation color; not material data
    payload = struct.pack('<IIffff', nv, 3*nf, 16., 0., .25, 0.) + vertices.tobytes() + triangles.tobytes()
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    (output/'mesh.bin').write_bytes(payload)
    (output/'body.bin').write_bytes(source['binding'])
    scene = {'schema':'chimera.shared_body_example.v1','graph_hash':graph.graph_hash(),
        'work_id':work['id'],'source_mesh_sha256':asset['mesh_sha256'],
        'source_binding_sha256':asset['binding_sha256'], 'vertices':nv,'triangles':nf,
        'mesh_payload_sha256':hashlib.sha256(payload).hexdigest(),
        'model':'JNT3_hierarchical','actuation':'kinematic','solver':'native CPU membrane reference with Vulkan rendering',
        'scope':'Whole surface follows one hierarchy, touch surface and seal inventory. One demonstration cut, not per-bone anatomical reconstruction.',
        'unit_convention':'Existing engine interprets one world unit as one metre; source anatomical scale is not independently calibrated. No silent rescaling.',
        'seals':[{'y':1.0,'cell':0}], 'known_gaps':['force-driven joints','6-DOF root','GPU-resident membrane dynamics','fixed simulation clock','layered anatomy fitting','qualified reflex behavior']}
    (output/'scene.json').write_text(json.dumps(scene, indent=2)+'\n', encoding='utf-8')
    return scene

def request(base, route, payload=None, binary=False):
    data = payload if binary else (None if payload is None else json.dumps(payload).encode())
    req=urllib.request.Request(base+route, data=data, headers={'Content-Type':'application/octet-stream' if binary else 'application/json'})
    with urllib.request.urlopen(req,timeout=60) as response: result=json.load(response)
    if data is not None: require(result.get('ok') is True,'engine_refused',result)
    return result

def load_scene(output, engine):
    parsed=urlparse(engine)
    require(parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost') and parsed.path in ('','/'), 'private_loopback_engine_required')
    engine=engine.rstrip('/'); output=Path(output)
    state=request(engine,'/tick_state')
    require(state.get('reflex_cell_count',0)==0,'engine_not_empty','Launch an isolated engine with --no-restore; do not replace a running world.')
    scene=json.loads((output/'scene.json').read_text(encoding='utf-8'))
    mesh=(output/'mesh.bin').read_bytes();binding=(output/'body.bin').read_bytes()
    require(hashlib.sha256(mesh).hexdigest()==scene['mesh_payload_sha256'],'compiled_mesh_drift')
    require(hashlib.sha256(binding).hexdigest()==scene['source_binding_sha256'],'compiled_binding_drift')
    request(engine,'/mesh_bin',mesh,True);request(engine,'/tick_body_bin',binding,True)
    for seal in scene['seals']: request(engine,'/tick_seal',seal)
    state=request(engine,'/tick_state'); require(state.get('body_model')==scene['model'],'body_model_not_active')
    (output/'loaded.json').write_text(json.dumps({'engine':engine,'scene':scene,'state':state},indent=2)+'\n',encoding='utf-8')
    return {'engine':engine,'body_model':state['body_model'],'cells':state['n_cells'],'graph_hash':scene['graph_hash']}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=ROOT/'.tmp/creature-assembly');ap.add_argument('--engine')
    args=ap.parse_args();scene=compile_scene(args.output)
    print(json.dumps(load_scene(args.output,args.engine) if args.engine else scene,indent=2))
if __name__=='__main__': main()
