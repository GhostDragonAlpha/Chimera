"""Pinned fluid database -> admitted assertions -> graph scene -> native surface packet.
Python is acquisition/setup only. The C++ engine owns all runtime mechanics.
"""
from pathlib import Path
import json, math, shutil, argparse
from .common import canonical, digest, sha, require, loads
from .pipeline import ingest, verify
from .graph import graph_from, propose
from tools.creature_graph.store import CreatureGraph
ROOT=Path(__file__).resolve().parents[2]
DATA=Path(__file__).parent/'data/coolprop'

def frame3(anchors):
    require(len(anchors)==3 and all(len(p)==3 for p in anchors),'three_anchors_required')
    require(all(type(x) in (int,float) and math.isfinite(x) for p in anchors for x in p),'nonfinite_anchor')
    a,b,c=anchors
    def sub(x,y): return [u-v for u,v in zip(x,y)]
    def dot(x,y): return sum(u*v for u,v in zip(x,y))
    u,v=sub(b,a),sub(c,a)
    length=math.sqrt(dot(u,u)); require(length>0 and math.isfinite(length),'coincident_anchors')
    u=[x/length for x in u]; projection=dot(v,u)
    v=[y-projection*x for x,y in zip(u,v)]
    width=math.sqrt(dot(v,v)); require(math.isfinite(width) and width>1e-10*length,'collinear_anchors')
    v=[x/width for x in v]
    n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
    return a,u,v,n,length,width

def compile_scene(graph, oid='surface.science_interface'):
    require(not graph.check(),'invalid_graph')
    obj=graph.get(oid); geo=obj['geometry']; phys=obj['physical']
    require(phys['law']=='constant_surface_tension','unsupported_surface_law')
    require(any(r['src']==oid and r['rel']=='uses_model' and r['dst']=='model.science_surface_area' for r in graph.relations),'missing_law_binding')
    a,u,v,n,L,W=frame3(obj['spatial']['anchors_m'])
    resolution=geo['subdivisions']
    require(type(resolution) is int and 4<=resolution<=48,'resolution_bounds')
    count=resolution+1; vertices=[]; triangles=[]; pins=[]; weights=[]
    radius=phys['probe_sigma_m']
    require(0<radius<min(L,W)/2,'probe_radius_bounds')
    for j in range(count):
        for i in range(count):
            s,t=i/resolution,j/resolution
            vertices.append([a[k]+s*L*u[k]+t*W*v[k] for k in range(3)])
            boundary=i in (0,resolution) or j in (0,resolution)
            if boundary:pins.append(j*count+i)
            weights.append(0 if boundary else math.exp(-(((s-.5)*L)**2+((t-.5)*W)**2)/(2*radius**2)))
            if i<resolution and j<resolution:
                q=j*count+i;triangles.extend([[q,q+1,q+count+1],[q,q+count+1,q+count]])
    total=sum(weights); weights=[w/total for w in weights]
    materials=[]
    for mid in phys['materials']:
        require(any(r['src']==oid and r['rel']=='uses_material' and r['dst']==mid for r in graph.relations),'missing_material_binding',mid)
        mat=graph.get(mid);rid=mat['physical']['surface_tension_record'];rec=graph.get(rid)['science_funnel']
        require(any(r['src']==mid and r['rel']=='derived_from' and r['dst']==rid for r in graph.relations),'missing_material_provenance')
        payload=rec['payload']
        require(payload['quantity']=='surface_tension' and payload['unit_si']=='N/m','surface_tension_units')
        require(payload['conditions']['temperature_K']==phys['temperature_K'],'surface_temperature_mismatch')
        require(payload['conditions']['interface']=='pure_liquid_vapor','surface_phase_mismatch')
        gamma=payload['value_si'];require(math.isfinite(gamma) and gamma>0,'surface_tension_positive')
        require(rec['id']==rid=='data.assertion.'+digest({k:v for k,v in rec.items() if k!='id'}),'assertion_identity_mismatch')
        require(mat['name']==payload['subject'],'fluid_identity_mismatch')
        materials.append({'name':mat['name'],'gamma_N_m':gamma,'record_id':rid,
          'source':{'revision':rec['source']['release'],'url':rec['source']['url'],'license':rec['source']['license'],
                    'artifact_sha256':rec['artifact']['sha256'],'correlation':payload['correlation']}})
    return {'schema':'chimera.surface.v1','object_id':oid,'graph_hash':graph.graph_hash(),
      'vertices_m':vertices,'triangles':triangles,'pinned':pins,'probe_weights':weights,'normal':n,
      'materials':materials,'temperature_K':phys['temperature_K'],'default_force_N':phys['default_force_N'],
      'max_force_N':phys['max_force_N'],'render_m_to_units':geo['render_m_to_units'],
      'render_translation_units':geo['render_translation_units'],'camera':geo['camera'],
      'scope':phys['scope'],'solver':'native Newton-CG quasistatic; iterations are not time'}

