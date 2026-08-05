# THE COMPILER — the operating model

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
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **THE OPERATOR, 2026-08-02:** *"You have written the specification. Now you need to write the
> compiler."*

A body is not a pile of muscles and a reward function. It is a **machine with an instruction set**,
and everything a player does is a **program** written in that instruction set. Saying it that way is
not a metaphor — it changes what counts as done, because a compiler is correct or it is not, one
instruction at a time, and each layer can be tested against the layer below.

```
   PORTS         the instruction set        one law each, tested ALONE against a known answer
      ▼
   PRIMITIVES    compositions of ports      what two ports do that neither does alone
      ▼
   PROGRAMS      actions                    STEP, PLANT, REACH, GRIP, BRACE, STAND, WALK
      ▼
   PARSER        intent -> program          ~12 buttons over an input-agnostic formula layer
      ▼
   RUNTIME       executes the program       dx/dt = f(x, u, p, w)
      ▼
   CALIBRATION   trains the FREE numbers    p splits DERIVED / INGESTED / TRAINED — never chosen
```

**The parser is built LAST.** It is the only layer that cannot be wrong in an interesting way: a
mis-parse produces the wrong program and you see it immediately. A wrong port produces a *plausible
number* and survives for months.

---

## THE ONE EQUATION

    dx / dt  =  f(x, u, p, w)

| symbol | what it is | where it comes from |
|---|---|---|
| `x` | state — positions, velocities, activations | the runtime |
| `u` | command — what the program asks for | the parser |
| `p` | parameters — stiffness, damping, limits, gains | **DERIVED · INGESTED · TRAINED** |
| `w` | the world — gravity, ground, wind, medium | the parent membrane (`tools/world.py`) |
| `f` | the law | **PROGRAMMED.** Never trained, never swept. |

**`f` is programmed and `p` is not chosen.** That is Rule 1 restated in the compiler's own terms:
the FORM of a law is authored, and the free numbers inside it are derived from a parent, ingested
from a measurement, or trained against a physics-checkable target. A number you picked is a fourth
category that does not exist here.

---

## LAYER 1 · PORTS — the instruction set

A port is **one instruction**: a mass falls, a muscle makes force, a spindle reports length, a
ligament resists, a sensor discriminates contact. It is tested **alone**, against an answer known
independently of the simulator.

> **A port that has not been tested alone cannot be ruled out when a composition built on it fails.**

### The three enforcements (`tools/port_registry.py`)

| enforcement | the failure that earned it |
|---|---|
| **no falsifier, no registration** | Rule 0, applied where it is cheapest. |
| **the COUNT is asserted** (`expect(12)`) | 8 of 12 tests registered into a second copy of the module and the harness printed **`4/4 ports validated`** — a confident success with two-thirds of the instruction set missing. |
| **duplicate names refused** | two instructions cannot share a name; a silent overwrite hides one. |

### THE TWELVE — validated 2026-08-02, `tools/port_tests.py` + `port_tests_more.py`

| # | port | what it claims | measured |
|---|---|---|---|
| 1 | RIGID_BODY | a mass in this world's gravity falls by `½gt²` | **0.00000%** against the DISCRETE integrator |
| 2 | CONTACT | the ground returns a normal force equal to weight | 29.6404 N predicted / 29.6404 measured, \|vz\| 1.9e-15 |
| 3 | HILL_MUSCLE | force is proportional to activation, with first-order dynamics | ratio 1.984 vs 2.000; t63 **15.0 ms** vs `tau_act` 15.0 |
| 4 | SPINDLE | length and RATE, and the rate integrates back to the length | drift **0.0000%** |
| 5 | JOINT_LIMIT | the published range is enforced, not advisory | overshoot **0.860°** under 400 N·m |
| 6 | PASSIVE_FORCE | tissue resists, and the resistance GROWS toward the stop | 1.84 / 1.92 / **225.89 N·m** at 10/50/90% of range |
| 7 | TENDON_ELASTICITY | a stretched, unactivated unit still makes force | 0.221 N at **zero** activation over 100.6 mm |
| 8 | FORCE_VELOCITY | a shortening muscle makes less force than an isometric one | `f_v` = **0.8324** |
| 9 | GTO | the tendon organ's signal is monotone in force | 2.2 / 147 / 293 / 438 / 584 N |
| 10 | OTOLITH | gravity IN HEAD COORDINATES: `g·sin` and `g·cos` | both **0.0000%** off |
| 11 | PLANTAR_PRESSURE | the foot sensors discriminate loaded from airborne | 71.65 N loaded / **0.000000** lifted |
| 12 | PHASE_OSCILLATOR | coupled oscillators converge; uncoupled ones do not | 2.6e-12 rad coupled vs **π** uncoupled |

