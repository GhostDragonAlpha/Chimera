# Work continuously toward the playable monkey

## Continuous execution: astra-0009

Read [CONTINUOUS_EXECUTION.md](../tools/monkey_campaign/CONTINUOUS_EXECUTION.md).
Every approved requirement now has a complete phase/calculation packet from
execution_plan.py. Reconcile existing receipts and execute the first unmet phase;
do not wait for the operator to write another task prompt. The existing coordinator
commissions production work using its actual source/resource claims and real harness.

Bounded workers use startup's handoff_template with --finish to submit evidence,
release their slot and receive next work in one invocation. Independent reviews are
automatically offered to other workers. Use --checkpoint after ceasing writes at the
hour boundary to preserve and recover unfinished work. The coordinator can publish
bounded follow-ups and explicitly request corrections through queue_control.py.
Successful arrivals no longer fill the suggestion box. Missing orientation refuses
new assignment. No status response or exhausted bounded queue completes the game.

These commands supersede older arrival-only and manual bounded-handoff wording below.
Existing production claims and protected jobs remain intact. A process does not execute
merely because a task was claimed; use real dispatch/wait and inspect actual outcomes.

## Current task authority and written plan

Execute worker_start.py below. It now reads the approved plan and EXECUTION_QUEUE,
and returns a concrete bounded task with a transactional shared-slot claim, or a named
blocker. For these lead-issued diagnostic briefs, that claim plus the complete brief
is the authorization; enrollment in the separate HTTP prototype is NOT a prerequisite.
Existing coordinator/source/hardware claims remain authoritative for other work.
Read [DOC_AUDIT.md](../tools/monkey_campaign/DOC_AUDIT.md) for corrected completion
semantics, the W03 versioned-anchor ruling, and current critical-path task details.
Never use an engine hierarchy term as your agent identity.


## OPERATOR EXECUTION ORDER

When the operator supplies this file as onboarding, execute it now. This is an
assignment to work on the playable-monkey goal, not a request to summarize the file.
Do not ask whether to execute, review, orient, or choose a goal. Your immediate assigned
action is the worker_start.py command below, followed by campaign validation and recovery
of an eligible owned task. Report actual tool results and continue permitted work.

The first startup command performs bounded CPU/file intake. The existence of later GPU,
disk and subagent policies is not a reason to ask permission for that startup command.
Resource ceilings are ceilings, not instructions to consume them. Subsequent GPU work,
training and write operations still require their actual task claims and existing gates.
Do not reinterpret this order as permission to take leadership, invent native credentials,
skip registration, or launch unqualified training. If a required tool or claim is missing,
execute the permitted startup steps, record the exact failure and preserve the request.
Explicit later operator requests to review only, pause or stop override this default.


## START HERE — the only onboarding entry

You have been assigned to advance the approved playable monkey in the forest. Start
now; do not ask the operator for another goal or a choice of startup activities.
Run this command yourself before returning a status-only response:

```powershell
python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py
```

It verifies instructions, reads the sealed plan, runs orientation, records your arrival,
and atomically reserves a ready bounded task and reporting slot. Save the returned
arrival ID; on retries use `--arrival-id <that-ID>`. An arrival alone is not a claim;
`assignment.state = ASSIGNED` supplies the claim and complete authorized brief. Execute
that brief immediately. `RECOVER_OWNED_ASSIGNMENT` means resume the recorded task,
subject to its lease. Other responses name the actual blocking condition. If already coordinating, reconcile your actual workers and assignments
instead of waiting for a second prompt. Never invent enrollment or write ownership.

The operator gives agents THIS FILE. Linked documents and CLI commands are internal
implementation instructions, not alternative prompts for the operator to choose from.
If startup fails, report its exact error and preserve existing work; do not ask
"what do you want?". Read the remaining directions and follow the verification loop.


