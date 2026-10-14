"""Derive the wave-16 LOAD/STRUT TRADE (scene statics; receipt_wave15 -> receipt_wave16).

ONE law, two branches, no sweeps (Rule 1). Wave 15 measured the two sides of
ONE quantity: the entry trunk lean drops the forward paw (the strut law) AND
presses it down (the fore load). The membrane: derive fore_reaction(theta) on
the Assembly and pick the entry lean inside the strut band that PLANTS the fore.

  N_PLANT (the planting threshold, from the measured anchors -- the equation
  and its inputs NAMED): a fore pad is pinned while its friction budget holds
  the settle's horizontal demand,
      mu * N  >=  F_h           (Coulomb static cone, mu = the store's
                                 contact_friction = 0.6)
  The two measured calibration points bracket the threshold:
      wave-15 level anchor  : N = 1.923/3.276 N per pad, slip 0.796/0.786 m/s
                              -- SLIDING  (this lane's baseline run, tick 0)
      wave-14 leaned anchor : N = 13.58/8.27 N per pad, slip 1.1 mm
                              -- PINNED   (receipt_wave14/15)
  so F_h/mu, hence N_plant, is bracketed:
      N_plant_pad  in ( 3.276 , 13.58 ) N   (largest load measured SLIDING ...
                                            largest load measured PINNED)
      N_plant_total(4 fore pts) in ( 5.199 , 21.85 ) N
  The falsifier bound is the CONSERVATIVE low end (the slide ceiling): the
  trade must beat every load known to slide. The pinned marker is reported
  alongside (the full-plant point). No number is chosen.

  FORE_REACTION(theta) (the reset statics): the seated body on fore/hind
  contact lines, the lever law
      F_fore(theta) = W * clamp( (x_com(theta) - x_hind) / (x_fore - x_hind), 0, 1 )
  with x_com(theta) measured on the Assembly at the SEATED reset state (the
  seat moves with the lean), x_fore the fore contact line, and x_hind the hind
  resultant. Wave-15 anchors calibrate: ~0 N fore at theta=0 (x_com 0.117 m
  BEHIND the hind line -- the backward tip) and 21.85 N total at theta_vault.

  BRANCH A (primary, the assembly the runtime assembles TODAY): the owed
  hind-reset phi-column defect means the RIGHT hind's joints are assembled
  from the phi=1.0==0.0 (TD) column against its 0.5 clock (banked wave 15;
  this lane's baseline re-measures the runtime dangles 4.575/4.557 cm vs the
  scene-derived 4.62/9.19). Branch A evaluates the trade on THAT assembly:
  both hind feet at the TD column make x_hind DETERMINATE, and x_com stays
  behind it through the whole strut band -> F_fore == 0 < N_plant everywhere
  -> NO theta in [-0.0449, 0] plants the fore. The falsification is
  derivation-stage; the membrane executes BRANCH B.

  BRANCH B (the owed repair, demanded by the derivation's own inequality):
  the hind reset phi-column defect is repaired (the right hind assembles at
  its 0.5 clock column; itemized in the receipt with before/after baselines),
  and the whole trade is re-derived on the CORRECTED assembly: the strut law
  D(theta) at three leans, the load anchors' bracket, the CoM margin at level
  (the right hind's mid-stance geometry moves the hind contact line -- the
  0.117 m deficit may shrink wholesale), the band, and theta_e. The corrected
  state is statically INDETERMINATE (three sagittal contact lines: right hind,
  left hind, fore), so the derivation yields a BRACKET, not a point: the run's
  fore-load census is the direct test. The capture prediction is LOAD-AWARE:
  delta_settle interpolates linearly in the load fraction between the two
  measured anchors (unloaded +0.019, loaded -0.095), and because the statics
  cannot fix the fraction, the pre-registered capture band is the FULL
  anchor-to-anchor range -- derived, not chosen.

Outputs derived_load_strut_trade.json (consumed by gait_scene.py).
"""
import json,math,sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))

