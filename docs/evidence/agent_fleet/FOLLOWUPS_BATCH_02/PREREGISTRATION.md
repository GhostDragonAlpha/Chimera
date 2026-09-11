# fleet-followups-batch-02 preregistration (2026-09-11, subagent-worker-06)

Task `fleet-followups-batch-02` generation 1, slot 9, worktree
`E:\ChimeraWork\slot-09`, base `4c31999797a9383ea252019be1f32511709fa280`
(= tip of `astra/gait-capture` / merge of PR #63; verified worktree HEAD ==
record base, clean, nothing to reconcile). This file is committed BEFORE any
implementation, measurement, or test run and names no measured actuals. It
records four one-liner followups (F1-F4) left by earlier reviews; each is a
smallest correction to already-landed work, batched into one PR.

## STATEMENT

Each recorded followup lands as a smallest correction without weakening any
gate: evidence is corrected by dated APPEND (never rewritten), test coverage
is strengthened by name (never loosened), and the one out-of-scope code fix
is delivered as a documented finding with the exact patch and test sketch
for the scope that owns the file.

## THE FOUR FOLLOWUPS (recorded in the task packet)

- F1 (PR #63 delta review INFO): `SLOT_EXPANSION/RESULT.md` line 12 still
  cites the unretained scale-probe run (1456 ops / p50 13.6ms) although the
  retained evidence replaced those figures with the three retained runs.
  Fix: dated one-line APPEND to `RESULT.md` pointing at the three retained
  runs; line 12 itself is left untouched (append-only evidence).
- F2 (PR #63 delta review INFO): the scale probe's `lock_errors == 0`
  assertion is load-fragile under full-suite contention (two observed runs
  under suite load each recorded exactly one database-locked error; green in
  isolation). Fix: dated append note in `SLOT_EXPANSION/MEASUREMENT.json`
  (the `correction_20260911_gen2` key precedent) recording the fragility and
  the isolation-rerun disposition. The assertion is NOT removed, NOT
  weakened. The optional in-test load-context comment would live in
  `tools/agent_fleet/test_slot_expansion.py`, which is NOT in this task's
  write scopes, so the exact comment text is delivered in this evidence dir
  for the lead's disposition (same treatment as F4).
- F3 (PR #62 review F2/F3): `test_task_abandon` has two bare
  `assertRaises(Refusal)` blocks that do not name the refusal, and the
  `task_has_no_slot` / `slot_binding_mismatch` refusal arms have no
  executable test. Fix: assert the exact `missing_*` refusal NAMES
  (`missing_abandon_reason` / `missing_abandon_evidence` /
  `missing_preservation_evidence` / `missing_drain_evidence`) instead of
  bare `Refusal`; for the two unreachable arms, document in a comment WHY
  they are unreachable by design and pin the design INVARIANT that makes
  them unreachable (RUNNING implies a bound slot whose back-reference names
  the task) instead of pretending to drive an impossible state.
- F4 (PR #62 review F4 INFO): `capture_window.install_parent_watchdog`
  is FAIL-OPEN on a malformed `CHIMERA_FIXTURE_PARENT_PID`: the ValueError
  handler sets `parent_pid = 0` and the function returns None - the orphan
  guard is silently DISABLED exactly when the spawner's env is corrupt.
  `tools/agent_fleet/capture_window.py` is NOT in this task's write scopes,
  so F4 lands as a DOCUMENTED FINDING in this evidence dir: exact fail-closed
  patch (malformed env -> watchdog ACTIVE with `os.getppid()`, the real
  parent), the regression test sketch, and the disposition note for the lead.

## PREDICTION

1. F1/F2 are append-only evidence edits: every pre-existing line/key of
   `RESULT.md` and `MEASUREMENT.json` survives byte-identical; only appends
   (a dated correction line; a new dated correction key) are added.
2. F3 converts bare `assertRaises(Refusal)` to named refusals and adds the
   unreachable-by-design documentation + invariant pin; the
   task-abandon suite stays green and the number of named refusal
   assertions increases; no existing assertion is removed or loosened.
3. F4 lands as documentation only: no file outside this task's scopes
   changes; the finding names the exact current fail-open lines, the exact
   fail-closed replacement, and a runnable test sketch.
4. The full fleet suite from the repo root
   (`python -m unittest discover -s tools/agent_fleet -p 'test_*.py'`)
   is green at the delivery head; the exact count is reported with
   provenance whatever it is (baseline measured at base AFTER this
   registration, captured in this evidence dir). If the documented F2
   load-fragility fires under suite load, the recorded disposition is an
   isolation rerun of the flaky test with both outputs retained - the gate
   is not weakened either way.

## FALSIFIER

Any assertion removed or loosened (including the `lock_errors == 0`
assertion); any evidence file rewritten instead of appended (an existing
line or key of `RESULT.md` / `MEASUREMENT.json` changed); a followup
"fixed" by deleting the behavior it describes (e.g. the watchdog finding
delivered as a code edit outside scopes, or the unreachable refusals
"fixed" by deleting the refusal arms); any file outside this task's scopes
modified; the full fleet suite red at the delivery head without the
documented isolation-rerun disposition. Any of these and the task FAILS
regardless of how many corrections landed.

## Method notes (binding on the run)

- Scopes (registry-recorded): `docs/evidence/agent_fleet/SLOT_EXPANSION/`,
  `docs/evidence/agent_fleet/TASK_ABANDON/`,
  `tools/agent_fleet/test_task_abandon.py`,
  `docs/evidence/agent_fleet/FOLLOWUPS_BATCH_02/`. Nothing else.
- Evidence filenames `*.txt` only for run-output captures (the `*.log`
  gitignore trap); findings/prereg/result documents follow the dir
  convention (.md).
- `TASK_ABANDON/` receives a dated one-line append noting the F3 named-
  refusal completion (its test file changed); `SLOT_EXPANSION/` receives
  the F1/F2 appends.
- Prereg is this commit; implementation follows as its own commit(s); run
  outputs are captured only at the delivery head.
