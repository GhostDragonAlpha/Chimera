"""Derive the wave-15 LEVEL ENTRY (scene statics; receipt_wave14 -> receipt_wave15).

ONE law, no sweeps (Rule 1). The entry trunk state has ONE continuous unknown
(the reset lean theta_e; the entry phase stays the wave-8 TD entry {0,0.5},
whose settling-contact and no-skid constraints are leg-geometry laws the lean
does not touch) and it is PINNED by the wave-14 strut-difference law:

  STRUT-BOUND LAW (calibrated, Assembly-exact, runtime-validated): at the
  leaned reset the paw gaps are set by the SEAT (base_y = -min(raw heights) +
  2e-6), so every paw's dangle is raw_p(lean) - min_p raw_p(lean). The
  fore-hind strut difference the waves measured is the TD-side hind heel
  dangle over the seated fore pads:
      D(lean) = raw_heel(lean) - min_p raw_p(lean) + 2e-6
  with raw heights from the Assembly at the authored entry state. Calibration
  (this script re-measures both points on the Assembly; the forward point is
  runtime-validated against the wave-14 trace tick-0 gap 1.051e-1 m):
      wave-13 back pose  @ -0.2064 rad: D = 6.50 cm  (survived its settle)
      wave-14 fwd pose   @ -0.2064 rad: D = 10.52 cm (fatal: refused tick 30)
  The measured SURVIVABLE band is D <= 0.059 m (receipt_wave14). The law is
  linear in lean on each branch through (D(0), D(+-theta_v)) -- three
  Assembly evaluations fix the two slopes and the intercept; no sweep.

  THE LEVEL ENTRY: theta_e = 0 is the UNIQUE global minimum of D (both slopes
  positive away from 0 -- measured), gives D(0) = 4.62 cm <= 0.059 with the
  band's full margin, and is ON the vault table: theta*(phi) crosses zero at
  phi_z ~= 0.14 (the wave-8 single-support entry phase ~0.35 carries the
  OPPOSITE sign -- the phase space straddles zero). The level state is not
  foreign to the table; it is the table's own zero-crossing state.

  HAND-OFF LAW (the entry-to-table transition): the wave-10 gradual vault
  activation ramps the posture target to FULL theta*(entry phase) BY the
  settle capture -- exactly the leaned capture the strut bound forbids (the
  fore MP pokes sin(|theta*|) deeper every tick, regrowing the wave-14
  geometry through the settle). The level entry therefore holds the posture
  target at 0 through the settle (trunk LEVEL at the capture) and blends
  linearly onto theta*(phi) over the FIRST cycle:
      amp(t) = clamp((t - t_capture)/T_cycle, 0, 1)
  -- the wave-10 gradualness preserved, parameter-free (T_cycle in-tree),
  full table from the second cycle on. The v[2] init is the blend's own rate
  at t=0 (0). The named tension: cycle 1 runs under a partial lean, so the
  vault-statics margin (0.881) is not yet centered there -- measured by the
  run, never patched.

Also re-derived here (the entry state changed, so the dependent numbers are
re-derived, wave-14 pattern): the capture equation at the level reset (the
measured delta_settle transfer applied), the envelope closure at THAT capture
(the LF grid lift is tau_env-clamped -- named), the fore statics load line,
contact_vy(0) <= 0 and the no-skid speed (leg-geometry laws, lean-independent
-- re-measured to show it), and the find that the scene's vestigial
single-support require (gait_entry_swing_not_clear) COLLIDES with the level
seat (the L/R fore pads seat symmetrically; a strict ordering is impossible)
-- its own comment scopes it to the biped path; the quadruped path gets the
strut bound as its compile-time require instead.

Outputs derived_level_entry.json (consumed by gait_scene.py).
"""
import json,math,sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))

from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.gait_scene import RECORD,DERIVED,build_walker_model,require
from tools.science_funnel.coupled_arm import Assembly

OUT=ROOT/'tools/science_funnel/validation/gait_zero_20260919/derived_level_entry.json'
POSE_PATH=ROOT/'tools/science_funnel/validation/gait_zero_20260919/derived_entry_pose.json'
HEEL=np.array([-0.012,0.,0.]); HMP=np.array([0.074,0.,0.])            # hind sole locals
FHEEL=np.array([-0.012,-0.13555305347340657,0.]); FMP=np.array([0.074,-0.129953,0.])
FREF=0.5*(FHEEL+FMP)
RADIUS=0.004
T_CYCLE=0.71; DUTY=0.683; TICK=1.0/300.0
THETA_VAULT=0.2064            # |theta*(entry phase 0)| -- the current leaned reset
D_SURV=0.059                  # the measured survivable band (receipt_wave14)
D_LIVED=0.1744                # the strongest hind dangle that SURVIVED a settle
                              # (wave-13 entry, right heel, this script re-measures)