def build(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    receipt=json.loads((DATA/'download_receipt.json').read_text(encoding='utf-8-sig'))
    for art in receipt['artifacts']:
        require(sha((DATA/art['path']).read_bytes())==art['sha256'],'download_pin_drift',art['path'])
    graph=graph_from(ROOT/'tools/creature_graph/data/creature_graph.json')
    recipe=loads((DATA.parent/'surface_recipe.json').read_bytes())
    require(recipe['schema']=='chimera.surface.recipe.v1','surface_recipe_schema')
    receipts=[]
    for binding in recipe['sources']:
        fluid=binding['fluid']
        folder=output/'sources'/fluid;folder.mkdir(parents=True,exist_ok=True)
        artifact=next(a for a in receipt['artifacts'] if a['path']==fluid+'.json')
        license_art=next(a for a in receipt['artifacts'] if a['path']=='LICENSE')
        for art in (artifact,license_art):shutil.copyfile(DATA/art['path'],folder/art['path'])
        manifest={'schema_version':'1.0.0','adapter':'coolprop_surface',
          'source':{'id':'coolprop.'+fluid.lower(),'release':receipt['revision'],'license':'MIT','url':artifact['url']},
          'temperature_K':298.15,'artifacts':[dict(id=a['path'],role='data' if a==artifact else 'attachment',
            path=a['path'],sha256=a['sha256'],url=a['url']) for a in (artifact,license_art)]}
        (folder/'manifest.json').write_bytes(canonical(manifest))
        bundle=ingest(folder/'manifest.json',output/'bundles');data=verify(bundle)
        require(not data['quarantine'],'fluid_intake_quarantined')
        patch=propose(bundle,graph)
        # Isolated compiled-scene graph, not a write to a deployed controller/store.
        for o in patch['payload']['objects']:graph.add(o)
        for r in patch['payload']['relations']:graph.relate(**r)
        require(graph.graph_hash()==patch['metadata']['candidate_graph_hash'],'admission_mismatch')
        rid=next(r['id'] for r in data['records'] if r['record_type']=='measurement')
        mid=binding['material_id']
        graph.add({'id':mid,'kind':'material','name':fluid,'status':'specified','priority':'P0',
          'physical':{'surface_tension_record':rid,'applicability':'idealized pure liquid-vapor interface at 298.15 K'},
          'unknowns':['bulk_flow','biological_skin','optical_appearance']})
        graph.relate(mid,'derived_from',rid,'Selected immutable fluid correlation evaluation')
        receipts.append({'fluid':fluid,'bundle_id':data['receipt']['bundle_id'],'record':rid})
    for obj in recipe['objects']:graph.add(obj)
    for rel in recipe['relations']:graph.relate(**rel)
    require(not graph.check(),'compiled_graph_invalid',graph.check())
    graph.save(str(output/'surface_graph.json'))
    reloaded=graph_from(output/'surface_graph.json')
    scene=compile_scene(reloaded);scene['graph_file']=str(output/'surface_graph.json')
    scene['page_file']=str(Path(__file__).parent/'surface.html')
    (output/'surface_scene.json').write_bytes(canonical(scene))
    (output/'intake.json').write_bytes(canonical(receipts))
    return {'scene':str(output/'surface_scene.json'),'graph_hash':scene['graph_hash'],
      'vertices':len(scene['vertices_m']),'triangles':len(scene['triangles']),'materials':scene['materials']}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'.tmp/surface-feature')
    args=ap.parse_args();print(json.dumps(build(args.output),indent=2))
