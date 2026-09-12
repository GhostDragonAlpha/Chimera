# PREREG — holodeck-gov-05 (gen 1)

- Agent: subagent-worker-07. Slot 14, worktree E:\ChimeraWork\slot-14, branch
  astra/tasks/holodeck-gov-05, base 62b8e35757c71e31d621c26b32a7c52558905b02
  (== astra/gait-capture tip at claim; provision verified HEAD==base, clean).
- Admitted from DRAFT-holodeck-gov-05 (catalogue card GOV-05, catalogue digest
  b9d32319..., content_sha256 d0f492ac...); dependency holodeck-gov-01
  INTEGRATED (PR #77) — its evidence pattern (reference/ + controls/ + checks/)
  is the precedent this lane follows.
- SOURCE-ONLY lane: the DEPLOYED contract is studied from the source text at
  base (tools/agent_fleet/control.py 839 lines sha256
  7cee259b35a21ebe689feb5d77c8f2bb10b7125cd1ea9c3ac06e1cb6254bfa30;
  tools/agent_fleet/publish.py 128 lines sha256
  ffd7d08c483d1450c0bf8cde2a38823c150f184b2d4fcd1f68a4233b762201bf;
  tools/agent_fleet/review_handoff.py 227 lines sha256
  ad3674bd2e1f1a60a3762e44cd26578150b2c475b064af042a40bace30b51811).
  The live service at 127.0.0.1:8099 is NEVER contacted; no port, socket or
  HTTP connection to the control plane is opened. DYAD: NOT_APPLICABLE —
  source-only scope, reason recorded in RESULT.md.
- This commit contains the PREREG ONLY. No reference model, no controls, no
  results, no measured actuals.

## CARD MEMBRANE (quoted from the card / task packet)

- CARD STATEMENT: Recovery journal and serialized integration procedure.
- CARD PREDICTION: Replay reconstructs accepted task state without overwriting
  unpublished work.
- CARD FALSIFIER (named BEFORE the run, for both the reference model and the
  source trace): **Duplicate publication or orphaned ownership changes task
  truth.**
- CARD MATHEMATICS: event sourcing; content addressing; idempotence.

## REFERENCE MODEL CONTRACT (fixed before implementation)

A self-contained stdlib-only module (`reference/gov05_reference_model.py`,
inside this evidence scope) implementing the INTENDED base contract for crash
recovery + publication, NOT the known live interceptor deviation:

- **Journal + committed-blob persistence boundary** (the card's event-sourcing
  math as the deployed contract realizes it): every mutating op builds its
  full next-state in a staging copy; `commit()` appends exactly ONE journal
  event (`seq = revision+1`, the deployed event INSERT at control.py:350 has
  seq = the bumped revision) and atomically swaps staged state in with the
  event — the model of the single SQLite transaction (BEGIN IMMEDIATE
  control.py:308; event INSERT 350; state UPDATE 351; COMMIT 356; ROLLBACK
  358-360). `crash()` discards staging AND the not-yet-appended event: a crash
  mid-transaction can leave neither partial state nor a torn journal entry.
  `load(blob)` = the deployed restart reload (control.py:65-76, committed blob
  is authoritative, identity/config checked). `replay(journal)` reconstructs
  state by folding the journal from the empty registry — the card's event
  sourcing — and must equal the committed state (this is the INTENDED
  mathematics; where the deployed text realizes recovery by atomic
  blob-reload instead of replay, that is recorded as a measured mapping in
  the source trace, not silently reconciled).
- **Crash-recovery gates** (control.py at base): `fail()` per _fail (134-149):
  owned RUNNING/BLOCKED/REVIEW -> RECOVERY_HOLD with generation+1, queue
  entries dropped `owner_failed`, resource ownership INTENTIONALLY retained,
  leader re-election. `recover()` per recover (631-648): supervisor-only
  (`preservation_observer_required`), RECOVERY_HOLD-only
  (`not_recovery_hold`), refuses `resources_still_held`, queue entries dropped
  `recovered_generation`, checkpoint = preservation evidence, provision
  retired through preserve-provision (152-172: bounded preserved_provisions
  history, active fields cleared so no later claimant inherits source
  authority), slot freed, task READY ownerless at generation+1.
  `review_requeue()` per 724-735: lead+epoch-only, REVIEW -> RUNNING, head
  cleared (review void), generation+1, worktree preserved.
- **Serialized integration procedure**: `integration_request()` per 695-712:
  lead+epoch-only, REVIEW-only (`not_in_review`), head+branch identity
  (`head_or_branch_mismatch`), exactly ONE request per publication, state
  PENDING_EXTERNAL_BROKER, carrying expected_base sha + epoch + leader.
  `publish()` per publish.py:50-124: fetch-verify, content-addressed identity
  (`task_head_mismatch_remote` :73-74), interrupted-integration reconciliation
  (`already_integrated` :79-83 — a push that succeeded but was never
  acknowledged is DETECTED, never repeated), `base_rewritten_since_task_fork`
  :92-94, fast-forward-only (`non_fast_forward_refused` :99-102), never master
  (`forbidden_branch` :63-64), post-push re-verification
  (`verification_failed_after_push` :119-121). `ack()` per ack_integration
  (713-721): trusted-publisher-only, `stale_integration_epoch` (epoch+leader
  binding), `integration_already_acknowledged` (idempotence),
  `review_changed`, wrong-base refusal, -> INTEGRATED with content-addressed
  integration.commit.
- **Orphaned-ownership protection**: the owner+generation CAS gate
  (`stale_or_foreign_claim`, control.py:116-124, with the INTENDED
  owner_instance binding) survives fail/recover generation bumps, so an
  orphaned owner cannot write task truth after recovery.

## PREREGISTERED NUMBERS / THRESHOLDS (stated before ANY implementation test)

Verdict rule: each R row must reach its full N/N; any miss = that row's
falsifier FIRED and the miss is REPORTED verbatim, never patched around, no
threshold widened. For the reference model a fired card falsifier means the
MODEL (or my reading of the semantics) is wrong: the model is fixed, the
correction disclosed in RESULT.md, and the fired run's output retained; the
DEPLOYED-source findings are never edited.

- **R1 positive controls** (model must ACCEPT): N=6/6 —
  (a) claim -> checkpoint -> submit_review(head) -> integration_request legal
  chain, one PENDING request;
  (b) publish FF push success: remote base becomes exactly the task head,
  push_count 1;
  (c) ack -> INTEGRATED, integration.commit recorded (content address);
  (d) crash mid-transaction then retry: after crash the state equals the last
  committed state; the retried op succeeds and the final state equals an
  identical never-crashed run (determinism);
  (e) fail -> recover cycle: READY at gen+1, ownerless, slot freed, provision
  record RETAINED in preserved history with its provision_task/generation
  while active fields are cleared;
  (f) publish again after integration -> `already_integrated`, push_count
  still 1 (idempotent, no duplicate).
- **R2 kill-mid-transaction** (negative — no corruption, no torn journal):
  N=5/5 — crash after staging, before commit, asserted on a registry holding
  2 owned tasks + 1 pending integration request:
  (a) staged state change NOT visible (all compared fields equal last
  committed);
  (b) journal length unchanged (no torn/partial event);
  (c) revision unchanged;
  (d) retry after crash succeeds and the resulting state is field-identical
  to a control run that never crashed;
  (e) two crashes then one success -> exactly one new journal event,
  revision+1 (no double-append).
- **R3 stale-epoch / serialized-integration refusals** (negative): N=5/5 —
  (a) ack with the pre-fail epoch -> `stale_integration_epoch`;
  (b) ack naming a different leader -> `stale_integration_epoch`;
  (c) second ack on an acknowledged request -> `integration_already_acknowledged`;
  (d) integration_request while RUNNING -> `not_in_review`;
  (e) integration_request with a head that differs from the task's recorded
  head -> `head_or_branch_mismatch`.
  Post-state assertions in every case: request state unchanged, task state
  unchanged, remote base ref unchanged.
- **R4 duplicate publication / overwrite protection** (card falsifier clause
  1 — model must REJECT): N=5/5, each with a push_count assertion (refusals
  leave push_count unchanged; the remote base ref is NEVER moved backwards or
  sideways) —
  (a) publish when remote base already contains the task head ->
  `already_integrated`, push_count unchanged;
  (b) publish when the remote base legitimately advanced past the task's base
  (unpublished newer work landed) -> `non_fast_forward_refused`, remote base
  UNCHANGED;
  (c) remote base rewritten so the task's recorded base is no longer an
  ancestor -> `base_rewritten_since_task_fork`;
  (d) remote task branch moved off the registry head ->
  `task_head_mismatch_remote`;
  (e) publication targeting `master` -> `forbidden_branch`.
- **R5 orphaned ownership** (card falsifier clause 2 — model must REJECT):
  N=4/4 —
  (a) fail -> owned tasks RECOVERY_HOLD at generation+1; the old owner's
  mutation at the pre-fail generation refused `stale_or_foreign_claim`;
  (b) recover while a resource is still held -> `resources_still_held`, task
  state UNCHANGED (no recovery through held resources);
  (c) recover on a RUNNING (non-HOLD) task -> `not_recovery_hold`, unchanged;
  (d) after recover + re-claim by another agent: the orphan's old generation
  refused, the new claimant's generation is old+2, and the slot's preserved
  history holds exactly the old provision record (active fields cleared —
  no source-authority inheritance).
- **R6 replay/restart reconstruction** (card prediction "Replay reconstructs
  accepted task state without overwriting unpublished work"): N=13/13 —
  replay(journal) from empty equals the committed state on 2 tasks x 5 fields
  (state, owner, generation, slot, head) = 10, + revision (11), + pending
  request state (12); post-replay stale ack still refused (13) and the
  replayed registry still refuses to overwrite a diverged remote base (14th
  assertion folded into R6: threshold stated as 14/14 total).
- **R7 deployed-source trace** (the card prediction judged against the
  DEPLOYED text at base 62b8e357): threshold 8/8 named semantics found with
  exact file:line quotes —
  (1) recover gates (control.py:631-648); (2) _fail RECOVERY_HOLD + gen bump
  (134-149); (3) _preserve_provision bounded history + field clearing
  (152-172); (4) review_requeue (724-735); (5) integration_request identity +
  PENDING_EXTERNAL_BROKER (695-712); (6) ack_integration epoch/idempotence/
  INTEGRATED (713-721); (7) the atomic journal+state transaction (308, 350,
  351, 356, 358-360) and restart identity checks (74-76); (8) publish.py gate
  chain (63-64, 73-74, 79-83, 92-94, 99-102, 119-121).
- **R8 known-regression delta** (recorded finding, NOT adopted as the model's
  truth): the live claim path is served by the review-handoff interceptor
  whose bind (review_handoff.py:90-91) sets {owner, slot, state, generation}
  and omits owner_instance. Preregistered textual prediction at this base:
  owner_instance occurrences in review_handoff.py == 0 (measured at
  prereg time from the base text; the run re-measures and reports), while
  control.py carries > 0 (exact count measured and reported — prereg-time
  count 8, e.g. claim bind 553-554, _task CAS 121-123, yield guard ~497-501,
  call() setdefault ~328). Consequence: for interceptor-claimed tasks
  owner_instance stays None so the INTENDED instance fencing is inert on the
  live claim path while instance_fencing=='compat'; fix in flight as PR #80
  (in review at capture time). The reference model deliberately models the
  INTENDED binding. If the delta measures differently at this base, that is
  reported as a surprise finding, never silently reconciled.

## METHOD

1. Write the reference model (evidence-scoped, stdlib-only, target <300
   lines) implementing the contract above.
2. `controls/run_controls.py` (stdlib-only) executes R1-R6 against the model
   in one process and writes `checks/r1_positive.txt`,
   `checks/r2_kill_mid_transaction.txt`, `checks/r3_stale_epoch.txt`,
   `checks/r4_duplicate_publication.txt`, `checks/r5_orphaned_ownership.txt`,
   `checks/r6_replay_restart.txt` — every refusal verbatim, every post-state
   assertion computed, verdicts computed never asserted.
3. R7/R8 measured from the source text at base by a read-only script:
   `checks/r7_source_trace.txt` (quoted lines),
   `checks/r8_owner_instance_delta.txt` (counts + quoted bind sites).
4. RESULT.md: scoreboard, reproduction commands, source identity (git sha +
   file sha256), limitations, DYAD NOT_APPLICABLE record, ship record.
5. Commit chain on astra/tasks/holodeck-gov-05 (trailer
   `Agent: subagent-worker-07`), push no-force, PR into astra/gait-capture,
   submit_review with exact HEAD and generation.

## SCOPE

docs/evidence/agent_fleet/HOLODECK/GOV/GOV-05 only. Evidence files *.txt / *.md
(never *.log). No code outside the evidence scope is written or modified; the
deployed source is read-only; the live control plane (127.0.0.1:8099, the
control deployment dir's runtime state) is never contacted or mutated.
