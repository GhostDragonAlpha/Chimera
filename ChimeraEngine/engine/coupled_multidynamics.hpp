#pragma once
#include "coupled_articulation.hpp"
#include <algorithm>
#include <cstdint>
#include <memory>
#include <tuple>
#if defined(CHIMERA_CONTACT_TRACE)
#include <cstdio>
#endif
namespace chimera::multibody {
// Generalized N-coordinate coupled dynamics (the seven-coordinate lift,
// docs/packets/seven_coordinate_lift_v1.md). The qualified 2-coordinate
// CoupledDynamics class keeps its exact bytes (S7 frozen control): this
// class serves ONLY a chimera.coupled_scene7.v1 recipe and refuses the
// qualified schema, so the serving layer's schema check is the dispatch and
// the qualified path never reroutes through here.
//
// S1 cascade law (event level): each violated coordinate bound is localized
// by its own 42-step bisection; the EARLIEST crossing time wins and ties
// within 1e-12*h break to the LOWEST recipe-coordinate index; the contact
// localization enters the same selection as the LAST candidate index (a tie
// between a joint stop and the contact plane goes to the joint stop);
// exactly one stop impact is applied per event and advance recurses
// (depth < 8, "coupled_impact_event_budget"). The qualified n=2 loop keeps
// its own t<=hit (last-index/contact-wins) tie law byte-for-byte; both are
// deterministic and neither crosses the other.
class CoupledMultiDynamics {
 struct State {Dense q,v,work,impulse,contact_generalized;double external=0,damping=0,impact=0;double contact_impact=0,contact_impact_impulse=0,contact_force_impulse=0;double friction_heat=0,friction_heat_tick=0,friction_impulse=0,friction_force_impulse=0;};
 struct Rate {Dense q,v,reaction,contact_force,friction_force;double damping;double contact_lambda=0;double friction_lambda=0,friction_heat=0,slip=0;int mode=0;};
 std::shared_ptr<const Model> model_;J recipe_,config_;size_t hand_,n_;V local_,shift_,gravity_;
 double dt_,initial_store_,initial_potential_=0;Dense kp_,kd_,damping_,last_torque_,battery_,brake_;
 std::vector<uint64_t> empty_events_;
 bool contact_=false;double plane_world_y_=0,plane_model_y_=0,radius_=0,mu_=0;
 static constexpr double kTouch=1e-5,kSlip=1e-9;
 uint64_t ticks_=0;
 State s_;
 Evaluation evaluate(const State& s)const{return model_->evaluate(s.q,s.v,gravity_);}
 double mechanical(const State& s)const{auto e=evaluate(s);return .5*inner(s.v,multiply(e.mass,s.v))+e.potential;}
 // Per-row armed joint-stop normals: +e_i at the lower bound, -e_i at the
 // upper (the qualified normals() law, per row).
 std::vector<char> normals(const State& s)const{std::vector<char> row(n_,0);for(size_t i=0;i<n_;++i){if(std::abs(s.q[i]-model_->lower[i])<1e-10)row[i]=1;else if(std::abs(s.q[i]-model_->upper[i])<1e-10)row[i]=-1;}return row;}
 // The rate-level armed set: the normals law plus the qualified velocity
 // gate, evaluated ONCE per substep (row latch). A row armed at the substep
 // start stays armed through every RK4 stage of that substep -- the
 // stage-wise re-evaluation would disarm a parked wall after the first
 // stage and let it re-cross every substep.
 std::vector<char> armed_rows(const State& s)const{
  std::vector<char> row=normals(s);
  for(size_t i=0;i<n_;++i)if(row[i]&&std::abs(s.v[i])>1e-9)row[i]=0;
  return row;
 }
 static Dense unit_row(size_t n,size_t i,int sign){Dense r(n,0);r[i]=sign;return r;}
 double gap_of(const Evaluation& e)const{return e.point(hand_,local_).first[1]+radius_-plane_model_y_;}
 double gap(const State& s)const{return gap_of(evaluate(s));}
 Dense contact_row(const Evaluation& e)const{auto j=e.point(hand_,local_).second;Dense row(n_);for(size_t i=0;i<n_;++i)row[i]=j[i][1];return row;}
 double contact_bias(const Evaluation& e)const{return vector(e.frames[hand_].ddt,local_,1)[1];}
 // Coulomb friction row: the hand point Jacobian projected onto the
 // in-plane unit direction of the current hand velocity (the free
 // tangential acceleration direction when at rest). Returns {row, slip
 // speed, tangent world direction}.
 std::tuple<Dense,double,V> friction_row(const Evaluation& e,const Dense& v,const Dense& free_accel)const{
  auto j=e.point(hand_,local_).second;
  for(int pass=0;pass<2;++pass){V hand{};for(size_t i=0;i<n_;++i){const Dense& source=pass?free_accel:v;hand=add(hand,mul(j[i],source[i]));}
   double planar=std::hypot(hand[0],hand[2]);
   if(planar>(pass?1e-9:kSlip)){V t{hand[0]/planar,0,hand[2]/planar};Dense row(n_);for(size_t i=0;i<n_;++i)row[i]=dot(t,j[i]);return {row,pass?0.:planar,t};}}
  return {Dense(n_,0),0.,V{}};
 }
 static double slip_signed(const Dense& v,const Dense& row_t){double s=0;for(size_t i=0;i<v.size();++i)s+=row_t[i]*v[i];return s;}
 // Small SPD solve (Cholesky, refusing numerically dependent systems) for
 // the active-set KKT Gram systems. A false return is the lifted form of
 // the qualified det<=1e-18 guard: the caller skips that subset.
 static bool cholesky_solve(std::vector<double> a,size_t m,const std::vector<double>& b,std::vector<double>& x){
  for(size_t i=0;i<m;++i)for(size_t j=0;j<=i;++j){double t=a[i*m+j];for(size_t k=0;k<j;++k)t-=a[i*m+k]*a[j*m+k];if(i==j){if(!(t>1e-18))return false;a[i*m+i]=std::sqrt(t);}else a[i*m+j]=t/a[j*m+j];}
  x.assign(m,0);for(size_t i=0;i<m;++i){double t=b[i];for(size_t k=0;k<i;++k)t-=a[i*m+k]*x[k];x[i]=t/a[i*m+i];}
  for(size_t ii=m;ii-->0;){double t=x[ii];for(size_t k=ii+1;k<m;++k)t-=a[k*m+ii]*x[k];x[ii]=t/a[ii*m+ii];}
  return true;
 }
public:
 // F4 white-box seam: the deterministic event-selection law as a pure
 // function. candidates[k] is the localized crossing time of coordinate k
 // (or the sentinel 2h when that bound was not violated; the sentinel is
 // never selected). Earliest time wins; ties within 1e-12*h break to the
 // LOWEST index. Returns candidates.size() when nothing violated.
 static size_t select_stop_event(const std::vector<double>& candidates,double h,double& hit){
  require(!candidates.empty()&&h>0,"coupled_cascade_input");
  double best=h;size_t which=candidates.size();
  for(size_t k=0;k<candidates.size();++k){
   if(candidates[k]>=2*h)continue;
   if(which==candidates.size()){best=candidates[k];which=k;}
   else if(candidates[k]<best-1e-12*h){best=candidates[k];which=k;}
   else if(candidates[k]<=best+1e-12*h&&k<which){best=candidates[k];which=k;}
  }
  hit=which==candidates.size()?h:best;return which;
 }
private:
 // Mass-metric projection onto the admissible cone defined by named
 // constraint rows (joint stops and/or the contact plane): row_k.x >=
 // floor_k with NONNEGATIVE multipliers (a row can never attract). The
 // qualified two-row subset enumeration lifted row-count-only: subsets are
 // enumerated in deterministic mask order, each active set is solved in the
 // mass metric, and a candidate is accepted only when every multiplier is
 // nonnegative AND every row (active or not) is satisfied. Enumeration caps
 // at n active rows (an n-DOF system admits at most n independent
 // multipliers) and n+1 rows total -- the "coupled_contact_row_budget".
 static Dense reaction_rows(const Dense& initial,const Dense& inverse,const std::vector<Dense>& rows,const Dense& floors,std::vector<double>* multipliers=nullptr){
  size_t n=initial.size();
  require(rows.size()==floors.size()&&rows.size()<=n+1,"coupled_contact_row_budget");
  for(size_t mask=0;mask<(size_t(1)<<rows.size());++mask){
   std::vector<size_t> act;for(size_t k=0;k<rows.size();++k)if(mask>>k&1)act.push_back(k);
   if(act.size()>n)continue; // mask 0 (no correction) is a legal candidate:
   // armed-but-satisfied rows must yield p=0, exactly as the qualified
   // reaction() does with its mask-0 pass.
   std::vector<double> gram(act.size()*act.size(),0),rhs(act.size());
   for(size_t a=0;a<act.size();++a){for(size_t b=0;b<act.size();++b)gram[a*act.size()+b]=inner(rows[act[a]],multiply(inverse,rows[act[b]]));rhs[a]=floors[act[a]]-inner(rows[act[a]],initial);}
   std::vector<double> lambda;
   if(!cholesky_solve(gram,act.size(),rhs,lambda))continue;
   bool valid=true;Dense p(n,0);
   for(size_t k=0;k<act.size();++k){if(lambda[k]<-1e-10)valid=false;double l=(std::max)(0.,lambda[k]);for(size_t i=0;i<n;++i)p[i]+=l*rows[act[k]][i];}
   if(!valid)continue;
   auto change=multiply(inverse,p);Dense projected(n);
   for(size_t i=0;i<n;++i)projected[i]=initial[i]+change[i];
   for(size_t k=0;k<rows.size();++k)if(inner(rows[k],projected)<floors[k]-1e-9){valid=false;break;}
   if(valid){if(multipliers){multipliers->assign(rows.size(),0.);for(size_t k=0;k<act.size();++k)(*multipliers)[act[k]]=(std::max)(0.,lambda[k]);}return p;}
  }
#if defined(CHIMERA_PROJECTION_TRACE)
  {std::fprintf(stderr,"PROJECTION refusing: rows=%zu init=[",rows.size());
   for(size_t i=0;i<n;++i)std::fprintf(stderr,"%s%.6g",i?", ":"",initial[i]);
   std::fprintf(stderr,"] floors=[");
   for(size_t k=0;k<rows.size();++k)std::fprintf(stderr,"%s%.6g",k?", ":"",floors[k]);
   std::fprintf(stderr,"] rows:\n");
   for(size_t k=0;k<rows.size();++k){std::fprintf(stderr,"  r%zu=[",k);
    for(size_t i=0;i<n;++i)std::fprintf(stderr,"%s%.3g",i?", ":"",rows[k][i]);
    std::fprintf(stderr,"]\n");}
   std::fprintf(stderr,"inverse:\n");
   for(size_t i=0;i<n;++i){std::fprintf(stderr,"  [");
    for(size_t j=0;j<n;++j)std::fprintf(stderr,"%s%.4g",j?", ":"",inverse[i*n+j]);
    std::fprintf(stderr,"]\n");}}
#endif
  throw Refusal("coupled_contact_cone_unsolved");
 }
 // Coulomb friction at one evaluation point (the qualified single-tangent
 // solve, row-count-parametric exactly as written): joint (lambda_n, f_t)
 // solve so the hand's normal and tangential components reach their floors,
 // f_t signed. Stick when |f_t| <= mu*lambda_n; slide caps f_t at
 // -mu*lambda_n*sign(slip) and re-solves lambda_n with the exact M^-1
 // cross-coupling. Friction never acts without a positive normal reaction.
 static void friction_solve(const Dense& initial,const Dense& inverse,const Dense& row_n,const Dense& row_t,double floor_n,double floor_t,double mu,double slip_sign,Dense& force,double& lambda_n,double& lambda_t,int& mode){
  size_t n=initial.size();
  auto in=multiply(inverse,row_n),it=multiply(inverse,row_t);
  double A=inner(row_n,in),B=inner(row_n,it),C=inner(row_t,it),rn=-(inner(row_n,initial)-floor_n),rt=-(inner(row_t,initial)-floor_t),det=A*C-B*B;
  if(det>1e-18){double nn=(rn*C-rt*B)/det,t=(rt*A-rn*B)/det;
   // Stick acceptance carries the DERIVED dissipation condition (lift-law
   // fix exposed at n>2): friction may only OPPOSE the current slip. The
   // qualified n=2 branch lacked it; configurations reachable at n>=5 can
   // make the bare stick solve assign t along the slip, creating energy.
   // Violations fall through to the slide branch, which is dissipative by
   // construction (t=-s*mu*nn with s=sign(slip)).
   if(nn>=0&&std::abs(t)<=mu*nn+1e-12&&(slip_sign==0.||t*slip_sign<=0.)){force=Dense(n);for(size_t i=0;i<n;++i)force[i]=row_n[i]*nn+row_t[i]*t;lambda_n=nn;lambda_t=t;mode=1;return;}}
  // Exact-rest fallback (qualified review F1): rt>0 means the free
  // tangential motion would run BELOW floor_t, i.e. impending slip along
  // -t; friction opposes impending slip, and since the cap is
  // f_t=-s*mu*lambda_n, that demands s=-1 when rt>=0.
  double s=slip_sign!=0.?slip_sign:(rt>=0.?-1.:1.),den=A-s*mu*B;
  if(den<=1e-12)throw Refusal("coupled_friction_slide_singular");
  double nn=rn/den,t=-s*mu*nn;
  if(nn>=0){force=Dense(n);for(size_t i=0;i<n;++i)force[i]=row_n[i]*nn+row_t[i]*t;lambda_n=nn;lambda_t=t;mode=2;return;}
  force=Dense(n,0);lambda_n=0;lambda_t=0;mode=0;
 }
 Rate rate(const State& s,const std::vector<char>& armed,const Dense& tau,bool live,bool plane=false)const{
  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);V load{0,-number(config_["load_N"]),0};auto external=e.force(hand_,local_,load);Dense rhs(n_);double heat=0;
  for(size_t i=0;i<n_;++i){rhs[i]=tau[i]+e.gravity[i]-e.bias[i]+external[i]-damping_[i]*s.v[i];heat+=damping_[i]*s.v[i]*s.v[i];}
  auto free=multiply(inv,rhs);
  bool friction=contact_&&live&&mu_>0;
  if(!contact_||!live){
   std::vector<Dense> rows;Dense floors;
   for(size_t i=0;i<n_;++i){if(!armed[i])continue;rows.push_back(unit_row(n_,i,armed[i]));floors.push_back(0);}
   Rate out{s.v,free,Dense(n_,0),Dense(n_,0),Dense(n_,0),heat};
   if(!rows.empty()){auto p=reaction_rows(free,inv,rows,floors);auto correction=multiply(inv,p);for(size_t i=0;i<n_;++i)free[i]+=correction[i];out.v=free;out.reaction=p;}
   return out;
  }
  std::vector<Dense> rows;Dense floors;
  bool stop=false;
  for(size_t i=0;i<n_;++i)if(armed[i]){rows.push_back(unit_row(n_,i,armed[i]));floors.push_back(0);stop=true;}
  auto row=contact_row(e);
  double speed_norm=0;for(size_t i=0;i<n_;++i)speed_norm+=std::abs(s.v[i]);
  double gate=1e-6+1e-3*speed_norm;
  bool touching=plane||(gap_of(e)<=kTouch&&inner(row,s.v)<=gate);
  if(touching){rows.push_back(row);floors.push_back(-contact_bias(e));}
  Rate out{s.v,free,Dense(n_,0),Dense(n_,0),Dense(n_,0),heat};
  // Friction participates only in plain contact stages: no simultaneous
  // joint stop rows, a positive normal reaction and a defined direction.
  if(touching&&!stop&&friction){
   Dense zero(n_,0);auto [row_t,slip,tangent]=friction_row(e,s.v,zero);
   bool defined=false;for(size_t i=0;i<n_;++i)if(row_t[i])defined=true;
   if(defined){double slip_v=slip_signed(s.v,row_t);
    V bias=vector(e.frames[hand_].ddt,local_,1);
    try{Dense force;double lambda_n,lambda_t;int mode;
     friction_solve(free,inv,row,row_t,floors.back(),-dot(tangent,V{bias[0],0,bias[2]}),mu_,slip_v>0.?1.:(slip_v<0.?-1.:0.),force,lambda_n,lambda_t,mode);
     if(mode){auto correction=multiply(inv,force);for(size_t i=0;i<n_;++i)free[i]+=correction[i];
      out.reaction=force;out.contact_lambda=lambda_n;for(size_t i=0;i<n_;++i)out.contact_force[i]=lambda_n*row[i];
      out.friction_lambda=lambda_t;for(size_t i=0;i<n_;++i)out.friction_force[i]=lambda_t*row_t[i];
      out.slip=std::abs(slip_v);out.mode=mode;out.friction_heat=lambda_t!=0.?-(lambda_t*slip_v):0.;}}
    catch(const Refusal&){/* singular slide geometry this stage: keep the frictionless solve */}}}
  if(out.mode==0){
   std::vector<double> multipliers;auto p=reaction_rows(free,inv,rows,floors,&multipliers);auto correction=multiply(inv,p);for(size_t i=0;i<n_;++i)free[i]+=correction[i];
   out.reaction=p;out.v=free;
   if(touching){out.contact_lambda=multipliers.back();for(size_t i=0;i<n_;++i)out.contact_force[i]=out.contact_lambda*row[i];}}
  out.v=free;
  return out;
 }
 State free_step(const State& start,double h,const Dense& tau,bool live=true)const{
  auto shifted=[&](const Rate& d,double t){State x=start;for(size_t i=0;i<n_;++i){x.q[i]+=d.q[i]*t;x.v[i]+=d.v[i]*t;}return x;};
  bool plane=false;
  if(contact_&&live&&mu_>0){auto e0=evaluate(start);double speed_norm=0;for(size_t i=0;i<n_;++i)speed_norm+=std::abs(start.v[i]);
   plane=gap_of(e0)<=kTouch&&inner(contact_row(e0),start.v)<=1e-6+1e-3*speed_norm;}
  // The armed-row set is LATCHED at the substep start (see armed_rows).
  auto armed=armed_rows(start);
  auto a=rate(start,armed,tau,live,plane),b=rate(shifted(a,h/2),armed,tau,live,plane),c=rate(shifted(b,h/2),armed,tau,live,plane),d=rate(shifted(c,h),armed,tau,live,plane);State end=start;
  for(size_t i=0;i<n_;++i){end.q[i]+=h*(a.q[i]+2*b.q[i]+2*c.q[i]+d.q[i])/6;end.v[i]+=h*(a.v[i]+2*b.v[i]+2*c.v[i]+d.v[i])/6;end.work[i]+=tau[i]*(end.q[i]-start.q[i]);end.impulse[i]+=h*(a.reaction[i]+2*b.reaction[i]+2*c.reaction[i]+d.reaction[i])/6;end.contact_generalized[i]+=h*((a.contact_force[i]+a.friction_force[i])+2*(b.contact_force[i]+b.friction_force[i])+2*(c.contact_force[i]+c.friction_force[i])+(d.contact_force[i]+d.friction_force[i]))/6;}
  end.damping+=h*(a.damping+2*b.damping+2*c.damping+d.damping)/6;end.contact_force_impulse+=h*(a.contact_lambda+2*b.contact_lambda+2*c.contact_lambda+d.contact_lambda)/6;
  end.friction_heat+=h*(a.friction_heat+2*b.friction_heat+2*c.friction_heat+d.friction_heat)/6;
  end.friction_heat_tick+=h*(a.friction_heat+2*b.friction_heat+2*c.friction_heat+d.friction_heat)/6;
  end.friction_force_impulse+=h*(a.friction_lambda+2*b.friction_lambda+2*c.friction_lambda+d.friction_lambda)/6;
  double dy=evaluate(end).point(hand_,local_).first[1]-evaluate(start).point(hand_,local_).first[1];end.external-=number(config_["load_N"])*dy;
  return end;
 }
 double impact(State& s)const{
  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);std::vector<Dense> rows;Dense floors;auto armed=normals(s);
  for(size_t i=0;i<n_;++i)if(armed[i]){rows.push_back(unit_row(n_,i,armed[i]));floors.push_back(0);}
  // The plane exists ONLY when contact is enabled (the qualified law): a
  // disabled-contact scene passing near the plane feels nothing.
  bool touching=contact_&&gap_of(e)<=kTouch;if(touching){rows.push_back(contact_row(e));floors.push_back(0);}
  if(rows.empty())return 0.;
  // Coulomb landing impulse: one JOINT (lambda_n, lambda_t) solve so the
  // closing velocity lands exactly at zero in stick AND capped-slide modes,
  // only when the contact row is the single constraint (as qualified).
  if(touching&&mu_>0&&rows.size()==1){
   auto [row_t,slip,tangent]=friction_row(e,s.v,s.v);
   bool defined=false;for(size_t i=0;i<n_;++i)if(row_t[i])defined=true;
   if(defined){double slip_v=slip_signed(s.v,row_t);
    try{Dense force;double lambda_n,lambda_t;int mode;
     friction_solve(s.v,inv,rows[0],row_t,0,0,mu_,slip_v>0.?1.:(slip_v<0.?-1.:0.),force,lambda_n,lambda_t,mode);
     if(mode){auto change=multiply(inv,force);double before=.5*inner(s.v,multiply(e.mass,s.v));
      Dense mean(n_);for(size_t i=0;i<n_;++i)mean[i]=s.v[i]+change[i]/2;
      for(size_t i=0;i<n_;++i){s.v[i]+=change[i];s.impulse[i]+=force[i];}
      double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"coupled_impact_created_energy");
      // Per-row dissipation split: sum_k lambda_k (v_mean . row_k) equals the loss exactly.
      double share_n=lambda_n*inner(rows[0],mean),share_t=lambda_t*inner(row_t,mean);
      require(share_n<=1e-11&&share_t<=1e-11,"coupled_contact_impact_gain");
      s.impact+=(std::max)(0.,loss+share_n+share_t);s.contact_impact+=(std::max)(0.,-share_n);s.contact_impact_impulse+=lambda_n;
      s.friction_heat+=(std::max)(0.,-share_t);s.friction_impulse+=std::abs(lambda_t);
      return lambda_n;}}
    catch(const Refusal&){/* singular geometry: fall through to the frictionless impulse */}}}
  std::vector<double> multipliers;auto p=reaction_rows(s.v,inv,rows,floors,&multipliers);auto change=multiply(inv,p);double before=.5*inner(s.v,multiply(e.mass,s.v));
  Dense mean(n_);for(size_t i=0;i<n_;++i)mean[i]=s.v[i]+change[i]/2;
  for(size_t i=0;i<n_;++i){s.v[i]+=change[i];s.impulse[i]+=p[i];}
  double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"coupled_impact_created_energy");
  if(touching){double lambda=multipliers.back();double share=lambda*inner(contact_row(e),mean);
   // Dissipation split (multi-row correction): the TOTAL dissipation is
   // `loss` (enforced above). The contact's own share can be POSITIVE in a
   // stops+contact co-impact at n>2 through mass-metric coupling -- that is
   // energy transferred by the other rows' impulses, not created. The
   // contact heat account takes only the contact's dissipation; the
   // remainder (including any positive share) stays in the general impact
   // heat. Conservation holds in both branches.
   double contact_part=(std::max)(0.,-share);
   double joint_part=share<=0.?(std::max)(0.,loss+share):(std::max)(0.,loss);
   s.impact+=joint_part;s.contact_impact+=contact_part;s.contact_impact_impulse+=lambda;return lambda;}
  s.impact+=(std::max)(0.,loss);return 0.;
 }
 State advance(State start,double h,const Dense& tau,int depth=0,int clamps=0)const{
  if(h<1e-12)return start;
  // Event-depth budget: the qualified 8 was sized for two stops + contact.
  // At n coordinates a single substep can legitimately contain O(n) events,
  // so the cap scales with n (derived revision of S1's constant; still
  // bounded, still loud).
  require(depth<4*n_+16,"coupled_impact_event_budget");double caught=impact(start);
  // A friction catch at substep entry leaves a violent post-impulse
  // transient; integrating the catching substep in halves quarters its
  // O(h^2) defect (qualified law, carried).
  if(mu_>0&&caught>1e-9&&depth<5)return advance(advance(start,h/2,tau,depth+3,0),h/2,tau,depth+3,0);
  // Contact rows are live only in a substep that STARTS in contact.
  bool live=!contact_||gap(start)<=kTouch;
  auto end=free_step(start,h,tau,live);
  // Event cascade (S1): localize EVERY violated bound by its own 42-step
  // bisection, plus the contact crossing as the last candidate, then apply
  // the deterministic selection law once. Violations shallower than 1e-12
  // (fp noise of an armed, projected wall) are not events -- they sit an
  // order of magnitude inside the 1e-9 state tolerance and would otherwise
  // livelock a parked wall against its own drive.
  std::vector<double> candidates(n_+1,2*h);std::vector<double> walls(n_,0);
  for(size_t i=0;i<n_;++i){bool low=end.q[i]<model_->lower[i];if(!low&&end.q[i]<=model_->upper[i])continue;
   double depth_v=low?model_->lower[i]-end.q[i]:end.q[i]-model_->upper[i];
   if(depth_v<=1e-12)continue;
   double bound=low?model_->lower[i]:model_->upper[i],left=0,right=h;
   for(int j=0;j<42;++j){double mid=(left+right)/2;double q=free_step(start,mid,tau,live).q[i];if(low?q<=bound:q>=bound)right=mid;else left=mid;}
   candidates[i]=(left+right)/2;walls[i]=bound;}
  if(contact_&&!live&&gap(end)<0){double left=0,right=h;
   // The pre-touching piece is integrated without contact rows: no contact
   // force exists before the first touching state.
   for(int j=0;j<42;++j){double mid=(left+right)/2;if(gap(free_step(start,mid,tau,false))<=0)right=mid;else left=mid;}
   candidates[n_]=(left+right)/2;}
  double hit;size_t which=select_stop_event(candidates,h,hit);
  if(which>=n_+1)return end;
  if(hit<=1e-12){
   // An fp-level crossing at the substep boundary (a wall the cascade just
   // clamped, re-crossed by rounding inside the first interval): pin the
   // violated coordinate, absorb the impact, and integrate the remainder.
   // The clamp carries its OWN consecutive bound (64) and does NOT consume
   // event depth: real, distinct landings need the depth budget; only a
   // genuine same-wall livelock can exhaust the clamp counter, loudly.
   require(clamps<64,"coupled_impact_event_budget");
   State pinned=start;
   if(which<n_)pinned.q[which]=walls[which];
   impact(pinned);
   return advance(pinned,h,tau,depth,clamps+1);
  }
  if(which==n_){auto crossing=free_step(start,hit,tau,false);require(std::abs(gap(crossing))<1e-9,"coupled_contact_localization");impact(crossing);
   // The friction catch transient magnifies the event-split boundary defect;
   // halving the first post-landing intervals quarters it (qualified law).
   if(mu_>0)return advance(advance(crossing,(h-hit)/2,tau,depth+1,0),(h-hit)/2,tau,depth+2,0);
   return advance(crossing,h-hit,tau,depth+1,0);}
  auto wall_state=free_step(start,hit,tau,live);require(std::abs(wall_state.q[which]-walls[which])<1e-9,"coupled_impact_localization");wall_state.q[which]=walls[which];impact(wall_state);return advance(wall_state,h-hit,tau,depth+1,0);
 }
 Dense torque()const{
  Dense tau(n_,0);
  for(size_t d=0;d<n_;++d){const std::string& stem=model_->names[d];
   if(config_["power"].get<bool>()&&config_[stem+"_drive"].get<bool>()&&battery_[d]>1e-12){double target=number(config_[stem+"_target_deg"])*pi/180,cap=number(config_[stem+"_torque_limit_N_m"]);tau[d]=(std::max)(-cap,(std::min)(cap,kp_[d]*(target-s_.q[d])-kd_[d]*s_.v[d]));}}
  return tau;
 }
 static J array_of(const Dense& v){J a=J::array();for(double x:v)a.push_back(x);return a;}
 static J array_of(const std::vector<uint64_t>& v){J a=J::array();for(uint64_t x:v)a.push_back(x);return a;}
