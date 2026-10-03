# DEV_RUN_REFUSALS — MAT2-X05 (lane x05-impl, wk-x05-impl)

Honest negatives of Phase B. Nothing here is deleted; every entry names its
run (by sealed manifest sha256 where applicable), its root cause, its fix,
and where the preserved receipt lives. COMPLETE ITEMIZATION: S1-S22 plus the
S19b/S19c process notes (an earlier append cascade lost S7-S10 and S19b from
this file; they are RESTORED here verbatim-in-substance from the lane record
- review R2).

## Pre-seal development record (no sealed run consumed by these)

- R1-dev: the lane consistency script's first execution refused with
  `git_failed` on every git-backed check - the helper passed `data=` to
  `subprocess.run` instead of `input=`. Fixed in
  `E:\ChimeraWork\monkey-coordination\x05-impl\x05_consistency_check.py`;
  the rerun is 65/65 GREEN. No sealed run was consumed.
- R2-dev: `landmarks_x05.live_checks` was first written with a broken
  pairwise-separation implementation (subsampled bbox arithmetic plus a
  placeholder in `draw_landmarks`). Replaced BEFORE any run: the landmarks
  rasterize through the pinned `f04.raster_tri` with the real camera, and
  the separation law uses the declared vertex-based measure (exact over all
  12 vertices per landmark) with a rendered-mask-overlap pin to 0.
- R3-dev: `diff_channels.pair_series` first computed channel diffs against
  frame A's masks only, which would MISS a channel pixel appearing on only
  one arm. Fixed to the union of both arms' channel masks BEFORE any run;
  covered by the unit battery.
- R4-dev (declared content overlap, recorded by design): on DIAGNOSTIC
  frames the frozen render order makes the instrument strip overlap the
  pinned tick-digit overlay and the L2 strip overlap the pinned stride bar.
  Disclosed in the capture context, the view-spec calibration, card_prereg
  and REPORT.md; the tick remains readable in the L2 declared layer.
