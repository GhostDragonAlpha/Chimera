# Five worktrees, one prompt, a replaceable lead

**Status: executable control-plane reference for review. Not deployed on Alan's
Windows machine. No current agent is migrated, stopped or reassigned.**

Alan authorized five reusable workspaces, task branches with lead integration,
a model-agnostic joining prompt, automatic leadership recovery beyond silence
checks, and multiple task workspaces per agent session. This document implements
that operating design without weakening the physics or protected-path rules.
The Master list remains the human/agent front door. Its live operational fields
must point to one controller snapshot after activation, not be separately edited
by every worktree. The holodeck book remains the feature/design catalogue.

## Architecture and what exists

`tools/agent_fleet/control.py` stores task, agent, resource, slot and leadership
state transactionally in one local SQLite database. `service.py` serves an
authenticated loopback API. `client.py` is the provider-neutral adapter;
`inventory.py` only measures directories and describes the proposed layout.
`test_control.py` exercises actual concurrent SQLite calls and real local HTTP.
None of these tools launches models, mutates Git, merges PRs, deletes files,
starts the engine or claims to be a filesystem security sandbox.

The service is an initial operational core, not a claim of an already self-
running software factory. The activation gates below name the remaining local
launcher, worktree, process-observer and GitHub publication integrations.

### One physical layout, five source slots

| Location | Purpose |
|---|---|
| `E:\ChimeraWork\repo.git` | Shared bare repository/object store; no sixth source checkout |
| `E:\ChimeraWork\slot-01` | Integration task workspace, claimable by the current lead |
| `E:\ChimeraWork\slot-02` through `slot-05` | Four worker task workspaces |
| `E:\ChimeraWork\control` | Durable state and trusted supervisor configuration, outside worktrees |
| `E:\ChimeraWork\evidence` | Preserved unpublished evidence pending GitHub integration |

Keep `E:\PythonChimera` and all active old checkouts untouched during rollout.
Slots belong to tasks; models/sessions are replaceable workers. The proposed
five-slot limit is the steady-state source-workspace limit. Existing legacy
copies mean migration temporarily occupies additional disk; report this honestly
and inventory before creating new copies. Never delete a legacy checkout just
because its model session ended.

