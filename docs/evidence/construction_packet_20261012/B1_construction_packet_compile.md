# B1 — Construction packet compile evidence (2026-10-12)

Gate under test (§13, B1, verbatim):

> Two asymmetric solid templates, a tapered layer and an open-surface refusal
> control; stable material/region/boundary IDs and resource inventory |
> Geometry refusals, positive volumes, mass/COM/inertia, correct interface
> orientation and no overlapping ownership; original compiler checks reused

Baseline: branch `WK-ENGINE-PATHS-20260929-PR`, HEAD
`f5afc75131b45b2ac990eaa2277bbdae0ddbc9de` (the B0-pinned baseline; see
`B0_baseline_and_ownership_map.md`).

## What was built

One narrowly scoped construction packet, `tools/construction_packet/packet.py`,
driving the **existing** `tools/material_volume.py` compiler
(schema `chimera.material_volume.v1`). No new geometry or physics code: the
packet only authors inputs and asserts on compiler outputs. Acceptance battery:
`tools/construction_packet/test_construction_packet.py` (23 tests).

Explicit ownership before coding (per §13): each template declares its
materials (`MaterialSpec`: density + non-empty `density_source` +
`conditions`), regions (`RegionSpec`: region → exactly one `mass_owner_id` +
material), and per-cell proposals. Mass ownership is catalogue-level and
enforced (`duplicate_mass_owner_id`); cell ownership is proposal-level and
conflicted cells are never silently merged. DOF ownership is deferred to B2 by
design: the packet produces parts, not runtime bodies.

## Templates and compiler results (from `B1_resource_inventory.json`)

| template | verts | cells | volume m³ | mass kg | COM m | interfaces | boundary faces |
|---|---|---|---|---|---|---|---|
| `template_wedge_a` (granite, L0.30 W0.20 H0.12) | 6 | 3 | 0.0036 | 9.72 | (0.1, 0.0666667, 0.06) | 0 | 8 |
| `template_wedge_b` (steel, L0.22 W0.34 H0.09) | 6 | 3 | 0.003366 | 26.4231 | (0.0733333, 0.1133333, 0.045) | 0 | 8 |
| `template_tapered_layer` (cork core 40 % / alloy skin, L0.40 W0.25 h 0.02→0.05) | 12 | 12 | 0.0035 | 13.146 | (0.2285714, 0.125, 0.0255253) | 2 | 20 |

Both wedges are right triangular prisms with unequal legs (asymmetric),
different sizes, different materials, and different mass distributions; their
geometry signatures differ. All compile `complete=True`,
`ownership_complete=True`, one connected component, positive volumes.

## Independent references (fixed tolerances, never widened)

- **Wedges, closed form** (rel 1e-12 mass/volume, abs 1e-12 COM):
  m = ρLWH/2, COM = (L/3, W/3, H/2); inertia about COM
  m·[[W²/18+H²/12, LW/36, 0],[LW/36, L²/18+H²/12, 0],[0,0,(L²+W²)/18]]
  matched to rel 1e-9 of the tensor scale, including the positive off-diagonal
  −∫(x−x̄)(y−ȳ)dm = +mLW/36 sign convention. Tensor asserted symmetric and
  positive-definite.
- **Tapered layer, closed form** (rel 1e-12): total volume/mass/COM and both
  region subtotals, using the trapezoid centroid x̄ = L(h0+2h1)/(3(h0+h1)),
  z̄ = (h0²+h0h1+h1²)/(3(h0+h1)), core COM z̄_core = α·z̄, skin
  z̄_skin = (1+α)·z̄, mass-weighted composite.
