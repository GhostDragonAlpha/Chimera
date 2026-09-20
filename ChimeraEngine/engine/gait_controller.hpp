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
  static double interp(const double* t,double phi){phi-=std::floor(phi);double x=phi*20.;int k=(int)x;if(k>=20)k=19;double f=x-k;return t[k]*(1.-f)+t[k+1]*f;}
  void at(double phi,double out[4])const{out[0]=interp(hip,phi)+zeros[0];out[1]=interp(knee,phi)+zeros[1];out[2]=interp(ankle,phi)+zeros[2];out[3]=interp(mp,phi)+zeros[3];}
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
 std::vector<double> posture_phi_,posture_theta_; // theta*(phi): the derived trunk-pitch freedom (wave 8)
 double e_ref_=0; // the LEDGER BASELINE: the reset state's actual mechanical energy (the gait entry injects pose+momentum the standing-pose reference never sees; measured offset -0.59 J at tick 0 before this)
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
 // Contact-reset hybrid clock (Section 5.1): advance by sim time, RESET to 0
 // at the leg's own kTouch crossing (a leg is touching when ANY of its foot
 // points is inside the band). Returns true when a reset fired this tick.
 bool update_clock(const Evaluation& e,double dt){
  bool reset_fired=false;
  for(size_t leg=0;leg<2;++leg){
   bool touching=false;const char* prefix=leg==0?"left":"right";
   for(size_t k=0;k<npts_;++k)if(points_[k].name.rfind(prefix,0)==0&&gap_of(e,k)<=kTouch)touching=true;
   if(touching&&!touching_prev_[leg]){phi_[leg]=0.;reset_fired=true;}
   else phi_[leg]=std::fmod(phi_[leg]+dt/T_CYCLE+(leg==0?0.:0.5),1.);
   touching_prev_[leg]=touching;}
  return reset_fired;}
 // Support hull + CoM (Section 5.4). Returns com_in_hull; sets hull/com refs.
 bool support_state(const Evaluation& e,std::vector<std::pair<double,double>>& hull,V& com)const{
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
  h.resize(k-1);double px=com[0],pz=com[2];bool inside=true;int side=0;
  for(size_t i=0;i<h.size();++i){auto&a=h[i];auto&b=h[(i+1)%h.size()];double cross=(b.first-a.first)*(pz-a.second)-(b.second-a.second)*(px-a.first);
   if(std::abs(cross)<1e-15)continue;int s=cross>0?1:-1;if(side==0)side=s;else if(s!=side){inside=false;break;}}
  return inside;}
 // Capture-step reflex (Section 5.4): CoM projection outside the hull moving
 // outward -> swing leg phase jumps to 0.95 (early touchdown). Falsified by
 // F-G6: without it a push must tip; with it the capture step must land.
 void capture_reflex(const Evaluation& e,const std::vector<std::pair<double,double>>& hull,const V& com){
  if(hull.size()<3)return;
  // Outward-velocity probe: pelvis horizontal speed (base trans rows 3,5).
  double vx=s_.v[3],vz=s_.v[5];
  for(size_t i=0;i<hull.size();++i){auto&a=hull[i];auto&b=hull[(i+1)%hull.size()];
   double ex=b.first-a.first,ez=b.second-a.second,nx=ez,nz=-ex;double nl=std::hypot(nx,nz);if(nl<1e-12)continue;nx/=nl;nz/=nl;
   // outward normal = pointing away from hull centroid
   double cx=0,cz=0;for(auto&p:hull){cx+=p.first;cz+=p.second;}cx/=hull.size();cz/=hull.size();
   if((com[0]-cx)*nx+(com[2]-cz)*nz<0){nx=-nx;nz=-nz;}
   bool outside=(com[0]-a.first)*nx+(com[2]-a.second)*nz>1e-9;
   if(outside&&(vx*nx+vz*nz)>0){
    // capture with the SWING leg (the non-touching one; if both or neither,
    // the nearer-to-liftoff phase drives).
    for(size_t leg=0;leg<2;++leg){bool touching=false;const char* prefix=leg==0?"left":"right";
     for(size_t k=0;k<npts_;++k)if(points_[k].name.rfind(prefix,0)==0&&gap_of(e,k)<=kTouch)touching=true;
     if(!touching){phi_[leg]=CAPTURE_PHI;++capture_events_;return;}}
    return;}}}
 Dense servo()const{ // capped mass-normalized PD at the derived 4.0 Hz (Section 5.2)
  Dense tau(n_,0.);
  bool walking=config_["gait_enabled"].get<bool>();
  for(size_t d=0;d<nd_;++d){const Drive& dr=drives_[d];size_t c=dr.coordinate;
   if(!config_["power"].get<bool>()||!config_[dr.name+"_drive"].get<bool>()||battery_[d]<=1e-12)continue;
   // Stage E -> F handoff: with the clock frozen (gait_enabled=false) the
   // drives hold the MODEL DEFAULTS -- the flat-footed standing pose the
   // seating scan proves supportable -- not the TD columns (a pointe-feet
   // pose is not a static stand). The tables engage with the walk.
   double target=0.;
   if(walking){double qstar[4];tables_.at(phi_[dr.leg=="left"?0:1],qstar);target=qstar[dr.joint=="hip"?0:dr.joint=="knee"?1:dr.joint=="ankle"?2:3];}
   tau[c]=(std::max)(-dr.cap,(std::min)(dr.cap,kp_[d]*(target-s_.q[c])-kd_[d]*s_.v[c]));}
  // The source model's POSTURE CONTROL (the pinned fulltext: the trunk pitch
  // theta_HAT is a model DOF driven by hip uniarticular muscles -- iliopsoas
  // and gluteus medius -- as one-sided reflexes toward the trunk target):
  // realized as the same mass-normalized PD on the trunk pitch toward the
  // model's authored erect default (zero), capped at the hip moment (the same
  // musculature carries the trunk moment). Active whenever the power is on:
  // it is what makes stage E's stand a stand.
  if(config_["power"].get<bool>()&&config_["posture_drive"].get<bool>()&&battery_post_>1e-12){
   // THE TRUNK-PITCH FREEDOM (wave 8): the posture target is the derived
   // theta*(phi) of the STANCE leg -- the trunk is a load-bearing DOF (the
   // statics: theta* centers the leg demands inside their caps; leaning
   // forward 5-30 deg over the loaded leg is the vault's posture). Absent
   // table -> the erect default 0 (the pre-wave-8 pin).
   double target_post=0.;
   if(posture_phi_.size()>=2){
    double phi=(touching_prev_[0]&&!touching_prev_[1])?phi_[0]:(!touching_prev_[0]&&touching_prev_[1])?phi_[1]:std::min(phi_[0],phi_[1]);
    if(phi<=posture_phi_.front())target_post=posture_theta_.front();
    else if(phi>=posture_phi_.back())target_post=posture_theta_.back();
    else{size_t k=1;while(posture_phi_[k]<phi)++k;
     double f=(phi-posture_phi_[k-1])/(posture_phi_[k]-posture_phi_[k-1]);
     target_post=posture_theta_[k-1]*(1.-f)+posture_theta_[k]*f;}}
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
   auto ee=evaluate(start);for(size_t k=0;k<npts_;++k){auto pp=ee.point(points_[k].index,points_[k].local);std::fprintf(stderr,"    %-12s gap=%.3e vy=%+.3e\n",points_[k].name.c_str(),pp.first[1]+points_[k].radius-plane_model_y_,pp.second[1]);}
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
   auto ee=evaluate(start);for(size_t k=0;k<npts_;++k){auto pp=ee.point(points_[k].index,points_[k].local);std::fprintf(stderr,"    %-12s gap=%.3e vy=%+.3e\n",points_[k].name.c_str(),pp.first[1]+points_[k].radius-plane_model_y_,pp.second[1]);}}
#endif
   require(clamps<64,"gait_impact_event_budget");
   State pinned=start;
   if(which>=0){size_t pc=drives_[size_t(which)].coordinate;
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
  n_=model_->names.size();require(n_>NB&&n_==NB+2*NLEG,"gait_coordinate_capacity");
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
 if(recipe_.contains("zero_map_rad")){
  const J& zm=recipe_.at("zero_map_rad");
  require(zm.contains("hip")&&zm.contains("knee")&&zm.contains("ankle")&&zm.contains("MP"),"gait_zero_map_keys");
  tables_.zeros[0]=number(zm.at("hip"));tables_.zeros[1]=number(zm.at("knee"));
  tables_.zeros[2]=number(zm.at("ankle"));tables_.zeros[3]=number(zm.at("MP"));
  for(double z:tables_.zeros)require(std::isfinite(z)&&std::abs(z)<=3.,"gait_zero_map_range");}
 // theta*(phi): the derived posture target table (wave 8)
 if(recipe_.contains("posture_target_rad")&&recipe_.contains("posture_target_phases")){
  const J& tt=recipe_.at("posture_target_rad");const J& tp=recipe_.at("posture_target_phases");
  require(tt.is_array()&&tp.is_array()&&tt.size()==tp.size()&&tt.size()>=2,"gait_posture_table_shape");
  for(size_t k=0;k<tt.size();++k){posture_phi_.push_back(number(tp[k]));posture_theta_.push_back(number(tt[k]));
   require(std::isfinite(posture_theta_.back())&&std::abs(posture_theta_.back())<=1.0,"gait_posture_table_range");}
  for(size_t k=1;k<posture_phi_.size();++k)require(posture_phi_[k]>posture_phi_[k-1],"gait_posture_table_monotone");}
  plane_world_y_=number(recipe_.at("contact_plane_height_m"));require(std::isfinite(plane_world_y_),"gait_contact_plane_invalid");plane_model_y_=plane_world_y_-shift_[1];
  require(config_.contains("contact_enabled")&&config_["contact_enabled"].is_boolean(),"gait_contact_flag_invalid");contact_=config_["contact_enabled"].get<bool>();
  require(config_.contains("contact_friction")&&config_["contact_friction"].is_number()&&number(config_["contact_friction"])>=0&&number(config_["contact_friction"])<=1,"gait_friction_flag_invalid");mu_=number(config_["contact_friction"]);
  require(recipe_.contains("contact_points")&&recipe_.at("contact_points").is_array()&&!recipe_.at("contact_points").empty(),"gait_contact_points");
  for(const J& p:recipe_.at("contact_points")){ContactPoint out;out.name=p.at("name").get<std::string>();out.body=p.at("body").get<std::string>();
   out.index=model_->body(out.body);out.local=p.at("point_m").get<V>();
   out.radius=number(p.at("radius_m"));require(out.radius>0,"gait_contact_radius_invalid");points_.push_back(out);}
  npts_=points_.size();require(npts_>=1&&npts_<=6,"gait_contact_capacity");
  // Drives: the recipe lists them AFTER the six base coordinates, in leg
  // pairs; the mass-normalized gains use the DEFAULTS-pose diagonal (the
  // qualified mass-normalized PD), the DERIVED f_s and the qualified zeta.
  const J& dj=recipe_.at("drives");require(dj.is_array()&&dj.size()==2*NLEG,"gait_drive_count");
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
  reset();}
 double timestep()const{return dt_;}const Dense& angles()const{return s_.q;}const Dense& speeds()const{return s_.v;}const Model& model()const{return *model_;}
 const Dense& batteries()const{return battery_;}double phase(size_t leg)const{return phi_[leg];}uint64_t capture_events()const{return capture_events_;}
 void reset(){
  s_=State(n_,npts_);s_.q=model_->defaults;s_.v=Dense(n_,0.);ticks_=0;capture_events_=0;last_torque_=Dense(n_,0.);
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
    double qstar[4];tables_.at(phi_[dr.leg=="left"?0:1],qstar);
    int ji=dr.joint=="hip"?0:dr.joint=="knee"?1:dr.joint=="ankle"?2:3;
    s_.q[dr.coordinate]=qstar[ji];
    double p=phi_[dr.leg=="left"?0:1],dp=0.05;double a1[4],a2[4];
    tables_.at(p+dp,a1);tables_.at(p-dp,a2);
    s_.v[dr.coordinate]=(a1[ji]-a2[ji])/(2*dp*T_CYCLE);}
   if(config_.contains("base_speed_x_m_s"))s_.v[3]=number(config_["base_speed_x_m_s"]);}
  auto e=evaluate(s_);
  for(size_t leg=0;leg<2;++leg){bool touching=false;const char* prefix=leg==0?"left":"right";
   for(size_t k=0;k<npts_;++k)if(points_[k].name.rfind(prefix,0)==0&&gap_of(e,k)<=kTouch)touching=true;
   touching_prev_[leg]=touching;}
  for(size_t k=0;k<npts_;++k)require(gap_of(e,k)>0,"gait_initial_penetration");
  e_ref_=mechanical(s_);} // baseline the ledger at the ACTUAL initial state (entry pose + injected momentum)
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
  bool walking=config_["gait_enabled"].get<bool>();
  // 1) clock update at the tick start (contact reset dominates).
  {auto e=evaluate(s_);if(walking)update_clock(e,dt_);else{for(size_t leg=0;leg<2;++leg){bool touching=false;const char* prefix=leg==0?"left":"right";
   for(size_t k=0;k<npts_;++k)if(points_[k].name.rfind(prefix,0)==0&&gap_of(e,k)<=kTouch)touching=true;touching_prev_[leg]=touching;}}}
  // 2) reflex on the tick-start state (armed only in the walk, and only when
  //    the capture reflex is enabled -- F-G6's disarmed control leg).
  {auto e=evaluate(s_);std::vector<std::pair<double,double>> hull;V com{};
   bool inside=support_state(e,hull,com);(void)inside;
   if(walking&&config_["capture_enabled"].get<bool>())capture_reflex(e,hull,com);}
  // 3) integrate 4 substeps; the tau input is the controller's capped PD;
  //    the per-drive store bisection (40-step, the qualified law) scales tau
  //    so each drive's positive substep work fits ITS store.
  Dense impulse_torque(n_,0.);
  adv_calls_=0;
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
  for(size_t d=0;d<nd_;++d){const Drive& dr=drives_[d];size_t c=dr.coordinate;work+=s_.work[c];battery_total+=battery_[d];brake_total+=brake_[d];empty_total+=empty_events_[d];
   double qstar[4];tables_.at(phi_[dr.leg=="left"?0:1],qstar);double target=qstar[dr.joint=="hip"?0:dr.joint=="knee"?1:dr.joint=="ankle"?2:3];
   joints.push_back({{"name",dr.name},{"leg",dr.leg},{"joint",dr.joint},{"phase",phi_[dr.leg=="left"?0:1]},
    {"angle_deg",s_.q[c]*180/pi},{"target_rad",target},{"target_deg",target*180/pi},{"speed_rad_s",s_.v[c]},
    {"motor_torque_N_m",last_torque_[c]},{"drive_enabled",config_[dr.name+"_drive"]},{"torque_cap_N_m",dr.cap},
    {"battery_J",battery_[d]},{"brake_heat_J",brake_[d]},{"empty_events",empty_events_[d]},{"actuator_work_J",s_.work[c]}});}
  // The trunk-pitch posture drive (the source model's theta_HAT musculature).
  {work+=s_.work[2];battery_total+=battery_post_;brake_total+=brake_post_;empty_total+=empty_post_;
   joints.push_back({{"name","trunk_pitch_HAT"},{"leg","trunk"},{"joint","posture"},{"phase",0.},
    {"angle_deg",s_.q[2]*180/pi},{"target_rad",0.},{"target_deg",0.},{"speed_rad_s",s_.v[2]},
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
  return {{"sim_time_s",ticks_*dt_},{"ticks",ticks_},{"mode","native_gait_walker"},{"joints",joints},
   {"config",config_},{"power",config_["power"]},{"gait",gait},
   {"contact",{{"enabled",contact_},{"friction",mu_>0},{"friction_mu",mu_},{"plane_world_up_m",plane_world_up_m()},{"points",points},
     {"reaction_N",reaction_total},{"friction_heat_J",friction_heat_total},{"cone_valid",cone_valid}}},
   {"support",support},{"energy",energy},
   {"body",{{"position_m",add(vector(e.frames[0].t,V{},1),shift_)},{"radius_m",0.05}}}};
 }
 double plane_world_up_m()const{return plane_world_y_;}
};
} // namespace chimera::multibody
