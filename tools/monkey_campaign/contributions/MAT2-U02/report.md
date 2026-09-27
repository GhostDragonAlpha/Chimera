# MAT2-U02 candidate report — follow camera (reconciliation port), attempt 8c5027541211433d8b449f695e714bc5

Agent `arrival-5bd346d1456b4af9942242139034b13d`; base 9ba1be77 (branch-4);
freeze commit fc600f4c; criteria `59dda60fd40a0b94c27378f660bd576e44fe5f7f36f66533448f764128d98c89`;
scope `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.
Done_when: "Player can see motion on ground and at trunk; camera avoids tested
obstruction cases and never moves the animal." Profile `controls` (kind
motion), calculation C23. All work CPU-only (`python -B`), headless, inside
this attempt workspace; E:/PythonChimera and all other workspaces read-only.

## 1. Reconciliation first (what was reused, and proof it is the reviewed work)

The merged ONT-U02 candidate (PR #154 head `c8f0f3b7e4fe2ec6bee0827e54ceacb8fe392750`,
lead ACCEPTED, merged into astra/gait-capture at `7f351044`; registry PASS
review `22bb4e0b67ad4a2ea0e94e28213805c3`) already qualifies this exact
done_when at the component level. The MAT2 card's `definition_raw_sha256`
(`57ded6eb...`) is byte-identical to the archived card's — same done_when,
same controls/motion profile, same C23 attachment; only the scope digest
differs. Both MAT2 dependencies are DONE (MAT2-P01 PR #192 merged 97993cbe;
MAT2-P03 PR #194 merged 13a94391).

Recovery: `git archive 7f351044` extracted the merged contribution read-only
into this attempt's `reconciliation/` area; EVERY recorded hash re-verified
byte-equal before the freeze (trace `97f9fbfc`, capture.mp4 `e3129099`,
capture_manifest `103b93ed`, runtime `a43cec4c`, numerical `c9611b3f`,
capture_receipt `4ef97d7f`, qualification_receipt `8afbe47c`, prereg
`18f1ffca`, report `f78b7a0a`, probe `20f37ae2`, builder `0c3a1bb0`, and all
six pinned reference files equal to their f30f2224 pins).

## 2. What this attempt contributes

Not a re-implementation: an identity-scoped, re-frozen, re-measured port to
the MAT2 scope/criteria, plus the F01-lesson manifest envelope fix:

1. PREREGISTRATION frozen (commit `fc600f4c`) BEFORE this attempt's first
   probe run; archived prereg `18f1ffca` appended byte-verbatim (appendix
   tail hash-equal `18f1ffca`); laws/predictions C1-C14 unchanged.
2. card_task.json generated from the registry brief (task_id U02, scope
   cb5475f8) — the gate's verification contract for THIS card.
3. Ported probe/builder/tests with identity-only edits (exact audit:
   probe 17 removed/22 added, builder 5/5, tests 1/2); nothing else differs.
4. Re-executed everything live in this attempt (numbers in section 4).
5. Camera manifest re-shipped in `chimera.visual_capture_manifest.v1` with
   the identity envelope bound to THIS attempt's committed bytes:
   task_id `U02`, run_id `mat2-u02-camera-20260926-8c502754`,
   subject_sha256 `d61347f0` (pinned subject), capture_sha256 `e3129099`
   (committed capture), tick_interval `[0, 390]`.

## 3. Failing-first (falsifiers demonstrated non-vacuous BEFORE the green run)

- PIN DRIFT bite: one byte of the recovered subject corrupted ->
  `camera_profile_probe.py` refused at import:
  `PIN DRIFT: tools/monkey_campaign/product/follow_camera.py is c41cbb5b...,
  pinned d61347f0...`, exit 1, zero checks executed; byte restored
  (before == after `d61347f0`).
- Gate negative controls on the built manifest (untouched copy validates):
  distance tamper -> `camera_target_distance_mismatch`; clean-row diagnostic
  tamper -> `clean_view_contains_diagnostics`; identity-envelope tamper ->
  `capture_identity_mismatch:run_id`. All three refused.

## 4. Commands and observed results (this attempt, live)

| command (cwd = contribution dir) | observed |
|---|---|
| `python -B camera_profile_probe.py` | 15/15 PASS, `RESULT: ALL CHECKS PASS`, exit 0 |
| (trace determinism vs archived) | evidence/trace.jsonl sha `97f9fbfcfafcfbeaa02ced70636231bd3935ee446b8a9b9c114d2f05ad8a3c8a` — BYTE-IDENTICAL to the archived, PASS-reviewed trace |
| `python -B -m unittest test_camera_profile_probe -v` (pre-build) | 8 tests: 6 OK, 2 skipped (evidence not built yet) |
| `python -B capture_build_camera.py` | 2346 frames, 640x360 @20fps, capture.mp4 sha `e3129099...` — BYTE-IDENTICAL to the archived PASS-reviewed capture; gate `structurally_valid: true` (`CAMERA_METADATA_STRUCTURE_ONLY`), exit 0 |
| `python -B -m unittest test_camera_profile_probe -v` (post-build) | 8/8 OK, 0 skipped |
| pinned suite (inside probe, recorded in runtime_receipt) | 24/24 OK, 0 failures, 0 errors |
| latency (wall clock, reported separately per pinned C12/FD law) | max subject 0.60 ms vs 50 ms budget |

Check names all green: C1_ground_follow_law_motion_visible,
C2_controls_focus_loss_no_stuck, C3_settle_law, C4_pole_episode_oc1_oc6,
C5_trunk_approach_oc3_close_target, C6_oc4_static_noop_and_tapering_settle,
C7_oc5_height_aware_flyover, C8_oc3b_honest_degrade_and_zero_concealed,
C9_oc2_oc7_pullin_largest_feasible, C10_never_moves_the_animal_oc8,
C11_ff_speed_clamp_declared_reframes_only, C12_fg_apply_echo,
C13_fd_latency_budgets, C14_fe_framing_and_quaternion_unit,
C15_pinned_suite_24_tests.

Clause coverage: "motion on ground" -> C1 (ground patch + anchor subtend
< 22.5 deg); "motion at trunk" -> C5 (two-point close-target framing, anchor
AND trunk contact subtend < 22.5 deg every trunk tick); "avoids tested
obstruction cases" -> OC1-OC8 via C4, C6, C7, C8, C9 + pinned suite re-run;
"never moves the animal" -> C10 stream audit (zero allowlist violations, zero
forbidden routes, pan exactly 0.0, exactly 8 camera fields, zero undeclared
engine-double attempts, harness-owned anchor stream).

## 5. Honest deviations and errata (nothing smoothed)

1. Three prereg sub-clause BOUNDARY mispredictions fired again, byte-for-byte
   the same three recorded in the archived reviewed run, and are preserved
   FIRED in `numerical_receipt.prediction_deviations` (settle-tail writes
   taper instead of ceasing; 85 degraded ticks exactly where the smoothed aim
   sits inside an obstacle optical margin; avoidance onset on the smoothed
   sight-line lags the raw-anchored window). The prereg itself declares these
   recorded-not-smoothed; the laws (C3/C8/C4) are green.
2. ERRATUM to the frozen PREREGISTRATION header (frozen file left untouched):
   its port-audit sentence cites estimated diff counts ("20/9/2 changed
   lines"); exact measured counts are 17 removed/22 added (probe), 5/5
   (builder), 1/2 (tests). Descriptive-sentence error only; no prediction,
   law, threshold, timeline, scene or bound is affected.
3. Receipt/manifest bytes legitimately differ from the archived ones
   (identity strings + live wall-clock latency samples); trace.jsonl and
   capture.mp4 are byte-identical. visual_gate.py (13cf07f4, master
   e3be713b) and visual_capture.py (5ee55d5a, committed at base 9ba1be77)
   were imported read-only from the on-disk source tree; both byte-equal
   their committed blobs (verified by hash before use).
4. The pinned suite re-run overwrites
   `reference/.../U02_camera/receipts/latency_run.json` with a live-latency
   receipt (observed here; the committed tree briefly carried the overwritten
   bytes during staging). Restored byte-exact to the pinned
   `440d7a9d...` after verification — the same restore-after-verify practice
   the archived PASS review records ("candidate committed receipt/latency
   files restored after verification so the review tree is clean at head").
   The committed candidate tree contains the PINNED bytes, not the live ones.

## 6. Honest boundary (unchanged from the merged acceptance)

Pixels are a deterministic CPU visualization of the recorded headless trace
of the pinned camera subject — NOT native engine frames; no V03 native
checkpoint or human visual acceptance is claimed here. The obstruction model
is the declared injected cylinder scene (unmodeled obstacles can still
occlude). Component-level boundary preserved exactly as the lead ACCEPTED it
for ONT-U02; the native integration checkpoint V03 remains with the
integration lane (dependencies for final acceptance: P01, P03 — both DONE).

## 7. Remaining gates (not claimable by this candidate)

Independent review of THIS port; lead ACCEPTED review passing
`qualification_receipt.json` with head_sha set to the exact reviewed head;
exact-head PR publication to `review/MAT2-U02` (lead-serialized); V03 native
integration; downstream runtime cards. Writes stopped after the candidate
commit; artifacts hash-bound in the publication request.
