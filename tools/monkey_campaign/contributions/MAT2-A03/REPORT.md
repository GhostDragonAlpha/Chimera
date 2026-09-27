# REPORT — MAT2-A03 (attempt 7ac643af941548f39ad251b024eda976)

Arrival `arrival-c2a69acdef164e47b9b59d751a25d6a6`. Card MAT2-A03, planning id
A03, kind `decision+implementation`. Criteria sha256
`a4d6c38cbc07587a261fbde90425e5f0afa5dbd2d8edb4f40713f277e93c3aa8`.
Base `cb4af613aac6841925535624405b3f630a787c3c` (astra/gait-capture tip, MAT2-A02
merge, PR #214). Freeze chain: `5019ceea9d0a23e5c41be27a8cfd73c08290a414`
(original) -> `a0c1e5549d9ed9db59438450a812ba00a1cd22a3` (Amendment 1), both
touching only `PREREGISTRATION.md`, both ancestors of the candidate HEAD.

## Critical check first (dispatch question): is the adoption authorized?

**YES — the card authorizes adoption; there is no authorization gap.** Basis:

1. The MAT2-A03 done_when is BYTE-UNCHANGED from ONT-A03: registry read-only
   proof in MR-1 — `definition_raw_sha256`
   `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1` equal;
   projected task objects digest
   `944e19ee697cf953046f73501dc2669f3a0611789abcb7ae356a944b303324a9` equal;
   spec diff exactly the envelope {`id`, `depends_on[0]`,
   `ontology_qualification.scope_sha256`}; `digest(spec)` recomputes to the
   recorded criteria on BOTH cards.
2. The Architect approval clause is ALREADY EXECUTED: the staged record's own
   approval semantics define the lead merge of the exact head as the approval
   act; that merge happened (PR #187 head `051d341da2…`, merge `4aecbc9e…`,
   2026-09-27T06:44:32Z, registry verdict ACCEPTED at that head; registry
   accept-merge independently verifies GitHub merged state). The record's
   status stays exactly as merged — the approval lives in the registry, not a
   status flip.
3. `MATERIAL_PLAN_ADOPTION.md` (astra-0031 installation policy) authorizes
   exactly this path: "Old evidence may satisfy unchanged clauses after
   checking exact inputs, dependencies and validity; submit that reconciliation
   as the new card's contribution instead of reimplementing known-good code."
4. The MAT2-A03 inbox is EMPTY: no Lieutenant message restricts or re-scopes
   the card. The MAT2-A02 merged card (my dependency, same shape) is the
   precedent whose review confirmed the staged record untouched and nothing
   executed.

The work performed is therefore the authorized form: **binding the merged,
approved staged record into the MAT2 identity with full re-verification at the
current base** — no re-staging, no re-decision, no ONT-A03 byte modified.

## What was implemented (candidate contents, all under `contributions/MAT2-A03/`)

- `PREREGISTRATION.md` — frozen predictions MR-0..MR-8 (freeze chain above).
- `verify_adoption.py` — the probe executing the frozen predictions.
- `reconcile_clause_map.json` — clause-to-evidence map, C01/C16 verdicts,
  dependency verdicts, authorization basis.
- `evidence/reconciliation_receipt.json` — probe record (11/11, outcome
  `ADOPTED_AND_REVERIFIED`).
- `evidence/qualification_receipt.json` — MAT2 identity qualification envelope
  (schema `chimera.mat2_a03_qualification.v1`, task_id A03) binding the adopted
  record, merged evidence pins, the approval act, and the visual applicability
  declaration.

## Exact commands and observed results

Probe (CPU-only, offline): `python -B
tools/monkey_campaign/contributions/MAT2-A03/verify_adoption.py` from the
attempt checkout at the candidate HEAD. Confirmatory run: **11/11 PASS,
outcome `ADOPTED_AND_REVERIFIED`, exit 0**.

- MR-0 freeze chronology: chain HEAD<-a0c1e554(parent 5019ceea, parent
  cb4af613); both commits touch only PREREGISTRATION.md; HEAD-vs-base diff
  confined to `contributions/MAT2-A03/`.
- MR-1 clause identity: digests + envelope diff as above; attempt
  `7ac643af…` WORKING under my arrival id.
- MR-2 byte stability: ONT-A03 = 37 files, blob-identical across
  `051d341da2…` -> `4aecbc9e…` -> `cb4af613…`.
- MR-3 committed pins: all 10 pinned files reproduce (record
  `e98c3c77…`, prereg `1b1ca64a…`, numerical receipt `6862817b…`, state
  snapshot `f9cae65f…`, capture manifest `d11ac140…`, capture context
  `c0797687…`, PNG `7ee98625…`, visual provenance `1266921a…`, merged
  qualification receipt `27331aad…`, EXTRACTION `4fe87ba7…`); record/receipt/
  manifest/context/qualification envelopes all reproduce (status
  `STAGED_FOR_ARCHITECT_APPROVAL`; receipt 75/75 `STAGED_AND_QUALIFIED`;
  AFTER scale `0.20418868001006546`, span `0.05962909405176015` m; BEFORE
  scale `0.22170679566544982`, span `0.06474489854186721` m; R1 verdict
  verbatim; no-utility selection; four carried bounds).
- MR-4 approval act + dependency: winner PR #187 head/merge/timestamp,
  ACCEPTED at that head, `done_when_verified` True, evidence pins match my
  computed file hashes; `4aecbc9e` ancestor of base; MAT2-A02 DONE via PR
  #214 merge == base.
- MR-6 pristine suite (BEFORE regeneration): exit 1, `137/138 tests PASS`,
  exactly one FAIL line `recomputed state equals the committed state snapshot`
  — the recorded environmental path-dependence (committed state snapshot
  embeds the original ONT-A03 attempt checkout's absolute
  `staged_record_path`).
- MR-5 probe re-execution: exit 0, `checks 75/75 PASS
  outcome=STAGED_AND_QUALIFIED`; regenerated staged record BYTE-IDENTICAL
  (`e98c3c77…`); state snapshot diff keys exactly `['staged_record_path']`;
  numerical receipt diff keys exactly `['state_snapshot_sha256']`;
  regenerated receipt re-binds the regenerated state.
- MR-5b post-regeneration suite: exit 1, `137/138 tests PASS`, exactly one
  FAIL line `subject hash matches the state snapshot` (Amendment 1
  expectation; the committed manifest binds the committed state hash).
- MR-7 capture class: canonical `validate_manifest` from the base blob
  (play-checkout copy byte-identical) structurally_valid, view_count 6;
  `visual_gate.verify` with THIS card's contract (task_id `A03` envelope,
  anatomy profile) structurally_valid, view_count 6; all 16 contract camera
  fields on every row; pairs share camera+state; PNG bound. Limits declared:
  CPU software-raster component capture, CAMERA_METADATA_STRUCTURE_ONLY, no
  native frames, no new human acceptance claimed.
