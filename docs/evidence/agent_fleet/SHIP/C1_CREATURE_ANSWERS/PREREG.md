# C1 CREATURE ANSWERS — PREREGISTRATION

Fleet agent C1r "creature-answers" · 2026-09-13 · branch `astra/tasks/matter-kernel-format-01`
Both blind judges converged: **the creature must ANSWER** — "it never initiates
anything", "the fantasy stops at the HUD". This prereg opens BEFORE the build
(Rule 0): each reflex states STATEMENT / PREDICTION / FALSIFIER, and every
number is derived in [DERIVATIONS.md](DERIVATIONS.md) from measurements taken
on the CURRENT binary (floors_scratch8163.json, walk_scales_scratch8163.json,
stance_floor_scratch8163.json) or from the repo's own named bars. Nothing here
is tuned by taste; the constants that ARE taste are marked **AWAITING ASTRA**
(lead owns window #8; the external AI derives the honest reflex set in
parallel and lands on this plumbing).

Owns: `ChimeraEngine/engine/membrane_tick.cpp` + `.hpp` + the `/tick_reflex`
route in `ChimeraEngine/engine/main.cpp`. Default state: **OFF on boot** until
the lead verifies at window #8 (route-armed only; the page reads state fields
later — zero page edits).

---

## R1 — AUTONOMIC BREATHING

**STATEMENT.** A breath is the torso cell's VOLUME TARGET changing, not a load
on the sealed water. The engine's sealed cells are water-stiff
(kappa = 4.6e-10 Pa^-1): a visible tidal swell, if the kappa law saw it, would
answer **14.9 MPa** — 99% of the skin yield — for the allometric tidal volume.
A real animal breathes through a COMPLIANT thorax, not its coelom. Therefore
the breath is realized as a sinusoidal volume-target offset with its geometric
shadow on the surface (raised-cosine profile over the torso cell's y-band,
along authored normals), applied as the last surface pass so the pressure law,
the conservation export, and every gait measurement are structurally blind to
it. Rate from Stahl's mammalian respiratory allometry at the engine's own
mass (13,824.5 kg): f = 53.5·M^-0.26 = 4.485 breaths/min → period 13.38 s →
ω = 0.4697 rad/s. Amplitude from the tidal volume V_T = 6.2 mL/kg·M^1.01 =
0.0940 m³ = 0.752% of the measured torso v0 (12.509 m³) = 1.45 mm mean linear
swell over the measured 64.69 m² torso skin (raised-cosine peak ≈ 2.9 mm).

