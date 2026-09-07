# BP-PAN — right-drag pan routing (the unreachable pan arm, spec-first)

**Commit context:** published as EVIDENCE on `astra/gait-capture`. The patch is
**not wired into the engine** and **no binaries were rebuilt**; it ships as a
spec (`this file`), the executable form of the patch
(`tools/window_input_replay/pan_routing_replay.cpp`), and its offline run
(`PAN_ROUTING_REPLAY_RUN.txt`). Source-of-record for the current behavior:
P06 spec `P06_WINDOW_INPUT_PATCH_SPEC.md` §12 (the dead-arm record) and the W2
golden `P06_GOLDEN_TRANSCRIPT_W2.txt`.

## 1. The defect being fixed (a documented, deliberate camera-semantics change)

GLM verified at head (`cececb23`, confirmed again at `4f0b4618`): `engine.cpp`
has **two sequential** `if (msg == WM_MOUSEMOVE && g_mouse_captured)` handlers —

- `engine.cpp:191–200` (the ORBITER) — applies theta/phi, `return 0;`
- `engine.cpp:221–231` (the PANNER) — applies pan_x/pan_y, `return 0;`

The first handler's guard is a **prefix** of the second's: any captured move
satisfies the second guard too, so the first handler returns and the pan arm
is **UNREACHABLE DEAD CODE**. At runtime, right-drag ORBITS (both buttons
orbit; the "Right-drag pan" help text in `main.cpp:2492` is unreachable).
P06 locked that degraded behavior as the W2 baseline. BP-PAN proposes the
minimal routing fix; the RBUTTONDOWN/RBUTTONUP click/drag split
(`ui.cpp:319–357`: travel under 4·ui_scale px = click → menu) is **preserved
unchanged** and is asserted by the fixtures.

## 2. The patch (unified diff vs. `ChimeraEngine/engine/engine.cpp` @ `cececb23`)

The complete change: **one file-scope state + two condition guards + four
set/clear statements**. The pan math, the orbit math, the capture call sites,
and the menu split are byte-for-byte untouched.

```diff
--- a/ChimeraEngine/engine/engine.cpp	(revision cececb23)
+++ b/ChimeraEngine/engine/engine.cpp	(BP-PAN proposal)
@@ -31,4 +31,5 @@ struct CameraState {
 static CameraState g_cam;
 static bool       g_mouse_captured = false;
 static int        g_last_mx = 0, g_last_my = 0;
+static int        g_drag_button = 0;   // 0=none, 1=L(moves orbit), 2=R(moves pan); DOWN sets, UP clears
 static bool       g_keys[256] = {};     // current frame key state
 
@@ -180,6 +181,7 @@
     if (msg == WM_LBUTTONDOWN) {
         SetCapture(hwnd);
         g_mouse_captured = true;
+        g_drag_button = 1;                       // L drag orbits (unchanged semantics)
         g_last_mx = (int)(short)LOWORD(lp);
         g_last_my = (int)(short)HIWORD(lp);
         return 0;
@@ -187,7 +189,8 @@
     if (msg == WM_LBUTTONUP) {
-        if (g_mouse_captured) { ReleaseCapture(); g_mouse_captured = false; }
+        if (g_mouse_captured) { ReleaseCapture(); g_mouse_captured = false; g_drag_button = 0; }
         return 0;
     }
-    if (msg == WM_MOUSEMOVE && g_mouse_captured) {
+    if (msg == WM_MOUSEMOVE && g_mouse_captured && g_drag_button == 1) {
         int mx = (int)(short)LOWORD(lp), my = (int)(short)HIWORD(lp);
         float dm = static_cast<float>(mx - g_last_mx);
         float  dm_y = static_cast<float>(my - g_last_my);
@@ -205,6 +208,9 @@
     if (msg == WM_RBUTTONDOWN) {
         if (g_key_engine && g_key_engine->ui_.visible)
             g_key_engine->ui_.on_rbutton_down((int)(short)LOWORD(lp), (int)(short)HIWORD(lp));
         SetCapture(hwnd);
         g_mouse_captured = true;
+        g_drag_button = 2;                       // R drag pans (was dead code)
         g_last_mx = (int)(short)LOWORD(lp);
         g_last_my = (int)(short)HIWORD(lp);
         return 0;
@@ -214,7 +213,8 @@
     if (msg == WM_RBUTTONUP) {
-        if (g_mouse_captured) { ReleaseCapture(); g_mouse_captured = false; }
+        if (g_mouse_captured) { ReleaseCapture(); g_mouse_captured = false; g_drag_button = 0; }
         if (g_key_engine && g_key_engine->ui_.visible &&
             g_key_engine->ui_.on_rbutton_up((int)(short)LOWORD(lp), (int)(short)HIWORD(lp)))
             return 0;   // the menu consumed the click
         return 0;
     }
-    if (msg == WM_MOUSEMOVE && g_mouse_captured) {
+    if (msg == WM_MOUSEMOVE && g_mouse_captured && g_drag_button == 2) {
         int mx = (int)(short)LOWORD(lp), my = (int)(short)HIWORD(lp);
         float dm = static_cast<float>(mx - g_last_mx);
         float  dm_y = static_cast<float>(my - g_last_my);
```