- MR-8 failing-first: (a) one-token record tamper -> MR-3 fails on
  `record status='TAMPERED_RECORD'`; (b) winner-head tamper -> MR-4 fails;
  (c) one-ulp tamper of pinned receipt 08 -> merged probe reports
  `checks 73/75 PASS  outcome=DISCREPANCY_RECORDED` (exactly the merged
  review's recorded behavior). The checks have teeth.

## Amendment disclosure (honesty record)

- Original freeze `5019ceea` predicted MR-5b as "exit 0, 138/138" after
  regeneration. One instrument-shakeout probe run (receipts discarded, never
  published) showed that prediction was mis-derived: regenerating the state
  snapshot in a path-changed replica necessarily breaks the committed
  manifest->state hash binding (the merged independent review had already
  recorded that suite 138/138 requires the original attempt checkout path).
  Amendment 1 (`a0c1e554`, child of the original freeze, PREREGISTRATION.md
  only, BEFORE the confirmatory run) corrected exactly that prediction and
  disclosed the shakeout observations. No prediction concerning the evidence
  itself was changed. Instrument corrections in the same window (probe only):
  spec-diff path formatting; removal of a wrongly-assumed `criteria_sha256`
  receipt field (the merged receipt has none; the frozen text never pinned
  one); visual_gate imported from the play checkout (`visual_gate.py` is not
  part of the base tree; the A02 merged precedent imported it identically),
  sha `13cf07f4…` recorded in the MR-7 detail.
- Post-commit determinism: the committed receipts are the ones regenerated at
  the candidate HEAD. A probe re-run at a fixed HEAD regenerates both receipts
  byte-identical; the only observed cross-run difference (pre-commit vs
  at-HEAD) was MR-0's honest record of the HEAD-vs-base diff file count
  (1 file at the amendment HEAD vs 6 at the candidate HEAD) and the dependent
  `reconciliation_receipt_sha256` inside the qualification receipt. No
  evidence-bearing value differs between runs.

## Falsifiers — status

- F1 identity: did not fire (MR-1/2/3/4 PASS).
- F2 value: did not fire on the frozen predictions (MR-5/5b/6 exactly as
  frozen, including the two environmental FAIL lines predicted).
- F3 visual: did not fire (MR-7 PASS with declared limits).
- F4 execution/authority: did not fire — nothing outside this contribution
  directory and the attempt `probe_tmp/` was written; ONT-A03 bytes untouched;
  no production/source/fit/training mutation; no relabeling; no utility
  selection; no mechanically-qualified-grasp claim.

## Bounds carried verbatim from the merged record

No mechanically-qualified-grasp claim (G-chain work remains); no utility
selection; not-anatomical (source-kinematic convention fidelity, R1 refutation
retained verbatim); staged-only (the supersession is NOT executed into any
production asset by this card). Terminal hand tendon sites wait on A04/A05;
BIC thorax half is campaign-level scope.

## Remaining gates (not claimable by this card)

Independent review receipt (reviewer fills reference + raw_sha256 and pins the
head); lead publication to `review/MAT2-A03` and exact-head merge; runtime and
grasp-facing clauses remain downstream (A06/G-chain) and are not claimed here.
