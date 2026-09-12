# PREREGISTRATION — feature-walk-01

Written BEFORE any build, render, capture, or judgment, on base `c91518a5`
(task branch `astra/tasks/feature-walk-01`). No measured actuals appear in
this commit. Trailer: `Agent: subagent-worker-05`.

## The product defect being answered (operator doctrine 2026-09-11)

> every feature is a goal; ships only when VISUALLY VERIFIABLE

FEATURE: WALK — the creature walks across the grid under its own gait. The
engine exposes the gait machinery over HTTP (`/gait`, `/gait_bin`,
`/gait_state`, `/stride`, `/stride_bin`), but the PR #97 blind dyad judge
found "gait steps=0 and no foot movement — no locomotion is demonstrated".
The gait plane has never been shown walking. This lane closes that defect:
engage BOTH gait planes through the public routes, capture the take, and let
a blind judge rule on what the creature is doing.

## Rule 0 parts

**STATEMENT.** The gait machinery exists behind the public HTTP contract and
has never been shown moving; the missing feature is the visible walk.

**PREDICTION (unmeasured at this commit).** A blind judge, given the take
movie and 6 ordered keyframes, names the creature as WALKING/TRAVELING (not
merely stepping in place) and can say which direction it went.

**FALSIFIER (named before the run).** The lane records the honest partial —
and the product defect stands as an ENGINE-SERVICE gap, not a lane failure —
if any of these fire:

- **F1 (translation):** feet cycle but the body never translates
  (in-place stepping). Record: the walk feature is NOT closed; the gap is
  that no public route can translate the creature's root (derivation below).
- **F2 (naming):** the judge does not call it walking.
- **F3 (edit):** any engine-source edit would be needed to produce travel.
  Structurally excluded and checked: the lane may only speak the engine's
  public HTTP surface plus the two harness wrappers the accepted PR #97
  probe used (`tools/engine_demo.py` launch/stop; `cpp_bridge.load_mesh_bin`
  = POST /mesh_bin, `cpp_bridge.encode_movie`). Zero C++ edits (architecture
  directive); any engine edit inside this lane is a finding, not a fix.

## The derivation (Rule 1) — what the contract CAN and CANNOT produce

Traced from the engine source at base `c91518a5` (read-only):

1. The CPG plane (`/gait_bin` + `/gait`): an 8-oscillator Kuramoto-Sakaguchi
   CPG with the Owaki load surrogate, stepped by RK4 on the GPU
   (`shaders/gait.comp`, bit-exact port of the golden CPU reference). Its
   only pose output is `thetaL/thetaR` = theta_mid + theta_amp*sin(phi) of
   the two HIND KNEES (the H7 law, measured H6 ROM: L mid 71.915 amp 73.475;
   R mid 69.210 amp 71.540, degrees).
2. Those thetas drive the pose ONLY through the hinge law: every banded
   vertex rotates about the FIXED pivots JL/JR about the ONE inter-knee axis
   (`engine.cpp pose_hinge`; `hinge.comp` executes the same law on the GPU).
   A rotation about a fixed pivot cannot translate the body.
3. The stride plane (`/stride_bin` + `/stride`): the certified stride's
   thetas are written per joint into the joints state lane
   (`engine.cpp stride_tick`); the joints kernel poses the creature by LBS
   rotations about the pack's joint pivots (`joints.comp`). Rotations only —
   no root DOF exists in the JNT3 pack.
4. Ownership (`engine.cpp` frame()): the joints path takes precedence over
   the hinge path when live (`if (joints_on_ || edit_mode || stride_drives)
   ... else if (hinge_active_ ...)`), so the two pose planes are engaged
   SEQUENTIALLY, never simultaneously.
