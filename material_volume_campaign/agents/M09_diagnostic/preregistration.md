# M09 preregistration — READ-ONLY diagnostic CLI (frozen before implementation)

Frozen: 2026-09-24, before `material_volume_diagnostic.py` exists.
Status vocabulary and readiness law come from contract v0.9
(`Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md`):
root statuses `complete|partial|blocked|unsupported|refused`; per-body
`exported|not_exported`; `dynamics_readiness_claimed` always `false` (CON-14);
no promotion anywhere in this tool.

## THEORY (Rule 0)

- **STATEMENT**: The existing reader's public interface
  (`read_json_file`, `summarize_export_report`, `canonical_json`,
  `ExportInputError`, `EXPORT_SCHEMA`) is sufficient to build a diagnostic CLI
  that surfaces every contract-mandated diagnostic (status, every omitted body
  + reasons, unassigned cell IDs, frames, units, readiness=false) without
  re-parsing or reimplementing any validation.
- **PREDICTION** (untested until the suite runs): (a) the reader accepts
  genuine exporter `blocked` and `refused` reports without misbehavior (U7);
  (b) the reader's *summary* drops some contract-preserved diagnostics
  (`blocking_cell_ids`, `blocking_assignment_statuses`, top-level
  `reason_codes`/`detail`, `unassigned_cells` per-cell rows), so the CLI must
  pass those through from the reader-parsed raw mapping for display only.
- **FALSIFIERS** (named before the run; any hit = defect in THIS tool, fix
  here; reader misbehavior = finding about `tools/`, preserved not fixed):
  - F1: any code path in the CLI that writes or modifies an input file
    (includes writing `__pycache__` into `tools/` — mitigated by
    `sys.dont_write_bytecode = True` set before the reader import).
  - F2: CLI output displaying readiness != `false` anywhere.
  - F3: CLI displaying a status (root or per-body) that is not present in the
    report / not produced by the reader's summary (status invention).

## FROZEN OUTPUT CONTRACT (v1)

Invocation:
```
python material_volume_diagnostic.py REPORT [REPORT ...] [--json] [--tools-dir DIR]
```
`--tools-dir` (or env `M09_TOOLS_DIR`) points at the directory holding
`material_volume_body_export_reader.py`; default = nearest ancestor directory
of this file containing `tools/material_volume_body_export_reader.py`.

Sources of truth: ALL parsing via `exporter.read_json_file`; ALL validation,
status vocabulary, per-body summaries and readiness via
`reader.summarize_export_report`; JSON serialization via
`reader.canonical_json`. The raw reader-parsed mapping is used ONLY for
display passthrough of fields the summary drops (never for re-validation, and
displayed values are never transformed into new statuses).

### JSON output (`--json`; one object, canonical JSON via reader)

Top level:
- `tool`: `"material_volume_diagnostic"`
- `readiness`: constant `false` (mirrors every per-report value; a violation
  aborts with exit 4 and a stderr alarm, output readiness stays `false`)
- `reports`: array, one entry per path argument, same order.

Per-report entry, when the reader accepts the report (`ok: true`):
- `path` — exactly as given on the command line
- `ok` — `true`
- `schema_version` — from summary (must equal `exporter.EXPORT_SCHEMA`)
- `export_status` — from summary only
- `admission_status` — from summary, or `"not_reported"` when null
- `readiness_claimed` — from summary `dynamics_readiness_claimed`; must be
  `false` (F2)
- `physical_state_mutated` — from summary (`false`)
- `unassigned_cell_ids` — from summary
- `unassigned_cells` — display passthrough of raw `unassigned_cells` rows
  (`cell_id`, `assignment_status`, `reason`; missing key → `null`), only when
  the raw report carries them
- `top_level_reason_codes` — raw `reason_codes` when present
- `detail` — raw `detail` when present
- `input_hashes` — from summary
- `bodies` — from summary `bodies`; each: `body_id`, `export_status`,
  `owned_cell_ids`, `omitted` (= `export_status != "exported"`); for exported
  bodies also `mass_kg`, `com` `{value, unit, coordinate_frame}`, `inertia`
  `{unit, coordinate_frame, basis}`; for omitted bodies also `reason_codes`
- `omitted_bodies` — the omitted subset, each with `body_id`,
  `export_status`, `reason_codes` (from summary) plus display passthrough from
  the raw row when present: `blocking_cell_ids`,
  `blocking_assignment_statuses`, `admission_reason_codes`
- `frames` — sorted distinct coordinate frames across bodies (summary data)
- `units` — sorted distinct units across bodies (summary data)

When the reader rejects the report (`ok: false`): `path`, `ok: false`,
`error` `{reason, detail}` from `exporter.ExportInputError`; all summary
fields ABSENT (never invented).

### Human output (default; deterministic line grammar)

