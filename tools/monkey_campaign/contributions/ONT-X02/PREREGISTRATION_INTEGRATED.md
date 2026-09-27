# PREREGISTRATION — ONT-X02 INTEGRATED SESSION RUN (lead correction msg-95a3ac7f)

Frozen BEFORE the integrated run. This file freezes the probes, views, pins and
honest boundaries of the source-bound integrated session required by the lead's
CHANGES_REQUIRED at eac8788ca0153f6b626aa7b40fa4e85bf591165f. The prior
PREREGISTRATION.md (headless probe + CPU trace visualization) and its tests stay
frozen, preserved and green; nothing in them is weakened or relabeled.

## Card clause under test (verbatim, unchanged)

done_when: "Player reaches play and can pause/restart/exit without developer
commands; reset is an explicit user action."
verification_profile: recovery (kind motion), checkpoint V08.
falsifier (card): "Changed pose/contact/ownership or stale commands after
restore, leaked owned resources or mismatched camera/state evidence fails."

## WHAT CHANGES (the correction)

The prior head proved the flow LOGIC over test doubles (StrictBootWorld,
StrictTeardownWorld, SessionAnchorProvider, CameraClientDouble) and rendered
that headless trace with PIL. It did NOT run the integrated player application.
This run exercises the REAL application lineage end to end: the native engine
process, the slice server that owns it, the browser page (the player entry
surface), and the X02 SessionFlow bound to the REAL World lifecycle seam —
with real process/socket receipts and REAL screenshots of the running app.

## SOURCE PINS (all read-only extractions via `git show` / `git archive`)

- play repo E:/ChimeraWork/monkey-play-20260924 (live worktree HEAD 8d16d3c1 is
  NEVER written and never checked out):
  - 8550b634ebd7034bb8873eed41d8bdce4d3843d0 — tools/playable_slice/ complete
    (slice_server.py, scene_boot.py, index.html, push_channel.py,
    standing_body.obj/glb, ghost_standing.obj, boot_cache_manifest.json,
    mock_registry.json, launchers) + every dependency the pinned boot needs:
    tools/science_funnel/{ct_skeleton_layer.py, ct_skeleton_triangle.py},
    data/morphosource_ct/{meshes_preview/ (25 bones),
    meshes_body_20260922/body_manifest.json, meshes/manifest.json,
    bone_identification.json}, validation/{standing_pose_20260921/
    {pose.json,standing_pose_core.py}, hip_pivot_proof_20260921/,
    gait_controller_20260918/derived_numbers.json},
    ChimeraEngine/engine/ (the engine's C++/CMake source, 184 files).
  - f30f2224663324e9374b076938c56672febf4082 — the M-X02 session_flow module
    (session_flow.py sha 30e06c04…) + product/input_mapper.py (7a36a45e…),
    already pinned byte-exact in contributions/ONT-X02/reference/ by the prior
    attempts; reused, never redeclared.
- Engine binary: BUILT FOR THIS RUN from the pinned 8550b634 engine source
  (cmake -S ChimeraEngine/engine -B <ws>/build -DCMAKE_BUILD_TYPE=Release;
  cmake --build) inside MY attempt workspace. Its sha256 is recorded in the
  runtime receipt AFTER the build (a build artifact cannot be pre-hashed; the
  prereg freezes the RECIPE and the source pin, not the output hash).
- The live play worktree's missing-on-disk runtime (no tools/playable_slice/,
  no .tmp/slice_build/chimera_engine.exe) is itself a recorded finding (M3).

## THE RUNTIME RECONSTRUCTION (my workspace only)

scratch/run/play/ — the pinned subset above, extracted by pinned blob bytes.
scratch/run/engine/ — chimera_engine.exe + its shaders/ staged beside it (the
  engine loads shaders from its cwd; the exe is passed --engine-exe).
