#pragma once
// Rest-frame articulated transforms and strict, transactional JNT decoding.
// Geometry binding only: these operations do not supply actuator dynamics.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <set>
#include <string>
#include <vector>

namespace chimera::articulation {
// M,T maps rest coordinates through the already-composed ancestor chain.
// Append a child rotation about its REST pivot: A <- A * child, not child * A.
inline void append_local_rotation(const float R[9], const float J[3],
                                  float M[9], float T[3]) {
    float off[3], next[9], shift[3];
    for (int r=0;r<3;++r) {
        off[r]=J[r];
        for (int c=0;c<3;++c) off[r]-=R[r*3+c]*J[c];
    }
    for (int r=0;r<3;++r) {
        shift[r]=T[r];
        for (int c=0;c<3;++c) shift[r]+=M[r*3+c]*off[c];
        for (int c=0;c<3;++c) {
            next[r*3+c]=0;
            for (int k=0;k<3;++k) next[r*3+c]+=M[r*3+k]*R[k*3+c];
        }
    }
    std::copy(next,next+9,M); std::copy(shift,shift+3,T);
}

struct JointBinding {
    uint32_t vertex_count=0, joint_count=0;
    bool lbs=false, second_owner=false;
    std::vector<std::string> names;
    std::vector<int32_t> owner, parents, secondary;
    std::vector<float> weight, pivots, axes, limits, secondary_weight;
};

inline bool decode_joint_binding(const std::vector<uint8_t>& bytes,
                                size_t mesh_vertices, JointBinding& output,
                                std::string& error) {
    auto fail=[&](const char* why){error=why;return false;};
    if (bytes.size()<16) return fail("short_header");
    bool v1=std::memcmp(bytes.data(),"JNT1",4)==0;
    bool v2=std::memcmp(bytes.data(),"JNT2",4)==0;
    bool v3=std::memcmp(bytes.data(),"JNT3",4)==0;
    if (!(v1||v2||v3)) return fail("unsupported_format");
    auto u32=[&](size_t p)->uint32_t {
        return uint32_t(bytes[p]) | uint32_t(bytes[p+1])<<8 |
               uint32_t(bytes[p+2])<<16 | uint32_t(bytes[p+3])<<24;
    };
    uint32_t nv=u32(4), nj=u32(8), nl=u32(12);
    if (!nv || nv!=mesh_vertices) return fail("mesh_vertex_count_mismatch");
    if (!nj || nj>65536) return fail("joint_count_limit");
    uint64_t expected=16ull+nl+8ull*nv+32ull*nj+(v1?0ull:4ull*nj)+(v3?8ull*nv:0ull);
    if (expected!=bytes.size()) return fail("payload_length_mismatch");
    JointBinding b; b.vertex_count=nv;b.joint_count=nj;b.lbs=!v1;b.second_owner=v3;
    size_t p=16, names_end=16ull+nl;
    std::set<std::string> unique;
    for (uint32_t i=0;i<nj;++i) {
        size_t start=p;
        while (p<names_end && bytes[p]) ++p;
        if (p==start || p==names_end) return fail("joint_name_invalid");
        std::string name(reinterpret_cast<const char*>(bytes.data()+start),p-start);
        if (!unique.insert(name).second) return fail("duplicate_joint_name");
        b.names.push_back(name);++p;
    }
    if (p!=names_end) return fail("joint_names_length_mismatch");
    auto ints=[&](std::vector<int32_t>& out,size_t n){
        out.resize(n);
        for (auto& x:out) {uint32_t bits=u32(p);std::memcpy(&x,&bits,4);p+=4;}
    };
    auto floats=[&](std::vector<float>& out,size_t n){
        out.resize(n);
        for (auto& x:out) {uint32_t bits=u32(p);std::memcpy(&x,&bits,4);p+=4;}
    };
    ints(b.owner,nv);floats(b.weight,nv);floats(b.pivots,3ull*nj);
    floats(b.axes,3ull*nj);floats(b.limits,2ull*nj);
    if (v1) b.parents.assign(nj,-1); else ints(b.parents,nj);
    if (v3) {ints(b.secondary,nv);floats(b.secondary_weight,nv);}
    else b.secondary.assign(nv,-1);
    for (auto* values:{&b.weight,&b.pivots,&b.axes,&b.limits,&b.secondary_weight})
        for (float x:*values) if (!std::isfinite(x)) return fail("nonfinite_joint_data");
    for (uint32_t i=0;i<nv;++i) {
        int j=b.owner[i];
        // Legacy JNT1 explicitly supports untouched vertices. LBS bodies must be complete.
        if (j < (v1?-1:0) || j>=int(nj)) return fail("unbound_or_invalid_vertex_owner");
        if (b.weight[i]<0 || b.weight[i]>1) return fail("invalid_binding_weight");
        if (b.secondary[i]<-1 || b.secondary[i]>=int(nj)) return fail("invalid_secondary_owner");
        if (v3 && (b.secondary_weight[i]<0 || b.secondary_weight[i]>1 ||
                   std::fabs(b.weight[i]+b.secondary_weight[i]-1.f)>2e-5f))
            return fail("binding_partition_of_unity");
    }
    for (uint32_t i=0;i<nj;++i) {
        int parent=b.parents[i];
        if (parent<-1 || parent>=int(nj)) return fail("invalid_parent");
        if (b.limits[2*i]>b.limits[2*i+1]) return fail("reversed_joint_limits");
        double length=0;
        for (int k=0;k<3;++k) length+=double(b.axes[3*i+k])*b.axes[3*i+k];
        if (std::fabs(length-1.)>1e-4) return fail("joint_axis_not_unit");
    }
    // Validate every chain, including zero-weight joints. The resident shader has 8 slots.
    for (uint32_t i=0;i<nj;++i) {
        std::set<int> visited;
        for (int j=int(i);j>=0;j=b.parents[j]) {
            if (!visited.insert(j).second) return fail("parent_cycle");
            if (visited.size()>8) return fail("shader_chain_capacity");
        }
    }
    output=std::move(b); error.clear();return true;
}
} // namespace chimera::articulation
