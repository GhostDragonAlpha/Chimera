# A1_XPBD BATTERY RESULTS — the coupled XPBD reference model, measured

**2026-09-14.** Agent B1x-xpbd-reference. The preregistered battery of
`PREREG.md` (bars P1–P6, falsifiers a–d), run against the CPU reference model
in `tools/xpbd_reference/` (pure Python + numpy; no engine edits, no live
calls — every input is the MEASURED table in `DIAGNOSTIC.md`). Raw numbers:
`battery_results.json` (this directory, written by the runner). Re-run:

```bash
python -m tools.xpbd_reference.run_battery --json battery_results.json
python -m tools.xpbd_reference.xpbd_reference_tests   # 17/17 PASS
```

Probe press used throughout (the world's own scale): the torso weight
m3·g = 122,634 N applied at the hip ring direction, 3 ticks, then released.
Divergence criterion (stated in code, `solver.DIVERGE_RATIO`): worst-cell
|dV|/V0 exceeds 1e3× the press-on amplitude, or goes non-finite.

## THE BAR TABLE

```
  BAR                         PREDICTED            MEASURED                       VERDICT
  ----------------------------------------------------------------------------------------
  P1 pressure recovery        miss < 1%            miss 2.87e-13 %                    PASS
  P1 at rest                  P=0, dV=0            maxP 0 Pa, maxdV 0    PASS
  P2 explicit       n=1         diverges            DIVERGES @t=5
  P2 explicit       n=2         diverges            DIVERGES @t=5
  P2 explicit       n=4         bounded             bounded (max 0.00)
  P2 xpbd           n=1         bounded             bounded (max 0.00)
  P2 xpbd           n=2         bounded             bounded (max 0.00)
  P2 xpbd           n=4         bounded             bounded (max 0.00)
  P3/falsifier(a) rigs @ n=4 (operating point, +-10% bar):
    cell 0  pred   907.5   measured   777.0   -14.4%   (derived -14.4%)
    cell 1  pred   842.8   measured   734.7   -12.8%   (derived -12.8%)
    cell 2  pred  1785.6   measured  1174.9   -34.2%   (derived -34.2%)
    cell 3  pred   420.3   measured   404.3   -3.8%   (derived -3.8%)
  P3/falsifier(a) coupled ring @ n=4:
    mode 0  pred  1949.0   measured  1222.7   -37.3%   (derived -37.3%)
    mode 1  pred  1364.0   measured  1019.1   -25.3%   (derived -25.3%)
    mode 2  pred   540.1   measured   507.5   -6.0%   (derived -6.0%)
  P3 model validation @ n=11 (fidelity) / n=32: worst misses 9.7% / 1.3%
  P3 chain witness (distributed inertia): 114, 63, 8 rad/s
  P4 servo reactions         dp=0, dL=0           dp 1.42e-14, dL 0.00281 kg.m2/s
  P4 pose-overwrite contrast dL != 0           dL 1.07 kg.m2/s
  P5 momentum (100 ticks)    drift < 0.1%         drift 3.98e-06%
  P6 balance stance        PASS
  P6 balance single_point  REFUSED
  P6 balance com_outside   REFUSED
  (d) wrong compliance      ratio V0             measured ['0.288', '0.335', '0.693', '12.509']
  (d) predicted V0 per cell ['0.288', '0.335', '0.693', '12.509']
  port: iters/tick mean 8.0 max 8; 7.57 ms/tick (python, 12-DOF chain)
```

## THE DIVERGENCE DEMO (falsifier b's headline)

Torso-weight press at the hip ring, 3 ticks, release. Amplitude = worst
|dV|/V0. The EXPLICIT update (the current architecture's idealization) blows
up 2.4e6× in 5 ticks UNDER THE SAME PRESS that the coupled XPBD solve at
n = 4 absorbs and decays (monotone decay continues to 1e-14 by tick 59):

```
  tick   explicit n=1            xpbd n=4
     0   1.817e-03            1.898e-05
     1   6.943e-02            3.379e-06
     2   2.763e+00            8.206e-06
     3   1.105e+02            1.615e-05
     4   4.428e+03  DIVERGED  6.876e-06
     5                        6.259e-06
     ...                      (decays to 1.089e-14 by tick 59)
```

The measured explicit growth rate, log(amplitude)/tick = 3.6878, matches the
DERIVED symplectic-Euler multiplier at eta = h·omega_max = 6.497
(|eig| = 40.18, ln = 3.6931) to 0.14% — the divergence is the derived
instability, not numerical noise.

## FALSIFIER VERDICTS

### (a) FREQUENCY — FIRED AS WRITTEN at n = 4; the named diagnosis refuted; amended bar measured and adopted

At the operating point n = 4 the stiff modes MISS the ±10% bar (worst: the
coupled 1949.0 rad/s mode reads 1222.7 rad/s, −37.3%). But the falsifier's
named successor diagnosis ("geometry or compliance is not the world's") is
REFUTED by the instrument: every measured miss equals the DERIVED
discrete-map bias of the converged XPBD substep,
`acos(1/sqrt(1+x^2))/x` with x = omega·h/n (from `measured.predicted_bias`),
to better than 0.05 percentage points — at every cell, every ring mode,
every probed n. The model IS the world's; the miss is the scheme's
O(h_sub^2) frequency bias, exactly derived. The n-scan closes the case:
worst miss 9.7% at n = 11, 1.3% at n = 32. AMENDED BAR (the prereg's own
protocol: the measured number replaces the prediction): the ±10% frequency
bar holds for n >= n_fidelity = ceil(omega_max·h / 0.603) = 11, where
0.603 is the root of acos(1/sqrt(1+x^2)) = 0.9x. At the operating point
n = 4 the solver CARRIES the derived bias as a calibration datum
(−14.4/−12.8/−34.2/−3.8% per cell; −37.3% on the coupled mode) — the
appliance must budget it or raise n when frequency fidelity matters.

### (b) BOUNDEDNESS — the prereg's named "conversely" branch fired: the coupled solve is bounded at EVERY probed n

XPBD n = 1, 2, 4 all stay bounded under the press (max amplitudes 4.5e-5,
2.8e-5, 1.6e-5 — press-on scale, then decay). The eta < 2 substep law is the
EXPLICIT family's law, and the explicit family measures exactly where
derived: DIVERGES at n = 1 and n = 2 (both at t = 5; the prereg predicted
"n = 1 within 3 ticks" — measured 5, the measured number replaces the
prediction per the falsifier's own text), BOUNDED at n = 4. MEASURED
BOUNDARY, replacing the prediction: the IMPLICIT coupled solve has no
stability-driven substep floor on this world's press; n = 4 remains the
OPERATING POINT (the derivation's 23% stability headroom at the residual
eta = 1.62, plus frequency fidelity per (a)), not a stability cliff. The
theory's confirmation stands in the demo: the press that kills the explicit
update in 5 ticks is absorbed and decayed by the coupled solve.

### (c) PRESSURE LAW — never fired

P = lambda/h_sub^2 vs the engine's own law P = −dV/(kappa·V0): worst miss
2.87e-13 % under full press (bar: 1%). The per-cell press-on pressures read
[17838.9, 11893.7, 555.0, −759.5] Pa and satisfy both laws simultaneously.
At rest: max |P| = 0 Pa, max |dV|/V0 = 0 exactly. The sign convention check
(compress a cell → P > 0) passes. Astra's lambda recovery is correctly
signed and scaled.

### (d) NEGATIVE CONTROLS — both fire as predicted

* Wrong compliance (alpha = kappa, V0 dropped): the pressure check FAILS by
  the predicted ratio — P_wrong/P_true = V0 per cell, measured
  [0.288, 0.335, 0.693, 12.509] vs predicted V0 = [0.288, 0.335, 0.693,
  12.509] (worst-cell check miss 1151%, i.e. three orders of magnitude of
  wrongness, as V0 spans three orders).
* The balance gate REFUSES the single-point-contact "balance": its FORCE
  gate alone PASSES (n = W is feasible, friction slack 108,458 N) — the
  refusal comes from the SUPPORT gate (margin 0.0, a point has empty
  interior) and the MOMENT gate (required moment arm torque 0.0 Nm slack —
  a measure-zero knife edge). COM outside the support is refused by all
  three gates. The real two-foot stance PASSES all gates (support margin
  8.77 cm, friction slack 54,229 N). Balance is its own gate, exactly as
  the prereg separated it.

## P4/P5 (coupling and momentum)

* P4 — servo REACTION forces: the solve drives the knee from rest through an
  equal-and-opposite torque pair (row shape asserted in tests); net linear
  momentum stays at 1.4e-14 and angular transport is 2.8e-3 kg·m²/s over 20
  ticks. The POSE-OVERWRITE contrast (the current `joint_deg_` architecture,
  idealized as a direct pose write) injects dL = 1.065 kg·m²/s in the same
  run — 380× the solve's transport floor, with zero force having produced
  it. P4 is where the two architectures differ, measurably.
* P5 — momentum conservation (gravity off, no contacts, consistent
  rigid-field start, 100 coupled ticks): linear momentum drift 1.1e-11
  (exact to fp), angular drift 1.1e-3 of |L0| = 21,936 — total 3.98e-06 %
  against the 0.1% bar: four orders of magnitude of margin. From a
  constraint-VIOLATING impulse start the angular transport is bounded at
  0.055 kg·m²/s (reported, not a bar).

## WHAT THE MEASUREMENTS CORRECTED IN THE PREREG

1. **P3's tolerance guess was wrong; the exact map replaces it.** "XPBD at
   n = 4 carries O(h_sub^2) frequency error; 10% is the stated tolerance"
   under-estimated the constant: the measured n = 4 bias is up to −37.3%.
   The battery derived the EXACT converged-substep map (not an expansion),
   verified it against the solver to <0.05 pp at 21 (mode, n) points, and
   the amended bar is n >= 11 for ±10% (n = 32 validates the model itself to
   1.3%). The prereg's falsifier-(a) successor machinery (refit compliance
   from the miss) is moot — the miss has no model term.
2. **P2's divergence predictions belonged to the wrong family.** "n = 2
   diverges within 10 ticks; n = 1 within 3" measured as: the EXPLICIT
   family diverges at n = 1 and n = 2, both at t = 5; the IMPLICIT coupled
   solve is bounded at every probed n including n = 1. The eta < 2 law is
   re-attributed to the explicit update (where it lands exactly: growth rate
   3.6878 vs derived 3.6931/tick); the implicit solve's measured stability
   boundary on this press is n = 1. The n = 4 operating point stands on the
   derivation's headroom plus the fidelity bar, not on a measured cliff.
3. **NEW datum the prereg did not name: the discrete frequency bias map**
   (`predicted_bias`/`predicted_decay` in `measured.py`) — the per-mode
   frequency bias and numerical damping a converged XPBD substep carries at
   any (omega, n). This is a calibration input the appliance inherits.
4. **NEW port finding: the stopping criterion.** The first shipped solver
   tested RAW |C| against a rigid-sized tolerance; a compliant constraint's
   converged state is C = −(alpha/h^2)·lambda != 0, so under load the loop
   burned its 200-iteration cap on idempotent solves (measured: 800
   iterations/tick, 213 ms/tick, parallel wall 327.4s gated by one probe).
   Fixed to test the REGULARIZED residual r = C + (alpha/h^2)·lambda: 8
   iterations/tick, 7.57 ms/tick, bars unchanged (differences only at fp
   noise: P1 miss 2.1e-14 → 2.9e-13 %). The appliance ports the regularized
   test, not the raw one.

## PORT-READINESS (for the membrane_tick appliance lane, DESIGN.md's consumer)

* The solver IS the appliance's shape: stack [volume | joint | servo |
  contact] -> one regularized solve -> Jacobian refresh -> position
  correction -> consistent velocity update. `SolveReport` already carries
  the `/xpbd_state` fields (iterations, substeps, per-cell P, residual).
* Constraints vectorize as rows; the 12-DOF chain runs 8 iterations/tick at
  7.57 ms/tick in pure Python — the C++ appliance budgets from the
  iteration count (2 per substep at n = 4), not the Python wall.
* The SlabChain witness (the full planar chain, distributed slab inertia,
  servo compliance 1° droop under full torso load) reads its dominant axial
  response at 114/63/8 rad/s — far below the water pistons: the chain's
  SOFT joint-servo modes, not the sealed water, own the low spectrum. Both
  families live in one constraint stack there and the solve handles both
  (the pins are rigid rows, alpha = 0; the pistons are compliant; the
  servos are intents) — the exact stacking the appliance must reproduce.
* Balance: the P6 gate (support-interior + force + moment) is the stance
  bar to port alongside the solve; the force-only test is measured
  insufficient (it passes on a knife edge).

## PARALLELIZATION NOTE (operator's standing rule 2026-09-14)

The battery runs as 35 INDEPENDENT atomic probes mapped over a 32-worker
`multiprocessing` spawn pool with I/O overlapped (progress line + partial
JSON rewrite after every probe). MEASURED, same code: serial 14.5 s vs
parallel 8.5 s wall post-fix; the pool's decisive case was the pre-fix
world, where one 314 s straggler gated the serial order (parallel wall
327.4 s) — and any future heavy probe joins the pool instead of the critical
path. Probes are deterministic and schedule-independent: parallel and serial
runs return identical numbers. In-probe numpy is vectorized but the dense
solves are 3x3–12x12 (BLAS overhead exceeds arithmetic); the probe is the
unit of parallelism.

 (Agent: B1x-xpbd-reference)
