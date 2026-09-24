# tools/tests/material_volume — landed suites (W7 publication, 2026-09-24)

The two reviewed material-volume tools (`tools/material_volume_diagnostic.py`,
`tools/rigid_body_mass_consumption_validator.py`) plus their 7-module closure
(`material_volume*.py`) and these test suites + fixtures are the W5/W6 packages
published onto the game lineage. The tool and closure files are byte-identical
to their reviewed sources (hashes:
`tools/monkey_campaign/agents/W7_landing/receipts/landed_fixture_hashes.json`
and the W7 report); only the tests carry path adaptations (ledger in the W7
report; diffs in `receipts/test_path_adaptations.diff`).

## Canonical run command (from the worktree root)

```bash
CHIMERA_TOOLS_DIR=<worktree>/tools PYTHONDONTWRITEBYTECODE=1 \
    python -m pytest tools/tests/material_volume/ -v
```

Concrete (this worktree):

```bash
CHIMERA_TOOLS_DIR=E:/ChimeraWork/monkey-play-20260924/tools \
PYTHONDONTWRITEBYTECODE=1 \
python -m pytest tools/tests/material_volume/ -v
```

Environment requirements, and why:

- `CHIMERA_TOOLS_DIR=<worktree>/tools` — REQUIRED. The validator resolves its
  reader for the R0 cross-check via `CHIMERA_TOOLS_DIR` or
  `parents[3]/"tools"` (its home layout). Landed one level deep, the ancestor
  arithmetic cannot reach `tools/`, and the validator is hash-frozen (zero
  behavior edits), so the env var is the legal pin. Without it the reader
  cross-check degrades to `{"ran": false}` and
  `test_reader_cross_check_passes_on_accept` fails.
- `PYTHONDONTWRITEBYTECODE=1` — REQUIRED for the frozen falsifiers to hold in
  their strict form: T9/F1 forbid `__pycache__` under the material-volume
  surface of `tools/`. The env var arms the flag interpreter-wide (before any
  import), so no bytecode is written anywhere, including the test dir itself.
  `conftest.py` also sets `sys.dont_write_bytecode` before any tools/ import as
  a second belt.
- `M09_TOOLS_DIR` — NOT required. The diagnostic self-locates `tools/` by
  walking ancestors from its own file (it sits inside `tools/`); the env var
  remains supported as an optional override.
- CPU-only; the only third-party imports are pytest and numpy.

Expected: 118 passed (W6 validator suite: 101 — test_validator +
test_w6_con16_aggregate + test_w6_exit_classes + test_w6_fullreport_mvb31 +
test_w6_hash_scope_mvo1 + test_w6_reconciled_records; W5 diagnostic suite: 17 —
test_material_volume_diagnostic). Receipts:
`tools/monkey_campaign/agents/W7_landing/receipts/`.

## Layout

- `test_material_volume_diagnostic.py` — W5 suite (17 tests). Generates its own
  fixtures at runtime from the shipped examples into `work/` (created here;
  the landed surface's only sanctioned write location besides this dir).
- `test_validator.py`, `test_w6_*.py` — W6 suite (101 tests).
- `fixtures/` — the W6 frozen fixture battery (55 JSON) plus the two fixture
  generators (`make_fixtures.py`, `make_genuine_blocked_fixture.py`), landed
  byte-identical from the reviewed source package.
- `conftest.py` — landing shim: puts `tools/` on sys.path and arms the
  bytecode guard. No test import was edited for module resolution.

Shipped examples the suites read (landed byte-identical from the reviewed mv
worktree; the W7-declared new tools/ paths):

- `tools/material_volume_body_export_example_report.json`
- `tools/material_volume_body_export_manifest_example.json`
- `tools/material_volume_body_export_partition_example.json`
- `tools/material_volume_body_export_groups_example.json`

## Landed-layout caveat (shared worktree)

The two preregistered falsifiers that scan the whole `tools/` tree assume the
quiet single-campaign home tree. In this shared worktree:

- `test_t9_no_pycache_in_tools` is scoped (path-scope adaptation, documented)
  to the tools/ TOP level — where all landed material-volume bytecode would
  land. Pre-existing nested `__pycache__` dirs of other campaigns
  (`tools/creature_graph/`, `tools/monkey_campaign/`, `tools/science_funnel/`)
  are outside the M09/M10 surface; NEW pycache anywhere under tools/ mid-suite
  is still caught by the F1 tree snapshot in `tearDownClass`.
- The F1 snapshot (AcceptanceTests teardown) compares every file under `tools/`
  + `Chimera/docs/matter` across the suite window. Concurrent writes by OTHER
  live campaign lanes into `tools/monkey_campaign/**` during that window trip
  it exogenously (observed: a sibling agent's `brief.md` landing mid-run). All
  118 tests still pass; re-run in a quiet window for an error-free receipt.
