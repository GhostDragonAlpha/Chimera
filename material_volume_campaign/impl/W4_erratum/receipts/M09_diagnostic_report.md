# M09 report — READ-ONLY diagnostic CLI on the body-export reader

Agent: M09 · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924` (branch
`material-volume-campaign-20260924`, base `3db8bc4e`) · campaign dir
`material_volume_campaign/agents/M09_diagnostic/`

**Verdict: ACCEPTED by my own acceptance suite — 11/11 tests pass, all three
falsifiers clean, read-only proof clean, repo integrity clean. No commit made
(not requested; promotion into tools/ is a coordinator decision).**

## What was built

`material_volume_diagnostic.py` — a read-only CLI: given one or more
`chimera.rigid_body_mass_export.v1` report paths it displays, per report: the
reader-validated `export_status`; EVERY omitted (non-`exported`) body with its
reason codes plus the contract's preserved blocking diagnostics
(`blocking_cell_ids`, `blocking_assignment_statuses`,
`admission_reason_codes`); unassigned cell IDs AND their per-cell
`unassigned_cells` rows (cell_id / assignment_status / reason); frames; units;
masses of exported bodies; top-level `reason_codes`/`detail`; and readiness
shown as-is — always `false`. Human-readable default, `--json` for machines,
`--tools-dir`/`M09_TOOLS_DIR` for reader location. Exit codes: 0 = every
report accepted (any of the five statuses is a successfully *diagnosed*
report, incl. `refused`); 2 = reader rejected a report; 4 = readiness
violation alarm (never fired).

Preregistration (output contract + test plan + falsifiers) was frozen in
`preregistration.md` BEFORE the implementation file existed.

## Implementation is on the reader's public interface — functions called

- `material_volume_body_export.read_json_file(path)` — ALL file parsing
  (strict: duplicate keys and NaN/Infinity constants rejected). No re-parsing.
- `material_volume_body_export_reader.summarize_export_report(report)` — ALL
  validation; the ONLY source of statuses, per-body summaries, readiness.
- `material_volume_body_export_reader.canonical_json(payload)` — machine
  output serialization.
- `material_volume_body_export.ExportInputError` (`.reason`/`.detail`) —
  reader-rejection surfacing; `material_volume_body_export.EXPORT_SCHEMA` —
  schema constant.
- Test fixtures call `material_volume_body_export.build_export_report(...)` —
  the exporter's own public function — on mutated IN-MEMORY copies of the
  shipped example manifest/partition/groups, so every fixture is a GENUINE
  exporter output; fixture bytes are written only under `work/` in my dir.
- The raw reader-parsed mapping is used only to pass through, for DISPLAY,
  fields the reader summary drops. Nothing is re-validated; no status is
  invented; nothing is promoted.
- Reader import path: the worktree's `tools/` is put on `sys.path` directly
  (no byte-copy needed); `sys.dont_write_bytecode = True` is set BEFORE the
  import so no `__pycache__` can be written into `tools/`. Everything ran
  under `PYTHONDONTWRITEBYTECODE=1` as well.

## Test receipts (receipts/test_run.log, final run)

```
Ran 11 tests in 3.643s
OK
M09 suite verdict: PASS (tests: 11 run, 0 failures, 0 errors)
```

- T1 happy path, shipped example `tools/material_volume_body_export_example_report.json`
  (READ-ONLY): `complete`, 2 exported bodies (coupon-body-A 2.0 kg,
  coupon-body-B 1.0 kg), 0 omitted, frames {coupon-A-authored,
  coupon-B-authored}, units {kg, kg*m^2, m}, readiness false.
- T2 unassigned-cells case: genuine exporter `partial` (body-B group dropped) —
  `unassigned_cell_ids: ["cell-B"]`, row `cell-B / resolved /
  not_assigned_to_an_authored_body_group` surfaced from the raw report.
- T3 omitted-bodies case: genuine `blocked` (region-B → unknown material) —
  both bodies `not_exported` with `reconstructed_mass_admission_required`;
  body-B's blocking cell `cell-B` (status `invalid_material_reference`) and
  admission reason codes (`compiler_refusal:missing_material`, …) surfaced;
  no mass fields for omitted bodies.
- T4 refused case: genuine `refused` (empty body_id) —
  `top_level_reason_codes: ["bad_identifier"]`, `detail:
  "body_groups[0].body_id must be a non-empty string"` surfaced; exit 0
  (diagnosed, not a CLI failure).
- T5 unsupported case: genuine `unsupported` (source-effective segment
  authority) — both bodies omitted with
  `source_effective_segment_mass_unsupported`; readiness false.
- T6 malformed ×2: wrong `schema_version` → `bad_export_report_version`;
  duplicate JSON key → `duplicate_json_key`; both `ok: false`, exit 2.
- T7 (F2) readiness: `readiness_claimed: false` and final line
  `readiness: false` in every accepted case, human + JSON.
- T8 (F3) status invention: every displayed root/per-body status equals both
  the raw report value and the reader summary value; omitted bodies never
  `exported`.
- T9 (F1) read-only: see proof below.
- T10 exit codes: 0 for all five genuine statuses; 2 for malformed.
- T11 human grammar on blocked incl. the corrected
  `blocking_assignment_statuses=cell-B:invalid_material_reference` rendering.
- Fixture authenticity asserted in-suite: `build_export_report` on the
  unmutated example inputs reproduces the shipped example report exactly.

## Falsifier results

- F1 (writes/modifies inputs): CLEAN. Full SHA-256 + st_mtime_ns snapshot of
  `tools/` + `Chimera/docs/matter` (415 files) before vs after the entire
  suite: identical — `added=0, removed=0, changed=0`
  (receipts/read_only_proof.json). No `__pycache__` in `tools/` (T9).
- F2 (displays readiness != false): CLEAN — exit-4 alarm never fired; T7.
- F3 (invents a status): CLEAN — T8.
- Defect found and fixed in MY tool during the campaign: the human renderer
  passed the already-joined `blocking_assignment_statuses` string back into
  the list renderer, producing per-character output; fixed and locked with a
  test assertion (T11). JSON output was never affected.

## U7 finding — reader behavior on blocked/refused (preserved, NOT fixed)

Probe: the reader's own CLI (`tools/material_volume_body_export_reader.py`)
run on genuine blocked/refused fixtures (receipts/u7_reader_probe.txt).

1. **No misbehavior.** Reader exits 0, no stderr, correct
   `export_status` (`blocked` / `refused`), `dynamics_readiness_claimed` stays
   `False`, malformed group masses and unknown statuses are still rejected.
   U7's fear (reader crashing or corrupting on blocked/refused) is not
   realized at this base.
2. **Finding (summary thinning, not a defect):** the reader's summary drops
   diagnostics the contract says to preserve — for `blocked` bodies,
   `blocking_cell_ids` / `blocking_assignment_statuses` /
   `admission_reason_codes` (CON-4) are absent from summary body entries; for
   `refused` reports, top-level `reason_codes` and `detail` (CON-6) are absent
   from the summary; per-cell `unassigned_cells` rows (CON-7) are reduced to
   bare IDs. The M09 CLI compensates by passing these through from the raw
   reader-parsed mapping for display only — a consumer relying on the reader's
   summary alone would lose the blocking-cell attribution. If the coordinator
   ever extends the reader summary, my tests T3/T4 pin today's behavior and
   would flag the change.
3. **Exporter semantic observed and locked (not a defect):** with a
   report-global admission failure, `blocking_cell_ids` is per-body — body-A
   (whose cell is still `resolved`) is omitted with an EMPTY blocking list,
   only body-B names `cell-B`. Admission failure blocks the whole report; the
   blocking attribution is per body.

## Integrity pastes

```
$ git -C E:\ChimeraWork\mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty)
```
read-only proof: before_after_identical=True (files_snapshotted=415, added=0, removed=0, changed=0)

## Notes / decision requests

- Brief said the shipped body-export example report (tools/, worktree root); the actual
  shipped example is `tools/material_volume_body_export_example_report.json`
  (used as-is, read-only). No other ambiguity met — no decision requests.
- No status was promoted anywhere; readiness remains `false` in every output
  (human tail line `readiness: false`; JSON `"readiness": false`).
- CPU-only; runtime ~3.6 s for the full suite.

## Artifacts (all under my dir; nothing written outside it)

- `brief.md` (verbatim copy, first action) · `preregistration.md` (frozen)
- `material_volume_diagnostic.py` · `run_suite.py`
- `tests/test_material_volume_diagnostic.py` (+ `tests/__init__.py`)
- `work/` — 7 generated fixture reports (genuine exporter outputs + 2
  hand-written malformed files)
- `receipts/` — `test_run.log`, `read_only_proof.json`,
  `output_samples.txt`, `u7_reader_probe.txt`, `git_integrity.txt`
