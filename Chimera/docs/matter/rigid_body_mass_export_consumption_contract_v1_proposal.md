# Consumption contract for `chimera.rigid_body_mass_export.v1` — proposal v0.9

**Status: PROPOSED contract for the dynamics lane. No runtime wiring.**
Consumer-side code does not exist and is not authorized by this document.
Parent composition stays **external and pre-composed** under v1 (flat frames).
Five decisions at the end require **Astra's architectural approval**; work
stops there.

**Non-claims.** Nothing in v1 establishes anatomical correctness, mechanical
qualification, or dynamics readiness. `dynamics_readiness_claimed` is always
`false`. No combination of v1 fields implies readiness (CON-14).

## 1. Authoritative record

A consumable unit is one body record (`body_groups[i]`) inside one export
report produced by `tools/material_volume_body_export.py` from inputs that the
exporter itself revalidated (never from a caller-supplied pass flag).

| field | authority | notes |
|---|---|---|
| `body_id` | identity of the authored rigid body | authored grouping only; never inferred from stiffness/materials/anatomy |
| `owned_cell_ids` | the body's owned cells | one mass owner per cell, exporter-enforced |
| `mass_properties.mass` | `{value, unit: kg, coordinate_frame: "frame_invariant", frame_invariant: true}` | authoritative mass |
| `mass_properties.volume` | `{value, unit: "m^3", frame_invariant: true}` | informational |
| `mass_properties.center_of_mass` | `{value[3], unit: "m", coordinate_frame: frame_id}` | COM in the authored frame |
| `mass_properties.inertia_tensor_about_com` | `{value[3][3], unit: "kg*m^2", coordinate_frame: frame_id, basis: "authored_body_frame", full_symmetric_tensor: true, off_diagonal_terms_preserved: true, principal_axis_transform_applied: false}` | **full** symmetric tensor about COM; all 9 entries retained |
| `body_frame` | `{frame_id, handedness: "right", coordinate_unit: "m", domain_from_body: {rotation, origin_m}}` | `x_domain = rotation · x_body + origin_m` |
| `cell_provenance[]` | per cell: `mass_owner_id`, `region_id`, `material_id`, `density_kg_m3`, `density_source`, `density_conditions` | travels with the body; never summarized away |
| `material_mass_source_provenance` | `mass_authority`, `mass_source_kind`, `integration_model`, `material_records[]`, `mass_owner_ids[]`, overlay/source-consumption flags (all `false` in v1) | reconstructed-volume provenance |
| `admission_status` + `admission_report_sha256` | revalidated input-gate result and its binding hash | gate only, not readiness |
| `input_hashes` | SHA-256 of manifest, partition, body-group documents (canonical JSON) | integrity anchors |
| `export_status`, `reason_codes` | per-record disposition | see §2 |
| root `unassigned_cell_ids`, `unassigned_cells[]`, `all_supplied_cells_assigned` | supplied cells with no authored group | see §3 |
| flags `validation_only`, `dynamics_readiness_claimed`, `physical_state_mutated`, `production_wired`, `anatomical_completeness_certified`, `surface_mass_overlay_generated`, `source_effective_segment_payloads_consumed` | fixed `v1` semantics | all safety-relevant ones are `false` |

## 2. Status handling (exhaustive)

Root `export_status`:

| status | meaning | consumer handling |
|---|---|---|
| `complete` | all supplied cells assigned; all bodies exported | MAY consume `exported` bodies as **static** mass properties (CON-1/2). Readiness NOT implied |
| `partial` | bodies exported but some supplied cells unassigned | **Silent partial assembly FORBIDDEN.** Default: REJECT. Explicit subset consumption is permitted only under decision D2 and MUST carry `unassigned_cell_ids` forward as acknowledged gaps and mark the model incomplete (CON-3) |
| `blocked` | admission failed (missing density, unresolved/conflicted ownership, domain mismatch, geometry refusal) | REJECT for dynamics consumption; preserve `blocking_cell_ids` / `blocking_assignment_statuses` for diagnostics only (CON-4) |
| `unsupported` | source-effective segment mass authority | REJECT. Source masses are **never** consumed; no substitution from any other source (CON-5) |
| `refused` | malformed/inconsistent request or input | REJECT; preserve `reason_codes`/`detail` (CON-6) |

