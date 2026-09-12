# GOV-01 acceptance matrix — evidence reconciliation

Task `gov01-evidence-reconcile-01`, generation 7, slot 2, worker
`subagent-worker-01`. Offline read-only reconciliation of the existing
authoritative-ledger/ownership source and evidence against roadmap card
GOV-01 (`docs/roadmap/holodeck_tasks.json:413-434`). **Canonical GOV-01
acceptance is NOT claimed here** — slot 1 decides acceptance after review and
the full catalogue import. DYAD: NOT_APPLICABLE — reference/source-only docs
scope; no runtime, GPU or engine process was run, so no simulation validation
is claimed.

Reconciliation basis: worktree head `d012b4b12ea2224d6b5669974776047238b76755`
(task base `7d3601e7d9e04019cc3794ccf0a9738627c9fd71` verified ancestor; base
to head added the slot-binding/layer-guard/execution-proof/review-handoff and
catalogue-plane modules — see `docs/evidence/master_completion/GOV01/`).
Source identity bound in `BINDING.json`; suite evidence in
`SUITE_RAW_OUTPUT.txt` / `SUITE_SUMMARY.json`; preregistration written before
execution in `docs/evidence/master_completion/GOV01/PREREGISTRATION.md`.

## Per-clause matrix

| # | GOV-01 clause | Verdict | Maps to (source) | Maps to (executed tests, this run) | Maps to (preserved evidence) |
|---|---------------|---------|------------------|-------------------------------------|------------------------------|
| 1 | Canonical task IDs, claims, owners and publication queue | **SUPPORTED** | `tools/agent_fleet/control.py:398-414` create_task (canonical ID regex, duplicate refusal, unique `astra/tasks/<id>` branch, `pr_base` pinned to `astra/gait-capture`, scope validation `control.py:41-49`); `control.py:415-438` claim (qualified agent, capacity, integrated dependencies, overlapping-scope refusal `control.py:51-53,425-427`, slot bind, generation bump); `control.py:93-98` `_task` owner+generation fencing (`stale_or_foreign_claim`); publication queue `control.py:528-536` (`integration_request`, `publication_executed: False`) and `control.py:537-546` (`ack_integration`, supervisor-only, epoch-fenced, base-pinned); durable state `control.py:65-75,279-313` (SQLite `BEGIN IMMEDIATE` + append-only events) | `test_control.py`: test_five_slots_and_sixth_refusal, test_concurrent_claim_one_winner, test_claim_capacity, test_scope_conflict_casefold, test_foreign_and_stale_claim_refused_without_revision, test_integration_ack_and_explicit_slot_release, test_master_base_refused, test_task_branch_wrong_refused, test_dependency_waits_for_integration, test_restart_retains_identity_and_claims; `test_run_queue.py` (independent RunQueue reference: exact-head ack, lease/recovery fencing); `test_slot_binding.py` 11 tests; `test_review_handoff.py` 13 tests; `test_layer_guard.py` 8 tests; `test_execution_proof.py` 4 tests | `docs/evidence/agent_fleet/FIVE-CLIENT-COORDINATION/20260909Z-A/` (9/9 preregistered scenarios incl. capacity, FIFO contention, restart durability); `docs/evidence/agent_fleet/PREREGISTRATION.md` (10 structural predictions, each with named falsifier) |
| 2 | Independent reference/benchmark and executed negative controls | **SUPPORTED** (limitations recorded) | Negative-control refuse paths: `control.py:425-427` scope conflict; `control.py:93-98` stale/foreign fencing; `control.py:512-527` recover (supervisor-only, evidence-gated, generation bump); `control.py:537-546` ack epoch/base fencing; `control.py:74` identity mismatch; `run_queue.py` as the independent reference queue implementation | Executed 2026-09-11 on Windows/CPython 3.14.3, this base: **166 tests, 163 pass, 1 skip (Windows symlink unavailability), 2 pre-existing documented `test_master_catalogue` count-pin failures owned by the parallel catalogue lane** — zero controller-plane failures. Negative controls N1–N7 of `PREREGISTRATION.md` all present in the run (concurrent claim one winner; casefolded scope conflict refused; foreign/stale generation refused without revision bump; restart retains identity+claims and refuses foreign credentials; recover requires attestation+new generation; ack refuses stale epoch/wrong base/wrong branch; exact-head integration + evidenced recovery) | `docs/evidence/agent_fleet/WINDOWS_LEAD_REVIEW_20260910/` (PR11 fleet fixes: independent Windows suite 78/78, raw `suite.txt`, preregistered prediction, candidate `8bf8f643` vs reconciled head `4e7d074f` identity check); `BOOTSTRAP-LIVE-RESTART/LIVE-RESTART-20260909.md` (live restart preserved revision/epoch/leader/owner/slot/generation; duplicate start refused); failed-run evidence preserved (`FAILED-slot02par-162905`, retained Linux failures per PR11 RECORD) |
| 3 | Reproduction commands, source identity, preserved evidence and limitations | **SUPPORTED** | n/a (this clause is about the evidence instrument itself; enforced record fields: `control.py:299-301` audit events without credentials; `test_control.py:173-176` token-exposure test) | Exact commands and raw outputs: `SUITE_RAW_OUTPUT.txt` (verbatim), `SUITE_SUMMARY.json` (command, counts, per-failure detail); command form matches the PR11 record | Source identity: `BINDING.json` SHA-256 of all 19 controller/source+test files, captured before the run and re-verified after with **0 mismatches**; base/head lineage recorded; evidence preserved in-repo under `docs/evidence/agent_fleet/` (append-only records with commands, hashes, limitations) |
| 4 | Integration contract and full autonomous handoff | **OPEN** (contract present and tested; autonomous completion not executed and not claimed) | Contract enforced in source: branch/PR/base rules `control.py:410,448-449,531,543`; review freeze `control.py:447,453`; `review_requeue` stale-base reconciliation without force-push `control.py:547-557`; provision bound to task+generation+base `control.py:558-573`; `review_handoff.py` review-preserving slot handoff layer; deployment boundary documented in `docs/THE_CONTROLLER_TRANSITION.md` (integrated PR ≠ deployment; five transition gates listed) | `test_review_handoff.py` 13/13 (handoff preserves review, frees execution capacity, exact-head provisioning, restart preserves detached review); `test_layer_guard.py` 8/8 (stale-provision refusals, rebind attestations, bounded preservation history); `test_control.py` integration/ack/requeue tests | PR11 RECORD: "The running project controller remains on its original operator-checkout source; source integration does not install this patch" (deployment unclaimed); Master list: "GOV-01 acceptance remain[s] open under [its] existing IDs and owners" |

