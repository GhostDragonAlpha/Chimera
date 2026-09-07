#pragma once
// P05 — platform surface seam.
//
// Encapsulates the two windows into the Vulkan surface layer that differ by
// platform:
//   1. which INSTANCE extensions a surface on this platform needs, and whether
//      the loader actually provides them (the old inline gate in Engine::init);
//   2. how a presentable surface is created from a native window handle.
//
// Behavior contract vs. the code it replaces — R1-corrected wording:
//   - HAPPY-PATH behaviour is preserved: Win32 uses the same extension string
//     (VK_KHR_win32_surface), the same creation arguments (sType, hwnd,
//     GetModuleHandle(nullptr), null allocator), the same hard-fail signal on
//     absence, and the same teardown contract (the ENGINE destroys the
//     surface, in the same order — this header owns nothing).
//   - The ERROR-PATH is STRICTER, not identical: the pre-seam gate ignored
//     vkEnumerateInstanceExtensionProperties VkResults; this seam checks them,
//     and enumeration failure / VK_INCOMPLETE / allocation failure all fold
//     into blocked=true (documented in docs/evidence/p05/P05_REPAIR_R1.md).
//
// Two tagged backend implementations exist (selected by the build):
//   - Win32Backend        engine/platform/vulkan_surface_win32.cpp
//   - UnavailableBackend  engine/platform/vulkan_surface_unavailable.cpp
// The ENGINE links exactly one. The standalone probe harness
// (tools/platform_surface_probe) links BOTH and drives each tagged backend
// directly, so the "unavailable" contract is exercised even on Windows.

#include <vulkan/vulkan.h>
#include <cstdint>

namespace plat {

// Tag types selecting a backend implementation.
struct Win32Backend {};
struct UnavailableBackend {};

// Which instance extensions a surface on this platform needs declared, and
// whether surface functionality is mandatory for this build.
//   names   extension-name string LITERALS in FIXED static storage (valid for
//           the process lifetime; the pointer is stable by construction —
//           there is no per-process mutable cache). count names follow. Only
//           the platform-conditional name is listed (Win32:
//           VK_KHR_win32_surface); the engine pushes the generic VK_KHR_surface
//           itself, as before.
//   required  the engine must NOT permit a surface-less run (Win32: true;
//             unavailable backend: false).
//   blocked   the required platform extension cannot be established: absent
//             from the loader, OR the enumeration itself failed, VK_INCOMPLETE,
//             or the allocation failed (explicit policy). The engine aborts
//             init on blocked, exactly like the historical hard-fail.
struct SurfaceExtensionSet {
    const char* const* names;
    uint32_t           count;
    bool               required;
    bool               blocked;
};

// Enumerates the loader's instance extensions in FRESH LOCAL STORAGE on every
// call and reports the surface-relevant result (no mutable state between
// queries). names always points at the fixed static array above; count is 0
// and blocked=true on failure/incomplete/absent.  noexcept with a declared
// failure policy: every potentially-throwing allocation in this function is
// covered — std::bad_alloc folds into blocked=true. (See P05_REPAIR_R1.md for
// the exact enumeration-error semantics.)
SurfaceExtensionSet surface_instance_extensions(Win32Backend) noexcept;
SurfaceExtensionSet surface_instance_extensions(UnavailableBackend) noexcept;

enum class SurfaceStatus : uint8_t {
    kCreated,     // surface holds a real loader-created handle; result == its VkResult (VK_SUCCESS)
    kUnavailable, // this platform can never produce a surface; surface + result untouched
    kFailed       // the (injected or real) call returned an error; result holds the EXACT
                  // VkResult; surface untouched — caller keeps its sentinel
};

// Single outcome struct, passed by reference so the caller can observe the
// untouched-handle contract.  Caller pre-initializes:
//   out.result  = VK_SUCCESS
//   out.surface = its sentinel (engine: VK_NULL_HANDLE)
// The backend only ever writes .surface on kCreated.  noexcept: no
// allocation, no exceptions.
struct SurfaceCreateOutcome {
    SurfaceStatus status;
    VkResult      result;
    VkSurfaceKHR  surface;
};

// Creates a presentation surface for `instance` on `native_window` (the
// Win32 HWND, passed as void* to keep OS types out of the shared header; the
// window handle is BORROWED — the caller owns the window and destroys it, in
// the same teardown order as today).
void create_surface(VkInstance instance, void* native_window,
                    SurfaceCreateOutcome& out, Win32Backend) noexcept;
void create_surface(VkInstance instance, void* native_window,
                    SurfaceCreateOutcome& out, UnavailableBackend) noexcept;

// Platform-agnostic entry points used by the engine (resolve to the backend
// selected at compile time).
#if defined(_WIN32)
inline SurfaceExtensionSet surface_instance_extensions() noexcept {
    return surface_instance_extensions(Win32Backend{});
}
inline void create_surface(VkInstance i, void* w, SurfaceCreateOutcome& o) noexcept {
    create_surface(i, w, o, Win32Backend{});
}
#else
inline SurfaceExtensionSet surface_instance_extensions() noexcept {
    return surface_instance_extensions(UnavailableBackend{});
}
inline void create_surface(VkInstance i, void* w, SurfaceCreateOutcome& o) noexcept {
    create_surface(i, w, o, UnavailableBackend{});
}
#endif

} // namespace plat