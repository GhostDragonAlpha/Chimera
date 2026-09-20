"""Compile the gait walker native scene (docs/research/20260918_gait_controller_derivation.md,
stages D-F implementation, record model.dynamics.gait_walker).

Sibling of coupled_free_scene.py (which stays byte-untouched). This compiler
emits the `gait_controller` bundle kind: the 14-coordinate walker recipe
(6-axis authored free base + hip/knee/ankle/MP per leg in the Oku sign
convention) and the walker model authored from the pinned Oku Table 1
segments. The qualified world's compilers are untouched: the
`gait_controller` key exists ONLY in this compiler's output (default off).

The seating scan is the compile-time proof that the standing reset puts all
six foot contact points at the authored +2e-6 m gap and the CoM strictly
inside the support hull (the free-root packet's D4/D7 pattern).
"""
import argparse,json,math,sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.science_funnel.common import canonical,digest
from tools.creature_graph.store import CreatureGraph

RECORD='model.dynamics.gait_walker'
DERIVED=ROOT/'tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json'
K_TOUCH=1e-5
SOLE_RADIUS=0.004
RESET_GAP=2e-6


def body(name,parent,mass,com,inertia,joint=None):
    return {'name':name,'mass_kg':mass,'mass_center_m':com,'inertia_kg_m2':inertia,
            'joint':joint}


def revolute(name,parent,parent_location,child_location,coordinate,axis=(0.,0.,1.)):
    return {'name':name,'type':'CustomJoint','parent':parent,
            'parent_location_m':[float(v) for v in parent_location],
            'parent_orientation_rad':[0.,0.,0.],
            'child_location_m':[float(v) for v in child_location],
            'child_orientation_rad':[0.,0.,0.],
            'axes':[{'name':'rotation1','axis':[float(v) for v in axis],'coordinate':coordinate,
                     'function':{'type':'LinearFunction','coefficients':[1.0,0.0]}}]}


