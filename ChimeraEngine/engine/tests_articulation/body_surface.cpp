#include "../membrane_tick.hpp"
#include "../../native/viewer3rd/json.hpp"
#include <fstream>
#include <iostream>
using json=nlohmann::json;
using namespace chimera::articulation;
std::vector<uint8_t> read(const char* path){std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("input missing");return {std::istreambuf_iterator<char>(f),{}};}
// Independent oracle: rotate each point about the leaf first, then walk upward.
std::array<double,3> oracle(std::array<double,3> p,int j,const JointBinding& b,const std::vector<float>& angles,bool position){
    for(;j>=0;j=b.parents[j]){
        std::array<double,3>a{},q{},pivot{};
        for(int k=0;k<3;++k){a[k]=b.axes[3*j+k];pivot[k]=position?b.pivots[3*j+k]:0.;q[k]=p[k]-pivot[k];}
        double c=std::cos(double(angles[j])),s=std::sin(double(angles[j])),dot=a[0]*q[0]+a[1]*q[1]+a[2]*q[2];
        for(int k=0;k<3;++k)p[k]=pivot[k]+q[k]*c+a[k]*dot*(1-c)+s*(a[(k+1)%3]*q[(k+2)%3]-a[(k+2)%3]*q[(k+1)%3]);
    }return p;
}