A worktree shares Git objects and common repository resources, but has its own
checked-out files, HEAD and index. Each checkout and build still uses disk.
Worktrees are not nested repositories, containers, separate GPUs or a security
boundary. See [Git's worktree contract](https://git-scm.com/docs/git-worktree).

### A complete engine installation in every slot

Each slot, including the integration slot, owns an engine built from its task
branch. Do not borrow another slot's executable for a claimed test result.
The claim and inventory expose a matching engine plan:

| Per-slot location | Ownership |
|---|---|
| `.tmp/engine_build/` | That slot's CMake cache, native objects, executable and compiled shaders |
| `.tmp/engine_runtime/<unique-run-id>/` | That run's CWD, session snapshots, session log and studio state |
| `.tmp/engine_evidence/<unique-run-id>/` | Commands, identities, sidecars, captures and verdicts |

Candidate ports are 8101–8105 respectively. These are planned values, not
reservations. The launcher must check availability and record the actual
bound port and endpoint; a collision is a named refusal, never grounds to
kill an unknown process. Launch with `--no-restore` from the run's own CWD.
Resolve shader paths from the tested build's layout, and record executable
and SPIR-V hashes plus source HEAD, dirty diff, configuration and toolchain.
Never copy outputs to `ChimeraEngine/engine/build/`.

A launch manifest binds task ID, claim generation, slot, PID and process start
identity, executable, shader set, runtime CWD, endpoint and evidence directory.
Before any mutation/capture/shutdown the adapter verifies that binding.
PID alone is insufficient after process reuse. Slot reuse requires stopped
writers and preserved runtime/evidence files; stale artifacts must not be
reported as the new task's engine. Shared writable caches are not presumed safe.

Five installed engines do not imply five simultaneous GPU runs. CPU builds
may run in parallel within measured RAM/disk budgets. GPU tests and the
resident DYAD eye obey shared resource reservations; initially serialize
hardware runtime tests. The existing `engine_demo` reservation also remains
exclusive pending a tested launcher. No model is unloaded for slot testing.

Provisioning is still an activation gate: the reference returns plans and
checks their separation; it does not build or launch these five installations.
Windows acceptance must run each slot's own version, verify snapshot/log paths,
check that actions on one endpoint leave other sessions unchanged, and preserve
one failed/recovered run without corrupting its successor. STATEMENT: runtime
writes and control stay in their owning slot. PREDICTION: five distinct build
and run identities, no cross-slot mutations. FALSIFIER: shared session files,
wrong source/binary association, endpoint collision, foreign process control,
or any protected-path write. NOT_TESTED by the offline layout test.

### Multiple tasks per session

An enrolled session can claim up to its supervisor-approved `max_tasks` (1–5)
subject to the five global slots, task requirements and non-overlapping scopes.
Every checkpoint, resource request and review submission includes task ID and
claim generation. The reply includes the exact worktree and task branch.

The agent must use that worktree explicitly for each command; no session-global
`cd` assumption. It keeps a separate checkpoint and evidence stream per task.
One model can interleave tasks or use parallel tools if its environment supports
that; this does not create additional model context windows or give it access to
another provider's chat history. Published artifacts and checkpoints carry the
shared context. A session with only sequential tools should not claim a capacity
it cannot service usefully.

### Branch and GitHub contract

Each task ID creates exactly `astra/tasks/<unique-task-id>` from a recorded full
base SHA. Each PR targets `astra/gait-capture`. Branch identity follows the task,
not the reusable slot or model. Do not push different tasks onto one worker
branch. Do not check out a shared branch in multiple linked worktrees using
force/override options.

The slot-1 lead reviews and requests integration under the PR workflow below.
A trusted publication broker verifies:
current leader epoch, task branch, exact reviewed head, current integration base,
scoped diff, required evidence and branch protections. It then serializes the
actual GitHub operation and records the resulting commit. If the base changes,
reconcile and retest affected paths; never force-push to make a check succeed.
`master` remains untouched. New task branches do not authorize main-branch
merges. Alan's 2026-09-10 instruction authorizes workers to push their own task
branches and open PRs; it supersedes the earlier blanket worker no-push rule.
Use the provisioned GitHub identity; missing access is not permission to borrow
another agent's credentials.

The reference's `integration_request` stores a **pending intent**. It executes
no GitHub call. `ack_integration` accepts only a trusted publisher's result for
the current leadership epoch and exact stored base/head. It is not proof of a
real merge by itself; the publisher must supply actual GitHub evidence. Do not
advertise end-to-end merge fencing until the broker is deployed and tested.

### Pull request workflow

Alan's current direction (2026-09-10): workers issue their own PRs; the person
in slot 1 periodically checks for them and deals with them. This applies to
all project PRs, including existing and externally submitted ones.

- **Workers:** implement and test in their assigned worktree, checkpoint and
  submit review with the actual claim generation, push their task branch, and
  open a PR against `astra/gait-capture`. Include the task ID, exact commit,
  concise behavior change, executed tests, evidence and remaining gates. Use
  a draft when work or required verification remains incomplete. Respond to
  review on that branch; use the controller's review-requeue path before
  further edits to a frozen REVIEW task. Keep failed evidence and never
  force-push. No separate message through Alan is required to announce a PR.
- **Slot 1:** check the GitHub open-PR queue at the start of each active work
  turn, at task checkpoints and before selecting new work. Review new PRs and
  changed heads, request concrete corrections from their authors, verify the
  required evidence, and resolve integration order and conflicts. Track
  disposition through GitHub and the existing controller/Master list. Recheck
  the actual head and base before authorized integration; a review of an older
  head does not approve new commits. Keep slot 1's own PRs subject to independent
  review. Handle PRs through the authorized integration/broker path; workers
  do not merge their own work. When no PR needs action, continue slot 1's own
  assigned lane. PRs awaiting author corrections or external dependencies do
  not require idle waiting; return to the queue at the next checkpoint.
- **Recovery:** slot 1 is the PR responsibility of the current qualified lead.
  Follow controller election, epoch and workspace-preservation rules when
  transferring that role. A slot path alone grants no leadership or credentials.
  Report a role/assignment mismatch to the trusted launcher for reconciliation.

Periodic checks are an agent duty while active; this document does not install
a background polling service or claim that an inactive agent monitors GitHub.
PR ownership does not authorize unreviewed changes, weakened gates, controller
deployment or modification of the operator's checkout. Specific current user
restrictions still govern integration and publication.

Benign head changes are reconciled, not escalated (2026-09-10): refresh the
actual controller owner/generation and compare the expected head with the
read-only inspector `tools/agent_fleet/worktree_reconcile.py` (contract:
THE_WORKTREE_RECONCILIATION.md). Evidence-only descendant commits with
preserved staged runs need no operator confirmation: retain both, commit the
remaining own evidence, and submit the exact current head. Changed
implementation requires targeted revalidation; conflicting claims or history
route to the lead while other owned work continues. Never reset, clean, or
force-push to restore an old prompt. Git author is not authenticated identity,
and stronger client-instance fencing remains separate pending work.

Use cheaper subagents for bounded research, tests or independent reviews when
they can run usefully in parallel. The owning agent checks their evidence and
remains accountable. Helpers receive only the scope and access they need; they
do not inherit fleet ownership or supervisor authority. Avoid duplicate work
with live workers and do not use a model's name as proof of qualification.

## Leadership recovery stronger than a timeout

Silence is ambiguous: the agent may be computing, rate-limited, disconnected,
blocked on a tool, or gone. A heartbeat/elapsed-time alert can trigger a status
investigation but cannot prove failure or authorize taking its files.

| Signal | Action |
|---|---|
| Missing heartbeat or no recent file changes | `suspect`: preserve leader and claims; investigate |
| Explicit authenticated yield | Revoke that session; preserve its tasks; consider a ready successor |
| Trusted launcher observes its owned process exit | Record exact evidence, revoke session, initiate failover |
| Trusted provider adapter reports terminal failure | Record the provider event, revoke session, initiate failover |
| Operator revokes a session | Record decision and apply the same recovery rules |
| Unqualified agent claims another failed | Refuse authority-changing request |

The trusted observer is outside the model being monitored. A model cannot use
an accusation to grant itself leadership. UI processes remaining alive do not
prove the model is making progress; semantic stalls require corroboration and
an explicit revocation decision, not automatic inference from slow tokens.

Candidates must have independently recorded qualification, lead capability,
and an explicit readiness/recovery offer for the current epoch. A supervisor-
approved preference rank is policy, not a claimed intelligence measurement.
Selection is deterministic among eligible offers. On confirmed leader failure,
the controller changes leader and increments the epoch atomically. Previously
submitted integration intents become stale. If no eligible successor exists,
leadership remains vacant and the system reports the missing qualification or
readiness. It never assigns an incapable agent to keep a dashboard green.

Qualification and readiness cannot prove a candidate will never fail. Record
observed results and retain recovery paths. After an epoch change, standbys
refresh their recovery offers against the new state. A full controller restart
reopens the same durable state; it does not manufacture a new election.

### Fencing and the split-brain boundary

An epoch is useful only if the side-effect executor enforces it. The reference
rejects stale **control-plane** actions. It cannot revoke GitHub credentials,
stop an old tool process or prevent direct file writes by an agent sharing the
same OS user. Deployment must put integration credentials exclusively behind
a supervisor/broker and prevent ordinary sessions bypassing it. The broker must
hold the publication operation fence through the actual external side effect;
a token checked once before an asynchronous request is insufficient. Do not
elect a successor that can publish while an old broker operation is unresolved.

A single-host controller is chosen for five local slots. This is not a multi-
node consensus implementation. Do not start independent controllers on copied
DBs. If the controller itself fails, restart the single service with the same
store and keys; if the store is inaccessible, pause shared authority changes.
Do not promote local worktree snapshots into competing leaders.

## Task and resource lifecycle

Tasks enter READY, then RUNNING, optionally BLOCKED, then REVIEW. Worker reports
never directly mark INTEGRATED. The trusted publication acknowledgement closes
the integration gate. Slots remain held until a supervisor attests that changes
and required evidence are preserved and old processes/writers have stopped.
The tool never deletes the old directory.

A failed worker's tasks enter RECOVERY_HOLD with increased claim generation.
GPU/engine/DYAD resource reservations remain held because an external process
may still be active. Recovery requires observed process drainage and preserved
work. Only then can a replacement receive a new claim. New agents inspect the
checkpoint and exact source state; they do not redo successful history blindly.

An agent may hold several workspaces, but the RTX4090 reservation remains
exclusive, including for two tasks owned by that same agent. DYAD requires the
GPU reservation plus the eye reservation. Only the runtime owner initializes
DYAD under its documented protocol. No worker unloads the resident model,
changes another agent's engine or starts competing performance measurements.

Scoped writes are checked conservatively for overlap in the registry, including
case-insensitive Windows-style comparisons. This is coordination validation,
not enforcement of every shell write. Worktree executors and Git diff review
must enforce paths too. Broad scopes containing the protected build directory
are refused; reserve precise permitted files/directories instead.

## Disk policy and staged migration

Disk inventory precedes provisioning. Record shared Git bytes, each checkout,
active builds, retained evidence, caches, existing legacy copies and volume free
space. `inventory.py` reports logical file bytes, not allocated blocks or unique
deduplicated storage, and reports incomplete scans. It skips symlinks/reparse
points. Do not sum duplicate volume-free figures or overlapping scanned roots.

No arbitrary GB quota is supplied without inventory. The lead records a minimum
operating reserve and per-task build/evidence forecasts after measurement. These
are policy limits; a future launcher enforces them before large jobs. This
reference does not claim OS disk quotas or automatic garbage collection.

Retain source, manifests, logs, important failures, reproductions, required
captures and selected binaries/SPIR-V needed for provenance. Avoid retaining
entire build directories for every run. Before any cleanup, the lead checks
that no only-copy evidence, untracked changes, active process or recovery need
is being removed. The protected build path remains excluded even from cleanup.

Migration procedure:
1. Inventory existing locations read-only. Reconcile actual task owners.
2. Allow running tasks to finish/checkpoint in their existing workspaces.
3. Prepare the shared store only when disk reserve supports the temporary
   overlap; record remote, hash algorithm and exact base.
4. Prepare one free slot for a NEW task. Never move a running checkout.
5. Create its unique task branch. If tracked protected build files exist,
   provision with `worktree add --no-checkout` and establish sparse-checkout
   exclusion before populating files; verify no protected files were written.
   Read required canonical blobs from an approved immutable location.
6. Verify worktree/common-dir/branch identity, build and evidence paths,
   Windows/WSL line-ending behavior, and a small real build/test.
7. Test its GitHub draft PR to `astra/gait-capture` and lead review flow.
8. Adopt other slots at subsequent task boundaries, never exceeding five
   managed source slots. Legacy archives are separately tracked until reviewed.

## Service and client interfaces

Run tests without installations:

```bash
python -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v
python tools/agent_fleet/inventory.py --path <existing-checkout> --repo <existing-checkout> --plan-root <proposed-root>
```

The trusted launcher supplies distinct `CHIMERA_FLEET_SUPERVISOR_TOKEN` and
`CHIMERA_FLEET_ENROLLMENT_TOKEN` outside worktrees, then starts:

```bash
python tools/agent_fleet/service.py --root <workspace-root> --db <local-control-dir>/state.sqlite --port <assigned-free-port>
```

The port is required configuration: 8765 already belongs to a documented
gallery example. No controller default may silently claim that endpoint.
The server binds loopback and never contacts the engine. Its SQLite file must
remain local to that service. Windows and WSL clients should connect through
an explicitly configured HTTP adapter rather than concurrently open a mounted
DB. No LAN exposure or TLS/reverse-proxy configuration is performed here.

Use [SQLite transaction semantics](https://www.sqlite.org/lang_transaction.html)
for the single-writer core, and heed its [network-file boundary](https://www.sqlite.org/useovernet.html).
Transport wait limits are distinct from leadership failure detection: a client
request timeout means read/reconcile state, not elect a new lead.

The trusted launcher enrolls an agent, receives its random session token and
stores that token in a private session JSON (endpoint and token). It qualifies
capabilities and capacity from actual evidence. Workers are never given the
supervisor token. The CLI deliberately refuses enrollment to avoid printing or
losing a credential in model logs. Provider launcher integration is NOT supplied.

Every request is `POST /v1/action` with bearer authentication and:
`{"operation":"snapshot","arguments":{}}`. Responses include a monotonic
revision. `events` with `since` returns up to 200 ordered events; continue from
the last received sequence, not the snapshot revision if a page is incomplete.
This is polling-based shared state, not an implemented push/event-stream client.
After an ambiguous transport failure, inspect snapshot/events before retrying a
mutation; operations do not all have idempotency keys in this reference.

| Actor | Operations |
|---|---|
| Trusted enrollment adapter | enroll |
| Trusted supervisor | qualify, elect when vacant, fail with evidence, recover, resource_clear, ack_integration, release_slot |
| Qualified agent | claim, checkpoint, submit_review, resource_acquire/release |
| Lead-qualified ready agent | offer_lead; authenticated yield by any live agent |
| Current lead (catalogue plane) | catalogue_import (validated, idempotent, stale-refusing); any live agent may read via catalogue_read and catalogue_next |

The catalogue plane is discoverable planning data, separate from the live
plane: `catalogue_import` stores validated records built by
`tools/agent_fleet/master_catalogue.py` (all roadmap cards plus the
Master-list task rows, with provenance and content hashes); the snapshot
carries only a summary (digest, counts), and `catalogue_read` returns records
by digest. `catalogue_next` lists planning-only candidates whose dependencies
are integrated and never creates tasks, claims or admissions. A repeated
identical import is refused (`duplicate_catalogue_import`); replacing content
requires the current digest (`stale_catalogue_import` otherwise) and leaves
tasks, claims, resources and slots untouched.
| Current lead with matching epoch | create_task, integration_request |
| Live agent or supervisor | snapshot, events, suspect |

## One prompt scales through a growing falsification registry

The goal is a project that can continue designing, building and testing from
one entry instruction. Workspaces supply isolation; the task/dependency graph
and falsification records supply direction. More worktrees alone supply neither
correct physics nor independent review. This reference admits five active slots;
thousands of workers are a later architecture question, not an unmeasured
configuration change to this single-host service.

Each activated task packet must name its product requirement, assumptions,
STATEMENT, quantitative PREDICTION, FALSIFIER, exact test command, oracle and
its independence, frozen thresholds and units, expected failure signals, source
and artifact identities, required resources and evidence class. Record whether
the gate is proposed, executed, failed, inconclusive, or accepted by scoped
review. A build crash is not successful mutation detection. Passing a test is
not proof that no untested defect exists. Product experience also needs Alan's
actual acceptance where specified; it is not derivable from numerical tests.

A discovered contradiction creates a new gate or reopens the affected claim and
dependent acceptance. Preserve the old prediction, failed evidence, correction
and review. Do not silently change a bound to close a task. The 240 catalogue
cards are a map of proposed work; they are not 240 complete executable gates.
The controller checks claims and coordination but does not parse and certify
the physical contents of a packet. A gate-runner/evidence-verifier integration
is required before autonomous task admission can enforce this richer contract.

Scale by measuring useful throughput, false acceptances, integration conflicts,
recovery losses and resource saturation. Add independent test/review capacity
alongside implementers. Validate the five-slot system with real failures first;
then introduce additional hosts, scheduled compute and a coordination service
appropriate for that topology. Never treat a larger worker count as evidence
that the finished game is physically correct or complete.

## Activation gates before calling the fleet operational

- Reviewed Windows deployment of the service and private credential storage.
- At least two independently qualified lead candidates and genuine readiness
  offers; process/provider observation adapter with reproducible failure events.
- Five-slot filesystem provisioning and disk-reservation enforcement, including
  protected-path exclusion and worktree identity verification.
- A fencing-aware GitHub broker with no bypass credentials, exact-head review
  and serialized merge evidence; test failure during an in-flight publication.
- At least two real agent clients using the same prompt; one session completes
  two scoped tasks without mixing workspaces. Different-provider contexts are
  not assumed shared.
- Real process failure/recovery with preserved dirty/untracked work; demonstrate
  old agent/tool publication cannot continue after revocation.
- Restart and backup/recovery tests for the single local controller itself.
- Scope-specific numerical/runtime/DYAD/human gates remain separate from all
  orchestration checks.

Until those pass, call this the tested control-plane reference, not a deployed
self-building engine. Current work continues under the live controller's
leadership epoch and the PR workflow below, without interruption.

## Documentation reconciliation and continuing DYAD criticism (2026-09-09)

Read the [documentation review](evidence/agent_fleet/DOCUMENTATION_REVIEW.md).
This fleet coordinates execution of the existing ORIENT → NEXT → PROVE(X) →
CHECK → COMMIT loop. It must not introduce a second meaning of proven. The
controller's INTEGRATED means a publisher acknowledged a reviewed Git change,
not that a physics term passed `prove` or a human accepted a product. Existing
verdict/engine stores retain those meanings. An adapter maps term IDs, gate
records, source revision and artifact identity to a task; this adapter is an
activation gate, not implemented by this reference. `next` supplies eligible
domain work; the lead schedules independent branches only after reconciling
domain prerequisites, existing assignments and resources. The 240-card book
is a proposal catalogue and cannot override the engine's unresolved gates.

DYAD drives repeated, observable turns as THE_WORKFLOW §0b already requires.
Tasks declare intermediate review checkpoints before long computation. Fresh
evidence ends each turn; a correction can change the next turn. No invented
fixed timeout ends the eye's inference; follow THE_DYAD_PROTOCOL. Service HTTP
timeouts apply to control requests only, never to DYAD calls.

### Human feedback is criticism with retained authority

All human input enters the same criticism record. Retain the original words
and distinguish interpretation from observation. Categories are INTENT,
APPEARANCE, USABILITY, PHYSICS_CLAIM, DEFECT, PERFORMANCE, ACCESSIBILITY,
QUESTION, STOP, PERMISSION, SCOPE, or UNCLASSIFIED; multiple categories are
allowed. Emotional language is a useful signal, not a reason to discount an
observation or infer an unstated diagnosis, preference or approval.

STOP, PERMISSION and SCOPE remain instructions with their original authority.
Do not queue a stop behind an aesthetic review, convert revoked permission
into a suggestion, or manufacture consent from positive sentiment. The
trusted human adapter must route those actions immediately to the authorized
executor and record acknowledgement. This reference records that obligation
with `authority_action_required`; it does not stop processes or grant rights.

The `feedback_add` operation records original text, source, category labels,
linked tasks and evidence reference. Only the trusted supervisor/human adapter
may assert HUMAN origin; model vision is DYAD, never HUMAN. A relayed claim
without trusted attribution stays AGENT with an explicit reference. Category
labels are supplied by the adapter; no semantic classifier is implemented.
Original records have no update/delete operation. Current-epoch lead
`feedback_disposition` appends ACKNOWLEDGED, INVESTIGATE, TASK_PROPOSED,
ADDRESSED, DEFERRED or DISAGREEMENT_RECORDED with rationale and evidence.
None marks a task integrated, a physical law true, or human acceptance granted.

Measurement questions become preregistered tests; preferences guide a visible
comparison against the stated intent. Disagreement between eye and measurement
requires examining state association, observability, instrument and diagnosis.
Do not automatically rewrite physics from prose. Do not claim an AI inference
is Alan's decision. A new test can reopen a claim and affected dependencies;
retain original evidence and append the correction. Open source publication
of code does not require publishing private session tokens or raw personal
feedback: publish only the appropriate reviewed, attributed project evidence.

### Visible runtime is required

Every engine running for agent runtime work is non-headless, visible and not
minimized, identified by slot, task, revision and process manifest. Include
actual `/glass` and `/frame` evidence where the protocol requires it, with
state/tick linkage and fresh binary/shader identity. Provide beginning and end
and enough intermediate frames to assess the claimed change. Submit ONE image
per eye call, record the served model, use UTF-8 and supply physical context
and prior corrections without priming expected defect strings. A static
image cannot certify motion. Use the current senses API; old movie/Ollama
instructions are historical where the newer one-image LM Studio protocol
and actual implementation contradict them.

No visible runtime access means the required window gate remains NOT_TESTED,
not waived by a headless numerical pass. Offline reference/unit/compile tests
remain useful separately. Keep the active runtime inspectable by the human;
resource scheduling may pause a job but must not secretly run its engine
headless. Five slots own five builds; concurrent GPU runtime requires measured
capacity and an explicit scheduler policy. Initially serialize hardware runs
and preserve the resident eye. The fleet launcher/viewer integrations remain
NOT_IMPLEMENTED; these requirements are not claims of current deployment.

## Five-slot readiness (2026-09-10, FIVE-SLOT-READINESS-01)

Live control plane: deployment E:\ChimeraWork\control (service.py pidfile-alive; supervisor + agent sessions under control\sessions). Slots 01-05 of the fleet registry are provisioned; worker slots 02-05 host scripted readiness stage agents (`stage03/04/05`, labeled FIVE-SLOT-READINESS-01) that are NOT independent human/prompt-spawned agents. Slot-01 is the integration slot (certification record). Slot-02 published the coordination driver at `bb61993e` (fetch-verified FF through publish.py; base advanced).

Scheduling: resources serialize through the controller — `resource_request` grants under FIFO + priority-aging + benchmark exclusivity + memory budget; `allocation_refused` entries auto-grant on a later promotion when memory frees (do not re-request). GPU runs are guarded by reservations over the WHOLE machine for `gpu_benchmark`; `gpu_functionality` grants are per-slot and chained to `dyad_eye`. An interrupted owner enters RECOVERY_HOLD with resources intentionally retained until trusted drain evidence clears them; recovery bumps the generation and the fresh generation is claimed again.

Remaining before the three-agent universal-prompt start: (1) operator loads a vision-capable model in LM Studio and the three slot DYAD reviews (one image per call) are run or deferred explicitly; (2) the certification record integrates (task `five-slot-integration-record`); (3) Alan asserts the go.

## Resource lifecycle repair (2026-09-10, Linux-reviewed proposal)

The resource lifecycle patch prevents replacement of an existing non-memory
reservation, including a same-task class change. Release engine_demo and dyad_eye
before releasing their GPU parent; supervisor clear follows the same dependency
checks. A retained child from an older registry blocks a foreign GPU grant.
Legacy engine acquisition also requires the task's GPU reservation.

A task retaining resources may acquire an immediately available extension, but
an infeasible request becomes terminal (`served:true`, `granted:false`,
`dropped_reason:release_required`). Its resources remain held. The owner must drain
and release them, then request its complete bundle. Do not keep polling that
terminal request as if it will auto-promote. A nonholder's pending request retains
normal promotion behavior. Existing blocked-holder requests are reconciled on the
next promotion; no process is stopped or reservation forcibly released.

`memory.admitted_mb` is recomputed from held allocations on release/clear and
snapshot reads. It remains declared accounting, not measured physical GPU memory.
Missing or non-string resource names now receive `invalid_resource_name`.

Correction to older strict-FIFO/priority-aging claims: the existing promotion
loop scans arrival order but permits an eligible group to bypass an older
ineligible group. Priority and waiting-revision values are metadata, not an
implemented starvation bound. This patch does not change that policy; a bounded
fairness decision and implementation remain open.

Evidence and executed regression counts are recorded in
[evidence/agent_fleet/RESOURCE_FIX_20260910/REPORT.md](evidence/agent_fleet/RESOURCE_FIX_20260910/REPORT.md).
Live Windows migration and consumer handling of terminal release_required results
must be reviewed by the current local lead. No live service was modified by this
Linux review. The universal prompt does not change.

## Slot-provision binding, supervisor rebind, and detached review capacity (2026-09-11, fleet-docs-operating-model-01)

Deployed operating model, verified against controller source `d012b4b1`
(deployment `E:\ChimeraWork\control\deployments\slot-binding-d012b4b1`, service
live since 2026-09-11). Every operation named here was read from that deployed
source; the verification table is
[evidence/agent_fleet/OPERATING_MODEL/VERIFICATION.md](evidence/agent_fleet/OPERATING_MODEL/VERIFICATION.md).
Copy-paste joining prompts per role are in
[evidence/agent_fleet/OPERATING_MODEL/PROMPTS.md](evidence/agent_fleet/OPERATING_MODEL/PROMPTS.md).
The historical sections above remain unchanged and govern where they speak.

### Task/generation-bound provisioning

Supervisor `provision_slot` no longer records a bare head. The active provision
is bound to its task and generation: `provision_task`, `provision_generation`,
`provision_base`, plus `worktree_head` and `provision_evidence`. Stale authority
is therefore distinguishable from current authority by inspection of the slot's
engine record.

### Claim refusal `stale_provision_requires_recovery`

A `claim` that finds a free slot of the right kind still carrying an ACTIVE
provision from an earlier task/generation is refused with
`stale_provision_requires_recovery` (distinguished from `no_free_slot`). The
refusal names the actionable cause: the slot is recovered by supervisor
`slot_rebind`, never silently adopted by the next claimant. The worker-side
claim loop treats this refusal as recoverable contention — it skips the task and
retries later; the refusal appears in the loop's refusals list and never crashes
the worker.

### Supervisor `slot_rebind` with preservation + drain attestations

`slot_rebind` is the supervisor-only recovery for a slot whose active provision
belongs to an earlier task/generation. The caller attests work preservation
(`preservation_evidence`) AND process/resource drain (`drain_evidence`). The
physical workspace is never touched (`filesystem_touched: False`). Named
refusals: `no_stale_provision` (nothing stale to clear), `slot_task_not_running`
(the slot's bound task is not RUNNING), `resources_still_held` (the old
provision's task still holds resources). On success the stale record moves to
the slot's preserved history with reason `supervisor_slot_rebind`.

### Evidence-preserving recover/release: `preserved_provisions` (cap 20)

Retiring a provision never deletes its evidence. The full record moves to
`engine['preserved_provisions']`, bounded at 20 entries with the oldest dropped
first, and the active binding fields clear so no later task/generation can
inherit source authority. Preserve reasons: `recovered_task_generation`
(supervisor `recover`, which refuses `resources_still_held` until trusted drain
evidence), `released_after_integration` (supervisor `release_slot`, which
refuses `resource_still_held` and never deletes the workspace),
`supervisor_slot_rebind`, and `released_for_review_handoff`.

### Review-slot handoff flow: detached REVIEW capacity

After a worker stops writing, drains, pushes its task branch, opens its PR and
`submit_review`s the exact head from its own session, the trusted lead/broker
independently verifies the remote branch, PR identity and head, then calls
`release_review_slot`. The receipt appended to the task's
`review_slot_handoffs` carries the frozen binding (owner, generation, slot,
head, branch, review, checkpoint), the PR identity and pushed/PR heads, the five
attestations (remote verification, preservation, writer stopped, runtime
drained, slot reprovision-ready), the retained **provision identity**
(`provision_task`, `provision_generation`, `provision_base`, `worktree_head`,
`provision_evidence`) and the released revision. The slot frees immediately
while the task stays REVIEW: the detached review protects its write scope but
consumes neither a slot nor the submitter's execution capacity, and
`ack_integration` on a handed-off task returns `slot: null` /
`RELEASED_AT_REVIEW_HANDOFF`. Corrections go through lead `review_requeue`
(READY with `correction_base_head`; provisioning must match that exact head), a
failed reviewer-side recovery through supervisor `recover`, and a redundant
`release_slot` on an already handed-off task is a no-op attestation. The full
contract is [THE_REVIEW_SLOT_HANDOFF.md](THE_REVIEW_SLOT_HANDOFF.md).

## Client instance identity: task-centric fence with staged migration (2026-09-11, fleet-client-instance-01)

Distinct durable client identities are now part of the protocol
(`tools/agent_fleet/`, reviewed with the lane). The trusted launcher mints a
per-enrollment instance (`instance_id` + `instance_secret`) into the private
session file; the controller stores ONLY the secret's sha256 fingerprint; the
client sends `X-Chimera-Instance: <id>:<secret>` on every call (malformed →
named refusal `invalid_instance_header`). Identity is a secret, never a PID.

The fence is TASK-CENTRIC: `claim` binds the claiming instance
(`owner_instance`); every owner-mutation op (checkpoint, submit_review,
resource_*) on a bound task requires that instance — a second client sharing
the bearer is refused by name (`instance_not_bound`;
`instance_secret_mismatch` for a forged secret). Lead/supervisor integration
paths (review_requeue, integration_request, ack, release*) are exempt by
design: the integrator is not the task owner.

Migration is staged and auditable: registry flag `instance_fencing`
(supervisor `instance_fencing_set`) starts in `compat` — legacy sessions
remain admitted, and their task events carry the explicit marker
`legacy-unfenced` (the audit can always distinguish fenced from unfenced
writes; the proven two-writer baseline is retained as a test). `enforced`
refuses instance-less CLAIMS (existing unfenced claims drain naturally);
flip only through a reviewed deployment transition after per-client
migration. Bound state persists across restart (same store). Cooperative
boundary unchanged: bearer+instance fencing is capability fencing, not a
sandbox — same-OS-account shell access remains outside the model. Tests:
`tools/agent_fleet/test_client_instance.py` (7: baseline before-picture,
fence matrix, secret-absence scan across state/snapshot/events, reopen
persistence, enforced-mode gating, transport refusal, supervisor-marker
absence).

## Abandon: retiring stale READY records and unprovisionable claims (2026-09-11, fleet-task-abandon-01)

Two supervisor-only, audited ops close the controller gaps recorded in the
third-wave Master amendment. Neither ever touches the filesystem, and
neither ever revokes an agent session. Preregistration and measured
results: [TASK_ABANDON](evidence/agent_fleet/TASK_ABANDON/PREREGISTRATION.md).

`task_abandon(task, reason, evidence)` retires a stale READY task: the task
becomes **ABANDONED** — a new TERMINAL state — with `{reason, evidence,
actor, revision}` recorded on the task and an audit event carrying the
reason. Refusals: `supervisor_only`, `unknown_task`, `task_not_ready` for
every non-READY state (RUNNING, BLOCKED, REVIEW, RECOVERY_HOLD, INTEGRATED,
already ABANDONED), and blank attestations. The id is retired permanently
(`create_task` refuses it as a duplicate): redoing the work means a NEW task
id, so the retired record's audit history is preserved, never rewritten.

ABANDONED coherence rule (one rule, applied everywhere): ABANDONED joins NO
active-state tuple (`RUNNING/BLOCKED/REVIEW/RECOVERY_HOLD`), so claim
eligibility, capacity accounting, the write-scope-conflict predicate, the
`_fail`/`yield` recovery sweep and stale-claim queue drops all treat it as
INACTIVE with no further edits, and the dependency gate
(`dependencies_not_integrated`) treats it as NOT satisfying a dependency
(`INTEGRATED`-only, unchanged). The one complement-enumeration was fixed
explicitly: `catalogue_next` no longer counts ABANDONED as `live`, so the
card of an abandoned realization becomes a PROPOSED candidate again (while
cards DEPENDING on it stay blocked — `done` remains INTEGRATED-only). The
run-queue surfaces (`run_queue.py` reference model, `run_queue_worker.py`
adapter) read READY/active tuples only, so they ignore ABANDONED records
with no change — audited, pinned by tests.

`claim_abandon(task, preservation_evidence, drain_evidence)` retires an
unprovisionable RUNNING claim WITHOUT ending the owner's session — the gap
the yield→recover path filled at the cost of the session (that path remains
available and unchanged, still the right tool when the session itself must
end). The supervisor attests work preservation AND process/resource drain
(`recover`'s exact guard: `resources_still_held` until drained); the slot
frees through the same `_preserve_provision` machinery as
recover/slot_rebind/release_slot; queued resource requests for the task die
(`dropped_reason='claim_abandoned'`); the task returns to READY at
generation+1 with owner, slot and instance bindings cleared and the
attestations stored as its checkpoint, so any qualified agent — including
the same one, which stays `alive` with its remaining capacity — can re-claim
at the new generation. A slot carrying an ACTIVE provision is refused by
name (`provision_active_use_slot_rebind`): that situation belongs to
`slot_rebind`, whose contract this op does not weaken or duplicate.
Refusals: `supervisor_only`, `unknown_task`, `task_not_running`,
`task_has_no_slot`, `slot_binding_mismatch`,
`provision_active_use_slot_rebind`, `resources_still_held`, and blank
attestations — every refusal leaves revision and audit untouched.

Tests: `tools/agent_fleet/test_task_abandon.py` (19: both positive paths
with reopen invariants, every named refusal with revision-preservation,
ABANDONED coherence across claim/dependency/scope/capacity/catalogue,
permanent-id retirement, never-touches-filesystem proof, append-only
token-free audit, and the yield→recover path still intact). Deployment note:
`control.py` is also the deployed service source — this change reaches the
live controller only through the next controlled transition; nothing here
mutates the live service. The documented stale records
(fleet-run-queue-01, fleet-orient-continuation-01, engine-vulkan-cleanup-01,
window-capture-ownership-01, fleet-controller-upgrade-01) are to be retired
by the SUPERVISOR with these ops AFTER review, per the Master amendment.
