# F03 Handoffs — what F04 and G01 consume from the trunk asset

Author: M-F03. Date: 2026-09-24. The one file to load:
`tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json`
(schema `chimera.trunk_asset.v1`, self-pinned `declaration_sha256 =
b7089e7826a221a570b261b8c69666a4017a6ab62d20a2223d061654d0f63fe3`, 16,634 canonical
bytes). Loader/validator:
`tools/monkey_campaign/data/monkey_trunk/trunk_recipe.py`
(`load_declaration`, `validate_declaration`, plus the analytic predicates
`dist_to_axis`, `on_lateral`, `sagitta`). Import from the repo root or load by path;
stdlib-only. Receipts: `agents/F03_trunk/receipts/`.

## The frozen trunk, in one block

| Quantity | Value | Field |
|---|---|---|
| Site (F01's, consumed) | (11.976783, 0.0, 2.471766) m, axis +Y, terrain 0.0 m / slope 0.0 | `site.base_centre_m` |
| Collision representation | EXACT analytic cylinder solid, radius 0.037 m, height 1.158 m | `collision_representation.solid` |
| Contact normals | lateral = radial outward; base cap (0,-1,0); top cap (0,+1,0) | `collision_representation.contact_normals` |
| Render mesh | 130 vertices (9-float pos+normal+colour), 384 uint32 indices, 32 ring segments, outward winding | `render_mesh` |
| Measured representation error | 1.78307e-4 m vs sagitta formula 1.78165e-4 m, tolerance 2e-4 m | `representation_error` |
| Surface IDs | `trunk_01.lateral` (climbable), `trunk_01.base_cap`, `trunk_01.top_cap` | `surface_ids` |
| Material | `mat.bark.trunk_01`; friction 0.6 = UNEVIDENCED-PLACEHOLDER (G04 acquires) | `material` |
| Rigid law | rigid true / deformable false / damage none / branches deferred (closed vocabulary) | `collision_representation` |
| Derivation basis | H = (0.419+0.482)+(0.125+0.132) = 1.158 m; R = 0.074/2 = 0.037 m — all Oku-2021 pinned numbers, cited in-declaration | `geometry.derivation` |

## To F04 (contact verification; contracts C08, C14, C15)

1. **The analytic solid is the collision contract.** The frozen engine has NO
   mesh-collision route (route survey: `agents/F03_trunk/discovery_note.md` §2 — every
   engine contact is analytic and plane-only). Verify contacts against the analytic
   cylinder: containment = `dist_to_axis <= R and y0 <= y <= y0+H`; lateral normal =
   `(x-cx, 0, z-cz)/d`; caps at `y = y0` / `y0+H`. If you drive the real engine,
   upload `render_mesh` via `load_mesh` (9-float layout, `graph_earth.hpp:26-30`) and
   treat any engine-side trunk contact capability you find as a separately-gated
   finding — none exists in the frozen HTTP contract, and no C++ was touched here.
2. **Render-vs-collision check (C14/C15 pattern)**: the render surface is INSCRIBED —
   it lies inside the analytic cylinder by up to the measured 1.78307e-4 m
   (`representation_error.max_measured_m`, recomputable from the stored vertex table;
   `trunk_recipe.measure_representation_error`). Frozen tolerance 2e-4 m. A contact
   query may therefore report a gap up to that amount where the render shows contact;
   that is the DECLARED representation error, not a defect — anything LARGER than
   2e-4 m is your red.
3. **Ground-trunk joint**: base cap at y = 0.0 on F01 terrain (height 0.0, slope 0.0
   at the site — re-derivable via `clearing_recipe.height_at`). Verify no
   interpenetration below y = 0 and no ghost gap at the base cap under a downward
   load case.
4. **Tunnelling cases**: contact spheres are the walker's 0.004 m soles
   (`gait_scene.py SOLE_RADIUS`); the lateral surface is convex and exactly
   cylindrical, so approach-speed cases should use the walker lane's own contact
   velocity gate scale (`gait_controller.hpp:1727`). The trunk has no thin features —
   minimum curvature radius 0.037 m — so pure-geometry tunnelling is bounded by your
   timestep budget, not by asset thinness.
5. **Refusal reuse**: `trunk_recipe.validate_declaration` re-proves every number from
   stored data (digest, site vs F01's live file, mesh on the analytic surface,
   winding outward, error identities). Run it on whatever file you actually received;
   any `f03_*` refusal means the artifact drifted — do not patch the JSON by hand,
   recompile via `python tools/monkey_campaign/data/monkey_trunk/trunk_recipe.py
   compile`.

## To G01 (support and grip feasibility; contracts C19, C20)

1. **Consume the radius as data**: `geometry.radius_m = 0.037 m` — derived as half
   the pinned Oku foot length (opposed-grip span rule; hand digits not yet assembled,
   map A05). If your reach/wrench math needs a different span, that is a PREREG
   AMENDMENT to F03 (the spawn-clearance chain and the grip rule both move), not a
   free parameter — record it and route it back.
2. **Friction is a PLACEHOLDER, not evidence**: `material.friction
   .coefficient_placeholder = 0.6`, provenance `UNEVIDENCED-PLACEHOLDER` — the walking
   lane's own uncited design constant, carried transparently. Your static support
   envelope (`sum f + mg = 0`, tangential bound `|ft| <= mu*fn`, C19) may be computed
   from it but MUST be labelled provisional; no grip verdict is final until G04
   acquires a measured bark-on-appendage coefficient (`acquisition_prerequisite:
   "G04"` — that acquisition debt is recorded in the declaration itself).
3. **Contact geometry for the wrench**: grasp points on `trunk_01.lateral` have exact
   outward normals (radial) and exact height bounds `0 <= y <= 1.158 m`. The declared
   meaning of the height: the top exceeds the walker's max ground-static reach
   (0.901 m) by one forelimb chain (0.257 m), so a hold near the top is a genuine
   climb — the vertical transfer envelope (C20) starts where the feet leave the
   ground, and the full-ascent potential scale is m·g·H = 113.992539 J (walker
   10.038 kg, g 9.80665), with 25.298862 J above the reach line.
4. **Surfaces you may use**: `trunk_01.lateral` is the only climbable surface
   (`climbable: true`); the caps are boundaries, not grip surfaces. Do not infer grip
   on the top cap.
5. **Rigid-only**: the trunk will not deflect, damp, or deform — no compliance exists
   in the record and the closed vocabulary refuses to let any appear. Compliance
   belongs to the attachment model (C17/G02), not to this asset.

## Open debts recorded (not silently dropped)

- Measured bark-on-appendage friction coefficient — G04 prerequisite (declared in the
  artifact).
- Engine-side trunk collision — none exists in the frozen C++; any addition is a
  separately gated engine change that must implement the declared analytic contract.
- Hand/digit segments (map A05) — the radius derivation names the Oku foot as the
  span proxy until A05 lands; G01 consumes the consequence.
