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
  `stale_provision_requires_recovery` classified as recoverable contention.
  The skip is observable through `claim_once`'s `refusals` list, whose entries
  now carry the machine-readable reason code (`task:code`, via the new
  `_refusal_code` helper). `run_forever` itself does not alert — stated here
  exactly: a stale-provision-blocked worker polls and skips silently until a
  supervisor rebinds; supervisory observation comes from the controller events
  and the refusals list, not from an active worker alarm.
- **F6** `tools/agent_fleet/test_layer_guard.py`: 8 characterization tests
  (layered claim refusal + rebind unblock; clean-slot claim unaffected;
  release preservation in slot history AND receipt incl. composite attestation
  evidence; immediate reclaimability; detached-review capacity accounting with
  the guard; contention classification for both message forms; queue skip with
  reason-code refusal entries; layer-level rebind refusals; never-provisioned
  release no-op path).

## Dispositions (documented, control.py items deferred to a future lane)

- F4: `review_requeue` generation/provision skew — structural enforcement
  already prevents authority reuse; enforcement assertion deferred.
- F5: `slot_rebind` bound-task hold cross-check — drain attestation required;
  deferred.
- F7/F8: informational; deferred with rationale in REVIEW_INDEPENDENT.md.

## Commands and outcomes (isolated temporary registries)

- `python -m unittest test_layer_guard` → **8/8 OK** (after the second
  independent-review pass: composite-attestation assertion, reason-code
  refusal entries, layer rebind refusals, never-provisioned release).
- `python -m unittest discover -s tools/agent_fleet -p 'test_*.py'` (repo
  root) → 164 tests, 2 failures, 1 skip; failures identical to the documented
  pre-existing catalogue count pins (unchanged from the PR #42 record); no
  weakened expectations.

## Prediction check

- Layered claim refusing a stale-provisioned free slot with the actionable
  reason: PASS (fixture identical to the live condition).
- `release_review_slot` preserving provision evidence: PASS (slot history +
  receipt fields + composite attestation evidence).
- Worker loop degrading the refusal to skip/retry with observable reason
  codes: PASS (`run_forever` itself does not alert — see F3 wording above).
- Existing review-handoff/worker expectations: unchanged suite result.

## Second independent-review pass (amend commit)

Findings addressed in-branch rather than deferred: refusal entries carry
reason codes (`_refusal_code`), F3 evidence wording corrected (no claim of an
alert path), composite attestation asserted, layer rebind refusals and the
never-provisioned release path pinned. Verdict of record:
APPROVE_WITH_FOLLOWUPS → findings landed.
