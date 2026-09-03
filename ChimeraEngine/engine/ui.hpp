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
#include <mutex>

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
    // E2: the deep link — the stage's own line numbers in the pipeline doc,
    // DERIVED by tools/studio_board.py (never hardcoded here): row_line = the
    // glance-table row; spec_line = the ### envelope's heading (-1 = none).
    int row_line = -1, spec_line = -1;
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

// 2026-08-31: one screen-space segment of the viewport reference frame, built
// from world points the ENGINE projected (project_world). An instrument, never matter.
struct StudioGridLine { float x0, y0, x1, y1, r, g, b, a; };

// 2026-09-02: one explicit FK segment projected by the engine. Parent links are
// authored by the rig topology, never inferred from spatial proximity.
struct StudioRigSegment { float x0, y0, x1, y1; bool selected; };

class StudioUI {
public:
    bool visible = true;     // default-ON (2026-09-01): a relaunch must not come up bare — F1 still toggles; the viewport stays live underneath

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
    int   cursor_x_ = -1, cursor_y_ = -1;  // last render-thread pointer position
    bool  marker_hover_ = false;            // D3: derived read-only timeline tooltip
    float marker_hover_x_ = 0.f, marker_hover_y_ = 0.f;
    double marker_hover_t_ = 0.0;
    int   marker_hover_kind_ = 0;
    std::string marker_hover_label_;
    bool  hit_strip_title(int x, int y) const;
    bool  hit_left_title(int x, int y) const;
    bool  hit_right_title(int x, int y) const;
    bool  hit_bottom_title(int x, int y) const;
    bool  hit_reel_title(int x, int y) const;
    void  layout(uint32_t w, uint32_t h, float out_rects[5][4]) const;  // strip, left, right, bottom, reel

    // ── clickable controls (D1: rebuilt every frame by prepare, hit-tested on click) ──
    struct Hot { float x, y, w, h; int id; float hit_t = 0.f; };  // id: 1 play/pause, 2 step-, 3 step+, 4 speed;
                                                // 100+i = strip node i (B3); 300+i = workspace row i,
                                                // 400+i = joint row i (C1: select = gizmo + paint)
                                                // 500+i = docs picker row i (E1)
                                                // 700+i = master key-mark diamond i (hit_t = key time)
                                                // 1000+i = Dope Sheet key diamond i (joint-aware recall)
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
    std::vector<StudioGridLine> grid_;                // the viewport reference frame
    std::vector<StudioRigSegment> rig_segments_;      // D8: projected FK links
    bool        rig_overlay_ui_ = true;              // engine-pushed toggle state
    bool        viewport_empty_ = false;        // nothing loaded — say so

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
        std::vector<int> display_src;               // E2: display line -> source line (the wrap map)
        int      pending_line = -1;                 // E2: a deep link awaiting resolution (source line)
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
    // the LIVE CLOCK's identity (2026-09-02): "joints" (the 19-joint show),
    // "hinge" (the knee march), "none". The buttons drive whichever is live.
    std::string clk_source_ = "none";
    float clk_hinge_period_ = 0.f;
    bool   hinge_live_ = false;
    uint32_t clk_n_ = 0, clk_cur_ = 0;
    float  clk_period_ = 4.0f;
    std::string clk_name_;

public:
    // callbacks into the Engine (wired in Engine::init — the panel issues, the engine owns)
    std::function<void()>     cb_play_toggle_;
    std::function<void(int)>  cb_step_;          // ±1 frames of 1/240 s
    std::function<void(int)>  cb_key_recall_;    // scrub to key i (h.w carries hit_t)
    std::function<void(int)>  cb_dope_key_recall_; // D9: recall key time + select keyed joint
    std::function<void()>     cb_key_save_;      // key the live clock time
    std::function<void(int)>  cb_key_delete_;    // G1: delete key by index
    std::function<void()>     cb_key_clear_;     // G1: clear all keys
    std::function<void()>     cb_speed_cycle_;
    std::function<void(double)> cb_scrub_;       // absolute time target
    // C1: the joints editor's intents — select toggles the gizmo+paint target;
    // a theta intent is an ownership claim (the editor takes the pose)
    std::function<void()>           cb_rig_toggle_;  // D8: toggle explicit FK overlay
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

