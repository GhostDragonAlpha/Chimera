# MAT2-M10 PREREGISTRATION — frozen before implementation and before any measurement

Frozen: 2026-09-29Z, before authoring actuator_world.py, run_experiments.py,
test_actuator_world.py, render_run.py, make_capture.py, make_report.py,
lint_report_numbers.py, before any experiment run, any falsifier arm, any
capture code or frame, and before any GPU/mailbox submission. Task: MAT2-M10 /
planning id M10 — "Demonstrate active pressurized material with directional
reinforcement" (criteria sha256
5e7560caa9efae9ec819c9127ab6ee6e7016e134bdf97e525f06cfedee31190c, attempt
02cc9dbda6f3494f8d8de36e20b94c0f, arrival
arrival-5c71030b5a614f89ac0716c1d99bfa0d).

done_when (verbatim): "A pressure-controlled membrane with authored directional
resistance performs bounded work through actual attachments. Measure
force-displacement/work against independent expectations, blocked-load
reaction, pressure limits and power-off behavior. Classify it as an engineering
actuator unless biological equivalence is independently evidenced."

Card task falsifier (verbatim, registry spec.falsifier + ontology task):
"Activation writes body poses, contraction is claimed from isotropic inflation
alone, or work has no source."

Verification-profile falsifier (verbatim): "Unbound media, clipped load path,
hidden constraint/support, area-independent triangle forces, overlay-driven
motion, or unaccounted energy prevents acceptance."

Port contract (verbatim): "Bounded activation/pressure command + energy supply
-> distributed surface/tissue loads, observed strain and power."

Registry profile note (P7): the verification profile is read READ-ONLY from
E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
kanban.cards[MAT2-M10].spec.ontology_qualification.task.verification_profile
(id "material", kind "motion", clean_view_required true,
numerical_evidence_required true, 5 diagnostic layers, 3 views, 16
camera_required_fields). The dispatch brief's phrase "17-field camera record"
enumerates exactly those 16 registry fields (counted: frame_id,
coordinate_unit, position, orientation_convention_and_values, target,
distance_to_target, projection, vertical_fov_or_orthographic_span,
near_far_planes, aspect_ratio, viewport_resolution,
camera_motion_or_bookmark_sequence, visibility_layers, label_ids,
occlusion_or_xray_mode, state_or_tick_interval); the registry row is the
authority and the capture carries all 16 on every camera record.

## Base and dependency pins (verified before this freeze)

- Attempt branch branch-2 fast-forwarded (ancestor check performed:
  c525b82c7c3ce0128565424764293a3c85811ab3 = origin/branch-2 prepared head IS
  an ancestor) to the sealed-line tip
  b3490ecda8265468fea7e4a28a76fa7cc44a3cb8 = merge of PR #267 (MAT2-M08
  winner), which carries the merged winners of declared dependencies MAT2-M03,
  MAT2-M04, MAT2-M05 and MAT2-M08 (and transitively M01/M02/M06/M07).
- Isolated attempt checkout (worktree of E:/PythonChimera) at
  E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-M10/
  02cc9dbda6f3494f8d8de36e20b94c0f/checkout. The parent checkout's dirty
  state is untouched; M09 (branch-1 lane) runs in parallel and is not touched.
- Frozen input pins (sha256 re-verified at run time; mismatch refuses
  `input_pin_drift`):
  - MAT2-M01/material_state.py (schema authority, validator used UNMODIFIED),
  - MAT2-M03/pressure_membrane.py (Membrane, PressureSource, meshes,
    linear-field references; used UNMODIFIED),
  - MAT2-M04/passive_response.py (the frozen anisotropy law
    effective_modulus(E_fiber, E_trans, theta) = E_trans + (E_fiber -
    E_trans) * cos^2(theta); used UNMODIFIED),
  - MAT2-M05/interface_exchange.py (bond/tie interface law form and refusal
    vocabulary; used UNMODIFIED as the sealed authority for the tie law),
  - MAT2-M07/integrated_step.py, MAT2-M06/local_contact.py (present on the
    sealed line; M07's suite re-run as regression via M08's committed
    receipts; not imported by this card).
- Regression baseline (run green in this checkout BEFORE implementation):
  M03 test_pressure_membrane.py 15 tests OK; M04 test_passive_response.py ALL
  FROZEN PROBES GREEN; M05 test_interface_exchange.py OK. At the candidate
  revision all three re-run green plus M08's committed-receipt suite.

## Scope decision (declared, honest): CPU-only physics

