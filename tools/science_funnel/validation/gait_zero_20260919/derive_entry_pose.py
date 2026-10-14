"""Derive the wave-14 ENTRY FORE POSE (scene statics; the wave-13 banked next
membrane, receipt_wave13 -> receipt_wave14).

ONE law, no sweeps (Rule 1). The fore pose has exactly two continuous unknowns
(shoulder q1, elbow q2 -- shared by both legs through the z mirror) and both
are PINNED by requires that already exist:

  STANDING PIN (the compile-time seating scan's own require): at the standing
  defaults (hind q=0, base at leg_drop+2e-6, upright) the fore heel AND MP
  gaps must both sit in (0, 1e-5). Solving them AT the authored +2e-6 seating
  gap makes the pad flat (equal gaps) and pins the paw height -- two
  equations, two unknowns. Two roots exist (elbow-behind / elbow-forward);
  the branch is a DISCRETE choice, not a sweep.

  CAPTURE EQUATION (the wave-14 membrane): the settle capture should land the
  paw at the stepping law's symmetric touchdown offset
      x_off = v_settle_end * (DUTY_SAMPLED*T_CYCLE)/2
  AHEAD of the shoulder. The settle between the reset and the capture (60
  ticks of loaded settling with the soft 4 Hz fore servos) TRANSFERS the
  offset by a measured amount: delta_settle = measured wave-13 capture
  offset0 (baseline binary, this lane's run) - the same Assembly prediction
  for the OLD pose. The transfer is applied to the new pose; the
  pose_installed falsifier judges it (a miss is a finding, never a re-solve).

Outputs derived_entry_pose.json (consumed by gait_scene.py, the wave-1
zero-map pattern): fore joint targets + the capture prediction + the statics
+ the envelope closure + the entry-clock stagger derivation.
"""
import json,math,sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))

from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.gait_scene import RECORD,DERIVED,build_walker_model,seating_scan,require
from tools.science_funnel.coupled_arm import Assembly

OUT=ROOT/'tools/science_funnel/validation/gait_zero_20260919/derived_entry_pose.json'
HEEL=np.array([-0.012,-0.13555305347340657,0.])
MP=np.array([0.074,-0.129953,0.])
REF=0.5*(HEEL+MP)
RADIUS=0.004
# Baseline measurements (wave-13 binary at 554f40ed, this lane's run; the
# trace-derived numbers are in receipt_wave14.json measurements.baseline).
V_SETTLE=0.420440          # m/s, pelvis x-speed at tick 60 ([foreclk] xoff=0.101938 = v*DUTY*T/2)
THETA_CAP=-10.68131*math.pi/180.0   # trunk pitch at the capture tick ([trunk])
OFFSET0_MEASURED={'fore_left':-0.215670,'fore_right':-0.209846}  # [foreclk] arm
X_OFF_MEASURED=0.101938    # the engine's own x_off at the arm tick
T_CYCLE=0.71; DUTY=0.683; TICK=1.0/300.0; FORE_SHARE=0.45
SHOULDER_MOUNT=np.array([0.2689,-0.1331,0.0])

graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
record=graph.get(RECORD)
contract=record['physical']['contract']
derived=json.loads(DERIVED.read_text(encoding='utf-8'))
PLANE=float(contract['contact_plane_height_m'])
GAP_TARGET=float(contract['seating_scan']['reset_gap_target_m'])

BASE_POINTS=[('left_heel','foot_left',np.array([-0.012,0.,0.])),
             ('left_mp_head','foot_left',np.array([0.074,0.,0.])),
             ('right_heel','foot_right',np.array([-0.012,0.,0.])),
             ('right_mp_head','foot_right',np.array([0.074,0.,0.])),
             ('fore_left_heel','forearm_fore_left',HEEL),
             ('fore_left_mp_head','forearm_fore_left',MP),
             ('fore_right_heel','forearm_fore_right',HEEL),
             ('fore_right_mp_head','forearm_fore_right',MP)]

def make_model(q1,q2):
    m=build_walker_model(record,derived)
    for leg in ('fore_left','fore_right'):
        m['coordinates'][f'shoulder_flexion_{leg}']['default_rad']=float(q1)
        m['coordinates'][f'elbow_flexion_{leg}']['default_rad']=float(q2)
    return m

def point(asm,body,local):
    return np.asarray(asm.point(body,list(local))[0],dtype=float)

