# MAT2-P04 preregistration — reconciliation of the fleet resource/gaming contract (records profile)

Frozen before any probe run of this attempt. Task `MAT2-P04`, attempt
`90d82bf414454bb7bf7cb4b38ee5dec8`, arrival
`arrival-b06f9edfa4f64d1b9834c47b943348fb`, card criteria
`967f4062200c2b0448f8436d507d99fcbb0989a0dcca5c39f16bb9379ddf7020`, scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`, pinned
attempt head `c525b82c7c3ce0128565424764293a3c85811ab3` (branch-2), profile
`records` (offline), calculation contract `C27` (inventory only). Dependency
`MAT2-P03` is DONE (registry revision 1166 board: PR #194, winner head
`250d6b243947eceb0abd93c6ffadea099a612bd7`, merge `13a943911da711a4dd24a450055ba0d1b1fe1d04`,
merged 2026-09-27T09:36:08Z).

## Reconcile-phase observations (read-only, pre-freeze, with sources)

1. The `done_when` text of MAT2-P04 is byte-identical to the closed legacy
   card `ONT-P04` (sources: registry revision 1166 assignment brief returned
   by `worker_start.py --task MAT2-P04`; `kanban_cli.py inbox --task ONT-P04`
   returning `HISTORICAL_SCOPE_READ_ONLY`). Same three clauses, same
   calculation id `C27`, same catalog refs GOV-01/02/04/05, SYS-03.
2. The legacy card ONT-P04 is DONE: review history shows lead ACCEPTED at PR
   #158 head `68290bec...`, then CHANGES_REQUIRED (foreign enrolled gamer
   could mutate training drain evidence; unload accepted a different
   restoration config), then ACCEPTED at PR #175 head
   `16390061951fc139bae539bda819cd8260d729c1` ("evidence mutations fenced +
   registered restore config required", 129/129 battery x2, 11 failing-first
   regressions preserved).
3. PR #175 is MERGED on GitHub (observed via `gh pr view 175` at reconcile
   time): base `astra/gait-capture`, head `16390061951fc139bae539bda819cd8260d729c1`,
   merge commit `b7c4b79756d03aa26552273f6339495d419d19d5`, 20 changed files
   under `tools/monkey_campaign/contributions/ONT-P04/`.
4. This attempt's pinned head equals the legacy attempts' pinned head
   `c525b82c7c3ce0128565424764293a3c85811ab3` (checkout_identity.json; legacy
   receipts), so the qualified source revision is unchanged.
5. The planning observation "Supervisor reported 8/8 passing; broker
   completion needs current receipt" was reconciled by the prior attempt to
   the only 8-test suites in the pinned fleet tree, `test_run_queue.py` and
   `test_layer_guard.py`; this attempt re-runs BOTH to produce the requested
   current receipt.

## Frozen statement

Per MATERIAL_PLAN_ADOPTION.md ("Old evidence may satisfy unchanged clauses
after checking exact inputs, dependencies and validity; submit that
reconciliation as the new card's contribution instead of reimplementing
known-good code"), this attempt contributes RECONCILIATION, not
reimplementation: a crosswalk of the three done_when clauses to the
lead-accepted merged implementation, plus fresh re-verification at the pinned
head. No production path is modified; no new handoff implementation is
authored; no live GPU/model/game/process action is performed or claimed.

Clause map (full citations in RECONCILIATION.md):

- C1 "Every launched job uses existing ownership/broker rules" — pinned
  `tools/agent_fleet/control.py` (authenticated claim/admission, atomic
  all-or-nothing grants, never-replace-reservation) plus the
  `review_handoff.py` ReviewHandoffControl broker layer.
- C2 "admitted training may interrupt gaming and local inference through a
  verified supervisor handoff" — merged `contributions/ONT-P04/gpu_handoff.py`
  `HandoffControl`: REQUESTED -> DRAINING -> READY -> TRAINING -> RESTORING ->
  AVAILABLE plus RECOVERY_HOLD (never fabricates READY), additive subclass of
  the pinned controller under its existing authentication; supervisor-only
  recover/clear; inference admission gate stays closed on timeout.
- C3 "already-running protected training retains ownership until confirmed
  release" — owner/generation-bound evidenced release; timer/lease/silence
  never releases (`release_requires_observed_cessation`); supervisor
  `resource_clear` requires actual drained-process evidence; force kill
  refused in every phase.

## Frozen prediction

P1 The 52-file pinned tree extracted from this attempt's HEAD matches every
   entry of the merged `pinned_file_hashes.json` (whose whole-file sha256 is
   `c79f248b5f75f38f2ae04f3b43de988801ae06ddfc1f8e1aee45c2125fbc0753`); the
   pinned `control.py` sha256 begins `39ff01dc`.
P2 All 20 merged contribution blobs at merge commit `b7c4b797...` are
   byte-identical to the same paths at PR head `1639006195...`.
P3 The probe suites executed by this attempt are the merged blobs
   byte-unmodified; their sha256 values are recorded in
   `reconciliation_checks.json` and equal the merged blob hashes.
P4 The full battery runs green at the pinned head: pinned suites
   12+12+13+12+8; carried/merged probes 17+6+28+10+11 = 129/129 OK, exit 0;
   the two supervisor-referent suites `test_run_queue` (8) and
   `test_layer_guard` (8) also run green, for 145 recorded OK in total.
P5 The untracked specification receipt
   `GPU_HANDOFF_PUBLICATION_RECEIPT.untracked.json`, copied byte-exact with
   provenance from the final legacy attempt workspace
   `kanban-attempts/ONT-P04/06792d79c3704ac29df519055aabbc57/pinned/`,
   hashes identically at source and at the verification layout.

Any P1-P5 violation is recorded as a failure with disposition in
`reconciliation_checks.json` / `probe_run_results.json`; a green-after-fix
rerun preserves the failing first run's captured output. Failing-first
discipline applies to this attempt's own new runner: any first-run runner
defect is preserved (`first_run_failures/`) and fixed in the RUNNER only,
never in the carried probes.

## Frozen falsifier (card-level)

"Missing identities or a claimed pass unsupported by records fails; a
screenshot is not a substitute." Operationalized here: every clause evidence
carries artifact path + raw sha256 + source revision; every suite result
carries exact command, exit code and unittest summary; a pass not present as
a record in `probe_run_results.json` is not a pass; any carried artifact
without a recorded hash fails the reconciliation claim.

## Frozen procedure (post-freeze, in order)

1. Build the verification layout inside this attempt workspace only:
   `reference/ONT-P04/` receives the 20 merged blobs from merge commit
   `b7c4b797...` via `git show`; `reference/ONT-P04/pinned/` receives the
   52-file tree via `git show HEAD:<path>` for each path keyed in the merged
   `pinned_file_hashes.json`, plus the provenance-copied untracked receipt.
2. Identity checks P1/P2/P3/P5 -> `reconciliation_checks.json`.
3. Battery via this attempt's `run_reconciliation_probes.py` (commands
   identical in shape to the merged runner: `python -B -m unittest` with
   per-suite capture, 600 s timeout) -> `probe_run_results.json`.
4. Constraints: CPU-only `python -B`; no GPU action; no model load/unload; no
   game start/stop; no process beyond the test processes; fixtures use
   isolated temporary registries (loopback-only servers exist only inside
   pinned suites); zero writes outside this attempt workspace, in particular
   zero writes to `E:/PythonChimera`.

## Remaining gates (recorded, not silently waived)

- GPU-B (Bionic/inference adapter), GPU-C (Windows game adapter), GPU-D
  (independent recovery test) and the live handoff qualification remain open
  with their owning records (COORDINATION.md implementation queue); this
  records-profile card does not close them and claims no live preemption.
- C27 "Compute, memory and frame budgets" stays an inventory contract for the
  runtime-facing cards (M08, R03); no new numerical runtime measurement is
  claimed here.
- Decision requests: none new. The training-over-gaming operator override is
  already published (COORDINATION.md, operator override 2026-09-24); this
  attempt manufactures no operator decision.

## Applicability boundary

Profile `records` (offline): visual verification does not apply (profile
`nonvisual_reason`: "A source/contract/measurement task whose truth requires
records or numerical oracles, not a 3D image"). Resource-blocked live phases
remain pending and are never passed by a fixture. Integration checkpoints are
downstream milestones, not prerequisites of this card.
