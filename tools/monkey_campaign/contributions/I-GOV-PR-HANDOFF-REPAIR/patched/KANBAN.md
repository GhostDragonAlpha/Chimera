# Ten-card Kanban â€” current workflow

The ten slots are TASKS, not worker reservations. No 20-minute or hourly expiry exists.
Multiple workers may attempt the same card in separate workspaces and branches.
The first qualifying PR reviewed by Astra and merged to astra/gait-capture wins.
The lead then records GitHub's merge; the card closes and the next eligible backlog
item occupies the freed slot atomically. If no dependency-ready item exists, report the
gap instead of inventing filler. Neither an early submission nor a report is completion.

## Worker loop

1. Run worker_start.py, retaining arrival_id. Optionally add --task TASK_ID to revisit
   a correction. Read assignment.task_inbox, criteria hash and legacy_work before edits.
2. Use only your returned attempt workspace and branch. It is a nonexclusive attempt
   on the card, not permission to edit another worker's workspace. Recover your own old
   work by copying needed artifacts with provenance; others' old work is read-only.
3. Implement the exact brief and verify its falsifier. Respect source pins, resource
   budgets and actual native/visual gates. Write a report containing commands, observed
   results, failures and source/artifact identities. Never invent game acceptance.
4. Prepare a PR against GhostDragonAlpha/Chimera, base astra/gait-capture. Put this
   bounded contribution under the card's pr_destination; include task ID, attempt ID,
   criteria_sha256 and verification evidence in the PR description. Reuse an available
   isolated source workspace or a small shared-object sparse checkout. Do not switch
   the live checkout, copy large assets, change main, or create a full clone per retry.
   Only explicitly scoped integration cards may change production paths.
5. Record the PR using startup's pr_submission_template and the actual full Git head:

```powershell
python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id YOUR_ID --submit-pr E:/PATH/submission.json
```

This immediately returns another card and its inbox. It does not mark the submitted
card complete. If GitHub REST access is unavailable, do not wait for a token: push the
branch if SSH allows it, then submit a durable **publication request**:

```powershell
python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id YOUR_ID --request-pr E:/PATH/request.json
```

The request JSON carries agent_id, task_id, attempt_id, criteria_sha256, the exact
branch name, the full 40-character head SHA, a checkpoint description,
writes_stopped=true, and artifact paths with raw SHA-256 hashes. The handoff records
the request durably on the card (idempotent per exact request identity; a new head
supersedes the worker's earlier open request while preserving it), moves the attempt
to PUBLICATION_REQUESTED, and immediately returns the next card — the worker is never
trapped waiting for the lead. When the lead acts on it, the lead creates the PR and
records it against the verified request identity (same task/attempt/agent/head/
criteria), which records the PR exactly like a worker submission. A request is
evidence-preserving handoff, never acceptance: it never sets REVIEW/DONE, never
creates a PR record, never resolves inbox messages, and never counts as a reviewed
merge. Workers can still revisit a requested card explicitly to address corrections.

## Task-ID inbox

Read messages whenever taking/revisiting a task and before updating its PR:

```powershell
python -B E:/PythonChimera/tools/monkey_campaign/kanban_cli.py inbox --task TASK_ID
```

To respond or ask a question, use `kanban_cli.py message --arguments FILE` with:

```json
{"task_id":"TASK_ID","author":"YOUR_ID","body":"What changed, exact evidence, or the precise question","reply_to":"optional existing message ID","pr_url":"optional project PR URL","head_sha":"optional exact PR head"}
```

Omit optional fields when unused. Message IDs and original bodies remain durable.
Worker replies do not erase or resolve a lead finding. Another agent sees the same
correction and may submit a competing fix. The lead resolves findings only after
reviewing evidence. PR head changes invalidate previous approval.

To leave unfinished work voluntarily, save a checkpoint and cease its writes, then run
startup with --park FILE containing agent_id, task_id, attempt_id, checkpoint and
writes_stopped=true. The next card is returned; no timer chooses for you. Old work stays
preserved. Resource limits still bound actual running agents and processes.

## Lead loop, only when the operator engages Astra

Use `kanban_cli.py status` to read the ten cards and submitted PRs. Check task inboxes.
Inspect PR source changes and reproduce appropriate tests/runtime/visual evidence.
Do not merge a second solution for a card already completed. If a merge occurred before
an interrupted board update, reconcile that existing merge before considering another PR.

Leave a review with `kanban_cli.py review --arguments FILE`:

```json
{"actor":"astra-codex","task_id":"TASK_ID","pr_url":"https://github.com/GhostDragonAlpha/Chimera/pull/123","head_sha":"40-character reviewed head","verdict":"CHANGES_REQUIRED","body":"Exact issue and acceptance needed for its correction","evidence_reference":"Actual reviewed source/test evidence","resolved_message_ids":[]}
```

CHANGES_REQUIRED automatically posts actionable feedback under the task ID. ACCEPTED
requires no unresolved applicable lead findings; use resolved_message_ids only for
findings whose fixes were actually verified. A review is not a merge.

Merge the approved exact head through GitHub's normal merge tool with its expected-head
check. Then run `kanban_cli.py accept-merge --arguments FILE` with actor, task_id and
pr_url. This command independently fetches the actual PR from GitHub and requires its
merged state, base branch and head to match the stored approval. Worker-supplied merged
flags are never accepted by this CLI. It stores both PR head and merge commit, closes
one card, and refills from eligible backlog. Retrying the winner is idempotent.

Add genuinely ready replacement work with `kanban_cli.py enqueue --arguments FILE`:
actor=astra-codex plus spec, using KANBAN_BACKLOG.json as the shape. Do not edit a live
card's criteria in place. Clarifications stay in its inbox; materially changed acceptance
requires an explicit new scoped card and preserved prior decision, not a silent hash change.

## Migration and limits

The board lives inside the EXISTING agent_slots.sqlite3 state; no new service or task
database is started. Existing work is imported as task references. The operator's
explicit stop permits clearing old model registrations while retaining their handoffs
and files. New Kanban operations disable legacy timer transitions. Old helpers remain
for preservation of historical records; they cannot create new exclusive leases.

The initial board is the nine previously issued tasks plus the existing R5 forest
review, totaling ten. Ten concrete dependent follow-ups are prepared in backlog.
Diagnostic PRs close their evidence card only; they never complete parent gameplay gates.
Role labels remain cooperative rules on this shared account, not authenticated identities.
No automatic model launch, agent restart, process kill, GPU action or lead wakeup occurs.
