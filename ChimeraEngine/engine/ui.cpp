// ui.cpp — THE ENGINE STUDIO overlay (see ui.hpp for the law this file lives under)
#include "ui.hpp"

#include <windows.h>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <fstream>

// ── local helpers (no external deps — the engine's standing rule) ─────────────

static std::vector<char> ui_read_file(const char* path) {
    std::ifstream f(path, std::ios::ate | std::ios::binary);
    if (!f.is_open()) return {};
    auto size = f.tellg();
    std::vector<char> buf(static_cast<size_t>(size));
    f.seekg(0); f.read(buf.data(), static_cast<std::streamsize>(size));
    return buf;
}

static VkShaderModule ui_shader_module(VkDevice dev, const std::vector<char>& spv) {
    if (spv.empty()) return VK_NULL_HANDLE;
    VkShaderModuleCreateInfo ci{};
    ci.sType    = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    ci.codeSize = spv.size();
    ci.pCode    = reinterpret_cast<const uint32_t*>(spv.data());
    VkShaderModule m = VK_NULL_HANDLE;
    vkCreateShaderModule(dev, &ci, nullptr, &m);
    return m;
}

// Minimal JSON string-value reader (same philosophy as main.cpp's helpers:
// the board file is written by our own tool — well-formed, flat, ASCII).
static std::string ui_json_string(const std::string& body, const char* key, size_t from = 0) {
    std::string needle = std::string("\"") + key + "\"";
    size_t pos = body.find(needle, from);
    if (pos == std::string::npos) return "";
    size_t p = pos + needle.size();
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (p >= body.size() || body[p] != ':') return "";
    ++p; while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (p >= body.size() || body[p] != '"') return "";
    ++p;
    size_t start = p;
    while (p < body.size() && body[p] != '"') ++p;
    return body.substr(start, p - start);
}

// ── input ─────────────────────────────────────────────────────────────────────

void StudioUI::on_mouse_move(int x, int y) {
    if (drag_kind_ == 1) {          // strip bottom border: height follows the cursor
        float ns = static_cast<float>(y);
        float mx = ext_.height * strip_.max_frac;
        strip_.size = ns < strip_.min_size ? strip_.min_size : (ns > mx ? mx : ns);
    } else if (drag_kind_ == 2) {   // left panel right border: width follows
        float ns = static_cast<float>(x);
        float mx = ext_.width * left_.max_frac;
        left_.size = ns < left_.min_size ? left_.min_size : (ns > mx ? mx : ns);
    } else if (drag_kind_ == 3) {   // right panel left border: width follows (from the right edge)
        float ns = static_cast<float>(ext_.width) - static_cast<float>(x);
        float mx = ext_.width * right_.max_frac;
        right_.size = ns < right_.min_size ? right_.min_size : (ns > mx ? mx : ns);
    } else if (drag_kind_ == 4) {   // bottom panel top border: height follows (from the bottom edge)
        float ns = static_cast<float>(ext_.height) - static_cast<float>(y);
        float mx = ext_.height * bottom_.max_frac;
        bottom_.size = ns < bottom_.min_size ? bottom_.min_size : (ns > mx ? mx : ns);
    } else if (drag_kind_ == 6) {   // D3: reel panel top border: height follows (above the timeline)
        float bh = bottom_.collapsed ? 22.f : bottom_.size;
        float ns = static_cast<float>(ext_.height) - bh - static_cast<float>(y);
        float mx = ext_.height * reel_.max_frac;
        reel_.size = ns < reel_.min_size ? reel_.min_size : (ns > mx ? mx : ns);
    } else if (drag_kind_ == 5) {   // D1: dragging the playhead — every move is a scrub
        if (cb_scrub_) cb_scrub_(scrub_time_at(x));
    } else if (drag_kind_ == 7) {   // C1: dragging a theta slider — every move is an intent
        if (cb_joint_theta_ && drag_joint_ >= 0)
            cb_joint_theta_(drag_joint_, slider_theta_at(drag_joint_, x));
    } else if (drag_kind_ == 8) {   // E1: dragging the docs scrollbar — thumb follows the cursor
        float track_h = docs_sb_track_[3] - docs_sb_thumb_[3];
        if (track_h > 0.f && docs_scroll_max_ > 0.f) {
            float f = (static_cast<float>(y) - docs_sb_track_[1] - docs_sb_thumb_[3] * 0.5f) / track_h;
            docs_.scroll = f * docs_scroll_max_;
            docs_clamp_scroll();
        }
    }
}

void StudioUI::layout(uint32_t w, uint32_t h, float R[5][4]) const {
    // strip: top, full width. bottom: between left/right, docked low.
    // reel: between left/right, directly above the bottom timeline.
    // left/right: between strip and (bottom + reel), docked to their edges.
    // F2: the status bar owns the bottom BAR_H px when it's on — every panel
    // yields to it, so the bar never covers content (and content never the bar).
    const float hh = static_cast<float>(h) - (bar_on_ ? BAR_H : 0.f);
    float sh = strip_.collapsed ? 22.f : strip_.size;
    if (sh > hh) sh = hh;
    float bh = bottom_.collapsed ? 22.f : bottom_.size;
    if (bh > hh - sh) bh = hh - sh;
    if (bh < 22.f) bh = 22.f;
    float rh = reel_.collapsed ? 22.f : reel_.size;
    if (rh > hh - sh - bh) rh = hh - sh - bh;
    if (rh < 22.f) rh = 22.f;
    float lw = left_.collapsed  ? 22.f : left_.size;
    float rw = right_.collapsed ? 22.f : right_.size;
    R[0][0] = 0; R[0][1] = 0; R[0][2] = static_cast<float>(w); R[0][3] = sh;
    R[1][0] = 0; R[1][1] = sh; R[1][2] = lw; R[1][3] = hh - sh - bh - rh;
    R[2][0] = static_cast<float>(w) - rw; R[2][1] = sh; R[2][2] = rw; R[2][3] = hh - sh - bh - rh;
    R[3][0] = lw; R[3][1] = hh - bh; R[3][2] = static_cast<float>(w) - lw - rw; R[3][3] = bh;
    R[4][0] = lw; R[4][1] = hh - bh - rh; R[4][2] = static_cast<float>(w) - lw - rw; R[4][3] = rh;
}

bool StudioUI::hit_strip_title(int x, int y) const {
    return y >= 0 && y < 22 && x >= 0 && x < static_cast<int>(ext_.width);
}
bool StudioUI::hit_left_title(int x, int y) const {
    float sh = strip_.collapsed ? 22.f : strip_.size;
    return x >= 0 && x < 22 && y >= static_cast<int>(sh);
}
bool StudioUI::hit_right_title(int x, int y) const {
    float sh = strip_.collapsed ? 22.f : strip_.size;
    return x >= static_cast<int>(ext_.width) - 22 && y >= static_cast<int>(sh);
}
bool StudioUI::hit_bottom_title(int x, int y) const {
    float R[5][4]; layout(ext_.width, ext_.height, R);
    return y >= static_cast<int>(R[3][1]) && y < static_cast<int>(R[3][1] + 22)
        && x >= static_cast<int>(R[3][0]) && x < static_cast<int>(R[3][0] + R[3][2]);
}
bool StudioUI::hit_reel_title(int x, int y) const {
    float R[5][4]; layout(ext_.width, ext_.height, R);
    return y >= static_cast<int>(R[4][1]) && y < static_cast<int>(R[4][1] + 22)
        && x >= static_cast<int>(R[4][0]) && x < static_cast<int>(R[4][0] + R[4][2]);
}

float StudioUI::scrub_time_at(int x) const {
    if (clk_total_ <= 0.0 || scrub_rect_[2] <= 0.f) return 0.0;
    float f = (static_cast<float>(x) - scrub_rect_[0]) / scrub_rect_[2];
    if (f < 0.f) f = 0.f;
    if (f > 1.f) f = 1.f;
    return f * clk_total_;
}

bool StudioUI::wants_mouse(int x, int y) {
    if (!visible) return false;
    float R[5][4]; layout(ext_.width, ext_.height, R);
    for (int i = 0; i < 5; ++i) {
        if (x >= R[i][0] && x < R[i][0] + R[i][2] && y >= R[i][1] && y < R[i][1] + R[i][3]) return true;
    }
    return false;
}

bool StudioUI::on_lbutton(int x, int y, bool down) {
    if (!visible) return false;
    if (!down) {
        bool had = drag_kind_ != 0;
        drag_kind_ = 0;
        drag_joint_ = -1;
        return had;
    }
    float R[5][4]; layout(ext_.width, ext_.height, R);
    // resize borders first (a 6 px grab band on the panel's inner edge)
    if (!strip_.collapsed && y >= R[0][3] - 3 && y <= R[0][3] + 3) { drag_kind_ = 1; return true; }
    if (!left_.collapsed  && x >= R[1][2] - 3 && x <= R[1][2] + 3 && y >= R[1][1] && y < R[1][1] + R[1][3]) { drag_kind_ = 2; return true; }
    if (!right_.collapsed && x >= R[2][0] - 3 && x <= R[2][0] + 3 && y >= R[2][1] && y < R[2][1] + R[2][3]) { drag_kind_ = 3; return true; }
    if (!bottom_.collapsed && y >= R[3][1] - 3 && y <= R[3][1] + 3 && x >= R[3][0] && x < R[3][0] + R[3][2]) { drag_kind_ = 4; return true; }
    if (!reel_.collapsed && y >= R[4][1] - 3 && y <= R[4][1] + 3 && x >= R[4][0] && x < R[4][0] + R[4][2]) { drag_kind_ = 6; return true; }
    // D1: the scrub bar — press grabs the playhead (drags scrub; a click lands one)
    if (!bottom_.collapsed && clk_total_ > 0.0
        && x >= scrub_rect_[0] && x <= scrub_rect_[0] + scrub_rect_[2]
        && y >= scrub_rect_[1] - 4 && y <= scrub_rect_[1] + scrub_rect_[3] + 4) {
        drag_kind_ = 5;
        if (cb_scrub_) cb_scrub_(scrub_time_at(x));
        return true;
    }
    // C1: a theta slider's track — press grabs the thumb (a click lands one
    // exact intent; drags stream them). Hit-tested before the Hot list because
    // the tracks live inside the left dock's joint rows.
    if (left_mode_ == 1 && !left_.collapsed) {
        for (size_t i = 0; i < slider_tracks_.size(); ++i) {
            const auto& tr = slider_tracks_[i];
            if (x >= tr[0] && x <= tr[0] + tr[2] && y >= tr[1] - 6 && y <= tr[1] + tr[3] + 6) {
                drag_kind_ = 7;
                drag_joint_ = static_cast<int>(i);
                if (cb_joint_theta_) cb_joint_theta_(drag_joint_, slider_theta_at(drag_joint_, x));
                return true;
            }
        }
    }
    // D1: the timeline's buttons (play/pause, frame-step, speed)
    // B3: the strip's stage nodes (id 100+i) select/deselect the stage panel
    for (const Hot& h : hots_) {
        if (x >= h.x && x < h.x + h.w && y >= h.y && y < h.y + h.h) {
            if (h.id == 1 && cb_play_toggle_) cb_play_toggle_();
            if (h.id == 2 && cb_step_) cb_step_(-1);
            if (h.id == 3 && cb_step_) cb_step_(+1);
            if (h.id == 4 && cb_speed_cycle_) cb_speed_cycle_();
            if (h.id >= 100 && h.id < 300) {
                int i = h.id - 100;
                selected_stage_ = (selected_stage_ == i) ? -1 : i;
                left_mode_ = 0;              // a stage click always shows its envelope (B3)
            }
            if (h.id >= 300 && h.id < 400) {
                int i = h.id - 300;          // the workspace rows (A3); three are live so far
                if (i == 0) { left_mode_ = 0; }                          // BOARD
                if (i == 1) { left_mode_ = 4; selected_stage_ = -1; }    // SCENE (C4)
                if (i == 2) { left_mode_ = 1; selected_stage_ = -1; }    // JOINTS (C1)
                if (i == 7) { left_mode_ = 2; selected_stage_ = -1; }    // DOCS (E1)
                if (i == 8) { left_mode_ = 3; selected_stage_ = -1; }    // LOG (F4)
                if (i == 6) { left_mode_ = 5; selected_stage_ = -1; }    // CAPTURE (D5)
            }
            if (h.id >= 400 && h.id < 500 && cb_joint_select_) cb_joint_select_(h.id - 400);
            if (h.id >= 500 && h.id < 600) docs_set(h.id - 500);         // E1: the doc picker
            if (h.id >= 600 && h.id < 700) {                             // C4: the outliner's rows
                int i = h.id - 600;
                if (i >= 0 && i < static_cast<int>(scene_.size()) &&
                    scene_[i].toggleable && cb_scene_toggle_) cb_scene_toggle_(i);
            }
            if (h.id >= 700 && h.id < 800 && cb_scene_select_)           // C2: inspect a row
                cb_scene_select_(h.id - 700);
            if (h.id >= 800 && h.id < 850 && cb_cam_recall_)             // D6: recall a shot
                cb_cam_recall_(h.id - 800);
            if (h.id == 850 && cb_cam_save_) cb_cam_save_();             // D6: save the live camera
            return true;
        }
    }
    // E1: the docs scrollbar — press on the thumb grabs it (drag_kind_ 8);
    // a track click pages by exactly the visible line count (the panel's own
    // geometry, so the HTTP twin can predict it)
    if (left_mode_ == 2 && !left_.collapsed && docs_sb_track_[3] > 0.f) {
        if (x >= docs_sb_thumb_[0] - 2 && x <= docs_sb_thumb_[0] + docs_sb_thumb_[2] + 2 &&
            y >= docs_sb_thumb_[1] && y <= docs_sb_thumb_[1] + docs_sb_thumb_[3]) {
            drag_kind_ = 8;
            return true;
        }
        if (x >= docs_sb_track_[0] - 2 && x <= docs_sb_track_[0] + docs_sb_track_[2] + 2 &&
            y >= docs_sb_track_[1] && y <= docs_sb_track_[1] + docs_sb_track_[3]) {
            float R2[5][4]; layout(ext_.width, ext_.height, R2);
            float visible_n = (docs_sb_track_[3]) / cell_h_;
            if (y < docs_sb_thumb_[1]) docs_.scroll -= visible_n;
            else                       docs_.scroll += visible_n;
            docs_clamp_scroll();
            return true;
        }
    }
    // title bars toggle collapse (Blender's area header law: every area collapses)
    if (hit_strip_title(x, y)) { strip_.collapsed = !strip_.collapsed; return true; }
    if (hit_left_title(x, y))  { left_.collapsed  = !left_.collapsed;  return true; }
    if (hit_right_title(x, y)) { right_.collapsed = !right_.collapsed; return true; }
    if (hit_bottom_title(x, y)){ bottom_.collapsed = !bottom_.collapsed; return true; }
    if (hit_reel_title(x, y))  { reel_.collapsed  = !reel_.collapsed;  return true; }
    // anywhere else inside a panel: consume (never leak a camera orbit through the UI)
    return wants_mouse(x, y);
}