**12 / 12.** Ports 5 and 6 were the two that failed on the first full run, and they were **one
finding, not two**: the body had no ligaments, so the hard constraint carried the entire end-range
load. Passive tissue was added the same day (below), and both closed.

### The port lessons, each paid for

- **PREDICT WHAT IS ACTUALLY RUN.** Port 1's 0.2% error was exactly the semi-implicit Euler term
  `g·dt²·n(n+1)/2`. The port was right; the falsifier was mis-specified. Fixed by predicting the
  **discrete sum** and printing the continuous value beside it — *never* by widening the tolerance.
- **A WRONG INDEX THAT RAISES COSTS AN HOUR; ONE THAT RETURNS 0.0 COSTS A DIAGNOSIS.**
  `actuator_moment` is SPARSE (`moment_rownnz` / `moment_rowadr` / `moment_colind`). A dense reshape
  raised loudly in one place and returned a silent zero in another.
- **READ THE RIGHT ARRAY.** `qfrc_passive` carries joint and TENDON springs; MuJoCo files a
  MUSCLE's passive force under `qfrc_actuator`. Port 6 asked a true question of the wrong array —
  right conclusion, unreachable by that measurement.
- **`ctrl` IS EXCITATION; FORCE READS `act`.** A test that zeroes `ctrl` and calls the muscle
  silent is measuring whatever activation the keyframe stored.
- **MEASURE THE EFFECT, NOT THE INTERMEDIATE.** `qfrc_actuator[dof]` is the generalized force
  *before constraints*. Read that way, the knee had twelve muscles pulling one way and one the
  other, with the **entire quadriceps group in neither list** — because this knee is an OpenSim
  patellar mechanism whose extensor effect arrives through coupled dofs. `qacc` is downstream of
  the solver. Anything selecting "the muscles at the knee" by `qfrc_actuator` has been selecting
  flexors.

---

## LAYER 2 · PRIMITIVES — compositions of ports

A primitive is **what two or more ports do together that none does alone**. Two guards beyond the
port layer's:

1. **It must NAME the ports it composes**, and every named one must already be registered. You
   cannot declare a composition over an instruction that does not exist. *(This fired on the first
   run: `port_tests` registers 1–4 and imports 5–12 only inside `main()`, so eight instructions
   were unloaded and `end_stop` was refused at import.)*
2. **It must ABLATE.** The test runs twice — once composed, once with one port's contribution
   removed — and **passes only if the second one fails**.

> **THE CONTROL IS NOT AN EXTRA. IT IS THE MEASUREMENT.**

**MATCHED DRIVE.** Where the ablation is "open the loop", the open-loop control gets the closed
loop's **own mean activation** — not zero, not a round number — or the comparison changes both the
feedback *and* the amount of drive. **The exception is a loop whose whole mechanism IS lowering the
drive** (LOAD_RELIEF): there, matching the mean deletes the effect under test, and the control must
remove the *signal* instead. Which control is right is a claim about the mechanism, and has to be
stated.

### Status — `tools/primitive_tests.py`, 4 of 7

| primitive | ports | measured | |
|---|---|---|---|
| **END_STOP** | joint_limit + passive_force + tendon_elasticity | 0.860° overshoot vs **3.574°** with ligaments removed; tissue carries 306.9 N·m | PASS |
| **DAMPING** | hill_muscle + force_velocity | **−28.54 J** absorbed per cycle at 6 rad/s; 1.1% left at 1/100 speed | PASS |
| **LOAD_RELIEF** | hill_muscle + gto | sustained 2440 N vs **4896 N** with the force signal ignored — 50.2% relieved | PASS |
| **RHYTHM_DRIVE** | phase_oscillator + hill_muscle | L/R correlation **−0.689**, swing 81.5° vs 6.2° on a constant of the same mean | PASS |
| **STIFFNESS** | hill_muscle + spindle | closed 39.6° vs open 37.7° — the leg swings under the probe | FAIL |
| **WEIGHT_TRANSFER** | rigid_body + contact + plantar_pressure | left share moves +0.7 points; feet carry **177 N of 580** | FAIL |
| **UPRIGHT** | hill_muscle + otolith | 104.2° lean closed vs 102.7° open | FAIL |

