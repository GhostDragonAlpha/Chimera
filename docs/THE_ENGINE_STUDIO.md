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

## SHIPPED — A2a: LINE-ISOLATED STATE RECOVERY (2026-09-03)

- **Statement:** one malformed numeric record in `studio_state.txt` must not
  suppress valid workspace records that follow it.
- **Prediction:** when `nan`, `inf`, or another invalid numeric token appears in
  the middle of the state file, that record is skipped, later valid records are
  restored, and the next save rewrites a clean key/value file.
- **Falsifier:** reject the change if a malformed line terminates state loading,
  later valid layout values are lost, invalid geometry reaches the UI, or the
  engine cannot serve `/studio` afterward.
- **Implementation:** `StudioUI::studio_state_load()` now reads one physical line
  at a time through an isolated `std::istringstream`. Extraction failures and
  non-finite values are ignored for that line only; the existing finite checks
  and layout clamps remain in force.
- **Verification:** configured Debug build/link passed. Focused source checks
  confirmed line-isolated parsing, finite filtering, removal of the old
  whole-stream loop, and retention of later fields. A malformed-line recovery
  model check passed. Runtime fixture verification remains open for this new
  behavior; the local agent's evidence directory was not modified.

## SHIPPED — E1a: RENDER-THREAD DOCS CONTROL (2026-09-03)

- **Statement:** document selection and scrolling are render-thread-owned editor
  actions whether they originate from the docs panel or HTTP.
- **Prediction:** `POST /studio_doc {"doc":N}`, `{"scroll":N}`, or both applies
  in the same order as visible docs controls in normal and idle paths; the
  response reports the acknowledged document and clamped scroll values, and no
  HTTP worker mutates `DocsState` directly.
- **Falsifier:** reject the change if `/studio_doc` directly calls `docs_set()`
  or `docs_set_scroll()` from the HTTP handler, either frame path misses the
  request, a timed-out request applies stale navigation later, or the request
  changes simulation, pose, camera, or mesh state.
- **Implementation:** `Engine::request_ui_doc()` serializes callers, queues the
  optional document and scroll operations, and waits for render-thread
  acknowledgment. The normal and idle frame paths consume the same request;
  cancellation is protected by the request mutex, and shutdown wakes blocked
  callers. The existing UI methods remain the single state owner and continue
  to persist document state through the A2 workspace store.
- **Verification boundary:** source falsifiers passed for one declaration and
  definition, two frame-path consumers, atomic pending state, render-thread-only
  DocsState mutation, HTTP no-direct-write discipline, cancellation, and
  shutdown wakeup. Debug compiled and linked successfully; runtime API probing
  remains open because the live Release process was not interrupted.

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

### The subject baseline (2026-09-03, post binary-swap)

