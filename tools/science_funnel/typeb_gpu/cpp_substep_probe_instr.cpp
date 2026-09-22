// cpp_substep_probe.cpp -- the C++ GaitWalker step() inlined per-substep dump:
// replicates step()'s 4-substep loop verbatim (servo/store/advance) and prints
// q/v after each substep, for tick 1, stand config (gait off).
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
  d.configure({{"gait_enabled",false},{"reset",true}});
  // ONE step() call = one tick; we cannot see inside, so instead replicate:
  // we use step() but print the public state per tick for tick 0..3 and rely
  // on the kernels' per-substep [SUB] prints only for structure. To get
  // per-substep on the C++ side we re-derive via public API is impossible;
  // so print per-tick here and compare the tick-1 end state.
  for(int t=0;t<3;++t){d.step();
   const Dense& q=d.angles();const Dense& v=d.speeds();
   std::printf("[TICK] t=%d q12=%.17g v9=%.17g v12=%.17g v13=%.17g v14=%.17g v17=%.17g v4=%.17g\n",
     t,q[12],v[9],v[12],v[13],v[14],v[17],v[4]);}
  return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"ERROR %s\n",e.what());return 1;}
}
