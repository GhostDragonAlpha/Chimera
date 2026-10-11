# Round-11 — Phase 1 slice 1: follow camera, pass-1 lighting, ledger guard

## Step 0 partial-state audit
- Found a prior worker's near-complete state: modified engine sources (uncommitted),
  configured+built `.tmp/cam-engine` (exe 15:33), `.tmp/tendon_test_r11.exe`,
  round-11 evidence (3 probe logs + 4 PNGs + probe scripts), `.tmp/scratch-8119/assembly`.
- No process bound any port >= 8119 (nothing to kill; prior scratch engine already dead).
- Shared stack: at audit time :8110, :8210 and :8117 all refused connections
  (curl exit 7 / HTTP 000; netstat shows no listeners). Not started, touched, or
  restarted by me at any point — verified untouched at teardown too.
- Reused: the configured build dir, the scene output dir, and the three probe
  scripts. Re-verified everything myself: rebuild, tests, launch, capture,
  ledger, regression (numbers below are from MY runs, not the dead worker's logs).

## Changed files (all additive + toggle-gated; both toggles default OFF)
- `ChimeraEngine/engine/engine.cpp`
  - :191-197 WndProc edge-triggered 'C' -> toggle_follow_cam, 'V' -> toggle_pass1_lighting.
  - :65-72, :2130-2156 creature root: vertex centroid + height measured in load_mesh
    (the mesh the renderer already uploads); measured here: centroid (0, 5.596, 0.406), height 9.991.
  - :6759-6801 toggle_follow_cam: saves dev orbit (theta/phi/radius), sets
    behind=1.75x height, above=0.80x height via radius=hypot, phi=atan2; restores exactly on OFF.
  - :6803-6875 update_camera_matrices: while ON, orbit target = centroid + sim root
    offset, exponential smoothing k=1-exp(-8*dt) (~8/s); eye/look_at use the smoothed
    target so mouse drag orbits the CREATURE; pan suppressed in follow mode; while OFF
    `cam_target IS g_cam.target` — shipped path byte-identical. ~10 Hz stderr eye/root/delta log.
  - :1704-1726, :1859-1880 pass-1 twin pipelines (tri_skin_pipeline_, floor_skin_pipeline_)
    via specialization constant PASS1=1; failure is non-fatal (keeps shipped shading).
  - :8595-8632 frame(): binds the skin/floor twins ONLY while 'v' is on.
- `ChimeraEngine/engine/engine.hpp` :574-591, :690-698, :1020-1032 — toggle API, atomics,
  follow target, saved dev framing, twin pipeline handles.
- `ChimeraEngine/engine/main.cpp` :4498-4507 — per frame: engine.set_sim_root(0, root_y, 0)
  (fall law is single-Y DOF) + surface a pending ledger violation as one engine log line.
- `ChimeraEngine/engine/membrane_tick.cpp` :855-858 (guard call in step, armed only),
  :1088-1134 ledger_guard_frame_ (per-frame |drain-(work+heat+dE)|<1e-6, stderr summary
  every 300 armed frames, immediate violation print + pending flag), :4791-4796 additive
  /tick_state fields tendon_ledger_max_err_J/_frames/_violations. Physics untouched.
- `ChimeraEngine/engine/shaders/render_tri.frag` :42-62, `floor.frag` :32-51,
  `floor.vert` :31-37 — PASS1 specialization branch: skin albedo (0.72,0.55,0.42) /
  stone ground (0.42,0.42,0.45), one directional key (existing vLightDir UBO varying)
  + flat ambient 0.25. PASS1=0 path unchanged.
- Pre-existing uncommitted changes NOT from this slice (preserved, not mine):
  depth LESS->LESS_OR_EQUAL tie fix (engine.cpp), ui.cpp CHIMERA_GRID_DIAG fprintf removal.

## Toggle behavior
- 'c' OFF->ON: dev framing saved; camera frames creature behind-and-above scaled to
  its measured height; orbit target becomes the smoothed creature root; drag circles
  the creature. ON->OFF: dev theta/phi/radius restored exactly.
- 'v' OFF->ON: fill draws with PASS1=1 skin twin; ground plane draws with PASS1=1 lit
  twin (same light direction as the shipped rig). OFF: shipped pipelines rebound.

## Acceptance
- A PASS: cmake configure + `--build --config Release --parallel 2` clean, exe links, no warnings.
- B PASS: engine on :8119 (`8119 --hidden 1600 900 --no-restore`); creature_scene load
  ok (JNT3_hierarchical, graph b0e30d6c...); /tick_state returns all 10 tendon_* fields
  (+3 additive ledger fields).
- C PASS: engine-native GET /frame + PostMessage WM_KEYDOWN/UP to the scratch window
  (path-pinned to .tmp/cam-engine). 11a vs 11b: 28.6% pixels changed (viewpoint moved:
  stderr FOLLOWCAM eye=(0,13.589,-17.078) root=(0,5.596,0.406) d=19.224 = 1.75h/0.8h law).
  11b vs 11c: 98.4% changed, scene luma 10.4 -> 95.2 (lit ground + skin shading read).
  11a vs 11d (toggles cycled back OFF): mean |dRGB| 0.00, 0.0% changed — default-OFF exact.
- D PASS: armed u=0.6, 759 armed frames (>=600); guard summaries at frames 300/600/900;
  max err 1.055e-12 J (engine counter AND independent HTTP recomputation agree),
  0 violations, < 1e-6 J. Sever ok, disarm ok, counters reset per arm session.
- E PASS: tendon unit tests 5/5 (LEDGER, SEVER, STALL, REST, MONOTONIC; exit 0);
  /tick_pose knee_L 40 unarmed ok:true (name and index 15); reflex arm/belly press
  /tick_touch ok:true, clear ok:true (reflex_cell_count 36630 live; flinch block
  "no_drive_resolution" is the pre-existing kernel state, unchanged). Shell untouched.
- F PASS: scratch engine killed by PID after runs; no process on >=8119 remains;
  :8110/:8210/:8117 never signaled or touched (they were already down at audit — see Qwen note).

## Evidence
- 11_camera_light_report.md (this file), 11a_dev_default.png, 11b_follow_cam.png,
  11c_lighting.png, 11d_toggles_off_restored.png, 11_capture_log.txt,
  11_ledger_guard.txt, 11_ledger_probe.txt, 11_regression.txt, 11_regression_probe.txt,
  scripts _capture_r11.py/_ledger_r11.py/_regress_r11.py; engine logs
  .tmp/scratch-8119/r11b_out.log / r11b_err.log.

## Residual risks / questions for Qwen
1. Shared stack :8110/:8210 (and foreign :8117) were already DOWN at audit; I left them
   untouched per hard rules. If they must be running for review, someone must restart them.
2. Follow-cam "behind" is behind the user's current azimuth (theta untouched at toggle-on);
   confirm that matches the intended game feel.
3. The uncommitted depth LESS_OR_EQUAL tie fix and ui.cpp diag removal predate this slice;
   flagging for Qwen's review ownership, not reverted.