    // ── THE VIEWPORT REFERENCE FRAME (2026-08-31 — the eye's #1 defect) ───────
    // An empty 3D viewport reads as BROKEN, not as empty: "no grid, no origin
    // axes ... it's indistinguishable from a crashed GL context. This is the
    // biggest fix you can make."
    //
    // A grid is a DECLARED INSTRUMENT, not a body: it is the viewport's frame of
    // reference, the way a Blender grid is. It must never be mistaken for matter,
    // so it is drawn by the UI in screen space, from world points the ENGINE
    // projected through its own camera (project_world) — one projection law, so
    // the grid cannot disagree with whatever is standing on it.
    void set_grid_lines(std::vector<StudioGridLine> lines) { grid_ = std::move(lines); }
    void set_rig_segments(std::vector<StudioRigSegment> segments, bool enabled) {
        rig_segments_ = std::move(segments); rig_overlay_ui_ = enabled;
    }
    bool rig_overlay() const { return rig_overlay_ui_; }
    size_t rig_segment_count() const { return rig_segments_.size(); }
    // honest emptiness: when there is genuinely nothing loaded, SAY SO in the
    // viewport instead of leaving a void the eye has to interpret.
    void set_viewport_empty(bool empty) { viewport_empty_ = empty; }
    int  left_mode() const { return left_mode_; }
    void set_left_mode(int m) { left_mode_ = m; selected_stage_ = -1; }
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
    // ── E2: DEEP LINKS — a stage's falsifier/spec row jumps the DOCS dock to
    // the membrane section that named it. The TARGET is the tool-derived line
    // (spec_line when the doc has a ### envelope, else the glance-table row);
    // the LANDING is resolved in prepare() through the live wrap map, so the
    // glass click and the /link twin land identically by construction.
    int         docs_link_line(int stage_index) const;  // the resolution law (-1 = no link)
    void        docs_link_stage(int stage_index);       // navigate: doc 0 + pending_line
    int         docs_top_src() const;                   // source line under the scroll's top
    float       link_hot_[4] = {0, 0, 0, 0};            // the envelope's link row rect (last prepared)
    // E1: the hidden+idle path in Engine::frame() returns BEFORE prepare() —
    // without this the HTTP twins (board, docs) freeze the moment the overlay
    // is closed. 1 Hz each, cheap; the panels read the repo, never write it.
    void        idle_poll() { poll_board(); docs_poll(); }

    // ── F2/F3: THE CHROME — the status bar + HUD, drawn whether the overlay ──
    // is open or not ("always visible, overlay or no overlay"). Every number
    // is the engine's own state, pushed by the engine/main — the UI never
    // derives on its own. The strings served on /studio_chrome are the SAME
    // strings build_chrome() draws: the HTTP twin cannot drift from the glass.
    // ── THE 2K SCALE (2026-08-31, operator decree + the eye's report) ──────────
    // "We will make this project run on a 2K monitor and the monitor resolution
    // should match the project in all efforts including the dyad." The eye, at
    // 2560x1440: "Text is too small for 2560x1440 ... most body text is one step
    // too small to be comfortable."
    //
    // Every layout number below is the DESIGN value — the one this UI was built
    // and read at, on a 1080p panel. Nothing is re-tuned for 2K; the window's own
    // height derives one factor and the design values are MULTIPLIED by it. The
    // proportion the eye approved at 1080p is thus preserved at any resolution,
    // which is the only defensible thing to preserve (choosing new pixel numbers
    // for 1440 would be taste, and taste is not ours to spend).
    //
    // Root cause of "too small": the font. advance_ and cell_h_ come straight
    // from GDI metrics for a fixed 16px Consolas, and every text position in this
    // UI is measured in multiples of those two numbers. Scale the font and the
    // whole layout follows — which is why this is one factor and not a hunt.
    static constexpr float DESIGN_H       = 1080.f;   // the height the design was read at
    static constexpr float DESIGN_FONT_PX = 16.f;     // the Consolas it was read at
    static constexpr float DESIGN_TITLE_H = 22.f;     // a collapsed panel's title bar
    float ui_scale_ = 1.f;                            // derived in prepare()
    float bar_h()   const { return BAR_H * ui_scale_; }
    float title_h() const { return DESIGN_TITLE_H * ui_scale_; }