Server is started with --no-browser (automated lane; the R1 launcher's own
automated mode). Playwright headless, channel "chrome" (the operator-sanctioned
headless path; bundled chromium recorded as fallback deviation if chrome fails).
CPU-first: no GPU training; the app's own Vulkan render path runs as shipped.

## SESSION A — the shipped application through the PAGE's own controls

A1 BOOT. Start `python tools/playable_slice/slice_server.py --no-browser
--port <bind-tested free>` from scratch/run/play. Prediction: within 300 s the
server answers /api/health {ok:true, world_booted:true}; /api/status shows
scene_sha256 == bc9033bfc6c54db0220364821ee19028bf2ac6f740dc70f4c1e9be5f02089111
(the pinned standing body), boot_count == 1, and exactly ONE chimera_engine.exe
child process exists (PID recorded). Falsifier: any refused import, missing
binary, wrong scene sha, zero or multiple engine children.

A2 PLAY REACHED (the player surface is live). Headless chrome loads
http://127.0.0.1:<port>/ . Prediction: zero console/page errors; the page's own
status line shows live engine state (ticks advance between reads); the WebGL
canvas presents non-uniform frames; window.__CHIMERA_VIEW is readable. REAL
screenshots: diagnostic = full page (HUD visible); clean = the canvas's own
pixels via the page's draw-path toDataURL (canvas-only). Additional real
camera-path artifact: one /api/frame JPEG fetched through the server's own
passthru (the ENGINE's own rendered frame — this is the app's real camera
path), sha recorded. Falsifier: console errors, frozen canvas, no live ticks,
or any synthetic/PIL frame offered as evidence.

A3 RESTART — explicit user action through the page's own key. Wait until
scene.settled == true; record the BEFORE pinned state (scene_sha256,
start_state_sha256, start_root_y, engine PID, /api/stats). Then page keydown
"r" (index.html:1072 binds R -> POST /api/restart; this is the page's own
restart control — no developer command). Prediction: the old engine PID
TERMINATES and exactly one NEW engine PID exists; boot_count 1 -> 2;
scene_sha256 identical before/after (byte-clean reload through World.boot:
shutdown_engine -> free port -> fresh engine -> wait_engine -> /mesh_import);
after settle, start_state_sha256 recorded again (its equality across boots is
the engine's own determinism claim — if it differs, that difference is
RECORDED AS MEASURED, not tuned). After-screenshots exactly as A2. Falsifier:
the same PID surviving, zero new boots, scene sha drift, or an orphaned engine.

A4 EXIT. Close the server via its own shutdown path (CTRL_BREAK_EVENT ->
KeyboardInterrupt -> the shipped `finally: WORLD.shutdown_engine()`).
Prediction: engine child PID gone within 12 s (terminate -> wait(10 s)), the
server port refuses connections, and NO chimera_engine.exe I started remains.
Falsifier: any surviving engine process or bound port = a leaked owned
resource (the card falsifier fires).

## SESSION B — the X02 SessionFlow bound to the REAL World lifecycle seam

Driver (my workspace): imports the pinned session_flow (f30f2224) and pinned
input_mapper; imports World from the pinned slice_server (8550b634); constructs
the REAL World(engine_exe) and follows the shipped main() boot path
(WORLD.boot()). The flow is constructed EXACTLY as the module's own docstring
prescribes: SessionFlow(mapper, restart_scene=world.boot,
teardown=world.shutdown_engine). Every state change is driven ONLY through the
public mutators key()/tick() — the flow's own no-developer-commands law.
All times are injected integers; the WORLD calls are the real ones.

