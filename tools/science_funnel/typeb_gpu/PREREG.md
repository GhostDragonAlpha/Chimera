# PREREG — TypeB-P2 batched GPU physics feasibility probe (2026-09-21)

Rule 0 preregistration, written and committed BEFORE any throughput number or
fidelity number was measured. Trailer Agent: GLM 5.3.

## ADDENDUM (2026-09-21, pre-run amendment — the prereg's glue arithmetic was wrong)

A smoke NaN exposed it before any measurement existed. Two errors, both fixed
by deriving rather than patching:

1. ARITHMETIC: the prereg wrote k_glue = 60,000 N/m, but its own formula
   E_glue*(t*s)/g_gap with the stated numbers gives 6e7 N/m (1000x). Caught
   because the initial state then carried a 103 kN glue force (a 1.7 mm
   stretch at 6e7 N/m), exploding the very first tick.
2. GEOMETRY: the 0.05 m "glue gap" was invented to dodge stiffness, not
   derived. Bonded membranes touch; the glue layer thickness IS the gap.
   Corrected: L_glue = 0.002 m (the bond line, = membrane thickness).

Corrected chain: k_glue = E_glue*(t*s)/L_glue = 2e9 * 0.0015 / 0.002 =
1.5e9 N/m. At the engine's dt = 1/300 this is EXPLICITLY UNINTEGRABLE in one
step (worst free-free vertex omega ~ 7.4e4 rad/s => omega*dt ~ 148 >> 2), so
the tier REQUIRES substepping, and the substep count is derived from the same
stability margin as everything else: omega*dt_sub <= 1.557 gives n_sub = 159.
(Second pre-run correction, also falsified numerically before any measurement:
the frequency bound must carry the factor 2 of FREE-FREE vibration — a bond
connects two dynamic vertices, pair mode sqrt(2k/m); the first bound without
it measured omega*h = 2.198 > 2 and NaN'd both backends identically.)

This is a FINDING of the probe, preregistered before the run: explicit
semi-implicit Euler at 300 Hz cannot carry the sourced bond stiffness; the
full-body port needs implicit bonds/constraints, or pays the substep cost
measured below.

Predictions affected: P1 throughput now includes 159 substeps/tick
(477 kernel launches/tick, predicted launch-overhead-bound ~1e7 env-steps/s
aggregate at 16384, range 3e6..3e7); P3 one-step error now accumulates over
159 float32 substeps, predicted <= 1e-4 (bar unchanged; may fire, honestly
reported). All falsifiers unchanged.


## ADDENDUM 2 (2026-09-21, still pre-run — probe design corrections from smoke)

1. MATCHED INIT MUST BE QUANTIZED: the rest layout is not f32-exact; casting
   it only on the GPU side plants a ~1e-7 m position difference which at
   k_glue = 1.5e9 N/m is a ~150 N phantom force. Both backends now start from
   f64-of-f32 initial states. FINDING for the tier: any CPU<->GPU state
   transfer at stiff bonds must quantize through the training precision.
2. PERTURBATION SCALE: a 1 mm position kick excites the bond mode at ~kJ
   (free-fall launched itself 8 m). The fidelity probe therefore runs TWO
   regimes per case: quiescent (velocity-only kick ~ 20 N forces — the f32
   noise floor) and energetic (the original 1 mm kick — the boundedness
   envelope). F-PARITY-ONESTEP is judged on the quiescent one-step; the
   energetic regime is governed by F-PARITY-BOUNDS only. P3 prediction
   refined: quiescent one-step pos_rel <= 1e-5; energetic one-step <= 1e-4
   (may fire, reported honestly).

## ADDENDUM 3 (2026-09-21, post-first-full-run — batch-isolation confound resolved)

The first full run FIRED F-BATCH-COUPLING as written: env0 in-batch vs solo
pos_rel = 1.08e-1 (energetic regime) against the prereg bar 1e-5. Diagnostics
run before any verdict was recorded:

1. GPU solo-vs-solo run-to-run variance in the energetic regime is ~1.1e-1 —
   the atomic-add ORDER of the f32 spring reduction is nondeterministic (one
   env's springs can straddle a warp boundary) and the energetic regime
   amplifies rounding to that level.
2. 5v5 repetition study (quiescent): solo-vs-solo envelope 1.5e-6; batch-vs-
   solo median 3.2e-5, max 3.4e-5 — exceeds the envelope consistently.
3. Neighbor-independence check: with UNRELATED neighbor states at batch
   2/8/16, env0's offset from solo is 1.4e-4/1.1e-4/1.1e-4 — and batch=8 vs
   batch=16 (different neighbor sets) are BIT-IDENTICAL. The offset tracks
   launch configuration, never neighbor state; cross-env data flow is also
   structurally impossible (env-private force slots).

FINAL READING, reported red-with-numbers: F-BATCH-COUPLING stands FIRED as
operationalized (batched env0 does not reproduce solo env0 within 1e-5). The
diagnosed cause is reduction-order rounding across launch configs, NOT
lane-contamination (envs evolve independently; the contamination claim
itself is not falsified). Tier implication: training over batched envs is
unaffected; any exact-replay/byte-reproducibility claim requires a
deterministic reduction (sorted spring order or per-vertex thread ownership)
and is out of this probe's scope.

## STATEMENT (disagreeable)

Chimera's minimal representative dynamics slice — mass-spring triangle-mesh
membranes joined by glue bonds, under gravity, against the engine's penalty
ground-contact law, integrated at the engine's dt = 1/300 — batched in NVIDIA
Warp on one RTX 4090 delivers (a) aggregate env-step throughput far above the
CPU reference's 9.68 ticks/s, at VRAM cost well inside the card, and (b)
per-step and 300-tick behavior numerically consistent with a float64 CPU
reference of the IDENTICAL equations, bounded in both free-fall and contact.

This is a feasibility existence proof for the tier (lane P1 throughput + P2
discrepancy kind-2 evidence). It is NOT the full membrane-body port and does
not forecast full-body throughput (lane warning honored: a fast isolated
spring kernel does not satisfy a claim about full membrane-body rollouts).

## EQUATIONS (single source of truth, identical on both backends)

All constants derive, none tuned; chain per repo source:

- Gravity: g = 9.81 m/s^2 down (ChimeraEngine/engine/membrane_tick.cpp:45,
  `G_EARTH`), engine tick 3.34 ms => dt = 1/300 s (300 Hz convention, lane doc).
- Integrator: semi-implicit Euler, velocity then position
  (membrane_tick.cpp:865-867: `root_vy_ += ... * dts; root_y_ += root_vy_ * dts`).
- Membrane: 1.5 m x 1.5 m skin sheet, 3x3 vertices (s = 0.75 m spacing),
  thickness t = 0.002 m, material mat.skin (E = 15 MPa, rho = 1100 kg/m^3,
  tools/matter_kernel/constants.py). Mass DERIVED: M = area x t x rho
  (matter_kernel/definition.py:71) = 4.95 kg; per-vertex m = M/9 = 0.55 kg.
  Springs on the 12 structural edges per membrane (36 total); no diagonals.
- Membrane spring stiffness (continuum correspondence, grid-independent):
  k = E * t = 30,000 N/m (each edge carries cross-section t*s over length s).
- Glue bond (B2 law, tools/matter_kernel/glue.py: a bond is a THIRD material):
  k_glue = E_glue * (t*s) / g_gap with mat.wood_glue E = 2 GPa, gap g = 0.05 m
  => k_glue = 60,000 N/m. 6 bonds (3 per seam x 2 seams).
- GEOMETRY DERIVED FROM STABILITY, not taste: semi-implicit Euler on a spring
  is stable iff omega*dt < 2. Worst membrane vertex (4 springs):
  omega = 3*sqrt(E/rho)/s => s > 0.584 m; taken s = 0.75 m (margin: omega*dt
  = 1.56). Glue vertex: k_glue <= (2/dt)^2 * m - 2k => g_gap > 0.0217 m; taken
  g_gap = 0.05 m (same 1.56 omega*dt margin). dt is FIXED by the engine; E, rho
  FIXED by the sourced table; the only free geometry follows from their product.
- Ground contact (engine law verbatim, membrane_tick.cpp:842-860): per vertex,
  depth = max(0, -y); F = k_g*depth + c_g*max(0,-vy); F capped at 50*m*g.
  k_g = m*g/0.01 (engine's own rest-sink derivation, GAIT_SINK comment: k*s=m*g,
  sink 1 cm) = 539.55 N/m; c_g = 2*sqrt(k_g*m) (critically damped, restitution-
  free) = 34.49 N s/m.
- Body: 3 membranes chained along x with 0.05 m glue gaps; 27 vertices,
  42 springs, 14.85 kg total.

## PREDICTIONS (made before measurement)

- P1 throughput: launch-bound; predicted order of magnitude 1e8 aggregate
  env-steps/s at batch 16384 (acceptable range 3e7..5e8); monotonically rising
  in batch size over 1024/4096/16384.
- P2 VRAM: state at 16384 envs = 10.6 MB; process VRAM dominated by CUDA/Warp
  context; predicted < 1.5 GB total, < 1 MB per env marginal.
- P3 one-step fidelity: relative error (scaled norm, 1 + ||x||_inf denominator)
  <= 1e-5 per step; free-fall 300-tick relative error <= 1e-2, contact case
  <= 1e-1, both BOUNDED (no NaN, no divergence) — the slice is linear springs
  + one piecewise-linear contact, no chaotic amplification expected.

## FALSIFIERS (named before the run)

- F-GPU-TRAINING-BUDGET (lane P1): fires if aggregate env-step throughput at
  batch 16384 < 968 steps/s (100x the banked CPU 9.68 ticks/s).
- F-GPU-MEMORY (lane P1): fires if VRAM exceeds 24 GB or 1 MB/env marginal.
- F-PARITY-ONESTEP (lane P2 kind 2): fires if one-step relative error > 1e-4.
- F-PARITY-BOUNDS (lane P2): fires if the GPU 300-tick rollout NaNs or exceeds
  1.0 relative error vs the float64 reference, in EITHER free-fall or contact.
- F-BATCH-COUPLING (lane P1): fires if env0 run inside a batch differs from
  env0 run solo by > 1e-5 relative after 300 ticks.

A fired falsifier is reported as fired, with numbers. Nothing is re-tuned to
turn a red green.
