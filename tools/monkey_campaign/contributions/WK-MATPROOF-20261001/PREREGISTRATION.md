# PREREG DRAFT v1 — Material Proof Specimen Battery (wk-proof-material)

Status: DRAFT for Lieutenant commit. Gated execution is forbidden until the
Lieutenant commits this prereg and hands back the pin SHA. This document is
written before any specimen run. No specimen has been executed yet — not even a
smoke run — under the preregistration law.

- Lane: `E:/ChimeraWork/monkey-coordination/material-proof/`
- Worker: wk-proof-material
- Date: 2026-09-29
- Selected backend (verified on this host, see EVIDENCE.md for hashes of this
  verification): pinned env `E:/ChimeraWork/envs/newton/Scripts/python.exe`,
  Python 3.13.5, newton 1.6.0, warp-lang 1.17.0. C:/Python314 (stale newton
  1.3.0/warp 1.15.0) is NOT used.
- Structural template:
  `E:/ChimeraWork/envs/newton/Lib/site-packages/newton/examples/mpm/example_mpm_multi_material.py`
  (register_custom_attributes, disjoint per-material fills, two-state swap loop,
  `project_outside`, final predicate check).
- Solver: `newton.solvers.SolverImplicitMPM`
  (`E:/ChimeraWork/envs/newton/Lib/site-packages/newton/_src/solvers/implicit_mpm/solver_implicit_mpm.py`).

## 0. Verified backend facts this prereg relies on (source-inspected 2026-09-29)

1. NO thermal capability anywhere in the implicit_mpm package:
   `grep -ril thermal` over
   `.../newton/_src/solvers/implicit_mpm/` returns 0 files. This is the known
   missing capability and forces the external thermal companion (Section 6).
2. Float `wp.atomic_add` in force scattering: solver_implicit_mpm.py lines
   4011, 4015, 4019 (particle forces) and 4096 (body forces). Library-level
   determinism risk (Risk R2).
3. Capability extrema are CACHED AT MODEL BUILD:
   `implicit_mpm_model.py` lines 400-403 compute `min_young_modulus`,
   `max_hardening`, `has_viscosity`, `has_dilatancy` from active material
   parameters; no refresh method was found. Therefore mid-run parameter
   changes are restricted to VALUE-ONLY changes within features that are
   already enabled (nonzero somewhere) at build time (Risk R3). All sweep
   points that change feature enablement rebuild model+solver fresh.
4. Per-particle material attributes (model.mpm.*): young_modulus (default
   1e15 Pa), poisson_ratio (0.3), damping (s, default 0), friction (0.5),
   yield_pressure (1e15 Pa), tensile_yield_ratio (0), yield_stress (0 Pa),
   hardening (0), hardening_rate (1), softening_rate (1), dilatancy (0),
   viscosity (Pa.s, 0).
5. Per-particle state (state.mpm.*): particle_qd_grad (mat33),
   particle_elastic_strain (mat33), particle_Jp (f32),
   particle_stress (mat33, Cauchy), particle_transform (mat33).
6. Yield surface is Drucker-Prager-like and rate-dependent:
   compressive/tensile pressure caps, deviatoric yield stress s_max,
   frictional term mu*p, dilatancy, viscosity (rheology_solver_kernels.py,
   YieldParamVec layout lines ~40-70, shear_yield_stress lines ~92-110).
   Viscosity enters as purely dissipative flow viscosity: this is
   viscoplastic (Bingham-type) behavior, NOT Maxwell viscoelasticity.
7. `mpm.damping` (elastic damping relaxation time, seconds) enters the elastic
   stress update as `alpha = 1/(1 + damping/dt)`
   (implicit_mpm_solver_kernels.py line 526): a genuine candidate
   stress-relaxation mechanism that MUST be probed, not assumed (Section 3).
8. Kinematic boundary: particles with mass=0/density=0 act as infinite-mass BC
   (example template line ~106). The piston drive used here writes kinematic
   particle q/qd directly (Risk R5: out-of-example-API drive).

## 1. Common rig and protocol (all specimens)

- Device: warp CPU (`device="cpu"`). GPU is not used unless a specimen is
  demonstrated insufficient on CPU, in which case the GPU queue at
  E:/ChimeraWork/gpu-queue/ per PROTOCOL.md is used and this prereg is amended
  before the GPU run.
- Numerics: frame_dt = 1/60 s, sim_substeps = 2 (sim_dt = 1/120 s), voxel_size
  0.02 m (S1/S2) or 0.04 m (S3/S4), SolverImplicitMPM.Config tolerance=1e-6,
  max_iterations=250, solver="auto", grid_type="sparse".
