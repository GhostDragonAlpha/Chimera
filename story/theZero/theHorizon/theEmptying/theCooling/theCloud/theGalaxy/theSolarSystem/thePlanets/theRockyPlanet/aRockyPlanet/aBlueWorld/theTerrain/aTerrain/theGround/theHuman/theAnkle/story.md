# theAnkle

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 25** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **2.0692 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** The joint that makes walking cheap, and the only one that touches the ground.
The parent's gait was a **sled**: both feet 4.2% of stature off the floor at mid-stride, duty factor
near 1.0 on each, no double support. Two faults caused it, and the second is this chapter — the knee
bent on the wrong leg, **and the foot had no joint.**

*The smallest membrane about a body.* Thirty-six centimetres, heel to toe, and its film is one stance
phase.

## A rigid foot cannot walk

A foot welded to a swinging shank has two options and both are wrong: plough its toe, or lift its
heel. It cannot keep a sole on the ground, because the sole's height is then a rigid function of the
leg's angle. That was the residual contact-plane travel the parent could not remove by fixing the
knee alone.

## The foot is worth 30% of the vault

Hansen, Childress & Knox measured the **roll-over shape** — the locus the effective contact point
traces during stance, in a shank frame — and found a circular arc of radius about **0.30 of leg
length**, near-independent of walking speed. That independence is what makes it a property of the
limb rather than of the gait.

A rocker of radius `R` rolls with its hub at *constant* height, so only the leg above the hub swings:

| | |
|---|---|
| rocker radius | **0.283 m** (0.30 of a 0.943 m leg) |
| a point foot vaults | 8.2 cm |
| **a rocker foot vaults** | **5.7 cm** |
| **the foot is worth** | **30% of the rise** |

That is a large part of why walking costs so little: **a third of the pole-vaulting is deleted by
having feet.**

## But the arc is not a wheel — and that trap cost a rebuild

I modelled it as a literal wheel first. The hip rose correctly and **the sole left the ground**,
because a wheel has nowhere to put a foot: measured, duty factor fell to **0.12**, worse than the
sled it replaced.

The arc is an **effective** description of three rockers in sequence, with an ankle pitching the foot
between them:

| rocker | share of stance | what is happening |
|---|---:|---|
| **heel** | 15% | toe up, rolling forward over the heel |
| **ankle** | 50% | sole flat and still; the shank rotates over it |
| **forefoot** | 35% | heel rising, rolling off the ball |

**Model the joint and the arc emerges. Model the arc and the joint disappears.** The three fractions
are measured kinematics and they partition stance exactly — `measure()` checks they sum to one.

## What it pushes with, and the check nobody fitted

At toe-off the ground reaction acts on the forefoot lever. Both numbers come from above: a body
weight this chain derived, a peak ground reaction measured in body weights, and a lever measured off
a cadaver.

`τ = 1.2 · mg · 0.10h` → **122.7 N·m**

Divide by the body mass and it is **1.51 N·m/kg**. **The measured peak ankle moment in human walking
is ~1.5 N·m/kg.** Nothing here was tuned toward that — it is three inherited numbers multiplied
together, and it lands on the literature to within 1%.

> ### That check was wrong, and this is what it took to see it
>
> Two years of gait data later — 246 adults, joint moments at every percent of the cycle — the peak
> plantarflexor moment measures **1.51 N·m/kg**. The *result* above is right to three figures.
>
> The *inputs* are not. The measured peak ground reaction is **1.10** body weights, not 1.2, and the
> forefoot lever is **0.071** of stature, not 0.10. Two errors of opposite sign, cancelling.
>
> And the arithmetic never even belonged to Earth: `1.2·g·0.10·h` gives 1.51 only at **this planet's
> 7.08 m/s²**. At Earth's 9.81 the same formula returns **2.09 N·m/kg** — 39% above the literature
> value it was being congratulated for matching. The agreement was a coincidence of local gravity.
>
> **A check that passes for a compensating reason is not a check**, and from the inside it looked
> exactly like one. The torque now comes from the measured curve. The paragraph above is left
> standing because deleting it would delete the lesson.

