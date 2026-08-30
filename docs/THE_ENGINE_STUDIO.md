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