**All twelve ports are composed by at least one primitive** (`port_coverage()` reports any that are
not — an instruction nothing rests on is either unnecessary or a layer that was never built).

**THE THREE FAILURES SHARE ONE CAUSE and are recorded as UNMEASURED, not rescoped:** each probes a
joint while the body collapses around it. The pelvis harness does not hold the thigh, so a knee
probe measures a leg swinging; does not hold the trunk, so a lumbar probe measures a spine folding
at four joints in series; and cannot be used at all where feet must carry load, because **a rigid
root pin carries the weight the feet were supposed to share**. They need a stronger isolation, not
different physics. **Compositions do not proceed on them.**

### The primitive lessons

- **SATURATION IS AN OUT-OF-RANGE READING, NOT A NULL RESULT.** Three primitives failed at mean
  drive 0.987, 0.972 and 1.000. A loop pinned at its ceiling cannot respond to feedback, so closed
  and open were **the same experiment**, and it reported a confident `1.0x`. `unsaturated()` now
  backs the probe off until the loop is in range, or says SATURATED.
- **THE FIX THAT DELETES ITS OWN MEASUREMENT** appeared four times in one file: a harness that
  carried the load being measured; seating by `geom_rbound` (a bounding *sphere*, which lifted the
  feet clear of the floor); a suffix test on sensors named `l_foot` / `r_foot` (all four scored
  right); and translating the root sideways, which moves the feet with it and changed nothing to
  the decimal. **Translating is not leaning.**
- **A HARNESS THAT SLIPS IS NOT A HARNESS.** Zeroing the root's `qvel` before each step lets
  `mj_step` accelerate it anyway.

---

## LAYER 3 · PROGRAMS — the action primitives

**Twelve, named by the operator 2026-08-02, and tested: `tools/action_tests.py`.**
An action is a **program in the port instruction set**, and `action_test()` enforces the part of
Rule 0 the other registries let slip: **PREDICTION is a required registration argument**, declared
at import, which is necessarily before the test can have run. A prediction written after the
measurement is a description.

| | prediction (closed form, computed before the run) | measured | |
|---|---|---|---|
| **SWING** | `T = 2π√(I/(m g d))` — the leg as a compound pendulum | 1.7093 s vs 1.7929 predicted, **4.7%** | PASS |
| **THROW** | `R = v² sin(2θ)/g` | 5.0089 m vs 5.0102, **0.03%** | PASS |
| **LAND** | `J = m√(2gh)` — impulse, needing no stiffness | 147.08 vs 138.03 N·s, **6.6%** | PASS |
| **TURN** | `ΔL_z = 0` under internal drive | 0.0415 vs **41.82** for the external-torque control | PASS |
| **STANCE** | `Σplantar = (1−s)W` across three harness settings | fitted slope **−583.7 N** vs −W = −580.5 | PASS |
| **PUSH** | `F_slip = μN` | slid at 185.3 N against a 348.3 N bound | PASS |
| **LIFT** | `0 < mgΔh / W_muscle ≤ 1` | 0.0337 — **and flagged WEAK in its own output** | PASS |
| **BALANCE** | `ω₀ = √(g/H)` | 0.4186 vs 2.7623 — pivot pinned at the ROOT, `H` measured from the FOOT | FAIL |
| **PULL** | `F_slip(pull) = F_slip(push)` | 81.4 vs 185.3 N — a **real 56.1% asymmetry** | FAIL |
| **STEP** | one foot takes what the other drops | the left foot carries nothing in double support | FAIL |
| **CROUCH** | `τ_knee = W_above × lever`, two routes | 5100.81 vs 59.64 N·m — see below | FAIL |
| **GRIP** | — | **REFUSED**: 47 joints, not one shoulder, elbow, wrist, thumb or finger | REFUSED |

**A REFUSAL IS NOT A FAILURE OF THE BODY.** It is an absent structure, and the test stays
registered so the gap is *counted* rather than forgotten.