from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.gait_scene import RECORD,DERIVED,build_walker_model,require
from tools.science_funnel.coupled_arm import Assembly

OUT=ROOT/'tools/science_funnel/validation/gait_zero_20260919/derived_load_strut_trade.json'
POSE_PATH=ROOT/'tools/science_funnel/validation/gait_zero_20260919/derived_entry_pose.json'
HEEL=np.array([-0.012,0.,0.]); HMP=np.array([0.074,0.,0.])            # hind sole locals
FHEEL=np.array([-0.012,-0.13555305347340657,0.]); FMP=np.array([0.074,-0.129953,0.])
FREF=0.5*(FHEEL+FMP)
RADIUS=0.004
T_CYCLE=0.71; DUTY=0.683; TICK=1.0/300.0; TOE_OFF=0.68
THETA_VAULT=0.2064            # |theta*(entry phase 0)| -- the vault-table reset lean
D_SURV=0.059                  # the measured survivable band (receipt_wave14)
D_LIVED=0.1744                # the strongest hind dangle that SURVIVED a settle
MU=0.6                        # the store's contact_friction (the equation's input)
# ── measured calibration inputs (the anchors; provenance in the emit) ──────
RUNTIME_DEFECTED_DANGLES={'left_heel':4.575e-2,'right_heel':4.557e-2}  # this lane's baseline
                                 # run, tick 0 ([pt] gaps) -- the DEFECTED assembly's state
SLIDE_ANCHOR={'left_pad_N':1.923,'right_pad_N':3.276,'slip_m_s':(0.796,0.786)}  # SLIDING, tick 0
PIN_ANCHOR={'left_pad_N':13.58,'right_pad_N':8.27,'slip_m':1.1e-3}              # PINNED (wave 14)
DELTA_LOADED={'left':-0.0980,'right':-0.0922}    # settle transfer under the lean's fore load
V_SETTLE=0.420440                                 # measured settle-exit speed prior (wave-13/14)
H_FOLD=0.081667                                   # shoulder-over-ref height at the LOADED capture
                                                  # (receipt_wave14; the fold's equilibrium)

graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
record=graph.get(RECORD)
contract=record['physical']['contract']
derived=json.loads(DERIVED.read_text(encoding='utf-8'))
PLANE=float(contract['contact_plane_height_m'])
GAP=float(contract['seating_scan']['reset_gap_target_m'])
POSE=json.loads(POSE_PATH.read_text(encoding='utf-8'))
require(POSE.get('schema')=='chimera.entry_pose.v1','trade_entry_pose_schema')
Q1F,Q2F=float(POSE['targets']['shoulder_rad']),float(POSE['targets']['elbow_rad'])

BASE_POINTS=[('left_heel','foot_left',HEEL),('left_mp_head','foot_left',HMP),
             ('right_heel','foot_right',HEEL),('right_mp_head','foot_right',HMP),
             ('fore_left_heel','forearm_fore_left',FHEEL),('fore_left_mp_head','forearm_fore_left',FMP),
             ('fore_right_heel','forearm_fore_right',FHEEL),('fore_right_mp_head','forearm_fore_right',FMP)]

def make_model():
    return build_walker_model(record,derived)

