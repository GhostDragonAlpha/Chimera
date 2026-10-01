# REPORT — MAT2-W06 the frozen per-seed evaluation of the walk1m-r1 trained walking outcomes

Generated from the receipts; no hand-transcribed numbers (P2/P3). Profile: walking/motion; numerical evidence required (the receipts); clean view + camera record delivered as the declared record-space raster (G4/G8 honesty label and absent inventory below) — this card EXECUTES ZERO RUNS (no training, no evaluation rollout, no tuned run).

## done_when verification (verbatim clause -> evidence)

done_when (verbatim): "Frozen walking success/failure metrics reported per seed without cherry-picking or additional tuned runs".

| clause | outcome | evidence |
|---|---|---|
| frozen metrics per seed | REPORTED for all 3 seeds | the M1-M6 table below, recomputed from the pinned curves and cross-checked bit-exactly against the sealed receipts |
| without cherry-picking | HELD | seed set completeness 3/3; held-out matrix 9 cells (6 off-diagonal held out); FB3 bite arms prove the completeness detectors fire on dropped seeds/cells |
| without additional tuned runs | HELD (structural) | zero runs of any kind executed by this card (receipt field `no_runs_law`); FB5 AST scan over the whole contribution finds 0 run paths; the executor itself has no retry path (FB5/W05) |
| a failed result is not an implementation success | APPLIED | all 3 seeds FAIL the frozen training-signal criterion; the failure is the honest REPORTED outcome this card is graded on |

## Identity

