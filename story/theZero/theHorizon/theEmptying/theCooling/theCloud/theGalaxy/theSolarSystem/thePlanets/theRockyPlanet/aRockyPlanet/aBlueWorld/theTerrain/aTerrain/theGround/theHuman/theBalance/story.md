# theBalance

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 28** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **3.44867 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** Everything above this walks forwards. Seen from the side a body is never falling
sideways, which is why the side view is comfortable and why it is only half the story. This chapter
is the other half: the sway, the step width, and the fact that a pelvis is a **bar between two hips**
which tilts — so the two hips are not at the same height, and a side view has no way to say so.

*It is not a smaller thing than its parent. It is the same body, seen along the other axis.*

## Sideways is a different problem, and that is measured

Fore-and-aft, the catch is free. The swing leg is going forward anyway, so a forward fall lands on a
foot that was already on its way there. Sideways it is not: the leg has to be **put** there, and if
it is not, nothing stops the fall.

That asymmetry is not a story about the two planes — Bauby & Kuo (2000) measured it. Lateral balance
in walking needs active control; fore-aft balance is passively stable. So the frontal plane is where
the control lives, and it is the plane a sagittal model silently assumes away.

## The chapter had a number waiting for it

theAnkle closed with a residual it could locate but not spend:

> in double support the two legs disagree by **2.02% of stature** about where the pelvis is. About
> 40% of it — **0.81% of stature** — is pelvic list, which is frontal-plane.

A sagittal model puts both hips at one height **by construction**, so when the leading leg and the
trailing leg demand different pelvis heights it can satisfy neither. A pelvis that lists satisfies
both, and the amount it can supply is one line:

`Δz = W · sin φ`

W is the distance between the hip joints; φ is the pelvic obliquity. That is the whole payoff, and
the rest of this page is where those two numbers come from.

## A joint centre is inside you, so a tape measure cannot reach it

ANSUR II measured 4,082 men with callipers and has no hip joint separation in it. It has **hip
breadth** — 0.197 of stature, which is where the classic 0.191 H figure comes from — but that is skin
over trochanters over soft tissue, and the joint is centimetres medial of all three.

The number lives in musculoskeletal models, and there are two independent ones tracked in this repo:

| model | hip joints apart | its stature | its mass, from the paper | its mass, summed from the file |
|---|---:|---:|---:|---:|
| Delp et al. 1990 (`gait2392`) | 0.1670 m | 1.80 m | 75.16 kg | **75.165 kg** |
| Rajagopal et al. 2016 | 0.15452 m | 1.70 m | 75.3 kg | **75.337 kg** |

As fractions of stature that is **0.09278** and **0.09089** — two labs, a quarter of a century apart,
**2.1% apart**. The mean is used and the spread is published, because averaging away a disagreement
throws out the only estimate of how well a number is known.

**The statures are quoted from the papers, and that would be a bare literal** except that each file
independently confirms the other half of the same sentence: the papers say 1.80 m / 75.16 kg and
1.70 m / 75.3 kg, and summing the bodies in the files gives 75.165 and 75.337. A file that agrees on
the mass to four figures is the file the height belongs to.

| | |
|---|---:|
| **pelvis width, this body** | **0.1612 m** |
| abductor moment arm | 0.0412 m |

The lever is not a coordinate either — it is computed. For each gluteus medius and minimus
compartment the line of action runs from its origin on the ilium to its insertion on the trochanter,
both expressed relative to the hip joint centre, and the moment arm about the fore-aft axis is the
perpendicular component. Weighted by maximum isometric force over the six compartments it comes to
**0.0422 m in a 1.80 m body**. The textbook says the abductor lever is "about 5 cm"; this is that,
derived from a muscle path rather than remembered.

## The frontal pendulum, solved

Same law as fore-aft, same `ω₀ = √(g/H)` the parent already publishes, turned ninety degrees. With
`y` measured from the stance foot:

`ÿ = ω₀² y`  →  `y(t) = y₀ cosh(ω₀t) + (v₀/ω₀) sinh(ω₀t)`

