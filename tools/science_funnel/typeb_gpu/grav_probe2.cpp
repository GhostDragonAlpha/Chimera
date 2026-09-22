// grav_probe2.cpp -- the C++ rhs at the CAPTURE state: e.gravity - e.bias
// - damping*v, solved through inverse_spd. Compares the C++ bias machinery
// against the kernels' rate and the numpy replica. Trailer Agent: GLM 5.3.
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
  Dense q=d.angles(),v=d.speeds();
  auto e=m.evaluate(q,v,V{0,-9.80665,0});
  Dense rhs=e.gravity; for(size_t i=0;i<n;++i)rhs[i]-=e.bias[i];
  // passive damping on the drive rows (scene viscous_damping_N_m_s_rad)
  const J& dj=recipe.at("drives");
  for(const auto& dr:dj){
   const std::string& cn=dr.at("coordinate").get<std::string>();
   double dmp=number(dr.at("viscous_damping_N_m_s_rad"));
   for(size_t i=0;i<n;++i)if(m.names[i]==cn)rhs[i]-=dmp*v[i];}
  std::printf("== capture-state rhs (gravity-bias-damping*v) ==\n");
  for(size_t i=0;i<n;++i)std::printf("  r[%zu] %-28s %.17g\n",i,m.names[i].c_str(),rhs[i]);
  std::printf("== e.bias ==\n");
  for(size_t i=0;i<n;++i)std::printf("  b[%zu] %-28s %.17g\n",i,m.names[i].c_str(),e.bias[i]);
  auto inv=inverse_spd(e.mass,n);
  auto acc=multiply(inv,rhs);
  std::printf("== acc ==\n");
  for(size_t i=0;i<n;++i)std::printf("  a[%zu] %-28s %.17g\n",i,m.names[i].c_str(),acc[i]);
  return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"ERROR %s\n",e.what());return 1;}
}
