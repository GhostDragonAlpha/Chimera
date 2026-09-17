#include "../coupled_dynamics.hpp"
#include "../graph_earth.hpp"
#include <fstream>
#include <iostream>
using namespace chimera::multibody;
int main(int argc,char**argv){try{
 require(argc==3,"usage_scene_and_reference_cases");J scene,cases;std::ifstream(argv[1])>>scene;std::ifstream(argv[2])>>cases;Model m(scene.at("coupled_dynamics").at("model"));double worst=0;size_t count=0;
 auto compare=[&](double a,double b){worst=(std::max)(worst,std::abs(a-b));require(std::abs(a-b)<2e-9,"native_reference_mismatch");++count;};
 for(auto c:cases.at("cases")){Dense q,v;for(auto n:m.names){q.push_back(number(c["angles_rad"][n]));v.push_back(c["rates_rad_s"].value(n,0.));}auto ref=c["reference"];auto e=m.evaluate(q,v,ref["gravity_m_s2"].get<V>());size_t n=m.names.size();for(size_t i=0;i<n;++i){compare(e.gravity[i],ref["gravity_force_N_m"][i]);compare(e.bias[i],ref["bias_force_N_m"][i]);for(size_t j=0;j<n;++j)compare(e.mass[i*n+j],ref["mass_matrix"][i][j]);}compare(e.potential,ref["potential_J"]);auto point=e.point(m.body("hand"),c["hand_local_point_m"].get<V>());auto force=e.force(m.body("hand"),c["hand_local_point_m"].get<V>(),c["force_world_N"].get<V>());auto acc=e.acceleration(force);for(int k=0;k<3;++k){compare(point.first[k],c["hand_world_point_m"][k]);for(size_t i=0;i<n;++i)compare(point.second[i][k],c["hand_jacobian_m_per_rad"][k][i]);}for(size_t i=0;i<n;++i){compare(force[i],c["point_generalized_force_N_m"][i]);compare(acc[i],c["unconstrained_acceleration_rad_s2"][i]);}}

 J data=scene.at("coupled_dynamics"),runs=J::array();double residual=0;int checks=0;
 auto ck=[&](bool ok,const char* message){require(ok,message);++checks;};
 std::vector<J> configs={J{{"power",false}},J::object(),J{{"shoulder_drive",false}},J{{"elbow_drive",false}},J{{"load_N",3.}},J{{"shoulder_target_deg",-75.},{"elbow_target_deg",20.}},J{{"shoulder_target_deg",90.},{"elbow_target_deg",140.},{"shoulder_torque_limit_N_m",1.},{"elbow_torque_limit_N_m",.6}}};
 V shift=scene.at("scene").at("arm_translation_m").get<V>();
 for(size_t n=0;n<configs.size();++n){CoupledDynamics d(data,9.7982854791873,shift);if(!configs[n].empty())d.configure(configs[n]);double peak=0;
  for(int i=0;i<3000;++i){d.step();auto s=d.status();for(const char* key:{"balance_error_J","store_balance_error_J"})peak=(std::max)(peak,std::abs(number(s["energy"][key])));ck(number(s["energy"]["battery_J"])>=0,"store_negative");for(auto j:s["joints"])ck(std::abs(number(j["motor_torque_N_m"]))<=number(j["torque_limit_N_m"])+1e-12,"torque_cap");}
  std::cerr<<"trial "<<n<<" residual "<<peak<<"\n";ck(peak<1e-5,"ten_second_energy_residual");residual=(std::max)(residual,peak);auto final=d.status();if(n==0)ck(number(final["energy"]["actuator_work_J"])==0,"passive_work");runs.push_back({{"input",configs[n]},{"peak_residual_J",peak},{"final",final}});
 }
 CoupledDynamics intent(data,9.81,shift);auto before=intent.status();intent.configure({{"shoulder_target_deg",-40.},{"elbow_target_deg",40.}});ck(intent.angles()==intent.model().defaults&&intent.speeds()==Dense(2),"intent_changed_pose");auto saved=intent.status();bool refused=false;try{intent.configure({{"load_N",1.},{"angles",J::array({0,0})}});}catch(const Refusal&){refused=true;}ck(refused&&intent.status()==saved,"transactional_refusal");
 auto tiny=data;tiny["recipe"]["battery_initial_J"]=1e-5;CoupledDynamics empty(tiny,9.81,shift);for(int i=0;i<300;++i)empty.step();auto exhausted=empty.status();ck(exhausted["battery_empty_events"]==1&&!exhausted["energy"]["battery_usable"].get<bool>(),"exhaustion_event");double exhausted_work=number(exhausted["energy"]["actuator_work_J"]);for(int i=0;i<300;++i)empty.step();ck(empty.status()["energy"]["actuator_work_J"]==exhausted_work,"exhausted_motor_work");
 CoupledDynamics free(data,0,shift),driven(data,0,shift);free.configure({{"power",false}});driven.configure({{"elbow_drive",false}});free.step();driven.step();ck(std::abs(driven.speeds()[1]-free.speeds()[1])>1e-4,"cross_joint_coupling");
 std::vector<Dense> fine;for(int multiple:{1,2,4,8}){CoupledDynamics d(data,9.81,shift,1./(300*multiple));d.configure({{"power",false}});for(int i=0;i<24*multiple;++i)d.step();Dense x=d.angles();auto v=d.speeds();x.insert(x.end(),v.begin(),v.end());fine.push_back(x);}
 auto distance=[](const Dense&a,const Dense&b){double x=0;for(size_t i=0;i<a.size();++i)x+=(a[i]-b[i])*(a[i]-b[i]);return std::sqrt(x);};double ratio=distance(fine[0],fine[1])/distance(fine[1],fine[2]);ck(ratio>12&&ratio<20,"rk4_refinement");
 // Disabled-contact determinism: two identical passive runs agree bit-for-bit.
 CoupledDynamics control_a(data,9.81,shift),control_b(data,9.81,shift);control_a.configure({{"power",false}});control_b.configure({{"power",false}});
 for(int i=0;i<3000;++i){control_a.step();control_b.step();}ck(control_a.angles()==control_b.angles()&&control_a.speeds()==control_b.speeds(),"free_control_deterministic");

 // Contact Jacobian consistency: J_n equals finite differences of the same model's
 // FK gap at several reached poses, and the row really varies with the shoulder.
 V point=scene.at("coupled_dynamics").at("recipe").at("hand_point_m").get<V>();double plane=number(scene.at("coupled_dynamics").at("recipe").at("contact_plane_height_m"))-shift[1];
 auto fk_gap=[&](const Dense& q){auto e=control_a.model().evaluate(q,Dense(2),V{0,-9.81,0});return e.point(control_a.model().body("hand"),point).first[1]+number(scene.at("coupled_dynamics").at("recipe").at("proxy_radius_m"))-plane;};
 double eps=1e-6;std::vector<Dense> rows_seen;
 for(double target:{-40.,0.,35.}){CoupledDynamics d(data,9.81,shift);d.configure({{"contact_enabled",true},{"reset",true},{"shoulder_target_deg",target},{"elbow_target_deg",110.}});
  for(int i=0;i<900;++i)d.step();auto s=d.status();auto row=s["contact"]["jacobian_m_per_rad"];Dense q=d.angles();
  double fd0=(fk_gap(Dense{q[0]+eps,q[1]})-fk_gap(Dense{q[0]-eps,q[1]}))/(2*eps),fd1=(fk_gap(Dense{q[0],q[1]+eps})-fk_gap(Dense{q[0],q[1]-eps}))/(2*eps);
  ck(std::abs(fd0-number(row[0]))<1e-6&&std::abs(fd1-number(row[1]))<1e-6,"contact_jacobian_consistency");
  rows_seen.push_back(Dense{number(row[0]),number(row[1])});}
 ck(std::abs(rows_seen[0][0]-rows_seen[2][0])>1e-6||std::abs(rows_seen[0][1]-rows_seen[2][1])>1e-6,"contact_geometry_moves_with_shoulder");

 // Obstructed target: press the plane, measure reaction and stall, never teleport.
 // The three frozen metrics are the qualified frictionless receipt values: the
 // mu=0 default must reproduce candidate 8e010738 bit-exactly.
 double worst_gap=1,peak_reaction=0;{CoupledDynamics d(data,9.81,shift);d.configure({{"contact_enabled",true},{"reset",true},{"shoulder_target_deg",20.},{"elbow_target_deg",20.}});
  for(int i=0;i<6000;++i){d.step();auto s=d.status();double g=number(s["contact"]["gap_m"]),r=number(s["contact"]["reaction_N"]);worst_gap=(std::min)(worst_gap,g);peak_reaction=(std::max)(peak_reaction,r);
   ck(g>=-1e-5,"contact_no_pass_through");ck(r>=-1e-9,"contact_reaction_nonnegative");ck(std::abs(number(s["energy"]["balance_error_J"]))<1e-5&&std::abs(number(s["energy"]["store_balance_error_J"]))<1e-5,"contact_balance");}
  auto s=d.status();ck(worst_gap<1e-5,"contact_actually_touched");ck(peak_reaction>0.05,"contact_reaction_bears_load");ck(number(s["joints"][1]["angle_deg"])>30.,"contact_target_obstructed");
  ck(worst_gap==4.147475858029548e-07&&peak_reaction==2.5894018617259906,"frictionless_slice_bit_exact");}

 // Power-cut drop: the fall is absorbed inelastically without creating energy.
 // The frozen heat value is the qualified frictionless receipt's drop impact heat.
 double contact_heat=0;{CoupledDynamics d(data,9.81,shift);d.configure({{"contact_enabled",true},{"reset",true},{"power",false}});
  for(int i=0;i<6000;++i){d.step();auto s=d.status();ck(number(s["contact"]["gap_m"])>=-1e-5,"contact_drop_no_pass_through");ck(number(s["contact"]["reaction_N"])>=-1e-9,"contact_drop_nonnegative");contact_heat=(std::max)(contact_heat,number(s["energy"]["contact_impact_heat_J"]));ck(number(s["energy"]["actuator_work_J"])==0,"contact_passive_no_work");}
  auto s=d.status();ck(contact_heat>0,"contact_impact_dissipated");ck(contact_heat==0.06656390658451124,"frictionless_drop_bit_exact");ck(std::abs(number(s["energy"]["balance_error_J"]))<1e-5&&std::abs(number(s["energy"]["store_balance_error_J"]))<1e-5,"contact_drop_balance");ck(number(s["contact"]["gap_m"])>=-1e-5&&std::abs(number(s["joints"][1]["speed_rad_s"]))<.05,"contact_settles_on_plane");}

 // Coulomb friction: cone and no-adhesion every tick, dissipation grows with mu,
 // the landed arm ends held (stick) with the plane horizontal so only friction
 // brakes the landing slip; mu=0 shows no tangential force at all.
 double heat_low=0,heat_high=0;long long stick_low=0;{CoupledDynamics zero(data,9.81,shift);zero.configure({{"contact_enabled",true},{"reset",true},{"contact_friction",0.},{"shoulder_target_deg",20.},{"elbow_target_deg",20.}});
  for(int i=0;i<300;++i){zero.step();auto s=zero.status();ck(number(s["contact"]["friction_force_N"])==0&&number(s["energy"]["friction_heat_J"])==0,"friction_zero_mu_inert");}
  for(double mu:{0.05,0.8}){CoupledDynamics d(data,9.81,shift);d.configure({{"contact_enabled",true},{"reset",true},{"contact_friction",mu},{"shoulder_target_deg",20.},{"elbow_target_deg",20.}});long long stick=0;double settled_bal=0;bool settled=false;
   for(int i=0;i<6000;++i){d.step();auto s=d.status();
    double fn=number(s["contact"]["reaction_N"]),ft=std::abs(number(s["contact"]["friction_force_N"])),bal=std::abs(number(s["energy"]["balance_error_J"])),store=std::abs(number(s["energy"]["store_balance_error_J"]));
    ck(ft<=mu*fn+1e-9,"friction_cone");ck(fn>1e-9||ft<1e-12,"friction_no_pull_without_load");
    // Review F3: the impact-level cone, guarded every tick. Whenever a
    // friction landing impulse exists it is bounded by mu times the normal
    // landing impulse (previously held by construction, never asserted).
    double fi=number(s["contact"]["friction_impact_impulse_N_s"]),ni=number(s["contact"]["impact_impulse_N_s"]);
    if(fi>1e-15)ck(fi<=mu*ni+1e-9,"friction_impact_cone");
    ck(number(s["energy"]["friction_heat_J"])>=-1e-12,"friction_heat_nonnegative");
    // Preregistered: one-time catch-event allowance <= 5e-5 J; below 1e-5 J
    // thereafter with no sustained drift (amendment recorded in the graph).
    ck(bal<5e-5&&store<5e-5,"friction_balance_allowance");
    if(i==600){settled=true;settled_bal=(std::max)(bal,store);}
    if(settled)ck(bal<settled_bal+1e-5&&store<settled_bal+1e-5,"friction_balance_no_drift");
    if(s["contact"]["mode"]=="stick")++stick;}
   auto s=d.status();ck(number(s["energy"]["friction_heat_J"])>0,"friction_dissipated");
   // On a horizontal plane a fully settled static pose has no impending slip, so
   // the terminal mode may be free; stick must have been observed while holding.
   ck(std::abs(d.speeds()[0])<.02&&std::abs(d.speeds()[1])<.02&&number(s["contact"]["gap_m"])>=-1e-5,"friction_lands_settled");
   ck(stick>0,"friction_stick_observed");
   if(mu<0.5){heat_low=number(s["energy"]["friction_heat_J"]);stick_low=stick;}else heat_high=number(s["energy"]["friction_heat_J"]);}}
 ck(heat_high>heat_low&&heat_low>0,"friction_more_mu_more_heat");
 // The coefficient is a live control: accepted without reset, echoed in status.
 {CoupledDynamics d(data,9.81,shift);d.configure({{"contact_enabled",true},{"reset",true}});d.step();d.configure({{"contact_friction",.4}});auto s=d.status();ck(number(s["config"]["contact_friction"])==.4&&number(s["contact"]["friction_mu"])==.4,"friction_live_control");bool refused=false;try{d.configure({{"contact_friction",1.5}});}catch(const Refusal&){refused=true;}ck(refused,"friction_range_refused");}

 // Review F2: the derived critical-mu hold-vs-slide pair (the deferred
 // falsifier of the qualified slice). The critical coefficient at the
 // settled press pose (targets 20/20) is mu_crit=0.7820104343 by settle
 // bisection, descent peak demand 0.7848445602 (derivation recreated in
 // tests_coupled_arm/mucrit_derivation.cpp, output archived in the fixes
 // receipt). mu=0.8 sits above the boundary and must end held: sub-threshold
 // slip on every one of the final 600 ticks. mu=0.6 sits below it and must
 // keep sliding: measurable tangential travel and strictly more friction
 // heat than the held trial. If both held or both slid, no derived critical
 // mu would exist and this falsifier would fail.
 double heat_hold=0,heat_slide=0,slide_travel=0;bool held=false;
  for(double mu:{0.8,0.6}){CoupledDynamics d(data,9.81,shift);d.configure({{"contact_enabled",true},{"reset",true},{"contact_friction",mu},{"shoulder_target_deg",20.},{"elbow_target_deg",20.}});
   double last=NAN,travel_mu=0;bool settle_window=true;
   for(int i=0;i<6000;++i){d.step();auto s=d.status();
    double fi=number(s["contact"]["friction_impact_impulse_N_s"]),ni=number(s["contact"]["impact_impulse_N_s"]);
    if(fi>1e-15)ck(fi<=mu*ni+1e-9,"friction_impact_cone");
    double slip=number(s["contact"]["slip_speed_m_s"]);
    if(i>=5400)settle_window=settle_window&&slip<1e-9;
    auto pos=s["body"]["position_m"];double planar=std::hypot(number(pos[0]),number(pos[2]));
    if(!std::isnan(last))travel_mu+=std::abs(planar-last);last=planar;}
   double heat=number(d.status()["energy"]["friction_heat_J"]);
   if(mu>0.7){held=settle_window;heat_hold=heat;ck(settle_window,"mucrit_high_mu_holds_tail");}
   else{heat_slide=heat;slide_travel=travel_mu;ck(travel_mu>1e-3,"mucrit_low_mu_slides_travel");ck(heat>heat_hold,"mucrit_low_mu_more_heat");}}
  ck(held,"mucrit_pair_separates_hold_from_slide");


 GraphEarth graph;graph.load(argv[1]);auto graph_status=graph.status();ck(graph_status["mode"]=="native_coupled_arm"&&!graph_status.contains("elbow_deg"),"coupled_coordinate_schema");ck(graph_status["contacts"]["environment"]==false,"free_mode_default_off");graph.control({{"paused",true}});auto g0=graph.status();graph.control({{"shoulder_target_deg",60.},{"elbow_target_deg",130.}});auto g1=graph.status();for(int i=0;i<2;++i){ck(g0["joints"][i]["angle_deg"]==g1["joints"][i]["angle_deg"],"graph_intent_angle");ck(g0["joints"][i]["speed_rad_s"]==g1["joints"][i]["speed_rad_s"],"graph_intent_speed");}
 size_t triangles_free=number(graph.render().state.at("mesh_triangles"));
 auto saved_status=graph.status();bool toggle_refused=false;
 try{graph.control({{"contact_enabled",true}});}catch(const std::exception&){toggle_refused=true;}
 ck(toggle_refused&&graph.status()==saved_status,"contact_toggle_requires_reset");
 graph.control({{"contact_enabled",true},{"reset",true}});auto enabled=graph.status();
 ck(enabled["contact"]["enabled"].get<bool>()&&enabled["contacts"]["environment"].get<bool>()&&enabled["config"]["contact_enabled"].get<bool>()&&enabled["contact"]["friction"]==false&&enabled["contact"]["grasp"]==false,"contact_mode_engaged");
 ck(std::isfinite(number(enabled["contact"]["gap_m"]))&&number(enabled["contact"]["plane_world_up_m"])==number(scene.at("coupled_dynamics").at("recipe").at("contact_plane_height_m")),"contact_plane_recipe_agreement");
 auto plane_render=graph.render();ck(number(plane_render.state.at("mesh_triangles"))>=triangles_free+6,"contact_plane_rendered");

 std::cout<<J({{"reference_cases",cases["cases"].size()},{"scalar_comparisons",count},{"worst_absolute_error",worst},{"dynamics_checks",checks},{"peak_energy_residual_J",residual},{"free_refinement_ratio",ratio},{"trials",runs},{"exhaustion",empty.status()},{"contact",{{"worst_gap_m",worst_gap},{"peak_reaction_N",peak_reaction},{"impact_heat_J",contact_heat}}},{"friction",{{"heat_low_mu_J",heat_low},{"heat_high_mu_J",heat_high},{"stick_ticks_low_mu",stick_low}}},{"mucrit_pair",{{"heat_hold_J",heat_hold},{"heat_slide_J",heat_slide},{"slide_travel_m",slide_travel},{"held",held}}},{"pass",true}}).dump(2)<<"\n";
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
