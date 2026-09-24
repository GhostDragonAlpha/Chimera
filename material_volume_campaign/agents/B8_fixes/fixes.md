# B8 receipt — M09 diagnostic CLI defect fixes (D1/D2/D3) + coverage gaps

Agent: B8 · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924`, branch
`material-volume-campaign-20260924`. Task: brief.md (verbatim copy in this
dir). Fix plan preregistered and FROZEN before any edit:
`preregistration_fixes.md`. Under fix: B2a ACCEPT-WITH-NOTES
(`agents/B2a_review_m09/report.md`) against
`material_volume_campaign/agents/M09_diagnostic/`. B2a's dir and its
`work/probes.py` were used READ-ONLY (verified below). Exclusive ownership of
`agents/M09_diagnostic/` exercised; writes confined to `agents/M09_diagnostic/`
and `agents/B8_fixes/`.

**Verdict: ALL THREE DEFECTS FIXED, failing-then-passing demonstrated, all
four coverage gaps closed, 17/17 tests green, genuine outputs byte-identical,
probes clean, integrity clean.**

## Method (frozen order, executed as frozen)

1. Tests written FIRST (new class `B8RegressionTests` + T9 hash-proof hooks;
   zero edits to existing T1–T11 assertions).
2. Pre-fix run: `receipts/tests_before_fix.log` — 17 tests, exactly the three
   D-regressions FAIL, all 11 originals + 3 gap tests green. F-B8.4 satisfied
   (no D-test passed pre-fix; each demonstrates its defect).
3. Fixes implemented (only `material_volume_diagnostic.py` touched).
4. Post-fix run: `receipts/tests_after_fix.log` — 17/17 OK. Repeated inside
   `run_suite.py`: verdict PASS.

## D1 — usage errors exited 2, colliding with frozen `2 = reader-rejected`

**Explanation (logged per campaign law).** The frozen contract
(`M09_diagnostic/preregistration.md`, "Exit codes (frozen)") mandates `0`
accepted / `2` reader-rejected / `4` alarm / "other nonzero — usage errors
(argparse)". argparse's default usage exit IS 2, so a bad invocation was
indistinguishable from a reader rejection by exit code alone. The contract is
unambiguous on the requirement (usage must be outside {0,2,4}); the specific
"other nonzero" value is unpinned by the frozen text, so no decision request
was needed. **DECISION RECORDED: usage errors exit 64** (BSD `sysexits.h`
`EX_USAGE` convention; nothing in this campaign keys on 64).

**Change** (`material_volume_diagnostic.py`): added `EXIT_USAGE = 64` and a
tiny `_UsageErrorParser(argparse.ArgumentParser)` overriding only `error()` to
`print_usage(sys.stderr)` + `self.exit(64, ...)` — stderr text byte-identical
to argparse's default, only the status differs; `main` constructs the parser
from the subclass. Docstring exit-code line updated. Reader paths untouched.

**Before/after evidence**
- Before (B2a `receipts/b2a_probes_receipt.txt` P7): `no arguments (usage):
  exit=2`, `bogus flag (usage): exit=2`.
- Before (in-suite): `AssertionError: 2 != 64` (`tests_before_fix.log`).
- After (in-suite, same test also re-pins malformed -> 2):
  `test_d1_usage_errors_exit_distinct_from_reader_rejection ... ok`.
- After (probe rerun, `receipts/b8_probes_rerun_receipt.txt` P7):
  `no arguments (usage): exit=64 stderr_first=usage: material_volume_diagnostic
  [-h] [--json] [--tools-dir TOOLS_DIR]` (usage TEXT unchanged),
  `bogus flag (usage): exit=64`, while `nonexistent path: exit=2` and
  `directory as path: exit=2` — reader-rejection semantics preserved.

## D2 — human-mode crash (AttributeError, exit 1 + traceback) on reader-accepted non-object `unassigned_cells` rows

**Explanation.** `render_human` called `row.get('cell_id')` on every
passthrough row; the reader does not validate `unassigned_cells` row types, so
a reader-accepted report with string rows crashed the human display path with
a traceback and exit 1 — an exit code outside the frozen contract. JSON mode
already passed rows through verbatim. The frozen grammar has no production for
a non-object row, so any non-crashing render necessarily emits a token outside
the frozen per-row grammar; the chosen marker (`<non-object row: <repr>>`)
names the row's TYPE and prints the value verbatim — it never invents a
cell_id/status (F3 discipline) and is the human mirror of the JSON
passthrough.

**Change**: in `render_human`'s row loop, `isinstance(row, Mapping)` renders
the frozen grammar line unchanged; any other row renders
`unassigned[<i>] <non-object row: {row!r}>`. Count line unchanged.

**Before/after evidence**
- Before (B2a probes P5): `human: exit=1 crash=True`,
  `LAST_ERR=AttributeError: 'str' object has no attribute 'get'`.
- Before (in-suite): `AssertionError: 1 != 0` (`tests_before_fix.log`).
- After (probe rerun P5): `json: exit=0 crash=False`, `human: exit=0
  crash=False`, rendering `unassigned[0] <non-object row: 'cell-B'>`,
  `unassigned[1] <non-object row: 'cell-C'>`, `readiness: false`.
- After (in-suite): `test_d2_string_unassigned_cells_rows_render_gracefully
  ... ok` (also pins JSON passthrough `["cell-B","cell-C"]` unchanged).

## D3 — string `unassigned_cell_ids` mangled per-character

**Explanation.** `_plural_list` iterates any `Sequence`; a `str` IS a
`Sequence`, so a reader-accepted bare-string `unassigned_cell_ids` rendered
per character (`c, e, l, l, -, B`) — the exact mangle class M09's report says
was "fixed and locked" for the sibling field `blocking_assignment_statuses`.
Genuine exporter output always carries lists, so this is hostile-input-only.

**Change**: one guard at the top of `_plural_list` —
`if isinstance(values, str): values = [values]` — closing the defect CLASS at
every call site (unassigned IDs, frames, units, reason codes, blocking lists,
top-level reason codes) by joining whole values.

**Before/after evidence**
- Before (B2a probes P4): `unassigned_cell_ids: c, e, l, l, -, B`.
- Before (in-suite): `'unassigned_cell_ids: cell-B' not found in ...`
  (with the mangle visible in the logged stdout) (`tests_before_fix.log`).
- After (probe rerun P4): `unassigned_cell_ids: cell-B`, `json: exit=0`,
  `human: exit=0`.
- After (in-suite): `test_d3_string_unassigned_cell_ids_not_mangled ... ok`
  (asserts the whole value AND `assertNotIn("c, e, l, l")`; pins JSON
  passthrough `"cell-B"` unchanged).

## Coverage gaps closed (B2a's list)

- **Exit-4 readiness-alarm path** — `test_exit4_readiness_alarm_path`: mocks
  the reader's public `summarize_export_report` (the only seam; the real
  reader hard-codes readiness false, making the alarm unreachable on genuine
  input) to force `dynamics_readiness_claimed = True`: returns 4, stderr
  carries `READINESS-VIOLATION`, JSON top-level `readiness` stays `False`,
  human final line stays `readiness: false`. Green before AND after (pins
  existing honest behavior).
- **Mixed accepted+rejected invocation** — `test_mixed_accepted_and_rejected_
  invocation`: `[complete, malformed_version]` -> exit 2, argv order pinned,
  rejected entry carries `error.reason` and NO summary fields, human mode
  shows both entries with final `readiness: false`.
- **`(not reported)` grammar token** — `test_unassigned_cells_not_reported_
  token`: reader-accepted report with the `unassigned_cells` key deleted ->
  human contains the literal token `unassigned_cells: (not reported)`, JSON
  entry has no `unassigned_cells` key, exit 0.
- **T9's second half (hash proof) moved in-suite** — `AcceptanceTests.
  setUpClass` snapshots SHA-256 + `st_mtime_ns` of every file under `tools/`
  and `Chimera/docs/matter` (same roots as `run_suite.snapshot`), and
  `tearDownClass` asserts identical — the snapshot straddles every CLI
  subprocess the whole suite spawns. Passed on every run (the 415-file
  run_suite proof independently confirms: `before_after_identical=True,
  files_snapshotted=415, added=0, removed=0, changed=0`).

## Suite results (old + new; nothing weakened)

- Pre-fix (`receipts/tests_before_fix.log`): `Ran 17 tests ... FAILED
  (failures=3)` — exactly `test_d1` (2 != 64), `test_d2` (1 != 0), `test_d3`
  (mangle in output); T1–T11 + 3 gap tests green.
- Post-fix (`receipts/tests_after_fix.log`): `Ran 17 tests ... OK`.
- `run_suite.py` (`receipts/run_suite_b8.log`): `Ran 17 tests ... OK`,
  read-only proof identical (415 files), git integrity empty,
  `M09 suite verdict: PASS`.
- Honest intermediate failure preserved: my first attempt at inserting the new
  helpers accidentally dropped the `def run_cli(...)` signature line
  (NameError x15); repaired immediately; log preserved verbatim as
  `receipts/tests_edit_mistake_run1_preserved.log`.
- F-B8.2 (no genuine-output byte changed): pre-fix `receipts/
  output_samples_before_fix.txt` vs post-fix regenerated
  `M09_diagnostic/receipts/output_samples.txt` — SHA-256 identical
  (`de0fdc5e9c11877e58b14c0e4f1ab29fb1161b9004af459a566ac4b0d8286233`).

## B2a probes re-run against the fixed CLI (probes.py untouched, READ-ONLY)

`work/probes_rerun.py` is a verbatim adaptation of B2a's `probes.py`; only the
CLI path (now the fixed committed CLI), the fixture dir (regenerated under
`B8_fixes/work/probes/`, same generator code), and the receipt destination
differ. Full transcript: `receipts/b8_probes_rerun_receipt.txt`. Result vs
B2a's `b2a_probes_receipt.txt`:

| Probe | B2a (pre-fix) | B8 rerun (post-fix) |
|---|---|---|
| P1 empty body_groups | clean, exit 0 | clean, exit 0 (unchanged) |
| P2 all-omitted minimal | clean, exit 0 | clean, exit 0 (unchanged) |
| P3 out-of-vocab body status | reader REJECTED `blocked_group_has_mass`, exit 2 | identical (unchanged) |
| P4 string `unassigned_cell_ids` | human mangle `c, e, l, l, -, B` | `unassigned_cell_ids: cell-B` — FIXED |
| P5 string `unassigned_cells` rows | human `exit=1 crash=True` AttributeError | `exit=0 crash=False`, verbatim `<non-object row: ...>` — FIXED |
| P6 depth-2000 reason_codes | clean, exit 0 both modes | clean, exit 0 both modes (unchanged) |
| P7 usage errors | exit 2 (the collision) | exit 64, usage text unchanged — FIXED; reader rejections still exit 2 |

## Falsifier ledger (from the frozen preregistration)

- F-B8.1 (existing test weakened/red): NOT HIT — T1–T11 untouched, green in
  every post-fix run.
- F-B8.2 (genuine-output byte changed): NOT HIT — SHA-256-identical samples.
- F-B8.3 (write outside my dirs / tools+docs change): NOT HIT — integrity
  paste below empty; full porcelain shows only my two files + new fixtures +
  `B8_fixes/`; no `__pycache__` under `tools/`.
- F-B8.4 (a D-test passing pre-fix): NOT HIT — all three failed pre-fix.

## Integrity paste

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty; exit 0)
```

Full porcelain after all runs (write inventory — exclusively M09 + B8):

```
 M material_volume_campaign/agents/M09_diagnostic/material_volume_diagnostic.py
 M material_volume_campaign/agents/M09_diagnostic/tests/test_material_volume_diagnostic.py
?? material_volume_campaign/agents/B8_fixes/
?? material_volume_campaign/agents/M09_diagnostic/work/fixture_hostile_no_unassigned_cells.json
?? material_volume_campaign/agents/M09_diagnostic/work/fixture_hostile_string_ids.json
?? material_volume_campaign/agents/M09_diagnostic/work/fixture_hostile_string_rows.json
```

`git status --porcelain -- material_volume_campaign/agents/B2a_review_m09`
-> empty (B2a dir untouched; `probes.py` read, never written). M09 receipts
regenerated by `run_suite.py` came out byte-identical to the committed ones
(hence absent from porcelain) — expected, since genuine outputs are unchanged.

Note: worktree HEAD moved `35d909e7` -> `9848cece` during this task (parallel
B7x integration commit, not a B8 write); integrity checks above were run
after it. My diffs are relative to the same two files throughout.

Nothing committed — integration/commit is the coordinator's call.
