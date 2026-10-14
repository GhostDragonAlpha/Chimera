# Worker report triage and recovery — 2026-09-25

## Confirmed identity sequence
The forest attempt c95e1722350849bca846b237c1f60997 EXISTS in SQLite and belongs to arrival-bccd7c8d08df43869d1dfcd3d913de59. Subsequent tasks belong to the distinct worker identity c95e1722350849bca846b237c1f60997. This is consistent with copying an attempt ID into --arrival-id, not a lost transaction. Do not merge these identities or delete their work. Registry WORKING is not proof of a live process.

## Installed recovery improvements
Startup reads registry metadata directly from SQLite, not STATUS.json. Before checkout creation it atomically saves a minimal identity receipt under E:/ChimeraWork/monkey-coordination/startup-receipts/ (filename = SHA256 of the arrival identity), prints its path and arrival ID to stderr, and puts arrival_id first in stdout JSON. Receipt carries task, assignment, criteria and workspace; no role token. Retry the receipt's arrival ID. Never use attempt ID as arrival ID. Receipts are recovery hints; SQLite is assignment authority. An abrupt kill between claim and receipt remains recoverable from SQLite: this is not a filesystem/database atomic transaction guarantee. Partial checkouts remain preserved for inspection. Closed stdout is not reported as an unclaimed task.

## Reproducer locations
- Trace and ledger: E:/Chimera/queue-review-20260925/probes.py
- Package: E:/Chimera/queue-review-20260925/probe124.py
- Lead decisions: E:/Chimera/queue-review-20260925/REVIEW.md
- Additional trace statistics boundary: E:/Chimera/zcode-quality-20260925/independent_probes.py
These are actual local files. Ask for artifact transport when working on another host; never guess a relative path.

## Remaining report items / dispositions
1. Lost-claim diagnosis contradicted by live records; identity recovery improved. No orphan deletion authorized by a label.
2. Bare reproducer filenames are poor guidance: absolute references supplied above and in affected task inboxes.
3. Historical play worktree scope is not current authority. Use E:/PythonChimera/tools/monkey_campaign/monkey_completion_map.json and APPROVED_SCOPE.json for current scope; pinned worktree copies remain historical source evidence. Do not synchronize them by overwriting active worktrees.
4. Candidate discovery is an improvement backlog item. Unsubmitted bytes cannot be accepted or attributed without identity/hash review. Preserve any candidate and report its absolute path/hash to the existing task inbox; do not invent ownership or verification.
5. A local missing merge object is not an absent GitHub merge. Publisher/reviewer may fetch the verified exact source commit into its isolated checkout via its configured approved Git remote, then use git show HEADSHA:path. Reconcile task-specific source restrictions; never switch/reset the shared checkout. Read source from the winning PR/commit, not an unrelated live file.
6. Publication backlog is real. No new cap silently introduced: existing operator policy favors continuous work. Authenticated publication service and explicit backpressure remain architectural work; review requests do not equal PR URLs.
7. Cleanup requires evidence of cessation and durable work preservation. No automated deletion based on time or WORKING labels; known partial checkouts preserved.
8. Generated ontology briefs contain task kind under spec.ontology_qualification.task.kind; some lack authored output schemas. Generic brief improvements remain open; do not invent acceptance criteria or claim all cards already have owned_files lists.
9. Current I-GOV read_first is E:/Chimera/pr-review-20260925/REVIEW.md (exists), not the reported E:/PythonChimera path. No active card criteria changed.
10. Startup no longer consumes stale STATUS.json metadata; external consumers must use Registry.readonly(). Historical snapshots remain historical.
11. _artifacts enforces containment, existence and raw hashes, not semantic completeness. Deliberate evidence flexibility does not replace independent review or the ontology qualification gate. Artifact-schema/required-deliverable enforcement remains separate work, not silently changed here.

No scratch files, attempts, checkouts, criteria or active coordination claims deleted or reset. Review current tasks with their existing identities; do not resubmit already-pending handoffs.
