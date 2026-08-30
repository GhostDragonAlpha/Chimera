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
#include <array>
#include <chrono>
#include <cstdint>
#include <functional>

struct StudioStage {
    std::string id;       // "B0" .. "B10"
    std::string name;     // "ACQUIRE" ..
    std::string status;   // green | partial | next | pending | blocked | rolling
    // B3: the stage's envelope, VERBATIM from docs/THE_BODY_PIPELINE.md (a panel
    // that paraphrases is a panel that lies)
    std::string law;        // the Law/method cell
    std::string tool;       // the referee tool cell
    std::string artifact;   // the output-artifact cell (with paths)
    std::string falsifier;  // the gate cell
    std::string cell;       // the Monkey-status cell (the verdict row)
    std::string spec_title; // the ### envelope's title, when the doc has one
    std::string spec;       // the numbered steps (the task envelope itself)
};

struct StudioBoard {
    std::vector<StudioStage> stages;
    std::string standing;     // the standing-rule line (computed by the tool, never edited)
    std::string updated;      // the pipeline doc's status-board date
    bool        loaded = false;
};

// C1: one row of the joints editor — the engine pushes this view every frame;
// the UI never owns pose state (ext/flex = the pack's derived ROM, degrees).
struct StudioJoint {
    std::string name;
    float ext = 0.f, flex = 0.f, theta = 0.f;
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

    // B3: the selected stage's panel (-1 = none, the left dock shows the menu).
    // Set by clicking a strip node (Hot id 100+i); read by /studio GET for agents.
    int  selected_stage() const { return selected_stage_; }
    std::string selected_stage_id() const;

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
    struct Vert { float x, y, u, v, r, g, b, a, flags; };  // flags: 0 font, 1 reel thumb (D3)
    std::vector<Vert> verts_;
    void rect(float x, float y, float w, float h, float r, float g, float b, float a);
    void rect_outline(float x, float y, float w, float h, float t, float r, float g, float b, float a);
    void text(float x, float y, const std::string& s, float r, float g, float b, float a);
    void line(float x0, float y0, float x1, float y1, float th,
              float r, float g, float b, float a);   // C1: the gizmo's axis (rotated quad)
    void thumb(float x, float y, float w, float h, int slot);   // D3: a reel tile's image
    // B3: greedy word-wrap at maxc columns (monospace: arithmetic); splits on
    // newlines first. Lines whose top is past y_max are NOT drawn, but the walk
    // continues — the returned y is where the text WOULD end, so callers can
    // detect clipping honestly. Returns the y of the NEXT free line.
    float text_wrap(float x, float y, const std::string& s, size_t maxc,
                    float r, float g, float b, float a, float y_max = 1e30f);

    // ── panels (A2: edge-docked, collapsible, drag-resizable — Blender's area law) ──
    struct Panel {
        float size;         // strip: height px; left/right: width px
        float min_size, max_frac;
        bool  collapsed;
    };
    Panel strip_{ 92.f, 26.f, 0.30f, false };   // B1: the stage strip (top, full width)
    Panel left_ { 300.f, 26.f, 0.45f, false };  // STUDIO panel (left, below the strip)
    Panel right_{ 330.f, 26.f, 0.45f, false };  // STATUS panel (right, below the strip)
    Panel bottom_{118.f, 26.f, 0.35f, false };  // D1: the TIMELINE (bottom, between left/right)
    Panel reel_ { 172.f, 26.f, 0.40f, false };  // D3: the REEL (above the timeline)
    int   drag_kind_ = 0;   // 0 none, 1 strip border, 2 left, 3 right, 4 bottom, 5 scrub playhead,
                            // 6 reel, 7 joint slider (C1), 8 docs scrollbar (E1)
    bool  hit_strip_title(int x, int y) const;
    bool  hit_left_title(int x, int y) const;
    bool  hit_right_title(int x, int y) const;
    bool  hit_bottom_title(int x, int y) const;
    bool  hit_reel_title(int x, int y) const;
    void  layout(uint32_t w, uint32_t h, float out_rects[5][4]) const;  // strip, left, right, bottom, reel

