# Review and execution slot handoff

Status: implementation and validation in progress under
`fleet-review-slot-handoff-01`. The live controller has not adopted this contract.

Alan's requirement is that a submitted task PR releases execution capacity while
the task remains available for lead review. A pending PR is not accepted work.
Slot 1 continues reviewing the queue; workers continue eligible independent tasks.

## Statement, prediction, falsifiers

Statement: a preserved, drained task at an independently verified pushed PR head
can remain frozen in REVIEW without occupying a physical slot or the submitter's
execution capacity. Corrections can resume from that submitted head in an
available registered slot, including under a qualified replacement worker.

Prediction: a worker at capacity can submit and hand off its PR, claim unrelated
work, and later have its original PR integrated without disturbing the new task.
A requested correction returns to READY, then normal claim and provisioning
restore the exact reviewed branch head before editing.

Reject the implementation if it loses evidence or branch history, releases a task
with resources or an active writer, accepts mismatched PR/remote/registry heads,
changes another task or slot, counts detached reviews against execution capacity,
permits overlapping write claims, accepts stale correction writes, or treats
submission as integration. The controller's transactions must roll back refusals.

## Handoff responsibilities

The worker stops writing, drains its task processes and reservations, commits and
pushes its task branch, opens a PR targeting `astra/gait-capture`, and submits the
exact head for review using its own provisioned client. It records preservation
and drain evidence. A PR URL alone does not prove that local work was preserved.

The trusted lead/broker independently checks the remote branch, PR repository,
base branch and exact head against the frozen controller record. It checks the
slot's actual branch/head, staged changes and untracked artifacts, preserving
anything outside the commit before allowing reprovisioning. It then records the
verified handoff through the authenticated controller operation. Supervisor
credentials remain outside worker sessions and evidence.

The controller records attestations; it does not execute Git, stop arbitrary
processes, or make a stale shell unable to write files. Distinct concurrent tabs
need distinct session identities. Do not infer a tab's ownership from Git authors
or a shared display name.

## Review and corrections

A detached REVIEW retains its exact submitted head, branch and evidence. It still
protects its write scope from overlapping claims. It does not consume a slot or
the submitter's execution capacity. Slot 1 may integrate its exact reviewed head
through the existing fenced publication path.

For corrections, the current lead records the rejected/revised review head and
reason, cancels pending integration requests for that review, and returns it to
READY. A qualified worker claims the task normally. Provisioning must start at
the submitted correction head, preserving the original branch history; it must
not silently start over at the original integration base. Normal merge commits
handle subsequent base changes. Never force-push or reset the operator checkout.

A released worktree can still have its previous branch checked out. Before
reusing it, the provisioner verifies preservation and uses an ordinary branch
switch in that released slot. Before attaching a correction branch elsewhere,
it verifies the branch is no longer checked out in another active worktree.
Controller metadata is not evidence that these filesystem steps happened.

## Deployment boundary

Run the new lifecycle tests against the currently deployed controller source and
the integrated reference, then the relevant existing fleet regressions. Test
authenticated HTTP, capacity reuse, exact-head integration, correction reclaim,
stale generations, failures/recovery, refusal rollback and resource retention.
Retain failed runs and exact source identities.

Publish and review the change before a controlled service transition. Preserve
the existing registry and credentials; announce the interruption, verify the
owned service/listener, and retain an exact rollback package. Check assignments,
resources and leadership after restart. Reverting to an older service after new
slotless states exist requires an explicit compatibility/reconciliation plan.
No live slot is freed merely because this document exists.

## Adapter operations

Use the provisioned `tools/agent_fleet/client.py`; its JSON envelope is
`{"operation": "operation_name", "arguments": {}}`. The CLI accepts the argument
object through `--arguments`, not a nested envelope file. Workers use only their
own session for `submit_review`, with `task`, `generation`, `branch`, `head` and
`evidence`. No worker should hand-build a supervisor request to resolve an
`invalid_envelope` error.

After independent verification, the trusted broker calls `release_review_slot`
with these fields:

| Field | Evidence required |
| --- | --- |
| `task`, `owner`, `generation`, `slot` | Exact frozen controller binding. |
| `head`, `pushed_head`, `pr_head` | Matching full commit IDs, independently checked against the remote branch and task PR. |
| `pr_identity` | Verified repository, PR number and target `astra/gait-capture`. |
| `remote_verification_evidence` | Record of the remote checks, not merely a worker's claimed hash. |
| `preservation_evidence` | Retained committed history and any uncommitted/untracked evidence. |
| `writer_stopped_evidence` | The worker has ended writes to this task's slot. |
| `runtime_drained_evidence` | Owned processes drained and reservations released. |
| `slot_reprovision_ready_evidence` | Actual worktree inspected and safe to reprovision without losing unrelated work. |

For a detached review, lead `review_requeue` requires `epoch`, `task`, exact
review `head`, and correction `evidence`. It returns READY without allocating a
slot. The next ordinary `claim` increments the generation and returns
`correction_base_head`; supervisor provisioning must verify that exact head.
Until then, correction resource requests, resource acquisition and review
submission are refused. Checkpoints remain available for preparation.

The claim override preserves qualification, dependency, slot-kind and scope
checks from the base controller. Future changes to those checks, including
catalogue admission, must update and regression-test the extension together.
