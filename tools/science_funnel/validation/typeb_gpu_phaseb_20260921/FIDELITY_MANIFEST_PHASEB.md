# FIDELITY MANIFEST — Phase B: the reflex core, Python side (2026-09-21)

What is PORTED vs DEFERRED in `walker_reflex.py`, relative to
`ChimeraEngine/engine/gait_controller.hpp` @ the base (`agent/typea-commandadapter-20260921`
bytes, 9808dc94, carried through the physics lane's checkpoint a336955 ->
final 0763d27 unchanged). Written BEFORE the replay numbers were frozen into
the receipt; corrected only where the SHIP BYTES contradicted the physics
lane's manifest (noted inline). Trailer Agent: GLM 5.3.

Level gate: 0 = pure physics (the layer is inert) · 1 = touch + clocks ·
2 = + holds/alternation · 3 = full (+ the adapter channel).

## LEVEL 1 — touch + clocks (4 law families, PORTED)

| Law | Wave | Status |
|---|---|---|
| Contact-reset hybrid clock (T_CYCLE=0.71, offsets {0,0.5} applied ONCE at reset, dt/T_CYCLE advance, settle freeze, the touching classification held through frozen windows) | Sec 5.1 | PORTED |
| The run repair's clock discipline (never a per-tick offset increment; fmod advance) | wave 16 (clock half) | PORTED |
| Touch classes: kTouch=1e-5 any-point band, kReleaseBand=1e-6 genuine-departure hysteresis, the band-edge graze that re-arms nothing | wave 22 | PORTED |
| Capture arming: the three-clause law (true monotone-chain hull, swing-window clock, slip cone v_bound = mu*g*(1-CAPTURE_PHI)*T_CYCLE); its only mutation is the clock (phi := CAPTURE_PHI) | wave 21 | PORTED (0 fires on the ship walk = the ship's own capture_events 0) |

## LEVEL 2 — holds/alternation (21 law families, PORTED)

| Law | Wave | Status |
|---|---|---|
| Settle window + the plant capture at settle end (the loaded state IS the planted pose; the capture/arm ordering) | waves 8/12 | PORTED |
| Planted-strut closure: the closed-form fore IK (pelvis-frame solve), the branch captured ONCE at the capture, the analytic round-trip check, the annulus saturation read | wave 12 | PORTED |
| The stepping-strut fore clock: arm at the capture, liftoff/glide/TD schedule, the world-line+arch glide, TD re-capture of the ACTUAL paw | wave 13 | PORTED |
| The wave-14 lateral-grid arm (lift = same-side hind lift + T/4, read once from the hind clock) | wave 14 | PORTED |
| The wave-15 units law (tau1 seconds -> ticks) + the grid convergence search (k=1..8 split cycles, both directions, the duty-1/2 floor, the envelope-capped lengthening) | wave 15 | PORTED |
| The mid-entry re-plant: tau1 = max(0, tau_env - (t_air+g)), t_air = ceil((T_CYCLE-DUTY)/dt) = 9, the entry hand-off clear at the first at/ahead TD, the re-arm from the fresh envelope, the in-place ground re-plant at the cycle/envelope edge | wave 20 | PORTED |
| The wall-bound trigger (ACTUAL joint headroom <= kWallMargin, counted per stance tick), the thin-seat deferral (target headroom < 2*kWallMargin + the actual-bound conjunct), the admissible follow seat (the +/- 1 mm authority sample, the 42-step bisections, the annulus-bounded slide) | wave 23 | PORTED |
| The pocket-clear hold: the arm on wall-bound lifts, the annulus-edge ground seat, the line-march of joint-range-exiting ticks, the held span | wave 24 | PORTED (3 holds armed on the ship walk) |
| The held-glide predicate + the gate's contact-aware scopes: clause (a) gates only a TRUE airborne glide (a held glide spends no support); clauses (b)/(c) scoped to stance bookkeeping | wave 25 | PORTED |
| The wall-adjacent wait override (kWallMargin / kDiveRateMax / kWaitFloor = 2*kDiveRateMax) | wave 26 | PORTED (0 fires on the ship walk) |
| The height emergency: the scene crit key, the derived floor (2*kSinkRateMax + kSinkRateMax*tau_settle), the one-way latch on min shoulder height | wave 27 | PORTED (margin 0.039326 m = the receipts' 39.3 mm EXACT; the fire is stamped tick 76 in this lane's pre-step tick convention) |
| The hind step law: the slot fire at phi >= TOE_OFF with live pads, the glide IK (2-link, held ap/mp, the branch captured at the fire), the 2*pad-radius arch, the annulus clamp (counted, never silent), the fire qerr self-check | wave 28 | PORTED |
| The alternation law: the concentration clause ('<' form), the alternation-due predicate (phi below the slot + the clock's own wait vs the deadline), the kick-stand promise (clause (d): the stance-or-held-glide coverage of tair) | wave 29 | PORTED |
| The band-entry completion (a replant is not complete until the band entry; the hold-return at the plant point) | wave 31 | PORTED |
| The min-form deadline: fold = other_last_td + kFoldBudgetTicks - tair - g; the unload bound other_last_td + kUnloadTicks - g armed by the ride era; the binding term flagged | wave 32 | PORTED |
| The stand-first arming read (the other mid-glide AND in-band AND this leg the ride-era carrier with live pads; the planar re-capture every pinned tick; the y-anchor captured once at the arm) | wave 33 | PORTED (first engagement the 176 decision = the receipt's own number) |
| The latched carrier hold + the frozen-pivot variant + the extension-envelope release read | wave 34 | NOT CARRIED — reverted upstream; the 9808dc94 ship bytes do not contain it (the manifest row's census fields exist only as reset bookkeeping) — parity with the ship |
| The carrier self-unload fire deadline: clause (a) yields when the deadline binds on the UNLOAD form and the other's lift-first hold genuinely cleared; the stall-era census | wave 35 | PORTED |
| The concentration repair (the stale hand-off read) + the waive-era hand-off preservation (the (b)-waive disarmed out of a waive-ridden swing, self-expiring at the other's next fire) | wave 35/36 | PORTED |
| The completion-tick graze yield | wave 37 | PORTED **AS SHIPPED** — the 9808dc94 bytes carry it (the yield + its census); the physics lane's FIDELITY_MANIFEST row said "REVERTED upstream; the ship does not carry it", which contradicts the bytes; this lane follows THE BYTES |
| The calendar-arithmetic waive scope guard: the stall-era link test (own last era ran the tair cadence iff the other's current era is the chain's next link); the guard only REMOVES openings | wave 38 | PORTED (25 guard blocks on the ship walk; the waive fires EXACTLY ONE, L@161 = the wave-38 receipt's own pre-registered letter) |
| The unload-gate ((b)/(c) yield at the deadline, the wave-32 arithmetic, the fold/unload class census) | wave 32/35 | PORTED (14 unloadgates on the ship walk) |

## LEVEL 3 — the adapter channel (1 law family, PORTED)

| Law | Wave | Status |
|---|---|---|
| {commanded_target_velocity_x}: first-class, live (NOT restart-gated), zero-order hold at tick boundaries (value-only — a re-issue is decision-identical), v >= 0 number domain (no bool), the authority law xoff = v_cmd*(DUTY_SAMPLED*T_CYCLE)/2 at BOTH plant sites (the fore xoff, the hind fire), the envelope keeps the MEASURED v everywhere else, the census (calls + first tick), INERT WHEN UNUSED (max(0, v3)) | typea 20260921 | PORTED (first consumption tick 157 EXACT; xoff 0.145479 = 0.60*0.2424650 at every post-issue fire while measured v3 was 0.672; the ZOH re-issue census identical) |

## DEFERRED (this lane; itemized with the expected face)

| Item | Wave | Reason | Expected face of the deferral |
|---|---|---|---|
| The servo TARGET APPLICATION path (the capped mass-normalized PD, the store bisection, the posture drive/post_amp, the wave-10 vault ramp, the wave-16 phase-advanced target consumption) | 5/8/10/16/27 | owns no decision: it lives inside the env kernel (the physics lane's Phase-A port, walker_gpu.py/walker_numba_gen.py). This lane owns decisions + commands, not the tau path; the layer's outputs enter dynamics only through set_command | none for decisions; the tau path is judged by the physics lane's anchors |
| The reset-state law (defaults, tables columns, phase-slope speeds, the wave-16 reset repair) | 4/16 | carried via walker_model.reset_state (the interface's committed mirror), consumed at the layer's reset seeding — not re-implemented | none |
| The energy/heat ledger, per-tick status JSON, the wall-pin/pin-census bookkeeping | diagnostics | diagnostics feed no decision; the layer carries the census counters the DECISIONS read (waive/guard/hold/deadline books) but not the energy books | none for dynamics |
| The live-GPU leg of level monotonicity (status-byte identity of the numba env at levels 0..2) | — | the env's tick-0 hang is the physics lane's open Phase-A defect (their final receipt, honest UNMEASURED state); CPU-side replay is this lane's validation surface per the SPLIT deal | deferred WITH the hang, not tuned away; the phase-C lane inherits the check |
| push_N external force, event-DFS/poscorr physics internals | engine | physics, not reflex; outside this lane's interface | none |

## Counts (the fidelity manifest numbers)

- Level 1: 4/4 law families PORTED, 0 deferred.
- Level 2: 21 families carried: 19 PORTED + 1 NOT-CARRIED (wave 34, reverted
  upstream — parity with the ship) + 1 superseded-and-carried (the wave-30
  unload-lift face lives inside the wave-32 min-form deadline's arithmetic
  and the wave-33 stand-first read; no separate law remains in the ship
  bytes). Deferred: 0.
- Level 3: 1/1 PORTED.
- Total: 25 law families ported across levels 1-3 + 2 carried-equivalent
  (wave 34 not-carried, wave 30 superseded) + the deferred diagnostics/
  reset/tau-path items above, each owned where it was already proven.