**PREDICTION.** With reflexes armed at rest: /tick_state `reflex_*` fields
show the phase advancing at 4.485/min and breath displacement oscillating
±1.45 mm (peak 2.9 mm), while (a) max|P| over all sealed cells stays EXACTLY
0 (V1c/V10's bar), (b) |conserve_pct| stays at its measured noise (1.2e-4),
(c) /verts torso min/max y oscillates at the breath period with zero drift at
suspend, (d) gait_verify passes 15/15 with breathing armed.

**FALSIFIER.** (a) If /tick_state max|P| oscillates at the breath period with
amplitude ~ΔP = ΔV/(κ·V0) ≈ 14.9 MPa, the breath leaked into the kappa inputs
(wrong pass order) — design falsified, move the breath after the volume block.
(b) If suspending the oscillator leaves /verts drift above the measured
zero-motion reference (M5: exactly 0 m over 4 s), the displacement is
accumulating state, not a pure function of phase — falsified.
(c) If the breathing rate or amplitude had to be changed to make the bars
pass, the derivation broke — stop and report.

**AWAITING ASTRA**: rate + amplitude constants (the honest interim values are
1.0x the allometric numbers; the perceptual lever — a game-scale amplitude
multiple — is taste and therefore not mine to set).

## R2 — LOCAL FLINCH ARC

**STATEMENT.** A flinch is a two-neuron arc: stimulus (a sealed cell whose
pressure crosses a threshold on a RISING edge) → response (the nearest limb's
binding-derived strut pin flexes toward its raising branch, decaying with the
tissue tau). No central planner: the engine's gait machine already resolves
the per-side drive pins from the vertbind (the V3a net-weight law —
independently re-derived from the snapshot blobs in Python during this prereg,
matching the engine's enable log exactly: L 17/15, R 18/16). Threshold
1.0e5 Pa = 2x the repo's named gentle-hand bar (GAIT_P_RELAX_PA) = 0.67% of
the skin yield (15 MPa, Yamada, in the header) = 150x below damage. Measured
placement: rest and stance-idle floors are EXACTLY 0 Pa; a 10 kN belly touch
answers 51 kPa (tolerated — gentle handling); the 20 kN demo press answers
432 kPa (flinches); 50 kN answers 9.1 MPa (flinches hard). Amplitude =
STANCE_THETA_MAX_DEG (5 deg): a reflex may never demand more of the ankle
than the balance rung's own derived authority. Decay tau = tau_relax_ (0.5 s,
the named tissue family); attack instant (a reflex, not a servo ramp).

**PREDICTION.** Armed at rest: a 20 kN belly touch → the touched side's strut
pin shows a ~5 deg flex decaying to zero in ~2.5 s (5 taus) in /tick_state
(`reflex_flinch_env_*`) and the limb visibly withdraws in /verts; a 10 kN
touch fires nothing; with `pressure_coupling:false` (the nerve cut) the
identical 20 kN touch fires nothing.

**FALSIFIER.** (a) A flinch that fires without its stimulus (nerve cut +
identical press → any envelope > 0) is an animation — falsified. (b) A
falling crossing (post-walk pressure collapse) that fires — falsified (the
trigger is rising-edge only). (c) A flinch that writes a pin while an armed
rung owns it — falsified by construction; the gate is the point.

**GATE (measured-mandatory).** While `gait_on_`, or stance under load
(`stance_on_ && gravity_on_`), the flinch is SUPPRESSED: the walk's own
per-cell pressures measured 24 MPa median / 86 MPa max — 240x-860x the
threshold — an ungated flinch fires at every stride and fights the walker.
Plus a 1.0 s quiet window after gait disarm (2 tissue taus) so the post-cut
pressure collapse cannot ring a crossing (defer, not lose: a pressure that
persists past the quiet window still fires its rising edge).

**AWAITING ASTRA**: threshold (behavioral: what the creature tolerates) and
amplitude (perceptual).

## R3 — STARTLE COUPLING

**STATEMENT.** A startle is the WHOLE-BODY reflex: a sharp pressure TRANSIENT
(rate, not level) couples a small nudge INTO the stance servo — the one
whole-body actuator that already exists — kept inside its existing 5 deg cap.
Detector: max over sealed cells of max(0, dP/dt) crossing 1.0e6 Pa/s
(rising only — a hit increases pressure; a release does not startle). The
measured floors it must clear: rest and stance-idle are EXACTLY 0 Pa with
0 Pa/s; the light ladder end (500 N touch) steps 3.6 kPa in one tick
(3.34 ms, 299 Hz measured) ≈ 1.1 MPa/s — fires; sub-tick onset means any real
contact is a step, so the threshold is a floor-sensitivity choice, 1.0e6 Pa/s
≈ 3.3 kPa/tick. Nudge magnitude = GAIT_SINK_M / S_measured = 0.01 m / 0.283
m/rad = 2.03 deg — one rest-sink quantum of lean through the stance channel
the engine itself measured (S = 1/stance_kp_; the prereg audit reference
0.283 m/rad when stance has never run). Direction: away from the stimulus
point's z-offset from the body center (the sagittal axis is the only actuated
lean subspace — the stance prereg's own disclosure); midline ties resolve
deterministically. Decay tau = 0.5 s; envelope-gated refractory (re-trigger
below 10% envelope); active ONLY while the stance rung is armed
(stance_on_ && gravity_on_ && !gait_on_) — the coupling is into the stance
machine, and G1 suppresses it under gait.

**PREDICTION.** Armed, gravity+stance on, settled: a sharp 2 kN touch →
`stance_ankle_deg` shows a ~2.03 deg bias pulse away from the touch, decaying
in ~2.5 s, `reflex_startle_last_tick` stamps the trigger; the ankle angle
never leaves the 5 deg cap; the nerve cut makes the identical touch inert;
gait_verify passes 15/15 armed (the startle is suppressed under gait and
latent in teardown).

**FALSIFIER.** (a) A startle under gait (the cut transient false-firing) —
falsified (quiet window). (b) A startle on pressure RELEASE (falling) —
falsified. (c) An ankle command beyond the 5 deg cap — falsified by
construction (min with the remaining cap headroom).

**AWAITING ASTRA**: threshold and nudge magnitude.

---

## THE INTERACTION LAWS (shared)

1. **The walker owns its pins.** gait_on → flinch + startle fully suppressed;
   quiet window 1.0 s post-disarm (defer). Measured reason: walk pressures
   exceed the flinch threshold by 240x; the gait machine is the sole writer
   of the drive pins while armed.
2. **Balance owns the ankles under load.** stance under load suppresses the
   flinch (its response limb IS an ankle pin on this body); the startle is
   the only reflex allowed into that state, and only as a composer
   (stance_th_ + bias, the gait composition precedent), inside the cap.
3. **The nerve cut is a route flag**, built into the battery as the negative
   control: `pressure_coupling:false` severs pressure → reflex-intent for
   flinch AND startle; breathing is not pressure-driven and continues.
4. **Breathing is measurement-invisible by design** (pass order): pressures,
   conservation, foot sets, lean, depth all read the pre-breath surface.
   Window #8 MEASURES this (R1's prediction), it is not assumed.
5. **Default OFF on boot**; a mesh swap (init) clears all reflex state (the
   C1 stale-index crash class); deterministic off (the flex-0 precedent):
   disarm zeroes envelopes, phase, and any reflex-owned pin.

## THE PRE-BUILT FALSIFIER

`tools/gait_verify.py` (15 bars) must pass on a scratch with reflexes ARMED —
the armed run is window #8's first act (procedure: WINDOW8.md). The control
leg (reflexes absent, current binary) was run at prereg time: 15/15 PASS
(gait_verify_control_scratch8164.json).
