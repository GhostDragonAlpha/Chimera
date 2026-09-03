#include "engine.hpp"
#include <windows.h>
#include <vulkan/vulkan_win32.h>
#include <stdio.h>
#include <fstream>
#include <iostream>
#include <algorithm>
#include <cstring>
#include <cmath>
#include <vector>
#include <string>
#include <unordered_set>
#include <atomic>
#include <ctime>

// ── Minimal GLFW-free Win32 window helpers ─────────────────────────────────────────────

static const char* WINDOW_TITLE = "Chimera Engine";
static HWND g_hwnd = nullptr;

// ── Camera state (orbiting + user-controlled) ───────────────────────────────────────────
struct CameraState {
    float theta   = 0.0f;   // horizontal angle (radians)
    float phi     = 0.3f;   // vertical angle from horizon (-PI/2 .. PI/2)
    float radius  = 12.0f;
    float pan_x   = 0.0f;
    float pan_y   = 0.0f;
    float target[3] = {0.0f, 0.0f, 0.0f};
};
static CameraState g_cam;
static bool       g_mouse_captured = false;
static int        g_last_mx = 0, g_last_my = 0;
static bool       g_keys[256] = {};     // current frame key state
static Engine*    g_key_engine = nullptr;  // set in Engine::init so WndProc can reach pose toggles
// THE ENGINE STUDIO: ui.cpp's one-shot font upload needs the engine's queue + a
// command pool; init() publishes them here before ui_.init runs.
VkQueue       g_ui_queue    = VK_NULL_HANDLE;
VkCommandPool g_ui_cmd_pool = VK_NULL_HANDLE;
// B1: WndProc records a pending window resize; frame() consumes it and rebuilds the
// swapchain. Before this, WM_SIZE was never handled — resize() was dead code, and the
// first OUT_OF_DATE froze the window forever while the loop kept logging FPS.
static std::atomic<uint32_t> g_pending_resize_w{0};
static std::atomic<uint32_t> g_pending_resize_h{0};
// Bounding-sphere radius of the posted triangle mesh, measured at upload.
// The zoom floor: below 1.02x this radius the eye enters the mesh and the
// near plane SLICES it (operator report: "the nose and one hand are severed
// at the wall of deletion"). Derived from the geometry, never a constant.
static float      g_mesh_sphere = 0.0f;
static float radius_floor() { return fmaxf(1.0f, g_mesh_sphere * 1.02f); }
// THE PENUMBRA'S MEASURE (2026-09-03): the contact shadow's alpha falls with
// the occluder's height above the floor — real penumbrae widen with
// occluder-receiver distance, contact stays darkest. The reference height H0
// is DERIVED at load, not chosen: alpha reaches HALF its contact value at
// half the mesh's own y-extent (a half-body-height limb casts a half-strength
// shadow). Consumed by render_tri_shadow.vert via the UBO.
static float      g_mesh_ymin = 0.0f;
static float      g_mesh_ymax = 1.0f;

// Keyboard helper: wasd + qe + space/ctrl + r reset
static void update_camera_input(CameraState& cam, float dt) {
    // F1: the console captures the ENTIRE keyboard while open — typing a
    // command must never fly the camera (WASD/QE/space/ctrl/R all gated).
    if (g_key_engine && g_key_engine->ui_.console_open()) return;
    const float move_speed = 4.0f * dt;   // units/sec
    const float rot_speed  = 1.5f * dt;   // radians/sec
    const float zoom_speed = 8.0f * dt;   // units/sec

    // WASD → pan target in camera-local XY plane
    float dx = 0.0f, dy = 0.0f;
    if (g_keys['W'] || g_keys[VK_UP])    { dx -= sinf(cam.theta);    dy += cosf(cam.theta); }
    if (g_keys['S'] || g_keys[VK_DOWN])  { dx += sinf(cam.theta);    dy -= cosf(cam.theta); }
    if (g_keys['A'] || g_keys[VK_LEFT])  { dx -= cosf(cam.theta);    dy -= sinf(cam.theta); }
    if (g_keys['D'] || g_keys[VK_RIGHT]) { dx += cosf(cam.theta);    dy += sinf(cam.theta); }
    cam.target[0] += dx * move_speed;
    cam.target[2] += dy * move_speed;

    // Q/E → vertical movement
    if (g_keys['Q']) cam.target[1] -= move_speed;
    if (g_keys['E']) cam.target[1] += move_speed;

    // Space / Ctrl → zoom
    if (g_keys[' ']) cam.radius = fmaxf(radius_floor(), cam.radius - zoom_speed);
    if (g_keys[VK_CONTROL]) cam.radius = fminf(100.0f, cam.radius + zoom_speed);

    // Hold R → reset view (radius frames the whole mesh when one is loaded:
    // 45° FOV needs >= sphere/tan(22.5°) ≈ 2.41x; 2.7x leaves margin)
    if (g_keys['R']) {
        cam.theta   = 0.0f;
        cam.phi     = 0.3f;
        cam.radius  = fmaxf(12.0f, 2.7f * g_mesh_sphere);
        cam.pan_x   = 0.0f;
        cam.pan_y   = 0.0f;
        cam.target[0] = cam.target[1] = cam.target[2] = 0.0f;
    }
}

static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    if (msg == WM_CLOSE)  { DestroyWindow(hwnd); return 0; }
    if (msg == WM_DESTROY){ PostQuitMessage(0); return 0; }

    // B1: tell the render thread the window size changed (0x0 = minimized; frame()
    // skips the rebuild until a real extent arrives).
    if (msg == WM_SIZE) {
        g_pending_resize_w.store((uint32_t)LOWORD(lp));
        g_pending_resize_h.store((uint32_t)HIWORD(lp));
        return 0;
    }

    // Track key state for frame-by-frame polling
    if (msg == WM_KEYDOWN || msg == WM_SYSKEYDOWN) {
        g_keys[wp & 0xFF] = true;
        // F1 CONSOLE: ` toggles it (edge-triggered, overlay open or closed).
        // While open it captures the ENTIRE keyboard — the pose key, the F1
        // overlay toggle, and the camera poll (update_camera_input) are all
        // gated on it, so a typed command can never leak into the scene.
        bool con = g_key_engine && g_key_engine->ui_.console_open();
        if ((wp & 0xFF) == VK_OEM_3 && !(lp & 0x40000000) && g_key_engine) {
            g_key_engine->ui_.console_toggle();
            return 0;
        }
        if (con && g_key_engine) {
            // UP/DOWN recall history, ESCAPE closes — everything else waits
            // for WM_CHAR (shifted JSON punctuation types exactly)
            if ((wp & 0xFF) == VK_UP || (wp & 0xFF) == VK_DOWN || (wp & 0xFF) == VK_ESCAPE)
                g_key_engine->ui_.console_key(static_cast<int>(wp & 0xFF));
            return 0;
        }
        // 'P' toggles rest (slot 0) <-> wave (slot 1) on a skinned splat. Edge-triggered
        // (bit 30 of lParam = previous key state) so key autorepeat doesn't double-toggle.
        if ((wp & 0xFF) == 'P' && !(lp & 0x40000000) && g_key_engine) {
            g_key_engine->toggle_pose();
        }
        // F1: THE ENGINE STUDIO overlay (same edge-trigger law)
        if ((wp & 0xFF) == VK_F1 && !(lp & 0x40000000) && g_key_engine) {
            g_key_engine->ui_toggle();
        }
        // F2-F8: workspace shortcuts (G1 panel added 2026-09-02)
        if (!(lp & 0x40000000) && g_key_engine && g_key_engine->ui_.visible) {
            int wk = -1;
            if ((wp & 0xFF) == VK_F2) wk = 0;   // BOARD
            if ((wp & 0xFF) == VK_F3) wk = 4;   // SCENE
            if ((wp & 0xFF) == VK_F4) wk = 1;   // JOINTS
            if ((wp & 0xFF) == VK_F5) wk = 6;   // POSES
            if ((wp & 0xFF) == VK_F6) wk = 2;   // DOCS
            if ((wp & 0xFF) == VK_F7) wk = 3;   // LOG
            if ((wp & 0xFF) == VK_F8) wk = 5;   // CAPTURE
            if (wk >= 0) g_key_engine->ui_.set_left_mode(wk);
        }
    } else if (msg == WM_KEYUP || msg == WM_SYSKEYUP) {
        g_keys[wp & 0xFF] = false;
    }

    // F1 CONSOLE: printable input lands here (the console's own keyboard)
    if (msg == WM_CHAR && g_key_engine && g_key_engine->ui_.console_open()) {
        g_key_engine->ui_.console_char(static_cast<int>(wp));
        return 0;
    }

    // THE STUDIO: the UI always sees the cursor (panel hover/drag state), and a
    // press that lands on a panel is CONSUMED — it must never start a camera
    // orbit underneath (the Blender law: panels are not transparent to input).
    if (msg == WM_MOUSEMOVE && g_key_engine && g_key_engine->ui_.visible) {
        g_key_engine->ui_.on_mouse_move((int)(short)LOWORD(lp), (int)(short)HIWORD(lp));
    }
    if (msg == WM_LBUTTONDOWN && g_key_engine && g_key_engine->ui_.visible) {
        int mx = (int)(short)LOWORD(lp), my = (int)(short)HIWORD(lp);
        if (g_key_engine->ui_.on_lbutton(mx, my, true)) {
            if (g_key_engine->ui_.mouse_captured()) SetCapture(hwnd);  // border drag
            return 0;
        }
    }
    if (msg == WM_LBUTTONUP && g_key_engine && g_key_engine->ui_.visible) {
        if (g_key_engine->ui_.on_lbutton(0, 0, false)) { ReleaseCapture(); return 0; }
    }

    // Left-mouse drag → orbit rotation
    if (msg == WM_LBUTTONDOWN) {
        SetCapture(hwnd);
        g_mouse_captured = true;
        g_last_mx = (int)(short)LOWORD(lp);
        g_last_my = (int)(short)HIWORD(lp);
        return 0;
    }
    if (msg == WM_LBUTTONUP) {
        if (g_mouse_captured) { ReleaseCapture(); g_mouse_captured = false; }
        return 0;
    }
    if (msg == WM_MOUSEMOVE && g_mouse_captured) {
        int mx = (int)(short)LOWORD(lp), my = (int)(short)HIWORD(lp);
        float dm = static_cast<float>(mx - g_last_mx);
        float  dm_y = static_cast<float>(my - g_last_my);
        g_cam.theta -= dm * 0.005f;
        g_cam.phi   -= dm_y * 0.003f;   // drag UP -> camera UP (screen y grows downward)
        g_last_mx = mx;
        g_last_my = my;
        return 0;
    }

    // Right-mouse drag → pan
    if (msg == WM_RBUTTONDOWN) {
        SetCapture(hwnd);
        g_mouse_captured = true;
        g_last_mx = (int)(short)LOWORD(lp);
        g_last_my = (int)(short)HIWORD(lp);
        return 0;
    }
    if (msg == WM_RBUTTONUP) {
        if (g_mouse_captured) { ReleaseCapture(); g_mouse_captured = false; }
        return 0;
    }
    if (msg == WM_MOUSEMOVE && g_mouse_captured) {
        int mx = (int)(short)LOWORD(lp), my = (int)(short)HIWORD(lp);
        float dm = static_cast<float>(mx - g_last_mx);
        float  dm_y = static_cast<float>(my - g_last_my);
        // Pan in camera local XZ plane, scaled by radius
        g_cam.pan_x -= dm * 0.02f;
        g_cam.pan_y += dm_y * 0.02f;
        g_last_mx = mx;
        g_last_my = my;
        return 0;
    }

    // Scroll wheel → the docs browser when its dock is under the cursor (E1:
    // panels are not transparent to input), else camera zoom
    if (msg == WM_MOUSEWHEEL) {
        float delta = static_cast<float>(GET_WHEEL_DELTA_WPARAM(wp)) / 120.0f;
        if (g_key_engine && g_key_engine->ui_.visible) {
            POINT pt{ (int)(short)LOWORD(lp), (int)(short)HIWORD(lp) };   // wheel coords are SCREEN
            ScreenToClient(hwnd, &pt);
            if (g_key_engine->ui_.on_wheel(pt.x, pt.y, delta)) return 0;
        }
        g_cam.radius = fmaxf(radius_floor(), fminf(100.0f, g_cam.radius + delta * 2.0f));
        return 0;
    }

    return DefWindowProc(hwnd, msg, wp, lp);
}

static HWND create_window(uint32_t w, uint32_t h) {
    WNDCLASSEX wc{};
    wc.cbSize        = sizeof(wc);
    wc.style         = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc   = WndProc;
    wc.hInstance     = GetModuleHandle(nullptr);
    wc.lpszClassName = "ChimeraEngine";
    wc.hCursor       = LoadCursor(nullptr, IDC_ARROW);
    if (!RegisterClassEx(&wc)) return nullptr;

    RECT r = {0, 0, static_cast<LONG>(w), static_cast<LONG>(h)};
    AdjustWindowRect(&r, WS_OVERLAPPEDWINDOW | WS_CLIPSIBLINGS | WS_CLIPCHILDREN, FALSE);
    HWND hwnd = CreateWindowEx(0, "ChimeraEngine", WINDOW_TITLE,
                               WS_OVERLAPPEDWINDOW | WS_CLIPSIBLINGS | WS_CLIPCHILDREN,
                               CW_USEDEFAULT, CW_USEDEFAULT,
                               r.right - r.left, r.bottom - r.top,
                               nullptr, nullptr, wc.hInstance, nullptr);
    if (!hwnd) return nullptr;
    ShowWindow(hwnd, SW_SHOW);
    UpdateWindow(hwnd);
    g_hwnd = hwnd;
    return hwnd;
}

// ── SPIR-V loader ────────────────────────────────────────────────────────────────────────

static std::vector<char> read_file(const char* path) {
    std::ifstream f(path, std::ios::ate | std::ios::binary);
    if (!f.is_open()) return {};
    auto size = f.tellg();
    std::vector<char> buf(static_cast<size_t>(size));
    f.seekg(0); f.read(buf.data(), static_cast<std::streamsize>(size));
    return buf;
}

static VkShaderModule create_shader_module(VkDevice dev, const std::vector<char>& spirv) {
    VkShaderModuleCreateInfo info{};
    info.sType           = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    info.codeSize        = spirv.size();
    info.pCode           = reinterpret_cast<const uint32_t*>(spirv.data());
    VkShaderModule mod;
    if (vkCreateShaderModule(dev, &info, nullptr, &mod) != VK_SUCCESS) return VK_NULL_HANDLE;
    return mod;
}

// ── Vulkan helper: validation layers ─────────────────────────────────────────────────────

static bool check_extension(const std::vector<VkExtensionProperties>& avail, const char* name) {
    for (auto& e : avail) if (strcmp(e.extensionName, name) == 0) return true;
    return false;
}

static VkPhysicalDevice pick_physical_device(VkInstance inst) {
    uint32_t count = 0;
    vkEnumeratePhysicalDevices(inst, &count, nullptr);
    if (count == 0) return VK_NULL_HANDLE;
    std::vector<VkPhysicalDevice> devs(count);
    vkEnumeratePhysicalDevices(inst, &count, devs.data());

    // Prefer discrete GPU
    VkPhysicalDevice best = VK_NULL_HANDLE;
    int best_score = -1;
    for (auto d : devs) {
        VkPhysicalDeviceProperties props{};
        vkGetPhysicalDeviceProperties(d, &props);
        int score = (props.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) ? 10 : 0;
        // Require float32 blend operations for alpha blending
        VkPhysicalDeviceFeatures feats{};
        vkGetPhysicalDeviceFeatures(d, &feats);
        if (!feats.fillModeNonSolid) score -= 5;
        if (score > best_score) { best_score = score; best = d; }
    }
    return best != VK_NULL_HANDLE ? best : devs[0];
}

// ── Queue family finder ──────────────────────────────────────────────────────────────────

struct QueueFamilies {
    uint32_t graphics = UINT32_MAX;
    uint32_t compute  = UINT32_MAX;
    uint32_t transfer = UINT32_MAX;
    bool complete() const { return graphics != UINT32_MAX && compute != UINT32_MAX && transfer != UINT32_MAX; }
};

static QueueFamilies find_queue_families(VkPhysicalDevice phys) {
    QueueFamilies qf{};
    uint32_t count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(phys, &count, nullptr);
    std::vector<VkQueueFamilyProperties> families(count);
    vkGetPhysicalDeviceQueueFamilyProperties(phys, &count, families.data());

    for (uint32_t i = 0; i < count; ++i) {
        if (families[i].queueFlags & VK_QUEUE_GRAPHICS_BIT && qf.graphics == UINT32_MAX)
            qf.graphics = i;
        if (families[i].queueFlags & VK_QUEUE_COMPUTE_BIT && qf.compute == UINT32_MAX)
            qf.compute = i;
        if (families[i].queueFlags & VK_QUEUE_TRANSFER_BIT && qf.transfer == UINT32_MAX)
            qf.transfer = i;
    }
    // Try to share graphics and compute queues
    if (qf.graphics != UINT32_MAX && (families[qf.graphics].queueFlags & VK_QUEUE_COMPUTE_BIT))
        qf.compute = qf.graphics;
    if (qf.graphics != UINT32_MAX && (families[qf.graphics].queueFlags & VK_QUEUE_TRANSFER_BIT))
        qf.transfer = qf.graphics;
    return qf;
}

// ── Surface extension name ───────────────────────────────────────────────────────────────

static const char* EXTENSIONS[] = {
    VK_KHR_SWAPCHAIN_EXTENSION_NAME,
#ifdef VK_ENABLE_BETA_EXTENSIONS
    // VK_KHR_portability_subset is optional; we skip it for now
#endif
};

// ── Debug messenger (validation layers) ──────────────────────────────────────────────
static VKAPI_ATTR VkBool32 VKAPI_CALL debug_utils_callback(
    VkDebugUtilsMessageSeverityFlagBitsEXT severity,
    VkDebugUtilsMessageTypeFlagsEXT,
    const VkDebugUtilsMessengerCallbackDataEXT* data, void*) {
    if (severity >= VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT) {
        fprintf(stderr, "[VK %s] %s\n",
                severity >= VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT ? "ERROR" : "WARN",
                data->pMessage);
    }
    return VK_FALSE;
}
// ── Engine implementation ────────────────────────────────────────────────────────────────

static const uint32_t MAX_FRAMES_IN_FLIGHT = 2;

bool Engine::init(const EngineConfig& cfg) {
    cfg_ = cfg;
    g_key_engine = this;   // WndProc ('P' pose toggle) reaches the engine through this

    // ── F4: the recorder opens the session log FIRST — before any covered state
    //    change can happen, so no event can ever precede the file that records it.
    {
        char name[64];
        std::time_t now = std::time(nullptr);
        std::tm tmv{}; localtime_s(&tmv, &now);
        snprintf(name, sizeof(name), "session_%04d%02d%02d_%02d%02d%02d.jsonl",
                 tmv.tm_year + 1900, tmv.tm_mon + 1, tmv.tm_mday,
                 tmv.tm_hour, tmv.tm_min, tmv.tm_sec);
        log_file_ = name;
        log_fp_ = fopen(name, "ab");
        if (!log_fp_) {
            fprintf(stderr, "studio: cannot open session log %s — recorder offline\n", name);
            log_file_.clear();
        } else {
            printf("studio: session log -> %s\n", name);
        }
        ui_.log_file_ = log_file_;
    }

    // ── 1. Win32 window ──────────────────────────────────────────────────────────────
    if (!create_window(cfg.width, cfg.height)) {
        fprintf(stderr, "Failed to create window\n");
        return false;
    }

    // ── 2. Vulkan instance ───────────────────────────────────────────────────────────
    VkApplicationInfo app{};
    app.sType              = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app.pApplicationName   = "Chimera Engine";
    app.applicationVersion = VK_MAKE_VERSION(1, 0, 0);
    app.pEngineName        = "Chimera";
    app.engineVersion      = VK_MAKE_VERSION(1, 0, 0);
    app.apiVersion         = VK_API_VERSION_1_2;

    VkInstanceCreateInfo info{};
    info.sType               = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    info.pApplicationInfo    = &app;

    // Get required extensions
    std::vector<const char*> instance_extensions;
    // Always need surface: VK_KHR_win32_surface (if present) + VK_KHR_surface.
    // NOTE: use the STRING LITERAL macro, not a pointer into a local enumeration vector --
    // a pointer into `exts` dangles once that block's vector is destroyed (a use-after-scope
    // that made vkCreateInstance read garbage and return VK_ERROR_EXTENSION_NOT_PRESENT).
    bool has_win32_surface = false;
    {
        uint32_t cnt = 0;
        vkEnumerateInstanceExtensionProperties(nullptr, &cnt, nullptr);
        std::vector<VkExtensionProperties> exts(cnt);
        vkEnumerateInstanceExtensionProperties(nullptr, &cnt, exts.data());
        for (auto& e : exts) {
            if (strcmp(e.extensionName, VK_KHR_WIN32_SURFACE_EXTENSION_NAME) == 0) {
                has_win32_surface = true;
                break;
            }
        }
    }
    if (has_win32_surface) instance_extensions.push_back(VK_KHR_WIN32_SURFACE_EXTENSION_NAME);
    else { fprintf(stderr, "VK_KHR_win32_surface not available\n"); return false; }
    instance_extensions.push_back(VK_KHR_SURFACE_EXTENSION_NAME);

    // Try to enable validation layers (development) + debug utils messenger
    uint32_t layer_count = 0;
    vkEnumerateInstanceLayerProperties(&layer_count, nullptr);
    std::vector<VkLayerProperties> layers(layer_count);
    vkEnumerateInstanceLayerProperties(&layer_count, layers.data());
    const char* validation_layer = nullptr;
    for (auto& l : layers) {
        if (strcmp(l.layerName, "VK_LAYER_KHRONOS_validation") == 0) {
            validation_layer = "VK_LAYER_KHRONOS_validation"; break;
        }
    }

    bool has_debug_utils = false;
    {
        uint32_t cnt = 0;
        vkEnumerateInstanceExtensionProperties(nullptr, &cnt, nullptr);
        std::vector<VkExtensionProperties> exts(cnt);
        vkEnumerateInstanceExtensionProperties(nullptr, &cnt, exts.data());
        for (auto& e : exts)
            if (strcmp(e.extensionName, VK_EXT_DEBUG_UTILS_EXTENSION_NAME) == 0) { has_debug_utils = true; break; }
    }
    if (has_debug_utils) instance_extensions.push_back(VK_EXT_DEBUG_UTILS_EXTENSION_NAME);

    info.ppEnabledExtensionNames = instance_extensions.data();
    info.enabledExtensionCount   = static_cast<uint32_t>(instance_extensions.size());
    info.enabledLayerCount       = validation_layer ? 1u : 0u;
    info.ppEnabledLayerNames     = validation_layer ? &validation_layer : nullptr;

    VkResult inst_res = vkCreateInstance(&info, nullptr, &instance_);
    if (inst_res != VK_SUCCESS) {
        fprintf(stderr, "Failed to create Vulkan instance (VkResult=%d)\n", (int)inst_res);
        return false;
    }

    // Set up the debug messenger (stored so shutdown can destroy it — B2: it was
    // created into a local and leaked into instance teardown; validation fired
    // on every exit).
    if (has_debug_utils) {
        auto pfn = (PFN_vkCreateDebugUtilsMessengerEXT)
            vkGetInstanceProcAddr(instance_, "vkCreateDebugUtilsMessengerEXT");
        if (pfn) {
            VkDebugUtilsMessengerCreateInfoEXT dci{};
            dci.sType = VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT;
            dci.messageSeverity = VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT |
                                  VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT;
            dci.messageType = VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT |
                              VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT |
                              VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT;
            dci.pfnUserCallback = debug_utils_callback;
            pfn(instance_, &dci, nullptr, &debug_messenger_);
        }
    }

    // ── 3. Surface ───────────────────────────────────────────────────────────────────
    VkWin32SurfaceCreateInfoKHR surface_info{};
    surface_info.sType         = VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR;
    surface_info.hwnd          = g_hwnd;
    surface_info.hinstance     = GetModuleHandle(nullptr);
    VkResult surf_res = vkCreateWin32SurfaceKHR(instance_, &surface_info, nullptr, &surface_);
    if (surf_res != VK_SUCCESS) {
        fprintf(stderr, "Failed to create Win32 surface (VkResult=%d)\n", (int)surf_res);
        return false;
    }


    // ── 4. Physical device ───────────────────────────────────────────────────────────
    phys_dev_ = pick_physical_device(instance_);
    if (phys_dev_ == VK_NULL_HANDLE) {
        fprintf(stderr, "Failed to find Vulkan physical device\n");
        return false;
    }
    // F2: the status bar names the GPU it runs on — the device's OWN name
    {
        VkPhysicalDeviceProperties dprops{};
        vkGetPhysicalDeviceProperties(phys_dev_, &dprops);
        ui_.set_gpu_name(dprops.deviceName);
    }

    // ── 5. Queue families ────────────────────────────────────────────────────────────
    QueueFamilies qf = find_queue_families(phys_dev_);
    if (!qf.complete()) {
        fprintf(stderr, "Failed to find suitable queue families\n");
        return false;
    }

    // Check surface compatibility
    uint32_t format_count = 0;
    vkGetPhysicalDeviceSurfaceFormatsKHR(phys_dev_, surface_, &format_count, nullptr);
    if (format_count == 0) { fprintf(stderr, "No surface formats\n"); return false; }

    // ── 6. Logical device ────────────────────────────────────────────────────────────
    float queue_priority = 1.0f;
    std::vector<VkDeviceQueueCreateInfo> queue_creates;
    std::unordered_set<uint32_t> unique_families = {qf.graphics, qf.compute, qf.transfer};
    for (uint32_t family : unique_families) {
        VkDeviceQueueCreateInfo qi{};
        qi.sType           = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
        qi.queueFamilyIndex = family;
        qi.queueCount      = 1;
        qi.pQueuePriorities = &queue_priority;
        queue_creates.push_back(qi);
    }

    VkPhysicalDeviceFeatures features{};
    features.fillModeNonSolid = VK_TRUE;  // needed for wireframe debugging
    features.shaderFloat64 = VK_TRUE;     // the water solver's float math must
                                          // match the CPU reference's float64
                                          // bit-for-bit (RTX 4090 supports it)
    features.shaderInt64 = VK_TRUE;       // H9 frost decode: the integer MLP's
                                          // fixed-point rescale path (RTX 4090)
    features.geometryShader = VK_TRUE;    // H9 frost display: gl_PrimitiveID in
                                          // the fragment shader pulls Geometry

    VkDeviceCreateInfo device_info{};
    device_info.sType                     = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    device_info.queueCreateInfoCount      = static_cast<uint32_t>(queue_creates.size());
    device_info.pQueueCreateInfos         = queue_creates.data();
    device_info.pEnabledFeatures          = &features;

    // Required device extensions
    std::vector<const char*> device_exts = {
        VK_KHR_SWAPCHAIN_EXTENSION_NAME,
#ifdef VK_KHR_DEFERRED_HOST_OPERATIONS_EXTENSION_NAME
        VK_KHR_DEFERRED_HOST_OPERATIONS_EXTENSION_NAME,
#endif
    };
    device_info.ppEnabledExtensionNames = device_exts.data();
    device_info.enabledExtensionCount   = static_cast<uint32_t>(device_exts.size());

    VkResult dev_res = vkCreateDevice(phys_dev_, &device_info, nullptr, &device_);
    if (dev_res != VK_SUCCESS) {
        fprintf(stderr, "Failed to create Vulkan device (VkResult=%d)\n", (int)dev_res);
        return false;
    }


    vkGetDeviceQueue(device_, qf.graphics, 0, &queue_);

    // ── 7. Command pool ───────────────────────────────────────────────────────────────
    {
        VkCommandPoolCreateInfo pci{};
        pci.sType         = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
        pci.queueFamilyIndex = qf.graphics;
        pci.flags         = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        vkCreateCommandPool(device_, &pci, nullptr, &cmd_pool_);
    }

    // ── 8. Swapchain ─────────────────────────────────────────────────────────────────
    if (!create_swapchain()) return false;


    // ── 8. Render pass ───────────────────────────────────────────────────────────────
    if (!create_render_pass()) return false;


    // ── 8.5 Depth buffer + framebuffers + command buffers + offscreen target ─────
    create_depth_resources();
    if (!create_framebuffers()) return false;
    if (!create_command_buffers()) return false;
    create_offscreen();


    // ── 9. Shaders ───────────────────────────────────────────────────────────────────
    if (!compile_shaders()) return false;


    // ── 10. Descriptor sets (layout first — the pipeline layout references it) ────────
    if (!create_descriptor_sets()) return false;


    // ── 11. Pipeline ─────────────────────────────────────────────────────────────────
    if (!create_pipeline()) return false;
    if (!create_triangle_pipeline()) return false;


    // ── 12. Compute pipeline ───────────────────────────────────────────────────────
    if (!create_compute_pipeline()) return false;

    // ── 12.5 GPU radix sort (back-to-front splat ordering) ──────────────────────────
    if (!create_sort_pipeline()) return false;

    // ── 12.6 GPU skinning (LBS pose over the splats) ────────────────────────────────
    if (!create_skin_pipeline()) return false;

    // ── 12.7 THE ENGINE STUDIO (the overlay: font atlas, UI pipeline, framebuffers) ──
    // Non-fatal by design: a UI failure must never take the renderer down with it.
    {
        g_ui_queue = queue_;
        g_ui_cmd_pool = cmd_pool_;
        uint32_t host_mt = find_mem_type(~0u, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                                                VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        if (ui_.init(device_, phys_dev_, swap_fmt_, extent_.width, extent_.height, host_mt)) {
            ui_.create_swap_resources(img_views_, extent_);
            // D1: the timeline panel issues intents; the engine owns the clock.
            ui_.cb_play_toggle_ = [this] {
                bool np = !show_playing_.load();
                show_playing_.store(np);
                if (np) joints_owner_.store(0);   // C1: play hands the pose back to the show
            };
            ui_.cb_step_ = [this](int n) {
                double t = show_time_.load() + n / 240.0;   // exactly one 240fps frame
                show_scrub_.store(t < 0.0 ? 0.0 : t);
            };
            ui_.cb_speed_cycle_ = [this] {
                double s = show_speed_.load();
                s = (s < 0.5) ? 0.5 : (s < 1.0) ? 1.0 : (s < 2.0) ? 2.0 : (s < 4.0) ? 4.0 : 0.25;
                show_speed_.store(s);
            };
            ui_.cb_scrub_ = [this](double t) { show_scrub_.store(t < 0.0 ? 0.0 : t); };
            // TIMELINE KEY MARKS: a diamond click scrubs to the pose; the
            // KEY button keys the live clock time (auto-name keyN, as the
            // camera's save auto-names camN).
            ui_.cb_key_recall_ = [this](int i) {
                std::vector<std::pair<std::string, double>> ks = key_marks_list();
                if (i < 0 || i >= static_cast<int>(ks.size())) return;
                show_scrub_.store(ks[i].second < 0.0 ? 0.0 : ks[i].second);
            };
            ui_.cb_dope_key_recall_ = [this](int i) {
                std::vector<KeyMarkInfo> keys = key_marks_list_info();
                if (i < 0 || i >= static_cast<int>(keys.size())) return;
                const KeyMarkInfo& key = keys[static_cast<size_t>(i)];
                selected_joint_.store(key.joint.empty() ? -1 : joint_index(key.joint),
                                      std::memory_order_relaxed);
                show_scrub_.store(key.t < 0.0 ? 0.0 : key.t, std::memory_order_relaxed);
            };
            ui_.cb_key_save_ = [this] {
                int sel = selected_joint_.load(std::memory_order_relaxed);
                std::string jn = (sel >= 0 && sel < static_cast<int>(j_names_.size())) ? j_names_[sel] : std::string();
                key_mark_save(std::string(), jn);
            };
            ui_.cb_key_delete_ = [this](int i) {
                std::vector<std::pair<std::string, double>> ks = key_marks_list();
                if (i >= 0 && i < static_cast<int>(ks.size())) {
                    key_mark_delete(ks[i].first);
                }
            };
            ui_.cb_key_clear_ = [this] { key_marks_clear(); };
            ui_.cb_rig_toggle_ = [this] {
                set_rig_overlay(!rig_overlay_on());
            };
            // C1: the joints editor's intents — select (gizmo + paint target)
            // toggles; a theta intent is an ownership claim (editor takes the pose).
            ui_.cb_joint_select_ = [this](int idx) {
                selected_joint_.store(selected_joint_.load() == idx ? -1 : idx);
            };
            ui_.cb_joint_theta_ = [this](int idx, float deg) { request_joint_edit(idx, deg); };
            // F1: the console issues request lines; the engine's worker owns
            // execution through the SAME handler main wires to the HTTP server
            ui_.cb_console_ = [this](const std::string& line) { console_exec(line); };
            // C4: the outliner's row toggles — rebuilt from FRESH state at click
            // time (never the pushed view), routed through the console's one path
            ui_.cb_scene_toggle_ = [this](int row) { scene_toggle(row); };
            // C2: selecting a row is pure view state — re-click deselects
            ui_.cb_scene_select_ = [this](int row) {
                inspect_row_.store(inspect_row_.load() == row ? -1 : row);
            };
            // D6: camera bookmarks — the glass path runs ON the render thread
            // (ui clicks land there), so recall/save apply directly; the HTTP
            // path goes through the membrane request. Both end in the same
            // set_camera_full / cam_mark_save.
            cam_marks_load();
            key_marks_load();
            ui_.cb_cam_recall_ = [this](int i) {
                std::vector<std::string> names = cam_mark_names();
                if (i < 0 || i >= static_cast<int>(names.size())) return;
                float v[8];
                if (cam_mark_get(names[i], v)) set_camera_full(v);
            };
            ui_.cb_cam_save_ = [this] { cam_mark_save(""); };
            console_thread_ = std::thread([this] { console_worker(); });
            printf("THE ENGINE STUDIO: overlay ready (F1)\n");
        } else {
            fprintf(stderr, "studio: overlay init failed — continuing without UI\n");
        }
    }


    // ── 13. Buffers (will be resized in push_state) ──────────────────────────────────
    // pos_buf_, vel_buf_, acc_buf_ are created lazily on first push_state

    // ── 13. Sync objects ─────────────────────────────────────────────────────────────
    draw_sem_.resize(MAX_FRAMES_IN_FLIGHT);
    flush_sem_.resize(MAX_FRAMES_IN_FLIGHT);
    fences_.resize(MAX_FRAMES_IN_FLIGHT);
    for (uint32_t i = 0; i < MAX_FRAMES_IN_FLIGHT; ++i) {
        VkSemaphoreCreateInfo si{};
        si.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
        vkCreateSemaphore(device_, &si, nullptr, &draw_sem_[i]);
        vkCreateSemaphore(device_, &si, nullptr, &flush_sem_[i]);

        VkFenceCreateInfo fi{};
        fi.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
        fi.flags = VK_FENCE_CREATE_SIGNALED_BIT;  // start signaled so first wait passes
        vkCreateFence(device_, &fi, nullptr, &fences_[i]);
    }

    printf("Vulkan engine initialized: %u x %u, %u frames in flight\n",
           cfg.width, cfg.height, MAX_FRAMES_IN_FLIGHT);
    return true;
}

void Engine::shutdown() {
    // F1: stop the console worker first — it may be inside the api handler,
    // so give it the device-idle barrier before joining
    {
        std::lock_guard<std::mutex> lk(console_m_);
        console_stop_ = true;
    }
    {
        std::lock_guard<std::mutex> lk(console_ui_m_);
        console_ui_stop_ = true;
        console_ui_done_ = true;
    }
    {
        std::lock_guard<std::mutex> lk(doc_request_m_);
        doc_request_stop_ = true;
        doc_request_done_ = true;
    }
    console_cv_.notify_all();
    console_ui_cv_.notify_all();
    doc_request_cv_.notify_all();
    if (console_thread_.joinable()) console_thread_.join();

    // F4: the recorder outlives every event source; the file closes LAST among
    // the teardown's early steps, after the worker that could still log joins.
    {
        std::lock_guard<std::mutex> lk(log_m_);
        if (log_fp_) { fflush(log_fp_); fclose(log_fp_); log_fp_ = nullptr; }
    }

    vkDeviceWaitIdle(device_);

    ui_.shutdown();   // THE STUDIO: before any pool/device teardown
    if (cmd_pool_)    vkDestroyCommandPool(device_, cmd_pool_,   nullptr);
    destroy_depth_resources();
    if (rt_framebuffer_) vkDestroyFramebuffer(device_, rt_framebuffer_, nullptr);
    if (rt_render_pass_) vkDestroyRenderPass(device_, rt_render_pass_, nullptr);
    if (rt_view_)     vkDestroyImageView(device_, rt_view_,      nullptr);
    if (rt_mem_)      vkFreeMemory(device_,  rt_mem_,            nullptr);
    if (rt_image_)    vkDestroyImage(device_,  rt_image_,        nullptr);

    for (auto f : frames_) vkDestroyFramebuffer(device_, f, nullptr);
    for (auto v : img_views_) vkDestroyImageView(device_, v, nullptr);
    if (swapchain_) vkDestroySwapchainKHR(device_, swapchain_, nullptr);

    if (pos_buf_)  { vkDestroyBuffer(device_, pos_buf_,  nullptr);  vkFreeMemory(device_, pos_mem_,  nullptr); }
    if (vel_buf_)  { vkDestroyBuffer(device_, vel_buf_,  nullptr);  vkFreeMemory(device_, vel_mem_,  nullptr); }
    if (acc_buf_)  { vkDestroyBuffer(device_, acc_buf_,  nullptr);  vkFreeMemory(device_, acc_mem_,  nullptr); }
    if (img_buf_)  { vkDestroyBuffer(device_, img_buf_,  nullptr);  vkFreeMemory(device_, img_mem_,  nullptr); }
    if (params_buf_)   { vkDestroyBuffer(device_, params_buf_,   nullptr); vkFreeMemory(device_, params_mem_,   nullptr); }
    for (int k = 0; k < 2; ++k) {
        if (params_ubo_[k]) {
            if (params_umap_[k]) vkUnmapMemory(device_, params_umem_[k]);
            vkDestroyBuffer(device_, params_ubo_[k], nullptr);
            vkFreeMemory(device_, params_umem_[k], nullptr);
            params_ubo_[k] = VK_NULL_HANDLE; params_umap_[k] = nullptr;
        }
    }
    if (comp_params_buf_) { vkDestroyBuffer(device_, comp_params_buf_, nullptr); vkFreeMemory(device_, comp_params_mem_, nullptr); }
    if (capture_staging_) { vkDestroyBuffer(device_, capture_staging_, nullptr); vkFreeMemory(device_, capture_staging_mem_, nullptr); }
    if (glass_staging_)   { vkDestroyBuffer(device_, glass_staging_, nullptr);   vkFreeMemory(device_, glass_staging_mem_, nullptr); }
    destroy_sort_resources();
    destroy_skin_resources();
    destroy_triangle_resources();

    if (compute_desc_pool_)     vkDestroyDescriptorPool(device_,     compute_desc_pool_,      nullptr);
    if (compute_desc_layout_)   vkDestroyDescriptorSetLayout(device_, compute_desc_layout_,   nullptr);
    if (compute_pipeline_layout_) vkDestroyPipelineLayout(device_, compute_pipeline_layout_, nullptr);
    if (compute_pipeline_)      vkDestroyPipeline(device_,          compute_pipeline_,      nullptr);

    // hinge kernel resources
    if (hinge_pipe_)        vkDestroyPipeline(device_, hinge_pipe_, nullptr);
    if (hinge_layout_)      vkDestroyPipelineLayout(device_, hinge_layout_, nullptr);
    if (hinge_desc_layout_) vkDestroyDescriptorSetLayout(device_, hinge_desc_layout_, nullptr);
    if (hinge_desc_pool_)   vkDestroyDescriptorPool(device_, hinge_desc_pool_, nullptr);
    if (hinge_mod_)         vkDestroyShaderModule(device_, hinge_mod_, nullptr);
    if (hinge_rest_buf_)  { vkDestroyBuffer(device_, hinge_rest_buf_, nullptr); vkFreeMemory(device_, hinge_rest_mem_, nullptr); }
    if (hinge_wL_buf_)    { vkDestroyBuffer(device_, hinge_wL_buf_, nullptr);   vkFreeMemory(device_, hinge_wL_mem_, nullptr); }
    if (hinge_wR_buf_)    { vkDestroyBuffer(device_, hinge_wR_buf_, nullptr);   vkFreeMemory(device_, hinge_wR_mem_, nullptr); }
    // volp-ARAP kernel resources (H13)
    if (volp_pipe_)        vkDestroyPipeline(device_, volp_pipe_, nullptr);
    if (volp_layout_)      vkDestroyPipelineLayout(device_, volp_layout_, nullptr);
    if (volp_desc_layout_) vkDestroyDescriptorSetLayout(device_, volp_desc_layout_, nullptr);
    if (volp_desc_pool_)   vkDestroyDescriptorPool(device_, volp_desc_pool_, nullptr);
    if (volp_mod_)         vkDestroyShaderModule(device_, volp_mod_, nullptr);
    if (volp_stats_map_)   vkUnmapMemory(device_, volp_st_mem_);
    if (volp_hdr_buf_)   { vkDestroyBuffer(device_, volp_hdr_buf_, nullptr); vkFreeMemory(device_, volp_hdr_mem_, nullptr); }
    if (volp_u_buf_)     { vkDestroyBuffer(device_, volp_u_buf_, nullptr);   vkFreeMemory(device_, volp_u_mem_, nullptr); }
    if (volp_f_buf_)     { vkDestroyBuffer(device_, volp_f_buf_, nullptr);   vkFreeMemory(device_, volp_f_mem_, nullptr); }
    if (volp_x_buf_)     { vkDestroyBuffer(device_, volp_x_buf_, nullptr);   vkFreeMemory(device_, volp_x_mem_, nullptr); }
    if (volp_sc_buf_)    { vkDestroyBuffer(device_, volp_sc_buf_, nullptr);  vkFreeMemory(device_, volp_sc_mem_, nullptr); }
    if (volp_st_buf_)    { vkDestroyBuffer(device_, volp_st_buf_, nullptr);  vkFreeMemory(device_, volp_st_mem_, nullptr); }
    if (volp_rb_buf_)    { vkDestroyBuffer(device_, volp_rb_buf_, nullptr);  vkFreeMemory(device_, volp_rb_mem_, nullptr); }

    // gait CPG resources
    if (gait_pipe_)        vkDestroyPipeline(device_, gait_pipe_, nullptr);
    if (gait_layout_)      vkDestroyPipelineLayout(device_, gait_layout_, nullptr);
    if (gait_desc_layout_) vkDestroyDescriptorSetLayout(device_, gait_desc_layout_, nullptr);
    if (gait_desc_pool_)   vkDestroyDescriptorPool(device_, gait_desc_pool_, nullptr);
    if (gait_mod_)         vkDestroyShaderModule(device_, gait_mod_, nullptr);
    if (gait_consts_buf_) { vkDestroyBuffer(device_, gait_consts_buf_, nullptr); vkFreeMemory(device_, gait_consts_mem_, nullptr); }
    if (gait_edges_buf_)  { vkDestroyBuffer(device_, gait_edges_buf_, nullptr);  vkFreeMemory(device_, gait_edges_mem_, nullptr); }
    if (gait_phase_buf_)  { vkDestroyBuffer(device_, gait_phase_buf_, nullptr);  vkFreeMemory(device_, gait_phase_mem_, nullptr); }
    if (gait_ring_buf_)   { vkDestroyBuffer(device_, gait_ring_buf_, nullptr);   vkFreeMemory(device_, gait_ring_mem_, nullptr); }
    if (gait_theta_buf_)  { if (gait_theta_map_) vkUnmapMemory(device_, gait_theta_mem_);
                            vkDestroyBuffer(device_, gait_theta_buf_, nullptr);  vkFreeMemory(device_, gait_theta_mem_, nullptr); }
    if (gait_ring_rb_buf_){ if (gait_ring_rb_map_) vkUnmapMemory(device_, gait_ring_rb_mem_);
                            vkDestroyBuffer(device_, gait_ring_rb_buf_, nullptr);vkFreeMemory(device_, gait_ring_rb_mem_, nullptr); }

    if (desc_pool_)  vkDestroyDescriptorPool(device_, desc_pool_, nullptr);
    if (desc_layout_) vkDestroyDescriptorSetLayout(device_, desc_layout_, nullptr);

    if (pipeline_)  vkDestroyPipeline(device_, pipeline_,  nullptr);
    if (pipeline_layout_) vkDestroyPipelineLayout(device_, pipeline_layout_, nullptr);  // B2: was leaked
    if (render_pass_) vkDestroyRenderPass(device_, render_pass_, nullptr);

    if (comp_mod_) vkDestroyShaderModule(device_, comp_mod_, nullptr);
    if (vert_mod_) vkDestroyShaderModule(device_, vert_mod_, nullptr);
    if (frag_mod_) vkDestroyShaderModule(device_, frag_mod_, nullptr);

    for (auto s : draw_sem_)  vkDestroySemaphore(device_, s,  nullptr);
    for (auto s : flush_sem_) vkDestroySemaphore(device_, s,  nullptr);
    for (auto f : fences_)    vkDestroyFence(device_,   f,    nullptr);

    if (surface_)  vkDestroySurfaceKHR(instance_, surface_,  nullptr);
    if (device_)   vkDestroyDevice(device_,                  nullptr);
    // B2: the messenger must die BEFORE the instance, or validation fires at exit.
    if (debug_messenger_) {
        auto pfn = (PFN_vkDestroyDebugUtilsMessengerEXT)
            vkGetInstanceProcAddr(instance_, "vkDestroyDebugUtilsMessengerEXT");
        if (pfn) pfn(instance_, debug_messenger_, nullptr);
        debug_messenger_ = VK_NULL_HANDLE;
    }
    if (instance_) vkDestroyInstance(instance_,              nullptr);

    if (g_hwnd) { DestroyWindow(g_hwnd); g_hwnd = nullptr; }
    printf("Vulkan engine shut down\n");
}

bool Engine::create_swapchain() {
    // Query surface capabilities
    VkSurfaceCapabilitiesKHR caps{};
    vkGetPhysicalDeviceSurfaceCapabilitiesKHR(phys_dev_, surface_, &caps);

    uint32_t format_count = 0;
    vkGetPhysicalDeviceSurfaceFormatsKHR(phys_dev_, surface_, &format_count, nullptr);
    if (format_count == 0) return false;
    VkSurfaceFormatKHR format = {VK_FORMAT_B8G8R8A8_UNORM, VK_COLOR_SPACE_SRGB_NONLINEAR_KHR};
    if (format_count == 1) {
        std::vector<VkSurfaceFormatKHR> fs(1);
        vkGetPhysicalDeviceSurfaceFormatsKHR(phys_dev_, surface_, &format_count, fs.data());
        format = fs[0];
    } else if (format_count > 0) {
        std::vector<VkSurfaceFormatKHR> fs(format_count);
        vkGetPhysicalDeviceSurfaceFormatsKHR(phys_dev_, surface_, &format_count, fs.data());
        bool found = false;
        for (auto& f : fs) { if (f.format == VK_FORMAT_B8G8R8A8_UNORM && f.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) { format = f; found = true; break; } }
        if (!found) format = fs[0];
    } else {
        format = {VK_FORMAT_B8G8R8A8_UNORM, VK_COLOR_SPACE_SRGB_NONLINEAR_KHR};
    }

    uint32_t mode_count = 0;
    vkGetPhysicalDeviceSurfacePresentModesKHR(phys_dev_, surface_, &mode_count, nullptr);
    std::vector<VkPresentModeKHR> modes(mode_count);
    vkGetPhysicalDeviceSurfacePresentModesKHR(phys_dev_, surface_, &mode_count, modes.data());
    VkPresentModeKHR present_mode = VK_PRESENT_MODE_FIFO_KHR;  // vsync
    for (auto& m : modes) {
        if (m == VK_PRESENT_MODE_MAILBOX_KHR) { present_mode = m; break; }
    }

    uint32_t image_count = caps.minImageCount ? ((caps.minImageCount > MAX_FRAMES_IN_FLIGHT) ? caps.minImageCount : MAX_FRAMES_IN_FLIGHT) : MAX_FRAMES_IN_FLIGHT;
    if (caps.maxImageCount > 0) image_count = ((image_count > caps.maxImageCount) ? caps.maxImageCount : image_count);

    VkExtent2D extent;
    if (caps.currentExtent.width != UINT32_MAX) {
        extent = caps.currentExtent;
    } else {
        extent.width  = (cfg_.width < caps.minImageExtent.width)  ? caps.minImageExtent.width :
                        (cfg_.width > caps.maxImageExtent.width) ? caps.maxImageExtent.width : cfg_.width;
        extent.height = (cfg_.height < caps.minImageExtent.height) ? caps.minImageExtent.height :
                        (cfg_.height > caps.maxImageExtent.height) ? caps.maxImageExtent.height : cfg_.height;
    }
    // A minimized window reports extent 0x0; clamp so the swapchain/depth/framebuffers never
    // get a zero size (which is invalid and crashed the engine on minimize).
    if (extent.width  == 0) extent.width  = 800;
    if (extent.height == 0) extent.height = 600;

    VkImageUsageFlags usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT
                            | VK_IMAGE_USAGE_TRANSFER_SRC_BIT   // frame capture reads the swapchain image
                            | VK_IMAGE_USAGE_TRANSFER_DST_BIT;  // blit from the offscreen target

    // Find a queue family that supports both graphics and transfer
    uint32_t count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(phys_dev_, &count, nullptr);
    std::vector<VkQueueFamilyProperties> families(count);
    vkGetPhysicalDeviceQueueFamilyProperties(phys_dev_, &count, families.data());
    uint32_t graphics_family = UINT32_MAX, transfer_family = UINT32_MAX;
    for (uint32_t i = 0; i < count; ++i) {
        if (families[i].queueFlags & VK_QUEUE_GRAPHICS_BIT && graphics_family == UINT32_MAX) graphics_family = i;
        if (families[i].queueFlags & VK_QUEUE_TRANSFER_BIT && transfer_family == UINT32_MAX) transfer_family = i;
    }
    bool separate_transfer = (graphics_family != transfer_family);

    VkSwapchainCreateInfoKHR sci{};
    sci.sType              = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
    sci.surface            = surface_;
    sci.minImageCount      = image_count;
    sci.imageFormat        = format.format;
    sci.imageColorSpace    = format.colorSpace;
    sci.imageExtent        = extent;
    sci.imageArrayLayers   = 1;
    sci.imageUsage         = usage;
    sci.preTransform       = caps.currentTransform;
    sci.compositeAlpha     = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
    sci.presentMode        = present_mode;
    sci.clipped            = VK_TRUE;
    if (separate_transfer) {
        uint32_t families_arr[] = {graphics_family, transfer_family};
        sci.imageSharingMode       = VK_SHARING_MODE_CONCURRENT;
        sci.queueFamilyIndexCount  = 2;
        sci.pQueueFamilyIndices    = families_arr;
    } else {
        sci.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
    }

    if (vkCreateSwapchainKHR(device_, &sci, nullptr, &swapchain_) != VK_SUCCESS) return false;

    // Get swapchain images
    uint32_t img_cnt = 0;
    vkGetSwapchainImagesKHR(device_, swapchain_, &img_cnt, nullptr);
    std::vector<VkImage> imgs(img_cnt);
    vkGetSwapchainImagesKHR(device_, swapchain_, &img_cnt, imgs.data());

    swap_imgs_.resize(img_cnt);
    img_views_.resize(img_cnt);
    frames_.resize(img_cnt);
    cmd_bufs_.resize(img_cnt);
    desc_sets_.resize(img_cnt);

    for (uint32_t i = 0; i < img_cnt; ++i) {
        std::memcpy(&swap_imgs_[i], &imgs[i], sizeof(VkImage));
        VkImageViewCreateInfo ivci{};
        ivci.sType         = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image         = imgs[i];
        ivci.viewType      = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format        = format.format;
        ivci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        ivci.subresourceRange.levelCount = 1;
        ivci.subresourceRange.layerCount = 1;
        vkCreateImageView(device_, &ivci, nullptr, &img_views_[i]);
    }

    extent_ = extent;
    swap_fmt_ = format.format;
    return true;
}

bool Engine::create_render_pass() {
    VkAttachmentDescription color_attach{};
    color_attach.format        = swap_fmt_;
    color_attach.samples       = VK_SAMPLE_COUNT_1_BIT;
    color_attach.loadOp        = VK_ATTACHMENT_LOAD_OP_CLEAR;
    color_attach.storeOp       = VK_ATTACHMENT_STORE_OP_STORE;
    color_attach.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    color_attach.stencilStoreOp= VK_ATTACHMENT_STORE_OP_DONT_CARE;
    color_attach.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    color_attach.finalLayout   = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;

    VkAttachmentDescription depth_attach{};
    depth_attach.format        = VK_FORMAT_D32_SFLOAT;
    depth_attach.samples       = VK_SAMPLE_COUNT_1_BIT;
    depth_attach.loadOp        = VK_ATTACHMENT_LOAD_OP_CLEAR;
    depth_attach.storeOp       = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    depth_attach.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    depth_attach.stencilStoreOp= VK_ATTACHMENT_STORE_OP_DONT_CARE;
    depth_attach.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    depth_attach.finalLayout   = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    VkAttachmentReference color_ref{};
    color_ref.attachment = 0;
    color_ref.layout     = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkAttachmentReference depth_ref{};
    depth_ref.attachment = 1;
    depth_ref.layout     = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint       = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount    = 1;
    subpass.pColorAttachments       = &color_ref;
    subpass.pDepthStencilAttachment = &depth_ref;

    VkAttachmentDescription attachments[2] = {color_attach, depth_attach};
    VkRenderPassCreateInfo rpci{};
    rpci.sType             = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    rpci.attachmentCount   = 2;
    rpci.pAttachments      = attachments;
    rpci.subpassCount      = 1;
    rpci.pSubpasses        = &subpass;

    if (vkCreateRenderPass(device_, &rpci, nullptr, &render_pass_) != VK_SUCCESS) return false;
    return true;
}

bool Engine::compile_shaders() {
    // Load pre-compiled SPIR-V files (generated by CMake from GLSL)
    std::string base = ".";  // shaders are copied next to executable by CMake post-build
    auto vert_spv = read_file((base + "/shaders/render.vert.spv").c_str());
    auto frag_spv = read_file((base + "/shaders/render.frag.spv").c_str());
    auto comp_spv = read_file((base + "/shaders/compute.spv").c_str());
    auto sort_spv = read_file((base + "/shaders/sort.spv").c_str());
    auto skin_spv = read_file((base + "/shaders/skin.spv").c_str());

    if (vert_spv.empty()) { fprintf(stderr, "Failed to load render.vert.spv\n"); return false; }
    if (frag_spv.empty()) { fprintf(stderr, "Failed to load render.frag.spv\n"); return false; }
    if (sort_spv.empty()) { fprintf(stderr, "Failed to load sort.spv\n"); return false; }
    if (skin_spv.empty()) { fprintf(stderr, "Failed to load skin.spv\n"); return false; }
    // compute is optional for first pass (CPU physics path)

    vert_mod_ = create_shader_module(device_, vert_spv);
    frag_mod_ = create_shader_module(device_, frag_spv);
    sort_mod_ = create_shader_module(device_, sort_spv);
    skin_mod_ = create_shader_module(device_, skin_spv);
    if (vert_mod_ == VK_NULL_HANDLE || frag_mod_ == VK_NULL_HANDLE || sort_mod_ == VK_NULL_HANDLE
        || skin_mod_ == VK_NULL_HANDLE) return false;

    auto trivert_spv = read_file((base + "/shaders/render_tri.vert.spv").c_str());
    auto trifrag_spv = read_file((base + "/shaders/render_tri.frag.spv").c_str());
    if (trivert_spv.empty()) { fprintf(stderr, "Failed to load render_tri.vert.spv\n"); return false; }
    if (trifrag_spv.empty()) { fprintf(stderr, "Failed to load render_tri.frag.spv\n"); return false; }
    tri_vert_mod_ = create_shader_module(device_, trivert_spv);
    tri_frag_mod_ = create_shader_module(device_, trifrag_spv);
    if (tri_vert_mod_ == VK_NULL_HANDLE || tri_frag_mod_ == VK_NULL_HANDLE) return false;
    // THE CONTACT SHADOW: optional at init (the engine still runs if the spv
    // is stale) — the shadow is an instrument upgrade, not a load-bearing wall.
    {
        auto shspv = read_file((base + "/shaders/render_tri_shadow.frag.spv").c_str());
        if (!shspv.empty())
            tri_shadow_frag_mod_ = create_shader_module(device_, shspv);
        auto shvsp = read_file((base + "/shaders/render_tri_shadow.vert.spv").c_str());
        if (!shvsp.empty())
            tri_shadow_vert_mod_ = create_shader_module(device_, shvsp);
        // THE GROUND PLANE: same optional-instrument policy — a stale/missing
        // spv costs the floor, not the engine.
        auto fvspv = read_file((base + "/shaders/floor.vert.spv").c_str());
        if (!fvspv.empty())
            floor_vert_mod_ = create_shader_module(device_, fvspv);
        auto ffspv = read_file((base + "/shaders/floor.frag.spv").c_str());
        if (!ffspv.empty())
            floor_frag_mod_ = create_shader_module(device_, ffspv);
    }

    if (!comp_spv.empty()) {
        comp_mod_ = create_shader_module(device_, comp_spv);
    }
    return true;
}

bool Engine::create_pipeline() {
    // Vertex input — matches render.vert: 14 floats = pos(3) color(3) alpha(1) scale(3) rot(4)
    VkVertexInputBindingDescription binding{};
    binding.binding   = 0;
    binding.stride    = sizeof(float) * 14;  // x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz
    binding.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;

    VkVertexInputAttributeDescription attrs[5] = {};
    attrs[0].location = 0;  attrs[0].binding = 0;
    attrs[0].format   = VK_FORMAT_R32G32B32_SFLOAT;
    attrs[0].offset   = 0;            // xyz

    attrs[1].location = 1;  attrs[1].binding = 0;
    attrs[1].format   = VK_FORMAT_R32G32B32_SFLOAT;
    attrs[1].offset   = sizeof(float) * 3;   // rgb

    attrs[2].location = 2;  attrs[2].binding = 0;
    attrs[2].format   = VK_FORMAT_R32_SFLOAT;
    attrs[2].offset   = sizeof(float) * 6;   // alpha

    attrs[3].location = 3;  attrs[3].binding = 0;
    attrs[3].format   = VK_FORMAT_R32G32B32_SFLOAT;
    attrs[3].offset   = sizeof(float) * 7;   // scale (sx,sy,sz)

    attrs[4].location = 4;  attrs[4].binding = 0;
    attrs[4].format   = VK_FORMAT_R32G32B32A32_SFLOAT;
    attrs[4].offset   = sizeof(float) * 10;  // rotation quaternion (w,x,y,z)

    // Pipeline stages
    VkPipelineShaderStageCreateInfo stages[2] = {};
    stages[0].sType           = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage           = VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module          = vert_mod_;
    stages[0].pName           = "main";

    stages[1].sType           = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage           = VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module          = frag_mod_;
    stages[1].pName           = "main";

    // Input assembly — point list (shader expands to quads)
    VkPipelineInputAssemblyStateCreateInfo ia{};
    ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_POINT_LIST;

    // Viewport + scissor (dynamic)
    VkViewport viewport{};
    viewport.width  = static_cast<float>(extent_.width);
    viewport.height = static_cast<float>(extent_.height);
    viewport.maxDepth = 1.0f;

    VkRect2D scissor{};
    scissor.extent = extent_;

    VkPipelineViewportStateCreateInfo vp{};
    vp.sType               = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vp.viewportCount       = 1;
    vp.pViewports          = &viewport;
    vp.scissorCount        = 1;
    vp.pScissors           = &scissor;

    // Rasterization
    VkPipelineRasterizationStateCreateInfo ras{};
    ras.sType               = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    ras.depthClampEnable    = VK_FALSE;
    ras.rasterizerDiscardEnable = VK_FALSE;
    ras.polygonMode         = VK_POLYGON_MODE_FILL;
    ras.cullMode            = VK_CULL_MODE_BACK_BIT;
    ras.frontFace           = VK_FRONT_FACE_CLOCKWISE;
    ras.depthBiasEnable     = VK_FALSE;
    ras.lineWidth           = 1.0f;

    // Multisampling — disabled for splat rendering
    VkPipelineMultisampleStateCreateInfo ms{};
    ms.sType                = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = rt_samples_;   // MUST equal the offscreen pass (pass compatibility)
    ms.sampleShadingEnable  = VK_FALSE;

    // Color blend
    VkPipelineColorBlendAttachmentState blend{};
    blend.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                           VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
    blend.blendEnable    = VK_TRUE;
    blend.srcColorBlendFactor  = VK_BLEND_FACTOR_SRC_ALPHA;   // back-to-front standard alpha
    blend.dstColorBlendFactor  = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    blend.colorBlendOp   = VK_BLEND_OP_ADD;
    blend.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
    blend.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;  // accumulate coverage:
    // a_out = a_src + a_dst(1-a_src). ZERO here let each splat's alpha REPLACE the
    // destination's — a low-alpha skirt turned the pixel translucent, and the PNG
    // composite-over-white readback washed every overlap to white.
    blend.alphaBlendOp       = VK_BLEND_OP_ADD;

    VkPipelineColorBlendStateCreateInfo cb{};
    cb.sType                = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    cb.attachmentCount      = 1;
    cb.pAttachments         = &blend;

    // Dynamic state
    VkPipelineDynamicStateCreateInfo dyn{};
    dyn.sType              = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dyn.dynamicStateCount  = 2;
    static const VkDynamicState dyn_states[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    dyn.pDynamicStates     = dyn_states;

    // Pipeline layout (descriptor set layout)
    VkPipelineLayoutCreateInfo plci{};
    plci.sType            = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    plci.setLayoutCount   = 1;
    plci.pSetLayouts      = &desc_layout_;
    if (vkCreatePipelineLayout(device_, &plci, nullptr, &pipeline_layout_) != VK_SUCCESS) return false;

    // Graphics pipeline
    VkGraphicsPipelineCreateInfo gpci{};
    // Depth stencil — enable depth test/write so the near surface occludes the far (front vs back)
    VkPipelineDepthStencilStateCreateInfo ds{};
    ds.sType             = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    ds.depthTestEnable   = VK_FALSE;   // 3DGS: sorted back-to-front + alpha blend, no depth test
    ds.depthWriteEnable  = VK_FALSE;
    ds.depthCompareOp    = VK_COMPARE_OP_LESS_OR_EQUAL;
    ds.depthBoundsTestEnable = VK_FALSE;
    ds.stencilTestEnable = VK_FALSE;

    gpci.sType                        = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gpci.stageCount                   = 2;
    gpci.pStages                      = stages;
    gpci.pVertexInputState            = nullptr;  // we set this below
    gpci.pInputAssemblyState          = &ia;
    gpci.pViewportState               = &vp;
    gpci.pRasterizationState          = &ras;
    gpci.pMultisampleState            = &ms;
    gpci.pDepthStencilState           = &ds;
    gpci.pColorBlendState             = &cb;
    gpci.pDynamicState                = &dyn;
    gpci.layout                       = pipeline_layout_;
    gpci.renderPass                   = rt_render_pass_;   // frame() renders to the offscreen target
    gpci.subpass                      = 0;

    // Vertex input (need separate struct since it's not const)
    VkPipelineVertexInputStateCreateInfo vi{};
    vi.sType            = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vi.vertexBindingDescriptionCount = 1;
    vi.pVertexBindingDescriptions    = &binding;
    vi.vertexAttributeDescriptionCount = 5;
    vi.pVertexAttributeDescriptions  = attrs;
    gpci.pVertexInputState = &vi;

    VkPipelineCache cache{};
    if (vkCreateGraphicsPipelines(device_, cache, 1, &gpci, nullptr, &pipeline_) != VK_SUCCESS) {
        fprintf(stderr, "Failed to create graphics pipeline\n");
        return false;
    }
    vkDestroyPipelineCache(device_, cache, nullptr);

    return true;
}

bool Engine::create_triangle_pipeline() {
    // Vertex input — matches render_tri.vert: 9 floats = pos(3) normal(3) color(3)
    VkVertexInputBindingDescription binding{};
    binding.binding   = 0;
    binding.stride    = sizeof(float) * 9;  // x,y,z, nx,ny,nz, r,g,b
    binding.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;

    VkVertexInputAttributeDescription attrs[3] = {};
    attrs[0].location = 0;  attrs[0].binding = 0;
    attrs[0].format   = VK_FORMAT_R32G32B32_SFLOAT;
    attrs[0].offset   = 0;            // xyz

    attrs[1].location = 1;  attrs[1].binding = 0;
    attrs[1].format   = VK_FORMAT_R32G32B32_SFLOAT;
    attrs[1].offset   = sizeof(float) * 3;   // normal

    attrs[2].location = 2;  attrs[2].binding = 0;
    attrs[2].format   = VK_FORMAT_R32G32B32_SFLOAT;
    attrs[2].offset   = sizeof(float) * 6;   // color

    // Pipeline stages
    VkPipelineShaderStageCreateInfo stages[2] = {};
    stages[0].sType           = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage           = VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module          = tri_vert_mod_;
    stages[0].pName           = "main";

    stages[1].sType           = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage           = VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module          = tri_frag_mod_;
    stages[1].pName           = "main";

    // Input assembly — triangle list
    VkPipelineInputAssemblyStateCreateInfo ia{};
    ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    // Viewport + scissor (dynamic)
    VkViewport viewport{};
    viewport.width  = static_cast<float>(extent_.width);
    viewport.height = static_cast<float>(extent_.height);
    viewport.maxDepth = 1.0f;

    VkRect2D scissor{};
    scissor.extent = extent_;

    VkPipelineViewportStateCreateInfo vp{};
    vp.sType               = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vp.viewportCount       = 1;
    vp.pViewports          = &viewport;
    vp.scissorCount        = 1;
    vp.pScissors           = &scissor;

    // Rasterization
    VkPipelineRasterizationStateCreateInfo ras{};
    ras.sType               = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    ras.depthClampEnable    = VK_FALSE;
    ras.rasterizerDiscardEnable = VK_FALSE;
    ras.polygonMode         = VK_POLYGON_MODE_FILL;
    ras.cullMode            = VK_CULL_MODE_NONE;
    ras.frontFace           = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    ras.depthBiasEnable     = VK_FALSE;
    ras.lineWidth           = 1.0f;

    // Multisampling — disabled
    VkPipelineMultisampleStateCreateInfo ms{};
    ms.sType                = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = rt_samples_;   // MUST equal the offscreen pass (pass compatibility)
    ms.sampleShadingEnable  = VK_FALSE;

    // Color blend — opaque
    VkPipelineColorBlendAttachmentState blend{};
    blend.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                           VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
    blend.blendEnable    = VK_FALSE;

    VkPipelineColorBlendStateCreateInfo cb{};
    cb.sType                = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    cb.attachmentCount      = 1;
    cb.pAttachments         = &blend;

    // Dynamic state
    VkPipelineDynamicStateCreateInfo dyn{};
    dyn.sType              = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dyn.dynamicStateCount  = 2;
    static const VkDynamicState dyn_states[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    dyn.pDynamicStates     = dyn_states;

    // Depth stencil — enable depth test/write for triangle occlusion
    VkPipelineDepthStencilStateCreateInfo ds{};
    ds.sType             = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    ds.depthTestEnable   = VK_TRUE;
    ds.depthWriteEnable  = VK_TRUE;
    ds.depthCompareOp    = VK_COMPARE_OP_LESS;
    ds.depthBoundsTestEnable = VK_FALSE;
    ds.stencilTestEnable = VK_FALSE;

    // Graphics pipeline — reuse the existing pipeline_layout_ (UBO binding 0)
    VkGraphicsPipelineCreateInfo gpci{};
    gpci.sType                        = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gpci.stageCount                   = 2;
    gpci.pStages                      = stages;
    gpci.pVertexInputState            = nullptr;  // set below
    gpci.pInputAssemblyState          = &ia;
    gpci.pViewportState               = &vp;
    gpci.pRasterizationState          = &ras;
    gpci.pMultisampleState            = &ms;
    gpci.pDepthStencilState           = &ds;
    gpci.pColorBlendState             = &cb;
    gpci.pDynamicState                = &dyn;
    gpci.layout                       = pipeline_layout_;
    gpci.renderPass                   = rt_render_pass_;
    gpci.subpass                      = 0;

    VkPipelineVertexInputStateCreateInfo vi{};
    vi.sType            = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vi.vertexBindingDescriptionCount = 1;
    vi.pVertexBindingDescriptions    = &binding;
    vi.vertexAttributeDescriptionCount = 3;
    vi.pVertexAttributeDescriptions  = attrs;
    gpci.pVertexInputState = &vi;

    VkPipelineCache cache{};
    if (vkCreateGraphicsPipelines(device_, cache, 1, &gpci, nullptr, &tri_pipeline_) != VK_SUCCESS) {
        fprintf(stderr, "Failed to create triangle graphics pipeline\n");
        return false;
    }
    // Wireframe twin: identical in every state except polygon mode — the GPU
    // rasterizes the triangle EDGES as constant 1px lines (device has
    // fillModeNonSolid). Hairlines at any zoom; no world-space rod geometry.
    ras.polygonMode = VK_POLYGON_MODE_LINE;
    if (vkCreateGraphicsPipelines(device_, cache, 1, &gpci, nullptr, &tri_wire_pipeline_) != VK_SUCCESS) {
        fprintf(stderr, "Failed to create triangle wireframe pipeline\n");
        return false;
    }
    // THE GROUND PLANE geometry: one static quad on the xz plane, big enough
    // that the camera's usual orbits never see its edge. y is IGNORED by the
    // vertex stage (the UBO's floor plane owns it) but set to 0 for clarity.
    // BUFFER GATE FIX (2026-09-03): this used to ALSO require floor_pipeline_
    // != VK_NULL_HANDLE — but the pipeline is created LATER in this function, so
    // on the only call the gate was false and floor_vbuf_ stayed null forever:
    // the draw site's guard silently skipped the quad every frame. The buffer
    // never depended on the pipeline; gate on the buffer alone.
    if (floor_vbuf_ == VK_NULL_HANDLE) {
        const float R = 60.f;
        const float q[FLOOR_VERTS * 3] = {
            -R, 0.f, -R,   R, 0.f, -R,   R, 0.f,  R,
            -R, 0.f, -R,   R, 0.f,  R,  -R, 0.f,  R,
        };
        upload_buffer(q, sizeof(q), VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, floor_vbuf_, floor_vmem_);
    }
    // Shadow twin (the eye's "subject ungrounded", 2026-09-02): the same mesh
    // projected to the floor plane by the vertex stage; blended translucent
    // black, no depth write (the mesh's own depth test decides visibility).
    // Culling stays OFF — the recon mesh's winding is unreliable (the fill
    // pipeline is CULL_MODE_NONE for the same reason), and a culled shadow is
    // an invisible shadow. Requires its own frag module (flat alpha) —
    // silently skipped if the module failed to load.
    if (tri_shadow_frag_mod_ != VK_NULL_HANDLE && tri_shadow_vert_mod_ != VK_NULL_HANDLE) {
        ras.polygonMode = VK_POLYGON_MODE_FILL;
        ras.cullMode    = VK_CULL_MODE_NONE;
        stages[0].module = tri_shadow_vert_mod_;   // THE projection — without this
                                                   // the shadow draws at the mesh's own
                                                   // position, hidden behind the subject
        stages[1].module = tri_shadow_frag_mod_;
        blend.blendEnable = VK_TRUE;
        blend.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
        blend.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
        blend.colorBlendOp        = VK_BLEND_OP_ADD;
        blend.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
        blend.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
        blend.alphaBlendOp        = VK_BLEND_OP_ADD;
        ds.depthWriteEnable = VK_FALSE;
        ds.depthTestEnable  = VK_FALSE;
        // FLOOR-COEXIST (2026-09-03, two rounds): the shadow projects onto the
        // SAME y=0 plane the floor rasterizes, so its fragment depth equals the
        // floor's only up to float ulps — LESS rejected every fragment (shadow
        // = 0 pixels measured), and LESS_OR_EQUAL still rejected the half where
        // the interpolated depth lands 1e-6 FARTHER. A decal that draws
        // immediately after the floor and before the mesh must not gamble on
        // depth equality at all: test OFF, write OFF. The mesh (drawn later,
        // depth-tested) still wins where it stands in front.
        if (vkCreateGraphicsPipelines(device_, cache, 1, &gpci, nullptr, &tri_shadow_pipeline_) != VK_SUCCESS) {
            fprintf(stderr, "Failed to create triangle shadow pipeline\n");
            tri_shadow_pipeline_ = VK_NULL_HANDLE;
        }
    }
    // THE GROUND PLANE twin: position-only verts (one vec3), opaque, depth-test
    // ON + depth-write ON — the floor is world geometry the subject stands ON,
    // and the shadow's no-depth-write draw must lose to it where they overlap.
    // Built ONLY if both modules loaded (same instrument policy as the shadow).
    if (floor_vert_mod_ != VK_NULL_HANDLE && floor_frag_mod_ != VK_NULL_HANDLE) {
        printf("floor: building pipeline (modules ok)\n");
        VkVertexInputBindingDescription fbinding{};
        fbinding.binding   = 0;
        fbinding.stride    = sizeof(float) * 3;
        fbinding.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;

        VkVertexInputAttributeDescription fattrs[1] = {};
        fattrs[0].location = 0; fattrs[0].binding = 0;
        fattrs[0].format   = VK_FORMAT_R32G32B32_SFLOAT;
        fattrs[0].offset   = 0;

        stages[0].module = floor_vert_mod_;
        stages[1].module = floor_frag_mod_;

        vi.pVertexBindingDescriptions   = &fbinding;
        vi.pVertexAttributeDescriptions = fattrs;
        vi.vertexAttributeDescriptionCount = 1;

        blend.blendEnable = VK_FALSE;             // opaque
        ds.depthTestEnable  = VK_TRUE;            // shared ds now carries the shadow's
                                                  // depthTestEnable=FALSE — pin the
                                                  // floor's own law explicitly
        ds.depthWriteEnable = VK_TRUE;
        ds.depthCompareOp    = VK_COMPARE_OP_LESS; // shared ds carries the shadow's
                                                   // LESS_OR_EQUAL — pin the floor's
                                                   // own law explicitly
        ras.cullMode = VK_CULL_MODE_NONE;         // winding kept unordered by intent

        if (vkCreateGraphicsPipelines(device_, cache, 1, &gpci, nullptr, &floor_pipeline_) != VK_SUCCESS) {
            fprintf(stderr, "Failed to create floor pipeline\n");
            floor_pipeline_ = VK_NULL_HANDLE;
        } else {
            printf("floor: pipeline created\n");
        }
    } else {
        printf("floor: SKIPPED (vert=%p frag=%p)\n", (void*)floor_vert_mod_, (void*)floor_frag_mod_);
    }
    vkDestroyPipelineCache(device_, cache, nullptr);

    return true;
}

bool Engine::load_mesh(const std::vector<float>& verts, const std::vector<uint32_t>& indices,
                       uint32_t vcount, uint32_t icount) {
    vkDeviceWaitIdle(device_);
    // B3: an empty POST clears the mesh slot (was: 0-byte buffer -> NULL-handle crash).
    if (verts.empty() || indices.empty() || icount == 0) {
        upload_buffer(nullptr, 0, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, tri_vbuf_, tri_vmem_);
        upload_buffer(nullptr, 0, VK_BUFFER_USAGE_INDEX_BUFFER_BIT, tri_ibuf_, tri_imem_);
        tri_idx_count_ = 0;
        has_mesh_ = false;
        joints_desc_dirty_ = true;   // tri_vbuf_ recreated — the old handle dangles
        hinge_desc_dirty_ = true;
        return true;
    }
    // THE NORMAL-HYGIENE GATE (2026-09-03, the eye's speckle finding): a degenerate
    // triangle ships a zero-length stored normal; normalize(0) is NaN in the shader
    // and the vertex shades to a bright speckle (measured: a dotted arc at the neck
    // base). Any vertex whose stored normal is non-finite or far from unit length
    // is re-derived here as the area-weighted sum of its adjacent face normals —
    // in load_mesh, the one gate every upload path passes through, so the class is
    // dead for all meshes, not just this one. Healthy vertices are untouched.
    std::vector<float> clean(verts);           // mutable working copy
    const size_t nv = clean.size() / 9;
    auto nrm_bad = [](const float* n) {
        if (!std::isfinite(n[0]) || !std::isfinite(n[1]) || !std::isfinite(n[2])) return true;
        float len = sqrtf(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
        return len < 0.5f || len > 2.0f;       // only genuinely-broken normals repair
    };
    std::vector<char> bad(nv, 0);
    size_t nbad = 0;
    for (size_t v = 0; v < nv; ++v)
        if (nrm_bad(clean.data() + v * 9 + 3)) { bad[v] = 1; ++nbad; }
    if (nbad > 0) {
        std::vector<float> acc(nv * 3, 0.0f);
        for (size_t t = 0; t + 2 < indices.size(); t += 3) {
            uint32_t ia = indices[t], ib = indices[t + 1], ic = indices[t + 2];
            if ((size_t)ia >= nv || (size_t)ib >= nv || (size_t)ic >= nv) continue;
            const float* A = clean.data() + (size_t)ia * 9;
            const float* B = clean.data() + (size_t)ib * 9;
            const float* C = clean.data() + (size_t)ic * 9;
            float ux = B[0] - A[0], uy = B[1] - A[1], uz = B[2] - A[2];
            float wx = C[0] - A[0], wy = C[1] - A[1], wz = C[2] - A[2];
            float fx = uy * wz - uz * wy, fy = uz * wx - ux * wz, fz2 = ux * wy - uy * wx; // area-weighted
            if (!std::isfinite(fx) || !std::isfinite(fy) || !std::isfinite(fz2)) continue;
            const uint32_t tri[3] = { ia, ib, ic };
            for (int k = 0; k < 3; ++k) {
                uint32_t v = tri[k];
                if (!bad[v]) continue;         // only the broken verts accumulate
                acc[(size_t)v * 3 + 0] += fx; acc[(size_t)v * 3 + 1] += fy; acc[(size_t)v * 3 + 2] += fz2;
            }
        }
        for (size_t v = 0; v < nv; ++v) {
            if (!bad[v]) continue;
            float nx = acc[v * 3], ny = acc[v * 3 + 1], nz = acc[v * 3 + 2];
            float len = sqrtf(nx * nx + ny * ny + nz * nz);
            if (len > 1e-12f) {
                clean[v * 9 + 3] = nx / len; clean[v * 9 + 4] = ny / len; clean[v * 9 + 5] = nz / len;
            } else {                            // isolated: every adjacent face degenerate
                clean[v * 9 + 3] = 0.0f; clean[v * 9 + 4] = 1.0f; clean[v * 9 + 5] = 0.0f;
            }
        }
        fprintf(stderr, "[load_mesh] normal hygiene: repaired %zu/%zu verts\n", nbad, nv);
    }
    // Vertex buffer: DEVICE_LOCAL (the hot path must stay in VRAM — a host-visible
    // buffer cost ~6 ms/frame of PCIe traffic when the GPU hinge kernel wrote it).
    // CPU-side writes (update_mesh, hinge restore) go through a persistent
    // host-visible STAGING buffer + one transfer; the draw/compute path never
    // leaves the GPU.
    upload_buffer(clean.data(), static_cast<VkDeviceSize>(clean.size()) * sizeof(float),
                  VK_BUFFER_USAGE_VERTEX_BUFFER_BIT | VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
                  tri_vbuf_, tri_vmem_);
    {
        if (tri_staging_buf_) {
            vkUnmapMemory(device_, tri_staging_mem_);
            vkDestroyBuffer(device_, tri_staging_buf_, nullptr);
            vkFreeMemory(device_, tri_staging_mem_, nullptr);
            tri_staging_buf_ = VK_NULL_HANDLE; tri_vmap_ = nullptr;
        }
        VkDeviceSize sz = static_cast<VkDeviceSize>(verts.size()) * sizeof(float);
        VkBufferCreateInfo sci{};
        sci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        sci.size        = sz;
        sci.usage       = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
        sci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &sci, nullptr, &tri_staging_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, tri_staging_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize  = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &tri_staging_mem_);
        vkBindBufferMemory(device_, tri_staging_buf_, tri_staging_mem_, 0);
        vkMapMemory(device_, tri_staging_mem_, 0, sz, 0, &tri_vmap_);
    }
    mesh_cpu_ = clean;
    tri_vfloats_ = clean.size();
    // THE DEGENERATE EVICTION (2026-09-03, same eye finding — the speckle dots):
    // the birth mesh carries 206 EXACTLY-zero-area triangles (collinear verts).
    // They contribute nothing to the surface, but on the GPU the MVP transform's
    // f32 rounding can reopen them into sub-pixel slivers that rasterize as 1px
    // dots along the pinched creases — measured flicker class. Evicted here, in
    // the same load gate; per-vertex systems (hinge/gait/springs) are untouched,
    // and tri_rest_area_/strain stay consistent because they are recomputed from
    // the KEPT list. 206/36630 = 0.56% of the indices.
    std::vector<uint32_t> clean_idx;
    clean_idx.reserve(indices.size());
    // The sub-pixel threshold needs the model radius BEFORE the loop: 1px at the
    // auto-framed camera is ~ r/720 world units (measured: r=10 -> body half-width
    // ~595px on a 1440p viewport ~ 60px/unit).
    float rfit2 = 0.0f;
    for (size_t i = 0; i + 2 < clean.size(); i += 9) {
        float x = clean[i], y = clean[i + 1], z = clean[i + 2];
        rfit2 = (std::max)(rfit2, x * x + y * y + z * z);
    }
    const float px1 = sqrtf(rfit2) / 720.0f;      // ~1px at the auto frame
    // The physically-derived cut: at 4x MSAA a feature wider than 1/4 px still
    // catches a sample (renders as a blended line). Below 1/4 px it is
    // sub-sample — dot-or-nothing, unresolvable by ANY sampling rate. Measured:
    // the mesher gradates a CONTINUUM of thin tris at creases (170 < 0.14px,
    // 460 < 0.36px, 2945 < 1px wide), so the cut belongs at the sampling
    // physics, not at a taste threshold. Width = |cross|/longest-edge.
    const float sliver_max = 0.25f * px1;
    size_t n_evict = 0, n_collapse = 0;
    for (size_t t = 0; t + 2 < indices.size(); t += 3) {
        uint32_t ia = indices[t], ib = indices[t + 1], ic = indices[t + 2];
        bool keep = true;
        if ((size_t)ia < nv && (size_t)ib < nv && (size_t)ic < nv) {
            const float* A = clean.data() + (size_t)ia * 9;
            const float* B = clean.data() + (size_t)ib * 9;
            const float* C = clean.data() + (size_t)ic * 9;
            double ux = (double)B[0] - A[0], uy = (double)B[1] - A[1], uz = (double)B[2] - A[2];
            double wx = (double)C[0] - A[0], wy = (double)C[1] - A[1], wz = (double)C[2] - A[2];
            double cx = uy * wz - uz * wy, cy = uz * wx - ux * wz, cz = ux * wy - uy * wx;
            if (0.5 * sqrt(cx * cx + cy * cy + cz * cz) < 1e-12) { keep = false; ++n_evict; }
            else {
                // THE SUB-PIXEL SLIVER COLLAPSE (2026-09-03, MSAA follow-up):
                // tiny but WELL-SHAPED triangles (longest edge <= ~0.5px at the
                // auto frame) cannot cover a full sample even at 4x — the
                // sampler quantizes them into the 1px dots the eye mapped on the
                // creases. Collapse in place to (0,0,0): a degenerate triangle
                // emits no fragments (the rasterizer's own law — the evicted
                // zeros already ride this path at zero pixel cost), and
                // collapse-in-place never renumbers, so every lane that stores
                // triangle references stays aligned.
                double eab = sqrt(ux * ux + uy * uy + uz * uz);
                double ebc = sqrt((double)(C[0] - B[0]) * (C[0] - B[0]) + (double)(C[1] - B[1]) * (C[1] - B[1]) + (double)(C[2] - B[2]) * (C[2] - B[2]));
                double eca = sqrt(wx * wx + wy * wy + wz * wz);
                double eM = (std::max)(eab, (std::max)(ebc, eca));
                // width = 2*area / longest edge = |cross| / eM — the tri's
                // minimal-footprint statistic. Sub-sample-width tris collapse.
                double width = sqrt(cx * cx + cy * cy + cz * cz) / (std::max)(eM, 1e-12);
                if (width < (double)sliver_max) {
                    clean_idx.push_back(0); clean_idx.push_back(0); clean_idx.push_back(0);
                    ++n_collapse;
                    continue;
                }
            }
        }
        if (keep) { clean_idx.push_back(ia); clean_idx.push_back(ib); clean_idx.push_back(ic); }
    }
    if (n_evict > 0)
        fprintf(stderr, "[load_mesh] degenerate eviction: dropped %zu zero-area tris\n", n_evict);
    if (n_collapse > 0)
        fprintf(stderr, "[load_mesh] sliver collapse: neutralized %zu sub-sample tris (width < %.5f wu)\n", n_collapse, sliver_max);
    // THE STRAIN OVERLAY: keep the index list — true triangle strain needs the
    // adjacency, and the loader used to throw it away.
    mesh_tris_.assign(clean_idx.begin(), clean_idx.end());
    tri_rest_area_.clear();
    upload_buffer(clean_idx.data(), static_cast<VkDeviceSize>(clean_idx.size()) * sizeof(uint32_t),
                  VK_BUFFER_USAGE_INDEX_BUFFER_BIT | VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, tri_ibuf_, tri_imem_);
    tri_idx_count_ = static_cast<uint32_t>(clean_idx.size());
    has_mesh_ = true;
    water_vis_desc_dirty_ = true;   // buffers recreated -> the water-vis set must rebind (H4)
    frost_desc_dirty_ = true;       // same for the frost decode set (H9)
    joints_desc_dirty_ = true;      // same for the joints set (binding 4 = tri_vbuf_)
    hinge_desc_dirty_ = true;       // same for the hinge set (binding 3 = tri_vbuf_)
    // THE STRAIN OVERLAY: rest areas are a REST-SHAPE property — computed once
    // per mesh, here, from the kept index list. strain_flags_ marks which
    // records carry a strain value (verts_touched order from set_hinge).
    tri_rest_area_.clear();
    if (!mesh_tris_.empty()) {
        tri_rest_area_.reserve(mesh_tris_.size() / 3);
        for (size_t t = 0; t + 2 < mesh_tris_.size(); t += 3) {
            const float* A = mesh_cpu_.data() + (size_t)mesh_tris_[t] * 9;
            const float* B = mesh_cpu_.data() + (size_t)mesh_tris_[t + 1] * 9;
            const float* C = mesh_cpu_.data() + (size_t)mesh_tris_[t + 2] * 9;
            float ux = B[0] - A[0], uy = B[1] - A[1], uz = B[2] - A[2];
            float wx = C[0] - A[0], wy = C[1] - A[1], wz = C[2] - A[2];
            float cx = uy * wz - uz * wy, cy = uz * wx - ux * wz, cz = ux * wy - uy * wx;
            // collapsed slivers ride as exact 0 — clamp so no downstream
            // strain division can ever see a zero rest area.
            tri_rest_area_.push_back((std::max)(0.5f * sqrtf(cx * cx + cy * cy + cz * cz), 1e-12f));
        }
    }
    // Measure the bounding sphere about the origin (the camera target) — the
    // zoom floor derives from THIS, so the near plane can never slice the
    // mesh no matter how far in the operator scrolls. Vertex stride = 9
    // (pos3 + normal3 + color3).
    float r2max = 0.0f;
    float ymin = 0.0f, ymax = 1.0f;   // H0 defaults sane for degenerate payloads
    bool first = true;
    for (size_t i = 0; i + 2 < clean.size(); i += 9) {
        float x = clean[i], y = clean[i + 1], z = clean[i + 2];
        float r2 = x * x + y * y + z * z;
        if (r2 > r2max) r2max = r2;
        if (first)      { ymin = y; ymax = y; first = false; }
        else if (y < ymin) ymin = y;
        else if (y > ymax) ymax = y;
    }
    g_mesh_sphere = sqrtf(r2max);
    g_mesh_ymin = ymin; g_mesh_ymax = ymax;
    return true;
}

void Engine::mesh_upload(const float* data, size_t floats) {
    if (tri_staging_buf_ == VK_NULL_HANDLE || floats != tri_vfloats_) return;
    // Sync: previous draws may still be reading the buffer. Wait ALL flight fences
    // (not device idle) — cheap, and it does not stall the loop.
    vkWaitForFences(device_, MAX_FRAMES_IN_FLIGHT, fences_.data(), VK_TRUE, UINT64_MAX);
    std::memcpy(tri_vmap_, data, floats * sizeof(float));
    VkCommandBuffer cb = begin_single_time_cmd();
    VkBufferCopy bc{}; bc.size = floats * sizeof(float);
    vkCmdCopyBuffer(cb, tri_staging_buf_, tri_vbuf_, 1, &bc);
    end_single_time_cmd(cb);
}

bool Engine::update_mesh(const std::vector<float>& verts9, uint32_t vcount) {
    if (!has_mesh_ || tri_staging_buf_ == VK_NULL_HANDLE) return false;
    if (verts9.size() != tri_vfloats_) return false;  // layout changed -> full load
    mesh_upload(verts9.data(), verts9.size());
    (void)vcount;
    return true;
}

// ── The hinge lives in the engine ────────────────────────────────────────────
// Same skin-moving law the operator approved on the Python march: each vertex
// rotates by theta(t) * w_i about (J, axis), w fading to 0 at the joint's
// measured extent. Computed here, on the engine's clock, at render rate.

bool Engine::set_hinge(const std::vector<float>& wL, const std::vector<float>& wR,
                       const float JL[3], const float JR[3], const float axis[3],
                       float romL, float romR, float period, float phaseR) {
    if (!has_mesh_ || mesh_cpu_.empty()) return false;
    size_t nv = tri_vfloats_ / 9;
    if (wL.size() != nv || wR.size() != nv) {
        fprintf(stderr, "set_hinge: weight count mismatch (%zu/%zu vs %zu verts)\n",
                wL.size(), wR.size(), nv);
        return false;
    }
    vkDeviceWaitIdle(device_);
    // rest state = the CPU copy of the last full-loaded mesh (rest pose by contract)
    hinge_rest_ = mesh_cpu_;
    hinge_wL_ = wL; hinge_wR_ = wR;
    std::memcpy(hinge_JL_, JL, 12); std::memcpy(hinge_JR_, JR, 12);
    std::memcpy(hinge_axis_, axis, 12);
    hinge_romL_ = romL; hinge_romR_ = romR;
    hinge_period_ = period; hinge_phaseR_ = phaseR;
    hinge_t0_ = std::chrono::steady_clock::now();

    // ── THE STRAIN OVERLAY: touched-vertex set + per-vertex SSBO ────────────
    // verts_touched order (wL/wR nonzero, disjoint bands) is the compact
    // domain of the strain math; rank_ scatters a compact index -> vertex.
    {
        strain_vt_.clear(); strain_vt_.reserve(nv);
        for (size_t i = 0; i < nv; ++i)
            if (wL[i] != 0.0f || wR[i] != 0.0f) strain_vt_.push_back(static_cast<uint32_t>(i));
        strain_rank_.assign(nv, -1);
        for (size_t r = 0; r < strain_vt_.size(); ++r) strain_rank_[strain_vt_[r]] = static_cast<int32_t>(r);
        strain_acc_.assign(strain_vt_.size(), 0.f);       // compact: indexed by rank
        strain_posed_.assign(strain_vt_.size() * 3, 0.f); // compact xyz per rank
        strain_cnt_.assign(strain_vt_.size(), 0u);
        const VkDeviceSize need = static_cast<VkDeviceSize>(nv) * sizeof(float);
        if (strain_buf_ == VK_NULL_HANDLE || strain_cap_ < nv) {
            if (strain_map_) { vkUnmapMemory(device_, strain_mem_); strain_map_ = nullptr; }
            if (strain_buf_ != VK_NULL_HANDLE) { vkDestroyBuffer(device_, strain_buf_, nullptr); strain_buf_ = VK_NULL_HANDLE; }
            if (strain_mem_ != VK_NULL_HANDLE) { vkFreeMemory(device_, strain_mem_, nullptr); strain_mem_ = VK_NULL_HANDLE; }
            VkBufferCreateInfo sbci{};
            sbci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
            sbci.size  = need;
            sbci.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
            vkCreateBuffer(device_, &sbci, nullptr, &strain_buf_);
            VkMemoryRequirements smr; vkGetBufferMemoryRequirements(device_, strain_buf_, &smr);
            VkMemoryAllocateInfo sai{};
            sai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
            sai.allocationSize = smr.size;
            sai.memoryTypeIndex = find_mem_type(smr.memoryTypeBits,
                VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
            vkAllocateMemory(device_, &sai, nullptr, &strain_mem_);
            vkBindBufferMemory(device_, strain_buf_, strain_mem_, 0);
            vkMapMemory(device_, strain_mem_, 0, need, 0, reinterpret_cast<void**>(&strain_map_));
            strain_cap_ = nv;
        }
        std::memset(strain_map_, 0, need);   // 0 = rest color until the first frame
    }

    // ── GPU hinge kernel setup (the CA-field path) ─────────────────────────
    // rest state + weights as SSBOs; hinge.comp poses into tri_vbuf_ per frame.
    {
        std::string spv_path = "shaders/hinge.spv";
        std::vector<char> spv = read_file(spv_path.c_str());
        if (!spv.empty()) {
            if (hinge_mod_ == VK_NULL_HANDLE) {
                VkShaderModuleCreateInfo smci{};
                smci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
                smci.codeSize = spv.size();
                smci.pCode = reinterpret_cast<const uint32_t*>(spv.data());
                vkCreateShaderModule(device_, &smci, nullptr, &hinge_mod_);
            }
            upload_buffer(hinge_rest_.data(), hinge_rest_.size() * sizeof(float),
                          VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, hinge_rest_buf_, hinge_rest_mem_);
            upload_buffer(hinge_wL_.data(), hinge_wL_.size() * sizeof(float),
                          VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, hinge_wL_buf_, hinge_wL_mem_);
            upload_buffer(hinge_wR_.data(), hinge_wR_.size() * sizeof(float),
                          VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, hinge_wR_buf_, hinge_wR_mem_);

            if (hinge_pipe_ == VK_NULL_HANDLE && hinge_mod_ != VK_NULL_HANDLE) {
                VkDescriptorSetLayoutBinding b[5] = {};
                for (int k = 0; k < 5; ++k) {
                    b[k].binding = k;
                    b[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
                    b[k].descriptorCount = 1;
                    b[k].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
                }
                VkDescriptorSetLayoutCreateInfo dlci{};
                dlci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
                dlci.bindingCount = 5;
                dlci.pBindings = b;
                vkCreateDescriptorSetLayout(device_, &dlci, nullptr, &hinge_desc_layout_);

                VkPushConstantRange pcr{};
                pcr.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
                pcr.offset = 0;
                pcr.size = 3 * 16 + 10 * 4;  // vec4 JL/JR/axis + 8 floats + 2 uints
                VkPipelineLayoutCreateInfo plci{};
                plci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
                plci.setLayoutCount = 1;
                plci.pSetLayouts = &hinge_desc_layout_;
                plci.pushConstantRangeCount = 1;
                plci.pPushConstantRanges = &pcr;
                vkCreatePipelineLayout(device_, &plci, nullptr, &hinge_layout_);

                VkComputePipelineCreateInfo cpci{};
                cpci.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
                cpci.stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
                cpci.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
                cpci.stage.module = hinge_mod_;
                cpci.stage.pName = "main";
                cpci.layout = hinge_layout_;
                vkCreateComputePipelines(device_, VK_NULL_HANDLE, 1, &cpci, nullptr, &hinge_pipe_);

                VkDescriptorPoolSize ps{};
                ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
                ps.descriptorCount = 5;
                VkDescriptorPoolCreateInfo dpci{};
                dpci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
                dpci.maxSets = 1;
                dpci.poolSizeCount = 1;
                dpci.pPoolSizes = &ps;
                vkCreateDescriptorPool(device_, &dpci, nullptr, &hinge_desc_pool_);
                VkDescriptorSetAllocateInfo dsai{};
                dsai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
                dsai.descriptorPool = hinge_desc_pool_;
                dsai.descriptorSetCount = 1;
                dsai.pSetLayouts = &hinge_desc_layout_;
                vkAllocateDescriptorSets(device_, &dsai, &hinge_desc_set_);
            }
            if (hinge_desc_set_ != VK_NULL_HANDLE) {
                VkDescriptorBufferInfo infos[5] = {};
                infos[0].buffer = hinge_rest_buf_; infos[0].range = VK_WHOLE_SIZE;
                infos[1].buffer = hinge_wL_buf_;   infos[1].range = VK_WHOLE_SIZE;
                infos[2].buffer = hinge_wR_buf_;   infos[2].range = VK_WHOLE_SIZE;
                infos[3].buffer = tri_vbuf_;       infos[3].range = VK_WHOLE_SIZE;
                infos[4].buffer = strain_buf_;     infos[4].range = VK_WHOLE_SIZE;
                VkWriteDescriptorSet w[5] = {};
                for (int k = 0; k < 5; ++k) {
                    w[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
                    w[k].dstSet = hinge_desc_set_;
                    w[k].dstBinding = k;
                    w[k].descriptorCount = 1;
                    w[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
                    w[k].pBufferInfo = &infos[k];
                }
                vkUpdateDescriptorSets(device_, 5, w, 0, nullptr);
            }
            // upload_buffer DESTROYED and recreated hinge_rest_buf_ above —
            // the JOINTS kernel's set binds it too (binding 0, "Rest") and
            // still points at the dead handle. Its dispatch choked on exactly
            // this (VK_ERROR_DEVICE_LOST, _launch_err.log, D5 hunt). The
            // water/frost precedent: mark dirty, rebind lazily in frame().
            joints_desc_dirty_ = true;
        } else {
            fprintf(stderr, "hinge.spv missing — CPU pose fallback\n");
        }
    }
    hinge_active_ = true;
    printf("Hinge engaged: %zu verts, period %.1fs, ROM L %.1f R %.1f deg\n",
           nv, period, romL, romR);
    return true;
}

void Engine::stop_hinge() {
    if (!hinge_active_) return;
    hinge_active_ = false;
    // restore the rest pose so the mesh doesn't freeze mid-bend
    if (!hinge_rest_.empty()) mesh_upload(hinge_rest_.data(), hinge_rest_.size());
    printf("Hinge disengaged, rest pose restored\n");
}

// Per-frame pose, called right after the fence wait in frame() (previous draw
// is done reading the buffer). Rodrigues per vertex about (J, axis) by
// theta * w; normals rotate identically (records are pos3 nrm3 col3, stride 9).
void Engine::pose_hinge() {
    float t = hinge_time();   // the transport drives the live clock (D1, 2026-09-02)
    float thL_deg, thR_deg;
    if (gait_on_.load(std::memory_order_relaxed) && gait_loaded_) {
        double tL, tR; gait_theta(tL, tR);          // H7: the gait CPG commands the knees
        thL_deg = static_cast<float>(tL); thR_deg = static_cast<float>(tR);
    } else {
        const float two_pi = 6.28318530718f;
        float ph = fmodf(t, hinge_period_) / hinge_period_;
        thL_deg = (0.5f - 0.5f * cosf(two_pi * ph)) * hinge_romL_;
        thR_deg = (0.5f - 0.5f * cosf(two_pi * ph + hinge_phaseR_)) * hinge_romR_;
    }
    float thL = thL_deg * 0.01745329251f;   // deg -> rad
    float thR = thR_deg * 0.01745329251f;

    float* buf = static_cast<float*>(tri_vmap_);
    const float* rest = hinge_rest_.data();
    size_t nv = hinge_wL_.size();
    const float ax = hinge_axis_[0], ay = hinge_axis_[1], az = hinge_axis_[2];
    for (size_t i = 0; i < nv; ++i) {
        float wL = hinge_wL_[i], wR = hinge_wR_[i];
        if (wL == 0.0f && wR == 0.0f) continue;     // never moves: rest is already correct
        float th = thL * wL + thR * wR;             // bands are disjoint by construction
        const float* J = (wL >= wR) ? hinge_JL_ : hinge_JR_;
        float c = cosf(th), s = sinf(th);
        float* dst = buf + i * 9;
        const float* src = rest + i * 9;
        for (int k = 0; k < 2; ++k) {               // 0 = position, 1 = normal
            const float* base = (k == 0) ? J : nullptr;
            float vx = src[k * 3 + 0] - (base ? base[0] : 0.f);
            float vy = src[k * 3 + 1] - (base ? base[1] : 0.f);
            float vz = src[k * 3 + 2] - (base ? base[2] : 0.f);
            float cx = ay * vz - az * vy, cy = az * vx - ax * vz, cz = ax * vy - ay * vx;
            float d = ax * vx + ay * vy + az * vz;
            float rx = vx * c + cx * s + ax * d * (1.f - c);
            float ry = vy * c + cy * s + ay * d * (1.f - c);
            float rz = vz * c + cz * s + az * d * (1.f - c);
            dst[k * 3 + 0] = rx + (base ? base[0] : 0.f);
            dst[k * 3 + 1] = ry + (base ? base[1] : 0.f);
            dst[k * 3 + 2] = rz + (base ? base[2] : 0.f);
        }
        // colors (src[6..8]) pass through untouched — dst already holds them
    }
    // CPU fallback wrote the STAGING map — push it to the device buffer.
    VkCommandBuffer cb = begin_single_time_cmd();
    VkBufferCopy bc{}; bc.size = hinge_rest_.size() * sizeof(float);
    vkCmdCopyBuffer(cb, tri_staging_buf_, tri_vbuf_, 1, &bc);
    end_single_time_cmd(cb);

    // Same tint the kernel applies (below), so the CPU fallback path shows the
    // identical overlay — one law, two executors.
    if (strain_on_.load(std::memory_order_relaxed) && strain_map_ != nullptr) {
        for (size_t r = 0; r < strain_vt_.size(); ++r) {
            const float s = strain_map_[strain_vt_[r]] * 10.f;   // SSBO value: mean strain per vert
            const float t = fminf(fabsf(s), 1.f);
            float* col = buf + (size_t)strain_vt_[r] * 9 + 6;
            if (s >= 0.f) {                            // stretch: toward red
                col[0] = fminf(col[0] + 0.55f * t, 1.f);
                col[1] = fminf(col[1] + 0.10f * t, 1.f);
                col[2] = fmaxf(col[2] - 0.55f * t, 0.f);
            } else {                                   // compression: toward blue
                col[0] = fmaxf(col[0] - 0.35f * t, 0.f);
                col[1] = fmaxf(col[1] - 0.10f * t, 0.f);
                col[2] = fminf(col[2] + 0.55f * t, 1.f);
            }
        }
    }
}

// Triangle area from the pose cache: each corner is either touched (posed
// position from posed_[rank*3 ..]) or rigid (its REST position from
// hinge_rest_ — a rigid corner does not move).
static inline float tri_area_posed(const uint32_t* tri, int32_t ra, int32_t rb, int32_t rc,
                                   const std::vector<float>& posed, const float* rest) {
    const float* A = (ra >= 0) ? &posed[(size_t)ra * 3] : rest + (size_t)tri[0] * 9;
    const float* B = (rb >= 0) ? &posed[(size_t)rb * 3] : rest + (size_t)tri[1] * 9;
    const float* C = (rc >= 0) ? &posed[(size_t)rc * 3] : rest + (size_t)tri[2] * 9;
    float ux = B[0] - A[0], uy = B[1] - A[1], uz = B[2] - A[2];
    float wx = C[0] - A[0], wy = C[1] - A[1], wz = C[2] - A[2];
    float cx = uy * wz - uz * wy, cy = uz * wx - ux * wz, cz = ux * wy - uy * wx;
    return 0.5f * sqrtf(cx * cx + cy * cy + cz * cz);
}

// THE STRAIN OVERLAY — true per-triangle area strain from the SAME analytic FK
// law the kernels execute, computed on the CPU with zero GPU readbacks:
//   1. pose the touched verts exactly as pose_hinge/hinge.comp do (Rodrigues
//      about the band's joint by theta * w);
//   2. area(A') of every triangle with >=1 touched vert;
//   3. e = area'/area_rest - 1 per triangle, scattered to its touched verts
//      by area weight (the vertex strain is the area-weighted mean of its
//      adjacent triangles' strain — the standard surface measure);
//   4. write the per-vertex scalar into the SSBO (0 = untouched/rest).
// The kernel (hinge.comp, flags bit1) converts scalar -> tint; ±10% saturates.
void Engine::compute_strain() {
    if (!strain_on_.load(std::memory_order_relaxed)) return;   // off: no work at all
    if (!hinge_active_ || strain_map_ == nullptr || mesh_tris_.empty()
        || tri_rest_area_.empty() || strain_vt_.empty()) return;

    const float t = hinge_time();
    float thL_deg, thR_deg;
    if (gait_on_.load(std::memory_order_relaxed) && gait_loaded_) {
        double tL, tR; gait_theta(tL, tR);
        thL_deg = static_cast<float>(tL); thR_deg = static_cast<float>(tR);
    } else {
        const float two_pi = 6.28318530718f;
        float ph = fmodf(t, hinge_period_) / hinge_period_;
        thL_deg = (0.5f - 0.5f * cosf(two_pi * ph)) * hinge_romL_;
        thR_deg = (0.5f - 0.5f * cosf(two_pi * ph + hinge_phaseR_)) * hinge_romR_;
    }
    if (volp_manual_.load(std::memory_order_relaxed)) {          // H13: same override as the pose paths
        thL_deg = volp_thL_.load(std::memory_order_relaxed);
        thR_deg = volp_thR_.load(std::memory_order_relaxed);
    }
    const float thL = thL_deg * 0.01745329251f, thR = thR_deg * 0.01745329251f;

    // 1. pose the touched verts (the compact domain — one Rodrigues each)
    const float ax = hinge_axis_[0], ay = hinge_axis_[1], az = hinge_axis_[2];
    const float* rest = hinge_rest_.data();
    for (size_t r = 0; r < strain_vt_.size(); ++r) {
        const uint32_t i = strain_vt_[r];
        const float wL = hinge_wL_[i], wR = hinge_wR_[i];
        const float th = thL * wL + thR * wR;
        const float* J = (wL >= wR) ? hinge_JL_ : hinge_JR_;
        const float c = cosf(th), s = sinf(th);
        const float* src = rest + (size_t)i * 9;
        const float vx = src[0] - J[0], vy = src[1] - J[1], vz = src[2] - J[2];
        const float cx = ay * vz - az * vy, cy = az * vx - ax * vz, cz = ax * vy - ay * vx;
        const float d = ax * vx + ay * vy + az * vz;
        strain_posed_[r * 3 + 0] = vx * c + cx * s + ax * d * (1.f - c) + J[0];
        strain_posed_[r * 3 + 1] = vy * c + cy * s + ay * d * (1.f - c) + J[1];
        strain_posed_[r * 3 + 2] = vz * c + cz * s + az * d * (1.f - c) + J[2];
    }

    // 2+3. per-triangle area strain, scattered to touched verts by area weight
    std::fill(strain_cnt_.begin(), strain_cnt_.end(), 0u);
    const size_t ntri = mesh_tris_.size() / 3;
    for (size_t tci = 0; tci < ntri; ++tci) {
        const uint32_t ia = mesh_tris_[tci * 3], ib = mesh_tris_[tci * 3 + 1], ic = mesh_tris_[tci * 3 + 2];
        const int32_t ra = strain_rank_[ia], rb = strain_rank_[ib], rc = strain_rank_[ic];
        if (ra < 0 && rb < 0 && rc < 0) continue;                 // rigid triangle: e = 0 exactly
        const float e = tri_area_posed(mesh_tris_.data() + tci * 3, ra, rb, rc,
                                       strain_posed_, rest)
                        / tri_rest_area_[tci] - 1.f;
        if (ra >= 0) { strain_acc_[ra] += e; ++strain_cnt_[ra]; }
        if (rb >= 0) { strain_acc_[rb] += e; ++strain_cnt_[rb]; }
        if (rc >= 0) { strain_acc_[rc] += e; ++strain_cnt_[rc]; }
    }
    // 4. area-weighted mean per touched vertex -> SSBO (0 stays untouched)
    for (size_t r = 0; r < strain_vt_.size(); ++r) {
        const float s = strain_cnt_[r] ? strain_acc_[r] / static_cast<float>(strain_cnt_[r]) : 0.f;
        strain_acc_[r] = 0.f;                                     // reset for the next frame
        strain_map_[strain_vt_[r]] = s;
    }
}

// ── THE GAIT CPG ON THE CA FIELD (H7 stage 2) ────────────────────────────────
// Port of .tmp/gait_ref.py (the golden CPU reference). Schedule: per engine
// tick, one workgroup of 8 invocations runs one fixed-order RK4 step
// (barrier-synced stages) and records the 8 phases into the ring. The hinge
// pose path reads thetaL/thetaR from the host-visible mirror the kernel
// maintains — the gait replaces the hinge's open-loop cosine clock.

static bool w_make_pipeline(VkDevice device, const char* spv_path, uint32_t n_bindings,
                            uint32_t pc_size, VkShaderModule& mod,
                            VkDescriptorSetLayout& dsl, VkPipelineLayout& layout,
                            VkPipeline& pipe);

void Engine::gait_theta(double& tL, double& tR) const {
    if (gait_theta_map_) {
        const volatile double* m = static_cast<const volatile double*>(gait_theta_map_);
        tL = m[0]; tR = m[1];
    } else {
        tL = tR = 0.0;
    }
}

// F1: the console's queue — the UI (or POST /console) hands a raw request
// line; the worker parses and executes it through main's api handler.
void Engine::console_exec(const std::string& line) {
    {
        std::lock_guard<std::mutex> lk(console_m_);
        console_q_.push(line);
    }
    console_cv_.notify_one();
}

// ── C4: THE OUTLINER ──
// scene_rows() is the ONE formatting site: the left dock draws exactly this,
// and GET /scene serves exactly this. Every row is composed from live engine
// state at read time — there is no stored row state to drift.
std::vector<StudioUI::SceneRow> Engine::scene_rows() {
    std::vector<StudioUI::SceneRow> rows;
    auto add = [&](const char* id, const char* label, const std::string& detail,
                   int state, bool toggleable) {
        StudioUI::SceneRow r; r.id = id; r.label = label; r.detail = detail;
        r.state = state; r.toggleable = toggleable; rows.push_back(std::move(r));
    };
    {
        char d[96]; snprintf(d, sizeof(d), has_mesh_ ? "%u tris, %u verts, r=%.1f" : "no mesh",
                             tri_idx_count_ / 3,
                             static_cast<unsigned>(mesh_cpu_.size() / 9),
                             g_mesh_sphere);
        add("body", "body", d, has_mesh_ ? 1 : 0, false);
    }
    add("overlay", "overlay", has_overlay_ ? "loaded" : "none", has_overlay_ ? 1 : 0, false);
    {
        char d[64]; snprintf(d, sizeof(d), "t=%.2fs x%.2f", show_time_.load(),
                             show_speed_.load());
        add("show", "show", d, show_playing_.load() ? 1 : 0, true);
    }
    {
        char d[64]; snprintf(d, sizeof(d), "%u joints", j_n_joints_);
        add("joints", "joints", d, joints_on_.load() != 0 ? 1 : 0, true);
    }
    {
        bool volp = volp_mode_.load() == 1;
        add("volp", "volp", volp_loaded() ? (volp ? "mode=volp" : "mode=blend") : "no kernel",
            volp ? 1 : 0, volp_loaded());
    }
    {
        char d[96]; snprintf(d, sizeof(d), "steps=%llu omega=%.2f",
                             (unsigned long long)gait_steps_total_.load(), gait_omega_.load());
        add("gait", "gait", d, gait_on_.load() ? 1 : 0, true);
    }
    {
        char d[96]; snprintf(d, sizeof(d), "steps_total=%llu inj=%d/%d",
                             (unsigned long long)water_clock_steps_total_.load(),
                             water_clock_inj_count_.load(), water_clock_inj_target_.load());
        add("water_clock", "water clock", d, water_clock_on_.load() ? 1 : 0, true);
    }
    add("water_vis", "water vis", "the field, drawn", water_vis_on_.load() ? 1 : 0, true);
    add("frost", "frost", frost_loaded_ ? "decode + render" : "no pack",
        frost_on_.load() ? 1 : 0, frost_loaded_);
    add("strain", "strain", hinge_active_ ? "area strain" : "no hinge",
        strain_on_.load() ? 1 : 0, hinge_active_);
    add("chrome", "chrome", "the studio bar", ui_.bar_on_ ? 1 : 0, true);
    return rows;
}

std::string Engine::scene_command(const std::string& id, bool on) {
    if (id == "show")        return std::string("POST /show {\"playing\":") + (on ? "true" : "false") + "}";
    if (id == "joints")      return std::string("POST /joints {\"on\":") + (on ? "true" : "false") + "}";
    if (id == "volp")        return std::string("POST /volp {\"mode\":\"") + (on ? "volp" : "blend") + "\"}";
    if (id == "gait")        return std::string("POST /gait {\"on\":") + (on ? "true" : "false") + "}";
    if (id == "water_clock") return std::string("POST /water_clock {\"on\":") + (on ? "true" : "false") + "}";
    if (id == "water_vis")   return std::string("POST /water_vis {\"on\":") + (on ? "true" : "false") + "}";
    if (id == "frost")       return std::string("POST /frost {\"on\":") + (on ? "true" : "false") + "}";
    if (id == "strain")      return std::string("POST /strain {\"on\":") + (on ? "true" : "false") + "}";
    if (id == "chrome")      return std::string("POST /studio_chrome {\"on\":") + (on ? "true" : "false") + "}";
    return "";
}

std::string Engine::scene_exec(const std::string& id, bool on) {
    std::string line = scene_command(id, on);
    if (!line.empty()) console_exec(line);
    return line;
}

void Engine::scene_toggle(int row) {
    std::vector<StudioUI::SceneRow> rows = scene_rows();   // FRESH state at click time
    if (row < 0 || row >= static_cast<int>(rows.size())) return;
    const StudioUI::SceneRow& r = rows[row];
    if (!r.toggleable) return;
    scene_exec(r.id, r.state == 0);
}

// ── C2: THE INSPECTOR's document — one formatting site for glass and twin ──
// Every value is read from the SAME atomics the named endpoint serves; the
// inspector holds no properties of its own, so it cannot drift or invent.
std::vector<std::pair<std::string, std::string>> Engine::inspect_kv(int row) {
    std::vector<std::pair<std::string, std::string>> kv;
    std::vector<StudioUI::SceneRow> rows = scene_rows();
    if (row < 0 || row >= static_cast<int>(rows.size())) return kv;
    const std::string& id = rows[row].id;
    auto add = [&](const char* k, const std::string& v) { kv.emplace_back(k, v); };
    auto b = [](bool v) { return v ? "true" : "false"; };
    char nb[96];
    if (id == "body") {
        add("mesh", b(has_mesh_));
        snprintf(nb, sizeof(nb), "%u", tri_idx_count_ / 3); add("tris", nb);
    } else if (id == "overlay") {
        add("loaded", b(has_overlay_));
        snprintf(nb, sizeof(nb), "%u", ov_idx_count_ / 3); add("tris", nb);
    } else if (id == "show") {
        double t = show_time_.load();
        uint32_t nj = show_joint_count();
        float per = show_period();
        uint32_t cur = nj ? static_cast<uint32_t>(t / per) % nj : 0;
        add("playing", b(show_playing_.load()));
        snprintf(nb, sizeof(nb), "%.3f s", t); add("time", nb);
        snprintf(nb, sizeof(nb), "%.2f", show_speed_.load()); add("speed", nb);
        snprintf(nb, sizeof(nb), "%u", nj); add("n_joints", nb);
        snprintf(nb, sizeof(nb), "%.3f s", per); add("period", nb);
        add("current", show_joint_name(cur));
        snprintf(nb, sizeof(nb), "%+.3f deg", show_current_theta()); add("theta", nb);
    } else if (id == "joints") {
        add("on", b(joints_on_.load() != 0));
        add("owner", joints_owner_.load(std::memory_order_relaxed) == 1 ? "edit" : "show");
        int sel = selected_joint_.load(std::memory_order_relaxed);
        add("selected", (sel >= 0 && sel < static_cast<int>(j_names_.size()))
                        ? j_names_[sel] : std::string("none"));
        snprintf(nb, sizeof(nb), "%u", j_n_joints_); add("n_joints", nb);
    } else if (id == "volp") {
        add("loaded", b(volp_loaded()));
        add("mode", volp_mode_.load() == 1 ? "volp" : "blend");
        add("manual", b(volp_manual_.load()));
        snprintf(nb, sizeof(nb), "%d", volp_M_.load()); add("M", nb);
        const float* st = volp_stats();
        if (st) { snprintf(nb, sizeof(nb), "%.6f", st[0]); add("dV", nb); }
    } else if (id == "gait") {
        double tL = 0, tR = 0; gait_theta(tL, tR);
        add("loaded", b(gait_loaded()));
        add("on", b(gait_on_.load()));
        snprintf(nb, sizeof(nb), "%d", gait_steps_per_frame_.load()); add("steps/frame", nb);
        snprintf(nb, sizeof(nb), "%.4f", gait_omega_.load()); add("omega", nb);
        snprintf(nb, sizeof(nb), "%llu", (unsigned long long)gait_steps_total_.load());
        add("steps_total", nb);
        snprintf(nb, sizeof(nb), "%+.4f", tL); add("thetaL", nb);
        snprintf(nb, sizeof(nb), "%+.4f", tR); add("thetaR", nb);
    } else if (id == "water_clock") {
        add("on", b(water_clock_on_.load()));
        snprintf(nb, sizeof(nb), "%d", water_clock_steps_per_frame_.load()); add("steps/frame", nb);
        snprintf(nb, sizeof(nb), "%d", water_clock_inj_target_.load()); add("inj_target", nb);
        snprintf(nb, sizeof(nb), "%d", water_clock_inj_count_.load()); add("inj_count", nb);
        snprintf(nb, sizeof(nb), "%llu", (unsigned long long)water_clock_steps_total_.load());
        add("steps_total", nb);
    } else if (id == "water_vis") {
        add("on", b(water_vis_on_.load()));
    } else if (id == "strain") {
        add("on", b(strain_on_.load()));
        snprintf(nb, sizeof(nb), "%zu", strain_vt_.size()); add("touched verts", nb);
        snprintf(nb, sizeof(nb), "%zu", tri_rest_area_.size()); add("triangles", nb);
        add("measure", "area strain, area-weighted mean");
        add("color", "blue = compress, red = stretch (+/-10% sat)");
    } else if (id == "frost") {
        add("loaded", b(frost_loaded_));
        add("on", b(frost_on_.load()));
        snprintf(nb, sizeof(nb), "%u", frost_tris()); add("n_tris", nb);
        snprintf(nb, sizeof(nb), "%llu", (unsigned long long)frost_frame_.load()); add("frame", nb);
    } else if (id == "chrome") {
        add("bar_on", b(ui_.bar_on_));
    }
    return kv;
}

// ── D6: CAMERA BOOKMARKS ──
// One engine-owned store; the glass chips and the /cameras twin both read it.
// Persistence is a flat file (name + 8 floats per line) in the CWD — the same
// discipline as the session logs; the served JSON twin is the formatting site.
static const char* CAM_MARKS_FILE = "camera_bookmarks.txt";
static const char* KEY_MARKS_FILE = "timeline_keymarks.txt";

// ── TIMELINE KEY MARKS (tool feature 4) — the camera-bookmark pattern on the
// live clock: a key is a NAME and a TIME; recall is a scrub. The pose is not
// stored (the clock IS the pose storage — replay the same law, get the same
// pose), so a key file is 30 bytes and cannot drift from the rig.
void Engine::key_marks_load() {
    std::lock_guard<std::mutex> lk(key_marks_m_);
    key_marks_.clear();
    FILE* f = fopen(KEY_MARKS_FILE, "r");
    if (!f) return;
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        char nm[64], jn[64] = ""; double t;
        int n = sscanf(line, "%63s %lf %63s", nm, &t, jn);
        if (n >= 2) {
            KeyMark k; k.name = nm; k.t = t; k.joint = (n >= 3) ? jn : "";
            key_marks_.push_back(k);
        }
    }
    fclose(f);
}

void Engine::key_marks_persist() {
    std::lock_guard<std::mutex> lk(key_marks_m_);
    FILE* f = fopen(KEY_MARKS_FILE, "w");
    if (!f) return;
    for (const auto& k : key_marks_)
        if (k.joint.empty())
            fprintf(f, "%s %.9f\n", k.name.c_str(), k.t);
        else
            fprintf(f, "%s %.9f %s\n", k.name.c_str(), k.t, k.joint.c_str());
    fclose(f);
}

std::string Engine::key_mark_save(const std::string& name, const std::string& joint) {
    double t = show_time_.load(std::memory_order_relaxed);
    std::string nm = name;
    {
        std::lock_guard<std::mutex> lk(key_marks_m_);
        if (nm.empty()) {
            int n = static_cast<int>(key_marks_.size()) + 1;
            char nb[32]; snprintf(nb, sizeof(nb), "key%d", n);
            nm = nb;
        }
        for (char& c : nm) if (c == ' ' || c == '\t') c = '_';
        for (auto& k : key_marks_)
            if (k.name == nm) { k.t = t; k.joint = joint; goto stored; }
        { KeyMark k; k.name = nm; k.t = t; k.joint = joint; key_marks_.push_back(k); }
        stored:;
    }
    key_marks_persist();
    return nm;
}

bool Engine::key_mark_delete(const std::string& name) {
    bool found = false;
    {
        std::lock_guard<std::mutex> lk(key_marks_m_);
        for (size_t i = 0; i < key_marks_.size(); ++i)
            if (key_marks_[i].name == name) {
                key_marks_.erase(key_marks_.begin() + i);
                found = true;
                break;
            }
    }
    if (found) key_marks_persist();
    return found;
}

bool Engine::key_mark_time(const std::string& name, double& out_t) {
    std::lock_guard<std::mutex> lk(key_marks_m_);
    for (const auto& k : key_marks_)
        if (k.name == name) { out_t = k.t; return true; }
    return false;
}

void Engine::key_marks_clear() {
    {
        std::lock_guard<std::mutex> lk(key_marks_m_);
        key_marks_.clear();
    }
    key_marks_persist();
}

std::vector<std::pair<std::string, double>> Engine::key_marks_list() {
    std::lock_guard<std::mutex> lk(key_marks_m_);
    std::vector<std::pair<std::string, double>> out;
    out.reserve(key_marks_.size());
    for (const auto& k : key_marks_) out.emplace_back(k.name, k.t);
    return out;   // copy-under-lock (C4's rule)
}

std::vector<Engine::KeyMarkInfo> Engine::key_marks_list_info() {
    std::lock_guard<std::mutex> lk(key_marks_m_);
    std::vector<KeyMarkInfo> out;
    out.reserve(key_marks_.size());
    for (const auto& k : key_marks_) out.push_back({k.name, k.t, k.joint});
    return out;
}

void Engine::cam_marks_load() {
    std::lock_guard<std::mutex> lk(cam_marks_m_);
    cam_marks_.clear();
    FILE* f = fopen(CAM_MARKS_FILE, "r");
    if (!f) return;
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        CamBookmark b;
        char nm[64];
        if (sscanf(line, "%63s %f %f %f %f %f %f %f %f", nm,
                   &b.v[0], &b.v[1], &b.v[2], &b.v[3], &b.v[4], &b.v[5],
                   &b.v[6], &b.v[7]) == 9) {
            b.name = nm;
            cam_marks_.push_back(b);
        }
    }
    fclose(f);
}

void Engine::cam_marks_persist() {
    std::lock_guard<std::mutex> lk(cam_marks_m_);
    FILE* f = fopen(CAM_MARKS_FILE, "w");
    if (!f) return;
    for (const auto& b : cam_marks_)
        fprintf(f, "%s %.9g %.9g %.9g %.9g %.9g %.9g %.9g %.9g\n", b.name.c_str(),
                b.v[0], b.v[1], b.v[2], b.v[3], b.v[4], b.v[5], b.v[6], b.v[7]);
    fclose(f);
}

std::string Engine::cam_mark_save(const std::string& name) {
    float v[8]; camera_state(v);
    std::string nm = name;
    {
        std::lock_guard<std::mutex> lk(cam_marks_m_);
        if (nm.empty()) {
            int n = static_cast<int>(cam_marks_.size()) + 1;
            char nb[32]; snprintf(nb, sizeof(nb), "cam%d", n);
            nm = nb;   // auto-name: the count is the derivation, no taste
        }
        for (char& c : nm) if (c == ' ' || c == '\t') c = '_';   // flat-file safe
        for (auto& b : cam_marks_)
            if (b.name == nm) { memcpy(b.v, v, sizeof(b.v)); goto saved; }
        { CamBookmark b; b.name = nm; memcpy(b.v, v, sizeof(b.v)); cam_marks_.push_back(b); }
        saved:;
    }
    cam_marks_persist();
    return nm;
}

bool Engine::cam_mark_save_exact(const std::string& name, const float v[8]) {
    if (name.empty()) return false;
    {
        std::lock_guard<std::mutex> lk(cam_marks_m_);
        std::string nm = name;
        for (char& c : nm) if (c == ' ' || c == '\t') c = '_';
        for (auto& b : cam_marks_)
            if (b.name == nm) { memcpy(b.v, v, sizeof(b.v)); goto stored; }
        { CamBookmark b; b.name = nm; memcpy(b.v, v, sizeof(b.v)); cam_marks_.push_back(b); }
        stored:;
    }
    cam_marks_persist();
    return true;
}

bool Engine::cam_mark_delete(const std::string& name) {
    bool found = false;
    {
        std::lock_guard<std::mutex> lk(cam_marks_m_);
        for (size_t i = 0; i < cam_marks_.size(); ++i)
            if (cam_marks_[i].name == name) {
                cam_marks_.erase(cam_marks_.begin() + i);
                found = true;
                break;
            }
    }
    if (found) cam_marks_persist();
    return found;
}

bool Engine::cam_mark_get(const std::string& name, float out[8]) {
    std::lock_guard<std::mutex> lk(cam_marks_m_);
    for (const auto& b : cam_marks_)
        if (b.name == name) { memcpy(out, b.v, sizeof(b.v)); return true; }
    return false;
}

std::vector<std::string> Engine::cam_mark_names() {
    std::lock_guard<std::mutex> lk(cam_marks_m_);
    std::vector<std::string> out;
    out.reserve(cam_marks_.size());
    for (const auto& b : cam_marks_) out.push_back(b.name);
    return out;
}

bool Engine::camera_fit(float out[8]) {
    // THE MESH IS THE TRUTH. The AABB comes from the same CPU copy the loaders
    // fill; the target is its center — a camera that targets the origin when the
    // subject stands on the floor crops exactly the feet the eye complained
    // about (2026-09-02). Radius is the bounding-sphere fit for the 45° FOV.
    if (mesh_cpu_.empty()) return false;
    float lo[3] = { 1e30f, 1e30f, 1e30f }, hi[3] = { -1e30f, -1e30f, -1e30f };
    for (size_t i = 0; i + 2 < mesh_cpu_.size(); i += 9) {
        for (int k = 0; k < 3; ++k) {
            float c = mesh_cpu_[i + k];
            if (c < lo[k]) lo[k] = c;
            if (c > hi[k]) hi[k] = c;
        }
    }
    // FIT v2 (2026-09-02, the eye's confirmation scan): the floor is part of
    // the composition. v1 centered the mesh's own AABB and framed the body
    // perfectly — feet 4 px from the viewport's bottom edge — while the floor
    // plane (y=0, where the contact shadow lives) fell out of frame below.
    // The grid is an unconditional instrument and the shadow sits ON it, so
    // the fit's box extends down to the floor whenever the body floats above:
    // the frame gains ground reference, derived from the scene law, not taste.
    if (lo[1] > 0.0f) lo[1] = 0.0f;
    float cx = 0.5f * (lo[0] + hi[0]), cy = 0.5f * (lo[1] + hi[1]), cz = 0.5f * (lo[2] + hi[2]);
    float dx = hi[0] - lo[0], dy = hi[1] - lo[1], dz = hi[2] - lo[2];
    float half_diag = 0.5f * sqrtf(dx * dx + dy * dy + dz * dz);
    // 45° vertical FOV: dist = r / sin(fov/2); +5% margin so no limb kisses the edge
    float dist = fmaxf(radius_floor(), half_diag / sinf(3.14159265f * 0.125f) * 1.05f);
    camera_state(out);
    out[0] = dist;
    out[3] = cx; out[4] = cy; out[5] = cz;
    out[6] = 0.f; out[7] = 0.f;
    return true;
}

void Engine::set_camera_full(const float v[8]) {
    g_cam.radius    = fmaxf(radius_floor(), v[0]);
    g_cam.theta     = v[1];
    g_cam.phi       = v[2];
    g_cam.target[0] = v[3]; g_cam.target[1] = v[4]; g_cam.target[2] = v[5];
    g_cam.pan_x     = v[6]; g_cam.pan_y     = v[7];
}

// ── D5: THE CAPTURE SESSION's document — one formatting site ──
std::vector<std::pair<std::string, std::string>> Engine::capture_kv() {
    std::vector<std::pair<std::string, std::string>> kv;
    auto add = [&](const char* k, const std::string& v) { kv.emplace_back(k, v); };
    char nb[96];
    int st = capture_state_.load();
    add("state", st == 0 ? "idle" : st == 1 ? "rendering" : st == 2 ? "done" : "FAILED");
    std::lock_guard<std::mutex> lk(cap_m_);
    if (!cap_name_.empty()) add("name", cap_name_);
    if (st != 0) {
        snprintf(nb, sizeof(nb), "%.3f .. %.3f s", cap_t0_, cap_t1_); add("range", nb);
        snprintf(nb, sizeof(nb), "%d", cap_fps_); add("fps", nb);
        if (!cap_camera_.empty()) add("camera", cap_camera_);
        snprintf(nb, sizeof(nb), "%d / %d", capture_done_.load(), capture_total_.load());
        add("frames", nb);
        snprintf(nb, sizeof(nb), "t = %.4f s", capture_t_.load()); add("last frame", nb);
        if (!cap_dir_.empty()) add("dir", cap_dir_);
        if (!cap_error_.empty()) add("error", cap_error_);
    }
    return kv;
}

int Engine::console_pending() {
    std::lock_guard<std::mutex> lk(console_m_);
    return static_cast<int>(console_q_.size());
}

void Engine::console_worker() {
    for (;;) {
        std::string line;
        {
            std::unique_lock<std::mutex> lk(console_m_);
            console_cv_.wait(lk, [&] { return console_stop_ || !console_q_.empty(); });
            if (console_stop_) return;
            line = console_q_.front();
            console_q_.pop();
        }
        // parse: METHOD SP /path [SP json...]
        std::string method, path, req_body, resp = "", ctype = "application/json";
        size_t a = line.find_first_not_of(" \t");
        size_t sp = a == std::string::npos ? a : line.find_first_of(" \t", a);
        method = line.substr(a, sp == std::string::npos ? sp : sp - a);
        size_t p0 = sp == std::string::npos ? sp : line.find_first_not_of(" \t", sp);
        size_t p1 = p0 == std::string::npos ? p0 : line.find_first_of(" \t", p0);
        path = p0 == std::string::npos ? "" : line.substr(p0, p1 == std::string::npos ? p1 : p1 - p0);
        if (p1 != std::string::npos) {
            size_t b0 = line.find_first_not_of(" \t", p1);
            if (b0 != std::string::npos) req_body = line.substr(b0);
        }
        for (auto& c : method) c = static_cast<char>(toupper(static_cast<unsigned char>(c)));
        ApiFn api;
        {
            std::lock_guard<std::mutex> lk(console_m_);
            api = api_;
        }
        if (path.empty() || path[0] != '/') {
            resp = "console: want `METHOD /path [json]` — e.g. GET /studio";
        } else if ((method == "GET" || method == "POST") && api) {
            api(method, path, req_body, resp, ctype);   // the HTTP server's own handler
        } else if (!api) {
            resp = "console: no api handler wired";
        } else {
            resp = "console: method must be GET or POST";
        }
        {
            std::lock_guard<std::mutex> lk(console_m_);
            console_done_.push_back(resp);
        }
    }
}

void Engine::console_drain() {
    std::vector<std::string> done;
    {
        std::lock_guard<std::mutex> lk(console_m_);
        done.swap(console_done_);
    }
    for (const std::string& r : done) ui_.console_result(r);
}

// ── F4: the recorder ─────────────────────────────────────────────────────────
// One JSON line per event, at the moment it happens, to the session file AND
// the LOG dock's ring — same bytes, same order. The file is the record; the
// ring is only its tail view.
static std::string log_jesc(const std::string& s) {
    std::string o; o.reserve(s.size() + 8);
    for (char c : s) {
        switch (c) {
            case '"':  o += "\\\""; break;
            case '\\': o += "\\\\"; break;
            case '\n': o += "\\n";  break;
            case '\r': o += "\\r";  break;
            case '\t': o += "\\t";  break;
            default:   o += c;
        }
    }
    return o;
}

void Engine::log_event(const std::string& kind, const std::string& detail) {
    // wall-clock timestamp, millisecond precision
    using namespace std::chrono;
    auto now_tp  = system_clock::now();
    auto ms      = duration_cast<milliseconds>(now_tp.time_since_epoch()) % 1000;
    std::time_t now = system_clock::to_time_t(now_tp);
    std::tm tmv{}; localtime_s(&tmv, &now);
    char tbuf[32];
    snprintf(tbuf, sizeof(tbuf), "%04d-%02d-%02dT%02d:%02d:%02d.%03d",
             tmv.tm_year + 1900, tmv.tm_mon + 1, tmv.tm_mday,
             tmv.tm_hour, tmv.tm_min, tmv.tm_sec, (int)ms.count());
    std::string tstr = tbuf;

    uint64_t seq;
    {
        std::lock_guard<std::mutex> lk(log_m_);
        seq = ++log_seq_;
        if (log_fp_) {
            fprintf(log_fp_, "{\"seq\":%llu,\"t\":\"%s\",\"kind\":\"%s\",\"detail\":\"%s\"}\n",
                    (unsigned long long)seq, tstr.c_str(),
                    log_jesc(kind).c_str(), log_jesc(detail).c_str());
            fflush(log_fp_);   // a line on disk the moment it happens, not on exit
        }
    }
    ui_.log_push(seq, seq, tstr, kind, detail);   // the stream sees the same line
}

// F3: the chrome's HUD rows, pushed from the engine's own state. The gait
// row's lam is the Owaki surrogate s = max(0, -sin phi), derived by inverting
// the G1 map on the SAME theta mirror the hinge pose reads — the shader's own
// load term, no new GPU channel. (G3 real contact load is still blocked
// upstream — the row says "surrogate" on its face.)
void Engine::push_hud_state() {
    if (gait_on_.load(std::memory_order_relaxed) && gait_loaded_) {
        double tL, tR; gait_theta(tL, tR);
        double sL = gait_tha_l_ != 0.0 ? (tL - gait_thm_l_) / gait_tha_l_ : 0.0;
        double sR = gait_tha_r_ != 0.0 ? (tR - gait_thm_r_) / gait_tha_r_ : 0.0;
        double lamL = (-sL) > 0.0 ? -sL : 0.0;   // lam = max(0, -sin phi)
        double lamR = (-sR) > 0.0 ? -sR : 0.0;
        ui_.set_gait_hud(true, lamL, lamR, tL, tR,
                         gait_steps_total_.load(std::memory_order_relaxed),
                         gait_omega_.load(std::memory_order_relaxed));
    } else {
        ui_.set_gait_hud(false, 0, 0, 0, 0, 0, 0);
    }
    if (water_clock_on_.load(std::memory_order_relaxed) && water_loaded_) {
        ui_.set_water_hud(true,
                          water_clock_steps_total_.load(std::memory_order_relaxed),
                          water_clock_dt_.load(std::memory_order_relaxed),
                          water_clock_inj_target_.load(std::memory_order_relaxed),
                          water_clock_inj_count_.load(std::memory_order_relaxed));
    } else {
        ui_.set_water_hud(false, 0, 0, -1, 0);
    }
}

bool Engine::load_gait(const std::vector<double>& consts, const std::vector<int32_t>& edges,
                       const double phi0[8], const double theta0[2]) {
    if (consts.size() < 37 || edges.size() < 16) {
        fprintf(stderr, "gait: bad setup (%zu consts, %zu edges)\n", consts.size(), edges.size());
        return false;
    }
    // F3: keep the G1 map constants host-side so the HUD's lam row derives
    // from the theta mirror (consts layout: 25 THM_L 26 THA_L 27 THM_R 28 THA_R)
    gait_thm_l_ = consts[25]; gait_tha_l_ = consts[26];
    gait_thm_r_ = consts[27]; gait_tha_r_ = consts[28];
    vkDeviceWaitIdle(device_);

    upload_buffer(consts.data(), consts.size() * sizeof(double),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, gait_consts_buf_, gait_consts_mem_);
    upload_buffer(edges.data(), edges.size() * sizeof(int32_t),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, gait_edges_buf_, gait_edges_mem_);
    upload_buffer(phi0, 8 * sizeof(double),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, gait_phase_buf_, gait_phase_mem_);

    // record ring (device-local) + host-visible readback
    VkDeviceSize ring_sz = static_cast<VkDeviceSize>(gait_ring_cap_) * 8 * sizeof(double);
    {
        std::vector<double> zeros(static_cast<size_t>(gait_ring_cap_) * 8, 0.0);
        upload_buffer(zeros.data(), ring_sz,
                      VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                      gait_ring_buf_, gait_ring_mem_);
    }
    {
        VkBufferCreateInfo bci{};
        bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size = ring_sz;
        bci.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        if (gait_ring_rb_buf_) { if (gait_ring_rb_map_) vkUnmapMemory(device_, gait_ring_rb_mem_);
                                 vkDestroyBuffer(device_, gait_ring_rb_buf_, nullptr);
                                 vkFreeMemory(device_, gait_ring_rb_mem_, nullptr); }
        vkCreateBuffer(device_, &bci, nullptr, &gait_ring_rb_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, gait_ring_rb_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &gait_ring_rb_mem_);
        vkBindBufferMemory(device_, gait_ring_rb_buf_, gait_ring_rb_mem_, 0);
        vkMapMemory(device_, gait_ring_rb_mem_, 0, ring_sz, 0, &gait_ring_rb_map_);
    }
    // theta mirror: host-visible coherent, the kernel writes it every step
    {
        VkBufferCreateInfo bci{};
        bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size = 16;
        bci.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        if (gait_theta_buf_) { if (gait_theta_map_) vkUnmapMemory(device_, gait_theta_mem_);
                               vkDestroyBuffer(device_, gait_theta_buf_, nullptr);
                               vkFreeMemory(device_, gait_theta_mem_, nullptr); }
        vkCreateBuffer(device_, &bci, nullptr, &gait_theta_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, gait_theta_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &gait_theta_mem_);
        vkBindBufferMemory(device_, gait_theta_buf_, gait_theta_mem_, 0);
        vkMapMemory(device_, gait_theta_mem_, 0, 16, 0, &gait_theta_map_);
        std::memcpy(gait_theta_map_, theta0, 16);   // theta(phi0): no snap-to-rest on enable
    }

    if (!w_make_pipeline(device_, "shaders/gait.spv", 5, 16,
                         gait_mod_, gait_desc_layout_, gait_layout_, gait_pipe_)) return false;
    {
        VkDescriptorPoolSize ps{};
        ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        ps.descriptorCount = 5;
        VkDescriptorPoolCreateInfo dpci{};
        dpci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
        dpci.maxSets = 1;
        dpci.poolSizeCount = 1;
        dpci.pPoolSizes = &ps;
        vkCreateDescriptorPool(device_, &dpci, nullptr, &gait_desc_pool_);
        VkDescriptorSetAllocateInfo dsai{};
        dsai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        dsai.descriptorPool = gait_desc_pool_;
        dsai.descriptorSetCount = 1;
        dsai.pSetLayouts = &gait_desc_layout_;
        vkAllocateDescriptorSets(device_, &dsai, &gait_desc_set_);

        VkDescriptorBufferInfo infos[5] = {};
        infos[0].buffer = gait_consts_buf_; infos[0].range = VK_WHOLE_SIZE;
        infos[1].buffer = gait_edges_buf_;  infos[1].range = VK_WHOLE_SIZE;
        infos[2].buffer = gait_phase_buf_;  infos[2].range = VK_WHOLE_SIZE;
        infos[3].buffer = gait_ring_buf_;   infos[3].range = VK_WHOLE_SIZE;
        infos[4].buffer = gait_theta_buf_;  infos[4].range = VK_WHOLE_SIZE;
        VkWriteDescriptorSet w[5] = {};
        for (int k = 0; k < 5; ++k) {
            w[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            w[k].dstSet = gait_desc_set_;
            w[k].dstBinding = k;
            w[k].descriptorCount = 1;
            w[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            w[k].pBufferInfo = &infos[k];
        }
        vkUpdateDescriptorSets(device_, 5, w, 0, nullptr);
    }
    gait_steps_total_.store(0);
    gait_loaded_ = true;
    printf("Gait CPG loaded: 8 oscillators, ring cap %u steps\n", gait_ring_cap_);
    return true;
}

bool Engine::gait_download(std::vector<double>& out_ring) {
    if (!gait_loaded_) return false;
    VkDeviceSize ring_sz = static_cast<VkDeviceSize>(gait_ring_cap_) * 8 * sizeof(double);
    vkDeviceWaitIdle(device_);
    VkCommandBuffer cb = begin_single_time_cmd();
    VkBufferCopy bc{}; bc.size = ring_sz;
    vkCmdCopyBuffer(cb, gait_ring_buf_, gait_ring_rb_buf_, 1, &bc);
    end_single_time_cmd(cb);
    out_ring.resize(static_cast<size_t>(gait_ring_cap_) * 8);
    std::memcpy(out_ring.data(), gait_ring_rb_map_, ring_sz);
    return true;
}

// ── VOLP-ARAP KNEE KERNEL (H13) ─────────────────────────────────────────────
// Blob layout (built by .tmp/volp_pack.py — the engine only consumes):
//   [u32 'VOLP'][u32 version=2][64 u32 directory][ublob u32 * hd[6]][fblob f32 * hd[7]]
// directory: counts at 0..7, f32 offsets 8..23, u32 offsets 24..47.
bool Engine::load_volp(const std::vector<uint8_t>& blob) {
    if (blob.size() < 8 + 256) { fprintf(stderr, "volp: short blob\n"); return false; }
    const uint8_t* d = blob.data();
    uint32_t magic, version;
    std::memcpy(&magic, d, 4); std::memcpy(&version, d + 4, 4);
    if (magic != 0x564F4C50u || version != 2) {
        fprintf(stderr, "volp: bad magic/version (%08x v%u)\n", magic, version); return false;
    }
    std::vector<uint32_t> hd(64);
    std::memcpy(hd.data(), d + 8, 256);
    volp_NF_ = hd[0]; volp_NC_ = hd[1];
    uint64_t nu = hd[6], nf = hd[7];
    size_t expect = 8 + 256 + static_cast<size_t>(nu) * 4 + static_cast<size_t>(nf) * 4;
    if (blob.size() != expect || volp_NF_ == 0 || volp_NC_ == 0) {
        fprintf(stderr, "volp: size mismatch (%zu vs %zu)\n", blob.size(), expect); return false;
    }
    if (tri_vbuf_ == VK_NULL_HANDLE) { fprintf(stderr, "volp: no mesh\n"); return false; }
    vkDeviceWaitIdle(device_);
    const uint8_t* udata = d + 8 + 256;
    const uint8_t* fdata = udata + static_cast<size_t>(nu) * 4;

    upload_buffer(hd.data(), 256, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, volp_hdr_buf_, volp_hdr_mem_);
    upload_buffer(udata, nu * 4, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, volp_u_buf_, volp_u_mem_);
    upload_buffer(fdata, nf * 4, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, volp_f_buf_, volp_f_mem_);
    // X state buffer, initialised from the packed X0 (fblob offset hd[22])
    const float* x0 = reinterpret_cast<const float*>(fdata) + hd[22];
    upload_buffer(x0, static_cast<size_t>(volp_NC_) * 3 * sizeof(float),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                  volp_x_buf_, volp_x_mem_);
    // scratch: 12*NC + 18*NF floats (shader layout) — upload_buffer memcpys
    // unconditionally, so stage zeros (nullptr + size crashed the live engine)
    {
        std::vector<float> zeros(static_cast<size_t>(12 * volp_NC_ + 18 * volp_NF_), 0.f);
        upload_buffer(zeros.data(), zeros.size() * sizeof(float),
                      VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, volp_sc_buf_, volp_sc_mem_);
    }
    // stats mirror: host-visible coherent f32[16]
    {
        if (volp_st_buf_) { if (volp_stats_map_) vkUnmapMemory(device_, volp_st_mem_);
                            vkDestroyBuffer(device_, volp_st_buf_, nullptr);
                            vkFreeMemory(device_, volp_st_mem_, nullptr); volp_stats_map_ = nullptr; }
        VkBufferCreateInfo bci{};
        bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size = 16 * sizeof(float);
        bci.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &volp_st_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, volp_st_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &volp_st_mem_);
        vkBindBufferMemory(device_, volp_st_buf_, volp_st_mem_, 0);
        vkMapMemory(device_, volp_st_mem_, 0, 16 * sizeof(float), 0, &volp_stats_map_);
        std::memset(volp_stats_map_, 0, 16 * sizeof(float));
    }
    // mesh readback buffer (debug endpoint): full vertex buffer, host-visible
    {
        if (volp_rb_buf_) { vkDestroyBuffer(device_, volp_rb_buf_, nullptr);
                            vkFreeMemory(device_, volp_rb_mem_, nullptr); }
        VkDeviceSize sz = static_cast<VkDeviceSize>(hinge_rest_.size()) * sizeof(float);
        VkBufferCreateInfo bci{};
        bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size = sz;
        bci.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &volp_rb_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, volp_rb_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &volp_rb_mem_);
        vkBindBufferMemory(device_, volp_rb_buf_, volp_rb_mem_, 0);
    }

    if (!w_make_pipeline(device_, "shaders/volp.spv", 7, 16,
                         volp_mod_, volp_desc_layout_, volp_layout_, volp_pipe_)) return false;
    {
        VkDescriptorPoolSize ps{};
        ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        ps.descriptorCount = 7;
        VkDescriptorPoolCreateInfo dpci{};
        dpci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
        dpci.maxSets = 1;
        dpci.poolSizeCount = 1;
        dpci.pPoolSizes = &ps;
        vkCreateDescriptorPool(device_, &dpci, nullptr, &volp_desc_pool_);
        VkDescriptorSetAllocateInfo dsai{};
        dsai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        dsai.descriptorPool = volp_desc_pool_;
        dsai.descriptorSetCount = 1;
        dsai.pSetLayouts = &volp_desc_layout_;
        vkAllocateDescriptorSets(device_, &dsai, &volp_desc_set_);
        VkDescriptorBufferInfo infos[7] = {};
        infos[0].buffer = volp_hdr_buf_; infos[0].range = VK_WHOLE_SIZE;
        infos[1].buffer = volp_u_buf_;   infos[1].range = VK_WHOLE_SIZE;
        infos[2].buffer = volp_f_buf_;   infos[2].range = VK_WHOLE_SIZE;
        infos[3].buffer = volp_x_buf_;   infos[3].range = VK_WHOLE_SIZE;
        infos[4].buffer = volp_sc_buf_;  infos[4].range = VK_WHOLE_SIZE;
        infos[5].buffer = volp_st_buf_;  infos[5].range = VK_WHOLE_SIZE;
        infos[6].buffer = tri_vbuf_;     infos[6].range = VK_WHOLE_SIZE;
        VkWriteDescriptorSet w[7] = {};
        for (int k = 0; k < 7; ++k) {
            w[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            w[k].dstSet = volp_desc_set_;
            w[k].dstBinding = k;
            w[k].descriptorCount = 1;
            w[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            w[k].pBufferInfo = &infos[k];
        }
        vkUpdateDescriptorSets(device_, 7, w, 0, nullptr);
    }
    volp_cold_.store(true);
    volp_last_thL_ = volp_last_thR_ = 0.f;
    volp_loaded_ = true;
    printf("Volp-ARAP loaded: NF %u NC %u (the H13 knee kernel)\n", volp_NF_, volp_NC_);
    return true;
}

bool Engine::volp_download_mesh(std::vector<float>& out) {
    if (!volp_loaded_ || hinge_rest_.empty()) return false;
    VkDeviceSize sz = static_cast<VkDeviceSize>(hinge_rest_.size()) * sizeof(float);
    vkDeviceWaitIdle(device_);
    VkCommandBuffer cb = begin_single_time_cmd();
    VkBufferCopy bc{}; bc.size = sz;
    vkCmdCopyBuffer(cb, tri_vbuf_, volp_rb_buf_, 1, &bc);
    end_single_time_cmd(cb);
    void* p = nullptr;
    vkMapMemory(device_, volp_rb_mem_, 0, sz, 0, &p);
    out.resize(hinge_rest_.size());
    std::memcpy(out.data(), p, sz);
    vkUnmapMemory(device_, volp_rb_mem_);
    return true;
}

// ── THE WATER SOLVER ON THE CA FIELD (B15) ──────────────────────────────────
// Port of .tmp/tri_water.py (the golden CPU reference, B7). Schedule: per
// macro step [inject+depth pre-pass] -> [per-color Gauss-Seidel dispatches in
// canonical color order, barrier-separated] -> [occ zero post-pass] -> [record
// V into the states buffer for readback]. float64 math everywhere, integer
// volumes, roundEven == np.rint, R1 clamp — the same law, bit-for-bit.

static bool w_make_pipeline(VkDevice device, const char* spv_path, uint32_t n_bindings,
                            uint32_t pc_size, VkShaderModule& mod,
                            VkDescriptorSetLayout& dsl, VkPipelineLayout& layout,
                            VkPipeline& pipe) {
    std::vector<char> spv = read_file(spv_path);
    if (spv.empty()) { fprintf(stderr, "water: %s missing\n", spv_path); return false; }
    VkShaderModuleCreateInfo smci{};
    smci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    smci.codeSize = spv.size();
    smci.pCode = reinterpret_cast<const uint32_t*>(spv.data());
    vkCreateShaderModule(device, &smci, nullptr, &mod);

    std::vector<VkDescriptorSetLayoutBinding> b(n_bindings);
    for (uint32_t k = 0; k < n_bindings; ++k) {
        b[k].binding = k;
        b[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        b[k].descriptorCount = 1;
        b[k].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    }
    VkDescriptorSetLayoutCreateInfo dlci{};
    dlci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dlci.bindingCount = n_bindings;
    dlci.pBindings = b.data();
    vkCreateDescriptorSetLayout(device, &dlci, nullptr, &dsl);

    VkPushConstantRange pcr{};
    pcr.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    pcr.offset = 0;
    pcr.size = pc_size;
    VkPipelineLayoutCreateInfo plci{};
    plci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    plci.setLayoutCount = 1;
    plci.pSetLayouts = &dsl;
    plci.pushConstantRangeCount = pc_size ? 1u : 0u;
    plci.pPushConstantRanges = pc_size ? &pcr : nullptr;
    vkCreatePipelineLayout(device, &plci, nullptr, &layout);

    VkComputePipelineCreateInfo cpci{};
    cpci.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
    cpci.stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    cpci.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    cpci.stage.module = mod;
    cpci.stage.pName = "main";
    cpci.layout = layout;
    VkResult pr = vkCreateComputePipelines(device, VK_NULL_HANDLE, 1, &cpci, nullptr, &pipe);
    if (pr != VK_SUCCESS) fprintf(stderr, "water: pipeline %s failed (%d)\n", spv_path, (int)pr);
    return pr == VK_SUCCESS;
}

bool Engine::load_water(const WaterUpload& up) {
    vkDeviceWaitIdle(device_);
    w_n_cells_ = up.n_cells; w_n_edges_ = up.n_edges; w_n_colors_ = up.n_colors;
    w_Q_ = up.Q; w_G_ = up.G; w_c_local_ = up.c_local;
    w_color_start_ = up.color_start;
    w_inj_ = up.inj;

    // buffers (V0 + q_e zeroed via initial upload)
    upload_buffer(up.V0.data(), up.V0.size() * sizeof(int32_t),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT, w_V_buf_, w_V_mem_);
    upload_buffer(up.areas.data(), up.areas.size() * sizeof(double),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, w_areas_buf_, w_areas_mem_);
    upload_buffer(up.bed.data(), up.bed.size() * sizeof(double),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, w_bed_buf_, w_bed_mem_);
    upload_buffer(up.eij.data(), up.eij.size() * sizeof(int32_t),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, w_eij_buf_, w_eij_mem_);
    upload_buffer(up.k_e.data(), up.k_e.size() * sizeof(double),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, w_ke_buf_, w_ke_mem_);
    upload_buffer(up.l_ij.data(), up.l_ij.size() * sizeof(double),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, w_lij_buf_, w_lij_mem_);
    upload_buffer(up.edge_active.data(), up.edge_active.size() * sizeof(uint32_t),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, w_eactive_buf_, w_eactive_mem_);
    std::vector<double> zeros_d(up.n_edges, 0.0);
    upload_buffer(zeros_d.data(), zeros_d.size() * sizeof(double),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, w_qe_buf_, w_qe_mem_);
    std::vector<double> zeros_c(up.n_cells, 0.0);
    upload_buffer(zeros_c.data(), zeros_c.size() * sizeof(double),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, w_depth_buf_, w_depth_mem_);
    upload_buffer(up.occ.data(), up.occ.size() * sizeof(uint32_t),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, w_occ_buf_, w_occ_mem_);

    // states buffer (cap 64 macro steps + the initial state) + host readback
    w_states_cap_ = 65;
    VkDeviceSize states_sz = static_cast<VkDeviceSize>(w_states_cap_) * up.n_cells * sizeof(int32_t);
    {
        VkBufferCreateInfo bci{};
        bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size = states_sz;
        bci.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        if (w_states_buf_) { vkDestroyBuffer(device_, w_states_buf_, nullptr); vkFreeMemory(device_, w_states_mem_, nullptr); }
        vkCreateBuffer(device_, &bci, nullptr, &w_states_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, w_states_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &w_states_mem_);
        vkBindBufferMemory(device_, w_states_buf_, w_states_mem_, 0);
    }
    {
        if (w_readback_buf_) { if (w_readback_map_) vkUnmapMemory(device_, w_readback_mem_); vkDestroyBuffer(device_, w_readback_buf_, nullptr); vkFreeMemory(device_, w_readback_mem_, nullptr); }
        VkBufferCreateInfo bci{};
        bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size = states_sz;
        bci.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &w_readback_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, w_readback_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &w_readback_mem_);
        vkBindBufferMemory(device_, w_readback_buf_, w_readback_mem_, 0);
        vkMapMemory(device_, w_readback_mem_, 0, states_sz, 0, &w_readback_map_);
    }

    // pipelines
    if (!w_make_pipeline(device_, "shaders/water_depth.spv", 3, 24, w_depth_mod_, w_depth_dsl_, w_depth_layout_, w_depth_pipe_)) return false;
    if (!w_make_pipeline(device_, "shaders/water_color.spv", 9, 48, w_color_mod_, w_color_dsl_, w_color_layout_, w_color_pipe_)) return false;
    if (!w_make_pipeline(device_, "shaders/water_occ.spv", 2, 8, w_occ_mod_, w_occ_dsl_, w_occ_layout_, w_occ_pipe_)) return false;
    // W4 surface displacement (optional: the solver must not depend on the vis path)
    if (!w_make_pipeline(device_, "shaders/water_vis.spv", 6, 24, w_vis_mod_, w_vis_dsl_, w_vis_layout_, w_vis_pipe_)) {
        fprintf(stderr, "water_vis: pipeline missing — vis disabled, solver unaffected\n");
        w_vis_pipe_ = VK_NULL_HANDLE;
    }

    // W4 vis buffers: 3 verts (9 floats each) per potentially-wet cell + the
    // indirect-draw command ({vertexCount=0, instanceCount=1, 0, 0} — frame()
    // refills vertexCount via vkCmdFillBuffer; upload_buffer adds TRANSFER_DST).
    w_vis_cap_verts_ = 3 * up.n_cells;
    if (w_vis_pipe_ != VK_NULL_HANDLE) {
        std::vector<float> vzeros(static_cast<size_t>(w_vis_cap_verts_) * 9, 0.0f);
        upload_buffer(vzeros.data(), vzeros.size() * sizeof(float),
                      VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
                      w_vis_vbuf_, w_vis_vmem_);
        uint32_t ind_init[4] = { 0, 1, 0, 0 };
        upload_buffer(ind_init, sizeof(ind_init),
                      VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT,
                      w_vis_indirect_buf_, w_vis_indirect_mem_);
    }

    // descriptor pool + sets
    VkDescriptorPoolSize ps{};
    ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    ps.descriptorCount = 20;
    if (w_desc_pool_) vkDestroyDescriptorPool(device_, w_desc_pool_, nullptr);
    VkDescriptorPoolCreateInfo dpci{};
    dpci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dpci.maxSets = 4;
    dpci.poolSizeCount = 1;
    dpci.pPoolSizes = &ps;
    vkCreateDescriptorPool(device_, &dpci, nullptr, &w_desc_pool_);
    VkDescriptorSetLayout dsls[4] = { w_depth_dsl_, w_color_dsl_, w_occ_dsl_, w_vis_dsl_ };
    VkDescriptorSet sets[4];
    uint32_t n_sets = (w_vis_pipe_ != VK_NULL_HANDLE) ? 4 : 3;
    VkDescriptorSetAllocateInfo dsai{};
    dsai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dsai.descriptorPool = w_desc_pool_;
    dsai.descriptorSetCount = n_sets;
    dsai.pSetLayouts = dsls;
    vkAllocateDescriptorSets(device_, &dsai, sets);
    w_depth_set_ = sets[0]; w_color_set_ = sets[1]; w_occ_set_ = sets[2];
    w_vis_set_ = (n_sets == 4) ? sets[3] : VK_NULL_HANDLE;
    water_vis_desc_dirty_ = true;   // mesh buffers not (yet) bound -> lazy rebind in frame()

    auto bind = [&](VkDescriptorSet set, uint32_t binding, VkBuffer buf) {
        VkDescriptorBufferInfo info{};
        info.buffer = buf; info.range = VK_WHOLE_SIZE;
        VkWriteDescriptorSet w{};
        w.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w.dstSet = set; w.dstBinding = binding; w.descriptorCount = 1;
        w.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        w.pBufferInfo = &info;
        vkUpdateDescriptorSets(device_, 1, &w, 0, nullptr);
    };
    bind(w_depth_set_, 0, w_V_buf_); bind(w_depth_set_, 1, w_areas_buf_); bind(w_depth_set_, 2, w_depth_buf_);
    bind(w_color_set_, 0, w_V_buf_); bind(w_color_set_, 1, w_areas_buf_); bind(w_color_set_, 2, w_depth_buf_);
    bind(w_color_set_, 3, w_bed_buf_); bind(w_color_set_, 4, w_eij_buf_); bind(w_color_set_, 5, w_ke_buf_);
    bind(w_color_set_, 6, w_lij_buf_); bind(w_color_set_, 7, w_qe_buf_);
    bind(w_color_set_, 8, w_eactive_buf_);
    bind(w_occ_set_, 0, w_V_buf_); bind(w_occ_set_, 1, w_occ_buf_);

    if (w_fence_ == VK_NULL_HANDLE) {
        VkFenceCreateInfo fi{};
        fi.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
        fi.flags = VK_FENCE_CREATE_SIGNALED_BIT;
        vkCreateFence(device_, &fi, nullptr, &w_fence_);
    }

    // record the initial state (states[0] = V0)
    {
        VkCommandBuffer cb = begin_single_time_cmd();
        VkBufferCopy bc{};
        bc.size = up.V0.size() * sizeof(int32_t);
        vkCmdCopyBuffer(cb, w_V_buf_, w_states_buf_, 1, &bc);
        end_single_time_cmd(cb);
    }
    w_states_n_ = 1;
    water_loaded_ = true;
    printf("Water loaded: %u cells, %u edges, %u colors, %zu injections\n",
           w_n_cells_, w_n_edges_, w_n_colors_, w_inj_.size() / 2);
    return true;
}

void Engine::water_record_macro_step(VkCommandBuffer cb, double dt_macro,
                                     int32_t inj_target, int32_t inj_count) {
    auto barrier = [&]() {
        VkMemoryBarrier mb{};
        mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT;
        vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                             VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0, 1, &mb, 0, nullptr, 0, nullptr);
    };

    // 1. inject + depth pre-pass
    struct { double Q; uint32_t n; int32_t inj_target, inj_count; uint32_t pad; } dpc{};
    dpc.Q = w_Q_; dpc.n = w_n_cells_; dpc.inj_target = inj_target; dpc.inj_count = inj_count;
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_COMPUTE, w_depth_pipe_);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_COMPUTE, w_depth_layout_, 0, 1, &w_depth_set_, 0, nullptr);
    vkCmdPushConstants(cb, w_depth_layout_, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(dpc), &dpc);
    vkCmdDispatch(cb, (w_n_cells_ + 255) / 256, 1, 1);
    barrier();

    // 2. per-color Gauss-Seidel dispatches in canonical color order
    for (uint32_t c = 0; c < w_n_colors_; ++c) {
        uint32_t e0 = w_color_start_[c], e1 = w_color_start_[c + 1];
        if (e1 <= e0) continue;
        struct { double dt, Q, g, cl; uint32_t off, tot, end, p1; } cpc{};
        cpc.dt = dt_macro; cpc.Q = w_Q_; cpc.g = w_G_; cpc.cl = w_c_local_;
        cpc.off = e0; cpc.tot = w_n_edges_; cpc.end = e1;
        vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_COMPUTE, w_color_pipe_);
        vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_COMPUTE, w_color_layout_, 0, 1, &w_color_set_, 0, nullptr);
        vkCmdPushConstants(cb, w_color_layout_, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(cpc), &cpc);
        vkCmdDispatch(cb, (e1 - e0 + 255) / 256, 1, 1);
        barrier();
    }

    // 3. occ zero post-pass
    struct { uint32_t n, pad; } opc{};
    opc.n = w_n_cells_;
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_COMPUTE, w_occ_pipe_);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_COMPUTE, w_occ_layout_, 0, 1, &w_occ_set_, 0, nullptr);
    vkCmdPushConstants(cb, w_occ_layout_, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(opc), &opc);
    vkCmdDispatch(cb, (w_n_cells_ + 255) / 256, 1, 1);
    barrier();
}

bool Engine::water_run(uint32_t n_macro, double dt_macro, int64_t& sum_out, int64_t& min_out) {
    if (!water_loaded_) return false;
    if (w_states_n_ + n_macro > w_states_cap_) n_macro = w_states_cap_ - w_states_n_;
    if (n_macro == 0) return false;

    VkCommandBufferAllocateInfo cbai{};
    cbai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    cbai.commandPool = cmd_pool_;
    cbai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cbai.commandBufferCount = 1;
    VkCommandBuffer cb;
    vkAllocateCommandBuffers(device_, &cbai, &cb);
    VkCommandBufferBeginInfo bbi{};
    bbi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    vkBeginCommandBuffer(cb, &bbi);

    for (uint32_t step = 0; step < n_macro; ++step) {
        // injection from the recorded upload table, indexed by absolute step
        int32_t inj_target = -1, inj_count = 0;
        uint32_t inj_idx = (w_states_n_ - 1 + step);
        if (inj_idx * 2 + 1 < w_inj_.size()) {
            inj_target = static_cast<int32_t>(w_inj_[inj_idx * 2]);
            inj_count = static_cast<int32_t>(w_inj_[inj_idx * 2 + 1]);
        }
        water_record_macro_step(cb, dt_macro, inj_target, inj_count);

        // record the state (batch verification path only)
        VkBufferCopy bc{};
        bc.srcOffset = 0;
        bc.dstOffset = static_cast<VkDeviceSize>(w_states_n_ + step) * w_n_cells_ * sizeof(int32_t);
        bc.size = static_cast<VkDeviceSize>(w_n_cells_) * sizeof(int32_t);
        vkCmdCopyBuffer(cb, w_V_buf_, w_states_buf_, 1, &bc);
        VkMemoryBarrier cmb{};
        cmb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        cmb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        cmb.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
        vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                             VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 1, &cmb, 0, nullptr, 0, nullptr);
    }
    vkEndCommandBuffer(cb);

    vkResetFences(device_, 1, &w_fence_);
    VkSubmitInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &cb;
    vkQueueSubmit(queue_, 1, &si, w_fence_);
    vkWaitForFences(device_, 1, &w_fence_, VK_TRUE, UINT64_MAX);
    vkFreeCommandBuffers(device_, cmd_pool_, 1, &cb);
    w_states_n_ += n_macro;

    // final sum/min from the last recorded state (host readback)
    {
        VkCommandBuffer cb2 = begin_single_time_cmd();
        VkBufferCopy rc{};
        rc.size = static_cast<VkDeviceSize>(w_states_n_) * w_n_cells_ * sizeof(int32_t);
        vkCmdCopyBuffer(cb2, w_states_buf_, w_readback_buf_, 1, &rc);
        end_single_time_cmd(cb2);
    }
    const int32_t* last = static_cast<const int32_t*>(w_readback_map_) +
                          static_cast<size_t>(w_states_n_ - 1) * w_n_cells_;
    int64_t s = 0, mn = INT64_MAX;
    for (uint32_t i = 0; i < w_n_cells_; ++i) { s += last[i]; if (last[i] < mn) mn = last[i]; }
    sum_out = s; min_out = mn;
    return true;
}

bool Engine::water_download(std::vector<int32_t>& out_states, uint32_t& n_states, uint32_t& n_cells) {
    if (!water_loaded_ || w_states_n_ == 0) return false;
    VkCommandBuffer cb = begin_single_time_cmd();
    VkBufferCopy rc{};
    rc.size = static_cast<VkDeviceSize>(w_states_n_) * w_n_cells_ * sizeof(int32_t);
    vkCmdCopyBuffer(cb, w_states_buf_, w_readback_buf_, 1, &rc);
    end_single_time_cmd(cb);
    const int32_t* src = static_cast<const int32_t*>(w_readback_map_);
    out_states.assign(src, src + static_cast<size_t>(w_states_n_) * w_n_cells_);
    n_states = w_states_n_;
    n_cells = w_n_cells_;
    return true;
}

// DEBUG readback for the W4 vis path: indirect draw command + a slice of the
// water vertex buffer, packed into out (int32 view: [4 u32 indirect][floats...]).
bool Engine::water_vis_debug(std::vector<int32_t>& out, uint32_t max_floats) {
    if (!water_loaded_ || w_vis_indirect_buf_ == VK_NULL_HANDLE) return false;
    VkDeviceSize vbytes = std::min<VkDeviceSize>(static_cast<VkDeviceSize>(max_floats) * 4,
        static_cast<VkDeviceSize>(w_vis_cap_verts_) * 9 * sizeof(float));
    VkCommandBuffer cb = begin_single_time_cmd();
    VkBufferCopy c0{}; c0.size = 16;
    vkCmdCopyBuffer(cb, w_vis_indirect_buf_, w_readback_buf_, 1, &c0);
    VkBufferCopy c1{}; c1.srcOffset = 0; c1.dstOffset = 16; c1.size = vbytes;
    vkCmdCopyBuffer(cb, w_vis_vbuf_, w_readback_buf_, 1, &c1);
    end_single_time_cmd(cb);
    const uint8_t* src = static_cast<const uint8_t*>(w_readback_map_);
    const int32_t* as_i32 = reinterpret_cast<const int32_t*>(src);
    out.assign(as_i32, as_i32 + 4 + vbytes / 4);
    return true;
}

// (Re)point the water-vis descriptor set at the LIVE mesh buffers. /mesh_bin
// full-loads recreate tri_vbuf_/tri_ibuf_; they set water_vis_desc_dirty_ and
// frame() calls this lazily (only when both water and mesh are loaded).
void Engine::water_vis_rebind() {
    if (w_vis_set_ == VK_NULL_HANDLE || !water_loaded_ || !has_mesh_) return;
    VkBuffer bufs[6] = { w_V_buf_, w_areas_buf_, tri_vbuf_, tri_ibuf_,
                         w_vis_indirect_buf_, w_vis_vbuf_ };
    VkWriteDescriptorSet w[6]{};
    VkDescriptorBufferInfo infos[6]{};
    for (uint32_t k = 0; k < 6; ++k) {
        infos[k].buffer = bufs[k]; infos[k].range = VK_WHOLE_SIZE;
        w[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w[k].dstSet = w_vis_set_; w[k].dstBinding = k; w[k].descriptorCount = 1;
        w[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        w[k].pBufferInfo = &infos[k];
    }
    vkUpdateDescriptorSets(device_, 6, w, 0, nullptr);
    water_vis_desc_dirty_ = false;
}

// (Re)point the hinge descriptor set at the LIVE buffers. set_hinge updates
// the set itself; the dirty flag covers the OTHER recreator — load_mesh
// replacing tri_vbuf_ (binding 3, "Out"). Same lazy discipline as W4/H9.
void Engine::hinge_rebind() {
    if (hinge_desc_set_ == VK_NULL_HANDLE || !has_mesh_) return;
    VkBuffer bufs[5] = { hinge_rest_buf_, hinge_wL_buf_, hinge_wR_buf_, tri_vbuf_, strain_buf_ };
    VkWriteDescriptorSet w[5]{};
    VkDescriptorBufferInfo infos[5]{};
    for (uint32_t k = 0; k < 5; ++k) {
        infos[k].buffer = bufs[k]; infos[k].range = VK_WHOLE_SIZE;
        w[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w[k].dstSet = hinge_desc_set_; w[k].dstBinding = k; w[k].descriptorCount = 1;
        w[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        w[k].pBufferInfo = &infos[k];
    }
    vkUpdateDescriptorSets(device_, 5, w, 0, nullptr);
    hinge_desc_dirty_ = false;
}

// (Re)point the joints descriptor set at the LIVE buffers. The set binds TWO
// buffers it does not own: hinge_rest_buf_ (binding 0, "Rest" — recreated by
// every set_hinge) and tri_vbuf_ (binding 4, "Out" — recreated by every mesh
// full-load). Either recreation left the set pointing at a DESTROYED buffer;
// the next dispatch was an illegal access -> VK_ERROR_DEVICE_LOST. That was
// the crash that hunted D5: the first probe run on a fresh engine always
// passed (load order mesh -> hinge -> joints ends consistent), the SECOND
// run on the same engine died in the load phase. frame() calls this lazily,
// before the joints dispatch — same discipline as water_vis_rebind (W4).
void Engine::joints_rebind() {
    if (joints_desc_set_ == VK_NULL_HANDLE || !joints_loaded_ || !has_mesh_) return;
    VkBuffer bufs[5] = { hinge_rest_buf_, j_assign_buf_, j_w_buf_, j_state_buf_, tri_vbuf_ };
    VkWriteDescriptorSet w[5]{};
    VkDescriptorBufferInfo infos[5]{};
    for (uint32_t k = 0; k < 5; ++k) {
        infos[k].buffer = bufs[k]; infos[k].range = VK_WHOLE_SIZE;
        w[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w[k].dstSet = joints_desc_set_; w[k].dstBinding = k; w[k].descriptorCount = 1;
        w[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        w[k].pBufferInfo = &infos[k];
    }
    vkUpdateDescriptorSets(device_, 5, w, 0, nullptr);
    joints_desc_dirty_ = false;
}

// ── THE FROST DECODE (H9) ────────────────────────────────────────────────────
// The trained per-triangle relighting MLP as an integer compute kernel —
// shaders/frost_decode.comp is a bit-exact port of .tmp/frost_decode_ref.py
// (the golden fixed-point reference; IT defines the shipped decode). All state
// downstream of the posed float32 vertex buffer is exact integer (Q formats
// derived + budget-measured in the reference: C_total = 0.56 dB <= X = 1.0).
//
// Paths probed at load: DP4a is UNAVAILABLE to GLSL shaders (glslang 1.4.328
// exposes no integer-dot-product binding), VK_NV_cooperative_vector is probed
// and logged but left INACTIVE — the scalar int32 IMAD path is exact, atomic-
// free, fixed-order, and meets render rate with headroom; a second exact path
// would double the verification surface for no measured need (V5: determinism
// outranks speed).

static void quantize_dir_q30(const double v[3], int32_t out[3]) {
    // IEEE float64, correctly rounded (+,*,/,sqrt) => bit-identical to the
    // reference's numpy float64 path. round-half-away (rha) on |x|*2^30.
    double n = sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    if (n == 0.0) { out[0] = 0; out[1] = 1 << 30; out[2] = 0; return; }
    for (int k = 0; k < 3; ++k) {
        double d = v[k] / n;
        double a = fabs(d) * 1073741824.0;          // 2^30
        double q = floor(a + 0.5);
        out[k] = static_cast<int32_t>((d < 0.0) ? -static_cast<int64_t>(q)
                                                :  static_cast<int64_t>(q));
    }
}

bool Engine::load_frost(const uint8_t* blob, size_t size) {
    vkDeviceWaitIdle(device_);
    // ── coop-vec probe (log only; see the block comment above) ──
    {
        uint32_t n_ext = 0;
        vkEnumerateDeviceExtensionProperties(phys_dev_, nullptr, &n_ext, nullptr);
        std::vector<VkExtensionProperties> exts(n_ext);
        vkEnumerateDeviceExtensionProperties(phys_dev_, nullptr, &n_ext, exts.data());
        for (const auto& e : exts)
            if (strcmp(e.extensionName, "VK_NV_cooperative_vector") == 0)
                frost_coopvec_present_ = true;
        printf("FROST paths: scalar-int32 IMAD (PINNED, exact) | DP4a: no GLSL binding "
               "(glslang 1.4.328) | VK_NV_cooperative_vector: %s (inactive)\n",
               frost_coopvec_present_ ? "present" : "absent");
    }
    // ── parse the blob (layout: .tmp/frost_decode_ref.py::export_blob) ──
    if (size < 64 || memcmp(blob, "FRO1", 4) != 0) {
        fprintf(stderr, "frost: bad blob\n"); return false;
    }
    uint32_t F, lut_len;
    memcpy(&F, blob + 4, 4);
    memcpy(&lut_len, blob + 8, 4);
    int32_t fmts[8];   // PP QN SD RM SZ R QO ACT_HI
    memcpy(fmts, blob + 12, 32);
    printf("FROST model: %u tris, lut %u | PP %d QN %d SD %d RM %d SZ %d R %d QO %d ACT_HI %d\n",
           F, lut_len, fmts[0], fmts[1], fmts[2], fmts[3], fmts[4], fmts[5], fmts[6], fmts[7]);
    const size_t w_bytes = (64 * 14 + 64 * 64 + 64 * 64 + 3 * 64) * 4;  // int8-valued int32s
    const size_t ab_rows = 64 + 64 + 64 + 3;
    size_t off = 64;
    size_t expect = off + static_cast<size_t>(F) * 4 + 8 * 4 + w_bytes
                  + ab_rows * 16 + static_cast<size_t>(lut_len) * 4;
    if (size != expect) {
        fprintf(stderr, "frost: blob size mismatch (%zu vs %zu)\n", size, expect);
        return false;
    }
    const uint8_t* p_lat = blob + off;                       off += static_cast<size_t>(F) * 4;
    const uint8_t* p_m   = blob + off;                       off += 8 * 4;
    const uint8_t* p_w   = blob + off;                       off += w_bytes;
    const uint8_t* p_ab  = blob + off;                       off += ab_rows * 16;
    const uint8_t* p_lut = blob + off;

    upload_buffer(p_lat, static_cast<size_t>(F) * 4, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, f_lat_buf_, f_lat_mem_);
    upload_buffer(p_m, 8 * 4, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, f_m_buf_, f_m_mem_);
    upload_buffer(p_w, w_bytes, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, f_w_buf_, f_w_mem_);
    upload_buffer(p_ab, ab_rows * 16, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, f_ab_buf_, f_ab_mem_);
    upload_buffer(p_lut, static_cast<size_t>(lut_len) * 4, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, f_lut_buf_, f_lut_mem_);
    {
        std::vector<int32_t> zeros(static_cast<size_t>(F) * 3, 0);
        upload_buffer(zeros.data(), zeros.size() * 4,
                      VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                      f_color_buf_, f_color_mem_);
        std::vector<int32_t> z2(static_cast<size_t>(F) * 14, 0);
        upload_buffer(z2.data(), z2.size() * 4,
                      VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                      f_dbg_buf_, f_dbg_mem_);
    }
    // host-visible readbacks (snapshot path)
    auto make_readback = [&](VkDeviceSize bytes, VkBuffer& buf, VkDeviceMemory& mem, void*& map) {
        if (buf) { if (map) vkUnmapMemory(device_, mem); vkDestroyBuffer(device_, buf, nullptr); vkFreeMemory(device_, mem, nullptr); }
        VkBufferCreateInfo bci{};
        bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size = bytes; bci.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &buf);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, buf, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &mem);
        vkBindBufferMemory(device_, buf, mem, 0);
        vkMapMemory(device_, mem, 0, bytes, 0, &map);
    };
    make_readback(static_cast<size_t>(F) * 3 * 4, f_color_rb_, f_color_rb_mem_, f_color_rb_map_);
    make_readback(static_cast<size_t>(F) * 14 * 4, f_dbg_rb_, f_dbg_rb_mem_, f_dbg_rb_map_);

    // ── compute pipeline (10 SSBOs + 32 B push constants; binding 9 = eye class) ──
    if (!w_make_pipeline(device_, "shaders/frost_decode.spv", 10, 32,
                         frost_mod_, frost_dsl_, frost_layout_, frost_pipe_)) {
        fprintf(stderr, "frost: compute pipeline failed\n"); return false;
    }
    // E1: the eye-class buffer (2,092 u32; 0=sclera 1=iris 2=pupil; default all
    // sclera until /eye_bin uploads the measured classification).
    if (f_eye_buf_ == VK_NULL_HANDLE) {
        std::vector<uint32_t> zeros(2092, 0);
        upload_buffer(zeros.data(), zeros.size() * sizeof(uint32_t),
                      VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, f_eye_buf_, f_eye_mem_);
    }
    // ── frost render pipeline: same vertex stage, frag reads the color SSBO ──
    {
        std::vector<char> spv = read_file("shaders/render_tri_frost.spv");
        if (spv.empty()) { fprintf(stderr, "frost: render_tri_frost.spv missing\n"); return false; }
        if (tri_frost_frag_mod_) vkDestroyShaderModule(device_, tri_frost_frag_mod_, nullptr);
        VkShaderModuleCreateInfo smci{};
        smci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        smci.codeSize = spv.size();
        smci.pCode = reinterpret_cast<const uint32_t*>(spv.data());
        vkCreateShaderModule(device_, &smci, nullptr, &tri_frost_frag_mod_);

        // set 1: the per-triangle color SSBO (fragment)
        if (!frost_frag_dsl_) {
            VkDescriptorSetLayoutBinding b{};
            b.binding = 0; b.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            b.descriptorCount = 1; b.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
            VkDescriptorSetLayoutCreateInfo dlci{};
            dlci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
            dlci.bindingCount = 1; dlci.pBindings = &b;
            vkCreateDescriptorSetLayout(device_, &dlci, nullptr, &frost_frag_dsl_);
            VkDescriptorSetLayout sets[2] = { desc_layout_, frost_frag_dsl_ };
            VkPipelineLayoutCreateInfo plci{};
            plci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
            plci.setLayoutCount = 2; plci.pSetLayouts = sets;
            vkCreatePipelineLayout(device_, &plci, nullptr, &frost_render_layout_);
            VkDescriptorPoolSize ps{};
            ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER; ps.descriptorCount = 1;
            VkDescriptorPoolCreateInfo dpci{};
            dpci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
            dpci.maxSets = 1; dpci.poolSizeCount = 1; dpci.pPoolSizes = &ps;
            vkCreateDescriptorPool(device_, &dpci, nullptr, &frost_frag_pool_);
            VkDescriptorSetAllocateInfo dsai{};
            dsai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
            dsai.descriptorPool = frost_frag_pool_; dsai.descriptorSetCount = 1;
            dsai.pSetLayouts = &frost_frag_dsl_;
            vkAllocateDescriptorSets(device_, &dsai, &frost_frag_set_);
        }

        // graphics pipeline — identical state to create_triangle_pipeline's fill
        VkVertexInputBindingDescription binding{};
        binding.binding = 0; binding.stride = sizeof(float) * 9;
        binding.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;
        VkVertexInputAttributeDescription attrs[3] = {};
        attrs[0].location = 0; attrs[0].binding = 0;
        attrs[0].format = VK_FORMAT_R32G32B32_SFLOAT; attrs[0].offset = 0;
        attrs[1].location = 1; attrs[1].binding = 0;
        attrs[1].format = VK_FORMAT_R32G32B32_SFLOAT; attrs[1].offset = sizeof(float) * 3;
        attrs[2].location = 2; attrs[2].binding = 0;
        attrs[2].format = VK_FORMAT_R32G32B32_SFLOAT; attrs[2].offset = sizeof(float) * 6;
        VkPipelineShaderStageCreateInfo stages[2] = {};
        stages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
        stages[0].module = tri_vert_mod_; stages[0].pName = "main";
        stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
        stages[1].module = tri_frost_frag_mod_; stages[1].pName = "main";
        VkPipelineInputAssemblyStateCreateInfo ia{};
        ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
        ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
        VkPipelineViewportStateCreateInfo vp{};
        vp.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
        vp.viewportCount = 1; vp.scissorCount = 1;
        VkPipelineRasterizationStateCreateInfo ras{};
        ras.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
        ras.polygonMode = VK_POLYGON_MODE_FILL;
        ras.cullMode = VK_CULL_MODE_NONE;
        ras.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
        ras.lineWidth = 1.0f;
        VkPipelineMultisampleStateCreateInfo ms{};
        ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
        ms.rasterizationSamples = rt_samples_;   // frost fill renders into the MSAA offscreen pass too
        VkPipelineColorBlendAttachmentState blend{};
        blend.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                               VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
        VkPipelineColorBlendStateCreateInfo cb{};
        cb.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
        cb.attachmentCount = 1; cb.pAttachments = &blend;
        VkPipelineDynamicStateCreateInfo dyn{};
        dyn.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
        static const VkDynamicState dyn_states[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
        dyn.dynamicStateCount = 2; dyn.pDynamicStates = dyn_states;
        VkPipelineDepthStencilStateCreateInfo ds{};
        ds.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
        ds.depthTestEnable = VK_TRUE; ds.depthWriteEnable = VK_TRUE;
        ds.depthCompareOp = VK_COMPARE_OP_LESS;
        VkPipelineVertexInputStateCreateInfo vi{};
        vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
        vi.vertexBindingDescriptionCount = 1; vi.pVertexBindingDescriptions = &binding;
        vi.vertexAttributeDescriptionCount = 3; vi.pVertexAttributeDescriptions = attrs;
        VkGraphicsPipelineCreateInfo gpci{};
        gpci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
        gpci.stageCount = 2; gpci.pStages = stages;
        gpci.pVertexInputState = &vi;
        gpci.pInputAssemblyState = &ia; gpci.pViewportState = &vp;
        gpci.pRasterizationState = &ras; gpci.pMultisampleState = &ms;
        gpci.pDepthStencilState = &ds; gpci.pColorBlendState = &cb;
        gpci.pDynamicState = &dyn;
        gpci.layout = frost_render_layout_;
        gpci.renderPass = rt_render_pass_; gpci.subpass = 0;
        if (tri_frost_pipeline_) vkDestroyPipeline(device_, tri_frost_pipeline_, nullptr);
        VkResult pr = vkCreateGraphicsPipelines(device_, VK_NULL_HANDLE, 1, &gpci,
                                                nullptr, &tri_frost_pipeline_);
        if (pr != VK_SUCCESS) {
            fprintf(stderr, "frost: render pipeline failed (%d)\n", (int)pr); return false;
        }
        frost_render_ready_ = true;
    }

    // descriptor pool + set for the compute kernel
    {
        VkDescriptorPoolSize ps{};
        ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER; ps.descriptorCount = 10;
        if (frost_desc_pool_) vkDestroyDescriptorPool(device_, frost_desc_pool_, nullptr);
        VkDescriptorPoolCreateInfo dpci{};
        dpci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
        dpci.maxSets = 1; dpci.poolSizeCount = 1; dpci.pPoolSizes = &ps;
        vkCreateDescriptorPool(device_, &dpci, nullptr, &frost_desc_pool_);
        VkDescriptorSetAllocateInfo dsai{};
        dsai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        dsai.descriptorPool = frost_desc_pool_; dsai.descriptorSetCount = 1;
        dsai.pSetLayouts = &frost_dsl_;
        vkAllocateDescriptorSets(device_, &dsai, &frost_desc_set_);
        // static bindings 2..8 (model + outputs); 0/1 (mesh buffers) bind lazily
        VkBuffer bufs[7] = { f_lat_buf_, f_w_buf_, f_ab_buf_, f_m_buf_,
                             f_lut_buf_, f_color_buf_, f_dbg_buf_ };
        VkWriteDescriptorSet w[7]{};
        VkDescriptorBufferInfo infos[7]{};
        for (uint32_t k = 0; k < 7; ++k) {
            infos[k].buffer = bufs[k]; infos[k].range = VK_WHOLE_SIZE;
            w[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            w[k].dstSet = frost_desc_set_; w[k].dstBinding = 2 + k;
            w[k].descriptorCount = 1;
            w[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            w[k].pBufferInfo = &infos[k];
        }
        vkUpdateDescriptorSets(device_, 7, w, 0, nullptr);
        // binding 9: the eye-class buffer (E1)
        {
            VkDescriptorBufferInfo einfo{};
            einfo.buffer = f_eye_buf_; einfo.range = VK_WHOLE_SIZE;
            VkWriteDescriptorSet ew{};
            ew.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            ew.dstSet = frost_desc_set_; ew.dstBinding = 9; ew.descriptorCount = 1;
            ew.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            ew.pBufferInfo = &einfo;
            vkUpdateDescriptorSets(device_, 1, &ew, 0, nullptr);
        }
        // the frost render set reads the same color buffer
        VkDescriptorBufferInfo cinfo{};
        cinfo.buffer = f_color_buf_; cinfo.range = VK_WHOLE_SIZE;
        VkWriteDescriptorSet cw{};
        cw.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        cw.dstSet = frost_frag_set_; cw.dstBinding = 0; cw.descriptorCount = 1;
        cw.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        cw.pBufferInfo = &cinfo;
        vkUpdateDescriptorSets(device_, 1, &cw, 0, nullptr);
    }
    f_n_tris_ = F;
    f_lut_len_ = lut_len;
    frost_loaded_ = true;
    frost_desc_dirty_ = true;
    frost_frame_.store(0);
    printf("FROST loaded: %u triangles of relighting state\n", F);
    return true;
}

// E1: upload the measured eye classification (u32 per eye tri: shell tris then
// appended cap tris; 0 sclera / 1 iris / 2 pupil). Size follows the mesh.
bool Engine::set_eye_class(const std::vector<uint32_t>& cls) {
    if (f_eye_buf_ == VK_NULL_HANDLE || cls.size() < 2092) {
        fprintf(stderr, "eye class: count mismatch (%zu) or frost not loaded\n", cls.size());
        return false;
    }
    vkDeviceWaitIdle(device_);
    upload_buffer(cls.data(), cls.size() * sizeof(uint32_t),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, f_eye_buf_, f_eye_mem_);
    // upload_buffer recreates the buffer -> the frost compute set's binding 9
    // must be re-pointed or every frost dispatch references a destroyed buffer
    // (the pose froze when the command buffer choked on it, engine_v21).
    if (frost_desc_set_ != VK_NULL_HANDLE) {
        VkDescriptorBufferInfo einfo{};
        einfo.buffer = f_eye_buf_; einfo.range = VK_WHOLE_SIZE;
        VkWriteDescriptorSet ew{};
        ew.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        ew.dstSet = frost_desc_set_; ew.dstBinding = 9; ew.descriptorCount = 1;
        ew.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        ew.pBufferInfo = &einfo;
        vkUpdateDescriptorSets(device_, 1, &ew, 0, nullptr);
    }
    printf("EYE class uploaded: %zu eye tris classified\n", cls.size());
    return true;
}

// ── H15: the all-joints articulation ─────────────────────────────────────────
// Blob 'JNT1': [magic][u32 n_verts][u32 n_joints][u32 names_len][names][assign
// i32*n][w f32*n][J f32*3j][axis f32*3j][rom f32*2j (deg, ext|flex)].
bool Engine::load_joints(const std::vector<uint8_t>& blob) {
    if (!has_mesh_ || hinge_rest_.empty()) { fprintf(stderr, "joints: no mesh/hinge rest\n"); return false; }
    if (blob.size() < 16 || memcmp(blob.data(), "JNT1", 4) != 0) {
        fprintf(stderr, "joints: bad blob\n"); return false;
    }
    const uint8_t* p = blob.data() + 4;
    uint32_t nv, nj, nl;
    memcpy(&nv, p, 4); p += 4;
    memcpy(&nj, p, 4); p += 4;
    memcpy(&nl, p, 4); p += 4;
    j_names_.clear();
    {   // \0-separated names
        const char* s = reinterpret_cast<const char*>(p);
        size_t used = 0;
        for (uint32_t k = 0; k < nj; ++k) {
            size_t l = strnlen(s + used, nl - used);
            j_names_.emplace_back(s + used, l);
            used += l + 1;
        }
    }
    p += nl;
    const int32_t* assign = reinterpret_cast<const int32_t*>(p); p += nv * 4;
    const float* w = reinterpret_cast<const float*>(p); p += nv * 4;
    const float* J = reinterpret_cast<const float*>(p); p += nj * 12;
    const float* ax = reinterpret_cast<const float*>(p); p += nj * 12;
    const float* rom = reinterpret_cast<const float*>(p);
    size_t nv_mesh = hinge_wL_.size();
    if (nv != nv_mesh) {
        fprintf(stderr, "joints: %u assignments vs %zu mesh verts\n", nv, nv_mesh);
        return false;
    }
    vkDeviceWaitIdle(device_);
    j_n_verts_ = nv; j_n_joints_ = nj;
    j_rom_.assign(rom, rom + nj * 2);

    // C1: the gizmo's axis length is DERIVED, not picked — the RMS radius of
    // the joint's own band (assign == k) about its center J. A big joint gets
    // a long axis, a small joint a short one, from the pack's own geometry.
    j_gizmo_len_.assign(nj, 0.5f);
    if (hinge_rest_.size() >= static_cast<size_t>(nv) * 9) {
        for (uint32_t k = 0; k < nj; ++k) {
            double acc = 0.0; uint32_t cnt = 0;
            for (uint32_t i = 0; i < nv; ++i) {
                if (assign[i] != static_cast<int32_t>(k)) continue;
                double dx = hinge_rest_[i * 9 + 0] - J[k * 3 + 0];
                double dy = hinge_rest_[i * 9 + 1] - J[k * 3 + 1];
                double dz = hinge_rest_[i * 9 + 2] - J[k * 3 + 2];
                acc += dx * dx + dy * dy + dz * dz; ++cnt;
            }
            if (cnt) j_gizmo_len_[k] = static_cast<float>(sqrt(acc / cnt));
        }
    }

    upload_buffer(assign, nv * sizeof(int32_t), VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, j_assign_buf_, j_assign_mem_);
    upload_buffer(w, nv * sizeof(float), VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, j_w_buf_, j_w_mem_);

    // joints state: per joint 8 floats [Jx Jy Jz Ax Ay Az 0 theta(rad)], host-visible
    {
        if (j_state_map_) { vkUnmapMemory(device_, j_state_mem_); j_state_map_ = nullptr; }
        if (j_state_buf_) { vkDestroyBuffer(device_, j_state_buf_, nullptr); vkFreeMemory(device_, j_state_mem_, nullptr); }
        VkDeviceSize sz = static_cast<VkDeviceSize>(nj) * 8 * sizeof(float);
        VkBufferCreateInfo bci{};
        bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size = sz;
        bci.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &j_state_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, j_state_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &j_state_mem_);
        vkBindBufferMemory(device_, j_state_buf_, j_state_mem_, 0);
        vkMapMemory(device_, j_state_mem_, 0, sz, 0, &j_state_map_);
        float* st = static_cast<float*>(j_state_map_);
        for (uint32_t k = 0; k < nj; ++k) {
            st[k * 8 + 0] = J[k * 3 + 0]; st[k * 8 + 1] = J[k * 3 + 1]; st[k * 8 + 2] = J[k * 3 + 2];
            st[k * 8 + 3] = ax[k * 3 + 0]; st[k * 8 + 4] = ax[k * 3 + 1]; st[k * 8 + 5] = ax[k * 3 + 2];
            st[k * 8 + 6] = 0.0f;
            st[k * 8 + 7] = 0.0f;         // theta = 0 (rest)
        }
    }

    // pipeline (5 SSBOs + 16 B push constants: n, nj, paint, pad — C1)
    if (!w_make_pipeline(device_, "shaders/joints.spv", 5, 16,
                         joints_mod_, joints_dsl_, joints_layout_, joints_pipe_)) {
        fprintf(stderr, "joints: pipeline failed\n"); return false;
    }
    {
        VkDescriptorPoolSize ps{};
        ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER; ps.descriptorCount = 5;
        if (joints_desc_pool_) vkDestroyDescriptorPool(device_, joints_desc_pool_, nullptr);
        VkDescriptorPoolCreateInfo dpci{};
        dpci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
        dpci.maxSets = 1; dpci.poolSizeCount = 1; dpci.pPoolSizes = &ps;
        vkCreateDescriptorPool(device_, &dpci, nullptr, &joints_desc_pool_);
        VkDescriptorSetAllocateInfo dsai{};
        dsai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        dsai.descriptorPool = joints_desc_pool_; dsai.descriptorSetCount = 1;
        dsai.pSetLayouts = &joints_dsl_;
        vkAllocateDescriptorSets(device_, &dsai, &joints_desc_set_);
        VkBuffer bufs[5] = { hinge_rest_buf_, j_assign_buf_, j_w_buf_, j_state_buf_, tri_vbuf_ };
        VkWriteDescriptorSet wr[5]{};
        VkDescriptorBufferInfo infos[5]{};
        for (uint32_t k = 0; k < 5; ++k) {
            infos[k].buffer = bufs[k]; infos[k].range = VK_WHOLE_SIZE;
            wr[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            wr[k].dstSet = joints_desc_set_; wr[k].dstBinding = k;
            wr[k].descriptorCount = 1;
            wr[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            wr[k].pBufferInfo = &infos[k];
        }
        vkUpdateDescriptorSets(device_, 5, wr, 0, nullptr);
    }
    joints_t0_ = std::chrono::steady_clock::now();
    joints_loaded_ = true;
    printf("JOINTS loaded: %u verts, %u joints (the show sweeps each through its ROM)\n", nv, nj);
    return true;
}

std::string Engine::joints_status() const {
    if (!joints_loaded_) return "{\"loaded\":false}";
    float t = static_cast<float>(show_time_.load(std::memory_order_relaxed));
    float per = j_sweep_period_;
    uint32_t cur = j_n_joints_ ? static_cast<uint32_t>(t / per) % j_n_joints_ : 0;
    std::string s = std::string("{\"loaded\":true,\"on\":") + (joints_on_.load() ? "true" : "false")
        + ",\"n_joints\":" + std::to_string(j_n_joints_)
        + ",\"current\":\"" + (cur < j_names_.size() ? j_names_[cur] : std::string("?")) + "\""
        + ",\"t\":" + std::to_string(t) + "}";
    return s;
}

// D1: the current joint's live theta (degrees) — the timeline's pose readout and
// the scrub gate's verification channel (j_state_map_ stride 8: theta at +7, rad).
double Engine::show_current_theta() {
    if (!joints_loaded_ || j_state_map_ == nullptr) return 0.0;
    float t = static_cast<float>(show_time_.load(std::memory_order_relaxed));
    uint32_t cur = j_n_joints_ ? static_cast<uint32_t>(t / j_sweep_period_) % j_n_joints_ : 0;
    const float* st = static_cast<const float*>(j_state_map_);
    return st[cur * 8 + 7] * 57.29577951308232;
}

void Engine::show_current_rom(float& ext, float& flex) const {
    ext = flex = 0.0f;
    if (!joints_loaded_ || j_rom_.empty()) return;
    float t = static_cast<float>(show_time_.load(std::memory_order_relaxed));
    uint32_t cur = j_n_joints_ ? static_cast<uint32_t>(t / j_sweep_period_) % j_n_joints_ : 0;
    ext  = j_rom_[cur * 2 + 0];   // degrees (the sweep kernel converts to radians)
    flex = j_rom_[cur * 2 + 1];
}

// ── C1: THE JOINTS EDITOR ────────────────────────────────────────────────────
int Engine::joint_index(const std::string& name) const {
    for (size_t i = 0; i < j_names_.size(); ++i)
        if (j_names_[i] == name) return static_cast<int>(i);
    return -1;
}

void Engine::request_joint_edit(int idx, float deg) {
    // An edit intent is an ownership claim: the editor takes the pose, the show
    // clock stops writing thetas (the clock itself keeps running — D1's readout
    // stays honest). Pressing play hands the pose back to the show.
    if (!joints_loaded_ || idx < 0 || idx >= static_cast<int>(j_n_joints_)) return;
    joints_owner_.store(1, std::memory_order_relaxed);
    edit_joint_.store(idx, std::memory_order_relaxed);
    edit_theta_deg_.store(deg, std::memory_order_relaxed);
    edit_pending_.store(true, std::memory_order_relaxed);
}

std::string Engine::joints_editor_json() {
    if (!joints_loaded_) return "{\"loaded\":false}";
    const float* st = static_cast<const float*>(j_state_map_);
    int owner = joints_owner_.load(std::memory_order_relaxed);
    int sel = selected_joint_.load(std::memory_order_relaxed);
    float t = static_cast<float>(show_time_.load(std::memory_order_relaxed));
    uint32_t cur = j_n_joints_ ? static_cast<uint32_t>(t / j_sweep_period_) % j_n_joints_ : 0;
    std::string s = std::string("{\"loaded\":true,\"on\":") + (joints_on_.load() ? "true" : "false")
        + ",\"owner\":\"" + (owner == 1 ? "edit" : "show") + "\""
        + ",\"selected\":" + std::to_string(sel)
        + ",\"t\":" + std::to_string(t)
        + ",\"current\":\"" + (cur < j_names_.size() ? j_names_[cur] : std::string("?")) + "\""
        + ",\"n_joints\":" + std::to_string(j_n_joints_) + ",\"joints\":[";
    char jb[320];
    for (uint32_t k = 0; k < j_n_joints_; ++k) {
        double th = st ? st[k * 8 + 7] * 57.29577951308232 : 0.0;
        snprintf(jb, sizeof(jb),
            "{\"name\":\"%s\",\"ext\":%.2f,\"flex\":%.2f,\"theta\":%.3f,"
            "\"J\":[%.4f,%.4f,%.4f],\"axis\":[%.4f,%.4f,%.4f]}",
            j_names_[k].c_str(), j_rom_[k * 2 + 0], j_rom_[k * 2 + 1], th,
            st ? st[k * 8 + 0] : 0.f, st ? st[k * 8 + 1] : 0.f, st ? st[k * 8 + 2] : 0.f,
            st ? st[k * 8 + 3] : 0.f, st ? st[k * 8 + 4] : 0.f, st ? st[k * 8 + 5] : 0.f);
        s += jb;
        if (k + 1 < j_n_joints_) s += ",";
    }
    s += "]}";
    return s;
}

// C1: world -> screen through the SAME proj/view the mesh pass used this frame
// (stashed in frame()). The gizmo and the /project verification channel share
// this one math path, so a probe that checks /project checks the gizmo.
void Engine::camera_state(float out[8]) const {
    out[0] = g_cam.radius; out[1] = g_cam.theta; out[2] = g_cam.phi;
    out[3] = g_cam.target[0]; out[4] = g_cam.target[1]; out[5] = g_cam.target[2];
    out[6] = g_cam.pan_x;  out[7] = g_cam.pan_y;
}
bool Engine::project_world(const float p[3], float& sx, float& sy) const {
    if (!last_vp_valid_) return false;
    // view * p (column-major 4x4 as written by look_at)
    float vx = last_view_[0] * p[0] + last_view_[4] * p[1] + last_view_[8]  * p[2] + last_view_[12];
    float vy = last_view_[1] * p[0] + last_view_[5] * p[1] + last_view_[9]  * p[2] + last_view_[13];
    float vz = last_view_[2] * p[0] + last_view_[6] * p[1] + last_view_[10] * p[2] + last_view_[14];
    float vw = last_view_[3] * p[0] + last_view_[7] * p[1] + last_view_[11] * p[2] + last_view_[15];
    float cx = last_proj_[0] * vx + last_proj_[4] * vy + last_proj_[8]  * vz + last_proj_[12] * vw;
    float cy = last_proj_[1] * vx + last_proj_[5] * vy + last_proj_[9]  * vz + last_proj_[13] * vw;
    float cw = last_proj_[3] * vx + last_proj_[7] * vy + last_proj_[11] * vz + last_proj_[15] * vw;
    if (cw <= 1e-6f) return false;               // behind the camera
    sx = (cx / cw * 0.5f + 0.5f) * static_cast<float>(extent_.width);
    // NDC is Y-down already (perspective() negates the Y row for Vulkan):
    // ndc -1 = framebuffer top = window top. No second flip — a point above
    // the target lands ABOVE center (verified against the anatomy: the neck's
    // +Y projects to a smaller sy than the hips').
    sy = (cy / cw * 0.5f + 0.5f) * static_cast<float>(extent_.height);
    return true;
}

void Engine::frost_rebind() {
    if (frost_desc_set_ == VK_NULL_HANDLE || !frost_loaded_ || !has_mesh_) return;
    VkBuffer bufs[2] = { tri_vbuf_, tri_ibuf_ };
    VkWriteDescriptorSet w[2]{};
    VkDescriptorBufferInfo infos[2]{};
    for (uint32_t k = 0; k < 2; ++k) {
        infos[k].buffer = bufs[k]; infos[k].range = VK_WHOLE_SIZE;
        w[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w[k].dstSet = frost_desc_set_; w[k].dstBinding = k; w[k].descriptorCount = 1;
        w[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        w[k].pBufferInfo = &infos[k];
    }
    vkUpdateDescriptorSets(device_, 2, w, 0, nullptr);
    frost_desc_dirty_ = false;
}

bool Engine::frost_finish_snapshot(std::vector<int32_t>& out) {
    if (!frost_loaded_ || !frost_dbg_copy_recorded_) return false;
    vkDeviceWaitIdle(device_);   // one-off debug path — the frame that recorded
                                 // the copies has submitted; drain it
    size_t nc = static_cast<size_t>(f_n_tris_) * 3;
    size_t nd = static_cast<size_t>(f_n_tris_) * 14;
    out.resize(nc + nd);
    memcpy(out.data(), f_color_rb_map_, nc * 4);
    memcpy(out.data() + nc, f_dbg_rb_map_, nd * 4);
    frost_dbg_copy_recorded_ = false;
    return true;
}


bool Engine::load_overlay(const std::vector<float>& verts, const std::vector<uint32_t>& indices,
                          uint32_t vcount, uint32_t icount) {
    vkDeviceWaitIdle(device_);
    // B3: an empty POST clears the overlay slot (stage scripts use it to clear the
    // wireframe; was: 0-byte buffer -> NULL-handle crash).
    if (verts.empty() || indices.empty() || icount == 0) {
        upload_buffer(nullptr, 0, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, ov_vbuf_, ov_vmem_);
        upload_buffer(nullptr, 0, VK_BUFFER_USAGE_INDEX_BUFFER_BIT, ov_ibuf_, ov_imem_);
        ov_idx_count_ = 0;
        has_overlay_ = false;
        return true;
    }
    upload_buffer(verts.data(), static_cast<VkDeviceSize>(verts.size()) * sizeof(float),
                  VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, ov_vbuf_, ov_vmem_);
    upload_buffer(indices.data(), static_cast<VkDeviceSize>(indices.size()) * sizeof(uint32_t),
                  VK_BUFFER_USAGE_INDEX_BUFFER_BIT, ov_ibuf_, ov_imem_);
    ov_idx_count_ = icount;
    has_overlay_ = true;
    return true;
}

void Engine::destroy_triangle_resources() {
    if (floor_pipeline_) { vkDestroyPipeline(device_, floor_pipeline_, nullptr); floor_pipeline_ = VK_NULL_HANDLE; }
    if (floor_vbuf_) { vkDestroyBuffer(device_, floor_vbuf_, nullptr); vkFreeMemory(device_, floor_vmem_, nullptr); floor_vbuf_ = VK_NULL_HANDLE; }
    if (floor_vert_mod_) { vkDestroyShaderModule(device_, floor_vert_mod_, nullptr); floor_vert_mod_ = VK_NULL_HANDLE; }
    if (floor_frag_mod_) { vkDestroyShaderModule(device_, floor_frag_mod_, nullptr); floor_frag_mod_ = VK_NULL_HANDLE; }
    if (tri_pipeline_) { vkDestroyPipeline(device_, tri_pipeline_, nullptr); tri_pipeline_ = VK_NULL_HANDLE; }
    if (tri_wire_pipeline_) { vkDestroyPipeline(device_, tri_wire_pipeline_, nullptr); tri_wire_pipeline_ = VK_NULL_HANDLE; }
    if (tri_vert_mod_) { vkDestroyShaderModule(device_, tri_vert_mod_, nullptr); tri_vert_mod_ = VK_NULL_HANDLE; }
    if (tri_frag_mod_) { vkDestroyShaderModule(device_, tri_frag_mod_, nullptr); tri_frag_mod_ = VK_NULL_HANDLE; }
    if (tri_vbuf_) { vkDestroyBuffer(device_, tri_vbuf_, nullptr); vkFreeMemory(device_, tri_vmem_, nullptr); tri_vbuf_ = VK_NULL_HANDLE; }
    if (tri_staging_buf_) { if (tri_vmap_) vkUnmapMemory(device_, tri_staging_mem_); tri_vmap_ = nullptr; vkDestroyBuffer(device_, tri_staging_buf_, nullptr); vkFreeMemory(device_, tri_staging_mem_, nullptr); tri_staging_buf_ = VK_NULL_HANDLE; }
    if (tri_ibuf_) { vkDestroyBuffer(device_, tri_ibuf_, nullptr); vkFreeMemory(device_, tri_imem_, nullptr); tri_ibuf_ = VK_NULL_HANDLE; }
    if (ov_vbuf_) { vkDestroyBuffer(device_, ov_vbuf_, nullptr); vkFreeMemory(device_, ov_vmem_, nullptr); ov_vbuf_ = VK_NULL_HANDLE; }
    if (ov_ibuf_) { vkDestroyBuffer(device_, ov_ibuf_, nullptr); vkFreeMemory(device_, ov_imem_, nullptr); ov_ibuf_ = VK_NULL_HANDLE; }
    if (w_vis_vbuf_) { vkDestroyBuffer(device_, w_vis_vbuf_, nullptr); vkFreeMemory(device_, w_vis_vmem_, nullptr); w_vis_vbuf_ = VK_NULL_HANDLE; }
    if (w_vis_indirect_buf_) { vkDestroyBuffer(device_, w_vis_indirect_buf_, nullptr); vkFreeMemory(device_, w_vis_indirect_mem_, nullptr); w_vis_indirect_buf_ = VK_NULL_HANDLE; }
    if (rt_depth_view_)  { vkDestroyImageView(device_, rt_depth_view_, nullptr); rt_depth_view_ = VK_NULL_HANDLE; }
    if (rt_depth_image_) { vkDestroyImage(device_, rt_depth_image_, nullptr); rt_depth_image_ = VK_NULL_HANDLE; }
    if (rt_depth_mem_)   { vkFreeMemory(device_, rt_depth_mem_, nullptr); rt_depth_mem_ = VK_NULL_HANDLE; }
}

bool Engine::create_descriptor_sets() {
    // Descriptor set layout: binding 0 = uniform buffer (camera), binding 1 = vertex storage
    VkDescriptorSetLayoutBinding bindings[2] = {};

    bindings[0].binding        = 0;
    bindings[0].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    bindings[0].descriptorCount= 1;
    bindings[0].stageFlags     = VK_SHADER_STAGE_VERTEX_BIT;
    bindings[0].pImmutableSamplers = nullptr;

    bindings[1].binding        = 1;
    bindings[1].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    bindings[1].descriptorCount= 1;
    bindings[1].stageFlags     = VK_SHADER_STAGE_VERTEX_BIT;
    bindings[1].pImmutableSamplers = nullptr;

    VkDescriptorSetLayoutCreateInfo dslci{};
    dslci.sType         = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dslci.bindingCount  = 2;
    dslci.pBindings     = bindings;
    if (vkCreateDescriptorSetLayout(device_, &dslci, nullptr, &desc_layout_) != VK_SUCCESS) return false;

    // Descriptor pool — 1 uniform buffer + N storage buffers (one per frame in flight)
    VkDescriptorPoolSize pool_sizes[] = {
        {VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,      MAX_FRAMES_IN_FLIGHT},
        {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,      MAX_FRAMES_IN_FLIGHT * 2},
    };
    VkDescriptorPoolCreateInfo dpci{};
    dpci.sType             = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dpci.maxSets           = MAX_FRAMES_IN_FLIGHT;
    dpci.poolSizeCount     = 2;
    dpci.pPoolSizes        = pool_sizes;
    if (vkCreateDescriptorPool(device_, &dpci, nullptr, &desc_pool_) != VK_SUCCESS) return false;

    // Allocate descriptor sets
    std::vector<VkDescriptorSetLayout> layouts(MAX_FRAMES_IN_FLIGHT, desc_layout_);
    VkDescriptorSetAllocateInfo dai{};
    dai.sType            = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dai.descriptorPool   = desc_pool_;
    dai.descriptorSetCount= static_cast<uint32_t>(layouts.size());
    dai.pSetLayouts      = layouts.data();
    if (vkAllocateDescriptorSets(device_, &dai, desc_sets_.data()) != VK_SUCCESS) return false;

    return true;
}

bool Engine::create_compute_pipeline() {
    if (comp_mod_ == VK_NULL_HANDLE) {
        fprintf(stderr, "Compute shader module not loaded, skipping compute pipeline\n");
        return true;  // optional: fall back to CPU physics
    }

    // Descriptor set layout: 4 bindings matching compute.glsl
    VkDescriptorSetLayoutBinding bindings[4] = {};
    bindings[0].binding        = 0;
    bindings[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    bindings[0].descriptorCount= 1;
    bindings[0].stageFlags     = VK_SHADER_STAGE_COMPUTE_BIT;

    bindings[1].binding        = 1;
    bindings[1].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    bindings[1].descriptorCount= 1;
    bindings[1].stageFlags     = VK_SHADER_STAGE_COMPUTE_BIT;

    bindings[2].binding        = 2;
    bindings[2].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    bindings[2].descriptorCount= 1;
    bindings[2].stageFlags     = VK_SHADER_STAGE_COMPUTE_BIT;

    bindings[3].binding        = 3;
    bindings[3].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    bindings[3].descriptorCount= 1;
    bindings[3].stageFlags     = VK_SHADER_STAGE_COMPUTE_BIT;

    VkDescriptorSetLayoutCreateInfo dslci{};
    dslci.sType         = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dslci.bindingCount  = 4;
    dslci.pBindings     = bindings;
    if (vkCreateDescriptorSetLayout(device_, &dslci, nullptr, &compute_desc_layout_) != VK_SUCCESS)
        return false;

    // Descriptor pool — one set per frame in flight
    VkDescriptorPoolSize pool_sizes[] = {
        {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, MAX_FRAMES_IN_FLIGHT * 3},
        {VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, MAX_FRAMES_IN_FLIGHT},
    };
    VkDescriptorPoolCreateInfo dpci{};
    dpci.sType             = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dpci.maxSets           = MAX_FRAMES_IN_FLIGHT;
    dpci.poolSizeCount     = 2;
    dpci.pPoolSizes        = pool_sizes;
    if (vkCreateDescriptorPool(device_, &dpci, nullptr, &compute_desc_pool_) != VK_SUCCESS)
        return false;

    compute_desc_sets_.resize(MAX_FRAMES_IN_FLIGHT);
    std::vector<VkDescriptorSetLayout> layouts(MAX_FRAMES_IN_FLIGHT, compute_desc_layout_);
    VkDescriptorSetAllocateInfo dai{};
    dai.sType            = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dai.descriptorPool   = compute_desc_pool_;
    dai.descriptorSetCount= static_cast<uint32_t>(layouts.size());
    dai.pSetLayouts      = layouts.data();
    if (vkAllocateDescriptorSets(device_, &dai, compute_desc_sets_.data()) != VK_SUCCESS)
        return false;

    // Pipeline layout
    VkPipelineLayoutCreateInfo plci{};
    plci.sType            = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    plci.setLayoutCount   = 1;
    plci.pSetLayouts      = &compute_desc_layout_;
    if (vkCreatePipelineLayout(device_, &plci, nullptr, &compute_pipeline_layout_) != VK_SUCCESS)
        return false;

    // Compute shader stage
    VkPipelineShaderStageCreateInfo csi{};
    csi.sType           = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    csi.stage           = VK_SHADER_STAGE_COMPUTE_BIT;
    csi.module          = comp_mod_;
    csi.pName           = "main";

    // Compute pipeline
    VkComputePipelineCreateInfo cp_ci{};
    cp_ci.sType                        = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
    cp_ci.stage                        = csi;
    cp_ci.layout                       = compute_pipeline_layout_;
    if (vkCreateComputePipelines(device_, VK_NULL_HANDLE, 1, &cp_ci, nullptr, &compute_pipeline_) != VK_SUCCESS) {
        fprintf(stderr, "Failed to create compute pipeline\n");
        return false;
    }

    printf("Compute pipeline created\n");
    return true;
}

bool Engine::push_state(const std::vector<float>& pos_data, const std::vector<float>& vel_data, uint32_t count) {
    bool count_changed = (count != n_);
    n_ = count;
    if (count == 0) { dirty_ = true; return true; }

    // Layout: [x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz] = 14 floats per splat = 56 bytes stride
    VkDeviceSize buf_size     = static_cast<VkDeviceSize>(count) * 14ULL * sizeof(float);
    VkDeviceSize vec4_size    = static_cast<VkDeviceSize>(count) * 4ULL * sizeof(float);  // for vel/acc buffers

    // ── Create or resize pos_buf_ (dirty flag gates reallocation) ─────────────
    if (dirty_ || count_changed || pos_buf_ == VK_NULL_HANDLE) {
        // Create or resize vertex buffer
        VkBuffer old_buf = pos_buf_;
        VkDeviceMemory old_mem = pos_mem_;

        VkBufferCreateInfo bci{};
        bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size        = buf_size;
        bci.usage       = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT | VK_BUFFER_USAGE_VERTEX_BUFFER_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &pos_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, pos_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType       = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &pos_mem_);
        vkBindBufferMemory(device_, pos_buf_, pos_mem_, 0);

        if (old_buf) { vkDestroyBuffer(device_, old_buf, nullptr); vkFreeMemory(device_, old_mem, nullptr); }
    }

    // ── Create vel_buf_ and acc_buf_ for compute ───────────────────────────────
    bool need_vel_upload = (dirty_ || count_changed) && !vel_data.empty();
    if (dirty_ || count_changed || vel_buf_ == VK_NULL_HANDLE) {
        for (auto& buf : {std::pair<VkBuffer&, VkDeviceMemory&>{vel_buf_, vel_mem_},
                          std::pair<VkBuffer&, VkDeviceMemory&>{acc_buf_, acc_mem_}}) {
            VkBuffer old_b = buf.first;
            VkDeviceMemory old_m = buf.second;
            VkBufferCreateInfo bci{};
            bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
            bci.size        = vec4_size;
            bci.usage       = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT;
            bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
            vkCreateBuffer(device_, &bci, nullptr, &buf.first);
            VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, buf.first, &mr);
            VkMemoryAllocateInfo ai{};
            ai.sType       = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
            ai.allocationSize = mr.size;
            ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
            vkAllocateMemory(device_, &ai, nullptr, &buf.second);
            vkBindBufferMemory(device_, buf.first, buf.second, 0);
            if (old_b) { vkDestroyBuffer(device_, old_b, nullptr); vkFreeMemory(device_, old_m, nullptr); }
        }
    }

    // ── Upload velocity data when available and needed ─────────────────────────
    if (need_vel_upload && vel_buf_ != VK_NULL_HANDLE && !vel_data.empty()) {
        VkBufferCreateInfo staging_ci{};
        staging_ci.sType      = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        staging_ci.size       = vec4_size;
        staging_ci.usage      = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
        staging_ci.sharingMode= VK_SHARING_MODE_EXCLUSIVE;
        VkBuffer staging_buf;
        vkCreateBuffer(device_, &staging_ci, nullptr, &staging_buf);

        VkMemoryRequirements mr_s; vkGetBufferMemoryRequirements(device_, staging_buf, &mr_s);
        VkMemoryAllocateInfo ai_s{};
        ai_s.sType       = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai_s.allocationSize = mr_s.size;
        ai_s.memoryTypeIndex = find_mem_type(mr_s.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        VkDeviceMemory staging_mem;
        vkAllocateMemory(device_, &ai_s, nullptr, &staging_mem);
        vkBindBufferMemory(device_, staging_buf, staging_mem, 0);

        void* mapped;
        vkMapMemory(device_, staging_mem, 0, vec4_size, 0, &mapped);
        std::memcpy(mapped, vel_data.data(), vec4_size);
        vkUnmapMemory(device_, staging_mem);

        VkCommandBuffer cb = begin_single_time_cmd();
        VkBufferCopy copy{};
        copy.srcOffset = 0; copy.dstOffset = 0; copy.size = vec4_size;
        vkCmdCopyBuffer(cb, staging_buf, vel_buf_, 1, &copy);
        end_single_time_cmd(cb);

        vkDestroyBuffer(device_, staging_buf, nullptr);
        vkFreeMemory(device_, staging_mem, nullptr);
    }

    // ── Upload position data via staging (always, since particles move every frame) ─
    VkBufferCreateInfo staging_ci{};
    staging_ci.sType      = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    staging_ci.size       = buf_size;
    staging_ci.usage      = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
    staging_ci.sharingMode= VK_SHARING_MODE_EXCLUSIVE;
    VkBuffer staging_buf;
    vkCreateBuffer(device_, &staging_ci, nullptr, &staging_buf);

    VkMemoryRequirements mr_s; vkGetBufferMemoryRequirements(device_, staging_buf, &mr_s);
    VkMemoryAllocateInfo ai_s{};
    ai_s.sType       = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai_s.allocationSize = mr_s.size;
    ai_s.memoryTypeIndex = find_mem_type(mr_s.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    VkDeviceMemory staging_mem;
    vkAllocateMemory(device_, &ai_s, nullptr, &staging_mem);
    vkBindBufferMemory(device_, staging_buf, staging_mem, 0);

    void* mapped;
    vkMapMemory(device_, staging_mem, 0, buf_size, 0, &mapped);
    std::memcpy(mapped, pos_data.data(), buf_size);
    vkUnmapMemory(device_, staging_mem);

    // Copy staging → device local
    VkCommandBuffer cb = begin_single_time_cmd();
    VkBufferCopy copy{};
    copy.srcOffset = 0; copy.dstOffset = 0; copy.size = buf_size;
    vkCmdCopyBuffer(cb, staging_buf, pos_buf_, 1, &copy);
    end_single_time_cmd(cb);

    vkDestroyBuffer(device_, staging_buf, nullptr);
    vkFreeMemory(device_, staging_mem, nullptr);

    // Update graphics descriptor (binding 1 = vertex storage buffer)
    VkDescriptorBufferInfo buf_info{};
    buf_info.buffer = pos_buf_;
    buf_info.offset = 0;
    buf_info.range  = VK_WHOLE_SIZE;
    VkWriteDescriptorSet writes[1] = {};
    writes[0].sType            = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    writes[0].dstSet           = desc_sets_[image_idx_];
    writes[0].dstBinding       = 1;
    writes[0].dstArrayElement  = 0;
    writes[0].descriptorCount  = 1;
    writes[0].descriptorType   = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    writes[0].pBufferInfo      = &buf_info;
    vkUpdateDescriptorSets(device_, 1, writes, 0, nullptr);

    // (Re)build the GPU radix-sort buffers for this splat count (keys + ping-pong indices + hist).
    ensure_sort_buffers(count);

    dirty_ = false;
    return true;
}

// ── Camera: simple orbiting camera ───────────────────────────────────────────────────────

static void perspective(float* out, float fov_y, float aspect, float zNear, float zFar) {
    // Column-major 4x4. Vulkan NDC is Y-down (unlike OpenGL/WebGL, which are Y-up), so the Y row
    // is NEGATED: this is the single place that defines "up" on screen. World +Y stays up.
    float f = 1.0f / tanf(fov_y * 0.5f);
    std::memset(out, 0, sizeof(float) * 16);
    out[0]  = f / aspect;
    out[5]  = -f;   // Vulkan Y-flip
    out[10] = (zFar + zNear) / (zNear - zFar);
    out[11] = -1.0f;
    out[14] = (2.0f * zFar * zNear) / (zNear - zFar);
}

static void look_at(float* out, const float* eye, const float* center, const float* up) {
    // Column-major 4x4
    float zx = eye[0] - center[0], zy = eye[1] - center[1], zz = eye[2] - center[2];
    float len = sqrtf(zx*zx + zy*zy + zz*zz);
    zx /= len; zy /= len; zz /= len;

    float xx = up[1]*zz - up[2]*zy, xy = up[2]*zx - up[0]*zz, xz = up[0]*zy - up[1]*zx;
    len = sqrtf(xx*xx + xy*xy + xz*xz);
    if (len > 1e-6) { xx /= len; xy /= len; xz /= len; }
    else { xx = 1.0f; xy = 0.0f; xz = 0.0f; }

    float yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;

    out[0] = xx;   out[1] = yx;   out[2] = zx;   out[3] = 0.0f;
    out[4] = xy;   out[5] = yy;   out[6] = zy;   out[7] = 0.0f;
    out[8] = xz;   out[9] = yz;   out[10]= zz;   out[11]= 0.0f;
    out[12]= -(xx*eye[0]+xy*eye[1]+xz*eye[2]);
    out[13]= -(yx*eye[0]+yy*eye[1]+yz*eye[2]);
    out[14]= -(zx*eye[0]+zy*eye[1]+zz*eye[2]);
    out[15]= 1.0f;
}

// ── Image layout transition (pipeline barrier) ──────────────────────────────────────
static void transition_image_layout(VkCommandBuffer cb, VkImage img,
                                    VkImageLayout old_layout, VkImageLayout new_layout,
                                    VkAccessFlags src_access, VkAccessFlags dst_access,
                                    VkPipelineStageFlags src_stage, VkPipelineStageFlags dst_stage) {
    VkImageMemoryBarrier barrier{};
    barrier.sType               = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    barrier.oldLayout           = old_layout;
    barrier.newLayout           = new_layout;
    barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    barrier.image               = img;
    barrier.subresourceRange.aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT;
    barrier.subresourceRange.baseMipLevel   = 0;
    barrier.subresourceRange.levelCount     = 1;
    barrier.subresourceRange.baseArrayLayer = 0;
    barrier.subresourceRange.layerCount     = 1;
    barrier.srcAccessMask = src_access;
    barrier.dstAccessMask = dst_access;
    vkCmdPipelineBarrier(cb, src_stage, dst_stage, 0, 0, nullptr, 0, nullptr, 1, &barrier);
}

// ── Compute dispatch + velocity readback ───────────────────────────────────────────
// Dispatches the compute shader, then copies acc_buf (new velocities) back to CPU.
// Returns false if compute pipeline is unavailable.
bool Engine::dispatch_compute(std::vector<float>& out_velocities) {
    if (compute_pipeline_ == VK_NULL_HANDLE || n_ == 0) return false;

    // Create readback staging buffer lazily
    VkDeviceSize vec4_size = static_cast<VkDeviceSize>(n_) * 4ULL * sizeof(float);
    static VkBuffer readback_buf = VK_NULL_HANDLE;
    static VkDeviceMemory readback_mem = VK_NULL_HANDLE;
    static VkDeviceSize readback_size = 0;
    if (readback_buf == VK_NULL_HANDLE || vec4_size != readback_size) {
        if (readback_buf) { vkDestroyBuffer(device_, readback_buf, nullptr); vkFreeMemory(device_, readback_mem, nullptr); }
        VkBufferCreateInfo bci{};
        bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size        = vec4_size;
        bci.usage       = VK_BUFFER_USAGE_TRANSFER_DST_BIT | VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &readback_buf);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, readback_buf, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType       = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &readback_mem);
        vkBindBufferMemory(device_, readback_buf, readback_mem, 0);
        readback_size = vec4_size;
    }

    // Record compute dispatch in a single-time command buffer
    VkCommandBuffer cb = begin_single_time_cmd();

    // Bind compute pipeline and descriptor set (use frame 0 for simplicity — single-threaded)
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_COMPUTE, compute_pipeline_);

    // Update descriptors for frame 0
    VkDescriptorBufferInfo pos_info{}, vel_info{}, acc_info{};
    pos_info.buffer = pos_buf_; pos_info.offset = 0; pos_info.range = VK_WHOLE_SIZE;
    vel_info.buffer = vel_buf_; vel_info.offset = 0; vel_info.range = VK_WHOLE_SIZE;
    acc_info.buffer = readback_buf; acc_info.offset = 0; acc_info.range = VK_WHOLE_SIZE;

    VkWriteDescriptorSet writes[3] = {};
    writes[0].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET; writes[0].dstSet = compute_desc_sets_[0];
    writes[0].dstBinding = 0; writes[0].descriptorCount = 1; writes[0].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    writes[0].pBufferInfo = &pos_info;
    writes[1].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET; writes[1].dstSet = compute_desc_sets_[0];
    writes[1].dstBinding = 1; writes[1].descriptorCount = 1; writes[1].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    writes[1].pBufferInfo = &vel_info;
    writes[2].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET; writes[2].dstSet = compute_desc_sets_[0];
    writes[2].dstBinding = 2; writes[2].descriptorCount = 1; writes[2].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    writes[2].pBufferInfo = &acc_info;
    vkUpdateDescriptorSets(device_, 3, writes, 0, nullptr);

    // Upload compute params to dedicated buffer
    if (comp_params_buf_ == VK_NULL_HANDLE) {
        VkBufferCreateInfo bci{};
        bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size        = 64;  // 10 floats + padding, aligned to 16 bytes
        bci.usage       = VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &comp_params_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, comp_params_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType       = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &comp_params_mem_);
        vkBindBufferMemory(device_, comp_params_buf_, comp_params_mem_, 0);
    }

    struct alignas(16) ComputeParams {
        float G, eps2, rw, rb, rc, kw, kb, gamma_w, dt;
        float _pad[3];
    } cparams{cfg_.G, 1e-8f, cfg_.rw, cfg_.rb, cfg_.rc, cfg_.kw, cfg_.kb, cfg_.gamma_w, cfg_.dt, {0}};

    VkBufferCreateInfo staging_ci{};
    staging_ci.sType      = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    staging_ci.size       = 64;
    staging_ci.usage      = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
    staging_ci.sharingMode= VK_SHARING_MODE_EXCLUSIVE;
    VkBuffer staging_buf;
    vkCreateBuffer(device_, &staging_ci, nullptr, &staging_buf);

    VkMemoryRequirements mr_s; vkGetBufferMemoryRequirements(device_, staging_buf, &mr_s);
    VkMemoryAllocateInfo ai_s{};
    ai_s.sType       = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai_s.allocationSize = mr_s.size;
    ai_s.memoryTypeIndex = find_mem_type(mr_s.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    VkDeviceMemory staging_mem;
    vkAllocateMemory(device_, &ai_s, nullptr, &staging_mem);
    vkBindBufferMemory(device_, staging_buf, staging_mem, 0);

    void* mapped;
    vkMapMemory(device_, staging_mem, 0, 64, 0, &mapped);
    std::memcpy(mapped, &cparams, sizeof(cparams));
    vkUnmapMemory(device_, staging_mem);

    VkCommandBuffer cb_params = begin_single_time_cmd();
    VkBufferCopy bc_p{}; bc_p.size = 64;
    vkCmdCopyBuffer(cb_params, staging_buf, comp_params_buf_, 1, &bc_p);
    end_single_time_cmd(cb_params);
    vkDestroyBuffer(device_, staging_buf, nullptr);
    vkFreeMemory(device_, staging_mem, nullptr);

    // Bind compute params descriptor
    VkDescriptorBufferInfo params_info{};
    params_info.buffer = comp_params_buf_;
    params_info.offset = 0;
    params_info.range = VK_WHOLE_SIZE;
    VkWriteDescriptorSet param_write{};
    param_write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    param_write.dstSet = compute_desc_sets_[0];
    param_write.dstBinding = 3;
    param_write.descriptorCount = 1;
    param_write.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    param_write.pBufferInfo = &params_info;
    vkUpdateDescriptorSets(device_, 1, &param_write, 0, nullptr);

    // Dispatch: one workgroup per particle batch of 256
    uint32_t groups = (n_ + 255) / 256;
    vkCmdDispatch(cb, groups, 1, 1);

    end_single_time_cmd(cb);

    // Read back velocities from readback buffer
    out_velocities.resize(n_ * 4);
    void* rb_mapped;
    vkMapMemory(device_, readback_mem, 0, vec4_size, 0, &rb_mapped);
    std::memcpy(out_velocities.data(), rb_mapped, vec4_size);
    vkUnmapMemory(device_, readback_mem);

    // Copy readback results back to acc_buf_ and also sync to vel_buf_ for next frame's input
    cb = begin_single_time_cmd();
    VkBufferCopy bc{}; bc.size = vec4_size;
    vkCmdCopyBuffer(cb, readback_buf, acc_buf_, 1, &bc);
    end_single_time_cmd(cb);

    // Sync acc → vel so next dispatch reads current velocities
    cb = begin_single_time_cmd();
    vkCmdCopyBuffer(cb, acc_buf_, vel_buf_, 1, &bc);
    end_single_time_cmd(cb);

    return true;
}

// ── Membrane streaming + frame capture (the C++ engine is the emission target) ──────────

void Engine::ensure_capture_staging() {
    VkDeviceSize size = static_cast<VkDeviceSize>(extent_.width) * extent_.height * 4;
    if (capture_staging_ != VK_NULL_HANDLE && size == capture_staging_size_) return;
    if (capture_staging_ != VK_NULL_HANDLE) {
        vkDestroyBuffer(device_, capture_staging_, nullptr);
        vkFreeMemory(device_, capture_staging_mem_, nullptr);
        capture_staging_ = VK_NULL_HANDLE;
    }
    VkBufferCreateInfo bci{};
    bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bci.size        = size;
    bci.usage       = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
    bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    vkCreateBuffer(device_, &bci, nullptr, &capture_staging_);
    VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, capture_staging_, &mr);
    VkMemoryAllocateInfo ai{};
    ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize  = mr.size;
    ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    vkAllocateMemory(device_, &ai, nullptr, &capture_staging_mem_);
    vkBindBufferMemory(device_, capture_staging_, capture_staging_mem_, 0);
    capture_staging_size_ = size;
}

// The glass channel's staging, allocated by the SAME law as the pixel-clean one
// (host-visible + coherent, sized to the swapchain extent). It is a SEPARATE
// buffer on purpose: the two channels must never share a destination, or a glass
// grab silently overwrites the frame /frame and the reel just handed out.
void Engine::ensure_glass_staging() {
    VkDeviceSize size = static_cast<VkDeviceSize>(extent_.width) * extent_.height * 4;
    if (glass_staging_ != VK_NULL_HANDLE && size == glass_staging_size_) return;
    if (glass_staging_ != VK_NULL_HANDLE) {
        vkDestroyBuffer(device_, glass_staging_, nullptr);
        vkFreeMemory(device_, glass_staging_mem_, nullptr);
        glass_staging_ = VK_NULL_HANDLE;
    }
    VkBufferCreateInfo bci{};
    bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bci.size        = size;
    bci.usage       = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
    bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    vkCreateBuffer(device_, &bci, nullptr, &glass_staging_);
    VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, glass_staging_, &mr);
    VkMemoryAllocateInfo ai{};
    ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize  = mr.size;
    ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    vkAllocateMemory(device_, &ai, nullptr, &glass_staging_mem_);
    vkBindBufferMemory(device_, glass_staging_, glass_staging_mem_, 0);
    glass_staging_size_ = size;
}

// ── THE GLASS CHANNEL — one law, two loops ─────────────────────────────────────
// Both frame() and frame_idle_ui() draw the Studio into the swapchain, and both
// must service the capture requests. Sharing ONE recorder is the whole point:
// two copies of this law is two things that drift, and the drift shows up as a
// capture that works in one loop and times out in the other -- which is exactly
// the bug this function was written to fix (see frame_idle_ui).
//
// `cur` is the swapchain image's layout on entry: PRESENT_SRC after the UI render
// pass, TRANSFER_DST when only the clear/blit ran. It is handed back as
// PRESENT_SRC, because the queue presents this image.
static void record_glass_copy(VkCommandBuffer cb, VkImage swap_img,
                              VkImageLayout cur, VkBuffer dst, VkExtent2D extent) {
    if (cur != VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL)
        transition_image_layout(cb, swap_img, cur, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                                VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_TRANSFER_WRITE_BIT,
                                VK_ACCESS_TRANSFER_READ_BIT,
                                VK_PIPELINE_STAGE_TRANSFER_BIT | VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
                                VK_PIPELINE_STAGE_TRANSFER_BIT);
    VkBufferImageCopy greg{};
    greg.bufferOffset      = 0;
    greg.bufferRowLength   = 0;
    greg.bufferImageHeight = 0;
    greg.imageSubresource.aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT;
    greg.imageSubresource.mipLevel       = 0;
    greg.imageSubresource.baseArrayLayer = 0;
    greg.imageSubresource.layerCount     = 1;
    greg.imageOffset = {0, 0, 0};
    greg.imageExtent = {extent.width, extent.height, 1};
    vkCmdCopyImageToBuffer(cb, swap_img, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, dst, 1, &greg);
    transition_image_layout(cb, swap_img, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                            VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                            VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_MEMORY_READ_BIT,
                            VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
}

// D8: THE AUTHORED FK TOPOLOGY — these links are the native rig's semantic
// parent map. The JNT1 upload intentionally carries centers/axes/ROM but no
// parent array, so the overlay uses this map and refuses spatial inference.
void Engine::push_rig_overlay() {
    std::vector<StudioRigSegment> segments;
    if (!rig_overlay_on() || !joints_loaded_ || !j_state_map_ || !last_vp_valid_) {
        ui_.set_rig_segments(std::move(segments), rig_overlay_on());
        return;
    }

    static const std::pair<const char*, const char*> FK[] = {
        {"neck", "jaw"},
        {"neck", "spine_upper"}, {"spine_upper", "spine_mid"},
        {"spine_mid", "spine_lower"}, {"spine_lower", "tail_base"},
        {"tail_base", "tail_mid"},
        {"spine_upper", "shoulder_L"}, {"shoulder_L", "elbow_L"},
        {"elbow_L", "wrist_L"},
        {"spine_upper", "shoulder_R"}, {"shoulder_R", "elbow_R"},
        {"elbow_R", "wrist_R"},
        {"spine_lower", "hip_L"}, {"hip_L", "knee_L"},
        {"knee_L", "ankle_L"},
        {"spine_lower", "hip_R"}, {"hip_R", "knee_R"},
        {"knee_R", "ankle_R"}
    };
    const int selected = selected_joint_.load(std::memory_order_relaxed);
    const float* st = static_cast<const float*>(j_state_map_);
    for (const auto& edge : FK) {
        int a = joint_index(edge.first), b = joint_index(edge.second);
        if (a < 0 || b < 0 || a >= static_cast<int>(j_n_joints_) || b >= static_cast<int>(j_n_joints_))
            continue;  // absent anatomy is omitted, never replaced by a guessed link
        float pa[3] = { st[a * 8 + 0], st[a * 8 + 1], st[a * 8 + 2] };
        float pb[3] = { st[b * 8 + 0], st[b * 8 + 1], st[b * 8 + 2] };
        float x0, y0, x1, y1;
        if (project_world(pa, x0, y0) && project_world(pb, x1, y1))
            segments.push_back({x0, y0, x1, y1, a == selected || b == selected});
    }
    ui_.set_rig_segments(std::move(segments), true);
}

// ── THE VIEWPORT REFERENCE FRAME (2026-08-31) ───────────────────────────────────
// The eye's #1 defect: an empty viewport reads as a crashed renderer, not as an
// empty scene. This draws a ground grid + an XYZ triad so the centre of the window
// has mass and the eye has somewhere to land.
//
// EVERY NUMBER IS DERIVED FROM THE CAMERA, none chosen:
//   spacing = the power of ten nearest to radius/5 — so the grid reads at the
//             same density whether you are looking at a paw or a planet, and it
//             steps by decades as you dolly instead of sliding continuously
//   extent  = spacing * ceil(radius / spacing) — the grid always reaches past the
//             orbit sphere, so it never ends inside the frame
//   axis len= one spacing, so the triad is exactly one grid cell long
// The plane is y = 0 with +Y up, which is the engine's own convention
// (perspective() negates the Y row so world +Y stays up on screen).
void Engine::push_grid_overlay() {
    std::vector<StudioGridLine> lines;
    lines.reserve(128);
    ui_.set_viewport_empty(n_ == 0 && !has_mesh_);
    if (!last_vp_valid_) { ui_.set_grid_lines(std::move(lines)); return; }

    const float R  = (g_cam.radius > 1e-3f) ? g_cam.radius : 1e-3f;
    const float sp = powf(10.0f, floorf(log10f(R / 5.0f)));
    const int   n  = (int)ceilf(R / sp);
    const float h  = sp * static_cast<float>(n);

    auto seg = [&](float ax, float ay, float az, float bx, float by, float bz,
                   float r, float g, float b, float a) {
        float p0[3] = { ax, ay, az }, p1[3] = { bx, by, bz };
        float x0, y0, x1, y1;
        if (project_world(p0, x0, y0) && project_world(p1, x1, y1))
            lines.push_back({ x0, y0, x1, y1, r, g, b, a });
    };

    // the two lines through the origin read as the axes of the plane, so they are
    // brighter than the rest — no separate legend, no invented colour key
    // 2026-09-02, the eye on the glass: "the perspective grid is so low-contrast
    // (dim blue on near-black) that it doesn't read as a floor" — measured: the
    // bottom third's max luminance was 24/765. THE PERCEPTION FLOOR LAW: a line
    // that cannot clear ~40/255 on black does not exist for the viewer. The
    // plane reads as a floor now; the axes-of-the-plane distinction is kept.
    const float GR = 0.30f, GG = 0.34f, GB = 0.46f, GA = 0.70f;
    const float AR = 0.42f, AG = 0.48f, AB = 0.62f, AA = 0.90f;
    for (int i = -n; i <= n; ++i) {
        const float v = sp * static_cast<float>(i);
        const bool  mid = (i == 0);
        seg(-h, 0.f, v, h, 0.f, v, mid ? AR : GR, mid ? AG : GG, mid ? AB : GB, mid ? AA : GA);
        seg(v, 0.f, -h, v, 0.f, h, mid ? AR : GR, mid ? AG : GG, mid ? AB : GB, mid ? AA : GA);
    }
    // the triad: one cell long, +X red, +Y up green, +Z blue
    // 2026-09-02, the eye: "too small and unlabeled" — alpha to 1.0 and the
    // Y arm brightened so up reads first (the eye lands on the axis gizmo as
    // the one spatial anchor); color IS the label, no text drawn.
    seg(0, 0, 0, sp, 0, 0, 1.00f, 0.40f, 0.40f, 1.f);
    seg(0, 0, 0, 0, sp, 0, 0.40f, 1.00f, 0.50f, 1.f);
    seg(0, 0, 0, 0, 0, sp, 0.45f, 0.70f, 1.00f, 1.f);

    ui_.set_grid_lines(std::move(lines));
}

void Engine::update_camera_matrices(float proj[16], float view[16]) {
    float aspect = static_cast<float>(extent_.width) / static_cast<float>(extent_.height);
    perspective(proj, 45.0f * 3.14159265f / 180.0f, aspect, 0.1f, 1000.0f);

    update_camera_input(g_cam, cfg_.dt);

    // Build eye position from spherical coords + pan offset
    float c = cosf(g_cam.phi), s = sinf(g_cam.phi);
    float cx = cosf(g_cam.theta), sx = sinf(g_cam.theta);
    float eye[3] = {
        g_cam.target[0] + g_cam.radius * c * sx + g_cam.pan_x,
        g_cam.target[1] + g_cam.radius * s              + g_cam.pan_y,
        g_cam.target[2] - g_cam.radius * c * cx
    };
    // Up vector = ∂(eye)/∂phi (the direction the camera tilts "up" as elevation increases).
    // This is unit-length for every (theta, phi) — no pole singularity — so the camera can spin
    // continuously over the top (free rotation on both axes) without the old +-1.55 rad stopper.
    float up_vec[3] = {-s * sx, c, s * cx};
    look_at(view, eye, g_cam.target, up_vec);
    // publish the eye too: the frost light and anything else that needs "where the
    // camera is" reads last_eye_, so there is exactly one camera law.
    last_eye_[0] = eye[0]; last_eye_[1] = eye[1]; last_eye_[2] = eye[2];
    // C1: stash the VP for the gizmo, /project, and the viewport grid.
    //
    // sizeof(proj) is 8, NOT 64 — `float proj[16]` in a parameter list DECAYS TO
    // A POINTER, so a straight sizeof copies two floats and leaves the rest zero.
    // A zeroed projection makes cw == 0, so project_world() answers "behind the
    // camera" for every point in the world and the grid silently does not exist.
    // The size is spelled out; never let a decayed array measure itself.
    std::memcpy(last_proj_, proj, 16 * sizeof(float));
    std::memcpy(last_view_, view, 16 * sizeof(float));
    last_vp_valid_ = true;
}

// ── GPU bitonic sort (back-to-front splat ordering — no CPU in the per-frame path) ─────────

static uint32_t next_pow2(uint32_t v) {
    v--;
    v |= v >> 1; v |= v >> 2; v |= v >> 4; v |= v >> 8; v |= v >> 16;
    return v + 1;
}

bool Engine::create_sort_pipeline() {
    if (sort_mod_ == VK_NULL_HANDLE) { fprintf(stderr, "sort.spv not loaded\n"); return false; }

    VkDescriptorSetLayoutBinding bindings[3] = {};
    for (uint32_t i = 0; i < 3; ++i) {
        bindings[i].binding            = i;
        bindings[i].descriptorType     = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        bindings[i].descriptorCount    = 1;
        bindings[i].stageFlags         = VK_SHADER_STAGE_COMPUTE_BIT;
    }
    VkDescriptorSetLayoutCreateInfo dslci{};
    dslci.sType         = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dslci.bindingCount  = 3;
    dslci.pBindings     = bindings;
    if (vkCreateDescriptorSetLayout(device_, &dslci, nullptr, &sort_desc_layout_) != VK_SUCCESS) return false;

    VkDescriptorPoolSize pool_size{};
    pool_size.type            = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    pool_size.descriptorCount = 3;
    VkDescriptorPoolCreateInfo dpci{};
    dpci.sType            = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dpci.maxSets          = 1;
    dpci.poolSizeCount    = 1;
    dpci.pPoolSizes       = &pool_size;
    if (vkCreateDescriptorPool(device_, &dpci, nullptr, &sort_desc_pool_) != VK_SUCCESS) return false;

    VkDescriptorSetAllocateInfo dai{};
    dai.sType              = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dai.descriptorPool     = sort_desc_pool_;
    dai.descriptorSetCount = 1;
    dai.pSetLayouts        = &sort_desc_layout_;
    if (vkAllocateDescriptorSets(device_, &dai, &sort_desc_set_) != VK_SUCCESS) return false;

    VkPushConstantRange pcr{};
    pcr.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    pcr.offset     = 0;
    pcr.size       = 32;   // mode, j, k, count, zx, zy, zz, tz

    VkPipelineLayoutCreateInfo plci{};
    plci.sType                  = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    plci.setLayoutCount         = 1;
    plci.pSetLayouts            = &sort_desc_layout_;
    plci.pushConstantRangeCount = 1;
    plci.pPushConstantRanges    = &pcr;
    if (vkCreatePipelineLayout(device_, &plci, nullptr, &sort_layout_) != VK_SUCCESS) return false;

    VkPipelineShaderStageCreateInfo stage{};
    stage.sType  = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stage.stage  = VK_SHADER_STAGE_COMPUTE_BIT;
    stage.module = sort_mod_;
    stage.pName  = "main";

    VkComputePipelineCreateInfo cpci{};
    cpci.sType  = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
    cpci.stage  = stage;
    cpci.layout = sort_layout_;
    if (vkCreateComputePipelines(device_, VK_NULL_HANDLE, 1, &cpci, nullptr, &sort_pipe_) != VK_SUCCESS) {
        fprintf(stderr, "Failed to create sort compute pipeline\n");
        return false;
    }
    return true;
}

void Engine::ensure_sort_buffers(uint32_t count) {
    if (sort_pipe_ == VK_NULL_HANDLE) return;

    uint32_t padded = next_pow2(count);
    if (sort_count_ != count || sort_idx_buf_ == VK_NULL_HANDLE) {
        sort_count_ = count;
        sort_padded_ = padded;
        sort_ready_ = false;

        if (keys_buf_)     { vkDestroyBuffer(device_, keys_buf_, nullptr);     vkFreeMemory(device_, keys_mem_, nullptr);     keys_buf_ = VK_NULL_HANDLE; }
        if (sort_idx_buf_) { vkDestroyBuffer(device_, sort_idx_buf_, nullptr); vkFreeMemory(device_, sort_idx_mem_, nullptr); sort_idx_buf_ = VK_NULL_HANDLE; }

        VkDeviceSize padded_size = static_cast<VkDeviceSize>(padded) * sizeof(uint32_t);

        auto create_buf = [&](VkDeviceSize size, VkBufferUsageFlags usage, VkBuffer& buf, VkDeviceMemory& mem) {
            VkBufferCreateInfo bci{};
            bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
            bci.size        = size;
            bci.usage       = usage;
            bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
            vkCreateBuffer(device_, &bci, nullptr, &buf);
            VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, buf, &mr);
            VkMemoryAllocateInfo ai{};
            ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
            ai.allocationSize  = mr.size;
            ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
            vkAllocateMemory(device_, &ai, nullptr, &mem);
            vkBindBufferMemory(device_, buf, mem, 0);
        };

        create_buf(padded_size, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT, keys_buf_, keys_mem_);
        create_buf(padded_size, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_INDEX_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT, sort_idx_buf_, sort_idx_mem_);

        // init: indices = 0..count-1 (padding entries clamp to 0), keys = 0xFFFFFFFF for padding
        // (sorts them to the end; the draw only reads the first `count` indices).
        std::vector<uint32_t> init_idx(padded), init_keys(padded, 0xFFFFFFFFu);
        for (uint32_t i = 0; i < padded; ++i) init_idx[i] = (i < count) ? i : 0u;

        auto upload = [&](VkBuffer dst, const void* data, VkDeviceSize size) {
            VkBufferCreateInfo sci{};
            sci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
            sci.size        = size;
            sci.usage       = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
            sci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
            VkBuffer sb; vkCreateBuffer(device_, &sci, nullptr, &sb);
            VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, sb, &mr);
            VkMemoryAllocateInfo ai{};
            ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
            ai.allocationSize  = mr.size;
            ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
            VkDeviceMemory sm; vkAllocateMemory(device_, &ai, nullptr, &sm);
            vkBindBufferMemory(device_, sb, sm, 0);
            void* mapped; vkMapMemory(device_, sm, 0, size, 0, &mapped);
            std::memcpy(mapped, data, size);
            vkUnmapMemory(device_, sm);
            VkCommandBuffer cb = begin_single_time_cmd();
            VkBufferCopy bc{}; bc.size = size;
            vkCmdCopyBuffer(cb, sb, dst, 1, &bc);
            end_single_time_cmd(cb);
            vkDestroyBuffer(device_, sb, nullptr);
            vkFreeMemory(device_, sm, nullptr);
        };

        upload(keys_buf_, init_keys.data(), padded_size);
        upload(sort_idx_buf_, init_idx.data(), padded_size);
    }

    // (Re)bind the descriptor set — binding 0 (pos_buf_) may be a NEW buffer if push_state
    // reallocated the vertex buffer while the count stayed the same.
    VkDescriptorBufferInfo infos[3] = {};
    infos[0].buffer = pos_buf_;      infos[0].offset = 0; infos[0].range = VK_WHOLE_SIZE;
    infos[1].buffer = keys_buf_;     infos[1].offset = 0; infos[1].range = VK_WHOLE_SIZE;
    infos[2].buffer = sort_idx_buf_; infos[2].offset = 0; infos[2].range = VK_WHOLE_SIZE;
    VkWriteDescriptorSet writes[3] = {};
    for (uint32_t i = 0; i < 3; ++i) {
        writes[i].sType           = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[i].dstSet          = sort_desc_set_;
        writes[i].dstBinding      = i;
        writes[i].dstArrayElement = 0;
        writes[i].descriptorCount = 1;
        writes[i].descriptorType  = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        writes[i].pBufferInfo     = &infos[i];
    }
    vkUpdateDescriptorSets(device_, 3, writes, 0, nullptr);

    sort_ready_ = true;
}

void Engine::destroy_sort_resources() {
    if (keys_buf_)     { vkDestroyBuffer(device_, keys_buf_, nullptr);     vkFreeMemory(device_, keys_mem_, nullptr);     keys_buf_ = VK_NULL_HANDLE; }
    if (sort_idx_buf_) { vkDestroyBuffer(device_, sort_idx_buf_, nullptr); vkFreeMemory(device_, sort_idx_mem_, nullptr); sort_idx_buf_ = VK_NULL_HANDLE; }
    if (sort_pipe_)    { vkDestroyPipeline(device_, sort_pipe_, nullptr); sort_pipe_ = VK_NULL_HANDLE; }
    if (sort_layout_)  { vkDestroyPipelineLayout(device_, sort_layout_, nullptr); sort_layout_ = VK_NULL_HANDLE; }
    if (sort_desc_pool_) { vkDestroyDescriptorPool(device_, sort_desc_pool_, nullptr); sort_desc_pool_ = VK_NULL_HANDLE; }
    if (sort_desc_layout_) { vkDestroyDescriptorSetLayout(device_, sort_desc_layout_, nullptr); sort_desc_layout_ = VK_NULL_HANDLE; }
    if (sort_mod_)     { vkDestroyShaderModule(device_, sort_mod_, nullptr); sort_mod_ = VK_NULL_HANDLE; }
    sort_count_ = 0;
    sort_padded_ = 0;
    sort_ready_ = false;
}

// ── GPU skinning (LBS over the 3DGS splats — skin.comp) ─────────────────────────────────

// Staging -> device-local buffer upload (same pattern as push_state / ensure_sort_buffers).
// Destroys any previous buffer first. Call only when the GPU is idle (vkDeviceWaitIdle).
void Engine::upload_buffer(const void* data, VkDeviceSize size, VkBufferUsageFlags usage,
                           VkBuffer& buf, VkDeviceMemory& mem) {
    if (buf) { vkDestroyBuffer(device_, buf, nullptr); vkFreeMemory(device_, mem, nullptr); buf = VK_NULL_HANDLE; }
    // B3: an empty upload CLEARS the slot. A 0-byte vkCreateBuffer is a validation error
    // and the NULL buffer that followed crashed the engine on the next call.
    if (size == 0) return;

    VkBufferCreateInfo bci{};
    bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bci.size        = size;
    bci.usage       = usage | VK_BUFFER_USAGE_TRANSFER_DST_BIT;
    bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    vkCreateBuffer(device_, &bci, nullptr, &buf);
    VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, buf, &mr);
    VkMemoryAllocateInfo ai{};
    ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize  = mr.size;
    ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    vkAllocateMemory(device_, &ai, nullptr, &mem);
    vkBindBufferMemory(device_, buf, mem, 0);

    VkBufferCreateInfo sci{};
    sci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    sci.size        = size;
    sci.usage       = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
    sci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VkBuffer sb; vkCreateBuffer(device_, &sci, nullptr, &sb);
    VkMemoryRequirements mr_s; vkGetBufferMemoryRequirements(device_, sb, &mr_s);
    VkMemoryAllocateInfo ai_s{};
    ai_s.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai_s.allocationSize  = mr_s.size;
    ai_s.memoryTypeIndex = find_mem_type(mr_s.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    VkDeviceMemory sm; vkAllocateMemory(device_, &ai_s, nullptr, &sm);
    vkBindBufferMemory(device_, sb, sm, 0);
    void* mapped; vkMapMemory(device_, sm, 0, size, 0, &mapped);
    std::memcpy(mapped, data, size);
    vkUnmapMemory(device_, sm);
    VkCommandBuffer cb = begin_single_time_cmd();
    VkBufferCopy bc{}; bc.size = size;
    vkCmdCopyBuffer(cb, sb, buf, 1, &bc);
    end_single_time_cmd(cb);
    vkDestroyBuffer(device_, sb, nullptr);
    vkFreeMemory(device_, sm, nullptr);
}

bool Engine::create_skin_pipeline() {
    if (skin_mod_ == VK_NULL_HANDLE) { fprintf(stderr, "skin.spv not loaded\n"); return false; }

    VkDescriptorSetLayoutBinding bindings[4] = {};
    for (uint32_t i = 0; i < 4; ++i) {
        bindings[i].binding            = i;
        bindings[i].descriptorType     = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        bindings[i].descriptorCount    = 1;
        bindings[i].stageFlags         = VK_SHADER_STAGE_COMPUTE_BIT;
    }
    VkDescriptorSetLayoutCreateInfo dslci{};
    dslci.sType         = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dslci.bindingCount  = 4;
    dslci.pBindings     = bindings;
    if (vkCreateDescriptorSetLayout(device_, &dslci, nullptr, &skin_desc_layout_) != VK_SUCCESS) return false;

    VkDescriptorPoolSize pool_size{};
    pool_size.type            = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    pool_size.descriptorCount = 4;
    VkDescriptorPoolCreateInfo dpci{};
    dpci.sType            = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dpci.maxSets          = 1;
    dpci.poolSizeCount    = 1;
    dpci.pPoolSizes       = &pool_size;
    if (vkCreateDescriptorPool(device_, &dpci, nullptr, &skin_desc_pool_) != VK_SUCCESS) return false;

    VkDescriptorSetAllocateInfo dai{};
    dai.sType              = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dai.descriptorPool     = skin_desc_pool_;
    dai.descriptorSetCount = 1;
    dai.pSetLayouts        = &skin_desc_layout_;
    if (vkAllocateDescriptorSets(device_, &dai, &skin_desc_set_) != VK_SUCCESS) return false;

    VkPushConstantRange pcr{};
    pcr.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    pcr.offset     = 0;
    pcr.size       = 8;   // count, n_bones

    VkPipelineLayoutCreateInfo plci{};
    plci.sType                  = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    plci.setLayoutCount         = 1;
    plci.pSetLayouts            = &skin_desc_layout_;
    plci.pushConstantRangeCount = 1;
    plci.pPushConstantRanges    = &pcr;
    if (vkCreatePipelineLayout(device_, &plci, nullptr, &skin_layout_) != VK_SUCCESS) return false;

    VkPipelineShaderStageCreateInfo stage{};
    stage.sType  = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stage.stage  = VK_SHADER_STAGE_COMPUTE_BIT;
    stage.module = skin_mod_;
    stage.pName  = "main";

    VkComputePipelineCreateInfo cpci{};
    cpci.sType  = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
    cpci.stage  = stage;
    cpci.layout = skin_layout_;
    if (vkCreateComputePipelines(device_, VK_NULL_HANDLE, 1, &cpci, nullptr, &skin_pipe_) != VK_SUCCESS) {
        fprintf(stderr, "Failed to create skin compute pipeline\n");
        return false;
    }
    return true;
}

void Engine::destroy_skin_resources() {
    if (rest_buf_)   { vkDestroyBuffer(device_, rest_buf_, nullptr);   vkFreeMemory(device_, rest_mem_, nullptr);   rest_buf_ = VK_NULL_HANDLE; }
    if (skin_w_buf_) { vkDestroyBuffer(device_, skin_w_buf_, nullptr); vkFreeMemory(device_, skin_w_mem_, nullptr); skin_w_buf_ = VK_NULL_HANDLE; }
    if (pose_buf_)   { vkDestroyBuffer(device_, pose_buf_, nullptr);   vkFreeMemory(device_, pose_mem_, nullptr);   pose_buf_ = VK_NULL_HANDLE; }
    if (skin_pipe_)  { vkDestroyPipeline(device_, skin_pipe_, nullptr); skin_pipe_ = VK_NULL_HANDLE; }
    if (skin_layout_) { vkDestroyPipelineLayout(device_, skin_layout_, nullptr); skin_layout_ = VK_NULL_HANDLE; }
    if (skin_desc_pool_) { vkDestroyDescriptorPool(device_, skin_desc_pool_, nullptr); skin_desc_pool_ = VK_NULL_HANDLE; }
    if (skin_desc_layout_) { vkDestroyDescriptorSetLayout(device_, skin_desc_layout_, nullptr); skin_desc_layout_ = VK_NULL_HANDLE; }
    if (skin_mod_)   { vkDestroyShaderModule(device_, skin_mod_, nullptr); skin_mod_ = VK_NULL_HANDLE; }
    pose_slots_.clear();
    skin_count_ = 0;
    skin_bones_ = 0;
    skin_cur_slot_ = 0;
    skinned_active_ = false;
    skin_pose_dirty_ = false;
}

bool Engine::load_skinned(const std::vector<float>& rest, const std::vector<float>& weights,
                          uint32_t n, uint32_t n_bones) {
    if (skin_pipe_ == VK_NULL_HANDLE || n == 0 || n_bones == 0) return false;
    if (rest.size() != static_cast<size_t>(n) * 14 || weights.size() != static_cast<size_t>(n) * 4) return false;
    vkDeviceWaitIdle(device_);   // the old buffers are still referenced by the last frame's cmdbuf

    // pos_buf_ (vertex + sort binding 0) + sort buffers come from the existing upload path.
    std::vector<float> no_vel;
    if (!push_state(rest, no_vel, n)) return false;
    dirty_ = false;

    // rest splat, per-splat weights (N*4), and the pose buffer (B*7, starts at identity)
    upload_buffer(rest.data(),    static_cast<VkDeviceSize>(n) * 14 * sizeof(float),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, rest_buf_, rest_mem_);
    upload_buffer(weights.data(), static_cast<VkDeviceSize>(n) * 4 * sizeof(float),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, skin_w_buf_, skin_w_mem_);
    std::vector<float> ident(static_cast<size_t>(n_bones) * 7, 0.0f);
    for (uint32_t b = 0; b < n_bones; ++b) ident[b * 7] = 1.0f;   // qw = 1
    upload_buffer(ident.data(), static_cast<VkDeviceSize>(n_bones) * 7 * sizeof(float),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, pose_buf_, pose_mem_);

    skin_count_ = n;
    skin_bones_ = n_bones;
    skin_cur_slot_ = 0;
    pose_slots_.clear();

    // (Re)bind the skin descriptor set — pos_buf_ may be a NEW buffer after push_state.
    VkDescriptorBufferInfo infos[4] = {};
    infos[0].buffer = rest_buf_;   infos[0].offset = 0; infos[0].range = VK_WHOLE_SIZE;
    infos[1].buffer = skin_w_buf_; infos[1].offset = 0; infos[1].range = VK_WHOLE_SIZE;
    infos[2].buffer = pose_buf_;   infos[2].offset = 0; infos[2].range = VK_WHOLE_SIZE;
    infos[3].buffer = pos_buf_;    infos[3].offset = 0; infos[3].range = VK_WHOLE_SIZE;
    VkWriteDescriptorSet writes[4] = {};
    for (uint32_t i = 0; i < 4; ++i) {
        writes[i].sType           = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[i].dstSet          = skin_desc_set_;
        writes[i].dstBinding      = i;
        writes[i].dstArrayElement = 0;
        writes[i].descriptorCount = 1;
        writes[i].descriptorType  = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        writes[i].pBufferInfo     = &infos[i];
    }
    vkUpdateDescriptorSets(device_, 4, writes, 0, nullptr);

    skinned_active_  = true;
    skin_pose_dirty_ = true;   // first frame runs skin.comp with the identity pose (== rest)
    printf("Skinned splat loaded: %u splats, %u bones\n", n, n_bones);
    return true;
}

bool Engine::store_pose(uint32_t slot, const std::vector<float>& pose) {
    if (!skinned_active_) { fprintf(stderr, "store_pose: no skinned splat loaded\n"); return false; }
    if (pose.size() != static_cast<size_t>(skin_bones_) * 7) {
        fprintf(stderr, "store_pose: got %zu floats, expected %u (B=%u bones * 7)\n",
                pose.size(), skin_bones_ * 7, skin_bones_);
        return false;
    }
    pose_slots_[slot] = pose;
    return true;
}

bool Engine::apply_pose(uint32_t slot) {
    if (!skinned_active_) { fprintf(stderr, "apply_pose: no skinned splat loaded\n"); return false; }
    auto it = pose_slots_.find(slot);
    if (it == pose_slots_.end()) { fprintf(stderr, "apply_pose: slot %u not stored\n", slot); return false; }
    vkDeviceWaitIdle(device_);   // pose_buf_ may be read by the in-flight frame's skin dispatch
    upload_buffer(it->second.data(), static_cast<VkDeviceSize>(it->second.size()) * sizeof(float),
                  VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, pose_buf_, pose_mem_);
    // upload_buffer recreated pose_buf_ -> rebind binding 2
    VkDescriptorBufferInfo info{};
    info.buffer = pose_buf_; info.offset = 0; info.range = VK_WHOLE_SIZE;
    VkWriteDescriptorSet w{};
    w.sType           = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    w.dstSet          = skin_desc_set_;
    w.dstBinding      = 2;
    w.dstArrayElement = 0;
    w.descriptorCount = 1;
    w.descriptorType  = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    w.pBufferInfo     = &info;
    vkUpdateDescriptorSets(device_, 1, &w, 0, nullptr);

    skin_pose_dirty_ = true;   // posed on the next frame; the posed buffer persists after that
    skin_cur_slot_   = slot;
    printf("Pose slot %u applied (%u bones)\n", slot, skin_bones_);
    return true;
}

void Engine::toggle_pose() {
    if (!skinned_active_) return;
    uint32_t next = (skin_cur_slot_ == 0) ? 1 : 0;
    if (pose_slots_.find(next) == pose_slots_.end()) {
        printf("Pose toggle: slot %u not stored (only slot %u loaded)\n", next, skin_cur_slot_);
        return;
    }
    apply_pose(next);
}

bool Engine::load_membrane(const std::string& term, const std::vector<float>& pos, uint32_t count) {
    membrane_term_ = term;
    vkDeviceWaitIdle(device_);   // the old buffers are still referenced by the last frame's cmdbuf
    skinned_active_ = false;     // a plain membrane upload leaves the skinned path
    std::vector<float> no_vel;   // a membrane is static — no velocity to upload
    bool ok = push_state(pos, no_vel, count);
    if (ok) dirty_ = false;
    return ok;
}

void Engine::set_camera(float radius, float theta, float phi) {
    g_cam.radius = fmaxf(radius_floor(), radius);
    g_cam.theta  = theta;
    g_cam.phi    = phi;   // free spin — the camera up vector handles any elevation
    g_cam.target[0] = g_cam.target[1] = g_cam.target[2] = 0.0f;
    g_cam.pan_x = g_cam.pan_y = 0.0f;
}

bool Engine::capture_frame(std::vector<uint8_t>& out_rgba, uint32_t& w, uint32_t& h) {
    std::lock_guard<std::mutex> lk(capture_mutex_);
    if (capture_rgba_.empty()) return false;
    out_rgba = capture_rgba_;
    w = capture_w_;
    h = capture_h_;
    return true;
}

bool Engine::glass_frame(std::vector<uint8_t>& out_rgba, uint32_t& w, uint32_t& h) {
    std::lock_guard<std::mutex> lk(glass_mutex_);
    if (glass_rgba_.empty()) return false;
    out_rgba = glass_rgba_;
    w = glass_w_;
    h = glass_h_;
    return true;
}

// D3: THE REEL — every grab lands. Render thread, called from frame()'s capture
// readback, so the metadata IS the state at grab time (t, joint, theta, camera,
// light). The UI gets the pixels; the ledger (reel_json) is the dyad's channel.
void Engine::reel_note_grab() {
    if (capture_rgba_.empty() || capture_w_ == 0 || capture_h_ == 0) return;
    const int TW = StudioUI::THUMB_W, TH = StudioUI::THUMB_H;
    const uint32_t sw = capture_w_, sh = capture_h_;
    static std::vector<uint8_t> tb;
    tb.assign(static_cast<size_t>(TW) * TH * 4, 0);
    for (int ty = 0; ty < TH; ++ty) {
        uint32_t y0 = static_cast<uint32_t>(static_cast<uint64_t>(ty) * sh / TH);
        uint32_t y1 = static_cast<uint32_t>(static_cast<uint64_t>(ty + 1) * sh / TH);
        if (y1 <= y0) y1 = y0 + 1;
        for (int tx = 0; tx < TW; ++tx) {
            uint32_t x0 = static_cast<uint32_t>(static_cast<uint64_t>(tx) * sw / TW);
            uint32_t x1 = static_cast<uint32_t>(static_cast<uint64_t>(tx + 1) * sw / TW);
            if (x1 <= x0) x1 = x0 + 1;
            uint32_t r = 0, g = 0, b = 0, a = 0, n = 0;
            for (uint32_t y = y0; y < y1 && y < sh; ++y)
                for (uint32_t x = x0; x < x1 && x < sw; ++x) {
                    const uint8_t* p = &capture_rgba_[(static_cast<size_t>(y) * sw + x) * 4];
                    r += p[0]; g += p[1]; b += p[2]; a += p[3]; ++n;
                }
            uint8_t* d = &tb[(static_cast<size_t>(ty) * TW + tx) * 4];
            d[0] = static_cast<uint8_t>(r / n); d[1] = static_cast<uint8_t>(g / n);
            d[2] = static_cast<uint8_t>(b / n); d[3] = static_cast<uint8_t>(a / n);
        }
    }

    ReelEntry e{};
    e.seq = reel_seq_;
    {
        std::time_t now = std::time(nullptr);
        std::tm tmv{}; localtime_s(&tmv, &now);
        char wb[32]; std::strftime(wb, sizeof(wb), "%Y-%m-%d %H:%M:%S", &tmv);
        e.wall = wb;
    }
    e.show_t = show_time_.load(std::memory_order_relaxed);
    e.cam_r = g_cam.radius; e.cam_theta = g_cam.theta; e.cam_phi = g_cam.phi;
    e.light[0] = frost_light_x_.load(); e.light[1] = frost_light_y_.load(); e.light[2] = frost_light_z_.load();
    float per = show_period();
    uint32_t nj = show_joint_count();
    if (joints_loaded_ && nj) {
        uint32_t cur = static_cast<uint32_t>(e.show_t / per) % nj;
        e.joint = show_joint_name(cur);
        e.theta = show_current_theta();
    }

    char l1[96], l2[96], l3[128];
    if (!e.joint.empty()) snprintf(l1, sizeof(l1), "t%.2f %s", e.show_t, e.joint.c_str());
    else                  snprintf(l1, sizeof(l1), "t%.2f (no show)", e.show_t);
    snprintf(l2, sizeof(l2), "%+.1fd  %s", e.theta, e.wall.c_str() + 11);
    snprintf(l3, sizeof(l3), "r%.1f %.2f/%.2f  L%.2f/%.2f/%.2f",
             e.cam_r, e.cam_theta, e.cam_phi, e.light[0], e.light[1], e.light[2]);
    ui_.reel_push(tb.data(), l1, l2, l3);

    {
        std::lock_guard<std::mutex> lk(reel_mutex_);
        reel_entries_.push_back(e);
        while (reel_entries_.size() > static_cast<size_t>(StudioUI::REEL_MAX))
            reel_entries_.erase(reel_entries_.begin());
    }
    ++reel_seq_;
}

std::string Engine::reel_json() const {
    std::lock_guard<std::mutex> lk(reel_mutex_);
    std::string s = "{\"count\":" + std::to_string(reel_entries_.size())
                  + ",\"cap\":" + std::to_string(StudioUI::REEL_MAX)
                  + ",\"grabs_total\":" + std::to_string(reel_seq_) + ",\"entries\":[";
    for (size_t i = reel_entries_.size(); i-- > 0;) {   // newest first
        const ReelEntry& e = reel_entries_[i];
        char eb[512];
        snprintf(eb, sizeof(eb),
            "{\"seq\":%llu,\"wall\":\"%s\",\"show_t\":%.6f,\"joint\":\"%s\",\"theta\":%.4f,"
            "\"cam\":[%.4f,%.4f,%.4f],\"light\":[%.3f,%.3f,%.3f]}",
            static_cast<unsigned long long>(e.seq), e.wall.c_str(), e.show_t, e.joint.c_str(),
            e.theta, e.cam_r, e.cam_theta, e.cam_phi, e.light[0], e.light[1], e.light[2]);
        s += eb;
        if (i) s += ",";
    }
    s += "]}";
    return s;
}

// D2: the timeline marker feed is derived from the same live sources as the
// panels' other twins. Kind 1 is a joint sweep-window start, kind 3 is its
// end, and kind 2 is a recorded reel capture. No marker owns time or pose state.
void Engine::push_timeline_markers() {
    std::vector<StudioUI::TimelineMarker> markers;
    if (joints_loaded_ && j_sweep_period_ > 0.f) {
        markers.reserve(static_cast<size_t>(j_n_joints_) * 2);
        for (uint32_t i = 0; i < j_n_joints_; ++i) {
            const double t0 = static_cast<double>(i) * j_sweep_period_;
            const double t1 = static_cast<double>(i + 1) * j_sweep_period_;
            markers.push_back({t0, show_joint_name(i) + " start", 1});
            markers.push_back({t1, show_joint_name(i) + " end", 3});
        }
    }
    {
        std::lock_guard<std::mutex> lk(reel_mutex_);
        markers.reserve(markers.size() + reel_entries_.size());
        for (const auto& e : reel_entries_)
            markers.push_back({e.show_t, e.joint.empty() ? "capture" : e.joint, 2});
    }
    ui_.set_timeline_markers(std::move(markers));
}

// E2a: enqueue a deep link and wait only for its render-thread commit. The
// caller is the HTTP worker; the render thread owns every StudioUI mutation.
bool Engine::request_ui_link(int stage, int& line, int& doc) {
    // Serialize the single-slot request so concurrent HTTP callers cannot
    // replace the stage while another caller waits for its acknowledgment.
    std::lock_guard<std::mutex> submit_lk(link_request_submit_m_);
    {
        std::lock_guard<std::mutex> lk(link_request_m_);
        link_request_done_ = false;
        link_request_ok_ = false;
        link_request_line_ = -1;
        link_request_doc_ = 0;
    }
    link_request_stage_.store(stage, std::memory_order_relaxed);
    link_request_pending_.store(true, std::memory_order_release);
    std::unique_lock<std::mutex> lk(link_request_m_);
    const bool signaled = link_request_cv_.wait_for(lk, std::chrono::seconds(3),
        [this] { return link_request_done_; });
    if (!signaled) {
        line = -1;
        doc = -1;
        return false;
    }
    line = link_request_line_;
    doc = link_request_doc_;
    return link_request_ok_;
}

// F1a: the HTTP console membrane. The request is serialized because the render
// thread has one StudioUI owner and acknowledgments must belong to one caller.
bool Engine::request_console_ui(const std::string& line, bool has_line,
                                bool open, bool has_open, bool& open_result) {
    std::lock_guard<std::mutex> submit_lk(console_ui_submit_m_);
    {
        std::lock_guard<std::mutex> lk(console_ui_m_);
        if (console_ui_stop_) {
            open_result = false;
            return false;
        }
        console_ui_done_ = false;
        console_ui_cancelled_ = false;
        console_ui_ok_ = false;
        console_ui_has_line_ = has_line;
        console_ui_has_open_ = has_open;
        console_ui_open_ = open;
        console_ui_line_ = line;
    }
    console_ui_pending_ = true;
    std::unique_lock<std::mutex> lk(console_ui_m_);
    const bool signaled = console_ui_cv_.wait_for(lk, std::chrono::seconds(3),
        [this] { return console_ui_done_ || console_ui_stop_; });
    if (!signaled || console_ui_stop_) {
        if (!signaled) console_ui_cancelled_ = true;
        open_result = false;
        return false;
    }
    open_result = console_ui_open_;
    return console_ui_ok_;
}

void Engine::consume_console_ui_request() {
    if (!console_ui_pending_.exchange(false)) return;
    // Hold the request lock through application and acknowledgment. This closes
    // the timeout race where a caller could cancel after the render thread had
    // copied the payload but before it mutated StudioUI.
    std::unique_lock<std::mutex> lk(console_ui_m_);
    if (console_ui_cancelled_) {
        console_ui_done_ = true;
        console_ui_ok_ = false;
        lk.unlock();
        console_ui_cv_.notify_one();
        return;
    }
    const bool has_line = console_ui_has_line_;
    const bool has_open = console_ui_has_open_;
    const bool open = console_ui_open_;
    const std::string line = console_ui_line_;
    if (has_open) ui_.set_console_open(open);
    if (has_line) ui_.console_submit_line(line);
    console_ui_open_ = ui_.console_is_open();
    console_ui_ok_ = true;
    console_ui_done_ = true;
    lk.unlock();
    console_ui_cv_.notify_one();
}

// E1a: queue docs navigation and wait for the render-thread commit. The same
// request lock covers cancellation and application, so a timeout cannot land
// stale document state on a later frame.
bool Engine::request_ui_doc(int doc, bool has_doc, float scroll, bool has_scroll,
                            int& doc_result, float& scroll_result) {
    std::lock_guard<std::mutex> submit_lk(doc_request_submit_m_);
    {
        std::lock_guard<std::mutex> lk(doc_request_m_);
        if (doc_request_stop_) {
            doc_result = -1;
            scroll_result = 0.f;
            return false;
        }
        doc_request_done_ = false;
        doc_request_cancelled_ = false;
        doc_request_ok_ = false;
        doc_request_has_doc_ = has_doc;
        doc_request_has_scroll_ = has_scroll;
        doc_request_doc_ = doc;
        doc_request_scroll_ = scroll;
    }
    doc_request_pending_.store(true, std::memory_order_release);
    std::unique_lock<std::mutex> lk(doc_request_m_);
    const bool signaled = doc_request_cv_.wait_for(lk, std::chrono::seconds(3),
        [this] { return doc_request_done_ || doc_request_stop_; });
    if (!signaled || doc_request_stop_) {
        if (!signaled) doc_request_cancelled_ = true;
        doc_result = -1;
        scroll_result = 0.f;
        return false;
    }
    doc_result = doc_request_doc_result_;
    scroll_result = doc_request_scroll_result_;
    return doc_request_ok_;
}

void Engine::consume_doc_request() {
    if (!doc_request_pending_.exchange(false)) return;
    std::unique_lock<std::mutex> lk(doc_request_m_);
    if (doc_request_cancelled_) {
        doc_request_done_ = true;
        doc_request_ok_ = false;
        lk.unlock();
        doc_request_cv_.notify_one();
        return;
    }
    const bool has_doc = doc_request_has_doc_;
    const bool has_scroll = doc_request_has_scroll_;
    const int doc = doc_request_doc_;
    const float scroll = doc_request_scroll_;
    if (has_doc) ui_.docs_set(doc);
    if (has_scroll) ui_.docs_set_scroll(scroll);
    doc_request_doc_result_ = ui_.docs_current();
    doc_request_scroll_result_ = ui_.docs_scroll();
    doc_request_ok_ = true;
    doc_request_done_ = true;
    lk.unlock();
    doc_request_cv_.notify_one();
}

// ── Frame submission ─────────────────────────────────────────────────────────────────────

bool Engine::frame() {
    // B1: consume a pending window resize BEFORE anything else — the swapchain must
    // track the window or every acquire/present goes OUT_OF_DATE from here on.
    {
        uint32_t prw = g_pending_resize_w.exchange(0);
        uint32_t prh = g_pending_resize_h.exchange(0);
        if (prw != 0 && prh != 0) resize(prw, prh);
    }
    if (n_ == 0 && !has_mesh_) {
        // THE STUDIO: with nothing loaded the 3D paths all idle — but the board
        // is exactly what an incoming agent needs to see, so the overlay still
        // presents (clear + UI pass only).
        // E1: hidden + idle never reaches prepare() — run the panels' polls
        // anyway or the HTTP twins (board, docs) freeze with the overlay.
        ui_.idle_poll();
        // F2/F3: the chrome presents hidden+idle too — "always visible" means
        // the clear + bar frame still renders when the overlay is closed.
        if ((ui_.visible || ui_.wants_chrome()) && ui_.ok()) return frame_idle_ui();
        return true;
    }
    // D1: push the show clock's view to the timeline panel (the UI never owns time)
    // THE TRANSPORT DRIVES THE LIVE CLOCK: the push names the SOURCE so the
    // panel serves whichever clock is loaded (joints show / hinge march).
    {
        double t = show_time_.load(std::memory_order_relaxed);
        float per = show_period();
        uint32_t nj = show_joint_count();
        uint32_t cur = nj ? static_cast<uint32_t>(t / per) % nj : 0;
        bool hinge_now = hinge_active_ && nj == 0;
        std::string src = nj ? "joints" : (hinge_now ? "hinge" : "none");
        ui_.set_show_clock(t, nj ? nj * static_cast<double>(per) : (hinge_now ? hinge_period_ : 0.0),
                           show_playing_.load(), show_speed_.load(), nj, cur, per,
                           nj ? show_joint_name(cur) : std::string(hinge_now ? "knees (hinge march)" : "none"),
                           show_current_theta(), src, hinge_now ? hinge_period_ : 0.f);
                           ui_.set_key_marks(key_marks_list(), src);   // D1: the timeline's key diamonds
                           // D7: push joint-aware key marks for the dope sheet
                           { auto li = key_marks_list_info();
                             std::vector<StudioUI::DopeKey> dk;
                             dk.reserve(li.size());
                             for (auto& i : li) dk.push_back({i.name, i.t, i.joint});                              ui_.set_dope_keys(std::move(dk)); }
                            push_timeline_markers();

    }
    push_hud_state();   // F3: the gait/water rows, from the engine's own state
    console_drain();    // F1: finished console responses land in the scrollback
    consume_console_ui_request(); // F1a: HTTP presentation requests land here
    consume_doc_request();         // E1a: HTTP docs requests land here
    // B3: consume a queued synthetic click (agents drive the panels over HTTP —
    // input lands on the render thread, same discipline as the WndProc's)
    // D4a: HTTP compare requests are consumed on the render thread, before
    // prepare() publishes the current glass. GET /compare therefore reads a
    // committed selection, never a half-applied network intent.
    if (compare_request_pending_.exchange(false)) {
        ui_.apply_compare_request(compare_request_slot_.load(),
                                  compare_request_clear_.load());
    }
    // E2a: resolve the HTTP deep link on the render thread before prepare()
    // publishes the glass; the HTTP worker only receives the committed result.
    if (link_request_pending_.exchange(false)) {
        const int stage = link_request_stage_.load(std::memory_order_relaxed);
        const int line = ui_.docs_link_line(stage);
        const bool ok = line >= 0;
        if (ok) ui_.docs_link_stage(stage);
        {
            std::lock_guard<std::mutex> lk(link_request_m_);
            link_request_ok_ = ok;
            link_request_line_ = ok ? line : -1;
            link_request_doc_ = ui_.docs_current();
            link_request_done_ = true;
        }
        link_request_cv_.notify_one();
    }
    if (ui_click_pending_.exchange(false)) {
        ui_.on_lbutton(ui_click_x_.load(), ui_click_y_.load(), true);
        ui_.on_lbutton(0, 0, false);
    }
    // C1: push the joints editor's view (the UI draws; the engine owns). The
    // gizmo aims through last frame's stashed VP — one frame of latency at
    // the frame cap is invisible, and the alternative is re-deriving the VP.
    if (joints_loaded_) {
        const float* st = static_cast<const float*>(j_state_map_);
        joint_view_scratch_.resize(j_n_joints_);
        for (uint32_t k = 0; k < j_n_joints_; ++k) {
            joint_view_scratch_[k].name  = j_names_[k];
            joint_view_scratch_[k].ext   = j_rom_[k * 2 + 0];
            joint_view_scratch_[k].flex  = j_rom_[k * 2 + 1];
            joint_view_scratch_[k].theta = st ? st[k * 8 + 7] * 57.29577951308232f : 0.0f;
        }
        ui_.set_joints_view(joint_view_scratch_, joints_owner_.load(std::memory_order_relaxed),
                            selected_joint_.load(std::memory_order_relaxed));
        int sel = selected_joint_.load(std::memory_order_relaxed);
        bool drawn = false;
        if (sel >= 0 && sel < static_cast<int>(j_n_joints_) && st && last_vp_valid_) {
            float J[3] = { st[sel * 8 + 0], st[sel * 8 + 1], st[sel * 8 + 2] };
            float L = (sel < static_cast<int>(j_gizmo_len_.size())) ? j_gizmo_len_[sel] : 0.5f;
            float T[3] = { J[0] + st[sel * 8 + 3] * L, J[1] + st[sel * 8 + 4] * L,
                           J[2] + st[sel * 8 + 5] * L };
            float x0, y0, x1, y1;
            if (project_world(J, x0, y0) && project_world(T, x1, y1)) {
                ui_.set_gizmo(true, x0, y0, x1, y1, j_names_[sel].c_str());
                drawn = true;
            }
        }
        if (!drawn) ui_.set_gizmo(false, 0, 0, 0, 0, "");
    } else {
        joint_view_scratch_.clear();
        ui_.set_joints_view(joint_view_scratch_, 0, -1);
        ui_.set_gizmo(false, 0, 0, 0, 0, "");
    }
    // C4: the outliner's view — composed from live state, one formatting site
    {
        auto rows = scene_rows();
        int ir = inspect_row_.load();
        if (ir >= 0 && ir < static_cast<int>(rows.size())) {
            const auto& r = rows[ir];
            std::string hint = r.toggleable
                ? "toggle: " + scene_command(r.id, r.state == 0)
                : "read-only atom (status row)";
            ui_.set_inspect_view(ir, r.id, r.label, inspect_kv(ir), hint);
        } else {
            ui_.set_inspect_view(-1, "", "", {}, "");
        }
        ui_.set_scene_view(std::move(rows));
    }
    // D6: the bookmark chips — the store's own names, every frame
    ui_.set_cam_view(cam_mark_names());
    // D5: the capture session document — one formatting site
    ui_.set_capture_view(capture_kv());
    ui_.prepare(extent_.width, extent_.height);   // build the draw list (cheap no-op when hidden)

    // ── THE STUDIO CLOCK (D1): consume a pending scrub, then advance if playing.
    // The joints SHOW below poses from show_time_ — pause freezes the pose,
    // scrub lands an exact pose, frame-step is exactly 1/240 s.
    {
        double scrub = show_scrub_.exchange(-1.0, std::memory_order_relaxed);
        if (scrub >= 0.0) show_time_.store(scrub, std::memory_order_relaxed);
        if (show_time_.load(std::memory_order_relaxed) < 0.0)
            show_time_.store(0.0, std::memory_order_relaxed);   // the clock has no negative time
        auto now = std::chrono::steady_clock::now();
        if (show_last_.time_since_epoch().count() != 0 && show_playing_.load(std::memory_order_relaxed)) {
            show_time_.store(show_time_.load(std::memory_order_relaxed)
                + std::chrono::duration<double>(now - show_last_).count()
                * show_speed_.load(std::memory_order_relaxed), std::memory_order_relaxed);
        }
        show_last_ = now;
    }
    // Offscreen: render to rt_framebuffer_ and capture from rt_image_. No swapchain acquire, so
    // the /frame endpoint works even when the window is minimized (or entirely headless).
    // Frames-in-flight: slot cycles 0..1 — the CPU records this frame while the GPU
    // may still be drawing the previous slot. Per-slot fence/cmdbuf/descriptors/UBO.
    uint32_t img_idx = image_idx_;
    VkResult fence_res = vkWaitForFences(device_, 1, &fences_[img_idx], VK_TRUE, UINT64_MAX);
    if (fence_res == VK_ERROR_DEVICE_LOST) {
        fprintf(stderr, "FATAL: VK_ERROR_DEVICE_LOST at frame fence wait (slot %u)\n", img_idx);
        fflush(stderr);
        exit(2);
    }
    // NOTE: the fence is NOT reset here — an early return (OUT_OF_DATE) would leave
    // it reset-but-never-submitted and the next wait on this slot would hang.
    // Reset happens at the submit site, immediately before vkQueueSubmit.
    // THE STRAIN OVERLAY: the CPU computes true area strain from the SAME
    // analytic FK law (works for both the CPU fallback and the GPU kernel),
    // then the kernel tints when the overlay flag is set. One call, both paths.
    compute_strain();

    // CPU hinge fallback (only when the GPU kernel didn't build); the GPU path
    // is recorded into the command buffer below.
    if (hinge_active_ && hinge_pipe_ == VK_NULL_HANDLE && tri_vmap_ != nullptr) pose_hinge();

    // Upload uniform buffer (camera matrices + resolution)
    float proj[16], view[16];
    update_camera_matrices(proj, view);
    push_grid_overlay();
    push_rig_overlay();          // the viewport's frame of reference (see its note)

    // Depth sort is done on the GPU (radix sort, recorded in the command buffer below). Stash the
    // view matrix's z-row, which the depth-key pass needs as push constants.
    float depth_zx = view[2], depth_zy = view[6], depth_zz = view[10], depth_tz = view[14];

    struct alignas(16) Uniforms {
        float proj[16];
        float view[16];
        float resolution[2];
        float floor_y;      // the grid plane (the shadow projects onto it)
        float shadow_alpha; // contact shadow opacity (0 = off)
        float shadow_h0;    // THE penumbra's reference height (derived at load:
                            // alpha halves at half the mesh's y-extent)
        float light_pad[3]; // std140: the vec4 must START on a 16-byte boundary
                            // (offset 160). After shadow_h0 (ends 148) the pad
                            // fills 148..159 — the pad goes BEFORE the vector,
                            // not after: a trailing pad leaves light_dir at 148
                            // while the shader reads 160 (measured: L=(0,0,0),
                            // NaN key, ambient-only body, dead shadow).
        float light_dir[3]; // THE LIGHT (Studio-owned, /light steers it): one
                            // vector for the lit flank AND the shadow — they
                            // cannot disagree, so they cannot drift. Consumed
                            // by VERTEX stages only; fragments get it via
                            // varying (frag-side UBO reads are untrustworthy).
        float light_tail;   // 172..175: block size lands at 176 = GLSL's
    } ubo{};
    static_assert(sizeof(ubo) == 176,
        "UBO layout drifted from the shaders' std140 block (176 B) — "
        "light/matrix reads land on the wrong bytes (the 2026-09-03 alignment trap)");
    std::memcpy(ubo.proj, proj, sizeof(proj));
    std::memcpy(ubo.view, view, sizeof(view));
    ubo.resolution[0] = static_cast<float>(extent_.width);
    ubo.resolution[1] = static_cast<float>(extent_.height);
    ubo.floor_y = 0.0f;   // THE grid plane: push_grid_overlay draws the floor at y=0
    ubo.shadow_alpha = 0.38f;
    ubo.shadow_h0 = fmaxf(g_mesh_ymax - g_mesh_ymin, 1e-3f);
    {
        const float* L = ui_.light_dir();   // already unit-length (Studio normalizes)
        ubo.light_dir[0] = L[0]; ubo.light_dir[1] = L[1]; ubo.light_dir[2] = L[2];
    }

    // Per-slot camera UBO, host-visible + persistently mapped: create once, memcpy
    // per frame. NO staging buffer, NO queue submit, NO vkQueueWaitIdle per frame —
    // that was the frame-time killer (each end_single_time_cmd drained the pipe).
    if (params_ubo_[img_idx] == VK_NULL_HANDLE) {
        VkBufferCreateInfo bci{};
        bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size        = sizeof(Uniforms);
        bci.usage       = VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &params_ubo_[img_idx]);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, params_ubo_[img_idx], &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType       = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &params_umem_[img_idx]);
        vkBindBufferMemory(device_, params_ubo_[img_idx], params_umem_[img_idx], 0);
        vkMapMemory(device_, params_umem_[img_idx], 0, sizeof(Uniforms), 0, &params_umap_[img_idx]);
    }
    std::memcpy(params_umap_[img_idx], &ubo, sizeof(Uniforms));

    // Update uniform descriptor
    VkDescriptorBufferInfo ubo_info{};
    ubo_info.buffer = params_ubo_[img_idx];
    ubo_info.offset = 0;
    ubo_info.range  = VK_WHOLE_SIZE;
    VkWriteDescriptorSet uw[1] = {};
    uw[0].sType            = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    uw[0].dstSet           = desc_sets_[img_idx];
    uw[0].dstBinding       = 0;
    uw[0].dstArrayElement  = 0;
    uw[0].descriptorCount  = 1;
    uw[0].descriptorType   = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    uw[0].pBufferInfo      = &ubo_info;
    vkUpdateDescriptorSets(device_, 1, uw, 0, nullptr);

    // Acquire a swapchain image so the WINDOW can show the render. The offscreen target is always
    // drawn (so /frame works headless/minimized); this blits it to the screen. A minimized window
    // makes acquire time out / go out-of-date — not fatal: skip the present, the capture still works.
    uint32_t sc_idx = 0;
    VkResult acquire_res = vkAcquireNextImageKHR(device_, swapchain_, 100000000ULL,  // 100 ms
                                                 draw_sem_[img_idx], VK_NULL_HANDLE, &sc_idx);
    // B1: OUT_OF_DATE means the swapchain is dead (resize, occlusion, driver). Rebuild it
    // NOW instead of skipping presents forever — the old code left the window frozen
    // at the last presented image while the loop ran at full FPS.
    if (acquire_res == VK_ERROR_DEVICE_LOST) {
        fprintf(stderr, "FATAL: VK_ERROR_DEVICE_LOST at swapchain acquire\n");
        fflush(stderr);
        exit(2);
    }
    if (acquire_res == VK_ERROR_OUT_OF_DATE_KHR) {
        VkSurfaceCapabilitiesKHR caps{};
        vkGetPhysicalDeviceSurfaceCapabilitiesKHR(phys_dev_, surface_, &caps);
        if (caps.currentExtent.width != 0 && caps.currentExtent.height != 0) {
            resize(caps.currentExtent.width, caps.currentExtent.height);
            return true;  // next frame presents on the fresh swapchain
        }
        // 0x0 surface = MINIMIZED: fall through with can_present=false. The
        // offscreen target renders + captures without the swapchain — that is
        // the headless law this block's comment promises. The old early
        // return made it a lie: minimized, frame() never reached the capture
        // block and every /frame and /capture timed out (caught by the D5
        // probe while the operator had the window minimized mid-game).
        headless_minimized_.store(true);
    } else if (acquire_res == VK_SUCCESS || acquire_res == VK_SUBOPTIMAL_KHR) {
        headless_minimized_.store(false);
    }
    bool can_present = (acquire_res == VK_SUCCESS || acquire_res == VK_SUBOPTIMAL_KHR);
    bool recreate_after_frame = (acquire_res == VK_SUBOPTIMAL_KHR);

    // Record command buffer
    VkCommandBufferBeginInfo bbi{};
    bbi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    vkResetCommandBuffer(cmd_bufs_[img_idx], 0);
    vkBeginCommandBuffer(cmd_bufs_[img_idx], &bbi);

    // GPU hinge kernel — the first CA-field pass: per-vertex weight SSBO + engine
    // clock -> posed vertices, before the render pass reads the vertex buffer.

    // ── THE GAIT CLOCK (H7 stage 2) — RK4 steps on the engine's own clock,
    // recorded into THIS frame's command buffer (the water clock's pattern).
    // The kernel's theta mirror feeds the hinge pose below; the phase ring is
    // the /gait_state verification endpoint (B15-style bit-exactness gate).
    if (gait_on_.load(std::memory_order_relaxed) && gait_loaded_) {
        uint32_t nsteps = gait_steps_per_frame_.load(std::memory_order_relaxed);
        double om = gait_omega_.load(std::memory_order_relaxed);
        for (uint32_t s = 0; s < nsteps; ++s) {
            struct GaitPC { double omega; uint32_t rec_index, pad; } gpc{};
            gpc.omega = om;
            gpc.rec_index = static_cast<uint32_t>(gait_steps_total_.load(std::memory_order_relaxed)
                                                  % gait_ring_cap_);
            vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, gait_pipe_);
            vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, gait_layout_,
                                    0, 1, &gait_desc_set_, 0, nullptr);
            vkCmdPushConstants(cmd_bufs_[img_idx], gait_layout_, VK_SHADER_STAGE_COMPUTE_BIT,
                               0, sizeof(gpc), &gpc);
            vkCmdDispatch(cmd_bufs_[img_idx], 1, 1, 1);
            VkMemoryBarrier gmb{};
            gmb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            gmb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
            gmb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT;
            vkCmdPipelineBarrier(cmd_bufs_[img_idx],
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                0, 1, &gmb, 0, nullptr, 0, nullptr);
            gait_steps_total_.fetch_add(1, std::memory_order_relaxed);
        }
    }

    // H15/C1: the joints kernel dispatches whenever EITHER pose owner is live —
    // the SHOW (joints_on_, the D1 studio clock sweeps the ROMs) or the EDITOR
    // (joints_owner_ == 1, thetas persist where intents put them). One owner
    // at a time, observable in GET /joints; the show never overwrites an edit.
    const bool edit_mode = joints_owner_.load(std::memory_order_relaxed) == 1;
    if ((joints_on_.load(std::memory_order_relaxed) || edit_mode) &&
        joints_loaded_ && joints_pipe_ != VK_NULL_HANDLE) {
        float* st = static_cast<float*>(j_state_map_);
        if (edit_mode) {
            // C1: THE EDITOR owns the pose. Consume a pending intent (clamped
            // to the pack's derived ROM — the slider's hard range is the law);
            // every other theta stays exactly where the last intent left it.
            if (edit_pending_.exchange(false, std::memory_order_relaxed)) {
                int idx = edit_joint_.load(std::memory_order_relaxed);
                float deg = edit_theta_deg_.load(std::memory_order_relaxed);
                if (idx >= 0 && idx < static_cast<int>(j_n_joints_)) {
                    float lo = j_rom_[idx * 2 + 0], hi = j_rom_[idx * 2 + 1];
                    if (lo > hi) { float tmp = lo; lo = hi; hi = tmp; }
                    float cl = deg < lo ? lo : (deg > hi ? hi : deg);
                    st[idx * 8 + 7] = cl * 0.01745329251f;
                    edit_applied_deg_.store(cl, std::memory_order_relaxed);
                }
            }
        } else {
            // H15: THE SHOW — sweep every joint through its derived ROM, one at
            // a time, on THE STUDIO CLOCK (D1: a parameter — play/pause/scrub/
            // step). 4 s per joint: 0 -> flex (1.5 s), back (0.5 s), -> ext
            // (1.5 s), back (0.5 s). Cosine ramps.
            float t = static_cast<float>(show_time_.load(std::memory_order_relaxed));
            float per = j_sweep_period_;
            uint32_t cur = static_cast<uint32_t>(t / per) % j_n_joints_;
            float ph = fmodf(t, per);
            auto ramp = [](float x) { x = x < 0 ? 0 : (x > 1 ? 1 : x); return 0.5f - 0.5f * cosf(3.14159265f * x); };
            float flex = j_rom_[cur * 2 + 1] * 0.01745329251f;
            float ext  = j_rom_[cur * 2 + 0] * 0.01745329251f;
            float th;
            if      (ph < 1.5f) th = flex * ramp(ph / 1.5f);
            else if (ph < 2.0f) th = flex * (1.0f - ramp((ph - 1.5f) / 0.5f));
            else if (ph < 3.5f) th = ext  * ramp((ph - 2.0f) / 1.5f);
            else                th = ext  * (1.0f - ramp((ph - 3.5f) / 0.5f));
            for (uint32_t k = 0; k < j_n_joints_; ++k) st[k * 8 + 7] = 0.0f;
            st[cur * 8 + 7] = th;
        }

        struct JointsPC { uint32_t n, nj; int32_t paint; uint32_t pad; }
            jpc{ j_n_verts_, j_n_joints_, selected_joint_.load(std::memory_order_relaxed), 0 };
        if (joints_desc_dirty_) joints_rebind();   // rest/Out recreated -> rebind BEFORE dispatch
        vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, joints_pipe_);
        vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, joints_layout_,
                                0, 1, &joints_desc_set_, 0, nullptr);
        vkCmdPushConstants(cmd_bufs_[img_idx], joints_layout_, VK_SHADER_STAGE_COMPUTE_BIT,
                           0, sizeof(jpc), &jpc);
        vkCmdDispatch(cmd_bufs_[img_idx], (j_n_verts_ + 255) / 256, 1, 1);
        VkMemoryBarrier jmb{};
        jmb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        jmb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        jmb.dstAccessMask = VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,
            0, 1, &jmb, 0, nullptr, 0, nullptr);
    } else if (hinge_active_ && hinge_pipe_ != VK_NULL_HANDLE) {
        if (hinge_desc_dirty_) hinge_rebind();   // tri_vbuf_ recreated -> rebind BEFORE dispatch
        struct HingePC { float JL[4], JR[4], axis[4]; float romL, romR, period, phaseR, time;
                         float thetaL, thetaR; uint32_t flags; uint32_t n; } hpc{};
        hpc.JL[0] = hinge_JL_[0]; hpc.JL[1] = hinge_JL_[1]; hpc.JL[2] = hinge_JL_[2];
        hpc.JR[0] = hinge_JR_[0]; hpc.JR[1] = hinge_JR_[1]; hpc.JR[2] = hinge_JR_[2];
        hpc.axis[0] = hinge_axis_[0]; hpc.axis[1] = hinge_axis_[1]; hpc.axis[2] = hinge_axis_[2];
        hpc.romL = hinge_romL_; hpc.romR = hinge_romR_;
        hpc.period = hinge_period_; hpc.phaseR = hinge_phaseR_;
        hpc.time = hinge_time();   // the transport drives the live clock (D1, 2026-09-02)
        bool gait_drives = gait_on_.load(std::memory_order_relaxed) && gait_loaded_;
        if (gait_drives) {
            double tL, tR; gait_theta(tL, tR);
            hpc.thetaL = static_cast<float>(tL); hpc.thetaR = static_cast<float>(tR);
        }
        hpc.flags = gait_drives ? 1u : 0u;
        if (strain_on_.load(std::memory_order_relaxed)) hpc.flags |= 2u;   // bit1: strain tint
        hpc.n = static_cast<uint32_t>(hinge_wL_.size());
        // H13: the manual verification override applies to BOTH pose laws —
        // hinge.comp's theta-mode (flags bit0) IS the blend law at a fixed
        // angle, so the operator/dyad can compare volp vs blend at the same
        // commanded theta.
        if (volp_manual_.load(std::memory_order_relaxed)) {
            hpc.thetaL = volp_thL_.load(std::memory_order_relaxed);
            hpc.thetaR = volp_thR_.load(std::memory_order_relaxed);
            hpc.flags |= 1u;
        }
        bool volp = volp_loaded_ && volp_pipe_ != VK_NULL_HANDLE
                    && volp_mode_.load(std::memory_order_relaxed) == 1;
        if (volp) {
            // H13: the volp-ARAP kernel replaces the blend dispatch (same theta
            // source; blend stays behind the flag). One workgroup, M fixed.
            struct VolpPC { float thetaL, thetaR; uint32_t flags, M; } vpc{};
            float thL_deg, thR_deg;
            if (volp_manual_.load(std::memory_order_relaxed)) {
                thL_deg = volp_thL_.load(std::memory_order_relaxed);
                thR_deg = volp_thR_.load(std::memory_order_relaxed);
            } else if (gait_drives) {
                thL_deg = hpc.thetaL; thR_deg = hpc.thetaR;
            } else {
                const float two_pi = 6.28318530718f;
                float ph = fmodf(hpc.time, hinge_period_) / hinge_period_;
                thL_deg = (0.5f - 0.5f * cosf(two_pi * ph)) * hinge_romL_;
                thR_deg = (0.5f - 0.5f * cosf(two_pi * ph + hinge_phaseR_)) * hinge_romR_;
            }
            uint32_t vflags = 0;
            float dL = fabsf(thL_deg - volp_last_thL_), dR = fabsf(thR_deg - volp_last_thR_);
            // 2.5 deg: outside the tracking derivation's domain (2 deg/frame,
            // volp_track.json) -> cold-start from the theta-exact blend pose.
            if (volp_cold_.exchange(false) || dL > 2.5f || dR > 2.5f) vflags |= 1u;
            volp_last_thL_ = thL_deg; volp_last_thR_ = thR_deg;
            vpc.thetaL = thL_deg; vpc.thetaR = thR_deg;
            vpc.flags = vflags;
            vpc.M = volp_M_.load(std::memory_order_relaxed);
            vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, volp_pipe_);
            vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, volp_layout_,
                                    0, 1, &volp_desc_set_, 0, nullptr);
            vkCmdPushConstants(cmd_bufs_[img_idx], volp_layout_, VK_SHADER_STAGE_COMPUTE_BIT,
                               0, sizeof(vpc), &vpc);
            vkCmdDispatch(cmd_bufs_[img_idx], 1, 1, 1);
            VkMemoryBarrier vmb{};
            vmb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            vmb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
            vmb.dstAccessMask = VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT;
            vkCmdPipelineBarrier(cmd_bufs_[img_idx],
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,
                0, 1, &vmb, 0, nullptr, 0, nullptr);
        } else {
        vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, hinge_pipe_);
        vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, hinge_layout_,
                                0, 1, &hinge_desc_set_, 0, nullptr);
        vkCmdPushConstants(cmd_bufs_[img_idx], hinge_layout_, VK_SHADER_STAGE_COMPUTE_BIT,
                           0, sizeof(hpc), &hpc);
        vkCmdDispatch(cmd_bufs_[img_idx], (hpc.n + 255) / 256, 1, 1);
        VkMemoryBarrier hmb{};
        hmb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        hmb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        hmb.dstAccessMask = VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,
            0, 1, &hmb, 0, nullptr, 0, nullptr);
        }
    }

    // ── FROST decode (H9) — relight the mesh from the CURRENT camera view
    // direction + the configured light: after the pose, before the render pass.
    bool frost_active = frost_loaded_ && has_mesh_ && f_n_tris_ > 0
                        && f_n_tris_ == tri_idx_count_ / 3
                        && frost_pipe_ != VK_NULL_HANDLE;
    bool frost_want = frost_on_.load(std::memory_order_relaxed)
                      || frost_dbg_arm_.load(std::memory_order_relaxed);
    if (frost_active && frost_want) {
        if (frost_desc_dirty_) frost_rebind();
        // hinge pose (or any prior compute write) -> kernel SSBO read
        VkMemoryBarrier fmb{};
        fmb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        fmb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        fmb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            0, 1, &fmb, 0, nullptr, 0, nullptr);
        // view dir = toward the camera (e42's view_to_cam = eye - target).
        // The eye is the SAME vector update_camera_matrices computed for the UBO —
        // read from last_eye_, not recomputed here. It used to be a third copy of
        // the spherical expression, which is exactly how an eye that reads the
        // light drifts from the eye that renders the frame.
        double eye[3] = { (double)last_eye_[0], (double)last_eye_[1], (double)last_eye_[2] };
        double vd[3] = { eye[0] - (double)g_cam.target[0],
                         eye[1] - (double)g_cam.target[1],
                         eye[2] - (double)g_cam.target[2] };
        double ld[3] = { frost_light_x_.load(std::memory_order_relaxed),
                         frost_light_y_.load(std::memory_order_relaxed),
                         frost_light_z_.load(std::memory_order_relaxed) };
        struct FrostPC { int32_t vq[4]; int32_t lq[4]; } fpc{};   // ivec4+ivec4: no
        quantize_dir_q30(vd, fpc.vq);                            // std430 packing trap
        quantize_dir_q30(ld, fpc.lq);
        fpc.vq[3] = (int32_t)f_n_tris_;
        fpc.lq[3] = frost_dbg_arm_.load(std::memory_order_relaxed) ? 1 : 0;
        for (int k = 0; k < 3; ++k) {
            frost_vq_[k].store(fpc.vq[k], std::memory_order_relaxed);
            frost_lq_[k].store(fpc.lq[k], std::memory_order_relaxed);
        }
        vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, frost_pipe_);
        vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, frost_layout_,
                                0, 1, &frost_desc_set_, 0, nullptr);
        vkCmdPushConstants(cmd_bufs_[img_idx], frost_layout_, VK_SHADER_STAGE_COMPUTE_BIT,
                           0, sizeof(fpc), &fpc);
        vkCmdDispatch(cmd_bufs_[img_idx], (f_n_tris_ + 255) / 256, 1, 1);
        frost_frame_.fetch_add(1, std::memory_order_relaxed);
        if (fpc.lq[3]) {
            VkMemoryBarrier smb{};
            smb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            smb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
            smb.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
            vkCmdPipelineBarrier(cmd_bufs_[img_idx],
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                0, 1, &smb, 0, nullptr, 0, nullptr);
            VkBufferCopy cc{}; cc.size = (VkDeviceSize)f_n_tris_ * 3 * 4;
            vkCmdCopyBuffer(cmd_bufs_[img_idx], f_color_buf_, f_color_rb_, 1, &cc);
            VkBufferCopy dc{}; dc.size = (VkDeviceSize)f_n_tris_ * 14 * 4;
            vkCmdCopyBuffer(cmd_bufs_[img_idx], f_dbg_buf_, f_dbg_rb_, 1, &dc);
            VkMemoryBarrier tmb{};
            tmb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            tmb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
            tmb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
            vkCmdPipelineBarrier(cmd_bufs_[img_idx],
                VK_PIPELINE_STAGE_TRANSFER_BIT,
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT | VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
                0, 1, &tmb, 0, nullptr, 0, nullptr);
            frost_dbg_copy_recorded_ = true;
            frost_dbg_arm_.store(false, std::memory_order_relaxed);
        }
        // color SSBO write -> fragment shader read at the draw
        VkMemoryBarrier cmb{};
        cmb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        cmb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        cmb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
            0, 1, &cmb, 0, nullptr, 0, nullptr);
    }

    // ── THE WATER CLOCK (H4) — macro steps on the engine's own clock, recorded
    // into THIS frame's command buffer (no submit/fence/readback per step, no
    // HTTP). Constant source: a river's source doesn't stop. States slot 0
    // always holds the latest V so /water_state stays the verification endpoint;
    // w_states_n_ never advances here (no cap exhaustion).
    if (water_clock_on_.load(std::memory_order_relaxed) && water_loaded_) {
        uint32_t nsteps = water_clock_steps_per_frame_.load(std::memory_order_relaxed);
        double cdt = water_clock_dt_.load(std::memory_order_relaxed);
        int32_t it = water_clock_inj_target_.load(std::memory_order_relaxed);
        int32_t ic = water_clock_inj_count_.load(std::memory_order_relaxed);
        for (uint32_t s = 0; s < nsteps; ++s)
            water_record_macro_step(cmd_bufs_[img_idx], cdt, it, ic);
        water_clock_steps_total_.fetch_add(nsteps, std::memory_order_relaxed);
        // copy the latest V into states slot 0 (transfer after the compute writes)
        VkMemoryBarrier wmb{};
        wmb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        wmb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        wmb.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
            0, 1, &wmb, 0, nullptr, 0, nullptr);
        VkBufferCopy wbc{};
        wbc.size = static_cast<VkDeviceSize>(w_n_cells_) * sizeof(int32_t);
        vkCmdCopyBuffer(cmd_bufs_[img_idx], w_V_buf_, w_states_buf_, 1, &wbc);
        // transfer write -> shader read/write (next step / next frame reads V, not
        // the states buffer — but water_vis below reads V this same frame)
        VkMemoryBarrier wmb2{};
        wmb2.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        wmb2.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        wmb2.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            0, 1, &wmb2, 0, nullptr, 0, nullptr);
    }

    // ── W4 surface displacement — build the water vertex buffer from the POSED
    // mesh (runs after the hinge/clock compute, before the render pass reads it).
    if (water_vis_on_.load(std::memory_order_relaxed) && water_loaded_ && has_mesh_
        && w_vis_pipe_ != VK_NULL_HANDLE && w_vis_set_ != VK_NULL_HANDLE) {
        if (water_vis_desc_dirty_) water_vis_rebind();
        // zero indirect.vertexCount (instanceCount stays 1 from the init upload)
        vkCmdFillBuffer(cmd_bufs_[img_idx], w_vis_indirect_buf_, 0, 4, 0);
        VkMemoryBarrier fmb{};
        fmb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        fmb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        fmb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            0, 1, &fmb, 0, nullptr, 0, nullptr);
        struct { double Q; uint32_t n, tri_base, cap; float tint; } vpc{};
        vpc.Q = w_Q_; vpc.n = w_n_cells_;
        vpc.tri_base = water_vis_tri_base_.load(std::memory_order_relaxed);
        vpc.cap = w_vis_cap_verts_; vpc.tint = 0.0f;
        vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, w_vis_pipe_);
        vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, w_vis_layout_,
                                0, 1, &w_vis_set_, 0, nullptr);
        vkCmdPushConstants(cmd_bufs_[img_idx], w_vis_layout_, VK_SHADER_STAGE_COMPUTE_BIT,
                           0, sizeof(vpc), &vpc);
        vkCmdDispatch(cmd_bufs_[img_idx], (w_n_cells_ + 255) / 256, 1, 1);
        // compute write -> vertex attribute read + indirect-command read at the draw
        VkMemoryBarrier vmb{};
        vmb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        vmb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        vmb.dstAccessMask = VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT | VK_ACCESS_INDIRECT_COMMAND_READ_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            VK_PIPELINE_STAGE_VERTEX_INPUT_BIT | VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT,
            0, 1, &vmb, 0, nullptr, 0, nullptr);
    }

    // GPU skinning: pose the splats (rest + weights + pose -> pos_buf_) when a pose was applied.
    // Runs BEFORE the sort so the depth keys are computed from the posed positions. Dirty-flag
    // gated: the posed buffer persists while the camera orbits (only the sort re-runs per frame).
    if (skinned_active_ && skin_pose_dirty_ && skin_pipe_ != VK_NULL_HANDLE && n_ > 0) {
        vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, skin_pipe_);
        vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, skin_layout_,
                                0, 1, &skin_desc_set_, 0, nullptr);
        struct SkinPC { uint32_t count, n_bones; } spc{ n_, skin_bones_ };
        vkCmdPushConstants(cmd_bufs_[img_idx], skin_layout_, VK_SHADER_STAGE_COMPUTE_BIT,
                           0, sizeof(spc), &spc);
        vkCmdDispatch(cmd_bufs_[img_idx], (n_ + 255) / 256, 1, 1);
        // skin (compute write) -> sort (compute read) AND -> vertex attribute read at draw
        VkMemoryBarrier smb{};
        smb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        smb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        smb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT | VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,
            0, 1, &smb, 0, nullptr, 0, nullptr);
        skin_pose_dirty_ = false;
    }

    // GPU bitonic sort: back-to-front splat ordering (compute passes) — no CPU in the per-frame path.
    if (sort_ready_ && n_ > 0) {
        vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, sort_pipe_);
        vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_COMPUTE, sort_layout_, 0, 1, &sort_desc_set_, 0, nullptr);

        struct SortPC { uint32_t mode, j, k, count; float zx, zy, zz, tz; } pc{};
        pc.mode = 0; pc.count = n_; pc.zx = depth_zx; pc.zy = depth_zy; pc.zz = depth_zz; pc.tz = depth_tz;

        auto sort_barrier = [&]() {
            VkMemoryBarrier mb{};
            mb.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
            mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT;
            vkCmdPipelineBarrier(cmd_bufs_[img_idx],
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                0, 1, &mb, 0, nullptr, 0, nullptr);
        };

        uint32_t groups_real   = (n_ + 255) / 256;
        uint32_t groups_padded = (sort_padded_ + 255) / 256;

        // 1. depth -> sortable key (real splats only; padding keys stay 0xFFFFFFFF)
        vkCmdPushConstants(cmd_bufs_[img_idx], sort_layout_, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(pc), &pc);
        vkCmdDispatch(cmd_bufs_[img_idx], groups_real, 1, 1);
        sort_barrier();

        // 2. bitonic sort over the padded (power-of-two) array
        pc.mode = 1; pc.count = sort_padded_;
        for (uint32_t k = 2; k <= sort_padded_; k <<= 1) {
            for (uint32_t j = k >> 1; j > 0; j >>= 1) {
                pc.j = j; pc.k = k;
                vkCmdPushConstants(cmd_bufs_[img_idx], sort_layout_, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(pc), &pc);
                vkCmdDispatch(cmd_bufs_[img_idx], groups_padded, 1, 1);
                sort_barrier();
            }
        }

        // barrier: sort (compute write) -> index read (vertex input)
        VkMemoryBarrier mb2{};
        mb2.sType         = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        mb2.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        mb2.dstAccessMask = VK_ACCESS_INDEX_READ_BIT;
        vkCmdPipelineBarrier(cmd_bufs_[img_idx],
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,
            0, 1, &mb2, 0, nullptr, 0, nullptr);
    }

    // Render pass (offscreen — color only)
    VkRenderPassBeginInfo rpb{};
    rpb.sType             = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpb.renderPass        = rt_render_pass_;
    rpb.framebuffer       = rt_framebuffer_;
    rpb.renderArea.extent = extent_;
    VkClearValue clears[2] = {};
    clears[0].color.float32[0] = 0.015f;
    clears[0].color.float32[1] = 0.02f;
    clears[0].color.float32[2] = 0.06f;
    clears[0].color.float32[3] = 1.0f;
    clears[1].depthStencil.depth = 1.0f;
    rpb.clearValueCount   = 3;   // att 2 (the MSAA canvas) also LOAD_OP_CLEARs at 4x
    rpb.pClearValues       = clears;

    vkCmdBeginRenderPass(cmd_bufs_[img_idx], &rpb, VK_SUBPASS_CONTENTS_INLINE);
    {
        VkViewport vp{};
        vp.width  = static_cast<float>(extent_.width);
        vp.height = static_cast<float>(extent_.height);
        vp.minDepth = 0.0f; vp.maxDepth = 1.0f;
        vkCmdSetViewport(cmd_bufs_[img_idx], 0, 1, &vp);
        VkRect2D sc{};
        sc.extent = extent_;
        vkCmdSetScissor(cmd_bufs_[img_idx], 0, 1, &sc);
    }
    if (has_mesh_ && tri_pipeline_ != VK_NULL_HANDLE && tri_idx_count_ > 0) {
        vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline_layout_, 0, 1, &desc_sets_[img_idx], 0, nullptr);
        VkBuffer vb = tri_vbuf_; VkDeviceSize off = 0;
        // mesh_mode_: 0 = fill, 1 = wire only, 2 = fill then wire overlay
        // H9: frost ON swaps the fill pipeline for the relit-color one (same
        // vertex stage; frag reads the decode SSBO via gl_PrimitiveID).
        bool frost_draw = frost_on_.load(std::memory_order_relaxed)
                          && frost_active && frost_render_ready_;
        if (frost_draw) {
            vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS,
                                    frost_render_layout_, 1, 1, &frost_frag_set_, 0, nullptr);
        }
        // THE GROUND PLANE first of all (opaque, depth-writing): the surface
        // the contact shadow lands on. The shadow (no depth write) blends over
        // it; the mesh's depth-tested draw wins where they overlap.
        if (floor_pipeline_ != VK_NULL_HANDLE && floor_vbuf_ != VK_NULL_HANDLE) {
            vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, floor_pipeline_);
            vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS,
                                    pipeline_layout_, 0, 1, &desc_sets_[img_idx], 0, nullptr);
            VkBuffer fvb = floor_vbuf_; VkDeviceSize foff = 0;
            vkCmdBindVertexBuffers(cmd_bufs_[img_idx], 0, 1, &fvb, &foff);
            vkCmdDraw(cmd_bufs_[img_idx], FLOOR_VERTS, 1, 0, 0);
        }
        // THE CONTACT SHADOW first (blended over the cleared background, under
        // the mesh): the flattened mesh on the floor plane, moving with the
        // pose. Depth write is off, so the mesh's own draw wins the depth test.
        if (tri_shadow_pipeline_ != VK_NULL_HANDLE) {
            vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, tri_shadow_pipeline_);
            vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS,
                                    pipeline_layout_, 0, 1, &desc_sets_[img_idx], 0, nullptr);
            vkCmdBindVertexBuffers(cmd_bufs_[img_idx], 0, 1, &vb, &off);
            vkCmdBindIndexBuffer(cmd_bufs_[img_idx], tri_ibuf_, 0, VK_INDEX_TYPE_UINT32);
            vkCmdDrawIndexed(cmd_bufs_[img_idx], tri_idx_count_, 1, 0, 0, 0);
        }
        if (mesh_mode_ != 1) {
            vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS,
                              frost_draw ? tri_frost_pipeline_ : tri_pipeline_);
            vkCmdBindVertexBuffers(cmd_bufs_[img_idx], 0, 1, &vb, &off);
            vkCmdBindIndexBuffer(cmd_bufs_[img_idx], tri_ibuf_, 0, VK_INDEX_TYPE_UINT32);
            vkCmdDrawIndexed(cmd_bufs_[img_idx], tri_idx_count_, 1, 0, 0, 0);
        }
        if (mesh_mode_ >= 1 && tri_wire_pipeline_ != VK_NULL_HANDLE) {
            vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, tri_wire_pipeline_);
            vkCmdBindVertexBuffers(cmd_bufs_[img_idx], 0, 1, &vb, &off);
            vkCmdBindIndexBuffer(cmd_bufs_[img_idx], tri_ibuf_, 0, VK_INDEX_TYPE_UINT32);
            vkCmdDrawIndexed(cmd_bufs_[img_idx], tri_idx_count_, 1, 0, 0, 0);
        }
        if (has_overlay_ && ov_idx_count_ > 0) {
            vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, tri_pipeline_);
            VkBuffer ovb = ov_vbuf_; VkDeviceSize ooff = 0;
            vkCmdBindVertexBuffers(cmd_bufs_[img_idx], 0, 1, &ovb, &ooff);
            vkCmdBindIndexBuffer(cmd_bufs_[img_idx], ov_ibuf_, 0, VK_INDEX_TYPE_UINT32);
            vkCmdDrawIndexed(cmd_bufs_[img_idx], ov_idx_count_, 1, 0, 0, 0);
        }
        // W4 water surface: displaced substrate triangles (non-indexed, indirect —
        // vertexCount was atomically compacted by water_vis.comp this frame).
        if (water_vis_on_.load(std::memory_order_relaxed) && water_loaded_
            && w_vis_pipe_ != VK_NULL_HANDLE && w_vis_vbuf_ != VK_NULL_HANDLE) {
            vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, tri_pipeline_);
            VkBuffer wvb = w_vis_vbuf_; VkDeviceSize woff = 0;
            vkCmdBindVertexBuffers(cmd_bufs_[img_idx], 0, 1, &wvb, &woff);
            vkCmdDrawIndirect(cmd_bufs_[img_idx], w_vis_indirect_buf_, 0, 1, 0);
        }
    } else {
        vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline_);
        vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline_layout_, 0, 1, &desc_sets_[img_idx], 0, nullptr);

        // Bind vertex buffer and draw points (depth-sorted back-to-front via the GPU sort's index buffer)
        VkBuffer buf = pos_buf_;
        VkDeviceSize offset = 0;
        vkCmdBindVertexBuffers(cmd_bufs_[img_idx], 0, 1, &buf, &offset);
        if (sort_idx_buf_ != VK_NULL_HANDLE) {
            vkCmdBindIndexBuffer(cmd_bufs_[img_idx], sort_idx_buf_, 0, VK_INDEX_TYPE_UINT32);
            vkCmdDrawIndexed(cmd_bufs_[img_idx], n_, 1, 0, 0, 0);
        } else {
            vkCmdDraw(cmd_bufs_[img_idx], n_, 1, 0, 0);
        }
    }

    vkCmdEndRenderPass(cmd_bufs_[img_idx]);

    // Capture the rendered frame (copy offscreen image -> host staging) when requested.
    // The offscreen render pass leaves the image in TRANSFER_SRC, so no layout transition needed.
    bool do_capture = capture_requested_.exchange(false);
    if (do_capture) {
        ensure_capture_staging();
        VkBufferImageCopy region{};
        region.bufferOffset      = 0;
        region.bufferRowLength   = 0;
        region.bufferImageHeight = 0;
        region.imageSubresource.aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT;
        region.imageSubresource.mipLevel       = 0;
        region.imageSubresource.baseArrayLayer = 0;
        region.imageSubresource.layerCount     = 1;
        region.imageOffset = {0, 0, 0};
        region.imageExtent = {extent_.width, extent_.height, 1};
        vkCmdCopyImageToBuffer(cmd_bufs_[img_idx], rt_image_, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                               capture_staging_, 1, &region);
    }

    // Blit the offscreen result into the swapchain image and present it, so the WINDOW shows the
    // render instead of a blank screen. Skipped when the window is minimized / out-of-date.
    if (can_present) {
        transition_image_layout(cmd_bufs_[img_idx], swap_imgs_[sc_idx],
                                VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                0, VK_ACCESS_TRANSFER_WRITE_BIT,
                                VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);

        VkImageBlit blit{};
        blit.srcSubresource.aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT;
        blit.srcSubresource.mipLevel       = 0;
        blit.srcSubresource.baseArrayLayer = 0;
        blit.srcSubresource.layerCount     = 1;
        blit.srcOffsets[0] = {0, 0, 0};
        blit.srcOffsets[1] = {static_cast<int32_t>(extent_.width),
                              static_cast<int32_t>(extent_.height), 1};
        blit.dstSubresource.aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT;
        blit.dstSubresource.mipLevel       = 0;
        blit.dstSubresource.baseArrayLayer = 0;
        blit.dstSubresource.layerCount     = 1;
        blit.dstOffsets[0] = {0, 0, 0};
        blit.dstOffsets[1] = {static_cast<int32_t>(extent_.width),
                              static_cast<int32_t>(extent_.height), 1};
        vkCmdBlitImage(cmd_bufs_[img_idx],
                       rt_image_, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                       swap_imgs_[sc_idx], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                       1, &blit, VK_FILTER_LINEAR);

        if ((ui_.visible || ui_.wants_chrome()) && ui_.ok()) {
            // THE STUDIO: draw the overlay straight into the swapchain image.
            // The render pass takes it from TRANSFER_DST to PRESENT_SRC itself.
            // rt_image_ is never touched — the dyad's /frame stays pixel-clean.
            // F2/F3: wants_chrome() keeps the status bar + HUD on the glass
            // even with the overlay closed — "always visible" is literal.
            VkRenderPassBeginInfo urp{};
            urp.sType             = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
            urp.renderPass        = ui_.render_pass();
            urp.framebuffer       = ui_.fb(sc_idx);
            urp.renderArea.extent = extent_;
            vkCmdBeginRenderPass(cmd_bufs_[img_idx], &urp, VK_SUBPASS_CONTENTS_INLINE);
            ui_.record(cmd_bufs_[img_idx]);
            vkCmdEndRenderPass(cmd_bufs_[img_idx]);
        } else {
            transition_image_layout(cmd_bufs_[img_idx], swap_imgs_[sc_idx],
                                    VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                                     VK_ACCESS_TRANSFER_WRITE_BIT, 0,
                                     VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
        }
    }

    // ── THE GLASS CHANNEL ────────────────────────────────────────────────────
    // Copy the COMPOSITED swapchain image -- viewport + the Studio's overlay --
    // into the glass staging. Both branches of the present block above leave
    // swap_imgs_[sc_idx] in PRESENT_SRC, so it must be taken to TRANSFER_SRC for
    // the copy and handed BACK to PRESENT_SRC before the queue presents it.
    // (The usage flag is already there: the swapchain is created with
    // TRANSFER_SRC_BIT at engine.cpp:862.)
    //
    // NO PRESENT, NO GLASS: can_present is false when the surface is 0x0
    // (minimized) or the swapchain is out of date. There is no presented image to
    // read, and returning last frame's pixels would be an instrument reporting
    // on a window nobody can see -- so it fails loudly instead.
    bool do_glass = glass_requested_.exchange(false);
    if (do_glass) {
        if (!can_present) {
            glass_err_.store(GLASS_ERR_NO_PRESENT);
            glass_ready_.store(true);        // ready, so HTTP can report the failure
        } else {
            ensure_glass_staging();
            // both branches above leave the swapchain in PRESENT_SRC
            record_glass_copy(cmd_bufs_[img_idx], swap_imgs_[sc_idx],
                              VK_IMAGE_LAYOUT_PRESENT_SRC_KHR, glass_staging_, extent_);
        }
    }
    vkEndCommandBuffer(cmd_bufs_[img_idx]);

    // Submit. When presenting, wait on the acquire semaphore and signal the present semaphore.
    VkSubmitInfo si{};
    si.sType               = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount  = 1;
    si.pCommandBuffers     = &cmd_bufs_[img_idx];
    VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
    if (can_present) {
        si.waitSemaphoreCount   = 1;
        si.pWaitSemaphores      = &draw_sem_[img_idx];
        si.pWaitDstStageMask    = &wait_stage;
        si.signalSemaphoreCount = 1;
        si.pSignalSemaphores    = &flush_sem_[img_idx];
    }
    vkResetFences(device_, 1, &fences_[img_idx]);
    VkResult submit_res = vkQueueSubmit(queue_, 1, &si, fences_[img_idx]);
    if (submit_res == VK_ERROR_DEVICE_LOST) {
        fprintf(stderr, "FATAL: VK_ERROR_DEVICE_LOST at frame submit (slot %u)\n", img_idx);
        fflush(stderr);
        exit(2);
    }

    if (can_present) {
        VkPresentInfoKHR pi{};
        pi.sType              = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
        pi.waitSemaphoreCount = 1;
        pi.pWaitSemaphores    = &flush_sem_[img_idx];
        pi.swapchainCount     = 1;
        pi.pSwapchains        = &swapchain_;
        pi.pImageIndices      = &sc_idx;
        // B1: the present result is a swapchain-health signal, not noise — a swapchain
        // that goes stale here would otherwise never be rebuilt.
        VkResult pres_res = vkQueuePresentKHR(queue_, &pi);
        if (pres_res == VK_ERROR_DEVICE_LOST) {
            fprintf(stderr, "FATAL: VK_ERROR_DEVICE_LOST at present\n");
            fflush(stderr);
            exit(2);
        }
        if (pres_res == VK_ERROR_OUT_OF_DATE_KHR || pres_res == VK_SUBOPTIMAL_KHR)
            recreate_after_frame = true;
    }

    // the one readback law, shared with frame_idle_ui()
    readback_captures(do_capture, do_glass);
    if (do_capture) reel_note_grab();   // D3: every grab lands in the reel

    // B1: deferred swapchain rebuild (suboptimal acquire, or present reported
    // OUT_OF_DATE/SUBOPTIMAL) — done at frame end, outside the render pass.
    if (recreate_after_frame) {
        VkSurfaceCapabilitiesKHR caps{};
        vkGetPhysicalDeviceSurfaceCapabilitiesKHR(phys_dev_, surface_, &caps);
        if (caps.currentExtent.width != 0 && caps.currentExtent.height != 0)
            resize(caps.currentExtent.width, caps.currentExtent.height);
    }
    image_idx_ = (image_idx_ + 1) % MAX_FRAMES_IN_FLIGHT;
    return true;  // a present failure (minimized window) is not fatal — skip, retry next frame
}

void Engine::readback_captures(bool do_capture, bool do_glass) {
    if (do_capture) {
        vkQueueWaitIdle(queue_);
        void* mapped = nullptr;
        vkMapMemory(device_, capture_staging_mem_, 0, capture_staging_size_, 0, &mapped);
        {
            std::lock_guard<std::mutex> lk(capture_mutex_);
            size_t px = static_cast<size_t>(extent_.width) * extent_.height;
            capture_rgba_.resize(px * 4);
            const uint8_t* src = static_cast<const uint8_t*>(mapped);
            for (size_t i = 0; i < px; ++i) {
                capture_rgba_[i * 4 + 0] = src[i * 4 + 2];  // R
                capture_rgba_[i * 4 + 1] = src[i * 4 + 1];  // G
                capture_rgba_[i * 4 + 2] = src[i * 4 + 0];  // B
                capture_rgba_[i * 4 + 3] = src[i * 4 + 3];  // A
            }
            capture_w_ = extent_.width;
            capture_h_ = extent_.height;
        }
        vkUnmapMemory(device_, capture_staging_mem_);
        capture_ready_.store(true);
    }
    // the glass readback: same BGRA->RGBA swizzle (the swapchain is B8G8R8A8,
    // same as rt_image_), the same vkQueueWaitIdle the pixel-clean path already
    // paid -- but into glass_rgba_, never capture_rgba_, and it never touches the
    // reel: the reel is the pixel-clean capture ledger the dyad reads.
    if (do_glass && glass_err_.load() == GLASS_OK) {
        if (!do_capture) vkQueueWaitIdle(queue_);
        void* gmap = nullptr;
        vkMapMemory(device_, glass_staging_mem_, 0, glass_staging_size_, 0, &gmap);
        {
            std::lock_guard<std::mutex> lk(glass_mutex_);
            size_t px = static_cast<size_t>(extent_.width) * extent_.height;
            glass_rgba_.resize(px * 4);
            const uint8_t* src = static_cast<const uint8_t*>(gmap);
            for (size_t i = 0; i < px; ++i) {
                glass_rgba_[i * 4 + 0] = src[i * 4 + 2];  // R
                glass_rgba_[i * 4 + 1] = src[i * 4 + 1];  // G
                glass_rgba_[i * 4 + 2] = src[i * 4 + 0];  // B
                glass_rgba_[i * 4 + 3] = src[i * 4 + 3];  // A
            }
            glass_w_ = extent_.width;
            glass_h_ = extent_.height;
        }
        vkUnmapMemory(device_, glass_staging_mem_);
        glass_ready_.store(true);
    }
}

// THE STUDIO: the overlay with nothing loaded — the pipeline board is the
// agent-onboarding view, so it must present even when every 3D path idles.
// Same per-slot sync discipline as frame().
//
// CAPTURES ARE SERVICED HERE TOO (2026-08-31). The comment below used to read
// "no offscreen pass, no capture" and the function matched it: with no mesh and
// no particles the engine lives in THIS loop, so GET /frame could never
// complete -- it timed out for the whole idle session, and the glass channel
// would have inherited the same hole. The claim and the code disagreed, and the
// code was the one the operator's eye hit. Now:
//   /frame -> rt_image_ cleared to the studio background (there is honestly
//             nothing rendered; a stale or uninitialized offscreen image would
//             be an instrument reading a frame that was never drawn)
//   /glass -> the composited swapchain, exactly as frame() serves it
bool Engine::frame_idle_ui() {
    // D1: the clock ticks here too — idle must not freeze the studio's time
    {
        double scrub = show_scrub_.exchange(-1.0, std::memory_order_relaxed);
        if (scrub >= 0.0) show_time_.store(scrub, std::memory_order_relaxed);
        if (show_time_.load(std::memory_order_relaxed) < 0.0)
            show_time_.store(0.0, std::memory_order_relaxed);
        auto now = std::chrono::steady_clock::now();
        if (show_last_.time_since_epoch().count() != 0 && show_playing_.load(std::memory_order_relaxed)) {
            show_time_.store(show_time_.load(std::memory_order_relaxed)
                + std::chrono::duration<double>(now - show_last_).count()
                * show_speed_.load(std::memory_order_relaxed), std::memory_order_relaxed);
        }
        show_last_ = now;
    }
    {
        double t = show_time_.load(std::memory_order_relaxed);
        float per = show_period();
        uint32_t nj = show_joint_count();
        uint32_t cur = nj ? static_cast<uint32_t>(t / per) % nj : 0;
        bool hinge_now = hinge_active_ && nj == 0;
        std::string src = nj ? "joints" : (hinge_now ? "hinge" : "none");
        ui_.set_show_clock(t, nj ? nj * static_cast<double>(per) : (hinge_now ? hinge_period_ : 0.0),
                           show_playing_.load(), show_speed_.load(), nj, cur, per,
                           nj ? show_joint_name(cur) : std::string(hinge_now ? "knees (hinge march)" : "none"),
                           show_current_theta(), src, hinge_now ? hinge_period_ : 0.f);
                           ui_.set_key_marks(key_marks_list(), src);   // D1: the timeline's key diamonds
                           // D7: push joint-aware key marks for the dope sheet (idle path)
                           { auto li = key_marks_list_info();
                             std::vector<StudioUI::DopeKey> dk;
                             dk.reserve(li.size());
                             for (auto& i : li) dk.push_back({i.name, i.t, i.joint});                              ui_.set_dope_keys(std::move(dk)); }
                            push_timeline_markers();

    }
    push_hud_state();   // F3: idle presents the chrome too (gait/water rows)
    console_drain();    // F1: the console answers even when every 3D path idles
    consume_console_ui_request(); // F1a: HTTP presentation requests land here
    consume_doc_request();         // E1a: HTTP docs requests land here
    // B3: consume a queued synthetic click (idle path too — the Studio must
    // answer even when every 3D path idles)
    // D4a: HTTP compare requests are consumed on the render thread, before
    // prepare() publishes the current glass. GET /compare therefore reads a
    // committed selection, never a half-applied network intent.
    if (compare_request_pending_.exchange(false)) {
        ui_.apply_compare_request(compare_request_slot_.load(),
                                  compare_request_clear_.load());
    }
    // E2a: resolve the HTTP deep link on the render thread before prepare()
    // publishes the glass; the HTTP worker only receives the committed result.
    if (link_request_pending_.exchange(false)) {
        const int stage = link_request_stage_.load(std::memory_order_relaxed);
        const int line = ui_.docs_link_line(stage);
        const bool ok = line >= 0;
        if (ok) ui_.docs_link_stage(stage);
        {
            std::lock_guard<std::mutex> lk(link_request_m_);
            link_request_ok_ = ok;
            link_request_line_ = ok ? line : -1;
            link_request_doc_ = ui_.docs_current();
            link_request_done_ = true;
        }
        link_request_cv_.notify_one();
    }
    if (ui_click_pending_.exchange(false)) {
        ui_.on_lbutton(ui_click_x_.load(), ui_click_y_.load(), true);
        ui_.on_lbutton(0, 0, false);
    }
    // C1: idle means no pack and no mesh — the editor view is honestly empty
    {
        joint_view_scratch_.clear();
        ui_.set_joints_view(joint_view_scratch_, 0, -1);
        ui_.set_gizmo(false, 0, 0, 0, 0, "");
    }
    // C4: the outliner answers in idle too — same one formatting site
    {
        auto rows = scene_rows();
        int ir = inspect_row_.load();
        if (ir >= 0 && ir < static_cast<int>(rows.size())) {
            const auto& r = rows[ir];
            std::string hint = r.toggleable
                ? "toggle: " + scene_command(r.id, r.state == 0)
                : "read-only atom (status row)";
            ui_.set_inspect_view(ir, r.id, r.label, inspect_kv(ir), hint);
        } else {
            ui_.set_inspect_view(-1, "", "", {}, "");
        }
        ui_.set_scene_view(std::move(rows));
    }
    // D6: the bookmark chips answer in idle too — same store
    ui_.set_cam_view(cam_mark_names());
    // D5: the capture session answers in idle too — same document
    ui_.set_capture_view(capture_kv());
    ui_.prepare(extent_.width, extent_.height);
    uint32_t img_idx = image_idx_;
    VkResult fence_res = vkWaitForFences(device_, 1, &fences_[img_idx], VK_TRUE, UINT64_MAX);
    if (fence_res == VK_ERROR_DEVICE_LOST) {
        fprintf(stderr, "FATAL: VK_ERROR_DEVICE_LOST at idle-ui fence wait\n");
        fflush(stderr);
        exit(2);
    }
    uint32_t sc_idx = 0;
    VkResult acquire_res = vkAcquireNextImageKHR(device_, swapchain_, 100000000ULL,
                                                 draw_sem_[img_idx], VK_NULL_HANDLE, &sc_idx);
    if (acquire_res == VK_ERROR_DEVICE_LOST) {
        fprintf(stderr, "FATAL: VK_ERROR_DEVICE_LOST at idle-ui acquire\n");
        fflush(stderr);
        exit(2);
    }
    if (acquire_res == VK_ERROR_OUT_OF_DATE_KHR) {
        VkSurfaceCapabilitiesKHR caps{};
        vkGetPhysicalDeviceSurfaceCapabilitiesKHR(phys_dev_, surface_, &caps);
        if (caps.currentExtent.width != 0 && caps.currentExtent.height != 0) {
            resize(caps.currentExtent.width, caps.currentExtent.height);
            return true;
        }
        // 0x0 = minimized: fall through with can_present=false — the idle path
        // keeps the UI's own captures servable headless (same law as frame()).
        headless_minimized_.store(true);
    } else if (acquire_res == VK_SUCCESS || acquire_res == VK_SUBOPTIMAL_KHR) {
        headless_minimized_.store(false);
    }
    bool can_present = (acquire_res == VK_SUCCESS || acquire_res == VK_SUBOPTIMAL_KHR);
    bool recreate_after_frame = (acquire_res == VK_SUBOPTIMAL_KHR);

    bool do_capture = capture_requested_.exchange(false);
    bool do_glass   = glass_requested_.exchange(false);
    bool ui_drawn   = false;

    // the SAME camera law frame() uses, so /project and the gizmo stay live when
    // nothing is loaded (they used to go dead here — last_vp_valid_ was never set
    // on the idle path, so the emptiest viewport was also the one with no frame
    // of reference at all).
    float proj[16], view[16];
    update_camera_matrices(proj, view);
    push_grid_overlay();
    push_rig_overlay();

    VkCommandBufferBeginInfo bbi{};
    bbi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    vkResetCommandBuffer(cmd_bufs_[img_idx], 0);
    vkBeginCommandBuffer(cmd_bufs_[img_idx], &bbi);
    if (can_present) {
        transition_image_layout(cmd_bufs_[img_idx], swap_imgs_[sc_idx],
                                VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                0, VK_ACCESS_TRANSFER_WRITE_BIT,
                                VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
        VkClearColorValue cc = {{0.015f, 0.02f, 0.06f, 1.0f}};
        VkImageSubresourceRange sr{ VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };
        vkCmdClearColorImage(cmd_bufs_[img_idx], swap_imgs_[sc_idx],
                             VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &cc, 1, &sr);

        // /frame in idle: there is no offscreen render this pass, so the honest
        // pixel-clean image is the studio background -- NOT whatever rt_image_
        // happened to hold. UNDEFINED as the old layout discards the contents,
        // which is exactly right before a clear.
        if (do_capture) {
            ensure_capture_staging();
            transition_image_layout(cmd_bufs_[img_idx], rt_image_,
                                    VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                    0, VK_ACCESS_TRANSFER_WRITE_BIT,
                                    VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
            vkCmdClearColorImage(cmd_bufs_[img_idx], rt_image_,
                                 VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &cc, 1, &sr);
            transition_image_layout(cmd_bufs_[img_idx], rt_image_,
                                    VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                                    VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                                    VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
            VkBufferImageCopy region{};
            region.bufferOffset      = 0;
            region.bufferRowLength   = 0;
            region.bufferImageHeight = 0;
            region.imageSubresource.aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT;
            region.imageSubresource.mipLevel       = 0;
            region.imageSubresource.baseArrayLayer = 0;
            region.imageSubresource.layerCount     = 1;
            region.imageOffset = {0, 0, 0};
            region.imageExtent = {extent_.width, extent_.height, 1};
            vkCmdCopyImageToBuffer(cmd_bufs_[img_idx], rt_image_, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                                   capture_staging_, 1, &region);
        }

        VkRenderPassBeginInfo urp{};
        urp.sType             = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
        urp.renderPass        = ui_.render_pass();
        urp.framebuffer       = ui_.fb(sc_idx);
        urp.renderArea.extent = extent_;
        vkCmdBeginRenderPass(cmd_bufs_[img_idx], &urp, VK_SUBPASS_CONTENTS_INLINE);
        ui_.record(cmd_bufs_[img_idx]);
        vkCmdEndRenderPass(cmd_bufs_[img_idx]);
        ui_drawn = true;
    }
    if (do_glass) {
        if (!can_present) {
            glass_err_.store(GLASS_ERR_NO_PRESENT);
            glass_ready_.store(true);
        } else {
            ensure_glass_staging();
            // the UI render pass leaves the swapchain in PRESENT_SRC; with no UI
            // it is still TRANSFER_DST from the clear above.
            record_glass_copy(cmd_bufs_[img_idx], swap_imgs_[sc_idx],
                              ui_drawn ? VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
                                       : VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                              glass_staging_, extent_);
        }
    }
    vkEndCommandBuffer(cmd_bufs_[img_idx]);

    VkSubmitInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &cmd_bufs_[img_idx];
    VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
    if (can_present) {
        si.waitSemaphoreCount = 1;
        si.pWaitSemaphores = &draw_sem_[img_idx];
        si.pWaitDstStageMask = &wait_stage;
        si.signalSemaphoreCount = 1;
        si.pSignalSemaphores = &flush_sem_[img_idx];
    }
    vkResetFences(device_, 1, &fences_[img_idx]);
    VkResult submit_res = vkQueueSubmit(queue_, 1, &si, fences_[img_idx]);
    if (submit_res == VK_ERROR_DEVICE_LOST) {
        fprintf(stderr, "FATAL: VK_ERROR_DEVICE_LOST at idle-ui submit\n");
        fflush(stderr);
        exit(2);
    }
    if (can_present) {
        VkPresentInfoKHR pi{};
        pi.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
        pi.waitSemaphoreCount = 1;
        pi.pWaitSemaphores = &flush_sem_[img_idx];
        pi.swapchainCount = 1;
        pi.pSwapchains = &swapchain_;
        pi.pImageIndices = &sc_idx;
        VkResult pres_res = vkQueuePresentKHR(queue_, &pi);
        if (pres_res == VK_ERROR_DEVICE_LOST) {
            fprintf(stderr, "FATAL: VK_ERROR_DEVICE_LOST at idle-ui present\n");
            fflush(stderr);
            exit(2);
        }
        if (pres_res == VK_ERROR_OUT_OF_DATE_KHR || pres_res == VK_SUBOPTIMAL_KHR)
            recreate_after_frame = true;
    }
    // the SAME readback law as frame() — one implementation, two loops
    readback_captures(do_capture, do_glass);
    if (recreate_after_frame) {
        VkSurfaceCapabilitiesKHR caps{};
        vkGetPhysicalDeviceSurfaceCapabilitiesKHR(phys_dev_, surface_, &caps);
        if (caps.currentExtent.width != 0 && caps.currentExtent.height != 0)
            resize(caps.currentExtent.width, caps.currentExtent.height);
    }
    image_idx_ = (image_idx_ + 1) % MAX_FRAMES_IN_FLIGHT;
    Sleep(8);   // same pacing law as the idle path: never spin a core on nothing
    return true;
}


void Engine::resize(uint32_t w, uint32_t h) {
    vkDeviceWaitIdle(device_);
    // A minimized window reports a 0x0 surface (min==max==0); a swapchain cannot be created for
    // it. Skip the rebuild and keep the old swapchain — the next resize (after restore) rebuilds.
    VkSurfaceCapabilitiesKHR caps{};
    vkGetPhysicalDeviceSurfaceCapabilitiesKHR(phys_dev_, surface_, &caps);
    if (caps.currentExtent.width == 0 || caps.currentExtent.height == 0) return;

    extent_ = {w, h};
    // Recreate swapchain and all dependent resources

    // Destroy framebuffers
    for (auto f : frames_) vkDestroyFramebuffer(device_, f, nullptr);
    for (auto v : img_views_) vkDestroyImageView(device_, v, nullptr);
    vkDestroySwapchainKHR(device_, swapchain_, nullptr);
    destroy_depth_resources();

    // Recreate swapchain (re-fills img_views_/frames_/cmd_bufs_/desc_sets_ to the new count)
    create_swapchain();
    create_depth_resources();

    // Recreate framebuffers (command buffers persist -- they are re-recorded each frame)
    create_framebuffers();

    // Recreate the offscreen target too, so its extent stays in lockstep with the swapchain
    // (the blit offscreen -> swapchain and the /frame capture both assume matching extents).
    if (rt_framebuffer_) vkDestroyFramebuffer(device_, rt_framebuffer_, nullptr);
    if (rt_render_pass_) vkDestroyRenderPass(device_, rt_render_pass_, nullptr);
    if (rt_view_)        vkDestroyImageView(device_, rt_view_, nullptr);
    if (rt_mem_)         vkFreeMemory(device_, rt_mem_, nullptr);
    if (rt_image_)       vkDestroyImage(device_, rt_image_, nullptr);
    create_offscreen();

    // THE STUDIO: the UI's per-image framebuffers die with the swapchain views
    if (ui_.ok()) ui_.create_swap_resources(img_views_, extent_);
}

void Engine::create_depth_resources() {
    VkImageCreateInfo ici{};
    ici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType     = VK_IMAGE_TYPE_2D;
    ici.format        = VK_FORMAT_D32_SFLOAT;
    ici.extent        = {extent_.width, extent_.height, 1};
    ici.mipLevels     = 1;
    ici.arrayLayers   = 1;
    ici.samples       = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling        = VK_IMAGE_TILING_OPTIMAL;
    ici.usage         = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    vkCreateImage(device_, &ici, nullptr, &depth_image_);
    VkMemoryRequirements mr; vkGetImageMemoryRequirements(device_, depth_image_, &mr);
    VkMemoryAllocateInfo ai{};
    ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize  = mr.size;
    ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    vkAllocateMemory(device_, &ai, nullptr, &depth_mem_);
    vkBindImageMemory(device_, depth_image_, depth_mem_, 0);

    VkImageViewCreateInfo vci{};
    vci.sType    = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    vci.image    = depth_image_;
    vci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    vci.format   = VK_FORMAT_D32_SFLOAT;
    vci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    vci.subresourceRange.levelCount = 1;
    vci.subresourceRange.layerCount = 1;
    vkCreateImageView(device_, &vci, nullptr, &depth_view_);
}

void Engine::destroy_depth_resources() {
    if (depth_view_)  { vkDestroyImageView(device_, depth_view_, nullptr); depth_view_ = VK_NULL_HANDLE; }
    if (depth_image_) { vkDestroyImage(device_, depth_image_, nullptr); depth_image_ = VK_NULL_HANDLE; }
    if (depth_mem_)   { vkFreeMemory(device_, depth_mem_, nullptr); depth_mem_ = VK_NULL_HANDLE; }
}

void Engine::create_offscreen() {
    // MSAA 4x (2026-09-03 membrane): the scene renders INTO a multisample image;
    // the pass auto-resolves into rt_image_. Every consumer (capture, blit, the
    // pixel-clean background clear) keeps touching rt_image_ and never knows.
    // Falsifier at the query: if the GPU can't do 4x for color AND depth, fall
    // back to 1x — structurally identical to the pre-MSAA pass (no resolve).
    VkPhysicalDeviceProperties props{};
    vkGetPhysicalDeviceProperties(phys_dev_, &props);
    VkPhysicalDeviceLimits lim = props.limits;
    auto has = [&lim](VkSampleCountFlags f, VkSampleCountFlags want) {
        return (f & want) == want;
    };
    rt_samples_ = VK_SAMPLE_COUNT_1_BIT;
    if (has(lim.framebufferColorSampleCounts, VK_SAMPLE_COUNT_4_BIT) &&
        has(lim.framebufferDepthSampleCounts,   VK_SAMPLE_COUNT_4_BIT)) {
        rt_samples_ = VK_SAMPLE_COUNT_4_BIT;
    } else {
        fprintf(stderr, "[msaa] 4x unsupported (color=0x%x depth=0x%x) — rendering at 1x\n",
                (unsigned)lim.framebufferColorSampleCounts,
                (unsigned)lim.framebufferDepthSampleCounts);
    }
    const bool msaa = rt_samples_ == VK_SAMPLE_COUNT_4_BIT;
    // Recreate-safety: create_offscreen runs again on every resize — release the
    // previous MSAA block first (rt_image_ and friends are released by the caller).
    if (rt_msaa_view_)   { vkDestroyImageView(device_, rt_msaa_view_, nullptr); rt_msaa_view_ = VK_NULL_HANDLE; }
    if (rt_msaa_image_)  { vkDestroyImage(device_, rt_msaa_image_, nullptr); rt_msaa_image_ = VK_NULL_HANDLE; }
    if (rt_msaa_mem_)    { vkFreeMemory(device_, rt_msaa_mem_, nullptr); rt_msaa_mem_ = VK_NULL_HANDLE; }

    // Offscreen render target: /frame renders to this and captures from it, so the capture never
    // depends on the (minimizable) window. Color-only, final layout TRANSFER_SRC for direct readback.
    // At 4x this attachment is the RESOLVE target (validation law: resolves are always 1x) —
    // the multisample canvas below is the subpass's color attachment.
    VkAttachmentDescription color{};
    color.format         = swap_fmt_;
    color.samples        = VK_SAMPLE_COUNT_1_BIT;    // resolve targets are ALWAYS 1x
    color.loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR;
    color.storeOp        = VK_ATTACHMENT_STORE_OP_STORE;
    color.stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    color.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    color.initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED;
    color.finalLayout    = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

    // The multisample canvas the scene draws into (only present at 4x).
    VkAttachmentDescription msaa_att{};
    msaa_att.format         = swap_fmt_;
    msaa_att.samples        = rt_samples_;
    msaa_att.loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR;
    msaa_att.storeOp        = VK_ATTACHMENT_STORE_OP_DONT_CARE;   // data lives in the resolve
    msaa_att.stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    msaa_att.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    msaa_att.initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED;
    msaa_att.finalLayout    = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkAttachmentReference color_ref{};
    color_ref.attachment = msaa ? 2 : 0;   // at 4x the SCENE draws into the multisample att
    color_ref.layout     = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkAttachmentReference msaa_ref{};
    msaa_ref.attachment = 0;               // ...and resolves into rt_image_ (1x, the law)
    msaa_ref.layout     = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkAttachmentDescription depth{};
    depth.format         = VK_FORMAT_D32_SFLOAT;
    depth.samples        = rt_samples_;
    depth.loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR;
    depth.storeOp        = VK_ATTACHMENT_STORE_OP_STORE;
    depth.stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    depth.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    depth.initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED;
    depth.finalLayout    = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    VkAttachmentReference depth_ref{};
    depth_ref.attachment = 1;
    depth_ref.layout     = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint    = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments    = &color_ref;
    subpass.pDepthStencilAttachment = &depth_ref;
    if (msaa) {
        subpass.pResolveAttachments = &msaa_ref;   // MSAA image (att 2) -> rt_image_ (att 0)
    }

    VkAttachmentDescription attachments[3] = { color, depth, msaa_att };
    VkRenderPassCreateInfo rpci{};
    rpci.sType           = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    rpci.attachmentCount = msaa ? 3 : 2;
    rpci.pAttachments    = attachments;
    rpci.subpassCount    = 1;
    rpci.pSubpasses      = &subpass;    vkCreateRenderPass(device_, &rpci, nullptr, &rt_render_pass_);

    // The multisample canvas (4x): the scene's actual attachment 2. Resolution
    // into rt_image_ happens inside the render pass, free of extra barriers.
    if (msaa) {
        VkImageCreateInfo mici{};
        mici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        mici.imageType     = VK_IMAGE_TYPE_2D;
        mici.format        = swap_fmt_;
        mici.extent        = {extent_.width, extent_.height, 1};
        mici.mipLevels     = 1;
        mici.arrayLayers   = 1;
        mici.samples       = rt_samples_;
        mici.tiling        = VK_IMAGE_TILING_OPTIMAL;
        mici.usage         = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
        mici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        if (vkCreateImage(device_, &mici, nullptr, &rt_msaa_image_) == VK_SUCCESS) {
            VkMemoryRequirements mmr; vkGetImageMemoryRequirements(device_, rt_msaa_image_, &mmr);
            VkMemoryAllocateInfo mai{};
            mai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
            mai.allocationSize  = mmr.size;
            mai.memoryTypeIndex = find_mem_type(mmr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
            if (vkAllocateMemory(device_, &mai, nullptr, &rt_msaa_mem_) == VK_SUCCESS &&
                vkBindImageMemory(device_, rt_msaa_image_, rt_msaa_mem_, 0) == VK_SUCCESS) {
                VkImageViewCreateInfo mvci{};
                mvci.sType    = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
                mvci.image    = rt_msaa_image_;
                mvci.viewType = VK_IMAGE_VIEW_TYPE_2D;
                mvci.format   = swap_fmt_;
                mvci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
                mvci.subresourceRange.levelCount = 1;
                mvci.subresourceRange.layerCount = 1;
                vkCreateImageView(device_, &mvci, nullptr, &rt_msaa_view_);
            }
        }
    }

    VkImageCreateInfo ici{};
    ici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType     = VK_IMAGE_TYPE_2D;
    ici.format        = swap_fmt_;
    ici.extent        = {extent_.width, extent_.height, 1};
    ici.mipLevels     = 1;
    ici.arrayLayers   = 1;
    ici.samples       = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling        = VK_IMAGE_TILING_OPTIMAL;
    ici.usage         = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    vkCreateImage(device_, &ici, nullptr, &rt_image_);
    VkMemoryRequirements mr; vkGetImageMemoryRequirements(device_, rt_image_, &mr);
    VkMemoryAllocateInfo ai{};
    ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize  = mr.size;
    ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    vkAllocateMemory(device_, &ai, nullptr, &rt_mem_);
    vkBindImageMemory(device_, rt_image_, rt_mem_, 0);

    VkImageViewCreateInfo vci{};
    vci.sType    = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    vci.image    = rt_image_;
    vci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    vci.format   = swap_fmt_;
    vci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    vci.subresourceRange.levelCount = 1;
    vci.subresourceRange.layerCount = 1;
    vkCreateImageView(device_, &vci, nullptr, &rt_view_);

    // Depth attachment for triangle depth testing
    VkImageCreateInfo di{};
    di.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    di.imageType     = VK_IMAGE_TYPE_2D;
    di.format        = VK_FORMAT_D32_SFLOAT;
    di.extent        = {extent_.width, extent_.height, 1};
    di.mipLevels     = 1; di.arrayLayers = 1; di.samples = rt_samples_;   // MSAA depth (matches the pass)
    di.tiling        = VK_IMAGE_TILING_OPTIMAL;
    di.usage         = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT;
    di.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    vkCreateImage(device_, &di, nullptr, &rt_depth_image_);
    VkMemoryRequirements dmr; vkGetImageMemoryRequirements(device_, rt_depth_image_, &dmr);
    VkMemoryAllocateInfo dai{};
    dai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    dai.allocationSize = dmr.size;
    dai.memoryTypeIndex = find_mem_type(dmr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    vkAllocateMemory(device_, &dai, nullptr, &rt_depth_mem_);
    vkBindImageMemory(device_, rt_depth_image_, rt_depth_mem_, 0);
    VkImageViewCreateInfo dvi{};
    dvi.sType    = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    dvi.image    = rt_depth_image_;
    dvi.viewType = VK_IMAGE_VIEW_TYPE_2D;
    dvi.format   = VK_FORMAT_D32_SFLOAT;
    dvi.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    dvi.subresourceRange.levelCount = 1; dvi.subresourceRange.layerCount = 1;
    vkCreateImageView(device_, &dvi, nullptr, &rt_depth_view_);

    VkFramebufferCreateInfo fci{};
    fci.sType           = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
    fci.renderPass      = rt_render_pass_;
    VkImageView off_attach[3] = { rt_view_, rt_depth_view_, rt_msaa_view_ };
    fci.attachmentCount = msaa ? 3 : 2;
    fci.pAttachments    = off_attach;
    fci.width           = extent_.width;
    fci.height          = extent_.height;
    fci.layers          = 1;
    vkCreateFramebuffer(device_, &fci, nullptr, &rt_framebuffer_);
}

bool Engine::create_framebuffers() {
    VkImageView attachments[2];
    for (uint32_t i = 0; i < frames_.size(); ++i) {
        attachments[0] = img_views_[i];
        attachments[1] = depth_view_;
        VkFramebufferCreateInfo fci{};
        fci.sType            = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass       = render_pass_;
        fci.attachmentCount  = 2;
        fci.pAttachments     = attachments;
        fci.width            = extent_.width;
        fci.height           = extent_.height;
        fci.layers           = 1;
        if (vkCreateFramebuffer(device_, &fci, nullptr, &frames_[i]) != VK_SUCCESS) return false;
    }
    return true;
}

bool Engine::create_command_buffers() {
    if (cmd_bufs_.empty()) return true;
    VkCommandBufferAllocateInfo ai{};
    ai.sType              = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    ai.commandPool        = cmd_pool_;
    ai.level              = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    ai.commandBufferCount = static_cast<uint32_t>(cmd_bufs_.size());
    return vkAllocateCommandBuffers(device_, &ai, cmd_bufs_.data()) == VK_SUCCESS;
}

// ── Single-time command helper ───────────────────────────────────────────────────────────

VkCommandBuffer Engine::begin_single_time_cmd() {
    VkCommandBufferAllocateInfo ai{};
    ai.sType            = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    ai.commandPool      = cmd_pool_;  // need to create this — add to engine.hpp
    ai.level            = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    ai.commandBufferCount = 1;
    VkCommandBuffer cb;
    vkAllocateCommandBuffers(device_, &ai, &cb);
    VkCommandBufferBeginInfo bbi{};
    bbi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    bbi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    vkBeginCommandBuffer(cb, &bbi);
    return cb;
}

void Engine::end_single_time_cmd(VkCommandBuffer cb) {
    vkEndCommandBuffer(cb);
    VkSubmitInfo si{};
    si.sType               = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount  = 1;
    si.pCommandBuffers     = &cb;
    vkQueueSubmit(queue_, 1, &si, VK_NULL_HANDLE);
    vkQueueWaitIdle(queue_);
    vkFreeCommandBuffers(device_, cmd_pool_, 1, &cb);
}

uint32_t Engine::find_mem_type(uint32_t types, VkMemoryPropertyFlags flags) {
    VkPhysicalDeviceMemoryProperties props;
    vkGetPhysicalDeviceMemoryProperties(phys_dev_, &props);
    for (uint32_t i = 0; i < props.memoryTypeCount; ++i) {
        if ((types & (1u << i)) && (props.memoryTypes[i].propertyFlags & flags) == flags)
            return i;
    }
    fprintf(stderr, "Failed to find suitable memory type\n");
    return 0;
}
