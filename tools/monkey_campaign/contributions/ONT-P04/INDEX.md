# first_run_failures/ - preserved failing-run evidence (ONT-P04 correction)

Every first-run failure of this attempt's new probes is preserved here and
enumerated below, so the preservation claim is verifiable from artifacts
(correcting the prior attempt's "preserved in session history" gap named by
the operational lead). Files:

- `test_gpu_handoff_run1.log` - FIRST recorded run of the frozen GPU-A probe
  suite: 28 tests, 4 errors + 1 failure, 23 OK.
- `test_gpu_handoff_run2.log` - after the first fix round: 28 tests,
  1 error + 1 failure.
- `test_gpu_handoff_run3.log` - green: 28/28 OK (matches the final battery).
- `correction_records_and_p04_records_battery_stage_diagnostic.log` - captured
  diagnostic of the battery-stage failures (carried test_p04_records +
  new test_correction_records).

## Complete failed-run sequence and disposition

1. `test_gpu_handoff` run1 (archived): H6 x3 ERROR - the shared
   `draining_with_gate` helper omitted the `handoff_admit` step, so
   `handoff_gate_close` correctly refused `handoff_not_draining` (probe
   fixture defect). H2 `test_restoring_and_available_phase_refusals` ERROR -
   the new-cycle probe's fresh `handoff_request` was refused
   `training_request_not_admitted` because the trainer's controller request
   had already been served in the completed cycle (probe fixture defect).
   H4 `test_hold_then_recover_without_evidence_stays_held` FAIL - the probe
   expectation contradicted the frozen semantics: with the grant still live,
   recover correctly resumes TRAINING (protected retention). Fix: the probe
   now releases the grant first and asserts the stronger `already_launched`
   replay guard. Dispositions: expectation/fixture fixes in the PROBE only;
   no implementation behavior changed.
2. `test_gpu_handoff` run2 (archived): H2
   `test_restoring_and_available_phase_refusals` ERROR again - after adding a
   fresh controller `resource_request`, the GPU was FREE, so the controller
   granted it immediately and the machine again correctly refused
   `training_request_not_admitted` (the frozen "admitted" definition is a
   queued, unserved request). Fix: the fixture re-acquires the GPU with the
   gamer first, restoring genuine contention.
3. `test_gpu_handoff` run3 (archived): green 28/28.
4. Battery stage, carried `test_p04_records.test_publication_receipt_states_
   specification_only` ERROR (archived diagnostic): this attempt's extraction
   initially placed `GPU_HANDOFF_PUBLICATION_RECEIPT.untracked.json` at the
   repo-true subpath `pinned/tools/monkey_campaign/`, while the byte-identical
   carried probe reads it at `pinned/` root (the prior verified layout).
   Fix: extraction layout aligned to the prior attempt (file at `pinned/`
   root; the 52-entry `pinned_file_hashes.json` is now the exact key/hash set
   of the prior verified list - its whole-file sha256 c79f248b5f75f38f2ae04f3
   b43de988801ae06ddfc1f8e1aee45c2125fbc0753 equals the prior one).
5. Battery stage, `test_correction_records.test_prior_records_carry_all_three_
   counts` FAIL (archived diagnostic): assertIn on line-wrapped markdown.
   Fix: whitespace normalization. (Same defect class as the prior attempt's
   "wrapped-markdown record match" first-run fix.)
6. Battery stage, `test_correction_records.test_pinned_controller_is_unmutated_
   at_the_head` FAIL (partial output in session transcript; defect and fix
   described here): the COORDINATION.md string "does not implement the
   model/game handoff above" spans wrapped lines. Fix: whitespace
   normalization.
7. Battery stage, runner-level: `run_all_probes.py` initially listed
   PREREGISTRATION.md in `CARRIED_FROM_PRIOR` against the PRIOR attempt's
   prereg hash - a runner bug (this attempt's preregistration is its own
   frozen document, hash 124c3acfc6ae572bdfab7021c30a0802ddd6f5551b4f9c12a18e8
   ad72e85ecbc, unchanged since its freeze BEFORE any probe ran). Fix: only
   the two carried probe files belong in that list.
8. Final battery: 9 suites, 118/118 OK, exit 0, carried-forward probes
   byte-identical.

Every failure above was a probe-fixture, expectation or harness defect; none
required changing the frozen semantics or the implementation's decision logic.
Nothing suppressed.