FORE_SHARE=0.45
DELTA_SETTLE={'left':-0.0980,'right':-0.0922}  # measured settle transfer (receipt_wave14;
                                               # capture offset0 minus Assembly prediction, old pose)

graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
record=graph.get(RECORD)
contract=record['physical']['contract']
derived=json.loads(DERIVED.read_text(encoding='utf-8'))
PLANE=float(contract['contact_plane_height_m'])
GAP=float(contract['seating_scan']['reset_gap_target_m'])
POSE=json.loads(POSE_PATH.read_text(encoding='utf-8'))
require(POSE.get('schema')=='chimera.entry_pose.v1','level_entry_pose_schema')
Q1F,Q2F=float(POSE['targets']['shoulder_rad']),float(POSE['targets']['elbow_rad'])

BASE_POINTS=[('left_heel','foot_left',HEEL),('left_mp_head','foot_left',HMP),
             ('right_heel','foot_right',HEEL),('right_mp_head','foot_right',HMP),
             ('fore_left_heel','forearm_fore_left',FHEEL),('fore_left_mp_head','forearm_fore_left',FMP),
             ('fore_right_heel','forearm_fore_right',FHEEL),('fore_right_mp_head','forearm_fore_right',FMP)]

def make_model():
    return build_walker_model(record,derived)

def entry_values(m,lean):
    """The scene's TD-entry start values (hind machinery unchanged) at a lean,
    seated exactly as the scene seats (base_y = -min(raw)+gap)."""
    tables=contract['tables_rad'];zeros=contract['zero_map_rad']
    def _table(t,phi):
        x=phi*20.0;k=min(19,int(x));f=x-k;return t[k]*(1.0-f)+t[k+1]*f
    jstems=['hip_flexion','knee_extension','ankle_dorsiflexion','MP_dorsiflexion']
    sv={}
    for leg,phi in (('left',0.0),('right',0.5)):
        for stem,key in zip(jstems,('hip','knee','ankle','MP')):
            sv[f'{stem}_{leg}']=float(_table(tables[key],phi%1.0))+float(zeros[key])
    for b in ('base_rot_x','base_rot_y','base_rot_z','base_trans_x','base_trans_y','base_trans_z'):
        sv[b]=0.0
    sv['base_rot_z']=float(lean)
    asm=Assembly(m,values=sv,gravity=[0.,-9.80665,0.])
    raw={n:float(asm.point(b,list(p))[0][1]) for n,b,p in BASE_POINTS}
    sv['base_trans_y']=-min(raw.values())+GAP
    asm2=Assembly(m,values=sv,gravity=[0.,-9.80665,0.])
    gaps={n:float(asm2.point(b,list(p))[0][1])+RADIUS-PLANE for n,b,p in BASE_POINTS}
    return sv,raw,gaps

def struts(m,lean):
    """The strut law at a lean: per-point raw heights, gaps, the seat, and the
    calibrated fore-hind strut difference (the TD-side heel dangle)."""
    sv,raw,gaps=entry_values(m,lean)
    lo=min(raw.values())
    d_td=raw['left_heel']-lo+GAP          # the calibrated quantity (heel over the seat)
    spread=max(raw.values())-lo           # the full 8-point spread
    return {'lean_rad':float(lean),'base_trans_y_m':float(sv['base_trans_y']),
            'raw_heights_m':raw,'gaps_m':gaps,
            'd_td_heel_m':float(d_td),'all_paw_spread_m':float(spread),
            'fore_lr_gap_equality_m':float(abs(gaps['fore_left_heel']-gaps['fore_right_heel']))}

def reset_offset(m,sv):
    """paw_ref_x - shoulder_x at the given seated reset pose (Assembly-exact)."""
    asm=Assembly(m,values=sv,gravity=[0.,-9.80665,0.])
    out={}
    for side in ('left','right'):
        sh=np.asarray(asm.point(f'upperarm_fore_{side}',[0.,0.,0.])[0],dtype=float)
        paw=np.asarray(asm.point(f'forearm_fore_{side}',list(FREF))[0],dtype=float)
        out[side]=float(paw[0]-sh[0])
    return out,asm

