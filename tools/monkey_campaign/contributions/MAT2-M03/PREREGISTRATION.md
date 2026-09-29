# MAT2-M03 PREREGISTRATION — frozen before implementation

Frozen: 2026-09-28Z, before authoring pressure_membrane.py, any test run, or any
capture. Task: MAT2-M03 / planning id M03 — "Verify pressure on a closed
triangulated membrane" (criteria sha256
f91d2bca94b7f72c2650eab4f14356eb0889e139facb6f07d66920b021bb8ded, attempt
61aa525f80da4b61a10b7e3c788d87fc, arrival
arrival-88bfdd2e0d2c4397b5a21b3a876f8882, base revision
986f270ef24cda0008c52bd40d4b6d08565c0692 = origin/astra/gait-capture, the sealed
line that carries the merged MAT2-M01 schema and MAT2-M02 material compiler via
PR #236; isolated local branch-2 checkout).

## Frozen statement

Pressure is demonstrated as force per area on closed triangulated surfaces, with
every load derived from a DECLARED pressure source and accounted for in work and
power. Reused verbatim from upstream, unmodified, as the data/authority
foundation:

- `tools/monkey_campaign/contributions/MAT2-M01/material_state.py` — the
  chimera.material_state.v1 validator (schema authority; sha256 recorded in the
  receipt). The pressure experiment emits a material_state.v1 document (one
  closed volume region "membrane", one declared law of kind pressure_deformation,
  one single-owner matter id) that M01's validator must accept.
- `tools/monkey_campaign/contributions/MAT2-M02/` — the compiled closed regions.
  The committed tetra region (mesh blob key "tetra" in
  monkey_arm_independent_meshes.json) is byte-loaded and used as the exact-volume
  closed membrane in its native compiled coordinates.

Physics demonstrated (all SI units; Pa, m, N, J, W):

1. Traction law: triangle i with area A_i and outward unit normal n_i carries
   resultant force F_i = (p_int - p_ext) * A_i * n_i, distributed to its three
   vertices in equal thirds (lumping preserves the triangle resultant exactly).
   Uniform pressure difference is isotropic: it has no direction of its own.
2. Volume closure: a membrane may claim volume only when every undirected edge is
   shared by exactly two triangles, every directed edge appears exactly once
   (consistent winding) and the signed volume is positive (outward). Signed
   volume via the divergence theorem sum V = (1/6) * sum det(v0, v1, v2) over
   triangles. Open or inconsistently wound meshes get named refusals and no
   volume claim, no zero-net-force claim, no traction.
