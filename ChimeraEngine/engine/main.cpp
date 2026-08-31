// main.cpp — Bootstrap + Main Loop
// Initializes Engine, Physics; runs the simulation loop with GPU rendering.
// Also serves /frame (PNG of the current render) and /membrane (load a story membrane
// scene into the Vulkan renderer) so the engine is the emission target the dyad points at.
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <mmsystem.h>
#pragma comment(lib, "winmm.lib")
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
    float cam_full[8] = {};      // D6: r,theta,phi,target xyz,pan xy (recall)
    bool cam_full_set = false;   // true: apply all 8, ignore the r/theta/phi fields
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
struct MeshReq { std::vector<float> verts; std::vector<uint32_t> indices; uint32_t N=0, idxCount=0; float cam_radius=12.f, cam_theta=0.f, cam_phi=0.3f; uint32_t slot=0, mode=0; bool update_only=false; bool valid=false; };
static MeshReq g_mesh_req;
static std::mutex g_mesh_mutex;
static std::condition_variable g_mesh_cv;
static bool g_mesh_pending = false, g_mesh_applied = false;

// ── Pending hinge request (the engine-internal knee pose; same handoff) ──────
struct HingeReq { std::vector<float> wL, wR; float JL[3]={}, JR[3]={}, axis[3]={}; float romL=0, romR=0, period=4.f, phaseR=3.14159265f; uint32_t n=0; };
static HingeReq g_hinge_req;
static std::mutex g_hinge_mutex;
static std::condition_variable g_hinge_cv;
static bool g_hinge_pending = false, g_hinge_applied = false;

// ── Pending water request (the CA-field solver; same handoff) ───────────────
struct WaterReq { Engine::WaterUpload up; int kind = 1; uint32_t n_macro = 1; double dt = 0.01;
                  int64_t sum = 0, mn = 0; std::vector<int32_t> states; uint32_t ns = 0, nc = 0; bool ok = false; };
static WaterReq g_water_req;
static std::mutex g_water_mutex;
static std::condition_variable g_water_cv;
static bool g_water_pending = false, g_water_applied = false;

// ── Pending gait request (H7 stage 2 CPG; same handoff) ─────────────────────
struct GaitReq { int kind = 0;                       // 1 = load (gait_bin), 2 = download ring
                 std::vector<double> consts; std::vector<int32_t> edges;
                 double phi0[8] = {}; double theta0[2] = {};
                 std::vector<double> ring; bool ok = false; };
static GaitReq g_gait_req;
static std::mutex g_gait_mutex;
static std::condition_variable g_gait_cv;

// ── Pending volp request (H13 volp-ARAP knee kernel; same handoff) ──────────
struct VolpReq { int kind = 0;                       // 1 = load (volp_bin), 2 = download mesh
                 std::vector<uint8_t> blob; std::vector<float> mesh; bool ok = false; };
static VolpReq g_volp_req;
static std::mutex g_volp_mutex;
static std::condition_variable g_volp_cv;
static bool g_volp_pending = false, g_volp_applied = false;
static bool g_gait_pending = false, g_gait_applied = false;

// ── Pending frost request (H9 decode; same handoff) ─────────────────────────
struct FrostReq { int kind = 0; std::vector<uint8_t> blob; std::vector<int32_t> data; bool ok = false; };
static FrostReq g_frost_req;
static std::mutex g_frost_mutex;
static std::condition_variable g_frost_cv;
static bool g_frost_pending = false, g_frost_applied = false;

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

static double get_double(const std::string& body, const char* key, double def) {
    size_t p = find_colon_after(body, key);
    if (p == std::string::npos) return def;
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    try { return std::stod(body.substr(p)); } catch (...) { return def; }
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
    // F1: posted console lines carry escaped JSON (\" \\ \n) — unescape them
    // F4: and \uXXXX too (json.dumps' ensure_ascii) — a posted verdict must
    // land VERBATIM, em-dashes and CJK included (surrogate pairs decoded).
    std::string out;
    auto hex4 = [&](size_t at, uint32_t& v) -> bool {
        if (at + 4 > body.size()) return false;
        v = 0;
        for (int k = 0; k < 4; ++k) {
            char c = body[at + k]; v <<= 4;
            if (c >= '0' && c <= '9') v |= c - '0';
            else if (c >= 'a' && c <= 'f') v |= c - 'a' + 10;
            else if (c >= 'A' && c <= 'F') v |= c - 'A' + 10;
            else return false;
        }
        return true;
    };
    auto utf8 = [&](uint32_t cp) {
        if (cp < 0x80) out += static_cast<char>(cp);
        else if (cp < 0x800) {
            out += static_cast<char>(0xC0 | (cp >> 6));
            out += static_cast<char>(0x80 | (cp & 0x3F));
        } else if (cp < 0x10000) {
            out += static_cast<char>(0xE0 | (cp >> 12));
            out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
            out += static_cast<char>(0x80 | (cp & 0x3F));
        } else {
            out += static_cast<char>(0xF0 | (cp >> 18));
            out += static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
            out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
            out += static_cast<char>(0x80 | (cp & 0x3F));
        }
    };
    while (p < body.size() && body[p] != '"') {
        if (body[p] == '\\' && p + 1 < body.size()) {
            char e = body[p + 1];
            if (e == '"' || e == '\\' || e == '/') { out += e; p += 2; continue; }
            if (e == 'n') { out += '\n'; p += 2; continue; }
            if (e == 't') { out += '\t'; p += 2; continue; }
            if (e == 'r') { out += '\r'; p += 2; continue; }
            if (e == 'b') { out += '\b'; p += 2; continue; }
            if (e == 'f') { out += '\f'; p += 2; continue; }
            if (e == 'u') {
                uint32_t hi = 0;
                if (hex4(p + 2, hi)) {
                    p += 6;
                    if (hi >= 0xD800 && hi <= 0xDBFF &&
                        p + 1 < body.size() && body[p] == '\\' && body[p + 1] == 'u') {
                        uint32_t lo = 0;
                        if (hex4(p + 2, lo) && lo >= 0xDC00 && lo <= 0xDFFF) {
                            utf8(0x10000 + ((hi - 0xD800) << 10) + (lo - 0xDC00));
                            p += 6;
                            continue;
                        }
                    }
                    utf8(hi);
                    continue;
                }
            }
        }
        out += body[p++];
    }
    return out;
}

