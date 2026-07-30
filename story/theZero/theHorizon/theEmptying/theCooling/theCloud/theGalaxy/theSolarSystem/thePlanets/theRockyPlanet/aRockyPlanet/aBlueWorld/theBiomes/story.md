# theBiomes

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
