# PREREGISTRATION — I-R05-RESOURCE-LEDGER (planning id R05)

Attempt: 080ba14585ce405e9b7d0ae87632a8af · branch-6 · pinned base `9afbddcd90164b5544a16fd0bc72278d985eb6e3`
Written BEFORE any implementation edit (Rule 0: statement / prediction / falsifier).

## RULE 0 — STATEMENT

An ownership-scoped resource ledger for repeated session/restart teardown can be a small,
deterministic, stdlib-only event ledger keyed on (SESSION GENERATION, OWNER, RESOURCE ID),
which classifies exactly five named failure modes — duplicate-acquire, unknown-release,
wrong-generation, wrong-owner, live-at-close — and judges every cycle strictly against
caller-provided ceilings, never against probed memory or OS process state. The pinned
teardown code (`tools/monkey_campaign/product/session_flow.py`,
`tools/monkey_campaign/data/monkey_forest/forest_loader.py` at 9afbddcd) currently tears
down by imperative cleanup without such a per-resource ownership record, which is why a
leak or an owner collision can pass silently today.

## PREDICTION (not yet measured)

1. `git grep` at the pinned revision will find NO existing equivalent ownership-scoped
   accounting checker (no acquire/release ledger with generation+owner+resource-id and
   named failure classes); the new module is not duplicating live code.
2. The implemented ledger will reject an unrelated owner's release attempt, reject a
   stale-generation release, and mark a leaking cycle as FAILED — all demonstrated by the
   unittest suite (≈ 14–22 tests) which runs green in well under 120 s (predicted < 5 s,
   pure CPU, no I/O beyond the test file itself).
3. Cycle summaries will judge only against ceilings the caller passes in; no code path
   probes RAM, processes, or system state.

## FALSIFIER (named before the run — ANY ONE fails the build)

- F1: an unrelated (operator) owner's resource can be released through the session owner.
- F2: a release recorded against a stale generation is accepted against a
  current-generation resource (stale generations close current resources).
- F3: a resource left live at close is reported as a clean/passing cycle (a leak passes).
- F4: the suite cannot reach green inside the 120-second per-invocation bound, or needs
  anything outside the stdlib.

If F1–F3 occur the design is wrong (ownership key is broken); if F4 occurs the
implementation is wrong. Neither may be tuned away — the result gets recorded and the
card reports honestly.

## BOUNDS

std lib only · Python 3.11+ · headless · deterministic · no psutil / process enumeration /
kills / engine launches / memory probing · tests < 120 s · total new output < 16 MiB ·
code only inside WS.
