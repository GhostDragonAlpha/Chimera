# PREREGISTRATION (DRAFT) — lane latency: input-to-visible-response latency on the certified integrated build

STATUS: DRAFT for Lieutenant commit (separate-first law, M03/P04). These bytes
are NOT frozen until the Lieutenant commits them on the `astra/gait-capture`
lineage through the publication owner and hands back the commit sha (the pin).
Phase B (the gated measurement) starts ONLY after that handoff. Every receipt
of this lane will embed `preregistration_sha256` of the COMMITTED bytes and
refuse any mismatch.

- Lane `latency`, worker `wk-latency` (Captain correction order #3, item 7:
  the integrated build has MEASURED command-processing latency but UNMEASURED
  input-to-visible-response latency; the two are distinct and every claim of
  this lane names which one it makes).
- Proposed card id `MAT2-L01` (PENDING Lieutenant assignment; the lane and the
  design are the substance, the id is the Lt's to fix). Write scope: the NEW
  lane dir `E:\ChimeraWork\monkey-coordination\latency\`; Phase B contribution
  dir `tools/monkey_campaign/contributions/MAT2-L01/` in a pinned file package.
- NO_WORKTREES law: pinned file packages only; CPU runs only through
  `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`;
  no Git clone, worktree, ref or index mutation by this lane.
- Certified build identity (the measurement TARGET; verified 2026-09-29 from
  the shared repository's object database, read-only):
  - Integrated tip `a30bfb9fc0ac4c46fb677224a76814d349c1e286` ==
    `refs/remotes/origin/astra/gait-capture` ("MAT2-U07: runtime control
    commands", PR #312). The LOCAL branch ref `astra/gait-capture`
    (`5e54c0b7…`) is behind and is NOT read or moved by this lane.
  - `a07ac859d4ef16bb34d4006a75c4de8dbee462b4` = Merge PR #311 (MAT2-W10
    walking), verified ANCESTOR of the tip.
  - Lineage between them (merge-base verified): `34049772` (U07 prereg
    A1-A3) -> `69772e91` (U07 controls package, PR #312 head) -> `a4bc6240`
    (A4 pixel-gate amendment) -> `9a5b9541` (U07 r1 correction) -> `a30bfb9f`.

## 0. The governing frame (what is measured and what is NOT)

THE CERTIFIED INTEGRATED LINE IS THE FROZEN TARGET — nothing is re-tuned,
re-issued or amended. This lane ADDS a measurement of
**input-event-to-first-reflecting-rendered-frame latency**: from a declared
input event at the input seam to the FIRST presented frame whose decoded
pixels differ, inside the body region of interest, in a way attributable to
that command. This is DISTINCT from, and COMPLEMENTARY to, the sealed U07
result (P1 `first_response_ms_max` = 27 ms worst, 50 ms bound, exactly-one-tick
consumed lag over 403 chains), which measures COMMAND PROCESSING (input ->
consumed record) and contains NO pixel claim. Every output of this lane
reports BOTH domains and names the distinction.

- "RENDERED FRAME" on this line is the DECLARED CPU-line presented frame of
  the W10 records-only software renderer (`visualization.py`, pinned bytes):
  the frame record rendered from the run's own per-tick telemetry, encoded
  FFV1 losslessly (bgr0, bitexact, declared ffmpeg calls) and decoded with
  pixel-exact probes. Decoded pixels are the declared proxy of rendered
  pixels (the transport is proven lossless per frame at run time).
- "INPUT EVENT" is the scripted key-state transition observed at the input
  seam by the accepted SeamTracer (the only input writer; the feed_events
  law). It is a physical event ON THE MEASURED PIPELINE, not an OS HID event.
- Attribution law: the deterministic-build property makes the commanded run
  and its control run byte-identical up to the command's effect, so a pixel
  difference between the pair is EXACTLY attributable to the one declared
  command that separates them. Attribution is executed, not assumed:
  prefix-identity and control-diff checks are gated predictions below.
- ONE clock: the injected integer-millisecond monotonic clock (`injected_ms`,
  `now_ms(tick) = tick*1000//300`; tick rate 300 Hz), one run identity per
  arm, one build identity (`cpu-walk-scene-build-N`), per the accepted
  I-U07-TRACE law. Mixed identities are REFUSED, never interpolated.
- Claim boundary (stated in every report of this lane): the measured number
  quantifies the runtime path input-event -> first-reflecting frame INSIDE
  the captured pipeline. It does NOT measure host display/compositor latency,
  GPU present time, USB/HID polling, OS input queueing, or human perception.
  It does not close any acceptance card alone; it FEEDS the
  playable-demonstration report's "usable controls" criterion as the
  runtime-path component of input-to-visible-response latency.

## 1. Input pins (byte-verified at draft time from the certified tip `a30bfb9f`; drift = refusal `input_pin_mismatch` / `input_pin_missing`)

Content sha256 at `a30bfb9f` (read-only `git cat-file blob`):

- `tools/monkey_campaign/contributions/MAT2-U07/controls_harness.py`
  `b4c71813fe05008976611d12b954c5a07dbdfb616556dff62ecc513ca1e28b95`
- `tools/monkey_campaign/contributions/MAT2-U07/run_capture_u07.py`
  `b70c12f3dad5577e9cd1c9f6d45597710f9365d8ce5a9c2cfc7d2b5fd0c18695`
- `tools/monkey_campaign/contributions/MAT2-U07/camera_views.py`
  `0bb53f98de48df1b0541370930614a937e0287b99b8a1a10845a8947786d4b8c`
- `tools/monkey_campaign/contributions/MAT2-U07/pixel_gate.py`
  `784b78032da10816647245b535ab9b88e17586f0e5d76d5183f799c5aadcb0d7`
- `tools/monkey_campaign/contributions/MAT2-U07/source_access.py`
  `0563d123b51bd65a28f74b01afa0daa766001830890b4babb458f407e475759b`
- `tools/monkey_campaign/contributions/MAT2-U07/verify_inputs_u07.py`
  `f5b1e18b22edf408baea26d8b4b349b9688fedc320dd0f373a63a647227e1742`
- `tools/monkey_campaign/contributions/MAT2-U07/run_controls_verification.py`
  `20923d0592f8488f9a3c5980ee2b2ff7cbb86fe1db447f091749fdc3efcda279`
- `tools/monkey_campaign/contributions/MAT2-U07/run_all.py`
  `f8fffd0f895e7b9011dcae1b3c1e92cb91273ef29b0291d0da3a4486e50b9cae`
- `tools/monkey_campaign/contributions/MAT2-U07/PREREGISTRATION.md`
  `a8781f6e9ae3b5aff31a497e52d697e8c60b0ab80b338e48707736576432d033`
- `tools/monkey_campaign/contributions/MAT2-W10/visualization.py`
  `2e98e8d803f1fde383b00f648100bc8404eac41e3e27db9f6bc32a03de71fafb`
- `tools/monkey_campaign/contributions/MAT2-W10/command_model.py`
  `0f9fa1a37092760ab4de05bcd32a7b0c769202dddd4347ff54fbdb5c77d184aa`
- `tools/monkey_campaign/contributions/MAT2-W10/walking_demo.py`
  `fb394677306bcb3d808271cce72212c000b82455567e74c1090d3c1003d90ea1`
- `tools/monkey_campaign/contributions/MAT2-W10/verify_inputs.py`
  `25c5fc289a48f24886510d8849856044016e155c627b92c78c15a8781f18f4f6`
- `tools/monkey_campaign/contributions/I-U07-TRACE/input_trace.py`
  `c8f4e4442a3ceedecd9c636857eda92642d26ec535d45f2c91a3ce9fd4550a57`
- `tools/monkey_campaign/contributions/I-U07-TRACE-FOLLOWUP/adapter.py`
  `8522cbefb176fbd512f7191dfc79e8ff6dd45d9ed51fe4d34b23c307829df723`
- `tools/monkey_campaign/visual_capture.py`
  `5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05`
- The seam modules are NOT in-tree (in-tree paths hold empty placeholders):
  `input_mapper` is pinned at the FOLLOWUP reference copy
  `contributions/I-U07-TRACE-FOLLOWUP/reference/tools/monkey_campaign/product/input_mapper.py`
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44`;
  `command_record` at
  `contributions/I-U07-TRACE-FOLLOWUP/reference/tools/science_funnel/typeb_export/command_record.py`
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e`;
  `follow_camera` at
  `contributions/I-U07-TRACE-FOLLOWUP/reference/tools/monkey_campaign/product/follow_camera.py`
  `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7`;
  `focus_policy` at
  `contributions/MAT2-U02/reference/tools/monkey_campaign/product/focus_policy.py`
  `e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0`.
  Resolution law: U07's own `verify_inputs_u07.py` + `source_access.py`
  (declared read-only cat-file; IMPORTED, never copied).

Evidence-store pins (verified by sha256 at draft time):

- `MAT2-P06/numerical/numerical` (frozen P06 limits)
  `a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8`
- `MAT2-W10/numerical/walking_demo_receipt.json`
  `2fa7dbf180db6090611fdc0d074ebe80d79b43eb25a4a7162e218cbacd22aa02`
- `MAT2-W10/numerical/checks_receipt.json`
  `999fc693dab04199fe3459ff332577d1d73a7e9506a335e2db5f0a3f7ec142b2`
- `MAT2-U07` controls receipt (the sealed P1 = 27 ms / 50 ms / 403 chains
  record this lane cross-checks against)
  `fe73fbcc4dac411d44075d6a212fa6f8a35af95aa3f832543f867c1063d0d299`
  (at `kanban-attempts/MAT2-U07/wk-u07-fix-r1/package/files/.../receipts/controls_receipt.json`)
- U07 capture video `capture_u07_controls.mkv`
  `05ad0e2283581b8489fc857c422af32e92dd9b24892254c84eba20216955a50f`;
  W10 walk video `capture_w10_walk.mkv`
  `bedbe71640f3d09c411e45274b427e7d2876fb3279b9077f33ea0101a7fbd406`
  (cited heritage; NOT re-claimed).

## 2. The measurement instrument (three stages + pixel attribution)

Reuse, read-only and IMPORTED at the pinned bytes (never copies, never
edits): the accepted SeamTracer + adapter (one-clock four-stage law), the
U07 controls harness structure (scene identity, ZOH pending law, recording
sink, consumer-side expiry), the W10 records-only renderer, the U07 capture
stage's codec law (FFV1 bgr0 `-level 3 -g 1 -fflags +bitexact`; encode +
pixel-exact decode probes), and the mechanical decode gate (`pixel_gate.py`,
AMENDMENT-A4 law). The lane ADDS only:

