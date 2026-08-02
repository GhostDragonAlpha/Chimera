# step — controlled falling, caught at the capture point   [derivation CLOSED]

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
> **[docs/THE_LAW.md](../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

**Claim:** To move, you leave the base of support ON PURPOSE — lean until the capture
point passes the front edge, begin to topple (stance/'s unstable mode), and catch the
fall by planting the swing foot at the capture point. Every step is a caught fall.

## Variables
- ω₀ = 3.188 rad/s                   ← stance/
- v = CoM forward speed; b = foot offset ahead of CoM
- g = 9.81, H = 0.965                ← aPlanet, aBody

## Math that closes
Foot placement that arrests forward speed v:
  **b = v/ω₀**   (plant at the capture point ahead of the CoM).
After the plant the CoM VAULTS over the new stance foot — inverted-pendulum arc again —
trading KE↔PE (Cavagna pendular recovery ~65%): CoM highest at mid-stance, lowest at
double-support. Speed needed to clear the vault apex:
  `½v² ≥ gH(1 − cos θ_step)`  →  a **minimum walk speed** exists; below it you stall
and must stop or fall.

## Prediction it was not fitted to
`b = v/ω₀` ⇒ step length grows LINEARLY with speed, and (ω₀=√(g/H)) steps are 2.46×
longer per unit speed on the Moon. The existence of a minimum walking speed — very slow
walking is unstable, you either stand or walk above a threshold — is a lived fact the
model predicts.

## Why (terminal → PHYSICS)
Capture-point dynamics (Hof) + energy conservation over the inverted-pendulum vault,
from ω₀ and g.

## Witness: PENDING
Gait run must show: step length ∝ speed, foot landing near XcoM, CoM height oscillating
(the vault). Observable in `gait_myobody.py`.
