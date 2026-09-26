# F07 Preregistration — frozen BEFORE implementation

Recorded 2026-09-24, before `route_recipe.py`, `verify_routes.py`, the route
declaration, or any run. Item F07, verbatim: "The clearing offers traversable
routes; no invisible walls masquerade as physical obstacles. Player steering
needs no general autonomous pathfinding." Contracts C14 (terrain and
traversability), C23 (camera/presentation — noted: this item supplies the
occlusion/blocking geometry layer; camera response itself is U02's).

Inputs, read and re-proved at load (all three validated live on 2026-09-24
before this prereg was frozen):

| Input | Path (repo-relative) | Self-pin (body) | File sha256 |
|---|---|---|---|
| F01 clearing | `tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json` | `aa2607df97e0d6ec6a132b1e1ed0686da2ae920de7d659a8bb5ced013a358474` | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` |
| F02 terrain bundle | `tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json` | `8c7d60c88a75234a4ea94bc5ec83b666d620502b47cac8667e83b8713cb04fe0` (`bundle_sha256`) | `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52` |
| F03 trunk | `tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json` | `b7089e7826a221a570b261b8c69666a4017a6ab62d20a2223d061654d0f63fe3` | `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1` |

A drifted input (any mismatch) is a refusal, not a re-pin (F02's pattern).

## Statement (someone could disagree with it)

The clearing's route/blocking layer is already fully determined by the three
integrated artifacts: the ONLY physical blockers in the 40 m × 40 m extent are
the declared extent rule (visible as F01's 80-post ring standing exactly on that
edge) and F03's rigid trunk solid; the five mounds are traversable everywhere
under the 0.05 slope law; therefore every point of the clearing is reachable
from the spawn, a corridor of at least the walker's maneuvering envelope exists
from spawn to trunk, both tangent sides of every mound offer an alternative
route, and the traversal predicate needs no term beyond those two declared
causes — so no invisible wall can exist, and player steering needs no
pathfinding (straight headings suffice).

## Prediction (not yet measured)

1. Free space is ONE connected component: the BFS over the 0.05 m route grid
   from the spawn cell reaches every non-blocked cell; unreachable-free count
   is exactly 0; blocked cells number ≈ π·0.287²/0.05² ≈ 104 (all cause B2) on
   the closed grid, 0 for cause B1 (the closed extent contains its edge).
2. The spawn→trunk corridor's bottleneck width is exactly the approach-gate
   value: min clearance 0.5 m at the declared approach-zone entry (width
   1.0 m = the envelope bound, met with zero margin BY DERIVATION — the
   approach-zone radius is defined as r_block + 2·r_body), and the extent-side
   clearance along the route never drops below 8.0 m (the site is 8.02 m from
   the nearest edge).
3. Worst slope by every measure lands in the already-received bands: F01 grid
   central differences 0.034606 (F01's receipt, re-derived), F02 physical
   `gradient_at` over the route grid ≤ 0.05, analytic per-mound bound
   max A·π/(2R) ≤ 0.0471, F02 mesh triangle worst 0.042522 (F02's receipt,
   re-derived). No sample anywhere refuses on slope.
4. All 10 tangent routes (5 mounds × both sides) construct and verify valid;
   the straight route clears every mound footprint by ≥ 3.79 m (pre-freeze
   derivation: closest mound-footprint approach is mound 2 at 8.123 m centre
   distance − 4.330 m radius).
5. Edge-ray walks from spawn toward each of the four edges stay traversable up
   to the post line (within one grid step) and the first refused query beyond
   it is `f02_outside_extent` — the blocking edge is where the visible posts
   stand, never inside the ring.

## Frozen values (no tuning after this point)

### Walker stance/turning envelope — the derivation (no free parameter)

- `r_body = 0.25 m` — F01's declared body-footprint envelope
  (`spawn.body_radius_envelope_m`, "generous macaque envelope"), consumed from
  the LIVE declaration, not restated.
- Stance floor: a route point admits the walker iff the envelope fits:
  free width ≥ 2·r_body = 0.5 m.
- Maneuvering quantum: F01's frozen passing-room derivation
  (`R_clear = r_trunk_bound + 4·r_body`) establishes **4·r_body = 1.0 m** as
  THE passing-room width of this scene — two body diameters, i.e. room to pass
  a blocker and turn about. Corridor envelope **W_env = 4·r_body = 1.0 m**
  (min clearance 0.5 m). This reuses the scene's own derived number; it is not
  a new choice.
- Gait cross-check (context, not a second constraint): the pinned stride
  0.72 m (`derived_numbers.json timing_paper.simulated_before.stride_m`) fits
  inside W_env — a full pinned stride completes within the corridor.
- Discretization: route grid step **Δ = r_body/5 = 0.05 m** (the stance radius
  spans 5 cells; the envelope width spans 20 cells; 801×801 grid over the
  closed extent). Pinned per-tick travel s_tick = v_max·dt = 1.01/300 =
  3.366667e-3 m ≪ Δ (v_max 1.01 m/s, `timing_paper.simulated_before.speed_m_s`;
  dt ≤ 1/300 s, `gait_controller.hpp:1961`): physics steering corrections occur
  INSIDE one route cell — the operational content of "no general autonomous
  pathfinding". Also pinned for citation: SOLE_RADIUS 0.004 m
  (`gait_scene.py:28`), K_TOUCH 1e-5 (`gait_scene.py:27`), trunk radius
  0.037 m = Oku foot 0.074/2 (`trunk_declaration`).

### Obstacle inventory (frozen)

1. **The 5 mounds — NOT obstacles.** Slope-limited traversable features under
   F01's walk law |∇h| ≤ 0.05 (continuous bound ≤ 0.0471 by F01's amendments;
   F02 mesh worst 0.042522). Blocking: NO.
2. **The trunk — THE one rigid blocker.** F03's analytic solid, radius 0.037 m
   at the pinned site (11.976783, 0.0, 2.471766). Routing blocker radius
   **r_block = r_trunk + r_body = 0.287 m** (the body envelope may not
   interpenetrate the solid) — inside F01's 0.5 m footprint bound, so F01's
   spawn-clearance chain is untouched. Blocking: YES.
3. **The boundary — the extent rule itself**, |x| > 20 or |z| > 20 (strict >,
   `earth_environment.hpp:118` semantics), VISIBLE as F01's 80 posts standing
   exactly ON that edge (F01 receipt: worst off-edge error 0.0, ring extent
   == 20.0, coverage gap ≤ 1.0 m). F04 VIS-03: posts are RENDER-ONLY
   (PASS-AS-DECLARED, NO-CLAIM) — the posts do not block; the rule does.
   Blocking: YES (the rule).
4. **The spawn disk** (R_clear = 1.5 m): headroom by construction, not a
   blocker.

### Blocking-causes table — skeleton (frozen; the implementation instantiates exactly these rows)

| id | predicate (the ONLY refuse conditions `traversable()` may contain) | declared physical cause | visible cause | blocks? |
|---|---|---|---|---|
| B1 | point outside the closed extent (\|x\| > 20 or \|z\| > 20, strict >) | F01 `boundary.physical` extent rule (= engine `out_of_patch`) | 80 ochre posts, bases on the edge ≤ 1e-6 m, ring extent == 20.0 | YES |
| B2 | dist to trunk axis < 0.287 m (r_trunk 0.037 + r_body 0.25) | F03 `collision_representation` analytic cylinder solid | trunk render mesh, 130 v / 128 tri, representation error 1.783e-4 ≤ 2e-4 m | YES |
| N1 | slope > 0.05 anywhere would be a NEW blocker | F01 `terrain.max_slope_bound` (the walk law) | the terrain surface itself (C14: render IS the collision surface) | NO — predicted ≤ 0.05 everywhere; a refusal here FIRES falsifier (c) |
| N2 | boundary posts | none declared (F04 VIS-03 NO-CLAIM, render-only) | the posts themselves | NO — the predicate contains NO post term (structural: see sweep) |

**Zero unexplained causes** is the acceptance clause: every blocked grid cell
must carry annotation B1 or B2; every refused sample query must be one of the
above; the predicate's source contains no other refuse site (checked by the
enumeration sweep, not by prose).

### Routes (frozen constructions, derived from live data; no search tuning)

- **R0 — spawn→trunk straight route (the no-pathfinding claim):** the segment
  from (0,0,0) to the trunk axis, sampled at 0.01 m, must be traversable at
  every sample (B1/B2/N1 never refuse outside the declared final approach),
  with clearance ≥ 0.5 m everywhere outside the approach zone. Pre-freeze
  derivation: length 12.229185 m; nearest mound-footprint approach 3.793 m
  (mound 2, centre distance 8.1229 − radius 4.3296).
- **R1..R5 × {L,R} — tangent routes around each mound:** from the spawn,
  the straight segment tangent to the disk {centre C_i, radius R_i + r_body}
  (the stance envelope must clear the visible footprint), extended until it
  has passed the mound centre plane by R_i + 2·r_body. BOTH tangent sides must
  yield a valid route: inside the extent; min distance to C_i ≥ R_i + r_body
  (measured, not assumed); clearance to B1/B2 ≥ 0.5 m; slope ≤ 0.05;
  outside the trunk approach zone. 10/10 required.
- **BFS route — the graph-level corridor:** shortest 8-connected free path
  from the spawn cell to the contact ring (free cells with
  r_block ≤ dist_axis < r_block + Δ·√2). 8-connectivity cannot leak through
  the B2 disk (≈ 11 cells across). Route-grid convention: row = z, col = x
  (F01's grid convention), cell (i, j) centre at (−20 + j·Δ, −20 + i·Δ).
- **Corridor width (frozen definition):** clearance(p) =
  min(20 − |x_p|, 20 − |z_p|, max(0, dist_axis(p) − r_block)); the width at p
  is 2·clearance(p) (maximal inscribed free disk diameter, conservative);
  the **approach zone** is dist_axis ≤ r_block + 2·r_body = 0.787 m — inside
  it width → 0 BY DESIGN (the walker is deliberately touching its goal).
  The corridor bound applies to route cells OUTSIDE the approach zone:
  **2·min clearance ≥ W_env = 1.0 m** (min clearance ≥ 0.5 m). Reported for
  R0 (straight) and the BFS route both.
- **Traversability predicate (frozen form):** traversable(x, z) :=
  inside closed extent AND dist_axis ≥ r_block AND slope(x, z) ≤ 0.05, with
  slope from F02's physical `gradient_at` (ONE implementation — no second
  truth); B1/B2 refusals annotated with their cause id; slope refusals would
  be annotated N1 (none predicted).

### Falsifiers (frozen before the run; a hit refutes the design)

- **(a) Invisible wall / unexplained blocker:** any grid cell that is
  free-by-predicate yet unreachable from the spawn cell (BFS); OR any cell
  refused without cause B1/B2 (in particular any N1 slope refusal); OR an edge
  ray from spawn whose last traversable point stops short of the post line by
  more than one grid step (blocking inside the visible ring).
- **(b) Corridor narrower than the derived envelope:** 2·min clearance
  < 1.0 m on R0 or the BFS route outside the approach zone; or any tangent
  route with min clearance < 0.5 m; or any tangent route failing its
  construction invariants (footprint clearance, extent, trunk clearance).
- **(c) Any mound steeper than the 0.05 law:** worst slope > 0.05 by ANY of
  the four measures (F01 grid central differences; F02 physical gradient on
  the 0.05 m route grid; analytic per-mound max A·π/(2R); F02 mesh triangle
  slopes). Re-verified from F01's grid as the brief demands.

## Amendment 1 (2026-09-24, AFTER the first run — a prereg miss, RECORDED then re-derived)

The first run kept falsifiers (a) and (c) green and corridor V4 green, but V5
FIRED: 8 of the 10 frozen tangent routes failed their validity checks
(`receipts/run_attempt1_RED.json`, preserved). Diagnosis: the CONSTRUCTION was
mis-derived, not the scene. "Extend the tangent past the mound centre plane by
R + 2·r_body" is unbounded toward the extent edge; five mound centres lie
within ~2–7 m of a boundary (e.g. mound 0 at (−18.31, −6.42), 1.69 m from the
west edge), so those segments ran PAST the declared extent — the refusals they
then hit were the B1 edge doing its declared, VISIBLE job, caught by a waypoint
rule that told the walker to leave the world. Reachability V3 passed in the
same run (zero unreachable free cells): routes around every mound EXIST; the
frozen endpoint rule simply overshot them.

Re-derivation of the endpoint (no scene number changed; falsifiers (a)–(c)
unchanged): a route "around the mound" ends at the EARLIER of

- **t_exit** — the ray's exit from the enlarged disk {C_i, R_i + 2·r_body}
  (the walker has passed the mound with the stance envelope clearing it):
  t_exit = t_pass + sqrt(r_body·(2·R_i + 3·r_body)), exact half-chord algebra
  for a ray at tangent distance R_i + r_body; or
- **t_extent** — the ray's exit from the closed extent (analytic wall times
  from the stored direction; the walkable world ends there, at the visible
  post line).

Second clause, found by the validator during this re-derivation, BEFORE the
second run (measured on all 10 routes: four sides reach the wall first; mound
3's R side at t_extent 21.68 m before its t_pass 22.22 m): the centre-plane
requirement binds only a side the world lets pass — for an extent_edge side
the declared wall may terminate the ray before the mound's centre plane, and
that is PASS-AS-DECLARED (the mound's far side there lies outside the walkable
world; the around-route exists via the other side, which every mound has).

Validity per side (kept strict): all samples traversable (a correctly built
segment never leaves the world); own-mound margin ≥ R_i + r_body − the derived
direction-rounding tolerance; t_end ≥ t_pass (the centre plane was passed);
**trunk clearance (B2) ≥ 0.5 m at EVERY sample** (a mid-route pinch toward the
small trunk disk would be a genuine invisible-pinch failure); wall clearance
(B1) may fall below 0.5 m only as a CONTIGUOUS FINAL APPROACH — the shallow
samples must form a suffix of the route (perpendicular distance to the wall,
so a slanted approach legitimately spans more than 0.5 m of arc length) — AND
only when the route is B1-terminated with the endpoint on the visible edge
(within one sample step of |x| or |z| = 20). A mid-route dip below the
envelope that then recovers is a pinch with no declared cause and FAILS. A mound verdicts FAIL only if BOTH sides fail (no
around-route exists) or any side fails non-B1 checks; V5 passes only if every
mound has at least one outright PASS side. The prediction "10/10 construct and
verify" is corrected to: 10/10 construct; B1-terminated sides are expected for
the boundary-adjacent mounds and are declared causes, not misses.

### Declared new scene-data paths (the route/blocking layer as data)

- `tools/monkey_campaign/data/monkey_routes/route_recipe.py` — frozen
  constants (envelope, blockers, bounds, grid), deterministic tangent/route
  constructions from the LIVE inputs, canonical compile, self-pinned
  `route_declaration_sha256`, strict `loads`, full validator. Schema
  `chimera.monkey_routes.v1`. Stdlib-only, CPU-only, headless.
- `tools/monkey_campaign/data/monkey_routes/route_declaration.json` — the
  compiled declaration: pinned input digests, the walker envelope + derivation,
  the blocking-causes table, route definitions (R0, R1..R5 × {L,R} waypoints),
  grid spec, frozen bounds. Deterministic: same live inputs → byte-identical
  file (derived floats snapped to the 1e-6 grid, F01's rule).

These two paths + this agent dir are the ONLY writes this task may make.

## Stop rule

All three falsifiers verdicted NOT OBSERVED with receipts; the blocking-causes
table closes with zero unexplained causes; route map figure written; handoffs
to F08/W10/F05 recorded; `git status` shows changes only in
`tools/monkey_campaign/agents/F07_obstacles/` + the two declared data paths.
CPU-only, headless; no engine launch, no C++ edits, no GPU, no servers.