def statics(m,sv,share):
    """The fore load line at the pose (the wave-14 statics pattern)."""
    asm=Assembly(m,values=sv,gravity=[0.,-9.80665,0.])
    W=float(np.sum([b['mass_kg'] for b in m['bodies']]))*9.80665
    R=share*W/2.0
    rows={}
    for side in ('left','right'):
        rows[side]={}
        for joint,coord in (('shoulder',f'shoulder_flexion_fore_{side}'),('elbow',f'elbow_flexion_fore_{side}')):
            idx=[i for i,c in enumerate(asm.coordinates) if c==coord]
            require(len(idx)==1,'level_entry_coord_row',coord)
            worst=0.0
            for split in ((1.0,0.0),(0.0,1.0),(0.5,0.5)):
                tg=asm.gravity_force[idx[0]]
                tc=split[0]*asm.point_force(f'forearm_fore_{side}',FHEEL,np.array([0.,R,0.]))[idx[0]] \
                  +split[1]*asm.point_force(f'forearm_fore_{side}',FMP,np.array([0.,R,0.]))[idx[0]]
                worst=max(worst,abs(-(tg+tc)))
            rows[side][joint]=float(worst)
    return {'weight_N':W,'pad_reaction_N':R,'demands_N_m':rows,
            'shoulder_cap_N_m':4.229*(share/0.45),'elbow_cap_N_m':3.76}

def leg_laws():
    """The settling-contact and no-skid speed laws at the TD entry phase 0
    (the scene's own formulas -- leg geometry, lean-independent)."""
    tables=contract['tables_rad'];zeros=contract['zero_map_rad']
    seg=derived['body_model']['segments_Table1']
    _L1=float(seg['thigh']['length_m']);_L2=float(seg['shank']['length_m'])
    _XM=0.074;_XH=-0.012;T=float(contract['cycle_duration_s'])
    def _table(t,phi):
        x=phi*20.0;k=min(19,int(x));f=x-k;return t[k]*(1.0-f)+t[k+1]*f
    def _contact_xy(phi):
        th1=zeros['hip']+_table(tables['hip'],phi)
        th2=th1+zeros['knee']+_table(tables['knee'],phi)
        p=th2+zeros['ankle']+_table(tables['ankle'],phi)
        x=_L1*math.sin(th1)+_L2*math.sin(th2)+((_XH if p>0 else _XM)*math.cos(p))
        y=-_L1*math.cos(th1)-_L2*math.cos(th2)+((_XH if p>0 else _XM)*math.sin(p))
        return x,y
    cd=1e-4
    vy=(_contact_xy(cd)[1]-_contact_xy(-cd)[1])/(2*cd)/T
    vx=(_contact_xy(cd)[0]-_contact_xy(-cd)[0])/(2*cd)/T
    return {'contact_vy_m_s':float(vy),'contact_vx_m_s':float(vx),'no_skid_speed_m_s':float(-vx)}

def vault_zero_crossing():
    """The ENGINE-frame vault table's lean-zero crossing (the scene's sign
    probe is +1: negative engine lean drops forward points)."""
    vault=json.loads((ROOT/'tools/science_funnel/validation/gait_zero_20260919/trunk_vault_reachable.json')
                     .read_text(encoding='utf-8'))['theta_reachable_rad']
    def at(phi):
        x=(phi%1.0)*20.0;k=min(19,int(x));f=x-k;return vault[k]*(1.0-f)+vault[k+1]*f
    phi_z=None
    for i in range(20):
        a,b=vault[i],vault[i+1]
        if a<0.0<=b or a>0.0>=b:
            phi_z=(i+abs(a)/(abs(a)+abs(b)))*0.05;break
    require(phi_z is not None,'level_entry_no_zero_crossing')
    return {'phi_zero_crossing':float(phi_z),'theta_at_crossing_rad':float(at(phi_z)),
            'theta_at_wave8_phase_0.35_rad':float(at(0.35)),
            'table':vault}

