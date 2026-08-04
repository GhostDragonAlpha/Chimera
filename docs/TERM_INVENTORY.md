# TERM INVENTORY — what the engine declares against what it can draw

**2026-08-04.** `ChimeraEngine/terms_data.py` declares **59** terms. `splat_appearance.scene_terms()` can render **42**. The intersection is **13**.

These are two nearly-disjoint vocabularies, and the gap is not a naming problem.

| | count |
|---|---:|
| declared in `terms_data.TERMS` | 59 |
| renderable via `scene_terms()` | 42 |
| **HAVE EMIT** — declared *and* renderable | **13** |
| **DECLARED ONLY** — declared, no `emit()` anywhere | **46** |
| **SCENE WITHOUT TERM** — renders, not declared | **29** |

## THE FALSIFIER DID NOT FIRE

> *"The inventory shows fewer than 10 true gaps — the 46 resolves to mostly terminology mismatches, not missing code."*

**46 true gaps.** Not one of the 46 has a `physics.py`. Exactly one — `aPlanet` — has a `story/` folder at all, and it is awaiting its law. Checking for naming variants by string similarity against the renderable set returns five candidates, of which **one** is a real concept match (`aPlanet` ↔ `aRockyPlanet`/`aBlueWorld`, the abstract of two instances); the other four (`theScan~theStance`, `theSeed~theSweep`, `theSpace~theStance`, `theState~theStance`) are string similarity with no shared meaning, and reporting them as matches would be the instrument talking. **At most 1 of 46 is terminology. 45 are absent code.**

## HAVE EMIT — declared and renderable (13)

| term | parent | kind | what it is |
|---|---|---|---|
| `theAtmosphere` | aPlanet | P | air, sky, weather |
| `theBalance` | theVerbs | P | center-of-mass vs center-of-thrust |
| `theBiomes` | aPlanet | P | climate + life bands |
| `theDensityClock` | theSolarSystem | P | time leans with mass and speed |
| `theGround` | aPlanet | P | the surface underfoot (matter under boots) |
| `theInterior` | aPlanet | P | layers, ore, caves |
| `theMining` | theInterior | P | planetary excavation -- the dig verb on a world (bore, ore, claim, beacon) |
| `theOcean` | aPlanet | P | the water |
| `thePlanets` | theSolarSystem | P | the worlds in orbit |
| `theSolarSystem` | theStory | P | the setting you fly |
| `theStar` | theSolarSystem | P | the yellow hearth |
| `theTerrain` | aPlanet | P | the whole-sphere surface |
| `theThrust` | theVerbs | P | energy -> motion (the density clock) |

## DECLARED ONLY — no `emit()` anywhere (46)

`story?` = a `story/` folder exists · `physics?` = it has a law · `engine_state?` = the name appears in `engine_state.py`