5. The route table (`engine.cpp` main.cpp route dispatch, read verbatim)
   contains NO route that mutates a mesh root or model transform: `/camera`
   moves the VIEWER, not the creature. `/mesh_bin` re-loads a mesh but is a
   full load (not a per-frame transform), and using it to drag the body
   would be Python dragging the mesh, not the creature walking under its own
   gait — the exact "distance = a receipt, not a gait" impostor
   (`tools/chimera_gait.py` header).

**Derived conclusion.** Under the current contract the creature CANNOT
translate through the world by any legal route sequence; the maximum visible
walk is in-place stepping. The prediction is still tested (the judge may or
may not read the swing as travel); if F1 fires it fires as a MEASURED engine
fact, with the route table as the named gap. The camera is therefore FIXED
for the whole take (moving it would fake travel and corrupt the falsifier).

## Declared inputs (read, not measured by this lane)

- Mesh `Saved/meshes/monkey_birth.bin` (via `cpp_bridge.load_mesh_bin`) +
  rig `Saved/meshes/monkey_joints.bin` (JNT3, nv 18459, nj 28) via
  `POST /joints_bin` — IDENTICAL subject pair to PR #97 and the motion sweep.
- The certified stride pack `stride_certified_pack.json` in this directory —
  a VERBATIM copy of the operator checkout's `Saved/gait/stride.json`
  (format chimera-stride-1, 331 samples x 28 joints, dt 1/60, loop_t0
  1.832 s, stride_t 3.664 s, clock T_stance 1.832 s from LIPM, gates
  foot_max 9.54e-05, velocity_jump 2.74e-15, tracking PASS, physical_contact
  UNVERIFIED), sha256
  `883ed9d87859dfe4e4126631149ca09b250e1be441357f3db4a16c468b01f50a`.
  The original is uncommitted in the operator checkout, so the copy rides
  in this evidence directory; the hash binds the copy to the original.
- CPG constants (embedded in the driver with provenance): the golden
  reference's packet constants (SIGMA 0.5, W 1.0, DT 1e-3,
  N0 = 2*omega_ref/sigma DERIVED for the stall regime, omega_ref 2.5*pi)
  and the measured H6 knee theta maps (THM_L 71.915, THA_L 73.475, THM_R
  69.210, THA_R 71.540) from `.tmp/gait_ref.py` at the operator checkout;
  the ucrtbase.dll sin/cos implementation constants the shader was
  bit-exact-ported against (A1..A6, C1..C6, TWO_OVER_PI, MAGIC, PC0, PC1,
  PC3, SIXTH) from `.tmp/ucrt_trig.py`. Both .tmp sources are uncommitted
  operator files; the constants are embedded verbatim in the driver, which
  lives in this lane's scope.
- Hinge blob DERIVED from the JNT3 pack's own data (via the canonical loader
  `tools/gait_mirror.py::load_pack`, offline check executed on the declared
  base before this commit): JL/JR = the pack's knee_L/knee_R pivots,
  axis = normalize(pivot_kneeL - pivot_kneeR) (the bilateral transverse
  line; the corrected-axis law of the H6 march), wL/wR = the pack's own
  per-vertex skinning weights for the two knees made disjoint (offline
  measured: 842 verts per band, ZERO overlap — no BFS stand-in needed, the
  pack carries disjoint bands natively). Flexion sign derived: shank tip
  v=(0,-1,0) under +theta about +x sends z' = -sin(theta) < 0 = posterior
  (the measured anatomy: tail at z = -4.288 is posterior) = heel-to-butt.
  The driver asserts this sign numerically with the same Rodrigues law as
  `pose_hinge` before engaging.