- Card MAT2-W06 (planning id W06), agent `wk-w06-eval`, attempt `a5ccec3526f344438a1cc484cae1bd58`.
- Criteria sha256 `2b9478cb28462c029f9d51267f933474878ba78438e4be88a5a3707808850d26` (join == registry read-only re-read; card state at run time: OPEN, registry revision 1616).
- Base: `af751aa5` (the MAT2-W05 merge, PR #297; the sealed W05 outcomes are pinned AT THEIR MERGED IN-TREE PATHS — 21 input pins, all byte-exact).
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

## The no-runs law (structural)

- Physics runs executed by this card: 0; training runs: 0; tuned runs: 0.
- FB5 AST scan over every contribution .py: 0 run-path violations (scene/policy/training imports, subprocess, socket); the bite arms prove the scanner fires on each class.
- Every number in this report is therefore a PROOF-READING of the sealed record (sha-pinned inputs), not a new measurement.

## Named checks (G12 accounting)

- Suite: test_w06_evaluation.py (unittest discover -p test_*.py).
- Accounting claim: **28 executed, 0 skipped**; known skips: none (zero skips by design; no KNOWN_SKIPS entries); pass: true.

## Capture (profile walking/motion; the record-space delivery)

- Honesty label: RECORD-SPACE RASTER of pinned receipts - not engine frames; native pose/contact trajectory records inventoried ABSENT (runbook trajectory_retention NONE; streaming chain hashing only).
- Frames: 6 (3 record-space views x diagnostic/clean); capture sha256 `60067a31bed04afea234f7c4de2d8999a14182cf331ac0fac753c6b6dd914076` (sha256 over the concatenation of the frame PNG bytes in sorted frame_files order (the B03 image-set convention)).
- Subject identity on every row (clean AND diagnostic): composite evaluation-record sha `e6cc53fbc9b025724715236ed2e6e742331c1f7b52560e1eb6d2222dc1d69e90` — view toggles preserve the record identity (the profile falsifier's instrument); all rows structure-OK: 6/6; validator CAMERA_METADATA_STRUCTURE_ONLY; visual_acceptance false (independent visual review remains the Sergeant's).
- Absent inventory (named, never imputed): ["native pose/contact trajectory records (the runbook retains NONE: streaming chain hashing only) - the three profile views are delivered as declared record-space panels of the pinned outcome receipts, never as invented bodies", "native camera frames (no runtime session exists in this lane; the native visual walk claim belongs to the W07 runtime-consumption card)"]

## Gate disclosure (G1-G12)

- G1 falsifier arms with clean controls and bites: FB1 pin bite, FB2 recompute bite, FB3 cherry-pick bites (seed set + held-out cell), FB4 deploy-gate bite, FB5 no-runs structural scan + bites, FB6 verdict-purity bite — all executed in the named-check suite.
- G2 lint: `python -B lint_report_numbers.py --selftest` must exit 0; every number in this report traces to the bound artifacts.
- G3: this report is GENERATED from the receipts; no hand-written qualitative claim.
- G4/G8: delivered as the record-space raster above (camera field vocabulary complete per row; NOT engine frames — named, with the absent inventory).
- G5: `refuse_vacuous_comparison` + `vacuous_guard_selftest()` run at import and guard every relative-window comparison (M4 windows, M3 envelope, held-out deltas).
- G6: keyed extractors; the frozen iteration windows are the receipts' own keyed fields; this card adds no phase definitions.
- G7: registry identity read-only (card state OPEN, revision 1616); criteria sha identical across join/registry/prereg/checks.
- G9: prereg committed separate-first; ONE publication commit on `review/MAT2-W06` with the full lineage; contribution within the file/size bounds; commit-message metrics generated from these FINAL receipts.
- G10: every pin below hashes against the on-disk file at its card-relative path (batch gate pin_vs_disk).
- G11: every commit in the candidate chain carries `Agent: wk-w06-eval` (chain scoped from the prereg's parent).
- G12: "28 executed, 0 skipped" (zero skips by design).

## Evidence pins (G10: every pin hashes against the on-disk file)

- PREREGISTRATION.md | 31d43b67132b2a4fe0167be0297193734e0a8d2bca929ac8607157b72d53a87e
- checks_receipt.json | 0c1a14c50c9713925f5d7892ddc036e83eb511a2084265a88a1ad0f0af06709b
- receipts/input_pins.json | f62b32455be1abd4cd45982cf01485999e8e61fa433831fdd249eb317bf66144
- receipts/evaluation_summary.json | 3ddd5cc5bd596d107cfd42aa7cc8679654a0260fb04a5831ff825788b2a88cc2
- capture/capture_manifest.json | 0eeb6f4048402ecf5eaea5e9aec2404aa6f61f55e7cd25c0d08f08e99ccabdda
- capture/capture_context.json | 49caf4f048f42ca8f174c0743eef4026b1b9c4a52ad2a5d5bb2d36fb99659278
- capture/capture_validation_receipt.json | 8ce8866d5cff1081079b08a6047fe7cead91eb3c5156a68801fea144a423e3a8
- receipts/seed_20260919_evaluation.json | d49b83d7682e77efbfedb44b99f2366a5eef7d842b8fd12c2431f563ea432d4f
- receipts/seed_20260920_evaluation.json | 1ee769fd995ddc38d9b2bc95af45d380400a2fcbf81053cca92486d6602a4b6c
- receipts/seed_20260921_evaluation.json | 89baa5472076a1a8669389bc207fd49e6b06645b6db2519ca5d333cafe26015b
- upstream pins (at their merged in-tree paths; verified by verify_inputs.py, 21/21 byte-exact): see the pin verification record in the attempt scratch and PREREGISTRATION.md section 1.

## Honest limitations (named, not skipped)

- This evaluation is RECORDS-ONLY: it proves what the sealed run recorded and nothing about unrecorded quantities. Native pose/contact trajectories were never retained by the runbook, so the profile's native views cannot be rendered from evidence — the absent inventory is declared in the capture manifest, not imputed.
- The M4 window metric is the f_plus (positive-perturbation) evaluation mean — the executor's own frozen definition, reproduced bit-exactly here; the f_minus column is carried in the pinned curves (M6) and rendered in the capture, and the frozen criterion does not read it.
- The trained thetas remain BLOCKed training candidates; no claim about FC-3 changes. A future accepted walking policy requires a re-trained run that actually improves the frozen criterion plus reissuance through the TC-6 gate — neither is this card's scope, and the no-runs law forbids this card from attempting either.
- Registry revision is read at run time and recorded; it is a live field (the F03 F-1 law: the suite asserts only attempt-immutable identity).

