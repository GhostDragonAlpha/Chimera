# A1_XPBD DESIGN — from the reference model to the engine appliance

**2026-09-14.** Agent A12-xpbd-prereg. Consumes `DIAGNOSTIC.md` (measured) and
`PREREG.md` (the bars). No solver code exists yet; this is the increment plan
the code must follow when the prereg's build window opens.

## 0. THE SCHEME (Astra's, verbatim in shape)

    predict (x *= x + h*v, apply external forces)
    loop n = 4 substeps (h_sub = h/n = 8.333e-4 s, from DIAGNOSTIC.md's table):
        reset lambdas
        loop iterations:
            stack the constraints: [volume | joint | servo-target | contact]
            solve (J M^-1 J^T + Lambda/h_sub^2) dLambda = -C - (Lambda/h_sub^2) Lambda
            refresh the NONLINEAR Jacobians during the iterations
              (dV/dq per cell re-read from the posed surface — the engine's
               numeric-probe doctrine, not a frozen linearization)
        x += J^T Lambda  (position correction)
        v += M^-1 J^T Lambda / h_sub   (CONSISTENT velocity update)
    recover pressure: P_i = lambda_i / h_sub^2  (Astra's convention)

Two laws in that loop are the whole point: servos enter as CONSTRAINTS WITH
REACTION FORCES (never as a pose written after the solve — the current
`joint_deg_` overwrite bypasses the coupling and injects energy), and the
velocity update is CONSISTENT with the position correction (else the solve
heats the body every substep).

## 1. STAGE B1 — the CPU reference model (scratch, no engine edits)

House pattern: the matter kernel's B1 scratch. Same mesh numbers, no engine.

- Geometry: 4 prismatic reference cells with the MEASURED table
  (V0 = 0.287914 / 0.334578 / 0.693006 / 12.5091 m^3; piston areas
  A = 0.175356 / 0.254922 / 1.099935 m^2 at the ankle/knee/hip planes;
  reduced masses mu = 281.9 / 594.5 / 1190.3 kg), plus rigid sub-bodies
  standing in for the joint-driven sides.
- Constraints: volume (compliance kappa*V0_i), hinge joints at the three
  planes, servo targets (torque -> lambda), floor contact (penalty, matching
  the engine's lowest-vertex spring until P2/P5 decide its constraint form).
- Instrument: spectral probe about rest + a probe press (a step force at one
  ring), explicit n=1 vs XPBD n=4.
- Exit bars: PREREG P1–P6, falsifiers (a) and (b) pointed at the predicted
  omega = [907.5, 842.8, 1785.6, 420.3] and 1949.0 rad/s, ±10%, and at the
  n = 4 boundedness boundary. The appliance is NOT built until these clear.

## 2. STAGE B2 — the engine appliance (`membrane_tick`)

### 2.1 Where the solve sits

`MembraneTick::step()` already runs: pose/FK -> seal volume sums (divergence,
the existing per-cell V) -> pressure law `c.p = (c.v0 - v)/(kappa_*c.v0)` ->
contact/stance/gait passes. The solve inserts as a STAGE between the volume
sums and the pressure readout:

    predict sub-body states from velocities
    for sub in 0..n_sub-1 (n_sub from tools/xpbd_diagnostic.py, 4 today):
        build C: [C_volume (per seal cell, from the divergence sums)]
                 [C_joint (per active pin, from the rig/classify FK)]
                 [C_servo (torque error per driven pin)]
                 [C_contact (floor depth, per support vertex)]
        iterate: solve dLambda; REFRESH dV/dq per cell by the numeric probe
                 (perturb the pin, re-sum the divergence volumes — the exact
                 doctrine the engine's travel channels already use)
        apply position corrections; update velocities consistently
    per-cell P = lambda/h_sub^2 -> the SAME state_json fields (V, P)

The constitutive readout does not change: `kappa_ = 4.6e-10` stays, and
P = lambda/h^2 replaces (not amends) the direct `dP = -dV/(kappa*V0)` sum —
PREREG P1 demands they agree within 1%, which is the cheapest continuous
test the appliance carries.

### 2.2 Servos: the retirement of the pose overwrite

Today `joint_deg_[pin] = angle` is written by stance (pins 17/18), gait
(pins 15/16 after R3's binding resolution), flex and teardown. The appliance
turns each of those writes into servo INTENTS (torque or target angle ->
lambda in the coupled solve). The machines keep EVERYTHING else:

- F1 stance: support-set selection (frozen band), rest lean reference,
  k_p = 1/(|S|*tau) — unchanged; its actuation becomes an intent, and
  `stance_off_locked_` teardown (angles -> exactly 0, the V10 fix) becomes
  intent -> exactly zero lambda. Rest is still rest.
- G1 gait: the STANCE -> LIFT -> REACH -> LOAD (+ RECOVER) machine, every
  measured gate, the rate caps, the F1-owned ankles, the strut composition
  over stance — unchanged in gating; the drive channel becomes lambda rates
  under the same caps.
- The 57.3x probe-unit/radian servo-frame gain (named, absorbed by ROM clamps)
  is RE-DERIVED at the swap: the servo constraint's unit is torque-newtons,
  not degrees, and the calibration constant dies with the overwrite.

### 2.3 Routes

- NEW `POST /tick_xpbd` {enable, substeps?, probe_press_n?} — feature-flagged,
  DEFAULT OFF; the tick is bit-identical to today when off.
- NEW `GET /xpbd_state` — per-cell lambda, P, dV last step, measured
  omega_max, eta, n_sub, iteration counts (the witness fields P1/P2 need).
- `POST /tick_pose` and `/tick_flex` keep working for authored poses (the
  pose-overwrite path remains for UNarmed, kinematic authoring); when the
  solve is armed they are refused with a named reason (one writer per DOF).
- `POST /tick_intent` (the standing press) maps onto the contact constraints.
- `/tick_stance`, `/tick_gait`, `/tick_gravity`, `/tick_seal*`: signatures and
  semantics unchanged.

### 2.4 What stays untouched

The seal tree and cut-and-weld (volumes, caps, degenerate guard), the
snapshot/restore blob (self-validating v0 recompute), the gait machine's
measured gates, the R3/R4/V10 fixes (binding-resolved pins, ABORT contract,
teardown arming), the render path, the HTTP read-only discipline. The appliance
adds a stage; it does not re-architect the tick.

## 3. RISK REGISTER (what the reference model must decide before B2)

| risk | decided by |
|---|---|
| contact form under the solve (penalty vs constraint) | P2/P5 in B1 |
| iteration count vs realtime budget (36,630-tri divergence refresh per iteration) | B1 timing instrument; fallback: refresh once per substep, not per iteration (the gate's own slack: eta 1.62 at n=4) |
| the sparse-loop sampling found in Route 3 (50 verts within 5 cm of the knee plane) | the Jacobian probe uses pin-space perturbation (dV/dtheta), which the engine's FK moves densely — the vertex-space under-sampling does not transfer |
| servo unit calibration (the retired 57.3x gain) | B1 P4 vs the measured stance holding torque |

## 4. ROLLBACK

The flag is the rollback: `/tick_xpbd {enable:false}` restores today's tick
bit-for-bit. The diagnostic tool re-runs in seconds (GET-only) and re-derives
n on any new world. The prereg's falsifiers fire on the reference model BEFORE
any engine edit exists — the cheapest possible place to lose.

 (Agent: A12-xpbd-prereg)
