# F02 Preregistration — frozen BEFORE implementation

Recorded 2026-09-24, before the terrain bundle, the query binding, or any test was written.
Companion discovery note: `discovery_note.md` (same dir). Item F02, verbatim: "Rendered
ground and physical query surfaces agree within frozen geometric tolerance. Reuse engine
geometry/collision paths." Calculation contract C14: "compute geometry and gradient/normal
consistently with physical collision representation. Render/query agreement and frozen
slope/obstacle cases."

## Statement (someone could disagree with it)

The clearing's rendered ground and its physical query surface can be made THE SAME
geometric object — one triangulation of F01's stored 41×41 grid, compiled once into a
digest-pinned bundle whose render section is verbatim the engine's `load_mesh` arrays and
whose collision section is a Python binding reading those same arrays — so that
render↔query agreement is an identity (zero by construction, tolerance covering only float
reordering), the normals/gradients the query answers are the containing triangle's own
plane values computed with the engine's formula, and the physical boundary is the engine's
strict-`>` extent rule with the rendered posts exactly on that edge.

## Prediction (not yet measured)

1. Compiling the frozen bundle against F01's committed declaration twice (in-process and
   in a fresh subprocess) yields byte-identical canonical JSON — the bundle is RNG-free.
2. Mesh shape: 13,920 vertices and 4,640 triangles (3,200 ground triangles from 40×40
   cells, flat-shaded duplicated → 9,600 ground vertices; 80 hexagonal posts × 18 triangles
   → 1,440 triangles, 4,320 vertices).
3. Render↔query agreement over the frozen sample set (~21,700 points): worst height
   disagreement exactly 0.0, worst normal component disagreement ≤ 1e-12 (predicted 0.0 —
   identical arithmetic), worst gradient-vs-stored-normal disagreement ≤ 1e-9.
4. The engine's normal-hygiene gate (`engine.cpp:1854-1937`) would fire on ZERO vertices:
   every stored ground/post normal is the unit face normal of its own triangle (0 broken,
   0 deviant).
5. Worst triangle-plane slope over all 3,200 ground triangles is ≤ 0.05 (F01's
   `MAX_SLOPE_BOUND`) and lands near F01's central-difference 0.034606 shifted by the
   1 m-cell interpolation scale (predicted band 0.030–0.045).
