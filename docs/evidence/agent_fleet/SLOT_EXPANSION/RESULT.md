# fleet-slot-expansion-03 result (2026-09-11, lead lane, operator priority)

Prereg `4bb3e143` precedes implementation. Operator directives: 4e55c08a
(grow to the empirical limit; I/O hypothesis), dbd97562 (worktree
semantics).

| Prediction | Outcome |
|---|---|
| existing registry unchanged on reopen | PASS (byte-equal slots) |
| spawn/retire with named refusals | PASS (busy/provisioned/slot-1/unknown/kind/supervisor/guard) |
| claim auto-spawn end-to-end + stale-provision NOT masked | PASS (slot 6 claim->checkpoint; stale provision still refuses by name) |
| scale probe: zero lock errors, latency measured | PASS mixed (1456 ops, 0 locked, p50 13.6ms); saturated profile recorded (max 5s waits at the single-writer store - the predicted I/O boundary) |
| inventory default-5 compat | PASS |
| full fleet suite green | PASS 222/0/1 (one non-reproducing capture flake retained in the first output) |

Two old-design tests re-specified to the new contract (named in
MEASUREMENT) - the count wall they pinned is deliberately superseded;
the new guarantees are pinned in test_slot_expansion. Test-found
implementation fix: the guard binds the NEXT id, not the count (retired
ids are never reused) - a count-only guard crashes past the layout bound
instead of refusing by name.
