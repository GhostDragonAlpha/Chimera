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
    if (g_keys[' ']) cam.radius = fmaxf(1.0f, cam.radius - zoom_speed);
    if (g_keys[VK_CONTROL]) cam.radius = fminf(100.0f, cam.radius + zoom_speed);

    // Hold R → reset view
    if (g_keys['R']) {
        cam.theta   = 0.0f;
        cam.phi     = 0.3f;
        cam.radius  = 12.0f;
        cam.pan_x   = 0.0f;
        cam.pan_y   = 0.0f;
        cam.target[0] = cam.target[1] = cam.target[2] = 0.0f;
    }
}

static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    if (msg == WM_CLOSE)  { DestroyWindow(hwnd); return 0; }
    if (msg == WM_DESTROY){ PostQuitMessage(0); return 0; }

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
        g_cam.radius = fmaxf(1.0f, fminf(100.0f, g_cam.radius + delta * 2.0f));
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

    // Set up the debug messenger (leaked until instance teardown — dev tooling only)
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
            VkDebugUtilsMessengerEXT messenger;
            pfn(instance_, &dci, nullptr, &messenger);
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
    if (comp_params_buf_) { vkDestroyBuffer(device_, comp_params_buf_, nullptr); vkFreeMemory(device_, comp_params_mem_, nullptr); }
    if (capture_staging_) { vkDestroyBuffer(device_, capture_staging_, nullptr); vkFreeMemory(device_, capture_staging_mem_, nullptr); }
    destroy_sort_resources();
    destroy_skin_resources();
    destroy_triangle_resources();

    if (compute_desc_pool_)     vkDestroyDescriptorPool(device_,     compute_desc_pool_,      nullptr);
    if (compute_desc_layout_)   vkDestroyDescriptorSetLayout(device_, compute_desc_layout_,   nullptr);
    if (compute_pipeline_layout_) vkDestroyPipelineLayout(device_, compute_pipeline_layout_, nullptr);
    if (compute_pipeline_)      vkDestroyPipeline(device_,          compute_pipeline_,      nullptr);

    if (desc_pool_)  vkDestroyDescriptorPool(device_, desc_pool_, nullptr);
    if (desc_layout_) vkDestroyDescriptorSetLayout(device_, desc_layout_, nullptr);

    if (pipeline_)  vkDestroyPipeline(device_, pipeline_,  nullptr);
    if (render_pass_) vkDestroyRenderPass(device_, render_pass_, nullptr);

    if (comp_mod_) vkDestroyShaderModule(device_, comp_mod_, nullptr);
    if (vert_mod_) vkDestroyShaderModule(device_, vert_mod_, nullptr);
    if (frag_mod_) vkDestroyShaderModule(device_, frag_mod_, nullptr);

    for (auto s : draw_sem_)  vkDestroySemaphore(device_, s,  nullptr);
    for (auto s : flush_sem_) vkDestroySemaphore(device_, s,  nullptr);
    for (auto f : fences_)    vkDestroyFence(device_,   f,    nullptr);

    if (surface_)  vkDestroySurfaceKHR(instance_, surface_,  nullptr);
    if (device_)   vkDestroyDevice(device_,                  nullptr);
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
    vkDestroyPipelineCache(device_, cache, nullptr);

    return true;
}

bool Engine::load_mesh(const std::vector<float>& verts, const std::vector<uint32_t>& indices,
                       uint32_t vcount, uint32_t icount) {
    vkDeviceWaitIdle(device_);
    upload_buffer(verts.data(), static_cast<VkDeviceSize>(verts.size()) * sizeof(float),
                  VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, tri_vbuf_, tri_vmem_);
    upload_buffer(indices.data(), static_cast<VkDeviceSize>(indices.size()) * sizeof(uint32_t),
                  VK_BUFFER_USAGE_INDEX_BUFFER_BIT, tri_ibuf_, tri_imem_);
    tri_idx_count_ = icount;
    has_mesh_ = true;
    return true;
}

