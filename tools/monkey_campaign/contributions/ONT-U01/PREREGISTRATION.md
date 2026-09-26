# PREREGISTRATION — ONT-U01 controls/motion-profile qualification

Card `ONT-U01` (planning U01, verification profile `controls`, kind **motion**),
attempt `243e4030e63d47059cb2b8eb3fe98082`, agent
`arrival-def19617206b427aa7b8a40d66b59f72`, criteria
`7c54e8356f287c08e694fc7455d64b31e1d0d295a1835d921f8163fa39b2fa62`, scope
`01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Written and frozen BEFORE the controls probe or capture ran (first probe run
timestamp is recorded in the runtime receipt; this file is committed before
any evidence exists). The probe code implements EXACTLY the frozen timeline,
checks and views below; any misprediction is recorded FIRED in
numerical_receipt.prediction_deviations, never smoothed.

## DONE_WHEN being qualified (the ONLY clause)

"Input emits bounded speed/heading commands at the existing 20 Hz boundary,
without state teleportation" — calculation C12: "20 Hz implies a 50 ms command
interval, not an end-to-end latency guarantee"; observation: "Do not require
retraining for a UI remapping". Dependencies ONT-P01, ONT-P03: DONE with
qualified winners (lead-verified publications; see report.md reconciliation).

## RECONCILE (records reused, not duplicated)

U01 is ALREADY IMPLEMENTED and integrated in the play lineage at `8550b634`
("U01 integrated — input mapper on the real CommandRecord v1 seam"; ancestor
of the pinned head). The preserved records-leg evidence, recovered read-only
via `git -C E:/ChimeraWork/monkey-play-20260924 show f30f2224…:<path>` into
this attempt's `reference/` subtree (byte-exact, hashes asserted at probe
import; play worktree left untouched at HEAD `8d16d3c1`):

- `tools/monkey_campaign/product/input_mapper.py`
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` — THE
  QUALIFIED SUBJECT (`subject_sha256` of the capture): the M-U01 mapper.
