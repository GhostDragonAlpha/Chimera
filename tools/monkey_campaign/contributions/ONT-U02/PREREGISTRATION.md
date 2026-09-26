# PREREGISTRATION — ONT-U02 follow-camera qualification (reconciliation)

Card `ONT-U02` (planning U02, verification profile `controls`, kind **motion**),
attempt `2c724944121f4feb893f671504bbac00`, agent
`arrival-286909b6a5744dd79beb1a4a52c75b78`, criteria
`5fb0dee8d086f9fd638507058063dd7b7c138958ab7433e5f086da2bbc120b83`, scope
`01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Written BEFORE the camera probe or capture ran (the reference recovery and the
open-loop geometry derivation in `scratch/derive_geometry.py` preceded this
file; the probe itself runs only after it is committed). Dependencies ONT-P01
(PR #127, merged 391f0ede) and ONT-P03 (PR #140, merged 736d12cc) are DONE
with qualified winners; this card reuses their frozen contracts (the C23
camera-calculation record and the playable-monkey scope bounds) and changes
nothing they froze.

## RECONCILIATION FIRST (what already exists)

The pinned play lineage ALREADY CONTAINS the implemented U02 camera, its
frozen preregistration with the tested obstruction cases, and its green
receipts. Recovered READ-ONLY via `git -C E:/ChimeraWork/monkey-play-20260924
show f30f2224663324e9374b076938c56672febf4082:<path>` into this attempt's
`reference/` subtree (byte-exact; play worktree untouched at HEAD 8d16d3c1):

| source | sha256 | role |
|---|---|---|
| product/follow_camera.py | `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7` | THE QUALIFIED SUBJECT |
| product/focus_policy.py | `e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0` | focus loss / release surface (exercised) |
| product/state_feedback.py | `74c0aad033eeafef971888809702a0d0f4f387c55ac9690ee5380edc02a189d1` | related pinned lineage (recovered + hash-pinned; NOT imported: its observation needs climb_intent + session_flow, which belong to other lanes) |
| product/input_mapper.py | `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` | walk command seam (exercised) |
| product/follow_camera_tests.py | `4d75164ff6a16bf0d817332b7c5229513750782727ad1a23911025dc93d31b27` | the pinned suite incl. obstruction cases OC1-OC8 (re-run) |
| science_funnel/typeb_export/command_record.py | `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` | the command record v1 seam |

The TESTED OBSTRUCTION CASES the card names are the pinned
`agents/U02_camera/PREREGISTRATION.md` cases **OC1-OC8** (frozen 2026-09-24
with Amendments 1-5) with falsifiers **FA-FG**. This qualification MEASURES
that pinned subject over its cases; it does not reimplement the camera and
does not edit any pinned byte (reference hash drift fails).

## SUBJECT and harness

The REAL pinned `FollowCamera` (d61347f0) is bound twice over ONE shared
deterministic anchor provider: the SUBJECT instance carries the declared
obstacle scene (trunk + pole + low curb below); a BASELINE instance carries
NO obstacles (the clean-scene reference framing — the "normal follow-camera
distance" law). Both write through RecordingClient-wrapped strict engine
doubles whose ONLY write surface is `POST /camera` (8 fields) and whose
`POST /project` echoes the applied camera (FG). The anchor ("body") stream is
HARNESS-OWNED: the REAL pinned `InputMapper` (U01) inside the REAL pinned
`FocusPolicy` (U03) emits CommandRecords; the provider integrates them
(v=0.763625 m/s band ceiling, yaw_rate carried at 1.6 rad/s bound, decay to
exactly 0.0 within 100 ms, then silence). Provider time is INJECTED tick
milliseconds (never a wall clock). Wall-clock latency is measured separately
(pinned C12 law: setpoint vs measured reported separately, FD is a test-level
budget).

Injected geometry (subject constants; derived OPEN-LOOP from the pinned
formulas in `scratch/derive_geometry.py` BEFORE this file): mesh_r=0.5,
provider extent=0.5 -> r_subject=1.0, r_floor=1.0, r_ground=2.534924,
phi_min=0.198546 <= phi_max=0.314159 so phi_ground=0.256353, no low_eye hint;
eye height 0.642741 m, eye back offset 2.452086 m. Obstacles (declared
model, vertical cylinders, y=0 bases):

- TRUNK `(3.4, -5.0)` r=0.5 top=8.0 — designated trunk (largest r*top among
  r>=0.25; Amendment 5 law).
- POLE `(2.0, 0.2)` r=0.3 top=6.0 — trunk-scale obstacle, NOT the trunk.
- CURB `(3.0, 0.1)` r=0.12 top=0.15 — sub-ray boundary curb (OC5 height-aware
  flyover; r<0.25 so never trunk-designated).

## FROZEN TIMELINE (injected ms; tick grid 50 ms = INTERVAL_MS; ticks 0..390)

Start anchor (0,0,0), heading east (yaw pi/2). Camera bind at t=0 (provider
ts 0.0). "press/release/blur/focus" are REAL FocusPolicy calls.

- t=200 press W; records from t=250 at full v (0.763625).
- t=1400 on_blur WHILE WALKING (ax~0.88): release_all as physical releases;
  tail records at 1450 (0.3818) and 1550 (EXACTLY 0.0), then silence; held
  empty from 1400.
- t=1900 press W while blurred -> DROPPED BY NAME (dropped_blurred), zero
  records 1900..2450 (no stuck command).
- t=2500 on_focus; t=2900 press W -> fresh grid, full-v record at 2950, no
  phantom keys (held == ['W']).
- Walk east; the base sight-line crosses the POLE for ax in (1.76, 4.96)
  (derived; ray-blocked, eye-bad only from 3.94): avoidance active while
  ax in that window (measured boundary ±2 ticks of the derived predicate);
  resolution through the frozen order (latch -> pull_in -> steepen ->
  height_radius -> orbit; here pull_in cannot act below its floor and the
  eye stays clear, so the measured order is expected to start at steepen and
  resolve via orbit; the CURB also blocks for ax in (3.0, 3.65) so the first
  clearing orbit step may be +-45 deg rather than +-22.5 — LAWS asserted,
  exact step recorded).
- t=5700 release W (halt ax~3.05 INSIDE the blocked window): decay tail
  5750 (0.3818), 5850 (0.0), silence; the avoidance solution is RETAINED at
  the halt (OC6 retain law; halt pose re-verified clear+framed each tick).
- Idle ~7.3 s..9.5 s: camera settles onto the stopped anchor and WRITES CEASE
  (deadband starvation) — predicted within 1.5 s of the exact-zero record.
- t=9500 press W AND press A (turn_left, +1.6 rad/s): 20 boundaries of arc
  (radius v/omega = 0.477 m), yaw pi/2 -> pi+0.03; camera theta follows the
  heading (ground-mode instant-follow law); avoidance RELEASES mid-arc when
  the base sight-line clears the pole (OC6 release law; base framing restored
  within 1 tick of the first clean tick).
- t=10550 release A; W stays held; leg 2 walks south from ~(3.53, -0.48).
- Trunk mode ENTERS when dist2D(anchor, trunk axis) <= 2.952086
  (= r_ground*cos(phi_ground) + r_trunk; measured entry z ~ -2.05, recorded),
  framing switches to the Amendment 4.2 two-point fit (target = midpoint of
  anchor and the SURFACE contact point; radius = clamp law; theta = derived
  atan2 law). CLOSE-TARGET VIEW.
- t=15450 release W (halt at dist ~0.8 from the trunk axis, z~-4.2): tail
  15500/15600, silence; trunk-mode framing persists at the halt; the anchor
  AND the trunk contact point both stay framed (both subtend < 22.5 deg,
  measured 0.74/0.67 deg in the open-loop derivation).
- Idle to T_END=19500: final settled close-target view, ZERO writes over the
  last 100 ticks.

## PREDICTIONS (numbered frozen checks; each is a LAW with named measured values)

- C1 ground follow law: while walking in ground mode outside obstruction
  windows, the subject's applied command equals the base framing law
  (radius == r_ground, phi == phi_ground, theta == atan2(-hx,hz), target ==
  smoothed anchor, pan 0) to 1e-9; the anchor subtends < 22.5 deg and a
  ground patch 2 m ahead of the anchor along the heading subtends < 22.5 deg
  (MOTION ON GROUND IS VISIBLE); commanded phi <= PHI_MAX_GROUND + 1e-12
  (feet-in-frame law).
- C2 controls + no-stuck: W press -> full-band records within 2 ticks;
  blur@1400 -> held empty immediately, tail <= 2 records each <= pre-loss
  speed with the LAST EXACTLY 0.0 then silence; press while blurred is
  dropped BY NAME; focus + fresh press re-arms a fresh grid at the pre-loss
  rate with no phantom keys.
- C3 settle + write starvation: after the exact-zero record the camera eases
  to the stopped anchor and camera writes CEASE within 1.5 s; zero writes
  over the idle window; the anchor stays framed at the settled pose.
- C4 pole episode (OC1+OC6 live): no avoidance before the first derived
  blocked tick (±2); every non-degraded applied solution in the window ends
  eye-clear by m_cam=0.25, ray-clear by m_ray=0.02, anchor-framed; the
  avoidance order of every avoiding tick is a contiguous prefix of the frozen
  order; the solution is RETAINED at the halt (latch) and RELEASED to exact
  base framing after the turn (first clean tick, |Δ| <= 1e-9 vs the baseline
  camera's command).
- C5 trunk approach (OC3 live): exactly one ground->trunk transition, entry
  when the measured axis distance <= 2.952086 (no chatter, zero exits);
  in trunk mode target == midpoint(anchor, surface contact) and radius ==
  clamp law to 1e-9; BOTH the anchor and the contact point subtend < 22.5 deg
  every trunk tick (MOTION AT TRUNK IS VISIBLE — close target).
- C6 OC4 static no-op: over the final 100 idle ticks zero camera writes on
  both cameras; in the case matrix, a clean scene with a static anchor writes
  at most once and re-commanded poses are bitwise identical (|Δ| <= 1e-9).
- C7 OC5 height-aware flyover: case matrix — the base sight-line horizontally
  crosses the curb footprint (measured with the module's own
  _segment_hits_disk_2d) while ray_clear (height-aware) stays True and the
  command equals the clean-scene base command (no avoidance attributable to
  the sub-ray obstacle); eye height-clear (0.6427 >= 0.15+0.25).
- C8 OC3b honest degradation (case matrix): a static anchor inside the
  optical margin of an unreachable blocker (top=50 m) ends DEGRADED=True with
  the declared reason, recorded by name; the continuous run has ZERO
  degraded ticks and every degradation flag would be visible in trace and
  capture diagnostics.
- C9 OC2/OC7 pull-in (case matrix): a trunk-approach static anchor with a
  trap cylinder at the trunk-mode eye -> order starts pull_in; resolution
  radius R' in [pull_floor, base radius), eye- and ray-clear by margins,
  anchor framed; re-running the case reproduces the identical solution
  (determinism); monotonicity itself is owned by the pinned suite (re-run).
- C10 never moves the animal (OC8, whole run + case matrices): the recorded
  command stream of BOTH cameras contains zero allowlist violations and zero
  forbidden paths; every write is POST /camera with exactly the 8 camera
  fields and pan_x == pan_y == 0.0; the engine doubles expose NO body surface
  (zero undeclared attempts); the anchor stream is harness-injected — camera
  code never writes body state.
- C11 FF smoothness: per tick |Δ smoothed anchor| <= max(0.05, 2*v_animal)*dt
  + 1e-9 absent a declared cut; zero cuts in the run.
- C12 FG apply echo: every engine double applies each POST /camera verbatim;
  verify_apply()'s /project cam echo equals the last commanded v within 1e-3
  on both cameras.
- C13 FD latency budgets (test-level, wall-clock, reported separately):
  compute + command round trip <= 50 ms and mock-deadline presentation
  <= 200 ms per tick on the subject camera.
- C14 FE framing: anchor subtend < 22.5 deg on every non-degraded tick
  (continuous run: every tick), zero degraded ticks; baseline camera writes
  follow the same laws with zero avoidance entries.

Plus the pinned suite: `reference/.../follow_camera_tests.py` re-run 24/24 OK
(reconciliation evidence that the recovered bytes are the qualified ones).

## FROZEN CAPTURE (from the SAME trace; one run, no second run)

One deterministic video `evidence/capture.mp4` (640x360, 20 fps, ffmpeg
libx264 yuv420p bitexact), 3 views x 391 ticks, rendered by the capture
builder from `evidence/trace.jsonl`; manifest
`chimera.visual_capture_manifest.v1` validated in-process with the
campaign's `visual_capture.validate_manifest` + `visual_gate.verify` against
`card_task.json`. Views (each a diagnostic+clean pair, state_binding kind
trace = the trace sha, all cameras perspective 45 deg vertical FOV
(tan_half 0.41421356), near/far 0.1/200, 640x360, aspect 16:9, right-handed
Y-up metres, frame `monkey_u02_world_yup_m`, quaternion wxyz camera->frame,
sampled_trajectory / recorded_each_tick, samples covering tick_interval
[0, 390] exactly):

1. `normal follow-camera distance` — the BASELINE camera's applied solution
   per tick (clean scene; the normal-distance follow framing law;
   motion on ground visible).
2. `obstructed and close-target views` — the SUBJECT camera's applied
   solution per tick (pole avoidance episode, latch retain/release, trunk
   close-target framing).
3. `repeatable inspection side view` — fixed bookmark camera (radius 14,
   theta pi/2, phi 0.3, target (3,0,-2), the pinned engine eye law),
   identical pose all 391 samples; deterministic side view of the whole run.

Diagnostic rows carry exactly the three profile layers ("input/state/tick
display", "camera target and frustum diagnostics", "selected creature
labels") with stable tag bindings; clean rows carry the scene only
(depth-tested, no diagnostics). Required subject `monkey_body` is observed in
every view (drawn every frame).

HONEST BOUNDARY (declared up front): the pixels are a deterministic CPU
visualization of the recorded headless trace of the pinned camera subject
(the module is headless by construction; the engine is consumed only through
its HTTP contract which the doubles stand in for). They are NOT native engine
frames and make no V03/V08 native-rendering claim — the integrated native
checkpoint stays with the integration lane.

## FALSIFIER (card text mapped to this probe)

- "stuck command" -> C2/C3: any held key after blur without a named record,
  any non-zero record after the decay deadline, any camera write after
  settle, any mapper event after silence — FIRES.
- "camera-induced body movement" -> C10: any non-allowlisted route, any
  missing/extra camera field, any non-zero pan, any undeclared engine-double
  attribute attempt, any camera-code write to body state — FIRES.
- "unreadable required target" -> C1/C5/C14: anchor or trunk contact
  subtending >= half-FOV while not degraded, missing `monkey_body` observation
  in any view — FIRES.
- "concealed obstruction" -> C4/C7/C8: avoidance resolving without margin
  clearance, a degraded tick without the flag recorded, a diagnostic view
  without the obstruction visible (pole/curb drawn), clean rows carrying
  diagnostics — FIRES.
- "unbound timing evidence" -> C13 + manifest binding: trace t_ms not
  injected-tick-bound, samples not covering [0,390], latency reported without
  the setpoint/measured separation — FIRES.
A prediction mispicking a measured boundary (not a law) is recorded FIRED in
`numerical_receipt.prediction_deviations` — never smoothed.

## BOUNDS

CPU-only; stdlib + Pillow + ffmpeg on rendered frames; no GPU, no engine
process, no browser, no network (github.com reads excepted); <= 16 MiB new
output; all writes inside this attempt workspace (checkout + scratch);
E:/PythonChimera and the play worktree READ-ONLY; pinned reference hash drift
fails; no next assignment taken after submission.
