# PREREGISTRATION — MAT2-U07 measure controls during actual play

Frozen BEFORE any implementation file, harness run, measurement or capture
frame of this card exists. This file is committed ALONE (separate-first; the
M03/P04 law). Every emitted receipt refuses any document whose
`preregistration_sha256` does not match these live bytes.

- Card MAT2-U07 (planning id U07, slot 2), agent `wk-u07-arrival-1`,
  attempt `5e2bc3cb1fec4305911a1048b600723d`, attempt workspace
  `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-U07\5e2bc3cb1fec4305911a1048b600723d`,
  file package `package` (NO_WORKTREES law: pinned file package, no clone, no
  worktree), publication branch `review/MAT2-U07`, PR base `astra/gait-capture`.
- Criteria sha256 `029dc39358471b06fed736c4712d6b1d92d4b1c22178e20027dfff53cbdc1532`
  (startup join == registry `kanban.cards[MAT2-U07].criteria_sha256`, re-read
  READ-ONLY (`file:...?mode=ro`) from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` at run time;
  mismatch = refusal `criteria_pin_mismatch`).
- done_when (verbatim, registry): "End-to-end input response and camera
  behavior meet P06 limits under repeatable scenes".
- Observation (verbatim, registry): "Human feel and measured latency are
  distinct acceptance fields".
- Card task falsifier (verbatim, registry brief): "A stuck command,
  camera-induced body movement, unreadable required target, concealed
  obstruction or unbound timing evidence fails."
- Profile: `controls`/`motion` (registry read-only at capture time; G7);
  numerical_evidence_required true; clean_view_required true; diagnostic
  layers ["input/state/tick display", "camera target and frustum diagnostics",
  "selected creature labels"]; views ["normal follow-camera distance",
  "obstructed and close-target views", "repeatable inspection side view"];
  profile procedure (verbatim): "Exercise controls, focus loss, camera
  obstruction and release while logging the exact input and body state. Use
  the task-owned subset of layers/behaviors. Inventory absent or unresolved
  components explicitly; do not require downstream skills to accept an
  upstream interface. Freeze exact applicable probes and views before
  execution."
- Base: `a07ac859d4ef16bb34d4006a75c4de8dbee462b4` = the seeded
  `refs/remotes/origin/review/MAT2-U07` (the publisher-seeded integrated tip:
  the MAT2-W10 merge, PR #311; the worker_start preparation pinned it after
  the named ref was seeded). The file package is pinned to this base by
  worker_start preparation. Ancestry at prereg freeze: the W10, U03, U04,
  P06, F08, M12 and G04 winner heads are all ancestors of this base
  (merge-base verified at attempt start).
- Composed against CARD_STARTER v5 and the house standards:
  `IMPLEMENTER_CHECKLIST.md` (G1-G9) + `TOOLKIT.md` (P1-P9), cited at the
  candidate commit. Dispatch brief: card slot 2 of MAT2-U07.
- Calculations: C12 (input timing and control mapping — sealed by W08;
  consumed, retained at the 50 ms seam law, never re-modeled) and C23
  (camera/response interface law; consumed through the pinned U02 camera
  constants and the U03 focus policy; nothing sealed is recomputed or
  re-decided).

## 0. The governing frame (what "actual play", "controls" and "camera" mean here)

THE CERTIFIED WALKING RUNTIME IS THE FROZEN CERTIFIED LINE — nothing else.
W07 loaded the accepted walking policy through the certificate machinery;
W08 commanded it through the ACTUAL player command port with a frozen script;
W09 wrapped the declared supervisor; W10 delivered the walking acceptance in
the pinned clearing build. This card adds no policy, no reissue, no retune,
no runtime change: it DRIVES the same certified line and, for the first
time, threads ONE clock through all four measured input-pipeline stages while
logging the exact input and body state — the I-U07-TRACE / -FOLLOWUP
remaining gates ("native recorder seams; one-clock threading in a live run
with repeatable scenes and actual play") executed on the live control path
that EXISTS.

- "ACTUAL PLAY" is the W08/W10 sealed open-loop form: the pinned U01
  InputMapper (the port seam, INTERVAL_MS=50) produces versioned
  CommandRecord v1 records into a recording sink; the frozen adapter
  projects; the certified scene `cpu-walk-scene/1.0.0`, build
  `cpu-walk-scene-build-N`, steps at 300 Hz. No engine process, no GPU, no
  training (claim class stays offline/trace at the 300 Hz tick; TC-11
  COST-GAP carried).
- "CONTROLS" is the frozen W08/W10 input script (W10 `command_model.py`,
  extracted UNMODIFIED at the base and imported, never copied): start /
  in-range turns / saturating turn / release-decay / live-zero stop, PLUS
  this card's probes: an expiry hold (R4) and a focus-loss window (R5).
- "CAMERA" on this line is the DECLARED CPU-line camera law: the pinned U02
  `follow_camera.py` geometric constants and projection laws (imported
  reference bytes; the module is an HTTP client and no engine service exists
  here — its LAWS are consumed, its transport is NOT) applied to the run's
  own recorded state through the W10 records-only software renderer
  (`visualization.py`, extracted UNMODIFIED). The render consumes records
  ONLY (W10 FB6 sealed heritage, cited, not re-claimed); the simulation loop
  has NO camera input channel (structural: the loop signature admits none),
  and the camera-body invariance arm executes the falsifier check at the
  only place it can exist on this line.
- Physics charter: commands choose actuator setpoints; camera and focus
  policy WRITE NOTHING. The scene's public stepping API (`step(applied,
  saturation)`) is the only motion path; no pose-write channel exists in any
  arm; the focus policy is U03's sealed layer over the untouched mapper
  (imported reference bytes).
- The no-reissue law: the EXISTING certificate is deployed; nothing is
  re-issued, re-certified or amended; no trained bundle is loaded.
- OUTCOME-INDEPENDENCE: W08's tracking bands, W09's envelope responses and
  W10's walking acceptance are SEALED and are NOT re-claimed. This card
  measures the TIMING/CONTROL-RESPONSE and CAMERA behavior of the same line
  against P06's frozen limits.

## 1. Input pins (verified byte-exact at attempt start; drift = refusal `input_pin_mismatch` / `input_pin_missing`)

Store pins (evidence-store `E:/ChimeraWork/monkey-coordination/evidence-store/`):
- `MAT2-P06/numerical/numerical` `a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8`
  (the frozen P06 limits record: `ui-poll-cadence-ms` = 100 ms carried;
  `camera_visible_player_outcomes`; the `network-latency-sla-ms` operator
  decision request — UNRESOLVED, honest negative section 8)
- `MAT2-U01/numerical/qualification_receipt.json` `94887cc14ba6d2fc7a76c04949d5015cbfada899a817c3acb497e5d53a7a0c61`
- `MAT2-W08/numerical/checks_receipt.json` `cd9998ab612b0e320b657a196d672e668199bb92188527d887aafeb321014c37`
- `MAT2-W10/numerical/walking_demo_receipt.json` `2fa7dbf180db6090611fdc0d074ebe80d79b43eb25a4a7162e218cbacd22aa02`
- `MAT2-W10/numerical/checks_receipt.json` `999fc693dab04199fe3459ff332577d1d73a7e9506a335e2db5f0a3f7ec142b2`

Base-blob pins (read from the shared repository's Git object database at the
package base `a07ac859d4ef16bb34d4006a75c4de8dbee462b4` through the DECLARED
read-only `git cat-file` access in `source_access.py`; NO_WORKTREES law).
The W10 certified-line pin table (W04 certificate machinery, lane repo
machinery, scene, F04 rasterizer, terrain, visual validator, W09 supervisor)
is verified by W10's own `verify_inputs.py`, extracted UNMODIFIED at the base
and executed first (it pins its own base `273d7e59…`, an ancestor blob-identical
for every file it names — the W10 merge is contained in this base). The
U07-ADDED pins, all computed at prereg freeze from the base tree:
- `tools/monkey_campaign/contributions/I-U07-TRACE/input_trace.py`
  `c8f4e4442a3ceedecd9c636857eda92642d26ec535d45f2c91a3ce9fd4550a57` (PR #138 bytes)
- `tools/monkey_campaign/contributions/I-U07-TRACE-FOLLOWUP/adapter.py`
  `8522cbefb176fbd512f7191dfc79e8ff6dd45d9ed51fe4d34b23c307829df723` (PR #145 bytes)
- `tools/monkey_campaign/contributions/I-U07-TRACE-FOLLOWUP/reference/tools/monkey_campaign/product/follow_camera.py`
  `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7`
- `tools/monkey_campaign/contributions/MAT2-U02/reference/tools/monkey_campaign/product/focus_policy.py`
  `e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0`
- `tools/monkey_campaign/contributions/MAT2-W10/command_model.py`
  `0f9fa1a37092760ab4de05bcd32a7b0c769202dddd4347ff54fbdb5c77d184aa`
- `tools/monkey_campaign/contributions/MAT2-W10/visualization.py`
  `2e98e8d803f1fde383b00f648100bc8404eac41e3e27db9f6bc32a03de71fafb`
- `tools/monkey_campaign/contributions/MAT2-W10/verify_inputs.py`
  `25c5fc289a48f24886510d8849856044016e155c627b92c78c15a8781f18f4f6`
- `tools/monkey_campaign/contributions/MAT2-W10/walking_demo.py`
  `fb394677306bcb3d808271cce72212c000b82455567e74c1090d3c1003d90ea1`
- `tools/monkey_campaign/visual_capture.py`
  `5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05`
- `tools/monkey_campaign/product/input_mapper.py` — the seam is NOT in-tree;
  its byte identity is pinned at the FOLLOWUP reference copy
  (`contributions/I-U07-TRACE-FOLLOWUP/reference/tools/monkey_campaign/product/input_mapper.py`,
  `7a36a45e…`, the U01 pinned-lineage hash; the runtime resolves the module
  through the W10 extraction's stripped namespace, byte-equal)
- `tools/science_funnel/typeb_export/command_record.py` — same law: pinned at
  the FOLLOWUP reference copy (`67711759…`; resolved at run through the W10
  extraction's stripped namespace, byte-equal)

## 2. The four-stage one-clock law (the card's measurement instrument)

The accepted I-U07-TRACE module (`input_trace.py`, PR #138 bytes, IMPORTED —
never copied, hash asserted at run) owns the trace law: a latency is EXACTLY
the difference of two matched-stage timestamps on ONE clock identity, ONE run
identity and ONE build identity; anything unmatched is REFUSED, never
interpolated; a refused trace produces NO latency output. The I-U07-TRACE-
FOLLOWUP adapter (PR #145 bytes, IMPORTED) is the seam-connection precedent:
its two Python stages are consumed as declared; its two declared-MISSING
native stages are exactly what THIS card supplies on the certified line:

- `input`            — the harness observes the scripted key/mouse state
                       transition (the only input writer; `feed_events` law).
- `command_emitted`  — the pinned mapper's sink receives the CommandRecord
                       (the recording sink; the no-teleport law).
- `simulation_consumed` — the certified scene's step that zero-order-holds
                       that record (the ZOH boundary at issued_tick+1).
- `presented`        — the declared CPU-line frame record offered by the
                       U07 capture for that tick (the W10 records-only
                       renderer's frame; ABSENT-INVENTORY item A1 names what
                       a native engine presented frame would require).

ONE clock: the injected integer-millisecond monotonic clock (`injected_ms`),
one run identity per arm, one build identity (`cpu-walk-scene-build-N`).
Clock identity, run identity and build identity are recorded on EVERY event;
the accepted module refuses mixed identities by name (`mixed_clock`,
`mixed_run`, `mixed_build`) and the checks re-prove it.

## 3. Frozen arms (the repeatable scenes)

Scene identity: certified declared scene, SEED 20260920 (the certified scene
seed; continuity with W08/W10), horizon and script constants from the
UNMODIFIED W10 `command_model.py`. "Repeatable" is EXECUTED: R2 is a
byte-identical re-execution of R1 and must reproduce R1's per-tick state
chain exactly (P5).

- R1 BASELINE: the full frozen W08/W10 script, horizon 10500 ticks; the
  four-stage trace; stage segments; latency metrics (informational for
  wall-clock; structural bounds are the frozen laws).
- R2 REPEAT: identical re-execution (determinism zero-control).
- R3 WRONG-KEY SCRIPT: W10 R3 semantics verbatim (the wrong operator presses
  W at the stop boundary and holds it); identical to R1 through tick 5429;
  trace-level wrong-command response is this card's claim (the physical
  separation is W10's sealed P9, cited, not re-claimed).
- R4 EXPIRY HOLD: press W at the start, never release, no further input
  events; the pinned consumer-side expiry contract (EXPIRY_TICKS=30) must
  revert the consumer to the inert path; stuck-command law.
- R5 FOCUS LOSS: the pinned U03 focus policy over the untouched mapper:
  W held; declared BLUR event fires `release_all` (physical-release decay to
  exact zero then silence); a press DURING the blurred window is dropped and
  NAMED (no chain); after `on_focus`, a fresh press opens a NEW chain.
- CAMERA ARMS (records-only, AFTER the runs; bounded frames; frozen plan):
  - The declared render window: consumed ticks [4351, 4651] (the turn/hold
    segment); presentation frames at ticks 4365..4665 step 15 (21 frames,
    the clean C_V1 view; every window chain's presented lag <= 15 ticks).
  - C-V1 "normal follow-camera distance" — the declared follow view (clean
    presentation frames + diagnostic frames at ticks {4365, 4500, 4650}).
  - C-V2 "obstructed and close-target views" — the declared occluder box
    between camera and body (clean+diagnostic at tick 4500) + a close-target
    (small radius) view (clean at ticks {4500, 4650}); occlusion declared,
    never concealed.
  - C-V3 "repeatable inspection side view" — fixed side bookmark at tick
    4365, rendered TWICE clean and TWICE diagnostic; identical frame bytes
    required within each mode pair (repeatable inspection).
  - Diagnostic layers on every diagnostic frame: input/state/tick display,
    camera target and frustum diagnostics, selected creature labels (the
    task-owned subset of the `controls` profile).

## 4. Frozen predictions (named variables; every number derived at run from pinned bytes, none hand-copied)

- P1 `seg_input_to_command_ms_max`: over every R1 chain,
  `command_emitted.t_ms - input.t_ms <= 50.0` ms (the seam poll INTERVAL_MS;
  C12 caller-data limit).
- P2 `consumed_lag_ticks_max`: over every R1 chain,
  `consumed_tick - issued_tick == 1` (the ZOH boundary law; the derived ms
  value `1000/300` is recorded, never asserted as a wall-clock).
- P3 `presented_lag_ticks_max`: over every presented event,
  `presented_tick - consumed_tick <= 300` ticks (1 s at 300 Hz; the declared
  CPU-line render bookkeeping bound; wall-clock verdict stays UNQUALIFIED —
  section 8 item A2).
- P4 `poll_period_ms_max`: every input poll lands on the 50 ms grid;
  `poll_period_ms <= 100.0` (the P06 frozen `ui-poll-cadence-ms` caller-data
  limit; the ONLY P06 numeric the latency chain is QUALIFIED against).
- P5 R2 `state_chain_sha256` list == R1's (bit-identical repeatable scene);
  R2 trace events == R1 trace events under the declared normalization
  (the per-arm `run` identity field is normalized away; every other byte of
  the canonical JSON must be equal).
- P6 R3: after `WRONG_INJECT_TICK`, R3's emitted records carry
  `v_forward_m_s > 0.0` with `wrong_script=true` while R1's corresponding
  records are inert/zero — the wrong-command response at the trace level.
- P7 R4: `first_revert_age_ticks == 31` (age = t - last_record_tick; the
  pinned `> EXPIRY_TICKS=30` law); after revert, no positive-speed record
  exists without a new press (silence/inert).
- P8 R5: (a) no positive-speed record after `blur_ms + decay_deadline_ms`
  (the pinned decay law); (b) dropped blurred presses produce NO new chain
  and ARE named in the policy decisions; (c) the post-recovery press opens a
  chain with a fresh seq.
- P9 `camera_fields_complete`: every rendered frame's manifest row carries
  ALL the profile's `camera_required_fields` (15; recorded per-frame with
  declared units); `occlusion_or_xray_mode` = "declared_occluder_depth_test"
  on C-V2, "none" elsewhere; the C-V2 occluder provably intersects the
  look ray (executed segment-box intersection, recorded numerically) and
  the target label is depth-tested (an occluded label is DECLARED occluded,
  never concealed).
- P10 `camera_body_invariance`: the recorded per-tick state chain is taken
  BEFORE any render; the camera arms render DIFFERENT parameter sets from
  the SAME records; no render call touches run state (structural: render
  consumes records only; W10 FB6 heritage cited).
- P11 `limits_honesty`: the accepted module's summary verdict for
  wall-clock `end_to_end_ms` is `unqualified` (no frozen wall-clock SLA
  exists); the qualified verdicts are exactly P1/P2/P4 against the frozen
  caller-data laws. A fabricated wall-clock PASS is the falsifier.
- P12 `timing_evidence_bound`: every emitted event carries clock
  `injected_ms`, one run identity, one build identity; a deliberately
  mixed-clock fixture is REFUSED by the accepted module in the checks
  (unbound timing evidence fails).

## 5. Frozen probes and views (profile procedure executed verbatim)

- Controls probe: the frozen script exercises start, in-range turns both
  directions, the saturating turn, release-decay and live-zero stop.
- Focus-loss probe: R5's declared BLUR/DROP/RECOVER sequence through the
  pinned U03 policy (operator desktop untouched — the U03 constraint).
- Camera obstruction probe: the declared occluder axis-aligned box
  `[ocx0,ocx1]x[ocy0,ocy1]x[ocz0,ocz1]` = `[-0.35,0.35]x[0.5,1.0]x[0.4,0.8]`
  metres in the body-anchored camera frame at the declared C-V2 ticks. The
  C-V1 look ray (eye offset `[1.2,1.6,3.2]` -> target offset `[0,0.5,0]`)
  provably crosses this box: at z=0.8 the ray is at (x=0.3, y=0.775) and at
  z=0.4 it is at (x=0.15, y=0.6375), all inside the box ranges
  (pre-registered arithmetic; the run re-executes the segment-box slab test
  numerically and must confirm it). The look ray must intersect the box
  (numerical test) and the target's projected screen point must fall inside
  the box's projected 8-corner screen footprint (executed convex-hull
  containment test); the target label is depth-tested (an occluded label is
  DECLARED occluded, never concealed).
- Release probe: R1's declared W release (decay tail) + R4/R5's release
  paths; every release is a traced input event.
- Views: C-V1/C-V2/C-V3 above; viewport 960x540; vertical FOV per view
  declared in the manifest; near/far per view; aspect 16:9; projection
  "perspective"; coordinate_unit "m"; right-handed Y-up (the pinned camera
  law).
- Clean view required: C-V1 is the clean view; it must show the readable
  required target (the body label) unoccluded with the diagnostic layers.

## 6. P06 limits as caller data (the acceptance law of the done_when)

The ONLY P06 numbers that exist as frozen limits for this chain:
- `ui-poll-cadence-ms` = 100 ms (carried limit; P4's caller data).
- The seam INTERVAL_MS = 50 ms command cadence (C12; P1's caller data) — a
  command cadence, not a latency guarantee (W08's sealed framing).
- `camera_visible_player_outcomes.walking_replay_scenario` + the profile's
  `camera_required_fields` (the camera-behavior acceptance structure; P9).
The `network-latency-sla-ms` operator decision is UNRESOLVED in the P06
record: NO wall-clock end-to-end latency limit exists. The accepted module's
own law (limits are caller data; absent limits stay `unqualified`) is
EXECUTED, not restated (P11). Human feel is a DISTINCT acceptance field
(observation verbatim) and is NOT measured here (section 8 item A4).

## 7. Falsifier disposition (each card falsifier clause -> executing arm)

- "A stuck command … fails" -> R4 (expiry revert law) + R3 (wrong-key script)
  + R5(a) (no-stuck invariant after blur).
- "camera-induced body movement" -> P10 (records-only render; no camera
  channel in the loop; executed A/B renders over identical records).
- "unreadable required target" -> P9 (clean view C-V1 label readability
  recorded; occluded labels declared occluded in C-V2).
- "concealed obstruction" -> P9 (the C-V2 occluder is declared geometry with
  a numerical intersection proof and depth-test record; concealment would
  fail the intersection/depth records).
- "unbound timing evidence" -> P12 (one clock/run/build per trace; mixed
  identities refused; the checks re-prove refusal on a tampered fixture).

## 8. Absent inventory (honest negatives; declared, not discovered at run time)

- A1 NATIVE RECORDER SEAMS: the native engine's input/tick/frame recorder
  seams DO NOT EXIST. The `presented` stage here is the DECLARED CPU-line
  frame record of the records-only renderer. A native presented frame would
  require the engine recorder work explicitly left open by the FOLLOWUP
  record. No native engine process is started.
- A2 WALL-CLOCK END-TO-END LATENCY: the P06 `network-latency-sla-ms`
  decision is UNRESOLVED; this card QUALIFIES only the structural
  tick/cadence bounds (P1/P2/P4) and reports wall-clock metrics
  informationally as `unqualified` (P11).
- A3 HUMAN FEEL: not measured (distinct acceptance field; observation
  verbatim). No human trial exists in this evidence.
- A4 CAMERA SERVICE: the pinned `follow_camera.py` is a frozen HTTP client;
  no engine service exists on this line; its geometric LAWS are consumed,
  its transport is NOT exercised.
- A5 SESSION CONTROLS: the X02 Return/Escape/R/Q session semantics attach to
  no interactive process on this line; declared, not exercised.
- A6 OS FOCUS: the U03 constraint (operator desktop untouched) holds; focus
  loss is exercised at the policy layer, not the OS window layer.
- A7 PHYSICAL SEPARATION: W10's sealed P9 wrong-command physical separation
  is CITED; this card re-executes only the trace-level wrong-command
  response (P6).

## 9. Publication and honesty mechanics

- This file is committed ALONE first (the M03/P04 law), by the Lieutenant;
  every receipt embeds `preregistration_sha256` of THESE bytes and refuses
  any mismatch.
- The sealed run executes ONE command (`run_all.py`) through the CPU runner
  (task_package.py): pins -> registry -> W10 pin/extract layer -> gate and
  load identity -> arms R1-R5 -> predictions P1-P12 -> receipts + trace
  JSONL -> named checks -> bounded capture (views + manifest + mkv) ->
  report -> report-number lint. First failure stops with that stage's exit
  code.
- The 12 card-kit gates run against the card directory. Dev-run failures and
  refusals are preserved in `DEV_RUN_REFUSALS.md` (honest negatives), never
  deleted.
- Claim class: offline/trace controls-camera verification on the certified
  CPU line. A diagnostic or scaffold alone cannot close this card; the card
  closes only through the lead-approved exact-head PR with the full
  qualification evidence.
