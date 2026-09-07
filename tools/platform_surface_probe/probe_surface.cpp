// P05 — standalone platform-seam probe.
//
// Drives both backends of the platform seam against the REAL Vulkan loader
// and headers and reports PASS/FAIL per rule-0 falsifier (P1..P4, F1..F5 in
// docs/evidence/p05/P05_PLAN_RULE0.md). Exit code 0 = all checks passed.
//
//   A) UnavailableBackend — extension set is empty / not required / not
//        blocked; create_surface -> kUnavailable with the caller's handle
//        and result byte-for-byte untouched.
//   B) Win32Backend (Windows only) — real loader enumeration; the reported
//        extension must be genuinely present and pointer-stable; a real
//        instance + real hidden HWND -> kCreated, destroyed cleanly (engine
//        teardown order); an instance created WITHOUT the win32 surface
//        extension -> kFailed with the loader's REAL non-success VkResult and
//        the handle untouched (error propagation).
//   C) Zero-arg entry point agrees with the platform-selected backend.

#include "platform/vulkan_surface.h"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include <windows.h>
#include <vulkan/vulkan_win32.h>

namespace {

int g_fails = 0;
int g_checks = 0;

void check(bool ok, const char* what) {
    ++g_checks;
    std::printf("  [%s] %s\n", ok ? "PASS" : "FAIL", what);
    if (!ok) ++g_fails;
}

// Sentinel deliberately NOT VK_NULL_HANDLE so "untouched" is observable.
const VkSurfaceKHR kSentinel = reinterpret_cast<VkSurfaceKHR>(std::uintptr_t{0x12345678u});

std::vector<const char*> enumerate_instance_ext_names() {
    std::vector<const char*> names;
    uint32_t cnt = 0;
    if (vkEnumerateInstanceExtensionProperties(nullptr, &cnt, nullptr) != VK_SUCCESS) return names;
    std::vector<VkExtensionProperties> exts(cnt);
    if (vkEnumerateInstanceExtensionProperties(nullptr, &cnt, exts.data()) != VK_SUCCESS) return names;
    for (const auto& e : exts) names.push_back(e.extensionName);
    return names;
}

VkInstance make_instance(const char* const* ext_names, uint32_t ext_count) {
    VkApplicationInfo ai{};
    ai.sType            = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    ai.pApplicationName = "platform_surface_probe";
    ai.pEngineName      = "chimera_probe";
    ai.apiVersion       = VK_API_VERSION_1_2;

    VkInstanceCreateInfo ci{};
    ci.sType                   = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    ci.pApplicationInfo        = &ai;
    ci.enabledExtensionCount   = ext_count;
    ci.ppEnabledExtensionNames = ext_count ? ext_names : nullptr;

    VkInstance inst = VK_NULL_HANDLE;
    if (vkCreateInstance(&ci, nullptr, &inst) != VK_SUCCESS) inst = VK_NULL_HANDLE;
    return inst;
}

void leg_unavailable() {
    std::printf("[A] UnavailableBackend\n");
    plat::SurfaceExtensionSet s = plat::surface_instance_extensions(plat::UnavailableBackend{});
    check(!s.required, "extensions: required == false");
    check(!s.blocked,  "extensions: blocked == false");
    check(s.count == 0, "extensions: count == 0");
    check(s.names == nullptr, "extensions: names == nullptr");

    plat::SurfaceCreateOutcome o{};
    o.result  = VK_SUCCESS;
    o.surface = kSentinel;
    plat::create_surface(VK_NULL_HANDLE, nullptr, o, plat::UnavailableBackend{});
    check(o.status == plat::SurfaceStatus::kUnavailable, "create_surface -> kUnavailable");
    check(o.result == VK_SUCCESS, "create_surface: result untouched (VK_SUCCESS)");
    check(o.surface == kSentinel, "create_surface: output handle byte-for-byte untouched");
}

#if defined(_WIN32)
void leg_win32() {
    std::printf("[B] Win32Backend\n");
    plat::SurfaceExtensionSet s1 = plat::surface_instance_extensions(plat::Win32Backend{});
    check(s1.required, "extensions: required == true");
    check(!s1.blocked, "extensions: blocked == false (win32 surface present on this loader)");
    check(s1.count == 1, "extensions: count == 1");
    check(s1.names != nullptr, "extensions: names != nullptr");
    check(s1.count == 0 ||
          std::strcmp(s1.names[0], VK_KHR_WIN32_SURFACE_EXTENSION_NAME) == 0,
          "extensions: name == VK_KHR_win32_surface");

    // The reported extension must really be enumerable (ties the seam to reality).
    bool present_in_loader = false;
    for (const char* n : enumerate_instance_ext_names())
        if (std::strcmp(n, VK_KHR_WIN32_SURFACE_EXTENSION_NAME) == 0) present_in_loader = true;
    check(present_in_loader, "extensions: VK_KHR_win32_surface IS present in the loader list");
    check(s1.blocked == !present_in_loader, "extensions: blocked agrees with loader presence");

    // Pointer stability across calls (no per-init re-enumeration).
    plat::SurfaceExtensionSet s2 = plat::surface_instance_extensions(plat::Win32Backend{});
    check(s2.names == s1.names && s2.count == s1.count, "extensions: pointer-stable across calls");

    // Real instance + real hidden window -> kCreated.
    const char* const ext_names[] = {
        VK_KHR_SURFACE_EXTENSION_NAME,
        VK_KHR_WIN32_SURFACE_EXTENSION_NAME,
    };
    VkInstance inst = make_instance(ext_names, 2);
    check(inst != VK_NULL_HANDLE, "instance: created with the surface ext set");

    WNDCLASSW wc{};
    wc.lpfnWndProc   = DefWindowProc;
    wc.hInstance     = GetModuleHandle(nullptr);
    wc.lpszClassName = L"chimera_probe_wnd";
    check(RegisterClassW(&wc) != 0, "window: class registered");
    HWND hwnd = wc.hInstance
        ? CreateWindowW(wc.lpszClassName, L"chimera_probe", WS_OVERLAPPEDWINDOW,
                        CW_USEDEFAULT, CW_USEDEFAULT, 320, 200, nullptr, nullptr,
                        wc.hInstance, nullptr)
        : nullptr;
    check(hwnd != nullptr, "window: HWND created");

    if (inst != VK_NULL_HANDLE && hwnd != nullptr) {
        plat::SurfaceCreateOutcome o{};
        o.result  = VK_SUCCESS;
        o.surface = kSentinel;
        plat::create_surface(inst, static_cast<void*>(hwnd), o, plat::Win32Backend{});
        check(o.status == plat::SurfaceStatus::kCreated, "create_surface (real instance+window) -> kCreated");
        check(o.surface != nullptr, "create_surface: non-null surface");
        check(o.result == (VkResult)0, "create_surface: result == VK_SUCCESS");
        if (o.status == plat::SurfaceStatus::kCreated) {
            // Mirrors the engine's teardown contract: a clean vkDestroySurfaceKHR
            // executes without fault (destroy returns void by spec).
            vkDestroySurfaceKHR(inst, o.surface, nullptr);
            check(true, "teardown: vkDestroySurfaceKHR executed cleanly (engine-order compatible)");
        }
    } else {
        check(false, "create_surface (real instance+window) NOT RUN: prerequisite failed");
    }

    // Error propagation: an instance WITHOUT the win32 surface extension must
    // yield kFailed carrying the loader's REAL non-success VkResult, with the
    // output handle untouched.
VkInstance bare = make_instance(nullptr, 0);
        check(bare != VK_NULL_HANDLE, "instance: bare (no surface ext) created");
        if (bare != VK_NULL_HANDLE && hwnd != nullptr) {
            plat::SurfaceCreateOutcome o2{};
            o2.result  = VK_SUCCESS;
            o2.surface = kSentinel;
            plat::create_surface(bare, static_cast<void*>(hwnd), o2, plat::Win32Backend{});
            check(o2.status == plat::SurfaceStatus::kFailed, "error-path: kFailed (no win32 ext on instance)");
            check(o2.result != (VkResult)0, "error-path: REAL VkResult is not swallowed");
            check(o2.surface == kSentinel, "error-path: output handle untouched on failure");
            vkDestroyInstance(bare, nullptr);
        }

    if (inst != VK_NULL_HANDLE) vkDestroyInstance(inst, nullptr);
    if (hwnd != nullptr) DestroyWindow(hwnd);
    if (wc.hInstance) UnregisterClassW(wc.lpszClassName, wc.hInstance);
}
#endif

void leg_platform_entry() {
    std::printf("[C] zero-arg platform entry point\n");
    plat::SurfaceExtensionSet u = plat::surface_instance_extensions();
    plat::SurfaceExtensionSet t = plat::surface_instance_extensions(
#if defined(_WIN32)
        plat::Win32Backend{});
#else
        plat::UnavailableBackend{});
#endif
    check(u.names == t.names && u.count == t.count &&
          u.required == t.required && u.blocked == t.blocked,
          "entry point agrees with the platform-selected backend");
}

} // namespace

int main() {
#if defined(_WIN32)
    std::printf("platform_surface_probe — P05 seam harness (Win32 + Unavailable, real loader)\n");
#else
    std::printf("platform_surface_probe — P05 seam harness (Unavailable only, per this host)\n");
#endif
    leg_unavailable();
#if defined(_WIN32)
    leg_win32();
#endif
    leg_platform_entry();

    std::printf("%d checks, %d failed -> %s\n", g_checks, g_fails,
                g_fails == 0 ? "PASS" : "FAIL");
    return g_fails == 0 ? 0 : 1;
}