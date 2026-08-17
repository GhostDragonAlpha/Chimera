// SPIACE native viewer — the operator window, C++ end to end.
// No browser, no Python in the frame path: Win32 window, wgpu-native (the
// Phase-13 render API), the EXACT WGSL extracted from spiace_native.html at
// startup (single source of truth for the splat shader), and the sim stream
// read from the relay over plain loopback HTTP (the transport that never
// broke). Sim stays in ca_core.exe; this is a pipe, not a brain.
//
//   viewer.exe [port] [shell.json]
//
// Mouse: drag = orbit, wheel = zoom. Keys: 1 wave, 2 walk, 3 rest, Esc quit.
//
// Build (from ChimeraEngine/native):
//   g++ -O2 -std=c++17 viewer.cpp -I viewer3rd -o viewer.exe
//       viewer3rd/wgpu_native.dll -lws2_32 -luser32 -lgdi32 -lcomctl32
//   cp viewer3rd/wgpu_native.dll .        # runtime lookup is the exe's dir

#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <commctrl.h>

#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <mutex>
#include <regex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include "webgpu.h"
#include "wgpu.h"
#include "json.hpp"

using json = nlohmann::json;

// ---------------------------------------------------------------- config --
static int   g_port = 8799;
static float CELL = 0.06f;            // genome meta cell (overwritten on meta)

// ------------------------------------------------------- stream (HTTP) ----
// The relay's SSE feed: one NDJSON JSON object per "data:" line. Read on a
// background thread; the render thread pulls the newest state out.
struct SimState {
    std::mutex m;
    std::string genome = "?";
    float cell = 0.06f;
    double bodyX = 0, bodyY = 0;
    double ground = -4;
    bool done = false;
    bool hasAnim = false;
    uint64_t animSeq = 0;             // bumped when body pose changes
};
static SimState g_sim;
static std::atomic<bool> g_running{ true };

static bool httpGetStream(int port, const char* path, SOCKET& out) {
    addrinfo hints{}, * res = nullptr;
    hints.ai_family = AF_INET; hints.ai_socktype = SOCK_STREAM;
    char ps[16]; snprintf(ps, sizeof ps, "%d", port);
    if (getaddrinfo("127.0.0.1", ps, &hints, &res) != 0) return false;
    SOCKET s = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    bool ok = false;
    if (s != INVALID_SOCKET) {
        if (connect(s, res->ai_addr, (int)res->ai_addrlen) == 0) {
            std::string req = std::string("GET ") + path +
                " HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n";
            send(s, req.c_str(), (int)req.size(), 0);
            ok = true;
        }
        if (!ok) { closesocket(s); s = INVALID_SOCKET; }
    }
    freeaddrinfo(res);
    if (ok) out = s;
    return ok;
}

// one-shot HTTP GET (scores, etc.) — returns body or ""
static std::string httpGet(int port, const char* path) {
    SOCKET s; if (!httpGetStream(port, path, s)) return "";
    std::string raw; char buf[8192]; int n;
    while ((n = recv(s, buf, sizeof buf, 0)) > 0) raw.append(buf, n);
    closesocket(s);
    auto p = raw.find("\r\n\r\n");
    return p == std::string::npos ? "" : raw.substr(p + 4);
}

static void httpPost(int port, const char* path, const std::string& body) {
    addrinfo hints{}, * res = nullptr;
    hints.ai_family = AF_INET; hints.ai_socktype = SOCK_STREAM;
    char ps[16]; snprintf(ps, sizeof ps, "%d", port);
    if (getaddrinfo("127.0.0.1", ps, &hints, &res) != 0) return;
    SOCKET c = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (c != INVALID_SOCKET && connect(c, res->ai_addr, (int)res->ai_addrlen) == 0) {
        std::ostringstream q;
        q << "POST " << path << " HTTP/1.0\r\nHost: 127.0.0.1\r\n"
          << "Content-Length: " << body.size() << "\r\n\r\n" << body;
        std::string qs = q.str();
        send(c, qs.c_str(), (int)qs.size(), 0);
        closesocket(c);
    }
    freeaddrinfo(res);
}