int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("usage: body_surface monkey_birth.bin monkey_joints.bin");
 auto mesh=read(argv[1]),raw=read(argv[2]);uint32_t nv,nf;std::memcpy(&nv,mesh.data(),4);std::memcpy(&nf,mesh.data()+4,4);
 if(mesh.size()!=8ull+12ull*nv+12ull*nf)throw std::runtime_error("mesh size");
 std::vector<float> rest(9ull*nv,0.f);std::vector<uint32_t> ids(3ull*nf);
 for(uint32_t i=0;i<nv;++i){std::memcpy(&rest[9ull*i],mesh.data()+8+12ull*i,12);for(int k=6;k<9;++k)rest[9ull*i+k]=.6f;}
 std::memcpy(ids.data(),mesh.data()+8+12ull*nv,ids.size()*4);
 // Area weighted normals from the canonical triangles.
 for(size_t i=0;i<ids.size();i+=3){float u[3],v[3],n[3];for(int k=0;k<3;++k){u[k]=rest[9ull*ids[i+1]+k]-rest[9ull*ids[i]+k];v[k]=rest[9ull*ids[i+2]+k]-rest[9ull*ids[i]+k];}for(int k=0;k<3;++k)n[k]=u[(k+1)%3]*v[(k+2)%3]-u[(k+2)%3]*v[(k+1)%3];for(int j=0;j<3;++j)for(int k=0;k<3;++k)rest[9ull*ids[i+j]+3+k]+=n[k];}
 for(uint32_t i=0;i<nv;++i){double nn=0;for(int k=0;k<3;++k)nn+=double(rest[9ull*i+3+k])*rest[9ull*i+3+k];if(nn>0)for(int k=0;k<3;++k)rest[9ull*i+3+k]/=float(std::sqrt(nn));}
 JointBinding b;std::string error; if(!decode_joint_binding(raw,nv,b,error))throw std::runtime_error(error);
 std::string pack(raw.begin(),raw.end());MembraneTick tick;tick.init(nf,ids,rest);auto surface=rest;
 json checks=json::array();auto test=[&](std::string n,bool ok,json detail=json::object()){checks.push_back({{"name",n},{"pass",ok},{"detail",detail}});};
 test("JNT3_admission",tick.load_body_binding(pack)&&tick.body_active());tick.step(surface,1.f/300);
 double rest_error=0;for(uint32_t i=0;i<nv;++i)for(int k=0;k<3;++k)rest_error=std::max(rest_error,double(std::fabs(surface[9ull*i+k]-rest[9ull*i+k])));
 test("rest_geometry",rest_error<2e-6,{{"max_error",rest_error}});
 auto angles=std::vector<float>(b.joint_count,0.f);
 for(uint32_t j=0;j<b.joint_count;++j){float deg=(b.names[j]=="hip_L"?20.f:b.names[j]=="knee_L"?25.f:0.f);if(deg){test("pose_"+b.names[j],tick.pose_index(j,deg));angles[j]=deg*3.14159265358979f/180.f;}}
 tick.step(surface,1.f/300);double pe=0;size_t moved=0;double farthest=0;
 for(uint32_t i=0;i<nv;++i){std::array<double,3>p{rest[9ull*i],rest[9ull*i+1],rest[9ull*i+2]};int j=b.owner[i],k=b.secondary[i]<0?b.parents[j]:b.secondary[i];auto a=oracle(p,j,b,angles,true),z=oracle(p,k,b,angles,true);double delta2=0;for(int c=0;c<3;++c){double want=b.weight[i]*a[c]+(1-b.weight[i])*z[c];pe=std::max(pe,std::fabs(want-surface[9ull*i+c]));double d=surface[9ull*i+c]-rest[9ull*i+c];delta2+=d*d;}if(delta2>farthest){farthest=delta2;moved=i;}}
 test("full_mesh_independent_hierarchy_oracle",pe<2e-5,{{"max_error",pe},{"vertices",nv}});
 auto before=surface;auto before_state=json::parse(tick.state_json());bool refused=!tick.load_body_binding(pack.substr(0,pack.size()-1));auto after_state=json::parse(tick.state_json());for(const char* field:{"ts_us","ts_ms"}){before_state.erase(field);after_state.erase(field);}test("invalid_binding_transactional",refused&&before_state==after_state);
 test("competing_legacy_binding_refused",!tick.load_vertbind("bad")&&!tick.load_joint_pins("bad")&&!tick.load_classify("bad"));
 test("legacy_controller_not_silently_reused",!tick.set_gait(true)&&!tick.set_stance(true)&&!tick.set_reflex_channel("breathing",true));
 float hit[3]={surface[9*moved],surface[9*moved+1],surface[9*moved+2]};
 test("touch_reads_moved_surface",tick.point_skin_dist2(hit)<1e-12f && farthest>.0225,{{"vertex",moved},{"displacement_m",std::sqrt(farthest)}});
 test("press_admission",tick.touch_press_at(hit,200.f));tick.step(surface,1.f/300);
 double inward=0,dist=0;for(int k=0;k<3;++k){double d=surface[9*moved+k]-before[9*moved+k];inward-=d*before[9*moved+3+k];dist+=d*d;}
 double expected=200./(4.*3.14159265358979*4000.);
 test("press_uses_posed_normal",std::fabs(inward-expected)<2e-6 && std::fabs(std::sqrt(dist)-expected)<2e-6,{{"expected_m",expected},{"inward_m",inward}});
 std::vector<uint8_t> streamed;tick.export_verts(rest,streamed);
 test("export_uses_authoritative_surface",streamed.size()==4+surface.size()*4 && std::memcmp(streamed.data()+4,surface.data(),surface.size()*4)==0);
 tick.touch_clear();for(int i=0;i<900;++i)tick.step(surface,1.f/300);for(uint32_t j=0;j<b.joint_count;++j)tick.pose_index(j,0);tick.step(surface,1.f/300);
 int outcome;bool sealed=tick.seal(1.f,0,&outcome);test("actual_monkey_seal",sealed,{{"state",json::parse(tick.state_json())["seal_refusal"]}});
 if(sealed){tick.step(surface,1.f/300);auto state=json::parse(tick.state_json());std::vector<uint8_t> seal;tick.export_seal_state(seal);auto w=state["w_sum"];tick.pose_index(13,20);tick.step(surface,1.f/300);auto posed_state=json::parse(tick.state_json());test("pose_preserves_inventory",w==posed_state["w_sum"]);tick.pose_index(13,0);tick.step(surface,1.f/300);auto reset=json::parse(tick.state_json());bool stable=true;for(size_t i=0;i<state["seal_cells"].size();++i)stable &= state["seal_cells"][i]["v0"]==reset["seal_cells"][i]["v0"] && state["seal_cells"][i]["w"]==reset["seal_cells"][i]["w"] && std::fabs(double(reset["seal_cells"][i]["p"]))<1.;test("pose_reset_reference_pressure",stable);
 MembraneTick restored;restored.init(nf,ids,rest);bool ok=restored.load_body_binding(pack)&&restored.load_seal_state(std::string(seal.begin(),seal.end()));auto rs=rest;restored.step(rs,1.f/300);test("body_and_seal_restore",ok && json::parse(restored.state_json())["w_sum"]==w && restored.body_active());}
 tick.init(nf,ids,rest);test("mesh_reload_clears_body_owner",!tick.body_active());
 int failed=0;for(auto& c:checks)if(!c["pass"].get<bool>())++failed;
 std::cout<<json({{"checks",checks},{"failed",failed},{"scope","shared geometry, touch and seal state; not force-driven actuation or locomotion"}}).dump(2)<<"\n";return failed?1:0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
