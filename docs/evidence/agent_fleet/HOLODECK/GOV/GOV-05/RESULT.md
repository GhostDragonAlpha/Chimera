# RESULT — holodeck-gov-05 (gen 1)

Agent: subagent-worker-07 · slot 14 · worktree E:\ChimeraWork\slot-14 · branch
astra/tasks/holodeck-gov-05 · base 62b8e35757c71e31d621c26b32a7c52558905b02
(== astra/gait-capture tip at claim; provision verified HEAD==base, clean).
CPU only; no GPU/model/engine process; no controller resources; the live
service at 127.0.0.1:8099 was NEVER contacted (no socket, no HTTP).

## SOURCE IDENTITY (the deployed contract, read-only reference text)

- tools/agent_fleet/control.py, 839 lines, sha256
  7cee259b35a21ebe689feb5d77c8f2bb10b7125cd1ea9c3ac06e1cb6254bfa30
- tools/agent_fleet/publish.py, 128 lines, sha256
  ffd7d08c483d1450c0bf8cde2a38823c150f184b2d4fcd1f68a4233b762201bf
- tools/agent_fleet/review_handoff.py, 227 lines, sha256
  ad3674bd2e1f1a60a3762e44cd26578150b2c475b064af042a40bace30b51811
- All at git base 62b8e357 (== astra/gait-capture tip 62b8e357, the GOV-01
  integration merge).

## DELIVERABLES

- `reference/gov05_reference_model.py` — independent, stdlib-only reference
  model (546 lines — over the prereg's <300 target; disclosed in
  LIMITATIONS) of the INTENDED base contract for crash recovery + serialized
  publication: the atomic journal+state transaction boundary (with an armed
  kill raising `Crash` at the commit boundary), the recovery gates
  (fail/recover/review_requeue/provision_slot with bounded
  preserved_provisions), the serialized integration procedure
  (integration_request -> publish -> ack_integration), fast-forward-only
  content-addressed publication against a modeled remote, owner+generation
  (+ intended owner_instance) CAS, and journal REPLAY through the public
  gate chain (the card's event-sourcing mathematics as a real equivalence
  check, not a snapshot copy).
- `controls/run_controls.py` — executes preregistered R1-R6; every refusal
  recorded verbatim; every post-state assertion computed.
- `controls/trace_source.py` — read-only R7/R8 measurements of the deployed
  text at base (no network).
- `checks/r1_positive.txt` — R1 HOLDS 6/6 cases (legal chain to one PENDING
  request; FF push success; ack -> INTEGRATED content-addressed;
  crash-mid-transaction retry == never-crashed control by full 9-field
  snapshot equality; fail->recover with the provision record preserved and
  active fields cleared; publication idempotence: lost-ack re-publish ->
  already_integrated with NO second push, post-ack re-publish refused
  integration_already_acknowledged).
- `checks/r2_kill_mid_transaction.txt` — R2 HOLDS 5/5: staged change not
  visible; journal length unchanged; revision unchanged; retry == never-
  crashed twin; two kills + one success -> exactly one event, revision+1.
- `checks/r3_stale_epoch.txt` — R3 HOLDS 5/5: ack with pre-fail epoch and
  ack with leader-mismatched request both refused stale_integration_epoch
  (the two conjuncts of control.py:716's gate, isolated per case); second
  ack refused integration_already_acknowledged with the first commit
  preserved; integration_request while RUNNING refused not_in_review; head
  mismatch refused head_or_branch_mismatch. Post-states intact in all.
- `checks/r4_duplicate_publication.txt` — R4 HOLDS 5/5 (card falsifier
  clause 1 NOT reproduced): duplicate publish -> already_integrated with
  push_count unchanged; diverged base -> non_fast_forward_refused with the
  remote base UNCHANGED (unpublished newer work never overwritten);
  rewritten base -> base_rewritten_since_task_fork; tampered task branch ->
  task_head_mismatch_remote; master -> forbidden_branch. push_count == 0 in
  every refusal.
- `checks/r5_orphaned_ownership.txt` — R5 HOLDS 4/4 (card falsifier clause 2
  NOT reproduced): fail -> RECOVERY_HOLD at gen+1 with the orphan's
  old-generation mutation refused; recover with a held resource refused
  resources_still_held (state unchanged); recover on RUNNING refused
  not_recovery_hold; after recover+re-claim the orphan is refused at ANY
  stale generation and the slot's preserved history retains the old
  provision identity with active fields cleared.
- `checks/r6_replay_restart.txt` — R6 HOLDS 14/14 (card prediction): replay
  through the public gate chain from the fixture baseline reconstructs the
  committed registry exactly (2 tasks x 5 fields, revision, pending-request
  count), post-replay stale ack refused, post-replay diverged publish
  refused with the base still at the accepted head; replay's push_count
  witness 2 == the original's 2 (replay never republishes — the deployed
  already_integrated idempotence).