static void streamThread(int port) {
    while (g_running) {
        SOCKET s;
        if (!httpGetStream(port, "/stream", s)) {
            Sleep(500);               // relay not up yet — keep retrying
            continue;
        }
        // skip HTTP headers
        std::string pending; char buf[16384]; bool headersDone = false;
        int n;
        while (g_running && (n = recv(s, buf, sizeof buf, 0)) > 0) {
            pending.append(buf, n);
            if (!headersDone) {
                auto p = pending.find("\r\n\r\n");
                if (p == std::string::npos) continue;
                pending.erase(0, p + 4);
                headersDone = true;
            }
            size_t nl;
            while ((nl = pending.find('\n')) != std::string::npos) {
                std::string line = pending.substr(0, nl);
                pending.erase(0, nl + 1);
                if (line.rfind("data: ", 0) != 0) continue;
                std::string js = line.substr(6);
                if (js.empty()) continue;
                json m = json::parse(js, nullptr, false);
                if (m.is_discarded()) continue;
                std::lock_guard<std::mutex> lk(g_sim.m);
                if (m.value("type", "") == "meta") {
                    g_sim.genome = m.value("name", "?");
                    g_sim.cell = m.value("cell", 0.06);
                } else if (m.value("type", "") == "frame") {
                    g_sim.done = m.value("done", false);
                } else if (m.contains("bodyX")) {
                    double bx = m.value("bodyX", 0.0), by = m.value("bodyY", 0.0);
                    if (bx != g_sim.bodyX || by != g_sim.bodyY) {
                        g_sim.bodyX = bx; g_sim.bodyY = by; g_sim.animSeq++;
                    }
                    g_sim.hasAnim = true;
                    if (m.contains("ground") && m["ground"].is_number())
                        g_sim.ground = m["ground"].get<double>();
                }
            }
        }
        closesocket(s);
        Sleep(500);                   // stream ended — reconnect
    }
}

// ------------------------------------------------------------- WGSL -------
// Extracted from spiace_native.html at runtime: ONE shader, two frontends.
static std::string loadWGSL(const std::string& htmlPath) {
    std::ifstream f(htmlPath);
    std::ostringstream ss; ss << f.rdbuf();
    std::string h = ss.str();
    std::smatch m;
    std::regex re("const WGSL = `([^`]*)`;");
    if (!std::regex_search(h, m, re)) { fprintf(stderr, "WGSL not found in %s\n", htmlPath.c_str()); exit(1); }
    return m[1].str();
}

// ------------------------------------------------------------- shell ------
struct ShellLevel { int h; float cell; std::vector<float> inst; int n; };
static std::vector<ShellLevel> g_levels;

static void loadShell(const std::string& path) {
    std::ifstream f(path);
    if (!f) { fprintf(stderr, "no shell at %s\n", path.c_str()); exit(1); }
    json j = json::parse(f);
    for (auto& L : j["levels"]) {
        ShellLevel lv;
        lv.h = L["h"]; lv.cell = L["cell"];
        int n = L["n"]; lv.n = n;
        lv.inst.resize((size_t)n * 11);
        for (int i = 0; i < n; i++) {
            auto& p = L["pos"][i]; auto& c = L["col"][i]; auto& nr = L["nor"][i];
            float* d = lv.inst.data() + (size_t)i * 11;
            d[0] = p[0].get<double>() * lv.cell;
            d[1] = p[1].get<double>() * lv.cell;
            d[2] = p[2].get<double>() * lv.cell;
            d[3] = lv.cell * 0.6f;
            d[4] = c[0]; d[5] = c[1]; d[6] = c[2]; d[7] = 1.0f;
            d[8] = nr[0]; d[9] = nr[1]; d[10] = nr[2];
        }
        g_levels.push_back(std::move(lv));
        printf("level h=%d n=%d cell=%.4f\n", lv.h, lv.n, lv.cell);
    }
}

// --------------------------------------------------------- camera math ----
// Ported verbatim from spiace_native.html (perspective/lookAt, column-major).
static void perspective(float fovY, float aspect, float near_, float far_, float* m) {
    memset(m, 0, 16 * sizeof(float));
    float f = 1.0f / tanf(fovY / 2);
    m[0] = f / aspect; m[5] = f; m[10] = far_ / (near_ - far_); m[11] = -1;
    m[14] = far_ * near_ / (near_ - far_);
}
static void lookAt(float ex, float ey, float ez, float tx, float ty, float tz, float* m) {
    float fx = tx - ex, fy = ty - ey, fz = tz - ez;
    float fl = sqrtf(fx * fx + fy * fy + fz * fz); fx /= fl; fy /= fl; fz /= fl;
    float rx = -fz, ry = 0, rz = fx;
    float rl = sqrtf(rx * rx + rz * rz); rx /= rl; rz /= rl;
    float ux = ry * fz - rz * fy, uy = rz * fx - rx * fz, uz = rx * fy - ry * fx;
    float t[16] = { rx, ux, -fx, 0, ry, uy, -fy, 0, rz, uz, -fz, 0,
                    -(rx * ex + ry * ey + rz * ez), -(ux * ex + uy * ey + uz * ez),
                    (fx * ex + fy * ey + fz * ez), 1 };
    memcpy(m, t, sizeof t);
}

