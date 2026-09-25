# D-FOREST-RUNTIME — native collision integration brief for the first playable clearing

- **Card:** D-FOREST-RUNTIME-20260924 (planning ids F02/F03/F04)
- **Attempt:** 6691766eea124942984e4b6e8e24bc82
- **Arrival:** arrival-ec97e63be318447499de475cc02077cd
- **Branch:** branch-3 (checkout head `c525b82c7c3ce0128565424764293a3c85811ab3`, clean, sparse)
- **Criteria:** dc47ff858da36a02a6e2354ea25aa480e929e098e0ad89742a0c7d09bf815cb8
- **Objective (verbatim):** "Specify the smallest missing native terrain/trunk collision integration needed for the first playable clearing."
- **Deliverable class:** specification only. No implementation files were edited. No engine started, no GPU, no builds, no server.

## SCOPE VERDICT (one line)

**Terrain-first:** the smallest integration is a per-point terrain surface service replacing the walker's single
`plane_model_y_` scalar (gait lane) plus a collision query route, with the trunk scoped in Stage 1 to its already-derived
F07 blocking disk + rendered mesh, and full trunk/rigid-prop contact named as the separately-gated Stage-2 follow-up —
because trunk contact requires a subsystem that does not exist (no prop machinery, no non-(0,1,0) solver rows, no SDF
route, no measured bark friction), while terrain contact is a delta onto contact machinery that already solves, bisects
contact events, and solves Coulomb friction.

---

## 1. Pinned revisions (verified)

| Label | Commit (full sha) | Role |
|---|---|---|
| game lineage master | `33e7a444fe7b4c35aa99afe7ef898046877025b4` | THE pinned runtime revision for every engine citation below |
| typeb-gpu-finish tip | `a62b286effa27ee2db7bbcb65507a2ac45ad0d0c` | Python walking drivers; `derived_numbers.json` (v_max 1.01 / 0.97 m/s) |
| first-skill-prestage | `73f3a86082e0f5ab6de88e17831e4d10cb9e8b00` | frozen first_skill modules + RUNBOOK |
| wave-46/47 ship state | `f106fc54448aece034886c65e4bc5ccf4ebd6c7f` | the byte-anchored walk state; ancestor of 33e7a444 |
| monkey-play worktree head | `dc7ea81111d98f32a4d88252c59f2fb8cf3c7399` | forest artifacts (F01–F08 data + agent dirs) |

Blob shas cited by this brief (all read via `git ls-tree`/`git show` at the named revision):

| File | Revision | Blob |
|---|---|---|
| `ChimeraEngine/engine/gait_controller.hpp` | 33e7a444 | `5863348f2deef1f01e3cf761d0c4151a10035a6d` |
| `ChimeraEngine/engine/gait_controller.hpp` | f106fc54 | `02335aa982e26b2a196aad88ba12aacfe30a17a0` (**drift note**, §2.4) |
| `ChimeraEngine/engine/earth_environment.hpp` | 33e7a444 | `38edb9807b61539094c05464d303723a16dfbec7` |
| `ChimeraEngine/engine/graph_earth.hpp` | 33e7a444 | `accfecbe03415654a68f354157d9ce51572f467d` |
| `ChimeraEngine/engine/engine.hpp` | 33e7a444 | `58a2f3650b1f211d6a8f972a5362a7eef3133955` |
| `ChimeraEngine/engine/engine.cpp` | 33e7a444 | `3abc8e37b046d03e7f84ed734a13c5a513a7989e` |
| `ChimeraEngine/engine/main.cpp` | 33e7a444 | `beca3cf844069e032f71f6a39d37dbc64218f1ca` |
| `ChimeraEngine/engine/membrane_tick.hpp` | 33e7a444 | `5a15b1097ab007e69df3d9e295fbc1cb6f13482f` |
| `ChimeraEngine/engine/membrane_tick.cpp` | 33e7a444 | `ae11ac7696d8324a9e8d15e5bea0a75e678e2763` |
| `tools/science_funnel/gait_scene.py` | 33e7a444 | `5c8792aef60f9eb2eb2e10549546ff12a2efe21b` |
| `tools/playable_slice/slice_server.py` | dc7ea811 | `721b643d6e35ec30d6f48868e1cdb44233a0c1f2` |
| `tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json` | dc7ea811 | `e0f9f8ed3c01277086f844db22bf2125a7be472b` |
| `tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json` | dc7ea811 | `f4be30e37da4f25ef5d577e8b30c3726891cbfde` |
| `tools/monkey_campaign/data/monkey_clearing/terrain_query.py` | dc7ea811 | `0f68f951b39fb4c2c99b5930ddbc1ee9cfad17a1` |
| `tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json` | dc7ea811 | `c7b37531a98a6e213107ecdb9e61bad1074fc973` |
| `tools/monkey_campaign/data/monkey_trunk/trunk_recipe.py` | dc7ea811 | `698acf7c04827114a61998f989d4a544f5d9ea6f` |

---

## 2. The native collision-path inventory (what actually exists at 33e7a444)

