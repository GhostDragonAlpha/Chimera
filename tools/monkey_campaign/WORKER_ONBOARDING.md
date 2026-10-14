# Current operating method — file packages and the continuous scheduler, 2026-10-01

Read [docs/WORKFLOW.md](../../docs/WORKFLOW.md) first (the method map), then
[NO_WORKTREES.md](NO_WORKTREES.md) and runner_profile.json. New attempts use pinned
file packages from canonical `worker_start.py` startup with your existing arrival ID;
no new clones or worktrees; CPU commands run through `task_package.py` (four slots;
BUSY/exit 75 means back off). Capacity truth is the registry's per-card attempt
records: 12 target / 15 ceiling API agents including descendants, four CPU package
slots, one publication writer, GPU work through the existing GPU queue. Dispatch is
advised by the continuous scheduler
(`E:/ChimeraWork/monkey-coordination/compiler-scheduler/scheduler.py`, serving since
2026-10-01) and consumed by the Lieutenant; you claim work through the registry
join/claim path, never by inventing an assignment. Handoffs --finish, --submit-pr
and --review-result deal the next card only with the explicit `--take-next` flag;
--checkpoint and --park never re-deal. Acceptance runs through the acceptance-chain
packets; evidence anchors through the evidence-store before anything references it;
the 150G free-disk floor stops new dispatches when crossed. The ten-worker limit,
hourly handoff mechanics and EXECUTION_QUEUE/execution_plan.py coordinator wording
below are historical layers from before this method; where they conflict with this
section, this section and docs/WORKFLOW.md govern.

# Material-first scope — astra-0031

Read [MATERIAL_PLAN_ADOPTION.md](MATERIAL_PLAN_ADOPTION.md). Use canonical startup, your existing arrival ID, and the returned MAT2- assignment. Prior ONT- work is archived evidence, not an active claim. Do not ask the operator for a new goal or recreate completed implementation.

# Current delivery direction — astra-0030

[DELIVERY.md](DELIVERY.md) governs priority, bounded review and integration reporting. Read it before applying older maximum-parallel wording below.

> astra-0012: use KANBAN.md. PR submission and task-ID inboxes replace the old exclusive queue and hourly handoff below. Reports do not close cards.

> astra-0011: startup offers ready implementation as well as diagnostic/review briefs.
> Execute code/tests where the brief explicitly grants its unique output workspace;
> no coordinator impersonation or new permission is required. --finish hashes required
> source/test artifacts as well as the report. Preserve existing claims and continue.

# Worker procedure â€” internal reference, not another onboarding prompt

The sole user-facing entry is `E:/PythonChimera/docs/MONKEY_RUN.md`.
Its first action runs `worker_start.py`: instruction verification, real orientation,
shared-status inspection, and transactional task/slot assignment. Successful arrivals
are registry events; only genuine unresolved questions go to the mailbox.
No hand-authored arrival JSON or separate goal prompt is needed.

Retain the returned arrival ID and use it on retries. Check for an existing native
claim before taking another. Arrival IDs are explicitly unauthenticated intake IDs;
they do not grant filesystem ownership or certify harness capacity.

For completion, review, corrections and hourly recovery, follow CONTINUOUS_EXECUTION.md.
Use the returned handoff_template with --finish to submit and receive next work in
one invocation. Use --checkpoint after ceasing writes at the hour boundary.
The existing coordinator commissions every selected task through its first unmet phase
using execution_plan.py; it must not wait for another operator goal prompt.

Workers continue their owned tasks through preregistration, derivation, implementation,
appropriate numerical/runtime/visual verification, independent review and integration.
Then acquire the next eligible unit. A small direct operator task takes priority after
ownership is reconciled. Architecture questions go to the suggestion box.

Use COORDINATION.md for slot/report contracts, hourly Central deadlines, GPU rules and
recovery. Use SUGGESTION_BOX.md for questions and answers. Astra checks only when the
operator messages Astra; there is no automatic lead wakeup. Preserve protected training
across reporting-lease expiry. Do not reuse a slot until the previous worker has stopped.

The coordinator uses useful available subagents up to the shared ten-worker limit and
the lower real harness/controller/resource limits. Do not duplicate work to fill capacity.
Never mark the game complete without its required evidence and operator acceptance.

Startup now also reads EXECUTION_QUEUE and atomically claims a bounded diagnostic task
and free slot. Execute the returned brief immediately; no second goal prompt or HTTP
prototype enrollment is required for that explicitly scoped work. Recover an existing
owned task instead of double-claiming. Native/source/hardware assignments outside these
briefs still follow the current coordinator. An arrival alone is not a claim; the
returned ASSIGNED record is the bounded claim. Worker execution is never inferred from
a claim record. Read DOC_AUDIT.md for the live plan and acceptance corrections.
