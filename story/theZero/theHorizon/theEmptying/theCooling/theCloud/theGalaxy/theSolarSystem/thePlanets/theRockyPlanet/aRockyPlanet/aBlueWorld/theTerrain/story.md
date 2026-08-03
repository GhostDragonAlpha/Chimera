# theTerrain

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 17** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **86400 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** The last chapter said how much water there is but refused to say where the coast
is, because on a perfectly smooth world there isn't one — the sea just goes all the way round. Land
exists only because some rock stands higher than the water reaches. This chapter works out how high
rock is *able* to stand, and then fills the low ground with the water until it fits. Where it stops
is sea level, and everything above it is land: **30% of this world.**

*The planet's outer membrane.* Not a patch of ground — the whole shell, seen at the scale where
continents are the things you can make out.

## How tall a mountain can be

```
h = σ / (ρ g)        rock crushes at σ ≈ 200 MPa
```

Pile rock up and the pressure at the base grows. Past the point where the rock gives way, the base
spreads and the mountain sinks into itself. So there is a **ceiling**, and it is set by **gravity**,
not by geology.

**It predicts a mountain it was never shown.** Earth's ceiling comes out at 7.6 km, and the tallest
thing on Earth measured base-to-summit — Mauna Kea, 10.2 km — sits right at it. Mars has 0.38 of
Earth's gravity, so its ceiling should be about **2.6× taller**. Olympus Mons is 21.9 km against
Mauna Kea's 10.2: a ratio of **2.15**. One line, nothing fitted, right to within a fifth.

Here, at 0.73 g, the ceiling is **10.4 km**, and the highest land stands **7.7 km** above the sea.

## Why there are two heights and not a smooth slope

Crust floats on mantle the way ice floats on water, so a **thicker, lighter** block stands higher and
has a deeper root. There are two kinds of it:

| | thickness | density | floats at |
|---|---|---|---|
| continental (granite) | 30 km | 2,700 | high |
| **shelf** — continental rock stretched at a block's edge | 18 km | 2,700 | between |
| oceanic (basalt) | 7 km | 2,900 | low |

The step from continent to seafloor here is **5.5 km** — and *that* is why a coastline is a sharp
line rather than a gentle shading. It is not drawn. It is where two populations of crust stop
overlapping.

**The shelf is not a detail.** With only two populations this law reported 35% of Earth dry against a
measured 29%. The margins float between the two, and they are what drowns first. Add them and Earth
comes out at **29.6%**.

A basin full of water is also **carrying** that water, so it sits **923 m** lower than a dry one
would. Leave that out and you overstate the step by a kilometre.

## Sea level is solved, never placed

The water has a volume; the ground has a shape; sea level is just the height at which the two agree.
Here that is **+3,100 m** above the seafloor datum, which leaves **30% land**, seas averaging
**3.0 km** deep and reaching **6.5 km** at the deepest.

Run Earth's own numbers through the same solver and it returns **29.6% land** with a mean ocean depth
of **3,815 m**. The measured values are 29% and 3,800 m.

### What it still gets wrong, said plainly

Mean **land elevation** comes out at 2.4 km here and 1.5 km for Earth, against Earth's measured
840 m. The law puts continents about 1.8× too high. The missing piece is that real continental crust
is denser at depth than the single density used here, so it floats lower than simple isostasy says.
The land *fraction* and the ocean *depth* are right; the average height of the land is not, and no
number in this chapter has been bent to hide it.

## The dial: how much light crust

Everything above is forced. **How much of a world's crust ever separated into the light, thick,
buoyant kind is not** — that is a fact about its history, so it is free, and it is the single dial
that moves every coastline at once:

Turn it up and there is more land — but it stops paying off past about 60%, because with almost no
deep basin left the water has nowhere to go but onto the continents, and drowns them as fast as you
make them.

## Its name

A body seen from outside is classified by its colour. A surface you **stand on** is classified by
**what carves it** — because that is what its shape is made of. Here 57% of the land gets rain rather
than ice, so running water is in charge: **`aRiverTerrain`**.

## Snow is a temperature, not a latitude

An ice cap and a mountain snowfield are the same fact — water below freezing — so there is one rule,
and it needs the **lapse rate**: air cools as it rises and expands, at `Γ = g/c_p`, about two-thirds
of that once the heat released by condensing water is counted.

That is derived, and it predicts what it was not fitted to. Earth's `9.81/1005` gives 9.8 K/km dry
and 6.5 K/km moist — both textbook — and puts Earth's tropical snow line at 4.2 km against a measured
4.8. Here gravity is weaker, so air cools **more slowly** with height: **4.7 K/km**. This world's
snow line therefore stands *higher* than Earth's, despite the world being far colder overall.

The same rule freezes the sea. Water has no altitude, so the ocean freezes purely by latitude — which
is why both poles here are ice even where there is no land under them.

## Where the clock finally comes into reach

This membrane's movie is **one day**, not one year. That is the rung where the gearing ladder
finally steps into the band a person can feel: the parent's year-long film could not show a sunrise
without strobing 394 of them past, and here the sun crosses the sky exactly once.

*Contained in `aBlueWorld`. What it hands on: a sea level, a land fraction, a relief ceiling, and
the name of the process that carves it.*
