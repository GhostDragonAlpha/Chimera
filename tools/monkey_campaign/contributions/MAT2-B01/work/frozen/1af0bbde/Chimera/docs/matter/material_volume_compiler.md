# Material-volume compiler, v1

**Status: standalone NumPy reference; no production wiring.** This compiler supplies material ownership and geometric rigid-body properties only. It does not fit anatomy, infer labels, create tetrahedra, solve membrane-to-bone attachments, or introduce a constitutive law.

## Decision: conforming, positively oriented tetrahedral cells

Use a tetrahedral complex as the first bounded volume representation. It supports piecewise-constant material density, internal interfaces on shared triangular faces, and exact polynomial integration for each cell. The compiler consumes the already-fitted cell complex and per-cell AI proposals; fitting and attachment mechanics remain separate tasks.

The domain is the **union of all supplied tetrahedra**, not an inferred creature envelope. A proposal is a list of region IDs for each input cell. Every resolved tetrahedron has **one region, one material, one globally unique `mass_owner_id`**, and one density. Therefore a region may own many cells, but the v1 contract uses a region as the unit of unique mass ownership; splitting one semantic region across independently owned subregions requires distinct region IDs:

- `[]` — unresolved; no owner/material/density is assigned.
- `["region-id"]` — exactly one resolved owner and material.
- Multiple distinct IDs — explicit conflict, with all proposed region and owner IDs retained. The cell is not averaged or integrated into the body total.
- Repeated copies of the same ID are consensus, not a conflict. Unknown IDs are rejected.

There is one output accounting row for every input tetrahedron. The full-body mass properties are JSON `null` unless every cell resolves. A separately named resolved-only subtotal can be useful for diagnosis, but is never a body total. An absent tetrahedron that was never supplied cannot be inferred from this input contract; caller-side comparison to a fitting/domain manifest is required if omission relative to an intended anatomy must be detected.

### Input contract: `chimera.material_volume.v1`

A UTF-8 JSON object has exactly these top-level fields (unknown fields are rejected so legacy mass values cannot be silently ignored):

| Field | Contract |
|---|---|
| `schema_version` | Exact string `chimera.material_volume.v1`. |
| `coordinate_unit` | Exact string `m`; right-handed Cartesian coordinates. |
| `density_unit` | Exact string `kg/m^3`; v1 does no implicit conversion. |
| `mass_source_kind` | Exact string `reconstructed_material_volume`. |
| `vertices_m` | Finite numeric `nV x 3` array, `nV >= 4`; no coincident distinct node positions and no unused nodes. |
| `tetrahedra` | Integral `nT x 4` array, `nT >= 1`, zero-based node IDs. Every row has four distinct IDs, unique unordered node set, and **strictly positive signed determinant** `det([v1-v0,v2-v0,v3-v0])`. The compiler never reorders or repairs a cell. |
| `materials` | List of unique `{material_id, density_kg_m3, density_source, conditions}` records. Density must be finite and positive; source and conditions are required and nonblank. |
| `regions` | List of unique `{region_id, mass_owner_id, material_id}` records; each mass-owner ID is unique across regions and each material reference must exist. Optional `stiffness_pa` is opaque, inert metadata for the independence control only: the mass compiler neither validates nor uses its value. |
| `cell_proposals` | Exactly `nT` rows in tetrahedron order. Each row is an array of region IDs, as described above. |

Minimal runnable fixture (two tetrahedra forming a unit-height triangular bipyramid):

```json
{
  "schema_version": "chimera.material_volume.v1",
  "coordinate_unit": "m",
  "density_unit": "kg/m^3",
  "mass_source_kind": "reconstructed_material_volume",
  "vertices_m": [[0,0,0],[1,0,0],[0,1,0],[0,0,1],[0,0,-1]],
  "tetrahedra": [[0,1,2,3],[0,2,1,4]],
  "materials": [
    {"material_id":"upper-tissue","density_kg_m3":2.0,"density_source":"fixture","conditions":"uniform"},
    {"material_id":"lower-tissue","density_kg_m3":4.0,"density_source":"fixture","conditions":"uniform"}
  ],
  "regions": [
    {"region_id":"region-A","mass_owner_id":"owner-A","material_id":"upper-tissue"},
    {"region_id":"region-B","mass_owner_id":"owner-B","material_id":"lower-tissue"}
  ],
  "cell_proposals": [["region-A"],["region-B"]]
}
```