| | |
|---|---|
| push-off work | **55 J** per step |
| mean power over a step | 86 W |
| work to lift the vault, per stride | 96 J |
| **the ankle's share of positive work** | **45.6%** |

**That last row is a second check that was not fitted.** The literature puts the ankle at 45–50% of
the positive work in walking; this chain gives **45.6%**, from a torque it derived and a vault it
derived, agreeing to within 4%. I had written 37% here from an earlier, cruder vault measurement, and
the chapter's own `measure()` corrected me — which is the arrangement working.

## What it fixed, measured

| | sled | wheel | **the joint** | a real walk |
|---|---:|---:|---:|---|
| contact-plane travel | 4.2% | 3.9% | **1.2%** | 0 |
| duty factor, each foot | ~1.0 | 0.12 | **0.58 / 0.60** | 0.55–0.65 |
| double support | 0% | 0% | **17–21%** | ~20% |
| swing-foot clearance | ~0 | — | **9.7%** | 8–15% |

The footfall diagram is the alternating Hildebrand pattern the studio's gait witness looks for, with
the overlap that makes it a walk rather than two abutting hops.

**And one structural thing had to change to get there.** The hip angle was `swing·sin(φ)`, which puts
each foot down for *exactly* half the cycle — so the two stances abut and never overlap, and without
overlap there is no leg pushing off while the other reaches. **A sine cannot produce a walk.** The
cycle is now parameterised by duty factor directly, with 0.60 as a measured input, and the 0.2 of
overlap that buys is where double support comes from.

## What you are looking at

One foot, heel strike to toe off, on a line that is the ground.

The bright mark is **the centre of pressure** — where the ground is pushing, now. It starts under the
heel, sweeps forward along the sole, and ends under the ball of the foot. The pale trail behind it is
where the pressure has already been, so **the roll-over shape draws itself**, by the thing that makes
it, rather than by a curve fitted over the top.

**And it took a correction to get right.** The first version asked the *geometry* where the foot
touched — the lowest point of the sole. But **a flat foot has no lowest point**: while the sole is
flat every part of it is equally low, so the mark sat on the heel through half of stance and then
*teleported* to the toe the instant the pitch went negative. The sweep this page describes is real,
but it is not caused by the pitch: the centre of pressure advances **because the body advances over
it.** That is measured CoP behaviour, and it is what turns three rockers into one continuous arc.

## What is honestly still missing

Three of the four entries that stood here have been closed, and by the same thing: the parent's gait
stopped being a model and became 246 measured adults. They are kept, struck through, because what
closed them is more useful than the fact that they are gone.

- ~~**The vault is still too tall** — 4.7% of stature against a human ~2.5%. The remaining cause is a
  fully *locked* stance knee; real walking flattens the path with a stance-knee flexion wave of about
  15° at mid-stance.~~ **CLOSED.** The measured knee has that wave — **18.2° at 11% of the cycle** —
  and the vault fell to **2.36%** at Earth gravity against the literature's 2.5%. The mechanism was
  named here rather than the number scaled, and naming it is what let the data close it untouched.
- ~~**The peak of the hip path is at push-off, not mid-stance.**~~ **CLOSED.** It peaks at **29% of
  the cycle**. Two things fixed it: the pelvis now rides its legs weighted by the load each is
  actually carrying (measured GRF) instead of by whichever is tallest, and the foot pivots on the
  **ball** rather than the toe tip. The second was the diagnosis written above — *"treating the foot
  as rigid about a single pitch"* — and it was worth 3.6 cm.
- ~~**`swing = 0.42` rad is still the one number in this gait neither derived nor measured.**~~
  **CLOSED.** There is no amplitude any more; there is a curve.
- **No arch, no toes, no heel pad.** A foot stores and returns elastic energy in its plantar fascia
  (~8–17% of the stride's work) and none of that is here. **Still open.**
- **New, and precisely located:** in double support the two legs disagree by **2.02% of stature**
  about where the pelvis is. In single support the model is exact — sole error 0.000%. About 40% of
  the residual is pelvic list, which is frontal-plane and belongs to `theBalance`.

*Contained in `theHuman`. What it hands on: the reason a walk is cheap, and a sole that stays down.*