B1 Return -> PLAYING (key-only start).
B2 While playing: mapper.press("W")/release through flow.key + flow.tick ->
REAL CommandRecords in the sink (the records leg already qualified in the
prior head now runs against the live session).
B3 Escape -> PAUSED: the quiesce release_all runs on the REAL mapper; while
paused, flow.tick emits zero records and the mapper is untouched (suspended
decision clock, now over a live session).
B4 R from paused -> EXACTLY ONE real World.boot: the engine process alive at
B3's end terminates (PID observed gone), a NEW engine PID + port appears,
/mesh_import runs again (scene_sha256 equal), flow returns to PLAYING; total
boots in the session == 2. Falsifier: any second world contact, any other
attribute touched on World (the flow's own declared surface), or a leaked
first engine.
B5 R while playing -> no transition, no boot (boot count unchanged).
B6 Return from paused -> resume to PLAYING, no boot.
B7 Q -> EXITED: teardown EXACTLY ONCE through the REAL World.shutdown_engine
(slice_server.py:174-181 terminate -> wait(10 s) -> kill); the engine PID is
observed dead and its port refuses connections after B7.
B8 After exit: flow.key/flow.tick move nothing; terminal state holds.
B9 Containment across the whole session: at every instant at most ONE engine
process is alive; after B7 there are ZERO; every port the world opened is
closed. Receipt: PID table + TCP connect probes + timings.

## FROZEN VIEWS (captured only in Session A; Session B is process-receipt leg)

- V1 "playing_before_restart": diagnostic full-page + clean canvas-only.
- V2 "playing_after_restart": same pair, same camera bookmark (the page's own
  cam defaults; camera fields read live from window.__CHIMERA_VIEW + the
  page's lookFrom/projection matrix — declared, not guessed).
- Manifest: chimera.visual_capture_manifest.v1 over ONE contact-sheet image
  container (the four real screenshots packed without edits), capture_sha256 =
  the sheet's sha, kind visible_static, per-view state_binding = sha256 of the
  /api/status snapshot taken at capture time. The recovery profile's required
  diagnostic layer names are mapped onto the page's REAL overlay groups;
  layers with no on-screen referent in the standing start are declared MISSING
  in the receipt (never invented). Camera/scene fields the page does not expose
  are recorded as unresolved, not fabricated. visual_acceptance stays false
  (structural validation only); independent visual review is the reviewer's.

## MISSING-INTEGRATION LIST (declared BEFORE the run; confirmed precisely after)

- M1: at the pinned lineage the page/server expose NO pause or exit control:
  slice_server imports neither session_flow nor input_mapper and ships no
  /api/pause or /api/exit route; index.html binds no Escape/Q handler. The
  pause/exit legs of done_when therefore run through the SessionFlow over the
  REAL World seam (Session B), which is the module's declared integration
  contract — the page-level wiring is the unresolved piece, listed as such.
- M2: no locomotion consumer: mapper CommandRecords have no walking/climbing
  consumer in the slice (standing start only). X02's clause does not demand
  them; downstream skills stay out of scope.
- M3: the live play worktree ships neither tools/playable_slice/ nor a built
  engine on disk at HEAD 8d16d3c1; the runtime is reconstructed here from the
  pinned commit's bytes, with every extracted file's sha recorded. The
  reconstruction is read-only w.r.t. the play repo (git show/archive only).

## HONEST BOUNDARIES (frozen)

- The screenshots are real pixels of the real running application (page HUD +
  WebGL canvas + the engine's own /frame JPEG). The prior head's PIL video
  remains labeled exactly what it was: a deterministic visualization of a
  headless trace. Neither is relabeled.
- V08 (native integrated playable runtime/visual checkpoint) evidence IMPROVES
  here (a real engine process really boots/pauses-context/restarts/exits) but
  V08 acceptance remains the lead's call; visual_acceptance is false by
  validator law.
- Any check that FIRES is recorded as fired, with its measured numbers.
- No criteria hash changes. No prior test is deleted or weakened.

## Success criteria for THIS correction

Sessions A and B complete with their predictions recorded pass/fail AS
MEASURED; the before/after pinned state comparison is real (A3/B4); the owned
resource lifecycle is real (PIDs, ports, teardown); the visual evidence is
real; the missing-integration list is confirmed or corrected precisely; all
prior tests still pass; nothing outside my attempt workspace is written.