Save as `bipyramid.json`, then run:

```bash
python tools/material_volume.py bipyramid.json
python tools/material_volume_checks.py
```

The CLI writes compiled JSON to stdout; exit 0 means complete, exit 1 means valid geometry but incomplete/conflicted ownership, exit 2 means a named input refusal. The compiler does not write evidence or mutate project/production files.

## Derivation

For positively oriented tet vertices `x_i` (`i=0..3`),

```text
V_t = det([x_1-x_0, x_2-x_0, x_3-x_0]) / 6
m_t = rho_t V_t
c_t = sum_i x_i / 4
```

Uniform volume measure on a 3-simplex has barycentric moments `E[lambda_i]=1/4` and `E[lambda_i lambda_j]=(1 + delta_ij)/20`. Thus the central second-moment matrix and inertia tensor of one tet are

```text
Q_t(c_t) = integral rho (x-c_t)(x-c_t)^T dV
          = (m_t/20) sum_i (x_i-c_t)(x_i-c_t)^T
I_t(c_t) = trace(Q_t) identity - Q_t
```

For all resolved cells, `M = sum m_t`, `C = sum(m_t c_t)/M`, and the inertia about the total COM uses the parallel-axis identity

```text
I_C = sum_t [ I_t(c_t) + m_t ( (d_t·d_t) identity - d_t d_t^T ) ],
 d_t = c_t - C.
```

These are volume/density integrals; no stiffness or elastic response enters. Under a uniform coordinate scale `s`, `V -> s^3 V`, `m -> s^3 m`, and `I -> s^5 I`. Refining a homogeneous tet into a conforming tet subdivision preserves the integral (up to float64 summation roundoff).

## Interfaces and orientation

A triangular face key is its three sorted node IDs, so a conforming shared face is stored once. Exterior faces are identified by one incident cell; an internal face has exactly two incident cells. Same-region internal faces are omitted. A cross-region face produces one `MaterialInterface` record with both region, mass-owner, and material IDs.

Convention: region IDs are sorted lexically to choose A and B; `vertices` is the outward face order of A's positively oriented tetrahedron, so `cross(x1-x0, x2-x0)` and `normal_a_to_b` point **from region A into region B**. The reverse side is implicit, not a second record. Exterior boundary-face vertices point outward from their incident tet. Faces adjacent to unresolved/conflicted cells are listed in `unresolved_adjacencies`, not fabricated into an interface.

For a region's closed boundary, combine its resolved exterior faces with each interface oriented outward from that region (A uses the stored order; B reverses it). The two region contributions on a shared interface are exact opposites: both area-vector terms cancel and the signed tetrahedral-volume surface terms cancel. Region-local closure is therefore testable without duplicating the stored interface.

## Membrane thickness and ownership

V1 has **no extra areal-mass term** in a volume compilation. A zero-thickness membrane has zero volume and contributes no bulk mass here. If a membrane of thickness `t > 0` and density `rho` is a distinct material layer, its matter must be represented by exclusive tetrahedral volume cells (`V_layer` integrates to the swept layer volume; for an ideal flat uniform sheet the limit is `rho * area * t`). Assign those cells to the membrane material region exactly once. Neighboring tissue cells must cover only the remaining, disjoint volume. If the existing tissue volume already includes the membrane matter, keep those cells owned by that volume and do not add a second membrane representation.

`validate_mass_source_claims()` rejects a body ledger mixing `reconstructed_material_volume` with legacy `thin_sheet` or `effective_skeletal_segment` claims. This is deliberately conservative: v1 has no geometric proof that those external contributions are disjoint, so it refuses even an allegedly disjoint mixed ledger. The JSON schema also refuses unknown fields, including imported segment-mass payloads. A future explicit mixed-dimensional compiler would need a declared disjointness/ownership proof before relaxing this boundary.

## Checks actually performed and honest limits

Before integrating, v1 checks:

