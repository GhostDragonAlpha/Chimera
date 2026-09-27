# MAT2-P04 reconciliation — fleet resource and gaming contract (records profile)

Attempt `90d82bf414454bb7bf7cb4b38ee5dec8`, arrival
`arrival-b06f9edfa4f64d1b9834c47b943348fb`. Pinned attempt head
`c525b82c7c3ce0128565424764293a3c85811ab3` (branch-2). Card criteria
`967f4062200c2b0448f8436d507d99fcbb0989a0dcca5c39f16bb9379ddf7020`. Scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.
Profile: records (offline); numerical evidence required; nonvisual.

This card is a reconciliation, not a reimplementation. The done_when text of
MAT2-P04 is byte-identical to the closed legacy card ONT-P04 (sources:
registry revision 1166 assignment brief; `kanban_cli.py inbox --task ONT-P04`
returning `HISTORICAL_SCOPE_READ_ONLY`), and the legacy card closed DONE with
lead ACCEPTED reviews, final at merged PR #175. Per
`MATERIAL_PLAN_ADOPTION.md` ("Old evidence may satisfy unchanged clauses
after checking exact inputs, dependencies and validity; submit that
reconciliation as the new card's contribution instead of reimplementing
known-good code"), this document crosswalks each clause to current-revision
evidence and re-verified records. Old DONE does not silently become
MAT2-DONE: the fresh re-verification below is the qualification evidence for
review.

## Crosswalk (legacy -> current)

| Field | Legacy ONT-P04 | MAT2-P04 | Relation |
|---|---|---|---|
| done_when | identical text | identical text | byte-identical (observed in both registry card definitions) |
| criteria_sha256 | `6191e11c...` | `967f4062...` | different namespace criteria hashes; identical clause text |
| scope_sha256 | `01ea5cdd...` | `cb5475f8...` | different scope generations (M01-M12 addition) |
| dependency P03 | ONT-P03 DONE (PR #140) | MAT2-P03 DONE (PR #194, winner `250d6b243947eceb0abd93c6ffadea099a612bd7`, merge `13a943911da711a4dd24a450055ba0d1b1fe1d04`, merged 2026-09-27T09:36:08Z) | satisfied in both namespaces |
| pinned head | `c525b82c7c3ce0128565424764293a3c85811ab3` | same | unchanged qualified source revision |
| implementation | PR #175 MERGED, head `16390061951fc139bae539bda819cd8260d729c1`, merge `b7c4b79756d03aa26552273f6339495d419d19d5`, base `astra/gait-capture` (observed via `gh pr view 175`) | not duplicated; machine of record stays at `contributions/ONT-P04/` on the base line | carried forward with fresh re-verification |

## Clause-to-evidence map

### C1 — "Every launched job uses existing ownership/broker rules"

VERIFIED at the records profile.

- Ownership/admission law: pinned `tools/agent_fleet/control.py`, sha256
  `39ff01dc8a4192e04606ee9d87386780739e89c8a1774da48501a9545792f6b3`
  (archive-extraction convention; raw LF blob of the same file at the pinned
  head hashes `b540966ab06d86a02b226daefa8249d7e1379bf41c847ff707c629e3b9d3026c`;
  both bind the identical blob at `c525b82c`), re-verified in
  `reconciliation_checks.json` P1.control_py_frozen and
  P1.pinned_tree_52_files (52/52 manifest entries).
- Broker layer: pinned `tools/agent_fleet/review_handoff.py`
  (`ReviewHandoffControl`), guarded by pinned `test_layer_guard.py`.
- Fresh evidence this run: pinned suites `test_resources` 12/12,
  `test_resource_lifecycle` 12/12, `test_review_handoff` 13/13,
  `test_review_handoff_claim` 12/12, `test_run_queue` 8/8,
  `test_layer_guard` 8/8; carried probe `test_p04_contract` 17/17
  (byte-identical to PR #158 head `68290bec...`, sha256 `e9b8b62d...`).
- Catalog refs GOV-01/02/04/05, SYS-03 are addressed by these records
  (one owner per claim, authenticated admission, atomic all-or-nothing
  grants, never-replace-reservation) as qualified by the legacy receipt and
  re-run here.

### C2 — "admitted training may interrupt gaming and local inference through a verified supervisor handoff"

VERIFIED at the records profile (mechanism exists and is probe-verified;
live preemption is NOT executed or claimed).

- Machine of record: `tools/monkey_campaign/contributions/ONT-P04/gpu_handoff.py`
  sha256 `fd664b5f8182ea3466b37f9cdfe217950bcc6e91a4bb72c23c9ac6c33ad78dc0`,
  byte-identical at PR head `1639006195...` and merge commit `b7c4b797...`
  (P2, P3). `HandoffControl` is an additive subclass of the pinned
  `Control` (no rival GPU authority; one registry; every transition inside
  the controller's `BEGIN IMMEDIATE`; supervisor-only recover/clear).
  States `REQUESTED -> DRAINING -> READY -> TRAINING -> RESTORING ->
  AVAILABLE` plus `RECOVERY_HOLD` (never fabricates READY); inference
  admission gate stays closed on timeout; graceful game release bound to a
  registered identity (executable+pid+start_time); named model unloads with
  restoration configs; launch exactly once with a durable run id.
- Spec authority: `tools/monkey_campaign/COORDINATION.md` "GPU handoff:
  training can preempt gaming and local inference" with the operator
  override of 2026-09-24 (training may interrupt gaming; only the existing
  supervisor executes the handoff). GPU-A (authority/state machine) is the
  merged contribution; GPU-B/GPU-C/GPU-D remain open (below).
- Fresh evidence this run: `test_gpu_handoff` 28/28,
  `test_correction_fencing` 11/11 (evidence mutations fenced by live request
  owner/generation/instance or supervisor authority; registered restore
  configuration required — the lead CHANGES_REQUIRED findings on PR #158,
  resolved in PR #175 and re-verified here), `test_correction_records` 10/10.

### C3 — "already-running protected training retains ownership until confirmed release"

VERIFIED at the records profile.

- Law: owner/generation-bound evidenced release; `release_requires_observed_
  cessation` (timer/lease/silence never releases); supervisor-only
  `resource_clear` with actual drained-process evidence; `force_kill_refused`
  in every phase; crash recovery keeps a protected run protected and refuses
  replay (`already_launched`). Implemented by the merged machine plus the
  pinned controller release laws.
- Fresh evidence this run: pinned `test_resource_lifecycle` 12/12;
  `test_gpu_handoff` 28/28 (hold persists through observed cessation until
  the owner's evidenced release; protected run survives supervisor restart);
  `test_correction_fencing` 11/11 (foreign/stale mutation refusals).

## Planning observation — current receipt

Card observation: "Supervisor reported 8/8 passing; broker completion needs
current receipt."

- 8/8 referent: the only 8-test suites in the pinned fleet tree are
  `test_run_queue.py` and `test_layer_guard.py`; BOTH re-ran green 8/8 this
  attempt (`probe_run_results.json`, suites `pinned:agent_fleet:test_run_queue`
  and `referent:agent_fleet:test_layer_guard`), completing the prior
  attempt's referent reconciliation.
- Broker completion: the broker suites (`test_review_handoff` 13/13,
  `test_review_handoff_claim` 12/12, `test_layer_guard` 8/8) plus the full
  battery below are the requested current receipt, produced fresh at the
  pinned head inside this attempt (not copied from the legacy run).

## Executed verification (run 3, after frozen preregistration + 2 addenda)

- Preregistration frozen before any probe: `PREREGISTRATION.md`
  (sha256 `0d4a27fe0412c0f4d600e6b939f2a8ea2c171ad43217c74a8d19ee2d2e8c81c5`),
  addendum 1 (`32086bc84de3269a573d47fb882c90e27101d712cf5ae9e33ff02629fdb5a498`,
  carried-probe source), addendum 2
  (`ea852b07ef24103072e32ee28ceb06b96d006a22dc4a713fece321b7c5131720`,
  extraction convention + legacy-untracked fixture layout). Full hashes in
  `probe_run_results.json`.
- Battery (CPU-only `python -B`, isolated temporary registries, no GPU, no
  live registry, no model/game/process actions; E:/PythonChimera zero
  writes): 11 suites, 137/137 OK, exit 0 — pinned 12+12+13+12+8, referent 8,
  carried/merged probes 17+6+28+10+11. Exact commands, exit codes, unittest
  summaries and durations: `probe_run_results.json`.
- Identity checks (P1, P2, P3, P3b, P5, P6): all true in
  `reconciliation_checks.json`.
- Run ledger (failing-first, preserved in `first_run_failures/`):
  run 1 — runner crash before any probe (layout defect;
  `runner_run1_traceback.txt`); run 2 — P1 FAIL (raw-blob vs archive CRLF
  extraction convention; content identical) + `test_correction_records`
  7/10 (missing legacy-untracked fixture elements;
  `run2_probe_run_results.json`, `run2_reconciliation_checks.json`,
  `probe_test_correction_records.log`); run 3 — green. Dispositions in
  `PREREGISTRATION-ADDENDUM-2.md`; carried probes were never edited.

## Calculation contract C27 (applicability boundary)

C27 "Compute, memory and frame budgets" is an inventory contract whose
measurement deliverables belong to the runtime-facing cards (M08, R03). This
records-profile card adds the admission contract (which workload may run,
under which owner/broker rules) and claims no new frame-time, memory or VRAM
measurement. Contention invalidating benchmark claims (C27 verification)
stays with the owning runtime cards.

## Remaining gates (recorded, not waived)

1. GPU-B Bionic/inference adapter, GPU-C Windows game adapter, GPU-D
   independent recovery test — open implementation queue items
   (COORDINATION.md).
2. Live handoff qualification (live Bionic preservation/restore, real game
   safe-release, training across :00) — open with its owning records; no
   live preemption was performed or claimed by the legacy work or this
   attempt.
3. Lead publication and independent (non-author) review of this
   reconciliation; head_sha re-binding to the published PR head.

## Decision requests

None new. The training-over-gaming permission is an already-published
operator override (COORDINATION.md, 2026-09-24); no operator decision is
manufactured or assumed by this attempt. Any materially new scope belongs in
a new scoped card per KANBAN.md.