- **Tapered inertia, seeded Monte-Carlo** (seed 20261012, N = 10⁶, independent
  of the compiler's exact tetrahedral integration): every component within
  2 % (diagonal) / 3 % (off-diagonal) of the tensor scale — the MC noise floor,
  since I_xy and I_yz are exactly zero (uniform extrusion along y) and are
  separately asserted < 1e-12 on the compiler output.
- **Additivity** (rel 1e-9): core + skin inertia shifted to the common origin
  equals the total inertia — catches double-counted or dropped cells.
- **No overlapping ownership**: every cell exactly one region and one mass
  owner, all cells `resolved`; region subtotals sum to total mass (abs 1e-12)
  and total volume (abs 1e-15); cell counts sum to the cell count.
- **Interface orientation**: exactly 2 interface faces on the tapered layer;
  each `normal_a_to_b` unit-length (1e-12) and pointing from region_a's
  centroid toward region_b's (dot > 0); summed interface area equals the
  analytic parallelogram W·√(L²+(α(h1−h0))²) to rel 1e-12.
- **Stable IDs**: double compile gives identical `geometry_signature`,
  identical sorted boundary `face_key`s and interface `face_key`s, and
  identical `to_dict()` for all three templates.

## Geometry refusals (observed compiler reasons)

| control | observed reason |
|---|---|
| open-surface flat sheet (4 coplanar nodes) | `degenerate_tetrahedron` |
| document with `mass_source_kind='thin_sheet'` over solid cells | `mixed_mass_representations` |
| inverted cell (vertex order not repaired) | `inverted_tetrahedron` |
| strictly-interior overlapping cell | `overlapping_tetrahedra` |
| two regions, one `mass_owner_id` | `duplicate_mass_owner_id` |
| unknown region in proposals | `unknown_region` |
| one cell proposed to two regions | accepted with cell status `conflict`, `conflicting_cell_ids=(0,)`, excluded from every subtotal — explicit conflict, never a silent merge |

**Open-surface finding (parity theorem).** The compiler's dedicated
`OPEN_BOUNDARY` refusal (`_check_closed_boundary`, the `len(directions) < 2`
branch) is unreachable for conforming tetrahedral input: the mod-2 boundary of
any union of tetrahedra is an edge cycle, so every exterior edge sees an even
number of boundary faces. Open-surface *documents* are therefore refused
upstream instead — a flat sheet dies as `degenerate_tetrahedron` at the cell
check, and a thin-sheet mass claim over solid cells dies as
`mixed_mass_representations` at the catalogue check. Both honest controls are
in the battery; the argument is recorded in `packet.py`'s
`refusal_open_surface_sheet` docstring.

## Document contract

`wedge_document()` round-trips through `compile_document()` with an identical
geometry signature; an unknown extra field and a missing required field are
both refused with `bad_schema`.

## Runs

- `python tools/construction_packet/test_construction_packet.py` → **23/23 OK**
  (0.5 s).
- `python tools/assembly_handoff/run_fixtures.py` → all fixtures and controls
  passed (the existing consumer of the same compiler; original checks reused,
  compiler file unmodified).
- `python tools/material_volume_checks.py` → **17/17 OK** — the original
  compiler check suite (byte-identical to the frozen reference family,
  restored into `tools/` alongside the byte-identical compiler; its contract
  doc restored at `Chimera/docs/matter/material_volume_compiler.md`, the path
  the compiler docstring points at).
- `python tools/construction_packet/packet.py` →
  `B1_resource_inventory.json` (this directory): per-template vertex/cell
  counts, signatures, materials/regions/mass owners, region subtotals,
  interfaces, boundary face keys, and the refusal-reason map above.

## Resource inventory

`B1_resource_inventory.json` is the machine-readable inventory the gate asks
for: every material ID, region ID, mass-owner ID, geometry signature, and
boundary face key the packet produces, plus the refusal-control map.

## Commit scope (§15)

Explicit paths only, on `WK-ENGINE-PATHS-20260929-PR`, trailer `Agent: TIEL`:
`tools/material_volume.py` (the reused compiler, previously untracked,
byte-identical to the frozen reference), `tools/material_volume_checks.py` +
`tools/material_volume_example.json` (the original checks + example, restored
from the same frozen family so the gate evidence is reproducible),
`Chimera/docs/matter/material_volume_compiler.md` (the contract doc the
compiler docstring points at, restored), `tools/construction_packet/` (packet
+ battery), `docs/evidence/construction_packet_20261012/` (this report +
inventory JSON). No force-push, reset, stash, or rebase of the shared checkout.
