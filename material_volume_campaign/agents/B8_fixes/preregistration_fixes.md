# B8 preregistration — M09 diagnostic CLI defect fixes + coverage gaps

Frozen: 2026-09-24, BEFORE any edit to `agents/M09_diagnostic/`.
Scope of writes: `material_volume_campaign/agents/B8_fixes/` and
`material_volume_campaign/agents/M09_diagnostic/` ONLY. `tools/` and
`Chimera/docs/matter` stay READ-ONLY. Under review: B2a ACCEPT-WITH-NOTES
(`agents/B2a_review_m09/report.md`) against the M09 CLI at worktree HEAD
`35d909e7` (branch `material-volume-campaign-20260924`).

## THEORY (Rule 0)

- **STATEMENT**: The three B2a defects (D1 usage-exit collision, D2 human-mode
  crash on non-object `unassigned_cells` rows, D3 per-character mangle of a
  string `unassigned_cell_ids`) are display/exit-path defects in the CLI's own
  code, each fixable with a minimal, local change that keeps the frozen JSON
  contract, the frozen human grammar for genuine reports, and every existing
  test byte-for-byte intact.
- **PREDICTION** (untested until the runs below): (a) remapping argparse usage
  errors to exit 64 leaves every reader-path exit code (0/2/4) and all stderr
  usage TEXT unchanged; (b) guarding non-Mapping rows and joining whole
  strings changes NO byte of human or JSON output for any genuine exporter
  report — the existing 11 tests stay green with zero edits to their
  assertions; (c) B2a probes P4/P5/P7 flip exactly: P4 renders `cell-B` whole,
  P5 renders rows gracefully at exit 0 in both modes, P7 usage errors no
  longer return 2.
- **FALSIFIERS** (named before the run; any hit = stop and re-diagnose):
  - F-B8.1: any existing test (T1–T11) weakens, changes an assertion, or turns
    red after the fix.
  - F-B8.2: any byte of human/JSON output for the GENUINE fixtures (complete/
    partial/blocked/unsupported/refused/malformed) changes vs the pre-fix
    outputs (`M09_diagnostic/receipts/output_samples.txt`). Hostile-path
    outputs changing IS the fix and is expected.
  - F-B8.3: any write outside `agents/B8_fixes/` and `agents/M09_diagnostic/`;
    any change under `tools/` or `Chimera/docs/matter`
    (`git status --porcelain -- tools Chimera/docs/matter` must stay empty).
  - F-B8.4: any D-regression test PASSES on the pre-fix CLI (a regression test
    that cannot fail does not demonstrate the defect — the test or the defect
    claim is wrong).

## D1 — argparse usage errors exit 2, colliding with frozen `2 = reader-rejected`

Evidence: B2a report Area 2 + Area 4 P7; `receipts/b2a_probes_receipt.txt`
L48–49 (no-args -> 2, `--bogus-flag` -> 2).

**Contract reading**: `agents/M09_diagnostic/preregistration.md`, "Exit codes
(frozen)": `0` accepted / `2` reader-rejected / `4` readiness alarm / "other
nonzero — usage errors (argparse)". The contract is UNAMBIGUOUS on the
requirement: a usage error must not return 0, 2, or 4. The specific "other
nonzero" value is deliberately unpinned by the frozen text, so choosing it is
authorized and is NOT a decision request. **DECISION (recorded)**: exit `64` —
the BSD `sysexits.h` `EX_USAGE` convention; outside {0, 2, 4}; nothing in this
campaign keys on 64.

**Minimal fix**: one tiny `argparse.ArgumentParser` subclass overriding
`error()` to `print_usage(sys.stderr)` then `self.exit(64, "{prog}: error: ...
")` — stderr text byte-identical to argparse's default, only the status
changes; the parser construction call switches to the subclass. Reader paths
untouched.

**Regression test (must FAIL pre-fix, PASS post-fix)**:
`test_d1_usage_errors_exit_distinct_from_reader_rejection` — `run_cli([])`
(no args) returns 64 with stderr starting `usage:`; `run_cli([complete,
"--bogus-flag"])` returns 64; and in the SAME test `run_cli([malformed_version])`
still returns 2, so the fix cannot be achieved by remapping the rejection code.

## D2 — human-mode crash (AttributeError, exit 1 + traceback) on reader-accepted non-object `unassigned_cells` rows

Evidence: B2a Area 4 P5; probes receipt L31–34 (`render_human` L205-208,
`row.get` on a `str`).

**Minimal fix**: in `render_human`'s row loop, guard
`isinstance(row, Mapping)`: mapping rows render the frozen per-row grammar
line unchanged; any other row renders
`unassigned[<i>] <non-object row: <repr>>` — the value verbatim (`!r`, so
string vs number is unambiguous), never treated as a `cell_id` (no field-value
invention; F3 discipline), never iterated per character. The count line
(`unassigned_cells: <count|(not reported)>`) is unchanged — `len()` of the
passthrough list is still the row count. JSON mode already passes such rows
through verbatim; this is the human mirror of that behavior.

**Why a new token is unavoidable**: the frozen grammar has no production for a
non-object row, so any non-crashing render must emit text outside the frozen
per-row grammar. The marker names the row's TYPE, not any contract field or
status.

