# PREREGISTRATION — MAT2-W06 the frozen per-seed evaluation of the walk1m-r1 trained walking outcomes

Frozen BEFORE any evaluation receipt exists. This file is committed ALONE
(separate-first; the M03/P04 law identity bound in the W04 freeze). Every
emitted receipt refuses any document whose `preregistration_sha256` does not
match these live bytes.

- Card MAT2-W06 (planning id W06, wave 7), agent `wk-w06-eval`, attempt
  `a5ccec3526f344438a1cc484cae1bd58`, attempt workspace
  `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W06\a5ccec3526f344438a1cc484cae1bd58`,
  publication branch `review/MAT2-W06`, PR base `astra/gait-capture`.
- Criteria sha256 `2b9478cb28462c029f9d51267f933474878ba78438e4be88a5a3707808850d26`
  (startup join == registry `kanban.cards[MAT2-W06].criteria_sha256`,
  re-read READ-ONLY (`file:...?mode=ro`) from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` at attempt start;
  mismatch = refusal `criteria_pin_mismatch`).
- done_when (verbatim, registry): "Frozen walking success/failure metrics
  reported per seed without cherry-picking or additional tuned runs".
- Observation (verbatim, registry): "Use existing runbook; a failed result is
  not an implementation success".
- Card task falsifier (verbatim): "Sliding/penetration, unsupported
  propulsion, hidden reset, wrong command response or diagnostic/clean state
  divergence fails."
- Profile: `walking`/`motion`; numerical_evidence_required true;
  clean_view_required true; the full camera record is delivered per the W04
  record-space precedent (section 5c) with the absent inventory named.
- Base: `af751aa5` = `origin/astra/gait-capture` tip at join (the MAT2-W05
  merge, PR #297; board revision 1613). Candidate branch:
  `codex/monkey-mat2-w06-a5ccec352` (the join's nominal `branch-1` is held by
  the PRESERVED MAT2-W04 attempt checkout; worktrees cannot share a branch
  and another lane's state is never touched — recorded deviation, not a
  silent one; same recorded deviation as the W05 attempt).
- Composed against CARD_STARTER v3 and the house standards:
  `IMPLEMENTER_CHECKLIST.md` (G1-G9) + `TOOLKIT.md` (P1-P9), cited at the
  candidate commit. Dispatch brief:
  `E:/ChimeraWork/monkey-coordination/gap-analysis/wave-7.md` (MAT2-W06
  section).

## 0. The governing frame (what this attempt composes against)

This card EVALUATES; it trains nothing. The outcomes under evaluation were
produced by MAT2-W05 (attempt `ce1576896a454f109a52de3a136c5117`, sealed at
rev 1613 by PR #297) executing the frozen runbook `walk1m-r1` on the three
prescribed seeds. The W05 preregistration section 2B froze the success
metrics as "W06's evaluation input, NOT gate conditions of this card" and
bound the sentence "a failed result is not an implementation success" to
W06 — this card is where that sentence executes.

- TC-10 / FC-4: the runbook identity, seeds and acceptance criteria were
  frozen BEFORE the W05 run (W04 freeze manifest sha
  `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`, slot
  filled by W05's `w05_freeze_fill.json`); "no criteria edits after W04
  froze them" — this card edits nothing. Every criterion applied here is
  quoted from the pinned upstream documents, never introduced by this card.
- BQ-1 (CPU walk backend): the evaluated run was CPU-only; this evaluation is
  CPU-only records work; no GPU work exists in this lane.
- FC-3 / TC-9 (trained walking policy): EXPLICITLY UNRESOLVED upstream and
  unchanged here. The trained thetas are training CANDIDATES bound ONLY by
  reissuance through the TC-6 gate; the frozen deploy gate BLOCKs their
  bundle tuple (compat key mismatch against the sealed W04 certificate). This
  card reports that ruling; it does not deploy, re-certify or re-issue
  anything.
- The no-runs law (the done_when's "without additional tuned runs"): this
  attempt executes ZERO physics runs — no training run, no evaluation
  rollout, no tuned run, no retry of any seed. Every reported number is
  recomputed from the PINNED recorded artifacts (the fitness curves and
  receipts) by deterministic arithmetic, or quoted from a pinned receipt
  field with its sha. A named check structurally asserts the evaluator
  cannot launch runs (FB5, section 5).

OUTCOME-INDEPENDENCE DISCLOSURE (recorded, not hidden): the dispatch
required reading the W05 REPORT.md and evidence before this prereg, and that
report is sealed public record at the base commit. The defense against
outcome bias is structural, not procedural: (a) the metric set is NOT
selected by this card — it is the upstream-frozen set (K01: metrics approved
before training; W05 prereg 2B frozen before the W05 run), quoted verbatim
below; (b) every input artifact is sha-pinned in section 1 BEFORE evaluation
and any drift is the named refusal `input_pin_mismatch`; (c) the evaluation
is mechanical — exact recomputation, structural completeness, and verdicts
that are pure functions of pinned bytes; this card introduces no threshold,
no window, and no substitute metric.

## 1. Input pins (verified byte-exact at attempt start; drift = refusal `input_pin_mismatch`)

All W05 outcome artifacts are pinned AT THEIR MERGED IN-TREE PATHS
(`tools/monkey_campaign/contributions/MAT2-W05/...` at base `af751aa5`) —
the sealed published bytes, not workspace copies:

- `runbook.json` `f173a1c5993929e10bac3365a46739aad0f9856b640b5de66ae06eaac2e1d6b0`
- `w05_freeze_fill.json` `258749b826bc1dcd86d2b3a127606e11792c3b014d904f0e105cea124a48bf63`
- `PREREGISTRATION.md` `260c6d53e66c79689e95b5f880c1f6828f5316d4d7d6e172132296137d3f1c2a`
- `PREREGISTRATION-ADDENDUM-1.md` `a257826f26936f4bf388d140ff7158eac851a0c9dae4ca01a9db3a6abdd886d7`
- `checks_receipt.json` `69e315a1e1aa54eb0221127acd7e4a93ff9036eaedade1f21d6170ae68683677`
- `receipts/baseline_receipt.json` `6ede18c05e9cd31b9c6cf493bfe471a1711439980dbe55723dfe4fc6f4bc3bb2`
- `receipts/recipe_equivalence_receipt.json` `bbb6dbd34dff0d9f8a3f4940e947eba428b330f25bff3c15b7fcbdb7bbf22bdd`
- `receipts/heldout_receipt.json` `4deff1a2efec7112b975230fba24fa8818715fc378f453654e57a5cb05fce4f1`
- `receipts/deploy_check_receipt.json` `766a7cbe6a2ccd67c739d82af5b32e859ee4bc3f3a558715fafc63dbab0ae635`
- `trained/trained_policy_manifest.json` `02538194cad7f200985e628c55c86fb3fb6d2b76bfb6b44220fab7d32343571e`
- `receipts/seed_20260919_receipt.json` `b866e9b1e2a3d516a960a88362c95d2f8211d28b894cc4d8c16dcebc4dc8b896`
- `receipts/seed_20260919_curve.json` `56e645a2a6ba7b594e0d98ab682c169e5132bca70abc233aa67eae19548fb450`
- `trained/theta_20260919.npz` `eacdafdb1de9034a39084f4fd81eaad8c4d3d9a09496c9d6b6758e2391388589`
- `receipts/seed_20260920_receipt.json` `3d795b5ca523289c1ceac7dac72070875d8cc4b8e24e4ac2a5a64a9733e766ff`
- `receipts/seed_20260920_curve.json` `185ac6e3afa5b891d4032256f59c1340421ae7c649ed5cac173adc18c2e4835c`
- `trained/theta_20260920.npz` `89df7ac6ca3c94c547be5692da55c98e0e510050ff0b1e8df6912f2bb4d949aa`
- `receipts/seed_20260921_receipt.json` `10c4090473c75ec99559dd9f1f13729d96c3c7d5cf037569c63253e308f472af`
- `receipts/seed_20260921_curve.json` `145b2eb6069913719f7a1f575fad76a32764127ae62b736ad5209c2ce0c09972`
- `trained/theta_20260921.npz` `7b11dd01f8495068f46def84a072d211fe47b778bfc0fbc3f53fe3e82a7fe1a7`
- `E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W04/numerical/w04_freeze_manifest.json` `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`
- `E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W04/numerical/w04_certificate.json` `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`

## 2. THE FROZEN EVALUATION METRIC SET (per seed; verbatim identities from the pinned upstream documents)

The six frozen success metrics (W05 prereg section 2B / runbook
`acceptance_criteria.success_metrics_reported_not_gated`), each reported for
EVERY seed [20260919, 20260920, 20260921]:

- M1 total forward displacement (m) — pinned receipt field
  `final_window.total_dx_m`.
- M2 mean com speed (m/s) — `final_window.mean_speed_m_s`.
- M3 max |v| vs envelope — `final_window.v_max` against
  `velocity_envelope_m_s` (2.977443609022557 m/s; derived, never hardcoded
  upstream; quoted here as the receipt carries it).
- M4 mean decision reward (m/decision), first vs last 100 iterations —
  receipt fields `success_metrics.mean_iteration_fitness_first100` /
  `..._last100`. RECOMPUTATION IDENTITY (declared for the exact-equality
  cross-check): the executor computes `np.mean` over the `f_plus` column of
  the 2000x2 curve, first slice `[:100]`, last slice `[-100:]` — the
  evaluator reproduces exactly this float semantics and requires BIT-EXACT
  agreement with the receipt fields (a mismatch is a RETAINED FINDING, never
  silently accepted or rounded).
- M5 limiter saturation fraction — `final_window.saturation_frac`.
- M6 the full fitness curve (2000 x (f_plus, f_minus)) — present per seed,
  digest-checked: sha256 of the canonical curve bytes equals the receipt's
  `fitness_curve_sha256`, and the curve file's own sha equals the pinned
  section 1 value.

THE FROZEN PER-SEED SUCCESS/FAILURE RULING (the criterion this card applies;
frozen upstream, W05 prereg section 4 P3): a seed's training outcome is

- SUCCESS iff `mean_iteration_fitness_last100 > mean_iteration_fitness_first100`;
- FAILURE otherwise (`improved_first_to_last_100 == false`).

Both window means and the flag are recomputed from the pinned curve and
cross-checked bit-exactly against the receipt fields before the verdict is
emitted. The verdict is a pure function of pinned bytes: no discretionary
step exists. NO seed may be dropped, no window moved, no substitute metric
substituted, no re-run substituted for a bad number.

FROZEN EVALUATION-INTEGRITY CRITERIA (W05 prereg 2A; checked per seed, all
must hold for the evaluation to be well-formed; failures are reported, never
repaired):

- I1 status `EXECUTED_COMPLETED` or `EXECUTED_TERMINATED_<code>` with the
  code from the frozen termination list; never silent.
- I2 decisions executed == 1000000 declared (or a retained termination
  explains the shortfall); iterations 2000; ticks 15000000.
- I3 no termination code (physical falsifier classes): a completed seed
  records NO breach of the six hard gates (no_nan_inf, velocity_envelope,
  bounds_honored, contact_floor, availability_exact, no_intervention) at any
  tick — the executor's status law retains any breach as a termination
  record; `termination_code == null` is the receipt-level evidence that no
  sliding/penetration-class gate (contact_floor), no unsupported-propulsion
  class (velocity envelope), no hidden-reset class (intervention_observed),
  no wrong-command class (bounds_honored) fired during the run.
- I4 state-chain head present; theta identity chain initial -> final bound;
  theta npz on disk hashes to the receipt and to the trained manifest.
- I5 held-out completeness (C10): all 9 cells of the 3x3 matrix present,
  exactly 6 off-diagonal `held_out: true`, 3 diagonal `held_out: false`,
  every cell carrying fitness/mean speed/v_max/state sha; none cherry-picked.
- I6 deploy-gate rows (C10): `allow_frozen_relation.decision == "ALLOW"`,
  `block_trained_bundle.decision == "BLOCK"` with the mismatch reason
  present, `block_foreign_build.decision == "BLOCK"`; the trained theta npz
  shas bound in the deploy receipt equal the pinned section 1 npz shas.

## 3. The no-runs law (structural)

The evaluator contains no scene import, no policy import, no training entry
point, no subprocess and no socket. FB5 (section 5) AST-scans every
contribution `.py` for those constructs and fails on presence. The numbers
reported by this card are therefore PROOF-READINGS of the sealed record, not
new measurements.

## 4. Predictions (registered BEFORE the evaluation receipts exist; disclosed either way)

- E1 (training signal): all three seeds FAIL the frozen P3 criterion
  (improved=false on all three, per the sealed upstream report; expected
  first->last windows approx 15.44 -> 11.44, 15.69 -> 11.42, 15.46 -> 11.44
  m/250-decision). The honest per-seed walking outcome of walk1m-r1 is
  therefore NEGATIVE on all three seeds: training DEGRADED forward progress
  from its entry-law level on every seed. This is a FAILURE REPORT for the
  training outcomes — and exactly that report satisfies the done_when; it is
  not an implementation failure of this card.
- E2 (recomputation): every frozen metric recomputes BIT-EXACTLY to its
  receipt field under the declared float semantics (M4 identity) for all
  three seeds.
- E3 (completeness): the receipts are complete (I1-I6 all hold; nothing
  cherry-picked, nothing missing).
- E4 (deploy gate): the trained thetas are BLOCKed from deploy per I6; the
  evaluation reports them as non-deployable training candidates (FC-3 stays
  explicitly-unresolved).

If any prediction fails, the failure is RETAINED and reported in the report
with its named refusal code; no re-run, no repair, no silent acceptance.

## 5. Falsifier arms (each with its own clean control, G1; the card falsifier mapped)

The card falsifier classes are evaluated AT THE RECEIPT LEVEL (the runbook's
hard-gate termination records are their detectors; I3): sliding/penetration
(contact_floor_breach), unsupported propulsion (envelope_breach),
hidden reset (intervention_observed + the continuous 4096-tick state-chain
anchoring), wrong command response (bounds_breach), diagnostic/clean state
divergence (the recipe-equivalence receipt: the trainable controller class
reproduced the frozen policy applied bytes tick-for-tick — trajectory sha
`cd4944d99be1270951926be53859828a6b0aef21d32d6551f68e78d504ef6c7a`). None
fired on any seed (no termination code exists); the evaluation verifies
these receipts and reports the mapping explicitly.

Named-check bite arms (every arm: clean control FIRST on pinned bytes, then
the bite on a scratch tampered copy; the detector must FAIL the tampered
copy with its named code):

- FB1 `input_pin_mismatch`: control — the pin verifier runs GREEN on the
  section 1 pins; arm — a mutated expected sha in the override table must
  FAIL the verifier.
- FB2 `metric_recompute_mismatch`: control — M4 recomputation is bit-exact
  for all seeds on pinned bytes; arm — one curve value perturbed in a
  scratch copy must produce a recomputed window mean that differs from the
  receipt value and fire the detector.
- FB3 `cherry_pick_detected`: control — seed-set and held-out completeness
  pass on pinned bytes; arm — (a) a scratch receipt set missing one seed and
  (b) a scratch held-out receipt missing one off-diagonal cell must each
  fire the completeness detector.
- FB4 `deploy_gate_ruling_violated`: control — the I6 rows hold on pinned
  bytes; arm — a scratch deploy receipt with
  `block_trained_bundle.decision = "ALLOW"` must fire the detector.
- FB5 `run_path_present` (structural, the no-runs law): control — the AST
  scan is GREEN on this contribution; arm — a scratch file importing
  `run_training` / `scene_cpu` / `policy_compat` or calling `subprocess`/
  `socket` must fire the scanner.
- FB6 `verdict_not_a_pure_function`: control — every emitted per-seed verdict
  recomputes identically from the pinned inputs; arm — a scratch evaluation
  receipt with one verdict flipped relative to its inputs must fire the
  verdict-consistency detector.

- G5: `refuse_vacuous_comparison(a, b, code)` precedes every relative-window
  comparison (M4 first-vs-last, M3 v-vs-envelope, the held-out diagonal vs
  off-diagonal deltas) and `vacuous_guard_selftest()` is required by the
  check main; identical-to-the-bit window comparisons are refused as
  vacuous rather than silently judged.

## 5c. Camera record delivery (profile `walking`; the W04 record-space precedent)

The runbook's bounded-resources law retained NO trajectory bytes (streaming
chain hashing only; `trajectory_retention: NONE`) and no pose, contact or
camera records exist for the trained rollouts. The profile's native views
(full-body ground overview; side view of stance/swing; close-up of
foot-ground contact) CANNOT be rendered from retained records without
inventing bodies — which the laws forbid (never invent missing anatomy).
Therefore, exactly as the sealed W04 card did under its profile, this card
delivers a RECORD-SPACE RASTER capture: deterministic CPU rasters of the
pinned receipts (per-seed fitness curves with the frozen first/last-100
windows marked; the per-seed frozen-metric outcome table; the 3x3 held-out
matrix), clean and diagnostic modes rendered from the SAME pinned bytes
(diagnostic adds the window markers and labels; both carry the SAME record
identity — the composite evaluation-record sha — on every row, the
view-toggle instrument of the profile falsifier), each view row carrying the
full camera field vocabulary (frame_id .. state_or_tick_interval;
structure-only values declared orthographic record-space; honesty label
"RECORD-SPACE RASTER of pinned receipts - not engine frames; native pose/
contact trajectory records inventoried ABSENT (runbook trajectory_retention
NONE; streaming chain hashing only)"). The validator class is
CAMERA_METADATA_STRUCTURE_ONLY; visual_acceptance is NOT claimed from these
rasters — the numerical evidence is the receipts; independent visual review
remains the Sergeant's. The absent inventory is NAMED in the manifest, the
context and the report (not silently skipped).

## 6. Determinism and honesty

- Canonical JSON everywhere (`sort_keys`, compact separators, `allow_nan`
  false, LF, UTF-8); no wall-clock in canonical blocks.
- All three seed outcomes are reported whether SUCCESS or FAILURE; a failed
  seed is not hidden, retried, or averaged away (the no-runs law).
- G12: the named-check suite claims "N executed, M skipped"; zero skips by
  design (no KNOWN_SKIPS file).
- G7: criteria sha256 identical across join / registry (read-only re-read) /
  prereg / checks identity.
- CRLF law: path-local `* -text`; byte-level edits only.
- EVIDENCE ANCHORING: every store addition goes through
  `anchor.py add <file> --card MAT2-W06`; reference fields carry one path +
  one sha each; no prose in reference fields. (Store verify state at attempt
  start: PASS — 10780 files, 0 mismatch; the store is accepting adds.)

## 7. Gates disclosure (G1-G12 at the candidate commit)

G1 falsifier arms with clean controls: this prereg section 5 (FB1-FB6).
G2 lint: `lint_report_numbers.py` + selftest must exit 0. G3 no
hand-written qualitative claims: report generated from receipts only.
G4/G8 capture: delivered as the section 5c record-space raster with full
camera vocabulary; NOT engine frames (named, with the absent inventory).
G5 vacuous guards + selftest: section 5. G6 keyed extractors: the frozen
iteration windows are carried as keyed receipt fields; the evaluation adds
no new phase definitions. G7 registry read-only identity: section 0/6.
G9 publication hygiene: prereg committed separate-first; contribution within
32 files / 16 MB; ONE publication commit on `review/MAT2-W06` with the full
lineage and `Agent: wk-w06-eval`; commit-message metrics generated from
FINAL receipts. G10 pin-vs-disk: every receipt/report pin hashes against the
on-disk bytes at its card-relative path. G11 agent trailer: every commit in
the candidate chain carries `Agent: wk-w06-eval` (chain scoped from
`<prereg>^`). G12 skip accounting: "N executed, M skipped" in the checks
receipt and report.