**Periodicity is what makes it solvable, and it costs nothing to assume:** a walk is the same step,
mirrored, forever. Put `t = 0` at mid-step, where by that mirror symmetry the lateral velocity is
zero. Then `y = d·cosh(ω₀t)`, and half a step later the same condition must hold about the *other*
foot, a step width away:

`2 d cosh(ω₀T/2) = w`

That relates `d` and `w` and fixes neither. **One statement about the leg fixes both:** at mid-stance
the stance hip sits over the stance ankle, so the leg is a strut carrying a vertical load and no
frontal moment is demanded at either end. Then the centre of mass, which is `d` medial of the ankle,
is `d` medial of the *hip* — and half a pelvis medial of a hip is the pelvis centre:

`d = W/2`

Everything falls out of those two lines, and it falls out clean:

| | |
|---|---|
| CoM's medial offset at mid-stance | `W/2` |
| **step width** | `W · cosh(ω₀T/2)` |
| **lateral sway, peak to peak** | `W · (cosh(ω₀T/2) − 1)` |
| **margin of stability** | `(W/2) · e^(−ω₀T/2)` |

A pelvis width, magnified by half a step's worth of e-folding. Nothing was chosen to make them come
out that simple, and `measure()` checks all four identities rather than trusting this paragraph.

The **margin** is Hof's, unchanged. The extrapolated centre of mass, `XcoM = y + v/ω₀`, is where the
body would come to rest if the pressure point stayed put — so a foot placed lateral of it reverses
the fall and a foot placed medial of it does not. Solve for where the XcoM is at the step transition
and the next foot lands exactly `b` beyond it.

### What this body does, on this world

| | |
|---|---:|
| fall rate `ω₀` (inherited) | 2.648 rad/s |
| step time (inherited, derived) | 0.5927 s |
| e-folds in half a step | 0.785 |
| **step width** | **0.2134 m** |
| CoM medial offset at mid-stance | 0.0806 m |
| **lateral sway, peak to peak** | **5.22 cm** (2.98% of stature) |
| **margin of stability** | **3.68 cm** |

## The check nobody fitted, run at Earth gravity because that is where the data is

The 246 adults walked on Earth. Their step width may only be compared with what this law says **at
Earth** — Earth's `ω₀`, and their own measured step time. Feeding this world's gravity into a
comparison with Earth data is the mistake theAnkle's struck-through paragraph is a monument to: *a
formula that lands on the literature only at the local `g` has not been checked, it has been
flattered.* At `g = 7.076` this derivation scores 0.7% and deserves none of it.

| | |
|---|---:|
| step width, this law at Earth | 0.2440 m |
| step width, 246 adults measured | 0.2119 m |
| **error** | **+15.2%** |

**Fifteen percent high, reported as it fell.** A pelvis width from two musculoskeletal models, a step
time from a treadmill study, Earth's gravity, and one sentence about a leg being a strut. Nothing was
fitted to a step width, and here is a step width, to within a sixth.

The same disagreement, said as an angle, is smaller than it sounds. At Earth with the *measured*
width the pendulum puts the CoM 7.00 cm medial of the stance foot while half a pelvis is 8.06 cm.
Over a 0.93 m leg that 1.06 cm gap is **0.65 of a degree** of leg tilt. The one criterion — hip over
ankle — misses by two thirds of a degree.

## The sway, and the part that could not have been fitted

Fed the *measured* step width, so this check does not inherit the error of the one above it:

| speed | step width, measured | **sway, this law** | margin, this law |
|---:|---:|---:|---:|
| 0.910 m/s | 0.2119 m | **7.20 cm** | 2.64 cm |
| 1.300 m/s | 0.2110 m | **5.66 cm** | 3.36 cm |
| 1.688 m/s | 0.2125 m | **4.81 cm** | 3.89 cm |

Orendurff et al. (2004) measured mediolateral centre-of-mass displacement falling from about **7 cm
at 0.7 m/s to about 4 cm at 1.6 m/s**. This is that band, and it is that *slope*.

