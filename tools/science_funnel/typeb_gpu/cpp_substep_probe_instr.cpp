// cpp_substep_probe.cpp -- the C++ GaitWalker per-substep dump drill: runs the
// NOMINAL WALK config (default configure, exactly like cpu_probe walk) and
// lets gait_controller_instr.hpp print the per-substep SUBFULL state lines
// during tick 1 (ticks_==0), matching probe_kernels.cuh's SUBFULL format so
// diff_trace.py can align the two at substep granularity.
// Trailer Agent: GLM 5.3.
#include "gait_controller_instr.hpp"
#include <cstdio>
#include <fstream>
using namespace chimera::multibody;
static J load_json(const char* path){J j;std::ifstream f(path);if(!f)throw std::runtime_error("open failed");f>>j;return j;}
int main(int argc,char**argv){
 try{
  J scene=load_json(argv[1]);
  const J& data=scene.at("gait_controller");
  const J& recipe=data.at("recipe");
  const double dt=1.0/number(recipe.at("tick_hz"));
  GaitWalker d(data,9.80665,V{0,0,0},dt);
  // default config == cpu_probe "walk" (the nominal walk the shim mirrors);
  // SUBFULL per-substep prints fire inside step() while ticks_==0.
  for (int s = 0; s < 5; ++s) d.step(); // ticks 1..5 (the drill window t=0..4)
  return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"ERROR %s\n",e.what());return 1;}
}
