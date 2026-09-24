# M10 PREREGISTRATION — static consumption validator, contract v1 (frozen before implementation)

Frozen: 2026-09-24. This file is written BEFORE `rigid_body_mass_consumption_validator.py`
exists. Its SHA-256 is recorded in `receipts/freeze_sha256.txt` before implementation starts.
Any change after the freeze must be an appended amendment, never an edit.

## Rule-0 membrane

- **STATEMENT.** A pure-static structural validator (no runtime assembly, no physics, no
  mutation) over a `chimera.rigid_body_mass_export.v1` report, enforcing rules R1–R16 below,
  ACCEPTS exactly those reports whose bodies are assembly-ELIGIBLE under the strictest reading
  of `Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md`, and
  REJECTS every report that (a) is not root-`complete` with every body `exported`, (b) violates
  any authority-field form, or (c) carries any readiness claim, ownership inference,
  recombination/lineage claim, or safety-flag deviation.
- **PREDICTION (not yet measured).** The frozen test suite below passes: the accept fixture is
  ACCEPTED; every reject fixture is REJECTED naming the rule it targets; all four adversarial
  fixtures are REJECTED; `git status --porcelain -- tools Chimera/docs/matter` stays empty.
- **FALSIFIER (named before the run).** Any adversarial fixture the validator ACCEPTS while the
  strictest contract reading demands rejection — except the pre-declared static-limit class
  (integrity-vs-reference facts that are undecidable without the source documents supplied,
  e.g. a consistently-symmetric wrong tensor; see LIMITS). Also falsified by: a false rejection
  of the clean accept fixture, or a non-empty tools/contract-docs integrity check.

## Scope (from the campaign directive)

STATIC VALIDATION ONLY. The validator only ACCEPTS/REJECTS report bodies for assembly
ELIGIBILITY and reports reasons. No runtime wiring, no assembly, no dynamics, no mutation,
CPU-only. Writes only inside `agents/M10_validator/`. `tools/` and `docs/` are READ-ONLY; the
existing reader is imported via `sys.path` with bytecode writing disabled.

## Numbered rule set (each rule quotes the contract line it enforces)

Contract = `Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md`
(proposal v0.9). All comparisons are case-sensitive and exact unless stated. A rule failure is
preserved, never swallowed: the verdict enumerates every rule failure, not just the first.

- **R1 — report identity & strict parse.** The document is a JSON object with
  `schema_version == "chimera.rigid_body_mass_export.v1"` and a list `body_groups`.
  Contract §1: "A consumable unit is one body record (`body_groups[i]`) inside one export
  report produced by `tools/material_volume_body_export.py`". Parsing reuses the exporter's
  strict loader (duplicate JSON keys and NaN/Infinity constants are refusals).
- **R2 — root `export_status` gate (exhaustive, strictest per status).** Value must be exactly
  one of `complete|partial|blocked|unsupported|refused`; anything else is rejected. Only
  `complete` can ACCEPT. Contract §2 root table: `partial` — "**Silent partial assembly
  FORBIDDEN.** Default: REJECT."; `blocked` — "REJECT for dynamics consumption; preserve
  `blocking_cell_ids` / `blocking_assignment_statuses` for diagnostics only (CON-4)";
  `unsupported` — "REJECT. Source masses are **never** consumed (CON-5)"; `refused` —
  "REJECT; preserve `reason_codes`/`detail` (CON-6)"; `complete` — "MAY consume `exported`
  bodies as **static** mass properties (CON-1/2). Readiness NOT implied". Unknown statuses are
  outside v1 and rejected. [D2 and D5 are exercised here; see DECISION REQUESTS.]
- **R3 — `admission_status` exact value.** Root and every body must carry
  `admission_status == "validation_only_admissible"` (exact, case-sensitive). Contract CON-13:
  "`admission_status` MUST be `validation_only_admissible`; anything else is non-consumable."