// ── board polling (read the repo's truth; never own it) ───────────────────────

void StudioUI::poll_board() {
    auto now = std::chrono::steady_clock::now();
    if (std::chrono::duration<float>(now - last_poll_).count() < 1.0f) return;
    last_poll_ = now;

    WIN32_FILE_ATTRIBUTE_DATA fad{};
    if (!GetFileAttributesExA(board_path_.c_str(), GetFileExInfoStandard, &fad)) return;
    uint64_t mt = (static_cast<uint64_t>(fad.ftLastWriteTime.dwHighDateTime) << 32)
                | fad.ftLastWriteTime.dwLowDateTime;
    if (mt == last_mtime_) return;
    last_mtime_ = mt;

    std::ifstream f(board_path_, std::ios::binary);
    if (!f.is_open()) return;
    std::string body((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());

    StudioBoard b;
    b.standing = ui_json_string(body, "standing");
    b.updated  = ui_json_string(body, "updated");
    // stages: walk the flat per-stage objects the tool writes (B3: the envelope
    // cells ride along — law, tool, artifact, falsifier, cell, spec)
    size_t cur = 0;
    for (int i = 0; i < 32; ++i) {
        size_t pos = body.find("\"id\"", cur);
        if (pos == std::string::npos) break;
        StudioStage s;
        s.id        = ui_json_string(body, "id", pos);
        s.name      = ui_json_string(body, "name", pos);
        s.status    = ui_json_string(body, "status", pos);
        s.law       = ui_json_string(body, "law", pos);
        s.tool      = ui_json_string(body, "tool", pos);
        s.artifact  = ui_json_string(body, "artifact", pos);
        s.falsifier = ui_json_string(body, "falsifier", pos);
        s.cell      = ui_json_string(body, "cell", pos);
        s.spec_title = ui_json_string(body, "spec_title", pos);
        s.spec      = ui_json_string(body, "spec", pos);
        if (s.id.empty()) break;
        // JSON escapes newlines in the spec body; restore them for the wrap
        for (size_t p2 = s.spec.find("\\n"); p2 != std::string::npos; p2 = s.spec.find("\\n", p2))
            s.spec.replace(p2, 2, 1, '\n');
        b.stages.push_back(s);
        cur = pos + 4;
    }
    b.loaded = !b.stages.empty();
    board_ = std::move(b);
}

// ── draw list ─────────────────────────────────────────────────────────────────

void StudioUI::uv_cell(int ch, float& u0, float& v0, float& u1, float& v1) const {
    int idx = ch - 32;
    if (idx < 0 || idx > 94) idx = 0;   // 95 is the white cell
    // UVs are over the FULL atlas (font cells are the top-left sub-rect)
    u0 = (idx % ATLAS_COLS) * cell_w_ / atlas_w_;
    v0 = (idx / ATLAS_COLS) * cell_h_ / atlas_h_;
    u1 = u0 + cell_w_ / atlas_w_;
    v1 = v0 + cell_h_ / atlas_h_;
}

void StudioUI::uv_white(float& u0, float& v0, float& u1, float& v1) const {
    // the DEL slot (index 95) is filled solid white; sample its center so rect
    // edges never bleed glyph ink from the neighboring cell
    float cx = (15 + 0.5f) * cell_w_ / atlas_w_;
    float cy = (5 + 0.5f) * cell_h_ / atlas_h_;
    float mx = 1.5f / atlas_w_, my = 1.5f / atlas_h_;
    u0 = cx - mx; v0 = cy - my; u1 = cx + mx; v1 = cy + my;
}

void StudioUI::rect(float x, float y, float w, float h, float r, float g, float b, float a) {
    float u0, v0, u1, v1; uv_white(u0, v0, u1, v1);
    Vert v[6] = {
        {x,     y,     u0, v0, r, g, b, a, 0.f},
        {x + w, y,     u1, v0, r, g, b, a, 0.f},
        {x + w, y + h, u1, v1, r, g, b, a, 0.f},
        {x,     y,     u0, v0, r, g, b, a, 0.f},
        {x + w, y + h, u1, v1, r, g, b, a, 0.f},
        {x,     y + h, u0, v1, r, g, b, a, 0.f},
    };
    verts_.insert(verts_.end(), v, v + 6);
}

void StudioUI::rect_outline(float x, float y, float w, float h, float t,
                            float r, float g, float b, float a) {
    rect(x, y, w, t, r, g, b, a);
    rect(x, y + h - t, w, t, r, g, b, a);
    rect(x, y, t, h, r, g, b, a);
    rect(x + w - t, y, t, h, r, g, b, a);
}

// C1: a line as a rotated quad (the draw list has no line primitive — the
// gizmo's axis needs one). Solid white-UV like rect, thickness in px.
void StudioUI::line(float x0, float y0, float x1, float y1, float th,
                    float r, float g, float b, float a) {
    float dx = x1 - x0, dy = y1 - y0;
    float len = sqrtf(dx * dx + dy * dy);
    if (len < 1e-4f) { rect(x0 - th * 0.5f, y0 - th * 0.5f, th, th, r, g, b, a); return; }
    float nx = -dy / len * th * 0.5f, ny = dx / len * th * 0.5f;
    float u0, v0, u1, v1; uv_white(u0, v0, u1, v1);
    Vert v[6] = {
        {x0 + nx, y0 + ny, u0, v0, r, g, b, a, 0.f},
        {x1 + nx, y1 + ny, u1, v0, r, g, b, a, 0.f},
        {x1 - nx, y1 - ny, u1, v1, r, g, b, a, 0.f},
        {x0 + nx, y0 + ny, u0, v0, r, g, b, a, 0.f},
        {x1 - nx, y1 - ny, u1, v1, r, g, b, a, 0.f},
        {x0 - nx, y0 - ny, u0, v1, r, g, b, a, 0.f},
    };
    verts_.insert(verts_.end(), v, v + 6);
}

// C1: the slider law — a linear map from track x to theta over the joint's
// DERIVED ROM [ext, flex], clamped at both ends. No tuning, no easing.
float StudioUI::slider_theta_at(int row, int x) const {
    if (row < 0 || row >= static_cast<int>(joints_.size()) ||
        row >= static_cast<int>(slider_tracks_.size())) return 0.0f;
    const auto& tr = slider_tracks_[row];
    if (tr[2] <= 0.f) return 0.0f;
    float f = (static_cast<float>(x) - tr[0]) / tr[2];
    if (f < 0.f) f = 0.f;
    if (f > 1.f) f = 1.f;
    return joints_[row].ext + f * (joints_[row].flex - joints_[row].ext);
}

void StudioUI::text(float x, float y, const std::string& s, float r, float g, float b, float a) {
    float pen = x;
    for (char c : s) {
        float u0, v0, u1, v1; uv_cell(static_cast<unsigned char>(c), u0, v0, u1, v1);
        float x0 = pen, y0 = y, x1 = pen + cell_w_, y1 = y + cell_h_;
        Vert v[6] = {
            {x0, y0, u0, v0, r, g, b, a, 0.f},
            {x1, y0, u1, v0, r, g, b, a, 0.f},
            {x1, y1, u1, v1, r, g, b, a, 0.f},
            {x0, y0, u0, v0, r, g, b, a, 0.f},
            {x1, y1, u1, v1, r, g, b, a, 0.f},
            {x0, y1, u0, v1, r, g, b, a, 0.f},
        };
        verts_.insert(verts_.end(), v, v + 6);
        pen += advance_;
    }
}

// B3: greedy word-wrap (monospace arithmetic; newlines are hard breaks first).
float StudioUI::text_wrap(float x, float y, const std::string& s, size_t maxc,
                          float r, float g, float b, float a, float y_max) {
    if (maxc < 8) maxc = 8;
    size_t start = 0;
    while (start < s.size()) {
        size_t nl = s.find('\n', start);
        std::string para = s.substr(start, nl == std::string::npos ? nl : nl - start);
        start = (nl == std::string::npos) ? s.size() : nl + 1;
        if (para.empty()) { y += cell_h_; continue; }   // blank line stays a blank line
        while (!para.empty()) {
            if (para.size() <= maxc) {
                if (y <= y_max) text(x, y, para, r, g, b, a);
                y += cell_h_; break;
            }
            size_t cut = para.rfind(' ', maxc);
            if (cut == std::string::npos || cut == 0) cut = maxc;
            if (y <= y_max) text(x, y, para.substr(0, cut), r, g, b, a);
            y += cell_h_;
            para = para.substr(cut + (cut < para.size() && para[cut] == ' ' ? 1 : 0));
        }
    }
    return y;
}

std::string StudioUI::selected_stage_id() const {
    if (selected_stage_ < 0 || selected_stage_ >= static_cast<int>(board_.stages.size()))
        return "";
    return board_.stages[selected_stage_].id;
}

// D3: a reel tile's image — flags=1, UVs into the thumbnail grid below the font cells.
void StudioUI::thumb_uv(int slot, float& u0, float& v0, float& u1, float& v1) const {
    float font_h = cell_h_ * ATLAS_ROWS;
    float px = static_cast<float>((slot % 4) * THUMB_W);
    float py = font_h + static_cast<float>((slot / 4) * THUMB_H);
    u0 = px / atlas_w_;               v0 = py / atlas_h_;
    u1 = (px + THUMB_W) / atlas_w_;   v1 = (py + THUMB_H) / atlas_h_;
}

void StudioUI::thumb(float x, float y, float w, float h, int slot) {
    float u0, v0, u1, v1; thumb_uv(slot, u0, v0, u1, v1);
    Vert v[6] = {
        {x,     y,     u0, v0, 1.f, 1.f, 1.f, 1.f, 1.f},
        {x + w, y,     u1, v0, 1.f, 1.f, 1.f, 1.f, 1.f},
        {x + w, y + h, u1, v1, 1.f, 1.f, 1.f, 1.f, 1.f},
        {x,     y,     u0, v0, 1.f, 1.f, 1.f, 1.f, 1.f},
        {x + w, y + h, u1, v1, 1.f, 1.f, 1.f, 1.f, 1.f},
        {x,     y + h, u0, v1, 1.f, 1.f, 1.f, 1.f, 1.f},
    };
    verts_.insert(verts_.end(), v, v + 6);
}

// D3: a grab lands — text into the ring, pixels into its atlas slot. Render thread.
void StudioUI::reel_push(const uint8_t* rgba, const std::string& l1,
                         const std::string& l2, const std::string& l3) {
    if (dev_ == VK_NULL_HANDLE || thumb_stage_map_ == nullptr || font_img_ == VK_NULL_HANDLE) return;
    int slot = static_cast<int>(reel_seq_ % REEL_MAX);
    tiles_[slot].used = true;
    tiles_[slot].l1 = l1; tiles_[slot].l2 = l2; tiles_[slot].l3 = l3;
    ++reel_seq_;
    if (reel_count_ < REEL_MAX) ++reel_count_;

    std::memcpy(thumb_stage_map_, rgba, static_cast<size_t>(THUMB_W) * THUMB_H * 4);

    extern VkQueue g_ui_queue;
    extern VkCommandPool g_ui_cmd_pool;
    VkCommandBuffer cmd;
    VkCommandBufferAllocateInfo cai{};
    cai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    cai.commandPool = g_ui_cmd_pool;
    cai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cai.commandBufferCount = 1;
    vkAllocateCommandBuffers(dev_, &cai, &cmd);
    VkCommandBufferBeginInfo bbi{};
    bbi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    bbi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    vkBeginCommandBuffer(cmd, &bbi);
    auto barrier = [&](VkImageLayout oldl, VkImageLayout newl,
                       VkAccessFlags srca, VkAccessFlags dsta,
                       VkPipelineStageFlags srcs, VkPipelineStageFlags dsts) {
        VkImageMemoryBarrier b{};
        b.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
        b.oldLayout = oldl; b.newLayout = newl;
        b.srcAccessMask = srca; b.dstAccessMask = dsta;
        b.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        b.image = font_img_;
        b.subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };
        vkCmdPipelineBarrier(cmd, srcs, dsts, 0, 0, nullptr, 0, nullptr, 1, &b);
    };
    barrier(VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_TRANSFER_WRITE_BIT,
            VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
    VkBufferImageCopy cp{};
    cp.imageSubresource = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1 };
    cp.imageOffset = { (slot % 4) * THUMB_W,
                       static_cast<int32_t>(cell_h_ * ATLAS_ROWS) + (slot / 4) * THUMB_H, 0 };
    cp.imageExtent = { static_cast<uint32_t>(THUMB_W), static_cast<uint32_t>(THUMB_H), 1 };
    vkCmdCopyBufferToImage(cmd, thumb_stage_, font_img_, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &cp);
    barrier(VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
            VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT,
            VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT);
    vkEndCommandBuffer(cmd);
    VkSubmitInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
    vkQueueSubmit(g_ui_queue, 1, &si, VK_NULL_HANDLE);
    vkQueueWaitIdle(g_ui_queue);
    vkFreeCommandBuffers(dev_, g_ui_cmd_pool, 1, &cmd);
}