def build_walker_model(record,derived):
    """The Oku Table 1 planar assembly: pelvis (HAT) on an authored 6-axis
    base joint, two identical hindlimb chains (thigh/shank/foot/toe). q=0 is
    the straight-leg standing pose; the +/-1 stem mapping is the DECLARED
    convention: every joint axis is world South {0,0,1} with slope +1, so
    positive q IS flexion/extension/dorsiflexion exactly as the tables."""
    seg=derived['body_model']['segments_Table1']
    def inert(i): return [float(i),float(i),float(i),0.,0.,0.]
    contract=record['physical']['contract']
    z=contract['leg_z_offset_m']
    base_axes=[]
    for k,coord in enumerate(['base_rot_x','base_rot_y','base_rot_z']):
        axis=[1.0 if k==0 else 0.0,1.0 if k==1 else 0.0,1.0 if k==2 else 0.0]
        base_axes.append({'name':f'rotation{k+1}','axis':axis,'coordinate':coord,
                          'function':{'type':'LinearFunction','coefficients':[1.0,0.0]}})
    for k,coord in enumerate(['base_trans_x','base_trans_y','base_trans_z']):
        axis=[1.0 if k==0 else 0.0,1.0 if k==1 else 0.0,1.0 if k==2 else 0.0]
        base_axes.append({'name':f'translation{k+1}','axis':axis,'coordinate':coord,
                          'function':{'type':'LinearFunction','coefficients':[1.0,0.0]}})
    base_joint={'name':'ground_pelvis','type':'CustomJoint','parent':'ground',
                'parent_location_m':[0.,0.,0.],'parent_orientation_rad':[0.,0.,0.],
                'child_location_m':[0.,0.,0.],'child_orientation_rad':[0.,0.,0.],
                'axes':base_axes}
    pelvis=body('pelvis',None,float(seg['HAT']['mass_kg']),
                [0.,float(seg['HAT']['com_frac']*seg['HAT']['length_m']),0.],
                inert(seg['HAT']['I_com']),base_joint)
    bodies=[{'name':'ground','mass_kg':0.0,'mass_center_m':[0.,0.,0.],
             'inertia_kg_m2':[0.,0.,0.,0.,0.,0.],'joint':None},pelvis]
    ranges=contract['joint_ranges_rad']
    for leg,side in (('left',1.0),('right',-1.0)):
        bodies.append(body(f'thigh_{leg}','pelvis',float(seg['thigh']['mass_kg']),
            [0.,-float(seg['thigh']['com_frac']*seg['thigh']['length_m']),0.],
            inert(seg['thigh']['I_com']),
            revolute(f'ground_thigh_{leg}','pelvis',[0.,0.,side*z],[0.,0.,0.],f'hip_flexion_{leg}')))
        bodies.append(body(f'shank_{leg}',f'thigh_{leg}',float(seg['shank']['mass_kg']),
            [0.,-float(seg['shank']['com_frac']*seg['shank']['length_m']),0.],
            inert(seg['shank']['I_com']),
            revolute(f'thigh_shank_{leg}',f'thigh_{leg}',[0.,-float(seg['thigh']['length_m']),0.],[0.,0.,0.],f'knee_extension_{leg}')))
        bodies.append(body(f'foot_{leg}',f'shank_{leg}',float(seg['foot']['mass_kg']),
            [float(seg['foot']['com_frac']*seg['foot']['length_m']),0.,0.],
            inert(seg['foot']['I_com']),
            revolute(f'shank_foot_{leg}',f'shank_{leg}',[0.,-float(seg['shank']['length_m']),0.],[0.,0.,0.],f'ankle_dorsiflexion_{leg}')))
        bodies.append(body(f'toe_{leg}',f'foot_{leg}',float(seg['phalanges']['mass_kg']),
            [float(seg['phalanges']['com_frac']*seg['phalanges']['length_m']),0.,0.],
            inert(seg['phalanges']['I_com']),
            revolute(f'foot_toe_{leg}',f'foot_{leg}',[float(seg['foot']['length_m']),0.,0.],[0.,0.,0.],f'MP_dorsiflexion_{leg}')))
    coordinates={}
    for c in contract['coordinates']:
        if c.startswith('base_rot'):
            coordinates[c]={'default_rad':0.0,'range_rad':[-math.pi,math.pi],'locked':False}
        elif c.startswith('base_trans'):
            coordinates[c]={'default_rad':0.0,'range_rad':[-1.0,1.0],'locked':False}
        else:
            stem=c.rsplit('_',1)[0]
            lo,hi=ranges[stem]
            coordinates[c]={'default_rad':0.0,'range_rad':[float(lo),float(hi)],'locked':False}
    # Standing reset height: ankle at sole radius above the plane model origin,
    # minus the authored +2e-6 seating lift (the free-root's D4 pattern).
    leg_drop=float(seg['thigh']['length_m'])+float(seg['shank']['length_m'])
    base_y=leg_drop+contract['seating_scan']['reset_gap_target_m']
    coordinates['base_trans_y']['default_rad']=base_y
    return {'schema':'chimera.anatomical_assembly.v1','coordinates':coordinates,'bodies':bodies}


def seating_scan(model,record):
    """Compile-time seat proof: all six foot points at the authored gap, CoM
    strictly inside the standing support hull."""
    contract=record['physical']['contract']
    plane=contract['contact_plane_height_m']
    from tools.science_funnel.coupled_arm import Assembly
    asm=Assembly(model,gravity=[0.,-9.80665,0.])
    com=np.zeros(3);mtot=0.
    for b in model['bodies']:
        m=float(b['mass_kg']);p,_=asm.point(b['name'],b['mass_center_m'])
        com+=m*np.asarray(p);mtot+=m
    com/=mtot
    pts=contract['contact_points']
    gaps=[]
    for p in pts:
        pos,_=asm.point(p['body'],p['point_m'])
        gaps.append(float(pos[1])+float(p['radius_m'])-plane)
    for g in gaps:require(0<g<K_TOUCH,'gait_seated_reset_gap_invalid',g)
    hull=[(float(asm.point(p['body'],p['point_m'])[0][0]),float(asm.point(p['body'],p['point_m'])[0][2])) for p in pts]
    c=(float(com[0]),float(com[2]))
    # Convex hull (monotone chain) then strict inside test.
    pts2=sorted(set(hull))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for p in pts2:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(pts2):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    hull2=lower[:-1]+upper[:-1]
    inside=all(cross(hull2[i],hull2[(i+1)%len(hull2)],c)>0 for i in range(len(hull2)))
    require(inside,'gait_com_outside_support_hull',c)
    return {'reset_gaps_m':gaps,'com_projection_model_m':[c[0],c[1]],'assembly_mass_kg':mtot,
            'weight_N':mtot*9.80665,'hull_vertices':hull2}


