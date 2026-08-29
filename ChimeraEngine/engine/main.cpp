// main.cpp — Bootstrap + Main Loop
// Initializes Engine, Physics; runs the simulation loop with GPU rendering.
// Also serves /frame (PNG of the current render) and /membrane (load a story membrane
// scene into the Vulkan renderer) so the engine is the emission target the dyad points at.
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include "engine.hpp"
#include "physics.hpp"
#include "shared_mem.hpp"
#include "http_server.hpp"
#include "png_encoder.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cctype>
#include <chrono>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <string>
#include <algorithm>

static Engine* g_engine = nullptr;
static Physics g_physics;
static SharedRing g_ring("ChimeraPhysicsRing");

// ── Pending membrane request (Vulkan work must stay on the main/render thread) ───────
struct MembraneRequest {
    std::string term;
    std::vector<float> pos;      // 7 floats per particle: x,y,z,r,g,b,size
    uint32_t count = 0;
    float cam_radius = 12.0f;
    float cam_theta  = 0.0f;
    float cam_phi    = 0.3f;
    bool camera_only = false;    // true: only move the camera, keep the loaded membrane
    bool valid = false;
};
static MembraneRequest g_mem_req;
static std::mutex g_mem_mutex;
static std::condition_variable g_mem_cv;
static bool g_mem_pending = false;
static bool g_mem_applied = false;
static bool g_membrane_active = true;  // 3DGS-only: the N-body sim (7-float) is retired

// ── Pending triangle mesh request (same handoff: Vulkan work stays on the render thread) ──
struct MeshReq { std::vector<float> verts; std::vector<uint32_t> indices; uint32_t N=0, idxCount=0; float cam_radius=12.f, cam_theta=0.f, cam_phi=0.3f; uint32_t slot=0, mode=0; bool valid=false; };
static MeshReq g_mesh_req;
static std::mutex g_mesh_mutex;
static std::condition_variable g_mesh_cv;
static bool g_mesh_pending = false, g_mesh_applied = false;

// ── Pending skin/pose request (same handoff: Vulkan work stays on the render thread) ────
struct SkinRequest {
    int kind = 0;                    // 1 = skin_bin load, 2 = pose_store, 3 = pose_apply
    std::vector<float> rest;         // kind 1: N*14 rest splat
    std::vector<float> weights;      // kind 1: N*4 [bone0, w0, bone1, w1]
    std::vector<float> pose;         // kind 2: B*7 [qw,qx,qy,qz, tx,ty,tz] per bone
    uint32_t n = 0, bones = 0, slot = 0;
    float cam_radius = 2.2f;
    float cam_theta  = 0.0f;
    float cam_phi    = 0.15f;
    bool ok = false;                 // result of the engine call
};
static SkinRequest g_skin_req;
static std::mutex g_skin_mutex;
static std::condition_variable g_skin_cv;
static bool g_skin_pending = false;
static bool g_skin_applied = false;

// ── Minimal JSON helpers (no external deps) ───────────────────────────────────────
static std::string fmt_float(float f) {
    char buf[32];
    if (f == static_cast<float>(static_cast<int>(f)))
        sprintf(buf, "%d", static_cast<int>(f));
    else
        sprintf(buf, "%.6g", f);
    return std::string(buf);
}

static size_t find_colon_after(const std::string& body, const char* key) {
    std::string needle = std::string("\"") + key + "\"";
    size_t pos = body.find(needle);
    if (pos == std::string::npos) return std::string::npos;
    size_t after_key = pos + needle.size();
    while (after_key < body.size() && (body[after_key] == ' ' || body[after_key] == '\t')) ++after_key;
    if (after_key >= body.size() || body[after_key] != ':') return std::string::npos;
    return after_key + 1;
}

static float get_float(const std::string& body, const char* key, float def) {
    size_t p = find_colon_after(body, key);
    if (p == std::string::npos) return def;
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    try { return std::stof(body.substr(p)); } catch (...) { return def; }
}

static uint32_t get_uint(const std::string& body, const char* key, uint32_t def) {
    size_t p = find_colon_after(body, key);
    if (p == std::string::npos) return def;
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    try { return static_cast<uint32_t>(std::stoul(body.substr(p))); } catch (...) { return def; }
}

