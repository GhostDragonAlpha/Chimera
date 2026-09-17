#pragma once
#include "coupled_articulation.hpp"
#include <memory>
namespace chimera::multibody {
class CoupledDynamics {
 struct State {Dense q,v,work{0,0},impulse{0,0};double external=0,damping=0,impact=0;};
 struct Rate {Dense q,v,reaction;double damping;};
 std::shared_ptr<const Model> model_;J recipe_,config_;size_t hand_;V local_,shift_,gravity_;
 double dt_,initial_store_,initial_potential_=0;Dense kp_,kd_,damping_,last_torque_{0,0};
 State s_;double battery_=0,brake_=0;uint64_t ticks_=0,empty_events_=0;
 Evaluation evaluate(const State& s)const{return model_->evaluate(s.q,s.v,gravity_);}
 double mechanical(const State& s)const{auto e=evaluate(s);return .5*inner(s.v,multiply(e.mass,s.v))+e.potential;}
 Dense normals(const State& s)const{Dense n(2);for(int i=0;i<2;++i){if(std::abs(s.q[i]-model_->lower[i])<1e-10)n[i]=1;else if(std::abs(s.q[i]-model_->upper[i])<1e-10)n[i]=-1;}return n;}
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
 Rate rate(const State& s,const Dense& tau)const{
  auto e=evaluate(s);auto inv=inverse_spd(e.mass,2);auto external=e.force(hand_,local_,V{0,-number(config_["load_N"]),0});Dense rhs(2);double heat=0;
  for(int i=0;i<2;++i){rhs[i]=tau[i]+e.gravity[i]-e.bias[i]+external[i]-damping_[i]*s.v[i];heat+=damping_[i]*s.v[i]*s.v[i];}
  auto free=multiply(inv,rhs);auto normal=normals(s);for(int i=0;i<2;++i)if(std::abs(s.v[i])>1e-9)normal[i]=0;auto p=reaction(free,inv,normal);auto correction=multiply(inv,p);for(int i=0;i<2;++i)free[i]+=correction[i];return {s.v,free,p,heat};
 }
 State free_step(const State& start,double h,const Dense& tau)const{
  auto shifted=[&](const Rate& d,double t){State x=start;for(int i=0;i<2;++i){x.q[i]+=d.q[i]*t;x.v[i]+=d.v[i]*t;}return x;};
  auto a=rate(start,tau),b=rate(shifted(a,h/2),tau),c=rate(shifted(b,h/2),tau),d=rate(shifted(c,h),tau);State end=start;
  for(int i=0;i<2;++i){end.q[i]+=h*(a.q[i]+2*b.q[i]+2*c.q[i]+d.q[i])/6;end.v[i]+=h*(a.v[i]+2*b.v[i]+2*c.v[i]+d.v[i])/6;end.work[i]+=tau[i]*(end.q[i]-start.q[i]);end.impulse[i]+=h*(a.reaction[i]+2*b.reaction[i]+2*c.reaction[i]+d.reaction[i])/6;}
  end.damping+=h*(a.damping+2*b.damping+2*c.damping+d.damping)/6;
  double dy=evaluate(end).point(hand_,local_).first[1]-evaluate(start).point(hand_,local_).first[1];end.external-=number(config_["load_N"])*dy;return end;
 }
 void impact(State& s)const{
  auto normal=normals(s);auto e=evaluate(s);auto p=reaction(s.v,inverse_spd(e.mass,2),normal);auto change=multiply(inverse_spd(e.mass,2),p);double before=.5*inner(s.v,multiply(e.mass,s.v));
  for(int i=0;i<2;++i){s.v[i]+=change[i];s.impulse[i]+=p[i];}double loss=before-.5*inner(s.v,multiply(e.mass,s.v));require(loss>=-1e-11,"coupled_impact_created_energy");s.impact+=(std::max)(0.,loss);
 }
 State advance(State start,double h,const Dense& tau,int depth=0)const{
  if(h<1e-12)return start;require(depth<8,"coupled_impact_event_budget");impact(start);auto end=free_step(start,h,tau);int which=-1;double hit=h,wall=0;
  for(int i=0;i<2;++i){bool low=end.q[i]<model_->lower[i];if(!low&&end.q[i]<=model_->upper[i])continue;double bound=low?model_->lower[i]:model_->upper[i],left=0,right=h;
   for(int j=0;j<42;++j){double mid=(left+right)/2;double q=free_step(start,mid,tau).q[i];if(low?q<=bound:q>=bound)right=mid;else left=mid;}double t=(left+right)/2;if(t<=hit){hit=t;which=i;wall=bound;}}
  if(which<0)return end;
  require(hit>1e-12,"coupled_unresolved_impact_time");auto contact=free_step(start,hit,tau);require(std::abs(contact.q[which]-wall)<1e-9,"coupled_impact_localization");contact.q[which]=wall;impact(contact);return advance(contact,h-hit,tau,depth+1);
 }
 Dense torque()const{
  Dense tau(2);for(int i=0;i<2;++i){std::string stem=i?"elbow":"shoulder";if(config_["power"].get<bool>()&&config_[stem+"_drive"].get<bool>()&&battery_>1e-12){double target=number(config_[stem+"_target_deg"])*pi/180,cap=number(config_[stem+"_torque_limit_N_m"]);tau[i]=(std::max)(-cap,(std::min)(cap,kp_[i]*(target-s_.q[i])-kd_[i]*s_.v[i]));}}return tau;
 }
public:
 CoupledDynamics(const J& data,double gravity,V shift,double dt=1/300.):recipe_(data.at("recipe")),shift_(shift),gravity_{0,-gravity,0},dt_(dt){
  require(recipe_.at("schema")=="chimera.coupled_scene.v1"&&recipe_.at("coordinates")==J::array({"shoulder_flexion","elbow_flexion"}),"coupled_dynamics_schema");require(dt>0&&dt<=1/300.,"coupled_timestep");require(recipe_.at("substeps")==4,"coupled_substeps");model_=std::make_shared<Model>(data.at("model"),recipe_.at("coordinates").get<std::vector<std::string>>());hand_=model_->body(recipe_.at("hand_body"));local_=recipe_.at("hand_point_m").get<V>();config_=recipe_.at("defaults");initial_store_=number(recipe_.at("battery_initial_J"));require(initial_store_>=0,"coupled_store_initial");auto e=model_->evaluate(model_->defaults,Dense(2),gravity_);double freq=2*pi*number(recipe_["servo_frequency_Hz"]),zeta=number(recipe_["servo_damping_ratio"]),decay=number(recipe_["passive_decay_rate_s"]);require(freq>=0&&zeta>=0&&decay>=0,"coupled_drive_parameters");for(int i=0;i<2;++i){kp_.push_back(e.mass[3*i]*freq*freq);kd_.push_back(2*zeta*e.mass[3*i]*freq);damping_.push_back(e.mass[3*i]*decay);}reset();
 }
 double timestep()const{return dt_;}const Dense& angles()const{return s_.q;}const Dense& speeds()const{return s_.v;}const Model& model()const{return *model_;}
 void reset(){s_=State{};s_.q=model_->defaults;s_.v=Dense(2);ticks_=empty_events_=0;last_torque_=Dense(2);battery_=initial_store_;brake_=0;initial_potential_=evaluate(s_).potential;}
 void configure(const J& input){
  require(input.is_object()&&!input.empty(),"coupled_control_object");auto c=config_;bool restart=false;
  for(auto it=input.begin();it!=input.end();++it){if(it.key()=="reset"){require(it.value().is_boolean()&&it.value().get<bool>(),"coupled_reset_true");restart=true;}else{require(c.contains(it.key()),"unknown_coupled_control");c[it.key()]=it.value();}}
  for(auto key:{"power","shoulder_drive","elbow_drive"})require(c[key].is_boolean(),"coupled_boolean_control");
  for(int i=0;i<2;++i){std::string stem=i?"elbow":"shoulder";double target=number(c[stem+"_target_deg"])*pi/180,cap=number(c[stem+"_torque_limit_N_m"]);require(target>=model_->lower[i]-1e-8&&target<=model_->upper[i]+1e-8&&cap>=0&&cap<=(i?.6:1.),"coupled_control_range");}double load=number(c["load_N"]);require(load>=0&&load<=3,"coupled_load_range");config_=c;if(restart)reset();
 }
 void step(){
  s_.impulse=Dense(2);Dense impulse_torque(2);for(int k=0;k<4;++k){auto tau=torque();auto trial=advance(s_,dt_/4,tau);auto work=[&](const State& s){double p=0;for(int i=0;i<2;++i)p+=(std::max)(0.,s.work[i]-s_.work[i]);return p;};
   if(work(trial)>battery_){double lo=0,hi=1;trial=advance(s_,dt_/4,Dense(2));for(int j=0;j<40;++j){double mid=(lo+hi)/2;Dense effort{tau[0]*mid,tau[1]*mid};auto candidate=advance(s_,dt_/4,effort);if(work(candidate)<=battery_){lo=mid;trial=std::move(candidate);}else hi=mid;}for(double& t:tau)t*=lo;}
   double spent=work(trial),before=battery_;battery_-=spent;require(battery_>=0,"coupled_negative_store");if(before>1e-12&&battery_<=1e-12)++empty_events_;for(int i=0;i<2;++i){brake_+=(std::max)(0.,s_.work[i]-trial.work[i]);impulse_torque[i]+=tau[i]/4;require(std::isfinite(trial.q[i])&&std::isfinite(trial.v[i])&&trial.q[i]>=model_->lower[i]-1e-9&&trial.q[i]<=model_->upper[i]+1e-9,"coupled_state_invalid");}s_=std::move(trial);
  }last_torque_=impulse_torque;++ticks_;
 }
 J status()const{
  auto e=evaluate(s_);auto hand=e.point(hand_,local_);V velocity{};for(int i=0;i<2;++i)velocity=add(velocity,mul(hand.second[i],s_.v[i]));double kinetic=.5*inner(s_.v,multiply(e.mass,s_.v)),u=e.potential-initial_potential_,energy=kinetic+u,work=s_.work[0]+s_.work[1];J joints=J::array();
  for(int i=0;i<2;++i){std::string stem=i?"elbow":"shoulder";joints.push_back({{"name",model_->names[i]},{"angle_deg",s_.q[i]*180/pi},{"target_deg",config_[stem+"_target_deg"]},{"speed_rad_s",s_.v[i]},{"motor_torque_N_m",last_torque_[i]},{"gravity_torque_N_m",e.gravity[i]},{"limit_reaction_N_m",s_.impulse[i]/dt_},{"drive_enabled",config_[stem+"_drive"]},{"torque_limit_N_m",config_[stem+"_torque_limit_N_m"]}});}
  return {{"sim_time_s",ticks_*dt_},{"ticks",ticks_},{"joints",joints},{"config",config_},{"power",config_["power"]},{"load_N",config_["load_N"]},{"battery_empty_events",empty_events_},{"contacts",{{"environment",false},{"joint_limits",true}}},{"body",{{"position_m",add(hand.first,shift_)},{"velocity_m_s",velocity},{"radius_m",recipe_["proxy_radius_m"]}}},
   {"energy",{{"kinetic_J",kinetic},{"gravitational_J",u},{"potential_reference","reset pose"},{"mechanical_J",energy},{"actuator_work_J",work},{"external_work_J",s_.external},{"damping_heat_J",s_.damping},{"impact_heat_J",s_.impact},{"brake_heat_J",brake_},{"battery_J",battery_},{"battery_initial_J",initial_store_},{"battery_usable",battery_>1e-12},{"balance_error_J",energy-work-s_.external+s_.damping+s_.impact},{"store_balance_error_J",energy+battery_+s_.damping+s_.impact+brake_-initial_store_-s_.external}}},
   {"coupling",{{"mass_matrix_kg_m2",J::array({J::array({e.mass[0],e.mass[1]}),J::array({e.mass[2],e.mass[3]})})},{"bias_torque_N_m",e.bias}}}};
 }
};
} // namespace chimera::multibody
