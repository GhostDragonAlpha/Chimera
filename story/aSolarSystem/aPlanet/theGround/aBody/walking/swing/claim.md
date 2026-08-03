# swing — the leg is a pendulum, and it sets the cadence   [derivation CLOSED]

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

**Claim:** The swing leg hangs from the hip and swings forward as a COMPOUND pendulum.
Its natural period is not chosen — it is the leg's resonance, and it sets the walking
cadence (ballistic walking, Mochon & McMahon 1980).

## Variables (all traced, all measured)
- I_hip = 2.879 kg·m²  (leg inertia about hip)     ← aBody
- m_leg = 13.65 kg,  d = 0.374 m (hip→leg-CoM)     ← aBody
- g = 9.81 m/s²                                    ← aPlanet

## Math that closes
Compound-pendulum period:
  **T = 2π√(I/(m g d)) = 2π√(2.879/(13.65·9.81·0.374)) = 2π√(0.0575) = 1.506 s.**
One step = a half-swing (leg goes from behind to in front): **t_step = T/2 = 0.753 s.**
Cadence = 60/0.753 = **79.7 steps/min** (the metabolically cheapest cadence; walking
faster needs active hip torque ABOVE this baseline).
Oscillator frequency handed to `rhythm/`: **ω_swing = 2π/T = 4.170 rad/s.**

## Prediction it was not fitted to
`T ∝ 1/√g`. On the Moon (g=1.62): T = 3.71 s, t_step = 1.85 s, cadence ≈ 32 steps/min —
legs swing 2.46× slower. This is WHY Moon walking looks slow-motion, and (with the Froude
walk→run drop to 0.83 m/s) WHY Apollo astronauts abandoned walking for BOUNDING: hopping
decouples the body from the slow pendular swing. Predicted, never fitted.

## Why (terminal → PHYSICS)
Physical-pendulum period from measured I, m, d, g. A theorem, not a tuning.

## Witness: PENDING
Gait run must show natural cadence ≈ 0.75 s/step at the preferred speed. Observable in
`gait_myobody.py` (spacing of the periodicity peaks).
