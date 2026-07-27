# THE BODY — first-person movement with real physics

> **The operator, 2026-07-26:** *"In normal video games the player doesn't fall down unless that's
> the design. This design is different... think about how Call of Duty works. They've got these
> states that are written into the game... it's all designed to simulate really moving around with
> your body. Now with REAL physics, Call of Duty would be amazing, and that's what we're going to
> bring to our game."*
>
> This document exists because he also said: *"I don't want to have to go backwards."* Everything
> below is organised around that one sentence — what is expensive to change later, and what is not.

---

## 1. What is actually different

Call of Duty has **states**: standing, crouched, prone, prone-on-back, ADS. Each is an authored
pose, and the transitions between them are hand-animated. There are maybe twenty states and a
hand-built table of which can reach which.

We do not have states. We have a **configuration** — every joint angle, the base pose, and every
velocity — and it is continuous. "Prone" is not a mode you enter; it is a region of that space you
happen to be in. There is no transition table because there is nothing to transition *between*.

That sounds like a loss of control. It is actually the whole product:

| | authored states | configuration space |
|---|---|---|
| falling over | only where scripted | wherever the physics says |
| getting up | one animation | depends on how you landed |
| pushed while prone | nothing, or a canned stagger | you slide, roll, or brace |
| low gravity | same animations, faster | different gait, and you learn it |
| carrying something heavy | an animation set | your balance actually changes |
| a slope | IK foot placement | you might not stay on it |

**The controller replaces the transition table.** That is the entire technical problem, stated once.

---

## 2. THE HONEST DESIGN CONSEQUENCE — read this before anything else

Real-physics movement is **slower and less precise** than animated movement, and no amount of
training fixes that, because it is not a training problem. It is what bodies are.

A player presses *prone* in Call of Duty and is prone in ~0.3 s. A real body takes ~1.5 s and can
be interrupted halfway. Games that have gone this way — Exanima most honestly — all end up feeling
deliberate and heavy. That is not a bug in their execution; it is the physics arriving.

So: **this engine cannot produce a twitch shooter, and trying will waste a year.** What it produces
is weight, consequence, and the feeling that your body is a thing you are operating rather than a
cursor you are pointing.

Which is *exactly right for a space game.* EVA is slow. Suits are clumsy. Falling over in 1/6 g and
having to get up is the good part, not the friction. **The constraint and the genre agree** — but
that should be a choice made on purpose now, not a discovery made in a year.

---

## 3. WHAT TO FREEZE FIRST (the anti-backwards list)

Four decisions are expensive to change after training starts. Everything else is cheap. If you get
these right up front you never go backwards; if you get them wrong you retrain from zero.

### 3.1 The observation space — WHAT THE BODY CAN SENSE
Add a sense later and every policy is invalid, because the network's input width changed.

`Player.sense()` already returns the right list, and it was built from the operator's own
observation that a ship's instruments and a body's senses are the same thing. **Freeze it now,
including things not yet used:**

| reading | why it must be in from day one |
|---|---|
| gravity **direction** (local up) | there is no global up on a sphere |
| gravity **strength** | §3.5 — this is what makes one policy work on every world |
| contact per limb (which parts touch, and how hard) | getting up is a contact problem |
| joint angles + rates (proprioception) | you know where your arm is with your eyes shut |
| base velocity + angular velocity (vestibular) | falling is detected here first |
| suit/skin temperature, pressure, O2 | EVA status, and it is already built |

Include gravity strength **even for the first Earth-only run.** A constant input costs one weight
and saves retraining everything later. This is the single highest-value line in this document.

### 3.2 The action space — WHAT THE BODY CAN DO
Joint torques, or muscle activations?

**Recommendation: joint torques, with a per-joint limit.** `nervous.py` already has antagonistic
muscles and they are the more honest model, but muscles double the action count (two per joint),
add the Hill force-length nonlinearity to whatever the policy must learn, and buy nothing the
torque limit does not for a body wearing a suit. Muscles matter for *creatures*; a torque limit
matters for a *person in a spacesuit*. Keep muscles for the bestiary.

Whichever is chosen, **it is frozen before the first run.**

### 3.3 The morphology — HOW MANY LINKS
Change the skeleton and every policy dies. Also: `CLAUDE.md` records that morphology is **not
GPU-batchable** (mujoco-warp batches N copies of *one* model), so a morphology change is not just a
retrain, it is a slow one.

The current `Player` is a torso with two rod "arms" — a placeholder that cannot get up because it
has no legs. Minimum viable body for get-up + walk + prone + reach:

```
pelvis (base)  ·  chest  ·  head
2 x [thigh, shin, foot]        <- get up, stand, walk
2 x [upper arm, forearm]       <- push off the ground, brace, reach, carry
```

~14 links, ~17 actuated DOF. That is deliberately the size of the standard MuJoCo humanoid, because
a very large published literature says bodies of that size are trainable and this is not the place
to be original. **The head is not decoration — it is the first-person camera mount, and where it
ends up during a fall is the shot.**

### 3.4 Whose physics does the training run on — AND THE TRAP
This is the most expensive mistake available, so it gets stated plainly.

Training needs thousands of rollouts per second. Our engine is CPU numpy. `mujoco-warp` measured
**2,358 evals/sec** on this machine versus pybullet's 70 — that is the only viable trainer.

**But a policy trained in MuJoCo and run in our engine is trained on a different world.** Contact
stiffness, integrator, joint limits and armature all differ, and a policy exploits exactly those
details. That gap is a sim-to-sim transfer problem, and discovering it *after* a training run is
the definition of going backwards.

