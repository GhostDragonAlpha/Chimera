# F04 Preregistration — frozen case matrix, BEFORE suite implementation

Recorded 2026-09-24, before `verify_contact.py` was written. Companion inputs: F02's
report (`../F02_terrain/report.md`, §5 follow-ups), F03's HANDOFFS ("To F04") and
discovery note §2. Item F04, verbatim: "No unacceptable tunnelling, ghost support,
interpenetration or visual/collision disagreement in frozen cases. Only claimed
collision capabilities must be demonstrated." Contracts C08 (contact/collision),
C14 (terrain), C15 (trunk surface).

## Statement (someone could disagree with it)

The three integrated forest artifacts — F01's clearing declaration, F02's terrain
bundle/query, F03's trunk declaration — form a DECLARED geometric contact model
(L1: analytic cylinder solid + stored-triangulation ground vs the walker's 0.004 m
sole spheres) in which every frozen contact pathology is either absent (no
tunnelling at the engine's own declared tick and speed scales; no ghost support;
no interpenetration beyond declared representation error; no visual/collision
disagreement beyond the frozen tolerances) or explicitly DECLARED (the inscribed
render mesh's 1.78307e-4 m chord error; render-only post markers) — and, honestly
separated, the frozen engine (L2) can exercise almost NONE of it in-vivo, because
its only contact machinery is point spheres vs ONE plane.

## Prediction (not yet measured)

Every frozen L1 case below lands inside its derived bound with the numbers shown in
the "expected" column where one is derivable; the two harness-sensitivity controls
(TUN-02, TUN-03b) FIRE (report a missed catch) by construction; and the suite
measures the engine's vertical-gap law's slope submergence at
r_s*(1 - 1/sqrt(1+0.042522^2)) ~= 3.6e-6 m worst on the actual terrain, inside the
derived legal-slope bound 4.9938e-6 m.

## Frozen model inputs (all cited; nothing tuned)

| Quantity | Value | Source (pinned) |
|---|---|---|
| Sole contact sphere r_s | 0.004 m | `gait_scene.py:28 SOLE_RADIUS`; `trunk_declaration.geometry.derivation.sole_contact_radius_m` |
| Touch quantum kTouch | 1e-5 m (release band 1e-6) | `gait_controller.hpp:36,52` |
| Declared tick bound dt | 1/300 s (substeps 4, RK4) | `gait_controller.hpp:1961` |
| Declared max walker speed v_max | 1.01 m/s | `tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json` `timing_paper.simulated_before.speed_m_s` (simulated_after 0.97) |
| Per-tick travel s_tick | v_max*dt = 3.366667e-3 m | derived |
| Per-tick vertical travel (terrain-following, F01 slope law 0.05) | s_tick*sin(atan(0.05)) = 1.681230e-4 m | derived |
| Trunk catch chord (head-on) | 2R + 2r_s = 0.074 + 0.008 = 0.082 m; derived full-tunnel speed 0.082/dt = 24.6 m/s | derived from `trunk_declaration` R, r_s |
| Trunk render/collision TOL | 2e-4 m | `trunk_declaration.representation_error.tolerance_m` |
| Terrain height/normal frozen tolerances | 1e-9 m / 1e-12 (F02's frozen family) | `../F02_terrain/report.md` measured-numbers table |
| Analytic tangency tolerance | 1e-9 (trunk_recipe's own predicate tolerance) | `trunk_recipe.on_lateral(tol=1e-9)` |
| Terrain surface | stored grid's triangulation (3,200 ground triangles, frozen 00-11 diagonal); queries refuse off-patch (strict >) | `terrain_query.py`; `earth_environment.hpp:118` |
| Trunk solid | cylinder cx,cz=(11.976783, 2.471766), R=0.037, y0=0, H=1.158, axis +Y | `trunk_declaration.collision_representation.solid` |
| Worst triangle slope (actual terrain) | 0.042522 m/m (F02's receipt) | `../F02_terrain/report.md` |
| Boundary posts | 80 hexagonal prisms, circumradius 0.05, RENDER-ONLY (no collision representation declared anywhere) | F01 `boundary.physical.posts_m`; F02 bundle `render.style` |
| Engine gap law | VERTICAL: gap = P_y + r - plane (`gait_controller.hpp:635-643`, `gait_scene.py:178`) | cited |
| Contact catch criterion (engine) | gap <= kTouch at a tick sample (`gait_controller.hpp:1727` gate) | cited |

Contact-model scope (declared): L1 verifies the DECLARED geometric model — the
terrain query surface and the trunk's ANALYTIC solid are the collision
representations (`trunk_declaration.collision_representation.engine_binding.
collision_route`: "Collision consumers implement THIS analytic contract"); the
render meshes are C14/C15's visual references. The friction placeholder 0.6 is
consumed NOWHERE in this suite (geometry only; provenance UNEVIDENCED-PLACEHOLDER,
acquisition G04 — handoff).

## Frozen case matrix (12 cases + 2 controls; sample seeds frozen: seed 20260924)

### Tunnelling (caught = at least one tick sample inside the contact band)

- **TUN-01 through-face, terrain.** Sole-sphere sweeps at dt=1/300, v=1.01 m/s:
  (a) vertical drop onto the worst-slope triangle's centroid; (b) vertical drops onto
  each of the 5 mound crests; (c) 45-degree diagonal approach onto mound 2's east
  flank through F02's worst discretization point (19.5, 5.5); (d) vertical drop into
  the trunk-site cell. Caught iff min engine-vertical gap <= kTouch.
  BOUND: caught; deepest penetration at first caught sample <= per-tick travel —
  3.366667e-3 m for the vertical drops (vertical speed = v_max), 1.681230e-4 m for
  the terrain-following case (c).
- **TUN-02 ridge-skip CONTROL (must fire).** Same harness with a synthetic
  4.329635 m sample step (half of the minimum mound diameter 2*4.329635) across a
  mound: detector MUST report NOT caught. Proves the harness can detect tunnelling
  (non-vacuity). Firing is the PASS condition; not a defect of the asset.
- **TUN-03 head-on trunk.** Sole sphere swept along -x at the axis mid-height
  (y = 0.579 m), sample spacing s_tick = 3.366667e-3 m: caught iff min sdf <= r_s.
  BOUND: caught; penetration <= s_tick. (b) CONTROL (must fire): spacing 0.083 m
  (> 0.082 m catch chord): detector MUST report NOT caught.
- **TUN-04 crease/edge sweep.** 500 seeded straight paths crossing shared triangle
  edges in the r <= 2 m ring around the trunk site (including frozen-diagonal
  crossings), plus a sweep across the WORST twisted cell (max diagonal-split surface
  difference over all 1,600 cells), at dt/v_max sampling. BOUND: caught with
  penetration <= 1.681230e-4 m; edge-continuity |dh| across 1,000 seeded edge
  crossings <= 1e-9 m (the surface is piecewise linear on shared corner heights).

### Ghost support (support claimed where no surface exists)

- **GHO-01 outside extent.** 12 frozen probes (each edge: +1e-9, +1e-6, +0.5 m
  beyond, strict >): `classify` == "outside" AND height/gradient/normal queries
  REFUSE (`f02_outside_extent`). BOUND: no surface served past the patch, 12/12.
- **GHO-02 floating-support probes.** At 5 frozen gap/saddle points (spawn cell +
  the 4 nearest-mound-pair midpoints): sphere at h + r_s + 1e-4 must report
  NO support (gap > kTouch); sphere tangent at h + r_s must report gap == 0
  (<= 1e-15). BOUND: floating gap in [1e-4 - kTouch, 1e-4 + 1e-12]; tangent |gap|
  <= 1e-15.
- **GHO-03 trunk volume/void.** Probes on the trunk axis at y in {0.1, 0.579, 1.0}:
  analytic sdf = -0.037 (INSIDE the solid: contact law says penetrating — no void)
  while distance to the render MESH = 0.037 (the mesh alone would lie). DECLARED
  model: consumers implement the ANALYTIC contract (collision_route), so the verdict
  is PASS-AS-DECLARED iff the mesh-vs-analytic shell disagreement is bounded by
  TOL: mid-facet tangent sphere penetrates the analytic solid by <= 2e-4 m, and
  analytic-tangent sphere's ghost gap to the mesh <= 2e-4 m, at all 32 mid-facet
  azimuths.

### Interpenetration (signed distances over frozen samples)

- **INT-01 sphere vs trunk analytic solid.** (a) tangency: 64 azimuths x 5 heights
  on the lateral + 33 per cap + 32 rim-circle: |sdf - r_s| <= 1e-9; (b) 4,096 seeded
  non-contact shell samples (sdf > 1.05 r_s): penetration max(0, r_s - sdf) == 0
  (min margin > 0, recorded); (c) 256 seeded interior samples: sdf < -1e-6 (recorded
  as expected-contact). BOUND: (a) 1e-9; (b) zero penetrations; (c) all inside.
- **INT-02 sphere vs terrain — the vertical-gap law's slope submergence.** At all
  3,200 ground triangle centroids, sphere placed at the law's zero gap
  (center = h + r_s vertical): TRUE plane penetration = r_s*(1 - n_y).
  BOUND (derived at F01's legal worst slope 0.05): worst measured
  <= r_s*(1 - 1/sqrt(1+0.05^2)) = 4.99377e-6 m (also <= TOL 2e-4; expected worst
  ~= 3.6e-6 at slope 0.042522). This is a MEASURED property of the engine's own
  declared law on slopes, not a defect — unacceptable only beyond the legal-slope
  bound.
- **INT-03 trunk base cap vs terrain (the ground joint).** (a) 65 cap-disk samples:
  terrain height == 0.0 (<= 1e-15), gradient (0,0), cap plane y=0 — coplanar
  contact, zero gap, zero penetration below y=0; (b) terrain heights on a 9x9 grid
  over the footprint square: all 0.0 -> no terrain point inside the solid;
  BOUND: all zeros within 1e-9 (site declared height 0.0 / slope 0.0).

### Visual/collision disagreement

- **VIS-01 terrain render vs collision at trunk neighborhood + boundary.** 2,500
  seeded samples in the r <= 2 m ring around the trunk site + 4x100 boundary-strip
  samples: independent barycentric evaluation of the stored RENDER triangle's plane
  vs `height_at` corner algebra (BOUND <= 1e-9 m, F02's frozen family), stored
  position cross-normal vs `normal_at` (BOUND <= 1e-12), `classify` inside at the
  closed edge |x| = 20.0; analytic-mound disagreement recorded (declared
  discretization; F02's global 6.46e-3 bound, expected 0.0 on the flat ring).
- **VIS-02 trunk render vs analytic.** Recompute the representation error from the
  STORED vertex table (32 mid-facet chord depths): must equal the declared
  1.78307e-4 m (<= 2e-7 of the sagitta formula) and be <= TOL 2e-4; 128/128
  triangles outward-wound; all 130 vertices on the analytic surface <= 1e-6.
- **VIS-03 posts are render-only (capability NOT claimed).** Frozen probe: sole
  sphere on the ground at 0.03 m from declared post index 30 ((20,0,0), F01
  `posts_m`), toward spawn: the collision query serves GROUND ONLY (support gap 0
  by placement) while the exact distance from the sphere center to the post's render
  triangles is measured — overlap recorded as a positive depth. BOUND: none to
  enforce — this case VERIFIES THE DECLARATION (posts are markers; the blocking rule
  is the extent rule, F01 `boundary.physical`; no post collision is claimed anywhere
  in F01/F02/F03), per the item's own observation clause "Only claimed collision
  capabilities must be demonstrated": post collision is NOT claimed and MUST NOT be
  demonstrated. Verdict vocabulary: PASS-AS-DECLARED with the measured overlap.
  Falsifier: an engine/declaration CLAIM of post collision existing.

## Falsifiers (frozen before the run; any hit refutes the L1 claim)

- **F-a (tunnelling):** any TUN case at declared tick/speed not caught, or caught
  with penetration beyond its derived per-tick bound — EXCEPT the two controls,
  whose FIRING is required (a control that does not fire refutes the HARNESS).
- **F-b (ghost support):** any support claim outside the touch band (GHO-02), any
  surface served past the strict-> extent (GHO-01), or the trunk void exceeding the
  declared analytic/mesh split (GHO-03 shell disagreement > 2e-4).
- **F-c (interpenetration):** INT-01 non-contact penetration > 0 or tangency beyond
  1e-9; INT-02 submergence > 4.99377e-6; INT-03 non-coplanarity beyond 1e-9.
- **F-d (visual/collision):** terrain agreement beyond 1e-9 (height) / 1e-12
  (normal) — F02's frozen family; trunk chord error > 2e-4 or != declared value
  beyond 2e-7; a claimed-but-undemonstrated capability (VIS-03 wording violation).

## L2 separation (declared here, reported separately)

No L1 case is claimed as an in-vivo engine capability. The L2 gap statement (in the
report + HANDOFFS) records, with cited lines, that the frozen engine's contact
machinery is point spheres vs ONE plane (`gait_controller.hpp:94` single
`plane_model_y_`; `:1961` tick; `:716` friction solve; `:2005-2010` recipe gates;
`earth_environment.hpp:67,118` sphere-vs-plane + out_of_patch; render-only meshes
`graph_earth.hpp:26-30,82`, upload `main.cpp:736,751,764`; no collision query route)
— so tunnelling through PROPS, terrain-heightfield contact, trunk contact and
multi-surface support CANNOT be exercised in-vivo today. Frozen-core law: the gap is
RECORDED for G04; no C++ is edited here.

## Stop rule

All 12 cases + 2 controls verdicted with numbers into `receipts/`, falsifiers
adjudicated, integrity paste shows writes ONLY in `agents/F04_contact/`; CPU-only;
headless; no engine C++; no servers. Exercising the engine HTTP contract and
measured friction acquisition remain named follow-ups (W10/G04), per brief.