// ── E1: THE DOCS BROWSER — the repo's own workflow docs, verbatim, in a panel ──

void StudioUI::docs_init() {
    if (!docs_.paths.empty()) return;
    // The menu (docs/THE_ENGINE_STUDIO.md, E1) names the five. The exe's CWD
    // is build/Release — the repo root is four levels up.
    const char* base = "../../../../docs/";
    docs_.paths = {
        std::string(base) + "THE_BODY_PIPELINE.md",
        std::string(base) + "THE_ARTISTS_SOLID.md",
        std::string(base) + "THE_MASTER_LIST.md",
        std::string(base) + "THE_TRIANGLE_GUIDE.md",
        std::string(base) + "THE_OPERATING_MANUAL.md",
    };
}

std::string StudioUI::docs_path() const {
    if (docs_.paths.empty() || docs_.current < 0 ||
        docs_.current >= static_cast<int>(docs_.paths.size())) return "";
    return docs_.paths[docs_.current];
}

static uint64_t fnv1a64(const std::string& s) {
    uint64_t h = 14695981039346656037ull;
    for (unsigned char c : s) { h ^= c; h *= 1099511628211ull; }
    return h;
}

void StudioUI::docs_poll() {
    docs_init();
    auto now = std::chrono::steady_clock::now();
    if (std::chrono::duration<float>(now - docs_.last_poll).count() < 1.0f) return;
    docs_.last_poll = now;

    std::string path = docs_path();
    if (path.empty()) return;
    WIN32_FILE_ATTRIBUTE_DATA fad{};
    if (!GetFileAttributesExA(path.c_str(), GetFileExInfoStandard, &fad)) return;
    uint64_t mt = (static_cast<uint64_t>(fad.ftLastWriteTime.dwHighDateTime) << 32)
                | fad.ftLastWriteTime.dwLowDateTime;
    if (mt == docs_.mtime) return;
    docs_.mtime = mt;

    // Read the file's EXACT bytes — the browser's one job is to not interpret
    std::ifstream f(path, std::ios::binary);
    if (!f.is_open()) return;
    docs_.raw.assign((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    docs_.fnv = fnv1a64(docs_.raw);
    docs_.lines.clear();
    size_t start = 0;
    while (start <= docs_.raw.size()) {
        size_t nl = docs_.raw.find('\n', start);
        std::string line = docs_.raw.substr(start, nl == std::string::npos ? nl : nl - start);
        if (!line.empty() && line.back() == '\r') line.pop_back();
        docs_.lines.push_back(std::move(line));
        if (nl == std::string::npos) break;
        start = nl + 1;
    }
    docs_.wrap_cols = 0;      // force a rewrap at the dock's current width
}

void StudioUI::docs_rewrap(size_t maxc) {
    if (maxc < 8) maxc = 8;
    if (docs_.wrap_cols == maxc) return;
    docs_.wrap_cols = maxc;
    docs_.display.clear();
    // The same greedy law as text_wrap — the browser and the renderer can
    // never disagree about where a line breaks
    for (const std::string& line : docs_.lines) {
        std::string para = line;
        if (para.empty()) { docs_.display.emplace_back(); continue; }
        while (!para.empty()) {
            if (para.size() <= maxc) { docs_.display.push_back(para); break; }
            size_t cut = para.rfind(' ', maxc);
            if (cut == std::string::npos || cut == 0) cut = maxc;
            docs_.display.push_back(para.substr(0, cut));
            para = para.substr(cut + (cut < para.size() && para[cut] == ' ' ? 1 : 0));
        }
    }
    docs_clamp_scroll();
}

void StudioUI::docs_clamp_scroll() {
    if (docs_.scroll < 0.f) docs_.scroll = 0.f;
    if (docs_.scroll > docs_scroll_max_) docs_.scroll = docs_scroll_max_;
}

void StudioUI::docs_set(int idx) {
    docs_init();
    if (idx < 0 || idx >= static_cast<int>(docs_.paths.size())) return;
    if (idx == docs_.current) return;
    docs_.current = idx;
    docs_.mtime = 0;                       // force a reload on the next poll
    docs_.scroll = 0.f;
    docs_.last_poll = std::chrono::steady_clock::time_point{};
    docs_poll();
}

void StudioUI::docs_set_scroll(float s) {
    docs_.scroll = s;
    docs_clamp_scroll();
}

bool StudioUI::on_wheel(int x, int y, float delta) {
    if (!visible || left_mode_ != 2 || left_.collapsed) return false;
    float R[5][4]; layout(ext_.width, ext_.height, R);
    if (x < R[1][0] || x >= R[1][0] + R[1][2] || y < R[1][1] || y >= R[1][1] + R[1][3])
        return false;
    docs_.scroll -= delta * 3.0f;          // one notch = 3 lines (the platform convention)
    docs_clamp_scroll();
    return true;
}

static void status_color(const std::string& s, float& r, float& g, float& b) {
    if      (s == "green")   { r = 0.25f; g = 0.75f; b = 0.35f; }
    else if (s == "partial") { r = 0.90f; g = 0.70f; b = 0.20f; }
    else if (s == "next")    { r = 0.30f; g = 0.60f; b = 1.00f; }
    else if (s == "blocked") { r = 0.85f; g = 0.28f; b = 0.28f; }
    else if (s == "rolling") { r = 0.60f; g = 0.45f; b = 0.90f; }
    else                     { r = 0.42f; g = 0.44f; b = 0.50f; }  // pending / unknown
}

// ── per-frame build ───────────────────────────────────────────────────────────

void StudioUI::prepare(uint32_t win_w, uint32_t win_h) {
    ext_.width = win_w; ext_.height = win_h;
    poll_board();
    docs_poll();    // E1: unconditional — the HTTP twin stays live in any dock mode
    verts_.clear();
    verts_.reserve(8192);
    hots_.clear();
    hud_rows_.clear();
    // F2/F3: the chrome draws whether the overlay is open or not. With the
    // overlay closed it is the ONLY thing drawn — "always visible" is literal.
    if (!visible) { build_chrome(); build_console(); return; }

    float R[5][4]; layout(win_w, win_h, R);
    const float lh = cell_h_;                       // one text line
    const float TR = 0.86f, TG = 0.88f, TB = 0.92f; // text color

    // ── the stage strip (B1: the pipeline map; B2: the standing rule, displayed) ──
    rect(R[0][0], R[0][1], R[0][2], R[0][3], 0.07f, 0.08f, 0.11f, 0.88f);
    rect(R[0][0], R[0][1], R[0][2], 22, 0.13f, 0.14f, 0.19f, 0.95f);
    text(8, (22 - lh) * 0.5f, "THE ENGINE STUDIO - pipeline board (B0-B10)  [F1] hide  [click bar] collapse  [drag edge] resize",
         0.62f, 0.66f, 0.74f, 1.f);
    if (!strip_.collapsed) {
        float y0 = 30.f;
        float node_h = strip_.size - 30.f - lh - 12.f;
        if (node_h < 14.f) node_h = 14.f;
        if (!board_.loaded) {
            text(8, y0 + 6, "no board file - run: python tools/studio_board.py  (the repo's gate truth, read never owned)",
                 0.85f, 0.55f, 0.30f, 1.f);
        } else {
            size_t n = board_.stages.size();
            float pad = 8.f, gap = 6.f;
            float bw = (static_cast<float>(win_w) - 2 * pad - (n - 1) * gap) / n;
            for (size_t i = 0; i < n; ++i) {
                const StudioStage& s = board_.stages[i];
                float x = pad + i * (bw + gap);
                float cr, cg, cb; status_color(s.status, cr, cg, cb);
                bool sel = (static_cast<int>(i) == selected_stage_);
                rect(x, y0, bw, node_h, cr * 0.35f, cg * 0.35f, cb * 0.35f, 0.92f);
                rect_outline(x, y0, bw, node_h, s.status == "next" ? 3.f : (sel ? 2.f : 1.f), cr, cg, cb, 1.f);
                if (sel) rect_outline(x - 2, y0 - 2, bw + 4, node_h + 4, 1.5f, 1.f, 1.f, 1.f, 1.f);
                hots_.push_back({ x, y0, bw, node_h, 100 + static_cast<int>(i) });   // B3: click -> its panel
                // id centered, name under it (monospace: centering is arithmetic)
                float idw = s.id.size() * advance_;
                text(x + (bw - idw) * 0.5f, y0 + 4, s.id, 1.f, 1.f, 1.f, 1.f);
                if (node_h > 2 * lh + 8) {
                    std::string nm = s.name.size() * advance_ > bw - 4
                                   ? s.name.substr(0, static_cast<size_t>((bw - 4) / advance_)) : s.name;
                    float nw = nm.size() * advance_;
                    text(x + (bw - nw) * 0.5f, y0 + 6 + lh, nm, TR, TG, TB, 0.85f);
                }
                if (node_h > 3 * lh + 10) {
                    std::string st = s.status;
                    float sw = st.size() * advance_;
                    text(x + (bw - sw) * 0.5f, y0 + 8 + 2 * lh, st, cr, cg, cb, 1.f);
                }
            }
            // B2: the standing rule, displayed - computed by the tool, never edited here
            float sy = y0 + node_h + 4;
            text(8, sy, board_.standing, 1.0f, 0.85f, 0.40f, 1.f);
            std::string src = "docs/THE_BODY_PIPELINE.md " + board_.updated;
            text(static_cast<float>(win_w) - src.size() * advance_ - 8, sy, src, 0.45f, 0.47f, 0.52f, 1.f);
        }
    }

    // ── the STUDIO panel (left): the menu + the join's provenance — or, when a
    // strip node is selected (B3), the stage's task envelope, VERBATIM ──
    rect(R[1][0], R[1][1], R[1][2], R[1][3], 0.07f, 0.08f, 0.11f, 0.85f);
    rect(R[1][0], R[1][1], R[1][2], 22, 0.13f, 0.14f, 0.19f, 0.95f);
    const bool have_sel = selected_stage_ >= 0
                       && selected_stage_ < static_cast<int>(board_.stages.size());
    text(R[1][0] + 8, R[1][1] + (22 - lh) * 0.5f,
         left_.collapsed ? "+" : (left_mode_ == 1 ? "JOINTS - the editor (C1)"
            : (left_mode_ == 2 ? "DOCS - the browser (E1)"
            : (left_mode_ == 3 ? "LOG - the recorder (F4)"
            : (left_mode_ == 4 ? "SCENE - the outliner (C4)"
            : (left_mode_ == 5 ? "CAPTURE - render-to-MP4 (D5)"
            : (have_sel ? board_.stages[selected_stage_].id + " - " + board_.stages[selected_stage_].name : "STUDIO")))))),
         TR, TG, TB, 1.f);
    if (left_mode_ != 1) slider_tracks_.clear();   // stale hit-rects are a lie
    if (left_mode_ != 4) { scene_row_rects_.clear(); scene_sel_rects_.clear(); } // same law
    if (!left_.collapsed && left_mode_ == 2) {
        // E1: THE DOCS BROWSER. The five docs the menu names, verbatim (the
        // panel's FNV hash is served over HTTP — a rendered line that is not
        // the file's line is a bug by definition). Read-only by architecture.
        docs_init();
        float x = R[1][0] + 10, y = R[1][1] + 30;
        float y_max = R[1][1] + R[1][3] - lh;
        for (size_t i = 0; i < docs_.paths.size(); ++i) {
            std::string nm = docs_.paths[i];
            nm = nm.substr(nm.find_last_of('/') + 1);
            if (nm.size() > 3) nm = nm.substr(0, nm.size() - 3);   // strip .md
            bool cur = static_cast<int>(i) == docs_.current;
            if (cur) rect(R[1][0] + 2, y - 2, R[1][2] - 4, lh + 4, 0.13f, 0.16f, 0.24f, 0.95f);
            text(x, y, nm, cur ? 0.45f : 0.42f, cur ? 0.75f : 0.44f, cur ? 1.00f : 0.50f, 1.f);
            hots_.push_back({ x - 2, y - 2, R[1][2] - 20, lh + 4, 500 + static_cast<int>(i) });
            y += lh + 2;
        }
        char ib[160];
        snprintf(ib, sizeof(ib), "%zu lines  |  read-only  |  re-read on file change (1 Hz)",
                 docs_.lines.size());
        text(x, y, ib, 0.45f, 0.47f, 0.52f, 1.f); y += lh + 4;
        // the text, wrapped to the CURRENT dock width (narrow the dock and the
        // wrap follows next frame — the wrap is derived, never stored stale)
        size_t maxc = static_cast<size_t>((R[1][2] - 20 - 14) / advance_);
        docs_rewrap(maxc);
        float text_top = y;
        int visible_n = static_cast<int>((y_max - text_top) / lh) + 1;
        if (visible_n < 1) visible_n = 1;
        docs_scroll_max_ = docs_.display.size() > static_cast<size_t>(visible_n)
            ? static_cast<float>(docs_.display.size() - visible_n) : 0.f;
        docs_clamp_scroll();
        int first = static_cast<int>(docs_.scroll);
        for (size_t i = static_cast<size_t>(first); i < docs_.display.size(); ++i) {
            if (y > y_max) break;
            text(x, y, docs_.display[i], TR, TG, TB, 0.95f);
            y += lh;
        }
        size_t last_shown = first + static_cast<size_t>(visible_n);
        if (last_shown < docs_.display.size() && y_max >= text_top) {
            char cb[96];
            snprintf(cb, sizeof(cb), "... (%zu more lines - wheel / drag the bar)",
                     docs_.display.size() - last_shown);
            rect(R[1][0], y_max - 2, R[1][2] - 12, lh + 4, 0.07f, 0.08f, 0.11f, 0.95f);
            text(x, y_max, cb, 0.85f, 0.55f, 0.30f, 1.f);
        }
        // the scrollbar: track + thumb, sized by visible/total (derived, like
        // every other number in this panel)
        float sb_x = R[1][0] + R[1][2] - 10;
        docs_sb_track_[0] = sb_x; docs_sb_track_[1] = text_top;
        docs_sb_track_[2] = 6.f; docs_sb_track_[3] = y_max + lh - text_top;
        rect(sb_x, text_top, 6, docs_sb_track_[3], 0.12f, 0.13f, 0.17f, 0.95f);
        float thumb_h = docs_sb_track_[3];
        float thumb_y = text_top;
        if (!docs_.display.empty() && docs_scroll_max_ > 0.f) {
            thumb_h = docs_sb_track_[3] * static_cast<float>(visible_n)
                    / static_cast<float>(docs_.display.size());
            if (thumb_h < 20.f) thumb_h = 20.f;
            if (thumb_h > docs_sb_track_[3]) thumb_h = docs_sb_track_[3];
            thumb_y = text_top + (docs_.scroll / docs_scroll_max_)
                    * (docs_sb_track_[3] - thumb_h);
        }
        docs_sb_thumb_[0] = sb_x - 1; docs_sb_thumb_[1] = thumb_y;
        docs_sb_thumb_[2] = 8.f; docs_sb_thumb_[3] = thumb_h;
        rect(sb_x - 1, thumb_y, 8, thumb_h, 0.45f, 0.60f, 1.00f, 0.95f);
    } else if (!left_.collapsed && left_mode_ == 3) {
        // F4: THE RECORDER's stream. The session file holds everything; this
        // dock draws the tail, newest at the bottom — the same lines in the
        // same order (the /log probe diffs the served tail against the file).
        float x = R[1][0] + 10, y = R[1][1] + 30;
        float y_max = R[1][1] + R[1][3] - lh;
        char ib[192];
        snprintf(ib, sizeof(ib), "%s  |  %llu events  |  the file holds everything",
                 log_file_.empty() ? "(recorder offline)" : log_file_.c_str(),
                 (unsigned long long)log_total_);
        text(x, y, ib, 0.45f, 0.47f, 0.52f, 1.f); y += lh + 4;
        // wrap oldest-to-newest, then keep only the rows that fit — the newest
        // line lands at the bottom. REBUILT ONLY ON CHANGE (a new event or a
        // new dock width): wrapping 200 lines every frame spiked frame time.
        size_t maxc = static_cast<size_t>((R[1][2] - 20) / advance_);
        if (maxc < 8) maxc = 8;
        {
            std::lock_guard<std::mutex> lk(log_m_);
            if (log_rows_total_ != log_total_ || log_rows_maxc_ != maxc) {
                log_rows_.clear();
                for (const auto& e : log_ring_) {
                    float r = 0.55f, g = 0.58f, b = 0.65f;
                    if      (e.kind == "upload") { r = 0.30f; g = 0.60f; b = 1.00f; }
                    else if (e.kind == "mode")   { r = 0.25f; g = 0.75f; b = 0.35f; }
                    else if (e.kind == "intent") { r = 0.90f; g = 0.80f; b = 0.30f; }
                    else if (e.kind == "gate")   { r = 0.60f; g = 0.45f; b = 0.90f; }
                    char head[40];
                    snprintf(head, sizeof(head), "[%llu] %.8s ",
                             (unsigned long long)e.seq, e.t.c_str() + 11);
                    std::string line = std::string(head) + e.kind + " " + e.detail;
                    if (line.empty()) { log_rows_.push_back({ "", r, g, b }); continue; }
                    size_t pos = 0;
                    while (pos < line.size()) {
                        size_t n = line.size() - pos;
                        if (n > maxc) {
                            n = maxc;
                            size_t sp = line.rfind(' ', pos + n);
                            if (sp != std::string::npos && sp > pos) n = sp - pos;
                        }
                        log_rows_.push_back({ line.substr(pos, n), r, g, b });
                        pos += n;
                        while (pos < line.size() && line[pos] == ' ') ++pos;
                    }
                }
                log_rows_total_ = log_total_;
                log_rows_maxc_  = maxc;
            }
        }
        if (log_rows_.empty()) {
            text(x, y, "no events yet - the recorder is listening", 0.45f, 0.47f, 0.52f, 1.f);
        } else {
            int visible_n = static_cast<int>((y_max - y) / lh) + 1;
            if (visible_n < 1) visible_n = 1;
            size_t start = log_rows_.size() > static_cast<size_t>(visible_n)
                         ? log_rows_.size() - static_cast<size_t>(visible_n) : 0;
            for (size_t i = start; i < log_rows_.size(); ++i) {
                if (y > y_max) break;
                text(x, y, log_rows_[i].s, log_rows_[i].r, log_rows_[i].g, log_rows_[i].b, 0.95f);
                y += lh;
            }
        }
    } else if (!left_.collapsed && left_mode_ == 5) {
        // D5: THE CAPTURE SESSION. The engine composes the document
        // (capture_kv — the same site GET /capture serves); the dock draws it.
        float x = R[1][0] + 10, y = R[1][1] + 30;
        float y_max = R[1][1] + R[1][3] - lh;
        text(x, y, "offline render: scrub the clock, grab each frame",
             0.45f, 0.47f, 0.52f, 1.f); y += lh;
        text(x, y, "POST /capture {\"op\":\"render\",\"t0\":0,\"t1\":2,\"fps\":24}",
             0.45f, 0.47f, 0.52f, 1.f); y += lh;
        text(x, y, "then: cpp_bridge.encode_movie(frames, out.mp4, fps)",
             0.45f, 0.47f, 0.52f, 1.f); y += lh + 4;
        for (const auto& kv : capture_kv_) {
            if (y > y_max) break;
            text(x, y, kv.first, 0.62f, 0.66f, 0.74f, 1.f);
            text(x + 12 * advance_, y, kv.second,
                 kv.first == "state" ? (kv.second == "FAILED" ? 0.85f : kv.second == "done" ? 0.25f : 1.0f)
                                     : TR,
                 kv.first == "state" ? (kv.second == "FAILED" ? 0.55f : kv.second == "done" ? 0.75f : 0.85f)
                                     : TG,
                 kv.first == "state" ? (kv.second == "FAILED" ? 0.30f : kv.second == "done" ? 0.35f : 0.40f)
                                     : TB, 1.f);
            y += lh;
        }
    } else if (!left_.collapsed && left_mode_ == 4) {
        // C4: THE OUTLINER. Every row is composed by the ENGINE from live state
        // at read time (one formatting site: Engine::scene_rows()); the panel
        // only draws. A toggle click routes through the console's one path
        // (Engine::scene_exec -> console_exec), so the F4 recorder logs the
        // inner endpoint's event automatically — no parallel mutation path.
        float x = R[1][0] + 10, y = R[1][1] + 30;
        float y_max = R[1][1] + R[1][3] - lh;
        text(x, y, "the scene's atoms - every row is live engine state",
             0.45f, 0.47f, 0.52f, 1.f); y += lh;
        text(x, y, "chip = toggle (one path)  |  label = inspect (C2)",
             0.45f, 0.47f, 0.52f, 1.f); y += lh + 4;
        scene_row_rects_.assign(scene_.size(), {0.f, 0.f, 0.f, 0.f});
        scene_sel_rects_.assign(scene_.size(), {0.f, 0.f, 0.f, 0.f});
        const float chip_w = 5 * advance_;
        for (size_t i = 0; i < scene_.size(); ++i) {
            if (y > y_max) {
                text(x, y_max, "... (clipped - widen this dock or collapse the reel to read on)",
                     0.85f, 0.55f, 0.30f, 1.f);
                break;
            }
            const SceneRow& r = scene_[i];
            bool is_sel = static_cast<int>(i) == inspect_row_;
            if (is_sel) rect(R[1][0] + 2, y - 2, R[1][2] - 4, lh + 4, 0.13f, 0.16f, 0.24f, 0.95f);
            if (r.toggleable) {
                bool on = r.state != 0;
                text(x, y, on ? "[on] " : "[off]",
                     on ? 0.25f : 0.62f, on ? 0.75f : 0.40f, on ? 0.35f : 0.36f, 1.f);
                // the chip is the toggle; the label is the inspector (C2) —
                // two intents, two rects, never crossed
                hots_.push_back({ x - 2, y - 2, chip_w + 8, lh + 4, 600 + static_cast<int>(i) });
                scene_row_rects_[i] = { x - 2, y - 2, chip_w + 8, lh + 4 };
                hots_.push_back({ x + chip_w + 4, y - 2, R[1][2] - 20 - chip_w - 4, lh + 4,
                                  700 + static_cast<int>(i) });
                scene_sel_rects_[i] = { x + chip_w + 4, y - 2, R[1][2] - 20 - chip_w - 4, lh + 4 };
            } else {
                text(x, y, " --  ", 0.45f, 0.47f, 0.52f, 1.f);
                hots_.push_back({ x - 2, y - 2, R[1][2] - 20, lh + 4, 700 + static_cast<int>(i) });
                scene_sel_rects_[i] = { x - 2, y - 2, R[1][2] - 20, lh + 4 };
            }
            text(x + chip_w + 6, y, r.label,
                 is_sel ? 0.45f : TR, is_sel ? 0.75f : TG, is_sel ? 1.00f : TB, 1.f);
            float dx = x + chip_w + 6 + (r.label.size() + 1) * advance_;
            text(dx, y, r.detail, 0.45f, 0.47f, 0.52f, 1.f);
            y += lh + 2;
        }
    } else if (!left_.collapsed && left_mode_ == 1) {
        // C1: THE JOINTS EDITOR. Every row is the pack's own data: name, the
        // derived ROM as the slider's hard range, the live theta from the
        // joints state buffer. Click a name -> gizmo + weight-paint on that
        // joint (the engine owns the selection); drag a slider -> an intent.
        float x = R[1][0] + 10, y = R[1][1] + 30;
        float y_max = R[1][1] + R[1][3] - lh;
        if (joints_.empty()) {
            text(x, y, "no joints pack - POST .tmp/skeleton/joints_pack.bin", 0.85f, 0.55f, 0.30f, 1.f); y += lh;
            text(x, y, "to /joints_bin, then /joints on", 0.85f, 0.55f, 0.30f, 1.f); y += lh;
        } else {
            char hb[128];
            snprintf(hb, sizeof(hb), "pose owner: %s   [%zu joints]",
                     joints_owner_ui_ == 1 ? "EDIT (sliders)" : "show (clock)", joints_.size());
            text(x, y, hb, joints_owner_ui_ == 1 ? 0.55f : 0.62f,
                     joints_owner_ui_ == 1 ? 0.85f : 0.66f, joints_owner_ui_ == 1 ? 0.55f : 0.74f, 1.f); y += lh;
            text(x, y, "click a name = gizmo + weight-paint (again to clear)",
                 0.45f, 0.47f, 0.52f, 1.f); y += lh;
            text(x, y, "drag a slider = pose intent (clamps to the derived ROM)",
                 0.45f, 0.47f, 0.52f, 1.f); y += lh + 4;
            const float name_w = 15 * advance_;
            const float val_w  = 8 * advance_;
            float tx = x + name_w + 4;
            float tw = R[1][0] + R[1][2] - 10 - val_w - 4 - tx;
            slider_tracks_.assign(joints_.size(), {0, 0, 0, 0});
            for (size_t i = 0; i < joints_.size(); ++i) {
                if (y > y_max) {
                    text(x, y_max, "... (clipped - widen this dock or collapse the reel to read on)",
                         0.85f, 0.55f, 0.30f, 1.f);
                    break;
                }
                const StudioJoint& jn = joints_[i];
                bool sel = static_cast<int>(i) == joints_sel_ui_;
                if (sel) rect(R[1][0] + 2, y - 2, R[1][2] - 4, lh + 4, 0.13f, 0.16f, 0.24f, 0.95f);
                text(x, y, jn.name, sel ? 0.45f : TR, sel ? 0.75f : TG, sel ? 1.00f : TB, 1.f);
                hots_.push_back({ x - 2, y - 2, name_w + 6, lh + 4, 400 + static_cast<int>(i) });
                // the track: ROM span, zero line, the theta thumb — all derived
                float range = jn.flex - jn.ext;
                float track_y = y + (lh - 6) * 0.5f;
                rect(tx, track_y, tw, 6, 0.12f, 0.13f, 0.17f, 0.95f);
                rect_outline(tx, track_y, tw, 6, 1.f, sel ? 0.30f : 0.35f,
                             sel ? 0.60f : 0.37f, sel ? 1.00f : 0.42f, 1.f);
                if (range > 0.f) {
                    float zx = tx + (0.0f - jn.ext) / range * tw;      // theta = 0 (rest)
                    rect(zx - 0.5f, track_y - 1, 1.f, 8, 0.45f, 0.47f, 0.52f, 1.f);
                    float fx = tx + (jn.theta - jn.ext) / range * tw;  // the live theta
                    rect(fx - 2.f, track_y - 3, 4.f, 12, sel ? 0.30f : 1.0f,
                         sel ? 0.60f : 0.85f, sel ? 1.00f : 0.40f, 1.f);
                }
                slider_tracks_[i] = { tx, track_y, tw, 6.f };
                char vb[32]; snprintf(vb, sizeof(vb), "%+7.2f", jn.theta);
                text(tx + tw + 4, y, vb, 1.0f, 0.85f, 0.40f, 1.f);
                y += lh + 6;
            }
        }
    } else if (!left_.collapsed && have_sel) {
        // B3: the Operating Manual's task envelope, rendered. Every word below
        // is the pipeline doc's own; the panel invents nothing.
        const StudioStage& st = board_.stages[selected_stage_];
        float cr, cg, cb; status_color(st.status, cr, cg, cb);
        size_t maxc = static_cast<size_t>((R[1][2] - 20) / advance_);
        float x = R[1][0] + 10, y = R[1][1] + 30;
        float y_max = R[1][1] + R[1][3] - lh;
        auto row = [&](const char* label, const std::string& body, float r, float g, float b) {
            if (y > y_max) return;
            text(x, y, label, 0.62f, 0.66f, 0.74f, 1.f); y += lh;
            y = text_wrap(x + 8, y, body, maxc - 2, r, g, b, 1.f, y_max); y += 4;
        };
        text(x, y, st.status, cr, cg, cb, 1.f);
        std::string hint = "  [click the node again to close]";
        text(x + st.status.size() * advance_ + 4, y, hint, 0.45f, 0.47f, 0.52f, 1.f); y += lh + 6;
        row("LAW (verbatim):", st.law, TR, TG, TB);
        row("FALSIFIER (named before the run):", st.falsifier, 1.0f, 0.85f, 0.40f);
        row("VERDICT (the doc's own row):", st.cell, cr, cg, cb);
        row("REFEREE TOOL:", st.tool, TR, TG, TB);
        row("ARTIFACT:", st.artifact, 0.55f, 0.85f, 0.55f);
        if (!st.spec.empty()) {
            if (y <= y_max) { text(x, y, "NEXT ACTION (the envelope):", 0.62f, 0.66f, 0.74f, 1.f); y += lh; }
            float y_end = text_wrap(x + 8, y, st.spec, maxc - 2, TR, TG, TB, 0.95f, y_max);
            if (y_end > y_max + lh) {
                // clipped: say so, honestly — the Blender law is that areas yield
                // space (collapse the reel/timeline or widen the dock to read on)
                rect(R[1][0], y_max - 2, R[1][2], lh + 4, 0.07f, 0.08f, 0.11f, 0.95f);
                text(x, y_max, "... (clipped - widen this dock or collapse the reel to read on)",
                     0.85f, 0.55f, 0.30f, 1.f);
            }
            y = y_end;
        } else if (y <= y_max) {
            text(x, y, "NEXT ACTION: (no envelope in the doc yet - the row above is the law)",
                 0.85f, 0.55f, 0.30f, 1.f);
        }
    } else if (!left_.collapsed) {
        float x = R[1][0] + 10, y = R[1][1] + 30;
        text(x, y, "the JOIN of engine state + repo truth", 0.55f, 0.58f, 0.65f, 1.f); y += lh + 6;
        text(x, y, board_.loaded ? "board: live (studio_board.json)" : "board: no file yet",
             board_.loaded ? 0.25f : 0.85f, board_.loaded ? 0.75f : 0.55f, board_.loaded ? 0.35f : 0.30f, 1.f); y += lh;
        text(x, y, "feed: tools/studio_board.py", 0.45f, 0.47f, 0.52f, 1.f); y += lh + 8;
        text(x, y, "workspaces (A3 - click to switch):", 0.62f, 0.66f, 0.74f, 1.f); y += lh + 2;
        const char* ws[] = {"BOARD   (this strip)", "SCENE   - the outliner (C4)", "JOINTS  - the editor (C1)", "GAIT    - parked",
                            "WATER   - parked", "FROST   - parked", "CAPTURE - render-to-MP4 (D5)", "DOCS    - the browser (E1)",
                            "LOG     - the recorder (F4)"};
        for (int i = 0; i < 9; ++i) {
            bool live = (i == 0 || i == 1 || i == 2 || i == 6 || i == 7 || i == 8);
            text(x + 8, y, ws[i], live ? 0.30f : 0.42f, live ? 0.60f : 0.44f, live ? 1.00f : 0.50f, 1.f);
            if (live) hots_.push_back({ x + 4, y - 2, R[1][2] - 30, lh + 4, 300 + i });
            y += lh;
        }
        y += 6;
        text(x, y, "click a stage node above -> its envelope (B3)", 0.30f, 0.60f, 1.00f, 1.f); y += lh;
        text(x, y, "next per the menu: C2 inspector, D5 render-to-MP4, D6 bookmarks", 0.45f, 0.47f, 0.52f, 1.f); y += lh;
        text(x, y, "(docs/THE_ENGINE_STUDIO.md)", 0.45f, 0.47f, 0.52f, 1.f);
    }

    // ── the STATUS panel (right): the engine's own live rows, honest — or,
    // when an outliner row is selected, the INSPECTOR (C2): the atom's full
    // state document, engine-composed. The FPS pulse stays on top either way.
    rect(R[2][0], R[2][1], R[2][2], R[2][3], 0.07f, 0.08f, 0.11f, 0.85f);
    rect(R[2][0], R[2][1], R[2][2], 22, 0.13f, 0.14f, 0.19f, 0.95f);
    {
        std::string rtitle = inspect_row_ >= 0
            ? "INSPECT - " + inspect_label_ + " (C2)" : "STATUS (live)";
        text(R[2][0] + 8, R[2][1] + (22 - lh) * 0.5f,
             right_.collapsed ? "+" : rtitle, TR, TG, TB, 1.f);
    }
    if (!right_.collapsed) {
        float x = R[2][0] + 10, y = R[2][1] + 30;
        float y_max = R[2][1] + R[2][3] - lh;
        char buf[128];
        snprintf(buf, sizeof(buf), "FPS %.0f | ft avg %.2f ms | max %.2f ms", fps_, ft_avg_, ft_max_);
        text(x, y, buf, 0.55f, 0.85f, 0.55f, 1.f); y += lh + 6;
        if (inspect_row_ >= 0) {
            // C2: every line is the engine's document for the selected atom —
            // key dim, value bright; the panel invents nothing.
            for (const auto& kv : inspect_kv_) {
                if (y > y_max) break;
                text(x, y, kv.first, 0.62f, 0.66f, 0.74f, 1.f);
                text(x + 16 * advance_, y, kv.second, TR, TG, TB, 1.f);
                y += lh;
            }
            if (!inspect_hint_.empty() && y <= y_max) {
                y += 4;
                text(x, y, inspect_hint_, 0.45f, 0.47f, 0.52f, 1.f); y += lh;
            }
            if (y <= y_max)
                text(x, y, "[click the row again to close]", 0.45f, 0.47f, 0.52f, 1.f);
        } else {
            for (const std::string& line : status_lines_) {
                text(x, y, line, TR, TG, TB, 0.95f); y += lh;
                if (y > y_max) break;
            }
        }
    }

    // ── the REEL (D3: every /frame grab lands here — the evidence tray, on-screen) ──
    rect(R[4][0], R[4][1], R[4][2], R[4][3], 0.07f, 0.08f, 0.11f, 0.88f);
    rect(R[4][0], R[4][1], R[4][2], 22, 0.13f, 0.14f, 0.19f, 0.95f);
    {
        char rb[64];
        snprintf(rb, sizeof(rb), "REEL (D3) - every /frame grab lands here  [%d/%d]", reel_count_, REEL_MAX);
        text(R[4][0] + 8, R[4][1] + (22 - lh) * 0.5f, reel_.collapsed ? "+" : rb, 0.62f, 0.66f, 0.74f, 1.f);
    }
    if (!reel_.collapsed) {
        float cap_h = 3 * lh + 8;                            // the three metadata lines under a tile
        float th = R[4][3] - 22 - 8 - cap_h;                 // thumbnail draw height
        if (th < 24.f) th = 24.f;
        float tw = th * (16.f / 9.f);
        if (reel_count_ == 0) {
            text(R[4][0] + 10, R[4][1] + 30,
                 "no grabs yet - GET /frame (or /stream) and the capture docks here with its t, joint, theta, camera",
                 0.85f, 0.55f, 0.30f, 1.f);
        } else {
            int show_n = reel_count_ < REEL_MAX ? reel_count_ : REEL_MAX;
            for (int k = 0; k < show_n; ++k) {
                float tx = R[4][0] + 10 + k * (tw + 10);
                if (tx + tw > R[4][0] + R[4][2] - 8) break;  // clip: the newest stay visible
                int slot = static_cast<int>((reel_seq_ - 1 - k) % REEL_MAX);  // newest first
                const ReelTile& tl = tiles_[slot];
                float ty = R[4][1] + 26;
                rect(tx - 1, ty - 1, tw + 2, th + 2, 0.35f, 0.37f, 0.42f, 1.f);
                if (tl.used) thumb(tx, ty, tw, th, slot);
                float ly = ty + th + 4;
                // caption lines clip to the tile width (monospace: arithmetic, not hope)
                size_t fit = static_cast<size_t>(tw / advance_);
                std::string s1 = tl.l1.size() > fit ? tl.l1.substr(0, fit) : tl.l1;
                std::string s2 = tl.l2.size() > fit ? tl.l2.substr(0, fit) : tl.l2;
                std::string s3 = tl.l3.size() > fit ? tl.l3.substr(0, fit) : tl.l3;
                text(tx, ly,          s1, 1.0f, 0.85f, 0.40f, 1.f);
                text(tx, ly + lh,     s2, TR, TG, TB, 0.95f);
                text(tx, ly + 2 * lh, s3, 0.45f, 0.47f, 0.52f, 1.f);
            }
        }
    }

    // ── the TIMELINE (D1: the show clock, drawn; the engine owns the time) ──
    rect(R[3][0], R[3][1], R[3][2], R[3][3], 0.07f, 0.08f, 0.11f, 0.88f);
    rect(R[3][0], R[3][1], R[3][2], 22, 0.13f, 0.14f, 0.19f, 0.95f);
    text(R[3][0] + 8, R[3][1] + (22 - lh) * 0.5f,
         bottom_.collapsed ? "+" : "TIMELINE (D1) - the show clock is a parameter",
         0.62f, 0.66f, 0.74f, 1.f);
    if (!bottom_.collapsed) {
        float x = R[3][0] + 10, y = R[3][1] + 28;
        // buttons: [PAUSE/PLAY] [-1f] [+1f] [speed] — ASCII glyphs (the atlas is ASCII)
        auto button = [&](float& bx, const std::string& label, int id, bool hot) {
            float bw = label.size() * advance_ + 14;
            rect(bx, y, bw, 20, 0.16f, 0.17f, 0.22f, 0.95f);
            rect_outline(bx, y, bw, 20, 1.f, hot ? 0.30f : 0.45f, hot ? 0.60f : 0.47f,
                         hot ? 1.00f : 0.52f, 1.f);
            text(bx + 7, y + (20 - lh) * 0.5f, label, TR, TG, TB, 1.f);
            hots_.push_back({ bx, y, bw, 20, id });
            bx += bw + 8;
        };
        float bx = x;
        button(bx, clk_playing_ ? "PAUSE" : "PLAY ", 1, true);
        button(bx, " -1f ", 2, false);
        button(bx, " +1f ", 3, false);
        char spb[16]; snprintf(spb, sizeof(spb), " %.2gx ", clk_speed_);
        button(bx, spb, 4, false);

        // the readout: time / loop, joint, theta, state — the engine's own rows
        char tb[192];
        snprintf(tb, sizeof(tb), "t = %.3f s / %.1f s  |  %s theta = %+.2f deg  |  %s",
                 clk_t_, clk_total_, clk_name_.c_str(), clk_theta_,
                 clk_playing_ ? "PLAYING" : "PAUSED (scrub/step = exact poses)");
        text(bx + 10, y + (20 - lh) * 0.5f, tb, 1.0f, 0.85f, 0.40f, 1.f);

        // the scrub bar: joint markers auto from the show clock (D2's seed)
        float bar_y = y + 30;
        float bar_h = 16.f;
        scrub_rect_[0] = x; scrub_rect_[1] = bar_y;
        scrub_rect_[2] = R[3][0] + R[3][2] - 10 - x; scrub_rect_[3] = bar_h;
        if (clk_n_ == 0 || clk_total_ <= 0.0) {
            text(x, bar_y, "no joints pack - POST .tmp/skeleton/joints_pack.bin to /joints_bin, then /joints on",
                 0.85f, 0.55f, 0.30f, 1.f);
        } else {
            rect(scrub_rect_[0], bar_y, scrub_rect_[2], bar_h, 0.12f, 0.13f, 0.17f, 0.95f);
            rect_outline(scrub_rect_[0], bar_y, scrub_rect_[2], bar_h, 1.f, 0.35f, 0.37f, 0.42f, 1.f);
            for (uint32_t i = 0; i < clk_n_; ++i) {
                float fx = scrub_rect_[0] + (i * clk_period_ / clk_total_) * scrub_rect_[2];
                bool cur = (i == clk_cur_);
                rect(fx, bar_y + 2, 2.f, bar_h - 4,
                     cur ? 0.30f : 0.45f, cur ? 0.60f : 0.47f, cur ? 1.00f : 0.52f, 1.f);
            }
            // the playhead (loops over the show's total)
            double lt = clk_total_ > 0.0 ? clk_t_ - floor(clk_t_ / clk_total_) * clk_total_ : 0.0;
            float px = scrub_rect_[0] + static_cast<float>(lt / clk_total_) * scrub_rect_[2];
            rect(px - 1, bar_y - 2, 3, bar_h + 4, 1.f, 1.f, 1.f, 1.f);
            // per-loop marker labels: current joint's name over its window
            char jb[96];
            snprintf(jb, sizeof(jb), "joint %u/%u: %s  (%.1f s windows)", clk_cur_ + 1, clk_n_,
                     clk_name_.c_str(), clk_period_);
            text(x, bar_y + bar_h + 6, jb, 0.62f, 0.66f, 0.74f, 1.f);
        }
    }

    // ── C1: THE GIZMO — the selected joint's center + axis over the viewport,
    // projected by the engine through the mesh pass's own VP (drawn last, over
    // everything — it is screen-space truth about the model underneath) ──
    if (gizmo_vis_ && visible) {
        line(gizmo_[0], gizmo_[1], gizmo_[2], gizmo_[3], 2.5f, 1.0f, 0.85f, 0.20f, 1.f);
        rect(gizmo_[0] - 3, gizmo_[1] - 3, 6, 6, 1.0f, 0.85f, 0.20f, 1.f);   // J, the center
        rect_outline(gizmo_[0] - 5, gizmo_[1] - 5, 10, 10, 1.f, 0.2f, 0.2f, 0.2f, 1.f);
        text(gizmo_[0] + 8, gizmo_[1] - lh * 0.5f, gizmo_label_, 1.0f, 0.85f, 0.40f, 1.f);
    }

    build_chrome();   // F2/F3: the status bar + HUD draw over everything, always
    build_console();  // F1: the console tops everything when it's open
}

// ── F1: THE CONSOLE — the HTTP API's interactive twin ──────────────────────
// The UI collects the line and ISSUES it; the engine's worker executes it
// through the same handler the HTTP server runs (the panels' law: the UI
// never owns execution). Input is WM_CHAR-routed so shifted JSON punctuation
// ('{', '"', ':') types exactly as the operator intends.

void StudioUI::console_char(int c) {
    if (c == '`') { console_toggle(); return; }         // the classic close
    else if (c == 13) {                                 // CR — submit
        console_submit_line(console_input_);
        console_input_.clear();
        console_hist_nav_ = -1;
    } else if (c == 8) {                                // backspace
        if (!console_input_.empty()) console_input_.pop_back();
    } else if (c >= 32 && c < 127) {
        console_input_.push_back(static_cast<char>(c));
    }
}

void StudioUI::console_key(int vk) {
    if (vk == 0x1B) { console_toggle(); return; }       // ESCAPE closes
    if (vk == 0x26) {                                   // UP — recall older
        if (console_history_.empty()) return;
        if (console_hist_nav_ < 0) console_hist_nav_ = static_cast<int>(console_history_.size()) - 1;
        else if (console_hist_nav_ > 0) --console_hist_nav_;
        console_input_ = console_history_[console_hist_nav_];
    } else if (vk == 0x28) {                            // DOWN — recall newer
        if (console_hist_nav_ < 0) return;
        ++console_hist_nav_;
        if (console_hist_nav_ >= static_cast<int>(console_history_.size())) {
            console_hist_nav_ = -1;
            console_input_.clear();
        } else {
            console_input_ = console_history_[console_hist_nav_];
        }
    }
}

void StudioUI::console_submit_line(const std::string& line) {
    std::string t = line;
    size_t a = t.find_first_not_of(" \t"), b = t.find_last_not_of(" \t");
    if (a == std::string::npos) return;                 // an empty line is a no-op
    t = t.substr(a, b - a + 1);
    console_history_.push_back(t);
    console_log_.push_back({t, "", false});
    if (console_log_.size() > 200) console_log_.erase(console_log_.begin());
    if (cb_console_) cb_console_(t);                    // the engine owns execution
}

void StudioUI::console_result(const std::string& resp) {
    // the worker completes in order — land the response on the oldest open entry
    for (auto& e : console_log_) {
        if (!e.done) { e.resp = resp; e.done = true; return; }
    }
}

// F4: an event lands the moment it happens — the dock's tail and the session
// file carry the same line
void StudioUI::log_push(uint64_t seq, uint64_t total, const std::string& t,
                        const std::string& kind, const std::string& detail) {
    std::lock_guard<std::mutex> lk(log_m_);
    log_ring_.push_back({seq, t, kind, detail});
    if (log_ring_.size() > 200) log_ring_.erase(log_ring_.begin());
    log_total_ = total;
}

void StudioUI::build_console() {
    if (!console_open_) return;
    const float lh = cell_h_;
    const float W = static_cast<float>(ext_.width);
    const float H = static_cast<float>(ext_.height);
    float ch = H * 0.42f;
    rect(0, 0, W, ch, 0.04f, 0.05f, 0.08f, 0.93f);
    rect(0, ch - 1, W, 1, 0.30f, 0.60f, 1.00f, 0.9f);
    text(8, 4, "F1 CONSOLE - ` or ESC closes - METHOD /path [json] - enter runs - up/down history",
         0.55f, 0.58f, 0.65f, 1.f);

    // the prompt, with a steady underline cursor (honest — no blink clock)
    float py = ch - lh - 6;
    std::string prompt = "> " + console_input_;
    text(8, py, prompt, 0.86f, 0.88f, 0.92f, 1.f);
    rect(8 + static_cast<float>(prompt.size()) * advance_, py + lh - 4,
         advance_, 3, 0.86f, 0.88f, 0.92f, 1.f);

    // the scrollback, wrapped with the SAME greedy law as text_wrap, newest
    // last — take the tail that fits above the prompt and draw top-down
    size_t maxc = static_cast<size_t>((W - 16) / advance_);
    if (maxc < 8) maxc = 8;
    struct VLine { std::string s; bool resp; };
    std::vector<VLine> flat;
    for (const auto& e : console_log_) {
        std::string head = "> " + e.cmd;
        std::string body = e.done ? e.resp : "...";
        for (int part = 0; part < 2; ++part) {
            std::string para = part == 0 ? head : body;
            bool is_resp = part == 1;
            while (true) {
                if (para.size() <= maxc) { flat.push_back({para, is_resp}); break; }
                size_t cut = para.rfind(' ', maxc);
                if (cut == std::string::npos || cut == 0) cut = maxc;
                flat.push_back({para.substr(0, cut), is_resp});
                para = para.substr(cut + (cut < para.size() && para[cut] == ' ' ? 1 : 0));
            }
        }
    }
    int fit = static_cast<int>((py - 6 - (lh + 6)) / lh);
    if (fit < 0) fit = 0;
    size_t start = flat.size() > static_cast<size_t>(fit) ? flat.size() - fit : 0;
    float y = py - 6 - lh * static_cast<float>(flat.size() - start);
    for (size_t i = start; i < flat.size(); ++i) {
        if (flat[i].resp) text(8, y, flat[i].s, 0.55f, 0.90f, 0.65f, 1.f);
        else              text(8, y, flat[i].s, 0.62f, 0.66f, 0.74f, 1.f);
        y += lh;
    }
}

// ── F2/F3: THE CHROME — the engine wearing its own vital signs ─────────────
// The bar owns the bottom BAR_H px (layout() yields it); the HUD rows sit at
// the viewport's top-left (right of the left dock when the overlay is open).
// Every string drawn here is ALSO the string the HTTP twin serves — one
// formatting site, so the glass and the twin can never disagree.

void StudioUI::build_chrome() {
    const float lh = cell_h_;
    const float W = static_cast<float>(ext_.width);
    const float H = static_cast<float>(ext_.height);
    char b[256];

    // ── F3: the HUD rows — present only while their mode is live ──
    float R[5][4]; layout(ext_.width, ext_.height, R);
    float hx = visible ? R[1][0] + R[1][2] + 10.f : 10.f;
    float hy = visible ? R[0][3] + 8.f : 10.f;
    hud_rows_.clear();
    if (hud_show_on()) {
        const StudioJoint& j = joints_[clk_cur_ < joints_.size() ? clk_cur_ : 0];
        snprintf(b, sizeof(b), "SHOW %s  theta %.2f deg  ROM [%.1f .. %.1f]",
                 clk_name_.c_str(), clk_theta_, j.ext, j.flex);
        hud_rows_.emplace_back(b);
    }
    if (hud_gait_.on) {
        snprintf(b, sizeof(b), "GAIT lamL %.3f  lamR %.3f (surrogate)  steps %llu  omega %.2f",
                 hud_gait_.lamL, hud_gait_.lamR,
                 static_cast<unsigned long long>(hud_gait_.steps), hud_gait_.omega);
        hud_rows_.emplace_back(b);
    }
    if (hud_water_.on) {
        snprintf(b, sizeof(b), "WATER steps %llu  dt %.3f  inj %d/%d",
                 static_cast<unsigned long long>(hud_water_.steps), hud_water_.dt,
                 hud_water_.inj_t, hud_water_.inj_c);
        hud_rows_.emplace_back(b);
    }
    for (size_t i = 0; i < hud_rows_.size(); ++i) {
        // a dark chip behind each row keeps it readable over any render
        float rw = static_cast<float>(hud_rows_[i].size()) * advance_ + 16.f;
        rect(hx - 6, hy - 3, rw, lh + 6, 0.05f, 0.06f, 0.09f, 0.75f);
        text(hx, hy, hud_rows_[i], 0.55f, 0.90f, 0.65f, 1.f);
        hy += lh + 4;
    }

    // ── D6: the camera bookmarks — one chip per named shot, then "+ cam".
    // Same chip language as the HUD rows; click = recall, "+" = save the live
    // camera. The rects are the aim map the /cameras twin serves.
    cam_mark_rects_.assign(cam_marks_.size(), {0.f, 0.f, 0.f, 0.f});
    cam_save_rect_ = {0.f, 0.f, 0.f, 0.f};
    {
        float cx2 = hx - 6, cy = hy - 3;
        for (size_t i = 0; i < cam_marks_.size(); ++i) {
            std::string cap = "[" + std::to_string(i + 1) + " " + cam_marks_[i] + "]";
            float cw = static_cast<float>(cap.size()) * advance_ + 12.f;
            rect(cx2, cy, cw, lh + 6, 0.10f, 0.13f, 0.22f, 0.85f);
            rect_outline(cx2, cy, cw, lh + 6, 1.f, 0.30f, 0.60f, 1.00f, 0.9f);
            text(cx2 + 6, cy + 3, cap, 0.30f, 0.60f, 1.00f, 1.f);
            hots_.push_back({ cx2, cy, cw, lh + 6, 800 + static_cast<int>(i) });
            cam_mark_rects_[i] = { cx2, cy, cw, lh + 6 };
            cx2 += cw + 6;
        }
        std::string cap = "+ cam";
        float cw = static_cast<float>(cap.size()) * advance_ + 12.f;
        rect(cx2, cy, cw, lh + 6, 0.05f, 0.06f, 0.09f, 0.75f);
        rect_outline(cx2, cy, cw, lh + 6, 1.f, 0.45f, 0.47f, 0.52f, 0.9f);
        text(cx2 + 6, cy + 3, cap, 0.45f, 0.47f, 0.52f, 1.f);
        hots_.push_back({ cx2, cy, cw, lh + 6, 850 });
        cam_save_rect_ = { cx2, cy, cw, lh + 6 };
    }

    // ── F2: the status bar ──
    if (!bar_on_) { chrome_stage_.clear(); chrome_fps_.clear(); chrome_gpu_.clear(); return; }
    float by = H - BAR_H;
    rect(0, by, W, BAR_H, 0.06f, 0.07f, 0.10f, 0.95f);
    rect(0, by, W, 1.f, 0.30f, 0.60f, 1.00f, 0.9f);   // the studio's accent line

    // left: the board's standing line, verbatim (the current-stage readout)
    chrome_stage_ = board_.loaded ? board_.standing : "no board file";
    text(8, by + (BAR_H - lh) * 0.5f, chrome_stage_, 0.30f, 0.60f, 1.00f, 1.f);

    // center: FPS + the frame-time histogram (the ring, oldest -> newest)
    float hist_w = static_cast<float>(FT_RING) * 3.f;
    float cx = W * 0.5f - hist_w * 0.5f;
    snprintf(b, sizeof(b), "%.0f fps  %.2f ms", fps_, ft_avg_);
    chrome_fps_ = b;
    text(cx - 8 - static_cast<float>(chrome_fps_.size()) * advance_,
         by + (BAR_H - lh) * 0.5f, chrome_fps_, 0.86f, 0.88f, 0.92f, 1.f);
    float hb = by + 3.f, hh = BAR_H - 6.f;
    rect(cx, hb, hist_w, hh, 0.10f, 0.11f, 0.15f, 0.9f);
    for (int i = 0; i < ft_ring_n_; ++i) {
        float v = ft_ring_[(ft_ring_head_ - ft_ring_n_ + i + FT_RING) % FT_RING];
        float f = v / 33.3f; if (f > 1.f) f = 1.f;
        float bh2 = f * hh; if (bh2 < 1.f && v > 0.f) bh2 = 1.f;
        float cr = 0.30f, cg = 0.80f, cb = 0.40f;            // < 16.7 ms: green
        if (v > 33.3f)      { cr = 0.90f; cg = 0.25f; cb = 0.25f; }
        else if (v > 16.7f) { cr = 0.95f; cg = 0.75f; cb = 0.20f; }
        rect(cx + i * 3.f, hb + hh - bh2, 2.f, bh2, cr, cg, cb, 1.f);
    }
    // the 16.7 ms line — the 60 fps budget, drawn across the histogram
    rect(cx, hb + hh * (1.f - 16.7f / 33.3f), hist_w, 1.f, 1.f, 1.f, 1.f, 0.45f);

    // right: the GPU's own name + the swapchain extent
    snprintf(b, sizeof(b), "%s  %ux%u", gpu_name_.c_str(), ext_.width, ext_.height);
    chrome_gpu_ = b;
    text(W - 8 - static_cast<float>(chrome_gpu_.size()) * advance_,
         by + (BAR_H - lh) * 0.5f, chrome_gpu_, 0.55f, 0.58f, 0.65f, 1.f);
}

// ── Vulkan: init / resources / record ─────────────────────────────────────────

bool StudioUI::ensure_vbuf(VkDeviceSize bytes) {
    if (vcap_ >= bytes) return true;
    if (vbuf_ != VK_NULL_HANDLE) {
        vkDeviceWaitIdle(dev_);
        vkDestroyBuffer(dev_, vbuf_, nullptr);
        vkFreeMemory(dev_, vmem_, nullptr);
        vbuf_ = VK_NULL_HANDLE; vmap_ = nullptr;
    }
    VkDeviceSize cap = bytes * 2;
    VkBufferCreateInfo bci{};
    bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bci.size  = cap;
    bci.usage = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT;
    if (vkCreateBuffer(dev_, &bci, nullptr, &vbuf_) != VK_SUCCESS) return false;
    VkMemoryRequirements mr; vkGetBufferMemoryRequirements(dev_, vbuf_, &mr);
    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = mr.size;
    ai.memoryTypeIndex = mem_type_host_;
    if (vkAllocateMemory(dev_, &ai, nullptr, &vmem_) != VK_SUCCESS) return false;
    vkBindBufferMemory(dev_, vbuf_, vmem_, 0);
    vkMapMemory(dev_, vmem_, 0, cap, 0, &vmap_);
    vcap_ = cap;
    return true;
}

void StudioUI::record(VkCommandBuffer cb) {
    if (verts_.empty() || !ok()) return;
    VkDeviceSize bytes = verts_.size() * sizeof(Vert);
    if (!ensure_vbuf(bytes)) return;
    std::memcpy(vmap_, verts_.data(), bytes);

    VkViewport vp{};
    vp.width = static_cast<float>(ext_.width); vp.height = static_cast<float>(ext_.height);
    vp.minDepth = 0.f; vp.maxDepth = 1.f;
    vkCmdSetViewport(cb, 0, 1, &vp);
    VkRect2D sc{}; sc.extent = ext_;
    vkCmdSetScissor(cb, 0, 1, &sc);

    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, pipe_);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, layout_, 0, 1, &dset_, 0, nullptr);
    float pc[2] = { static_cast<float>(ext_.width), static_cast<float>(ext_.height) };
    vkCmdPushConstants(cb, layout_, VK_SHADER_STAGE_VERTEX_BIT, 0, sizeof(pc), pc);
    VkDeviceSize off = 0;
    vkCmdBindVertexBuffers(cb, 0, 1, &vbuf_, &off);
    vkCmdDraw(cb, static_cast<uint32_t>(verts_.size()), 1, 0, 0);
}

