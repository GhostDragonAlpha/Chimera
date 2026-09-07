// P06 — window/input TRANSLATOR implementation. Verbatim port of the CURRENT
// engine.cpp WndProc translation arms (engine.cpp:100–247) and
// update_camera_input (engine.cpp:63–98), minus the Win32 message decoding.
// Every arithmetic string is copied as-is. One deliberate record (P06 spec
// §6/W2 + §13): the current WndProc's right-drag PAN arm is UNREACHABLE dead
// code (the first WM_MOUSEMOVE&&captured arm at engine.cpp:191 RETURNS before
// the pan arm at 221 ever runs). The translator reproduces the REACHABLE
// behavior (any captured drag orbits; pan never executes) and does NOT emit
// pan effects. Keeping the dead pan arm verbatim would only fake coverage.
#include "platform/window_input.h"
#include <algorithm>
#include <cmath>

namespace plat {

namespace {
inline float radius_floor(const SceneRef& s) noexcept {
    return std::fmax(1.0f, s.mesh_sphere * 1.02f);   // engine.cpp:51 verbatim
}
}

void update_camera_input(CameraState& cam, const InputState& st, float dt,
                         const SceneRef& scene, const WindowHost& host) noexcept {
    // F1: the console captures the ENTIRE keyboard while open — typing a
    // command must never fly the camera (WASD/QE/space/ctrl/R all gated).
    if (host.console_open()) return;
    const float move_speed = 4.0f * dt;   // units/sec
    const float rot_speed  = 1.5f * dt;   // radians/sec
    const float zoom_speed = 8.0f * dt;   // units/sec

    // WASD -> pan target in camera-local XY plane
    float dx = 0.0f, dy = 0.0f;
    if (st.keys['W'] || st.keys[vkcode::kUp])    { dx -= std::sin(cam.theta);    dy += std::cos(cam.theta); }
    if (st.keys['S'] || st.keys[vkcode::kDown])  { dx += std::sin(cam.theta);    dy -= std::cos(cam.theta); }
    if (st.keys['A'] || st.keys[vkcode::kLeft])  { dx -= std::cos(cam.theta);    dy -= std::sin(cam.theta); }
    if (st.keys['D'] || st.keys[vkcode::kRight]) { dx += std::cos(cam.theta);    dy += std::sin(cam.theta); }
    cam.target[0] += dx * move_speed;
    cam.target[2] += dy * move_speed;

    // Q/E -> vertical movement
    if (st.keys['Q']) cam.target[1] -= move_speed;
    if (st.keys['E']) cam.target[1] += move_speed;

    // Space / Ctrl -> zoom
    if (st.keys[' ']) cam.radius = std::fmax(radius_floor(scene), cam.radius - zoom_speed);
    if (st.keys[vkcode::kCtrl]) cam.radius = std::fmin(100.0f, cam.radius + zoom_speed);

    // Hold R -> reset view (radius frames the whole mesh when one is loaded:
    // 45 FOV needs >= sphere/tan(22.5) ~ 2.41x; 2.7x leaves margin)
    if (st.keys['R']) {
        cam.theta   = 0.0f;
        cam.phi     = 0.3f;
        cam.radius  = std::fmax(12.0f, 2.7f * scene.mesh_sphere);
        cam.pan_x   = 0.0f;
        cam.pan_y   = 0.0f;
        cam.target[0] = cam.target[1] = cam.target[2] = 0.0f;
    }
}

bool apply_input_event(const InputEvent& ev, InputState& st, CameraState& cam,
                       SceneRef& scene, WindowHost& host) noexcept {
    switch (ev.kind) {

    case InputKind::kClose:
        // Reachable only through non-pump dispatch paths in the future
        // backend; the pump reports WM_CLOSE as exit_now and never emits this.
        // The engine's shutdown tail destroys the window directly.
        return false;

    case InputKind::kResize:
        // B1 law: frame() consumes these; (0,0) = minimized, frame() skips.
        st.pending_resize_w.store(ev.w);
        st.pending_resize_h.store(ev.h);
        return true;

    case InputKind::kKeyDown: {
        st.keys[ev.key & 0xFF] = true;
        // F1 CONSOLE: the whole keyboard belongs to it while open (edge-triggered).
        const bool con = host.console_open();
        if (ev.key == vkcode::kOem3 && !ev.repeat) { host.console_toggle(); return true; }
        if (con) {
            // UP/DOWN recall history, ESCAPE closes — everything else waits for
            // kChar (shifted JSON punctuation types exactly).
            if (ev.key == vkcode::kUp || ev.key == vkcode::kDown || ev.key == vkcode::kEsc)
                host.console_key(static_cast<int>(ev.key));
            return true;
        }
        // 'P' rest<->wave toggle (edge: autorepeat must not double-toggle).
        if (ev.key == 'P' && !ev.repeat) host.toggle_pose();
        // F1: THE ENGINE STUDIO overlay (same edge-trigger law)
        if (ev.key == vkcode::kF1 && !ev.repeat) host.ui_toggle();
        // F2-F8: workspace shortcuts (G1 panel)
        if (!ev.repeat && host.ui_visible()) {
            int wk = -1;
            if (ev.key == vkcode::kF2) wk = 0;   // BOARD
            if (ev.key == vkcode::kF3) wk = 4;   // SCENE
            if (ev.key == vkcode::kF4) wk = 1;   // JOINTS
            if (ev.key == vkcode::kF5) wk = 6;   // POSES
            if (ev.key == vkcode::kF6) wk = 2;   // DOCS
            if (ev.key == vkcode::kF7) wk = 3;   // LOG
            if (ev.key == vkcode::kF8) wk = 5;   // CAPTURE
            if (wk >= 0) host.set_workspace(wk);
        }
        return false;   // falls through to DefWindowProc, as today
    }

    case InputKind::kKeyUp:
        st.keys[ev.key & 0xFF] = false;
        return false;   // DefWindowProc, as today

    case InputKind::kChar:
        if (host.console_open()) { host.console_char(static_cast<int>(ev.key)); return true; }
        return false;

    case InputKind::kMouseMove: {
        // THE STUDIO always sees the cursor (panel hover/drag state).
        if (host.ui_visible()) host.ui_on_mouse_move(ev.x, ev.y);
        // Captured drag -> ORBIT. (The original's second captured-move arm,
        // engine.cpp:221, is dead code — see the file-top record — so no pan.)
        if (st.mouse_captured) {
            const float dm   = static_cast<float>(ev.x - st.last_mx);
            const float dm_y = static_cast<float>(ev.y - st.last_my);
            cam.theta -= dm * 0.005f;
            cam.phi   -= dm_y * 0.003f;   // drag UP -> camera UP (screen y grows downward)
            st.last_mx = ev.x;
            st.last_my = ev.y;
            return true;
        }
        return false;
    }

    case InputKind::kLeftDown: {
        // A press on a panel is CONSUMED — it must never start an orbit
        // underneath (the Blender law: panels are not transparent to input).
        if (host.ui_visible() && host.ui_consume_lbutton(ev.x, ev.y, true)) {
            if (host.ui_mouse_captured()) host.set_capture(true);   // border drag
            return true;
        }
        // Orbit drag (or mouse capture for a plain press away from the UI).
        host.set_capture(true);
        st.mouse_captured = true;
        st.last_mx = ev.x;
        st.last_my = ev.y;
        return true;
    }

    case InputKind::kLeftUp: {
        if (host.ui_visible() && host.ui_consume_lbutton(0, 0, false)) {
            host.ui_release_capture();
            return true;
        }
        if (st.mouse_captured) { host.set_capture(false); st.mouse_captured = false; }
        return true;   // WndProc returns 0 unconditionally here
    }

    case InputKind::kRightDown:
        if (host.ui_visible()) host.ui_on_rbutton_down(ev.x, ev.y);
        host.set_capture(true);
        st.mouse_captured = true;
        st.last_mx = ev.x;
        st.last_my = ev.y;
        return true;

    case InputKind::kRightUp:
        if (st.mouse_captured) { host.set_capture(false); st.mouse_captured = false; }
        if (host.ui_visible() && host.ui_on_rbutton_up(ev.x, ev.y)) return true;
        return true;   // WndProc returns 0 unconditionally here

    case InputKind::kWheel: {
        // Wheel -> docs browser when its dock is under the cursor, else zoom.
        const float delta = static_cast<float>(ev.wheel) / 120.0f;
        if (host.ui_visible() && host.ui_on_wheel(ev.x, ev.y, delta)) return true;
        cam.radius = std::fmax(radius_floor(scene),
                               std::fmin(100.0f, cam.radius + delta * 2.0f));
        return true;
    }
    }
    return false;
}

} // namespace plat