- **R4 — hash binding.** (a) Root and every body carry `admission_report_sha256`; it is a
  64-character lowercase hex string. (b) On root-`complete` reports, every body hash equals the
  root hash (binding consistency; tamper signal). (c) `input_hashes` present with
  `algorithm == "sha256"` and `manifest_sha256`, `partition_sha256`, `body_groups_sha256` all
  non-null well-formed hex on root-`complete` reports. (d) OPTIONAL recomputation: if the
  admission report document is supplied, its canonical-JSON SHA-256 must equal the recorded
  hash, else tamper refusal. Contract CON-13: "Integrity: `input_hashes` and
  `admission_report_sha256` MUST be verified on receipt against the documents actually
  delivered; any mismatch is a corruption/tamper refusal." LIMIT recorded: without the supplied
  admission document, presence+well-formedness+consistency is all that is statically checkable.
- **R5 — per-body consumable status (CON-1/4/7).** Only per-body
  `export_status == "exported"` with non-null `mass_properties` is eligible; `not_exported`
  bodies are rejected as diagnostics and any `not_exported` body carrying `mass_properties`
  is also rejected (placeholder). Unknown per-body statuses rejected. A root-`complete` report
  containing any `not_exported` body is self-contradictory and rejected. Contract CON-1: "Only
  `exported` bodies with non-null `mass_properties` are consumable, and only as static mass
  properties."; per-body table: "`not_exported` | `mass_properties` is `null` — **no placeholder
  bodies, no estimated masses**"; CON-4: "Blocked/not-exported records are diagnostics, never
  inputs."; §3: "A consumer MUST NOT assemble a body it did not receive properties for, and
  MUST NOT synthesize substitutes (CON-7)."
