# F03 Preregistration — frozen BEFORE implementation

Recorded 2026-09-24, before the recipe, declaration, loader, or tests were written.
Companion discovery note: `discovery_note.md` (same dir). Item F03, verbatim: "Trunk
geometry, surface IDs, material provenance and collision representation are explicit.
Deformable branches and bark damage deferred." Calculation contract C15.

## Statement (someone could disagree with it)

One rigid climbable trunk can be authored as pure data — one deterministic recipe
compiling to one byte-identical declaration — that qualifies the F01-pinned site with
an exact analytic collision solid (vertical circular cylinder + caps, closed-form
contact normals), a render mesh whose discretization error against that analytic
surface is MEASURED and provably inside a tolerance derived from the walker's contact
machinery, explicit surface IDs each resolving to one material record, and a friction
provenance that honestly names itself UNEVIDENCED-PLACEHOLDER (acquisition = G04
prerequisite) — with no deformable or damage representation anywhere in the record.

## Prediction (not yet measured)

Compiling the frozen recipe twice (in-process and in a fresh subprocess) yields
byte-identical canonical JSON and identical sha256; the validator re-derives every
claim from stored numbers alone (footprint inside F01's 0.5 m bound, site equal to the
live F01 declaration's `trunk_sites[0]`, height equal to the stored pinned-number
sum 0.901 + 0.257, radius equal to 0.074/2, every declared mesh vertex exactly on the
analytic cylinder, the measured mid-facet discretization error equal to the sagitta
formula R(1-cos(pi/N)) and <= the frozen 2e-4 m tolerance, every surface ID unique and
resolvable to the material record); and every corrupted variant tested (larger radius,
moved site, wrong height, fewer ring segments, widened tolerance, renamed material
ref, deleted surface, added damage/deformable field) is refused with a named code.

## Frozen values (no tuning after this point)

- **Schema**: `chimera.trunk_asset.v1` (house convention, discovery note §1).
- **Determinism rule**: same as F01 — canonical bytes, self-pinned `declaration_sha256`
  over the body without the pin, every derived float rounded onto the 1e-6 grid. The
  geometry is pure arithmetic (NO PRNG): the cylinder mesh is fully determined by
  R, H, N — no seed is consumed, so there is nothing to re-roll.
- **Site (consumed from F01, not re-derived)**: base centre
  (11.976783, 0.0, 2.471766) m, axis (0,1,0), id `trunk_01`, terrain height 0.0 m and
  slope 0.0 at the site. The validator loads the LIVE F01 declaration, validates it
  with F01's own validator, and requires equality with `trunk_sites[0]`.
- **Geometry profile**: a RIGHT CIRCULAR CYLINDER, radius constant over its height:
  `r(y) = R` for `0 <= y - y0 <= H` about the axis through the base centre. The
  analytic solid (collision representation) is: lateral surface + base cap (y=y0) +
  top cap (y=y0+H). No buttress, taper, bark relief, branches or damage: rigid only
  (map: deformable branches and bark damage deferred — they are NOT modeled, and the
  validator enforces a closed key vocabulary so they cannot silently appear).
- **Trunk height** `H = 1.158 m`, derived entirely from P02P03-pinned walker numbers
  (discovery note §4): `H = (leg_len_hip_to_MP + HAT_length) + (upperarm + forearm)
  = (0.419 + 0.482) + (0.125 + 0.132) = 0.901 + 0.257`. Basis: the trunk top must
  exceed the animal's maximum ground-static reach (its own vertical extent, 0.901 m)
  by exactly one forelimb chain (0.257 m), so a hold at the top is a genuine climb —
  both feet clear of the ground by construction — and the ascent carries
  `m*g*L_fore = 98.439*0.257 ≈ 25.30 J` above the reach line (full ascent
  `m*g*H ≈ 114.0 J`), same order as the W03 walk ledger (30.970714 J). No multiplier
  is tuned; every input is a pinned number with a citation.
- **Trunk radius** `R = 0.037 m = 0.074/2` (half the pinned Oku Table 1 foot segment
  length). Basis: an opposed grip must span the trunk diameter with one appendage; the
  pinned foot is the assembly's only measured appendage length (map A05: hand digits
  not yet assembled). Contact nondegeneracy holds: `R / r_sole = 0.037 / 0.004 = 9.25`
  (contact spheres are small against trunk curvature). If A05's eventual hand is
  smaller, G01 consumes this radius and reports infeasibility — the radius is data.
- **Footprint bound**: max radial extent `R = 0.037 m <= 0.5 m` (F01's bound; the
  spawn-clearance derivation depends on it). Falsifier (a).
- **Render mesh**: right prism tessellation of the cylinder, `N = 32` ring segments,
  two rings (base, top) + 2 cap centres; vertices 9 floats pos+normal+color (house
  layout, `graph_earth.hpp:26-30`), lateral normals exactly radial, cap normals
  (0,-1,0)/(0,+1,0), single declared colour RGB (0.36, 0.25, 0.16). Vertex components
  rounded to the 1e-6 grid. N is derived, not chosen: the discretization (sagitta)
  error of an N-gon inscribed in a circle is `delta(N) = R*(1 - cos(pi/N))`; the
  frozen tolerance (below) requires `delta <= 2e-4`, i.e. `N >= 30.24 -> N_min = 31`;
  N = 32 is the smallest power of two >= N_min (power of two keeps the vertex table
  exact in binary floats and indexable by shift). N = 24 would measure
  `3.17e-4 > 2e-4` — a test asserts the compile refuses it.
