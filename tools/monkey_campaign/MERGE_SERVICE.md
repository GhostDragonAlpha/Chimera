# Connected-lead merge service

## Owner, trigger and service expectation

The operator chose option 2: Astra, or the operator-appointed replacement lead with
an authenticated GitHub connection, owns draft-to-ready and GitHub merge execution.
ZCode campaign workers do not currently have those API credentials. They must not
attempt unauthenticated merges, invent credentials, or rediscover this same known
capability boundary. No new PAT is installed by this policy.

The service runs when the operator starts/resumes a lead session or explicitly
requests queue service. At the start and again before ending that active session,
the connected lead reads `kanban_cli.py merge-queue`. Within that session it handles
each ACCEPTED exact head present in the scan: merge and reconcile, or leave a named
head-specific blocking finding. There is no unattended polling, five-minute timer,
or promised wall-clock turnaround while no lead session is running. New ACCEPTED
heads after the final scan wait for the next operator-triggered lead session.
This replaces the expectation that every worker can execute GitHub merges.

## Worker responsibility

Finish scoped implementation, push/publish through the approved path, obtain actual
independent exact-head review, and record ACCEPTED only when authorized and evidenced.
Use the task inbox for a one-time merge-service request; the accepted registry record
is the durable queue item. Release coordination before returning to other work.
Accepted-only queues are excluded from worker coordination assignment under this
policy. Continue other eligible development or review. If every remaining step
requires the connected lead, checkpoint that precise state; do not busy-poll.

## Connected-lead execution

1. Read `python -B E:/PythonChimera/tools/monkey_campaign/kanban_cli.py merge-queue`.
2. Confirm approval, head, criteria and unresolved findings locally; freshly fetch
   GitHub head/base/draft/mergeability and applicable checks. PASS alone is not ACCEPTED.
3. Mark the exact candidate ready through the available authenticated GitHub tool.
4. Merge with expected_head_sha set to the full approved head. Any changed head,
   conflict or required check failure blocks that operation. Do not force a merge.
5. Call the existing kanban_cli.py accept-merge with actor astra-codex, task_id and
   pr_url. That CLI fetches GitHub independently; it alone records DONE/refill.
   If the remote merge succeeded but local reconciliation failed, retry accept-merge
   against that actual merge. Never fabricate a winner or merge another head.
6. Preserve receipts and tell the task inbox what happened. Do not steal or clear
   another active coordinator claim; connected lead merge service is a separately
   assigned capability. Workers cannot also execute remote merges under this policy.

Development slots were already released when candidates entered Review. A merge
can now unlock dependent/follow-up work; it does not clear a historical slot that
another task may be using. A diagnostic merge does not qualify parent gameplay.

## Verified first service batch

On 2026-09-25, #118 was merged at approved head
24db3062187e617cf576019adb131926df63a237, merge commit
a4fb2b41435904d56a2947973a08f0eab7bb4ec7. The worker-host CLI independently returned
COMPLETED and assigned D-W04-MASS-20260924-FOLLOWUP to Development. #119, #120 and
#117 were also merged at their accepted heads and reconciled via the same CLI.
Receipts: E:/Chimera/merge-service/accept-*-result.json. These are historical facts;
always query the live queue for current work.
