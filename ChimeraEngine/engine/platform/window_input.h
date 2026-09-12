#pragma once
// P06 — window/input TRANSLATOR (engine-side, pure). This is the current
// engine.cpp WndProc body minus its Win32 message decoding, ported with the
// arithmetic strings VERBATIM (the "no new camera semantics" law, P06 spec
// §2). The engine links this TU when Inc 3 lands; the offline replay harness
// (tools/window_input_replay) compiles it NOW with a fake WindowHost to
// verify W1–W4 (P06 spec §6). No OS headers, no Vulkan — only standard C++17.
#include "platform/window.h"
#include <cstdint>
#include <atomic>

namespace plat {

// VK_* numeric values adopted as the interchange key space (spec §4 NOTE).
// Values verified against the Windows 10.0.26100 winuser.h (2026-09-07);
// listed as literals so this TU stays free of windows.h.
namespace vkcode {
constexpr uint16_t kCtrl   = 0x11;
constexpr uint16_t kEsc    = 0x1B;
constexpr uint16_t kLeft   = 0x25;
constexpr uint16_t kUp     = 0x26;
constexpr uint16_t kRight  = 0x27;
constexpr uint16_t kDown   = 0x28;
constexpr uint16_t kF1     = 0x70;
constexpr uint16_t kF2     = 0x71;
constexpr uint16_t kF3     = 0x72;
constexpr uint16_t kF4     = 0x73;
constexpr uint16_t kF5     = 0x74;
constexpr uint16_t kF6     = 0x75;
constexpr uint16_t kF7     = 0x76;
constexpr uint16_t kF8     = 0x77;
constexpr uint16_t kOem3   = 0xC0;   // backtick
}

// Camera state + input state as CURRENTLY in engine.cpp, moved out of
// anonymous scope into named types (structural move only — fields and
// arithmetic unchanged).
struct CameraState {
    float  theta  = 0.0f;
    float  phi    = 0.3f;
    float  radius = 12.0f;
    float  pan_x  = 0.0f;
    float  pan_y  = 0.0f;
    float  target[3] = {0.0f, 0.0f, 0.0f};
};

// Load-bearing clones of the engine.cpp statics. `pending_resize_*` keep the
// exact std::atomic memory story of g_pending_resize_* (frame()-side skips 0).
struct InputState {
    bool                   keys[256] = {};
    bool                   mouse_captured = false;
    int32_t                last_mx = 0, last_my = 0;
    std::atomic<uint32_t>  pending_resize_w{0};
    std::atomic<uint32_t>  pending_resize_h{0};
};

// Non-input state the translation reads. `mesh_sphere` drives radius_floor()
// (the zoom floor law: 1.02x the bounding-sphere radius of the posted mesh).
struct SceneRef {
    float mesh_sphere = 0.0f;
};

// The engine's UI gates, injected so the translator is callable with a
// recording fake (offline tests) or the real engine (Inc 3). A host is ALWAYS
// bound once the window exists (window creation happens in Engine::init AFTER
// `g_key_engine = this`), which discharges the old `g_key_engine &&` guards
// (behavior-preserving: no input can arrive before init completes).
struct WindowHost {
    virtual ~WindowHost() = default;
    virtual bool console_open()          const noexcept = 0;
    virtual bool ui_visible()            const noexcept = 0;
    virtual bool ui_mouse_captured()     const noexcept = 0;   // border-drag pose
    virtual bool ui_consume_lbutton(int x, int y, bool down) noexcept = 0;
    virtual void ui_release_capture()              noexcept = 0;
    virtual bool ui_on_rbutton_down(int x, int y)  noexcept = 0;
    virtual bool ui_on_rbutton_up(int x, int y)    noexcept = 0;
    virtual void ui_on_mouse_move(int x, int y)    noexcept = 0;
    virtual bool ui_on_wheel(int x, int y, float delta) noexcept = 0;
    virtual void set_capture(bool on)              noexcept = 0;  // SetCapture/ReleaseCapture binding
    virtual void console_toggle()                  noexcept = 0;
    virtual void console_key(int code)             noexcept = 0;
    virtual void console_char(int c)               noexcept = 0;
    virtual void toggle_pose()                     noexcept = 0;
    virtual void ui_toggle()                       noexcept = 0;
    virtual void set_workspace(int idx)            noexcept = 0;
};

// The current WndProc body, one InputEvent at a time, in arrival order.
// Returns "consumed" (true = return 0 without DefWindowProc — parity with
// WndProc's early returns). Thin sequential ifs REPRODUCE the original
// fall-through precedence exactly (e.g. WM_MOUSEMOVE runs the UI hook AND the
// capture orbit math when both apply, because the UI hook does not consume).
bool apply_input_event(const InputEvent& ev,
                       InputState& st,
                       CameraState& cam,
                       SceneRef& scene,
                       WindowHost& host) noexcept;

// Parity with update_camera_input(g_cam, cfg_.dt) — the per-frame keyboard
// poll. Reads st.keys[] exactly as the original reads g_keys[].
void update_camera_input(CameraState& cam,
                         const InputState& st,
                         float dt,
                         const SceneRef& scene,
                         const WindowHost& host) noexcept;

} // namespace plat