bool StudioUI::create_font_atlas() {
    // GDI rasterization of the system monospace font — zero vendored assets.
    HDC hdc = CreateCompatibleDC(nullptr);
    if (!hdc) return false;
    HFONT font = CreateFontW(-16, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                             DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                             CLEARTYPE_QUALITY, FIXED_PITCH | FF_MODERN, L"Consolas");
    if (!font) font = CreateFontW(-16, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                                  DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                                  CLEARTYPE_QUALITY, FIXED_PITCH | FF_MODERN, L"Courier New");
    HGDIOBJ old = SelectObject(hdc, font);
    TEXTMETRICW tm{};
    GetTextMetricsW(hdc, &tm);
    cell_w_  = static_cast<float>(tm.tmAveCharWidth + 3);
    cell_h_  = static_cast<float>(tm.tmHeight + 5);
    advance_ = static_cast<float>(tm.tmAveCharWidth);
    ascent_  = tm.tmAscent;

    int aw = static_cast<int>(cell_w_ * ATLAS_COLS);
    int ah = static_cast<int>(cell_h_ * ATLAS_ROWS);

    BITMAPINFO bmi{};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = aw;
    bmi.bmiHeader.biHeight = -ah;          // top-down
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;
    void* bits = nullptr;
    HBITMAP bmp = CreateDIBSection(hdc, &bmi, DIB_RGB_COLORS, &bits, nullptr, 0);
    if (!bmp) { DeleteObject(font); DeleteDC(hdc); return false; }
    HGDIOBJ oldbmp = SelectObject(hdc, bmp);
    std::memset(bits, 0, static_cast<size_t>(aw) * ah * 4);
    SetTextColor(hdc, RGB(255, 255, 255));
    SetBkMode(hdc, TRANSPARENT);
    for (int ch = 32; ch < 127; ++ch) {
        int idx = ch - 32;
        int cx = (idx % ATLAS_COLS) * static_cast<int>(cell_w_);
        int cy = (idx / ATLAS_COLS) * static_cast<int>(cell_h_);
        wchar_t wc = static_cast<wchar_t>(ch);
        TextOutW(hdc, cx + 1, cy + 2, &wc, 1);
    }
    // index 95 (the DEL slot): solid white cell for colored rects
    {
        int cx = 15 * static_cast<int>(cell_w_);
        int cy = 5 * static_cast<int>(cell_h_);
        uint8_t* px = static_cast<uint8_t*>(bits);
        for (int y = 0; y < static_cast<int>(cell_h_); ++y)
            for (int x = 0; x < static_cast<int>(cell_w_); ++x) {
                size_t o = (static_cast<size_t>(cy + y) * aw + (cx + x)) * 4;
                px[o + 0] = px[o + 1] = px[o + 2] = 255;
            }
    }
    // pack to RGBA8 (rgb=white, a=coverage; the thumb grid below starts at a=0)
    // D3: ONE image holds the font cells AND the reel's 4x3 thumbnail grid.
    // The font cells are the top-left aw x ah sub-rect of an atlas_w_-wide image —
    // the row stride is atlas_w_, not aw (getting this wrong smears every glyph).
    atlas_w_ = static_cast<uint32_t>(aw) > static_cast<uint32_t>(4 * THUMB_W)
             ? static_cast<uint32_t>(aw) : static_cast<uint32_t>(4 * THUMB_W);
    atlas_h_ = static_cast<uint32_t>(ah) + 3 * THUMB_H;
    std::vector<uint8_t> r8(static_cast<size_t>(atlas_w_) * atlas_h_ * 4, 0);
    {
        const uint8_t* px = static_cast<const uint8_t*>(bits);
        for (size_t y = 0; y < static_cast<size_t>(ah); ++y)
            for (size_t x = 0; x < static_cast<size_t>(aw); ++x) {
                size_t di = (y * atlas_w_ + x) * 4;
                r8[di + 0] = 255; r8[di + 1] = 255; r8[di + 2] = 255;
                r8[di + 3] = px[(y * aw + x) * 4];
            }
    }
    SelectObject(hdc, oldbmp); DeleteObject(bmp);
    SelectObject(hdc, old);    DeleteObject(font);
    DeleteDC(hdc);

    // upload: staging -> image (init-time only; one-shot command pool of our own)
    VkBuffer stage; VkDeviceMemory smem;
    VkBufferCreateInfo bci{};
    bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bci.size  = r8.size();
    bci.usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
    if (vkCreateBuffer(dev_, &bci, nullptr, &stage) != VK_SUCCESS) return false;
    VkMemoryRequirements mr; vkGetBufferMemoryRequirements(dev_, stage, &mr);
    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = mr.size;
    ai.memoryTypeIndex = mem_type_host_;
    if (vkAllocateMemory(dev_, &ai, nullptr, &smem) != VK_SUCCESS) return false;
    vkBindBufferMemory(dev_, stage, smem, 0);
    void* mp = nullptr;
    vkMapMemory(dev_, smem, 0, r8.size(), 0, &mp);
    std::memcpy(mp, r8.data(), r8.size());
    vkUnmapMemory(dev_, smem);

    VkImageCreateInfo ici{};
    ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType = VK_IMAGE_TYPE_2D;
    ici.format = VK_FORMAT_R8G8B8A8_UNORM;
    ici.extent = { atlas_w_, atlas_h_, 1 };
    ici.mipLevels = 1; ici.arrayLayers = 1;
    ici.samples = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling = VK_IMAGE_TILING_OPTIMAL;
    ici.usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    if (vkCreateImage(dev_, &ici, nullptr, &font_img_) != VK_SUCCESS) return false;
    VkMemoryRequirements imr; vkGetImageMemoryRequirements(dev_, font_img_, &imr);
    VkMemoryAllocateInfo iai{};
    iai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    iai.allocationSize = imr.size;
    // device-local for the sampled image: find a DEVICE_LOCAL type
    {
        VkPhysicalDeviceMemoryProperties mp2{};
        vkGetPhysicalDeviceMemoryProperties(phys_, &mp2);
        iai.memoryTypeIndex = UINT32_MAX;
        for (uint32_t i = 0; i < mp2.memoryTypeCount; ++i)
            if ((imr.memoryTypeBits & (1u << i)) &&
                (mp2.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)) {
                iai.memoryTypeIndex = i; break;
            }
        if (iai.memoryTypeIndex == UINT32_MAX) iai.memoryTypeIndex = mem_type_host_;
    }
    if (vkAllocateMemory(dev_, &iai, nullptr, &font_mem_) != VK_SUCCESS) return false;
    vkBindImageMemory(dev_, font_img_, font_mem_, 0);

    // one-shot copy on a private pool (the engine's queue is shared; init is pre-loop)
    extern VkQueue g_ui_queue;   // set by Engine::init before ui_.init
    extern VkCommandPool g_ui_cmd_pool;
    VkCommandBuffer cmd;
    VkCommandBufferAllocateInfo cai{};
    cai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    cai.commandPool = g_ui_cmd_pool;
    cai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cai.commandBufferCount = 1;
    vkAllocateCommandBuffers(dev_, &cai, &cmd);
    VkCommandBufferBeginInfo bbi{};
    bbi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    bbi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    vkBeginCommandBuffer(cmd, &bbi);
    auto barrier = [&](VkImageLayout oldl, VkImageLayout newl,
                       VkAccessFlags srca, VkAccessFlags dsta,
                       VkPipelineStageFlags srcs, VkPipelineStageFlags dsts) {
        VkImageMemoryBarrier b{};
        b.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
        b.oldLayout = oldl; b.newLayout = newl;
        b.srcAccessMask = srca; b.dstAccessMask = dsta;
        b.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        b.image = font_img_;
        b.subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };
        vkCmdPipelineBarrier(cmd, srcs, dsts, 0, 0, nullptr, 0, nullptr, 1, &b);
    };
    barrier(VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            0, VK_ACCESS_TRANSFER_WRITE_BIT,
            VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
    VkBufferImageCopy cp{};
    cp.imageSubresource = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1 };
    cp.imageExtent = { atlas_w_, atlas_h_, 1 };
    vkCmdCopyBufferToImage(cmd, stage, font_img_, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &cp);
    barrier(VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
            VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT,
            VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT);
    vkEndCommandBuffer(cmd);
    VkSubmitInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
    vkQueueSubmit(g_ui_queue, 1, &si, VK_NULL_HANDLE);
    vkQueueWaitIdle(g_ui_queue);
    vkFreeCommandBuffers(dev_, g_ui_cmd_pool, 1, &cmd);
    vkDestroyBuffer(dev_, stage, nullptr);
    vkFreeMemory(dev_, smem, nullptr);

    VkImageViewCreateInfo vci{};
    vci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    vci.image = font_img_;
    vci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    vci.format = VK_FORMAT_R8G8B8A8_UNORM;
    vci.subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };
    if (vkCreateImageView(dev_, &vci, nullptr, &font_view_) != VK_SUCCESS) return false;

    // D3: the reel's persistent thumb staging buffer (host-visible, mapped once)
    {
        VkBufferCreateInfo tbci{};
        tbci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        tbci.size = static_cast<VkDeviceSize>(THUMB_W) * THUMB_H * 4;
        tbci.usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
        if (vkCreateBuffer(dev_, &tbci, nullptr, &thumb_stage_) != VK_SUCCESS) return false;
        VkMemoryRequirements tmr; vkGetBufferMemoryRequirements(dev_, thumb_stage_, &tmr);
        VkMemoryAllocateInfo tai{};
        tai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        tai.allocationSize = tmr.size;
        tai.memoryTypeIndex = mem_type_host_;
        if (vkAllocateMemory(dev_, &tai, nullptr, &thumb_stage_mem_) != VK_SUCCESS) return false;
        vkBindBufferMemory(dev_, thumb_stage_, thumb_stage_mem_, 0);
        vkMapMemory(dev_, thumb_stage_mem_, 0, tbci.size, 0, &thumb_stage_map_);
    }

    VkSamplerCreateInfo sci{};
    sci.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    sci.magFilter = VK_FILTER_LINEAR;
    sci.minFilter = VK_FILTER_LINEAR;
    sci.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    if (vkCreateSampler(dev_, &sci, nullptr, &font_samp_) != VK_SUCCESS) return false;
    return true;
}

