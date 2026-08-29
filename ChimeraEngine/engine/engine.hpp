#pragma once
#include <vulkan/vulkan.h>
#include <vector>
#include <string>
#include <mutex>
#include <atomic>
#include <chrono>
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
    // Nothing to draw: frame() early-returns in this state — the main loop must
    // pace itself instead of spinning a core at millions of FPS (B5).
    bool idle() const { return n_ == 0 && !has_mesh_; }

    // ── membrane streaming (the C++ engine is the emission target) ──────────────
    bool load_membrane(const std::string& term, const std::vector<float>& pos, uint32_t count);
    void set_camera(float radius, float theta, float phi);
    void request_capture() { capture_ready_.store(false); capture_requested_.store(true); }
    bool capture_ready() const { return capture_ready_.load(); }
    bool capture_frame(std::vector<uint8_t>& out_rgba, uint32_t& w, uint32_t& h);

    // ── triangle mesh rendering (depth-tested opaque Lambert) ────────────────
    bool load_mesh(const std::vector<float>& verts, const std::vector<uint32_t>& indices,
                   uint32_t vcount, uint32_t icount);
    // Animation driver path: memcpy new posed vertices into the persistently
    // mapped host-visible vertex buffer — no GPU idle, no buffer recreate, so
    // streaming poses at driver rate never stalls the render/input loop.
    // Returns false if the mesh layout changed (caller must full-load).
    bool update_mesh(const std::vector<float>& verts9, uint32_t vcount);
    // ── THE HINGE LIVES IN THE ENGINE (operator decree 2026-08-28) ─────────
    // The knee pose is an engine-internal state on the engine's own clock,
    // not a Python stream: per frame, each vertex near the joint rotates by
    // theta(t) * w_i about the measured joint (J, n) — the same skin-moving
    // law the operator approved, computed at render rate with zero network
    // in the loop. Python's whole job is ONE setup POST with the weights.
    bool set_hinge(const std::vector<float>& wL, const std::vector<float>& wR,
                   const float JL[3], const float JR[3], const float axis[3],
                   float romL, float romR, float period, float phaseR);
    void stop_hinge();
    void pose_hinge();   // per-frame, after the frame fence wait
    bool hinge_active() const { return hinge_active_; }

    // ── THE WATER SOLVER ON THE CA FIELD (B15 — port of .tmp/tri_water.py) ──
    // Order-consistent Gauss-Seidel: per-color parallel dispatches, sequential
    // across colors — provably identical to the CPU reference's sequential
    // canonical sweep. float64 shader math, integer volumes, injection table
    // as data (no RNG in the runtime).
    struct WaterUpload {
        uint32_t n_cells = 0, n_edges = 0, n_colors = 0;
        double Q = 0, G = 0, c_local = 0;
        std::vector<double> areas, bed, k_e, l_ij;
        std::vector<int32_t> V0, eij;
        std::vector<uint32_t> occ, color_start, inj, edge_active;  // inj: pairs (cell, count)
    };
    bool load_water(const WaterUpload& up);
    // Runs n_macro macro-steps at dt_macro; records V after each step for
    // readback. Returns (final_sum, final_min).
    bool water_run(uint32_t n_macro, double dt_macro, int64_t& sum_out, int64_t& min_out);
    bool water_download(std::vector<int32_t>& out_states, uint32_t& n_states, uint32_t& n_cells);
    // ── THE WATER CLOCK (H4: macro steps on the engine's clock, CA-field) ──
    // Set from the HTTP thread, consumed on the render thread inside frame():
    // while water_clock_on_, every frame records water_clock_steps_per_frame_
    // macro steps with a CONSTANT source (a river's source doesn't stop — no
    // finite upload table). States buffer slot 0 always holds the latest V so
    // /water_state stays a verification endpoint; w_states_n_ never advances
    // in clock mode (no cap exhaustion).
    std::atomic<bool>     water_clock_on_{false};
    std::atomic<uint32_t> water_clock_steps_per_frame_{1};
    std::atomic<double>   water_clock_dt_{0.01};
    std::atomic<int32_t>  water_clock_inj_target_{-1};
    std::atomic<int32_t>  water_clock_inj_count_{0};
    std::atomic<uint64_t> water_clock_steps_total_{0};   // bookkeeping (replaces w_states_n_)
    // ── W4 surface displacement render (the visible river) ──
    // The water surface IS the substrate triangulation, displaced: cell t ==
    // whole-mesh face water_vis_tri_base_ + t (proven by .tmp/water_align_check.py).
    std::atomic<bool>     water_vis_on_{false};
    std::atomic<uint32_t> water_vis_tri_base_{0};
    // DEBUG: read back the indirect command + a slice of the water vertex buffer
    // (packed: [4 u32 indirect][floats...] as int32) — the W4 bring-up probe.
    bool water_vis_debug(std::vector<int32_t>& out, uint32_t max_floats);

    // ── THE GAIT CPG ON THE CA FIELD (H7 stage 2 — port of .tmp/gait_ref.py) ──
    // 8 oscillators, Owaki surrogate load + Sakaguchi coupling, fixed-order RK4
    // at dt = 1e-3, float64 pinned schedule — the bit-exactness gate compares
    // the recorded phase ring against the golden CPU run. The shader's sin/cos
    // is an op-for-op port of ucrtbase.dll's FMA path (what np.sin/np.cos/
    // math.sin all execute on this machine — measured).
    bool load_gait(const std::vector<double>& consts, const std::vector<int32_t>& edges,
                   const double phi0[8], const double theta0[2]);
    // Copies the whole phase-record ring to the readback buffer and out.
    bool gait_download(std::vector<double>& out_ring);
    std::atomic<bool>     gait_on_{false};
    std::atomic<uint32_t> gait_steps_per_frame_{3};
    std::atomic<double>   gait_omega_{7.853981633974483};   // 2.5*pi (omega_ref)
    std::atomic<uint64_t> gait_steps_total_{0};
    bool gait_loaded() const { return gait_loaded_; }
    // Latest commanded knee angles (deg), written by the gait kernel into a
    // host-visible mirror; read per frame for the hinge pose + /gait status.
    void gait_theta(double& tL, double& tR) const;

    // ── VOLP-ARAP KNEE KERNEL (H13 — the blend's successor, agent_logs/kimi/volp_arap_01.md)
    // The SHIP-path law as ONE compute dispatch per frame: bi-Laplacian smooth
    // ARAP (lam=0.05, uniform Laplacian) + in-solve Lagrange multiplier on
    // Sigma V = V_rest (Schur row inside the solve), unified two-knee system,
    // precomputed dense inverse (A_ff is theta-independent), M fixed damped
    // outer iterations (omega=0.5, derived). Tier-1b: fixed order, no atomics
    // in the value path; f32 — not bit-exact vs the f64 CPU golden (boundary
    // named; the gate measures the deviation). When volp_mode_ == 1 the hinge
    // GPU dispatch is replaced by this kernel (blend stays behind the flag).
    bool load_volp(const std::vector<uint8_t>& blob);
    // Debug/verification readback: the full posed vertex buffer (stride 9).
    bool volp_download_mesh(std::vector<float>& out);
    std::atomic<int>      volp_mode_{1};            // 0 = blend, 1 = volp (default SHIP: H13 gates green)
    std::atomic<bool>     volp_manual_{false};      // theta override (verification)
    std::atomic<float>    volp_thL_{0.f}, volp_thR_{0.f};
    std::atomic<uint32_t> volp_M_{8};               // derived default (volp_track.json)
    std::atomic<bool>     volp_cold_{true};         // cold-start next dispatch
    bool volp_loaded() const { return volp_loaded_; }
    const float* volp_stats() const { return static_cast<const float*>(volp_stats_map_); }

    // Overlay slot: a second mesh drawn after the main one, always FILL
    // (used for the bone axis while the main mesh is in wireframe mode).
    bool load_overlay(const std::vector<float>& verts, const std::vector<uint32_t>& indices,
                      uint32_t vcount, uint32_t icount);
    void set_mesh_mode(uint32_t m) { mesh_mode_ = m; }

    // ── FROST decode (H9): the trained per-triangle MLP as an integer kernel ──
    // .tmp/frost_decode_ref.py is the golden fixed-point reference;
    // shaders/frost_decode.comp is its bit-exact port. The decoded per-triangle
    // relit RGB (Q16 int32) lives in a dedicated color SSBO read by the frost
    // fragment shader via gl_PrimitiveID — the mesh's welded/shared vertices
    // cannot carry flat per-triangle colors, and the vertex color channel is
    // load-bearing for the stock Lambert path.
    bool load_frost(const uint8_t* blob, size_t size);
    // E1: upload the measured eye classification (2092 u32; 0 sclera / 1 iris / 2 pupil).
    bool set_eye_class(const std::vector<uint32_t>& cls);
    // ── H15: the all-joints articulation (the skeleton SHOW) ────────────────
    // Per-vertex dominant joint + weight (the factory's distal sets); the
    // engine sweeps every joint through its derived ROM on the render clock.
    bool load_joints(const std::vector<uint8_t>& blob);
    std::atomic<int>      joints_on_{0};          // 1 = the show owns the pose
    bool                  joints_loaded() const { return joints_loaded_; }
    std::string           joints_status() const;
    void frost_rebind();                     // mesh buffers recreated -> rebind (like W4)
    // Arm + finish a debug snapshot (bit-exactness verification): the next
    // dispatched frame also writes the 14 kernel inputs per triangle; after
    // that frame, frost_finish_snapshot readbacks colors (F*3) + inputs (F*14).
    std::atomic<bool>     frost_on_{false};
    std::atomic<bool>     frost_dbg_arm_{false};
    std::atomic<double>   frost_light_x_{0.35}, frost_light_y_{0.8}, frost_light_z_{0.45};
    std::atomic<uint64_t> frost_frame_{0};   // decode dispatches since load
    std::atomic<int32_t>  frost_vq_[3] = {{0},{0},{0}};   // published Q30 dirs
    std::atomic<int32_t>  frost_lq_[3] = {{0},{0},{0}};   // (verification reads these)
    bool frost_loaded_ = false;
    uint32_t frost_tris() const { return f_n_tris_; }
    bool frost_coopvec_present_ = false;     // probed at load_frost (logged, inactive)
    bool frost_snapshot_pending() const { return frost_dbg_copy_recorded_; }
    bool frost_finish_snapshot(std::vector<int32_t>& out);  // [colors F*3][inputs F*14]

    // ── GPU skinning (LBS over the 3DGS splats, skin.comp) ──────────────────────
    bool load_skinned(const std::vector<float>& rest, const std::vector<float>& weights,
                      uint32_t n, uint32_t n_bones);
    bool store_pose(uint32_t slot, const std::vector<float>& pose);  // B*7 floats: [qw,qx,qy,qz, tx,ty,tz] per bone
    bool apply_pose(uint32_t slot);   // upload stored slot to pose_buf_, pose on next frame
    void toggle_pose();               // 'P' key: rest (slot 0) <-> wave (slot 1)
    bool skinned_active() const { return skinned_active_; }

