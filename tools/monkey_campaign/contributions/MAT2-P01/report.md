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

## Correction (independent review bb096a44d27e451fb4535f468411a9c5, verdict CHANGES_REQUIRED)

Defects found by the independent reviewer at head a195f457 and fixed in this correction:

- D1: the frozen prereg falsifier F1 ("removing or altering any identity binding
  (criteria sha, scope sha, archived scope sha, planning id) makes test_contract.py
  exit nonzero with IDENTITY_MISMATCH") was not implemented: the test had no
  planning_id check and its three hash checks were prefix-only, so planning id
  removal/alteration and 4-char hash-suffix alterations all exited 0.
- D2: test_contract.py contained a tautological self-referential criteria check
  (lines 50-51, "self-referential skip") — dead code presented as a criteria check.

Fix (test-only; PREREGISTRATION.md and contract.json are byte-identical to the
originally published artifacts, sha256 e895e8a2... and e255eb44...): test_contract.py
now parses the FULL 64-hex criteria/active-scope/archived-scope hashes and the
planning id from the frozen PREREGISTRATION.md text and requires exact equality with
contract.json, deletes the dead check, and additionally cross-checks the criteria sha
against the live registry card (fail-closed when the campaign store is reachable).

Failing-first demonstration (transcript bound in review workspace
kanban-reviews/MAT2-P01/bb096a44d27e451fb4535f468411a9c5/evidence/transcripts_correction.txt):
planning id removed -> exit 1 IDENTITY_MISMATCH; planning id altered to P99 -> exit 1;
4-char suffix alteration of criteria/active-scope/archived-scope sha -> exit 1 each;
criteria removed -> exit 1; active scope swapped with archived -> exit 1; prereg+contract
collusion on the criteria sha -> exit 1 via the live registry card check. Baseline
unchanged -> ALL CHECKS PASS, exit 0. No new probes were added: the frozen prereg
(P1-P3, F1-F3) is unchanged and is now fully implemented.

## Artifacts (absolute paths + sha256)

- PREREGISTRATION.md — e895e8a2d46d6c9e4b5a6980c6a83f9a8a785142c06248e0d843b013369c73c9 (unchanged by correction)
- contract.json — e255eb44203212c039598d28629c21e6e1c019d1abe6caa07b4430fca53715a5 (unchanged by correction)
- test_contract.py — changed by correction; exact sha256 in the publication record
- qualification_receipt.json — changed by correction; exact sha256 in the publication record
- report.md — this file (changed by correction)
