# walking — the body crosses the ground it stands on   [FRONTIER — not yet closed]

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
> **[docs/THE_LAW.md](../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

**Principle (the whole membrane in one line):** walking is CONTROLLED FALLING. You
lean past your base of support, begin to topple, and catch the fall by placing a foot
at the capture point — then do it again on the other side. Standing is the resolved
state; walking is a *rhythmic, deliberate departure from it and return to it.*

## What this membrane INHERITS (the seams, already closed above)
- from `aPlanet/`    → **g**  (Earth 9.81 / Moon 1.62 / Mars 3.72) — the ONE number
                        that re-derives everything below when the world changes
- from `theGround/`  → **μ_s = tan(repose) ≈ 0.84**, surface normal, slope
- from `aBody/`      → **M, H, L, m_leg, d, I_hip**, and a proven static balance

Because g is inherited, this whole chapter is **gravity-portable**: the Froude number
`Fr = v²/(gL)` makes the gait on any world dynamically similar. That is the space
game's locomotion axis — one derivation, every planet.

## Child membranes to close (the derivation, in order — each earns the next)
- `stance/`  — the inverted pendulum. Timescale `ω₀ = √(g/H)`; stay balanced by
               keeping the capture point `XcoM = com + v/ω₀` over the base of support.
               [inherits g, H]
- `step/`    — the controlled fall and catch. Leave the base on purpose; place the
               swing foot at XcoM to arrest the topple. [inherits ω₀ from stance]
- `swing/`   — the swing leg is a compound pendulum, `T = 2π√(I/mgd)`. Its natural
               period SETS THE CADENCE (ballistic walking). [inherits m_leg, d, I_hip, g]
- `rhythm/`  — stance and swing ALTERNATE, left/right, in antiphase. Two coupled
               oscillators alternating = a LIMIT CYCLE. **This is where the CPG is
               earned** — a feedforward reflex has no clock; a limit cycle needs an
               oscillator. [inherits the two periods above]
- `contact/` — the foot meets the ground: friction cone (μ_s from theGround), center
               of pressure, never airborne beyond the step. The deepest membrane —
               the "finger touches finger." [inherits μ_s]

## Why (terminal → PHYSICS through its children) — DERIVATION COMPLETE
All five children are now derivation-CLOSED — Newtonian / dynamical-systems theorems
from the inherited constants, each predicting a fact it was not fitted to. walking is
therefore **proven on paper**; it rests on PHYSICS through its subtree. What remains is
the WITNESS: `stance/` is already witnessed (the stand); `step/ swing/ rhythm/ contact/`
await one gait run. The load-bearing proof is `rhythm/` — the Hopf oscillator's provable
stable limit cycle, tuned to ω_swing = 4.170 rad/s, antiphase-coupled, contact-entrained.
Reference: `docs/THE_MATHEMATICS_OF_WALKING.md`. The falsifiable witness: periodicity → 1.0.
