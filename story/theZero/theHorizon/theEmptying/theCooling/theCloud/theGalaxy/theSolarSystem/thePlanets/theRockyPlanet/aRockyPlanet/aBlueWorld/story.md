# aBlueWorld

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 14** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **3.31094e+07 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** This is the weather, worked out for the world the last chapter built. It turns
out to be an ice-age Earth: an average of about **−0.5 °C**, ice reaching down from both poles to
about **35° latitude**, and liquid ocean across the middle third. That liquid water is why it is
called *a blue world* — the name is the answer, not a label put on it.

It is not uniformly cold. The same profile that puts the ice line at 35° puts the **equator at
+14.5 °C** and the **poles at −30.5 °C** — a temperate band with an ice sheet at each end.

*The first membrane that could have gone either way.* Everything above this was forced. Here three
different feedbacks push against each other, and the temperature is whatever value all three can
agree on at once.

## Why the temperature has to be *solved*, not calculated

Three loops, all running into each other:

- **The greenhouse.** The air the parent kept lets sunlight in and slows heat out, so the ground runs
  hotter than bare balance. Earth's version of this is worth 33 K; this world's is worth **33.6 K**.
- **Ice.** Cool it down and ice spreads; ice is bright, so it reflects more, so it cools further.
  A runaway, if nothing stops it.
- **Carbon.** Cool it down and the rain stops scrubbing CO₂ out of the air, so CO₂ builds up, so the
  greenhouse deepens and it warms back. A brake on the runaway.

Because each depends on the answer, there is no formula — you have to look for the temperature that
is **consistent with the albedo and the CO₂ it produces**. That self-consistent value *is* the
climate.

## The thermostat is doing almost all the work

| | mean temperature |
|---|---|
| with the carbon cycle | **272.6 K** (−0.5 °C) — ice caps, open ocean |
| without it | **234.0 K** — frozen pole to pole, permanently |

**38.7 K.** That is what the carbonate–silicate cycle is worth to this planet, and it is the
difference between a world you could stand on and a snowball. It is also the honest reason a
habitable zone has an outer edge: the thermostat is bounded by the carbon a planet actually has, and
past that bound it runs out of gas. Here it is holding **3.1×** Earth's CO₂ and has plenty left.

## It gets Earth right, and it was not fitted to

Run Earth's own mass and orbit through this same law and it returns **288 K** and an ocean
**2,700 m** deep. Both are Earth's measured values. Neither was put in.

And a check nobody arranged: an ice line at **35°** is close to where the ice actually stood at the
Last Glacial Maximum — about 40° north. This world simply sits permanently in the state Earth visits
during an ice age.

### One profile, or the numbers drift

Temperature-against-latitude used to be written twice — once here as a straight ramp, and again in
the terrain below with different constants. The two answers were six degrees apart, and the terrain
drew a hard white band across a world that does not have one. There is now **one** profile, it lives
here because the climate does, and everything below reads it rather than rebuilding it.

Fixing that turned up a second error underneath it. Earth's albedo of 0.30 is measured **with** its
ice on, so feeding 0.30 in as the ice-free ground and then adding ice counts Earth's ice twice. The
ice-free figure is **0.227** — solved from the measurement, not chosen.

## Where the water came from

It cannot have formed here. This world grew *inside* the snow line, where water is vapour and does
not stick to anything. So the ocean was **delivered** — thrown inward later from beyond the line,
where the disk had four times as much solid material because ice counts as rock out there. Scaled to
this world's mass and its system's ice supply, that delivery is **half an Earth ocean**, which spread
over a smooth sphere would lie **2.0 km** deep.

## What it deliberately does not say

**Where the coast is.** With no relief a world is ocean all the way round; land exists only because
rock stands above sea level. That belongs to the terrain, so this chapter hands down a sea depth and
lets the next one subtract the continents.

*Contained in `theRockyPlanet`. What it hands on: a surface temperature, a sea level, an ice line,
and the gravity to stand in.*