// ------------------------------------------------------------- ground -----
// Port of groundSplats(): per-depth ring march, budget = level n >> 2.
static unsigned g_seed = 1;
static float hash01(int v) {                          // visual-only hash
    unsigned x = (unsigned)v * 2654435761u;
    x ^= x >> 15; x *= 2246822519u; x ^= x >> 13;
    return (x & 0xFFFFFF) / 16777215.0f;
}
static double lodSpacing(double depth, int hPx) {
    double f = 1.0 / tan(0.85 / 2);
    return 2.5 * (depth < 0.5 ? 0.5 : depth) / ((hPx / 2.0) * f);
}

// ------------------------------------------------------------ wgpu glue ---
static WGPUInstance g_inst;
static WGPUSurface g_surf;
static WGPUAdapter g_adapter;
static WGPUDevice g_dev;
static WGPUQueue g_queue;
static WGPURenderPipeline g_pipe;
static WGPUBuffer g_ubuf, g_ibuf;
static WGPUBindGroup g_bg;
static WGPUTexture g_depth;
static WGPUSurfaceConfiguration g_sc;
static size_t g_ibufCap = 0;
static size_t g_drawCount = 0;
static int g_winW = 1360, g_winH = 860;

struct CbResult { void* p; };
static void onAdapter(WGPURequestAdapterStatus st, WGPUAdapter a, WGPUStringView, void* ud1, void*) {
    ((CbResult*)ud1)->p = (void*)a;
}
static void onDevice(WGPURequestDeviceStatus st, WGPUDevice d, WGPUStringView, void* ud1, void*) {
    ((CbResult*)ud1)->p = (void*)d;
}
// wgpu-native v25: WaitAnyOnly panics (unimplemented) — the working sync
// pattern is AllowProcessEvents + a ProcessEvents pump loop.
static void pumpUntil(bool* flag) {
    while (!*flag) wgpuInstanceProcessEvents(g_inst);
}

static void initGPU(HWND hwnd) {
    WGPUInstanceDescriptor id{}; g_inst = wgpuCreateInstance(&id);
    WGPUSurfaceSourceWindowsHWND src{};
    src.chain.sType = WGPUSType_SurfaceSourceWindowsHWND;
    src.hinstance = GetModuleHandle(NULL);
    src.hwnd = hwnd;
    WGPUSurfaceDescriptor sd{}; sd.nextInChain = (WGPUChainedStruct*)&src;
    g_surf = wgpuInstanceCreateSurface(g_inst, &sd);

    CbResult ra{};
    bool gotA = false;
    WGPURequestAdapterOptions ao{}; ao.compatibleSurface = g_surf;
    WGPURequestAdapterCallbackInfo aci{};
    aci.mode = WGPUCallbackMode_AllowProcessEvents;
    aci.callback = [](WGPURequestAdapterStatus st, WGPUAdapter a, WGPUStringView, void* ud1, void* ud2) {
        onAdapter(st, a, {}, ud1, ud2); *(bool*)ud2 = true;
    };
    aci.userdata1 = &ra; aci.userdata2 = &gotA;
    wgpuInstanceRequestAdapter(g_inst, &ao, aci);
    pumpUntil(&gotA);
    g_adapter = (WGPUAdapter)ra.p;
    if (!g_adapter) { fprintf(stderr, "no adapter\n"); exit(1); }

    CbResult rd{};
    bool gotD = false;
    WGPUDeviceDescriptor dd{};
    WGPURequestDeviceCallbackInfo dci{};
    dci.mode = WGPUCallbackMode_AllowProcessEvents;
    dci.callback = [](WGPURequestDeviceStatus st, WGPUDevice d, WGPUStringView, void* ud1, void* ud2) {
        onDevice(st, d, {}, ud1, ud2); *(bool*)ud2 = true;
    };
    dci.userdata1 = &rd; dci.userdata2 = &gotD;
    wgpuAdapterRequestDevice(g_adapter, &dd, dci);
    pumpUntil(&gotD);
    g_dev = (WGPUDevice)rd.p;
    if (!g_dev) { fprintf(stderr, "no device\n"); exit(1); }
    g_queue = wgpuDeviceGetQueue(g_dev);

    WGPUSurfaceCapabilities caps{};
    wgpuSurfaceGetCapabilities(g_surf, g_adapter, &caps);
    memset(&g_sc, 0, sizeof g_sc);
    g_sc.device = g_dev;
    g_sc.format = caps.formats[0];
    g_sc.usage = WGPUTextureUsage_RenderAttachment;
    g_sc.width = g_winW; g_sc.height = g_winH;
    g_sc.presentMode = WGPUPresentMode_Fifo;
    g_sc.alphaMode = WGPUCompositeAlphaMode_Auto;
    wgpuSurfaceConfigure(g_surf, &g_sc);
    wgpuSurfaceCapabilitiesFreeMembers(caps);
}

