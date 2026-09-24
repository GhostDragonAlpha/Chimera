# Provenance of the synthetic fixture parts

Every file in this directory is **AUTHORED SYNTHETIC**. None of it is a measurement, and none
of it came from `.tmp/anatomy_compiler/runs/`. The adapter records each part's provenance in
the manifest (`inputs[].admitted_as = "synthetic"`, plus the sha256 of its bytes), so this
table is the human-readable counterpart: what was authored, and against which upstream
*contract* rather than which upstream *data*.

| Part | Role it plays | Authored against | Claim-reference prefix |
|---|---|---|---|
| `anatomy_synthetic.json` | `anatomy_packet` | the anatomy compiler's physiology record shape (`mass_kind`, `status`, `com_fitted`, `inertia_fitted`) | `anatomy:synthetic_anatomy:physiology:<body>` |
| `candidates_synthetic.json` | `attachment_candidates` | `attachment_candidates` revision 5 record shape (`endpoint_roles`, `source_pos_local`, `mechanical_qualification: false`) | `cand:candidates_synthetic:<body>:<site>` |
| `material_volume_synthetic.json` | `material_volume_document` | `tools/material_volume.py` v1 contract; geometry is the two-tetrahedron bipyramid of `tools/material_volume_example.json` with region/owner ids renamed to this fixture's components | `material_volume:materials_synthetic:region:<rid>` |
| `ownership_complete.json` | `ownership_bindings` | this adapter's own ownership schema (`chimera.assembly_ownership.v1`) | — (binds the refs above) |
| `ownership_duplicate.json` | `ownership_bindings` (fixture 2) | as above, with one component given two counting owners | — |
| `ownership_anatomy_transport_only.json` | `ownership_bindings` (fixture 3) | as above, with only transported anatomy mass bound | — |
| `requirements_complete.json` | `mechanical_requirements` | this adapter's requirements schema; anchors/weights/patch area/κ_areal authored by hand | — |
| `requirements_waypoint_incomplete.json` | `mechanical_requirements` (fixture 4) | as above, with patch area and κ_areal deliberately left unauthored | — |

## Numbers, and where they come from

Nothing here is tuned to a target. Each value was chosen first, then the expected result was
computed from it:

* **Densities** `upper-tissue = 2 kg/m³`, `lower-tissue = 4 kg/m³` — round numbers with no
  physical meaning, declared in `density_source` as `AUTHORED SYNTHETIC FIXTURE constant`.
* **Geometry** the bipyramid is two unit tetrahedra, each of volume 1/6 m³. So region-upper is
  `2 × 1/6 = 1/3 kg` and region-lower is `4 × 1/6 = 2/3 kg`, totalling exactly **1 kg**. The
  fixture asserts that total; it is arithmetic, not a fitted constant.
* **Attachment anchors** four corners of a square, ρ = 0.02 m from the patch centre, weights
  0.25 each (positive, summing to 1 as `AttachmentSpec` requires).
* **Patch stiffness** κ_areal = 1×10⁸ N/m³ × A = 0.0016 m² → Kbar = 1.6×10⁵ N/m, which the
  finite-area gate reports as λ_min ≈ 32 N·m/rad against an authored requirement of 1 N·m/rad.

## What is deliberately *not* here

No densities were inferred from anatomy. No mesh was repaired. No missing patch area, stiffness,
material or frame was filled in — where a fixture omits one, it stays absent and the manifest
says so. The synthetic parts are admitted as synthetic; they are never presented as evidence
about the real animal.