<!-- CHIMERA_LEAD_CONTROL
{
  "schema": "chimera.lead_instructions.v1",
  "lead_id": "astra-codex",
  "revision": 9,
  "revision_id": "astra-0009",
  "scope_sha256": "5b07ce0c49c6a8cae42bc4f04ebce8d2835104d5591df4f1feecf7fa0dc56a00",
  "files": [
    "docs/MONKEY_RUN.md",
    "tools/monkey_campaign/COORDINATION.md",
    "tools/monkey_campaign/CHECKPOINT_WORKFLOW.md",
    "tools/monkey_campaign/decisions/20260924_campaign_handoffs.md",
    "tools/monkey_campaign/monkey_completion_map.json",
    "tools/monkey_campaign/APPROVED_SCOPE.json",
    "tools/monkey_campaign/instruction_state.py",
    "tools/monkey_campaign/agent_slots.py",
    "tools/monkey_campaign/campaign.py",
    "tools/monkey_campaign/checkpoints.py",
    "tools/monkey_campaign/integrity.py",
    "tools/monkey_campaign/Invoke-MonkeyCampaign.ps1",
    "tools/monkey_campaign/WORKER_ONBOARDING.md",
    "tools/monkey_campaign/SUGGESTION_BOX.md",
    "tools/monkey_campaign/suggestion_box.py",
    "tools/monkey_campaign/MONKEY_COMPLETION_MAP.md",
    "tools/monkey_campaign/worker_start.py",
    "tools/monkey_campaign/SCOPE_AMENDMENT_20260924.json",
    "tools/monkey_campaign/EXECUTION_QUEUE.json",
    "tools/monkey_campaign/task_queue.py",
    "tools/monkey_campaign/DOC_AUDIT.md",
    "tools/monkey_campaign/execution_plan.py",
    "tools/monkey_campaign/queue_control.py",
    "tools/monkey_campaign/CONTINUOUS_EXECUTION.md"
  ]
}
CHIMERA_LEAD_CONTROL -->

## Current lead instructions: astra-0009

The operator designates **Astra/Codex as lead developer**. The lead publishes overall
instructions here; workers report progress and propose changes separately. Only the
operator can replace the lead. The approved feature scope and acceptance bar stay sealed.
Read the canonical file at `E:/PythonChimera/docs/MONKEY_RUN.md`, including from worktrees.

**Universal onboarding includes bootstrap:** an existing coordinator reconciles its
real fleet and provisions assignments; a new worker records its arrival before requesting
work. Follow the universal prompt and arrival schema in WORKER_ONBOARDING.md. Neither
role waits for a second goal prompt. Missing access is recorded as a concrete request.

**Worker entry is an assignment to start:** automatically orient, recover/claim the
next eligible playable task, and execute. Do not ask the operator to choose a startup
activity. Follow the onboarding's mandatory commands and concrete bootstrap-failure path.

- **New or returning workers:** [universal onboarding prompt](../tools/monkey_campaign/WORKER_ONBOARDING.md).
  A direct small request from the operator becomes that worker's scoped task, with
  existing ownership reconciled. Architecture questions go to the lead.
- **Coordinator:** [lead revision pickup, ten shared agent slots and hourly memory](../tools/monkey_campaign/COORDINATION.md).
  Read and acknowledge this revision; adopt actual existing workers before admitting
  new ones. Ten model-agent reporting slots do not increase native writer/GPU capacity.
- **Suggestion box:** [submit questions and read lead answers](../tools/monkey_campaign/SUGGESTION_BOX.md).
  Astra checks it **only when the operator messages Astra**. No scheduled lead review,
  automatic wakeup or endless lead loop. Workers continue independent permitted work.
