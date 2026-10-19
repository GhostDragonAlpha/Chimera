// SPDX-License-Identifier: AGPL-3.0-or-later
#include "engine.hpp"
#include "water_checkpoint.hpp"
#include <limits>

// WCS1 little-endian envelope (Windows/x64): 80-byte header, V int32[n],
// persistent edge flow float64[e], depth float64[n], 8-byte FNV-1a checksum.
// Checksum detects damage, not authenticity; the Blender document also pins
// SHA256 of the complete blob and the executable/shaders/source manifest.
// Render/history buffers are observations, not part of the physical state.
bool Engine::water_finish_command(VkCommandBuffer cb) {
    bool ok=vkEndCommandBuffer(cb)==VK_SUCCESS;
    if(ok) ok=vkResetFences(device_,1,&w_fence_)==VK_SUCCESS;
    if(ok) {
        VkSubmitInfo si{}; si.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;
        si.commandBufferCount=1; si.pCommandBuffers=&cb;
        ok=vkQueueSubmit(queue_,1,&si,w_fence_)==VK_SUCCESS;
        if(ok) ok=vkWaitForFences(device_,1,&w_fence_,VK_TRUE,UINT64_MAX)==VK_SUCCESS;
    }
    vkFreeCommandBuffers(device_,cmd_pool_,1,&cb); return ok;
}

