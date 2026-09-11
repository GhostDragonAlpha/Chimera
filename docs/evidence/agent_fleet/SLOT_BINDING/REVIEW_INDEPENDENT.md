# SLOT_BINDING — Independent adversarial review (PR #42)

Reviewer: independent general-purpose subagent (fresh context; not the change
author). Method: read diff `87e281e5..78ec8a61`, parent implementation,
subclass and worker loop; static analysis only (suite claims reported, not
re-executed by the reviewer). Retained verbatim summary; full text in the lead
session record.

## Verdict: APPROVE_WITH_FOLLOWUPS

Base `control.py` change correct, transactional (all mutations inside the
single BEGIN IMMEDIATE with rollback), legacy-safe (all new key access via
`.get`/`setdefault`; schema unchanged), evidence-preserving (only
`_preserve_provision` clears fields, and it appends the full record first;
cap keeps newest 20). Claim guard refusal machine-distinguishable from
`no_free_slot`. No correctness bug found in the base diff.

## Findings

- **F1 MAJOR** — `review_handoff.py::_claim_with_detached_review_capacity`
  lacked the stale-provision guard; deployed claim path silently adopted
  foreign active provisions and returned `no_free_slot` where base returns the
  actionable reason. → landed in fleet-layer-guard-01.
- **F2 MAJOR** — `review_handoff.py::_release_review_slot` wholesale engine
  reset deleted ACTIVE provision + `preserved_provisions` without retention;
  receipt lacked provision fields. → landed in fleet-layer-guard-01
  (preserve-then-reset carrying history; receipt carries provision identity).
- **F3 MAJOR (operational)** — `run_queue_worker.py::_claim_contention` did
  not classify `stale_provision_requires_recovery`; worker loop crashed on the
  refusal. → landed in fleet-layer-guard-01 (skip/retry classification;
  unknown reasons still raise).
- **F4 MINOR** — base `review_requeue` bumps generation leaving an active
  provision bound to the old generation; fields are not consumed as authority
  anywhere (write-only documentation today). Disposition: documented
  exception — the stale provision cannot serve as current authority because
  `provision_slot` refuses while provisioned (rebind required) and the
  executor validates task generation, not provision fields. Enforcement
  improvement (compare binding at recovery time) recorded as a future
  control.py lane item.
- **F5 MINOR** — `slot_rebind` resource check covers `provision_task` only;
  legacy provisions without the field and bound-task holds are covered by the
  required drain attestation instead. Disposition: documented; control.py
  future lane.
- **F6 MINOR** — subclass falsifiers unpinned by tests. → pinned by
  `test_layer_guard.py` (layered claim refusal+rebind, release preservation,
  detached-review capacity, contention classification, queue skip).
- **F7 INFO** — binding fields write-only; structural enforcement via claim
  filter + `slot_already_provisioned`. Future lane: recovery-time assertion.
- **F8 INFO** — `del history[:-LIMIT]` degenerates if LIMIT were 0; guarded by
  the constant (20). Corrupt non-list history raises and rolls back; acceptable.
- Pre-existing (unchanged): base `recover` KeyErrors on slotless
  RECOVERY_HOLD when base Control runs against layered-service state; the
  subclass intercepts slotless recover.

Reviewer condition: land F1/F3 before migration relies on the guard, F2 with
them, pin F6. All three landed in fleet-layer-guard-01 before any live
migration was performed.
