# F04 Handoffs — what G01 and G04 consume from the contact verification

Author: M-F04. Date: 2026-09-24. The one suite to re-run:
`tools/monkey_campaign/agents/F04_contact/verify_contact.py` (stdlib-only, CPU,
headless; `python tools/monkey_campaign/agents/F04_contact/verify_contact.py` from
the repo root; receipts in `receipts/run.json` + `run.txt`, deterministic,
sha256 `efded8042d76f0879add4c278e7538ef0701bcb443086a16adc94b439eb70e6a`).
Case matrix: `PREREGISTRATION.md` (same dir). Full numbers: `report.md`.

## To G01 (support and grip feasibility; contracts C19, C20)

1. **Verified contact geometry (consume as data):** the trunk's lateral grasp band
   is exact — 320 tangency probes (64 azimuths x 5 heights) give
   `|sdf - r_sole| <= 7.05e-16 m`, caps and rim `<= 7.1e-16`; 4,096 seeded
   non-contact shell samples show zero penetration (min margin 2.30e-4 m); the
   render mesh is inscribed within the declared 1.78307e-4 m (VIS-02 recomputes it
   from the stored vertex table; tolerance 2e-4). Grasp points: exact radial
   normals, height bounds 0 <= y <= 1.158 m, surface id `trunk_01.lateral` only.
2. **The gap-law convention (do not mix conventions):** the engine's own law is
   `gap = point_y + r_sole - surface` (`gait_controller.hpp:635-643`;
   `gait_scene.py:178`), so its zero-gap REST is `point_y = surface - r_sole`
   (GHO-02 measured: rest gap 0 exactly at 5 probes). Naive sphere-CENTER tangency
   reads `gap = 2*r_sole = 8e-3 m` under this law. Your support/wrench math must
   pick and LABEL one convention (the engine's law vs geometric tangency) — the
   divergence is one-sided (the law claims contact LATER than naive geometry,
   never earlier), so mixing them cannot create phantom support, but it will shift
   every envelope by 2*r_sole.
3. **Slope submergence (F05 consumes too):** the engine's vertical gap law on a
   sloped triangle submerges the geometric sphere by `r_sole*(1 - n_y)`:
   measured worst 3.6114e-6 m at the worst triangle (slope 0.042522), derived
   legal bound 4.9906e-6 m at F01's 0.05 slope law. Inside your static envelope
   math on slopes, this is the declared contact-penetration allowance.
4. **Ground joint (INT-03):** trunk base cap vs terrain is watertight at the site —
   65 cap-disk samples and an 81-point footprint grid all measure terrain height
   exactly 0.0, gradient (0,0): coplanar contact, zero gap, zero penetration.
   The trunk is a rigid extension of the ground plane at this site.
5. **Friction: NOTHING changed.** The suite consumed NO friction number
   (geometry-only). `mat.bark.trunk_01` friction stays 0.6
   UNEVIDENCED-PLACEHOLDER with acquisition prerequisite G04. Provisional
   envelopes only, per F03's handoff.

## To G04 (physical grip contact; contract C08) — the L2 engine-service gap

**What the frozen engine exercises today (cited):** point spheres vs ONE ground
plane, nothing else.
- `gait_controller.hpp:94` — ONE plane scalar for ALL contact points
  (`plane_world_y_`, `plane_model_y_`, `mu_`).
- `gait_controller.hpp:635-643` — `gap_of` = point_y + radius - plane_model_y_
  (vertical law, single plane).
- `gait_controller.hpp:36,52` — touch band kTouch=1e-5, kSlip=1e-9,
  kReleaseBand=1e-6.
- `gait_controller.hpp:645` — `contact_row` takes ONLY the plane's y-row: every
  contact normal in the solver is (0,1,0).
- `gait_controller.hpp:716` — `friction_solve` (discrete-cone Coulomb) — takes
  arbitrary row_n/row_t but is only ever fed the plane rows.
- `gait_controller.hpp:1727` — engagement gate (gap <= kTouch AND inward speed
  <= 1e-6 + 1e-3*joint_speed_scale).
- `gait_controller.hpp:1961` — dt <= 1/300 s, substeps == 4.
- `gait_controller.hpp:2005-2010` — recipe: ONE `contact_plane_height_m`,
  `contact_friction` in [0,1], contact points `radius_m > 0`, capacity 1..8.
- `earth_environment.hpp:67,110,118` — the earth lane: ONE body sphere vs one
  plane; `out_of_patch` strict-> (|x|>half || |z|>half).
- `graph_earth.hpp:26-30,82,100` — meshes (9-float pos+normal+color,
  cross(b-a,c-a) normals) are RENDER-only; upload via `engine.load_mesh`
  (`main.cpp:736,751,764`). The route chain contains NO collision query route
  (F03 discovery_note.md §2).

**What F04's cases therefore CANNOT be exercised in-vivo (all verified L1-only,
Python vs the declared geometric model):** terrain-heightfield contact (the gait
plane is ONE height; F01/F02's mounds and slopes have no native consumer — even
the TERRAIN is beyond the current walker contact model); ALL trunk contact (no
prop/rigid-prop collision machinery exists); multi-surface support (ground+trunk
needs contact rows with non-(0,1,0) normals); any continuous-collision detection
(the kTouch band at tick samples is the only anti-tunnelling machinery, plane-only).

**What G04 needs (a preregistered, separately-gated ENGINE task — frozen-core law:
this is a recorded gap, not an agent-file edit; no C++ was touched in F04):**
1. A per-contact-point SURFACE service: gap + world normal + tangent frame from
   (a) F02's terrain query (containing triangle's plane + normal) and (b) F03's
   analytic cylinder contract (`trunk_declaration.collision_representation`:
   containment, signed distance, radial lateral normals, cap normals) — replacing
   the single `plane_model_y_` (gait_controller.hpp:94) and the y-row-only
   `contact_row` (gait_controller.hpp:645).
2. Multi-normal contact rows fed to the EXISTING `friction_solve` (716) — the
   solve already accepts arbitrary row_n/row_t; G04 must verify (not assume) that
   nothing else in the solver assumes the plane normal.
3. A collision-query route (or in-process service) in the HTTP contract so gait
   ticks consume `terrain_bundle.json` + `trunk_declaration.json` — no such route
   exists today.
4. The measured bark-on-appendage friction coefficient (the declared G04
   prerequisite; placeholder 0.6 is unevidenced).
5. In-vivo demonstrations owed to C08's verification clause: impact/sliding/
   resting controls on the SLOPED terrain, trunk-contact reaction accounting, and
   the tunnelling cases re-run through the real tick loop (F04's L1 margins to
   hold: trunk chord 24.4x, vertical catch band 23.8x at the declared speed/tick).

## Open debts recorded (not silently dropped)

- In-vivo (engine) exercise of every L1 case — blocked by the gap above; W10's
  walking demo still runs the PLANE lane.
- Measured bark friction — G04 prerequisite (declared in the trunk artifact).
- The walker's visual mesh vs the contact points: the law's rest puts sole points
  4 mm BELOW the surface (GHO-02 convention note) — any render-vs-physics
  comparison must account for this declared offset (2*r_sole = 8 mm from naive
  tangency).
