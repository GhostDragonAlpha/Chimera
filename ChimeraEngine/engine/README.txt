# Chimera Engine — the ship folder

A from-scratch C++/Vulkan 3D engine built alongside a creature game. This folder
(`ChimeraEngine/engine/build/Release/`) is the release: the engine and its shaders
are self-contained here.

## Launch

    chimera_engine.exe [port] [genome] [width] [height]

- `port` — the HTTP instrument port (dev default 8090). Every control has an
  HTTP twin; the editor and the API drive the same state.
- Launch from ANY directory: if shaders are not in the working directory the
  engine adopts its own. Double-clicking the exe works.
- The window opens flush to the bottom of your primary monitor (2K decree:
  2560x1440). The title bar may sit above the screen edge on 1440p panels —
  drag with Win+Arrow if you need it.

## What you see

- CENTER — the viewport: the creature on a studio cyclorama, contact shadow,
  antialiased (4x MSAA). The show (turntable) plays by default.
- TOP — the pipeline strip: stage NAME first (the B-code is a dim suffix for
  doc references). Click a stage for its task envelope.
- LEFT — JOINTS editor (sliders + gizmo), DOCS browser (repo docs + LIVE LOGS:
  the dyad log and the engine log), SCENE outliner, POSES library.
- BOTTOM — the status bar: current stage, fps/frame-time histogram, the color
  legend, and THE EYE: the newest verdict from the dyad (the vision model that
  reviews renders), amber for HOLD, green for SHIP. Click it to open the full
  dyad log.
- TIMELINE — play/pause/scrub, KEY button. A key saves the WHOLE pose; the dope
  sheet groups keys by joint; click a diamond to recall (pose + playhead).

## Keyboard / mouse

- F1 — hide/show the editor chrome (pure viewport).
- F4 — engine session log page.
- Camera: orbit with the mouse; camera bookmarks are chips above the timeline
  (`[+ cam]` saves the current view). `/cameras` is the HTTP twin.

## Persistence (created beside the exe, all plain text)

- camera_bookmarks.txt   — saved camera views
- timeline_keymarks.txt  — timeline keys (name, time, optional `.keys` pose record)
- studio_state.txt       — panel layout, visibility, docs page (workspace)
- engine.log / session_*.jsonl — the engine's own session record
- ../Saved/dyad/dyad_log.txt — the dyad's full report history

## HTTP surface (same state the editor drives; GET readback / POST intent)

- /scene /state /studio /studio_chrome /joints /show /cameras /keys /light
- /mesh_bin /joints_bin /hinge_bin /gait_bin /skin_bin /frost_bin — loaders
- /frame /glass — PNG captures (the swapchain's content, what the editor shows)
- /joint {"joint":name,"theta":deg} — pose a joint (clamped to derived ROM)
- /keys {"op":"save"|"recall"|"delete"|"clear","name":X}
- /light {"x":..,"y":..,"z":..} — THE key light: the lit flank and the shadow
  move together, one fact
- /camera_bookmark, /cameras {"op":"save"|"recall","name":X,"v":[8 floats]}

## The dyad (the eye)

When an LM Studio vision model is loaded locally, scans are sent through
ChimeraEngine/senses.py; every report lands in Saved/dyad/dyad_log.jsonl and
the human-readable mirror. The model is auto-followed from the server (or
pinned in Saved/dyad_model.txt). The newest verdict always shows in the status
bar — you never have to hunt for it.

## Build (from the repo root)

    cmake -S ChimeraEngine/engine -B ChimeraEngine/engine/build
    cmake --build ChimeraEngine/engine/build --config Release

Docs that govern the work: docs/THE_ENGINE_STUDIO.md (the ledger), docs/THE_LAW.md,
docs/THE_OPERATING_MANUAL.md.
