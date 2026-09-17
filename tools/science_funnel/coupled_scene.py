"""Compile the admitted two-coordinate native scene from the existing anatomy/Earth funnels."""
import argparse,json,math
from pathlib import Path
import numpy as np
from .earth_scene import ROOT,compile_scene
from .common import canonical,digest,require
from .macaque_anatomy import parse_source,pose_frames
from .coupled_arm import Assembly
from tools.creature_graph.store import CreatureGraph
MODEL='model.dynamics.coupled_arm'

def _gap_scan(model,recipe,shift_y,steps=24):
    """Signed plane gap from source FK only: reset value and workspace minimum."""
    point=np.array(recipe['hand_point_m']);radius=float(recipe['proxy_radius_m']);plane=float(recipe['contact_plane_height_m'])
    def gap(values):return (pose_frames(model,values)['hand']@np.r_[point,1.])[1]+shift_y+radius-plane
    reset=gap({})
    coordinates=model['coordinates'];least=min(
        gap({'shoulder_flexion':float(s),'elbow_flexion':float(e)})
        for s in np.linspace(coordinates['shoulder_flexion']['range_rad'][0],coordinates['shoulder_flexion']['range_rad'][1],steps)
        for e in np.linspace(coordinates['elbow_flexion']['range_rad'][0],coordinates['elbow_flexion']['range_rad'][1],steps))
    return reset,least

def compile_coupled(graph,output):
    recipe=graph.get(MODEL)['physical']['contract'];model=graph.get(recipe['source_model_id'])['physical']['model']
    require(recipe['schema']=='chimera.coupled_scene.v1' and recipe['coordinates']==['shoulder_flexion','elbow_flexion'],'coupled_scene_contract')
    require(recipe['tick_hz']==300 and recipe['substeps']==4,'coupled_timestep_contract')
    require(model==parse_source()[0],'coupled_arm_source_model_drift')
    port=graph.get(recipe['attachment_id'])['physical']
    require(port['source_body']=='ref.macaque_arm.body.hand' and port['local_point_m']==recipe['hand_point_m'],'coupled_hand_recipe_drift')
    plane=recipe.get('contact_plane_height_m')
    require(isinstance(plane,(int,float)) and math.isfinite(plane),'coupled_contact_plane_invalid')
    require(isinstance(recipe['defaults'].get('contact_enabled'),bool),'coupled_contact_flag_invalid')
    Assembly(model) # strict physical-inertia and kinematic intake checks
    scene=graph.get('model.environment.earth_patch')['physical']['contract']
    surface=graph.get(recipe['contact_plane_id'])['physical']
    require(surface['height_world_up_m']==plane and surface['normal_world']==[0.,1.,0.],'coupled_contact_surface_drift')
    reset,least=_gap_scan(model,recipe,float(scene['arm_translation_m'][1]))
    require(reset>1e-6,'coupled_contact_initial_penetration',reset)
    require(least<0,'coupled_contact_plane_unreachable',least)
    bundle=compile_scene(graph,output)
    bundle['coupled_dynamics']={'model_id':MODEL,'recipe':recipe,'model':model}
    bundle['page_file']=str(ROOT/'tools/science_funnel/coupled_arm.html')
    bundle['scope']='Native source-derived shoulder/elbow dynamics, fixed mount, finite ideal actuator work, source joint stops and an optional frictionless rigid hand contact plane (off by default; the toggle requires reset). No friction, grasp, free root, whole animal, muscles, tissue mechanics or GPU residency qualification.'
    bundle['sources'] += [{'title':'Pinned macaque anatomy and effective segment inertia','url':'https://github.com/limblab/monkeyArmModel/tree/4fb7dddeec06a0df9525c18f37234a824cb1b5b1'}]
    bundle.pop('scene_sha256');bundle['scene_sha256']=digest(bundle)
    (Path(output)/'scene.json').write_bytes(canonical(bundle));return bundle

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.tmp/coupled-native');a=p.parse_args()
    graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'));b=compile_coupled(graph,a.output)
    print(json.dumps({'scene':str(a.output/'scene.json'),'scene_sha256':b['scene_sha256']}))
if __name__=='__main__':main()
