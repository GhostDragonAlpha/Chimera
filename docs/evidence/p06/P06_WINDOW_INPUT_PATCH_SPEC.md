# P06 — Window/input boundary: patch specification (prepare only)

Status: **SPECIFICATION, NOT IMPLEMENTATION.** P06 prepares the window/input
boundary so a later increment can implement a non-Windows window backend
(Linux is the settled direction; `docs/THE_RENDERER_DECISION.md`). It makes NO
production code change to the engine, starts NO live-engine control, and
invents NO new camera semantics. The deliverable is this document: the
ownership map, the seam contract, exact signatures, file ownership,
dependency order, the smallest behavior-preserving first increment, and the
offline event-replay test plan with STATEMENT / PREDICTION / FALSIFIER named
for every test.

Unpublished until it passes the same protected-path / normal-push /
isolated-checkout discipline as every prior evidence commit.

Companion records:
- P05 command-record correction (the actual commands as run): appended to
  `docs/evidence/p05/P05_REPAIR_R1.md` in the same commit as this spec.
- Line anchors below refer to the current remote head
  `902dc80ac2f83c295dd1dfe1d49e2eae3d74ceec`.

---

## 1. Ownership map (current, both files)

The window and its input are split across `ChimeraEngine/engine/engine.cpp`
and `ChimeraEngine/engine/main.cpp`. This is the fact that defeats any plan
that "just extracts main.cpp" — the window, the WndProc, the camera state and
the resize/minimize law all live in `engine.cpp`; only the message pump lives
in `main.cpp`.

### 1.1 engine.cpp owns

| Lines | What |
|---|---|
| 3–4 | `#include <windows.h>`, `#include <vulkan/vulkan_win32.h>` |
| 19–20 | `WINDOW_TITLE`, `static HWND g_hwnd` — the only native-handle holder |
| 23–31 | `CameraState` (theta/phi/radius/pan_x/pan_y/target[3]) + `static g_cam` |
| 32–34 | `g_mouse_captured`, `g_last_mx`, `g_last_my`, `g_keys[256]` — capture + key state, all file-scope |
| 35 | `g_key_engine` — the WndProc's backdoor into `Engine` (pose/UI) |
| 43–44 | `g_pending_resize_w/h` — `std::atomic<uint32_t>`, written by WndProc, consumed by `frame()` |
| 63–98 | `update_camera_input(cam, dt)` — polled camera translation (WASD/QE/space/ctrl/R) gated on `ui_.console_open()` |
| 100–247 | `WndProc` — the WHOLE input decoder + translator: WM_CLOSE→DestroyWindow, WM_DESTROY→PostQuitMessage(0), WM_SIZE→atomics, WM_KEYDOWN/SYSKEYDOWN (backtick console edge, P pose, F1, F2–F8 workspace, `g_keys` table), WM_KEYUP, WM_CHAR (console), WM_MOUSEMOVE/LBUTTONDOWN/UP (StudioUI panel consume + capture), orbit drag, WM_RBUTTONDOWN/UP (pan + context menu), WM_MOUSEWHEEL (docs-under-cursor or radius, `ScreenToClient`) |
| 249–300 | `create_window(w, h)` — RegisterClassEx("ChimeraEngine"), AdjustWindowRect, CreateWindowEx(WS_OVERLAPPEDWINDOW…), bar-off-screen clamp (MonitorFromWindow/GetMonitorInfoA/SetWindowPos), ShowWindow, UpdateWindow; sets `g_hwnd` |
| 412 | `g_key_engine = this` (init) |
| 434–438 | init §1 calls `create_window(cfg.width, cfg.height)` |
| 526–545 | seam call `plat::create_surface(instance_, g_hwnd, surf_out)` — native handle BORROWED by the surface seam |
| 794–934 | `shutdown()` — destroys surface(921), device(922), debug messenger(924–929), instance(930), **window LAST** `DestroyWindow(g_hwnd); g_hwnd=nullptr`(932) |
| 5726–5744 | `update_camera_matrices` — aspect from `extent_`; spherical→eye; `look_at` |
| 6451–6458 | `frame()` B1: consume `g_pending_resize_*` (skip when 0) → `resize(prw,prh)` |
| 6736–6757 | acquire OUT_OF_DATE/minimize law: nonzero currentExtent → `resize(caps…)`; 0x0 (minimized) → `headless_minimized_=true`, offscreen render + capture continue; SUCCESS → `false` |
| 7809–7844 | `Engine::resize` — `vkDeviceWaitIdle`, 0x0 skip, rebuild swapchain/depth/framebuffers/offscreen/UI |
| 2757, 7804 | `Sleep(1)` (UI throttle block), `Sleep(8)` (idle pacing law) |

