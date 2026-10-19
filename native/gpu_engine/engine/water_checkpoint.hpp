// SPDX-License-Identifier: AGPL-3.0-or-later
#pragma once
#include <vulkan/vulkan.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

namespace water_checkpoint {
inline uint64_t hash(const uint8_t* data, size_t n) {
    uint64_t h = 14695981039346656037ull;
    for (size_t i = 0; i < n; ++i) { h ^= data[i]; h *= 1099511628211ull; }
    return h;
}
template<class T> void put(std::vector<uint8_t>& out, T value) {
    const auto* p = reinterpret_cast<const uint8_t*>(&value);
    out.insert(out.end(), p, p + sizeof(T));
}
template<class T> void array(std::vector<uint8_t>& out, const std::vector<T>& values) {
    for (const T& x : values) put(out, x);
}
template<class T> T get(const std::vector<uint8_t>& data, size_t offset) {
    T value; std::memcpy(&value, data.data() + offset, sizeof(T)); return value;
}
// All these APIs run on the owner thread. Transfers and compute must be
// ordered in both directions, including read-before-write hazards.
inline void barrier(VkCommandBuffer cb) {
    VkMemoryBarrier b{}; b.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    b.srcAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT;
    b.dstAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT;
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
        VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 1, &b, 0, nullptr, 0, nullptr);
}
// Explicit device -> host memory-domain dependency, followed by a fence wait.
// https://docs.vulkan.org/guide/latest/synchronization_examples.html
inline void host_read_barrier(VkCommandBuffer cb) {
    VkMemoryBarrier b{}; b.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    b.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT; b.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
    vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,
        0,1,&b,0,nullptr,0,nullptr);
}
template<class Upload> uint64_t substrate_id(const Upload& u) {
    // Exact little-endian /water_bin bytes, including initial V and future injections.
    std::vector<uint8_t> b;
    put(b,u.n_cells); put(b,u.n_edges); put(b,u.n_colors); put(b,uint32_t(u.inj.size()/2));
    put(b,u.Q); put(b,u.G); put(b,u.c_local);
    array(b,u.areas); array(b,u.bed); array(b,u.V0); array(b,u.occ);
    array(b,u.eij); array(b,u.k_e); array(b,u.l_ij); array(b,u.edge_active);
    array(b,u.color_start); array(b,u.inj);
    return hash(b.data(),b.size());
}
template<class Upload> bool valid_upload(const Upload& u) {
    const size_t n=u.n_cells, e=u.n_edges, c=u.n_colors;
    if (!n || n>262144 || !e || e>786432 || !c || c>64 ||
        u.areas.size()!=n || u.bed.size()!=n || u.V0.size()!=n || u.occ.size()!=n ||
        u.eij.size()!=2*e || u.k_e.size()!=e || u.l_ij.size()!=e || u.edge_active.size()!=e ||
        u.color_start.size()!=c+1 || u.inj.size()%2 || u.inj.size()>2000000 ||
        !std::isfinite(u.Q) || u.Q<=0 || !std::isfinite(u.G) || u.G<=0 ||
        !std::isfinite(u.c_local) || u.c_local<=0 || u.color_start.front()!=0 ||
        u.color_start.back()!=e) return false;
    for (size_t i=0;i<n;++i)
        if (!std::isfinite(u.areas[i]) || u.areas[i]<=0 || !std::isfinite(u.bed[i]) ||
            u.V0[i]<0 || u.occ[i]>1) return false;
    std::vector<int> touched(n,-1);
    for (size_t color=0;color<c;++color) {
        if (u.color_start[color]>u.color_start[color+1] || u.color_start[color+1]>e) return false;
        for (size_t i=u.color_start[color];i<u.color_start[color+1];++i) {
            int a=u.eij[2*i], b=u.eij[2*i+1];
            if (a<0 || b<0 || size_t(a)>=n || size_t(b)>=n || a==b ||
                !std::isfinite(u.k_e[i]) || u.k_e[i]<0 || !std::isfinite(u.l_ij[i]) || u.l_ij[i]<=0 ||
                u.edge_active[i]>1 || touched[a]==int(color) || touched[b]==int(color)) return false;
            touched[a]=touched[b]=int(color);
        }
    }
    for (size_t i=0;i<u.inj.size();i+=2)
        if (u.inj[i+1]>INT32_MAX || (u.inj[i]>=n && u.inj[i]!=UINT32_MAX)) return false;
    return true;
}
} // namespace water_checkpoint
