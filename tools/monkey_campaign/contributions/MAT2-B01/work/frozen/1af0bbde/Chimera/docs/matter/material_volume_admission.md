# Fitting-manifest admission adapter, v1

**Status: standalone, opt-in, validation-only. No production wiring.** The adapter compares a caller-supplied material partition to a versioned fitting manifest, invokes the tetrahedral compiler for geometric validation, and emits a deterministic report. It imports no Chimera runtime or physical recipe modules, calls no setters, and does not mutate the manifest, partition, or physical state. `validation_only_admissible` is a result at this boundary—not authorization to change a production recipe.

The adapter does **not** certify that a manifest is anatomically complete. It can detect deviations from the exact domain that the caller declared; a caller can still provide a manifest that omits anatomy. `anatomical_completeness_certified` is always `false`.

## Files and running it

- `tools/material_volume_admission.py` — pure adapter and CLI.
- `tools/material_volume_admission_schema.json` — JSON Schema 2020-12 definitions for either input document. Runtime checks also enforce cross-reference and ownership rules that JSON Schema cannot conveniently express.
- `tools/material_volume_admission_manifest_example.json` and `tools/material_volume_admission_partition_example.json` — matching, runnable two-tetrahedron fixture.
- `tools/material_volume_admission_checks.py` — executable standard-library `unittest` metamorphic suite.

```bash
python tools/material_volume_admission.py \
  --manifest tools/material_volume_admission_manifest_example.json \
  --partition tools/material_volume_admission_partition_example.json
python tools/material_volume_admission_checks.py
```

The CLI writes one canonical JSON report to stdout. Exit status `0` means the declared validation boundary passed; `1` means valid inputs were not admitted (for example, missing expected cells, conflict, unresolved assignment, or incomplete density); `2` means malformed inputs or a named geometry/compiler refusal. No report includes timestamps, random IDs, file paths, or physical-state handles.

## Manifest contract: `chimera.fitting_manifest.v1`

The fitting manifest is an explicit, caller-owned declaration of the intended *fitting domain*:

| Field | Meaning |
|---|---|
| `fitting_id`, `domain_id`, `domain_revision` | Stable identifiers for the fitting and the precise declared domain revision. These are assertions from the producer, not inferred anatomy. |
| `coordinate_frame` | `frame_id`, right-handedness (`right` only), descriptive `coordinate_unit`, and positive finite `scale_to_m`. Every input position is multiplied by this scale to obtain metres. No reflection, frame conversion, or automatic registration is attempted. |
| `vertices` | Exact expected stable `vertex_id` values and three finite coordinates in the declared frame/units. |
| `cells` | Exact expected stable `cell_id` values, each with four distinct stable `vertex_ids` and a declared `component_id`. Component IDs define the manifest's component inventory; they are not inferred from a watertight remainder. |
| `regions` | Exact region catalogue: `region_id`, unique `mass_owner_id`, and `material_id`. Region definitions must match the partition catalogue. Per-cell AI proposals remain on partition rows so unresolved/conflicted proposals are not overwritten by the manifest. |
| `mass_authority` | Required explicit choice: `reconstructed_tissue_mass` or `source_effective_segment_mass`. There is no inferred or combined authority. |
| `source_effective_segment_ids` | Empty for reconstructed tissue mass; one or more opaque stable IDs for source effective segment authority. Numeric legacy mass payloads are neither accepted nor read by this adapter. |
| `matter_ownership` | One or more `{matter_id, representation, mass_owner_id}` declarations. For reconstructed mass, each region owner must be claimed once as `tetrahedral_volume`; for effective-segment authority, the listed source IDs must be claimed once as `source_effective_segment`. A duplicate matter ID or owner is refused. |