    // ── clickable controls (D1: rebuilt every frame by prepare, hit-tested on click) ──
    struct Hot { float x, y, w, h; int id; };   // id: 1 play/pause, 2 step-, 3 step+, 4 speed;
                                                // 100+i = strip node i (B3); 300+i = workspace row i,
                                                // 400+i = joint row i (C1: select = gizmo + paint)
                                                // 500+i = docs picker row i (E1)
    std::vector<Hot> hots_;
    float scrub_rect_[4] = {0, 0, 0, 0};        // the scrub bar's live rect
    int   selected_stage_ = -1;                 // B3: -1 none; click the same node again to close

    // ── C1: THE JOINTS EDITOR (the JOINTS workspace's left-dock mode) ──
    int   left_mode_ = 0;                       // 0 = board/menu (B3), 1 = joints editor
    std::vector<StudioJoint> joints_;           // the engine's per-frame push
    int   joints_owner_ui_ = 0;                 // 0 show, 1 edit (display only)
    int   joints_sel_ui_ = -1;                  // the engine's selected (gizmo+paint) joint
    std::vector<std::array<float, 4>> slider_tracks_;   // row i's track rect (prepare-owned)
    int   drag_joint_ = -1;                     // drag_kind_ 7: which slider is grabbed
    float slider_theta_at(int row, int x) const;        // linear map track-x -> theta (ROM-clamped)

    // ── C1: the gizmo — the selected joint's center/axis, projected by the engine ──
    bool        gizmo_vis_ = false;
    float       gizmo_[4] = {0, 0, 0, 0};       // x0,y0 (J) -> x1,y1 (J + axis * band RMS)
    std::string gizmo_label_;

    // ── E1: THE DOCS BROWSER (the DOCS workspace's left-dock mode, left_mode_ 2) ──
    // Read-only, verbatim, current with git: the file is re-read when its
    // mtime moves (1 Hz poll — the board's discipline). The UI READS the repo;
    // it never writes it. `fnv` is FNV-1a/64 over the file's exact bytes — the
    // verbatim proof the HTTP twin serves.
    struct DocsState {
        std::vector<std::string> paths;             // the menu's five (E1 names them)
        int      current = 0;
        std::string raw;                            // the file's exact bytes
        std::vector<std::string> lines;             // split on '\n'
        std::vector<std::string> display;           // re-wrapped to the dock width
        size_t   wrap_cols = 0;                     // the column count `display` was wrapped at
        uint64_t mtime = 0;
        uint64_t fnv = 0;
        float    scroll = 0.f;                      // in DISPLAY lines
        std::chrono::steady_clock::time_point last_poll{};
    };
    DocsState docs_;
    float    docs_scroll_max_ = 0.f;            // last prepared (visible-dependent)
    float    docs_sb_track_[4] = {0, 0, 0, 0};  // the scrollbar's live track rect
    float    docs_sb_thumb_[4] = {0, 0, 0, 0};  // ... and its live thumb rect
    void     docs_init();                       // fills `paths` (the menu's five, once)
    void     docs_poll();                       // mtime -> reload -> rewrap (1 Hz)
    void     docs_rewrap(size_t maxc);          // greedy, same law as text_wrap
    void     docs_clamp_scroll();