Nothing in done_when requires GPU residency; the four sealed dependencies
(M03/M04/M05 physics + M08 residency) are all reused as CPU numpy modules.
This card is CPU-only (stdlib + numpy, fixed 300 Hz tick, deterministic,
float64, no RNG, no wall-clock in physics) for the same reason M03/M04/M05
were: the demonstration is of the material physics, not of the resident
executor, and M08 already qualified the resident-GPU path upstream. This also
keeps the single GPU free for the parallel M09 lane (the wave brief serializes
cards only by single-GPU occupancy; a CPU-only card removes its own
occupancy). Declared as an applicability boundary, not an omission. If review
requires a GPU-resident rerun of the same laws, that is a follow-up card, not
a silent gap.

## Frozen statement (what is built)

An engineering pneumatic bending actuator composed ONLY from sealed laws:

- Body "actuator": a closed triangulated box beam — M03 `cube_grid(n=8,
  side=1.0)` vertices affinely scaled to the declared box
  L x w x h = 0.30 x 0.06 x 0.06 m (x in [0, L], y in [-0.03, 0.03], z in
  [-0.03, 0.03]), re-closed and re-verified through M03's
  `Membrane.require_closed()` at construction (open edges 0, consistent
  winding, positive signed volume; expected counts frozen below). 768
  triangles; 414 vertices (derived: two (n+1)^2 = 81-vertex face sheets +
  4 edge strips of (n+1)(n-1) = 63 vertices each: 2*81 + 4*63 = 414).
- Support (visible, declared): the root clamp — all membrane vertices with
  rest x <= 0.0375 m (= L/8: the root face's 81 vertices plus the first
  cross-section ring of 4n = 32 vertices; count identity 113 asserted at
  construction). The clamp is a DECLARED body, rendered and labeled in every
  whole/side/front view (profile falsifier "hidden constraint/support" is
  refused by construction and audited by FB6).
