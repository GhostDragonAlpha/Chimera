// P06 — offline window/input event-replay harness.
// NO window, NO GPU, NO Vulkan, NO OS calls. Drives the SAME translator TU
// the engine will link (ChimeraEngine/engine/platform/window_input.cpp) with
// a recording fake WindowHost, over golden transcripts. Suite W1–W4
// (docs/evidence/p06/P06_WINDOW_INPUT_PATCH_SPEC.md §6).
//
// Golden grammar (see tools/window_input_replay/README.md):
//   mode console <0|1>   set fake console state
//   mode ui     <0|1>    set fake StudioUI visibility
//   mode sphere <float>  set SceneRef.mesh_sphere
//   > <event>            append an InputEvent to the pending batch
//   |                    flush the batch through apply_input_event()
//   poll <dt>            run update_camera_input() (a fake frame)
//   ! <expectation>      check live state / recorded host calls
// Event syntax: down|down.r|up <key> | char <int> | move <x> <y> |
//   ldown <x> <y> | lup | rdown <x> <y> | rup | wheel <steps> <x> <y> |
//   resize <w> <h>
// Key tokens: W A S D Q E R P SPACE CTRL ESC UP DOWN LEFT RIGHT GRAVE F1..F8 (or a raw int)
#include "platform/window_input.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {

struct FakeHost : plat::WindowHost {
    bool console = false;
    bool ui      = false;
    std::string log;

    void rec(const std::string& what) { if (!log.empty()) log += " "; log += what; }

    bool console_open()        const noexcept override { return console; }
    bool ui_visible()          const noexcept override { return ui; }
    bool ui_mouse_captured()   const noexcept override { return false; }
    bool ui_consume_lbutton(int, int, bool) noexcept override { return false; }
    void ui_release_capture()        noexcept override { rec("ui_release_capture"); }
    bool ui_on_rbutton_down(int x, int y) noexcept override { rec("ui_rdown:" + std::to_string(x) + "," + std::to_string(y)); return false; }
    bool ui_on_rbutton_up(int x, int y) noexcept override { rec("ui_rup:" + std::to_string(x) + "," + std::to_string(y)); return false; }
    void ui_on_mouse_move(int x, int y) noexcept override { rec("ui_move:" + std::to_string(x) + "," + std::to_string(y)); }
    bool ui_on_wheel(int x, int y, float d) noexcept override { char b[64]; std::snprintf(b, sizeof b, "ui_wheel:%d,%d,%.6g", x, y, (double)d); rec(b); return false; }
    void set_capture(bool on)  noexcept override { rec(on ? "capture:on" : "capture:off"); }
    void console_toggle()      noexcept override { rec("console_toggle"); }
    void console_key(int c)    noexcept override { rec("console_key:" + std::to_string(c)); }
    void console_char(int c)   noexcept override { rec("console_char:" + std::to_string(c)); }
    void toggle_pose()         noexcept override { rec("toggle_pose"); }
    void ui_toggle()           noexcept override { rec("ui_toggle"); }
    void set_workspace(int i)  noexcept override { rec("workspace:" + std::to_string(i)); }
};

bool fail(const std::string& golden, int line_no, const std::string& what) {
    std::printf("FAIL %s:%d — %s\n", golden.c_str(), line_no, what.c_str());
    return false;
}

bool expect(const std::string& golden, int line_no, bool ok, const std::string& what) {
    if (!ok) return fail(golden, line_no, what);
    return true;
}

