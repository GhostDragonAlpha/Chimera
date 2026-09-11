# Run queue: execution contract and verified limits

## Current acceptance status

The live SQLite controller is the durable task authority. `run_queue.py` is an
in-memory reference only. Earlier descriptions calling that module durable, or
describing the claim-printing poller as a coding worker, were incorrect.

The execution correction requires an explicit executor profile before enrollment
or a continuous claiming loop. The profile contains an `argv` array whose first
entry is an absolute executable path. The child receives a JSON task envelope
on stdin and runs in the controller-provisioned Git worktree. A provider adapter
must consume that envelope and invoke the actual coding model. Python fixture
commands are orchestration tests, not evidence that a model can execute tasks.

Each worker resumes its own RUNNING/BLOCKED task before claiming more work. An
OS lock on its private session path prevents two pollers using that same path.
This is not a lock across copied credentials or separately started model tabs.
Successful process exit does not accept a task: without controller review
submission the task is checkpointed BLOCKED. Timeouts retain ownership pending
actual descendant/resource drainage. They never automatically reassign work.

`timeout_seconds` in an executor profile is an operational direct-child limit;
the default is 900 seconds, not a physical parameter or a convergence criterion.
No shell interpolation is used. Supervisor/enrollment environment credentials
are excluded from the worker. The launcher reports only process creation, not
model readiness or successful work. `--out` remains an alias for `--session`.

The integration test `tools/agent_fleet/test_execution_proof.py` uses an actual
temporary HTTP controller, SQLite restart, three identities, three Git working
directories and a three-process barrier. It checks concurrent execution, unique
claims, resumption, missing-provision refusal, lock exclusion, review-only
completion, and timeout ownership retention. No production tasks are consumed.

Still OPEN: deployed provider adapter/readiness handshake; automatic physical
provisioning and preservation; authenticated PR broker/handoff daemon; process
tree observer and restart recovery; multi-model live acceptance. The installed
Freebuff help exposes interactive operation and `--cwd`/`--continue`; unattended
stdin task execution has not been verified. Do not start generic pollers and
call those coding agents. Slot 1 owns completing these integrations; Alan is not
the launcher or the recovery mechanism.

The sections below describe the earlier prototype. This acceptance statement
supersedes its timeout/requeue and durability claims; historical Git revisions
preserve those prototypes unchanged.

`tools/agent_fleet/run_queue.py` is a reference layer of the continuous
workflow. It is a pure state machine: it does not run Git, the engine, a model,
or a network request. The controller adapter remains responsible for authenticated
claims, isolated worktrees, resource reservations, branch publication, and PRs.

The queue has four relevant states: `READY`, `RUNNING`, `REVIEW`, and
`INTEGRATED`. Dispatch is deterministic (priority, then enqueue order). Every
running assignment has an owner, generation, and expiring lease. Expiry enters
`RECOVERY_HOLD` and retains ownership until evidenced recovery. Submitting review releases the
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

`tools/agent_fleet/launch_worker.py` is the trusted launcher boundary. It
enrolls a fresh identity, qualifies it through the supervisor path, removes
service secrets from the child environment, and starts the worker with only its
private session-file path. It refuses to overwrite an existing session file.
The launcher does not provision worktrees; a claimed task still requires the
documented supervisor provisioning step.
