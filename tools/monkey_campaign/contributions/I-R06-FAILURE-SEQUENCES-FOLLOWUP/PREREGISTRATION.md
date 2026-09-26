# PREREGISTRATION — I-R06-FAILURE-SEQUENCES-FOLLOWUP

Card `I-R06-FAILURE-SEQUENCES-FOLLOWUP` (planning R06; parent
I-R06-FAILURE-SEQUENCES = merged PR #123, runner verified this attempt:
`failure_sequences.py` sha256 `d3e11285…`, suite `283efad2…`, CLI 8/8 PASS
exit 0). Attempt `fbefa4a1790247f9851c73e016e1dd4f`, agent
`c95e1722350849bca846b237c1f60997`, criteria
`e9207e45980f6e9e7207c3a1b328c1a3911cb9f6835fb6d3fc78ea81367eb4db`.
Written BEFORE the adapter ran.

## STATEMENT

The smallest product-regression entry is an ADAPTER that invokes the accepted
runner and its pinned real product classes (reference/ extraction, ledger-
bound at base `9afbddcd`) — no new sequences, no new fuzz volume, no
production change — with identity verification before invocation and
injected-counterexample detection demonstrated through the runner's OWN
deliberately-broken controls.

## PREDICTION (not yet measured by this attempt)

1. With identity verified (runner + suite sha256; reference ledger present),
   the adapter's clean run reproduces 8/8 sequences PASS via the runner CLI,
   and the runner's own unittest suite passes via subprocess.
2. Injecting the runner's `LatchingMapper` control produces a DETECTED
   invariant failure (non-zero/raise) — detection demonstrably fires.
3. A tampered runner (identity check sabotaged in an isolated copy) is
   REFUSED by the adapter before any run (fails closed).

## FALSIFIER

The adapter adding new sequences/fuzz, claiming device testing, invoking a
runner whose identity does not verify, or the injected counterexample passing
undetected. No production behavior is changed (no retained failing
counterexample exists to justify a patch — the runner's clean run just
reproduced 8/8).

## BOUNDS

CPU-only, stdlib; read-only over the parent attempt directory; subprocess
bounded ≤110 s; own workspace; ≤16 MiB output.
