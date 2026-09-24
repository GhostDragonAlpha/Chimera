# F03 Discovery Note — asset, material and collision machinery on the game lineage

Author: M-F03 (rigid climbable trunk). Date: 2026-09-24. Checkout:
`E:/ChimeraWork/monkey-play-20260924`, branch `monkey-play-20260924`, HEAD `1d34b0f5`
(base = game lineage tip `33e7a444`). Read-only discovery; no files modified.
Item F03, verbatim: "Trunk geometry, surface IDs, material provenance and collision
representation are explicit. Deformable branches and bark damage deferred."

## 1. The asset pattern (compiled canonical-JSON bundles) — reused

F01's discovery (`agents/F01_clearing/discovery_note.md` §1) mapped the live pattern and
F01 implemented it: Python compiles a declaration to **canonical JSON bytes**
(`tools/science_funnel/common.py::canonical`, lines 21-23: `sort_keys=True,
ensure_ascii=False, separators=(',',':'), allow_nan=False`), the bundle **pins its own
sha256** (`earth_scene.py:46`), intake is **strict** (`require`/`Refusal`,
duplicate-key and non-finite-number refusal, `common.py:10-56`), schema strings follow
`chimera.<thing>.v<N>` (`chimera.earth_scene.v1`, `chimera.earth_patch.v1`,
`chimera.surface.v1`), lengths are SI metres with `_m` field suffixes
(`tools/science_funnel/units.py`). F01's clearing declaration
(`tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json`,
`chimera.monkey_clearing.v1`) is the direct precedent this task follows. I reuse all of
it, including the self-pinned digest and the strict loader.

## 2. What "a rigid prop" is on this lineage today — nothing; collision is ANALYTIC and PLANE-ONLY

There is **no rigid-prop object class** in the game lineage. Every physics contact the
frozen engine implements is analytic:

| Lane | Collision representation | Friction source | Citations |
|---|---|---|---|
| Gait (the walker) | contact-point **spheres** (r = 0.004 m) vs **ONE ground plane** (`plane_model_y_`); discrete-cone Coulomb solve at each point | `contact_friction` config key, required number in [0,1] | `ChimeraEngine/engine/gait_controller.hpp:94` (plane), `:716` (`friction_solve`), `:1727` (plane engagement gate), `:2005`/`:2259` (mu range check) |
| Earth (single body) | body sphere vs an **inclined plane** `n_{0,1,0}`-frame tangent | `friction` scene-config key | `ChimeraEngine/engine/earth_environment.hpp:51,56,71,102` |
| Render meshes | 9-float vertices pos+normal+color, `uint32` indices, triangle normals `cross(b-a,c-a)` — **render only**; no mesh collision query exists | — | `ChimeraEngine/engine/graph_earth.hpp:26-30,82`; upload via `engine.load_mesh` (`main.cpp:697-705` per F01's note) |

The HTTP route surface (`ChimeraEngine/engine/main.cpp` route chain, lines ~793-2054:
`/earth*`, `/mesh_bin`, `/mesh_import`, `/gait*`, `/tick_*`, `/membrane*`, `/water*`,
`/hinge_bin`, ...) contains **no collision query route at all** — mesh routes feed
render/membrane paths. The engine C++ is FROZEN for this task (no edits allowed).

**Consequence (the design this forces, stated before the prereg):** the trunk's
collision representation must be **an analytic solid with exact contact laws** — an
exact vertical circular cylinder (lateral surface + two caps) whose containment,
signed distance and contact normals are closed-form — because that is the only form
that (i) needs no engine change, (ii) gives F04/G01/G04 exact numbers to verify and
consume, and (iii) makes "representation error" a *measurable* quantity: the render
mesh is the analytic surface's tessellation, and its discretization error is measured,
not assumed. C15's "evaluate explicit rigid geometry and contact normals; quantify
representation error" is satisfied exactly this way. Exercising any future mesh-based
engine collision is a separately gated engine change — out of scope here, named in the
handoffs.

## 3. Material/friction provenance — what the lineage actually has

- **The only friction number on the play lineage** is the walking contract's
  `contact_friction = 0.6`
  (`tools/creature_graph/data/creature_graph.json`, object
  `model.dynamics.gait_walker`, `physical.contract.contact_friction`), authored as the
  bare constant `CONTACT_FRICTION = 0.6` in
  `tools/creature_graph/validation/admit_gait_walker_20260919.py:60`. **No measurement
  or citation backs it**: the derivation doc it points to
  (`docs/research/20260918_gait_controller_derivation.md`) mentions friction only in a
  support-hull context (line 440); no friction measurement is derived anywhere in it.
- **Provenance FORM reference** (other lineage, used for form only, per the brief):
  `Chimera/docs/matter/matter_library.json` — provenance classes
  `seed / code / researched / provisional / trained / design`, rule "EVERY NUMBER
  CARRIES PROVENANCE", interface families so N materials stays O(families^2). The game
  lineage has no equivalent library; this record's taxonomy is the citing convention I
  adopt.
- **Evidenced external data searched on disk** (`tools/science_funnel/data/`):
  `dryad_granatosky/` + `granatosky_gait/` (Wimberly/Slater/Granatosky Dryad
  `10.5061/dryad.z08kprrd5` + tetrapod gait kinematics tables — gait, not surface
  friction), `usgs_splib07_subset/` (USGS spectral library archives, not unpacked into
  any curated bark/wood entry), `oku_bipedal/` + `oku_paper_table/` (segment masses —
  the body, no friction). **No evidenced bark/wood-on-skin friction exists on this
  lineage.**
- **Conclusion (brief-compliant):** the trunk's friction coefficient is declared
  `UNEVIDENCED-PLACEHOLDER`; the placeholder value transparently carries the walking
  contract's 0.6 **as a seed inherited from the walker's own uncited design constant,
  not as evidence**; acquisition of a measured bark-on-appendage friction coefficient
  is named as a **G04 prerequisite**; render colour is declared `design` (a chosen game
  value, named as such). No invented number is presented as evidence.

## 4. Creature scale — the pinned numbers the height/radius derivation uses

All from the P02P03-pinned walker (10.038 kg, Oku 2021 Table 1; verdicts in
`agents/P02P03/report.md` §1, "Training body (physics)" row):

| Quantity | Value | Source (pinned) |
|---|---|---|
| Assembly mass | 10.038 kg | `tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json` `body_model.mass_kg` |
| Weight | 98.439 N (g = 9.80665) | same file `body_model.weight_N`; gravity `gait_scene.py:164` |
| Hip→MP leg length | 0.419 m | same file `body_model.leg_len_hip_to_MP_m` |
| HAT segment length | 0.482 m | same file `segments_Table1.HAT.length_m` |
| Foot segment length | 0.074 m | same file `segments_Table1.foot.length_m` |
| Forelimb strut lengths | 0.125 + 0.132 m | `tools/science_funnel/gait_scene.py` `fore = (("upperarm", 0.2737, 0.125), ("forearm", 0.1323, 0.132))` |
| Sole contact sphere radius | 0.004 m | `gait_scene.py:26` `SOLE_RADIUS=0.004`; contract `contact_points[*].radius_m` |

Derivations from these numbers (stated here, frozen in the prereg):

- **Standing-height bound** `h_body = leg + HAT = 0.419 + 0.482 = 0.901 m` — the
  assembly's vertical extent (MP on the ground, HAT top above the hip); an upper bound
  on any gripper height while the feet remain on the ground.
- **Trunk height** `H = h_body + L_fore = 0.901 + (0.125 + 0.132) = 1.158 m` — the top
  exceeds the animal's max ground-static reach by exactly one pinned forelimb chain,
  so a hold at the top is a genuine climb (both feet clear by construction) and the
  climb delivers a measurable potential-energy scale (`m·g·L_fore ≈ 25.3 J` above the
  reach line; full ascent `m·g·H ≈ 114.0 J`, same order as the W03 walk ledger
  30.970714 J). No free multiplier is introduced.
- **Trunk radius** `R = foot/2 = 0.074/2 = 0.037 m` — an opposed grip must span the
  diameter with one appendage; the pinned Oku foot is the assembly's only measured
  appendage length (hand/digit segments are NOT assembled — map A05 open). If the
  eventual hand is smaller, G01 consumes this radius and reports infeasibility; the
  radius is frozen data, changeable only by prereg amendment.

## 5. The site F01 pinned (consumed, not re-derived)

`trunk_sites[0]` in `tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json`:
id `trunk_01`, site (11.976783, 0.0, 2.471766) m, axis +Y,
`footprint_radius_bound_m = 0.5`, `terrain_slope_at_site_m_per_m = 0.0`, marker
`geometry_qualified_in: "F03"`. My declaration must embed THIS site verbatim and my
validator re-checks it against the live F01 file (loading and validating F01's
declaration with F01's own loader/validator). The spawn-clearance derivation depends
on the 0.5 m bound, so geometry larger than that is a prereg change, not an edit
(F01 report handoff, "To F03").

## 6. Where the new files go (declared before implementation)

Existing data convention `tools/<area>/data/<scene>/` (F01 used
`tools/monkey_campaign/data/monkey_clearing/`). Declared NEW paths, all owned by F03,
disjoint from F02's terrain work and from every existing file:

- `tools/monkey_campaign/data/monkey_trunk/trunk_recipe.py` — stdlib-only deterministic
  recipe + strict loader/validator (importable as
  `tools.monkey_campaign.data.monkey_trunk.trunk_recipe` from the repo root).
- `tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json` — the compiled
  canonical declaration (`chimera.trunk_asset.v1`).
- Agent dir `tools/monkey_campaign/agents/F03_trunk/` — brief, this note, prereg,
  tests, receipts, handoffs, report.

No engine C++ is touched; no GPU; no servers launched; scratch compiles go to gitignored
`.tmp/`.
