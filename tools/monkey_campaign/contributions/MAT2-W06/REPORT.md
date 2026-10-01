# REPORT — MAT2-W06 the frozen per-seed evaluation of the walk1m-r1 trained walking outcomes

Generated from the receipts; no hand-transcribed numbers (P2/P3). Profile: walking/motion; numerical evidence required (the receipts); the profile-conformant capture is the MOTION REPLAY of the sealed certified line (addendum 1; G4/G8 details below) — zero training, zero tuned runs, zero evaluation rollouts of the trained candidates.

## done_when verification (verbatim clause -> evidence)

done_when (verbatim): "Frozen walking success/failure metrics reported per seed without cherry-picking or additional tuned runs".

| clause | outcome | evidence |
|---|---|---|
| frozen metrics per seed | REPORTED for all 3 seeds | the M1-M6 table below, recomputed from the pinned curves and cross-checked bit-exactly against the sealed receipts |
| without cherry-picking | HELD | seed set completeness 3/3; held-out matrix 9 cells (6 off-diagonal held out); FB3 bite arms prove the completeness detectors fire on dropped seeds/cells |
| without additional tuned runs | HELD (structural) | zero training runs, zero tuned runs, zero evaluation rollouts of the trained candidates (receipt field `no_runs_law`); the ONE declared capture replay of the sealed certified line (addendum A1; ALLOW(frozen) relation, anchors EXACT) produces no outcome number any verdict reads; FB5 AST scan over the whole contribution finds 0 undeclared run paths; the training executor itself has no retry path (FB5/W05) |
| a failed result is not an implementation success | APPLIED | all 3 seeds FAIL the frozen training-signal criterion; the failure is the honest REPORTED outcome this card is graded on |

## Identity