Per-body `export_status`:

| status | handling |
|---|---|
| `exported` | `mass_properties` present and authoritative under CON-1/9/10/11 |
| `not_exported` | `mass_properties` is `null` — **no placeholder bodies, no estimated masses**; carry `reason_codes` + `blocking_cell_ids` (CON-4) |

## 3. Unexported bodies and unassigned cells

- `not_exported` bodies are diagnostic records. A consumer MUST NOT assemble
  a body it did not receive properties for, and MUST NOT synthesize
  substitutes (CON-7).
- Root `unassigned_cells[]` keeps each cell's `assignment_status`; consumers
  MUST surface these as explicit gaps in any assembly record. Unassigned cells
  MUST NOT be merged into a body, distributed by proportion, or dropped
  silently (CON-3/7).

## 4. Binding rules

- **CON-1** Only `exported` bodies with non-null `mass_properties` are
  consumable, and only as static mass properties.
- **CON-2** `complete` authorizes static consumption of exported bodies
  only. Readiness is out of scope (CON-14).
- **CON-3** No silent partial assembly (see `partial` above).
- **CON-4** Blocked/not-exported records are diagnostics, never inputs.
- **CON-5** `unsupported` (source-effective) is terminal: nothing is
  consumed; source payloads never enter dynamics by any path in v1.
- **CON-6** `refused` reports are terminal.
- **CON-7** Unassigned cells and missing bodies are surfaced gaps.
- **CON-8** Ownership is taken verbatim from `cell_provenance` /
  `mass_owner_id`. **Inferred ownership is forbidden** (no derivation from
  anatomy, stiffness, region labels, or connected components).
- **CON-9** The full symmetric tensor is authoritative. **Dropped
  off-diagonal terms are forbidden**; silent principal-axis frames are
  forbidden (`principal_axis_transform_applied` must remain `false` in any
  forwarded record). A consumer that diagonalizes MUST do so as an explicit,
  documented, consumer-side transformation with its own error accounting and
  MUST retain the original record.
- **CON-10** Frame convention `x_domain = rotation · x_body + origin_m`;
  right-handed, meters. `rotation` is proper orthonormal **as authored and
  never repaired** — a consumer whose loader would "repair" or re-orthonormalize
  MUST refuse instead.
- **CON-11** Units: kg, m, kg·m², m³ as declared per field; mass and volume
  frame-invariant; COM and inertia expressed in `frame_id`.
- **CON-12** Provenance travels with the body (`cell_provenance`,
  `material_mass_source_provenance`, `mass_source_kind:
  "reconstructed_material_volume"`); stripping provenance voids the contract.
- **CON-13** Integrity: `input_hashes` and `admission_report_sha256` MUST be
  verified on receipt against the documents actually delivered; any mismatch
  is a corruption/tamper refusal. `admission_status` MUST be
  `validation_only_admissible`; anything else is non-consumable.
- **CON-14** **No automatic readiness claim.** `dynamics_readiness_claimed` is
  `false` and no field combination may be read as readiness. Readiness is a
  separate future act under D1.
- **CON-15** **Parent composition is external.** v1 frames are flat,
  pre-composed transforms (proven equivalent to two-step composition on the
  FC coupon, ≤ 9.4e-16). Frame lineage, if needed, is carried outside v1;
  the v2 lineage schema is D4 and is **not** invented here.

## 5. Unresolved decisions — require Astra's architectural approval (STOP)

| id | decision | why architectural |
|---|---|---|
| D1 | Readiness promotion: authority and criteria that may later turn an export into a dynamics-ready body | introduces a new claim class |
| D2 | `partial` policy: reject-by-default vs explicit subset binding with acknowledged gaps | cross-lane assembly semantics |
| D3 | Composite recombination: may consumers combine exported bodies (parallel axis) into composites, who owns that math and its error accounting | shared numeric authority |
| D4 | Parent-frame lineage schema (`chimera.rigid_body_cell_groups.v2`) | schema change to v1's flat frame contract |
| D5 | Any future transport path for source-effective segment masses | currently prohibited; needs authority design |

Until each is approved, the conservative reading above holds: reject `partial`,
no recombination claims, external pre-composed frames, no source masses, no
readiness. No runtime wiring is proposed or implied by this document.
