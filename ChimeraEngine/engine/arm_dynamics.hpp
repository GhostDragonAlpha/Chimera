#pragma once
#include "earth_environment.hpp"

namespace chimera::environment {
// One physical coordinate, derived from a source assembly. Geometry consumes q;
// controls only change effort requests. Fixed upstream coordinates take reaction.
class ArmDynamics {
 J recipe_,parameters_,config_;
 V axis_,pivot_,first_,hand_;
 double dt_,I_,mass_,g_,rest_,lo_,hi_,support_q_,radius_,kp_,kd_,b_,initial_battery_;
 double E0_=0,Wmotor_=0,Wexternal_=0,Qdamping_=0,Qimpact_=0,Qbrake_=0;
 double support_impulse_=0,limit_impulse_=0,torque_=0;
 V mount_force_{};
 uint64_t empty_events_=0;
 struct Trial{double q,w;};
 V rotate(V v,double angle)const{
  return add(add(mul(v,std::cos(angle)),mul(cross(axis_,v),std::sin(angle))),mul(axis_,dot(axis_,v)*(1-std::cos(angle))));
 }
 double hand_jacobian(double angle)const{return cross(axis_,rotate(hand_,angle))[1];}
 double gravity_U(double angle)const{return g_*(mass_*pivot_[1]+rotate(first_,angle)[1]);}
 double gravity_gradient(double angle)const{return g_*cross(axis_,rotate(first_,angle))[1];}
 double combined_gradient(double angle)const{return gravity_gradient(angle)+number(config_["load_N"])*hand_jacobian(angle);}
 double energy()const{return .5*I_*w*w+gravity_U(q);}
 V momentum()const{return mul(cross(axis_,rotate(first_,q)),w);}
 static double sinc(double x){return std::abs(x)<1e-5?1-x*x/6+x*x*x*x/120:std::sin(x)/x;}
 double discrete_gradient(double q0,double q1)const{
  V s=add(mul(first_,g_),mul(hand_,number(config_["load_N"])));
  double A=s[1]-axis_[1]*dot(axis_,s),B=cross(axis_,s)[1],mid=(q0+q1)/2;
  return sinc((q1-q0)/2)*(-A*std::sin(mid)+B*std::cos(mid));
 }
 Trial free_step(double h,double tau)const{
  require(h>0,"arm_positive_step");V s=add(mul(first_,g_),mul(hand_,number(config_["load_N"])));
  double amplitude=std::hypot(s[1]-axis_[1]*dot(axis_,s),cross(axis_,s)[1]);
  // A strict monotonic residual gives a unique solve, independently of iteration count.
  require(2*I_/(h*h)+b_/h>amplitude/2,"arm_step_not_uniquely_bounded");
  auto residual=[&](double end){return 2*I_*(end-q-h*w)/(h*h)+b_*(end-q)/h+discrete_gradient(q,end)-tau;};
  double span=h*(std::abs(w)+h*(std::abs(tau)+amplitude)/I_)+1e-12;
  double l=q-span,u=q+span;int expansions=0;
  while(residual(l)>0||residual(u)<0){require(++expansions<32,"arm_root_bracket");span*=2;l=q-span;u=q+span;}
  for(int i=0;i<72;++i){double mid=(l+u)/2;if(residual(mid)>0)u=mid;else l=mid;}
  double end=(l+u)/2;return {end,2*(end-q)/h-w};
 }
 void free_commit(Trial t,double h,double tau){
  double dq=t.q-q,dy=rotate(hand_,t.q)[1]-rotate(hand_,q)[1];
  Wmotor_+=tau*dq;Wexternal_-=number(config_["load_N"])*dy;Qdamping_+=b_*dq*dq/h;q=t.q;w=t.w;
 }
 double lower()const{return config_["support"].get<bool>()?(std::max)(lo_,support_q_):lo_;}
 void boundary_impulse(double boundary,double impulse){
  if(config_["support"].get<bool>()&&std::abs(boundary-support_q_)<1e-12){
   require(impulse>=-1e-12&&hand_jacobian(q)>0,"arm_unilateral_reaction");support_impulse_+=impulse/hand_jacobian(q);
  }else limit_impulse_+=impulse;
 }
 void advance(double h,double tau,int depth=0){
  if(h<=1e-14)return;require(depth<8,"arm_contact_event_budget");double low=lower();
  // Resting contact supports only an effort directed into the boundary.
  for(double wall:{low,hi_}){
   bool lower_wall=wall==low;double sign=lower_wall?1.:-1.;
   if(std::abs(q-wall)<1e-12&&sign*w<=0){
    if(w!=0){Qimpact_+=.5*I_*w*w;boundary_impulse(wall,-I_*w);w=0;}
    double net=tau-combined_gradient(q);
    if(sign*net<=0){boundary_impulse(wall,-net*h);return;}
   }
  }
  auto end=free_step(h,tau);
  if(end.q>=low&&end.q<=hi_){free_commit(end,h,tau);return;}
  double wall=end.q<low?low:hi_,left=0,right=h;bool at_lower=end.q<low;
  // Locate impact inside this tick using the same discrete-gradient free flow.
  for(int i=0;i<55;++i){double mid=(left+right)/2;auto t=free_step(mid,tau);bool crossed=at_lower?t.q<=wall:t.q>=wall;if(crossed)right=mid;else left=mid;}
  double hit=(left+right)/2;require(hit>1e-14,"arm_unresolved_impact_time");
  Trial impact{wall,2*(wall-q)/hit-w};free_commit(impact,hit,tau);
  Qimpact_+=.5*I_*w*w;boundary_impulse(wall,-I_*w);w=0;advance(h-hit,tau,depth+1);
 }
public:
 double q=0,w=0,battery=0;uint64_t ticks=0;
 ArmDynamics(const J& data,double gravity,double step_s=1/300.):recipe_(data.at("recipe")),parameters_(data.at("parameters")),dt_(step_s),g_(gravity){
  require(data.at("schema")=="chimera.force_arm.v1","arm_dynamics_schema");
  axis_=parameters_.at("axis").get<V>();pivot_=parameters_.at("pivot_m").get<V>();first_=parameters_.at("first_moment_kg_m").get<V>();hand_=parameters_.at("hand_offset_m").get<V>();
  I_=number(parameters_.at("inertia_kg_m2"));mass_=number(parameters_.at("mass_kg"));rest_=number(parameters_.at("rest_rad"));lo_=number(parameters_.at("limits_rad")[0]);hi_=number(parameters_.at("limits_rad")[1]);
  support_q_=number(recipe_.at("support_angle_deg"))*pi/180-rest_;radius_=number(recipe_.at("proxy_radius_m"));
  double frequency=2*pi*number(recipe_.at("servo_frequency_Hz"));kp_=I_*frequency*frequency;kd_=2*number(recipe_.at("servo_damping_ratio"))*I_*frequency;b_=I_*number(recipe_.at("passive_decay_rate_s"));initial_battery_=number(recipe_.at("battery_initial_J"));
  require(dt_>0&&dt_<=1/300.&&I_>0&&mass_>0&&g_>=0&&radius_>0&&lo_<0&&hi_>0&&support_q_>lo_&&support_q_<0&&b_>=0&&kp_>=0&&kd_>=0&&initial_battery_>=0&&std::abs(norm(axis_)-1)<1e-9,"arm_parameters");
  config_=recipe_.at("defaults");reset();
 }
 double timestep()const{return dt_;}
 double delta_deg()const{return q*180/pi;}
 double radius()const{return radius_;}
 bool support_enabled()const{return config_["support"].get<bool>();}
 V hand_position()const{return add(pivot_,rotate(hand_,q));}
 V hand_velocity()const{return mul(cross(axis_,rotate(hand_,q)),w);}
 double support_height()const{return pivot_[1]+rotate(hand_,support_q_)[1]-radius_;}
 const J& config()const{return config_;}
 void reset(){q=0;w=0;ticks=0;battery=initial_battery_;empty_events_=0;Wmotor_=Wexternal_=Qdamping_=Qimpact_=Qbrake_=0;support_impulse_=limit_impulse_=torque_=0;mount_force_={};E0_=energy();}
 void configure(const J& data){
  require(data.is_object()&&!data.empty(),"arm_control_object");auto c=config_;bool restart=false;
  for(auto it=data.begin();it!=data.end();++it){
   if(it.key()=="reset"){require(it.value().is_boolean()&&it.value().get<bool>(),"arm_reset_true_required");restart=true;}
   else{require(c.contains(it.key()),"unknown_arm_control");c[it.key()]=it.value();}
  }
  require(!data.contains("support")||restart,"support_change_requires_reset");require(c["power"].is_boolean()&&c["support"].is_boolean(),"arm_boolean_required");
  double target=number(c["target_deg"])*pi/180-rest_,cap=number(c["torque_limit_N_m"]),load=number(c["load_N"]);
  require(target>=lo_-1e-8&&target<=hi_+1e-8&&cap>=0&&cap<=.6&&load>=0&&load<=3,"arm_control_range");config_=c;if(restart)reset();
 }
 void step(){
  const double h=timestep(),threshold=1e-12;V before_p=momentum();double target=number(config_["target_deg"])*pi/180-rest_;
  double cap=number(config_["torque_limit_N_m"]),tau=config_["power"].get<bool>()&&battery>threshold?(std::max)(-cap,(std::min)(cap,kp_*(target-q)-kd_*w)):0;
  auto attempt=[&](double effort){auto x=*this;x.support_impulse_=x.limit_impulse_=0;x.advance(h,effort);return x;};
  auto candidate=attempt(tau);double work=candidate.Wmotor_-Wmotor_;
  if(work>battery){
   // The largest affordable effort is found against the actual solved displacement.
   double low=0,high=1;candidate=attempt(0);
   for(int i=0;i<52;++i){double mid=(low+high)/2;auto trial=attempt(tau*mid);if(trial.Wmotor_-Wmotor_<=battery){low=mid;candidate=std::move(trial);}else high=mid;}
   tau*=low;work=candidate.Wmotor_-Wmotor_;
  }
  candidate.battery=battery-(std::max)(0.,work);require(candidate.battery>=0,"arm_negative_energy_inventory");
  candidate.Qbrake_+=-(std::min)(0.,work);candidate.torque_=tau;if(battery>threshold&&candidate.battery<=threshold)++candidate.empty_events_;
  candidate.ticks=ticks+1;candidate.mount_force_=mul(sub(candidate.momentum(),before_p),1/h);
  candidate.mount_force_[1]+=mass_*g_+number(config_["load_N"])-candidate.support_impulse_/h;
  require(std::isfinite(candidate.q)&&std::isfinite(candidate.w)&&candidate.q>=candidate.lower()-1e-12&&candidate.q<=hi_+1e-12,"arm_state_invalid");*this=std::move(candidate);
 }
 J status()const{
  double support=support_impulse_/timestep(),e=energy();
  return {{"sim_time_s",ticks*timestep()},{"ticks",ticks},
   {"joint",{{"angle_deg",(q+rest_)*180/pi},{"target_deg",config_["target_deg"]},{"speed_rad_s",w},{"motor_torque_N_m",torque_},{"gravity_torque_N_m",-gravity_gradient(q)},{"external_load_N",config_["load_N"]},{"support_reaction_N",support},{"limit_reaction_N_m",limit_impulse_/timestep()},{"motor_enabled",config_["power"]},{"torque_limit_N_m",config_["torque_limit_N_m"]},{"support_enabled",config_["support"]},{"inertia_kg_m2",I_},{"moving_mass_kg",mass_},{"battery_empty_events",empty_events_}}},
   {"body",{{"position_m",hand_position()},{"velocity_m_s",hand_velocity()},{"radius_m",radius_}}},
   {"energy",{{"kinetic_J",.5*I_*w*w},{"gravitational_J",gravity_U(q)},{"mechanical_J",e},{"initial_mechanical_J",E0_},{"actuator_work_J",Wmotor_},{"external_work_J",Wexternal_},{"damping_heat_J",Qdamping_},{"impact_heat_J",Qimpact_},{"brake_heat_J",Qbrake_},{"battery_J",battery},{"battery_initial_J",initial_battery_},{"balance_error_J",e-E0_-Wmotor_-Wexternal_+Qdamping_+Qimpact_},{"store_balance_error_J",e+battery+Qdamping_+Qimpact_+Qbrake_-E0_-initial_battery_-Wexternal_}}},
   {"exchange",{{"mount_reaction_force_N",mount_force_},{"support_force_N",support},{"motor_reaction_torque_N_m",-torque_}}}};
 }
};
} // namespace chimera::environment