- Card MAT2-W06 (planning id W06), agent `wk-w06-eval`, attempt `a5ccec3526f344438a1cc484cae1bd58`.
- Criteria sha256 `2b9478cb28462c029f9d51267f933474878ba78438e4be88a5a3707808850d26` (join == registry read-only re-read; card state at run time: REVIEW, registry revision 1623).
- Base: `af751aa5` (the MAT2-W05 merge, PR #297; the sealed W05 outcomes are pinned AT THEIR MERGED IN-TREE PATHS — 36 input pins, all byte-exact).
- Preregistration sha256 `31d43b67132b2a4fe0167be0297193734e0a8d2bca929ac8607157b72d53a87e` (committed separate-first, BEFORE any evaluation receipt — the M03/P04 law).
- Under evaluation: runbook `walk1m-r1` (schema chimera.w05_runbook.v1), executed by MAT2-W05 (attempt `ce1576896a454f109a52de3a136c5117`) on seeds [20260919, 20260920, 20260921].
- Upstream freeze: the W04 freeze manifest (sha `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`) froze the slot the runbook filled; the criteria applied here are quoted from that frozen lineage — this card introduces no criterion of its own.

## The frozen per-seed metric table (M1-M6; all seeds; failures retained)

Recomputation identity (declared in the prereg): M4 is `np.mean` over the f_plus column, slices [:100] and [-100:] — the executor's own float semantics; every M4 value below is BIT-EXACT against the sealed receipt field (E2).

| seed | status | M4 first100 (m) | M4 last100 (m) | M4 improved | M1 final-window dx (m) | M2 mean speed (m/s) | M3 max |v| (envelope m/s) | M5 saturation | M6 curve sha (12) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 20260919 | EXECUTED_COMPLETED | 15.44039271957343 | 11.444787669784418 | false | 8.894332472928278 | 0.7115465978342622 | 0.8999990977122645 (2.977443609022557)  | 0.0 | d2e8de96d28a | **FAILURE** |
| 20260920 | EXECUTED_COMPLETED | 15.686209528073409 | 11.422063862161158 | false | 8.872841644128576 | 0.7098273315302861 | 0.897132456507337 (2.977443609022557)  | 0.0 | 5b19d59b9f9f | **FAILURE** |
| 20260921 | EXECUTED_COMPLETED | 15.46322027908788 | 11.435178660784368 | false | 8.925413122530959 | 0.7140330498024767 | 0.9048679008874374 (2.977443609022557)  | 0.0 | 704038c30350 | **FAILURE** |

THE HONEST OUTCOME (prereg prediction E1, observed): **all 3 seeds FAIL the frozen training-signal criterion** — training DEGRADED mean iteration fitness from its first-100 to its last-100 window on every seed (approx 15.44039271957343 -> 11.444787669784418 on seed 20260919, with the same sign of degradation on every seed; see the table). No seed improved; the walk1m-r1 training outcomes are NEGATIVE on the full registered seed set. Per the observation law, this failed result is reported as a failure — it is not an implementation success and it is not hidden, retried or averaged away (the no-runs law forbids the retry).

Integrity receipt per seed (I1-I4): status 20260919 EXECUTED_COMPLETED, termination_code null; 20260920 EXECUTED_COMPLETED, termination_code null; 20260921 EXECUTED_COMPLETED, termination_code null. The executor's status law retains any hard-gate breach as a termination record; no termination code exists on any seed.

## Predictions (registered BEFORE the evaluation receipts; disclosed either way)

- E1_all_seeds_fail_training_signal: predicted true, observed true.
- E2_bit_exact_recomputation: predicted true, observed true.
- E3_receipts_complete: predicted true, observed true.
- E4_trained_blocked_from_deploy: predicted true, observed true.

## The card falsifier, mapped to receipt evidence

Card falsifier (verbatim): "Sliding/penetration, unsupported propulsion, hidden reset, wrong command response or diagnostic/clean state divergence fails." — evaluated at the receipt level (the runbook's hard-gate termination records are the detectors); NONE fired on any seed:

| falsifier class | receipt-level detector | fired? |
|---|---|---|
| sliding/penetration | contact_floor gate; no contact_floor_breach termination exists | no |
| unsupported propulsion | velocity_envelope gate; no envelope_breach termination exists | no |
| hidden reset | no_intervention gate + the continuous 4096-tick state-chain anchoring; no intervention_observed termination exists | no |
| wrong command response | bounds_honored gate; no bounds_breach termination exists | no |
| diagnostic/clean state divergence | the recipe-equivalence receipt: the trainable controller class reproduced the frozen policy applied bytes tick-for-tick (trajectory sha cd4944d9...) | no (byte_identical: true) |

Baseline anchors of the retained certified line (the relation the trained outcomes are read against): final_state_sha256 EXACT; initial_snapshot_sha256 EXACT; trajectory_sha256 EXACT.

## Held-out evaluation (C10; separate train/evaluation cases)

All 9 cells receipted (6 off-diagonal held out); per-theta generalization deltas (diagonal minus off-diagonal mean, m; receipt field `diag_minus_offdiag_mean`): seed 20260919 0.0005893194163353321; seed 20260920 -0.00041962182740462595; seed 20260921 -1.701672507037344e-05.

| theta seed | scene seed | held out | fitness (m) | mean speed (m/s) | max |v| |
|---|---|---|---|---|---|
| 20260919 | 20260919 | false | 2.4519699186819754 | 0.4903939837363951 | 0.7615615310830239 |
| 20260919 | 20260920 | true | 2.451395184387545 | 0.490279036877509 | 0.7614270501926432 |
| 20260919 | 20260921 | true | 2.451366014143735 | 0.490273202828747 | 0.7614239282955511 |
| 20260920 | 20260919 | true | 2.4502160222955607 | 0.49004320445911215 | 0.7606012044016266 |
| 20260920 | 20260920 | false | 2.4496159767225167 | 0.48992319534450335 | 0.7605040138661803 |
| 20260920 | 20260921 | true | 2.4498551748042816 | 0.4899710349608563 | 0.7608914440538379 |
| 20260921 | 20260919 | true | 2.457445688796291 | 0.4914891377592582 | 0.7635010047686593 |
| 20260921 | 20260920 | true | 2.457432864046284 | 0.49148657280925684 | 0.7634925786889509 |
| 20260921 | 20260921 | false | 2.457422259696217 | 0.49148445193924345 | 0.7634866343289674 |

## Deploy-gate treatment of the trained thetas (C10; the frozen gate)

- The certificate's own relation: ALLOW (the gate still closes on the certified tuple).
- The trained bundle tuple: BLOCK — reasons: ["BLOCKED: compatibility key mismatch -- the request's 5-tuple (5006d524d76c2d90...) is NOT the certificate's (dbda388b4797cfaa...); the bundle/build/runtime/body/suite is not the certified one"].
- A foreign build: BLOCK — reasons: ["BLOCKED: compatibility key mismatch -- the request's 5-tuple (fc3cd885d79fbd5d...) is NOT the certificate's (dbda388b4797cfaa...); the bundle/build/runtime/body/suite is not the certified one"].
- TREATMENT APPLIED BY THIS EVALUATION: the trained thetas (npz shas eacdafdb1de9, 89df7ac6ca3c, 7b11dd01f849) are NON-DEPLOYABLE training candidates: the frozen deploy gate BLOCKs their tuple (compatibility-key mismatch against the sealed W04 certificate). They are evaluated as OFFLINE training outcomes only; they bind ONLY by reissuance through the TC-6 gate; FC-3 (trained walking policy) stays explicitly-unresolved. This card deploys, re-certifies and re-issues nothing.

## The no-runs law (structural; addendum A4 vocabulary)

- Training runs executed by this card: 0; tuned runs: 0; evaluation rollouts of the trained candidates: 0; declared capture replays of the sealed certified line: 1 (the addendum A1 arm; anchors EXACT; no outcome number of this evaluation reads it).
- FB5 AST scan over every contribution .py (three declared classes: training/run-launch paths everywhere; the pinned replay import and the ffmpeg capture-tool calls only inside the declared run_replay_capture.py): 0 violations; the bite arms prove the scanner fires on each class.
- The per-seed verdicts remain PROOF-READINGS of the sealed W05 record (sha-pinned inputs), not new measurements.

## Named checks (G12 accounting)

- Suite: test_w06_evaluation.py (unittest discover -p test_*.py).
- Accounting claim: **33 executed, 0 skipped**; known skips: none (zero skips by design; no KNOWN_SKIPS entries); pass: true.

## Capture (profile walking/motion; the profile-conformant MOTION replay)

Delivered per prereg addendum 1 (committed BEFORE the capture; the M03/P04 law): the SEALED CERTIFIED BASELINE LINE re-executed through the UNMODIFIED pinned machinery — frozen P3 policy closed loop, build cpu-walk-scene-build-N, seed 20260920, 900 ticks — the deploy gate's ALLOW(frozen) relation. The BLOCKED trained thetas are never loaded (structural: the generator never references them). VALIDITY INSTRUMENT: the three W05 baseline anchors reproduce EXACTLY (final_state_sha256 EXACT; initial_snapshot_sha256 EXACT; trajectory_sha256 EXACT) — every frame is by construction a view of the sealed line's own trajectory; any drift would have been the named refusal `baseline_drift:<key>` with NO capture emitted.

- tick_interval: [0, 899] (t0 < t1; 1 tick = 1/300 s).
- Frames: 60 at the pinned runner's decision boundaries (stride 15 ticks), each a sheet of the three profile views (diagnostic band on top, clean band below, SAME recorded state per row); video 10 fps; ffmpeg: ffmpeg version 8.1.1-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers.
- Media: `capture_replay.mkv` (FFV1 level 3, g=1, bitexact), capture sha256 `d32fafdbffe492170519ef7985b7c38f619d367df12a63c56e52b8a747011d44`; G4: the decode is pixel-exact against the rendered stills on ALL 60 frames, and the frame-order sensitivity check passes.
- Trace binding (motion state_binding.kind == 'trace'): `trace.json` sha `15bf0b4c47ba208366b4bf7cd77775d434c836b70c992e198c51aa9012e1d535` — the per-tick sealed telemetry (com, phases, contacts, forces, pad gaps, applied commands) plus the pinned state-chain events; subject receipt `replay_receipt.json` sha `c8ba8705560a148c82922efd2f194d29378c672a065eea97692900c42d32cd8d`.
- Replay integrity (addendum R2, over all 900 ticks): contact_count min 4 (gate >= 2); max |v| 0.8737777695842058 m/s (envelope 2.977443609022557 m/s); intervention none everywhere; 60 state-chain events continuous (no hidden reset). The stance/swing alternation of the recorded pads is visible in the side view and close-up; the command and tick overlay shows the frozen policy's own command stream (start/stride = speed, phase offsets = turn).
- Validator: CAMERA_METADATA_STRUCTURE_ONLY, structurally_valid true, views 6, visual_acceptance false — independent visual review remains the Sergeant's.
- Honesty: the scene of record is the DECLARED SURROGATE CPU walk scene (its own module docstring and the W04 certificate say so); the rigid skeleton of a full articulated body is NAMED ABSENT (the surrogate records phases/contacts/forces, and the diagnostic `skeleton` layer renders the recorded phase state — never invented geometry); no claim about the C++ engine or the adopted assembly is made; the native visual walk claim belongs to the W07 runtime-consumption card.
- RETIRED from the capture manifest (named, not silent): the first capture's static record-space rasters — the format validator forbids image rows under a motion profile (every row must be video-located). They remain in the attempt workspace and the evidence store as ADDITIONAL evidence; the metric tables they rendered remain in this report as receipt-rendered text.

## Gate disclosure (G1-G12)

- G1 falsifier arms with clean controls and bites: FB1 pin bite, FB2 recompute bite, FB3 cherry-pick bites (seed set + held-out cell), FB4 deploy-gate bite, FB5 no-runs structural scan + bites, FB6 verdict-purity bite — all executed in the named-check suite.
- G2 lint: `python -B lint_report_numbers.py --selftest` must exit 0; every number in this report traces to the bound artifacts.
- G3: this report is GENERATED from the receipts; no hand-written qualitative claim.
- G4/G8: delivered as the profile-conformant MOTION replay capture above (tick_interval [0, 899]; FFV1 mkv; trace-bound; camera vocabulary per the closed validator; NOT engine frames — the surrogate scene is declared, with the absent inventory named).
- G5: `refuse_vacuous_comparison` + `vacuous_guard_selftest()` run at import and guard every relative-window comparison (M4 windows, M3 envelope, held-out deltas).
- G6: keyed extractors; the frozen iteration windows are the receipts' own keyed fields; this card adds no phase definitions.
- G7: registry identity read-only (card state REVIEW, revision 1623); criteria sha identical across join/registry/prereg/checks.
- G9: prereg committed separate-first; ONE publication commit on `review/MAT2-W06` with the full lineage; contribution within the file/size bounds; commit-message metrics generated from these FINAL receipts.
- G10: every pin below hashes against the on-disk file at its card-relative path (batch gate pin_vs_disk).
- G11: every commit in the candidate chain carries `Agent: wk-w06-eval` (chain scoped from the prereg's parent).
- G12: "33 executed, 0 skipped" (zero skips by design).

## Evidence pins (G10: every pin hashes against the on-disk file)

- PREREGISTRATION.md | 31d43b67132b2a4fe0167be0297193734e0a8d2bca929ac8607157b72d53a87e
- PREREGISTRATION-ADDENDUM-1.md | dea6b825774b0770100a81c482fb08082397ae740f23034954454c2a6df9caba
- checks_receipt.json | 7e4891be165ce9113c3bf7b319e2ab5bb0ac34ec76994264e5339c172c1439b2
- receipts/input_pins.json | 6740532e6159ebe6493527ed8908f5041841510e29fb344c14a05467382902c1
- receipts/evaluation_summary.json | a1af58baf15edd7ac595b5bb4571e13ed44780f77faf5a761355140f456b075a
- capture/capture_manifest.json | 6b696efa76b1e9e0a8d3a5ff4f7cbd0a248e65f843d1f8f1ded4d7d29516f181
- capture/capture_context.json | 7cbc302efe15fad78e1fae557fbfd610c1a77756b697437bcc75567cc4afe390
- capture/capture_validation_receipt.json | 335a9091071eea6e4881b797094890d792192edc4f0febd6ba6ea0b9d41c003e
- capture/replay_receipt.json | c8ba8705560a148c82922efd2f194d29378c672a065eea97692900c42d32cd8d
- capture/trace.json | 15bf0b4c47ba208366b4bf7cd77775d434c836b70c992e198c51aa9012e1d535
- capture/frame_hashes.json | be88b5381ab0c814845fcbc7ea99219f704db9695b3ad937856cd965f017f443
- receipts/seed_20260919_evaluation.json | d49b83d7682e77efbfedb44b99f2366a5eef7d842b8fd12c2431f563ea432d4f
- receipts/seed_20260920_evaluation.json | 1ee769fd995ddc38d9b2bc95af45d380400a2fcbf81053cca92486d6602a4b6c
- receipts/seed_20260921_evaluation.json | 89baa5472076a1a8669389bc207fd49e6b06645b6db2519ca5d333cafe26015b
- upstream pins (at their merged in-tree paths; verified by verify_inputs.py, 36/36 byte-exact): see the pin verification record in the attempt scratch and PREREGISTRATION.md section 1.

## Honest limitations (named, not skipped)

- The per-seed evaluation is RECORDS-ONLY: it proves what the sealed W05 run recorded and nothing about unrecorded quantities. The TRAINING rollouts retained no trajectory bytes (the runbook's streaming-chain law), so no per-seed motion capture of the TRAINED candidates exists or may be produced without a new training run — which the no-runs law forbids.
- The motion replay capture is of the SEALED CERTIFIED BASELINE LINE (the frozen P3 policy; the deploy gate's ALLOW relation), not of the trained candidates: it demonstrates the profile procedure on the only line the deploy gate admits, and its per-tick telemetry is the trace-bound evidence. It is NOT a picture of the trained policies' behavior.
- The scene of record is the DECLARED SURROGATE CPU walk scene; the rigid skeleton of an articulated body is NAMED ABSENT (the diagnostic `skeleton` layer renders the recorded phase state; no geometry is invented). No C++ engine or adopted-assembly claim is made; the native visual walk claim belongs to W07.
- The M4 window metric is the f_plus (positive-perturbation) evaluation mean — the executor's own frozen definition, reproduced bit-exactly here; the f_minus column is carried in the pinned curves (M6) and rendered in the retired record-space rasters, and the frozen criterion does not read it.
- The trained thetas remain BLOCKed training candidates; no claim about FC-3 changes. A future accepted walking policy requires a re-trained run that actually improves the frozen criterion plus reissuance through the TC-6 gate — neither is this card's scope, and the no-runs law forbids this card from attempting either.
- Registry revision is read at run time and recorded; it is a live field (the F03 F-1 law: the suite asserts only attempt-immutable identity).

