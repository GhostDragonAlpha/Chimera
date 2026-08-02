# THE BODY — first-person movement with real physics

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

> **⚠ STATUS BANNER (2026-07-28) — read before the body of this doc.** The *design intent* below (Call-of-Duty states with real physics; don't-go-backwards; contact-first; the three budgets) is all CURRENT and load-bearing. But the **muscle implementation** described from §7 on — the hand-built moment-arm paths in `body.py`, "the muscle paths are a download, not a derivation" — has been **SUPERSEDED**. That hand-built body had one flexor+extensor per joint and, proven by a passive test, **cannot stand** (it lacks biarticular muscles, per-joint redundancy, and the postural chain). The project now uses **MyoSuite's validated musculoskeletal models** (`vendor/myo_sim/`): **myoLegs (80 muscles)** and the full **myobody (290 muscles, legs+torso+arms+spine)**, which batch on `mujoco_warp`. What is now PROVEN on the real body: **it stands** (full body, 77% survival, arms settled by rewarding "be still" not a pose target). What is IN PROGRESS: **walking** — a real gait, not travel, measured by periodicity (the `gait_myobody.py` witness convicted the first attempt at periodicity 0.24). The METHOD also changed: **derive the mathematics first** (`docs/THE_MATHEMATICS_OF_WALKING.md`), and drive the 290 muscles through **~16 measured synergies** (`synergy.py`), not raw per-muscle. See CLAUDE.md "How work gets done" and `docs/THE_MATHEMATICS_OF_WALKING.md` for the current state. Everything below is kept for its design reasoning, not its muscle mechanics.
>
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

## 4. CONTACT-FIRST — one planner, one controller, three costs

> **The operator, 2026-07-26:** *"Everything is like a mountain climber even when walking on two
> feet... all we'd have to do is calculate getting up and then calculate what is the FIRST STEP,
> because that's all we ever need — we repeat it... It happens instantaneously. There's no training
> on the spot."*

This section replaced an earlier plan that had four sequential training runs. It is **smaller** than
what it replaced, which is the sign it is right.

### 4.1 The reframe
Split movement in two, the way Atlas and ANYmal do rather than the way research papers do:

- a **PLANNER** decides *where the next contact goes*
- a **CONTROLLER** moves one limb there without falling

Then walking, climbing and getting up stop being three skills. They are **one loop with three cost
functions:**

| | contacts | the cost rewards |
|---|---|---|
| walking | feet | progress toward the goal per unit energy |
| getting up | elbows, hands, knees, feet | COM height gained per unit energy |
| climbing | hands + feet, keep 3 | ascent, subject to 3-contact stability |
| EVA | handholds | the same loop with nothing to stand on |

Same enumerate-score-pick. Same "move a limb from A to B while the others hold you up." Swap the
objective, get a different behaviour.

### 4.2 ONE STEP AT A TIME — receding horizon
Plan one contact, execute it, **throw the plan away**, re-plan. Repetition produces the traverse.
Never plan the route; plan the step. This is why it is cheap:

```
2 limbs x ~48 placements (8 directions x 6 distances)          =    96 candidates
per candidate: friction cone, reachability, support polygon,
               terrain slope, torque feasibility               ~    50 flops
small value net (64x64) per candidate                          ~ 8,000 flops
                                                        total  ~   0.8 MFLOP
```

Microseconds. A 1 ms budget is 100x more than it needs. **Nothing is trained at runtime and nothing
is deeply searched at runtime** — it is enumerate, score, pick.

### 4.3 THE ONE REAL GAP: greedy walks into dead ends
Pure greedy takes the locally best foothold and arrives somewhere with no feasible next step — it
finds out one step too late, and falls.

Getting up shows it worst. From flat on your back, "raise my COM" refuses to **roll onto your side
first**, because rolling *lowers* the COM. But rolling is how you get up. Greedy cannot see past
the dip.

**The fix is a learned VALUE FUNCTION, not a deeper search.** Score each candidate by *how good is
the situation this leaves me in*, not *how much progress does this make*. The value net IS the
lookahead, compressed into something evaluated in microseconds — the AlphaZero pattern, and the
project's own thesis: compress the expensive search into weights and evaluate instead.

### 4.4 WHAT REPLACES THE 45-DEGREE RULE
Games hard-code "slopes over 45 degrees are unclimbable." The real answer is six measurable limits,
and every one is already in this engine:

| real limit | the law | where it lives |
|---|---|---|
| you slip | `tan(theta) > mu` — the friction cone | `Coupling` / `ContactModel.mu` |
| the ground gives way | angle of repose | measured: **40.03 deg** for regolith (`granular.py`) |
| you cannot reach | limb length vs foothold distance | morphology |
| you fall over | COM projection outside the support polygon | geometry, per contact set |
| not strong enough | required joint moment > what the muscles make | the muscle model |
| not worth it | cost of transport | energy, measured |

**And `tan(45 deg) = 1.0`.** The industry's magic constant is exactly the friction angle for
`mu = 1.0` — a coefficient nobody wrote down and everybody assumed, then applied to ice and gravel
alike. With real numbers: rubber on rock `mu ~ 0.9` -> **42 deg**; boots on dry regolith
`mu ~ 0.6` -> **31 deg**; ice `mu ~ 0.1` -> **5.7 deg**.

Regolith's own angle of repose is 40.03 deg, so the steepest natural dust slope is ~40 deg and you
slip at ~31. **A fresh crater wall is unwalkable** — which is what Apollo crews reported, and
nobody has to author it.

### 4.5 GAIT IS NOT AUTHORED EITHER
Cost of transport (energy per unit distance per unit weight, dimensionless, ~0.2 for human walking)
is the objective. Preferred step length and preferred speed fall out of minimising it rather than
being tuned.

And the **Froude number** `Fr = v^2 / (g L)` decides which gait wins; humans switch walk->run at
`Fr ~ 0.5`:

```
Earth, 0.9 m leg:  v = sqrt(0.5 x 9.81 x 0.9) = 2.10 m/s
Moon:              v = sqrt(0.5 x 1.62 x 0.9) = 0.85 m/s   <- barely a stroll
```

In 1/6 g, walking stops being efficient at walking pace, so the optimum becomes a hop. **That is the
Apollo bunny-hop, predicted from one dimensionless group.** A gravity-conditioned planner
rediscovers it, because on the Moon the hop wins on cost of transport. No gait authored, nobody
told it about the Moon.

### 4.6 The seam that can lie
The planner can propose a foothold the controller cannot actually reach. Robotics solves this by
giving the planner a **learned reachability model** — the controller tells the planner what it can
do. Design that feedback in from the start; bolting it on later means re-training the planner.

Runtime failure handling is then free, and it is the behaviour the operator asked for: try a
foothold, fail to reach it, **mark it infeasible for a few seconds**, pick the next candidate. The
player watches the character struggle at a slope, fail twice, and route around. Nothing is scripted
-- it is the search visibly working.

### 4.7 What still has to be trained
Only two things, and both are small compared to "learn to walk":

1. **The transition controller** — move one limb from A to B while the others hold you up. Reused by
   every behaviour above. This is where the balance problem lives and where the GPU hours go.
2. **The value function** — how good is the situation this contact leaves me in. Trains alongside.

Everything else is enumeration and measured physics.
### 4.8 THE PLANNER'S BUDGET IS A CHARACTER STAT

> **The operator, 2026-07-26:** *"Maybe how many steps your character plans ahead is a feature of
> the character itself that can be upgraded. It could be part of a movement intelligence."*

Yes -- and it is the correct place to put a stat, for a reason worth stating as a rule.

**Price it first.** Beam search keeping the best 8 at each level:

```
depth 1     96 node evals    0.8 MFLOP     "greedy"
depth 2   ~864               7   MFLOP
depth 3  ~1632              13   MFLOP
depth 4  ~2400              19   MFLOP     "plans ahead"
```

1.15 GFLOP/s at 60 Hz for the top end. **The whole range from clumsy to expert is free**, so this is
a pure design dial and not a performance tradeoff.

**Express it as a NODE BUDGET, not a depth.** Chess engines do not sell skill as "depth 4", they use
iterative deepening against a budget -- and that is better here because **depth then emerges from how
hard the terrain is.** On flat ground few footholds are plausible, so a small budget still reaches
depth 6. On a boulder field the branching explodes and a large budget only reaches depth 2.

The consequence is the good part: **the stat only matters where the ground is hard.** Walking a
corridor, a low-budget character is indistinguishable from a high one. On scree the difference is
immediate -- one picks a line, the other commits to a rock that dead-ends and has to back off.
Self-scaling difficulty out of one integer.

#### THE RULE THAT KEEPS STATS FROM CORRUPTING THE SIMULATION

> **A stat may change the BODY or the DECISION. It may NEVER change the PHYSICS.**

    WRONG   "movement intelligence +10 -> you slip 10% less"   (a lie about friction)
    RIGHT   "movement intelligence = node budget"              (friction identical; you choose better)

A clumsy character and an expert on the same rock face meet the same mu, the same reach, the same
torque limits. The expert is not luckier. They pick better footholds. A stat defined this way cannot
corrupt the simulation because it never touches it.

Every stat this game needs fits under that rule:

| stat | what it actually is | body or controller |
|---|---|---|
| strength | joint torque limits | body |
| flexibility | joint range limits | body |
| stamina | energy budget before cost of transport bites | body |
| movement intelligence | planner node budget | controller |
| body awareness | proprioception noise | controller |
| reflexes | replan rate | controller |

#### AND INJURY COMES FREE

A hurt left leg is: reduced torque limit + reduced joint range + noisier proprioception, on that limb
only. The planner's torque-feasibility check then rejects footholds asking too much of it, so it
takes shorter steps on that side and shifts weight to the right.

**That is a limp, and nobody authored it.** No limp animation, no injury state, no modifier -- three
numbers moving on one limb and a planner that respects its own constraints.

The same mechanism gives a heavy pack (mass and balance change), a stiff pressurised suit (joint
ranges shrink -- exactly what an EVA suit does, and why Apollo crews moved the way they did), and
fatigue (the energy budget tightens, so it starts choosing cheaper lines).

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

1. **Build the real body** (§3.3) — ~14 links, muscle-actuated (§3.2), and freeze it. Half a day.
2. **Freeze the observation and action spaces** (§3.1), gravity strength included. Hours.
3. **WITNESS OUR PHYSICS AGAINST MUJOCO** on that exact body (§3.4). A day, and it is the one that
   prevents the expensive backtrack. Do not skip it because training looks more exciting.
4. **Build the PLANNER first — it needs no training** (§4.2, §4.4). Enumerate candidate contacts,
   score them against the six measured limits, pick. It is testable on day one against a static
   body: *given this pose and this terrain, where can a foot go?* Render the candidates and look at
   them. This is the cheapest large piece of the system and it is pure geometry plus physics that
   already exists.
5. **Train the TRANSITION CONTROLLER** (§4.7) — one limb, A to B, others holding. Gravity-
   conditioned. Scored from N randomised starts keeping the **worst** (`robustness` = worst/mean;
   a real controller is ~1.0, a lucky one is ~0).
6. **Train the VALUE FUNCTION** alongside it (§4.3), which is what stops the greedy planner walking
   into dead ends.
7. Swap cost functions for get-up / walk / climb / EVA (§4.1). No new system.

Step 4 before step 5 is deliberate: the planner is free, visible, and debuggable, and building it
first tells you what the controller actually has to be able to do — which is the reachability model
of §4.6 arriving by construction rather than by retrofit.

**The rule that survives all of it:** one rollout is a coin toss. It cost this project a celebrated
walker that turned out to be noise, and it will cost a celebrated get-up the same way if the
scoring is not honest.

---

## 7. THE MUSCLE PATHS ARE A DOWNLOAD, NOT A DERIVATION (2026-07-26)

> **The operator:** *"the muscle transmission is decided by nature so we have to find actual
> biological data that's been recorded."*

Right, and two things were settled by acting on it.

### 7.1 I was WRONG that MuJoCo has no primitive for this
MuJoCo has `<tendon><spatial>` that **wraps around geoms** — which is a pulley — and
`<actuator><muscle>` with force-length and force-velocity built in. It derives the moment arm
**from the path**. Measured on a toy elbow with a 30 mm wrapping cylinder:

```
angle    tendon len    moment arm MuJoCo computes
   0     0.31085 m     30.00 mm    <- CONSTANT while the tendon hugs the pulley
  30     0.32161 m     30.00 mm       (r = the pulley radius, exactly)
  60     0.30591 m     30.00 mm
  90     0.28460 m     50.60 mm    <- lifts off; bowstringing begins
 120     0.25452 m     62.36 mm
```

So the pulley is not an approximation of the mechanism, it **is** the mechanism, and MuJoCo already
models it. What MuJoCo lacks is only a way to TYPE IN `r(q) = r0 + r1 cos(q - q_peak)` as a formula
— which it does not need, because the geometry generates the curve. **The actuation seam is not a
blocker.**

### 7.2 The download: MyoSuite `myo_sim`, Apache-2.0
`external/myo_sim` (gitignored). `leg/myolegs.xml` alone carries **80 muscles, 324 wrap objects,
382 sites** — cadaver dissection, MRI and ultrasound already encoded as geometry.

Checked against the papers this project pulled separately, which is a `dyadAnalysis`: two
independent routes to the same measured truth.

| | MyoSuite | published | verdict |
|---|---|---|---|
| glute max at hip 0° → 90° | 62.2 → 23.5 mm | 79 mm at 0°, decreasing | **shape agrees**, magnitude within a compartment-averaging difference |
| plantarflexors, dorsi → plantar | 38.6 → 44.0 mm | 34.6 → 36.9 mm peak | **agrees** |
| knee extensors | 3.2 mm | ~46 mm | **my measurement is invalid** — see below |

### 7.3 The knee number is MY bug, and it is worth keeping
The OpenSim knee is a **coupled** joint: `knee_angle_r` drives `knee_angle_r_translation1/2` and
`knee_angle_r_rotation2/3` through equality constraints (this model has 14). Writing `qpos` and
calling `mj_forward` does **not** enforce them, so the patellofemoral mechanism never moves and the
quadriceps path barely changes — hence 3.2 mm instead of 46.

That is the whole reason the knee's moment arm is large and flat in the first place: **the patella
is a pulley that holds the quadriceps tendon away from the joint centre.** Miss the coupling and
you delete the patella. Reading it correctly needs the constraint solver run, not a forward pass.

Two earlier lookups in this session failed the same way and silently: `mj_name2id` returns **-1**
for a name that does not exist, and `ten_length[-1]` is a valid index — so a wrong name reads the
LAST tendon instead of raising. Assert `>= 0` on every id.

### 7.4 What this changes
Muscle geometry stops being authored and becomes **transferred**: place tendon sites and wrapping
surfaces so the resulting `r(q)` reproduces the published curve, on our joints. The 6 joints still
marked ASSUMED in `body.MOMENT_ARM` have a source now.

### 7.5 The knee: THREE hypotheses tested, all wrong, and what is now actually known

The knee reads a 1008 mm moment arm — a metre-long lever. Each attempt narrowed it:

1. **"The couplings are not applied."** Wrong. Evaluating the seven `mjEQ_JOINT` polynomials and
   writing `qpos` does move the coupled DOFs, and they move **smoothly**:
   `translation1` 0.0000 → −0.0155, `rotation2` 0.0000 → −0.0769 → −0.0035 across 0 → −100°.
2. **"The polynomial is relative to the reference pose."** It is (`qpos1 − qpos1_0 = poly(qpos2 −
   qpos2_0)`), and fixing that changed **nothing**, because `qpos0` is zero for these joints.
3. **"The finite difference straddles a discontinuity."** Wrong — see (1); the coupled DOFs are
   continuous, so ±h does not jump.

**What the length curve actually shows.** `vaslat_r` over 0 → −100° of knee flexion:

```
   0 deg  0.29563      Quadriceps LENGTHENING with flexion is correct in sign.
 -20 deg  0.28435      But it SHORTENS to -20 and then reverses -- so r crosses
 -30 deg  0.28415      ZERO near -25 deg, which is why the arm read 3.2 mm at 0.
 -60 deg  0.34652      And 0.284 -> 0.524 over the back half is dL/dq ~ 170 mm,
-100 deg  0.52356      four times any real quadriceps lever.
```

A moment arm that crosses zero mid-range and then reaches 170 mm is not a knee. The suspect that
survives is the **PATELLA**: three of the seven couplings are `knee_angle_r_beta_*`, which drive the
patellar body the quadriceps tendon routes over, and one of them (`beta_rotation1`) has a strongly
quadratic coefficient set `[0.0105, 0.0248, −1.3165, 0.7163, −0.1383]`. If the patella is mis-posed,
the tendon wraps the wrong side of it and the lever inverts — which is exactly the signature above.

**This is not a MyoSuite bug to route around; it is the mechanism we came for.** The patella IS the
pulley that holds the quadriceps tendon off the joint centre, and it is the whole reason the knee's
arm is large and flat. Getting it right is the point, not a detail.

**Next attempt should stop hand-posing and let MuJoCo solve it** — drive `knee_angle_r` with a
weld/equality-respecting solve (`mj_step` to settle, or `mj_inverse` with the constraint solver
active) rather than writing `qpos` and calling `mj_forward`. Until then the knee curve in
`body.MOMENT_ARM` stays on the published papers, which give 53.4/38.6 mm and pass B9.

---

## 8. EXTRACTING FROM THE RETIRED `Chimera/` TREE — the manifest (2026-07-27)

The tree is **2,378 tracked files** and cannot simply be deleted: `ChimeraEngine` reaches into it.
`core/membranes.py` exists ONLY there (measured — `core/membranes.py` at the root does not exist,
and the import resolves to `Chimera/core/membranes.py`), and `physics.py:31` /
`physics_articulated.py:35` add `Chimera/` to `sys.path` to find it.

**Everything ChimeraEngine imports from it:**

```
core.capcom        core.eden        core.membranes        core.saturation        core.scene
```

plus two file reads: `gen_decl.py:14` and `human_messenger.py:31` want `Chimera/docs/THE_STORY.md`.

**Why this is not a small job.** Those five are only the FIRST level. Each carries its own
transitive dependencies inside `Chimera/core/`, and `capcom` in particular sits on `world_store`
(the SQLite substrate holding the DNA graph, rep ledger and CAPCOM stores). The closure has to be
walked before anything moves, or the deletion takes the physics stack down with it.

**The safe order**, and the ordering matters more than the speed:

1. Walk the transitive closure of those five modules — list every file actually reached.
2. Move that closure into `ChimeraEngine/`, keeping the `core.` package name so imports are
   unchanged, and drop the two `sys.path` insertions.
3. Re-run ALL SIX witness suites green: body, planner, mjcf, nervous, contact, gravity.
4. **Only then** delete. Everything is in git history, so the deletion itself is recoverable —
   what is not recoverable cheaply is a half-moved tree with broken imports.

**The urgency is already gone.** The churn this was meant to stop came from the Stop hook's
`git add -A`, now scoped, and the retired tree can sit there indefinitely doing no harm.

### 8.1 The closure, WALKED (2026-07-27)

49 modules total — but they are not one lump. Measured per entry point:

```
core.membranes    ->  16 modules
core.saturation   ->   1
core.eden         ->   4
core.capcom       ->  26     <- the expensive tail: world_store, task_board,
                                preflight, the gates, the rep engine
```

**And the consumers split along the same line:**

| needs | modules pulled | who imports it |
|---|---|---|
| `membranes`, `saturation` | **~16** | `physics.py`, `physics_articulated.py`, `engine_state.py`, `fields_witness.py`, `gravity_witness.py` |
| `capcom`, `eden`, `scene` | **26+** | `appearance.py`, `human_messenger.py`, `sound_messenger.py` |

That is the whole job, and it is two jobs rather than one:

**THE PHYSICS EXTRACTION IS ~16 MODULES AND UNBLOCKS THE DELETION.** Everything built in the
body/planner/fields work depends only on `membranes` + `saturation`. Move that closure and the
simulation stops needing `Chimera/` at all.

**THE TOOLING EXTRACTION IS THE EXPENSIVE ONE**, and it is optional. `capcom` drags in the whole
studio-automation substrate — the SQLite world store, the task board, the gates. Those three
consumers are messengers and appearance plumbing, not physics. They can keep the `sys.path` shim,
be stubbed, or be retired with the tree.

So the order that gets the tree deleted soonest: extract the **16**, re-run the six witnesses,
decide separately whether the three tooling consumers are worth carrying or worth dropping.

---

## 9. THE TRANSITION CONTROLLER — the spec (2026-07-27)

Everything else is built. This is the one thing that must be TRAINED, and §4.7 established why:
the planner decides *where* the next contact goes; this moves a limb *there* without falling. One
policy, reused by walking, climbing, getting up and EVA.

### 9.1 The task, stated so it can be scored
**Given** a stance and a target contact point for one limb, **reach it and hold** — while the other
contacts keep the body up.

```
episode      start from a stance, planner picks a target, run 1.5 s of sim
success      the swing limb is within 3 cm of the target AND all other contacts held
              AND base tilt from LOCAL up stayed under 25 deg throughout
terminate    early on: tilt > 60 deg (fallen), or any non-swing contact broken
```

Nothing in that mentions gait, style, or what a step should look like. Those are consequences.

### 9.2 What it sees and does — ALREADY FROZEN
`body.OBSERVATION` (96) and `body.ACTION` (36), unchanged since §3.1. The observation includes
**gravity strength**, which is what makes one policy work from an asteroid to a super-Earth, and
the action is muscle activations in [0,1] — so **co-contraction is a legal move** and bracing on
landing is something the policy can discover rather than something authored.

### 9.3 The reward, in physics not taste
```
+  progress of the swing limb toward the target      (the task)
+  survival, per tick upright                        (do not fall)
-  cost of transport, integral of muscle work        (the SAME quantity that gives the planner
                                                      its step length and the Apollo bunny-hop)
-  contact slip at the supporting limbs              (measurable: tangential velocity at a
                                                      contact that should be static)
```
No term for "looks natural." If it looks wrong, the missing term is a physical one.

### 9.4 The randomisation ranges ARE A CONTRACT (§3.5)
A policy interpolates inside its training distribution and degrades outside it, so the range must
CONTAIN everything the game will ever do:

```
gravity        0.001 .. 12 m/s^2      asteroid to super-Earth. CONDITIONED, not just randomised.
start pose     the whole fallen space  supine, prone, on one side, crouched, mid-stride
ground mu      0.10 .. 0.95            ice to dry rock -- and it is NOT in the observation, so the
                                       policy must infer it from slipping. That is stepping onto
                                       ice and finding out.
slope          0 .. 35 deg
carried mass   0 .. 40 kg
perturbation   0 .. 400 N impulses     the shove that F6/P3 already measured toppling at
```

### 9.5 SCORING — the rule that has already cost this project once
**Score every genome from N randomised starts and keep the WORST.** Report
`robustness = worst / mean`; a real controller is ~1.0, a lucky one is ~0.

This is not a preference. A celebrated 13.52-body-length walker in this repo had
`periodicity 0.25` and lost 5.5 body lengths to a **one-micron** nudge — 80,000 evaluations spent
selecting lucky dice. One rollout is a coin toss.

### 9.6 Where it runs
`mjcf_body.FastBody` steps this body in **3.3 us** against the numpy engine's 51 ms, and
`mjcf_witness` proved the two agree to **1e-13 m** — so training in MuJoCo and running in this
engine are the same world. For the population, `mujoco-warp` measured **2,358 evals/sec** on this
box, whole population in ONE kernel. THE ONE RULE from `CLAUDE.md`: **nothing reads back from the
GPU inside the rollout loop** — a previous attempt did 1,575 syncs per batch and ran 300x SLOWER
than the CPU.

### 9.7 The known gap to close first
MuJoCo has `<tendon><spatial>` wrapping and `<actuator><muscle>` (§7.1), but our transmission is
currently a sampled `r(q)` table on our side only. Before training: express the same curves as
MuJoCo tendon geometry, and witness that the actuated bodies agree the way the passive ones already
do. Training against a different actuator than the game runs would reproduce, at the muscle layer,
exactly the sim-to-sim mistake §3.4 exists to prevent.