**Regression test (must FAIL pre-fix, PASS post-fix)**:
`test_d2_string_unassigned_cells_rows_render_gracefully` — fixture: genuine
exporter `build_export_report` output with `unassigned_cell_ids =
["cell-B","cell-C"]`, `unassigned_cells = ["cell-B","cell-C"]`
(reader-acceptance asserted via public `summarize_export_report` BEFORE the
CLI runs); human run: exit 0, no `Traceback` in stderr, stdout contains
`unassigned_cells: 2`, `<non-object row: 'cell-B'>`,
`<non-object row: 'cell-C'>`; JSON run: rows pass through verbatim
(`["cell-B","cell-C"]`), exit 0.

## D3 — string `unassigned_cell_ids` mangled per-character (`str` is a `Sequence`; `_plural_list` iterates characters)

Evidence: B2a Area 4 P4; probes receipt L22–30 (`c, e, l, l, -, B`). Same
defect class M09 locked for `blocking_assignment_statuses`.

**Minimal fix**: in `_plural_list`, treat a `str` as ONE value:
`if isinstance(values, str): values = [values]` — joins whole values, closes
the class at every call site (`unassigned_cell_ids`, frames, units,
reason_codes, blocking lists, top-level reason codes) with one line. Genuine
reports always carry lists, so no genuine output changes.

**Regression test (must FAIL pre-fix, PASS post-fix)**:
`test_d3_string_unassigned_cell_ids_not_mangled` — fixture: genuine exporter
output with `unassigned_cell_ids = "cell-B"` (reader-acceptance asserted
first); human run: exit 0, stdout contains `unassigned_cell_ids: cell-B` and
NOT the per-character mangle signature `c, e, l, l`; JSON run:
`entry["unassigned_cell_ids"] == "cell-B"` (raw passthrough unchanged).

## COVERAGE GAPS (tests to ADD)

- **G-exit4** `test_exit4_readiness_alarm_path`: in-process `diag.main` with
  `unittest.mock.patch.object(reader, "summarize_export_report", ...)` wrapping
  the real function and forcing `dynamics_readiness_claimed = True` on the
  complete fixture. Assert: return value 4, stderr contains `READINESS-VIOLATION`,
  JSON top-level `readiness` is `False` (the F2 sentinel stays false), and the
  human run's final line is `readiness: false`. Pins the alarm path
  (unreachable with the real reader, by its construction) and its precedence.
- **G-mixed** `test_mixed_accepted_and_rejected_invocation`: one invocation
  `[complete, malformed_version]`: JSON exit 2; `reports[0]` ok/`complete`;
  `reports[1]` ok=false with `error.reason == "bad_export_report_version"` and
  NO summary fields (`export_status`, `schema_version`, `input_hashes`
  absent); entry order == argv order; human run: exit 2, contains both
  `export_status: complete` and `error_reason: bad_export_report_version`,
  final line `readiness: false`.
- **G-notreported** `test_unassigned_cells_not_reported_token`: fixture:
  genuine exporter output with the `unassigned_cells` key DELETED
  (reader-acceptance asserted first — verified 2026-09-24 pre-freeze:
  `summarize_export_report` ACCEPTS). Assert human stdout contains the literal
  token `unassigned_cells: (not reported)`; JSON entry has NO
  `unassigned_cells` key; exit 0. Locks the third grammar token B2a found
  untested.
- **G-hashproof** (T9's second half, moved in-suite where feasible): a tree
  snapshot (SHA-256 + `st_mtime_ns` of every file under `tools/` and
  `Chimera/docs/matter`, same roots as `run_suite.snapshot`) taken in
  `AcceptanceTests.setUpClass` (after fixture generation) and re-taken +
  asserted identical in `tearDownClass` — so the snapshot straddles every
  CLI subprocess the whole suite spawns, which is the strongest in-suite form
  of the preregistered T9 proof. No existing assertion is touched; only the
  two hooks are added.

Gap tests pin honest current behavior and are expected GREEN before AND after
the fixes, except insofar as they exercise fixed paths (none do: exit-4,
mixed, `(not reported)`, and hash paths are all defect-free today).

## EXECUTION ORDER (frozen)

1. Add ALL new tests (no edits to existing tests).
2. Run the suite; capture the three D-regressions FAILING and the gap tests
   GREEN on the pre-fix CLI. Preserve log: `receipts/tests_before_fix.log`.
3. Implement the three fixes in `material_volume_diagnostic.py` (nothing else).
4. Rerun the full suite -> all green; log: `receipts/tests_after_fix.log`.
5. Rerun the B2a probes against the FIXED CLI via
   `B8_fixes/work/probes_rerun.py` (a copy of B2a's `probes.py` with only the
   CLI path and receipt destination changed; `probes.py` and everything else
   under `B2a_review_m09/` stays READ-ONLY). Require P4/P5/P7 clean; receipt:
   `receipts/b8_probes_rerun_receipt.txt`.
6. Run `M09_diagnostic/run_suite.py` for the regenerated read-only proof +
   M09 receipts (415-file snapshot, U7 probe, output samples).
7. Write `B8_fixes/fixes.md`: per change, explanation + before/after evidence
   + probe outputs + integrity paste
   (`git status --porcelain -- tools Chimera/docs/matter` -> empty).

FROZEN AT: 2026-09-24, before the first edit to `agents/M09_diagnostic/`.
