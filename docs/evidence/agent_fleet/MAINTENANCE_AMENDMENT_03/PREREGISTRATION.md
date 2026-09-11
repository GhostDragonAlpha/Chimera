# PREREGISTRATION — fleet-maintenance-amendment-03

Agent: glm53-lead-02 (lead, slot 1) · base cb874a3a · branch
astra/tasks/fleet-maintenance-amendment-03 · declared BEFORE any
measurement or amendment text lands in this branch's later commits.

## What this amendment will claim (dispositions, declared in advance)

1. `fleet-review-handoff-claim-delegation` (-01 refused live, -02 integrated
   as PR #80, head 2c8fb069 at merge) is CLOSED: deployed via controlled
   transition `claim-restore-d8e3b5f5` (post-transition state ALL-EQUAL);
   the Master note "disposition PENDING integration" is answered.
2. `fleet-catalogue-realization-matching-01` (PR #92, merged bf1a72f6,
   deployment `catalogue-provenance-bf1a72f6`, ALL-EQUAL) is CLOSED, and the
   measured legacy-citation gap it exposed is recorded: the eight pre-field
   holodeck tasks carry `realized_from=None`; lane
   `fleet-task-provenance-backfill-01` (RUNNING, worker-04) lands the
   supervisor op + backfill plan; controlled transition #3 and the eight
   citations follow its integration, in that order.
3. `product-feel-probe-01` (PR #97, merged cb874a3a) is INTEGRATED: blind
   ordered-frames dyad judge PASS 2/2; five product defects measured (the
   judge's findings retained verbatim in the lane's DYAD_REPORT.txt);
   admitted follow-on lanes `product-hud-truth-01` (worker-02) and
   `product-motion-sweep-01` (worker-03); framing and locomotion queued.
4. MAT-02..05 admitted and assigned through team lead subagent-worker-10
   (charter rev 902) via the fleet mailbox; the lead executes host spawns.
5. `engine-feature-resource-lifetime-01` is SUPERSEDED BY CONSTRUCTION by
   the INTEGRATED `-02` (deps corrected to engine-vulkan-cleanup-02); `-01`
   retires via supervisor task_abandon AFTER this PR integrates, this entry
   as evidence.

## Repin procedure (declared before running)

- Run `python tools/agent_fleet/master_catalogue.py --out <tmp>` at the
  AMENDED head; read `coverage.master_row_ids` and
  `coverage.master_row_observations`.
- PREDICTION: the amendment's prose sections add no `| id | ... |` task
  rows, so both counts EQUAL the standing pins (97 / 142) unless a
  disposition entry parses as a row observation (history accumulation) —
  in which case the pins move UP by exactly the measured delta, never down.
- Whatever the measured values: set the two pins to them in
  tools/agent_fleet/test_master_catalogue.py, then run the PERTURBATION
  CONTROL (flip one pin by +1, the pinned test must FAIL, restore) and the
  full agent_fleet suite at the amended head.
- FALSIFIER for the repin: builder output at the amended head that does not
  validate (`validate_payload` non-empty), counts that move DOWN, or a
  perturbed pin that still passes — any of these stops the amendment.

## Honesty clause

No measured actuals appear in this prereg. All counts above the fold are
predictions. Builder output, suite runs, and perturbation results land only
in the later evidence files (RUN_BUILDER_AMENDED_HEAD.txt,
RUN_FULL_FLEET_SUITE.txt, RESULT.md).