**CROUCH names the sharpest structural finding:** writing `knee_angle_r = 45°` does **not pose the
knee.** It drives seven coupled dofs by equality constraint, and they were left where the keyframe
put them — so the brace is holding the knee against its own coupling. The 5100 N·m is real; it is
simply not a crouch.

### THE BRACE — an instrument, declared, and three attempts of which one is physics

| attempt | what happened |
|---|---|
| restore `qpos` every step | **teleportation.** A stable pose reporting **8344 N** of plantar load against a predicted 290, because the contact solver answers a teleport with whatever force that takes. Stable, repeatable, 28× wrong. |
| `qfrc_applied` + PD | a real force, but **explicit** — NaN at t = 0.006 s. Shrinking gains until it survives is a sweep standing in for a derivation. |
| `jnt_stiffness` + `dof_damping` | the model's own passive spring, integrated **implicitly**, stable exactly where the explicit force is not. **This one.** |

`K` is derived — stiff enough that this body's largest static moment deflects the joint under a
degree — and the brace **reports what it actually held to** rather than assuming it.

### Four vacuous or misattributed passes, which mattered more than the failures

- **PULL passed at 0.0% asymmetry** because push and pull both ran to the same *ramp ceiling*
  without ever sliding, and two identical non-events are identical whether or not friction is
  isotropic. The harness was holding the root's x,y: a pinned body cannot slide however hard it is
  pushed. Released, both slip — and the **real 56.1% asymmetry the vacuous version had hidden**
  appears.
- **STEP passed with the lifted foot already at 0.0 N.** Lifting a foot that carries nothing
  transfers nothing; the test scored an absence as a clean unload.
- **STANCE reported a 20.89° brace slip** that was not slip: 13 joints of this keyframe start
  outside their own published range, and a spring whose set point is past the limit can never
  reach it.
- **SWING returned `nan` over 0 cycles** — a teleported pendulum has no period.

**COMMAND THE PROCESS AND ITS STOP CONDITION, NEVER THE FINAL POSITION.** A hand does not aim its
fingers at coordinates; it *closes until it cannot*, and the object decides where they land. So one
GRIP serves a pin and a bowling ball: the object parameterises the **result**, not the command.
**Positions are OUTPUTS.** Every atom is `apply effort → stop when a sensor says stop`, which is a
state-machine transition — and why a reward must never target a pose.

**STAND IS NOT A PORT. IT IS A STATE** — the operator. You train the ports; you *measure* the state.

## HOW A MOTION IS REPRESENTED — one finding from outside, and what it is worth

**NVIDIA ARDY, SIGGRAPH 2026 — read 2026-08-03 for extractable physics and there is NONE.** The
paper says so in its own words: the model is *"purely kinematic… lacks awareness of physical
dynamics."* Its loss is four L1/L2 terms with no energy, momentum or dynamics prior. Nothing in it
would have saved one port test, and it is **not adopted** — its motion is 630 hours of Earth mocap
with no gravity input, which is the authored-phenotype defect this project already named. Replayed
on this body an Earth walk lands at **Fr 0.2536 against the 0.1513 `theHuman` derives for itself**.

What is worth keeping is one **representational** result, and it is an empirical finding we could
not have got by reasoning:

> **HORIZONTAL IS RELATIVE; VERTICAL IS NOT.** ARDY keeps the root explicit and global for
> constraint work, but when it *decodes* it converts the root to `(psi_dot, p_x_dot, p_z_dot, p_y)`
> — heading rate, planar velocities, and **height kept ABSOLUTE**. Their stated reason is measured,
> not argued: it mitigates foot skating.

**VERIFIED** (quoted from the paper): the representation and the reason. **INFERRED** (ours, and
marked as such): *why* it works. Height is measured against gravity and the ground sits at a fixed
place, so height is an absolute; heading and planar position are frame-arbitrary. Mixing the two
the wrong way round is what makes feet slide.

That is `core/membranes.py`'s law arriving from the other direction — *a boundary supplies its own
frame, and up is its normal.* We had the principle; this is a measured consequence of getting it
wrong, which is the part we did not have. **It bears on `emit()` frames and on any future motion
representation, and it has NOT been tested here.**

**TWO INDEPENDENT CONFIRMATIONS, worth recording because they came from strangers:**

