# ONT-U05 PREREGISTRATION (attempt c7f9519f83c54b3094f1cf097baa742b) — bring-forward + independent re-verification of the climb/let-go intent seam

Frozen 2026-09-26 BEFORE any candidate assembly or verification run, in isolated
attempt workspace `E:/ChimeraWork/monkey-coordination/kanban-attempts/ONT-U05/c7f9519f83c54b3094f1cf097baa742b`
(slot branch `branch-3`, base `c525b82c7c3ce0128565424764293a3c85811ab3`).
Arrival: `arrival-807603c1f2d14bf6bb8327f1ed07fc6a`. Card criteria sha256:
`699696427b5c52bad16f970e88af13e5dbfb137533d8d48c890f126676d28f92`.

## DONE_WHEN (verbatim, frozen by the card)

"One explicit climb/let-go intent reaches the skill selector with versioned
semantics; frozen walk contract remains unchanged." Constraint: "Requires a
reviewed interface decision, not an invented API."

## RECONCILIATION (phase 1 deliverable, frozen here before verification)

Clause-to-evidence map (all pinned to lineage commit `272e7bda` on
`monkey-play-20260924`, the current code owner of the U-lane product modules):

- The reviewed interface decision EXISTS: `agents/U05_climb_intent/INTENT_SEAM_SPEC.md`
  (sha256 of LF blob `772d809df620bb93cce97fd41f081ba244b44edfef8d9ee4797f16cc8eac143b`),
  frozen before implementation 2026-09-24, and the independent R4 review returned
  `APPROVED-WITH-AMENDMENTS` (`agents/R4_intent_review/report.md`); its four BINDING
  amendments (AMR-1..4) are already landed inside the amended module with
  failing-first receipts (`agents/U05b_amendments_U06/receipts/`).
- The implementation EXISTS and is owned by this exact task:
  `product/climb_intent.py` @ `272e7bda` (LF blob sha256
  `586cb1c541afdc391ac14ce989cf2d2561a9ee79e25e874f7fbfc2312fd3c5a2`), plus its two
  falsifier suites `product/climb_intent_tests.py` (73 checks) and
  `product/climb_intent_amr_tests.py` (4 checks), recorded GREEN 77/77 with
  failing-first amendment receipts.
- "Reaches the skill selector": the selector does not exist yet (K-series owns it);
  the spec's section 7 DECLARS the sink interface the selector will implement
  (`emit(IntentEvent)` only), and the channel delivers the versioned stream to that
  declared interface. This is the map's own completion semantics for this row —
  not a completion claim about climbing behavior.
- "Frozen walk contract remains unchanged": the channel imports exactly ONE name
  from the walk seam (`PHYSICS_HZ`, a constant) and the suites pin byte-identity of
  `tools/science_funnel/typeb_export/command_record.py` across the whole run
  (falsifier I6). Walk seam frozen at v1 by commit `e028d6fb` (recorded in
  `agents/R4_intent_review/receipts/walk_contract_hash_proof_20260924.txt`).