```
report: <path>
  ok: true|false
  (ok=false) error_reason: <reason> / error_detail: <detail>
  (ok=true)
  schema_version: <v>
  export_status: <status>
  admission_status: <status|not_reported>
  readiness_claimed: false
  physical_state_mutated: false
  top_level_reason_codes: <c1, c2|(none)>
  detail: <d|(none)>
  bodies: <n>
  omitted_bodies: <m>
    omitted[<i>] body_id=<id> export_status=<s> reason_codes=<c1, c2|(none)> blocking_cell_ids=<x, y|(none)> blocking_assignment_statuses=<cell:st, ...|(none)> admission_reason_codes=<c1, c2|(none)>
  unassigned_cell_ids: <id1, id2|(none)>
  unassigned_cells: <count|(none)>
    unassigned[<i>] cell_id=<id> assignment_status=<s> reason=<r>
  frames: <f1; f2|(none)>
  units: <u1; u2|(none)>
  exported_masses: <k|(none)>
    mass[<i>] body_id=<id> mass=<m> kg com_frame=<f> com_unit= m inertia_frame=<f> inertia_unit=<u> inertia_basis=<b>
readiness: false
```
The final line of every human-mode run is `readiness: false` (F2 sentinel).

### Exit codes (frozen)

- `0` — every path accepted by the reader (any of the five statuses counts as
  a successfully *diagnosed* report; `refused` is not a CLI failure)
- `2` — at least one path rejected by the reader (`ExportInputError`)
- `4` — readiness violation alarm (F2; must never fire)
- other nonzero — usage errors (argparse)

## FROZEN ACCEPTANCE TEST PLAN

Fixtures: the shipped example report is READ as-is; all other reports are
generated IN-MEMORY by calling the exporter's own public
`build_export_report(manifest, partition, groups)` on mutated in-memory copies
of the shipped example manifest/partition/groups (file inputs never mutated;
generated bytes written only under `agents/M09_diagnostic/work/`), plus two
hand-written malformed files in `work/`. Expected genuine outputs:
- complete — shipped example, unchanged.
- partial — drop body-B from the groups doc → `unassigned_cell_ids ==
  ["cell-B"]`, `unassigned_cells` row reason
  `not_assigned_to_an_authored_body_group`, status `partial`.
- blocked — point region-B at a material absent from `materials` → status
  `blocked`, every group `not_exported`, reason
  `reconstructed_mass_admission_required`, `mass_properties: null`,
  blocking cell `cell-B`.
- unsupported — manifest `mass_authority = "source_effective_segment_mass"` →
  status `unsupported`, reason `source_effective_segment_mass_unsupported`.
- refused — empty `body_id` string in groups → status `refused`, top-level
  `reason_codes` `["bad_identifier"]`, `body_groups: []`.
- malformed ×2 — wrong `schema_version` (reader `bad_export_report_version`)
  and duplicate JSON key (reader `duplicate_json_key`).

Tests (unittest, CPU-only, run with `PYTHONDONTWRITEBYTECODE=1`):
- T1 happy path: shipped example → ok, `complete`, 2 exported bodies, 0
  omitted, `unassigned_cell_ids: []`, readiness false, frames
  {coupon-A-authored, coupon-B-authored}, units {kg, kg*m^2, m}.
- T2 partial case: status `partial`; CLI surfaces `unassigned_cell_ids` AND
  the raw `unassigned_cells` row for `cell-B`.
- T3 omitted-bodies case (blocked): status `blocked`; `omitted_bodies` has
  coupon-body-A and coupon-body-B with reason
  `reconstructed_mass_admission_required`; `blocking_cell_ids` surfaced
  (["cell-A"], ["cell-B"]); no mass fields for omitted bodies.
- T4 refused case: status `refused`; `top_level_reason_codes == ["bad_identifier"]`,
  `detail` surfaced, `bodies == []`; exit code 0 (successfully diagnosed).
- T5 unsupported case: status `unsupported`, omission reason
  `source_effective_segment_mass_unsupported`, readiness false.
- T6 malformed cases: `ok: false` with the reader's reason; exit code 2.
- T7 F2 falsifier: for EVERY accepted case, `readiness_claimed == false`,
  top-level `readiness == false`, human output contains
  `readiness_claimed: false` and final line `readiness: false`.
- T8 F3 falsifier: every displayed root/per-body status equals the reader
  summary value and the raw report value (no invention); no body in
  `omitted_bodies` has `export_status == "exported"`.
- T9 F1 falsifier (read-only proof): SHA-256 + st_mtime_ns of every tools/
  file used, both example JSONs, and the contract doc captured before and
  after the full suite → identical; `tools/` contains no new `__pycache__`.
- T10 exit codes: 0 for all five genuine statuses; 2 for malformed.
- T11 U7 record: reader behavior on genuine blocked/refused observed and
  recorded (accepts without misbehavior? which summary fields survive?).

Acceptance = all tests green as specified + read-only proof + repo integrity
`git status --porcelain -- tools Chimera/docs/matter` empty.
