# SLOT_BINDING — Preregistration (before any code change)

Task: `fleet-slot-binding-01` (gen 1, slot 2, owner glm53-fresh-01, epoch 3)
Base: `8d72c4f36f5565aa33edf04da86d9f2d86347dc0` reconciled with integration tip
`87e281e5c208afaa484b06a871453ebe5da631fd` (merge, no force).
Recorded: 2026-09-11, before implementation.

## Observed defects (live controller state.sqlite, revision 472)

1. `recover` (base `Control`) clears `slots[n]['task']` but leaves
   `engine.provisioned/worktree_head/provision_evidence` active. A recovered slot
   therefore carries provisioning authority from an earlier task/generation.
   Live evidence: slots 4 and 5 are task-free yet `provisioned: true` with
   worktree heads of integrated tasks (`7d3601e7` master-catalogue-sync-01,
   `d7c47446` slot05-runtime-probe). Slot 3 (gov01 gen 4) carries a gen-1
   provision whose recorded head no longer describes the physical checkout
   (foreign branch + uncommitted work; see gov01 checkpoint and
   `E:/ChimeraWork/evidence/glm53-fresh-01/gov01-slot03-mismatch-20260910T0130Z/`).
2. `provision_slot` records no task/generation identity with the provision, so a
   stale provision cannot be distinguished from a current one by the registry.
3. `claim` selects any slot with `task is None`; a free-but-provisioned slot
   (legacy/migrated state) is silently adopted. The executor
   (`run_queue_worker.CommandExecutor`) fail-closes later on branch mismatch by
   raising, which crashes the worker loop instead of producing an actionable
   recovery event at assignment time.
4. `release_slot` pops provision metadata without retaining it (evidence loss).

## Derived invariants

I1. A slot's ACTIVE provision (`engine.provisioned == true`) is always bound to
    the slot's current task and that task's current generation.
I2. No claim may bind a slot whose active provision belongs to any other
    task/generation (including provision-orphaned free slots).
I3. Provision evidence is never deleted: clearing an active provision moves the
    full record (task, generation, head, evidence) into
    `engine.preserved_provisions` (bounded history) with the clearing reason and
    attestation.
I4. Only SUPERVISOR may clear/rebind a stale provision, and only with explicit
    preservation AND drain attestations, and never while the old task still
    holds runtime resources.
I5. `recover` and `release_slot` preserve I1/I3 as a side effect of their normal
    transition (no separate caller discipline required).

## State transitions (added/changed in `tools/agent_fleet/control.py`)

- `provision_slot` (SUPERVISOR, unchanged authority): additionally records
  `provision_task`, `provision_generation` (= task's current generation) and
  `provision_base` (= task's recorded base) beside the existing fields. Existing
  refusal `slot_already_provisioned` unchanged (now also covers stale-gen case
  until rebind).
- `slot_rebind` (NEW, SUPERVISOR only): clears an ACTIVE stale provision from a
  slot after attestations. Refuses: worker/lead callers (`supervisor_only`);
  nothing stale (`no_stale_provision`); old provision task still holds resources
  (`resources_still_held`); slot bound to a task not RUNNING
  (`slot_task_not_running`); missing/blank preservation or drain evidence.
  Allowed for a slot whose current task is RUNNING (rebind for fresh
  provisioning) or whose task is None (legacy orphan cleanup). The stale record
  moves to `engine.preserved_provisions`.
- `recover`: before freeing the slot, if `engine.provisioned` the record moves to
  `engine.preserved_provisions` with the recovery evidence, then active fields
  are cleared (fixes defect 1 at its source).
- `release_slot`: same preservation move (fixes defect 4).
- `claim`: slot selection additionally requires `not engine.get('provisioned')`;
  refusal `stale_provision_requires_recovery` names the recovery op (fixes
  defect 3).
- `preserved_provisions` is capped (last 20 records) to bound registry growth;
  the cap drops oldest records only (documented).

## Statement / Prediction / Falsifier (task packet, restated exactly)

STATEMENT: A current claim cannot inherit usable source authority from an
earlier task/generation, and authorized recovery can safely rebind a preserved
slot.

PREDICTION: Isolated tests refuse stale-generation provisioning, wrong-owner or
worker-driven rebind, resource-held rebind, and claim-time adoption of a
stale-provisioned slot; permit current-claim supervised repair without losing
old evidence or changing unrelated claims; `recover`/`release_slot` leave no
active stale provision and retain the full record in `preserved_provisions`.

FALSIFIER (any one rejects): inherited provision accepted as current; a worker
clears another binding; held-runtime rebind; silent evidence deletion; a claim
silently adopting a foreign active provision; unrelated task/claim/slot state
changed by any new transition; an existing suite expectation weakened.

## Test plan (tools/agent_fleet/test_slot_binding.py, isolated temp registries)

T1 stale-gen provisioning refused; T2 slot_rebind happy path then re-provision
records new generation; T3 worker/lead rebind refused (`supervisor_only`);
T4 rebind refused with resources held; T5 rebind refused without stale provision;
T6 recover clears active provision AND preserves record; T7 release_slot
preserves record; T8 claim refuses stale-provisioned free slot with actionable
reason; T9 unrelated claims/slots untouched by rebind; T10 ReviewHandoffControl
subclass: same guard expectations (documents the subclass override gap if any);
T11 full existing fleet suite still green (no weakened expectations).

## Out of scope (recorded follow-ups, not silenced)

- `review_handoff.py::_claim_with_detached_review_capacity` duplicates base
  claim slot selection; it must adopt the same guard (file outside this task's
  declared scopes; one-line adoption recorded for lead review).
- `run_queue_worker.py::_claim_contention` should classify
  `stale_provision_requires_recovery` as contention so a worker skips rather
  than crashes (same scope constraint).
- `review_handoff.py::_release_review_slot` resets the engine dict wholesale;
  this drops `preserved_provisions` history (receipts on the task remain the
  authoritative evidence).
