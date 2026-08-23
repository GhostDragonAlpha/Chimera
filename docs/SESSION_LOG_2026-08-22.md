# SESSION LOG 2026-08-22 -- the kernel-native bear

Operator's doctrine shift (his call, settled): splat-model line DEAD (no AI-trained
assets anywhere); 100% physics; the CAD bear becomes kernel-native. Active goal
(CreateGoal, operator-approved text): translated -> standing -> walking -> dressed,
dyad per milestone (numbers AND his eyes; milestone advances on his verdict only).

- M1 TRANSLATION (docs/THE_TRANSLATION.md, new): triangle->packet sampler
  (tools/cad_sample.py). RUN RECORD: run 1 per-triangle-abs volume bug + spurious
  interior cone in cad_mesh capsule() (duplicated equator ring ate ~25% volume;
  rendered fine in UE -- NUMBERS caught it); run 2 inertia noise floor sat exactly
  at the tolerance (N = 1/tol^2 is luck, derived N >= 4/tol^2 = 10000); run 3
  ALL PASS: 190,000 packets, 2.5044 kg, mass err 0.000%, inertia <= 1.921% on
  all 19 parts. S = 0.008 m derived from the thinnest load-bearing part.
- M2 STANDING (tools/kernel_stand.py): FIVE RUNS, four falsifiers, then PASS.
  RUN 1 dt misderived (whole-body vs per-packet wall oscillator, omega*dt=14.4,
  explosion -- numeric, not physics). RUN 2 PHYSICS FALSIFIER: COM 0.3 mm BEHIND
  the heel line -> fell backward; successor = vertical legs (90 deg, zero hip
  torque). RUN 3 toe-pole contact (the "foot" ellipsoid stood on its pole; rock
  test d_tau/d_theta > 0 = inverted pendulum, unstable for ANY damping) ->
  successors: ankle dorsiflexion + FLAT SOLE (cad_core feet get sole=0.8 clip,
  position solved from constraints: sole-only contact, COM >= 16.6 mm inside the
  patch, patch center under the COM line -- uniform wall pressure puts the force
  centroid at the patch centroid). RUN 4 slow forward tip: measured
  d_tau/d_theta = +2.5 N.m/rad; the inverted-pendulum term W*h = 4.05 beat the
  sole's rocking stiffness -> K_S now DERIVED from the stability condition
  K_S * sum(dz^2) >= 2 * W * h (converged 487.5 N/m), replacing the arbitrary
  0.5 mm sink. RUN 5 PASS: pen 0.705 mm, tilt 0.05 deg, drift 0.00 mm, settled
  (final-0.5s motion 0.000 mm). Wall dashpots (body-level Kelvin-Voigt, critical
  per mode) dissipate the drop energy by design -- energy not conserved across
  the settle and should not be.
- M3 begun (tools/kernel_walk.py): 3 rigid bodies (trunk, leg_L, leg_R) joined
  by spring-bond hips (kernel RESISTANCE bonds, stiffness derived from the
  single-support joint moment 0.41 N.m and 1 deg deflection bound -> k_rot
  23.5 N.m/rad). M3-STEP-0 PASS: the jointed bear reproduces the M2 standing
  bounds, hip deflection L +1.51 / R +1.59 deg (the ~2.3 deg trunk sag is the
  compliant joint under the 0.34 N.m gravity moment -- real plush physics).
  M3-STEP-1 (friction): Coulomb-capped viscous stick, mu=0.5 plush-on-laminate.
  RUN 1 falsifier fired (impact skid + compliant sag creep misread as drift);
  successor = measure against the post-impact t=1.0 s reference, same bounds.
  RUN 2 PASS: the jointed, friction-contact bear stands and HOLDS.
- M3-STEP-2 (the gait) pre-registered in kernel_walk.py's docstring: muscle
  tone = the hip bonds' rest frame rotated by a derived phase schedule
  (lean phi* = asin(0.058/L_leg) ~ 19.7 deg, swing 15 deg, plant/transfer
  asin(15 mm/L_leg) ~ 5 deg, T_xfer from the inverted-pendulum timescale;
  no positional drives, no tuned constants). Smoke test = 2 steps; metrics:
  tilt, non-band clearance, forward progress, plant detection, roll symmetry.
- Dyad status: M1 image (.tmp/packet_bear.png) + M2 image (.tmp/kernel_stand.png)
  presented to the operator; verdict PENDING (gate on advancement, not prep).

Still open: UE viewport path for the packet bear (the .tmp scatters are the
referee views); fur/cloth (M4); the docs-map update below is pending review.

## M3-STEP-2 continued — FORK 2, the EVOLVED signal (operator-approved, his "2")