static void makePipeline(const std::string& wgsl) {
    WGPUShaderSourceWGSL srcw{};
    srcw.chain.sType = WGPUSType_ShaderSourceWGSL;
    srcw.code = { wgsl.data(), wgsl.size() };
    WGPUShaderModuleDescriptor smd{};
    smd.nextInChain = (WGPUChainedStruct*)&srcw;
    WGPUShaderModule mod = wgpuDeviceCreateShaderModule(g_dev, &smd);
    // NOTE: wgpuShaderModuleGetCompilationInfo is unimplemented in wgpu-native
    // v25 (panics) — validity is enforced by wgpu-py pre-checks in the harness
    // and by the null-pipeline guard below.

    WGPUVertexAttribute attrs[4] = {
        { nullptr, WGPUVertexFormat_Float32x3, 0, 0 },
        { nullptr, WGPUVertexFormat_Float32, 12, 1 },
        { nullptr, WGPUVertexFormat_Float32x4, 16, 2 },
        { nullptr, WGPUVertexFormat_Float32x3, 32, 3 },
    };
    WGPUVertexBufferLayout vbl{};
    vbl.arrayStride = 44; vbl.stepMode = WGPUVertexStepMode_Instance;
    vbl.attributeCount = 4; vbl.attributes = attrs;
    WGPUDepthStencilState ds{};
    ds.format = WGPUTextureFormat_Depth24Plus;
    ds.depthWriteEnabled = WGPUOptionalBool_True;
    ds.depthCompare = WGPUCompareFunction_Less;
    WGPUColorTargetState ct{}; ct.format = g_sc.format; ct.writeMask = WGPUColorWriteMask_All;
    WGPUFragmentState frag{}; frag.module = mod; frag.entryPoint = { "fs", 2 };
    frag.targetCount = 1; frag.targets = &ct;
    WGPURenderPipelineDescriptor pd{};
    pd.vertex.module = mod; pd.vertex.entryPoint = { "vs", 2 };
    pd.vertex.bufferCount = 1; pd.vertex.buffers = &vbl;
    pd.fragment = &frag;
    pd.primitive.topology = WGPUPrimitiveTopology_TriangleStrip;
    pd.primitive.cullMode = WGPUCullMode_None;
    pd.depthStencil = &ds;
    pd.multisample.count = 1; pd.multisample.mask = 0xFFFFFFFF;
    g_pipe = wgpuDeviceCreateRenderPipeline(g_dev, &pd);
    if (!g_pipe) { fprintf(stderr, "pipeline failed\n"); exit(1); }
    wgpuShaderModuleRelease(mod);

    WGPUBufferDescriptor ubd{};
    ubd.usage = WGPUBufferUsage_Uniform | WGPUBufferUsage_CopyDst;
    ubd.size = 160;
    g_ubuf = wgpuDeviceCreateBuffer(g_dev, &ubd);
    WGPUBindGroupEntry bge{};
    bge.binding = 0; bge.buffer = g_ubuf; bge.offset = 0; bge.size = 160;
    WGPUBindGroupDescriptor bgd{};
    bgd.layout = wgpuRenderPipelineGetBindGroupLayout(g_pipe, 0);
    bgd.entryCount = 1; bgd.entries = &bge;
    g_bg = wgpuDeviceCreateBindGroup(g_dev, &bgd);
}

// ------------------------------------------------------------- window -----
static HWND g_hwnd, g_gl, g_sb;
static bool g_drag = false;
static POINT g_last{ 0, 0 };
static float g_userAng = 0, g_userEl = 0, g_userZoom = 1.0f;