def fore_gaps(m,values):
    asm=Assembly(m,values=values,gravity=[0.,-9.80665,0.])
    out={}
    for side in ('left','right'):
        gh=point(asm,f'forearm_fore_{side}',HEEL)[1]+RADIUS-PLANE
        gm=point(asm,f'forearm_fore_{side}',MP)[1]+RADIUS-PLANE
        out[side]=(float(gh),float(gm))
    return out,asm

# ── 1. THE STANDING PIN: pad flat at the authored +2e-6 seating gap ─────────
def q2_flat(q1):
    """Elbow making the pad flat at the standing scan pose (heel gap = MP gap)."""
    m=make_model(q1,0.0)
    lo,hi=-1.6,1.6
    f=lambda q2: fore_gaps(m,{f'shoulder_flexion_fore_left':q1,f'elbow_flexion_fore_left':q2,
                              f'shoulder_flexion_fore_right':q1,f'elbow_flexion_fore_right':q2})[0]['left'][0]\
                   -fore_gaps(m,{f'shoulder_flexion_fore_left':q1,f'elbow_flexion_fore_left':q2,
                                 f'shoulder_flexion_fore_right':q1,f'elbow_flexion_fore_right':q2})[0]['left'][1]
    flo,fhi=f(lo),f(hi)
    require(flo*fhi<0,'entry_pose_flat_q2_bracket_failed',q1,flo,fhi)
    for _ in range(80):
        mid=0.5*(lo+hi);fm=f(mid)
        if flo*fm<=0:hi,fhi=mid,fm
        else:lo,flo=mid,fm
    return 0.5*(lo+hi)

def gap_at(q1,target):
    q2=q2_flat(q1)
    m=make_model(q1,q2)
    g,_=fore_gaps(m,{**{f'shoulder_flexion_fore_{s}':q1 for s in ('left','right')},
                     **{f'elbow_flexion_fore_{s}':q2 for s in ('left','right')}})
    return g['left'][0]-target,q2

def solve_standing(target):
    """Both branches of gap(q1)=target with the pad held flat."""
    roots=[]
    for lo,hi in ((-1.599,-1e-3),(1e-3,1.599)):
        gl,_=gap_at(lo,target);gh,_=gap_at(hi,target)
        if gl*gh>0:continue
        a,b=lo,hi
        for _ in range(80):
            mid=0.5*(a+b);gm,_=gap_at(mid,target)
            if gl*gm<=0:b=mid
            else:a,gl=mid,gm
        q1=0.5*(a+b);q2=q2_flat(q1)
        roots.append((q1,q2))
    require(len(roots)==2,'entry_pose_branch_count',len(roots))
    return roots

# ── 2. THE RUNTIME LEANED RESET POSE (the scene's own entry path) ───────────
def start_values_for(m):
    """The scene's TD entry start values + the vault sign probe + the seat."""
    tables=contract['tables_rad'];zeros=contract['zero_map_rad']
    def _table(t,phi):
        x=phi*20.0;k=min(19,int(x));f=x-k;return t[k]*(1.0-f)+t[k+1]*f
    jstems=['hip_flexion','knee_extension','ankle_dorsiflexion','MP_dorsiflexion']
    sv={}
    for leg,phi in (('left',0.0),('right',0.5)):
        for stem,key in zip(jstems,('hip','knee','ankle','MP')):
            sv[f'{stem}_{leg}']=float(_table(tables[key],phi%1.0))+float(zeros[key])
    vault=json.loads((ROOT/'tools/science_funnel/validation/gait_zero_20260919/trunk_vault_reachable.json')
                     .read_text(encoding='utf-8'))['theta_reachable_rad']
    def _vault_at(phi):
        x=(phi%1.0)*20.0;k=min(19,int(x));f=x-k;return vault[k]*(1.0-f)+vault[k+1]*f
    probe0=dict(sv);probe0['base_rot_z']=0.0
    probe1=dict(sv);probe1['base_rot_z']=0.1745
    a0=Assembly(m,values=probe0,gravity=[0.,-9.80665,0.])
    a1=Assembly(m,values=probe1,gravity=[0.,-9.80665,0.])
    i0=min(range(len(BASE_POINTS)),key=lambda i:point(a0,BASE_POINTS[i][1],BASE_POINTS[i][2])[1])
    y0=point(a0,BASE_POINTS[i0][1],BASE_POINTS[i0][2])[1]
    y1=point(a1,BASE_POINTS[i0][1],BASE_POINTS[i0][2])[1]
    sign=1.0 if (y1-y0)>0.0 else -1.0
    lean=sign*_vault_at(0.0)
    for b in ('base_rot_x','base_rot_y','base_rot_z','base_trans_x','base_trans_y','base_trans_z'):
        sv[b]=0.0
    return sv,lean,sign

