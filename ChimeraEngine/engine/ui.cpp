// ui.cpp — THE ENGINE STUDIO overlay (see ui.hpp for the law this file lives under)
#include "ui.hpp"
#include <cmath>

#include <windows.h>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <unordered_map>

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

// E2: the board JSON's integer fields (row_line / spec_line — the deep links)
static int ui_json_int(const std::string& body, const char* key, size_t from, int dflt) {
    std::string needle = std::string("\"") + key + "\"";
    size_t pos = body.find(needle, from);
    if (pos == std::string::npos) return dflt;
    size_t p = pos + needle.size();
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (p >= body.size() || body[p] != ':') return dflt;
    ++p; while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    return static_cast<int>(strtol(body.c_str() + p, nullptr, 10));
}

// ── persisted Studio layout (A2) ───────────────────────────────────────────────

void StudioUI::studio_state_clamp() {
    auto clamp_panel = [](Panel& p, float extent, float scale) {
        if (extent <= 0.f || scale <= 0.f) return;
        float lo = p.min_size;
        float hi = (extent * p.max_frac) / scale;
        if (hi < lo) hi = lo;
        if (p.size < lo) p.size = lo;
        if (p.size > hi) p.size = hi;
    };
    clamp_panel(strip_, static_cast<float>(ext_.height), ui_scale_);
    clamp_panel(left_, static_cast<float>(ext_.width), ui_scale_);
    clamp_panel(right_, static_cast<float>(ext_.width), ui_scale_);
    clamp_panel(bottom_, static_cast<float>(ext_.height), ui_scale_);
    clamp_panel(reel_, static_cast<float>(ext_.height), ui_scale_);
    if (left_mode_ < 0 || left_mode_ > 6) left_mode_ = 0;
    if (docs_.current < 0 || docs_.current > 4) docs_.current = 0;
    if (docs_.scroll < 0.f) docs_.scroll = 0.f;
    // THE LIGHT: a loaded record is normalized (or restored to the historical
    // default if degenerate) — the shaders normalize too, but the stored file
    // should hold the honest unit vector.
    {
        float L = sqrtf(light_dir_[0] * light_dir_[0] + light_dir_[1] * light_dir_[1]
                      + light_dir_[2] * light_dir_[2]);
        if (L < 1e-4f) { light_dir_[0] = 0.35f; light_dir_[1] = 0.8f; light_dir_[2] = 0.45f; }
        else { light_dir_[0] /= L; light_dir_[1] /= L; light_dir_[2] /= L; }
    }
}

void StudioUI::studio_state_load() {
    std::ifstream f(studio_state_file_);
    if (!f.is_open()) return;
    // Parse each record independently. Some MSVC library versions set failbit
    // when extracting tokens such as "nan" or "inf" into a double; parsing the
    // entire file with operator>> would then silently discard every later record.
    // A malformed line is one bad record, not permission to lose the workspace.
    std::string line;
    while (std::getline(f, line)) {
        std::istringstream row(line);
        std::string key;
        double value = 0.0;
        if (!(row >> key >> value)) continue;
        if (key == "version") continue;
        if (!std::isfinite(value)) continue;
        if (key == "visible") visible = value != 0.0;
        else if (key == "bar_on") bar_on_ = value != 0.0;
        else if (key == "console_open") console_open_ = value != 0.0;
        else if (key == "left_mode") left_mode_ = static_cast<int>(value);
        else if (key == "selected_stage") selected_stage_ = static_cast<int>(value);
        else if (key == "docs_current") docs_.current = static_cast<int>(value);
        else if (key == "docs_scroll") docs_.scroll = static_cast<float>(value);
        else if (key == "strip_size") strip_.size = static_cast<float>(value);
        else if (key == "left_size") left_.size = static_cast<float>(value);
        else if (key == "right_size") right_.size = static_cast<float>(value);
        else if (key == "bottom_size") bottom_.size = static_cast<float>(value);
        else if (key == "reel_size") reel_.size = static_cast<float>(value);
        else if (key == "strip_collapsed") strip_.collapsed = value != 0.0;
        else if (key == "left_collapsed") left_.collapsed = value != 0.0;
        else if (key == "right_collapsed") right_.collapsed = value != 0.0;
        else if (key == "bottom_collapsed") bottom_.collapsed = value != 0.0;
        else if (key == "reel_collapsed") reel_.collapsed = value != 0.0;
        else if (key == "light_x") light_dir_[0] = static_cast<float>(value);
        else if (key == "light_y") light_dir_[1] = static_cast<float>(value);
        else if (key == "light_z") light_dir_[2] = static_cast<float>(value);
    }
    studio_state_clamp();
}

void StudioUI::studio_state_save() {
    std::ofstream f(studio_state_file_, std::ios::trunc);
    if (!f.is_open()) return;
    f << "version 1\n"
      << "visible " << (visible ? 1 : 0) << "\n"
      << "bar_on " << (bar_on_ ? 1 : 0) << "\n"
      << "console_open " << (console_open_ ? 1 : 0) << "\n"
      << "left_mode " << left_mode_ << "\n"
      << "selected_stage " << selected_stage_ << "\n"
      << "docs_current " << docs_.current << "\n"
      << "docs_scroll " << docs_.scroll << "\n"
      << "strip_size " << strip_.size << "\n"
      << "left_size " << left_.size << "\n"
      << "right_size " << right_.size << "\n"
      << "bottom_size " << bottom_.size << "\n"
      << "reel_size " << reel_.size << "\n"
      << "strip_collapsed " << (strip_.collapsed ? 1 : 0) << "\n"
      << "left_collapsed " << (left_.collapsed ? 1 : 0) << "\n"
      << "right_collapsed " << (right_.collapsed ? 1 : 0) << "\n"
      << "bottom_collapsed " << (bottom_.collapsed ? 1 : 0) << "\n"
      << "reel_collapsed " << (reel_.collapsed ? 1 : 0) << "\n"
      << "light_x " << light_dir_[0] << "\n"
      << "light_y " << light_dir_[1] << "\n"
      << "light_z " << light_dir_[2] << "\n";
}

std::string StudioUI::studio_state_json() const {
    std::string out = "{\"path\":\"studio_state.txt\",\"version\":1";
    out += ",\"visible\":" + std::string(visible ? "true" : "false");
    out += ",\"bar_on\":" + std::string(bar_on_ ? "true" : "false");
    out += ",\"console_open\":" + std::string(console_open_ ? "true" : "false");
    out += ",\"left_mode\":" + std::to_string(left_mode_);
    out += ",\"selected_stage\":" + std::to_string(selected_stage_);
    out += ",\"docs_current\":" + std::to_string(docs_.current);
    out += ",\"docs_scroll\":" + std::to_string(docs_.scroll);
    out += ",\"strip_size\":" + std::to_string(strip_.size);
    out += ",\"left_size\":" + std::to_string(left_.size);
    out += ",\"right_size\":" + std::to_string(right_.size);
    out += ",\"bottom_size\":" + std::to_string(bottom_.size);
    out += ",\"reel_size\":" + std::to_string(reel_.size);
    out += ",\"strip_collapsed\":" + std::string(strip_.collapsed ? "true" : "false");
    out += ",\"left_collapsed\":" + std::string(left_.collapsed ? "true" : "false");
    out += ",\"right_collapsed\":" + std::string(right_.collapsed ? "true" : "false");
    out += ",\"bottom_collapsed\":" + std::string(bottom_.collapsed ? "true" : "false");
    out += ",\"reel_collapsed\":" + std::string(reel_.collapsed ? "true" : "false");
    out += ",\"light\":[" + std::to_string(light_dir_[0]) + "," + std::to_string(light_dir_[1])
         + "," + std::to_string(light_dir_[2]) + "]}";
    return out;
}

// ── input ─────────────────────────────────────────────────────────────────────