    static constexpr float BAR_H = 24.f;   // DESIGN value at scale 1; use bar_h()
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
    // 2026-09-02, the zero-pixel probe: record()'s liveness, served on the twin.
    // The chrome strings can be fresh while the draw is dead — the twin MUST be
    // able to say which side of record() the chain breaks on.
    uint64_t rec_calls_ = 0, rec_draws_ = 0;
    uint64_t rec_bail_verts_ = 0, rec_bail_ok_ = 0, rec_bail_vbuf_ = 0;
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
        return bar_on_ || hud_show_on() || hud_gait_.on || hud_water_.on || console_open_;
    }
    std::string board_standing() const { return board_.standing; }
    void        build_chrome();               // the bar + HUD draw list (+ twin strings)
    float fps_f()    const { return fps_; }      // the twin reads the same
    float ft_avg_f() const { return ft_avg_; }   // numbers the bar draws
    float ft_max_f() const { return ft_max_; }

    // ── F1: THE CONSOLE — the HTTP API's interactive twin ──
    // A request line `METHOD /path [json]` — typed at the window or posted to
    // /console — enters ONE path (history + scrollback + the engine's worker
    // queue). The UI never executes; cb_console_ hands the line to the engine,
    // whose worker runs the SAME handler the HTTP server runs and pushes the
    // response back. While open the console captures the ENTIRE keyboard —
    // nothing leaks to the camera, the pose key, or the overlay toggle.
    bool        console_open_ = false;
    std::string console_input_;
    std::vector<std::string> console_history_;
    int         console_hist_nav_ = -1;         // -1 = editing the current line
    struct ConsoleEntry { std::string cmd, resp; bool done = false; };
    std::vector<ConsoleEntry> console_log_;     // the scrollback (capped at 200)
    std::function<void(const std::string&)> cb_console_;   // the engine owns execution
    void console_toggle() { console_open_ = !console_open_; console_hist_nav_ = -1; }
    bool console_open() const { return console_open_; }
    void console_char(int c);                   // WM_CHAR route (printables, BS, CR)
    void console_key(int vk);                   // UP/DOWN recall, ESCAPE closes
    void console_submit_line(const std::string& line);  // Enter AND POST /console — one path
    void console_result(const std::string& resp);       // engine -> UI, render thread
    void build_console();                       // draw list (called when open)

    // ── C4: THE OUTLINER (the SCENE workspace's left-dock mode, left_mode_ 4) ──
    // The engine's live systems as a list with working toggles — the Scene-dock
    // equivalent. The ENGINE composes the rows from its own atomics at read time
    // (one formatting site for the glass AND the /scene twin — no drift); a
    // toggle click routes through console_exec — the console's ONE PATH — so the
    // F4 recorder logs the inner endpoint's event like any mode flip.
    struct SceneRow { std::string id, label, detail; int state = 0; bool toggleable = false; };
    std::vector<SceneRow> scene_;
    std::vector<std::array<float, 4>> scene_row_rects_;   // prepare-owned (aiming)
    std::function<void(int)> cb_scene_toggle_;            // row index -> the engine
    void set_scene_view(std::vector<SceneRow> rows) { scene_ = std::move(rows); }
    const std::vector<SceneRow>& scene_view() const { return scene_; }
    const std::vector<std::array<float, 4>>& scene_rects() const { return scene_row_rects_; }

    // ── C2: THE INSPECTOR (the right dock, when an outliner row is selected) ──
    // The same live-view law applied to depth: the ENGINE composes the selected
    // atom's full state document at read time (one formatting site, shared with
    // the /inspect twin); the panel holds no properties of its own. Selection
    // is pure VIEW state (it mutates nothing in the scene), so it does not
    // route through the console — only state mutation does.
    int inspect_row_ = -1;                                 // pushed by the engine
    std::string inspect_id_, inspect_label_, inspect_hint_;
    std::vector<std::pair<std::string, std::string>> inspect_kv_;
    std::vector<std::array<float, 4>> scene_sel_rects_;   // label-rect aim map
    std::function<void(int)> cb_scene_select_;            // row index -> the engine
    void set_inspect_view(int row, std::string id, std::string label,
                          std::vector<std::pair<std::string, std::string>> kv,
                          std::string hint) {
        inspect_row_ = row; inspect_id_ = std::move(id); inspect_label_ = std::move(label);
        inspect_kv_ = std::move(kv); inspect_hint_ = std::move(hint);
    }
    const std::vector<std::array<float, 4>>& scene_sel_rects() const { return scene_sel_rects_; }

    // ── D6: CAMERA BOOKMARKS — named shots as chips under the HUD rows ──
    // A bookmark is a NAMED 8-float camera state (r, theta, phi, target xyz,
    // pan xy) owned by the ENGINE and persisted to camera_bookmarks.txt (CWD).
    // The engine pushes the name list every frame (one store for the glass AND
    // the /cameras twin); a chip click recalls, the "+" chip saves the live
    // camera with an auto name. Recall applies the full 8 floats — POST
    // /camera's r/theta/phi-only semantics would zero the operator's pan.
    std::vector<std::string> cam_marks_;
    std::vector<std::array<float, 4>> cam_mark_rects_;      // prepare-owned (aiming)
    std::array<float, 4> cam_save_rect_{0.f, 0.f, 0.f, 0.f};
    std::function<void(int)> cb_cam_recall_;                // index -> the engine
    std::function<void()> cb_cam_save_;
    void set_cam_view(std::vector<std::string> names) { cam_marks_ = std::move(names); }
    const std::vector<std::string>& cam_view() const { return cam_marks_; }
    const std::vector<std::array<float, 4>>& cam_rects() const { return cam_mark_rects_; }
    std::array<float, 4> cam_save_rect() const { return cam_save_rect_; }

    // ── D5: THE CAPTURE SESSION (the CAPTURE workspace's left-dock mode 5) ──
    // The engine composes the session document (capture_kv — one formatting
    // site, shared with GET /capture); the dock only draws it.
    std::vector<std::pair<std::string, std::string>> capture_kv_;
    void set_capture_view(std::vector<std::pair<std::string, std::string>> kv) {
        capture_kv_ = std::move(kv);
    }

    // ── F4: THE RECORDER's ring — the LOG stream (left dock mode 3) ──
    // The engine pushes each event the moment it happens; the dock draws the
    // tail, newest at the bottom. The FILE holds everything — the stream is
    // the live edge of the same lines, never a summary.
    struct LogLine { uint64_t seq; std::string t, kind, detail; };
    std::vector<LogLine> log_ring_;
    uint64_t log_total_ = 0;                    // the session's full count
    std::string log_file_;                      // the session file's name
    mutable std::mutex log_m_;                  // pushes arrive on the HTTP thread; draws on the render thread
    void log_push(uint64_t seq, uint64_t total, const std::string& t,
                  const std::string& kind, const std::string& detail);
    // wrapped-row cache: rebuilt ONLY when a line lands or the dock width
    // changes — re-wrapping 200 lines every frame spiked ft (chrome gate B)
    struct LogRow { std::string s; float r, g, b; };
    std::vector<LogRow> log_rows_;
    uint64_t log_rows_total_ = ~0ull;
    size_t   log_rows_maxc_  = 0;

    void set_show_clock(double t, double total, bool playing, double speed,
                        uint32_t n, uint32_t cur, float period,
                        const std::string& name, double theta,
                        const std::string& source = "joints", float hinge_period = 0.f) {
        clk_t_ = t; clk_total_ = total; clk_playing_ = playing; clk_speed_ = speed;
        clk_n_ = n; clk_cur_ = cur; clk_period_ = period; clk_name_ = name; clk_theta_ = theta;
        clk_source_ = source; clk_hinge_period_ = hinge_period;
        hinge_live_ = (source == "hinge");
        if (source == "hinge") { clk_total_ = hinge_period; }   // scrub maps over one march period
    }
    float scrub_time_at(int x) const;            // map a cursor x to a time on the bar

    // ── TIMELINE KEY MARKS (tool feature 4): named poses on the live clock. ──
    // The engine pushes the list each clock push; the timeline draws diamonds
    // at each key's time; a diamond click scrubs to it. The KEY button keys
    // the live clock time under an auto name (keyN), like the camera's save.
    void set_key_marks(std::vector<std::pair<std::string, double>> ks, const std::string& src) {
        key_marks_ui_ = std::move(ks); key_marks_src_ = src;
    }
    // D7: joint-aware key marks for the dope sheet — standalone struct to avoid
    // pulling engine.hpp into this header.
    struct DopeKey { std::string name; double t; std::string joint; };
    void set_dope_keys(std::vector<DopeKey> dk) { dope_keys_ = std::move(dk); }
    // D2: timeline markers are engine-fed event positions; the UI only draws.
    struct TimelineMarker { double t; std::string label; int kind; };
    void set_timeline_markers(std::vector<TimelineMarker> markers) {
        timeline_markers_ = std::move(markers);
    }
    std::vector<TimelineMarker> timeline_markers_;
    std::vector<std::pair<std::string, double>> key_marks_ui_;
    std::vector<DopeKey> dope_keys_;              // D7: joint-grouped key marks
    float dope_sheet_h_ = 0.f;                   // D7: height of the dope sheet rows
    std::string key_marks_src_;                  // which clock the keys live on

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
