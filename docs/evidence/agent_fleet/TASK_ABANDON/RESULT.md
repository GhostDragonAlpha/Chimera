# fleet-task-abandon-01 — RESULT (2026-09-11, subagent-worker-04)

Task generation 1, slot 3, worktree `E:\ChimeraWork\slot-03`, base
`5199d9c3015f6840b12186f34c3e0c2fd5d7b0a4` (worktree HEAD == record base,
verified clean at claim). Preregistered in
[PREREGISTRATION.md](PREREGISTRATION.md) (own commit `802e4f72`, before any
code; it forward-references the test file by construction). Acceptance is
NOT_CLAIMED until independent review.

## Delivered

- `tools/agent_fleet/control.py`: supervisor-only `task_abandon` (READY ->
  ABANDONED terminal, reason+evidence on the record + audited event,
  permanent id retirement), supervisor-only `claim_abandon` (RUNNING ->
  READY at generation+1 without session revocation; preservation+drain
  attestations; slot freed via the shared `_preserve_provision` machinery;
  active-provision refusal names `slot_rebind`; `resources_still_held`
  mirrors `recover`), and the single ABANDONED-coherence edit
  (`catalogue_next` `live` excludes ABANDONED; `done` stays
  INTEGRATED-only). All other state switches audited: ABANDONED joins no
  active tuple, so claim eligibility, capacity, write-scope-conflict,
  `_fail`/`yield` sweep and stale-claim drops treat it as inactive with no
  code change (each pinned by a test).
- `tools/agent_fleet/test_task_abandon.py`: 19 isolated tests (temp
  registry per test; no live service, no live store).
- `docs/THE_AGENT_FLEET.md`: dated append documenting both ops, the
  coherence rule, refusals and the deployment boundary.

## Measured actuals vs preregistered predictions

Raw outputs (all `*.txt` by design — the `*.log` ignore trap):
- `SUITE_BASELINE_AT_BASE.txt` — full fleet suite at base source
  (worktree HEAD = preregistration commit `802e4f72`; source identical to
  base `5199d9c3` since that commit adds one evidence doc):
  **Ran 198 tests, OK (skipped=1)** — the documented Windows-symlink skip.
- `TASK_ABANDON_TESTS.txt` — the new module: **Ran 19 tests, OK**.
- `SUITE_FULL_WITH_TASK_ABANDON.txt` — full fleet suite from the repo root
  with the implementation, re-captured at the exact DELIVERY HEAD
  `555d76c0` after a scope-string constant in one new test was renamed to
  satisfy the doc-lint pointer pass (behavior-free rename): **Ran 217
  tests, OK (skipped=1)**; 198 + 19 = 217, no existing test removed,
  skipped or weakened. An intermediate full-suite run before the rename
  was also 217 OK.

Prediction-by-prediction:

1. task_abandon happy path + audit record + `filesystem_touched: False` —
   CONFIRMED (`test_task_abandon_retires_ready_task_with_audit_record`,
   `test_task_abandon_never_touches_the_filesystem`: the whole temp store
   tree is unchanged by the op).
2. All task_abandon refusals, names as registered, revision unchanged —
   CONFIRMED (`..._refuses_non_supervisor_actors`,
   `..._refuses_unknown_task`, `..._refuses_inactive_states` incl.
   RUNNING/BLOCKED/RECOVERY_HOLD/ABANDONED/REVIEW/INTEGRATED,
   `..._requires_reason_and_evidence`, plus
   `test_refusals_leave_revision_and_audit_untouched`).
3. claim_abandon happy path (READY at gen+1, owner/slot/instance cleared,
   attestations in checkpoint, queue drops, session intact, no fabricated
   preserved-provision record) — CONFIRMED
   (`test_claim_abandon_returns_ready_at_new_generation_without_revoking_session`,
   `test_claim_abandon_drops_queued_resource_requests`).
4. All claim_abandon refusals incl. `provision_active_use_slot_rebind` and
   `resources_still_held` — CONFIRMED
   (`..._refuses_non_supervisor_and_wrong_states`,
   `..._refuses_active_provision_naming_slot_rebind`,
   `..._refuses_while_resources_still_held`,
   `..._requires_both_attestations`).
5. ABANDONED coherence (not claimable; satisfies no dependency; scope
   freed; not owner-capacity; catalogue card re-proposable, live_tasks
   exclusion) — CONFIRMED (`test_abandoned_id_is_permanent_scope_freed_and_dependency_blocking`,
   `test_abandoned_task_not_counted_as_owner_capacity_or_active`,
   `test_abandoned_card_is_reproposable_in_catalogue_next`).
6. Reopen invariants (stale generation refused; re-claim advances
   generation again) — CONFIRMED (`test_stale_generation_refused_after_claim_abandon`).
7. yield -> recover path intact (session ends by design there; recover
   returns READY at gen+1) — CONFIRMED
   (`test_yield_recover_path_still_works_alongside_claim_abandon`).
8. Audit append-only, strictly increasing sequences, no token material in
   snapshot or events — CONFIRMED (`test_audit_trail_append_only_and_token_free`).
9. Full suite green with exact counts reported with provenance — CONFIRMED
   (198 -> 217, both OK).

FALSIFIER status: none triggered. No live claim retired without
attestations; no session revoked by the new ops (the yield path still ends
its own session by design, unchanged); no filesystem write; audit history
append-only; no gate weakened (217/217 vs 198/198 baseline, same single
documented skip); yield-recover path proven intact.

## Boundary notes

- Scope: only `tools/agent_fleet/control.py`,
  `tools/agent_fleet/test_task_abandon.py`, `docs/THE_AGENT_FLEET.md`
  (append-only dated section) and this evidence dir. `review_handoff.py`'s
  duplicated claim predicate needed no change (the single-omission rule
  keeps it coherent) and was NOT touched — out of scope.
- Deployment: `control.py` is also the deployed controller source. This
  change reaches the live service only via a later controlled transition;
  no live-service mutation was performed or attempted here.
- Preregistration commit `802e4f72` used `--no-verify` once, per the
  library-guard hook's own instruction, because a preregistration
  necessarily forward-references the not-yet-existing test file; the
  reference is satisfied by this delivery and the hook is green on every
  subsequent commit.
- Post-review supervisor steps (the LEAD's, not in this PR): retire the
  documented stale records (fleet-run-queue-01, fleet-orient-continuation-01,
  engine-vulkan-cleanup-01, window-capture-ownership-01,
  fleet-controller-upgrade-01) with the new ops, per the third-wave Master
  amendment.
