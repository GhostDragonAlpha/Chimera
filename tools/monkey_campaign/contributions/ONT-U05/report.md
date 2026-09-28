# ONT-U05 qualification report — climb/let-go intent seam (bring-forward, independently re-verified)

Attempt `c7f9519f83c54b3094f1cf097baa742b`, arrival `arrival-807603c1f2d14bf6bb8327f1ed07fc6a`,
card `ONT-U05` (criteria sha256 `699696427b5c52bad16f970e88af13e5dbfb137533d8d48c890f126676d28f92`),
isolated checkout `E:/ChimeraWork/monkey-coordination/kanban-attempts/ONT-U05/c7f9519f83c54b3094f1cf097baa742b/checkout`,
slot branch `branch-3`, base `c525b82c7c3ce0128565424764293a3c85811ab3`. Date 2026-09-26.
Prereg frozen before any assembly/verification: `PREREGISTRATION.md` (this directory).

## 1. DONE_WHEN and the reconciliation verdict

DONE_WHEN (verbatim): "One explicit climb/let-go intent reaches the skill selector
with versioned semantics; frozen walk contract remains unchanged." Constraint:
"Requires a reviewed interface decision, not an invented API."

| clause | evidence (current owner, pinned) | verdict |
|---|---|---|
| reviewed interface decision exists | `agents/U05_climb_intent/INTENT_SEAM_SPEC.md` @ lineage `272e7bda` (LF blob `772d809d…`), frozen 2026-09-24 BEFORE implementation; independent R4 review: `APPROVED-WITH-AMENDMENTS` (`reference/lineage/receipts/R4_review_report.md`), 4 BINDING amendments landed failing-first (`reference/lineage/receipts/amr_failing_first_20260924.txt`) | MET |
| one explicit climb/let-go intent, versioned semantics | `product/climb_intent.py` @ `272e7bda` (`586cb1c5…`): `IntentEvent` v1 (closed 2-name vocabulary, edge-triggered, drop-named gates, `intent_version` validated), delivered to the DECLARED sink interface (spec section 7: `emit(IntentEvent)` only) — the selector is a K-series consumer that does not exist yet; delivery-to-declared-interface is the map's own completion semantics for this row | MET (delivery sense; no climbing-behavior claim) |
| frozen walk contract unchanged | the channel imports exactly ONE walk-seam name (`PHYSICS_HZ`, a constant); walk seam frozen v1 by `e028d6fb`; re-measured THIS attempt: `command_record.py` sha256 identical before/after every suite run (F3, section 4) | MET |
| dependency ONT-U01 | board winner PR #169 merged 2026-09-26 (head `f8a5f712…`, merge `048b63f4…`); winning `subject_sha256` `7a36a45e…` is byte-identical to `reference/product/input_mapper.py` @ `272e7bda` — same artifact this card leaves unchanged | SATISFIED |

Reconciliation outcome: the task-owned behavior EXISTS, reviewed and amended, on the
monkey-play lineage (`87c14ca5` U05 integrated 73/73 → `272e7bda` U05 amendments +
U06, 77/77, R4 battery 27/27). Per the card's step 1 ("reuse verified work; do not
repeat completed implementation") this attempt does NOT re-author the seam; it
brings the exact reviewed bytes forward as this card's candidate and independently
re-verifies them (the lineage receipts are treated as claims to re-confirm, not as
proof).

## 2. What this attempt implemented (the candidate)

`tools/monkey_campaign/contributions/ONT-U05/` on top of base `c525b82c` — nothing
outside this directory changes (F5 measured, section 4):

- `implementation.py` — the seam, BYTE-IDENTICAL to `product/climb_intent.py` @
  `272e7bda` (sha256 `586cb1c541afdc391ac14ce989cf2d2561a9ee79e25e874f7fbfc2312fd3c5a2`).
- `INTENT_SEAM_SPEC.md` — the reviewed interface decision, byte-identical
  (`772d809df620bb93cce97fd41f081ba244b44edfef8d9ee4797f16cc8eac143b`).
- `PREREGISTRATION.md` — this attempt's frozen prereg (statement, prediction,
  falsifiers F1–F5, stop rule, ownership, applicability boundary).
- `test_implementation.py` — the attempt's only authored source: the
  re-verification harness (identity, sandbox assembly, suite re-runs, failing-first
  mutation demos, walk-contract pin, scope check).
- `reference/` — 17 hash-pinned extracts from `272e7bda` (READ-ONLY after
  extraction): the four sibling product modules, both original suites, the two
  package `__init__.py` files, the walk contract, the lineage prereg and receipts,
  the R4 verdict. Full manifest with observed==expected assertion results:
  `receipts/identity_manifest.json`.
- `receipts/` — this attempt's run outputs (baseline, mutations, restore, scope,
  sibling baselines).

## 3. Exact commands (all CPU-only, headless, `python -B`, Python 3.14.3, Windows)

```
python -B tools/monkey_campaign/contributions/ONT-U05/test_implementation.py
# sibling baselines (supplementary), in a scratch sandbox built from reference/:
python -B tools/monkey_campaign/product/input_mapper_tests.py
python -B tools/monkey_campaign/product/focus_policy_tests.py
python -B tools/monkey_campaign/product/session_flow_tests.py
```

Extraction provenance for every pinned byte:
`git -c safe.directory='*' show 272e7bda:<path>` from the attempt checkout (LF blob
bytes; the LF/CRLF distinction and the recorded pipe-hash trap are handled per
`reference/lineage/receipts/walk_contract_hash_proof_20260924.txt`).

