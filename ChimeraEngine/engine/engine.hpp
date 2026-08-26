#pragma once
#include <vulkan/vulkan.h>
#include <vector>
#include <string>
#include <mutex>
#include <atomic>
#include <cstdint>
#include <map>

struct EngineConfig {
    uint32_t width  = 1920;
    uint32_t height = 1080;
    float    G      = 1.0f;
    float    rw     = 0.5f;
    float    rb     = 2.0f;
    float    rc     = 3.0f;
    float    kw     = 100.0f;
    float    kb     = 10.0f;
    float    gamma_w= 5.0f;
    float    dt     = 0.02f;
    int      n_particles = 1200;
};

class Engine {
public:
    bool init(const EngineConfig& cfg);
    void shutdown();
    bool frame();                       // submit one physics+render pass, return true on success
    bool push_state(const std::vector<float>& pos, const std::vector<float>& vel, uint32_t count);
    bool dispatch_compute(std::vector<float>& out_velocities);  // GPU compute + velocity readback
    void mark_dirty() { dirty_ = true; }  // signal that params/count changed — next push_state reallocates
    uint32_t particle_count() const { return n_; }

    // ── membrane streaming (the C++ engine is the emission target) ──────────────
    bool load_membrane(const std::string& term, const std::vector<float>& pos, uint32_t count);
    void set_camera(float radius, float theta, float phi);
    void request_capture() { capture_ready_.store(false); capture_requested_.store(true); }
    bool capture_ready() const { return capture_ready_.load(); }
    bool capture_frame(std::vector<uint8_t>& out_rgba, uint32_t& w, uint32_t& h);

    // ── triangle mesh rendering (depth-tested opaque Lambert) ────────────────
    bool load_mesh(const std::vector<float>& verts, const std::vector<uint32_t>& indices,
                   uint32_t vcount, uint32_t icount);

    // ── GPU skinning (LBS over the 3DGS splats, skin.comp) ──────────────────────
    bool load_skinned(const std::vector<float>& rest, const std::vector<float>& weights,
                      uint32_t n, uint32_t n_bones);
    bool store_pose(uint32_t slot, const std::vector<float>& pose);  // B*7 floats: [qw,qx,qy,qz, tx,ty,tz] per bone
    bool apply_pose(uint32_t slot);   // upload stored slot to pose_buf_, pose on next frame
    void toggle_pose();               // 'P' key: rest (slot 0) <-> wave (slot 1)
    bool skinned_active() const { return skinned_active_; }

private:
    bool create_instance();
    bool create_device();
    bool create_swapchain();
    bool create_render_pass();
    bool create_framebuffers();
    bool create_command_buffers();
    bool create_pipeline();
    bool create_buffers();
    bool compile_shaders();
    bool create_descriptor_sets();
    bool create_compute_pipeline();

    void record_command_buffer(VkCommandBuffer cb);
    void resize(uint32_t w, uint32_t h);
    void ensure_capture_staging();
    bool create_sort_pipeline();
    void ensure_sort_buffers(uint32_t count);
    void destroy_sort_resources();
    bool create_skin_pipeline();
    void destroy_skin_resources();
    void upload_buffer(const void* data, VkDeviceSize size, VkBufferUsageFlags usage,
                       VkBuffer& buf, VkDeviceMemory& mem);
    void create_depth_resources();
    void destroy_depth_resources();
    void create_offscreen();
    VkCommandBuffer begin_single_time_cmd();
    void end_single_time_cmd(VkCommandBuffer cb);
    uint32_t find_mem_type(uint32_t types, VkMemoryPropertyFlags flags);

    VkInstance         instance_      = VK_NULL_HANDLE;
    VkPhysicalDevice   phys_dev_      = VK_NULL_HANDLE;
    VkDevice           device_        = VK_NULL_HANDLE;
    VkQueue            queue_         = VK_NULL_HANDLE;
    VkSurfaceKHR       surface_       = VK_NULL_HANDLE;
    VkSwapchainKHR     swapchain_     = VK_NULL_HANDLE;
    VkFormat           swap_fmt_      = VK_FORMAT_B8G8R8A8_UNORM;
    VkExtent2D         extent_        = {1920, 1080};

    VkRenderPass       render_pass_   = VK_NULL_HANDLE;
    VkPipeline         pipeline_      = VK_NULL_HANDLE;
    VkPipelineLayout   pipeline_layout_= VK_NULL_HANDLE;
    VkDescriptorSetLayout desc_layout_= VK_NULL_HANDLE;
    VkDescriptorPool   desc_pool_     = VK_NULL_HANDLE;
    std::vector<VkDescriptorSet> desc_sets_;

    // Validation layer callback
    VkDebugReportCallbackEXT debug_cb_ = VK_NULL_HANDLE;
    // Command pool for single-time uploads
    VkCommandPool cmd_pool_ = VK_NULL_HANDLE;

    // Buffers
    VkBuffer pos_buf_       = VK_NULL_HANDLE;
    VkBuffer vel_buf_       = VK_NULL_HANDLE;
    VkBuffer acc_buf_       = VK_NULL_HANDLE;
    VkDeviceMemory pos_mem_, vel_mem_, acc_mem_;
    VkBuffer img_buf_       = VK_NULL_HANDLE;
    VkDeviceMemory img_mem_;

    // Shader modules
    VkShaderModule comp_mod_= VK_NULL_HANDLE;
    VkShaderModule vert_mod_= VK_NULL_HANDLE;
    VkShaderModule frag_mod_= VK_NULL_HANDLE;