- **GPU priority override:** the operator explicitly permits training to interrupt
  gaming and local inference. Any authorized worker may request a handoff; only the
  existing supervisor executes it. Follow the [GPU handoff specification and implementation queue](../tools/monkey_campaign/COORDINATION.md#gpu-handoff-training-can-preempt-gaming-and-local-inference).
  This specification is published; automatic game/model handoff is not yet deployed.
  Existing training stays protected. Do not substitute forced termination for a failed
  graceful release, or assume an unloaded model cannot reload on the next request.
- **Worker deadlines:** next top of the hour on **Windows system Central Time**, with
  daylight saving handled by Windows. A :40 registration expires at the next :00;
  reports do not extend it. Preserve work and confirm cessation before reassigning.

Before dispatch, after completion, before publication and at the hour boundary, read
`instruction_state.py` and the current policy bundle. A new revision requires the
coordinator's own acknowledgement; the lead never fabricates a read receipt for GLM.
The bundle fingerprint detects drift relative to a saved acknowledgement. Lead-only
editing is an operator rule; current shared-account Windows ACLs do not enforce it.
This metadata supplements the existing native controller; it does not replace it.

**This is the single file the operator gives the coordinating agent.** You follow
the linked machinery; the operator does not assemble another multi-part prompt.

> Complete the playable-monkey list. Keep the maximum useful number of actual
> subagents running within the harness, controller, disk and machine limits.
> Refill free slots, integrate verified work, reclaim your disposable outputs,
> checkpoint, and continue until the selected game is complete or all remaining
> work requires a named external decision or unavailable resource.

[Astra campaign decisions and next assignments (2026-09-24)](../tools/monkey_campaign/decisions/20260924_campaign_handoffs.md)
Read this supplement when reconciling the completed campaigns. The approved-list fingerprint and acceptance gates remain unchanged.

## Current execution priorities

Follow the execution-plan refinement in [COORDINATION.md](../tools/monkey_campaign/COORDINATION.md#execution-plan-refinement-astra-0007).
The immediate playable checkpoint is controlled walking with a camera in one clearing;
the final goal still includes the full ground-tree-ground loop and all selected requirements.
Preserve active assignments and protected training; apply sequencing changes at checkpoints.
The scope pin below includes the operator-authorized P04 training-priority correction,
recorded in SCOPE_AMENDMENT_20260924.json. Reverting that one field recovers the old pin.

## 1. The goal and the approved list

The goal is one physically controlled monkey in a small forest: walk on all fours,
steer, stop, approach a rigid trunk, attach, climb, hold, descend, release and walk
again, with a usable camera and complete player flow. Keep broader Chimera features
in the later backlog. The architecture, frozen walking runbook and falsifiers remain
in force. No kinematic locomotion substitute or invisible support force is permitted.

Read `tools/monkey_campaign/MONKEY_COMPLETION_MAP.md` for the scope, existing receipts,
83 work items, 28 calculation contracts, dependencies and completion conditions.
The matching JSON contains the task definitions, not live progress.

Default selection: 76 core/product items; the seven conditional material/assembly
items become required only if the selected playable build consumes them. Preserve
ongoing explicit assignments on that branch. Do not interrupt authorized walking
training to complete an unrelated compiler or catalogue.

Product-decision cards remain required decisions; they are not permission to invent
the operator's tastes. Implement independent parts while awaiting the few decisions
that cannot be derived or recovered from existing instructions.

**Scope fingerprint (`sha256-chimera-json-v1`):**

`5b07ce0c49c6a8cae42bc4f04ebce8d2835104d5591df4f1feecf7fa0dc56a00`

The operator's copy of this fingerprint in the commissioning conversation is the
trust anchor. Record it with the trusted coordinator/controller outside worker write
scope. Never derive a replacement expected value from an edited list or lock file.
`APPROVED_SCOPE.json` is a convenient comparison copy, not an authentication key.

Hash definition: decode UTF-8 JSON (optional BOM), reject duplicate object keys and
non-finite values; serialize sorted object keys with Python JSON `ensure_ascii=False`,
`separators=(',', ':')`, `allow_nan=False`; UTF-8 encode; SHA-256. Array order is significant.
This is an explicitly named project encoding, not a claim of RFC 8785 conformance.
Raw-file SHA-256 is recorded separately. Formatting/newline changes may preserve
content identity, but goals, dependencies, scopes and acceptance changes may not.

**Requirements are sealed; progress is not.** Workers update checkpoints and evidence
in the existing controller. They propose list changes in separate artifacts containing
the previous digest, exact diff, rationale, affected dependencies and proposed digest.
The lead may split a task into implementation subtasks without changing its meaning;
it cannot quietly remove requirements, weaken criteria, or declare a blocked task done.
New scope approval comes from the operator. Keep prior approved versions and failed runs.

The hash detects unauthorized list changes relative to the pinned value. It does not
stop a process with write access or authenticate a human. Stronger authentication
requires an external verifier and human-held signing key unavailable to the fleet.
No secret key or digital signature is created or claimed by this package.

## 2. Recover the existing system first

Read current operator directions, `AGENTS.md`, `docs/AGENT_START.md`, and the existing
fleet/controller contract. Newer operator gaming rules override historical visible-
editor/window rules. Read `E:/ChimeraWork/lane-archive/MACHINE_FINDINGS.md` before host
diagnosis. Use PowerShell `.ps1` mechanics; do not paste inline dollar commands.

Use the launcher-provisioned ordinary session to read the existing controller. Never
print credentials or obtain supervisor secrets to manufacture permissions. Do not
start a second registry, duplicate task board, or replacement service. No service
restart, database reset, mass worktree migration or takeover is implied by this entry.

Map the 83 planning IDs onto existing native/controller tasks by meaning and receipts.
The JSON's `UNRECONCILED` means this review did not establish current acceptance; it
does not mean the implementation is missing. Store the ID crosswalk and disk forecasts
in a coordinator-owned bindings file using `bindings.example.json` as its format.
Live ownership, status, generations and integration evidence remain controller-owned.
Create missing tasks through the authorized controller, with real scopes, capabilities,
base revisions, dependencies and packets. Reuse existing integrated work.

The inspected older controller exposes five source slots, one reserved for integration.
Do not claim it supports ten writer slots. Determine the live deployment's capacity.
Fill every available legal slot; bounded read-only reviews may share a pinned checkout
if the actual controller/harness permits it. A capacity extension belongs to P04:
implement and test it in isolation, preserve IDs/claims/storage limits, and use the
trusted rollout path. Do not manually edit a running registry to bypass the limit.

If this agent has no actual subagent tool, report `DISPATCH_UNAVAILABLE` immediately.
Keep any existing authorized useful task; do not label sequential packages as agents.
The next delegation-enabled coordinator can resume from the same entry and records.

## 3. Continuous maximum-parallel loop

Follow [the checkpoint workflow](../tools/monkey_campaign/CHECKPOINT_WORKFLOW.md) for every
assignment: implement, verify numerically, exercise the runtime, actually inspect visual
evidence, review/integrate, and advance to the first unmet checkpoint. Offline-only work
needs a predeclared nonvisual rationale; motion needs motion evidence. The executable
`checkpoint` action checks record bindings and evidence-file hashes, not pixels or human consent.

Keep the persistent goal active until the selected requirements and final integrated
playthrough have their numerical/runtime/visual evidence and explicit operator acceptance.
An interim status response is not a completed goal. While children remain active, use the
actual harness completion/wait mechanism, process results, and refill legal slots. Prove
continuation by observing successive completion-to-next-action events without another
operator prompt; do not claim these documents alone supply a missing scheduler.


1. Verify the approved-list fingerprint and obtain a fresh controller snapshot.
2. Recover your live claims before creating work. Read actual harness capacity and
   count active children, including reviewers. Preserve other agents' assignments.
3. Select independent ready work: current walking blockers first, controls/forest in
   parallel, supported grasp/climbing next. Existing evidence can close a prerequisite;
   a report's existence alone cannot. Decision or missing-data tasks are real work.
4. Admit tasks only within remaining harness capacity (initial campaign cap 10),
   controller slots, non-overlapping scopes and declared disk growth. Reserve CPU/GPU/
   memory and processes through the existing supervisor/broker before execution.
5. Use real native subagent dispatch. Supply one bounded task, its exact base/claim,
   owned paths, calculations, preregistration, resource allowances, deliverables,
   reviewer and stop rule. Keep a durable mapping from real agent ID to claim and slot.
6. Collect outcomes as they arrive. Refill freed slots with ready implementation or
   independent review. Do not wait for the slowest task before advancing unrelated work.
7. Review, integrate, record acceptance and reuse the workspace. A worker's PASS or
   commit is not integration. The current publication authority serializes integration.
8. Audit retained disk and evidence, checkpoint the exact next actions, and repeat.

Continue across batches and context refreshes. Do not end because one agent blocks,
one batch finishes, or a status report was produced. During a temporary resource or
quota wait, checkpoint and use the harness's supported wait/resume behavior; never
claim you can continue after a terminated session without a real supervisor/wakeup.

Target ten useful concurrent children if allowed, adapting the mix of implementers,
reviewers and integration assistance to ready work. Do not manufacture tasks or duplicate
audits to reach ten. Report the concrete constraint when useful concurrency is lower.
Explicit operator stop, budget limits, quota and safety boundaries always take priority.

## 4. Bound disk growth before it happens

Reuse a bounded pool of existing source slots. Do not create a new clone/worktree for
every task or every retry. Shared Git objects save history storage; checked-out files,
builds, downloaded assets and evidence still consume disk.

Initial administrative guardrails, not measured physics limits:

- Leave at least **100 GiB free** on the working volume after admitted growth forecasts.
- Keep total **outstanding additional growth at or below 160 GiB** for the host tasks
  included in this campaign's admission calculation. This does not measure total
  historical storage or impose an OS quota. Reconcile other active writers too.
- Forecast each task's peak checkout/build/scratch/evidence growth before admission.
  Missing forecast means measure/derive it before large writes; never assume zero.
- Permit at most ten worker source slots plus the existing integration workspace,
  subject to the controller's lower actual limit. Reuse existing slots before creating any.
- Share immutable assets/models through approved read-only references. Never share
  mutable build outputs between slots or misattribute a reused executable's identity.
- Rotate operational logs. Keep minimum reproducibility inputs, results, failed-run
  evidence and necessary captures; remove duplicate generated intermediates after
  preserving what the relevant preregistration requires. Do not erase failures.

The coordinator serializes admission decisions, subtracts active outstanding growth
as well as new batch forecasts, and checks free space before every build/download/
capture batch and at integration. Avoid continuous expensive directory scans while
gaming. If a forecast is exceeded, stop that task's new disk-producing work at a safe
boundary and re-evaluate. Never kill a protected training run to reclaim space.

For cleanup, require all of: exact fleet-owned path within the designated workspace;
verified inactive claim and drained processes; required evidence preserved; every
needed Git tip has a durable ref; no uncommitted/untracked/ignored unique work remains.
Inspect ignored files too. A clean Git status does not prove a directory disposable.
Do not traverse junctions/symlinks into other roots. Delete only named disposable
outputs or remove a qualified worktree through the trusted cleanup path. Never use
broad process-name kills, `git clean -xfd`, age-only deletion or recursive root removal.
Protected/dirty/locked/preservation trees remain untouched.

If preserved evidence fills the budget, queue bulk work and report the exact storage
need. Moving everything into an ever-growing archive is not reclamation. No finite
disk can retain unlimited outputs; the run must stay within its admitted budget.

## 5. Helper commands (the agent runs them)

`tools/monkey_campaign/Invoke-MonkeyCampaign.ps1` wraps the stateless Python helper.
It has no code that spawns models, mutates controller state or deletes files.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File 'E:/PythonChimera/tools/monkey_campaign/Invoke-MonkeyCampaign.ps1' -Action validate
```

The execution-policy setting applies only to that process; do not change the machine's
policy. For `packet` or `plan`, supply `-ApprovedSha256` with the pinned fingerprint above
(or the trusted-launcher-provided `CHIMERA_MONKEY_APPROVED_SHA256` environment value).
For a packet also supply `-TaskId W01`. For planning, supply `-SessionPath` with the
provisioned ordinary session, `-BindingsPath` with the reconciled crosswalk,
`-HarnessLimit` with the actual tool limit and `-ActiveSubagents` with the actual count.
`-SnapshotPath` is an offline alternative with a `captured_at_unix` timestamp and
`snapshot` object; snapshots older than 120 seconds are refused.

The planner provides recommendations only. The controller must still accept the
claim, the harness must actually launch the child, and the resource broker must admit
its execution. A helper result cannot override any rejection. `storage -ScanPath`
performs a bounded read-only logical-size scan; incomplete scans stay incomplete.

## 6. Completion and escalation

The selected goal is complete only when every selected requirement has scoped,
integrated evidence and the player acceptance task has actual human acceptance.
Do not count placeholders, skipped gates, stale evidence, partial reports or rejected
features as complete. Conditional items are never auto-activated merely to fill slots.

When all useful work is blocked, return one compact decision packet: affected IDs,
cause and evidence, work completed independently, smallest missing decision/resource,
and exact resume action. Do not keep repeating the same blocked work or issue empty
status updates. When a decision arrives, resume the original goal from the checkpoint.

Routine reports contain: accepted features, active actual agents, current blockers,
disk free/outstanding forecasts, next tasks and scope fingerprint. The operator should
not have to dispatch workers or manage their worktrees manually.

**First action:** verify the approved fingerprint, reconcile existing receipts and
controller bindings, recover active work, and fill every legal ready slot. Continue.
