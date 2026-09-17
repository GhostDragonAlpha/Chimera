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
#include "membrane_tick.hpp"
#include "graph_surface.hpp"
#include "graph_thermal.hpp"
#include "graph_earth.hpp"
#include "importer.hpp"    // C1: /mesh_import (the aliveness law ingestion)

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cctype>
#include <cmath>
#include <fstream>
#include <iterator>
#include <thread>
#include <chrono>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <string>
#include <algorithm>
#include <atomic>

static Engine* g_engine = nullptr;
static Physics g_physics;
static GraphSurface g_science_surface;
static std::mutex g_science_mutex;
static GraphThermal g_thermal;
static GraphEarth g_earth;
static std::mutex g_thermal_frame_mutex;
static std::map<uint64_t,GraphThermal::J> g_thermal_frames;
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
    bool cam_full_set = false;       // true: apply all 8, ignore the r/theta/phi fields
    bool camera_only = false;         // true: only move the camera, keep the loaded membrane
    bool valid = false;
};
// 2026-09-05 (the dyad's F3 + shader-issue): the global g_mem_req's camera slots
// were left with default-init indeterminate values; when a membrane POST hands the
// request off and the 3s pending expires mid-transition, the pending render thread
// consumes the stale g_mem_req.cam_theta (which can be anything in [0, 2pi]),
// producing the transient CAM-lock reset to ~pi observed by the dyad. The fix: zero
// the request's camera slots at declaration (the kind values are always the pending
// render thread's fallback, not the operator's gaze).
static MembraneRequest g_mem_req;
static std::mutex g_mem_mutex;
static std::condition_variable g_mem_cv;
static bool g_mem_pending = false;
static bool g_mem_applied = false;
static bool g_membrane_active = true;  // 3DGS-only: the N-body sim (7-float) is retired

// ── Pending GPU membrane-demo request (Vulkan work remains on the render thread)
// Binary layout, little-endian: MD01 magic, nv, nf, centre, gamma f64, lift f32,
// reserved u32 (32-byte header), then positions f32[nv*3], indices u32[nf*3],
// CSR offsets u32[nv+1], CSR corner ids u32[nf*3], gamma f32[nf].
struct MembraneDemoRequest {
    int kind = 0;       // 1 init, 2 control, 3 status
    int ctl_kind = 0;   // 0 reset, 1 step, 2 run, 3 pause, 4 gamma, 5 reject
    Engine::MembraneDemoUpload upload;
    uint32_t n_steps = 0;
    double gamma = 0.0;
    Engine::MembraneDemoStatus status{};
    bool ok = false;
};
static MembraneDemoRequest g_md_req;
static std::mutex g_md_mutex;
static std::condition_variable g_md_cv;
static bool g_md_pending = false, g_md_applied = false;

// ── Pending triangle mesh request (same handoff: Vulkan work stays on the render thread) ──
struct MeshReq { std::vector<float> verts; std::vector<uint32_t> indices; uint32_t N=0, idxCount=0; float cam_radius=12.f, cam_theta=0.f, cam_phi=0.3f; uint32_t slot=0, mode=0; bool update_only=false; bool valid=false; };
static MeshReq g_mesh_req;
static MembraneTick g_tick;                    // THE MEMBRANE TICK (Appliance 1)

// THE SESSION SNAPSHOT list, shared by status/restore/clear: order matters
// (mesh first, then the tick payloads their sizes verify against, then the
// other uploads). /tick_seal has no single blob — its INTENTS append to
// session_snapshot/tick_seal_history.log and replay in order, so the whole
// cell tree comes back exactly as authored. tick_seal_state is the tree's
// own STATE blob (R-restore-doctor): it loads before the history replay so
// a boot whose tree already round-trips executes ZERO seals — every
// history entry then answers "already satisfied" — and it sits LAST in the
// replay order because load_seal_state validates against the loaded mesh.
static const char* const k_snapshot_endpoints[] = {
    "mesh_bin", "tick_joints", "tick_classify", "tick_vertbind",
    "hinge_bin", "joints_bin", "gait_bin", "stride_bin", "water_bin",
    "tick_body_bin", "tick_seal_state",
    // AN2: the limb registry (segments + patch regions/constants) and the
    // patch states (arm + per-path connection + cut stamps) restore after
    // the seal tree they index into. A stale limb blob (any mesh change)
    // refuses -- the staleness is visible, never silent.
    "tick_limb_state", "tick_patch_state",
};
static std::vector<float> g_tick_verts;        // host mirror the tick tints
static uint32_t g_tick_vcount = 0;
// THE REPLAY JOURNAL GATE (R-restore-doctor): the snapshot write-through
// at the bottom of the api lambda fires for EVERY successful POST it
// sees — including the NESTED invoke_api calls the restore replay makes —
// so every boot over the same snapshot re-appended its successfully
// replayed seals to tick_seal_history.log (measured 60 -> 63 -> 66 -> 69
// lines across R-after's single boot). The replay runs on ONE thread and
// invoke_api is a nested call on that same thread, so a thread-local flag
// suppresses journaling for exactly the replayed calls while the
// operator's live POSTs (HTTP worker threads) still journal.
static thread_local bool g_replay_in_flight = false;
struct ReplayJournalGuard {
    ReplayJournalGuard()  { g_replay_in_flight = true; }
    ~ReplayJournalGuard() { g_replay_in_flight = false; }
};
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
// MSVC's %.6g prints non-finite floats as "nan"/"inf"/"-inf" — bare tokens that
// are ILLEGAL in JSON. Physics particles reach deep-space values within minutes,
// so every /state fetch was malformed JSON past that point (measured 2026-09-03:
// a deterministic cut at 104948 chars that full-parse clients died on). JSON's
// own name for the value is the fix: null is legal, "nan" is a lie.
static std::string fmt_float(float f) {
    char buf[32];
    if (f != f || f >= HUGE_VALF || f <= -HUGE_VALF)
        return "null";
    if (f == static_cast<float>(static_cast<int>(f)))
        sprintf(buf, "%d", static_cast<int>(f));
    else
        sprintf(buf, "%.6g", f);
    return std::string(buf);
}

static size_t find_colon_after(const std::string& body, const char* key) {
    // GLM-GPU-DEMO-02 fix: the FIRST textual occurrence of "key" may be a
    // VALUE, not a name ({"op":"gamma","gamma":2.0} shadowed the real
    // "gamma": member and get_double silently returned its default 0.0,
    // which md_admit_gamma legally admitted as a zero material). Scan all
    // occurrences and accept the first one that is actually followed by
    // ':'. The closing-quote guard rejects longer names that merely share
    // the key as a prefix ("n_steps" vs "n_steps_x").
    std::string needle = std::string("\"") + key + "\"";
    size_t pos = 0;
    while ((pos = body.find(needle, pos)) != std::string::npos) {
        size_t after_quote = pos + needle.size();
        if (after_quote < body.size() && body[after_quote] == '"') {
            pos = after_quote;
            continue;   // prefix of a longer name; keep scanning
        }
        size_t after_key = after_quote;
        while (after_key < body.size() && (body[after_key] == ' ' || body[after_key] == '\t')) ++after_key;
        if (after_key < body.size() && body[after_key] == ':') return after_key + 1;
        pos = after_quote;   // value occurrence; keep scanning
    }
    return std::string::npos;
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

// C1r: boolean body fields WITHOUT stod. std::stod("true") THROWS (the
// documented stod-on-booleans trap) and the catch silently returns the
// default -- a cut-nerve request that flips itself back on. The value's
// own first character is the truth: 't' -> true, 'f' -> false, anything
// else -> the default.
static bool get_bool(const std::string& body, const char* key, bool def) {
    size_t p = find_colon_after(body, key);
    if (p == std::string::npos) return def;
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (p >= body.size()) return def;
    if (body[p] == 't') return true;
    if (body[p] == 'f') return false;
    return def;
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

static std::string membrane_demo_status_json(const Engine::MembraneDemoStatus& s, bool ok) {
    char b[2048];
    snprintf(b, sizeof(b),
        "{\"ok\":%s,\"active\":%s,\"iteration\":%u,\"accepted\":%u,\"trials\":%u,\"energy\":%.9g,\"energy_initial\":%.9g,\"terminal_state\":\"%s\",\"centre\":[%.9g,%.9g,%.9g],\"centre_force\":[%.9g,%.9g,%.9g],\"accepted_state_id\":%llu,\"render_state_id\":%llu,\"last_control\":\"%s\",\"material_snapshot\":%s}",
        ok ? "true" : "false", s.active ? "true" : "false",
        s.iteration, s.n_accepted, s.n_trials, s.energy, s.energy_initial,
        s.terminal_state.c_str(), s.centre[0], s.centre[1], s.centre[2],
        s.centre_force[0], s.centre_force[1], s.centre_force[2],
        static_cast<unsigned long long>(s.accepted_state_id),
        static_cast<unsigned long long>(s.render_state_id),
        s.last_control.c_str(), s.material_snapshot.empty() ? "null" : s.material_snapshot.c_str());
    return b;
}

// Signal handler for graceful shutdown
struct ShutdownCancellation {};
static std::atomic<bool> g_shutdown_closing{false};
#ifdef CHIMERA_SHUTDOWN_TEST
static std::atomic<bool> g_shutdown_test_boot_waiting{false};
#endif

template <class Condition, class Lock, class Rep, class Period, class Predicate>
static bool wait_for_shutdown(Condition& cv, Lock& lock,
                              const std::chrono::duration<Rep, Period>& timeout,
                              Predicate predicate) {
#ifdef CHIMERA_SHUTDOWN_TEST
    printf("shutdown_test: wait_entered\n");
    fflush(stdout);
#endif
    cv.wait_for(lock, timeout, [&] {
        return predicate() || g_shutdown_closing.load(std::memory_order_acquire);
    });
    // The render thread owns the applied flag under this same channel mutex.
    // Recheck it while still holding the caller's lock so cancellation cannot
    // turn an already-applied request into a false cancellation.
    if (g_shutdown_closing.load(std::memory_order_acquire) && !predicate())
        throw ShutdownCancellation{};
    return predicate();
}

template <class Mutex, class Condition>
static void notify_shutdown(Mutex& mutex, Condition& cv) {
    std::lock_guard<Mutex> lock(mutex);
    cv.notify_all();
}

static bool wait_for_shutdown_delay(std::mutex& mutex, std::condition_variable& cv,
                                    const std::atomic<bool>& cancel,
                                    std::chrono::milliseconds delay) {
    std::unique_lock<std::mutex> lock(mutex);
#ifdef CHIMERA_SHUTDOWN_TEST
    g_shutdown_test_boot_waiting.store(true, std::memory_order_release);
    printf("shutdown_test: boot_wait_entered\n");
    fflush(stdout);
#endif
    return cv.wait_for(lock, delay, [&] {
        return cancel.load(std::memory_order_acquire)
            || g_shutdown_closing.load(std::memory_order_acquire);
    });
}

static void notify_shutdown_channels() {
    notify_shutdown(g_mem_mutex, g_mem_cv);
    notify_shutdown(g_md_mutex, g_md_cv);
    notify_shutdown(g_mesh_mutex, g_mesh_cv);
    notify_shutdown(g_hinge_mutex, g_hinge_cv);
    notify_shutdown(g_water_mutex, g_water_cv);
    notify_shutdown(g_gait_mutex, g_gait_cv);
    notify_shutdown(g_volp_mutex, g_volp_cv);
    notify_shutdown(g_frost_mutex, g_frost_cv);
    notify_shutdown(g_skin_mutex, g_skin_cv);
}

#ifdef _WIN32
BOOL WINAPI handleCtrlC(DWORD) {
    g_shutdown_closing.store(true, std::memory_order_release);
    return TRUE;
}
#else
void handleSignal(int) {
    g_shutdown_closing.store(true, std::memory_order_release);
}
#endif

// ═══ F2 BEGIN: /frame fast path helpers — WIC JPEG + box downscale ═════════════════
// Prereg (Rule 0, written BEFORE this code): docs/evidence/agent_fleet/
// MATTER_KERNEL/SEAL_PREREGISTRATION.md, section "F2: /FRAME FAST PATH".
// STATEMENT — a preview-quality fast path serves /frame in <= 200 ms.
// DERIVATION — the floor is the stored-deflate PNG encoder (a second 14.7 MB
// copy + bitwise CRC32 + Adler-32 over the full 2560x1440 buffer), so the
// honest wins are JPEG (in-box WIC, no new libs) at ?q=, and the downscale
// BEFORE encode so the encoder never sees the full buffer.
// FALSIFIER — the fast path > 400 ms, or q85 artifacts the eye can see, or
// the default PNG route's bytes change. Named successor: render-thread-side
// staged downscale (engine.cpp surgery — not this file's to make).
#include <wincodec.h>
#include <objbase.h>
#include <ocidl.h>
#include <oleauto.h>
#pragma comment(lib, "windowscodecs.lib")
#pragma comment(lib, "ole32.lib")

namespace f2 {

// Unsigned int query param ("w=", "q=") — find-after-'?', exactly the
// hand-rolled parse this replaces. 0 when absent.
inline uint32_t query_uint(const std::string& path, const char* key) {
    size_t q = path.find('?');
    if (q == std::string::npos) return 0;
    size_t k = path.find(key, q);
    if (k == std::string::npos) return 0;
    return static_cast<uint32_t>(strtoul(path.c_str() + k + strlen(key), nullptr, 10));
}

inline bool query_has(const std::string& path, const char* needle) {
    size_t q = path.find('?');
    return q != std::string::npos && path.find(needle, q) != std::string::npos;
}

// Box (area-average) downscale — same integer geometry as the nearest-skip
// this replaces (step = w/want_w, nw = w/step, nh = h/step), so ?w= serves
// the same SIZE it always did, just averaged instead of point-sampled.
// Reads the full buffer, writes only nw*nh*4 (~2.4 MB at w=1024): a few ms.
inline void box_downscale(const std::vector<uint8_t>& src, uint32_t w, uint32_t h,
                          std::vector<uint8_t>& dst, uint32_t& nw, uint32_t& nh,
                          uint32_t want_w) {
    uint32_t step = w / want_w;
    if (step < 1) step = 1;
    nw = w / step;
    nh = h / step;
    dst.assign(static_cast<size_t>(nw) * nh * 4, 0);
    const float inv = 1.0f / static_cast<float>(step * step);
    for (uint32_t y = 0; y < nh; ++y) {
        for (uint32_t x = 0; x < nw; ++x) {
            float acc[4] = {0.f, 0.f, 0.f, 0.f};
            for (uint32_t sy = 0; sy < step; ++sy) {
                const uint8_t* row = src.data() + static_cast<size_t>(y * step + sy) * w * 4;
                for (uint32_t sx = 0; sx < step; ++sx) {
                    const uint8_t* p = row + static_cast<size_t>(x * step + sx) * 4;
                    acc[0] += p[0]; acc[1] += p[1]; acc[2] += p[2]; acc[3] += p[3];
                }
            }
            uint8_t* d = &dst[(static_cast<size_t>(y) * nw + x) * 4];
            d[0] = static_cast<uint8_t>(acc[0] * inv + 0.5f);
            d[1] = static_cast<uint8_t>(acc[1] * inv + 0.5f);
            d[2] = static_cast<uint8_t>(acc[2] * inv + 0.5f);
            d[3] = static_cast<uint8_t>(acc[3] * inv + 0.5f);
        }
    }
}

// Baseline JPEG through Windows Imaging Component (in-box, no new libs).
// Alpha is dropped (JPEG has none). Returns false if COM/WIC refuses — the
// caller falls back to the PNG path, so the route serves an IMAGE, never an
// error body, even on WIC failure. COM init is per-thread and the HTTP
// server serves every request on ONE accept thread, so the first fmt=jpg
// request pays the init once and it holds for the process lifetime.
inline bool jpeg_encode_wic(const uint8_t* rgba, uint32_t w, uint32_t h,
                            uint32_t quality /*1..100*/, std::vector<uint8_t>& out) {
    out.clear();
    HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) return false;
    const bool must_uninit = SUCCEEDED(hr);
    bool ok = false;
    IWICImagingFactory* fac = nullptr;
    IStream* stream = nullptr; // CreateStreamOnHGlobal hands back an IStream*;
                               // enc->Initialize(stream, ...) takes IStream* too.
    IWICBitmapEncoder* enc = nullptr;
    IWICBitmapFrameEncode* frame = nullptr;
    IPropertyBag2* bag = nullptr;
    IWICBitmap* bmp = nullptr;
    IWICFormatConverter* conv = nullptr;
    do {
        if (FAILED(CoCreateInstance(CLSID_WICImagingFactory, nullptr,
                                    CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&fac)))) break;
        if (FAILED(CreateStreamOnHGlobal(nullptr, TRUE, &stream))) break;
        if (FAILED(fac->CreateEncoder(GUID_ContainerFormatJpeg, nullptr, &enc))) break;
        if (FAILED(enc->Initialize(stream, WICBitmapEncoderNoCache))) break;
        if (FAILED(enc->CreateNewFrame(&frame, &bag))) break;
        if (bag) {
            // the JPEG encoder option "ImageQuality" is a VT_R4 in [0,1]
            PROPBAG2 opt{};
            opt.pstrName = const_cast<LPOLESTR>(L"ImageQuality");
            VARIANT v;
            VariantInit(&v);
            v.vt = VT_R4;
            v.fltVal = static_cast<float>(quality) / 100.0f;
            bag->Write(1, &opt, &v);
            VariantClear(&v);
        }
        if (FAILED(frame->Initialize(bag))) break;
        const size_t bytes = static_cast<size_t>(w) * h * 4;
        // WIC's CreateBitmapFromMemory takes a non-const BYTE* (it predates
        // const-correct COM); rgba is read-only input here, so the const is
        // cast, never written through.
        if (FAILED(fac->CreateBitmapFromMemory(w, h, GUID_WICPixelFormat32bppRGBA,
                                               w * 4, static_cast<UINT>(bytes),
                                               reinterpret_cast<BYTE*>(const_cast<uint8_t*>(rgba)),
                                               &bmp))) break;
        if (FAILED(fac->CreateFormatConverter(&conv))) break;
        if (FAILED(conv->Initialize(bmp, GUID_WICPixelFormat32bppBGR,
                                    WICBitmapDitherTypeNone, nullptr, 0.0,
                                    WICBitmapPaletteTypeCustom))) break;
        if (FAILED(frame->SetSize(w, h))) break;
        if (FAILED(frame->WriteSource(conv, nullptr))) break;
        if (FAILED(frame->Commit())) break;
        if (FAILED(enc->Commit())) break;
        STATSTG st{};
        if (FAILED(stream->Stat(&st, STATFLAG_NONAME))) break;
        const ULONGLONG n64 = st.cbSize.QuadPart;
        HGLOBAL hg = nullptr;
        if (n64 == 0 || FAILED(GetHGlobalFromStream(stream, &hg))) break;
        if (n64 > GlobalSize(hg)) break;
        void* p = GlobalLock(hg);
        if (!p) break;
        out.assign(static_cast<uint8_t*>(p),
                   static_cast<uint8_t*>(p) + static_cast<size_t>(n64));
        GlobalUnlock(hg);
        ok = true;
    } while (false);
    if (conv) conv->Release();
    if (bmp) bmp->Release();
    if (frame) frame->Release();
    if (bag) bag->Release();
    if (enc) enc->Release();
    if (stream) stream->Release();
    if (fac) fac->Release();
    if (must_uninit) CoUninitialize();
    return ok;
}

} // namespace f2
// ═══ F2 END (file-scope helpers) ══════════════════════════════════════════════════