### 1.2 main.cpp owns

| Lines | What |
|---|---|
| 5–9 | `winsock2.h`, `ws2tcpip.h`, `windows.h`, `mmsystem.h`, `#pragma comment(lib,"winmm.lib")` |
| 283 | `handleCtrlC` → returns TRUE (swallows Ctrl+C; the engine exits only via the window X) |
| 285 | `handleSignal(int)` → `exit(0)` (non-Windows path only) |
| 2496–2501 | `SetConsoleCtrlHandler(handleCtrlC, TRUE)` / `signal(SIGINT/SIGTERM)` |
| 2510–2522 | the pump: `while (PeekMessage(&msg,nullptr,0,0,PM_REMOVE))`, intercept WM_QUIT/WM_CLOSE→quit, Translate+Dispatch. The drain-ALL-per-frame comment (the queue-starvation fix) is contract |
| 2735–2738 | `engine.frame()` failure → break |
| 2838–2840 | "Shutting down…", `engine.shutdown()`, `return 0` |
| 930/1454/1482/2281/2287/2319, 2753, 2778 | `Sleep(...)` in HTTP handler pacing + idle + frame cap |

### 1.3 Threading model (why extraction is low-risk)

The message pump, the WndProc dispatch, `frame()`, and the resize consumer are
ALL on the single main thread. `g_keys`/`g_cam`/`g_mouse_captured`/`g_last_*`
are written by WndProc and read by `frame()`/`update_camera_matrices` on that
same thread — no locking exists or is needed (ui.hpp:131 documents exactly
this). The `std::atomic<uint32_t>` on the resize pair is belt-and-suspenders;
the seam must preserve it as-is (see §5).

The HTTP server runs on other threads and reaches the engine ONLY through
mutex+CV gated request structs, applied inside the frame loop (main.cpp
2524–2685). No HTTP path touches the window. That separation is a boundary
the seam must NOT cross.

---

## 2. Design: a platform seam mirroring the P05 surface seam

The P05 `plat::` surface seam (`engine/platform/vulkan_surface.*`) is the
established pattern in this repo for exactly this cut: tagged backends,
`/*_win32.cpp` / `/*_unavailable.cpp`, OS types kept out of the shared header,
results as `Outcome` structs, teardown ownership explicitly "the caller owns".
The window/input seam reuses that shape so the two seams compose.

The cut that makes P06 safe:

- **What moves to a backend:** native window creation/destruction, message
  decoding, event pumping. All Win32 calls (`RegisterClassEx`, `CreateWindowEx`,
  `PeekMessage`, `SetCapture`, `ScreenToClient`, `DestroyWindow`…) end up behind
  `window_win32.cpp`. A stub `window_unavailable.cpp` stands in for the future
  Linux backend and names the contract.
- **What stays in engine.cpp:** ALL translation of decoded input into intent —
  the current WndProc body minus its message decoding, ported VERBATIM into a
  pure `plat::apply_input_event(ev, st, cam, host)`. Camera arithmetic is
  copied string-for-string; it is asserted equal by golden replay (§7), not
  re-derived. **This is the "no new camera semantics" law.**
- **What the backend emits:** `InputEvent` — an OS-neutral event. The neutral
  key space is **the Win32 VK_* numeric range, adopted as interchange** (see
  note in §4). The future Linux backend carries its own xkb/evdev→VK_* table in
  the SAME increment that adds it.
- **What the engine's pump loop becomes:** `plat::pump_events` drains the OS
  queue (preserving drain-everything-per-frame), collecting a FIFO batch of
  `InputEvent`s; the loop then feeds them to `apply_input_event` in order. The
  capture cursor succussion (`SetCapture`/`ReleaseCapture`) goes through the
  injected `WindowHost::set_capture` inside the apply pass — legal on the
  message thread even outside the dispatch frame.