- the PROBE DRIVER: per repeat n, a commanded arm A(n) and a control arm
  B(n) that differ in EXACTLY the one declared probe command (below);
- the ROI DIFF TOOL: decodes each declared frame of both arms from the FFV1
  videos, computes the per-frame pixel-difference COUNT inside the declared
  body ROI, and emits per-pair first-reflecting-frame records with full
  diff-count series (no thresholding beyond "count >= 1");
- the CADENCE meter: the presented-event series of the declared window.

Frozen geometry: the ROI is the projected screen footprint of the body
bounding cylinder (axis at the per-tick body anchor, radius and height from
the run's own state records, grown by the declared 8-pixel margin), computed
at run from records on BOTH arms identically (the union over the pair's
window; the camera is body-anchored, so the ROI rides the body per frame).
Clean C_V1 frames only participate in attribution; diagnostic frames are
excluded (their overlay text changes with tick regardless of the command).

## 3. Frozen arms and repeat count N

Scene identity: the certified declared scene, SEED 20260920, build
`cpu-walk-scene-build-N`; scene constants from the UNMODIFIED W10
`walking_demo.gate_and_load()` (the U07 gate-and-load law: deploy ALLOW or
refusal). Tick rate 300 Hz; the seam poll grid is 50 ms = 15 ticks.

Common script (BOTH arms of every pair): the full frozen W08/W10 R1 script
bytes through tick 4350, then SILENCE (no input events), horizon 4800 ticks
(bounded: covers the declared window plus decay tail). Arm-prefix state-chain
byte-identity between A(n) and B(n) is verified through the probe's consumed
tick (gated prediction L-P1b).

- N = 10 pairs = 2 command classes x 5 declared repeats:
  - Class `FWD` (n odd, n in {1,3,5,7,9}): press `W` at `T_in(n)`, release
    at `T_in(n) + 150` (declared 150 ms hold on the injected clock).
  - Class `TURN` (n even, n in {2,4,6,8,10}): press `A` at `T_in(n)`, held
    through the pair's attribution window (no release inside it).
  - `T_in(n) = 4351 + (n-1)` -> T_in = 4351..4360 (tick-domain repeat
    indices; residues mod 15 = 1..10 sample the seam-poll quantization phase
    without clustering).
- The declared render window (U07's sealed window, reused for continuity):
  consumed ticks [4351, 4651]; presentation frames at ticks 4365..4665
  step 15 (21 frames per arm); presented lag <= 15 ticks is U07's sealed
  law on exactly this window.
- Attribution search set per pair: the presented frames with
  `presented_tick in [T_in(n)+1, T_in(n)+61]` (bounded to the first 4
  presentation slots; a pair with NO differing frame inside it is recorded
  as finding `no_pixel_reflection_in_window`, never interpolated).
- Repeats are full independent runs (no shared state); each pair is sealed
  and receipted individually and in aggregate.

## 4. Frozen predictions (named variables; every number derived at run from pinned bytes; exceeding a bound is a RECORDED FINDING, never tuned away)

- L-P1a `determinism_zero_control`: B(n) re-executed reproduces B(n)'s
  per-tick state chain and all 21 decoded frame bytes exactly.
- L-P1b `prefix_identity`: A(n) and B(n) state chains are byte-identical
  through the command's consumed tick; any earlier divergence is refusal
  `attribution_contaminated` for that pair.
- L-P1c `control_silence`: for every presentation slot with
  `presented_tick < first consumed tick of the command chain`, the A-vs-B
  ROI diff count is 0 (the pair's pre-command frames are pixel-identical).
- L-P2 `state_first_reflection`: `L_state_ticks(n) = presented_tick(first
  frame whose source consumed tick >= consumed_tick(command chain)) -
  T_in(n)` satisfies `1 <= L_state_ticks(n) <= 30` (structure: seam poll
  <= 15 + ZOH consumed = issued+1 + presented lag <= 15).
- L-P3 `pixel_first_reflection` (THE deliverable):
  `L_pixel_ticks(n) = presented_tick(first frame with ROI diff count >= 1) -
  T_in(n)`; expected `1 <= L_pixel_ticks(n) <= 45` (the L-P2 structure plus
  a declared one-slot pixel-accumulation tolerance of 15 ticks: a sub-pixel
  state change may need part of one more stride to become a visible pixel
  difference; the nominal expectation is the command-processing latency
  (27 ms worst, U07 P1) plus at most one render frame (50 ms)). A measured
  value above 45 ticks, or `no_pixel_reflection_in_window`, is a RECORDED
  FINDING about the pipeline's visible-response behavior — not a failure,
  and never a reason to alter the render or the scene.
- L-P4 `clock_conversion`: on the injected clock,
  `L_pixel_ms(n) = presented_now_ms(f*) - input_now_ms(T_in(n))` and
  `L_pixel_ms(n) = L_pixel_ticks(n) * 1000/300` exactly (derived, recorded;
  asserted as injected-clock arithmetic ONLY, never as OS wall-clock — see
  A2). Reported per class (FWD/TURN) as min/median/max over the 5 repeats,
  plus the full per-repeat series in the receipt.
- L-P5 `frame_cadence` (the ticks-to-wall-time denominator): over the
  declared window's 21 presented frames, the measured stride
  `presented_tick(k+1) - presented_tick(k)` is exactly 15 for every
  consecutive pair and `period_injected_ms = 50.0` for every pair; any
  deviation is a finding `cadence_anomaly` (it would change the conversion
  denominator and every L-P4 number).
- L-P6 `command_processing_crosscheck`: on every probe chain, the sealed U07
  laws reproduce: `command_emitted.t_ms - input.t_ms <= 50.0` ms and
  `consumed_tick - issued_tick == 1` (ties this lane's probes to the sealed
  P1 = 27 ms worst result; a violation is a finding, since it would mean the
  certified line's own seam law did not reproduce).
- L-P7 `class_separation`: TURN pairs produce a first-diff frame whose ROI
  difference is nonzero in the horizontal-displacement half of the ROI
  (left/right asymmetry recorded), FWD pairs in the forward half; a class
  that produces no asymmetry signal is recorded as finding
  `class_pixel_signature_absent` (informational about render sensitivity,
  not a failure).

## 5. Probes and views (frozen)

- View: C_V1 clean body-anchored follow view (the frozen U07 follow law,
  follow:True on all views), viewport 960x540, declared near/far and
  vertical FOV in the manifest, aspect 16:9, projection "perspective",
  coordinate_unit "m", right-handed Y-up. Diagnostic frames rendered ONLY at
  the U07 diagnostic ticks {4365, 4500, 4650} for honesty context, excluded
  from attribution.
- Codec: FFV1 bgr0 `-level 3 -g 1 -fflags +bitexact` (the W09/W10/U07
  declared calls); decode probes on frames 0, 16, 20 must be pixel-exact
  (piped-frame sha == decoded sha); a non-exact probe refuses the capture.
- Mechanical gate: every declared frame decodes non-uniform and carries the
  body palette at the declared floors (the A4 gate law), planted-defect
  selftest embedded; the gate is a precondition for attribution, not the
  latency metric.

## 6. P06 limits as caller data

The ONLY frozen cadence/limit numerics this lane consumes: seam
`INTERVAL_MS` = 50 ms (C12, command cadence, not a latency guarantee),
P06 `ui-poll-cadence-ms` = 100 ms (carried limit), and the sealed U07 P1/P2
results as the cross-check anchor (L-P6). The P06 `network-latency-sla-ms`
operator decision remains UNRESOLVED: NO wall-clock end-to-end latency SLA
exists on this line, and this lane fabricates none (A2).

## 7. Falsifier disposition

- "Unbound timing evidence" -> the one-clock/run/build identity law on every
  event; a deliberately mixed-identity fixture is refused by the accepted
  module in the checks (executed, not restated).
- "Attribution not exactly the command" -> L-P1a/L-P1b/L-P1c (determinism,
  prefix identity, pre-command silence); any failure brands that pair
  `attribution_contaminated` and excludes it from L-P3/L-P4 aggregates
  (reported, never silently dropped).
- "A fabricated visible-response claim" -> any claim of host display or OS
  input latency, or any wall-clock SLA verdict, is outside this lane's
  measured boundary by law (A1/A2); emitting one would be the falsifier.

## 8. Absent inventory and honesty (declared up front)

- A1 HOST DISPLAY PATH: not measured. No OS window, compositor, GPU present,
  display scanout or USB/HID polling exists in the measured path; the first
  "physical" input event here is the scripted seam transition and the first
  rendered frame is the records-only renderer's presented frame.
- A2 WALL-CLOCK SLA: none exists (P06 `network-latency-sla-ms` UNRESOLVED).
  All milliseconds in this lane are injected-clock arithmetic
  (`1000/300` ms per tick; 50 ms per presented frame), reported
  informationally for the demonstration report with verdict `unqualified`
  against any SLA.
- A3 NATIVE ENGINE RECORDER SEAMS: absent (U07 A1 inherited); the presented
  stage is the declared CPU-line frame record.
- A4 HUMAN FEEL: not measured (distinct acceptance field).
- A5 TRANSPORT: decoded FFV1 pixels are the declared pixel proxy; the
  pixel-exact decode probes are the evidence that the proxy is lossless.
- A6 DEMONSTRATION REPORT ROLE: this lane's numbers FEED the
  playable-demonstration report's "usable controls" criterion as the
  runtime-path input-to-visible-response component, explicitly bounded by
  A1/A2; they do not by themselves close any card.

## 9. Publication and Phase-B mechanics

- This draft is committed ALONE first (the M03/P04 separate-first law) by
  the Lieutenant through the publication owner; the gated measurement starts
  only after the commit sha (the pin) is handed back to `wk-latency`.
- Phase B package: pinned to the published prereg commit (or a descendant
  containing these bytes identically); certified-line bytes are read at
  `a30bfb9f` through `source_access.py` (read-only cat-file). Contribution
  files: `PREREGISTRATION.md` (these bytes), `probe_driver.py`, `roi_diff.py`,
  `cadence_meter.py`, `run_all.py`, checks, DEV_RUN_REFUSALS.md, receipts.
- Execution: ONE command through
  `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal`
  then `run` (CPU slot), CHIMERA_OUTPUT_DIR declared outputs with --keep;
  run receipts + bounded logs land in the runner results store; lane
  evidence (per-pair records, diff series, videos or their digests, report,
  lint) anchored through `anchor.py` before registry reference; every
  load-bearing artifact sha256-recorded in the lane `EVIDENCE.md`.
- Claim class: offline/trace pixel-attribution timing on the certified CPU
  line; findings are recorded as findings; nothing here re-claims W08/W09/
  W10/U07 sealed results.
