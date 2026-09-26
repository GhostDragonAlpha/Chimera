# Checkpoint workflow preregistration

Recorded before implementation and tests, 2026-09-24.

Statement: a stateless evidence checker can identify the first unmet checkpoint,
bind the supplied evidence to a coordinator-pinned task/run/candidate/criteria,
and refuse stale or missing artifacts without declaring gameplay or human acceptance.
The native controller remains the owner of progress and claims.

Prediction: integration receipts alone never produce goal_complete=true. Missing,
failed or inconclusive gates return a concrete next action. Altered evidence, wrong
scope/generation/build identity, mixed capture runs, screenshot-only motion evidence,
self-review, and self-granted visual exemptions do not reach review readiness.

Falsifiers: any of the above reaches ready_for_controller_review; an agent-authored
human field yields authenticated human acceptance; the checker launches, mutates
controller state, deletes artifacts or declares the game complete. Also reject duplicate
JSON keys and nonfinite values. Evidence paths stay within the explicitly supplied
root and cannot traverse links/reparse points. File reading is bounded.

Tests use synthetic bytes and controller/context data. They verify structure, bindings,
hashes and next-action selection, NOT whether a video depicts success or any person's
identity. Actual visual inspection, numerical acceptance, publisher approval and human
acceptance remain external evidence judgments. No physical thresholds are invented.

Before fixing the old planner, freeze a regression asserting that all-selected-integrated
does not authorize goal completion. Preserve the pre-fix failure. The sealed 83-task
catalogue is unchanged. New workflow rules operationalize its existing acceptance gates.
