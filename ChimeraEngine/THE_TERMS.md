# THE TERMS — everything the game must prove, distilled from the primary timeline

> The complete list of terms to PROVE for Chimera, each distilled from a beat of the story
> (`Chimera/docs/THE_STORY.md` — the primary timeline, the seed). Every term is a membrane proven
> through the engine (`ChimeraEngine/MCP_ENGINE.md`): **PHYSICS** terms are measured, **THE HUMAN**
> terms are decided by the operator. This is the **source for the engine's hierarchy**
> (`engine_state._SEED_HIERARCHY`) — shape it here, then load it into the engine.
>
> Legend: `[P]` physics · `[H]` the human · `✓` proven through the engine · `~` built/measured but
> not yet proven through it · `○` open · dates: 2026-07-25.

---

## I. The Seed — *"in the beginning, a number… this universe is true"*
- **theSeed** `[P]` — the number + the laws that unfold the world
  - theDeterminism `[P] ~` — same seed → same world, bit-identical
  - theLaws `[P] ○` — the trained physics the seed runs under (gravity, accretion, thermo, growth)
  - theTruth `[P] ○` — every fact reaches physics; the world cannot lie

## II. Arrival — *"you arrive… thrust… the solar system is the first room"*
- **theSolarSystem** `[P] ✓` — the setting you fly
  - theStar `[P] ✓` — the yellow hearth
  - thePlanets `[P] ○` — the worlds in orbit
  - theSpace `[P] ○` — the medium you fly (the dark, gravity, scale)
  - theDensityClock `[P] ~` — time leans with mass and speed
- **theShip** `[P] ○` — the player's vessel; the cold start

## III. Descent — *"orbit → atmosphere → ground → grain… stand on real ground, dig, scan"*
- **theDescent** `[P] ○` — traversing the scales (the membrane onion; LOD of meaning)
- **aPlanet** `[P] ~` — the world you fall toward
  - theTerrain `[P] ~` — the whole-sphere surface
  - theAtmosphere `[P] ○` — air, sky, weather
  - theOcean `[P] ○` — the water
  - theBiomes `[P] ~` — climate + life bands
  - theGround `[P] ~` — the surface underfoot (matter under boots)
  - theInterior `[P] ~` — layers, ore, caves
- **theStanding** `[P] ~` — you stand on real ground, witnessed by contact
- **theBlackHole** `[P] ~` — the density clock's ceiling; the hole you can't see into

## IV. The Garden — *"a garden… grow a forest… the Tree of Knowledge"*
- **theGarden** `[P] ~` — the lush living place (`lushEden`); whether it is *paradise* is `[H]`
  - theEcosystem `[P] ○` — life cascading from physics
  - theTree `[P] ~` — the Tree of Knowledge; its *meaning* is `[H]`
    - theTreeForm `[P] ~` — grown from one genome
    - theFruit `[H] ○` — knowledge of good and evil
  - thePlanting `[P] ~` — the tree grows into the surface (the seam)

## V. The Gift (meaning) — *"the knowledge of good and evil… you decide what things mean"*
- **theMeaning** `[H]` — deciding what things mean; the gift, your terminal
  - theParadise `[H] ○` — does Eden read as paradise
  - theChoice `[H] ○` — good and evil; the human decides
  - theWorthPlaying `[H] ○` — is it a game worth playing (structure proven; the fun is yours)
  - theExperience `[H] ○` — the felt whole; understood, not won

## Cross-cutting — how you act, and the loop that holds it
*(The story's verbs and the engine that runs them — they thread every movement above.)*
- **theVerbs** `[P] ~` — verb over nouns
  - theThrust `[P] ~` · theDig `[P] ~` · theBalance `[P] ~` · theGrow `[P] ~` · theScan `[P] ○` · theNavigate `[P] ○`
- **theLoop** `[P] ~` — world + player + input → verbs → state → tick
  - thePlayer `[P] ~` — the character; presence before action (the Dot)
  - theInput `[P] ○` — keystrokes → verb dials
  - theState `[P] ~` — what ticks
  - thePersistence `[P] ○` — same seed, same world, forever (save / return)

---

## The tree (setting-first — the shape the engine will hold)

```
theStory ◆ (the seed / timeline — decided)
├─ theSeed  → theDeterminism · theLaws · theTruth
├─ theSolarSystem ✓
│  ├─ theStar ✓
│  ├─ thePlanets → aPlanet
│  │   ├─ theTerrain · theAtmosphere · theOcean · theBiomes · theGround · theInterior
│  │   └─ theGarden → theEcosystem · theTree (→ theTreeForm · theFruit) · thePlanting
│  ├─ theSpace
│  └─ theDensityClock
├─ theShip
├─ theDescent → theStanding · theBlackHole
├─ theVerbs → theThrust · theDig · theBalance · theGrow · theScan · theNavigate
├─ theLoop → thePlayer · theInput · theState · thePersistence
└─ theMeaning → theParadise · theChoice · theWorthPlaying · theExperience
```

## Counts
~45 terms. **Physics:** ~34 (measured). **The human:** ~7 (paradise, meaning, choice, fruit,
worth-playing, experience). **Proven through the engine:** 2 (theSolarSystem, theStar). The rest
is the road — and most physics terms already have built substrate (`~`) to prove *through* the
engine rather than build from scratch.

## Honest note
This is a **distillation** — a design act over the timeline. The story grounds *what* the terms
are; their granularity and grouping carry a little taste (e.g., whether `theGarden` sits under
`aPlanet` spatially or as its own movement narratively). Shape it — add, cut, regroup — before it
is loaded into `engine_state._SEED_HIERARCHY` as the working hierarchy.
