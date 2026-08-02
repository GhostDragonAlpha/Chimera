# aBody — a body stands on the formed ground

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
> **[docs/THE_LAW.md](../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

**Claim:** A full musculoskeletal body, placed on the settled surface, holds itself
upright against gravity — a balanced inverted pendulum, witnessed by foot contact.

## Math that closes (the constants walking inherits)
Measured from `myobody.xml`: M = 82.04 kg, CoM height H = 0.965 m, leg length
L = 0.845 m, leg mass m_leg = 13.65 kg (17%), hip→leg-CoM d = 0.374 m,
I_hip = 2.879 kg·m². Standing = keeping the CoM's ground projection inside the base of
support; the inverted pendulum's timescale is `ω₀ = √(g/H)` (g inherited from aPlanet).

## Why (terminal → PHYSICS, measured)
The body stands: 77% survival across randomized starts, witnessed by CONTACT (foot
resting on formed relief, not the floor). Reward is process-based (be still), no pose
target — stillness climbed 0.85 → 0.93 in lockstep with survival, and the arms' rest
position EMERGED. Receipts: `ChimeraEngine/train_myobody.py`, the stand policy, the
contact witness.

## OPEN edge (honest plot hole)
The body's *constants* are measured from a real model, but its *morphology is adopted*
(MyoSuite myobody), not yet GROWN from aPlanet's chemistry and gravity. This membrane
is proven to STAND (physics); its ORIGIN — why this body on this world — is not yet
closed. It does not block walking (walking inherits the measured constants either
way), but it is a Chekhov's gun to fire later.

## Outputs (handed DOWN) → outputs.json
M, H, L, m_leg, d, I_hip, and the proven capability: static balance (stance).

## Children
- `walking/` — the body crosses the ground it stands on
