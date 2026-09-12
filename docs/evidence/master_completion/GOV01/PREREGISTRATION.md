# GOV-01 evidence reconciliation — preregistration

Written BEFORE any reconciliation execution, by `subagent-worker-01`, task
`gov01-evidence-reconcile-01`, generation 7, slot 2. Docs-only task: no
runtime, DYAD, GPU or engine process is run, and no simulation validation is
claimed (that is WHY the runtime tools are unused, not an oversight). No
controller/catalogue code, Master list or live claims are edited; the
master-catalogue lane retains that ownership.

## Bound identity (captured before execution)

- Worktree: `E:\ChimeraWork\slot-02`, branch `astra/tasks/gov01-evidence-reconcile-01`
- Task base (controller packet): `7d3601e7d9e04019cc3794ccf0a9738627c9fd71`
  (verified ancestor of the worktree head)
- Worktree head at preregistration: `d012b4b12ea2224d6b5669974776047238b76755`
- Working tree clean at start.
- Source identity (SHA-256, tracked files as checked in): see `BINDING.json`
  written alongside this file; the same hashes are re-verified after the run.

## Packet theory (restated, unchanged)

- STATEMENT: checked-in source at the exact base rejects overlapping
  claims/stale generations and preserves assignments across isolated restart;
  provenance and publication limits can be traced to executed evidence.
- PREDICTION: existing targeted isolated Windows controller tests reproduce;
  each GOV-01 clause maps to exact source/test/evidence or explicitly remains
  OPEN.
- FALSIFIER (any one fails the reconciliation): conflicting scope accepted;
  stale state replacing a newer claim; restart losing a claim; source/evidence
  mismatch; an unsupported acceptance claim in this matrix.

## Roadmap clauses being reconciled (docs/roadmap/holodeck_tasks.json, GOV-01)

Card GOV-01 "Authoritative ledger and ownership" declares four deliverables:

1. Canonical task IDs, claims, owners and publication queue.
2. Independent reference/benchmark and executed negative controls appropriate
   to this scope.
3. Reproduction commands, source identity, preserved evidence and limitations.
4. Integration contract and full autonomous handoff.

Card prediction: "Conflicting claims are rejected and active assignments
survive restart". Card falsifier: "Two agents own the same write scope or
stale state replaces a newer claim".

## Exact commands (run only after this file exists)

From the worktree root, using existing tests only, in their own private
temporary registries (each unittest fixture builds a `TemporaryDirectory`
SQLite registry; no live controller, DB or slot process is touched):

1. `git -C E:\ChimeraWork\slot-02 rev-parse HEAD`
2. `git -C E:\ChimeraWork\slot-02 status --porcelain`
3. `python -m unittest discover -s tools/agent_fleet -p "test_*.py" -v`
   with raw stdout/stderr captured verbatim to `SUITE_RAW_OUTPUT.txt`.
4. `python --version` and `git -C E:\ChimeraWork\slot-02 diff --stat
   7d3601e7d9e04019cc3794ccf0a9738627c9fd71 HEAD -- tools/agent_fleet`
   (base-to-head source drift of the controller plane).
5. Re-hash the files listed in `BINDING.json` and compare.

## Preregistered predictions and their falsifiers (this run)

- P1: The discovery suite at this base reproduces on Windows with every
  controller-plane test passing. Known exception, documented not owned here:
  exactly the two `test_master_catalogue` count-pin failures already recorded
  as pre-existing and being repaired by the parallel master-catalogue worker.
  Falsified if any OTHER test fails, or if the catalogue failures differ from
  the documented pair, or if the suite cannot run at all.
- P2: Every GOV-01 clause above maps to named source lines, named existing
  tests and preserved evidence, or is marked OPEN. Falsified if this matrix
  marks SUPPORTED without an executed test or preserved evidence behind it,
  or if cited source behavior contradicts the cited evidence.
- P3: The negative controls already checked into the suite exercise, against
  real SQLite transactions: concurrent duplicate claim (one winner), refused
  overlapping write scope (case-insensitive), refused foreign/stale
  generation without a revision bump, restart retaining identity+claims and
  refusing foreign credentials, recovery requiring trusted attestation and a
  new generation, and integration acknowledgement refusing wrong branch, base
  or stale epoch. Falsified if any of these refuse-paths passes an operation
  it must refuse, or mutates state on refusal.

## Negative controls preregistered (all EXISTING tests; none added, none weakened)

| id | existing test | must refuse / must hold |
|----|---------------|--------------------------|
| N1 | test_control.ControlTests.test_concurrent_claim_one_winner | two agents race one READY task: exactly one claim succeeds |
| N2 | test_control.ControlTests.test_scope_conflict_casefold | second claim over an active overlapping scope: `write_scope_conflict` |
| N3 | test_control.ControlTests.test_foreign_and_stale_claim_refused_without_revision | foreign actor or stale generation: refused, revision unchanged |
| N4 | test_control.ControlTests.test_restart_retains_identity_and_claims | new Control instance over the same store: snapshot identical; foreign credentials: `service_identity_mismatch` |
| N5 | test_control: test_integration_request_stale_after_failover, test_master_base_refused, test_task_branch_wrong_refused | integration ack refused on stale epoch, wrong base branch, wrong task branch |
| N6 | test_control: test_recovery_requires_attestation_and_new_generation | recover refused to non-supervisor and without evidence; new claim gets a strictly greater generation |
| N7 | test_run_queue: test_review_releases_capacity_but_requires_exact_integration_head, test_expired_lease_holds_owner_until_evidenced_recovery | integration head mismatch: `review_head_mismatch`; expired lease holds the owner until preserved+drained evidence |

## Planned outputs

- `SUITE_RAW_OUTPUT.txt` — verbatim unittest output (raw, not summarized).
- `SUITE_SUMMARY.json` — counts parsed from the raw file, plus command and
  Python version.
- `BINDING.json` — base/head/source hashes, before-run; re-verified after.
- `RECORD.md` — execution narrative, per-clause findings, limitations.
- `RESULT.md` — one-paragraph conclusion.
- `docs/GOV01_ACCEPTANCE.md` — the per-clause SUPPORTED/OPEN/FAILED matrix.

Acceptance itself is NOT claimed anywhere: slot 1 decides canonical GOV-01
acceptance after review and the full catalogue import (task packet), and the
controller itself records `acceptance: NOT_CLAIMED` semantics for review
states.
