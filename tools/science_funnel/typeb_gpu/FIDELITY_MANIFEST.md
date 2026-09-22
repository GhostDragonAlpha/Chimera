# FIDELITY MANIFEST — the GPU full-body port (2026-09-21)

What is PORTED vs DEFERRED relative to `ChimeraEngine/engine/gait_controller.hpp`
@ `agent/typea-command-adapter-20260921` (9808dc94). Written BEFORE the Phase-C
runs. Trailer Agent: GLM 5.3.

## PHYSICS (all ported)

| Piece | Reference | Status |
|---|---|---|
| Articulated dynamics M(q), g(q), bias(q,v) | coupled_articulation.hpp Model::evaluate | PORTED (geometric-Jacobian form; frames t/dt/ddt by the same product recursion) |
| Semi-implicit RK4 at dt/4 (substeps=4) | GaitWalker free_step | PORTED |
| Plane contact: pair-min sole gap, velocity-gate arming, the plane hold | free_step/rate | PORTED |
| Contact active-set projection (mass metric, exhaustive mask enumeration, stop-tier-first law) | project_rows | PORTED |
| Discrete-cone Coulomb friction (stick + slide + the swallowed slide-singular) | friction_solve | PORTED |
| Impact velocity projection + friction catch + positional correction with the 0.05 m budget | impact | PORTED |
| Joint-stop rows, walls, clamp-pin + pin bookkeeping (no ledger) | advance | PORTED |
| Event detection: earliest stop/contact, 42-step bisection, DFS event split | advance | PORTED (explicit LIFO stack; budgets kept) |
| Servo muscles: mass-normalized PD at 4 Hz/zeta 0.8, torque caps, viscous damping | servo | PORTED |
| Depletive actuator stores with the per-substep 40-step work bisection (8 rounds) | step | PORTED |
| Trunk-pitch posture drive + the wave-10 settle ramp | servo/post_amp | PORTED |

## REFLEX DETERMINISTIC CORE (ported)

| Law | Wave | Status |
|---|---|---|
| Contact-reset hybrid clock, T_CYCLE=0.71, per-leg offset {0,0.5} | Sec 5.1 | PORTED |
| Touch classes: kTouch=1e-5, kReleaseBand=1e-6 hysteresis; kSlip=1e-9 | wave 22 | PORTED |
| Settle window (60 ticks), the entry-pose hold, the plant capture at settle end | wave 8/12 | PORTED |
| Planted-strut IK (branch capture, annulus clamp + counted saturation) | wave 12 | PORTED |
| Fore stepping clock: wave-14 lateral-grid arm, liftoff, world-line+arch glide, TD recapture | waves 13/14 | PORTED |
| Fore grid convergence search + entry re-plant/re-arm (tau1 = env-(tair+g)) | waves 15/20 | PORTED |
| Fore no-double-swing gate clauses (a)/(b)/(c) + thin-seat deferral + admissible follow + wall-bound counting + wait override (kWallMargin/kDiveRateMax/kWaitFloor) | waves 20/23/25*/26 | PORTED (*wave-25's held-glide scope is inert here: the wave-24 pocket hold is deferred, so fore_glide_held == false, the wave-20 original reading) |
| Hind tables + Oku zeros; height-hold emergency latch + feed-forward | wave 16 repair/27 | PORTED |
| Hind step law: slot fires, gates (a)(b)(c)(d incl. kick-stand promise), lift-first hold, glide IK + arch, wave-31 band-entry completion, wave-29 alternation deadline, wave-32 min-form deadline (kFoldBudgetTicks=45 / kUnloadTicks=1), wave-35 (a)-waive + wave-38 stall-era scope guard | waves 28/29/31/32/35/38 | PORTED |
| Capture-step reflex with the wave-21 three-clause arming law (true hull, swing clock, slip cone) | wave 21 | PORTED |
| THE COMMAND ADAPTER channel: commanded_target_velocity_x as the plant law's v at BOTH sites (fore_xoff, the hind fire), zero-order hold, census counters, byte-inert when unused | typea 20260921 | PORTED |

## DEFERRED (itemized; each a late-survival law, mined at ticks > ~140)

| Law | Wave | Reason | Expected face of the deferral |
|---|---|---|---|
| Pocket-clear hold (the body-locked annulus-edge glide seat at wall-bound lifts) | 24 | its map/bisection state machinery is self-contained but interacts with the wave-25/26 gate reads; deferred as one unit with the held-glide scope | wall-bound fore lifts run the plain clamped glide; fore wall pins may reappear late in the walk |
| Stand-first carrier hold + its latch history | 33/34 | pure late-era hind-carrier law (engages only in ride-era exchanges) | carrier unloads during stall-class exchange swings late in the walk |
| Waive-era hand-off preservation census (waive_last disarm) | 36 | census-backed disarm of the (b)-waive; the port yields (b) unconditionally at the deadline (documented at the code site) | rare +1 calendar phase shifts after waive fires |
| Completion-tick re-lock | 37 | REVERTED upstream (the wave-37 ledger falsifier fired; the ship does not carry it) | none — parity with the ship |
| Ledger/heat bookkeeping (impulse, constraint work, friction/impact heats, external work), per-tick status JSON | diagnostics | energy books are diagnostics; they feed NO dynamics read | none for dynamics; the port is not energy-audited |
| push_N external-force row | engine | the reference's own e.force(0,..) resolves on the GROUND row (structurally zero Jacobian) — ported as the same structural zero | none |

## Deferral honesty clause

If a Phase-C falsifier fires, the receipt must state whether a deferred law was
ENGAGED-CLASS on the CPU reference trace near the failure tick before any
back-port is attempted; a back-port is a NEW prereg addendum committed before
the re-run, never a silent patch after seeing the number.

## ADDENDUM — power-off semantics disposition (2026-09-22 closeout lane)

The prior premise "the C++ power-off HOLDS the legs frozen while the kernels
FREE them (tau=0); the kernels must adopt hold" is RETIRED. Verified by direct
interrogation of the reference (grav_probe/grav_probe2 against
engine_inc/gait_controller.hpp):

- Both implementations run tau=0 at power-off; there is no hold law in either.
- The C++ evaluate's generalized gravity at the defaults pose is NONZERO on the
  hind rows (-0.0558675 N·m) — byte-identical to the kernels' gv — yet the
  C++ freefall trace shows the joints frozen and the base at exactly
  -9.80665 m/s^2. The frozen legs are EMERGENT: at the straight-chain zero
  pose every link CoM hangs below its joint axis, uniform gravity produces no
  generalized joint torque, and the free-fall solve M^-1*gv is weightless
  (joint rows ~0, base-y = -g exactly). Free fall IS the hold.
- The kernels' old -10.038 m/s^2 with joint drift was the fk_eval
  derivative-frame seed/chain-product defect class (receipt closeout appendix),
  not a semantics difference. After the fix the GPU freefall reproduces the
  C++ trace bit-for-bit pre-latch.

No ported-vs-deferred change; no back-port required. The deferral honesty
clause was checked: no deferred law (all late-survival, ticks > 140) is
engaged-class anywhere near the tick-40..63 refusal window.
