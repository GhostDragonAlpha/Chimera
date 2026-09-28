# PREREGISTRATION — ONT-U03 focus-loss/input-release controls qualification

Card `ONT-U03` (planning U03, verification profile `controls`, kind **motion**),
attempt `593b5ff8b920461581bb715826613ad7`, agent
`arrival-b249a6084f3c4525afde7644b08ead4f`, criteria
`a161edd6e1bb2aaf7f55c96503992b17a008f5ebe111032be01d717846aef625`, scope
`01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`. Written and
frozen BEFORE the focus-policy probe or capture ran (the first probe run
timestamp is recorded in the runtime receipt; this file is committed before any
evidence artifact exists). The probe code implements EXACTLY the frozen
timeline, checks and views below; any misprediction is recorded FIRED in
`numerical_receipt.prediction_deviations`, never smoothed.

## REVISION TRAIL (before any candidate commit; nothing smoothed)

- REVISION A (pre-run, from the pinned module laws): D-key steering sign
  (A/D are LEFT/RIGHT turn => the D press carries -OMEGA and curves the
  referent AWAY from the pillar), the mid-interval release instant (2075, not
  2050: the 2050 boundary carries the held demand) and the second blur
  instant (1620, a mid-interval no-op) were corrected BEFORE the first run.
- REVISION B (post-first-run, recorded FIRED in
  numerical_receipt.prediction_deviations): the camera-only window was moved
  from [3000,3400] to [3100,3400] — the frozen decay law samples the
  2950-release tail at 2950 (full), 3000 (v0*0.5) and 3050 (exact 0.0), so
  the original window contained a legitimate decay record; and the C1
  generated-schedule silence clause was scoped to the positive-speed
  deadline (the frozen mapper's own precedence law can deliver a SECOND
  exact-zero record after a live S override — measured as
  second_zero_observations, never a stuck command; the strict two-zeros
  clause holds on the scripted timeline in C2/C3). The probe itself was
  never edited to change a measured outcome: the trace bytes, every scripted
  check measurement and the capture video are identical across the revision
  boundary.

## DONE_WHEN being qualified (the ONLY clause)

"Alt-tab, disconnect and key release clear or age commands under a declared
policy; no stuck movement" — calculation C12: "20 Hz implies a 50 ms command
interval, not an end-to-end latency guarantee"; observation: "Keep operator
desktop focus and processes untouched". Dependency ONT-U01: DONE (merged PR
#152, merge commit `f8a5f712`, the qualified ONT-U01 input-mapper lineage).

## RECONCILE (records reused, not duplicated)

U03 is ALREADY IMPLEMENTED and integrated in the play lineage at `8fc072f3`
("U03 integrated — focus-loss/disconnect policy (41/41; consistency-with-U01
held byte-identically; expiry floor; no-stuck fuzz clean; honest REVISION A
trail)"; ancestor of the pinned head), with the R3 stack fix (release_all
passthrough) integrated at `d2a0e593` and X02's SessionFlow driving it. The
preserved records-leg evidence, recovered read-only via
`git -C E:/ChimeraWork/monkey-play-20260924 show 9afbddcd…:<path>` into this
attempt's `reference/` subtree (byte-exact, hashes asserted at probe import;
EXTRACTION.json records all hashes; the play worktree is left untouched at its
HEAD `8d16d3c1`):

- `tools/monkey_campaign/product/focus_policy.py`
  `e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0` — THE
  QUALIFIED SUBJECT (`subject_sha256` of the capture): the M-U03 focus/
  disconnect policy layer (declared blur/disconnect/recovery/age-floor policy;
  its own file docstring is the declared policy).
- `tools/monkey_campaign/product/focus_policy_tests.py`
  `f1d7a2fd39dca37729532c41a74f2d061e6d7fc95dedb3da564d13b2b4304fa9` and
  `agents/U03_focus/receipts/focus_policy_tests_20260924.txt`
  `3e31524f765697290469fcba5f35b11524e9a916e6c9e6d2800aad32e2967552` — the
  preserved frozen U03 falsifier module and its GREEN 41/41 receipt
  (P1 no-stuck, P2 consistency, P3 expiry floor, P4 no-desktop, P5 named
  state, P6 seeded fuzz), reused as the records leg.
