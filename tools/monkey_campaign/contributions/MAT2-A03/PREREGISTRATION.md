# PREREGISTRATION — MAT2-A03 (attempt 7ac643af941548f39ad251b024eda976)

Frozen 2026-09-27, BEFORE any verification run, replica extraction, probe execution
or receipt build of this attempt. Arrival
`arrival-c2a69acdef164e47b9b59d751a25d6a6`. Card MAT2-A03, planning id A03.
Criteria sha256
`a4d6c38cbc07587a261fbde90425e5f0afa5dbd2d8edb4f40713f277e93c3aa8`.
Scope sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.
Verification profile `anatomy` (`visible_static`), `numerical_evidence_required: true`,
`clean_view_required: true`.

## done_when (exact card clause — UNCHANGED from ONT-A03)

> Architect approves mapping/supersession, historical radius preserved, new
> transforms and regressions qualified

Kind `decision+implementation`. This MAT2 card is a RECONCILIATION-AND-READOPTION
candidate: it binds the merged, lead-approved ONT-A03 staged supersession into the
MAT2 identity by full re-verification at the current base. It does NOT re-stage,
re-execute, alter or flip any merged ONT-A03 byte.

## Reconciliation (read-only, completed before this freeze)

- Dependency MAT2-A02 DONE/merged: PR #214, head `aa2bbb65ae272cc7e873ecf6f02c8ec0926a23f4`,
  merge `cb4af613aac6841925535624405b3f630a787c3c` (2026-09-27T17:42:05Z) — this
  merge is this candidate's base and the astra/gait-capture tip per the registry.
- The merged ONT-A03 contribution (PR #187, head `051d341da2c0786fe9706d169fe16b8127cb8772`,
  merge `4aecbc9ee98cb115ec9a690f5c0df173d9f3efbf`, 2026-09-27T06:44:32Z) is present
  at `tools/monkey_campaign/contributions/ONT-A03/` in this base: 37 files.
- Clause identity is proven from the registry (read-only): `digest(spec)` recomputes
  to the recorded criteria for BOTH cards (ONT-A03 `d15183d955c5d3764ed605e4c265145400806e5fb7e67738cebb3cf569056e7d`,
  MAT2-A03 `a4d6c38cbc07587a261fbde90425e5f0afa5dbd2d8edb4f40713f277e93c3aa8`);
  `definition_raw_sha256` is equal (`57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`);
  the projected task objects are byte-equal (digest
  `944e19ee697cf953046f73501dc2669f3a0611789abcb7ae356a944b303324a9` both); the only
  spec differences are the envelope fields `id`, `depends_on[0]`
  (ONT-A02→MAT2-A02) and `ontology_qualification.scope_sha256`
  (01ea5cdd…→cb5475f8…).
- Authorization for the adoption (the dispatch critical check): the done_when
  clauses are UNCHANGED; MATERIAL_PLAN_ADOPTION.md authorizes "old evidence may
  satisfy unchanged clauses after checking exact inputs, dependencies and validity;
  submit that reconciliation as the new card's contribution"; the Architect
  approval clause is ALREADY EXECUTED — the staged record's own approval semantics
  define "the connected lead's merge of this exact head IS the architect approval
  act", and that merge happened at `4aecbc9e` with registry verdict ACCEPTED at the
  pinned head; the MAT2-A03 inbox is empty (no restricting message). Therefore the
  authorized work is binding the approved record into the MAT2 identity with full
  re-verification — not a new decision, and not an authorization gap.
- The MAT2-A02 merged precedent (same shape) reconciled ONT-A02 the same way at
  base `6af853ad`; its independent review confirmed at `4aecbc9e` and later bases
  that the ONT evidence stays byte-identical and nothing was executed.

## Statement (frozen)

