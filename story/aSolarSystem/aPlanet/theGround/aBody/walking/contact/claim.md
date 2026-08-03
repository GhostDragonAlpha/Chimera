# contact — the foot meets the ground (the finger touches the finger)   [derivation CLOSED]

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

**Claim:** The deepest membrane: a foot pressing the ground. The ground's own repose
angle becomes the friction cone the foot lives inside; the center of pressure must stay
under the foot; in walking a foot is ALWAYS down (no flight). This same primitive is a
hand gripping an object.

## Variables
- μ_s = 0.84  (= tan 40°, the repose angle)     ← theGround
- g = 9.81 m/s²                                  ← aPlanet
- N = normal force, F = friction (tangential), CoP = center of pressure

## Math that closes
- **Friction cone:** no slip iff `|F| ≤ μ_s N`. Max push angle from vertical =
  `arctan(μ_s) = 40.03°` — exactly the ground's repose angle (that is where μ came from).
  Max horizontal acceleration: **a_max = μ_s g = 0.84·9.81 = 8.24 m/s².**
- **Center of pressure / ZMP:** the ground reaction acts at a point that must stay inside
  the foot polygon; at the edge the foot tips — the boundary of dynamic balance.
- **Never airborne:** walking keeps ≥1 foot down (duty factor > 0.5). A flight phase
  (duty < 0.5) is running — a different membrane.

## Prediction it was not fitted to
`a_max = μ_s g`. On ice (μ≈0.1): a_max = 0.98 m/s² — you can barely start or stop, so ice
walking becomes a shuffle of tiny steps. On the Moon (g=1.62, same μ): a_max = 1.36 m/s² —
harder to change direction, another push toward the bounding gait. Both fall out of μ and
g; neither fitted.

## The finger-touches-finger note
Foot-on-ground and hand-on-object are the SAME primitive: close until the friction cone
holds. GRAB = keep contact within the cone; the object sets the scale. So contact/ is the
shared floor of walking AND manipulation — the bottom of the whole story.

## Why (terminal → PHYSICS)
Coulomb friction + statics of the contact wrench, from measured μ_s and g.

## Witness: PENDING
Gait run must show: no foot slip (friction respected), CoP inside the foot, duty > 0.5
(never airborne). Observable in `gait_myobody.py`.