- R5-dev (unit reconciliation, recorded by design): the frozen prereg
  phrasing "re-press at +150 ms (SHORT) / +300 ms (LONG)" rides the sealed
  a12 probe_events, whose deltas are exactly +150/+300 TICKS on the 300 Hz
  injected clock. The driver reproduces the sealed deltas ("classes
  verbatim"); every receipt carries UNIT_RECONCILIATION.
- R6-dev (declared view subset, recorded by design): the registry
  presentation profile declares three views while the frozen X05 capture
  law declares ONE (the pinned U07 C_V1 constants, identical to the profile
  view "normal player camera"). The manifest validates against the DECLARED
  one-view subset; the FULL registry profile is recorded read-only in the
  capture context with the disclosure.

## Sealed-run refusals and failures (chronological; all receipts preserved)

- S1 (job e6ff38cbd23d454d8bedfe85bb2d9a40, seal 374e2250..., FAILED):
  stage unit_battery RED - test_x05's attribution-law fixture itself made
  the synthetic arms differ in a PRE-LAWFUL slot (forbidden by prefix
  identity); `pre_lawful_all_zero` honestly reported False. The machinery
  was correct; the fixture was wrong. Fixture fixed; the lawful-frame-only
  mutation asserted with first_lawful_whole_frame_diff == 1.
- S2 (job 5aadb20d61904d15aa0f03317a8aa8d8, seal cf7d7f89..., FAILED):
  unit_battery GREEN, then ModuleNotFoundError `source_access` - W10's
  verify_inputs imports it at module top and this card carries NO copy
  (imported, never copied). Fix: w10_layer() puts the PINNED MAT2-U07
  extraction dir (section-1 pin) on sys.path before executing the layer.
- S3 (job 963ec24957a044fa9dc1036a1897eca3, seal a843d005..., FAILED):
  `input_pin_missing:.../MAT2-U07/verify_inputs_u07.py` - the U07 pin layer
  is not one of this card's section-1 pins, so it was never extracted.
  Fix: u07_layer() loads it from the package's MAT2-U07 sibling after
  asserting byte-equality with the shared object database at THIS base.
- S4 (job 0da38d650e2040d085af93b63e0df38f, seal 636b6527..., FAILED):
  AttributeError - the U07 layer's extractor is `extract_u07_tree`, not
  `extract_pinned_tree`. Fix: call the module's real attribute.
- S5 (job 035c9c9355d24d579e75bfd04469f031, seal 8882edbe..., FAILED):
  unit+layers+gate_and_load GREEN; the first brake arm refused with
  port_issued_tick. ROOT CAUSE: the frozen probe events are OFF-GRID (the
  a12 sealed probe_events carry the re-press at now_ms 15003 = tick 4501);
  the mapper's poll grid restarts AT that off-grid reading and the mapper's
  own issued_tick law ((now_ms*300)//1000, no explicit tick_source in the
  tracer path) reads one tick BELOW the emission loop tick thereafter. This
  driver's assertion (issued == loop tick) was stricter than the certified
  mapper law. Fix: enforce the MAPPER'S OWN law; record
  issued_minus_emission_loop per chain; the X-P9 consumed lag defined on
  the certified ZOH (applied at the NEXT tick after the poll: exactly 1).
  Also: the X-P2a frame sha moved from canonical-JSON of the 518k-cell
  buffer (seconds per frame) to the lossless packed-bgr0 bytes.
- S6 (job 1b840e9bc5bc402fadfc65688ca176ca, seal 53a97cbb..., FAILED):
  `prediction_failed:X_P9_emit_latency:pair1:A:13500.00` - the 50 ms law
  had been bound to EVERY chain; between scripted inputs the certified
  mapper emits on its own poll grid with a seconds-old input ANTECEDENT
  (no latency claim). The frozen law reads "on every probe chain".
  Fix: X-P9 evaluated on the probe chains; the full per-chain table
  recorded; the ZOH consumed-lag == 1 enforced on every chain.
- S7 (job 42667cb0c17149f0bb36d3719c7bbec3, seal e69d55db..., FAILED):
  pairs executed fully; then a probe chain at 97 ms - the pinned mapper's
  release-decay law (_apply_tail) emits a SECOND record on the release
  event: the tail-deadline exact-zero record at the second boundary after
  release (<= released_ms + 100 ms by the mapper's own deadline law), which
  the frozen 50 ms phrasing did not anticipate. Disposition (the prereg's
  own rule: exceeding a bound is a RECORDED FINDING, never tuned): each
  probe event's FIRST-response chain is GATED at 50 ms (worst 47 ms); any
  further exceeding chain is the named finding
  `x_p9_probe_latency_exceeded` recorded with census. A relaunch of this
  sealed manifest had its exit code masked by a `| tail` pipe in the
  dispatch shell; the lane now reads receipt states directly (one
  execution, one receipt).
- S8 (job 03e3895c3b1043af9736816165a23db8, seal 7698ac30..., FAILED):
  KeyError 'com_v_m_s' in the instrument draw - render_frame_x05 was
  handed the POSE (which carries the row's value as `com_vel`) where the
  instrument's row law expects the ROW field name. Fix: render_frame_x05
  takes the consumed `row` explicitly (pose fallback maps com_vel ->
  com_v_m_s unchanged).
- S9 (job 58793f7c78934421835f3930bc08924b, seal 0cf32671..., FAILED):
  pair 1 CLEAN renders passed in full (X-P2a byte-identity, X-P2b, the
  live checks, X-P4 clean probes, X-P7), then
  `X_P4_instrument_diag:pair1:A` - on DIAGNOSTIC frames the X04 L1 panel
  (drawn after the instrument per the frozen layer law) fills row y=40
  over x[12,300], exactly the instrument's bottom border row (the frozen
  rects share that row). The ink text (y[14,24]) is untouched. Fix: the
  probe takes the DECLARED overlap (DIAG_BORDER_OVERLAP_PX = 289 border px,
  diag frames only), disclosed in the probe receipt row.
- S10 (job 37701f1115a443d19892897e0bbfadf0, seal 200e8e4c..., FAILED):
  pair 1 executed END-TO-END GREEN; pair 2 arm A recorded the first X-P3
  bbox-census deviation: landmark_rock_far on one frame measured
  rendered-mask right edge 190 vs projected-vertex edge 193 (3 px > the
  frozen +/-2 px tolerance) - the rock tetra's acute base corner thins
  below pixel coverage at that depth. The diagnostic rerun
  (e86bc4b6273b423c95d5923b57820934, seal 9780bf02...) carried the
  failing-row instrumentation. Disposition: bbox-census deviations beyond
  the frozen tolerance are the named finding
  `x_p3_raster_tolerance_exceeded` (recorded with census; tolerance NOT
  changed), while the SUBSTANTIVE world-fixed law is gated separately and
  more sharply: measured landmark-mask displacement == the ACTUAL pinned
  F04 projection's displacement through each frame's own row-derived
  camera (the Captain's correction 2; the derived px/m scale recorded per
  frame per landmark - prereg X-P3 already deferred to the actual
  projection; NO amendment required).
- Captain corrections mid-flight (2026-10-02), applied: (1) SEPARATE THE
  VISUAL TESTS - the landmark displacement consumes only the four declared
  landmark palettes; the separation is DECLARED in the falsifier/
  presentation receipts and REPORT.md. (2) THE ACTUAL CAMERA PROJECTION -
  gated per frame as described in S10; stated where the prereg defers.
- S11 (job 761cbab378f84686ae331fd07d2f8248, seal 31bf4716..., FAILED):
  KeyError 'p3_flow_rows' - the corrections patch for the X-P3 rewrite was
  applied with a str.replace whose anchor text no longer matched, so the
  rewrite was a SILENT NO-OP while the aggregation block landed. Fix: the
  section replaced with an ASSERTED match. Lesson: patches must assert
  their anchor or refuse.
- S12 (job 16e964b43a6f4d07aa19f6ed9e77c98a, FIRST seal of package-final
  (d19a9e6f...) after package/'s history budget refused further seals,
  FAILED): the KeyError persisted because the aggregation indexed the
  per-arm fact tables while the X-P3 flow/findings accumulate at the
  pair-facts dict level. Fix: aggregation reads the dict-level keys. (A
  suspected duplicated loop line was a false alarm from overlapping sed
  windows - the file verified intact.) package/ PRESERVED with its sealed
  history.
- S13 (seal ed7d1bab..., job in the runner store, FAILED): THE MILESTONE -
  stage presentation_verification GREEN for the first time (all 10 pairs;
  live checks measured min clearance 110.83 px, exactly the design
  number; the actual-projection flow law held on every frame pair);
  named_checks GREEN; then stage capture refused
  `capture_piped_sha_drift:pair1:A` - stage 1 persisted the frame arrays
  in bgr0 channel order while every consumer expects the true render
  colors. Fix: npys saved as decoded RGB.
- S14 (seal 1de84ebd..., FAILED): stages 1-3 ran through all 20 videos
  (full-stream decode + the decoded diff channels + the falsifier
  receipt); refused at the END of stage 3 in the pinned validator:
  `camera_sample_mode_invalid` - the camera record lacked the TOP-LEVEL
  `sample_mode` and `samples` keys (the X04 form sets them explicitly).
  Fix: camera_record adds fixed_bookmark + two identical samples covering
  the declared tick interval.
- S15 (seal 89ea0055..., FAILED): stages 1-3 GREEN including the pinned
  validator; stage 4 refused on its first case: the card FrameStore looked
  up `frames_P01_BRAKE-SHORT.npy` while the arrays are per-Arm. Fix: the
  gate's frame-id keys carry the arm.
- S16 (seal 7e31d4ec..., FAILED): THE EVIDENCE RUN - stages 1-3 GREEN end
  to end (`X-P5 visible pairs 10/10; X-P6 depth ordering True`); the four
  defect cases each REJECTED with their expected codes; the gate RED on
  exactly ONE production law: landmark_rock_far's DIAGNOSTIC floor (25 px)
  - measured census 743-769 px on every clean frame and 0 on every
  diagnostic frame (rock_far's projected footprint lies ENTIRELY inside
  the declared L1 panel rect which the frozen layer law draws last on
  diagnostic frames). Disposition: view-spec v2 minted per the freeze law
  BEFORE any GREEN sealed capture (clean floors untouched).
- S17 (seal d43cd5ed..., FAILED): v2's floor-0 form still routed the empty
  rock_far footprint through the template's co-location ratio (60 frames).
  Disposition: view-spec v3 - the diag class no longer expects
  landmark_rock_far at all (zero mask pixels there, so no UNDECLARED error
  arises either); disclosed; still BEFORE any GREEN sealed capture.
- S18 (seal dd106e2b..., FAILED): ALL 20 PRODUCTION CASES GREEN under v3;
  the gate RED narrowed to ONE defect-expectation mismatch:
  defect_clean_diagnostic_leak was RED (correctly) but its dominant code
  tied between UNDECLARED_MASK_ID (the leak's essence) and
  SUBJECT_MASK_BELOW_FLOOR (the L1 leak rect also covers rock_far). Fix
  (card-owned defect geometry, not a threshold): the leak paints the L2
  (x04_event_strip) rect, which contains no landmark footprint.
- S19 (seal c0859cf1..., FAILED): THE GATE RUN - `capture gate: GREEN (24
  cases)`; `report written; L_pixel=VISIBLE L_state=SUPPORTS`; the only
  RED: make_report's self-inflicted circular dependency on the driver
  summary (result.json), which run_all writes only AFTER all stages.
  Fix: the report's law is the stage receipts; the dependency removed.
- S19b (process note): the first S19 fix attempt aborted on an asserted
  anchor mismatch BEFORE writing, but the follow-up seal had already been
  chained in the same shell command and captured the UNFIXED tree (seals
  1c853d6f... and 48d4143d... - preserved, never run). Standing rule: the
  seal is never chained with an unverified patch.
- S19c (process note, cont.): the standing lane rule, effective now:
  patch -> verify (asserted anchors + parse + behavioral absence checks)
  -> byte-verified sync -> seal, each in its own command, never chained.
- S20 (seal 002074a0..., job in the runner store, FAILED): GATE GREEN +
  `report written; L_pixel=VISIBLE L_state=SUPPORTS`; the only RED: the
  report lint's `lint:min_separation` - a number-FORMATTING mismatch (%s
  vs the %.2f form). Fix: the report prints both live-check minima with
  %.2f. No measurement or threshold involved.
- S21 (process note): package-final's retained sealed history reached the
  ~1 GiB budget law (`package_history_budget_exceeded_preserve_and_
  publish`). package-final PRESERVED; a third package (`package-run`)
  created at the SAME pin with the same scopes and the contribution copied
  byte-verified (31 files identical). The chain is recorded in EVIDENCE.md.
- S22 (job 1f98e087b2b04f8bb9fe132e00661f2f, seal 002074a0..., exit code 0
  but runner state FAILED on ONE missing declared keep): THE COMPLETE GREEN
  RUN except bookkeeping - every stage GREEN, all artifacts preserved; the
  missing keep was `outputs/pins_x05.json`: the verification stage called
  the pin layer's functions directly, so the pin layer's own receipt file
  (written by its main()) was never emitted. Fix: the stage calls
  verify_inputs_x05.main() first. The run's evidence is preserved and
  load-bearing.

## Review corrections (post-review; text-only, no pixel re-measurement)

- Captain precision correction (post-R1, APPLIED): the corrected claim is
  exactly "GAIT PHASES DIVERGE IN THIS RUN; THE CAUSE REMAINS UNVERIFIED."
  The finding + the scoped wording carry ONLY the observational claim; the
  a12-vs-this-run contradiction may be regime, seed, window or mechanism
  differences, and none is isolated. The landmark-visibility result (the
  independently verified deliverable) stands on its own and is not tied to
  any gait-response claim.
- R1 (REVIEWER, substantive, APPLIED): the a12-based coupling determination
  and THIS run's own window rows CONTRADICT each other, previously
  undisclosed - this run's brake-vs-control phases DIVERGE (identity 4/21
  per pair; first divergent presented tick t4425; body-channel diffs
  85-155 px from that tick). Disposition: the run's own determination is
  now derived and recorded (x_run_phase_determination) with the NAMED
  FINDING `x_run_phase_divergence_observed`; the coupling-absent wording
  is REGIME-SCOPED everywhere ("DECLARED_ABSENT_IN_THE_A12_LINE_REGIME");
  the deeper a12-vs-X05 question routes to the Lieutenant. CAPTAIN
  PRECISION CORRECTION applied: the claim is OBSERVATIONAL ONLY - the
  gait phases diverge in this run; THE CAUSE REMAINS UNVERIFIED (regime,
  seed, window or mechanism differences are candidates; none isolated).
  No causal "responds to speed" claim is made, and the
  landmark-visibility deliverable stands independently of this finding.
- R2 (REVIEWER, minor, APPLIED): this file is now COMPLETELY ITEMIZED
  (S1-S22 + S19b/S19c; the earlier append cascade had lost S7-S10 and
  S19b), and EVIDENCE.md's sealed-snapshot counts corrected (package/ 12,
  package-final/ 12, package-run/ as sealed).
