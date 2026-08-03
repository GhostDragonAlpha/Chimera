# THE SEAM — where the prologue ends and the world begins

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

> Measured 2026-08-01 with `tools/slider.py`. The story has **two regimes**, joined at a physical
> seam, and until now nothing said so — which is why a slider had to find it.

---

## The measurement

Move one free number and watch what follows.

**The seed's mass** (`theHorizon.M_added`, ×3):

    theHorizon     4/8  moved        theEmptying   5/5  moved
    theCooling     1/11 moved
    theCloud       0/15 moved   <-- and every chapter below it, ~600 numbers, nothing

**The planet's rotation** (`theRockyPlanet.rotation_hours`, ×1.6):

    everything ABOVE theRockyPlanet   0 moved      <-- correct: a spin cannot reach the Big Bang
    theRockyPlanet 3/36    aBlueWorld    11/55     aSteppeBiomes 12/39
    theAtmosphere  3/13    aSaltOcean     8/38     aTerrain       3/36
    theGround      3/37    theHuman      10/103

---

## What it means

**Chapters 0–11 are a PROLOGUE.** They derive the constants: the Planck scale from ħ, G, c; the
recombination temperature from hydrogen's 13.6 eV bond; the Jeans mass that fixes the size of the
first bound objects. Those numbers are *supposed* to sit still when a dial moves — that is what a
constant is. A universe that started hotter still recombines at 3760 K.

**Chapter 12 down is the WORLD**, and it is a live derivation. Change the day length and the
atmosphere's circulation changes, the biomes shift, the ocean responds, the terrain reshapes, and
**the person standing on it walks differently** — 10 of `theHuman`'s 103 numbers move because a
planet spun slower.

    THE PROLOGUE'S JOB IS TO JUSTIFY THE CONSTANTS, NOT TO PROPAGATE THEM.

So "declare universal truth and skip the first thirteen billion years" is not a shortcut. It is an
accurate description of what the code already does, and stating it is a correction to the
documentation rather than to the physics.

---

## The one thing that is genuinely wrong

`theCooling` types its own duration:

    "duration_s": 3.8e5 * 3.1557e7          # 380,000 years, by hand
    "extent_m":   c * 3.8e5 * 3.1557e7

The time to recombination is not a constant of nature — it follows from the expansion history,
matter and radiation densities integrated down to the temperature atoms need. Every chapter
inherits its scale from its parent, so this literal is the anchor the whole lower tree hangs from.

Being in the prologue makes it *cheaper* to leave, not correct. It is a named debt, recorded in
`theCooling/story.md`, and a typed number that is named is a debt while one that is hidden is a lie.

---

## What this licenses

Expansion in any direction, from chapter 12 down, without re-deriving cosmology. Add a moon, a
second continent, a city, a creature — each hangs off a parent whose numbers respond to the dials
above it, and `tools/slider.py` will say so in one run. The fundamentals hold where a game lives.

    python tools/slider.py --dial theRockyPlanet:rotation_hours --factor 1.6
