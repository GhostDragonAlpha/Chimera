# swing — the leg is a pendulum, and it sets the cadence   [derivation CLOSED]

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
