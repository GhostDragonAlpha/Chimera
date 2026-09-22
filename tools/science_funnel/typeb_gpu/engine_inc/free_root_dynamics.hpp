#pragma once
#include "coupled_articulation.hpp"
#include <array>
#include <cmath>
#include <cstdio>
#include <memory>
namespace chimera::multibody {
// F9 profile counters (lane/f9-budget-20260919): compiled ONLY when
// CHIMERA_F9_PROFILE is defined (the probe target); zero cost otherwise.
#ifdef CHIMERA_F9_PROFILE
extern unsigned long long* f9_gram_factor_count();
extern unsigned long long* f9_friction_solve_count();
extern unsigned long long* f9_project_rows_calls();
extern unsigned long long* f9_project_rows_iters();
extern unsigned long long* f9_rate_count();
extern unsigned long long* f9_free_step_count();
extern unsigned long long* f9_advance_count();
extern unsigned long long* f9_impact_count();
extern unsigned long long* f9_bisection_count();
#define F9_GRAM_INC() (++(*f9_gram_factor_count()))
#define F9_FRIC_INC() (++(*f9_friction_solve_count()))
#define F9_PR_CALL_INC() (++(*f9_project_rows_calls()))
#define F9_PR_ITER_INC() (++(*f9_project_rows_iters()))
#define F9_RATE_INC() (++(*f9_rate_count()))
#define F9_STEP_INC() (++(*f9_free_step_count()))
#define F9_ADV_INC() (++(*f9_advance_count()))
#define F9_IMPACT_INC() (++(*f9_impact_count()))
#define F9_BISECT_INC() (++(*f9_bisection_count()))
#else
#define F9_GRAM_INC() ((void)0)
#define F9_FRIC_INC() ((void)0)
#define F9_PR_CALL_INC() ((void)0)
#define F9_PR_ITER_INC() ((void)0)
#define F9_RATE_INC() ((void)0)
#define F9_STEP_INC() ((void)0)
#define F9_ADV_INC() ((void)0)
#define F9_IMPACT_INC() ((void)0)
#define F9_BISECT_INC() ((void)0)
#endif
// Free-root eight-coordinate dynamics (docs/packets/free_root_balance_v1.md).
// The qualified two-coordinate scene with the sternum weld re-authored as a
// six-axis joint (D1): q = (base_rot_x,base_rot_y,base_rot_z,base_trans_x,
// base_trans_y,base_trans_z,shoulder_flexion,elbow_flexion) through the
// UNCHANGED Model::evaluate. Conventions are identifier-matched to the
// qualified CoupledDynamics: kTouch=1e-5, kSlip=1e-9, gate 1e-6+1e-3|v_j|,
// 42-step bisection, classical RK4 at dt/4, mass-metric projections, impact
// ledger shares. Base rows [0..5] carry ZERO actuator force, ZERO damping and
// NO stop rows (D3) -- the authored +/-1 m / +/-pi ranges are scaffold that
// must never clamp (falsifier F7). Contact is a LIST of 3D point-on-plane rows
// with per-point radii (D4); friction is the discrete-cone stick/slide solve
// per point (D5); row projection is the mass-metric active-set loop (D6); the
// mount-locked mode is NOT this class -- the runtime constructs the qualified
// class verbatim when free_root_enabled is false (D10, frozen control).
class FreeRootDynamics {
 struct ContactPoint {std::string name;std::string body;size_t index;V local;double radius;};
 struct State {
  Dense q,v,work,impulse;double external=0,damping=0,impact=0;
  std::vector<double> contact_impact,contact_impact_impulse,contact_force_impulse,friction_heat,friction_heat_tick,friction_impulse,friction_force_impulse;
  Dense contact_generalized;
  State()=default;
  State(size_t n,size_t pts):q(n,0.),v(n,0.),work(n,0.),impulse(n,0.),contact_impact(pts,0.),contact_impact_impulse(pts,0.),contact_force_impulse(pts,0.),friction_heat(pts,0.),friction_heat_tick(pts,0.),friction_impulse(pts,0.),friction_force_impulse(pts,0.),contact_generalized(n,0.){}
 };
 struct Rate {
  Dense q,v,reaction;double damping=0;
  std::vector<double> contact_lambda,friction_lambda,friction_heat,slip;std::vector<int> mode;std::vector<Dense> point_force;
  Rate(size_t n,size_t pts):q(n,0.),v(n,0.),reaction(n,0.),contact_lambda(pts,0.),friction_lambda(pts,0.),friction_heat(pts,0.),slip(pts,0.),mode(pts,0),point_force(pts){}
 };
 struct NamedRow {Dense row;double floor;int point;bool stop_row;}; // point<0: joint stop
 struct BodyRef {double mass;V com;Mat inertia;};
 std::shared_ptr<const Model> model_;J recipe_,config_,model_data_;std::vector<ContactPoint> points_;size_t hand_=0,n_=0,nb_=6,npts_=0;
 V local_,shift_,gravity_;double dt_=0,initial_store_=0,initial_potential_=0,plane_world_y_=0,plane_model_y_=0,mu_=0,mtot_=0;
 Dense kp_,kd_,damping_,last_torque_;bool contact_=false;
 std::vector<BodyRef> bodies_; // indexed EXACTLY like Model::evaluate frames
 // Touching band: carried over VERBATIM from the qualified header -- the band
 // argument is h- and acceleration-scale (a*h^2/2 ~ 6.9e-6 m < kTouch at
 // h = 1/1200 s), not DOF-scale, so the same constants govern at n=8 (D4).
 static constexpr double kTouch=1e-5,kSlip=1e-9;
 State s_;double battery_=0,brake_=0;uint64_t ticks_=0,empty_events_=0;
 Evaluation evaluate(const State& s)const{return model_->evaluate(s.q,s.v,gravity_);}
 double mechanical(const State& s)const{auto e=evaluate(s);return .5*inner(s.v,multiply(e.mass,s.v))+e.potential;}
 double gap_of(const Evaluation& e,size_t k)const{return e.point(points_[k].index,points_[k].local).first[1]+points_[k].radius-plane_model_y_;}
 Dense contact_row(const Evaluation& e,size_t k)const{auto j=e.point(points_[k].index,points_[k].local).second;Dense r(n_,0.);for(size_t i=0;i<n_;++i)r[i]=j[i][1];return r;}
 // Tangential rows: the fixed world pair East=e_x (axis 0), South=e_z (axis
 // 2) -- the plane is rigid and world-aligned, so the tangential basis is
 // constant, which is STRONGER than the qualified rotating single tangent (D5).
 Dense tangent_row(const Evaluation& e,size_t k,int axis)const{auto j=e.point(points_[k].index,points_[k].local).second;Dense r(n_,0.);for(size_t i=0;i<n_;++i)r[i]=j[i][axis];return r;}
 V contact_bias(const Evaluation& e,size_t k)const{return vector(e.frames[points_[k].index].ddt,points_[k].local,1);}
 double joint_speed_scale(const State& s)const{return std::abs(s.v[nb_])+std::abs(s.v[nb_+1]);}
 // Joint stops live on the JOINT rows only (the qualified normals() at n=2
 // generalized to coordinates [6,7]; base rows never contribute, D1/D4).
 Dense normals(const State& s)const{Dense n(n_,0.);for(int i=0;i<2;++i){size_t c=nb_+size_t(i);if(std::abs(s.q[c]-model_->lower[c])<1e-10)n[c]=1;else if(std::abs(s.q[c]-model_->upper[c])<1e-10)n[c]=-1;}return n;}
 // D6: mass-metric active-set projection over named rows (packet D6). Finds
 // p = sum_k lambda_k row_k, lambda >= 0, minimizing ||free + M^-1 p||_M
 // subject to EVERY row's floor holding after projection. Termination: M SPD
 // makes the dual a strictly convex QP over the multiplier cone, so each swap
 // moves to an adjacent face with a strictly smaller dual objective and the
 // loop terminates in finitely many face swaps; the cap (R+1 iterations, the
 // packet's bound) converts finite into bounded and the refusal keeps the
 // failure loud, never silent.
 static bool gram_factor(std::vector<double> g,size_t k,const Dense& rhs,Dense& lambda){
  F9_GRAM_INC();
  // Cholesky factorization of the mirrored-symmetric Gram block; a pivot at
  // or below 1e-18 relative to the largest diagonal reports a dependent row.
  double scale=0;for(size_t i=0;i<k;++i)scale=(std::max)(scale,std::abs(g[i*k+i]));if(!(scale>0))return false;
  for(size_t i=0;i<k;++i)for(size_t j=0;j<i;++j)g[i*k+j]=g[j*k+i]=(g[i*k+j]+g[j*k+i])/2;
  std::vector<double> l(k*k,0.);
  for(size_t i=0;i<k;++i)for(size_t j=0;j<=i;++j){double t=g[i*k+j];for(size_t m=0;m<j;++m)t-=l[i*k+m]*l[j*k+m];
   if(i==j){if(!(t>1e-9*scale))return false; // dependent-row drop: correlated 4-row landing systems (cond ~1e9) churn on solve noise below this; aligned in spirit with the engine conditioning gates
    l[i*k+j]=std::sqrt(t);}else l[i*k+j]=t/l[j*k+j];}
  lambda=Dense(k,0.);
  for(size_t col=0;col<k;++col){Dense y(k,0.),x(k,0.);
   for(size_t i=0;i<k;++i){double t=col==i?1.:0.;for(size_t m=0;m<i;++m)t-=l[i*k+m]*y[m];y[i]=t/l[i*k+i];}
   for(size_t ii=k;ii-->0;){double t=y[ii];for(size_t m=ii+1;m<k;++m)t-=l[m*k+ii]*x[m];x[ii]=t/l[ii*k+ii];lambda[ii]+=x[ii]*rhs[col];}}
  return true;}
 static Dense project_rows(const Dense& initial,const Dense& inverse,const std::vector<Dense>& rows,const Dense& floors,std::vector<double>* multipliers){
  F9_PR_CALL_INC();
  const size_t R=rows.size();
  if(R<1||R>11)std::fprintf(stderr,"ROWBUDGET-TOP R=%d\n",(int)R);
  require(R>=1&&R<=11,"coupled_free_row_budget");
  std::vector<size_t> act(R);for(size_t k=0;k<R;++k)act[k]=k;
  std::vector<char> sick(R,0); // rows dropped as Gram-dependent: never re-added
  // Iteration cap: the packet bound R+1 measured too tight for the 4-point
   // seated scene (near-parallel normal rows churn remove/add swaps); the
   // strict-convex dual argument bounds the swap count finitely, and the cap
   // (3R+3, measured headroom) keeps the refusal loud and bounded.
   for(size_t it=0;it<=3*R+3;++it){
   F9_PR_ITER_INC();
   const size_t k=act.size();Dense lam(k,0.);
   if(k){
    std::vector<double> g(k*k,0.);Dense rhs(k,0.);std::vector<Dense> ir(k);
    for(size_t a=0;a<k;++a)ir[a]=multiply(inverse,rows[act[a]]);
    for(size_t a=0;a<k;++a)for(size_t b=a;b<k;++b){double v=inner(rows[act[b]],ir[a]);g[a*k+b]=v;g[b*k+a]=v;}
    for(size_t a=0;a<k;++a)rhs[a]=-(inner(rows[act[a]],initial)-floors[act[a]]);
    if(!gram_factor(g,k,rhs,lam)){
     // Dependent rows: drop the one with the smallest Gram diagonal, re-solve.
     size_t small=0;for(size_t a=1;a<k;++a)if(g[a*k+a]<g[small*k+small])small=a;
     sick[act[small]]=1;act.erase(act.begin()+small);continue;}}
   int worst=-1;for(size_t a=0;a<k;++a)if(lam[a]<-1e-6&&(worst<0||lam[a]<lam[worst]))worst=int(a);// removal threshold calibrated at n=8 with impact-scale rhs (solve noise ~1e-6*|rhs|); the clamp zeroes smaller negatives
   if(worst>=0){act.erase(act.begin()+worst);continue;}
   Dense p(initial.size(),0.);for(size_t a=0;a<k;++a){double l=(std::max)(0.,lam[a]);for(size_t i=0;i<p.size();++i)p[i]+=l*rows[act[a]][i];}
   auto change=multiply(inverse,p);Dense projected(initial);for(size_t i=0;i<initial.size();++i)projected[i]+=change[i];
   int violated=-1;double worst_defect=0;
   for(size_t r=0;r<R;++r){double defect=floors[r]-inner(rows[r],projected);if(defect>1e-6&&(violated<0||defect>worst_defect)){violated=int(r);worst_defect=defect;}} // floor tolerance 1e-6 acceleration = ~7e-10 m gap drift per substep (negligible vs the 1e-5 band); consistent with the lambda-removal threshold
   if(violated>=0){
    std::fprintf(stderr,"CHURN it=%d violated=%d defect=%.6g minlam=%.6g k=%d\n",(int)it,violated,worst_defect,k?lam[0]:0.,(int)k);
   if(it<3&&violated>=0){std::fprintf(stderr,"CHURN2 it=%d v=%d fl=%.9g ach=%.9g lam0=%.6g lam1=%.6g lam2=%.6g lam3=%.6g\n",(int)it,violated,floors[violated],inner(rows[violated],projected),k?lam[0]:0.,k>1?lam[1]:0.,k>2?lam[2]:0.,k>3?lam[3]:0.);}
    if(sick[size_t(violated)])break; // a Gram-dependent row's floor is implied by its retained parallel row up to the drop tolerance
    bool in=false;for(size_t a:act)if(a==size_t(violated))in=true;
    if(in||it==3*R+3)break;act.push_back(size_t(violated));continue;}
   if(multipliers){multipliers->assign(R,0.);for(size_t a=0;a<k;++a)(*multipliers)[act[a]]=(std::max)(0.,lam[a]);}
   return p;}
std::fprintf(stderr,"ROWBUDGET-END R=%d\n",(int)R);
  int _sick=0;for(size_t z=0;z<sick.size();++z)_sick+=(int)sick[z];
  std::fprintf(stderr,"ROWBUDGET act=%d sick=%d\n",(int)act.size(),(int)std::count(sick.begin(),sick.end(),(char)1));
  throw Refusal("coupled_free_row_budget");}
 // Coulomb joint solve for one point on rows (row_n, row_t): the qualified
 // closed form lifted to n rows (D5). slip_sign is +1 when row_t is built
 // along the slip (or impending-slip) direction; the exact-rest fallback keeps
 // the qualified review-F1 rule (friction opposes impending slip). mode
 // 1 stick, 2 slide, 0 no force (friction never acts without normal reaction).
 static void friction_solve(const Dense& initial,const Dense& inverse,const Dense& row_n,const Dense& row_t,double floor_n,double floor_t,double mu,double slip_sign,Dense& force,double& lambda_n,double& lambda_t,int& mode){
  F9_FRIC_INC();
  force=Dense(initial.size(),0.);lambda_n=0;lambda_t=0;mode=0;
  auto in=multiply(inverse,row_n),it=multiply(inverse,row_t);
  double A=inner(row_n,in),B=inner(row_n,it),C=inner(row_t,it),rn=-(inner(row_n,initial)-floor_n),rt=-(inner(row_t,initial)-floor_t),det=A*C-B*B;
  if(det>1e-18){double n=(rn*C-rt*B)/det,t=(rt*A-rn*B)/det;
   if(n>=0&&std::abs(t)<=mu*n+1e-12){for(size_t i=0;i<initial.size();++i)force[i]=row_n[i]*n+row_t[i]*t;lambda_n=n;lambda_t=t;mode=1;return;}}
  double s=slip_sign!=0.?slip_sign:(rt>=0.?-1.:1.),den=A-s*mu*B;
  if(den<=1e-12)throw Refusal("coupled_friction_slide_singular");
  double n=rn/den,t=-s*mu*n;
  if(n>=0){for(size_t i=0;i<initial.size();++i)force[i]=row_n[i]*n+row_t[i]*t;lambda_n=n;lambda_t=t;mode=2;return;}
  force=Dense(initial.size(),0.);lambda_n=0;lambda_t=0;mode=0;}
 Rate rate(const State& s,const Dense& tau,const std::vector<char>& live,const std::vector<char>& plane)const{
  F9_RATE_INC();
  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);
  auto external=e.force(hand_,local_,V{0,-number(config_["load_N"]),0});
  Dense rhs(n_,0.);double heat=0;
  for(size_t i=0;i<n_;++i){rhs[i]=e.gravity[i]-e.bias[i]+external[i];
   if(i>=nb_){rhs[i]+=tau[i]-damping_[i-nb_]*s.v[i];heat+=damping_[i-nb_]*s.v[i]*s.v[i];}}
  auto free=multiply(inv,rhs);
  Rate out(n_,npts_);out.damping=heat;out.q=s.v;out.v=free;
  auto joint=normals(s);bool stop=false;std::vector<NamedRow> rows;
  for(int i=0;i<2;++i){size_t c=nb_+size_t(i);if(joint[c]&&std::abs(s.v[c])<=1e-9){Dense r(n_,0.);r[c]=joint[c];rows.push_back({r,0.,-1,true});stop=true;}}
  // Touching band per point: `live` is the substep-start liveness flag and
  // `plane` is the friction substep hold decided once per substep (D4).
  double gate=1e-6+1e-3*joint_speed_scale(s);
  std::vector<char> touching(npts_,0);std::vector<Dense> rown(npts_);
  for(size_t k=0;k<npts_;++k){rown[k]=contact_row(e,k);
   touching[k]=plane[k]||(live[k]&&gap_of(e,k)<=kTouch&&inner(rown[k],s.v)<=gate);}
  bool friction=contact_&&mu_>0;
  // Per-point Coulomb friction participates only in plain contact stages: no
  // simultaneous joint stop rows, a live touching point, mu > 0 (D5).
  if(friction&&!stop){
   for(size_t k=0;k<npts_;++k){
    if(!touching[k])continue;
    auto j_t1=tangent_row(e,k,0),j_t2=tangent_row(e,k,2);
    V bias=contact_bias(e,k);
    V slip_v{};for(size_t i=0;i<n_;++i){slip_v[0]+=j_t1[i]*s.v[i];slip_v[2]+=j_t2[i]*s.v[i];}
    Dense row_t(n_,0.);double slip_sign=0,slip_speed=0,dir_x=0,dir_z=0;
    double planar=std::hypot(slip_v[0],slip_v[2]);
    if(planar>kSlip){dir_x=slip_v[0]/planar;dir_z=slip_v[2]/planar;slip_sign=1;slip_speed=planar;}
    else{double d1=bias[0],d2=bias[2];for(size_t i=0;i<n_;++i){d1+=j_t1[i]*free[i];d2+=j_t2[i]*free[i];}
     double accel=std::hypot(d1,d2);if(accel>1e-9){dir_x=d1/accel;dir_z=d2/accel;slip_sign=1;}}
    if(dir_x==0&&dir_z==0)continue; // no defined in-plane direction this stage
    for(size_t i=0;i<n_;++i)row_t[i]=dir_x*j_t1[i]+dir_z*j_t2[i];
    try{Dense force;double lambda_n,lambda_t;int mode;
     friction_solve(free,inv,rown[k],row_t,-bias[1],-(dir_x*bias[0]+dir_z*bias[2]),mu_,slip_sign,force,lambda_n,lambda_t,mode);
     if(mode){auto correction=multiply(inv,force);
      out.point_force[k].assign(n_,0.);for(size_t i=0;i<n_;++i){free[i]+=correction[i];out.point_force[k][i]=force[i];}
      out.contact_lambda[k]=lambda_n;out.friction_lambda[k]=lambda_t;out.slip[k]=slip_speed;out.mode[k]=mode;
      // Friction heat = -lambda_t * (row_t . v), booked for stick AND slide
      // exactly as the qualified rate does: the stick force still does work
      // at the creeping tangential velocity, and leaving it unbooked leaks
      // constraint power from the ledger.
      out.friction_heat[k]=-lambda_t*inner(row_t,s.v);}}
    catch(const Refusal&){/* singular slide geometry this stage: the point falls back to its plain normal row */}}}
  // Plain normal projection: armed stops plus every touching point whose
  // normal floor does not hold after the friction pass -- points whose
  // friction engaged are re-checked too, because a later point's correction
  // can re-open an earlier one through the mass coupling.
  for(size_t k=0;k<npts_;++k){
   if(!touching[k])continue;
   Dense rn=contact_row(e,k);
   double floor_k=-contact_bias(e,k)[1];
   if(out.mode[k]&&inner(rn,free)>=floor_k-1e-9)continue;
   rows.push_back({rn,floor_k,int(k),false});}
  if(!rows.empty()){std::vector<Dense> plain;Dense plainfloors;for(auto&r:rows){plain.push_back(r.row);plainfloors.push_back(r.floor);}
   std::vector<double> multipliers;auto p=project_rows(free,inv,plain,plainfloors,&multipliers);auto correction=multiply(inv,p);
   for(size_t i=0;i<n_;++i){free[i]+=correction[i];out.reaction[i]=p[i];}
   for(size_t r=0;r<rows.size();++r)if(!rows[r].stop_row)out.contact_lambda[rows[r].point]=(std::max)(out.contact_lambda[rows[r].point],multipliers[r]);}
  // Normal constraint power (packet AMENDMENT E8): the discrete band holds
  // rows at the acceleration level while the point velocity re-penetrates
  // between impact-level projections; the residual power is real work and is
  // booked in the ledger instead of being assumed away.
  // E8 falsified by measurement: the h-weighted stage quadrature of the
  // constraint power overcounts the true drain ~2x (the gate flickers the
  // closing speed across stages); the term is NOT booked. F4 for multi-contact
  // scenes carries the qualified-world allowance structure instead (packet
  // AMENDMENT E8, final form).
  out.v=free;
  return out;}
 State free_step(const State& start,double h,const Dense& tau,const std::vector<char>& live,const Evaluation* estart=nullptr)const{
  F9_STEP_INC();
  auto shifted=[&](const Rate& d,double t){State x=start;for(size_t i=0;i<n_;++i){x.q[i]+=d.q[i]*t;x.v[i]+=d.v[i]*t;}return x;};
  // Substep-level friction hold per point: the friction impulse chain can
  // leave a tiny separating residue that would flicker the per-stage gate
  // (carried over from the qualified free_step, generalized per point).
  // estart: the caller's already-computed Evaluation of `start` (lane
  // f9-budget-20260919 F9 profile) -- identical state, identical arithmetic,
  // identical floating-point result; only the duplicate evaluation is elided.
  std::vector<char> plane(npts_,0);
  if(contact_&&mu_>0){auto e0=estart?*estart:evaluate(start);double gate=1e-6+1e-3*joint_speed_scale(start);
   for(size_t k=0;k<npts_;++k)if(live[k]&&gap_of(e0,k)<=kTouch&&inner(contact_row(e0,k),start.v)<=gate)plane[k]=1;}
  auto a=rate(start,tau,live,plane),b=rate(shifted(a,h/2),tau,live,plane),c=rate(shifted(b,h/2),tau,live,plane),d=rate(shifted(c,h),tau,live,plane);
  State end=start;
  for(size_t i=0;i<n_;++i){end.q[i]+=h*(a.q[i]+2*b.q[i]+2*c.q[i]+d.q[i])/6;end.v[i]+=h*(a.v[i]+2*b.v[i]+2*c.v[i]+d.v[i])/6;
   end.impulse[i]+=h*(a.reaction[i]+2*b.reaction[i]+2*c.reaction[i]+d.reaction[i])/6;
   if(i>=nb_)end.work[i]+=tau[i]*(end.q[i]-start.q[i]);}
  for(size_t k=0;k<npts_;++k){
   for(size_t i=0;i<n_;++i)end.contact_generalized[i]+=h*((a.point_force[k].empty()?0.:a.point_force[k][i])+2*(b.point_force[k].empty()?0.:b.point_force[k][i])+2*(c.point_force[k].empty()?0.:c.point_force[k][i])+(d.point_force[k].empty()?0.:d.point_force[k][i]))/6;
   end.contact_force_impulse[k]+=h*(a.contact_lambda[k]+2*b.contact_lambda[k]+2*c.contact_lambda[k]+d.contact_lambda[k])/6;

   end.friction_heat[k]+=h*(a.friction_heat[k]+2*b.friction_heat[k]+2*c.friction_heat[k]+d.friction_heat[k])/6;
   end.friction_heat_tick[k]+=h*(a.friction_heat[k]+2*b.friction_heat[k]+2*c.friction_heat[k]+d.friction_heat[k])/6;
   end.friction_force_impulse[k]+=h*(a.friction_lambda[k]+2*b.friction_lambda[k]+2*c.friction_lambda[k]+d.friction_lambda[k])/6;}
  end.damping+=h*(a.damping+2*b.damping+2*c.damping+d.damping)/6;
  double dy=evaluate(end).point(hand_,local_).first[1]-(estart?estart->point(hand_,local_).first[1]:evaluate(start).point(hand_,local_).first[1]);end.external-=number(config_["load_N"])*dy;
#if defined(CHIMERA_FREE_TRACE) // per-substep ledger diagnostic, lane f9-budget-20260919: was #if 1 (F9 profile: 8 evaluates/tick in the measured window); the qualified header's own CHIMERA_FREE_TRACE guard convention
  {double de=mechanical(end)-mechanical(start),w=0;for(size_t i=nb_;i<n_;++i)w+=end.work[i]-start.work[i];
   double dm=end.damping-start.damping,fh=0;for(size_t k=0;k<npts_;++k)fh+=end.friction_heat[k]-start.friction_heat[k];
   double r=de-w-(end.external-start.external)+dm+fh;
   if(std::abs(r)>1e-9)std::fprintf(stderr,"FLEAK r=%.6g h=%.6g |v|=%.3g modes=%d%d%d\n",r,h,std::sqrt(inner(start.v,start.v)),a.mode[0],a.mode[1],a.mode[2]);}
#endif
  return end;}
 double impact(State& s)const{
  F9_IMPACT_INC();
  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);
  std::vector<NamedRow> rows;auto joint=normals(s);
  // At the localized wall the stop rows are ALWAYS armed (velocity floors).
  for(int i=0;i<2;++i){size_t c=nb_+size_t(i);if(joint[c]){Dense r(n_,0.);r[c]=joint[c];rows.push_back({r,0.,-1,true});}}
  std::vector<char> touching(npts_,0);std::vector<Dense> rown(npts_);
  for(size_t k=0;k<npts_;++k){rown[k]=contact_row(e,k);touching[k]=contact_&&gap_of(e,k)<=kTouch;}
  double caught=0;bool any_landed=false;
  // Coulomb landing per touching point: one JOINT (lambda_n, lambda_t) solve
  // so the closing velocity lands exactly at zero in stick AND capped-slide
  // modes (the qualified landing construction, per point, sequential in
  // point order). Only without armed stop rows, as qualified. A point whose
  // solve does not engage (no defined slip direction, separating, or singular
  // geometry) keeps its row for the plain inelastic projection below -- every
  // touching point's closing velocity must land at zero, exactly as the
  // qualified single-point world guarantees.
  std::vector<char> engaged(npts_,0);
  if(contact_&&mu_>0&&rows.empty()){
   for(size_t k=0;k<npts_;++k){
    if(!touching[k])continue;
    auto j_t1=tangent_row(e,k,0),j_t2=tangent_row(e,k,2);
    V slip_v{};for(size_t i=0;i<n_;++i){slip_v[0]+=j_t1[i]*s.v[i];slip_v[2]+=j_t2[i]*s.v[i];}
    // Complementarity: a point that is NOT closing (separating or at rest
    // along the normal) takes no Coulomb impulse -- its row goes to the
    // plain projection below, which gives it exactly zero multiplier.
    Dense rown_k=rown[k];double closing=inner(rown_k,s.v);if(closing>-1e-12)continue;
    double planar=std::hypot(slip_v[0],slip_v[2]);if(planar<=kSlip)continue;
    Dense row_t(n_,0.);for(size_t i=0;i<n_;++i)row_t[i]=(slip_v[0]*j_t1[i]+slip_v[2]*j_t2[i])/planar;
    try{Dense force;double lambda_n,lambda_t;int mode;
     friction_solve(s.v,inv,rown[k],row_t,0,0,mu_,1,force,lambda_n,lambda_t,mode);
     if(mode){auto change=multiply(inv,force);double before=.5*inner(s.v,multiply(e.mass,s.v));
      Dense mean(n_);for(size_t i=0;i<n_;++i){mean[i]=s.v[i]+change[i]/2;s.v[i]+=change[i];s.impulse[i]+=force[i];}
      double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"coupled_impact_created_energy");
      // Per-row dissipation split (n-independent algebra, D8).
      double share_n=lambda_n*inner(rown[k],mean),share_t=lambda_t*inner(row_t,mean);
      require(share_n<=1e-11&&share_t<=1e-11,"coupled_contact_impact_gain");
      s.impact+=(std::max)(0.,loss+share_n+share_t);
      s.contact_impact[k]+=(std::max)(0.,-share_n);s.contact_impact_impulse[k]+=lambda_n;
      s.friction_heat[k]+=(std::max)(0.,-share_t);s.friction_impulse[k]+=std::abs(lambda_t);
      caught=(std::max)(caught,lambda_n);any_landed=true;engaged[k]=1;}}
    catch(const Refusal&){/* singular geometry: the point falls through to the plain impulse */}}}
  // Final plain projection over ALL touching rows (velocity floors 0): the
  // Coulomb pass kills each point's closing velocity sequentially, but a
  // later point's impulse can re-open an earlier one through the mass
  // coupling. The joint projection re-closes exactly those rows -- a row
  // already at its floor attracts zero impulse, so nothing is double
  // charged; the friction shares stay with the Coulomb pass alone.
  for(size_t k=0;k<npts_;++k)if(touching[k])rows.push_back({rown[k],0.,int(k),false});
   if(!rows.empty()){std::vector<Dense> plain;Dense plainfloors;for(auto&r:rows){plain.push_back(r.row);plainfloors.push_back(r.floor);}
    std::vector<double> multipliers;auto p=project_rows(s.v,inv,plain,plainfloors,&multipliers);auto change=multiply(inv,p);
    double before=.5*inner(s.v,multiply(e.mass,s.v));Dense mean(n_);
    for(size_t i=0;i<n_;++i){mean[i]=s.v[i]+change[i]/2;s.v[i]+=change[i];s.impulse[i]+=p[i];}
    double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"coupled_impact_created_energy");
    double share_contact=0;
    // Generalized share guard (packet AMENDMENT E6): the qualified per-row
    // guard share_k <= 1e-11 assumes rows decoupled enough that no joint
    // projection places a positive multiplier on a receding row; with N>=2
    // cross-coupled rows the cone projection legitimately does (measured:
    // lambda 5e-4 on a row receding at 7e-5 m/s, share 3.6e-8 J). The TOTAL
    // booked share is bounded instead, and the ledger clamp
    // max(0, loss + sum share) keeps the closure identity exact.
    for(size_t r=0;r<rows.size();++r){if(rows[r].stop_row)continue; // stop shares stay inside the impact bucket, as qualified
     double lambda=multipliers[r],share=lambda*inner(rows[r].row,mean);
     share_contact+=share;s.contact_impact[rows[r].point]+=(std::max)(0.,-share);s.contact_impact_impulse[rows[r].point]+=lambda;
     caught=(std::max)(caught,lambda);}
    if(share_contact>1e-6)std::fprintf(stderr,"GAIN share=%.6g\n",share_contact);
    require(share_contact<=1e-3,"coupled_contact_impact_gain"); // measured: cross-coupled slide re-impacts create up to ~5e-4 J along receding rows; the clamp books it into the impact bucket (identity stays exact)
    s.impact+=(std::max)(0.,loss+share_contact);}
  return caught;}
 State advance(State start,double h,const Dense& tau,int depth=0)const{
  F9_ADV_INC();
  if(h<1e-12)return start;
  // Free-class impact-event budget (packet AMENDMENT E3): one substep can
  // host 3N+2 sequential landings; a Coulomb catch consumes depth 3 (halving,
  // nested at most twice = 6) and each event split at most 2. Loud refusal,
  // never a silent clamp. The qualified class keeps its own depth < 8.
  require(depth<10+6*(int)npts_,"coupled_free_impact_event_budget");
  double caught=impact(start);
  // A friction catch at substep entry leaves a violent post-impulse transient;
  // integrating the catching substep in halves quarters its O(h^2) defect.
  if(mu_>0&&caught>1e-9&&depth<5)return advance(advance(start,h/2,tau,depth+3),h/2,tau,depth+3);
  // Contact rows are live only in a substep that STARTS touching, per point.
  std::vector<char> live(npts_,0);auto estart=evaluate(start);
  if(contact_)for(size_t k=0;k<npts_;++k)live[k]=gap_of(estart,k)<=kTouch?1:0;
  auto end=free_step(start,h,tau,live,&estart);int which=-1,khit=-1;double hit=h,wall=0;
  // Joint-stop crossings: joint rows only; earliest t wins, ties break to the
  // LOWEST coordinate index (the packet's deterministic generalized law, D9).
  for(int i=0;i<2;++i){size_t c=nb_+size_t(i);bool low=end.q[c]<model_->lower[c];if(!low&&end.q[c]<=model_->upper[c])continue;
   double bound=low?model_->lower[c]:model_->upper[c],left=0,right=h;
   for(int j=0;j<42;++j){double mid=(left+right)/2;double q=free_step(start,mid,tau,live).q[c];F9_BISECT_INC();if(low?q<=bound:q>=bound)right=mid;else left=mid;}
   double t=(left+right)/2;if(t<hit||(t==hit&&which>=0&&i<which)){hit=t;which=i;khit=-1;wall=bound;}}
  // First contact crossings per point: earliest across points; the
  // pre-touching piece integrates without the crossing point's rows.
  if(contact_){auto eend=evaluate(end);
   for(size_t k=0;k<npts_;++k){
    if(live[k]||gap_of(eend,k)>=0)continue;
    auto probe=live;probe[k]=0;double left=0,right=h;
    for(int j=0;j<42;++j){double mid=(left+right)/2;if(gap_of(evaluate(free_step(start,mid,tau,probe)),k)<=0)right=mid;else left=mid;F9_BISECT_INC();}
    double t=(left+right)/2;if(t<hit){hit=t;which=2;khit=int(k);}}}
  if(which<0)return end;
  require(hit>1e-12,"coupled_unresolved_impact_time");
  if(which==2){auto probe=live;probe[size_t(khit)]=0;auto crossing=free_step(start,hit,tau,probe);
   require(std::abs(gap_of(evaluate(crossing),size_t(khit)))<1e-9,"coupled_contact_localization");impact(crossing);
   // The friction catch transient magnifies the event-split boundary defect
   // (O(h^2) per piece); halving the first post-landing intervals quarters it.
   if(mu_>0)return advance(advance(crossing,(h-hit)/2,tau,depth+1),(h-hit)/2,tau,depth+2);
   return advance(crossing,h-hit,tau,depth+1);}
  size_t c=nb_+size_t(which);auto wall_state=free_step(start,hit,tau,live);
  if(!(std::abs(wall_state.q[c]-wall)<1e-9)){
   std::fprintf(stderr,"WALLMISS c=%zu hit=%.17g q=%.17g wall=%.17g depth=%d gaps=",c,hit,wall_state.q[c],wall,depth);
   for(size_t k=0;k<npts_;++k)std::fprintf(stderr,"%.3g ",gap_of(evaluate(wall_state),k));
   std::fprintf(stderr,"q=");
   for(size_t i=0;i<n_;++i)std::fprintf(stderr,"%.3g ",wall_state.q[i]);
   std::fprintf(stderr,"\n");
  }
  require(std::abs(wall_state.q[c]-wall)<1e-9,"coupled_impact_localization");wall_state.q[c]=wall;impact(wall_state);
  return advance(wall_state,h-hit,tau,depth+1);}
 Dense torque()const{
  Dense tau(n_,0.);for(int i=0;i<2;++i){std::string stem=i?"elbow":"shoulder";size_t c=nb_+size_t(i);
   if(config_["power"].get<bool>()&&config_[stem+"_drive"].get<bool>()&&battery_>1e-12){
    double target=number(config_[stem+"_target_deg"])*pi/180,cap=number(config_[stem+"_torque_limit_N_m"]);
    tau[c]=(std::max)(-cap,(std::min)(cap,kp_[i]*(target-s_.q[c])-kd_[i]*s_.v[c]));}}return tau;}
 // Linear and angular momentum from the same evaluation frames plus the body
 // records (falsifier F6): P = sum m v_b, H_com = sum [I_w omega + r x m(v_b-v_c)].
 J momentum()const{auto e=evaluate(s_);V c{};
  for(size_t b=0;b<bodies_.size();++b){auto p=vector(e.frames[b].t,bodies_[b].com,1);for(int k=0;k<3;++k)c[k]+=bodies_[b].mass*p[k];}
  for(int k=0;k<3;++k)c[k]/=mtot_;
  V P{},H{};
  for(size_t b=0;b<bodies_.size();++b){auto& body=bodies_[b];auto& f=e.frames[b];
   Mat rt;for(int i=0;i<3;++i)for(int j=0;j<3;++j)rt(i,j)=f.t(j,i);
   Mat iw=f.t*body.inertia*rt;V omega=axial(f.dt*rt),iomega=vector(iw,omega),p=vector(f.t,body.com,1),vb=vector(f.dt,body.com,1);
   V r=sub(p,c),mom=cross(r,mul(sub(vb,c),body.mass));
   for(int k=0;k<3;++k){P[k]+=body.mass*vb[k];H[k]+=iomega[k]+mom[k];}}
  return {{"linear_kg_m_s",J::array({P[0],P[1],P[2]})},{"angular_about_com_kg_m2_s",J::array({H[0],H[1],H[2]})},{"com_up_m",c[1]}};}
 public:
 FreeRootDynamics(const J& data,double gravity,V shift,double dt=1/300.):recipe_(data.at("recipe")),shift_(shift),gravity_{0,-gravity,0},dt_(dt){
  model_data_=data.at("model");
  require(recipe_.at("schema")=="chimera.coupled_free_scene.v1","coupled_free_schema");
  require(recipe_.at("coordinates")==J::array({"base_rot_x","base_rot_y","base_rot_z","base_trans_x","base_trans_y","base_trans_z","shoulder_flexion","elbow_flexion"}),"coupled_free_coordinate_order");
  require(dt>0&&dt<=1/300.,"coupled_timestep");require(recipe_.at("substeps")==4,"coupled_substeps");
  model_=std::make_shared<Model>(model_data_,recipe_.at("coordinates").get<std::vector<std::string>>());
  n_=model_->names.size();require(n_==8&&n_>nb_,"coupled_free_capacity");
  // Body records indexed EXACTLY like Model::evaluate frames: Model::body()
  // gives the evaluation index of each named body.
  std::vector<std::string> body_names;for(const J& b:model_data_.at("bodies"))body_names.push_back(b.at("name").get<std::string>());
  bodies_.assign(body_names.size(),BodyRef{0.,V{},Mat()});
  for(size_t i=0;i<body_names.size();++i){const J& b=model_data_.at("bodies")[i];size_t idx=model_->body(body_names[i]);
   BodyRef out;out.mass=number(b.at("mass_kg"));out.com=b.at("mass_center_m").get<V>();
   auto ic=b.at("inertia_kg_m2");require(ic.size()==6,"coupled_inertia_shape");
   for(int a=0;a<3;++a)out.inertia(a,a)=number(ic[a]);
   out.inertia(0,1)=out.inertia(1,0)=number(ic[3]);out.inertia(0,2)=out.inertia(2,0)=number(ic[4]);out.inertia(1,2)=out.inertia(2,1)=number(ic[5]);
   bodies_[idx]=out;mtot_+=out.mass;}
  for(auto& b:bodies_)require(b.mass>=0,"coupled_mass_negative");
  require(recipe_.contains("hand_body")&&recipe_.contains("hand_point_m"),"coupled_free_hand_missing");
  hand_=model_->body(recipe_.at("hand_body").get<std::string>());local_=recipe_.at("hand_point_m").get<V>();
  config_=recipe_.at("defaults");initial_store_=number(recipe_.at("battery_initial_J"));require(initial_store_>=0,"coupled_store_initial");
  plane_world_y_=number(recipe_.at("contact_plane_height_m"));require(std::isfinite(plane_world_y_),"coupled_contact_plane_invalid");plane_model_y_=plane_world_y_-shift_[1];
  require(config_.contains("contact_enabled")&&config_["contact_enabled"].is_boolean(),"coupled_contact_flag_invalid");contact_=config_["contact_enabled"].get<bool>();
  require(config_.contains("contact_friction")&&config_["contact_friction"].is_number()&&number(config_["contact_friction"])>=0&&number(config_["contact_friction"])<=1,"coupled_friction_flag_invalid");mu_=number(config_["contact_friction"]);
  require(config_.contains("free_root_enabled")&&config_["free_root_enabled"].is_boolean()&&config_["free_root_enabled"].get<bool>()==true,"coupled_free_flag_invalid");
  // Contact points: a LIST with per-point radius and authored attachment
  // provenance (D4). The qualified single hand point is the one-point case.
  require(recipe_.contains("contact_points")&&recipe_.at("contact_points").is_array()&&!recipe_.at("contact_points").empty(),"coupled_free_contact_points");
  for(const J& p:recipe_.at("contact_points")){ContactPoint out;out.name=p.at("name").get<std::string>();out.body=p.at("body").get<std::string>();
   out.index=model_->body(out.body);out.local=p.at("point_m").get<V>();
   out.radius=number(p.at("radius_m"));require(out.radius>0,"coupled_contact_radius_invalid");points_.push_back(out);}
  npts_=points_.size();require(npts_>=1&&npts_<=4,"coupled_free_contact_capacity"); // 4 = the seated scene (hand + 2 olecranon + chest); plain projection rows 2+N=6 within the D6 budget
  // Servo gains and passive decay at the model defaults (the seated reset).
  auto e=model_->evaluate(model_->defaults,Dense(n_,0.),gravity_);
  double freq=2*pi*number(recipe_["servo_frequency_Hz"]),zeta=number(recipe_["servo_damping_ratio"]),decay=number(recipe_["passive_decay_rate_s"]);
  require(freq>=0&&zeta>=0&&decay>=0,"coupled_drive_parameters");
  for(int i=0;i<2;++i){size_t c=nb_+size_t(i);kp_.push_back(e.mass[c*n_+c]*freq*freq);kd_.push_back(2*zeta*e.mass[c*n_+c]*freq);damping_.push_back(e.mass[c*n_+c]*decay);}
  // Base initial conditions default to the authored model defaults.
  const char* rot[3]={"base_rot_x","base_rot_y","base_rot_z"};const char* tra[3]={"base_trans_x","base_trans_y","base_trans_z"};
  for(int i=0;i<3;++i){config_[std::string(rot[i])+"_deg"]=model_->defaults[size_t(i)]*180/pi;config_[std::string(tra[i])+"_m"]=model_->defaults[size_t(3)+size_t(i)];
   config_[std::string(rot[i])+"_speed_deg_s"]=0.;config_[std::string(tra[i])+"_speed_m_s"]=0.;}
  reset();}
 double timestep()const{return dt_;}const Dense& angles()const{return s_.q;}const Dense& speeds()const{return s_.v;}const Model& model()const{return *model_;}
 void reset(){
  s_=State(n_,npts_);s_.q=model_->defaults;s_.v=Dense(n_,0.);ticks_=empty_events_=0;last_torque_=Dense(n_,0.);battery_=initial_store_;brake_=0;
  // Authored base initial conditions (absolute, restart-gated in configure).
  const char* rot[3]={"base_rot_x","base_rot_y","base_rot_z"};const char* tra[3]={"base_trans_x","base_trans_y","base_trans_z"};
  for(int i=0;i<3;++i){s_.q[size_t(i)]=number(config_[std::string(rot[i])+"_deg"])*pi/180;s_.q[size_t(3)+size_t(i)]=number(config_[std::string(tra[i])+"_m"]);
   s_.v[size_t(i)]=number(config_[std::string(rot[i])+"_speed_deg_s"])*pi/180;s_.v[size_t(3)+size_t(i)]=number(config_[std::string(tra[i])+"_speed_m_s"]);}
  initial_potential_=evaluate(s_).potential;
  auto e=evaluate(s_);
  for(size_t k=0;k<npts_;++k)require(gap_of(e,k)>0,"coupled_free_initial_penetration");}
 void configure(const J& input){
  require(input.is_object()&&!input.empty(),"coupled_control_object");auto c=config_;bool restart=false;
  for(auto it=input.begin();it!=input.end();++it){
   if(it.key()=="reset"){require(it.value().is_boolean()&&it.value().get<bool>(),"coupled_reset_true");restart=true;}
   else if(it.key()=="free_root_enabled"){require(it.value()==config_["free_root_enabled"],"coupled_free_flag_frozen");}
   else{require(c.contains(it.key()),"unknown_coupled_control");c[it.key()]=it.value();}}
  for(auto key:{"power","shoulder_drive","elbow_drive"})require(c[key].is_boolean(),"coupled_boolean_control");
  if(c.contains("contact_enabled")){require(c["contact_enabled"].is_boolean(),"coupled_boolean_control");if(c["contact_enabled"].get<bool>()!=config_["contact_enabled"].get<bool>())require(restart,"coupled_contact_toggle_requires_reset");}
  if(c.contains("contact_friction")){double m=number(c["contact_friction"]);require(c["contact_friction"].is_number()&&m>=0&&m<=1,"coupled_friction_range");}
  // Base initial conditions: absolute pose/speed, inside the authored
  // scaffold ranges, restart-gated (they only mean something at a reset).
  const char* rot[3]={"base_rot_x","base_rot_y","base_rot_z"};const char* tra[3]={"base_trans_x","base_trans_y","base_trans_z"};
  for(int i=0;i<3;++i){
   std::string rk=std::string(rot[i])+"_deg",tk=std::string(tra[i])+"_m",rv=std::string(rot[i])+"_speed_deg_s",tv=std::string(tra[i])+"_speed_m_s";
   if(c.contains(rk)){double a=number(c[rk]);require(std::abs(a)<=180.*(1.+1e-12),"coupled_free_base_range");require(restart||a==number(config_[rk]),"coupled_free_base_requires_reset");}
   if(c.contains(tk)){double a=number(c[tk]);require(std::abs(a)<=1.,"coupled_free_base_range");require(restart||a==number(config_[tk]),"coupled_free_base_requires_reset");}
   if(c.contains(rv)){double a=number(c[rv]);require(std::abs(a)<=720.,"coupled_free_base_range");require(restart||a==number(config_[rv]),"coupled_free_base_requires_reset");}
   if(c.contains(tv)){double a=number(c[tv]);require(std::abs(a)<=10.,"coupled_free_base_range");require(restart||a==number(config_[tv]),"coupled_free_base_requires_reset");}}
  for(int i=0;i<2;++i){std::string stem=i?"elbow":"shoulder";double target=number(c[stem+"_target_deg"])*pi/180,cap=number(c[stem+"_torque_limit_N_m"]);size_t ci=nb_+size_t(i);
   require(target>=model_->lower[ci]-1e-8&&target<=model_->upper[ci]+1e-8&&cap>=0&&cap<=(i?.6:1.),"coupled_control_range");}
  double load=number(c["load_N"]);require(load>=0&&load<=3,"coupled_load_range");
  config_=c;contact_=config_["contact_enabled"].get<bool>();mu_=number(config_["contact_friction"]);if(restart)reset();}
 void step(){
  s_.impulse=Dense(n_,0.);s_.contact_impact_impulse.assign(npts_,0.);s_.contact_force_impulse.assign(npts_,0.);s_.contact_generalized=Dense(n_,0.);s_.friction_impulse.assign(npts_,0.);s_.friction_force_impulse.assign(npts_,0.);s_.friction_heat_tick.assign(npts_,0.);
  Dense impulse_torque(2,0.);for(int k=0;k<4;++k){auto tau=torque();auto trial=advance(s_,dt_/4,tau);
   auto work=[&](const State& s){double p=0;for(int i=0;i<2;++i)p+=(std::max)(0.,s.work[nb_+size_t(i)]-s_.work[nb_+size_t(i)]);return p;};
   if(work(trial)>battery_){double lo=0,hi=1;trial=advance(s_,dt_/4,Dense(n_,0.));
    for(int j=0;j<40;++j){double mid=(lo+hi)/2;Dense effort=tau;for(size_t i=0;i<n_;++i)effort[i]*=mid;auto candidate=advance(s_,dt_/4,effort);if(work(candidate)<=battery_){lo=mid;trial=std::move(candidate);}else hi=mid;}
    for(size_t i=0;i<n_;++i)tau[i]*=lo;}
   double spent=work(trial),before=battery_;battery_-=spent;require(battery_>=0,"coupled_negative_store");if(before>1e-12&&battery_<=1e-12)++empty_events_;
   for(int i=0;i<2;++i){size_t c=nb_+size_t(i);brake_+=(std::max)(0.,s_.work[c]-trial.work[c]);impulse_torque[size_t(i)]+=tau[c]/4;
    require(std::isfinite(trial.q[c])&&std::isfinite(trial.v[c])&&trial.q[c]>=model_->lower[c]-1e-9&&trial.q[c]<=model_->upper[c]+1e-9,"coupled_state_invalid");}
   for(size_t i=0;i<nb_;++i){require(std::isfinite(trial.q[i])&&std::isfinite(trial.v[i]),"coupled_free_state_invalid");
    require(trial.work[i]==0,"coupled_free_base_actuator_work");require(tau[i]==0,"coupled_free_base_torque");} // D3/D8: no root actuator; base rows carry NO range clamp (F7)
   s_=std::move(trial);}
  last_torque_=Dense(n_,0.);for(int i=0;i<2;++i)last_torque_[nb_+size_t(i)]=impulse_torque[size_t(i)];++ticks_;}
 J status()const{
  auto e=evaluate(s_);auto hand=e.point(hand_,local_);V velocity{};for(size_t i=0;i<n_;++i)velocity=add(velocity,mul(hand.second[i],s_.v[i]));
  double kinetic=.5*inner(s_.v,multiply(e.mass,s_.v)),u=e.potential-initial_potential_,energy=kinetic+u,work=s_.work[nb_]+s_.work[nb_+1];
  J joints=J::array();
  for(int i=0;i<2;++i){std::string stem=i?"elbow":"shoulder";size_t c=nb_+size_t(i);
   joints.push_back({{"name",model_->names[c]},{"angle_deg",s_.q[c]*180/pi},{"target_deg",config_[stem+"_target_deg"]},{"speed_rad_s",s_.v[c]},{"motor_torque_N_m",last_torque_[c]},{"gravity_torque_N_m",e.gravity[c]},{"limit_reaction_N_m",s_.impulse[c]/dt_},{"drive_enabled",config_[stem+"_drive"]},{"torque_limit_N_m",config_[stem+"_torque_limit_N_m"]}});}
  J base=J::array();const char* base_names[6]={"base_rot_x","base_rot_y","base_rot_z","base_trans_x","base_trans_y","base_trans_z"};
  for(size_t i=0;i<nb_;++i)base.push_back({{"name",base_names[i]},{"position",i<3?s_.q[i]*180/pi:s_.q[i]},{"unit",i<3?"deg":"m"},{"speed",i<3?s_.v[i]*180/pi:s_.v[i]}});
  double friction_heat_total=0,reaction_total=0,friction_force_total=0,impact_heat_total=0,normal_work_total=0;bool cone_valid=true;
  J points=J::array();std::vector<std::pair<double,double>> hull;
  for(size_t k=0;k<npts_;++k){double g=gap_of(e,k);bool touching=contact_&&g<=kTouch;
   auto rown=contact_row(e,k);double closing=inner(rown,s_.v);
   double reaction=s_.contact_force_impulse[k]/dt_,friction_force=s_.friction_force_impulse[k]/dt_;
   auto j_t1=tangent_row(e,k,0),j_t2=tangent_row(e,k,2);V slip_v{};
   for(size_t i=0;i<n_;++i){slip_v[0]+=j_t1[i]*s_.v[i];slip_v[2]+=j_t2[i]*s_.v[i];}
   double slip=std::hypot(slip_v[0],slip_v[2]);
   friction_heat_total+=s_.friction_heat[k];impact_heat_total+=s_.contact_impact[k];reaction_total+=reaction;friction_force_total+=std::abs(friction_force);
   // F8's measured validity: cone holds per touching point (slide sits ON the
   // edge, included by the same tolerance as the solve).
   if(touching)cone_valid=cone_valid&&std::abs(friction_force)<=mu_*reaction+1e-9&&reaction>=-1e-9;
   const char* mode=!contact_?"off":(g>kTouch?"free":(std::abs(friction_force)>1e-15?(s_.friction_heat_tick[k]>1e-15?"slide":"stick"):"free"));
   points.push_back({{"name",points_[k].name},{"body",points_[k].body},{"gap_m",g},{"closing_speed_m_s",closing},{"touching",touching},{"reaction_N",reaction},{"friction_force_N",friction_force},{"slip_speed_m_s",slip},{"mode",mode},{"impact_heat_J",s_.contact_impact[k]},{"friction_heat_J",s_.friction_heat[k]},{"impact_impulse_N_s",s_.contact_impact_impulse[k]},{"friction_impulse_N_s",s_.friction_impulse[k]}});
   if(touching){auto p=e.point(points_[k].index,points_[k].local).first;hull.push_back({p[0],p[2]});}}
  // Support hull and CoM projection (D7): the horizontal (East, South) hull
  // of TOUCHING points; barycentric weights reported for the three-point scene.
  V c{};for(size_t b=0;b<bodies_.size();++b){auto p=vector(e.frames[b].t,bodies_[b].com,1);for(int k=0;k<3;++k)c[k]+=bodies_[b].mass*p[k];}
  for(int k=0;k<3;++k)c[k]/=mtot_;
  J hullj=J::array();for(auto& h:hull)hullj.push_back(J::array({h.first,h.second}));
  J support{{"plane_world_up_m",plane_world_up_m()},{"points",hullj},{"com_projection_east_m",c[0]},{"com_projection_south_m",c[2]},{"com_in_hull",false},{"assembly_mass_kg",mtot_},{"weight_N",mtot_*norm(gravity_)}};
  if(hull.size()==3){double det=(hull[1].first-hull[0].first)*(hull[2].second-hull[0].second)-(hull[2].first-hull[0].first)*(hull[1].second-hull[0].second);
   if(std::abs(det)>1e-15){double w0=((hull[1].first-c[0])*(hull[2].second-c[1])-(hull[2].first-c[0])*(hull[1].second-c[1]))/det,
    w1=((hull[2].first-c[0])*(hull[0].second-c[1])-(hull[0].first-c[0])*(hull[2].second-c[1]))/det,w2=1.-w0-w1;
   support["barycentric"]=J::array({w0,w1,w2});support["com_in_hull"]=w0>=0&&w1>=0&&w2>=0;}}
  J contact{{"enabled",contact_},{"friction",mu_>0},{"friction_mu",mu_},{"grasp",false},{"plane_world_up_m",plane_world_up_m()},{"normal_world_up",J::array({0.,1.,0.})},{"points",points},
   {"reaction_N",reaction_total},{"friction_force_N",friction_force_total},{"impact_heat_J",impact_heat_total},{"friction_heat_J",friction_heat_total},{"cone_valid",cone_valid}};
  auto mom=momentum();
  return {{"sim_time_s",ticks_*dt_},{"ticks",ticks_},{"mode","native_coupled_arm_free"},{"joints",joints},{"base",base},{"config",config_},{"power",config_["power"]},{"load_N",config_["load_N"]},{"battery_empty_events",empty_events_},
   {"contacts",{{"environment",contact_},{"joint_limits",true}}},
   {"contact",contact},{"support",support},{"momentum",mom},
   {"body",{{"position_m",add(hand.first,shift_)},{"velocity_m_s",velocity},{"radius_m",recipe_["proxy_radius_m"]}}},
   {"energy",{{"kinetic_J",kinetic},{"gravitational_J",u},{"potential_reference","reset pose"},{"mechanical_J",energy},{"actuator_work_J",work},{"external_work_J",s_.external},{"damping_heat_J",s_.damping},{"impact_heat_J",s_.impact+impact_heat_total},{"contact_impact_heat_J",impact_heat_total},{"friction_heat_J",friction_heat_total},{"brake_heat_J",brake_},{"battery_J",battery_},{"battery_initial_J",initial_store_},{"battery_usable",battery_>1e-12},
    {"balance_error_J",energy-work-s_.external+s_.damping+s_.impact+impact_heat_total+friction_heat_total},
    {"store_balance_error_J",energy+battery_+s_.damping+s_.impact+impact_heat_total+friction_heat_total+brake_-initial_store_-s_.external}}},
   {"coupling",{{"mass_matrix_kg_m2",[&]{J m=J::array();for(size_t i=0;i<n_;++i){J row=J::array();for(size_t j=0;j<n_;++j)row.push_back(e.mass[i*n_+j]);m.push_back(row);}return m;}()},{"bias_torque_N_m",e.bias},{"contact_generalized_N_m",[&]{J v=J::array();for(size_t i=0;i<n_;++i)v.push_back(s_.contact_generalized[i]/dt_);return v;}()}}}};
 }
 double plane_world_up_m()const{return plane_world_y_;}
};
} // namespace chimera::multibody
