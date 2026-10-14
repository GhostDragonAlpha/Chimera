# CBP-PREREG-001-AMENDMENT-001 — Prospective amendment: pivot-consistent floor-removal control, unpowered-window ledger denominator, checkpoint arithmetic, frozen reaction envelope

Status: COMPLETE, UNPUBLISHED. Authored 2026-10-04 by worker `wk-cbp-prereg`.
This is the ONE prospective amendment required by the Sergeant Flash
endorsement verdict `CHANGES_REQUIRED` (freeze-time catch; ZERO runs executed;
no observation preceded it, so the amendment law of CBP-PREREG-001 section 7
is satisfied prospectively). It is published through the same one serialized
publication owner as CBP-PREREG-001, before any gated measurement. The
Lieutenant pins both documents; the fresh endorsement review follows; only
then does gate G4 unlock. `SCIENTIFIC_PREREGISTRATION.md` (sha256
`0f62cbfa3212298eba6972a446998005369208a0caab774fdfa92889253c8dc2`) is NOT
rewritten; its bytes stand as the endorsed-except-herein base. Where this
amendment restates a clause, the restatement supersedes; every clause not
named in sections 2-6 stands ENDORSED unchanged.

Trigger of record: the endorsement review found that P6's ballistic identity
is analytically inconsistent with the sealed fixture. Verified against the
sealed source: `fixture.py` `add_joint_revolute(-1, arm,
parent_xform=(0, 0.07, 0), ...)` attaches the arm to the WORLD at a pivot.
Control C2 removes only the ground plane, so post-C2 the fixture is a
world-pivoted pendulum with a spring-hung pad — not a falling body. The
original P6 free-fall numbers (drop 4.9033e-2 m, KE 0.4193 J after 0.1 s from
rest) would have produced a GUARANTEED FALSE NEGATIVE in hard gate G4. The
endorsement review's own pivot-consistent integration is recorded here as
review-reported reference values (theta ~ 0.2205 rad, arm-COM drop ~ 0.0328 m,
KE ~ 0.3037 J at t = 0.1 s from theta = 0 at rest; joint limit engaged at
t ~ 0.126 s); they are references, not frozen gates.

Fix choice: option (b) — restate P6 pivot-consistently. Option (a) (also
removing the shoulder joint) is DECLINED: it would change the C2 scenario,
forfeiting the pivot-constraint qualification value of the sealed control.
The C2 scenario is unchanged: ground plane removed; shoulder joint NOT
removed.

---

## 1. Restated C2 and its V-law rows (scenario unchanged)

C2 (unchanged): private fork of the committed end-of-phase-A state; ground
plane removed; 600 ticks, tau = 0; checkpoints per section 4.

| Frozen constraint fact | Declaration / assumption | Violation observable |
|---|---|---|
| World pivot: the arm's revolute joint anchors the body origin (0, 0.07, 0) to the world for the entire C2 window | The joint anchor is fixed by the solver's joint constraint; the fixture is a pendulum, not a free body. | Joint-anchor world position drifting beyond the frozen 1.0e-4 m bound across C2 (basis: XPBD joint projection at 12 iterations, dt 1/1200 s, float32 state). |
| Joint limits [-0.35, +0.35] rad remain active in C2 | Gravity torque drives theta toward the lower limit; the limit stop is an INELASTIC, UNMODELED constraint impulse: energy absorbed by it has no authored ledger term. | Rotation beyond a limit; a limit engagement not recorded as an event row (section 2, E6). |
| Initial state = measured end-of-settle committed state (theta_0, omega_0, spring extensions, pad contact state as measured) | No analytic assumption that settle ends at rest, at theta = 0, or off the limit; all three are possible and only measured state is assumed. | Any use of assumed initial values in a gated comparison. |
| Spring-hung pad | The pad's only support in C2 is the 9-spring network; it may oscillate and is not monotone after the arm is stopped. | A pad node world-pinned; pad motion attributed to anything but gravity, springs, and solver contact numerics. |

## 2. Restated P6 (supersedes P6 in its entirety)