**And the slope is the interesting half.** Step width is flat across a near doubling of speed —
0.2119, 0.2110, 0.2125, a third of a percent — while the sway falls by a third. The law says exactly
why, and it is not that the feet move: sway is the width times `(cosh − 1)`, and `cosh` falls because
the step gets **shorter in time**. Walking faster does not narrow your stance; it shortens the
interval over which you are permitted to fall.

The margin does the opposite, and that is the same fact from the other side: at a step width that
does not change, a faster walk keeps **more** room to spare. Which is why hurrying across ice is not
obviously the wrong instinct.

> **The literature figures on this page are quoted, not held.** Orendurff (2004) and Bergmann (2001)
> are not in this repo; both are quoted to one significant figure from memory of the papers. The
> checks against them are ballpark checks, and `measure()` flags them `..._is_quoted_not_held` so
> nothing downstream can read them as measurements this story owns. The step-width check above is the
> only one that is fully internal.

## The muscle that holds the pelvis up — and the hip that pays

A list is not free: something has to resist it. In single support the pelvis is a lever. Everything
the stance leg is not — trunk, head, arms and the entire swinging leg — hangs medial of the stance
hip, and the abductors are the only thing on the other side. Take moments about the hip joint:

`F_abd · a = W_supported · c`

**`c` is not the whole-body offset**, and skipping that is worth 20%. The stance leg is a fifth of the
body and it hangs *under* the hip, contributing nothing to the moment; take it out and the remaining
mass's centre moves further medial by exactly `1/(1 − leg mass fraction)`.

The femoral head then carries the muscle and the load pressing the same way, so the joint contact
force is about `F_abd + W_supported`.

| | this world | at Earth |
|---|---:|---:|
| supported weight | 536 N | — |
| body's lever about the hip | 10.06 cm | 8.75 cm |
| abductor force | 1310 N = **1.96 BW** | 1.70 BW |
| **hip contact force** | 1845 N = **2.76 BW** | **2.50 BW** |

**That last cell is the second unfitted check, and it is the better one.** Bergmann et al. (2001)
measured hip contact force directly, through instrumented prostheses, and level walking comes out
near **2.4 body weights**. This chain gives **2.50** — from a lever arm read off a 1990 muscle path,
a lateral offset solved out of a hyperbolic cosine, and a mass fraction from de Leva. None of those
three has ever been near a hip prosthesis.

*(Honest deductions: this is a static single-support balance. It ignores the medio-lateral ground
reaction, and the real peak occurs where the vertical reaction is ~1.05 BW rather than 1.0 — both
push the true number up a few percent.)*

## The payoff: what the frontal plane hands back to theAnkle

The measured obliquity, read at the cohort and speed **the parent already chose** — this chapter
picks neither — over 246 adults:

| | |
|---|---:|
| peak obliquity, whole cycle | **4.46°** |
| range, peak to peak | 8.47° |
| peak within a double-support window | 4.26° |

Multiply by the pelvis width:

| | metres | of stature |
|---|---:|---:|
| hip height split, at peak | 0.01253 | **0.714%** |
| **hip height split, in double support** | **0.01198** | **0.683%** |
| theAnkle's residual | 0.0355 | 2.02% |
| theAnkle's estimate of the list's share | 0.0142 | 0.81% |

**The pelvic list accounts for 33.8% of the residual.** theAnkle guessed 40%, from the outside, and
was 84% of the way right. Neither the pelvis width nor the obliquity knew the residual existed: one
came from two musculoskeletal models, the other from a treadmill study, and the residual came from a
geometry check on a sagittal gait table.

That is the chapter's job, done. **A sagittal model was short 0.68% of stature in double support
because it had nowhere to put a tilt, and this is the tilt.**

## What you are looking at

One stride, from the front. Two steps, two lists, one sway.