- finite numeric coordinates, array shapes/dtypes, valid integer indices, repeated IDs within cells, duplicate unordered tetrahedra, unused nodes, and exactly coincident distinct node positions;
- positive signed cell orientation (inverted cells are rejected, never flipped) and a scale-normalized nondegeneracy gate `|det| / max_edge^3 > 64 * float64_epsilon`; arithmetic overflow/nonpositive computed volume is rejected;
- exact face incidence: `>2` cells on one node-ID face is non-manifold; a shared face must have opposite outward orientation;
- an exterior boundary with exactly two oppositely directed boundary triangles per boundary edge, and one connected vertex link that is a disk for a boundary node or a sphere for an interior node;
- strict tetrahedron interior overlap using an x-sorted AABB broad phase and convex-polyhedron separating-axis tests (tet face normals plus cross products of edge directions). Projection overlap at or below `128 * float64_epsilon * max(cell edge)` is treated as contact/tolerance, not positive-volume overlap;
- one region mass-owner ID per region, a known material for each region, positive finite density with source/conditions, one proposal row per cell, and known proposal IDs;
- conservation fixtures: one shared interface, outward area-vector closure and signed-volume closure per region, and no omission of any supplied cell from the assignment result.

This is an O(nT^2) worst-case reference overlap check, not a production spatial index. It checks a **conforming shared-node-ID simplicial complex**; it does not weld nodes, repair T-junctions, infer an intended outer envelope, or certify anatomical completeness. The closed-manifold edge/link checks reject the tested cracks and non-manifold cases, and pairwise SAT rejects strict cell-interior overlap; near-contact within its stated float64 tolerance is deliberately ambiguous. The boundary is checked combinatorially, not with a separate triangle-triangle surface self-intersection routine. Passing establishes only the declared input contract—not that a mesh is a correct anatomy or that AI labels are biologically valid.

## Integration record

The input schema names a single `mass_source_kind`. Every resolved cell emits `cell_id`, `region_id`, `mass_owner_id`, `material_id`, `density_kg_m3`, density source, and conditions. Each cross-region interface carries one face key, ordered node triple, both region/owner/material IDs, area, and A-to-B normal. The output carries `complete`, all per-cell statuses/candidates, unresolved/conflict IDs, geometric volume, total properties or `null`, clearly marked resolved-only subtotal, region subtotals, exterior faces, unresolved adjacencies, and connected-component count.

The engine integration owner must treat the compiled `mass_properties` as the sole reconstructed rigid-body mass source. Do not add imported effective skeletal-segment masses, old thin-sheet masses, or renderer/attachment proxy masses to it. An unresolved compile is not eligible for physical import. Membrane-to-bone forces remain the attachment worker's responsibility; `normal_a_to_b` only describes region ownership geometry.

## Validation record (initial failures retained)

The test battery is directly runnable with the Python standard library; no pytest installation is required.

- Initial `python tools/material_volume_checks.py`: **14/15 passed**. The intended non-manifold-face negative control mistakenly repeated the lower bipyramid tetrahedron, so the earlier, correct `duplicate_tetrahedron` guard fired. Corrected only the fixture: three distinct positive-volume tets now share one face, and the check asserts `non_manifold_face`.
- Next run after that correction: **15/15 passed**. Later, while expanding the battery for all-unresolved JSON safety, edge/vertex-link defects, and T-junction topology, the T-junction fixture initially failed at `inverted_tetrahedron`; one small tet had reversed node order. The compiler correctly refused it before topology checks. Reordered that fixture positively without changing the intended subdivision geometry, so it reaches the intended `non_manifold_boundary` check.
- Focused run after the T-junction correction: **16/16 passed**. A separate inert-stiffness-metadata check was then added; final focused run: **17/17 passed**. No refusal threshold was relaxed and no production code changed to accommodate either fixture error.
- `python -m py_compile tools/material_volume.py tools/material_volume_checks.py`: passed. `python tools/material_volume.py tools/material_volume_example.json`: exited 0; analytic bipyramid result is volume `1/3 m^3`, mass `1 kg`, COM `(0.25, 0.25, -1/12) m`, one interface of area `0.5 m^2` oriented `(0,0,-1)`.
- Environment note: `pytest -q tools/material_volume_checks.py` is unavailable here (`pytest: command not found`); run the documented `python` command instead. An unrelated existing `Chimera/tools/surface_energy_checks.py` invocation from the `Chimera/` working directory also stopped at its `evidence_output` import path (`ModuleNotFoundError`); that surface-energy suite is outside this compiler's dependency/test path and was not used as evidence for this change.

The failed fixture assertions and corrections are preserved here as a test-history record; the live battery retains the corrected negative controls.