Every line below was read at the pinned blob with `git show`; signatures are quoted, not paraphrased.

### 2.1 Path A — the science-funnel walker's contact (THE creature contact machinery; the path the playable walk obeys)

`ChimeraEngine/engine/gait_controller.hpp` (blob `5863348f…`, class `GaitWalker`):

- `:36` — `static constexpr double kTouch=1e-5,kSlip=1e-9;` and `:52` — `static constexpr double kReleaseBand=1e-6;` — the touch quantum and release band (release edge 1.1e-5 m).
- `:94` — member declaration `V shift_,gravity_;double dt_=0,plane_world_y_=0,plane_model_y_=0,mu_=0,mtot_=0,store_total_=0;` — ONE plane scalar pair for ALL contact points.
- `:635-644` — `double gap_of(const Evaluation& e,size_t k)const` — the vertical gap law:
  `double gh=e.point(points_[h].index,points_[h].local).first[1]+points_[h].radius-plane_model_y_;` (`:642`),
  `double gm=e.point(points_[m].index,points_[m].local).first[1]+points_[m].radius-plane_model_y_;` (`:643`),
  `return (std::min)(gh,gm);` (`:644`) — heel/MP pair-min. Units: m. Convention: the law's zero-gap REST is
  `point_y = plane − r_sole` (F04 GHO-02 measured: rest gap exactly 0; naive sphere-center tangency reads `2*r_sole = 8e-3 m`).
- `:645` — `Dense contact_row(const Evaluation& e,size_t k)const{auto j=e.point(points_[k-(k%2)].index,sole_local(e,k)).second;Dense r(n_,0.);for(size_t i=0;i<n_;++i)r[i]=j[i][1];return r;}` — takes ONLY the y-row: every contact normal in the solver is (0,1,0).
- `:646` — `Dense tangent_row(const Evaluation& e,size_t k,int axis)const{...r[i]=j[i][axis];...}` — friction tangent rows are WORLD x/z axes (axis 0 or 2), not surface tangents.
- `:683-715` — `static Dense project_rows(const Dense& initial,const Dense& inverse,const std::vector<Dense>& rows,const Dense& floors,std::vector<double>* multipliers,size_t n_stops=0)` — mass-metric active-set cone projection, `require(R>=1&&R<=10,"gait_row_budget")` (`:685`), tier law for joint stops.
- `:716-726` — `static void friction_solve(const Dense& initial,const Dense& inverse,const Dense& row_n,const Dense& row_t,double floor_n,double floor_t,double mu,double slip_sign,Dense& force,double& lambda_n,double& lambda_t,int& mode)` — discrete-cone Coulomb solve. KEY FACT: it accepts ARBITRARY `row_n`/`row_t`; it is only ever FED the plane rows. Refusal `gait_friction_slide_singular` at `:723`.
- `:1724` — `double gate=1e-6+1e-3*joint_speed_scale(s);` and `:1727` — the engagement gate
  `touching[k]=plane[k]||(live[k]&&gap_of(e,k)<=kTouch&&inner(rown[k],s.v)<=gate);` — contact arms only at a tick sample with gap ≤ kTouch AND inward speed under the gate. This is the ONLY anti-tunnelling machinery: a tick-sample band, plane-only.