bool StudioUI::create_swap_resources(const std::vector<VkImageView>& views, VkExtent2D ext) {
    for (VkFramebuffer fb : fbs_) vkDestroyFramebuffer(dev_, fb, nullptr);
    fbs_.clear();
    ext_ = ext;
    fbs_.resize(views.size());
    for (size_t i = 0; i < views.size(); ++i) {
        VkImageView att[1] = { views[i] };
        VkFramebufferCreateInfo fci{};
        fci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass = rp_;
        fci.attachmentCount = 1;
        fci.pAttachments = att;
        fci.width = ext.width; fci.height = ext.height; fci.layers = 1;
        if (vkCreateFramebuffer(dev_, &fci, nullptr, &fbs_[i]) != VK_SUCCESS) return false;
    }
    return true;
}

bool StudioUI::init(VkDevice dev, VkPhysicalDevice phys, VkFormat swap_fmt,
                    uint32_t w, uint32_t h, uint32_t mem_type_host) {
    dev_ = dev; phys_ = phys; mem_type_host_ = mem_type_host;
    ext_ = { w, h };

    // render pass: LOAD the blitted 3D frame, draw, leave it PRESENT-able.
    // initialLayout matches the post-blit TRANSFER_DST (the idle path clears
    // into the same layout first, so one pass serves both).
    VkAttachmentDescription att{};
    att.format = swap_fmt;
    att.samples = VK_SAMPLE_COUNT_1_BIT;
    att.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
    att.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    att.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    att.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    att.initialLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    att.finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    VkAttachmentReference ref{ 0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL };
    VkSubpassDescription sub{};
    sub.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    sub.colorAttachmentCount = 1;
    sub.pColorAttachments = &ref;
    VkSubpassDependency deps[2]{};
    deps[0].srcSubpass = VK_SUBPASS_EXTERNAL; deps[0].dstSubpass = 0;
    deps[0].srcStageMask = VK_PIPELINE_STAGE_TRANSFER_BIT;
    deps[0].dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    deps[0].srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    deps[0].dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    deps[1].srcSubpass = 0; deps[1].dstSubpass = VK_SUBPASS_EXTERNAL;
    deps[1].srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    deps[1].dstStageMask = VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT;
    deps[1].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    deps[1].dstAccessMask = 0;
    VkRenderPassCreateInfo rci{};
    rci.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    rci.attachmentCount = 1; rci.pAttachments = &att;
    rci.subpassCount = 1; rci.pSubpasses = &sub;
    rci.dependencyCount = 2; rci.pDependencies = deps;
    if (vkCreateRenderPass(dev_, &rci, nullptr, &rp_) != VK_SUCCESS) return false;

    if (!create_font_atlas()) { fprintf(stderr, "studio: font atlas failed\n"); return false; }

    // descriptor: the font atlas
    VkDescriptorSetLayoutBinding bind{};
    bind.binding = 0;
    bind.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    bind.descriptorCount = 1;
    bind.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    VkDescriptorSetLayoutCreateInfo dci{};
    dci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dci.bindingCount = 1; dci.pBindings = &bind;
    if (vkCreateDescriptorSetLayout(dev_, &dci, nullptr, &dsl_) != VK_SUCCESS) return false;
    VkDescriptorPoolSize ps{ VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1 };
    VkDescriptorPoolCreateInfo pci{};
    pci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    pci.maxSets = 1; pci.poolSizeCount = 1; pci.pPoolSizes = &ps;
    if (vkCreateDescriptorPool(dev_, &pci, nullptr, &dpool_) != VK_SUCCESS) return false;
    VkDescriptorSetAllocateInfo dai{};
    dai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dai.descriptorPool = dpool_; dai.descriptorSetCount = 1; dai.pSetLayouts = &dsl_;
    if (vkAllocateDescriptorSets(dev_, &dai, &dset_) != VK_SUCCESS) return false;
    VkDescriptorImageInfo ii{ font_samp_, font_view_, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL };
    VkWriteDescriptorSet wr{};
    wr.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    wr.dstSet = dset_; wr.dstBinding = 0; wr.descriptorCount = 1;
    wr.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    wr.pImageInfo = &ii;
    vkUpdateDescriptorSets(dev_, 1, &wr, 0, nullptr);

    // pipeline
    auto vert_spv = ui_read_file("shaders/ui.vert.spv");
    auto frag_spv = ui_read_file("shaders/ui.frag.spv");
    VkShaderModule vm = ui_shader_module(dev_, vert_spv);
    VkShaderModule fm = ui_shader_module(dev_, frag_spv);
    if (vm == VK_NULL_HANDLE || fm == VK_NULL_HANDLE) {
        fprintf(stderr, "studio: ui shaders missing (shaders/ui.*.spv)\n");
        return false;
    }
    VkPipelineShaderStageCreateInfo stages[2]{};
    stages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;   stages[0].module = vm; stages[0].pName = "main";
    stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT; stages[1].module = fm; stages[1].pName = "main";

    VkVertexInputBindingDescription vbd{ 0, sizeof(Vert), VK_VERTEX_INPUT_RATE_VERTEX };
    VkVertexInputAttributeDescription vad[4]{};
    vad[0] = { 0, 0, VK_FORMAT_R32G32_SFLOAT,       0  };
    vad[1] = { 1, 0, VK_FORMAT_R32G32_SFLOAT,       8  };
    vad[2] = { 2, 0, VK_FORMAT_R32G32B32A32_SFLOAT, 16 };
    vad[3] = { 3, 0, VK_FORMAT_R32_SFLOAT,          32 };   // D3: 0 font, 1 reel thumb
    VkPipelineVertexInputStateCreateInfo vin{};
    vin.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vin.vertexBindingDescriptionCount = 1; vin.pVertexBindingDescriptions = &vbd;
    vin.vertexAttributeDescriptionCount = 4; vin.pVertexAttributeDescriptions = vad;
    VkPipelineInputAssemblyStateCreateInfo ia{};
    ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
    VkPipelineViewportStateCreateInfo vps{};
    vps.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vps.viewportCount = 1; vps.scissorCount = 1;
    VkDynamicState dyn[2] = { VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR };
    VkPipelineDynamicStateCreateInfo ds{};
    ds.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    ds.dynamicStateCount = 2; ds.pDynamicStates = dyn;
    VkPipelineRasterizationStateCreateInfo rs{};
    rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    rs.lineWidth = 1.f;
    VkPipelineMultisampleStateCreateInfo ms{};
    ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
    VkPipelineColorBlendAttachmentState cba{};
    cba.blendEnable = VK_TRUE;
    cba.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
    cba.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    cba.colorBlendOp = VK_BLEND_OP_ADD;
    cba.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
    cba.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    cba.alphaBlendOp = VK_BLEND_OP_ADD;
    cba.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                         VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
    VkPipelineColorBlendStateCreateInfo cb{};
    cb.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    cb.attachmentCount = 1; cb.pAttachments = &cba;

    VkPushConstantRange pcr{ VK_SHADER_STAGE_VERTEX_BIT, 0, 8 };
    VkPipelineLayoutCreateInfo lci{};
    lci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    lci.setLayoutCount = 1; lci.pSetLayouts = &dsl_;
    lci.pushConstantRangeCount = 1; lci.pPushConstantRanges = &pcr;
    if (vkCreatePipelineLayout(dev_, &lci, nullptr, &layout_) != VK_SUCCESS) return false;

    VkGraphicsPipelineCreateInfo gpi{};
    gpi.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gpi.stageCount = 2; gpi.pStages = stages;
    gpi.pVertexInputState = &vin;
    gpi.pInputAssemblyState = &ia;
    gpi.pViewportState = &vps;
    gpi.pDynamicState = &ds;
    gpi.pRasterizationState = &rs;
    gpi.pMultisampleState = &ms;
    gpi.pColorBlendState = &cb;
    gpi.layout = layout_;
    gpi.renderPass = rp_;
    VkResult pr = vkCreateGraphicsPipelines(dev_, VK_NULL_HANDLE, 1, &gpi, nullptr, &pipe_);
    vkDestroyShaderModule(dev_, vm, nullptr);
    vkDestroyShaderModule(dev_, fm, nullptr);
    return pr == VK_SUCCESS;
}