Rationale for the decoding/translation split (the load-bearing decision): the
decoder is the ONLY non-portable part; the translator is the ONLY testable
part. Separating them means the offline replay suite exercises the translator
with no OS calls at all, and the decoder is covered by a thin Windows-only
smoke suite (§8). The former is cross-platform CI-able; the latter is not.
This is the same reasoning that split the P05 seam into enumeration (portable)
and create (Win32-only) halves.

---

## 3. Files (new; the P06 commit carries ONLY these)

```
ChimeraEngine/engine/platform/window.h             NEW — shared types, backend tags, entry points
ChimeraEngine/engine/platform/window_win32.cpp     NEW — Win32 window backend (DECLARED contract; body lands Inc 3)
ChimeraEngine/engine/platform/window_unavailable.cpp NEW — stub backend (backend B)
ChimeraEngine/engine/platform/window_input.h       NEW — InputEvent decode→intent translator decl
ChimeraEngine/engine/platform/window_input.cpp     NEW — translator TU (verbatim WndProc port; compiled by the harness NOW, by the engine at Inc 3)
tools/window_input_replay/CMakeLists.txt           NEW — offline replay harness (NO window, NO GPU)
tools/window_input_replay/replay_main.cpp          NEW — runner driving goldens through the translator
tools/window_input_replay/README.md                NEW — suite structure + how goldens are recorded
docs/evidence/p06/P06_WINDOW_INPUT_PATCH_SPEC.md   THIS SPEC
docs/evidence/p06/P06_COMMAND_RECORD_CORRECTION.md — the corrected P05 command record (actual, as-ran)
docs/evidence/p06/goldens/P06_GOLDEN_TRANSCRIPT_*.txt — test data recorded per §6 (P06-A: format +
                                                     one hand-authored sample; the live capture
                                                     session is an implementation-increment gate)
```

**Every `.cpp`/`.h` above is declared but NOT compiled into the engine in
P06.** P06 builds the Windows surface seam untouched; the two new `window_*`
backends are NOT wired into `engine/CMakeLists.txt` (the engine's CMake diff
is empty). Only `tools/window_input_replay` is wired — a standalone target
that must build and run offline (its `apply_input_event` path contains no OS
or Vulkan dependency).

The command-record correction file is split from the spec so the P05 doc can
point at a dedicated artifact (append-only discipline, §10).

---

## 4. Exact interface signatures

### 4.1 `window.h` — shared types and entry points (no OS types)

```cpp
#pragma once
#include <cstdint>
#include <cstddef>

namespace plat {

// Neutral input event. `key` carries the Win32 VK_* numeric code in the
// interchange space (see NOTE). `repeat` = "autorepeat/previous-state set"
// (the WndProc lParam bit-30 edge law), only meaningful for key events.
enum class InputKind : uint8_t {
    kClose,            // title-bar X / WM_CLOSE — the ONLY normal exit
    kResize,           // client w,h; (0,0) = minimized (frame() skips 0)
    kKeyDown, kKeyUp,  // g_keys[ key & 0xFF ] write
    kChar,             // console printable (WM_CHAR)
    kMouseMove,        // client x,y
    kLeftDown, kLeftUp,
    kRightDown, kRightUp,
    kWheel,            // wheel in 120-units (steps); x,y ALREADY client (backend did ScreenToClient)
};

struct InputEvent {
    InputKind kind;
    uint16_t  key;      // kWheel: unused; others: VK_* code unless noted
    bool      repeat;   // key events only
    int32_t   x, y;     // client coords (kWheel: after the client conversion)
    int32_t   wheel;    // kWheel only: 120-unit steps
    uint32_t  w, h;     // kResize only, client px
};

// Opaque window. OS handle lives inside the backend; `native` is exposed for
// the surface seam only.
struct Window {
    void*    native = nullptr;
    uint32_t client_w = 0, client_h = 0;
};

struct WindowCreateOutcome {
    enum class Status : uint8_t { kCreated, kFailed, kUnavailable };
    Status      status;
    Window      window;      // written ONLY on kCreated
    const char* error;       // static-storage text on !kCreated; nullptr on kCreated
};

WindowCreateOutcome create_window(uint32_t w, uint32_t h);   // request; outcome carries actual extent
void                destroy_window(Window& win);             // idempotent; nulls native
void*               native_handle(const Window& win);        // feeds plat::create_surface's void* param

// Drains the OS queue once, appending every decoded event in FIFO order.
// Returns true iff the caller should exit (WM_QUIT or WM_CLOSE). The caller
// owns the drain-when-empty policy (current: keep draining per frame).
// kClose is returned through `exit_now` ONLY; it is never emitted as an
// InputEvent (preserves today's pump-intercepts-WM_CLOSE behavior exactly).
bool pump_events(Window& win, std::vector<InputEvent>& out);
```

