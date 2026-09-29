# MAT2-F07 PREREGISTRATION — forest obstacles and scene boundaries, frozen vocabulary

Committed BEFORE any implementation file, harness run, measurement or capture
frame existed (git-provable: this is the first commit of this contribution
directory on the attempt branch). Everything below is frozen now; amendments,
if any, will be separate commits BEFORE the implementation commit and BEFORE
any build, each disclosing what changed and why. No bar is tuned after a
measurement is seen.

## 0. Task and criteria identity (verbatim, not paraphrased)

- card: MAT2-F07; planning id F07; attempt `7f734268b7ee4a9887f794f9f620175e`;
  arrival `arrival-c7445b4a9e9640a8a821006fff1fd3b0`; criteria sha256
  `20eb25ac4401eea15fc28ad475c88a7d7b2798aad3a0bed36ecc4aa3fb56320b`;
  scope sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`;
  base revision `d62c56f67f7524222839c1ebf31f0dbc6fe9ea31` (branch-1 after
  fast-forward; = merge of PR #256 review/MAT2-B06, the sealed line tip,
  carrying merged F01/F02/F03/F04).
- done_when (verbatim): "The clearing offers traversable routes; no invisible
  walls masquerade as physical obstacles"
- falsifier (verbatim, card): "Rendered/collision mismatch, ghost support,
  missing boundaries or off-frame probe subject fails; tags alone do not
  establish contact."
- REGISTRY profile object (read READ-ONLY from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3`,
  `kanban.cards[MAT2-F07].spec.ontology_qualification.task.verification_profile`;
  canonical sha256 recorded in the receipt): id `forest`, kind
  `visible_static`, subject "Terrain/trunk geometry and actual contact
  surfaces", scenario "Qualify only this task: The clearing offers traversable
  routes; no invisible walls masquerade as physical obstacles Profile
  procedure: Inspect world frames and render/collision correspondence at
  representative ground/trunk probes, including silhouettes and depth. Use the
  task-owned subset of layers/behaviors. Inventory absent or unresolved
  components explicitly; do not require downstream skills to accept an
  upstream interface. Freeze exact applicable probes and views before
  execution.", diagnostic_layers ["render mesh", "collision surfaces",
  "normals/contact markers", "scene bounds", "stable 3D labels"], views
  ["clearing overview", "terrain/trunk seam close-up", "side and oblique
  depth checks"], clean_view_required true, numerical_evidence_required true,
  falsifier: "Rendered/collision mismatch, ghost support, missing boundaries
  or off-frame probe subject fails; tags alone do not establish contact."
- task_id in the capture manifest/context: `F07` (SHORT form).

## 1. Reconcile-first: reused published bytes only (nothing re-derived)

All input pins are published bytes of merged cards, asserted by raw sha256 at
every run; the harness refuses on any mismatch (`f07_pin_*`). Paths are the
committed sibling contribution directories at the base revision.

| pin | published location | raw sha256 |
|---|---|---|
| terrain asset (render arrays = query triangulation) | contributions/MAT2-F02/pins/terrain_bundle.json | `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52` |
| terrain query surface | contributions/MAT2-F02/pins/terrain_query.py | `b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1` |
| terrain bundle module/validator | contributions/MAT2-F02/pins/terrain_bundle.py | `c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e` |
| clearing recipe | contributions/MAT2-F02/pins/clearing_recipe.py | `ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc` |
| clearing declaration | contributions/MAT2-F02/pins/clearing_declaration.json | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` |
| trunk asset declaration | contributions/MAT2-F02/pins/trunk_declaration.json | `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1` |
| F01 render law | contributions/MAT2-F02/pins/f01_implementation.py | `50e191cfc6f592fd9919534c8986c049939a4e88c4922e135f383bbf06e693af` |
| F04 contact-qualification machinery (imported, never forked) | contributions/MAT2-F04/implementation.py | `5c398d22b4259d9e4c89ca3a7900610d629e318ac13b57681cbc7c617619e083` |
| M06 shared contact path | contributions/MAT2-M06/local_contact.py | `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc` |
| M06 contact law declarations | contributions/MAT2-M06/contact_law.json | `583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b` |
| F03 pinned trunk mesh asset | contributions/MAT2-F03/assets/trunk_01_mesh.json | `3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7` |

(The F04 pin hash is the raw sha256 of the merged bytes at the base
revision, recorded here from the merged tree before the implementation
commit; it is re-asserted against the actual bytes at every run.)

Merged-card constants reused as frozen (no new physics constants): ground
`monkey_clearing_ground`/`clearing_ground_topsoil` mu 0.9/0.65 thickness
0.002 (F02); trunk `trunk_01.*`/`wood_trunk_01` mu 0.6/0.6 thickness 0.0
solid (F03, friction remains the declared UNEVIDENCED-PLACEHOLDER, G04 debt);
probe shell matter `mass_tetra` 0.12 kg mu 0.6/0.4 thickness 0.002
(F02/M06); M06 law constants g 9.81, dt 0.005, slop/margin 1e-5, beta 0.2,
restitution 0, CCD max_iters 64 / tol 1e-12 (contact_law.json). Declared
scene vocabulary reused as frozen: extent square half 20.0 m with the engine
`out_of_patch` refusal rule (clearing_declaration.extent, citing
earth_environment.hpp:118); boundary post ring 80 posts spacing 2.0 m, bases
ON the edge, max gap to post 1.0 m, height 0.9 m, min protrusion 0.6 m, with
F02's note that no invisible wall may exist between the walkable area and the
visible ring (F07's law); safe spawn (0,0,0) body-radius envelope 0.25 m
required clearance 1.5 m; terrain max slope bound 0.05; trunk site
(11.976783, 0, 2.471766) analytic radius 0.037 m height 1.158 m required
clearance 1.5 m.

## 2. F07-owned scene vocabulary (the implementation's declared output)

The obstacle/boundary vocabulary is NEW scene data authored by F07 in
`assets/obstacle_declaration.json` (canonical JSON, self-pinned sha256, SI
metres, clearing frame x east / y up / z south):

- SEVEN explicit material obstacles, each with BOTH a render section and a
  pinned collision body carrying the SAME vertex array (the collision-visible
  law; nothing collidable is unrendered, nothing rendered is non-collidable):
  - `rock_01`, `rock_02`, `rock_03`: scaled regular icosahedra (12 vertices,
    20 faces), semi-axes sx in [0.30, 0.45], sy in [0.22, 0.34], sz in
    [0.26, 0.40] m, centre at the query height + sy (resting on the ground).
  - `log_01`, `log_02`: fallen trunks = horizontal 24-gon capped prisms
    (cylinder mesh, capsule solid), radius in [0.12, 0.16] m, length in
    [2.0, 2.6] m, axis horizontal at a deterministic yaw, axis height =
    query height + radius (resting on the ground).
  - `stand_01`, `stand_02`: dense stands of FIVE saplings each, vertical
    24-gon capped prisms radius 0.06 m height 1.6 m, bases on the ground on a
    ring of radius 0.45 m around the stand centre.
- Mesh determinism: splitmix64 integer PRNG seeded with SEED = 4600823
  (ASCII "F07"), the same PRNG family as F01's recipe; every derived float is
  rounded onto the 1e-6 grid before any use, so libm ulp differences cannot
  change the declaration bytes. Placement is rejection sampling in the frozen
  order rock_01..stand_02.
- Placement constraints (all frozen): obstacle centre inside [-19, 19]^2 (>=
  1.0 m from the extent edge, so the boundary ring stays clean); distance
  from the spawn >= 2.5 m (> declared clearance 1.5 m); distance from the
  trunk axis >= 2.0 m (> trunk clearance 1.5 m); pairwise centre distance >=
  footprint_radius_i + footprint_radius_j + 2*0.25 + 0.5 m.
- BOUNDARY RECORDS with named behavior (the card's declaration law):
  - `extent_rule`: kind physical_extent_rule, behavior `refuse_out_of_patch`
    (the declared clamp/refusal at the engine rule; never a silent
    invisible stop), rendered by the declared post ring.
  - one `solid_obstacle` record per obstacle: behavior `contact_stop` through
    the unmodified M06 law; names its render section id and collision body id.
  - `trunk_01`: kind climbable_feature (F03), behavior `contact_stop`
    (climbable, not a route-blocking wall; its footprint is in the mask).

## 3. Frozen numerical bars (all derived from pinned records; none tuned)

| id | bar | derivation |
|---|---|---|
| PEN_BAR_M | 1e-4 m | F04's frozen solver-anchored penetration bar, unchanged; measured by the MESH-EXACT convex-solid depth of any probe vertex inside the struck obstacle (face-plane tests on the obstacle's own vertex table; no representation slack) |
| PRE_OVERLAP | first contact of every impact episode has kind 'ccd' with gap_m > 0 | F04's frozen form (M06 X4) |
| ARREST_SPEED_BAR | 1e-3 m/s | new F07 bar: max probe speed over the LAST 5 ticks of every impact run; each impact is a normal incidence (frozen start points at analytic surface poles/midspan/mid-height so the contact normal is antiparallel to the approach) with restitution 0 (contact_law.json), so the post-impact speed must decay to rest |
| LEDGER_BAR | 1e-12 | per-tick ledger residual of every run (M06 A2 identity, F04 form) |
| PLANE_BAR_M | 1e-9 | F02/F04: every obstacle contact point lies ON its render triangle |
| ANALYTIC_BAR | 1e-9 m (rocks: mesh-exact convex hull) / r*(1-cos(pi/24)) + 1e-9 m (logs, saplings: inscribed 24-gon representation bound) | contact radial identity to the declared analytic form; the bound is the closed-form chord sagitta of the frozen mesh, computed from the declared radius, before any measurement |
| SLOPE_BAR | 0.05 | declared terrain.max_slope_bound; route cells sampled from the pinned query |
| PASSABLE_EXTENT_BOUND_M | 19.75 m | extent half 20.0 minus the declared body-radius envelope 0.25 (clearing_declaration.spawn.body_radius_envelope_m) |
| BLOCK_INFLATION_M | 0.25 m | the same declared envelope, inflated obstacle footprints |
| MASK_STEP_M | 0.5 m | mask resolution (81x81 centres over [-20, 20]^2) |
| EDGE_COVERAGE_BAR | 1.0 m | declared boundary.rendered.max_gap_to_post_m: every edge sample (step 0.05 m, the recipe's PERIMETER_SAMPLE_STEP) lies within 1.0 m of a post base; every post base lies exactly ON the edge (|x| or |z| == 20.0) and its base height equals the pinned query height at its (x, z) to 1e-6 |
| UNATTRIBUTED_BLOCKED_CELLS | 0 | invisible-wall audit: every mask cell blocked INSIDE the passable extent attributes to >= 1 declared obstacle/trunk inflated footprint; every cell blocked outside the passable extent attributes to the declared extent rule; any other blocked cell is an undeclared invisible wall and fails the build |
| STOP_DECLARATION_COVERAGE | 100% | every arrest event in the probe suite names the declared record of the surface that stopped it (contact record surface id -> solid_obstacle record); every mask block names its record; no stop without a record |

## 4. Frozen route verification (measured, not asserted)

- Walkability mask: cell centre (x, z) passable iff |x| <= 19.75 AND |z| <=
  19.75 AND the measured query slope at (x, z) <= 0.05 AND the horizontal
  distance from (x, z) to every declared footprint (rock: ellipse semi-axes
  sx + 0.25, sz + 0.25 — conservative over all heights; log: capsule segment
  + radius + 0.25; stand: disc centre + ring radius + sapling radius + 0.25;
  trunk_01: disc site + 0.037 + 0.25) is >= 0.25 m... precisely: the cell
  centre is blocked iff it lies inside any inflated footprint.
- Destinations (frozen, TEN — the spawn is the BFS origin, never a
  destination): D_trunk: the passable cell nearest
  the trunk approach point (trunk site shifted 1.5 m toward the origin);
  D_E/D_W/D_S/D_N: the passable cells nearest (±19.75, 0) and (0, ±19.75);
  D_obs_<id> for each of the seven obstacles: the passable cell nearest each
  obstacle centre (its viewpoint). The spawn cell itself must be passable
  (asserted separately as part of P3).
- BFS 4-connected from the spawn cell. Every destination must be REACHED
  (`route_exists` True); recorded per route: hop count, path length in metres
  (sum of step distances), min footprint clearance along the path (>=
  BLOCK_INFLATION_M - 1e-9 by construction of the mask), max sampled slope
  along the path (<= SLOPE_BAR).
- The route layer and the mask are DERIVED ONLY from declared geometry (the
  obstacle declaration + the pinned query + the declared extent); no cell is
  blocked by anything else. P4's attribution audit is the invisible-wall
  detector; FB1 proves it has teeth.

## 5. Frozen physical probes (the collision-visible law, measured)

Probe shell: F04's 12-triangle box, half 0.1 m, mass_tetra 0.12 kg, mu
0.6/0.4, thickness 0.002. All ticks through unmodified
`local_contact.solve_tick`, CCD on. Per F04's measured P0 heritage the ground
and any obstacle touch at exactly 0.0 m at the obstacle base, so each impact
run instantiates EXACTLY the struck obstacle's body (declared composition
scope); P0 below measures the refusal first.

| run | struck body | probe start (clearing frame) | velocity | ticks |
|---|---|---|---|---|
| HIT_rock_01..03 | the obstacle body | +x pole of the analytic ellipsoid + 0.25 m outward, at centre height | (-2, 0, 0) m/s | 30 |
| HIT_log_01..02 | the obstacle body | midspan side point (axis + radius, perpendicular to the axis) + 0.25 m outward | radial inward 2 m/s | 30 |
| HIT_stand_01..02 | the stand's sapling_01 body | (sapling axis + radius + 0.25, mid-height) | (-2, 0, 0) m/s | 30 |

Every tick records the probe vertices, velocity, all contact records and the
ledger residual; `evidence/contact_trace.json` is the state binding of the
capture rows. Bars of section 3 apply to EVERY tick of EVERY run.

## 6. Predictions (frozen before the build; each is falsifiable)

- P0_combined_ground_obstacle_refusal: solving the ground body together with
  ANY obstacle body is REFUSED by the unmodified M06 law (`nonfinite_state`,
  both-pinned exact contact at the obstacle base ring/point), F04's P0
  heritage at the obstacle bases. Any other outcome is disclosed as an
  amendment before the build proceeds.
- P1_tied_obstacle_assets: for every obstacle, the collision body vertices ==
  its render section vertices EXACTLY (element equality, both orders
  hashed); the render-section id set == the collision body surface-id set
  bidirectionally (no ghost surface, no phantom surface); every post base
  lies exactly ON the extent edge; edge coverage within the declared 1.0 m.
- P2_declared_boundary_completeness: the boundary record set (extent_rule +
  7 solid_obstacle records + trunk_01) covers EVERY stop/refusal event:
  unattributed blocked mask cells == 0; every probe arrest's contact surface
  has a declared record; the extent refusal is declared. No undeclared stop
  exists anywhere in the scene vocabulary.
- P3_routes_exist: BFS reaches ALL frozen destinations; per-route min
  clearance >= 0.25 - 1e-9 m; max sampled slope <= 0.05; the spawn cell is
  passable. The clearing offers traversable routes — measured.
- P4_no_invisible_walls: mask attribution (section 3 bar) holds on the real
  scene: zero unattributed blocked cells inside the passable extent.
- P5_obstacles_stop_physically: every HIT run: first contact pre-overlap
  (ccd, gap > 0); mesh-exact penetration <= 1e-4 m over ALL ticks; arrest:
  max speed over the last 5 ticks <= 1e-3 m/s; every contact point on its
  render triangle (plane err <= 1e-9) and within its analytic bar; ledger
  residual <= 1e-12.
- P6_no_ghost_support: no arrest/stop exists without a real contact record of
  the struck obstacle's declared surface (ledger identity, P5); the mask
  blocks no cell without a declared footprint; combined instantiation is
  refused (P0), so no support is invented by composition.
- P7_visual_correspondence: with render and collision arrays element-identical
  (P1), the pure ray/geometry marker classify (F04's oracle form, markers
  never read pixels) reports every assigned marker in every view at its
  frozen outcome (each obstacle subject VISIBLE_EXACT in the V1 overview;
  trunk and boundary subjects per the frozen marker table); zero
  VISIBLE_BUT_MISMATCH anywhere; zero UNRENDERED required subjects.
- P8_determinism: the full pinned pass run twice produces byte-identical
  evidence artifacts; no RNG except the frozen splitmix64 draws, no
  wall-clock anywhere in the build.

## 7. Falsifier arms (run FIRST, fail-first; each must bite; named refusals)

Every arm carries its OWN passing clean control (F04 house standard) and a
named premature guard (`f07_fb*_premature`); the bite is credited only when
its clean control passes. A non-biting arm fails the whole build
(`f07_falsifier_did_not_bite`).

- FB1_invisible_wall_in_mask: inject ONE undeclared blocked disc (radius
  1.0 m) into a COPY of the mask at a frozen meadow location (at least 3 m
  from every footprint and the spawn) — the attribution audit MUST fire with
  >= 1 unattributed cell (an invisible wall would be caught). Clean control:
  the real mask attributes 100% of its blocked cells (P4 pass).
- FB2_ghost_obstacle_collision_without_render: build a ghost obstacle (a
  fourth rock) with a collision body but NO render section — the
  bidirectional surface-set audit MUST fire (collision surface without
  render section), and the marker on the ghost's surface MUST classify
  UNRENDERED while the same-form marker on the real rock_01 classifies
  VISIBLE_EXACT (clean control). A stop with no rendered surface is
  detectable.
- FB3_phantom_obstacle_render_without_collision: build a phantom obstacle (a
  fourth stand rendered but with no collision body) — the surface-set audit
  MUST fire (render section without collision surface), and a probe driven
  through the phantom's footprint MUST record ZERO contacts while the same
  probe against the real stand_01 records a real contact (clean control).
  A rendered non-object is detectable.
- FB4_undeclared_stop_event: remove the extent_rule record from a COPY of the
  boundary records while the mask still blocks outside-extent cells — the
  stop-declaration audit MUST fire (blocking events with no declared
  record). Clean control: with the records present, stop coverage is 100%
  (P2 pass).
- FB5_route_metric_teeth: fence the spawn with a declared ring of eight
  footprint discs (radius 0.5 m, centres at radius 1.0 m, contiguous) in a
  COPY of the obstacle set — BFS from the spawn MUST reach NO destination
  (route_exists False for every one of the ten destinations), proving the
  route metric is measured, not asserted. Clean control: the real scene
  reaches all ten destinations (P3 pass).
- FB6_off_frame_probe_subject: a required subject placed 155.7 deg off the
  V2 view azimuth MUST classify OFF_FRAME (tags alone do not establish
  contact). Clean control: the same subject form classifies VISIBLE_EXACT in
  V2.
- FB7_render_collision_decouple: perturb a COPY of rock_01's render vertex
  array by +1 cm on ALL vertices of the triangle the marker's classify ray
  hits (F04 A3/A4 form) — the array-equality audit MUST fire (render/
  collision decoupled) and the classify MUST lose VISIBLE_EXACT (OCCLUDED:
  the raised render surface stands as a nearer same-surface hit) while the
  unperturbed render classifies VISIBLE_EXACT on the same ray (clean
  control).

## 8. Views, cameras and capture binding (frozen)

- Exactly the three profile views, by their exact registry names:
  "clearing overview" (wide bookmark over the clearing), "terrain/trunk seam
  close-up" (bookmark framed on the trunk base at the seam), "side and
  oblique depth checks" (bookmark from the opposite side, oblique elevation).
- Each view: one diagnostic row + one clean row (clean_view_required). Clean
  rows draw the pinned assets and the obstacle meshes ONLY — no overlays, no
  labels, depth-tested. Diagnostic rows carry ALL FIVE profile layers:
  render-mesh wireframes (ground, trunk, obstacles), collision-surface probe
  markers (obstacle vertices sampled on their analytic forms), contact-normal
  arrows + impact tick IDs at the frozen impact points (normals/contact
  markers), the scene-bounds rectangle (extent edge + corner posts), and
  stable 3D labels (obstacle ids, boundary records, trunk, spawn).
- Profile kind is `visible_static`: every row is an IMAGE locator
  (whole_frame BMP, 960x540 — publication byte budget, declared per row in
  the 16-field camera record; the pinned render law is otherwise unchanged).
  `capture_sha256` = sha256 of the single gate-bound artifact
  (`evidence/frame_V1_clearing_overview_clean.bmp`, F03's static form); the
  remaining stills are committed hash-listed supplementary files in
  `capture_layout.files`. Rows bind `state_binding.kind='state'` to
  `assets/obstacle_declaration.json`'s sha256.
- tick_interval [0, 0] (static). Transform-list gate (video-frame vs still
  identity) is NOT APPLICABLE to a static image capture — there are no video
  frames; this applicability boundary is recorded here before the build and
  restated in the report. The transform-list selftest still runs to prove
  the gate machinery refuses a flipped frame.
- Cameras: perspective, fixed bookmarks, quaternion convention
  quaternion_wxyz_camera_to_frame, forward -Z / up +Y, declared near/far
  [0.05, 500], declared vfov 55 deg, aspect == 960/540, one sample at tick 0.
  16-field camera records in `evidence/capture_manifest.json`.
- REGISTRY profile validation: `visual_capture.validate_manifest` with the
  profile object read READ-ONLY from agent_slots.sqlite3 (canonical sha256
  3348d00194c8d920abe3c5902c36a0f23088838bd293172f10f65a3de2670852);
  `visual_gate.verify` re-hashes camera JSON + capture and binds
  capture_sha256. `visual_acceptance` stays false BY DESIGN — independent
  visual review remains mandatory.

## 9. Honest boundaries (inventoried before the build)

- CPU-only, stdlib; no engine run, no native change, no GPU, no training, no
  runtime/playable-build acceptance. The obstacle stop law is the pinned M06
  contact law through unmodified vendored bytes — no new physics.
- The obstacle impact runs instantiate exactly one static body each (P0
  refusal heritage); a probe supported by the ground WHILE contacting an
  obstacle is NOT demonstrated and is recorded as an unresolved upstream
  component (F04's open seam composition), never claimed.
- Obstacle friction uses the F03 wood values for logs/saplings
  (UNEVIDENCED-PLACEHOLDER, G04 debt) and the F02 probe values on rocks
  (rock matter is not separately acquired; declared placeholder).
- Traversal is verified on the declared walkability mask (geometry + slope +
  footprints) at 0.5 m resolution with the declared 0.25 m body envelope;
  continuous-space motion planning is NOT claimed (card observation: player
  steering needs no general autonomous pathfinding).
- Frictionless boundary behavior: the extent rule is a declared refusal in
  the mask/vocabulary; the engine-side out_of_patch refusal is cited
  (earth_environment.hpp:118), not re-executed natively here; no native run
  is claimed.
- Visual acceptance itself belongs to the independent visual reviewer; this
  build's capture machinery is structural (validator + hashes + committed
  stills), not acceptance.
- Budgets: <= 32 files and <= 16 MB in this contribution directory.

## 10. Amendments (each committed separately BEFORE the implementation/build)

- (none yet)