P6 — Pivot-consistent floor-removal identity. Gated quantities:

- E1 (identity, primary gate): over every checkpoint interval of C2 that lies
  strictly BETWEEN recorded joint-limit events, the unpowered mechanical
  identity d(KE + E_grav + E_attach + E_xpbd)/dt = 0 holds within the
  unpowered-window bound of section 3 (5% of window turnover D, or the
  absolute floor for degenerate windows). The identity is NOT claimed across
  a limit event.
- E2 (event rows): every joint-limit engagement is recorded as its own
  ledger event row: tick, t, theta, omega before/after, and the
  E_accounted discontinuity in the residual column, labeled "unmodeled
  constraint impulse" — never as heat and never silently absorbed.
- E3 (pivot membership): joint-anchor world position invariance within
  1.0e-4 m across the whole C2 window (V-law row above).
- E4 (drop bounds): over any unpowered checkpoint interval not containing an
  event, each of arm-COM and pad-COM vertical displacements is negative
  (downward) while theta is strictly inside the limits, and each magnitude is
  <= the free-fall bound 0.5*g*T^2 (with g = 9.80665 m/s^2; over 0.1 s:
  4.9033e-2 m). Basis: a fixed pivot strictly reduces COM vertical
  acceleration below g. The pivot bound is the pendulum's, for ANY measured
  initial state.
- E5 (monotonicity, scoped): all body and particle y decrease
  checkpoint-to-checkpoint only within the FIRST pre-limit segment, and only
  if that segment contains >= 2 checkpoints. If the measured settled state is
  already at or beyond the lower limit (empty first segment), monotonicity is
  reported NOT EVALUABLE with the event time recorded; this is an anticipated
  outcome branch, not a failure.
- E6 (reference labels): the original free-fall numbers (4.9033e-2 m drop,
  0.980665 m/s, 0.4193 J KE after 0.1 s from rest, m = 0.872 kg) are retained
  ONLY as the labeled UNCONSTRAINED reference for a fully released body. C2
  is not that experiment. The endorsement review's pivot-consistent values
  (theta ~ 0.2205 rad; arm-COM drop ~ 0.0328 m; KE ~ 0.3037 J at 0.1 s from
  theta = 0 at rest; limit at t ~ 0.126 s) are retained as review-reported
  references. Neither set is a gated C2 prediction.

Contradicting observations (named): pivot-anchor drift beyond E3's bound; a
segment identity failing section 3's bound; rotation beyond a limit or an
unrecorded limit event; upward COM motion inside the limits without a spring
term to pay for it; KE growth exceeding PE loss beyond the bound within a
segment; or any report citing the unconstrained reference numbers as C2
predictions. A static post-event configuration is not a failure; the tested
quantities are the segment identity, the event rows, and the scoped
monotonicity.

P5, P7, and gate G4's other clauses are unchanged; G4 remains locked for C2
until the fresh endorsement of this amendment. P6's original free-fall
prediction is WITHDRAWN as a binding prediction and marked superseded by this
section.

## 3. Unpowered-window ledger denominator (defining sentence, amends P3)

**Defining sentence:** for any window with actuator work identically zero
(tau = 0), the 5% relative form carries on the window's energy turnover
D = sum over the four same-stage terms (kinetic, gravitational, attachment,
XPBD penalty) of |E_term(after) - E_term(before)| — i.e.
|unexplained_residual_j| <= 0.05 * D — and if D < 1.0e-6 J the window is
evaluated by the absolute bound |unexplained_residual_j| <= 1.0e-8 J.

Powered windows keep the frozen P3 form (5% of |actuator_work_estimate_j|).
Basis for the frozen floors: same-stage float64 diagnostic readback of float32
state; 1e-8 J absolute residual at 1e-6 J turnover is the smallest scale the
diagnostic path can meaningfully resolve. Both numbers are frozen and may
fail; a failure is a finding.

## 4. Checkpoint arithmetic repair (amends section 2.1 cadence and every windowed clause)

