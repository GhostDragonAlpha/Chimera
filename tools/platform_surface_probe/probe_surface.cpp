// P05-R1 — standalone platform-seam probe (repair edition).
//
// P05 review round R1 corrected four truths in this harness:
//   (1) The R0 enumeration helper returned `const char*` pointing INTO a
//       buffer that died at return. It now returns OWNED VkExtensionProperties,
//       and a dedicated leg re-reads the names AFTER the helper has returned.
//   (2) The R0 "error" experiment deliberately violated Vulkan usage
//       requirements (it called the create on an instance that never enabled
//       VK_KHR_win32_surface). REPLACED by a controlled-failure test that
//       injects a substitute with the real PFN_vkCreateWin32SurfaceKHR
//       signature and asserts EXACT VkResult propagation. The real-loader
//       successful creation test is preserved separately (leg C).
//   (3) Windows includes/helpers are guarded (legs C, D) so the source is
//       portable to a Vulkan-enabled non-Windows host.
//   (4) The standalone target uses DISCOVERED Vulkan dependencies
//       (find_package), not a hard-coded SDK path (see CMakeLists.txt).
//
// Legs:
//   A  unavailable backend contract            (portable)
//   B  extension-name lifetime after return     (portable)
//   C  Win32Backend REAL LOADER success+teardown (Windows)
//   D  controlled failure: injected substitute   (Windows)
//   E  zero-arg platform entry point             (portable)
//
// Exit code 0 = all checks passed.

#include "platform/vulkan_surface.h"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <new>
#include <string>
#include <vector>

#if defined(_WIN32)
#include <windows.h>
#include <vulkan/vulkan_win32.h>            // VK_KHR_WIN32_SURFACE_EXTENSION_NAME literal
#include "platform/vulkan_surface_win32.h"  // the controlled-failure injection seam
#endif

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

