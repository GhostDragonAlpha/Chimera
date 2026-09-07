// P05 — "unavailable" surface backend for the platform seam.
//
// Serves exactly one purpose: letting the STANDALONE HARNESS exercise the
// unavailable contract on any host (including the Windows dev box). It is
// deliberately NOT wired into any engine headless path — the engine has no
// headless surface path, and create_surface's kUnavailable outcome is a
// hard init failure there.
//
// By construction this TU performs NO surface creation and NO presentation:
// it contains no vkCreate*/vkAcquire*/vkQueuePresent calls and effectively
// only writes `status`. The probe verifies the caller's handle stays byte-
// for-byte untouched.

#include "platform/vulkan_surface.h"

namespace plat {
namespace {

// No surface extensions exist on an unavailable platform: names is nullptr,
// count 0. (A zero-length array is not standard C++ and MSVC rejects it, so
// the empty set is expressed as a null pointer.)
const SurfaceExtensionSet kEmptySet{nullptr, 0, false, false};

} // namespace

SurfaceExtensionSet surface_instance_extensions(UnavailableBackend) noexcept {
    return kEmptySet;
}

void create_surface(VkInstance, void*, SurfaceCreateOutcome& out, UnavailableBackend) noexcept {
    out.status = SurfaceStatus::kUnavailable;   // result + surface left untouched
}

} // namespace plat