# FIVE-CLIENT-COORDINATION-20260909Z-A — scripted five-client coordination verified

Record of `tools/agent_fleet/five_slot_coordination.py` run against a FRESH
isolated five-slot registry with the REAL control service and five REAL
authenticated HTTP clients.

LABEL: **scripted clients.** This record does NOT certify the milestone
"five independent agents verified" — that milestone requires Alan to start
one fresh agent for an independent trial (see `docs/THE_AGENT_FLEET.md`).

## Preregistration (written before the run)

- STATEMENT: five isolated clients coordinated through one controller exhibit
  capacity, FIFO resource fairness, benchmark isolation, memory admission,
  fail-hold + recovery, bootstrap guards, restart durability, the evidence
  gate, and deadlock-free progress WITHOUT any cross-client mutation.
- PREDICTION: scenarios S1–S9 all end PASS on a fresh isolated registry.
- FALSIFIER: any scenario ending FAIL, or any partial state observable in the
  exported snapshots.

## Scenarios (all over the live HTTP path)

| id | scenario | falsifier it closes | result |
| -- | -------- | ------------------- | ------ |
| S1 | CAPACITY: sixth claim (5 slots busy) refused; registry unmutated | no_free_slot without revision change | PASS |
| S2 | FIFO CONTENTION: later rtx request queued; earlier waiter granted on release | out-of-order grant | PASS |
| S3 | BENCHMARK ISOLATION: benchmark waits under utilization, grants on an empty GPU, excludes interactive while held | benchmark stealing or granting while GPU busy | PASS |
| S4 | MEMORY ADMISSION: over-budget request stays queued (all-or-nothing), auto-grants on release | over-budget grant or silent drop | PASS |
| S5 | FAIL-HOLD + RECOVERY: failed owner's task → RECOVERY_HOLD and resources retained; recover gated on drain (`resources_still_held`); fresh generation on reassignment | lost work / premature recover | PASS |
| S6 | BOOTSTRAP GUARDS: foreign listener and duplicate start both refused | conflicting listener or second fleet instance | PASS |
| S7 | RESTART DURABILITY: managed restart preserves revision, epoch, leader, all 5 claims (owner/slot), and the pre-restart session token | dropped claim / invalid token after restart | PASS |
| S8 | EVIDENCE GATE: review refused while resources held; gate clears after drain | review with unreleased resources | PASS |
| S9 | DEADLOCK-FREE PROGRESS: overlapping wants (functionality vs benchmark vs memory) all eventually granted in FIFO order; benchmark gates on full-machine drain; no unserved queue entries remain | circular wait / stale arrival | PASS |

`all_pass: true` (9/9).

## Verified facts

- Every scenario ran through `client.py` HTTP calls with distinct per-agent
  session tokens plus the supervisor token; the isolated service was spawned
  and torn down by `bootstrap_fleet.py` (controlled, acknowledged).
- Configurations that would have been mutated by a bug are asserted from the
  live snapshot, not from memory of the request: grant revisions,
  enqueued-revision order, retained-resource keys, and queue `served` flags.
- Registry final state exported to `FINAL_SNAPSHOT.json` (revision 49, epoch 1,
  leader a1, five coord-* tasks RUNNING, `coord-sixth` READY/unclaimed).
- Machine-exclusivity of `gpu_benchmark` observed live: after releasing the
  rtx holder, the benchmark stayed stalled with `benchmark_exclusive:other_hold`
  while another task still held memory, and granted only on full-machine drain.

## Files

- `COORDINATION.json` — per-scenario PASS/FAIL machine record.
- `FINAL_SNAPSHOT.json` — registry state at teardown.