// -------------------------------------------------------- score bar -------
// Live scoreboard: re-read engine/score_ledger.json every ~2 s so new judge
// rounds appear in the window without a restart. Part 1 = scores + round,
// part 2 = the judge's current defect list.
static std::string g_scoreTitle;      // title-bar suffix, set by loadScores
static std::string g_scoreDir;        // exe dir, for locating the ledger
static void loadScores() {
    std::ifstream lf(g_scoreDir + "/../engine/score_ledger.json");
    if (!lf) return;
    json led = json::parse(lf, nullptr, false);
    if (led.is_discarded() || !led.contains("rounds") || led["rounds"].empty())
        return;
    auto& rounds = led["rounds"];
    auto& r = rounds.back();
    int P = (int)r.value("P", 0.0), V = (int)r.value("V", 0.0);
    std::string task = r.value("task", std::string("?"));
    char b[160];
    snprintf(b, sizeof b, "  P %d / V %d (%s)", P, V, task.c_str());
    g_scoreTitle = b;
    snprintf(b, sizeof b, "P %d / V %d  -  round %d: %s",
        P, V, (int)rounds.size(), task.c_str());
    std::string defs;
    if (r.contains("deficiencies"))
        for (auto& d : r["deficiencies"]) {
            if (!defs.empty()) defs += " | ";
            defs += d.get<std::string>();
            if (defs.size() > 220) { defs = defs.substr(0, 220) + "..."; break; }
        }
    if (g_sb) {
        SendMessageA(g_sb, SB_SETTEXTA, 0, (LPARAM)b);
        SendMessageA(g_sb, SB_SETTEXTA, 1, (LPARAM)defs.c_str());
    }
}

static void handleKey(WPARAM w) {
    if (w == VK_ESCAPE) { g_running = false; PostQuitMessage(0); }
    if (w == '1') httpPost(g_port, "/cmd", "wave");
    if (w == '2') httpPost(g_port, "/cmd", "walk");
    if (w == '3') httpPost(g_port, "/cmd", "rest");
}

// Render-host child window: the wgpu surface lives HERE, the status bar on
// the parent — a GPU surface and a GDI control must not share a client area
// (flicker/clipping). Mouse lives here; keys forward to the shared handler.
static LRESULT CALLBACK GlProc(HWND h, UINT msg, WPARAM w, LPARAM l) {
    switch (msg) {
    case WM_LBUTTONDOWN:
        g_drag = true; g_last = { (short)LOWORD(l), (short)HIWORD(l) };
        SetCapture(h); SetFocus(h);
        return 0;
    case WM_LBUTTONUP: g_drag = false; ReleaseCapture(); return 0;
    case WM_MOUSEMOVE:
        if (g_drag) {
            int x = (short)LOWORD(l), y = (short)HIWORD(l);
            g_userAng += (x - g_last.x) * 0.008f;
            g_userEl = (float)fmax(-1.2, fmin(1.2, g_userEl - (y - g_last.y) * 0.008));
            g_last = { x, y };
        }
        return 0;
    case WM_MOUSEWHEEL:
        g_userZoom = (float)fmax(0.2, fmin(8, g_userZoom * exp(GET_WHEEL_DELTA_WPARAM(w) * -0.001)));
        return 0;
    case WM_KEYDOWN: handleKey(w); return 0;
    }
    return DefWindowProc(h, msg, w, l);
}

static LRESULT CALLBACK WndProc(HWND h, UINT msg, WPARAM w, LPARAM l) {
    switch (msg) {
    case WM_DESTROY: g_running = false; PostQuitMessage(0); return 0;
    case WM_SIZE:
        if (g_sb && g_gl) {
            SendMessage(g_sb, WM_SIZE, 0, 0);      // status bar docks itself
            RECT rc; GetClientRect(h, &rc);
            RECT sr; GetWindowRect(g_sb, &sr);
            int sbh = sr.bottom - sr.top;
            g_winW = rc.right; g_winH = rc.bottom - sbh;
            if (g_winH < 1) g_winH = 1;
            MoveWindow(g_gl, 0, 0, g_winW, g_winH, TRUE);
            if (g_surf && g_winW > 0 && g_winH > 0) {
                g_sc.width = g_winW; g_sc.height = g_winH;
                wgpuSurfaceConfigure(g_surf, &g_sc);
                if (g_depth) { wgpuTextureRelease(g_depth); g_depth = nullptr; }
            }
        }
        return 0;
    case WM_KEYDOWN: handleKey(w); return 0;
    }
    return DefWindowProc(h, msg, w, l);
}

// ------------------------------------------------------------- render -----
static int g_lvl = -1;                // current shell level index
static float g_cx, g_cy, g_R, g_eyeY; // derived framing