static std::string get_string(const std::string& body, const char* key) {
    std::string needle = std::string("\"") + key + "\"";
    size_t pos = body.find(needle);
    if (pos == std::string::npos) return "";
    size_t p = pos + needle.size();
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (p >= body.size() || body[p] != ':') return "";
    p++; while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (p >= body.size() || body[p] != '"') return "";
    p++;
    size_t start = p;
    while (p < body.size() && body[p] != '"') ++p;
    return body.substr(start, p - start);
}

static bool parse_float_array(const std::string& body, const char* key, std::vector<float>& out) {
    std::string needle = std::string("\"") + key + "\"";
    size_t pos = body.find(needle);
    if (pos == std::string::npos) return false;
    size_t p = pos + needle.size();
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (p >= body.size() || body[p] != ':') return false;
    p++; while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (p >= body.size() || body[p] != '[') return false;
    p++;
    out.clear();
    while (p < body.size() && body[p] != ']') {
        char c = body[p];
        if (c == ',' || c == ' ' || c == '\t' || c == '\n' || c == '\r') { p++; continue; }
        size_t start = p;
        while (p < body.size() && (std::isdigit(static_cast<unsigned char>(body[p])) ||
               body[p] == '-' || body[p] == '+' || body[p] == '.' || body[p] == 'e' || body[p] == 'E')) ++p;
        if (p == start) { p++; continue; }
        try { out.push_back(std::stof(body.substr(start, p - start))); } catch (...) { /* skip */ }
    }
    return !out.empty();
}

// Signal handler for graceful shutdown
#ifdef _WIN32
BOOL WINAPI handleCtrlC(DWORD) { return TRUE; }
#else
void handleSignal(int) { exit(0); }
#endif

