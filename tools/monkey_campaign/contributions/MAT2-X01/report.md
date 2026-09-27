# MAT2-X01 attempt report — c593fffda68845b9bc76d361ef8065dd

Agent `arrival-44b4c756e017416b9c81f9532c4cb3a1`; card criteria sha256
`e2f2c219a438c9575c01698dc5dd66f799f6eef8a7577ad3571dcae8c8d1c9aa`;
checkout branch-6 at c525b82c7c3ce0128565424764293a3c85811ab3 (isolated sparse
attempt checkout); instruction revision astra-0031; scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.

## What was produced

The selected finite repeatable objective for the small game
(`objective_definition.json`, schema `mat2-x01.objective.v1`), derived by
extraction from hash-pinned current records — no invention, no archived-DONE
promotion:

- Framing: complete game (not movement demo), recovered from the pinned
  MONKEY_RUN goal line ("complete player flow") and the X01 catalog
  observation.
- Repeatable objective: ONE complete ground -> trunk -> climb -> hold ->
  descend -> release -> ground loop, in one session, repeated as free play.
  Finite frame = frozen MAT2-P01 core clause (verbatim); loop success clause =
  live catalog K08 done_when (verbatim); failure semantics = frozen "explicit
  success/failure behavior" plus the pinned MONKEY_RUN physical law; milestone
  order = frozen material-first addition (verbatim: walking through woods
  first, then climb/return).
- No-campaign law: contract "broader features excluded" + catalog finish line
  + MONKEY_RUN backlog law; B01-B07 are required selected tasks in this
  revision (quoted), which is approved scope, not a campaign.
- Unresolved inventory (explicit): spatial envelope pending MAT2-F01,
  acceptance limits pending MAT2-P06, session flow owned by MAT2-X02;
  archived-era envelope numbers are NOT promoted (flags false).
- Exactly one operator decision request, carried unresolved with provenance:
  objective-presentation-surface (disclosed open in the ONT-X01 PR #136 lead
  review). Recommendation recorded; not decided by this card.
- Legacy crosswalk with provenance: archived ONT-X01 (attempt
  30614130594b42b1afd8cbcfe5e6c840, PR #136, head 0c9a615c, ACCEPTED under
  archived scope 01ea5cdd) reused for structure and the decision request only;
  four enumerated not-carried items; promotion_claim NONE.

## Reconciliation (reuse before new work)

- `kanban_cli.py inbox --task MAT2-X01`: empty (no messages, no PRs).
- Legacy `ONT-X01` (read-only): DONE, WON attempt 30614130594b42b1afd8cbcfe5e6c840,
  PR #136 ACCEPTED. Its objective_definition.json in the archived attempt
  workspace hashes `45e97fc64df8f28b15da80affc0124af5a631075149806503e81a3108960057d`,
  byte-identical to the reviewer rerun evidence recorded on the board. Its
  sources are archived-era (contract 80b2e2f2..., scope 01ea5cdd), so its DONE
  is not new acceptance; scoped crosswalk only.
- MAT2-P01 (dependency, merged at 97993cbe via PR #192): contract artifact
  read from the board-recorded evidence path
  `E:/ChimeraWork/monkey-coordination/lead-verify-20260926/MAT2-P01-accept-materialized/contract.json`,
  sha256 verified `e255eb44203212c039598d28629c21e6e1c019d1abe6caa07b4430fca53715a5`
  (matches board winner evidence exactly; test_contract.py cb0f0ba2... also
  matches). The branch-6 head (c525b82c) predates the merge and does not
  contain the object; the board evidence path is the pinned identity.
- Catalog refs AUTH-04, AUTH-06, LGT-01, SND-05, SOC-05 read from
  `docs/roadmap/holodeck_tasks.json` (sha d5c7aa8b...): they are downstream
  engineering/research consumers of the selected objective; none is modified
  and none blocks this decision card.

## Commands and observed results (CPU-only, python -B)

1. `python -B implementation.py --out objective_definition.json`
   -> {"schema": "mat2-x01.objective.v1", "decision_requests": 1,
   "evidence_quotes": 14, "unresolved_inventory": 3,
   "contract_sha256": "e255eb44203212c0"}
2. `python -B -m unittest test_implementation -v` -> Ran 15 tests ... OK
   (frozen probes P1-P4 identity/quote checks, F1 loud tamper/drift refusal
   bites, F2 banned-element scan, F3 envelope non-promotion, F4 single
   decision request, F5 every-quote-reproduces oracle, F6 full-hash
   completeness).
3. Reproducibility: re-running extraction after deleting the output
   reproduces objective_definition.json byte-identically (sha256 below).

## Failures observed (honest log)

- Run 1 of the extraction failed loudly:
  `ExtractionFailure: completion_map_schema_unexpected` — the frozen
  identity probes refused my incorrect guessed schema constant. Fixed by
  pinning the actual catalog schema
  `chimera-monkey-completion-planning-handoff-v1` and revision
  `material-first-v2`. This is the falsifier working as frozen.
- Two preregistration wording corrections were made BEFORE any probe ran and
  are annotated inside PREREGISTRATION.md: P2's carry target (catalog P01
  done_when, not the MAT2-X01 done_when) and F3's scope (tokens banned in
  `selected_definition`, allowed only in `legacy_crosswalk.not_carried` as
  the explicit non-promotion record). The repetition field was reworded so
  the frozen F2 banned-phrase scan stays truthful.

## Limits / applicability boundary

- Profile `records` (offline): truth comes from the pinned records and their
  reproducing quotes; no runtime, GPU, or visual claim is made
  (nonvisual_reason applies).
- MONKEY_RUN.md, monkey_completion_map.json and holodeck_tasks.json are
  pinned by raw-file sha256 at extraction time; if the live tree moves,
  re-verification requires re-pinning — by design (F1 refuses drift).
- The decision request (presentation surface) is NOT answered here; it is
  routed to the operator with evidence-backed options, per the decide-phase
  law.

## Artifact identities

Computed at submission time (see publication_request.json); all files under
`tools/monkey_campaign/contributions/MAT2-X01/` in attempt checkout
`E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-X01/c593fffda68845b9bc76d361ef8065dd/checkout`.