void StudioUI::on_mouse_move(int x, int y) {
    cursor_x_ = x; cursor_y_ = y;
    // Panel sizes are stored in DESIGN units and multiplied by ui_scale_ at
    // layout time, so a drag — which arrives in SCREEN pixels — must be converted
    // at the boundary or the panel jumps by the scale factor the instant you let
    // go. Clamp in screen px (that is what max_frac is a fraction of), then
    // divide on the way in. One conversion, at the seam, so the two cannot drift.
    auto to_design = [&](float px, const Panel& p) {
        float mn = p.min_size * ui_scale_;
        float v  = (px < mn) ? mn : px;
        return v / ui_scale_;
    };
    if (drag_kind_ == 1) {          // strip bottom border: height follows the cursor
        float mx = ext_.height * strip_.max_frac;
        strip_.size = to_design(static_cast<float>(y) > mx ? mx : static_cast<float>(y), strip_);
    } else if (drag_kind_ == 2) {   // left panel right border: width follows
        float mx = ext_.width * left_.max_frac;
        left_.size = to_design(static_cast<float>(x) > mx ? mx : static_cast<float>(x), left_);
    } else if (drag_kind_ == 3) {   // right panel left border: width follows (from the right edge)
        float mx = ext_.width * right_.max_frac;
        float ns = static_cast<float>(ext_.width) - static_cast<float>(x);
        right_.size = to_design(ns > mx ? mx : ns, right_);
    } else if (drag_kind_ == 4) {   // bottom panel top border: height follows (from the bottom edge)
        float mx = ext_.height * bottom_.max_frac;
        float ns = static_cast<float>(ext_.height) - static_cast<float>(y);
        bottom_.size = to_design(ns > mx ? mx : ns, bottom_);
    } else if (drag_kind_ == 6) {   // D3: reel panel top border: height follows (above the timeline)
        float bh = bottom_.collapsed ? title_h() : bottom_.size * ui_scale_;
        float mx = ext_.height * reel_.max_frac;
        float ns = static_cast<float>(ext_.height) - bh - static_cast<float>(y);
        reel_.size = to_design(ns > mx ? mx : ns, reel_);
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
    const float th = title_h();                    // a collapsed title bar, scaled
    const float hh = static_cast<float>(h) - (bar_on_ ? bar_h() : 0.f);
    float sh = strip_.collapsed ? th : strip_.size * ui_scale_;
    if (sh > hh) sh = hh;
    float bh = bottom_.collapsed ? th : bottom_.size * ui_scale_;
    if (bh > hh - sh) bh = hh - sh;
    if (bh < th) bh = th;
    float rh = reel_.collapsed ? th : reel_.size * ui_scale_;
    if (rh > hh - sh - bh) rh = hh - sh - bh;
    if (rh < th) rh = th;
    float lw = left_.collapsed  ? th : left_.size  * ui_scale_;
    float rw = right_.collapsed ? th : right_.size * ui_scale_;
    // left/right: between strip and the status bar — the DOCKEDGE RUNS THE FULL
    // HEIGHT now. It used to stop above the reel + timeline, which left two solid
    // black rectangles in the bottom corners. The eye: "those two black blocks
    // look like a missing panel or a layout bug, not intentional whitespace. The
    // eye can't track a clean grid because the vertical boundaries disagree
    // between the upper and lower thirds." The timeline and the reel are the
    // CENTRE column's own bands (Blender/After Effects do the same: full-height
    // docks, transport in the middle), so no column boundary ever disagrees.
    R[0][0] = 0; R[0][1] = 0; R[0][2] = static_cast<float>(w); R[0][3] = sh;
    R[1][0] = 0; R[1][1] = sh; R[1][2] = lw; R[1][3] = hh - sh;
    R[2][0] = static_cast<float>(w) - rw; R[2][1] = sh; R[2][2] = rw; R[2][3] = hh - sh;
    R[3][0] = lw; R[3][1] = hh - bh; R[3][2] = static_cast<float>(w) - lw - rw; R[3][3] = bh;
    R[4][0] = lw; R[4][1] = hh - bh - rh; R[4][2] = static_cast<float>(w) - lw - rw; R[4][3] = rh;
}

bool StudioUI::hit_strip_title(int x, int y) const {
    return y >= 0 && y < 22 && x >= 0 && x < static_cast<int>(ext_.width);
}
bool StudioUI::hit_left_title(int x, int y) const {
    float sh = strip_.collapsed ? title_h() : strip_.size * ui_scale_;
    return x >= 0 && x < 22 && y >= static_cast<int>(sh);
}
bool StudioUI::hit_right_title(int x, int y) const {
    float sh = strip_.collapsed ? title_h() : strip_.size * ui_scale_;
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

// ── THE CONTEXT MENU (2026-09-03, the operator): click/drag split ────────────
// A right-press RECORDS its start and travel; it keeps the existing pan law
// untouched (drag math reads g_last_* in WndProc exactly as before). At
// release, travel under 4 px means a CLICK: open the menu at the cursor (or
// close it if it was already open — a second click anywhere dismisses).
// Items land their verb and close; a click elsewhere closes. The menu lives
// in the UI only — no engine state, no persistence, nothing to restore.
void StudioUI::ctx_measure(float& w, float& h) const {
    w = 0.f;
    for (const auto& it : ctx_items_)
        w = (std::max)(w, static_cast<float>(it.label.size()) * advance_);
    w += 24.f * ui_scale_;
    h = static_cast<float>(ctx_items_.size()) * ctx_item_h() + 8.f * ui_scale_;
}

void StudioUI::on_rbutton_down(int x, int y) {
    rdown_x_ = static_cast<float>(x); rdown_y_ = static_cast<float>(y);
    ctx_travel_ = 0.f;
}

bool StudioUI::on_rbutton_up(int x, int y) {
    if (!visible) return false;
    ctx_travel_ += fabsf(static_cast<float>(x) - rdown_x_)
                 + fabsf(static_cast<float>(y) - rdown_y_);
    if (ctx_travel_ >= 4.f * ui_scale_) {          // a DRAG: pan, never menu work
        ctx_close();
        return false;
    }
    // a CLICK
    if (ctx_open()) {
        float w, h; ctx_measure(w, h);
        bool inside = x >= ctx_x_ && x < ctx_x_ + w && y >= ctx_y_ && y < ctx_y_ + h;
        int hit = inside ? static_cast<int>((y - ctx_y_ - 4.f * ui_scale_) / ctx_item_h()) : -1;
        int verb = (inside && hit >= 0 && hit < static_cast<int>(ctx_items_.size()))
                 ? ctx_items_[hit].verb : -1;
        int target = ctx_index_;
        ctx_close();
        if (inside && verb >= 0 && target >= 0 && cb_ctx_cam_)
            cb_ctx_cam_(target, verb);             // the verb lands AFTER the close
        return true;                               // a click on the open menu is consumed
    }
    // fresh menu: only over a registered customer rect (rctx_, rebuilt in prepare())
    for (const auto& rc : rctx_) {
        if (x >= rc.x && x < rc.x + rc.w && y >= rc.y && y < rc.y + rc.h) {
            ctx_index_ = rc.target;
            ctx_items_ = rc.items;
            float w, h; ctx_measure(w, h);
            float W = static_cast<float>(ext_.width), H = static_cast<float>(ext_.height);
            ctx_x_ = (x + w > W - 4.f) ? (W - 4.f - w) : static_cast<float>(x);
            ctx_y_ = (y + h > H - bar_h() - 4.f) ? (H - bar_h() - 4.f - h) : static_cast<float>(y);
            return true;
        }
    }
    return false;                                  // plain click on nothing: pan release
}

bool StudioUI::on_lbutton(int x, int y, bool down) {
    if (!visible) return false;
    // A left press while the menu is open: click ON the menu ACTIVATES the
    // item (menus answer on press, the immediate-mode law); click OUTSIDE
    // dismisses. Either way the press is consumed — never an orbit underneath.
    if (down && ctx_open()) {
        float w, h; ctx_measure(w, h);
        bool inside = x >= ctx_x_ && x < ctx_x_ + w && y >= ctx_y_ && y < ctx_y_ + h;
        int hit = inside ? static_cast<int>((y - ctx_y_ - 4.f * ui_scale_) / ctx_item_h()) : -1;
        int verb = (inside && hit >= 0 && hit < static_cast<int>(ctx_items_.size()))
                 ? ctx_items_[hit].verb : -1;
        int target = ctx_index_;
        ctx_close();
        if (inside && verb >= 0 && target >= 0 && cb_ctx_cam_)
            cb_ctx_cam_(target, verb);
        return true;
    }
    if (!down) {
        bool had = drag_kind_ != 0;
        if (had == true && drag_kind_ >= 1 && drag_kind_ <= 8) studio_state_save();
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
    // D1: the scrub bar — press grabs the playhead (drags scrub; a click lands one).
    // A diamond hotspot consumes the press first: click a key marker, land its
    // pose; drag elsewhere on the bar to scrub.
    if (!bottom_.collapsed && clk_total_ > 0.0
        && x >= scrub_rect_[0] && x <= scrub_rect_[0] + scrub_rect_[2]
        && y >= scrub_rect_[1] - 4 && y <= scrub_rect_[1] + scrub_rect_[3] + 4) {
        for (const Hot& h : hots_) {
            if (h.id >= 700 && h.id < 800
                && x >= h.x - 4 && x < h.x + h.w + 4 && y >= h.y - 3 && y < h.y + h.h + 3) {
                if (cb_key_recall_) cb_key_recall_(h.id - 700);
                return true;
            }
        }
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
                studio_state_save();
            }
            if (h.id >= 300 && h.id < 400) {
                int i = h.id - 300;          // the workspace rows (A3); three are live so far
                if (i == 0) { left_mode_ = 0; }                          // BOARD
                if (i == 1) { left_mode_ = 4; selected_stage_ = -1; }    // SCENE (C4)
                if (i == 2) { left_mode_ = 1; selected_stage_ = -1; }    // JOINTS (C1)
                if (i == 3) { left_mode_ = 6; selected_stage_ = -1; }    // POSES (G1)
                if (i == 7) { left_mode_ = 2; selected_stage_ = -1; }    // DOCS (E1)
                if (i == 8) { left_mode_ = 3; selected_stage_ = -1; }    // LOG (F4)
                if (i == 6) { left_mode_ = 5; selected_stage_ = -1; }    // CAPTURE (D5)
            }
            if (h.id >= 400 && h.id < 500 && cb_joint_select_) cb_joint_select_(h.id - 400);
            if (h.id >= 500 && h.id < 600) docs_set(h.id - 500);         // E1: the doc picker (legacy range)
            if (h.id >= 800 && h.id < 900) docs_set(h.id - 800);         // E1: the doc picker (8 pages)
            if (h.id == 700) {                                           // LOG follow chip: re-arm + jump to the live edge
                docs_.follow_tail = true;
                docs_.scroll = docs_scroll_max_;
            }
            if (h.id == 860) {                                           // THE EYE chip: straight to the dyad's page
                docs_init();
                docs_set(docs_.log_page);
                left_mode_ = 2;
                selected_stage_ = -1;
            }
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
            if (h.id >= 700 && h.id < 800 && cb_key_recall_)             // D1: key-mark diamonds
                cb_key_recall_(h.id - 700);
            if (h.id >= 1000 && h.id < 1100 && cb_dope_key_recall_)       // D9: Dope Sheet key diamonds
                cb_dope_key_recall_(h.id - 1000);
            if (h.id >= 1100 && h.id < 1112)                                // D4: choose a reel capture
                compare_select(h.id - 1100);
            if (h.id == 1112) compare_clear();                              // D4: clear A/B compare
            if (h.id == 905 && cb_key_save_) cb_key_save_();             // D1: KEY button
            if (h.id == 906 && cb_rig_toggle_) cb_rig_toggle_();         // D8: RIG overlay toggle
            if (h.id >= 910 && h.id < 930 && cb_key_recall_)             // G1: recall pose by index
                cb_key_recall_(h.id - 910);
            if (h.id >= 930 && h.id < 940 && cb_key_delete_)             // G1: delete pose by index
                cb_key_delete_(h.id - 930);
            if (h.id == 940 && cb_key_save_) cb_key_save_();             // G1: save current pose
            if (h.id == 941 && cb_key_clear_) cb_key_clear_();           // G1: clear all poses
            if ((h.id == 900 || h.id == 901) && selected_stage_ >= 0)    // E2: the deep link
                docs_link_stage(selected_stage_);
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
    if (hit_strip_title(x, y)) { strip_.collapsed = !strip_.collapsed; studio_state_save(); return true; }
    if (hit_left_title(x, y))  { left_.collapsed  = !left_.collapsed;  studio_state_save(); return true; }
    if (hit_right_title(x, y)) { right_.collapsed = !right_.collapsed; studio_state_save(); return true; }
    if (hit_bottom_title(x, y)){ bottom_.collapsed = !bottom_.collapsed; studio_state_save(); return true; }
    if (hit_reel_title(x, y))  { reel_.collapsed  = !reel_.collapsed;  studio_state_save(); return true; }

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
    // 2026-09-02, the eye: the window booted shouting "no board file" while the
    // file sat valid next to the exe. The old gate latched last_mtime_ BEFORE
    // the parse, so one transient failure at boot locked the empty board
    // forever (mtime never changes -> never retried). Retry while unhealthy:
    // an unchanged mtime only short-circuits a board that already parsed.
    if (mt == last_mtime_ && board_.loaded) return;
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
        s.row_line  = ui_json_int(body, "row_line", pos, -1);    // E2: the deep links
        s.spec_line = ui_json_int(body, "spec_line", pos, -1);
        if (s.id.empty()) break;
        // JSON escapes newlines in the spec body; restore them for the wrap
        for (size_t p2 = s.spec.find("\\n"); p2 != std::string::npos; p2 = s.spec.find("\\n", p2))
            s.spec.replace(p2, 2, 1, '\n');
        b.stages.push_back(s);
        cur = pos + 4;
    }
    b.loaded = !b.stages.empty();
    board_ = std::move(b);
    if (board_.loaded && (selected_stage_ < -1 ||
                          selected_stage_ >= static_cast<int>(board_.stages.size()))) {
        selected_stage_ = -1;
        studio_state_save();
    }
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

// 2026-09-03, the eye (loaded review r5): docs pages rendered "JOIN _" and
// "repo_" — the atlas is ASCII (32..126) but the markdown source speaks UTF-8:
// em dashes, typographic quotes, and ellipses decoded to junk glyphs that read
// as broken underscores. The draw entry normalizes: known typographic
// characters map to their ASCII homes; any other multibyte sequence is dropped.
// The atlas stays ASCII; the text reads.
static std::string ascii_text(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (size_t i = 0; i < s.size();) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        if (c < 0x80) { out.push_back(static_cast<char>(c)); ++i; continue; }
        unsigned cp = 0; int len = 0;
        if      ((c & 0xE0) == 0xC0) { cp = c & 0x1Fu; len = 2; }
        else if ((c & 0xF0) == 0xE0) { cp = c & 0x0Fu; len = 3; }
        else if ((c & 0xF8) == 0xF0) { cp = c & 0x07u; len = 4; }
        else { ++i; continue; }                       // stray continuation byte
        if (i + static_cast<size_t>(len) > s.size()) { ++i; continue; }
        bool ok = true;
        for (int k = 1; k < len; ++k) {
            unsigned char cc = static_cast<unsigned char>(s[i + k]);
            if ((cc & 0xC0) != 0x80) { ok = false; break; }
            cp = (cp << 6) | (cc & 0x3Fu);
        }
        if (!ok) { ++i; continue; }
        i += static_cast<size_t>(len);
        switch (cp) {
            case 0x2010: case 0x2011: case 0x2012: case 0x2013: case 0x2014:
            case 0x2212: out.push_back('-');  break;      // dashes
            case 0x2018: case 0x2019: out.push_back('\''); break;
            case 0x201C: case 0x201D: out.push_back('"');  break;
            case 0x2026: out.append("...");   break;      // ellipsis
            case 0x00A0: out.push_back(' ');  break;      // nbsp
            case 0x00D7: out.push_back('x');  break;      // multiplication sign
            default: break;                               // unknown: drop
        }
    }
    return out;
}

void StudioUI::text(float x, float y, const std::string& s, float r, float g, float b, float a) {
    float pen = x;
    for (char c : ascii_text(s)) {
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

void StudioUI::compare_clear() {
    compare_a_slot_ = -1;
    compare_b_slot_ = -1;
}

void StudioUI::compare_select(int slot) {
    if (slot < 0 || slot >= REEL_MAX || !tiles_[slot].used) return;
    if (compare_a_slot_ < 0) {
        compare_a_slot_ = slot;
        compare_b_slot_ = -1;
    } else if (compare_b_slot_ < 0) {
        if (slot != compare_a_slot_) compare_b_slot_ = slot;
    } else {
        // A third choice starts a new pair; this prevents an invisible
        // selection history from becoming a second state surface.
        compare_a_slot_ = slot;
        compare_b_slot_ = -1;
    }
}

// D3: a grab lands — text into the ring, pixels into its atlas slot. Render thread.
void StudioUI::reel_push(const uint8_t* rgba, const std::string& l1,
                         const std::string& l2, const std::string& l3) {
    if (dev_ == VK_NULL_HANDLE || thumb_stage_map_ == nullptr || font_img_ == VK_NULL_HANDLE) return;
    int slot = static_cast<int>(reel_seq_ % REEL_MAX);
    if (compare_a_slot_ == slot || compare_b_slot_ == slot) compare_clear();
    tiles_[slot].used = true;
    tiles_[slot].seq = reel_seq_;
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
// Pages 5-7 are LIVE LOGS: DYAD (Saved/dyad/dyad_log.jsonl, written by the
// Python senses lane), ENGINE (the F4 session file, CWD-relative), SESSIONS
// (the cross-session recorder). The dyad path is repo-root-anchored via the
// engine module's own location — the exe's CWD is build/Release, and the
// log's home is <repo>/Saved/dyad/ no matter where the exe runs from.
static std::string ui_log_file_name() {
    // The DYAD LOG page serves the HUMAN-READABLE companion (dyad_log.txt):
    // the .jsonl is the machine record tools parse; the editor page is what
    // the operator's eyes get. The WRITER owns the formatting (dyad_log.py
    // mirrors every append into the .txt) — the engine stays a verbatim
    // file browser and renders no JSON artifacts it does not understand.
    char mod[MAX_PATH];
    DWORD n = GetModuleFileNameA(nullptr, mod, MAX_PATH);   // <...>/build/Release/chimera_engine.exe
    if (n == 0 || n >= MAX_PATH) return "Saved/dyad/dyad_log.txt";
    std::string exe(mod, n);
    for (int i = 0; i < 5; ++i) {   // exe -> Release -> build -> engine -> ChimeraEngine -> REPO ROOT
        size_t s = exe.find_last_of("/\\");
        if (s == std::string::npos) break;
        exe.resize(s);
    }
    return exe + "/Saved/dyad/dyad_log.txt";
}
static constexpr int DYAD_LOG_PAGE = 5;

void StudioUI::docs_init() {
    if (!docs_.paths.empty()) return;
    // The menu (docs/THE_ENGINE_STUDIO.md, E1) names the five. The exe's CWD
    // is build/Release — the repo root is four levels up.
    const char* base = "../../../../docs/";
    // Pages 0-4: the workflow docs the board names. Pages 5-7: THE LIVE LOGS
    // (operator decree 2026-09-03: "two logs ... both available in the editor,
    // especially the dyad log"). All are plain text files the poll loop
    // re-reads when their mtime moves. DYAD is repo-root-anchored (written by
    // the Python senses lane, outside the exe's CWD); ENGINE is the F4 session
    // file (CWD-relative; the member is set by the engine before first draw);
    // SESSIONS is the cross-session boot record (CWD-relative).
    docs_.paths = {
        std::string(base) + "THE_BODY_PIPELINE.md",
        std::string(base) + "THE_ARTISTS_SOLID.md",
        std::string(base) + "THE_MASTER_LIST.md",
        std::string(base) + "THE_TRIANGLE_GUIDE.md",
        std::string(base) + "THE_OPERATING_MANUAL.md",
        ui_log_file_name(),                            // page 5: DYAD LOG (the eye's reports)
        log_file_,                                     // page 6: ENGINE LOG (F4's session file)
        "sessions.jsonl",                              // page 7: SESSIONS (boot/exit record)
    };
    docs_.log_page = DYAD_LOG_PAGE;
    docs_.sessions_page = static_cast<int>(docs_.paths.size()) - 1;
    if (docs_.current > static_cast<int>(docs_.paths.size()) - 1) docs_.current = 0;
    if (docs_.current == DYAD_LOG_PAGE + 1 && log_file_.empty()) docs_.current = DYAD_LOG_PAGE;
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
    // The LIVE LOG pages re-read at 4 Hz (250 ms) — the docs docs poll at 1 Hz;
    // a tail the operator watches must move at the pace the eye expects. The
    // mtime guard below still does the real work: no change, no re-read.
    bool is_log = docs_.current == docs_.log_page || docs_.current == docs_.sessions_page
               || docs_.current == docs_.log_page + 1;
    float period = is_log ? 0.25f : 1.0f;
    if (std::chrono::duration<float>(now - docs_.last_poll).count() < period) return;
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
    docs_.display_src.clear();
    // The same greedy law as text_wrap — the browser and the renderer can
    // never disagree about where a line breaks
    int src = 0;
    for (const std::string& line : docs_.lines) {
        std::string para = line;
        if (para.empty()) { docs_.display.emplace_back(); docs_.display_src.push_back(src); ++src; continue; }
        while (!para.empty()) {
            if (para.size() <= maxc) { docs_.display.push_back(para); docs_.display_src.push_back(src); break; }
            size_t cut = para.rfind(' ', maxc);
            if (cut == std::string::npos || cut == 0) cut = maxc;
            docs_.display.push_back(para.substr(0, cut));
            docs_.display_src.push_back(src);
            para = para.substr(cut + (cut < para.size() && para[cut] == ' ' ? 1 : 0));
        }
        ++src;
    }
    docs_clamp_scroll();
}

void StudioUI::docs_clamp_scroll() {
    if (docs_.scroll < 0.f) docs_.scroll = 0.f;
    // A zero maximum is also the pre-measurement value during initialization.
    // prepare() applies the zero-range clamp after it has measured the display.
    if (docs_scroll_max_ > 0.f && docs_.scroll > docs_scroll_max_)
        docs_.scroll = docs_scroll_max_;
}

void StudioUI::docs_set(int idx) {
    docs_init();
    if (idx < 0 || idx >= static_cast<int>(docs_.paths.size())) return;
    docs_.current = idx;
    docs_.scroll = 0.f;
    docs_.follow_tail = true;              // opening a log lands on its newest line
    docs_.mtime = 0;                       // force a reload on the next poll
    docs_.last_poll = std::chrono::steady_clock::time_point{};
    docs_poll();
    studio_state_save();
}

void StudioUI::docs_set_scroll(float s) {
    docs_.scroll = s;
    // THE TAIL LAW, one site: pinned at the bottom (or beyond), detached anywhere
    // below it. The HTTP twin obeys the same contract as the wheel — an agent's
    // scroll behaves like a human's, and a log the reader left is a log that
    // stays put while new lines land.
    docs_.follow_tail = (docs_.scroll >= docs_scroll_max_ - 0.5f);
    docs_clamp_scroll();
    studio_state_save();
}

// ── E2: DEEP LINKS ────────────────────────────────────────────────────────────
int StudioUI::docs_link_line(int stage_index) const {
    if (stage_index < 0 || stage_index >= static_cast<int>(board_.stages.size()))
        return -1;
    const StudioStage& st = board_.stages[stage_index];
    // the membrane section when the doc has one; the falsifier's other home
    // (the glance-table row) otherwise. Both derived by studio_board.py.
    return st.spec_line >= 0 ? st.spec_line : st.row_line;
}

void StudioUI::docs_link_stage(int stage_index) {
    int line = docs_link_line(stage_index);
    if (line < 0) return;
    left_mode_ = 2;                 // the DOCS workspace
    selected_stage_ = -1;           // the way back is the strip node (the workspace law)
    docs_set(0);                    // THE_BODY_PIPELINE.md — the board's own source
    docs_.pending_line = line;      // resolved in prepare() through the live wrap map
    studio_state_save();
}

int StudioUI::docs_top_src() const {
    if (docs_.display_src.empty()) return -1;
    int top = static_cast<int>(docs_.scroll);
    if (top < 0) top = 0;
    if (top >= static_cast<int>(docs_.display_src.size()))
        top = static_cast<int>(docs_.display_src.size()) - 1;
    return docs_.display_src[top];
}

bool StudioUI::on_wheel(int x, int y, float delta) {
    if (!visible || left_mode_ != 2 || left_.collapsed) return false;
    float R[5][4]; layout(ext_.width, ext_.height, R);
    if (x < R[1][0] || x >= R[1][0] + R[1][2] || y < R[1][1] || y >= R[1][1] + R[1][3])
        return false;
    docs_.scroll -= delta * 3.0f;          // one notch = 3 lines (the platform convention)
    // TAIL-FOLLOW: one notch UP detaches the view from the live edge (the
    // human is reading history); reaching the bottom re-arms it.
    if (delta > 0.f) docs_.follow_tail = false;
    if (docs_.scroll >= docs_scroll_max_ - 0.5f) docs_.follow_tail = true;
    docs_clamp_scroll();
    studio_state_save();
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

    // (The scale is derived once in init() — see the note there. Nothing here
    // rebuilds the font atlas at runtime: the descriptor is written once.)
    poll_board();
    docs_poll();    // E1: unconditional — the HTTP twin stays live in any dock mode
    verts_.clear();
    verts_.reserve(8192);
    hots_.clear();
    hud_rows_.clear();
    // F2/F3: the chrome draws whether the overlay is open or not. With the
    // overlay closed it is the ONLY thing drawn — "always visible" is literal.
    if (!visible) {
        marker_hover_ = false;
        marker_hover_label_.clear();
        build_chrome(); build_console(); return;
    }

    float R[5][4]; layout(win_w, win_h, R);
    const float lh = cell_h_;                       // one text line
    const float TR = 0.86f, TG = 0.88f, TB = 0.92f; // text color

    // ── the stage strip (B1: the pipeline map; B2: the standing rule, displayed) ──
    rect(R[0][0], R[0][1], R[0][2], R[0][3], 0.07f, 0.08f, 0.11f, 0.97f);   // near-opaque: the scene must not leak under the chrome (the eye, defect a)
    rect(R[0][0], R[0][1], R[0][2], 22, 0.13f, 0.14f, 0.19f, 0.95f);
    // 2026-09-02, the eye (defect e): this row read as permanent help clutter.
    // It IS the tooltip zone — a title belongs in the corner, context help in
    // the margin the cursor already occupies.
    // 2026-09-03, the eye (defect 3, standing since the first review): the title
    // line and the stage row ran edge to edge — "cramped and unframed". The
    // inset matches the strip's own vertical inset (30) — one number, uniform
    // breathing border, nothing invented.
    text(30, (22 - lh) * 0.5f, "THE ENGINE STUDIO",
         0.55f, 0.58f, 0.65f, 1.f);
    {
        // context help lives at the cursor's end of the bar, dim, right-aligned
        const char* help = "[F1] hide   [click bar] collapse   [drag edge] resize   [`] console";
        float hw = static_cast<float>(strlen(help)) * advance_;
        text(static_cast<float>(ext_.width) - hw - 30.f, (22 - lh) * 0.5f, help, 0.42f, 0.45f, 0.52f, 1.f);
    }
    if (!strip_.collapsed) {
        float y0 = 30.f;
        float node_h = strip_.size - 30.f - lh - 12.f;
        if (node_h < 14.f) node_h = 14.f;
        if (!board_.loaded) {
            text(30, y0 + 6, "no board file - run: python tools/studio_board.py  (the repo's gate truth, read never owned)",
                 0.85f, 0.55f, 0.30f, 1.f);
        } else {
            size_t n = board_.stages.size();
            float pad = 30.f, gap = 6.f;
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
                // THE OPERATOR'S DECREE (2026-09-03): the NAME is the stage's face —
                // the code ("B3") is plumbing for tools and links, not for eyes.
                // Name on top in FULL brightness; the code demoted to a dim suffix.
                {
                    std::string nm = s.name.size() * advance_ > bw - 4
                                   ? s.name.substr(0, static_cast<size_t>((bw - 4) / advance_)) : s.name;
                    float nw = nm.size() * advance_;
                    text(x + (bw - nw) * 0.5f, y0 + 4, nm, TR, TG, TB, 1.f);
                }
                if (node_h > 2 * lh + 8) {
                    std::string cd = s.id;
                    float cw2 = cd.size() * advance_;
                    text(x + (bw - cw2) * 0.5f, y0 + 6 + lh, cd, TR, TG, TB, 0.45f);
                } else {
                    std::string cd = " " + s.id;
                    text(x + 4, y0 + 4, cd, TR, TG, TB, 0.45f);
                }
                if (node_h > 3 * lh + 10) {
                    std::string st = s.status;
                    float sw = st.size() * advance_;
                    text(x + (bw - sw) * 0.5f, y0 + 8 + 2 * lh, st, cr, cg, cb, 1.f);
                }
            }
            // B2: the standing rule, displayed - computed by the tool, never edited here.
            // 2026-09-02, the knowledge-armed eye (C5): this line wore warning amber, the
            // color of "something broke", for what is a POINTER to the next stage. It now
            // wears the same accent blue as the bottom bar's stage pointer -- amber stays
            // reserved for genuine failures ("no board file" above keeps it).
            float sy = y0 + node_h + 4;
            text(8, sy, board_.standing, 0.30f, 0.60f, 1.00f, 1.f);
            std::string src = "docs/THE_BODY_PIPELINE.md " + board_.updated;
            text(static_cast<float>(win_w) - src.size() * advance_ - 8, sy, src, 0.45f, 0.47f, 0.52f, 1.f);
        }
    }

    // ── the STUDIO panel (left): the menu + the join's provenance — or, when a
    // strip node is selected (B3), the stage's task envelope, VERBATIM ──
    rect(R[1][0], R[1][1], R[1][2], R[1][3], 0.10f, 0.11f, 0.15f, 0.97f);   // 0.97: at 0.92 the grid bled through as "underline artifacts" under STATUS rows (the eye, twice)
    rect(R[1][0], R[1][1], R[1][2], 22, 0.17f, 0.18f, 0.25f, 0.97f);        // header band raised with the fill
    rect_outline(R[1][0], R[1][1], R[1][2], R[1][3], 1.f, 0.30f, 0.60f, 1.00f, 0.55f); // the container line: a panel is a thing on screen, not a rumor
    const bool have_sel = selected_stage_ >= 0
                       && selected_stage_ < static_cast<int>(board_.stages.size());
    text(R[1][0] + 8, R[1][1] + (22 - lh) * 0.5f,
         left_.collapsed ? "+" : (left_mode_ == 1 ? "JOINTS - the editor (C1)"
            : (left_mode_ == 2 ? "DOCS - the browser (E1)"
            : (left_mode_ == 3 ? "LOG - the recorder (F4)"
            : (left_mode_ == 4 ? "SCENE - the outliner (C4)"
            : (left_mode_ == 5 ? "CAPTURE - render-to-MP4 (D5)"
            : (left_mode_ == 6 ? "POSES - the library (G1)"
            : (have_sel ? board_.stages[selected_stage_].id + " - " + board_.stages[selected_stage_].name : "STUDIO"))))))),
         TR, TG, TB, 1.f);        if (left_mode_ != 1) slider_tracks_.clear();   // stale hit-rects are a lie

    if (left_mode_ != 4) { scene_row_rects_.clear(); scene_sel_rects_.clear(); } // same law
    if (!(left_mode_ == 0 && have_sel)) link_hot_[2] = 0.f;   // E2: same law — no envelope, no link rect
    if (!left_.collapsed && left_mode_ == 2) {
        // E1: THE DOCS BROWSER. The five docs the menu names, verbatim (the
        // panel's FNV hash is served over HTTP — a rendered line that is not
        // the file's line is a bug by definition). Read-only by architecture.
        docs_init();
        float x = R[1][0] + 10, y = R[1][1] + 30;
        float y_max = R[1][1] + R[1][3] - lh;
        for (size_t i = 0; i < docs_.paths.size(); ++i) {
            std::string nm;
            if (static_cast<int>(i) == docs_.log_page)           nm = "DYAD LOG - the eye's reports";
            else if (static_cast<int>(i) == docs_.log_page + 1)  nm = "ENGINE LOG - this session";
            else if (static_cast<int>(i) == docs_.sessions_page) nm = "SESSIONS - boot/exit record";
            else {
                nm = docs_.paths[i];
                nm = nm.substr(nm.find_last_of('/') + 1);
                if (nm.size() > 3) nm = nm.substr(0, nm.size() - 3);   // strip .md
            }
            bool cur = static_cast<int>(i) == docs_.current;
            if (cur) {
                rect(R[1][0] + 2, y - 2, R[1][2] - 4, lh + 4, 0.13f, 0.16f, 0.24f, 0.95f);
                rect(R[1][0] + 2, y - 2, 4, lh + 4, 0.30f, 0.60f, 1.00f, 0.95f);   // the selection accent: readable at a glance
            }
            text(x, y, nm, cur ? 0.55f : 0.42f, cur ? 0.85f : 0.44f, cur ? 1.00f : 0.50f, 1.f);
            hots_.push_back({ x - 2, y - 2, R[1][2] - 20, lh + 4, 800 + static_cast<int>(i) });
            y += lh + 2;
        }
        bool cur_is_log = docs_.current == docs_.log_page || docs_.current == docs_.log_page + 1
                       || docs_.current == docs_.sessions_page;
        if (cur_is_log) {
            // THE DIVIDER: a styled band behind the section line — the same
            // treatment as the dock's top bar, so the log section reads as its
            // own block (the eye: "plain inline text ... feels light").
            rect(R[1][0] + 2, y - 3, R[1][2] - 4, lh + 5, 0.17f, 0.18f, 0.25f, 0.95f);
            y += lh + 5;
        }
        char ib[192];
        if (cur_is_log) {
            // The live pages name what they count: the dyad log is REPORTS (the
            // eye's verdicts), the engine log is EVENTS, sessions is BOOTS.
            snprintf(ib, sizeof(ib), "%s  |  %zu lines  |  re-read on file change",
                     docs_.current == docs_.log_page ? "the dyad's written record"
                     : docs_.current == docs_.sessions_page ? "one line per boot/exit"
                     : "the recorder's stream",
                     docs_.lines.size());
        } else {
            snprintf(ib, sizeof(ib), "%zu lines  |  read-only  |  re-read on file change (1 Hz)",
                     docs_.lines.size());
        }
        text(x, y, ib, 0.45f, 0.47f, 0.52f, 1.f); y += lh + 4;
        if (cur_is_log) {
            // The FOLLOW chip: LIVE sticks to the newest line; PAUSED means the
            // human scrolled up to read history - click re-arms and jumps down.
            bool live = docs_.follow_tail;
            // A BUTTON, unambiguously: filled hit-area, state dot, and the label
            // names the ACTION a click performs (the eye: "reads like a status
            // badge ... nothing signals click me to pause").
            float cw = 8 * advance_ + 30;
            rect(R[1][0] + 10, y - 2, cw, lh + 2,
                 live ? 0.13f : 0.24f, live ? 0.40f : 0.22f, live ? 0.22f : 0.13f, 0.98f);
            rect_outline(R[1][0] + 10, y - 2, cw, lh + 2, 1.f,
                         live ? 0.35f : 0.80f, live ? 0.75f : 0.62f, live ? 0.55f : 0.30f, 0.90f);
            // icon glyphs drawn as TEXT so the atlas carries them: pause = two
            // bars, resume = a triangle — the icon must agree with the label
            // (the eye: "a solid square reads as stop, not pause").
            text(R[1][0] + 15, y, live ? "||" : ">",
                 live ? 0.50f : 1.00f, live ? 1.00f : 0.85f, live ? 0.55f : 0.40f, 1.f);
            text(R[1][0] + 45, y, live ? "PAUSE" : "RESUME",
                 live ? 0.80f : 1.00f, live ? 1.00f : 0.80f, live ? 0.85f : 0.50f, 1.f);
            hots_.push_back({ R[1][0] + 10, y - 2, cw, lh + 2, 700 });
            text(R[1][0] + 10 + cw + 10, y,
                 live ? "tail-following the newest line (scroll up to read history)"
                      : "reading history - RESUME or scroll to bottom for the live edge",
                 0.45f, 0.47f, 0.52f, 1.f);
            y += lh + 4;
        }
        // the text, wrapped to the CURRENT dock width (narrow the dock and the
        // wrap follows next frame — the wrap is derived, never stored stale).
        // 34px total inset: lines must not kiss the dock's right edge (the eye
        // called the padding "tight" — longer tokens were one glyph from clipping).
        size_t maxc = static_cast<size_t>((R[1][2] - 20 - 14 - 16) / advance_);
        docs_rewrap(maxc);
        float text_top = y;
        int visible_n = static_cast<int>((y_max - text_top) / lh) + 1;
        if (visible_n < 1) visible_n = 1;
        docs_scroll_max_ = docs_.display.size() > static_cast<size_t>(visible_n)
            ? static_cast<float>(docs_.display.size() - visible_n) : 0.f;
        // E2: a deep link lands HERE — after the rewrap (the wrap map is fresh)
        // and with scroll_max known, so the clamp is the same law a human's
        // scroll obeys. The target source line's FIRST display line goes top.
        if (docs_.pending_line >= 0) {
            int tgt = docs_.pending_line;
            docs_.pending_line = -1;
            for (size_t i = 0; i < docs_.display_src.size(); ++i) {
                if (docs_.display_src[i] == tgt) { docs_.scroll = static_cast<float>(i); break; }
            }
            docs_.follow_tail = (docs_.scroll >= docs_scroll_max_ - 0.5f);   // a deep link is a read-history act
        }
        if (docs_scroll_max_ <= 0.f) docs_.scroll = 0.f;
        else docs_clamp_scroll();
        if (docs_.follow_tail) docs_.scroll = docs_scroll_max_;   // LOG pages: the live edge owns the view
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
    } else if (!left_.collapsed && left_mode_ == 6) {
        // G1: THE POSES LIBRARY. Every saved key mark as a row: name, time,
        // and delete button. Click a name -> recall (scrub to that time).
        // The engine pushes key_marks_ui_ every frame; the panel only draws.
        float x = R[1][0] + 10, y = R[1][1] + 30;
        float y_max = R[1][1] + R[1][3] - lh;
        float dock_w = R[1][2] - 20;
        const float name_w = 14 * advance_;
        const float time_w = 7 * advance_;
        const float del_w = 3 * advance_;
        char hb[128];
        snprintf(hb, sizeof(hb), "saved poses: %zu", key_marks_ui_.size());
        text(x, y, hb, 0.62f, 0.66f, 0.74f, 1.f); y += lh;
        text(x, y, "click name = recall   click x = delete", 0.45f, 0.47f, 0.52f, 1.f); y += lh + 4;
        if (key_marks_ui_.empty()) {
            text(x, y, "no poses saved yet", 0.45f, 0.47f, 0.52f, 1.f); y += lh;
            text(x, y, "press KEY or POST /keys {\"action\":\"save\"}", 0.45f, 0.47f, 0.52f, 1.f); y += lh;
        } else {
            for (size_t i = 0; i < key_marks_ui_.size(); ++i) {
                if (y > y_max) {
                    text(x, y_max, "... (clipped)", 0.85f, 0.55f, 0.30f, 1.f);
                    break;
                }
                const auto& kp = key_marks_ui_[i];
                const std::string& nm = kp.first;
                double kt = kp.second;
                // highlight if this is the current pose (scrub matches)
                double cur_t = clk_t_;
                double period = clk_hinge_period_ > 0.0 ? clk_hinge_period_ : clk_total_ > 0.0 ? clk_total_ : 4.0;
                double local_cur = cur_t - floor(cur_t / period) * period;
                double local_key = kt - floor(kt / period) * period;
                bool current = std::abs(local_cur - local_key) < 0.05 || std::abs(local_cur - local_key + period) < 0.05 || std::abs(local_cur - local_key - period) < 0.05;
                // row background for current pose
                if (current) rect(R[1][0] + 2, y - 2, R[1][2] - 4, lh + 4, 0.13f, 0.16f, 0.24f, 0.95f);
                // name (clickable -> recall)
                text(x, y, nm, current ? 0.45f : TR, current ? 0.75f : TG, current ? 1.00f : TB, 1.f);
                hots_.push_back({ x - 2, y - 2, name_w + 6, lh + 4, 910 + static_cast<int>(i) });
                // time value
                char tb[32]; snprintf(tb, sizeof(tb), "t=%.2f", kt);
                text(x + name_w + 6, y, tb, 0.62f, 0.66f, 0.74f, 1.f);
                // delete button (x)
                float dx = x + name_w + 6 + time_w;
                text(dx, y, "x", 0.85f, 0.35f, 0.30f, 1.f);
                hots_.push_back({ dx - 2, y - 2, del_w + 4, lh + 4, 930 + static_cast<int>(i) });
                y += lh + 2;
            }
        }
        // action buttons at the bottom
        if (y + lh * 2 < y_max) {
            y += 4;
            text(x, y, "[SAVE current]", 0.30f, 0.75f, 0.45f, 1.f);
            hots_.push_back({ x - 2, y - 2, 16 * advance_, lh + 4, 940 });
            y += lh;
            if (!key_marks_ui_.empty()) {
                text(x, y, "[CLEAR all]", 0.85f, 0.45f, 0.30f, 1.f);
                hots_.push_back({ x - 2, y - 2, 14 * advance_, lh + 4, 941 });
            }
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
            std::string rig_label = rig_overlay_ui_ ? "[RIG ON]  FK chain overlay" : "[RIG OFF] FK chain overlay";
            text(x, y, rig_label, rig_overlay_ui_ ? 0.30f : 0.62f,
                 rig_overlay_ui_ ? 0.75f : 0.40f, rig_overlay_ui_ ? 1.00f : 0.42f, 1.f);
            hots_.push_back({ x - 2, y - 2, 22 * advance_, lh + 4, 906 });
            y += lh + 4;
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
        {
            // E2: the falsifier row IS the deep link — click it and the DOCS
            // dock opens at the membrane section that named it (the same jump
            // POST /link {"stage":...} makes; one resolution law for both).
            float y0 = y;
            row("FALSIFIER (named before the run):", st.falsifier, 1.0f, 0.85f, 0.40f);
            if (docs_link_line(selected_stage_) >= 0 && y0 <= y_max) {
                hots_.push_back({ x - 4, y0 - 2, R[1][2] - 30, y - y0 + 2, 900 });
                link_hot_[0] = x - 4; link_hot_[1] = y0 - 2;
                link_hot_[2] = R[1][2] - 30; link_hot_[3] = y - y0 + 2;
                text(R[1][0] + R[1][2] - 12 - 9 * advance_, y0, "[docs ->]",
                     0.30f, 0.60f, 1.00f, 1.f);
            }
        }
        row("VERDICT (the doc's own row):", st.cell, cr, cg, cb);
        row("REFEREE TOOL:", st.tool, TR, TG, TB);
        row("ARTIFACT:", st.artifact, 0.55f, 0.85f, 0.55f);
        if (!st.spec.empty()) {
            float y0 = y;
            if (y <= y_max) {
                text(x, y, "NEXT ACTION (the envelope):", 0.62f, 0.66f, 0.74f, 1.f);
                if (docs_link_line(selected_stage_) >= 0)   // E2: the spec's own section
                    text(R[1][0] + R[1][2] - 12 - 9 * advance_, y, "[docs ->]",
                         0.30f, 0.60f, 1.00f, 1.f);
                y += lh;
            }
            float y_end = text_wrap(x + 8, y, st.spec, maxc - 2, TR, TG, TB, 0.95f, y_max);
            if (docs_link_line(selected_stage_) >= 0 && y0 <= y_max)
                hots_.push_back({ x - 4, y0 - 2, R[1][2] - 30,
                                  (y_end < y_max ? y_end : y_max + lh) - y0 + 2, 901 });
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
        // THE DOCK IS A BOUNDARY (2026-08-31, found by the eye on the glass at 2K:
        // "the JOIN of engine state + repo truth" ran ~70px past this dock's right
        // edge and under the [1 alpha] chip in the centre column). The selected-node
        // path above already wraps to maxc; the default view never did, so a long line
        // bled into the viewport. Same law as the STATUS panel: fits or degrades --
        // here it wraps, and the dock's width picks the columns (arithmetic, not taste).
        size_t maxc = static_cast<size_t>((R[1][2] - 20) / advance_);
        float y_max = R[1][1] + R[1][3] - lh;
        auto line = [&](const char* s, float r, float g, float b) {
            if (y > y_max) return;
            y = text_wrap(x, y, s, maxc, r, g, b, 1.f, y_max);   // returns the next free line
        };
        line("the JOIN of engine state + repo truth", 0.55f, 0.58f, 0.65f); y += 6;
        if (board_.loaded) line("board: live (studio_board.json)", 0.25f, 0.75f, 0.35f);
        else               line("board: no file yet",            0.85f, 0.55f, 0.30f);
        line("feed: tools/studio_board.py", 0.45f, 0.47f, 0.52f); y += 8;
        line("workspaces (A3 - click to switch):", 0.62f, 0.66f, 0.74f); y += 2;
        const char* ws[] = {"BOARD   (this strip)", "SCENE   - the outliner (C4)", "JOINTS  - the editor (C1)", "POSES   - the library (G1)",
                            "WATER   - parked", "FROST   - parked", "CAPTURE - render-to-MP4 (D5)", "DOCS    - the browser (E1)",
                            "LOG     - the recorder (F4)"};
        for (int i = 0; i < 9; ++i) {
            bool live = (i == 0 || i == 1 || i == 2 || i == 3 || i == 6 || i == 7 || i == 8);
            text(x + 8, y, ws[i], live ? 0.30f : 0.42f, live ? 0.60f : 0.44f, live ? 1.00f : 0.50f, 1.f);
            if (live) hots_.push_back({ x + 4, y - 2, R[1][2] - 30, lh + 4, 300 + i });
            y += lh;
        }
        y += 6;
        line("click a stage node above -> its envelope (B3)", 0.30f, 0.60f, 1.00f);
        line("next per the menu: C2 inspector, D5 render-to-MP4, D6 bookmarks", 0.45f, 0.47f, 0.52f);
        line("(docs/THE_ENGINE_STUDIO.md)", 0.45f, 0.47f, 0.52f);
    }

    // ── the STATUS panel (right): the engine's own live rows, honest — or,
    // when an outliner row is selected, the INSPECTOR (C2): the atom's full
    // state document, engine-composed. The FPS pulse stays on top either way.
    rect(R[2][0], R[2][1], R[2][2], R[2][3], 0.10f, 0.11f, 0.15f, 0.97f);   // same law: no bleed-through underlines
    rect(R[2][0], R[2][1], R[2][2], 22, 0.17f, 0.18f, 0.25f, 0.97f);
    rect_outline(R[2][0], R[2][1], R[2][2], R[2][3], 1.f, 0.30f, 0.60f, 1.00f, 0.55f);
    {
        std::string rtitle = inspect_row_ >= 0
            ? "INSPECT - " + inspect_label_ + " (C2)" : "STATUS (live)";
        text(R[2][0] + 8, R[2][1] + (22 - lh) * 0.5f,
             right_.collapsed ? "+" : rtitle, TR, TG, TB, 1.f);
    }
    if (!right_.collapsed) {
        float x = R[2][0] + 10, y = R[2][1] + 30;
        float y_max = R[2][1] + R[2][3] - lh;
        // THE FPS PULSE FITS THE PANEL, OR IT DEGRADES (2026-08-31, found by the
        // eye on the glass at 2K: "the green FPS line runs into the panel's right
        // edge with no trailing space and its value is truncated at the border").
        // It is arithmetic, not taste: the full string is 36 chars at 9px advance
        // = 324px, and the right dock is 330px wide — it cannot fit its own
        // padding. THE PANEL'S WIDTH PICKS THE FORMAT, in tiers, so a number is
        // never silently cut in half mid-digit (a truncated "9" reads as "9" and
        // as "95" depending on where the border falls — a lie either way).
        float avail = R[2][2] - 20.f;                       // the panel's own padding
        int   maxch = (int)(avail / (advance_ > 0.f ? advance_ : 8.f));
        char buf[128];
        snprintf(buf, sizeof(buf), "FPS %.0f | ft avg %.2f ms | max %.2f ms", fps_, ft_avg_, ft_max_);
        if ((int)strlen(buf) > maxch)
            snprintf(buf, sizeof(buf), "FPS %.0f | ft %.2f ms | max %.2f", fps_, ft_avg_, ft_max_);
        if ((int)strlen(buf) > maxch)
            snprintf(buf, sizeof(buf), "FPS %.0f | ft %.1f ms", fps_, ft_avg_);
        if ((int)strlen(buf) > maxch)
            snprintf(buf, sizeof(buf), "FPS %.0f", fps_);
        text(x, y, buf, 0.55f, 0.85f, 0.55f, 1.f); y += lh + 6;
        if (inspect_row_ >= 0) {
            // C2: every line is the engine's document for the selected atom —
            // key dim, value bright; the panel invents nothing.
            for (const auto& kv : inspect_kv_) {
                if (y > y_max) break;
                text(x, y, kv.first, 0.62f, 0.66f, 0.74f, 1.f);
                // The value fits the columns right of the key tab, or it wraps —
                // a long value must not run under the viewport edge.
                const size_t val_maxc = maxch > 17 ? static_cast<size_t>(maxch) - 17 : 8;
                y = text_wrap(x + 16 * advance_, y, kv.second, val_maxc, TR, TG, TB, 1.f, y_max);
                y += 1;
            }
            if (!inspect_hint_.empty() && y <= y_max) {
                y += 4;
                text(x, y, inspect_hint_, 0.45f, 0.47f, 0.52f, 1.f); y += lh;
            }
            if (y <= y_max)
                text(x, y, "[click the row again to close]", 0.45f, 0.47f, 0.52f, 1.f);
        } else {
            // The STATUS rows fit the panel or they wrap — same law as the left
            // dock's default view (found by the eye: a long status line bled under
            // the viewport). The panel's width picks the columns, arithmetic not
            // taste; text_wrap yields at y_max like every other consumer.
            const size_t status_maxc = static_cast<size_t>(avail / (advance_ > 0.f ? advance_ : 8.f));
            for (const std::string& line : status_lines_) {
                if (y > y_max) break;
                y = text_wrap(x, y, line, status_maxc, TR, TG, TB, 0.95f, y_max);
                y += 2;
            }
            // 2026-09-03, the eye (loaded review): with no atom selected this dock
            // drew its 7 status rows and left ~77% of itself empty — the dyad read
            // the voids under the side panels as dead space ("half of both side
            // panels are dead black space"). The engine already composes the live
            // scene rows every frame (the /scene twin's own source), so the STATUS
            // view shows them: an honest readout covers the dock, the panel
            // invents nothing. VIEW ONLY — toggles stay in SCENE mode (left dock).
            if (y <= y_max && !scene_.empty()) {
                y += 6;
                // header fits the dock or it lies clipped (the eye, r6): the dock
                // is ~34 columns; the header must be shorter before it draws.
                text(x, y, "SCENE - live systems (view only)", 0.45f, 0.47f, 0.52f, 1.f);
                y += lh + 2;
                for (const auto& r : scene_) {
                    if (y > y_max) break;
                    // state chip: on = green, off = dim grey, read-only row = blue
                    float cr = 0.55f, cg = 0.85f, cb = 0.55f;
                    if (r.toggleable && r.state == 0) { cr = cg = cb = 0.45f; }
                    else if (!r.toggleable)           { cr = 0.55f; cg = 0.70f; cb = 0.95f; }
                    rect(x, y + lh * 0.30f, 5, 5, cr, cg, cb, 1.f);
                    const size_t row_maxc = status_maxc > 2 ? status_maxc - 2 : 8;
                    y = text_wrap(x + 12, y, r.label + "  " + r.detail, row_maxc,
                                  TR, TG, TB, 0.92f, y_max);
                    y += 1;
                }
            }
        }
    }

    // ── the REEL (D3: every /frame grab lands here — the evidence tray, on-screen) ──
    rect(R[4][0], R[4][1], R[4][2], R[4][3], 0.07f, 0.08f, 0.11f, 0.97f);   // near-opaque (defect a)
    rect(R[4][0], R[4][1], R[4][2], 22, 0.13f, 0.14f, 0.19f, 0.95f);
    {
        char rb[64];
        snprintf(rb, sizeof(rb), "REEL (D3) - every /frame grab lands here  [%d/%d]", reel_count_, REEL_MAX);
        text(R[4][0] + 8, R[4][1] + (22 - lh) * 0.5f, reel_.collapsed ? "+" : rb, 0.62f, 0.66f, 0.74f, 1.f);
        rect_outline(R[4][0], R[4][1], R[4][2], R[4][3], 1.f, 0.30f, 0.60f, 1.00f, 0.55f);   // the container line, same law as the docks
        if (!reel_.collapsed && compare_a_slot_ >= 0 && compare_b_slot_ >= 0) {
            const char* cmp = " A/B ACTIVE ";
            float cw = static_cast<float>(strlen(cmp)) * advance_ + 8.f;
            float cx = R[4][0] + R[4][2] - cw - 8.f;
            rect(cx, R[4][1] + 2.f, cw - 4.f, 18.f, 0.16f, 0.17f, 0.22f, 0.95f);
            text(cx + 4.f, R[4][1] + (22 - lh) * 0.5f, cmp, 1.f, 0.72f, 0.25f, 1.f);
            hots_.push_back({cx, R[4][1] + 2.f, cw - 4.f, 18.f, 1112});
        }
    }
    if (!reel_.collapsed) {
        float cap_h = 3 * lh + 8;                            // the three metadata lines under a tile
        float th = R[4][3] - 22 - 8 - cap_h;                 // thumbnail draw height
        if (th < 24.f) th = 24.f;
        float tw = th * (16.f / 9.f);
        if (reel_count_ == 0) {
            // same honesty as the no-clock timeline (the eye, 2026-09-03): state
            // the tray's shape, don't leave a void. ALL REEL_MAX slots are drawn
            // (the header counts to REEL_MAX; six slots next to [0/12] was a lie
            // the eye caught), sized to fill the band's width exactly.
            float ty = R[4][1] + 26;
            rect(R[4][0] + 10, ty, R[4][2] - 20, th, 0.10f, 0.11f, 0.15f, 0.95f);
            const float gap = 8.f;
            const float fit_w = (R[4][2] - 20.f - (REEL_MAX - 1) * gap) / static_cast<float>(REEL_MAX);
            const float fit_h = fit_w * (9.f / 16.f);
            for (int i = 0; i < REEL_MAX; ++i) {
                float px = R[4][0] + 10 + i * (fit_w + gap);
                rect_outline(px, ty + 6, fit_w, fit_h, 1.f,
                             i == 0 ? 0.85f : 0.30f, i == 0 ? 0.60f : 0.33f,
                             i == 0 ? 0.25f : 0.40f, 1.f);
                char ib[16]; snprintf(ib, sizeof(ib), "%d", i);
                text(px + 4, ty + 8, ib, i == 0 ? 0.85f : 0.40f,
                     i == 0 ? 0.60f : 0.42f, i == 0 ? 0.25f : 0.50f, 1.f);
            }
            text(R[4][0] + 10, ty + th + 2,
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
                hots_.push_back({tx, ty, tw, th, 1100 + slot});
            }
        }
    }

    // ── the TIMELINE (D1: the show clock, drawn; the engine owns the time) ──
    rect(R[3][0], R[3][1], R[3][2], R[3][3], 0.07f, 0.08f, 0.11f, 0.97f);   // near-opaque (defect a)
    rect(R[3][0], R[3][1], R[3][2], 22, 0.13f, 0.14f, 0.19f, 0.95f);
    text(R[3][0] + 8, R[3][1] + (22 - lh) * 0.5f,
         bottom_.collapsed ? "+" : "TIMELINE (D1) - the show clock is a parameter",
         0.62f, 0.66f, 0.74f, 1.f);
    // the container line, same law as the docks (2026-09-03, the eye): the
    // timeline and reel never got one, so the bottom bands read as voids with
    // text in them — not panels. A panel is a thing on screen, not a rumor.
    rect_outline(R[3][0], R[3][1], R[3][2], R[3][3], 1.f, 0.30f, 0.60f, 1.00f, 0.55f);
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
        button(bx, " KEY ", 905, false);   // key the live clock time (tool feature 4)

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
        if (clk_n_ == 0 && clk_total_ <= 0.0) {
            // THE TRANSPORT DRIVES THE LIVE CLOCK (2026-09-02): with no joints
            // pack the hinge march IS the show — same buttons, same scrub bar,
            // phase over the hinge's own period. The dead instruction text the
            // eye read ("no play button, no timeline") is gone: a clock that
            // exists is a clock that plays.
            if (hinge_live_ && clk_hinge_period_ > 0.f) {
                rect(scrub_rect_[0], bar_y, scrub_rect_[2], bar_h, 0.12f, 0.13f, 0.17f, 0.95f);
                rect_outline(scrub_rect_[0], bar_y, scrub_rect_[2], bar_h, 1.f, 0.35f, 0.37f, 0.42f, 1.f);
                // half-period marks: the ROM's extremes (cos law: 0 and P/2)
                rect(scrub_rect_[0] + scrub_rect_[2] * 0.25f, bar_y + 2, 2.f, bar_h - 4, 0.45f, 0.47f, 0.52f, 1.f);
                rect(scrub_rect_[0] + scrub_rect_[2] * 0.75f, bar_y + 2, 2.f, bar_h - 4, 0.45f, 0.47f, 0.52f, 1.f);
                // D2: derived sweep-window and reel-capture markers share the
                // same loop normalization as the playhead and key marks.
                for (const auto& marker : timeline_markers_) {
                    double period_m = clk_hinge_period_ > 0.0 ? clk_hinge_period_ : clk_total_;
                    if (period_m <= 0.0) continue;
                    double mt = marker.t - floor(marker.t / period_m) * period_m;
                    float mx = scrub_rect_[0] + static_cast<float>(mt / period_m) * scrub_rect_[2];
                    float mr = 0.30f, mg = 0.80f, mb = 0.45f;
                    if (marker.kind == 1) { mr = 0.30f; mg = 0.60f; mb = 1.00f; }
                    else if (marker.kind == 3) { mr = 0.90f; mg = 0.55f; mb = 0.20f; }
                    rect(mx - 0.5f, bar_y - 2.f, 1.f, 4.f, mr, mg, mb, 0.95f);
                }
                // THE KEY MARKS: diamonds on the bar, amber, clickable — click
                // one and the clock lands that pose (a paused clock = exact).
                for (size_t ki = 0; ki < key_marks_ui_.size() && ki < 99; ++ki) {
                    double kt = key_marks_ui_[ki].second;
                    double lkt = clk_hinge_period_ > 0.0
                                 ? kt - floor(kt / clk_hinge_period_) * clk_hinge_period_ : kt;
                    float kx = scrub_rect_[0] + static_cast<float>(lkt / clk_hinge_period_) * scrub_rect_[2];
                    float cw = fminf(7.f, bar_h * 0.45f);
                    rect(kx - cw * 0.5f, bar_y + (bar_h - cw) * 0.5f, cw, cw, 1.f, 0.72f, 0.25f, 1.f);
                    hots_.push_back({ kx - cw * 0.5f, bar_y + (bar_h - cw) * 0.5f, cw, cw,
                                      700 + static_cast<int>(ki) });
                }
                double lt = clk_hinge_period_ > 0.0 ? clk_t_ - floor(clk_t_ / clk_hinge_period_) * clk_hinge_period_ : 0.0;
                float px = scrub_rect_[0] + static_cast<float>(lt / clk_hinge_period_) * scrub_rect_[2];
                rect(px - 1, bar_y - 2, 3, bar_h + 4, 1.f, 1.f, 1.f, 1.f);
                char hb[160];
                snprintf(hb, sizeof(hb), "hinge march  t = %.3f / %.1f s  |  %zu key%s |  scrub/step = exact knee poses",
                         lt, clk_hinge_period_, key_marks_ui_.size(),
                         key_marks_ui_.size() == 1 ? "" : "s");
                text(x, bar_y + bar_h + 6, hb, 0.62f, 0.66f, 0.74f, 1.f);
            } else {
                // 2026-09-03, the eye (loaded review): with no clock loaded this
                // band was one amber line of void — the dyad read the empty
                // bottom band as dead space. A viewport gets a grid before a
                // mesh; the timeline gets the same honesty: an instrument
                // scaffold (baseline + ticks + readout) that states what fills
                // it. Static, truth-bearing, and gone the moment a clock lands.
                rect(scrub_rect_[0], bar_y, scrub_rect_[2], bar_h, 0.10f, 0.11f, 0.15f, 0.95f);
                rect_outline(scrub_rect_[0], bar_y, scrub_rect_[2], bar_h, 1.f, 0.50f, 0.55f, 0.65f, 1.f);
                const float mid = bar_y + bar_h * 0.5f;
                rect(scrub_rect_[0], mid, scrub_rect_[2], 1.f, 0.40f, 0.44f, 0.52f, 1.f);
                for (int i = 1; i < 10; ++i) {
                    float tx = scrub_rect_[0] + (i / 10.f) * scrub_rect_[2];
                    rect(tx, mid - 5.f, 1.f, 10.f, 0.45f, 0.48f, 0.56f, 1.f);
                }
                // one line, BELOW the bar like every clocked branch (the in-bar
                // zone is glyph-height, and lh > bar_h — an in-bar label overlaps
                // anything under the bar; the eye, loaded review r6). The label
                // IS the hint; a second line was clutter + collision.
                text(x, bar_y + bar_h + 6,
                     "no clock loaded - POST /hinge_bin (the march) or /joints_bin (the 19-joint show)",
                     0.85f, 0.55f, 0.30f, 1.f);
            }
        } else {
            rect(scrub_rect_[0], bar_y, scrub_rect_[2], bar_h, 0.12f, 0.13f, 0.17f, 0.95f);
            rect_outline(scrub_rect_[0], bar_y, scrub_rect_[2], bar_h, 1.f, 0.35f, 0.37f, 0.42f, 1.f);
            for (uint32_t i = 0; i < clk_n_; ++i) {
                float fx = scrub_rect_[0] + (i * clk_period_ / clk_total_) * scrub_rect_[2];
                bool cur = (i == clk_cur_);
                rect(fx, bar_y + 2, 2.f, bar_h - 4,
                     cur ? 0.30f : 0.45f, cur ? 0.60f : 0.47f, cur ? 1.00f : 0.52f, 1.f);
            }
            // D2: authored joint-window starts and recorded captures. These
            // markers are read-only engine events, not alternate key marks.
            for (const auto& marker : timeline_markers_) {
                if (clk_total_ <= 0.0) continue;
                double mt = marker.t - floor(marker.t / clk_total_) * clk_total_;
                float mx = scrub_rect_[0] + static_cast<float>(mt / clk_total_) * scrub_rect_[2];
                float mr = 0.30f, mg = 0.80f, mb = 0.45f;
                if (marker.kind == 1) { mr = 0.30f; mg = 0.60f; mb = 1.00f; }
                else if (marker.kind == 3) { mr = 0.90f; mg = 0.55f; mb = 0.20f; }
                rect(mx - 0.5f, bar_y - 2.f, 1.f, 4.f, mr, mg, mb, 0.95f);
            }
            // key marks over the joints show's total (same diamonds, same law)
            for (size_t ki = 0; ki < key_marks_ui_.size() && ki < 99; ++ki) {
                double kt = key_marks_ui_[ki].second;
                double lkt = clk_total_ > 0.0 ? kt - floor(kt / clk_total_) * clk_total_ : kt;
                if (lkt < 0.0 || lkt > clk_total_) continue;
                float kx = scrub_rect_[0] + static_cast<float>(lkt / clk_total_) * scrub_rect_[2];
                float cw = fminf(7.f, bar_h * 0.45f);
                rect(kx - cw * 0.5f, bar_y + (bar_h - cw) * 0.5f, cw, cw, 1.f, 0.72f, 0.25f, 1.f);
                hots_.push_back({ kx - cw * 0.5f, bar_y + (bar_h - cw) * 0.5f, cw, cw,
                                  700 + static_cast<int>(ki) });
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

        // ── D7: THE DOPE SHEET — per-joint key rows below the master scrub ──
        // Group dope_keys_ by joint. Each group gets one row: name label +
        // mini-scrub bar + amber diamonds (clickable). Unkeyed keys go in
        // the "UNGROUPED" row. This is the visual bridge between the key
        // system and the joint system — you SEE which joint owns which key.
        // 2026-09-03, the eye (r7): the sheet drew even with NO clock loaded —
        // persisted keys produced a floating "UNKEYED" row that overlapped the
        // no-clock hint text. A dope sheet is rows ALONG a time axis; without
        // a clock there is no axis, so the sheet waits for one.
        if (clk_n_ > 0 || clk_total_ > 0.0 || (hinge_live_ && clk_hinge_period_ > 0.f)) {
            float dy = bar_y + bar_h + 22;   // start below the info text
            float dw = scrub_rect_[2];        // same width as the master bar
            float dh = 14.f;                  // row height
            const float label_w = 90.f;      // joint name column width

            // group by joint
            std::unordered_map<std::string, std::vector<size_t>> groups;
            for (size_t i = 0; i < dope_keys_.size(); ++i) {
                std::string j = dope_keys_[i].joint.empty() ? "UNKEYED" : dope_keys_[i].joint;
                groups[j].push_back(i);
            }
            // stable order: named joints first (alphabetical), UNKEYED last
            std::vector<std::string> order;
            for (auto& p : groups)
                if (p.first != "UNKEYED") order.push_back(p.first);
            std::sort(order.begin(), order.end());
            if (groups.count("UNKEYED")) order.push_back("UNKEYED");

            float total_dh = static_cast<float>(order.size()) * (dh + 2.f);
            float max_dy = R[3][1] + R[3][3] - total_dh - 4;
            if (dy > max_dy) dy = max_dy;   // clamp so rows stay inside the dock

            for (auto& jn : order) {
                auto& indices = groups[jn];
                float row_x = x;
                // background
                rect(row_x, dy, dw, dh, 0.08f, 0.09f, 0.12f, 0.90f);
                // label (dim, fixed-width column)
                std::string label = jn.size() > 10 ? jn.substr(0, 9) + "." : jn;
                text(row_x + 2, dy + (dh - lh) * 0.5f, label, 0.48f, 0.50f, 0.58f, 0.9f);
                // mini-scrub bar
                float mbx = row_x + label_w;
                float mbw = dw - label_w - 4;
                rect(mbx, dy + 2, mbw, dh - 4, 0.10f, 0.11f, 0.14f, 0.85f);
                // playhead line on every row
                double period = clk_hinge_period_ > 0.f ? clk_hinge_period_ : clk_total_;
                if (period > 0.0) {
                    double lt = clk_t_ - floor(clk_t_ / period) * period;
                    float px = mbx + static_cast<float>(lt / period) * mbw;
                    rect(px - 0.5f, dy, 1.f, dh, 0.5f, 0.52f, 0.58f, 0.7f);
                }
                // key diamonds
                for (size_t ki = 0; ki < indices.size(); ++ki) {
                    const auto& dk = dope_keys_[indices[ki]];
                    double period2 = clk_hinge_period_ > 0.f ? clk_hinge_period_ : clk_total_;
                    double lkt = period2 > 0.0
                        ? dk.t - floor(dk.t / period2) * period2 : dk.t;
                    float kx = mbx + static_cast<float>(lkt / period2) * mbw;
                    float cw = fminf(8.f, (dh - 4) * 0.5f);
                    rect(kx - cw * 0.5f, dy + (dh - cw) * 0.5f, cw, cw, 1.f, 0.72f, 0.25f, 1.f);
                    hots_.push_back({ kx - cw * 0.5f, dy + (dh - cw) * 0.5f, cw, cw,
                                      1000 + static_cast<int>(indices[ki]) });
                }
                dy += dh + 2;
            }
            // total dope sheet height (so the dock can account for it)
            dope_sheet_h_ = dy - (bar_y + bar_h + 22);
        }
    }

    // D4: side-by-side evidence compare. The images and captions come directly
    // from the selected reel slots; this is a view, not a second render path.
    if (compare_a_slot_ >= 0 && compare_b_slot_ >= 0 &&
        tiles_[compare_a_slot_].used && tiles_[compare_b_slot_].used) {
        const float vx0 = R[1][2], vx1 = R[2][0];
        const float vy0 = R[0][3], vy1 = R[4][1];
        const float gap = 12.f;
        const float half_w = (vx1 - vx0 - gap - 20.f) * 0.5f;
        const float image_h = fminf(half_w * (9.f / 16.f), vy1 - vy0 - 5.f * lh - 30.f);
        if (half_w > 40.f && image_h > 24.f) {
            rect(vx0, vy0, vx1 - vx0, vy1 - vy0, 0.035f, 0.045f, 0.07f, 0.98f);
            text(vx0 + 10.f, vy0 + 8.f, "D4 A/B COMPARE - captured evidence (view only)",
                 0.86f, 0.88f, 0.92f, 1.f);
            const int slots[2] = {compare_a_slot_, compare_b_slot_};
            for (int side = 0; side < 2; ++side) {
                const float px = vx0 + 10.f + side * (half_w + gap);
                const float py = vy0 + 26.f;
                rect_outline(px - 1.f, py - 1.f, half_w + 2.f, image_h + 2.f, 2.f,
                             side == 0 ? 0.30f : 1.00f, side == 0 ? 0.60f : 0.72f,
                             side == 0 ? 1.00f : 0.25f, 1.f);
                thumb(px, py, half_w, image_h, slots[side]);
                const ReelTile& tile = tiles_[slots[side]];
                char tag[16]; snprintf(tag, sizeof(tag), "%c  seq %llu", side == 0 ? 'A' : 'B',
                                       static_cast<unsigned long long>(tile.seq));
                text(px, py + image_h + 6.f, tag, 1.f, side == 0 ? 0.72f : 0.86f,
                     side == 0 ? 0.25f : 0.30f, 1.f);
                text(px, py + image_h + 6.f + lh, tile.l1, 0.86f, 0.88f, 0.92f, 1.f);
                text(px, py + image_h + 6.f + 2.f * lh, tile.l2, 0.62f, 0.66f, 0.74f, 1.f);
                text(px, py + image_h + 6.f + 3.f * lh, tile.l3, 0.45f, 0.47f, 0.52f, 1.f);
            }
        }
    }

    // ── C1: THE GIZMO — the selected joint's center + axis over the viewport,
    // projected by the engine through the mesh pass's own VP (drawn last, over
    // everything — it is screen-space truth about the model underneath) ──
    // ── THE VIEWPORT REFERENCE FRAME, under everything else in the viewport ──
    // Drawn FIRST, so the gizmo, the chrome and the console all sit on top of it.
    // These are screen-space segments over world points the engine projected —
    // the grid is an instrument, never matter.
    if (visible) {
        // D8/C1 overlays belong to the central viewport only. Clip screen-space
        // instruments at the dock boundaries so a long projected axis cannot
        // bleed into the REEL or timeline chrome.
        const float clip_x0 = R[1][2], clip_y0 = R[0][3];
        const float clip_x1 = R[2][0], clip_y1 = R[4][1];
        auto inside_viewport = [&](float px, float py) {
            return px >= clip_x0 && px <= clip_x1 && py >= clip_y0 && py <= clip_y1;
        };
        auto clipped_line = [&](float ax, float ay, float bx, float by, float th,
                                float r, float g, float b, float a) {
            // Liang-Barsky: retain the portion inside the central viewport.
            float dx = bx - ax, dy = by - ay;
            float t0 = 0.f, t1 = 1.f;
            auto cut = [&](float p, float q) {
                if (fabsf(p) < 1e-6f) return q >= 0.f;
                float t = q / p;
                if (p < 0.f) { if (t > t1) return false; if (t > t0) t0 = t; }
                else         { if (t < t0) return false; if (t < t1) t1 = t; }
                return true;
            };
            if (!cut(-dx, ax - clip_x0) || !cut(dx, clip_x1 - ax) ||
                !cut(-dy, ay - clip_y0) || !cut(dy, clip_y1 - ay)) return;
            line(ax + t0 * dx, ay + t0 * dy, ax + t1 * dx, ay + t1 * dy,
                 th, r, g, b, a);
        };
        for (const auto& gl : grid_)
            clipped_line(gl.x0, gl.y0, gl.x1, gl.y1, 1.f, gl.r, gl.g, gl.b, gl.a);
        // D8: the authored FK chain, projected by the engine. This is an
        // editor instrument over the membrane, not a second renderable body.
        if (rig_overlay_ui_) {
            for (const auto& rs : rig_segments_) {
                const float r = rs.selected ? 1.00f : 0.30f;
                const float g = rs.selected ? 0.72f : 0.75f;
                const float b = rs.selected ? 0.18f : 0.95f;
                clipped_line(rs.x0, rs.y0, rs.x1, rs.y1, rs.selected ? 3.0f : 2.0f,
                             r, g, b, rs.selected ? 0.95f : 0.72f);
                if (inside_viewport(rs.x0, rs.y0))
                    rect(rs.x0 - 2.5f, rs.y0 - 2.5f, 5.f, 5.f, r, g, b,
                         rs.selected ? 1.f : 0.82f);
                if (inside_viewport(rs.x1, rs.y1))
                    rect(rs.x1 - 2.5f, rs.y1 - 2.5f, 5.f, 5.f, r, g, b,
                         rs.selected ? 1.f : 0.82f);
            }
        }
        if (viewport_empty_) {
            // SAY IT. A void makes the eye invent an explanation, and the
            // explanation it invents is "render failed".
            const char* msg = "no mesh loaded  -  POST /mesh_bin (or /membrane_bin)";
            float w = static_cast<float>(strlen(msg)) * advance_;
            text((static_cast<float>(ext_.width) - w) * 0.5f,
                 static_cast<float>(ext_.height) * 0.5f,
                 msg, 0.42f, 0.45f, 0.52f, 1.f);
        }
    }

    if (gizmo_vis_ && visible) {
        line(gizmo_[0], gizmo_[1], gizmo_[2], gizmo_[3], 2.5f, 1.0f, 0.85f, 0.20f, 1.f);
        rect(gizmo_[0] - 3, gizmo_[1] - 3, 6, 6, 1.0f, 0.85f, 0.20f, 1.f);   // J, the center
        rect_outline(gizmo_[0] - 5, gizmo_[1] - 5, 10, 10, 1.f, 0.2f, 0.2f, 0.2f, 1.f);
        text(gizmo_[0] + 8, gizmo_[1] - lh * 0.5f, gizmo_label_, 1.0f, 0.85f, 0.40f, 1.f);
    }

    // D3: resolve hover from the current frame's timeline geometry. This is
    // read-only presentation; no transport state moves and the tooltip is never
    // one frame stale.
    marker_hover_ = false;
    marker_hover_label_.clear();
    if (cursor_x_ >= 0 && cursor_y_ >= 0 && !bottom_.collapsed && clk_total_ > 0.0f) {
        const float hover_y0 = scrub_rect_[1] - 6.f;
        const float hover_y1 = scrub_rect_[1] + scrub_rect_[3] + 6.f;
        if (cursor_y_ >= hover_y0 && cursor_y_ <= hover_y1 && scrub_rect_[2] > 0.f) {
            const double period = clk_hinge_period_ > 0.f ? clk_hinge_period_ : clk_total_;
            const float px = static_cast<float>(cursor_x_);
            const float max_dx = fmaxf(1.f, scrub_rect_[3] * 0.5f);  // half the active marker lane height
            double best = 1e30;
            for (const auto& marker : timeline_markers_) {
                if (period <= 0.0) break;
                double mt = marker.t - floor(marker.t / period) * period;
                float mx = scrub_rect_[0] + static_cast<float>(mt / period) * scrub_rect_[2];
                float dx = fabsf(px - mx);
                if (dx <= max_dx && dx < best) {
                    best = dx; marker_hover_ = true; marker_hover_x_ = mx;
                    marker_hover_y_ = scrub_rect_[1]; marker_hover_t_ = marker.t;
                    marker_hover_kind_ = marker.kind; marker_hover_label_ = marker.label;
                }
            }
        }
    }

    // D3: show the derived marker metadata only while the pointer is close to
    // the marker tick.
    if (marker_hover_) {
        char hb[256];
        const char* kind = marker_hover_kind_ == 1 ? "WINDOW START"
                           : marker_hover_kind_ == 3 ? "WINDOW END" : "CAPTURE";
        snprintf(hb, sizeof(hb), "%s  |  t = %.6f s  |  %s",
                 kind, marker_hover_t_, marker_hover_label_.c_str());
        float hw = static_cast<float>(strlen(hb)) * advance_ + 12.f;
        float hx = marker_hover_x_ + 8.f;
        if (hx + hw > static_cast<float>(win_w) - 6.f) hx = marker_hover_x_ - hw - 8.f;
        if (hx < 6.f) hx = 6.f;
        float hy = marker_hover_y_ - lh - 10.f;
        if (hy < R[0][3] + 4.f) hy = marker_hover_y_ + scrub_rect_[3] + 8.f;
        rect(hx, hy, hw, lh + 6.f, 0.04f, 0.05f, 0.08f, 0.96f);
        rect_outline(hx, hy, hw, lh + 6.f, 1.f, 0.30f, 0.60f, 1.00f, 0.8f);
        text(hx + 6.f, hy + 3.f, hb, 0.86f, 0.88f, 0.92f, 1.f);
    }

    build_chrome();
    build_console();

    // ── THE CONTEXT MENU draw — LAST chrome, so it rides above everything.
    // It lives here, not in build_chrome(), because that builder early-returns
    // when the status bar is off — a menu must draw in every chrome state.
    if (ctx_open()) {
        float w, h; ctx_measure(w, h);
        rect(ctx_x_, ctx_y_, w, h, 0.10f, 0.11f, 0.16f, 0.98f);
        rect_outline(ctx_x_, ctx_y_, w, h, 1.f, 0.30f, 0.60f, 1.00f, 0.95f);
        float iy = ctx_y_ + 4.f * ui_scale_;
        for (const auto& it : ctx_items_) {
            float ir = 0.85f, ig = 0.87f, ib = 0.92f;
            if (it.verb == 2) { ir = 0.95f; ig = 0.45f; ib = 0.40f; }   // Delete reads as the destructive verb it is
            text(ctx_x_ + 10.f, iy, it.label, ir, ig, ib, 1.f);
            iy += ctx_item_h();
        }
    }
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
    rctx_.clear();                                  // right-click customers rebuild every frame
    {
        // 2026-09-02, the eye (defect d): the row was left-pinned under the
        // HUD rows, leaving the toolbar's right half dead. Right-ALIGN the
        // whole chip row to the viewport's right edge (10 px margin): the
        // viewport keeps the left, the shot controls own the right — the
        // balance the eye asked for. Row width first (names are known),
        // then draw from the computed start.
        float row_w = 0.f;
        for (size_t i = 0; i < cam_marks_.size(); ++i)
            row_w += static_cast<float>(std::string("[" + std::to_string(i + 1) + " " + cam_marks_[i] + "]").size()) * advance_ + 12.f + 6.f;
        row_w += 6.f + 7.f * advance_ + 12.f;   // the "[+ cam]" chip: gap + 7-char cap + the chips' 12px padding
        // 2nd-scan fix: right-align at the RIGHT DOCK'S LEFT edge (not its right
        // edge — that ran the row THROUGH the dock's top, colliding with the
        // FPS readout). The chips live in the viewport, never over a panel.
        float vw = visible ? (R[2][0] - 10.f) : (W - 10.f);   // viewport's right edge
        float cx2 = (vw - row_w) > (hx - 6) ? (vw - row_w) : (hx - 6);
        float cy = hy - 3;
        for (size_t i = 0; i < cam_marks_.size(); ++i) {
            std::string cap = "[" + std::to_string(i + 1) + " " + cam_marks_[i] + "]";
            // 2026-09-02, the eye: backing must be OPAQUE — at 0.85 a finger's
            // bright pixels bleed through and "merge into the chip borders".
            float cw = static_cast<float>(cap.size()) * advance_ + 12.f;
            rect(cx2, cy, cw, lh + 6, 0.07f, 0.08f, 0.12f, 1.f);
            rect_outline(cx2, cy, cw, lh + 6, 1.f, 0.30f, 0.60f, 1.00f, 0.9f);
            text(cx2 + 6, cy + 3, cap, 0.30f, 0.60f, 1.00f, 1.f);
            hots_.push_back({ cx2, cy, cw, lh + 6, 800 + static_cast<int>(i) });
            cam_mark_rects_[i] = { cx2, cy, cw, lh + 6 };
            // THE CONTEXT MENU's first customer: each bookmark chip carries its
            // verbs — Recall / Overwrite / Delete. The click/drag split keeps
            // pan on the same button (ui.hpp, the context-menu block).
            rctx_.push_back({ cx2, cy, cw, lh + 6, static_cast<int>(i),
                { { "Recall", 0 }, { "Overwrite", 1 }, { "Delete", 2 } } });
            cx2 += cw + 6;
        }
        std::string cap = "[+ cam]";
        // 2026-09-02, the eye (2nd scan): grammar unified — brackets, border, row
        // blue. 2026-09-03, the eye (loaded review r1) STILL read the chip as a
        // "dim grey box" — the dimmed ink was the remaining tell. Two rounds is
        // the law: the save/recall distinction lives in the LABEL (+ cam), the
        // color carries only affordance (clickable = the row's blue).
        float cw = static_cast<float>(cap.size()) * advance_ + 12.f;
        rect(cx2, cy, cw, lh + 6, 0.07f, 0.08f, 0.12f, 1.f);
        rect_outline(cx2, cy, cw, lh + 6, 1.f, 0.30f, 0.60f, 1.00f, 0.9f);
        text(cx2 + 6, cy + 3, cap, 0.30f, 0.60f, 1.00f, 1.f);
        hots_.push_back({ cx2, cy, cw, lh + 6, 850 });
        cam_save_rect_ = { cx2, cy, cw, lh + 6 };
    }

    // ── F2: the status bar ──
    if (!bar_on_) { chrome_stage_.clear(); chrome_fps_.clear(); chrome_gpu_.clear(); return; }
    float by = H - bar_h();
    rect(0, by, W, bar_h(), 0.06f, 0.07f, 0.10f, 0.95f);
    rect(0, by, W, 1.f, 0.30f, 0.60f, 1.00f, 0.9f);   // the studio's accent line

    // left: WHERE YOU ARE -- the stage's id + name, not the board's sentence.
    // 2026-08-31, the eye on the glass: "EARLIEST NON-GREEN GATE: B7 articulate --
    // the next stage [next] appears twice -- once under the stage bar at top and
    // again in the bottom status bar. Duplicated, low-value, adds noise."
    //
    // The standing RULE is the board's to state (B2: computed by
    // tools/studio_board.py, never edited here). The bar is a pointer to the stage
    // you are on. Both are derived from board_.stages -- the bar no longer reprints
    // the board's own sentence, so neither can drift from the other.
    chrome_stage_.clear();
    if (board_.loaded) {
        for (const auto& s : board_.stages) {
            if (s.status == "next") { chrome_stage_ = s.name + " (" + s.id + ")"; break; }
        }
        // no 'next' row (every gate green, or the board says something we do not
        // model) -- fall back to the standing line rather than showing nothing.
        if (chrome_stage_.empty()) chrome_stage_ = board_.standing;
    } else {
        chrome_stage_ = "no board file";
    }
    text(8, by + (bar_h() - lh) * 0.5f, chrome_stage_, 0.30f, 0.60f, 1.00f, 1.f);

    // center: FPS + the frame-time histogram (the ring, oldest -> newest)
    float hist_w = static_cast<float>(FT_RING) * 3.f;
    float cx = W * 0.5f - hist_w * 0.5f;
    snprintf(b, sizeof(b), "%.0f fps  %.2f ms", fps_, ft_avg_);
    chrome_fps_ = b;
    text(cx - 8 - static_cast<float>(chrome_fps_.size()) * advance_,
         by + (bar_h() - lh) * 0.5f, chrome_fps_, 0.86f, 0.88f, 0.92f, 1.f);
    float hb = by + 3.f, hh = bar_h() - 6.f;
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
    float gpu_x = W - 8.f - static_cast<float>(chrome_gpu_.size()) * advance_;
    text(gpu_x, by + (bar_h() - lh) * 0.5f, chrome_gpu_, 0.55f, 0.58f, 0.65f, 1.f);

    // THE EYE'S VERDICT, ALWAYS VISIBLE (2026-09-03, the operator's decree: "I need
    // to see it in the editor" — a report buried in the DOCS picker is a report the
    // operator never sees; the dyad log page remains for the full history). Reads
    // dyad_log.txt (the human-readable mirror the writer maintains), extracts the
    // NEWEST "VERDICT: X" token, shows it in every mode. The verdict line carries
    // the color: amber = HOLD (attention), green = SHIP/CLEAN/PASS/GROUNDED/IMPROVED,
    // gray = no verdict yet. The mtime poll: 1 Hz max, only re-read when the file moves.
    float eye_chip_left = -1.f;   // the legend starts LEFT of this (the no-overlap law)
    {
        static std::string eye_line;      // the last parsed verdict line
        static float eye_r = 0.45f, eye_g = 0.47f, eye_b = 0.52f;
        static long long last_mtime = -1;
        static FILETIME ft_prev{};
        FILETIME ft_now{};
        bool moved = false;
        {
            WIN32_FILE_ATTRIBUTE_DATA fa{};
            char mod[MAX_PATH];
            DWORD mn = GetModuleFileNameA(nullptr, mod, MAX_PATH);
            std::string p = (mn > 0 && mn < MAX_PATH) ? std::string(mod, mn) : "Saved/dyad/dyad_log.txt";
            for (int i = 0; i < 5; ++i) {
                size_t s2 = p.find_last_of("/\\");
                if (s2 == std::string::npos) break;
                p.resize(s2);
            }
            p += "/Saved/dyad/dyad_log.txt";
            if (GetFileAttributesExA(p.c_str(), GetFileExInfoStandard, &fa)) {
                moved = memcmp(&fa.ftLastWriteTime, &ft_prev, sizeof(FILETIME)) != 0;
                ft_prev = fa.ftLastWriteTime;
            }
            if (moved || last_mtime < 0) {
                last_mtime = 1;
                std::ifstream f(p.c_str());
                std::string all, line;
                while (std::getline(f, line)) { all += line; all += '\n'; }
                size_t vpos = all.rfind("VERDICT:");
                if (vpos != std::string::npos) {
                    size_t e = vpos + 8;
                    while (e < all.size() && (all[e] == ' ' || all[e] == '\t')) ++e;
                    size_t eend = e;
                    while (eend < all.size() && all[eend] != '\r' && all[eend] != '\n') ++eend;
                    std::string word = all.substr(e, eend - e);
                    // trim trailing punctuation the model may trail with
                    while (!word.empty() && (word.back() == '.' || word.back() == ',' || word.back() == '*')) word.pop_back();
                    if (!word.empty()) {
                        // the newest entry's time-of-day (the date is noise in a bar)
                        size_t ts = all.rfind('\n', vpos);
                        std::string head = (ts == std::string::npos || ts + 20 > vpos) ? "" : all.substr(ts + 12, 8);
                        eye_line = head + "  EYE: " + word;
                        bool good = (word.find("SHIP") != std::string::npos || word.find("CLEAN") != std::string::npos ||
                                     word.find("PASS") != std::string::npos || word.find("GROUNDED") != std::string::npos ||
                                     word.find("IMPROVED") != std::string::npos);
                        bool bad  = (word.find("HOLD") != std::string::npos || word.find("DEFECTS") != std::string::npos);
                        eye_r = bad ? 0.95f : (good ? 0.30f : 0.45f);
                        eye_g = bad ? 0.62f : (good ? 0.85f : 0.47f);
                        eye_b = bad ? 0.25f : (good ? 0.40f : 0.52f);
                    }
                }
            }
        }
        if (!eye_line.empty()) {
            float ex = gpu_x - 24.f - static_cast<float>(eye_line.size()) * advance_;
            if (ex > cx + hist_w + 180.f)   // degrade, never overlap (the legend's law)
            {
                text(ex, by + (bar_h() - lh) * 0.5f, eye_line, eye_r, eye_g, eye_b, 1.f);
                hots_.push_back({ ex - 4, by, static_cast<float>(eye_line.size()) * advance_ + 8, bar_h(), 860 });
                eye_chip_left = ex;
            }
        }
    }

    // THE LEGEND (2026-09-02, the eye on the glass: "two competing progress
    // metaphors ... no legend explaining why B8 is brown or B10 purple").
    // Drawn right-to-left from the GPU text: swatch + word, the swatch carrying
    // the EXACT status_color() values the strip draws, so the legend cannot
    // drift from the map it explains. Fits between the histogram and the GPU
    // row or it degrades (drops the two hues the board least uses), never overlaps.
    {
        struct Leg { const char* w; float r, g, b; };
        static const Leg legs[] = { {"rolling", 0.60f, 0.45f, 0.90f}, {"blocked", 0.85f, 0.28f, 0.28f},
                                    {"next", 0.30f, 0.60f, 1.00f}, {"partial", 0.90f, 0.70f, 0.20f},
                                    {"done", 0.25f, 0.75f, 0.35f} };
        const int NLEG = 5;
        // the eye chip owns the space right of the legend when present — the
        // first capture proved the collision ("EYE11Hog D" over the timestamp)
        float lx = (eye_chip_left > 0.f) ? eye_chip_left - 24.f : gpu_x - 24.f;
        float ly = by + (bar_h() - lh) * 0.5f;
        for (int i = 0; i < NLEG; ++i) {
            float ww = 6.f + 5.f + strlen(legs[i].w) * advance_ + 16.f;
            if (lx - ww < cx + hist_w + 16.f) break;   // out of room: degrade, don't overlap
            lx -= ww;
            rect(lx, ly + lh * 0.28f, 6.f, lh * 0.44f, legs[i].r, legs[i].g, legs[i].b, 1.f);
            text(lx + 11.f, ly, legs[i].w, legs[i].r, legs[i].g, legs[i].b, 0.95f);
        }
    }
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
    ++rec_calls_;
    if (verts_.empty()) { ++rec_bail_verts_; return; }
    if (!ok())          { ++rec_bail_ok_;   return; }
    VkDeviceSize bytes = verts_.size() * sizeof(Vert);
    if (!ensure_vbuf(bytes)) { ++rec_bail_vbuf_; return; }
    ++rec_draws_;
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
    HFONT font = CreateFontW(-(int)lroundf(DESIGN_FONT_PX * ui_scale_), 0, 0, 0, FW_NORMAL,
                             FALSE, FALSE, FALSE,
                             DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                             CLEARTYPE_QUALITY, FIXED_PITCH | FF_MODERN, L"Consolas");
    if (!font) font = CreateFontW(-(int)lroundf(DESIGN_FONT_PX * ui_scale_), 0, 0, 0, FW_NORMAL,
                                  FALSE, FALSE, FALSE,
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

    // THE 2K SCALE IS DERIVED HERE, ONCE, BEFORE THE ATLAS EXISTS.
    // Not in prepare(), and that is not laziness: create_font_atlas() allocates a
    // new VkImage while the descriptor set that samples it is written exactly
    // once, here in init(). Rebuilding it at runtime leaves dset_ bound to the
    // old image — measured 2026-08-31, the UI dropped to 1.0% coverage because
    // every glyph sampled a stale atlas. Doing it properly means updating the
    // descriptor (and destroying the old image/view), which is its own turn.
    // A mid-session RESIZE therefore does not rescale yet; recorded, not hidden.
    {
        float s = (h > 0) ? (static_cast<float>(h) / DESIGN_H) : 1.f;
            ui_scale_ = (s < 1.f) ? 1.f : s;      // never below the design size
    }
    studio_state_load();

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
    if (vkCreateRenderPass(dev_, &rci, nullptr, &rp_) != VK_SUCCESS) { fprintf(stderr, "studio init: render pass FAILED\n"); return false; }

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
    if (vkCreateDescriptorSetLayout(dev_, &dci, nullptr, &dsl_) != VK_SUCCESS) { fprintf(stderr, "studio init: descriptor set layout FAILED\n"); return false; }
    VkDescriptorPoolSize ps{ VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1 };
    VkDescriptorPoolCreateInfo pci{};
    pci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    pci.maxSets = 1; pci.poolSizeCount = 1; pci.pPoolSizes = &ps;
    if (vkCreateDescriptorPool(dev_, &pci, nullptr, &dpool_) != VK_SUCCESS) { fprintf(stderr, "studio init: descriptor pool FAILED\n"); return false; }
    VkDescriptorSetAllocateInfo dai{};
    dai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dai.descriptorPool = dpool_; dai.descriptorSetCount = 1; dai.pSetLayouts = &dsl_;
    if (vkAllocateDescriptorSets(dev_, &dai, &dset_) != VK_SUCCESS) { fprintf(stderr, "studio init: descriptor set alloc FAILED\n"); return false; }
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
    if (vkCreatePipelineLayout(dev_, &lci, nullptr, &layout_) != VK_SUCCESS) { fprintf(stderr, "studio init: pipeline layout FAILED\n"); return false; }

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
    if (pr != VK_SUCCESS) fprintf(stderr, "studio init: UI pipeline FAILED (%d)\n", (int)pr);
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
