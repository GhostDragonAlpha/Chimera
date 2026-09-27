# Material-first delivery — astra-0031

The active 95-item catalog replaces the original scope. Read [MATERIAL_PLAN_ADOPTION.md](MATERIAL_PLAN_ADOPTION.md). Recover the existing prototype; reconcile pressure, passive material, removable tissue interfaces and resident GPU interactions; reuse the same laws across shapes and the monkey limb. The first product checkpoint is controlled walking through woods, followed by climbing. No invisible skeletal hinge or cosmetic-only skin can substitute for the declared material assembly.

# Playable delivery — operator approved 2026-09-27

The next result is one physically controlled monkey on flat ground in one runnable
build: input -> existing 20 Hz speed/heading command port -> accepted controller ->
physics body -> observable movement -> follow camera. Stop/start, heading, speed,
focus loss and restart must be demonstrated in that same build. No mocked carry,
kinematic translation or alternate body can substitute for this result.

## Order and ownership

1. Close the existing walking lineage/parity/mass/policy blockers; integrate the
   existing controls and camera. W01–W10, U01–U03 and their prerequisite closure
   receive first priority. The catalog's qualification and training gates remain.
2. Extend that build to uneven terrain and the finite clearing: F01–F08, with
   certified runtime/training agreement and explicitly evidenced friction.
3. Add one trunk, grasp, climb, hold, descend and release using the existing
   anatomy/mechanics/climbing cards. Finish the end-to-end player acceptance.

Scheduling ranks eligible prerequisite closure; it never unlocks a dependency,
changes a frozen criterion, preempts an existing owner or invents physical values.
The 95-task catalog uses versioned MAT2- qualifications. Useful unrelated
work may proceed when the critical path is resource- or decision-blocked.

`PLAYABLE_BUILD.json` is the single build record. `astra/gait-capture` is the
integration destination; `master` is the separately reviewed release destination.
Pin the actual source commit, reproducible build recipe, executable hash, body,
scene and policy identities, then evidence for each real player action. Null means
unestablished. Do not point to an arbitrary current HEAD as a verified build.
Update this record through a reviewed integration PR, not from a worker summary.
Public workflow changes must reach master; game-lineage changes are not wholesale
merged into master merely to publish documentation.

Every candidate must state one of:
- Integrates into the named build, with source-bound tests and runtime evidence.
- Component complete, with the exact existing downstream integration task IDs,
  required ports and unresolved blockers. This is not a playable feature.
- Diagnostic only, with its finding and the implementation task it unblocks.

## Executable membranes and ports

Use the existing ontology, mapping contracts and test infrastructure. For each
boundary identify owned state, invariants, exchanged quantities, units, coordinate
frames, update rate/tick semantics, version and named failure behavior. Reuse the
existing port law and fixtures; add an adapter only for a demonstrated mismatch.
Verify producer/consumer agreement and failure behavior with executable examples.
One-off prose explaining a compatible connection is not a new implementation task.
Do not create a new ontology language, scheduler, registry or evidence framework.

## Capacity and review

Ten is available development capacity, not a utilization requirement. No filler,
duplicate implementation or repeated review just to occupy workers. Resume owned
work first. Ordinary review target is ONE independent reviewer per exact PR head
and criteria; uncovered candidates precede extra coverage. A completed PASS waits
for acceptance/integration instead of automatically commissioning another reviewer.
An explicitly justified additional numerical/security/visual review may be requested:

`python -B tools/monkey_campaign/kanban_cli.py request-review --arguments request.json`

Arguments: existing lead actor/role authority, task_id, pr_url, exact head_sha and
reason. No credentials belong in public receipts. At most two additional reviews
per exact head. A new head resets the allowance. Reviewer authorship exclusion and
all acceptance gates remain. This is cooperative authorization on the shared account.

On the next canonical startup, obsolete or excessive review owners retire their own
record and move on; their workspace/evidence stays. Nobody expires another worker
by time or registry label. Existing running reviews may finish; submit results before
asking for new work. Blocked capacity is reported, not relabeled as active work.

## Evidence and measurement

Use existing test runners, camera validator and source-bound runtime receipts.
Capture test output once; reference that artifact rather than repeatedly rewriting
the same report. Automate the byte inventory with:

`python -B tools/monkey_campaign/evidence_pack.py --root OWNED_OUTPUT --task TASK_ID --source-commit FULL_SHA --file report.md --file tests.log`

This emits JSON to stdout. Its `artifacts` entries can supply publication handoff
paths/hashes; it does not invent PASS, independently review work or submit it.
Existing camera metadata must include angle/orientation, distance, target, projection,
viewport, clipping/framing, subject identities, diagnostic tags and clean views as
required by the task's current profile. Reuse captured evidence unless sources,
criteria, material behavior or an unresolved finding require a rerun.

`python -B tools/monkey_campaign/delivery.py` reports implementation state, component
merge, recorded qualification and the separate unresolved integration status. It
reports first-review success and excess review records without treating labels as
liveness. Agent-hours, implementation-to-integration latency and demonstrated action
counts remain null until source-bound timing/build evidence exists. Wall time of a
single test is not agent-hours; provider token usage is not useful feature throughput.
Future integration receipts should retain task ID, source/build identities, first
implementation time, integration time, measured agent usage if available, actual
player actions and runtime/visual evidence. Do not fabricate historical timing.

Human visual decisions follow [OPERATOR_VISUAL_DECISIONS.md](OPERATOR_VISUAL_DECISIONS.md).
A local decision panel, screenshot path or mailbox notice is not presentation.
The Lieutenant must inspect and display the actual evidence in the Captain's active
conversation, explain labeled choices and consequences, and bind the explicit reply
to the exact shown bytes. Workers and the Sergeant must never choose for the Captain.
While waiting, mark the card decision-blocked, release its development capacity and
continue other eligible work. A missing human answer is not a worker failure.

Judge success by accepted behavior in the playable build, first-review acceptance,
correction cycles, duplicate coverage and integration latency. Checklist completion
is explicitly unweighted and is not a forecast of effort or elapsed time.

## Stop expanding administration

Freeze speculative workflow expansion. Fix demonstrated ownership, correctness,
recovery and dispatch defects; otherwise spend work on the executable slice.
Each cycle must demonstrate new behavior in the same build or remove a measured
blocker with a named downstream task. Preserve scientific uncertainty; escalate
genuine missing physical authority through the mailbox with exact source evidence.
