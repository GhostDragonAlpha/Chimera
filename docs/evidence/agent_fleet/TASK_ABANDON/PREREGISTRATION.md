# fleet-task-abandon-01 preregistration (2026-09-11, subagent-worker-04)

Task `fleet-task-abandon-01` generation 1, slot 3, worktree
`E:\ChimeraWork\slot-03`, base `5199d9c3015f6840b12186f34c3e0c2fd5d7b0a4`
(= merge of PR #60; verified worktree HEAD == record base, clean). This file
is committed BEFORE any implementation, measurement, or test run and names
no measured actuals. It necessarily forward-references
`tools/agent_fleet/test_task_abandon.py`, which does not exist yet by
construction (registration precedes code); the reference is satisfied by
the immediately following implementation commit. It closes the two controller gaps recorded in the
2026-09-11 third-wave Master amendment (candidate `fleet-task-abandon-01`):
(1) no op retires a stale READY task; (2) no supervisor op retires an
unprovisionable RUNNING claim without revoking the owning agent's session.

## STATEMENT

A supervisor can retire a stale READY task, or an unprovisionable RUNNING
claim, through a named, audited, supervisor-only controller op — with
preservation/drain attestations where a claim is being retired — and no op
in this task ever revokes an agent session or touches the filesystem. The
new terminal state `ABANDONED` is retired, not active: it blocks claiming
and satisfies no dependency, but holds no slot, holds no write scope, and
does not block catalogue re-proposal of its card.

## DERIVATION (why these exact semantics; no numbers chosen by taste)

The controller already contains the pattern this task needs; both ops are
compositions of existing machinery, not new mechanisms:

- `task_abandon` = the `recover` state surgery applied to a READY task
  (which holds no slot, no provision and no resources by invariant), minus
  requeue: the ONLY new thing is the terminal state, so the op is one
  guarded state transition plus an audit record.
- `claim_abandon` = `recover` minus the failure premise (`_fail` /
  RECOVERY_HOLD), because the falsifier forbids session revocation. It
  keeps recover's exact refusal vocabulary (`resources_still_held`), its
  evidence-in-checkpoint convention, its queue-drops, and routes slot
  freeing through the existing `_preserve_provision` machinery exactly as
  `recover`, `slot_rebind`, `release_slot` and `release_review_slot`
  already do.
- ABANDONED coherence follows from one rule applied uniformly: ABANDONED is
  added to NO active-state tuple (`RUNNING/BLOCKED/REVIEW/RECOVERY_HOLD`).
  That single omission makes claim eligibility, capacity accounting, the
  write-scope-conflict predicate, the `_fail`/`yield` recovery sweep and
  the stale-claim queue drop all treat it as inactive, and makes the
  dependency gate (`state == 'INTEGRATED'`) treat it as NOT satisfying a
  dependency. The ONE place that enumerates by complement
  (`catalogue_next` builds `live` as "not INTEGRATED") needs an explicit
  exclusion, otherwise a retired task would block re-proposing its card
  forever — a dead-end that contradicts "retire".

## PREDICTION

1. `task_abandon(task, reason, evidence)` called by SUPERVISOR on a READY
   task marks it `ABANDONED`, stores `{reason, evidence, actor, revision}`
   on the task record, and appends an audit event (kind `task_abandon`)
   carrying the reason; the result reports `filesystem_touched: False`.
2. `task_abandon` refusals (named, revision unchanged on refusal):
   `supervisor_only` for any agent or lead actor; `unknown_task`;
   `task_not_ready` for a task in RUNNING, BLOCKED, REVIEW, RECOVERY_HOLD,
   INTEGRATED, or already ABANDONED; `missing_abandon_reason` /
   `missing_abandon_evidence` for blank attestations.
3. `claim_abandon(task, preservation_evidence, drain_evidence)` called by
   SUPERVISOR on a RUNNING task whose slot was NEVER provisioned: returns
   the task to READY at generation+1 with `owner=None`, `slot=None`,
   `owner_instance=None`, the combined attestations stored as the task
   checkpoint, frees the slot through `_preserve_provision` (no preserved
   record is created because none was active), drops the task's queued
   resource requests (`dropped_reason='claim_abandoned'`), and does NOT
   revoke the owner session (the owner agent remains `alive` and retains
   remaining claim capacity).
4. `claim_abandon` refusals: `supervisor_only`; `unknown_task`;
   `task_not_running` for any non-RUNNING state; `task_has_no_slot`;
   `slot_binding_mismatch`; `provision_active_use_slot_rebind` when the
   slot's provision is ACTIVE (naming `slot_rebind` as the correct op);
   `resources_still_held` (mirrors `recover`); missing preservation or
   drain attestation. No refusal path mutates state (revision unchanged).
5. ABANDONED coherence: a claim of an ABANDONED task is refused
   (`task_not_ready`); a task depending on an ABANDONED task is refused at
   claim (`dependencies_not_integrated`); a new task whose scopes overlap
   an ABANDONED task's scopes claims WITHOUT `write_scope_conflict`; the
   ABANDONED task no longer appears in `catalogue_next`'s `live_tasks` and
   its card becomes a PROPOSED candidate again; re-creating a task with an
   ABANDONED id is refused (`invalid_or_duplicate_task`) — the id is
   retired permanently and the audit history is preserved, never rewritten.
6. Reopen invariants: after `claim_abandon` the previous owner's stale
   generation is refused for owner ops (`stale_or_foreign_claim`); any
   qualified agent can re-claim the READY task and the generation advances
   again; a worker-run-queue surface reading controller state never picks
   up an ABANDONED task (it enumerates READY/active tuples only — audited,
   no change required).
7. The `yield` → `recover` path still works unchanged: yielding a claim
   still ends the session (`alive=False`), holds the task at
   RECOVERY_HOLD, and supervisor `recover` still returns it to READY at
   generation+1 (the old path stays available; no longer mandatory).
8. The audit trail is append-only under both ops: event sequences strictly
   increase, prior events are byte-identical after the ops run, and no
   token material appears in state, snapshot or events.
9. The full fleet suite from the repo root
   (`python -m unittest discover -s tools/agent_fleet -p 'test_*.py'`)
   is green with the new `test_task_abandon.py` included; the exact count
   is reported with provenance whatever it is (baseline count measured at
   base AFTER this registration, recorded in the evidence dir).

## FALSIFIER

A live claim retired without both attestations; any agent session's
`alive` flag flipped false by `task_abandon` or `claim_abandon`; any
filesystem write from either op; audit history lost or rewritten; an
ABANDONED task claimable, satisfying a dependency, blocking a
non-overlapping claim's scope, or blocking catalogue re-proposal; an
existing gate weakened or an existing assertion removed; or the
yield-recover path broken. Any of these and the task FAILS regardless of
test count.

## Method notes (binding on the run)

- Tests are isolated: a temp registry root per test, exactly the
  `test_control.py` harness pattern (enroll/qualify/elect in `setUp`,
  `TemporaryDirectory` torn down in `tearDown`); no live service, no
  deployed store, no real slots.
- Scope discipline: only `tools/agent_fleet/control.py`,
  `tools/agent_fleet/test_task_abandon.py`, `docs/THE_AGENT_FLEET.md`
  (dated append) and `docs/evidence/agent_fleet/TASK_ABANDON/` change.
  `review_handoff.py`'s duplicated claim predicate needs NO change — the
  single-omission rule keeps it coherent (verified by the scope-freedom and
  dependency tests running through the production `Control` subclass used
  by the service, where applicable) — it is OUT of scope and untouched.
- Evidence filenames `*.txt` only (the `*.log` gitignore trap, twice
  bitten this wave per the Master followup ledger).
- Deployment note (recorded, not executed here): `control.py` is also the
  deployed service source; this change reaches the live controller only
  through a later controlled transition. No live-service mutation in this
  task.
- Supervisor steps AFTER review (the LEAD's, not in this PR): use the new
  ops to retire the documented stale records (fleet-run-queue-01,
  fleet-orient-continuation-01, engine-vulkan-cleanup-01,
  window-capture-ownership-01, fleet-controller-upgrade-01).
