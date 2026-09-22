// cpu_probe.cpp -- the FULL-BODY GPU PORT lane's CPU-reference probe harness.
// Links the in-tree GaitWalker (agent/typea-command-adapter-20260921 bytes,
// ZERO engine modifications) and dumps the reference data the Warp port is
// validated against:
//   probe=diag     -> the defaults-pose mass diagonal (the PD-gain anchor)
//   probe=reset    -> the reset state (q, v, phases)
//   probe=freefall -> 120 ticks, power off, contact off (F-G5 pattern)
//   probe=stand    -> 60 ticks, gait_enabled false (the stage-E stand)
//   probe=walk     -> N ticks uncommanded (or tick:vx command schedule)
//                      per-tick: tick,q3,q4,q2,v3,phiL,phiR,touchL,touchR,
//                                bat_total,hind_fires_l,hind_fires_r,
//                                fore_mode_l,fore_mode_r,refused_class
// Usage: cpu_probe <scene.json> <probe> [arg]
//   walk arg: tick count (default 600) or "ticks/tick:vx,tick:vx..."
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
  if(argc<3){std::fprintf(stderr,"usage: cpu_probe scene.json probe [arg]\n");return 2;}
  J scene=load_json(argv[1]);
  const J& data=scene.at("gait_controller");
  const J& recipe=data.at("recipe");
  const double dt=1.0/number(recipe.at("tick_hz"));
  const std::string probe=argv[2];
  if(probe=="diag"){
   GaitWalker d(data,9.80665,V{0,0,0},dt);
   const Model& m=d.model();
   auto e=m.evaluate(m.defaults,std::vector<double>(m.names.size(),0.),V{0,-9.80665,0});
   for(size_t i=0;i<m.names.size();++i)
    std::printf("%zu %s %.17g\n",i,m.names[i].c_str(),e.mass[i*m.names.size()+i]);
   return 0;
  }
  if(probe=="reset"){
   GaitWalker d(data,9.80665,V{0,0,0},dt);
   const Dense& q=d.angles();const Dense& v=d.speeds();
   for(size_t i=0;i<q.size();++i)std::printf("q %zu %.17g\n",i,q[i]);
   for(size_t i=0;i<v.size();++i)std::printf("v %zu %.17g\n",i,v[i]);
   std::printf("phi %.17g %.17g\n",d.phase(0),d.phase(1));
   return 0;
  }
  int ticks=120;std::vector<std::pair<int,double>> cmds;
  if(probe=="freefall"){ticks=120;}
  else if(probe=="stand"){ticks=60;}
  else if(probe=="walk"){
   if(argc>=4){ticks=std::atoi(argv[3]);}
   if(argc>=5){std::string spec=argv[4];size_t p=0;
    while(p<spec.size()){size_t q=spec.find(',',p),r=spec.find(':',p);
     int tk=std::atoi(spec.substr(p,r-p).c_str());
     double vx=std::atof(spec.substr(r+1,(q==std::string::npos?spec.size():q)-r-1).c_str());
     cmds.push_back({tk,vx});if(q==std::string::npos)break;p=q+1;}}
  }else{std::fprintf(stderr,"unknown probe\n");return 2;}
  std::fprintf(stderr,"PROBE=%s ticks=%d\n",probe.c_str(),ticks);
  GaitWalker d(data,9.80665,V{0,0,0},dt);
  std::fprintf(stderr,"CONSTRUCTED\n");
  if(probe=="freefall")d.configure({{"power",false},{"contact_enabled",false},{"start_at_tables",false},{"reset",true}});
  if(probe=="stand")d.configure({{"gait_enabled",false},{"reset",true}});
  if(getenv("CP_CFG")){ // mechanism-split knob: CP_CFG="key:val,key:val"
   J cfg=J::object();std::string s(getenv("CP_CFG"));size_t p=0;
   const char* boolkeys[]={"power","contact_enabled","gait_enabled","capture_enabled","posture_drive","start_at_tables","reset"};
   while(p<s.size()){size_t q=s.find(',',p),r=s.find(':',p);
    std::string k=s.substr(p,r-p);double val=std::atof(s.substr(r+1,(q==std::string::npos?s.size():q)-r-1).c_str());
    bool isbool=false;for(const char* bk:boolkeys)if(k==bk)isbool=true;
    if(isbool)cfg[k]=(val!=0.);else cfg[k]=val;if(q==std::string::npos)break;p=q+1;}
   cfg["reset"]=true;d.configure(cfg);std::fprintf(stderr,"CP_CFG applied\n");}
  std::fprintf(stderr,"CONFIGURED\n");
  size_t nc=d.model().names.size();
  double bat_prev=0;for(size_t k=0;k<12;++k)bat_prev+=d.batteries()[k];
  int cm=0;std::string refused="";int refused_tick=-1;
  for(int t=0;t<ticks;++t){
   if(cm<(int)cmds.size()&&cmds[cm].first==t){d.configure({{"commanded_target_velocity_x",cmds[cm].second}});++cm;}
   std::fprintf(stderr,"T%d ",t);try{d.step();}catch(const Refusal&e){refused=e.what();refused_tick=t;break;}
   const Dense& q=d.angles();const Dense& v=d.speeds();
   double bat=0;for(size_t k=0;k<12;++k)bat+=d.batteries()[k];
   int hf0=0,hf1=0,fm0=0,fm1=0;
   int tL=0,tR=0;
   if(getenv("CP_NO_STATUS")){std::printf("tick=%d q3=%.17g q4=%.17g q2=%.17g v3=%.17g phi0=%.17g phi1=%.17g tL=0 tR=0 bat=%.17g hf=0,0 fm=0,0\n",t,q[3],q[4],q[2],v[3],d.phase(0),d.phase(1),bat);continue;}
   {try{
    auto s=d.status();
    const J& g=s.at("gait");
    if(g.contains("hind_step")){hf0=(int)number(g.at("hind_step")[0].at("fires"));hf1=(int)number(g.at("hind_step")[1].at("fires"));}
    if(g.contains("fore_paw")&&g.at("fore_paw")[0].contains("fore_mode")){
     fm0=std::string(g.at("fore_paw")[0].at("fore_mode"))=="swing"?1:0;
     fm1=std::string(g.at("fore_paw")[1].at("fore_mode"))=="swing"?1:0;}
    tL=g.at("touching_left").get<bool>()?1:0;tR=g.at("touching_right").get<bool>()?1:0;
   }catch(const std::exception&){fm0=-1;fm1=-1;}}
   std::printf("tick=%d q3=%.17g q4=%.17g q2=%.17g v3=%.17g phi0=%.17g phi1=%.17g tL=%d tR=%d bat=%.17g hf=%d,%d fm=%d,%d\n",
    t,q[3],q[4],q[2],v[3],d.phase(0),d.phase(1),
    bat,hf0,hf1,fm0,fm1);
   if(getenv("CP_FULL")){
    std::printf("FULL t=%d",t);
    for(size_t i=0;i<nc;++i)std::printf(" q%zu=%.17g",i,(double)q[i]);
    for(size_t i=0;i<nc;++i)std::printf(" v%zu=%.17g",i,(double)v[i]);
    std::printf("\n");}
  }
  std::printf("END refused=%s refused_tick=%d\n",refused.c_str(),refused_tick);
  return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"ERROR %s\n",e.what());return 1;}
}
