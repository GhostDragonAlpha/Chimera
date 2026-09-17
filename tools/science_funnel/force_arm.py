"""Reduce pinned anatomical segment inertia to one physical elbow coordinate."""
from pathlib import Path
import argparse,json
import numpy as np
from .common import canonical,digest,require
from .earth_scene import compile_scene,ROOT
from .macaque_anatomy import parse_source,pose_frames,rotation
from tools.creature_graph.store import CreatureGraph
MODEL='model.dynamics.macaque_elbow'

def reduce_hinge(model,joints,mesh,arm,shift,rest_offset):
    coordinate='elbow_flexion';joint=next(j for j in joints if j['name']==coordinate)
    pivot=np.asarray(joint['pivot']);axis=np.asarray(joint['axis']);frames=pose_frames(model)
    body={b['name']:b for b in model['bodies']};roots=[b['name'] for b in model['bodies'] if b['joint'] and any(a['coordinate']==coordinate for a in b['joint']['axes'])]
    require(len(roots)==1,'hinge_coordinate_root');moving=set(roots)
    while True:
        more={b['name'] for b in model['bodies'] if b['joint'] and b['joint']['parent'] in moving}
        if more<=moving:break
        moving|=more
    inertia=np.zeros((3,3));first=np.zeros(3);mass=0.;parts=[]
    for name in sorted(moving):
        b=body[name];m=b['mass_kg'];xx,yy,zz,xy,xz,yz=b['inertia_kg_m2'];Ic=np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]])
        eigen=np.linalg.eigvalsh(Ic);require(eigen[0]>=-1e-14 and eigen[-1]<=sum(eigen[:-1])+1e-14,'nonphysical_segment_inertia',name)
        require(m>0 or not np.any(Ic),'massless_segment_with_inertia',name)
        f=frames[name];r=(f@np.r_[b['mass_center_m'],1])[:3]-pivot
        I=f[:3,:3]@Ic@f[:3,:3].T+m*(np.dot(r,r)*np.eye(3)-np.outer(r,r))
        inertia+=I;first+=m*r;mass+=m
        parts.append({'body_id':'ref.macaque_arm.body.'+name,'mass_kg':m,'com_from_hinge_m':r.tolist(),'inertia_about_hinge_kg_m2':I.tolist()})
    h=arm['hand_vertex_start'];n=arm['hand_vertex_count'];hand=mesh[h:h+n,:3].astype(float).mean(axis=0)+np.asarray(rest_offset)
    scalar=float(axis@inertia@axis);require(scalar>0 and mass>0,'empty_hinge_mass')
    limits=np.deg2rad(joint['limits_deg']);lever=hand-pivot
    # This first support uses a unique height-to-angle mapping. Refuse other axes/ranges.
    for q in np.linspace(*limits,257):require(np.cross(axis,rotation(axis,q)@lever)[1]>.01,'nonmonotone_hand_support')
    return {'axis':axis.tolist(),'pivot_m':(pivot+shift).tolist(),'mass_kg':mass,'first_moment_kg_m':first.tolist(),'inertia_tensor_kg_m2':inertia.tolist(),'inertia_kg_m2':scalar,'hand_offset_m':lever.tolist(),'rest_rad':model['coordinates'][coordinate]['default_rad'],'limits_rad':limits.tolist(),'moving_bodies':parts}

def compile_force_arm(graph,output):
    output=Path(output).resolve();recipe=graph.get(MODEL)['physical']['contract'];model=graph.get(recipe['source_model_id'])['physical']['model']
    require(model==parse_source()[0],'force_arm_source_model_drift')
    require(recipe['schema']=='chimera.force_arm.v1' and recipe['coordinate']=='elbow_flexion','unsupported_force_arm_coordinate')
    port=graph.get(recipe['attachment_id']);support=graph.get(recipe['support_id'])
    require(port['physical']['rest_offset_m']==recipe['proxy_rest_offset_m'] and port['physical']['source_body']=='ref.macaque_arm.body.hand' and support['physical']['support_angle_deg']==recipe['support_angle_deg'],'force_arm_boundary_recipe_drift')
    b=compile_scene(graph,output);a=json.loads((output/'arm/scene.json').read_text(encoding='utf-8'));raw=(output/'arm/mesh.bin').read_bytes();nv=int.from_bytes(raw[:4],'little');mesh=np.frombuffer(raw,dtype='<f4',offset=24,count=nv*9).reshape(-1,9)
    p=reduce_hinge(model,a['joints'],mesh,b['arm'],np.array(b['scene']['arm_translation_m']),recipe['proxy_rest_offset_m'])
    b['arm_dynamics']={'schema':'chimera.force_arm.v1','model_id':MODEL,'recipe':recipe,'parameters':p};b['page_file']=str(ROOT/'tools/science_funnel/arm_load.html')
    b['scope']='Source-derived effective segment mass/inertia, one dynamic elbow and fixed shoulder/other coordinates. Authored finite-work drive and unilateral hand proxy support. Native CPU reference, not biological muscles, full animal or GPU-resident dynamics.'
    b['sources'] += [{'title':'Macaque anatomical source (pinned revision)','url':'https://github.com/limblab/monkeyArmModel/tree/4fb7dddeec06a0df9525c18f37234a824cb1b5b1'},{'title':'OpenSim body inertia definition','url':'https://opensim-org.github.io/opensim-moco-site/docs/1.3.0/html_user/classOpenSim_1_1Body.html'}]
    b.pop('scene_sha256');b['scene_sha256']=digest(b);(output/'scene.json').write_bytes(canonical(b));return b

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.tmp/force-arm');a=p.parse_args();g=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'));b=compile_force_arm(g,a.output);print(json.dumps({'scene':str(a.output/'scene.json'),'mass_kg':b['arm_dynamics']['parameters']['mass_kg'],'inertia_kg_m2':b['arm_dynamics']['parameters']['inertia_kg_m2'],'hash':b['scene_sha256']}))
if __name__=='__main__':main()