1. **Adopted mapping/supersession (already approved — verified, not re-decided).**
   The staged record `transforms/radius_supersession_record.json` (sha256
   `e98c3c772e8088311278be13078a8cada43af59d1a81d962a634390c49514526`) is bound
   byte-exact into the MAT2 identity: U-STR with the O1-resolved roll, decision
   basis SOURCE-KINEMATIC CONVENTION FIDELITY, R1's refutation carried VERBATIM
   and never relabeled, no utility/moment-arm selection (T6 carried), status
   `STAGED_FOR_ARCHITECT_APPROVAL` preserved exactly as merged (the approval act
   lives in the registry's ACCEPTED review + merged PR #187, not in a status flip).
2. **Historical radius preserved (re-asserted at this base).** The BEFORE record
   stays packet-verbatim (scale `0.22170679566544982`, span `0.06474489854186721` m);
   the superseded set is enumerated as history; failed alternatives (U-ANA, H-BODY)
   stay named; the merged A02 provenance chain is re-asserted byte-exact.
3. **New transforms and regressions qualified (full re-verification at THIS base).**
   The merged probe (`ota03_ulna_correspondence.py`) and the merged regression suite
   (`test_ota03_ulna_correspondence.py`) are re-executed CPU-only (`python -B`,
   offline) in a fresh replica extracted from THIS base's committed tree; AFTER
   values re-checked against the pinned receipts (scale `0.20418868001006546`,
   span `0.05962909405176015` m, det = s³, site deltas == receipt 08, closure
   mechanism refused-by-name/closes-exactly).
4. **Bounds carried, never relaxed:** no mechanically-qualified-grasp claim;
   no utility selection; not-anatomical (kinematic-convention fidelity); staged-only
   (no production source, model store, fit or training body is touched; the
   supersession is NOT executed into any production asset by this card).

## Frozen predictions (MR probes; first run is the record; nothing is tuned)

Pins below are sha256 unless stated. All derived from committed bytes and the
read-only registry BEFORE this freeze.

- **MR-0 freeze chronology**: the freeze commit carrying ONLY this file has parent
  `cb4af613aac6841925535624405b3f630a787c3c` and is an ancestor of the candidate
  HEAD; HEAD adds only `tools/monkey_campaign/contributions/MAT2-A03/**`.
- **MR-1 clause identity (registry read-only)**: `digest(spec)` of live MAT2-A03 ==
  `a4d6c38cbc07587a261fbde90425e5f0afa5dbd2d8edb4f40713f277e93c3aa8` == the
  attempt's pinned criteria; archived `digest(spec)` of ONT-A03 ==
  `d15183d955c5d3764ed605e4c265145400806e5fb7e67738cebb3cf569056e7d`;
  `definition_raw_sha256` equal; projected task digests equal
  (`944e19ee697cf953046f73501dc2669f3a0611789abcb7ae356a944b303324a9`); the spec
  diff is EXACTLY {`id`, `depends_on[0]`, `ontology_qualification.scope_sha256`}
  (envelope only); my attempt state WORKING under my arrival id.
- **MR-2 byte stability**: `git ls-tree -r` of `tools/monkey_campaign/contributions/ONT-A03`
  is blob-identical (37 files) across `051d341da2c0786fe9706d169fe16b8127cb8772`
  → `4aecbc9ee98cb115ec9a690f5c0df173d9f3efbf` → `cb4af613aac6841925535624405b3f630a787c3c`.
- **MR-3 merged committed-byte pins at the base**: radius_supersession_record.json
  `e98c3c772e8088311278be13078a8cada43af59d1a81d962a634390c49514526`;
  PREREGISTRATION.md `1b1ca64adc42d77839c0bdfe1c9422768378504b78a69a3577031c089cd7a2df`;
  numerical_receipt.json `6862817bfdfd62ac42048f348063b2e8bd7f696f09387319a2cdd34d4840a9f8`;
  state_snapshot.json `f9cae65f43da70a3244752a1d67bee501b8c1b80aed6392ca4179c554d68b1a8`;
  capture_manifest.json `d11ac1409e403c193439e915fea662418099f1bd8402bd0f4b269a9a48e88dfb`;
  capture_context.json `c0797687119f5328361310848f13d9a4eff83ded04b5274385a5448194eb838b`;
  capture_sheet.png `7ee98625ecddf74083872131dba8736e4642128943e73cca4751a295354028f1`;
  visual_provenance.json `1266921aaff08ef83a1a490049067b496c4a04e9f5820338f33d9a55b5e167d6`;
  qualification_receipt.json `27331aad6b2f1fa8b6a58a51b35100fcbf6e076da73ec6f531eb5e91103f21a8`;
  reference/EXTRACTION.json `4fe87ba7f63eff429f62d19fb2a962173cfbe708a25b0665f97af06c0b0c66af`.
  Envelope pins: record status `STAGED_FOR_ARCHITECT_APPROVAL`, card ONT-A03,
  task A03, scope `01ea5cdd…`, criteria `d15183d955…`, `approval_semantics`
  contains "merge of this exact head", bounds carry the four carried bounds,
  basis startswith "SOURCE-KINEMATIC CONVENTION FIDELITY", R1 verdict verbatim
  present with all key phrases, selection rule contains "NO moment-arm, utility",
  BEFORE scale/span packet-verbatim, AFTER scale `0.20418868001006546` /
  span `0.05962909405176015`; receipt outcome `STAGED_AND_QUALIFIED`, summary
  {fail:0, pass:75, total:75}, F1 "no identity mismatch", F2 "none";
  manifest task_id A03 / card ONT-A03 / schema `chimera.visual_capture_manifest.v1` /
  profile anatomy / tick_interval [0,3] / capture_sha256 == PNG pin /
  subject_sha256 == state snapshot pin; context task_id A03, tick_interval [0,3];
  qualification receipt schema `chimera.ont_a03_qualification.v1`, task_id A03,
  head_sha None (honest pre-review), independent_review pending True.
- **MR-4 approval act + dependency (registry read-only)**: ONT-A03 winner PR ends
  "/187", head `051d341da2c0786fe9706d169fe16b8127cb8772`, merge_commit_sha
  `4aecbc9ee98cb115ec9a690f5c0df173d9f3efbf`, merged_at `2026-09-27T06:44:32Z`,
  review verdict ACCEPTED at that head with the ONT-A03 criteria; winner
  ontology_qualification task_id A03, done_when_verified True, profile_verified
  True, evidence pins numerical `6862817b…`, visual `7ee98625…`, camera
  `d11ac140…`; `4aecbc9e` is an ancestor of the base `cb4af613`; MAT2-A02 state
  DONE with winner merge_commit_sha == base == `cb4af613…` (PR #214).
- **MR-5 probe re-execution (fresh replica from the base tree, CPU-only, offline)**:
  exit 0; final stdout line exactly "checks 75/75 PASS  outcome=STAGED_AND_QUALIFIED";
  regenerated staged record is BYTE-IDENTICAL to committed (sha `e98c3c77…`);
  the regenerated numerical receipt equals the committed one in EVERY field except
  exactly `state_snapshot_sha256` (path-dependent binding), and its value equals
  sha256 of the regenerated state snapshot; the regenerated state snapshot equals
  the committed one in EVERY field except exactly `staged_record_path`; after the
  regeneration the suite re-run is self-consistent (see MR-5b).
- **MR-5b suite re-run AFTER regeneration**: exit 0, final line exactly
  "138/138 tests PASS", zero FAIL lines.
- **MR-6 suite on the PRISTINE replica (committed evidence intact), run BEFORE
  MR-5**: exit 1; final line exactly "137/138 tests PASS"; the ONLY FAIL line is
  "recomputed state equals the committed state snapshot"; a key-level diff of the
  recomputed vs committed state snapshot shows EXACTLY one differing key:
  `staged_record_path` (the committed snapshot embeds the original ONT-A03 attempt
  checkout path — environmental, recorded as such by the merged independent
  review). This reproduces the recorded environmental behavior at the new base.
- **MR-7 capture class at this base (committed bytes, canonical validators)**:
  `visual_capture.validate_manifest` imported from the base blob of
  `tools/monkey_campaign/visual_capture.py` (asserted byte-identical to the
  play-checkout copy) returns structurally_valid True, view_count 6; rows are
  V1/V2/V3 x diagnostic/clean; every row locates all 16 contract camera fields;
  diagnostic rows occlusion_mode "mixed", clean rows depth_tested with empty
  layers/label_ids; pairs share camera+state; `visual_gate.verify` with THIS
  card's contract (task_id "A03" envelope, anatomy profile) on the committed
  manifest/PNG/context returns structurally_valid True, view_count 6 — honestly
  bounded: CPU software-raster component capture, CAMERA_METADATA_STRUCTURE_ONLY,
  visual_acceptance not claimed (no native frames, no new human acceptance).
- **MR-8 failing-first (the checks have teeth)**: with everything pristine the
  check functions pass; each tampered variant independently FAILS its own check:
  (a) one token of the staged record flipped (status → TAMPERED_RECORD) fails the
  MR-3 record checks; (b) one character of the winner head sha in an in-memory
  registry copy fails MR-4; (c) a one-ulp tamper of the pinned receipt
  `reference/receipts/I7_08_radius_before_after.json` in a fresh replica makes the
  probe report DISCREPANCY_RECORDED with fewer than 75 PASS (M0 identity/
  provenance checks fail), reproducing the merged review's recorded behavior.

## Falsifier (decidable either way, reported as it falls)

Card falsifier: wrong owner/frame, hidden outside placement, clipped/occluded
subject or label ambiguity fails. View toggles must preserve the physical state
hash.

- **F1 identity**: any MR-1/MR-2/MR-3/MR-4 mismatch — recorded, attempt stops,
  nothing repaired here.
- **F2 value**: any MR-5/MR-5b/MR-6 expectation not met exactly (including a
  state-snapshot diff key other than `staged_record_path`) — recorded as it falls.
- **F3 visual**: canonical validator rejection, missing camera field, pair
  camera/state mismatch, or PNG/subject binding break — recorded.
- **F4 execution/authority**: any write outside this contribution directory and
  the attempt probe_tmp, any production/source/fit/training mutation, any ONT-A03
  byte change, any relabeling of R1's refutation, any utility selection, any
  mechanically-qualified-grasp claim — recorded as an attempt failure.

Bound carried verbatim from the merged ONT-A03 record: this adoption does NOT
authorize mechanically qualified grasp (G-chain work remains) and does not modify
the training body; grasp qualification stays with A05/G01+.
