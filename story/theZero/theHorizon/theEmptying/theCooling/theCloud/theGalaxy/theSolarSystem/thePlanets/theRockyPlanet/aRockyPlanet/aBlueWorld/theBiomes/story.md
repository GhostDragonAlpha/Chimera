# theBiomes

<!-- CHIMERA-LAW -->
> *Derive before you train — [THE LAW](../../../../../../../../../../../../../docs/THE_LAW.md). Every number below is derived from the parent's or measured; none is chosen.*
<!-- CHIMERA-LAW -->

> **chapter 35** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **3.31094e+07 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** A biome is the largest community of life a climate can hold. Give a world's
temperature and its rain, and the bands are forced — because life has requirements that do not
negotiate: warmth enough to grow, water enough to drink, light enough to eat.

*The law of life's bands. The instance of it here is `aSteppeBiomes`.*

## The two axes

Mean annual temperature × annual rain. The established classification — Whittaker, 1970 — is a
table on those two axes: rainforest, seasonal forest, temperate forest and woodland, taiga,
steppe, savanna, desert, tundra, ice. Change the climate and the same table repaints the world.
Nothing about a biome is chosen.

## The measured look

Each band reflects light its own measured way. Chlorophyll absorbs blue (430–450 nm) and red
(640–680) and throws green back — and past 700 nm the reflectance jumps so sharply (the **Red
Edge**) that satellites find plants by it. Sand returns ~0.35 across the band; snow ~0.85; open
water ~0.06. A biome map is a reflectance map, and the render reads the measurements.

## The production

Lieth's Miami model (1975) — fitted to measured sites worldwide — turns temperature and rain into
net primary productivity, whichever limits harder: the world's food budget, cell by cell.

## The classification

A band-set is named by its **dominant band** — the one covering most of its world's land
latitudes — and `measure()` checks the name still matches, exactly like the star's colour class.

*Contained in `aBlueWorld`, sibling to `theTerrain`, `theAtmosphere` and `theOcean`. Contains
`aSteppeBiomes` — the bands that actually wrap this world.*
