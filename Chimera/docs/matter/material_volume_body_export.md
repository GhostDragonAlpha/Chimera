# Explicit rigid-body material-volume export, v1

**Status: isolated compiler/export lane only.** This exporter is not assembly integration and does not claim dynamics readiness. A report's `admission_status: validation_only_admissible` is the input gate result only; it is not a dynamics/assembly-ready flag. The exporter imports only the NumPy material compiler and its validation-only admission adapter. It does not load Chimera runtime state, call setters, wire a recipe, infer body groups, or implement constitutive laws.

## Runnable two-body coupon

```bash
python tools/material_volume_body_export.py \
  --manifest tools/material_volume_body_export_manifest_example.json \
  --partition tools/material_volume_body_export_partition_example.json \
  --groups tools/material_volume_body_export_groups_example.json
```

The command emits deterministic `chimera.rigid_body_mass_export.v1` JSON to stdout. Inspect an already written report with:

```bash
python tools/material_volume_body_export_reader.py body_mass_export.json
```

The group assignment input is versioned `chimera.rigid_body_cell_groups.v1`; its request schema is `tools/material_volume_body_export_schema.json`. A manifest, partition, and authored two-body group example are provided alongside the executable checks `tools/material_volume_body_export_checks.py`.

This synthetic coupon contains two separated unit right-tetrahedra. Cell A has density `12 kg/m^3`, volume `1/6 m^3`, and mass `2 kg`; cell B has density `6 kg/m^3`, volume `1/6 m^3`, and mass `1 kg`. The independently integrated combined partition has mass `3 kg`, volume `1/3 m^3`, COM `(13/12, -5/12, 7/12) m`, and a full symmetric COM inertia tensor. The analytic check converts each exported body tensor back to the domain frame, applies the parallel-axis theorem, and matches the independently computed combined COM and inertia. The groups are explicitly authored synthetic components, not inferred anatomical bodies.

## Input and revalidation

The exporter accepts the same `chimera.fitting_manifest.v1` and `chimera.material_partition.v1` contracts as `material_volume_admission.py`, plus explicit body groups. It **recomputes admission from the actual manifest and partition**; no caller-supplied status/pass flag is accepted. Only `validation_only_admissible` reconstructed-tissue input can produce mass properties. This remains a preflight export, not production wiring or dynamics readiness.

Each body-group row contains a unique `body_id`, a non-empty list of stable `cell_ids`, and an explicitly authored right-handed body frame. Every supplied partition cell absent from the groups is listed in `unassigned_cell_ids`/`unassigned_cells`. It is never silently absorbed into a group or omitted from accounting. The report can therefore be `partial` when explicitly requested groups export successfully but some supplied cells are unassigned. A cell cannot be assigned to multiple body groups; duplicates refuse the request. Each emitted cell also carries its compiler-resolved `mass_owner_id`, region, material, density, density source, and conditions.

A density gap, unresolved proposal, conflict, region mismatch, incomplete domain, or geometry refusal prevents reconstructed mass export. The report marks group outputs `not_exported`, lists blocking cell IDs/statuses where available, and never substitutes a default density or ownership. Source-effective-segment authority returns `unsupported`; no source mass payload is imported, inspected for calculation, or combined with reconstructed masses. Surface-mass overlays are not generated. Existing material ownership checks continue to refuse volume/surface double ownership for the same matter.

## Authored frames and tensor contract

For each group the request supplies `body_frame` with `frame_id`, `handedness: right`, `coordinate_unit: m`, and `domain_from_body: {rotation, origin_m}`. The authored transform is

```text
x_domain = R_domain_from_body * x_body + origin_domain_m
```

`R` must already be finite, orthonormal, and proper (`det R = +1`); it is not normalized or repaired. The exporter computes the volume properties in domain coordinates, then writes the COM as `R^T (COM_domain - origin)` and the full COM inertia as `R^T I_domain R`. It does not diagonalize the tensor, invent principal axes, or remove cross terms. Each property states its units and coordinate frame; mass and volume are explicitly frame-invariant, while COM and inertia name the authored body frame.

The complete symmetric 3x3 inertia tensor is retained. Output metadata records `full_symmetric_tensor: true`, `off_diagonal_terms_preserved: true`, and `principal_axis_transform_applied: false`. `material_mass_source_provenance` records reconstructed-volume authority, integration model, material records and sources, unique owner IDs, and explicit false flags for consuming/generating surface overlays or source-segment payloads.

## Report and hashes

The root and each body record carry the admission status and SHA-256 hashes of the manifest, partition, and group-assignment documents. Each document hash uses UTF-8 compact canonical JSON (sorted object keys, array order preserved); it identifies the exact serialized inputs, including row ordering. An admission-report hash binds the exporter result to its freshly recomputed preflight report. Output records are key-sorted canonical JSON with no timestamps, random IDs, or non-finite numbers.

Possible `export_status` values are:

- `complete`: every supplied partition cell belongs to an authored group and all requested body exports succeeded.
- `partial`: requested groups succeeded but one or more supplied cells were left explicitly unassigned.
- `blocked`: reconstructed-mass admission failed; body properties are not exported.
- `unsupported`: source effective segment authority was selected; body properties are not exported and source values are not consumed.
- `refused`: malformed request, duplicate cell/body ownership, missing group cell, or invalid authored frame.

All reports retain `dynamics_readiness_claimed: false`, `physical_state_mutated: false`, `production_wired: false`, and `anatomical_completeness_certified: false`.

## Focused analytic checks

Run:

```bash
python tools/material_volume_body_export_checks.py
```

The checks cover independent one-simplex raw-moment integrals and recombination of group masses/COM/full inertia to the complete partition total; translation/rotation into authored frames; duplicate and unassigned cell handling; missing-density blocking; source-effective unsupported behavior without mass consumption; rejection of a caller-inserted pass flag and invalid/reflected frames; deterministic hashes/report serialization; and explicit off-diagonal tensor retention. The existing compiler/admission check suites remain separate and runnable.

## Scope limits

Body grouping is an explicit rigid-body modeling input, not a deduction from stiffness, region/material labels, connected components, or anatomy. The exporter handles mass, volume, COM, and COM inertia only. It does not export forces, joints, constraints, attachments, collision geometry, time integration, stiffness, principal-axis frames, or a second mass overlay. It does not infer anatomy, repair geometry, or wire these records into assembly/dynamics.