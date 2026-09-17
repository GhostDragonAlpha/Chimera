#pragma once
#include "coupled_articulation.hpp"
#include <memory>
#if defined(CHIMERA_CONTACT_TRACE)
#include <cstdio>
#endif
namespace chimera::multibody {
class CoupledDynamics {
 struct State {Dense q,v,work{0,0},impulse{0,0};double external=0,damping=0,impact=0;double contact_impact=0,contact_impact_impulse=0,contact_force_impulse=0;double friction_heat=0,friction_heat_tick=0,friction_impulse=0,friction_force_impulse=0;Dense contact_generalized{0,0};};
 struct Rate {Dense q,v,reaction;double damping;double contact_lambda=0;Dense contact_force{0,0};double friction_lambda=0,friction_heat=0,slip=0;int mode=0;Dense friction_force{0,0};};
 std::shared_ptr<const Model> model_;J recipe_,config_;size_t hand_;V local_,shift_,gravity_;
 double dt_,initial_store_,initial_potential_=0;Dense kp_,kd_,damping_,last_torque_{0,0};
 bool contact_=false;double plane_world_y_=0,plane_model_y_=0,radius_=0,mu_=0;
 // Touching band: derived as the intra-substep drift scale a*h^2/2 (a ~ 20 m/s^2,
 // h = 1/1200 s). Stage-probe gap noise (~6e-8 m) sits far inside it, so the
 // contact row cannot flicker inside one RK4 stencil, and the settled
 // micro-penetration (same bound) stays within the band.
 static constexpr double kTouch=1e-5,kSlip=1e-9;
 State s_;double battery_=0,brake_=0;uint64_t ticks_=0,empty_events_=0;
 Evaluation evaluate(const State& s)const{return model_->evaluate(s.q,s.v,gravity_);}
 double mechanical(const State& s)const{auto e=evaluate(s);return .5*inner(s.v,multiply(e.mass,s.v))+e.potential;}
 Dense normals(const State& s)const{Dense n(2);for(int i=0;i<2;++i){if(std::abs(s.q[i]-model_->lower[i])<1e-10)n[i]=1;else if(std::abs(s.q[i]-model_->upper[i])<1e-10)n[i]=-1;}return n;}
 // Contact geometry: one authored rigid plane, world Up normal. The signed gap is
 // hand Up + proxy radius - plane height in the model frame (shift removed once);
 // free motion keeps it nonnegative and the plane can only push +Up.
 double gap_of(const Evaluation& e)const{return e.point(hand_,local_).first[1]+radius_-plane_model_y_;}
 double gap(const State& s)const{return gap_of(evaluate(s));}
 Dense contact_row(const Evaluation& e)const{auto j=e.point(hand_,local_).second;return {j[0][1],j[1][1]};}
 // Normal acceleration of the hand point at qdd=0 (centripetal/Coriolis of the
 // same analytic transforms). The unilateral constraint is on the FULL second
 // derivative of the gap: row.qdd + bias_up >= 0 while touching.
 double contact_bias(const Evaluation& e)const{return vector(e.frames[hand_].ddt,local_,1)[1];}
 // Coulomb friction row: the same hand point Jacobian projected onto the in-plane
 // unit direction of the current hand velocity (the free tangential acceleration
 // direction when at rest). Returns {row, slip speed, tangent world direction}.
 std::tuple<Dense,double,V> friction_row(const Evaluation& e,const Dense& v,const Dense& free_accel)const{
  auto j=e.point(hand_,local_).second;
  for(int pass=0;pass<2;++pass){V hand{};for(int i=0;i<2;++i){const Dense& source=pass?free_accel:v;hand=add(hand,mul(j[i],source[i]));}
   double planar=std::hypot(hand[0],hand[2]);
   if(planar>(pass?1e-9:kSlip)){V t{hand[0]/planar,0,hand[2]/planar};return {Dense{dot(t,j[0]),dot(t,j[1])},pass?0.:planar,t};}}
  return {Dense{0,0},0.,V{}};
 }
 // Mass-metric projection onto the admissible velocity/acceleration cone.
 // Returns generalized impulse/force, with nonnegative normal multipliers.
 static Dense reaction(const Dense& initial,const Dense& inverse,const Dense& normal){
  for(int mask=0;mask<4;++mask){Dense lambda(2);bool valid=true;for(int i=0;i<2;++i)if((mask&(1<<i))&&!normal[i])valid=false;if(!valid)continue;
   if(mask==3){Dense k{inverse[0],normal[0]*normal[1]*inverse[1],normal[0]*normal[1]*inverse[2],inverse[3]};lambda=multiply(inverse_spd(k,2),Dense{-normal[0]*initial[0],-normal[1]*initial[1]});}
   else for(int i=0;i<2;++i)if(mask&(1<<i))lambda[i]=-normal[i]*initial[i]/inverse[3*i];
   Dense p(2);for(int i=0;i<2;++i){if(lambda[i]<-1e-10)valid=false;p[i]=normal[i]*(std::max)(0.,lambda[i]);}auto change=multiply(inverse,p);
   for(int i=0;i<2;++i)if(normal[i]&&(initial[i]+change[i])*normal[i]<-1e-9)valid=false;
   if(valid)return p;
  }throw Refusal("coupled_contact_cone_unsolved");
 }
 // Same projection over named constraint rows (joint stops and/or the contact
 // plane). Each row k enforces row_k.x >= floor_k: coordinates use floor 0 on
 // the direct second derivative, the contact row uses -bias so the PHYSICAL
 // normal acceleration of the hand point stays nonnegative. Two coordinates
 // admit at most two independent multipliers; subsets are enumerated and each
 // candidate must satisfy every row. A row can never attract.
 static Dense reaction_rows(const Dense& initial,const Dense& inverse,const std::vector<Dense>& rows,const Dense& floors,std::vector<double>* multipliers=nullptr){
  require(rows.size()==floors.size()&&rows.size()<=3,"coupled_contact_row_budget");
  for(size_t mask=0;mask<(size_t(1)<<rows.size());++mask){
   std::vector<size_t> act;for(size_t k=0;k<rows.size();++k)if(mask>>k&1)act.push_back(k);
   if(act.size()>2)continue;Dense lambda(act.size());
   if(act.size()==2){const Dense&a=rows[act[0]],&b=rows[act[1]];auto ia=multiply(inverse,a),ib=multiply(inverse,b);
    double aa=inner(a,ia),bb=inner(b,ib),ab=inner(a,ib),det=aa*bb-ab*ab;if(det<=1e-18)continue;
    double rx=-(inner(a,initial)-floors[act[0]]),ry=-(inner(b,initial)-floors[act[1]]);lambda[0]=(rx*bb-ry*ab)/det;lambda[1]=(ry*aa-rx*ab)/det;}
   else if(act.size()==1){const Dense&a=rows[act[0]];double d=inner(a,multiply(inverse,a));if(d<=1e-18)continue;lambda[0]=-(inner(a,initial)-floors[act[0]])/d;}
   bool valid=true;Dense p(2,0);for(size_t k=0;k<act.size();++k){if(lambda[k]<-1e-10)valid=false;lambda[k]=(std::max)(0.,lambda[k]);for(int i=0;i<2;++i)p[i]+=lambda[k]*rows[act[k]][i];}
   if(!valid)continue;auto change=multiply(inverse,p);Dense projected{initial[0]+change[0],initial[1]+change[1]};
   for(size_t k=0;k<rows.size();++k)if(inner(rows[k],projected)<floors[k]-1e-9){valid=false;break;}
   if(valid){if(multipliers){multipliers->assign(rows.size(),0.);for(size_t k=0;k<act.size();++k)(*multipliers)[act[k]]=lambda[k];}return p;}
  }throw Refusal("coupled_contact_cone_unsolved");
 }
 // Coulomb friction at one evaluation point: joint (lambda_n, f_t) solve so the
 // hand's normal and tangential components reach their floors, with f_t signed
 // (not unilateral). Stick when |f_t| <= mu*lambda_n; slide caps f_t at
 // -mu*lambda_n*sign(slip) and re-solves lambda_n with the exact M^-1
 // cross-coupling. Friction never acts without a positive normal reaction.
 static void friction_solve(const Dense& initial,const Dense& inverse,const Dense& row_n,const Dense& row_t,double floor_n,double floor_t,double mu,double slip_sign,Dense& force,double& lambda_n,double& lambda_t,int& mode){
  auto in=multiply(inverse,row_n),it=multiply(inverse,row_t);
  double A=inner(row_n,in),B=inner(row_n,it),C=inner(row_t,it),rn=-(inner(row_n,initial)-floor_n),rt=-(inner(row_t,initial)-floor_t),det=A*C-B*B;
  if(det>1e-18){double n=(rn*C-rt*B)/det,t=(rt*A-rn*B)/det;
   if(n>=0&&std::abs(t)<=mu*n+1e-12){force=Dense{row_n[0]*n+row_t[0]*t,row_n[1]*n+row_t[1]*t};lambda_n=n;lambda_t=t;mode=1;return;}}
  double s=slip_sign!=0.?slip_sign:(rt>=0.?1.:-1.),den=A-s*mu*B;
  if(den<=1e-12)throw Refusal("coupled_friction_slide_singular");
  double n=rn/den,t=-s*mu*n;
  if(n>=0){force=Dense{row_n[0]*n+row_t[0]*t,row_n[1]*n+row_t[1]*t};lambda_n=n;lambda_t=t;mode=2;return;}
  force=Dense{0,0};lambda_n=0;lambda_t=0;mode=0;
 }
 Rate rate(const State& s,const Dense& tau,bool live,bool plane=false)const{
  auto e=evaluate(s);auto inv=inverse_spd(e.mass,2);auto external=e.force(hand_,local_,V{0,-number(config_["load_N"]),0});Dense rhs(2);double heat=0;
  for(int i=0;i<2;++i){rhs[i]=tau[i]+e.gravity[i]-e.bias[i]+external[i]-damping_[i]*s.v[i];heat+=damping_[i]*s.v[i]*s.v[i];}
  auto free=multiply(inv,rhs);
  bool friction=contact_&&live&&mu_>0;
  if(!contact_||!live){auto normal=normals(s);for(int i=0;i<2;++i)if(std::abs(s.v[i])>1e-9)normal[i]=0;auto p=reaction(free,inv,normal);auto correction=multiply(inv,p);for(int i=0;i<2;++i)free[i]+=correction[i];return {s.v,free,p,heat};}
  std::vector<Dense> rows;Dense floors;auto joint=normals(s);
  bool stop=false;
  for(int i=0;i<2;++i)if(joint[i]&&std::abs(s.v[i])<=1e-9){rows.push_back(Dense{i?0.:double(joint[i]),i?double(joint[i]):0.});floors.push_back(0);stop=true;}
  auto row=contact_row(e);
  // Release gate is scale-aware: the contact row itself rotates with q at arm
  // scale, so probe-stage closing speeds carry O(0.1*|qdot|*h) kinematic noise.
  double gate=1e-6+1e-3*(std::abs(s.v[0])+std::abs(s.v[1]));
  // With friction active the plane mode is decided once per SUBSTEP (`plane`):
  // the friction impulse chain can leave a tiny separating residue that would
  // flicker the per-stage gate and let alternating stages fall unconstrained.
  bool touching=plane||(gap_of(e)<=kTouch&&inner(row,s.v)<=gate);
  if(touching){rows.push_back(row);floors.push_back(-contact_bias(e));}
  // Friction participates only in plain contact stages: no simultaneous joint
  // stop rows, a positive normal reaction and a defined in-plane direction.
  Rate out{s.v,free,Dense(2,0),heat};
  if(touching&&!stop&&friction){
   auto [row_t,slip,tangent]=friction_row(e,s.v,free);
   if(row_t[0]||row_t[1]){
    double slip_v=slip_signed(s.v,row_t);
    V bias=vector(e.frames[hand_].ddt,local_,1);
    try{Dense force;double lambda_n,lambda_t;int mode;
     friction_solve(free,inv,row,row_t,floors.back(),-dot(tangent,V{bias[0],0,bias[2]}),mu_,slip_v>0.?1.:(slip_v<0.?-1.:0.),force,lambda_n,lambda_t,mode);
     if(mode){auto correction=multiply(inv,force);for(int i=0;i<2;++i)free[i]+=correction[i];
#if defined(CHIMERA_CONTACT_TRACE)
      {Dense after{free[0],free[1]};std::fprintf(stderr,"RATE mode=%d lambda_n=%.6g f_t=%.6g Jn_qdd=%.6g floor_n=%.6g gap=%.4g slip=%.6g sign=%.0f\n",mode,lambda_n,lambda_t,inner(row,after),floors.back(),gap_of(e),slip_v,slip_v>0.?1.:(slip_v<0.?-1.:0.));}
#endif
      out.reaction=force;out.contact_lambda=lambda_n;for(int i=0;i<2;++i)out.contact_force[i]=lambda_n*row[i];
      out.friction_lambda=lambda_t;for(int i=0;i<2;++i)out.friction_force[i]=lambda_t*row_t[i];
      out.slip=std::abs(slip_v);out.mode=mode;out.friction_heat=lambda_t!=0.?-(lambda_t*slip_v):0.;}}
    catch(const Refusal&){/* singular slide geometry this stage: keep the frictionless solve */}}}
  if(out.mode==0){
   std::vector<double> multipliers;auto p=reaction_rows(free,inv,rows,floors,&multipliers);auto correction=multiply(inv,p);for(int i=0;i<2;++i)free[i]+=correction[i];
   out.reaction=p;
   if(touching){out.contact_lambda=multipliers.back();for(int i=0;i<2;++i)out.contact_force[i]=out.contact_lambda*row[i];}}
  out.v=free;
  return out;
 }
 // Signed slip speed along the friction row (row_t . qdot), used for heat power.
 static double slip_signed(const Dense& v,const Dense& row_t){return row_t[0]*v[0]+row_t[1]*v[1];}
 State free_step(const State& start,double h,const Dense& tau,bool live=true)const{
  auto shifted=[&](const Rate& d,double t){State x=start;for(int i=0;i<2;++i){x.q[i]+=d.q[i]*t;x.v[i]+=d.v[i]*t;}return x;};
  // Substep-level plane mode (friction only): holds the contact row through all
  // four stages when the substep starts in the band with sub-noise closing speed.
  bool plane=false;
  if(contact_&&live&&mu_>0){auto e0=evaluate(start);plane=gap_of(e0)<=kTouch&&inner(contact_row(e0),start.v)<=1e-6+1e-3*(std::abs(start.v[0])+std::abs(start.v[1]));}
  auto a=rate(start,tau,live,plane),b=rate(shifted(a,h/2),tau,live,plane),c=rate(shifted(b,h/2),tau,live,plane),d=rate(shifted(c,h),tau,live,plane);State end=start;
#if defined(CHIMERA_CONTACT_TRACE)
  if(contact_&&live){auto e0=evaluate(start);auto r0=contact_row(e0);std::fprintf(stderr,"FSTEP plane=%d in_closing=%.6g a=[%.4g,%.4g] b=[%.4g,%.4g] c=[%.4g,%.4g] d=[%.4g,%.4g]\n",(int)plane,inner(r0,start.v),a.v[0],a.v[1],b.v[0],b.v[1],c.v[0],c.v[1],d.v[0],d.v[1]);}
#endif
  for(int i=0;i<2;++i){end.q[i]+=h*(a.q[i]+2*b.q[i]+2*c.q[i]+d.q[i])/6;end.v[i]+=h*(a.v[i]+2*b.v[i]+2*c.v[i]+d.v[i])/6;end.work[i]+=tau[i]*(end.q[i]-start.q[i]);end.impulse[i]+=h*(a.reaction[i]+2*b.reaction[i]+2*c.reaction[i]+d.reaction[i])/6;end.contact_generalized[i]+=h*((a.contact_force[i]+a.friction_force[i])+2*(b.contact_force[i]+b.friction_force[i])+2*(c.contact_force[i]+c.friction_force[i])+(d.contact_force[i]+d.friction_force[i]))/6;}
  end.damping+=h*(a.damping+2*b.damping+2*c.damping+d.damping)/6;end.contact_force_impulse+=h*(a.contact_lambda+2*b.contact_lambda+2*c.contact_lambda+d.contact_lambda)/6;
  end.friction_heat+=h*(a.friction_heat+2*b.friction_heat+2*c.friction_heat+d.friction_heat)/6;
  end.friction_heat_tick+=h*(a.friction_heat+2*b.friction_heat+2*c.friction_heat+d.friction_heat)/6;
  end.friction_force_impulse+=h*(a.friction_lambda+2*b.friction_lambda+2*c.friction_lambda+d.friction_lambda)/6;
  double dy=evaluate(end).point(hand_,local_).first[1]-evaluate(start).point(hand_,local_).first[1];end.external-=number(config_["load_N"])*dy;
#if defined(CHIMERA_CONTACT_TRACE)
  if(contact_&&live){double de=mechanical(end)-mechanical(start),w=(end.work[0]-start.work[0])+(end.work[1]-start.work[1]),dm=end.damping-start.damping,fh=end.friction_heat-start.friction_heat,r=de-w-(end.external-start.external)+dm+fh;if(std::abs(r)>1e-8)std::fprintf(stderr,"FLEAK r=%.6g h=%.6g plane=%d\n",r,h,(int)plane);}
#endif
  return end;
 }
 double impact(State& s)const{
  if(!contact_){auto normal=normals(s);auto e=evaluate(s);auto p=reaction(s.v,inverse_spd(e.mass,2),normal);auto change=multiply(inverse_spd(e.mass,2),p);double before=.5*inner(s.v,multiply(e.mass,s.v));
   for(int i=0;i<2;++i){s.v[i]+=change[i];s.impulse[i]+=p[i];}double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"coupled_impact_created_energy");s.impact+=(std::max)(0.,loss);return 0.;}
  auto e=evaluate(s);auto inv=inverse_spd(e.mass,2);std::vector<Dense> rows;Dense floors;auto joint=normals(s);
  for(int i=0;i<2;++i)if(joint[i]){rows.push_back(Dense{i?0.:double(joint[i]),i?double(joint[i]):0.});floors.push_back(0);}
  bool touching=gap_of(e)<=kTouch;if(touching){rows.push_back(contact_row(e));floors.push_back(0);}
  // Coulomb landing impulse: one JOINT (lambda_n, lambda_t) solve so the closing
  // velocity lands exactly at zero in stick AND capped-slide modes. A sequential
  // tangential cap would re-open closing through the mass cross-coupling and
  // leave a separating residue that flickers the next substep's contact mode.
  if(touching&&mu_>0&&rows.size()==1){
   auto [row_t,slip,tangent]=friction_row(e,s.v,s.v);
   if(row_t[0]||row_t[1]){double slip_v=slip_signed(s.v,row_t);
    try{Dense force;double lambda_n,lambda_t;int mode;
     friction_solve(s.v,inv,rows[0],row_t,0,0,mu_,slip_v>0.?1.:(slip_v<0.?-1.:0.),force,lambda_n,lambda_t,mode);
     if(mode){auto change=multiply(inv,force);double before=.5*inner(s.v,multiply(e.mass,s.v));
      Dense mean{s.v[0]+change[0]/2,s.v[1]+change[1]/2};
      for(int i=0;i<2;++i){s.v[i]+=change[i];s.impulse[i]+=force[i];}
      double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"coupled_impact_created_energy");
      // Per-row dissipation split: sum_k lambda_k (v_mean . row_k) equals the loss exactly.
      double share_n=lambda_n*inner(rows[0],mean),share_t=lambda_t*inner(row_t,mean);
      require(share_n<=1e-11&&share_t<=1e-11,"coupled_contact_impact_gain");
      s.impact+=(std::max)(0.,loss+share_n+share_t);s.contact_impact+=(std::max)(0.,-share_n);s.contact_impact_impulse+=lambda_n;
      s.friction_heat+=(std::max)(0.,-share_t);s.friction_impulse+=std::abs(lambda_t);
#if defined(CHIMERA_CONTACT_TRACE)
      std::fprintf(stderr,"IMP joint mode=%d closing=%.6g slip=%.6g loss=%.6g\n",mode,inner(rows[0],Dense{s.v[0],s.v[1]}),inner(row_t,Dense{s.v[0],s.v[1]}),loss);
#endif
      return lambda_n;}}
    catch(const Refusal&){/* singular geometry: fall through to the frictionless impulse */}}}
  std::vector<double> multipliers;auto p=reaction_rows(s.v,inv,rows,floors,&multipliers);auto change=multiply(inv,p);double before=.5*inner(s.v,multiply(e.mass,s.v));
  Dense mean{s.v[0]+change[0]/2,s.v[1]+change[1]/2};for(int i=0;i<2;++i){s.v[i]+=change[i];s.impulse[i]+=p[i];}
  double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"coupled_impact_created_energy");
  if(touching){double lambda=multipliers.back();double share=lambda*inner(contact_row(e),mean);require(share<=1e-11,"coupled_contact_impact_gain");s.impact+=(std::max)(0.,loss+share);s.contact_impact+=(std::max)(0.,-share);s.contact_impact_impulse+=lambda;return lambda;}
  s.impact+=(std::max)(0.,loss);return 0.;
 }
 State advance(State start,double h,const Dense& tau,int depth=0)const{
  if(h<1e-12)return start;require(depth<8,"coupled_impact_event_budget");double caught=impact(start);
  // A friction catch at substep entry leaves a violent post-impulse transient;
  // integrating the catching substep in halves quarters its O(h^2) defect.
  if(mu_>0&&caught>1e-9&&depth<5)return advance(advance(start,h/2,tau,depth+3),h/2,tau,depth+3);
  // Contact rows are live only in a substep that STARTS in contact. A live-row
  // rollout across a first crossing would let late stages catch the hand, hide
  // the endpoint crossing and do unaccounted discrete constraint work.
  bool live=!contact_||gap(start)<=kTouch;
  auto end=free_step(start,h,tau,live);int which=-1;double hit=h,wall=0;
  for(int i=0;i<2;++i){bool low=end.q[i]<model_->lower[i];if(!low&&end.q[i]<=model_->upper[i])continue;double bound=low?model_->lower[i]:model_->upper[i],left=0,right=h;
   for(int j=0;j<42;++j){double mid=(left+right)/2;double q=free_step(start,mid,tau,live).q[i];if(low?q<=bound:q>=bound)right=mid;else left=mid;}double t=(left+right)/2;if(t<=hit){hit=t;which=i;wall=bound;}}
  if(contact_&&!live&&gap(end)<0){double left=0,right=h;
   // The pre-touching piece is integrated without contact rows: no contact force
   // exists before the first touching state.
   for(int j=0;j<42;++j){double mid=(left+right)/2;if(gap(free_step(start,mid,tau,false))<=0)right=mid;else left=mid;}double t=(left+right)/2;if(t<=hit){hit=t;which=2;}}
  if(which<0)return end;
  require(hit>1e-12,"coupled_unresolved_impact_time");
  if(which==2){auto crossing=free_step(start,hit,tau,false);require(std::abs(gap(crossing))<1e-9,"coupled_contact_localization");impact(crossing);
   // The friction catch transient magnifies the event-split boundary defect
   // (O(h^2) per piece); halving the first post-landing intervals quarters it.
   if(mu_>0)return advance(advance(crossing,(h-hit)/2,tau,depth+1),(h-hit)/2,tau,depth+2);
   return advance(crossing,h-hit,tau,depth+1);}
  auto wall_state=free_step(start,hit,tau,live);require(std::abs(wall_state.q[which]-wall)<1e-9,"coupled_impact_localization");wall_state.q[which]=wall;impact(wall_state);return advance(wall_state,h-hit,tau,depth+1);
 }
 Dense torque()const{
  Dense tau(2);for(int i=0;i<2;++i){std::string stem=i?"elbow":"shoulder";if(config_["power"].get<bool>()&&config_[stem+"_drive"].get<bool>()&&battery_>1e-12){double target=number(config_[stem+"_target_deg"])*pi/180,cap=number(config_[stem+"_torque_limit_N_m"]);tau[i]=(std::max)(-cap,(std::min)(cap,kp_[i]*(target-s_.q[i])-kd_[i]*s_.v[i]));}}return tau;
 }
