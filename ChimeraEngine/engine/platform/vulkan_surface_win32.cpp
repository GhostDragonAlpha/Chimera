// P05 — Win32 surface backend for the platform seam.
//
// Preserves EXACTLY the behavior of the code it replaces (Engine::init in
// engine.cpp):
//   - instance gate: enumerate, require VK_KHR_win32_surface, report `blocked`
//     when absent (the engine turns that into its historical hard-fail);
//   - creation: VkWin32SurfaceCreateInfoKHR built from the HWND +
//     GetModuleHandle(nullptr), null allocation callbacks, direct
//     vkCreateWin32SurfaceKHR call, REAL VkResult carried out.
// Cleanup (vkDestroySurfaceKHR) stays in the engine with today's order.

#include "platform/vulkan_surface.h"

#include <windows.h>          // HWND, GetModuleHandle
#include <vulkan/vulkan_win32.h> // VkWin32SurfaceCreateInfoKHR + extension literal

#include <cstring>
#include <new>
#include <vector>

namespace plat {

namespace {

const char* const kWin32SurfaceName = VK_KHR_WIN32_SURFACE_EXTENSION_NAME;

struct SurfaceProbeCache {
    bool                       built = false;
    std::vector<const char*>   own;    // stable backing storage for names
    SurfaceExtensionSet        set{};  // never dereferenced before built
};

SurfaceProbeCache& probe_cache() {
    static SurfaceProbeCache p;   // function-local static: initialized once
    return p;
}

} // namespace

SurfaceExtensionSet surface_instance_extensions(Win32Backend) noexcept {
    SurfaceProbeCache& p = probe_cache();
    if (p.built) return p.set;

    // Mirror the old gate: does the loader expose VK_KHR_win32_surface?
    std::vector<VkExtensionProperties> exts;
    bool enumerated = false;
    try {
        uint32_t cnt = 0;
        if (vkEnumerateInstanceExtensionProperties(nullptr, &cnt, nullptr) == VK_SUCCESS && cnt > 0) {
            exts.resize(cnt);
            enumerated = (vkEnumerateInstanceExtensionProperties(nullptr, &cnt, exts.data()) == VK_SUCCESS);
        }
    } catch (const std::bad_alloc&) {
        exts.clear();
        enumerated = false;   // explicit policy: OOM folds into blocked=true
    }
    bool has = false;
    if (enumerated) {
        for (const auto& e : exts) {
            if (std::strcmp(e.extensionName, kWin32SurfaceName) == 0) { has = true; break; }
        }
    }

    if (has) p.own.push_back(kWin32SurfaceName);   // literal macro: never dangles
    p.set.names    = p.own.empty() ? nullptr : p.own.data();
    p.set.count    = static_cast<uint32_t>(p.own.size());
    p.set.required = true;                          // Win32 engine run needs a surface
    p.set.blocked  = !has;                          // absent -> engine hard-fails
    p.built = true;
    return p.set;
}

void create_surface(VkInstance instance, void* native_window,
                    SurfaceCreateOutcome& out, Win32Backend) noexcept {
    VkWin32SurfaceCreateInfoKHR info{};
    info.sType     = VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR;
    info.hwnd      = static_cast<HWND>(native_window);
    info.hinstance = GetModuleHandle(nullptr);
    info.flags     = 0;

    VkSurfaceKHR created = VK_NULL_HANDLE;
    out.result = vkCreateWin32SurfaceKHR(instance, &info, nullptr, &created);
    if (out.result == VK_SUCCESS) {
        out.status = SurfaceStatus::kCreated;
        out.surface = created;
    } else {
        out.status = SurfaceStatus::kFailed;   // out.surface kept untouched
    }
}

} // namespace plat