- Authored directional resistance: the fiber layer = all edges whose BOTH
  endpoints have rest z >= +0.03 - 1e-9 m (the top face's edges). Fiber axis
  a = xhat = (1, 0, 0) on the layer. Edge stiffness uses M04's law
  UNMODIFIED: E(theta) = E_trans + (E_fiber - E_trans) * cos^2(theta) with
  theta = angle(edge direction, xhat), (E_fiber, E_trans) = (1.0e8, 1.0e6) Pa
  on the layer; edges outside the layer have NO fibers authored: E = E_trans
  at any theta. Wall thickness t_wall = 3.0e-3 m (declared). Edge
  characteristic: k_e = E_e * t_wall * A_dual_e / L0_e^2 where L0_e is the
  edge rest length and A_dual_e the summed rest area of the triangles
  incident to e (for an axis-aligned interior grid edge this reduces to
  E_e * t_wall * s_perp / L0_e; e.g. a bottom-face x-edge:
  1.0e6 * 3.0e-3 * 5.625e-4 / 0.0375^2 = 1200 N/m; the top-face x-edge is
  100x stiffer: 120000 N/m — the strain-limiting layer). XPBD compliance
  alpha_e = 1/k_e. Scalar XPBD edge projection, 8 iterations per substep in
  declared edge index order (M03 T7 heritage).
- Pressure source: M03 `PressureSource` UNMODIFIED — source_id "m10_source",
  p_ext = 0 Pa, scheduled p_int, max_delta_p = 5000 Pa, max_flow = 1.0e-3
  m^3/s, provenance "MAT2-M10 preregistered pneumatic actuator source
  (engineering actuator demonstration)". Traction recomputed on CURRENT
  geometry every substep (area-scaled, M03 law), equal-third lumped to
  vertices (M03 `vertex_loads`, default area weighting).
- Attachment (actual load path): one tie, M05 BondElement law form
  (zero-rest-length, tension-only) generalized to a declared tie axis = the
  current unit vector between its endpoints (the sealed M05 element is
  xhat-locked; this one-axis generalization is declared as THIS CARD's
  composition, with M05's file imported UNMODIFIED as the law authority and
  M05's refusal vocabulary reused: bond_not_bound, bond_already_bound,
  release_of_unbound_bond, auto_bond_refused). k_tie = 600 N/m. The tie binds
  a declared membrane anchor vertex (stable ID; the bottom-face vertex
  nearest (0.9*L, 0, -0.03) m) to the load. Proximity never creates a bond
  (M05's refuse_auto_bond heritage).
- Load (body "load"): a declared point mass m_load = 0.010 kg; gravity
  g = 9.80665 m/s^2 (declared scenario constant, M03's) acts on THE LOAD ONLY
  (declared: no gravity on the membrane scaffold — honest limit, M03
  heritage). Load damping c_load = 4.0 1/s (declared). Rest position
  directly below the tie anchor at z = -0.13 m. Tie bound at tick 0
  (explicit bind, never implied).
- Membrane scaffold mass: declared total 0.050 kg split equally per vertex
  (M03 T7 heritage; refinement-invariant by construction), for honest
  dynamics only.
- Integration: dt = 1/300 s fixed (300 Hz pin, req.teddy_gpu_matter_kernel
  heritage), N_SUB = 4 substeps per tick (M08 heritage), substep order
  DECLARED and digested every tick: (1) damping, (2) pressure loads from
  current geometry, (3) load forces (gravity + tie), (4) semi-implicit
  position step, (5) XPBD edge projection x 8 (clamped vertices pinned after
  every iteration), (6) tie projection, (7) volume/work/ledger accumulation.
  float64 throughout; no float atomics concern (sequential numpy), no RNG,
  no wall-clock in results.

## Frozen experiments and predictions (limits fixed before any run)

Pressure levels P = {1000, 2000, 3000, 4000} Pa (all within source limits).
Quasi-static runs settle 1500 ticks at fixed delta_p with c_v = 40.0 1/s
membrane damping; settle criterion at the measurement window (final 200
ticks): max vertex speed <= 1e-4 m/s, max load speed <= 1e-4 m/s (measured
values recorded next to the bounds).

- X0 material_state gate: the composed experiment document (region
  "actuator" with the declared pressure_deformation law + ports, region
  "load", one declared bond relation for the tie, single-owner matter rows)
  validates under M01's validator UNMODIFIED. Pre/post variants validate.
- X1 directional response (free run, no load): z_tip = z of the declared tip
  probe vertex (top-face vertex nearest (0.9*L, 0, +0.03) m) relative to its
  settled p=0 position.
  - X1a sign: z_tip(4000 Pa) > 0 (the beam curls TOWARD the stiff layer).
  - X1a magnitude window: z_tip(4000) in [1.0e-3, 8.0e-2] m. Derivation:
    bottom-wall differential strain eps_b - eps_t ~ p*w/(2*t_wall*E_trans)
    = 4000*0.06/(2*3e-3*1e6) = 0.04 minus the fiber layer's ~0.04/100,
    curvature k ~ (eps_b - eps_t)/h ~ 0.65 1/m, tip rise z ~ k*L^2/2 * (1 -
    kL/6)-ish ~ 3e-3 m; the frozen window brackets this estimate 3x below
    and 25x above (order-of-magnitude honest; falsifiable both ways).
  - X1b monotonicity: z_tip(1000) < z_tip(2000) < z_tip(3000) < z_tip(4000).
  - X1c isotropic control (FB2a clean side): with E_fiber := E_trans
    (reinforcement removed, same pressure), |z_tip_iso(4000)| <= 1.0e-4 m
    (the mesh is z-symmetric; without authored anisotropy there is no
    preferred bend direction; residual is solver round-off).
  - X1d sign-flip control (FB2b): fibers authored on the BOTTOM face
    instead: z_tip_flip(4000) < 0 and |z_tip_flip| in
    [0.4 * z_tip(4000), 2.5 * z_tip(4000)] (mirror symmetry of the mesh
    makes the mirrored run the same physics; window is float/solver
    honesty). Delta claim recorded: z_tip(4000) - z_tip_iso(4000) >= 1.0e-3
    m (the directional response is CAUSED by the authored anisotropy — the
    card falsifier "contraction is claimed from isotropic inflation alone"
    is refused by construction and bitten by FB2).
- X2 blocked-load reaction (blocked run): the tip probe vertex is pinned at
  its settled p=0 position by a declared anchor (visible body). The pin
  force per substep is accumulated (m_v * required acceleration to hold the
  vertex); F_block = the time-average over the settled window, components
  recorded.
  - X2a sign: F_block_z < 0 (the anchor pulls the tip DOWN against the
    free-run rise).
  - X2b magnitude window: |F_block(4000)| in [1.0e-2, 10.0] N (upper
    reference p * A_face = 4000 * 0.06 * 0.06 = 14.4 N; honest bracket).
  - X2c near-linearity: |F_block(1000) / F_block(4000) - 0.25| <= 0.15.
  - X2d power-off: the blocked force at delta_p = 0 (settled, post-schedule)
    satisfies |F_block(0)| <= 0.02 * |F_block(4000)| + 1e-4 N (no pneumatic
    holding without pressure).
- X3 reciprocity (independent expectation, Betti's theorem, derived BEFORE
  implementation): for the quasi-static families, dF_block/dp = dV_free/
  dz_tip at each interior level (both [m^2]). Central differences across the
  level set at 2000 Pa (levels 1000/3000) and 3000 Pa (levels 2000/4000).
  Frozen: relative disagreement <= 0.20 at BOTH levels (floored at 1e-12;
  vacuous comparisons refused — P5 guard armed and self-tested before any
  receipt). Linear-superposition honesty: follower loads make this second-
  order exact; deflections are small (X1a window caps z_tip at 8e-2 = 27% of
  L) and the window absorbs the remainder. Measured margins reported.
- X4 load-line superposition (loaded run, third independent expectation):
  with the tie + load settled at 4000 Pa, the loaded tip position must
  satisfy |z_tip_loaded - z_pred| <= 0.25 * max(|z_pred|, 1e-4) where
  z_pred = z_tip_free(4000) * (1 - T_meas / F_block(4000)) and T_meas is the
  MEASURED settled tie tension (not assumed mg). The load follows the tip
  through the taut tie: |dz_load - dz_tip_loaded| <= 3.3e-4 m (= mg/k_tie +
  margin, derived 1.635e-4 m).
- X5 work and energy ledger (the dynamic work run):
  schedule delta_p(tick) = 4000 * ramp: ticks 0-200 ramp 0 -> 1, ticks
  200-900 hold 1, ticks 900-1100 ramp 1 -> 0 (POWER OFF), ticks 1100-1500
  hold 0; 1500 ticks total, tie + load attached from tick 0 (200-tick
  pre-settle at p=0 recorded; lift measured relative to the settled start).
  - X5a per-tick ledger: R_tick = dE_kin + dU_edge + dU_tie + dE_grav_load
    + Q_damp - W_press_tick; frozen |R_tick| <= max(0.05 * turnover_tick,
    1e-7 J) at EVERY tick, R recorded (measured constraint-projection
    exchange is R, never hidden — M03 A1 form).
  - X5b two work measures agree: per tick, |W_press_volume -
    W_press_traction| <= max(1e-9 * |W_press_tick|, 1e-12 J) (M03's
    traction-displacement vs delta_p * dV identity at substep granularity,
    accumulated per tick).
  - X5c power identity: P_source = delta_p * dV/dt (M03 law);
    |sum(P_tick * dt) - W_press_total| <= 1e-9 * |W_press_total| (same
    integral, independent accumulation order).
  - X5d load work bounded by source: 0 < W_load = mg * (z_load(peak
    settle) - z_load(settled start)) and W_load <= W_press_peak_total where
    W_press_peak_total = cumulative W_press at the end of the hold phase;
    reported efficiency eta = W_load / W_press_peak_total <= 0.5 frozen
    (derivation: the source also inflates the whole volume and stretches
    the scaffold; expected eta is a few percent).
  - X5e power-off recovery (phases tagged per P6): at the settled end
    (phase D, ticks 1100-1500): |z_tip(end) - z_tip(start)| <= 0.1 *
    z_tip_peak and |z_load(end) - z_load(start)| <= 0.1 * lift_peak (the
    actuator does NOT hold the load powered off; it lowers it). Tie tension
    returns to <= 1.2 * mg_settled. Ledger stays closed through the
    transient (X5a every tick).
- X6 pressure limits (named refusals, M03 codes reused): demonstrated to
  fire in-process: pressure_source_delta_p_limit_exceeded (requested 6000 Pa
  > 5000), pressure_source_negative_absolute (p_int < 0),
  pressure_source_undeclared (traction without a declared source),
  pressure_source_flow_limit_exceeded (dV/dt > 1e-3). Every real run records
  max |delta_p| <= 5000 Pa and max |dV/dt| <= 1e-3 m^3/s (measured).
- X7 determinism: two fresh subprocess runs of the full dynamic scenario
  produce BYTE-IDENTICAL experiment_trace.json (sha256 recorded; no RNG, no
  wall-clock in physics; X2 heritage, the trace is the determinism unit).
- X8 phase accounting (P6): the dynamic run's states carry per-state phase
  tags (A_rampup 0-200, B_hold 200-900, C_poweroff 900-1100, D_settled_off
  1100-1500); all phase metrics extracted ONLY via keyed per-phase
  extractors; receipt carries phase_state_counts and keyed values.

## Frozen falsifier arms (P1: clean control FIRST, named premature guard, receipt row)

Every arm runs its clean control in the same executable; a vacuous arm dies
loudly via its guard; receipt rows embed clean_control {metric_scope, value,
within_tolerance, guard} beside the tampered value and bit.

- FB1 "activation writes body poses" (card falsifier): clean control = the
  motion audit — the load trajectory is re-integrated from the RECORDED
  per-substep load forces with the declared semi-implicit integrator from
  the recorded initial state and must reproduce the emitted trajectory
  (window 1e-9 m; the audit is an exact recomputation of the declared
  arithmetic). Tamper = a pose writer (z_load set kinematically from the tip
  each substep, forces bypassed): the audit deviation MUST exceed 1.0e-3 m
  (expected ~1e-2 m scale). Guard m10_fb1_premature.
- FB2 "contraction is claimed from isotropic inflation alone": FB2a tamper
  = E_fiber := E_trans build (isotropic inflation still happens — volume
  still changes, recorded — but the directional claim MUST be refused:
  z_tip_iso window X1c violated by the authored build's D >= 1.0e-3 m
  advantage, delta recorded); FB2b = sign-flip build (X1d). Clean controls:
  the authored free run passes X1a/X1b in the same executable. Guards
  m10_fb2a_premature / m10_fb2b_premature.
- FB3 "work has no source": tamper = tie force on the LOAD amplified x1.5
  with the membrane feeling the true reaction (one-way boost): the X5a
  ledger gate MUST fire (refusal unexplained_energy) on the tampered run;
  clean run stays green. Guard m10_fb3_premature.
- FB4 "area-independent triangle forces": clean control = per-triangle
  traction ratio |F_i|/A_i equals the scheduled delta_p within 1e-9
  relative on every substep of every run (min/max recorded) AND the M03
  linear-field buoyancy identity (F_net = rho g V exact, rel <= 1e-12, rho =
  1000 kg/m^3 declared) on the free actuator (mixed-area mesh: face
  triangles 1.40625e-4 m^2 vs end-face 2.8125e-5 m^2). Tamper =
  area_weighting='constant' (M03's falsifier hook): the buoyancy identity
  MUST degrade beyond 1e-6 relative. Guards m10_fb4_premature.
- FB5 "clipped load path": tamper = the tie's reaction on the membrane
  dropped (the load is pulled, the membrane never feels it): the
  equal/opposite interface audit (per-tick recorded tie force rows on both
  bodies) MUST refuse (tie_reaction_mismatch) AND the loaded tip position
  MUST differ from the clean loaded run by >= 5x the settle tolerance
  window. Clean control: audit green, loaded run matches superposition X4.
  Guard m10_fb5_premature.
- FB6 "hidden constraint/support": structural audit = the scene inventory
  (clamp, anchor when blocked, tie, load) must match the rendered subject
  list; the tamper removes the clamp from the inventory and MUST be refused
  (support_missing_from_scene). Visual half = measured pixel probe (P3
  discipline): the committed stills contain the clamp/anchor labels at
  integer-measured bounding boxes; the probe writes its own schema'd receipt
  and the report requires it fail-first (refusal codes m10_report_*).
- FB7 "unbound media / overlay-driven motion": capture gates = rendered
  vertex arrays asserted against the sha-bound trace before any pixel is
  written; every view row carries camera_motion_or_bookmark_sequence =
  fixed_bookmark and the SAME state_binding.sha256 (identical composite
  state hash on every view row); FB1's audit is the physics-side
  discriminator. Receipt rows recorded in the capture validation receipt.

## Frozen visual profile (material/motion; registry row is the authority)

- Views (exactly the registry's 3, each as a diagnostic/clean pair):
  "whole experiment at fixed distance", "orthogonal side and front",
  "oblique close-up of the loaded interface".
- Diagnostic layers (the registry's 5) on every diagnostic row; clean rows
  carry zero labels, zero layers, zero overlays, same cameras (clean rows
  must contain no diagnostic pixels — M05's leak lesson).
- Capture scenario: the dynamic work run (X5) with the 9 declared snapshot
  ticks [0, 300, 600, 900, 1000, 1100, 1200, 1350, 1500]. Single-artifact
  binding (P8): ONE video; capture_sha256 = that file's disk sha256 ==
  manifest == context == determinism record; committed BMP stills at
  declared indices [0, 3, 5, 8] (independently recomputable); every view row
  carries the same state_binding.sha256 (the committed trace sha) and the
  same per-tick composite state digest.
- Cameras: right-handed, metres, quaternion wxyz camera-to-frame, forward -Z
  / up +Y, near 0.01 / far 100, sheet 960x540 (16:9), fixed_bookmark, all 16
  registry camera fields per camera record:
  - whole: perspective, vertical_fov_degrees 40, position (0.55, -0.85,
    0.55) m, target (0.15, 0, 0) m.
  - side: orthographic, span 0.55 m, position (0.15, -1.2, 0) m, target
    (0.15, 0, 0) m; front: orthographic, span 0.55 m, position (0.15, 0,
    -1.2) m, target (0.15, 0, 0) m (front declared as a fully declared
    secondary camera).
  - close-up: perspective, vertical_fov_degrees 30, target = the tie anchor
    vertex position at rest, position = target + (0.10, -0.14, 0.10) m
    (distance derived and recorded).
- Ticks: 9 frames at 1 video second per snapshot tick; tick_to_seconds_map
  declared; 1 tick = 1/300 s simulated.
- The renderer is a CPU rasterizer, painter's algorithm (declared
  occlusion_mode depth_tested); it displays solver state, asserted against
  the sha-bound trace before any pixel.

## Applicability boundary (honest, frozen)

- A CPU-only deterministic demonstration over pinned sealed laws; not the
  native engine runtime, not a live renderer, not GPU-resident (declared
  above).
- The scaffold is an XPBD edge network (demonstration scaffold, M03
  heritage); no continuum constitutive model is claimed. The tie is a
  one-axis generalization of M05's sealed bond form (declared composition of
  this card; M05's file reused UNMODIFIED as law authority). Betti
  reciprocity and load-line superposition are exact for linear systems; the
  follower-load (current-geometry traction) nonlinearity is absorbed by the
  frozen windows and the measured margins are reported either way.
- Declared absences: no membrane self-gravity, no contact with other bodies,
  no fluid interior model, no valve dynamics (the source is an ideal declared
  pressure actuator with authored limits), no biological claims of any kind.
- Biological equivalence is NOT evidenced and is not sought; the
  classification is produced by the frozen rule below.

## Frozen classification rule (receipt-driven, declared before measurement)

The report classifies the demonstrator via a declared rule evaluated on the
final receipts: biological equivalence would independently require ALL of
(a) specific tension >= 2.0e5 Pa (skeletal muscle lower band, declared
textbook constant 0.1-0.4 MPa), (b) work density >= 20 J/kg (muscle band,
declared), (c) actuator efficiency within [0.20, 0.40]. The measured values
(F_block peak / declared scaffold mass 0.050 kg; W_load / declared mass; eta
from X5d) are computed from receipts and the classification string
'engineering_actuator' is rendered unless ALL three hold. None is expected to
hold; no biological equivalence is independently evidenced.

## Gates and hygiene (house standards, this commit cites them)

IMPLEMENTER_CHECKLIST.md G1-G9 and TOOLKIT.md P1-P9 (E:/ChimeraWork/
monkey-coordination/house-standards/) govern this card: P1 clean-control
arms (FB1-FB7 above), P2 report-numbers lint shipped WITH the report
(lint_report_numbers.py bound to this card's artifacts, --selftest proving
it still flags planted defect literals), P3 measured disclosures (FB6 pixel
probe receipt, fail-first loaders in make_report.py), P4 transform-list
capture gate (frames are the determinism unit: ffmpeg decode of the bound
video == committed BMP stills under the explicit transform list identity /
vflip / hflip / rot180 with identity-only passing, pure-stdlib row-order
test with sensitivity guard on the declared stills), P5 vacuous-comparison
guard (armed, self-tested in main() before any receipt), P6 per-phase keyed
extractors, P7 registry profile read-only at capture + SHORT task_id "M10" +
criteria_sha256 identity across dispatch/registry/prereg/checks
(5e7560caa9efae9ec819c9127ab6ee6e7016e134bdf97e525f06cfedee31190c), P8
single-artifact binding, P9 publication hygiene (prereg committed separately
BEFORE implementation; contribution <= 32 files / <= 16 MB; ONE publication
commit with Agent: trailer; commit-message metrics from FINAL receipts; all
files written LF under the contribution .gitattributes '* -text').

No measured value appears above; every number is declared or derived from
the frozen scenario constants. Amendments, if any, will be committed
separately BEFORE the affected receipt exists, with the triggering probe
value recorded (M03 A1-A4 precedent).
