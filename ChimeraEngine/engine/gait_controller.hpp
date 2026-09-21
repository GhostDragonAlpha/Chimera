#pragma once
#include "coupled_articulation.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <memory>
namespace chimera::multibody {
// Gait controller + walker runtime (docs/research/20260918_gait_controller_derivation.md,
// Rule-0 admission work.creature.gait_controller). The CONTROL LAW is exactly
// the derivation's four pieces: (1) a contact-reset hybrid phase clock
// (T = 0.71 s, per-leg offset {0, 0.5}, reset at the solver's own kTouch
// crossing -- never a clock guess, Section 5.1/5.3); (2) the 21-node phase
// target tables in the Oku sign convention (Section 2.4, left leg = right at
// phi+0.5); (3) the qualified mass-normalized PD at the DERIVED f_s = 4.0 Hz
// (0.95 amplitude-ratio criterion at the 1.408 Hz gait fundamental, zeta 0.8
// qualified; the arm servo's 2.0 Hz is falsified, Section 5.2) with caps at
// 1.25x the measured |tau_peak| (Section 4.3); (4) per-drive actuator stores
// at the derived floor 1.5x W+_d (Section 4.4, depletive -- braking recharges
// nothing) and the support-hull monitor with the derived capture-step reflex
// (Section 5.4: CoM projection exits the hull moving outward -> swing leg
// phase jumps to 0.95, an early touchdown).
//
// The RUNTIME carries the gait walker assembly (floating base + 4 hindlimb
// drives per leg through the UNCHANGED Model::evaluate -- the stage-D hindlimb
// lift). It consumes the controller's tau through the SAME advance(h, tau)
// input signature the qualified n-coordinate and free-root solvers use, and
// re-uses their laws verbatim: kTouch/kSlip band and velocity gate, RK4 at
// dt/4, 42-step event bisection, mass-metric active-set row projection with
// the Gram-dependent drop, per-point discrete-cone Coulomb friction, impact
// heat ledger. The qualified 2-coordinate class (coupled_dynamics.hpp) keeps
// its exact bytes; coupled_multidynamics.hpp / free_root_dynamics.hpp are not
// modified -- this header only adds a sibling runtime for the gait scene.
class GaitWalker {
 static constexpr double kTouch=1e-5,kSlip=1e-9;
 // THE TOUCH LAW (wave 22, receipt_wave22.json): the clock's contact state
 // releases only when the leg's pair-min gap clears the band by more than
 // kReleaseBand -- the contact solver's OWN gap quantum, already in this
 // machinery (the positional-correction penetration band -1e-6, the paw-band
 // penetration bound -1e-6). MEASURED SEPARATION (the byte-exact baseline,
 // mined per tick): a genuine touchdown arrives from departure depths of
 // 6.5e-2/1.17e-1 m and closes 1.21e-3/1.95e-3 m in its FINAL tick (1200-
 // 1950x the quantum; a free foot crosses it in under 1% of a tick -- gravity
 // alone moves g*dt^2 = 1.09e-4 m per tick, 109x); the wave-21 band-edge
 // graze (the touch-reset slam's arming event) excursed 1.6e-7 m above the
 // band for ONE tick at 4.8e-5 m/s separation -- 6.25x BELOW the quantum and
 // below the solver's own plane-engagement velocity gate (>= 1e-3 m/s scale):
 // by the machinery's own contact definition that foot NEVER left. A touch
 // event that resets a stance clock must be a TOUCHDOWN, not a band-edge
 // graze. No free constant: the quantum is the solver's existing one.
 static constexpr double kReleaseBand=1e-6;
 static constexpr size_t NB=6,NLEG=4;
 public:
 struct Drive {std::string name,leg,joint;size_t coordinate;double cap,store_floor,damping;};
 struct ContactPoint {std::string name,body;size_t index;V local;double radius;};
 // ── the 21-node target tables (derivation Section 2.4, rad, Oku convention) ──
 static constexpr double T_CYCLE=0.71,DUTY_SAMPLED=0.683,TOE_OFF=0.68;
 static constexpr double FS_HZ=4.0,ZETA=0.8,CAPTURE_PHI=0.95;
 struct Tables {
  double hip[21]={0.809,0.835,0.825,0.751,0.651,0.525,0.412,0.297,0.128,0.043,-0.027,-0.065,-0.139,-0.146,-0.042,0.167,0.442,0.767,0.887,0.885,0.807};
  double knee[21]={-0.472,-0.670,-0.852,-0.948,-0.973,-0.959,-0.946,-0.890,-0.826,-0.849,-0.860,-0.872,-0.847,-0.922,-1.045,-1.174,-1.201,-1.084,-0.865,-0.633,-0.470};
  double ankle[21]={0.928,1.232,1.383,1.440,1.447,1.465,1.460,1.487,1.499,1.433,1.354,1.153,0.910,0.846,0.852,0.969,1.253,1.303,1.225,1.071,0.927};
  double mp[21]={0.558,0.338,0.368,0.497,0.651,0.741,0.827,0.856,0.914,1.046,1.140,1.319,1.295,0.865,-0.025,-0.114,-0.142,-0.092,-0.035,0.134,0.559};
  // The four Oku angle zeros (model.dynamics.gait_walker revision 2, derived
  // by kinematic closure -- tools/science_funnel/validation/gait_zero_20260919).
  // Scene target q_j = zero_j + table_j: without them the composed TD foot
  // pitches nose-up 72.5 deg (heel digging); with them +15.9 deg heel-first
  // and the stance rolling contact rides 5.8 mm.
  double zeros[4]={0.,0.,0.,0.};
  // The trunk-vault table (wave 8, tools/science_funnel/validation/
  // gait_zero_20260919/trunk_vault.json, derived by derive_trunk_vault.py on
  // the wave-4 statics + the base-rot DOF + the sole CoP envelope): the
  // posture target theta*(phi) that centers the stance leg's demands inside
  // their caps (min-max demand/cap ratio 0.881 <= 1 at every single-support
  // node). HAT-FORWARD-POSITIVE, 0.5-periodic (left/right symmetry). Applied
  // exactly like the leg tables: the scene maps it through the same sign
  // probe as every other table; absent (legacy scenes) it stays all-zero and
  // the posture drive pins the trunk to 0 -- byte-identical legacy behavior.
  double trunk_vault[21]={0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.};
  static double interp(const double* t,double phi){phi-=std::floor(phi);double x=phi*20.;int k=(int)x;if(k>=20)k=19;double f=x-k;return t[k]*(1.-f)+t[k+1]*f;}
  void at(double phi,double out[4])const{out[0]=interp(hip,phi)+zeros[0];out[1]=interp(knee,phi)+zeros[1];out[2]=interp(ankle,phi)+zeros[2];out[3]=interp(mp,phi)+zeros[3];}
  double trunk_target(double phi)const{return interp(trunk_vault,phi);}
 };
 private:
 struct State {Dense q,v,work,impulse;double external=0,damping=0,impact=0,constraint_work=0;std::vector<double> contact_impact,contact_impact_impulse,contact_force_impulse,friction_heat,friction_heat_tick,friction_impulse,friction_force_impulse;Dense contact_generalized;
  State()=default;
  State(size_t n,size_t pts):q(n,0.),v(n,0.),work(n,0.),impulse(n,0.),contact_impact(pts,0.),contact_impact_impulse(pts,0.),contact_force_impulse(pts,0.),friction_heat(pts,0.),friction_heat_tick(pts,0.),friction_impulse(pts,0.),friction_force_impulse(pts,0.),contact_generalized(n,0.){}};
 struct Rate {Dense q,v,reaction;double damping=0;std::vector<double> contact_lambda,friction_lambda,friction_heat,slip;std::vector<int> mode;std::vector<Dense> point_force;
  Rate(size_t n,size_t pts):q(n,0.),v(n,0.),reaction(n,0.),contact_lambda(pts,0.),friction_lambda(pts,0.),friction_heat(pts,0.),slip(pts,0.),mode(pts,0),point_force(pts){}};
 struct NamedRow {Dense row;double floor;int point;bool stop_row;};
 struct BodyRef {double mass;V com;Mat inertia;};
 std::shared_ptr<const Model> model_;J recipe_,config_,model_data_;std::vector<ContactPoint> points_;std::vector<Drive> drives_;size_t n_=0,npts_=0,nd_=0;
 V shift_,gravity_;double dt_=0,plane_world_y_=0,plane_model_y_=0,mu_=0,mtot_=0,store_total_=0;
 Tables tables_{};double phi_[2]={0.,0.5};bool touching_prev_[2]={false,false};uint64_t ticks_=0;uint64_t capture_events_=0;
 Dense kp_,kd_,damping_,last_torque_,battery_,brake_;std::vector<uint64_t> empty_events_;
 double kp_post_=0,kd_post_=0,battery_post_=0,brake_post_=0,store_post_=0;uint64_t empty_post_=0;
 std::vector<double> posture_phi_,posture_theta_; // legacy non-periodic posture table (retained for receipt compatibility, not consumed)
 int settle_ticks_=0; // ORBIT CAPTURE (wave 8): hold the clock at the entry pose under load for the servo's settling time
 int settle_total_=0; // immutable reset value used by the wave-10 gradual vault activation
 double e_ref_=0; // the LEDGER BASELINE: the reset state's actual mechanical energy (the gait entry injects pose+momentum the standing-pose reference never sees; measured offset -0.59 J at tick 0 before this)
 // ── THE ENTRY POSE (wave 14): the pre-capture fore targets, consumed from ──
 // the scene recipe ('fore_entry_pose_rad', derived by the scene-statics
 // derivation derive_entry_pose.py). The wave-12/13 constants (-0.903/0.838)
 // are the legacy default: absent recipe key -> byte-identical legacy behavior
 // (the zero_map/trunk_vault pattern). The pose lives at THREE sites (the
 // reset initial state, the pre-capture servo target, the status fallback) --
 // a scene-only change cannot install it, which is why the controller
 // consumes it (receipt_wave14, controller_change_justification).
 double fore_pose_sh_=-0.903,fore_pose_el_=0.838;
 // ── THE TRUNK-POSTURE ACTIVATION (the wave-10 gradual vault activation; the
 // WAVE-15 LEVEL-ENTRY hand-off when the scene authors recipe
 // 'trunk_handoff_ticks', derived by derive_level_entry.py): the wave-10 ramp
 // reaches FULL theta*(entry phase) AT the settle capture -- that endpoint IS
 // the leaned capture the wave-15 strut bound forbids (the fore MP pokes
 // sin(|theta*|) deeper each tick, regrowing the wave-14 storm inside the
 // settle). The level entry therefore holds the posture target at 0 through
 // the settle (trunk LEVEL at the capture) and blends linearly onto
 // theta*(phi) over the FIRST cycle: amp(t)=clamp((t-t_capture)/T_cycle,0,1)
 // -- the wave-10 gradualness preserved, parameter-free, full table from the
 // second cycle. Absent key -> the legacy wave-10 ramp bytes exactly (the
 // zero_map/trunk_vault/fore_entry_pose pattern).
 double post_amp()const{
  if(!config_["gait_enabled"].get<bool>())return 0.;
  if(recipe_.contains("trunk_handoff_ticks")){
   double since=double(ticks_)-double(settle_total_);
   return since<=0.?0.:(std::min)(1.,since/number(recipe_["trunk_handoff_ticks"]));}
  return settle_total_>0?1.-double(settle_ticks_)/double(settle_total_):1.;}
 // ── THE PLANTED-STRUT CLOSURE (wave 12): forelimb paw IK ──
 // The fore struts no longer hold FIXED shoulder/elbow angles (the wave-11
 // refusal cause: through the first gait transition the fixed-angle paws
 // lift, the front sags, the hind poscorr budget exhausts). Each forelimb is
 // a planar 2-DOF chain; the controller solves the CLOSED-FORM law-of-cosines
 // IK for the joint targets that hold the paw reference (the heel/MP midpoint)
 // at its PLANTED WORLD POSITION, captured at the end of the settle window.
 bool paws_captured_=false; // armed at the END of the settle window
 V paw_target_[2]={V{},V{}}; // the planted paw world (model-frame) position per fore leg
 int ik_branch_[2]={-1,-1}; // the law-of-cosines branch matching the planted configuration
 size_t fore_coord_[2][2]{{0,0},{0,0}}; // [leg][0]=shoulder, [leg][1]=elbow coordinate rows
 size_t fore_mount_body_[2]={0,0}; // pelvis body row (the shoulder's parent)
 V fore_mount_local_[2]={V{},V{}}; // shoulder mount point in the pelvis frame
 size_t fore_paw_point_[2]={0,0}; // contact index of the leg's heel (names the forearm body)
 V paw_ref_local_[2]={V{},V{}}; // paw reference = heel/MP midpoint, forearm frame
 double fore_L1_=0,fore_rho_=0,fore_beta_=0; // the 2-DOF chain constants (humerus length; paw-polar)
 double ik_roundtrip_m_[2]={0,0}; // |FK(IK(target)) - target| measured at capture (the closure check)
 double ik_qerr_[2]={0,0}; // |IK solution - actual q| at capture (the closure check)
 uint64_t ik_sat_ticks_[2]={0,0}; // ticks the plant sat outside the chain's reachable annulus
 mutable bool ik_sat_prev_[2]={false,false}; // trace-only rising-edge flag
 // ── THE STEPPING-STRUT FORE CLOCK (wave 13) ──
 // Wave 12's membrane is banked: NO fixed world plant survives a translating
 // body (the shoulder-paw distance hit the 0.261324 m annulus at ticks 114/122;
 // 176/291 ticks saturated; the walk refused at 291). Each forelimb now
 // alternates STANCE (the wave-12 exact hold of its captured world spot) and
 // SWING (the IK target glides world-linearly to the law's plant point,
 // airborne under a pad-geometry clearance arch). THE REPLANT LAW
 // (receipt_wave13.json derivation; no free parameters):
 //   x_off = v * t_stance/2,  t_stance = DUTY_SAMPLED*T_CYCLE,
 // with v the pelvis x-speed read at the liftoff tick -- the symmetric-reach
 // (minimax) plant: equal margins at both stance ends. Fore period = hind
 // period, fore duty = the hind sampled duty (the reach closure passes at the
 // measured 0.391 m/s cruise with 2.7x margin, so no shortening is derived).
 // Phase relation: lateral-sequence lags (LF = LH + T/4, RF = RH + T/4); the
 // entry geometry cannot originate that grid, so each leg's SECOND cycle is
 // stretched/shrunk ONCE (stance2 = next_slot - TD1 - t_swing) to land it --
 // pure clock thereafter. TD re-captures the ACTUAL paw (horizontal) at the
 // leg's captured settle height (vertical): the wave-12-verified heel-grazing
 // geometry; the capture residual is absorbed by the reach margin, never
 // accumulated (each plant is fresh, x_off ahead).
 double fore_t_[2]={0.,0.};      // ticks since the leg's last TD (or arm)
 double fore_stance_[2]={0.,0.}; // stance length in ticks (entry tau1 / convergence / nominal)
 double fore_cycle_[2]={0.,0.};  // TD-to-TD length in ticks
 int fore_mode_[2]={0,0};        // 0 stance, 1 swing
 int fore_td_[2]={0,0};          // TDs since armed
 V swing_from_[2]={V{},V{}};     // world glide start (actual paw at liftoff)
 V swing_to_[2]={V{},V{}};       // world glide end (the law's plant point)
 double paw_plant_y_[2]={0.,0.}; // per-leg plant height (captured settle ref height)
 uint64_t fore_replants_[2]={0,0}; // TD re-captures
 uint64_t fore_clamped_[2]={0,0}; // liftoffs where the law's x_off hit the annulus at the current height
 int fore_conv_[2]={0,0}; // the leg's TD schedule is on its lateral slot (pure clock)
 // ── THE MID-ENTRY RE-PLANT (wave 20, receipt_wave20.json) ──
 // A BEHIND capture at the measured settle-exit speed 0.607 m/s cuts the entry
 // stances to the envelope's 8.9/11.1 ticks; the committed law then lifts BOTH
 // fores within 3 ticks into full-reach 95.04-tick glides and the wave-13 run-2
 // double-swing starves the front (the wave-19 refusal at 82). The entry clock
 // law changes to the DERIVED RE-PLANT POINT: hold to tau1 = max(0,
 // tau_env - (t_air + g)), then step forward with the machinery's OWN nominal
 // step air time under the NO-DOUBLE-SWING GATE, re-planting at the symmetric
 // +x_off target; the TD re-captures the ACTUAL paw and re-arms from the fresh
 // envelope. fore_entry_ marks the regime per leg (cleared at the first TD at
 // or ahead of the shoulder, where the committed grid convergence is lawful);
 // fore_gate_holds_ counts the gate-held liftoff ticks (the census).
 int fore_entry_[2]={0,0};
 uint64_t fore_gate_holds_[2]={0,0};
 // ── THE JOINT-ADMISIBLE HOLD (wave 23, receipt_wave23.json) ──
 // The law machinery sits after fore_ik's definition (it reuses ForeIK);
 // this block holds only its state: the censuses and the pin counter.
 // wall_pins_ counts the advance-loop's stop pins per drive, split
 // LOADED/AIRBORNE (the deadlock needs the contact over-constraint; the
 // wave-22 baseline also carried ONE airborne pin on the R shoulder's swing
 // transit -- the witness), mutable exactly like adv_calls_ (advance is
 // const; integer increments, never a floating-point byte of the dynamics).
 uint64_t fore_wall_bound_[2]={0,0};
 uint64_t fore_wall_follows_[2]={0,0};
 bool fore_td_plant_[2]={true,true}; // the leg's last plant opened a window (a TD); the gate's clause (b) scope
 mutable uint64_t wall_pins_[12]={0,0,0,0,0,0,0,0,0,0,0,0};
 mutable uint64_t wall_pins_air_[12]={0,0,0,0,0,0,0,0,0,0,0,0};
 // ── THE POCKET-CLEAR HOLD (wave 24, receipt_wave24.json) ──
 // The glide's joint-admissible presentation state: at a wall-bound lift
 // whose line-march finds joint-range-exiting ticks (the POCKET: the map
 // measured ALL nine line points of the wave-23 death glide outside the
 // scene's own joint ranges, on BOTH IK branches, at every height above
 // the plane), the glide holds the BODY-LOCKED LIFTED FOLLOW SEAT through
 // those ticks and resumes the standard line+arch at the release. The
 // body-lock keeps the held target's annulus D at its liftoff value (the
 // world-park variant recedes into the annulus wall within 2 ticks -- the
 // reach census); the lift clears the pad band (the v8 lesson inverted:
 // the hold that CLEARS, not the hold that hugs).
 int fore_glide_hold_[2]={0,0};
 int fore_hold_last_[2]={0,0};
 V fore_hold_off_[2]={V{},V{}}; // follow seat minus shoulder at the lift (world)
 // ── THE WALL-ADJACENT WAIT OVERRIDE (wave 26, receipt_wave26.json) ──
 // THE ACTUAL-SIDE MECHANISM FOR THE LAWFUL WAIT: at a gate-held liftoff-due
 // stance tick whose ACTUAL headroom crossed the derived floor, the gate
 // yields and the leg takes its lift now -- wall_bound arms the pocket-clear
 // hold, whose measured face is the ACTUAL healing WITH PADS LIVE (the L's
 // [73,82] heal 0.037575 -> 0.052603 on the wave-25 law-free baseline).
 // fore_wait_fires_ is the census counter (integer increments only, exactly
 // like adv_calls_/wall_pins_: never a floating-point byte of the dynamics).
 uint64_t fore_wait_fires_[2]={0,0};
 // ── THE HIND EXTENSION LAW (wave 27, receipt_wave27.json) ──
 // THE SINKING SHOULDER, OWNED. THE MEASURED COMPOSITION (the per-tick trace
 // of the byte-reproduced wave-26 baseline): the shoulder sink -71.2 mm over
 // [60,104] = the BASE drop -78.4 mm (110%) + the pitch coupling +7.2 mm
 // (-10%); the drop is the HIND STANCE EQUILIBRIUM FOLD (the L knee ACTUAL
 // folds 37.9 deg, its drive at 56% of cap with a 0.7917 rad deficit -- the
 // wave-23 deflection physics: error = tau_load/kp growing with the recede
 // lever), NOT the designed tables (2.60 mm of the 78.4 mm). The trunk pitch
 // -- the load-shift dial -- is MEASURED RAILING at its cap (11.213 =
 // drives_[0].cap exactly): no posture authority remains, hence the
 // feed-forward below and not a table amendment. THE LAW: at a derived
 // height emergency the pads-live hind drives take ff = last_torque/kp
 // (the wave-23 equilibrium identity: at equilibrium kp*(tgt+ff-actual) =
 // tau_load gives actual = tgt -- the DESIGNED pose, where the wave-8 load
 // book closes at 0.881 <= 1). A FEED-FORWARD, NOT A GAIN CHANGE: gains are
 // law. THE EMERGENCY CONSTANTS (derive_height_hold.py, validated
 // bit-for-bit against this lane's baseline): kSinkRateMax is the MAX
 // measured per-tick sh_min sink [61,104] (0.002349 m/tick at [103,104] --
 // the wave-26 kDiveRateMax mining pattern); the CRIT key (the scene's
 // 'hind_height_hold_crit_m', authored from derived_height_hold.json) is
 // h_crit = 0.055939 m -- the shoulder-min height at the first
 // stance-target admissibility death, reproduced by the F-G23(b) census's
 // own formula (march L@104, R@98: EXACTLY the measured first_viol); the
 // FLOOR is the wave-26 kWaitFloor turnaround shape in the qualified
 // servo's own envelope: kHeightFloor = 2*kSinkRateMax +
 // kSinkRateMax*tau_settle, tau_settle = 1/(ZETA*2*pi*FS_HZ) = 14.92 ticks
 // -- the error envelope e^(-zeta*omega_n*t) of the qualified PD the
 // derivation itself qualified (zero new free numbers): one full sink-tick
 // of pre-fire integration, one of standing margin, plus the envelope's
 // stop distance at the WORST measured rate (the constant worst-rate form:
 // the conservative early fire; the scene's floor key is cross-checked
 // against this controller expression at construction). THE SCOPE: the ff
 // applies to the pads-live hind drives only (touching_prev_: the legs that
 // bear the ride; a leg whose pads leave, swings, and resumes at the next
 // TD); consumed only when the recipe keys are present (absent ->
 // byte-identical legacy, the zero_map/trunk_vault/fore_entry_pose
 // pattern).
 static constexpr double kSinkRateMax=0.002349;
 bool hind_height_hold_armed_=false;   // the recipe keys present (constructor)
 bool hind_height_hold_latched_=false; // the emergency, once declared, holds
 double hind_height_crit_=0;           // h_crit (the scene key)
 double hind_height_floor_=0;          // kHeightFloor (the controller expression)
 uint64_t hind_height_fire_tick_=0;    // the fire's census record
 double hind_height_fire_margin_=0;    // the margin at the fire
 uint64_t hind_height_fires_=0;        // the census counter (integer increments)
 // ── THE HIND STEP LAW (wave 28, receipt_wave28.json) ──
 // THE ARREST'S GROUND PATH, OWNED. The wave-27 ff holds the vertical ride,
 // but the body's advance (v ~ 0.63-0.74 m/s) outruns the hind schedule: the
 // hind clock's first lift slots land at ~98 (R) / ~204 (L), and the R's slot
 // FIRED INTO A STALL on the reproduced baseline -- at phi >= TOE_OFF the
 // pads are still LIVE and LOADED (gap 2.4e-6, rxn 62.2 N at t=98): the
 // designed hind lift is kinematic only (the swing-column targets), and a
 // 60 N ride cannot be lifted by target motion. The swing columns pull the
 // joints against the planted paw: the ankle actual is driven ONTO ITS WALL
 // (the mined headroom 0.0032 rad at tick 120; the dive 0.053 rad/tick, 13x
 // the fore's 0.0039 class), the paw creeps past its designed stance end and
 // SKIDS (1.2455 m/s at 121, rxn 17.4 N, inside the cone), and the contact
 // event tree exhausts the budget at 122. THE LAW: when the clock's OWN lift
 // slot arrives (phi >= TOE_OFF -- the trigger is the clock's own constant,
 // derived by measurement among five candidates: the absolute stance-end
 // envelope never fires (the R's offset bottoms 1.7 mm short -- the skid
 // starts first); the actual-vs-own-column recede misfires on the L (its paw
 // rides 5.2 cm behind its column from the entry geometry); the raw slip
 // bound v_bound misfires on the DESIGNED residual (the R's settle face
 // sustains > 0.2089 m/s for ~35 ticks [55,90] admissibly); the CoM hull
 // face is a continuous regime from 84 with no derivable threshold; the
 // ankle wall is the death's ENDPOINT (0-1 tick of warning at its dive)) --
 // and the pads are STILL LIVE (the lift stalled), the leg STEPS: the
 // wave-20 minimal-air-time pattern, hind side -- the paw target glides
 // world-linearly from the liftoff spot to the symmetric offset ahead of the
 // hip at the current v (xoff = v*DUTY_SAMPLED*T_CYCLE/2, the fore law's own
 // form) under the 2*pad-radius clearance arch for the machinery's OWN
 // nominal air time t_air = ceil((T_CYCLE-DUTY_SAMPLED)/dt) = 9 ticks,
 // tracked by a closed-form 2-link IK on the hind chain (the held foot pitch
 // and MP preserve the paw's presentation; the branch captured at the fire),
 // with the xoff clamped to the chain's own reach annulus at the plant
 // height (counted, never silent). At the TD the leg returns to the tables
 // and the TOUCH RESET -- the machinery's own wave-22 law -- re-syncs the
 // clock to the TRUE stance (phi := 0), repairing the entry's clock skew
 // that scheduled the R's slot 43 ticks ahead of its real stance. THE
 // STAGGER: the no-double-step gate, the wave-20 clauses hind-side -- the
 // other hind not in step, its true-TD recency >= the hand-off clearance
 // g=1 tick, and THE SUPPORT FLOOR: the other three legs carry >= 2 live
 // pads at the fire (support >= 2 through every hind swing, the wave-25
 // clause hind-side). THE HEIGHT-LAW ORDERING (the composition derivation):
 // the step is REGIME-GATED to the height emergency (latched only -- pre-
 // latch the designed ride owns the walk, the [0,65] fence's proof); the
 // ff's own pads-live gate auto-releases the stepping leg (its equilibrium
 // identity needs a loaded pad), the stance leg keeps the ff UNCHANGED --
 // the laws compose leg-disjointly; the glide targets REPLACE the whole
 // hind target branch for the stepping leg, so the swing columns' pull --
 // the death's actuator -- is structurally removed during the step; at the
 // TD the ff re-engages and holds the re-synced TD column through the
 // qualified envelope (tau_settle). NO NEW CONSTANTS: the slot is TOE_OFF,
 // the air time the fore machinery's own, the plant offset the fore law's
 // own form, the arch the pad geometry, the reach the model's own segment
 // bytes (harvested below, require-guarded). The scene bytes: UNTOUCHED.
 int hind_step_mode_[2]={0,0};         // 0 stance (tables+ff), 1 step glide
 double hind_step_t_[2]={0.,0.};       // ticks since the fire
 V hind_step_from_[2]={V{},V{}};       // the liftoff paw spot (world)
 V hind_step_to_[2]={V{},V{}};         // the plant point (world)
 double hind_step_plant_y_[2]={0.,0.}; // the liftoff paw height
 double hind_step_ap_[2]={0.,0.};      // the held composed foot pitch
 double hind_step_mp_[2]={0.,0.};      // the held MP actual
 int hind_step_branch_[2]={-1,-1};     // the knee branch captured at the fire
 double hind_step_xoff_[2]={0.,0.};    // the plant offset used
 double hind_step_qerr_[2]={0.,0.};    // the fire-time IK self-check
 uint64_t hind_step_fires_[2]={0,0};
 uint64_t hind_step_tds_[2]={0,0};
 uint64_t hind_step_gated_[2]={0,0};
 uint64_t hind_step_clamped_[2]={0,0};
 uint64_t hind_step_last_fire_[2]={0,0};
 uint64_t hind_step_last_td_[2]={0,0};
 // ── THE HIND ALTERNATION LAW (wave 29, receipt_wave29.json) ──
 // THE SECOND HIND STEPS BEFORE THE FIRST'S STANCE EXHAUSTS. THE MEASURED
 // DEATH (the wave-28 run, re-mined on this lane's byte-reproduced baseline):
 // the R's replant (TD 107) concentrated the ride on the L hind, whose knee
 // was already at its wave-27 cap; the L's standing ride ran [107,152): the
 // mined load-share series peaks 82.8 N at 120, decays to zero at 151, and
 // the touch law's OWN release classification flips at the status 152 (the
 // tick-start pair-min gap 1.184e-4 > kTouch+kReleaseBand) -- the forced
 // liftoff at clock phase 0.4319, NOT a slot phase: the fold class. The body
 // slid one-legged into the [226,298] collapse. THE BUDGET: concentration
 // (the other's TD) to forced liftoff = 45 ticks of standing ride -- THE
 // MINED DEATH ENVELOPE, the kSinkRateMax precedent (the controller owns its
 // mined death constants; zero free numbers). The KINEMATIC envelope is NOT
 // the owner (measured): the fore_env_ticks form mirrored hind-side reads
 // 143 ticks at 107 -- the fold is CAP-LIMITED DYNAMICS, not reach
 // exhaustion; hence the budget is MINED, not geometric. THE NATURAL SLOT
 // CANNOT OWN THE SECOND STEP (measured): the L's slot read ~204, outside
 // the budget. THE LAW: at a live CONCENTRATION (the other hind's last fire
 // younger than this leg's last step-TD) whose natural slot lies beyond the
 // deadline arithmetic (the other's TD + kFoldBudgetTicks - tair - g, the
 // wave-20 tau1 form hind-side), the standing hind steps at the EARLIEST
 // LAWFUL SLOT -- the wave-28 gate's clauses PLUS THE KICK-STAND PROMISE
 // (new clause (d)): when the floor at the fire is exactly the pair (the
 // standing hind + one fore), that fore must promise its pads through the
 // glide -- its own fore clock covering tair from stance, or its held-glide
 // span covering tair (the wave-24/25 measured face). A floor of 3+ needs
 // no promise (the R's 98 fire ran support min 3: byte-preserved calendar).
 // At the deadline, clauses (c)/(d) YIELD to the fold's precedence -- (a)/(b)
 // NEVER (the no-double-step structure); the override counted, predicted
 // inert (the gate opens ~124, 18 ticks before 142 on the mined walk).
 // THE LIFT-FIRST GLIDE (the wave-28 bank's amendment, hind-side): while the
 // stepping leg's pads remain inside the release band, the glide target
 // HOLDS AT THE LIFTOFT SPOT + THE FULL ARCH (a static vertical demand: no
 // haul, no drag BY CONSTRUCTION, full servo authority into the lift); the
 // hold releases when the leg's pair-min gap clears the touch law's OWN
 // release quantum kTouch+kReleaseBand (checked at the tick-start), then the
 // standard line+arch resumes at the current glide phase (the clock never
 // stopped -- the fore pocket-clear hold's pattern). THE MINED DRAG FACE IT
 // OWNS: the wave-28 R pad cleared at the fire, SAGGED to ~1.4e-3 under the
 // 4.8 m/s haul's servo lag, RE-ENTERED the band at 104 (a hovering pad has
 // no normal force and no friction catch) and was hauled at slip 1.8674.
 static constexpr int kFoldBudgetTicks=45; // the mined [TD 107, release 152) standing budget
 // ── THE UNLOAD-LIFT DEADLINE (wave 32, receipt_wave32.json) ──
 // THE MINED UNLOAD LAW (the wave-31 shipped trace, the declared mining
 // script): a standing hind whose share vanishes lifts within ONE TICK -- the
 // R's rxn read 7.473@158 -> 3.795@159 -> 1.595@160 -> 0.000@161 N around the
 // L's 160 completion, and the pads left the band AT the vanish tick (0.0782
 // mm @161): the unload tick = the other's band entry + kUnloadTicks (the +1
 // class). THE CONTROL ERA: around the R's 107 completion the standing L's
 // share HELD (49-86 N, zero rxn-0 ticks in [107,142)) -- the ENTRY-era seat
 // (no completed step-replant of its own) survives the other's landing; the
 // RIDE era does not. The fire must PRECEDE the unload, and the machinery's
 // own hand-off g=1 already prices one tick of clearance into the wave-20
 // tau1 form, so the unload bound reads the OTHER'S BAND ENTRY TICK ITSELF:
 // min-form deadline = min(other_last_td + kFoldBudgetTicks - tair - g,
 //                          other_last_td + kUnloadTicks - g).
 // THE ARMING: the unload term binds only when THIS leg has completed a
 // step-replant (the ride era) -- disarmed, the deadline is the wave-29 fold
 // form exactly (the L's 108..141 due arithmetic and its 142 deadline fire
 // stay byte-identical). The WAVE-29 SKEW-REPAIR clause ('this leg replanted
 // -> the natural cadence owns') is REMOVED: its premise -- the re-synced
 // clock's slot arrives within the standing budget -- is falsified by the
 // mined face (the R's re-synced slot ~252 vs its window closed at 161; the
 // unloaded pad cannot wait for a slot 91 ticks past its own unload).
 static constexpr int kUnloadTicks=1;      // the mined +1 class (the unload = entry+1)
 // ── THE STAND-FIRST HOLD (wave 33, receipt_wave33.json) ──
 // THE MINED FACE (the wave-32 shipped trace, the declared mining script):
 // from the L@175 fire on, every exchange swing STALLED -- its lift-first hold
 // never released (the arch peak 0.0087-0.0124 mm vs the real lifts' 1.52-13.1
 // mm), the fired pads crept IN-BAND dragging (slip 0.10-0.7674 m/s), because
 // the exchange fires land on pads STILL LOADED (the fired leg's rxn at its
 // own fire 2.265/2.156/0.492/5.455/4.649 N). At the sixth exchange the sole
 // carrier's share drained mid-swing (the R 4.025@211 -> 0.000@215) and the
 // unloaded columns lifted its pad (the pair-min 9.63um@214 -> 193.72um@215):
 // the wave-30 unload-lift face, the strand, the refusal at 300. The wave-32
 // deadline reads the other's LAST TD and (a) never yields mid-glide -- no
 // FIRE deadline can cover a carrier unloading mid-swing. THE MIRROR: a PAD
 // HOLD (the descent-armed amendment). While the other hind is mid-glide AND
 // its pads are IN THE TOUCH BAND -- the swing's tick-start TOUCHING CLASS,
 // the mechanism's own clock: never-left (the stall swings) or RETURNED (the
 // real swings' descent re-entry, the mined +1 class's own face) -- AND this
 // leg is the ride-era carrier with live pads, this leg's stance target is
 // REPLACED by the IK hold at the pad spots RE-CAPTURED at each pinned tick
 // (a zero-velocity demand at the pads' instant position) -- the wave-29
 // glide hold's whole-branch replacement mirrored (the designed stance
 // tables AND the wave-27 ff both displaced): the unloaded columns cannot
 // lift the pad, disarmed BY STRUCTURE. The hold releases when the other
 // completes or its pads genuinely clear (the real lift's own era -- the
 // stance columns resume); the wave-32 exchange fire then lands on live pads
 // at the completion, untouched. Clause (a) NEVER yields -- untouched. Zero
 // new numeric constants: the read is the wave-22 touching class's own
 // hysteresis state. MAPPED LEAD (mined): the swing's in-band read lands one
 // decision before the fold's first band-exit read -- the +1 class again.
 // First engagement on the shipped bytes: the 176 decision (the cycle-2 stall
 // swing's first glide tick-start; the pre-176 real lifts' pads are out of
 // band at every glide tick-start until their completion -- the wave-31 hold
 // class: 1.2383e-3 m @159, 6.29e-4 m @174).
 uint64_t hind_step_stall_[2]={0,0};        // the per-swing stall clock (held ticks, reset at each fire; census)
 bool hind_step_stand_[2]={false,false};    // the stand-first hold is pinned this tick
 V hind_step_stand_from_[2]={V{},V{}};      // the pinned pad spots (planar re-captured every pinned tick)
 double hind_step_stand_y_[2]={0.,0.};      // the FLOOR ANCHOR: the pads' height captured at the arm tick
 double hind_step_stand_mp_[2]={0.,0.};     // the pinned MP angle (re-captured every pinned tick)
 uint64_t hind_step_stand_ticks_[2]={0,0};  // the pinned-tick census
 // THE LATCHED CARRIER HOLD (wave 34, receipt_wave34.json): the mined
 // 250 disarm -- the per-tick predicate defeats itself on the carrier's own
 // 1-tick graze past the genuine-departure bound (1.317e-5 > kTouch+
 // kReleaseBand), exactly the unload-lift it exists to prevent -- so the
 // LATCH: once the hold has armed in the other's swing era it stays armed
 // until the other completes or this leg fires, gated to the swing's own
 // genuinely-cleared lift-first hold (the real lift's own read: the stall
 // blinks ride the shipped 1-tick column resumptions -- pinning through them
 // launched the walk at 215, measured twice; the airborne gate was the wave
 // 34 first amendment). The latch's continuation pins with the SHIPPED
 // anchor (the planar re-captured every pinned tick, the y the arm capture):
 // the FROZEN WORLD PIVOT variant was tried and reverted (the second
 // amended build: the roll demand marched the knee target -59.5 -> -31.7
 // deg, the capped servo lost the pads at 259, the walk refused 298); its
 // extension-envelope release read is reverted with it (the release field
 // stays at its -1 sentinel).
 bool hind_step_stand_latch_[2]={false,false}; // the latch is armed this swing era
 bool hind_step_stand_pivot_[2]={false,false}; // the latch-era marker (the census)
 int hind_step_stand_release_[2]={-1,-1};      // the envelope-release tick (-1 sentinel; the read reverted)
 uint64_t hind_step_stand_latch_ticks_[2]={0,0};// the latch-era pinned-tick census
 // ── THE CARRIER SELF-UNLOAD FIRE DEADLINE (wave 35, receipt_wave35.json) ──
 // THE MINED FACE (the declared script .tmp/w35_receipt/mine_carrier.py on this
 // lane's byte-exact reproduction trace, the FRONT decision rule fixed in its
 // header BEFORE the numbers): the twelfth-era carrier drain on the SHIPPED
 // (unpinned) bytes is 4.648 N @247 -> 4.415 @248 -> 0.309 @249 -> 0.000 @250
 // (the pair-min 8.21e-6 -> 1.317e-5 = the band exit -> 6.70e-5): the carrier
 // gets EXACTLY THREE legal-fire decisions after the other's launch, while its
 // own alternation fire is alt-due the whole era with the deadline BINDING ON
 // THE UNLOAD FORM (dl=238 = the L's last TD + kUnloadTicks - g, the wave-32
 // arithmetic) and gated ONLY by clause (a). FRONT 2 failed both its
 // pre-registered conditions (R1: the era length does NOT scale with the plant
 // lead, r=0.3587; R2: the drain onset does NOT align geometrically, 0.126 vs
 // 0.382 m at the onsets) -- FRONT 1 owns. THE LAW: the no-double-step clause
 // (a) YIELDS for a carrier's alternation fire when the deadline fire is
 // binding ON THE UNLOAD FORM (hind_step_dl_unload_, the machinery's own
 // wave-32 flag) AND the other's lift-first hold has GENUINELY CLEARED
 // (hind_step_held_[o]==false, the machinery's own wave-31/34 airborne read --
 // the stall swings' holds never clear, so the stall eras never see the
 // waive). The wave-34 core carried verbatim: the drain is GEOMETRIC (every
 // replant under-delivers its target by 0.156-0.462 m -- the splay) and the
 // pin only presses dead pads; the REAL haul delivers (the L's 0.337 ->
 // 0.428 m, 47.717 N at the 262 completion) -- the fired carrier's own haul is
 // the escape. ZERO new numeric constants: the deadline is the machinery's own
 // kUnloadTicks/kFoldBudgetTicks/g arithmetic, the gate the machinery's own
 // held_ read.
 uint64_t hind_step_waive_fires_[2]={0,0};  // the (a)-waiving unload-deadline fires
 int hind_step_waive_first_[2]={-1,-1};     // the first waive fire's tick (the census)
 int hind_step_waive_last_[2]={-1,-1};      // the last waive fire's tick (the census)
 uint64_t hind_step_graze_yields_[2]={0,0}; // the completion-tick re-lock's graze yields (the census)
 int hind_step_graze_first_[2]={-1,-1};     // the first graze yield's tick (the census)
 uint64_t hind_step_guard_blocks_[2]={0,0}; // the calendar-arithmetic waive scope guard's blocks (the census)
 int hind_step_guard_first_[2]={-1,-1};     // the first guard block's tick (the census)
 // ── THE WAIVE-ERA HAND-OFF PRESERVATION (wave 36, receipt_wave36.json) ──
 // THE MINED FACE (the declared script .tmp/w36_receipt/mine_w36.py on this
 // lane's byte-exact reproduction trace, the decision rule fixed in its header
 // BEFORE the numbers): (R1) the hand-off fires are COMPLETION-TICK-LOCKED --
 // all 10 unloadgate-class fires land ON the other's last TD -- so any
 // completion perturbation shifts the whole resumed calendar (the wave-35
 // build-2 death: the waive-perturbed R landing at 174 re-phased the stall
 // chain -1 against the unshifted fore cadence, the dead-pad fire at 201, the
 // impact death at 266); (R2) the +2 waive edge is STRUCTURALLY DEAD in the
 // twelfth era (the carrier's touch hysteresis releases at the 249 tick-start:
 // 1.317e-5 > kTouch+kReleaseBand=1.1e-5; 8.207e-6 @248 in band) -- the wave-35
 // build-1 gate's +1 edge is the ONLY lawful waive edge, so the phase must be
 // restored at the HAND-OFF, not at the waive; (R3) the wave-35 amendment's
 // concentration repair is inert on the shipped trajectory over [0,160]
 // (0 flips). THE LAW'S THIRD CLAUSE: the (b)-waive is disarmed for the
 // hand-off out of a waive-ridden swing -- when this leg's own waive fire
 // postdates the other's current-swing launch, the hand-off rides the natural
 // g=1 clause (b) and lands at the completion + 1, the shipped grid tick; the
 // disarm self-expires at the other's next fire. One +1 hand-off absorbs the
 // perturbation; the stall calendar re-locks to the shipped cadence.
 mutable uint64_t hind_alt_repairs_[2]={0,0};        // the repair-flipped concentration reads
 uint64_t hind_step_handoff_restores_[2]={0,0};      // the (b)-waive disarms (the preserved hand-offs)
 bool hind_stand_hold(size_t hl)const{
  size_t o=hl==0?1:0;
  if(hind_step_mode_[o]!=1)return false;              // the exchange era only
  if(hind_step_last_td_[hl]==0)return false;          // the ride era only
  if(!(hind_step_t_[o]>=1.))return false;             // the swing UNDERWAY (not the same-tick fire)
  if(!touching_prev_[hl]||!touching_prev_[o])return false;
  // THE DESCENT ARM (the amendment): the swing's tick-start touching class is
  // the mechanism's own clock -- the pads in the band whether NEVER-LEFT (the
  // stall swings) or RETURNED (the real swings' descent re-entry, the mined
  // +1 class's own face). The wave-22 hysteresis is the read's dead-band.
  // The t>=1 guard excludes the fire tick itself: a just-fired leg is in-band
  // BY THE LIFT-FIRST HOLD's own design, and the same-tick loop order (leg 0
  // fires before leg 1's decision) would otherwise pin the carrier at the
  // fire -- measured: the 142 one-tick pin derailed the whole ride.
  return true;}
 bool hind_step_held_[2]={false,false};     // the lift-first hold is armed
 int hind_step_clear_tick_[2]={-1,-1};      // the tick the release quantum cleared
 uint64_t hind_step_hold_ticks_[2]={0,0};   // the held-tick census
 int hind_step_alt_[2]={0,0};               // the last fire's class: 0 slot, 1 alternation
 int hind_step_alt_due_[2]={0,0};           // the alternation-due flag at this tick (status)
 uint64_t hind_step_deadline_tick_[2]={0,0};// the current deadline arithmetic (status)
 uint64_t hind_step_deadline_fires_[2]={0,0};// the (b)/(c)/(d)-waiving deadline fires
 int hind_step_dl_unload_[2]={0,0};         // the binding deadline is the unload form (status)
 uint64_t hind_step_unload_fires_[2]={0,0}; // the unload-deadline fires (the exchange census)
 // The alternation-due predicate. THE WAVE-29 CONCENTRATION CLAUSE, '<' form
 // (wave 32): the other's fire ON THE SAME TICK as this leg's landing -- the
 // handed exchange's own signature -- concentrates the ride (byte-identical
 // through 159: no equal case arises before 160). Phi below the slot: the
 // natural trigger keeps precedence whenever the clock can still own the leg.
 bool hind_alt_due(size_t hl,double tair)const{
  size_t o=hl==0?1:0;
  if(hind_step_last_td_[o]==0)return false;            // no completed other step yet
  // THE EXCHANGE-CHAIN CONCENTRATION REPAIR (the wave-35 amendment form, carried
  // by the wave-36 law; receipt_wave35.json + receipt_wave36.json): the hand-off
  // is STALE only when NEITHER the other's last fire NOR the other's last replant
  // postdates this leg's own last replant. The wave-35 build-2 lesson is carried
  // by the preservation clause at the (b)-waive site, not here: the repair alone
  // re-armed the hand-off ON the perturbed completion tick and the completion-
  // tick-locked calendar re-phased -1 against the fore cadence (the R's dead-pad
  // fire at 201, the impact death at 266). STRUCTURAL FENCE PROOF (mined, the
  // declared script, R3): on the shipped trajectory the repair NEVER flips the
  // read over [0,160] -- 0 flips -- so the [0,160] identity and the named ticks
  // are untouched by this clause.
  if(hind_step_last_fire_[o]<hind_step_last_td_[hl]&&
     hind_step_last_td_[o]<hind_step_last_td_[hl])return false; // not concentrated
  if(hind_step_last_fire_[o]<hind_step_last_td_[hl])   // the repair flipped the read
   ++hind_alt_repairs_[hl];                            // (the census, status-only)
  if(phi_[hl]>=TOE_OFF)return false;                   // the natural slot owns
  uint64_t deadline=hind_deadline(hl,tair);
  double wait=(TOE_OFF-phi_[hl])/(dt_/T_CYCLE);        // the clock's own rate
  return double(ticks_)+wait>double(deadline);}
 // THE WAVE-32 MIN-FORM DEADLINE (the one arithmetic, shared by the due
 // predicate and the status census so they cannot drift): the wave-29 fold
 // budget form, tightened by the armed unload bound. Returns the deadline
 // tick; sets is_unload when the binding term is the unload form.
 uint64_t hind_deadline(size_t hl,double tair,bool* is_unload=nullptr)const{
  size_t o=hl==0?1:0;
  if(is_unload)*is_unload=false;
  if(hind_step_last_td_[o]==0)return 0;
  uint64_t fold=hind_step_last_td_[o]+(uint64_t)(kFoldBudgetTicks-(int)tair-1); // g=1
  if(hind_step_last_td_[hl]!=0){                       // the ride era: the unload arms
   uint64_t unload=hind_step_last_td_[o]+(uint64_t)(kUnloadTicks-1);            // g=1
   if(unload<fold){if(is_unload)*is_unload=true;return unload;}}
  return fold;}
 // the harvested hind chain geometry (the scene's own model bytes)
 size_t hind_coord_[2][4]{{0,0,0,0},{0,0,0,0}}; // [leg][hip,knee,ankle,MP]
 size_t pelvis_row_=0;
 V hind_mount_[2]={V{},V{}};           // the hip mounts in the pelvis frame
 double hind_L1_=0,hind_L2_=0;         // the thigh/shank lengths
 double hind_xm_=0;                    // the paw-midpoint x in the foot frame
 size_t hind_heel_pt_[2]={0,0},hind_mp_pt_[2]={0,0};
 std::vector<BodyRef> bodies_;bool contact_=false;
 State s_;mutable uint64_t adv_calls_=0;
 Evaluation evaluate(const State& s)const{return model_->evaluate(s.q,s.v,gravity_);}
 double mechanical(const State& s)const{auto e=evaluate(s);return .5*inner(s.v,multiply(e.mass,s.v))+e.potential;}
 bool sole_representative(size_t k)const{return k<npts_ && (k%2)==0;}
 V sole_local(const Evaluation& e,size_t k)const{
  // The contract keeps heel and MP endpoints. The active row is evaluated at
  // the closest point of their sole segment; a flat tie chooses its midpoint
  // deterministically, sharing the flat-phase load through the sole.
  size_t h=k-(k%2),m=h+1;
  auto ph=e.point(points_[h].index,points_[h].local).first;
  auto pm=e.point(points_[m].index,points_[m].local).first;
  double gh=ph[1]+points_[h].radius-plane_model_y_;
  double gm=pm[1]+points_[m].radius-plane_model_y_;
  double dy=pm[1]-ph[1];
  // Near a flat loaded window the segment's closest set is degenerate; keep
  // the CoP in its interior rather than letting endpoint roundoff select the
  // MP lever. Outside that band the lower endpoint is the migrating CoP.
  double a=(gh<=2e-6&&gm<=2e-6)||std::abs(dy)<1e-8?0.5:(dy<0.?1.:0.);
  V local=points_[h].local;for(int i=0;i<3;++i)local[i]+=(points_[m].local[i]-points_[h].local[i])*a;return local;}
 V sole_position(const Evaluation& e,size_t k)const{return e.point(points_[k-(k%2)].index,sole_local(e,k)).first;}
 double gap_of(const Evaluation& e,size_t k)const{
#ifdef GAIT_EVENT_TRACE
  if(k>=points_.size()||points_[k].index>=e.frames.size())
   std::fprintf(stderr,"[gapbound] k=%zu npts=%zu frames=%zu tick=%llu\n",
    k,points_.size(),e.frames.size(),(unsigned long long)ticks_);
#endif
  size_t h=k-(k%2),m=h+1;
  double gh=e.point(points_[h].index,points_[h].local).first[1]+points_[h].radius-plane_model_y_;
  double gm=e.point(points_[m].index,points_[m].local).first[1]+points_[m].radius-plane_model_y_;
  return (std::min)(gh,gm);}
 Dense contact_row(const Evaluation& e,size_t k)const{auto j=e.point(points_[k-(k%2)].index,sole_local(e,k)).second;Dense r(n_,0.);for(size_t i=0;i<n_;++i)r[i]=j[i][1];return r;}
 Dense tangent_row(const Evaluation& e,size_t k,int axis)const{auto j=e.point(points_[k-(k%2)].index,sole_local(e,k)).second;Dense r(n_,0.);for(size_t i=0;i<n_;++i)r[i]=j[i][axis];return r;}
 V contact_bias(const Evaluation& e,size_t k)const{return vector(e.frames[points_[k-(k%2)].index].ddt,sole_local(e,k),1);}
 double joint_speed_scale(const State& s)const{double a=0;for(size_t d=0;d<nd_;++d)a+=std::abs(s.v[drives_[d].coordinate]);return a;}
 Dense normals(const State& s)const{Dense row(n_,0.);for(size_t d=0;d<nd_;++d){size_t c=drives_[d].coordinate;if(std::abs(s.q[c]-model_->lower[c])<1e-10)row[c]=1;else if(std::abs(s.q[c]-model_->upper[c])<1e-10)row[c]=-1;}return row;}
 static bool gram_factor(std::vector<double> g,size_t k,const Dense& rhs,Dense& lambda){
  double scale=0;for(size_t i=0;i<k;++i)scale=(std::max)(scale,std::abs(g[i*k+i]));if(!(scale>0))return false;
  for(size_t i=0;i<k;++i)for(size_t j=0;j<i;++j)g[i*k+j]=g[j*k+i]=(g[i*k+j]+g[j*k+i])/2;
  std::vector<double> l(k*k,0.);
  for(size_t i=0;i<k;++i)for(size_t j=0;j<=i;++j){double t=g[i*k+j];for(size_t m=0;m<j;++m)t-=l[i*k+m]*l[j*k+m];
   if(i==j){if(!(t>1e-9*scale))return false;l[i*k+j]=std::sqrt(t);}else l[i*k+j]=t/l[j*k+j];}
  lambda=Dense(k,0.);
  for(size_t col=0;col<k;++col){Dense y(k,0.),x(k,0.);
   for(size_t i=0;i<k;++i){double t=col==i?1.:0.;for(size_t m=0;m<i;++m)t-=l[i*k+m]*y[m];y[i]=t/l[i*k+i];}
   for(size_t ii=k;ii-->0;){double t=y[ii];for(size_t m=ii+1;m<k;++m)t-=l[m*k+ii]*x[m];x[ii]=t/l[ii*k+ii];lambda[ii]+=x[ii]*rhs[col];}}
  return true;}
 // Mass-metric active-set projection (the free-root D6 law, row-count
 // parametric; the walker caps rows at n+1 like the n-coordinate class).
 static bool in_gait_diag(const std::vector<size_t>& act,int v){for(size_t a:act)if(a==(size_t)v)return true;return false;}
 // Mass-metric cone projection over named rows (the free-root D6 law). The
 // deterministic SOLVER is the n-coordinate class's full subset enumeration,
 // lifted row-count-only: every active-set mask is solved in mask order and
 // the first cone-valid candidate that satisfies EVERY row's floor wins.
 // Enumeration is exhaustive (the optimal active set IS some subset), so it
 // cannot churn; R is capped loudly (the free-root's seated 4-point scenes
 // measure R<=6; stops arm only within 1e-10 of a bound, so the walk's
 // plain-contact stages measure R<=4).
 // TIER LAW (the over-constraint membrane, 20260919): when an armed joint
 // stop coexists with arriving contacts (a heel seated, an MP landing under
 // the floor, the hip on its wall), more than one mask can be cone-valid and
 // numeric order can pick the one that DROPS the stop -- the contact then
 // relieves its penetration by pushing the joint past its wall, the clamp
 // loop re-pins, and the walk chatters into the budget refusal (measured:
 // tick 40, 64 identical clamp iterations, frozen state). A hard stop is
 // never sacrificed while a stop-holding projection exists: masks holding
 // EVERY stop row (plus the no-op mask 0, which sacrifices nothing) are
 // searched FIRST, the rest only if none is valid. The unilateral contacts
 // separate instead -- the heel lifts, the foot pivots on the MP head.
 static Dense project_rows(const Dense& initial,const Dense& inverse,const std::vector<Dense>& rows,const Dense& floors,std::vector<double>* multipliers,size_t n_stops=0){
  size_t n=initial.size();size_t R=rows.size();
  require(R>=1&&R<=10,"gait_row_budget");
  bool dbg=R==1;
  for(int tier=0;tier<2;++tier)
  for(size_t mask=0;mask<(size_t(1)<<R);++mask){
   if(mask!=0){bool holds=true;for(size_t k=0;k<n_stops;++k)if(!(mask>>k&1)){holds=false;break;}
    if(holds!=(tier==0))continue;}
   else if(tier!=0)continue;
   std::vector<size_t> act;for(size_t k=0;k<R;++k)if(mask>>k&1)act.push_back(k);
   if(act.size()>n)continue; // mask 0 (no correction) is a legal candidate
   if(act.empty()){ // mask 0: no correction -- valid iff every floor already holds
    bool ok=true;Dense zero(n,0.);
    for(size_t k=0;k<R;++k){double tol=1e-9*(1.+std::abs(floors[k]));if(inner(rows[k],initial)<floors[k]-tol){ok=false;break;}}
    if(ok){if(multipliers)multipliers->assign(R,0.);return zero;}
    continue;}
   std::vector<double> gram(act.size()*act.size(),0),rhs(act.size());
   for(size_t a=0;a<act.size();++a){for(size_t b=0;b<act.size();++b)gram[a*act.size()+b]=inner(rows[act[a]],multiply(inverse,rows[act[b]]));rhs[a]=floors[act[a]]-inner(rows[act[a]],initial);}
   std::vector<double> lambda;
   if(!gram_factor(gram,act.size(),rhs,lambda)){if(dbg)std::fprintf(stderr,"GAIT-R1 mask cholesky fail A=%.4g rhs=%.4g\n",act.size()?gram[0]:0.,act.size()?rhs[0]:0.);continue;}
   bool valid=true;Dense p(n,0.);
   for(size_t k=0;k<act.size();++k){if(lambda[k]<-1e-10){if(dbg)std::fprintf(stderr,"GAIT-R1 mask lam<0 lam=%.4g rhs=%.4g rowdot=%.4g\n",lambda[k],rhs[0],inner(rows[0],initial));valid=false;}double l=(std::max)(0.,lambda[k]);for(size_t i=0;i<n;++i)p[i]+=l*rows[act[k]][i];}
   if(!valid)continue;
   auto change=multiply(inverse,p);Dense projected(initial);
   for(size_t i=0;i<n;++i)projected[i]+=change[i];
   // Floor satisfaction is RELATIVE to each row's scale (the free-root/n-coord
   // absolute 1e-9 measured too tight when high-speed states push |floor| to
   // centripetal magnitudes; 1e-9 relative matches the suites' rel() bars).
   for(size_t k=0;k<R;++k){double tol=1e-9*(1.+std::abs(floors[k]));double got=inner(rows[k],projected);if(got<floors[k]-tol){if(dbg)std::fprintf(stderr,"GAIT-R1 mask floor fail row=%d got=%.9g floor=%.9g tol=%.4g\n",(int)k,got,floors[k],tol);valid=false;break;}}
   if(valid){if(multipliers){multipliers->assign(R,0.);for(size_t k=0;k<act.size();++k)(*multipliers)[act[k]]=(std::max)(0.,lambda[k]);}return p;}
  }
  std::fprintf(stderr,"GAIT-ROWBUDGET R=%d enumeration exhausted\n",(int)R);
  throw Refusal("gait_row_budget");}
 static void friction_solve(const Dense& initial,const Dense& inverse,const Dense& row_n,const Dense& row_t,double floor_n,double floor_t,double mu,double slip_sign,Dense& force,double& lambda_n,double& lambda_t,int& mode){
  force=Dense(initial.size(),0.);lambda_n=0;lambda_t=0;mode=0;
  auto in=multiply(inverse,row_n),it=multiply(inverse,row_t);
  double A=inner(row_n,in),B=inner(row_n,it),C=inner(row_t,it),rn=-(inner(row_n,initial)-floor_n),rt=-(inner(row_t,initial)-floor_t),det=A*C-B*B;
  if(det>1e-18){double nn=(rn*C-rt*B)/det,t=(rt*A-rn*B)/det;
   if(nn>=0&&std::abs(t)<=mu*nn+1e-12&&(slip_sign==0.||t*slip_sign<=0.)){for(size_t i=0;i<initial.size();++i)force[i]=row_n[i]*nn+row_t[i]*t;lambda_n=nn;lambda_t=t;mode=1;return;}}
  double s=slip_sign!=0.?slip_sign:(rt>=0.?-1.:1.),den=A-s*mu*B;
  if(den<=1e-12)throw Refusal("gait_friction_slide_singular");
  double nn=rn/den,t=-s*mu*nn;
  if(nn>=0){for(size_t i=0;i<initial.size();++i)force[i]=row_n[i]*nn+row_t[i]*t;lambda_n=nn;lambda_t=t;mode=2;return;}
  force=Dense(initial.size(),0.);lambda_n=0;lambda_t=0;mode=0;}
 // ── the controller proper ──
 // THE TOUCH LAW's classification (wave 22, receipt_wave22.json): the leg's
 // contact state for the CLOCK. In contact at pair-min gap <= kTouch; released
 // only when the pair-min gap exceeds kTouch+kReleaseBand (a GENUINE departure
 // clears the solver's own stabilization quantum within the tick); inside the
 // band's hysteresis margin the previous state HOLDS -- a band-edge graze
 // never releases, so its re-entry is not a rising edge and cannot reset the
 // stance clock. Deterministic, stateless beyond the previous state itself.
 bool leg_contact(const Evaluation& e,size_t leg,bool prev)const{
  double gmin=1e300;const char* prefix=leg==0?"left":"right";
  for(size_t k=0;k<npts_;++k)if(points_[k].name.rfind(prefix,0)==0)gmin=(std::min)(gmin,gap_of(e,k));
  if(gmin<=kTouch)return true;
  if(gmin>kTouch+kReleaseBand)return false;
  return prev;}
 // Contact-reset hybrid clock (Section 5.1): advance by sim time, RESET to 0
 // at the leg's own kTouch crossing (a leg is touching when ANY of its foot
 // points is inside the band). Returns true when a reset fired this tick.
 // WAVE 22: the crossing is classified by leg_contact -- the release state
 // cleared only by a genuine departure (> kTouch+kReleaseBand), so the edge
 // fires for TOUCHDOWNS tick-exactly as before, while a band-edge graze (the
 // measured 1.6e-7 m / 1-tick excursion that slammed phR 0.5282 -> 0 at the
 // walk's step 66 and plowed the loaded foot to 2.03 m/s) re-arms NOTHING.
 bool update_clock(const Evaluation& e,double dt){
  bool reset_fired=false;
  for(size_t leg=0;leg<2;++leg){
   bool touching=leg_contact(e,leg,touching_prev_[leg]);
   if(touching&&!touching_prev_[leg]){phi_[leg]=0.;reset_fired=true;}
   // RUN REPAIR (wave 16, itemized in receipt_wave16.json): the phase advance
   // carried the per-leg OFFSET inside the per-tick increment for the right
   // leg (+0.5 every tick), which aliases phi_[1] into two interleaved
   // half-clocks (f applied twice advances only 2c). The doc's law (Section
   // 5.1) is phi_leg=(t/T+off) mod 1 with the offset applied ONCE -- reset()
   // already inits phi_ to {0, 0.5}. Before: the right leg's phase (and with
   // the wave-16 target repair, its whole gait) aliased; the status phase
   // column alternated ~0/~0.5 tick by tick. No tuning: the doc's own law.
   else phi_[leg]=std::fmod(phi_[leg]+dt/T_CYCLE,1.);
   touching_prev_[leg]=touching;}
  return reset_fired;}
 // Support hull + CoM (Section 5.4). Returns com_in_hull; sets hull/com refs.
 // The out-parameter `hull` keeps its historical bytes: the lexicographically
 // SORTED touching-point cloud. The WAVE-21 ARMING LAW (receipt_wave21.json)
 // additionally needs the TRUE convex hull -- the monotone chain this function
 // builds locally -- so a defaulted out-param receives it; every existing call
 // site passes nothing and is byte-unchanged.
 bool support_state(const Evaluation& e,std::vector<std::pair<double,double>>& hull,V& com,
  std::vector<std::pair<double,double>>* chain=nullptr)const{
  hull.clear();
  for(size_t k=0;k<npts_;++k)if(contact_&&gap_of(e,k)<=kTouch){auto p=e.point(points_[k].index,points_[k].local).first;hull.push_back({p[0],p[2]});}
  for(size_t b=0;b<bodies_.size();++b){auto p=vector(e.frames[b].t,bodies_[b].com,1);for(int k=0;k<3;++k)com[k]+=bodies_[b].mass*p[k];}
  for(int k=0;k<3;++k)com[k]/=mtot_;
  if(hull.size()<3)return false;
  // Andrew monotone chain, deterministic lexicographic order.
  std::sort(hull.begin(),hull.end());
  hull.erase(std::unique(hull.begin(),hull.end()),hull.end());
  if(hull.size()<3)return false;
  std::vector<std::pair<double,double>> h(2*hull.size());
  size_t k=0;
  for(size_t i=0;i<hull.size();++i){while(k>=2&&(h[k-1].first-h[k-2].first)*(hull[i].second-h[k-2].second)-(h[k-1].second-h[k-2].second)*(hull[i].first-h[k-2].first)<=0)--k;h[k++]=hull[i];}
  for(size_t i=hull.size()-1,t=k+1;i-->0;){while(k>=t&&(h[k-1].first-h[k-2].first)*(hull[i].second-h[k-2].second)-(h[k-1].second-h[k-2].second)*(hull[i].first-h[k-2].first)<=0)--k;h[k++]=hull[i];}
  h.resize(k-1);
  if(chain)*chain=h;
  double px=com[0],pz=com[2];bool inside=true;int side=0;
  for(size_t i=0;i<h.size();++i){auto&a=h[i];auto&b=h[(i+1)%h.size()];double cross=(b.first-a.first)*(pz-a.second)-(b.second-a.second)*(px-a.first);
   if(std::abs(cross)<1e-15)continue;int s=cross>0?1:-1;if(side==0)side=s;else if(s!=side){inside=false;break;}}
  return inside;}
 // Capture-step reflex (Section 5.4): CoM projection exits the hull moving
 // outward -> swing leg phase jumps to 0.95 (early touchdown). Falsified by
 // F-G6: without it a push must tip; with it the capture step must land.
 // ── THE WAVE-21 ARMING LAW (receipt_wave21.json): the arming test had two
 //    measured defects -- it ran on the SORTED POINT CLOUD (a self-intersecting
 //    pseudo-polygon: the tick-65 fire armed at +0.0046 m 'outside' a pseudo-
 //    edge while the true hull held the CoM strictly inside) and it chose as
 //    its capture leg any non-touching leg (the tick-65 fire picked a foot
 //    straddling the band edge by 1.6e-7 m at stance clock 0.0235). The fire
 //    now requires ALL THREE derived clauses:
 // (i)  THE TRUE-HULL CLAUSE: the containment test runs on the monotone-chain
 //      convex hull (the doc's own law), never on the sorted cloud;
 // (ii) THE SWING-CLOCK CLAUSE: the candidate leg's clock is in its swing
 //      window (phi >= TOE_OFF, the machinery's own sampled toe-off -- a
 //      stance-clock leg's contact loss is instability, not swing; the reflex
 //      waits for the clock to bring the leg to swing);
 // (iii) THE SLIP-CONE CLAUSE: no touching sole's slip exceeds the derived
 //      bound v_bound = mu * g * (1-CAPTURE_PHI) * T_CYCLE = 0.2089 m/s --
 //      the cone's arrest capacity (mu*g, N-independent) within the capture's
 //      OWN touchdown window (the (1-CAPTURE_PHI)*T_CYCLE = 0.0355 s the jump
 //      itself grants).
 // MEASURED OUTCOME (honest, wave 21): the clauses removed the spurious fires
 // (capture_events 2 -> 0; the wave-19/20 phase-0.95 fingerprints gone) and
 // the walk STILL refused at 80 with the identical ledger -- the death's root
 // is the HIND CLOCK'S TOUCH-RESET SLAM (the kTouch chatter at [62,66] resets
 // a coherent mid-stance clock to the TD column: a ~47 deg multi-joint target
 // step whose capped drive plows the loaded sliding foot), NOT this reflex.
 // This law repairs the F-G6 machinery; it does not own the walk's lifetime.
 void capture_reflex(const Evaluation& e,const std::vector<std::pair<double,double>>& hull,const V& com){
  if(hull.size()<3)return;
  double vx=s_.v[3],vz=s_.v[5];
  // (iii) the slip-cone bound, derived from machinery constants only.
  double v_bound=mu_*norm(gravity_)*(1.-CAPTURE_PHI)*T_CYCLE;
  // (iii) max touching-sole slip, computed exactly as status() computes it.
  double slip_mx=0;
  for(size_t k=0;k<npts_;k+=2){
   if(!(contact_&&gap_of(e,k)<=kTouch))continue;
   auto j_t1=tangent_row(e,k,0),j_t2=tangent_row(e,k,2);
   V slip_v{};for(size_t i=0;i<n_;++i){slip_v[0]+=j_t1[i]*s_.v[i];slip_v[2]+=j_t2[i]*s_.v[i];}
   slip_mx=(std::max)(slip_mx,std::hypot(slip_v[0],slip_v[2]));}
  if(slip_mx>v_bound)return;
  // (i) the true-hull containment (the all-edge cross-sign law support_state
  // uses): still strictly inside -> nothing to capture. Outside -> the FIRST
  // violated edge supplies the outward probe (deterministic).
  size_t n=hull.size();int side=0;size_t violated=n;
  for(size_t i=0;i<n;++i){auto&a=hull[i];auto&b=hull[(i+1)%n];
   double cross=(b.first-a.first)*(com[2]-a.second)-(b.second-a.second)*(com[0]-a.first);
   if(std::abs(cross)<1e-15)continue;
   int s=cross>0?1:-1;if(side==0)side=s;else if(s!=side){violated=i;break;}}
  if(violated>=n)return; // strictly inside: the doc's trigger never armed
  {auto&a=hull[violated];auto&b=hull[(violated+1)%n];
   double ex=b.first-a.first,ez=b.second-a.second,nx=ez,nz=-ex;double nl=std::hypot(nx,nz);if(nl<1e-12)return;nx/=nl;nz/=nl;
   // outward normal = pointing away from the hull centroid (inside a convex chain)
   double cx=0,cz=0;for(auto&p:hull){cx+=p.first;cz+=p.second;}cx/=n;cz/=n;
   if((cx-a.first)*nx+(cz-a.second)*nz<0){nx=-nx;nz=-nz;}
   if((vx*nx+vz*nz)<=0)return; // exited but not moving outward
   // (ii) capture with the SWING leg: non-touching AND its clock in the
   // swing window -- a stance-clock leg's contact loss is instability; wait.
   for(size_t leg=0;leg<2;++leg){bool touching=false;const char* prefix=leg==0?"left":"right";
    for(size_t k=0;k<npts_;++k)if(points_[k].name.rfind(prefix,0)==0&&gap_of(e,k)<=kTouch)touching=true;
    if(!touching&&phi_[leg]>=TOE_OFF){phi_[leg]=CAPTURE_PHI;++capture_events_;return;}}
   return;}}
 // ── THE PLANTED-STRUT IK (wave 12) ──
 // Planar 2-DOF closed form (deterministic, no iteration), solved in the
 // PELVIS frame -- where the chain is defined: at q=0 the upperarm hangs
 // along the pelvis -y and q rotates about the pelvis z, so elbow =
 // S + L1*(sin q1, -cos q1) HOLDS in pelvis coordinates at ANY trunk lean
 // (the vault pitch cancels exactly; a world-frame solve biases the branch
 // and clamps -- measured and fixed the same day). The paw reference rides
 // the forearm at polar (rho, beta) in its frame; with q12 = q1+q2 the paw =
 // elbow + rho*(cos(q12+beta), sin(q12+beta)). The paw target stays WORLD
 // (the planted spot); it is mapped through the pelvis rotation transpose
 // every call. Law of cosines at the shoulder:
 // theta1 = atan2(dy,dx) + branch*acos((D^2+L1^2-rho^2)/(2 D L1));
 // the elbow closes vectorially: q2 = atan2(d - L1*u1) - q1 - beta.
 // The branch (+/-1) is captured ONCE at the settle as the solution matching
 // the planted configuration, then held -- no branch flapping mid-walk.
 struct ForeIK{double q1,q2;bool saturated;double q1_raw,q2_raw;};
 // WAVE 23 INSTRUMENTATION (the admissibility census's measured base): the
 // UNCLAMPED branch solution is carried beside the clamped one. The clamped
 // q1/q2 (the servo's targets) keep their exact bytes and values; the raw
 // fields expose where the branch solution sits relative to the joint walls
 // (the census's "inside annulus ∩ joint-range" test), nothing more.
 ForeIK fore_ik(size_t leg,const Evaluation& e)const{
  ForeIK out{0.,0.,false,0.,0.};
  const Mat& T=e.frames[fore_mount_body_[leg]].t;
  const V& m=fore_mount_local_[leg];
  double rx=paw_target_[leg][0]-T(0,3),ry=paw_target_[leg][1]-T(1,3),rz=paw_target_[leg][2]-T(2,3);
  double dx=T(0,0)*rx+T(1,0)*ry+T(2,0)*rz-m[0]; // (R^T r)_xy - mount: paw target
  double dy=T(0,1)*rx+T(1,1)*ry+T(2,1)*rz-m[1]; // in shoulder-local pelvis coordinates
  double D=std::hypot(dx,dy);
  double dmax=fore_L1_+fore_rho_,dmin=std::abs(fore_L1_-fore_rho_);
  // Reach saturation: the body has walked the shoulder past the plant. Pull
  // D to the reachable annulus boundary (the nearest reachable configuration,
  // which the capped PD then pursues) and COUNT it -- loud, never silent.
  if(D>dmax*(1.-1e-12)||D<dmin+1e-9){
   out.saturated=true;
   double Dc=(std::min)((std::max)(D,dmin+1e-9),dmax*(1.-1e-12));
   dx*=Dc/D;dy*=Dc/D;D=Dc;}
  double ca=(D*D+fore_L1_*fore_L1_-fore_rho_*fore_rho_)/(2.*D*fore_L1_);
  double th1=std::atan2(dy,dx)+double(ik_branch_[leg])*std::acos((std::max)(-1.,(std::min)(1.,ca)));
  out.q1=th1+pi/2;
  double ex=dx-fore_L1_*std::cos(th1),ey=dy-fore_L1_*std::sin(th1);
  double q2=std::atan2(ey,ex)-out.q1-fore_beta_;
  size_t c1=fore_coord_[leg][0],c2=fore_coord_[leg][1];
  out.q1_raw=out.q1;out.q2_raw=q2;
  out.q1=(std::max)(model_->lower[c1],(std::min)(model_->upper[c1],out.q1));
  out.q2=(std::max)(model_->lower[c2],(std::min)(model_->upper[c2],q2));
  return out;}
 // THE JOINT-ADMISIBLE HOLD's admissibility map: the branch IK at an
 // arbitrary paw seat (the same closed form fore_ik runs on the held
 // target; a separate body keeps fore_ik's mined bytes exact). Carries the
 // UNCLAMPED solution.
 ForeIK fore_ik_at(size_t leg,const Evaluation& e,const V& paw)const{
  ForeIK out{0.,0.,false,0.,0.};
  const Mat& T=e.frames[fore_mount_body_[leg]].t;
  const V& m=fore_mount_local_[leg];
  double rx=paw[0]-T(0,3),ry=paw[1]-T(1,3),rz=paw[2]-T(2,3);
  double dx=T(0,0)*rx+T(1,0)*ry+T(2,0)*rz-m[0];
  double dy=T(0,1)*rx+T(1,1)*ry+T(2,1)*rz-m[1];
  double D=std::hypot(dx,dy);
  double dmax=fore_L1_+fore_rho_,dmin=std::abs(fore_L1_-fore_rho_);
  if(D>dmax*(1.-1e-12)||D<dmin+1e-9){
   out.saturated=true;
   double Dc=(std::min)((std::max)(D,dmin+1e-9),dmax*(1.-1e-12));
   dx*=Dc/D;dy*=Dc/D;D=Dc;}
  double ca=(D*D+fore_L1_*fore_L1_-fore_rho_*fore_rho_)/(2.*D*fore_L1_);
  double th1=std::atan2(dy,dx)+double(ik_branch_[leg])*std::acos((std::max)(-1.,(std::min)(1.,ca)));
  out.q1=th1+pi/2;
  double ex=dx-fore_L1_*std::cos(th1),ey=dy-fore_L1_*std::sin(th1);
  double q2=std::atan2(ey,ex)-out.q1-fore_beta_;
  size_t c1=fore_coord_[leg][0],c2=fore_coord_[leg][1];
  out.q1_raw=out.q1;out.q2_raw=q2;
  out.q1=(std::max)(model_->lower[c1],(std::min)(model_->upper[c1],out.q1));
  out.q2=(std::max)(model_->lower[c2],(std::min)(model_->upper[c2],q2));
  return out;}
 double fore_D_at(size_t leg,const Evaluation& e,const V& paw)const{ // the raw annulus radius at a seat
  const Mat& T=e.frames[fore_mount_body_[leg]].t;
  const V& m=fore_mount_local_[leg];
  double rx=paw[0]-T(0,3),ry=paw[1]-T(1,3),rz=paw[2]-T(2,3);
  double dx=T(0,0)*rx+T(1,0)*ry+T(2,0)*rz-m[0];
  double dy=T(0,1)*rx+T(1,1)*ry+T(2,1)*rz-m[1];
  return std::hypot(dx,dy);}
 // ── THE JOINT-ADMISIBLE HOLD (wave 23, receipt_wave23.json) ──
 // THE MEMBRANE: the in-place hold's reachability includes the JOINT LIMITS,
 // not just the annulus. THE DERIVATION (measured on the byte-exact baseline,
 // the mining pass in gait_unit.cpp): the wave-22 refusal state held its
 // TARGET inside the joint range (0.0467 rad) while the ACTUAL shoulder sat
 // 0.0511 rad BELOW it (the servo's deflection under the L hind's 34-37 N
 // rear reaction: the measured 0.3314 N.m restoring at the mass-normalized
 // kp) -- the deflection consumed the margin and the substep crossed the
 // -1.6 rad wall (64 clamp pins at split depth 11). THE MINED SEPARATION:
 // the death's actual headroom ran 0.0482 (70) -> 0.0017 (82) at a ~0.0039
 // rad/tick dive, while the R's SURVIVABLE hold [60,66] dove at the same
 // rate but its clock lifted it before the wall; the L was GATE-HELD
 // PENDING -- a hold with no scheduled end. Both fore legs hold IK branch
 // -1, whose admissible ground-line band has a deep-bend pocket: a FORWARD
 // slide from the death seat DIVES THROUGH the wall (measured q1 -1.551 ->
 // -1.688 at +21 mm) while a BACKWARD slide restores (measured -1.551 ->
 // -1.460 at -5.5 mm); the pocket's far edge is the annulus itself, where
 // the nearly straight arm is jointly admissible (q1 -> psi+pi/2 ~ -1.29).
 // THE LAW: (i) the trigger -- the ACTUAL joints' wall headroom (NOT the
 // target's: the re-plants measurably restored the target, never the
 // actual) at or below kWallMargin, THE DEATH'S OWN DEFLECTION ENVELOPE
 // (the one measured constant: the wave-22 refusal state's actual-minus-
 // target offset 1.59930-1.54817 = 0.05113 rad), makes the liftoff DUE
 // through the standing no-double-swing gate (the forward re-plant
 // request); (ii) the gate-held wall-bound leg re-plants IN PLACE -- the
 // admissible follow: the target slides along the GROUND LINE (zero air
 // time, the pad stays in its band) to the seat whose TARGET headroom is
 // exactly 2*kWallMargin, in the authority direction (the +/- sample;
 // backward at the death window), the annulus bounding the slide (the
 // wave-20 never-saturate law; counted in fore_clamped_). The restore
 // re-arms the stance, so the follow recurs only at the dive rate; at the
 // annulus edge the joint margin is wide and the leg steps normally -- the
 // law converges, it cannot stall.
 static constexpr double kWallMargin=0.0511;
 // THE WAIT-OVERRIDE FLOOR (wave 26, receipt_wave26.json; derived, not
 // tuned). kDiveRateMax is the MAX measured per-tick dive of the wall-
 // adjacent wait on the byte-reproduced wave-25 law-free baseline: the R's
 // [dvf] series [81,89] = 0.026927, 0.023963, 0.020428, 0.017078, 0.013368,
 // 0.009348, 0.005897, 0.002231, 0.000000 -- the worst tick delta 0.004020
 // at [85,86] (the wave-25 chord 0.00373 is this same class). The fire
 // tick's integration completes under the PRE-FIRE target (the held-target
 // update runs BEFORE the liftoff decision in the same pass), so the worst-
 // case fire-tick dive is one full kDiveRateMax; the floor exceeds one full
 // dive-tick with the remainder at least one more dive-tick of standing
 // margin: at the worst fire (hr just under kWaitFloor) the minimum headroom
 // is >= kWaitFloor - kDiveRateMax = kDiveRateMax > 0 -- THE WALL IS NEVER
 // TOUCHED, WITH A FULL DIVE-TICK OF MARGIN, BY CONSTRUCTION. Emergency-
 // scoped: (kWallMargin - kWaitFloor)/kDiveRateMax ~ 10.7 wall-bound wait
 // ticks must elapse before it can fire (this baseline: the only crossing
 // in the measured life is the R's wait, hr 0.009348@86 -> 0.005897@87
 // decision states; the R's own first-stance dive bottoms 0.018355@70, the
 // L's 0.037575@74 -- both far above the floor).
 static constexpr double kDiveRateMax=0.004020;
 static constexpr double kWaitFloor=2.*kDiveRateMax;
 double fore_wall_headroom(size_t leg)const{ // the ACTUAL joints' min wall margin
  size_t c1=fore_coord_[leg][0],c2=fore_coord_[leg][1];
  double h1=(std::min)(s_.q[c1]-model_->lower[c1],model_->upper[c1]-s_.q[c1]);
  double h2=(std::min)(s_.q[c2]-model_->lower[c2],model_->upper[c2]-s_.q[c2]);
  return (std::min)(h1,h2);}
 double fore_target_headroom_at(size_t leg,const Evaluation& e,const V& paw)const{
  const ForeIK& ik=fore_ik_at(leg,e,paw);
  size_t c1=fore_coord_[leg][0],c2=fore_coord_[leg][1];
  double h1=(std::min)(ik.q1_raw-model_->lower[c1],model_->upper[c1]-ik.q1_raw);
  double h2=(std::min)(ik.q2_raw-model_->lower[c2],model_->upper[c2]-ik.q2_raw);
  return (std::min)(h1,h2);}
 // THE ADMISSIBLE FOLLOW (the crux clause): compute the seat restoring the
 // target headroom to 2*kWallMargin -- the direction the +/- 1 mm authority
 // sample picks, the distance a 42-step bisection finds (the machinery's own
 // depth), bounded by the annulus edge on that side (never saturating; the
 // edge itself is jointly admissible). Pure: returns the seat; the callers
 // adopt it. Deterministic; iterates the closed-form IK only.
 V fore_follow_seat(size_t leg,const Evaluation& e)const{
  V p=paw_target_[leg];
  V px=p,py=p;px[0]+=1e-3;py[0]-=1e-3;
  double dir=fore_target_headroom_at(leg,e,px)>=fore_target_headroom_at(leg,e,py)?+1.:-1.;
  double dmax=fore_L1_+fore_rho_;
  double lo=0,hi=2.*dmax; // the annulus edge on the authority side
  for(int j=0;j<42;++j){double mid=(lo+hi)/2;V t=p;t[0]+=dir*mid;
   if(fore_D_at(leg,e,t)<dmax)lo=mid;else hi=mid;}
  double edge=(lo+hi)/2;
  if(fore_target_headroom_at(leg,e,{p[0]+dir*edge,p[1],p[2]})<2.*kWallMargin)
   return {p[0]+dir*edge,p[1],p[2]};
  lo=0;hi=edge; // the restore distance: target headroom -> 2*kWallMargin
  for(int j=0;j<42;++j){double mid=(lo+hi)/2;V t=p;t[0]+=dir*mid;
   if(fore_target_headroom_at(leg,e,t)<2.*kWallMargin)lo=mid;else hi=mid;}
  return {p[0]+dir*((lo+hi)/2),p[1],p[2]};}
 // THE POCKET-CLEAR HOLD's march (wave 24, receipt_wave24.json): at a
 // wall-bound lift, walk the glide's own per-tick line points (no arch)
 // through the machinery's fore_ik_at and record the LAST tick whose
 // unclamped branch solution exits the scene's own joint ranges -- the
 // held span is [1, min(last, cycle-2)] and the release resumes the
 // standard line+arch. A wall_bound=0 lift marches nothing and holds
 // nothing: the standard path bytes run (the [0,65] proof standard).
 void fore_glide_arm_hold(size_t leg,const Evaluation& e,bool wall_bound){
  fore_glide_hold_[leg]=0;fore_hold_last_[leg]=0;
  if(!wall_bound)return;
  int n=(int)(fore_cycle_[leg]-fore_stance_[leg]);
  if(n<2)return;
  auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
  // THE HOLD SEAT: the map's unique above-ground MAXIMUM-AUTHORITY
  // configuration -- the annulus-edge ground seat in the authority
  // direction (the same +/- 1 mm sample and 42-step bisection the wave-23
  // follow runs; the wave-23 receipt's own words: the edge itself is
  // jointly admissible). MEASURED (v2, this lane): the follow-seat hold's
  // 0.49 N.m lost the wall fight to the contact closure on BOTH legs
  // (64+14 LOADED pins) -- the edge seat's 2.18 N.m (kp * the edge
  // headroom 0.3366 at the wave-23 liftoff state) is the machinery's
  // maximum; NO lift is added (the v2 held-pad gaps never cleared -- the
  // hug is force-held, and it is harmless once the wall is lost: the pins
  // need the wall).
  V p=paw_target_[leg];
  V px=p,py=p;px[0]+=1e-3;py[0]-=1e-3;
  double dir=fore_target_headroom_at(leg,e,px)>=fore_target_headroom_at(leg,e,py)?+1.:-1.;
  double dmax=fore_L1_+fore_rho_;
  double lo=0,hi=2.*dmax;
  for(int j=0;j<42;++j){double mid=(lo+hi)/2;V t=p;t[0]+=dir*mid;
   if(fore_D_at(leg,e,t)<dmax)lo=mid;else hi=mid;}
  V edge={p[0]+dir*((lo+hi)/2),p[1],p[2]};
  fore_hold_off_[leg]=V{edge[0]-sh[0],edge[1]-sh[1],edge[2]-sh[2]};
  size_t c1=fore_coord_[leg][0],c2=fore_coord_[leg][1];
  int last=0;
  for(int k=1;k<=n;++k){
   double s=double(k)/double(n);V t{};
   for(int i=0;i<3;++i)t[i]=swing_from_[leg][i]+(swing_to_[leg][i]-swing_from_[leg][i])*s;
   ForeIK ik=fore_ik_at(leg,e,t);
   if(ik.q1_raw<model_->lower[c1]||ik.q1_raw>model_->upper[c1]||
      ik.q2_raw<model_->lower[c2]||ik.q2_raw>model_->upper[c2])last=k;}
  if(last>0){fore_glide_hold_[leg]=1;fore_hold_last_[leg]=last;}
#ifdef GAIT_EVENT_TRACE
  std::fprintf(stderr,"[foreclk] hold leg=%zu tick=%llu armed=%d last=%d off=(%.6f,%.6f)\n",
   leg,(unsigned long long)ticks_,fore_glide_hold_[leg],fore_hold_last_[leg],
   fore_hold_off_[leg][0],fore_hold_off_[leg][1]);
#endif
 }
 // THE HELD GLIDE predicate (wave 25, receipt_wave25.json): the pocket-clear
 // hold's pads-live span -- EXACTLY the held branch of the glide target update
 // below, factored so the gate and the target update read one truth. During
 // the held ticks the target is the body-locked annulus-edge seat ON THE
 // GROUND LINE: the pads stay live (the wave-24 measured held gaps
 // 1e-6..3e-6, in-band, touching; support measured min 3 through every hold),
 // so a held glide is NOT a swing in the contact sense -- it spends no
 // support and must not consume the other leg's swing calendar.
 bool fore_glide_held(size_t leg)const{
  return fore_glide_hold_[leg]!=0&&fore_t_[leg]<fore_hold_last_[leg]&&fore_t_[leg]+1.<fore_cycle_[leg];}
 // THE PLANT CAPTURE (per leg; wave 13 refactor): freeze the paw's world
 // (model-frame) position as the target, pick the IK branch that matches the
 // planted configuration, and measure the analytic closure round-trip (FK of
 // the solution must rebuild the paw). Called at the settle entry AND at every
 // fore TD re-plant.
 void capture_paw(size_t leg,const Evaluation& e){
  auto pw=e.point(points_[fore_paw_point_[leg]].index,paw_ref_local_[leg]).first;
  paw_target_[leg]=pw;
  double err[2]={0.,0.};ForeIK sol[2]{{0,0,false},{0,0,false}};
  for(int b=0;b<2;++b){ik_branch_[leg]=b==0?1:-1;sol[b]=fore_ik(leg,e);
   err[b]=std::hypot(sol[b].q1-s_.q[fore_coord_[leg][0]],sol[b].q2-s_.q[fore_coord_[leg][1]]);}
  ik_branch_[leg]=err[0]<=err[1]?1:-1;
  const ForeIK&ik=sol[err[0]<=err[1]?0:1];
  ik_qerr_[leg]=(std::min)(err[0],err[1]);
  // Closure round-trip, end to end: FK the solution in the pelvis frame and
  // map the paw back to the WORLD frame -- it must rebuild the target.
  {const Mat& T=e.frames[fore_mount_body_[leg]].t;
   double q12=ik.q1+ik.q2,r0=paw_ref_local_[leg][0],r1=paw_ref_local_[leg][1];
   double ex=fore_L1_*std::sin(ik.q1)+r0*std::cos(q12)-r1*std::sin(q12);
   double ey=-fore_L1_*std::cos(ik.q1)+r0*std::sin(q12)+r1*std::cos(q12);
   const V& m=fore_mount_local_[leg];
   double lx=m[0]+ex,ly=m[1]+ey,lz=m[2]; // paw in pelvis coordinates
   double fx=T(0,0)*lx+T(0,1)*ly+T(0,2)*lz+T(0,3);
   double fy=T(1,0)*lx+T(1,1)*ly+T(1,2)*lz+T(1,3);
   ik_roundtrip_m_[leg]=std::hypot(fx-pw[0],fy-pw[1]);}
#ifdef GAIT_EVENT_TRACE
  std::fprintf(stderr,"[pawcap] leg=%zu td=%d paw=(%.9f,%.9f) branch=%+d qerr=%.3e rad roundtrip=%.3e m\n",
   leg,fore_td_[leg],pw[0],pw[1],ik_branch_[leg],ik_qerr_[leg],ik_roundtrip_m_[leg]);
#endif
 }
 void capture_paws(){
  auto e=evaluate(s_);
  for(size_t leg=0;leg<2;++leg)capture_paw(leg,e);
  paws_captured_=true;
  arm_fore_clock(e);} // THE STEPPING-STRUT CLOCK (wave 13): armed at the entry capture
 // ── THE REPLANT LAW (wave 13, receipt derivation) ──
 double fore_xoff()const{ // x_off = v * t_stance/2 at the CURRENT measured speed
  return (std::max)(0.,s_.v[3])*(DUTY_SAMPLED*T_CYCLE)/2.;}
 double fore_amax(const Evaluation& e,size_t leg)const{ // horizontal reach envelope at plant height
  auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
  double h=(std::max)(0.,sh[1]-paw_plant_y_[leg]),d=fore_L1_+fore_rho_,a2=d*d-h*h;
  return a2>0.?std::sqrt(a2):0.;}
 // THE MID-ENTRY RE-PLANT STANCE (wave 20, receipt_wave20.json): the derived
 // re-plant point tau1 = max(0, tau_env - (t_air + g)) in TICKS, evaluated on
 // the FRESH measured state at the arm and at every entry TD. t_air =
 // ceil((T_CYCLE-DUTY_SAMPLED)/dt_) = ceil(8.1) = 9 ticks -- the machinery's
 // OWN nominal ground-level step (the converged clock's swing); g = 1 tick --
 // the clock quantum, the support-hand-off clearance (windows >= 1 tick apart
 // are disjoint by construction; the census crime is an overlap >= 2). THE
 // COVERAGE CLOSURE (pre-registered): 9 <= tau_env(other) - tau1(this) - g =
 // 9.146 at the measured settle-exit state -- two independent derivations of
 // the same number agreeing to 0.15 ticks is what fixes t_air, not a choice.
 double fore_env_ticks(size_t leg,const Evaluation& e)const{ // the receding-side envelope tau_env, ticks
  auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
  double off=paw_target_[leg][0]-sh[0],amax=fore_amax(e,leg),v=(std::max)(0.,s_.v[3]);
  if(v<=1e-9)return 0.;
  return (std::max)(0.,(amax+off-v*dt_)/v/dt_);}
 double fore_entry_stance_ticks(size_t leg,const Evaluation& e)const{
  return (std::max)(0.,fore_env_ticks(leg,e)-((std::ceil)((T_CYCLE-DUTY_SAMPLED)/dt_)+1.));}
 // Re-arm the entry stance/cycle from the FRESH measured state (the arm and
 // every entry re-plant): tau1 = max(0, tau_env - (t_air + g)), cycle = tau1 + t_air.
 void fore_entry_stance_rearm(size_t leg,const Evaluation& e){
  fore_stance_[leg]=(std::max)(0.,fore_entry_stance_ticks(leg,e));
  fore_cycle_[leg]=fore_stance_[leg]+(std::ceil)((T_CYCLE-DUTY_SAMPLED)/dt_);}
 // ARM (entry, WAVE 14 LAW): the capture is a TOUCHDOWN plant -- the scene
 // statics derivation (derive_entry_pose.py) seats the paws at/under the
 // stepping law's symmetric offset, so the entry stance is timed by the
 // LATERAL-SEQUENCE LIFT GRID, not by the capture geometry: the fore lift =
 // same-side hind lift + T/4, read ONCE from the hind clock at the arm (the
 // hind entry phases are {0, 0.5}: RF ~92.2 ticks, LF ~198.7 -- the first
 // lifts land ON the steady lift slots, ~T/2 apart, swings disjoint). The
 // bound is the annulus HOLD time tau_env = (a + off0 - v*dt)/v -- the
 // RECEDING-side bound, the single formula valid for either capture sign
 // (wave 13's (a-|off0|-v*dt)/v is its off0<0 form; from an AHEAD capture
 // the shoulder walks ONTO the plant before the offset recedes, so the old
 // form would cut a legal stance). The wave-13 duty cap is DISSOLVED: the
 // grid-derived LF stance lawfully exceeds one duty because the capture is
 // at the touchdown offset; the envelope remains the guard. RUN-2 BANKED
 // WHY: the wave-13 behind-pose entry (tau_sym form) lifted BOTH paws within
 // 3.8 ticks and the walk died at 120 of support starvation.
 void arm_fore_clock(const Evaluation& e){
  double Tf=T_CYCLE/dt_;
  double tair=std::ceil((T_CYCLE-DUTY_SAMPLED)/dt_); // the nominal step (wave 20): ceil(8.1) = 9 ticks
  for(size_t leg=0;leg<2;++leg){
   paw_plant_y_[leg]=paw_target_[leg][1];
   auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
   double off=paw_target_[leg][0]-sh[0],xoff=fore_xoff(),tau1=0.;
   double amax=fore_amax(e,leg),v=(std::max)(0.,s_.v[3]);
   if(off<0.&&v>1e-9){ // THE MID-ENTRY RE-PLANT (wave 20): the BEHIND-capture
    // regime. The derived re-plant point (tau1 = max(0, tau_env - (t_air+g)))
    // supersedes the grid lift-wait here -- the grid slots are unreachable
    // from a behind capture (92.3/198.8 ticks vs tau_env 9-11), which is
    // exactly the wave-19 measured starvation.
    fore_entry_[leg]=1;
    tau1=(std::max)(0.,fore_entry_stance_ticks(leg,e))*dt_;}
   else if(xoff>0.&&v>1e-9){
    double lift_wait=(std::max)(0.,(DUTY_SAMPLED-phi_[leg]))*T_CYCLE+0.25*T_CYCLE;
    double tau_env=(amax+off-v*dt_)/v;
    if(tau_env<0.)tau_env=0.;
    tau1=(std::min)(lift_wait,tau_env);}
   // RUN-2 REPAIR (wave 15, itemized in receipt_wave15.json): the wave-14
   // commit changed tau1 from cycle fractions (wave 13: capped at
   // DUTY_SAMPLED, so tau1*Tf was ticks) to SECONDS but kept the *Tf
   // (ticks-per-CYCLE) multiply -- the entry stances ran at 213/300 of the
   // derived lengths (measured: stance 65.483 = 0.30743 s *213 exactly, the
   // law's 92.23 ticks). Seconds -> ticks is *1/dt_; latent through wave 14
   // because its clock never armed (paws_captured=0). No tuning: this
   // enforces the already-derived lift slots (RF 92.23, LF 198.73).
   fore_stance_[leg]=tau1/dt_;
   fore_cycle_[leg]=fore_stance_[leg]+(fore_entry_[leg]?tair:(1.-DUTY_SAMPLED)/dt_);
   fore_t_[leg]=0.;fore_mode_[leg]=0;fore_td_[leg]=0;fore_replants_[leg]=0;fore_clamped_[leg]=0;
   fore_conv_[leg]=0;
#ifdef GAIT_EVENT_TRACE
   std::fprintf(stderr,"[foreclk] arm leg=%zu tick=%llu offset0=%+.6f xoff=%.6f amax=%.6f stance=%.3f ticks cycle=%.3f entry=%d tau_env=%.3f\n",
    leg,(unsigned long long)ticks_,off,xoff,amax,fore_stance_[leg],fore_cycle_[leg],fore_entry_[leg],
    v>1e-9?(std::max)(0.,(amax+off-v*dt_)/v/dt_):-1.);
#endif
  }}
 // GRID CONVERGENCE (receipt derivation): the entry geometry cannot originate
 // the lateral grid (LF = LH + T/4, RF = RH + T/4), so each UNCONVERGED TD
 // moves the next TD as far toward the leg's lateral slot as the two reach
 // laws allow: a SHORTENING may go down to the duty-1/2 floor
 // (stance >= t_swing -- always envelope-safe); a LENGTHENING is capped by
 // the envelope inequality (plant_offset + a - v*dt)/v. The search walks
 // k = 1..8 split cycles and both circular directions (first feasible wins:
 // fewest cycles, then the short way); a k=1 short-way landing marks the leg
 // CONVERGED (pure clock thereafter). Deterministic; no force thresholds.
 void fore_converge(size_t leg){
  // RUN-2 REPAIR (wave 15, same units fix as arm_fore_clock): swing/stance
  // lengths are seconds * (1/dt_) = ticks; the SLOTS stay in ticks (Tf).
  double Tf=T_CYCLE/dt_,swing=(1.-DUTY_SAMPLED)/dt_;
  double slot0=(double)settle_total_+(leg==0?0.25:0.75)*Tf;
  double now=(double)ticks_;
  double slot=slot0;
  while(slot<=now+swing)slot+=Tf; // the smallest slot the leg can still land
  double d=slot-((double)now+Tf); // shift needed vs the uncorrected clock
  if(std::abs(d)<=0.5){fore_conv_[leg]=1;fore_stance_[leg]=DUTY_SAMPLED/dt_;fore_cycle_[leg]=Tf;
#ifdef GAIT_EVENT_TRACE
   std::fprintf(stderr,"[foreclk] converged leg=%zu tick=%llu slot=%.3f\n",leg,(unsigned long long)ticks_,slot);
#endif
   return;}
  auto e=evaluate(s_);
  auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
  double off=paw_target_[leg][0]-sh[0]; // the just-captured plant offset
  double v=(std::max)(0.,s_.v[3]),env=-1.; // env<0: lengthenings infeasible this cycle
  if(v>1e-9)env=(off+fore_amax(e,leg)-v*dt_)/v/dt_; // ticks (was seconds: mixed-unit compare)
  double smin=swing;
  for(int k=1;k<=8;++k)for(int w=0;w<2;++w){
   double step=(d-(w?Tf:0.))/k;
   double st=DUTY_SAMPLED/dt_+step;
   if(st<smin-1e-9)continue;
   if(step>0.&&(env<0.||st>env+1e-9))continue;
   fore_stance_[leg]=st;fore_cycle_[leg]=st+swing;
   if(k==1&&w==0)fore_conv_[leg]=1;
#ifdef GAIT_EVENT_TRACE
   std::fprintf(stderr,"[foreclk] converge leg=%zu tick=%llu slot=%.3f k=%d w=%d stance=%.3f env=%.3f conv=%d\n",
    leg,(unsigned long long)ticks_,slot,k,w,st,env,fore_conv_[leg]);
#endif
   return;}
  // no lawful correction this cycle: run nominal, retry at the next TD
  fore_stance_[leg]=DUTY_SAMPLED/dt_;fore_cycle_[leg]=Tf;}
 // ── THE HIND STEP LAW's helpers (wave 28) ──
 // The composed paw-MIDPOINT offset from the hip at a clock phase (the
 // scene's own stance-column FK -- the same composed chain the entry
 // derivation seats; engine-validated on this lane against the runtime's
 // own contact geometry at the reset state). The designed column the hind
 // ride is supposed to hold at that phase.
 double hind_off_col(double phi)const{
  double a1=tables_.zeros[0]+Tables::interp(tables_.hip,phi);
  double a2=a1+tables_.zeros[1]+Tables::interp(tables_.knee,phi);
  double ap=a2+tables_.zeros[2]+Tables::interp(tables_.ankle,phi);
  return hind_L1_*std::sin(a1)+hind_L2_*std::sin(a2)+hind_xm_*std::cos(ap);}
 // THE HIND STEP IK: the closed-form 2-link solve for the paw-MIDPOINT
 // target (the held composed foot pitch ap places the paw reference
 // xm*cos(ap), xm*sin(ap) off the ankle; the MP is held outright -- the
 // declared hind contact points live on the FOOT body, the MP does not move
 // them). Branch captured at the fire (the knee's sign); the wrist distance
 // clamped to the chain's own annulus (the nearest reachable configuration,
 // the fore_ik pattern: loud in the census, never silent).
 struct HindIKDiag{double wx=0,wy=0,ap=0,D=0,Dc=0,dmax=0,dmin=0;int clamped=0;}; // wave-43 [dvfj]: the solve's own inputs, read-only plumbing
 void hind_step_ik(size_t hl,const Evaluation& e,const V& tgt,double& qh,double& qk,double& qa,HindIKDiag* dg=nullptr)const{
  const Mat& T=e.frames[pelvis_row_].t;
  double rx=tgt[0]-T(0,3),ry=tgt[1]-T(1,3),rz=tgt[2]-T(2,3);
  double dx=T(0,0)*rx+T(1,0)*ry+T(2,0)*rz; // the pelvis-plane x (the hip
  double dy=T(0,1)*rx+T(1,1)*ry+T(2,1)*rz; //  mount sits ON the z-axis: no
  double ap=hind_step_ap_[hl];             //  in-plane correction)
  double wx=dx-hind_xm_*std::cos(ap),wy=dy-hind_xm_*std::sin(ap);
  double D=std::hypot(wx,wy);
  double dmax=hind_L1_+hind_L2_,dmin=std::abs(hind_L1_-hind_L2_);
  double Dc=(std::min)((std::max)(D,dmin+1e-9),dmax*(1.-1e-12));
  if(dg){dg->wx=wx;dg->wy=wy;dg->ap=ap;dg->D=D;dg->Dc=Dc;dg->dmax=dmax;dg->dmin=dmin;dg->clamped=(Dc!=D)?1:0;}
  double ca=(Dc*Dc-hind_L1_*hind_L1_-hind_L2_*hind_L2_)/(2.*hind_L1_*hind_L2_);
  double k=double(hind_step_branch_[hl])*std::acos((std::max)(-1.,(std::min)(1.,ca)));
  double a1=std::atan2(wy,wx)-std::atan2(-hind_L1_-hind_L2_*std::cos(k),hind_L2_*std::sin(k));
  qh=a1;qk=k;qa=ap-a1-k;}
 // THE FORE CLOCK: advances only in the walk (the hind clock's discipline).
 // LIFTOFF at fore_t_ >= fore_stance_: derive the glide (the law's plant point
 // from the CURRENT speed and shoulder position; the annulus clamps the law's
 // own x_off only if the current height has eaten the envelope -- counted,
 // loud). TOUCHDOWN at fore_t_ >= fore_cycle_: re-capture the actual paw,
 // converge/restore the schedule. SWING: the target glides world-linearly
 // under the clearance arch c*sin(pi*s), c = 2*pad radius (pad geometry).
 void update_fore_clock(const Evaluation& e){
  double Tf=T_CYCLE/dt_;
  double tair=std::ceil((T_CYCLE-DUTY_SAMPLED)/dt_); // the nominal step (wave 20): 9 ticks
  for(size_t leg=0;leg<2;++leg){
   fore_t_[leg]+=1.;
   if(fore_mode_[leg]==1){ // glide toward the plant point
    double s=(fore_t_[leg]-fore_stance_[leg])/(fore_cycle_[leg]-fore_stance_[leg]);
    if(s<0.)s=0.;if(s>1.)s=1.;
    double c=2.*points_[fore_paw_point_[leg]].radius;
    // THE POCKET-CLEAR HOLD (wave 24, receipt_wave24.json): during the
    // march's joint-range-exiting span the target is the BODY-LOCKED
    // ANNULUS-EDGE SEAT -- the map's unique above-ground maximum-authority
    // pair (q1u -1.2634 at the wave-23 liftoff state; D held at dmax by
    // the body-lock, the reach never recedes). MEASURED (v2): the
    // follow-seat hold's 0.49 N.m authority LOST the wall fight (the
    // closure pinned both legs' actuals at the wall, 64+14 LOADED pins);
    // the edge seat's 2.18 N.m out-pulls the closure, the actual LEAVES
    // the wall from the hold's first tick (the exit velocity is
    // wall-LEAVING -- the clamp's precondition, a wallward crossing, is
    // structurally dead). The release (the map's exit or the TD's eve)
    // resumes the standard bytes below.
    if(fore_glide_held(leg)){
     auto shh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
     paw_target_[leg]=V{shh[0]+fore_hold_off_[leg][0],shh[1]+fore_hold_off_[leg][1],shh[2]+fore_hold_off_[leg][2]};
    }else{
    for(int i=0;i<3;++i)paw_target_[leg][i]=swing_from_[leg][i]+(swing_to_[leg][i]-swing_from_[leg][i])*s;
    paw_target_[leg][1]+=c*std::sin(pi*s);
    }
    // THE GLIDE-ENTRY HOLD [REJECTED, mined v8]: holding this target at the
    // admissible seat while the pads remain in the band was built to stop
    // the tick-84 glide-transit clamp; it measured WORSE -- the R's pads hug
    // the band deep into the swing, the held target prevented the very
    // unload that clears them, the sustained crush drove its deflection
    // past the restore (h=0.000000 at 76, 73 loaded pins, the refusal back
    // at 82). The pocket-clear hold (wave 24) owns the transit now: the
    // hold that CLEARS (the lift), body-locked (the reach), released at
    // the map's exit -- derived, not tuned.
   }
   if(fore_mode_[leg]==0&&fore_t_[leg]>=fore_stance_[leg]){ // LIFTOFF
    size_t o=leg==0?1:0;
    // THE JOINT-ADMISIBLE HOLD's trigger (wave 23): the ACTUAL joints' wall
    // headroom at or below the deflection envelope makes the leg's liftoff
    // DUE regardless of its schedule -- the forward re-plant request, which
    // the standing no-double-swing gate below arbitrates exactly as always.
    // Counted every stance tick (the census), acted on only when true.
    bool wall_bound=fore_wall_headroom(leg)<=kWallMargin;
    if(wall_bound)++fore_wall_bound_[leg];
    // THE NO-DOUBLE-SWING GATE (wave 20): an entry leg may not begin its step
    // while the other fore is airborne, while the other entry fore's plant is
    // younger than the hand-off clearance g (windows >= 1 tick apart are
    // disjoint by construction), or while the other entry fore is PENDING
    // (its stance expired) and holds PRIORITY -- the pending leg whose PLANT
    // IS OLDER (larger fore_t_ since its last plant; the clock quantity),
    // equal ages breaking to the MORE RECEDED plant. Deterministic total
    // order, no deadlock. THE STAGGER IS THE GATE: the entry offsets differ
    // by 4.8 mm = 7.9 ticks, so no offset trigger can separate the steps
    // (7.9 < t_air + g); the support hand-off does.
    // THE WAVE-23 SCOPE OF CLAUSE (b) (the stall breaker, from the clause's
    // own derivation): the hand-off clearance exists so two AIRBORNE windows
    // stay disjoint -- an IN-PLACE re-plant (a wave-20 re-capture or a
    // wave-23 follow) opens NO window (both pads stay down), so the
    // clearance keys on the other leg's last TD plant only. Without this
    // scope the wave-23 follows (which reset fore_t_ like every re-plant)
    // seize the gate mutually: each follow resets the leg's age below g and
    // clause (b) then gates the OTHER leg forever -- the mined fixed-run
    // stall (both fores holding to the budget). Clause (a) -- the other
    // leg AIRBORNE -- is untouched and still forbids every double swing.
    // THE WAVE-25 CONTACT-AWARE SCOPE (receipt_wave25.json, THE GATE'S
    // CADENCE LAW): the gate schedules on CONTACT TRUTH, not phase
    // bookkeeping. Clause (a) gates only a TRUE airborne glide -- the other
    // fore in swing mode AND its pads out of the kTouch band (NOT
    // fore_glide_held: the pocket-clear hold rides the ground line, its
    // pads live, support measured min 3 through every hold -- a held glide
    // spends no support and must not consume the other leg's swing
    // calendar; the wave-24 death held the R off its last window exactly by
    // counting the L's held glides as airborne). Clauses (b) and (c) read
    // STANCE bookkeeping -- the hand-off clearance keys on the other leg's
    // last TD PLANT and the pending priority compares PLANT AGES, both of
    // which exist only in stance mode (mid-glide fore_t_ was reset at the
    // lift: a lift-clock, not a plant-clock) -- so both are scoped to
    // fore_mode_[o]==0. On mode-0 others every condition is byte-identical
    // to the wave-20/23 gate; the gate's total order, the tie-break, and
    // the wave-23 stall breaker are untouched.
    bool gated=false;
    if(fore_entry_[leg]){
     if(fore_mode_[o]==1&&!fore_glide_held(o))gated=true;
     else if(fore_mode_[o]==0&&fore_entry_[o]&&fore_td_plant_[o]&&fore_t_[o]<1.)gated=true;
     else if(fore_mode_[o]==0&&fore_entry_[o]&&fore_t_[o]>=fore_stance_[o]){
      bool o_prior=fore_t_[o]>fore_t_[leg];
      if(fore_t_[o]==fore_t_[leg]){
       auto sha=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
       auto sho=e.point(fore_mount_body_[o],fore_mount_local_[o]).first;
       o_prior=paw_target_[o][0]-sho[0]<paw_target_[leg][0]-sha[0];}
      gated=o_prior;}
     if(gated)++fore_gate_holds_[leg];}
    // THE DEFERRED LIFT (wave 23): a fore leg lifts only from an ADMISSIBLE
    // SEAT -- the target's joint headroom at or above 2*kWallMargin. THE
    // MEASURED SEPARATION (the mining pass): the R's liftoff at tick 71 sat
    // on a 0.111 rad seat and survived its glide (the servo's transient
    // reached the wall only after the pads left the ground -- the airborne
    // wall-touch, no pin), while the R's liftoff at tick 81 sat on a
    // 0.022 rad seat and the glide's first-sweep target (the paw plus
    // ~(to-paw)/9, diving ~0.05 rad through the branch's deep-bend pocket)
    // commanded the LOADED joint onto its stop within the tick (the mined
    // loaded pin). The seat bar is the law's own restore level -- no new
    // constant. A thin-seat leg re-plants IN PLACE instead (the admissible
    // follow below) and lifts on a later tick from the restored seat; the
    // no-double-swing gate above is untouched (clause (a) still forbids
    // every simultaneous swing). THE CONJUNCT (the law's own minimality):
    // the deferral protects a LOADED, WALL-ADJACENT joint -- the transient's
    // victim -- so it fires only when the ACTUAL is also wall-bound
    // (fore_wall_headroom <= kWallMargin). A leg whose actual holds a wide
    // margin has nothing to protect: deferring it would be pure re-timing
    // (the mined L@61: seat 0.102162 -- 3.8e-5 below the bar -- with the
    // actual at 0.0867: lifting is safe by 7x the transient; the mined
    // R@81: seat 0.022 with the actual at 0.0036: both clauses hold and the
    // lift pinned). The wall_bound flag is that clause.
    bool thin_seat=fore_target_headroom_at(leg,e,paw_target_[leg])<2.*kWallMargin;
    bool due=fore_t_[leg]>=fore_stance_[leg]||wall_bound;
    // THE NO-PLANTABLE-RESTORE GUARD (the machinery's own contact band): a
    // seat restore smaller than kTouch (1e-5 m -- the touch quantum, the
    // pad's own position resolution) cannot move the pad and cannot change
    // the transient: a seat within kTouch of the bar IS at the bar, and
    // deferring on it would re-time the solved dance for zero physical
    // effect (the mined L@61 knife-edge: the settle seat 0.102162 vs the
    // bar 0.102200 -- a 2.5 um restore; the lift survivable by 7x the
    // transient).
    if(!gated&&due&&(!thin_seat||!wall_bound)){
     fore_mode_[leg]=1;
     if(fore_entry_[leg])fore_t_[leg]=0.; // the entry air time is EXACTLY t_air (the glide runs 0->1)
    auto pw=e.point(points_[fore_paw_point_[leg]].index,paw_ref_local_[leg]).first;
    auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
    swing_from_[leg]=pw;
    double xoff=fore_xoff();
    double amax=fore_amax(e,leg);
    if(xoff>amax){xoff=amax;++fore_clamped_[leg];}
    swing_to_[leg]=V{sh[0]+xoff,paw_plant_y_[leg],pw[2]};
    fore_glide_arm_hold(leg,e,wall_bound); // THE POCKET-CLEAR HOLD (wave 24)
#ifdef GAIT_EVENT_TRACE
    std::fprintf(stderr,"[foreclk] lift leg=%zu tick=%llu td=%d entry=%d from=(%.6f,%.6f) to=(%.6f,%.6f) xoff=%.6f v=%.6f wall_bound=%d\n",
     leg,(unsigned long long)ticks_,fore_td_[leg],fore_entry_[leg],pw[0],pw[1],swing_to_[leg][0],swing_to_[leg][1],xoff,s_.v[3],wall_bound?1:0);
#endif
    }else if(!gated&&due&&thin_seat&&wall_bound){
     V seat=fore_follow_seat(leg,e);
     if(std::hypot(seat[0]-paw_target_[leg][0],seat[1]-paw_target_[leg][1])<kTouch){
      fore_mode_[leg]=1; // the restore is sub-quantum: the seat IS at the bar; lift
      if(fore_entry_[leg])fore_t_[leg]=0.;
      auto pw=e.point(points_[fore_paw_point_[leg]].index,paw_ref_local_[leg]).first;
      auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
      swing_from_[leg]=pw;
      double xoff=fore_xoff();
      double amax=fore_amax(e,leg);
      if(xoff>amax){xoff=amax;++fore_clamped_[leg];}
      swing_to_[leg]=V{sh[0]+xoff,paw_plant_y_[leg],pw[2]};
      fore_glide_arm_hold(leg,e,wall_bound); // THE POCKET-CLEAR HOLD (wave 24)
     }else{
      paw_target_[leg]=seat;++fore_wall_follows_[leg];
      fore_td_plant_[leg]=false;
      ++fore_replants_[leg];fore_t_[leg]=0.;fore_entry_stance_rearm(leg,e);}
#ifdef GAIT_EVENT_TRACE
     std::fprintf(stderr,"[foreclk] deflift leg=%zu tick=%llu seat_hr=%.6f\n",
      leg,(unsigned long long)ticks_,fore_target_headroom_at(leg,e,paw_target_[leg]));
#endif
     }
    else if(gated&&wall_bound&&fore_wall_headroom(leg)<kWaitFloor){
     // THE WALL-ADJACENT WAIT OVERRIDE (wave 26, receipt_wave26.json): the
     // gate yields to the wall emergency. THE MEASURED DEATH IT OWNS: the
     // wave-25 R's lawful gate-held wait -- the follow restored the TARGET
     // every 2-3 ticks and the ACTUAL dove straight through to hr=0.000000
     // (the loaded deflection GROWS faster than the restore; the follow's
     // convergence premise is measured false under load). THE MECHANISM: the
     // actual has crossed kWaitFloor = 2*kDiveRateMax -- one dive-tick of
     // engage latency plus one dive-tick of standing margin -- so the leg
     // takes its lift NOW through the standard lift bytes; wall_bound=1 arms
     // the POCKET-CLEAR HOLD (the wave-24 map's maximum-authority seat,
     // kp*0.3366 = 2.18 N.m), whose measured face is the ACTUAL healing WITH
     // PADS LIVE (the L's [73,82] heal on the same baseline: 0.037575 ->
     // 0.052603, monotonic from the hold's first engaged tick) -- the held
     // glide rides the GROUND LINE, spends NO support, and the other fore's
     // clause (a) reads it held (a held glide is not a swing). The wave-23
     // thin-seat pin route is closed by the hold arming at the fire: the
     // glide's first-sweep target is the wall-LEAVING edge seat, not the
     // pocket-diving line point. The floor is emergency-scoped (~10.7
     // wall-bound wait ticks of arming delay): in a healthy dance the branch
     // is inert.
     fore_mode_[leg]=1;
     if(fore_entry_[leg])fore_t_[leg]=0.; // the entry air time is EXACTLY t_air (the glide runs 0->1)
     auto pw=e.point(points_[fore_paw_point_[leg]].index,paw_ref_local_[leg]).first;
     auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
     swing_from_[leg]=pw;
     double xoff=fore_xoff();
     double amax=fore_amax(e,leg);
     if(xoff>amax){xoff=amax;++fore_clamped_[leg];}
     swing_to_[leg]=V{sh[0]+xoff,paw_plant_y_[leg],pw[2]};
     fore_glide_arm_hold(leg,e,wall_bound);
     ++fore_wait_fires_[leg];
#ifdef GAIT_EVENT_TRACE
     std::fprintf(stderr,"[foreclk] waitfire leg=%zu tick=%llu hr=%.6f floor=%.6f hold=%d last=%d\n",
      leg,(unsigned long long)ticks_,fore_wall_headroom(leg),kWaitFloor,
      fore_glide_hold_[leg],fore_hold_last_[leg]);
#endif
     }
    else if(fore_t_[leg]>=fore_cycle_[leg]||fore_t_[leg]>=fore_env_ticks(leg,e)){
     // THE IN-PLACE GROUND RE-PLANT (wave 20): the gate-held leg re-plants
     // where it stands -- at its cycle boundary, or at its envelope edge when
     // the plant is too starved to wait that long (never saturates). Zero air
     // time, the OTHER fore planted: the fork's literal 're-plant forward
     // along the ground while keeping the other fore planted'. THE TRIGGER
     // STAYS THE WAVE-20 CYCLE/ENVELOPE EDGE (the mined fence: a wall-bound
     // leg with cycle and envelope still in hand WAITS -- the R's survivable
     // hold [60,66] dove at the same 0.0039 rad/tick as the death but its
     // clock lifted it in time; firing on the headroom alone re-times the
     // solved dance).
     // THE JOINT-ADMISIBLE HOLD's crux clause (wave 23): a WALL-BOUND
     // gate-held leg re-plants not at its raw (deflected) seat but at the
     // admissible follow seat -- the ground-line slide that restores the
     // TARGET's joint headroom to 2*kWallMargin, so the servo's measured
     // deflection (the envelope) can never walk the ACTUAL joint onto its
     // stop while the gate holds the leg past its schedule. The raw
     // re-capture stands when the follow adds nothing (the target already
     // holds twice the envelope).
     bool followed=false;
     if(wall_bound&&fore_target_headroom_at(leg,e,paw_target_[leg])<2.*kWallMargin){
      V seat=fore_follow_seat(leg,e);
      if(std::hypot(seat[0]-paw_target_[leg][0],seat[1]-paw_target_[leg][1])<kTouch)
       capture_paw(leg,e); // a sub-quantum deficit: the raw re-capture stands (wave 20)
      else{paw_target_[leg]=seat;++fore_wall_follows_[leg];followed=true;}
     }
     else capture_paw(leg,e);
     fore_td_plant_[leg]=false; // an in-place re-plant opens no airborne window
     fore_td_plant_[leg]=false; // an in-place re-plant opens no airborne window
     ++fore_replants_[leg];
     fore_t_[leg]=0.;
     fore_entry_stance_rearm(leg,e);
#ifdef GAIT_EVENT_TRACE
     auto pw2=e.point(points_[fore_paw_point_[leg]].index,paw_ref_local_[leg]).first;
     std::fprintf(stderr,"[foreclk] inplace leg=%zu tick=%llu paw=(%.6f,%.6f) stance=%.3f entry=%d follow=%d\n",
      leg,(unsigned long long)ticks_,pw2[0],pw2[1],fore_stance_[leg],fore_entry_[leg],followed?1:0);
#endif
    }
   }
   if(fore_t_[leg]>=fore_cycle_[leg]){ // TOUCHDOWN: re-capture the actual paw
    capture_paw(leg,e);++fore_replants_[leg];++fore_td_[leg];
    fore_t_[leg]=0.;fore_mode_[leg]=0;fore_td_plant_[leg]=true; // the TD opened a window
    fore_glide_hold_[leg]=0;fore_hold_last_[leg]=0; // the hold's span ended with the swing
    // THE MID-ENTRY RE-PLANT re-arm (wave 20): from the FRESH measured
    // envelope; the HAND-OFF clears the regime at the first TD at/ahead of
    // the shoulder (off >= 0 -- the symmetric regime, envelope >= amax/v),
    // where the committed grid convergence takes over byte-identically.
    if(fore_entry_[leg]){
     auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
     if(paw_target_[leg][0]-sh[0]>=0.)fore_entry_[leg]=0;}
    if(fore_entry_[leg])fore_entry_stance_rearm(leg,e);
    else if(fore_conv_[leg]){fore_stance_[leg]=DUTY_SAMPLED/dt_;fore_cycle_[leg]=Tf;}
    else fore_converge(leg); // bounded grid convergence until the slot lands
#ifdef GAIT_EVENT_TRACE
    std::fprintf(stderr,"[foreclk] td leg=%zu tick=%llu td_count=%d entry=%d stance=%.3f roundtrip=%.3e m\n",
     leg,(unsigned long long)ticks_,fore_td_[leg],fore_entry_[leg],fore_stance_[leg],ik_roundtrip_m_[leg]);
#endif
   }
  }}
 Dense servo()const{ // capped mass-normalized PD at the derived 4.0 Hz (Section 5.2)
  Dense tau(n_,0.);
  bool walking=config_["gait_enabled"].get<bool>();
  Evaluation fe{};bool have_fe=false; // the planted-strut IK evaluates the shoulder pose once per call
  for(size_t d=0;d<nd_;++d){const Drive& dr=drives_[d];size_t c=dr.coordinate;
   if(!config_["power"].get<bool>()||!config_[dr.name+"_drive"].get<bool>()||battery_[d]<=1e-12)continue;
   // Stage E -> F handoff: with the clock frozen (gait_enabled=false) the
   // drives hold the MODEL DEFAULTS -- the flat-footed standing pose the
   // seating scan proves supportable -- not the TD columns (a pointe-feet
   // pose is not a static stand). The tables engage with the walk.
   double target=0.;
   if(walking){
    if(dr.leg=="fore_left"||dr.leg=="fore_right"){
     // THE PLANTED STRUT (wave 12): after the settle capture the fore targets
     // are the closed-form IK of the planted paw position (held fixed in the
     // world frame); before the capture the statics pose holds (the quad-share
     // lane's shoulder/elbow solution at the measured fore envelope midpoint).
     size_t leg=dr.leg=="fore_left"?0:1;
     if(paws_captured_){
      if(!have_fe){fe=evaluate(s_);have_fe=true;}
      ForeIK ik=fore_ik(leg,fe);
      auto sh=fe.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
#ifdef GAIT_EVENT_TRACE
      if(ik.saturated&&!ik_sat_prev_[leg]){ik_sat_prev_[leg]=true;
       std::fprintf(stderr,"[ik] leg=%zu tick=%llu SATURATED paw=(%.6f,%.6f) shoulder=(%.6f,%.6f) D=%.6f reach=[%.6f,%.6f]\n",
        leg,(unsigned long long)ticks_,paw_target_[leg][0],paw_target_[leg][1],sh[0],sh[1],
        std::hypot(paw_target_[leg][0]-sh[0],paw_target_[leg][1]-sh[1]),
        std::abs(fore_L1_-fore_rho_),fore_L1_+fore_rho_);}
      else if(!ik.saturated)ik_sat_prev_[leg]=false;
#endif
      target=dr.joint=="shoulder"?ik.q1:ik.q2;
     }
     else target=dr.joint=="shoulder"?fore_pose_sh_:fore_pose_el_;
    }
    // THE HIND TARGET (wave 16 repair, itemized in receipt_wave16.json): the
    // servo read tables_.at(dr.leg=="left"?0:1, ...) -- the CONSTANT column
    // (phi=0 left, phi=1.0==0.0 right): the forelimb commit (f0efbba7) dropped
    // the phase_ read here exactly as it did in reset() (the pre-forelimb
    // bytes read tables_.at(phi_[...]) at all three sites), so the hind legs
    // held the TD pose as a static target through every wave-12..15 walk and
    // the books (status) disagreed with the servo. The phase-advanced target
    // is the derivation's own law (the 21-node tables at the contact-reset
    // clock, Section 2.4/5.1); without it the reset repair below is undone
    // during the settle (the servo would drag the right hind back to the TD
    // column) and no hind lift could fire at its clock phase.
    else {size_t hl=dr.leg=="left"?0:1;
     // THE HIND STEP LAW's glide (wave 28): while the leg steps, the glide
     // target REPLACES the whole hind branch (tables AND the wave-27 ff) --
     // the swing columns' pull (the death's actuator) is structurally
     // removed for the stepping leg; the ff re-engages at the TD.
     if(hind_step_mode_[hl]==1){
      double ta=(std::ceil)((T_CYCLE-DUTY_SAMPLED)/dt_);
      double sg=hind_step_t_[hl]/ta;if(sg<0.)sg=0.;if(sg>1.)sg=1.;
      double c=2.*points_[hind_heel_pt_[hl]].radius;
      V tgt{};
      // THE LIFT-FIRST HOLD (wave 29): while the pads remain inside the
      // release band the target is the LIFTOFT SPOT + THE FULL ARCH -- a
      // static vertical demand: no haul (no drag BY CONSTRUCTION), full
      // servo authority into the lift. The glide clock never stopped: at
      // the release the standard line+arch resumes at the current phase
      // (the fore pocket-clear hold's pattern, hind-side).
      if(hind_step_held_[hl]){
       for(int i2=0;i2<3;++i2)tgt[i2]=hind_step_from_[hl][i2];
       tgt[1]+=c;
      }else{
       for(int i2=0;i2<3;++i2)
        tgt[i2]=hind_step_from_[hl][i2]+(hind_step_to_[hl][i2]-hind_step_from_[hl][i2])*sg;
       tgt[1]+=c*std::sin(pi*sg);
      }
      if(!have_fe){fe=evaluate(s_);have_fe=true;}
#ifdef GAIT_EVENT_TRACE
      if(dr.joint=="hip"){ // WAVE 42 ARCH INSTRUMENT (read-only plumbing, receipt_wave42.json):
       double py=0.5*(fe.point(points_[hind_heel_pt_[hl]].index,points_[hind_heel_pt_[hl]].local).first[1]
        +fe.point(points_[hind_mp_pt_[hl]].index,points_[hind_mp_pt_[hl]].local).first[1]);
       std::fprintf(stderr,"[dvfa] t=%llu leg=%zu br=%c held=%d sg=%.5f c=%.5f cmd_y=%.9f pad_y=%.9f plant_y=%.9f\n",
        (unsigned long long)ticks_,hl,hind_step_held_[hl]?'h':'g',hind_step_held_[hl]?1:0,sg,c,tgt[1],py,
        hind_step_plant_y_[hl]);} // the hold command vs the delivered pad y, one line per leg per tick
#endif
#ifdef GAIT_EVENT_TRACE
      if(dr.joint=="hip"){ // WAVE 43 IK-ABSORPTION INSTRUMENT (read-only plumbing, receipt_wave43.json):
       double dgh,dgk,dga;HindIKDiag dg;hind_step_ik(hl,fe,tgt,dgh,dgk,dga,&dg);
       const Mat& Tp=fe.frames[pelvis_row_].t;
       double cp=std::cos(dg.ap),sp=std::sin(dg.ap);
       double solx=Tp(0,3)+dg.wx*Tp(0,0)+dg.wy*Tp(0,1)+hind_xm_*(cp*Tp(0,0)+sp*Tp(0,1));
       double soly=Tp(1,3)+dg.wx*Tp(1,0)+dg.wy*Tp(1,1)+hind_xm_*(cp*Tp(1,0)+sp*Tp(1,1));
       std::fprintf(stderr,"[dvfj] t=%llu leg=%zu br=%c brn=%+d ap=%.9f qh=%.9f qk=%.9f qa=%.9f mp=%.9f ah=%.9f ak=%.9f aa=%.9f amp=%.9f D=%.9f Dc=%.9f dmax=%.9f clmp=%d sol_x=%.9f sol_y=%.9f\n",
        (unsigned long long)ticks_,hl,hind_step_held_[hl]?'h':'g',hind_step_branch_[hl],dg.ap,dgh,dgk,dga,
        hind_step_mp_[hl],s_.q[hind_coord_[hl][0]],s_.q[hind_coord_[hl][1]],s_.q[hind_coord_[hl][2]],
        s_.q[hind_coord_[hl][3]],dg.D,dg.Dc,dg.dmax,dg.clamped,solx,soly);} // the IK's own solve vs the actuals: WHERE the +8 mm demand goes
#endif
      double qh,qk,qa;hind_step_ik(hl,fe,tgt,qh,qk,qa);
      target=dr.joint=="hip"?qh:dr.joint=="knee"?qk:dr.joint=="ankle"?qa:hind_step_mp_[hl];
     }else{
     // THE STAND-FIRST HOLD (wave 33): the carrier's pads are pinned at the
     // spots captured at the arm tick -- the same whole-branch replacement
     // the wave-29 glide hold makes (the designed stance tables AND the
     // wave-27 ff both displaced): the unloaded columns cannot lift the pad.
     if(hind_step_stand_[hl]){
      if(!have_fe){fe=evaluate(s_);have_fe=true;}
      V stgt=hind_step_stand_from_[hl];stgt[1]=hind_step_stand_y_[hl];
#ifdef GAIT_EVENT_TRACE
      if(dr.joint=="hip"){ // WAVE 42 ARCH INSTRUMENT: the stand-first hold's command (the arm-tick y anchor)
       double py=0.5*(fe.point(points_[hind_heel_pt_[hl]].index,points_[hind_heel_pt_[hl]].local).first[1]
        +fe.point(points_[hind_mp_pt_[hl]].index,points_[hind_mp_pt_[hl]].local).first[1]);
       std::fprintf(stderr,"[dvfa] t=%llu leg=%zu br=%c held=%d sg=%.5f c=%.5f cmd_y=%.9f pad_y=%.9f plant_y=%.9f\n",
        (unsigned long long)ticks_,hl,'d',0,0.,2.*points_[hind_heel_pt_[hl]].radius,stgt[1],py,
        hind_step_plant_y_[hl]);}
#endif
      double qh,qk,qa;hind_step_ik(hl,fe,stgt,qh,qk,qa);
#ifdef GAIT_EVENT_TRACE
      if(dr.joint=="hip"){ // WAVE 44 FIRE-GATE INSTRUMENT (read-only plumbing, receipt_wave44.json): the stance-side gap build
       std::fprintf(stderr,"[dvfk] t=%llu leg=%zu br=d phi=%.9f qh=%.9f qk=%.9f qa=%.9f ah=%.9f ak=%.9f aa=%.9f stag=%llu oth=%d dl=%llu\n",
        (unsigned long long)ticks_,hl,phi_[hl],qh,qk,qa,
        s_.q[hind_coord_[hl][0]],s_.q[hind_coord_[hl][1]],s_.q[hind_coord_[hl][2]],
        (unsigned long long)hind_step_stand_ticks_[hl],(int)hind_step_mode_[1-hl],
        (unsigned long long)hind_step_deadline_tick_[hl]);} // the pinned solve vs the actuals: WHERE the next fire gap comes from
#endif
      target=dr.joint=="hip"?qh:dr.joint=="knee"?qk:dr.joint=="ankle"?qa:hind_step_stand_mp_[hl];
     }else{
     double qstar[4];tables_.at(phi_[hl],qstar);
     target=qstar[dr.joint=="hip"?0:dr.joint=="knee"?1:dr.joint=="ankle"?2:3];
     // THE HIND EXTENSION LAW (wave 27, receipt_wave27.json): the height
     // emergency's feed-forward -- the drive's OWN last applied tick-mean
     // torque over its OWN mass-normalized gain (the wave-23 equilibrium
     // identity: the actual returns to the designed pose, where the wave-8
     // load book closes). Pads-live drives only: a leg whose pads leave,
     // swings; it resumes at the next TD. No gain bytes change. The torque
     // is read at the drive's COORDINATE row (last_torque_ is n_-indexed).
     if(hind_height_hold_latched_&&touching_prev_[hl])
      target+=last_torque_[c]/kp_[d];
#ifdef GAIT_EVENT_TRACE
     if(dr.joint=="hip"){ // WAVE 42 ARCH INSTRUMENT: the stance tables (joint-space, no world command --
      if(!have_fe){fe=evaluate(s_);have_fe=true;} // cmd_y carries the declared print-only -1 sentinel)
       double py=0.5*(fe.point(points_[hind_heel_pt_[hl]].index,points_[hind_heel_pt_[hl]].local).first[1]
        +fe.point(points_[hind_mp_pt_[hl]].index,points_[hind_mp_pt_[hl]].local).first[1]);
       std::fprintf(stderr,"[dvfa] t=%llu leg=%zu br=%c held=%d sg=%.5f c=%.5f cmd_y=%.9f pad_y=%.9f plant_y=%.9f\n",
        (unsigned long long)ticks_,hl,'t',0,0.,2.*points_[hind_heel_pt_[hl]].radius,-1.,py,
        hind_step_plant_y_[hl]);}
     if(dr.joint=="hip"){ // WAVE 44 FIRE-GATE INSTRUMENT (read-only plumbing, receipt_wave44.json): the stance-side gap build
      std::fprintf(stderr,"[dvfk] t=%llu leg=%zu br=t phi=%.9f qh=%.9f qk=%.9f qa=%.9f ah=%.9f ak=%.9f aa=%.9f stag=%llu oth=%d dl=%llu\n",
       (unsigned long long)ticks_,hl,phi_[hl],qstar[0],qstar[1],qstar[2],
       s_.q[hind_coord_[hl][0]],s_.q[hind_coord_[hl][1]],s_.q[hind_coord_[hl][2]],
       (unsigned long long)hind_step_stand_ticks_[hl],(int)hind_step_mode_[1-hl],
       (unsigned long long)hind_step_deadline_tick_[hl]);} // the tables pose vs the actuals: WHERE the next fire gap comes from
#endif
     }}}}

   tau[c]=(std::max)(-dr.cap,(std::min)(dr.cap,kp_[d]*(target-s_.q[c])-kd_[d]*s_.v[c]));}
  // The source model's POSTURE CONTROL (the pinned fulltext: the trunk pitch
  // theta_HAT is a model DOF driven by hip uniarticular muscles -- iliopsoas
  // and gluteus medius -- as one-sided reflexes toward the trunk target):
  // realized as the same mass-normalized PD on the trunk pitch toward the
  // model's authored erect default (zero), capped at the hip moment (the same
  // musculature carries the trunk moment). Active whenever the power is on:
  // it is what makes stage E's stand a stand.
  if(config_["power"].get<bool>()&&config_["posture_drive"].get<bool>()&&battery_post_>1e-12){
   // The trunk-vault membrane (wave 8): the trunk pitch is a LOAD-BEARING
   // DOF -- the posture target tracks theta*(phi) from the continuous,
   // 0.5-periodic vault table while the walk runs; frozen clock (including
   // the main branch's settle window) holds the authored erect default 0.
   // WAVE 15: the activation is the post_amp() law -- the legacy wave-10 ramp,
   // or the level-entry first-cycle hand-off when the scene authors it.
   double trunk_amp=post_amp();
   double target_post=trunk_amp*tables_.trunk_target(phi_[0]);
   tau[2]=(std::max)(-drives_[0].cap,(std::min)(drives_[0].cap,kp_post_*(target_post-s_.q[2])-kd_post_*s_.v[2]));}
  return tau;}
 // ── walker runtime (the free-root laws, n generalization) ──
 Rate rate(const State& s,const Dense& tau,const std::vector<char>& live,const std::vector<char>& plane)const{
  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);
  V push{number(config_["push_N"]),0,0};auto external=e.force(0,V{},push); // pelvis = body 0 origin
  Dense rhs(n_,0.);double heat=0;
  for(size_t i=0;i<n_;++i){rhs[i]=e.gravity[i]-e.bias[i]+external[i];
   bool joint=false;for(size_t d=0;d<nd_;++d)if(drives_[d].coordinate==i)joint=true;
   if(joint){size_t d=0;for(;d<nd_;++d)if(drives_[d].coordinate==i)break;
    rhs[i]+=tau[i]-damping_[d]*s.v[i];heat+=damping_[d]*s.v[i]*s.v[i];}}
  auto free=multiply(inv,rhs);
  Rate out(n_,npts_);out.damping=heat;out.q=s.v;out.v=free;
  auto joint=normals(s);bool stop=false;std::vector<NamedRow> rows;
  for(size_t d=0;d<nd_;++d){size_t c=drives_[d].coordinate;if(joint[c]&&std::abs(s.v[c])<=1e-9){Dense r(n_,0.);r[c]=joint[c];rows.push_back({r,0.,-1,true});stop=true;}}
  double gate=1e-6+1e-3*joint_speed_scale(s);
  std::vector<char> touching(npts_,0);std::vector<Dense> rown(npts_);
  for(size_t k=0;k<npts_;++k){rown[k]=contact_row(e,k);
   touching[k]=plane[k]||(live[k]&&gap_of(e,k)<=kTouch&&inner(rown[k],s.v)<=gate);}
  bool friction=contact_&&mu_>0;
  if(friction&&!stop){
   for(size_t k=0;k<npts_;++k){
    if(!sole_representative(k)||!touching[k])continue;
    auto j_t1=tangent_row(e,k,0),j_t2=tangent_row(e,k,2);
    V bias=contact_bias(e,k);
    V slip_v{};for(size_t i=0;i<n_;++i){slip_v[0]+=j_t1[i]*s.v[i];slip_v[2]+=j_t2[i]*s.v[i];}
    Dense row_t(n_,0.);double slip_sign=0,slip_speed=0,dir_x=0,dir_z=0;
    double planar=std::hypot(slip_v[0],slip_v[2]);
    if(planar>kSlip){dir_x=slip_v[0]/planar;dir_z=slip_v[2]/planar;slip_sign=1;slip_speed=planar;}
    else{double d1=bias[0],d2=bias[2];for(size_t i=0;i<n_;++i){d1+=j_t1[i]*free[i];d2+=j_t2[i]*free[i];}
     double accel=std::hypot(d1,d2);if(accel>1e-9){dir_x=d1/accel;dir_z=d2/accel;slip_sign=1;}}
    if(dir_x==0&&dir_z==0)continue;
    for(size_t i=0;i<n_;++i)row_t[i]=dir_x*j_t1[i]+dir_z*j_t2[i];
    try{Dense force;double lambda_n,lambda_t;int mode;
     friction_solve(free,inv,rown[k],row_t,-bias[1],-(dir_x*bias[0]+dir_z*bias[2]),mu_,slip_sign,force,lambda_n,lambda_t,mode);
     if(mode){auto correction=multiply(inv,force);
      out.point_force[k].assign(n_,0.);for(size_t i=0;i<n_;++i){free[i]+=correction[i];out.point_force[k][i]=force[i];}
      out.contact_lambda[k]=lambda_n;out.friction_lambda[k]=lambda_t;out.slip[k]=slip_speed;out.mode[k]=mode;
      out.friction_heat[k]=-lambda_t*inner(row_t,s.v);}}
    catch(const Refusal&){}}}
  for(size_t k=0;k<npts_;++k){
   if(!sole_representative(k)||!touching[k])continue;
   Dense rn=contact_row(e,k);
   double floor_k=-contact_bias(e,k)[1];
   if(out.mode[k]&&inner(rn,free)>=floor_k-1e-9)continue;
   rows.push_back({rn,floor_k,int(k),false});}
  if(!rows.empty()){std::vector<Dense> plain;Dense plainfloors;size_t n_stops=0;for(auto&r:rows){plain.push_back(r.row);plainfloors.push_back(r.floor);if(r.stop_row)++n_stops;}
   std::vector<double> multipliers;auto p=project_rows(free,inv,plain,plainfloors,&multipliers,n_stops);auto correction=multiply(inv,p);
   for(size_t i=0;i<n_;++i){free[i]+=correction[i];out.reaction[i]=p[i];}
   for(size_t r=0;r<rows.size();++r)if(!rows[r].stop_row)out.contact_lambda[rows[r].point]=(std::max)(out.contact_lambda[rows[r].point],multipliers[r]);}
  out.v=free;
  return out;}
 State free_step(const State& start,double h,const Dense& tau,const std::vector<char>& live)const{
  auto shifted=[&](const Rate& d,double t){State x=start;for(size_t i=0;i<n_;++i){x.q[i]+=d.q[i]*t;x.v[i]+=d.v[i]*t;}return x;};
  std::vector<char> plane(npts_,0);
  if(contact_&&mu_>0){auto e0=evaluate(start);double gate=1e-6+1e-3*joint_speed_scale(start);
   for(size_t k=0;k<npts_;++k)if(sole_representative(k)&&live[k]&&gap_of(e0,k)<=kTouch&&inner(contact_row(e0,k),start.v)<=gate)plane[k]=1;}
  auto a=rate(start,tau,live,plane),b=rate(shifted(a,h/2),tau,live,plane),c=rate(shifted(b,h/2),tau,live,plane),d=rate(shifted(c,h),tau,live,plane);
  State end=start;
  for(size_t i=0;i<n_;++i){end.q[i]+=h*(a.q[i]+2*b.q[i]+2*c.q[i]+d.q[i])/6;end.v[i]+=h*(a.v[i]+2*b.v[i]+2*c.v[i]+d.v[i])/6;
   double di=h*(a.reaction[i]+2*b.reaction[i]+2*c.reaction[i]+d.reaction[i])/6;
   end.impulse[i]+=di;
   end.constraint_work+=di*(start.v[i]+end.v[i])/2; // E8: the discrete constraint power -- booked, never silent
   end.work[i]+=tau[i]*(end.q[i]-start.q[i]);}
  for(size_t k=0;k<npts_;++k){
   for(size_t i=0;i<n_;++i)end.contact_generalized[i]+=h*((a.point_force[k].empty()?0.:a.point_force[k][i])+2*(b.point_force[k].empty()?0.:b.point_force[k][i])+2*(c.point_force[k].empty()?0.:c.point_force[k][i])+(d.point_force[k].empty()?0.:d.point_force[k][i]))/6;
   end.contact_force_impulse[k]+=h*(a.contact_lambda[k]+2*b.contact_lambda[k]+2*c.contact_lambda[k]+d.contact_lambda[k])/6;
   end.friction_heat[k]+=h*(a.friction_heat[k]+2*b.friction_heat[k]+2*c.friction_heat[k]+d.friction_heat[k])/6;
   end.friction_heat_tick[k]+=h*(a.friction_heat[k]+2*b.friction_heat[k]+2*c.friction_heat[k]+d.friction_heat[k])/6;
   end.friction_force_impulse[k]+=h*(a.friction_lambda[k]+2*b.friction_lambda[k]+2*c.friction_lambda[k]+d.friction_lambda[k])/6;}
  end.damping+=h*(a.damping+2*b.damping+2*c.damping+d.damping)/6;
  V push{number(config_["push_N"]),0,0};
  auto p0=vector(evaluate(start).frames[0].t,V{},1),p1=vector(evaluate(end).frames[0].t,V{},1);
  end.external+=push[0]*(p1[0]-p0[0]);
  return end;}
 double impact(State& s)const{
  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);
  std::vector<NamedRow> rows;auto joint=normals(s);
  for(size_t d=0;d<nd_;++d){size_t c=drives_[d].coordinate;if(joint[c]){Dense r(n_,0.);r[c]=joint[c];rows.push_back({r,0.,-1,true});}}
  std::vector<char> touching(npts_,0);std::vector<Dense> rown(npts_);
  for(size_t k=0;k<npts_;++k){rown[k]=contact_row(e,k);touching[k]=contact_&&gap_of(e,k)<=kTouch;}
  double caught=0;
  std::vector<char> engaged(npts_,0);
  if(contact_&&mu_>0&&rows.empty()){
   for(size_t k=0;k<npts_;++k){
    if(!sole_representative(k)||!touching[k])continue;
    auto j_t1=tangent_row(e,k,0),j_t2=tangent_row(e,k,2);
    V slip_v{};for(size_t i=0;i<n_;++i){slip_v[0]+=j_t1[i]*s.v[i];slip_v[2]+=j_t2[i]*s.v[i];}
    Dense rown_k=rown[k];double closing=inner(rown_k,s.v);if(closing>-1e-12)continue;
    double planar=std::hypot(slip_v[0],slip_v[2]);if(planar<=kSlip)continue;
    Dense row_t(n_,0.);for(size_t i=0;i<n_;++i)row_t[i]=(slip_v[0]*j_t1[i]+slip_v[2]*j_t2[i])/planar;
    try{Dense force;double lambda_n,lambda_t;int mode;
     friction_solve(s.v,inv,rown[k],row_t,0,0,mu_,1,force,lambda_n,lambda_t,mode);
     if(mode){auto change=multiply(inv,force);double before=.5*inner(s.v,multiply(e.mass,s.v));
      Dense mean(n_);for(size_t i=0;i<n_;++i){mean[i]=s.v[i]+change[i]/2;s.v[i]+=change[i];s.impulse[i]+=force[i];}
      double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"gait_impact_created_energy");
      double share_n=lambda_n*inner(rown[k],mean),share_t=lambda_t*inner(row_t,mean);
      require(share_n<=1e-11&&share_t<=1e-11,"gait_contact_impact_gain");
      s.impact+=(std::max)(0.,loss+share_n+share_t);
      s.contact_impact[k]+=(std::max)(0.,-share_n);s.contact_impact_impulse[k]+=lambda_n;
      s.friction_heat[k]+=(std::max)(0.,-share_t);s.friction_impulse[k]+=std::abs(lambda_t);
      caught=(std::max)(caught,lambda_n);engaged[k]=1;}}
    catch(const Refusal&){}}}
  for(size_t k=0;k<npts_;++k)if(sole_representative(k)&&touching[k])rows.push_back({rown[k],0.,int(k),false});
  if(!rows.empty()){std::vector<Dense> plain;Dense plainfloors;size_t n_stops=0;for(auto&r:rows){plain.push_back(r.row);plainfloors.push_back(r.floor);if(r.stop_row)++n_stops;}
   std::vector<double> multipliers;auto p=project_rows(s.v,inv,plain,plainfloors,&multipliers,n_stops);auto change=multiply(inv,p);
   double before=.5*inner(s.v,multiply(e.mass,s.v));Dense mean(n_);
   for(size_t i=0;i<n_;++i){mean[i]=s.v[i]+change[i]/2;s.v[i]+=change[i];s.impulse[i]+=p[i];}
   double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"gait_impact_created_energy");
   double share_contact=0;
   for(size_t r=0;r<rows.size();++r){if(rows[r].stop_row)continue;
    double lambda=multipliers[r],share=lambda*inner(rows[r].row,mean);
    share_contact+=share;s.contact_impact[rows[r].point]+=(std::max)(0.,-share);s.contact_impact_impulse[rows[r].point]+=lambda;
    caught=(std::max)(caught,lambda);}
   require(share_contact<=1e-3,"gait_contact_impact_gain");
   s.impact+=(std::max)(0.,loss+share_contact);}
  // ── POSITIONAL CORRECTION (the over-constraint membrane, wave 3): a
  // velocity projection cannot restore FEASIBILITY. When a contact point
  // sits below the plane at an impact state (gap < -1e-6 m -- measured at
  // the tick-40 deadlock: the MP head 0.58 mm under while the heel rides
  // the plane and the hip holds its wall), the CONFIGURATION is outside
  // the admissible set and every velocity-level solve leaves a residual
  // that re-violates a stop. Correct q along the mass-metric least-norm
  // direction that zeroes the penetrating gaps (the contact rows ARE
  // d gap/d q), and book the potential change as the penetration's stored
  // elastic energy RETURNED (the compression was stored energy; releasing
  // it is a source, never free energy -- the ledger closes by
  // construction: u shifts by du, the dissipation books du).
