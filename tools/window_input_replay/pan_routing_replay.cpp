// BP-PAN — offline replay fixture for the PROPOSED right-drag-pan routing
// patch (docs/evidence/p06/PAN_ROUTING_PATCH.md).
//
// This TU is NOT the engine and NOT the P06 current translator
// (window_input.cpp). It is THE PATCH MADE EXECUTABLE: the diff's routing logic
// (g_drag_button tracking + the two condition guards) mirrored line-for-line
// against the P06 event model (platform/window.h InputEvent / CameraState).
// It is deliberately built OUTSIDE the engine and never linked into it.
//
// What it proves (fixtures PAN_ROUTING_P1..P4.txt under docs/evidence/p06/):
//   P1  L-drag orbits (theta/phi) and leaves pan_x/pan_y untouched.
//   P2  R-drag pans (pan_x/pan_y) and leaves theta/phi untouched.
//   P3  a quick R-click is consumed by the menu path with no pan.
//   P4  g_drag_button state does not leak between consecutive drags.
//
// Grammar (subset of tools/window_input_replay/README.md):
//   mode ui <0|1>    mode menu <0|1>    mode console <0|1>
//   > ldown <x> <y>  > lup  > rdown <x> <y>  > rup   > move <x> <y>
//   |                flush the pending batch through the patched executor
//   ! captured <0|1> ! cam <field> <float> (tol 1e-6) ! calls <record|none>
#include "platform/window_input.h"   // P06 types (InputEvent + CameraState) — the
                                     // translator TU window_input.cpp is NOT compiled here

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {

// The patch's `g_drag_button` (0=none, 1=L, 2=R) as the diff specifies it.
enum DragButton : int { kNone = 0, kLeft = 1, kRight = 2 };

struct DragState {
    bool captured = false;
    int  button   = kNone;
    int  lmx = 0, lmy = 0;
};

// Arithmetic strings VERBATIM from engine.cpp (the "no new camera semantics"
// law): orbit 0.005f/0.003f (:195-196), pan 0.02f (:226-227).
constexpr float kOrbitDx = 0.005f;
constexpr float kOrbitDy = 0.003f;
constexpr float kPan     = 0.02f;

struct FixtureHost {
    bool ui           = false;   // mode ui
    bool menu_consumes = false;  // mode menu — ui_on_rbutton_up returns true
    std::string log;

    void rec(const std::string& w) { if (!log.empty()) log += " "; log += w; }
};

// THE PATCH, EXECUTABLE — WndProc's mouse routing AS PAN_ROUTING_PATCH.md
// specifies it, nothing else (keyboard/wheel/resize arms are not in fixture
// scope and return unconsumed). Mirrors the diff's only two text changes: the
// two `g_drag_button == N` guards on the captured-move arms.
bool apply_patched(const plat::InputEvent& ev, DragState& st,
                   plat::CameraState& cam, FixtureHost& host) {
    switch (ev.kind) {
    case plat::InputKind::kMouseMove:
        // THE STUDIO hook (engine.cpp:165) runs before the capture arms.
        if (host.ui) host.rec("ui_move:" + std::to_string(ev.x) + "," + std::to_string(ev.y));
        // PATCH guard 1: only L drags orbit (engine.cpp:191, + `g_drag_button == 1`).
        if (st.captured && st.button == kLeft) {
            const float dm   = static_cast<float>(ev.x - st.lmx);
            const float dm_y = static_cast<float>(ev.y - st.lmy);
            cam.theta -= dm * kOrbitDx;
            cam.phi   -= dm_y * kOrbitDy;   // drag UP -> camera UP (screen y grows down)
            st.lmx = ev.x; st.lmy = ev.y;
            return true;
        }
        // PATCH guard 2: R drags reach the (previously dead) pan arm (engine.cpp:221,
        // + `g_drag_button == 2`). Pan math verbatim :226-227.
        if (st.captured && st.button == kRight) {
            const float dm   = static_cast<float>(ev.x - st.lmx);
            const float dm_y = static_cast<float>(ev.y - st.lmy);
            cam.pan_x -= dm * kPan;
            cam.pan_y += dm_y * kPan;       // camera-local XZ plane, scaled by radius
            st.lmx = ev.x; st.lmy = ev.y;
            return true;
        }
        return false;

    case plat::InputKind::kLeftDown:        // engine.cpp:180-186 + g_drag_button = 1
        st.captured = true; st.button = kLeft;
        st.lmx = ev.x; st.lmy = ev.y;
        host.rec("capture:on");
        return true;

    case plat::InputKind::kLeftUp:          // engine.cpp:187-190 + clear
        if (st.captured) { host.rec("capture:off"); st.captured = false; }
        st.button = kNone;
        return true;

    case plat::InputKind::kRightDown:       // engine.cpp:205-213 + g_drag_button = 2
        if (host.ui) host.rec("ui_rdown:" + std::to_string(ev.x) + "," + std::to_string(ev.y));
        st.captured = true; st.button = kRight;
        st.lmx = ev.x; st.lmy = ev.y;
        host.rec("capture:on");
        return true;

    case plat::InputKind::kRightUp:         // engine.cpp:214-220 + clear before the menu
        if (st.captured) { host.rec("capture:off"); st.captured = false; }
        st.button = kNone;
        // The click/drag split lives in ui.cpp:319-357 (travel under 4px = click);
        // it consumes -> the menu opens and no pan has happened (no moves).
        if (host.ui && host.menu_consumes) { host.rec("menu:open"); return true; }
        return true;

    default:
        return false;   // keyboard / wheel / resize: out of fixture scope
    }
}

bool fail(const std::string& f, int ln, const std::string& what) {
    std::printf("FAIL %s:%d — %s\n", f.c_str(), ln, what.c_str());
    return false;
}

std::vector<std::string> split(const std::string& s) {
    std::vector<std::string> out;
    size_t i = 0;
    while (i < s.size()) {
        while (i < s.size() && (s[i] == ' ' || s[i] == '\t')) ++i;
        size_t j = i;
        while (j < s.size() && s[j] != ' ' && s[j] != '\t') ++j;
        if (j > i) out.push_back(s.substr(i, j - i));
        i = j;
    }
    return out;
}

int run_one(const std::string& path) {
    std::FILE* f = std::fopen(path.c_str(), "r");
    if (!f) { std::printf("FAIL %s — cannot open\n", path.c_str()); return 1; }
    FixtureHost host;
    DragState st;
    plat::CameraState cam;
    std::vector<plat::InputEvent> batch;
    int line = 0, nevents = 0, nexpect = 0;
    bool ok = true;
    char buf[512];

    auto flush = [&]() {
        for (auto& ev : batch) apply_patched(ev, st, cam, host);
        nevents += (int)batch.size();
        batch.clear();
    };

    while (ok && std::fgets(buf, sizeof buf, f)) {
        ++line;
        std::string ln = buf;
        while (!ln.empty() && (ln.back() == '\n' || ln.back() == '\r')) ln.pop_back();
        { auto h = ln.find('#'); if (h != std::string::npos) ln = ln.substr(0, h); }
        if (ln.empty() || ln[0] == '#') continue;
        auto t = split(ln);
        if (t.empty()) continue;
        const std::string& cmd = t[0];

        if (cmd == "mode" && t.size() >= 3) {
            const bool v = t[2] == "1";
            if (t[1] == "ui") host.ui = v;
            else if (t[1] == "menu") host.menu_consumes = v;
            else if (t[1] == "console") {/* accepted for grammar parity */}
            else ok = fail(path, line, "unknown mode " + t[1]);
        } else if (cmd == ">") {
            plat::InputEvent ev{};
            if (t.size() < 2) { ok = false; break; }
            const std::string& k = t[1];
            if (k == "ldown")  { ev.kind = plat::InputKind::kLeftDown;  ev.x = atoi(t[2].c_str()); ev.y = atoi(t[3].c_str()); }
            else if (k == "lup") ev.kind = plat::InputKind::kLeftUp;
            else if (k == "rdown") { ev.kind = plat::InputKind::kRightDown; ev.x = atoi(t[2].c_str()); ev.y = atoi(t[3].c_str()); }
            else if (k == "rup") ev.kind = plat::InputKind::kRightUp;
            else if (k == "move") { ev.kind = plat::InputKind::kMouseMove; ev.x = atoi(t[2].c_str()); ev.y = atoi(t[3].c_str()); }
            else { ok = fail(path, line, "unknown event " + k); break; }
            if (ok) batch.push_back(ev);
        } else if (cmd == "|") {
            flush();
        } else if (cmd == "!") {
            flush();
            ++nexpect;
            const std::string& f2 = t[1];
            bool e = false;
            if (f2 == "captured") {
                e = (st.captured == (t[2] == "1"));
                if (!e) ok = fail(path, line, "captured = " + std::to_string(st.captured) + " expected " + t[2]);
            } else if (f2 == "cam") {
                const std::string& which = t[2];
                float got = 0, want = (float)std::atof(t[3].c_str());
                if (which == "theta") got = cam.theta;
                else if (which == "phi") got = cam.phi;
                else if (which == "pan_x") got = cam.pan_x;
                else if (which == "pan_y") got = cam.pan_y;
                else { ok = fail(path, line, "unknown cam field " + which); break; }
                e = (std::fabs(got - want) < 1e-6f);
                if (!e) ok = fail(path, line, which + " = " + std::to_string(got) + " expected " + std::to_string(want));
            } else if (f2 == "calls") {
                std::string want = ln.substr(std::strlen("! calls "));
                while (!want.empty() && (want.back() == ' ' || want.back() == '\t')) want.pop_back();
                if (want == "<none>") want.clear();
                e = (host.log == want);
                if (!e) ok = fail(path, line, "host log = [" + host.log + "] expected [" + want + "]");
                host.log.clear();
            } else {
                ok = fail(path, line, "unknown expectation " + f2);
            }
        } else {
            ok = fail(path, line, "unknown directive " + cmd);
        }
    }
    std::fclose(f);
    if (!ok) return 1;
    std::printf("PASS %s — %d events, %d expectations\n", path.c_str(), nevents, nexpect);
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) { std::printf("usage: pan_routing_replay <p1.txt> [p2.txt ...]\n"); return 2; }
    int rc = 0;
    for (int a = 1; a < argc; ++a) rc |= run_one(argv[a]);
    std::printf("%s\n", rc == 0 ? "pan_routing_replay: ALL PASS" : "pan_routing_replay: FAILURES");
    return rc;
}