- Ground: `builder.add_ground_plane()`; ground z=0.
- Piston: kinematic particle block (density=0) driven by direct writes of
  particle_q (displacement) and particle_qd (velocity BC) each substep:
  drive phases q += qd*dt; hold phases qd=0.
- Materials (SI): base elastic E=1.0e5 Pa, nu=0.3, rho=1000 kg/m^3 unless a
  specimen declares otherwise. Yield disabled means yield_pressure=1e9 Pa and
  yield_stress=1e9 Pa (declared peak stresses stay below ~1e6 Pa).
- Particle placement: `builder.add_particle_grid` with jitter=0.0 (declared
  deviation from the example template's jittered fill, chosen so initial
  conditions are exactly reproducible across processes; a regular lattice is
  the standard MPM particle layout).
- Specimen particle set: contiguous index range recorded at build; all metrics
  computed over that range only (piston/wall particles excluded).
- Gravity: 9.81 m/s^2 down for S1/S2; 1.62 m/s^2 (declared reduced gravity,
  chosen so predicted deposit thicknesses are resolvable at voxel 0.04 m) for
  S3/S4.
- Metrics (exact definitions):
  - height h(t) = p95(z) - p05(z) over specimen particle z.
  - von Mises sVM(t) = sqrt(3*J2) of the stress deviator, volume-unweighted
    mean over specimen particles, from state.mpm.particle_stress.
  - COM x(t), v_com(t) = central difference of COM x over a 5-frame window.
  - runout R = max(x) - min(x) over specimen particles at declared frames.
  - residual height h_res = h at final free frame.
- Determinism: EVERY specimen is run at least twice from identical initial
  conditions and code (two independent process invocations). At every 0.5 s
  checkpoint, a whole-state hash
  H_k = sha256(concat(raw little-endian bytes of particle_q, particle_qd,
  mpm.particle_stress, mpm.particle_Jp, mpm.particle_elastic_strain,
  mpm.particle_transform)) is recorded.
  P-D (determinism prediction): H_k identical across repeated runs.
  ANY hash divergence is recorded as a FINDING (Risk R2); the run is never
  silently retried until hashes match.
- Outputs per run: summary JSON (predictions vs measured, pass/fail), metrics
  CSV, checkpoint hash file. All sealed through the task-package runner with
  --keep; hashes recorded in material-proof/EVIDENCE.md.

## 2. Specimen S1 — elastic recovery (residual-strain bound)

Rig: cube L=0.16 m at voxel 0.02 (9^3 = 729 particles), piston footprint
0.24 x 0.24 m. Material: elastic-only (yield disabled, viscosity 0, damping 0,
friction 0.5).
Protocol: settle 0.5 s; piston bottom starts 2 mm above the measured settled
block top at t=0.5 s (declared adaptive contact, prevents a missed-contact
run), descends at v = (0.1*h0 + 0.002 m)/0.5 s for 0.5 s (nominal 10% strain
plus the 2 mm gap closure), hold 0.5 s, retract to start over 0.5 s, free
evolution 1.0 s. h0 = height at t=0.5 s (post-settle).

Predictions:
- P1.1 (hold height): h(hold)/h0 in [0.88, 0.92].
- P1.2 (residual strain): |h_final - h0|/h0 <= 0.03.
- P1.3 (containment): min z of ALL particles > -0.05 m (template's
  test_final predicate).
Refinement checks (only if P1.1/P1.2 fail): halve dt (sim_substeps=4), then
halve voxel (0.01); the metric direction must improve or stay stable; every
refinement run is recorded; no tolerance is edited after seeing results — a
genuine failure is preserved and reported as a finding.

## 3. Specimen S2 — relaxation probe (characterize actual behavior)

Two arms, both cube L=0.16 m, voxel 0.02, same adaptive piston contact as S1:
settle 0.5 s, piston bottom starts 2 mm above the settled top, compress to
nominal 5% strain (stroke = 0.05*h0 + 0.002 m) over 0.5 s, hold 3.0 s, retract
over 0.5 s, free 1.0 s.

Arm A (damping knob): elastic-only material (yield disabled, viscosity 0) with
mpm.damping tau in {0.05, 0.1, 0.2, 0.4} s. Fresh model+solver per tau.
- H-A1 (relaxation exists): with tau>0, sVM(t) decays during hold; tau=0
  control shows no monotone decay beyond 5% of sVM peak.
- H-A2 (timescale): exponential fit of sVM(t) over the window where sVM is in
  [0.2, 0.8]*sVM_peak yields tau_fit within a factor [0.5, 2.0] of nominal
  tau; tau_fit monotonically nondecreasing across the sweep.
- H-A3 (dissipation ordering): post-release height recovery decreases with
  tau: h_rec(tau=0.05) > h_rec(tau=0.4) strictly.

