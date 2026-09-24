# Consumption contract for `chimera.rigid_body_mass_export.v1` — v1.0 (D1–D5 decided)

**Status: APPROVED for static inspection and validation only (D1). No runtime
wiring.** Consumer-side code does not exist and is not authorized by this
document. Parent composition stays **external and pre-composed** under v1 (flat
frames). Decisions D1–D5 are decided (§5, recorded 2026-09-24); runtime binding
requires a separate **Astra-approved qualification gate** (D1), and work stops
there. The file name retains `_proposal` for pointer stability.

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
| `partial` | bodies exported but some supplied cells unassigned | **REJECT for assembly (D2), including any subset binding.** Diagnostic tools may inspect exported bodies only while explicitly displaying omitted bodies and unassigned cells (CON-3) |
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
- **CON-3** No partial assembly (D2). `partial` reports are rejected for
  assembly — including explicit subset binding (the earlier subset-binding
  reading is **superseded**). Diagnostic inspection of exported bodies is
  permitted only when the diagnostic explicitly displays omitted bodies and
  unassigned cells.
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
  `validation_only_admissible`; anything else is non-consumable. Artifact
  identity claims in receipts and manifests follow §6.
- **CON-14** **No automatic readiness claim.** `dynamics_readiness_claimed` is
  `false` and no field combination may be read as readiness. Readiness is a
  separate future act under D1.
- **CON-15** **Parent composition is external.** v1 frames are flat,
  pre-composed transforms (proven equivalent to two-step composition on the
  FC coupon, ≤ 9.4e-16). Frame lineage, if needed, is carried outside v1;
  the v2 lineage schema is D4 and is **not** invented here.

## 5. Decisions D1–D5 (decided 2026-09-24)

All five previously open decisions are decided. Each is recorded as issued,
with its operative effect on §2/§4. Nothing here authorizes runtime wiring;
runtime binding requires the separate Astra-approved qualification gate named
in D1.

| id | decision (as issued) | operative effect |
|---|---|---|
| D1 | Approve the contract for **static inspection and validation only**. Exporter success cannot promote a body to dynamics-ready. Runtime binding requires a separate Astra-approved qualification gate. | CON-2/CON-14 stand: no readiness-promotion authority exists in v1; the claim class stays closed |
| D2 | **Reject `partial` reports for assembly.** Diagnostic tools may inspect exported bodies only while explicitly displaying omitted bodies and unassigned cells. No subset-binding exception yet. | CON-3 amended: subset consumption is not permitted (the earlier subset-binding reading is superseded); diagnostics must explicitly display omitted bodies and unassigned cells |
| D3 | Allow **read-only aggregate calculations for verification**, with explicit frames and disjoint cell ownership. Do not collapse bodies, infer joints, or change runtime grouping. | new CON-16: verification-only aggregation math is permitted read-only; body collapse, joint inference, and runtime regrouping stay forbidden |
| D4 | Retain v1's flat, pre-composed transforms. Defer v2. | CON-15 stands; the lineage schema (`chimera.rigid_body_cell_groups.v2`) stays deferred and is not designed here |
| D5 | Source-effective masses remain **unsupported**. No fallback or transport is authorized. | CON-5 stands for v1 with no substitution path; any future transport would need new authority design |

- **CON-16 (D3)** Read-only aggregate calculations are permitted for
  **verification only**: composite mass, COM, and full inertia may be computed
  across exported bodies (e.g. parallel-axis aggregation) provided that (a)
  frames are stated explicitly, (b) cell ownership remains disjoint with one
  mass owner per cell taken verbatim from `cell_provenance`, (c) the result is
  recorded as a verification artifact with its own error accounting, and (d)
  no body record is collapsed, rewritten, or merged. Inferring joints,
  collapsing bodies, or changing runtime grouping is forbidden.

## 6. Identity and hashing rule (binding on receipts and manifests)

Every artifact-identity claim MUST name exactly one of the three identities
below and MUST NOT conflate them:

| identity | definition |
|---|---|
| **raw-file SHA-256** | SHA-256 over the exact bytes materialized on disk at claim time, with no transformation. Checkout-materialization dependent (finding M-1). |
| **Git blob identity** | the Git blob OID of the committed bytes at a named revision (`git ls-tree <rev> -- <path>`). Portable across checkouts; pins a revision. |
| **canonical-content SHA-256** | SHA-256 over canonicalized content bytes, defined only for **declared text artifacts**: the raw bytes with every CRLF (`\r\n`) and lone CR (`\r`) replaced by LF (`\n`). No other transformation — no BOM handling, no trailing-newline, whitespace, or Unicode normalization. |

- Newline normalization is restricted to artifacts explicitly declared text
  in the manifest. Binary artifacts have no canonical form; identify them by
  raw-file SHA-256 and/or Git blob identity only.
- The three identities are distinct claims. **A canonical-content match can
  never satisfy a raw-byte equality claim**, and neither can substitute for a
  Git blob identity claim.
- Any raw-file SHA-256 mismatch across checkouts MUST be adjudicated by Git
  blob identity and canonical-content SHA-256 before being recorded as content
  drift (V3-F / M-1 precedent: 13/14 raw hashes differed across checkouts with
  zero content drift).

No runtime wiring is proposed or implied by this document. Readiness is not
claimed; runtime binding stops at the separate Astra-approved qualification
gate (D1).
