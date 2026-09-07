#pragma once
// P05 — platform surface seam.
//
// Encapsulates the two windows into the Vulkan surface layer that differ by
// platform:
//   1. which INSTANCE extensions a surface on this platform needs, and whether
//      the loader actually provides them (the old inline gate in Engine::init);
//   2. how a presentable surface is created from a native window handle.
//
// The seam is behavior-preserving for Win32: same extension strings, same
// creation arguments, same real VkResult carried out on failure, same teardown
// contract (the ENGINE still destroys the surface, in the same order — this
// header owns nothing).
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
//   names   extension-name string LITERALS (static storage; valid for the
//           process lifetime, pointer-stable across calls). Only the
//           platform-conditional name is listed (Win32: VK_KHR_win32_surface);
//           the engine pushes the generic VK_KHR_surface itself, as before.
//   required  the engine must NOT permit a surface-less run (Win32: true;
//             unavailable backend: false).
//   blocked   a REQUIRED platform extension is absent from the loader:
//             instance creation must abort (Win32's historical hard-fail).
struct SurfaceExtensionSet {
    const char* const* names;
    uint32_t           count;
    bool               required;
    bool               blocked;
};

// Enumerates instance extensions and reports the surface-relevant result.
// The result is cached in a function-local static (pointer-stable; second
// and later calls return the same pointers — see regression P1).  noexcept:
// allocation failures are folded into blocked=true per explicit policy (a
// surface cannot be coerced under OOM; the engine aborts init for the same
// reason today).
SurfaceExtensionSet surface_instance_extensions(Win32Backend) noexcept;
SurfaceExtensionSet surface_instance_extensions(UnavailableBackend) noexcept;

enum class SurfaceStatus : uint8_t {
    kCreated,     // surface holds a real loader-created handle; result == its VkResult (VK_SUCCESS)
    kUnavailable, // this platform can never produce a surface; surface + result untouched
    kFailed       // loader returned an error; result holds the REAL VkResult, surface untouched
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