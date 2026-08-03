# aYellowStar

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
> **[docs/THE_LAW.md](../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 41** of the story  ·  **t = 3.0047e+17 s** since theZero  ·  lasts **2.96921e+17 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** This system's own star. Its whole life is one standoff: gravity pulling in,
fusion pushing out, holding each other exactly still — and every number about it, from its colour to
how long it lives, falls out of its mass alone.

**the yellow hearth — the one this world orbits**

**Its name is a derived fact.** Stars are classified by surface temperature (O B A F G K M), and
this one balances at 5772 K, which is class **G — yellow**. It is not called that because anyone
chose to; it is called that because that is what it *is*, and `measure()` checks the folder name
still matches the class its physics produces.

`theStar` said what a star *is*: a fall stopped by fire, and the smallest mass at which fire can
light. **This is the star that actually formed here**, and it takes its mass from the system that
made it.

Everything else follows from that one number.

## What its mass decides

```
R = R☉ (M/M☉)^0.8            L = L☉ (M/M☉)^3.5            T = (L / 4πR²σ)^¼
```

The temperature is not chosen — it is what balance *forces*. Whatever is generated inside must leave
through the surface, so the surface glows at exactly the temperature that radiates it away, and no
other. For this star: **5772 K**, which is why it looks the colour it does.

## What its surface is doing

Heat cannot get out by radiation alone in the outer layers, so the gas **overturns**: hot columns
rise, cool at the top, and sink at the edges. That is convection, and you can see it — the surface
is tiled with **granules**, each about 1000 km across, bright in the middle and dark at the rim,
each one the top of a rising column. The temperature contrast is small (~±250 K) and it is real.

## How long it lasts

A star burns its fuel at the rate its luminosity demands, so its life is `fuel / burn = M / L`:

```
lifetime ∝ M / M^3.5 = M^-2.5        →  ~10 billion years for this one
```

**A star twice as heavy lives less than a fifth as long.** Heavier is not better; it is briefer.

*Contained in `theStar`. What it hands on: a luminosity that lights everything outward, a surface
temperature that sets its colour, and a lifetime that bounds every story told beneath it.*

## What it predicted that it was never given

`lifetime_yr` = **9.41 billion years** — how long this star can burn hydrogen in its core.

    the Sun's main-sequence lifetime is ~10 billion years

And `T_surface` = **5839 K** against the Sun's measured **5772 K** — 1.2% out, for a star this
story grew from a collapsing fragment rather than copied from a table. The mass came out at 1.025
solar masses, so a slightly heavier star burning slightly hotter and living slightly less long is
exactly the direction the physics demands: luminosity climbs as roughly the cube of mass, so more
fuel is spent faster than it is gained.