## 4. Observed results (harness exit 0, RESULT: GREEN)

- F1 IDENTITY: all 17 pinned artifacts byte-identical to `272e7bda`, including
  `implementation.py == 586cb1c5…` (`receipts/identity_manifest.json`).
- F2 BASELINE (unmodified original suites in the hash-verified sandbox):
  `climb_intent_tests.py` exit 0, `RESULT: GREEN`, **73/73 PASS, 0 FAIL** (I1–I8
  incl. the 6000-event seed-20260924 REVISION A fuzz, vacuity floor 200 deliveries)
  in 0.2–0.4 s; `climb_intent_amr_tests.py` exit 0, GREEN, **4/4** (AMR-1..4)
  (`receipts/baseline_suites.txt`). Matches the lineage's recorded 77/77.
- F3 WALK CONTRACT: sandbox `command_record.py` sha256
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` (LF blob
  form) identical before and after every full suite run — the pinned walk seam is
  untouched by the channel and its suites.
- F4 FAILING-FIRST (suite teeth proven; candidate/reference bytes never mutated —
  mutations land only in disposable sandbox copies):
  - M1 edge law broken (held repeat press re-emits): main suite exit 1, I1-family
    fired (`I1.b,I1.e,I1.f,I1.g,I1.h,I1.i`, 12 FAILs)
    (`receipts/mutation_M1_edge_law_failing_first.txt`).
  - M2 version law broken (`intent_version: 2` accepted): exit 1, `I2.h` fired;
    the amendment suite ALSO fires `AMR-1` (bool/2 smuggle) under the same
    mutation (`receipts/mutation_M2_version_law_failing_first.txt`).
  - M3 gate law broken (gated press delivered, not dropped-named): exit 1,
    I3-family fired (`I3.b,I3.c,I3.d,I3.f,I3.k,I3.o`, 11 FAILs)
    (`receipts/mutation_M3_gate_law_failing_first.txt`).
  - RESTORE: pinned bytes rebuilt into a fresh sandbox → 73/73 + 4/4 GREEN again
    (`receipts/restored_green.txt`).
- F5 SCOPE: `git status --porcelain -uall` on the attempt checkout lists ONLY
  `tools/monkey_campaign/contributions/ONT-U05/**` paths on top of base
  `c525b82c` (`receipts/scope_check.txt`).
- Sibling baselines in the same sandbox layout (supplementary dependency evidence,
  `receipts/sibling_*_rerun.txt`): `input_mapper_tests.py` GREEN 30/30 (U01),
  `focus_policy_tests.py` GREEN 41/41 (U03), `session_flow_tests.py` GREEN 74/74
  (X02) — consistent with the lineage's recorded baseline rechecks.

### Honest defect trail (this attempt's own harness)

The FIRST harness run fired F4 on all three mutations: the mutation demo invoked a
closure over the BASELINE sandbox's suite path, so the mutated sandbox was built
but never executed (observed: exit=0, fail=0 for M1/M2/M3 while the M2/AMR control
— which ran the correct sandbox — fired AMR-1). Cause fixed in
`test_implementation.py` (run the mutated sandbox copy directly); the corrected run
is the one recorded above, exit 0. The falsifiers worked exactly as designed: the
claim "the suites have teeth" was tested and the defective demo was rejected before
it could support the claim. No receipt from the defective run survives (regenerated
by the corrected run); this paragraph is the preserved record of the firing.

## 5. Calculation contract C12 (input timing and control mapping)

"20 Hz implies a 50 ms command interval, not an end-to-end latency guarantee." The
50 ms interval is the WALK seam's frozen boundary (CommandRecord v1, U01's card) —
untouched here (F3). This channel adds NO queue and NO latency claim: delivery is
synchronous inside the press call (measured by I1.a: the event exists before
`press()` returns), stamps share the walk seam's tick convention via the imported
`PHYSICS_HZ` (I5 asserts the import identity; I2.d measures the (ms, tick) stamp
pairs). No end-to-end latency number is claimed from these fixtures; fixtures are
labeled fixtures.

## 6. Applicability boundary (recorded, not passed by fixture)

- Headless injected-clock evidence covers CHANNEL DISCIPLINE only: edges, gates,
  drop naming, versioning, walk-contract isolation, suite teeth. NOT covered: live
  key feel, the future selector's state machine, any rendered behavior.
- Visual/camera probes (controls profile) do NOT apply: the seam produces and
  consumes no rendered state; nothing exists to photograph without inventing a
  viewer. Visual evidence belongs to downstream U06 (renders gate/intent states)
  and K-series cards; actual-play/runtime evidence belongs to the runtime lane.
  Recorded not-applicable — never claimed as passed.
- The interface itself remains review-gated: spec section 11 lists the six rulings
  the reviewer is asked to make; R4's amendments are binding at v1. This
  submission carries the spec verbatim so the independent reviewer can rule.

## 7. Remaining gates (explicit)

1. Independent review of this candidate against every original done_when clause
   (the interface ruling is the reviewer's per the map).
2. Lead publication to `review/ONT-U05`, base `astra/gait-capture`, exact-head PR
   and merge per LEAD_SERIALIZED policy.
3. Downstream (NOT this card): K-series selector consuming the declared sink;
   U06 rendering; runtime/actual-play and visual lanes.

## 8. Artifact identities (sha256, raw file bytes)

See `receipts/identity_manifest.json` (17 pinned artifacts, observed==expected) —
authored-by-this-attempt files are hashed in the submission manifest. The candidate
commit on `branch-3` carries this directory only.