| term | parent | kind | story? | physics? | engine_state? | what it is |
|---|---|---|---|---|---|---|
| `aPlanet` | thePlanets | P | yes | — | yes | the world you fall toward |
| `theBlackHole` | theDescent | P | — | — | yes | the density clock's ceiling; the hole you can't see into |
| `theChoice` | theMeaning | H | — | — | — | good and evil; the human decides |
| `theDescent` | theStory | P | — | — | yes | traversing the scales (the membrane onion; LOD of meaning) |
| `theDeterminism` | theSeed | P | — | — | yes | same seed -> same world, bit-identical |
| `theDig` | theVerbs | P | — | — | yes | into the ground (grain physics) |
| `theEVA` | theVerbs | P | — | — | — | suit traversal in vacuum / low-g (jetpack, mag-boots) |
| `theEcosystem` | theGarden | P | — | — | — | life cascading from physics |
| `theExperience` | theMeaning | H | — | — | — | the felt whole; understood, not won |
| `theFarming` | theGarden | P | — | — | — | cultivation -- grow food from energy + soil (the grow verb, tended) |
| `theFlight` | theShip | P | — | — | — | translation, pitch / yaw / roll, VTOL, wings, landing gear |
| `theFruit` | theTree | H | — | — | — | knowledge of good and evil |
| `theGarden` | aPlanet | P | — | — | yes | the lush living place (lushEden) |
| `theGrow` | theVerbs | P | — | — | yes | life from energy (logistic) |
| `theInput` | theLoop | P | — | — | — | keystrokes -> verb dials |
| `theLaws` | theSeed | P | — | — | — | the trained physics the seed runs under |
| `theLoop` | theStory | P | — | — | yes | world + player + input -> verbs -> state -> tick |
| `theLunarFarm` | theFarming | P | — | — | — | farms on airless / low-g worlds (domes, regolith hydroponics) |
| `theMeaning` | theStory | H | — | — | yes | deciding what things mean; the gift, your terminal |
| `theMelee` | theVerbs | P | — | — | — | close-quarters strike |
| `theNavigate` | theVerbs | P | — | — | — | orbital mechanics, reach a target |
| `theOrbitalFarm` | theFarming | P | — | — | — | hydroponic farms in orbit / deep space |
| `theParadise` | theMeaning | H | — | — | — | does Eden read as paradise |
| `thePersistence` | theLoop | P | — | — | — | same seed, same world, forever (save / return) |
| `thePlanetaryFarm` | theFarming | P | — | — | — | farms on a world's surface |
| `thePlanting` | theGarden | P | — | — | yes | the tree grows into the surface (the seam) |
| `thePlayer` | theLoop | P | — | — | yes | the character; presence before action (the Dot) |
| `theSalvage` | theShip | P | — | — | — | the industrial array -- space mining + graviton handling |
| `theScan` | theVerbs | P | — | — | — | read composition (spectral) |
| `theSeed` | theStory | P | — | — | yes | the number + the laws that unfold the world |
| `theShields` | theShip | P | — | — | — | the barrier grid + directional bias |
| `theShip` | theStory | P | — | — | yes | the player's vessel; the cold start |
| `theShipCombat` | theShip | P | — | — | — | targeting grid, batteries, heavy ordnance, countermeasures |
| `theShipPower` | theShip | P | — | — | — | power buses + capacitor routing (attack / drive / barrier) |
| `theShipView` | theShip | P | — | — | — | pilot / external-drone perspective, camera presets |
| `theShoot` | theVerbs | P | — | — | — | aim + discharge weapons (infantry and ship) |
| `theSpace` | theSolarSystem | P | — | — | — | the medium you fly (the dark, gravity, scale) |
| `theStanding` | theDescent | P | — | — | yes | you stand on real ground, witnessed by contact |
| `theState` | theLoop | P | — | — | yes | what ticks |
| `theStory` | — | H | — | — | yes | the seed / the timeline |
| `theTree` | theGarden | P | — | — | yes | the Tree of Knowledge |
| `theTreeForm` | theTree | P | — | — | yes | grown from one genome |
| `theTruth` | theSeed | P | — | — | — | every fact reaches physics; the world cannot lie |
| `theVerbs` | theStory | P | — | — | yes | how you act -- verb over nouns |
| `theWarpDrive` | theShip | P | — | — | — | fold travel; VCM / WTM configuration |
| `theWorthPlaying` | theMeaning | H | — | — | — | is it a game worth playing |

## SCENE WITHOUT TERM — renders but is not declared (29)

These are the grown story tree: instances (`a…`) and membranes the design vocabulary never named. They are not errors — they are what `story/grow.py` actually produced.

`aActiveInterior` · `aBlueWorld` · `aHuman` · `aNitrogenAtmosphere` · `aRockyPlanet` · `aSaltOcean` · `aSteppeBiomes` · `aTerraceMine` · `aTerrain` · `aYellowStar` · `theAnkle` · `theBreath` · `theClock` · `theCloud` · `theCooling` · `theEmptying` · `theEye` · `theGalaxy` · `theGrip` · `theHand` · `theHorizon` · `theHuman` · `theHumanClock` · `theLoad` · `theRockyPlanet` · `theSkin` · `theStance` · `theSweep` · `theZero`