The live window is the **triangle lane**: `chimera_engine.exe` rebuilt from HEAD
(exe sha256 prefix `4cc84f9c…`), the creature loaded via `POST /mesh_bin` from
`Saved/meshes/monkey_birth.bin` (the SALLY monkey birth mesh). Triple-verified:
pixel analysis (object fills frame at orbit r=16), the dyad's independent visual
read ("a solid shaded triangle-mesh creature… a continuous polygonal mesh rather
than a particle cloud"), and `GET /studio` reporting the `state` object — the
persistence binary confirmed live, with `studio_state.txt` written on first
state change. **Lane guard:** the subject is loaded through `/mesh_bin`
(triangles). The `/membrane_bin` splat/orb route is the retired presenter — do
not load it over the creature. Camera framing note: auto-frame (r≈27.9) renders
the subject small in an 800×600 `/frame`; r≈14–16 fills it.

### The stale-spv incident and the lighting fix (2026-09-03, render lane)

The dyad's lighting critique ("severely underexposed single-source... near-black
and merge into the background") led to a build-system fault, not just a shader:
CMake's hand-list compiled SEVEN shaders while the triangle lane's .spv files
were copied STALE — `render_tri.frag` edits never reached the GPU. The list is
derived now (every .vert/.frag/.comp/.glsl in shaders/ compiles; stage kept in
the spv name for vert/frag pairs, bare stem for compute; collision guard).
Shipped with the derived lighting membrane: key 0.85 + wrap 0.10 unchanged in
direction (the contact shadow must keep agreeing), fill 0.18 opposite the key
(4.7:1 key:fill, the readable-form band), hemisphere ambient mix(0.15,0.35,up).
Measured same-camera: subject mean 69.9→94.0, near-black dim-band 0.290→0.085.
The GSQ RCO eye (30.3s per read, served-by verified) confirms soft symmetric
lighting, no vanishing limbs; its findings — shadow detached from the contact
point, floor barely visible — are the next membrane (one problem: nothing
visible for the shadow to land on). The viewport "strut" from r7 is the grid's
bright green Y triad arm at the origin, a feature ("up reads first"), misread.

### Chrome polish batch (2026-09-03, loaded review rounds 5–8)

Four more rounds against fresh glass: `[+ cam]` ink unified with its siblings
(two rounds of the eye flagging the dim variant is the law — the save/recall
distinction lives in the label, color carries only affordance); title row and
stage strip inset 30px, derived from the strip's own vertical inset, not
invented; the no-clock timeline hint moved below the bar (lh > bar_h — the
in-bar label overlapped the line under it) and merged into one line; the
right-dock scene header shortened to fit the dock's ~34 columns; and the D7
dope sheet now waits for a clock — persisted keys produced a floating
UNKEYED row overlapping the no-clock hint (an instrument with no time axis).
The protocol doc (`docs/THE_DYAD_PROTOCOL.md`) gained the leading-question
law after r7: a primed report is contamination. Round 8 verdict: "layout is
clean" — all three checks pass.

### The bottom bands learn to be panels (2026-09-03, loaded review rounds 2–4)

The dyad walked the fix chain against each glass capture: the TIMELINE's no-
clock branch was one amber line of void → an instrument scaffold (baseline +
ticks) inside the scrub rect, brighter outline; then both bottom bands got the
blue container line the docks always had — "a panel is a thing on screen" was
never applied to R[3]/R[4], which was the perceptual root of the original
defect 2; then the empty REEL tray drew 6 of 12 slots next to a header that
counts to 12 — the eye caught the lie, so the tray now draws ALL REEL_MAX
slots, sized to fill the band exactly (slot 0 promoted, amber). Round-4
verdict: "slots 0–11 stretch edge-to-edge… none [remaining] that reads as
broken/placeholder." Shipped to the operator's window in Release `963da89e…`.

### The right dock's no-selection view (2026-09-03, the loaded review)

The dyad's second review (creature loaded, `Saved/dyad/2026-09-03_loaded_review`)
re-scored its six empty-viewport defects: 1/5/6 fixed, 2/3/4 open, and named the
right dock's ~77% void the worst one — measured: 13 text bands ending at y=325
of a panel running to y=1416. Fix: when no atom is selected, the STATUS view now
also renders the live scene rows the engine composes every frame for `/scene`
(state chip + label + detail, view-only — toggles remain SCENE-mode's alone).
One formatting site holds: the drawn rows are the `/scene` rows, not a copy.
Verified: Debug build/link; drawn bands 13→25, deepest y 325→1431; rows equal
`GET /scene` on 8092; the dyad's read: "Filled… No longer a few lines then
void." The left dock is now the under-filled panel — the eye's next item.

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

**2026-09-03 TWO LOGS IN THE EDITOR (operator decree).** "One log for the engine and
another for the dyad log, both available in the editor — especially the dyad log so I can
watch the reports it gives." The DOCS browser now has three LIVE pages: **DYAD LOG**
(`Saved/dyad/dyad_log.jsonl` — every senses.py see/watch/hear report, written by the new
`ChimeraEngine/dyad_log.py`: one JSON line per call with requested model, actually-served
model, prompt/image counts, report (capped at 16k chars, true length kept), error, elapsed,
finish reason; failures and dark-eye calls are logged too — a log of only successes is a
lie), **ENGINE LOG** (the F4 session file), and **SESSIONS** (boot/exit record). Live pages
poll at 4 Hz with a TAIL-FOLLOW LAW: the view pins to the newest line until the reader
scrolls up (LIVE/PAUSED chip re-arms); the HTTP twin obeys the same contract — POST scroll
away from bottom detaches, scroll to bottom re-arms. Verified: append→re-read 4→5 lines,
overflow tail-pin, paused-view-stays-put, re-arm, twin parity on 8090.

**2026-09-03 THE SUBJECT IS THE ENGINE'S OWN STATE (the recurring "engine without the
object" defect, killed at the root).** Boot restore is now DEFAULT-ON: every launch replays
`session_snapshot/*.blob` (mesh/hinge/joints/gait/water) through the real API handler ~1.5 s
after boot, then re-fits the camera. `--no-restore` opts out (tests); POST /session
{"op":"clear"} makes emptiness INTENTIONAL (deletes the blobs; a cleared engine stays
cleared). Verified by `tools/subject_restore_test.py` (PASS): bare boot auto-restores the
creature (~2 s), --no-restore stays empty, a corrupt blob fails honestly (mesh_bin:FAIL,
replayed 0) with the engine alive.

**2026-09-03 TWO SILENT JSON CORRUPTIONS, found while testing.** (1) `/state` ended
`json += '}]}'` — a MULTICHAR LITERAL that narrows to one char, eating the closing `]`:
every /state response was malformed JSON since inception, and only head/regex clients never
noticed. (2) MSVC `%.6g` prints non-finite floats as `nan`/`inf` — illegal JSON tokens; the
formatter now emits `null`. `/state` parses fully for the first time. Also fixed:
`/studio_doc`'s path field is now JSON-escaped (Windows abs paths from the log pages broke
full-parse clients).

**2026-09-03 LOG PAGES: five dyad rounds to clean.** The eye reviewed the new log pages
five times (each round: fix -> recapture -> re-judge): (1) missing section boundary,
weak selection, chip reads as badge, tight padding, scratch data in the log -> divider,
selection accent stripe, scratch pruned; (2) boundary still light -> styled section band;
(3) LIVE chip must be a BUTTON (filled, icon, label names the action) -> PAUSE/RESUME
button; (4) icon must agree with label (`||` pause bars / `>` resume triangle, ASCII atlas)
+ log body leaked the eye's own markdown -> the WRITER owns formatting: dyad_log.py now
mirrors every append into a human-readable `Saved/dyad/dyad_log.txt` (markdown-normalized,
flattened, one line per call) and the DYAD page serves THAT — the .jsonl stays the machine
record. Round 5 verdict: **YES — clean plain prose; the dock is finished.** The engine
still renders files verbatim; readability is the writer's job, not the renderer's.

### 2026-09-03 — THE FLOOR AND THE SHADOW THAT FINALLY LANDS (render lane, 5 fixes + 1 law)
**Membrane (Rule 0):** a light ground plane (55/255) under the contact shadow gives it a receivable
surface (delta ~21/255 > perception) without changing the key or the creature's shading. **PASS —
measured, then judged by the eye (GSQ RCO, 17.2s): "long, sharply defined shadow... soles sit
directly on the plane, no gap. VERDICT: GROUNDED."**
The path there killed five distinct defects, each earning the next measurement:
1. **Buffer gate** — floor_vbuf_ creation was gated on floor_pipeline_ != NULL, but the pipeline is
   created LATER in the same function → the buffer never existed and the draw guard silently
   skipped the quad forever. Gate on the buffer alone.
2. **Measurement discipline** — turntable cameras swing below the plane ("sky" read 55 = the
   floor's underside) and dock panels pollute /glass bands; pin the camera, stop the show, sample
   the viewport rows of /frame, classify by luminance bucket.
3. **Depth coexistence** — shadow and floor rasterize the SAME plane: fragment depth is equal only
   up to float ulps. LESS discarded every fragment; LESS_OR_EQUAL still discarded the farther
   half. The decal draws between floor and mesh → depthTest OFF, write OFF (mesh still wins by
   draw order + its own test).
4. **Closed-silhouette law** — the projected mesh is closed: interior pixels catch >=2 layers,
   composing 1-(1-a)^2 ~ 0.62 at a=0.38 (floor 55 -> shadow 21, stacks to 8). The dyad's
   "detached shadow" was this perception bar all along.
5. **Fragment UBO untrustworthy on this pipeline** — fingerprint probes: the alpha arrived as
   55/255 (~a view-matrix element) while the VERTEX stage reads the same buffer correctly. The
   alpha is an authored perceptual decree, not a measurement → it lives in the shader.
Final histogram (floor region): 55 x66.8k, 21 x10.3k, 8 x5.5k, deep-stack x6.5k — clean buckets,
no garbage. Isolation-test discipline (red quad / magenta blob / RGB fingerprints) carried every
step; both isolation shaders are back to production ink.

### 2026-09-03 (cont.) — THE HEIGHT-DERIVED PENUMBRA (membrane B, PASS)
**Membrane (Rule 0):** shadow opacity falling with the occluder's height above the floor reads more
grounded than uniform ink — real penumbrae widen with occluder-receiver distance, contact stays
darkest. **Prediction:** foot-contact darker than the spread silhouette; eye keeps GROUNDED and
reads the shadow as more natural. **Falsifier:** contact lightens / wash detaches / verdict drops.
**RESULT: PASS** — measured AND judged.
- **H0 derived, not chosen:** alpha halves at half the mesh's own y-extent, measured at load
  (g_mesh_ymin/ymax join g_mesh_sphere's bounds loop); A0 stays the decreed 0.38.
- **Alpha computed in the VERTEX stage** (whose UBO reads are the measured-trustworthy ones) and
  interpolated to the fragment as a varying — the fragment stage now reads NO UBO on this pipeline
  at all (the fingerprint-probe defect is structurally avoided, not patched).
- Measured: identical shadow footprint (22,314 px), redistributed — spread 30-35 (was 18-23),
  mid-fall 18-23, contact zone 0-11 (feet keep the tight dark contact). Floor untouched (55).
- The eye (GSQ RCO, 21.6s) independently discovered the compositing law: "overlapping regions
  where two projected parts cross and darken again, which only happens with a semi-transparent
  falloff... soft penumbra-like gradient rather than a crisp cut-out. VERDICT: GROUNDED."
- Housekeeping: CMake COMMENT printed the bare stem for stage shaders (log-only lie; outputs were
  always correct .vert.spv/.frag.spv pairs with a collision guard) — fixed; stale bare-stem
  render_tri_shadow.spv flushed.
- FPS falsifier (floor+shadow, membrane A closeout): 299.4 fps / 0.37 ms avg — NOT OBSERVED.
  Grid confirmed UNREGRESSED: it is a UI-space overlay drawn by the dock, not world geometry.

- 2026-09-03 — THE LIGHT IS ONE FACT (membrane, SHIPPED `c3458fd5`-lineage). The key light was
  hardcoded TWICE (render_tri.frag shading + render_tri_shadow.vert projection) — a duplicated
  fact waiting to drift. Now one Studio-owned vector: UBO -> VERTEX stages only (frag reads it
  via varying), /light HTTP twin (GET readback, POST normalizes), persisted in studio_state.txt
  (light_x/y/z), survives restart. Measured: coupled steering PASS (key right -> shadow centroid
  +618 px; key left -> -140 px); persistence PASS; default reproduces the historical look
  (normalized 0.3563, 0.8144, 0.4581); FPS falsifier NOT OBSERVED (299.7 fps, present-capped).
- THE ALIGNMENT TRAP, CLASS-KILLED: the first C++ pad sat AFTER light_dir[3] (offset 148) while
  std140 starts a vec4 at 160 — L read as (0,0,0), normalize() = NaN, clamp(NaN) = 0: body
  ambient-only-dark (L~36), shadow dead. Fix: pad BEFORE the vector (148..159), light_dir at 160,
  light_tail to 176. static_assert(sizeof(ubo)==176) now refuses any future drift at compile time.
- THE EYE'S ROUND (qwen3.8-27b-gsq-rco, finish=stop, non-leading prompt): "VERDICT: GROUNDED";
  tight foot contact patches + graded penumbra confirmed. Its "not ONE coherent key" is the
  standing three-point decree (key+fill+hemisphere, 2026-09-03) doing its job — the single-source
  look is what left flanks near-black. OPEN ITEM from its list: dotted/jagged normal seam at the
  neck base (smooth-normal leak) — queued for a smoothing membrane.

- 2026-09-03 — THE SPECKLE INQUEST (the eye's neck-dots finding, three hypotheses MEASURED):
  (1) NaN normals — FALSIFIED: a load-gate normal repair (non-finite/non-unit -> area-weighted
  adjacent-face sum) found ZERO bad verts; frames bit-identical. Gate KEPT: the class is now
  dead for every future mesh.
  (2) Exactly-zero-area tris — FALSIFIED as the dot source, and EVICTED anyway: the birth mesh
  carried 206 collinear triangles (36630 -> 36424 on the /scene row); frame bit-identical.
  Eviction KEPT: they cost raster work and are a measured flicker class at other angles.
  (3) VERDICT: the dots are SUB-PIXEL SLIVERS at the tessellation creases (504 tris with area
  < 1e-4, ~0.01px wide at the operator's framing) — real geometry of the surface folds
  (shoulders/wrists/groin, exactly the eye's artifact map). No renderer defect.
  OPEN (queued, needs its own membrane): MSAA 4x kills the whole aliasing class (dots AND
  shadow-edge jaggies); the mesher's crease tessellation is the root-cause cure. The eye rates
  the speckle FAINT — "you have to look closely / zoom to register it".

- 2026-09-03 — MSAA 4x ON THE SCENE PASS (membrane, SHIPPED). Architecture discovered, not
  assumed: ALL 3D content renders into ONE offscreen pass (rt_render_pass_ -> rt_image_), the
  live render pass is dead code (its only rpb.framebuffer reference is rt_framebuffer_), and
  the swapchain receives a blit. So one resolve point serves every consumer — /frame capture,
  the present blit, the pixel-clean background clear — all untouched, all automatically AA'd.
  Mechanics: rt_samples_ queried (limits.framebufferColor/DepthSampleCounts, 1x fallback),
  rt_msaa_image_ (4x canvas, attachment 2, STORE=DONT_CARE), rt_image_ becomes the 1x RESOLVE
  (validation law: resolves are always 1x — first build inverted the roles and the layers
  caught it: resolve=4x rejected, framebuffer mismatch, clearValueCount 2<3, device lost),
  clear array 3 deep, rt depth 4x, all five pipelines' rasterizationSamples = rt_samples_
  (single source: pass compatibility can never drift), create_offscreen recreate-safe on
  resize. UI pass untouched; splat pipeline_ (unused but pass-compatible) flipped too.
- MEASURED: 4x active by pixel fingerprint (intermediate-value silhouette-edge pixels 7 -> 110;
  1x hard steps give ~0), framing matched A/B (bbox x995-1590 y189-1197 identical, body 51697
  px, shadow 68201 px), floor law intact (p50 55), /light steering spot-check ok, validation
  clean on the shipped binary. FPS: launch-transient 4.64 ms during restore+measurement storm;
  steady state present-capped 299.4 fps / 0.39 ms. The EYE (gsq-rco, non-leading): shadow edge
  "clearly smoother... consistent with 4x doing its job", creases correctly unchanged (mesh
  seams, not aliasing), NO new artifacts. VERDICT: IMPROVED. Neck speckle persists (faint) —
  confirmed NOT aliasing; its cure stays queued at the mesher (crease tessellation).

## 2026-09-03 — The sliver inquest closes: the dots were never triangles (membrane FALSIFIED honestly)
- STATEMENT tested: crease speckles are sub-pixel sliver triangles; collapsing width<1/4px
  tris (sub-sample by MSAA physics) at the load gate erases the dots.
- THREE hypotheses killed by identical-framing A/B (monkey_full recall, clock stopped,
  warm-spike detector, 3px clusters): edge<=1px collapse (18 tris, A/B identical), width
  metric ground truth (mesher emits a CONTINUUM: 170<0.14px, 460<0.36px, 2945<1px wide),
  width<1/4px collapse (268 tris, body 123161->123163 px, spikes 18->20 — noise).
- The detector itself was twice wrong and twice corrected (neutral-color filter missed
  warm body dots; "fit" framing landed the camera INSIDE the mesh — backfaces culled,
  floor+shadow only; operator bookmark monkey_full is the standing framing).
- THE ANSWER: the two stable "dots" are the AA signature of diagonal lit rim edges —
  correct 4x behavior, not defects. The EYE's DEFECTS verdict named the real class:
  "dark/bright mottling along the fold" = COINCIDENT SKIN LAYERS z-fighting at creases
  (deterministic: two-frame flip test = 0 — constant MVP picks the same winner; shimmer
  appears only on the turntable). Owner: the skin-wrap generator, not the renderer.
- KEPT (zero-cost physics guards, measured no-op on this mesh): normal hygiene gate,
  zero-area eviction (206), width<1/4px sub-sample collapse (268 here). Any future mesh
  with real degeneracy dies at load with three log lines. FPS falsifier: NOT OBSERVED
  (299.3 present-capped). QUEUED at the mesher: crease skin-layer separation (root cure).

## 2026-09-03 — Backface culling on the tri lane + the mottling inquest (measured)
- AUDIT: birth mesh winding is PERFECTLY consistent (every directed edge exactly once —
  the manifold law; signed volume +13.8; 0 non-manifold edges) — the old splat-era comment
  "winding kept unordered by intent" was falsified. 882 near-coincident OPPOSITE-facing
  pairs (<5e-4 wu) found at creases: the z-fight fuel; both layers rasterized because the
  tri pipeline ran CULL_MODE_NONE with a positive-Y viewport.
- CURE 1: CULL_MODE_BACK_BIT on the tri pipeline (one line, frontFace CCW held). MEASURED:
  body renders right-side-out (bbox identical, 123,331 warm px), mottling speckle 766->726
  px, all back-face bright pins dead. FPS falsifier: not observed (299 / 0.37 ms).
- CLASSIFIER: light-flip test (key left vs right, camera fixed) — crease speckle overlap
  only 15%, mass moves WITH the light: LIGHT-LOCKED shading noise, not depth fighting.
  Corollary: backface culling cannot kill the bulk; it lives in the folded-layer geometry.
- CURE 2 (guard): load-gate normal deviancy repair — stored normal opposing its own
  winding-consistent face average (dot<0) is rebuilt as that average. On THIS mesh: 0
  deviant, frames bit-identical (measured no-op; stored normals already sane). Kept: future
  meshes with scrambled normals self-heal at load. Normal side == cull side by construction.
- THE EYE (gsq-rco, non-leading SHIP/HOLD): silhouette clean, shadow correct, "acceptable
  low-poly clay shading"; HOLD on: neck speckle ring (mesher-side, standing item), HOT FOOT
  HIGHLIGHTS (up-facing normals saturating under key+fill+hemisphere), flat shadow flank.
  QUEUED: foot-highlight clamp membrane; crease skin-layer separation at the mesher.

## 2026-09-03 — The editor speaks human + the eye's verdict lives in the bar (operator decree)
- THE COMPLAINT: "B0 to B-10 — what the fuck is that supposed to mean"; the dyad's reports
  were buried in the DOCS picker. Both communication failures fixed at the root.
- STRIP: stage NAME now renders first in full brightness, the code (B3) demoted to a dim
  suffix; every stage pointer reads "NAME (CODE)" (bottom bar included). The EYE (gsq-rco)
  transcribed "ARTICULATE (B7)" — read correctly, measured.
- THE BAR: newest dyad verdict is a PERMANENT line in the status bar, every mode, no picker:
  "T19:07:28  EYE: HOLD" — amber for HOLD/DEFECTS, green for SHIP/CLEAN/PASS/GROUNDED/
  IMPROVED. Click jumps straight to the DYAD LOG page (full history). 1 Hz mtime poll,
  degrades before overlapping the legend. The EYE (gsq-rco, transcription probe):
  "T19:07:2 EYE: HOLD ... cleanly separated ... SEEN: yes".
- ROOT CAUSE (why the bar was silent): dyad_log.py's human twin truncated reports at 220
  chars — the VERDICT token lives at the END, amputated exactly where it mattered. Fixed in
  the WRITER (every human line now ends "| VERDICT: X" extracted from the full report) and
  the mirror was backfilled from the authoritative .jsonl (18 lines).
- FPS falsifier: not observed. Show restored playing.

## 2026-09-03 — THE BAR WAS OFF THE OPERATOR'S SCREEN (root cause of "I don't see it")
- The engine window's outer frame is 16px wider / ~39px taller than its 1440px client;
  CW_USEDEFAULT placed that excess OFF THE BOTTOM of the 1440 monitor. The status bar —
  the eye's verdict line — rendered below the physical display on every boot. /glass
  captures read the swapchain, not the monitor, so every verification "passed" while the
  operator saw nothing. Lesson: a UI instrument is verified against the WINDOW RECT, not
  the framebuffer.
- FIX (create_window): when the outer frame is taller than the monitor's work area, the
  window is placed FLUSH — client bottom == work-area bottom (measured: (0,-87)-(2576,1392);
  1392 == 1440 taskbar-adjusted work bottom). Title bar hangs off the top by design:
  content beats chrome. Durable: every boot, any launch path.

## 2026-09-03 — Energy conservation clamp on the creature shader (the hot-feet membrane)
- DERIVATION: amb+key+fill reaches ~1.38x albedo for up-facing normals under the key —
  more out than in; a diffuse surface cannot do that. The albedo is the physical cap.
- FIX: fragColor = albedo * min(amb+key+fill, 1.0). MEASURED at identical framing
  (runA baseline): 4,475 hottest px toned (meanL 158->143, max 181->153), rest of the
  body untouched, saturation now impossible at ANY turntable angle. FPS 296/0.37ms.
- THE EYE (gsq-rco): highlights "improved at best," feet still read hot when swung into
  the key — residual is the ALBEDO going flat (physically correct for a directional key
  on untextured clay; form detail there = normals/textures, a content-layer feature),
  plus the standing neck-seam item (mesher-owned). Renderer-side defect class CLOSED;
  the eye's remaining list is the mesher's crease cure + material work.

## 2026-09-03 — The cyclorama: the floor becomes a studio sweep (two drafts, the eye directs)
- THE EYE TWICE: "back plane falls off flat... silhouette edge muddy." DERIVED: a real
  sweep darkens with distance; the fade radius is the mesh's own measured extent
  (ubo.uMeshR = g_mesh_sphere, slots into the unused UBO tail — 176 B layout intact,
  static_assert still guards), computed in floor.vert (vertex UBO reads only), fading
  from 55 at the subject outward. Inner zone untouched: the ink law (55 -> 21) is
  measured where the eye looks.
- DRAFT 1 (outer 18 @ 3R): MEASURED HOLD — the eye: separation won, but "overcooked,
  black void, cast shadow reads as a second object." Applied its prescription verbatim.
- DRAFT 2 (outer 32 @ 5R, eased): MEASURED — floor@55 inner zone intact (31,354 px),
  outer pool at 28-36 (2.10M px), horizon glow survives, body untouched (122,796 px),
  FPS 296/0.37ms. DYAD VERDICT PENDING: the eye's endpoint returned 400 on every image
  request (minimal prompt too) at 20:5x — server-side; pixel verdicts carried the ship.
- VERDICT (eye recovered, gsq-rco): "separates cleanly... nothing floats... darkening
  right — subtle rather than dramatic... VERDICT: SHIP." Minor notes: faint straight
  horizon seam (quad edge vs sky) + the standing neck pixel. Seam cure queued.
- SEAM CURE: floor quad R 60->300 (same two triangles) — the edge sits beyond every
  framing the fit can produce. MEASURED: zero strong horizontal transitions in the upper
  frame (was the seam), floor@55 31,361 px, pool intact, body 122,808 px, show playing.

## 2026-09-03 — D7-POSE: keys become POSES, not just timestamps (the release's editor win)
- A key now captures the WHOLE pose at save (every joint's theta from j_state_map_ stride-8
  +7) and recall restores it through the render thread (pose_pending_/pose_applied_ — the
  intents pattern; all thetas swap at once, no joint-at-a-time flicker; owner -> EDIT).
- PERSISTENCE: ".keys <n> <radians...>" record per key, backward compatible (old lines
  load unchanged; keys saved without a pack keep the old format). MEASURED round-trip:
  the record survives load->persist byte-exact.
- MEASURED gates: save with no pack = graceful degradation (old-format line); recall with
  a size-mismatched pose = rejected ("posed":false), scrub still applies — no garbage
  blending, ever. The live apply path rides the same j_state_map_ write the joints editor
  verifies (harness falsifier A: set==reported).
- HONEST LIMIT: the end-to-end live-pose apply needs a mesh+pack pair in one session; the
  birth mesh's pack pairing is a mesher-side task (queued). The write path, the gates, and
  the persistence are verified; the flicker-free swap is the render thread's own pattern.

## 2026-09-03 — RELEASE READINESS: the engine now boots from any directory
- BLOCKER: every shader path was CWD-relative — launching from anywhere but build/Release
  died at pipeline creation (the 2026-09-03 morning diagnosis, now fixed at the root).
- FIX (main): if shaders/render.vert.spv is not in the CWD, adopt the exe's directory —
  the game-ship layout (shaders ride beside the binary). Dev runs from build/Release are
  a measured no-op (the guard short-circuits). MEASURED: launched with CWD = repo root —
  mesh auto-restored (36,424 tris), 296 fps / 0.36 ms.
- THE SHIP FOLDER: build/Release = chimera_engine.exe + shaders/ (26 spv, 385 KB).
  The state files (camera bookmarks, keymarks, studio state) are created beside the exe
  on first boot — the folder is self-contained.

## 2026-09-03 (late) — THE RIG FITS THE MESH: the canonical-frame refit

**The defect chain, all measured:** the old joints pack was built offline against a
vertex ordering that is not the engine's (npz/GLB ≠ `mesh_cpu_` order). Consequences:
8 of 19 joints shipped with EMPTY vertex bands (their rotations moved nothing),
`elbow_R`'s center floated off the creature entirely (0 body verts within 0.3 wu),
and the R-side ROMs were folded from those off-frame anchors. The engine's joints
lane itself could not load on a clean boot at all (`load_joints` demanded
`hinge_rest_`, a set_hinge artifact; gate counted against `hinge_wL_.size()`).

**Three fixes shipped:**
1. **Engine:** `load_joints` stands alone — rest = the mesh (`mesh_cpu_`), count law
   = `tri_vfloats_/9`, and the Rest SSBO (binding 0) is claimed from the mesh when no
   hinge exists. Clean boots now load the rig; theta=0 dispatch measured a no-op
   (342 px = noise floor); FPS untouched.
2. **The refit (`tools/rig_factory_fit.py`):** reads the CANONICAL frame
   (`session_snapshot/mesh_bin.blob`, the engine's own vertex order), medoid-snaps
   13 measured L landmarks onto vertex patches, builds every R limb by THE MIRROR
   LAW (x-negation, never fitted), assigns every vertex to its nearest bone segment
   with OWNERSHIP SHELLS (limbs capped at 0.7 wu reach; belly flank belongs to the
   torso), blended weights d2/(d1+d2). Result: all 19 bands non-empty (min 58),
   0 unassigned verts, exact L/R band parity (318/318 elbows, 172/172 knees),
   jaw owns its 150 face verts. MJCF primate template emitted for the B6 referee
   (`.tmp/skeleton/chimera_primate.xml`); asymmetric R ROM stops RETIRED with a
   referee note (`factory_rom_r2.json`) — re-measurable on the fitted frame.
3. **The gate (`tools/rig_gate.py`):** six hard checks — full assignment, no empty
   bands, on-mesh centers (eps 0.3), mirror law (tol 0.05), segment parity (2%),
   limb zigzag < 90 deg (axial exempt — a primate neck IS oblique; axial links
   >= 0.2 wu instead). It PASSes the refit and CONVICTS the old pack (empty jaw
   band) — the gate earns its keep against its own history.

**Live verification:** POST accepted; knee_L theta=45 moved 2,219 px (lower body
bbox), elbow_L theta=60 moved 2,411 px (arm bbox), neck theta=30 moved 12,317 px
(head+torso) — every joint class deforms with spatially correct reach.
Boot snapshot carries the refit pack (blob elbow_R = 1.7766, 4.9094, −0.0935).

**The eye's verdict on the new frame:** neck/arm dots on-surface, pose
mirror-symmetric. Three flags raised, three dispositioned by measurement: the
"loop on the back" is the shoulder girdle (FK table anatomy); the "central dot
between the thighs" is tail_base, measured ON the mesh; "pink lines" NOT OBSERVED
(0 pink px — amber UI accents misread). Operator confirmed the elbow repair
visually before the refit; the refit generalizes it to the whole skeleton.

**Queued:** re-measure paired ROM bone stops on the fitted frame (B5 referee,
round 2); gait development against the symmetric frame in the mujoco-warp lab.

## 2026-09-03 (night) — B5 REFEREE ROUND 2: derived axes + measured symmetric stops

**The referee convicted the round-1 axes.** Measured: the elbow's stored hinge
axis was 27 deg from PARALLEL to its own parent bone — a cone sweep that can
never fold (which is why the first referee draft found "no contact anywhere").
**The derivation that replaces it:** a hinge axis is not a free parameter — it
is the NORMAL of the plane containing the bones the joint connects,
n = (J - parent) x (child - J). Verified live: every limb hinge now sits at
exactly 90.0 deg to both its parent and child bone. And since R bones are
x-negations of L bones, (-u) x (-v) = u x v — **L and R share the identical
axis vector; the mirror law for axes falls out of the cross product itself.**

**Two more laws the referee forced:**
- Central joints (spine/neck/tail/jaw) ride the mirror axis (x := 0). The
  medoid snaps had drifted off-axis (up to 0.20 wu — the mesh itself is
  asymmetric), which broke the mirror conjugation for every limb hung off
  the spine. With centers on-axis and derived axes, the conjugation identity
  R(+t) = mirror(L(+t)) holds to 0.0e+00 wu on all six pairs.
- Wrist/ankle axes derive from the mesh-measured hand/foot tips (distal
  links end at tips, not joints).

**Bone-stop semantics (corrected twice, honestly):** skin-fold measurement
measures skin self-contact, not ROM — retired. Bone-stop measurement needs
capsule semantics: bones are THICK (radius 0.05), contact = sampled probe
interior within 0.10 of a static segment, pivot zone (0.15) excluded (that
contact is the joint; ligaments live there). Three failed drafts are in the
transcript: clamp-erased contact, grandchild self-touch at 2 deg, pivot
filter that also erased the knee's real stop. The diagnostic scans that
convicted each are recorded above.

**Measured stops (symmetric by law, L/R equal within 0 deg):**
elbow flex 130/130 -> ship +125; hip flex 120/120 -> ship +115;
knee flex 114/114 -> ship +109. Shoulder/wrist/ankle: no separable bone
stop exists in a stick skeleton (near-collinear capsules, ligament-limited
DOF) — pack ROMs kept, recorded as anatomy findings, not failures.
**Live:** POST accepted; both elbows clamp at exactly 125.000, 28,415 px
deform; both knees at 109, 17,037 px deform.

**The eye's verdict at full flexion: DEFECTS — and it is the next membrane.**
Both arms bend symmetrically, but the SKIN tears at the elbow crease at 125
deg: single-bone partial-rotation skinning (one (joint,w) pair per vertex,
rotate theta*w about the owner) makes adjacent verts rotate 112 vs 62 deg at
extreme angles. The cure is 2-bone linear-blend skinning (LBS): crease verts
transform under joint AND parent, blended. Engine kernel + pack format (JNT2)
arc — queued.

## THE CONTEXT MENU (2026-09-03, the operator's request)

The operator could ADD camera bookmarks all day (+ cam works) but could not
DELETE one — `cam_mark_delete` existed with an HTTP twin and no hand. A quick
right-click is now a CONTEXT MENU.

**The click/drag law.** The right button already pans by dragging; the menu
lives in the split: a right-press with under 4 px of travel at release is a
CLICK and opens the menu; a drag stays pan, byte-for-byte the old math. The
menu is UI-only state (nothing persisted, nothing restored).

**First customers — the D6 bookmark chips:** Recall / Overwrite / Delete.
Delete answers the exact complaint; Overwrite re-saves the live camera under
the chip's name; Recall mirrors the left-click. Activation is press-based
(immediate-mode law), a click elsewhere dismisses, the menu clamps on-screen,
and it draws LAST so it rides above every panel.

**Generic form:** customers register a rect + verb list each frame
(`rctx_`, rebuilt in prepare()); the engine wires one callback
(`cb_ctx_cam_`) through the same store the /cameras twin serves — UI and API
stay one law.

**Verified live (synthetic PostMessage clicks, 2560x1440):** right-click the
`[10 zz_ctx_test]` chip -> menu at cursor -> Delete -> the name left the
store AND camera_bookmarks.txt, neighbors untouched (controlled two-chip
experiment; an early neighbor loss was proven to be the TEST's stale
coordinates after re-layout, not an engine defect).

**Falsifiers named before the build:** menu opening on a drag (no — drag
short-circuits before menu code); deletion not persisting (no — file
re-read confirms); menu items dead (no — Delete verified end-to-end);
capture stuck after menu use (no — release path unchanged).

**Where the menu grows next:** pose chips (G1) get Recall/Delete; scene rows
get Isolate/Show/Hide; the viewport gets Frame Selected / Fit. The skeleton
is built to take them — register a rect, list verbs, wire the callback.

## JNT2 ELBOW, THE EYE'S VERDICT (2026-09-04, tools/jnt2_dyad_verdict.py)

The membrane's last open falsifier went to the eye: both elbows posed to the
measured 125-degree stop, one frame, briefing + live state + the ask. The
report is Saved/dyad/jnt2_elbow_verdict.md.

- **PRIMARY FALSIFIER PASSES: NO TEAR.** The crease is continuous on the
  visible face of both elbows — the JNT2 blend + envelope weights hold where
  the legacy law tore (62.9x edge stretch -> ~1.6x mean).
- **THE EYE'S OWN FINDING, CONFIRMED BY ARITHMETIC:** the posed forearms read
  as flat splayed blades, not folded limbs. Root cause is NOT the skin — the
  REFEREE'S hinge-axis derivation is degenerate for near-collinear bones: at
  rest the forearm is within ~10 deg of the upper arm (|u x v| = 0.18), so
  n = u x v inherits the rest pose's sideways splay (axis mostly world-z).
  Flexing 125 deg about it swings the forearm 1.40 in x vs 0.29 in z — the
  wing splay IS the true kinematics of that axis. The fix (next arc): when
  |u x v| is degenerate, the fold plane's normal comes from the body's own
  sagittal law (the spine axes, +/-x) — para-sagittal flexion, the primate
  anatomy the mesh already implies. Shared-axis mirror law is preserved
  (x-hat on both sides).
- The eye also read "no editor chrome" — MY capture error, not a UI crash:
  /frame is the viewport-only target; the chrome lives in /glass. Correction
  recorded here so the next verdict request captions its image honestly.
- Durable fix shipped in the factory (rig_factory_fit.py): the B5 referee's
  verdict file is now OVERLAID onto the ROM tables at emit time — the
  envelope-weights re-emit had silently regressed the referee's measured
  stops (elbow 125 -> round-1 60); a missing verdict file is now a loud
  warning, never a silent fall-back.

## THE SAGITTAL AXIS LAW — FLEXION FOLDS NOW (2026-09-04)

The wing-splay cure, shipped and verified end to end.

**The law.** Every paired limb hinge axis := the shared signed sagittal
x-hat, sign per joint from the CLOSING TEST (+theta must swing the distal
bone toward its parent): shoulder/elbow/hip/knee +x, wrist/ankle -x.
Justified by measurement BEFORE shipping (tools/axis_sagittal_probe.py):
every limb bends < 26 deg at rest, so the old n = u x v derivation was
degenerate for the ENTIRE class (alignment with the true plane normal as
low as 0.10); the closing signs agreed old-vs-sagittal on all six (the law
changes the fold PLANE, never the flexion DIRECTION); Rodrigues about x-hat
preserves v.x exactly, so a splay is geometrically impossible. Shared-axis
mirror law survives (x-hat is invariant under the y/z-negation mirror).

**Referee round 3 on the new axes: ALL CHECKS PASS.** Conjugation exact at
0.00e+00 wu on all six pairs. Re-measured bone stops in the honest
(para-sagittal) fold plane: hip 124/124 -> ship 119, knee 156/156 -> ship
151. The pre-registered falsifier "a stop moved >30 deg" fired on the knee
(114 -> 151) and is adjudicated: the old 114 was the shank sweeping
SIDEWAYS into neighboring geometry (the splay's own artifact); the contact
plane changed, so the stop legitimately re-measured. Ligament-limited pairs
(shoulder/elbow/wrist/ankle) keep pack ROMs; the elbow's working 125 is now
the factory FALLBACK (never again a round-1 placeholder). Gate: PASS, all
seven checks.

**The verification saga — instruments convicted one by one, honestly.**
Round 2 (rear view): splay cured, skin continuous — but the eye read the
posed arm as "straight," which contradicted the projection arithmetic. The
chase: kernel_axis_probe.py (candidate-axis bbox discriminator: NO candidate
matched, because) the selection gizmo was contaminating the diff; cleared,
the clean diff showed two disjoint clusters — the band's vacated silhouette
(top) and the hand's vacated silhouette (mid), the arrival occluded. The
cyan rig overlay was discovered to draw the REST skeleton (static under
posing — never verify a pose against it). The "side-view horizontal band =
twist" interpretation was MY error: on the fitted side camera +x projects
down-screen, so an x-hat fold legitimately leaves a horizontal band
(/project axis-mapping measured: +x down, +y up, +z screen-left). Final
arbitration: the MAGENTA DIFFERENTIAL (changed pixels highlighted) shown to
the eye, which ruled: **FOLD — one coherent vacated limb silhouette, no
twist/smear/explosion signature; skin continuous; no contradiction.**

**Capture-channel discipline (learned the hard way):** /frame = clean
viewport only (no chrome, no rig overlay); /glass = the composited window
(chrome + overlay). Every verdict request captions its channel; the
verdict script's LIVE STATE now reports each elbow's actual state
(rest/posed/at-stop) after it briefly mislabeled theta=0 as "FULL FLEXION."

**Residue (honest):** the folded forearm's destination is occluded from the
front camera — the fold verdict rests on the differential + projection
arithmetic + the eye's differential read; a closeup camera looking down the
fold plane is the ideal final picture. The eye's repeat audits also left a
real editor-defect backlog: timeline footer clip, EYE:DEFECTS orange
semantics, HUD/timeline not following posed joints, strain tint wired to
the march clock instead of live angles, referee chips missing B-numbers,
blank backtick glyph.

## 2026-09-04 — The operator's tags on EVERY joint + THE SIDE LAW (left := up x forward)
- THE OPERATOR CAUGHT A MIRROR BUG BY EYE on the elbow tag: "considering the creature,
  that would be its RIGHT elbow — the side of a thing is its own perspective." The
  factory had stamped _L/_R under the DEFAULT CAMERA's left. Measured, no probe needed:
  tail_mid extends to -z, jaw to +z => forward := +z => anatomical left := up x forward
  = y-hat x z-hat = +x. Every paired joint's tag was on the wrong limb.
- THE SIDE LAW SHIPPED IN THE FACTORY: the six _L anchors' x-signs flipped (SAME measured
  points, renamed to the creature's perspective); the mirror law (J_R := -J_L.x, ...)
  rebuilds the other side as always. Rotation about x-hat acts only in y-z, so the
  sagittal AXIS table and the referee's ROM stops are mirror-INVARIANT — no
  re-derivation; the name order (and D7 key indices) are untouched. Gate: green.
  Live: elbow_L now at Jx=+1.777 (was -1.777), all six pairs flipped.
- PER-JOINT TAGS (the operator's decree: "deploy those tags on everything... a spaceship's
  thrusters as vectors — the labels are going to be important"): every joint now wears
  the chip the selected joint's gizmo had (name + live theta, the approved display).
  Engine::push_joint_tags projects each joint through the frame VP each frame (same
  path as the rig overlay); StudioUI draws pin dot + label — selected = amber (the
  gizmo's own), posed (theta != 0) = green, rest = gray-blue. The viewport is now
  SELF-DESCRIBING: which side is the creature's left is read off the creature itself.
  Off-frame joints get no tag (project_world refuses); no depth test — a tag is an
  instrument, not matter. The pattern generalizes to any labeled mechanism.
- STRAIN TINT, JOINTS LANE (the backlog's fix 4, the substantive one): the tint existed
  only in the hinge lane; the JNT2 lane that actually drives the creature had none.
  joints.comp binding 6 (per-vert strain SSBO, shared with the hinge lane) + bit1
  (same ramp, same +/-10% saturation); Out is now read-write so the tint reads the REST
  colors from its own previous pass (per-frame chrome, never a cumulative stain).
  Engine::compute_strain_joints mirrors the kernel EXACTLY (blend of two FULL rigid
  Rodrigues motions — an earlier composed/angle-scaled draft disagreed with the kernel
  by tens of degrees at 125 deg and flooded the arm with phantom strain; the falsifier
  caught it). Compact domain: assign >= 0. VERDICT: REST tint exactly 0 px (the stale-
  scratch bug class died with the no-early-skip law); FLEX 12,227 warm px localized in
  a 143-px crease band, compression tail 106 px. An OOB read (unsigned (-1)*8 index on
  root-joint parents) crashed the first /strain-on frame — found by arithmetic.
- FIX 1 (timeline footer clip): the dope sheet started at +22 while the info line below
  the bar reaches ~+24 — rows painted over the footer's descenders. Sheet now starts
  BELOW the footer (bar_y + bar_h + 6 + lh + 6).
- FIX 2 (EYE:DEFECTS semantics): DEFECTS is the audit report's noun, not a demand for
  attention — it ships info-cyan; HOLD alone keeps warning-red.
- FIX 3 (HUD/timeline follow the POSED joint): in edit mode the HUD row and the timeline
  footer read "EDIT <joint> theta <live>" from the per-frame joints push; the sweep's
  "joint k/N" form returns with the show. VERIFIED live: hud_rows = ["EDIT elbow_L
  theta +0.00 deg ROM [-145.0 .. 125.0]"] while the show was paused and the elbow owned.
- Operator state restored after verification: selection cleared, show playing.

## SHIPPED — THE MEASURED-STATION RIG (2026-09-04)

The viewport tags' first conviction: the operator read the per-joint chips and
reported neck, jaw, spine_upper/mid/lower, and both ankles "too high" (lower
spine "too high" reading = the whole chain crowded above the shoulder line —
there was no lumbar joint at all: old seeds 7.71/6.86/5.68 vs shoulder 5.89).

**The measurement (tools/station_probe.py)** — stations re-derived from the
mesh's own anatomy, not re-guessed: neck := the skull-base flare (neck-tube
width min 0.52 at y 7.46; head z-extent jump 0.54->1.82 at 7.52 — the old
seed 8.37 was INSIDE the head); jaw := the mouth-valley crease (front-face
x-extent collapse 1.5->0.34 at y 8.26; old 9.05 was near the crown);
spine_upper/mid/lower := withers / girdle midpoint / pelvis (5.89/4.66/3.42 —
the girdles ARE the operator-approved shoulder/hip lines); ankle := the
tarsal break (foot flare ends y 0.35; old 1.17 was mid-shank). CONSEQUENCE,
not a pick: femur 1.51 ≈ tibia 1.57 — the leg segments became equal.

**Two laws had to be amended to accept their own fix:**
1. THE CENTRAL-STATION LAW (factory): central joints no longer medoid-snap.
   The snap drags interior anchors onto the nearest SKIN patch (first refit
   came back snap_d 0.576 — the disease itself). Stations are the authority:
   x=0 (axis law), y/z = measured (z = tail-robust slice median; the plain
   mean was poisoned by the hanging tail). Paired joints keep the medoid —
   on thin limbs skin IS the joint (ankle snap_d 0.076).
2. GATE CHECK 3 (rig_gate.py): "on-mesh centers" was a medoid-era artifact
   that convicted exactly the fix. The promise is class-aware now: paired
   joints skin-pinned (eps 0.3 — limb max d = 0.000, every limb joint is
   exactly a mesh vertex), centrals within 1.0 wu of skin (half-thickness).
   Ray-parity containment was tried and REJECTED this round: 26-28 crossings
   per ray even where the station is geometrically mid-tube — the blob is
   double-walled in places and parity even/odd is meaningless on it. Blob
   topology audit = named future work. (Blob layout settled: 24-B header,
   N*36 verts, then tris — the second header uint32 is NOT the tri count.)

**Verification:** referee ALL PASS (knee stop re-measured 152 on the new
tibia direction; M conjugation exact) -> gate 7/7 PASS -> live POST -> /joints
reports the exact measured stations -> rest strain A/B: 0 changed px
(falsifier clean) -> elbow_L at 90: 9,536 tinted px in a 128-px crease band,
nowhere else (positive control). Operator state restored (show owns, playing).

## SHIPPED — COMPOSED-FK LBS: THE FINGERTIP MEMBRANE (2026-09-04)

The operator's conviction, from the locked frame: bending shoulder/elbow
stretched the rest of the membrane while fingertips stayed frozen — "only the
joint is having any effect on the rest of the membranes."

**Root cause (kernel archaeology, joints.comp):** shipped JNT2 blended two
SINGLE-LEVEL rotations about independent pivots — a vertex saw only its own
joint's arc plus (1-w) of its IMMEDIATE parent's. An ancestor's rotation
reached deep bands only as the (1-w) residue of the one-level blend: hand
verts (w=0.85 to the wrist) inherited ~15% of the elbow's arc and none of
the shoulder's. The rest was stretch. Every rigged character law says a
joint's pose is the COMPOSITION of its FK chain:

    p' = R_own( R_parent( ... R_root( p ) ) )

accumulated root->own as an affine (M, T): R_k = Rodrigues(a_k, th_k),
t_k = J_k - R_k J_k, M <- R_k M, T <- R_k T + t_k. Term 1 = the band joint's
full world frame; term 2 = the same accumulation STOPPING BEFORE the band
joint (the parent's frame; identity when parentless). Ancestor motion is now
SHARED by both blend terms — a vertex inherits 100% of every ancestor's arc
plus its own blended arc. Convexity (the tear cure) is preserved: still a
lerp of two rigid motions of the same rest point. Normals ride the rotation
parts (kk=1). At all-zero thetas every R_k is exactly I — rest bit-identity
by construction. Chains deeper than 8 truncate (named boundary; deepest here
is 4). The CPU strain mirror (compute_strain_joints) was rewritten to the
same composition — v3, after v1 (angle-scaled, the flooded-tint lie) and v2
(single-level, the stretch lie); the mirror and the kernel are ONE law.

**Verification on the operator's locked frame (camera untouched, elbow_L=90
preserved):** shoulder_L 0->60 moves 24,057 px, of which 13,515 (56%) land
inside the hand region (projected wrist +-110 px) — under the old law that
region moved ~15% of the arc and read frozen. Tint at the crease: 17,438 px,
10,630 of them in the crease band (y 600-720), tapering to a 696-px tail —
crease-localized, not flooded. Small-angle control: elbow at 2 deg tints 695
px (the x10 magnifier's floor at the sharpest gradient) — monotone response,
no flood. Rest pose: all thetas zero on boot, identity holds by construction.

## THE MATTER PASS (M1) — the surface becomes matter (2026-09-04)

The operator's diagnosis: "everything is disjointed because nothing is
referenced to anything else." The composed-FK fix made skin FOLLOW bones;
this arc makes the surface RESIST — matter, not paint.

**The pass**: after the joints kernel poses the surface (Work half 0 seeded),
N Jacobi iterations relax every vertex against its mesh-edge rest lengths
(CSR adjacency built at load; strict ping-pong halves — V5 determinism) and
pin the surface to G3's measured ground plane. Bindings 7-10, /matter +
/matter_state are the HTTP twins; the CPU mirror (matter_stats) evaluates
the same law on the readback.

**Three falsifier catches, each a real bug the numbers exposed:**
1. Descriptor alignment (VUID-00328): the CSR's off|nbr|len sub-allocations
   rode on unpadded strides; binding 9's offset 512,008 % 16 = 8 — the write
   was dropped, Work stayed zero. Every CSR stride is 16-padded now.
2. The canonical-frame loss: the joints pack (18,572 verts) and the live
   mesh (18,459) disagreed after a mid-arc restart — the 18,572 frame was
   birth mesh + ~113 runtime vertex splits and died with the process. Honest
   fix: canonical = monkey_birth.bin exactly, pack regenerated (factory →
   referee knee 152/152 flex 136/136 ext, all symmetric; gate 7/7).
3. THE ANTI-RELAX: the shipped factor (L/|d| − 1) was sign-inverted —
   stretched edges pushed apart, error GREW every iteration (1.9% → 5e6%
   worst-edge by iter 32). (1 − L/|d|) = u·(|d|−L) is the relaxation;
   the rest-identity law survives the flip.

**k is TUNED, not derived** (Rule 1's lesson, paid again): the "derived"
k=0.5 diverged; measured optimum k=0.2, 48 iters — at knee 120°/elbow 90°:
worst-edge error 147.1% (pure LBS) → 18.9% (matter); RMS 2.49% → 0.65%.
Frame cost 0.43 → 0.53 ms avg at 300 fps. Live-tunable via /matter {k, iters};
iters=0 is the pure-LBS readback control.
