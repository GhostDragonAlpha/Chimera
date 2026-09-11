# fleet-regression-sweep-01 — RESULT

- agent: subagent-worker-07, slot 4 (E:/ChimeraWork/slot-04), generation 1
- preregistration: 92a67a4c (committed before any sweep command; see
  PREREGISTRATION.md — statement/prediction/falsifier, method, declared
  deviations D1–D4)
- sweep head: 4c31999797a9383ea252019be1f32511709fa280 (astra/gait-capture tip
  at sweep time; base 5199d9c3 was 15 commits behind and was fast-forward
  merged, no force)
- date: 2026-09-11
- raw evidence: the RAW_*.txt files beside this record, plus DRIFT_TABLE.txt

## STATEMENT (under test)

The gates, contracts, and evidence commands merged by wave-2/3 (eleven PRs,
#49–#64) pass at the current tip AS A SET.

## Verdict: HOLDS with one retained finding — the integration set is green but
not yet robust on a shared host

- Every per-lane decisive command re-runs clean at tip, standalone, with
  exactly the lane-recorded counts: test_worktree_reconcile 10/0/1 (the one
  expected Windows symlink skip), test_capture_window 28/28,
  test_controller_transition 4/4, test_client_instance 9/9,
  test_dyad_provider 14/14, test_slot_expansion 5/5 (isolated temp registries;
  the live service was never touched), test_task_abandon 19/19, catalogue pins
  23/23, test_orient_continuation 9/9, membrane CPU gate PASS (V1b–V9 +
  corrupt-control DETECTED, exit 0).
- Full fleet discover suite: run 1 = **231 tests, FAILED (failures=1,
  skipped=1)**; rerun = 231 tests, OK (skipped=1). The one failure did not
  reproduce in four standalone capture-window runs or the full-suite rerun.

## Finding F1 (retained; the reason this sweep exists)

`test_verify_hwnd_capture_none_pin_adopts_measured_size`
(tools/agent_fleet/test_capture_window.py:490) failed in full-suite context,
run 1, with a capture-content mismatch: the adopted-size capture's sha256 did
not match the expected fixture sha and the recorded verdict was
'occluded_or_foreign_content' instead of 'unobscured' (full traceback verbatim
in RAW_FULL_FLEET_SUITE.txt). Characterization:

- standalone: 4/4 runs green (RAW_TEST_CAPTURE_WINDOW.txt + 3 repeats in
  RAW_CAPTURE_WINDOW_REPEATS.txt);
- full-suite rerun: green, 231 tests (RAW_FULL_FLEET_SUITE_RERUN.txt);
- so: intermittent, specific to full-suite context at sweep time. The sweep
  host is SHARED — slot-02's worker (studio-grid-depth-01) was active on this
  same machine during run 1; a foreign window over the fixture at the sampled
  instant produces exactly this verdict. The suite's own overlap contract test
  (test_overlap_does_not_contaminate_window_specific_capture) passes, so the
  capture path itself is sound; what is not robust is a REAL capture racing
  concurrent host activity for the sampling instant.

This is integration-drift of the environment-sensitivity class: the wave's
"full suite green" claim holds at tip but is not REPRODUCIBLY green on a busy
host. A falsified prediction is a result: the sweep's PREDICTION 1 as written
(222/0/1) is falsified on both count and the run-1 verdict; the statement
survives only with this qualification attached.

## Finding F2 (count drift, explained)

The tip-era full-suite count is 231, not the 222 the dispatch expected. The
dispatch's own figures were mutually inconsistent: it expected "222/0/1" AND
"test_capture_window 28/28" — but 28 is +9 over the lane-era 19, and 222 + 9
= 231. The 222 figure was captured (SLOT_EXPANSION/RUN_FULL_SUITE_GEN2.txt)
before the capture-window additions landed. Resolved by measurement; recorded
so the next expectation is set correctly (231 at 4c319997).

## Declared deviations (fixed in the prereg, honored here)

- D1: the full membrane runner was NOT executed — its normal mode builds and
  launches a Vulkan compute probe against the host GPU, which this task's
  safety envelope (no GPU/model) forbids. The CPU claim was verified by
  running the runner's own cpu_reference command verbatim. The CPU gate PASS
  is therefore the verifier's own result, not a summary of all runner stages.
- D2: the packet's "vulkan ownership suite's CPU-side tests" does not exist as
  a runnable suite at tip; that lane's own RESULT.md records the CPU unit test
  NOT_APPLICABLE. Mapped onto D1's CPU gate, recorded in the drift table.
- D3: the CPU verifier's timestamped result JSON (written to
  docs/evidence/gpu_fixtures/, outside this task's write scope) was copied
  byte-identical into this directory and removed from the out-of-scope path;
  worktree left clean except this evidence dir.
- D4: the packet 19/19 vs dispatch 28/28 capture-window discrepancy — resolved
  by measurement (28 at tip; see F2).

## Scope discipline

All deliverable files are inside docs/evidence/agent_fleet/REGRESSION_SWEEP_01/
and are *.txt / *.md (never *.log). No code, no tests, no docs outside this
directory were touched. The live control plane and operator checkout were
never contacted or modified by any sweep command. Any fix motivated by F1
(harden the capture fixture against concurrent host overlap, or make the
verify test's environment-sensitivity explicit) and by F2 (refresh the
expected-count convention at integration time) is a SEPARATE task — this sweep
does not repair what it measures.