## Card-level prediction and falsifier check (GOV-01 card)

- Card prediction "Conflicting claims are rejected and active assignments
  survive restart": **reproduced at this base** by executed tests
  (test_scope_conflict_casefold, test_concurrent_claim_one_winner,
  test_restart_retains_identity_and_claims) plus preserved live-restart
  evidence (LIVE-RESTART-20260909: registry identical across a controlled
  live restart).
- Card falsifier "Two agents own the same write scope or stale state replaces
  a newer claim": **not triggered** — the refusing paths were executed this
  run and held; no counter-example found in source or evidence.
- Packet falsifiers: conflicting scope accepted — **not triggered**; stale
  state replacing new claim — **not triggered**; restart losing claim —
  **not triggered**; source/evidence mismatch — **not triggered** (PR11
  follow-up assertions named in its review are present in current source:
  `test_resources.py:113-135` FIFO-as-stamp with queue-state assertions,
  `test_resources.py:171-184` memory re-request after release); unsupported
  acceptance claim — **not triggered** (this matrix claims no acceptance).

## Known exceptions and limitations (recorded, not hidden)

1. The two `test_master_catalogue` count-pin failures are pre-existing,
   documented pre-run in the merged in-repo records
   (docs/evidence/agent_fleet/SLOT_BINDING/RESULT.md, LAYER_GUARD_RESULT.md), and
   owned by the parallel catalogue-repin lane: the pins (2430 Master lines, 65 master rows)
   lag the Master list's recorded append-only growth (2540 lines, 76 rows).
   They are catalogue-import pins, not ledger/ownership behavior. This task
   did not edit them, the catalogue, or the Master list.
2. One Windows skip: `test_unsafe_arguments_and_symlink_escape_refuse`
   (symlink creation unavailable) — environment limitation, preserved in the
   raw output, identical to prior Windows runs.
3. Offline controller tests exercise real SQLite transactions and local HTTP
   only; they are not live-deployment, GitHub-publication or Windows-service
   certification (`docs/evidence/agent_fleet/PREREGISTRATION.md:49-51`).
   The live controller still operates its original checkout source; no
   deployment is claimed by this task.
4. Slot-level GOV-01 history: the slot-5 historical provisioning mismatch
   recorded in the Master list was resolved structurally by the integrated
   slot-binding work (provision bound to task+generation+base,
   `slot_rebind` recovery with preserved records, stale-provision claim
   refusals) — tested by `test_slot_binding.py`/`test_layer_guard.py`; the
   historical observation itself remains preserved evidence.

## Proposed minimal remaining milestones (for slot 1's acceptance decision)

1. Master-catalogue lane (parallel worker) lands the two count-pin updates so
   `test_master_catalogue` returns green without weakening any pin's intent.
2. Slot 1 reviews this matrix plus the full catalogue import
   (`catalogue_import` plane), then decides canonical GOV-01 acceptance.
3. If live acceptance is to be claimed, execute the
   `docs/THE_CONTROLLER_TRANSITION.md` gates first: exact reviewed source
   revision, quiescence + drain attestation, listener/PID identity, isolated
   same-store upgrade/restart/rollback rehearsal, post-restart snapshot
   comparison. Deployment remains unclaimed until then.
4. Publication stays behind the external trusted publisher
   (`ack_integration` boundary, `publication_executed: False`); no autonomous
   self-publication path exists or should be added.

## Verdict summary

Clauses 1–3: **SUPPORTED**. Clause 4: **OPEN** (contract integrated and
tested; autonomous handoff completion, live deployment and canonical
acceptance remain explicitly unclaimed). GOV-01 acceptance:
**NOT_CLAIMED** by this task.
