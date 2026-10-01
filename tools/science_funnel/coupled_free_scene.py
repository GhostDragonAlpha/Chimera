"""Compile the free-root eight-coordinate native scene (docs/packets/free_root_balance_v1.md).

Sibling of coupled_scene.py, which stays byte-untouched (packet AMENDMENT E4:
the qualified receipts pin its sha256). This compiler emits the
`coupled_free_dynamics` bundle kind: the free 8-DOF recipe + model, and the
FROZEN qualified payload the runtime constructs verbatim when
free_root_enabled is false (D10 mount-locked bit-exact control).
"""
import argparse,copy,json,math
from pathlib import Path
import numpy as np
from .earth_scene import ROOT,compile_scene
from .common import canonical,digest,require
from .macaque_anatomy import parse_source,pose_frames
from .coupled_arm import Assembly
from tools.creature_graph.store import CreatureGraph
MODEL='model.dynamics.coupled_arm'
FREE_MODEL='model.dynamics.coupled_arm_free'
BASE_COORDINATES=[('base_rot_x',math.pi),('base_rot_y',math.pi),('base_rot_z',math.pi),('base_trans_x',1.0),('base_trans_y',1.0),('base_trans_z',1.0)]
COORDINATE_ORDER=['base_rot_x','base_rot_y','base_rot_z','base_trans_x','base_trans_y','base_trans_z','shoulder_flexion','elbow_flexion']
K_TOUCH=1e-5

def build_free_model(model,contract):
    """Source model with the sternum weld re-authored as the six-axis base joint."""
    free=copy.deepcopy(model)
    require(free['bodies'][1]['name']=='sternum','free_sternum_missing')
    sternum=[b for b in free['bodies'] if b['name']=='sternum'][0]
    require(sternum['joint']['type']=='WeldJoint' and sternum['joint']['parent']=='ground'
            and sternum['joint']['parent_location_m']==[0.,0.,0.] and sternum['joint']['child_location_m']==[0.,0.,0.]
            and sternum['joint']['parent_orientation_rad']==[0.,0.,0.] and sternum['joint']['child_orientation_rad']==[0.,0.,0.],
            'free_sternum_weld_identity')
    for name,rng in BASE_COORDINATES:
        require(name not in free['coordinates'],'free_base_coordinate_conflict',name)
        free['coordinates'][name]={'default_rad':0.0,'range_rad':[-rng,rng],'locked':False}
    base=contract['base_scaffold']['defaults_rad_m']
    for i,name in enumerate(['base_trans_x','base_trans_y','base_trans_z']):
        free['coordinates'][name]['default_rad']=float(base[3+i])
    axes=[]
    for k,coord in enumerate(['base_rot_x','base_rot_y','base_rot_z']):
        axis=[1.0 if k==0 else 0.0,1.0 if k==1 else 0.0,1.0 if k==2 else 0.0]
        axes.append({'name':f'rotation{k+1}','axis':axis,'coordinate':coord,'function':{'type':'LinearFunction','coefficients':[1.0,0.0]}})
    for k,coord in enumerate(['base_trans_x','base_trans_y','base_trans_z']):
        axis=[1.0 if k==0 else 0.0,1.0 if k==1 else 0.0,1.0 if k==2 else 0.0]
        axes.append({'name':f'translation{k+1}','axis':axis,'coordinate':coord,'function':{'type':'LinearFunction','coefficients':[1.0,0.0]}})
    sternum['joint']={'name':'ground_sternum','type':'CustomJoint','parent':'ground',
                      'parent_location_m':[0.,0.,0.],'parent_orientation_rad':[0.,0.,0.],
                      'child_location_m':[0.,0.,0.],'child_orientation_rad':[0.,0.,0.],'axes':axes}
    require([a['name'] for a in sternum['joint']['axes']]==['rotation1','rotation2','rotation3','translation1','translation2','translation3'],'free_transform_axis_order')
    # Trunk inertia authoring (packet AMENDMENT 20260918 E5, model record
    # revision 3): the source sternum is a POINT MASS (6.6 kg, zero inertia
    # tensor) -- the mounted world never felt it, but the free trunk-yaw mode
    # (base yaw + shoulder counter-swing keeping the arm fixed) measures
    # 1.56e-7 kg m^2 of inertia, and explicit RK4 at h = 1/1200 s diverges on
    # such a near-null mode. The free sternum therefore authors a derived
    # isotropic 0.01 kg m^2 (gyration radius 3.9 cm). The qualified payload
    # keeps the source bytes verbatim; the joint block stays bitwise because a
    # body's inertia enters the mass matrix only through its own jw rows and
    # the sternum's joint-slot Jacobian columns are exactly zero.
    require(sternum['inertia_kg_m2']==[0.,0.,0.,0.,0.,0.] and sternum['mass_kg']>0,'free_sternum_point_mass_identity')
    sternum['inertia_kg_m2']=[0.01,0.01,0.01,0.,0.,0.]
    # The free scene moves ONLY the base plus the qualified pair; the five
    # remaining source coordinates are LOCKED at their source defaults. The
    # native Model folds unselected coordinates to constants either way, so
    # this changes no arithmetic -- it documents the selection and keeps the
    # Python Assembly oracle (which uses every unlocked coordinate) exactly on
    # the native's 8-coordinate system.
    for name,c in free['coordinates'].items():
        if name not in COORDINATE_ORDER:
            c['locked']=True
    return free