Arm B (viscosity knob): yield_stress=500 Pa, damping=0, viscosity eta in
{0, 50, 500, 5000} Pa.s. Fresh model+solver per eta.
- H-B1 (eta=0 control): no relaxation beyond 10% of sVM peak during hold
  (rate-independent plateau at the yield envelope).
- H-B2 (eta>0): sVM decays during hold toward a NONZERO plateau; the
  1/e excess-decay time grows monotonically with eta.
- H-B3 (permanent set): residual strain is nondecreasing with eta.

Claims this probe MAY make:
- Arm A: the backend supports stress relaxation under held deformation with a
  per-particle relaxation-time parameter (mpm.damping, implemented as
  alpha = 1/(1 + tau/dt)); measured timescales as characterized.
- Arm B: the backend supports rate-dependent (viscoplastic) flow; held stress
  above yield relaxes only toward the yield envelope, never to zero.
Claims this probe MUST NOT make:
- That the backend implements Maxwell viscoelasticity (no recoverable viscous
  strain storage exists; viscosity is yield-surface flow viscosity only).
- Any frequency-domain modulus, broadband relaxation spectrum, or
  creep-recovery symmetry claim.
If Arm A shows decay inconsistent with a single timescale, the measured curve
is recorded and reported as-is (characterization, not curve fitting beyond the
declared tau_fit diagnostic).

Mid-run changes: none in S2. Stored-energy accounting: S2 computes the elastic
energy proxy W_el = sum_p 0.5 * sigma_p:eps_p * V_p (V_p = mass_p/rho,
eps_p from particle_elastic_strain) at hold start, hold end, and release end;
reported with each run.

## 4. Specimen S3 — sustained flow (arrest by yield stress)

Rig (reduced gravity 1.62 m/s^2): channel x in [-0.6, 0.6] m with kinematic
end walls; block 0.24 x 0.24 x 0.16 m at voxel 0.04 on the ground; material:
E=1e5, yield_pressure=1e9, tensile_yield_ratio=1.0, yield_stress=600 Pa,
viscosity=50 Pa.s, friction=0.1, damping=0. Pusher piston (kinematic wall,
footprint 0.28 x 0.28 m at z in [0.02, 0.14]) drives the -x face at
v=0.2 m/s for 1.0 s (0.2 m stroke), then stops.
- P3.1 (flow under load): during the push window, v_com >= 0.05 m/s and the
  top-decile/p05-layer x-displacement difference (shear measure) >= 0.02 m.
- P3.2 (arrest): after the pusher stops, |v_com| < 0.005 m/s within 1.0 s and
  remains < 0.005 m/s for the final 1.0 s.
- P3.3 (stability): R grows by < 2% between t=3 s and t=4 s.
- P1.3 containment predicate applies.

## 5. Specimen S4 — yielding under parameter change (sweeps)

(a) yield_stress sweep on the S3 rig: Y in {300, 600, 1200, 2400} Pa, fresh
model+solver per point (capability-flag constraint, Section 0.3).
- P4.1 (ordering): runout R(Y) strictly decreasing across the sweep, with
  adjacent ratio R(Y_i)/R(Y_{i+1}) > 1.05.
- P4.2 (deposit thickness): final deposit height h_end increases with Y
  (nondecreasing across the sweep).
- The relaxation-time-scale sweep required by the tasking is Arm A of S2
  (tau at fixed E, tau ~ effective timescale); cross-referenced here.

(b) Mid-run change specimen S4m: S3 rig at Y=300 Pa; pusher drives
t=0.5..1.5 s as in S3; at t=1.0 s (MID-PUSH, so the change is observable) set
mpm.yield_stress := 2400 Pa on all specimen particles (VALUE-ONLY change; the
yield feature is already enabled at build; no capability flag flips — Section
0.3), push continues to 1.5 s, observe to t=4.0 s.
- P4.3 (arrest after stiffening): runout growth R(1.5)-R(1.0) in S4m is less
  than half the same-window growth of the preregistered Y=300 sweep point
  (S4a cross-reference); v_com < 0.005 m/s by t=2.5 s.
- P4.4 (stored-energy account): W_el computed one frame before the switch,
  one frame after, and at t=4.0 s; the step delta W_el at the switch is
  reported explicitly. NO energy-conservation claim is made across the
  switch: the parameter change is external bookkeeping with a declared,
  reported stored-energy discontinuity.

## 6. External thermal companion — SEPARATELY SCOPED, NOT NEWTON'S SOLVER

Scope: a deterministic CPU companion model in pure NumPy float64 that
demonstrates (i) heat conduction and (ii) conversion of mechanical dissipation
into thermal energy. It is EXPLICITLY NOT Newton's solver and makes no claim
about the backend; the backend has no thermal capability (Section 0.1).