Allowed `matter_ownership.representation` values are `tetrahedral_volume`, `surface_mass_overlay`, and `source_effective_segment`. Surface overlays are not supported by the v1 volume compiler and therefore make the ledger non-admissible. In particular, if a matter ID has both `tetrahedral_volume` and `surface_mass_overlay` claims, the report explicitly marks a `volume_surface_ownership_collision`; the same membrane matter cannot be owned by both representations. A thickness-bearing membrane must instead occupy exclusive volume cells in the material partition. A zero-thickness sheet contributes no volume mass.

## Partition contract: `chimera.material_partition.v1`

The partition carries the same declared coordinate frame; stable `vertex_id` + position rows; stable cell rows `{cell_id, vertex_ids, proposals}`; material records `{material_id, density_kg_m3, density_source, conditions}`; the same region catalogue; and the same explicit mass-authority choice. Density may be `null` solely so an incomplete material assignment can be reported instead of silently filled. Missing-density cells remain visible, cannot contribute a total reconstructed mass, and prevent reconstructed-mass admission.

A proposal array has the compiler semantics:

- `[]`: unresolved; no region/owner/material is invented.
- One distinct known region ID: unique candidate ownership.
- Multiple distinct known IDs: conflict; all candidates and candidate owners are retained, with no selected default.
- Repeated identical IDs collapse to consensus. Unknown region references are retained in the row and cause a named refusal; they are never remapped.

The adapter turns stable IDs into a deterministic compiler indexing order only in local arrays. It does not reorder or repair tetrahedron orientation. Geometry must pass the existing compiler's finite-coordinate, positive-orientation, nondegeneracy, conforming manifold, closed-boundary, vertex-link, and strict-overlap checks.

## Correspondence and accounting are different assertions

The compiler emits one accounting row per **supplied** cell. The report's `assignments.supplied_cells_accounted_for` says only that each supplied row has a recorded assignment state; it can be `true` when rows are unresolved, conflicted, missing density, or when expected cells are absent.

`correspondence.intended_domain_fully_represented` is a separate exact comparison to the manifest. It requires matching vertex ID sets, exact coordinate values, frame identifier/handedness/unit, exact `scale_to_m`, cell ID sets, and cell connectivity (vertex order is immaterial for identity comparison). The report lists missing/extra vertices, missing/extra cells, connectivity mismatches, incomplete components, and components with no represented cells. Thus removal of one tetrahedron or an entire declared component cannot be hidden by the fact that the remainder is still watertight.

A changed cell or component inventory is not automatically repaired to match the manifest. To validate a refined mesh, provide a new manifest revision that declares its refined cells. The adapter does not infer which manifest cells a new subdivision replaces.

## Canonical identity versus physical equivalence

Both `identity.expected_geometry_signature` and `identity.supplied_geometry_signature` are SHA-256 digests of sorted records of exact float64 hexadecimal SI-coordinate tetrahedra. Each cell is represented by its four sorted coordinate tokens; the record list is sorted. Stable IDs, region labels, proposal order, input cell order, and local vertex numbering are excluded.

Therefore:

- **Preserve canonical identity:** reorder input cell rows; reorder the vertex table; apply any bijective vertex-ID/index renumbering while preserving coordinates and connectivity. Reordering a tet's four vertex IDs also preserves the identity digest, though the compiler independently requires its signed orientation to remain positive.
- **Do not preserve canonical identity:** rigidly translate/rotate the geometry; uniformly enlarge/shrink it; subdivide cells; change exact coordinates or the tetrahedral cell set. A changed region label does not change geometric identity because labels are outside the geometry digest.
- **May preserve physical equivalence, not exact identity:** a rigid transform preserves total mass, volume, and COM-relative inertia, while transforming the COM and rotating the inertia tensor. For constant density, a uniform scale `s` changes volume and mass by `s^3` and COM-relative inertia by `s^5`; it is not the same dimensional mass-property result. Homogeneous conforming subdivision preserves the integrated properties (within float64 summation tolerance) but changes exact cell identity. Relabeling regions can leave total homogeneous-body properties unchanged while changing the named interface ownership and its A-to-B normal.

