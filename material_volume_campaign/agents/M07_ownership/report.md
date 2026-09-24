# M07 — Ownership & Status Propagation — REPORT

Agent: M07 · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`, HEAD at run start `0c5cbbf0`; campaign base tip `3db8bc4e`)
Scope: ownership rules and admission-status propagation through
`tools/material_volume_body_export.py` (+ admission, reader). CPU-only. `tools/` and
`Chimera/docs/matter/` untouched (module copies in `work/`, `PYTHONDONTWRITEBYTECODE=1`).

- Preregistration (frozen BEFORE execution): `matrix.md` — case matrix C1, C2, C2b, C3, C4, C5,
  C6 + reader probes R1–R5, each with quoted contract lines and named falsifiers F1–F7.
- Result: **64 verifier checks, 64 PASS, 0 FAIL. No falsifier fired.** One preregistered
  decision request (O1) measured. One agent-side harness incident preserved (not a product defect).

## 1. Frozen matrix and expectations

Full preregistration with verbatim contract quotes: `matrix.md`. Cases:
- **C1 happy path (control)** — example two-body coupon verbatim. Contract: "`complete`: every
  supplied partition cell belongs to an authored group and all requested body exports succeeded";
  "The root and each body record carry the admission status and SHA-256 hashes...".
- **C2 duplicate cell ownership** — two groups claim `cell-A`. Contract: "A cell cannot be
  assigned to multiple body groups; duplicates refuse the request"; `refused` covers "duplicate
  cell/body ownership".
- **C2b duplicate body_id** — same `body_id` twice. Contract: `refused` covers "duplicate
  cell/body ownership".
- **C3 unassigned cell** — third supplied tet `cell-C` in no group. Contract: "Every supplied
  partition cell absent from the groups is listed in `unassigned_cell_ids`/`unassigned_cells`.
  It is never silently absorbed into a group or omitted from accounting."; "`partial`: requested
  groups succeeded but one or more supplied cells were left explicitly unassigned."
- **C4 blocked body (missing density)** — `tissue-B density_kg_m3: null` (admission-doc
  construction). Contract: "Missing-density cells remain visible, cannot contribute a total
  reconstructed mass, and prevent reconstructed-mass admission"; "A density gap ... prevents
  reconstructed mass export. The report marks group outputs `not_exported`, lists blocking cell
  IDs/statuses where available, and never substitutes a default density or ownership."
- **C5 mixed groups (complete + incomplete)** — `cell-A` resolved, `cell-B` `proposals: []`
  (unresolved). Same Q-BLOCK line; exporter contract: a partial admission is never promoted to
  body properties.
- **C6 group claims absent cell** — `body-B` owns `["cell-B","cell-Z"]`. Contract: `refused`
  covers "missing group cell".

Reader probes (U7-adjacent — open item "reader behavior on `blocked`/`refused`"):
R1 complete, R2 partial, R3 blocked, R4 refused, R5 tampered blocked-with-mass.

## 2. Receipts

All under `receipts/`:
- `case-{c1,c2,c2b,c3,c4,c5,c6}-export.json` + `.exit` (stdout + CLI exit code; `.stderr` all empty)
- `case-c1-export-rerun.json` (determinism receipt — byte-identical, F7)
- `probe-{r1..r5}-reader.json` + `.exit` + `.stderr`
- `verify-results.json` (all 64 claims with evidence)
- `harness-incident-20260924.md` (preserved first-run failure)

## 3. Propagation verdict table

| Case | Input defect | Root `export_status` | Root `admission_status` | Body outcomes | Exit | Verdict |
|---|---|---|---|---|---|---|
| C1 | none | `complete` | `validation_only_admissible` | A exported 2 kg, B exported 1 kg; body admission hash == root == fresh report (`a4ea955917b4…`) | 0 | PASS |
| C2 | `cell-A` in two groups | `refused` | `not_evaluated`, report hash `null` | `body_groups: []`; reason `duplicate_cell_ownership`; detail names cell + both bodies | 1 | PASS |
| C2b | duplicate `body_id` | `refused` | `not_evaluated`, hash `null` | `body_groups: []`; reason `duplicate_body_id` | 1 | PASS |
| C3 | `cell-C` unowned | `partial`, reasons `["unassigned_cells"]` | `validation_only_admissible`, hash binds fresh report | A/B still exported 2 kg/1 kg; `unassigned_cell_ids:["cell-C"]`; row `{resolved, not_assigned_to_an_authored_body_group}`; `all_supplied_cells_assigned:false`; `cell-C` in NO body record | 0 | PASS |
| C4 | `cell-B` density null | `blocked`, `["reconstructed_mass_admission_required"]` | `not_admitted`, codes `["missing_density"]`, root hash binds fresh report (`4d4c43e1e0d1…`) | both `not_exported`, `mass_properties:null`; B blocking `[{cell-B, missing_density}]`; A blocking `[]`; no `cell-B` in A's record, no `cell-A` in B's | 1 | PASS |
| C5 | `cell-B` unresolved + `cell-A` fine | `blocked` | `not_admitted`, codes `["incomplete_cell_ownership","unresolved_assignments"]` | B blocking `[{cell-B, unresolved}]`; A blocking `[]`, record intact (`owned_cell_ids` preserved), zero mass properties anywhere; no cross-mention either direction | 1 | PASS |
| C6 | phantom claim `cell-Z` | `refused`, `["unknown_group_cell_id"]` naming `cell-Z` | `validation_only_admissible`, hash binds fresh report and equals C1's (same manifest/partition) | `body_groups: []` — admissible partition does NOT partially export | 1 | PASS |

Reader probes (U7 evidence):

| Probe | Input | Behavior | Exit | Verdict |
|---|---|---|---|---|
| R1 | C1 report | masses/tensors/hashes surfaced | 0 | PASS |
| R2 | C3 report | `unassigned_cell_ids:["cell-C"]` surfaced | 0 | PASS |
| R3 | C4 report | **ACCEPTS blocked**: bodies listed, `mass_properties:null`, `admission_status:not_admitted` | 0 | PASS |
| R4 | C2 report | **ACCEPTS refused**: empty bodies, `admission_status:"not_evaluated"` surfaced | 0 | PASS |
| R5 | tampered C4 (not_exported group given `mass_properties`) | **REJECTS**: `blocked_group_has_mass: body_groups[0] is not exported but includes properties` | 2 | PASS |

Determinism (F7): C1 run twice, byte-identical (5473 bytes).

## 4. Falsifier results (all clear) and defects

- **F1 silent duplicate ownership**: not triggered — `duplicate_cell_ownership` /
  `duplicate_body_id` refusals, no body records, no mass properties, detail names the disputed
  cell and both claimants.
- **F2 unassigned cell silently vanishing**: not triggered — explicit `unassigned_cell_ids` +
  `unassigned_cells` row with reason `not_assigned_to_an_authored_body_group`; `partial` status;
  cell absent from every body record; cell fully accounted in the admission report.
- **F3 status leaking between bodies**: not triggered — in C4/C5 the good body's record never
  mentions the bad cell and vice versa; good body's blocking lists are empty; reader's
  `blocked_group_has_mass` guard independently rejects a not_exported body carrying properties.
- **F4 partial-admission promotion**: not triggered — zero `mass_properties` anywhere in
  blocked/refused reports; `not_exported` bodies carry `mass_properties: null`.
- **F5 unnamed refusal/blocking**: not triggered — every refusal/block names cell IDs and
  statuses (`missing_density`, `unresolved`, `cell-Z`, both body IDs in C2).
- **F6 hash binding**: holds at root for all evaluated cases (root `admission_report_sha256` ==
  SHA-256 of the independently recomputed admission report, including C6 where it equals C1's
  hash for identical inputs); parse-time refusals correctly carry `not_evaluated`/`null`.
- **F7 nondeterminism**: not triggered.

### Decision request O1 (preregistered; measured, not a falsifier hit)

Body-level `admission_report_sha256` on `not_exported` groups binds a REDUCED document, not the
fresh full report:
- Code: `tools/material_volume_body_export.py` `_blocked_group` (line 221–222) hashes
  `{"decision": <decision>, "reason_codes": <codes>}` → measured `298c544846f7…` (C4/C5 bodies),
  while the root and every exported body bind the full report `4d4c43e1e0d1…`.
- Contract (`material_volume_body_export.md` § Report and hashes): "An admission-report hash
  binds the exporter result to its freshly recomputed preflight report" — it does not name the
  reduction; grep confirms the doc never mentions a reduced body-level binding. The doc line
  "The root and each body record carry the admission status and SHA-256 hashes of the manifest,
  partition, and group-assignment documents" is satisfied (input hashes are full on bodies).
- Impact: two different documents share the field name `admission_report_sha256` depending on
  record status; a consumer verifying a blocked body's hash against the admission report it can
  recompute will see a mismatch. Reader R3 faithfully propagates the reduced hash.
- Ask: adjudicate whether the body-level reduced binding on `not_exported` groups is compliant
  with the sentence above, or should bind the full report (the `unsupported` path at line 404
  already binds the FULL report — the two non-export paths are inconsistent with each other).

### Harness incident (preserved; agent-side, not a product defect)

First execution attempt failed on all cases with `ModuleNotFoundError: No module named
'material_volume'` — my work/ copy set omitted the compiler module. Fixed by copying
`tools/material_volume.py` into `work/`; matrix re-run from scratch. Traceback preserved verbatim
in `receipts/harness-incident-20260924.md`. No tools/ or docs/ writes occurred at any point.

## 5. Integrity paste

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
$ echo "exit=$?"
exit=0
```

Output empty (exit 0): `tools/` and `Chimera/docs/matter/` carry zero modifications. Full-worktree
status shows only untracked `material_volume_campaign/agents/*/` directories (this agent wrote
only inside `agents/M07_ownership/`). All four work/ module copies verified byte-identical
(`cmp`) to their `tools/` sources.

## 6. Files

- `brief.md`, `matrix.md` (preregistration), this `report.md`
- `fixtures/` — 16 case fixtures + `probe-r5-tampered-blocked-with-mass.json`, all minimal diffs
  from `tools/material_volume_body_export_*_example.json` schemas
- `work/` — module copies (`material_volume.py`, `material_volume_admission.py`,
  `material_volume_body_export.py`, `material_volume_body_export_reader.py`), `gen_fixtures.py`,
  `verify_propagation.py`
- `receipts/` — all exporter/reader outputs, exit codes, `verify-results.json`, incident record

Matrix exhausted (C1, C2, C2b, C3, C4, C5, C6 + R1–R5). STOP.