def leaned_pose(m,q1,q2,lean):
    """Seat the leaned entry pose (all 8 contacts; the lowest defines the seat)."""
    sv,_,_=start_values_for(m)
    sv['base_rot_z']=lean
    asm=Assembly(m,values=sv,gravity=[0.,-9.80665,0.])
    hs=[point(asm,b,p)[1] for _,b,p in BASE_POINTS]
    sv['base_trans_y']=-min(hs)+GAP_TARGET
    return sv

def capture_offset(m,q1,q2,lean):
    """paw_ref_x - shoulder_x at the leaned seated pose (Assembly-exact, both legs).

    The shoulder IS the upperarm frame origin (the joint child location); the
    mount parent_location lives in the PELVIS frame, never in the arm frame."""
    sv=leaned_pose(m,q1,q2,lean)
    asm=Assembly(m,values=sv,gravity=[0.,-9.80665,0.])
    out={}
    for side in ('left','right'):
        sh=point(asm,'upperarm_fore_'+side,[0.,0.,0.])
        paw=point(asm,'forearm_fore_'+side,REF)
        out[side]=float(paw[0]-sh[0])
    g,_=fore_gaps(m,sv)
    return out,g,sv

# ── 3. STATICS: the fore load line at the pose (declared share s) ───────────
def statics(m,sv,share):
    asm=Assembly(m,values=sv,gravity=[0.,-9.80665,0.])
    W=float(np.sum([b['mass_kg'] for b in m['bodies']]))*9.80665
    R=share*W/2.0
    rows={}
    for side in ('left','right'):
        rows[side]={}
        for joint,coord in (('shoulder',f'shoulder_flexion_fore_{side}'),('elbow',f'elbow_flexion_fore_{side}')):
            idx=[i for i,c in enumerate(asm.coordinates) if c==coord]
            require(len(idx)==1,'entry_pose_coord_row',coord)
            worst=0.0
            for split in ((1.0,0.0),(0.0,1.0),(0.5,0.5)):
                tg=asm.gravity_force[idx[0]]
                tc=split[0]*asm.point_force(f'forearm_fore_{side}',HEEL,np.array([0.,R,0.]))[idx[0]] \
                  +split[1]*asm.point_force(f'forearm_fore_{side}',MP,np.array([0.,R,0.]))[idx[0]]
                worst=max(worst,abs(-(tg+tc)))
            rows[side][joint]=float(worst)
    return {'weight_N':W,'pad_reaction_N':R,'demands_N_m':rows,
            'shoulder_cap_N_m':4.229*(share/0.45),'elbow_cap_N_m':3.76}

# ── 4. THE ENTRY-CLOCK STAGGER (derived from the hind entry phases) ─────────
def entry_clock():
    Tf=T_CYCLE/TICK
    waits={}
    for leg,phi_h in (('fore_right',0.5),('fore_left',0.0)):
        lift_wait=max(0.0,(DUTY-phi_h)*T_CYCLE+0.25*T_CYCLE)
        waits[leg]={'hind_phase':phi_h,'lift_wait_s':lift_wait,'lift_wait_ticks':lift_wait/TICK}
    return waits