> NOTE — VK codes as interchange space: adopting the numeric VK_* range is a
> deliberate, recorded decision, NOT a shortcut. Rationale: (a) `g_keys[256]`
> is indexed by `wp & 0xFF`; resymbolizing to a fresh enum would touch the
> translator's arms and break the golden-replay guarantee; (b) the camera and
> console semantics keyed to VK_ codes are behavior, not platform, and P06
> preserves behavior exactly; (c) the future Linux backend's mapping table
> (xkb->VK_*) lands in the same increment that adds the backend and is subject
> to its OWN test (W5, §8.3). Documented here so the reviewer knows the
> portability debt is scoped, not hidden.

### 4.2 `window_input.h` — translator declaration (engine-land, pure)

```cpp
#pragma once
#include "platform/window.h"
#include <cstdint>

namespace plat {

// Camera state + input state as CURRENTLY in engine.cpp, moved out of
// anonymous scope into named types (structural move only — fields and
// arithmetic strings unchanged).
struct CameraState {
    float theta = 0.0f;         // current values keep today's defaults
    float phi   = 0.3f;
    float radius = 12.0f;
    float pan_x = 0.0f, pan_y = 0.0f;
    float target[3] = {0, 0, 0};
};

struct InputState {
    bool                 keys[256] = {};          // parity with g_keys[]
    bool                 mouse_captured = false;  // parity with g_mouse_captured
    int32_t              last_mx = 0, last_my = 0;
    std::atomic<uint32_t> pending_resize_w{0};    // identical memory story to today
    std::atomic<uint32_t> pending_resize_h{0};
};

// Scene data the translation reads (the radius_floor zoom law reads the
// posted mesh's bounding-sphere radius at engine.cpp:51). Moved out of
// engine.cpp's file-scope g_mesh_sphere so the translator stays pure.
struct SceneRef {
    float mesh_sphere = 0.0f;   // drives radius_floor = fmax(1, sphere*1.02)
};

// The engine's UI gates, injected so the translator is callable with a
// recording fake (offline tests) or the real engine (production).
struct WindowHost {
    virtual ~WindowHost() = default;
    virtual bool console_open()          const noexcept = 0;
    virtual bool ui_visible()            const noexcept = 0;
    virtual bool ui_mouse_captured()     const noexcept = 0;   // border-drag pose
    virtual bool ui_consume_lbutton(int x, int y, bool down) noexcept = 0;
    virtual void ui_release_capture()                 noexcept = 0;
    virtual bool ui_on_rbutton_down(int x, int y)     noexcept = 0;
    virtual bool ui_on_rbutton_up(int x, int y)       noexcept = 0;
    virtual void ui_on_mouse_move(int x, int y)       noexcept = 0;
    virtual bool ui_on_wheel(int x, int y, float delta) noexcept = 0;
    virtual void set_capture(bool on)                 noexcept = 0;  // SetCapture/ReleaseCapture binding
    virtual void console_toggle()                     noexcept = 0;
    virtual void console_key(int code)                noexcept = 0;
    virtual void console_char(int c)                  noexcept = 0;
    virtual void toggle_pose()                        noexcept = 0;
    virtual void ui_toggle()                          noexcept = 0;
    virtual void set_workspace(int idx)               noexcept = 0;
};

// The CURRENT WndProc body, ported verbatim, reachable without Windows.h.
// Exactly one InputEvent processed per call, in arrival order. Returns
// "consumed" (true = do NOT DefWindowProc — parity with WndProc's early
// returns). The `g_key_engine &&` guards are discharged by "a host is ALWAYS
// bound once the window exists" (window creation runs after g_key_engine=this
// in Engine::init, so no input can arrive before init completes).
bool apply_input_event(const InputEvent& ev,
                       InputState& st,
                       CameraState& cam,
                       SceneRef& scene,
                       WindowHost& host) noexcept;

// Parity with update_camera_input(g_cam, cfg_.dt) — the per-frame keyboard
// poll. Reads st.keys[] exactly as the original reads g_keys[].
void update_camera_input(CameraState& cam,
                         const InputState& st,
                         float dt,
                         const SceneRef& scene,
                         const WindowHost& host) noexcept;

}
```