static void deriveFraming() {
    // deriveTeddyFraming equivalent, from the coarsest shell level's bounds
    auto& L = g_levels[0];
    float x0 = 1e9f, x1 = -1e9f, y0 = 1e9f, y1 = -1e9f, z0 = 1e9f, z1 = -1e9f;
    for (int i = 0; i < L.n; i++) {
        float* d = L.inst.data() + (size_t)i * 11;
        x0 = fmin(x0, d[0]); x1 = fmax(x1, d[0]);
        y0 = fmin(y0, d[1]); y1 = fmax(y1, d[1]);
        z0 = fmin(z0, d[2]); z1 = fmax(z1, d[2]);
    }
    float bodyH = y1 - y0 + CELL, bodyW = fmax(x1 - x0 + CELL, z1 - z0 + CELL);
    double aspect = (double)g_winW / g_winH;
    double tV = tan(0.85 / 2), tH = tV * aspect;
    g_R = (float)fmax(bodyH / (2 * tV * 0.45), bodyW / (2 * tH * 0.45));
    g_cx = (x0 + x1) / 2; g_cy = (y0 + y1) / 2; g_eyeY = g_cy + bodyH * 0.3f;
}

static int pickLevel() {
    // the page's law, verbatim: finest level with cell >= spacing * 0.45
    double sp = lodSpacing(g_R * g_userZoom, g_winH);
    int best = 0;
    for (int i = 0; i < (int)g_levels.size(); i++)
        if (g_levels[i].cell >= sp * 0.45) best = i;
    return best;
}

static void rebuildInstances() {
    int li = pickLevel();
    auto& L = g_levels[li];
    double s0 = CELL;
    double bx, by, ground;
    { std::lock_guard<std::mutex> lk(g_sim.m);
      bx = g_sim.bodyX; by = g_sim.bodyY; ground = g_sim.ground; }
    // body splats (rigid bodyX/bodyY translation — pose binding is a
    // follow-up; the standing teddy reads correctly at rest)
    size_t nB = L.n;
    // ground ring march (page port, flat plane — terrain-wire is bearhill-only)
    std::vector<float> extra;
    double eyeD = g_R * g_userZoom;
    auto stepAt = [&](double d) { return lodSpacing(std::max(0.5, hypot(d, eyeD)), g_winH) * 2; };
    size_t budget = nB >> 2;
    double x0 = (bx - 48) * s0, x1 = (bx + 48) * s0, z1 = 26 * s0;
    double fadeEff = 1e-6;
    std::vector<std::array<double, 3>> pts;
    for (double r = stepAt(0) * 0.5; pts.size() < budget; r += stepAt(r)) {
        double sp = stepAt(r);
        int n = std::max(6, (int)llround(2 * 3.14159265358979 * r / sp));
        for (int k = 0; k < n && pts.size() < budget; k++) {
            double a = 2 * 3.14159265358979 * k / n;
            double x = bx * s0 + r * cos(a), z = r * sin(a);
            if (x < x0 || x > x1 || fabs(z) > z1) continue;
            pts.push_back({ x, z, sp });
        }
        fadeEff = r;
        if (r > 4 * eyeD) break;
    }
    for (auto& pt : pts) {
        double x = pt[0], z = pt[1], sp = pt[2];
        double y = ground * s0 - 0.012;
        double d = hypot(x - bx * s0, z);
        double fade = std::max(0.0, 1 - d / fadeEff);
        float k = (float)(0.30 * fade * (0.9 + 0.2 * hash01((int)llround(x * 997) + (int)llround(z * 613))));
        extra.insert(extra.end(), { (float)x, (float)y, (float)z, (float)(sp * 0.62),
                                    k, k * 0.97f, k * 0.85f, 1.0f, 0, 0, 0 });
    }
    size_t n = nB + pts.size();
    std::vector<float> all(n * 11);
    memcpy(all.data(), L.inst.data(), nB * 11 * sizeof(float));
    float ox = (float)(bx * s0), oy = (float)(by * s0);
    for (size_t i = 0; i < nB; i++) { all[i * 11] += ox; all[i * 11 + 1] += oy; }
    memcpy(all.data() + nB * 11, extra.data(), extra.size() * sizeof(float));

    if (n > g_ibufCap) {
        g_ibufCap = n * 2;
        if (g_ibuf) wgpuBufferRelease(g_ibuf);
        WGPUBufferDescriptor ibd{};
        ibd.usage = WGPUBufferUsage_Vertex | WGPUBufferUsage_CopyDst;
        ibd.size = g_ibufCap * 44;
        g_ibuf = wgpuDeviceCreateBuffer(g_dev, &ibd);
    }
    wgpuQueueWriteBuffer(g_queue, g_ibuf, 0, all.data(), n * 44);
    g_lvl = li;
    g_drawCount = n;
}

