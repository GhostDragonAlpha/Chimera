# PREREG AMENDMENT v2 DRAFT — material-proof battery (wk-proof-material)

Status: DRAFT for Lieutenant review/commit. Nothing in this amendment takes
effect for gated execution until committed. Frozen baseline: prereg v1 at pin
007ff99c61430ad418f41d5be27470d22a7653b6 (file sha 64225cf5...). This
amendment changes ONLY what first sealed execution proved must change; all
other predictions, tolerances, sweeps and protocols of v1 remain frozen.

## A. Thermal companion S6 — recalibration + boundary bugfix

Frozen S6 FAILED all three predictions, deterministically (both runs; profile
bytes identical across runs). Preserved receipts: thermal r1 job
49e645a57c974dda888439198f81df8e, r2 job 87892e055551411d967c55cdae69de9e
(profile sha ec9c980e... both; summaries 13e852fc... / e4dae719...).

A.1 T1 (energy closure): 0.09996 measured vs <= 1e-9 predicted. Cause: script
boundary bug — boundary nodes frozen instead of reflective (ghost) Neumann, so
the trapezoid-weighted discrete energy leaks into a permanent cold boundary
node. FIX: reflective Neumann update at both end nodes (T[0] += dt*alpha*2*
(T[1]-T[0])/dx^2, symmetric at the right end). The FROZEN PREDICTION IS
UNCHANGED (|E_th - beta*W_mech|/W_mech <= 1e-9); with the fix the scheme
conserves the trapezoid energy to roundoff.

A.2 T2 (conduction decay rate): fitted 1.78e-2 vs theory 1.97e-3 (9x off).
Cause: prereg miscalibration by the worker. With alpha=1e-4 m^2/s the first
mode time constant is L^2/(pi^2*alpha) = 1013 s; the declared fit windows
([2,3], [3,4] s) are multi-mode contaminated and cannot recover the asymptotic
rate. AMENDMENT: alpha := 5e-3 m^2/s (tau_1 = 1/(pi^2*alpha) = 20.26 s),
T_END := 140 s (6.9 tau_1), fit windows := [80,110] s and [110,140] s (by
t=80 s = 3.95 tau_1, mode n decays as exp(-n^2 * 3.95 * pi^2...): mode>=2
amplitudes < 1e-13 of mode 1). PREDICTION (restated, same tolerance form):
fitted rate within 5% of 2*pi^2*alpha/L^2 in both windows.

A.3 T3 (equilibration): 2.04 measured vs <= 1% predicted — impossible at
t=20 s with alpha=1e-4 (equilibration needs ~5 tau_1 ≈ 5000 s). Same cause as
A.2. AMENDMENT: at t=140 s (6.9 tau_1) residual nonuniformity is at the
1e-6 level. PREDICTION (restated, unchanged form): (max-min)/mean <= 1% at
t=140 s.

## B. Loading protocol S1-S4 — Risk R5 recorded outcome and replacement

B.1 Recorded outcome: kinematic particles with mass=0/density=0 (the example
template's "infinite-mass BC" construct) do NOT constrain compliant material
in SolverImplicitMPM 1.6.0. Evidence (all preserved):
- Pre-fix S1 (seal 11cc479b...): S1 r1 job 2ee48d206e7242ed84fe9545d84f748f —
  whole sim static (BF3 masked everything); r2 infra crash preserved (BF2).
- Sealed diagnostic job 845dd1158c7c44e986204b7d26f2aa97: gravity present,
  particles ACTIVE, densities correct, min_young_modulus stale (led to BF3).
- Post-fix S1 (seal 686c273a...): S1 r1 job 8058a2cc87da4f48965199be09b1a2c9 —
  material dynamics ENGAGE (gravity/friction stress vm ~ 640-750 Pa mean,
  ~2280 Pa max) while the driven piston passes through the block with ZERO
  effect (h constant to 1e-7; vm unaffected during the 0.5-1.0 s descend;
  piston overlap up to ~1.5 cm inside the specimen volume).
- The declared P1.1 outcome (no compression signature) is therefore a REAL
  recorded R5 failure, deterministic, and not an artifact of stiffness,
  gravity, or the drive kernel (kernel writes verified by diagnostic).
B.2 AMENDMENT (mechanism only — protocols, strokes, velocities, timings,
predictions and tolerances of v1 Sections 2-5 are UNCHANGED): replace all
kinematic PARTICLE boundaries (pistons, end walls) with kinematic RIGID BODY
colliders, the solver-supported path documented in implicit_mpm_model.py:
"Rigid body colliders will be treated as kinematic if their effective mass is
zero ... bodies flagged with newton.BodyFlags.KINEMATIC have zero effective
mass", with shapes flagged COLLIDE_PARTICLES; driven by direct body_q/body_qd
writes per the same declared velocity schedules (same phase timing, same
stroke). Fallback if the rigid path is itself infeasible on inspection: a
gravity-only redesign of the affected protocols, to be agreed with the
Lieutenant BEFORE implementation.
B.3 S1 reruns (r1/r2) after the Lt commits this amendment; then S2/S3/S4 r1/r2
as frozen otherwise. Determinism protocol (0.5 s whole-state sha256 pairs) is
unchanged.

## C. Declared proxy caveat (no change)

`w_el` in v1 Section 3 is a proxy: post-fix S1 shows NEGATIVE values
(sign/convention mismatch between state.mpm.particle_stress and
particle_elastic_strain). S4-P4.4 uses only CHANGES of w_el around the mid-run
switch (convention-independent); absolute w_el values are reported but no
absolute-energy claim is made.

## D. Execution-history note (recorded, no reruns)

Seal lineage: #1 4f234af6... (manifest 4b193533...) — thermal r1/r2; #2
5ffb4f37... (manifest 11cc479b...) — S1 r1 crash (BF1, preserved) + S1 r1
static outcome + S1 r2 crash (BF2, preserved); #3 f3337347... (manifest
0f447994...) — S1 r2 static outcome (byte-identical metrics to r1); #4
cc4b5570... (manifest 373a5a0c...) — sealed settle diagnostic; #5 b730cfd2...
(manifest 686c273a...) — post-BF3 S1 r1/r2. All pre-amendment receipts and
logs are preserved under E:/ChimeraWork/task-runner/results/<job>/.