### 4.3 `window_win32.cpp` — decode rules (behavior map, WndProc → seam)

The decode is a straight transcription of engine.cpp:100–247 minus the
translation, i.e.:

| WndProc arm (today) | Seam destination |
|---|---|
| WM_CLOSE | `WindowCreateOutcome` unused here → translator `kClose`; WndProc KEEPS its `DestroyWindow(hwnd)` for non-pump dispatch paths; pump maps WM_CLOSE to exit_now (§4.1). Dual path preserved exactly. |
| WM_DESTROY → PostQuitMessage(0) | backend posts quit (unchanged); `exit_now` true next pump. |
| WM_SIZE → atomics | `InputEvent{kResize, w=LO, h=HI}` — (0,0) minimized is carried through; translator writes `pending_resize_*` and frame()'s skip-0 test is unchanged. |
| WM_KEYDOWN/SYSKEYDOWN, repeat bit | `kKeyDown` + `repeat=(lp & 0x40000000)`; `g_keys[wp&0xFF]` written by the translator. Edge-triggered arms (backtick/P/F1/F2–F8) move VERBATIM into the translator; they are pure given `repeat`. |
| WM_KEYUP/SYSKEYUP | `kKeyUp`; translator clears bit. |
| WM_CHAR (console open) | `kChar`; translator gates on host.console_open(). |
| WM_MOUSEMOVE/LBUTTONDOWN/UP, RBUTTONDOWN/UP | decoded with client x,y; the StudioUI-consume-then-orbit order is the TRANSLATOR's logic (it decides consumption; only SetCapture/ReleaseCapture go through host.set_capture). |
| WM_MOUSEWHEEL | backend converts screen→client (`ScreenToClient`) THEN emits `kWheel` — ScreenToClient leaves the translator; x,y in kWheel are already client. |
| bar-off-screen clamp | backend code inside create (MonitorFromWindow etc. never reach the translator). |
| WM_CLOSE/WM_DESTROY double paths | both live per today: pump intercepts WM_CLOSE for the exit decision; WndProc handles a directly-DestroyWindow'd lifetime for shutdown's tail. The smoke suite (§8) asserts no double-destroy (destroy_window is idempotent). |

### 4.4 Thickness of the P06 commit (what is NOT built)