static double g_fps = 0;
static void render(double t) {
    if (!g_depth) {
        WGPUTextureDescriptor td{};
        td.dimension = WGPUTextureDimension_2D;
        td.size = { (uint32_t)g_winW, (uint32_t)g_winH, 1 };
        td.format = WGPUTextureFormat_Depth24Plus;
        td.mipLevelCount = 1; td.sampleCount = 1;
        td.usage = WGPUTextureUsage_RenderAttachment;
        g_depth = wgpuDeviceCreateTexture(g_dev, &td);
    }
    float u[40] = {};
    perspective(0.85f, (float)g_winW / g_winH, 0.05f, 50.0f, u);
    double ang = 0.6 + 0.10 * sin(t * 0.15) + g_userAng;
    double Ro = g_R * g_userZoom;
    double eye[3] = { g_cx + Ro * cos(g_userEl) * sin(ang),
                      g_eyeY + Ro * sin(g_userEl),
                      Ro * cos(g_userEl) * cos(ang) };
    lookAt((float)eye[0], (float)eye[1], (float)eye[2], g_cx, g_cy, 0, u + 16);
    u[32] = 1.0f;
    double lA = 3 * 3.14159265358979 / 4, lE = 3.14159265358979 / 4;
    u[36] = (float)(cos(lE) * sin(lA)); u[37] = (float)sin(lE); u[38] = (float)(cos(lE) * cos(lA));
    wgpuQueueWriteBuffer(g_queue, g_ubuf, 0, u, sizeof u);

    WGPUSurfaceTexture st{};
    wgpuSurfaceGetCurrentTexture(g_surf, &st);
    if (st.status != WGPUSurfaceGetCurrentTextureStatus_SuccessOptimal &&
        st.status != WGPUSurfaceGetCurrentTextureStatus_SuccessSuboptimal) {
        wgpuSurfaceConfigure(g_surf, &g_sc);
        return;
    }
    WGPUTextureView tv = wgpuTextureCreateView(st.texture, nullptr);
    WGPUTextureView dv = wgpuTextureCreateView(g_depth, nullptr);
    WGPURenderPassColorAttachment ca{};
    ca.view = tv; ca.loadOp = WGPULoadOp_Clear; ca.storeOp = WGPUStoreOp_Store;
    ca.clearValue = { 0.027, 0.031, 0.047, 1 };
    ca.depthSlice = WGPU_DEPTH_SLICE_UNDEFINED;
    WGPURenderPassDepthStencilAttachment dsa{};
    dsa.view = dv; dsa.depthLoadOp = WGPULoadOp_Clear; dsa.depthStoreOp = WGPUStoreOp_Store;
    dsa.depthClearValue = 1.0f;
    WGPURenderPassDescriptor rp{}; rp.colorAttachmentCount = 1; rp.colorAttachments = &ca;
    rp.depthStencilAttachment = &dsa;
    WGPUCommandEncoder enc = wgpuDeviceCreateCommandEncoder(g_dev, nullptr);
    WGPURenderPassEncoder pass = wgpuCommandEncoderBeginRenderPass(enc, &rp);
    wgpuRenderPassEncoderSetPipeline(pass, g_pipe);
    wgpuRenderPassEncoderSetBindGroup(pass, 0, g_bg, 0, nullptr);
    wgpuRenderPassEncoderSetVertexBuffer(pass, 0, g_ibuf, 0, WGPU_WHOLE_SIZE);
    wgpuRenderPassEncoderDraw(pass, 4, (uint32_t)g_drawCount, 0, 0);
    wgpuRenderPassEncoderEnd(pass);
    wgpuRenderPassEncoderRelease(pass);
    WGPUCommandBuffer cmd = wgpuCommandEncoderFinish(enc, nullptr);
    wgpuCommandEncoderRelease(enc);
    wgpuQueueSubmit(g_queue, 1, &cmd);
    wgpuCommandBufferRelease(cmd);
    wgpuSurfacePresent(g_surf);
    wgpuTextureViewRelease(tv); wgpuTextureViewRelease(dv);
    wgpuTextureRelease(st.texture);
}