def entry_values(m,lean,right_phi):
    """The scene's TD-entry start values at a lean, with the RIGHT hind's
    assembly phase explicit: 1.0 for the DEFECTED assembly (the controller's
    literal tables_.at(1, ...), periodic to the TD column), 0.5 for the
    CORRECTED one (its clock column). Seated exactly as the scene seats."""
    tables=contract['tables_rad'];zeros=contract['zero_map_rad']
    def _table(t,phi):
        x=phi*20.0;k=min(19,int(x));f=x-k;return t[k]*(1.0-f)+t[k+1]*f
    jstems=['hip_flexion','knee_extension','ankle_dorsiflexion','MP_dorsiflexion']
    sv={}
    for leg,phi in (('left',0.0),('right',right_phi)):
        for stem,key in zip(jstems,('hip','knee','ankle','MP')):
            sv[f'{stem}_{leg}']=float(_table(tables[key],phi%1.0))+float(zeros[key])
    for b in ('base_rot_x','base_rot_y','base_rot_z','base_trans_x','base_trans_y','base_trans_z'):
        sv[b]=0.0
    sv['base_rot_z']=float(lean)
    asm=Assembly(m,values=sv,gravity=[0.,-9.80665,0.])
    raw={n:float(asm.point(b,list(p))[0][1]) for n,b,p in BASE_POINTS}
    sv['base_trans_y']=-min(raw.values())+GAP
    asm2=Assembly(m,values=sv,gravity=[0.,-9.80665,0.])
    gaps={};pos={}
    for n,b,p in BASE_POINTS:
        q,_=asm2.point(b,list(p));pos[n]=(float(q[0]),float(q[1]))
        gaps[n]=float(q[1])+RADIUS-PLANE
    com=np.zeros(3);mtot=0.
    for b in m['bodies']:
        if b.get('joint') is None:continue
        mss=float(b['mass_kg']);p,_=asm2.point(b['name'],b['mass_center_m'])
        com+=mss*np.asarray(p);mtot+=mss
    com/=mtot
    return sv,raw,gaps,pos,(float(com[0]),mtot*9.80665)

def state_at(m,lean,right_phi):
    sv,raw,gaps,pos,(comx,W)=state_at_raw=m and entry_values(m,lean,right_phi)
    lo=min(raw.values())
    d_td=raw['left_heel']-lo+GAP
    spread=max(raw.values())-lo
    x_fore=0.5*(pos['fore_left_heel'][0]+pos['fore_left_mp_head'][0])   # z-mirror: L==R
    x_h_l=0.5*(pos['left_heel'][0]+pos['left_mp_head'][0])
    x_h_r=0.5*(pos['right_heel'][0]+pos['right_mp_head'][0])
    return {'lean_rad':float(lean),'base_trans_y_m':float(sv['base_trans_y']),
            'd_td_heel_m':float(d_td),'all_paw_spread_m':float(spread),
            'gaps_m':gaps,'com_x_m':comx,'weight_N':W,
            'x_fore_line_m':x_fore,'x_hind_left_m':x_h_l,'x_hind_right_m':x_h_r}

def f_fore(st,x_hind):
    """THE LEVER LAW (named in the docstring): total fore reaction from the
    hind resultant; clamped to [0, W] (contacts push, never pull)."""
    W=st['weight_N']
    return W*min(1.0,max(0.0,(st['com_x_m']-x_hind)/(st['x_fore_line_m']-x_hind)))

