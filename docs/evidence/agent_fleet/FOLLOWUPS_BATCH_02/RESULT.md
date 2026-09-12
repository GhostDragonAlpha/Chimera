# fleet-followups-batch-02 — RESULT (2026-09-11, subagent-worker-06)

Task generation 1, slot 9, worktree `E:\ChimeraWork\slot-09`, base
`4c31999797a9383ea252019be1f32511709fa280` (= tip of `astra/gait-capture`
at claim; worktree HEAD == record base verified clean, nothing to
reconcile). Preregistered in [PREREGISTRATION.md](PREREGISTRATION.md)
(own commit `7dd59c60`, before any correction, no measured actuals).
Acceptance is NOT_CLAIMED until independent review.

## Delivered (F1-F3 in scope; F4 documented per packet)

- F1: `docs/evidence/agent_fleet/SLOT_EXPANSION/RESULT.md` — dated
  append-only correction pointing at the three retained scale-probe runs
  (1473 ops p50 13.3ms / 1243 ops p50 15.5ms / 1426 ops p50 13.5ms, zero
  database-locked in all; `MEASUREMENT.json` `mixed_load_probe`). The stale
  line 12 is untouched: the file diff is +6/-0 (append-only by numstat).
- F2: `docs/evidence/agent_fleet/SLOT_EXPANSION/MEASUREMENT.json` — new
  dated key `correction_20260911_followups_batch_02` (the
  `correction_20260911_gen2` key precedent): records the load-fragility of
  the `lock_errors == 0` assertion, retains the assertion deliberately, and
  names the isolation-rerun disposition. Diff +5/-0; every prior key
  byte-identical. The optional in-test comment is delivered as
  [SCALE_PROBE_COMMENT_PROPOSAL.md](SCALE_PROBE_COMMENT_PROPOSAL.md)
  because `tools/agent_fleet/test_slot_expansion.py` is outside this task's
  write scopes (no edit made there).