int main(int argc, char** argv) {
    // 1 ms timer granularity for the frame-cap sleeps (Windows default is 15.6 ms).
    timeBeginPeriod(1);
    // THE SHADER-PATH RELEASE FIX (2026-09-03): every shader path in the engine is
    // CWD-relative ("shaders/*.spv"), so launching from anywhere but build/Release
    // failed at pipeline creation. If the shaders are not in the CWD, adopt the
    // EXE's directory — the engine carries its shaders beside its binary, which is
    // the layout every Windows game ships. A dev run from build/Release is
    // unchanged (the guard makes the change a no-op there).
    {
        DWORD attrs = GetFileAttributesA("shaders\\render.vert.spv");
        if (attrs == INVALID_FILE_ATTRIBUTES) {
            char mod[MAX_PATH];
            DWORD n = GetModuleFileNameA(nullptr, mod, MAX_PATH);
            if (n > 0 && n < MAX_PATH) {
                std::string dir(mod, n);
                size_t s = dir.find_last_of("/\\");
                if (s != std::string::npos) {
                    dir.resize(s);
                    SetCurrentDirectoryA(dir.c_str());
                }
            }
        }
    }
    // Config
    EngineConfig cfg;
    // 2K DECREE (2026-08-31, operator): "we will make this project run on a 2K
    // monitor and the monitor resolution should match the project in all efforts
    // including the dyad". The primary display measures 2560x1440, so that is the
    // window AND the capture: the eye reads the glass at the resolution the
    // operator sees it, never a downscale. (Every downscaled dyad frame in this
    // repo was sized to 384px because a 3D bear's silhouette survives it; panel
    // TEXT does not -- at 384px the instrument is unreadable to the eye.)
    // argv[3]/argv[4] override for a box with a different panel.
    cfg.width  = 2560;
    cfg.height = 1440;
    cfg.n_particles = 1200;
    cfg.G      = 1.0f;
    cfg.dt     = 0.02f;
    if (argc > 3) {
        int w = atoi(argv[3]), h = atoi(argv[4]);
        if (w > 0 && h > 0) { cfg.width = (uint32_t)w; cfg.height = (uint32_t)h; }
    }

    // HTTP port: argv[1] overrides the default 8080 (e.g. NVIDIA SDK Manager squats 8080).
    int http_port = 8080;
    if (argc > 1) { http_port = atoi(argv[1]); if (http_port <= 0) http_port = 8080; }
    // R1 DOUBLE-CLICK LAUNCH: --hidden retires the developer console (the
    // studio overlay F1 and the HTTP contract remain the surfaces). The
    // game must not open a terminal.
    bool console_hidden = false;
    for (int i = 1; i < argc; ++i)
        if (std::string(argv[i]) == "--hidden") console_hidden = true;

    // Physics init (passes cfg so it can set physical params)
    g_physics.init(cfg.n_particles, cfg);

    // Engine init (creates Win32 window + Vulkan)
    Engine engine;
    if (!engine.init(cfg)) {
        fprintf(stderr, "Failed to initialize Vulkan engine\n");
        return 1;
    }
    for (int i=1;i<argc;++i)
        if(std::string(argv[i])=="--preserve-mesh-topology") engine.preserve_mesh_topology_=true;
    g_engine = &engine;
    // Opt-in graph scene; existing sessions take no new path.
    for (int i=1;i+1<argc;++i) if(std::string(argv[i])=="--science-surface") {
        try {
            g_science_surface.load(argv[i+1]);
            auto mesh=g_science_surface.mesh();auto ids=g_science_surface.indices();
            if(!engine.load_mesh(mesh,ids,uint32_t(mesh.size()/9),uint32_t(ids.size()))) throw std::runtime_error("surface mesh upload failed");
            engine.set_mesh_mode(2);
            engine.ui_.set_visible(false);
            auto camera=g_science_surface.spec.at("camera").get<std::array<float,8>>();
            for(float x:camera)GraphSurface::need(std::isfinite(x),"nonfinite graph camera");
            engine.set_camera_full(camera.data());
        } catch(const std::exception& ex) {fprintf(stderr,"science surface: %s\n",ex.what());return 2;}
    }


    for(int i=1;i+1<argc;++i) if(std::string(argv[i])=="--thermal-salvage") {
        try {
            chimera::forces::require(!g_science_surface.active,"exclusive_science_scene");
            g_thermal.load(argv[i+1]);
            auto view=g_thermal.render();
            if(!engine.load_mesh(view.mesh,view.indices,uint32_t(view.mesh.size()/9),uint32_t(view.indices.size())))
                throw std::runtime_error("thermal_mesh_upload_failed");
            engine.set_mesh_mode(2);engine.ui_.set_visible(false);
            auto camera=g_thermal.bundle.at("camera").get<std::array<float,8>>();
            engine.set_camera_full(camera.data());
            g_thermal.start();
        }catch(const std::exception& ex){fprintf(stderr,"thermal salvage: %s\n",ex.what());return 2;}
    }

    for(int i=1;i+1<argc;++i) if(std::string(argv[i])=="--earth-patch") {
        try {
            chimera::forces::require(!g_science_surface.active&&!g_thermal.active(),"exclusive_earth_scene");
            g_earth.load(argv[i+1]);auto view=g_earth.render();engine.preserve_mesh_topology_=true;
            if(!engine.load_mesh(view.mesh,view.indices,uint32_t(view.mesh.size()/9),uint32_t(view.indices.size()))) throw std::runtime_error("earth_mesh_upload_failed");
            engine.set_mesh_mode(2);engine.external_body_owner_=true;engine.ui_.set_visible(false);
            float camera[8]={1.35f,.25f,.3f,0,.27f,0,0,0};engine.set_camera_full(camera);g_earth.start();
        }catch(const std::exception& e){fprintf(stderr,"earth patch: %s\n",e.what());return 2;}
    }

    // THE STUDIO: optional board file path (argv[2]); default is studio_board.json
    // in the CWD — tools/studio_board.py writes it next to the exe.
    // 2026-09-02: flags are not paths — `chimera_engine.exe 8090 --restore`
    // made argv[2] == "--restore" the board path, GetFileAttributesExA failed,
    // and the window booted "no board file" forever (the eye's #1 defect:
    // "a raw developer/console message leaking into the product UI").
    if (argc > 2 && std::string(argv[2]).rfind("--", 0) != 0)
        engine.ui_.set_board_file(argv[2]);

    // ── HTTP server for Python shim communication ───────────────────────────────
    // F1: the handler is a NAMED function — the HTTP server and the console's
    // worker run the SAME one (the console is the API's interactive twin).
    HttpServer server;
    Engine::ApiFn api = [&](const std::string& method, const std::string& path,
                            const std::string& req_body, std::string& body, std::string& content_type) {
        try {
        if (g_shutdown_closing.load(std::memory_order_acquire))
            throw ShutdownCancellation{};
        // strip query string
        size_t q = path.find('?');
        std::string p = (q == std::string::npos) ? path : path.substr(0, q);

        // The selected membrane body has one pose owner. A full mesh load starts
        // a new body; independent editors and animation uploads cannot bypass it.
        if(g_tick.body_active() && method=="POST") {
            static const std::set<std::string> competing={"/hinge_bin","/joints_bin","/joints","/joint","/stride_bin","/stride","/gait_bin","/gait","/volp_bin","/volp","/matter","/skin_bin","/pose_apply","/tick_rig","/tick_flex","/tick_joints","/tick_classify","/tick_vertbind","/water_vis"};
            bool mesh_update=false;
            if(p=="/mesh_bin" && req_body.size()>=24) {float mode;std::memcpy(&mode,req_body.data()+20,4);mesh_update=mode>=100.f;}
            if(competing.count(p) || mesh_update) {
                body="{\"ok\":false,\"error\":\"shared_body_owns_surface\"}";content_type="application/json";return;
            }
        }
        if(g_earth.active() && method=="POST" && p!="/earth_state") throw chimera::forces::Refusal("earth_scene_accepts_intent_controls_only");
        if(p=="/earth_state" || p=="/earth_snapshot" || p=="/earth" || p=="/earth_graph") {
            content_type="application/json";
            try {
                chimera::forces::require(g_earth.active(),"earth_scene_missing");
                if(p=="/earth" || p=="/earth_graph") {
                    chimera::forces::require(method=="GET","earth_method");
                    std::ifstream f(g_earth.bundle.at(p=="/earth"?"page_file":"graph_file").get<std::string>(),std::ios::binary);
                    chimera::forces::require(bool(f),"earth_page_missing");body.assign(std::istreambuf_iterator<char>(f),{});content_type=p=="/earth"?"text/html; charset=utf-8":"application/json";
                } else if(p=="/earth_snapshot") {
                    chimera::forces::require(method=="GET","earth_method");auto v=g_earth.render();body=GraphEarth::J{{"ok",true},{"state",v.state},{"vertices",v.mesh},{"indices",v.indices}}.dump();
                } else if(method=="POST") {
                    chimera::forces::require(req_body.size()<=4096,"earth_control_size");std::vector<std::set<std::string>> keys;
                    auto cb=[&](int,GraphEarth::J::parse_event_t event,GraphEarth::J& v){if(event==GraphEarth::J::parse_event_t::object_start)keys.emplace_back();if(event==GraphEarth::J::parse_event_t::key)chimera::forces::require(keys.back().insert(v.get<std::string>()).second,"duplicate_json_key");if(event==GraphEarth::J::parse_event_t::object_end)keys.pop_back();return true;};
                    body=g_earth.control(GraphEarth::J::parse(req_body,cb)).dump();
                }else {chimera::forces::require(method=="GET","earth_method");body=g_earth.status().dump();}
            }catch(const std::exception& e){body=GraphEarth::J{{"ok",false},{"error",e.what()}}.dump();}
            return;
        }
        if(g_thermal.active() && method=="POST" && p!="/thermal_state")
            throw chimera::forces::Refusal("thermal_scene_accepts_intent_controls_only");
        if(p=="/thermal_state" && (method=="GET" || method=="POST")) {
            content_type="application/json";
            try {
                if(method=="POST") {
                    std::vector<std::set<std::string>> keys;
                    auto cb=[&](int,GraphThermal::J::parse_event_t event,GraphThermal::J& v) {
                        if(event==GraphThermal::J::parse_event_t::object_start)keys.emplace_back();
                        if(event==GraphThermal::J::parse_event_t::key)
                            chimera::forces::require(keys.back().insert(v.get<std::string>()).second,"duplicate_json_key");
                        if(event==GraphThermal::J::parse_event_t::object_end)keys.pop_back();
                        return true;
                    };
                    chimera::forces::require(req_body.size()<=4096,"thermal_control_size");
                    body=g_thermal.control(GraphThermal::J::parse(req_body,cb)).dump();
                }else body=g_thermal.status().dump();
            }catch(const std::exception& e){body=GraphThermal::J{{"ok",false},{"error",e.what()}}.dump();}
        } else if(p=="/thermal_frame" && method=="GET") {
            content_type="application/json";
            try {
                chimera::forces::require(g_thermal.active(),"thermal_scene_missing");
                using PhaseClock=std::chrono::steady_clock;
                auto elapsed=[](PhaseClock::time_point a,PhaseClock::time_point b){return std::chrono::duration<double,std::milli>(b-a).count();};
                const auto t0=PhaseClock::now();
                const uint64_t want=engine.capture_arm_watermark()+1;
                engine.request_capture();
                const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
                while(!engine.capture_collected_since(want) && std::chrono::steady_clock::now()<deadline)
                    Sleep(2);
                chimera::forces::require(engine.capture_collected_since(want),"thermal_capture_timeout");
                const auto t1=PhaseClock::now();
                std::array<uint64_t,5> read_phases{};
                std::vector<uint8_t> rgba;uint32_t width=0,height=0;uint64_t seq=0;
                chimera::forces::require(engine.capture_frame(rgba,width,height,&seq,&read_phases) && seq>=want,
                                         "thermal_capture_identity");
                const auto t2=PhaseClock::now();
                GraphThermal::J snapshot;
                while(std::chrono::steady_clock::now()<deadline) {
                    {std::lock_guard<std::mutex> lk(g_thermal_frame_mutex);
                     auto it=g_thermal_frames.find(seq);if(it!=g_thermal_frames.end())snapshot=it->second;}
                    if(!snapshot.is_null())break;
                    Sleep(1);
                }
                chimera::forces::require(!snapshot.is_null(),"thermal_capture_state_missing");
                const auto t3=PhaseClock::now();
                const uint32_t target=(std::max)(320u,(std::min)(1600u,f2::query_uint(path,"w=")));
                if(target<width) {
                    std::vector<uint8_t> down;uint32_t nw=0,nh=0;
                    f2::box_downscale(rgba,width,height,down,nw,nh,target);
                    rgba.swap(down);width=nw;height=nh;
                }
                const auto t4=PhaseClock::now();
                std::vector<uint8_t> encoded;
                const bool jpg=f2::jpeg_encode_wic(rgba.data(),width,height,88,encoded);
                if(!jpg)encoded=png::encode_rgba(rgba.data(),width,height);
                const auto t5=PhaseClock::now();
                body=GraphThermal::J{{"ok",true},{"mime",jpg?"image/jpeg":"image/png"},
                    {"image_base64",GraphThermal::base64(encoded)},{"state",snapshot},
                    {"capture_sequence",seq},{"width",width},{"height",height},
                    {"timing_ms",{{"wait_collect",elapsed(t0,t1)},{"copy",elapsed(t1,t2)},{"state_lookup",elapsed(t2,t3)},
                                  {"downscale",elapsed(t3,t4)},{"encode",elapsed(t4,t5)}}},
                    {"read_phases_us",read_phases},
                    {"read_phase_names",{"map","invalidate","bulk_copy","conversion_or_direct_read","unmap"}}}.dump();
            }catch(const std::exception& e){body=GraphThermal::J{{"ok",false},{"error",e.what()}}.dump();}
        } else if((p=="/thermal" || p=="/thermal_graph") && method=="GET") {
            content_type=p=="/thermal"?"text/html; charset=utf-8":"application/json";
            if(g_thermal.active()) {
                auto key=p=="/thermal"?"page_file":"graph_file";
                std::ifstream f(g_thermal.bundle.at(key).get<std::string>(),std::ios::binary);
                if(f)body.assign(std::istreambuf_iterator<char>(f),{});
                else{body="{\"ok\":false,\"error\":\"thermal_scene_asset_missing\"}";content_type="application/json";}
            }else{body="{\"ok\":false,\"error\":\"thermal_scene_missing\"}";content_type="application/json";}
        } else         if (p == "/science_surface" && (method == "GET" || method == "POST")) {
            std::lock_guard<std::mutex> lk(g_science_mutex);
            content_type="application/json";
            try {
                GraphSurface::need(g_science_surface.active,"no graph surface loaded");
                if(method=="POST")g_science_surface.control(GraphSurface::J::parse(req_body));
                body=g_science_surface.status().dump();
            } catch(const std::exception& ex){body=GraphSurface::J{{"ok",false},{"error",ex.what()}}.dump();}
        } else if ((p == "/science" || p == "/science_graph") && method == "GET") {
            std::lock_guard<std::mutex> lk(g_science_mutex);
            if(g_science_surface.active){
                auto key=p=="/science"?"page_file":"graph_file";
                std::ifstream f(g_science_surface.spec.at(key).get<std::string>(),std::ios::binary);
                if(f){body.assign(std::istreambuf_iterator<char>(f),{});content_type=p=="/science"?"text/html; charset=utf-8":"application/json";}
                else{body="{\"ok\":false,\"error\":\"scene asset missing\"}";content_type="application/json";}
            }else{body="{\"ok\":false,\"error\":\"no graph surface loaded\"}";content_type="application/json";}
        } else if (p == "/state" && method == "GET") {
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
            json += "]}";   // NEVER ']}'  — a multichar literal narrows to ONE char and eats the ']' (the 2026-09-03 /state JSON bug)
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
            bool ok = wait_for_shutdown(g_mem_cv, lk, std::chrono::seconds(3), []{ return g_mem_applied; });
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
                    bool ok = wait_for_shutdown(g_mem_cv, lk, std::chrono::seconds(15), []{ return g_mem_applied; });
                    body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/membrane_demo_bin" && method == "POST") {
            if (req_body.size() < 32) {
                body = "{\"ok\":false,\"error\":\"short membrane demo header\"}";
            } else {
                const uint8_t* d = reinterpret_cast<const uint8_t*>(req_body.data());
                uint32_t magic = 0, nv = 0, nf = 0, centre = 0, reserved = 0;
                double gamma = 0.0; float lift = 0.0f;
                std::memcpy(&magic, d + 0, 4); std::memcpy(&nv, d + 4, 4);
                std::memcpy(&nf, d + 8, 4); std::memcpy(&centre, d + 12, 4);
                std::memcpy(&gamma, d + 16, 8); std::memcpy(&lift, d + 24, 4);
                std::memcpy(&reserved, d + 28, 4);
                const size_t pos_bytes = static_cast<size_t>(nv) * 3 * sizeof(float);
                const size_t idx_bytes = static_cast<size_t>(nf) * 3 * sizeof(uint32_t);
                const size_t off_bytes = static_cast<size_t>(nv + 1) * sizeof(uint32_t);
                const size_t csr_bytes = static_cast<size_t>(nf) * 3 * sizeof(uint32_t);
                const size_t gam_bytes = static_cast<size_t>(nf) * sizeof(float);
                const size_t expect = 32 + pos_bytes + idx_bytes + off_bytes + csr_bytes + gam_bytes;
                if (magic != 0x3130444Du || nv == 0 || nf == 0 || centre >= nv ||
                    !std::isfinite(gamma) || gamma < 0.0 || !std::isfinite(lift) ||
                    req_body.size() != expect) {
                    body = "{\"ok\":false,\"error\":\"invalid membrane demo upload\"}";
                } else {
                    size_t at = 32;
                    Engine::MembraneDemoUpload up{};
                    up.n_verts = nv; up.n_faces = nf; up.centre_index = centre; up.lift_m = lift;
                    up.gamma_admitted = gamma;
                    up.positions_f32.resize(static_cast<size_t>(nv) * 3);
                    up.indices.resize(static_cast<size_t>(nf) * 3);
                    up.csr_offsets.resize(static_cast<size_t>(nv) + 1);
                    up.csr_corners.resize(static_cast<size_t>(nf) * 3);
                    up.gamma_f32.resize(nf);
                    std::memcpy(up.positions_f32.data(), d + at, pos_bytes); at += pos_bytes;
                    std::memcpy(up.indices.data(), d + at, idx_bytes); at += idx_bytes;
                    std::memcpy(up.csr_offsets.data(), d + at, off_bytes); at += off_bytes;
                    std::memcpy(up.csr_corners.data(), d + at, csr_bytes); at += csr_bytes;
                    std::memcpy(up.gamma_f32.data(), d + at, gam_bytes);
                    char snap[256];
                    snprintf(snap, sizeof(snap),
                             "{\"gamma_admitted_f64\":%.17g,\"gamma_uploaded_f32\":%.9g,\"unit\":\"J/m^2\",\"wu_to_m\":1.0}",
                             gamma, static_cast<double>(static_cast<float>(gamma)));
                    up.material_snapshot_json = snap;
                    {
                        std::lock_guard<std::mutex> lk(g_md_mutex);
                        g_md_req = MembraneDemoRequest{};
                        g_md_req.kind = 1; g_md_req.upload = std::move(up);
                        g_md_pending = true; g_md_applied = false;
                    }
                    std::unique_lock<std::mutex> lk(g_md_mutex);
                    bool waited = wait_for_shutdown(g_md_cv, lk, std::chrono::seconds(30), []{ return g_md_applied; });
                    body = waited && g_md_req.ok ? membrane_demo_status_json(g_md_req.status, true)
                                                  : "{\"ok\":false,\"error\":\"membrane demo init failed or timed out\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/membrane_demo" && method == "POST") {
            int ctl = -1;
            std::string op = get_string(req_body, "op");
            if (op == "reset") ctl = 0;
            else if (op == "step") ctl = 1;
            else if (op == "run") ctl = 2;
            else if (op == "pause") ctl = 3;
            else if (op == "gamma") ctl = 4;
            else if (op == "reject") ctl = 5;
            if (ctl < 0) {
                body = "{\"ok\":false,\"error\":\"op must be reset|step|run|pause|gamma|reject\"}";
            } else {
                {
                    std::lock_guard<std::mutex> lk(g_md_mutex);
                    g_md_req = MembraneDemoRequest{};
                    g_md_req.kind = 2; g_md_req.ctl_kind = ctl;
                    g_md_req.n_steps = get_uint(req_body, "n_steps", ctl == 1 ? 1u : 126u);
                    g_md_req.gamma = get_double(req_body, "gamma", 0.0);
                    g_md_pending = true; g_md_applied = false;
                }
                std::unique_lock<std::mutex> lk(g_md_mutex);
                bool waited = wait_for_shutdown(g_md_cv, lk, std::chrono::seconds(60), []{ return g_md_applied; });
                body = waited ? membrane_demo_status_json(g_md_req.status, g_md_req.ok)
                              : "{\"ok\":false,\"error\":\"membrane demo control timeout\"}";
            }
            content_type = "application/json";
        } else if (p == "/membrane_demo" && method == "GET") {
            {
                std::lock_guard<std::mutex> lk(g_md_mutex);
                g_md_req = MembraneDemoRequest{};
                g_md_req.kind = 3; g_md_pending = true; g_md_applied = false;
            }
            std::unique_lock<std::mutex> lk(g_md_mutex);
            bool waited = wait_for_shutdown(g_md_cv, lk, std::chrono::seconds(10), []{ return g_md_applied; });
            body = waited ? membrane_demo_status_json(g_md_req.status, g_md_req.ok)
                          : "{\"ok\":false,\"error\":\"membrane demo status timeout\"}";
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
                    bool ok = wait_for_shutdown(g_mesh_cv, lk, std::chrono::seconds(15), []{ return g_mesh_applied; });
                    body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                }
            }
            content_type = "application/json";
        // ═══ C1 BEGIN: /mesh_import — THE ALIVENESS LAW, one POST ═════════
        } else if (p == "/mesh_import" && method == "POST") {
            // Body = 1-byte source kind ('O' OBJ subset, 'G' glTF 2.0/GLB)
            // + raw source bytes. The importer converts to the engine's
            // full mesh format (or refuses BY NAME — a leaky/open surface
            // never gets admitted) and the converted payload is applied
            // through the SAME handoff /mesh_bin uses: g_mesh_req under
            // g_mesh_mutex, acked by wait_for_shutdown. NOT a nested
            // invoke_api replay — the accepted-import AV (2026-09-13,
            // offline-clean importer) put the nested HTTP-thread handler
            // call in the dock, and the direct handoff is the proven
            // discipline. Deliberately NOT session-snapshotted: an import
            // is reproducible from its source file, and a poisoned blob
            // must never boot-loop the engine again.
            content_type = "application/json";
            if (req_body.empty()) {
                body = "{\"ok\":false,\"error\":\"empty body: expected a "
                       "1-byte kind ('O' OBJ, 'G' glTF) + source bytes\"}";
            } else if (req_body[0] != 'O' && req_body[0] != 'G') {
                body = "{\"ok\":false,\"error\":\"unknown source kind: the "
                       "first byte must be 'O' (OBJ) or 'G' (glTF)\"}";
            } else if (!g_engine) {
                body = "{\"ok\":false,\"error\":\"engine not wired\"}";
            } else if (g_tick.state_json().find("\"sealed\":true") !=
                       std::string::npos) {
                // THE STALE-SEAL GUARD (the accepted-import AV, root
                // cause): MembraneTick::init() rebuilds the cell field but
                // does NOT clear the seal tree, so step()'s seal block
                // keeps reading verts9 through the RESIDENT creature's
                // slot ids on the first tick after any mesh swap — far
                // out of bounds when the old body had more vertices than
                // the import. Until init() clears seal state, importing
                // onto a sealed tick is refused BY NAME, never admitted.
                body = "{\"ok\":false,\"error\":\"refused: the tick still "
                       "holds sealed cells from the resident creature; "
                       "restart the engine with --no-restore (or clear "
                       "its session) before importing\"}";
            } else {
                importer::Stats st;
                std::string bin, err;
                if (!importer::import_mesh(req_body[0],
                                           req_body.substr(1), bin, st, err)) {
                    std::string esc;               // err is quote-free by
                    for (size_t i = 0; i < err.size(); ++i)   // contract; belt
                        esc += err[i] == '"' ? '\'' : err[i]; // and braces
                    body = "{\"ok\":false,\"error\":\"refused: " + esc + "\"}";
                } else if (bin.size() < 24) {
                    body = "{\"ok\":false,\"error\":\"importer payload "
                           "shorter than its own header\"}";
                } else {
                    // decode the payload with /mesh_bin's exact arithmetic
                    uint32_t N = 0, IC = 0;
                    float cr = 12.f, ct = 0.f, cp = 0.3f, slotmode = 0.f;
                    std::memcpy(&N, bin.data() + 0, 4);
                    std::memcpy(&IC, bin.data() + 4, 4);
                    std::memcpy(&cr, bin.data() + 8, 4);
                    std::memcpy(&ct, bin.data() + 12, 4);
                    std::memcpy(&cp, bin.data() + 16, 4);
                    std::memcpy(&slotmode, bin.data() + 20, 4);
                    size_t expect = 24 + static_cast<size_t>(N) * 9 * 4 +
                                    static_cast<size_t>(IC) * 4;
                    if (bin.size() != expect || N == 0 || IC < 3 ||
                        IC % 3 != 0) {
                        body = "{\"ok\":false,\"error\":\"importer payload "
                               "fails the mesh_bin size equation\"}";
                    } else {
                        std::vector<float> verts(static_cast<size_t>(N) * 9);
                        std::vector<uint32_t> indices(IC);
                        std::memcpy(verts.data(), bin.data() + 24,
                                    static_cast<size_t>(N) * 9 * 4);
                        std::memcpy(indices.data(),
                                    bin.data() + 24 + static_cast<size_t>(N) * 9 * 4,
                                    static_cast<size_t>(IC) * 4);
                        {
                            std::lock_guard<std::mutex> lk(g_mesh_mutex);
                            g_mesh_req.verts = std::move(verts);
                            g_mesh_req.indices = std::move(indices);
                            g_mesh_req.N = N;
                            g_mesh_req.idxCount = IC;
                            g_mesh_req.cam_radius = cr;
                            g_mesh_req.cam_theta = ct;
                            g_mesh_req.cam_phi = cp;
                            uint32_t sm = static_cast<uint32_t>(
                                slotmode < 0 ? 0 : slotmode + 0.5f);
                            // slotmode >= 100 = animation delta: never
                            // produced by the importer, kept for shape
                            g_mesh_req.update_only = (sm >= 100);
                            if (g_mesh_req.update_only) sm -= 100;
                            g_mesh_req.slot = sm / 10;
                            g_mesh_req.mode = sm % 10;
                            g_mesh_pending = true; g_mesh_applied = false;
                        }
                        std::unique_lock<std::mutex> lk(g_mesh_mutex);
                        bool ok = wait_for_shutdown(g_mesh_cv, lk,
                                                    std::chrono::seconds(15),
                                                    []{ return g_mesh_applied; });
                        if (ok) {
                            char buf[256];
                            snprintf(buf, sizeof(buf),
                                     "{\"ok\":true,\"verts\":%u,\"tris\":%u,"
                                     "\"volume\":%.9g,\"ymin\":%.9g,"
                                     "\"ymax\":%.9g,\"winding_flipped\":%s}",
                                     st.verts, st.tris, st.volume, st.ymin,
                                     st.ymax,
                                     st.winding_flipped ? "true" : "false");
                            body = buf;
                        } else {
                            body = "{\"ok\":false,\"error\":\"timeout\"}";
                        }
                    }
                }
            }
        // ═══ C1 END ═══════════════════════════════════════════════════════
        } else if (p == "/tick_intent" && method == "POST") {
            // THE MEMBRANE TICK intents (Appliance 1): a standing press.
            // Force in newtons is a required input, never defaulted.
            // Two forms: {"force_n", "foot"} (feet scene) or
            // {"force_n", "joint_index"} (classified creature).
            float force = get_double(req_body, "force_n", NAN);
            int jidx = (int)get_double(req_body, "joint_index", -1.0);
            if (jidx >= 0) {
                body = g_tick.intent_joint(jidx, force)
                     ? "{\"ok\":true}"
                     : "{\"ok\":false,\"error\":\"refused: joint_index out of "
                       "range or force must be positive\"}";
            } else {
                std::string foot = get_string(req_body, "foot");
                if (g_tick.intent(force, foot)) {
                    body = "{\"ok\":true}";
                } else {
                    body = "{\"ok\":false,\"error\":\"refused: force_n must be a "
                           "positive number and foot L or R\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/tick_intent_clear" && method == "POST") {
            g_tick.clear_intent();
            body = "{\"ok\":true}";
            content_type = "application/json";
        } else if (p == "/tick_flex" && method == "POST") {
            // TRAVEL (Appliance 2): pose intent -- flex the feet at the
            // ankle pins, degrees. Poses are intents; flex 0 = authored rest.
            float dl = get_double(req_body, "deg_L", 0.0);
            float dr = get_double(req_body, "deg_R", 0.0);
            if (g_tick.flex(dl, dr)) {
                body = "{\"ok\":true}";
            } else {
                body = "{\"ok\":false,\"error\":\"refused: flex angles must "
                       "be finite and within +/-90 degrees\"}";
            }
            content_type = "application/json";
        } else if (p == "/tick_rig" && method == "POST") {
            // THE LEG (Appliance 3): the hinged chain config, posted by the
            // authoring script. Lines: name|start|count|px|py|pz|parent
            if (g_tick.load_rig(req_body)) body = "{\"ok\":true}";
            else body = "{\"ok\":false,\"error\":\"empty rig\"}";
            content_type = "application/json";
        } else if (p == "/tick_pose" && method == "POST") {
            // A pose intent: {"joint": "knee_L", "deg": -40} or
            // {"joint_index": 12, "deg": 30}
            std::string joint = get_string(req_body, "joint");
            float deg = (float)get_double(req_body, "deg", 0.0);
            int jidx = (int)get_double(req_body, "joint_index", -1.0);
            bool ok = jidx >= 0 ? g_tick.pose_index(jidx, deg)
                                : g_tick.pose(joint, deg);
            if (ok) body = "{\"ok\":true}";
            else body = "{\"ok\":false,\"error\":\"refused: unknown joint or "
                        "angle outside admitted limits\"}";
            content_type = "application/json";
        } else if (p == "/tick_body_bin" && method == "POST") {
            {
                std::lock_guard<std::mutex> lk(g_volp_mutex);
                g_volp_req=VolpReq{};g_volp_req.kind=4;
                g_volp_req.blob.assign(req_body.begin(),req_body.end());
                g_volp_pending=true;g_volp_applied=false;
            }
            std::unique_lock<std::mutex> lk(g_volp_mutex);
            bool done=wait_for_shutdown(g_volp_cv,lk,std::chrono::seconds(60),[]{return g_volp_applied;});
            body=done && g_volp_req.ok ? "{\"ok\":true,\"body_model\":\"JNT3_hierarchical\",\"actuation\":\"kinematic\"}" : "{\"ok\":false,\"error\":\"body_binding_refused_load_before_seals_and_controllers\"}";
            content_type="application/json";
        } else if (p == "/tick_classify" && method == "POST") {
            // CA CLASSIFICATION (Appliance 4): per-triangle joint type.
            body = g_tick.load_classify(req_body) ? "{\"ok\":true}"
                 : "{\"ok\":false,\"error\":\"classification size mismatch "
                   "(post after the mesh)\"}";
            content_type = "application/json";
        } else if (p == "/tick_vertbind" && method == "POST") {
            // TRAVEL binding: 15 bytes per vertex (3 pin indices + 3 weights)
            body = g_tick.load_vertbind(req_body) ? "{\"ok\":true}"
                 : "{\"ok\":false,\"error\":\"vertbind rejected (size or "
                   "vertex count mismatch)\"}";
            content_type = "application/json";
        } else if (p == "/tick_joints" && method == "POST") {
            // The measured pins: [u32 n][f32 x,y,z * n]
            body = g_tick.load_joint_pins(req_body) ? "{\"ok\":true}"
                 : "{\"ok\":false,\"error\":\"joint pins rejected\"}";
            content_type = "application/json";
        } else if (p == "/tick_seal" && method == "POST") {
            // THE MITOSIS OP (recursive cut-and-weld): cut sealed cell k
            // ("cell", default 0 = whole creature) with plane y into two
            // sealed cells — the growth law. An intent whose state ALREADY
            // exists (a replayed repeat: the plane already bounds the named
            // cell, or the tree already partitions at this plane) answers
            // ok:true with "seal":"already" — the idempotent skip (nothing
            // published, nothing refused, nothing re-journaled below).
            float y = (float)get_double(req_body, "y", 0.0);
            int cell = (int)get_double(req_body, "cell", 0.0);
            int outcome = MembraneTick::SEAL_CUT;
            if (g_tick.seal(y, cell, &outcome)) {
                body = outcome == MembraneTick::SEAL_ALREADY
                     ? "{\"ok\":true,\"seal\":\"already\"}"
                     : "{\"ok\":true}";
            } else {
                body = "{\"ok\":false,\"error\":\"refused: the cell index "
                        "must exist, the plane must cross that cell's "
                        "y-range, and the cut graph must close into loops\"}";
            }
            content_type = "application/json";
        } else if (p == "/tick_seal_state" && method == "POST") {
            // THE SEAL-TREE SNAPSHOT LOAD (R-restore-doctor): restore the
            // mitosis tree directly from its state blob — zero cuts
            // executed. The loader self-validates (vertex count + every
            // cell's recomputed rest volume), so a stale blob (any mesh
            // change since it was written) is REFUSED HERE WITHOUT
            // MUTATION — and this endpoint answers ok:true with
            // "seal_state":"skipped", NEVER a restore failure: the history
            // replay right after us rebuilds the tree the honest way
            // (executed cuts + already-skips) and re-snapshots it.
            if (g_tick.load_seal_state(req_body)) {
                body = "{\"ok\":true,\"seal_state\":\"loaded\"}";
                printf("snapshot: seal-tree loaded (%zu B, zero cuts "
                       "executed)\n", req_body.size());
            } else {
                body = "{\"ok\":true,\"seal_state\":\"skipped\"}";
                printf("snapshot: seal-tree blob refused (stale or absent "
                       "tree) -- falling back to the intent history\n");
            }
            fflush(stdout);
            content_type = "application/json";
        } else if (p == "/topology" && method == "GET") {
            // THE WEB KERNEL: one-time triangle topology for the browser's
            // own renderer.
            std::vector<uint8_t> out;
            g_tick.export_topology(out);
            body.assign(reinterpret_cast<const char*>(out.data()), out.size());
            content_type = "application/octet-stream";
        } else if (p == "/verts" && method == "GET") {
            // THE WEB KERNEL: the posed surface as state (pos+normal+color,
            // 9 f32 per vertex), serialized under the tick lock.
            std::vector<uint8_t> out;
            g_tick.export_verts(g_tick_verts, out);
            body.assign(reinterpret_cast<const char*>(out.data()), out.size());
// C3 BEGIN — THE KERNEL STREAM: delta compression for /verts (the
// internet-scale successor the web-kernel prereg named,
// docs/evidence/agent_fleet/MATTER_KERNEL/SEAL_PREREGISTRATION.md).
// Constraints stated before the mechanism: (1) the legacy framing
// [u32 n][f32*9n] is untouched — every request without ?delta=1 is
// answered exactly as before, so no existing consumer can regress;
// (2) the delta chains against this route's previous DELTA-SERVED
// export only (legacy pulls never advance the chain), which makes the
// stream defined for ONE delta client — a u32 seq on every emission
// lets a client detect a broken chain (dropped poll, interleaved
// second viewer) and resync with one ?delta=key pull; (3) "unchanged"
// is BIT-identical (memcmp), because idle exports are provably
// byte-identical (apply_chain copies base_pos_ at rest; tint and
// normals are pure functions of stable inputs); (4) a delta that
// would not beat the full frame is never sent — the route falls back
// to a keyframe; (5) the falsifier is a torn frame, so any size
// inconsistency aborts to the legacy frame server-side and the CLIENT
// refuses partial runs — nothing partial ever reaches a renderer.
            {
                bool want_delta = false, want_key = false;
                size_t q3 = path.find('?');
                if (q3 != std::string::npos) {
                    size_t d3 = path.find("delta=", q3);
                    if (d3 != std::string::npos) {
                        size_t v3 = d3 + 6, e3 = v3;
                        while (e3 < path.size() && path[e3] != '&') ++e3;
                        std::string val = path.substr(v3, e3 - v3);
                        want_key = (val == "key");     // forced keyframe: the resync pull
                        want_delta = !want_key && (val == "1");
                    }
                }
                if ((want_delta || want_key) && out.size() >= 4) {
                    // Route-local cache under its own small mutex — NEVER
                    // the tick lock: export_verts has already released
                    // seal_mtx_, and the delta math runs on this request's
                    // private copy, so the render loop is never blocked.
                    static std::mutex c3_mtx;
                    static std::vector<uint8_t> c3_prev;   // last delta-served export (legacy framing)
                    static uint32_t c3_seq = 0;            // advances on every delta-framed emission
                    static uint32_t c3_since_key = 0;      // runs-frames since the last keyframe
                    static bool c3_has_prev = false;
                    std::lock_guard<std::mutex> lk(c3_mtx);

                    uint32_t n = 0;
                    std::memcpy(&n, out.data(), 4);
                    const size_t payload = static_cast<size_t>(n) * 36;
                    bool chain_ok = c3_has_prev && c3_prev.size() == out.size();
                    if (chain_ok)
                        chain_ok = 0 == std::memcmp(out.data(), c3_prev.data(), 4);

                    // one pass: runs of CHANGED vertices (36-byte stride,
                    // bitwise compare — a pose recomputes values, but at
                    // rest the recomputation is bit-identical)
                    bool emit_key = want_key || !chain_ok || c3_since_key >= 60;
                    std::vector<uint32_t> run_start, run_len;
                    size_t changed = 0;
                    if (!emit_key) {
                        bool in_run = false;
                        for (uint32_t v = 0; v < n; ++v) {
                            bool ch = 0 != std::memcmp(out.data() + 4 + static_cast<size_t>(v) * 36,
                                                       c3_prev.data() + 4 + static_cast<size_t>(v) * 36, 36);
                            if (ch) {
                                if (!in_run) { run_start.push_back(v); run_len.push_back(1); in_run = true; }
                                else ++run_len.back();
                                ++changed;
                            } else {
                                in_run = false;
                            }
                        }
                        // the delta must never cost more than the full frame
                        if (16 + run_start.size() * 8 + changed * 36 >= 4 + payload)
                            emit_key = true;
                    }

                    std::vector<uint8_t> frame;
                    if (emit_key) {
                        // kernel framing: [u8 magic 0xD1][u8 flags][u16 rsvd]
                        //                 [u32 n][u32 seq][u32 runs]
                        frame.resize(16 + payload);        // resize zero-fills: rsvd=0, runs=0
                        frame[0] = static_cast<char>(0xD1);
                        frame[1] = 0;                      // flags 0 = keyframe
                        std::memcpy(&frame[4], &n, 4);
                        std::memcpy(&frame[8], &c3_seq, 4);
                        if (n) std::memcpy(&frame[16], out.data() + 4, payload);
                        c3_since_key = 0;
                    } else {
                        frame.resize(16 + run_start.size() * 8 + changed * 36);
                        frame[0] = static_cast<char>(0xD1);
                        frame[1] = 1;                      // flags 1 = runs
                        std::memcpy(&frame[4], &n, 4);
                        std::memcpy(&frame[8], &c3_seq, 4);
                        uint32_t rc = static_cast<uint32_t>(run_start.size());
                        std::memcpy(&frame[12], &rc, 4);
                        size_t w = 16;
                        for (size_t r = 0; r < run_start.size(); ++r) {
                            uint32_t s = run_start[r], c = run_len[r];
                            std::memcpy(&frame[w], &s, 4);
                            std::memcpy(&frame[w + 4], &c, 4);
                            std::memcpy(&frame[w + 8],
                                        out.data() + 4 + static_cast<size_t>(s) * 36,
                                        static_cast<size_t>(c) * 36);
                            w += 8 + static_cast<size_t>(c) * 36;
                        }
                        ++c3_since_key;
                    }
                    ++c3_seq;
                    c3_prev = out;       // the chain base is the EXPORTED state
                    c3_has_prev = true;
                    body.assign(reinterpret_cast<const char*>(frame.data()), frame.size());
                }
                // no ?delta=1|key (or an empty export): body already holds
                // the legacy full frame — bit-for-bit the pre-C3 answer.
            }
// C3 END
            content_type = "application/octet-stream";
        } else if (p == "/tick_touch" && method == "POST") {
            // THE TOUCH, three forms:
            //  {"cam":[8],"px","py",force_n} — the WEB KERNEL: the browser
            //    posts its own local camera + click pixel; the engine picks
            //    with the player's view (the proven closed-loop picker).
            //  {"hit":[x,y,z],force_n}          — a ready world point.
            //  {"px","py",force_n}             — the engine's own camera.
            content_type = "application/json";
            size_t cp = req_body.find("\"cam\"");
            if (cp != std::string::npos) {
                float cam8[8];
                size_t lb = req_body.find('[', cp);
                float px2 = (float)get_double(req_body, "px", 0.5);
                float py2 = (float)get_double(req_body, "py", 0.5);
                float F = (float)get_double(req_body, "force_n", 0.0);
                std::string err2;
                float hit2[3];
                float aspect = (float)get_double(req_body, "aspect", 2560.0 / 1440.0);
                if (lb == std::string::npos ||
                    sscanf(req_body.c_str() + lb + 1, "%f,%f,%f,%f,%f,%f,%f,%f",
                           &cam8[0], &cam8[1], &cam8[2], &cam8[3], &cam8[4],
                           &cam8[5], &cam8[6], &cam8[7]) != 8) {
                    body = "{\"ok\":false,\"error\":\"cam must be 8 floats\"}";
                } else if (g_tick.touch_press(px2, py2, F,
                        [&](float out[3]) -> bool {
                            return g_engine && g_engine->pick_cam(cam8, aspect, px2, py2,
                                g_tick_verts, g_tick.tri_verts(), out);
                        }, err2, hit2)) {
                    body = std::string("{\"ok\":true,\"hit\":[")
                         + std::to_string(hit2[0]) + "," + std::to_string(hit2[1])
                         + "," + std::to_string(hit2[2]) + "]}";
                } else {
                    body = "{\"ok\":false,\"error\":\"the ray misses the body\"}";
                }
            } else if (req_body.find("\"hit\"") != std::string::npos) {
                size_t hb = req_body.find('[', req_body.find("\"hit\""));
                float hx = 0, hy = 0, hz = 0;
                if (hb != std::string::npos)
                    sscanf(req_body.c_str() + hb + 1, "%f,%f,%f", &hx, &hy, &hz);
                float hit[3] = {hx, hy, hz};
                // truthfulness (A1's finding): a press lands on skin or is
                // refused — never ok:true with zero effect. The honest reach
                // is a few Gaussians (r0 = 3 cm): beyond 15 cm it is theatre.
                float d2 = g_tick.point_skin_dist2(hit);
                if (d2 > 0.15f * 0.15f) {
                    body = "{\"ok\":false,\"error\":\"the point is not on the body\"}";
                } else if (g_tick.touch_press_at(hit,
                        (float)get_double(req_body, "force_n", 0.0))) {
                    body = "{\"ok\":true}";
                } else {
                    body = "{\"ok\":false,\"error\":\"force_n must be positive\"}";
                }
            } else {
                float px = (float)get_double(req_body, "px", 0.5);
                float py = (float)get_double(req_body, "py", 0.5);
                float force = (float)get_double(req_body, "force_n", 0.0);
                std::string err;
                float hit[3];
                if (g_tick.touch_press(px, py, force,
                    [&](float out[3]) -> bool {
                        return g_engine && g_engine->pick(px, py, g_tick_verts,
                            g_tick.tri_verts(), out);
                    }, err, hit)) {
                    body = std::string("{\"ok\":true,\"hit\":[")
                         + std::to_string(hit[0]) + "," + std::to_string(hit[1])
                         + "," + std::to_string(hit[2]) + "]}";
                } else {
                    body = "{\"ok\":false,\"error\":\"" + err + "\"}";
                }
            }
        } else if (p == "/tick_touch_clear" && method == "POST") {
            g_tick.touch_clear();
            body = "{\"ok\":true}";
            content_type = "application/json";
        } else if (p == "/tick_gait" && method == "POST") {
            // THE GAIT CHECKPOINT MACHINE (fleet G1, lead-wired at the window):
            // per-leg STANCE/LIFT/REACH/LOAD, every gate a measured number.
            bool on = req_body.find("\"on\":true") != std::string::npos;
            if (g_tick.set_gait(on)) body = "{\"ok\":true,\"gait_on\":" + std::string(on ? "true" : "false") + "}";
            else body = "{\"ok\":false,\"error\":\"refused: needs gravity, stance, classification, pins 13-18, and a sealed feet cell\"}";
            content_type = "application/json";
        } else if (p == "/tick_stance" && method == "POST") {
            // THE STANCE SERVO (fleet 2/F1): ankles counter the body's lean
            // while gravity holds — the balance rung of the movement law.
            bool on = req_body.find("\"on\":true") != std::string::npos;
            if (g_tick.set_stance(on)) body = "{\"ok\":true,\"stance_on\":" + std::string(on ? "true" : "false") + "}";
            else body = "{\"ok\":false,\"error\":\"refused: the body must be classified and a support band must exist\"}";
            content_type = "application/json";
        } else if (p == "/tick_gravity" && method == "POST") {
            // THE MOVEMENT LAW (fleet C2, lead-wired at the build window):
            // gravity + ground contact on the root — "a creature that cannot
            // FALL cannot WALK". Default off until the F-bars pass.
            size_t onk = req_body.find("\"on\"");
            bool on = onk != std::string::npos &&
                      req_body.find("true", onk) != std::string::npos;
            if (g_tick.set_gravity(on)) body = "{\"ok\":true,\"gravity_on\":" + std::string(on ? "true" : "false") + "}";
            else body = "{\"ok\":false,\"error\":\"refused: no scene\"}";
            content_type = "application/json";
        } else if (p == "/tick_seal_split" && method == "POST") {
            // THE COMPONENT SPLIT: a cell of disjoint closed surfaces
            // (left+right after a band cut) divides per component.
            int cell = (int)get_double(req_body, "cell", 0.0);
            if (g_tick.split(cell)) body = "{\"ok\":true}";
            else body = "{\"ok\":false,\"error\":\"refused: the cell index "
                        "must exist and hold more than one closed surface\"}";
            content_type = "application/json";
        } else if (p == "/tick_reflex" && method == "POST") {
            // THE CREATURE ANSWERS (fleet C1r; lead-wired at window #8).
            // DEFAULT OFF ON BOOT -- this route is the only arming path.
            // Three PHYSICS reflexes: breathing (the torso cell's volume
            // target oscillates; the pressure law and every gait
            // measurement are structurally blind to it), flinch (a sealed
            // cell's pressure crossing on a RISING edge flexes the touched
            // side's binding-derived strut pin), startle (a pressure
            // TRANSIENT biases the stance servo inside its existing cap).
            // COMPACT-JSON HAZARD (R4_GAIT_VERIFY/PROTOCOL.md): the master
            // "on" arms on the LITERAL substring "on":true -- a space
            // ({"on": true}) parses as FALSE and silently disarms, the
            // same law as /tick_gait and /tick_stance. Channel switches
            // use get_bool, never stod (the stod-on-booleans trap).
            //   {"on":true}                        arm all three
            //   {"on":false}                       deterministic full off
            //   {"breathing":false}                suspend the oscillator
            //   {"pressure_coupling":false}        THE NERVE CUT (negative
            //                                      control: the flinch and
            //                                      startle detectors see
            //                                      nothing; breathing is
            //                                      not pressure-driven)
            // Refusals name themselves (reflex_block in /tick_state); a
            // partial arm is ok:true with the failed channels named.
            bool has_on = req_body.find("\"on\"") != std::string::npos;
            bool ok = true;
            if (has_on) {
                const bool on =
                    req_body.find("\"on\":true") != std::string::npos;
                ok = g_tick.set_reflex(on);
            }
            static const char* kReflexChannels[] = {
                "breathing", "flinch", "startle", "pressure_coupling"};
            for (const char* ch : kReflexChannels) {
                if (find_colon_after(req_body, ch) == std::string::npos)
                    continue;
                g_tick.set_reflex_channel(ch, get_bool(req_body, ch, true));
            }
            body = std::string("{\"ok\":") + (ok ? "true," : "false,")
                 + "\"reflex\":" + g_tick.reflex_summary_json() + "}";
            content_type = "application/json";
        } else if (p == "/tick_limb" && method == "POST") {
            // AN2: THE ONE-LIMB PARTITION (prereg
            // docs/evidence/agent_fleet/SHIP/ONE_LIMB/PREREG.md M1/M2).
            // Derives the leg's segments from skeleton CONNECTIVITY (the
            // pin graph over dominant-binding labels; a chain that does
            // not match refuses BY NAME), splits the band components,
            // merges the limb, seals it with TWO OBLIQUE walls through
            // the knee/ankle pins (one generalized cut core with the
            // horizontal seal), validates closure/orientation/volumes/
            // coverage/mass/genus, and builds the sensor patch regions.
            //   {"side":"L"}   |   {"side":"R"}
            // Refuses while any rung is armed (surgery at authored rest).
            // IDEMPOTENT: a replay of an executed partition answers
            // "limb":"already" (the R-restore-doctor law).
            std::string side = get_string(req_body, "side");
            std::string report;
            bool already = false;
            if (g_tick.limb_partition(side, report, &already)) {
                body = std::string("{\"ok\":true,\"limb\":\"")
                     + (already ? "already" : "executed")
                     + "\",\"report\":" + report + "}";
            } else {
                std::string esc;
                for (char ch : report) {
                    if (ch == '"' || ch == '\\') esc += '\\';
                    esc += ch;
                }
                body = "{\"ok\":false,\"error\":\"" + esc + "\"}";
            }
            content_type = "application/json";
        } else if (p == "/tick_limb_state" && method == "POST") {
            // AN2: the limb REGISTRY blob replay (the restore path; the
            // blob is self-validating: every segment's cell must exist
            // with the stored piece count and a matching rest volume).
            if (g_tick.limb_restore(req_body))
                body = "{\"ok\":true,\"limb_state\":\"restored\"}";
            else
                body = "{\"ok\":false,\"error\":\"refused: the limb "
                       "registry blob does not match this body (stale "
                       "or the tree is not restored yet)\"}";
            content_type = "application/json";
        } else if (p == "/tick_patch" && method == "POST") {
            // AN2: SENSOR PATCHES (prereg M3): finite receptor regions
            // with their own filtered/saturated signal and an explicit
            // finite transport delay; a path CUT is a real state.
            //   {"on":true}                            arm the layer
            //   {"on":false}                           deterministic off
            //   {"path":"shin_L","connected":false}    THE PATH CUT
            //   {"path":"shin_L","connected":true}     reconnect
            // Compact-JSON hazard: "on" arms on the literal substring
            // "on":true (the /tick_gait law); "connected" uses get_bool
            // (never stod -- the stod-on-booleans trap).
            std::string err;
            bool ok = true;
            if (find_colon_after(req_body, "path") != std::string::npos) {
                std::string nm = get_string(req_body, "path");
                bool conn = get_bool(req_body, "connected", true);
                ok = g_tick.patch_connect(nm, conn, err);
            }
            if (ok && find_colon_after(req_body, "on") != std::string::npos) {
                bool on = req_body.find("\"on\":true") != std::string::npos;
                ok = g_tick.patch_arm(on, err);
            }
            body = std::string("{\"ok\":") + (ok ? "true" : "false")
                 + (err.empty() ? "" : ",\"error\":\"" + err + "\"")
                 + ",\"patches\":" + g_tick.patch_json() + "}";
            content_type = "application/json";
        } else if (p == "/tick_patch_state" && method == "POST") {
            // AN2: the patch-state blob replay (arm + per-path connection
            // + cut stamps; must match the restored limb registry).
            if (g_tick.patch_restore(req_body))
                body = "{\"ok\":true,\"patch_state\":\"restored\"}";
            else
                body = "{\"ok\":false,\"error\":\"refused: the "
                       "patch-state blob does not match the limb "
                       "registry\"}";
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
                    bool ok = wait_for_shutdown(g_hinge_cv, lk, std::chrono::seconds(15), []{ return g_hinge_applied; });
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
                        bool ok = wait_for_shutdown(g_hinge_cv, lk, std::chrono::seconds(15), []{ return g_hinge_applied; });
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
                    bool ok = wait_for_shutdown(g_water_cv, lk, std::chrono::seconds(60), []{ return g_water_applied; });
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
                        wait_for_shutdown(g_water_cv, lk, std::chrono::seconds(120), []{ return g_water_applied; });
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
                wait_for_shutdown(g_water_cv, lk, std::chrono::seconds(60), []{ return g_water_applied; });
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
                    bool ok = wait_for_shutdown(g_gait_cv, lk, std::chrono::seconds(60), []{ return g_gait_applied; });
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
                wait_for_shutdown(g_gait_cv, lk, std::chrono::seconds(60), []{ return g_gait_applied; });
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
            bool ok = wait_for_shutdown(g_volp_cv, lk, std::chrono::seconds(60), []{ return g_volp_applied; });
            body = ok && g_volp_req.ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"load failed\"}";
            content_type = "application/json";
        } else if (p == "/stride_bin" && method == "POST") {
            // STRIDE: binary upload of a certified stride.
            //   [u32 magic=0x47415431 ('GAT1')][u32 n_samples][u32 n_joints]
            //   [f32 dt][u32 loop0][f32*n_samples*n_joints thetas, radians, pack order]
            if (req_body.size() < 20) {
                body = "{\"ok\":false,\"error\":\"short header\"}";
            } else {
                uint32_t magic = 0, n = 0, j = 0, loop0 = 0; float dt = 0.f;
                std::memcpy(&magic, req_body.data() + 0, 4);
                std::memcpy(&n, req_body.data() + 4, 4);
                std::memcpy(&j, req_body.data() + 8, 4);
                std::memcpy(&dt, req_body.data() + 12, 4);
                std::memcpy(&loop0, req_body.data() + 16, 4);
                if (magic != 0x47415431u) {
                    body = "{\"ok\":false,\"error\":\"bad magic\"}";
                } else if (req_body.size() != 20 + static_cast<size_t>(n) * j * 4) {
                    body = "{\"ok\":false,\"error\":\"size mismatch\"}";
                } else {
                    std::vector<float> rows(static_cast<size_t>(n) * j);
                    std::memcpy(rows.data(), req_body.data() + 20, static_cast<size_t>(n) * j * 4);
                    bool ok = g_engine ? g_engine->set_stride_stream(rows, n, j, dt, loop0) : false;
                    body = ok ? "{\"ok\":true,\"n\":" + std::to_string(n) + "}"
                              : "{\"ok\":false,\"error\":\"stream rejected (pack mismatch or bad values)\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/stride" && method == "POST") {
            // STRIDE control: {"on":true,"playing":true,"speed":1.0,"t":0.0}
            if (g_engine) {
                bool on = get_bool(req_body, "on", true);
                bool playing = get_bool(req_body, "playing", true);
                float speed = get_float(req_body, "speed", 1.0f);
                if (speed <= 0.f) speed = 1.0f;
                bool has_t = req_body.find("\"t\"") != std::string::npos;
                float t = get_float(req_body, "t", 0.f);
                g_engine->stride_control(on, playing, speed, has_t, t);
                body = "{\"ok\":true}";
            } else body = "{\"ok\":false,\"error\":\"no engine\"}";
            content_type = "application/json";
        } else if (p == "/stride" && method == "GET") {
            if (g_engine) {
                auto s = g_engine->stride_status();
                body = "{\"ok\":true,\"active\":" + std::string(s.active ? "true" : "false")
                     + ",\"playing\":" + std::string(s.playing ? "true" : "false")
                     + ",\"n\":" + std::to_string(s.n)
                     + ",\"j\":" + std::to_string(s.j)
                     + ",\"dt\":" + std::to_string(s.dt)
                     + ",\"loop0\":" + std::to_string(s.loop0)
                     + ",\"t\":" + std::to_string(s.t) + "}";
            } else body = "{\"ok\":false,\"error\":\"no engine\"}";
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
            bool ok = wait_for_shutdown(g_volp_cv, lk, std::chrono::seconds(60), []{ return g_volp_applied; });
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
                wait_for_shutdown(g_volp_cv, lk, std::chrono::seconds(60), []{ return g_volp_applied; });
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
                wait_for_shutdown(g_water_cv, lk, std::chrono::seconds(30), []{ return g_water_applied; });
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
                bool ok = wait_for_shutdown(g_frost_cv, lk, std::chrono::seconds(30), []{ return g_frost_applied; });
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
        } else if (p == "/keys" && (method == "GET" || method == "POST")) {
            // TIMELINE KEY MARKS: named poses on the live clock (tool feature 4).
            // GET  -> {"keys":[{"name":..,"t":..}..]}
            // POST {"op":"save","name":X}    -> key the live clock (no name = auto keyN)
            // POST {"op":"recall","name":X}  -> scrub to the key's time
            // POST {"op":"delete","name":X}  -> remove the key
            // POST {"op":"clear"}            -> remove all keys
            if (method == "GET") {
                std::string out = "{\"keys\":[";
                if (g_engine) {
                    auto ks = g_engine->key_marks_list_info();
                    bool first = true;
                    for (const auto& k : ks) {
                        if (!first) out += ",";
                        first = false;
                        out += "{\"name\":\"" + k.name + "\",\"t\":" + std::to_string(k.t);
                        if (!k.joint.empty()) out += ",\"joint\":\"" + k.joint + "\"";
                        out += "}";
                    }
                }
                out += "]}";
                body = out;
            } else {
                std::string op, name;
                auto get_str = [&](const char* key, std::string& val) {
                    std::string pat = std::string("\"") + key + "\"";
                    size_t kp = req_body.find(pat);
                    if (kp == std::string::npos) return;
                    size_t cp = req_body.find(':', kp + pat.size());
                    if (cp == std::string::npos) return;
                    size_t q1 = req_body.find('"', cp + 1);
                    if (q1 == std::string::npos) return;
                    size_t q2 = req_body.find('"', q1 + 1);
                    if (q2 == std::string::npos) return;
                    val = req_body.substr(q1 + 1, q2 - q1 - 1);
                };
                get_str("op", op);
                get_str("name", name);
                if (!g_engine) { body = "{\"ok\":false}";                } else if (op == "recall") {
                    double t = 0.0;
                    bool ok = g_engine->key_mark_time(name, t);
                    if (ok) g_engine->show_scrub_.store(t < 0.0 ? 0.0 : t);
                    // D7-POSE: the key also carries the WHOLE pose at save —
                    // restore it through the render thread (owner -> EDIT, all
                    // thetas at once). A timestamp-only key keeps the old
                    // scrub-only behavior.
                    bool posed = false;
                    if (ok) {
                        std::vector<float> snap;
                        if (g_engine->key_mark_pose(name, snap)) posed = g_engine->key_apply_pose(snap);
                    }
                    body = std::string("{\"ok\":") + (ok ? "true" : "false")
                         + ",\"t\":" + std::to_string(t) + ",\"posed\":" + (posed ? "true" : "false") + "}";
                } else if (op == "delete") {
                    body = std::string("{\"ok\":")
                         + (g_engine->key_mark_delete(name) ? "true" : "false") + "}";
                } else if (op == "clear") {
                    g_engine->key_marks_clear();
                    body = "{\"ok\":true}";
                } else {   // save is the default op (the KEY button's intent)
                    int sel = g_engine->selected_joint_.load(std::memory_order_relaxed);
                    std::string jn = (sel >= 0 && sel < static_cast<int>(g_engine->show_joint_count()))
                                    ? g_engine->show_joint_name(static_cast<uint32_t>(sel)) : std::string();
                    std::string nm = g_engine->key_mark_save(name, jn);
                    double t = 0.0;
                    g_engine->key_mark_time(nm, t);
                    body = "{\"ok\":true,\"name\":\"" + nm + "\",\"t\":"
                         + std::to_string(t);
                    if (!jn.empty()) body += ",\"joint\":\"" + jn + "\"";
                    body += "}";
                }
            }
            content_type = "application/json";
        } else if (p == "/strain" && method == "POST") {
            // THE STRAIN OVERLAY toggle: on = kernel tints the membrane by true
            // area strain (blue compress / red stretch). Read-only elsewhere.
            bool on = g_engine ? g_engine->strain_on() : false;
            {
                size_t op = req_body.find("\"on\"");
                if (op != std::string::npos) {
                    size_t cp = req_body.find(':', op + 4);
                    if (cp != std::string::npos) {
                        size_t a = req_body.find_first_not_of(" \t", cp + 1);
                        if (a != std::string::npos)
                            on = req_body.compare(a, 4, "true") == 0;
                    }
                }
            }
            if (g_engine) g_engine->strain_set(on);
            body = std::string("{\"ok\":true,\"on\":") + (on ? "true" : "false") + "}";
            content_type = "application/json";
        } else if (p == "/strain" && method == "GET") {
            body = std::string("{\"on\":") + (g_engine && g_engine->strain_on() ? "true" : "false")
                 + ",\"hinge\":" + (g_engine && g_engine->hinge_active() ? "true" : "false") + "}";
            content_type = "application/json";
        } else if (p == "/matter" && method == "POST") {
            // THE MATTER PASS (M1) toggle: on = after the LBS pose, the surface
            // relaxes against its own adjacency (edges resist deviation from
            // rest, k=0.5, 4 Jacobi iterations) and the ground plane forbids
            // penetration (y >= Y_G). JNT2 only; the scene row carries the same gate.
            bool on = g_engine ? g_engine->matter_on() : false;
            {
                size_t op = req_body.find("\"on\"");
                if (op != std::string::npos) {
                    size_t cp = req_body.find(':', op + 4);
                    if (cp != std::string::npos) {
                        size_t a = req_body.find_first_not_of(" \t", cp + 1);
                        if (a != std::string::npos)
                            on = req_body.compare(a, 4, "true") == 0;
                    }
                }
            }
            if (g_engine) {
                g_engine->matter_set(on);
                if (req_body.find("\"iters\"") != std::string::npos)
                    g_engine->matter_iters_set(get_float(req_body, "iters", 4.0f));
                if (req_body.find("\"k\"") != std::string::npos)
                    g_engine->matter_k_set(get_float(req_body, "k", 0.1f));
            }
            body = std::string("{\"ok\":true,\"on\":") + (on ? "true" : "false")
                 + ",\"iters\":" + std::to_string(g_engine ? g_engine->matter_iters() : 0.0f)
                 + ",\"k\":" + std::to_string(g_engine ? g_engine->matter_k() : 0.0f) + "}";
            content_type = "application/json";
        } else if (p == "/matter" && method == "GET") {
            body = std::string("{\"on\":") + (g_engine && g_engine->matter_on() ? "true" : "false")
                 + ",\"iters\":" + std::to_string(g_engine ? g_engine->matter_iters() : 0.0f)
                 + ",\"k\":" + std::to_string(g_engine ? g_engine->matter_k() : 0.0f)
                 + ",\"y_ground\":-0.0195}";
            content_type = "application/json";
        } else if (p == "/matter_state" && method == "GET") {
            // THE MATTER PASS's truth channel: the LAST dispatched frame's
            // surface state is read back from Work half 0 (persistent host
            // map) and measured against the REST edge lengths — the same law
            // the kernel relaxes. iters=0 turns the pass into the pure-LBS
            // control; iters=4 reads the matter-passed surface. The difference
            // IS the pass's effect, on the engine's own numbers.
            if (g_engine && g_engine->matter_readable()) {
                float s_mean, s_max, rms; uint32_t below;
                g_engine->matter_stats(s_mean, s_max, rms, below);
                char b2[256];
                snprintf(b2, sizeof(b2),
                         "{\"ok\":true,\"stretch_mean_pct\":%.4f,\"stretch_max_pct\":%.4f,"
                         "\"rms_err_pct\":%.4f,\"below_ground\":%u}",
                         s_mean, s_max, rms, below);
                body = b2;
            } else {
                body = "{\"ok\":false,\"error\":\"matter not readable (needs JNT2 + matter on)\"}";
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
                ok = wait_for_shutdown(g_frost_cv, lk, std::chrono::seconds(15), []{ return g_frost_applied; });
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
                bool ok = wait_for_shutdown(g_frost_cv, lk, std::chrono::seconds(30), []{ return g_frost_applied; });
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
                    bool ok = wait_for_shutdown(g_skin_cv, lk, std::chrono::seconds(15), []{ return g_skin_applied; });
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
                    bool ok = wait_for_shutdown(g_skin_cv, lk, std::chrono::seconds(5), []{ return g_skin_applied; });
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
                bool ok = wait_for_shutdown(g_skin_cv, lk, std::chrono::seconds(5), []{ return g_skin_applied; });
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
            bool ok = wait_for_shutdown(g_mem_cv, lk, std::chrono::seconds(3), []{ return g_mem_applied; });
            body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
            content_type = "application/json";
        } else if ((p == "/frame" || p == "/stream") && method == "GET") {
            // ══ G8 CONTRACT (2026-09-13, agent H3 "capture-readback") ══════════
            // The capture is TWO-PHASE on the render thread: a request ARMS a
            // copy into a staging-ring slot (recorded into the frame's cmdbuf);
            // the GPU finishes it OFF the tick path; collect_readbacks() drains
            // finished slots at the end of each rendered frame. The tick loop
            // (same thread as Engine::frame()) NEVER waits on a readback now —
            // the old synchronous servicing froze it ~910 ms per pull
            // (docs/evidence/agent_fleet/SHIP/G8_CAPTURE/).
            //
            //  /frame   (default; "?sync=1" is the same thing spelled out)
            //      STRICTLY FRESH — byte-identical contract to the pre-G8
            //      route: THIS request's own capture is armed, then collected
            //      before the answer (watermark wait, 3 s deadline). The wait
            //      runs on the HTTP WORKER, not the render thread, so the tick
            //      loop does not feel it; only other HTTP polls still queue
            //      behind it on the single worker (unchanged). Every existing
            //      caller (cpp_bridge.fetch_frame and its movie renderers, the
            //      native labelers, the bench tools) keeps its exact
            //      guarantee: the bytes POSTDATE the request.
            //
            //  /frame?async=1 — TWO-PHASE for burst/trailer/bench callers:
            //      arms a capture (when a ring slot is free) and returns
            //      IMMEDIATELY. The contract for an armed-not-collected call
            //      is PRIOR FRAME BYTES: the last COLLECTED capture is encoded
            //      and served as usual (image/png|jpeg) — chosen over an empty
            //      202-style body or a Retry-After header because it keeps
            //      every response an IMAGE for naive .read() callers. Only
            //      when NO capture has ever completed does it answer the
            //      legacy {"ok":false,"error":"no frame"} JSON body. Freshness
            //      sits one arm-collect cycle (~2 frames) behind the default;
            //      use the default when bytes must postdate a /membrane or
            //      /camera POST (cpp_bridge.wait_for_frame_change also
            //      self-heals: it refetches until the frame differs).
            if (g_engine) {
                const bool want_async = f2::query_has(path, "async=1") &&
                                        !f2::query_has(path, "sync=1");   // sync wins if both
                std::vector<uint8_t> rgba; uint32_t w = 0, h = 0;
                bool have_frame = false;
                if (want_async) {
                    // arm (if a slot is free) and serve whatever is already
                    // collected — the two-phase answer, never a wait
                    g_engine->request_capture_async();
                    have_frame = g_engine->capture_frame(rgba, w, h);
                    if (!have_frame) {
                        body = "{\"ok\":false,\"error\":\"no frame\"}";
                        content_type = "application/json";
                    }
                } else {
                    // Strictly fresh: wait until a capture ARMED AT OR AFTER
                    // this request is COLLECTED. The watermark (arm-sequence)
                    // guard is load-bearing: a bare capture_ready() could be
                    // satisfied by a stale slot an earlier ?async=1 pull left
                    // in flight, silently serving pre-request pixels.
                    const uint64_t want = g_engine->capture_arm_watermark() + 1;
                    g_engine->request_capture();
                    auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(3);
                    while (!g_engine->capture_collected_since(want)) {
                        if (std::chrono::steady_clock::now() > deadline) break;
                        Sleep(5);
                    }
                    if (g_engine->capture_collected_since(want))
                        have_frame = g_engine->capture_frame(rgba, w, h);
                    if (!have_frame) {
                        body = "{\"ok\":false,\"error\":\"capture timeout\"}";
                        content_type = "application/json";
                    }
                }
                if (have_frame) {
                    // ══ F2 BEGIN: /frame fast path (prereg: docs/evidence/agent_fleet/ ══
                    // ══ MATTER_KERNEL/SEAL_PREREGISTRATION.md — "F2: /FRAME FAST PATH") ══
                    // The ~1.1 s floor lived in the ENCODE (stored-deflate PNG over the
                    // full 14.7 MB buffer), not the capture: the encode path below is
                    // UNTOUCHED (the capture fetch moved into the contract branches
                    // above, and the capture servicing itself went two-phase async in
                    // G8 — see the contract comment above this block). Wins, derived in
                    // the prereg: ?w= downscales BEFORE encode (box average, was a
                    // nearest skip); ?fmt=jpg encodes JPEG through in-box WIC at ?q=
                    // (default 85; WIC failure falls back to the PNG path — an image,
                    // never an error body). No params -> byte-identical full-res PNG,
                    // exactly the route that stood here.
                    static const bool f2_bench = []{
                        char buf[8];
                        return GetEnvironmentVariableA("CHIMERA_FRAME_BENCH", buf, sizeof(buf)) > 0;
                    }();
                    LARGE_INTEGER f2_qpf{}, f2_t0{}, f2_t1{}, f2_t2{}, f2_t3{};
                    if (f2_bench) { QueryPerformanceFrequency(&f2_qpf); QueryPerformanceCounter(&f2_t0); }
                    {
                        if (f2_bench) QueryPerformanceCounter(&f2_t1);
                        f2_t2 = f2_t1;
                        uint32_t want_w = f2::query_uint(path, "w=");
                        const bool want_jpg = f2::query_has(path, "fmt=jpg") ||
                                              f2::query_has(path, "fmt=jpeg");
                        uint32_t jpg_q = f2::query_uint(path, "q=");
                        if (jpg_q < 1 || jpg_q > 100) jpg_q = 85;
                        if (want_w && want_w < w) {
                            std::vector<uint8_t> down;
                            uint32_t nw = 0, nh = 0;
                            f2::box_downscale(rgba, w, h, down, nw, nh, want_w);
                            rgba.swap(down); w = nw; h = nh;
                            if (f2_bench) QueryPerformanceCounter(&f2_t2);
                        }
                        std::vector<uint8_t> encoded;
                        bool f2_jpeg_ok = false;
                        if (want_jpg)
                            f2_jpeg_ok = f2::jpeg_encode_wic(rgba.data(), w, h, jpg_q, encoded);
                        if (f2_jpeg_ok) {
                            content_type = "image/jpeg";
                        } else {
                            if (want_jpg)
                                fprintf(stderr, "F2: WIC JPEG refused (w=%u h=%u q=%u) -- PNG fallback\n",
                                        w, h, jpg_q);
                            encoded = png::encode_rgba(rgba.data(), w, h);
                            content_type = "image/png";
                        }
                        if (f2_bench) {
                            QueryPerformanceCounter(&f2_t3);
                            auto f2_ms = [](LARGE_INTEGER a, LARGE_INTEGER b, LARGE_INTEGER f) {
                                return (double)(b.QuadPart - a.QuadPart) * 1000.0 /
                                       (double)f.QuadPart;
                            };
                            fprintf(stderr,
                                    "F2 /frame: copy %.1f ms | downscale %.1f ms | encode %.1f ms "
                                    "-> %zu B (%s w=%u h=%u q=%u)\n",
                                    f2_ms(f2_t0, f2_t1, f2_qpf), f2_ms(f2_t1, f2_t2, f2_qpf),
                                    f2_ms(f2_t2, f2_t3, f2_qpf), encoded.size(),
                                    f2_jpeg_ok ? "jpeg" : "png", w, h, f2_jpeg_ok ? jpg_q : 0u);
                        }
                        body.assign(reinterpret_cast<const char*>(encoded.data()), encoded.size());
                        // ══ F2 END (route) ══════════════════════════════════════════════
                    }
                }
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
                content_type = "application/json";
            }
        } else if (p == "/glass" && method == "GET") {
            // THE GLASS CHANNEL: the composited window -- viewport + the Studio's
            // docked panels, status bar and HUD -- as the operator sees it. The
            // twin of /frame, which stays pixel-clean by design.
            if (g_engine) {
                g_engine->request_glass();
                auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(3);
                while (!g_engine->glass_ready()) {
                    if (std::chrono::steady_clock::now() > deadline) { body = "{\"ok\":false,\"error\":\"glass timeout\"}"; break; }
                    Sleep(5);
                }
                if (g_engine->glass_ready()) {
                    int gerr = g_engine->glass_err();
                    if (gerr == Engine::GLASS_ERR_NO_PRESENT) {
                        // FAIL LOUDLY: no presented image exists (minimized / out-of-date
                        // swapchain). A stale frame here would be an instrument claiming to
                        // have read a window that was never on screen.
                        body = "{\"ok\":false,\"error\":\"no present: the window is minimized or the "
                               "swapchain is out of date -- there is no glass to read\"}";
                        content_type = "application/json";
                    } else {
                        std::vector<uint8_t> rgba; uint32_t w = 0, h = 0;
                        if (g_engine->glass_frame(rgba, w, h)) {
                            std::vector<uint8_t> encoded = png::encode_rgba(rgba.data(), w, h);
                            body.assign(reinterpret_cast<const char*>(encoded.data()), encoded.size());
                            content_type = "image/png";
                        } else {
                            body = "{\"ok\":false,\"error\":\"no glass frame\"}";
                            content_type = "application/json";
                        }
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
                // THE TRANSPORT DRIVES THE LIVE CLOCK: with no joints pack the
                // period/total answer from the HINGE (its period, its ROMs) so
                // the timeline is live whenever a clock IS (the eye: "no play
                // button, no timeline" — the march is the show here).
                bool hinge_live = g_engine->hinge_active();
                float per_eff = nj ? per : (hinge_live ? g_engine->hinge_period() : 0.f);
                double total_eff = nj ? nj * static_cast<double>(per)
                                      : (hinge_live ? static_cast<double>(per_eff) : 0.0);
                body = std::string("{\"playing\":") + (g_engine->show_playing_.load() ? "true" : "false")
                     + ",\"time\":" + std::to_string(t)
                     + ",\"speed\":" + std::to_string(g_engine->show_speed_.load())
                     + ",\"n_joints\":" + std::to_string(nj)
                     + ",\"period\":" + std::to_string(per_eff)
                     + ",\"total\":" + std::to_string(total_eff)
                     + ",\"clock\":\"" + std::string(nj ? "joints" : (hinge_live ? "hinge" : "none")) + "\""
                     + ",\"current\":\"" + (nj ? g_engine->show_joint_name(cur)
                                                : std::string(hinge_live ? "knees (hinge march)" : "none")) + "\""
                     + ",\"theta\":" + std::to_string(nj ? g_engine->show_current_theta() : 0.0)
                     + ",\"joints_loaded\":" + (g_engine->joints_loaded() ? "true" : "false")
                     + ",\"hinge_loaded\":" + (hinge_live ? "true" : "false");
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
        } else if (p == "/compare" && (method == "GET" || method == "POST")) {
            // D4a: the automation twin of the reel's visible A/B selector.
            // POST queues intent; the render thread commits it before prepare(),
            // and GET exposes only that committed view state.
            if (g_engine && method == "POST") {
                std::string op = get_string(req_body, "op");
                bool clear = (op == "clear");
                int slot = static_cast<int>(get_float(req_body, "slot", -1.0f));
                g_engine->queue_ui_compare(slot, clear);
                body = "{\"ok\":true,\"queued\":true}";
            } else if (g_engine) {
                const StudioUI& u = g_engine->ui_;
                body = std::string("{\"ok\":true,\"a_slot\":") + std::to_string(u.compare_a_slot())
                     + ",\"b_slot\":" + std::to_string(u.compare_b_slot())
                     + ",\"a_seq\":" + std::to_string(static_cast<unsigned long long>(u.compare_a_seq()))
                     + ",\"b_seq\":" + std::to_string(static_cast<unsigned long long>(u.compare_b_seq()))
                     + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/rig" && (method == "GET" || method == "POST")) {
            // D8: explicit FK overlay control/state. Parent links are authored
            // by the rig map; this endpoint never infers topology.
            if (g_engine && method == "POST") {
                bool on = get_bool(req_body, "on", g_engine->rig_overlay_on());
                g_engine->set_rig_overlay(on);
            }
            body = std::string("{\"on\":") + ((g_engine && g_engine->rig_overlay_on()) ? "true" : "false")
                 + ",\"segments\":" + std::to_string(g_engine ? g_engine->ui_.rig_segment_count() : 0)
                 + "}";
            content_type = "application/json";
        } else if (p == "/light" && (method == "GET" || method == "POST")) {
            // THE LIGHT (2026-09-03): one scene-level fact. POST steers it
            // ({"x","y","z"} — normalized by the Studio; a zero vector is
            // refused), GET reads it back. The lit flank AND the contact
            // shadow consume this same vector through the UBO — they rotate
            // together in the same frame by construction.
            if (g_engine && method == "POST") {
                const float* cur = g_engine->light_dir();
                float lx = get_float(req_body, "x", cur[0]);
                float ly = get_float(req_body, "y", cur[1]);
                float lz = get_float(req_body, "z", cur[2]);
                g_engine->set_light(lx, ly, lz);
            }
            if (g_engine) {
                const float* L = g_engine->light_dir();
                body = std::string("{\"x\":") + std::to_string(L[0])
                     + ",\"y\":" + std::to_string(L[1])
                     + ",\"z\":" + std::to_string(L[2]) + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/studio" && method == "POST") {
            // THE ENGINE STUDIO: visibility plus deterministic workspace selection.
            if (g_engine) {
                bool on = get_bool(req_body, "on", !g_engine->ui_.visible);
                g_engine->ui_.set_visible(on);
                std::string mode = get_string(req_body, "mode");
                int mode_id = -1;
                if (mode == "board") mode_id = 0;
                else if (mode == "joints") mode_id = 1;
                else if (mode == "docs") mode_id = 2;
                else if (mode == "log") mode_id = 3;
                else if (mode == "scene") mode_id = 4;
                else if (mode == "capture") mode_id = 5;
                else if (mode == "poses") mode_id = 6;
                if (mode_id >= 0) g_engine->ui_.set_left_mode(mode_id);
                // 2026-09-05: POST /studio now also applies panel collapsed/size
                // to the LIVE state (not just the file). Before this, a POST with
                // {"right_collapsed":false} wrote the file but the live UI kept the
                // old value loaded at startup. Panel indices: 0 strip, 1 left,
                // 2 right, 3 bottom, 4 reel (ui.hpp set_panel_*).
                if (req_body.find("strip_collapsed") != std::string::npos)
                    g_engine->ui_.set_panel_collapsed(0, get_bool(req_body, "strip_collapsed", false));
                if (req_body.find("left_collapsed") != std::string::npos)
                    g_engine->ui_.set_panel_collapsed(1, get_bool(req_body, "left_collapsed", false));
                if (req_body.find("right_collapsed") != std::string::npos)
                    g_engine->ui_.set_panel_collapsed(2, get_bool(req_body, "right_collapsed", false));
                if (req_body.find("bottom_collapsed") != std::string::npos)
                    g_engine->ui_.set_panel_collapsed(3, get_bool(req_body, "bottom_collapsed", false));
                if (req_body.find("reel_collapsed") != std::string::npos)
                    g_engine->ui_.set_panel_collapsed(4, get_bool(req_body, "reel_collapsed", false));
                if (req_body.find("strip_size") != std::string::npos)
                    g_engine->ui_.set_panel_size(0, get_float(req_body, "strip_size", 92.f));
                if (req_body.find("left_size") != std::string::npos)
                    g_engine->ui_.set_panel_size(1, get_float(req_body, "left_size", 300.f));
                if (req_body.find("right_size") != std::string::npos)
                    g_engine->ui_.set_panel_size(2, get_float(req_body, "right_size", 330.f));
                if (req_body.find("bottom_size") != std::string::npos)
                    g_engine->ui_.set_panel_size(3, get_float(req_body, "bottom_size", 118.f));
                if (req_body.find("reel_size") != std::string::npos)
                    g_engine->ui_.set_panel_size(4, get_float(req_body, "reel_size", 172.f));
            }
            body = std::string("{\"on\":") + ((g_engine && g_engine->ui_.visible) ? "true" : "false")
                 + ",\"left_mode\":" + std::to_string(g_engine ? g_engine->ui_.left_mode() : -1) + "}";
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
                     + ",\"h\":" + std::to_string(g_engine->win_h())
                     // E2: the envelope's link-row rect (client pixels), zeroed
                     // when no envelope is up — panels publish their rects,
                     // never hide them (the /joints law); a synthetic click on
                     // its center IS the glass deep link.
                     + ",\"link\":[" + std::to_string(g_engine->ui_.link_hot_[0])
                     + "," + std::to_string(g_engine->ui_.link_hot_[1])
                     + "," + std::to_string(g_engine->ui_.link_hot_[2])
                     + "," + std::to_string(g_engine->ui_.link_hot_[3]) + "]"
                     + ",\"link_stage\":" + std::to_string(g_engine->ui_.selected_stage())
                     + ",\"rig_overlay\":" + (g_engine->rig_overlay_on() ? "true" : "false")
                     + ",\"state\":" + g_engine->ui_.studio_state_json()
                     + "}";
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
                // The path is JSON-escaped: the log pages carry ABSOLUTE Windows
                // paths, and a raw backslash is an illegal \escape in JSON —
                // every full-parse client died on it (found by the twin test).
                std::string pj;
                for (char c : g_engine->ui_.docs_path()) {
                    if (c == '\\' || c == '"') { pj += '\\'; pj += c; }
                    else pj += c;
                }
                body = std::string("{\"doc\":") + std::to_string(g_engine->ui_.docs_current())
                     + ",\"path\":\"" + pj + "\""
                     + ",\"mtime\":" + std::to_string(static_cast<unsigned long long>(g_engine->ui_.docs_mtime()))
                     + ",\"fnv\":\"" + hb + "\""
                     + ",\"n_lines\":" + std::to_string(g_engine->ui_.docs_line_count())
                     + ",\"n_display\":" + std::to_string(g_engine->ui_.docs_display_count())
                     + ",\"scroll\":" + std::to_string(g_engine->ui_.docs_scroll())
                     + ",\"scroll_max\":" + std::to_string(g_engine->ui_.docs_scroll_max())
                     // E2: the source line under the scroll's top (the wrap map
                     // read back) — a deep link's landing is PROVED here: the
                     // probe polls until top_src == the stage's doc line.
                     + ",\"top_src\":" + std::to_string(g_engine->ui_.docs_top_src()) + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/studio_doc" && method == "POST") {
            // E1a: HTTP docs navigation is acknowledged after the render thread
            // applies it, matching visible docs controls and idle behavior.
            if (g_engine) {
                const bool has_doc = req_body.find("\"doc\"") != std::string::npos;
                const bool has_scroll = req_body.find("\"scroll\"") != std::string::npos;
                const int doc = static_cast<int>(get_float(req_body, "doc", 0.0f));
                const float scroll = get_float(req_body, "scroll", 0.0f);
                int doc_result = -1;
                float scroll_result = 0.f;
                const bool ok = g_engine->request_ui_doc(doc, has_doc, scroll, has_scroll,
                                                         doc_result, scroll_result);
                body = std::string("{\"ok\":") + (ok ? "true" : "false")
                     + ",\"doc\":" + std::to_string(doc_result)
                     + ",\"scroll\":" + std::to_string(scroll_result)
                     + (ok ? "}" : ",\"error\":\"docs request not applied\"}");
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/link" && method == "POST") {
            // E2a: the deep link's HTTP twin uses the render-thread membrane.
            // The response is sent only after the same docs_link_stage() call
            // used by the glass has committed and the landing target is known.
            if (g_engine) {
                int stage = static_cast<int>(get_float(req_body, "stage", -1.0f));
                int line = -1, doc = -1;
                bool ok = g_engine->request_ui_link(stage, line, doc);
                body = std::string("{\"ok\":") + (ok ? "true" : "false")
                     + ",\"stage\":" + std::to_string(stage)
                     + ",\"line\":" + std::to_string(line)
                     + ",\"doc\":" + std::to_string(doc)
                     + (ok ? "}" : ",\"error\":\"link not resolved\"}");
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
                     + ",\"ft_int\":" + std::to_string(u.ft_int_f())
                     + ",\"ft_max\":" + std::to_string(u.ft_max_f())
                     + ",\"pushes\":" + std::to_string(static_cast<unsigned long long>(u.ft_pushes_))
                     + ",\"rec\":{" + std::string(u.ok() ? "\"ok\":true" : "\"ok\":false")
                     + ",\"calls\":" + std::to_string(static_cast<unsigned long long>(u.rec_calls_))
                     + ",\"draws\":" + std::to_string(static_cast<unsigned long long>(u.rec_draws_))
                     + ",\"bail_verts\":" + std::to_string(static_cast<unsigned long long>(u.rec_bail_verts_))
                     + ",\"bail_ok\":" + std::to_string(static_cast<unsigned long long>(u.rec_bail_ok_))
                     + ",\"bail_vbuf\":" + std::to_string(static_cast<unsigned long long>(u.rec_bail_vbuf_)) + "}"
                     + ",\"ring_n\":" + std::to_string(u.ft_ring_n_)
                     + ",\"ring\":[" + ring + "]"
                     + ",\"ph_fence_us\":" + std::to_string(static_cast<unsigned long long>(g_engine->ph_fence_us_.load()))
                     + ",\"ph_coll_us\":" + std::to_string(static_cast<unsigned long long>(g_engine->ph_coll_us_.load()))
                     + ",\"ph_pres_us\":" + std::to_string(static_cast<unsigned long long>(g_engine->ph_pres_us_.load()))
                     + ",\"rb_mem_type\":" + std::to_string(static_cast<unsigned long long>(g_engine->rb_mem_type_.load()))
                     + ",\"rb_mem_flags\":" + std::to_string(static_cast<unsigned long long>(g_engine->rb_mem_flags_.load()))
                     + ",\"gpu\":\"" + u.gpu_name_ + "\""
                     + ",\"stage\":\"" + u.chrome_stage_ + "\""
                     + ",\"board\":{\"stages\":" + std::to_string(u.board().stages.size())
                     + ",\"standing\":\"" + u.board().standing.substr(0, 60) + "\"}"
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
                    g_engine->ui_.set_bar_on(get_bool(req_body, "on", true));
                body = std::string("{\"ok\":true,\"bar_on\":")
                     + (g_engine->ui_.bar_on_ ? "true" : "false") + "}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/tick_state" && method == "GET") {
            // THE MEMBRANE TICK readback (Appliance 1)
            body = g_tick.state_json();
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
                body = std::string("{\"open\":") + (u.console_is_open() ? "true" : "false")
                     + ",\"input\":\"" + jesc(u.console_input_) + "\""
                     + ",\"hist_n\":" + std::to_string(u.console_history_.size())
                     + ",\"pending\":" + std::to_string(g_engine->console_pending())
                     + ",\"log\":[" + entries + "]}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/console" && method == "POST") {
            // F1a: the HTTP worker queues presentation changes; the render
            // thread applies the same console path as keyboard input and then
            // acknowledges the committed open state.
            if (g_engine) {
                const bool has_line = req_body.find("\"line\"") != std::string::npos;
                const bool has_open = req_body.find("\"open\"") != std::string::npos;
                const std::string line = has_line ? get_string(req_body, "line") : std::string();
                const bool open = get_bool(req_body, "open", false);
                bool open_result = false;
                const bool ok = g_engine->request_console_ui(line, has_line, open, has_open, open_result);
                body = std::string("{\"ok\":") + (ok ? "true" : "false")
                     + ",\"open\":" + (open_result ? "true" : "false")
                     + (ok ? "}" : ",\"error\":\"console request not applied\"}");
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
                        bool ok = wait_for_shutdown(g_mem_cv, lk, std::chrono::seconds(3), []{ return g_mem_applied; });
                        body = ok ? "{\"ok\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
                    }
                } else if (op == "fit") {
                    // C6 (the eye): framing derived from the live mesh — same
                    // membrane-request discipline as recall, so the camera moves
                    // on the render thread, never mid-frame.
                    float v[8];
                    if (!g_engine->camera_fit(v)) {
                        body = "{\"ok\":false,\"error\":\"no mesh loaded\"}";
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
                        bool ok = wait_for_shutdown(g_mem_cv, lk, std::chrono::seconds(3), []{ return g_mem_applied; });
                        body = ok ? "{\"ok\":true,\"fit\":true}" : "{\"ok\":false,\"error\":\"timeout\"}";
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
        } else if (p == "/capture" && method == "GET") {
            // D5: the capture session's twin — the SAME capture_kv() document
            // the CAPTURE dock draws.
            if (g_engine) {
                auto jesc = [](const std::string& s) {
                    std::string o; o.reserve(s.size() + 16);
                    for (char c : s) { if (c == '"' || c == '\\') { o += '\\'; o += c; } else o += c; }
                    return o;
                };
                auto kv = g_engine->capture_kv();
                std::string ls;
                for (size_t i = 0; i < kv.size(); ++i) {
                    ls += (i ? "," : "");
                    ls += std::string("{\"k\":\"") + jesc(kv[i].first)
                        + "\",\"v\":\"" + jesc(kv[i].second) + "\"}";
                }
                body = std::string("{\"state\":") + std::to_string(g_engine->capture_state_.load())
                     + ",\"lines\":[" + ls + "]}";
            } else {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            }
            content_type = "application/json";
        } else if (p == "/capture" && method == "POST") {
            // D5: {"op":"render","t0":0,"t1":2,"fps":24,"camera":"alpha",
            // "name":"walk"} — a WAITING endpoint (the /mesh_bin discipline):
            // the handler drives scrub -> present -> capture -> PNG per step;
            // the render thread owns the GPU. The clock (playing + time) is
            // restored after — a render never steals the operator's clock.
            if (!g_engine) {
                body = "{\"ok\":false,\"error\":\"no engine\"}";
            } else if (g_engine->capture_state_.load() == 1) {
                body = "{\"ok\":false,\"error\":\"a render is already running\"}";
            } else if (g_engine->scene_rows()[0].state == 0) {   // the body row: no mesh
                body = "{\"ok\":false,\"error\":\"no mesh loaded\"}";
            } else {
                double t0 = get_double(req_body, "t0", 0.0);
                double t1 = get_double(req_body, "t1", 1.0);
                int fps = static_cast<int>(get_double(req_body, "fps", 24.0));
                std::string name = get_string(req_body, "name");
                std::string camera = get_string(req_body, "camera");
                if (fps < 1) fps = 1; if (fps > 60) fps = 60;
                if (t0 < 0.0) t0 = 0.0;
                if (t1 <= t0) t1 = t0 + 1.0 / fps;
                if (name.empty()) {
                    char nb[32]; time_t now = time(nullptr);
                    strftime(nb, sizeof(nb), "cap_%H%M%S", localtime(&now));
                    name = nb;
                }
                for (char& c : name)   // path-safe: the name becomes a directory
                    if (!(isalnum(c) || c == '_' || c == '-')) c = '_';
                std::string dir = std::string("captures/") + name;
                CreateDirectoryA("captures", nullptr);
                CreateDirectoryA(dir.c_str(), nullptr);
                {
                    std::lock_guard<std::mutex> lk(g_engine->cap_m_);
                    g_engine->cap_t0_ = t0; g_engine->cap_t1_ = t1; g_engine->cap_fps_ = fps;
                    g_engine->cap_name_ = name; g_engine->cap_dir_ = dir;
                    g_engine->cap_camera_ = camera; g_engine->cap_error_.clear();
                }
                g_engine->capture_done_.store(0);
                g_engine->capture_state_.store(1);
                // camera first (the membrane request's thread discipline)
                if (!camera.empty()) {
                    float v[8];
                    if (g_engine->cam_mark_get(camera, v)) {
                        {
                            std::lock_guard<std::mutex> lk(g_mem_mutex);
                            memcpy(g_mem_req.cam_full, v, sizeof(v));
                            g_mem_req.cam_full_set = true;
                            g_mem_req.valid = true;
                            g_mem_pending = true;
                            g_mem_applied = false;
                        }
                        std::unique_lock<std::mutex> lk(g_mem_mutex);
                        wait_for_shutdown(g_mem_cv, lk, std::chrono::seconds(3), []{ return g_mem_applied; });
                    }
                }
                bool was_playing = g_engine->show_playing_.load();
                double was_time = g_engine->show_time_.load();
                g_engine->show_playing_.store(false);
                int N = static_cast<int>((t1 - t0) * fps + 0.5);
                if (N < 1) N = 1;
                g_engine->capture_total_.store(N);
                int written = 0;
                for (int i = 0; i < N; ++i) {
                    double t = t0 + static_cast<double>(i) / fps;
                    g_engine->show_scrub_.store(t);
                    // wait for the scrub to land (paused clock: exact)
                    auto dl = std::chrono::steady_clock::now() + std::chrono::seconds(2);
                    while (std::fabs(g_engine->show_time_.load() - t) > 1e-9) {
                        if (std::chrono::steady_clock::now() > dl) break;
                        Sleep(2);
                    }
                    // G8: wait on the watermark, not capture_ready() — the served
                    // frame must be one armed at/after THIS scrub landed, never a
                    // stale slot an earlier /frame?async=1 pull left in flight.
                    const uint64_t want = g_engine->capture_arm_watermark() + 1;
                    g_engine->request_capture();
                    auto dl2 = std::chrono::steady_clock::now() + std::chrono::seconds(3);
                    while (!g_engine->capture_collected_since(want)) {
                        if (std::chrono::steady_clock::now() > dl2) break;
                        Sleep(2);
                    }
                    std::vector<uint8_t> rgba; uint32_t w = 0, h = 0;
                    if (!g_engine->capture_collected_since(want) || !g_engine->capture_frame(rgba, w, h)) {
                        std::lock_guard<std::mutex> lk(g_engine->cap_m_);
                        g_engine->cap_error_ = "capture timeout at frame " + std::to_string(i);
                        break;
                    }
                    std::vector<uint8_t> pngb = png::encode_rgba(rgba.data(), w, h);
                    char fp[300];
                    snprintf(fp, sizeof(fp), "%s/f%04d.png", dir.c_str(), i);
                    FILE* f = fopen(fp, "wb");
                    if (!f) {
                        std::lock_guard<std::mutex> lk(g_engine->cap_m_);
                        g_engine->cap_error_ = "cannot write ";
                        g_engine->cap_error_ += fp;
                        break;
                    }
                    fwrite(pngb.data(), 1, pngb.size(), f);
                    fclose(f);
                    ++written;
                    g_engine->capture_done_.store(written);
                    g_engine->capture_t_.store(t);
                }
                // hand the clock back, exactly as found. The scrub lands on
                // the render thread's NEXT frame — so WAIT for it before
                // answering (the same discipline the per-frame scrub uses).
                // "ok" must mean the clock IS back, not that it will be soon.
                g_engine->show_scrub_.store(was_time);
                auto dl3 = std::chrono::steady_clock::now() + std::chrono::seconds(2);
                while (std::fabs(g_engine->show_time_.load() - was_time) > 1e-9) {
                    if (std::chrono::steady_clock::now() > dl3) break;
                    Sleep(2);
                }
                g_engine->show_playing_.store(was_playing);   // only once the time landed
                g_engine->capture_state_.store(written == N ? 2 : 3);
                if (written == N)
                    body = std::string("{\"ok\":true,\"frames\":") + std::to_string(written)
                         + ",\"dir\":\"" + dir + "\"}";
                else {
                    std::lock_guard<std::mutex> lk(g_engine->cap_m_);
                    body = std::string("{\"ok\":false,\"frames\":") + std::to_string(written)
                         + ",\"error\":\"" + g_engine->cap_error_ + "\"}";
                }
            }
            content_type = "application/json";
        } else if (p == "/debug" && method == "GET") {
            // vp_valid: is the stashed view/projection live? The C1 gizmo, /project
            // and the viewport grid all answer from it, so a false here means the
            // viewport has no frame of reference -- published because otherwise the
            // only symptom is "the grid silently isn't there".
            body = "{\"n\":" + std::to_string(g_engine ? g_engine->particle_count() : 0)
                 + ",\"active\":" + (g_membrane_active ? "true" : "false")
                 + ",\"vp_valid\":" + (g_engine && g_engine->vp_valid() ? "true" : "false")
                 + "}";
            content_type = "application/json";
        } else if (p == "/session" && method == "GET") {
            // SESSION SNAPSHOT status — what a restore would replay.
            body = "{";
            bool first = true;
            for (const char* ep : k_snapshot_endpoints) {
                std::ifstream f(std::string("session_snapshot/") + ep + ".blob", std::ios::binary | std::ios::ate);
                if (!first) body += ",";
                first = false;
                body += std::string("\"") + ep + "\":" + (f ? std::to_string((long long)f.tellg()) : std::string("null"));
            }
            body += "}";
            content_type = "application/json";
        } else if (p == "/session" && method == "POST") {
            // RESTORE: replay the snapshot blobs through the SAME handler the
            // HTTP server runs (invoke_api — raw bytes, nested call). The
            // console worker's law holds: this handler must not be the render
            // thread, and it is not — the HTTP worker (or argv restore at boot).
            std::string op = get_string(req_body, "op");
            if (op == "clear") {
                // An intentional emptiness must persist like a subject does:
                // clear deletes the snapshot blobs, so the next boot restores
                // NOTHING — an engine born empty on purpose, not by amnesia.
                // (Without this, default-on boot restore would resurrect a
                // subject the operator deliberately removed.)
                int cleared = 0;
                for (const char* ep : k_snapshot_endpoints) {
                    std::string fp = std::string("session_snapshot/") + ep + ".blob";
                    if (DeleteFileA(fp.c_str())) ++cleared;
                }
                if (DeleteFileA("session_snapshot/tick_seal_history.log")) ++cleared;
                if (DeleteFileA("session_snapshot/tick_limb_history.log")) ++cleared;
                if (DeleteFileA("session_snapshot/tick_limb_state.blob")) ++cleared;
                if (DeleteFileA("session_snapshot/tick_patch_state.blob")) ++cleared;
                body = "{\"ok\":true,\"cleared\":" + std::to_string(cleared) + "}";
            } else if (op == "restore") {
                int done = 0, failed = 0, seal_already = 0, seal_executed = 0;
                std::string detail;
                // THE REPLAY JOURNAL GATE: nothing the replay re-posts may
                // re-journal itself (the amplification law: measured +3
                // history lines per restore attempt before this guard).
                ReplayJournalGuard replay_guard;
                for (const char* ep : k_snapshot_endpoints) {
                    // Registries index the FINAL seal tree; legacy snapshots
                    // may need history replay to construct it first. Sensor
                    // continuation must follow that registry construction.
                    if (std::string(ep) == "tick_limb_state" ||
                        std::string(ep) == "tick_patch_state") continue;
                    std::string fp = std::string("session_snapshot/") + ep + ".blob";
                    std::ifstream f(fp, std::ios::binary);
                    if (!f) continue;
                    std::string blob((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
                    std::string resp2, ct2;
                    g_engine->invoke_api("POST", std::string("/") + ep, blob, resp2, ct2);
                    bool okr = resp2.find("\"ok\":true") != std::string::npos;
                    done += okr ? 1 : 0; failed += okr ? 0 : 1;
                    detail += std::string(ep) + (okr ? ":ok " : ":FAIL ");
                }
                // THE MITOSIS TREE comes back through its intent history:
                // every successful /tick_seal body was appended verbatim, so
                // replaying the file in order rebuilds the same cells —
                // EXCEPT that an intent whose state already exists now
                // answers "seal":"already" (the idempotent skip) instead of
                // executing-and-refusing, and SKIPPED entries are counted
                // honestly instead of poisoning the restore with failures
                // (measured before the fix: ok:false, failed 60-66, boot
                // retry loop re-initializing the body three times per boot).
                {
                    std::ifstream hf("session_snapshot/tick_seal_history.log");
                    std::string line;
                    while (std::getline(hf, line)) {
                        if (line.empty()) continue;
                        std::string resp2, ct2;
                        g_engine->invoke_api("POST", "/tick_seal", line, resp2, ct2);
                        bool already =
                            resp2.find("\"seal\":\"already\"") != std::string::npos;
                        bool okr = resp2.find("\"ok\":true") != std::string::npos;
                        if (already) {
                            ++seal_already;
                            detail += "seal:already ";
                        } else if (okr) {
                            ++done; ++seal_executed;
                            detail += "seal:ok ";
                        } else {
                            ++failed;
                            detail += "seal:FAIL ";
                        }
                    }
                }
                auto restore_limb_blob = [&]() -> int {
                    std::ifstream lf("session_snapshot/tick_limb_state.blob",
                                     std::ios::binary);
                    if (!lf) return -1;  // absent is distinct from refused
                    std::string blob((std::istreambuf_iterator<char>(lf)),
                                     std::istreambuf_iterator<char>());
                    std::string response, ct;
                    g_engine->invoke_api("POST", "/tick_limb_state", blob,
                                         response, ct);
                    return response.find("\"ok\":true") != std::string::npos ? 1 : 0;
                };
                int limb_state_result = restore_limb_blob();
                // AN2: THE LIMB PARTITION HISTORY (same two laws as the
                // seal journal): replayed only when the registry blob
                // could not do the job (a restored registry answers
                // "limb":"already" -- the executed partition is a STATE,
                // not an action to repeat). Sits AFTER the seal replay:
                // the partition needs the band tree the seals build.
                int limb_executed = 0;
                {
                    std::ifstream hf2("session_snapshot/tick_limb_history.log");
                    std::string line2;
                    while (std::getline(hf2, line2)) {
                        if (line2.empty()) continue;
                        std::string resp3, ct3;
                        g_engine->invoke_api("POST", "/tick_limb", line2,
                                             resp3, ct3);
                        bool alr =
                            resp3.find("\"limb\":\"already\"") != std::string::npos;
                        bool okr3 = resp3.find("\"ok\":true") != std::string::npos;
                        if (alr) {
                            detail += "limb:already ";
                        } else if (okr3) {
                            ++limb_executed;
                            detail += "limb:ok ";
                        } else {
                            ++failed;
                            detail += "limb:FAIL ";
                        }
                    }
                }
                // A pre-partition tree can be rebuilt by its limb history.
                // Reapply the saved registry's exact sensor parameters only
                // after that construction, then restore sensor dynamics once.
                if (limb_state_result == 0 && limb_executed > 0)
                    limb_state_result = restore_limb_blob();
                if (limb_state_result >= 0) {
                    done += limb_state_result == 1 ? 1 : 0;
                    failed += limb_state_result == 0 ? 1 : 0;
                    detail += limb_state_result == 1
                        ? "tick_limb_state:ok " : "tick_limb_state:FAIL ";
                }
                {
                    std::ifstream pf("session_snapshot/tick_patch_state.blob",
                                     std::ios::binary);
                    if (pf) {
                        std::string blob((std::istreambuf_iterator<char>(pf)),
                                         std::istreambuf_iterator<char>());
                        std::string response, ct;
                        g_engine->invoke_api("POST", "/tick_patch_state", blob,
                                             response, ct);
                        const bool okr = response.find("\"ok\":true") != std::string::npos;
                        done += okr ? 1 : 0; failed += okr ? 0 : 1;
                        detail += okr ? "tick_patch_state:ok " : "tick_patch_state:FAIL ";
                    }
                }
                // THE TREE RE-SNAPSHOT: if the replay EXECUTED cuts (the
                // state blob was absent or stale and history rebuilt the
                // tree), snapshot the fresh tree so the NEXT boot executes
                // zero seals. Replayed-but-skipped trees are byte-identical
                // and are NOT rewritten (byte-stable snapshot dir).
                if (failed == 0 && (seal_executed > 0 || limb_executed > 0)) {
                    std::vector<uint8_t> sb;
                    g_tick.export_seal_state(sb);
                    if (!sb.empty()) {
                        CreateDirectoryA("session_snapshot", nullptr);
                        std::ofstream sf("session_snapshot/tick_seal_state.blob",
                                         std::ios::binary);
                        if (sf) {
                            sf.write(reinterpret_cast<const char*>(sb.data()),
                                     (std::streamsize)sb.size());
                            printf("snapshot: tick_seal_state written (%zu B, "
                                   "%d seals executed)\n", sb.size(),
                                   seal_executed);
                        }
                    }
                    // AN2: the limb registry + patch state follow the tree
                    std::vector<uint8_t> lb;
                    g_tick.export_limb_state(lb);
                    if (!lb.empty()) {
                        std::ofstream lf("session_snapshot/tick_limb_state.blob",
                                         std::ios::binary);
                        if (lf)
                            lf.write(reinterpret_cast<const char*>(lb.data()),
                                     (std::streamsize)lb.size());
                    }
                    std::vector<uint8_t> pb;
                    g_tick.export_patch_state(pb);
                    if (!pb.empty()) {
                        std::ofstream pf("session_snapshot/tick_patch_state.blob",
                                         std::ios::binary);
                        if (pf)
                            pf.write(reinterpret_cast<const char*>(pb.data()),
                                     (std::streamsize)pb.size());
                    }
                }
                // THE OK RULE (R-restore-doctor): a boot whose seal tree
                // came back through the STATE blob answers with done == 0
                // and every history entry an already-skip — a full restore,
                // not a failure. failed == 0 plus SOMETHING satisfied
                // (executed or already) is the honest ok. A truly empty
                // snapshot stays ok:false (nothing to restore).
                body = std::string("{\"ok\":") + (failed == 0 && (done > 0 || seal_already > 0) ? "true" : "false")
                     + ",\"replayed\":" + std::to_string(done)
                     + ",\"failed\":" + std::to_string(failed)
                     + ",\"seal_already\":" + std::to_string(seal_already)
                     + ",\"seal_executed\":" + std::to_string(seal_executed)
                     + ",\"detail\":\"" + detail + "\"}";
#ifdef CHIMERA_SHUTDOWN_TEST
                printf("shutdown_test: session_result %s\n", body.c_str());
                fflush(stdout);
#endif
            } else {
                body = "{\"ok\":false,\"error\":\"want op=restore|clear\"}";
            }
            content_type = "application/json";
        } else {
            body = "Not found";
        }

        // ── SESSION SNAPSHOT (2026-09-02, the tool-alongside-the-game decree):
        // every successful *_bin upload is written THROUGH to
        // session_snapshot/<endpoint>.blob — a folder of raw bytes, replayed
        // verbatim by restore through the engine's stored api handler. The
        // session log records metadata; the snapshot holds the PAYLOADS. Today's
        // restarts cost three hand-run scripts; a reload is now one flag.
        if (g_engine && method == "POST" &&
            (p == "/mesh_bin" || p == "/hinge_bin" || p == "/joints_bin" ||
             p == "/gait_bin" || p == "/stride_bin" || p == "/water_bin") &&
            body.find("\"ok\":true") != std::string::npos) {
            CreateDirectoryA("session_snapshot", nullptr);   // idempotent
            std::string fn = "session_snapshot/" + p.substr(1) + ".blob";
            std::ofstream f(fn, std::ios::binary);
            if (f) { f.write(req_body.data(), (std::streamsize)req_body.size()); printf("snapshot: %s (%zu B)\n", fn.c_str(), req_body.size()); }
            else fprintf(stderr, "snapshot: cannot write %s\n", fn.c_str());
        }
        // THE TICK PAYLOADS join the snapshot: classification, travel
        // bindings, measured pins and the mitosis intents are the authored
        // creature — a restart must not need a hand-run script to be the
        // same animal. /tick_seal APPENDS (the tree is a history).
        if (g_engine && method == "POST" &&
            (p == "/tick_classify" || p == "/tick_vertbind" || p == "/tick_joints" || p == "/tick_body_bin") &&
            body.find("\"ok\":true") != std::string::npos) {
            CreateDirectoryA("session_snapshot", nullptr);
            std::string fn = "session_snapshot/" + p.substr(1) + ".blob";
            std::ofstream f(fn, std::ios::binary);
            if (f) { f.write(req_body.data(), (std::streamsize)req_body.size()); printf("snapshot: %s (%zu B)\n", fn.c_str(), req_body.size()); }
        }
        // THE SEAL JOURNAL + THE TREE SNAPSHOT (R-restore-doctor's two
        // laws): (1) only a seal that EXECUTED journals its intent, and
        // never one the replay re-posted — the replay's thread-local gate
        // stops the nested calls here, which is what grew the history
        // +3 lines per restore attempt (measured 60->63->66->69 across
        // R-after's single boot); an "already satisfied" skip produced no
        // state change and journals nothing either. (2) An executed cut
        // re-snapshots the TREE (tick_seal_state.blob) so the next boot
        // restores by state and replays the history as pure no-ops.
        if (g_engine && method == "POST" && p == "/tick_seal" &&
            !g_replay_in_flight &&
            body.find("\"ok\":true") != std::string::npos &&
            body.find("\"seal\":\"already\"") == std::string::npos) {
            CreateDirectoryA("session_snapshot", nullptr);
            std::ofstream f("session_snapshot/tick_seal_history.log", std::ios::app);
            if (f) { f << req_body << "\n"; printf("snapshot: tick_seal_history +1\n"); }
            std::vector<uint8_t> sb;
            g_tick.export_seal_state(sb);
            if (!sb.empty()) {
                std::ofstream sf("session_snapshot/tick_seal_state.blob",
                                 std::ios::binary);
                if (sf) {
                    sf.write(reinterpret_cast<const char*>(sb.data()),
                             (std::streamsize)sb.size());
                    printf("snapshot: tick_seal_state written (%zu B)\n",
                           sb.size());
                }
            }
        }
        // AN2 (same two laws): an EXECUTED limb partition journals its
        // intent and re-snapshots the registry + patch state; an
        // already-skip journals nothing. Every successful /tick_patch
        // re-snapshots the patch state (arm + connections are state).
        if (g_engine && method == "POST" && p == "/tick_limb" &&
            !g_replay_in_flight &&
            body.find("\"limb\":\"executed\"") != std::string::npos) {
            CreateDirectoryA("session_snapshot", nullptr);
            std::ofstream f("session_snapshot/tick_limb_history.log",
                            std::ios::app);
            if (f) { f << req_body << "\n"; printf("snapshot: tick_limb_history +1\n"); }
            // LMB1 indexes the post-partition tree. Saving only the registry
            // leaves a restart with old cells and an unrestorable registry.
            std::vector<uint8_t> sb;
            g_tick.export_seal_state(sb);
            if (!sb.empty()) {
                std::ofstream sf("session_snapshot/tick_seal_state.blob",
                                 std::ios::binary);
                if (sf)
                    sf.write(reinterpret_cast<const char*>(sb.data()),
                             (std::streamsize)sb.size());
            }
            std::vector<uint8_t> lb;
            g_tick.export_limb_state(lb);
            if (!lb.empty()) {
                std::ofstream lf("session_snapshot/tick_limb_state.blob",
                                 std::ios::binary);
                if (lf)
                    lf.write(reinterpret_cast<const char*>(lb.data()),
                             (std::streamsize)lb.size());
                printf("snapshot: tick_limb_state written (%zu B)\n", lb.size());
            }
            std::vector<uint8_t> pb;
            g_tick.export_patch_state(pb);
            if (!pb.empty()) {
                std::ofstream pf("session_snapshot/tick_patch_state.blob",
                                 std::ios::binary);
                if (pf)
                    pf.write(reinterpret_cast<const char*>(pb.data()),
                             (std::streamsize)pb.size());
            }
        }
        if (g_engine && method == "POST" && p == "/tick_patch" &&
            !g_replay_in_flight && body.find("\"ok\":true") != std::string::npos) {
            CreateDirectoryA("session_snapshot", nullptr);
            std::vector<uint8_t> pb;
            g_tick.export_patch_state(pb);
            if (!pb.empty()) {
                std::ofstream pf("session_snapshot/tick_patch_state.blob",
                                 std::ios::binary);
                if (pf)
                    pf.write(reinterpret_cast<const char*>(pb.data()),
                             (std::streamsize)pb.size());
                printf("snapshot: tick_patch_state written (%zu B)\n", pb.size());
            }
        }

        // F4: the recorder — every covered state change lands at the moment it
        // happens, with its OUTCOME (the response body is the truth of what
        // happened; a logged success for a failed event would be a lie).
        if (g_engine && method == "POST") {
            const char* kind = nullptr;
            if (p == "/mesh_bin" || p == "/hinge_bin" || p == "/joints_bin" ||
                p == "/gait_bin" || p == "/stride_bin" || p == "/water_bin") kind = "upload";
            else if (p == "/show" || p == "/joints" || p == "/gait" || p == "/stride" ||
                     p == "/water_clock" || p == "/studio" ||
                     p == "/studio_chrome" || p == "/link") kind = "mode";
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
        } catch (const ShutdownCancellation&) {
            // Nested /session calls catch independently, so an unapplied child
            // becomes a failed replay item rather than a false restore success.
            body = "{\"ok\":false,\"error\":\"shutdown in progress\"}";
            content_type = "application/json";
#ifdef CHIMERA_SHUTDOWN_TEST
            printf("shutdown_test: cancelled %s\n", path.c_str());
            fflush(stdout);
#endif
        }
    };
    bool http_ok = server.start(http_port, api);
    engine.set_api(api);   // F1: the console's worker runs the SAME handler
    if (!http_ok) {
        fprintf(stderr, "Warning: Failed to start HTTP server on port %d\n", http_port);
    }

    // SESSION SNAPSHOT: boot restore is DEFAULT-ON (2026-09-03, the recurring
    // "engine without the object" defect — the operator, the eye, and every
    // agent each forgot the old opt-in flag, and a fresh boot is born empty
    // because the subject lives only in VRAM). Every boot now replays the last
    // session's uploads — mesh, hinge, joints, gait, water — through the SAME
    // handler (invoke_api). `--no-restore` (any argv position) opts out for
    // tests; POST /session {"op":"clear"} makes emptiness intentional.
    // The replay re-snapshots each blob (same bytes, idempotent).
    // MEASURED 2026-09-02: invoking this on the main thread BEFORE the frame
    // loop starts makes the waiting endpoints time out (their fences are
    // consumed by frame()) — the blob still applies, but the ack is a lie.
    // So: deferred joinable thread, after the loop is alive; retry on FAIL.
    std::mutex boot_restore_mutex;
    std::condition_variable boot_restore_cv;
    std::atomic<bool> boot_restore_cancel{false};
    std::thread boot_restore_thread;
    {
        bool boot_restore = true;
        for (int i = 1; i < argc; ++i)
            if (std::string(argv[i]) == "--no-restore") boot_restore = false;
        if (boot_restore) {
            boot_restore_thread = std::thread([&engine, &boot_restore_mutex,
                                               &boot_restore_cv, &boot_restore_cancel] {
                auto delay_or_cancel = [&](std::chrono::milliseconds delay) {
                    return wait_for_shutdown_delay(boot_restore_mutex, boot_restore_cv,
                                                   boot_restore_cancel, delay);
                };
                if (delay_or_cancel(std::chrono::milliseconds(1500))) return;
                for (int attempt = 0; attempt < 3; ++attempt) {
                    if (g_shutdown_closing.load(std::memory_order_acquire)) return;
                    std::string resp, ct;
                    engine.invoke_api("POST", "/session", "{\"op\":\"restore\"}", resp, ct);
                    printf("session: boot restore -> %s\n", resp.c_str());
                    fflush(stdout);
                    if (g_shutdown_closing.load(std::memory_order_acquire)) return;
                    // THE SUCCESS SIGNAL (R-restore-doctor): the body's own
                    // "ok" is now authoritative — it is true whenever
                    // failed == 0 AND something was actually satisfied
                    // (executed seals OR already-skips), which covers the
                    // state-blob boot (replayed:0, seal_already:N) that the
                    // old replayed-count heuristic misread as failure and
                    // retried. The "replayed":0,"failed":0 case stays a
                    // success: an empty snapshot has nothing to restore.
                    bool ok = resp.find("\"ok\":true") != std::string::npos
                           && resp.find("\"failed\":0") != std::string::npos;
                    if (ok || resp.find("\"replayed\":0,\"failed\":0") != std::string::npos) {
                        // C6 (the eye, 2026-09-02): the boot camera targets the origin
                        // and crops the subject's feet. After a successful restore,
                        // re-derive the framing from the mesh that just came back —
                        // the operator never boots into a cropped hero. (A named
                        // bookmark is one POST /cameras {"op":"recall"} away.)
                        if (g_shutdown_closing.load(std::memory_order_acquire)) return;
                        std::string fresp, fct;
                        engine.invoke_api("POST", "/cameras", "{\"op\":\"fit\"}", fresp, fct);
                        printf("session: boot fit -> %s\n", fresp.c_str());
                        fflush(stdout);
                        return;
                    }
                    if (delay_or_cancel(std::chrono::milliseconds(2000))) return;
                }
            });
        }
    }

#ifdef _WIN32
    if (console_hidden) {
        HWND cw = GetConsoleWindow();
        if (cw) ShowWindow(cw, SW_HIDE);   // logs continue; the window retires
    }
#endif
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
#ifdef CHIMERA_SHUTDOWN_TEST
    const bool shutdown_test_hold_md = std::getenv("CHIMERA_SHUTDOWN_TEST_HOLD") != nullptr;
    bool shutdown_test_md_marked = false;
    bool shutdown_test_mesh_marked = false;
#endif

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
        if (g_shutdown_closing.load(std::memory_order_acquire)) quit = true;
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
                g_mem_req.cam_full_set = false;
                g_mem_req.cam_full[0] = g_mem_req.cam_full[1] = g_mem_req.cam_full[2] = 0.f;
                g_mem_req.cam_full[3] = g_mem_req.cam_full[4] = g_mem_req.cam_full[5] = 0.f;
                g_mem_req.cam_full[6] = g_mem_req.cam_full[7] = 0.f;
                g_mem_pending = false;
                g_mem_applied = true;
                g_mem_cv.notify_all();
            }
        }

        // Apply a pending GPU membrane-demo request on the render thread.
        {
            std::lock_guard<std::mutex> lk(g_md_mutex);
#ifdef CHIMERA_SHUTDOWN_TEST
            if (shutdown_test_hold_md && g_md_pending) {
                if (!shutdown_test_md_marked) {
                    printf("shutdown_test: md_pending_held\n");
                    fflush(stdout);
                    shutdown_test_md_marked = true;
                }
            } else
#endif
            if (g_md_pending) {
                bool ok = false;
                if (g_md_req.kind == 1) {
                    ok = engine.membrane_demo_init(g_md_req.upload);
                    if (ok) {
                        g_membrane_active = true;
                        engine.membrane_demo_status(g_md_req.status);
                    }
                } else if (g_md_req.kind == 2) {
                    ok = engine.membrane_demo_ctl(g_md_req.ctl_kind, g_md_req.n_steps,
                                                  g_md_req.gamma, g_md_req.status);
                } else {
                    ok = engine.membrane_demo_status(g_md_req.status);
                }
                g_md_req.ok = ok;
                g_md_pending = false;
                g_md_applied = true;
                g_md_cv.notify_all();
            }
        }

        // Apply a pending mesh request (Vulkan work must stay on this thread)
        {
            std::lock_guard<std::mutex> lk(g_mesh_mutex);
#ifdef CHIMERA_SHUTDOWN_TEST
            if (shutdown_test_hold_md && g_mesh_pending) {
                if (!shutdown_test_mesh_marked) {
                    printf("shutdown_test: mesh_pending_held\n");
                    fflush(stdout);
                    shutdown_test_mesh_marked = true;
                }
            } else
#endif
            if (g_mesh_pending) {
                if (g_mesh_req.update_only) {
                    engine.update_mesh(g_mesh_req.verts, g_mesh_req.N);
                } else if (g_mesh_req.slot == 1) {
                    engine.load_overlay(g_mesh_req.verts, g_mesh_req.indices, g_mesh_req.N, g_mesh_req.idxCount);
                } else {
                    engine.load_mesh(g_mesh_req.verts, g_mesh_req.indices, g_mesh_req.N, g_mesh_req.idxCount);
                    engine.set_mesh_mode(g_mesh_req.mode);
                }
                // THE MEMBRANE TICK: a slot-0 mesh is the cell field. Cells =
                // triangles; capacity = mat.skin yield x cell area (prereg).
                // The count drops to 0 first so the frame loop skips while
                // the cell field rebuilds (the restore thread may be here).
                if (g_mesh_req.slot == 0 && g_mesh_req.idxCount >= 3) {
                    g_tick_vcount = 0;
                    g_tick.init(g_mesh_req.idxCount / 3, g_mesh_req.indices,
                                g_mesh_req.verts);
                    g_tick_verts = g_mesh_req.verts;
                    g_tick_vcount = g_mesh_req.N;
                    engine.external_body_owner_.store(false);
                }                // cam_radius <= 0 = "keep the current camera": animation drivers stream
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
                } else if (g_volp_req.kind == 4) {
                    std::string raw(g_volp_req.blob.begin(),g_volp_req.blob.end());
                    g_volp_req.ok=g_tick.load_body_binding(raw);
                    if(g_volp_req.ok)engine.external_body_owner_.store(true);
                    g_volp_req.blob.clear();
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

        if(g_earth.active()) {
            try {auto view=g_earth.render();if(!engine.update_mesh(view.mesh,uint32_t(view.mesh.size()/9))) throw std::runtime_error("earth_render_update_failed");}
            catch(const std::exception& e){fprintf(stderr,"earth render: %s\n",e.what());}
        }
        GraphThermal::J thermal_frame_state;
        if(g_thermal.active()) {
            try {
                auto view=g_thermal.render();
                if(!engine.update_mesh(view.mesh,uint32_t(view.mesh.size()/9)))
                    throw std::runtime_error("thermal_render_update_failed");
                thermal_frame_state=std::move(view.state);
                // This graph fixture declares a fixed observation frame. Reapply
                // it so unrelated native view input cannot drift between trials.
                const auto camera=g_thermal.bundle.at("camera").get<std::array<float,8>>();
                engine.set_camera_full(camera.data());
            }catch(const std::exception& e){fprintf(stderr,"thermal render: %s\n",e.what());}
        }
        unsigned surface_frame_revision=0;
        if (g_science_surface.active) {
            std::lock_guard<std::mutex> lk(g_science_mutex);
            try {
                bool changed=g_science_surface.step();
                if(changed || g_science_surface.render_revision!=g_science_surface.revision) {
                    auto mesh=g_science_surface.mesh();
                    if(!engine.update_mesh(mesh,uint32_t(mesh.size()/9)))throw std::runtime_error("surface render update refused");
                }
                surface_frame_revision=g_science_surface.revision;
            }catch(const std::exception& ex){g_science_surface.error=ex.what();}
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
        const uint64_t thermal_capture_before=engine.capture_arm_watermark();
        auto ft0 = std::chrono::high_resolution_clock::now();
        if (!engine.frame()) {
            fprintf(stderr, "Frame failed\n");
            break;
        }
        auto ft1 = std::chrono::high_resolution_clock::now();
        if(!thermal_frame_state.is_null()) {
            const uint64_t revision=thermal_frame_state.at("scene_revision").get<uint64_t>();
            g_thermal.rendered(revision);
            thermal_frame_state["render_revision"]=revision;
            std::array<float,8> frame_camera{};engine.camera_state(frame_camera.data());
            thermal_frame_state["render_camera"]=frame_camera;
            const uint64_t armed=engine.capture_arm_watermark();
            std::lock_guard<std::mutex> lk(g_thermal_frame_mutex);
            for(uint64_t seq=thermal_capture_before+1;seq<=armed;++seq)
                g_thermal_frames[seq]=thermal_frame_state;
            while(g_thermal_frames.size()>128)g_thermal_frames.erase(g_thermal_frames.begin());
        }

        if (surface_frame_revision) {
            std::lock_guard<std::mutex> lk(g_science_mutex);
            // This revision passed through frame submission. /frame separately
            // waits for its own fresh GPU readback; this counter is not a fence.
            g_science_surface.render_revision=surface_frame_revision;
        }

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

        // THE MEMBRANE TICK (Appliance 1): per-frame cell update on the
        // render thread; the tint streams to the GPU through update_mesh
        // (in-place vertex upload, no reload, no camera).
        if (g_tick.enabled_ && g_tick_vcount > 0) {
            // measured frame dt for the tick's time-dependent physics
            // (the hydraulic return decays in real seconds, HR prereg)
            static auto tick_last = std::chrono::high_resolution_clock::now();
            auto tick_now = std::chrono::high_resolution_clock::now();
            float tick_dt = std::chrono::duration_cast<std::chrono::microseconds>(
                tick_now - tick_last).count() / 1e6f;
            tick_last = tick_now;
            if (tick_dt < 0.f) tick_dt = 0.f;
            if (tick_dt > 0.1f) tick_dt = 0.1f;
            g_tick.step(g_tick_verts, tick_dt);
            engine.update_mesh(g_tick_verts, g_tick_vcount);
        }

        // Frame cap (frame-stutter fix): uncapped, the engine free-ran at 300-1800 FPS
        // and fought llama-server (65%% GPU) for every slice — each inference burst
        // delayed frames unpredictably = the stutter. A metronome at 144 FPS yields
        // the GPU predictably and paces display delivery. timeBeginPeriod(1) is set
        // in main() so these short sleeps land at ~1 ms granularity, not 15.6.
        {
            // Headless (minimized): 120 fps is plenty for captures nobody is
            // watching, and halves the GPU pressure on whatever the operator
            // is actually looking at (the frame-stutter law, extended).
            const double target_ms = 1000.0 / (engine.headless_minimized_.load() ? 120.0 : 300.0);
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

    g_shutdown_closing.store(true, std::memory_order_release);
    printf("shutdown: admission_closed\n");
    fflush(stdout);
    notify_shutdown_channels();
    boot_restore_cancel.store(true, std::memory_order_release);
    notify_shutdown(boot_restore_mutex, boot_restore_cv);
    if (boot_restore_thread.joinable()) boot_restore_thread.join();
    printf("shutdown: boot_joined\n");
    fflush(stdout);
    server.stop();
    printf("shutdown: http_stopped\n");
    fflush(stdout);
    printf("Shutting down...\n");
    g_thermal.stop();
    g_earth.stop();
    engine.shutdown();
    printf("shutdown: engine_shutdown\n");
    fflush(stdout);
#ifdef CHIMERA_SHUTDOWN_TEST
    std::string late_body, late_type;
    api("GET", "/membrane_demo", "", late_body, late_type);
    printf("shutdown_test: late_api %s\n", late_body.c_str());
    fflush(stdout);
    if (late_body != "{\"ok\":false,\"error\":\"shutdown in progress\"}") return 2;
#endif
    return 0;
}
