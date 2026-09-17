"""Compile the admitted two-coordinate native scene from the existing anatomy/Earth funnels."""
import argparse,json
from pathlib import Path
from .earth_scene import ROOT,compile_scene
from .common import canonical,digest,require
from .macaque_anatomy import parse_source
from .coupled_arm import Assembly
from tools.creature_graph.store import CreatureGraph
MODEL='model.dynamics.coupled_arm'

def compile_coupled(graph,output):
    recipe=graph.get(MODEL)['physical']['contract'];model=graph.get(recipe['source_model_id'])['physical']['model']
    require(recipe['schema']=='chimera.coupled_scene.v1' and recipe['coordinates']==['shoulder_flexion','elbow_flexion'],'coupled_scene_contract')
    require(recipe['tick_hz']==300 and recipe['substeps']==4,'coupled_timestep_contract')
    require(model==parse_source()[0],'coupled_arm_source_model_drift')
    port=graph.get(recipe['attachment_id'])['physical']
    require(port['source_body']=='ref.macaque_arm.body.hand' and port['local_point_m']==recipe['hand_point_m'],'coupled_hand_recipe_drift')
    Assembly(model) # strict physical-inertia and kinematic intake checks
    bundle=compile_scene(graph,output)
    bundle['coupled_dynamics']={'model_id':MODEL,'recipe':recipe,'model':model}
    bundle['page_file']=str(ROOT/'tools/science_funnel/coupled_arm.html')
    bundle['scope']='Native source-derived shoulder/elbow dynamics, fixed mount, finite ideal actuator work and joint stops. Hand force marker has no environment collision. No whole animal, muscles, tissue mechanics or GPU residency qualification.'
    bundle['sources'] += [{'title':'Pinned macaque anatomy and effective segment inertia','url':'https://github.com/limblab/monkeyArmModel/tree/4fb7dddeec06a0df9525c18f37234a824cb1b5b1'}]
    bundle.pop('scene_sha256');bundle['scene_sha256']=digest(bundle)
    (Path(output)/'scene.json').write_bytes(canonical(bundle));return bundle

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.tmp/coupled-native');a=p.parse_args()
    graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'));b=compile_coupled(graph,a.output)
    print(json.dumps({'scene':str(a.output/'scene.json'),'scene_sha256':b['scene_sha256']}))
if __name__=='__main__':main()
