# PREREG — TypeB GPU full-body port (2026-09-21)

Rule 0 preregistration, written and committed BEFORE any Phase-A/B/C code was
run. Branch `agent/typeb-gpu-fullport-20260921` (from
`agent/typea-command-adapter-20260921` @ `9808dc94`). Trailer Agent: GLM 5.3.

## STATEMENT (disagreeable)

The gait walk's full body — the 18-coordinate Oku walker (6-axis authored free
base + hip/knee/ankle/MP per hind leg + shoulder/elbow fore struts, the
Table-1 segment masses/inertias, 13 moving bodies), gravity, the plane contact
law (pair-min sole gap, velocity-gate arming, mass-metric active-set
projection with the discrete-cone Coulomb friction), the servo muscles (the
mass-normalized PD at the derived 4 Hz / zeta 0.8 with per-drive torque caps,
viscous damping and depletive actuator stores), and the reflex deterministic
core (contact-reset hybrid clock at T_CYCLE=0.71 with the touch classes,
the settle hold, the planted-strut IK hold, the fore stepping clock with the
replant law, the hind tables + height-hold feed-forward, the alternation
deadlines, the capture reflex, and the command adapter's channel) — runs
batched in NVIDIA Warp on one RTX 4090 as a training environment that (a)
sustains the uncommanded walk class (>=100 ticks in >=80% of 64 perturbed
seeds), (b) preserves the command adapter's authority law EXACTLY and its
grading DIRECTION, and (c) delivers aggregate env-step throughput at batch
1024 above 100x the CPU reference's 9.68 ticks/s, at VRAM well inside the
card.

## THE P2 FINDING, RESPECTED (bond stiffness)

P2 measured that the sourced glue-bond stiffness (k_glue = 1.5e9 N/m) is
EXPLICITLY UNINTEGRABLE at dt = 1/300 and demands 159 substeps or implicit
treatment. The walker's bonds are NOT glue springs: its bond network is
REVOLUTE JOINT CONSTRAINTS (hard bilateral constraints) plus the plane
contact — handled IMPLICITLY at the velocity level every substep (the
mass-metric projection IS the implicit solve; no penalty stiffness exists to
integrate). The remaining explicit stiffnesses are the servo PDs, derived at
omega_n = 2*pi*FS_HZ = 25.13 rad/s: omega_n*dt = 0.0838 << 2 at dt = 1/300,
and the scene contract integrates RK4 at substeps = 4 (dt/4, omega_n*dt_sub =
0.021). The integrable margin is MEASURED and reported in the receipt; the
159-substep cost class does not arise for this body. This IS the implicit
variant of the P2 finding, applied by the walk's own architecture.

## CPU REFERENCE (the behavior anchors)

The reference is the C++ `GaitWalker` at this branch's base commit `9808dc94`,
built natively on this machine (MinGW g++ 15.2.0, -O2): on the compiled scene
`scene.json` (sha256 e61ad386...) it reproduces the BANKED numbers exactly
(WAVE 38 ship: walk refused at tick 302, worst ledger 30.970714 J; fore lift
slots ~92.2/198.7; first hind lifts ~92-98). The GPU walk is judged against
that class, not byte-identity (f64 GPU vs f64 CPU: reduction order and
transcendental ulp differences remain; P2 measured this class of gap).

## SEED DISTRIBUTION (defined before the run; the C++ walk is deterministic)

Seed s in {0..63}: PCG64 stream seeded `s`; at reset, per unactuated-base
joint coordinate c in the 12 leg/fore drives: q[c] += U(-1,1)*1e-3 rad,
v[c] += U(-1,1)*1e-2 (rad/s); base x-speed v[3] *= (1 + U(-1,1)*0.02).
No other state varies. A seed SURVIVES tick t if no refusal fired, no NaN,
and base_trans_y >= 0.20 m (the collapse line: entry 0.386 m; a body below
0.20 m has folded off its ride height — not a walk). Survival horizon =
first failing tick; horizon = run cap (600) if never failing.

## PREDICTIONS (made before measurement)

- P-SURVIVAL: the median survival horizon is in the CPU class (137..302
  ticks); >=80% of seeds pass 100 ticks. The dominant GPU-side risk is
  late-walk divergence amplification of ulp differences (the CPU walk itself
  is chaos-bounded at 302 by the wave-38 calendar), not a porting defect.
- P-PROBE: free-fall over 120 ticks matches the analytic g = 9.80665 m/s^2
  drop to <1e-9 relative (f64); the stand/settle probe matches the CPU
  reference tick-by-tick to <1e-2 scaled max-norm over 60 ticks.
- P-AUTHORITY: the plant-law consumption is EXACT on the GPU
  (xoff = cmd*(DUTY_SAMPLED*T_CYCLE)/2 at the fire, to f64 rounding <1e-12
  relative); the achieved-speed spread across commands {0.0, 0.5, 1.0} m/s
  is POSITIVE and monotone but SUB-BAR (<0.05 m/s), reproducing the adapter
  receipt's open defect (the body-speed path is not owned by the plant
  target) — the port must REPRODUCE that defect, not fix it.
- P-THROUGHPUT: f64 per-env work is ~100x the P2 slice per env (14 bodies x
  18-coordinate Jacobians vs 27 verts x 42 springs); predicted 1e3..3e4
  env-steps/s aggregate at batch 1024 (i.e., 100x..3000x CPU), bounded by
  local-memory traffic, not FLOPs. Batch scaling monotone 1024 -> 4096.
- P-MEMORY: state < 10 KB/env; process VRAM dominated by the CUDA context
  (< 2 GB).

## FALSIFIERS (named before the run)

- F-FULLPORT-SURVIVAL: fires if fewer than 80% of N=64 seeds sustain
  >=100 ticks uncommanded (per the seed distribution above).
- F-FULLPORT-PROBE-PARITY: fires if the free-fall probe's measured mean
  acceleration deviates from 9.80665 m/s^2 by >0.01, OR the stand probe's
  60-tick tick-by-tick max scaled difference vs the CPU reference exceeds
  1e-2, OR any probe state NaNs.
- F-FULLPORT-CLASS: fires if the nominal (unperturbed) GPU walk does not
  produce >=1 hind step fire AND >=1 fore liftoff by tick 150 (the CPU class
  fires at ~92), or if the GPU walk's tick-0 state differs from the CPU
  reference's tick-0 state by >1e-9 (the port must start on the same entry
  state).
- F-FULLPORT-COMMAND-AUTHORITY: fires if the GPU plant-law consumption at
  the first post-command hind fire deviates from
  cmd*(DUTY_SAMPLED*T_CYCLE)/2 by >1e-9 (absolute), OR the mean achieved
  body speed over the post-command window is not monotone non-decreasing
  across commands {0.0, 0.5, 1.0} m/s.
- F-FULLPORT-THROUGHPUT: fires if batch-1024 aggregate env-steps/s
  (warm, median of 3 x 300 ticks) < 968 (= 100x the banked CPU 9.68).
- F-FULLPORT-MEMORY: fires if VRAM exceeds 24 GB or 1 MB/env marginal.

A fired falsifier is reported fired, with numbers. Nothing is re-tuned to
turn a red green. Deferred reflex laws (the fidelity manifest) are PORTED /
DEFERRED itemized in FIDELITY_MANIFEST.md BEFORE Phase C runs; a deferral
that turns out load-bearing for the survival bar is REPORTED as such, not
silently back-ported mid-measurement (any back-port = new prereg addendum,
committed before the re-run).