- `tools/science_funnel/typeb_export/command_record.py`
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` — the
  EXISTING seam: CommandRecord v1 + V1FamilyAdapter projection law.
- `tools/monkey_campaign/product/follow_camera.py`
  `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7` — the
  declared camera referent (engine eye/up laws, 45 deg FOV, obstacle model).
- `tools/monkey_campaign/product/input_mapper_tests.py`
  `95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e` and
  `agents/U01_input/{PREREGISTRATION.md,discovery_note.md,receipts/
  input_mapper_tests_20260924.txt}` (`0aadc3cd…`, `38efdf39…`, `00c73e34…`)
  — the preserved frozen U01 contract and its GREEN falsifier receipt
  (26/26), reused as the records leg.

The MISSING work this card adds is the controls/motion-profile QUALIFICATION:
the frozen probe + trace + camera manifest below (the original U01 records
are headless falsifier receipts with no controls-profile camera evidence).

## SUBJECT (identity pinned before execution)

The REAL pinned `InputMapper` driving the REAL pinned `CommandRecord` v1 seam
(`MockSink` records every seam call; `V1FamilyAdapter` projects every record)
+ the REAL pinned `FollowCamera` over a probe-owned deterministic body-state
referent. Imported byte-exact from `reference/` with hash assertion; probe
owns NO re-implementation of the subject.

## FROZEN RUNTIME PROBE (the ONLY run that produces evidence)

CPU-only; stdlib + Pillow (frame drawing) + ffmpeg (frame packing). One
deterministic headless run: injected integer milliseconds only (never a wall
clock in any asserted path); no window, process, HTTP, GPU or engine. Tick
grid 50 ms (`INTERVAL_MS`), ticks 0..3000 -> 61 rows in `evidence/trace.jsonl`
(tick id, t_ms, events, held keys, emitted records with issued_tick,
cumulative sink call log, mapper call log, body referent state, expiry states,
per-view camera poses with measured occlusion rays).

Frozen timeline (inputs processed before the tick at the same ms):

- t=100 `W` down -> commanded boundaries 100..650; t=300 `A` down (carried
  yaw +OMEGA), t=400 `A` up (steering release: boundary 400 yaw exactly 0.0
  — no heading memory).
- t=500 mouse +30 counts -> boundary 500 yaw = 30*0.002/0.05 = 1.2 rad/s
  (inside the bound, unclamped); t=600 mouse +120 -> boundary 600 raw 4.8
  -> EMITTED clamped to +OMEGA=1.6 (the input-side bound, named in trace).
- t=700 `W` up (on the boundary) -> the mapper's own decay law: boundary 700
  samples the tail with elapsed=0 (full pre-release speed), boundary 750
  carries EXACTLY 0.0 (the deadline clause), silence after.
- t=900 `W` down (re-arm); boundaries 900,950,1000 at V_MAX.
- t=1050 FOCUS LOSS: the DECLARED `mapper.release_all(1050)` hook while `W`
  is held. The same boundary law: boundary 1050 carries the full pre-loss
  speed (elapsed=0), boundary 1100 EXACTLY 0.0, silence from 1150. No stuck
  command.
- t=1200 reconnect `W` down -> fresh grid, boundary 1200 emits the pre-loss
  rate 0.763625; t=1400 `W` up -> boundary 1400 full (elapsed=0), boundary
  1450 EXACTLY 0.0; silence from 1500.
- t=1500..1800 CAMERA-ONLY WINDOW: zero input events of any kind. The camera
  pipeline keeps running (FollowCamera re-solve/writes; the three declared
  view constructions below). Frozen prediction: zero records, zero mapper
  events, body referent delta EXACTLY zero across the window while camera
  writes are observed.
- t=1975 `W` down (a MID-INTERVAL press, between the 1950 and 2000
  boundaries) -> the grid arms at the next boundary: records 2000..2350;
  t=2100 mouse -80 -> boundary 2100 raw -3.2 -> clamped -1.6 (negative
  bound).
- t=2400 `W` up -> boundary 2400 full (elapsed=0), boundary 2450 EXACTLY
  0.0; silence from 2500.
- t=2600 `Shift` down (REGISTERED REFUSAL by name), t=2650 `Space` down
  (REGISTERED REFUSAL by name); ups at 2700/2750. Zero records.
- t=2800 `W` down -> boundaries 2800,2850,2900; t=2950 `W` up AT the boundary
  -> the mapper's own law samples the full demand at 2950 (elapsed=0), and
  EXACTLY 0.0 at 3000 (the last tick). Traced to the end; silence asserted
  in the trailing checks of C3.

Body-state referent (probe-owned, declared, the ONLY mover of the body):
advances by the projected commanded speed under zero-order hold — per
emitted record, heading += yaw_rate*dt_s, x += v*sin(heading)*dt_s,
z += v*cos(heading)*dt_s (heading integration is a REFERENT preview of the
carried yaw demand; the v1 adapter routes yaw NOWHERE — measured in C5 —
and this referent claims no machinery authority). Positions are OUTPUTS of
records; nothing else (camera included) can move the referent.

## FROZEN CHECKS (each is a numbered prediction; measured by the probe)

1. `C1_bounded_no_teleport_fuzz` — 5000 seeded randomized input schedules
   (random.Random seed 20260926; keys W/S/A/D/Shift/Space/X/arrows + mouse
   deltas in [-200,200]; injected clock at 1 ms): every seam call is EXACTLY
   `("emit", CommandRecord)`; every emitted record is finite with
   v_forward in [0.0, 0.763625] and |yaw_rate| <= 1.6; the scripted trace's
   records satisfy the same bounds; the module source contains NONE of the
   14 forbidden markers (pose_apply, hinge_bin, joints_bin, stride_bin,
   gait_bin, urllib, socket, requests, ctypes, subprocess, qpos, keybd_event,
   SetCursorPos, SendInput).
2. `C2_boundary_50ms_exact` — held-key records spaced EXACTLY 50 ms; at most
   ONE record per tick call; a >= 450 ms stall yields exactly ONE record
   (current state, never a replay burst) and the grid re-anchors after it.
3. `C3_release_decay_to_silence` — every release tail: <= 2 records,
   monotone non-increasing, each <= the pre-release speed, landing EXACTLY
   0.0 at or before release+100 ms, then >= 300 ms of zero emission.
4. `C4_focus_loss_no_stuck_command` — after release_all@1050: held set is
   empty at once; the tail lands exactly 0.0 by 1100; the reconnect press
   re-arms a fresh grid at the pre-loss rate; `is_expired` marks a record
   expired strictly after 100 ms of age and not before.
5. `C5_projection_seam_v1` — every emitted record projects through the REAL
   `V1FamilyAdapter` to commanded_target_velocity_x == v_forward (float64
   passthrough), routed_yaw_rate False, actor conditioning empty bytes;
   issued_tick == t_ms*300//1000 for every record; decode_v1 round-trip is
   bit-identical on v1 fields for every sampled record.
6. `C6_no_camera_induced_body_movement` — (a) in the camera-only window:
   zero mapper events, zero records, body delta exactly zero while camera
   writes are observed; (b) every FollowCamera client write is on the single
   declared route with only the 8 camera fields (radius/theta/phi/pan/
   target) — the camera surface cannot carry a body command; (c) at EVERY
   tick the body position equals the exact zero-order-hold integral of the
   records emitted so far (independent recomputation from the sink log;
   max residual 0.0), and per-boundary displacement <= v_max*dt (no jump).
7. `C7_obstruction_declared_target_readable` — the obstructed view's occlusion
   ray is MEASURED blocked (pinned `FC.ray_clear(eye, target, pillar)` False)
   at EVERY sampled tick — the frozen construction aims the camera THROUGH
   the declared pillar (a `FC.Cylinder` at (0.9, 0, 0.75), r 0.30, top 2.0):
   eye = pillar + normalize(pillar - body_anchor)*1.4, target = body anchor,
   so the center ray passes through the pillar axis; the pillar is DRAWN in
   front of the body (declared, never concealed); the required target (the
   drawn player anchor marker: disc, post, heading arrow) stays readable —
   its center projects inside the frame and the marker extends far beyond
   the pillar's angular footprint every tick; close-target distance
   measured in [1.5, 3.0] m every tick.
8. `C8_remap_is_data_no_retraining` — a remapped bindings dict (physical
   I/K/J/L for forward/backward/turn_left/turn_right) emitting the same
   logical schedule produces IDENTICAL record values, type, version, bounds
   and clock; the adapter projection bytes are bit-identical for identical
   records; importing the pinned mapper adds ONLY the seam module to
   sys.modules (no training surface; a UI remap is a data edit).
9. `C9_timing_chain_bound` — the timestamp chain is bound end to end: every
   record carries (t_ms, issued_tick) with issued_tick == t_ms*300//1000;
   press-to-first-record gaps are measured and reported (frozen statement:
   the 50 ms boundary is a command CADENCE, not an end-to-end latency
   guarantee — the mid-interval press at 1975 first emits at the 2000
   boundary, a measured 25 ms gap; on-grid presses emit at the same
   boundary; C12's warning is measured, not just declared).

## FROZEN VISUAL CAPTURE (from the SAME trace; no second run)

One deterministic video `evidence/capture.mp4` (640x360, 183 frames = 3 views
x 61 ticks, 20 fps, ffmpeg libx264 yuv420p bitexact), rendered by
`capture_build.py` from `trace.jsonl` through the three DECLARED profile
views, each a diagnostic+clean pair binding the same trace sha:

- view `normal follow-camera distance` (seconds [0.00,3.05]):
  `sampled_trajectory`, interpolation `recorded_each_tick` — the REAL pinned
  FollowCamera's applied solution per tick (engine eye/up laws, 45 deg
  vertical FOV, engine radius floor at mesh_r 1.0).
- view `obstructed and close-target views` (seconds [3.05,6.10]):
  `sampled_trajectory`, `recorded_each_tick` — the frozen obstructed-close
  construction: eye = pillar + normalize(pillar - body_anchor)*1.4, target
  = body anchor; the center ray passes through the declared pillar (r 0.30
  at (0.9, 0, 0.75)), which is drawn depth-correctly in front; the measured
  occlusion ray is logged per tick in the trace.
- view `repeatable inspection side view` (seconds [6.10,9.15]):
  `fixed_bookmark` — the engine side bookmark (radius 12, theta pi/2,
  phi 0.3, target origin), identical pose all 61 samples (the repeatable
  inspection view).

Diagnostic rows carry the three profile layers with stable tag bindings —
"input/state/tick display" (held keys, state, tick, emitted records,
expiry), "camera target and frustum diagnostics" (target marker, frustum
edge rays, distance-to-target text), "selected creature labels" (the
selected creature tag bound to the player anchor) — plus the scene (ground
grid, player anchor disc + heading arrow, obstruction pillar in the
obstructed view). Clean rows carry the scene only (depth-tested, no
diagnostics). Camera fields per manifest schema: frame
`monkey_session_world_yup_m`, right-handed, metres, quaternion_wxyz_camera_
to_frame, forward +Z / up +Y, near/far 0.1/200, 640x360, aspect 16:9,
perspective 45 deg vertical FOV, samples covering tick_interval [0,60]
exactly. The manifest is validated in-process with the campaign's own
`visual_capture.validate_manifest` + `visual_gate.verify` against
`card_task.json` (the frozen card profile).

HONEST BOUNDARY (declared up front): the pixels are a deterministic CPU
visualization of the recorded headless command-seam trace of the qualified
subject (the mapper and the seam are headless by construction); they are NOT
native engine frames. The integrated native playable-runtime checkpoint stays
with the integration lane. The body referent is probe-owned and declared (the
machinery owns the real plant); the heading integration in the referent is a
declared preview of the carried yaw demand, which the v1 adapter routes
NOWHERE (measured in C5).

## FALSIFIER

Any probe outcome deviating from checks 1-9 fires; a stuck command after
focus loss or release; any record out of bounds; any seam call that is not
emit(CommandRecord); any body movement not exactly accounted for by emitted
records; any camera write carrying a body field; any tick gap inconsistent
with the frozen 50 ms chain; any obstructed-view tick where the occlusion ray
measures clear or the required target is unreadable; any clean view
containing diagnostics; any camera-manifest field disagreeing with the trace
(position, distance, orientation, coverage, bookmark stability); any editing
of the pinned reference sources (hash drift) — fails this qualification and
reopens the card.

## BOUNDS

CPU-only; stdlib + Pillow + ffmpeg on rendered frames; no GPU, no engine
launch, no browser, no network (github.com reads excepted); <= 16 MiB new
output (the video is <= 6 MiB); all writes inside this attempt workspace and
its prepared checkout; E:/PythonChimera and the play worktree read-only;
the ONT-X02 candidate workspace read-only (pattern reference).