- **The bar across the hips** is the pelvis, tilting by the measured obliquity. It is rigid and
  0.16 m wide, so tilting it puts its two ends at different heights — and that is the whole chapter,
  drawn at the size it actually is.
- **The flat line behind it** never tilts. That is the sagittal model's pelvis: both hips at one
  height, by construction. The gap opening at each end of the bar is the residual.
- **The legs splay** because each runs from a hip that is moving to a foot that is not. Nothing tells
  them to; the pelvis above them does.
- **The rod from the stance foot to the bright mark** is the inverted pendulum itself. It leans over,
  comes back, and swaps feet at the transition, because that is what the equation says a body does
  sideways.
- **The warm mark is where the mass is. The cool mark on the floor is where it is going** — the
  extrapolated centre of mass. Watch it run *ahead* of the body, out towards the next foot, and
  arrive a little short of it. **That gap is the margin of stability.** It is 3.7 cm, and it is the
  only thing between this and falling over.

Nothing is drawn above the hips except the segment from the pelvis to the centre of mass. A trunk's
length and a head's size are not derived here, and a render may not invent a body.

## What this still gets wrong

- **The step width is 15% wide and the sway is 15% wide with it**, at Earth. Both errors are the same
  error: the one geometric criterion — hip over ankle at mid-stance — is off by 0.65°. Whatever fixes
  that fixes both, and it will be something about the abductors *setting* the leg's angle rather than
  the leg being a passive strut.
- **The measured hip ad/abduction curve is not used, and it does not close.** It says the stance leg
  is adducted **4.06°** at mid-stance; the pendulum, the pelvis and the step width together say
  **0.65°**. A ~3.4° static frontal offset is the classic marker-model artefact, and picking a side
  of the disagreement would be inventing a resolution. It is published as `hip_abad_offset_deg` and
  spent on nothing.
- **The dataset's step width is itself odd.** 0.212 m between the feet, against the 0.10–0.13 m
  usually quoted for overground walking. Treadmills widen a stance and marker-model definitions of
  "step width" differ, but nothing ingested here states which definition this is — and every lateral
  number on this page is proportional to it. If it is a different quantity than assumed, the 15%
  above is explained and the agreement with Orendurff is luck.
- **The pelvis centre is treated as the CoM's lateral position.** The trunk leans (±6° here, measured)
  and the arms swing, so the two differ by around a centimetre. The render puts the lean back in; the
  derivation does not.
- **The pendulum's pivot jumps.** It swaps feet instantly at the middle of double support, because the
  model is a *single*-support pendulum with a point pivot. The real handover is spread over the 24.6%
  of the stride when both feet are down, and the centre of pressure crosses continuously between
  them. Smoothing the render would draw a physics this chapter has not written.
- **Nothing here is dynamic.** No perturbation, no recovery step, no reaction time. The one number
  pointing that way is the reserve: the walk uses **72%** of the ankle's lateral authority (half a
  foot's breadth is 5.09 cm; the margin is 3.68 cm), leaving 1.42 cm — a sideways nudge of about
  **0.038 m/s** before a step becomes obligatory rather than optional. Nothing in this repo has
  checked that number and it should be read as a prediction, not a result.
- **Standing still is not here.** The title promises "how a standing body stays up" and what is
  delivered is how a *walking* body stays up. Quiet standing is a different regime — no step to place,
  the whole job on the ankle, and postural sway with its own well-measured statistics. It is the
  obvious next thing and it is not written. With it go the verbs this chapter was declared for:
  **Brace [Y]** and **Steady Aim [Left Shift]**, and the reticle sway that is supposed to be
  theBreath at 15.7 breaths a minute showing up in the sights. None of that exists yet.
- **No pelvic ROTATION.** The stub promised list *and* rotation — the transverse-plane twist that
  lengthens a stride without lengthening a leg. Only the list is here. Rotation is a third plane and
  it is a third chapter.

*Contained in `theHuman`. What it hands on: a pelvis that is a bar and not a point, the reason a walk
is as wide as it is, and 0.68% of stature that a side view had nowhere to put.*
