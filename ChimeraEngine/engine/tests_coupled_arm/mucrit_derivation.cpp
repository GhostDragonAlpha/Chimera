// Recreated derivation of the critical Coulomb coefficient at the settled
// press pose (review F2, 2026-09-17). Method inherited from the published
// slice's .tmp/mucrit_debug.cpp, rebuilt from its frozen numbers
// (settle mu_crit 0.7820104343, descent peak 0.7848445602, mu=0.6: 2253
// slide ticks / 15 mm travel / 2.5x heat):
//   * press trial = contact on, targets 20 deg/20 deg, 6000 ticks from reset;
//   * a trial SETTLES when every one of its final 600 ticks has hand slip
//     speed below 1e-9 m/s (the same readout the native suite asserts);
//   * bisect mu on that predicate -> mu_crit(settle);
//   * descent peak = max over touching ticks of the DEMANDED stick ratio
//     |t|/n (the uncapped joint solve), sampled at post-tick states during
//     the landing phase;
//   * divergence stats at mu=0.6 and the hold stats at mu=0.8.
// Usage: mucrit_derivation.exe scene.json > mucrit.json
#include "../../native/viewer3rd/json.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

#define private public
#define class struct
#include "../coupled_dynamics.hpp"
#undef class
#undef private

using namespace chimera::multibody;

struct Trial {bool settles=true;long long slide_ticks=0,stick_ticks=0;double travel=0,heat=0;};

static Trial press_trial(const J& data,V shift,double mu){
 CoupledDynamics d(data,9.81,shift);
 d.configure({{"contact_enabled",true},{"reset",true},{"contact_friction",mu},{"shoulder_target_deg",20.},{"elbow_target_deg",20.}});
 Trial out;double last=NAN;
 for(int i=0;i<6000;++i){d.step();auto s=d.status();
  std::string mode=s["contact"]["mode"];
  if(mode=="slide")++out.slide_ticks;else if(mode=="stick")++out.stick_ticks;
  auto pos=s["body"]["position_m"];double planar=std::hypot(number(pos[0]),number(pos[2]));
  if(!std::isnan(last))out.travel+=std::abs(planar-last);last=planar;
  if(i>=5400&&number(s["contact"]["slip_speed_m_s"])>=1e-9)out.settles=false;}
 out.heat=number(d.status()["energy"]["friction_heat_J"]);
 return out;
}

// Demanded stick ratio |t|/n at the post-tick state, reconstructed through
// the seam from the same pieces rate() uses (free accel, contact row, floors).
static double demanded_ratio(const CoupledDynamics& d){
 const auto& s=d.s_;auto e=d.evaluate(s);
 if(e.point(d.hand_,d.local_).first[1]+d.radius_-d.plane_model_y_>d.kTouch)return 0;
 auto inv=inverse_spd(e.mass,2);
 auto ext=e.force(d.hand_,d.local_,V{0,-number(d.config_["load_N"]),0});
 Dense tau=d.torque(),rhs(2);
 for(int k=0;k<2;++k)rhs[k]=tau[k]+e.gravity[k]-e.bias[k]+ext[k]-d.damping_[k]*s.v[k];
 auto free=multiply(inv,rhs);
 auto row=d.contact_row(e);auto [row_t,slip,tangent]=d.friction_row(e,s.v,free);
 if(!row_t[0]&&!row_t[1])return 0;
 V bias=vector(e.frames[d.hand_].ddt,d.local_,1);
 double floor_n=-d.contact_bias(e),floor_t=-dot(tangent,V{bias[0],0,bias[2]});
 auto in=multiply(inv,row),it=multiply(inv,row_t);
 double A=inner(row,in),B=inner(row,it),C=inner(row_t,it);
 double rn=-(inner(row,free)-floor_n),rt=-(inner(row_t,free)-floor_t),det=A*C-B*B;
 if(det<=1e-18)return 0;
 double n=(rn*C-rt*B)/det,t=(rt*A-rn*B)/det;
 return n>1e-9?std::abs(t)/n:0;
}

int main(int argc,char** argv){try{
 require(argc==2,"usage_scene");J scene;std::ifstream(argv[1])>>scene;
 J data=scene.at("coupled_dynamics");V shift=scene.at("scene").at("arm_translation_m").get<V>();

 // Settle bisection: lo slides, hi settles.
 double lo=0,hi=1;
 for(int i=0;i<50;++i){double mid=(lo+hi)/2;if(press_trial(data,shift,mid).settles)hi=mid;else lo=mid;}
 double mu_crit=hi;

 // Descent-peak demanded ratio: mu=1 hold run, sample every tick, report the
 // landing-phase (first 600 ticks) and whole-trial maxima separately.
 CoupledDynamics d(data,9.81,shift);
 d.configure({{"contact_enabled",true},{"reset",true},{"contact_friction",1.},{"shoulder_target_deg",20.},{"elbow_target_deg",20.}});
 double peak_descent=0,peak_all=0;
 for(int i=0;i<6000;++i){d.step();double r=demanded_ratio(d);
  peak_all=(std::max)(peak_all,r);if(i<600)peak_descent=(std::max)(peak_descent,r);}

 Trial high=press_trial(data,shift,.8),low=press_trial(data,shift,.6);
 std::cout<<J({{"scene",argv[1]},{"predicate","press targets 20/20, 6000 ticks, settle = slip<1e-9 m/s on every one of the final 600 ticks"},
  {"mu_crit_settle_bisection",mu_crit},{"frozen_mu_crit_settle",0.7820104343},{"frozen_descent_peak",0.7848445602},
  {"descent_peak_demand_first_600_ticks",peak_descent},{"whole_trial_peak_demand",peak_all},
  {"mu_0_8",{{"settles",high.settles},{"slide_ticks",high.slide_ticks},{"stick_ticks",high.stick_ticks},{"travel_m",high.travel},{"friction_heat_J",high.heat}}},
  {"mu_0_6",{{"settles",low.settles},{"slide_ticks",low.slide_ticks},{"stick_ticks",low.stick_ticks},{"travel_m",low.travel},{"friction_heat_J",low.heat}}},
  {"heat_ratio_0_6_over_0_8",low.heat/high.heat}}).dump(2)<<"\n";
 return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
