# M07 — Ownership & Status Propagation — FROZEN CASE MATRIX

Preregistered 2026-09-24, BEFORE any exporter execution. Fixtures derive from the existing
example schemas (`tools/material_volume_body_export_*_example.json`, the two-body coupon).
Module copies live in `work/`; `tools/` and `Chimera/docs/matter/` untouched (read-only).

## Rule-0 membrane (the theory under test)

STATEMENT: The body exporter enforces one-mass-owner-per-cell at the group boundary, surfaces
unowned cells explicitly, refuses/blocks instead of promoting non-admissible input, and binds
every emitted record to one freshly recomputed admission report — with no status leaking
between body records.

PREDICTION (not yet measured): the six cases below propagate exactly as the contract lines
quote; all seven falsifiers stay untriggered.

FALSIFIERS (any hit = defect, preserved):
- F1: silent acceptance of duplicate ownership (any status other than `refused`, or a report in
  which two bodies both carry the disputed cell).
- F2: an unassigned cell silently vanishing (absent from `unassigned_cell_ids`/`unassigned_cells`,
  silently absorbed into a body, or `export_status: complete` despite unassigned cells).
- F3: status leaking between bodies (good body's record naming/n carrying the bad cell's status,
  or a not-exported group carrying mass properties).
- F4: promotion of a partial/failed admission to mass properties anywhere.
- F5: refusal/blocked report that fails to name the refusing/blocking cell or reason.
- F6: admission_status / admission_report_sha256 not binding the freshly recomputed admission
  report (root level).
- F7: nondeterminism (same inputs, different report bytes).

## Contract lines quoted (Chimera/docs/matter/material_volume_body_export.md unless noted)

- Q-INPUT: "A cell cannot be assigned to multiple body groups; duplicates refuse the request."
- Q-UNASSIGNED: "Every supplied partition cell absent from the groups is listed in
  `unassigned_cell_ids`/`unassigned_cells`. It is never silently absorbed into a group or
  omitted from accounting. The report can therefore be `partial` when explicitly requested
  groups export successfully but some supplied cells are unassigned."
- Q-BLOCK: "A density gap, unresolved proposal, conflict, region mismatch, incomplete domain, or
  geometry refusal prevents reconstructed mass export. The report marks group outputs
  `not_exported`, lists blocking cell IDs/statuses where available, and never substitutes a
  default density or ownership."
- Q-REFUSED: "`refused`: malformed request, duplicate cell/body ownership, missing group cell,
  or invalid authored frame."
- Q-STATUSES: "`complete`: every supplied partition cell belongs to an authored group and all
  requested body exports succeeded." / "`partial`: requested groups succeeded but one or more
  supplied cells were left explicitly unassigned." / "`blocked`: reconstructed-mass admission
  failed; body properties are not exported."
- Q-HASH: "The root and each body record carry the admission status and SHA-256 hashes of the
  manifest, partition, and group-assignment documents. ... An admission-report hash binds the
  exporter result to its freshly recomputed preflight report."
- Q-DENSITY (admission doc): "Density may be `null` solely so an incomplete material assignment
  can be reported instead of silently filled. Missing-density cells remain visible, cannot
  contribute a total reconstructed mass, and prevent reconstructed-mass admission."

## Cases

### C1 — happy path (control)
Fixture: example manifest/partition/groups verbatim (copies).
Expect: `complete`; bodies coupon-body-A (2 kg) and coupon-body-B (1 kg) exported; root and each
body `admission_status: validation_only_admissible`; root `admission_report_sha256` == SHA-256 of
the freshly recomputed admission report == each exported body's `admission_report_sha256`;
`input_hashes` match SHA-256 of canonical JSON of each fixture file; CLI exit 0.
Contract: Q-STATUSES (complete), Q-HASH.

### C2 — duplicate cell ownership (two bodies claim one cell)
Fixture: groups altered — body-1 owns [cell-A], body-2 owns [cell-A, cell-B].
Expect: `refused`; `reason_codes: ["duplicate_cell_ownership"]` naming cell-A and both bodies
(Q-INPUT, Q-REFUSED); `body_groups: []` (no mass properties anywhere); parse-time refusal precedes
admission recomputation, so `admission_status: "not_evaluated"`, `admission_report_sha256: null`;
`input_hashes` still present (hashes computed before parsing); exit 1.
Falsifier F1 watch.

### C2b — duplicate body_id (same body claimed twice)
Fixture: two groups both with `body_id: "coupon-body-A"` (owning cell-A / cell-B respectively).
Expect: `refused`; `reason_codes: ["duplicate_body_id"]`; same propagation shape as C2
(`not_evaluated`, null admission hash, empty body_groups); exit 1. Contract: Q-REFUSED
("duplicate cell/body ownership"). Falsifier F1 watch.