- `:1950-1951` — contact-event bisection localization: `require(std::abs(gap_of(evaluate(crossing),size_t(khit)))<1e-9,"gait_contact_localization");` — a located crossing must satisfy |gap| < 1e-9 m.
- `:1958` — `GaitWalker(const J& data,double gravity,V shift,double dt=1/300.)`; `:1961` — `require(dt>0&&dt<=1/300.,"gait_timestep");require(recipe_.at("substeps")==4,"gait_substeps");`
- `:2003` — `plane_world_y_=number(recipe_.at("contact_plane_height_m"));require(std::isfinite(plane_world_y_),"gait_contact_plane_invalid");plane_model_y_=plane_world_y_-shift_[1];` — the ONE recipe height, and THE model-frame transform (world → model subtracts `shift_[1]`).
- `:2005` — `require(config_.contains("contact_friction")&&config_["contact_friction"].is_number()&&number(config_["contact_friction"])>=0&&number(config_["contact_friction"])<=1,"gait_friction_flag_invalid");mu_=number(config_["contact_friction"]);` — ONE scalar mu for the whole body (scene value 0.6, an uncited design constant — F03's UNEVIDENCED-PLACEHOLDER, acquisition = G04).
- `:2006-2010` — `contact_points` array; each `ContactPoint{std::string name,body;size_t index;V local;double radius;}` (`:56`), `out.radius=number(p.at("radius_m"));require(out.radius>0,"gait_contact_radius_invalid");` and `npts_=points_.size();require(npts_>=1&&npts_<=8,"gait_contact_capacity");` — capacity 1..8 point-spheres, sole radius 0.004 m (`gait_scene.py:28 SOLE_RADIUS=0.004`).
- Public drive API: `void configure(const J& input)` `:2243`; `void step()` `:2262`; initial seating requires `require(gap_of(e,k)>0,"gait_initial_penetration")` for every point `:2239`.

This class is instantiated ONLY in the science-funnel/trace machinery (`tools/science_funnel/typeb*`, `tests_coupled_arm/gait_unit.cpp`, `tools/constraint_ledger/trace_harness.cpp`, `tools/policy_compat/snapshot_api.py` — verified by `git grep -l GaitWalker 33e7a444`). It is NOT wired into `main.cpp`; the engine's `/gait_bin` (`main.cpp:1954`) loads CPG display constants for the render-side gait display, not this solver.

Frozen acceptance anchors of the plane walk (receipt `tools/science_funnel/validation/gait_zero_20260919/receipt_wave47.json` @ 33e7a444): refusal `302 gait_positional_correction_budget`, worst moving ledger `30.970714 J`, stdout sha `8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc` (22,530 bytes), scene sha `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`, plain stderr `b505bb65…`, ship trace `c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481` (65,870 lines). Host replay walks past tick 41 (t=100, rc=0) — PLAY_BOARD.

### 2.2 Path B — the playable slice's native floor (the live playable process's floor law)

`ChimeraEngine/engine/membrane_tick.cpp:840-873` — THE MOVEMENT LAW: one rigid Y DOF for the whole body:

```
:856  const float depth = std::max(0.f, -lo);                       // lo = world lowest vertex y
:857  float F = k_ground_ * depth + c_ground_ * std::max(0.f, -root_vy_);
:858  const float F_cap = 50.f * mass_kg_ * G_EARTH;
:865  root_vy_ += (g_contact_n_ / mass_kg_ - G_EARTH) * dts;
```

against the fixed floor plane **y = 0** (`hpp:91`: "the floor y=0 holds what presses it through a penalty spring at the body's lowest vertex"). Constants `membrane_tick.hpp:423-427`: `mass_kg_=13824.5f`, `k_ground_=1.3562e7f` N/m (= m·g/0.01), `c_ground_=6.062e5f` N·s/m (ζ=0.7), clamps |root_y| ≤ 3 m, |vy| ≤ 30 m/s (`cpp:866-869`). Switched by `POST /tick_gravity` (`main.cpp:1597`). The playable front door is `tools/playable_slice/slice_server.py` (dc7ea811), whose fall-test/settle bars bank these same constants (`SETTLE_SINK_M = 13824.5*9.81/1.3562e7  # 0.010000 m`, `SETTLE_VY = 0.05`). Contact topology: ONE rigid root vs ONE horizontal plane; no friction, no x/z dependence, no heightfield. This is the membrane standing-body's law (mass 13,824.5 kg), deliberately separate from the 10.038 kg gait walker.

### 2.3 Path C — the earth-patch demo lane (single sphere vs one tilted plane)

`ChimeraEngine/engine/earth_environment.hpp` (blob `38edb980…`, class `EarthTrial`):

- `:67` — `double d=dot(x,n_)-r_,vn=dot(v,n_);normal_impulse_=0;` — sphere-vs-plane signed distance (m).
- `:107` — `n_={-std::sin(s),std::cos(s),0};tangent_={std::cos(s),std::sin(s),0};` — the plane normal comes from `slope_deg` and tilts in the X-Y plane only; there is NO height field and NO second surface.
- `:91` — `require(scene.at("schema")=="chimera.earth_patch.v1"&&number(scene.at("tick_hz"))==300,"earth_scene_contract");` — 300 Hz tick.
- `:118` — `outside=std::abs(x[0])>number(scene_.at("patch_half_width_m"))||std::abs(x[2])>number(scene_.at("patch_half_width_m"));` — the strict-`>` extent rule (`out_of_patch` phase, `:124`), the rule F01/F02 copied.
- `:119` — `require(dot(x,n_)>=r_-1e-10,"earth_ground_penetration");`

The render is the SAME plane: `graph_earth.hpp:102-105` `auto ground=[&](double x,double z){return V{x,std::tan(slope)*x,z};};` tiled 12×12 — render≡physics by construction (the pattern F02's "one surface, two projections" reuses). Demo lane (`native_earth_patch` mode, `graph_earth.hpp:39`), not the playable clearing.

### 2.4 Render-only mesh machinery and the NEGATIVE evidence

- `engine.hpp:138-141` — "triangle mesh rendering (depth-tested opaque Lambert)": `bool load_mesh(const std::vector<float>& verts, const std::vector<uint32_t>& indices, uint32_t vcount, uint32_t icount);` — 9-float pos+normal+color layout, size/9 (`engine.cpp:1862`).
- `engine.cpp:1854-1937` — THE NORMAL-HYGIENE GATE: non-finite/non-unit stored normals are re-derived as area-weighted adjacent-face sums at upload; healthy vertices untouched.
- Upload routes: `main.cpp:736` (`--science-surface`), `:751` (`--thermal-salvage`), `:764` (`--earth-patch`), `:1096`+ (`POST /mesh_bin`), thread-landing `:4266`.
- NEGATIVE (verified by `git grep` at 33e7a444): **zero** hits for `heightfield|height_field|terrain` in `gait_controller.hpp` and `earth_environment.hpp`; **zero** collision/SDF/height query routes in `main.cpp` (only URL query-param helpers). The HTTP contract has NO collision query route (F04's route survey confirmed).

### 2.5 Revision-drift honesty note

The wave-47 receipt's hpp line numbers (`:255` tau_settle, `:301` arch, `:1997` PD gains, `:2066` kHeightFloor) match blob `02335aa9…` at `f106fc54`, NOT master's blob `5863348f…` at 33e7a444 (verified: the file drifted between the ancestor f106fc54 and master). **Every citation in this brief is verified directly at 33e7a444's blob and is self-consistent.** Any implementation task must re-pin its own diff target the same way.

---

## 3. Static-vs-native comparison (what F02/F03/F04 actually proved vs what the engine lacks)

| Capability | F02/F03/F04 STATIC proof (L1, Python-vs-Python declarations) | Native engine reality at 33e7a444 (L2) |
|---|---|---|
| Rendered ground vs query surface | F02: one surface two projections; worst height disagreement **2.776e-17 m** over 20,177 pts (bound 1e-9); normals 0.0; gradient consistency 6.939e-18; both sides Python declarations over the same stored arrays | The engine never loaded the mesh and answers no query; its floors are constants — y=0 (membrane), one `contact_plane_height_m` (gait), `tan(slope)*x` (earth) |
| Terrain heightfield contact | None claimed — F02 named it "an ENGINE change … not an agent-file edit" | **Does not exist.** The walker's plane is ONE height; even the terrain is beyond the walker contact model |
| Trunk collision representation | F03: analytic capped cylinder (cx,cz)=(11.976783, 2.471766), R=0.037 m, H=1.158 m, axis +Y, closed-form radial/cap normal laws; mesh N=32, measured chord error 1.78307e-4 ≤ TOL 2e-4 m; surface IDs + material record | **Does not exist.** No rigid-prop/mesh collision machinery of any kind; meshes are render-only (§2.4) |
| Tunnelling | F04: TUN-01 7/7 caught at dt=1/300, v=1.01 m/s, worst pen 1.0000e-3 ≤ 3.3667e-3 m per-tick bound; TUN-02/TUN-03b controls FIRE (4.329635 m ridge-skip step missed by design); trunk catch chord 2R+2r_s=0.082 m ⇒ 24.4x margin | Only the kTouch tick band against ONE plane (`:1727`); no continuous collision detection; nothing to tunnel through but the plane |
| Ghost support | F04: GHO-01 12/12 strict-`>` extent refusals (`f02_outside_extent`); GHO-02 floating probes (+1e-4 m) claim no support; law-rest gap exactly 0 (≤1e-15); discovered convention: engine rest = `point_y = surface − r_sole` | The :1727 gate arms contact only at gap ≤ kTouch at a tick sample — plane-only; no off-plane surface exists to ghost against |
| Interpenetration / slope law | F04: INT-01 trunk tangency worst |sdf−r_s| = 7.043e-16; INT-02 vertical-law slope submergence 3.6114e-6 ≤ 4.9906e-6 m legal bound; INT-03 trunk base coplanar at 0.0 exactly | Earth lane has `require(d>=-1e-10,…)` / `earth_ground_penetration`; gait lane has `gait_initial_penetration` (:2239) — plane-only |
| Friction | F04 consumed NO friction number (geometry only); F03 pinned `mat.bark.trunk_01` friction 0.6 as UNEVIDENCED-PLACEHOLDER, acquisition = G04 | ONE scalar `contact_friction` in [0,1] (`:2005`), scene value 0.6, uncited design constant (`admit_gait_walker_20260919.py:60`) |
| Blocking (routes) | F07: 641,494/641,494 free cells reachable; 107 blocked cells ALL cause B2 (trunk disk dist < 0.287 m = R 0.037 + body envelope 0.25); B1 = strict-`>` extent; zero unexplained | B1 has a native analogue ONLY in the earth demo lane (`:118`); the gait lane and membrane lane have no extent rule; B2 is Python-only |

**The falsifier-bearing statement:** every proof in the left column is STATIC. Not one of F04's 13 verdicts ran inside an engine process (F04 report, "Honest boundaries": "L1 only"). None of it counts as native playable collision readiness — that is exactly this card's falsifier, and this brief treats the static results as ORACLE + REFERENCE only.

---

## 4. Missing-interface enumeration (with units and transforms)

**M1 — Native terrain surface service.** No `h(x,z)` exists anywhere in C++. Needed: per-contact-point
`gap + world normal + tangent frame` from `terrain_bundle.json` (13,920 vertices / 3,200 ground triangles, frozen 00–11
cell diagonal, 1 m grid over [−20,20]²). Units: meters; gradient m/m; normal unit. Consumers: `gap_of` (`:642-643`),
`contact_row` (`:645`), `tangent_row` (`:646`), the reset seating (`:2239`).

**M2 — Native rigid-prop service (trunk).** No prop collision machinery at all. Needed: the analytic capped-cylinder
contract from `trunk_declaration.collision_representation` (containment, signed distance m, radial lateral normals,
cap normals (0,∓1,0)), surface IDs `trunk_01.lateral/base_cap/top_cap`.

**M3 — Multi-normal solver rows.** `contact_row` (`:645`) carries only the y-row; on any non-flat surface the normal row
is `Jᵀn` with `n = normalize(−gx, 1, −gz)` and the friction tangent rows (`:646`, world axes 0/2) must become the
surface tangent projection (t = normalize(v_tangential) or the gradient-perpendicular in the slope plane).
`friction_solve` (`:716`) already accepts arbitrary rows — but per F04's handoff this is a NAMED VERIFICATION DUTY:
verify (do not assume) that no other solver site assumes the plane normal (`project_rows` floors, the tier law,
`contact_bias`, the `plane[k]` persistent-contact flag at `:1727`).

**M4 — Collision query route.** No HTTP/in-process route serves height/normal/classify/SDF (§2.4 negative evidence).
Needed so the playable layer and the oracle harness can interrogate the engine's served answers (acceptance A3/A5).

**M5 — Extent rule in the walker lane.** `out_of_patch` strict-`>` exists only in the earth demo lane (`:118`); the gait
lane has no extent refusal. Needed: refuse/hold at |x| > 20 or |z| > 20 with the SAME strict-`>` semantics
(`classify` in `terrain_query.py:72`).

**M6 — Friction provenance.** The plane-lane mu=0.6 stays (it is the frozen walk's own constant). Trunk lateral friction
has NO measured value; Stage 1 must NOT claim grip. Acquisition = G04 (bark-on-appendage measurement).

**Units and transforms (the complete list):**

| Item | Law | Citation |
|---|---|---|
| Lengths | meters everywhere; NO unit conversion needed or permitted (bundle verts m, declaration m, contact points m, kTouch m) | F02/F03 declarations; `:56` ContactPoint |
| Model-frame shift | `plane_model_y_ = plane_world_y_ − shift_[1]`; a surface service must apply the SAME shift for gap-law answers while answering queries in the world frame | `gait_controller.hpp:2003` |
| Grid → world | 41×41 nodes at 1 m spacing, node (i,j) at (−20+i, −20+j); cell-local (tx,tz) ∈ [0,1]²; frozen diagonal: triangle A (00,01,11) covers tz ≥ tx, triangle B (00,11,10) covers tz ≤ tx | `terrain_query.py:84-121`; F02 prereg |
| Normal ↔ gradient | `n = normalize(−gx, 1, −gz)` ⇒ `gx = −nx/ny`, `gz = −nz/ny` | F02 prereg; engine normal law `graph_earth.hpp:100` |
| Placement transform | clearing world frame ↔ walker reset frame: identity by default (spawn [0,0,0]; walker scene `arm_translation_m [0,0,0]`, `world_id gait_walker_plane`); any nonzero placement must be a DECLARED constant, never inferred | `clearing_declaration.json` spawn; `gait_scene.py:467` |
| Time | ticks of 1/300 s, substeps 4 (both gait and earth lanes) | `:1961`; `earth_environment.hpp:91` |
| Speeds | v_max 1.01 m/s (`timing_paper.simulated_before`, derived_numbers.json @ a62b286e); per-tick travel s_tick = v_max·dt = 3.366667e-3 m; terrain-following vertical 1.681230e-4 m (slope law 0.05) | F04 frozen inputs |
| Contact scales | r_sole 0.004 m; kTouch 1e-5; release edge 1.1e-5; tangency tol 1e-9; trunk TOL 2e-4; F02 render/query family 1e-9 m / 1e-12 | `gait_scene.py:28`; `:36,:52`; F02/F03/F04 |
| Law-rest convention | zero-gap rest is `point_y = h(x,z) − r_sole` (sole center 4 mm BELOW the surface); naive tangency = `2*r_sole = 8e-3` — every render-vs-physics and envelope comparison must pick and label one convention | F04 GHO-02 adjudication; `:642-643` |

---

## 5. THE BRIEF — the smallest native integration

### 5.0 Scope decision (terrain-first, derived not tasted)

1. **The trunk needs a subsystem; the terrain needs a seam.** Trunk contact = M2 + M3 + a contact-mode concept
   (ground vs prop per point) + measured friction (M6) — none exists (§2.4). Terrain contact = replace ONE scalar
   (`:94`, `:2003`) and one row-builder (`:645-646`) with a per-point service, feeding machinery that already projects
   cones (`:683`), solves Coulomb friction (`:716`), bisects contact events (`:1950-1951`), and gates touch (`:1727`).
2. **The clearing is already walkable-around the trunk without trunk contact.** F07 proved the route layer with the
   trunk as the B2 blocking disk (0.287 m, 107 cells, zero unexplained). A first playable clearing — walk the floor,
   be stopped by the extent and by the trunk — requires terrain contact + the EXISTING blocking data, not prop contact.
3. **The plane path is the frozen control.** The co8 walk's byte anchors (302 / 30.970714 / 8c537cdb / f6844eea / c6f9b6c0)
   must keep re-verifying. A heightfield service introduced as the general case whose one-height degeneracy IS the plane
   keeps the plane path byte-identical by construction — and that byte-identity is itself a falsifier for "smallest delta"
   (acceptance A1).

### 5.1 Stage 1 (the first playable clearing): native terrain-heightfield contact in the gait lane

**Candidate files and symbols (all at 33e7a444 blob `5863348f…` unless noted):**

| # | Change | Exact anchor |
|---|---|---|
| S1-1 | Per-point surface service (new seam): `surface_query(x_m, z_m) → {h_m, gx, gz, inside}` fed from `terrain_bundle.json` (blob `f4be30e3…` @ dc7ea811); strict-`>` extent refusal mapped to the gait lane's refusal vocabulary | consumers: `gait_controller.hpp:94` (plane scalars → per-point), `:2003` (recipe height → bundle source + shift law retained), `:642-643` (gap law becomes `point_y + r − h(point_x, point_z)` pair-min), `:2239` (initial seating at `h(spawn)` law-rest) |
| S1-2 | Normal row from the surface: `contact_row` returns `Jᵀn`, `n = normalize(−gx, 1, −gz)`; `contact_row`/`tangent_row` (`:645-646`) generalize from the y-row/world-axes; `friction_solve` (`:716`) UNCHANGED | duty added by this brief: enumerated verification that no other site assumes (0,1,0) — `:683` floors, `:1724-1727` gate + `plane[k]` flag, `:647` `contact_bias`, `:2237` reset touching scan |
| S1-3 | Collision query route (new): POST route in the route chain beside `/gait_bin` | `main.cpp:1954` (route-chain pattern), served by S1-1's service; response `{h_m, gx, gz, inside, surface_rev}`; NO render changes |
| S1-4 | Render binding: upload `terrain_bundle.json` `render.vertices`/`render.indices` verbatim through the existing path; capture a frame | `engine.hpp:140` `load_mesh`; `main.cpp:764` upload pattern (`--earth-patch`); expected: ZERO `[load_mesh] normal hygiene: repaired` lines (`engine.cpp:1854-1937`) — F02 measured 0 broken / 0 deviant of 13,920 |
| S1-5 | Extent rule live in the walker lane: strict-`>` | semantics from `earth_environment.hpp:118`; oracle `terrain_query.py:72 classify` |
| S1-6 | Trunk in Stage 1 (NOT contact): render mesh uploaded (`trunk_declaration.json` 130 v / 384 idx, house 9-float layout — consumes unchanged via `engine.hpp:140`) + B2 blocking disk dist-to-axis < 0.287 m enforced on the native path plan | blocking derivation: F07 report table (R 0.037 + envelope 0.25); SDF verification only via the A3 route |

**I/O contracts (each with units):**

- `surface_query(x_m: double, z_m: double) → {h_m: double, gx: double, gz: double, inside: bool}` — world frame;
  `h_m` the containing triangle's plane value; `(gx, gz)` its exact plane gradient (m/m); `inside=false` iff
  `|x| > 20.0 or |z| > 20.0` (strict); the service refuses (`f02_outside_extent` analogue) rather than extrapolating —
  NO surface served past the patch (ghost-support law).
- Gap law (modified `gap_of`): `gap = min_over_pair( point_y + radius − h(point_x_world, point_z_world) )`, where the
  point's world position is the model position + `shift_` (inverse of the `:2003` transform); law-rest remains
  `point_y = h − r_sole`. The plane case `h ≡ contact_plane_height_m` must reproduce the current bytes EXACTLY.
- Query route: request `{x_m, z_m}` (or a batch array), response as above + `surface_rev` (bundle sha prefix) so a
  stale-surface mismatch is detectable; refusal code for out-of-patch probes.
- Trunk SDF (verification route, Stage 1): `{p} → {sdf_m, surface_id}` implementing
  `trunk_declaration.collision_representation.solid` — oracle `verify_contact.py:82 sdf_capped_cylinder(p, cx, cz, radius, y0, height)`.

**What Stage 1 deliberately does NOT contain:** trunk contact rows, grip/climb modes, non-(0,1,0) support claims,
post collision, bark friction, any change to `friction_solve`'s algebra, any second runtime.

### 5.2 Stage 2 (named follow-up, separately gated): trunk / rigid-prop contact

Honest sizing, per the card's method discipline: this is a SUBSYSTEM, not a patch —
(a) the analytic SDF service from `trunk_declaration.collision_representation` (M2);
(b) mixed-surface contact rows: a point's row switches between ground n and radial/cap n by SDF argmin (M3), with the
solver's per-point mode bookkeeping extended (`touching`/`plane` flags at `:1727`, `Rate::mode` at `:89`);
(c) tangential frames on the cylinder (radial normal ⇒ tangent plane spanned by axis ŷ and azimuthal t̂);
(d) the climb/contact-mode layer (U05's intent vocabulary exists; the CLIMB rows do not);
(e) measured bark-on-appendage friction replacing the 0.6 placeholder (G04 prerequisite, gating any grip claim);
(f) multi-surface support solve verification (the cone projection must be re-proven for mixed-normal active sets).
Gate: a separate preregistered engine task (frozen-core law) with its own Rule-0 falsifiers, AFTER Stage 1's acceptance.

### 5.3 The independent contact oracle (never trust the engine's own math)

| Oracle | File/symbol (blob @ dc7ea811) | Proven by | Agreement bar |
|---|---|---|---|
| Terrain height/gradient/normal/classify | `tools/monkey_campaign/data/monkey_clearing/terrain_query.py` — `TerrainSurface.height_at` (`:115`), `gradient_at` (`:122`), `normal_at` (`:130`), `classify` (`:72`), loader `load` (`:182`) | F02: 42/42; render==query 2.776e-17 m over 20,177 pts | ≤ 1e-9 m height, ≤ 1e-12 normal component (F02 frozen family), over the FROZEN ~21,700-point sample set |
| Trunk analytic SDF | `tools/monkey_campaign/agents/F04_contact/verify_contact.py` — `sdf_capped_cylinder(p, cx, cz, radius, y0, height)` (`:82`), `point_triangle_distance` (`:92`), `Model.gap_law` (`:157`) | F04: INT-01 tangency worst 7.043e-16; run.json sha `efded804…b70e6a`, two fresh-process runs byte-identical | ≤ 1e-9 m over INT-01's 320 lateral + 66 cap + 32 rim tangency probes |
| The gap law itself | `tools/science_funnel/gait_scene.py:178` `gaps.append(float(pos[1])+float(p['radius_m'])-plane)` (blob `5c8792ae…` @ 33e7a444) | it is the engine law's Python mirror, byte-anchored in the walk receipts | the modified native `gap_of` must reproduce the plane-lane bytes on the plane scene (A1) and match the oracle on the heightfield (A4) |
| Harness sensitivity controls | F04 TUN-02 (ridge-skip 4.329635 m step) and TUN-03b (0.083 m spacing > 0.082 m chord) | F04 measured both FIRING (the detector can miss) | must FIRE again in-vivo (a control that stops firing refutes the harness) |

Oracle discipline: the engine's served query answers are compared against these Python derivations; the engine is never
asked to grade itself. Every acceptance number below is a cross-check against an oracle, not a self-report.

### 5.4 Tunnelling and ghost-support falsifiers (frozen here, before any implementation)

- **F-TUN-1 (through-face, in-vivo):** a sole point swept at dt = 1/300 s, v = 1.01 m/s across any frozen terrain case
  (worst-slope centroid at (17,7); the five mound crests; the 45° approach through (19.5,5.5); the trunk-site cell)
  MUST be caught (min sampled gap ≤ kTouch) with first-catch penetration ≤ its derived per-tick bound
  (3.366667e-3 m vertical; 1.681230e-4 m terrain-following). A miss at declared tick/speed fires.
- **F-TUN-2 (boundary crossing):** a fast body crossing a shared triangle edge (or the worst twisted cell (36,28)) between
  ticks MUST be caught within the same bounds; edge-continuity |Δh| across 1,000 seeded crossings must obey the corrected
  linear-ratio bound (≤ 0.2 of 4×0.05 slope, F04's adjudicated form). A catch that requires sub-tick steps beyond dt/4
  (the existing bisection budget, `:30` "42-step event bisection") fires.
- **F-TUN-3 (controls must fire):** the ridge-skip control (4.329635 m sample step) and the chord-jump control
  (0.083 m spacing across the 0.082 m trunk catch chord) MUST report NOT caught. A control that stops firing refutes the
  harness (non-vacuity law).
- **F-GHO-1 (no surface from nowhere):** any served height/normal/SDF outside the closed extent (strict `>`), any support
  row armed with oracle-gap > kTouch, or any query answered past `f02_outside_extent` — fires.
- **F-GHO-2 (rest gains no support):** a body seated at law-rest on ANY surface point reports gap 0 (≤ 1e-15); raised by
  1e-4 m it must claim NO support (gap 1e-4 > kTouch); the :1727 gate must never arm while the ORACLE's gap > kTouch.
  A body at rest acquiring a contact row that the oracle denies fires.
- **F-GHO-3 (no ghost through the trunk):** the trunk void stays closed by the analytic contract — axis probes return
  sdf = −0.037 (inside), never a mesh-only positive reading (F04 GHO-03's declared split ≤ TOL 2e-4).

### 5.5 Runtime acceptance evidence (what must run in the ACTUAL engine, with numerical bars)

| # | Evidence (all in-vivo unless marked) | Numerical bar |
|---|---|---|
| A1 | Plane-lane byte-anchor regression: rebuild + re-run the co8 walk with the heightfield service present but fed the plane scene | refusal `302 gait_positional_correction_budget`; ledger exactly `30.970714 J`; stdout sha `8c537cdb…`; scene sha `f6844eea…`; trace `c6f9b6c0` (65,870 lines) — byte-identical, ZERO plane-path diffs |
| A2 | Terrain render binding: bundle uploaded via `engine.hpp:140 load_mesh` (`main.cpp:764` pattern), one frame captured | mesh 13,920 v / 4,640 tris accepted; posts' hexagons + two-tone checker visible; ZERO hygiene-gate repair lines (`engine.cpp:1854-1937`) |
| A3 | Engine-side query agreement vs the Python oracle (§5.3) over the frozen sample set, via the S1-3 route | worst height ≤ 1e-9 m; worst normal component ≤ 1e-12; trunk SDF route ≤ 1e-9 over the 418-probe tangency family |
| A4 | In-vivo terrain walk: the co8 walker seated at `h(0,0)=0.0` law-rest and stepped on the heightfield at dt=1/300 for ≥ 41 ticks (target the 213-tick cycle) | every F-TUN case caught within bounds; energy-ledger balance inside the pre-existing dual-gate bar (worst moving ledger ≤ 32.861605 J, wave-47 receipt's frozen gate); `gait_contact_localization` holds (located crossings |gap| < 1e-9 vs the ORACLE); slope submergence ≤ 4.990644e-6 m worst over 3,200 centroids |
| A5 | Out_of_patch live: walker driven to |x| = 20+ε (ε = 1e-9, 1e-6, 0.5) | strict-`>` refusal/hold each time; stopped AT the post ring, never inside it; inside at exactly 20.0 |
| A6 | Trunk blocking live: the native path plan consumes B2 | exactly 107 blocked cells (F07's number), zero unexplained blocks; spawn clearance 12.192185 m ≥ 1.5 m unchanged |
| A7 | Friction honesty | plane mu=0.6 unchanged and byte-anchored (A1); NO grip/climb claim anywhere in Stage 1 acceptance text; trunk friction recorded as UNEVIDENCED-PLACEHOLDER (G04) |
| A8 | Determinism | two fresh-process in-vivo runs byte-identical (runbook pattern); all receipts at pinned revisions with blob shas |

Stage-1 done-when: A1–A8 green with receipts, and every F-TUN/F-GHO falsifier un-fired (controls fired).

### 5.6 Explicit non-goals

- **No second runtime / no new engine.** Every change lands in the existing files at the anchors of §5.1.
- **No kinematic locomotion substitute.** The walk remains the GaitWalker's dynamics (touch law `:36/:52`, cone projection
  `:683`, Coulomb solve `:716`, event bisection `:1950`). A scripted/animated body gliding over the surface is NOT contact
  and would fail F-TUN/F-GHO by construction.
- **No trunk contact, grip or climb claim in Stage 1** (Stage 2 + G04 own it); **no post collision** (render-only markers,
  F04 VIS-03's NO-CLAIM — 0.2327 m envelope overlap is measured and declared, not enforced); **no deformable branches or
  bark damage** (F03's rigid-only closed vocabulary); **no friction evidence invention** (G04's measured acquisition).
- No C++ edits inside this diagnostic card; no GPU; no engine starts; the Stage-1 engine task itself must be
  coordinator-gated and preregistered before implementation.

### 5.7 Falsifier self-check (this card)

- **"A Python-only/static test counted as native playable collision"** — NOT COMMITTED: every acceptance row (A1–A8)
  requires an engine-process run or a byte-anchor; the F02/F03/F04 receipts are labeled static/L1 throughout §3 and used
  only as oracle/reference (§5.3). The report itself started no engine, and claims no native readiness.
- **"An implementation brief without a real source interface"** — NOT COMMITTED: every proposed change names an exact
  existing file + symbol + line at the pinned blob (`5863348f…` etc., §2/§5.1); no invented files, no paraphrased
  signatures (all quoted from `git show` output).
- **Drift honesty** — the f106fc54↔33e7a444 line-number drift in the wave-47 receipt is recorded (§2.5); this brief
  standardizes on 33e7a444 and says so wherever it cites.
- **Smallest-integration honesty** — the trunk is explicitly declared a Stage-2 SUBSYSTEM (§5.2) rather than smuggled
  into Stage 1; terrain-first is justified by three derived reasons (§5.0), not preference.

### 5.8 Remaining gates

1. Coordinator registration of the Stage-1 engine task (frozen-core law: this card specifies; it does not implement).
2. Rule-0 preregistration for the Stage-1 task, with §5.4's falsifiers as its starting set and §5.5's bars as its
   acceptance; S-1 validate (`port_test()` refuses a test with no falsifier).
3. G04: measured bark-on-appendage friction (prerequisite for any Stage-2 grip claim) + the multi-normal solver
   verification duty (§5.1 S1-2).
4. W10: the playable scene exercise (A2/A5 are its first slices).
5. W03's named residuals remain untouched by this brief (GPU legs, tick-40/41 contact-residual knife, Astra anchor A/B,
   clean-window C3) — A1's byte-anchors depend on them staying owned where they are.
6. The anchor-drift decision (reach-band v1 patch d19eb1c6→b643a850 changes constructed band-entry bytes) is W03's open
   item; Stage 1 must pin its diff target blob and re-verify A1 against whichever anchor the operator selects.
