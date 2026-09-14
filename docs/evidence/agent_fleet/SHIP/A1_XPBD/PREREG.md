# A1_XPBD PREREGISTRATION — the coupled XPBD volume solve (reference-model-first)

**2026-09-14.** Agent A12-xpbd-prereg. Rule 0: statement, prediction, falsifier —
BEFORE any solver code. No measured actuals appear here; every number below is a
PREDICTION derived from the measured diagnostic (`DIAGNOSTIC.md`,
`diagnostic_results.json`, produced by `tools/xpbd_diagnostic.py` against the
live engine, GET-only) and from cited constants. Build order: CPU reference
model first (the house battery pattern, `MATTER_KERNEL/B1_PREREGISTRATION.md`),
engine appliance second (`DESIGN.md`).

## SOURCE OF TRUTH FOR THIS LANE (Astra's answer, received 2026-09)

1. The volume constraint C_i(q) = V_i(q) − V0_i has physical compliance
   alpha_i = kappa*V0_i (kappa = 4.6e-10 Pa^-1, B = 1/kappa = 2.174 GPa).
   Pressure recovers as P_i = lambda_i/h^2 under Astra's sign convention.
2. The coupled XPBD solve: (J M^-1 J^T + Lambda/h^2) dlambda = −C − (Lambda/h^2)
   lambda, stacking volume + joint + servo-target + contact constraints;
   recompute the nonlinear Jacobians during iterations; update velocities
   consistently; servos must exert reaction forces — overwriting joint poses
   after the solve bypasses coupling and injects energy. (Our current
   architecture overwrites `joint_deg_` — that is the defect this prereg retires.)
3. Stability gate: eta = h*omega_max, omega_max^2 = lambda_max(M^-1/2 K_tangent
   M^-1/2), K_water ~ J_V^T diag(1/(kappa V0_i)) J_V. Explicit at 300 Hz demands
   omega_max < 600 rad/s (f < 95.5 Hz). First diagnostic: the piston mode,
   eta^2 = h^2 A^2/(kappa V0 * m_eff).
4. Stability and balance are SEPARATE gates: 6-DOF balance requires feasible
   contact forces producing force AND moment within friction/actuator limits —
   "a foot is grounded" does not establish it.

## STATEMENT

A sealed-cell XPBD solve with compliance alpha_i = kappa*V0_i, solved COUPLED
with the joint, servo and contact constraints at the substep count the piston
diagnostic demands (n = 4 at h = 1/300 s), is stable (bounded under any probe
press the world can deliver) AND conserves momentum AND answers the same
pressure law the engine already ships (dP = −dV/(kappa*V0)) — while the current
pose-overwrite servo architecture is none of those three things, and the
explicit single-step update at 300 Hz diverges on this world's own measured
stiffness.

## DERIVATION (from the measured diagnostic only — full tables in DIAGNOSTIC.md)

- World (measured, live ticks 3,197,795): 36,630 triangles, 18,459 vertices,
  4 sealed cells, V_whole = 13.8246 m^3 -> 13,824.6 kg at rho = 1000 kg/m^3.
- Cut-plane piston areas (validated slicer, cells pinned to the live volumes at
  ~2 ppm): A(ankle 0.338) = 0.175356, A(knee 1.903) = 0.254922,
  A(hip 3.415) = 1.099935 m^2.
- Reduced masses at the planes: mu = 281.9, 594.5, 1190.3 kg
  (m_below = 287.9, 622.5, 1315.5 kg; m_above = 13,536.7, 13,202.1, 12,509.1 kg).
- Piston frequencies omega = A/sqrt(kappa*V0*mu): cell0 907.5, cell1 842.8,
  cell2 1785.6, cell3 420.3 rad/s. Single-cell etas at 300 Hz: 3.025, 2.809,
  5.952, 1.401 — three of four cells OUTSIDE the explicit bar.
- Coupled coarse modal estimate (3 ring directions, K = J^T S^-1 J,
  M = diag(mu)): omega^2 spectrum [3.798e6, 1.860e6, 2.917e5],
  omega_max = 1949.0 rad/s (310.2 Hz), eta = 6.497 at h = 1/300 s.
- Substep law: n >= ceil(eta/2) = 4 -> h/n = 8.333e-4 s, residual
  eta = omega_max*h/n = 1.624 < 2 (23% headroom).
- Grounded variant (the stance configuration, m_eff = m_above): the worst cell
  sits at eta = 1.836 — inside the bar by 8%, i.e. the balance rung has NO
  stability margin without the substepped coupled solve either.