def seating_scan(free_model,recipe,shift_y):
    """Compile-time seat proof (D4/D7): all support points in the touching band
    at the seated reset, plane reachable in the joint workspace, CoM strictly
    inside the support hull."""
    plane=float(recipe['contact_plane_height_m'])-shift_y
    pts=[(p['body'],[float(v) for v in p['point_m']],float(p['radius_m'])) for p in recipe['contact_points']]
    def gaps(values=None):
        frames=pose_frames(free_model,values or {})
        return [(frames[b]@np.r_[np.asarray(p),1.]).tolist()[1]+r-plane for b,p,r in pts]
    reset=gaps()
    for g in reset:require(0<g<K_TOUCH,'free_seated_reset_gap_invalid',g)
    coordinates=free_model['coordinates']
    least=min(min(gaps({'shoulder_flexion':float(s),'elbow_flexion':float(e)}))
              for s in np.linspace(coordinates['shoulder_flexion']['range_rad'][0],coordinates['shoulder_flexion']['range_rad'][1],24)
              for e in np.linspace(coordinates['elbow_flexion']['range_rad'][0],coordinates['elbow_flexion']['range_rad'][1],24))
    require(least<0,'free_contact_plane_unreachable',least)
    asm=Assembly(free_model,gravity=[0.,-9.80665,0.])
    com=np.zeros(3);mtot=0.
    for body in free_model['bodies']:
        m=float(body['mass_kg']);p,_=asm.point(body['name'],body['mass_center_m'])
        com+=m*np.asarray(p);mtot+=m
    com/=mtot
    frames=pose_frames(free_model,{})
    hull=[]
    for b,p,_ in pts:hull.append(((frames[b]@np.r_[np.asarray(p),1.])[0],(frames[b]@np.r_[np.asarray(p),1.])[2]))
    c=(float(com[0]),float(com[2]))
    det=(hull[1][0]-hull[0][0])*(hull[2][1]-hull[0][1])-(hull[2][0]-hull[0][0])*(hull[1][1]-hull[0][1])
    require(abs(det)>1e-15,'free_support_hull_degenerate',det)
    w0=((hull[1][0]-c[0])*(hull[2][1]-c[1])-(hull[2][0]-c[0])*(hull[1][1]-c[1]))/det
    w1=((hull[2][0]-c[0])*(hull[0][1]-c[1])-(hull[0][0]-c[0])*(hull[2][1]-c[1]))/det
    w2=1.-w0-w1
    require(w0>0 and w1>0 and w2>0,'free_com_outside_support_hull',[w0,w1,w2])
    return {'reset_gaps_m':reset,'com_projection_model_m':[c[0],c[1]],'barycentric_weights':[w0,w1,w2],
            'assembly_mass_kg':mtot,'weight_N':mtot*9.80665,'least_gap_m':least}

