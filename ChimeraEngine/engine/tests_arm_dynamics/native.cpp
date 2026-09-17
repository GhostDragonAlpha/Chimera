#include "../arm_dynamics.hpp"
#include "../graph_earth.hpp"
#include <fstream>
#include <iostream>
using namespace chimera::environment;
int main(int argc,char**argv){try{
 require(argc==2,"usage_arm_native_scene");J b;std::ifstream(argv[1])>>b;auto data=b["arm_dynamics"];double g=9.7982854791873;J checks=J::array();auto check=[&](const char* name,bool yes,J detail=J::object()){checks.push_back({{"name",name},{"pass",yes},{"detail",detail}});};
 auto make=[&](){return ArmDynamics(data,g);};
 auto x=make();double before=x.q;x.configure({{"target_deg",140.},{"power",false},{"load_N",1.}});check("intent_does_not_write_pose",x.q==before&&x.w==0);
 for(int i=0;i<300;++i)x.step();auto s=x.status();check("power_off_falls_to_support",x.q<-.1&&std::abs(number(s["joint"]["angle_deg"])-80)<1e-7&&number(s["joint"]["support_reaction_N"])>1);
 check("passive_work_zero",s["energy"]["actuator_work_J"]==0.);
 double q=x.q; // Independent static virtual-work check uses compiled vectors.
 V a=data["parameters"]["axis"],r=data["parameters"]["hand_offset_m"],S=data["parameters"]["first_moment_kg_m"];
 auto rot=[&](V v){return add(add(mul(v,std::cos(q)),mul(cross(a,v),std::sin(q))),mul(a,dot(a,v)*(1-std::cos(q))));};
 double expected=g*cross(a,rot(S))[1]/cross(a,rot(r))[1]+1;
 check("static_support_from_virtual_work",std::abs(number(s["joint"]["support_reaction_N"])-expected)<1e-11,{{"expected_N",expected},{"measured_N",s["joint"]["support_reaction_N"]}});
 auto blocked=make();blocked.configure({{"target_deg",20.}});for(int i=0;i<600;++i)blocked.step();s=blocked.status();check("obstruction_stalls_with_reaction",std::abs(number(s["joint"]["angle_deg"])-80)<1e-7&&number(s["joint"]["support_reaction_N"])>1&&std::abs(number(s["joint"]["motor_torque_N_m"]))<=.3);
 auto weak=make();weak.configure({{"torque_limit_N_m",.03},{"target_deg",130.}});for(int i=0;i<1200;++i)weak.step();check("insufficient_torque_cannot_reach_target",number(weak.status()["joint"]["angle_deg"])<90);
 auto strong=make();strong.configure({{"target_deg",130.}});for(int i=0;i<900;++i)strong.step();check("stronger_drive_lifts_weight",number(strong.status()["joint"]["angle_deg"])>110);
 double maxResidual=0,minBattery=1,maxTorque=0;
 for(bool support:{false,true})for(double load:{0.,3.})for(double cap:{0.,.03,.3,.6}){
  auto t=make();t.configure({{"reset",true},{"support",support},{"load_N",load},{"torque_limit_N_m",cap},{"target_deg",140.}});
  for(int i=0;i<1200;++i){t.step();auto z=t.status();maxResidual=(std::max)(maxResidual,std::abs(number(z["energy"]["balance_error_J"])));maxResidual=(std::max)(maxResidual,std::abs(number(z["energy"]["store_balance_error_J"])));minBattery=(std::min)(minBattery,t.battery);maxTorque=(std::max)(maxTorque,std::abs(number(z["joint"]["motor_torque_N_m"]))-cap);}
 }
 check("16_scenario_energy_account",maxResidual<1e-10,{{"worst_J",maxResidual}});check("nonnegative_store",minBattery>=0);check("torque_never_exceeds_cap",maxTorque<=1e-14);
 auto tiny=data;tiny["recipe"]["battery_initial_J"]=1e-5;ArmDynamics empty(tiny,g);for(int i=0;i<1200;++i)empty.step();s=empty.status();check("named_energy_exhaustion",s["joint"]["battery_empty_events"]==1&&empty.battery<=1e-12&&empty.battery>=0);double work=s["energy"]["actuator_work_J"];for(int i=0;i<300;++i)empty.step();check("empty_store_no_later_active_work",empty.status()["energy"]["actuator_work_J"]==work);
 check("empty_store_reports_unusable",empty.status()["energy"]["battery_usable"]==false&&make().status()["energy"]["battery_usable"]==true);
 auto remainder=data;remainder["recipe"]["battery_initial_J"]=1e-13;ArmDynamics dust(remainder,g);for(int i=0;i<30;++i)dust.step();check("positive_remainder_is_not_available_work",dust.battery>0&&dust.status()["energy"]["battery_usable"]==false&&dust.status()["energy"]["actuator_work_J"]==0.);
 auto ideal=data;ideal["recipe"]["passive_decay_rate_s"]=0.;ideal["recipe"]["servo_damping_ratio"]=0.;ArmDynamics ballistic(ideal,0);ballistic.configure({{"reset",true},{"support",false},{"target_deg",140.},{"torque_limit_N_m",.03}});double I=data["parameters"]["inertia_kg_m2"];for(int i=0;i<30;++i)ballistic.step();check("constant_torque_analytic",std::abs(ballistic.q-.5*.03/I*.01)<1e-11&&std::abs(ballistic.w-.03/I*.1)<1e-11);
 double reference[4];int j=0;for(int n:{1,2,4,8}){ArmDynamics t(ideal,g,1/(300.*n));t.configure({{"reset",true},{"support",false},{"power",false}});for(int i=0;i<30*n;++i)t.step();reference[j++]=t.q;}
 double coarse=std::abs(reference[0]-reference[3]),fine=std::abs(reference[1]-reference[3]);check("second_order_time_refinement",coarse>fine*3.5&&coarse<fine*5,{{"coarse_error_rad",coarse},{"half_step_error_rad",fine}});
 auto old=strong.status();bool refused=false;try{strong.configure({{"support",false}});}catch(const std::exception&){refused=true;}check("support_requires_explicit_reset",refused&&strong.status()==old);
 refused=false;try{strong.configure({{"elbow_deg",20.}});}catch(const std::exception&){refused=true;}check("pose_write_refused",refused&&strong.status()==old);
 GraphEarth scene;scene.load(argv[1]);auto view=scene.render();check("native_force_scene_geometry",view.state["mode"]=="native_force_arm"&&view.indices.size()>18000);
 int failed=0;for(auto c:checks)if(!c["pass"].get<bool>())++failed;std::cout<<J({{"checks",checks},{"failed",failed}}).dump(2)<<"\n";return failed?1:0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