def main():
    m=make_model()
    # ── 1. THE STRUT LAW: three leans, the calibrated slopes, the band ──────
    s_neg=struts(m,-THETA_VAULT)
    s_0=struts(m,0.0)
    s_pos=struts(m,+THETA_VAULT)
    # validation against the wave-14 runtime tick-0 gap (the trace's 1.051e-1)
    require(abs(s_neg['d_td_heel_m']-0.105190)<2e-3,'level_entry_calibration_fwd',
            s_neg['d_td_heel_m'])
    slope_neg=(s_neg['d_td_heel_m']-s_0['d_td_heel_m'])/THETA_VAULT   # dD/d|lean|, leaned branch
    slope_pos=(s_pos['d_td_heel_m']-s_0['d_td_heel_m'])/THETA_VAULT   # nose-up branch
    require(slope_neg>0 and slope_pos>0,'level_entry_not_minimal_at_zero',
            (slope_neg,slope_pos))  # theta=0 must be the UNIQUE minimum of D
    theta_lo=-((D_SURV-s_0['d_td_heel_m'])/slope_neg)   # most-negative admissible lean
    require(theta_lo<0.0,'level_entry_band_empty',theta_lo)
    require(s_0['d_td_heel_m']<=D_SURV,'level_entry_level_breaches_band',
            s_0['d_td_heel_m'])
    require(s_0['all_paw_spread_m']<=D_LIVED,'level_entry_level_beats_survived',
            s_0['all_paw_spread_m'])
    # the wave-13 back branch for the calibration record (both points re-measured)
    mb=build_walker_model(record,derived)
    for leg in ('fore_left','fore_right'):
        mb['coordinates'][f'shoulder_flexion_{leg}']['default_rad']=-0.903
        mb['coordinates'][f'elbow_flexion_{leg}']['default_rad']=0.838
    b_neg=struts(mb,-THETA_VAULT); b_0=struts(mb,0.0)
    # ── 2. THE REQUIRE COLLISION (the vestigial single-support ordering) ────
    lr_equal=s_0['fore_lr_gap_equality_m']
    require(lr_equal<1e-9,'level_entry_fore_symmetry_broken',lr_equal)
    # ── 3. THE ZERO CROSSING (the level state is on the table) ──────────────
    zc=vault_zero_crossing()
    # ── 4. THE LEG-GEOMETRY LAWS (unchanged by the lean; re-measured) ───────
    laws=leg_laws()
    require(laws['contact_vy_m_s']<=0.0,'level_entry_settling_contact',laws)
    # ── 5. THE CAPTURE EQUATION at the level reset ──────────────────────────
    sv_level,_,_=entry_values(m,0.0)
    off_level,_=reset_offset(m,sv_level)
    pred={s:off_level[s]+DELTA_SETTLE[s] for s in ('left','right')}
    pred_mean=0.5*(pred['left']+pred['right'])
    # ── 6. THE ENVELOPE at THAT capture (the tau_env clamp named) ───────────
    v_settle=0.420440   # measured prior (wave-13/14 baseline); the clock re-reads v at the arm
    # The capture happens AFTER the settle fold: the baseline measured the
    # shoulder-over-ref height at the capture tick at 0.081667 m (receipt_wave14
    # derivation; the fold hangs the arm to nearly the same height whatever the
    # authored pose -- the same first-order invariance delta_settle assumes).
    h_cap=abs(-0.081664-0.000003)
    dmax=0.125+float(np.hypot(FREF[0],FREF[1]))
    amax=math.sqrt(max(dmax*dmax-h_cap*h_cap,0.0))
    Tf=T_CYCLE/TICK  # ticks per cycle (213): the hand-off blend length
    env={}
    for leg,phi_h in (('fore_right',0.5),('fore_left',0.0)):
        grid=(max(0.0,(DUTY-phi_h))*T_CYCLE+0.25*T_CYCLE)/TICK   # seconds -> ticks
        tau_env=max(0.0,(amax+pred_mean-v_settle*TICK)/v_settle)/TICK
        env[leg]={'grid_lift_wait_ticks':grid,'tau_env_ticks':tau_env,
                  'lift_wait_ticks':min(grid,tau_env),
                  'offset_at_lift_m':pred_mean-v_settle*min(grid,tau_env)*TICK,
                  'annulus_bound_m':amax,
                  'margin_m':amax-abs(pred_mean-v_settle*min(grid,tau_env)*TICK)-v_settle*TICK}
        require(env[leg]['margin_m']>=-1e-9,'level_entry_envelope_violated',leg,env[leg])
    # ── 7. STATICS at the level entry state (the entry state changed) ───────
    stat=statics(m,sv_level,FORE_SHARE)
    for side in ('left','right'):
        require(stat['demands_N_m'][side]['shoulder']<=stat['shoulder_cap_N_m'],
                'level_entry_shoulder_statics',side,stat['demands_N_m'][side])
        require(stat['demands_N_m'][side]['elbow']<=stat['elbow_cap_N_m'],
                'level_entry_elbow_statics',side,stat['demands_N_m'][side])
    # ── 8. emit ─────────────────────────────────────────────────────────────
    out={'schema':'chimera.level_entry.v1',
         'provenance':{'script':'tools/science_funnel/validation/gait_zero_20260919/derive_level_entry.py',
                       'law':'strut-bound law D(lean)=raw_heel(lean)-min_p raw_p(lean)+2e-6 (the seat sets every dangle); linear in lean through (D(0), D(+/-theta_vault)); theta_e=0 the unique minimum, on the vault table at its zero crossing; hand-off amp=clamp((t-t_capture)/T_cycle,0,1)',
                       'pose_source':'derived_entry_pose.json (wave-14 standing pin, forward branch, unchanged)',
                       'measured':{'D_SURV_m':D_SURV,'D_LIVED_m':D_LIVED,
                                   'theta_vault_rad':THETA_VAULT,
                                   'delta_settle_m':DELTA_SETTLE,
                                   'v_settle_prior_m_s':v_settle}},
         'strut_law':{'level':s_0,'leaned':s_neg,'nose_up':s_pos,
                      'slope_neg_rad_m':float(slope_neg),'slope_pos_rad_m':float(slope_pos),
                      'theta_admissible_min_rad':float(theta_lo),
                      'back_branch_calibration':{'leaned':{k:b_neg[k] for k in ('d_td_heel_m','all_paw_spread_m','base_trans_y_m')},
                                                  'level_d_td_heel_m':float(b_0['d_td_heel_m']),
                                                  'note':'wave-13 back branch re-measured on the Assembly; its leaned TD-heel dangle is the 5.9-6.5 cm survivable marker'}},
         'require_collision':{'finding':'the single-support require gait_entry_swing_not_clear demands min(right heights) > min(left heights); at the level reset the L/R fore pads seat symmetrically (gap equality below) so the strict ordering is impossible at ANY seat',
                              'fore_lr_gap_equality_m':float(lr_equal),
                              'resolution':'the require is scoped to the single-support (biped) path exactly as its own comment states; the quadruped TD-entry path enforces the strut bound instead (scene require: TD-heel dangle <= D_SURV and every paw dangle <= D_LIVED)'},
         'zero_crossing':zc,
         'leg_geometry_laws':laws,
         'capture_prediction':{'reset_offset_m':off_level,'predicted_capture_offset_m':pred,
                               'predicted_mean_m':float(pred_mean),'band_half_width_m':0.025},
         'envelope':{'x_off_prior_m':v_settle*(DUTY*T_CYCLE)/2.0,
                     'amax_at_level_capture_m':amax,'per_leg':env,
                     'note':'the LF grid lift (198.7) exceeds tau_env at the near-central capture; the committed clock clamps to tau_env -- named, measured by the stagger census'},
         'handoff':{'law':'amp(t)=clamp((t-t_capture)/T_cycle,0,1); target_post=amp*theta*(phi); v2 init = amp(0)*table_slope = 0',
                    'blend_ticks':Tf,'trunk_handoff_ticks':Tf},
         'statics':stat,
         'entry_state':{'entry_trunk_rad':0.0,'start_phase_left':0.0,'start_phase_right':0.5}}
    OUT.write_text(json.dumps(out,indent=1),encoding='utf-8')
    print(json.dumps({'d_td_level_m':s_0['d_td_heel_m'],'d_td_leaned_m':s_neg['d_td_heel_m'],
                      'spread_level_m':s_0['all_paw_spread_m'],
                      'theta_band_min_rad':theta_lo,
                      'phi_zero_crossing':zc['phi_zero_crossing'],
                      'capture_prediction_m':pred,
                      'env_lift_ticks':{k:round(v['lift_wait_ticks'],2) for k,v in env.items()},
                      'statics_N_m':{s:stat['demands_N_m'][s] for s in ('left','right')}}))
if __name__=='__main__':main()
