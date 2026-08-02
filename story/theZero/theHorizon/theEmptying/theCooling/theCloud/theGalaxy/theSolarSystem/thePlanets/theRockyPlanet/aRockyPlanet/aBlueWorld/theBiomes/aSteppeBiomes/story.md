# aSteppeBiomes

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 36** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **3.31094e+07 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** A cold, dry world wearing mostly grass: a wide steppe belt around the
mid-latitudes, woodland and savanna nearer the equator, ice past 63°, and a frost line that
breathes 19 degrees poleward and back through the year.

*An instance of `theBiomes`, named by its dominant band.*

## The bands the table forced

The parent's climate gives each latitude a temperature and a rain; the Whittaker table turns each
into a band:

| share of the sphere | band |
|---|---|
| 32% | **steppe** — cold grassland, the dominant band |
| 16% | savanna |
| 14% | temperate woodland |
| 14% | ice |
| 9% | tundra |
| 8% | cold steppe |
| 7% | boreal forest |

Nobody picked the winner: the table decided, and the folder's name is that answer. `measure()`
checks the name still matches — change the climate and the name must move with it.

## The year's breathing

The obliquity is 37° — stronger seasons than Earth's — so every latitude's temperature swings
through the year, hardest at mid-latitudes (±13 °C at 45°). The frost line, the 5 °C edge where
growth stops, sits at **37°** on average and swings to **15° in winter and 54° in summer**. The
movie of this membrane is **one year**: the bands migrate poleward and back, and that is the
rung of the ladder where a year finally fits in one film.

## What grows

The equator grows **383 days a year**; the 45th parallel gets **132 frost-free days**. The Miami
model (Lieth 1975, measured fit) prices the world's food budget band by band; the tallest canopy
the climate allows is **18 m** (the temperate woodland belt), the richest standing biomass **22
kg/m²**.

## The honest weaknesses, said plainly

The rain profile's *shape* is the Hadley circulation's signature — wet at the rising branches,
dry at the descending ones — positioned at the parent's own band edges (12.7° / 39.6°) and scaled
to the air's derived mean of 1.69 mm/day. The positions are the parent's climate solution; the
weights are the circulation's standard form, not a fitted map. And the bands are computed over
*latitude area*: where the actual continents hold them is theTerrain's composition to draw.

## The free dials

None. Climate and the table force everything above.

*Contained in `theBiomes`. What it hands on: the band map and its seasonal swing, the growing
calendar, the productivity budget — everything a seed, a herd, or a farmer needs.*
