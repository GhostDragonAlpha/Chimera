# fleet-regression-sweep-01 — PREREGISTRATION

- task: fleet-regression-sweep-01, generation 1, slot 4 (E:/ChimeraWork/slot-04)
- agent: subagent-worker-07
- branch: astra/tasks/fleet-regression-sweep-01
- provisioned base: 5199d9c3015f6840b12186f34c3e0c2fd5d7b0a4 (PR #60 merge)
- reconciled sweep head (fast-forward merge of origin/astra/gait-capture, no force):
  4c31999797a9383ea252019be1f32511709fa280 ("Merge pull request #63", the
  4c319997-era tip this sweep names). Worktree clean at this head when this file
  was committed. 15 commits base..tip.
- written BEFORE any sweep command ran; contains no measured actuals.

## RULE 0 membrane

**STATEMENT** — The gates, contracts, and evidence commands merged by wave-2/3
(eleven PRs, #49–#64) pass at the current tip AS A SET; no lane's claim depends
on another lane's drift.

**PREDICTIONS** (from the packet and the per-lane records, all at tip):
1. Full fleet discover suite is green with exactly the one expected
   environment skip: 222 tests / 0 failures / 1 skip (`test_worktree_reconcile`
   symlink-creation skip on Windows).
2. Every per-lane decisive command re-runs clean at tip:
   - `python -m unittest tools.agent_fleet.test_worktree_reconcile -v` → 10 tests, 0 failures, 1 expected skip
   - `python -m unittest tools.agent_fleet.test_capture_window -v` → OK. The registry packet records the lane-era count as 19/19; the sweep dispatch records the tip-era count as 28/28 (wave commits grew the file: +269 lines at tip vs base). This sweep predicts the dispatch figure and treats either prior number as a prediction to falsify, not a tolerance: the ACTUAL count is recorded verbatim whatever it is, and the packet-vs-dispatch discrepancy is itself drift data.
   - `python -m unittest tools.agent_fleet.test_controller_transition -v` → 4/4
   - `python -m unittest tools.agent_fleet.test_client_instance -v` → 9/9
   - `python -m unittest tools.test_dyad_provider -v` → 14/14
   - `python -m unittest tools.agent_fleet.test_slot_expansion -v` → 5/5, on its own isolated temp registries (verified in source: `tempfile.TemporaryDirectory()`; the live service on 127.0.0.1 is never touched by this suite)
   - `python -m unittest tools.agent_fleet.test_task_abandon -v` → 19/19
   - `python -m unittest tools.agent_fleet.test_master_catalogue -v` (catalogue pins) → 23/23
   - `python -m unittest tools.test_orient_continuation -v` → 9/9
   - membrane CPU gate: `python tools/gpu_fixtures_verify.py` → exit 0, every check PASS, corrupt corner-order control DETECTED (this is exactly the `cpu_reference` check that tools/run_membrane_verification.py executes at line `run([sys.executable,"tools/gpu_fixtures_verify.py"], ROOT, cpu)`).
3. Any drift found is RETAINED as the finding. A falsified sweep is a result,
   not a failure.

**FALSIFIER** — drift hidden, tolerances widened, or a failing re-run not
reported verbatim. Concretely: any failing re-run, any count that moves from a
lane's recorded value, any skip that is not the one named expected symlink skip,
any suite exit code that is not 0 — each must appear in DRIFT_TABLE.txt with the
raw output retained, or this sweep's own claim is falsified.

## Method (fixed before the first run)

Run from the worktree root E:/ChimeraWork/slot-04 at the sweep head, `python`
(the host CPython 3.14), Windows Git Bash. Order:

1. Full fleet discover suite (README house command):
   `python -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v`
2. The ten per-lane decisive commands listed above, each captured raw.
3. Membrane CPU gate (see declared deviation D1).
4. Raw stdout+stderr of every command under this directory as `*.txt` only
   (never `*.log` — the fleet-evidence-hygiene-01 F1 ignore trap), plus
   DRIFT_TABLE.txt comparing prediction vs actual per command.

## Declared deviations (fixed before the run, not after)

- **D1 — membrane runner GPU stage.** tools/run_membrane_verification.py's
  normal mode builds and launches a standalone Vulkan compute probe against the
  host GPU. This task's safety envelope forbids GPU/model use, so the full
  runner is NOT executed here. The named CPU claim ("CPU PASS") is verified by
  running the runner's own cpu_reference command verbatim (same interpreter,
  same cwd, same argv as the runner uses), captured raw. The runner's other
  stages are NOT executed and NOT inferred. If a future re-run needs the full
  runner, it needs a GPU-qualified lane.
- **D2 — vulkan ownership suite "CPU-side tests".** The vulkan ownership lane's
  own record (docs/evidence/vulkan_resource_lifetime/RESULT.md) states the CPU
  ownership unit test is NOT_APPLICABLE ("engine internals are not
  CPU-unit-testable"); no CPU-side test file for it exists at tip. The sweep
  maps that packet line onto D1's CPU gate and records the mapping in the drift
  table rather than inventing a substitute command.
- **D3 — out-of-scope transient artifacts.** The CPU verifier writes its
  timestamped result JSON into docs/evidence/gpu_fixtures/ (outside this task's
  write scope). Each such file is copied into this evidence directory and then
  deleted from the out-of-scope location; the worktree is left clean at the
  final head. The copy is byte-identical; deletion is recorded in the drift
  table.
- **D4 — capture_window count discrepancy** packet 19/19 vs dispatch 28/28, as
  recorded under PREDICTIONS above; resolved by measurement, reported verbatim.

## Scope

docs/evidence/agent_fleet/REGRESSION_SWEEP_01 only. Pure verification: any fix
a drift motivates becomes a separate task; nothing outside this directory is
modified by the deliverable. The live control plane (E:/ChimeraWork/control,
port 8099/8765 service) and the operator checkout are never touched by any
sweep command.