## PREDICTIONS (test bars, reference model first, then the appliance)

P1 (pressure recovery — the constitutive law is unchanged): after the coupled
solve, the recovered pressure P_i = lambda_i/h^2 equals the engine's own law
P = −DeltaV/(kappa*V0_i) within 1% at every cell, at rest AND under a probe
press. At rest (zero press, zero servo intent) lambda -> 0 and every P = 0
with V = V0 (conservation at the live level, conserve_pct ~ 1e-6%).

P2 (substep count — the gate's own sharpness): at n = 4 the reference model's
coupled solve stays bounded under the probe press; at n = 2 (residual
eta = 3.25) it diverges within 10 ticks; at n = 1 (explicit, eta = 6.50) it
diverges within 3 ticks. The measured boundary lands at the predicted n.

P3 (piston-mode frequency — the reference model's solver reproduces the
derived dynamics): a spectral probe of the reference model's response about
rest peaks at omega = [907.5, 842.8, 1785.6, 420.3] rad/s per cell and at the
coupled omega_max = 1949.0 rad/s, each within ±10% (XPBD at n = 4 carries
O(h_sub^2) frequency error; 10% is the stated tolerance for that discretization).

P4 (servo reaction forces — the coupling is real): with a servo intent driving
a joint, the solve produces equal-and-opposite reaction forces through the
joint constraint into BOTH bodies; the net momentum injected per tick is zero.
The current pose-overwrite architecture (joint_deg_ written after the solve)
measurably injects momentum — P4 is where the two architectures differ.

P5 (momentum conservation): with gravity off and no contacts, total linear and
angular momentum of the coupled system is conserved across 100 ticks to solver
tolerance (< 0.1% of the initial press impulse).

P6 (balance is its own gate — force AND moment feasibility): the stance bar is
"there exist contact forces within the friction cone (mu from the world's
material) and within actuator limits with SUM F = m*g and SUM M_about_COM = 0".
"A foot is grounded" (contact depth > 0) alone FAILS the bar by construction.
The gait/stance machines' measured gates (support sets, lean, per-side depth)
stay exactly as shipped; feasibility is a NEW bar on top, not a replacement.

## FALSIFIER (named before any run)

(a) FREQUENCY: the reference model's measured piston-mode frequencies miss the
predicted omega = [907.5, 842.8, 1785.6, 420.3] rad/s or the coupled
1949.0 rad/s by more than ±10% — the reference model's geometry or compliance
is not the world's, and the successor hypothesis is named in the failure
(per-cell A from the slicer vs cap-fan areas; compliance from kappa*V0 vs an
effective kappa fitted from the miss).

(b) BOUNDEDNESS: at the predicted substep count n = 4 the coupled solve DIVERGES
under a probe press that the explicit update (n = 1) also diverges on — or,
conversely, n = 2 already stays bounded, meaning the gate over-predicted the
requirement. Either outcome REPLACES the prediction: the measured boundary is
reported and the substep law amended. Honest either way; a prereg whose
falsifier cannot fire is not a prereg.

(c) PRESSURE LAW: P_i = lambda_i/h^2 departs from −DeltaV/(kappa*V0_i) by more
than 1% under load — the lambda recovery (Astra's sign convention) is mis-signed
or mis-scaled in the implementation; fix is mechanical (sign/stacking order),
and P1 is re-run.

Successor machinery if (a) or (b) fires: the diagnostic gains the missing
geometry term (the reference model's piston idealization vs the real joint
kinematics), and n is re-derived from the MEASURED omega_max — the table in
DIAGNOSTIC.md is then re-read with the new number, not argued with.

## WHAT THIS PREREG DOES NOT CLAIM

- It does not claim the engine is stable today. It measures that today's
  architecture has no coupled solve to destabilize: servos overwrite poses,
  the pressure law is a readout, and the explicit-vs-implicit question does not
  arise until volume, joints, servos and contacts enter ONE linear system.
- It does not claim n = 4 is a constant. It is a function of the measured
  omega_max on THIS world (1949 rad/s); a new seal cut, a new body, or a new
  mesh re-runs `tools/xpbd_diagnostic.py` and re-derives n.
- It does not claim the ground contact model (penalty spring at the lowest
  vertex) survives the coupling unchanged — its constraint form is decided in
  the reference model by P2/P5, before any engine edit.

 (Agent: A12-xpbd-prereg)
