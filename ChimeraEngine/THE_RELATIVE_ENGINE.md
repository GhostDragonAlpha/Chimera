# THE RELATIVE ENGINE — why refusing a global frame is the whole trick

> Written 2026-07-26, from the operator's observation: *"it's almost like we have to generate the
> world's first relativity gaming."* The instinct is right, and the code is further along than it
> looks. This document sharpens the claim, says honestly what is and isn't true, and shows why the
> physics here is **load-bearing engineering** rather than decoration.

---

## 1. The claim, stated precisely

Every other engine has **one global coordinate system**. Unreal and Unity give you a float32 world,
and when your world gets big they bolt on *origin rebasing* — a workaround that periodically shoves
everything back toward zero so the floats stop shaking. Scale is a problem to be **managed**.

Chimera refuses the global frame. A coordinate only exists **relative to a membrane**, and a thing's
address is the **path of membranes you crossed to reach it** (`Membrane.path()`). That is not a
graphics trick; it is the same move relativity makes: *there is no privileged frame, only local
frames and the transformations between them.*

**And the payoff is not philosophical, it is numerical.** If a coordinate can never exceed its
membrane's extent, then precision stops being a problem *by construction* — not by rebasing hacks.
The reason you can fly from orbit to a footprint without a loading screen is the same reason the
maths is stable: nothing is ever measured against a distant origin.

**So: relativity is not a feature we would add to this engine. It is what the engine already is,
and it is what makes the hard problem tractable.**

---

## 2. What is already in the code (this surprised me)

`core/membranes.py` does not merely nest boxes. It carries a **clock law**:

| in the code | what it is |
|---|---|
| `C_LIGHT = 1.0e4` | the system's speed of light |
| `density()` | **relational** — a child has no density of its own, only one relative to its parent |
| `clock_rate() = sqrt(density)` | from the free-fall time `t ~ 1/sqrt(Gρ)`. **The size cancels** — two membranes of equal density tick alike whatever their size |
| `clock_rate_from_root()` | cumulative through the tree; `sqrt` is multiplicative, so it is the product of every level crossed |
| `light_ceiling_rate() = C_LIGHT / scale` | nothing internal can cycle faster than light crosses the region |
| `schwarzschild_scale(mass) = mass / C_LIGHT²` | `R_s = GM/c²` |

And the load-bearing sentence, already written in that file: where the density clock would exceed
the light ceiling, the region *can no longer talk to itself fast enough to hold together as one
object* — **it tears**. That is the Schwarzschild condition (`sqrt(Gρ) = c/R ⟺ R = GM/c²`) arriving
as a **consequence of the clock the verbs already run on**, not as a special case someone bolted on.

**Time already varies by depth in the hierarchy.** That is structurally a gravitational time
dilation. It is built, and it is currently unused.

---

## 3. Honest limits — what this is NOT

Being straight about this matters more than the slogan.

- **It is not Lorentz invariance.** There is no velocity-dependent dilation, no length contraction,
  no relativistic aberration or Doppler in the renderer. The clock law is `sqrt(density)` — the
  *dynamical/free-fall* time, a self-similarity law. It is physically motivated, and it is not
  Einstein's field equations.
- **It is not the world's first.** MIT Game Lab's *A Slower Speed of Light* (2012) does honest
  special-relativistic rendering; Space Engine and Kerbal handle scaled frames; several games use
  scaled space. Claiming "first" invites an easy correction and we do not need it.

**The claim that IS defensible, and is genuinely distinctive:**

> No engine makes **relative frames the architecture**. Everyone else has one global frame and
> patches around it. Here, locality is the primitive — and *time, level of detail, camera speed,
> numerical precision and object identity are all the same number*: `Membrane.depth()`.

That is a real structural difference, and it is worth saying plainly instead of overclaiming.

---

## 4. The consequence that matters most: **LOD of TIME**

Spatial LOD (fewer splats when far) is well understood and we have it trained. The thing almost
nobody does is the other half:

**Distant membranes should tick SLOWLY. Near ones tick fast.** `tick()` already returns exactly
that number. Coalesce/fracture applied to the *clock* instead of to geometry.

This is how a whole solar system stays simulated without costing everything: the planet you are
standing on runs at full rate; the station three orbits away advances in coarse steps; the outer
system barely moves. Nothing is frozen, nothing is faked — each region simply runs at *its own
natural rate*, which is the rate the physics gives it. And when you fly there, it refines.

**And it is free gameplay.** Time passing differently near dense objects is a mechanic no one has
built well — come back from a deep gravity well and the world has moved on. That is *Interstellar*
as a game system, and it drops out of a function that already exists.

---

## 5. How this changes the roadmap

Several roadmap items stop being separate features and become **one law**:

- **B1 scale-relative flight speed** is not a UI convenience. Speed relative to the current
  membrane's extent *is* the local light-ceiling analogue — the same `C_LIGHT / scale`.
- **B2 membrane traversal** already drives LOD, local up, precision **and now clock rate**, because
  they are all `depth()`.
- **D2 surface fracture** and temporal refinement are the same operation on different axes.
- **Picking returns a path**, which is simultaneously an address, an LOD level, and a clock.

**One number does all of it.** That is the argument for building the navigation layer
(Track B) directly on the membrane clock rather than as camera code with a speed slider.

---

## 6. First concrete steps (small, and they prove the idea)

1. **Wire `tick()` into the simulation loop** — advance each membrane at its own rate. Immediately
   makes a solar system affordable, and is a handful of lines.
2. **Camera speed = `k · C_LIGHT / scale` of the current membrane.** Removes the speed slider by
   deriving it, exactly as the roadmap's B1 wants.
3. **Show the clock in the HUD** next to the membrane path: rate relative to root. The first time
   you watch time change as you descend, the idea becomes real and testable.
4. **Witness it** — the project's own rule: a claim needs a measurement. Two clocks at different
   depths, run for N steps, and *show the divergence as a number*, not an assertion.

Then the optional, visible layer (aberration, Doppler, a hard `C_LIGHT` on ships) becomes a
**gameplay choice**, not an architectural one — because the architecture is already relative.