def main():
    m=make_model()
    out={'schema':'chimera.load_strut_trade.v1'}
    # ── 0. N_PLANT: the equation and its measured inputs ────────────────────
    slide_total=SLIDE_ANCHOR['left_pad_N']+SLIDE_ANCHOR['right_pad_N']
    pin_total=PIN_ANCHOR['left_pad_N']+PIN_ANCHOR['right_pad_N']
    plant={'mu_store':MU,'equation':'pad pinned iff mu*N >= F_h; N_plant = F_h/mu with '
           'F_h the settle horizontal demand per pad; the two measured anchors bracket it',
           'slide_anchor':SLIDE_ANCHOR,'pin_anchor':PIN_ANCHOR,
           'F_h_bracket_per_pad_N':[MU*SLIDE_ANCHOR['right_pad_N'],MU*PIN_ANCHOR['left_pad_N']],
           'n_plant_pad_N':[SLIDE_ANCHOR['right_pad_N'],PIN_ANCHOR['left_pad_N']],
           'n_plant_total_N':[slide_total,pin_total],
           'falsifier_bound_total_N':slide_total,
           'pinned_marker_total_N':pin_total}
    out['fore_load_law']=plant
    # ── 1. BRANCH A: the trade on the DEFECTED assembly (right hind at 1.0) ─
    a={t:state_at(m,t,1.0) for t in (0.0,THETA_VAULT,-THETA_VAULT)}
    # model-validation gate: the Assembly IS the runtime reset state (the owed
    # defect's geometry) -- the tick-0 heel gaps of this lane's baseline run
    va_l=abs(a[0.0]['gaps_m']['left_heel']-RUNTIME_DEFECTED_DANGLES['left_heel'])
    va_r=abs(a[0.0]['gaps_m']['right_heel']-RUNTIME_DEFECTED_DANGLES['right_heel'])
    require(va_l<2e-3 and va_r<2e-3,'trade_branchA_runtime_gate',(va_l,va_r))
    # the defected hind line is DETERMINATE (both feet at the TD column)
    x_hind_def=0.5*(a[0.0]['x_hind_left_m']+a[0.0]['x_hind_right_m'])
    require(abs(a[0.0]['x_hind_left_m']-a[0.0]['x_hind_right_m'])<1e-9,
            'trade_branchA_hind_line_not_determinate')
    # the strut band re-derived on THIS assembly (three leans, the wave-15 law).
    # FINDING (measured, kept): the defected assembly's POSITIVE branch is not
    # the corrected one -- at nose-up the seat migrates to the hind TD column
    # (the wave-14 'whichever pair seats, the other dangles' structure), so the
    # zero-minimum property of D was a CORRECTED-assembly property. The trade's
    # band lives on the NEGATIVE side only (the vault reset lean is negative);
    # there the two assemblies agree (the left-heel-over-fore-seat geometry
    # dominates; the right column rides above the seat in both).
    d0,dn,dp=a[0.0]['d_td_heel_m'],a[-THETA_VAULT]['d_td_heel_m'],a[+THETA_VAULT]['d_td_heel_m']
    slope_neg=(dn-d0)/THETA_VAULT;slope_pos=(dp-d0)/THETA_VAULT
    require(slope_neg>0,'trade_branchA_band_side_not_ascending',slope_neg)
    theta_lo=-((D_SURV-d0)/slope_neg)
    require(theta_lo<0.0,'trade_branchA_band_empty',theta_lo)
    # THE TRADE: F_fore across the band (x_com(theta) linear through the three
    # leans -- the wave-15 three-point standing; the seat moves with the lean
    # and is inside the measurement)
    c0,cn=a[0.0]['com_x_m'],a[-THETA_VAULT]['com_x_m']
    com_slope=(cn-c0)/THETA_VAULT
    ff_edge=f_fore({'com_x_m':c0+com_slope*theta_lo,'weight_N':a[0.0]['weight_N'],
                    'x_fore_line_m':a[0.0]['x_fore_line_m']},x_hind_def)
    ff_level=f_fore(a[0.0],x_hind_def)
    com_margin_level=c0-x_hind_def
    branch_a={'d_td_law':{'level_m':d0,'leaned_m':dn,'nose_up_m':dp,
                          'slope_neg_rad_m':float(slope_neg),'slope_pos_rad_m':float(slope_pos),
                          'theta_band_min_rad':float(theta_lo),
                          'note':'positive branch non-ascending on the defected assembly '
                          '(the seat migrates to the hind TD column at nose-up); the band '
                          'is negative-side only'},
              'x_hind_line_m':x_hind_def,'x_fore_line_m':a[0.0]['x_fore_line_m'],
              'com_x_level_m':c0,'com_x_slope_rad_m':float(com_slope),
              'com_margin_level_m':float(com_margin_level),
              'f_fore_level_N':float(ff_level),'f_fore_band_edge_N':float(ff_edge),
              'runtime_gate_m':{'left_heel':va_l,'right_heel':va_r}}
    require(ff_edge<plant['falsifier_bound_total_N'],'trade_branchA_feasible',
            ff_edge,plant['falsifier_bound_total_N'])
    out['branch_a']=branch_a
    # ── 2. BRANCH B: the trade on the CORRECTED assembly (right hind at 0.5) ─
    b={t:state_at(m,t,0.5) for t in (0.0,THETA_VAULT,-THETA_VAULT)}
    d0b,b_nb,b_pb=b[0.0]['d_td_heel_m'],b[-THETA_VAULT]['d_td_heel_m'],b[+THETA_VAULT]['d_td_heel_m']
    slope_nb=(b_nb-d0b)/THETA_VAULT;slope_pb=(b_pb-d0b)/THETA_VAULT
    require(slope_nb>0 and slope_pb>0,'trade_branchB_not_minimal_at_zero',(slope_nb,slope_pb))
    theta_ee=0.0   # the DERIVED unique minimum of D (both slopes positive away) --
                   # the strut side binds first; re-checked against the load side below
    require(d0b<=D_SURV,'trade_branchB_level_breaches_band',d0b)
    require(b[0.0]['all_paw_spread_m']<=D_LIVED,'trade_branchB_spread_beats_survived',
            b[0.0]['all_paw_spread_m'])
    # the CoM margin at level: the corrected REAR contact is the right hind's
    # mid-stance foot (measure the min-x hind point, heel or MP)
    x_rear=min(b[0.0]['x_hind_right_m'],b[0.0]['x_hind_left_m'])
    # the load bracket at theta_e: the hind resultant lives between the right
    # (rear) and left (front) hind lines -- INDETERMINATE in statics, named
    ff_lo=f_fore(b[0.0],b[0.0]['x_hind_left_m'])
    ff_hi=f_fore(b[0.0],b[0.0]['x_hind_right_m'])
    ff_hi=max(ff_hi,f_fore(b[0.0],x_rear))
    com_margin_b=b[0.0]['com_x_m']-x_rear
    branch_b={'d_td_law':{'level_m':d0b,'leaned_m':b_nb,'nose_up_m':b_pb,
                          'slope_neg_rad_m':float(slope_nb),'slope_pos_rad_m':float(slope_pb),
                          'theta_band_min_rad':float(-((D_SURV-d0b)/slope_nb))},
              'theta_e_rad':theta_ee,'binding':'the strut law: theta_e=0 is the unique '
              'minimum of D with the band\'s full margin; the load side is statically '
              'INDETERMINATE (three sagittal contact lines) and cannot bind a theta -- '
              'the run\'s fore-load census is its test',
              'x_rear_contact_m':float(x_rear),'x_hind_left_m':b[0.0]['x_hind_left_m'],
              'x_hind_right_m':b[0.0]['x_hind_right_m'],
              'x_fore_line_m':b[0.0]['x_fore_line_m'],
              'com_x_level_m':b[0.0]['com_x_m'],'com_margin_level_m':float(com_margin_b),
              'f_fore_bracket_N':[float(ff_lo),float(ff_hi)],
              'gaps_m':b[0.0]['gaps_m'],'spread_level_m':b[0.0]['all_paw_spread_m']}
    out['branch_b']=branch_b
    # ── 3. THE LOAD-AWARE CAPTURE PREDICTION ────────────────────────────────
    sv0,_,_,pos0,_=entry_values(m,0.0,0.5)
    asm0=Assembly(m,values=sv0,gravity=[0.,-9.80665,0.])
    off={}
    for side in ('left','right'):
        sh=np.asarray(asm0.point(f'upperarm_fore_{side}',[0.,0.,0.])[0],dtype=float)
        paw=np.asarray(asm0.point(f'forearm_fore_{side}',list(FREF))[0],dtype=float)
        off[side]=float(paw[0]-sh[0])
    # delta_settle(f) = (1-f)*delta_unloaded + f*delta_loaded, f the load
    # fraction; f unmeasurable before the run -> the band is the FULL anchor
    # range (derived from the anchors, covering the load-dependence wave 15
    # measured: +0.019 unloaded vs -0.095 loaded)
    delta_unloaded={'left':0.139577-off['left'],'right':0.139987-off['right']}  # wave-15 measured
    cap={}
    for s in ('left','right'):
        lo=off[s]+DELTA_LOADED[s];hi=off[s]+delta_unloaded[s]
        cap[s]={'reset_offset_m':off[s],'delta_unloaded_m':float(delta_unloaded[s]),
                'delta_loaded_m':DELTA_LOADED[s],'band_m':[min(lo,hi),max(lo,hi)],
                'mid_m':0.5*(lo+hi)}
    mean_lo=0.5*(cap['left']['band_m'][0]+cap['right']['band_m'][0])
    mean_hi=0.5*(cap['left']['band_m'][1]+cap['right']['band_m'][1])
    out['capture_prediction']={'per_leg':cap,'mean_band_m':[mean_lo,mean_hi],
        'interpolation_law':'delta_settle linear in the fore load fraction between the '
        'two measured anchors; the fraction is statically indeterminate (branch B), so '
        'the pre-registered band is the full anchor range -- DERIVED, not chosen'}
    # ── 4. THE ENVELOPE at the capture band's WORST corner (the unloaded hold:
    #        arms extended, smallest amax) and the loaded anchor ─────────────
    dmax=0.125+float(np.hypot(FREF[0],FREF[1]))
    amax_load=math.sqrt(max(dmax*dmax-H_FOLD*H_FOLD,0.0))
    h_ext=abs(-0.176971-0.000003)  # the wave-15 measured extended-hold height (arm at 0.177)
    amax_ext=math.sqrt(max(dmax*dmax-h_ext*h_ext,0.0))
    Tf=T_CYCLE/TICK
    env={}
    for leg,phi_h in (('fore_right',0.5),('fore_left',0.0)):
        grid=(max(0.0,(DUTY-phi_h))*T_CYCLE+0.25*T_CYCLE)/TICK
        row={'grid_lift_wait_ticks':grid}
        for nm,amax,offp in (('loaded',amax_load,0.5*(cap['left']['band_m'][0]+cap['right']['band_m'][0])),
                             ('unloaded',amax_ext,0.5*(cap['left']['band_m'][1]+cap['right']['band_m'][1]))):
            tau_env=max(0.0,(amax+offp-V_SETTLE*TICK)/V_SETTLE)/TICK
            row[nm]={'amax_m':amax,'tau_env_ticks':tau_env,'lift_wait_ticks':min(grid,tau_env)}
        env[leg]=row
    out['envelope']={'amax_loaded_m':amax_load,'amax_extended_m':amax_ext,
                     'dmax_m':dmax,'per_leg':env,
                     'note':'the clock re-measures amax and the offset at the arm; '
                     'the bracket covers the capture band\'s two corners'}
    # ── 5. THE CORRECTED HIND CLOCK SCHEDULE (the repair's measurable face) ─
    hind={'release_phase':{'left':0.0,'right':0.5},'settle_total':60,
          'left_first_lift_tick':60+TOE_OFF*Tf,'left_first_lift_phase':TOE_OFF,
          'left_first_td_tick':60+1.0*Tf,
          'right_foot_airborne_at_release':b[0.0]['gaps_m']['right_heel'],
          'right_first_td_tick':60+0.5*Tf,'right_first_td_note':'the right foot enters '
          'AIRBORNE at its 0.5 clock column (mid-stance geometry, dangle above); the '
          'stance columns keep it clear until its swing completes at phi=1.0==0 -- its '
          'first TOUCHDOWN is the clock\'s own TD event',
          'right_second_lift_tick':60+0.5*Tf+TOE_OFF*Tf,'right_second_lift_phase':TOE_OFF,
          'law':'phi_leg=(t/T+off) mod 1, off={0,0.5} (the doc\'s 5.1); TOE_OFF=0.68'}
    out['hind_clock_schedule']=hind
    # ── 6. THE HAND-OFF (unchanged law, re-emitted) ─────────────────────────
    out['handoff']={'law':'amp(t)=clamp((t-t_capture)/T_cycle,0,1); target_post=amp*theta*(phi); '
                    'v2 init = 0','blend_ticks':Tf,'trunk_handoff_ticks':Tf}
    # ── 7. THE LEG-GEOMETRY LAWS (re-measured, unchanged by the trade) ──────
    tables=contract['tables_rad'];zeros=contract['zero_map_rad']
    seg=derived['body_model']['segments_Table1']
    _L1=float(seg['thigh']['length_m']);_L2=float(seg['shank']['length_m'])
    _XM=0.074;_XH=-0.012
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
    vy=(_contact_xy(cd)[1]-_contact_xy(-cd)[1])/(2*cd)/T_CYCLE
    vx=(_contact_xy(cd)[0]-_contact_xy(-cd)[0])/(2*cd)/T_CYCLE
    require(vy<=0.0,'trade_settling_contact',vy)
    out['leg_geometry_laws']={'contact_vy_m_s':float(vy),'no_skid_speed_m_s':float(-vx)}
    # ── 8. emit ─────────────────────────────────────────────────────────────
    out['provenance']={'script':'tools/science_funnel/validation/gait_zero_20260919/derive_load_strut_trade.py',
        'law':'fore_reaction(theta)=W*clamp((x_com(theta)-x_hind)/(x_fore-x_hind),0,1); '
              'N_plant=F_h/mu bracketed by the measured sliding/pinned anchors; branch A '
              '(defected assembly, right hind at the 1.0==0.0 column) is infeasible by '
              'derivation; branch B re-derives on the corrected assembly (right hind at '
              'its 0.5 clock column)',
        'measured':{'runtime_defected_dangles_m':RUNTIME_DEFECTED_DANGLES,
                    'delta_settle_loaded_m':DELTA_LOADED,
                    'v_settle_prior_m_s':V_SETTLE,'H_FOLD_m':H_FOLD,
                    'D_SURV_m':D_SURV,'D_LIVED_m':D_LIVED}}
    out['entry_state']={'entry_trunk_rad':float(theta_ee),'start_phase_left':0.0,
                        'start_phase_right':0.5,
                        'note':'theta_e pinned by the strut law (the corrected assembly '
                        're-derivation: the unique D-minimum with the band\'s full '
                        'margin); the load side is statically indeterminate and cannot '
                        'bind a theta -- the run\'s fore-load census is its test'}
    OUT.write_text(json.dumps(out,indent=1),encoding='utf-8')
    print(json.dumps({'branch_A':{'com_margin_level_m':com_margin_level,
                                  'f_fore_level_N':ff_level,'f_fore_band_edge_N':ff_edge,
                                  'band_min_rad':theta_lo,'runtime_gate_m':[va_l,va_r]},
                      'branch_B':{'d_td_level_m':d0b,'band_min_rad':-((D_SURV-d0b)/slope_nb),
                                  'x_rear_m':x_rear,'com_margin_level_m':com_margin_b,
                                  'f_fore_bracket_N':[ff_lo,ff_hi],
                                  'spread_level_m':b[0.0]['all_paw_spread_m']},
                      'n_plant_total_N':plant['n_plant_total_N'],
                      'capture_mean_band_m':[mean_lo,mean_hi],
                      'right_first_td_tick':hind['right_first_td_tick'],
                      'right_second_lift_tick':hind['right_second_lift_tick']}))
if __name__=='__main__':main()
