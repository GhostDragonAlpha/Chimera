#pragma once
#include "earth_environment.hpp"
#include "arm_dynamics.hpp"
#include "coupled_dynamics.hpp"
#include "joint_binding.hpp"
#include <atomic>
#include <chrono>
#include <cstring>
#include <fstream>
#include <memory>
#include <mutex>
#include <thread>
class GraphEarth {
public:
 using J=chimera::environment::J;using V=chimera::environment::V;
 struct Render{std::vector<float> mesh;std::vector<uint32_t> indices;J state;};
 J bundle;
private:
 std::unique_ptr<chimera::environment::EarthTrial> sim_;std::unique_ptr<chimera::environment::ArmDynamics> dynamics_;std::unique_ptr<chimera::multibody::CoupledDynamics> coupled_;
 chimera::articulation::JointBinding binding_;std::vector<float> rest_,angles_;std::vector<uint32_t> indices_;
 mutable std::mutex mutex_;std::thread worker_;std::atomic<bool> stop_{false};bool paused_=false;uint64_t revision_=1,epoch_=0;double lag_=0,elbow_=0;std::string error_;
 static std::vector<uint8_t> read(const std::string& path){std::ifstream f(path,std::ios::binary);chimera::forces::require(bool(f),"earth_asset_missing");return {std::istreambuf_iterator<char>(f),{}};}
 std::vector<float> arm(double elbow)const{
  auto angles=angles_;auto elbow_it=std::find(binding_.names.begin(),binding_.names.end(),"elbow_flexion");chimera::forces::require(elbow_it!=binding_.names.end(),"arm_elbow_missing");angles[elbow_it-binding_.names.begin()]=float(elbow*chimera::environment::pi/180);
  if(coupled_){auto& model=coupled_->model();for(size_t i=0;i<model.names.size();++i){auto found=std::find(binding_.names.begin(),binding_.names.end(),model.names[i]);chimera::forces::require(found!=binding_.names.end(),"coupled_binding_coordinate_missing");angles[found-binding_.names.begin()]=float(coupled_->angles()[i]-model.defaults[i]);}}
  std::vector<float> posed;chimera::articulation::pose_binding(binding_,rest_,&angles,posed);V shift=bundle.at("scene").at("arm_translation_m").get<V>();
  for(size_t i=0;i<posed.size();i+=9)for(int k=0;k<3;++k){posed[i+k]+=float(shift[k]);posed[i+3+k]=0;}
  using namespace chimera::environment;
  for(size_t i=0;i<indices_.size();i+=3){auto get=[&](uint32_t j){return V{posed[9*j],posed[9*j+1],posed[9*j+2]};};auto n=cross(sub(get(indices_[i+1]),get(indices_[i])),sub(get(indices_[i+2]),get(indices_[i])));for(int j=0;j<3;++j)for(int k=0;k<3;++k)posed[9*indices_[i+j]+3+k]+=float(n[k]);}
  for(size_t i=0;i<posed.size();i+=9){double length=norm({posed[i+3],posed[i+4],posed[i+5]});if(length>0)for(int k=0;k<3;++k)posed[i+3+k]/=float(length);}
  return posed;
 }
 V hand(double elbow)const{auto mesh=arm(elbow);size_t start=bundle.at("arm").at("hand_vertex_start"),count=bundle.at("arm").at("hand_vertex_count");V p{};for(size_t i=start;i<start+count;++i)for(int k=0;k<3;++k)p[k]+=mesh[9*i+k]/count;p[1]-=chimera::forces::number(bundle.at("scene").at("hand_clearance_m"));return p;}
 J status_locked()const{
  auto s=coupled_?coupled_->status():(dynamics_?dynamics_->status():sim_->status());if(dynamics_||coupled_)s["environment"]=sim_->status()["environment"];s["ok"]=error_.empty();s["error"]=error_;s["mode"]=coupled_?"native_coupled_arm":(dynamics_?"native_force_arm":"native_earth_patch");s["scene_revision"]=revision_;s["epoch"]=epoch_;s["paused"]=paused_;s["clock_lag_s"]=lag_;s["graph_hash"]=bundle.at("graph_hash");s["scene_sha256"]=bundle.at("scene_sha256");if(!coupled_)s["elbow_deg"]=elbow_;s["world_id"]=bundle.at("scene").at("world_id");s["ground_id"]=bundle.at("scene").at("ground_id");s["attachment_id"]=bundle.at("scene").at("hand_port_id");if(dynamics_){s["attachment_id"]=bundle.at("arm_dynamics").at("recipe").at("attachment_id");s["support_id"]=bundle.at("arm_dynamics").at("recipe").at("support_id");}if(coupled_)s["attachment_id"]=bundle.at("coupled_dynamics").at("recipe").at("attachment_id");s["sources"]=bundle.at("sources");s["scope"]=bundle.at("scope");s["assumptions"]=coupled_?bundle.at("coupled_dynamics").at("recipe").at("assumptions"):dynamics_?bundle.at("arm_dynamics").at("recipe").at("assumptions"):bundle.at("scene").at("assumptions");return s;
 }
public:
 ~GraphEarth(){stop();}
 bool active()const{return bool(sim_);}
 void stop(){stop_=true;if(worker_.joinable())worker_.join();}
 void load(const std::string& path){
  using namespace chimera::environment;require(!sim_,"earth_already_loaded");std::ifstream f(path);require(bool(f),"earth_scene_missing");f>>bundle;require(bundle.at("schema")=="chimera.earth_scene.v1","earth_bundle_schema");
  auto mesh=read(bundle.at("arm").at("mesh_file"));require(mesh.size()>=24,"earth_mesh_header");uint32_t nv,ni;std::memcpy(&nv,mesh.data(),4);std::memcpy(&ni,mesh.data()+4,4);require(nv>0&&ni>0&&ni%3==0&&mesh.size()==24ull+36ull*nv+4ull*ni,"earth_mesh_length");
  rest_.resize(9ull*nv);indices_.resize(ni);std::memcpy(rest_.data(),mesh.data()+24,rest_.size()*4);std::memcpy(indices_.data(),mesh.data()+24+rest_.size()*4,indices_.size()*4);for(float p:rest_)require(std::isfinite(p),"earth_mesh_nonfinite");for(auto i:indices_)require(i<nv,"earth_mesh_index");
  std::string error;require(chimera::articulation::decode_joint_binding(read(bundle.at("arm").at("body_file")),nv,binding_,error),"earth_binding_refused");angles_.assign(binding_.joint_count,0);size_t start=bundle.at("arm").at("hand_vertex_start"),count=bundle.at("arm").at("hand_vertex_count");require(count>0&&start<=nv&&count<=nv-start,"earth_hand_range");
  sim_=std::make_unique<EarthTrial>(bundle.at("models"),bundle.at("source_parameters"),bundle.at("scene"));sim_->reset(hand(0));if(bundle.contains("coupled_dynamics"))coupled_=std::make_unique<chimera::multibody::CoupledDynamics>(bundle.at("coupled_dynamics"),number(sim_->status()["environment"]["gravity_m_s2"]),bundle.at("scene").at("arm_translation_m").get<V>());if(bundle.contains("arm_dynamics"))dynamics_=std::make_unique<ArmDynamics>(bundle.at("arm_dynamics"),number(sim_->status()["environment"]["gravity_m_s2"]));
 }
 void start(){
  chimera::forces::require(sim_&&!worker_.joinable(),"earth_worker_state");stop_=false;
  worker_=std::thread([this]{using clock=std::chrono::steady_clock;auto dt=std::chrono::duration_cast<clock::duration>(std::chrono::duration<double>(sim_->timestep()));auto next=clock::now()+dt;
   while(!stop_){std::this_thread::sleep_until(next);if(stop_)break;auto now=clock::now();{std::lock_guard<std::mutex> lock(mutex_);lag_=(std::max)(0.,std::chrono::duration<double>(now-next).count());if(!paused_&&error_.empty()&&(coupled_||dynamics_||(!sim_->held&&!sim_->outside))){try{if(coupled_){coupled_->step();}else if(dynamics_){dynamics_->step();elbow_=dynamics_->delta_deg();}else sim_->step();++revision_;}catch(const std::exception& e){error_=e.what();paused_=true;}}}next+=dt;}
  });
 }
 J status()const{std::lock_guard<std::mutex> lock(mutex_);chimera::forces::require(bool(sim_),"earth_scene_missing");return status_locked();}
 J control(const J& q){
  using namespace chimera::environment;require(q.is_object()&&!q.empty(),"earth_control_object");
  if(coupled_){
   std::lock_guard<std::mutex> lock(mutex_);
   if(q.contains("paused")){require(q.size()==1&&q.at("paused").is_boolean(),"coupled_pause_control");paused_=q.at("paused").get<bool>();}
   else {auto next=*coupled_;next.configure(q);*coupled_=std::move(next);if(q.value("reset",false)){error_.clear();paused_=false;++epoch_;}}
   ++revision_;return status_locked();
  }
  if(dynamics_){
   std::lock_guard<std::mutex> lock(mutex_);
   if(q.contains("paused")){require(q.size()==1&&q.at("paused").is_boolean(),"arm_pause_control");paused_=q.at("paused").get<bool>();}
   else {auto next=*dynamics_;next.configure(q);*dynamics_=std::move(next);elbow_=dynamics_->delta_deg();if(q.value("reset",false)){error_.clear();paused_=false;++epoch_;}}
   ++revision_;return status_locked();
  }
  J env=J::object();std::set<std::string> ops;
  for(auto it=q.begin();it!=q.end();++it){if(it.key()=="altitude_m"||it.key()=="slope_deg"||it.key()=="wind_m_s"||it.key()=="friction"||it.key()=="air")env[it.key()]=it.value();else{require(it.key()=="reset"||it.key()=="release"||it.key()=="paused"||it.key()=="elbow_deg","unknown_earth_control");ops.insert(it.key());}}
  require((env.empty()&&ops.size()==1)||(!env.empty()&&ops.empty()),"earth_control_conflict");
  for(const char* b:{"reset","release","paused"})if(q.contains(b))require(q.at(b).is_boolean(),"earth_boolean_required");
  std::lock_guard<std::mutex> lock(mutex_);require(bool(sim_),"earth_scene_missing");
  if(!env.empty()){auto candidate=*sim_;candidate.configure(env);candidate.reset(hand(elbow_));*sim_=std::move(candidate);error_.clear();paused_=false;++epoch_;}
  if(q.contains("elbow_deg")){double e=number(q.at("elbow_deg"));require(sim_->held&&e>=-60&&e<=40,"earth_elbow_requires_held_and_in_range");auto candidate=*sim_;candidate.reset(hand(e));*sim_=std::move(candidate);elbow_=e;++epoch_;}
  if(q.value("reset",false)){sim_->reset(hand(elbow_));error_.clear();paused_=false;++epoch_;}
  if(q.value("release",false)){require(error_.empty(),"earth_faulted");sim_->release();paused_=false;}
  if(q.contains("paused"))paused_=q.at("paused").get<bool>();++revision_;return status_locked();
 }
 Render render()const{
  using namespace chimera::environment;std::lock_guard<std::mutex> lock(mutex_);require(bool(sim_),"earth_scene_missing");Render out;out.state=status_locked();out.mesh=arm(elbow_);out.indices=indices_;
  auto triangle=[&](V a,V b,V c,V color){auto n=cross(sub(b,a),sub(c,a));double l=norm(n);require(l>1e-16,"earth_render_degenerate");for(auto p:{a,b,c}){out.indices.push_back(uint32_t(out.mesh.size()/9));for(double x:p)out.mesh.push_back(float(x));for(double x:n)out.mesh.push_back(float(x/l));for(double x:color)out.mesh.push_back(float(x));}};
  auto quad=[&](V a,V b,V c,V d,V color){triangle(a,b,c,color);triangle(a,c,d,color);};
  double size=number(bundle.at("scene").at("patch_half_width_m")),slope=number(sim_->config().at("slope_deg"))*pi/180;
  auto ground=[&](double x,double z){return V{x,std::tan(slope)*x,z};};
  // A metre-scale authored rigid plane, visually tiled without inventing terrain scans.
  for(int i=0;i<12;++i)for(int j=0;j<12;++j){double x=-size+2*size*i/12,z=-size+2*size*j/12,d=2*size/12;V color=(i+j)%2?V{.16,.22,.17}:V{.18,.24,.19};quad(ground(x,z),ground(x,z+d),ground(x+d,z+d),ground(x+d,z),color);}
  // Source arm is on an explicit fixed reference mount, not a simulated shoulder/body.
  V shift=bundle.at("scene").at("arm_translation_m").get<V>();double by=shift[1],bx=shift[0],bz=shift[2]-.045;quad({bx-.015,std::tan(slope)*(bx-.015),bz},{bx-.015,by,bz},{bx+.015,by,bz},{bx+.015,std::tan(slope)*(bx+.015),bz},{.22,.29,.32});
  if(dynamics_){
   // The visible platform is the same height as the unilateral hand boundary.
   double h=dynamics_->support_enabled()?dynamics_->support_height():-5.;V color{.25,.39,.43};
   quad({-.04,h,-.07},{-.04,h,.08},{.31,h,.08},{.31,h,-.07},color);
   quad({-.02,0,-.05},{-.02,h,-.05},{.00,h,-.05},{.00,0,-.05},color);
   quad({.27,0,.06},{.27,h,.06},{.29,h,.06},{.29,0,.06},color);
  }
  if(coupled_){
   // The visible slab is the same authored plane the solver presses against.
   const J& recipe=bundle.at("coupled_dynamics").at("recipe");
   if(recipe.contains("contact_plane_height_m")&&out.state.at("config").value("contact_enabled",false)){
    double h=number(recipe.at("contact_plane_height_m"));V color{.30,.42,.48};
    quad({-.15,h,-.15},{-.15,h,.15},{.40,h,.15},{.40,h,-.15},color);
    quad({-.15,h,-.15},{-.15,0,-.15},{.40,0,-.15},{.40,h,-.15},color);
    quad({-.15,h,.15},{-.15,0,.15},{.40,0,.15},{.40,h,.15},color);
   }
  }
  V center=coupled_?out.state.at("body").at("position_m").get<V>():dynamics_?dynamics_->hand_position():sim_->x;double radius=coupled_?number(out.state.at("body").at("radius_m")):dynamics_?dynamics_->radius():sim_->radius();double heat=(std::max)(0.,(std::min)(1.,(sim_->temperature-270)/25));V color{.85,.44+.18*heat,.14};
  const int rings=10,slices=20;auto point=[&](int j,int i){double t=pi*j/rings,p=2*pi*i/slices;return add(center,V{radius*std::sin(t)*std::cos(p),radius*std::cos(t),radius*std::sin(t)*std::sin(p)});};
  for(int j=0;j<rings;++j)for(int i=0;i<slices;++i){if(j>0)triangle(point(j,i),point(j,i+1),point(j+1,i),color);if(j<rings-1)triangle(point(j,i+1),point(j+1,i+1),point(j+1,i),color);}
  out.state["mesh_triangles"]=out.indices.size()/3;return out;
 }
};