- **Representation error (frozen tolerance)**: `TOL = 2e-4 m = 0.05 * r_sole`
  (5% of the walker's 0.004 m contact-sphere radius — the finest contact feature the
  creature machinery uses; the render surface must not lie to the contact law by more
  than that). The declared `representation_error.max_measured_m` must equal the
  sagitta `R*(1-cos(pi/32)) = 1.7817e-4 m` (computed at compile, asserted by test to
  match both the formula and an independent sampled measurement within 2e-6 m) and
  `TOL` must be stored in the declaration; the validator refuses any widening.
  Falsifier (b).
- **Surface IDs** (explicit, unique, each with exact analytic definition + normal law +
  material ref): `trunk_01.lateral` (grip/climb surface, normal = radial outward,
  climbable true), `trunk_01.base_cap` (ground joint, normal (0,-1,0), climbable
  false), `trunk_01.top_cap` (top, normal (0,+1,0), climbable false). Falsifier (c).
- **Material provenance**: ONE record, id `mat.bark.trunk_01`:
  - `friction.coefficient_placeholder = 0.6`, `friction.provenance =
    "UNEVIDENCED-PLACEHOLDER"` — the value is inherited from the walking lane's own
    uncited design constant (`admit_gait_walker_20260919.py:60 CONTACT_FRICTION=0.6`,
    carried in `creature_graph.json` `model.dynamics.gait_walker`) and is presented as
    a seed ONLY, never as evidence; `friction.acquisition_prerequisite = "G04"`;
    `friction.evidence_search` records where the lineage was searched (discovery
    note §3). Taxonomy relation stated per `Chimera/docs/matter/matter_library.json`
    (classes seed/code/researched/provisional/trained/design): this record is below
    `provisional` on that ladder — an unevidenced placeholder debt.
  - `colour_rgb = [0.36, 0.25, 0.16]`, `colour_provenance_class = "design"` (a chosen
    game value with no real-world referent, named as such).
  - `rigid = true`, `deformable = false`, `damage_model = "none"`,
    `branches = "deferred"` — the deferral is RECORDED (the map's own wording), and
    the validator's closed key vocabulary refuses any damage/deformability field
    beyond these exact four names and values. Falsifier (d).
- **Contact normal laws (explicit, closed-form)**: lateral —
  `n = (x-cx, 0, z-cz)/|(x-cx, 0, z-cz)|` on `dist_to_axis = R`, `y0 <= y <= y0+H`;
  base cap — `(0,-1,0)` on `y = y0`, `dist_to_axis <= R`; top cap — `(0,+1,0)` on
  `y = y0+H`, `dist_to_axis <= R`. Consumed by F04 (contact verification) and G01
  (grip wrench geometry).
- **Reachable approach checks (C15)**: from the LIVE F01 declaration —
  `distance(spawn, trunk axis) - R >= R_clear` (re-proven with MY radius, stronger
  than F01's bound-form check), terrain height at the site 0.0 m (recomputed via F01's
  `height_at`), and the whole solid inside the extent square (trunk at
  (11.98, ., 2.47), inset 3 m — trivially satisfied, still checked).
- **Consumable output for F02/F04**: the declaration carries the render mesh in the
  house 9-float layout so it can be uploaded via `engine.load_mesh` unchanged, next to
  the analytic solid that any collision consumer must reproduce. Exercising the engine
  HTTP contract is NOT done here (CPU-only, frozen C++; F02 owns the terrain-side
  exercise; F04 owns contact verification).

## Falsifiers (frozen before the run; a hit refutes the design)

- **(a) Geometry exceeds the 0.5 m footprint**: any stored radius, cap extent, or
  vertex radial distance from the axis > 0.5 m — or the solid outside the extent
  square. Refusal codes `f03_footprint_bound` / `f03_extent_bounds`.
- **(b) Collision representation diverges from render beyond the frozen tolerance**:
  any declared vertex off the analytic surface by > 1e-6 m; measured mid-facet error
  differing from the sagitta formula by > 2e-6 m; measured error > 2e-4 m; declared
  tolerance widened; N shrunk below the derivation (compile refuses N=24 with
  `f03_segments_below_tolerance`).
- **(c) Missing/implicit surface or material identity**: any surface ID absent,
  duplicated, or not resolving to `mat.bark.trunk_01`; missing analytic definition or
  normal law; missing friction placeholder/provenance/acquisition fields; a material
  number presented WITH evidence wording while its provenance is placeholder (the
  record's only coefficient field is literally named `coefficient_placeholder`).
  Refusal codes `f03_surface_*`, `f03_material_*`.
- **(d) Any deformable/damage claim**: the closed key vocabulary refuses any
  geometry/material key beyond the frozen allowlist, and the four rigid flags must be
  present with their exact frozen values (`rigid: true`, `deformable: false`,
  `damage_model: "none"`, `branches: "deferred"`). Injecting
  `"damage_model": "bark_crack"` or `"plasticity"` of any form is refused with
  `f03_rigid_vocabulary`.

## Stop rule

Determinism tests + footprint + representation-error + identity + rigid-only verdicts
green with receipts, and `git status` shows changes only in `agents/F03_trunk/` plus
the two declared data paths (`data/monkey_trunk/trunk_recipe.py`,
`data/monkey_trunk/trunk_declaration.json`). CPU-only; no GPU; no engine C++ edits; no
launched servers. Exercising the engine HTTP contract and measured friction acquisition
remain named follow-ups (F04/G04), per brief.
