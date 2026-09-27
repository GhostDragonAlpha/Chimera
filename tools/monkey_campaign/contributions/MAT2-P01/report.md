# MAT2-P01 — Completion-contract freeze (records card)

## What this delivers

The frozen playable-monkey completion contract under the astra-0031 material-first
plan, as the gating MAT2 card whose accepted merge unlocks prototype recovery and
all downstream prerequisites (MATERIAL_PLAN_ADOPTION.md scheduling rule).

## Reconciliation (step 1 — reuse, do not repeat)

- Archived ONT-P01 (read via `kanban_cli inbox --task ONT-P01`, HISTORICAL_SCOPE_READ_ONLY):
  its done_when core clause is carried VERBATIM into this contract. The archived
  board's evidence, PRs and winner are preserved untouched in scope_archives.
- The material-first addition is the Captain-selected architecture recorded in
  MATERIAL_PLAN_ADOPTION.md (regions, membrane pressure, removable tissue
  connections, graph composition, shared GPU passes; density-as-one-property;
  Barnes-Hut scope limit).
- Identity bindings: criteria e4521ad7..., active scope cb5475f8... (astra-0031
  pinned), archived scope 01ea5cdd..., authority file hashes bound in the receipt.

## Frozen-first discipline (step 2)

PREREGISTRATION.md frozen before test authoring and all runs (statement,
predictions P1-P3, falsifiers F1-F3, probes).

## Verification (step 4 — actual run)

`python -B test_contract.py` → RESULT: ALL CHECKS PASS: core clause and
material-first addition carried verbatim into the done_when (P1); identities
bound and authority hashes recomputed (P2/P3); falsifier bites demonstrated
live — SCOPE_UNSUPPORTED, CORE_CLAUSE_INCOMPLETE, RECORD_SUBSTITUTION all fire
on injected bad claims and a well-formed records claim evaluates SUPPORTED
(F1-F3); prereg completeness checked.

## Honest boundary

Offline records-kind card (verification_profile: offline). This contract FREEZES
the goal; it does not implement it. No runtime, visual, or native claim.
Completion semantics recorded: card closes only on lead-approved exact-head
merge with qualification evidence; the game closes only with integrated
evidence for every selected requirement and actual human player acceptance.

## Artifacts (absolute paths + sha256)

- PREREGISTRATION.md — e895e8a2d46d6c9e4b5a6980c6a83f9a8a785142c06248e0d843b013369c73c9
- contract.json — e255eb44203212c039598d28629c21e6e1c019d1abe6caa07b4430fca53715a5
- test_contract.py — 9db1a4d94db3879b171efbfa9269dce6e7a167af923b1ce357d62563411d2f25
- qualification_receipt.json — 648b42a1a447191a628a09c66ff1cf816e74d587c45afca7f36c4416baef5993
- report.md — this file
