# fleet-maintenance-amendment-01 result (2026-09-11, lead lane)

Prereg `c56006c5` precedes the amendment `977e7dcf` (+62/−0, append-only)
and the repin `e81585ca` (three literals, provenance comment updated).

| Prediction | Outcome |
|---|---|
| amendment append-only, single dated section | PASS (+62/−0) |
| fresh measured counts at amended head, pinned, suite green | PASS (89/127/2692; catalogue 23/23; full fleet 198/0/1 skip) |
| perturbation moves counts and fails the pins | PASS (2694≠2692, 90≠89 at the repinned head) |

Retained correction: the first perturbation attempt rooted its throwaway
worktree at the operator checkout's HEAD (wrong base; confounded failure) —
documented in MEASUREMENT.json; the operator checkout was never written.
