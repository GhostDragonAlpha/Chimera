# stance — the inverted pendulum that must not fall   [derivation CLOSED]

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