- F3: `tools/agent_fleet/test_task_abandon.py` — both bare
  `assertRaises(Refusal)` blocks now assert the exact `missing_*` refusal
  NAMES (`missing_abandon_reason` / `missing_abandon_evidence` /
  `missing_preservation_evidence` / `missing_drain_evidence`, matching the
  controller's text()-validation order); the `task_has_no_slot` /
  `slot_binding_mismatch` arms are documented UNREACHABLE BY DESIGN
  (comment in the new test) with their design invariant pinned
  executably: RUNNING implies a bound slot whose back-reference names the
  task, across a claim -> claim_abandon -> re-claim cycle. 19 -> 20 tests.
- F4: DOCUMENTED ONLY — [WATCHDOG_FAIL_CLOSED_FINDING.md](WATCHDOG_FAIL_CLOSED_FINDING.md)
  carries the exact fail-open lines, the exact fail-closed patch (malformed
  `CHIMERA_FIXTURE_PARENT_PID` -> watchdog ACTIVE with `os.getppid()`;
  empty/unset and explicit `parent_pid=0` behavior unchanged), a runnable
  regression-test sketch whose `assertIsNotNone` trips on the current code,
  and the recommended followup `watchdog-fail-closed-01` scoped to
  `capture_window.py` + `test_capture_window.py`. No out-of-scope file was
  touched.

## Measured actuals vs preregistered predictions

Raw outputs (all `*.txt` by design — the `*.log` ignore trap):

- `TASK_ABANDON_AT_BASE.txt` — the module at the prereg head (source
  identical to base): **Ran 19 tests, OK** (pre-edit baseline).
- `TASK_ABANDON_AT_DELIVERY_HEAD.txt` — the module with F3:
  **Ran 20 tests, OK** (19 + 1 new invariant test; no test removed,
  skipped or loosened; every prior named assertion intact).
- `RUN_FULL_SUITE.txt` — full fleet suite from the repo root, first run at
  the delivery head: **Ran 232 tests, FAILED (failures=1, skipped=1)** —
  the single failure is `test_capture_window`'s
  `test_verify_hwnd_capture_none_pin_adopts_measured_size`
  (`occluded_or_foreign_content` vs `unobscured`), the EXACT signature
  recorded in the RUNNING task `capture-flake-tolerance-01` (owner
  subagent-worker-11, slot 10, whose scopes own `test_capture_window.py`).
  Retained unmodified.
- `CAPTURE_FLAKE_ISOLATION_RERUN.txt` — the flaky test in isolation:
  **Ran 1 test, OK** — non-reproducing outside suite load, matching the
  recorded paint/occlusion-timing diagnosis. The fix is OWNED by the
  RUNNING tolerance task (retry-wrapper design, assertions unchanged);
  this task deliberately does not touch that file.
- `RUN_FULL_SUITE_RERUN.txt` — full-suite rerun (both outputs retained per
  the SLOT_EXPANSION precedent): **Ran 232 tests, FAILED (failures=1,
  skipped=1)** — the same single capture test, same verdict; identical
  capture_sha256 across both suite runs (deterministic under-load
  behavior, still green isolated). Every other test green in both runs.
- `SLOT_EXPANSION_MODULE_ISOLATED.txt` — the F2 module in isolation:
  **FAILED, lock_errors: 1** (single database-locked at the single-writer
  boundary; p99 2756ms, max 12264ms — the machine was co-loaded with other
  fleet slots' suites). Retained.
- `SLOT_EXPANSION_MODULE_ISOLATED_RERUN.txt` — rerun: **Ran 5 tests, OK**,
  lock_errors: 0. Both retained.

Prediction-by-prediction:

1. F1/F2 append-only evidence edits — CONFIRMED (numstat +6/-0 and +5/-0;
   JSON re-validated, all prior keys preserved).
2. F3 named refusals + unreachable-by-design documentation, suite green,
   no assertion removed or loosened — CONFIRMED (19 -> 20, both runs OK).
3. F4 lands as documentation only; no file outside scopes changes —
   CONFIRMED (git status shows exactly the four scoped paths).
4. Full fleet suite green at the delivery head, or the red with the
   documented isolation-rerun disposition — the disposition path fired:
   the ONLY red in both full-suite runs is the capture test whose fix is
   owned by the RUNNING `capture-flake-tolerance-01` task, and it is green
   in isolation with all outputs retained. NOT the F2 scale-probe
   assertion (lock_errors == 0 held in both full-suite runs, 0 locked).

## FALSIFIER status: none triggered

No assertion removed or loosened anywhere (the `lock_errors == 0`
assertion stands; the bare-Refusal conversions only ADD name precision);
no evidence file rewritten (numstat 0 deletions on all three evidence
docs; prior MEASUREMENT keys byte-identical); no followup "fixed" by
deleting the behavior it describes (the unreachable refusal arms remain in
`control.py`, untouched and now documented; the watchdog finding lands as
a finding, NOT as an out-of-scope code edit); no file outside the four
recorded scopes modified; the full-suite red is confined to the foreign
owned flake and carries the documented rerun disposition.

## New observation recorded for the lead (beyond the packet)

The F2 fragility is BROADER than the packet's "green in isolation": on
today's co-loaded fleet host, a MODULE-ISOLATED scale-probe run also caught
a single database-locked error once (`SLOT_EXPANSION_MODULE_ISOLATED.txt`;
rerun green, `..._RERUN.txt`). The single-writer SQLite boundary is
reachable whenever the HOST is loaded, not only under in-suite contention.
The retained assertion + rerun disposition still holds, but the isolation
rerun is only as green as the host is quiet — worth folding into the
eventual capture-flake-tolerance-style decision for the scale probe (a
bounded single-retry would need the same anti-masking bounds; NOT done
here, out of scope, recorded only).
