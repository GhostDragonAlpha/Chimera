# GOV-01 evidence reconciliation — record

Task `gov01-evidence-reconcile-01`, generation 7, slot 2, worker
`subagent-worker-01`. Executed 2026-09-11 (UTC) in worktree
`E:\ChimeraWork\slot-02` on branch `astra/tasks/gov01-evidence-reconcile-01`.

## Method compliance

1. **Preregistration first**: `PREREGISTRATION.md` and `BINDING.json` were
   written before any reconciliation execution; they contain the packet's
   STATEMENT/PREDICTION/FALSIFIER, the exact commands, the negative-control
   table, and the source-identity hashes captured beforehand.
2. **Reads before runs**: worktree/branch/ownership verified against the
   controller snapshot (task state RUNNING, owner subagent-worker-01,
   generation 7, slot 2, base `7d3601e7…` verified ancestor of head
   `d012b4b1…`); read AGENTS.md/CLAUDE.md guidance, roadmap GOV-01 card,
   controller source (`control.py`, `service.py`, `run_queue.py`),
   controller tests, PR11 Windows evidence
   (`docs/evidence/agent_fleet/WINDOWS_LEAD_REVIEW_20260910/`), historical
   restart/claim/integration records (`BOOTSTRAP-LIVE-RESTART`,
   `FIVE-CLIENT-COORDINATION`, `SLOT_BINDING`, `THE_CONTROLLER_TRANSITION.md`,
   Master list rows).
3. **Existing tests only, private temporary registries**: no test was added,
   edited or weakened; every fixture builds its own TemporaryDirectory SQLite
   registry; no live controller/DB/slot process was touched; no GPU/DYAD/
   engine resource used (docs-only task; runtime NOT_APPLICABLE with reason
   recorded in the matrix).
4. **Raw evidence preserved**: verbatim combined stdout/stderr captured to
   `SUITE_RAW_OUTPUT.txt`; failures preserved as-is; counts parsed into
   `SUITE_SUMMARY.json`.

## Commands actually executed (worktree root)

```
git rev-parse HEAD                       -> d012b4b12ea2224d6b5669974776047238b76755
git status --porcelain                   -> (empty before run)
git merge-base --is-ancestor 7d3601e7... HEAD -> ancestor confirmed
git diff --stat 7d3601e7... HEAD -- tools/agent_fleet -> drift recorded in matrix preamble
python --version                         -> Python 3.14.3
python -B -m unittest discover -s tools/agent_fleet -p test_*.py -v
  (stdout+stderr -> SUITE_RAW_OUTPUT.txt; exit 1)
Get-FileHash SHA-256 over the 19 bound files (before AND after the run)
git status --porcelain                   -> only docs/evidence/master_completion/GOV01/ untracked
```

## Results

- **166 tests ran in 89.670 s**: 163 pass, 1 skip, 2 fail, 0 errors.
  Result-line accounting verified in the raw output (163+1+2 = 166).
- The only failures are the two **documented pre-existing**
  `test_master_catalogue` count pins (`…:665` 2540 != 2430 Master lines;
  `…:183` 76 != 65 master rows) — owned by the parallel master-catalogue
  lane per the task packet; not edited by this task. Zero controller-plane
  failures.
- The single skip is `test_unsafe_arguments_and_symlink_escape_refuse`
  (symlink creation unavailable on Windows) — environment limitation,
  consistent with prior Windows runs.
- Source hashes re-verified after the run: **0 mismatches** against
  `BINDING.json`; working tree contains only this evidence directory.
- Preregistered predictions: P1 **reproduced** (with exactly the documented
  pair as the only exceptions); P2 satisfied by
  `docs/GOV01_ACCEPTANCE.md` (every clause mapped or explicitly OPEN);
  P3 negative controls N1–N7 all executed and held.
- Falsifiers: **none triggered** (per-falsifier dispositions in the matrix).

## Limitations

Offline controller tests are not live-deployment/publication certification;
the running controller still uses its original operator-checkout source
(deployment unclaimed, per THE_CONTROLLER_TRANSITION.md and the PR11
record). Canonical GOV-01 acceptance is NOT_CLAIMED; slot 1 decides after
review and full catalogue import.

## Files in this directory

- `PREREGISTRATION.md` — written before execution (theory, commands, N1–N7)
- `BINDING.json` — base/head/branch + SHA-256 source identity
- `SUITE_RAW_OUTPUT.txt` — verbatim suite output (raw, not summarized)
- `SUITE_SUMMARY.json` — parsed counts and failure detail
- `RECORD.md` — this file
- `RESULT.md` — one-paragraph conclusion
