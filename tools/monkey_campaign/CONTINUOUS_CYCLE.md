# Current delivery direction — astra-0030

[DELIVERY.md](DELIVERY.md) governs priority, bounded review and integration reporting. Read it before applying older maximum-parallel wording below.

# Continuous work cycle (file-package era, 2026-10-01)

Start here with [docs/WORKFLOW.md](../../docs/WORKFLOW.md) (method map) and
[NO_WORKTREES.md](NO_WORKTREES.md) (the package contract). Keep the same arrival
ID. Execute the returned assignment, then continue through the appropriate handoff
command. Do not end after a report while another useful assignment is available.
These helpers do not launch an AI model themselves.

Capacity is no longer a ten-slot ledger: it is the per-card attempt records in the
registry (the single authority), the API-agent target 12 / ceiling 15 including
descendants from runner_profile.json, four CPU package slots (BUSY, exit 75, retry
with backoff), one publication writer, and the existing GPU queue. Dispatch is
advised by the continuous scheduler
(`E:/ChimeraWork/monkey-coordination/compiler-scheduler/scheduler.py`, serving
since 2026-10-01) and consumed by the Lieutenant; workers acquire work ONLY
through the registry join/claim path in `worker_start.py`.

1. Implement or correct a card inside its pinned file package (never a new clone
   or worktree; never an experiment in the editing package). Read its ontology
   packets and task inbox. Preserve criteria and resource limits. Seal and run
   through `task_package.py`; declare every needed output with `--keep`.
2. For a candidate awaiting lead publication, send the sealed patch (manifest hash,
   base SHA, changed-file list and run receipts, with actual file paths and raw
   SHA-256 hashes) to the publication owner through the task inbox. The packet law
   is LEAD_SERIALIZED: the candidate goes to the publication owner for lead
   publication to the card's review/<task-id> branch; no worker push to the
   numbered branch. A publication request is not a GitHub PR; lead publication is
   still required. (The old --request-pr flag and publication_request_template no
   longer exist in worker_start.py.)
3. For an actual PR, use the existing --submit-pr handoff. Submitted candidates
   live in the separate Review queue and free Development capacity. Submission
   does not complete the task or unlock its dependencies. See REVIEW_LANE.md.
4. Once no eligible implementation remains, startup assigns an independent PR review
   at a pinned head. Review can proceed regardless of occupied Development work or
   busy CPU slots; the separate Review queue is not limited by the four package
   slots. Rerun appropriate checks, inspect actual visual evidence where required,
   and retain failures. Missing native/visual evidence is a gap, never a synthetic PASS.
5. Fill review_result_template and invoke:
   `worker_start.py --arrival-id YOUR_ID --review-result review.json`
   This records the verdict. The next card is dealt only when you also pass
   `--take-next`; park and checkpoint never re-deal. CHANGES_REQUIRED reopens
   correction work on the same card (the scheduler emits a correction dispatch only
   when the failure signature changed: new review body, head or round). PASS
   records a recommendation; it never fabricates lead approval or a GitHub merge.
6. The lead reviews verification receipts, publishes/merges acceptable exact heads,
   and records verified task completion to unlock dependent work. Development
   refills whenever eligible work exists, including after submission. The next task
   receives its assigned numbered branch, ontology binding and criteria hash;
   publication uses the card's review/<task-id> branch, which the publisher seeds
   local AND remote at the integrated tip BEFORE the card's first dispatch so a
   joining worker can pin its package base (the scheduler's named_ref_observation
   flags a missing ref for publisher refresh).

An explicit switch away from active work requires a saved checkpoint and --park.
No other worker is stopped, expired or impersonated. Do not review your own PR as
independent. If all eligible work is awaiting lead publication/merge, or only your
own PRs remain, preserve state and report that exact gate rather than loop wastefully.
Actual task/resource blockers remain valid; do not invent tasks to conceal them.
The cancelled timer remains cancelled; these transitions happen when workers or
the operator-engaged lead invoke the system.
