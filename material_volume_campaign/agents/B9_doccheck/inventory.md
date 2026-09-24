# B9 PREREGISTRATION — frozen example inventory (written BEFORE any documented CLI run)

Frozen at: 2026-09-24, worktree E:/ChimeraWork/mvc-20260924, HEAD 8d574a12 (branch
material-volume-campaign-20260924, base 3db8bc4e = merge-base). Docs at
Chimera/docs/matter/, CLIs at tools/material_volume*.py — both READ-ONLY.

Pre-freeze reconnaissance limited to: `git rev-parse/branch/merge-base/status`,
`ls`, and Read of the nine matter docs. No material CLI executed before this file
was written.

## Extraction rule (frozen)

- R1: every fenced code block containing a shell command line becomes an example;
  the command is executed verbatim (relative paths resolved from a repo-root work
  copy) unless the doc itself defines a different working directory.
- R2: every repo file path literal under tools/ or Chimera/ named in prose gets an
  existence check; every named code symbol referenced as behavior gets a
  symbol-presence check in the work copy.
- R3: every exit-status, stdout-shape, field/status/readiness promise attached to a
  documented command is compared against captured stdout/stderr/exit.
- R4: every numeric claim tied to CLI behavior (test counts, fixture
  masses/volumes/COM/inertia/areas, tolerance constants, frozen expectations,
  artifact hashes, listing digests, commit ids used as artifact identity) is
  compared against observed output or git object data.
- R5: claims about historical sessions, past run ledgers, or environment states
  that today's checkout cannot decide are recorded and classified UNVERIFIABLE
  with the reason.

## Comparison rules (frozen)

- C-exit: exit codes compared exactly to the documented promise.
- C-num: doc-quoted exact decimals compared exactly after float64 parsing;
  analytic quotes (1/3, 1/12, 13/12, ...) evaluated to float64 and compared with
  absolute tolerance 1e-12; suite-delta quotes (e.g. <= 9.44e-16) checked to the
  same order of magnitude or better; test counts exact integers.
- C-bytes: "deterministic" promises verified by two runs + byte compare.
- C-hash: hex digests compared exactly (case-insensitive, first-16 compares first
  16). Where the doc does not specify the hashed serialization, the two most
  natural constructions are attempted; if neither matches, the verdict is
  UNVERIFIABLE (underspecified), never DRIFTED — an underspecified claim cannot be
  falsified by a mismatch.
- C-json: promised report fields/flags verified by parsing actual stdout JSON.

## Executed-from rule

All Python executions run from a copy of the lane inside
agents/B9_doccheck/work/repo/ (copies of tools/material_volume*.py, the example
JSON documents, and schemas) with PYTHONDONTWRITEBYTECODE=1, so no write can land
in tools/. Git-history claims run as plain read-only git invocations on the
worktree. Nothing is written outside agents/B9_doccheck/.

## FROZEN INVENTORY

### D1 = Chimera/docs/matter/material_volume_compiler.md

- E-C-01 [R1,R3,R4] (L34-63): fixture JSON block (L36-54) is a valid minimal
  input; command block (L58-61): `python tools/material_volume.py bipyramid.json`
  and `python tools/material_volume_checks.py`. Promise (L63): CLI writes compiled
  JSON to stdout; exit 0 = complete, exit 1 = valid geometry but
  incomplete/conflicted, exit 2 = named input refusal.
- E-C-02 [R1,R4] (L128, L130-132): the battery runs on the Python standard
  library alone (no pytest required); final documented focused count 17/17.
- E-C-03 [R3] (L63): exit semantics exercised: incomplete-ownership input exits 1;
  malformed input exits 2 (minimal variants authored by B9 in work/, no fixture in
  the repo is modified).
- E-C-04 [R1] (L133): `python -m py_compile tools/material_volume.py
  tools/material_volume_checks.py` passes (run on work copies only — py_compile
  writes bytecode, never into the real tools/).
- E-C-05 [R1,R4] (L133): `python tools/material_volume.py
  tools/material_volume_example.json` exits 0; volume 1/3 m^3, mass 1 kg, COM
  (0.25, 0.25, -1/12) m, one interface of area 0.5 m^2 oriented (0,0,-1).
- E-C-06 [R5] (L134): environment note "pytest -q tools/material_volume_checks.py
  is unavailable here (pytest: command not found)". Check pytest availability
  today; classify per observation.