- **Their `L_consist = ||J_hat - FK(theta_hat)||` is `dyadAnalysis`.** They predict joint positions
  and joint rotations separately and force forward kinematics on the rotations to reproduce the
  positions — two independent routes to one number, required to agree. Same shape as
  `stand_port.py`'s closure (+0.0000%) and CROUCH's two-route torque check.
- **Their hybrid representation is our synergy result.** Root explicit *because it must be
  addressable* (you cannot inpaint a latent); body compressed because it need only be right. That
  is 290 muscles → 8 dims for 91% of movement, stated as a rule with its reason.

**STILL UNREAD:** `MotionCorrection/`, a C++ foot-skating post-process under Apache-2.0. Its README
does not name the algorithm and it is the one place in that repo a real solver might live.

## LAYER 4 · PARSER — intent to program

~12 buttons, bound twice (keyboard+mouse PRIMARY, gamepad port) over **one input-agnostic formula
layer**. The compression is the point: "everything a human does" is infinite and a gamepad has
twelve inputs, so every action must resolve onto a button.

**BUILT LAST, and deliberately.** It is the only layer that cannot be wrong in an interesting way.

---

## LAYER 5 · RUNTIME — execution

`dx/dt = f(x, u, p, w)`, stepped. **`w` comes from `tools/world.py` and from nowhere else** — one
module reads this world's gravity from the membrane that owns the body, seats the keyframe inside
its own published limits, and installs the passive tissue. There is **no fallback**: if the ledger
cannot be read it raises, because a default is exactly what produced the original defect (every run
for months simulated Earth because `myobody.xml` declares no `<option gravity>` and eight call sites
each forgot to override it).

---

## LAYER 6 · CALIBRATION — the free numbers

`p` splits three ways and the split is not negotiable:

| | meaning | example |
|---|---|---|
| **DERIVED** | follows from the parent's published numbers | comfortable speed from Froude and measured `g` |
| **INGESTED** | measured in the world, cited | ANSUR II segment proportions |
| **TRAINED** | genuinely free, trained against a physics-checkable target | control gains |

**A CHOSEN NUMBER IS NOT A FOURTH CATEGORY.** `python tools/training_gate.py` refuses targets that
are not Froude-consistent with the world the body stands in.

---

# PASSIVE TISSUE IS UNIVERSAL

> **THE OPERATOR, 2026-08-02:** *"Passive tissue applies to everything in the game world that has
> structure, not just humans."*

Passive tissue is **structural resistance to deformation that requires no active energy input** —
the stiffness, damping and energy storage of any physical object. The question is never *does this
object have passive tissue?* It is **how is its passive structure represented?**

    ligament : human  ::  cellulose : grass  ::  crystal lattice : rock  ::  rebar : wall

Every one is the same port, in a different material, at a different scale. This is why the ladder
is one ladder: **the same equations govern everything, the same tests validate everything, the same
ledger records everything.**

## THE UNIVERSAL PORT FRAMEWORK

| object | passive ports | form |
|---|---|---|
| **Human** | ligament · tendon · cartilage · fascia · skin | `τ = kθ + cω` · `F = kx + cv` |
| **Plant** | cellulose · lignin · cell-wall turgor · root | `F = kx` · `σ = Eε` · `P = k(V−V₀)` |
| **Rock** | crystal lattice · fracture planes · roughness · porosity | `σ = Eε`, fracture at `σ_max` · `μ = f(surface)` |
| **Tree** | wood fibre (orthotropic) · bark · root · branch joint · petiole | `σ = Eε` · `τ = kθ + cω` |
| **Building** | concrete · steel rebar · timber frame · masonry · glass · foundation | `σ_c = E_cε_c` · `σ_s = E_sε_s` |
| **Vehicle** | chassis · suspension · tyre · hull · wing · landing gear | `F = kx + cv` · `F_b = ρVg` · `F_L = ½ρC_LAv²` |
| **Fabric / rope** | fibre · weave · seam · elastic | `F = kx` · `F_break = f(seam)` |
| **Terrain** | soil · rock · sand · mud · ice · water | `σ = kε` · `μ = f(type)` · `F = ηAv` |

## What it means at the surface

Every one of these is a *gameplay* consequence of a *passive* number, not a scripted behaviour:

- **grass bends and springs back** under a foot; **flowers break** — low passive resistance
- **trees sway** in wind, **branches carry a climber**, and a trunk **fails at a threshold**
- **rocks do not bend, they shatter**; smooth ones are slippery and rough ones grip
- **walls deflect then fail**; **hulls float**; **rope holds until it is cut**
- **terrain deforms** — footprints, tyre tracks, craters