Effect on reachability: an L-captured move passes guard 1 (`== 1`) and
orbits; an R-captured move fails guard 1 (`== 2`), falls past both StudioUI
hooks (they are `WM_MOUSEMOVE`-universal but do not consume), reaches the
pan arm, passes guard 2 (`== 2`), and pans. `g_drag_button == 0` moves are
impossible while captured (every DOWN sets it, every UP clears it), so the
guards cannot strand a capture.

## 3. Why this shape is minimal (rules checked against)

- **No behavior change for left-drag.** Guard 1 is the same arm with the same
  math; the extra `== 1` only excludes cruft that could never reach it
  (an R-down sets `== 2`; WndProc's UI-consume paths return before capture).
- **Menu click/drag split untouched.** `StudioUI::on_rbutton_down/up` plus the
  travel accumulator (`ui.cpp:319–357`) are not modified; the UP arm's order is
  preserved (ReleaseCapture first, then the menu call). A quick R-click with
  zero intermediate moves applies NO deltas in either world, so "menu opens
  instead of panning on a genuine click" is invariant. Fixture PAN_P3.
- **StudioUI border-drag path untouched.** The border-drag `SetCapture` at
  `engine.cpp:171` never sets `g_mouse_captured`, so the captured-move guards
  never evaluate for it. No new interaction.
- **Pan math unchanged** (`0.02f` verbatim from `:226–227`); the only change is
  reachability. "New camera semantics" is thereby limited to *which button
  drives which tool* — the fix's entire point, and GLM-sanctioned.
- **The P06 translator (`window_input.cpp`) is NOT changed** in this commit. It
  still reproduces the W2 baseline. When this routing lands in the engine
  (Inc 3+), the translator's captured-MOVE arm gains the same button routing
  and the W2 golden's R-drag section is re-baselined in the same increment;
  this commit is the design + executable proof, published first (spec-first).

## 4. Rule 0 (Statement / Prediction / Falsifier) for the fixtures

- **P1 — L-drag orbits, pan untouched.** STATEMENT: with `g_drag_button == 1`,
  a captured move applies `theta -= dm*0.005f; phi -= dm_y*0.003f` and never
  touches pan_x/pan_y. PREDICTION: the L-golden replays to its theta/phi and
  pan_x/pan_y == 0 bit-for-bit. FALSIFIER: any pan delta in P1, or an orbit
  delta differing in any bit.
- **P2 — R-drag pans, orbit untouched.** STATEMENT: with `g_drag_button == 2`,
  a captured move reaches the pan arm and applies
  `pan_x -= dm*0.02f; pan_y += dm_y*0.02f` with theta/phi fixed. PREDICTION:
  the R-golden replays to its pan deltas and theta/phi == 0/0.3 exactly.
  FALSIFIER: any theta/phi delta in P2, or a pan delta differing in any bit.
- **P3 — quick R-click consumed by the menu, no pan.** STATEMENT: rdown+rup at
  the same client point with the UI visible and the menu consuming produces the
  menu call and no camera delta. PREDICTION: the release records
  `capture:off menu:open` and pan_x/pan_y/theta/phi stay at defaults.
  FALSIFIER: any camera delta, a missing capture:on, or a missing menu record.
- **P4 — drag-button state does not leak.** STATEMENT: every UP clears
  `g_drag_button`, every DOWN sets it per-button. PREDICTION: an L-drag then an
  R-drag in one transcript yields isolated deltas (orbit preserved after the R
  lane, pan zero after the L lane). FALSIFIER: cross-lane deltas on either side.

## 5. Verification (this commit)

`tools/window_input_replay/pan_routing_replay.cpp` compiles against the P06
types (`platform/window.h` + `window_input.h`) with a fake host — **the engine
is not involved, no binaries rebuilt**. `PAN_ROUTING_REPLAY_RUN.txt` records
`pan_routing_replay: ALL PASS` over PAN_P1..P4 (4+4+2+6 events; 9+9+8+13
expectations) AND a W1–W4 regression run after the harness CMake change (all
PASS; the current translator was not modified). The fixture file mirrors the
diff's two guards and four set/clear statements line-for-line, so a failing
fixture IS a failing patch design — discoverable before any engine edit.

## 6. Boundaries / deviations declared

- **Deviation (declared):** GLM suggested "e.g. `g_drag_button`"; this spec
  uses NONE/L/R as `0/1/2` (the diff's comment). Same intent.
- **Fixture scope** covers only the mouse routing the patch touches; the
  StudioUI panel-consume path (not changed by the patch) is exercised by the
  Windows smoke suite (P06 spec §8.1) instead.
- W2's recorded "right-drag ORBITS" expectation is **superseded by design** in
  this proposal (documented, not silently re-baselined).