## WHAT THIS MEANS

The declared set is the game's **design language** — `theShip`, `theVerbs`, `theMeaning`, `theWarpDrive`. The renderable set is the **grown world** — `aBlueWorld`, `theCooling`, `theSweep`. Both are legitimate; they are simply not the same list.

**`scene_terms()` must keep returning only what renders.** Unioning the two would make the viewer's sidebar offer 59 membranes, 46 of which return `None` when clicked — the specification cited as proof. `splat_appearance.term_inventory()` counts the gap instead, so it is visible without being claimed.

**Of the 46, 19 already appear in `engine_state.py`** — they have a place in the engine's state model but no geometry. That is where a scene author would start.

---

## PLANAR MEMBRANES — 2D BY DESIGN, NOT BY DEFECT

The orbit proof measures parallax, and a **billboard** and a genuinely **planar** membrane look
identical to it: neither changes when the camera moves. They want opposite responses, so the
buffer's own extent is used to tell them apart — a plane has ~zero spread along one axis, which is
a fact about the geometry rather than about the render.

**Six of the 42 are planar**, and the axes are internally consistent:

| term | flat axis | what it is |
|---|---|---|
| `theAnkle` | y | sagittal plane — the side view |
| `theGrip` | y | sagittal plane |
| `theLoad` | y | sagittal plane |
| `theThrust` | y | sagittal plane |
| `theBalance` | **x** | **frontal** plane — the front view |
| `theZero` | x | the seed: r = 0, a point, so every extent is zero |

`theBalance` is the case that forced the distinction, and its own `emit()` states the design:

> *"+Y is the body's LEFT and Z is up; **X is zero everywhere, because this membrane IS the
> frontal plane and drawing depth into it would be drawing the parent's chapter again.**"*

It is the frontal-plane view of walking — lateral sway, pelvic obliquity, the capture point
reaching sideways — and depth belongs to its parent's sagittal chapter. The four `theAnkle`-family
membranes are the mirror case: sagittal views with the lateral axis collapsed.

**The falsifier did not fire.** It asked whether `story.md` describes a 3D concept while `emit()`
produces a plane — a bug wearing a design's clothes. The opposite is true: the concept *is* a
plane, the code says so before it draws, and the reason given (do not redraw the parent's chapter)
is the tree's own composition rule. Reporting these as "UNVERIFIED (billboard?)" was the
instrument calling a correct design a defect.

---

## AMENDMENT — FIVE PLACEHOLDERS ADDED (and they are still gaps)

`theSeed`, `theShip`, `theDescent`, `theGarden`, `theFlight` now have `story/` chapters that
**draw but do not derive**. The counts move:

| | before | after |
|---|---:|---:|
| renderable | 42 | **47** |
| declared but not renderable | 46 | **41** |
| in both | 13 | **18** |

**Do not read the five as closed.** Each publishes `placeholder: true` in its own `numbers.json`
and says so in its `story.md`. What they claim is only that their **extent** tracks their parent's
published `extent_m` by one declared factor — the slider test, and nothing else. They claim nothing
about what the term *is*: no material, no law reaching them from the parent, no prediction they
were not fitted to.

    A PLACEHOLDER THAT ANNOUNCES ITSELF IS HONEST.
    ONE THAT DOES NOT IS THE SPECIFICATION CITED AS PROOF.

**The parents are substituted, and declared.** `terms_data.py` names `theStory` and `aPlanet` as
parents; neither is a node of the grown tree. Each stub is placed under the nearest real ancestor
and the substitution is written into its own `story.md` rather than made silently. `theFlight`'s
declared parent is `theShip` — itself a placeholder — so it is parented to `theSolarSystem`
instead: **a stub may not be another stub's parent, or the tree grows on nothing.**

The honest gap is therefore still **46**: 41 with no code at all, plus these 5 with geometry and
no law.