void Engine::destroy_triangle_resources() {
    if (tri_pipeline_) { vkDestroyPipeline(device_, tri_pipeline_, nullptr); tri_pipeline_ = VK_NULL_HANDLE; }
    if (tri_vert_mod_) { vkDestroyShaderModule(device_, tri_vert_mod_, nullptr); tri_vert_mod_ = VK_NULL_HANDLE; }
    if (tri_frag_mod_) { vkDestroyShaderModule(device_, tri_frag_mod_, nullptr); tri_frag_mod_ = VK_NULL_HANDLE; }
    if (tri_vbuf_) { vkDestroyBuffer(device_, tri_vbuf_, nullptr); vkFreeMemory(device_, tri_vmem_, nullptr); tri_vbuf_ = VK_NULL_HANDLE; }
    if (tri_ibuf_) { vkDestroyBuffer(device_, tri_ibuf_, nullptr); vkFreeMemory(device_, tri_imem_, nullptr); tri_ibuf_ = VK_NULL_HANDLE; }
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
    g_cam.radius = fmaxf(1.0f, radius);
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
    if (n_ == 0 && !has_mesh_) return true;
    // Offscreen: render to rt_framebuffer_ and capture from rt_image_. No swapchain acquire, so
    // the /frame endpoint works even when the window is minimized (or entirely headless).
    vkWaitForFences(device_, 1, &fences_[0], VK_TRUE, UINT64_MAX);
    vkResetFences(device_, 1, &fences_[0]);
    uint32_t img_idx = 0;

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

    if (params_buf_ == VK_NULL_HANDLE) {
        VkBufferCreateInfo bci{};
        bci.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bci.size        = sizeof(Uniforms);
        bci.usage       = VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device_, &bci, nullptr, &params_buf_);
        VkMemoryRequirements mr; vkGetBufferMemoryRequirements(device_, params_buf_, &mr);
        VkMemoryAllocateInfo ai{};
        ai.sType       = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = mr.size;
        ai.memoryTypeIndex = find_mem_type(mr.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        vkAllocateMemory(device_, &ai, nullptr, &params_mem_);
        vkBindBufferMemory(device_, params_buf_, params_mem_, 0);
    }

    // Upload UBO via staging
    VkBufferCreateInfo staging_ci{};
    staging_ci.sType      = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    staging_ci.size       = sizeof(Uniforms);
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
    vkMapMemory(device_, staging_mem, 0, sizeof(Uniforms), 0, &mapped);
    std::memcpy(mapped, &ubo, sizeof(Uniforms));
    vkUnmapMemory(device_, staging_mem);

    VkCommandBuffer cb = begin_single_time_cmd();
    VkBufferCopy bc{}; bc.size = sizeof(Uniforms);
    vkCmdCopyBuffer(cb, staging_buf, params_buf_, 1, &bc);
    end_single_time_cmd(cb);
    vkDestroyBuffer(device_, staging_buf, nullptr);
    vkFreeMemory(device_, staging_mem, nullptr);

    // Update uniform descriptor
    VkDescriptorBufferInfo ubo_info{};
    ubo_info.buffer = params_buf_;
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
    bool can_present = (acquire_res == VK_SUCCESS || acquire_res == VK_SUBOPTIMAL_KHR);

    // Record command buffer
    VkCommandBufferBeginInfo bbi{};
    bbi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    vkResetCommandBuffer(cmd_bufs_[img_idx], 0);
    vkBeginCommandBuffer(cmd_bufs_[img_idx], &bbi);

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
        vkCmdBindPipeline(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, tri_pipeline_);
        vkCmdBindDescriptorSets(cmd_bufs_[img_idx], VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline_layout_, 0, 1, &desc_sets_[img_idx], 0, nullptr);
        VkBuffer vb = tri_vbuf_; VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(cmd_bufs_[img_idx], 0, 1, &vb, &off);
        vkCmdBindIndexBuffer(cmd_bufs_[img_idx], tri_ibuf_, 0, VK_INDEX_TYPE_UINT32);
        vkCmdDrawIndexed(cmd_bufs_[img_idx], tri_idx_count_, 1, 0, 0, 0);
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
    vkQueueSubmit(queue_, 1, &si, fences_[0]);

    if (can_present) {
        VkPresentInfoKHR pi{};
        pi.sType              = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
        pi.waitSemaphoreCount = 1;
        pi.pWaitSemaphores    = &flush_sem_[img_idx];
        pi.swapchainCount     = 1;
        pi.pSwapchains        = &swapchain_;
        pi.pImageIndices      = &sc_idx;
        vkQueuePresentKHR(queue_, &pi);
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
