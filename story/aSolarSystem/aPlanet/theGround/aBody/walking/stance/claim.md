# stance — the inverted pendulum that must not fall   [derivation CLOSED]

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

**Claim:** A standing body is an inverted pendulum — mass M at CoM height H over the
ankle. It is UNSTABLE: any lean grows. Balance = keep the capture point over the base
of support.

## Variables (all traced)
- M = 82.04 kg, H = 0.965 m          ← aBody
- g = 9.81 m/s²                      ← aPlanet
- θ = lean from vertical; v = CoM horizontal speed

## Math that closes
Torque about the ankle: `I θ̈ = M g H sin θ`, with `I ≈ M H²` (point mass).
→ `θ̈ = (g/H) sin θ ≈ (g/H) θ`  (small angle) — the UNSTABLE pendulum,
`θ(t) = θ₀ e^{±ω₀ t}`, natural rate
  **ω₀ = √(g/H) = √(9.81/0.965) = 3.188 rad/s.**
Time constant `τ = 1/ω₀ = 0.314 s`; a lean DOUBLES in `ln2/ω₀ = 0.217 s` — ~0.2 s to react.
Balance (Hof 2005): upright iff the extrapolated CoM (capture point)
  **XcoM = x_com + v/ω₀**
lies inside the base of support. Outside → you must step to it (→ `step/`).

## Prediction it was not fitted to
`τ = √(H/g)`. On the Moon (g=1.62): ω₀=1.30 rad/s, τ=0.77 s — you fall **2.46× slower**,
which is why low-g feels forgiving. Taller bodies fall slower too (τ∝√H): a toddler
topples fast, an adult slowly. Neither fitted; both true.

## Why (terminal → PHYSICS)
Newton's second law for a rigid pendulum, from measured M, H, g. True in an empty universe.

## Witness: WITNESSED
The stand — 77% survival across randomized starts, contact-witnessed (aBody). The
balanced inverted pendulum is the state we already hold. Receipt: `ChimeraEngine/train_myobody.py`.
