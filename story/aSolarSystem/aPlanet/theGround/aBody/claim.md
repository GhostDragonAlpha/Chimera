# aBody — a body stands on the formed ground

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