// --------------------------------------------------------------- main -----
int main(int argc, char** argv) {
    if (argc > 1) g_port = atoi(argv[1]);
    std::string shellPath = argc > 2 ? argv[2] : "genomes/teddy_stand_shell.json";

    char exeDir[MAX_PATH];
    GetModuleFileNameA(NULL, exeDir, MAX_PATH);
    std::string dir = exeDir; dir = dir.substr(0, dir.find_last_of("\\/"));
    SetCurrentDirectoryA(dir.c_str());

    WSADATA wd; WSAStartup(MAKEWORD(2, 2), &wd);
    loadShell(shellPath);
    std::string wgsl = loadWGSL(dir + "/../engine/spiace_native.html");
    CELL = 0.06f;

    // The EXE is the whole engine entry point: if the relay isn't serving,
    // start it (sim core spawns lazily on the first stream connection).
    if (httpGet(g_port, "/scoreboard").empty()) {
        STARTUPINFOA si{}; si.cb = sizeof si;
        PROCESS_INFORMATION pi{};
        std::string cmd = "cmd /c start /min python relay.py 30 " +
            std::to_string(g_port) + " genomes\\teddystandmuscle.chimera";
        CreateProcessA(NULL, cmd.data(), NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi);
        for (int i = 0; i < 100 && httpGet(g_port, "/scoreboard").empty(); i++)
            Sleep(100);
    }

    // scores: read the ledger file directly (the ledger is the live truth),
    // then keep re-reading it every 2 s from the main loop
    g_scoreDir = dir;
    loadScores();

    SetProcessDPIAware();
    INITCOMMONCONTROLSEX icc{ sizeof icc, ICC_BAR_CLASSES };
    InitCommonControlsEx(&icc);
    HINSTANCE hInst = GetModuleHandle(NULL);
    WNDCLASSA wc{}; wc.lpfnWndProc = WndProc; wc.hInstance = hInst;
    wc.lpszClassName = "SpiaceViewer"; wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    RegisterClassA(&wc);
    WNDCLASSA glc{}; glc.lpfnWndProc = GlProc; glc.hInstance = hInst;
    glc.lpszClassName = "SpiaceGL"; glc.hCursor = LoadCursor(NULL, IDC_ARROW);
    RegisterClassA(&glc);
    g_hwnd = CreateWindowExA(0, "SpiaceViewer", "SPIACE native",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE, CW_USEDEFAULT, CW_USEDEFAULT,
        g_winW, g_winH, NULL, NULL, hInst, NULL);

    // status bar: [ scores + round | judge defect list ]
    g_sb = CreateWindowExA(0, STATUSCLASSNAMEA, "",
        WS_CHILD | WS_VISIBLE | SBARS_SIZEGRIP,
        0, 0, 0, 0, g_hwnd, NULL, hInst, NULL);
    int parts[2] = { 300, -1 };
    SendMessageA(g_sb, SB_SETPARTS, 2, (LPARAM)parts);

    // render-host child gets the client area above the status bar
    SendMessage(g_sb, WM_SIZE, 0, 0);
    RECT rc; GetClientRect(g_hwnd, &rc);
    RECT sr; GetWindowRect(g_sb, &sr);
    g_winW = rc.right; g_winH = rc.bottom - (sr.bottom - sr.top);
    if (g_winH < 1) g_winH = 1;
    g_gl = CreateWindowExA(0, "SpiaceGL", "", WS_CHILD | WS_VISIBLE,
        0, 0, g_winW, g_winH, g_hwnd, NULL, hInst, NULL);
    loadScores();   // now that g_sb exists, fill the bar

    initGPU(g_gl);
    makePipeline(wgsl);
    deriveFraming();
    std::thread(streamThread, g_port).detach();

    printf("viewer up — streaming from relay :%d\n", g_port);
    MSG msg;
    auto t0 = GetTickCount64();
    int frames = 0; ULONGLONG fpsT = t0;
    uint64_t lastSeq = UINT64_MAX; int lastLvl = -1;
    while (g_running) {
        while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) { g_running = false; break; }
            TranslateMessage(&msg); DispatchMessage(&msg);
        }
        if (!g_running) break;
        uint64_t seq; { std::lock_guard<std::mutex> lk(g_sim.m); seq = g_sim.animSeq; }
        int lvl = pickLevel();
        if (seq != lastSeq || lvl != lastLvl || g_drawCount == 0) {
            rebuildInstances();
            lastSeq = seq; lastLvl = lvl;
        }
        double t = (GetTickCount64() - t0) / 1000.0;
        render(t);
        frames++;
        ULONGLONG now = GetTickCount64();
        if (now - fpsT > 1000) {
            g_fps = frames * 1000.0 / (now - fpsT); frames = 0; fpsT = now;
            std::string genome; { std::lock_guard<std::mutex> lk(g_sim.m); genome = g_sim.genome; }
            char title[256];
            snprintf(title, sizeof title, "SPIACE native - %s - %.0f fps - %d splats%s",
                genome.c_str(), g_fps, (int)g_drawCount, g_scoreTitle.c_str());
            SetWindowTextA(g_hwnd, title);
        }
        static ULONGLONG scoreT = 0;
        if (now - scoreT > 2000) { scoreT = now; loadScores(); }
        wgpuInstanceProcessEvents(g_inst);
    }
    WSACleanup();
    return 0;
}
