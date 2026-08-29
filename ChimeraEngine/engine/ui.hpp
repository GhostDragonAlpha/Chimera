#pragma once
// ─────────────────────────────────────────────────────────────────────────────
// THE ENGINE STUDIO — the overlay that brings the workflow into the engine
// (docs/THE_ENGINE_STUDIO.md, groups A1/A2/B1/B2, operator request 2026-08-29).
//
// The one idea: the engine owns all LIVE state, the repo owns all GATE truth;
// the Studio is the JOIN of the two, drawn over the viewport. This module
// INVENTS NOTHING: every pixel it draws is read from the board file the repo's
// own tool writes (tools/studio_board.py <- docs/THE_BODY_PIPELINE.md) or from
// status lines the engine's own atomics produce in main.cpp.
//
// Presentation-layer law (Rule 0 for this build): the UI draws ONLY into the
// swapchain pass, never into rt_image_ — the dyad's /frame stays pixel-clean.
// ─────────────────────────────────────────────────────────────────────────────
#include <vulkan/vulkan.h>
#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct StudioStage {
    std::string id;       // "B0" .. "B10"
    std::string name;     // "ACQUIRE" ..
    std::string status;   // green | partial | next | pending | blocked | rolling
};

struct StudioBoard {
    std::vector<StudioStage> stages;
    std::string standing;     // the standing-rule line (computed by the tool, never edited)
    std::string updated;      // the pipeline doc's status-board date
    bool        loaded = false;
};

class StudioUI {
public:
    bool visible = false;    // F1 toggles; the viewport stays live underneath

    bool init(VkDevice dev, VkPhysicalDevice phys, VkFormat swap_fmt,
              uint32_t w, uint32_t h, uint32_t mem_type_host);
    void shutdown();

    // Swapchain-dependent resources (per-image framebuffers). Called at init and
    // on every resize() with the live image views + extent.
    bool create_swap_resources(const std::vector<VkImageView>& views, VkExtent2D ext);

    void set_board_file(const std::string& path) { board_path_ = path; }
    void set_fps(float fps, float ft_avg, float ft_max) { fps_ = fps; ft_avg_ = ft_avg; ft_max_ = ft_max; }
    void set_status_lines(const std::vector<std::string>& lines) { status_lines_ = lines; }
    const StudioBoard& board() const { return board_; }

    // ── input (WndProc is pumped on the render thread — no locking needed) ──
    void on_mouse_move(int x, int y);
    // Returns true when the UI consumed the press (a panel was hit) — the caller
    // must then NOT start a camera orbit/pan with that press.
    bool on_lbutton(int x, int y, bool down);
    bool wants_mouse(int x, int y);   // cursor over any panel rect?
    bool mouse_captured() const { return drag_kind_ != 0; }

    // Render thread: poll the board file (mtime, throttled), rebuild the draw
    // list, upload the vertex buffer. Called once per frame BEFORE recording.
    void prepare(uint32_t win_w, uint32_t win_h);
    // Record the UI draw into an open UI render pass on the swapchain image.
    void record(VkCommandBuffer cb);

    VkRenderPass render_pass() const { return rp_; }
    VkFramebuffer fb(uint32_t i) const { return (i < fbs_.size()) ? fbs_[i] : VK_NULL_HANDLE; }
    bool ok() const { return pipe_ != VK_NULL_HANDLE && font_view_ != VK_NULL_HANDLE; }

private:
    // ── draw list (immediate mode: rebuilt every frame) ──
    struct Vert { float x, y, u, v, r, g, b, a; };
    std::vector<Vert> verts_;
    void rect(float x, float y, float w, float h, float r, float g, float b, float a);
    void rect_outline(float x, float y, float w, float h, float t, float r, float g, float b, float a);
    void text(float x, float y, const std::string& s, float r, float g, float b, float a);

    // ── panels (A2: edge-docked, collapsible, drag-resizable — Blender's area law) ──
    struct Panel {
        float size;         // strip: height px; left/right: width px
        float min_size, max_frac;
        bool  collapsed;
    };
    Panel strip_{ 92.f, 26.f, 0.30f, false };   // B1: the stage strip (top, full width)
    Panel left_ { 300.f, 26.f, 0.45f, false };  // STUDIO panel (left, below the strip)
    Panel right_{ 330.f, 26.f, 0.45f, false };  // STATUS panel (right, below the strip)
    int   drag_kind_ = 0;   // 0 none, 1 strip border, 2 left border, 3 right border
    bool  hit_strip_title(int x, int y) const;
    bool  hit_left_title(int x, int y) const;
    bool  hit_right_title(int x, int y) const;
    void  layout(uint32_t w, uint32_t h, float out_rects[3][4]) const;  // strip, left, right

    // ── board file polling (the repo's gate truth, read never owned) ──
    std::string board_path_ = "studio_board.json";   // relative to the engine CWD
    StudioBoard board_;
    std::chrono::steady_clock::time_point last_poll_{};
    uint64_t last_mtime_ = 0;
    void poll_board();

    // ── status lines (the engine's own live state, composed in main.cpp) ──
    std::vector<std::string> status_lines_;
    float fps_ = 0.f, ft_avg_ = 0.f, ft_max_ = 0.f;

    // ── Vulkan resources ──
    VkDevice         dev_  = VK_NULL_HANDLE;
    VkPhysicalDevice phys_ = VK_NULL_HANDLE;
    uint32_t         mem_type_host_ = 0;
    VkExtent2D       ext_  = {1920, 1080};
    VkRenderPass     rp_   = VK_NULL_HANDLE;
    std::vector<VkFramebuffer> fbs_;
    VkPipelineLayout layout_ = VK_NULL_HANDLE;
    VkPipeline       pipe_   = VK_NULL_HANDLE;
    VkDescriptorSetLayout dsl_ = VK_NULL_HANDLE;
    VkDescriptorPool dpool_ = VK_NULL_HANDLE;
    VkDescriptorSet  dset_  = VK_NULL_HANDLE;
    // font atlas (GDI-rasterized monospace — no vendored font files, no deps)
    VkImage        font_img_  = VK_NULL_HANDLE;
    VkDeviceMemory font_mem_  = VK_NULL_HANDLE;
    VkImageView    font_view_ = VK_NULL_HANDLE;
    VkSampler      font_samp_ = VK_NULL_HANDLE;
    float          cell_w_ = 0.f, cell_h_ = 0.f;   // glyph cell px
    float          advance_ = 0.f;                  // monospace advance px
    int            ascent_ = 0;
    static const int ATLAS_COLS = 16, ATLAS_ROWS = 6;  // chars 32..127 (DEL slot = white)
    // dynamic vertex buffer (host-visible, persistently mapped; grown on demand)
    VkBuffer       vbuf_     = VK_NULL_HANDLE;
    VkDeviceMemory vmem_     = VK_NULL_HANDLE;
    void*          vmap_     = nullptr;
    VkDeviceSize   vcap_     = 0;
    bool ensure_vbuf(VkDeviceSize bytes);
    bool create_font_atlas();
    void uv_cell(int ch, float& u0, float& v0, float& u1, float& v1) const;
    void uv_white(float& u0, float& v0, float& u1, float& v1) const;
};