Frozen cadence is corrected so that every declared falsifier window contains
its required checkpoints. This supersedes the 120-tick cadence.

- Battery B1 (3600 ticks): checkpoints at ticks k*60 for k = 0..59 (ticks
  0..3540; phase boundaries 1200 and 2400 lie on this grid) PLUS a final
  checkpoint at tick 3599 — 61 checkpoints per battery.
- Controls C1-C2 (600 ticks each): checkpoints at ticks k*60 for k = 0..9
  PLUS a final checkpoint at tick 599 — 11 checkpoints per control.
- A "sustained" failure requires >= 3 consecutive checkpoints INSIDE the
  declared window. Window-to-checkpoint arithmetic, checked at freeze:

| Window | Tick range | Checkpoints | Count |
|---|---|---|---|
| P1(i) final 0.2 s of phase A | 1020-1199 | 1020, 1080, 1140 | 3 |
| P1(ii) all of phase A | 0-1199 | 0, 60, ..., 1140 | 20 |
| P3 press bound, final 0.2 s of phase B | 2220-2399 | 2220, 2280, 2340 | 3 |
| P6/E5 first pre-limit segment | C2 start .. first event | measured; >= 2 required, else NOT EVALUABLE | measured |

No other windowed clause exists. This repair changes checkpoint density and
therefore diagnostics-readback volume (twice the 120-tick cadence); that
overhead remains a separately measured line item under section 4.4 of
CBP-PREREG-001 and is never absorbed into tick latency.

## 5. Frozen reaction envelope and the no-unfrozen-budget law (carries endorsement note 2)

CBP-PREREG-001 P4 referenced "the frozen numerical budget implied by |tau|
<= 2 N m, spring displacements, and weight" without freezing a number. That
dangling reference is resolved by freezing:

- Per-anchor reaction envelope: |reaction_i| <= 50 N for each of the 9
  anchors (basis: k = 100 N/m against displacements up to the 0.3 m arm
  length; grosser deformation is already a failure under other clauses).
- Whole-body attachment force envelope: |sum of reactions| <= 450 N.
- Standing law: NO measurement report may reference a numerical budget,
  bound, or tolerance that is not frozen in the published preregistration or
  its published amendments. A comparison without a frozen bound is reported
  as an unbounded observation, explicitly labeled, or not made at all.

The primary P4 gate remains the EXACT pair-sum identity; the envelope is a
secondary sanity bound whose violation is a named finding.

## 6. Standing law (durable lessons, binding on this campaign)

- L1. Analytic control numbers are derived from the SEALED constraint graph
  (pivot, joint limits, spring network, contact geometry, masses), never from
  the scenario's colloquial name. "Floor-removal fall" is a name, not a
  derivation; the fixture's world pivot made it a pendulum.
- L2. Checkpoint-window arithmetic is checked at freeze: every falsifier that
  counts checkpoints must have its windows' checkpoint counts written out and
  verified against the frozen cadence before publication (section 4 table is
  the standing example).
- L3. Every measurement pin (job manifest `notes`, receipt references, report
  citations) cites the published preregistration path and revision verbatim —
  the published repository path and commit hash of CBP-PREREG-001 plus this
  amendment — not a lane-local filename or a paraphrase.

## 7. Endorsement scope and supersession

Endorsed unchanged (Sergeant verdict): all penetration bounds (P1), the
reciprocity identities and re-association budget (P4), the byte-identity
standard (P9), the convergence reporting (P10), the ledger residual form for
powered windows (P3), the construction tolerances (G1), sections 1, 2 (except
cadence), 4, 5, 6, 7 of CBP-PREREG-001, and amendments herein to P6/P3/cadence
once re-endorsed. This amendment supersedes only: P6 (section 2), P3's
unpowered-window denominator (section 3), the checkpoint cadence and windowed
clauses (section 4), and P4's dangling budget reference (section 5). G4
unlocks for C2 only after the Lieutenant pins and publishes this amendment
and the fresh endorsement verdict is recorded. No gated run of any kind has
been submitted.