    // Compute pipeline
    VkPipeline                    compute_pipeline_     = VK_NULL_HANDLE;
    VkPipelineLayout              compute_pipeline_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout         compute_desc_layout_  = VK_NULL_HANDLE;
    VkDescriptorPool              compute_desc_pool_    = VK_NULL_HANDLE;
    std::vector<VkDescriptorSet>  compute_desc_sets_;

    std::vector<VkFramebuffer> frames_;
    std::vector<VkImage>        swap_imgs_;
    std::vector<VkImageView>    img_views_;
    std::vector<VkCommandBuffer> cmd_bufs_;
    std::vector<VkSemaphore>     draw_sem_, flush_sem_;
    std::vector<VkFence>         fences_;

    uint32_t image_idx_ = 0;
    uint32_t n_ = 0;
    bool dirty_ = true;   // re-upload positions when count or params change
    EngineConfig cfg_;
    VkBuffer params_buf_     = VK_NULL_HANDLE;
    VkDeviceMemory params_mem_  = VK_NULL_HANDLE;
    VkBuffer comp_params_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory comp_params_mem_ = VK_NULL_HANDLE;

    // Offscreen render target for splat pass (headless: /frame never depends on the window)
    VkImage  rt_image_     = VK_NULL_HANDLE;
    VkDeviceMemory rt_mem_ = VK_NULL_HANDLE;
    VkImageView rt_view_   = VK_NULL_HANDLE;
    VkRenderPass rt_render_pass_ = VK_NULL_HANDLE;
    VkFramebuffer rt_framebuffer_ = VK_NULL_HANDLE;

    // Depth attachment (front/back occlusion for the splats)
    VkImage        depth_image_ = VK_NULL_HANDLE;
    VkDeviceMemory depth_mem_   = VK_NULL_HANDLE;
    VkImageView    depth_view_  = VK_NULL_HANDLE;

    // ── membrane + frame capture state ───────────────────────────────────────────
    std::string membrane_term_;
    std::atomic<bool> capture_requested_{false};
    std::atomic<bool> capture_ready_{false};
    std::mutex capture_mutex_;
    std::vector<uint8_t> capture_rgba_;
    uint32_t capture_w_ = 0, capture_h_ = 0;
    VkBuffer capture_staging_ = VK_NULL_HANDLE;
    VkDeviceMemory capture_staging_mem_ = VK_NULL_HANDLE;
    VkDeviceSize capture_staging_size_ = 0;

    // ── GPU bitonic sort (back-to-front splat ordering, no CPU in the per-frame path) ──
    VkShaderModule        sort_mod_ = VK_NULL_HANDLE;
    VkPipeline            sort_pipe_ = VK_NULL_HANDLE;
    VkPipelineLayout      sort_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout sort_desc_layout_ = VK_NULL_HANDLE;
    VkDescriptorPool      sort_desc_pool_ = VK_NULL_HANDLE;
    VkDescriptorSet       sort_desc_set_ = VK_NULL_HANDLE;
    VkBuffer keys_buf_ = VK_NULL_HANDLE, sort_idx_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory keys_mem_, sort_idx_mem_;
    uint32_t sort_count_ = 0;   // real N
    uint32_t sort_padded_ = 0;  // padded N (power of two)
    bool sort_ready_ = false;

    // ── GPU skinning state (skin.comp: rest + weights + pose -> pos_buf_) ─────────
    VkShaderModule        skin_mod_ = VK_NULL_HANDLE;
    VkPipeline            skin_pipe_ = VK_NULL_HANDLE;
    VkPipelineLayout      skin_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout skin_desc_layout_ = VK_NULL_HANDLE;
    VkDescriptorPool      skin_desc_pool_ = VK_NULL_HANDLE;
    VkDescriptorSet       skin_desc_set_ = VK_NULL_HANDLE;
    VkBuffer rest_buf_ = VK_NULL_HANDLE, skin_w_buf_ = VK_NULL_HANDLE, pose_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory rest_mem_ = VK_NULL_HANDLE, skin_w_mem_ = VK_NULL_HANDLE, pose_mem_ = VK_NULL_HANDLE;
    std::map<uint32_t, std::vector<float>> pose_slots_;  // slot -> B*7 pose deltas
    uint32_t skin_count_ = 0;      // N (matches the loaded skin)
    uint32_t skin_bones_ = 0;      // B
    uint32_t skin_cur_slot_ = 0;   // last applied slot (for the 'P' toggle)
    bool skinned_active_ = false;  // true after load_skinned; /membrane_bin clears it
    bool skin_pose_dirty_ = false; // dispatch skin.comp on the next frame

    // ── triangle mesh rendering ──────────────────────────────────────────────
    bool create_triangle_pipeline();
    VkShaderModule tri_vert_mod_ = VK_NULL_HANDLE, tri_frag_mod_ = VK_NULL_HANDLE;
    VkPipeline      tri_pipeline_ = VK_NULL_HANDLE;   // reuses pipeline_layout_
    VkBuffer        tri_vbuf_ = VK_NULL_HANDLE, tri_ibuf_ = VK_NULL_HANDLE;
    VkDeviceMemory  tri_vmem_, tri_imem_;
    uint32_t        tri_idx_count_ = 0;
    bool            has_mesh_ = false;
    // Offscreen depth attachment (for triangle depth testing)
    VkImage         rt_depth_image_ = VK_NULL_HANDLE;
    VkDeviceMemory  rt_depth_mem_   = VK_NULL_HANDLE;
    VkImageView     rt_depth_view_  = VK_NULL_HANDLE;
    void destroy_triangle_resources();
};
