// P05-R1 — Win32 surface backend for the platform seam.
//
// Behavior vs. the code it replaces (R1-corrected wording — do not describe
// the error path as "exactly unchanged"):
//   - HAPPY-PATH IDENTICAL: same extension string (VK_KHR_win32_surface), same
//     creation arguments (sType, hwnd, GetModuleHandle(nullptr), null
//     allocator), same "VK_KHR_win32_surface not available" hard-fail signal
//     via blocked=true, same teardown contract (the engine destroys the
//     surface, same order).
//   - ERROR-PATH STRICTER, per review point 3: the pre-seam gate IGNORED the
//     vkEnumerateInstanceExtensionProperties VkResults. This backend CHECKs
//     them: first-call failure, VK_INCOMPLETE from the fill, or std::bad_alloc
//     all fold into blocked=true and are reported. The observable upgrade is
//     strictly hard-fail-on-uncertainty instead of scan-garbage-and-proceed.
//   - NO MUTABLE CACHE (review point 2): the extension name lives in FIXED
//     static storage; every query enumerates in fresh local buffers.
//   - noexcept with a declared allocation policy: the enumeration buffer is
//     the only potentially-throwing allocation and is wrapped; bad_alloc
//     folds into blocked=true.
//
// The create path has one narrowly scoped injection seam (R1, review point 5):
// a single function-pointer override (default nullptr = direct loader call)
// written only by plat::win32_set_create_surface_override for the harness's
// controlled-failure experiments. The engine never writes it.

#include "platform/vulkan_surface.h"
#include "platform/vulkan_surface_win32.h"   // win32_set_create_surface_override (self-contained: windows.h)

#include <windows.h>            // HWND, GetModuleHandle (must precede vulkan_win32.h)
#include <vulkan/vulkan_win32.h> // VkWin32SurfaceCreateInfoKHR, PFN, extension literal

#include <cstring>
#include <new>
#include <vector>

namespace plat {

namespace {

// FIXED static extension-name storage (R1: no mutable per-process cache).
const char* const kWin32SurfaceNames[] = { VK_KHR_WIN32_SURFACE_EXTENSION_NAME };

// Controlled-failure test seam. nullptr = real loader call. Engine: never
// written (the setter is harness-only). Harness: written/restored around a
// single experiment. Reads are branch-predictable (null) in production.
PFN_vkCreateWin32SurfaceKHR g_create_override = nullptr;

} // namespace

void win32_set_create_surface_override(PFN_vkCreateWin32SurfaceKHR fn) noexcept {
    g_create_override = fn;
}

SurfaceExtensionSet surface_instance_extensions(Win32Backend) noexcept {
    // Per-query enumeration in FRESH LOCAL storage; no state survives the call.
    std::vector<VkExtensionProperties> enumerated;
    bool complete = false;
    try {
        uint32_t cnt = 0;
        VkResult r0 = vkEnumerateInstanceExtensionProperties(nullptr, &cnt, nullptr);
        if (r0 == VK_SUCCESS) {
            if (cnt == 0) {
                complete = true;                       // loader reports zero extensions
            } else {
                enumerated.resize(cnt);                // only throw point; caught below
                VkResult r1 = vkEnumerateInstanceExtensionProperties(nullptr, &cnt, enumerated.data());
                // VK_INCOMPLETE (list grew between the two calls) leaves the
                // buffer untrustworthy: presence cannot be proven -> blocked.
                complete = (r1 == VK_SUCCESS);
            }
        }
        // r0 != VK_SUCCESS: enumeration failure -> complete stays false -> blocked.
    } catch (const std::bad_alloc&) {
        enumerated.clear();
        complete = false;   // DECLARED policy: OOM folds into blocked=true
    }

    bool has = false;
    if (complete) {
        for (const auto& e : enumerated)
            if (std::strcmp(e.extensionName, kWin32SurfaceNames[0]) == 0) { has = true; break; }
    }

    SurfaceExtensionSet s{};
    s.names    = kWin32SurfaceNames;
    s.count    = has ? 1u : 0u;
    s.required = true;
    s.blocked  = !complete || !has;   // failure / VK_INCOMPLETE / OOM / absent -> hard-fail
    return s;
}

void create_surface(VkInstance instance, void* native_window,
                    SurfaceCreateOutcome& out, Win32Backend) noexcept {
    VkWin32SurfaceCreateInfoKHR info{};
    info.sType     = VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR;
    info.hwnd      = static_cast<HWND>(native_window);
    info.hinstance = GetModuleHandle(nullptr);
    info.flags     = 0;

    VkSurfaceKHR created = VK_NULL_HANDLE;
    PFN_vkCreateWin32SurfaceKHR fn = g_create_override;
    VkResult res = (fn != nullptr)
        ? fn(instance, &info, nullptr, &created)
        : vkCreateWin32SurfaceKHR(instance, &info, nullptr, &created);

    out.result = res;                 // EXACT VkResult always carried (R1)
    if (res == VK_SUCCESS) {
        out.status  = SurfaceStatus::kCreated;
        out.surface = created;
    } else {
        out.status = SurfaceStatus::kFailed;   // out.surface untouched
    }
}

} // namespace plat