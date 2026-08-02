# THE ACTUATED MEMBRANE — matter that DOES something

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
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Written 2026-07-26 from the operator's correction: **not relative frames — relative STATES.**
>
> *"If you want to apply thrust, we'll have to actually make a thruster that attains a certain
> state, and then wherever it's connected to, it will apply the force inside the physics simulation
> where each membrane floats free based on the constraints of physics."*
>
> *"If it stumbles in the game you stumble for real and you fall down and then you have to wait
> until your body picks itself back up again, just like in real life. Because your muscles are
> relative to their location and what they're attached to."*
>
> *"With the muscles, we'll attach them to a nervous system — trained algorithms of where to put
> your hands and feet based off surrounding state conditions and what the input is."*

---

## 1. The mechanism, in one paragraph

A **membrane** is not just a boundary — it holds matter, and matter **does** something. An actuator
is a membrane whose matter can **attain a state** (a `Verb`: two states and the dial between them).
It is joined to other membranes through **ports** — a port knows *where* it is, *which way it
faces*, and *what flows through it*. When an actuator's dial moves, the resulting force is applied
**at its port, in the frame of whatever it is attached to**. Every membrane floats free; the
constraints do the rest. **Motion is not authored — it is what happens.**

**A thruster and a leg muscle are the same object.** Both attain a state; both push at a port;
both move whatever they are bolted to. The only difference is what decides the dial: a pilot's
input, or a **nervous system**.

**Nothing is animated.** There is no walk cycle, no stumble animation, no get-up animation. You
stumble because the forces did not work out, and you get up because the nervous system drives the
muscles that get you up. That is the whole reason to imitate nature: *we have to provide the
functionality of the matter inside the membrane.*

---

## 2. What is ALREADY BUILT (most of it, and it is proven)

This is not a from-scratch design. Verified in the code today:

| piece | where | status |
|---|---|---|
| **Port** — "a stud: where a membrane connects, facing which way, and **what flows** through" (`at`, `facing`, `size`, typed `kind`) | `core/membranes.py` | **built** — this IS the force attachment point |
| **Verb / State** — two states that differ + the dial between them; extrapolation past [0,1] allowed | `core/membranes.py` | **built** — a muscle *is* this (relaxed ↔ contracted) |
| **Gate** — the dial cannot advance until something MEASURED is true | `core/membranes.py` | **built** — progression, and also "can this limb move yet" |
| **One skeleton for physics, flesh AND render** — the 17-bone evolved body; the creature that learned to walk IS the creature you see move | `core/rig.py` | **built, witnessed** |
| **Bones → MJCF** — real actuators, joints, torque; XML nesting IS the kinematic tree | `core/mjcf.py` | **built** |
| **The nervous system** — a trained brain driving those actuators, whole population in one GPU kernel | `core/trainables/brain_gpu.py` | **built, 2358 evals/s** |
| **The gait WITNESS** — Hildebrand footfall, duty factor, **periodicity**; a foot is *discovered* (a link that touches ground sometimes), never declared | `core/gait.py` | **built** — and it is what caught a fraud |
| Typed matter (muscle/bone/skin) grown by differential adhesion | `core/matter.py`, `core/limb.py` | **built** |

**So: a muscle-driven body, with a trained nervous system, walking under real physics, with an
honest witness — already exists.** The operator's architecture is not speculative here.

---

## 3. The honest gaps

1. **No runtime physics loop.** MuJoCo is used for *training*, offline. The game has no
   constrained-body solver running per frame. This is the biggest gap.
2. **Actuators are not expressed through Membrane + Port yet.** `mjcf.py` builds from a `bones`
   list, not from the membrane tree. The two models need to become one.
3. **The nervous system is a single-gait policy**, not *"where to put your hands and feet based on
   surrounding conditions and input."* That is goal-conditioned, terrain-aware control — a genuinely
   harder training problem than the flat-ground gait already solved.
4. **Nothing to stand on.** Terrain exists (`PlanetOnion`) but is not connected to the splats or to
   contact (roadmap A1 / E1).
5. **The player is not a creature yet** — the trained body is an *evolved* creature, not a human.

---

## 4. Two lessons this project already paid for — do not re-learn them

- **ONE ROLLOUT IS A COIN TOSS.** The celebrated 13.5-body-length walker had **periodicity 0.25**
  (no repeating cycle at all) and lost 5.5 body lengths to a **one-micron** change in start height.
  No attractor → no limit cycle → **no gait**. Score from N randomised starts and keep the WORST.
- **CHECK THE INHERITED CONSTANTS.** That same walker ran at `TORQUE = 22 N·m` on a 0.622 kg body —
  **35 N·m/kg**, where a human hip manages about **3** — and it flung itself 3.4 km into the air.
  A body permanently in flight has no contact to build a gait out of. *Actuator strength is physics,
  and it must be measured against the real thing.*

Both apply directly to muscles-as-actuators. A stumble must come from honest forces, or it is theatre.

---

## 5. The build order (smallest first, each one witnessed)

**Start with the THRUSTER, not the leg.** It is the same mechanism with none of the hard parts —
no balance, no gait, no nervous system. It proves the architecture end to end, and it is directly
the game (ships).

- **S1. Runtime bodies.** A membrane with mass + inertia that floats free, integrated per frame.
- **S2. Actuator + port.** A thruster membrane with a `Verb` (off ↔ full). Its dial produces a force
  applied **at its port's position, along its port's facing, in the parent body's frame**.
- **S3. WITNESS BALANCE.** Fire it **off-axis** and measure that the body's angular acceleration
  matches `τ = r × F` — Centre of Thrust vs Centre of Gravity, which is exactly the `BALANCE` verb
  the project's vision already names. A number, not a look.
- **S4. Joints.** Ports that constrain (hinge/ball) rather than just transmit — now bodies form trees.
- **S5. Muscle = the same thing across a joint.** A `Verb` whose dial produces torque about the
  joint it spans. `mjcf.py` already knows how to express this.
- **S6. Nervous system in the loop.** The trained brain reads state → sets the dials. Then: contact,
  stumble, recovery — none of them authored.
- **S7. Terrain contact.** Walk on `PlanetOnion` (needs roadmap A1/E1). Witnessed by CONTACT, per the
  project's own rule — `actor_exists` alone is verified-by-adjacency.

**The unification to keep in view:** S2 (thruster) and S5 (muscle) are the *same code*. If they
end up as two systems, the architecture was got wrong.

---

## 6. Why this is the right architecture

Every engine animates. A stumble is a clip; getting up is another clip; ragdoll is a *mode you
switch into* when the character is declared dead. The seams are exactly where the game stops being
believable.

Here there are no clips and no modes, because there is nothing to switch between: there is matter,
attached at ports, driven by states, under constraints. Falling over is not a failure case handled
by a different system — **it is the same system, producing a different outcome.**

That is what "imitating nature" buys, and it is why the functionality has to live *inside* the
membrane rather than in an animation track beside it.