int main(int argc, char** argv) {
    // Config
    EngineConfig cfg;
    cfg.width  = 1920;
    cfg.height = 1080;
    cfg.n_particles = 1200;
    cfg.G      = 1.0f;
    cfg.dt     = 0.02f;

    // HTTP port: argv[1] overrides the default 8080 (e.g. NVIDIA SDK Manager squats 8080).
    int http_port = 8080;
    if (argc > 1) { http_port = atoi(argv[1]); if (http_port <= 0) http_port = 8080; }

    // Physics init (passes cfg so it can set physical params)
    g_physics.init(cfg.n_particles, cfg);

    // Engine init (creates Win32 window + Vulkan)
    Engine engine;
    if (!engine.init(cfg)) {
        fprintf(stderr, "Failed to initialize Vulkan engine\n");
        return 1;
    }
    g_engine = &engine;

    // ── HTTP server for Python shim communication ───────────────────────────────
    HttpServer server;
    bool http_ok = server.start(http_port, [&](const std::string& method, const std::string& path,
                                          const std::string& req_body, std::string& body, std::string& content_type) {
        // strip query string
        size_t q = path.find('?');
        std::string p = (q == std::string::npos) ? path : path.substr(0, q);

        if (p == "/state" && method == "GET") {
            auto& parts = g_physics.particles();
            std::string json; json.reserve(200u * parts.size() + 64);
            json += "{\"n\":" + std::to_string(parts.size()) + ",\"particles\":[";
            for (size_t i = 0; i < parts.size(); ++i) {
                if (i) json += ',';
                json += '['
                    + fmt_float(parts[i].x)   + ',' + fmt_float(parts[i].y)   + ',' + fmt_float(parts[i].z)
                    + ',' + fmt_float(parts[i].vx)  + ',' + fmt_float(parts[i].vy)  + ',' + fmt_float(parts[i].vz)
                    + ',' + fmt_float(parts[i].cr)  + ',' + fmt_float(parts[i].cg)  + ',' + fmt_float(parts[i].cb)
                    + ',' + fmt_float(parts[i].size)
                    + ']';
            }
            json += ']}';
            body = std::move(json);
            content_type = "application/json";
        } else if (p == "/control" && method == "POST") {
            float G      = get_float(req_body, "G",           cfg.G);
            float rw     = get_float(req_body, "rw",          cfg.rw);
            float rb     = get_float(req_body, "rb",          cfg.rb);
            float rc     = get_float(req_body, "rc",          cfg.rc);
            float kw     = get_float(req_body, "kw",          cfg.kw);
            float kb     = get_float(req_body, "kb",          cfg.kb);
            float gamma_w= get_float(req_body, "gamma_w",     cfg.gamma_w);
            float dt     = get_float(req_body, "dt",          cfg.dt);

            g_physics.set_params(G, rw, rb, rc, kw, kb, gamma_w, dt);
            if (g_engine) g_engine->mark_dirty();
            body = "{\"ok\":true}";
            content_type = "application/json";
        } else if (p == "/membrane" && method == "POST") {
            std::string term = get_string(req_body, "term");
            uint32_t count = get_uint(req_body, "count", 0);
            std::vector<float> pos;
            parse_float_array(req_body, "particles", pos);
            float cam_radius = get_float(req_body, "cam_radius", 12.0f);
            float cam_theta  = get_float(req_body, "cam_theta", 0.0f);
            float cam_phi    = get_float(req_body, "cam_phi", 0.3f);

            if (term.empty() || pos.empty()) {
                body = "{\"ok\":false,\"error\":\"bad request\"}";
            } else {
                {
                    std::lock_guard<std::mutex> lk(g_mem_mutex);
                    g_mem_req.term = term;
                    g_mem_req.pos = std::move(pos);
                    g_mem_req.count = count ? count : static_cast<uint32_t>(g_mem_req.pos.size() / 7);
                    g_mem_req.cam_radius = cam_radius;
                    g_mem_req.cam_theta  = cam_theta;
                    g_mem_req.cam_phi    = cam_phi;
                    g_mem_req.valid = true;
                    g_mem_pending = true;
                    g_mem_applied = false;
                }
            std::unique_lock<std::mutex> lk(g_mem_mutex);
            bool ok = g_mem_cv.wait_for(lk, std::chrono::seconds(3), []{ return g_mem_applied; });
            body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
            }
            content_type = "application/json";
        } else if (p == "/membrane_bin" && method == "POST") {
            // Binary protocol (application/octet-stream), little-endian:
            //   [u32 count][f32 cam_radius][f32 cam_theta][f32 cam_phi][f32 * count * 14]
            // 14 floats per splat: x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz. No JSON: raw float32.
            if (req_body.size() < 16) {
                body = "{\"ok\":false,\"error\":\"short header\"}";
            } else {
                uint32_t count = 0; float cr = 12.0f, ct = 0.0f, cp = 0.3f;
                std::memcpy(&count, req_body.data() + 0, 4);
                std::memcpy(&cr,    req_body.data() + 4, 4);
                std::memcpy(&ct,    req_body.data() + 8, 4);
                std::memcpy(&cp,    req_body.data() + 12, 4);
                size_t expect = 16 + static_cast<size_t>(count) * 14 * 4;
                if (req_body.size() != expect) {
                    body = "{\"ok\":false,\"error\":\"size mismatch\"}";
                } else {
                    std::vector<float> pos(count * 14);
                    std::memcpy(pos.data(), req_body.data() + 16, count * 14 * 4);
                    {
                        std::lock_guard<std::mutex> lk(g_mem_mutex);
                        g_mem_req.term = "theTeddy";
                        g_mem_req.pos = std::move(pos);
                        g_mem_req.count = count;
                        g_mem_req.cam_radius = cr;
                        g_mem_req.cam_theta  = ct;
                        g_mem_req.cam_phi    = cp;
                        g_mem_req.camera_only = false;
                        g_mem_req.valid = true;
                        g_mem_pending = true;
                        g_mem_applied = false;
                    }
                    std::unique_lock<std::mutex> lk(g_mem_mutex);
                    bool ok = g_mem_cv.wait_for(lk, std::chrono::seconds(15), []{ return g_mem_applied; });
                    body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/mesh_bin" && method == "POST") {
            // Binary protocol (application/octet-stream), little-endian:
            //   [u32 N][u32 idxCount][f32 cam_radius][f32 cam_theta][f32 cam_phi][f32 slotmode]
            //   [f32 * N * 9  vertices: pos3, normal3, color3]
            //   [u32 * idxCount  triangle indices]
            // slotmode = slot*10 + mode: slot 0 = main mesh, 1 = overlay;
            // mode 0 = fill, 1 = wireframe (1px GPU line edges), 2 = fill + wire.
            if (req_body.size() < 24) {
                body = "{\"ok\":false,\"error\":\"short header\"}";
            } else {
                uint32_t N = 0, idxCount = 0; float cr = 12.0f, ct = 0.0f, cp = 0.3f, slotmode = 0.0f;
                std::memcpy(&N, req_body.data() + 0, 4);
                std::memcpy(&idxCount, req_body.data() + 4, 4);
                std::memcpy(&cr, req_body.data() + 8, 4);
                std::memcpy(&ct, req_body.data() + 12, 4);
                std::memcpy(&cp, req_body.data() + 16, 4);
                std::memcpy(&slotmode, req_body.data() + 20, 4);
                size_t expect = 24 + static_cast<size_t>(N) * 9 * 4 + static_cast<size_t>(idxCount) * 4;
                if (req_body.size() != expect) {
                    body = "{\"ok\":false,\"error\":\"size mismatch\"}";
                } else {
                    std::vector<float> verts(static_cast<size_t>(N) * 9);
                    std::vector<uint32_t> indices(idxCount);
                    std::memcpy(verts.data(), req_body.data() + 24, static_cast<size_t>(N) * 9 * 4);
                    std::memcpy(indices.data(), req_body.data() + 24 + static_cast<size_t>(N) * 9 * 4, static_cast<size_t>(idxCount) * 4);
                    {
                        std::lock_guard<std::mutex> lk(g_mesh_mutex);
                        g_mesh_req.verts = std::move(verts);
                        g_mesh_req.indices = std::move(indices);
                        g_mesh_req.N = N;
                        g_mesh_req.idxCount = idxCount;
                        g_mesh_req.cam_radius = cr; g_mesh_req.cam_theta = ct; g_mesh_req.cam_phi = cp;
                        uint32_t sm = static_cast<uint32_t>(slotmode < 0 ? 0 : slotmode + 0.5f);
                        g_mesh_req.slot = sm / 10; g_mesh_req.mode = sm % 10;
                        g_mesh_pending = true; g_mesh_applied = false;
                    }
                    std::unique_lock<std::mutex> lk(g_mesh_mutex);
                    bool ok = g_mesh_cv.wait_for(lk, std::chrono::seconds(15), []{ return g_mesh_applied; });
                    body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/skin_bin" && method == "POST") {
            // Binary protocol (application/octet-stream), little-endian:
            //   [u32 N][u32 B][f32 cam_radius][f32 cam_theta][f32 cam_phi]
            //   [f32 * N * 14 rest splat][f32 * N * 4 weights: bone0, w0, bone1, w1]
            if (req_body.size() < 20) {
                body = "{\"ok\":false,\"error\":\"short header\"}";
            } else {
                uint32_t n = 0, nb = 0; float cr = 2.2f, ct = 0.0f, cp = 0.15f;
                std::memcpy(&n,  req_body.data() + 0,  4);
                std::memcpy(&nb, req_body.data() + 4,  4);
                std::memcpy(&cr, req_body.data() + 8,  4);
                std::memcpy(&ct, req_body.data() + 12, 4);
                std::memcpy(&cp, req_body.data() + 16, 4);
                size_t expect = 20 + static_cast<size_t>(n) * 14 * 4 + static_cast<size_t>(n) * 4 * 4;
                if (req_body.size() != expect) {
                    body = "{\"ok\":false,\"error\":\"size mismatch\"}";
                } else {
                    std::vector<float> rest(static_cast<size_t>(n) * 14);
                    std::vector<float> wts(static_cast<size_t>(n) * 4);
                    std::memcpy(rest.data(), req_body.data() + 20, rest.size() * 4);
                    std::memcpy(wts.data(),  req_body.data() + 20 + rest.size() * 4, wts.size() * 4);
                    {
                        std::lock_guard<std::mutex> lk(g_skin_mutex);
                        g_skin_req.kind = 1;
                        g_skin_req.rest = std::move(rest);
                        g_skin_req.weights = std::move(wts);
                        g_skin_req.n = n;
                        g_skin_req.bones = nb;
                        g_skin_req.cam_radius = cr;
                        g_skin_req.cam_theta  = ct;
                        g_skin_req.cam_phi    = cp;
                        g_skin_pending = true;
                        g_skin_applied = false;
                    }
                    std::unique_lock<std::mutex> lk(g_skin_mutex);
                    bool ok = g_skin_cv.wait_for(lk, std::chrono::seconds(15), []{ return g_skin_applied; });
                    body = (ok && g_skin_req.ok) ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"apply failed or timeout\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/pose_store" && method == "POST") {
            // Binary protocol: [u32 slot][u32 B][f32 * B * 7] — per bone [qw,qx,qy,qz, tx,ty,tz]
            if (req_body.size() < 8) {
                body = "{\"ok\":false,\"error\":\"short header\"}";
            } else {
                uint32_t slot = 0, nb = 0;
                std::memcpy(&slot, req_body.data() + 0, 4);
                std::memcpy(&nb,   req_body.data() + 4, 4);
                size_t expect = 8 + static_cast<size_t>(nb) * 7 * 4;
                if (req_body.size() != expect) {
                    body = "{\"ok\":false,\"error\":\"size mismatch\"}";
                } else {
                    std::vector<float> pose(static_cast<size_t>(nb) * 7);
                    std::memcpy(pose.data(), req_body.data() + 8, pose.size() * 4);
                    {
                        std::lock_guard<std::mutex> lk(g_skin_mutex);
                        g_skin_req.kind = 2;
                        g_skin_req.slot = slot;
                        g_skin_req.pose = std::move(pose);
                        g_skin_pending = true;
                        g_skin_applied = false;
                    }
                    std::unique_lock<std::mutex> lk(g_skin_mutex);
                    bool ok = g_skin_cv.wait_for(lk, std::chrono::seconds(5), []{ return g_skin_applied; });
                    body = (ok && g_skin_req.ok) ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"store failed or timeout\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/pose_apply" && method == "POST") {
            // Binary protocol: [u32 slot] — copy the stored slot into pose_buf_, pose next frame
            if (req_body.size() < 4) {
                body = "{\"ok\":false,\"error\":\"short header\"}";
            } else {
                uint32_t slot = 0;
                std::memcpy(&slot, req_body.data() + 0, 4);
                {
                    std::lock_guard<std::mutex> lk(g_skin_mutex);
                    g_skin_req.kind = 3;
                    g_skin_req.slot = slot;
                    g_skin_pending = true;
                    g_skin_applied = false;
                }
                std::unique_lock<std::mutex> lk(g_skin_mutex);
                bool ok = g_skin_cv.wait_for(lk, std::chrono::seconds(5), []{ return g_skin_applied; });
                body = (ok && g_skin_req.ok) ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"apply failed or timeout\"}";
            }
            content_type = "application/json";
        } else if (p == "/camera" && method == "POST") {
            float cam_radius = get_float(req_body, "cam_radius", 12.0f);
            float cam_theta  = get_float(req_body, "cam_theta", 0.0f);
            float cam_phi    = get_float(req_body, "cam_phi", 0.3f);
            {
                std::lock_guard<std::mutex> lk(g_mem_mutex);
                g_mem_req.cam_radius = cam_radius;
                g_mem_req.cam_theta  = cam_theta;
                g_mem_req.cam_phi    = cam_phi;
                g_mem_req.camera_only = true;
                g_mem_req.valid = true;
                g_mem_pending = true;
                g_mem_applied = false;
            }
            std::unique_lock<std::mutex> lk(g_mem_mutex);
            bool ok = g_mem_cv.wait_for(lk, std::chrono::seconds(3), []{ return g_mem_applied; });
            body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
            content_type = "application/json";
        } else if ((p == "/frame" || p == "/stream") && method == "GET") {
            if (g_engine) {
                g_engine->request_capture();
                auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(3);
                while (!g_engine->capture_ready()) {
                    if (std::chrono::steady_clock::now() > deadline) { body = "{\"ok\":false,\"error\":\"capture timeout\"}"; break; }
                    Sleep(5);
                }
                if (g_engine->capture_ready()) {
                    std::vector<uint8_t> rgba; uint32_t w = 0, h = 0;
                    if (g_engine->capture_frame(rgba, w, h)) {
                        std::vector<uint8_t> encoded = png::encode_rgba(rgba.data(), w, h);
                        body.assign(reinterpret_cast<const char*>(encoded.data()), encoded.size());
                        content_type = "image/png";
                    } else {
                        body = "{\"ok\":false,\"error\":\"no frame\"}";
                        content_type = "application/json";
                    }
                } else {
                    content_type = "application/json";
                }
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
                content_type = "application/json";
            }
        } else if (p == "/debug" && method == "GET") {
            body = "{\"n\":" + std::to_string(g_engine ? g_engine->particle_count() : 0)
                 + ",\"active\":" + (g_membrane_active ? "true" : "false") + "}";
            content_type = "application/json";
        } else {
            body = "Not found";
        }
    });
    if (!http_ok) {
        fprintf(stderr, "Warning: Failed to start HTTP server on port %d\n", http_port);
    }

    printf("Chimera Engine running at http://localhost:%d/state\n", http_port);
    printf("  /frame  -> PNG of the current render (membrane if one is loaded)\n");
    printf("  /membrane (POST) -> load a story membrane scene\n");
    printf("Window: %ux%u, Press Ctrl+C to stop.\n", cfg.width, cfg.height);
    printf("Controls: Left-drag orbit | Scroll zoom | Right-drag pan\n");
    printf("          WASD move | Q/E up-down | Space/Ctrl zoom | R reset | P pose toggle\n");

#ifdef _WIN32
    SetConsoleCtrlHandler(handleCtrlC, TRUE);
#else
    signal(SIGINT, handleSignal);
    signal(SIGTERM, handleSignal);
#endif

    // Main loop — hybrid GPU compute / CPU integrate (or membrane display)
    auto last_time = std::chrono::high_resolution_clock::now();
    int frame_count = 0;
    bool use_compute = false;  // compute path disabled: the N-body sim is a placeholder; the membrane/teddy render is the target

    while (true) {
        // Process Windows messages (allows window to close gracefully).
        // Drain the WHOLE queue per iteration: one-message-per-frame starves input
        // whenever the frame rate drops (animation driver re-posting meshes at ~12 fps
        // made orbit/zoom feel dead — the queue filled faster than it was pumped).
        MSG msg;
        bool quit = false;
        while (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT || msg.message == WM_CLOSE) { quit = true; break; }
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
        if (quit) break;

        // Apply a pending membrane request (Vulkan work must stay on this thread)
        {
            std::lock_guard<std::mutex> lk(g_mem_mutex);
            if (g_mem_pending && g_mem_req.valid) {
                if (g_mem_req.camera_only) {
                    engine.set_camera(g_mem_req.cam_radius, g_mem_req.cam_theta, g_mem_req.cam_phi);
                } else {
                    engine.load_membrane(g_mem_req.term, g_mem_req.pos, g_mem_req.count);
                    engine.set_camera(g_mem_req.cam_radius, g_mem_req.cam_theta, g_mem_req.cam_phi);
                    g_membrane_active = true;
                }
                g_mem_req.camera_only = false;
                g_mem_pending = false;
                g_mem_applied = true;
                g_mem_cv.notify_all();
            }
        }

        // Apply a pending mesh request (Vulkan work must stay on this thread)
        {
            std::lock_guard<std::mutex> lk(g_mesh_mutex);
            if (g_mesh_pending) {
                if (g_mesh_req.slot == 1) {
                    engine.load_overlay(g_mesh_req.verts, g_mesh_req.indices, g_mesh_req.N, g_mesh_req.idxCount);
                } else {
                    engine.load_mesh(g_mesh_req.verts, g_mesh_req.indices, g_mesh_req.N, g_mesh_req.idxCount);
                    engine.set_mesh_mode(g_mesh_req.mode);
                }
                // cam_radius <= 0 = "keep the current camera": animation drivers stream
                // meshes every frame and must NOT steal the operator's orbit/zoom/pan.
                if (g_mesh_req.cam_radius > 0.0f)
                    engine.set_camera(g_mesh_req.cam_radius, g_mesh_req.cam_theta, g_mesh_req.cam_phi);
                g_mesh_pending = false; g_mesh_applied = true; g_mesh_cv.notify_all();
            }
        }

        // Apply a pending skin/pose request (Vulkan work must stay on this thread)
        {
            std::lock_guard<std::mutex> lk(g_skin_mutex);
            if (g_skin_pending) {
                bool ok = false;
                if (g_skin_req.kind == 1) {
                    ok = engine.load_skinned(g_skin_req.rest, g_skin_req.weights,
                                             g_skin_req.n, g_skin_req.bones);
                    if (ok) {
                        engine.set_camera(g_skin_req.cam_radius, g_skin_req.cam_theta,
                                          g_skin_req.cam_phi);
                        g_membrane_active = true;
                    }
                } else if (g_skin_req.kind == 2) {
                    ok = engine.store_pose(g_skin_req.slot, g_skin_req.pose);
                } else if (g_skin_req.kind == 3) {
                    ok = engine.apply_pose(g_skin_req.slot);
                }
                g_skin_req.ok = ok;
                g_skin_pending = false;
                g_skin_applied = true;
                g_skin_cv.notify_all();
            }
        }

        // Run the N-body simulation only when no membrane is loaded
        if (!g_membrane_active) {
            auto& particles = g_physics.particles();
            uint32_t count = static_cast<uint32_t>(particles.size());

            // Build position buffer for GPU upload: [x,y,z, r,g,b, size] per particle
            std::vector<float> pos_buf(count * 7, 0.f);
            // Build velocity buffer for GPU compute input: [vx,vy,vz, 0] per particle
            std::vector<float> vel_buf(count * 4, 0.f);
            for (uint32_t i = 0; i < count; ++i) {
                const auto& p = particles[i];
                pos_buf[i*7+0] = p.x;     pos_buf[i*7+1] = p.y;     pos_buf[i*7+2] = p.z;
                pos_buf[i*7+3] = p.cr;    pos_buf[i*7+4] = p.cg;    pos_buf[i*7+5] = p.cb;
                pos_buf[i*7+6] = p.size;
                vel_buf[i*4+0] = p.vx;    vel_buf[i*4+1] = p.vy;    vel_buf[i*4+2] = p.vz;
                vel_buf[i*4+3] = 0.0f;
            }

            if (!engine.push_state(pos_buf, vel_buf, count)) {
                fprintf(stderr, "Failed to push state to GPU\n");
                break;
            }

            // GPU compute dispatch: reads pos/vel, writes new velocities to acc buffer
            std::vector<float> readback_vels;
            if (use_compute && !engine.dispatch_compute(readback_vels)) {
                fprintf(stderr, "Compute dispatch failed — falling back to CPU-only\n");
                use_compute = false;
            }

            if (use_compute && !readback_vels.empty()) {
                for (uint32_t i = 0; i < count; ++i) {
                    particles[i].vx = readback_vels[i*4+0];
                    particles[i].vy = readback_vels[i*4+1];
                    particles[i].vz = readback_vels[i*4+2];
                }
            }

            // CPU integrate positions (semi-implicit Euler — velocities already include acceleration)
            for (auto& p : particles) {
                p.x += p.vx * cfg.dt;
                p.y += p.vy * cfg.dt;
                p.z += p.vz * cfg.dt;
            }
        }

        // Render one frame
        if (!engine.frame()) {
            fprintf(stderr, "Frame failed\n");
            break;
        }

        // No frame-rate cap — the loop is GPU-bound: the per-frame fence wait + MAILBOX present
        // mode let the renderer run as fast as the GPU finishes each frame ("unlimited" fps).
        frame_count++;

        auto now = std::chrono::high_resolution_clock::now();
        double elapsed_s = std::chrono::duration_cast<std::chrono::microseconds>(now - last_time).count() / 1e6;
        if (elapsed_s >= 1.0) {
            printf("FPS: %.0f (frame %d)\n", frame_count / elapsed_s, frame_count);
            fflush(stdout);
            frame_count = 0;
            last_time = now;
        }
    }

    printf("Shutting down...\n");
    engine.shutdown();
    return 0;
}