- E-C-07 [R5,R2] (L134): `Chimera/tools/surface_energy_checks.py` invocation from
  Chimera/ stopped at `evidence_output` import (ModuleNotFoundError). Outside the
  material lane; existence check + classification only.
- E-C-08 [R2] (L104): symbol `validate_mass_source_claims()` exists in the
  compiler and rejects mixed reconstructed/thin-sheet/effective-segment ledgers.
- E-C-09 [R3] (L122): compiler output carries `complete`, per-cell
  statuses/candidates, unresolved/conflict IDs, geometric volume, total properties
  or null, resolved-only subtotal, region subtotals, exterior faces, unresolved
  adjacencies, connected-component count; per-cell rows carry cell_id, region_id,
  mass_owner_id, material_id, density_kg_m3, density source, conditions (L120-122).

### D2 = material_volume_admission.md

- E-A-01 [R2] (L9-12): paths exist: tools/material_volume_admission.py,
  tools/material_volume_admission_schema.json,
  tools/material_volume_admission_manifest_example.json,
  tools/material_volume_admission_partition_example.json,
  tools/material_volume_admission_checks.py.
- E-A-02 [R1,R3] (L15-19): `python tools/material_volume_admission.py --manifest
  tools/material_volume_admission_manifest_example.json --partition
  tools/material_volume_admission_partition_example.json` exits 0, one canonical
  JSON report to stdout, decision validation_only_admissible,
  anatomical_completeness_certified false.
- E-A-03 [R1,R4] (L19, L100): `python tools/material_volume_admission_checks.py`
  runs green; documented identity count 21.
- E-A-04 [R3] (L21): exit 1 = valid-but-not-admitted, exit 2 = malformed/refusal;
  report contains no timestamps, random IDs, file paths, or physical-state
  handles (exercise exit-1 via a cell-removed variant, exit-2 via malformed JSON;
  both authored in work/).
- E-A-05 [R4] (L38, L100): volume_surface_ownership_collision is reported for a
  matter with both tetrahedral_volume and surface_mass_overlay claims; covered by
  the admission suite the doc cites — suite green is the evidence.

### D3 = material_volume_body_export.md

- E-B-01 [R1,R3] (L8-12): `python tools/material_volume_body_export.py --manifest
  tools/material_volume_body_export_manifest_example.json --partition
  tools/material_volume_body_export_partition_example.json --groups
  tools/material_volume_body_export_groups_example.json` emits
  chimera.rigid_body_mass_export.v1 JSON to stdout, exit 0.
- E-B-02 [R1,R3] (L17-18): `python tools/material_volume_body_export_reader.py
  body_mass_export.json` inspects a written report; reader must accept the
  exporter's stdout written verbatim to that file (file authored by B9 in work/).
  Per results doc L95 the reader reports `complete`,
  dynamics_readiness_claimed: false.
- E-B-03 [R2,R4] (L20): tools/material_volume_body_export_schema.json exists; the
  groups input is versioned chimera.rigid_body_cell_groups.v1 (inspect example
  JSON); tools/material_volume_body_export_checks.py exists.
- E-B-04 [R4] (L22): coupon numbers in exporter output: A mass 2 kg (rho 12,
  V 1/6), B mass 1 kg (rho 6, V 1/6); combined mass 3 kg, volume 1/3 m^3, COM
  (13/12, -5/12, 7/12) m.
- E-B-05 [R3] (L42): output metadata flags full_symmetric_tensor: true,
  off_diagonal_terms_preserved: true, principal_axis_transform_applied: false;
  material_mass_source_provenance present.
- E-B-06 [R3] (L48-56): export_status values complete/partial/blocked/unsupported/
  refused; reports retain dynamics_readiness_claimed: false,
  physical_state_mutated: false, production_wired: false,
  anatomical_completeness_certified: false.
- E-B-07 [R1,R4] (L62-64): `python tools/material_volume_body_export_checks.py`
  runs green; documented count 8.
- E-B-08 [R3,C-bytes] (L44-46): deterministic canonical JSON, no timestamps/random
  ids/non-finite numbers; root + per-body admission status and SHA-256 input
  hashes of manifest/partition/groups; two runs byte-identical.

### D4 = material_volume_export_proof_prereg_frame_composition.md

