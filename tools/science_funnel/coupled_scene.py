"""Compile the admitted two-coordinate native scene from the existing anatomy/Earth funnels."""
import argparse,json,math
from pathlib import Path
import numpy as np
from .earth_scene import ROOT,compile_scene
from .common import Refusal,canonical,digest,require,sha
from .macaque_anatomy import parse_source,pose_frames
from .coupled_arm import Assembly
from tools.creature_graph.store import CreatureGraph
MODEL='model.dynamics.coupled_arm'
# Terrain-derived contact plane (work.environment.terrain wiring_20260918): an
# OPT-IN recipe key, never a default. The committed recipe carries no source
# key, so the authored contact_plane_height_m=0.35 path is the qualified
# default world and stays byte-identical. terrain.py is deliberately not
# edited here: the terrain receipt pins its sha256.
TERRAIN_RECEIPT_DIR=ROOT/'tools/science_funnel/validation/terrain_20260917'
TERRAIN_PLANE_SOURCES={'terrain_cayo_20260917':{
 'patch':'cayo_santiago_patch','field':'h_ellipsoidal_m',
 'receipt_metric':'cayo_patch','receipt_metric_field':'h_ellipsoidal_m',
 'choice':'the terrain receipt scope reduces the Cayo Santiago patch centre and names '
          'Luquillo a coastal-plain land control and El Yunque a gate refusal; the coupled '
          'scene is the Cayo Santiago macaque reference, so the patch centre supplies the plane'}}

