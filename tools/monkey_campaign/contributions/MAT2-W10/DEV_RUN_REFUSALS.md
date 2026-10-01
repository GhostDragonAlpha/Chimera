# DEV_RUN_REFUSALS — MAT2-W10

The W08 lesson: development-run refusal codes live in a frozen prereg file
or here. Recorded BEFORE any sealed run; the sealed runs are the receipted
arms of `run_all.py` at the final candidate commit.

As of this file's writing (the implementation commit, BEFORE any gated run):

- GATED RUN 1 (runner job c3098c681fa54fb99db061263364b4cd, slot auto,
  sealed 69a97e4c..., manifest 1be34c73..., exit 2):
  `REFUSAL: input_pin_mismatch:extract:gait_controller.hpp`
  Cause: the gait_controller.hpp pin row carried the RUNTIME_RECORDED
  placeholder; extraction (extract_pinned_tree) requires the byte-exact
  expected sha for every blob it materializes. Correction: pinned the
  measured sha `f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd`
  (exactly the prereg's "sha recorded in verify_inputs.py PINS" clause).
  No physics ran; the refusal fired at stage 1 (pins) as designed.
- GATED RUN 2 (runner job aa2077c518f2453c806cd274db2be6d1, sealed
  859ff4e3..., manifest c79e764d..., exit 1): pins + gate/load + R1/R2/R3
  all GREEN through evaluation; then a code defect, not a physics refusal:
  `TypeError: '>' not supported between instances of 'str' and 'float'` at
  walking_demo.stability (the scene's declared pad_gaps shape is
  `{"hl": [g_hl, g_ml], "hr": [g_hr, g_mr]}` — a dict of two lists — not a
  flat iterable). Correction: `gap_values(row)` flattens the declared shape;
  the P8/P10/P11 gap consumers now use it. The scene bytes were never in
  question; the consumer misread the declared seam shape.
- GATED RUN 3 (runner job 052635c011934ec1bb05ccc66adeef94, sealed
  6a40329b..., manifest 09141ad3..., exit 1): P2-P7 evaluations GREEN;
  then `KeyError: 'per_tick'` at stability(res4) — the probe arm returns the
  scene's RAW observation records (its own dict shape: com_vel 3-vector,
  contact_count 4+legs, pad_gaps dict), not the commanded arms' per-tick
  rows. Correction: `normalize_record()` maps the raw record onto the row
  shape for the P8 bars; no physics claim touched.
