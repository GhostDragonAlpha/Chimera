#include "../earth_environment.hpp"
#include "../graph_earth.hpp"
#include <fstream>
#include <iostream>
using namespace chimera::environment;
int main(int argc,char**argv){try{
 require(argc==2,"usage_environment_native_scene_json");std::ifstream in(argv[1]);J b;in>>b;J checks=J::array();auto check=[&](std::string n,bool ok,J d=J::object()){checks.push_back({{"name",n},{"pass",ok},{"detail",d}});};
 auto make=[&](){return EarthTrial(b["models"],b["source_parameters"],b["scene"]);};
 chimera::forces::Library library(b["models"]);auto fields=sample_earth(library,b["source_parameters"],0,100,0);
 check("body_independent_field_sample",fields.density>1.2&&fields.density<1.3&&fields.pressure>101000&&fields.pressure<102000&&fields.temperature==288.19);
 auto frame=make_frame(b["source_parameters"]["datum"],35.6,139.7,321.);
 V small{.0012,.0023,-.0045};check("millimetre_global_local_roundtrip",norm(sub(frame.ecef_to_local(frame.local_to_ecef(small)),small))<2e-9);
 check("right_handed_frame",norm(sub(cross(frame.east,frame.up),frame.south))<1e-14&&std::abs(dot(frame.east,frame.up))<1e-14);
 auto vacuum=make();vacuum.configure({{"air",false}});vacuum.reset({0,1,0});vacuum.release();double g=vacuum.status()["environment"]["gravity_m_s2"];
 for(int i=0;i<60;++i)vacuum.step();check("vacuum_ballistic_position",std::abs(vacuum.x[1]-(1-.5*g*.2*.2))<2e-13);check("vacuum_ballistic_velocity",std::abs(vacuum.v[1]+g*.2)<2e-13);
 check("JPL_earth_gravity",g>9.79&&g<9.81);
 for(int i=0;i<900;++i)vacuum.step();auto vs=vacuum.status();check("unilateral_contact",std::abs(vacuum.x[1]-vacuum.radius())<1e-12&&norm(vacuum.v)==0);check("support_load_mg",std::abs(number(vs["body"]["normal_force_N"])-vacuum.mass()*g)<1e-14);
 check("vacuum_energy_account",std::abs(number(vs["energy"]["balance_error_J"]))<2e-14,vs["energy"]);
 double worstE=0,worstP=0,minLoss=0;
 for(double slope:{-20.,0.,20.})for(double wind:{-6.,0.,6.})for(double mu:{0.,.2,.8}){
  auto x=make();x.configure({{"slope_deg",slope},{"wind_m_s",wind},{"friction",mu}});x.reset({0,.4,0});x.release();
  for(int i=0;i<1200;++i){x.step();auto s=x.status();auto e=s["energy"];worstE=(std::max)(worstE,std::abs(number(e["balance_error_J"])));worstP=(std::max)(worstP,norm(s["exchange"]["momentum_error_N_s"].get<V>()));for(const char* k:{"drag_dissipation_J","friction_dissipation_J","contact_dissipation_J"})minLoss=(std::min)(minLoss,number(e[k]));}
 }
 check("27_scenario_energy_account",worstE<2e-12,{{"worst_J",worstE}});check("27_scenario_momentum_account",worstP<2e-12,{{"worst_N_s",worstP}});check("passive_losses_nonnegative",minLoss>=0);
 auto friction=make();friction.configure({{"air",false},{"slope_deg",20},{"friction",.4}});friction.reset({0,friction.radius()/std::cos(20*pi/180)+1e-12,0});friction.release();for(int i=0;i<600;++i)friction.step();check("above_static_threshold_holds",norm(friction.v)<1e-12&&std::abs(friction.x[0])<1e-8);
 friction.configure({{"friction",.1}});friction.reset({0,friction.radius()/std::cos(20*pi/180)+1e-12,0});friction.release();for(int i=0;i<60;++i)friction.step();check("below_static_threshold_slides",friction.v[0]<-.1);
 auto thermal=make();thermal.reset({0,.1,0});thermal.release();for(int i=0;i<3000;++i)thermal.step();auto s=thermal.status();double Ta=s["environment"]["temperature_K"],H=number(b["scene"]["sample"]["heat_transfer_W_m2_K"])*4*pi*thermal.radius()*thermal.radius(),C=b["scene"]["sample"]["heat_capacity_J_K"];
 check("thermal_exact_relaxation",std::abs(thermal.temperature-(Ta+(295-Ta)*std::exp(-H*thermal.time/C)))<1e-9);check("thermal_account",std::abs(number(s["energy"]["heat_to_air_J"])+number(s["energy"]["thermal_energy_change_J"]))<1e-12);check("thermal_no_overshoot",thermal.temperature>=Ta&&thermal.temperature<=295);
 auto high=make();double rho0=high.status()["environment"]["density_kg_m3"];high.configure({{"altitude_m",10000}});check("altitude_changes_fields",number(high.status()["environment"]["density_kg_m3"])<rho0/2&&number(high.status()["environment"]["gravity_m_s2"])<g);
 auto old=high.status();bool refused=false;try{high.configure({{"altitude_m",11000}});}catch(const std::exception&){refused=true;}check("unsupported_altitude_transactional",refused&&high.status()==old);
 GraphEarth graph;graph.load(argv[1]);auto view=graph.render();check("one_native_snapshot_finite",view.state["mode"]=="native_earth_patch"&&view.indices.size()>5384*3&&view.mesh.size()>2761*9);
 double sphereVolume=0;auto center=view.state["body"]["position_m"].get<V>();size_t sphereStart=5384*3+12*12*6+6;
 for(size_t i=sphereStart;i<view.indices.size();i+=3){auto at=[&](size_t j){uint32_t v=view.indices[j];return sub(V{view.mesh[9*v],view.mesh[9*v+1],view.mesh[9*v+2]},center);};sphereVolume+=dot(at(i),cross(at(i+1),at(i+2)))/6;}
 double exactVolume=4*pi*std::pow(number(view.state["body"]["radius_m"]),3)/3;check("display_sphere_outward_with_bounded_tessellation",sphereVolume>0&&sphereVolume/exactVolume>.95&&sphereVolume/exactVolume<=1.00001,{{"display_to_analytic_volume",sphereVolume/exactVolume}});
 auto before=graph.status();refused=false;try{graph.control({{"wind_m_s",20}});}catch(const std::exception&){refused=true;}check("invalid_control_transactional",refused&&graph.status()==before);
 graph.control({{"elbow_deg",20}});auto after=graph.status();check("hand_port_follows_source_arm",norm(sub(after["body"]["position_m"].get<V>(),before["body"]["position_m"].get<V>()))>.01);
 int failed=0;for(auto c:checks)if(!c["pass"].get<bool>())++failed;std::cout<<J({{"checks",checks},{"failed",failed}}).dump(2)<<"\n";return failed?1:0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}}
