# theGround

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 21** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **86400 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** Four metres across. The parent gave the *shape* of the land over twelve
kilometres, and never said what any of it is made of — but a shape cannot be stood on. This chapter
answers the only question a body actually asks of a planet: **will it hold me, and how far do I
sink?** It holds. You sink less than a millimetre.

*The scale where "the ground" stops being a surface and becomes a material.*

## Soil is made from the rock underneath it, and the deeper it gets the slower it is made

Bedrock turns into soil when frost, roots and water get at it — and a thick soil **insulates** the
rock from all three. So production falls off exponentially with depth (Heimsath, Dietrich,
Nishiizumi & Finkel 1997, measured with cosmogenic nuclides):

```
P(h)  =  P₀ · e^(−h/h₀)
```

Balance that against erosion carrying it away and the steady depth is `h = h₀·ln(P₀/E)`.

### And that equation predicts a hillside without being told about one

There is no slope anywhere in it. But erosion rises steeply with slope, so:

| slope | soil |
|---|---|
| 0° | 2.15 m |
| 5° | 1.00 m |
| 10° | 0.65 m |
| **17°** (this land's mean) | **0.37 m** |
| 24° | 0.19 m |
| 30° | 0.06 m |
| **33°** | **none — bare rock** |

**Soil thins uphill, deepens in hollows, and runs out entirely above about 33°.** That is what every
hillside on Earth looks like, and none of it was put in — it falls out of one exponential and one
erosion rate. The bare-rock threshold in particular is not a rule added on top: it is where the
logarithm goes negative, because the hill is being stripped faster than rock can become soil.

## Breaking rock is fractal, which is why all soil has the same shape

Break a rock and you get pieces; break those and you get the same distribution one scale down.
Repeat, and the mass fraction coarser than `d` follows a power law with dimension **2.6**. It is why
every soil on every planet has the same *shape* of grain-size curve however different its chemistry:
a few big clasts, a great many fines.

## Will it hold a person

Terzaghi: ground fails when a load pushes a wedge of it sideways, and what resists is friction
between grains plus whatever sticks them together.

| | |
|---|---|
| the ground carries | **41 kPa** at 5 cm down |
| …and at the surface | **23 kPa** — below this, nothing dents it at all |
| the standard bearing plate | **19 kPa** — under the threshold, so it leaves no mark |
| a person's foot | **24 kPa** — over it, and sinks **3.1 mm** |

**Cohesion is read, not typed, and for a long time it was typed.** This table used to say
**110 kPa** and *"sinkage under 1 mm"*, and the second number was not under 1 mm — it was
**0.00000000000000000087 mm**, a thousand times smaller than a proton. Nothing in this world
could leave a footprint, and nothing said so. One constant did it: a hand-written
`COHESION_PA = 2000` under the comment *"damp soil holds itself together a little"*, where this
world's own materials library publishes **0.5 ± 0.4 kPa** for this regolith (Mitchell et al. 1972).
Four times the researched mean, and it set the surface capacity to 92 kPa — nearly four times the
pressure under a person, so the equation balanced before it began.

It is read through the library now. **A person leaves a 3.1 mm print, and a jump punches in
however softly it is landed** — which is what walking on dry sand actually feels like.

**And the print is shallower here than it would be on Earth by more than gravity explains.** The
same body on the same soil leaves **20.9 mm** at Earth's gravity and **3.1 mm** here — 6.7× for a
gravity ratio of 1.39×. Cohesion does not scale with *g* while the load does, so a low-gravity
world sits nearer the threshold at which prints stop existing. Nothing was fitted to produce that;
it falls out of which term carries the *g*.

**The friction angle is not the repose angle**, and that distinction cost a fix. Loose material
poured into a heap settles at **40.03°** — this studio's own number, *grown* from a stochastic
sandpile in `core/trainables/granular.py` and never fitted to the lunar measurements it landed
inside. But the same material **under a foot** is compacted, and Terzaghi's factors climb so steeply
with angle that using the loose value returned 413 kPa — three times what real soil carries. Same
property, different packing, different number.

## What was wrong first

The erosion reference was set at 50 mm/kyr, which put the bare-rock threshold at **15°** — below
this landscape's own mean slope of 17°. The entire hillside would have been stripped rock, and the
chapter would have described a world with no soil on it at all. 21 mm/kyr puts the threshold at 33°,
which is where real soil-mantled hillslopes go bare.

*Contained in `aTerrain`. What it hands on: a surface that bears weight, and the grain of it.*