- Dependency verdict ONT-U01: DONE (board winner PR #169, merged 2026-09-26, head
  `f8a5f712ea65e8871840a89e20b4f75e1c68ff7c`, merge `048b63f41587bc76ecc27a8cf779d3bd94cd3254`).
  The winning qualification's `subject_sha256`
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` is
  byte-identical to `product/input_mapper.py` @ `272e7bda` — the same bytes this
  candidate pins in `reference/`. The dependency's frozen walk contract is therefore
  the SAME artifact this card must leave unchanged.

DECISION (recorded ruling, not invented here): the spec + R4 amendments ARE the
reviewed interface decision demanded by the row; no new interface, vocabulary,
default key, gate or stamp semantic is chosen by this attempt.

## RULE 0 — the theory, stated before the build

**STATEMENT** (disagreeable): the kanban-card deliverable for ONT-U05 is exactly
the already-verified seam at the pinned lineage revision — brought forward
BYTE-IDENTICAL into this card's contribution directory, with provenance hashes and
an INDEPENDENT re-verification (not a re-trust): the pinned bytes re-assembled into
a hash-verified sandbox reproduce both original suites GREEN, and the suites have
teeth (named injected defects FIRE them failing-first). No byte of the seam, the
spec, the walk contract, or any sibling product module is re-authored, re-tuned or
"improved" by this attempt.

**PREDICTION** (measured by `test_implementation.py` + the unmodified original
suites, all CPU-only, headless, injected clocks):

- P1 IDENTITY: `implementation.py` in this directory is byte-identical (sha256 of
  raw bytes) to `product/climb_intent.py` @ `272e7bda`
  (`586cb1c541afdc391ac14ce989cf2d2561a9ee79e25e874f7fbfc2312fd3c5a2`), and every
  `reference/` extract is byte-identical to its pinned blob at `272e7bda`.
- P2 SUITES GREEN: in the reconstructed sandbox the UNMODIFIED original suites
  print `RESULT: GREEN` with exit 0 — `climb_intent_tests.py` (73 checks, includes
  the 6000-event seed-20260924 REVISION A fuzz with vacuity floor 200 deliveries)
  and `climb_intent_amr_tests.py` (4 checks); I6 holds: sha256 of the sandbox
  `command_record.py` is identical before and after the full run.
- P3 FAILING-FIRST (suite teeth): three named single-defect mutations of the seam
  module each make the suites FAIL (exit 1) with the predicted falsifier family
  firing, and restoring the pinned bytes returns GREEN:
  - M1 EDGE LAW BROKEN (held repeat press emits a second event) → I1 fires.
  - M2 VERSION LAW BROKEN (`intent_version: 2` accepted by the validator) →
    I2/AMR-1 fires.
  - M3 GATE LAW BROKEN (a gated press is delivered instead of dropped-and-named)
    → I3 fires (and I4's no-fabrication counter-checks the delivery count).
- P4 SCOPE: the candidate commit touches ONLY
  `tools/monkey_campaign/contributions/ONT-U05/**` on top of base `c525b82c`;
  no product path, no sibling module, no campaign tooling is modified.

## FALSIFIERS (named now; any one firing kills THIS attempt's claim)

- **F1 IDENTITY DIVERGES**: candidate `implementation.py` or any `reference/`
  extract differs from its pinned `272e7bda` blob hash. Any hit fires.
- **F2 SUITE NOT GREEN**: any check of either unmodified original suite fails in
  the hash-verified sandbox run. Any hit fires.
- **F3 WALK CONTRACT TOUCHED**: sha256 of the sandbox
  `command_record.py` differs across a full suite run. Any hit fires.
- **F4 TOOTHLESS SUITE**: any mutation demo (M1/M2/M3) that leaves the suites
  GREEN, or a fired mutation outside its predicted falsifier family without an
  explained overlap. Any hit fires.
- **F5 SCOPE CREEP**: any file outside `contributions/ONT-U05/` changed in the
  attempt checkout relative to base `c525b82c`. Any hit fires.

**STOP RULE**: `test_implementation.py` exits 0 with all five falsifiers measured
GREEN (identity, baseline suites, mutation failing-first, restored-green, scope),
receipts saved under `receipts/`; then writes stop and the candidate is submitted
for lead publication to `review/ONT-U05`. No tuning loop exists: if a falsifier
fires, the CLAIM is wrong (the bring-forward or the sandbox is broken) and is
reported as a failure — the pinned 2026-09-24 semantics are never adjusted here to
pass; that would be a version bump on the lineage, not this card's authority.

## OWNERSHIP (declared before assembly)

- `contributions/ONT-U05/PREREGISTRATION.md` — this file (this attempt's frozen
  prereg; the LINEAGE prereg ships under `reference/` for provenance).
- `contributions/ONT-U05/implementation.py` — the pinned seam, byte-identical.
- `contributions/ONT-U05/INTENT_SEAM_SPEC.md` — the reviewed interface decision,
  byte-identical from `272e7bda`.
- `contributions/ONT-U05/test_implementation.py` — this attempt's re-verification
  harness (new code, this attempt's only authored source; imports the UNMODIFIED
  original suites from `reference/` and the pinned module; never edits them).
- `contributions/ONT-U05/reference/` — hash-pinned extracts from `272e7bda`
  (`command_record.py`, the four product modules, both original suites, the two
  package `__init__.py` files, the lineage prereg + receipts, the R4 review
  verdict). READ-ONLY after extraction.
- `contributions/ONT-U05/receipts/` — this attempt's run outputs and hash proofs.
- `contributions/ONT-U05/report.md` — the source-bound qualification receipt.

Nothing outside `contributions/ONT-U05/` is written.

## APPLICABILITY BOUNDARY (declared now; no invented acceptance)

- Headless, CPU-only, injected integer-millisecond clocks: this candidate measures
  CHANNEL DISCIPLINE (edges, gates, naming, versioning, walk-contract isolation,
  suite teeth). It does NOT measure live key feel, the future selector, or any
  rendered behavior. The controls profile's visual/camera probes do not apply:
  the seam produces and consumes no rendered state; visual evidence belongs to the
  downstream U06/K-series cards and the runtime lane (actual-play) — recorded as
  not-applicable here, never passed by a fixture.
- The C12 contract (20 Hz ⇒ 50 ms command interval) is the WALK seam's frozen
  boundary: untouched by this card; the intent channel adds no queue and no latency
  claim (delivery is synchronous inside the press call; stamps share the walk
  seam's tick convention via the imported `PHYSICS_HZ`).
- LF/CRLF: sandbox and candidate artifacts use the git BLOB (LF) bytes; the
  lineage receipts measured a CRLF working tree (e.g. `command_record.py`
  `061a2b55…` CRLF vs `67711759…` LF blob). Byte-identity claims state which form
  they hash; blob identity is the pinned canonical form.