    // ── the show clock's view (D1: pushed by the Engine every frame — the UI never owns it) ──
    double clk_t_ = 0.0, clk_total_ = 0.0, clk_speed_ = 1.0, clk_theta_ = 0.0;
    bool   clk_playing_ = true;
    uint32_t clk_n_ = 0, clk_cur_ = 0;
    float  clk_period_ = 4.0f;
    std::string clk_name_;

public:
    // callbacks into the Engine (wired in Engine::init — the panel issues, the engine owns)
    std::function<void()>     cb_play_toggle_;
    std::function<void(int)>  cb_step_;          // ±1 frames of 1/240 s
    std::function<void()>     cb_speed_cycle_;
    std::function<void(double)> cb_scrub_;       // absolute time target
    // C1: the joints editor's intents — select toggles the gizmo+paint target;
    // a theta intent is an ownership claim (the editor takes the pose)
    std::function<void(int)>         cb_joint_select_;
    std::function<void(int, float)>  cb_joint_theta_;

    // C1: the engine's per-frame pushes (render thread; the UI draws, never owns)
    void set_joints_view(const std::vector<StudioJoint>& j, int owner, int selected) {
        joints_ = j; joints_owner_ui_ = owner; joints_sel_ui_ = selected;
    }
    void set_gizmo(bool vis, float x0, float y0, float x1, float y1, const std::string& label) {
        gizmo_vis_ = vis; gizmo_[0] = x0; gizmo_[1] = y0; gizmo_[2] = x1; gizmo_[3] = y1;
        gizmo_label_ = label;
    }
    int  left_mode() const { return left_mode_; }
    // C1: the layout space's font metrics — agents aim slider clicks from these
    // (the same discipline as B3's w/h: the UI publishes, never hides)
    float line_height() const { return cell_h_; }
    float advance() const { return advance_; }

    // ── E1: the docs browser's HTTP twin (agents read what the panel shows) ──
    bool        on_wheel(int x, int y, float delta);   // true = a panel took it
    int         docs_current() const { return docs_.current; }
    std::string docs_path() const;
    uint64_t    docs_mtime() const { return docs_.mtime; }
    uint64_t    docs_fnv() const { return docs_.fnv; }
    size_t      docs_line_count() const { return docs_.lines.size(); }
    size_t      docs_display_count() const { return docs_.display.size(); }
    float       docs_scroll() const { return docs_.scroll; }
    float       docs_scroll_max() const { return docs_scroll_max_; }
    void        docs_set(int idx);
    void        docs_set_scroll(float s);
    // E1: the hidden+idle path in Engine::frame() returns BEFORE prepare() —
    // without this the HTTP twins (board, docs) freeze the moment the overlay
    // is closed. 1 Hz each, cheap; the panels read the repo, never write it.
    void        idle_poll() { poll_board(); docs_poll(); }

    // ── F2/F3: THE CHROME — the status bar + HUD, drawn whether the overlay ──
    // is open or not ("always visible, overlay or no overlay"). Every number
    // is the engine's own state, pushed by the engine/main — the UI never
    // derives on its own. The strings served on /studio_chrome are the SAME
    // strings build_chrome() draws: the HTTP twin cannot drift from the glass.
    static constexpr float BAR_H = 24.f;
    static const int FT_RING = 120;             // the histogram's frame-time ring
    bool     bar_on_ = true;                    // F2 default ON; POST /studio_chrome toggles
    float    ft_ring_[FT_RING] = {};
    int      ft_ring_head_ = 0, ft_ring_n_ = 0;
    uint64_t ft_pushes_ = 0;                    // liveness proof for the twin
    std::string gpu_name_;                      // pushed once at device pick
    // F3 rows — pushed per frame by the engine; drawn only while the mode is live
    struct HudGait  { bool on = false; double lamL = 0, lamR = 0, thL = 0, thR = 0;
                      uint64_t steps = 0; double omega = 0; } hud_gait_;
    struct HudWater { bool on = false; uint64_t steps = 0; double dt = 0;
                      int32_t inj_t = -1, inj_c = 0; } hud_water_;
    // the chrome's drawn strings (build_chrome fills; the twin serves verbatim)
    std::string chrome_stage_, chrome_fps_, chrome_gpu_;
    std::vector<std::string> hud_rows_;
    void push_frame_time(float ms) {
        ft_ring_[ft_ring_head_] = ms;
        ft_ring_head_ = (ft_ring_head_ + 1) % FT_RING;
        if (ft_ring_n_ < FT_RING) ++ft_ring_n_;
        ++ft_pushes_;
    }
    void set_gpu_name(const std::string& s) { gpu_name_ = s; }
    void set_gait_hud(bool on, double lL, double lR, double tL, double tR,
                      uint64_t steps, double om) {
        hud_gait_.on = on; hud_gait_.lamL = lL; hud_gait_.lamR = lR;
        hud_gait_.thL = tL; hud_gait_.thR = tR;
        hud_gait_.steps = steps; hud_gait_.omega = om;
    }
    void set_water_hud(bool on, uint64_t steps, double dt, int32_t it, int32_t ic) {
        hud_water_.on = on; hud_water_.steps = steps; hud_water_.dt = dt;
        hud_water_.inj_t = it; hud_water_.inj_c = ic;
    }
    bool hud_show_on() const { return !joints_.empty() && clk_n_ > 0; }
    bool wants_chrome() const {
        return bar_on_ || hud_show_on() || hud_gait_.on || hud_water_.on;
    }
    std::string board_standing() const { return board_.standing; }
    void        build_chrome();               // the bar + HUD draw list (+ twin strings)
    float fps_f()    const { return fps_; }      // the twin reads the same
    float ft_avg_f() const { return ft_avg_; }   // numbers the bar draws
    float ft_max_f() const { return ft_max_; }