### C3 — unassigned cell (owned by nobody)
Fixture: partition and manifest extended with a third disjoint positive tet cell-C
(region-C/owner-C/material tissue-C, density 3.0); groups unchanged (cell-C in no group).
Expect: `partial` (Q-STATUSES); `unassigned_cell_ids: ["cell-C"]`; `unassigned_cells` row
`{cell_id: cell-C, assignment_status: resolved, reason: not_assigned_to_an_authored_body_group}`;
`all_supplied_cells_assigned: false`; `reason_codes: ["unassigned_cells"]`; BOTH groups still
`exported` with masses 2 kg / 1 kg (Q-UNASSIGNED: groups export successfully); admission stays
`validation_only_admissible`; exit 0. Reader (U7-adjacent) must surface `unassigned_cell_ids`.
Falsifier F2 watch.

### C4 — blocked body (missing density, per admission doc)
Fixture: example partition with cell-B's material tissue-B `density_kg_m3: null`.
Expect: admission `decision: not_admitted`, reason_codes contain `missing_density` (Q-DENSITY);
root `export_status: blocked`, `reason_codes: ["reconstructed_mass_admission_required"]` (Q-BLOCK,
Q-STATUSES); group coupon-body-B `not_exported`, `mass_properties: null`,
`blocking_cell_ids: ["cell-B"]`, `blocking_assignment_statuses: [{cell_id: cell-B, status:
missing_density}]`; group coupon-body-A `not_exported`, `blocking_cell_ids: []`; BOTH groups'
`admission_status: not_admitted`; no mass properties anywhere; exit 1.
Falsifiers F3/F4/F5 watch.

### C5 — mixed groups: one complete + one incomplete
Fixture: example partition with cell-B `proposals: []` (unresolved; per partition contract
"`[]`: unresolved; no region/owner/material is invented").
Expect: admission `not_admitted`, reason_codes `["incomplete_cell_ownership",
"unresolved_assignments"]`; root `blocked`; group coupon-body-B (owns the bad cell)
`blocking_cell_ids: ["cell-B"]` with `status: unresolved`; group coupon-body-A (complete side)
`not_exported` with `blocking_cell_ids: []`, `mass_properties: null`, and NO occurrence of
`cell-B` anywhere in its serialized record; BAD body's record contains no occurrence of
`cell-A`; both bodies' `admission_status` equal the root's; the failing cell does NOT corrupt
the good body's record, and the good body does NOT receive mass properties (a partial admission
is never promoted — Q-BLOCK). Blocking attribution is per-body isolated. Exit 1.
Falsifiers F3/F4/F5 watch.

### C6 — group claims a cell absent from the partition
Fixture: groups altered — body-B owns ["cell-B", "cell-Z"].
Expect: `refused`; `reason_codes: ["unknown_group_cell_id"]` naming cell-Z (Q-REFUSED "missing
group cell"); admission IS recomputed (partition/manifest are admissible) so
`admission_status: validation_only_admissible` and `admission_report_sha256` binds the full fresh
report (contrast with C2's null); `body_groups: []`; `unassigned_cell_ids: []` (every supplied
cell is claimed; the phantom claim refuses the whole request); exit 1.
Falsifiers F1/F5 watch.

## Reader probes (U7-adjacent: reader behavior on blocked/refused; legacy covers unsupported)

- R1: reader on C1 report -> exit 0; summary carries both bodies' masses, tensors, hashes,
  admission_status.
- R2: reader on C3 (partial) -> exit 0; `unassigned_cell_ids: ["cell-C"]` surfaced.
- R3: reader on C4 (blocked) -> exit 0; bodies listed with `mass_properties: null`,
  `admission_status: not_admitted`.
- R4: reader on C2 (refused) -> exit 0; bodies list empty; root admission_status surfaced
  ("not_evaluated").
- R5: tampered C4 report (a `not_exported` group given `mass_properties`) -> reader exit 2,
  reason `blocked_group_has_mass` (the reader's own guard against F3/F4).

## Preregistered observation (decision request, not a defect claim)

O1: code inspection (before execution) shows `_blocked_group` writes the body-level
`admission_report_sha256` as the hash of a REDUCED document `{"decision", "reason_codes"}` while
the root and exported bodies bind the FULL admission report. Q-HASH says "An admission-report
hash binds the exporter result to its freshly recomputed preflight report" without naming the
reduction. MEASURE both hashes per blocked body and record; ambiguous contract -> decision
request.

## Execution protocol

Module copies (work/): material_volume_admission.py, material_volume_body_export.py,
material_volume_body_export_reader.py. PYTHONDONTWRITEBYTECODE=1. CPU-only. Receipts: per-case
exporter stdout + exit code, reader stdout + exit code, verifier verdicts. Determinism: C1 run
twice, bytes compared (F7). Integrity paste at the end:
git status --porcelain -- tools Chimera/docs/matter must be empty.

STOP when the matrix is exhausted: C1, C2, C2b, C3, C4, C5, C6 + R1-R5.
