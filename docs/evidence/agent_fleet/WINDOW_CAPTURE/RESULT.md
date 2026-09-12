# RESULT — window-capture-ownership-02 (fresh-system re-verification)

Worker `subagent-worker-02`, slot-03, generation 1. Base
`4604de40bd6cdd02d3cc277019f8bac5030c2dbe`, branch
`astra/tasks/window-capture-ownership-02`, PR base `astra/gait-capture`.
Preregistration committed BEFORE any run: `PREREGISTRATION.md` (commit
`c55a8383`). Acceptance: **NOT_CLAIMED**.

## Verdict

The inherited owned-client Windows capture contract (from
`window-capture-ownership-01`, `00a556b3`, merged additively as `e8705580`)
holds on this fresh system — every falsifier check came back untriggered
after REAL fixture exercises. **Acceptance is NOT claimed by this worker.**

## Verification table (PREDICTION → measured → result)

| Case | Prediction | Measured | Result |
|---|---|---|---|
| (a) unobscured owned | `unobscured`, publishable, capture == expected full matrix | sha match, full-matrix equality, pid owned | PASS |
| (a2) distinct content | distinct known solid contents each exact, distinguishable | red `5fcbf650…` ≠ blue `da076b0e…`, both `unobscured` | PASS |
| (b) overlapped | window-specific path reads the window's own surface; content deviation fails closed | overlap present, capture sha == expected sha | PASS |
| (b2) real cross-window mismatch | live hwnd vs other fixture's pattern → `occluded_or_foreign_content` | verdict `occluded_or_foreign_content`, publishable false (REAL windows) | PASS |
| (c) resized | real client ≠ pinned → `window_resized` with both sizes | client [200,110] vs pinned [120,70], publishable false | PASS |
| (d) destroyed / stale | `window_destroyed`; stale hwnd capture refused, never fallback | verdict `window_destroyed`; capture refused `stale_or_invalid_handle` | PASS |
| (e2) REAL foreign process | child-process fixture refused on pid even with known matching content | child pid 56876 ≠ capturing pid 64712, class owned, visible, content matching, verdict `foreign_process`, publishable false | PASS |
| (f2) client rect excludes nonclient | captured extent == pinned client; outer chrome strictly larger | client 120x90 vs outer 136x129; captured matrix [90,120] | PASS |
| (g) no screen fallback; no overwrite | no `CreateDC*`/`GetWindowDC`/`GetDCEx`/`GetDC(NULL)` (AST); `PrintWindow` present; evidence overwrite refused | AST test passed; `evidence_overwrite_refused=true`, bytes identical | PASS |

FALSIFIER check: none triggered (foreign pixels publishable / stale HWND or
PID accepted / desktop fallback / evidence overwritten / unknown windows
touched / point sampling — all false). Raw: `RAW_MEASUREMENT_OUTPUT.txt`,
structured: `MEASUREMENT.json`.

## Fresh-system finding (fixed, in scope)

The inherited module crashed with `ctypes` `OverflowError` at
`CreateCompatibleDC`/`CreateDIBSection` when the window DC handle exceeded
2^31-1 — GDI hands out such values on this system; the prior attempt passed
only because its session drew smaller handle values. Fixed by declaring
handle prototypes (`argtypes`), so every path returns a NAMED fail-closed
verdict. This is exactly what fresh-system re-verification is for.

## Test results (from repo root)

- `python -m unittest tools.agent_fleet.test_capture_window -v`
  → **17/17 OK** (12 inherited + 5 fresh). Raw: `RAW_TESTS_OUTPUT.txt`.
- `python -m unittest discover -s tools/agent_fleet -p 'test_*.py'`
  → 183 tests, **2 failures, 1 skip**. Raw: `RAW_FLEET_SUITE_OUTPUT.txt`.

The packet's expected baseline was "0 failures, 1 Windows-symlink skip". The
skip is as expected (`test_worktree_reconcile` symlink creation unavailable
on Windows). The 2 failures (`test_master_catalogue`:
`2584 != 2540` pinned catalogue lines; `82 != 76` pinned master_row_ids)
**pre-exist at base and are not caused by this branch**: `git diff
--name-only 4604de40..HEAD` touches only this task's scope files, and the
failing assertions plus their inputs (`THE_MASTER_LIST.md`,
`master_catalogue.py`, `test_master_catalogue.py`) are bit-identical between
base and head, so the outcome at base is identical — the canonical Master
list has grown past the pinned counts in recently integrated PRs. Those
files are outside this task's write scope; nothing was weakened, tolerated,
or fixed here. Recommendation: the catalogue lane should re-pin the counts
against the canonical Master.

## NOT_CLAIMED / open gates

- **Acceptance NOT_CLAIMED** — lead review and authorized integration are
  separate gates.
- No GPU work, no model loads, no engine build, no runtime was exercised:
  this contract is CPU/GDI and says nothing about GPU submission linkage.
- Engine-render capture vs screen presentation: this verifies the window's
  own surface; it is NOT a certificate of on-screen presentation (and screen
  occlusion cannot enter a record — both directions stated in the doc).
- `native_run.py` remains evidence of a manual run, not a general capture
  API; this module is the bounded contract.
- The inherited `RUN_RECORD.json` (-01) is retained untouched next to this
  run's files.