static bool get_bool(const std::string& body, const char* key, bool def) {
    size_t p = find_colon_after(body, key);
    if (p == std::string::npos) return def;
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (body.compare(p, 4, "true") == 0) return true;
    if (body.compare(p, 5, "false") == 0) return false;
    return def;
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
    // 1 ms timer granularity for the frame-cap sleeps (Windows default is 15.6 ms).
    timeBeginPeriod(1);
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

    // THE STUDIO: optional board file path (argv[2]); default is studio_board.json
    // in the CWD — tools/studio_board.py writes it next to the exe.
    if (argc > 2) engine.ui_.set_board_file(argv[2]);

    // ── HTTP server for Python shim communication ───────────────────────────────
    // F1: the handler is a NAMED function — the HTTP server and the console's
    // worker run the SAME one (the console is the API's interactive twin).
    HttpServer server;
    Engine::ApiFn api = [&](const std::string& method, const std::string& path,
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
                        // slotmode >= 100: vertex-update only (animation streaming) —
                        // memcpy into the mapped vertex buffer, no reload, no camera.
                        g_mesh_req.update_only = (sm >= 100);
                        if (g_mesh_req.update_only) sm -= 100;
                        g_mesh_req.slot = sm / 10; g_mesh_req.mode = sm % 10;
                        g_mesh_pending = true; g_mesh_applied = false;
                    }
                    std::unique_lock<std::mutex> lk(g_mesh_mutex);
                    bool ok = g_mesh_cv.wait_for(lk, std::chrono::seconds(15), []{ return g_mesh_applied; });
                    body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/hinge_bin" && method == "POST") {
            // Binary protocol (little-endian):
            //   [u32 nvert][f32 JL(3)][f32 JR(3)][f32 axis(3)][f32 romL,romR,period,phaseR]
            //   [f32 wL * nvert][f32 wR * nvert]
            // nvert == 0 -> disengage the hinge and restore the rest pose.
            if (req_body.size() < 4) {
                body = "{\"ok\":false,\"error\":\"short header\"}";
            } else {
                uint32_t n = 0;
                std::memcpy(&n, req_body.data(), 4);
                if (n == 0) {
                    {
                        std::lock_guard<std::mutex> lk(g_hinge_mutex);
                        g_hinge_req = HingeReq{};
                        g_hinge_pending = true; g_hinge_applied = false;
                    }
                    std::unique_lock<std::mutex> lk(g_hinge_mutex);
                    bool ok = g_hinge_cv.wait_for(lk, std::chrono::seconds(15), []{ return g_hinge_applied; });
                    body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                } else {
                    size_t expect = 4 + 13 * 4 + static_cast<size_t>(n) * 2 * 4;
                    if (req_body.size() != expect) {
                        body = "{\"ok\":false,\"error\":\"size mismatch\"}";
                    } else {
                        const float* f = reinterpret_cast<const float*>(req_body.data() + 4);
                        {
                            std::lock_guard<std::mutex> lk(g_hinge_mutex);
                            g_hinge_req.n = n;
                            std::memcpy(g_hinge_req.JL, f + 0, 12);
                            std::memcpy(g_hinge_req.JR, f + 3, 12);
                            std::memcpy(g_hinge_req.axis, f + 6, 12);
                            g_hinge_req.romL = f[9]; g_hinge_req.romR = f[10];
                            g_hinge_req.period = f[11]; g_hinge_req.phaseR = f[12];
                            g_hinge_req.wL.assign(f + 13, f + 13 + n);
                            g_hinge_req.wR.assign(f + 13 + n, f + 13 + 2 * n);
                            g_hinge_pending = true; g_hinge_applied = false;
                        }
                        std::unique_lock<std::mutex> lk(g_hinge_mutex);
                        bool ok = g_hinge_cv.wait_for(lk, std::chrono::seconds(15), []{ return g_hinge_applied; });
                        body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                    }
                }
            }
            content_type = "application/json";
        } else if (p == "/water_bin" && method == "POST") {
            // Binary protocol (little-endian):
            //   [u32 n_cells][u32 n_edges][u32 n_colors][u32 n_inj_pairs]
            //   [f64 Q][f64 G][f64 c_local]
            //   areas(n f64) | bed(n f64) | V0(n i32) | occ(n u32) |
            //   eij(2e i32) | k_e(e f64) | l_ij(e f64) |
            //   color_start(n_colors+1 u32) | inj(2*n_inj u32)
            if (req_body.size() < 40) {
                body = "{\"ok\":false,\"error\":\"short header\"}";
            } else {
                const uint8_t* d = reinterpret_cast<const uint8_t*>(req_body.data());
                auto rd_u32 = [&](size_t off) { uint32_t v; std::memcpy(&v, d + off, 4); return v; };
                auto rd_f64 = [&](size_t off) { double v; std::memcpy(&v, d + off, 8); return v; };
                Engine::WaterUpload up{};
                up.n_cells = rd_u32(0);
                uint32_t ne = rd_u32(4);
                up.n_edges = ne;
                up.n_colors = rd_u32(8);
                uint32_t n_inj = rd_u32(12);
                up.Q = rd_f64(16); up.G = rd_f64(24); up.c_local = rd_f64(32);
                size_t off = 40;
                size_t n = up.n_cells;
                size_t expect = off + n * 8 * 2 + n * 4 * 2 + static_cast<size_t>(ne) * 4 * 2
                              + static_cast<size_t>(ne) * 8 * 2 + static_cast<size_t>(ne) * 4 + (up.n_colors + 1) * 4 + static_cast<size_t>(n_inj) * 8;
                if (req_body.size() != expect) {
                    body = "{\"ok\":false,\"error\":\"size mismatch\"}";
                } else {
                    up.areas.resize(n); up.bed.resize(n); up.V0.resize(n); up.occ.resize(n);
                    up.eij.resize(static_cast<size_t>(ne) * 2);
                    up.k_e.resize(ne); up.l_ij.resize(ne);
                    up.color_start.resize(up.n_colors + 1);
                    up.inj.resize(static_cast<size_t>(n_inj) * 2);
                    std::memcpy(up.areas.data(), d + off, n * 8); off += n * 8;
                    std::memcpy(up.bed.data(), d + off, n * 8); off += n * 8;
                    std::memcpy(up.V0.data(), d + off, n * 4); off += n * 4;
                    std::memcpy(up.occ.data(), d + off, n * 4); off += n * 4;
                    std::memcpy(up.eij.data(), d + off, static_cast<size_t>(ne) * 8); off += static_cast<size_t>(ne) * 8;
                    std::memcpy(up.k_e.data(), d + off, static_cast<size_t>(ne) * 8); off += static_cast<size_t>(ne) * 8;
                    std::memcpy(up.l_ij.data(), d + off, static_cast<size_t>(ne) * 8); off += static_cast<size_t>(ne) * 8;
                    up.edge_active.resize(ne);
                    std::memcpy(up.edge_active.data(), d + off, static_cast<size_t>(ne) * 4); off += static_cast<size_t>(ne) * 4;
                    std::memcpy(up.color_start.data(), d + off, (up.n_colors + 1) * 4); off += (up.n_colors + 1) * 4;
                    std::memcpy(up.inj.data(), d + off, static_cast<size_t>(n_inj) * 8);
                    {
                        std::lock_guard<std::mutex> lk(g_water_mutex);
                        g_water_req = WaterReq{};
                        g_water_req.kind = 1;
                        g_water_req.up = std::move(up);
                        g_water_pending = true; g_water_applied = false;
                    }
                    std::unique_lock<std::mutex> lk(g_water_mutex);
                    bool ok = g_water_cv.wait_for(lk, std::chrono::seconds(60), []{ return g_water_applied; });
                    body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/water_step" && method == "POST") {
            // JSON {"n_macro":N, "dt_macro":D} -> runs on the render thread
            uint32_t n_macro = 1; double dt = 0.01;
            {
                auto find_num = [&](const char* key, std::string& out) {
                    size_t pos = req_body.find(key);
                    if (pos == std::string::npos) return false;
                    pos = req_body.find(':', pos);
                    if (pos == std::string::npos) return false;
                    size_t a = req_body.find_first_of("-0123456789.", pos);
                    size_t b = req_body.find_first_not_of("-0123456789.eE+", a);
                    out = req_body.substr(a, b - a);
                    return true;
                };
                std::string v;
                if (find_num("n_macro", v)) n_macro = static_cast<uint32_t>(std::stoul(v));
                if (find_num("dt_macro", v)) dt = std::stod(v);
            }
                    {
                        std::lock_guard<std::mutex> lk(g_water_mutex);
                        g_water_req = WaterReq{};
                        g_water_req.kind = 2;
                        g_water_req.n_macro = n_macro;
                        g_water_req.dt = dt;
                        g_water_pending = true; g_water_applied = false;
                    }
                    bool ok;
                    int64_t sum, mn;
                    {
                        std::unique_lock<std::mutex> lk(g_water_mutex);
                        g_water_cv.wait_for(lk, std::chrono::seconds(120), []{ return g_water_applied; });
                        ok = g_water_req.ok; sum = g_water_req.sum; mn = g_water_req.mn;
                    }
            body = std::string("{\"ok\":") + (ok ? "true" : "false")
                 + ",\"sum\":" + std::to_string(sum) + ",\"min\":" + std::to_string(mn) + "}";
            content_type = "application/json";
        } else if (p == "/water_state" && method == "GET") {
            {
                std::lock_guard<std::mutex> lk(g_water_mutex);
                g_water_req = WaterReq{};
                g_water_req.kind = 3;
                g_water_pending = true; g_water_applied = false;
            }
            bool ok;
            std::vector<int32_t> states; uint32_t ns, nc;
            {
                std::unique_lock<std::mutex> lk(g_water_mutex);
                g_water_cv.wait_for(lk, std::chrono::seconds(60), []{ return g_water_applied; });
                ok = g_water_req.ok; states = std::move(g_water_req.states);
                ns = g_water_req.ns; nc = g_water_req.nc;
            }
            if (ok) {
                std::string out(8 + states.size() * 4, '\0');
                uint32_t hdr[2] = { ns, nc };
                std::memcpy(out.data(), hdr, 8);
                std::memcpy(out.data() + 8, states.data(), states.size() * 4);
                body = std::move(out);
                content_type = "application/octet-stream";
            } else {
                body = "{\"ok\":false,\"error\":\"no water\"}";
                content_type = "application/json";
            }
        } else if (p == "/water_clock" && method == "POST") {
            // JSON {"on":bool, "steps":N, "dt":D, "inj_target":T, "inj_count":C} —
            // flags only (atomics); the stepping itself happens on the render
            // thread inside frame() (H4: the CA field runs on the engine's clock).
            auto find_bool = [&](const char* key, bool def) {
                size_t pos = find_colon_after(req_body, key);
                if (pos == std::string::npos) return def;
                while (pos < req_body.size() && (req_body[pos] == ' ' || req_body[pos] == '\t')) ++pos;
                if (req_body.compare(pos, 4, "true") == 0) return true;
                if (req_body.compare(pos, 5, "false") == 0) return false;
                return def;
            };
            bool on = find_bool("on", false);
            uint32_t steps = get_uint(req_body, "steps", 1);
            double dt = static_cast<double>(get_float(req_body, "dt", 0.01f));
            int32_t inj_target = static_cast<int32_t>(get_float(req_body, "inj_target", -1.0f));
            int32_t inj_count  = static_cast<int32_t>(get_float(req_body, "inj_count", 0.0f));
            if (g_engine) {
                bool was = g_engine->water_clock_on_.load();
                g_engine->water_clock_steps_per_frame_.store(steps ? steps : 1);
                g_engine->water_clock_dt_.store(dt);
                g_engine->water_clock_inj_target_.store(inj_target);
                g_engine->water_clock_inj_count_.store(inj_count);
                if (on && !was) g_engine->water_clock_steps_total_.store(0);  // a fresh run
                g_engine->water_clock_on_.store(on);
            }
            body = std::string("{\"ok\":true,\"steps_total\":")
                 + std::to_string(g_engine ? g_engine->water_clock_steps_total_.load() : 0) + "}";
            content_type = "application/json";
        } else if (p == "/water_clock" && method == "GET") {
            if (g_engine) {
                body = std::string("{\"on\":") + (g_engine->water_clock_on_.load() ? "true" : "false")
                     + ",\"steps\":" + std::to_string(g_engine->water_clock_steps_per_frame_.load())
                     + ",\"inj_target\":" + std::to_string(g_engine->water_clock_inj_target_.load())
                     + ",\"inj_count\":" + std::to_string(g_engine->water_clock_inj_count_.load())
                     + ",\"steps_total\":" + std::to_string(g_engine->water_clock_steps_total_.load()) + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/water_vis" && method == "POST") {
            // JSON {"on":bool, "tri_base":B} — B = face offset of the water part
            // inside the whole-mesh index buffer (proven by .tmp/water_align_check.py).
            auto find_bool = [&](const char* key, bool def) {
                size_t pos = find_colon_after(req_body, key);
                if (pos == std::string::npos) return def;
                while (pos < req_body.size() && (req_body[pos] == ' ' || req_body[pos] == '\t')) ++pos;
                if (req_body.compare(pos, 4, "true") == 0) return true;
                if (req_body.compare(pos, 5, "false") == 0) return false;
                return def;
            };
            bool on = find_bool("on", false);
            uint32_t tri_base = get_uint(req_body, "tri_base", 0);
            if (g_engine) {
                g_engine->water_vis_tri_base_.store(tri_base);
                g_engine->water_vis_on_.store(on);
            }
            body = "{\"ok\":true}";
            content_type = "application/json";
        } else if (p == "/gait_bin" && method == "POST") {
            // Binary protocol (little-endian), H7 stage 2 CPG setup:
            //   [u32 n_consts][u32 n_edges][f64 theta0L][f64 theta0R][f64 phi0 * 8]
            //   [f64 consts * n_consts][i32 edges * n_edges]
            if (req_body.size() < 88) {
                body = "{\"ok\":false,\"error\":\"short header\"}";
            } else {
                const uint8_t* d = reinterpret_cast<const uint8_t*>(req_body.data());
                auto rd_u32 = [&](size_t off) { uint32_t v; std::memcpy(&v, d + off, 4); return v; };
                uint32_t nc = rd_u32(0), ne = rd_u32(4);
                size_t expect = 8 + 16 + 64 + static_cast<size_t>(nc) * 8 + static_cast<size_t>(ne) * 4;
                if (req_body.size() != expect || nc < 37 || ne < 16) {
                    body = "{\"ok\":false,\"error\":\"size mismatch\"}";
                } else {
                    {
                        std::lock_guard<std::mutex> lk(g_gait_mutex);
                        g_gait_req = GaitReq{};
                        g_gait_req.kind = 1;
                        std::memcpy(g_gait_req.theta0, d + 8, 16);
                        std::memcpy(g_gait_req.phi0, d + 24, 64);
                        g_gait_req.consts.resize(nc);
                        std::memcpy(g_gait_req.consts.data(), d + 88, static_cast<size_t>(nc) * 8);
                        g_gait_req.edges.resize(ne);
                        std::memcpy(g_gait_req.edges.data(), d + 88 + static_cast<size_t>(nc) * 8,
                                    static_cast<size_t>(ne) * 4);
                        g_gait_pending = true; g_gait_applied = false;
                    }
                    std::unique_lock<std::mutex> lk(g_gait_mutex);
                    bool ok = g_gait_cv.wait_for(lk, std::chrono::seconds(60), []{ return g_gait_applied; });
                    body = ok && g_gait_req.ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"load failed\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/gait" && method == "POST") {
            // JSON {"on":bool, "steps":N, "omega":W} — flags only (atomics); the
            // stepping happens on the render thread inside frame() (the water
            // clock's pattern). "omega" parses as double: the bit-exactness gate
            // needs the exact float64 omega_ref, not a 32-bit round.
            auto find_bool = [&](const char* key, bool def) {
                size_t pos = find_colon_after(req_body, key);
                if (pos == std::string::npos) return def;
                while (pos < req_body.size() && (req_body[pos] == ' ' || req_body[pos] == '\t')) ++pos;
                if (req_body.compare(pos, 4, "true") == 0) return true;
                if (req_body.compare(pos, 5, "false") == 0) return false;
                return def;
            };
            bool on = find_bool("on", false);
            uint32_t steps = get_uint(req_body, "steps", 3);
            double omega = get_double(req_body, "omega", 7.853981633974483);
            if (g_engine) {
                bool was = g_engine->gait_on_.load();
                g_engine->gait_steps_per_frame_.store(steps ? steps : 1);
                g_engine->gait_omega_.store(omega);
                if (on && !was) g_engine->gait_steps_total_.store(0);   // a fresh run
                g_engine->gait_on_.store(on);
            }
            body = std::string("{\"ok\":true,\"steps_total\":")
                 + std::to_string(g_engine ? g_engine->gait_steps_total_.load() : 0) + "}";
            content_type = "application/json";
        } else if (p == "/gait" && method == "GET") {
            if (g_engine) {
                double tL = 0, tR = 0; g_engine->gait_theta(tL, tR);
                body = std::string("{\"loaded\":") + (g_engine->gait_loaded() ? "true" : "false")
                     + ",\"on\":" + (g_engine->gait_on_.load() ? "true" : "false")
                     + ",\"steps\":" + std::to_string(g_engine->gait_steps_per_frame_.load())
                     + ",\"omega\":" + std::to_string(g_engine->gait_omega_.load())
                     + ",\"steps_total\":" + std::to_string(g_engine->gait_steps_total_.load())
                     + ",\"thetaL\":" + std::to_string(tL)
                     + ",\"thetaR\":" + std::to_string(tR) + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/gait_state" && method == "GET") {
            // Binary: [u64 steps_total][u64 cap][f64 ring * cap * 8] — the phase
            // series ring for the bit-exactness gate (B15 pattern).
            {
                std::lock_guard<std::mutex> lk(g_gait_mutex);
                g_gait_req = GaitReq{};
                g_gait_req.kind = 2;
                g_gait_pending = true; g_gait_applied = false;
            }
            bool ok; std::vector<double> ring;
            {
                std::unique_lock<std::mutex> lk(g_gait_mutex);
                g_gait_cv.wait_for(lk, std::chrono::seconds(60), []{ return g_gait_applied; });
                ok = g_gait_req.ok; ring = std::move(g_gait_req.ring);
            }
            if (ok && g_engine) {
                uint64_t hdr[2] = { g_engine->gait_steps_total_.load(),
                                    static_cast<uint64_t>(ring.size() / 8) };
                std::string out(16 + ring.size() * 8, '\0');
                std::memcpy(out.data(), hdr, 16);
                std::memcpy(out.data() + 16, ring.data(), ring.size() * 8);
                body = std::move(out);
                content_type = "application/octet-stream";
            } else {
                body = "{\"ok\":false,\"error\":\"no gait\"}";
                content_type = "application/json";
            }
        } else if (p == "/joints_bin" && method == "POST") {
            // H15: the all-joints pack (JNT1 blob: assignments, weights, table)
            {
                std::lock_guard<std::mutex> lk(g_volp_mutex);
                g_volp_req = VolpReq{};
                g_volp_req.kind = 3;
                g_volp_req.blob.assign(req_body.begin(), req_body.end());
                g_volp_pending = true; g_volp_applied = false;
            }
            std::unique_lock<std::mutex> lk(g_volp_mutex);
            bool ok = g_volp_cv.wait_for(lk, std::chrono::seconds(60), []{ return g_volp_applied; });
            body = ok && g_volp_req.ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"load failed\"}";
            content_type = "application/json";
        } else if (p == "/joints" && method == "POST") {
            // JSON {"on":bool} — the show owns the pose while on.
            if (g_engine) {
                bool on = get_bool(req_body, "on", true);
                g_engine->joints_on_.store(on ? 1 : 0);
            }
            body = "{\"ok\":true}";
            content_type = "application/json";
        } else if (p == "/joint" && method == "POST") {
            // C1: THE JOINTS EDITOR's HTTP twin. {"joint":name|index,"theta":deg}
            // is an ownership claim — the editor takes the pose (clamped to the
            // pack's derived ROM). {"select":name|index|-1} aims the gizmo +
            // weight-paint without posing. The applied (post-clamp) theta comes
            // back once the render thread has consumed the intent.
            if (g_engine && g_engine->joints_loaded()) {
                auto resolve = [&](const std::string& key, bool& present) -> int {
                    present = req_body.find(std::string("\"") + key + "\"") != std::string::npos;
                    if (!present) return -2;
                    std::string nm = get_string(req_body, key.c_str());
                    if (!nm.empty()) return g_engine->joint_index(nm);
                    return static_cast<int>(get_float(req_body, key.c_str(), -1.0f));
                };
                bool has_sel = false, has_joint = false;
                int sel = resolve("select", has_sel);
                int jidx = resolve("joint", has_joint);
                if (has_sel) {
                    int prev = g_engine->selected_joint_.load();
                    g_engine->selected_joint_.store(sel == prev ? -1 : (sel < 0 ? -1 : sel));
                }
                std::string applied;
                if (has_joint && jidx >= 0 && req_body.find("\"theta\"") != std::string::npos) {
                    g_engine->request_joint_edit(jidx, get_float(req_body, "theta", 0.0f));
                    // wait for the render thread to consume (one frame is ~ms;
                    // 2 s is a hang, not a latency)
                    auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
                    while (g_engine->edit_pending_.load()) {
                        if (std::chrono::steady_clock::now() > deadline) break;
                        Sleep(2);
                    }
                    applied = std::string(",\"theta_applied\":")
                            + std::to_string(g_engine->edit_applied_deg_.load());
                }
                body = std::string("{\"ok\":true,\"owner\":\"")
                     + (g_engine->joints_owner_.load() == 1 ? "edit" : "show")
                     + "\",\"selected\":" + std::to_string(g_engine->selected_joint_.load())
                     + applied + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no joints pack\"}";
            }
            content_type = "application/json";
        } else if (p == "/project" && method == "POST") {
            // C1: the gizmo's math channel, exposed for verification — world in,
            // screen px out, through the same stashed VP the gizmo draws with.
            if (g_engine) {
                float wp[3] = { get_float(req_body, "x", 0.0f), get_float(req_body, "y", 0.0f),
                                get_float(req_body, "z", 0.0f) };
                float sx = 0.f, sy = 0.f;
                bool ok = g_engine->project_world(wp, sx, sy);
                float cam[8]; g_engine->camera_state(cam);
                char cb[192];
                snprintf(cb, sizeof(cb), "[%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f]",
                         cam[0], cam[1], cam[2], cam[3], cam[4], cam[5], cam[6], cam[7]);
                body = std::string("{\"ok\":") + (ok ? "true" : "false")
                     + ",\"sx\":" + std::to_string(sx) + ",\"sy\":" + std::to_string(sy)
                     + ",\"cam\":" + cb + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/joints" && method == "GET") {
            // C1: the full editor document (owner, selected, per-joint ROM/theta/J/axis)
            body = g_engine ? g_engine->joints_editor_json() : "{\"ok\":false}";
            content_type = "application/json";
        } else if (p == "/volp_bin" && method == "POST") {
            // H13: the volp-ARAP kernel payload (built by .tmp/volp_pack.py).
            // Raw binary body = the 'VOLP' v2 blob; loaded on the render thread.
            {
                std::lock_guard<std::mutex> lk(g_volp_mutex);
                g_volp_req = VolpReq{};
                g_volp_req.kind = 1;
                g_volp_req.blob.assign(req_body.begin(), req_body.end());
                g_volp_pending = true; g_volp_applied = false;
            }
            std::unique_lock<std::mutex> lk(g_volp_mutex);
            bool ok = g_volp_cv.wait_for(lk, std::chrono::seconds(60), []{ return g_volp_applied; });
            body = ok && g_volp_req.ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"load failed\"}";
            content_type = "application/json";
        } else if (p == "/volp" && method == "POST") {
            // JSON {"mode":"volp"|"blend", "manual":bool, "thetaL":deg, "thetaR":deg,
            //       "m":N} — flags only (atomics). A mode change cold-starts the
            // solve (the kernel re-poses from the theta-exact blend pose).
            if (g_engine) {
                std::string mode = get_string(req_body, "mode");
                if (mode == "volp")  { g_engine->volp_mode_.store(1); g_engine->volp_cold_.store(true); }
                if (mode == "blend") { g_engine->volp_mode_.store(0); g_engine->volp_cold_.store(true); }
                bool man = get_bool(req_body, "manual", g_engine->volp_manual_.load());
                if (man != g_engine->volp_manual_.load()) {
                    g_engine->volp_manual_.store(man);
                    g_engine->volp_cold_.store(true);
                }
                if (man) {
                    g_engine->volp_thL_.store((float)get_double(req_body, "thetaL", 0.0));
                    g_engine->volp_thR_.store((float)get_double(req_body, "thetaR", 0.0));
                }
                uint32_t m = get_uint(req_body, "m", 0);
                if (m >= 1 && m <= 64) g_engine->volp_M_.store(m);
            }
            body = "{\"ok\":true}";
            content_type = "application/json";
        } else if (p == "/volp" && method == "GET") {
            if (g_engine) {
                const float* st = g_engine->volp_stats();
                body = std::string("{\"loaded\":") + (g_engine->volp_loaded() ? "true" : "false")
                     + ",\"mode\":" + (g_engine->volp_mode_.load() == 1 ? "\"volp\"" : "\"blend\"")
                     + ",\"manual\":" + (g_engine->volp_manual_.load() ? "true" : "false")
                     + ",\"M\":" + std::to_string(g_engine->volp_M_.load())
                     + (st ? std::string(",\"dV\":") + std::to_string(st[0])
                           + ",\"mu\":" + std::to_string(st[1])
                           + ",\"residual\":" + std::to_string(st[2])
                           + ",\"v_cur\":" + std::to_string(st[3])
                           + ",\"frames\":" + std::to_string(st[5])
                           + ",\"thetaL\":" + std::to_string(st[6])
                           + ",\"thetaR\":" + std::to_string(st[7]) : "")
                     + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/volp_state" && method == "GET") {
            // Binary: [u32 n_records][f32 verts * n_records * 9] — the full posed
            // vertex buffer (the in-engine gate's readback; debug endpoint).
            {
                std::lock_guard<std::mutex> lk(g_volp_mutex);
                g_volp_req = VolpReq{};
                g_volp_req.kind = 2;
                g_volp_pending = true; g_volp_applied = false;
            }
            bool ok; std::vector<float> mesh;
            {
                std::unique_lock<std::mutex> lk(g_volp_mutex);
                g_volp_cv.wait_for(lk, std::chrono::seconds(60), []{ return g_volp_applied; });
                ok = g_volp_req.ok; mesh = std::move(g_volp_req.mesh);
            }
            if (ok) {
                uint32_t n = static_cast<uint32_t>(mesh.size() / 9);
                std::string out(4 + mesh.size() * 4, '\0');
                std::memcpy(out.data(), &n, 4);
                std::memcpy(out.data() + 4, mesh.data(), mesh.size() * 4);
                body = std::move(out);
                content_type = "application/octet-stream";
            } else {
                body = "{\"ok\":false,\"error\":\"no volp\"}";
                content_type = "application/json";
            }
        } else if (p == "/water_vis_state" && method == "GET") {
            // DEBUG (W4 bring-up): [4 u32 indirect][floats of the water vertex buffer]
            {
                std::lock_guard<std::mutex> lk(g_water_mutex);
                g_water_req = WaterReq{};
                g_water_req.kind = 4;
                g_water_pending = true; g_water_applied = false;
            }
            bool ok;
            std::vector<int32_t> dbg;
            {
                std::unique_lock<std::mutex> lk(g_water_mutex);
                g_water_cv.wait_for(lk, std::chrono::seconds(30), []{ return g_water_applied; });
                ok = g_water_req.ok; dbg = std::move(g_water_req.states);
            }
            if (ok) {
                body.assign(reinterpret_cast<const char*>(dbg.data()), dbg.size() * 4);
                content_type = "application/octet-stream";
            } else {
                body = "{\"ok\":false,\"error\":\"no water vis\"}";
                content_type = "application/json";
            }
        } else if (p == "/frost_bin" && method == "POST") {
            // Binary: the raw .tmp/frost_gt/frost_engine.bin blob (see
            // .tmp/frost_decode_ref.py::export_blob for the layout).
            if (req_body.size() < 64) {
                body = "{\"ok\":false,\"error\":\"short blob\"}";
            } else {
                {
                    std::lock_guard<std::mutex> lk(g_frost_mutex);
                    g_frost_req = FrostReq{};
                    g_frost_req.kind = 1;
                    g_frost_req.blob.assign(req_body.begin(), req_body.end());
                    g_frost_pending = true; g_frost_applied = false;
                }
                std::unique_lock<std::mutex> lk(g_frost_mutex);
                bool ok = g_frost_cv.wait_for(lk, std::chrono::seconds(30), []{ return g_frost_applied; });
                body = (ok && g_frost_req.ok) ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"apply failed or timeout\"}";
            }
            content_type = "application/json";
        } else if (p == "/frost" && method == "POST") {
            // JSON {"on":bool, "light":[x,y,z]} — light is a world-space direction
            // (normalized + quantized in-engine, correctly-rounded IEEE == Python).
            auto find_bool2 = [&](const char* key, bool def) {
                size_t pos = req_body.find(key);
                if (pos == std::string::npos) return def;
                pos = req_body.find(':', pos);
                if (pos == std::string::npos) return def;
                size_t a = req_body.find_first_not_of(" \t", pos + 1);
                return a != std::string::npos && req_body.compare(a, 4, "true") == 0;
            };
            bool on = find_bool2("on", g_engine ? g_engine->frost_on_.load() : false);
            if (g_engine) {
                size_t lp = req_body.find("\"light\"");
                if (lp != std::string::npos) {
                    size_t ob = req_body.find('[', lp);
                    if (ob != std::string::npos) {
                        double lv[3]; int got = 0;
                        const char* s = req_body.c_str() + ob + 1;
                        char* end = nullptr;
                        for (; got < 3; ++got) {
                            lv[got] = strtod(s, &end);
                            if (end == s) break;
                            s = end;
                            while (*s == ' ' || *s == ',') ++s;
                        }
                        if (got == 3) {
                            g_engine->frost_light_x_.store(lv[0]);
                            g_engine->frost_light_y_.store(lv[1]);
                            g_engine->frost_light_z_.store(lv[2]);
                        }
                    }
                }
                g_engine->frost_on_.store(on);
            }
            body = "{\"ok\":true}";
            content_type = "application/json";
        } else if (p == "/frost" && method == "GET") {
            if (g_engine && g_engine->frost_loaded_) {
                char buf[512];
                snprintf(buf, sizeof(buf),
                    "{\"on\":%s,\"loaded\":true,\"n_tris\":%u,\"frame\":%llu,"
                    "\"light\":[%.17g,%.17g,%.17g],"
                    "\"view_q\":[%d,%d,%d],\"light_q\":[%d,%d,%d],"
                    "\"kernel_path\":\"scalar-int32-imad\","
                    "\"dp4a\":\"unavailable: no GLSL integer-dot-product binding in glslang 1.4.328\","
                    "\"coopvec\":\"%s\"}",
                    g_engine->frost_on_.load() ? "true" : "false",
                    g_engine->frost_tris(),
                    (unsigned long long)g_engine->frost_frame_.load(),
                    g_engine->frost_light_x_.load(),
                    g_engine->frost_light_y_.load(),
                    g_engine->frost_light_z_.load(),
                    g_engine->frost_vq_[0].load(), g_engine->frost_vq_[1].load(),
                    g_engine->frost_vq_[2].load(),
                    g_engine->frost_lq_[0].load(), g_engine->frost_lq_[1].load(),
                    g_engine->frost_lq_[2].load(),
                    g_engine->frost_coopvec_present_ ? "present-inactive" : "absent");
                body = buf;
            } else {
                body = "{\"on\":false,\"loaded\":false}";
            }
            content_type = "application/json";
        } else if (p == "/frost_debug" && method == "POST") {
            // Bit-exactness snapshot: arms the debug write on the next dispatched
            // frame; returns [i32 * F*3 colors][i32 * F*14 kernel inputs].
            {
                std::lock_guard<std::mutex> lk(g_frost_mutex);
                g_frost_req = FrostReq{};
                g_frost_req.kind = 2;
                g_frost_pending = true; g_frost_applied = false;
            }
            bool ok; std::vector<int32_t> snap;
            {
                std::unique_lock<std::mutex> lk(g_frost_mutex);
                ok = g_frost_cv.wait_for(lk, std::chrono::seconds(15), []{ return g_frost_applied; });
                snap = std::move(g_frost_req.data);
                ok = ok && g_frost_req.ok;
            }
            if (ok) {
                body.assign(reinterpret_cast<const char*>(snap.data()), snap.size() * 4);
                content_type = "application/octet-stream";
            } else {
                body = "{\"ok\":false,\"error\":\"snapshot failed or timeout (frost on?)\"}";
                content_type = "application/json";
            }
        } else if (p == "/eye_bin" && method == "POST") {
            // E1: the measured eye classification — raw binary [u32 * N]
            // (0 sclera / 1 iris / 2 pupil), built by .tmp/eye_build.py's classifier.
            if (req_body.size() < 2092 * 4 || (req_body.size() % 4) != 0) {
                body = "{\"ok\":false,\"error\":\"need >=2092 u32\"}";
                content_type = "application/json";
            } else {
                const int32_t* src = reinterpret_cast<const int32_t*>(req_body.data());
                size_t n_cls = req_body.size() / 4;
                {
                    std::lock_guard<std::mutex> lk(g_frost_mutex);
                    g_frost_req = FrostReq{};
                    g_frost_req.kind = 3;
                    g_frost_req.data.assign(src, src + n_cls);
                    g_frost_pending = true; g_frost_applied = false;
                }
                std::unique_lock<std::mutex> lk(g_frost_mutex);
                bool ok = g_frost_cv.wait_for(lk, std::chrono::seconds(30), []{ return g_frost_applied; });
                body = (ok && g_frost_req.ok) ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"apply failed or timeout\"}";
                content_type = "application/json";
            }
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
        } else if (p == "/show" && method == "POST") {
            // THE STUDIO CLOCK (D1): the timeline's HTTP twin.
            // {"playing":bool, "time":T, "speed":S, "step":N} — step is N frames
            // of exactly 1/240 s relative to the current time (pause first to
            // step deterministically; the decree: every frame, not just extremes).
            if (g_engine) {
                if (req_body.find("\"playing\"") != std::string::npos) {
                    bool pl = get_bool(req_body, "playing", true);
                    g_engine->show_playing_.store(pl);
                    if (pl) g_engine->joints_owner_.store(0);   // C1: play hands the pose to the show
                }
                if (req_body.find("\"speed\"") != std::string::npos) {
                    double sp = get_double(req_body, "speed", 1.0);
                    if (sp > 0.0 && sp <= 16.0) g_engine->show_speed_.store(sp);
                }
                if (req_body.find("\"time\"") != std::string::npos) {
                    double t = get_double(req_body, "time", 0.0);
                    if (t < 0.0) t = 0.0;
                    g_engine->show_scrub_.store(t);
                }
                if (req_body.find("\"step\"") != std::string::npos) {
                    double n = get_double(req_body, "step", 0.0);
                    double t = g_engine->show_time_.load() + n / 240.0;
                    if (t < 0.0) t = 0.0;
                    g_engine->show_scrub_.store(t);
                }
            }
            body = std::string("{\"ok\":true,\"time\":")
                 + std::to_string(g_engine ? g_engine->show_time_.load() : 0.0) + "}";
            content_type = "application/json";
        } else if (p == "/show" && method == "GET") {
            if (g_engine) {
                double t = g_engine->show_time_.load();
                float per = g_engine->show_period();
                uint32_t nj = g_engine->show_joint_count();
                uint32_t cur = nj ? static_cast<uint32_t>(t / per) % nj : 0;
                body = std::string("{\"playing\":") + (g_engine->show_playing_.load() ? "true" : "false")
                     + ",\"time\":" + std::to_string(t)
                     + ",\"speed\":" + std::to_string(g_engine->show_speed_.load())
                     + ",\"n_joints\":" + std::to_string(nj)
                     + ",\"period\":" + std::to_string(per)
                     + ",\"total\":" + std::to_string(nj * static_cast<double>(per))
                     + ",\"current\":\"" + g_engine->show_joint_name(cur) + "\""
                     + ",\"theta\":" + std::to_string(g_engine->show_current_theta())
                     + ",\"joints_loaded\":" + (g_engine->joints_loaded() ? "true" : "false");
                float re_ = 0.f, rf_ = 0.f;
                g_engine->show_current_rom(re_, rf_);
                body += ",\"rom_ext\":" + std::to_string(re_)
                     +  ",\"rom_flex\":" + std::to_string(rf_) + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/reel" && method == "GET") {
            // D3: the grab ledger (newest first) — the dyad's evidence-tray channel
            body = g_engine ? g_engine->reel_json() : "{\"ok\":false,\"error\":\"no engine\"}";
            content_type = "application/json";
        } else if (p == "/studio" && method == "POST") {
            // THE ENGINE STUDIO: the F1 toggle's HTTP twin (agents can't press keys)
            if (g_engine) {
                bool on = get_bool(req_body, "on", !g_engine->ui_.visible);
                g_engine->ui_.visible = on;
            }
            body = std::string("{\"on\":") + ((g_engine && g_engine->ui_.visible) ? "true" : "false") + "}";
            content_type = "application/json";
        } else if (p == "/studio" && method == "GET") {
            // B3: the panel state for agents — visibility + the selected stage
            // + the layout space (synthetic clicks aim in client pixels)
            if (g_engine) {
                std::string sel = g_engine->ui_.selected_stage_id();
                body = std::string("{\"on\":") + (g_engine->ui_.visible ? "true" : "false")
                     + ",\"selected\":" + (sel.empty() ? "null" : "\"" + sel + "\"")
                     + ",\"left_mode\":" + std::to_string(g_engine->ui_.left_mode())
                     + ",\"lh\":" + std::to_string(g_engine->ui_.line_height())
                     + ",\"advance\":" + std::to_string(g_engine->ui_.advance())
                     + ",\"w\":" + std::to_string(g_engine->win_w())
                     + ",\"h\":" + std::to_string(g_engine->win_h()) + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/ui_click" && method == "POST") {
            // B3: a synthetic click, queued onto the render thread (the same
            // discipline as the WndProc's) — agents drive panels over HTTP.
            if (g_engine) {
                g_engine->queue_ui_click(static_cast<int>(get_float(req_body, "x", 0.0f)),
                                         static_cast<int>(get_float(req_body, "y", 0.0f)));
            }
            body = "{\"ok\":true}";
            content_type = "application/json";
        } else if (p == "/studio_doc" && method == "GET") {
            // E1: the docs browser's state for agents — which doc, its file
            // mtime, and the FNV-1a/64 of the bytes the panel holds. A probe
            // hashes the file itself; the two MUST match (verbatim = the law).
            if (g_engine) {
                char hb[32];
                snprintf(hb, sizeof(hb), "%016llx",
                         static_cast<unsigned long long>(g_engine->ui_.docs_fnv()));
                body = std::string("{\"doc\":") + std::to_string(g_engine->ui_.docs_current())
                     + ",\"path\":\"" + g_engine->ui_.docs_path() + "\""
                     + ",\"mtime\":" + std::to_string(static_cast<unsigned long long>(g_engine->ui_.docs_mtime()))
                     + ",\"fnv\":\"" + hb + "\""
                     + ",\"n_lines\":" + std::to_string(g_engine->ui_.docs_line_count())
                     + ",\"n_display\":" + std::to_string(g_engine->ui_.docs_display_count())
                     + ",\"scroll\":" + std::to_string(g_engine->ui_.docs_scroll())
                     + ",\"scroll_max\":" + std::to_string(g_engine->ui_.docs_scroll_max()) + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/studio_doc" && method == "POST") {
            // E1: agents can't drag — pick a doc ({"doc":i}) or land an exact
            // scroll ({"scroll":N}, clamped by the panel's own geometry).
            if (g_engine) {
                if (req_body.find("\"doc\"") != std::string::npos)
                    g_engine->ui_.docs_set(static_cast<int>(get_float(req_body, "doc", 0.0f)));
                if (req_body.find("\"scroll\"") != std::string::npos)
                    g_engine->ui_.docs_set_scroll(get_float(req_body, "scroll", 0.0f));
                body = std::string("{\"ok\":true,\"doc\":") + std::to_string(g_engine->ui_.docs_current())
                     + ",\"scroll\":" + std::to_string(g_engine->ui_.docs_scroll()) + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/studio_chrome" && method == "GET") {
            // F2/F3: the chrome's HTTP twin. The strings served here are the
            // SAME strings build_chrome() drew last frame — the twin cannot
            // drift from the glass. Live even with the overlay closed.
            if (g_engine) {
                const StudioUI& u = g_engine->ui_;
                // full precision where the twin's numbers feed a derivation —
                // std::to_string's 6 decimals would round the gait thetas and
                // break bit-exact lam checks downstream
                char dbuf[4][40];
                snprintf(dbuf[0], 40, "%.17g", u.hud_gait_.lamL);
                snprintf(dbuf[1], 40, "%.17g", u.hud_gait_.lamR);
                snprintf(dbuf[2], 40, "%.17g", u.hud_gait_.thL);
                snprintf(dbuf[3], 40, "%.17g", u.hud_gait_.thR);
                std::string ring;
                for (int i = 0; i < u.ft_ring_n_; ++i) {
                    float v = u.ft_ring_[(u.ft_ring_head_ - u.ft_ring_n_ + i + StudioUI::FT_RING)
                                         % StudioUI::FT_RING];
                    ring += (i ? "," : "") + std::to_string(v);
                }
                std::string rows;
                for (size_t i = 0; i < u.hud_rows_.size(); ++i) {
                    rows += (i ? "," : "");
                    rows += "\"" + u.hud_rows_[i] + "\"";
                }
                body = std::string("{\"bar_on\":") + (u.bar_on_ ? "true" : "false")
                     + ",\"bar_h\":" + std::to_string(StudioUI::BAR_H)
                     + ",\"fps\":" + std::to_string(u.fps_f())
                     + ",\"ft_avg\":" + std::to_string(u.ft_avg_f())
                     + ",\"ft_max\":" + std::to_string(u.ft_max_f())
                     + ",\"pushes\":" + std::to_string(static_cast<unsigned long long>(u.ft_pushes_))
                     + ",\"ring_n\":" + std::to_string(u.ft_ring_n_)
                     + ",\"ring\":[" + ring + "]"
                     + ",\"gpu\":\"" + u.gpu_name_ + "\""
                     + ",\"stage\":\"" + u.chrome_stage_ + "\""
                     + ",\"fps_str\":\"" + u.chrome_fps_ + "\""
                     + ",\"gpu_str\":\"" + u.chrome_gpu_ + "\""
                     + ",\"hud_rows\":[" + rows + "]"
                     + ",\"gait\":{\"on\":" + (u.hud_gait_.on ? std::string("true") : std::string("false"))
                     + ",\"lamL\":" + dbuf[0]
                     + ",\"lamR\":" + dbuf[1]
                     + ",\"thL\":" + dbuf[2]
                     + ",\"thR\":" + dbuf[3]
                     + ",\"steps\":" + std::to_string(static_cast<unsigned long long>(u.hud_gait_.steps))
                     + ",\"omega\":" + std::to_string(u.hud_gait_.omega) + "}"
                     + ",\"water\":{\"on\":" + (u.hud_water_.on ? std::string("true") : std::string("false"))
                     + ",\"steps\":" + std::to_string(static_cast<unsigned long long>(u.hud_water_.steps))
                     + ",\"dt\":" + std::to_string(u.hud_water_.dt)
                     + ",\"inj_t\":" + std::to_string(u.hud_water_.inj_t)
                     + ",\"inj_c\":" + std::to_string(u.hud_water_.inj_c) + "}"
                     + ",\"show_row\":" + (u.hud_show_on() ? "true" : "false") + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/studio_chrome" && method == "POST") {
            // F2: the bar's kill switch (default ON — "always visible" is the
            // ship state; the toggle exists so its cost is measurable and the
            // operator has an out).
            if (g_engine) {
                if (req_body.find("\"on\"") != std::string::npos)
                    g_engine->ui_.bar_on_ = get_bool(req_body, "on", true);
                body = std::string("{\"ok\":true,\"bar_on\":")
                     + (g_engine->ui_.bar_on_ ? "true" : "false") + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/console" && method == "GET") {
            // F1: the console's HTTP twin — what the glass shows, served
            if (g_engine) {
                const StudioUI& u = g_engine->ui_;
                auto jesc = [](const std::string& s) {   // the log holds raw JSON — escape it
                    std::string o; o.reserve(s.size() + 16);
                    for (char c : s) {
                        if (c == '"' || c == '\\') { o += '\\'; o += c; }
                        else if (c == '\n') o += "\\n";
                        else if (c == '\r') o += "\\r";
                        else if (c == '\t') o += "\\t";
                        else o += c;
                    }
                    return o;
                };
                std::string entries;
                size_t n = u.console_log_.size();
                size_t start = n > 50 ? n - 50 : 0;
                for (size_t i = start; i < n; ++i) {
                    const auto& e = u.console_log_[i];
                    entries += (i > start ? "," : "");
                    entries += std::string("{\"cmd\":\"") + jesc(e.cmd) + "\",\"done\":"
                             + (e.done ? "true" : "false") + ",\"resp\":\"" + jesc(e.resp) + "\"}";
                }
                body = std::string("{\"open\":") + (u.console_open_ ? "true" : "false")
                     + ",\"input\":\"" + jesc(u.console_input_) + "\""
                     + ",\"hist_n\":" + std::to_string(u.console_history_.size())
                     + ",\"pending\":" + std::to_string(g_engine->console_pending())
                     + ",\"log\":[" + entries + "]}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/console" && method == "POST") {
            // F1: a posted line enters the SAME path as a typed Enter —
            // history + scrollback + the worker queue. {"open":bool} sets the
            // console's visibility absolutely (agents can't send `).
            if (g_engine) {
                if (req_body.find("\"line\"") != std::string::npos)
                    g_engine->ui_.console_submit_line(get_string(req_body, "line"));
                if (req_body.find("\"open\"") != std::string::npos)
                    g_engine->ui_.console_open_ = get_bool(req_body, "open", true);
                body = std::string("{\"ok\":true,\"open\":")
                     + (g_engine->ui_.console_open_ ? "true" : "false") + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/log" && method == "GET") {
            // F4: the recorder's served tail — the file is the record; this is
            // its live edge. A probe diffs the two; they must never disagree.
            if (g_engine) {
                auto jesc = [](const std::string& s) {
                    std::string o; o.reserve(s.size() + 16);
                    for (char c : s) {
                        if (c == '"' || c == '\\') { o += '\\'; o += c; }
                        else if (c == '\n') o += "\\n";
                        else if (c == '\r') o += "\\r";
                        else if (c == '\t') o += "\\t";
                        else o += c;
                    }
                    return o;
                };
                const StudioUI& u = g_engine->ui_;
                std::string lines;
                {
                    std::lock_guard<std::mutex> lk(u.log_m_);
                    size_t n = u.log_ring_.size();
                    size_t start = n > 50 ? n - 50 : 0;
                    for (size_t i = start; i < n; ++i) {
                        const auto& e = u.log_ring_[i];
                        lines += (i > start ? "," : "");
                        lines += std::string("{\"seq\":") + std::to_string(e.seq)
                               + ",\"t\":\"" + e.t + "\",\"kind\":\"" + jesc(e.kind)
                               + "\",\"detail\":\"" + jesc(e.detail) + "\"}";
                    }
                }
                body = std::string("{\"file\":\"") + jesc(g_engine->log_file())
                     + "\",\"n\":" + std::to_string(g_engine->log_count())
                     + ",\"lines\":[" + lines + "]}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/log" && method == "POST") {
            // F4: an externally-posted gate verdict lands VERBATIM in the same
            // record as the engine's own events — kind "gate" by convention.
            if (g_engine) {
                std::string kind = get_string(req_body, "kind");
                std::string detail = get_string(req_body, "detail");
                if (kind.empty()) kind = "gate";
                g_engine->log_event(kind, detail);
                body = std::string("{\"ok\":true,\"seq\":")
                     + std::to_string(g_engine->log_count()) + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/scene" && method == "GET") {
            // C4: the outliner's HTTP twin. The rows are Engine::scene_rows() —
            // the ONE formatting site, identical to what the left dock draws.
            // The rects are the aim map for /ui_click (only meaningful while
            // the dock is in SCENE mode — served empty otherwise).
            if (g_engine) {
                auto jesc = [](const std::string& s) {
                    std::string o; o.reserve(s.size() + 16);
                    for (char c : s) {
                        if (c == '"' || c == '\\') { o += '\\'; o += c; }
                        else if (c == '\n') o += "\\n";
                        else if (c == '\r') o += "\\r";
                        else if (c == '\t') o += "\\t";
                        else o += c;
                    }
                    return o;
                };
                auto rows = g_engine->scene_rows();
                std::string rs;
                for (size_t i = 0; i < rows.size(); ++i) {
                    const auto& r = rows[i];
                    rs += (i ? "," : "");
                    rs += std::string("{\"id\":\"") + jesc(r.id) + "\",\"label\":\"" + jesc(r.label)
                        + "\",\"detail\":\"" + jesc(r.detail) + "\",\"state\":" + std::to_string(r.state)
                        + ",\"toggleable\":" + (r.toggleable ? "true" : "false") + "}";
                }
                std::string rects;
                if (g_engine->ui_.left_mode() == 4) {
                    const auto& sr = g_engine->ui_.scene_rects();
                    for (size_t i = 0; i < sr.size(); ++i) {
                        rects += (i ? "," : "");
                        char rb[128];
                        snprintf(rb, sizeof(rb), "[%.1f,%.1f,%.1f,%.1f]", sr[i][0], sr[i][1], sr[i][2], sr[i][3]);
                        rects += rb;
                    }
                }
                std::string srects;
                if (g_engine->ui_.left_mode() == 4) {
                    const auto& sr = g_engine->ui_.scene_sel_rects();
                    for (size_t i = 0; i < sr.size(); ++i) {
                        srects += (i ? "," : "");
                        char rb[128];
                        snprintf(rb, sizeof(rb), "[%.1f,%.1f,%.1f,%.1f]", sr[i][0], sr[i][1], sr[i][2], sr[i][3]);
                        srects += rb;
                    }
                }
                body = std::string("{\"left_mode\":") + std::to_string(g_engine->ui_.left_mode())
                     + ",\"inspect_row\":" + std::to_string(g_engine->inspect_row_.load())
                     + ",\"rows\":[" + rs + "],\"rects\":[" + rects + "]"
                     + ",\"sel_rects\":[" + srects + "]}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/scene" && method == "POST") {
            // C4: {"id":"gait","on":true} — routes through Engine::scene_exec,
            // i.e. the console's one path. The inner endpoint's own event is
            // what the F4 recorder logs; /scene itself is NOT a chokepoint kind
            // (a double-log would be a lie about what happened).
            if (g_engine) {
                std::string id = get_string(req_body, "id");
                bool on = get_bool(req_body, "on", true);
                std::string line = g_engine->scene_exec(id, on);
                auto jesc = [](const std::string& s) {
                    std::string o; o.reserve(s.size() + 16);
                    for (char c : s) { if (c == '"' || c == '\\') { o += '\\'; o += c; } else o += c; }
                    return o;
                };
                if (!line.empty())
                    body = std::string("{\"ok\":true,\"queued\":\"") + jesc(line) + "\"}";
                else
                    body = std::string("{\"ok\":false,\"error\":\"unknown or untoggleable id\"}");
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/inspect" && method == "GET") {
            // C2: the inspector's HTTP twin — the SAME inspect_kv() document
            // the right dock draws, composed fresh at read time.
            if (g_engine) {
                auto jesc = [](const std::string& s) {
                    std::string o; o.reserve(s.size() + 16);
                    for (char c : s) { if (c == '"' || c == '\\') { o += '\\'; o += c; } else o += c; }
                    return o;
                };
                int ir = g_engine->inspect_row_.load();
                if (ir < 0) {
                    body = "{\"row\":-1}";
                } else {
                    auto rows = g_engine->scene_rows();
                    auto kv = g_engine->inspect_kv(ir);
                    std::string ls;
                    for (size_t i = 0; i < kv.size(); ++i) {
                        ls += (i ? "," : "");
                        ls += std::string("{\"k\":\"") + jesc(kv[i].first)
                            + "\",\"v\":\"" + jesc(kv[i].second) + "\"}";
                    }
                    std::string id = (ir < static_cast<int>(rows.size())) ? rows[ir].id : "";
                    std::string label = (ir < static_cast<int>(rows.size())) ? rows[ir].label : "";
                    body = std::string("{\"row\":") + std::to_string(ir)
                         + ",\"id\":\"" + jesc(id) + "\",\"label\":\"" + jesc(label)
                         + "\",\"lines\":[" + ls + "]}";
                }
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/inspect" && method == "POST") {
            // C2: select ({"row":i} or {"id":"gait"}) / deselect ({"row":-1}).
            // Pure view state — no console path, no F4 event (nothing in the
            // scene changed; a log line here would claim an event that isn't).
            if (g_engine) {
                int row = -2;   // -2 = not specified
                if (req_body.find("\"row\"") != std::string::npos)
                    row = static_cast<int>(get_float(req_body, "row", -2.0f));
                else if (req_body.find("\"id\"") != std::string::npos) {
                    std::string id = get_string(req_body, "id");
                    auto rows = g_engine->scene_rows();
                    for (size_t i = 0; i < rows.size(); ++i)
                        if (rows[i].id == id) { row = static_cast<int>(i); break; }
                }
                if (row == -2) {
                    body = "{\"ok\":false,\"error\":\"need row or id\"}";
                } else {
                    int n = static_cast<int>(g_engine->scene_rows().size());
                    if (row < -1 || row >= n) {
                        body = "{\"ok\":false,\"error\":\"row out of range\"}";
                    } else {
                        g_engine->inspect_row_.store(row);
                        body = std::string("{\"ok\":true,\"row\":") + std::to_string(row) + "}";
                    }
                }
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/cameras" && method == "GET") {
            // D6: the bookmarks twin — the engine's store, verbatim (the glass
            // chips draw the same names in the same order).
            if (g_engine) {
                auto names = g_engine->cam_mark_names();
                std::string bs;
                for (size_t i = 0; i < names.size(); ++i) {
                    float v[8];
                    if (!g_engine->cam_mark_get(names[i], v)) continue;
                    char vb[256];
                    snprintf(vb, sizeof(vb), "[%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g]",
                             v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7]);
                    bs += (i ? "," : "");
                    bs += std::string("{\"name\":\"") + names[i] + "\",\"v\":" + vb + "}";
                }
                body = std::string("{\"bookmarks\":[") + bs + "]}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/cameras" && method == "POST") {
            // D6: {"op":"save","name":"x"} (live capture; name optional ->
            // auto camN) · {"op":"save","name":"x","v":[8]} (exact numbers —
            // an AI frames a shot from a derivation) · {"op":"recall",
            // "name":"x"} (applies all 8 through the membrane request, the
            // render-thread discipline) · {"op":"delete","name":"x"}.
            if (g_engine) {
                std::string op = get_string(req_body, "op");
                std::string name = get_string(req_body, "name");
                if (op == "save") {
                    size_t vp = req_body.find("\"v\"");
                    if (vp != std::string::npos) {
                        size_t lb = req_body.find('[', vp);
                        float v[8];
                        if (lb != std::string::npos &&
                            sscanf(req_body.c_str() + lb + 1, "%f,%f,%f,%f,%f,%f,%f,%f",
                                   &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], &v[6], &v[7]) == 8 &&
                            g_engine->cam_mark_save_exact(name, v)) {
                            body = std::string("{\"ok\":true,\"name\":\"") + name + "\"}";
                        } else {
                            body = "{\"ok\":false,\"error\":\"bad v (need 8 floats) or empty name\"}";
                        }
                    } else {
                        std::string nm = g_engine->cam_mark_save(name);
                        body = std::string("{\"ok\":true,\"name\":\"") + nm + "\"}";
                    }
                } else if (op == "recall") {
                    float v[8];
                    if (!g_engine->cam_mark_get(name, v)) {
                        body = "{\"ok\":false,\"error\":\"no such bookmark\"}";
                    } else {
                        {
                            std::lock_guard<std::mutex> lk(g_mem_mutex);
                            memcpy(g_mem_req.cam_full, v, sizeof(v));
                            g_mem_req.cam_full_set = true;
                            g_mem_req.valid = true;
                            g_mem_pending = true;
                            g_mem_applied = false;
                        }
                        std::unique_lock<std::mutex> lk(g_mem_mutex);
                        bool ok = g_mem_cv.wait_for(lk, std::chrono::seconds(3), []{ return g_mem_applied; });
                        body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                    }
                } else if (op == "delete") {
                    body = g_engine->cam_mark_delete(name)
                         ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"no such bookmark\"}";
                } else {
                    body = "{\"ok\":false,\"error\":\"op must be save|recall|delete\"}";
                }
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/debug" && method == "GET") {
            body = "{\"n\":" + std::to_string(g_engine ? g_engine->particle_count() : 0)
                 + ",\"active\":" + (g_membrane_active ? "true" : "false") + "}";
            content_type = "application/json";
        } else {
            body = "Not found";
        }

        // F4: the recorder — every covered state change lands at the moment it
        // happens, with its OUTCOME (the response body is the truth of what
        // happened; a logged success for a failed event would be a lie).
        if (g_engine && method == "POST") {
            const char* kind = nullptr;
            if (p == "/mesh_bin" || p == "/hinge_bin" || p == "/joints_bin" ||
                p == "/gait_bin" || p == "/water_bin") kind = "upload";
            else if (p == "/show" || p == "/joints" || p == "/gait" ||
                     p == "/water_clock" || p == "/studio" ||
                     p == "/studio_chrome") kind = "mode";
            else if (p == "/joint") kind = "intent";
            if (kind) {
                std::string d = method + " " + p + " " +
                                std::to_string(req_body.size()) + "B";
                if (p == "/joint") {   // the response omits WHICH joint — the
                    std::string j = get_string(req_body, "joint");   // record
                    if (!j.empty()) d += " joint=" + j;              // must not
                }
                g_engine->log_event(kind, d + " -> " + body);
            }
        }
    };
    bool http_ok = server.start(http_port, api);
    engine.set_api(api);   // F1: the console's worker runs the SAME handler
    if (!http_ok) {
        fprintf(stderr, "Warning: Failed to start HTTP server on port %d\n", http_port);
    }

    printf("Chimera Engine running at http://localhost:%d/state\n", http_port);
    printf("  /frame  -> PNG of the current render (membrane if one is loaded)\n");
    printf("  /membrane (POST) -> load a story membrane scene\n");
    printf("Window: %ux%u, Press Ctrl+C to stop.\n", cfg.width, cfg.height);
    printf("Controls: Left-drag orbit | Scroll zoom | Right-drag pan\n");
    printf("          WASD move | Q/E up-down | Space/Ctrl zoom | R reset | P pose toggle\n");
    printf("          F1 THE ENGINE STUDIO overlay (pipeline board + live status)\n");

#ifdef _WIN32
    SetConsoleCtrlHandler(handleCtrlC, TRUE);
#else
    signal(SIGINT, handleSignal);
    signal(SIGTERM, handleSignal);
#endif

    // Main loop — hybrid GPU compute / CPU integrate (or membrane display)
    auto last_time = std::chrono::high_resolution_clock::now();
    int frame_count = 0;
    double ft_sum = 0.0, ft_max = 0.0;   // frame-stutter instrument (per-second window)
    int ft_over16 = 0, ft_over33 = 0;
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
                if (g_mem_req.cam_full_set) {          // D6: a bookmark recall — all 8 floats
                    engine.set_camera_full(g_mem_req.cam_full);
                    g_mem_req.cam_full_set = false;
                } else if (g_mem_req.camera_only) {
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
                if (g_mesh_req.update_only) {
                    engine.update_mesh(g_mesh_req.verts, g_mesh_req.N);
                } else if (g_mesh_req.slot == 1) {
                    engine.load_overlay(g_mesh_req.verts, g_mesh_req.indices, g_mesh_req.N, g_mesh_req.idxCount);
                } else {
                    engine.load_mesh(g_mesh_req.verts, g_mesh_req.indices, g_mesh_req.N, g_mesh_req.idxCount);
                    engine.set_mesh_mode(g_mesh_req.mode);
                }
                // cam_radius <= 0 = "keep the current camera": animation drivers stream
                // meshes every frame and must NOT steal the operator's orbit/zoom/pan.
                if (!g_mesh_req.update_only && g_mesh_req.cam_radius > 0.0f)
                    engine.set_camera(g_mesh_req.cam_radius, g_mesh_req.cam_theta, g_mesh_req.cam_phi);
                g_mesh_req.update_only = false;
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

        // Apply a pending hinge request (Vulkan work must stay on this thread)
        {
            std::lock_guard<std::mutex> lk(g_hinge_mutex);
            if (g_hinge_pending) {
                if (g_hinge_req.n == 0) {
                    engine.stop_hinge();
                } else {
                    engine.set_hinge(g_hinge_req.wL, g_hinge_req.wR,
                                     g_hinge_req.JL, g_hinge_req.JR, g_hinge_req.axis,
                                     g_hinge_req.romL, g_hinge_req.romR,
                                     g_hinge_req.period, g_hinge_req.phaseR);
                }
                g_hinge_pending = false; g_hinge_applied = true; g_hinge_cv.notify_all();
            }
        }

        // Apply a pending gait request (Vulkan work must stay on this thread)
        {
            std::lock_guard<std::mutex> lk(g_gait_mutex);
            if (g_gait_pending) {
                if (g_gait_req.kind == 1) {
                    g_gait_req.ok = engine.load_gait(g_gait_req.consts, g_gait_req.edges,
                                                     g_gait_req.phi0, g_gait_req.theta0);
                    g_gait_req.consts.clear(); g_gait_req.consts.shrink_to_fit();
                } else {
                    g_gait_req.ok = engine.gait_download(g_gait_req.ring);
                }
                g_gait_pending = false; g_gait_applied = true; g_gait_cv.notify_all();
            }
        }

        // Apply a pending volp request (Vulkan work must stay on this thread)
        {
            std::lock_guard<std::mutex> lk(g_volp_mutex);
            if (g_volp_pending) {
                if (g_volp_req.kind == 1) {
                    g_volp_req.ok = engine.load_volp(g_volp_req.blob);
                    g_volp_req.blob.clear(); g_volp_req.blob.shrink_to_fit();
                } else if (g_volp_req.kind == 3) {
                    g_volp_req.ok = engine.load_joints(g_volp_req.blob);
                    g_volp_req.blob.clear(); g_volp_req.blob.shrink_to_fit();
                } else {
                    g_volp_req.ok = engine.volp_download_mesh(g_volp_req.mesh);
                }
                g_volp_pending = false; g_volp_applied = true; g_volp_cv.notify_all();
            }
        }

        // Apply a pending water request (Vulkan work must stay on this thread)
        {
            std::lock_guard<std::mutex> lk(g_water_mutex);
            if (g_water_pending) {
                if (g_water_req.kind == 1) {
                    g_water_req.ok = engine.load_water(g_water_req.up);
                } else if (g_water_req.kind == 2) {
                    g_water_req.ok = engine.water_run(g_water_req.n_macro, g_water_req.dt,
                                                      g_water_req.sum, g_water_req.mn);
                } else if (g_water_req.kind == 4) {
                    g_water_req.ok = engine.water_vis_debug(g_water_req.states, 512);
                } else {
                    g_water_req.ok = engine.water_download(g_water_req.states,
                                                           g_water_req.ns, g_water_req.nc);
                }
                g_water_pending = false; g_water_applied = true; g_water_cv.notify_all();
            }
        }

        // Apply a pending frost request (Vulkan work must stay on this thread).
        // kind 2 (snapshot) only ARMS here — it completes after the next frame
        // (below), once the debug dispatch + readback copies have been recorded.
        {
            std::lock_guard<std::mutex> lk(g_frost_mutex);
            if (g_frost_pending) {
                if (g_frost_req.kind == 1) {
                    g_frost_req.ok = engine.load_frost(g_frost_req.blob.data(),
                                                       g_frost_req.blob.size());
                    g_frost_req.blob.clear();
                    g_frost_req.blob.shrink_to_fit();
                    g_frost_pending = false; g_frost_applied = true; g_frost_cv.notify_all();
                } else if (g_frost_req.kind == 2) {
                    engine.frost_dbg_arm_.store(true);
                    // leave pending: completed after engine.frame() below
                } else if (g_frost_req.kind == 3) {
                    // E1: the eye-class upload (2092 u32 packed in `data`)
                    std::vector<uint32_t> cls(g_frost_req.data.begin(), g_frost_req.data.end());
                    g_frost_req.ok = engine.set_eye_class(cls);
                    g_frost_req.data.clear(); g_frost_req.data.shrink_to_fit();
                    g_frost_pending = false; g_frost_applied = true; g_frost_cv.notify_all();
                }
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

        // Render one frame (timed — the frame-stutter instrument)
        auto ft0 = std::chrono::high_resolution_clock::now();
        if (!engine.frame()) {
            fprintf(stderr, "Frame failed\n");
            break;
        }
        auto ft1 = std::chrono::high_resolution_clock::now();

        // Complete an armed frost snapshot: the frame just submitted recorded the
        // debug dispatch + readback copies; drain and hand the data back.
        if (engine.frost_snapshot_pending()) {
            std::vector<int32_t> snap;
            bool ok = engine.frost_finish_snapshot(snap);
            std::lock_guard<std::mutex> lk(g_frost_mutex);
            g_frost_req.ok = ok;
            if (ok) g_frost_req.data = std::move(snap);
            g_frost_pending = false; g_frost_applied = true; g_frost_cv.notify_all();
        }
        // B5: nothing loaded -> frame() returns immediately; pace the loop or it
        // spins a core at millions of FPS doing literally nothing.
        if (engine.idle()) Sleep(8);

        // Frame-time stats: averages hide stutter; spikes are the complaint.
        double ft_ms = std::chrono::duration_cast<std::chrono::microseconds>(ft1 - ft0).count() / 1e3;
        ft_sum += ft_ms;
        if (ft_ms > ft_max) ft_max = ft_ms;
        if (ft_ms > 16.7) ft_over16++;
        if (ft_ms > 33.3) ft_over33++;
        // F2: every frame's time lands on the status bar's histogram ring
        engine.ui_.push_frame_time(static_cast<float>(ft_ms));

        // Frame cap (frame-stutter fix): uncapped, the engine free-ran at 300-1800 FPS
        // and fought llama-server (65%% GPU) for every slice — each inference burst
        // delayed frames unpredictably = the stutter. A metronome at 144 FPS yields
        // the GPU predictably and paces display delivery. timeBeginPeriod(1) is set
        // in main() so these short sleeps land at ~1 ms granularity, not 15.6.
        {
            const double target_ms = 1000.0 / 300.0;
            double busy_ms = std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::high_resolution_clock::now() - ft0).count() / 1e3;
            if (busy_ms < target_ms) {
                double rem = target_ms - busy_ms;
                if (rem > 2.0) Sleep((DWORD)(rem - 1.0));
                while (std::chrono::duration_cast<std::chrono::microseconds>(
                       std::chrono::high_resolution_clock::now() - ft0).count() / 1e3 < target_ms) {}
            }
        }

        // No frame-rate cap — the loop is GPU-bound: the per-frame fence wait + MAILBOX present
        // mode let the renderer run as fast as the GPU finishes each frame ("unlimited" fps).
        frame_count++;

        auto now = std::chrono::high_resolution_clock::now();
        double elapsed_s = std::chrono::duration_cast<std::chrono::microseconds>(now - last_time).count() / 1e6;
        if (elapsed_s >= 1.0) {
            double fps_now = frame_count / elapsed_s;
            double ft_avg_now = frame_count ? ft_sum / frame_count : 0.0;
            printf("FPS: %.0f (frame %d) | ft ms avg %.2f max %.2f | >16.7ms: %d >33ms: %d\n",
                   fps_now, frame_count, ft_avg_now, ft_max, ft_over16, ft_over33);
            fflush(stdout);

            // THE STUDIO: feed the STATUS panel the engine's own live rows
            // (1 Hz is enough — the panel is an honest readout, not an oscilloscope)
            if (g_engine) {
                g_engine->ui_.set_fps(static_cast<float>(fps_now),
                                      static_cast<float>(ft_avg_now), static_cast<float>(ft_max));
                std::vector<std::string> lines;
                char lb[192];
                snprintf(lb, sizeof(lb), "mesh: %s | splats: %u",
                         "see viewport", g_engine->particle_count());
                lines.push_back(lb);
                snprintf(lb, sizeof(lb), "hinge: %s", g_engine->hinge_active() ? "ACTIVE" : "off");
                lines.push_back(lb);
                snprintf(lb, sizeof(lb), "joints show: %s%s", g_engine->joints_loaded() ? "loaded" : "no pack",
                         g_engine->joints_on_.load() ? " | LIVE" : "");
                lines.push_back(lb);
                snprintf(lb, sizeof(lb), "gait CPG: %s%s | steps %llu",
                         g_engine->gait_loaded() ? "loaded" : "no pack",
                         g_engine->gait_on_.load() ? " | RUNNING" : "",
                         (unsigned long long)g_engine->gait_steps_total_.load());
                lines.push_back(lb);
                snprintf(lb, sizeof(lb), "water clock: %s | macro steps %llu",
                         g_engine->water_clock_on_.load() ? "RUNNING" : "off",
                         (unsigned long long)g_engine->water_clock_steps_total_.load());
                lines.push_back(lb);
                snprintf(lb, sizeof(lb), "volp-ARAP: %s | mode %s",
                         g_engine->volp_loaded() ? "loaded" : "no pack",
                         g_engine->volp_mode_.load() == 1 ? "volp" : "blend");
                lines.push_back(lb);
                snprintf(lb, sizeof(lb), "frost decode: %s | frames %llu",
                         g_engine->frost_on_.load() ? "ON" : "off",
                         (unsigned long long)g_engine->frost_frame_.load());
                lines.push_back(lb);
                g_engine->ui_.set_status_lines(lines);
            }

            frame_count = 0;
            last_time = now;
            ft_sum = ft_max = 0.0; ft_over16 = ft_over33 = 0;
        }
    }

    printf("Shutting down...\n");
    engine.shutdown();
    return 0;
}
