# F07 Handoffs — what F08, W10 and F05 consume from the route/blocking layer

Author: M-F07. Date: 2026-09-24. The two files to load:

- `tools/monkey_campaign/data/monkey_routes/route_declaration.json` (schema
  `chimera.monkey_routes.v1`, self-pinned `route_declaration_sha256 =
  7c3ad6e86039b63324e4695abe5e5525e2693a98f9a0ef91355b804da8b8e211`, 8,495
  canonical bytes; committed-file sha256
  `28dff2b33e74fcc4103ac3699899b0937f6975323758d1fa142092704bf4496c`).
- Loader/validator:
  `tools/monkey_campaign/data/monkey_routes/route_recipe.py`
  (`load_live_inputs`, `compile_declaration`, `validate_declaration`,
  `tangent_route`, `straight_route`). Import from the repo root; stdlib-only.
  It refuses (`f07_input_drift`) if ANY of the three upstream artifacts
  (F01 declaration / F02 bundle / F03 trunk) has a drifted byte — re-compile
  via `python tools/monkey_campaign/data/monkey_routes/route_recipe.py
  compile`, never hand-edit.
- The suite that proved all of this:
  `tools/monkey_campaign/agents/F07_obstacles/verify_routes.py`
  (stdlib + matplotlib-Agg; CPU; headless; receipts in
  `agents/F07_obstacles/receipts/`; deterministic — two fresh runs produce
  byte-identical `run.json`, sha256
  `7baaf0184e75b92ba28b9cb8cd20be4f357e5b1c26f52d2eca081c8f7f148832`).

## The verified route/blocking layer, in one block

| Quantity | Value | Source |
|---|---|---|
| Blockers (the ONLY two) | B1 extent rule \|x\|>20 or \|z\|>20 (strict >); B2 trunk routing disk r = 0.287 m = 0.037 + 0.25 at (11.976783, 2.471766) | route_declaration.blocking_causes (F01/F03 consumed) |
| Non-blockers | N1 mound slopes (walk law 0.05 — never fires: worst 0.042522); N2 posts (render-only, F04 VIS-03 NO-CLAIM) | same |
| Reachability | 641,494/641,494 free grid cells reachable from spawn (0.05 m grid, 8-conn); 0 unreachable; blocked cells 107, all B2 | verify_routes V3 |
| Spawn→trunk corridor | BFS width 1.076 m (min clearance 0.538 m ≥ 0.5); straight R0 heading min clearance 0.502 m outside the approach zone; envelope W_env = 1.0 m = F01's 4·r_body | V4 |
| Corridor envelope derivation | W_env = 4·r_body = 1.0 m — F01's own passing-room quantum (R_clear = r_trunk_bound + 4·r_body); stance floor 2·r_body = 0.5 m; grid Δ = r_body/5 = 0.05 m; s_tick 3.3667e-3 m ≪ Δ | route_declaration.walker_envelope |
| Tangent routes around mounds | 10/10 construct; 6 PASS outright + 4 PASS-AS-DECLARED (B1-terminated on the visible edge); every mound has an outright PASS side | V5 |
| Edge rays | All 4 rays walk to the post line (stop-short ≤ one grid step), nearest post ≤ 1.0 m, first refusal beyond is `f02_outside_extent` | V6 |

## To F08 (repeatable forest loading; consumes the same declarations)