## THE METHOD FOR A NON-HUMAN OBJECT — the same seven steps

1. **Identify the object type.**
2. **Define its passive elements** — stiffness, damping, failure thresholds.
3. **Write the port equations** — the FORM is programmed.
4. **Write the tests** — statement · prediction · falsifier, one per port.
5. **Validate the ports** (S-1). Registration refuses a test with no falsifier.
6. **Build the object** by composing validated ports.
7. **Test the object** in the world.

## HONEST STATUS — SEVEN OF THE EIGHT ROWS ARE STILL SPECIFIED ONLY

> **A DESCRIPTION SURVIVES ANY RESULT. A THEORY CAN LOSE.** The table above began as a *design*,
> and saying so was the whole of Rule 0. **As of 2026-08-04 seven of its objects have ONE
> validated port each** (`tools/port_tests_matter.py`, run by the same harness as the human's):
>
> | object | port | what it validated | what it REFUSED |
> |---|---|---|---|
> | **Plant** | `grass_blade` | a lamina is a DISTRIBUTED beam; a lumped root spring is exact under a pure moment and **3× too stiff under a tip force**, and a foot is a tip force | damping `c` — Vincent publishes a dynamic modulus proving the blade is viscoelastic but no loss factor |
| **Plant** (2nd) | `plant_selfbuckling` | Greenhill: a blade stands to L_crit = (7.8373EI/rho g A)^(1/3). Vincent's 1982 modulus and Kew's blade dimensions -- neither computing this -- put the published 12 cm blade **9.2% under** its own Earth buckling limit of 13.21 cm, and the 4-20 cm range brackets it | **turgor**: Vincent measured LIVING leaf, so his E already contains it; separating needs a wilted modulus on the same tissue, unpublished |
> | **Rock** | `rock_fracture` | σ = Eε to σ_t; E/σ_t/K_IC are OVER-DETERMINED and the flaw they imply is **8.72 mm** (vesicle, not grain). UCS/σ_t = 18.3 against Griffith's 8 | the library's 2 mm "grain size" as a Griffith flaw — its own note says it is surface texture |
> | **Tree** | `tree_trunk` | orthotropic wood: G_LR/E_L = 0.086 is **4.47× below isotropic**; the shear share is exact at three slendernesses; trunks always fail in bending | a trunk diameter — no chapter grows a wood, so the claim is stated in L/d |
> | **Terrain** | `terrain_footprint` | a stiffness and a strength from two literatures land on the same millimetre (3.84 vs 3.12 mm) | a footprint DEPTH — unresolvable across cohesion's own ±0.4 kPa, which spans 54 mm to zero |
> | **Fabric/rope** | `fibre_rope` | EA from published strain-at-10%-BS; the same standard's break elongation **refutes F = kx for polyester** (96% of break at its RATED load) | the seam — a splice efficiency is not published in `matter_data` |
> | **Vehicle** | `suspension` | k and c DERIVED from ride frequency and damping ratio, not ingested; overshoot and settling exact to 0.02% | the quoted default (k, c) pair as a comfort car — it implies 1.42 Hz and ζ 0.122 |
> | **Building** | `building_rc` | concrete + rebar share a strain, so 3% of the area carries **18.8%** of the load; and ACI's bare 600 MPa in the balanced-ratio formula turns out to be **E_s x eps_cu**, so the code constant is a derivation somebody hid inside a number | nothing yet -- but every constant is from a design CODE, not a lab, and that is a different kind of claim |
| *(granular)* | `granular_repose` | θ_r = atan(μ) is **BRACKETED, not reached**: spheres 0.0° < 35.0° < boxes 66.2° at identical friction | a repose angle from a rigid-body engine at all |
>
> **21/21 ports and 7/7 primitives. BUILDING HAS ONE** (`building_rc`) -- the last zero
> in this table is closed. Nothing else in its row
> may be cited. One port per object is a beginning, not a passive-tissue model: each row above
> names several ports and exactly one of them has a measured falsifier.
>
> **The terrain port convicted a live membrane.** theGround publishes `sinkage_m = 8.674e-19` —
> 4.4×10¹⁵ times smaller than its own soil's elastic settlement — traced to a typed
> `COHESION_PA = 2000` where the world's library publishes 500 ± 400. **The soil is decorative and
> one typed constant is why.** Unfixed here: it is theGround's membrane, not the port's.

**Two things had to happen before any of them was built, and both did:**

- **THE TOLERANCES WERE CHOSEN AND WERE THEREFORE NOT LAW — and one of them turned out to be
  unmeetable.** "within 5%" and "within 10%" are round numbers with no source, and a tolerance
  chosen to be comfortable is a falsifier chosen to be survivable. Where a constant carries a
  published spread, the spread now sets the bar. **The rock port found the reverse case:** the
  brief asked fracture to land within 20% of the derived load, but basalt's tensile strength is
  published as 14.5 ± 3.3 MPa — **the literature's own spread is 22.8%**, so a model reproducing
  basalt perfectly would fail that bar one time in three. A tolerance can be too *tight* for the
  data as easily as too loose, and both are the same defect: a number with no source.
- **`k`, `c`, `E`, `μ`, `σ_max` ARE FREE NUMBERS AND RULE 1 APPLIES TO ALL OF THEM.** Writing
  `F = kx + cv` programs the FORM, which is legitimate and is exactly "program the rules". It says
  nothing about `k`. Each must be DERIVED from a parent, INGESTED from a citable measurement, or
  TRAINED — and where the data cannot support one, **the honest output is a refusal with a name**,
  not a plausible constant. `tools/matter_data.py` holds the ingested half: 43 constants, each
  with its citation, `cite()` raising rather than defaulting, and the world's own materials library
  read *through* rather than copied. **Four of the seven ports refuse something by name.**

**AND THE FOUR WRONG ARITHMETICS ARRIVED ON SCHEDULE**, exactly as the ligament precedent below
predicted — but they were INSTRUMENT defects, not derivation defects, and every one returned a
plausible number first: MuJoCo applies `xfrc_applied` at a body's centre of mass, so a tip load
acted half a segment short and read as a 3.10% "discretisation"; one fixed timestep served grass
and basalt, and a basalt rod returned **0.000 µm of stretch with |qvel| exactly 0** — a perfectly
rigid rock, reported without complaint; a convergence test watched *z* while an axial pull moved
in *x*; and `abs(qvel).max()` on a freejoint compared **rad/s against a m/s bound**, refusing a run
that was in fact correct. **Expect these to be the shape of the next four, too.**

**THE WORKED PRECEDENT** is the human ligament, `tools/world.py::derive_ligaments`:

    WHERE IT GOES TAUT   theHuman's published gait envelope -- a ligament is slack through the
                         motion the body performs; that is what range of motion MEANS
    HOW STRONG           the peak torque the muscles crossing that joint can produce, because a
                         ligament they could overpower would let every maximal contraction
                         dislocate the joint.  k = tau_max / gap
    WHERE IT REFUSES     as gap -> 0, k -> infinity, and that is a CONSTRAINT, not a ligament.
                         10 derived, 2 refused by name. L and R agree to 0.6% -- a check, not a hope.

Four wrong arithmetics were written on the way there, **every one returning a plausible number**:
absolute-value summing counted the antagonists as helping (6× too stiff); the signed version read
the sign of `moment` alone, but muscle force is negative in MuJoCo so the moment reads backwards;
`F_max` is peak *isometric* force, 2212 N nominal against 719 N actually produced at that angle;
and evaluated *at* the limit it read ≈0 for the knee, because at 120° the hamstrings are fully
shortened — true physiology, wrong number, since the ligament must catch what was launched from
mid-band. **Expect the same four when a tree trunk or a wall is derived.**

---

## Where the files are

| | |
|---|---|
| `tools/port_registry.py` | the shared registry — imported by everything, run by nothing |
| `tools/port_tests.py` · `port_tests_more.py` | the twelve ports |
| `tools/primitive_tests.py` | the primitive layer + its ablations |
| `tools/world.py` | the runtime's `w`: gravity, keyframe seating, passive tissue |
| `tools/tissue_witness.py` | the ligament moment–angle curves, drawn against the walked-through band |
| `docs/CONTROLLER_MAP.md` · `docs/CAPTURE_LIST.md` | layer 3 and layer 4 |

```bash
python tools/port_tests.py && python tools/primitive_tests.py && python tools/tissue_witness.py
```
