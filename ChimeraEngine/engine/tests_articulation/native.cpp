#include "../joint_binding.hpp"
#include "../../native/viewer3rd/json.hpp"
#include <fstream>
#include <iostream>
using namespace chimera::articulation;
using json=nlohmann::json;
std::vector<uint8_t> read(const char* path) {
    std::ifstream f(path,std::ios::binary);
    if(!f) throw std::runtime_error("input missing");
    return {std::istreambuf_iterator<char>(f),{}};
}
void put(std::vector<uint8_t>& b,size_t offset,uint32_t value) {
    for(int i=0;i<4;++i)b.at(offset+i)=uint8_t(value>>(8*i));
}
int main(int argc,char**argv) {
    try {
        if(argc!=2)throw std::runtime_error("usage: articulation_native monkey_joints.bin");
        auto raw=read(argv[1]);JointBinding b;std::string err;json checks=json::array();
        auto test=[&](std::string name,bool ok){checks.push_back({{"name",name},{"pass",ok}});};
        uint32_t nv=uint32_t(raw.at(4))|uint32_t(raw.at(5))<<8|uint32_t(raw.at(6))<<16|uint32_t(raw.at(7))<<24;
        test("actual_monkey_pack",decode_joint_binding(raw,nv,b,err));
        if(!err.empty()) throw std::runtime_error(err);
        size_t names=16;while(names<raw.size() && b.names.back()!=std::string(reinterpret_cast<char*>(raw.data()+names)))
            names+=std::strlen(reinterpret_cast<char*>(raw.data()+names))+1;
        names+=b.names.back().size()+1;
        size_t weights=names+4ull*nv, parents=names+8ull*nv+32ull*b.joint_count;
        auto reject=[&](const char* label,std::vector<uint8_t> bad,size_t n=0){
            JointBinding preserved=b;bool ok=decode_joint_binding(bad,n?n:nv,preserved,err);
            test(label,!ok && preserved.names==b.names && preserved.owner==b.owner && preserved.weight==b.weight);
        };
        auto bad=raw;bad.pop_back();reject("truncated_packet_preserves_binding",bad);
        bad=raw;bad.push_back(0);reject("trailing_bytes_refused",bad);
        reject("wrong_mesh_count_refused",raw,nv+1);
        bad=raw;bad[16]=0;reject("empty_name_refused",bad);
        bad=raw;put(bad,names,0xffffffffu);reject("unbound_lbs_vertex_refused",bad);
        bad=raw;put(bad,weights,0x7fc00000u);reject("nan_weight_refused",bad);
        bad=raw;put(bad,weights,0x40000000u);reject("overweight_refused",bad);
        bad=raw;put(bad,parents,0);reject("parent_cycle_refused",bad);
        bad=raw;put(bad,parents,0xfffffffeu);reject("negative_parent_refused",bad);
        bad=raw;for(int i=0;i<9;++i)put(bad,parents+4*i,i==8?0xffffffffu:uint32_t(i+1));
        reject("shader_depth_overflow_refused",bad);
        bad=raw;put(bad,names+8ull*nv+12ull*b.joint_count,0);
        put(bad,names+8ull*nv+12ull*b.joint_count+4,0);put(bad,names+8ull*nv+12ull*b.joint_count+8,0);
        reject("zero_axis_refused",bad);
        // Independent closed form: two 90 degree turns, pivots (0,0) and (1,0).
        // End point (2,0) must become (-1,1); child pivot becomes (0,1).
        float R[9]={0,-1,0,1,0,0,0,0,1}, J0[3]={0,0,0},J1[3]={1,0,0};
        float M[9]={1,0,0,0,1,0,0,0,1},T[3]={0,0,0};
        append_local_rotation(R,J0,M,T);append_local_rotation(R,J1,M,T);
        test("nested_hinge_endpoint",std::fabs(2*M[0]+T[0]+1)<1e-6 && std::fabs(2*M[3]+T[1]-1)<1e-6);
        test("child_pivot_follows_parent",std::fabs(M[0]+T[0])<1e-6 && std::fabs(M[3]+T[1]-1)<1e-6);
        test("terminal_bone_length_preserved",std::fabs(std::hypot(M[0],M[3])-1)<1e-6);
        // Third turn is about another axis; verifies multiplication cannot commute by accident.
        float X[9]={1,0,0,0,0,-1,0,1,0};float J2[3]={2,0,0};
        append_local_rotation(X,J2,M,T);
        // (2,1,0) -> local (2,0,1) -> elbow (1,1,1) -> base (-1,1,1).
        test("mixed_axis_chain",std::fabs(2*M[0]+M[1]+T[0]+1)<1e-6 &&
             std::fabs(2*M[3]+M[4]+T[1]-1)<1e-6 && std::fabs(2*M[6]+M[7]+T[2]-1)<1e-6);
        int fails=0;for(auto& c:checks)if(!c["pass"].get<bool>())++fails;
        std::cout<<json({{"checks",checks},{"failed",fails},{"vertices",nv},{"joints",b.joint_count},
                        {"names",b.names},{"scope","binding and transform arithmetic; no locomotion qualification"}}).dump(2)<<"\n";
        return fails?1:0;
    }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}
}
