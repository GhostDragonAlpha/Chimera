# Current merge owner — astra-0026

MERGE_SERVICE.md supersedes local ready/merge execution below: ZCode workers prepare and review; the connected lead services ACCEPTED heads on operator-triggered lead sessions. Release your coordination claim after recording acceptance, then continue work. Do not attempt tokenless merges or file duplicate credential blockers.

# GitHub capability and continuation — astra-0024

Missing gh does not establish operator-only PR access. Check your available GitHub
connector/tools and configured noninteractive API authentication. Never extract or
copy another harness's credentials or prompt for login. SSH push alone cannot open
or merge PRs. If your harness lacks that capability, post one exact-head API request
in the task inbox for the connected Astra reviewer, then continue independent review
or other eligible work. Already published candidates must not be reimplemented.

The current batch now has real draft PRs #117–#128. Read the registry for the mapping;
do not infer numbers or carry a previous nonexistent-PR approval forward. Draft PRs
are reviewable; final merge still requires actual readiness, independent exact-head
review, applicable ontology/visual qualification and a successful GitHub merge.

When a coordination queue is blocked by a concrete external capability, release-lead
accepts defer_unchanged_queue:true plus blocker_reason and the usual stopped-writes
checkpoint. This prevents immediate reassignment of the same queue to that identity;
a changed PR head/status or new publication/review allows another attempt. It does
not block other capable agents. Then run startup and execute its next review/card.
Stop only when there is no eligible work and name the exact remaining external gate.
Do not claim that documentation grants credentials or invent busywork to stay active.

# Current publication policy

REVIEW_LANE.md supersedes numbered-branch publication below. Use each card publication_branch: review/<task-id>. Development slots are freed on durable handoff, not merge. Existing PRs retain their original head branches. This is final verification/publication work, not architectural leadership.

# Automatic operational lead

Current operator directive supersedes the earlier Astra-only publication/merge rule.
The arrival awarded OPERATIONAL_LEAD_ASSIGNED becomes the execution coordinator
immediately. Do not finish the session saying publication belongs to Astra. Work the
returned queue. Astra remains architectural lead; scope, physical definitions,
acceptance thresholds, licensing and scientific rulings remain reserved decisions.

The role is acquired atomically in the shared registry. Retain your own arrival ID
and returned token. Never set actor to astra-codex. One holder serializes remote
branch publication; other agents continue implementation and independent review.
This is an authority convention in the shared workspace, not a cryptographic
security boundary against code with direct database access.

## Execute the queue

1. Re-read task inboxes and each publication request. Locate the original attempt
   checkout, exact candidate commit, preregistration and artifacts. Recompute their
   recorded hashes; inspect the diff against the card and preserve provenance.
   A report saying tests passed is insufficient. Missing evidence goes back to
   the task inbox with concrete corrections; existing architectural rulings apply.
2. Publish only the card's reviewed candidate changes through its branch-N in an
   isolated publisher checkout. Inspect the branch's current remote tip and current
   PRs first; preserve existing work. Do not overwrite branches or force-push over
   another tip. Resolve conflicts with relevant verification. Do not copy a whole
   source tree into a contribution directory. Open/update a PR targeting
   astra/gait-capture with task ID, original attempt, criteria hash and actual checks.
   Use available authenticated GitHub tooling. If unavailable, record the exact
   authentication/tool failure, keep the candidate, and handle other eligible work.
3. Record the published PR with kanban_cli.py record-publication --arguments FILE.
   JSON fields: actor (your arrival ID), role_token, task_id, request_id,
   criteria_sha256, pr_url, head_sha. The CLI reads GitHub to verify the PR's actual
   head, numbered branch and base. Authorship stays with the original worker.
4. Obtain an independent review of that exact published head and criteria through
   the worker review loop. Review your own or your construction subagents' work
   using a separate non-author reviewer, not a renamed identity. If your harness
   supports delegation, use available independent workers; do not invent them.
   Preserve CHANGES_REQUIRED findings and fix/re-review. A previous PASS does not
   apply to changed bytes. Structural checks never replace numerical/native/visual
   evidence required by the card. Camera/capture gates remain mandatory.
5. With a recorded exact-head non-author PASS, use kanban_cli.py review with actor,
   role_token and the usual review arguments. A coordinator may approve based on
   their own recorded review only if they are actually independent of the authors.
   Include ontology_qualification for ONT cards. Resolve existing lead inbox findings
   only with evidence; do not waive them or change the frozen criteria.
6. Merge the approved exact head using GitHub tooling with a head-SHA precondition.
   Then call kanban_cli.py accept-merge with actor, role_token, task_id and pr_url.
   The CLI independently fetches merged state; receipt acceptance/refill is atomic.
   A merge conflict, failing check or review is work to resolve, not permission to
   skip a gate. Retain branch-N and continue its new card after verified refill.
7. Continue publication/review/merge/refill. When returning to worker work, or before
   stopping, call kanban_cli.py release-lead with actor, role_token, checkpoint and
   writes_stopped:true. Checkpoint exact PR heads, pending operations and blockers.
   Then call worker_start.py with your original --arrival-id and an explicit --task
   for independent review/implementation if remaining coordination awaits another
   reviewer. Do not hold the role while idle or doing lengthy implementation.

There is no timer takeover: a crash leaves a visible coordination claim. Astra can
release it after checking publication state and preserving the checkpoint; a second
publisher must not silently steal it. Architectural blockers such as changing the
walking mass registration go to the suggestion box; they do not block unrelated
publication. The operational role does not authorize training, resource preemption
or changing the sealed plan beyond already granted permissions.