// OWNED enumeration return (R1). The loader's extensionName pointers are only
// valid while the returned vector is alive — that is the documented contract;
// callers either keep it alive or copy out owned strings. A failed or
// VK_INCOMPLETE fill returns an EMPTY vector (buffer untrustworthy).
std::vector<VkExtensionProperties> enumerate_instance_extensions() {
    std::vector<VkExtensionProperties> exts;
    uint32_t cnt = 0;
    if (vkEnumerateInstanceExtensionProperties(nullptr, &cnt, nullptr) != VK_SUCCESS) return exts;
    try {
        exts.resize(cnt);
    } catch (const std::bad_alloc&) {
        return {};
    }
    if (vkEnumerateInstanceExtensionProperties(nullptr, &cnt, exts.data()) != VK_SUCCESS)
        exts.clear();   // includes VK_INCOMPLETE
    return exts;
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

void leg_extension_lifetime() {
    std::printf("[B] extension-name lifetime (owned return; reads AFTER the helper returned)\n");
    std::vector<std::string> owned;
    size_t read_while_alive = 0;
    {
        const auto exts = enumerate_instance_extensions();  // owned; dies at block end
        for (const auto& e : exts) {
            owned.emplace_back(e.extensionName);            // charset-copy into owned storage
            if (!owned.back().empty()) ++read_while_alive;
        }
    } // exts (and every loader-owned string) die HERE; `owned` must survive
    size_t read_after_return = 0;
    for (const auto& n : owned)
        if (!n.empty() && n.size() <= 1024) ++read_after_return;

    check(!owned.empty(), "lifetime: loader reported a non-empty extension list");
    check(read_while_alive == owned.size() && read_after_return == owned.size(),
          "lifetime: every owned name still readable AFTER the helper returned (no dangling)");
}

#if defined(_WIN32)

// File-scope flag for the non-capturing substitute below (a capturing lambda
// cannot convert to the REAL PFN_vkCreateWin32SurfaceKHR function pointer).
bool g_sub_called = false;

HWND make_probe_window() {
    static bool registered = false;
    const HINSTANCE h = GetModuleHandle(nullptr);
    if (h == nullptr) return nullptr;
    if (!registered) {
        WNDCLASSW wc{};
        wc.lpfnWndProc   = DefWindowProc;
        wc.hInstance     = h;
        wc.lpszClassName = L"chimera_probe_wnd";
        if (RegisterClassW(&wc) == 0) return nullptr;
        registered = true;
    }
    return CreateWindowW(L"chimera_probe_wnd", L"chimera_probe", WS_OVERLAPPEDWINDOW,
                         CW_USEDEFAULT, CW_USEDEFAULT, 320, 200, nullptr, nullptr, h, nullptr);
}

void leg_win32_real_loader() {
    std::printf("[C] Win32Backend REAL LOADER success + teardown (no injection active)\n");
    const plat::SurfaceExtensionSet s1 = plat::surface_instance_extensions(plat::Win32Backend{});
    check(s1.required, "extensions: required == true");
    check(!s1.blocked, "extensions: blocked == false (win32 surface present on this loader)");
    check(s1.count == 1, "extensions: count == 1");
    check(s1.names != nullptr, "extensions: names != nullptr");
    check(std::strcmp(s1.names[0], VK_KHR_WIN32_SURFACE_EXTENSION_NAME) == 0,
          "extensions: name == VK_KHR_win32_surface");

    bool present_in_loader = false;
    for (const auto& e : enumerate_instance_extensions())
        if (std::strcmp(e.extensionName, VK_KHR_WIN32_SURFACE_EXTENSION_NAME) == 0)
            present_in_loader = true;
    check(present_in_loader, "extensions: VK_KHR_win32_surface IS present in the loader list");
    check(s1.blocked == !present_in_loader, "extensions: blocked agrees with loader presence");

    // Pointer stability: names live in FIXED static storage.
    const plat::SurfaceExtensionSet s2 = plat::surface_instance_extensions(plat::Win32Backend{});
    check(s2.names == s1.names && s2.count == s1.count,
          "extensions: names pointer-stable across calls (static storage, no cache)");

    const char* const ext_names[] = {
        VK_KHR_SURFACE_EXTENSION_NAME,
        VK_KHR_WIN32_SURFACE_EXTENSION_NAME,
    };
    VkInstance inst = make_instance(ext_names, 2);
    check(inst != VK_NULL_HANDLE, "instance: created with the surface ext set");
    HWND hwnd = make_probe_window();
    check(hwnd != nullptr, "window: HWND created");

    if (inst != VK_NULL_HANDLE && hwnd != nullptr) {
        plat::SurfaceCreateOutcome o{};
        o.result  = VK_SUCCESS;
        o.surface = kSentinel;
        plat::create_surface(inst, static_cast<void*>(hwnd), o, plat::Win32Backend{});
        check(o.status == plat::SurfaceStatus::kCreated, "real-loader: kCreated");
        check(o.surface != nullptr, "real-loader: non-null surface");
        check(o.result == VK_SUCCESS, "real-loader: result == VK_SUCCESS");
        if (o.status == plat::SurfaceStatus::kCreated) {
            vkDestroySurfaceKHR(inst, o.surface, nullptr);  // engine teardown order
            check(true, "teardown: vkDestroySurfaceKHR executed cleanly");
        }
    } else {
        check(false, "real-loader create NOT RUN: prerequisite failed");
    }

    if (hwnd != nullptr) DestroyWindow(hwnd);
    if (inst != VK_NULL_HANDLE) vkDestroyInstance(inst, nullptr);
}

void leg_controlled_failure() {
    std::printf("[D] controlled failure: injected substitute propagates the EXACT VkResult\n");
    const char* const ext_names[] = {
        VK_KHR_SURFACE_EXTENSION_NAME,
        VK_KHR_WIN32_SURFACE_EXTENSION_NAME,
    };
    VkInstance inst = make_instance(ext_names, 2);
    HWND hwnd = make_probe_window();
    check(inst != VK_NULL_HANDLE && hwnd != nullptr, "D: real instance + window available");
    if (inst == VK_NULL_HANDLE || hwnd == nullptr) return;

    // Pre-inject: confirm the real loader creates on this exact instance
    // (keeps the success test independent from the injection below).
    {
        plat::SurfaceCreateOutcome o0{};
        o0.result  = VK_SUCCESS;
        o0.surface = kSentinel;
        plat::create_surface(inst, static_cast<void*>(hwnd), o0, plat::Win32Backend{});
        check(o0.status == plat::SurfaceStatus::kCreated && o0.surface != nullptr,
              "D pre-inject: real loader creates on this instance");
        if (o0.status == plat::SurfaceStatus::kCreated)
            vkDestroySurfaceKHR(inst, o0.surface, nullptr);
    }

    // Inject: a non-capturing substitute carrying the REAL
    // PFN_vkCreateWin32SurfaceKHR signature (it sets g_sub_called instead of
    // capturing scope). VK_ERROR_DEVICE_LOST is a value the real loader
    // cannot naturally return from win32 surface creation here, so the
    // equality below proves the result came through the injected path.
    g_sub_called = false;
    plat::win32_set_create_surface_override(
        [](VkInstance, const VkWin32SurfaceCreateInfoKHR*,
           const VkAllocationCallbacks*, VkSurfaceKHR* out) -> VkResult {
            g_sub_called = true;
            *out = VK_NULL_HANDLE;
            return VK_ERROR_DEVICE_LOST;
        });
    plat::SurfaceCreateOutcome o1{};
    o1.result  = VK_SUCCESS;
    o1.surface = kSentinel;
    plat::create_surface(inst, static_cast<void*>(hwnd), o1, plat::Win32Backend{});
    check(g_sub_called, "D: substitute was actually invoked (injection engaged)");
    check(o1.status == plat::SurfaceStatus::kFailed, "D: status == kFailed");
    check(o1.result == VK_ERROR_DEVICE_LOST, "D: EXACT injected VkResult propagated");
    check(o1.surface == kSentinel, "D: output handle untouched on failure");

    // Restore the loader path; the real loader must be back.
    plat::win32_set_create_surface_override(nullptr);
    plat::SurfaceCreateOutcome o2{};
    o2.result  = VK_SUCCESS;
    o2.surface = kSentinel;
    plat::create_surface(inst, static_cast<void*>(hwnd), o2, plat::Win32Backend{});
    check(o2.status == plat::SurfaceStatus::kCreated && o2.surface != nullptr,
          "D post-reset: real loader path restored");
    if (o2.status == plat::SurfaceStatus::kCreated)
        vkDestroySurfaceKHR(inst, o2.surface, nullptr);

    DestroyWindow(hwnd);
    vkDestroyInstance(inst, nullptr);
}
#endif // _WIN32

void leg_platform_entry() {
    std::printf("[E] zero-arg platform entry point\n");
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
    std::printf("platform_surface_probe — P05-R1 harness (Win32 + Unavailable, real loader + controlled injection)\n");
#else
    std::printf("platform_surface_probe — P05-R1 harness (Unavailable only, per this host)\n");
#endif
    leg_unavailable();
    leg_extension_lifetime();
#if defined(_WIN32)
    leg_win32_real_loader();
    leg_controlled_failure();
#endif
    leg_platform_entry();

    std::printf("%d checks, %d failed -> %s\n", g_checks, g_fails,
                g_fails == 0 ? "PASS" : "FAIL");
    return g_fails == 0 ? 0 : 1;
}