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

// Keyboard helper: wasd + qe + space/ctrl + r reset
static void update_camera_input(CameraState& cam, float dt) {
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
        // 'P' toggles rest (slot 0) <-> wave (slot 1) on a skinned splat. Edge-triggered
        // (bit 30 of lParam = previous key state) so key autorepeat doesn't double-toggle.
        if ((wp & 0xFF) == 'P' && !(lp & 0x40000000) && g_key_engine) {
            g_key_engine->toggle_pose();
        }
    } else if (msg == WM_KEYUP || msg == WM_SYSKEYUP) {
        g_keys[wp & 0xFF] = false;
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

    // Scroll wheel → zoom
    if (msg == WM_MOUSEWHEEL) {
        float delta = static_cast<float>(GET_WHEEL_DELTA_WPARAM(wp)) / 120.0f;
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
    vkDeviceWaitIdle(device_);

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
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
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
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
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
        return true;
    }
    // Vertex buffer: DEVICE_LOCAL (the hot path must stay in VRAM — a host-visible
    // buffer cost ~6 ms/frame of PCIe traffic when the GPU hinge kernel wrote it).
    // CPU-side writes (update_mesh, hinge restore) go through a persistent
    // host-visible STAGING buffer + one transfer; the draw/compute path never
    // leaves the GPU.
    upload_buffer(verts.data(), static_cast<VkDeviceSize>(verts.size()) * sizeof(float),
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
    mesh_cpu_ = verts;
    tri_vfloats_ = verts.size();
    upload_buffer(indices.data(), static_cast<VkDeviceSize>(indices.size()) * sizeof(uint32_t),
                  VK_BUFFER_USAGE_INDEX_BUFFER_BIT | VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, tri_ibuf_, tri_imem_);
    tri_idx_count_ = icount;
    has_mesh_ = true;
    water_vis_desc_dirty_ = true;   // buffers recreated -> the water-vis set must rebind (H4)
    frost_desc_dirty_ = true;       // same for the frost decode set (H9)
    // Measure the bounding sphere about the origin (the camera target) — the
    // zoom floor derives from THIS, so the near plane can never slice the
    // mesh no matter how far in the operator scrolls. Vertex stride = 9
    // (pos3 + normal3 + color3).
    float r2max = 0.0f;
    for (size_t i = 0; i + 2 < verts.size(); i += 9) {
        float r2 = verts[i] * verts[i] + verts[i + 1] * verts[i + 1] + verts[i + 2] * verts[i + 2];
        if (r2 > r2max) r2max = r2;
    }
    g_mesh_sphere = sqrtf(r2max);
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
                VkDescriptorSetLayoutBinding b[4] = {};
                for (int k = 0; k < 4; ++k) {
                    b[k].binding = k;
                    b[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
                    b[k].descriptorCount = 1;
                    b[k].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
                }
                VkDescriptorSetLayoutCreateInfo dlci{};
                dlci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
                dlci.bindingCount = 4;
                dlci.pBindings = b;
                vkCreateDescriptorSetLayout(device_, &dlci, nullptr, &hinge_desc_layout_);

                VkPushConstantRange pcr{};
                pcr.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
                pcr.offset = 0;
                pcr.size = 3 * 16 + 6 * 4;   // vec4 JL/JR/axis + 5 floats + uint
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
                ps.descriptorCount = 4;
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
                VkDescriptorBufferInfo infos[4] = {};
                infos[0].buffer = hinge_rest_buf_; infos[0].range = VK_WHOLE_SIZE;
                infos[1].buffer = hinge_wL_buf_;   infos[1].range = VK_WHOLE_SIZE;
                infos[2].buffer = hinge_wR_buf_;   infos[2].range = VK_WHOLE_SIZE;
                infos[3].buffer = tri_vbuf_;       infos[3].range = VK_WHOLE_SIZE;
                VkWriteDescriptorSet w[4] = {};
                for (int k = 0; k < 4; ++k) {
                    w[k].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
                    w[k].dstSet = hinge_desc_set_;
                    w[k].dstBinding = k;
                    w[k].descriptorCount = 1;
                    w[k].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
                    w[k].pBufferInfo = &infos[k];
                }
                vkUpdateDescriptorSets(device_, 4, w, 0, nullptr);
            }
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
    float t = std::chrono::duration<float>(std::chrono::steady_clock::now() - hinge_t0_).count();
    const float two_pi = 6.28318530718f;
    float ph = fmodf(t, hinge_period_) / hinge_period_;
    float bL = 0.5f - 0.5f * cosf(two_pi * ph);
    float bR = 0.5f - 0.5f * cosf(two_pi * ph + hinge_phaseR_);
    float thL = bL * hinge_romL_ * 0.01745329251f;   // deg -> rad
    float thR = bR * hinge_romR_ * 0.01745329251f;

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

    // ── compute pipeline (9 SSBOs + 32 B push constants) ──
    if (!w_make_pipeline(device_, "shaders/frost_decode.spv", 9, 32,
                         frost_mod_, frost_dsl_, frost_layout_, frost_pipe_)) {
        fprintf(stderr, "frost: compute pipeline failed\n"); return false;
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
        ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
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
        ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER; ps.descriptorCount = 9;
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

// ── Frame submission ─────────────────────────────────────────────────────────────────────

bool Engine::frame() {
    // B1: consume a pending window resize BEFORE anything else — the swapchain must
    // track the window or every acquire/present goes OUT_OF_DATE from here on.
    {
        uint32_t prw = g_pending_resize_w.exchange(0);
        uint32_t prh = g_pending_resize_h.exchange(0);
        if (prw != 0 && prh != 0) resize(prw, prh);
    }
    if (n_ == 0 && !has_mesh_) return true;
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
    // CPU hinge fallback (only when the GPU kernel didn't build); the GPU path
    // is recorded into the command buffer below.
    if (hinge_active_ && hinge_pipe_ == VK_NULL_HANDLE && tri_vmap_ != nullptr) pose_hinge();

    // Upload uniform buffer (camera matrices + resolution)
    float proj[16], view[16];
    float aspect = static_cast<float>(extent_.width) / static_cast<float>(extent_.height);
    perspective(proj, 45.0f * 3.14159265f / 180.0f, aspect, 0.1f, 1000.0f);

    // Process keyboard input (WASD/QE/Space/Ctrl/R)
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

    // Depth sort is done on the GPU (radix sort, recorded in the command buffer below). Stash the
    // view matrix's z-row, which the depth-key pass needs as push constants.
    float depth_zx = view[2], depth_zy = view[6], depth_zz = view[10], depth_tz = view[14];

    struct alignas(16) Uniforms {
        float proj[16];
        float view[16];
        float resolution[2];
        float pad[2];
    } ubo{};
    std::memcpy(ubo.proj, proj, sizeof(proj));
    std::memcpy(ubo.view, view, sizeof(view));
    ubo.resolution[0] = static_cast<float>(extent_.width);
    ubo.resolution[1] = static_cast<float>(extent_.height);

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
        if (caps.currentExtent.width != 0 && caps.currentExtent.height != 0)
            resize(caps.currentExtent.width, caps.currentExtent.height);
        return true;  // next frame presents on the fresh swapchain
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
    if (hinge_active_ && hinge_pipe_ != VK_NULL_HANDLE) {
        struct HingePC { float JL[4], JR[4], axis[4]; float romL, romR, period, phaseR, time; uint32_t n; } hpc{};
        hpc.JL[0] = hinge_JL_[0]; hpc.JL[1] = hinge_JL_[1]; hpc.JL[2] = hinge_JL_[2];
        hpc.JR[0] = hinge_JR_[0]; hpc.JR[1] = hinge_JR_[1]; hpc.JR[2] = hinge_JR_[2];
        hpc.axis[0] = hinge_axis_[0]; hpc.axis[1] = hinge_axis_[1]; hpc.axis[2] = hinge_axis_[2];
        hpc.romL = hinge_romL_; hpc.romR = hinge_romR_;
        hpc.period = hinge_period_; hpc.phaseR = hinge_phaseR_;
        hpc.time = std::chrono::duration<float>(std::chrono::steady_clock::now() - hinge_t0_).count();
        hpc.n = static_cast<uint32_t>(hinge_wL_.size());
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
        // view dir = toward the camera (e42's view_to_cam = eye - target); eye is
        // the SAME float expression the camera UBO used above, widened to double.
        double eye[3] = { (double)(g_cam.target[0] + g_cam.radius * c * sx + g_cam.pan_x),
                          (double)(g_cam.target[1] + g_cam.radius * s              + g_cam.pan_y),
                          (double)(g_cam.target[2] - g_cam.radius * c * cx) };
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
    rpb.clearValueCount   = 2;
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

        transition_image_layout(cmd_bufs_[img_idx], swap_imgs_[sc_idx],
                                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                                VK_ACCESS_TRANSFER_WRITE_BIT, 0,
                                VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
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

    // Read back the captured frame (BGRA -> RGBA) into the shared CPU buffer
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
    // Offscreen render target: /frame renders to this and captures from it, so the capture never
    // depends on the (minimizable) window. Color-only, final layout TRANSFER_SRC for direct readback.
    VkAttachmentDescription color{};
    color.format         = swap_fmt_;
    color.samples        = VK_SAMPLE_COUNT_1_BIT;
    color.loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR;
    color.storeOp        = VK_ATTACHMENT_STORE_OP_STORE;
    color.stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    color.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    color.initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED;
    color.finalLayout    = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

    VkAttachmentReference color_ref{};
    color_ref.attachment = 0;
    color_ref.layout     = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkAttachmentDescription depth{};
    depth.format         = VK_FORMAT_D32_SFLOAT;
    depth.samples        = VK_SAMPLE_COUNT_1_BIT;
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

    VkAttachmentDescription attachments[2] = { color, depth };
    VkRenderPassCreateInfo rpci{};
    rpci.sType           = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    rpci.attachmentCount = 2;
    rpci.pAttachments    = attachments;
    rpci.subpassCount    = 1;
    rpci.pSubpasses      = &subpass;
    vkCreateRenderPass(device_, &rpci, nullptr, &rt_render_pass_);

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
    di.mipLevels     = 1; di.arrayLayers = 1; di.samples = VK_SAMPLE_COUNT_1_BIT;
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
    fci.attachmentCount = 2;
    VkImageView off_attach[2] = { rt_view_, rt_depth_view_ };
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
