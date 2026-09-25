> astra-0011: bounded_implementation briefs explicitly grant code/test writes in their
> unique task output directory, including pinned dependency extraction and test fixtures.
> Required source/test artifacts are hash-bound at submission and rechecked by review.
> New workers can claim these directly. Existing coordinator publication also supports
> this kind with production_edit_allowed=false, owned_files and required_artifacts.
> Other production-source/hardware authority remains unchanged. This supersedes the
> diagnostic-only queue description below; no conditional requirement is activated.

# Continuous execution — astra-0009

## Whole-plan coverage

Run the execution_plan_command returned by startup, optionally adding --task W03
or another planning ID. Every one of the 83 original requirements has a packet:
exact acceptance, dependencies, calculation contracts, and the phases reconcile,
decide, implement, verify, runtime, visual, review, integrate. Default selection is
76; the seven conditional tasks remain inactive. Reconcile live code, board, bindings,
owners and receipts first, then commission only the first unmet phase. Existing work
is not missing merely because the catalog says UNRECONCILED.

Production tasks retain existing coordinator/source/resource/publisher authority.
The queue covers bounded diagnostic and review assignments. A packet is not permission
to edit arbitrary source or use the GPU. A reviewed diagnostic is not feature acceptance.
The coordinator must commission ready production checkpoints through its existing
working dispatch path rather than waiting for Astra to author every implementation step.

## Submit and immediately take next work

Retain arrival_id; reuse it or CHIMERA_WORKER_ID on every call. Startup returns your
handoff_template containing actual agent_id, slot and generation. Fill report_path with
an absolute nonempty report file inside your assigned output directory. Include the
actual checks, identities, failures and remaining limits. Set worker_finished_confirmed
true only after this work unit's writes and owned subprocesses have ceased.

```powershell
python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id YOUR_ID --finish E:/PATH/handoff.json
```

The command atomically preserves the report hash and releases your slot, then claims
next eligible work. Execute it immediately rather than ending at a status report.
If interrupted between submission and next claim, ordinary startup recovers; do not
blindly repeat --finish after an uncertain response. Inspect queue_control.py status.

Another worker receives independent review automatically. Its handoff additionally
uses the supplied reviewed_sha256 and verdict PASS or CHANGES_REQUIRED. Reproduce
substantive checks; hash equality alone is not review. Changed evidence refuses review;
an author cannot take their own review. Accepted bounded dependencies unlock successors.
Original game gates still require integrated numerical/runtime/visual evidence and
actual human acceptance where specified.

## Hourly recovery

At the next Windows Central top-of-hour, cease task writes and preserve a checkpoint
inside the assigned output directory. Use the handoff fields with --checkpoint instead
of --finish. This explicitly releases the old generation and makes the brief recoverable
with its checkpoint, then takes eligible work. It works after lease expiry. Silence
never causes reassignment, reporting never renews a lease, and old generations cannot
complete a reassigned task. Native tasks without a queue brief use their own recovery
procedure. No processes are killed or protected training interrupted by this helper.

## Coordinator loop

Read/acknowledge lead updates at checkpoints. Collect actual child results as they
arrive, review/integrate, and fill legal capacity through real harness dispatch/wait
tools. Inspect every selected packet and its first unmet phase, not only the original
three diagnostic briefs. Preserve active claims and reuse verified existing work.

Use queue_control.py status for bounded-task state. Publish a scoped follow-up with
queue_control.py publish --arguments FILE: coordinator_id plus brief, using
EXECUTION_QUEUE.json's brief shape. Include planning_ids, original falsifier/stop rule,
read_first, steps, deliverables, completion, and depends_on for bounded predecessor IDs.
Output must be monkey-coordination/task-results/<id>; forecast at most 16 MiB per brief.
Publishing grants no production edits or GPU access and cannot activate conditional work.

For a rejected review, queue_control.py rework --arguments FILE takes coordinator_id,
task_id and correction. Prior submission/review stay preserved. Corrections never
authorize another experiment forbidden by its stop rule or relaxed acceptance criteria.

When useful work is temporarily blocked, use the harness's supported wait/resume path.
Return a terminal blocker only when all useful work needs a named decision or resource;
include exact IDs, evidence and resume actions. Scripts do not launch language models
or resume a dead harness. No background Astra wakeup is installed.

## State and bounds

READY -> CLAIMED -> REVIEW -> REVIEW_CLAIMED -> ACCEPTED. Rejection becomes
CHANGES_REQUIRED until explicit rework. Checkpoint recovery requires cessation and
preserved evidence. Current live claims are not migrated or reset by installation.

Reports are at most 1 MiB; outside paths and junction/symlink traversal are refused.
Recovery metadata retains ten recent entries; actual failed evidence remains within
the task's storage budget. The queue accepts at most 160 commissioned records and never
silently recycles task IDs. Output budgets are administrative, not OS quotas. Identity
labels are cooperative records, not authentication under a shared Windows account.