1. **Re-compile, never copy:** the route layer is DERIVED from the three live
   artifacts. Your repeatability check is:
   `route_recipe.compile_declaration()` twice (in-process + fresh subprocess)
   → byte-identical, then `validate_declaration` on the committed file (it
   re-derives every route, bound and blocker from stored numbers; any
   `f07_*` refusal means drift — recompile, don't patch). The same holds
   upstream: `load_live_inputs` refuses on any F01/F02/F03 byte drift, so
   loading the route declaration transitively re-proves the whole scene
   chain (clearing → terrain → trunk → routes).
2. **Initial state = the four declarations.** A repeatable scene load is:
   F01 clearing + F02 terrain bundle + F03 trunk + F07 routes, each passing
   its own validator, with the pinned digests
   (`aa2607df…` / `8c7d60c8…` / `b7089e78…` / `7c3ad6e8…` body pins — the
   route declaration's `inputs` block carries all three upstream pins, so
   ONE file gives you the chain to check).
3. **Clear failure for missing assets** already exists in the pattern: every
   loader raises a named `Refusal` (`f01_*`, `f02_*`, `f03_*`, `f07_*`).
   F08's missing-asset cases should assert THOSE codes, not generic
   exceptions. A missing terrain bundle must fail `f07_input_drift` (file
   sha) at route-declaration compile, and `f02_*` at terrain_query load.
4. **Determinism receipts to compare against:** route declaration 8,495
   bytes, byte-identical across in-process + subprocess compiles;
   `receipts/determinism.txt` records the identity. If a re-compile on your
   machine differs by even one byte, that is a finding (the float pipeline is
   grid-snapped to 1e-6 precisely so it cannot).

## To W10 (walking acceptance in this scene; C14/C23 in-vivo)

1. **The scene for the walking demo is now fully declared:** spawn (0, 0, 0)
   → trunk approach at (11.976783, 2.471766), corridor ≥ 1.0 m wide the
   whole way, mounds walkable (slope ≤ 0.05 everywhere — the walker may cross
   or round them; both are legal routes), boundary at the visible post ring.
   A walking acceptance run that stays inside these declarations needs NO
   pathfinding: R0 (one heading) is a proven route.
2. **Stop semantics at the boundary:** the walker's stop is the extent rule
   (`out_of_patch` strict `>`), which coincides with the visible post line
   (edge rays: stop-short ≤ 0.05 m, nearest post ≤ 1.0 m). In-vivo, phase
   `out_of_patch` should first occur when the body crosses |x| or |z| = 20 —
   exactly where the ochre posts stand. A stop EARLIER than the post line in
   the live engine is an invisible wall and must be reported as a defect
   (that is falsifier (a) made physical).
3. **The trunk approach zone:** within 0.787 m of the trunk axis the corridor
   narrows BY DESIGN (the walker is reaching its climb target). W10's pass
   criteria should treat contact at r_block = 0.287 m as goal contact, not
   as a collision failure.
4. **Slope reading:** use F02's `terrain_query.TerrainSurface.gradient_at`
   (ONE implementation law). Worst measured slope on the 0.05 m route grid is
   0.042522 at (17.0, 7.0) — mound 2's east flank; a live tilt there must
   read ≤ 0.05 or the contact model diverges from the declared surface
   (F04's L2 gap applies: the native walker plane is ONE height; until the
   preregistered engine task lands, terrain-aware walking lives in the Python
   binding lane).
5. **Camera note (C23):** the occlusion-relevant blocker set for camera cases
   is exactly B1 (post ring) + B2 (trunk cylinder h = 1.158 m, r = 0.037 m,
   rendered mesh inscribed ≤ 1.783e-4 m). There is no third occluder; mounds
   are ≤ 0.11 m tall. A camera-collision case that reports a third blocker is
   an engine-side defect, not scene data.

## To F05 (terrain envelope spec; same slope data)

1. **The slope data you asked for is measured and frozen:** worst slope by
   four independent measures, all ≤ the 0.05 law — F01 grid central
   differences 0.034606 (== F01's receipt, re-derived from the committed
   declaration), F02 physical `gradient_at` on the 801×801 @ 0.05 m route
   grid 0.042522289 (== F02's worst mesh triangle, at (17.0, 7.0)), analytic
   per-mound max A·π/(2R) 0.037956 (mound 2), mesh triangle worst 0.042522.
   Your walking envelope spec can cite these as the DECLARED gentle-terrain
   band: [0, 0.0426] measured, 0.05 the law.
2. **Traversal law used here (consume or amend explicitly):** traversable :=
   inside extent AND dist-to-trunk ≥ 0.287 AND slope ≤ 0.05. F05's job is to
   replace the 0.05 PLACEHOLDER-law with the evidence-based walking envelope
   (F01's 0.05 is a design bound, not a measured gait limit); when your
   evidence-based envelope lands, the route predicate's N1 row and
   `route_declaration.bounds.max_slope_m_per_m` must be re-frozen to it —
   that is a prereg amendment to THIS artifact, not an edit.
3. **Obstacle size envelope (your C14 row):** the scene's declared obstacle
   inventory is: zero props besides the trunk (r 0.037 m, h 1.158 m) + five
   traversable mounds (R 4.0–6.0 m, A 0.05–0.12 m, disjoint) + the boundary
   ring. There are no other obstacles to envelope against; if F05's evidence
   says the walker cannot climb X, that X must be stated against THIS
   inventory.
4. **Contact allowance reminder (F04's):** vertical-law slope submergence at
   the worst triangle is 3.6114e-6 m ≤ derived 4.9906e-6 — inside your
   static-envelope math on slopes, that is the declared penetration
   allowance.

## Open debts recorded (not silently dropped)

- In-vivo exercise of every verdict here is owed to G04/W10 (F04's L2 gap
  statement applies unchanged: the frozen engine has no heightfield or prop
  contact; this artifact is the DECLARED route/blocking layer).
- The 0.05 slope law and the 4·r_body envelope are design derivations, not
  measured gait limits — F05/G04 own the evidence-based replacements; the
  route declaration will re-freeze to them by amendment.
- Post collision is NOT claimed anywhere (F04 VIS-03 NO-CLAIM stands); if a
  future item wants solid posts, that is a new declared blocker and a new
  falsifier set — the blocking-causes table must grow a row, never a silent
  collider.
