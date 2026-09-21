#pragma once
#include "force_models.hpp"
namespace chimera::environment {
using J=chimera::forces::json;using V=std::array<double,3>;
using chimera::forces::require;using chimera::forces::number;
inline V add(V a,V b){for(int k=0;k<3;++k)a[k]+=b[k];return a;}
inline V sub(V a,V b){for(int k=0;k<3;++k)a[k]-=b[k];return a;}
inline V mul(V a,double s){for(double& x:a)x*=s;return a;}
inline double dot(V a,V b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
inline double norm(V a){return std::sqrt(dot(a,a));}
inline V cross(V a,V b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
constexpr double pi=3.14159265358979323846;
struct Frame {
 V origin,east,up,south;
 V local_to_ecef(V x)const{return add(origin,add(mul(east,x[0]),add(mul(up,x[1]),mul(south,x[2]))));}
 V ecef_to_local(V x)const{auto d=sub(x,origin);return {dot(d,east),dot(d,up),dot(d,south)};}
 J json()const{return {{"ecef_origin_m",origin},{"east",east},{"up",up},{"south",south},{"precision","float64; render local metres"}};}
};
inline Frame make_frame(const J& datum,double lat_deg,double lon_deg,double altitude){
 require(std::isfinite(lat_deg)&&std::isfinite(lon_deg)&&std::isfinite(altitude)&&std::abs(lat_deg)<=90&&std::abs(lon_deg)<=180,"earth_coordinate_range");
 double lat=lat_deg*pi/180,lon=lon_deg*pi/180,a=number(datum.at("semi_major_m")),f=1/number(datum.at("inverse_flattening")),e2=f*(2-f),n=a/std::sqrt(1-e2*std::sin(lat)*std::sin(lat));
 Frame x;x.origin={(n+altitude)*std::cos(lat)*std::cos(lon),(n+altitude)*std::cos(lat)*std::sin(lon),(n*(1-e2)+altitude)*std::sin(lat)};
 x.east={-std::sin(lon),std::cos(lon),0};x.up={std::cos(lat)*std::cos(lon),std::cos(lat)*std::sin(lon),std::sin(lat)};x.south=cross(x.east,x.up);return x;
}
// Body-independent field sample. The field never needs to know a creature mesh.
struct EarthFields {
 Frame frame;V central_acceleration_ecef;double gravity,temperature,pressure,density;
};
inline EarthFields sample_earth(const chimera::forces::Library& library,const J& params,double latitude,double longitude,double altitude,bool air=true){
 require(std::isfinite(altitude)&&altitude>=0&&altitude<=number(params.at("atmosphere").at("max_altitude_m")),"earth_altitude_out_of_range");
 EarthFields f;f.frame=make_frame(params.at("datum"),latitude,longitude,altitude);
 f.central_acceleration_ecef=library.gravity("399",f.frame.origin,1).at("acceleration_m_s2").get<V>();f.gravity=norm(f.central_acceleration_ecef);
 const auto& a=params.at("atmosphere");double tc=number(a.at("temperature0_C"))-number(a.at("lapse_C_m"))*altitude;
 f.temperature=tc+number(a.at("celsius_to_kelvin"));f.pressure=number(a.at("pressure_scale_Pa"))*std::pow((tc+number(a.at("fit_temperature_offset")))/number(a.at("pressure_reference_K")),number(a.at("exponent")));
 f.density=f.pressure/(number(a.at("density_R_J_kg_K"))*(tc+number(a.at("fit_temperature_offset"))));
 if(!air){f.pressure=0;f.density=0;}return f;
}
class EarthTrial {
 chimera::forces::Library library_;J params_,scene_,config_;Frame frame_;
 double g_=0,Tair_=0,pair_=0,rho_=0,m_=0,r_=0,C_=0,H_=0,cd_=0,area_=0,volume_=0,geff_=0;
 V n_{0,1,0},tangent_{1,0,0},gravity_impulse_{},buoyancy_impulse_{},air_impulse_{},ground_impulse_{};
 double E0_=0,Wwind_=0,Wbuoy_=0,Ddrag_=0,Dcontact_=0,Dfriction_=0,Qair_=0,T0_=0,normal_impulse_=0;
 V start_{};
 double energy()const{return .5*m_*dot(v,v)+m_*g_*x[1];}
 void move_free(double dt){
  double y=x[1];x=add(x,mul(v,dt));x[1]-=.5*geff_*dt*dt;v[1]-=geff_*dt;Wbuoy_+=rho_*volume_*g_*(x[1]-y);
 }
 void impact(){
  double vn=dot(v,n_);if(vn>=0)return;
  V before=v;double Jn=-m_*vn;normal_impulse_+=Jn;v=sub(v,mul(n_,vn));Dcontact_+=.5*m_*vn*vn;
  double vt=dot(v,tangent_),dv=(std::min)(std::abs(vt),number(config_["friction"])*Jn/m_);
  double next=vt-std::copysign(dv,vt);Dfriction_+=.5*m_*(vt*vt-next*next);v=add(v,mul(tangent_,next-vt));ground_impulse_=add(ground_impulse_,mul(sub(v,before),m_));
 }
 void slide(double dt){
  if(dt<=0)return;
  V before=v;double y=x[1],vt=dot(v,tangent_),at=-geff_*tangent_[1],mu=number(config_["friction"]),fric=mu*geff_*n_[1],distance=0,path=0;
  auto piece=[&](double a,double h){double d=vt*h+.5*a*h*h;distance+=d;path+=std::abs(d);vt+=a*h;};
  if(std::abs(vt)<1e-14)vt=0;
  if(vt!=0){double a=at-std::copysign(fric,vt),stop=a*vt<0?-vt/a:dt+1;if(stop<dt){piece(a,stop);vt=0;dt-=stop;if(std::abs(at)>fric)piece(at-std::copysign(fric,at),dt);}else piece(a,dt);}
  else if(std::abs(at)>fric)piece(at-std::copysign(fric,at),dt);
  x=add(x,mul(tangent_,distance));v=mul(tangent_,vt);Dfriction_+=m_*fric*path;Wbuoy_+=rho_*volume_*g_*(x[1]-y);
  // Caller accounts normal support for the complete contact interval.
  ground_impulse_=add(ground_impulse_,mul(sub(v,before),m_));
 }
 void mechanics(double dt){
  const V wind{number(config_["wind_m_s"]),0,0};const double k=.5*rho_*cd_*area_;
  double d=dot(x,n_)-r_,vn=dot(v,n_);normal_impulse_=0;
  const V acc{0,-geff_,0};gravity_impulse_[1]-=m_*g_*dt;buoyancy_impulse_[1]+=rho_*volume_*g_*dt;
  // A resting contact balances the combined tangential load, including wind.
  V airF=mul(wind,k*norm(wind)),total=add(mul(acc,m_),airF);double normal=-dot(total,n_),drive=dot(total,tangent_);
  if(d<=1e-12&&norm(v)<1e-14&&normal>=0&&std::abs(drive)<=number(config_["friction"])*normal){
   V ja=mul(airF,dt);air_impulse_=add(air_impulse_,ja);ground_impulse_=sub(ground_impulse_,mul(total,dt));normal_impulse_=normal*dt;
   double work=dot(wind,ja);Wwind_+=work;Ddrag_+=work;return;
  }
  if(d<=1e-12&&vn<=1e-12){
   impact();normal_impulse_+=m_*geff_*n_[1]*dt;slide(dt);ground_impulse_=sub(ground_impulse_,mul(acc,m_*dt));
  }else{
   double down=geff_*n_[1];require(d>=-1e-10&&down>0,"earth_contact_domain");
   double hit=(vn+std::sqrt(vn*vn+2*down*(std::max)(0.,d)))/down;
   if(hit>=dt)move_free(dt);
   else{move_free(hit);x=sub(x,mul(n_,dot(x,n_)-r_));impact();double remain=dt-hit;normal_impulse_+=m_*geff_*n_[1]*remain;slide(remain);ground_impulse_=sub(ground_impulse_,mul(acc,m_*remain));}
  }
  // Exact drag subflow for a fixed uniform wind: cannot reverse relative velocity.
  V before=v,u=sub(v,wind);double scale=1/(1+k*norm(u)*dt/m_);v=add(wind,mul(u,scale));V impulse=mul(sub(v,before),m_);
  air_impulse_=add(air_impulse_,impulse);Wwind_+=dot(wind,impulse);Ddrag_+=.5*m_*dot(u,u)*(1-scale*scale);
  if(dot(x,n_)-r_<=1e-12)impact();
 }
public:
 V x{},v{};double temperature=295,time=0;uint64_t ticks=0;bool held=true,outside=false;
 explicit EarthTrial(const J& models,const J& params,const J& scene):library_(models),params_(params),scene_(scene){
  require(scene.at("schema")=="chimera.earth_patch.v1"&&number(scene.at("tick_hz"))==300,"earth_scene_contract");
  auto s=scene.at("sample");m_=number(s.at("mass_kg"));r_=number(s.at("radius_m"));C_=number(s.at("heat_capacity_J_K"));cd_=number(s.at("drag_coefficient"));
  require(m_>0&&r_>0&&C_>0&&cd_>=0,"earth_sample_parameters");area_=pi*r_*r_;volume_=4*pi*r_*r_*r_/3;H_=number(s.at("heat_transfer_W_m2_K"))*4*area_;require(H_>=0,"earth_heat_coefficient");configure(scene.at("defaults"));
 }
 const J& config()const{return config_;}
 const Frame& frame()const{return frame_;}
 double radius()const{return r_;}double mass()const{return m_;}
 double timestep()const{return 1/300.;}
 void configure(const J& q){
  J c=config_.empty()?scene_.at("defaults"):config_;
  for(auto it=q.begin();it!=q.end();++it){require(c.contains(it.key()),"unknown_earth_environment_control");c[it.key()]=it.value();}
  double h=number(c.at("altitude_m")),s=number(c.at("slope_deg")),w=number(c.at("wind_m_s")),mu=number(c.at("friction"));
  require(h>=0&&h<=number(params_.at("atmosphere").at("max_altitude_m"))&&std::abs(s)<=20&&std::abs(w)<=10&&mu>=0&&mu<=1&&c.at("air").is_boolean(),"earth_environment_out_of_range");
  auto field=sample_earth(library_,params_,number(scene_.at("latitude_deg")),number(scene_.at("longitude_deg")),h,c.at("air").get<bool>());
  Frame f=field.frame;double g=field.gravity,tk=field.temperature,p=field.pressure,rho=field.density;
  double eff=g*(1-rho*volume_/m_);require(eff>0,"earth_sample_not_heavier_than_displaced_air");
  config_=c;frame_=f;g_=g;Tair_=tk;pair_=p;rho_=rho;geff_=eff;s*=pi/180;n_={-std::sin(s),std::cos(s),0};tangent_={std::cos(s),std::sin(s),0};
 }
 void reset(V position){
  for(double p:position)require(std::isfinite(p),"earth_reset_position");require(dot(position,n_)>=r_,"hand_below_ground");
  x=position;start_=x;v={};time=0;ticks=0;held=true;outside=false;temperature=T0_=number(scene_.at("sample").at("temperature0_K"));
  Wwind_=Wbuoy_=Ddrag_=Dcontact_=Dfriction_=Qair_=normal_impulse_=0;gravity_impulse_={};buoyancy_impulse_={};air_impulse_={};ground_impulse_={};E0_=energy();
 }
 void release(){require(held,"sample_not_held");held=false;E0_=energy();}
 void step(){
  if(held||outside)return;double dt=timestep();mechanics(dt);
  if(config_.at("air").get<bool>()){double next=Tair_+(temperature-Tair_)*std::exp(-H_*dt/C_);Qair_+=C_*(temperature-next);temperature=next;}
  ++ticks;time=ticks*dt;outside=std::abs(x[0])>number(scene_.at("patch_half_width_m"))||std::abs(x[2])>number(scene_.at("patch_half_width_m"));
  for(double p:x)require(std::isfinite(p),"earth_state_nonfinite");require(dot(x,n_)>=r_-1e-10,"earth_ground_penetration");
 }
 J status()const{
  auto env=config_;env["gravity_m_s2"]=g_;env["temperature_K"]=Tair_;env["pressure_Pa"]=pair_;env["density_kg_m3"]=rho_;
  V momentum_error=sub(mul(v,m_),add(add(gravity_impulse_,buoyancy_impulse_),add(air_impulse_,ground_impulse_)));
  return {{"held",held},{"phase",held?"held":outside?"out_of_patch":dot(x,n_)-r_<1e-9?"contact":"flight"},{"sim_time_s",time},{"ticks",ticks},{"environment",env},{"frame",frame_.json()},
   {"body",{{"position_m",x},{"velocity_m_s",v},{"mass_kg",m_},{"radius_m",r_},{"temperature_K",temperature},{"normal_force_N",normal_impulse_/timestep()}}},
   {"energy",{{"mechanical_J",energy()},{"initial_mechanical_J",E0_},{"wind_work_J",Wwind_},{"buoyancy_work_J",Wbuoy_},{"drag_dissipation_J",Ddrag_},{"contact_dissipation_J",Dcontact_},{"friction_dissipation_J",Dfriction_},{"balance_error_J",energy()-E0_-Wwind_-Wbuoy_+Ddrag_+Dcontact_+Dfriction_},{"heat_to_air_J",Qair_},{"thermal_energy_change_J",C_*(temperature-T0_)}}},
   {"exchange",{{"air_reaction_impulse_N_s",mul(add(air_impulse_,buoyancy_impulse_),-1)},{"ground_reaction_impulse_N_s",mul(ground_impulse_,-1)},{"ground_heat_J",Dcontact_+Dfriction_},{"air_heat_J",Qair_+Ddrag_},{"gravity_reaction_impulse_N_s",mul(gravity_impulse_,-1)},{"momentum_error_N_s",momentum_error}}}};
 }
};
} // namespace chimera::environment
