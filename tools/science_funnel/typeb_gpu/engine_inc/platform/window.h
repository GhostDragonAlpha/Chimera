#pragma once
// P06 — window/input platform seam (prepare-only boundary, mirrored on the
// P05 vulkan_surface seam: tagged backends, OS types out of the shared header,
// Outcome struct contract). DECLARED in P06; NOT yet wired into the engine
// build. Spec: docs/evidence/p06/P06_WINDOW_INPUT_PATCH_SPEC.md
#include <cstdint>
#include <vector>

namespace plat {

// Neutral input event. `key` carries the Win32 VK_* numeric code adopted as
// the interchange space (P06 spec §4 NOTE) — the future Linux backend maps
// xkb/evdev onto the same table in the increment that adds it. `repeat` is
// the WndProc edge law (previous-key-state / lParam bit 30).
enum class InputKind : uint8_t {
    kClose,            // title-bar X / WM_CLOSE — the ONLY normal exit
    kResize,           // client w,h; (0,0) = minimized (frame() skips 0)
    kKeyDown, kKeyUp,  // keys[ key & 0xFF ] write
    kChar,             // console printable (WM_CHAR)
    kMouseMove,        // client x,y
    kLeftDown, kLeftUp,
    kRightDown, kRightUp,
    kWheel,            // wheel in 120-units; x,y ALREADY client (backend did ScreenToClient)
};

struct InputEvent {
    InputKind kind;
    uint16_t  key = 0;    // VK_* interchange code (kWheel: unused)
    bool      repeat = false;  // key events only
    int32_t   x = 0, y = 0;    // client coords (kWheel: after screen->client)
    int32_t   wheel = 0;       // kWheel: 120-unit steps
    uint32_t  w = 0, h = 0;    // kResize: client px
};

// Opaque window. OS handle lives inside the backend; `native` is exposed for
// the surface seam only.
struct Window {
    void*    native = nullptr;
    uint32_t client_w = 0;
    uint32_t client_h = 0;
};

struct WindowCreateOutcome {
    enum class Status : uint8_t { kCreated, kFailed, kUnavailable };
    Status      status = Status::kUnavailable;
    Window      window{};
    const char* error = nullptr;  // static-storage text on !kCreated
};

// Window lifecycle + event pumping. Implementation: backend A
// platform/window_win32.cpp (Win32), backend B platform/window_unavailable.cpp
// (stub). P06 declares these; the engine does NOT call them yet.
WindowCreateOutcome create_window(uint32_t w, uint32_t h);
void                destroy_window(Window& win);   // idempotent; nulls native
void*               native_handle(const Window& win);

// Drains the OS queue once, appending decoded events in FIFO order. Returns
// true iff the caller should exit (WM_QUIT or WM_CLOSE). kClose is reported
// through the return value ONLY — never emitted as an InputEvent. The caller
// owns the drain-until-empty policy (current behavior, main.cpp:2510).
bool pump_events(Window& win, std::vector<InputEvent>& out);

} // namespace plat