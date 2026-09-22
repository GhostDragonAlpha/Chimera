// reflex_oracle.cpp -- TypeB PHASE-B observation oracle (reflex-core lane).
// NEW FILE, this lane only: consumes the COMMITTED gait_controller.hpp bytes
// through the PUBLIC API exclusively (angles/speeds/phase/configure/step) and
// dumps the per-tick observation stream the Python reflex layer replays:
//   OBS t=<tick> q0..q17 v0..v17 phi0 phi1
// The controller's own decision stream (the parity target) is produced by the
// header's GAIT_EVENT_TRACE instrumentation on stderr -- identical bytes to the
// ship build's. No engine file is modified. Command schedule (argv[4],
// "tick:vx,tick:vx" -- re-issue = repeat ticks) replays the typea adapter's
// declared channel through configure() exactly like cpu_probe.cpp.
// Trailer Agent: GLM 5.3.
#include "gait_controller.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
using namespace chimera::multibody;

static J load_json(const char* path){J j;std::ifstream f(path);if(!f)throw std::runtime_error("file open failed");f>>j;return j;}

int main(int argc,char**argv){
 try{
  if(argc<4){std::fprintf(stderr,"usage: reflex_oracle scene.json probe ticks [cmdspec]\n");return 2;}
  J scene=load_json(argv[1]);
  const J& data=scene.at("gait_controller");
  const J& recipe=data.at("recipe");
  const double dt=1.0/number(recipe.at("tick_hz"));
  const std::string probe=argv[2];
  int ticks=std::atoi(argv[3]);
  std::vector<std::pair<int,double>> cmds;
  if(argc>=5){std::string spec=argv[4];size_t p=0;
   while(p<spec.size()){size_t q=spec.find(',',p),r=spec.find(':',p);
    int tk=std::atoi(spec.substr(p,r-p).c_str());
    double vx=std::atof(spec.substr(r+1,(q==std::string::npos?spec.size():q)-r-1).c_str());
    cmds.push_back({tk,vx});if(q==std::string::npos)break;p=q+1;}}
  std::fprintf(stderr,"PROBE=%s ticks=%d\n",probe.c_str(),ticks);
  GaitWalker d(data,9.80665,V{0,0,0},dt);
  std::fprintf(stderr,"CONSTRUCTED\n");
  if(probe=="freefall")d.configure({{"power",false},{"contact_enabled",false},{"start_at_tables",false},{"reset",true}});
  if(probe=="stand")d.configure({{"gait_enabled",false},{"reset",true}});
  std::fprintf(stderr,"CONFIGURED\n");
  size_t nc=d.model().names.size();
  int cm=0;std::string refused="";int refused_tick=-1;
  for(int t=0;t<ticks;++t){
   if(cm<(int)cmds.size()&&cmds[cm].first==t){d.configure({{"commanded_target_velocity_x",cmds[cm].second}});++cm;}
   const Dense& q=d.angles();const Dense& v=d.speeds();
   std::printf("OBS t=%d",t);
   for(size_t i=0;i<nc;++i)std::printf(" %.17g",q[i]);
   for(size_t i=0;i<nc;++i)std::printf(" %.17g",v[i]);
   std::printf(" %.17g %.17g\n",d.phase(0),d.phase(1));
   std::fprintf(stderr,"PT t=%d\n",t); // the tick marker: every decision line
   // printed after it belongs to tick t (the controller stamps ticks_ = t).
   try{d.step();}catch(const Refusal&e){refused=e.what();refused_tick=t;break;}
  }
  std::printf("END refused=%s refused_tick=%d\n",refused.c_str(),refused_tick);
  return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"ERROR %s\n",e.what());return 1;}
}