Model: 1D bar, L=1 m, 201 nodes, insulated ends, explicit FTCS,
alpha=1e-4 m^2/s, dt = 0.4*dx^2/alpha (stability factor 0.4), volumetric heat
capacity normalized to 1. Mechanical source: prescribed plastic-work rate
density P(x,t) = P0 * exp(-((x-x_c(t))^2)/(2*0.05^2)) with
x_c(t) = 0.5 + 0.2*sin(2*pi*t/2), applied for t in [0, 2] s, P0 chosen so the
mechanical work totals W_mech = 100 (normalized J). Taylor-Quinney
coefficient beta = 0.9. Simulation t in [0, 20] s.

Predictions:
- T1 (conversion closure): |E_th(4 s) - beta*W_mech| / W_mech <= 1e-9.
- T2 (conduction decay): after source off, spatial variance of T decays as
  exp(-2*pi^2*alpha*(t-2)/L^2); fitted rate over windows [2,3] s and [3,4] s
  within 5% of the analytic rate.
- T3 (equilibration): max-min T at t=20 s <= 1% of mean temperature rise.

Interface statement (where coupling would attach if the backend gained
thermal): post-step in the driver loop — per-particle plastic dissipation
rate D_p = sigma_p : epsdot_p from state.mpm.particle_stress and
state.mpm.particle_qd_grad, accumulated with Taylor-Quinney beta into a
per-particle temperature custom attribute (registered via
builder.add_custom_attribute, as the mpm attributes are), with a conduction
pass over the MPM grid or particle neighborhoods. None of this exists in the
backend today; this companion is the standalone demonstration of the physics,
labeled external.

## 7. Named risks (carried verbatim from tasking + verified additions)

- R1: SolverImplicitMPM is UNMEASURED on this host. The adoption baseline
  recorded Newton 1.6.0 particle divergence on OTHER solvers
  (SemiImplicit/XPBD cloth). Any divergence/NaN/lithiation-style blowup here
  is preserved and recorded as a finding; it is never a retry-until-pass.
- R2: the MPM path uses float wp.atomic_add (verified lines 4011/4015/4019,
  4096): repeated-run whole-state hashes may diverge. Any divergence is a
  recorded finding per specimen; determinism is claimed only when hashes are
  equal.
- R3 (verified addition): capability extrema cached at model build
  (implicit_mpm_model.py:400-403) restrict mid-run changes to value-only
  changes within already-enabled features; sweep points rebuild fresh.
- R4 (verified addition): the backend claims unconditional dt stability, but
  accuracy at dt=1/120 s with E=1e5 Pa is unverified; refinement checks in
  S1/S2 cover this.
- R5 (verified addition): the piston drive writes kinematic particle q/qd
  directly (the template only uses static kinematic particles). If the drive
  is not honored (specimen unaffected), that is a recorded failure and the
  follow-up is an amendment proposing an alternative loading protocol — not a
  silent protocol swap.

## 8. Missing capabilities (declared)

1. Thermal: absent in the backend (verified 0 hits) — external companion
   required (Section 6).
2. Maxwell/linear-viscoelastic relaxation: absent; only elastic damping
   (alpha = 1/(1+tau/dt)) and yield-surface flow viscosity exist. S2
   characterizes what the actual behavior is; no viscoelastic claim.
3. Per-particle temperature attribute / conduction kernels: absent.
4. Mid-run feature-enable for material parameters: unreliable due to cached
   capability flags (R3); sweeps rebuild per point.
5. Anything else discovered during execution is recorded in
   material-proof/EVIDENCE.md as an addendum; this prereg is amended (v2)
   rather than silently stretched.

## 9. Failure preservation and execution protocol

- All runs go through the sealed task-package runner
  (`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`);
  exit 75 (BUSY) means wait 10 s and retry. GPU work, if ever needed, only
  via E:/ChimeraWork/gpu-queue/ per PROTOCOL.md.
- Every failed or divergent run keeps its receipt, logs, metrics CSV and
  checkpoint hashes; failures are recorded in EVIDENCE.md and reported to the
  Lieutenant. No tolerance, protocol or prediction is edited after results
  are seen; changes require a prereg amendment (v2) committed before the
  affected run.
- Refinement runs are declared per Section 2 and are themselves preregistered
  responses to declared failure modes (resolution/dt), not tuning.

## 10. Acceptance mapping (what "done" means for this lane)

- Prereg committed by the Lieutenant; pin SHA recorded in EVIDENCE.md.
- Battery executed sealed; per-specimen receipts, per-run state hashes,
  metrics CSVs, summary JSONs; EVIDENCE.md records sha256 of every
  load-bearing artifact.
- Findings report in the standing format: predictions vs measured per
  specimen, determinism verdict per specimen, thermal companion results,
  failures preserved, missing-capability addenda.