P06 wires nothing into the engine's CMake. `engine.cpp` is **untouched at the
source level**. The two `window_*` backends exist only as declared targets on
paper; the replay harness compiles `window_input.h` + `replay_main.cpp` + a
pure translator DUPLICATE? No — see §7: the offline suite consumes the
translator SOURCE (a single TU `window_input.cpp` IS added and target-linked
into the harness; the engine still doesn't use it). The translator TU is
compiled twice — once by the harness with a fake host, later once by the
engine — and that is the extraction proof point.

File table with exact ownership:
| File | Owner | Built by |
|---|---|---|
| `window.h` | plat (headers live `engine/platform/`, shared) | harness + (future) engine |
| `window_input.h` / `window_input.cpp` | plat translator | harness NOW; engine when increment lands |
| `window_win32.cpp` | backend A header-only-declared; implementation lands with inc. 3 | (future) |
| `window_unavailable.cpp` | backend B | (future) |
| `tools/window_input_replay/*` | harness | harness NOW |

---

## 5. Dependency order + smallest behavior-preserving first increment

Dependency order (a window needs the seam in this order):
1. `window.h` (types) → 2. `window_input.{h,cpp}` (translator, depends on window.h only) → 3. harness (depends on 1+2) → 4. `window_win32.cpp` (uses 1, calls translator) → 5. engine wiring (uses 1+2+4) → 6. Linux backend (maps to 1, new `window_wayland.cpp`-style file, carries its own xkb table).

**Smallest first increment (Inc 1, the P06 gate):**
- Add `window.h`, `window_input.{h,cpp}` as NEW files; compile NOTHING in the
  engine; add the standalone replay harness target; record the golden format
  + one hand-authored sample; append the P05 command-record correction.
- Increment gate: `tools/window_input_replay` builds with a fake host and runs
  W1–W4 below against the sample data; engine CMake remains UNCHANGED (a
  `git diff` proving `engine/*` untouched is part of the gate); 23/23 `.spv`
  identity is trivially satisfied (no engine change); no live-engine control.

Subsequent increments (implemented later, each with its own gate):
- **Inc 2** ESL/license this comment: record goldens from a live Windows
  session (registering the recorder is a logging-only change → bare gate:
  goldens captured, engine behaves as recorded).
- **Inc 3** wire the translator: engine.cpp's WndProc becomes the decode shell
  + `apply_input_event` calls; globals become `InputState`/`CameraState`.
  Gate: W1–W4 replay green against Inc-2 goldens; Windows smoke suite green;
  23/23 `.spv` identical; FPS path unchanged.
- **Inc 4** migrate creation + pump into `window_win32.cpp` behind §4
  signatures; `g_hwnd` becomes `plat::Window`; teardown order preserved
  (window last). Gate: smoke suite (capture/close/resize/re-arm) green;
  replay suite green; `plat::create_surface(instance_, native_handle(g_wnd), …)`
  compiles and the surface seam's own 31/31 probe still passes.
- **Inc 5** (future, out of P06 scope) Linux backend + xkb table + W5.

Each increment preserves: the atomics (memory story), the drain-EVERY-event
per frame order, the WM_CLOSE dual path, the consume-before-orbit order,
the minimized-headless law, and the window-destroyed-last teardown.

---

## 6. Offline event-replay tests — STATEMENT / PREDICTION / FALSIFIER

**Suite identity:** offline = no GPU, no window, no Vulkan, no OS calls in the
path under test. The translator + a recording `WindowHost` fake run the same
TU the engine will link. Test data = golden transcripts (recorded live from
the CURRENT engine per §7, or hand-authored bedside cases in this commit).
The suite is intentionally SEPARATE from the Windows interaction tests (§8)
and from the future Linux window tests (§8.3) — a window may never open here.

### W1 — Keyboard ordering + key-state parity

- **STATEMENT:** the translator, given the ordered `InputEvent` stream for any
  interleaving of keyDown/keyUp with repeat flags and console-open window
  states, produces the SAME `InputState.keys[]`, the same edge-trigger
  decisions (console-toggle, P, F1, F2–F8), and the same console key/char
  forwarding as the current WndProc on the identical message sequence.
- **PREDICTION:** every golden transcript replays to a captured intent
  snapshot byte-for-byte in `keys[]`, and the recording fake logs the same
  `set_workspace/toggle_pose/ui_toggle/console_*` call list.
- **FALSIFIER:** a single bit difference in `keys[]`, one missing or extra
  edge-trigger, one console leak (a workspace key or P firing while console
  open), or an order inversion relative to the golden. The increment that
  produced it reverts.

### W2 — Mouse capture + camera-delta parity

> **CORRECTED during the P06 ownership inspection (recorded discrepancy, §12):**
> the current WndProc's right-drag PAN arm (engine.cpp:221–231) is UNREACHABLE
> DEAD CODE — the first `WM_MOUSEMOVE && g_mouse_captured` arm (engine.cpp:191)
> returns before it ever runs. Observed behavior at `902dc80a`: every captured
> drag (left OR right) ORBITS; pan_x/pan_y never change at runtime despite the
> "Right-drag pan" help text (main.cpp:2492). W2 asserts the REACHABLE behavior;
> the dead arm is NOT silently fixed (a fix is a camera-semantics change and
> belongs to a later, separately-gated increment).

- **STATEMENT:** the capture/last-position discipline (capture on LeftDown
  while not captured, drag deltas from `last_mx/my`, ReleaseCapture on Up) and
  the orbit vs pan vs zoom split are invariant under extraction, measured on
  the REACHABLE path: left drag = theta/phi orbit, right drag = theta/phi
  orbit (same arm), wheel = radius (docs-under-cursor when the StudioUI is
  visible), pan never executes.
- **PREDICTION:** for golden transcripts of left/right drags and wheel events,
  the replayed `CameraState` deltas equal the captured floats bit-for-bit,
  `host.set_capture` toggles on/off in the same places, and pan_x/pan_y stay
  0.000000 across a right drag (the golden locks the dead-arm proof).
- **FALSIFIER:** an orbit/zoom delta differing in any bit, capture left
  asserted on mouse-up, pan_x/pan_y differing from 0 on any captured drag, or
  the wheel's docs-vs-zoom routing changing. Reverts the increment.

### W3 — Resize/minimize intent ordering

- **STATEMENT:** `kResize` events write `pending_resize_*` only, frame()-side
  skips the (0,0) minimized pair, and a later nonzero extent rebuilds — the
  exact current law.
- **PREDICTION:** replaying [kResize(0,0), kResize(800,600), kResize(1920,1080)]
  leaves pending {0,0} then {800,600} then {1920,1080} with no dropped or
  reordered write; the harness's fake frame() calls `resize` only when BOTH
  values are nonzero, and never with a zero extent.
- **FALSIFIER:** a resize write lost or duplicated out of order, or a zero
  extent reaching the fake frame() (`resize(0,0)`). Reverts the increment.

### W4 — Console gating (the focus discipline)

- **STATEMENT:** while the console is open, camera polling, P, F1, and the
  F2–F8 workspace keys are suppressed EXACTLY as today, because the gating
  lives in the shared translator over `host.console_open()`, not in the backend.
- **PREDICTION:** a transcript [backtick toggle, typed 'w', 'P', 'A', backtick
  toggle, 'A'] replays with: chars forwarded, zero camera delta while open,
  P not toggled while open, and the post-close 'A' again moving the camera —
  matching a live recording of the same keys.
- **FALSIFIER:** any key affecting camera/pose/workspace while open, or the
  backtick toggle failing to open/close. Reverts the increment.

---

## 7. Golden-transcript provenance (honesty requirement)

P06 ships goldens that are **hand-authored bedside cases** (documented as
such) because the live-recording session is an Inc-2 gate, not a P06 action
(recording requires touching the engine; P06 does not). The format is defined
now so the Inc-2 recorder writes byte-compatible transcripts:

```
# golden W2-drag-hit-slow.txt  (hand-authored P06 bedside case; live-captured
#   replacement scheduled Inc-2; source = engine.cpp WndProc verified 902dc80a)
> LDown 512 384
> MOVE 514 386
> MOVE 518 390
< capture on
< cam.dtheta -0.010000000000000009  cam.dphi -0.006...
> LUp
< capture off
```

`>` = InputEvent batch input; `<` = recorded intent side-effects expected by
the player. Each golden names the WndProc source revision it was written
against. A golden without such a header is rejected by the harness.

## 8. The OTHER suites (kept separate, by design)

### 8.1 Windows interaction tests (separate target, requires a real message thread)

`tools/window_smoke/` — real `HWND`, real `PostMessage`, real pump. Asserts:
WM_CLOSE → pump exit_now + engine.shutdown path runs exactly once;
WM_SIZE handling feeds a real swapchain-independent consume (layout only);
capture toggles really move capture; destroy_window idempotence (no
double-DestroyWindow). No GPU needed, a window IS needed → NOT part of the
offline suite; run only in the Windows interaction phase (Inc 3+).

### 8.2 (P06-scope boundary) — replay harness runs on the CI host with NO window

`tools/window_input_replay` runs headless on anything with a C++17 compiler;
no Vulkan headers required.

### 8.3 Future Linux window tests (W5, pre-registered, NOT to be run by P06)

- **STATEMENT:** when the Linux backend lands, its xkb/evdev→VK_* mapping is
  exercised by W1–W4 rerun against Linux-recorded goldens, PLUS a new W5 that
  asserts every key used by wasd/qe/space/ctrl/r/backtick/P/F1–F8 maps to the
  same VK_* code the translator keys on.
- **PREDICTION:** a Wayland/X11 session records transcripts that replay
  identically through the SAME translator TU.
- **FALSIFIER:** any mapping that changes an edge-trigger decision or a camera
  delta for the supported control set. The backend reverts.

---

## 9. Linux blockers (out of scope; recorded so the follow-up is priced)

These are the remaining non-portable surfaces a Linux build encounters; P06
only lists them with evidence so the follow-up can be scoped before
implementation:

| Surface | Evidence | Note |
|---|---|---|
| Window/WndProc (this spec) | engine.cpp:3–4, 100–300, 932 | the subject of this spec |
| Pump + console Ctrl+C path | main.cpp:5–9, 283–285, 2496–2501, 2510–2522 | pump handled here; `handleSignal` already exists for POSIX |
| `Sleep(...)` pacing | engine.cpp:2757, 7804; main.cpp:930,1454,1482,2281,2287,2319,2753,2778; http_server.cpp:76 | needs `std::this_thread::sleep_for` in the port; NOT part of the window seam |
| Winsock HTTP server | http_server.cpp:2–3,11 | full socket layer port; separate workstream |
| GDI font measurement (StudioUI) | ui.cpp:5, 2862–2893 (CreateCompatibleDC, CreateFontW, SelectObject) | font metrics are WINDOWING-adjacent but NOT window lifetime — decide with the UI workstream |
| `mmsystem.h`/winmm.timeBeginPeriod | main.cpp:8–9 + main() timeBeginPeriod | frame-metronome; separate |
| SharedRing / png_encoder | (no windows.h/winsock includes found by include scan) | appear platform-neutral; SHALLOW scan only — verify before relying |
| Vulkan surface on non-Win | P05: `vulkan_surface_unavailable.cpp` deliberately returns kUnavailable | the window seam will call `create_surface` with a real native handle only after a surface backend exists; today's no-headless law holds |

---

## 10. Append-only evidence discipline

- The P05 command-record correction is a NEW file
  (`P06_COMMAND_RECORD_CORRECTION.md`) plus an APPENDED pointer in
  `P05_REPAIR_R1.md` — R0 files are never edited (repo convention,
  P05_REPAIR_R1.md:1–9). See task §10 of this commit.
- Every golden names its source revision; hand-authored goldens are labeled.
- Nothing in this commit is compiled into the engine; the only new build
  target is the offline replay harness.

## 11. Verification summary (what P06 actually proves vs. defers)

| Claim | State after this commit |
|---|---|
| Ownership map is accurate at head `902dc80a` | PROVEN (line anchors, §1) |
| Seam signatures compile (translator TU) | PROVEN by `tools/window_input_replay` build |
| W1–W4 replay against hand-authored goldens | PROVEN (harness run recorded in this directory) |
| W1–W4 replay against LIVE goldens | DEFERRED to Inc 2 (recording session) |
| Engine behavior unchanged (no engine edit) | PROVEN by construction (`git show --stat` engine/* empty) |
| Surface seam 31/31 | UNCHANGED (engine untouched; probe rerun optional, recorded status) |
| Runtime/visual parity | still NOT TESTED (unchanged from P05) |

---

## 12. Recorded discrepancy (found by the P06 ownership inspection)

**The right-drag pan arm is dead code.** `engine.cpp:191–200` (the first
`WM_MOUSEMOVE && g_mouse_captured` arm) ends in `return 0;` BEFORE
`engine.cpp:221–231` (the pan arm) can be reached — the two blocks share the
identical guard, so the pan arm is unreachable on every captured move. The
runtime therefore ORBITS for both buttons; the help text "Right-drag pan"
(main.cpp:2492) describes behavior the code cannot perform. Verified by direct
read of engine.cpp at head `902dc80a` (lines printed in the inspection
transcript). The translator reproduces the REACHABLE behavior and the W2
golden locks it; fixing the arm is a camera-semantics decision and is
explicitly OUT of P06's scope (no new camera semantics).