Identity is exact, not tolerance-quantized. Physical-equivalence statements are metamorphic properties and need caller-chosen numeric tolerances; the adapter does not declare two distinct signatures equivalent or repair near-equal coordinates. The manifest and partition must exactly correspond in their declared coordinate frame. To represent an intentional transformed or rescaled fitting, declare the corresponding transform/scale and coordinates in both inputs (or issue a new manifest revision); the signature then identifies that declared SI geometry.

## Mass authority and report decisions

The report always records the chosen `mass_authority`, sets `source_segment_payloads_consumed: false`, and never adds legacy source segment values to reconstructed properties.

- Under `reconstructed_tissue_mass`, `reconstructed_mass_properties` is emitted only when domain correspondence, region/owner ledger, assignments, density, and compiler geometry all pass. It is `null` for any incomplete or conflicted state. The compiler's partial subtotal is not promoted to a body total by the adapter.
- Under `source_effective_segment_mass`, source segment IDs are treated as opaque ledger references. Geometry, correspondence, labels, ownership, and the selected source authority can be validation-admissible, but `reconstructed_mass_properties` is always `null`. Density is not consumed for this authority, so missing density is retained as a warning rather than blocking an external-mass-authority geometry check. This adapter never imports or reports effective segment mass values.
- No mixing of these choices, no legacy thin-sheet payload, no duplicate ownership, and no volume/surface overlay double ownership is admitted.

`decision` values:

- `validation_only_admissible`: declared checks passed; still no production import or state mutation.
- `not_admitted`: well-shaped inputs were compared and the report retains the discrepancy/statuses.
- `refused`: malformed input or compiler geometry refusal. `compiler_refusal` contains the stable reason and detail where relevant.

The report includes cell rows sorted by stable cell ID, sorted discrepancy/reason lists, canonical JSON key order, compact separators, ASCII escaping, and `allow_nan=False`. Under either authority, every provided cell has an assignment-status row; the report separately states whether all rows have unique owners and known density. Interfaces are keyed by sorted stable vertex IDs and emitted once, with the compiler's stored A-to-B orientation translated back to stable IDs. Exterior faces and unresolved adjacencies are likewise represented with stable IDs. `anatomical_completeness_certified` is always false, even for an admissible report.

## Unsupported and out of scope

- Anatomical-completeness inference, semantic segmentation, or verification that the manifest itself covers a whole creature/body.
- Fitting, tetrahedralization, geometric repair, vertex welding, node snapping, orientation auto-flips, T-junction resolution, coordinate registration, tolerance-based identity, or inferred cell correspondence after subdivision.
- Non-right-handed frames, reflections, nonuniform affine scaling, per-vertex transforms, multiple coordinate frames in one partition, or implicit unit conversion beyond the declared positive uniform `scale_to_m`.
- Surface-mass overlays, mixing reconstructed tissue mass with source effective skeletal-segment mass, and reading/importing effective segment numeric payloads.
- Constitutive laws, stiffness/dynamics, attachment mechanics, membrane-to-bone mechanics, physical-state setters, recipe mutation, or production wiring.
- Spatially accelerated overlap checks or a separate continuous triangle-surface self-intersection proof; the underlying reference compiler uses its documented quadratic tetrahedron SAT check and combinatorial boundary/manifold validation.

## Executable metamorphic coverage

`python tools/material_volume_admission_checks.py` independently checks cell/vertex list reorder and vertex renumber; exact identity changes versus rigid-transform and uniform-scale physical-property laws; equivalent SI scale declarations; homogeneous subdivision mass-property invariance and identity change; shared-face orientation under a positive tet permutation; region relabeling and normal direction; touching versus overlapping tetrahedra at three scales; removal of one cell and of a whole component; duplicate owner and membrane surface-overlay collision; missing density; unresolved/conflicting proposals; and source-effective authority's no-reconstructed-mass guarantee. The existing `python tools/material_volume_checks.py` exercises the compiler's independent analytic simplex integration oracle and topology refusals.
