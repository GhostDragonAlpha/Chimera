# ONT-U05 PREREGISTRATION — candidate submission of the climb/let-go intent seam

Frozen BEFORE any artifact write in this attempt, 2026-09-26. Attempt
`b60923e0331d44b1b4ac03dbd327bc01`, agent `arrival-3c2e330f584e4c399906ec4eff127054`,
branch `attempt/ont-u05-b60923e0` (isolated scratch checkout; base =
`56d0116ac20d70962b6d20e60b65380d3ca49d43` = then-tip of `astra/gait-capture`).
Card criteria: `criteria_sha256 = 699696427b5c52bad16f970e88af13e5dbfb137533d8d48c890f126676d28f92`.

Row, verbatim (monkey_completion_map.json tasks/U05): "One explicit climb/let-go
intent reaches the skill selector with versioned semantics; frozen walk contract
remains unchanged." Constraint: "Requires a reviewed interface decision, not an
invented API." Kind: decision+implementation. Depends on U01 — DONE (PR #169,
merge `048b63f41587bc76ecc27a8cf779d3bd94cd3254`, verified present in
`origin/astra/gait-capture` before this attempt's first edit).

## RECONCILIATION (phase 1, done BEFORE this freeze; read-only)

The game lineage (worktree `E:/ChimeraWork/monkey-play-20260924`, commit
`9afbddcd90164b5544a16fd0bc72278d985eb6e3` "F08 integrated ... FOREST FRONT
COMPLETE") ALREADY contains a complete, reviewed, integrated U05 implementation:

* `87c14ca5` "monkey-play: U05 integrated — climb intent seam v1 (73/73; ...)"
* `272e7bda` "monkey-play: U05 amendments + U06 integrated — R4's 4 binding fixes
  failing-first (77/77; R4 battery 27/27 clean) ..."
* `tools/monkey_campaign/agents/U05_climb_intent/INTENT_SEAM_SPEC.md` — THE REVIEWED
  INTERFACE DECISION (R4 verdict APPROVED-WITH-AMENDMENTS,
  `agents/R4_intent_review/report.md`; six interface rulings all APPROVE; AMR-1..4
  binding, landed inside v1). The selector itself does not exist yet (K-series);
  spec section 7 declares the exact sink interface (`emit(IntentEvent)`) the
  selector will implement — this is what "reaches the skill selector" means at
  this dependency layer, per the spec and the map's own observation clause.
* The kanban lineage (`astra/gait-capture`) carries NONE of it; this card's five
  prior attempt workspaces are empty (verified 2026-09-26: only bare prepared
  checkouts). Reuse, do not repeat: the candidate below is a BYTE-EXACT recovery.

## RULE 0 — statement, prediction, falsifier (stated before any write)

**STATEMENT** (disagreeable): the existing reviewed U05 intent seam — recovered
byte-exact from pinned commit `9afbddcd`, with its full falsifier suites and the
R4-reviewed interface spec — satisfies this card's done_when as a candidate
submission on `astra/gait-capture`, WITHOUT writing any new seam semantics, and
the recovery is proven by hash identity plus fresh green falsifier runs plus
failing-first sabotage demonstrations in this attempt.

**PREDICTION** (measured after this freeze, receipts in `evidence/`):
(a) `climb_intent_tests.py` exits 0 printing `RESULT: GREEN` with seam sha256
`6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` at start AND
end (falsifier I6: the frozen walk contract is byte-identical across the run);
(b) `climb_intent_amr_tests.py` exits 0 printing `RESULT: GREEN` (the 4 binding
R4 amendments); (c) sabotaging a recovered scratch copy — (c1) delete the
repeat-press no-op guard (edge law) and (c2) replace the gate-open test with
`True` (gate law) — makes the corresponding suite FAIL with named falsifier
checks (I1-family / I3-family), and restoring the exact bytes makes it green
again; (d) the candidate module's import surface pulls exactly `PHYSICS_HZ` from
the walk seam's record module and never constructs a `CommandRecord`; (e) a fresh
conformance suite (`test_climb_intent_candidate.py`, written in this attempt)
passes: pinned-hash binding, version refusal (`2`, `True`, `"1"`), unknown-intent
refusal, gate drop naming, no-fabricated-retract, and the C12 stamp convention
`issued_tick == now_ms * 300 // 1000` with an injected tick source overriding it.

**FALSIFIER** (any one kills this submission as specified):
* **F-R1 lineage drift**: any recovered byte differs from the pinned sha256
  (candidate or reference or recovered spec/receipt files). Any hit fires.
* **F-R2 suite failure**: either recovered suite exits nonzero or prints a FIRED
  check on the byte-exact tree. Any hit fires.
* **F-R3 undetected sabotage**: a sabotaged copy that still passes its suite
  (the checks would be vacuous). Any hit fires.
* **F-R4 walk contract touched**: `command_record.py` sha256 differs across any
  run, or the candidate constructs/imports `CommandRecord`. Any hit fires.
* **F-R5 invented semantics**: this attempt edits any recovered semantic — new
  intent name, changed trigger/drop/stamp/version behavior, a built selector, or
  a claimed live "climb" observation. Any hit fires (a semantic change is a
  version bump with a new prereg, not this card).

## OWNERSHIP (declared before implementation)

Writes ONLY under `tools/monkey_campaign/contributions/ONT-U05/` in this attempt
checkout (plus untracked run fixtures under the attempt workspace's `runenv/`,
which are NOT committed). No production path, no other contribution, no existing
file modified. Source repos `E:/PythonChimera` and
`E:/ChimeraWork/monkey-play-20260924` are READ-ONLY (`git show` extraction only).

## PINNED IDENTITIES (observed read-only at 9afbddcd before this freeze)

```
tools/monkey_campaign/product/climb_intent.py           586cb1c541afdc391ac14ce989cf2d2561a9ee79e25e874f7fbfc2312fd3c5a2
tools/monkey_campaign/product/climb_intent_tests.py     291eb0b60e754e497d425dada1dffdf0839ea3f8a91f16fd0239ab3f9fdc9895
tools/monkey_campaign/product/climb_intent_amr_tests.py 7ff7f3ba2678d6533e6f40666b5faf9f102751377bc4f89bf68846d2df3b7538
tools/monkey_campaign/product/input_mapper.py           7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44
tools/monkey_campaign/product/focus_policy.py           e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0
tools/monkey_campaign/product/session_flow.py           30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf
tools/science_funnel/typeb_export/command_record.py     6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e
```

(`climb_intent.py`, `input_mapper.py`, `focus_policy.py`, `session_flow.py`,
`command_record.py` hashes independently corroborated by the I-S04 and ONT-U01
contribution receipts already merged on `astra/gait-capture`.)

## RUN PROTOCOL (bounded, CPU-only)

Mirror tree under `<workspace>/runenv/` from the byte-exact recovered files;
`python -B tools/monkey_campaign/product/climb_intent_tests.py` and
`..._amr_tests.py` from the mirror root; every invocation bounded to 120 s;
output growth bounded to 16 MiB (actual: two text receipts, a few KB). Sabotage
demos run on SCRATCH COPIES inside `runenv/` only; the committed candidate bytes
are never mutated. No wall clock in any subject module; no network, no installs,
no GUI, no native build, no GPU, no training, no process control.

## HONEST LIMITS (stated now)

* The selector does not exist (K-series). This card closes the SEAM + versioned
  delivery to the declared consumer interface; it does not claim climbing, a
  skill arbitration, or any live in-game behavior. K01/K06 own what an intent
  MEANS; U06 owns rendering; the live wiring and actual-play lane stay open.
* The controls "motion" profile's native/visual probes do not apply to a pure
  signal channel with no runtime consumer yet; the applicability boundary is
  recorded in report.md without claiming runtime acceptance.
* The original receipts (2026-09-24) are the PRESERVED records leg; this
  attempt's fresh runs are the re-verification leg on the recovered bytes.
