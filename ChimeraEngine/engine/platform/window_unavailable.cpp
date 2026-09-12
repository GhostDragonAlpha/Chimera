// P06 — window/input backend B: UNAVAILABLE (stub). Mirrors the
// vulkan_surface_unavailable.cpp contract: on a platform with no window
// backend yet, window creation reports kUnavailable and the engine's
// no-headless law holds (the surface seam already refuses a surface-less
// engine — P05). DECLARED in P06; not wired into the engine build.
#include "platform/window.h"

namespace plat {

WindowCreateOutcome create_window(uint32_t /*w*/, uint32_t /*h*/) {
    WindowCreateOutcome out{};
    out.status = WindowCreateOutcome::Status::kUnavailable;
    out.error  = "no window backend on this platform";
    return out;
}

void destroy_window(Window& win) { win = Window{}; }

void* native_handle(const Window& win) { return win.native; }

bool pump_events(Window& /*win*/, std::vector<InputEvent>& /*out*/) {
    return true;   // nothing to pump — caller exits, as the surface seam aborts init
}

} // namespace plat