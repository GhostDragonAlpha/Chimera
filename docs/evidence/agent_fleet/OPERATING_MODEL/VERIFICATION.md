# VERIFICATION — fleet-docs-operating-model-01 (generation 1)

Source under test: `E:\ChimeraWork\control\deployments\slot-binding-d012b4b1`
(git `d012b4b1`, service live since 2026-09-11). Every operation documented in the
doc updates was read from the deployed source before being written down.
`control.py` cites below are `control.py:<line>` in that deployment; `review_handoff.py`
cites are `review_handoff.py:<line>`.

## Verification table

| # | Documented operation / fact | Evidence in deployed source | Result |
|---|---|---|---|
| 1 | Supervisor `provision_slot` records `provision_task`, `provision_generation`, `provision_base` (plus `worktree_head`, `provision_evidence`) bound to the task's current generation | control.py:558-573; field list `PROVISION_FIELDS` control.py:122-123 | VERIFIED |
| 2 | Provision is refused when the slot already carries an active one (`slot_already_provisioned`) and when the task is not RUNNING | control.py:562-563 | VERIFIED |
| 3 | Claim refusal `stale_provision_requires_recovery`: a free slot of the right kind still carrying an ACTIVE provision is refused, not silently adopted; `no_free_slot` distinguishes the no-slot case | control.py:428-436; same guard in the detached-capacity claim override review_handoff.py:78-87 | VERIFIED |
| 4 | Worker claim loop classifies `stale_provision_requires_recovery` as recoverable contention: skip and retry later; refusal is observable in `claim_once`'s refusals list; comment names supervisor `slot_rebind` as the recovery | run_queue_worker.py:71-80 | VERIFIED |
| 5 | Supervisor `slot_rebind`: supervisor-only; attests `preservation_evidence` AND `drain_evidence`; never touches the filesystem (`filesystem_touched: False`); stale record moves to `preserved_provisions` with reason `supervisor_slot_rebind` | control.py:574-598 | VERIFIED |
| 6 | `slot_rebind` refusal reasons: `no_stale_provision` (slot has no active provision), `slot_task_not_running` (bound task not RUNNING), `resources_still_held` (old provision task still holds resources) | control.py:585, 589, 594 | VERIFIED |
| 7 | Evidence-preserving retire: `_preserve_provision` moves the FULL provision record to `engine['preserved_provisions']`, bounded at `PRESERVED_PROVISION_LIMIT = 20` (oldest dropped first), then clears `provisioned` and all `PROVISION_FIELDS` so no later task/generation inherits source authority | control.py:124-147 | VERIFIED |
| 8 | Preserve call sites and reasons: `recover` → `recovered_task_generation`; `release_slot` → `released_after_integration`; `slot_rebind` → `supervisor_slot_rebind`; `release_review_slot` → `released_for_review_handoff` | control.py:523, 656, 595; review_handoff.py:148 | VERIFIED |
| 9 | `recover` (supervisor-only) refuses `resources_still_held`, drops queued requests `recovered_generation`, requires preserved-and-writer-stopped evidence, returns READY at generation+1 with `old_workspace` preserved | control.py:512-527 | VERIFIED |
| 10 | `release_slot` (supervisor-only) requires INTEGRATED + slot binding, refuses `resource_still_held`, returns `filesystem_deleted: False`; slot held until cleanup attestation | control.py:649-658; ack_integration return control.py:546 | VERIFIED |
| 11 | `release_review_slot` (supervisor-only): verifies frozen binding (owner/generation/slot/head), `head == pushed_head == pr_head` (`review_head_identity_mismatch`), refuses `resources_still_held`, `stale_generation`, `stale_slot`, `review_head_changed`, `slot_binding_mismatch` | review_handoff.py:95-124 | VERIFIED |
| 12 | Handoff receipt with provision identity: receipt appended to task `review_slot_handoffs` carries owner, generation, slot, head, branch, review, checkpoint, pr_identity, pushed/pr heads, the four evidence attestations, a `provision` block (`provision_task`, `provision_generation`, `provision_base`, `worktree_head`, `provision_evidence`) and `released_revision` | review_handoff.py:126-144 | VERIFIED |
| 13 | Detached REVIEW: slot task cleared, engine reset carrying `preserved_provisions` forward, `task.slot = None`, returns `filesystem_deleted: False`, acceptance `NOT_CLAIMED` | review_handoff.py:145-157 | VERIFIED |
| 14 | Detached REVIEW consumes neither slot nor submitter capacity: capacity override excludes slot-less reviews that have handoffs from the active count; write-scope protection retained | review_handoff.py:54-93 (capacity 66-71, scope 74-77) | VERIFIED |
| 15 | `ack_integration` on a slot-less handed-off task returns `slot: null`, `slot_status: RELEASED_AT_REVIEW_HANDOFF` | review_handoff.py:34-42 | VERIFIED |
| 16 | Correction path: lead `review_requeue` on a slot-less REVIEW requires the last handoff head (`missing_review_slot_handoff`), cancels pending broker requests (`CANCELLED_REQUEUED`), returns READY with `correction_base_head`; provisioning must then match that exact head (`correction_worktree_head_mismatch`) until `correction_provisioned_head` is recorded | review_handoff.py:159-186, 43-51 | VERIFIED |
| 17 | Slot-less recovery of a failed review: supervisor `recover` requires the review handoff receipt, records `review_recovery_history`, cancels requests `CANCELLED_RECOVERED_REVIEW`, READY at generation+1 with `correction_base_head` = reviewed head | review_handoff.py:188-217 | VERIFIED |
| 18 | `release_slot` on an already handed-off task is a no-op attestation: `released: False`, `already_released_for_review: True`, `filesystem_deleted: False` | review_handoff.py:219-227 | VERIFIED |
| 19 | Worker executor refuses to run against an unprovisioned or mismatched slot: `execution_claim_changed`, `execution_slot_not_provisioned`, `execution_branch_mismatch`, `execution_history_mismatch`; timeout retains ownership, checkpoints BLOCKED | run_queue_worker.py:144-160, 183-188 | VERIFIED |
| 20 | `run_queue.py` is a pure in-memory reference model: "never durable scheduling authority"; no Git/engine/network/filesystem effects | run_queue.py:1-5 (deployed copy) | VERIFIED |
| 21 | Prompt blocks name their own session/claim mechanism; no Alan-relay steps: worker/subagent/reviewer act through their own session file and owned claim; supervisor operations (slot_rebind, release_review_slot, recover, release_slot) are named as the supervisor's own operations, never as something Alan relays | PROMPTS.md (this change); cross-checked against THE_REVIEW_SLOT_HANDOFF.md "Adapter operations" | VERIFIED |

## Falsifier status

- F1 (documented operation that does not exist): NOT FIRED — items 1-20 all verified.
- F2 (Alan-relay steps in prompts): NOT FIRED — item 21.
- F3 (contradiction with AGENTS.md law): NOT FIRED — historical sections appended,
  not rewritten; `docs/THE_MASTER_LIST.md` untouched; docs only, no code changes.

## Acceptance

NOT_CLAIMED (per the review contract; acceptance is the lead's/supervisor's call).
