# rhythm — stance⇄swing alternation is a LIMIT CYCLE, and that is the CPG   [CLOSED — the proof that earns the GPU]

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

## Witness: TESTED — the WEAK form is REFUTED (2026-07-28)
Built as a phase clock in the OBSERVATION (sin φ, cos φ) at ω_swing = 4.171 rad/s, on the synergy
base, warm-started from the stand, 15 iters. Gait witness, worst-of-5 (`gait_myobody.py`):
- **synergy + CPG (clock):  periodicity 0.15** (mean 0.36) — NOT A GAIT; stands ~still, dist −0.06 m
- **synergy control (no clock): periodicity 0.48** (mean 0.54) — RUN/TROT; travels, but falls 4/5

The prediction periodicity → 1.0 FAILED — the clock made it WORSE. Iteration 0 was byte-identical
between the arms, so it is a clean one-variable A/B.

**Why it failed (honest):** this was the WEAK form. The phase only *informed* the observation, and
nothing in the reward rewarded phase-locking, so PPO had no gradient to synchronise with the clock —
it stayed decorative and the policy drifted to the laziest optimum (stand still). The STRONG form this
membrane's own `outputs.json` specifies — the phase DRIVES the muscle pattern (activation = f(φ)) and
the policy only *stabilises* it — is UNTESTED.

**Deeper finding:** neither policy WALKS (one freezes at periodicity 0.15, one falls forward at 0.48).
The base task selects stand-or-fall, not walk — a problem UPSTREAM of rhythm. And per the studio's own
law (PROGRAM the rules / TRAIN the numbers), a rhythm is a NUMBER: hand-coding a Hopf oscillator may be
the wrong tool, versus TRAINING the gait from reference motion (imitation), which the project already
found "has the reward RIGHT".

The Hopf limit-cycle THEOREM (above) stands. **Status: rhythm/ is OPEN. Do not claim a limit cycle.**