def require(cond,msg,*args):
    if not cond:raise SystemExit(f'REFUSAL: {msg} {list(args)}')


def compile_gait(graph,output):
    record=graph.get(RECORD)
    contract=record['physical']['contract']
    require(contract['schema']=='chimera.gait_scene.v1','gait_scene_contract')
    derived=json.loads(DERIVED.read_text(encoding='utf-8'))
    model=build_walker_model(record,derived)
    from tools.science_funnel.coupled_arm import Assembly
    Assembly(model)
    defaults={'power':True,'gait_enabled':True,'capture_enabled':True,'posture_drive':True,'push_N':0.0,'contact_enabled':True,
              'contact_friction':contract['contact_friction']}
    for d in contract['drives']:
        defaults[d['coordinate']+'_drive']=True
    measured=seating_scan(model,record)
    recorded=contract.get('seating_scan_measured')
    if recorded:
        require(abs(measured['assembly_mass_kg']-recorded['assembly_mass_kg'])<1e-9,'gait_seating_mass_drift')
        require(max(abs(a-b) for a,b in zip(measured['com_projection_model_m'],recorded['com_projection_model_m']))<1e-9,'gait_seating_com_drift')
    # THE SINGLE-SUPPORT ENTRY (the entry law, wave 4): the source model's
    # "enter at the TD state" is over-determined -- TD-left means
    # mid-stance-right, a DOUBLE-support instant, and the tables' closure
    # residual leaves the two stance contacts 2.96 mm apart; the
    # require(gap>0) reset then forces the loaded leg 3 mm into the air and
    # its drop delivers ~1 J into the hip/trunk (the measured tick-40
    # cascade). The lawful entry is the SINGLE-SUPPORT mid-stance instant:
    # the phase where the tables put the stance thigh exactly VERTICAL (the
    # mid-stance definition), the swing foot still clear. One load-bearing
    # contact seats; the swing leg lands through its own normal TD event.
    tables=contract['tables_rad']
    zeros=contract.get('zero_map_rad')
    require(zeros is not None,'gait_zero_map_missing','bank revision 2 with admit_gait_zeros_20260919.py')
    import math as _m
    seg=derived['body_model']['segments_Table1']
    _L1=float(seg['thigh']['length_m']);_L2=float(seg['shank']['length_m'])
    _XM=0.074;_XH=-0.012
    def _table(t,phi):
        x=phi*20.0;k=min(19,int(x));f=x-k;return t[k]*(1.0-f)+t[k+1]*f
    def _thigh_tilt(phi):  # composed stance-thigh tilt from vertical-down
        return zeros['hip']+_table(tables['hip'],phi)
    def _contact_xy(phi):
        th1=zeros['hip']+_table(tables['hip'],phi)
        th2=th1+zeros['knee']+_table(tables['knee'],phi)
        p=th2+zeros['ankle']+_table(tables['ankle'],phi)
        x=_L1*_m.sin(th1)+_L2*_m.sin(th2)+((_XH if p>0 else _XM)*_m.cos(p))
        y=-_L1*_m.cos(th1)-_L2*_m.cos(th2)+((_XH if p>0 else _XM)*_m.sin(p))
        return x,y
    _cd=1e-4
    def _contact_vy(phi):  # the composed contact's vertical speed rel. hip
        return (_contact_xy(phi+_cd)[1]-_contact_xy(phi-_cd)[1])/(2*_cd)/float(contract['cycle_duration_s'])
    # ENTRY LOAD-TRANSFER LAW (wave 6): the seated contact must not be
    # OPENING at entry -- the solver's plane-arming gate rejects a point
    # whose normal velocity exceeds ~4 mm/s upward, so an entry on the
    # rising limb of the closure residual's bob (measured +64 mm/s at the
    # bare vertical-thigh instant, phi=0.449) lifts the seated foot within
    # one tick: no force path, a bounce, and the wrong leg catches the body
    # (the [pt] trace, receipt_wave5). The entry is therefore the phase
    # nearest vertical thigh SUBJECT TO the composed contact settling
    # (vy <= 0). Measured convergence: this also lands on the most
    # statically-holdable phase in the window (phi~0.35: knee 4.34,
    # ankle 7.20 -- every demand inside the ORIGINAL caps; why the caps
    # amendment was not binding).
    e_best,e_err=None,1e9
    for i in range(180,501):  # phi in [0.09, 0.50] at 1e-3: the stance window before heel-off
        phi=i/1000.0
        err=abs(_thigh_tilt(phi))
        # the swing partner (phi+0.5) must be airborne: after its toe-off (0.68) before its TD (1.0)
        if 0.70<phi+0.5<0.99 and _contact_vy(phi)<=0.0 and err<e_err: e_best,e_err=phi,err
    entry_phase=float(e_best)
    require(entry_phase is not None and e_err<0.35,'gait_entry_phase_not_found',e_err)
    # WAVE 8 EXPERIMENT: the TD entry RETURNS -- the settle window absorbs the
    # TD bounce (the wave-5 killer), so the original source-model entry scheme
    # (enter at TD, phases {0, 0.5}) gets its fair test with settling.
    entry_phase=0.0
    jstems=['hip_flexion','knee_extension','ankle_dorsiflexion','MP_dorsiflexion']
    start_values={}
    for leg,phi in (('left',entry_phase),('right',entry_phase+0.5)):
        for stem,key in zip(jstems,('hip','knee','ankle','MP')):
            # scene q = zero + table (revision 2: the derived Oku angle zeros)
            start_values[f'{stem}_{leg}']=float(_table(tables[key],phi%1.0))+float(zeros[key])
    # THE TRUNK-VAULT TABLE (wave 8): the posture target theta*(phi) derived by
    # derive_trunk_vault.py (the wave-4 statics + the base-rot DOF + the sole
    # CoP envelope; min-max demand/cap ratio 0.881 <= 1 at every
    # single-support node). HAT-FORWARD-POSITIVE in the derivation's frame;
    # mapped into the ENGINE's base_rot_z frame by the same sign probe every
    # other table gets: pitch the assembled walker +10 deg about z and watch
    # the seat rise (slope +1 -> identity) or fall (slope -1 -> negation).
    _vault_path=ROOT/'tools/science_funnel/validation/gait_zero_20260919/trunk_vault_reachable.json'
    require(_vault_path.exists(),'gait_trunk_vault_missing','run derive_reachable_vault.py first')
    _vault_derived=json.loads(_vault_path.read_text(encoding='utf-8'))['theta_reachable_rad']
    require(len(_vault_derived)==21,'gait_trunk_vault_shape',len(_vault_derived))
    def _vault_at(phi):
        x=(phi%1.0)*20.0;k=min(19,int(x));f=x-k;return _vault_derived[k]*(1.0-f)+_vault_derived[k+1]*f
    _probe0=dict(start_values);_probe0['base_rot_z']=0.0
    _probe1=dict(start_values);_probe1['base_rot_z']=0.1745
    _h0=Assembly(model,values=_probe0,gravity=[0.,-9.80665,0.])
    _h1=Assembly(model,values=_probe1,gravity=[0.,-9.80665,0.])
    _p0=contract['contact_points']; _i0=min(range(len(_p0)),key=lambda i:float(_h0.point(_p0[i]['body'],_p0[i]['point_m'])[0][1]))
    _y0=float(_h0.point(_p0[_i0]['body'],_p0[_i0]['point_m'])[0][1])
    _y1=float(_h1.point(_p0[_i0]['body'],_p0[_i0]['point_m'])[0][1])
    _vault_sign=1.0 if (_y1-_y0)>0.0 else -1.0
    trunk_vault=[round(_vault_sign*t,4) for t in _vault_derived]  # ENGINE frame (base_rot_z+)
    def _contact_vx(phi):
        th1=zeros['hip']+_table(tables['hip'],phi)
        th2=th1+zeros['knee']+_table(tables['knee'],phi)
        p=th2+zeros['ankle']+_table(tables['ankle'],phi)
        x=_L1*_m.sin(th1)+_L2*_m.sin(th2)+((_XH if p>0 else _XM)*_m.cos(p))
        return x
    _d=1e-4
    _contact_rel_vx=(_contact_vx(entry_phase+_d)-_contact_vx(entry_phase-_d))/(2*_d)/float(contract['cycle_duration_s'])
    speed=-_contact_rel_vx  # base speed making the stance contact still on the ground
    for b in ('base_rot_x','base_rot_y','base_rot_z','base_trans_x','base_trans_y','base_trans_z'):
        start_values[b]=0.0  # probe the gait pose relative to the origin
    # The walker ENTERS ON the vault table: the reset pose is leaned at
    # theta*(entry phase) (the engine adds the table-slope pitch speed), so
    # the seat below is measured on the LEANED pose and the seated contact
    # does not dangle at the entry instant (the wave-6 load-transfer law).
    start_values['base_rot_z']=_vault_sign*_vault_at(entry_phase)
    asm0=Assembly(model,values=start_values,gravity=[0.,-9.80665,0.])
    heights=[float(asm0.point(p['body'],p['point_m'])[0][1]) for p in contract['contact_points']]
    # SEAT THE STANCE LEG ONLY (the single-support entry): the mid-stance leg
    # carries the body and its contact defines the floor; the swing leg must
    # be strictly airborne at the entry instant (a derived require, not a
    # hope).
    left_idx=[i for i,p in enumerate(contract['contact_points']) if p['name'].startswith('left')]
    right_idx=[i for i,p in enumerate(contract['contact_points']) if p['name'].startswith('right')]
    seated=min(heights[i] for i in left_idx)
    require(min(heights[i] for i in right_idx)>seated,
            'gait_entry_swing_not_clear',min(heights[i] for i in right_idx)-seated)
    base_y=-seated+contract['seating_scan']['reset_gap_target_m']
    defaults['start_at_tables']=True
    # ORBIT CAPTURE: settle at the entry pose under load for the servo's
    # settling time (3 periods at 4 Hz, zeta 0.8 ~= 0.19 s -> 57 ticks; 60
    # rounded) before releasing the clock -- the corrected statics prove the
    # pose holdable, so the load transfer completes before the stride begins.
    defaults['settle_ticks']=60
    defaults['base_speed_x_m_s']=float(speed)
    defaults['base_trans_y_m']=base_y
    # theta*(phi): the derived posture target (the trunk-pitch freedom, wave 8)
    tp_table=json.loads((ROOT/'tools/science_funnel/validation/gait_zero_20260919/trunk_pitch_table.json').read_text(encoding='utf-8'))
    posture_phases=[n['phi'] for n in tp_table['nodes']]
    posture_rads=[n['theta_star_rad'] for n in tp_table['nodes']]
    defaults['start_phase_left']=entry_phase
    defaults['start_phase_right']=(entry_phase+0.5)%1.0
    defaults['start_trunk_rad']=float(start_values['base_rot_z'])
    bundle={'schema':'chimera.earth_scene.v1','graph_hash':graph.graph_hash(),
            'scene':{'arm_translation_m':[0.,0.,0.],'world_id':'gait_walker_plane','ground_id':'gait_plane'},
            'gait_controller':{'gait_enabled':True,'recipe':{
                'schema':'chimera.gait_scene.v1',
                'coordinates':contract['coordinates'],
                'drives':contract['drives'],
                'cycle_duration_s':contract['cycle_duration_s'],
                'duty_factor_sampled':contract['duty_factor_sampled'],
                'servo_frequency_Hz':contract['servo_frequency_Hz'],
                'servo_damping_ratio':contract['servo_damping_ratio'],
                'capture_step_phase':contract['capture_step_phase'],
                'tables_rad':contract['tables_rad'],
                'trunk_vault_rad':trunk_vault,
                'zero_map_rad':contract['zero_map_rad'],
                'posture_target_phases':posture_phases,'posture_target_rad':posture_rads,
                'contact_points':contract['contact_points'],
                'contact_plane_height_m':contract['contact_plane_height_m'],
                'contact_friction':contract['contact_friction'],
                'tick_hz':contract['tick_hz'],'substeps':contract['substeps'],
                'defaults':defaults},
                'model':model,'seating_scan_measured':measured,
                'record_id':RECORD,'scope':'Gait walker: the derivation stages D-F runtime. Headless native scene for the F-G1..F-G8 falsifier suite; the live renderer path stays the qualified arm world (untouched).'},
            'sources':[{'title':'docs/research/20260918_gait_controller_derivation.md','url':'in-tree'}]}
    bundle['scene_sha256']=digest(bundle)
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    (out/'scene.json').write_bytes(canonical(bundle))
    return bundle


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'.tmp/gait-walker')
    a=p.parse_args()
    graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
    require(RECORD in graph.objects,'gait_model_record_missing',RECORD)
    b=compile_gait(graph,a.output)
    print(json.dumps({'scene':str(a.output/'scene.json'),'scene_sha256':b['scene_sha256'],
                      'seating_scan':b['gait_controller']['seating_scan_measured']}))
if __name__=='__main__':main()