- **R6 — authoritative mass field.** `mass_properties.mass` present with `value` a finite
  number > 0, `unit == "kg"`, `coordinate_frame == "frame_invariant"`, `frame_invariant is
  True`. Contract §1 table: "`mass_properties.mass` | `{value, unit: kg, coordinate_frame:
  "frame_invariant", frame_invariant: true}` | authoritative mass"; CON-11: "Units: kg, m,
  kg·m², m³ as declared per field; mass and volume frame-invariant".
- **R7 — volume field form.** `mass_properties.volume` present with finite positive `value`,
  `unit == "m^3"`, `frame_invariant is True` (informational per contract, but its declared form
  is enforced). Contract §1 table: "`mass_properties.volume` | `{value, unit: "m^3",
  frame_invariant: true}` | informational".
- **R8 — COM field and frame binding.** `mass_properties.center_of_mass` present with `value`
  exactly 3 finite numbers, `unit == "m"`, `coordinate_frame ==` the body's
  `body_frame.frame_id`. Contract §1 table: "`mass_properties.center_of_mass` | `{value[3],
  unit: "m", coordinate_frame: frame_id}` | COM in the authored frame"; CON-11: "COM and
  inertia expressed in `frame_id`".
- **R9 — full-tensor integrity (CON-9).** `mass_properties.inertia_tensor_about_com`:
  `value` is exactly 3×3 finite numbers (9 entries; truncation rejected); exact symmetry
  `value[i][j] == value[j][i]` for all i,j (JSON round-trips doubles exactly; stricter than the
  reader's 1e-12 — deliberate, "as authored and never repaired"); flags exactly
  `full_symmetric_tensor is True`, `off_diagonal_terms_preserved is True`,
  `principal_axis_transform_applied is False`; `unit == "kg*m^2"`;
  `coordinate_frame == body_frame.frame_id`; `basis == "authored_body_frame"`.
  Contract §1 table: "`mass_properties.inertia_tensor_about_com` | `{value[3][3], unit:
  "kg*m^2", coordinate_frame: frame_id, basis: "authored_body_frame",
  full_symmetric_tensor: true, off_diagonal_terms_preserved: true,
  principal_axis_transform_applied: false}` | **full** symmetric tensor about COM; all 9
  entries retained"; CON-9: "**Dropped off-diagonal terms are forbidden**; silent principal-axis
  frames are forbidden (`principal_axis_transform_applied` must remain `false`...)".
- **R10 — body frame authority (CON-10).** `body_frame` present: `frame_id` non-empty string;
  `handedness == "right"`; `coordinate_unit == "m"`; `domain_from_body.rotation` exactly 3×3
  finite AND proper orthonormal as authored (max|RᵀR−I| ≤ 1e-12 and |det R − 1| ≤ 1e-12 — a
  non-conforming rotation is REFUSED, never repaired); `origin_m` exactly 3 finite numbers.
  Contract CON-10: "Frame convention `x_domain = rotation · x_body + origin_m`; right-handed,
  meters. `rotation` is proper orthonormal **as authored and never repaired** — a consumer whose
  loader would 'repair' or re-orthonormalize MUST refuse instead."
- **R11 — ownership verbatim; provenance travels (CON-8/12).** Per eligible body:
  `owned_cell_ids` non-empty list of unique non-empty strings; `cell_provenance` a list with
  exactly one row per owned cell (`cell_id` bijects with `owned_cell_ids`), each row carrying
  `mass_owner_id`, `region_id`, `material_id`, `density_kg_m3` (finite > 0), `density_source`,
  `density_conditions`; duplicate `cell_id` rows with conflicting `mass_owner_id` rejected
  (one mass owner per cell); `material_mass_source_provenance` present with
  `mass_source_kind == "reconstructed_material_volume"`, `mass_authority ==
  "reconstructed_tissue_mass"`, and `mass_owner_ids` equal (as a set) to the provenance
  `mass_owner_id` values; per-body overlay/source flags all exactly `false`.
  Contract CON-8: "Ownership is taken verbatim from `cell_provenance` / `mass_owner_id`.
  **Inferred ownership is forbidden** (no derivation from anatomy, stiffness, region labels, or
  connected components)."; CON-12: "Provenance travels with the body (`cell_provenance`,
  `material_mass_source_provenance`, `mass_source_kind: "reconstructed_material_volume"`);
  stripping provenance voids the contract."; §1 table: "`owned_cell_ids` | the body's owned
  cells | one mass owner per cell, exporter-enforced". [D5 exercised here: any other
  `mass_authority` is rejected.]
- **R12 — readiness prohibition (CON-14) [D1].** `dynamics_readiness_claimed` present and
  exactly `False` at root and in every body; PLUS a recursive scan of the entire document: any
  key at any depth whose name (case-insensitive) contains `dynamics_readiness`,
  `readiness_claimed`, `dynamics_ready`, `assembly_ready`, or `simulation_ready` and whose
  value is not exactly `False`/`null` is a readiness claim → REJECT. Contract CON-14: "**No
  automatic readiness claim.** `dynamics_readiness_claimed` is `false` and no field combination
  may be read as readiness. Readiness is a separate future act under D1."; Non-claims:
  "Nothing in v1 establishes anatomical correctness, mechanical qualification, or dynamics
  readiness. `dynamics_readiness_claimed` is always `false`."
- **R13 — fixed v1 safety flags.** Root: `validation_only is True`, `physical_state_mutated is
  False`, `production_wired is False`, `anatomical_completeness_certified is False`,
  `surface_mass_overlay_generated is False`, `source_effective_segment_payloads_consumed is
  False`; all must be present. Contract §1 table: "flags `validation_only`,
  `dynamics_readiness_claimed`, `physical_state_mutated`, `production_wired`,
  `anatomical_completeness_certified`, `surface_mass_overlay_generated`,
  `source_effective_segment_payloads_consumed` | fixed `v1` semantics | all safety-relevant
  ones are `false`". [D5 exercised: a `true` source-effective flag is terminal.]
- **R14 — unassigned cells surfaced and consistent (CON-3/7) [D2].** Root carries
  `unassigned_cell_ids` (list), `unassigned_cells` (list), `all_supplied_cells_assigned`
  (bool). On a root-`complete` report all three must agree with `complete`:
  `unassigned_cell_ids == []`, `unassigned_cells == []`, `all_supplied_cells_assigned is True`;
  any disagreement is a self-contradictory report → REJECT. Any report with unassigned cells
  fails R2 first (strictest D2). Contract §2 `partial` row (quoted in R2) and §3: "Root
  `unassigned_cells[]` keeps each cell's `assignment_status`; consumers MUST surface these as
  explicit gaps in any assembly record. Unassigned cells MUST NOT be merged into a body,
  distributed by proportion, or dropped silently (CON-3/7)."
- **R15 — no recombination, no runtime wiring (CON-15) [D3].** Any field at root or in a body
  from the reserved set {`composite_of`, `composite`, `is_composite`, `recombined`,
  `recombination`, `parallel_axis_applied`, `aggregated_from`, `combined_from`} → REJECT. The
  validator itself provides no composite math. Contract CON-15: "**Parent composition is
  external.** v1 frames are flat, pre-composed transforms"; §2 `unsupported`/CON-5 and §5:
  "no recombination claims"; status line: "No runtime wiring."
- **R16 — v1 flat-frame purity; no lineage schema (CON-15/D4).** `schema_version` other than
  v1, or any field from the reserved lineage set {`frame_lineage`, `parent_frame`,
  `composed_from`, `frame_lineage_schema`, `lineage`} at root or in a body → REJECT. Contract
  CON-15: "Frame lineage, if needed, is carried outside v1; the v2 lineage schema is D4 and is
  **not** invented here."

Cross-cutting: **R0 — reader cross-check.** The existing reader
(`tools/material_volume_body_export_reader.py::summarize_export_report`) is run on the raw
report as an independent structural check; any reader refusal is preserved as an additional
failure. The validator reads the RAW report for its own rules (the reader's summary hard-codes
`dynamics_readiness_claimed: False` in its output, so its summary is never trusted for flag
values). Preservation duty (CON-4/6): when rejecting, `blocking_cell_ids`,
`blocking_assignment_statuses`, `reason_codes`, and `detail` are echoed into the verdict.

## Frozen acceptance tests

- **T-ACC** the clean example report (verbatim copy of
  `tools/material_volume_body_export_example_report.json` into THIS agent's fixtures/) →
  ACCEPT, both bodies eligible.
- Reject fixtures (each = the accept copy mutated in exactly one way, mutants generated by
  `fixtures/make_fixtures.py`, stored as frozen JSON in `fixtures/`, never touching `tools/`):
  T-R2a `partial` root status; T-R2b `blocked` root status (with a `not_exported` body carrying
  `blocking_cell_ids`, echoed in the verdict); T-R2c `unsupported`; T-R2d `refused`; T-R2e
  unknown root status `"assembled"`; T-R2f case-variant root status `"Complete"` + body
  `"Exported"` [adversarial A3]; T-R3a `"Validation_Only_Admissible"`; T-R3b `"admissible"`;
  T-R4a body hash removed; T-R4b hash 63 hex chars; T-R4c body hash ≠ root hash on a
  `complete` report; T-R4d uppercase hex hash; T-R4e/f recomputation path: supplied admission
  document matching / mismatching a synthetic report's recorded hash; T-R5a `not_exported` body
  (null properties); T-R5b `not_exported` body WITH mass properties (placeholder); T-R6a mass
  unit `"g"`; T-R6b negative mass; T-R6c `frame_invariant: false` on mass; T-R7 volume unit
  `"cm^3"`; T-R8 COM frame ≠ body frame; T-R8b COM `value` of 2 numbers; T-R9a truncated tensor
  (2×3) [adversarial A1]; T-R9b transposed off-diagonal pair (asymmetric) [adversarial A2];
  T-R9c `principal_axis_transform_applied: true`; T-R9d `off_diagonal_terms_preserved: false`;
  T-R9e `full_symmetric_tensor: false`; T-R9f tensor unit `"kg m^2"`; T-R9g tensor frame ≠ body
  frame; T-R10a left-handed rotation (det = −1); T-R10b scaled non-orthonormal rotation;
  T-R10c `handedness: "left"`; T-R10d `coordinate_unit: "cm"`; T-R11a `cell_provenance`
  stripped; T-R11b owned cell absent from provenance; T-R11c duplicate cell row with
  conflicting owner; T-R11d `mass_owner_ids` ≠ provenance owners; T-R11e `mass_source_kind`
  wrong; T-R12a root `dynamics_readiness_claimed: true`; T-R12b body-level readiness flag true;
  T-R12c deeply nested `{"admission": {"dynamics_ready": true}}` [adversarial A4]; T-R13a
  `production_wired: true`; T-R13b `physical_state_mutated: true`; T-R13c
  `source_effective_segment_payloads_consumed: true` [D5]; T-R13d `validation_only: false`;
  T-R14a `complete` with one unassigned cell id; T-R14b `all_supplied_cells_assigned: false`;
  T-R15 `composite_of` present [D3]; T-R16 `frame_lineage` present [D4].
- Decision-request exercises (strictest reading, all REJECT): D1 ← T-R12a/b/c; D2 ← T-R2a +
  T-R14a/b; D3 ← T-R15; D4 ← T-R16; D5 ← T-R2c + T-R13c + an extra fixture with
  `material_mass_source_provenance.mass_authority = "source_effective_segment_mass"` (T-D5).

## Adversarial self-probe (falsifier execution; ≥3 fixtures, 4 planned + 1 limit probe)

- A1 truncated tensor (row dropped) while flags claim full → MUST REJECT (R9).
- A2 transposed off-diagonal pair (asymmetric tensor) while flags claim preserved → MUST
  REJECT (R9 symmetry).
- A3 status string case-variants (`"Complete"`, `"Exported"`) → MUST REJECT (R2/R5 exact
  matching).
- A4 readiness claim in a nested field not named at root → MUST REJECT (R12 recursive scan).
- A5 (pre-declared limit probe) silently diagonalized tensor — off-diagonals zeroed, symmetry
  and flags kept — PREDICTED: validator ACCEPTS (statically indistinguishable from a genuinely
  diagonal authored body without the reference documents). This is a named LIMIT, not a rule
  bypass; mitigation is R4's supplied-document recomputation path.

## Recorded LIMITS (declared before the run)

1. `admission_report_sha256` and `input_hashes` recomputation is only checkable when the source
   documents are supplied; otherwise presence + well-formedness + root↔body consistency.
2. A wrong-but-symmetric, correctly-flagged tensor (A5 class) is undecidable statically;
   integrity anchors are the hashes, verifiable only against supplied documents.
3. R4(b) root↔body hash equality is enforced only on root-`complete` reports: the exporter's
   `_blocked_group` legitimately hashes a different document subset per body on blocked
   reports, so equality there would be an invented constraint.

## DECISION REQUESTS (the five Astra-reserved spots; validator implements the STRICTEST reading)

- **D1** readiness promotion → enforced by R12: any readiness claim anywhere = REJECT; no
  promotion path exists in this validator.
- **D2** `partial` policy → enforced by R2/R14: `partial` (and any unassigned cell) = REJECT
  always; no explicit-subset path exists.
- **D3** composite recombination → enforced by R15: any recombination claim = REJECT; the
  validator computes no composite math.
- **D4** parent-frame lineage schema → enforced by R16: any lineage field / non-v1 version =
  REJECT.
- **D5** transport path for source-effective masses → enforced by R2/R11/R13: `unsupported`
  status, non-`reconstructed_tissue_mass` authority, or any consumed source payload flag =
  REJECT.

## AMENDMENT A1 (appended before implementation, after inspecting real exporter output)

- **R12 scope fix.** `dynamics_readiness_claimed` is required present-and-exactly-`False` at
  ROOT only. The exporter's per-body records do not carry this flag, so requiring it per body
  would false-reject clean reports. Bodies remain fully covered by the recursive claim scan
  (any claim-shaped key anywhere with a value that is not exactly `False`/`null` = REJECT);
  absence of the flag on a body is not a claim.
- **Per-record `reason_codes` scope.** Root `reason_codes` is required (list). Body
  `reason_codes` is required ONLY for `not_exported` bodies (contract §2: "carry
  `reason_codes` + `blocking_cell_ids`"); on `exported` bodies it is checked only if present.
- **R1 addition.** A root-`complete` report with an empty `body_groups` list is rejected
  (a consumable unit requires at least one body record).