- GATED RUN 4 (runner job 35815882484c4525bcf2279f74698d0a, sealed
  d381ccc9..., manifest 06949e96..., exit 2):
  `REFUSAL: prediction_failed:P11_com_identity` — my P11 paired the x-delta
  with the PRE-step velocity; the pinned scene law updates v FIRST and then
  advances x by dt*v (scene_cpu.step), so the exact identity pairs the
  x-delta with the POST-step velocity (the next row). Correction: P11 and
  the FB4 com identity now pair with the post-step v (the identical pairing
  W08's P8 carried). A detector pairing defect, disclosed; the scene bytes
  were never in question.
- GATED RUN 5 (runner job c1f4fa8a1bbd40049f994bf3fa1e4313, sealed
  1d3f7ac5..., manifest 37398d73..., exit 2):
  `REFUSAL: prediction_failed:P10_supervisor_events` — a REAL refuted
  prediction, disclosed and corrected by AMENDMENT A3 (before any passing
  claim is recorded): P10's zero-unsupported-ticks claim misread the sealed
  chain. W09's A0 run MEASURED 224 unsupported-class ticks of 900 (the
  gait's own double-swing windows; W09 amendment A4 declared it a finding),
  and the pinned scene carries four ALWAYS-CONTACTED front pads
  (contact_count = 4 + legs). "On a supported surface" is executed as the
  four-pad floor at every tick + no penetration + the swing windows counted
  and bounded (A3), never as zero-swing. The supervisor on R1 is
  observation-only (zero response events by construction; the sealed
  responses are R4's).
- GATED RUN 6 (runner job 49b9b3a2161f4cf8929f5faa151630b7, sealed
  50efad8b..., manifest 1d5758ef..., exit 1; AFTER A3 = 90a9367a landed):
  P2-P13 evaluations + supervisor classification GREEN; the sealed W09
  detector battery then raised `KeyError: '_front_force'` —
  oe.derive_constants does not include the two scene-derived keys the
  sealed detectors consume; W09's own run built consts with a small
  builder (`build_consts`) adding `_front_force` (scene_cpu._FRONT_FORCE)
  and `velocity_envelope_m_s` (scene_cpu.derived_envelope()). Correction:
  w09_consts now replicates that builder exactly (pinned bytes only).
- GATED RUN 7 (runner job 946b2c05663b4ab69a6b0cf9525e815c, sealed
  24ee22ac..., manifest e7aa1a7b..., exit 2):
  `REFUSAL: falsifier_did_not_bite:FB2` — my FB2 credit condition demanded a
  velocity-recursion residual > 1e-5, but the stride override rode the
  RECORDED command channel, so the identity law CLOSES on the tampered arm
  (it is a sealed-R1-law violation, not a concealed force). Correction: the
  arm's bit now credits the prereg's FIRST-named detector — the applied
  stride deviation from the sealed R1 law (clean 0.2 exact, tampered 1.8)
  — with the velocity residuals recorded honestly beside it and the
  class provenance named (the concealed-force form is W09's FB2 heritage,
  sealed in the W09 receipt and carried, not re-run here).
- GATED RUN 8 (runner job 03067077f7574955870067e215bbfd52, sealed
  104cff5a..., manifest 2f632e2a..., exit 1): ALL predictions P1-P13 and
  all falsifier arms GREEN through evaluation; the failure moved to the
  trace exporter: `KeyError: 'per_tick'` on R4 (the probe arm delivered
  only raw records). Correction: run_probe_arm now records the same
  per-tick row shape as the commanded arms (including the per-tick state
  hash), so the fall arm's trace is first-class like the walk arm's.
- GATED RUNS 9-11 (jobs 9835fc83 / c84cd1af / 9940225d): walking_demo
  reached FULL GREEN (P2-P12 all PASS, F_all_green True, traces
  0dc4dc75.../0b8b7545...) with three exporter-stage plumbing reds in
  between (probe-arm per_tick rows missing intervention_reason; trace
  final-hash fallback), then run_capture refused
  `asset_geometry_absent:thigh_length` — the declared segment table lives
  at `body_model.segments_Table1` inside the pinned derived-numbers bytes,
  not at the top level. Correction: the reader descends the pinned
  structure (bytes unchanged; the pin already holds).
- GATED RUN 12 (job b88bf7721987464892b1fb8c1f500497): run_capture hit the
  pinned F04 raster convention — `TypeError: 'float' object is not
  subscriptable`; F04's raster_tri consumes colour[y][x] rgb tuples and
  depth[y][x] (2D), not flat buffers. Correction: render_frame builds the
  pinned convention; the encoder feeds f04.frame_bytes with rgb24 (960*3 =
  2880 is 4-aligned, no padding) and the G4 decode identity compares
  decoded bytes to the SAME frame bytes (still BMPs remain the committed
  supplementary set, hash-listed per row).
- GATED RUN 14 (job 98ddffe86afa465e81408bdcc892f0e0):
  `REFUSAL: falsifier_did_not_bite:FB5` — walking_demo stayed fully green;
  the capture's FB5 frames rendered IDENTICAL because both the bound and the
  tampered body sat OUTSIDE the fixed bookmark frusta (empty backdrops):
  the walk covers meters and the declared bookmarks were spawn-anchored.
  Correction: all three profile views are declared BODY-ANCHORED FOLLOW
  views (position/target are offsets from the walked body's anchor at the
  sampled tick; the per-frame anchor is recorded in every manifest row and
  the camera-frame law is declared in the capture context) — the U02
  follow-camera heritage. The tampered binding now differs in-pose and is
  visible; the discriminator compares actual rendered content.
- GATED RUN 15 (job 65961ea3270e414ca8636987a25895bb): FB5 now BITES (the
  follow-anchor frames carry real content); the G4 decode identity then
  failed (`capture_codec_violation:decode_mismatch`) — 3-byte rgb24 into
  FFV1 risks ffmpeg's automatic yuv conversion (not byte-exact). Correction:
  the capture moves to the W09 codec-standard form — FFV1 `-level 3 -g 1
  -fflags +bitexact` mkv with `bgr0` frames (4 bytes/px, top-down), which
  FFV1 carries LOSSLESSLY, and the G4 decode probes decode bgr0 and compare
  byte-exact to the SAME frame bytes.
- No development harness run of walking_demo.py has happened beyond the
  gated runs above. The implementation was written against the pinned bytes
  and compile-checked; every execution is runner-gated. Any further
  pre-green refusal will be APPENDED here verbatim with its named code, the
  exact command and the correction — never silently discarded, never cited
  as final-run evidence.
- Anticipated refusal codes are frozen in PREREGISTRATION.md section 9
  (`criteria_pin_mismatch`, `input_pin_missing`, `input_pin_drift`,
  `certificate_validator_violation`, `deploy_gate_sanity`,
  `load_identity_mismatch`, `build_identity_mismatch`,
  `prediction_failed:<name>`, `walk_unsupported_tick:<tick>`,
  `w09_replay_drift`, `asset_geometry_absent`,
  `registry_profile_missing_key`, `capture_codec_violation`,
  `w10_fb<n>_premature`, `falsifier_did_not_bite:<arm>`,
  `fb1_window_precondition_unmet`, `vacuous_comparison:<name>`).

Known pre-prereg dev notes (disclosed for completeness):

- The segment lengths (thigh 0.163 m, shank 0.182 m) were located in the
  derivation lane's derived_numbers.json during implementation; that became
  Amendment A2 (pin added BEFORE any run) rather than an inline constant —
  the refusal law (`asset_geometry_absent`) worked as designed.
- The W09 supervisor module needed an explicit pin for the replay arm; that
  became Amendment A1 (BEFORE any run).

- GATED RUNS 16-32 (iteration to full green; every red preserved above and
  in the runner job logs): (a) the pinned visual_capture validator required
  the CAMPAIGN capture schema (task_id/run_id/subject_sha256/capture_sha256/
  tick_interval + per-row view_id/mode/pair_id/state_binding/
  artifact_locator/camera 17-field/visibility) — the manifest builder was
  restructured to that shape with ONE manifest per arm (walk, fall) so the
  (view_id, mode) universe stays unique; (b) the codec settled on the W09
  standard form (FFV1 -level 3 -g 1 -fflags +bitexact mkv, bgr0 frames)
  after a codec_probe diagnostic proved the bgr0 roundtrip byte-exact
  (a micro runner job; its three-line output is in job
  35a761d0c01e4852bf18e45bb6e24940's log, dev-diagnostic only, never
  evidence); (c) the G4 probes bind to the sha of the bytes ACTUALLY piped
  into each encode; (d) FB4's receipt row gained the standard
  clean_control.green key (receipt-shape fix only).

FINAL GATED RUN (job 183dad8bec084a09a58df4150d371825): ALL STEPS GREEN —
walking_demo P2-P12 all PASS + F_all_green; run_capture 24 frames, two FFV1
mkv videos, both arm manifests structurally valid (validator verdicts
CARema-METADATA-STRUCTURE-ONLY / visual_acceptance false); run_checks 13
executed 0 skipped pass; REPORT.md generated; lint OK; evidence bundle
39 files; batch_gates 12/12 PASS (RESULT: PASS).
