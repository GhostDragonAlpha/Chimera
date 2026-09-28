# Development and Review

Ten numbered slots are development capacity. Review is a separate durable queue
addressed by task ID, with one publication branch named review/<task-id> per task.
The name is reserved in the card; the branch is created when the candidate is
actually pushed. It is never a shared branch containing unrelated unreviewed work.

Submit hash-bound candidate artifacts with worker_start.py --request-pr as before.
That durable handoff moves the card to Review / publication pending and frees its
development slot atomically. No GitHub PR or merge is claimed until actually verified.
The next eligible dependency task refills the free slot. Already published legacy
PRs remain on their original branches and retain their exact-head review history;
do not recreate or close them merely to rename a branch.

Fresh workers select eligible development first. When development offers no work,
they may help publish or independently review the Review queue. Astra can review
the queue directly. The existing serialized final-review/merge capability remains;
it does not grant architectural authority. Calling it OPERATIONAL_LEAD_ASSIGNED
is a compatibility field, not a change of project leadership.

Corrections go to CORRECTION_QUEUED, retaining the same task, PR, evidence, inbox and
criteria. They get the next available development slot before ordinary backlog.
A correction already handed off is not duplicated. Updated heads need fresh review.
Only approved, GitHub-verified merges mark DONE or unlock dependencies.

An old attempt whose card left Development must preserve/cease writes and submit
the returned park_template. Its checkout remains intact. Its historical slot does
not grant access to the new task in that slot. The summary reports current slots
only for Development, and exposes distinct development/review/corrections sections.

## GitHub publication

Use the card's publication_branch (review/<task-id>), not its historical branch-N.
Publish only candidate changes from the isolated attempt, inspect current remote
tips, and never overwrite another branch or unrelated pending work. The isolated
development checkout can still be named branch-N locally. Numbered branch names
are not the destination for submitted PRs under this policy. Base remains
astra/gait-capture. Record actual PR URL/head through the existing verified path;
all exact-head, independent-review, numerical and visual acceptance gates remain.

No extra files or captures are copied merely to move a card between lanes. A free
slot is filled only when dependencies permit; blocked work is not manufactured
to make the count ten. Disk limits and cleanup protections remain unchanged.
