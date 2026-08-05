# theGarden

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 42** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **3.31094e+07 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** The world grows its life in one place and the whole world agrees where: the
equator, 21 °C and 99.8 cm of rain a year — a wet savanna-woodland, not a jungle, because that
climate is a hair short of the rainforest's 100 cm floor. The band that holds 90% of the peak is
2,018 km wide. The render is not a map of cells; it is the production field itself — how much life
each latitude actually makes — lit by the world's star from the equator, bright at the garden and
dark where nothing can grow.

*The lush place. The word "garden" is a verdict, and this chapter derives it.*

## The garden is an argmax, not a choice

Give the world its temperature and rain — both already published by its own law — and feed them
to the Miami model (Lieth 1975, the measured fit the biomes law already owns). The answer to
"where is the lush place" is not a pick: it is the latitude with the largest net primary
productivity. On this world that latitude is **0.0°**, the equator, because temperature and rain
peak at the same place, which is the rare coincidence of both axes at once.

`measure()` checks the verdict still holds on every grow: `lush_lat_deg == 0.0`. Change the
climate and the garden must move with the argmax, or the law lied.

## The savanna, not the jungle

The garden's own cell — read from the biomes law by path, never re-typed — is **savanna** (21.0 °C,
99.8 cm): a 20 °C+ latitude with under 100 cm of rain, which is exactly one centimetre short of
the rainforest's floor. This world's lush place is a wet woodland with 3 m trees and 4 kg/m² of
standing biomass, not a jungle. The green in the render is the savanna's measured reflectance
brightened by how close the local production is to the peak: the world's life is a number, and the
garden is where it is largest.

## The lush as a number

The peak production is **1,454 g/m²/yr**, which is **1.86×** the world's area-weighted mean of 780 —
the "lush" made into a number. The belt holding 90% of that peak spans **±11° (2,018 km)**; the
half is where the green glow visibly lives, and the whole reach of the lush is ±30° (5,506 km).
The equator grows **383 days a year** — no seasonal swing, so the garden is never frost-bitten.

## The one sun at the equator

The light is the world's star at the garden's own latitude: 37.03° above the horizon at the shared
opening hour, direction (0.496, 0.625, 0.602). `sun_direction()` declares it so the viewer arms the
renderer with exactly what the emit baked. The movie is one year: the production field is an annual
number and stays put, while the declination swings the terminator — the garden's green is stable,
its light is not, and that is the honest pair.

## The honest weaknesses, said plainly

The rain profile's *shape* is the Hadley circulation's signature — the same law aSteppeBiomes owns —
positioned at the parent's own band edges and scaled to the air's derived mean of 1.693464... mm/day,
so the garden's rain closes to the atmosphere's published number to ten digits. The shape's weights
are the circulation's standard form, not a fitted map. And the field is computed over *latitude*:
where the actual continents hold it is theTerrain's composition to draw. The equatorial peak is
real because both axes peak there; on a world where they did not, the argmax would move and the
folder's name would have to follow.

## The free dials

None. Temperature, rain, the Miami model, and the Whittaker table force everything above.

*Contained in `aBlueWorld`, after `theBiomes`. What it hands on: the place itself — the 
production field as light, and the lush as the argmax of a number no one picked.*
