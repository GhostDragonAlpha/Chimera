"""Compile the seven-coordinate native scene from the existing anatomy/Earth funnels.

Sibling of coupled_scene.py (which stays byte-untouched, frozen control S7 of
docs/packets/seven_coordinate_lift_v1.md): reads the admitted
model.dynamics.coupled_arm7 contract (chimera.coupled_scene7.v1), pins the
chain-depth coordinate order, per-drive stores and the hand recipe carried
from the qualified scene, and emits the same earth bundle shape with the
coupled_dynamics section bound to the seven-coordinate contract.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from .earth_scene import ROOT,compile_scene
from .common import canonical,digest,require
from .macaque_anatomy import parse_source,pose_frames
from .coupled_arm import Assembly
from tools.creature_graph.store import CreatureGraph
MODEL='model.dynamics.coupled_arm7'
# Pinned chain-depth order (packet THE REFERENCE section): sternum->humerus->
# ulna->radius->hand, qualified pair first, so stage comparisons are prefix
# expansions. The Python oracle's own order is sorted(); the permutation is
# pinned in the oracle fixture, one declared list.
COORDINATES=['shoulder_flexion','elbow_flexion','radial_pronation',
             'wrist_flexion','wrist_abduction','shoulder_adduction',
             'shoulder_rotation']

def _gap_scan(model,recipe,shift_y,steps=24,samples=512,seed=20260918):
    """Signed plane gap from source FK only: reset value and workspace minimum.

    The qualified compile proved plane reachability on the 24x24
    shoulder/elbow grid with the remaining coordinates at defaults (the
    qualified pair dominates the reach); that grid is carried verbatim and
    extended by a recorded-seed sample over ALL seven ranges, because added
    coordinates can only extend the reached workspace, never shrink it at
    fixed shoulder/elbow. Deterministic, no sweep: the seed is committed and
    the scan is a compile-time safety check, not a fixture."""
    point=np.array(recipe['hand_point_m']);radius=float(recipe['proxy_radius_m']);plane=float(recipe['contact_plane_height_m'])
    def gap(values):return (pose_frames(model,values)['hand']@np.r_[point,1.])[1]+shift_y+radius-plane
    coordinates=model['coordinates'];others=[c for c in COORDINATES if c not in ('shoulder_flexion','elbow_flexion')]
    reset=gap({})
    least=min(
        gap({'shoulder_flexion':float(s),'elbow_flexion':float(e)})
        for s in np.linspace(coordinates['shoulder_flexion']['range_rad'][0],coordinates['shoulder_flexion']['range_rad'][1],steps)
        for e in np.linspace(coordinates['elbow_flexion']['range_rad'][0],coordinates['elbow_flexion']['range_rad'][1],steps))
    rng=np.random.default_rng(seed)
    for _ in range(samples):
        values={c:float(coordinates[c]['range_rad'][0])+rng.uniform(.02,.98)*float(np.ptp(coordinates[c]['range_rad'])) for c in COORDINATES}
        least=min(least,gap(values))
    return reset,least

def compile_coupled7(graph,output):
    stored=graph.get(MODEL)['physical']['contract'];model=graph.get(stored['source_model_id'])['physical']['model']
    require(stored['schema']=='chimera.coupled_scene7.v1' and stored['coordinates']==COORDINATES,'coupled_scene7_contract')
    require(stored['tick_hz']==300 and stored['substeps']==4,'coupled_timestep_contract')
    require(model==parse_source()[0],'coupled_arm_source_model_drift')
    port=graph.get(stored['attachment_id'])['physical']
    require(port['source_body']=='ref.macaque_arm.body.hand' and port['local_point_m']==stored['hand_point_m'],'coupled_hand_recipe_drift')
    unlocked=sorted(k for k,v in model['coordinates'].items() if not v['locked'])
    require(sorted(stored['coordinates'])==unlocked,'coupled_scene7_coordinate_set','pinned order must cover exactly the unlocked source coordinates')
    defaults=stored['defaults']
    for c in COORDINATES:
        require(defaults.get(c+'_drive') is True,'coupled_scene7_drive_flag_missing',c)
        require(isinstance(defaults.get(c+'_target_deg'),(int,float)),'coupled_scene7_target_missing',c)
        require(isinstance(defaults.get(c+'_torque_limit_N_m'),(int,float)) and 0<=defaults[c+'_torque_limit_N_m']<=1.,'coupled_scene7_cap_invalid',c)
        target=defaults[c+'_target_deg']*np.pi/180
        require(model['coordinates'][c]['range_rad'][0]-1e-8<=target<=model['coordinates'][c]['range_rad'][1]+1e-8,'coupled_scene7_target_out_of_range',c)
    require(stored['battery_initial_J']==2.0,'coupled_scene7_store_contract','per-drive battery_initial_J pinned at the derived 2.0 J')
    plane=stored.get('contact_plane_height_m')
    require(isinstance(plane,(int,float)) and math.isfinite(plane),'coupled_contact_plane_invalid')
    require(isinstance(defaults.get('contact_enabled'),bool),'coupled_contact_flag_invalid')
    friction=defaults.get('contact_friction')
    require(isinstance(friction,(int,float)) and not isinstance(friction,bool) and 0<=friction<=1,'coupled_friction_flag_invalid')
    Assembly(model) # strict physical-inertia and kinematic intake checks
    scene=graph.get('model.environment.earth_patch')['physical']['contract']
    surface=graph.get(stored['contact_plane_id'])['physical']
    require(surface['height_world_up_m']==plane and surface['normal_world']==[0.,1.,0.],'coupled_contact_surface_drift')
    reset,least=_gap_scan(model,stored,float(scene['arm_translation_m'][1]))
    require(reset>1e-6,'coupled_contact_initial_penetration',reset)
    require(least<0,'coupled_contact_plane_unreachable',least)
    bundle=compile_scene(graph,output)
    bundle['coupled_dynamics']={'model_id':MODEL,'recipe':stored,'model':model}
    bundle['page_file']=str(ROOT/'tools/science_funnel/coupled_arm.html')
    bundle['scope']='Native source-derived SEVEN-coordinate dynamics (shoulder flexion/adduction/rotation, elbow flexion, radial pronation, wrist flexion/abduction), fixed mount, per-drive finite ideal actuator stores, per-coordinate source joint stops under a deterministic simultaneous-stop cascade, actual source geometry, and an optional frictionless-to-Coulomb hand contact plane on the full 7-row point Jacobian (off and frictionless by default; the plane toggle requires reset, mu is live). The qualified two-coordinate scene runs unchanged as the frozen bit-exact control. No grasping, free root, whole animal, muscles, tissue mechanics or GPU residency qualification.'
    bundle.pop('scene_sha256');bundle['scene_sha256']=digest(bundle)
    (Path(output)/'scene.json').write_bytes(canonical(bundle));return bundle

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.tmp/coupled-native7')
    a=p.parse_args()
    graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
    b=compile_coupled7(graph,a.output)
    print(json.dumps({'scene':str(a.output/'scene.json'),'scene_sha256':b['scene_sha256']}))
if __name__=='__main__':main()