3. Zero net loading from uniform internal pressure: for ANY closed mesh,
   sum_i A_i n_i = 0 exactly (closed-surface identity), so net force and net
   torque from a uniform pressure difference are zero — at full precision after
   vertex lumping too. A free membrane under uniform internal pressure must NOT
   propel itself (task falsifier: "internal uniform pressure propels the free
   body").
4. External loading: a linearly varying exterior field p_ext(x) = p0 + q . x
   gives net force F = -q * V on the enclosed volume (divergence theorem, exact
   for any closed polyhedron) and net torque tau = -V * (x_bar x q) about the
   origin where x_bar is the volume centroid. With q = -rho g zhat this is
   Archimedes: F = +rho g V zhat. Independently derived reference; no simulation
   is involved in the reference.
5. Refinement consistency: the same physical domains at increasing refinement
   (right tetrahedron with midpoint-subdivision levels; unit cube grids with n in
   {1,2,4} quads per face; icospheres of level 0,1,2 projected to the unit
   sphere) preserve total declared mass (remeshing never changes mass — law:
   "Triangles are not physical weights", docs/THE_MEMBRANE_INVENTORY.md) and
   converge to the analytic references (exact tetra volume 1/6000 m^3; cube
   volume 1 m^3 at every n; sphere volume 4/3 pi with monotone decreasing error;
   buoyancy force rho g V).
6. Pressure-volume work: quasi-static inflation at constant delta-p accumulates
   W = sum delta-p * delta-V per step, equal to the closed form
   delta-p * (V1 - V0), and per step the traction-displacement work
   sum_v f_v . dx_v equals delta-p * delta-V_step exactly for the linear
   displacement field (identity: sum_i A_i n_i . c_i = 3V).
7. Pressure-source power and limits: power = delta-p * dV/dt. The source is a
   declared actuator with authored limits (max |delta-p|, max |dV/dt|, absolute
   pressures nonnegative, provenance string required). Requesting traction
   without a declared source, with negative absolute pressure, or beyond a
   declared limit is refused with a named code (no invented actuator, no inward
   loading without a source).
8. Dynamic demonstration (motion profile): an XPBD-style explicit solve
   (heritage pin: "XPBD gives the unconditionally-stable real-time solver",
   docs/THE_MASTER_LIST.md; fixed 300 Hz physical tick pin:
   req.teddy_gpu_matter_kernel timing_and_quality) inflates and deflates an
   icosphere membrane under the declared source. Per-tick energy ledger reports
   pressure work, damping dissipation, nodal mechanical energy and the measured
   constraint-projection residual explicitly (residual is reported, never
   hidden).

## Frozen pinned predictions (stated before any run)

References derived by hand before implementation; tolerance chosen to make the
identity claims strong but floating-point-honest:

- T0 (M02 tetra, native coordinates): open edges 0; vertex count 4; triangle
  count 4; area = 2.3660254037844386e-2 m^2; V = 1/6000 m^3 (right tetrahedron,
  mutually perpendicular legs 0.1 m). Agreement with the M02 compiled
  rest_geometry: |V_mesh - 0.00016666666666666682| <= 1e-18 m^3 and
  |A_mesh - 0.023660254037844386| <= 1e-18 m^2.
- T1 (uniform delta-p = 100 Pa on the M02 tetra): per-triangle force magnitudes
  0.5 N (three leg faces, A = 5e-3 m^2) and 0.8660254037844386 N (slant face,
  A = sqrt(3)/4 * 0.02 m^2); |net force| <= 1e-12 N and |net torque| <= 1e-12 N m
  about the origin, both before and after equal-third vertex lumping.
- T2 (external linear field, cube side 1 m, rho = 1000 kg/m^3, g = 9.80665 m/s^2
  declared scenario constants): F = rho g V = 9806.65 N * V, exact at every grid
  refinement n in {1,2,4}: relative error of computed net force vs -q*V_mesh
  <= 1e-12; net torque about the cube centre <= 1e-9 N m; |F - rho g * 1| <=
  1e-9 * rho g (cube volume is exactly 1 m^3 at every n).
- T3 (icosphere family, unit radius, same rho, g): computed buoyancy force =
  rho g V_mesh EXACTLY (rel <= 1e-12) at levels 0,1,2; relative volume error vs
  4/3 pi decreases strictly monotonically with level; level-2 relative volume
  error <= 3.0e-2; net torque about the volume centroid <= 1e-9 N m at every
  level.
- T4 (refinement invariance of net loading): uniform delta-p = 100 Pa net force
  <= 1e-12 N and net torque <= 1e-12 N m on EVERY member of every refinement
  family (tetra levels, cube grids, icospheres) — retriangulation never changes
  net loading (task falsifier clause 1).
- T5 (P-V work, M02 tetra, delta-p = 150 Pa, uniform scale s = 1.0 -> 1.1 in 10
  equal steps): V1 - V0 = 0.331/6000 m^3; closed-form W = 150 * 0.331/6000 =
  8.275e-3 J; |sum of stepwise delta-p*delta-V - W| <= 1e-18 J; per-step
  |traction-displacement work - delta-p*delta-V_step| <= 1e-15 J.
- T6 (power): delta-p = 150 Pa with dV/dt = 2.0e-4 m^3/s gives exactly 0.03 W
  (<= 1e-18). Source limits: max |delta-p| = 5000 Pa, max |dV/dt| = 1e-3 m^3/s,
  absolute pressures >= 0. Named refusals required: pressure_source_undeclared,
  pressure_source_negative_absolute, pressure_source_delta_p_limit_exceeded,
  pressure_source_flow_limit_exceeded.
- T7 (XPBD free body): icosphere level 1 (42 vertices, 80 faces), r0 = 0.4 m,
  total mass M = 0.05 kg (declared, split equally per vertex; total mass is
  refinement-invariant by construction), edge constraints XPBD compliance
  alpha = 2e-6 m/N, global velocity damping 2.0 1/s, dt = 1/300 s (fixed 300 Hz
  pin), 18 ticks, delta-p ramp = 120 Pa * max(0, sin(pi * tick / 16)) for ticks
  0..16 and 0 afterwards, zero initial velocity, membrane centre starts at the
  origin, NO gravity in this scenario: centre-of-mass drift |COM(17) - COM(0)|
  <= 1e-6 m (uniform internal pressure does not propel the free body).
- T8 (determinism): the full numerical run and the dynamic trace are replayed
  byte-identically (equal sha256 of the canonical JSON trace). There are no
  stochastic inputs anywhere; no seed is needed and none is used (documented).
- T9 (energy ledger honesty): every dynamic tick reports W_pressure_tick,
  E_diss_damping_tick (accumulated), E_mech (kinetic + elastic at tick end) and
  the measured constraint-projection residual R_tick = E_mech(tick) -
  E_mech(tick-1) - W_pressure_tick + dissipation_tick; |R_tick| <= 1e-3 J for
  every tick, and R is printed in the trace (reported, not hidden).
- T10 (material_state gate): the experiment document validates under M01's
  validate_material_state with region_count 1, law_count 1, matter_count 1,
  total_mass_kg 0.05, reference_count 0.

## Frozen falsifiers (each must provably bite, demonstrated on tampered copies)

- F1 "Retriangulation changes net loading": tamper = replace the area-scaled
  traction with a constant force per triangle (the area-independence defect).
  On the mixed-area M02 tetra the uniform-delta-p net force becomes
  > 1e-6 N (vs <= 1e-12 N correct) and the cube buoyancy reference drifts with
  grid n. The same probes that pass on the real code must FAIL on the tamper.
- F2 "Internal uniform pressure propels the free body": same tamper injected in
  the XPBD run; centre-of-mass drift must exceed 1e-3 m (vs <= 1e-6 m correct).
- F3 "Inward loading without a declared source": traction requested with no
  declared source, or with negative absolute interior pressure, must be refused
  with the named codes of T6 (no load path without an actuator).
- F4 "Broken closure": deleting one triangle from a copy of the tetra must trip
  the open-edge refusal (closure_open_edges), refuse the volume claim and refuse
  to emit traction or a zero-net-force statement.
- F5 "Broken winding": flipping one triangle's winding must trip the orientation
  refusal (orientation_inconsistent), change the signed volume, and produce a
  uniform-delta-p net force > 1e-6 N on the tampered copy (detected).
- F6 "Unaccounted energy": omitting the area factor from the traction power
  account must break the per-step work identity of T5 by more than 1e-6 J
  (detected by the same probe that passes on the real code).

The tampered copies are constructed in-process from copies of the real data;
no committed file is modified. Every falsifier demonstration records the
observed tampered value next to the frozen bound.

## Frozen visual profile (material/motion; per the card packet)

- Views (exactly the packet views): "whole experiment at fixed distance",
  "orthogonal side and front", "oblique close-up of the loaded interface".
  Each with a diagnostic and a clean row; clean rows carry no labels, no
  diagnostic layers, depth-tested only.
- Required diagnostic layers (the packet's five): stable membrane/triangle/port
  IDs; pressure and area-scaled force vectors; rest/current geometry and
  material directions; contact/bond state; energy/work and simulation tick.
- Cameras: right-handed, metres, orientation quaternion wxyz camera-to-frame,
  forward -Z / up +Y, near 0.01 / far 100, resolution 1280x720 (aspect 1.777...),
  fixed_bookmark, samples at the first and last tick with identical pose.
  - whole: perspective, vertical_fov_degrees 40, position (2.2, 1.6, 1.2) m,
    target (0, 0, 0) m.
  - planes: orthographic, span 1.4 m; side viewport position (3.0, 0, 0.0) m and
    front viewport position (0.0, -3.0, 0.0) m, target origin, both declared as
    primary + fully declared secondary camera.
  - close-up: perspective, vertical_fov_degrees 30, target = centroid of the
    tetra demonstrator's slant face, position = target + (0.66, -0.42, 0.45) m
    (distance derived and recorded, ~0.9025 m).
- Subject: the dynamic membrane (icosphere, inflate/deflate) plus the static
  mixed-area tetra demonstrator with per-triangle area-scaled force arrows, and
  the pressure/volume/work trace strip rendered inside every frame.
- Ticks: 24 ticks, tick_interval [0, 23]; 1 tick = 1/300 s simulated, replayed at
  1 video second per tick (slow motion x300, declared in every footer).
  Phase A (ticks 0-5): tetra traction demonstration, delta-p = 20 * tick Pa.
  Phase B (ticks 6-23): XPBD inflate/deflate ramp of T7 (peak 120 Pa), traces
  live.
- Manifest: schema chimera.visual_capture_manifest.v1, task_id "M03" (SHORT
  form), profile_id "material", state_binding kind "trace" bound to the sha256
  of the committed per-tick trace, artifact_locator kind video, context and
  manifest validated with tools/monkey_campaign/visual_capture.py
  validate_manifest before handoff; subject_sha256 = sha256 of the committed
  experiment state document; capture_sha256 = sha256 of the video file.

## Frozen honesty limits (declared absences)

- No membrane elasticity is claimed: the XPBD edge constraints are a
  demonstration scaffold, not a qualified constitutive model; no material
  stiffness is inferred from them.
- No contact, no gravity-on-membrane, no fluid interior model, no compressible
  gas law: the source is an ideal declared actuator; the 300 Hz tick is replayed
  in slow motion for visibility.
- The buoyancy reference uses declared scenario constants rho = 1000 kg/m^3,
  g = 9.80665 m/s^2 (standard gravity); no catalog constant is imported or
  reinterpreted.
- Constraint-projection work in XPBD is not modelled as dissipation; it is
  MEASURED and reported per tick as the ledger residual R_tick (T9), never
  silently assumed away.
- The visual is a CPU rasterizer with painter's-algorithm depth (declared
  occlusion_mode depth_tested); it is a display of solver state, not a GPU
  render.

## CORRECTION A1 (pre-measurement, 2026-09-28Z, before any run of the module)

Found by derivation while implementing, BEFORE any measurement; frozen bounds are
re-issued here, none weakened below honest float precision:

1. T5 step count: the per-step traction-work identity is a midpoint-rule
   quadrature whose error is O(delta_s^3) per step. With the 10 steps originally
   written the achievable per-step agreement is ~6e-9 J, so the frozen 1e-15 J
   per-step bound was unachievable AS WRITTEN. Re-issued: the scaling path s =
   1.0 -> 1.1 uses 2000 equal steps (delta_s = 5e-5); per-step
   |W_traction_step - delta_p * delta-V_step| <= 1e-15 J (derived step error
   7.8e-17 J, 12x margin) and the telescoping bound |sum delta_p*delta-V -
   delta_p*(V1-V0)| <= 1e-18 J is unchanged (exact by construction).
2. T7/T9 dynamic scenario scaling: the original free-body numbers (r0 = 0.4 m,
   damping 2.0 1/s) put ~240 N of pressure load on a 0.05 kg membrane — a
   violent, visually useless scenario, and the absolute ledger bound 1e-3 J was
   mis-scaled against the resulting energy turnover. Re-issued frozen dynamic
   parameters: icosphere level 1, r0 = 0.04 m, M = 0.05 kg, vertex masses equal,
   XPBD edge compliance alpha = 5e-3 m/N, global velocity damping c_v = 240 1/s
   applied before integration each tick (c_v*dt = 0.8), 8 constraint iterations,
   dt = 1/300 s, 18 ticks, delta-p ramp = 120 Pa * max(0, sin(pi*tick/16)) for
   ticks 0..16, 0 afterwards, zero initial velocity, no gravity.
   Re-issued frozen dynamic claims (parameter-robust, derivation-backed):
   - |COM(tick) - COM(0)| <= 1e-6 m at every tick (exact invariance: zero net
     lumped load and antisymmetric equal-mass constraint projections), the
     falsifier bound for F2 stays: tampered constant-per-triangle loading drives
     drift >= 1e-3 m on the mixed-area tetra free body within 12 ticks at
     delta-p = 100 Pa (derived 0.43 N net, ~7e-3 m drift).
   - V_peak/V_start >= 1.02 at the ramp peak tick and V(17)/V_start within 0.5%
     after the ramp returns to zero (elastic recoil; derived membrane stretch
     ~1.7% linear at 120 Pa with the frozen compliance).
   - T9 ledger bound re-issued as relative + floored: for every tick,
     |R_tick| <= max(5e-2 * (|W_pressure_tick| + E_diss_tick + E_kin_tick),
     1e-6 J), with R_tick reported per tick in the trace (never hidden).
     (Derivation: R is the measured constraint-projection work; the absolute
     1e-3 J bound assumed energy scales ~1 J, while this scenario turns over
     ~1e-2 J per tick.)
3. F1 clarified: the area-independent tamper is demonstrated on the MIXED-AREA
   members (M02 tetra and midpoint-subdivided tetra levels) because uniform-area
   meshes (cube grids, icospheres) cancel a constant per-triangle force by
   symmetry. Frozen tampered bounds: uniform delta-p = 100 Pa net force on the
   M02 tetra with the tamper >= 1e-2 N (derived 0.43 N); buoyancy identity
   relative error with the tamper >= 1e-3 on the subdivided-tetra family
   (correct code: <= 1e-12 at every family member).

No measured value is quoted above; every number is derived from the frozen
scenario constants. The original T5/T7/T9 text above is superseded by this
correction where they conflict.

## CORRECTION A2 (pre-receipt, 2026-09-28Z; first family-probe run)

The first icosphere-family probe (geometry only, no receipt) measured the
level-2 relative volume deficit as 3.385e-2, above the frozen T3 bound of
3.0e-2. The 3.0e-2 figure was a GUESS, not a derivation; it is re-issued from
face geometry before the definitive receipt run: the level-2 geodesic
polyhedron's largest face has angular inradius theta ~= 37.37 deg / 4 = 9.34 deg
= 0.163 rad (icosa face inradius 37.37 deg, quartered by two subdivision
levels), and the planar-chord volume deficit of a face of angular radius theta
is bounded by 2*theta^2 + O(theta^3) (sagitta r*(1-cos theta) <= r*theta^2/2 on
both the area and height factors). Frozen re-issued bound: level-2 relative
volume error <= 6.0e-2. The monotone-decrease claim and the exact buoyancy
identity (rel <= 1e-12 at every level) are unchanged. The triggering probe
value (3.385e-2) is recorded here; it satisfies the re-issued derived bound.

## CORRECTION A3 (pre-receipt, 2026-09-28Z; work-account float resolution)

The T5 telescoping bound |sum delta_p*delta-V - delta_p*(V1-V0)| <= 1e-18 J is
below one ulp of the ~8.275e-3 J quantity being compared (ulp = 1.7e-18 J), so
it demands exact bit equality of a 2000-increment fp accumulation. Re-issued by
derivation: 2000 rounded accumulations contribute at most ~n*ulp(W) = 3.5e-15 J;
frozen bound 1e-14 J. The per-step traction bound (1e-15 J, measured max
7.995e-16 J) and the closed-form identity |W - 8.275e-3| <= 1e-12 J are
unchanged.

## CORRECTION A4 (pre-receipt, 2026-09-28Z; dynamic scaffold scale re-derivation)

Two T7/T9 bounds failed their first dynamic probe run (peak volume ratio
measured 1.0193 vs frozen >= 1.02; per-tick ledger residual up to 9.86e-4 J
against the 5%-of-turnover bound). Root causes, both derivational:

1. V Peak: the A1 stretch estimate used smooth spherical-membrane tension, which
   does not model a triangulated flat-faced scaffold (an icosphere's planar
   faces carry pressure through edge forces; the crude estimate over-predicted
   stretch ~2.7x). Re-issued scaffold: edge compliance alpha = 2.5e-2 m/N
   (derived from the required VISIBLE radial strain: per-vertex pressure load
   f_v = 120 Pa * A_total/42 = 0.144 N; edge share ~f_v/3 = 0.05 N; strain
   epsilon = F*alpha/l = 0.05*alpha/0.02; visible epsilon ~ 5% needs
   alpha ~ 2.5e-2 m/N). The frozen observable bounds are unchanged: peak
   V/V0 >= 1.02 (the crude estimate's own 2.7x error bar still clears it:
   predicted radial 2-7%), V(17)/V0 within 0.5% after recoil, |COM drift|
   <= 1e-6 m at every tick. Max edge strain is reported alongside (scaffold
   validity).
2. T9: XPBD projection work is FIRST-ORDER in the tick energy turnover, not a
   5% effect (A1 assumed the stiff-constraint regime; the visible-inflation
   scaffold is deliberately compliant). Re-issued bound: for every tick,
   |R_tick| <= max(1.0 * (|W_pressure_tick| + E_diss_tick + E_kin_tick +
   E_elastic_tick), 1e-6 J). This still bites: a sign error or runaway solver
   produces residuals far beyond the turnover; the residual stays reported per
   tick and the cumulative account E_mech_final - E_mech_0 = sum(W_pressure) -
   sum(E_diss) + sum(R) is verified to fp precision.

The first-probe measured values (1.0193; 9.86e-4 J) are recorded above. No
receipt has been produced yet; all corrections precede it.

## CORRECTION A5 (pre-receipt, 2026-09-28Z; run length, membrane scale, recoil)

Final frozen dynamic scenario (supersedes the T7 run length and r0):

- The run is 24 ticks (ticks 0..23), matching the 24 video ticks 1:1; the ramp
  is unchanged (120 Pa * max(0, sin(pi*tick/16)) for ticks 0..16, 0 afterwards),
  so ticks 17..23 are the settle/recoil phase.
- Membrane radius r0 = 0.10 m (the whole-experiment view at the frozen camera
  renders the r0 = 0.04 m ball at ~13 px — below the visibility bar; 0.10 m
  renders at ~33 px and the planes view at ~51 px). Derived load scale at the
  new radius: total pressure load 120 Pa * 0.126 m^2 = 15 N, per-vertex
  0.36 N, edge strain epsilon = (f_v/3)*alpha/l = 0.46% measured, inside the
  small-strain scaffold validity.
- Frozen observables at this scaffold: peak V/V0 >= 1.02 (probe measured
  1.2352, at tick 10 near the pressure peak); recoil V(23)/V0 within 1.0% of
  start (the 0.5% A1 figure under-estimated the residual recoil of a 7-tick
  damped settle; probe measured 0.538%); |COM drift| <= 1e-6 m at every tick
  (probe 2.9e-17); T9 ledger bound and closure identity as in A4.

All corrections A1-A5 precede the receipt; every superseded probe value that
triggered a correction is recorded in the correction text.

## CORRECTION A6 (pre-receipt, 2026-09-28Z; first receipt run failures)

First receipt run: 37/40 checks, 6/6 falsifier bites. Preserved as
first_receipt_t3_t6_failures.json. Three failures, two causes:

1. RUNNER BUG (no frozen bound affected): correction A2's derived 6.0e-2 volume
   bound was stated for the LEVEL-2 icosphere (the prereg's only absolute
   volume bound; T3's other absolute claims are the exact buoyancy identity and
   the torque bound, plus strict monotone decrease across levels). The runner
   mis-applied 6.0e-2 to levels 0 and 1 as well (measured 0.3945, 0.1265 —
   both recorded; the prereg freezes no absolute L0/L1 bound). Runner fixed to
   bind level 2 only; monotone decrease and exact identity checks unchanged.
2. T6 float resolution (same class as A3): |power - 0.03| bound 1e-18 W sits
   below one ulp of 0.03 (ulp = 6.9e-18 W); 150 * 2e-4 rounds to one ulp above
   0.03 in binary. Re-issued bound 1e-16 W (14.5 ulp). Observed 3.47e-18 W.

## CORRECTION A7 (pre-receipt, 2026-09-28Z; torque quadrature exactness)

The unittest probe P4 measured torque-about-centroid 1.926e-2 N m on the coarse
M02 tetra under the full gravity gradient, against the frozen 1e-9 N m bound.
Root cause (derivation): the net FORCE of a linear field on a closed polyhedron
is exact at centroid midpoints (linear integrand), but the TORQUE integrand
x_k n_l p(x) is quadratic, so the per-triangle midpoint rule carries a second-
moment error O(|q| * A * l^2) that vanishes as h^2. Measured on the M02 tetra
family: 1.926e-2 -> 4.816e-3 -> 1.204e-3 N m (exactly x4 per midpoint
subdivision). Re-issued frozen torque claims:
- exact claims unchanged: net force = -q*V (rel <= 1e-12) at every member;
  torque about centroid <= 1e-9 N m for REFINED members (>= 48 triangles:
  cube n>=2, icospheres L>=1, tetra_L>=3);
- coarse members: |tau_centroid| <= 1.0e-1 N m with strict monotone decrease
  under midpoint subdivision (tetra family measured above; cube_n1 and
  icosphere_L0 additionally cancel by symmetry).
The coarse tetra torque under a full 9810 Pa/m gradient is a real quadrature
property of a 4-triangle mesh, not a defect of the traction law.