public:
 CoupledMultiDynamics(const J& data,double gravity,V shift,double dt=1/300.):recipe_(data.at("recipe")),shift_(shift),gravity_{0,-gravity,0},dt_(dt){
  require(recipe_.at("schema")=="chimera.coupled_scene7.v1","coupled_dynamics7_schema");
  // The dispatch itself (S7): a qualified recipe must NEVER reach this
  // class; the serving layer routes it to the byte-untouched qualified one.
  n_=recipe_.at("coordinates").size();
  require(n_>=2&&n_<=7,"coupled_coordinate_capacity");
  require(dt>0&&dt<=1/300.,"coupled_timestep");require(recipe_.at("substeps")==4,"coupled_substeps");
  model_=std::make_shared<Model>(data.at("model"),recipe_.at("coordinates").get<std::vector<std::string>>());
  require(model_->names.size()==n_,"coupled_coordinate_capacity");
  hand_=model_->body(recipe_.at("hand_body"));local_=recipe_.at("hand_point_m").get<V>();config_=recipe_.at("defaults");
  initial_store_=number(recipe_.at("battery_initial_J"));require(initial_store_>=0,"coupled_store_initial");
  plane_world_y_=number(recipe_.at("contact_plane_height_m"));require(std::isfinite(plane_world_y_),"coupled_contact_plane_invalid");radius_=number(recipe_.at("proxy_radius_m"));require(radius_>0,"coupled_contact_radius_invalid");plane_model_y_=plane_world_y_-shift[1];
  require(config_.contains("contact_enabled")&&config_["contact_enabled"].is_boolean(),"coupled_contact_flag_invalid");contact_=config_["contact_enabled"].get<bool>();
  require(config_.contains("contact_friction")&&config_["contact_friction"].is_number()&&number(config_["contact_friction"])>=0&&number(config_["contact_friction"])<=1,"coupled_friction_flag_invalid");mu_=number(config_["contact_friction"]);
  {State probe;probe.q=model_->defaults;probe.v=Dense(n_,0);probe.work=Dense(n_,0);probe.impulse=Dense(n_,0);probe.contact_generalized=Dense(n_,0);require(gap(probe)>1e-6,"coupled_contact_initial_penetration");}
  auto e=model_->evaluate(model_->defaults,Dense(n_,0),gravity_);
  double freq=2*pi*number(recipe_["servo_frequency_Hz"]),zeta=number(recipe_["servo_damping_ratio"]),decay=number(recipe_["passive_decay_rate_s"]);
  require(freq>=0&&zeta>=0&&decay>=0,"coupled_drive_parameters");
  // Servo gains extend by the SAME formula (S2 derivation): the qualified
  // mass-normalized PD at the diagonal; the diagonal at any n is the same
  // physical quantity per coordinate.
  for(size_t d=0;d<n_;++d){double m=e.mass[n_*d+d];kp_.push_back(m*freq*freq);kd_.push_back(2*zeta*m*freq);damping_.push_back(m*decay);}
  battery_.assign(n_,initial_store_);brake_.assign(n_,0);empty_events_.assign(n_,0);
  reset();
 }
 double timestep()const{return dt_;}const Dense& angles()const{return s_.q;}const Dense& speeds()const{return s_.v;}const Model& model()const{return *model_;}
 const Dense& batteries()const{return battery_;}
 void reset(){ticks_=0;s_=State{};s_.q=model_->defaults;s_.v=Dense(n_,0);s_.work=Dense(n_,0);s_.impulse=Dense(n_,0);s_.contact_generalized=Dense(n_,0);last_torque_=Dense(n_,0);battery_.assign(n_,initial_store_);brake_.assign(n_,0);empty_events_.assign(n_,0);initial_potential_=evaluate(s_).potential;}
 void configure(const J& input){
  require(input.is_object()&&!input.empty(),"coupled_control_object");auto c=config_;bool restart=false;
  for(auto it=input.begin();it!=input.end();++it){if(it.key()=="reset"){require(it.value().is_boolean()&&it.value().get<bool>(),"coupled_reset_true");restart=true;}else{require(c.contains(it.key()),"unknown_coupled_control");c[it.key()]=it.value();}}
  require(c["power"].is_boolean(),"coupled_boolean_control");
  for(size_t d=0;d<n_;++d)require(c[model_->names[d]+"_drive"].is_boolean(),"coupled_boolean_control");
  if(c.contains("contact_enabled")){require(c["contact_enabled"].is_boolean(),"coupled_boolean_control");if(c["contact_enabled"].get<bool>()!=config_["contact_enabled"].get<bool>())require(restart,"coupled_contact_toggle_requires_reset");}
  if(c.contains("contact_friction")){double m=number(c["contact_friction"]);require(c["contact_friction"].is_number()&&m>=0&&m<=1,"coupled_friction_range");}
  for(size_t d=0;d<n_;++d){const std::string& stem=model_->names[d];double target=number(c[stem+"_target_deg"])*pi/180,cap=number(c[stem+"_torque_limit_N_m"]);
   require(target>=model_->lower[d]-1e-8&&target<=model_->upper[d]+1e-8&&cap>=0&&cap<=1.,"coupled_control_range");}
  double load=number(c["load_N"]);require(load>=0&&load<=3,"coupled_load_range");config_=c;contact_=config_["contact_enabled"].get<bool>();mu_=number(config_["contact_friction"]);if(restart)reset();
 }
 void step(){
  s_.impulse=Dense(n_,0);s_.contact_force_impulse=0;s_.contact_generalized=Dense(n_,0);s_.friction_impulse=0;s_.friction_force_impulse=0;s_.friction_heat_tick=0;
  Dense impulse_torque(n_,0);
  for(int k=0;k<4;++k){
   auto tau=torque();
   Dense scales(n_,1.); // per-substep: each bisection starts from the full drive
   auto effort=[&](){Dense t(n_,0);for(size_t d=0;d<n_;++d)t[d]=tau[d]*scales[d];return t;};
   auto work_of=[&](const State& s){Dense w(n_,0);for(size_t d=0;d<n_;++d)w[d]=(std::max)(0.,s.work[d]-s_.work[d]);return w;};
   auto trial=advance(s_,dt_/4,effort());
   // Per-drive store accounting (S2): each enabled+powered drive scales ITS
   // OWN tau_d (40-step bisection) so ITS positive work fits ITS store,
   // with the other drives' scales held; rounds repeat until every cap
   // holds at the FINAL scales (bounded and deterministic; one round in
   // practice). A disabled or unpowered drive never spends (tau_d == 0
   // makes its work increment exactly zero) -- falsifier F5.
   for(int round=0;round<8;++round){
    bool scaled=false;
    auto w=work_of(trial);
    for(size_t d=0;d<n_;++d){
     if(!config_["power"].get<bool>()||!config_[model_->names[d]+"_drive"].get<bool>())continue;
     if(w[d]>battery_[d]){double lo=0,hi=1;
      for(int j=0;j<40;++j){double mid=(lo+hi)/2;scales[d]=mid;
       auto candidate=advance(s_,dt_/4,effort());
       if(work_of(candidate)[d]<=battery_[d]){lo=mid;trial=std::move(candidate);}else hi=mid;}
      scales[d]=lo;scaled=true;}}
    if(!scaled)break;
    trial=advance(s_,dt_/4,effort());
    auto wf=work_of(trial);
    for(size_t d=0;d<n_;++d)if(wf[d]>battery_[d]&&round==7)throw Refusal("coupled_store_cap_unresolved");
   }
   auto spent=work_of(trial);
   for(size_t d=0;d<n_;++d){
    double before=battery_[d];battery_[d]-=spent[d];
    require(battery_[d]>=0,"coupled_negative_store");
    if(!config_["power"].get<bool>()||!config_[model_->names[d]+"_drive"].get<bool>())require(spent[d]==0.,"coupled_disabled_drive_spent");
    if(before>1e-12&&battery_[d]<=1e-12)++empty_events_[d];
    brake_[d]+=(std::max)(0.,s_.work[d]-trial.work[d]);
    impulse_torque[d]+=tau[d]/4;
    require(std::isfinite(trial.q[d])&&std::isfinite(trial.v[d])&&trial.q[d]>=model_->lower[d]-1e-9&&trial.q[d]<=model_->upper[d]+1e-9,"coupled_state_invalid");
   }
   s_=std::move(trial);
  }
  last_torque_=impulse_torque;++ticks_;
 }
 J status()const{
  auto e=evaluate(s_);auto hand=e.point(hand_,local_);V velocity{};for(size_t i=0;i<n_;++i)velocity=add(velocity,mul(hand.second[i],s_.v[i]));
  double kinetic=.5*inner(s_.v,multiply(e.mass,s_.v)),u=e.potential-initial_potential_,energy=kinetic+u;
  double work=0,battery_total=0,brake_total=0;uint64_t empty_total=0;
  for(size_t d=0;d<n_;++d){work+=s_.work[d];battery_total+=battery_[d];brake_total+=brake_[d];empty_total+=empty_events_[d];}
  J joints=J::array();
  for(size_t d=0;d<n_;++d){const std::string& stem=model_->names[d];
   joints.push_back({{"name",model_->names[d]},{"angle_deg",s_.q[d]*180/pi},{"target_deg",config_[stem+"_target_deg"]},{"speed_rad_s",s_.v[d]},{"motor_torque_N_m",last_torque_[d]},{"gravity_torque_N_m",e.gravity[d]},{"limit_reaction_N_m",s_.impulse[d]/dt_},{"drive_enabled",config_[stem+"_drive"]},{"torque_limit_N_m",config_[stem+"_torque_limit_N_m"]}});}
  auto row=contact_row(e);double g=gap_of(e);double closing=0;for(size_t i=0;i<n_;++i)closing+=row[i]*s_.v[i];
  Dense zero(n_,0);auto [row_t,slip,tangent]=friction_row(e,s_.v,zero);
  (void)tangent;
  // Mode: friction active this tick (any tangential reaction) splits into
  // slide (dissipating heat right now) and stick (holding without slip).
  const char* mode=!contact_?"off":(g>kTouch?"free":(std::abs(s_.friction_force_impulse)>1e-15?(s_.friction_heat_tick>1e-15?"slide":"stick"):"free"));
  J jac=J::array();for(size_t i=0;i<n_;++i)jac.push_back(row[i]);
  J contact{{"enabled",contact_},{"friction",mu_>0},{"friction_mu",mu_},{"grasp",false},{"plane_world_up_m",plane_world_y_},{"proxy_radius_m",radius_},{"normal_world_up",J::array({0.,1.,0.})},{"gap_m",g},{"closing_speed_m_s",closing},{"touching",contact_&&g<=kTouch},{"jacobian_m_per_rad",jac},{"reaction_N",s_.contact_force_impulse/dt_},{"impact_impulse_N_s",s_.contact_impact_impulse},{"impact_heat_J",s_.contact_impact},{"friction_force_N",s_.friction_force_impulse/dt_},{"friction_impact_impulse_N_s",s_.friction_impulse},{"slip_speed_m_s",slip},{"mode",mode},{"generalized_reaction_N_m",array_of(s_.contact_generalized)}};
  // The ledger stays GLOBAL (S2): work = sum_d work_d; there is no
  // per-drive energy closure and none is claimed.
  J mass=J::array();for(size_t i=0;i<n_;++i){J r=J::array();for(size_t j=0;j<n_;++j)r.push_back(e.mass[n_*i+j]);mass.push_back(r);}
  J names=J::array();for(size_t i=0;i<n_;++i)names.push_back(model_->names[i]);
  return {{"sim_time_s",ticks_*dt_},{"ticks",ticks_},{"joints",joints},{"config",config_},{"power",config_["power"]},{"load_N",config_["load_N"]},{"coordinate_order",names},{"battery_empty_events",empty_total},{"contacts",{{"environment",contact_},{"joint_limits",true}}},{"contact",contact},
   {"body",{{"position_m",add(hand.first,shift_)},{"velocity_m_s",velocity},{"radius_m",recipe_["proxy_radius_m"]}}},
   {"energy",{{"kinetic_J",kinetic},{"gravitational_J",u},{"potential_reference","reset pose"},{"mechanical_J",energy},{"actuator_work_J",work},{"external_work_J",s_.external},{"damping_heat_J",s_.damping},{"impact_heat_J",s_.impact+s_.contact_impact},{"contact_impact_heat_J",s_.contact_impact},{"friction_heat_J",s_.friction_heat},{"brake_heat_J",brake_total},{"battery_J",battery_total},{"battery_initial_J",initial_store_},{"battery_initial_total_J",initial_store_*double(n_)},{"battery_usable",battery_total>1e-12},{"balance_error_J",energy-work-s_.external+s_.damping+s_.impact+s_.contact_impact+s_.friction_heat},{"store_balance_error_J",energy+battery_total+s_.damping+s_.impact+s_.contact_impact+s_.friction_heat+brake_total-initial_store_*double(n_)-s_.external},{"work_per_drive_J",array_of(s_.work)},{"battery_per_drive_J",array_of(battery_)},{"brake_per_drive_J",array_of(brake_)},{"empty_events_per_drive",array_of(empty_events_)}}},
   {"coupling",{{"mass_matrix_kg_m2",mass},{"bias_torque_N_m",array_of(e.bias)}}}};
 }
};
} // namespace chimera::multibody