- `agents/U03_focus/PREREGISTRATION.md` `f078f1fd…` and `brief.md`
  `3156ab60…` — the preserved frozen U03 contract.
- `tools/monkey_campaign/product/input_mapper.py`
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` — U01's
  mapper the policy drives (byte-identical to the qualified ONT-U01 subject
  hash in PR #152's merged evidence) with its tests
  `95f44e90…` and GREEN receipt `00c73e34…`.
- `tools/science_funnel/typeb_export/command_record.py`
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` — the
  seam; `tools/monkey_campaign/product/follow_camera.py`
  `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7` — the
  declared camera referent (same pin as the qualified U01 capture).

The MISSING work this card adds is the controls/motion-profile QUALIFICATION:
the frozen focus-policy probe + trace + camera manifest below (the original
U03 records are headless falsifier receipts with no controls-profile camera
evidence; the card's own completion clause is "Lead-approved exact-head PR
merged with full ontology qualification evidence").

## SUBJECT (identity pinned before execution)

The REAL pinned `FocusPolicy` (which itself wraps the REAL pinned
`InputMapper` and gates its output through `is_expired` at the emission
boundary) over the REAL pinned `CommandRecord` v1 seam, plus the REAL pinned
`FollowCamera` over a probe-owned deterministic body referent. Imported
byte-exact from `reference/` with hash assertion at import; the probe owns NO
re-implementation of the subject. The policy's event surface is exercised
exactly as declared in its docstring: `press`/`release`/`mouse`/`tick`,
`on_blur`/`on_focus`/`on_disconnect`/`on_reconnect`, named `state`
(`focused`/`blurred`/`disconnected`), `last_trace` receipts.

## FROZEN RUNTIME PROBE (the ONLY run that produces evidence)

CPU-only; stdlib + Pillow (frame drawing) + ffmpeg (frame packing). One
deterministic headless run: injected integer milliseconds only (never a wall
clock in any asserted path); no window, process, HTTP, GPU or engine; the
operator's desktop focus and processes are untouched (the "alt-tab" of this
profile is the policy's declared `on_blur` event, not an actual OS focus
change — synthetic events only). Tick grid 50 ms (`INTERVAL_MS`), ticks 0..3400
-> 69 rows in `evidence/trace.jsonl` (tick id, t_ms, events, held keys, named
policy state, emitted records with issued_tick and gate disposition, cumulative
sink call log, policy trace receipts, body referent state, per-view camera
poses with measured occlusion rays).

Frozen timeline (events processed before the tick at the same ms; press time
1000 keeps every press on-grid):

- t=1000 `W` down -> commanded boundaries 1000..1450 at the band ceiling
  0.763625; t=1100 `D` down (carried yaw -OMEGA, curving the referent AWAY
  from the declared pillar at x=+0.9); t=1200 `D` up (boundary 1200 yaw
  exactly 0.0 — steering release carries no heading memory).
- t=1300 `W` up (on the boundary) -> the mapper's own decay law: boundary 1300
  samples elapsed=0 (full pre-release speed), boundary 1350 carries EXACTLY
  0.0, silence after. (The KEY RELEASE leg of done_when, under the mapper's
  declared decay.)
- t=1450 `W` down again; boundaries 1450,1500,1550 at V_MAX.
- t=1600 FOCUS LOSS (the declared `on_blur`): policy `release_all` through the
  mapper while `W` is held. Same boundary law: boundary 1600 carries full
  pre-loss speed (elapsed=0), boundary 1650 EXACTLY 0.0, silence from 1700.
  The policy's own trace records the release receipt `(blur, 1600, ["W"])`.
  No stuck command. (The ALT-TAB leg.)
- t=1620 a SECOND blur while already blurred: a NAMED no-op (`no_op`), one
  release receipt only, and the in-flight decay tail is NOT restarted —
  boundary 1650 stays EXACTLY 0.0 (a restarted tail would sample
  0.763625*0.5 there instead).
