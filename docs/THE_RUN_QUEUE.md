# Durable run queue

`tools/agent_fleet/run_queue.py` is the first bounded layer of the continuous
workflow. It is a pure state machine: it does not run Git, the engine, a model,
or a network request. The controller adapter remains responsible for authenticated
claims, isolated worktrees, resource reservations, branch publication, and PRs.

The queue has four relevant states: `READY`, `RUNNING`, `REVIEW`, and
`INTEGRATED`. Dispatch is deterministic (priority, then enqueue order). Every
running assignment has an owner, generation, and expiring lease. Expiry returns
the task to `READY` and fences the old worker. Submitting review releases the
worker lease immediately, but does not accept the change. Integration requires
the exact reviewed head, preserving slot 1's review authority.

## Statement, prediction, falsifier

**Statement:** a durable dispatcher can keep eligible work moving after review
or local hierarchy completion while preserving controller ownership and PR review.

**Prediction:** temporary-controller tests will show deterministic dispatch,
lease expiry, capacity reuse after review, and exact-head integration without
Git or engine mutation.

**Falsifier:** duplicate dispatch, stale lease acceptance, fabricated ownership,
review bypass, missing dependency refusal, or mutation outside the queue state.

The next implementation step is an adapter that calls the existing authenticated
controller operations and GitHub PR API. It must be tested against a temporary
store before any live service transition.

`tools/agent_fleet/run_queue_worker.py` is the worker-side adapter. It reads a
fresh authenticated snapshot for every cycle, attempts READY tasks in
deterministic order, and advances after a normal claim race. A successful
claim is only metadata; the worker must still verify and provision the returned
worktree before writing. The module has no direct database, Git, engine, or
credential output path. The `--poll-seconds` loop is deliberately separate
from task execution so build, runtime, and DYAD admission remain explicit.