uint16_t key_code(const std::string& raw, const std::string& golden, int line_no,
                  bool& ok) {
    // Strip optional surrounding single quotes: 'W' -> W
    std::string tok = raw;
    if (tok.size() >= 2 && tok.front() == '\'' && tok.back() == '\'')
        tok = tok.substr(1, tok.size() - 2);
    ok = true;
    if (tok.size() == 1) return (uint16_t)tok[0];
    if (tok == "SPACE") return 0x20;
    if (tok == "CTRL")  return 0x11;
    if (tok == "ESC")   return 0x1B;
    if (tok == "LEFT")  return 0x25;
    if (tok == "UP")    return 0x26;
    if (tok == "RIGHT") return 0x27;
    if (tok == "DOWN")  return 0x28;
    if (tok == "GRAVE") return 0xC0;
    if (tok.size() >= 2 && tok[0] == 'F') {
        int n = std::atoi(tok.c_str() + 1);
        if (n >= 1 && n <= 8) return (uint16_t)(0x70 + n - 1);
    }
    char* end = nullptr;
    long v = std::strtol(tok.c_str(), &end, 0);
    if (end && *end == '\0' && v >= 0 && v <= 0xFF) return (uint16_t)v;
    ok = false;
    return 0;
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

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::printf("usage: window_input_replay <golden.txt> [more...]\n");
        return 2;
    }
    bool all_ok = true;
    for (int a = 1; a < argc; ++a) {
        const std::string golden = argv[a];
        std::FILE* f = std::fopen(golden.c_str(), "r");
        if (!f) { all_ok = false; std::printf("FAIL %s — cannot open\n", golden.c_str()); continue; }

        FakeHost host;
        plat::InputState st;
        plat::CameraState cam;
        plat::SceneRef scene;
        std::vector<plat::InputEvent> batch;
        int line_no = 0;
        int nevents = 0, nexpect = 0;
        bool ok_here = true;
        char buf[512];

        auto flush = [&]() -> bool {
            for (auto& ev : batch) { if (!plat::apply_input_event(ev, st, cam, scene, host)) { /* unconsumed == DefWindowProc, allowed */ } }
            nevents += (int)batch.size();
            batch.clear();
            return true;
        };

        while (ok_here && std::fgets(buf, sizeof buf, f)) {
            ++line_no;
            std::string ln = buf;
            while (!ln.empty() && (ln.back() == '\n' || ln.back() == '\r')) ln.pop_back();
            { auto hash = ln.find('#'); if (hash != std::string::npos) ln = ln.substr(0, hash); }  // inline comments
            if (ln.empty() || ln[0] == '#') continue;
            auto t = split(ln);
            if (t.empty()) continue;
            const std::string& cmd = t[0];
            bool kk = true;

            if (cmd == "mode" && t.size() >= 3) {
                bool v = t[2] == "1";
                if (t[1] == "console") host.console = v;
                else if (t[1] == "ui") host.ui = v;
                else if (t[1] == "sphere") scene.mesh_sphere = (float)std::atof(t[2].c_str());
                else ok_here = expect(golden, line_no, false, "unknown mode " + t[1]);
            } else if (cmd == ">") {
                plat::InputEvent ev{};
                if (t.size() < 2) { ok_here = false; break; }
                const std::string& k = t[1];
                if (k == "down" || k == "down.r") {
                    if (t.size() < 3) { ok_here = false; break; }
                    ev.kind = plat::InputKind::kKeyDown;
                    ev.repeat = (k == "down.r");
                    ev.key = key_code(t[2], golden, line_no, kk);
                } else if (k == "up") {
                    if (t.size() < 3) { ok_here = false; break; }
                    ev.kind = plat::InputKind::kKeyUp;
                    ev.key = key_code(t[2], golden, line_no, kk);
                } else if (k == "char") {
                    ev.kind = plat::InputKind::kChar;
                    ev.key = (uint16_t)std::atoi(t[2].c_str());
                } else if (k == "move") { ev.kind = plat::InputKind::kMouseMove; ev.x = atoi(t[2].c_str()); ev.y = atoi(t[3].c_str()); }
                else if (k == "ldown") { ev.kind = plat::InputKind::kLeftDown; ev.x = atoi(t[2].c_str()); ev.y = atoi(t[3].c_str()); }
                else if (k == "lup")   { ev.kind = plat::InputKind::kLeftUp; }
                else if (k == "rdown") { ev.kind = plat::InputKind::kRightDown; ev.x = atoi(t[2].c_str()); ev.y = atoi(t[3].c_str()); }
                else if (k == "rup")   { ev.kind = plat::InputKind::kRightUp; }
                else if (k == "wheel") { ev.kind = plat::InputKind::kWheel; ev.wheel = atoi(t[2].c_str()); ev.x = atoi(t[3].c_str()); ev.y = atoi(t[4].c_str()); }
                else if (k == "resize"){ ev.kind = plat::InputKind::kResize; ev.w = (uint32_t)atoi(t[2].c_str()); ev.h = (uint32_t)atoi(t[3].c_str()); }
                else { ok_here = fail(golden, line_no, "unknown event " + k); break; }
                if (!kk) { ok_here = fail(golden, line_no, "bad key token " + t[2]); break; }
                if (ok_here) batch.push_back(ev);
            } else if (cmd == "|") {
                ok_here = flush();
            } else if (cmd == "poll") {
                ok_here = flush();
                if (ok_here) plat::update_camera_input(cam, st, (float)std::atof(t[1].c_str()), scene, host);
            } else if (cmd == "!") {
                ok_here = flush();
                if (!ok_here) break;
                ++nexpect;
                const std::string& f = t[1];
                bool e = false;
                if (f == "keys" && t.size() >= 4) {
                    uint16_t c = key_code(t[2], golden, line_no, kk);
                    e = (st.keys[c & 0xFF] == ((uint16_t)std::atoi(t[3].c_str()) != 0));
                    if (!e) ok_here = fail(golden, line_no, "keys[" + std::to_string(c) + "] = " + std::to_string(st.keys[c & 0xFF]) + " expected " + t[3]);
                } else if (f == "captured") {
                    e = (st.mouse_captured == (t[2] == "1"));
                    if (!e) ok_here = fail(golden, line_no, "mouse_captured = " + std::to_string(st.mouse_captured) + " expected " + t[2]);
                } else if (f == "cam") {
                    const std::string& which = t[2];
                    float got = 0, want = (float)std::atof(t[3].c_str());
                    if (which == "theta") got = cam.theta;
                    else if (which == "phi") got = cam.phi;
                    else if (which == "radius") got = cam.radius;
                    else if (which == "pan_x") got = cam.pan_x;
                    else if (which == "pan_y") got = cam.pan_y;
                    else if (which == "target0") got = cam.target[0];
                    else if (which == "target1") got = cam.target[1];
                    else if (which == "target2") got = cam.target[2];
                    else { ok_here = fail(golden, line_no, "unknown cam field " + which); break; }
                    e = (std::fabs(got - want) < 1e-6f);
                    if (!e) ok_here = fail(golden, line_no, which + " = " + std::to_string(got) + " expected " + std::to_string(want));
                } else if (f == "psize") {
                    uint32_t pw = st.pending_resize_w.load(), ph = st.pending_resize_h.load();
                    e = (pw == (uint32_t)atoi(t[2].c_str()) && ph == (uint32_t)atoi(t[3].c_str()));
                    if (!e) ok_here = fail(golden, line_no, "pending resize = " + std::to_string(pw) + "x" + std::to_string(ph) + " expected " + t[2] + "x" + t[3]);
                } else if (f == "calls") {
                    std::string want = ln.substr(std::strlen("! calls "));
                    while (!want.empty() && (want.back() == ' ' || want.back() == '\t')) want.pop_back();
                    if (want == "<none>") want.clear();
                    e = (host.log == want);
                    if (!e) ok_here = fail(golden, line_no, "host log = [" + host.log + "] expected [" + want + "]");
                    host.log.clear();
                } else {
                    ok_here = fail(golden, line_no, "unknown expectation " + f);
                }
            } else {
                ok_here = fail(golden, line_no, "unknown directive " + cmd);
            }
        }
        std::fclose(f);
        if (!ok_here) { all_ok = false; continue; }
        std::printf("PASS %s — %d events, %d expectations\n",
                    golden.c_str(), nevents, nexpect);
    }
    std::printf("%s\n", all_ok ? "window_input_replay: ALL PASS" : "window_input_replay: FAILURES");
    return all_ok ? 0 : 1;
}