- `checks/r7_source_trace.txt` — the card prediction judged against the
  DEPLOYED text: 8/8 semantics present at base with measured line numbers:
  recover (control.py:629), _fail (134), _preserve_provision (152),
  review_requeue (722), integration_request (703), ack_integration (712),
  the atomic journal+state transaction (BEGIN 308 / event INSERT 350 /
  state UPDATE 351 / COMMIT 356 / ROLLBACK 359) with restart identity gates
  (74-75), and the publish.py gate chain (64, 73, 80, 94, 101, 120).
- `checks/r8_owner_instance_delta.txt` — the known-regression delta (below).
- `checks/fired_run_01/` — the RETAINED first-run outputs of the four rows
  that falsified before the fixes disclosed below (per the prereg verdict
  rule; never edited after the fact).
- `PREREG.md` — committed FIRST (53dff45d), untouched since.

## PREDICTION SCOREBOARD (card prediction / prereg rows)

| row | prediction (fixed in PREREG before any run) | verdict |
|-----|---------------------------------------------|---------|
| R1 | model accepts 6/6 legal sequences | HOLDS 6/6 |
| R2 | kill-mid-transaction corrupts nothing (5 assertions) | HOLDS 5/5 |
| R3 | stale-epoch/leader/identity publication paths all refused | HOLDS 5/5 |
| R4 | duplicate publication / overwrite paths all refused | HOLDS 5/5 |
| R5 | orphaned-ownership paths all refused | HOLDS 4/4 |
| R6 | replay reconstructs accepted task state (14 assertions) | HOLDS 14/14 |
| R7 | all 8 semantics present in deployed text with quotes | HOLDS 8/8 |
| R8 | interceptor bind free of owner_instance (rh==0); control.py count reported | HOLDS 2/2 (control.py measured 8 sites: 121,122,123,323,499,501,554,697) |

## CARD VERDICT (GOV-05 at catalogue digest b9d32319)

- CARD PREDICTION "Replay reconstructs accepted task state without
  overwriting unpublished work": SUPPORTED. In the reference model, replay
  re-executing the journal reconstructs the committed registry exactly (R6)
  and publication can never move the base backwards or sideways (R4). In the
  deployed source at base, recovery is realized as an ATOMIC committed-blob
  reload (state+events written in one BEGIN IMMEDIATE..COMMIT transaction,
  restart identity-checked) rather than literal replay-from-events — the
  same guarantee (accepted state survives; nothing partial is ever visible;
  unpublished/newer base work is protected by the FF-only publication gates)
  reached by atomicity instead of re-execution. That mapping is the lane's
  one card-vs-source divergence finding: the card's event-sourcing
  mathematics is present as the journal (events table, seq=revision) plus
  atomic commit, not as a replay engine.
- CARD FALSIFIER "Duplicate publication or orphaned ownership changes task
  truth": NOT reproduced by the intended contract. Every duplicate-
  publication path is refused or detected idempotent (already_integrated /
  integration_already_acknowledged / non_fast_forward_refused /
  task_head_mismatch_remote / base_rewritten_since_task_fork), and every
  orphaned-ownership write is refused by the generation-monotone CAS
  (stale_or_foreign_claim) through fail/recover/re-claim.
- MEASURED DEVIATION (recorded, not adopted as model truth): the live claim
  path is served by the review-handoff interceptor, whose bind
  (review_handoff.py:90-91) sets {owner, slot, state, generation} and omits
  owner_instance (measured occurrences in review_handoff.py: 0; in
  control.py: 8, sites 121/122/123/323/499/501/554/697). Consequence
  (static): for interceptor-claimed tasks owner_instance stays None, so the
  _task instance check (control.py:121-123) is skipped — the INTENDED
  per-instance fencing is inert on the live claim path while
  instance_fencing=='compat'. Matches the coordinator's known-regression
  note; fix in flight as PR #80 (in review at capture time). The reference
  model deliberately models the INTENDED binding (R4 asserts its
  persistence via the CAS gate).

## PRE-VERDICT FIRED RUN AND FIXES (disclosed; per prereg verdict rule)

The FIRST execution falsified four rows (R1, R2, R4, R6 — outputs retained
verbatim in `checks/fired_run_01/`). Root causes, all fixed before any
verdict was recorded; the deployed-source findings (R7/R8) were never
edited:

- MODEL (one API addition): the model's ops were atomic whole, so the kill
  window between BEGIN IMMEDIATE and COMMIT was not observable from the
  runner — R1(d)/R2 could not run as preregistered (first run recorded
  MISMATCH). Added `arm_crash()` + `Crash`: commit() discards the staged
  state and its journal event together and raises — the faithful model of
  process death at the SQLite commit boundary. No gate, refusal, or state
  change was altered; R3/R5/R7 passed unchanged before and after.
- RUNNER (assertion bugs): three refusals carry publish.py-style detail
  suffixes ('non_fast_forward_refused (base has diverged; rebase instead)',
  'task_head_mismatch_remote (remote task branch is ...)') and exact-equality
  assertions missed them; fixed by normalizing the named reason (details
  remain verbatim in the outputs). R8-b's bind-site check read only the
  first of the two source lines of the interceptor bind; fixed to read both.
- RUNNER (scenario bug, caught in the fired run): R6's second
  integration_request was issued by a non-leader actor and was correctly
  REFUSED by the model (not_leader_or_stale_epoch) — the scenario now
  requests through the leader, matching the deployed lead-only gate.
- PREREG expectation-text slip (disclosed, not a model defect): R5(d)
  predicted the post-recover re-claim generation as "old+2"; the deployed
  monotone chain (fail +1 control.py:140, recover +1 control.py:~646, claim
  +1 control.py:554) gives old+3. The model implements the deployed chain;
  the assertion asserts 4 (= old+3 from claim-time gen 1) and the note is
  recorded verbatim in checks/r5_orphaned_ownership.txt. The prereg file
  itself is NOT edited post-run.
- R1(f) prereg-wording refinement (disclosed in the check output):
  publish.py reads no registry state, so "publish again after integration"
  resolves to two witnesses, both asserted: the lost-ack re-publish ->
  already_integrated (no second push) and the post-ack re-publish ->
  integration_already_acknowledged (no second push).

## DYAD RECORD

NOT_APPLICABLE — source-only scope: no executed runtime behavior of the
deployed system was produced or altered; the deliverables are a reference
model, its in-process controls, and static source measurements. Per the
card's DYAD policy, reference-only scope records NOT_APPLICABLE with this
reason.

## REPRODUCTION

```
git -C <checkout> rev-parse 62b8e357            # base identity
cd docs/evidence/agent_fleet/HOLODECK/GOV/GOV-05
python controls/run_controls.py .               # rewrites checks/r1..r6 (R1-R6)
python controls/trace_source.py <repo-root> .   # rewrites checks/r7, r8 (R7-R8)
sha256sum ../../../../../tools/agent_fleet/control.py \
          ../../../../../tools/agent_fleet/publish.py \
          ../../../../../tools/agent_fleet/review_handoff.py   # identity
```
(The relative depth above is from GOV-05/ to repo root: five levels.)
R7/R8 quotes re-derivable with `sed -n '<line>p'` at the recorded numbers.

## LIMITATIONS

- The model covers the crash-recovery + publication surface only (the card's
  statement scope): claim/CAS/persistence, fail/recover/review_requeue/
  provision_slot, integration_request/publish/ack. It does not model
  resources scheduling, queues beyond the drop-on-recovery semantics,
  elections beyond the leader/epoch bump, or the catalogue plane.
- Persistence is modeled as whole-registry snapshots with a staged-commit
  boundary; the deployed controller uses SQLite BEGIN IMMEDIATE per op.
  The modeled guarantee (committed state survives; a kill leaves no partial
  state and no torn journal entry) matches by construction; SQLite's
  durability under POWER loss is NOT modeled.
- Replay is re-execution through the model's public gates; the deployed
  recovery is blob-reload, not replay (see CARD VERDICT — the mapping is
  the finding, not a defect).
- Concurrency is modeled as sequential calls; the deployed serialization
  guarantee is cited from source (BEGIN IMMEDIATE + ROLLBACK), not stress-
  tested. The remote is a linear-history stand-in; git's real merge-base
  semantics are richer, but the FF-only gate's contract is faithfully
  reduced.
- The model is 546 lines, over the prereg's <300-line target (the surface —
  transaction boundary, remote DAG, replay, fixtures — exceeded the
  estimate). Disclosed; no threshold of the CARD is affected.
- R8 is a static textual measurement of one base revision; it does not
  observe the live service and makes no claim about PR #80's content.

## SHIP RECORD

- Commit chain: 53dff45d (PREREG, no actuals) -> artifact commit(s) -> pushed
  HEAD recorded in the controller submit_review event; PR into
  astra/gait-capture; pushed no-force.
- Files changed: docs/evidence/agent_fleet/HOLODECK/GOV/GOV-05/** only
  (*.md / *.py / *.txt; never *.log).
