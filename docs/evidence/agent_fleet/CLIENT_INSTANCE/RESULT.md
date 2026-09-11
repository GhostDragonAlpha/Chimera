# fleet-client-instance-01 result (2026-09-11, lead lane)

Preregistration commit `573ea042` (design + staged-migration rationale)
precedes all results recorded here.

## Prediction outcomes

| # | Prediction | Outcome | Evidence |
|---|---|---|---|
| a | baseline: two legacy clients sharing a bearer both checkpoint; audit lacks instance identity | PASS (retained before-picture, compat mode is explicit) | `RUN_INSTANCE_SUITE.txt` test 1 |
| b | bound task refuses second instance (`instance_not_bound`) / forged secret (`instance_secret_mismatch`); bound instance succeeds; resource paths fenced | PASS | test 2 |
| c | events identify the admitted instance; secrets absent from snapshot/events/state/tables | PASS (scanned incl. SQLite bodies) | test 3 |
| d | fence survives reopen on the same store | PASS | test 4 |
| e | enforced mode refuses instance-less claims; flip needs supervisor + an instance-bearing agent | PASS (both directions + guard) | test 5 |
| f | malformed header refused by name at transport | PASS (`invalid_instance_header`) | test 6 |
| g | full fleet suite green | PASS — 194 tests, 0 failures, 1 skip | `RUN_FULL_SUITE.txt` |

## Retained corrections

1. Patch script aborted pre-write on a non-unique pattern (4 identical
   `_task` call sites, not 1) — atomic design paid for itself; fixed to
   replace all four (all are owner-mutation guards: checkpoint /
   submit_review / resource_acquire / resource_release group header).
2. Test harness passed the literal `'lead'` where a token was required
   (`unauthorized`); helper now maps the fixture lead token.
3. One test dict used a bare `checkpoint=` kwarg after a dict literal
   (SyntaxError); fixed. Unclosed-HTTPError ResourceWarning avoided from the
   start (the recorded PR #55 trivial, closed via context manager).

## Fence boundary (explicit)

Lead/supervisor integration paths are exempt by design — the integrator is
not the task owner (test 7 pins the marker absence for supervisor events).
Legacy claims drain naturally; `enforced` gates only NEW claims. The live
deployment flips only after client migration, through a reviewed controlled
transition (NOT_CLAIMED here).