    void set_show_clock(double t, double total, bool playing, double speed,
                        uint32_t n, uint32_t cur, float period,
                        const std::string& name, double theta) {
        clk_t_ = t; clk_total_ = total; clk_playing_ = playing; clk_speed_ = speed;
        clk_n_ = n; clk_cur_ = cur; clk_period_ = period; clk_name_ = name; clk_theta_ = theta;
    }
    float scrub_time_at(int x) const;            // map a cursor x to a time on the bar

    // ── D3: THE REEL — every /frame grab lands here (the engine pushes; the UI draws) ──
    static const int REEL_MAX = 12, THUMB_W = 384, THUMB_H = 216;
    struct ReelTile { bool used = false; std::string l1, l2, l3; };
    // Render thread only. rgba = THUMB_W*THUMB_H*4 bytes, RGBA8. Slot = seq % REEL_MAX.
    void reel_push(const uint8_t* rgba, const std::string& l1,
                   const std::string& l2, const std::string& l3);
    int  reel_count() const { return reel_count_; }

private:

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
    // D3: ONE RGBA8 image — font cells up top (rgb=white, a=coverage), the
    // reel's 4x3 thumbnail grid below. One descriptor, one draw call.
    VkImage        font_img_  = VK_NULL_HANDLE;
    VkDeviceMemory font_mem_  = VK_NULL_HANDLE;
    VkImageView    font_view_ = VK_NULL_HANDLE;
    VkSampler      font_samp_ = VK_NULL_HANDLE;
    float          cell_w_ = 0.f, cell_h_ = 0.f;   // glyph cell px
    float          advance_ = 0.f;                  // monospace advance px
    int            ascent_ = 0;
    uint32_t       atlas_w_ = 0, atlas_h_ = 0;      // full image incl. thumb grid
    static const int ATLAS_COLS = 16, ATLAS_ROWS = 6;  // chars 32..127 (DEL slot = white)
    // D3: reel ring (CPU-side tile text + a persistently-mapped staging buffer
    // that each push copies into its atlas slot with a one-shot submit)
    ReelTile       tiles_[12];
    int            reel_count_ = 0;
    uint64_t       reel_seq_   = 0;
    VkBuffer       thumb_stage_     = VK_NULL_HANDLE;
    VkDeviceMemory thumb_stage_mem_ = VK_NULL_HANDLE;
    void*          thumb_stage_map_ = nullptr;
    void           thumb_uv(int slot, float& u0, float& v0, float& u1, float& v1) const;
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