private:
    // H15 joints kernel state
    bool            joints_loaded_ = false;
    uint32_t        j_n_verts_ = 0, j_n_joints_ = 0;
    std::vector<std::string> j_names_;
    std::vector<float> j_rom_;                  // per joint [ext, flex] (radians)
    VkBuffer        j_assign_buf_ = VK_NULL_HANDLE, j_w_buf_ = VK_NULL_HANDLE,
                    j_state_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory  j_assign_mem_ = VK_NULL_HANDLE, j_w_mem_ = VK_NULL_HANDLE,
                    j_state_mem_ = VK_NULL_HANDLE;
    void*           j_state_map_ = nullptr;      // host-visible: J/axis/theta per joint
    VkShaderModule  joints_mod_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout joints_dsl_ = VK_NULL_HANDLE;
    VkPipelineLayout joints_layout_ = VK_NULL_HANDLE;
    VkPipeline      joints_pipe_ = VK_NULL_HANDLE;
    VkDescriptorPool joints_desc_pool_ = VK_NULL_HANDLE;
    VkDescriptorSet joints_desc_set_ = VK_NULL_HANDLE;
    std::chrono::steady_clock::time_point joints_t0_;
    float           j_sweep_period_ = 4.0f;      // seconds per joint in the show

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
    VkDebugUtilsMessengerEXT debug_messenger_ = VK_NULL_HANDLE;
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
    // Per-flight-slot camera UBOs, host-visible + persistently mapped: the old
    // path created+destroyed a staging buffer and did vkQueueWaitIdle EVERY
    // FRAME for the camera upload (the frame-time killer).
    static const uint32_t MAX_SLOT = 2;
    VkBuffer       params_ubo_[2]  = {VK_NULL_HANDLE, VK_NULL_HANDLE};
    VkDeviceMemory params_umem_[2] = {VK_NULL_HANDLE, VK_NULL_HANDLE};
    void*          params_umap_[2] = {nullptr, nullptr};
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
    VkPipeline      tri_wire_pipeline_ = VK_NULL_HANDLE; // same shaders, VK_POLYGON_MODE_LINE
    uint32_t        mesh_mode_ = 0;   // 0 = fill, 1 = wire only, 2 = fill + wire overlay
    VkBuffer        tri_vbuf_ = VK_NULL_HANDLE, tri_ibuf_ = VK_NULL_HANDLE;
    VkDeviceMemory  tri_vmem_, tri_imem_;
    void*           tri_vmap_ = nullptr;      // persistent map of the STAGING buffer (host-visible)
    size_t          tri_vfloats_ = 0;         // floats in the current vertex payload
    VkBuffer        tri_staging_buf_ = VK_NULL_HANDLE;  // CPU writes here; copied to device-local tri_vbuf_
    VkDeviceMemory  tri_staging_mem_ = VK_NULL_HANDLE;
    std::vector<float> mesh_cpu_;             // CPU copy of the last full-loaded mesh (hinge rest snapshot)
    void mesh_upload(const float* data, size_t floats);  // staging memcpy + transfer to device
    // water solver state (B15)
    bool            water_loaded_ = false;
    uint32_t        w_n_cells_ = 0, w_n_edges_ = 0, w_n_colors_ = 0;
    double          w_Q_ = 0, w_G_ = 0, w_c_local_ = 0;
    std::vector<uint32_t> w_color_start_;
    std::vector<uint32_t> w_inj_;              // pairs (cell, count)
    uint32_t        w_states_cap_ = 0, w_states_n_ = 0;
    VkBuffer        w_V_buf_ = VK_NULL_HANDLE, w_depth_buf_ = VK_NULL_HANDLE,
                    w_areas_buf_ = VK_NULL_HANDLE, w_bed_buf_ = VK_NULL_HANDLE,
                    w_eij_buf_ = VK_NULL_HANDLE, w_ke_buf_ = VK_NULL_HANDLE,
                    w_lij_buf_ = VK_NULL_HANDLE, w_qe_buf_ = VK_NULL_HANDLE,
                    w_eactive_buf_ = VK_NULL_HANDLE,
                    w_occ_buf_ = VK_NULL_HANDLE, w_states_buf_ = VK_NULL_HANDLE,
                    w_readback_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory  w_V_mem_ = VK_NULL_HANDLE, w_depth_mem_ = VK_NULL_HANDLE,
                    w_areas_mem_ = VK_NULL_HANDLE, w_bed_mem_ = VK_NULL_HANDLE,
                    w_eij_mem_ = VK_NULL_HANDLE, w_ke_mem_ = VK_NULL_HANDLE,
                    w_lij_mem_ = VK_NULL_HANDLE, w_qe_mem_ = VK_NULL_HANDLE,
                    w_eactive_mem_ = VK_NULL_HANDLE,
                    w_occ_mem_ = VK_NULL_HANDLE, w_states_mem_ = VK_NULL_HANDLE,
                    w_readback_mem_ = VK_NULL_HANDLE;
    void*           w_readback_map_ = nullptr;
    VkShaderModule  w_depth_mod_ = VK_NULL_HANDLE, w_color_mod_ = VK_NULL_HANDLE, w_occ_mod_ = VK_NULL_HANDLE;
    VkPipeline      w_depth_pipe_ = VK_NULL_HANDLE, w_color_pipe_ = VK_NULL_HANDLE, w_occ_pipe_ = VK_NULL_HANDLE;
    VkPipelineLayout w_depth_layout_ = VK_NULL_HANDLE, w_color_layout_ = VK_NULL_HANDLE, w_occ_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout w_depth_dsl_ = VK_NULL_HANDLE, w_color_dsl_ = VK_NULL_HANDLE, w_occ_dsl_ = VK_NULL_HANDLE;
    VkDescriptorPool w_desc_pool_ = VK_NULL_HANDLE;
    VkDescriptorSet w_depth_set_ = VK_NULL_HANDLE, w_color_set_ = VK_NULL_HANDLE, w_occ_set_ = VK_NULL_HANDLE;
    VkFence         w_fence_ = VK_NULL_HANDLE;
    // Records ONE macro step (inject+depth pre-pass -> per-color Gauss-Seidel ->
    // occ post-pass, barrier-separated) into an EXISTING command buffer — no
    // submit/fence/readback. Shared by water_run (batch path) and the clock.
    void water_record_macro_step(VkCommandBuffer cb, double dt_macro,
                                 int32_t inj_target, int32_t inj_count);
    // ── W4 water-vis resources (displaced-surface render) ──
    VkShaderModule  w_vis_mod_ = VK_NULL_HANDLE;
    VkPipeline      w_vis_pipe_ = VK_NULL_HANDLE;
    VkPipelineLayout w_vis_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout w_vis_dsl_ = VK_NULL_HANDLE;
    VkDescriptorSet w_vis_set_ = VK_NULL_HANDLE;   // 4th set out of w_desc_pool_
    VkBuffer        w_vis_vbuf_ = VK_NULL_HANDLE, w_vis_indirect_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory  w_vis_vmem_ = VK_NULL_HANDLE, w_vis_indirect_mem_ = VK_NULL_HANDLE;
    uint32_t        w_vis_cap_verts_ = 0;          // 3 * n_cells
    bool            water_vis_desc_dirty_ = false; // mesh buffers recreated -> rebind
    void            water_vis_rebind();            // (re)point the vis set at the live mesh buffers
    bool            hinge_active_ = false;
    std::vector<float> hinge_rest_;           // rest vertex records (stride 9)
    std::vector<float> hinge_wL_, hinge_wR_;  // per-vertex blend weights
    float           hinge_JL_[3] = {}, hinge_JR_[3] = {}, hinge_axis_[3] = {};
    float           hinge_romL_ = 0.f, hinge_romR_ = 0.f;
    float           hinge_period_ = 4.f, hinge_phaseR_ = 3.14159265f;
    std::chrono::steady_clock::time_point hinge_t0_{};
    // GPU hinge kernel (the CA-field path): rest state + weights as SSBOs,
    // pose computed by hinge.comp into the vertex buffer each frame.
    VkShaderModule  hinge_mod_ = VK_NULL_HANDLE;
    VkPipeline      hinge_pipe_ = VK_NULL_HANDLE;
    VkPipelineLayout hinge_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout hinge_desc_layout_ = VK_NULL_HANDLE;
    VkDescriptorPool hinge_desc_pool_ = VK_NULL_HANDLE;
    VkDescriptorSet  hinge_desc_set_ = VK_NULL_HANDLE;
    VkBuffer        hinge_rest_buf_ = VK_NULL_HANDLE, hinge_wL_buf_ = VK_NULL_HANDLE, hinge_wR_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory  hinge_rest_mem_ = VK_NULL_HANDLE, hinge_wL_mem_ = VK_NULL_HANDLE, hinge_wR_mem_ = VK_NULL_HANDLE;

    // gait CPG state (H7 stage 2)
    bool            gait_loaded_ = false;
    uint32_t        gait_ring_cap_ = 262144;      // 262144 steps * 8 f64 = 16 MiB
    VkShaderModule  gait_mod_ = VK_NULL_HANDLE;
    VkPipeline      gait_pipe_ = VK_NULL_HANDLE;
    VkPipelineLayout gait_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout gait_desc_layout_ = VK_NULL_HANDLE;
    VkDescriptorPool gait_desc_pool_ = VK_NULL_HANDLE;
    VkDescriptorSet  gait_desc_set_ = VK_NULL_HANDLE;
    VkBuffer        gait_consts_buf_ = VK_NULL_HANDLE, gait_edges_buf_ = VK_NULL_HANDLE;
    VkBuffer        gait_phase_buf_ = VK_NULL_HANDLE, gait_ring_buf_ = VK_NULL_HANDLE;
    VkBuffer        gait_theta_buf_ = VK_NULL_HANDLE, gait_ring_rb_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory  gait_consts_mem_ = VK_NULL_HANDLE, gait_edges_mem_ = VK_NULL_HANDLE;
    VkDeviceMemory  gait_phase_mem_ = VK_NULL_HANDLE, gait_ring_mem_ = VK_NULL_HANDLE;
    VkDeviceMemory  gait_theta_mem_ = VK_NULL_HANDLE, gait_ring_rb_mem_ = VK_NULL_HANDLE;
    void*           gait_theta_map_ = nullptr;    // host-visible f64[2]
    void*           gait_ring_rb_map_ = nullptr;  // host-visible ring readback
    // volp-ARAP kernel state (H13)
    bool            volp_loaded_ = false;
    uint32_t        volp_NF_ = 0, volp_NC_ = 0;
    VkShaderModule  volp_mod_ = VK_NULL_HANDLE;
    VkPipeline      volp_pipe_ = VK_NULL_HANDLE;
    VkPipelineLayout volp_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout volp_desc_layout_ = VK_NULL_HANDLE;
    VkDescriptorPool volp_desc_pool_ = VK_NULL_HANDLE;
    VkDescriptorSet  volp_desc_set_ = VK_NULL_HANDLE;
    VkBuffer        volp_hdr_buf_ = VK_NULL_HANDLE, volp_u_buf_ = VK_NULL_HANDLE,
                    volp_f_buf_ = VK_NULL_HANDLE, volp_x_buf_ = VK_NULL_HANDLE,
                    volp_sc_buf_ = VK_NULL_HANDLE, volp_st_buf_ = VK_NULL_HANDLE,
                    volp_rb_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory  volp_hdr_mem_ = VK_NULL_HANDLE, volp_u_mem_ = VK_NULL_HANDLE,
                    volp_f_mem_ = VK_NULL_HANDLE, volp_x_mem_ = VK_NULL_HANDLE,
                    volp_sc_mem_ = VK_NULL_HANDLE, volp_st_mem_ = VK_NULL_HANDLE,
                    volp_rb_mem_ = VK_NULL_HANDLE;
    void*           volp_stats_map_ = nullptr;    // host-visible f32[16]
    float           volp_last_thL_ = 0.f, volp_last_thR_ = 0.f;
    uint32_t        tri_idx_count_ = 0;
    bool            has_mesh_ = false;
    // ── FROST decode (H9) resources ──
    uint32_t        f_n_tris_ = 0, f_lut_len_ = 0;
    VkShaderModule  frost_mod_ = VK_NULL_HANDLE;
    VkPipeline      frost_pipe_ = VK_NULL_HANDLE;
    VkPipelineLayout frost_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout frost_dsl_ = VK_NULL_HANDLE;
    VkDescriptorPool frost_desc_pool_ = VK_NULL_HANDLE;
    VkDescriptorSet  frost_desc_set_ = VK_NULL_HANDLE;
    VkBuffer        f_lat_buf_ = VK_NULL_HANDLE, f_m_buf_ = VK_NULL_HANDLE,
                    f_w_buf_ = VK_NULL_HANDLE, f_ab_buf_ = VK_NULL_HANDLE,
                    f_lut_buf_ = VK_NULL_HANDLE, f_color_buf_ = VK_NULL_HANDLE,
                    f_dbg_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory  f_lat_mem_ = VK_NULL_HANDLE, f_m_mem_ = VK_NULL_HANDLE,
                    f_w_mem_ = VK_NULL_HANDLE, f_ab_mem_ = VK_NULL_HANDLE,
                    f_lut_mem_ = VK_NULL_HANDLE, f_color_mem_ = VK_NULL_HANDLE,
                    f_dbg_mem_ = VK_NULL_HANDLE;
    VkBuffer        f_color_rb_ = VK_NULL_HANDLE, f_dbg_rb_ = VK_NULL_HANDLE;
    VkDeviceMemory  f_color_rb_mem_ = VK_NULL_HANDLE, f_dbg_rb_mem_ = VK_NULL_HANDLE;
    void*           f_color_rb_map_ = nullptr, *f_dbg_rb_map_ = nullptr;
    // E1: the eye-class SSBO (2,092 u32: 0 sclera / 1 iris / 2 pupil)
    VkBuffer        f_eye_buf_ = VK_NULL_HANDLE;
    VkDeviceMemory  f_eye_mem_ = VK_NULL_HANDLE;

    bool            frost_desc_dirty_ = false;
    bool            frost_dbg_copy_recorded_ = false;
    // frost render path (frag reads the per-tri color SSBO via gl_PrimitiveID)
    VkShaderModule  tri_frost_frag_mod_ = VK_NULL_HANDLE;
    VkPipeline      tri_frost_pipeline_ = VK_NULL_HANDLE;
    VkPipelineLayout frost_render_layout_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout frost_frag_dsl_ = VK_NULL_HANDLE;
    VkDescriptorPool frost_frag_pool_ = VK_NULL_HANDLE;
    VkDescriptorSet  frost_frag_set_ = VK_NULL_HANDLE;
    bool            frost_render_ready_ = false;
    // Overlay slot (e.g. the bone axis): always FILL, drawn after the main mesh.
    VkBuffer        ov_vbuf_ = VK_NULL_HANDLE, ov_ibuf_ = VK_NULL_HANDLE;
    VkDeviceMemory  ov_vmem_, ov_imem_;
    uint32_t        ov_idx_count_ = 0;
    bool            has_overlay_ = false;
    // Offscreen depth attachment (for triangle depth testing)
    VkImage         rt_depth_image_ = VK_NULL_HANDLE;
    VkDeviceMemory  rt_depth_mem_   = VK_NULL_HANDLE;
    VkImageView     rt_depth_view_  = VK_NULL_HANDLE;
    void destroy_triangle_resources();
};