- E-FC-01 [R1] (L11-13): tools/material_volume_export_proof_prereg_derivation.py
  runs (H, Q, R2 agree within 1e-12 or the script fails) — exit 0.
- E-FC-02 [R2,R4] (L16-19, L23-77): the four fixture JSONs exist and match the
  frozen tables (vertices/cells/densities; composed matrices R_DA/t_DA/R_DB/t_DB
  at L73-77 equal the groups_composed example contents).
- E-FC-03 [R1,R4] (L186-188): tools/material_volume_frame_composition_proof.py
  runs; documented count 8 (results doc L16: 8/8 OK).
- E-FC-04 [R4] (L102-121, L162-168): frozen run expectations hold at TOL=1e-12,
  T_PROTECTED=0.002, smallest protected off-diagonal 0.004575317547305488 —
  evidenced by the proof suite's falsifier gates F1/F3/F4 passing.

### D5 = material_volume_export_proof_prereg_shared_interface.md

- E-SI-01 [R2] (L10): derivation script path exists (execution = E-FC-01).
- E-SI-02 [R2,R4] (L15-17, L21-43): three fixture JSONs exist and match the
  frozen fixture tables (vertices, cells, densities, groups, interface face).
- E-SI-03 [R1,R4] (L126-129): tools/material_volume_shared_interface_proof.py
  runs; documented count 5 (results doc L15: 5/5 OK).
- E-SI-04 [R4] (L65-79): frozen decimal literals (bodies A/B/combined, interface
  exactly 1 internal face {v0,v1,v2} area 0.5 m^2) hold at TOL=1e-12 — evidenced
  by suite falsifier gates F1/F2/F4 passing.

### D6 = material_volume_export_proof_results.md

- E-R-01 [R4] (L14): landing commit d2c23741 exists in history.
- E-R-02 [R1,R4] (L15): package 1 proof = 5/5 OK (rerun at HEAD).
- E-R-03 [R1,R4] (L16): package 2 proof = 8/8 OK (rerun at HEAD).
- E-R-04 [R1,R4] (L17, L100-101): `python
  tools/material_volume_export_proof_verify.py` = Ran 7 tests OK (rerun at HEAD).
- E-R-05 [R1,R4] (L18): compiler 17 + admission 21 + export 8 leaf suites all OK
  (rerun at HEAD; counts exact).
- E-R-06 [R4] (L39-52): observed deltas <= 9.44e-16 against frozen expectations
  (rerun reproduces deviations of the same order or smaller).
- E-R-07 [R5] (L18-19): R1 clean-room reproduction and the integrated-revision
  full battery "recorded at handoff" — historical execution record; rerun
  performed as E-R-04/05 covers the live claim; the handoff record itself is
  UNVERIFIABLE.

### D7 = material_volume_export_verification_prereg.md

- E-V-01 [R4] (L4-5): revision 1af0bbde exists at the full hash given in the
  receipt (1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56).
- E-V-02 [R1,R4] (L27): all six suites green with counts 17/21/8/5/8/7 at the
  current checkout (rerun; this is V1).
- E-V-03 [R4] (L28): unique test identities by unittest discovery = 17/21/8/5/8/7,
  total 66 = 59 leaf + 7 verification; verification runner reports only
  `Ran 7 tests` (this is V2).
- E-V-04 [R4] (L29): V3 hashes — compare LF-canonical SHA-256 of lane artifacts at
  1af0bbde against the receipt's canonical manifest (E-VR-07).

### D8 = material_volume_export_verification_receipt.md

- E-VR-01 [R4] (L3): full object 1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56 exists.
- E-VR-02 [R4] (L6): commit 02da40be exists (the revision the shared branch moved
  to).
- E-VR-03 [R4] (L8): commit f2bcac88 exists (prereg freeze commit).
- E-VR-04 [R4,C-hash] (L29-35): V2 listing-sha256[:16] per module
  (838d5bf26e7eb88d, 3b230e19d1e95da9, f02f7f4b4ff01133, 3366b8c609c51d5d,
  25507952edb39d51, 489fdeabce8367d6) — serialization of the "listing" is not
  specified; attempt natural constructions; else UNVERIFIABLE (underspecified).
- E-VR-05 [R5] (L49-63): repeated-executions ledger (totals 328, per-suite
  standalone/nested run counts) — historical ledger of past executions;
  UNVERIFIABLE.