#ifdef GAIT_NO_POSCORR
  if(false){
#else
  if(contact_){
#endif
   std::vector<size_t> pen;std::vector<double> gaps;
   {auto ec=evaluate(s);
    for(size_t k=0;k<npts_;++k){if(!sole_representative(k))continue;double g=gap_of(ec,k);if(g<-1e-6){pen.push_back(k);gaps.push_back(g);}}}
   if(!pen.empty()){
    double u_before=evaluate(s).potential;
    std::vector<Dense> arows;for(size_t k:pen)arows.push_back(contact_row(evaluate(s),k));
    size_t R=pen.size();std::vector<double> gram(R*R,0),rhs(R);
    for(size_t a2=0;a2<R;++a2){for(size_t b2=0;b2<R;++b2)gram[a2*R+b2]=inner(arows[a2],multiply(inv,arows[b2]));rhs[a2]=-gaps[a2];}
    std::vector<double> lam;
    if(gram_factor(gram,R,rhs,lam)){
     Dense corr(n_,0.);for(size_t a2=0;a2<R;++a2)for(size_t i=0;i<n_;++i)corr[i]+=lam[a2]*multiply(inv,arows[a2])[i];
     double dq_max=0;for(size_t i=0;i<n_;++i)dq_max=(std::max)(dq_max,std::abs(corr[i]));
     require(dq_max<=0.05,"gait_positional_correction_budget");
     for(size_t i=0;i<n_;++i)s.q[i]+=corr[i];
     double du=evaluate(s).potential-u_before;
     s.impact-=du; // the stored compression returned: the round trip gives back
     // exactly what the discretization let through while penetrating (the
     // mechanical energy DROPPED as the point went under; the correction
     // returns it) -- the ledger closes by construction, no net free energy
#ifdef GAIT_EVENT_TRACE
     std::fprintf(stderr,"[poscorr] tick=%llu points=%d dq_max=%.3e du=%+.6e J\n",(unsigned long long)ticks_,(int)R,dq_max,du);
     // Per-point totals (wave 12 diagnostic): lam_a * gap_a is the work
     // conjugate pair of the correction at each point (gap<0, lam>=0).
     for(size_t a2=0;a2<R;++a2)std::fprintf(stderr,"[poscorr-pt] tick=%llu pt=%s gap=%.6e lam=%.6e du_pt=%.6e J\n",
      (unsigned long long)ticks_,points_[pen[a2]].name.c_str(),gaps[a2],lam[a2],lam[a2]*gaps[a2]);
#endif
     }
    // gram failure: no correction applied -- the state stays infeasible and
    // the budgets refuse loudly downstream (honest, never silent)
   }}
  return caught;}
 State advance(State start,double h,const Dense& tau,int depth=0,int clamps=0)const{
  if(h<1e-12)return start;
  ++adv_calls_;require(adv_calls_<=3000,"gait_step_work_budget"); // bounds the event-split TREE per tick (deterministic, loud)
  // Impact-event budget (the free-class E3 derivation, the walker's 4-point
  // count): one substep can host 3N+2 sequential landings; a Coulomb catch
  // consumes depth 3 (halving, nested at most twice = 6) and each event split
  // at most 2. Loud refusal, never a silent clamp. The budget also bounds the
  // event-split TREE (each level halves the interval), keeping every tick's
  // work finite.
  require(depth<10+6*(int)npts_,"gait_impact_event_budget");
#ifdef GAIT_EVENT_TRACE
  if(depth>=10+6*(int)npts_-4){std::fprintf(stderr,"[evt] tick=%llu depth=%d clamps=%d adv=%llu h=%.3e mu=%.2f\n",ticks_,depth,clamps,adv_calls_,h,mu_);
   auto ee=evaluate(start);for(size_t k=0;k<npts_;++k){auto pp=ee.point(points_[k].index,points_[k].local);std::fprintf(stderr,"    %-12s gap=%.3e vy=%+.3e\n",points_[k].name.c_str(),pp.first[1]+points_[k].radius-plane_model_y_,pp.second[0][1]);}
   for(size_t d=0;d<nd_;++d){size_t c=drives_[d].coordinate;std::fprintf(stderr,"    drive %-28s q=%+.4f v=%+.4f\n",drives_[d].name.c_str(),start.q[c],start.v[c]);}}
#endif
  double caught=impact(start);
  if(mu_>0&&caught>1e-9&&depth<5)return advance(advance(start,h/2,tau,depth+3),h/2,tau,depth+3);
  std::vector<char> live(npts_,0);auto estart=evaluate(start);
  if(contact_)for(size_t k=0;k<npts_;++k)if(sole_representative(k))live[k]=gap_of(estart,k)<=kTouch?1:0;
  auto end=free_step(start,h,tau,live);int which=-1,khit=-1;double hit=h,wall=0;
  // Event namespaces: which = 0..nd_-1 a DRIVE joint-stop event (the drive
  // index), which = -2 a CONTACT event (khit = the point), which = -1 none.
  // THE SENTINEL COLLISION BUG (found by the walk at tick 117, 20260919):
  // contacts were marked which==2 -- the SAME value as a drive-2 (the left
  // ankle) stop event; the contact branch then indexed probe[(size_t)khit]
  // with khit=-1 and smeared the heap. Distinct sentinels, distinct laws.
  for(size_t d=0;d<nd_;++d){size_t c=drives_[d].coordinate;bool low=end.q[c]<model_->lower[c];if(!low&&end.q[c]<=model_->upper[c])continue;
   double depth_v=low?model_->lower[c]-end.q[c]:end.q[c]-model_->upper[c];
   if(depth_v<=1e-12)continue; // fp noise of an armed wall: not an event (the n-coordinate law)
   double bound=low?model_->lower[c]:model_->upper[c],left=0,right=h;
   for(int j=0;j<42;++j){double mid=(left+right)/2;double q=free_step(start,mid,tau,live).q[c];if(low?q<=bound:q>=bound)right=mid;else left=mid;}
   double t=(left+right)/2;if(t<hit||(t==hit&&which>=0&&d<(size_t)which)){hit=t;which=int(d);khit=-1;wall=bound;}}
  if(contact_){auto eend=evaluate(end);
   for(size_t k=0;k<npts_;++k){
    if(!sole_representative(k)||live[k]||gap_of(eend,k)>=0)continue;
    auto probe=live;probe[k]=0;double left=0,right=h;
    for(int j=0;j<42;++j){double mid=(left+right)/2;if(gap_of(evaluate(free_step(start,mid,tau,probe)),k)<=0)right=mid;else left=mid;}
    double t=(left+right)/2;if(t<hit){hit=t;which=-2;khit=int(k);}}}
  if(which==-1)return end;
   if(hit<=1e-12){
   // An fp-level crossing at the substep boundary (the n-coordinate clamp
   // law): pin the violated stop, absorb the impact, integrate the remainder.
#ifdef GAIT_EVENT_TRACE
  if(clamps>=8){std::fprintf(stderr,"[clamp] tick=%llu depth=%d clamps=%d which=%d khit=%d wall=%+.6f h=%.3e\n",ticks_,depth,clamps,which,khit,wall,h);
   auto ee=evaluate(start);for(size_t k=0;k<npts_;++k){auto pp=ee.point(points_[k].index,points_[k].local);std::fprintf(stderr,"    %-12s gap=%.3e vy=%+.3e\n",points_[k].name.c_str(),pp.first[1]+points_[k].radius-plane_model_y_,pp.second[0][1]);}}
#endif
   require(clamps<64,"gait_impact_event_budget");
   State pinned=start;
   if(which>=0){size_t pc=drives_[size_t(which)].coordinate;
    // THE WAVE-23 PIN CENSUS: the deadlock's direct face, split LOADED
    // (the leg's pad in the contact band -- the over-constraint precondition,
    // the wave-22 death's 64-pin loop) vs AIRBORNE (the glide's pocket
    // transit coasting the joint onto its stop; the wave-22 baseline's own
    // witness: one R-shoulder airborne pin).
    {bool loaded=false;const std::string& lg=drives_[size_t(which)].leg;
     for(size_t k=0;k<npts_;++k)if(points_[k].name.rfind(lg,0)==0&&live[k])loaded=true;
     if(loaded)++wall_pins_[size_t(which)];else ++wall_pins_air_[size_t(which)];}
    // BOOK THE PIN: setting q to the wall is a positional change; without
    // booking, its potential shift leaves the ledger (measured: up to 2.99 J
    // of balance error accumulated over the walk's clamp events). Same law
    // as the poscorr booking: the identity must see du paired with -du.
    // ORDER LAW: snap FIRST, then measure -- u_pin computed before the snap
    // is identically zero (the wave-4 no-op this line was until 20260919
    // wave 5 caught it: bit-identical ledger pre/post "fix").
    pinned.q[pc]=wall;
    double u_pin=evaluate(pinned).potential-evaluate(start).potential;
    pinned.impact-=u_pin;}
#ifdef GAIT_EVENT_TRACE
  if(clamps>=8){size_t c0=drives_[0].coordinate;auto jn=normals(pinned);
   auto endp=free_step(pinned,h,tau,live);
   std::fprintf(stderr,"    [clamp2] armed=%d v_hip=%.3e dq_over_wall=%.3e tau_hip=%+.4f target=%+.4f\n",
    jn[c0]!=0?1:0,pinned.v[c0],endp.q[c0]-model_->upper[c0],tau[c0],0.);
   for(size_t d=0;d<nd_;++d){size_t c=drives_[d].coordinate;
    if(d<4)std::fprintf(stderr,"      drive%zu %-26s q=%+.5f v=%+.3e tau=%+.3f\n",d,drives_[d].name.c_str(),pinned.q[c],pinned.v[c],tau[c]);}}
#endif
   impact(pinned);
   return advance(pinned,h,tau,depth,clamps+1);}
  if(which==-2&&khit>=0){auto probe=live;probe[size_t(khit)]=0;auto crossing=free_step(start,hit,tau,probe);
   require(std::abs(gap_of(evaluate(crossing),size_t(khit)))<1e-9,"gait_contact_localization");impact(crossing);
   if(mu_>0)return advance(advance(crossing,(h-hit)/2,tau,depth+1),(h-hit)/2,tau,depth+2);
   return advance(crossing,h-hit,tau,depth+1);}
  require(which>=0&&which<(int)nd_,"gait_event_namespace");size_t c=drives_[size_t(which)].coordinate;auto wall_state=free_step(start,hit,tau,live);
  require(std::abs(wall_state.q[c]-wall)<1e-9,"gait_impact_localization");wall_state.q[c]=wall;impact(wall_state);
  return advance(wall_state,h-hit,tau,depth+1);}
 public:
 GaitWalker(const J& data,double gravity,V shift,double dt=1/300.):shift_(shift),gravity_{0,-gravity,0},dt_(dt){
  recipe_=data.at("recipe");model_data_=data.at("model");
  require(recipe_.at("schema")=="chimera.gait_scene.v1","gait_schema");
  require(dt>0&&dt<=1/300.,"gait_timestep");require(recipe_.at("substeps")==4,"gait_substeps");
  model_=std::make_shared<Model>(model_data_,recipe_.at("coordinates").get<std::vector<std::string>>());
  n_=model_->names.size();// Quadruped amendment: 6 floating-base + 8 hind + 4 fore strut coordinates.
  // The fore pair is intentionally only shoulder/elbow (no unsupported wrist
  // walker), preserving the 20-coordinate capacity amendment in Model.
  require(n_>NB&&n_==18,"gait_coordinate_capacity");
  std::vector<std::string> body_names;for(const J& b:model_data_.at("bodies"))body_names.push_back(b.at("name").get<std::string>());
  bodies_.assign(body_names.size(),BodyRef{0.,V{},Mat()});
  for(size_t i=0;i<body_names.size();++i){const J& b=model_data_.at("bodies")[i];size_t idx=model_->body(body_names[i]);
   BodyRef out;out.mass=number(b.at("mass_kg"));out.com=b.at("mass_center_m").get<V>();
   auto ic=b.at("inertia_kg_m2");require(ic.size()==6,"gait_inertia_shape");
   for(int a=0;a<3;++a)out.inertia(a,a)=number(ic[a]);
   out.inertia(0,1)=out.inertia(1,0)=number(ic[3]);out.inertia(0,2)=out.inertia(2,0)=number(ic[4]);out.inertia(1,2)=out.inertia(2,1)=number(ic[5]);
   bodies_[idx]=out;mtot_+=out.mass;}
  for(auto& b:bodies_)require(b.mass>=0,"gait_mass_negative");
  config_=recipe_.at("defaults");
 // The derived angle zeros (revision 2): loaded from the scene recipe when
 // present; absent -> all zeros (a pre-revision scene composes unchanged).
 if(recipe_.contains("trunk_vault_rad")){ // the trunk-vault table (wave 8); absent -> all-zero (legacy pin-to-0)
  const J& tv=recipe_.at("trunk_vault_rad");
  require(tv.is_array()&&tv.size()==21,"gait_trunk_vault_shape");
  for(size_t i=0;i<21;++i){tables_.trunk_vault[i]=number(tv[i]);
   require(std::isfinite(tables_.trunk_vault[i])&&std::abs(tables_.trunk_vault[i])<=0.6,"gait_trunk_vault_range");}}
 if(recipe_.contains("zero_map_rad")){
  const J& zm=recipe_.at("zero_map_rad");
  require(zm.contains("hip")&&zm.contains("knee")&&zm.contains("ankle")&&zm.contains("MP"),"gait_zero_map_keys");
  tables_.zeros[0]=number(zm.at("hip"));tables_.zeros[1]=number(zm.at("knee"));
  tables_.zeros[2]=number(zm.at("ankle"));tables_.zeros[3]=number(zm.at("MP"));
  for(double z:tables_.zeros)require(std::isfinite(z)&&std::abs(z)<=3.,"gait_zero_map_range");}
 if(recipe_.contains("fore_entry_pose_rad")){ // the wave-14 entry pose (scene statics; absent -> legacy constants)
  const J& fp=recipe_.at("fore_entry_pose_rad");
  require(fp.contains("shoulder_rad")&&fp.contains("elbow_rad"),"gait_fore_entry_pose_keys");
  fore_pose_sh_=number(fp.at("shoulder_rad"));fore_pose_el_=number(fp.at("elbow_rad"));
  require(std::isfinite(fore_pose_sh_)&&std::isfinite(fore_pose_el_)&&
   std::abs(fore_pose_sh_)<=1.6&&std::abs(fore_pose_el_)<=1.6,"gait_fore_entry_pose_range");}
 if(recipe_.contains("trunk_handoff_ticks")){ // the wave-15 level-entry hand-off (scene statics; absent -> legacy wave-10 ramp)
  const J& th=recipe_.at("trunk_handoff_ticks");
  require(th.is_number(),"gait_trunk_handoff_shape");
  double thv=number(th);
  require(std::isfinite(thv)&&thv>0.&&thv<=600.,"gait_trunk_handoff_range");}
 // theta*(phi): the derived posture target table (wave 8)
 if(config_.contains("settle_ticks")){require(config_["settle_ticks"].is_number(),"gait_settle_shape");settle_ticks_=(int)number(config_["settle_ticks"]);require(settle_ticks_>=0&&settle_ticks_<=600,"gait_settle_range");settle_total_=settle_ticks_;}
  plane_world_y_=number(recipe_.at("contact_plane_height_m"));require(std::isfinite(plane_world_y_),"gait_contact_plane_invalid");plane_model_y_=plane_world_y_-shift_[1];
  require(config_.contains("contact_enabled")&&config_["contact_enabled"].is_boolean(),"gait_contact_flag_invalid");contact_=config_["contact_enabled"].get<bool>();
  require(config_.contains("contact_friction")&&config_["contact_friction"].is_number()&&number(config_["contact_friction"])>=0&&number(config_["contact_friction"])<=1,"gait_friction_flag_invalid");mu_=number(config_["contact_friction"]);
  require(recipe_.contains("contact_points")&&recipe_.at("contact_points").is_array()&&!recipe_.at("contact_points").empty(),"gait_contact_points");
  for(const J& p:recipe_.at("contact_points")){ContactPoint out;out.name=p.at("name").get<std::string>();out.body=p.at("body").get<std::string>();
   out.index=model_->body(out.body);out.local=p.at("point_m").get<V>();
   out.radius=number(p.at("radius_m"));require(out.radius>0,"gait_contact_radius_invalid");points_.push_back(out);}
  npts_=points_.size();require(npts_>=1&&npts_<=8,"gait_contact_capacity");
  // Drives: the recipe lists them AFTER the six base coordinates, in leg
  // pairs; the mass-normalized gains use the DEFAULTS-pose diagonal (the
  // qualified mass-normalized PD), the DERIVED f_s and the qualified zeta.
  const J& dj=recipe_.at("drives");require(dj.is_array()&&dj.size()==12,"gait_drive_count");
  auto e=model_->evaluate(model_->defaults,Dense(n_,0.),gravity_);
  double freq=2*pi*FS_HZ;
  for(const J& d:dj){Drive out;out.name=d.at("coordinate").get<std::string>();out.leg=d.at("leg").get<std::string>();out.joint=d.at("joint").get<std::string>();
   auto it=std::find(model_->names.begin(),model_->names.end(),out.name);require(it!=model_->names.end(),"gait_drive_coordinate");out.coordinate=size_t(it-model_->names.begin());
   require(out.coordinate>=NB,"gait_drive_base_row");
   out.cap=number(d.at("torque_cap_N_m"));out.store_floor=number(d.at("store_floor_J"));require(out.cap>0&&out.store_floor>0,"gait_drive_budget");
   out.damping=number(d.at("viscous_damping_N_m_s_rad"));require(out.damping>=0,"gait_damping_negative");
   double m=e.mass[out.coordinate*n_+out.coordinate];require(m>0,"gait_drive_mass");
   kp_.push_back(m*freq*freq);kd_.push_back(2*ZETA*m*freq);damping_.push_back(out.damping);
   drives_.push_back(out);}
  nd_=drives_.size();
  battery_.assign(nd_,0.);brake_.assign(nd_,0.);empty_events_.assign(nd_,0);
  for(size_t d=0;d<nd_;++d){battery_[d]=drives_[d].store_floor;store_total_+=drives_[d].store_floor;}
  // The posture drive: mass-normalized at the trunk-pitch diagonal, the same
  // derived 4.0 Hz; its store keys to the hip row (the same iliopsoas/GMed
  // musculature carries the trunk moment, pinned fulltext).
  {double m=e.mass[2*n_+2];require(m>0,"gait_posture_mass");
   kp_post_=m*freq*freq;kd_post_=2*ZETA*m*freq;store_post_=drives_[0].store_floor;}
  require(config_.contains("power")&&config_["power"].is_boolean(),"gait_power_flag");
  require(config_.contains("gait_enabled")&&config_["gait_enabled"].is_boolean(),"gait_enabled_flag");
  require(config_.contains("capture_enabled")&&config_["capture_enabled"].is_boolean(),"gait_capture_flag");
  require(config_.contains("posture_drive")&&config_["posture_drive"].is_boolean(),"gait_posture_flag");
  require(config_.contains("push_N")&&number(config_["push_N"])>=-30.&&number(config_["push_N"])<=30.,"gait_push_range");
  for(size_t d=0;d<nd_;++d)require(config_.contains(drives_[d].name+"_drive")&&config_[drives_[d].name+"_drive"].is_boolean(),"gait_drive_flag");
  // ── the planted-strut constants (wave 12): the fore chain geometry from ──
  // the scene's OWN model/contact bytes, never re-authored here.
  {
   for(size_t leg=0;leg<2;++leg){
    const std::string tag=leg==0?"fore_left":"fore_right";
    bool got_sh=false,got_el=false,got_heel=false,got_mp=false;
    V heel{},mp{};
    for(size_t k=0;k<npts_;++k){
     if(points_[k].name==tag+"_heel"){fore_paw_point_[leg]=k;heel=points_[k].local;got_heel=true;}
     if(points_[k].name==tag+"_mp_head"){mp=points_[k].local;got_mp=true;}}
    require(got_heel&&got_mp,"gait_fore_paw_points_missing");
    paw_ref_local_[leg]=V{0.5*(heel[0]+mp[0]),0.5*(heel[1]+mp[1]),0.5*(heel[2]+mp[2])};
    for(size_t d=0;d<nd_;++d){const Drive& dr=drives_[d];
     if(dr.leg==tag){bool sh=dr.joint=="shoulder";
      require(!(sh?got_sh:got_el),"gait_fore_drive_duplicate");
      fore_coord_[leg][sh?0:1]=dr.coordinate;(sh?got_sh:got_el)=true;}}
    require(got_sh&&got_el,"gait_fore_drives_missing");}
   require(std::abs(paw_ref_local_[0][0]-paw_ref_local_[1][0])<1e-12&&std::abs(paw_ref_local_[0][1]-paw_ref_local_[1][1])<1e-12,"gait_fore_paw_asym");
   fore_rho_=std::hypot(paw_ref_local_[0][0],paw_ref_local_[0][1]);
   fore_beta_=std::atan2(paw_ref_local_[0][1],paw_ref_local_[0][0]);
   require(fore_rho_>1e-6,"gait_fore_paw_rho");
   bool got_mount=false;
   for(const J& b:model_data_.at("bodies")){
    const std::string nm=b.at("name").get<std::string>();
    if(nm=="upperarm_fore_left"||nm=="upperarm_fore_right"){
     size_t leg=nm=="upperarm_fore_left"?0:1;
     fore_mount_body_[leg]=model_->body("pelvis");
     fore_mount_local_[leg]=b.at("joint").at("parent_location_m").get<V>();
     got_mount=true;}
    if(nm=="forearm_fore_left"||nm=="forearm_fore_right"){
     double l=std::abs(number(b.at("joint").at("parent_location_m")[1]));
     if(fore_L1_>0)require(std::abs(l-fore_L1_)<1e-12,"gait_fore_L1_mismatch");
     fore_L1_=l;}}
   require(got_mount&&fore_L1_>0,"gait_fore_chain_geometry_missing");
   require(fore_L1_+fore_rho_>fore_L1_+1e-6,"gait_fore_reach_degenerate");
   // THE DOC CEILING (the wave-11 falsifier, now code): the fore elbow cap is
   // the doc-derived 3.76 N.m at every share; demands beyond it are banked
   // red, never raised away.
   for(size_t d=0;d<nd_;++d)
    if((drives_[d].leg=="fore_left"||drives_[d].leg=="fore_right")&&drives_[d].joint=="elbow")
     require(drives_[d].cap<=3.76*(1.+1e-9),"gait_fore_elbow_cap_raised");
   // THE SHARE FLAG (wave 12): the quad-share envelope the strut's static
   // load line is scoped to; the scene compiler scales the drive envelope.
   if(recipe_.contains("fore_share")){double s=number(recipe_.at("fore_share"));
    require(std::isfinite(s)&&s>=0.25&&s<=0.55,"gait_fore_share_range");}
  }
  // ── THE HIND EXTENSION LAW's emergency constants (wave 27, derived by ──
  // derive_height_hold.py; absent keys -> the law is inert, byte-identical
  // legacy behavior -- the zero_map/trunk_vault/fore_entry_pose pattern).
  // The floor key is CROSS-CHECKED against this controller's own expression
  // (the scene's authored constant must be the same derivation).
  if(recipe_.contains("hind_height_hold_crit_m")&&recipe_.contains("hind_height_hold_floor_m")){
   hind_height_crit_=number(recipe_.at("hind_height_hold_crit_m"));
   hind_height_floor_=2.*kSinkRateMax+kSinkRateMax*(1./(ZETA*2.*pi*FS_HZ))/dt_;
   require(std::isfinite(hind_height_crit_)&&hind_height_crit_>0.,"gait_height_hold_crit");
   require(std::abs(number(recipe_.at("hind_height_hold_floor_m"))-hind_height_floor_)<=1e-9,"gait_height_hold_floor_mismatch");
   hind_height_hold_armed_=true;}
  // ── THE HIND STEP LAW's chain geometry (wave 28): harvested from the ──
  // scene's OWN model bytes (the same segments the Assembly seats), never
  // re-authored: the thigh/shank lengths from the chain's child-joint
  // parent offsets, the hip mounts from the thigh joints, the paw-midpoint
  // offset from the declared hind contact locals.
  {
   pelvis_row_=model_->body("pelvis");
   for(size_t leg=0;leg<2;++leg){
    const std::string legn=leg==0?"left":"right";
    bool got[4]={false,false,false,false};
    for(size_t d=0;d<nd_;++d){const Drive& dr=drives_[d];
     if(dr.leg!=legn)continue;
     int ji=dr.joint=="hip"?0:dr.joint=="knee"?1:dr.joint=="ankle"?2:dr.joint=="MP"?3:-1;
     require(ji>=0&&!got[ji],"gait_hind_drive_duplicate");
     hind_coord_[leg][ji]=dr.coordinate;got[ji]=true;}
    require(got[0]&&got[1]&&got[2]&&got[3],"gait_hind_drives_missing");}
   {bool gh=false,gm=false;
    for(size_t k=0;k<npts_;++k){
     if(points_[k].name=="left_heel"){hind_heel_pt_[0]=k;gh=true;}
     if(points_[k].name=="left_mp_head"){hind_mp_pt_[0]=k;gm=true;}
     if(points_[k].name=="right_heel")hind_heel_pt_[1]=k;
     if(points_[k].name=="right_mp_head")hind_mp_pt_[1]=k;}
    require(gh&&gm,"gait_hind_paw_points_missing");
    require(std::abs(points_[hind_heel_pt_[0]].local[0]-points_[hind_heel_pt_[1]].local[0])<1e-12&&
     std::abs(points_[hind_mp_pt_[0]].local[0]-points_[hind_mp_pt_[1]].local[0])<1e-12,"gait_hind_paw_asym");
    hind_xm_=0.5*(points_[hind_heel_pt_[0]].local[0]+points_[hind_mp_pt_[0]].local[0]);}
   {bool gotM=false,gotL1=false,gotL2=false;
    for(const J& b:model_data_.at("bodies")){
     const std::string nm=b.at("name").get<std::string>();
     if(nm=="thigh_left"||nm=="thigh_right"){
      size_t leg=nm=="thigh_left"?0:1;
      hind_mount_[leg]=b.at("joint").at("parent_location_m").get<V>();
      require(b.at("joint").at("parent").get<std::string>()=="pelvis","gait_hind_mount_parent");
      gotM=true;}
     if(nm=="shank_left"||nm=="shank_right"){
      double l=std::abs(number(b.at("joint").at("parent_location_m")[1]));
      if(gotL1)require(std::abs(l-hind_L1_)<1e-12,"gait_hind_L1_mismatch");
      hind_L1_=l;gotL1=true;}
     if(nm=="foot_left"||nm=="foot_right"){
      double l=std::abs(number(b.at("joint").at("parent_location_m")[1]));
      if(gotL2)require(std::abs(l-hind_L2_)<1e-12,"gait_hind_L2_mismatch");
      hind_L2_=l;gotL2=true;}}
    require(gotM&&gotL1&&gotL2,"gait_hind_chain_geometry_missing");
    require(hind_L1_+hind_L2_>hind_L1_+1e-6,"gait_hind_reach_degenerate");}
  }
  reset();}
 double timestep()const{return dt_;}const Dense& angles()const{return s_.q;}const Dense& speeds()const{return s_.v;}const Model& model()const{return *model_;}
 const Dense& batteries()const{return battery_;}double phase(size_t leg)const{return phi_[leg];}uint64_t capture_events()const{return capture_events_;}
 void reset(){
  s_=State(n_,npts_);s_.q=model_->defaults;s_.v=Dense(n_,0.);ticks_=0;capture_events_=0;last_torque_=Dense(n_,0.);settle_ticks_=settle_total_;
  hind_height_hold_latched_=false;hind_height_fire_tick_=0;hind_height_fire_margin_=0;hind_height_fires_=0;
  paws_captured_=false;ik_sat_ticks_[0]=ik_sat_ticks_[1]=0;ik_roundtrip_m_[0]=ik_roundtrip_m_[1]=0;
  ik_qerr_[0]=ik_qerr_[1]=0;
  ik_sat_prev_[0]=ik_sat_prev_[1]=false;
  fore_t_[0]=fore_t_[1]=0.;fore_stance_[0]=fore_stance_[1]=0.;fore_cycle_[0]=fore_cycle_[1]=0.;
  fore_mode_[0]=fore_mode_[1]=0;fore_td_[0]=fore_td_[1]=0;
  fore_replants_[0]=fore_replants_[1]=0;fore_clamped_[0]=fore_clamped_[1]=0;fore_conv_[0]=fore_conv_[1]=0;
  fore_entry_[0]=fore_entry_[1]=0;fore_gate_holds_[0]=fore_gate_holds_[1]=0;
  fore_wall_bound_[0]=fore_wall_bound_[1]=0;fore_wall_follows_[0]=fore_wall_follows_[1]=0;
  fore_td_plant_[0]=fore_td_plant_[1]=true;
  fore_glide_hold_[0]=fore_glide_hold_[1]=0;fore_hold_last_[0]=fore_hold_last_[1]=0;
  fore_hold_off_[0]=V{};fore_hold_off_[1]=V{};
  fore_wait_fires_[0]=fore_wait_fires_[1]=0;
  hind_step_mode_[0]=hind_step_mode_[1]=0;
  hind_step_t_[0]=hind_step_t_[1]=0.;
  hind_step_from_[0]=hind_step_from_[1]=V{};hind_step_to_[0]=hind_step_to_[1]=V{};
  hind_step_plant_y_[0]=hind_step_plant_y_[1]=0.;
  hind_step_ap_[0]=hind_step_ap_[1]=0.;hind_step_mp_[0]=hind_step_mp_[1]=0.;
  hind_step_branch_[0]=hind_step_branch_[1]=-1;
  hind_step_xoff_[0]=hind_step_xoff_[1]=0.;hind_step_qerr_[0]=hind_step_qerr_[1]=0.;
  hind_step_fires_[0]=hind_step_fires_[1]=0;hind_step_tds_[0]=hind_step_tds_[1]=0;
  hind_step_gated_[0]=hind_step_gated_[1]=0;hind_step_clamped_[0]=hind_step_clamped_[1]=0;
  hind_step_last_fire_[0]=hind_step_last_fire_[1]=0;hind_step_last_td_[0]=hind_step_last_td_[1]=0;
  hind_step_held_[0]=hind_step_held_[1]=false;hind_step_clear_tick_[0]=hind_step_clear_tick_[1]=-1;
  hind_step_hold_ticks_[0]=hind_step_hold_ticks_[1]=0;hind_step_alt_[0]=hind_step_alt_[1]=0;
  hind_step_stall_[0]=hind_step_stall_[1]=0;
  hind_step_stand_[0]=hind_step_stand_[1]=false;hind_step_stand_ticks_[0]=hind_step_stand_ticks_[1]=0;
  hind_step_stand_mp_[0]=hind_step_stand_mp_[1]=0.;
  hind_step_stand_latch_[0]=hind_step_stand_latch_[1]=false;
  hind_step_stand_pivot_[0]=hind_step_stand_pivot_[1]=false;
  hind_step_stand_release_[0]=hind_step_stand_release_[1]=-1;
  hind_step_stand_latch_ticks_[0]=hind_step_stand_latch_ticks_[1]=0;
  hind_step_alt_due_[0]=hind_step_alt_due_[1]=0;hind_step_deadline_tick_[0]=hind_step_deadline_tick_[1]=0;
  hind_step_deadline_fires_[0]=hind_step_deadline_fires_[1]=0;
  hind_step_dl_unload_[0]=hind_step_dl_unload_[1]=0;hind_step_unload_fires_[0]=hind_step_unload_fires_[1]=0;
  hind_step_waive_fires_[0]=hind_step_waive_fires_[1]=0;
  hind_step_waive_first_[0]=hind_step_waive_first_[1]=-1;hind_step_waive_last_[0]=hind_step_waive_last_[1]=-1;
  hind_step_graze_yields_[0]=hind_step_graze_yields_[1]=0;
  hind_step_graze_first_[0]=hind_step_graze_first_[1]=-1;
  hind_step_guard_blocks_[0]=hind_step_guard_blocks_[1]=0;
  hind_step_guard_first_[0]=hind_step_guard_first_[1]=-1;
  hind_alt_repairs_[0]=hind_alt_repairs_[1]=0;hind_step_handoff_restores_[0]=hind_step_handoff_restores_[1]=0;
  for(size_t d=0;d<12;++d){wall_pins_[d]=0;wall_pins_air_[d]=0;}
  battery_.assign(nd_,0.);brake_.assign(nd_,0.);empty_events_.assign(nd_,0);store_total_=0;
  for(size_t d=0;d<nd_;++d){battery_[d]=drives_[d].store_floor;store_total_+=drives_[d].store_floor;}
  battery_post_=store_post_;brake_post_=0;empty_post_=0;store_total_+=store_post_;
  phi_[0]=0.;phi_[1]=0.5;
  // The entry phases (the single-support entry law, wave 4): the scene
  // recipe names them; absent -> the TD entry {0, 0.5}.
  if(config_.contains("start_phase_left"))phi_[0]=number(config_["start_phase_left"]);
  if(config_.contains("start_phase_right"))phi_[1]=number(config_["start_phase_right"]);
  // The gait-state initialization (the source model's own scheme: enter the
  // periodic cycle AT the TD state): joints at the reset columns, joint
  // speeds at the table phase slope, the base at the authored gait-pose
  // height (the compiler's seating of that pose) and the measured gait speed.
  if(config_.contains("start_at_tables")&&config_["start_at_tables"].get<bool>()){
   if(config_.contains("base_trans_y_m"))s_.q[4]=number(config_["base_trans_y_m"]);
   for(size_t d=0;d<nd_;++d){const Drive& dr=drives_[d];
    if(dr.leg=="fore_left"||dr.leg=="fore_right"){s_.q[dr.coordinate]=dr.joint=="shoulder"?fore_pose_sh_:fore_pose_el_;s_.v[dr.coordinate]=0.;continue;}
    // RUN REPAIR (wave 16, THE OWED DEFECT, itemized in receipt_wave16.json
    // with before/after baselines): the right hind's JOINTS were assembled
    // from tables_.at(1, ...) -- the phi=1.0 column, periodic to the phi=0.0
    // (TD) column -- while its clock starts at start_phase_right=0.5: the
    // literal '1' meant the LEG INDEX, not a phase (the forelimb commit
    // f0efbba7 dropped the phi_ read here; the pre-forelimb bytes read
    // tables_.at(phi_[...])). Measured before: runtime L/R hind pair-min
    // dangles 4.575e-2/4.557e-2 m vs the scene-derived 4.616e-2/4.913e-2 --
    // both legs at TD-pose geometry, the right against its own clock. The
    // repair assembles each hind at ITS clock column, making the runtime
    // state the scene's derivation state (the model-validation gate).
    double qstar[4];tables_.at(phi_[dr.leg=="left"?0:1],qstar);
    int ji=dr.joint=="hip"?0:dr.joint=="knee"?1:dr.joint=="ankle"?2:3;
    s_.q[dr.coordinate]=qstar[ji];
    double p=phi_[dr.leg=="left"?0:1],dp=0.05;double a1[4],a2[4];
    tables_.at(p+dp,a1);tables_.at(p-dp,a2);
    s_.v[dr.coordinate]=(a1[ji]-a2[ji])/(2*dp*T_CYCLE);}
   if(config_.contains("base_speed_x_m_s"))s_.v[3]=number(config_["base_speed_x_m_s"]);
   // The trunk enters ON the vault table too (the source's own scheme: the
   // entry state IS the cycle state): pitch at theta*(entry phase), speed at
   // the vault table's phase slope -- the scene seats base_y against THIS
   // pose (a q2=0 reset under a leaned seat dangles the contact and
   // reintroduces the wave-6 bounce).
   if(config_.contains("start_trunk_rad"))s_.q[2]=number(config_["start_trunk_rad"]);
   if(config_.contains("start_trunk_rad")){double p=phi_[0],dp=0.05;
    // WAVE 15: under the level-entry hand-off the entry state is the BLEND's
    // own state at t=0 (amp=0 -> rate 0): the trunk enters at rest in pitch.
    // The legacy table-slope injection is the LEANED entry's rate.
    if(recipe_.contains("trunk_handoff_ticks"))s_.v[2]=0.;
    else s_.v[2]=(tables_.trunk_target(p+dp)-tables_.trunk_target(p-dp))/(2*dp*T_CYCLE);}}
  auto e=evaluate(s_);
  for(size_t leg=0;leg<2;++leg){bool touching=false;const char* prefix=leg==0?"left":"right";
   for(size_t k=0;k<npts_;++k)if(points_[k].name.rfind(prefix,0)==0&&gap_of(e,k)<=kTouch)touching=true;
   touching_prev_[leg]=touching;}
  for(size_t k=0;k<npts_;++k)require(gap_of(e,k)>0,"gait_initial_penetration");
  e_ref_=mechanical(s_); // baseline the ledger at the ACTUAL initial state (entry pose + injected momentum)
  // No settle window: the entry pose IS the settle end -- capture immediately.
  if(settle_total_==0&&config_["gait_enabled"].get<bool>()&&config_["power"].get<bool>()&&contact_)capture_paws();}
 void configure(const J& input){
  require(input.is_object()&&!input.empty(),"gait_control_object");auto c=config_;bool restart=false;
  for(auto it=input.begin();it!=input.end();++it){
   if(it.key()=="reset"){require(it.value().is_boolean()&&it.value().get<bool>(),"gait_reset_true");restart=true;}
   else if(it.key()=="base_trans_y_m"){ // release height for the settle-drop start: absolute, restart-gated (the free-root base-key law)
    require(it.value().is_number(),"gait_base_range");double a=number(it.value());require(std::abs(a)<=1.,"gait_base_range");
    require(restart||!config_.contains("base_trans_y_m")||a==number(config_["base_trans_y_m"]),"gait_base_requires_reset");
    c["base_trans_y_m"]=it.value();}
   else{require(c.contains(it.key()),"unknown_gait_control");c[it.key()]=it.value();}}
  for(auto key:{"power","contact_enabled","gait_enabled","capture_enabled"})require(c[key].is_boolean(),"gait_boolean_control");
  for(size_t d=0;d<nd_;++d)require(c[drives_[d].name+"_drive"].is_boolean(),"gait_boolean_control");
  if(c.contains("contact_enabled")){require(c["contact_enabled"].get<bool>()==config_["contact_enabled"].get<bool>()||restart,"gait_contact_toggle_requires_reset");}
  if(c.contains("contact_friction")){double m=number(c["contact_friction"]);require(c["contact_friction"].is_number()&&m>=0&&m<=1,"gait_friction_range");}
  if(c.contains("push_N")){double p=number(c["push_N"]);require(c["push_N"].is_number()&&p>=-30.&&p<=30.,"gait_push_range");}
  config_=c;contact_=config_["contact_enabled"].get<bool>();mu_=number(config_["contact_friction"]);if(restart)reset();}
 void step(){
#ifdef GAIT_EVENT_TRACE
  if(ticks_%10==0)std::fprintf(stderr,"[tick] %llu\n",(unsigned long long)ticks_);
#endif
  s_.impulse=Dense(n_,0.);s_.contact_impact_impulse.assign(npts_,0.);s_.contact_force_impulse.assign(npts_,0.);s_.contact_generalized=Dense(n_,0.);s_.friction_impulse.assign(npts_,0.);s_.friction_force_impulse.assign(npts_,0.);s_.friction_heat_tick.assign(npts_,0.);
  // Stage E -> F handoff (the derivation's ladder): gait_enabled=false holds
  // the clock frozen at the reset columns phi={0, 0.5} -- both legs standing
  // in the double-support TD state, servos driving the frozen tables (the
  // stage-E stand); true releases the clock (the stage-F walk).
  bool walking=config_["gait_enabled"].get<bool>()&&(settle_ticks_<=0);
  if(settle_ticks_>0)--settle_ticks_; // the settle window: clock frozen, targets hold the entry pose
  // THE PLANT CAPTURE (wave 12): the settle window just ended -- the loaded
  // state IS the planted pose. Freeze the paw spots (world frame) and the IK
  // branch; the struts hold THEM from here on, not fixed joint angles.
  if(!paws_captured_&&settle_total_>0&&settle_ticks_==0&&walking&&config_["power"].get<bool>()&&contact_)capture_paws();
  // 1) clock update at the tick start (contact reset dominates).
  {auto e=evaluate(s_);if(walking)update_clock(e,dt_);else{for(size_t leg=0;leg<2;++leg)
   // THE TOUCH LAW's classification held through the frozen window too (the
   // same release state the walk's first update consumes; a foot planted at
   // the band edge through the settle is ONE contact, not a new touchdown).
   touching_prev_[leg]=leg_contact(e,leg,touching_prev_[leg]);}
   // THE STEPPING-STRUT FORE CLOCK (wave 13): armed at the settle capture,
   // advanced only in the walk -- liftoff/glide/touchdown transitions are
   // CLOCK-derived (deterministic), never force- or position-triggered.
   if(walking&&paws_captured_)update_fore_clock(e);
   // ── THE HEIGHT EMERGENCY (wave 27): the hind extension law's trigger. ──
   // Runs on the SAME tick-start evaluation update_fore_clock read (the fore
   // decisions at the fire tick stay byte-identical: they read the pre-servo
   // state); the ff engages THIS tick's servo calls. The latch is one-way:
   // the decayed regime, once declared, is never un-declared -- the ff is
   // equilibrium-seeking (it drives the actual TO the designed pose), so the
   // latch cannot overshoot the pose it holds.
   if(walking&&paws_captured_&&hind_height_hold_armed_&&!hind_height_hold_latched_){
    double shl=e.point(fore_mount_body_[0],fore_mount_local_[0]).first[1];
    double shr=e.point(fore_mount_body_[1],fore_mount_local_[1]).first[1];
    double shmin=shl<shr?shl:shr;
    if(shmin-hind_height_crit_<=hind_height_floor_){
     hind_height_hold_latched_=true;hind_height_fire_tick_=ticks_;
     hind_height_fire_margin_=shmin-hind_height_crit_;++hind_height_fires_;}}
   // ── THE HIND STEP LAW's trigger (wave 28): the clock's own lift slot ──
   // arrived with the pads STILL LIVE -- the designed kinematic lift has
   // stalled under the ride -- so the leg STEPS (the wave-20 pattern, hind
   // side), and the step's TD touch reset re-syncs the clock to the true
   // stance. Regime-gated to the height emergency; the fore decisions at
   // this tick are byte-safe (the same pre-servo evaluation they already
   // read). The gate is the wave-20 clauses hind-side + the support floor.
   if(walking&&paws_captured_&&hind_height_hold_latched_){
    double tair=(std::ceil)((T_CYCLE-DUTY_SAMPLED)/dt_);
    for(size_t hl=0;hl<2;++hl)if(hind_step_mode_[hl]==1){ // the glide clock
     if(hind_step_held_[hl]){ // THE LIFT-FIRST HOLD's release test: the leg's
      // OWN release quantum (the touch law's), on this same tick-start
      // evaluation -- a static vertical demand until the band clears.
      double g1=gap_of(e,hind_heel_pt_[hl]),g2=gap_of(e,hind_mp_pt_[hl]);
      if((g1<g2?g1:g2)>kTouch+kReleaseBand){hind_step_held_[hl]=false;hind_step_clear_tick_[hl]=(int)ticks_;}
      else{++hind_step_hold_ticks_[hl];++hind_step_stall_[hl];}
#ifdef GAIT_EVENT_TRACE
      // WAVE 45 HOLD-CLEARANCE INSTRUMENT (read-only plumbing, receipt_wave45.json):
      // the release band's OWN decision view -- the heel/MP gaps the release test
      // reads, the band edge (the machinery's own constants), the held state after
      // the test (hd=0 marks THE CROSSING TICK), the hold census clock, the glide
      // clock pre-increment (the td test this tick evaluates tm+1 >= tair), the
      // clear tick, the other leg's mode, the deadline. One line per held tick.
      std::fprintf(stderr,"[dvfl] t=%llu leg=%zu g1=%.9e g2=%.9e edge=%.1e hd=%d ht=%llu tm=%.1f clr=%d oth=%d dl=%llu\n",
       (unsigned long long)ticks_,hl,g1,g2,kTouch+kReleaseBand,hind_step_held_[hl]?1:0,
       (unsigned long long)hind_step_hold_ticks_[hl],hind_step_t_[hl],
       hind_step_clear_tick_[hl],(int)hind_step_mode_[1-hl],
       (unsigned long long)hind_step_deadline_tick_[hl]);
#endif
     }
     ++hind_step_t_[hl];
     // THE GLIDE-RETURN LAW (wave 31, receipt_wave31.json): A REPLANT IS NOT
     // COMPLETE UNTIL THE BAND ENTRY. The wave-28..30 clocked TD delivered the
     // L's 142 replant 12.9 mm HIGH (the formal decomposition: pin error
     // 0.0100 mm = the fire-tick-start touch gap itself, the pin FRESH -- the
     // settle-staleness hypothesis falsified; the delivery error 12.88 mm
     // owns the miss: the pad tracked the arch's RISE to 0.1-0.3 mm and then
     // under-tracked the descent +1.4 -> +10.4 mm as the haul-dominated hip
     // never reversed) and the pads never re-entered the band (rxn 0 from
     // 142, 56 mm by 200): the replant was a CLOCK event with no touchdown.
     // The law: the clock's TD test no longer completes the replant by
     // itself; the leg HOLDS THE PLANT POINT (the glide's own sg clamp at 1
     // already commands exactly the plant target -- zero new constants)
     // until the pair-min pads gap <= kTouch (the wave-22 touch class, the
     // same band the crossing reset reads), and ONLY THEN does the replant
     // complete: mode 0, the tds counter, and the wave-22 crossing re-syncs
     // phi_[leg]=0 at that same class crossing (the completion and the
     // re-sync land on the same tick, the R's own 107 pattern). Shipped
     // completions whose pads are already in band (the R's 107: tick-start
     // pair-min 4.16e-7 m) are UNCHANGED -- the fence bytes through 150 stand.
     if(hind_step_t_[hl]>=tair){
      double g1=gap_of(e,hind_heel_pt_[hl]),g2=gap_of(e,hind_mp_pt_[hl]);
      if((g1<g2?g1:g2)<=kTouch){ // the band entry: the replant IS a touchdown
      hind_step_mode_[hl]=0;hind_step_t_[hl]=0.; // touch reset re-syncs phi
      hind_step_held_[hl]=false;
      hind_step_last_td_[hl]=ticks_;++hind_step_tds_[hl];
#ifdef GAIT_EVENT_TRACE
      std::fprintf(stderr,"[hindstep] td leg=%zu tick=%llu tds=%llu\n",
       hl,(unsigned long long)ticks_,(unsigned long long)hind_step_tds_[hl]);
#endif
      }
#ifdef GAIT_EVENT_TRACE
      else std::fprintf(stderr,"[hindstep] holdreturn leg=%zu tick=%llu t=%d pairmin=%.4e\n",
       hl,(unsigned long long)ticks_,(int)hind_step_t_[hl],(g1<g2?g1:g2));
#endif
     }}
    for(size_t hl=0;hl<2;++hl){
     size_t o=hl==0?1:0;
     if(hind_step_mode_[hl]!=0)continue;
     // THE ALTERNATION-DUE FLAG (wave 29): computed every decision tick for
     // the status census; the alternation leg still requires LIVE PADS (it
     // is the standing leg's ride that the budget bounds).
     hind_step_alt_due_[hl]=hind_alt_due(hl,tair)?1:0;
     // THE WAVE-32 MIN-FORM DEADLINE: the one arithmetic shared with the due
     // predicate (hind_deadline); the status census reads the same ticks.
     hind_step_dl_unload_[hl]=0;
     {bool is_unload=false;
      uint64_t dl=hind_deadline(hl,tair,&is_unload);
      hind_step_deadline_tick_[hl]=dl;
      hind_step_dl_unload_[hl]=is_unload?1:0;}
     // THE STAND-FIRST HOLD (wave 33): arm/disarm per decision tick, BEFORE
     // any gate continue -- the carrier must be pinned while the swing's pads
     // are in the band (the stall's never-left or the descent's returned
     // read), released the tick the other completes OR the swing's pads clear
     // (the real lift's own era: the stance columns resume). THE LATCH WAS
     // TRIED AND REVERTED (the fourth amended build, receipt): a hold held
     // through the swing's airborne era removed the vault's pivot for the
     // whole glide -- the planar re-capture folded the leg under the hauling
     // body (the R's hip 63 deg), the body launched, the impact-event budget
     // refused at 215. The planar re-capture needs the columns' periodic
     // resumption to re-establish the pivot; the latch's falsifier fired and
     // the bytes were restored. The pin re-captures its planar target every
     // pinned tick; the y-anchor is captured once at the arm tick (the floor
     // anchor, the second amendment).
     // THE LATCHED CARRIER HOLD (wave 34): the mined 250 disarm -- the
     // predicate read the CARRIER's own 1-tick graze past the genuine-
     // departure bound (1.317e-5) one tick after the arm, while the swing's
     // read was still in band: the trigger defeats itself on the exact lift
     // it exists to prevent. THE LATCH: once armed in the other's swing era,
     // the hold stays armed until the other completes (mode 0) or this leg
     // fires. The latch's continuation pins with the SHIPPED anchor (the
     // planar re-captured every pinned tick, the y the arm capture) -- the
     // frozen world pivot was tried and reverted (the second amended build:
     // the 259 pad loss under the roll demand, the 298 refusal); the
     // extension-envelope release read is reverted with it.
     // THE WAVE-34 LATCH IS REVERTED (the pre-committed falsifier action,
     // receipt_wave34.json amendment 2): three builds measured -- (1) the
     // latch through the stall blinks launches the walk at 215 (the wave-33
     // amendment-3 face, reproduced on the world-pivot variant:
     // gait_impact_event_budget, the R's hip 63.0254 deg) -- the 1-tick
     // blink resumptions are the vault's pivot re-establishment; (2)+(3) the
     // AIRBORNE-GATED latch (the swing's hold genuinely cleared) with EITHER
     // anchor -- the frozen world pivot AND the shipped re-capture -- rides
     // the twelfth exchange exactly [250,262) and still loses the pads at
     // 259: the real swing's 15-tick haul transfers the carrier's whole share
     // forward (the rxn 10.1 N @254 -> 0 @260, both anchors) before the 262
     // window opens -- the drain is GEOMETRIC (the mined hind splay: the
     // plants 0.12-0.24 m ahead of the body's 4 mm/tick advance), not
     // control. The pin buys 9-10 ticks of ride; the era needs 13. THE
     // WAVE-35 BANK: the carrier's exchange fire must land before its share
     // drains -- a fire deadline reading the carrier's own rxn decay (the
     // wave-31/32-mined LAW-1 candidate), or the splay itself.
     if(hind_stand_hold(hl)){
      auto p1=e.point(points_[hind_heel_pt_[hl]].index,points_[hind_heel_pt_[hl]].local).first;
      auto p2=e.point(points_[hind_mp_pt_[hl]].index,points_[hind_mp_pt_[hl]].local).first;
      for(int i2=0;i2<3;++i2)hind_step_stand_from_[hl][i2]=(p1[i2]+p2[i2])/2.;
      hind_step_stand_mp_[hl]=s_.q[hind_coord_[hl][3]];
      if(!hind_step_stand_[hl]){
       // THE FLOOR ANCHOR (the second amendment): the pads' HEIGHT is captured
       // ONCE at the arm tick -- the vault must roll the body OVER the pinned
       // pads (the planar position stays re-captured, the pads slide with the
       // drag), only the unload-lift's HEIGHT demand is held down.
       hind_step_stand_y_[hl]=hind_step_stand_from_[hl][1];
       hind_step_stand_[hl]=true;
#ifdef GAIT_EVENT_TRACE
       std::fprintf(stderr,"[hindstep] standhold leg=%zu tick=%llu swing_stall=%llu\n",
        hl,(unsigned long long)ticks_,(unsigned long long)hind_step_stall_[hl==0?1:0]);
#endif
      }
      ++hind_step_stand_ticks_[hl];}
     else hind_step_stand_[hl]=false;
     hind_step_stand_latch_[hl]=false;hind_step_stand_pivot_[hl]=false;
     bool live_slot=phi_[hl]>=TOE_OFF&&touching_prev_[hl];
     bool alt_fire=hind_step_alt_due_[hl]!=0&&touching_prev_[hl];
     // THE COMPLETION-TICK RE-LOCK (wave 37, the fourth clause): on the
     // completion tick itself (ticks_ == the binding unload deadline, which
     // kUnloadTicks=1 makes the other's last TD tick) the alternation fire
     // attempt YIELDS the standing leg's transient band-edge graze and
     // proceeds on hind_alt_due alone -- the deadline's own transient-dip
     // precedence extended to the graze. The machine's own guards keep the
     // scope inside the hand-off class (the loop's mode-0 continue; N ==
     // deadline names the completion tick by construction); the yield
     // changes no read and adds no bound. Zero new numeric constants.
     if(!touching_prev_[hl]&&hind_step_alt_due_[hl]!=0&&
        hind_step_dl_unload_[hl]!=0&&hind_step_deadline_tick_[hl]>0&&
        ticks_==hind_step_deadline_tick_[hl]){
      ++hind_step_graze_yields_[hl];
      if(hind_step_graze_first_[hl]<0)hind_step_graze_first_[hl]=(int)ticks_;
      alt_fire=true;}
     if(!live_slot&&!alt_fire)continue; // a live slot or a due alternation only
     bool gated=false;
     bool gated_b=false; // clause (b) is the gate holding (the wave-32 waive target)
     bool floor_gated=false;
     int live=0; // the other-three live-pad count (clause (c); trace-reported)
     if(hind_step_mode_[o]==1)gated=true;                    // (a) no double step
     else if(hind_step_last_td_[o]+1>ticks_){gated=true;gated_b=true;} // (b) the hand-off g
     else{ // (c) THE SUPPORT FLOOR: the other three legs >= 2 live pads
      for(size_t l2=0;l2<2;++l2){
       double mn=1e300;
       for(size_t k=0;k<npts_;++k)
        if(points_[k].name.rfind(l2==0?"fore_left":"fore_right",0)==0)
         mn=(std::min)(mn,gap_of(e,k));
       if(mn<=kTouch)++live;}
      double mn=1e300;
      for(size_t k=0;k<npts_;++k)
       if(points_[k].name.rfind(o==0?"left_":"right_",0)==0)
        mn=(std::min)(mn,gap_of(e,k));
      if(mn<=kTouch)++live;
      if(live<2)floor_gated=true;
      // (d) THE KICK-STAND PROMISE (wave 29, ALTERNATION fires only): the
      // alternation fire is the gate's own scheduling choice, so it must
      // PROMISE its floor -- the standing hind (the other, touching) plus
      // one fore whose own clock holds a real stance across the glide
      // (mode 0, stance remaining >= tair) or whose held-glide span covers
      // tair (the wave-24/25 measured pads-live face). MEASURED BASIS (the
      // first build's falsifier firing, reported in the receipt): a
      // transient 3-pad floor at the fire is NOT a promise -- both fores
      // left inside the glide (the L fore's scheduled 115 lift, the R
      // fore's geometric ~118 leave) and the floor ran at 1 for 8 ticks.
      // The natural SLOT fires keep the wave-28 gate (a)-(c) unchanged:
      // their floor is that census's own judged face (min 3 at the 98
      // fire), and no clock promise exists for the decayed-seated fores
      // (the wave-28b map's geometric-unload class: the in-place churn
      // holds them without a stance to cite).
      if(alt_fire&&!gated&&!floor_gated){
       bool promised=false;
       if(touching_prev_[o]){
        for(size_t l2=0;l2<2;++l2){
         double mn2=1e300;
         for(size_t k=0;k<npts_;++k)
          if(points_[k].name.rfind(l2==0?"fore_left":"fore_right",0)==0)
           mn2=(std::min)(mn2,gap_of(e,k));
         if(mn2>kTouch)continue;
         if((fore_mode_[l2]==0&&fore_stance_[l2]-fore_t_[l2]>=tair)||
            (fore_mode_[l2]==1&&fore_glide_held(l2)&&fore_hold_last_[l2]-fore_t_[l2]>=tair)){
          promised=true;break;}}}
       if(!promised)floor_gated=true;}
     }
     // THE DEADLINE (the fold's precedence): at the budget's deadline
     // arithmetic the floor clauses (c)/(d) yield -- a forced fold-liftoff
     // kills the walk, a floor dip is transient and healed by the replant.
     // THE WAVE-32 UNLOAD-LIFT DEADLINE: clause (b) yields too -- the armed
     // unload bound IS the other's band entry tick, the very tick (b) guards,
     // so (b)'s one-tick hand-off would consume the whole window the law
     // exists to spend (the unload lands at entry+1). The waive is PROVABLY
     // INERT for the fold class: the +35 form lies 34 ticks past (b)'s
     // one-tick window, so only the armed unload term can ever engage it.
     // Clause (a) (the no-double-step) NEVER yields. Counted per leg; the
     // trace-only line reports each waive (never owned silent).
     bool deadline_fire=hind_step_alt_due_[hl]!=0&&hind_step_deadline_tick_[hl]>0&&
      ticks_>=hind_step_deadline_tick_[hl];
     if(floor_gated&&deadline_fire){floor_gated=false;++hind_step_deadline_fires_[hl];}
     // THE WAIVE-ERA HAND-OFF PRESERVATION (wave 36, the third clause): the
     // (b)-waive may not fire for the hand-off OUT of a waive-ridden swing --
     // when this leg's own waive fire postdates the other's current-swing
     // launch, the hand-off rides the natural g=1 clause (b) and lands at the
     // completion + 1 (the shipped grid tick); the disarm self-expires at the
     // other's next fire. The wave-35 build-2 face this owns: the repaired
     // concentration re-armed the (b)-waive ON the perturbed 174 completion and
     // the completion-tick-locked calendar re-phased -1 (the dead-pad fire at
     // 201, the impact death at 266).
     bool waive_ridden=hind_step_waive_last_[hl]>(int)hind_step_last_fire_[o];
     if(gated_b&&deadline_fire){
      if(waive_ridden){++hind_step_handoff_restores_[hl];}
      else{gated=false;gated_b=false;++hind_step_deadline_fires_[hl];
       if(hind_step_dl_unload_[hl])++hind_step_unload_fires_[hl];
#ifdef GAIT_EVENT_TRACE
       std::fprintf(stderr,"[hindstep] unloadgate leg=%zu tick=%llu dl=%llu class=%s\n",
        hl,(unsigned long long)ticks_,(unsigned long long)hind_step_deadline_tick_[hl],
        hind_step_dl_unload_[hl]?"unload":"fold");
#endif
      }}
     // THE CARRIER SELF-UNLOAD FIRE DEADLINE, TICKED BY THE REAL SWING (the
     // wave-36 law's first clause, the wave-35 build-1 gate VERBATIM; receipt
     // wave 35 measured the gate TRUE -- the first waive fire EXACTLY 161,
     // dead=0, stall_era=0 -- and its cost was the CHAIN AROUND it: the
     // waive-era double-completion disarmed the wave-29 concentration read
     // (the calendar death, 305), and repairing the concentration alone let
     // the (b)-waive re-phase the calendar (the death at 266); the wave-36
     // law carries the gate VERBATIM plus the repair plus the preservation
     // clause above, so the waive's perturbation is absorbed by ONE +1
     // hand-off and the stall calendar re-locks to the shipped grid).
     // THE GATE: clause (a) yields for the carrier's alternation fire when
     // the deadline fire is binding ON THE UNLOAD FORM and the other's
     // lift-first hold has GENUINELY CLEARED (the stall swings' holds never
     // clear, so the stall eras never see the waive). ZERO new numeric
     // constants: the deadline flag, the deadline fire and the held_ read are
     // the machinery's own.
     // THE CALENDAR-ARITHMETIC WAIVE SCOPE GUARD (wave 38, the fifth
     // clause): the pose read (!hind_step_held_[o]) cannot tell a real era
     // from a stall era -- the [202,211) stall graze cleared at 206 on EVERY
     // measured trajectory (the shipped walk's own era max pair-min
     // 1.116e-05, the re-locked walk's 1.147e-05, both past the 1.1e-05
     // release bound). The era's CLASS the calendar arithmetic owns: this
     // leg's own just-completed era ran the stall cadence (its length ==
     // tair, the machine's own constant) iff the other's current era is that
     // chain's next link. The waive rides REAL swings only: the yield
     // additionally requires the link test to FAIL. The pose read stays
     // byte-verbatim -- the guard only REMOVES openings (the chain-head case
     // the pose read correctly holds: the R's 175 decision on the L's
     // [175,184) head, the R's own last era 14 ticks). ZERO new numeric
     // constants.
     bool stall_era_link=hind_step_last_td_[hl]!=0&&
      hind_step_last_td_[hl]-hind_step_last_fire_[hl]==tair;
     if(gated&&!gated_b&&!floor_gated&&alt_fire&&hind_step_dl_unload_[hl]&&
        deadline_fire&&!hind_step_held_[o]){
      if(stall_era_link){
       if(hind_step_guard_first_[hl]<0)hind_step_guard_first_[hl]=(int)ticks_;
       ++hind_step_guard_blocks_[hl];
#ifdef GAIT_EVENT_TRACE
       std::fprintf(stderr,"[hindstep] guardblock leg=%zu tick=%llu dl=%llu link_td=%llu link_fire=%llu\n",
        hl,(unsigned long long)ticks_,(unsigned long long)hind_step_deadline_tick_[hl],
        (unsigned long long)hind_step_last_td_[hl],(unsigned long long)hind_step_last_fire_[hl]);
#endif
      }else{
      gated=false;++hind_step_waive_fires_[hl];
      if(hind_step_waive_first_[hl]<0)hind_step_waive_first_[hl]=(int)ticks_;
      hind_step_waive_last_[hl]=(int)ticks_;
#ifdef GAIT_EVENT_TRACE
      std::fprintf(stderr,"[hindstep] waivefire leg=%zu tick=%llu dl=%llu\n",
       hl,(unsigned long long)ticks_,(unsigned long long)hind_step_deadline_tick_[hl]);
#endif
      }}
#ifdef GAIT_EVENT_TRACE
     if(alt_fire)std::fprintf(stderr,"[hindgate] tick=%llu leg=%zu live=%d tL=%d sL=%.1f tR=%d sR=%.1f hL=%d hR=%d gated=%d floor=%d dl=%llu v=%.3f\n",
      (unsigned long long)ticks_,hl,live,
      fore_mode_[0]==0?(int)fore_t_[0]:-1,fore_stance_[0]-fore_t_[0],
      fore_mode_[1]==0?(int)fore_t_[1]:-1,fore_stance_[1]-fore_t_[1],
      fore_glide_held(0)?1:0,fore_glide_held(1)?1:0,
      gated,floor_gated,(unsigned long long)hind_step_deadline_tick_[hl],s_.v[3]);
#endif
     if(gated||floor_gated){++hind_step_gated_[hl];continue;}
     // FIRE: the wave-20 glide, hind side. The class recorded; the
     // LIFT-FIRST HOLD armed (the target holds at the spot + arch until the
     // release quantum clears).
     hind_step_mode_[hl]=1;hind_step_t_[hl]=0.;
     hind_step_alt_[hl]=live_slot?0:1;
     hind_step_held_[hl]=true;hind_step_clear_tick_[hl]=-1;hind_step_stall_[hl]=0;
     ++hind_step_fires_[hl];hind_step_last_fire_[hl]=ticks_;
     auto p1=e.point(points_[hind_heel_pt_[hl]].index,points_[hind_heel_pt_[hl]].local).first;
     auto p2=e.point(points_[hind_mp_pt_[hl]].index,points_[hind_mp_pt_[hl]].local).first;
     V from{(p1[0]+p2[0])/2,(p1[1]+p2[1])/2,(p1[2]+p2[2])/2};
     hind_step_from_[hl]=from;hind_step_plant_y_[hl]=from[1];
     hind_step_ap_[hl]=s_.q[hind_coord_[hl][0]]+s_.q[hind_coord_[hl][1]]+s_.q[hind_coord_[hl][2]];
     hind_step_mp_[hl]=s_.q[hind_coord_[hl][3]];
     hind_step_branch_[hl]=s_.q[hind_coord_[hl][1]]>=0.?1:-1;
     double xoff=(std::max)(0.,s_.v[3])*(DUTY_SAMPLED*T_CYCLE)/2.;
     auto hip=e.point(pelvis_row_,hind_mount_[hl]).first;
     double h=(std::max)(0.,hip[1]-hind_step_plant_y_[hl]);
     double a2m=hind_L1_+hind_L2_;
     double dxs=hind_xm_*std::cos(hind_step_ap_[hl]);
     double dys=h+hind_xm_*std::sin(hind_step_ap_[hl]);
     double under=a2m*a2m-dys*dys;
     double xmax=dxs+(under>0.?std::sqrt(under):0.);
     if(xoff>xmax){xoff=xmax;++hind_step_clamped_[hl];}
     hind_step_xoff_[hl]=xoff;
     hind_step_to_[hl]=V{hip[0]+xoff,hind_step_plant_y_[hl],from[2]};
     {double qh,qk,qa;hind_step_ik(hl,e,from,qh,qk,qa);
      hind_step_qerr_[hl]=(std::max)(std::abs(qh-s_.q[hind_coord_[hl][0]]),
       (std::max)(std::abs(qk-s_.q[hind_coord_[hl][1]]),std::abs(qa-s_.q[hind_coord_[hl][2]])));}
#ifdef GAIT_EVENT_TRACE
     std::fprintf(stderr,"[hindstep] fire leg=%zu tick=%llu phi=%.5f class=%s from=(%.6f,%.6f) to=(%.6f,%.6f) xoff=%.6f v=%.6f qerr=%.3e ap=%.4f br=%+d dl=%llu\n",
      hl,(unsigned long long)ticks_,phi_[hl],hind_step_alt_[hl]?"alt":"slot",from[0],from[1],hind_step_to_[hl][0],hind_step_to_[hl][1],
      xoff,s_.v[3],hind_step_qerr_[hl],hind_step_ap_[hl],hind_step_branch_[hl],
      (unsigned long long)hind_step_deadline_tick_[hl]);
#endif
    }}}
  // 2) reflex on the tick-start state (armed only in the walk, and only when
  //    the capture reflex is enabled -- F-G6's disarmed control leg). THE
  //    WAVE-21 ARMING LAW: the containment test runs on the TRUE monotone-chain
  //    hull (the chain out-param), not on the sorted point cloud -- the
  //    misfire's measured arming defect (receipt_wave21.json).
  {auto e=evaluate(s_);std::vector<std::pair<double,double>> hull,chain;V com{};
   bool inside=support_state(e,hull,com);(void)inside;
   if(walking&&config_["capture_enabled"].get<bool>()){
    support_state(e,chain,com,&chain);
    capture_reflex(e,chain,com);}}
  // 3) integrate 4 substeps; the tau input is the controller's capped PD;
  //    the per-drive store bisection (40-step, the qualified law) scales tau
  //    so each drive's positive substep work fits ITS store.
  Dense impulse_torque(n_,0.);
  adv_calls_=0;
  // Planted-strut saturation census (wave 12): once per tick, on the
  // tick-start state -- did the body walk the shoulder outside the chain's
  // reachable annulus? Counted, reported in status; never hidden.
  if(paws_captured_){auto e0=evaluate(s_);
   for(size_t leg=0;leg<2;++leg){
    if(fore_ik(leg,e0).saturated)++ik_sat_ticks_[leg];}}
  const size_t NST=nd_+1; // the leg drives + the trunk-pitch posture drive
  for(int k=0;k<4;++k){
   auto tau=servo();
   Dense scales(NST,1.);
   auto effort=[&](){Dense t(tau);for(size_t d=0;d<nd_;++d)t[drives_[d].coordinate]*=scales[d];t[2]*=scales[nd_];return t;};
   auto work_of=[&](const State& s){Dense w(NST,0.);for(size_t d=0;d<nd_;++d){size_t c=drives_[d].coordinate;w[d]=(std::max)(0.,s.work[c]-s_.work[c]);}w[nd_]=(std::max)(0.,s.work[2]-s_.work[2]);return w;};
   auto trial=advance(s_,dt_/4,effort());
   for(int round=0;round<8;++round){
    bool scaled=false;
    auto w=work_of(trial);
    for(size_t d=0;d<NST;++d){
     if(!config_["power"].get<bool>())continue;
     if(d<nd_?!config_[drives_[d].name+"_drive"].get<bool>():!config_["posture_drive"].get<bool>())continue;
     double store=d<nd_?battery_[d]:battery_post_;
     if(w[d]>store){double lo=0,hi=1;
      for(int j=0;j<40;++j){double mid=(lo+hi)/2;scales[d]=mid;
       auto candidate=advance(s_,dt_/4,effort());
       if(work_of(candidate)[d]<=store){lo=mid;trial=std::move(candidate);}else hi=mid;}
      scales[d]=lo;scaled=true;}}
    if(!scaled)break;
    trial=advance(s_,dt_/4,effort());
    auto wf=work_of(trial);
    for(size_t d=0;d<NST;++d){double store=d<nd_?battery_[d]:battery_post_;
     if(wf[d]>store&&round==7)throw Refusal("gait_store_cap_unresolved");}}
   auto spent=work_of(trial);
   for(size_t d=0;d<NST;++d){size_t c=d<nd_?drives_[d].coordinate:2;
    double before=d<nd_?battery_[d]:battery_post_;
    if(d<nd_)battery_[d]-=spent[d];else battery_post_-=spent[nd_];
    double after=d<nd_?battery_[d]:battery_post_;
    require(after>=0,"gait_negative_store");
    bool enabled=config_["power"].get<bool>()&&(d<nd_?config_[drives_[d].name+"_drive"].get<bool>():config_["posture_drive"].get<bool>());
    if(!enabled)require(spent[d]==0.,"gait_disabled_drive_spent");
    if(before>1e-12&&after<=1e-12){if(d<nd_)++empty_events_[d];else ++empty_post_;}
    if(d<nd_)brake_[d]+=(std::max)(0.,s_.work[c]-trial.work[c]);else brake_post_+=(std::max)(0.,s_.work[c]-trial.work[c]);
    impulse_torque[c]+=tau[c]/4;
    if(d<nd_)require(std::isfinite(trial.q[c])&&std::isfinite(trial.v[c])&&trial.q[c]>=model_->lower[c]-1e-9&&trial.q[c]<=model_->upper[c]+1e-9,"gait_state_invalid");}
   for(size_t i=0;i<NB;++i){require(std::isfinite(trial.q[i])&&std::isfinite(trial.v[i]),"gait_base_state_invalid");
    if(i==2)continue; // the trunk-pitch posture drive: admitted source architecture (the paper's theta_HAT musculature)
    require(trial.work[i]==0,"gait_base_actuator_work");require(tau[i]==0,"gait_base_torque");}
   s_=std::move(trial);}
  last_torque_=impulse_torque;++ticks_;}
 J status()const{
  auto e=evaluate(s_);
  double kinetic=.5*inner(s_.v,multiply(e.mass,s_.v)),u=e.potential; // absolute; the ledger works in deltas below
  J joints=J::array();double work=0,battery_total=0,brake_total=0;uint64_t empty_total=0;
  // Fore targets mirror servo() exactly (wave 12): the planted-paw IK after
  // the settle capture, the statics pose before it, 0 with the clock frozen.
  bool walking_st=config_["gait_enabled"].get<bool>();
  auto foreTgt=[&](const Drive& dr)->double{
   size_t leg=dr.leg=="fore_left"?0:1;
   if(!walking_st||!paws_captured_)return dr.joint=="shoulder"?fore_pose_sh_:fore_pose_el_;
   ForeIK ik=fore_ik(leg,e);
   return dr.joint=="shoulder"?ik.q1:ik.q2;};
  for(size_t d=0;d<nd_;++d){const Drive& dr=drives_[d];size_t c=dr.coordinate;work+=s_.work[c];battery_total+=battery_[d];brake_total+=brake_[d];empty_total+=empty_events_[d];
   double qstar[4];tables_.at(phi_[dr.leg=="left"?0:1],qstar);double target=(dr.leg=="fore_left"||dr.leg=="fore_right")?foreTgt(dr):qstar[dr.joint=="hip"?0:dr.joint=="knee"?1:dr.joint=="ankle"?2:3];
   joints.push_back({{"name",dr.name},{"leg",dr.leg},{"joint",dr.joint},{"phase",phi_[dr.leg=="left"?0:1]},
    {"angle_deg",s_.q[c]*180/pi},{"target_rad",target},{"target_deg",target*180/pi},{"speed_rad_s",s_.v[c]},
    {"motor_torque_N_m",last_torque_[c]},{"drive_enabled",config_[dr.name+"_drive"]},{"torque_cap_N_m",dr.cap},
    {"battery_J",battery_[d]},{"brake_heat_J",brake_[d]},{"empty_events",empty_events_[d]},{"actuator_work_J",s_.work[c]}});}
  // The trunk-pitch posture drive (the source model's theta_HAT musculature).
  // WAVE 15: the reported target mirrors servo()'s post_amp() law exactly.
  {work+=s_.work[2];battery_total+=battery_post_;brake_total+=brake_post_;empty_total+=empty_post_;
   double trunk_amp=post_amp();
   joints.push_back({{"name","trunk_pitch_HAT"},{"leg","trunk"},{"joint","posture"},{"phase",phi_[0]},
    {"angle_deg",s_.q[2]*180/pi},{"target_rad",trunk_amp*tables_.trunk_target(phi_[0])},
    {"target_deg",trunk_amp*tables_.trunk_target(phi_[0])*180/pi},{"speed_rad_s",s_.v[2]},
    {"motor_torque_N_m",last_torque_[2]},{"drive_enabled",config_["posture_drive"]},{"torque_cap_N_m",drives_[0].cap},
    {"battery_J",battery_post_},{"brake_heat_J",brake_post_},{"empty_events",empty_post_},{"actuator_work_J",s_.work[2]}});}
  double friction_heat_total=0,reaction_total=0,impact_heat_total=0;bool cone_valid=true;
  J points=J::array();
  for(size_t k=0;k<npts_;++k){double g=gap_of(e,k);bool touching=contact_&&g<=kTouch;
   double reaction=s_.contact_force_impulse[k]/dt_,friction_force=s_.friction_force_impulse[k]/dt_;
   auto j_t1=tangent_row(e,k,0),j_t2=tangent_row(e,k,2);V slip_v{};
   for(size_t i=0;i<n_;++i){slip_v[0]+=j_t1[i]*s_.v[i];slip_v[2]+=j_t2[i]*s_.v[i];}
   double slip=std::hypot(slip_v[0],slip_v[2]);
   friction_heat_total+=s_.friction_heat[k];impact_heat_total+=s_.contact_impact[k];reaction_total+=reaction;
   if(touching)cone_valid=cone_valid&&std::abs(friction_force)<=mu_*reaction+1e-9&&reaction>=-1e-9;
   auto cop=sole_position(e,k);
   points.push_back({{"name",points_[k].name},{"body",points_[k].body},{"position_m",cop},{"gap_m",g},{"touching",touching},
    {"reaction_N",reaction},{"friction_force_N",friction_force},{"slip_speed_m_s",slip},
    {"impact_heat_J",s_.contact_impact[k]},{"friction_heat_J",s_.friction_heat[k]},
    {"impact_impulse_N_s",s_.contact_impact_impulse[k]},{"normal_impulse_N_s",s_.contact_force_impulse[k]}});}
  std::vector<std::pair<double,double>> hull;V com{};
  bool com_in_hull=support_state(e,hull,com);
  J hullj=J::array();for(auto& h:hull)hullj.push_back(J::array({h.first,h.second}));
  J support{{"plane_world_up_m",plane_world_y_},{"points",hullj},{"com_projection_east_m",com[0]},
   {"com_projection_south_m",com[2]},{"com_up_m",com[1]},{"com_in_hull",com_in_hull&&hull.size()>=3},
   {"hull_size",hull.size()},{"assembly_mass_kg",mtot_},{"weight_N",mtot_*norm(gravity_)}};
  double impact_heat_total2=impact_heat_total+s_.impact;
  // Ledger (the free-root identities, gait books): potential measured from
  // the reset pose (recomputed from the stored default pose, deterministic,
  // no hidden state); external = the scripted push's work on the pelvis.
  double u0;{State r;r.q=model_->defaults;r.v=Dense(n_,0.);u0=evaluate(r).potential;}
  // LEDGER BASELINE (20260919 wave 4): the identities measure FROM the
  // reset state's actual mechanical energy. The old u0 (the standing-pose
  // potential, v=0) silently offset every gait-entry walk by the injected
  // KE + pose offset (-0.59 J at tick 0, growing as the walk ran) -- the
  // meter, not the walk, was broken.
  double bal=kinetic+(u-u0)-(e_ref_-u0)-work-s_.external+s_.damping+impact_heat_total2+friction_heat_total-s_.constraint_work;
  double stor=kinetic+(u-u0)-(e_ref_-u0)+battery_total+s_.damping+impact_heat_total2+friction_heat_total+brake_total-store_total_-s_.external-s_.constraint_work;
  J energy{{"kinetic_J",kinetic},{"gravitational_J",u-u0},{"potential_reference","reset pose"},{"mechanical_J",kinetic+(u-u0)},
   {"actuator_work_J",work},{"external_work_J",s_.external},
   {"damping_heat_J",s_.damping},{"impact_heat_J",impact_heat_total2},{"friction_heat_J",friction_heat_total},
   {"brake_heat_J",brake_total},{"battery_J",battery_total},{"battery_initial_J",store_total_},
   {"battery_usable",battery_total>1e-12},
   {"constraint_work_J",s_.constraint_work},{"balance_error_J",bal},{"store_balance_error_J",stor}};
  J gait{{"cycle_duration_s",T_CYCLE},{"duty_factor_sampled",DUTY_SAMPLED},{"servo_frequency_Hz",FS_HZ},
   {"phase_left",phi_[0]},{"phase_right",phi_[1]},{"phase_offset",std::fmod(phi_[1]-phi_[0]+1.,1.)},
   {"capture_events",capture_events_},{"touching_left",touching_prev_[0]},{"touching_right",touching_prev_[1]}};
  // THE PLANTED STRUT (wave 12) + THE STEPPING CLOCK (wave 13): paw
  // diagnostics -- held/glided target, tracked error, closure round-trip and
  // capture qerr, saturation census, clock phase/mode/schedule.
  {J forepaw=J::array();
   for(size_t leg=0;leg<2;++leg){
    if(paws_captured_){auto pw=e.point(points_[fore_paw_point_[leg]].index,paw_ref_local_[leg]).first;
     // WAVE 23 instrumentation: the shoulder's world seat, the UNCLAMPED
     // branch solution, the ACTUAL joints' min headroom to their four walls,
     // and the wave-23 law censuses. Read-only: no servo byte depends on it.
     auto shw=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;
     ForeIK ikd=fore_ik(leg,e);
     size_t c1=fore_coord_[leg][0],c2=fore_coord_[leg][1];
     double h1=(std::min)(s_.q[c1]-model_->lower[c1],model_->upper[c1]-s_.q[c1]);
     double h2=(std::min)(s_.q[c2]-model_->lower[c2],model_->upper[c2]-s_.q[c2]);
     uint64_t pins=0,pins_air=0;const std::string lg=leg==0?"fore_left":"fore_right";
     for(size_t d=0;d<nd_;++d)if(drives_[d].leg==lg){pins+=wall_pins_[d];pins_air+=wall_pins_air_[d];}
     forepaw.push_back({{"leg",leg==0?"fore_left":"fore_right"},{"target_m",{paw_target_[leg][0],paw_target_[leg][1]}},
      {"error_m",std::hypot(pw[0]-paw_target_[leg][0],pw[1]-paw_target_[leg][1])},
      {"ik_roundtrip_m",ik_roundtrip_m_[leg]},{"ik_qerr_rad",ik_qerr_[leg]},
      {"ik_saturated_ticks",ik_sat_ticks_[leg]},
      {"shoulder_m",{shw[0],shw[1]}},
      {"ik_q1_unc_rad",ikd.q1_raw},{"ik_q2_unc_rad",ikd.q2_raw},
      {"wall_headroom_rad",(std::min)(h1,h2)},
      {"wall_bound_ticks",fore_wall_bound_[leg]},{"wall_follows",fore_wall_follows_[leg]},
      {"wall_pins",pins},{"wall_pins_air",pins_air},
      {"wait_override_fires",fore_wait_fires_[leg]},
      {"fore_mode",fore_mode_[leg]==1?"swing":"stance"},{"td_count",fore_td_[leg]},
      {"replants",fore_replants_[leg]},{"annulus_clamped_plants",fore_clamped_[leg]},
      {"entry_replant",fore_entry_[leg]==1},{"gate_hold_ticks",fore_gate_holds_[leg]},
      {"glide_hold",fore_glide_hold_[leg]==1&&fore_t_[leg]<fore_hold_last_[leg]&&fore_t_[leg]+1.<fore_cycle_[leg]},
      {"glide_hold_last",fore_hold_last_[leg]},
      {"grid_converged",fore_conv_[leg]==1},
      {"t_in_cycle",fore_t_[leg]},{"stance_ticks",fore_stance_[leg]},{"cycle_ticks",fore_cycle_[leg]}});}
    else forepaw.push_back({{"leg",leg==0?"fore_left":"fore_right"},{"captured",false}});}
   gait["fore_paw"]=forepaw;gait["fore_paw_captured"]=paws_captured_;
   // THE HIND EXTENSION LAW's census block (wave 27): the emergency's state,
   // read by the F-G27 height census. Read-only.
   gait["height_hold"]={{"armed",hind_height_hold_armed_},{"latched",hind_height_hold_latched_},
    {"fire_tick",hind_height_fire_tick_},{"fire_margin_m",hind_height_fire_margin_},
    {"fires",hind_height_fires_}};
   // THE HIND STEP LAW's census block (wave 28): the step clocks and their
   // counters, read by the F-G28 census. Read-only. The hind drives' stop
   // pins (loaded/airborne) are summed per leg here -- the wave-23 array
   // covers all 12 drives but only the fore legs were exposed before.
   {J hs=J::array();
    for(size_t hl=0;hl<2;++hl){
     uint64_t hp=0,hpa=0;const std::string lg=hl==0?"left":"right";
     for(size_t d=0;d<nd_;++d)if(drives_[d].leg==lg){hp+=wall_pins_[d];hpa+=wall_pins_air_[d];}
     hs.push_back({{"leg",lg},{"mode",hind_step_mode_[hl]==1?"step":"stance"},
      {"t",hind_step_t_[hl]},{"fires",hind_step_fires_[hl]},{"tds",hind_step_tds_[hl]},
      {"gated",hind_step_gated_[hl]},{"reach_clamped",hind_step_clamped_[hl]},
      {"last_fire_tick",hind_step_last_fire_[hl]},{"last_td_tick",hind_step_last_td_[hl]},
      {"from_x",hind_step_from_[hl][0]},{"to_x",hind_step_to_[hl][0]},
      {"plant_y",hind_step_plant_y_[hl]},{"xoff_m",hind_step_xoff_[hl]},
      {"held_ap_deg",hind_step_ap_[hl]*180/pi},{"branch",hind_step_branch_[hl]},
      {"fire_qerr_rad",hind_step_qerr_[hl]},
      {"wall_pins",hp},{"wall_pins_air",hpa},{"phase",phi_[hl]},
      // THE HIND ALTERNATION LAW's census fields (wave 29). Read-only.
      {"fire_class",hind_step_alt_[hl]==1?"alternation":"slot"},
      {"held",hind_step_held_[hl]},{"clear_tick",hind_step_clear_tick_[hl]},
      {"hold_ticks",hind_step_hold_ticks_[hl]},
      {"alt_due",hind_step_alt_due_[hl]!=0},
      {"deadline_tick",hind_step_deadline_tick_[hl]},
      {"deadline_fires",hind_step_deadline_fires_[hl]},
      {"fold_budget_ticks",(double)kFoldBudgetTicks},
      // THE UNLOAD-LIFT DEADLINE's census fields (wave 32). Read-only.
      {"deadline_unload",hind_step_dl_unload_[hl]!=0},
      {"unload_fires",hind_step_unload_fires_[hl]},
      // THE STAND-FIRST HOLD's census fields (wave 33). Read-only.
      {"swing_stall_ticks",hind_step_stall_[hl]},
      {"stand_hold",hind_step_stand_[hl]},
      {"stand_hold_ticks",hind_step_stand_ticks_[hl]},
      // THE LATCHED WORLD-PIVOT HOLD's census fields (wave 34). Read-only.
      {"stand_latch",hind_step_stand_latch_[hl]},
      {"stand_pivot",hind_step_stand_pivot_[hl]},
      {"stand_release",hind_step_stand_release_[hl]},
      {"stand_latch_ticks",hind_step_stand_latch_ticks_[hl]},
      // THE CARRIER SELF-UNLOAD FIRE DEADLINE's census fields (wave 35). Read-only.
      {"waive_fires",hind_step_waive_fires_[hl]},
      {"waive_first_tick",hind_step_waive_first_[hl]},
      {"waive_last_tick",hind_step_waive_last_[hl]},
      // THE COMPLETION-TICK RE-LOCK's census fields (wave 37). Read-only.
      {"graze_yields",hind_step_graze_yields_[hl]},
      {"graze_first_tick",hind_step_graze_first_[hl]},
      // THE CALENDAR-ARITHMETIC WAIVE SCOPE GUARD's census fields (wave 38). Read-only.
      {"guard_blocks",hind_step_guard_blocks_[hl]},
      {"guard_first_tick",hind_step_guard_first_[hl]},
      // THE WAIVE-ERA HAND-OFF PRESERVATION's census fields (wave 36). Read-only.
      {"handoff_restores",hind_step_handoff_restores_[hl]},
      {"alt_repairs",hind_alt_repairs_[hl]}});}
    gait["hind_step"]=hs;}}
  return {{"sim_time_s",ticks_*dt_},{"ticks",ticks_},{"mode","native_gait_walker"},{"joints",joints},
   {"config",config_},{"power",config_["power"]},{"gait",gait},
   {"contact",{{"enabled",contact_},{"friction",mu_>0},{"friction_mu",mu_},{"plane_world_up_m",plane_world_up_m()},{"points",points},
     {"reaction_N",reaction_total},{"friction_heat_J",friction_heat_total},{"cone_valid",cone_valid}}},
   {"support",support},{"energy",energy},
   {"base_q",{s_.q[3],s_.q[4],s_.q[5]}},
   {"body",{{"position_m",add(vector(e.frames[0].t,V{},1),shift_)},{"radius_m",0.05}}}};
 }
 double plane_world_up_m()const{return plane_world_y_;}
};
} // namespace chimera::multibody
