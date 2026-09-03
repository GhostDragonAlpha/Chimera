# THE ENGINE STUDIO — the dashboard that brings the workflow into the engine

> Drafted 2026-08-29, operator request: game-engine features that fit our method,
> the pipeline map live in the window, Blender-style UI structure, video-editing
> features for the visual methodology, the whole documentation system accessible
> from the engine. This doc is the menu — pick what gets built and in what order.
>
> **The one idea:** the engine already owns all LIVE state (joints, gait, water,
> frost, volp, the show clock); the repo already owns all GATE truth (the pipeline,
> the master list, the membranes). The Studio is the JOIN of the two, drawn over
> the viewport. Nothing in it invents state — every panel reads the engine's own
> rows or the repo's own docs.

---

## A. The overlay shell

- **A1 — The overlay itself.** UI panels rendered over the 3D viewport inside the
  engine window (immediate-mode style, Vulkan-drawn, non-blocking — the Blender
  law: no modal dialogs ever). Toggle with a key (e.g. F1); the viewport stays live
  and orbitable underneath.
- **A2 — Dockable panels (Blender's area model).** Panels snap to the viewport
  edges, resize, collapse. Any panel can hold any editor type (Blender's "every
  area can be every editor").
- **A3 — Workspaces (Blender's tabs).** Named panel layouts: **MODEL, JOINTS,
  GAIT, WATER, FROST, CAPTURE, DOCS, BOARD.** One key cycles them.

## B. The pipeline board (the map of all steps + where we are)

- **B1 — The stage strip.** The B0–B10 pipeline as a strip of nodes across the
  top of the window, each colored by gate status (green / amber / red / blocked /
  pending). This is the agent-onboarding view: any agent (or you) reads the strip
  and knows exactly where the project stands in one glance.
- **B2 — The standing rule, displayed.** Under the strip, one line: "EARLIEST
  NON-GREEN GATE: **B5 anatomy referee** — the next stage." Computed, never edited.
- **B3 — Click a stage → its panel.** The stage's law (verbatim from the pipeline
  doc), its artifacts (with paths), its falsifier row with verdicts, its referee
  tool, and the next action. This is the Operating Manual's task envelope,
  rendered — the "bring an agent up to speed" feature.
- **B4 — The ledger browser.** The master list's H/B rows live from
  `docs/THE_MASTER_LIST.md` (read-only render, deep-linked from the strip).

## C. Blender-style editors for the visual work

- **C1 — JOINTS editor.** Per-joint θ sliders with the derived ROM as the hard
  range (from `factory_rom.json`); the joint's center/axis drawn as a gizmo on the
  mesh; the joint's band shown as a **weight-paint heat overlay** (Blender's
  weight-paint mode) so band quality is visible, not guessed.
- **C2 — Properties panel.** The selected thing's database row: a triangle's
  substrate row (latent, AO band, cube address, part), a joint's factory row
  (axis, ROM, the contact rod pair that earned the stop).
- **C3 — Modes (Blender's mode system).** OBJECT / POSE / WEIGHT / RENDER modes,
  each re-keying the mouse (Blender's Tab-mode law: one window, many tools).
- **C4 — Scene outliner.** The registered parts tree (body, eye layers, water,
  overlays) with visibility toggles — the control-triangle hiding problem's
  permanent home.

## D. Video-editing features (the capture methodology)

- **D1 — The timeline.** Playhead bound to the engine's gait/sweep clock; scrub
  time, the pose follows; frame-step keys (◀ ▶) that step θ in exact increments —
  the "every range in between, not just extremes" decree baked into the UI.
- **D2 — Markers.** Auto-markers on the timeline for each joint's sweep window
  (from the show clock), each gait footfall (from λ), each recorded dyad capture.
- **D3 — The reel.** Every `/frame` grab lands in a filmstrip with its metadata
  (timestamp, camera, joint, θ, light) — the project's visual evidence tray,
  on-screen instead of buried in `.tmp`.
- **D4 — A/B compare.** Split view (video-editor style): two reels or two modes
  side by side (blend vs volp at the same θ — the dyad's head-to-head, done in
  the window instead of scripts).
- **D5 — Render to MP4.** Sweep/march/orbit rendered to a movie with a named
  output row (the dyad movie protocol, button-driven).
- **D6 — Camera bookmarks.** Named camera states (face close-up, knee fold, full
  body) with jump-to keys; the E5 framing derivation saved, not re-hunted.

## E. Docs-in-engine

- **E1 — The docs browser.** `THE_BODY_PIPELINE.md`, `THE_ARTISTS_SOLID.md`,
  `THE_MASTER_LIST.md`, `THE_TRIANGLE_GUIDE.md`, the Operating Manual — rendered
  in a panel, read-only, current with git.
- **E2 — Deep links.** Click a falsifier on the board → the membrane section that
  named it. Click a stage → its pipeline spec. The documentation stops being a
  place you go to; it's a layer of the window.

## F. Game-engine-type features

- **F1 — Console.** A command line (Blender's console model) that issues engine
  commands/endpoints typed, with history — the HTTP API's interactive twin.
- **F2 — Status bar.** FPS + frame-time histogram live, GPU state, the
  current-stage line — always visible, overlay or no overlay.
- **F3 — HUD readouts.** During the show: current joint + θ + ROM range. During
  the walk: λ per foot. During water: ΣV conserved count. Small, honest, live.
- **F4 — Recorder.** Every gate-relevant state change (blob uploads, mode flips,
  gate verdicts) appended to an on-disk session log with timestamps — the
  "done-is-a-log" doctrine as a visible stream.

## G. The dyad's channels (how the eye reads the engine)

- **G1 — The glass channel.** `GET /glass` — the COMPOSITED window: viewport
  **plus** the overlay, the docks, the status bar, the HUD, the console and the
  reel. The twin of `/frame`, which is deliberately pixel-clean (it copies
  `rt_image_`; the Studio is drawn straight into the swapchain and never touches
  it). **Without G1 there is no capture in this repo that can see the
  instrument** — measured 2026-08-31: 49.8% of the glass was invisible to every
  capture path we had.
- **G2 — The dyad scan.** Sweeps through the glass, one image per vision call
  (the resident eye has a small context and cannot take a batch), N reads per
  shot, resume-safe, with the HTTP twins recorded beside every shot. The eye's
  report is the work list: **the dyad drives, the operator supervises.**

---

## Recommended build order (the spine first)

1. **A1 + A2** — the overlay + panels (everything else is content in panels).
2. **B1 + B2** — the stage strip + the standing-rule line (the map you asked for;
   it's read-only state, cheap to draw, instantly the onboarding view).
3. **D1 + D3** — the timeline + the reel (the video-editing core the visual
   methodology actually runs on).
4. **B3** — the stage panel (the agent-up-to-speed feature).
5. Then C1 (joints editor), E1 (docs browser), F2/F3 (status + HUD), and the rest
   by value.

**Why this order:** A and B make the workflow visible (the ask), D makes the
motion judgeable (the method), and everything after is refinement on a spine
that already answers "where are we and what's next" from inside the window.

**What it deliberately is NOT:** not a second app, not a web page, not a wiki.
It is the engine drawing its own state and the repo's own truth over the viewport
— Blender's non-blocking panels + the video editor's timeline, and nothing else.

---

## SHIPPED 2026-08-29 — the spine (A1 + A2 + B1 + B2)

- **A1 — the overlay.** Immediate-mode panels Vulkan-drawn into the swapchain
  pass, F1 (or `POST /studio {"on":bool}`) toggles; the viewport stays live and
  orbitable underneath. The presentation-layer law is enforced by architecture:
  the UI never touches `rt_image_`, so the dyad's `/frame` is pixel-identical
  with the overlay on or off (measured: md5 match, `engine/scratch/_studio_verify.log`).
- **A2 — docked panels.** Top stage strip + left STUDIO + right STATUS panels;
  click a title bar to collapse, drag an inner edge to resize, panel presses are
  consumed (never leak a camera orbit). Round-trip verified by injected clicks.
- **B1 — the stage strip.** B0–B10 nodes colored by gate status, live from
  `studio_board.json` (mtime-polled, 1 Hz). **B2 — the standing rule, displayed.**
- **The feed:** `python tools/studio_board.py` parses `docs/THE_BODY_PIPELINE.md`
  (the status-board section outranks per-cell prose) and writes the JSON next to
  the exe. The tool computes; the engine reads. Nothing in the overlay owns state.
- **Rule 0 verdicts:** /frame parity PASS · toggle health PASS · overlay cost
  inside ±0.05 ms noise at the 300 FPS cap (budget was 0.5 ms).
- **Files:** `engine/ui.{hpp,cpp}`, `engine/shaders/ui.{vert,frag}`, hooks in
  `engine/engine.{hpp,cpp}` + `engine/main.cpp`, `tools/studio_board.py`.
- **Next per the menu:** D1 timeline + D3 reel, then B3 stage panels.

## SHIPPED — A2 FOLLOW-UP: PERSISTED STUDIO WORKSPACE (2026-09-03)

- **Statement:** the editor's presentation state can be persisted in one
  engine-owned store and restored on relaunch without changing simulation state.
- **Prediction:** visibility, chrome, workspace, document selection/scroll,
  panel sizes, and collapse flags round-trip through `studio_state.txt`; malformed
  or non-finite values are ignored, valid panel sizes are clamped to the current
  window, and an invalid saved stage selection is cleared after the live board
  loads.
- **Falsifier:** reject the implementation if the saved file contains literal
  escape text instead of line records, `/studio` exposes invalid JSON, any HTTP
  or keyboard path bypasses the `StudioUI` state owner, or restored values can
  create out-of-bounds panel geometry.
- **Implementation:** versioned key/value records are loaded before the first
  frame and saved only after completed UI actions. The existing `/studio` readback
  includes the same JSON snapshot; F1 and `/studio_chrome` use the same setters
  as visible controls. Document scroll is clamped only after `prepare()` derives
  the current display range, so a valid restored position is not erased during
  startup.
- **Verification:** source checks cover valid newline/JSON literals,
  finite-value filtering, setter ownership, board-relative stage clamping, and
  deferred document-range clamping. The configured Debug build compiled and
  linked successfully; runtime relaunch verification remains open because the
  live Release process was not interrupted.

## SHIPPED — D1: THE TIMELINE (2026-08-29)

The show clock is a **parameter**, not a wall clock. The joints SHOW (H15) no
longer reads `steady_clock`; it reads `show_time_` — an engine-owned atomic the
TIMELINE panel issues intents against (play/pause, speed 0.25–4x, ±1/240 s
steps, direct scrub). The UI proposes; the engine's tick consumes, clamps,
advances. A bottom panel (118 px, drag-resizable like the rest) carries the
transport buttons, the scrub bar with per-joint marker ticks (current joint in
blue), the looping playhead, and the live readout `t / total | joint θ | state`.

- **Rule 0 verdicts** (evidence: `engine/scratch/_timeline_verify.{py,log}`,
  screenshots `_d1_rest_shot.png` / `_d1_flex_shot.png`):
  - **A — freeze:** paused at T=10.73, t and θ bit-identical across 60+ frames. PASS
  - **B — scrub = law:** θ at a scrubbed T matches the sweep law recomputed in
    Python to 0.000° (tolerance was ±0.5°). PASS at T=10.73, 10.734, 17.0
  - **C — step:** +1f advances t by exactly 1/240 s; θ follows the law. PASS
  - **D — markers:** scrub to T=17.0 switches the current joint to idx 4
    (spine_lower); the marker tick under the playhead turns blue. PASS
  - **speed:** measured dt/dwall = 2.000 at 2x. PASS · UI cost inside frame-time
    noise (ft avg 0.38 ms, budget 0.5 ms). PASS
  - **visual:** rest (T=16.0, θ=0) vs spine_lower full flex (T=17.5, θ=+152.51°):
    25405 pixels differ, torso fold unambiguous. PASS
- **Found while verifying (pre-existing, not D1's):** 10 of the 19 pack joints
  own zero skin verts (knees, ankles, wrists, elbows, jaw, tail_mid,
  shoulder_R) — the skeleton factory assigned by nearest rod and those rods had
  no skin near them. The clock still sweeps them; the mesh just can't show it.
  The ligament line owns the weights; flagged here so B5 doesn't re-discover it.
- **Load order note:** `load_joints` requires the hinge's rest state, so the
  driver POSTs a scaffold `/hinge_bin` (zero weights) before `/joints_bin`;
  the SHOW's dispatch supersedes the hinge the moment `/joints on` lands.
- **Endpoint:** `POST/GET /show` — `{playing, speed, time, step}` in;
  `{playing, time, speed, n_joints, period, total, current, theta, rom_ext,
  rom_flex, joints_loaded}` out. The dyad can now pose the body by name and
  number, exactly.
- **Next per the menu:** D3 reel (capture → filmstrip with metadata), then B3.

## SHIPPED — D3: THE REEL (2026-08-29)

A capture is only evidence if it is inspectable in the window where judgment
happens. Every `/frame` (or `/stream`) grab now lands in the REEL — a fifth
panel docked above the timeline — as a filmstrip tile with its metadata
composed AT GRAB TIME on the render thread: show t, joint, theta, camera
(r/theta/phi), light direction, wall timestamp. A ring of 12, newest first,
oldest evicted. The engine owns the ledger (`GET /reel`, newest-first JSON);
the UI owns the pixels. One RGBA atlas holds font cells (top) + the 4x3
thumbnail grid (bottom); one descriptor, one draw call, a per-vertex flag picks
font-coverage vs thumbnail-RGBA in the fragment shader.

- **Rule 0 verdicts** (evidence: `engine/scratch/_reel_verify.{py,log}`,
  `_d3_printwindow.png` — captured through PrintWindow because the operator's
  game owned the foreground; we do not fight the operator for their screen):
  - **A — /frame parity:** md5-identical with the reel live (studio on/off).
    The dyad channel stays pixel-clean. PASS
  - **B — metadata = grab-time truth:** reel theta == /show theta to 0.001 deg;
    joint, show_t, camera, light, wall stamp all equal the independent reads.
    PASS at two posed grabs (spine_upper T=10.73, spine_lower T=17.5)
  - **C — the ring:** count caps at 12, window = last 12 grabs, newest-first
    order verified by seq. PASS
  - **D — posed captures differ:** distinct md5s; tiles read as distinct poses
    in the on-screen strip. PASS
  - **cost:** reel on/off frame-time differential ~0.05 ms (budget 0.5 ms). PASS
- **Found while building (fixed same session):** the first atlas build smeared
  every glyph — font cells must be written at the atlas row stride, and the
  glyph UVs must be over the full atlas, not the font sub-rect. Rule 7 caught
  it in the first screenshot; the probe could not have.
- **Found while verifying (environmental, not D3's):** parity testing against a
  free-running show clock compares two different poses — pause before parity.
  The probe's own first bug, documented so the next agent doesn't re-pay for it.
- **Endpoint:** `GET /reel` -> `{count, cap, grabs_total, entries:[{seq, wall,
  show_t, joint, theta, cam, light}]}` newest first.
- **Next per the menu:** B3 stage panels (the agent-up-to-speed feature).

---

## SHIPPED — B3: THE STAGE PANELS (2026-08-29)

**Rule 0 — a panel that paraphrases is a panel that lies.**
- **Statement:** an agent (or the operator) can click any stage node on the
  strip and read that stage's complete Operating-Manual task envelope — LAW,
  FALSIFIER, VERDICT, REFEREE TOOL, ARTIFACT, NEXT ACTION — rendered as the
  pipeline doc's own words, and any word the panel invents or silently drops
  is a bug by definition.
- **Prediction:** every one of the 44 status cells (11 stages x 4 columns) and
  every envelope field the doc holds will round-trip verbatim into the board
  feed; clicking a node selects it, re-clicking closes it, and the selection
  is readable over HTTP so an agent can aim a click without eyes.
- **Falsifiers (named before the build):** (A) any doc cell or envelope field
  missing or altered in `studio_board.json`; (B) a click at a node's computed
  center not selecting that stage, or a re-click not closing the panel; (C) a
  screenshot that shows paraphrase, markup bleed (`**`), or silent truncation
  — the panel must say when it clips.

**What shipped.** `tools/studio_board.py` parses `docs/THE_BODY_PIPELINE.md`
into `studio_board.json`: 11 stages, each with its verbatim status cells plus
`law / falsifier / tool / artifact / spec_title / spec` (bold stripped;
the `### B7b` spec attaches to B7). The UI registers the strip nodes as hot
regions; a click selects (white outline), a re-click deselects, and the left
dock renders the envelope via `text_wrap` — or the workspace menu when nothing
is selected. New endpoints: `POST /ui_click {x,y}` (queued onto the render
thread, consumed before `ui_.prepare` in both frame paths) and `GET /studio`
-> `{on, selected, w, h}` so an agent can compute node centers from the live
extent and aim its own clicks.

- **Rule 0 verdicts** (evidence: `engine/scratch/_stage_verify.py`,
  `_b3_stage_shot2.png`, `_b3_stage_shot3.png` — PrintWindow again, the
  operator's game still owns the foreground):
  - **A — verbatim feed:** 11 stages; all 44 cells found verbatim in the doc;
    envelopes on B5/B6/B7/B8; B5 spec 846 chars verbatim. PASS
  - **B — click round-trip:** clicks at computed centers select B5, B0, B10;
    re-click closes; `GET /studio.selected` agrees every time. PASS
  - **C — the visual read:** VERDICT renders `NEXT` with no markup bleed;
    overflow ends in `... (clipped - widen this dock or collapse the reel to
    read on)` and NOT one line more. PASS
- **Found while verifying (fixed same session):** two honest-lie bugs the
  first screenshot caught — the `cell` field kept the doc's `**` bold markers
  (the feed stripped them everywhere else), and the clip indicator was drawn
  while `text_wrap` kept drawing past it — an indicator that says "clipped"
  over unclipped text is a lie. `text_wrap` now takes `y_max`: lines past the
  dock floor are never drawn, but the walk continues so the return value
  still reports where the text WOULD have ended. Rule 7 (read the screenshot)
  earned its keep twice more.
- **Layout note:** the docks yield height to the reel+timeline stack, so the
  indicator's advice is literal — collapse the reel and the dock grows by the
  reel's height; widen the dock and the wrap shortens.
- **Files:** `tools/studio_board.py`, `ChimeraEngine/engine/ui.{hpp,cpp}`,
  `engine.{hpp,cpp}`, `main.cpp`, this doc.
- **Next per the menu:** C1 joints editor (theta sliders + gizmo + weight-paint
  heat overlay), then E1 docs browser, F2/F3.

---

## SHIPPED — C1: THE JOINTS EDITOR (2026-08-29)

**Rule 0 — the editor poses any joint to any theta inside its derived ROM,
from the window or from HTTP, and every number and pixel it shows is the
engine's own state.**
- **Statement:** with the pack live, an agent or the operator can set a joint's
  theta (slider or endpoint), see the joint's center + axis on the mesh as a
  gizmo, and see the joint's band as Blender-style weight-paint — and posing a
  joint moves exactly that joint's band.
- **Prediction:** set theta == reported theta; two thetas give two frames;
  clamps land exactly on the pack ROM; the pose owner (show clock vs editor)
  is single and observable; the gizmo's projection channel matches an
  independent Python projection; paint changes exactly the band's colors and
  unpaints bit-exact.
- **Falsifiers (named before the build):** (A) theta mismatch > 0.5 deg or
  shared frame md5 across thetas; (B) clamp overshoot > 0.01 deg; (C) an edit
  drifting while owner==edit, or play not returning the pose to the show;
  (D) projection error > 1 px; (E) paint on/off not md5-round-tripping, or
  paint showing nothing; (F) a synthetic slider click off the linear map by
  > 1 deg; (G) editor cost > 0.5 ms over the show.

**What shipped.** One pose owner, observable: `joints_owner_` (0 show, 1
edit) — a theta intent claims the pose, pressing play hands it back, and the
joints kernel dispatches whenever EITHER owns it (in EDIT thetas persist
where intents put them, clamped to the derived ROM). The JOINTS workspace
(A3) is live: the left dock lists all 19 joints with the pack's derived ROM
as each slider's hard range, the zero line, and the live theta thumb; click a
name for gizmo + weight-paint (again to clear). The gizmo is the joint's J
and J + axis * L, where L is DERIVED — the band's RMS radius about J from the
pack's own geometry. Weight-paint folds into joints.comp as a push constant:
the band colored by the standard heat ramp on the factory's w, everything
else dimmed to a quarter — the mesh's own vertex colors, not chrome, off by
default. New endpoints: `POST /joint` ({"joint","theta"} intent with
post-clamp ack; {"select"} aims the gizmo+paint), `POST /project` (the
gizmo's math channel + the camera state), `GET /joints` extended to the full
editor document (owner, selected, per-joint name/ROM/theta/J/axis), and
`GET /studio` extended with left_mode + the font metrics so agents can aim
slider clicks.

- **Rule 0 verdicts** (evidence: `engine/scratch/_joints_verify.{py,log}`,
  `_c1_editor_shot.png` — PrintWindow; the operator's game owned the screen):
  - **A:** theta 60.000 reported/acked; md5s distinct at 60/0/-20, repeat-60
    identical. PASS
  - **B:** +999 -> 152.510 (flex), -999 -> -117.870 (ext), exact. PASS
  - **C:** edit frozen 30.000 over 2.2 s; play -> owner show, current joint
    drifted 131.5 deg; re-edit -> frozen. PASS
  - **D:** worst projection error 0.000 px over 3 points (incl. the neck's J).
    PASS
  - **E:** paint on != off (4.74% of pixels repainted), paint off restores the
    pre-paint md5 exactly. PASS
  - **F:** click x=198 -> theta 85.955, want 85.955. PASS
  - **G:** show 0.327 ms -> editor 0.353 ms (delta +0.027, budget 0.5). PASS
  - **B3 regression:** `_stage_verify.py` re-run — ALL PASS.
- **Found while verifying (fixed same session):** the projection had a double
  Y-flip — NDC is already Y-down after perspective()'s Vulkan row negation,
  and project_world flipped again. The D gate PASSED the wrong math because
  the Python replica carried the same flip; framing the screenshot caught it
  (the neck, anatomically +Y, projected below the window while the teddy
  stands upright). Rule 7 (read the screenshot) caught what self-consistency
  could not — the gate now verifies the CORRECT math (world-up = screen-up).
- **Found while verifying (the probe's own bugs, documented so the next agent
  doesn't re-pay):** clicks are integer pixels — aiming at a fractional x and
  expecting the fraction's value fails by floor(x) (measured: x_eff ==
  floor(sent x) exactly); and slice a growing log as BYTES then decode —
  slicing decoded text at a byte offset lands past the end.
- **Build note:** joints.spv is NOT in CMake's hardcoded shader list —
  recompile by hand after editing joints.comp:
  `glslangValidator -S comp -V shaders/joints.comp -o build/Release/shaders/joints.spv`
- **Files:** `engine/engine.{hpp,cpp}`, `engine/main.cpp`, `engine/ui.{hpp,cpp}`,
  `engine/shaders/joints.comp`, this doc.
- **Next per the menu:** E1 docs browser, then F2/F3 (status bar + HUD).

## SHIPPED — D8: THE AUTHORED FK RIG OVERLAY (2026-09-02)

**Statement:** the JOINTS workspace can show the loaded creature's authored FK
links as a toggleable viewport instrument, without inventing parent links from
spatial proximity or altering the triangle mesh.

**Prediction:** the known 19-joint monkey pack produces exactly 18 projected FK
segments; turning the overlay off changes only central-viewport overlay pixels,
and turning it back on restores the same segment count and visible chain.

**Falsifier:** reject the feature if the loaded pack cannot produce the 18
explicit links, if the toggle does not round-trip, if overlay pixels bleed into
the reel/timeline chrome, or if an endpoint is not coincident with its source
joint projection under the engine's camera law.

**What shipped.** The native FK topology is represented by an explicit name map:
neck → jaw/spine, spine → tail/shoulders/hips, and limb chains through wrists and
ankles. The JNT1 payload has centers, axes, ROM, weights, and names but no parent
array, so unknown links are omitted rather than guessed. `push_rig_overlay()`
projects the live joint centers through the engine camera; the Studio draws the
segments and endpoint markers in cyan/amber screen space. JOINTS exposes a
`[RIG ON/OFF] FK chain overlay` control, `POST/GET /rig` reports and toggles it,
and `POST /studio {"mode":"joints"}` selects the workspace deterministically.
All screen-space instruments are clipped to the central viewport rectangle.

- **Verification:** 19 joints → **18 authored FK segments**; toggle
  `true → false → true`; the on/off capture changed 7,388 central-viewport
  pixels; the final glass showed the chain without chrome bleed. Independent
  pixel probes confirmed the tail edge and both ankle edges were present, so
  the dyad's conflicting visual claims were not used to corrupt valid rig data.
- **Files:** `engine/engine.{hpp,cpp}`, `engine/main.cpp`, `engine/ui.{hpp,cpp}`,
  this doc.
- **Next per the menu:** E1 docs browser, then F2/F3 (status bar + HUD).

## SHIPPED — D9: ACTIONABLE DOPE SHEET KEYS (2026-09-02)

**Statement:** every visible Dope Sheet key diamond is an authoring control,
not merely a marker: clicking it recalls the saved clock time and selects the
joint stored on that key.

**Prediction:** a keyed diamond click will queue its exact persisted `t` and
select its persisted joint; an unkeyed key will clear joint selection. Existing
master-timeline diamonds and scene-inspector hits will remain independent.

**Falsifier:** reject the feature if a Dope Sheet key has no distinct hit region,
if its selected joint is not the saved joint, if recalled time differs from the
saved time by more than `1e-6`, or if the master timeline/key behavior regresses.

**What shipped.** Dope Sheet diamonds now use the dedicated `1000+i` hot-ID
range, avoiding the existing `700+i` scene-inspector/master-key collision. The
engine's `cb_dope_key_recall_` resolves the key through `key_marks_list_info()`,
selects the saved joint by name, and queues the exact saved time through the
same render-thread clock scrub path. Keys without joint metadata remain honest:
they scrub time and leave selection unset rather than claiming anatomy.

- **Build:** Debug configuration compiled and linked successfully. Release
  source compilation passed; final linking was blocked only because the live
  Release executable held its output file open, so the running operator session
  was not interrupted.
- **Files:** `engine/engine.cpp`, `engine/ui.cpp`, `engine/ui.hpp`, this doc.
- **Next per the menu:** E1 docs browser, then F2/F3 (status bar + HUD).

## SHIPPED — D2: DERIVED TIMELINE EVENT MARKERS (2026-09-02)

**Statement:** the timeline can display event markers derived from the engine's
live state without becoming a second clock or marker authority.

**Prediction:** a 19-joint show produces 38 sweep-boundary markers—one start and
one end for each `j_sweep_period_` window—and each recorded reel entry produces
one capture marker. Marker positions use the same loop normalization as the
playhead and key diamonds.

**Falsifier:** reject the feature if marker count differs from `2 × joint count +
reel count`, if a marker's normalized position is more than one pixel from its
source time, if markers appear without their source state, or if scrub/key
behavior regresses.

**What shipped.** `Engine::push_timeline_markers()` derives start/end markers
from the loaded joint count and sweep period, then appends capture markers from
the thread-safe reel ledger. The UI receives the read-only marker feed and draws
compact ticks on both hinge and joints timelines: blue starts, amber ends, and
green capture events. The normal and idle frame paths both refresh the feed, so
hidden or mesh-idle Studio operation cannot freeze the timeline's event view.
The marker labels are retained in the engine-fed data and are inspectable by
hovering the marker lane; this remains read-only and does not invent a second
interaction surface.

- **Verification:** Debug configuration compiled and linked successfully;
  structural falsifiers passed for two frame-path feeds, two boundaries per
  joint, capture-source consumption under the reel mutex, and distinct marker
  kinds/colors. `git diff --check` passed.
- **Files:** `engine/engine.{hpp,cpp}`, `engine/ui.{hpp,cpp}`, this doc.
- **Next per the menu:** E1 docs browser, then F2/F3 (status bar + HUD).

## SHIPPED — D2 FOLLOW-UP: MARKER HOVER INSPECTION (2026-09-02)

**Statement:** when the pointer rests on a derived timeline marker, the Studio
can identify that marker from the engine-fed label, kind, and source time without
changing the clock, pose, or marker feed.

**Prediction:** a pointer inside the scrub lane and within half the marker-lane
height of a visible marker produces a bounded readout containing its kind, exact
source time, and label; moving away, hiding the overlay, or collapsing the
transport clears the readout. Playback, scrubbing, and key-diamond clicks remain
unchanged.

**Falsifier:** reject the change if a tooltip appears without a nearby marker, if
its kind/label/time differs from the selected engine marker, if it changes
transport state, if it survives pointer departure or overlay hiding, or if the
readout can extend outside the window.

**What shipped.** `StudioUI::on_mouse_move()` retains the render-thread pointer;
`prepare()` resolves the nearest marker using the same loop-normalized x law as
the marker renderer. The tolerance is derived from the active scrub-bar height,
the tooltip is clamped to the window, and hidden-state cleanup clears stale
hover. The UI reads `timeline_markers_`; it owns no marker or clock state and
issues no transport callback.

- **Verification:** Debug configuration compiled and linked successfully;
  source falsifiers passed for pointer tracking, hidden-state clearing, exactly
  one current-frame hover resolution, marker metadata rendering, no transport
  callback from the hover path, and intact console compilation. `git diff --check`
  passed. Runtime glass verification remains intentionally open because the
  operator's Release executable was left running and was not interrupted.
- **Files:** `engine/ui.{hpp,cpp}`, this doc.

---

## SHIPPED — D4: A/B CAPTURE COMPARE (2026-09-02)

**Statement:** the Studio can compare two already-captured reel images side by
side while preserving each tile's grab-time metadata; comparison is a view of
evidence, not a second renderer or simulation.

**Prediction:** selecting two reel tiles will show those exact captures as A and
B in the central viewport, with distinct sequence labels and independent
metadata. Selecting a third tile starts a new A selection; clearing compare
returns to the normal viewport and reel without changing `/show`, `/frame`, the
camera, or the reel ledger.

**Falsifier:** reject the feature if fewer than two valid reel selections can
enter compare, either image is not the selected atlas tile, metadata is mixed
between captures, selection mutates engine state, an overwritten ring slot
remains selectable, or the normal reel layout regresses.

**What shipped.** Reel tiles use dedicated `1100 + slot` hit regions and the
header exposes a clear control while A/B is active. The render-thread view state
selects A, then B, and a third selection starts a new pair. The compare pane
reads the existing reel atlas and each tile's stored sequence/caption data,
draws the two captures side by side in the central viewport, and deliberately
issues no engine callback. A ring-slot overwrite clears any selection that
would otherwise point at newly written pixels.

- **Verification:** Debug configuration compiled and linked successfully;
  source falsifiers passed for dedicated hit IDs, A/B/third-selection behavior,
  clear behavior, ring overwrite invalidation, view-only rendering, and
  independent A/B captions. `git diff --check` passed. Runtime glass verification
  remains intentionally open because the operator's Release executable was left
  running and was not interrupted.
- **Files:** `engine/ui.{hpp,cpp}`, this doc.

---

## SHIPPED — D4a: A/B COMPARE HTTP TWIN (2026-09-02)

**Statement:** the A/B comparison can be controlled and inspected through the
same render-thread membrane as the Studio UI, so HTTP automation and visible
clicks cannot diverge.

**Prediction:** `GET /compare` reports the selected A/B reel sequence IDs;
`POST /compare {"slot":n}` applies the same A → B → new-A selection law, and
`POST /compare {"op":"clear"}` clears it. Invalid or evicted slots do not enter
compare, and no simulation state changes.

**Falsifier:** reject the feature if HTTP and glass use different selection
rules, an invalid slot is accepted, reported state differs from the selected tile
sequence, requests mutate `/show` or camera state, or the endpoint acts outside
the render-thread queue.

**What shipped.** `Engine::queue_ui_compare()` carries HTTP intent through
atomics; both normal and idle frame paths consume that request before
`StudioUI::prepare()`. The UI applies the same `compare_select()` and
`compare_clear()` functions used by visible reel hit regions. `GET /compare`
returns committed `a_slot`, `b_slot`, `a_seq`, and `b_seq`; POST returns
`queued:true` because the render thread has not necessarily consumed the request
at response time.

- **Verification:** Debug configuration compiled and linked successfully;
  source falsifiers passed for the queue API, exactly two render-path consumers,
  shared UI selection law, committed GET readback, explicit clear operation, and
  absence of direct engine mutation from the endpoint. `git diff --check` passed.
  Runtime glass/API verification remains intentionally open because the
  operator's Release executable was left running and was not interrupted.
- **Files:** `engine/engine.{hpp,cpp}`, `engine/main.cpp`, `engine/ui.hpp`, this doc.

---

## SHIPPED — E1: THE DOCS BROWSER (2026-08-29)

- **Statement:** the DOCS workspace renders the repo's own workflow docs
  VERBATIM — the panel's bytes ARE the file's bytes (provable over HTTP by an
  FNV-1a/64 hash), live with git (a save re-reads within the poll), and
  scrollable under both the wheel and an agent's exact POST.
- **Prediction (unmeasured at naming time):** the served hash matches the
  file's hash for all five docs; appending one line to a doc moves the served
  hash within 5 s and restoring the file restores the hash; a POSTed scroll
  lands to the hundredth; the scrollbar's track click pages by exactly
  track_height / cell_h lines.
- **Falsifiers (named before the build):** (A) any of the five docs' served
  FNV or line count differing from the file's; (B) an appended marker not
  live in the served hash within 5 s, or the restore not byte-exact (md5);
  (C) a POSTed scroll not landing exact, the clamp not landing on
  scroll_max, or the track page off the 21.25-line law; (G) the DOCS dock
  costing > 0.5 ms a frame over the BOARD dock.

**What shipped.** The DOCS workspace (A3 row 8) is the left dock's mode 2:
a picker of the five docs the menu names (THE_BODY_PIPELINE,
THE_ARTISTS_SOLID, THE_MASTER_LIST, THE_TRIANGLE_GUIDE,
THE_OPERATING_MANUAL), the doc re-wrapped to the dock's live width by the
same greedy law as text_wrap (the browser and the renderer can never
disagree about a line break), a scrollbar whose thumb drag and track page
use the panel's own geometry, and wheel routing in the WndProc (over the
dock -> the doc; elsewhere -> the camera zoom). Read-only by architecture:
the panel READS the repo (1 Hz mtime poll, the board's discipline) and
never writes it. New endpoints: `GET /studio_doc` (doc, path, mtime, the
verbatim-proof FNV, line counts, scroll and scroll_max) and
`POST /studio_doc` ({"doc": i} picks; {"scroll": N} lands an exact scroll,
clamped by the panel's own geometry). `StudioUI::idle_poll()` keeps both
HTTP twins (board + docs) live on the hidden-and-idle path.

- **Rule 0 verdicts** (evidence: `engine/scratch/_docs_verify.{py,log}`,
  `e1_docs_dock.png` — PrintWindow; the operator's game owned the screen):
  - **A:** all five docs — served FNV == file FNV, served line count ==
    file line count (121 / 914 / 1076 / 182 / 139). PASS
  - **B:** marker live in the served hash after 0.75 s; restore live after
    1.00 s; file md5 byte-exact after the gate. PASS
  - **C:** scroll 100.000 landed exact; 999999 clamped to scroll_max
    4822.00; the track click paged 0.00 -> 21.25 (the law: 21.25). PASS
  - **G:** board 8.930 ms -> docs 8.983 ms (delta +0.053, budget 0.5). PASS
  - **Idempotence:** the probe run twice back-to-back — ALL PASS both times.
  - **B3 regression:** `_stage_verify.py` re-run — ALL PASS.
- **Found while verifying (fixed same session):** `Engine::frame()`'s
  hidden-and-idle early return (`n_==0 && !has_mesh_`, overlay closed)
  returned BEFORE `ui_.prepare()` — so the 1 Hz polls never ran and both
  HTTP twins served a frozen empty state the moment the operator hid the
  overlay. The B3 board had the same latent freeze; E1's design ("the twin
  stays live in any dock mode") exposed it. Fix: `idle_poll()` runs the
  board + docs polls on that path.
- **Found while verifying (the probe's own bugs, documented so the next
  agent doesn't re-pay):** the workspace row TOGGLES — a probe that
  blindly clicks its setup row undoes itself on re-run (click only when
  not already in the mode); the menu rows exist ONLY in mode 0 with no
  stage selected (a selected stage shows its envelope instead — close it
  before aiming at a menu row); and from a workspace the way back to the
  menu is a STRIP NODE click, not a dock click — gate G's first draft
  "measured" board-vs-docs by clicking picker rows both times.
- **Known nit (not a falsifier):** the dock's footer line ("... N more
  lines") is drawn unwrapped and can overrun the dock's right edge by a few
  pixels; every content line wraps to the dock width.
- **Files:** `engine/engine.cpp` (idle_poll on the hidden-idle path, wheel
  routing), `engine/ui.{hpp,cpp}` (DocsState, poll/wrap/scroll, picker,
  scrollbar), `engine/main.cpp` (GET/POST /studio_doc), this doc.
- **Next per the menu:** F2/F3 (status bar + HUD).

## SHIPPED — F2/F3: THE CHROME (status bar + HUD) (2026-08-29)

- **Statement:** the engine wears its own vital signs. A status bar — FPS,
  a live 120-frame frame-time histogram, the GPU's own name, the board's
  standing line — is drawn on EVERY presented frame whether the overlay is
  open or closed, and a HUD shows the live context rows (show: joint +
  theta + ROM; gait: the Owaki lam surrogate per foot; water: the clock's
  bookkeeping), each row present only while its mode is live. Every number
  is the engine's own state, and /studio_chrome serves the SAME strings the
  glass draws — one formatting site, no drift possible.
- **Prediction (unmeasured at naming time):** with the overlay closed, the
  twin still advances (frame pushes increase over 1.5 s); the ring holds
  exactly 120 frame times with its max inside the engine log's own band;
  the stage line equals studio_board.json's standing verbatim and the GPU
  name matches WMI; the SHOW row's paused theta equals /joints within
  0.05 deg and its ROM equals the pack's; the gait row's lam equals
  max(0,-(th-THM)/THA) of the row's own thetas to 1e-9; the water steps
  strictly increase; the bar costs < 0.5 ms.
- **Falsifiers (named before the build):** (A) any chrome field stale with
  the overlay closed, or a switchable row visible while its mode is off;
  (B) ring discipline broken (n != 120, insane values, max outside the
  log's band); (C) stage/GPU disagreeing with the independent reads;
  (D) SHOW row missing, theta frozen while playing, paused theta off >
  0.05 deg, or ROM strings != the pack; (E) lam off the derivation by >
  1e-9, outside [0,1], or surviving /gait off; (F) water steps not
  advancing, or the row surviving the clock off; (G) bar cost > 0.5 ms.

**What shipped.** `layout()` yields the bottom 24 px to the bar (every
panel shrinks honestly; the bar never covers content). The bar: standing
line left, FPS + the frame-time histogram center (green < 16.7 ms, yellow
< 33.3, red above, the 60 fps budget line drawn across), GPU name +
swapchain extent right. The HUD rows draw as dark chips at the viewport's
top-left (right of the left dock when the overlay is open). The render
gating now keys on `wants_chrome()` — hidden+idle still presents the
clear + chrome frame. The gait row's lam is the shader's OWN Owaki load
term s = max(0,-sin phi), derived host-side by inverting the G1 map on
the same theta mirror the hinge pose reads (the G1 consts are kept from
load_gait) — no new GPU channel. New twin: `GET /studio_chrome` (bar
state, fps/ft, the full-precision ring + gait thetas — %.17g where a
derivation feeds on them), `POST /studio_chrome {"on":...}` (the bar's
kill switch — default ON; the toggle exists so the cost is measurable and
the operator has an out). main pushes every frame's time into the ring.

- **Rule 0 verdicts** (evidence: `engine/scratch/_chrome_verify.{py,log}`,
  `f23_chrome_{hidden,open}.png` — PrintWindow; the operator's game owned
  the screen):
  - **A:** pushes 299 -> 385 in 1.5 s with the overlay CLOSED; no phantom
    gait/water rows. PASS
  - **B:** ring 120/120, values in (8.5, 10.1] ms, max 10.036 inside the
    log's [8.990, 10.090]. PASS
  - **C:** stage == the board's standing verbatim; Vulkan "NVIDIA GeForce
    RTX 4090" == WMI's adapter. PASS
  - **D:** SHOW row present; ROM (-169.7, 119.2) == the pack's; theta
    moved 97.87 -> 76.99 while playing; paused, the row's 69.71 ==
    /joints' 69.706. PASS
  - **E:** lamL/lamR == the derivation to 1e-9; in [0,1]; the row's string
    == the formatting of its own served values; the row dies with /gait
    off. PASS
  - **F:** water steps 714 -> 1432; the row dies with the clock off. PASS
  - **G:** no bar 0.367 ms -> bar 0.337 ms (delta -0.030, budget 0.5). PASS
  - **E1/B3 regressions:** `_docs_verify.py` (updated to read bar_h from
    the chrome twin — the docks honestly yield 24 px, so the track-page
    law is now 20.25 lines) and `_stage_verify.py` — ALL PASS both.
- **Found while verifying (fixed same session):** the twin's gait thetas
  went out as std::to_string's 6 decimals — the probe's lam check failed
  at 1e-8 against the engine's full-double lam. The displayed values
  matched to 6 places; only the derivation caught the rounding. The twin
  now serves %.17g wherever a derivation feeds on a number.
- **Named boundaries (honest deviations from the menu text):** water
  Sigma-V is NOT mirrored live — the clock deliberately avoids readbacks,
  so Sigma-V stays on the batch verification path (/water_step); the row
  carries the clock's bookkeeping. Gait lam is the Owaki SURROGATE (the
  row says so on its face) — G3 real contact load is still blocked
  upstream (gait.comp line 3).
- **Files:** `engine/engine.{hpp,cpp}`, `engine/main.cpp`,
  `engine/ui.{hpp,cpp}`, this doc.
- **Next per the menu:** E2 deep links, F1 console, F4 recorder — and the
  rest by value.

## SHIPPED — F1: THE CONSOLE (2026-08-29)

- **Statement:** the console is the HTTP API's interactive twin. A request
  line `METHOD /path [json]` — typed at the window or posted to /console —
  enters ONE path (history + scrollback + the engine's worker queue) and
  executes through the SAME handler the HTTP server runs; the scrollback
  holds the command and the handler's verbatim response. While open, the
  console captures the ENTIRE keyboard — nothing leaks to the camera, the
  pose key, or the overlay toggle.
- **Prediction (unmeasured at naming time):** a console GET /studio's
  fields equal curl's; a console POST /show flips the served playing state
  within 1 s; a /joint intent acks through the scrollback in < 10 s with
  no deadlock; VK_UP recalls the last command verbatim and VK_DOWN clears;
  F1 with the console open does NOT toggle the overlay while the control
  (console closed) does; the open console costs < 0.5 ms.
- **Falsifiers (named before the build):** (A) console GET != curl GET;
  (B) show state not following a console POST; (C) /joint ack missing or
  > 10 s; (D) keystrokes not landing (type/Enter/recall); (E) F1 leaking
  while open, or the control F1 not toggling (which would mean the test's
  keystrokes never landed); (G) console cost > 0.5 ms.

**What shipped.** Backtick (or ESC) toggles the console — overlay open or
closed (it is chrome: `wants_chrome()` includes it). Input is WM_CHAR-
routed so shifted JSON punctuation types exactly; Enter submits; UP/DOWN
recall history. The UI collects and ISSUES; the engine owns execution:
`cb_console_` queues the line to a worker thread that parses
`METHOD /path [json]` and invokes the SAME `Engine::ApiFn` main wires to
the HTTP server — waiting endpoints (/mesh_bin and kin) behave exactly as
over HTTP because the worker is not the render thread. Responses drain to
the scrollback once per frame (both frame paths). While open, the pose
key, the F1 overlay toggle, and the camera poll (`update_camera_input`)
are all gated — the keyboard is the console's. The twin: `GET /console`
(open, input, history count, the last 50 scrollback entries, escaped) and
`POST /console` ({"line": ...} enters the same path as a typed Enter;
{"open": bool} sets visibility absolutely). `get_string` learned to
unescape — posted lines carry escaped JSON.

- **Rule 0 verdicts** (evidence: `engine/scratch/_console_verify.{py,log}`,
  `f1_console.png` — PrintWindow; keystrokes via `_postmsg.ps1`
  PostMessageW, so the operator's fullscreen game was never disturbed):
  - **A:** console GET /studio's on/selected/left_mode/w/h == curl's. PASS
  - **B:** POST /show false -> playing False; true -> True, each < 1 s. PASS
  - **C:** POST /joint knee_L 30 -> `{"ok":true,"owner":"edit",...,
    "theta_applied":30.000000}` in 0.00 s. PASS
  - **D:** real keystrokes — "GET /debug" typed char-by-char landed
    verbatim; Enter submitted (hist 9 -> 10, response in the scrollback);
    VK_UP recalled it verbatim; VK_DOWN cleared. PASS
  - **E:** F1 with the console open moved nothing (False -> False); the
    control F1 with it closed toggled (False -> True) — the keystrokes
    provably land, the capture provably holds. PASS
  - **G:** closed 0.333 ms -> open 0.360 ms (delta +0.027, budget 0.5). PASS
  - **B3/F2 regressions:** `_stage_verify.py` and `_chrome_verify.py` —
    ALL PASS both.
- **Found while verifying (the probe's own bug, documented):** the /joint
  ack's field is `theta_applied`, not `theta` — the probe's first draft
  failed a PASSING engine. Read the response before asserting its shape.
- **Files:** `engine/engine.{hpp,cpp}`, `engine/main.cpp`,
  `engine/ui.{hpp,cpp}`, this doc.
- **Next per the menu:** E2 deep links, F4 recorder — and the rest by value.

## SHIPPED — F1a: RENDER-THREAD CONSOLE CONTROL (2026-09-03)

- **Statement:** console visibility and posted console lines are presentation
  actions owned by the render thread, regardless of whether they originate from
  keyboard input or HTTP.
- **Prediction:** `POST /console {"open":bool}` and `POST /console {"line":...}`
  are consumed in both normal and idle frame paths; the command enters the same
  history/worker path as a typed Enter, while the response reports only after
  the requested console state has been applied.
- **Falsifier:** reject the change if the HTTP handler directly writes
  `console_open_`, `console_input_`, `console_history_`, or `console_log_`; if
  either render path fails to consume the request; or if a timeout reports a
  committed UI result.
- **Implementation:** `Engine::request_console_ui()` serializes HTTP callers,
  queues the optional open/line operation, and waits for render-thread
  acknowledgment. The render thread applies `set_console_open()` and
  `console_submit_line()` through the existing console worker path. Shutdown
  wakes blocked callers; a stalled request returns `ok:false` and does not read
  mutable UI state from the HTTP thread. Console visibility is also persisted by
  the A2 workspace store.
- **Verification boundary:** source falsifiers passed for one declaration and
  definition, two frame-path consumers, render-thread-only UI mutation, no direct
  HTTP console writes, atomic pending state, and shutdown wakeup. Debug compiled
  and linked successfully; runtime API probing remains open because the live
  Release process was not interrupted.

## SHIPPED — F4: THE RECORDER (2026-08-30)

- **Statement:** every gate-relevant state change through the api chokepoint
  (blob uploads, mode flips, intents) plus externally-posted gate verdicts
  lands as a timestamped JSON line in a per-session on-disk file AND in the
  LOG dock's stream — the same lines, in the same order, at the moment it
  happens. The log records OUTCOMES: a line claiming success for a failed
  event is a lie. Named boundaries: panel-only gestures (dock switches) are
  not events; the stream is a tail view — the file holds everything.
- **Prediction (unmeasured at naming time):** a covered endpoint's success
  is followed within 1 s by a parsing file line carrying its outcome; the
  served stream's tail equals the file's tail; a 50-event burst shows no
  seq gap or reorder in either; a posted verdict lands verbatim (escapes,
  Unicode and all); the burst costs < 0.5 ms of frame time.
- **Falsifiers (named before the build):** (A) a covered endpoint succeeding
  without a parsing file line within 1 s; (B) stream tail != file tail;
  (C) a seq gap or reorder in the burst; (D) a posted verdict not verbatim;
  (E) burst cost > 0.5 ms.

**What shipped.** `Engine::log_event(kind, detail)` — one mutex, one
monotonic seq, a millisecond wall timestamp, JSON-escaped, `fprintf` +
`fflush` to `session_YYYYmmdd_HHMMSS.jsonl` (opened FIRST in `Engine::init`,
before any covered state change can exist; closed in shutdown after the
console worker joins) and a push to the UI ring (200-line tail). The
chokepoint in `main.cpp` logs at the END of the api chain, POSTs only, with
the RESPONSE BODY as the detail — the endpoint's own answer is the outcome
(/joint also appends `joint=<name>` from the request, because the response
omits which joint moved). Kinds: upload (the five `_bin` blobs), mode
(/show /joints /gait /water_clock /studio /studio_chrome), intent (/joint),
gate (POST /log — externally-posted verdicts, verbatim). `GET /log` serves
{file, n, last-50 lines}; `POST /log` records and answers the seq. The LOG
dock (left dock mode 3, workspace menu row 8) draws the tail newest-at-
bottom, kind-colored (upload blue / mode green / intent yellow / gate
purple), wrapped by the same greedy law as the docs browser — and the
wrapped rows are CACHED, rebuilt only when a line lands or the dock width
changes (see below). `get_string` learned `\uXXXX` (surrogate pairs
included): a posted verdict's em-dash and CJK land verbatim, not as
ascii-escaped soup.

- **Rule 0 verdicts** (evidence: `engine/scratch/_log_verify.{py,log}`,
  `f4_log_stream.png` — PrintWindow, dock in LOG mode):
  - **D:** `probe heartbeat 'q' \ backslash<newline>newline<tab>tab —
    verbatim or it is a lie` — found verbatim in the file in 0.00-0.01 s
    AND in the served stream, after the \uXXXX fix (the first run caught
    the em-dash landing as `\u2014`: the falsifier fired, the engine was
    fixed, not the probe). PASS
  - **A:** /mesh_bin 1110396B, /hinge_bin, /joints_bin uploads logged
    `-> {"ok":true}` in 0.01 s; /show flip logged with its verbatim answer
    in 0.00-0.01 s; /joint intent logged `joint=knee_L ->
    {"ok":true,"owner":"edit",...,"theta_applied":30.000000}` in 0.00 s.
    PASS
  - **C:** 50-post burst — 50/50 in the file, seq 1..58 continuous, no
    reorder; the served ring's burst lines in order. PASS
  - **E:** idle 0.315-1.070 ms -> burst 0.300-0.325 ms (delta negative;
    50 posts in 0.22-0.34 s, budget 0.5 ms). PASS
  - **B:** last-3 file details == last-3 served details, byte-equal. PASS
  - **Regressions on the final binary:** `_stage_verify.py`,
    `_docs_verify.py`, `_console_verify.py` — ALL PASS. See the chrome note.
- **Found while verifying (two probe-side truths, documented):**
  - `_chrome_verify.py`'s gates B (ring max in band) and E (row verbatim)
    are FLAKY independent of F4: both failed with the LOG dock CLOSED
    (mode-3 branch never drawn), and E's failures show the gait clock
    advancing between the probe's expectation read and its rows read
    (steps equal, lam drifted — two reads of a live clock). Post-cache-fix
    with the LOG dock OPEN, B passed 4/4. F4's own cost gate (E above)
    measured the recorder itself at negative delta every run.
  - The LOG dock's first draft re-wrapped 200 lines EVERY FRAME — that
    was a real F4 cost and it did move the chrome probe's B gate. Fixed
    by the change-only rebuild cache; that is when B stopped failing with
    the dock open.
- **Files:** `engine/engine.{hpp,cpp}`, `engine/main.cpp`,
  `engine/ui.{hpp,cpp}`, this doc.
- **Next per the menu:** E2 deep links — and the board's own earliest
  non-green gate, B5 anatomy referee, is what the strip keeps naming.

## SHIPPED — THE MCP TWIN + THE BRIEFING (2026-08-30)

- **Statement:** an MCP twin over the studio HTTP API gives any MCP-speaking
  AI full, sanctioned control of the RUNNING engine with ZERO new engine
  surface — every tool routes through the existing endpoints (the F1 console
  law at process scale: one path, no side channels) — and one call,
  `briefing`, transfers complete working context (where the project stands,
  what the engine shows, what just happened) to an AI that has never seen
  this session. The human path is the same code: `python
  ChimeraEngine/mcp_studio.py --briefing` prints it for a copy-paste.
- **Prediction (unmeasured at naming time):** every tool's payload equals the
  same-moment HTTP read modulo live-clock fields; the briefing carries the
  standing rule verbatim + all 11 stage rows; a down engine answers "ENGINE
  DOWN" plainly; a paused screenshot md5-matches a direct /frame grab.
- **Falsifiers (named before the build):** (A) any tool disagreeing with the
  same-moment curl beyond live-clock tolerance; (B) the briefing missing the
  standing rule or any stage; (C) a stack trace instead of "ENGINE DOWN";
  (D) paused tool-screenshot md5 != direct /frame md5.

**What shipped.** `ChimeraEngine/mcp_studio.py` — a second FastMCP server,
`chimera-studio` (registered in `.mcp.json` and `opencode.json`; the workflow
engine `chimera-engine` is untouched — that one owns "proven", this one owns
"what's on screen"). Twelve tools: `state` (vitals: chrome + overlay + show +
joints + gait + water + volp in one read), `screenshot` (the pixel-clean
/frame channel to a PNG with md5), `transport` (play/pause/scrub/speed/step —
the D1 clock), `pose_joint` (ROM-clamped intent; the C1 ownership law stands),
`joints` (the editor document), `click` (aimed via the geometry the panels
publish), `console` (the one-path escape hatch — `METHOD /path [json]` through
the SAME handler the HTTP server runs), `log_tail` (the F4 recorder's edge),
`reel`, `stages` (the board's own feed, read never owned), and `briefing`.
Every tool answers "ENGINE DOWN (localhost:8090 unreachable)" when the engine
is down — an AI cannot fix what it cannot parse.

- **Rule 0 verdicts** (evidence: `engine/scratch/_mcp_studio_verify.{py,log}`):
  - **A:** paused — show/joints/log tool reads == same-moment curl, exact
    (the D1 freeze law makes paused frames deterministic). PASS
  - **B:** standing rule verbatim ("EARLIEST NON-GREEN GATE: B7 articulate"),
    11/11 stage rows byte-anchored in the briefing. PASS
  - **C:** dead port -> `ENGINE DOWN: http://localhost:59999 unreachable
    (URLError). Start chimera_engine.exe (port 8090) and retry.` PASS
  - **D:** paused tool screenshot md5 == direct /frame md5. PASS
  - **E (round-trips):** transport +1 step advanced the clock exactly 1/240 s;
    pose_joint knee_L 30 acked `theta_applied 30.000000` owner=edit; play
    handed the pose back to the show. PASS
- **Found while verifying (fixed same session):** the F4 twin's list field is
  `lines` (dicts {seq,t,kind,detail}), not `last` — the probe's first draft
  KeyError'd a PASSING engine. Read the response before asserting its shape
  (the /joint ack lesson, twice learned).
- **Files:** `ChimeraEngine/mcp_studio.py`, `.mcp.json`, `opencode.json`,
  this doc. No engine binary changes (the surface is the API's twin).
- **Next per the menu:** C4 scene outliner (the Godot Scene dock: the live
  systems as a tree with toggles routed through these same endpoints), C2
  inspector, E2 deep links, D5 render-to-MP4, D6 camera bookmarks.

## SHIPPED — C4: THE OUTLINER (2026-08-30)

- **Statement:** the outliner is a LIVE VIEW of engine state, not a copy —
  every row the dock draws is composed by the ENGINE at read time (one
  formatting site, `Engine::scene_rows()`) from the same atomics the HTTP
  endpoints serve, and every toggle routes through the console's one path
  (`console_exec`), so the panel, the HTTP twin, and the F4 record can never
  tell three different stories about the same switch.
- **Prediction (unmeasured at naming time):** the served rows equal the
  independent endpoint reads at the same configuration for every atom that
  has an independent read; a `/scene` POST flips the target endpoint within
  1 s and the F4 tail names the INNER endpoint (not `/scene`); an aimed
  `/ui_click` at a served rect toggles exactly that row and no other; the
  view costs < 0.5 ms of frame time.
- **Falsifiers (named before the build):** (A) any row's state != its
  independent endpoint read (show, joints, volp, gait, water_clock, frost,
  chrome — water_vis has no GET twin; its POST echo is the only read, noted
  not hidden); (B) `/scene` POST fails to flip `/gait` in 1 s, or the F4 tail
  lacks a mode event naming `POST /gait`; (C) an aimed click at the gait
  row's served rect fails the off-then-on round-trip, or any OTHER row moves
  with it; (D) ft_avg(SCENE) - ft_avg(BOARD) >= 0.5 ms; (E) `_stage_verify.py`
  regresses.

**What shipped.** The SCENE workspace (menu row 1, formerly the parked
"MODEL" row) opens the outliner in the left dock: ten atoms — `body` and
`overlay` (status-only: "36815 tris" / "loaded"), then `show`, `joints`,
`volp`, `gait`, `water_clock`, `water_vis`, `frost`, `chrome` as toggleable
rows with `[on]`/`[off]` chips, each with a live detail string (the show's
clock+speed, the joint count, the volp mode, the gait steps+omega, the water
clock's totals). A click on a toggleable row calls `Engine::scene_toggle`,
which rebuilds rows from FRESH state at click time (never the pushed view)
and queues the inner line — `POST /gait {"on":false}` and kin — through
`console_exec`; the F4 chokepoint then logs the inner endpoint's event with
its outcome, automatically, because there is no second path. The HTTP twin:
`GET /scene` serves the same `scene_rows()` plus the row hit-rects (only
while the dock is in SCENE mode — the aim map for `/ui_click`) and
`left_mode`; `POST /scene {"id","on"}` queues through `scene_exec` and
returns the queued line. `/scene` is deliberately NOT an F4 chokepoint kind —
the inner line logs itself; a double log would be a lie about what happened.

- **Rule 0 verdicts** (evidence: `engine/scratch/_scene_verify.{py,log}`,
  ALL PASS first run):
  - **A:** 7/7 atoms with independent reads matched exactly (show, joints,
    volp, gait, water_clock, frost, chrome); status rows honest
    (`body=36815 tris`, `overlay=none`, `volp=no kernel`, `frost=no pack`).
    PASS
  - **B:** `POST /scene {"id":"gait","on":true}` queued
    `POST /gait {"on":true}`, `/gait` flipped in 0.03 s, and the F4 tail's
    new event was kind=mode `POST /gait 11B -> {"ok":true,...}` — zero
    `/scene` self-events. PASS
  - **C:** 10 rects served; the aimed click at the gait row's rect toggled
    /gait off, then on; no other row moved on either click. PASS
  - **D:** ft_scene 0.351 ms vs ft_board 0.373 ms — delta -0.022 ms (the
    view is inside measurement noise). PASS
  - **E:** `_stage_verify.py` re-run after all of the above — 9/9 PASS.
    PASS
- **Found while verifying C2 (fixed same session):** the water clock row
  showed `inj=0/4294967295` — that was THIS feature's formatting bug, not the
  engine's state: `inj_target` is int32 with -1 = "no target", the endpoint
  has always served -1, and the row's `%u` re-interpreted the sign bit. The
  "honest rendering" note this section used to carry was wrong about whose
  oddity it was; the C2 probe's value-for-value comparison caught it, which
  is exactly what gate A is for.
- **Files:** `engine/ui.{hpp,cpp}` (SceneRow, the mode-4 dock, menu row 1,
  hot range 600+), `engine/engine.{hpp,cpp}` (`scene_rows`/`scene_command`/
  `scene_exec`/`scene_toggle`, the cb wiring, both push sites),
  `engine/main.cpp` (GET/POST `/scene`), this doc.
- **Next per the menu:** C2 inspector, E2 deep links, D5 render-to-MP4, D6
  camera bookmarks — and the board's own earliest non-green gate, B5 anatomy
  referee, is what the strip keeps naming.

## SHIPPED — C2: THE INSPECTOR (2026-08-30)

- **Statement:** the inspector is the C4 live-view law applied to depth —
  selecting an outliner atom serves its FULL state document, composed by the
  ENGINE at read time (one formatting site, `Engine::inspect_kv`) from the
  same atomics the named endpoints serve; the panel holds no properties of
  its own, so it cannot drift or invent. Selection is pure VIEW state: one
  atomic, no console path, no F4 event (nothing in the scene changes).
- **Prediction (unmeasured at naming time):** every inspector line that names
  a value equals the independent endpoint's same-named field at the same
  moment; selection is drivable identically from the glass (label click) and
  HTTP (`POST /inspect`); the chip and the label are separate intents that
  never cross; the open inspector costs < 0.5 ms.
- **Falsifiers (named before the build):** (A) any inspector key/value
  disagrees with the independent endpoint's same-named field (gait, show,
  water_clock — the three richest documents); (B) `POST /inspect` fails to
  move the served view, or deselect fails to return STATUS, or id-select
  picks the wrong row; (C) a chip click toggles WITHOUT selecting, or a label
  click selects WITHOUT toggling; (D) ft delta >= 0.5 ms; (E)
  `_scene_verify.py` regresses.

**What shipped.** The outliner row is now TWO intents: the chip
(`[on]`/`[off]`) is the toggle (unchanged, one path), the label selects the
atom for inspection. The right dock becomes `INSPECT - <atom> (C2)`: the
FPS pulse stays on top, then the atom's full document — gait serves
loaded/on/steps-per-frame/omega/steps_total/thetaL/thetaR; show serves
playing/time/speed/n_joints/period/current/theta; every atom down to chrome
serves its whole endpoint state. The footer shows the exact console line for
the toggle (`toggle: POST /gait {"on":false}`) — the edit path is taught in
place, and it is the SAME one path. Re-click the row (or `POST /inspect
{"row":-1}`) and STATUS returns. The HTTP twin: `GET /inspect` serves the
same `inspect_kv()` document; `POST /inspect {"row"|"id"}` selects. The
/scene twin grew `inspect_row` and a `sel_rects` aim map. Selection is NOT
an F4 event by design — a log line would claim a scene change that never
happened.

- **Rule 0 verdicts** (evidence: `engine/scratch/_inspect_verify.{py,log}`,
  ALL PASS):
  - **A:** 12/12 fields across gait, show, water_clock matched the
    independent endpoints value-for-value (show paused first — the D1 freeze
    law makes the clock comparison exact). PASS
  - **B:** id-select (`{"id":"gait"}`) landed row 5; `{"row":-1}` returned
    STATUS; row 999 refused with an error. PASS
  - **C:** chip click toggled /gait with inspect_row unmoved; label click
    selected row 5 with /gait unmoved; label re-click deselected. The two
    intents never crossed. PASS
  - **D:** ft_inspect 0.963 ms vs ft_board 0.911 ms — delta +0.052 ms. PASS
  - **E:** `_scene_verify.py` re-run after all of the above — ALL PASS
    (including its own nested `_stage_verify.py`). PASS
- **Found while verifying (fixed same session):** gate A caught a REAL bug in
  C4's shipped code — the water clock row printed `inj=0/4294967295` because
  the row's `%u` re-interpreted `inj_target`'s sign bit (int32, -1 = "no
  target"; the endpoint has always served -1). The C4 doc's "honest
  rendering" note was wrong about whose oddity it was — corrected in place.
  This is the value-for-value gate doing exactly its job.
- **Files:** `engine/ui.{hpp,cpp}` (inspect view, chip/label split, the
  right-dock inspector), `engine/engine.{hpp,cpp}` (`inspect_row_`,
  `inspect_kv`, the cb + both push sites), `engine/main.cpp`
  (GET/POST `/inspect`, `/scene` grew `inspect_row` + `sel_rects`), this doc.
- **Next per the menu:** E2 deep links, D5 render-to-MP4, D6 camera
  bookmarks, B4 ledger — and the board's own earliest non-green gate, B5
  anatomy referee, is what the strip keeps naming.

## SHIPPED — D6: CAMERA BOOKMARKS (2026-08-30)

- **Statement:** a camera bookmark is a NAMED 8-float camera state (r, theta,
  phi, target xyz, pan xy) owned by the ENGINE and persisted to
  `camera_bookmarks.txt`; saving captures the live camera verbatim, recalling
  applies the full state through the SAME membrane-request thread discipline
  as POST /camera, and the store is served over HTTP — so a glass chip
  click, a human POST, and an AI call frame the IDENTICAL shot.
- **Prediction (unmeasured at naming time):** recall round-trips all 8
  components to within 1e-4 (read back through /project's cam field, the
  independent read); a paused re-recall reproduces the frame md5 exactly
  while a different camera does not; the served list equals the file on
  disk; the chips cost < 0.5 ms.
- **Falsifiers (named before the build):** (A) any of the 8 components wrong
  by > 1e-4 after moving away — for a live-captured bookmark AND an
  exact-numbers one with non-zero target/pan (the half POST /camera cannot
  set); (B) paused pixel identity breaks, or two different bookmarks share
  an md5; (C) GET /cameras disagrees with the file on disk, or delete /
  unknown-recall misbehave; (D) chips cost >= 0.5 ms; (E) the studio chain
  (`_inspect_verify.py`, which nests scene, which nests stage) regresses.

**What shipped.** Bookmark chips under the viewport's HUD rows — `[1 alpha]
[2 beta] [+ cam]` — one click recalls, `+ cam` saves the live camera with an
auto name. The engine owns the store (`cam_marks_`), persists every mutation
to `camera_bookmarks.txt` (flat: name + 8 floats, same CWD discipline as the
session logs), and loads it at studio init — bookmarks survive relaunch.
`set_camera_full` applies all 8 floats (radius floor respected); the glass
path calls it directly (ui clicks land on the render thread), the HTTP path
crosses through a membrane request (`cam_full_set`), same discipline as
POST /camera. The twin: `GET /cameras` (the store, verbatim) ·
`POST /cameras {"op":"save"}` (live capture or `"v":[8]` exact numbers — an
AI frames a shot from a derivation) · `{"op":"recall"}` · `{"op":"delete"}`.
The reel independently captions each grab with its camera — the two stories
match because both read the same `g_cam`.

- **Rule 0 verdicts** (evidence: `engine/scratch/_cameras_verify.{py,log}`,
  ALL PASS):
  - **A:** exact-numbers recall (non-zero target+pan): worst |delta| =
    0.00e+00, bit-exact. Live-capture recall: 1.2e-08 (float reparse noise,
    4 orders under the bar). PASS
  - **B:** paused — alpha md5 `3c6dcc79…`; moved away: differs; re-recalled:
    identical; beta: distinct. PASS
  - **C:** served == file on disk (3 bookmarks, values to 1e-6); unknown
    recall refused; delete removes from both. PASS
  - **D:** ft_zero 2.259 ms → ft_chips 2.481 ms — delta +0.222 ms. PASS
  - **E:** `_inspect_verify.py` ALL PASS (which re-ran `_scene_verify.py`
    ALL PASS, which re-ran `_stage_verify.py` 9/9). PASS
- **Files:** `engine/ui.{hpp,cpp}` (the chips, hot range 800+/850),
  `engine/engine.{hpp,cpp}` (the store, persistence, `set_camera_full`, cb
  wiring + both push sites), `engine/main.cpp` (membrane request grew
  `cam_full[8]`, GET/POST `/cameras`), this doc.
- **Next per the menu:** E2 deep links, B4 ledger — and
  the board's own earliest non-green gate, B5 anatomy referee, is what the
  strip keeps naming.

## SHIPPED — D5: RENDER-TO-MP4 (2026-08-30)

- **Statement:** a render is an OFFLINE capture SESSION owned by the engine —
  `POST /capture {"op":"render","t0","t1","fps","camera","name"}` scrubs the
  studio clock through N = round((t1-t0)·fps) exact poses, presenting and
  capturing each through the SAME offscreen path /frame uses, writing
  `captures/<name>/f%04d.png`, then handing the clock (time AND playing)
  back exactly as found. The MP4 encode is the DRIVER's job
  (`cpp_bridge.encode_movie` → ffmpeg); the engine's job is frame-exact
  capture. A camera bookmark name frames the whole render through the D6
  membrane discipline.
- **Prediction (unmeasured at naming time):** every captured PNG is
  md5-identical to an independent scrub+grab at the same t (the render is
  the show, not a look-alike); the operator's clock survives a render
  bit-exactly, paused or playing; the encoded MP4 reads back with the
  requested fps and frame count; the CAPTURE dock's served record equals
  the directory on disk; and all of it works with the window MINIMIZED.
- **Falsifiers (named before the build):** (A) frame count ≠
  round((t1-t0)·fps), stale files counted as fresh, or any frame's md5 ≠
  the independent grab at the same t; (B) the clock (time or playing)
  differs from before the render, in either the paused or the playing
  case; (C) ffprobe reads back a different rate or frame count; (D)
  `GET /capture`'s record disagrees with the directory on disk; (E) the
  studio chain (`_cameras_verify.py`, nesting inspect → scene → stage)
  regresses.

**What shipped.** The CAPTURE dock (menu row 6, left dock mode 5) draws the
live session document — state, name, range, fps, frames done/total, last
frame t, dir — from the ONE formatting site `Engine::capture_kv()`, which
`GET /capture` serves verbatim (the dock and the twin can never drift).
The endpoint is WAITING (the /mesh_bin discipline): the HTTP handler drives
scrub → present → capture → PNG per step while the render thread owns the
GPU, refuses a second concurrent render and a render with no mesh loaded,
sanitizes the name into a path-safe directory, and answers only when the
session is done or failed — including waiting for the RESTORE scrub to
land, so `ok` means the clock IS back, not that it will be soon.

**The TWO bugs the probe found (and the fixes).** (1) The pre-existing
"the /frame endpoint works even when minimized" comment was a LIE: with a
0x0 surface, `vkAcquireNextImageKHR` returns OUT_OF_DATE every frame and
both `frame()` and the idle path returned BEFORE the capture block — every
/frame and /capture timed out on a minimized window, which is exactly how
the operator runs while gaming. Fixed: on OUT_OF_DATE with 0x0 caps, fall
through with `can_present=false` (the blit+UI block is entirely inside
`if (can_present)`; submit is ungated), set `headless_minimized_`, and pace
the main loop at 120 fps when headless instead of 300. (2) The DEVICE_LOST
crashes — three of them, all in the probe's LOAD phase, all on the SECOND
probe run against one engine process. Not churn (a dedicated
minimize/restore-mid-render test passed 48/48 frames), not the new
fall-through: the JOINTS kernel's descriptor set binds two buffers it does
not own — `hinge_rest_buf_` (binding 0, "Rest"), destroyed+recreated by
every `set_hinge`, and `tri_vbuf_` (binding 4, "Out"), destroyed+recreated
by every mesh full-load — and NOTHING re-pointed the set afterward, so the
next dispatch read a destroyed buffer (illegal access → device lost). A
fresh engine never reproduced it because the load order mesh → hinge →
joints ends consistent; only a RELOAD dangled. The water-vis (W4) and
frost (H9) sets already carried the cure — a dirty flag set at recreation,
a lazy rebind in frame() before the dispatch — so the joints and hinge
sets got the same: `joints_desc_dirty_` (set by `load_mesh` AND
`set_hinge`), `hinge_desc_dirty_` (set by `load_mesh`), `joints_rebind()`
/ `hinge_rebind()` called at the dispatch sites. Verdict: the exact repro
— the full probe run TWICE on one engine, window VISIBLE at ~299 fps —
passes ALL gates both times with zero validation errors on stderr. Known
same-class instance NOT fixed (untested path, no probe coverage): the volp
debug kernel binds `tri_vbuf_` at binding 6 with no rebind — flagged for
its own membrane when the volp path gets one.

- **Rule 0 verdicts** (evidence: `engine/scratch/_capture_verify.{py,log}` —
  ALL PASS force-minimized AND ALL PASS twice on one visible engine, the
  reload repro; churn: `engine/scratch/_churn_test.py`):
  - **A:** N=4 = round(0.5·8), all fresh; per-frame md5 == independent
    scrub+grab, zero mismatches. PASS
  - **B:** paused case: before(t=3.21, playing=False) → after(t=3.21,
    playing=False), bit-exact (the endpoint waits for the restore scrub to
    land before answering; the probe reads the clock BEFORE its own md5
    grabs scrub it — an earlier FAIL was the probe reading after them).
    Playing case: hands back running. PASS
  - **C:** ffprobe readback: rate 8/1, 4 frames — as requested. PASS
  - **D:** served record == directory: state=done, 2/2 frames on disk for
    the playing render. PASS
  - **E:** `_cameras_verify.py` ALL PASS (12 chain gates, nesting inspect →
    scene → stage). PASS
  - **Reload (the crash's own falsifier):** the probe run TWICE against one
    engine process, window visible — the second run's load phase (mesh +
    hinge + joints RELOADED over live ones) was the DEVICE_LOST repro;
    post-fix: ALL PASS both runs, zero VK errors on stderr. PASS
  - **Churn (beyond the named falsifiers):** 48/48 frames with 4
    minimize/restore cycles mid-render; engine alive; /frame still answers.
- **Files:** `engine/engine.{hpp,cpp}` (session state, `capture_kv()`,
  both push sites, the OUT_OF_DATE fall-through + `headless_minimized_`,
  `joints_rebind()` / `hinge_rebind()` + their dirty flags),
  `engine/ui.{hpp,cpp}` (CAPTURE dock: menu row 6, mode 5),
  `engine/main.cpp` (GET/POST `/capture` — the render waits for the
  clock-restore scrub to land before answering; headless pacing), this doc.
- **Next per the menu:** E2 deep links, B4 ledger — and the board's own
  earliest non-green gate, B5 anatomy referee, is what the strip keeps
  naming.

## SHIPPED — E2: DEEP LINKS (2026-08-31)

- **Statement:** a dock row is a link when its TARGET is derived from the doc
  by `tools/studio_board.py` (`row_line` = the glance-table row, `spec_line`
  = the `###` envelope's heading, −1 when absent) and its LANDING is resolved
  through the LIVE wrap map in `prepare()` — so the glass click on the
  envelope's `[docs ->]` FALSIFIER / NEXT ACTION rows (hot ids 900/901) and
  `POST /link {"stage":N}` land identically BY CONSTRUCTION: one resolution
  law (`docs_link_line()` → `pending_line` → the target source line's FIRST
  display line, clamped by `scroll_max`) for both glass and HTTP.
- **Prediction (unmeasured at naming time):** every stage's link lands the
  DOCS dock at exactly its own doc line; a synthetic click on the FALSIFIER
  row's hotspot produces the same `(doc, top_src)` as POST /link for the same
  stage; the wrap map is monotonic and total.
- **Falsifiers (named before the build):** (A) any board-JSON `row_line` /
  `spec_line` whose doc line does NOT contain that stage's glance-table row /
  `###` envelope heading — the target is a lie (offline, no engine needed);
  (B) POST /link `{"stage":i}` for ANY i fails to land — GET /studio_doc never
  shows doc 0 with `top_src ==` the stage's derived line within 6 s; (C) the
  synthetic click lands a DIFFERENT `(doc, top_src)` than POST /link for the
  same stage — two resolution laws exist and the "one law" claim is false;
  (D) the wrap map breaks — the live `top_src` sweep over scroll is not
  non-decreasing, or a byte-exact re-derivation of `docs_rewrap()` at the
  dock's own width disagrees with the engine's display count, or some source
  line maps to zero display lines.

**What shipped.** The board JSON carries each stage's own line numbers in the
pipeline doc (derived, never hardcoded — a doc edit moves the number and the
Studio just reads it). `docs_rewrap()` now records `display_src` (display line
→ source line) alongside the wrapped text; a deep link sets `pending_line`
and switches to the DOCS workspace, and the NEXT prepare() — after the rewrap,
with `scroll_max` known — puts the target's first display line at the top,
the same clamp a human's scroll obeys. The envelope draws `[docs ->]` on its
FALSIFIER and NEXT ACTION rows with their live rect published as `link`
(client pixels, zeroed when no envelope is up) so a synthetic click IS the
glass deep link; `GET /studio_doc` serves `top_src` (the source line under
the scroll's top — the wrap map read back), which is where a landing is
PROVED. The MCP twin gained `link(stage)` over POST /link, and the briefing's
driving manual names it.

**The bugs found while verifying (all probe-side; the engine was innocent).**
(1) Falsifier A first fired on B7: its `spec_line` points at `### B7b — VOLP
GENERALIZATION`, not a plain `### B7`. Not a bug — the doc has no plain B7
envelope, and the tool's own law attaches `B7b` to stage B7 (whose pending
status is exactly "volp-generalization"); that section IS B7's membrane.
The probe asserted `^### B7\b` and fired on the truth; it now accepts the
tool's `B\d+\w?` law. (2) Falsifier D failed on run 1 with a live-sweep
inversion: C's second landing poll could pass SPURIOUSLY — after the glass
leg, scroll already sat at the target, so POST /link's fresh `pending_line`
could still be in flight when D started sweeping; one frame resolved it
mid-sweep and jumped the scroll back. A standalone sweep showed zero
inversions (the map is monotonic). Fixed by starting each C leg from a
PROVEN-OTHER scroll (`scroll_to(0)` + a quiescence check) and giving D its
own quiescence pre-check — a landing must be observed as a CHANGE, not merely
seen. (3) `studio_board.py` crashed with `UnicodeEncodeError` AFTER writing
the JSON: B5's status cell now carries `≥`, which the cp1252 console cannot
print. Fixed with `sys.stdout.reconfigure(errors="replace")` — the tool no
longer dies on a glyph the doc is allowed to contain.

- **Rule 0 verdicts** (evidence: `tools/probe_studio_e2.py`,
  `.tmp/e2_probe/results.json` + `engine_stdout.log` — ALL PASS twice
  back-to-back, fresh engine each run):
  - **A:** all 11 stages' `row_line`s contain their `| **B#** |` glance-table
    row; B5–B8's `spec_line`s are their `###` headings (B7 → its own B7b
    section, per the tool's law). PASS
  - **B:** POST /link lands doc 0 with `top_src ==` the derived line for ALL
    11 stages (B5–B8 at their envelope headings, the rest at their table
    rows), each within the 6 s poll. PASS
  - **C:** glass `(0, 54)` vs http `(0, 54)` — identical landing from the same
    clean start for B5's spec heading; one resolution law, glass and HTTP.
    PASS
  - **D:** `maxc=29` (the dock's own width ÷ advance) reproduces the engine's
    `n_display=456`; the live sweep over all 437 readable scroll positions is
    non-decreasing AND byte-identical to the re-derived map; every one of the
    144 source lines maps to ≥1 display line. PASS
  - **VK errors in the engine log:** zero (validation / VK_ERROR /
    device-lost pattern). PASS
- **Files:** `engine/ui.{hpp,cpp}` (`display_src` wrap map, `pending_line`,
  public `docs_link_line()` / `docs_link_stage()` / `docs_top_src()`, hot rows
  900/901 + the `[docs ->]` affordance, `link_hot_` rect), `engine/main.cpp`
  (POST `/link`; GET `/studio` serves the link rect; GET `/studio_doc` serves
  `top_src`), `tools/studio_board.py` (`row_line` / `spec_line` derivation +
  the console-encoding fix), `ChimeraEngine/mcp_studio.py` (`t_link` + the MCP
  tool + the briefing line), `tools/probe_studio_e2.py`, this doc.
- **Next per the menu:** B4 ledger, then the rest of the menu by value (C3
  modes, D2 markers, D4 A/B compare) — and the board's own earliest non-green
  gate, B7 articulate, is what the strip keeps naming.

## SHIPPED — E2a: RENDER-THREAD DEEP-LINK ACK (2026-09-03)

- **Statement:** HTTP deep-link navigation must cross the same render-thread
  membrane as visible Studio clicks; the network handler may request and await
  a committed landing, but it must never mutate `StudioUI` directly.
- **Prediction:** `POST /link {"stage":N}` will be consumed in both the normal
  and idle render paths, apply the same `docs_link_stage()` operation as the
  glass link, and return the committed source line/document. Concurrent link
  requests will serialize instead of replacing one another's stage.
- **Falsifier:** reject the change if either render path lacks a consumer, if
  the HTTP handler still calls a `StudioUI` navigation method directly, if a
  request can be acknowledged before render-thread application, if concurrent
  requests overwrite one another, or if a timeout reports a fabricated landing.

**What shipped.** `Engine::request_ui_link()` owns a single-slot request and
acknowledgment membrane. A submission mutex serializes HTTP callers; the stage
is published atomically; the render thread resolves the board-derived line,
calls `docs_link_stage()`, records the committed document, and signals the
waiting caller. `frame()` and `frame_idle_ui()` consume the same request before
`prepare()`, so docs navigation remains live with or without a mesh. A three-
second wait returns `ok:false`, `line:-1`, and `doc:-1` on a stalled render rather
than reading unsynchronized UI state or claiming a landing that did not happen.

- **Verification:** Debug compiled and linked successfully. Source falsifiers
  passed: two render-path consumers, two render-thread UI applications, no
  direct `/link` UI call from the HTTP handler, serialized submission, and
  acknowledgment through the condition variable. Runtime API/glass probing
  remains open because the live Release executable was not interrupted.
- **Files:** `engine/engine.{hpp,cpp}` (queued request, serialization, render
  consumers), `engine/main.cpp` (acknowledged `/link` response), this doc.

---

## SHIPPED — G1: THE GLASS CHANNEL (2026-08-31)

**The one-line finding:** the Studio is drawn into the SWAPCHAIN
(`engine.cpp`, the render pass inside `frame()`), and `/frame` copies
`rt_image_`, which the overlay "never touched — the dyad's /frame stays
pixel-clean". That was deliberate and it is still right. But nobody had priced
the consequence: **the instrument existed in no capture the repo could make.**
Zero hits repo-wide for `PrintWindow|BitBlt|mss|ImageGrab|win32gui`. The eye
could see the physics and never the window. Measured on the first glass grab:
**49.8% of the screen was invisible** (docks 73% covered, status bar 87%, top
bar 100%, centre 39% — the pipeline board).

**`GET /glass`** copies the swapchain *after* `ui_.record()` into its OWN
staging buffer and its OWN destination (`glass_rgba_`):

| | `/frame` | `/glass` |
|---|---|---|
| reads | `rt_image_` (offscreen) | `swap_imgs_[sc_idx]` (presented) |
| contains | the 3D render only | render + overlay + docks + bar + HUD + console + reel |
| destination | `capture_rgba_` | `glass_rgba_` |
| lands in the reel | yes (D3) | **no** — the reel is the pixel-clean ledger |

`TRANSFER_SRC_BIT` on the swapchain images was already set (`engine.cpp:862`,
commented *"frame capture reads the swapchain image"*) — the flag had been
waiting years for the route that used it.

**Two pre-existing defects the build walked into, both fixed:**

1. **`/frame` could not complete at all.** With `n_ == 0` and no mesh the engine
   lives in `frame_idle_ui()`, which serviced *no* capture — while its own
   comment claimed "the idle path keeps the UI's own captures servable
   headless". Claim and code disagreed; the operator's eye hit the code. Both
   channels now follow **one law** (`readback_captures()` + the shared
   `record_glass_copy()` recorder) so an idle grab cannot drift from a rendered
   one. `/frame` in idle clears `rt_image_` to the studio background rather than
   reading an offscreen image nothing drew this pass.
2. **Launching minimized silently loses the whole swapchain** — a 0×0 surface
   extent fails `vkCreateSwapchainKHR`, and nothing reports it until a capture
   times out three seconds later.

**NO PRESENT, NO GLASS.** `can_present == false` (minimized / out-of-date) now
returns `{"ok":false,"error":"no present: the window is minimized or the
swapchain is out of date -- there is no glass to read"}` instead of last frame's
pixels. An instrument that reports on a window nobody can see is worse than no
instrument.

- **Rule 0 verdicts** (evidence: `tools/probe_glass.py`, artefacts
  `.tmp/glass_probe/`, idempotent across runs):
  - **A — the pixel-clean channel never moves:** `frame(overlay ON)` is
    **byte-identical** to `frame(overlay OFF)` (sha256 `0957ed3f51953e23` both
    ways). PASS
  - **B — the glass carries the panels:** diff-pixels `overlay OFF = 56,430`
    (chrome alone) → `overlay ON = 1,032,734` (**18×**). PASS
  - **C — THE ABLATION:** turning the chrome off shrinks it
    `1,032,734 → 1,001,774`, and `frame` stays byte-identical. Without this the
    channel would be a second capture route wearing a new name. PASS
  - **D — stability:** three grabs, show clock paused →
    `[1032734, 1032734, 1032734]`, spread **0.0000%**. PASS
  - **D-loud** (`--minimize`): minimized `/glass` **refuses** rather than
    returning a stale frame. PASS
  - **E:** zero VK errors. PASS
- **Files:** `engine/engine.cpp` (`ensure_glass_staging`, `record_glass_copy`,
  `readback_captures`, `glass_frame`, the glass block in both `frame()` and
  `frame_idle_ui()`), `engine/engine.hpp` (the GLASS CHANNEL block + error
  enum), `engine/main.cpp` (`GET /glass`), `tools/probe_glass.py`, this doc.
- **Two laws the run earned:**
  - **Quiescence on the glass is NOT byte-identity.** The glass carries the
    status bar's LIVE fps readout, so it is never twice identical — defining
    settling as equality made the instrument report "never settled" on a channel
    that measured perfectly still. The stable quantity is the **structure**
    (diff-pixel count), not the digits.
  - **The cp1252 console strikes again** (same class as `studio_board.py`'s `≥`):
    a window title with a glyph it cannot encode killed the `--minimize`
    falsifier outright. Sanitized.
- **Next per the menu:** G2 the dyad scan — shipped, see below.

---

## SHIPPED — G2: THE DYAD SCAN (2026-08-31)

**`tools/dyad_scan.py`.** The eye reads the glass, one image per call; its report
is the work list.

```
python tools/dyad_scan.py --shots 8 --reads 3
python tools/dyad_scan.py --shots 4 --crop 2230,92,330,900    # one panel, close
python tools/dyad_scan.py --prompt-file my_question.txt --shots 2
python tools/dyad_scan.py --resume Saved/dyad/<run_id>
```

### Terms of engagement (operator, 2026-08-31)

**THERE IS NO SCORE.** No alignment, no threshold, no pass/fail, no points. The
eye is not a gate to clear; it is a second mind looking at the same window. The
craft is entirely in what you ASK — be descriptive about what you are looking for
and it will tell you its opinion. *"Living in this world is subjective and so is
this process."*

So N reads per shot are **not a vote and are never averaged**. All are reported
verbatim. Where the eye disagrees with itself on the SAME image, that
disagreement **is** the finding: the thing it is arguing about is ambiguous in the
picture. Resume-safe, flush-after-every-read (a 6-minute vision call is never
lost), and the HTTP twins are recorded beside every shot because the eye reads
pixels while the twins read state.

### Two laws the instrument earned the hard way

- **The scan perturbs the frame rate it records.** Every capture calls
  `vkQueueWaitIdle`, so mid-scan the engine reads **10.7 fps / 84 ms**; at rest it
  is **56 fps / 8.95 ms**. Believing the per-shot number would be an instrument
  convicting the engine for the instrument's own stall. The tool now takes clean
  samples before and after and marks every per-shot twin
  `_fps_is_under_capture_load`. (The eye read the mid-scan "7 fps" *off the glass*
  and reported it as a defect — it was looking at my stall.)
- **The eye corrects itself under magnification.** The whole-window report claimed
  "glyph collision on the trailing characters" of three STATUS lines. Two close
  reads of that panel both said there is none — *"every character sits in its own
  monospace cell… the density is just a small font rendered tightly"* — and found
  the REAL defect instead (the clipped FPS line below). A whole-window read at 1:1
  is too coarse to judge 9 px text. `--crop` is the higher-magnification
  instrument. An eye's first claim is a claim; magnification is how you test it.

### The first three defects it named — all fixed

1. **The STATUS panel's FPS line was clipped at the panel edge.** It is
   arithmetic, not taste: 36 chars × 9 px = 324 px in a 330 px dock, so it cannot
   fit its own padding. The **panel's width** now picks the format, degrading in
   tiers, so a number is never cut mid-digit (a truncated "9" reads as "9" *and*
   as "95" depending on where the border falls).
2. **The standing rule was printed twice** — under the stage strip and again in
   the status bar: *"duplicated, low-value, adds noise."* The board states the
   RULE (B2, computed by `tools/studio_board.py`); the bar now states WHERE YOU
   ARE, derived from `board_.stages` rather than parsed out of the board's
   sentence. One source, so neither can drift. The bar reads `B7 ARTICULATE`.
3. **The whole UI was too small for 2K.** Root cause was ONE number: a fixed 16 px
   Consolas whose GDI metrics *become* `advance_` and `cell_h_` — the unit every
   text position is measured in. So the fix is one derived factor, not a hunt:
   `ui_scale_ = window_height / DESIGN_H(1080)`, applied to the font, the bar, the
   collapsed title bars and the panel sizes. **Nothing was re-tuned for 1440** —
   the proportion the eye approved at 1080p is what is preserved. Measured: UI
   coverage **41.2% → 49.8%**, which is the 1080p figure exactly; `lh` 24→29,
   `advance` 9→12. Panel sizes are stored in DESIGN units and the drag handler
   converts at the seam (`to_design`), or a panel jumps by the scale factor the
   instant you release it.

   **KNOWN LIMIT, recorded not hidden:** the scale is derived **once in `init()`**.
   `create_font_atlas()` allocates a new `VkImage` while the descriptor that
   samples it is written once at init — rebuilding at runtime left `dset_` bound
   to the old image (measured: the UI dropped to **1.0% coverage**). A mid-session
   resize does not rescale yet; the fix is to update the descriptor and destroy
   the old image/view, in its own turn.

### The eye's current list (Saved/dyad/2026-08-31_145002, its own priority)

1. **The empty black viewport reads as BROKEN, not as an empty scene.** Grid +
   axes + a "no mesh loaded" placeholder. *"This is your single biggest defect."*
2. **The grid is broken:** REEL (D3) and TIMELINE (D1) span only the CENTRE
   column, leaving black rectangles bottom-left and bottom-right. *"Those two
   black blocks look like a layout bug, not intentional whitespace."*
3. **Zero horizontal margins:** the title line and the B0–B10 row run edge to
   edge, so the top feels cramped and unframed.
4. `+ cam` is a plain grey box beside three blue-outlined ones — inconsistent
   affordance; all four orphaned in empty black.
5. Too many competing accent colours and no on-screen key for the gate colours.
6. The bottom bar is under-filled: large empty gaps between its three clusters.

### ONE OPEN TENSION — an operator decision, not mine

After the 1.33× scale the eye **still** says the type is too small: *"At
2560×1440 the type does not scale up, so it looks tiny… scale type up ~1.5× for
4K."*

The scale preserved the 1080p **proportion** exactly, which is the defensible
derived answer. The eye is asking for a larger **relative** size than that design.
Those are not the same request, and closing the gap means picking a number —
which is taste, and taste is the operator's. **Options:** (a) keep the derived
proportion and accept the eye's objection as recorded; (b) add one explicit
legibility factor (e.g. type height as a fraction of screen height) and derive
*that* instead; (c) let the operator set it by eye, since they are the terminal.