6. Mesh↔analytic deviation (the surface vs F01's `height_at`): worst ≤ 0.01 m — the
   derived bound is `2·(1/8)·A_max·π²/(2·R_min²)` with A_max 0.12, R_min 4.0, dx=dz=1 →
   0.00925 m; expected worst a few millimetres on the steepest flank (mound 2, east edge).
7. Posts: all 80 bundle post bases EQUAL F01's declaration positions exactly (`==`); every
   post base is a grid node, so the mesh surface height at each post base equals the
   declared base y exactly (0.0 disagreement).
8. Spawn: the query at (0,0) returns height 0.0, gradient (0,0), normal (0,1,0) — the nine
   cells around the origin are pure base plane by F01's construction.

## Headless strategy (frozen)

NO engine process, NO GPU, NO server is launched. Both sides are built as DECLARATIONS:
- **Render-side surface data**: `tools/monkey_campaign/data/monkey_clearing/
  terrain_bundle.json` (schema `chimera.monkey_terrain.v1`), compiled by
  `terrain_bundle.py` — canonical bytes, self-pinned `bundle_sha256` (house pattern,
  `common.py::canonical`, `earth_scene.py:46`), carrying `render.vertices` (9 floats =
  position(3) + normal(3) + color(3)) and `render.indices` (uint32) in the exact
  `engine.load_mesh` layout (`engine.hpp:140`, `main.cpp:764`).
- **Collision-side surface data**: `terrain_query.py` reads THE SAME bundle arrays and
  answers height / gradient / normal / inside-outside from them. Agreement is therefore
  measured declaration-vs-declaration: for every sampled point, the query's plane value
  against the barycentric evaluation of the STORED render vertices, the query's normal
  against the STORED vertex normals, and the query's gradient against the stored normal's
  own direction (n = normalize(−gx, 1, −gz) ⇒ gx = −nx/ny, gz = −nz/ny).
- Live-engine exercise (uploading the bundle via `engine.load_mesh`, capturing a frame,
  and eventually a native heightfield contact mode) is NOT done here; recorded as the
  follow-up (F04/W10 territory) in `report.md`.

## Frozen construction (no tuning after this point)

- **Source**: F01's committed `clearing_declaration.json` ONLY. The bundle records the
  declaration file's sha256 (`18dd2ff6...bfbc1`) and refuses to compile/validate against a
  drifted copy. The grid stored in the bundle must equal the declaration's grid.
- **Diagonal rule**: every cell splits along `(x_i,z_j)–(x_{i+1},z_{j+1})`; triangle A =
  (node00, node01, node11) covers `tz ≥ tx`; triangle B = (node00, node11, node10) covers
  `tz ≤ tx`; winding gives `cross(b−a, c−a)` with +Y dominant (verified per-triangle at
  compile). The diagonal choice itself is agreement-neutral — both splits deviate from the
  grid's bilinear by the identical bound |Δ|/4 — what is NOT free is the render projection
  and the query projection using DIFFERENT diagonals; that drift is falsifier (a)'s content.
- **Shading**: fully duplicated per-triangle vertices with face normals (the engine's
  authored-ground style, `graph_earth.hpp:100`), degenerate refusal at `|cross| ≤ 1e-16`.
  Ground colours: the engine's two-tone checker (0.16,0.22,0.17)/(0.18,0.24,0.19) on
  `(i+j)%2` (`graph_earth.hpp:105`). No smooth/shared normals anywhere.
- **Posts**: 80 hexagonal prisms (render row: 6 sides, circumscribed radius 0.05 m — a
  render-legibility constant with no upstream derivation, THE HUMAN's to move, same status
  as `walker.py`'s `_STEP0`), sides + top cap, open bottom (occluded by ground contact,
  declared), colour F01's ochre (0.72, 0.55, 0.20) from the declaration, base y = the
  declaration's post base, top = base + 0.9. Post positions are COPIED from the
  declaration at compile — never re-derived.
- **Boundary**: `physical = {kind: extent_rule, half_width_m: 20.0}` copied from F01;
  `classify` implements exactly `outside = |x| > 20.0 or |z| > 20.0` (strict `>`,
  `earth_environment.hpp:118`). Height/gradient/normal queries REFUSE outside the closed
  extent (`f02_outside_extent`) — the engine stops at the patch edge; no surface is
  served past it, and no mesh vertex may lie outside the closed extent (renderable ground
  beyond the blocking edge would be fake ground — the invisible-wall law's other face).
- **Frozen tolerances** (identity + float-reordering scale, not perceptual slack):
  - height render↔query: ≤ **1e-9 m** (F01's own grid≡function scale);
  - normal components render↔query: ≤ **1e-12**;
  - gradient vs stored-normal direction: ≤ **1e-9 m/m** (one extra digit for the division);
  - post positions: EXACT (`==`) — copied bytes, not computed numbers;
  - mesh↔analytic (`height_at`) deviation: ≤ **0.01 m**, derived bound 0.00925 m — this is
    the inherited 1 m-grid discretization, carried IDENTICALLY by both projections; it is
    measured and reported, and it is NOT a render/query disagreement. It bounds what F05
    must know about the envelope between grid nodes.
- **Frozen sample set** (the agreement measurement's domain): all 1,681 grid nodes + all
  1,600 cell centres + all 3,200 triangle centroids + 3×3,200 triangle edge midpoints +
  4,096 pseudo-random points on [−20,20]² from the F01-style splitmix64 seeded 4598322
  (ASCII "F02") — ~21,700 points, edges and mound flanks included (the lineage's own law:
  edge faults are invisible at the spawn, `terrain_witness.py:53-68`).
- **Frozen slope/obstacle cases** (each must satisfy F01's law ≤ 0.05 and the agreement
  tolerances): (i) the worst-slope point (x=17, z=6, on mound 2's west flank); (ii) the
  five mound crests — mesh height == declaration-derivable crest height A (1e-6 grid) at
  the crest sample, crest-cell plane slope ≤ 0.05 and normal_y ≥ 0.99; (iii) the boundary
  edge — heights and normals on the four edges (incl. edge midpoints and corners, and the
  mound-2 crossing near (20, 6)); (iv) the spawn cell (0,0): height 0.0, gradient (0,0),
  normal (0,1,0); (v) posts standing on the boundary, incl. the corner posts.

## Falsifiers (frozen before the run; a hit refutes the design)

- **(a) render↔query disagreement beyond frozen tolerance**: ANY sampled point where the
  query surface and the stored render surface disagree by more than 1e-9 m (height),
  1e-12 (normal component), or 1e-9 m/m (gradient/normal consistency) — including any
  diagonal drift between the two projections.
- **(b) boundary post position mismatch**: ANY of the 80 bundle post bases differing from
  F01's declaration (exact equality), or wrong count/colour/height, or a post base off the
  physical edge, or a post base not exactly on the mesh surface height.
- **(c) physical bound not matching |x|>20/|z|>20 semantics**: `classify` calling any point
  with |x| = 20.0 "outside" (the rule is strict), or any point with |x| = 20+ε (ε = 1e-9,
  1e-6) "inside"; a height/gradient/normal query SERVED outside the closed extent; any
  GROUND-mesh vertex outside the closed extent; or the bundle's physical half-width
  differing from the rendered ring's max extent (invisible-wall guard, F01's
  `f01_invisible_wall`).

## Amendment 1 (2026-09-24, during implementation, BEFORE any run — derivation caught a contradiction)

The falsifier (c) clause as first written said "any mesh vertex outside the closed
extent". That contradicts this same prereg's own post design: a hexagonal prism of
circumscribed radius 0.05 m whose axis stands ON the edge (F01's law: post bases on the
perimeter lines) necessarily has vertices 0.05 m beyond |x| = 20 — no orientation avoids
it, and moving the axes inward would violate falsifier (b) (positions must equal F01's
declaration). Corrected by derivation, not tuning: the anti-fake-ground law binds the
WALKABLE SURFACE, so the closed-extent check applies to the GROUND section's vertices;
the post MARKER girth is checked against its own declared bound (half_width + post
radius). The physical semantics are untouched — `out_of_patch` stops motion at the edge
regardless of marker geometry, and the posts are not queryable surface. Falsifiers (a),
(b), (d) and all tolerances are unchanged.
- **(d) frozen slope/obstacle cases failing F01's law**: worst triangle-plane slope > 0.05;
  any frozen case height/normal disagreeing with the declaration-derived value beyond the
  frozen tolerances; mesh↔analytic worst deviation > 0.01 m (the derived bound would be
  wrong); any refusal from the engine-mirror checks (degenerate triangle, non-unit stored
  normal, hygiene-gate would fire).

## Stop rule

All falsifier tests green with receipts under `agents/F02_terrain/receipts/`, byte-identical
determinism receipt, and `git status` showing changes ONLY in `agents/F02_terrain/` plus the
three declared data paths (`terrain_bundle.py`, `terrain_bundle.json`, `terrain_query.py`
under `tools/monkey_campaign/data/monkey_clearing/`). CPU-only; no GPU; no servers; no
engine C++ edits. Live-engine verification recorded as follow-up, per brief.

## Scope boundary

F02 renders terrain/posts and declares the collision/query surface + boundary binding.
Trunk geometry, surface IDs and material provenance are F03's (F01's site is data;
`footprint_radius_bound_m` 0.5 m untouched). Obstacle colliders are F07's. Walking on the
surface (slope/friction envelope, terrain-aware gait) is F05/F06's. The native engine's
contact mode remains the plane (`earth_environment.hpp`); binding the clearing to it live
is F04/W10's exercise, recorded as follow-up.