- `/gait` engagement constants: steps_per_frame 3 (the route's own default)
  and omega 2.5*pi (omega_ref). Wall cadence is frame-rate dependent by
  engine design (RK4 steps per FRAME); the delivered cadence is MEASURED
  from thetaL/R readbacks and recorded, not assumed.

## The take (declared schedule, single engine instance, fixed camera)

10 fps capture x 360 frames = 36.0 s of ENCODED take (inside the 30-60 s
window). Wall-clock capture rate is measured and recorded: the engine renders
continuously in its own visible window, and slow capture turns the movie into
a time-lapse of a real-time motion — declared here, never hidden. Both /glass
(the product surface, judge artifact) and /frame (pixel-clean twin) captured
every frame; the camera is set ONCE (r = 3.4x mesh extent, the motion sweep's
head-crop fix) and never touched again.

- f000-014 REST (rig verified, standing)
- f015-164 CPG MARCH (150 frames): POST /hinge_bin (derived blob) ->
  POST /gait_bin -> POST /gait {on:true, steps:3, omega:2.5*pi}
- f165-174 SETTLE: /gait {on:false} -> /hinge_bin nvert=0 (rest pose restore)
- f175-354 CERTIFIED STRIDE (180 frames): POST /stride_bin ->
  POST /stride {on:true, playing:true, t:0} (wall clock, loops forever)
- f355-359 HOLD

6 ordered judge keyframes: f000, f090, f164, f175, f265, f359. At each
keyframe a full engine-truth readback is recorded: GET /gait, GET /stride,
GET /joints (all 28 thetas), GET /scene, and the /project camera-fixity
probe (below).

## Gates (declared BEFORE the run; measured actuals recorded after)

- **G1 (closes "gait steps=0"):** during MARCH, GET /gait reports
  loaded=true, on=true, steps_total > 0 and STRICTLY increasing across >= 3
  readbacks.
- **G2 (H7 law live):** thetaL/thetaR swing at least 80% of the declared
  amplitude about the declared mid at some MARCH readback.
- **G3:** GET /gait_state returns a phase ring whose per-oscillator std > 0
  (the CPG is stepping, not parked).
- **G4:** during STRIDE, GET /stride reports active=true, playing=true and
  t advances past loop0*dt (the stride entered its loop).
- **G5 (closes "no foot movement"):** GET /joints during STRIDE shows
  hip/knee/ankle thetas with max |theta| >= 10 deg at >= 2 stride keyframes.
- **G6 (camera-fixity probe):** POST /project with the SAME world point
  (the knee_R pivot, a fixed body point) at every keyframe returns sx,sy
  constant within 0.5 px — the camera provably did not move, so any
  apparent translation in the frames cannot be a camera pan.
- **G7 (the falsifier measurement):** with G6 holding and the pose laws
  rotating about fixed pivots (derivation items 2-3), the take's keyframes
  show the creature at a constant position over the grid: travel = 0, F1
  fires, and the honest partial is recorded as an engine-service gap.

Every gate records actuals as evidence `.txt` in this directory. A fired
falsifier is a delivered finding, never a silent bound change.

## The blind judge (SIMPLE protocol)

At the end of the lane, the lead is asked (fleet mailbox, coordination-only)
to spawn a fresh blind judge with: the take movie, the 6 ordered keyframes,
and the simple question — "What is the creature doing? Does it travel
anywhere? If yes, which direction and how far?" The judge sees NOTHING about
gait planes, scripting, the route table, or the expected answer. The verdict
maps: WALKING/TRAVELING + direction named = PREDICTION MET; stepping in
place / no travel = F1 (honest partial). The lane claims NO acceptance
beyond the measured verdict.

## Scope and resources

Write scope: `tools/product_features_walk` (the driver module) +
`docs/evidence/agent_fleet/FEATURE_WALK` (this directory). Resources:
`rtx4090` + `engine_demo` via the controller (water-room may hold them; the
lane authors on CPU and waits). Engine: this slot's OWN private build under
`.tmp/engine_build/featurewalk/`, port from the fleet range (never 8080),
launch `--no-restore` from a unique runtime CWD, executable + SPIR-V hashes
recorded. `ChimeraEngine/engine/build/` untouched. Non-headless, visible,
slot-owned runtime per the fleet's visible-runtime rule.