**The fix, before any training: prove the two engines agree.** `core/mjcf.py` already turns a bone
tree into MJCF. Build the body once, export it, and witness that our integrator and MuJoCo produce
the same trajectory from the same initial condition to a stated tolerance. That is a
`dyadAnalysis` at the engine seam — two independent implementations of one law — and it is a day
of work that de-risks every training run after it.

If they cannot be made to agree, the answer is to **run MuJoCo as the game's physics** rather than
to hope. Better to learn that from a witness than from a policy that walks in training and
collapses in the game.

### 3.5 Gravity, and why it is an OBSERVATION and not a setting
The operator: *"we will need to train for various gravity strengths."* Right — and there are two
ways, one of which is much better.

- **Randomise** g each episode and let the policy become robust to it. Works, but produces a
  conservative policy that is mediocre everywhere.
- **CONDITION** on g: feed gravity strength in as an observation *and* randomise it. The policy
  learns `g -> behaviour` and adapts instead of hedging.

Conditioning is strictly better and costs one input, **and the body already has the sensor** —
`sense()['gravity']['strength']` is the inner ear. Train over `g ∈ [0.001, 12] m/s²` and one policy
covers Earth, Mars, the Moon, the asteroid, and a spinning station. This is standard domain
randomisation, and the conditioned variant is why it will feel *different* on the Moon rather than
just floatier.

---

## 4. THE ORDER — and why GETTING UP is first

The operator: *"the robot starts out on the ground as a pile of robot, and then it gets itself up
like a normal human that's waking up. That would probably be the first thing, because we'll need
that ability when we fall down, and we will be falling down in many different configurations."*

**This is correct, and the reasons are stronger than the intuition.**

1. **Get-up CONTAINS standing.** The last second of getting up *is* balancing. Train get-up and
   standing arrives free; train standing first and you have a policy that works from one pose.
2. **It is self-supervising.** "Are you up?" is trivially measurable — COM height above the local
   surface, only feet in contact, held for N seconds. No reference motion, no gait quality metric,
   no taste. Walking needs a target velocity *and* a quality measure, which is a much harder
   objective to write without encoding taste.
3. **Its initial-state distribution is the whole space.** A get-up policy is trained from bodies
   dumped on the ground in arbitrary configurations, so it sees the broadest state distribution of
   any skill. That is the opposite of the failure this project already paid for — the celebrated
   walker that scored `periodicity 0.25` and lost 5.5 body lengths to a one-micron nudge, because
   it had been trained from one initial condition and was selecting luck.
4. **There is direct precedent.** Hwangbo et al., *Science Robotics* 2019, trained ANYmal to
   recover to its feet from arbitrary fallen configurations with exactly this approach. This is not
   speculative.
5. **The game needs it most.** In a game where you genuinely fall, "can't get up" is unshippable.

### The batches
The operator asked what groups together. Skills share a training run when they share an
**objective**, not when they feel related:

| # | batch | one reward | why together |
|---|---|---|---|
| **1** | **POSTURE** — get up, stand, resist a shove, survive a landing | *reach and hold the upright configuration* | all four are the same goal from different starts; a shove is just a new start |
| **2** | **LOCOMOTION** — walk, turn, stop, speed control | *track a commanded velocity in the local tangent plane* | one reward with a commanded direction; needs posture solid first |
| **3** | **CONTACT SKILLS** — reach, grab, carry, brace, climb | *make and hold contact at the hand while staying up* | changes the mass distribution, so posture must already be robust |
| **4** | **ZERO-G / EVA** — orient, push off, catch a handhold | *reach a target attitude and stop* | no ground; a different problem, see §5 |

Prone, crouched, on-your-back and aiming are **not** separate items. They are configurations
batch 1 already passes through, and batch 3 lets you aim from them. That is the whole payoff of
throwing away the state machine.

Curriculum inside batch 1, easiest first: land supine on flat ground → arbitrary orientation →
random g → slope → a shove partway up.

---

## 5. EVA — and the thing already proven that nobody planned for

The operator asked for an EVA status. Every field it needs is built and witnessed:

- suit temperature, from the light field — **+148.5 C in lunar sun, cooling to +31.1 C after 3 h of
  night** (`player_witness` P4)
- the ground radiating at you — **1208 W/m² at lunar noon, 2.00× the sun alone** (`fields_witness` R3)
- pressure and breathability (A7), and radiator sizing at T⁴ (T4)
- micro-gravity is just the low end of the same conditioned policy from §3.5

And one mechanic fell out that was never designed:

> **`floating_witness` F4 — the falling cat.** With angular momentum EXACTLY zero, muscle-driven
> internal motion still reorients the torso: **1.0635°** per cycle, unchanged to 5 significant
> figures across an 8× change in timestep.

That is **the EVA reorientation mechanic, already proven.** A player adrift with no thruster can
turn around by moving their limbs — slowly, at a real rate, conserving angular momentum. No
authored ability, no cooldown, no "stabiliser" stat. It is a consequence, and it is the kind of
thing you only get if the physics is real.

---

## 6. WHAT TO DO NEXT, in order

1. **Build the real body** (§3.3) — ~14 links, and freeze it. Half a day.
2. **Freeze the observation and action spaces** (§3.1, §3.2), gravity strength included. Hours.
3. **WITNESS OUR PHYSICS AGAINST MUJOCO** on that exact body (§3.4). A day, and it is the one that
   prevents the expensive backtrack. Do not skip it because training looks more exciting.
4. **Train batch 1, POSTURE**, gravity-conditioned, scored from N randomised starts keeping the
   **worst** (`robustness` = worst/mean; a real controller is ~1.0, a lucky one is ~0).
5. Only then, batch 2.

**The rule that survives all of it:** one rollout is a coin toss. It cost this project a celebrated
walker that turned out to be noise, and it will cost a celebrated get-up the same way if the
scoring is not honest.
