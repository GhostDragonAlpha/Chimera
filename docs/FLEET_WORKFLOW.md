# Chimera fleet workflow

This is the maintained overview of the playable-monkey campaign workflow.
[MONKEY_RUN.md](MONKEY_RUN.md) remains the campaign execution entry point.
The published implementation includes the locally deployed astra-0029 recovery
and separate-review-queue mechanisms. No live registry, credential, model process,
or worker checkpoint is distributed with this documentation.

## People and agents

The human Captain sets the goal and can override project decisions. The
[Lieutenant](../tools/monkey_campaign/LIEUTENANT_ONBOARDING.md) is the lead developer:
maintains architecture, ontology and acceptance criteria; reviews integration;
answers the mailbox; and advises the Captain candidly about quality, delivery,
resource needs, player value and financial viability. The Lieutenant should push
back with evidence and alternatives, while respecting the Captain's final decision.

[Execution Sergeants](../tools/monkey_campaign/EXECUTION_SERGEANT.md) direct workers
or implement assigned work themselves. They use the maximum available capacity,
up to ten subagents, when independent authorized work and machine resources permit.
Agent count and token consumption are not measures of product value.

The legacy `astra-codex` label names the Lieutenant in the existing code. It is not
a secret credential. Operational coordinator tokens serialize cooperation; they
are not GitHub credentials. This single-account implementation does not enforce
isolation against software able to modify the shared files and registry.

## Ontology determines the work

[Membranes](MEMBRANE_ONTOLOGY.md) organize containment, physical boundaries,
validation and connections through ports. The [work plan](ONTOLOGY_WORK_PLAN.md)
maps tasks to membranes, ports and verification profiles. The sealed completion
map is the approved backlog; verified dependencies determine which work is ready.
See [ontology queue](../tools/monkey_campaign/ONTOLOGY_QUEUE.md).
A merged diagnostic supplies evidence; it does not automatically qualify its parent.

## Ten Development slots and a separate Review queue

1. Startup verifies current instructions, saves arrival recovery information and
   obtains eligible work with task, attempt and criteria identities.
2. The worker uses the returned isolated checkout and assigned branch-N. Never
   switch the shared project checkout or write into another attempt's directory.
3. Work progresses through statement/prediction/falsifier, implementation and the
   card's numerical, runtime and visual verification. Preserve failures and history.
4. A hash-bound handoff moves the candidate to Review and frees its Development
   slot. The worker immediately takes other eligible implementation or review work.
5. The coordinator publishes on the card's `review/<task-id>` branch after checking
   the entire base-to-head diff. Only scoped files and required evidence belong there.
6. A non-author reviewer examines the exact head and criteria. Findings return to
   the task inbox and correction work. PASS is a recommendation, not a merge.
7. Authorized acceptance plus a GitHub merge at the exact approved head and the
   independent `accept-merge` fetch records DONE and unlocks dependent work.

The ten slots limit Development tasks, not the number of pending reviews or the
number of processes allowed to compete for the GPU. Missing dependencies can
legitimately reduce concurrency. Do not manufacture duplicate work to fill slots.
See [Review lane](../tools/monkey_campaign/REVIEW_LANE.md),
[continuous cycle](../tools/monkey_campaign/CONTINUOUS_CYCLE.md), and
[operational coordination](../tools/monkey_campaign/OPERATIONAL_LEAD.md).

## Startup, recovery and mailbox

On the operator's host, run:

```powershell
python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py
```

On recovery add `--arrival-id` with the identity from your own receipt, never an
attempt ID. The receipt is saved before checkout/output. SQLite is assignment
authority; saving a file atomically is not a database/filesystem atomic transaction.
See [startup recovery](../tools/monkey_campaign/STARTUP_RECOVERY.md).
Use the returned templates for `--request-pr`, `--submit-pr`, `--review-result`,
checkpointing and coordination release. Do not fabricate a handoff template or token.
The entry point is host-specific; a fresh clone requires deliberate installation,
registry initialization and path configuration. It is not an unattended installer.

The [mailbox](../tools/monkey_campaign/SUGGESTION_BOX.md) carries architectural
questions and answers; task inboxes carry actionable review findings. Workers read
updates at startup and assignment boundaries. The Lieutenant checks when the Captain
starts/resumes a lead session, unless a bounded monitor was explicitly requested.
Recover or release a stopped coordinator with exact-holder checks and preserved
history; a timestamp or WORKING label alone does not prove process liveness or death.

## Evidence and publication

Keep task ID, attempt ID, arrival ID, criteria hash, source revision and artifact
hashes distinct. Check the submitted bytes; preserve prior regressions and original
receipts. A hash mismatch proves drift, not which person or agent caused it.
Instruction hashes detect changes relative to a trusted pin; they do not grant rank.

For visual gates capture the actual required runtime and identify the ontology
elements, labels and normally hidden debug geometry. Record camera position,
orientation, distance, framing and other card-required settings so another reviewer
can reproduce the view. Static receipts are not native gameplay qualification.
See [visual capture contract](../tools/monkey_campaign/visual_capture.py).

A publication request is not a PR. An open PR is not accepted work. A conflict-free
PR is not evidence of correctness. The [connected merge service](../tools/monkey_campaign/MERGE_SERVICE.md)
checks accepted heads during active lead sessions, merges with a head precondition,
and reconciles actual GitHub proof. Missing worker GitHub credentials do not justify
copying another harness's secrets or inventing completion. No automatic merge daemon
is implied. Checkpoint genuine external blockers and continue other eligible work.

## Implementation map

- `agent_slots.py`: transactional coordination state and read-only snapshots.
- `worker_start.py`, `worker_checkout.py`: identity recovery, routing and isolated checkout.
- `kanban.py`, `continuous_cycle.py`, `review_lane.py`: task transitions and corrections.
- `ontology_queue.py`, `visual_gate.py`: dependency and evidence gates.
- `operational_lead.py`, `verified_submission.py`, `merge_service.py`: publication,
  independent acceptance and connected merge handoff.
- `suggestion_box.py`: questions and append-only lead answers.

These files live in [tools/monkey_campaign](../tools/monkey_campaign/).
Submitted candidate files are rehashed at boundaries; attempt directories are not
OS-enforced sandboxes or immutable stores. Shared-account authority and retained
machine-specific evidence paths remain explicit limitations.
