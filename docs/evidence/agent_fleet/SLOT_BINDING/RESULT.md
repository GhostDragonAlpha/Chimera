# SLOT_BINDING — Result record

Task: `fleet-slot-binding-01` gen 1, slot 2, owner `glm53-fresh-01` (lead+worker, epoch 3).
Compared against preregistration in `PREREGISTRATION.md`. Recorded after execution.

## Implemented (tools/agent_fleet/control.py)

1. `_preserve_provision` helper: retiring an ACTIVE slot provision moves the full
   record (`provision_task`, `provision_generation`, `worktree_head`,
   `provision_base`, `provision_evidence`, reason, evidence, cleared revision)
   into `engine['preserved_provisions']` (bounded at 20, oldest dropped) and
   clears the active fields. No path deletes provision evidence silently.
2. `provision_slot` now binds the provision to the claiming task's id, current
   generation and recorded base; reply carries the binding.
3. New `slot_rebind` (SUPERVISOR only): clears an ACTIVE stale provision after
   explicit preservation AND process/resource-drain attestations; refuses
   worker/lead callers, missing attestations, `no_stale_provision`,
   `resources_still_held` for the old provision task, and slots bound to a
   non-RUNNING task. Never touches the filesystem.
4. `recover` retires the slot's provision into history before freeing the slot
   (fixes the observed stale-binding leak at its source).
5. `release_slot` retires the provision into history instead of popping it.
6. `claim` refuses to adopt a free slot carrying an ACTIVE provision with the
   actionable refusal `stale_provision_requires_recovery` (distinguished from
   `no_free_slot`).
7. Audit events may carry `slot` (used by `slot_rebind`).

## Commands and outcomes (isolated temporary registries)

- `python -m unittest test_slot_binding` (tools/agent_fleet): **11/11 OK**
  (T1 stale-gen refused + rebind repair; T2 authority/attestations; T3 held
  resource blocks rebind; T4 non-RUNNING slot task; T5 recover clears+preserves
  and fresh generation provisions without inheritance; T6 release preserves
  record; T7 claim refuses stale-provisioned free slot then rebind unblocks;
  T8 unrelated state untouched; T9 history bounded at 20; T10
  ReviewHandoffControl inherits binding/rebind/recover-preservation; T11 rebind
  event carries slot id).
- `python -m unittest discover -s tools/agent_fleet -p 'test_*.py'` from repo
  root (this worktree, changes applied): **158 tests, 2 failures, 1 skip**.
- Identical command at pristine `87e281e5` (throwaway worktree): **147 tests,
  same 2 failures, 1 skip** → no weakened expectations; delta is exactly the 11
  new tests, all passing.

## Pre-existing failures (NOT caused by this change; documented, not silenced)

- `test_master_catalogue.py::test_import_real_sources_full_coverage`
  (76 != 65 master row ids) and `::test_gen5_exhaustive_partition_no_silent_omissions`
  (2540 != 2430) fail identically at pristine `87e281e5`: the pinned counts
  predate document growth merged by later lanes (elastic/dyad/PR41 docs). The
  catalogue lane owns updating those pins; repairing them is outside this
  task's scopes.

## Prediction check (from the packet)

- Inherited provision accepted as current: refused (`slot_already_provisioned`
  for stale gen; claim-time `stale_provision_requires_recovery`).
- Worker clears another binding: refused (`supervisor_only`).
- Held-runtime rebind: refused (`resources_still_held`) until verified drain.
- Silent evidence deletion: falsified — every clearing path preserves the full
  record; bounded history drops only the oldest beyond 20 (documented).
- Current-claim supervised repair: `slot_rebind` + fresh `provision_slot`
  records the new generation; unrelated claims/slots byte-identical (T8).

## Out-of-scope follow-ups recorded for lead review

1. `review_handoff.py::_claim_with_detached_review_capacity` re-implements base
   claim slot selection and does not include the stale-provision guard
   (one-line adoption; file outside this task's scopes). Until adopted, the
   deployed ReviewHandoffControl layer enforces the guard only through base
   `Control.claim` paths; migration must rebind stale slots before workers
   claim through the layered service.
2. `run_queue_worker.py::_claim_contention` should classify
   `stale_provision_requires_recovery` as recoverable contention (skip/retry
   instead of crash) — same scope constraint.
3. `review_handoff.py::_release_review_slot` resets the engine dict wholesale,
   dropping `preserved_provisions` history; task-side handoff receipts remain
   the authoritative evidence.