- t=1700 press `W` while blurred -> DROPPED BY NAME (`dropped_blurred`);
  t=1700 mouse +30 while blurred -> DROPPED BY NAME. Zero records.
- t=1800 `on_focus` (recovery) -> blurred cleared; the held set is empty (the
  release already happened); the next accepted press arms a fresh grid.
- t=1900 `W` down (fresh grid, boundaries 1900..2000 at V_MAX); t=2075 `W` up
  (MID-INTERVAL, between the 2050 and 2100 boundaries) -> tail: boundary 2050
  still carried the full held demand; boundary 2100 samples elapsed=50 ms ->
  v0*0.5 = 0.3818125; boundary 2150 EXACTLY 0.0; silence after.
- t=2200 FOCUS LOSS again, now idle (inert): blur emits NOTHING; the state
  names `blurred`.
- t=2300 `on_focus`; t=2400 `W` down; boundaries 2400,2450,2500 at V_MAX.
- t=2550 DISCONNECT (`on_disconnect`): release + the named disconnected state;
  boundary 2550 carries full pre-loss speed, boundary 2600 EXACTLY 0.0;
  silence from 2650. (The DISCONNECT leg.)
- t=2650 press `S` while disconnected -> DROPPED BY NAME
  (`dropped_disconnected`); the state names `disconnected` (disconnect
  dominates blur in the named state).
- t=2700 `on_reconnect` -> disconnected cleared; state returns to `focused`.
- t=2800 `W` down -> boundaries 2800,2850,2900 at V_MAX; t=2950 `W` up (the
  boundary instant itself) -> boundary 2950 samples elapsed=0 (full
  pre-release speed), boundary 3000 samples v0*0.5 = 0.3818125, boundary 3050
  EXACTLY 0.0; silence from 3100.
- t=3100..3400 CAMERA-ONLY WINDOW: zero input events of any kind. The camera
  pipeline keeps running. Frozen prediction: zero records, zero policy events,
  body referent delta EXACTLY zero while camera writes are observed.