- E-VR-06 [R4,C-hash] (L84-89): digest ee27dcd22aedac909984650dcc69f02ea8d66f4eea
  4bfd96d00ce29604f048a4 over "listing of 33 blobs at 1af0bbde, sorted" — file-set
  and serialization underdetermined; attempt natural constructions; else
  UNVERIFIABLE.
- E-VR-07 [R4,C-hash] (L104-118): canonical LF sha256[:16] of the eight named
  artifacts at 1af0bbde (15a42e3d21357350, 844170e92bd4cf82, a5d762daefb136a0,
  282bc52bfa997c6c, 5485c8c4fe73d679, d190eae0791277d1, 546c943d585cab6b,
  e5bf32fd94dcfd7f) — computed from `git show 1af0bbde:<path>` bytes with CRLF
  normalized to LF.
- E-VR-08 [R5] (L96-101): V3 recheck numbers (14/14, 14/14, 1/14) reference the
  14 previously reported working-copy hashes, which the docs do not print in
  full — UNVERIFIABLE as stated (inputs not in the record).

### D9 = rigid_body_mass_export_consumption_contract_v1_proposal.md

- E-P-01 [R2] (L15-17): tools/material_volume_body_export.py is the named
  producer; path exists.
- E-P-02 [R3,C-json] (L19-34): report carries exactly-named fields: body_id,
  owned_cell_ids, mass_properties.mass {value, unit kg, coordinate_frame
  frame_invariant, frame_invariant true}, mass_properties.volume {value, unit
  "m^3", frame_invariant true}, mass_properties.center_of_mass {value[3], unit m,
  coordinate_frame frame_id}, mass_properties.inertia_tensor_about_com {value[3][3],
  unit kg*m^2, coordinate_frame frame_id, basis authored_body_frame,
  full_symmetric_tensor true, off_diagonal_terms_preserved true,
  principal_axis_transform_applied false}, body_frame {frame_id, handedness right,
  coordinate_unit m, domain_from_body {rotation, origin_m}}, cell_provenance[]
  per-cell mass_owner_id/region_id/material_id/density_kg_m3/density_source/
  density_conditions, material_mass_source_provenance (mass_authority,
  mass_source_kind, integration_model, material_records[], mass_owner_ids[],
  overlay/source-consumption flags false), admission_status +
  admission_report_sha256, input_hashes (manifest/partition/groups), export_status,
  reason_codes, root unassigned_cell_ids / unassigned_cells[] /
  all_supplied_cells_assigned, flags validation_only, dynamics_readiness_claimed,
  physical_state_mutated, production_wired, anatomical_completeness_certified,
  surface_mass_overlay_generated, source_effective_segment_payloads_consumed
  (safety-relevant ones false).
- E-P-03 [R3] (L39-54): status semantics exercised directly on B9-authored
  variants in work/: source-effective authority -> unsupported; null-density
  partition -> blocked with blocking diagnostics; groups omitting one cell ->
  partial with unassigned_cell_ids; malformed -> refused. not_exported bodies
  carry null mass_properties and reason_codes.
- E-P-04 [R4] (L102-105): CON-15 numeric "proven equivalent ... <= 9.4e-16" —
  consistent with results doc (9.44e-16) and evidenced by E-FC-03 suite pass.

### X = CLI surface (--help receipts; brief mandate)

- E-X-01 [R1]: `--help` captured for every tools/material_volume*.py executable:
  material_volume.py, material_volume_checks.py, material_volume_admission.py,
  material_volume_admission_checks.py, material_volume_body_export.py,
  material_volume_body_export_reader.py, material_volume_body_export_checks.py,
  material_volume_shared_interface_proof.py, material_volume_frame_composition_proof.py,
  material_volume_export_proof_verify.py,
  material_volume_export_proof_prereg_derivation.py. Observation only (help text
  content is not promised by any doc); files without argparse mains are recorded
  as such.

## Verdict scale (frozen)

MATCHES / DRIFTED (runs but differs; exact diff quoted) / BROKEN (fails to run or
documented promise absent) / UNVERIFIABLE (undecidable today; reason stated).

FALSIFIER (frozen): any BROKEN or any promised behavior absent after honest
execution is a finding; verbatim outputs preserved under receipts/. A fired
falsifier is reported, never tuned away.