bool Engine::water_transfer_state(std::vector<uint8_t>& data, bool write) {
    const VkDeviceSize vb=VkDeviceSize(w_n_cells_)*4, qb=VkDeviceSize(w_n_edges_)*8;
    const VkDeviceSize db=VkDeviceSize(w_n_cells_)*8, bytes=vb+qb+db;
    if (write && data.size()!=bytes) return false;
    if (vkDeviceWaitIdle(device_)!=VK_SUCCESS) return false;
    VkBuffer staging=VK_NULL_HANDLE; VkDeviceMemory memory=VK_NULL_HANDLE; void* mapped=nullptr;
    auto cleanup=[&]() { if(mapped) vkUnmapMemory(device_,memory);
        if(staging) vkDestroyBuffer(device_,staging,nullptr);
        if(memory) vkFreeMemory(device_,memory,nullptr); };
    VkBufferCreateInfo bi{}; bi.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO; bi.size=bytes;
    bi.usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT|VK_BUFFER_USAGE_TRANSFER_DST_BIT;
    bi.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
    if(vkCreateBuffer(device_,&bi,nullptr,&staging)!=VK_SUCCESS) return false;
    VkMemoryRequirements mr{}; vkGetBufferMemoryRequirements(device_,staging,&mr);
    VkMemoryAllocateInfo ai{}; ai.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO; ai.allocationSize=mr.size;
    ai.memoryTypeIndex=find_mem_type(mr.memoryTypeBits,VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    if(vkAllocateMemory(device_,&ai,nullptr,&memory)!=VK_SUCCESS ||
       vkBindBufferMemory(device_,staging,memory,0)!=VK_SUCCESS ||
       vkMapMemory(device_,memory,0,bytes,0,&mapped)!=VK_SUCCESS) { cleanup(); return false; }
    if(write) std::memcpy(mapped,data.data(),size_t(bytes)); else data.resize(size_t(bytes));
    VkCommandBuffer cb=begin_single_time_cmd();
    water_checkpoint::barrier(cb);
    VkBuffer buffers[3]={w_V_buf_,w_qe_buf_,w_depth_buf_};
    VkDeviceSize sizes[3]={vb,qb,db}; VkDeviceSize off=0;
    for(int i=0;i<3;++i) {
        VkBufferCopy cp{}; cp.size=sizes[i];
        if(write) { cp.srcOffset=off; vkCmdCopyBuffer(cb,staging,buffers[i],1,&cp); }
        else { cp.dstOffset=off; vkCmdCopyBuffer(cb,buffers[i],staging,1,&cp); }
        off+=sizes[i];
    }
    water_checkpoint::barrier(cb);
    if(write) {
        // Restore starts a new bounded observation history, without stepping.
        VkBufferCopy cp{}; cp.size=vb; vkCmdCopyBuffer(cb,w_V_buf_,w_states_buf_,1,&cp);
        water_checkpoint::barrier(cb);
    }
    if(!write) water_checkpoint::host_read_barrier(cb);
    bool ok=water_finish_command(cb);
    if(ok && !write) std::memcpy(data.data(),mapped,size_t(bytes));
    cleanup(); return ok;
}

bool Engine::water_save(std::vector<uint8_t>& out, std::string& error) {
    using namespace water_checkpoint;
    if(!water_loaded_ || water_clock_on_.load()) { error="pause_water_clock_before_checkpoint"; return false; }
    std::vector<uint8_t> state;
    if(!water_transfer_state(state,false)) { error="water_checkpoint_gpu_transfer_failed"; return false; }
    out.clear(); put(out,uint32_t(0x31534357)); put(out,uint32_t(1)); // WCS1
    put(out,w_n_cells_); put(out,w_n_edges_); put(out,w_substrate_id_);
    put(out,w_steps_total_); put(out,water_clock_steps_total_.load());
    put(out,w_time_); put(out,w_last_dt_);
    put(out,water_clock_steps_per_frame_.load()); put(out,water_clock_inj_target_.load());
    put(out,water_clock_inj_count_.load()); put(out,uint32_t(0)); // paused, reserved flags
    put(out,water_clock_dt_.load());
    out.insert(out.end(),state.begin(),state.end());
    put(out,hash(out.data(),out.size())); return true;
}

bool Engine::water_restore(const std::vector<uint8_t>& data, std::string& error) {
    using namespace water_checkpoint;
    const size_t size=88+size_t(w_n_cells_)*12+size_t(w_n_edges_)*8;
    auto refuse=[&](const char* why) { error=why; return false; };
    if(!water_loaded_ || water_clock_on_.load()) return refuse("pause_water_clock_before_restore");
    if(data.size()!=size || get<uint32_t>(data,0)!=0x31534357 || get<uint32_t>(data,4)!=1)
        return refuse("water_checkpoint_format_or_length");
    if(get<uint32_t>(data,8)!=w_n_cells_ || get<uint32_t>(data,12)!=w_n_edges_ ||
       get<uint64_t>(data,16)!=w_substrate_id_) return refuse("water_checkpoint_substrate_mismatch");
    if(get<uint64_t>(data,size-8)!=hash(data.data(),size-8)) return refuse("water_checkpoint_checksum");
    const auto steps=get<uint64_t>(data,24), automatic=get<uint64_t>(data,32);
    const double time=get<double>(data,40), dt=get<double>(data,48), clockdt=get<double>(data,72);
    const auto clocksteps=get<uint32_t>(data,56);
    const auto target=get<int32_t>(data,60), count=get<int32_t>(data,64);
    if(automatic>steps || !std::isfinite(time) || time<0 || !std::isfinite(dt) || dt<0 || dt>1 ||
       (steps && (dt<=0 || time<=0)) || (!steps && (time!=0 || dt!=0)) ||
       !std::isfinite(clockdt) || clockdt<=0 || clockdt>1 || !clocksteps || clocksteps>4096 ||
       target < -1 || (target>=0 && uint32_t(target)>=w_n_cells_) || count<0 || get<uint32_t>(data,68)!=0)
        return refuse("water_checkpoint_clock_invalid");
    size_t off=80;
    for(uint32_t i=0;i<w_n_cells_;++i,off+=4)
        if(get<int32_t>(data,off)<0) return refuse("water_checkpoint_negative_volume");
    for(uint32_t i=0;i<w_n_edges_;++i,off+=8)
        if(!std::isfinite(get<double>(data,off))) return refuse("water_checkpoint_nonfinite_flow");
    for(uint32_t i=0;i<w_n_cells_;++i,off+=8)
        if(!std::isfinite(get<double>(data,off)) || get<double>(data,off)<0) return refuse("water_checkpoint_invalid_depth");
    // No GPU writes, counters, clocks or history changes until ALL validation passes.
    std::vector<uint8_t> state(data.begin()+80,data.end()-8);
    if(!water_transfer_state(state,true)) return refuse("water_checkpoint_gpu_transfer_failed");
    w_steps_total_=steps; water_clock_steps_total_.store(automatic); w_time_=time; w_last_dt_=dt;
    water_clock_steps_per_frame_.store(clocksteps); water_clock_dt_.store(clockdt);
    water_clock_inj_target_.store(target); water_clock_inj_count_.store(count);
    w_states_n_=1; w_history_next_=1;
    return true;
}

bool Engine::water_clock_config(bool on, uint32_t steps, double dt, int32_t target, int32_t count) {
    if(!water_loaded_ || !steps || steps>4096 || !std::isfinite(dt) || dt<=0 || dt>1 ||
       target < -1 || (target>=0 && uint32_t(target)>=w_n_cells_) || count<0) return false;
    water_clock_steps_per_frame_.store(steps); water_clock_dt_.store(dt);
    water_clock_inj_target_.store(target); water_clock_inj_count_.store(count);
    water_clock_on_.store(on); return true;
}