void StudioUI::shutdown() {
    if (dev_ == VK_NULL_HANDLE) return;
    for (VkFramebuffer fb : fbs_) vkDestroyFramebuffer(dev_, fb, nullptr);
    fbs_.clear();
    if (vbuf_ != VK_NULL_HANDLE) { vkDestroyBuffer(dev_, vbuf_, nullptr); vkFreeMemory(dev_, vmem_, nullptr); }
    if (pipe_ != VK_NULL_HANDLE) vkDestroyPipeline(dev_, pipe_, nullptr);
    if (layout_ != VK_NULL_HANDLE) vkDestroyPipelineLayout(dev_, layout_, nullptr);
    if (dpool_ != VK_NULL_HANDLE) vkDestroyDescriptorPool(dev_, dpool_, nullptr);
    if (dsl_ != VK_NULL_HANDLE) vkDestroyDescriptorSetLayout(dev_, dsl_, nullptr);
    if (font_samp_ != VK_NULL_HANDLE) vkDestroySampler(dev_, font_samp_, nullptr);
    if (font_view_ != VK_NULL_HANDLE) vkDestroyImageView(dev_, font_view_, nullptr);
    if (font_img_ != VK_NULL_HANDLE) { vkDestroyImage(dev_, font_img_, nullptr); vkFreeMemory(dev_, font_mem_, nullptr); }
    if (thumb_stage_ != VK_NULL_HANDLE) {
        vkUnmapMemory(dev_, thumb_stage_mem_);
        vkDestroyBuffer(dev_, thumb_stage_, nullptr);
        vkFreeMemory(dev_, thumb_stage_mem_, nullptr);
        thumb_stage_ = VK_NULL_HANDLE; thumb_stage_map_ = nullptr;
    }
    if (rp_ != VK_NULL_HANDLE) vkDestroyRenderPass(dev_, rp_, nullptr);
    dev_ = VK_NULL_HANDLE;
}