- RUN 11-31: 21-run hand-derived controller tree measured to its structural
  limit (full record: tools/kernel_walk.py's docstring). Every constant
  derived; the FSM+PD+brake tree cannot close the load transfer.
- RUN 32 F2-a REGRESSION PASS: the batched float64 GPU port
  (tools/kernel_batch.py, BatchBear) reproduces the Python stand reference at
  61 checkpoints -- max |dcom| 3.704e-16 m, max |dtilt| 4.505e-12 deg.
  Machine epsilon: the port IS the same arithmetic.
- FORK 2 (operator's pick): LEARNED CONTROL POLICY on kernel physics. The
  physics stays kernel-native (mass/gravity/contacts/bonds -- nothing learned,
  no AI assets); the GPU EVOLVES only the 8-dim joint command signal
  ((phi_s, th) per joint, Q = Rz(phi_s)@Rx(th) about the joint frame,
  zero-order hold at the 50 ms referee cadence).
- THE TERM (operator, settled): what the GPU is doing is EVOLVING, not
  training -- "training evolves the teddy bear that allows it to walk."
  The word generalizes: UVs will be EVOLVED too. Blender is what a graphic
  artist would use; we are not graphic artists, so the texture layout is an
  evolved signal like the gait signal. Local solutions only -- no cloud
  models anywhere in the chain.
- RUN 33 pre-registered in kernel_walk.py's docstring: sep-CMA-ES, linear
  18->8 tanh policy (152 params), sigma0 = cmd_xfer = 0.0131 rad; episode
  2.0 s (the FSM's 2xT_xfer); reward = (BASE_GAP - min_t |com_x - X_R|)
  / BASE_GAP over the 56 mm transfer window; corridor breach (trunk tilt >
  17.2 deg) freezes progress; budget = measured throughput, 6 h cap.
  FALSIFIER: no evolved policy beats 28 mm min-gap within budget -> the
  interface is broken, not the physics.
- SWEEP ERRATUM (pre-data, recorded): the first sweep expectation conflated
  the pressure-centroid gain Gx = dP_x/dth_z with the COM response -- the
  pendulum inverts it (+phi_s -> sole centroid -x -> COM accelerates +x,
  x_ddot ~= (g/h_c)|Gx|th, h_c = 0.157 m). Measured +9.62 / -6.55 mm at
  0.5 s, zero-command drift 0.001 mm -> command path VERIFIED.
- Evolution in flight (task bash-t1zw3a3s) at this entry: gen 14 at 65 min,
  best reward 0.4959 (min-gap ~ 28.2 mm) -- at the falsifier threshold's
  edge, not yet past it.
- NEXT: F2-c, the official proof -- the evolved policy as command source
  through kernel_walk.py's OWN gait harness (hook site
  tools/kernel_walk.py:3522-3544; mapping: hips cmdk[2i]=phi_s,
  cmdk[2i+1]=th; ankles ac=(th, phi_s)), filmstrips + referee metrics, then
  the M1+M2+M3 dyad screenshots to the operator TOGETHER (his verdict is the
  gate; M1/M2 verdicts still pending).

## DOCTRINE AMENDMENT (operator, 2026-08-22) -- the no-AI line, scoped

The "no AI-trained assets anywhere in the chain" boundary is SUSPENDED for one
purpose: researching 2D AI-generated UVs (texture/material images) that we
apply to objects. The material-EXTRACTION methodology survives the swap --
same pipeline shape, but the carrier is TRIANGLES (UV-mapped surfaces), not
splats. Everything else about the boundary stands: the geometry is authored,
the physics is kernel-native, the gait signal is evolved locally. The AI
image is an input we extract material parameters from -- it is not an asset
in the chain and it is not generated geometry.

## UV METHOD, RUN-1 (2026-08-22 ~12:40) -- the falsifier chain worked

docs/THE_UV_METHOD.md pre-registered TESTS A/B/C; first run FAILED both A and
B, and both failures located real defects instead of being swept:

- TEST A RUN-1 (uniform-theta v): tears 0 everywhere, but pole-strip density
  blew the erratum bound by ~40x (measured 398-14007 vs bound 15-29).
  Uniform-v gives constant UV area per strip while 3D strip area falls like
  sin(phi). Falsifier fired -> successor equal-area v (TEST A2).
- TEST A2 (equal-area v from the tessellation's own measured strip areas):
  ratio stuck at 140.5 on EVERY part + 48 tears on every capsule. Diagnosis:
  (1) the theta-wrap seam triangles spanned the FULL tile in u (47/48 -> 0),
  a real full-tile smear in any REPEAT-wrap renderer; (2) capsules carried a
  coincident equator ring (explicit ring@b == top cap row 0) -> zero-area
  strip. Two genuine mesh defects, found by the numbers.
- TEST B RUN-1: category error caught -- compared a vertex-sampled render
  against a per-pixel reference; the measured delta WAS the sheet's
  sub-triangle frequency content, not a chain defect. Extract link passed
  silently (sheet stats == known MAT stats to rounding).
- TEST A3 (duplicated seam column, zero strip removed, equal-area v):
  PASS -- tears 0, cut clean, quad density ratio 1.000-1.370 (bound 2.0),
  per-part area/volume conserved vs HEAD tessellation to 3e-16.
- TEST B2 (chain through the actual artifact): PASS -- TEXCOORD_0 read back
  from cad_bear_uv.glb bit-exact, per-pixel renders identical (corr 1.0000).

Links 1/3/4/5 of the UV flow proven. Link 2 (the sheet) is TEST C: SD3.5
Medium downloaded to local cache (HF token, symlinks off), generation in
flight (task bash-k0b6pl2t) -> models/materials/fur_sd35_testc.png, then the
operator's eye at link 5.

File state: tools/cad_mesh.py (seam-cut equal-area UVs, still byte-identical
default GLB at md5 640626a3... verified BEFORE the A3 tessellation change;
post-A3 geometry conserved to machine epsilon), tools/cad_uv.py (A3+B2
runner), tools/uv_sheet.py (TEST C), docs/THE_UV_METHOD.md (results below
the line, all failures recorded).

## INCIDENT (2026-08-22 ~15:45) -- orphaned CUDA workers wedged the GPU driver

Root cause (mine): .venv-gs's python is a 3.13 REDIRECTOR that spawns the
base interpreter (AppData\...\Python313\python.exe) as a separate process.
Timeout kills (task-level and subprocess.run) terminated the launcher but
orphaned the real workers. Five zombie SD3.5 worker processes ended up stuck
in uninterruptible GPU-driver calls -- taskkill /F /T cannot reap them; one
holds 14 GB RAM. nvidia-smi now hangs; RUN 33 slowed to ~18 min/gen (from
~5). C4 (four fur sheets) failed twice as collateral: falsifier recorded,
but the honest cause is the wedged machine, not the method.

What is SAFE: policy_run33.npz checkpoints ON NEW BEST -- best policy
r=+0.6794 (min-gap ~18.0 mm vs the 28 mm bar) is on disk (12:50). A reboot
loses only the CMA-ES search state, not the result. Code+docs pushed
(8ddcd93..85e788c).

Operational lesson recorded for all future GPU work: never rely on timeout
kills for venv-python GPU processes on Windows; find the base-interpreter
child via tasklist and kill by WINPID, or design runs so workers exit
cleanly themselves (single-shot processes that return, as TEST C/C2 did).

## RUN 34 RESULT + ERRATUM (F2-c, 2026-08-22 ~18:40) -- FALSIFIER FIRED; the label was a bug

RUN 34 ("gait policy", reference harness, the policy as the ONLY command
source): FALSIFIER FIRED per pre-registration. Fell at t=0.58 s; corridor
breach ~t=0.43 s (table rows: t=0.40 tilt 11.75 deg / com_x 30.1 mm, t=0.45
20.85 deg / 22.8 mm); com_x swept 59.1 -> 3.8 mm in 0.55 s; FnL unloaded
24.6 -> 0.5 N; tilt max 48.18 deg. Full-trace min |com_x - X_R| = 1.8 mm at
t=0.55 s -- achieved while falling (the pre-registered referee is full-trace
min + no-fall + tilt <= 17.2 deg; the fall alone fires it). Evidence:
.tmp/run34_f2c.log, filmstrips .tmp/kernel_walk_gait{,_side}.png.

ERRATUM -- retraction of the "port best 16.4 mm / reward +0.7076" claim in
the RUN 34 pre-registration and the npz label: it was an artifact-labeling
bug, not a result. train() saved the gen-39 population MEAN m labeled with
a transient best SAMPLE's reward (+0.7076 / min gap 16.4 mm); that sample
was never persisted (m and sig at gen 39 are not on disk). The new eval mode
measures the saved theta's true reward through a port episode: +0.5427,
frozen min gap 25.61 mm -- and the reference replay brackets it (~25.6 mm
before corridor breach in BOTH harnesses). No chaotic divergence: under
identical commands the two implementations agree; transfer holds for this
policy, it just is not the 16.4 mm one. The pre-registered successor
diagnostic (obs channel mapping) ran first and found nothing wrong -- the
mapping is channel-for-channel identical to BatchBear.obs()/step().

Fix: train() now saves thetas[order[0]] (the actual best sample), not m;
new "eval [npz]" mode measures any artifact's true reward. Provenance: the
mislabeled gen-39 mean preserved as
models/cad_bear/policy_run33_gen39_mean_mislabeled.npz before overwrite.

Successor (pre-authorized RUN 33 procedure, not a new decision): honest
retrain -- E=20, hours=6 cap, OUT path policy_run33.npz now honestly
labeled; then re-run the reference referee and bring M1+M2+M3 dyad views to
the operator TOGETHER. His verdict is the gate on the walking milestone;
M1/M2 verdicts still pending.
