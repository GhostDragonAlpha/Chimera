# I-R06-FAILURE-SEQUENCES-FOLLOWUP — product regression entry adapter

**Verdict: implemented and verified — the accepted runner (merged PR #123) is
now invokable as a single product-regression entry with identity verification
before invocation, clean 8/8 reproduction, the accepted suite green, and
injected-counterexample detection demonstrably firing. No production change
(no retained failing counterexample exists to justify one), no new sequences,
no device claim.**

- Card `I-R06-FAILURE-SEQUENCES-FOLLOWUP` (planning R06), attempt
  `fbefa4a1790247f9851c73e016e1dd4f`, agent `c95e1722350849bca846b237c1f60997`,
  criteria `e9207e45980f6e9e7207c3a1b328c1a3911cb9f6835fb6d3fc78ea81367eb4db`.
- Parent: I-R06-FAILURE-SEQUENCES (merged PR #123); accepted runner
  re-verified by this attempt: `failure_sequences.py` sha256 `d3e11285…`,
  suite `283efad2…`, reference ledger at base `9afbddcd`.

## The adapter (`implementation.py::run_entry`)

1. **Identity first**: runner + suite sha256 pins and the reference
   extraction ledger must verify BEFORE anything runs; a tampered copy is
   refused (`IdentityFailure`) — tested with a sabotaged isolated copy.
2. **Clean run**: the runner CLI reproduces **8/8 sequences PASS** against
   the ledger-bound pinned product classes (SessionFlow→FocusPolicy→
   InputMapper, base `9afbddcd`).
3. **Suite**: the accepted unittest suite passes via subprocess (exit 0).
4. **Injected-counterexample detection**: the runner's OWN deliberately-
   broken `LatchingMapper` control replayed through SEQ-01 — DETECTED
   (`passed: false`, violation `zombie…`, control identity recorded), using
   the same call shape the accepted suite's BrokenControls test uses.
5. Output `regression_entry_result.json` carries `device_testing_claimed:
   false` and the headless-CPU note (card falsifier law).

## Measured

`python -B implementation.py` → all_ok true (clean 8/8, suite OK, detection
true). `python -B -m unittest test_implementation -v` → **7/7 OK**.

## Falsifier scorecard

- New sequences/fuzz added: NOT FIRED (adapter only invokes).
- Device testing claimed: NOT FIRED (explicit false flag).
- Unverified runner invoked: NOT FIRED (identity gate + tamper test).
- Counterexample passing undetected: NOT FIRED (latch caught, zombie
  violation recorded).
- Production patch: NONE — the clean run reproduced 8/8; no retained failing
  counterexample exists (the card's own condition for a patch).

## Preserved gates

Runtime/visual/device gates remain with their owning cards; this entry is
headless CPU regression only.