public:
 CoupledDynamics(const J& data,double gravity,V shift,double dt=1/300.):recipe_(data.at("recipe")),shift_(shift),gravity_{0,-gravity,0},dt_(dt){
  require(recipe_.at("schema")=="chimera.coupled_scene.v1"&&recipe_.at("coordinates")==J::array({"shoulder_flexion","elbow_flexion"}),"coupled_dynamics_schema");require(dt>0&&dt<=1/300.,"coupled_timestep");require(recipe_.at("substeps")==4,"coupled_substeps");model_=std::make_shared<Model>(data.at("model"),recipe_.at("coordinates").get<std::vector<std::string>>());hand_=model_->body(recipe_.at("hand_body"));local_=recipe_.at("hand_point_m").get<V>();config_=recipe_.at("defaults");initial_store_=number(recipe_.at("battery_initial_J"));require(initial_store_>=0,"coupled_store_initial");
  plane_world_y_=number(recipe_.at("contact_plane_height_m"));require(std::isfinite(plane_world_y_),"coupled_contact_plane_invalid");radius_=number(recipe_.at("proxy_radius_m"));require(radius_>0,"coupled_contact_radius_invalid");plane_model_y_=plane_world_y_-shift_[1];
  require(config_.contains("contact_enabled")&&config_["contact_enabled"].is_boolean(),"coupled_contact_flag_invalid");contact_=config_["contact_enabled"].get<bool>();
  require(config_.contains("contact_friction")&&config_["contact_friction"].is_number()&&number(config_["contact_friction"])>=0&&number(config_["contact_friction"])<=1,"coupled_friction_flag_invalid");mu_=number(config_["contact_friction"]);
  {State probe;probe.q=model_->defaults;probe.v=Dense(2);require(gap(probe)>1e-6,"coupled_contact_initial_penetration");}
  auto e=model_->evaluate(model_->defaults,Dense(2),gravity_);double freq=2*pi*number(recipe_["servo_frequency_Hz"]),zeta=number(recipe_["servo_damping_ratio"]),decay=number(recipe_["passive_decay_rate_s"]);require(freq>=0&&zeta>=0&&decay>=0,"coupled_drive_parameters");for(int i=0;i<2;++i){kp_.push_back(e.mass[3*i]*freq*freq);kd_.push_back(2*zeta*e.mass[3*i]*freq);damping_.push_back(e.mass[3*i]*decay);}reset();
 }
 double timestep()const{return dt_;}const Dense& angles()const{return s_.q;}const Dense& speeds()const{return s_.v;}const Model& model()const{return *model_;}
 void reset(){s_=State{};s_.q=model_->defaults;s_.v=Dense(2);ticks_=empty_events_=0;last_torque_=Dense(2);battery_=initial_store_;brake_=0;initial_potential_=evaluate(s_).potential;}
 void configure(const J& input){
  require(input.is_object()&&!input.empty(),"coupled_control_object");auto c=config_;bool restart=false;
  for(auto it=input.begin();it!=input.end();++it){if(it.key()=="reset"){require(it.value().is_boolean()&&it.value().get<bool>(),"coupled_reset_true");restart=true;}else{require(c.contains(it.key()),"unknown_coupled_control");c[it.key()]=it.value();}}
  for(auto key:{"power","shoulder_drive","elbow_drive"})require(c[key].is_boolean(),"coupled_boolean_control");
  if(c.contains("contact_enabled")){require(c["contact_enabled"].is_boolean(),"coupled_boolean_control");if(c["contact_enabled"].get<bool>()!=config_["contact_enabled"].get<bool>())require(restart,"coupled_contact_toggle_requires_reset");}
  if(c.contains("contact_friction")){double m=number(c["contact_friction"]);require(c["contact_friction"].is_number()&&m>=0&&m<=1,"coupled_friction_range");}
  for(int i=0;i<2;++i){std::string stem=i?"elbow":"shoulder";double target=number(c[stem+"_target_deg"])*pi/180,cap=number(c[stem+"_torque_limit_N_m"]);require(target>=model_->lower[i]-1e-8&&target<=model_->upper[i]+1e-8&&cap>=0&&cap<=(i?.6:1.),"coupled_control_range");}double load=number(c["load_N"]);require(load>=0&&load<=3,"coupled_load_range");config_=c;contact_=config_["contact_enabled"].get<bool>();mu_=number(config_["contact_friction"]);if(restart)reset();
 }
 void step(){
  s_.impulse=Dense(2);s_.contact_impact_impulse=0;s_.contact_force_impulse=0;s_.contact_generalized=Dense(2);s_.friction_impulse=0;s_.friction_force_impulse=0;s_.friction_heat_tick=0;Dense impulse_torque(2);for(int k=0;k<4;++k){auto tau=torque();auto trial=advance(s_,dt_/4,tau);auto work=[&](const State& s){double p=0;for(int i=0;i<2;++i)p+=(std::max)(0.,s.work[i]-s_.work[i]);return p;};
   if(work(trial)>battery_){double lo=0,hi=1;trial=advance(s_,dt_/4,Dense(2));for(int j=0;j<40;++j){double mid=(lo+hi)/2;Dense effort{tau[0]*mid,tau[1]*mid};auto candidate=advance(s_,dt_/4,effort);if(work(candidate)<=battery_){lo=mid;trial=std::move(candidate);}else hi=mid;}for(double& t:tau)t*=lo;}
   double spent=work(trial),before=battery_;battery_-=spent;require(battery_>=0,"coupled_negative_store");if(before>1e-12&&battery_<=1e-12)++empty_events_;for(int i=0;i<2;++i){brake_+=(std::max)(0.,s_.work[i]-trial.work[i]);impulse_torque[i]+=tau[i]/4;require(std::isfinite(trial.q[i])&&std::isfinite(trial.v[i])&&trial.q[i]>=model_->lower[i]-1e-9&&trial.q[i]<=model_->upper[i]+1e-9,"coupled_state_invalid");}s_=std::move(trial);
  }last_torque_=impulse_torque;++ticks_;
 }
 J status()const{
  auto e=evaluate(s_);auto hand=e.point(hand_,local_);V velocity{};for(int i=0;i<2;++i)velocity=add(velocity,mul(hand.second[i],s_.v[i]));double kinetic=.5*inner(s_.v,multiply(e.mass,s_.v)),u=e.potential-initial_potential_,energy=kinetic+u,work=s_.work[0]+s_.work[1];J joints=J::array();
  for(int i=0;i<2;++i){std::string stem=i?"elbow":"shoulder";joints.push_back({{"name",model_->names[i]},{"angle_deg",s_.q[i]*180/pi},{"target_deg",config_[stem+"_target_deg"]},{"speed_rad_s",s_.v[i]},{"motor_torque_N_m",last_torque_[i]},{"gravity_torque_N_m",e.gravity[i]},{"limit_reaction_N_m",s_.impulse[i]/dt_},{"drive_enabled",config_[stem+"_drive"]},{"torque_limit_N_m",config_[stem+"_torque_limit_N_m"]}});}
  auto row=contact_row(e);double g=gap_of(e),closing=row[0]*s_.v[0]+row[1]*s_.v[1];
  auto [row_t,slip,tangent]=friction_row(e,s_.v,Dense{0,0});
  // Mode: friction active this tick (any tangential reaction) splits into slide
  // (dissipating heat right now) and stick (holding without slip).
  const char* mode=!contact_?"off":(g>kTouch?"free":(std::abs(s_.friction_force_impulse)>1e-15?(s_.friction_heat_tick>1e-15?"slide":"stick"):"free"));
  J contact{{"enabled",contact_},{"friction",mu_>0},{"friction_mu",mu_},{"grasp",false},{"plane_world_up_m",plane_world_y_},{"proxy_radius_m",radius_},{"normal_world_up",J::array({0.,1.,0.})},{"gap_m",g},{"closing_speed_m_s",closing},{"touching",contact_&&g<=kTouch},{"jacobian_m_per_rad",J::array({row[0],row[1]})},{"reaction_N",s_.contact_force_impulse/dt_},{"impact_impulse_N_s",s_.contact_impact_impulse},{"impact_heat_J",s_.contact_impact},{"friction_force_N",s_.friction_force_impulse/dt_},{"friction_impact_impulse_N_s",s_.friction_impulse},{"slip_speed_m_s",slip},{"mode",mode},{"generalized_reaction_N_m",J::array({s_.contact_generalized[0]/dt_,s_.contact_generalized[1]/dt_})}};
  return {{"sim_time_s",ticks_*dt_},{"ticks",ticks_},{"joints",joints},{"config",config_},{"power",config_["power"]},{"load_N",config_["load_N"]},{"battery_empty_events",empty_events_},{"contacts",{{"environment",contact_},{"joint_limits",true}}},{"contact",contact},{"body",{{"position_m",add(hand.first,shift_)},{"velocity_m_s",velocity},{"radius_m",recipe_["proxy_radius_m"]}}},
   {"energy",{{"kinetic_J",kinetic},{"gravitational_J",u},{"potential_reference","reset pose"},{"mechanical_J",energy},{"actuator_work_J",work},{"external_work_J",s_.external},{"damping_heat_J",s_.damping},{"impact_heat_J",s_.impact+s_.contact_impact},{"contact_impact_heat_J",s_.contact_impact},{"friction_heat_J",s_.friction_heat},{"brake_heat_J",brake_},{"battery_J",battery_},{"battery_initial_J",initial_store_},{"battery_usable",battery_>1e-12},{"balance_error_J",energy-work-s_.external+s_.damping+s_.impact+s_.contact_impact+s_.friction_heat},{"store_balance_error_J",energy+battery_+s_.damping+s_.impact+s_.contact_impact+s_.friction_heat+brake_-initial_store_-s_.external}}},
   {"coupling",{{"mass_matrix_kg_m2",J::array({J::array({e.mass[0],e.mass[1]}),J::array({e.mass[2],e.mass[3]})})},{"bias_torque_N_m",e.bias}}}};
 }
};
} // namespace chimera::multibody
