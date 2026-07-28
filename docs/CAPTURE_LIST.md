# THE CAPTURE LIST — everything the character must handle

> The complete domain the ONE policy must generalize over. Each axis below is a **membrane axis**;
> the game samples a point in the product space `(verb × terrain × gravity × surface × state)`, and
> the body must solve it. Trained all-at-once by **domain randomization** — randomize every axis
> per world, and the behavior *segments itself* by context because the policy senses (or is told) the
> context. This is how ANYmal robots walk real mountains; gravity/surface just add space-game axes.
>
> **Status:** DRAFT for the operator to prune / extend. Ranges are first-pass, grounded where noted.

## The principle — seen vs told

A membrane supplies a **local context**. The policy handles a condition either by **seeing** it
(sensing) or being **told** it (the membrane hands it over — for a game we always know the world's
physics, so telling is free and correct):

- **SEEN** (sensed each step): terrain shape (a heightmap patch under the body), foot contacts,
  proprioception (joint angles/velocities, root tilt), how the body is actually responding.
- **TOLD** (a constant the membrane provides): gravity, surface friction/softness, and the **command**
  (which verb to do). These are cheap inputs the policy conditions on.

One network: `act = π(proprioception, terrain_heightmap, command, gravity, surface)`.

---

## Axis 1 — VERBS (the command, TOLD)

| verb | description | reward source |
|---|---|---|
| **stand** | hold balance in place | hand-writable ✓ |
| **walk** | forward at a commanded speed | hand-writable ✓ |
| **run / sprint** | fast forward | hand-writable ✓ |
| **turn** | rotate heading in place / while moving | hand-writable ✓ |
| **strafe** | sideways while facing forward | hand-writable ✓ |
| **crouch / crouch-walk** | lowered stance, move | hand-writable ✓ |
| **jump / land** | leave ground, absorb landing | hand-writable ✓ |
| **stop / brace** | decelerate, plant, hold | hand-writable ✓ |
| **get-up** | stand from prone / fallen | mixed (mocap helps) |
| **belly-crawl / prone** | move on the ground | **needs mocap (AMP)** |
| **climb** | ladder / wall / steep face | **needs mocap (AMP)** |
| **mantle / vault** | pull up / over an obstacle | **needs mocap (AMP)** |
| **slide** | drop and slide under / down | **needs mocap (AMP)** |
| **take-cover / lean** | crouch behind, peek | **needs mocap (AMP)** |
| **aim / carry** | hold a pose while moving (weapon, load) | **needs mocap (AMP)** |
| **melee** | strike | **needs mocap (AMP)** |

**Data-free verbs train NOW; mocap verbs fold into the same policy as we source and retarget motion.**

## Axis 2 — TERRAIN (SEEN via heightmap)

| type | range (first-pass) |
|---|---|
| flat | baseline |
| slope up / down | 0° → ~35° (beyond ~35° needs hands → climb) |
| stairs up / down | rise 10–20 cm, run 25–32 cm (human code) — your "stair exerciser" |
| single steps / curbs | 5–45 cm |
| rough / rubble | noise amplitude 0–15 cm, varying wavelength |
| gaps / gullies | 0–1.0 m (step or jump across) |
| narrow / beams | width down to ~foot span (balance) |

## Axis 3 — GRAVITY (TOLD — the world's constant, m/s²)

| world | g | notes |
|---|---|---|
| zero-g | 0.0 | float / push off surfaces — a different regime |
| Moon | **1.62** | 1/6 Earth — long floaty strides |
| Mars | **3.71** | ~0.38 g |
| Mercury / Titan-ish | ~3.7 / ~1.35 | |
| Earth | **9.81** | baseline |
| super-Earth / high-g | up to ~20–25 (≈2–2.5 g) | heavy, careful, low steps |

Randomize continuously across `[0, ~25]`; the named worlds are the ones the game will actually visit.

## Axis 4 — SURFACE (TOLD — contact params)

| property | range | examples |
|---|---|---|
| friction | 0.1 → 1.2 | ice → rock/rubber; sand/mud effectively lower |
| restitution | 0.0 → 0.4 | dead ground → springy |
| softness / sink | rigid → deformable | rock → sand/snow/mud (feet sink) |

## Axis 5 — PERTURBATIONS & INITIAL STATE (randomized)

- **Start pose:** standing keyframe + noise; also mid-stride, off-balance, prone (for get-up).
- **Shoves:** random impulses to the torso/limbs (robustness — the "one-micron nudge" lesson made a training input).
- **Carried load:** extra mass on hands/back (later, for carry/aim).

## Axis 6 — BODY (LATER — morphology)

- Size / mass scaling, limb-length variation, **damage** (a weakened/disabled limb), **fatigue**.
- This is where the trained-body library ([[myosuite-myolegs-pivot]], the matter model) reconnects:
  the same policy conditioned on the *body* it's driving.

---

## Training implication

- The product space is huge, but **each axis is cheap to sample** — gravity and surface are single
  numbers; terrain is a generator; the command is one-hot/scalar. Randomize all per world.
- **Start with the data-free core:** `locomotion (stand/walk/run/turn) × terrain × gravity × surface`.
  This is provable and needs no motion data — it is most of what the operator described.
- **Add acrobatics via AMP** (crawl, climb, mantle, cover) into the SAME policy as mocap is sourced
  and retargeted to the 290-muscle body.
- **Curriculum:** begin easy (flat, Earth-g, high friction), widen the ranges as survival climbs —
  the standard terrain-RL recipe (Rudin et al., "Learning to walk in minutes").

## The one-line north star

> One policy. It is TOLD the world (gravity, surface) and the intent (the verb), it SEES the ground,
> and it moves a real 290-muscle human body correctly — on any planet, on any surface, doing anything
> a human does. Everything is a membrane; the policy is trained across all of them at once.