def compile_free(graph,output):
    free_record=graph.get(FREE_MODEL)['physical']['contract']
    stored=graph.get(MODEL)['physical']['contract']
    model=graph.get(stored['source_model_id'])['physical']['model']
    require(stored['schema']=='chimera.coupled_scene.v1' and stored['coordinates']==['shoulder_flexion','elbow_flexion'],'coupled_scene_contract')
    require(model==parse_source()[0],'coupled_arm_source_model_drift')
    require(free_record['schema']=='chimera.coupled_free_scene.v1' and free_record['derived_from_contract']==MODEL,'free_scene_contract')
    require(free_record['coordinates']==COORDINATE_ORDER,'free_coordinate_order')
    scene=graph.get('model.environment.earth_patch')['physical']['contract']
    shift=[float(v) for v in scene['arm_translation_m']]
    surface=graph.get(free_record['contact_plane_id'])['physical']
    require(surface['height_world_up_m']==free_record['contact_plane_height_m'] and surface['normal_world']==[0.,1.,0.],'free_contact_surface_drift')
    Assembly(model) # strict physical-inertia intake on the qualified source
    free_model=build_free_model(model,free_record)
    Assembly(free_model) # strict physical-inertia and kinematic checks on the derived assembly
    defaults=dict(free_record['defaults'])
    require(defaults.get('free_root_enabled') is True,'free_root_flag_required')
    base_defaults=[float(v) for v in free_record['base_scaffold']['defaults_rad_m']]
    defaults.update({'base_rot_x_deg':base_defaults[0]*180/math.pi,'base_rot_y_deg':base_defaults[1]*180/math.pi,'base_rot_z_deg':base_defaults[2]*180/math.pi,
                     'base_trans_x_m':base_defaults[3],'base_trans_y_m':base_defaults[4],'base_trans_z_m':base_defaults[5],
                     'base_rot_x_speed_deg_s':0.,'base_rot_y_speed_deg_s':0.,'base_rot_z_speed_deg_s':0.,
                     'base_trans_x_speed_m_s':0.,'base_trans_y_speed_m_s':0.,'base_trans_z_speed_m_s':0.})
    recipe={'schema':'chimera.coupled_free_scene.v1','source_model_id':free_record['source_model_id'],
            'derived_from_contract':MODEL,'coordinates':COORDINATE_ORDER,
            'hand_body':free_record['hand_body'],'hand_point_m':free_record['hand_point_m'],
            'attachment_id':free_record['attachment_id'],'proxy_radius_m':free_record['proxy_radius_m'],
            'contact_points':free_record['contact_points'],
            'contact_plane_height_m':free_record['contact_plane_height_m'],
            'tick_hz':free_record['tick_hz'],'substeps':free_record['substeps'],
            'servo_frequency_Hz':free_record['servo_frequency_Hz'],'servo_damping_ratio':free_record['servo_damping_ratio'],
            'passive_decay_rate_s':free_record['passive_decay_rate_s'],'battery_initial_J':free_record['battery_initial_J'],
            'defaults':defaults,'assumptions':free_record['assumptions']}
    measured=seating_scan(free_model,recipe,shift[1])
    recorded=free_record['seating_scan']
    require(abs(measured['com_projection_model_m'][0]-recorded['com_projection_model_m'][0])<1e-9
            and abs(measured['com_projection_model_m'][1]-recorded['com_projection_model_m'][1])<1e-9,'free_seating_scan_com_drift')
    require(abs(measured['assembly_mass_kg']-recorded['assembly_mass_kg'])<1e-12,'free_seating_scan_mass_drift')
    bundle=compile_scene(graph,output)
    # The frozen qualified payload (D10): constructed VERBATIM by the runtime
    # when free_root_enabled is false; the qualified recipe is never mutated.
    qualified={'model_id':MODEL,'recipe':stored,'model':model}
    bundle['coupled_free_dynamics']={'free_root_enabled':bool(defaults['free_root_enabled']),
                                     'recipe':recipe,'model':free_model,'qualified':qualified,
                                     'seating_scan_measured':measured}
    bundle['page_file']=str(ROOT/'tools/science_funnel/coupled_arm.html')
    bundle['scope']='Free-root eight-coordinate source-derived arm dynamics (floating sternum base + shoulder/elbow), rigid plane contact as a LIST of 3D point-on-plane rows with per-point radii, discrete-cone Coulomb friction, mass-metric active-set projection and the qualified energy ledger; the mount-locked mode (free_root_enabled=false) constructs the qualified two-coordinate class verbatim as the frozen bit-exact control. No walking or balance controller, no muscles, no grasp, no compliant or distributed contact, no terrain beyond the authored plane, no GPU residency qualification.'
    bundle['sources']=bundle['sources']+[{'title':'Pinned macaque anatomy and effective segment inertia','url':'https://github.com/limblab/monkeyArmModel/tree/4fb7dddeec06a0df9525c18f37234a824cb1b5b1'}]
    bundle.pop('scene_sha256');bundle['scene_sha256']=digest(bundle)
    (Path(output)/'scene.json').write_bytes(canonical(bundle));return bundle

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.tmp/coupled-free')
    a=p.parse_args()
    graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
    require(FREE_MODEL in graph.objects,'free_model_record_missing',FREE_MODEL)
    b=compile_free(graph,a.output)
    print(json.dumps({'scene':str(a.output/'scene.json'),'scene_sha256':b['scene_sha256'],
                      'free_root_enabled':b['coupled_free_dynamics']['free_root_enabled'],
                      'seating_scan':b['coupled_free_dynamics']['seating_scan_measured']}))
if __name__=='__main__':main()
