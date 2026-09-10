# Review-slot handoff — preregistration

Recorded before writing this private design.  No live slot, task, controller,
service, process, or worktree will be changed.  In particular, neither the
stopped extra Buffy task nor the possibly slot-4 GLM task will be released.

## Statement

A task whose exact pushed head is submitted in a PR can remain frozen in
`REVIEW` while releasing its scarce physical slot.  Its owner, generation, head,
review evidence, branch, checkpoint, and integration eligibility remain exact.
If review requests corrections, the current lead atomically reacquires a free
slot for the same task/owner, advances the generation once, retains the reviewed
head in history, clears the active head, and returns the task to `RUNNING` for
ordinary reprovisioning.  This is distinct from failure recovery, which returns
a task to `READY` and may change owner.

## Predicted transitions

An additive `ReviewHandoffControl(Control)` handles two operations through the
inherited `Control.call` transaction/authentication/event path:

1. `release_review_slot` is supervisor-only and requires exact task, owner,
   generation, slot, registry head, pushed remote head, and PR head; all three
   heads must be the same 40-hex commit.  It also requires nonempty PR identity,
   remote verification, preserved evidence, writer-stopped evidence, runtime
   drain evidence, and slot-ready-for-reprovision evidence.  The task must be
   `REVIEW`, its slot binding exact, and it must hold no actual resource.  The
   operation resets only that slot to canonical unprovisioned layout and clears
   task.slot.  It does not alter task state, owner, generation, head, review,
   checkpoint, branch, integration, agent, resource, leader, epoch, requests, or
   other tasks/slots.  It appends a handoff receipt containing the exact review
   identity and evidence.
2. `review_requeue` preserves the existing base behavior when a REVIEW task still
   owns a slot.  When task.slot is null, it remains lead/current-epoch only,
   requires the exact current review head, refuses if no matching-kind slot is
   free, binds one slot atomically, changes REVIEW to RUNNING, advances generation
   exactly once, clears active head, records the previous review identity in an
   append-only correction history, and exposes the new worktree/engine plan.
   Pending integration requests for that task become terminal
   `CANCELLED_REQUEUED`; unrelated requests do not change.  The same owner stays
   assigned.  The newly allocated slot is unprovisioned and requires the normal
   supervisor provisioning gate before use.

`integration_request` and `ack_integration` already depend on REVIEW state/head,
not slot, so a slotless REVIEW remains integrable.  Existing post-ack
`release_slot` must either remain unused for such a task or be made a documented
idempotent no-slot result in the extension; existing INTEGRATED tasks that still
hold slots retain the old release behavior.

## Falsifiers

1. Slot release succeeds without supervisor auth, exact task/owner/generation/
   slot/head identity, verified pushed/PR equality, all drain attestations, REVIEW
   state, exact slot binding, or zero actual resource holds.
2. Release changes any frozen review field, agent/session, leader/epoch,
   integration request, resource, unrelated task/slot, or filesystem, or fails to
   clear stale provisioning metadata in only the released slot.
3. A slotless REVIEW cannot create an integration request or receive a valid
   integration acknowledgement for its exact head.
4. Correction requeue runs under a nonlead/stale epoch/stale head, proceeds with
   no free matching-kind slot, changes owner, increments generation other than
   once, loses prior review evidence/head, leaves active head set, or fails to
   cancel only target pending integration requests.
5. The previous generation can write through task APIs after correction requeue,
   or the correction can run without normal slot provisioning.
6. Existing slotted `review_requeue`, post-integration slot release, recovery,
   resource scheduling, and service HTTP authentication regress.
7. Stored schema-1 registries lacking new optional history fields cannot be read
   and transitioned additively.

The control plane records human/supervisor drain attestations but cannot stop a
foreign process or prevent a human from resuming an old authenticated tab.