def terrain_plane_height(source_id):
    """Resolve an admitted contact_plane_height_source to the PINNED reduction
    value. Pin, not recompute: the reduction is qualified and deterministically
    replayed by tests.test_terrain against the pinned DEM+EGM08 grids; running
    terrain.reduce_terrain at compile would add a second producer that can drift
    from the receipted number and a ~250 MB two-grid decode per launch for zero
    added verification. Here the pin is verified instead (reduction_result.json
    must hash to the receipt-pinned sha256 and agree with the receipt metric)."""
    spec=TERRAIN_PLANE_SOURCES.get(source_id)
    if spec is None:
        raise Refusal('coupled_contact_plane_source_unknown',
                      f'{source_id!r}; admitted: {sorted(TERRAIN_PLANE_SOURCES)}')
    result_path=TERRAIN_RECEIPT_DIR/'reduction_result.json'
    require(result_path.is_file(),'terrain_reduction_result_missing',str(result_path))
    raw=result_path.read_bytes()
    receipt=json.loads((TERRAIN_RECEIPT_DIR/'receipt.json').read_text(encoding='utf-8'))
    pinned=receipt.get('artifacts',{}).get('reduction_result.json')
    require(isinstance(pinned,str) and sha(raw)==pinned,
            'terrain_reduction_result_pin_drift',f'{result_path} vs {pinned}')
    result=json.loads(raw)
    require(spec['patch'] in result,'terrain_reduction_patch_missing',spec['patch'])
    value=result[spec['patch']].get(spec['field'])
    require(isinstance(value,(int,float)) and not isinstance(value,bool)
            and math.isfinite(value),'terrain_reduction_value_invalid',str(value))
    metric=receipt.get('metrics',{}).get(spec['receipt_metric'],{}).get(spec['receipt_metric_field'])
    require(metric==value,'terrain_receipt_result_disagree',f'{metric} != {value}')
    return float(value),spec,receipt

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
    stored=graph.get(MODEL)['physical']['contract'];model=graph.get(stored['source_model_id'])['physical']['model']
    require(stored['schema']=='chimera.coupled_scene.v1' and stored['coordinates']==['shoulder_flexion','elbow_flexion'],'coupled_scene_contract')
    require(stored['tick_hz']==300 and stored['substeps']==4,'coupled_timestep_contract')
    require(model==parse_source()[0],'coupled_arm_source_model_drift')
    port=graph.get(stored['attachment_id'])['physical']
    require(port['source_body']=='ref.macaque_arm.body.hand' and port['local_point_m']==stored['hand_point_m'],'coupled_hand_recipe_drift')
    # Opt-in terrain plane: the stored contract is NEVER mutated; an opted-in
    # compile works on a copy whose effective plane is the pinned reduction.
    source_key=stored.get('contact_plane_height_source')
    recipe=stored;terrain=None
    if source_key is not None:
        require(isinstance(source_key,str),'coupled_contact_plane_source_invalid',str(source_key))
        value,spec,receipt=terrain_plane_height(source_key)
        recipe=dict(stored)
        recipe['contact_plane_height_m']=value
        terrain={'source':source_key,'patch':spec['patch'],'field':spec['field'],
                 'height_world_up_m':value,
                 'reduction_result_sha256':receipt['artifacts']['reduction_result.json'],
                 'receipt':'tools/science_funnel/validation/terrain_20260917/receipt.json',
                 'frame':'local_EUS world Up; the scene origin sits on the WGS84 ellipsoid '
                         '(earth altitude_m=0), so the plane height is h_ellipsoidal_m',
                 'choice':spec['choice'],
                 'pin_mode':'pinned recorded reduction result, hash-verified at compile; '
                            'terrain.reduce_terrain is not re-run here (see '
                            'work.environment.terrain wiring_20260918)'}
    plane=recipe.get('contact_plane_height_m')
    require(isinstance(plane,(int,float)) and math.isfinite(plane),'coupled_contact_plane_invalid')
    require(isinstance(stored['defaults'].get('contact_enabled'),bool),'coupled_contact_flag_invalid')
    friction=stored['defaults'].get('contact_friction')
    require(isinstance(friction,(int,float)) and not isinstance(friction,bool) and 0<=friction<=1,'coupled_friction_flag_invalid')
    Assembly(model) # strict physical-inertia and kinematic intake checks
    scene=graph.get('model.environment.earth_patch')['physical']['contract']
    surface=graph.get(recipe['contact_plane_id'])['physical']
    require(surface['height_world_up_m']==plane and surface['normal_world']==[0.,1.,0.],'coupled_contact_surface_drift')
    reset,least=_gap_scan(model,recipe,float(scene['arm_translation_m'][1]))
    require(reset>1e-6,'coupled_contact_initial_penetration',reset)
    if terrain is None:
        require(least<0,'coupled_contact_plane_unreachable',least)
    else:
        # The real ground at the reduction centre sits ~42.8 m below the
        # ellipsoidal mount origin, so the mounted arm records the terrain plane
        # as unreachable instead of asserting the authored pressing-workload
        # reachability law. Measured, never hidden; no initial penetration.
        terrain['plane_reachable']=bool(least<0)
        terrain['gap_scan_m']={'reset_gap_m':reset,'least_gap_m':least,
            'reading':'the terrain plane is recorded unreachable for the mounted arm at '
                      'arm scale; the qualified pressing workload remains the authored plane'}
    bundle=compile_scene(graph,output)
    bundle['coupled_dynamics']={'model_id':MODEL,'recipe':recipe,'model':model}
    if terrain is not None:
        bundle['coupled_dynamics']['contact_plane_terrain_provenance']=terrain
    bundle['page_file']=str(ROOT/'tools/science_funnel/coupled_arm.html')
    bundle['scope']='Native source-derived shoulder/elbow dynamics, fixed mount, finite ideal actuator work, source joint stops, an optional frictionless-to-Coulomb hand contact plane (off and frictionless by default; the plane toggle requires reset, mu is live) and authored friction heat accounts. No grasping, free root, whole animal, muscles, tissue mechanics or GPU residency qualification.'
    bundle['sources'] += [{'title':'Pinned macaque anatomy and effective segment inertia','url':'https://github.com/limblab/monkeyArmModel/tree/4fb7dddeec06a0df9525c18f37234a824cb1b5b1'}]
    bundle.pop('scene_sha256');bundle['scene_sha256']=digest(bundle)
    (Path(output)/'scene.json').write_bytes(canonical(bundle));return bundle

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.tmp/coupled-native')
    p.add_argument('--contact-plane-height-source',default=None,dest='contact_plane_height_source',
                   help='opt-in: derive the hand contact plane from an admitted terrain source '
                        '(terrain_cayo_20260917). Injects the recipe key + coherent surface '
                        'entity into the in-memory graph only; the committed default recipe '
                        'and the qualified default world stay untouched.')
    a=p.parse_args()
    graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
    if a.contact_plane_height_source is not None:
        value,spec,receipt=terrain_plane_height(a.contact_plane_height_source) # refuses unknown before any mutation
        contract=graph.get(MODEL)['physical']['contract']
        require('contact_plane_height_source' not in contract,'coupled_contact_plane_source_conflict',
                'the stored recipe already carries a source key; opt in through the graph, not the CLI')
        contract['contact_plane_height_source']=a.contact_plane_height_source
        graph.get(contract['contact_plane_id'])['physical']['height_world_up_m']=value
    b=compile_coupled(graph,a.output)
    print(json.dumps({'scene':str(a.output/'scene.json'),'scene_sha256':b['scene_sha256']}))
if __name__=='__main__':main()
