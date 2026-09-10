# Review-preserving slot handoff design

## Boundary

This proposal adds `ReviewHandoffControl` as the controller instantiated by the
loopback service.  It does not edit `control.py`, touch the live registry,
release a live slot, mutate Git, remove a worktree, stop a process, or attest to
a remote PR.  The supervisor broker supplies the external pushed-head, PR-head,
writer-stop, runtime-drain, and preservation observations.

## State transitions

The ordinary submission transition remains the existing
`RUNNING -> REVIEW`.  Once the submitted commit is pushed, the PR head is read
back, the writer is stopped, task resources and runtimes are drained, and the
worktree is preserved elsewhere or is safe to reprovision, the supervisor may
call `release_review_slot`.

```
REVIEW + slot N
  -- release_review_slot(exact owner/gen/slot/head, broker evidence) -->
REVIEW + slot null + immutable handoff receipt
```

The operation clears only the registry binding for slot N and resets that
slot's engine metadata to `slot_layout(...)`.  It preserves the task's REVIEW
state, owner, generation, head, branch, review, checkpoint, integration field,
agent identity, leader, epoch, resources, requests, and every unrelated task and
slot.  A second call with the old slot is a named `stale_slot` refusal and rolls
back.

A detached REVIEW does not consume the owner's execution capacity because it
has no execution slot.  It continues to block overlapping write scopes.  The
extension copies the base `claim` predicate because `control.py` is outside the
task scope; qualification, capabilities, dependency, lead-only, master-list,
scope, slot-kind, and no-free-slot checks remain byte-for-byte equivalent apart
from the capacity exclusion.  The rebound base suites are the drift check.

Integration remains the inherited flow.  `integration_request` and
`ack_integration` already bind the exact REVIEW head without consulting a slot.
After inherited acknowledgement succeeds, the extension changes only the
returned slot description for a handed-off task to `slot: null` and
`slot_status: RELEASED_AT_REVIEW_HANDOFF`.  Slotted acknowledgements retain the
base result.  The later legacy `release_slot` call is accepted as an idempotent
no-slot cleanup acknowledgement for an integrated task with a handoff receipt.

For requested corrections:

```
detached REVIEW(head=H, generation=G)
  -- lead review_requeue(exact H) -->
READY(owner/slot/head=null, generation=G, correction_base_head=H)
  -- qualified worker claim -->
RUNNING(new slot, generation=G+1, correction_base_head=H)
  -- external exact-H materialization + supervisor provision_slot(H) -->
RUNNING(correction_provisioned_head=H)
```

The requeue receipt retains the previous head, review, checkpoint, submitter,
generation, and handoff.  Target pending integration requests become
`CANCELLED_REQUEUED`; unrelated requests remain unchanged.  Requeue does not
need a free slot.  The later ordinary claim does.

While `correction_base_head` is pending, the exact owner may write a checkpoint,
but authenticated `resource_request`, legacy `resource_acquire`, and
`submit_review` refuse `correction_provision_required`.  Foreign or stale
sessions first receive the inherited `stale_or_foreign_claim` refusal.  This is
an API admission gate; it does not fence arbitrary filesystem or process use.

If the retained owner fails after handoff, the inherited failure transition
first invalidates its generation and moves the task to slotless RECOVERY_HOLD.
The extension's slotless recovery preserves the reviewed artifact in recovery
history, cancels target pending integration requests, clears the active head,
sets `correction_base_head`, and returns READY with no owner or slot.  A
replacement then uses the same claim/materialize/provision path.  Existing
generation behavior is retained: failure, recovery, and replacement claim each
advance the generation.

## Storage and compatibility

The SQLite schema number stays 1.  The proposal adds task-local JSON fields only
when a transition needs them:

- `review_slot_handoffs`: append-only handoff receipts.
- `review_correction_history`: append-only correction receipts.
- `review_recovery_history`: append-only slotless recovery receipts.
- `correction_base_head`: exact commit required at the next provisioning gate.
- `correction_provisioned_head` and revision: consumed receipt after provision.

Both the old deployed `control.py` and the integrated resource-lifecycle version
can deserialize these fields.  The extension's focused tests pass with either
base.  Operational rollback to the base class is not safe after creating a
detached task: the old class can integrate a detached review, but cannot recover
one and counts it against capacity.  Deploy or roll back the service and its
extension as a unit.

## Call-site and operational migration

- `service.py` must instantiate `ReviewHandoffControl`; its HTTP protocol and
  `Control.call` transaction, authentication, event, and rollback path remain
  unchanged.
- Existing clients can continue submit/integrate/release with a held slot.  To
  free it at PR submission, the supervisor broker calls the new operation only
  after external identity and drain checks.  Afterward, callers must not ask
  `fleet_worktree` for the detached task.
- `demo_live.py`'s current held-until-integration path remains valid.  Adopting
  early handoff requires inserting the broker call after PR verification and
  accepting the idempotent post-ack cleanup result.
- `inventory.py` already derives occupancy from `slots[*].task`, so it sees the
  released execution capacity without a migration.
- Existing `provision_slot.py create` refuses an already-existing task branch.
  A correction run therefore needs an operator-owned, documented Git step that
  parks/removes the drained old worktree and materializes the existing branch at
  `correction_base_head`; the controller then verifies that exact head through
  `provision_slot`.  This scoped proposal deliberately does not claim that the
  controller performs the Git operation.
- `test_control.py`, `test_bootstrap.py`, `test_resources.py`, and
  `test_resource_lifecycle.py` must also run with their imported `Control`
  rebound to `ReviewHandoffControl`.  The private runner demonstrates that
  composition for both available base generations.

The service restart test shows that schema-1 persistence retains the detached
review, handoff, correction receipt, replacement claim, and exact provisioning
requirement.  No test opens the live registry or performs a process, GPU,
worktree, remote, or slot operation.