- S23 (job f19b1f08106c4fd38d9c5d5845b9beeb, R1-correction seal
  87e25abe..., FAILED): the unit battery asserted the OLD disposition
  literal (DECLARED_ABSENT) against the R1-scoped value. Fix: the test
  asserts DECLARED_ABSENT_IN_THE_A12_LINE_REGIME. Also recorded here: the
  first launch of the R1-correction seal was BLOCKED before admission by
  slot 1's preserved-crash recovery refusing on the output budget (a dead
  job's 861 MB scratch, not this lane's data - untouched, reported); the
  rerun pinned --slot 2 per the runner's fixed-slot contract.
- S24 (process note): the R1 wording was first applied with a causal
  implication ("the gait pose responds to the brake... strengthens the
  visible-motion story"). The Captain's PRECISION CORRECTION superseded
  it: the corrected claim is exactly "GAIT PHASES DIVERGE IN THIS RUN;
  THE CAUSE REMAINS UNVERIFIED" - observational only, no causal claim,
  and the landmark-visibility deliverable stands independently. Applied to
  coupling_determination (the finding's law), make_report (the finding
  line + the verdict paragraph), this file, and the lane EVIDENCE
  generator; the intermediate seal (64e8ca22..., job 492dad506f1f46feaba9
  ee4fd3f8b416 - PASSED end-to-end, validating the run-phase wiring) is
  preserved as never-cited evidence.
- S25 (process note, job 5999166962364f9aabd9da28ad8db1ba, seal
  516c7798.../b4bb5ec0...): the launch's exec-harness record died with
  exit 127 and an empty log while the runner process (pid 51148) executed
  the unit battery, then vanished - the same harness-instability class as
  the run-7 disappearance. No receipt was written; the lease + scratch
  remain as a crashed runner's state for the runner's own recovery
  (preserve declared keeps - none were produced - then clean). The lane
  relaunches the SAME seal; the recovery runs first. No sealed bytes
  changed.