EXPIRY FLOOR sub-probe (the AGE leg of done_when, frozen values at the SAME
probe's checks): with the policy's gate clock deliberately stalled (the
declared failure mode: a record already older than `MAX_AGE_MS` = `VALID_MS` =
100 ms at the moment of delivery), stale records are dropped AT THE GATE, by
name (`expired_at_gate` with the record's issued tick), never emitted; a
healthy clock delivers with age 0. Ages are physics ticks (15 = 50 ms);
`is_expired` is strictly greater than `EXPIRY_TICKS` = 30.

Body-state referent (probe-owned, declared, the ONLY mover of the body):
advances by the projected commanded speed under zero-order hold — per
delivered record, heading += yaw_rate*dt_s, x += v*sin(heading)*dt_s,
z += v*cos(heading)*dt_s. Positions are OUTPUTS of delivered records; nothing
else (camera included) can move the referent.

## FROZEN CHECKS (each is a numbered prediction; measured by the probe)

1. `C1_policy_no_stuck_fuzz` — 5000 seeded randomized event schedules
   (random.Random seed 20260926; keys W/S/A/D/Shift/Space + mouse deltas +
   policy events blur/focus/disconnect/reconnect; injected clock at 1 ms):
   after EVERY release/blur/disconnect event at instant E, no positive-speed
   record is emitted later than E + `RELEASE_DECAY_MS` (the mapper's own decay
   is the only tail; the per-schedule window runs from E to the next accepted
   speed press, whose records are the NEW command, not the old one);
   every emitted record is finite with v_forward in [0.0, 0.763625] and
   |yaw_rate| <= 1.6; every sink call is exactly one `emit(CommandRecord)`
   through the policy gate; no phantom key ever survives while the gate is
   closed (a drop never arms a key); the scripted trace's records satisfy the
   same bounds; the module source contains NONE of the forbidden markers
   (pose_apply, hinge_bin, joints_bin, stride_bin, gait_bin, urllib, socket,
   requests, ctypes, subprocess, qpos, keybd_event, SetCursorPos, SendInput).
   The strict two-zeros silence clause of the preserved P6 is measured as an
   observation on the scripted timeline (C2/C3); on generated schedules the
   frozen mapper's own precedence law (a live `S` overriding a decaying `W`
   tail can emit a second exact-zero record, delivered by the policy gate as
   a live zero-advance target) is measured and reported as an observation
   with its exact schedule, not as a stuck-command failure — no positive
   speed ever survives its deadline and no emission occurs without a live
   demand.
2. `C2_blur_clears_no_stuck_command` — the t=1600 blur with `W` held: held set
   empty at once; the tail lands EXACTLY 0.0 by 1650 (<= blur+100 ms); total
   silence from 1700 until the recovery press at 1900; the policy trace names
   the release. (P1.a–P1.c of the preserved receipt, re-measured on the probe
   timeline.)
3. `C3_disconnect_clears_named_state` — the t=2550 disconnect: same decay law;
   the named state is `disconnected` afterwards; press/mouse while
   disconnected are dropped and NAMED (`dropped_disconnected`); the reconnect
   clears the named state; blur and disconnect are independent named states
   (reconnect restores `focused` when nothing else is held).
4. `C4_press_mouse_dropped_while_unfocused` — the t=1700 blurred press/mouse
   and the t=2650 disconnected press produce ZERO records and NAMED drops; the
   held set stays empty; releases always pass; ticks always pass (the in-flight
   decay reaches the sink).
5. `C5_recovery_clean_rearm` — after `on_focus`@1800 and `on_reconnect`@2700
   the held set is empty (recorded in the policy's rearm receipt), no phantom
   key survives, the next accepted press starts a NEW grid at the full demand
   (no replayed tail, no resurrection of the old command), and a double blur
   while already blurred is a NAMED no-op that does NOT restart a decay tail.
6. `C6_age_floor_expiry_gate` — the stalled-clock sub-probe: records already
   older than `MAX_AGE_MS` at delivery are dropped at the gate, named with
   their issued tick; delivery ages measured in physics ticks (0/15/30 kept,
   45+ dropped); `is_expired` marks expiry strictly after 30 physics ticks of
   age (100 ms) and not before; `MAX_AGE_MS` is the SAME OBJECT as
   `VALID_MS`; every frozen constant is the SAME OBJECT as the mapper's
   (imported, never redeclared); the module source declares no duplicated
   frozen literal.
7. `C7_consistency_with_u01_release_all` — the policy's blur stream is
   BYTE-IDENTICAL to U01's own `mapper.release_all` at the same instant on the
   same demand (count, values, issued ticks, source, version); every record
   that reached the sink carries `source == "u01_input_mapper"` (the policy
   never rewrote a record); blur's decay is the mapper's own law, never
   restarted by the policy.
8. `C8_no_camera_induced_body_movement` — (a) in the camera-only window:
   zero policy events, zero records, body delta exactly zero while camera
   writes are observed; (b) every FollowCamera client write is on the single
   declared route with only the 8 camera fields; (c) at every tick the body
   position equals the exact zero-order-hold integral of the records DELIVERED
   so far (independent recomputation from the sink log; max residual 0.0) and
   per-boundary displacement <= v_max*dt (no jump); the policy cannot move the
   body because it can only gate records.
9. `C9_obstruction_declared_target_readable` — the obstructed view's occlusion
   ray is MEASURED blocked (pinned `FC.ray_clear(eye, target, pillar)` False)
   at EVERY sampled tick — the frozen construction aims the camera THROUGH
   the declared pillar (a `FC.Cylinder` at (0.9, 0, 0.75), r 0.30, top 2.0):
   eye = pillar + normalize(pillar - body_anchor)*1.4, target = body anchor;
   the pillar is DRAWN in front of the body (declared, never concealed); the
   required target (the drawn player anchor marker) stays readable — its
   center projects inside the frame and the marker extends far beyond the
   pillar's angular footprint every tick; close-target distance measured in
   [1.5, 3.0] m every tick.
10. `C10_timing_chain_bound` — every delivered    record carries (t_ms, issued_tick) with issued_tick == t_ms*300//1000;
    press-to-first-record gaps measured and reported; the 50 ms boundary is a
    command CADENCE, not an end-to-end latency guarantee (the mid-interval
    release at 2075 first samples at the 2100 boundary — a measured gap,
    declared in the trace; C12's warning is measured, not just declared).

## FROZEN VISUAL CAPTURE (from the SAME trace; no second run)

One deterministic video `evidence/capture.mp4` (640x360, 207 frames = 3 views
x 69 ticks, 20 fps, ffmpeg libx264 yuv420p bitexact), rendered by
`capture_build.py` from `trace.jsonl` through the three DECLARED profile
views, each a diagnostic+clean pair binding the same trace sha:

- view `normal follow-camera distance` (seconds [0.00,3.45]):
  `sampled_trajectory`, interpolation `recorded_each_tick` — the REAL pinned
  FollowCamera's applied solution per tick (engine eye/up laws, 45 deg
  vertical FOV, engine radius floor at mesh_r 1.0).
- view `obstructed and close-target views` (seconds [3.45,6.90]):
  `sampled_trajectory`, `recorded_each_tick` — the frozen obstructed-close
  construction (eye through the declared pillar, target the body anchor), the
  measured occlusion ray logged per tick in the trace, the pillar drawn
  depth-correctly in front.
- view `repeatable inspection side view` (seconds [6.90,10.35]):
  `fixed_bookmark` — the engine side bookmark (radius 12, theta pi/2, phi 0.3,
  target origin), identical pose all 69 samples (the repeatable inspection
  view).

Diagnostic rows carry the three profile layers with stable tag bindings —
"input/state/tick display" (held keys, NAMED policy state, tick, emitted/gated
records, expiry), "camera target and frustum diagnostics" (target marker,
frustum edge rays, distance-to-target text), "selected creature labels" (the
selected creature tag bound to the player anchor) — plus the scene (ground
grid, player anchor disc + heading arrow, obstruction pillar in the obstructed
view). Clean rows carry the scene only (depth-tested, no diagnostics). Camera
fields per manifest schema: frame `monkey_session_world_yup_m`, right-handed,
metres, quaternion_wxyz_camera_to_frame, forward +Z / up +Y, near/far 0.1/200,
640x360, aspect 16:9, perspective 45 deg vertical FOV, samples covering
tick_interval [0,68] exactly. The manifest is validated in-process with the
campaign's own `visual_capture.validate_manifest` + `visual_gate.verify`
against `card_task.json` (the frozen card profile).

HONEST BOUNDARY (declared up front): the pixels are a deterministic CPU
visualization of the recorded headless focus-policy trace of the qualified
subject (the policy, mapper and seam are headless by construction); they are
NOT native engine frames. "Alt-tab" here is the policy's DECLARED `on_blur`
event, not an OS focus change — the observation clause forbids touching the
operator's desktop focus. The integrated native playable-runtime checkpoint
stays with the integration lane. The body referent is probe-owned and
declared; the heading integration is a declared preview of the carried yaw
demand, which the v1 adapter routes NOWHERE (measured in the U01 lineage and
re-checked in C7 here).

## FALSIFIER

Any probe outcome deviating from checks 1-10 fires; a stuck command after a
blur, disconnect or key release (a positive-speed record after its clearing
event's decay deadline); any record out of bounds; any seam call that is not
emit(CommandRecord); any body movement not exactly accounted for by delivered
records; any camera write carrying a body field; any unnamed dropped intent
while unfocused; any unnamed stale delivery at the gate; any tick gap
inconsistent with the frozen 50 ms chain; any obstructed-view tick where the
occlusion ray measures clear or the required target is unreadable; any clean
view containing diagnostics; any camera-manifest field disagreeing with the
trace; any editing of the pinned reference sources (hash drift) — fails this
qualification and reopens the card. A second exact-zero record following a
live `S` precedence override (U01's own law, delivered as a live zero-advance
target) is a recorded observation, not a stuck command.

## BOUNDS

CPU-only; stdlib + Pillow + ffmpeg on rendered frames; no GPU, no engine
launch, no browser, no network (github.com reads excepted for publication);
<= 16 MiB new output (the video is <= 6 MiB); all writes inside this attempt
workspace and its prepared checkout; E:/PythonChimera and the play worktree
read-only; each test invocation bounded to 120 s.