# ── solve, evaluate both branches, choose, emit ─────────────────────────────
def main():
    roots=solve_standing(GAP_TARGET)
    old_m=make_model(-0.903,0.838)
    old_lean=start_values_for(old_m)[1]
    old_pred,_,_=capture_offset(old_m,-0.903,0.838,old_lean)
    old_pred_cap,_,_=capture_offset(old_m,-0.903,0.838,THETA_CAP)
    delta={s:OFFSET0_MEASURED['fore_left' if s=='left' else 'fore_right']-old_pred[s] for s in ('left','right')}
    delta_cap={s:OFFSET0_MEASURED['fore_left' if s=='left' else 'fore_right']-old_pred_cap[s] for s in ('left','right')}
    xoff=V_SETTLE*(DUTY*T_CYCLE)/2.0
    branches=[]
    for q1,q2 in roots:
        m=make_model(q1,q2)
        lean=start_values_for(m)[1]
        pred,gaps,_=capture_offset(m,q1,q2,lean)
        pred_cap,_,_=capture_offset(m,q1,q2,THETA_CAP)
        p={s:pred_cap[s]+delta[s] for s in ('left','right')}
        p_cap={s:pred_cap[s]+delta_cap[s] for s in ('left','right')}
        err=np.mean([abs(p[s]-xoff) for s in ('left','right')])
        branches.append({'q1_rad':q1,'q2_rad':q2,'lean_rad':lean,
                         'offset_reset':pred,'offset_at_capture_lean':pred_cap,
                         'capture_prediction_transfer':p,'capture_prediction_transfer_capture_delta':p_cap,
                         'mean_abs_error_vs_xoff_m':float(err)})
    branches.sort(key=lambda b:b['mean_abs_error_vs_xoff_m'])
    chosen=branches[0]
    q1,q2=chosen['q1_rad'],chosen['q2_rad']
    m=make_model(q1,q2)
    lean=chosen['lean_rad']
    # the compile-time seating scan on the modified model (the real require)
    scan=seating_scan(m,record)
    # the envelope closure at the measured settle-end speed
    Tf=T_CYCLE/TICK
    clock=entry_clock()
    _,gaps_chosen,_=capture_offset(m,q1,q2,THETA_CAP)
    h=abs(-0.081664-(0.000003))  # baseline capture shoulder-over-ref height (measured)
    dmax=0.125+float(np.hypot(REF[0],REF[1]))
    amax=math.sqrt(max(dmax*dmax-h*h,0.0))
    env={}
    for leg,w in clock.items():
        t=w['lift_wait_s']
        off_end=xoff-V_SETTLE*t
        env[leg]={'lift_wait_ticks':w['lift_wait_ticks'],'offset_at_lift_m':off_end,
                  'annulus_bound_m':amax,'margin_m':amax-abs(off_end)-V_SETTLE*TICK}
        require(env[leg]['margin_m']>0,'entry_pose_envelope_violated',leg,env[leg])
    sweep={'total_sweep_m':2*xoff+0.08,'bound_m':2*amax,'closes':2*xoff+0.08<=2*amax}
    require(sweep['closes'],'entry_pose_sweep_violated',sweep)
    # statics at the authored (pre-fold) settle pose
    sv=leaned_pose(m,q1,q2,lean)
    stat=statics(m,sv,FORE_SHARE)
    for side in ('left','right'):
        require(stat['demands_N_m'][side]['shoulder']<=stat['shoulder_cap_N_m'],
                'entry_pose_shoulder_statics',side,stat['demands_N_m'][side])
        require(stat['demands_N_m'][side]['elbow']<=stat['elbow_cap_N_m'],
                'entry_pose_elbow_statics',side,stat['demands_N_m'][side])
    out={'schema':'chimera.entry_pose.v1',
         'provenance':{'script':'tools/science_funnel/validation/gait_zero_20260919/derive_entry_pose.py',
                       'law':'standing seating pin (pad flat at +2e-6) pins (q1,q2); capture equation selects the branch; settle transfer measured on the wave-13 baseline (delta applied); entry clock = lateral-sequence lift grid',
                       'measured':{'v_settle_end_m_s':V_SETTLE,'x_off_m':xoff,'x_off_engine_at_arm_m':X_OFF_MEASURED,
                                   'theta_capture_deg':THETA_CAP*180/math.pi,
                                   'offset0_measured_m':OFFSET0_MEASURED,
                                   'offset0_old_pose_assembly_prediction_m':old_pred,
                                   'delta_settle_m':delta,
                                   'delta_settle_capture_lean_m':delta_cap}},
         'validation':{'old_pose_prediction_note':'delta_settle is DEFINED on the old pose; its pose-invariance to first order is the theory the pose_installed falsifier tests'},
         'branches':branches,'chosen':chosen,
         'seating_scan':{'reset_gaps_m':scan['reset_gaps_m'],
                         'com_projection_model_m':scan['com_projection_model_m'],
                         'assembly_mass_kg':scan['assembly_mass_kg'],'weight_N':scan['weight_N'],
                         'fore_gaps_at_leaned_reset':gaps_chosen},
         'envelope':{'x_off_m':xoff,'amax_at_capture_height_m':amax,'per_leg':env,'sweep':sweep},
         'entry_clock':clock,
         'statics':stat,
         'targets':{'shoulder_rad':q1,'elbow_rad':q2}}
    OUT.write_text(json.dumps(out,indent=1),encoding='utf-8')
    print(json.dumps({'chosen':{'q1_rad':q1,'q2_rad':q2},
                      'capture_prediction_m':chosen['capture_prediction_transfer'],
                      'x_off_target_m':xoff,
                      'seating_ok':True,'statics':stat['demands_N_m'],
                      'entry_clock':{k:v['lift_wait_ticks'] for k,v in clock.items()}}))
if __name__=='__main__':main()
