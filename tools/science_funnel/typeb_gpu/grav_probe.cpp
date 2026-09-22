// grav_probe.cpp -- is the C++ generalized gravity on the joint rows ZERO at
// the defaults pose (where the kernels produce nonzero), and does the true
// -d(potential)/dq agree with e.gravity? Prints e.gravity, e.bias at defaults
// and finite-difference checks. Trailer Agent: GLM 5.3.
#include "gait_controller.hpp"
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
  const Model& m=d.model();
  size_t n=m.names.size();
  Dense q=m.defaults;Dense Densev(n,0.);
  auto e=m.evaluate(q,Densev,V{0,-9.80665,0});
  std::printf("== e.gravity at defaults ==\n");
  for(size_t i=0;i<n;++i)std::printf("  g[%zu] %-28s %.17g\n",i,m.names[i].c_str(),e.gravity[i]);
  std::printf("== e.bias at defaults ==\n");
  for(size_t i=0;i<n;++i)std::printf("  b[%zu] %-28s %.17g\n",i,m.names[i].c_str(),e.bias[i]);
  std::printf("== model limits ==\n");
  for(size_t i=0;i<n;++i)std::printf("  q[%zu] %-28s lower=%.17g upper=%.17g\n",i,m.names[i].c_str(),m.lower[i],m.upper[i]);
  // finite-difference the potential: true generalized gravity = -dV/dq
  std::printf("== -d(potential)/dq (central diff h=1e-6) ==\n");
  for(size_t i=6;i<n;++i){
   Dense qp=q,qm=q;qp[i]+=1e-6;qm[i]-=1e-6;
   auto ep=m.evaluate(qp,Densev,V{0,-9.80665,0});
   auto em=m.evaluate(qm,Densev,V{0,-9.80665,0});
   double gfd=-(ep.potential-em.potential)/2e-6;
   std::printf("  q[%zu] %-28s fd=%.17g  eval=%.17g\n",i,m.names[i].c_str(),gfd,e.gravity[i]);
  }
  return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"ERROR %s\n",e.what());return 1;}
}
