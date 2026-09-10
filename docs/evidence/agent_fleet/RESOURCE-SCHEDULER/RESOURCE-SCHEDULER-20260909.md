# RESOURCE-SCHEDULER-20260909 — integrated fleet resource contract

Record for the resource scheduler layered onto the existing five-slot
controller (schema-1 additive, no live-registry schema change).

## Preregistration (written before the run)

- STATE: fair, deadlock-free resource scheduling can be added to the
  controller without breaking the legacy acquire/release semantics.
- PREDICTION: (1) grouped wants grant all-or-nothing; (2) same-resource FIFO
  holds (priority is a stamp; aging is the recorded waiting count); (3) the
  gpu_benchmark class requires an empty GPU and excludes every other GPU use
  while held; (4) memory admission refuses over-budget grants with an explicit
  allocation_failed state and admits declared-unknown memory uncharged;
  (5) pending requests are dropped with their owner's recorded failure and a
  task's recovery generation bump; (6) legacy `resource_acquire/release`
  still pass unchanged.
- FALSIFIER: a partial grouped grant, a same-resource queue-jump, benchmark
  coexisting with interactive GPU use, an over-budget memory grant, or a
  zombie request surviving its owner's failure.

## Mechanism

- Tasks may declare resources at creation (`create_task resources=[...]`).
- `resource_request` enqueues wants (strict FIFO per resource) with a priority
  stamp 0-9 and a waiting/aging counter (`waiting_revisions`). Grants are
  all-or-nothing within one BEGIN IMMEDIATE transaction.
- Grant promotion runs on release/clear/revoke/recover inside the SAME
  transaction as the releasing op (no partial states are ever visible).
- Physical GPU `rtx4090`; `dyad_eye`/`engine_demo` chain to it (same task);
  `gpu_benchmark` is exclusive of every other GPU-family use, including the
  same task's functionality hold.
- Memory is admitted against `memory.budget_mb` (persisted policy, default
  16384 MiB) as `memory.<request>` resource entries, so review/recovery/slot
  gates treat memory like any other held resource. `memory_mb: null` is the
  explicit unknown state: admitted, recorded, and NOT charged to the budget.

## Verification

- `tools/agent_fleet/test_resources.py` — 12 isolated-registry tests, all
  green (the listed falsifiers each have a named test).
- Full fleet offline suite still green: test_control + test_bootstrap (50)
  + test_resources (12) + test_bootstrap_fleet (4).
- Live registry (8099) reloaded with the scheduler under a controlled restart:
  revision 23, epoch 1, leader big-pickle, all five tasks RUNNING, all five
  slots occupied, queues empty, budget 16384 MiB — unchanged across the load.