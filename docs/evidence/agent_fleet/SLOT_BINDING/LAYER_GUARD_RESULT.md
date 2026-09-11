# LAYER_GUARD — Result record (fleet-layer-guard-01, gen 1, slot 2)

Base: `6e8cb1d2` (= `astra/gait-capture` after PR #42). Executed after the
independent review of PR #42 (see `REVIEW_INDEPENDENT.md` in this directory).

## Implemented

- **F1** `review_handoff.py::_claim_with_detached_review_capacity`: adopted the
  stale-provision guard — slot selection requires `not engine.get('provisioned')`
  with the same two-refusal fallback (`no_free_slot` vs
  `stale_provision_requires_recovery`) as the base controller.
- **F2** `review_handoff.py::_release_review_slot`: the provision record is
  retired through `Control._preserve_provision` (reason
  `released_for_review_handoff`, attestations embedded) BEFORE the engine-plan
  reset, and the reset now carries `preserved_provisions` forward; the
  task-side receipt additionally carries `provision` identity
  (task/generation/base/head/evidence).
- **F3** `run_queue_worker.py::_claim_contention`:
  `stale_provision_requires_recovery` classified as recoverable contention
  (worker skips/alerts rather than crashing); all other unknown reasons still
  raise.
- **F6** `tools/agent_fleet/test_layer_guard.py`: 6 characterization tests
  (layered claim refusal + rebind unblock; clean-slot claim unaffected;
  release preservation in slot history AND receipt; immediate reclaimability;
  detached-review capacity accounting with the guard; contention
  classification for both message forms; WorkerQueue skip path).

## Dispositions (documented, control.py items deferred to a future lane)

- F4: `review_requeue` generation/provision skew — structural enforcement
  already prevents authority reuse; enforcement assertion deferred.
- F5: `slot_rebind` bound-task hold cross-check — drain attestation required;
  deferred.
- F7/F8: informational; deferred with rationale in REVIEW_INDEPENDENT.md.

## Commands and outcomes (isolated temporary registries)

- `python -m unittest test_layer_guard` → **6/6 OK**
- `python -m unittest discover -s tools/agent_fleet -p 'test_*.py'` (repo
  root) → 164 tests, 2 failures, 1 skip; failures identical to the documented
  pre-existing catalogue count pins (unchanged from the PR #42 record); no
  weakened expectations.

## Prediction check

- Layered claim refusing a stale-provisioned free slot with the actionable
  reason: PASS (fixture identical to the live condition).
- `release_review_slot` preserving provision evidence: PASS (slot history +
  receipt fields).
- Worker loop degrading the refusal to skip/retry: PASS.
- Existing review-handoff/worker expectations: unchanged suite result.
