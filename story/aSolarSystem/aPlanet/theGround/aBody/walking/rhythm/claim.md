# rhythm — stance⇄swing alternation is a LIMIT CYCLE, and that is the CPG   [CLOSED — the proof that earns the GPU]

**Claim:** Walking is stance and swing ALTERNATING left/right in antiphase — a closed,
self-restoring loop in phase space (a limit cycle). A feedforward policy has no clock
and cannot hold a limit cycle; an OSCILLATOR can, provably. That oscillator, tuned to
the swing period and entrained by ground contact, is the central pattern generator.

## Why the feedforward policy failed (the measured fact this explains)
A limit cycle needs a PHASE state φ that advances monotonically and wraps 0→2π. PPO's
feedforward net maps obs→action with no internal phase — it must reconstruct φ from
proprioception every step, so it drifts. Measured: **periodicity 0.53** (a real cycle is
~1.0). Not a reward bug — a missing STATE VARIABLE.

## The proof that a limit cycle EXISTS (Hopf oscillator, one per leg)
State (x, y), dynamics:
  `ẋ = α(μ − r²)x − ω y`
  `ẏ = α(μ − r²)y + ω x` ,   `r² = x² + y²`.
Polar (r, θ):  `r ṙ = x ẋ + y ẏ = α(μ − r²) r²`  ⇒  **ṙ = α(μ − r²) r**
             `θ̇ = (x ẏ − y ẋ)/r² =` **ω.**
The radial ODE has a fixed point at **r = √μ**; derivative there is `α(μ − 3μ) = −2αμ < 0`
⇒ ASYMPTOTICALLY STABLE, attracting every r>0. θ rotates at constant ω. So every
trajectory (bar the origin) converges to the circle r=√μ and circulates forever: a
**globally stable limit cycle.** (Poincaré–Bendixson gives the same: bounded flow, sole
fixed point unstable ⇒ a limit cycle.) A THEOREM — it holds before a single training step.

## Tune it to THIS body, couple it for alternation, close the loop with contact
- **Frequency:** set `ω = ω_swing = 4.170 rad/s` (from swing/) — the oscillator ticks at
  the legs' own resonance.
- **Antiphase coupling:** two oscillators (L, R) coupled to `Δφ = π` lock into alternation
  (Kuramoto: antiphase is the stable state) → left stance while right swings, then swap.
- **Sensory entrainment:** heel-strike (contact/) resets φ each step, so the CPG locks to
  the real mechanics: a push changes contact timing → resets phase → adjusts the next step
  → catches the fall (step/'s capture point). Closed loop mechanics↔oscillator (Taga 1991).
  THIS is what makes it robust, not merely rhythmic.

## Prediction it was not fitted to (and the falsifiable GPU test)
A limit cycle RETURNS to itself after a perturbation. So adding the CPG must drive
**periodicity → 1.0** and **worst-of-N robustness → 1.0**, precisely because the phase
state was the missing piece — and if it does NOT, this derivation is wrong. We know the
number to watch (periodicity) and the value that confirms (≈1.0) BEFORE spending one
GPU-hour. That is derive-before-train.

## Why (terminal → PHYSICS)
Dynamical-systems theorem (stable limit cycle of the Hopf normal form) + the measured
swing frequency ω_swing.

## Witness: PENDING
Gait run with the CPG-augmented policy: periodicity → ~1.0, duty > 0.5, robustness → ~1.0.
Receipt-to-be: `gait_myobody.py` on the CPG policy.
