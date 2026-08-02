# PHASE 0: CREATIVE RESEARCH — DEEP SPACE TRADER

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

Before building anything, study everything. This phase establishes the visual, emotional, and sensory foundation for the entire game. Do not skip. Do not rush. Understanding comes before creation.

---

## RESEARCH CYCLE 1: SPACE STATIONS

**Emotional Target:** Each station has a different feeling. Research them separately.

### Orbital_Hub_7 — Neutral Trading Hub
Search and gather:
- Use **playwright** to search "ISS interior exterior photos NASA"
- Search "functional industrial architecture trading post"
- Search "busy marketplace concept art"
- Search "neutral welcoming lighting design"
- Download 30+ images to `research/stations/orbital_hub_7/`

Extract patterns:
- What makes a space feel "neutral" rather than hostile or friendly?
- What makes a space feel "functional" rather than luxurious or decrepit?
- How do real trading posts handle traffic flow?
- What's the color language of neutrality?

### Ares_Market_Central — Busy Commercial Hub
Search and gather:
- Search "bustling market concept art sci-fi"
- Search "commercial district architecture photography"
- Search "warm inviting public space design"
- Download 30+ images to `research/stations/ares_market_central/`

Extract patterns:
- What makes a space feel "busy" even when empty?
- What makes a space feel "commercial" rather than residential or military?
- How do real markets use lighting to guide people?
- What's the sound of commerce?

### Shadow_Reef — Hidden Pirate Outpost
Search and gather:
- Search "abandoned military bunker photography"
- Search "pirate hideout concept art"
- Search "salvaged scrap metal structure"
- Search "hidden cave base sci-fi"
- Search "dangerous flickering lighting horror"
- Download 30+ images to `research/stations/shadow_reef/`

Extract patterns:
- What makes a space feel "hidden"?
- What makes a space feel "dangerous" but not suicidal?
- How do real pirates/outlaws modify existing structures?
- What's the lighting language of "you shouldn't be here"?

---

## RESEARCH CYCLE 2: SPACESHIPS

**Emotional Target:** The player's ship should feel like home. Pirate ships should feel like threats.

### Trader_Vessel_Alpha — The Player's Home
Search and gather:
- Search "utilitarian spaceship concept art"
- Search "lived-in spacecraft interior The Expanse"
- Search "functional cockpit design"
- Search "worn but maintained vehicle"
- Download 30+ images to `research/ships/trader_vessel/`

Extract patterns:
- What makes a ship feel "lived-in"?
- What makes a ship feel "yours"?
- How do real pilots personalize their aircraft?
- Where does wear naturally accumulate on a frequently-used vehicle?

### Pirate Ships — Threatening and Scrappy
Search and gather:
- Search "scrap-built spacecraft concept art"
- Search "modified stolen vehicle"
- Search "aggressive angular ship design"
- Search "spike and jagged silhouette"
- Download 30+ images to `research/ships/pirate/`

Extract patterns:
- What shapes read as "aggressive" vs "defensive"?
- What makes a ship look "stolen and modified"?
- How do you communicate danger through silhouette alone?

---

## RESEARCH CYCLE 3: CELESTIAL BODIES

### Titan — Gas Giant
Search and gather:
- Search "Jupiter NASA high resolution"
- Search "Saturn rings Cassini photography"
- Search "gas giant concept art cinematic"
- Search "planet from orbit lighting reference"
- Download 30+ images to `research/planets/titan/`

Extract patterns:
- What makes a gas giant feel "vast"?
- How do rings catch light?
- What colors occur naturally in gas giants?
- How does a planet look from a station in orbit?

### Ares-Prime — Terrestrial World
Search and gather:
- Search "Mars surface NASA photography"
- Search "Earth from space photography"
- Search "terrestrial planet concept art"
- Search "cratered moon surface"
- Download 30+ images to `research/planets/ares_prime/`

Extract patterns:
- What makes a planet feel "solid" vs "gaseous"?
- How do craters and mountains read at different distances?
- What's the color palette of a habitable world?

---

## RESEARCH CYCLE 4: DEEP SPACE ENVIRONMENT

**Emotional Target:** The void should feel beautiful, lonely, and slightly terrifying.

Search and gather:
- Search "Hubble deep field photography"
- Search "nebula NASA high resolution"
- Search "starfield from space photography"
- Search "deep space void concept art"
- Search "sublime terrifying beautiful space art"
- Download 50+ images to `research/environment/deep_space/`

Extract patterns:
- What makes space feel "infinite"?
- What makes space feel "cold"?
- What makes space feel "beautiful" despite being empty?
- How do real nebulae create color?
- How do stars cluster vs spread?
- What's the difference between "lonely space" and "peaceful space"?

---

## RESEARCH CYCLE 5: DEBRIS AND DESTRUCTION

**Emotional Target:** Debris tells the story of what happened here.

Search and gather:
- Search "shipwreck photography underwater"
- Search "junkyard aerial photography"
- Search "post-war destruction photography"
- Search "space debris field concept art"
- Search "floating debris zero-G reference"
- Download 40+ images to `research/environment/debris/`

Extract patterns:
- How do objects break in different materials?
- How does debris cluster in zero-G?
- What makes debris feel "recent" vs "ancient"?
- How does lighting interact with irregular surfaces?
- What story does the debris tell about what happened?

---

## RESEARCH CYCLE 6: LIGHTING MOODS

**Emotional Target:** Master the six emotional lighting states.

For each emotion, find 20+ references:

### Lonely Lighting
- Search "single light source photography"
- Search "isolated light in darkness"
- Search "Edward Hopper lighting analysis"

### Hopeful Lighting
- Search "single warm light in cold scene"
- Search "beacon of hope photography"
- Search "light at the end of the tunnel"

### Dangerous Lighting
- Search "horror movie lighting analysis"
- Search "flickering emergency light"
- Search "red warning light industrial"

### Safe Lighting
- Search "warm cozy interior lighting"
- Search "welcoming public space lighting"
- Search "home lighting design photography"

### Awesome Lighting
- Search "cathedral light beams photography"
- Search "dramatic volumetric lighting"
- Search "sublime landscape lighting"

### Mysterious Lighting
- Search "chiaroscuro painting analysis"
- Search "partially lit corridor"
- Search "colored shadow photography"

Save all to `research/lighting/[emotion]/`

---

## RESEARCH CYCLE 7: SOUND REFERENCES

**Emotional Target:** Sound is half the experience.

Search and gather:
- Search "NASA space audio recordings"
- Search "space station ambient sound"
- Search "industrial hum sound reference"
- Search "metal stress creaking sound"
- Search "electronic beacon ping sound"
- Search "silence in film sound design"

For each station, ship, and environment, find or note reference sounds. Build a sound mood board for each location.

Save references to `research/sound/[location]/`

---

## RESEARCH CYCLE 8: CROSS-DOMAIN INSPIRATION

Don't limit to game art. Pull from everywhere.

- **Architecture:** Search "brutalist architecture photography", "sacred space design", "public transit hub design"
- **Music:** Find tracks that evoke "lonely", "cold", "hopeful", "dangerous", "awesome", "mysterious"
- **Poetry:** Find poems about isolation, the sublime, hope against odds, the terror of infinity
- **Painting:** Search "caspar david friedrich wanderer", "turner seascapes", "rothko color fields"
- **Film:** Study lighting in Alien, 2001, Interstellar, Solaris, Sunshine
- **Theater:** Research how stage lighting creates mood with limited resources

Save all to `research/cross_domain/[category]/`

---

## AFTER ALL RESEARCH CYCLES

### Step 1: Pattern Summary Documents
For each cycle, create a pattern summary document in `research/[category]/patterns.md` with:
- Emotional target
- Shape language findings
- Color language findings
- Light language findings
- Texture language findings
- Sound language findings
- Key insights (3-5 things you now understand that you didn't before)

### Step 2: Mood Boards
Pick the 10 strongest images per subject. Arrange them. Note what they have in common.

### Step 3: Record Everything in Graphify
Each pattern is a node. Each reference is an edge. Each insight is a mutation.

### Step 4: Proceed to Phase 1
Only then, proceed to Phase 1 of the master workflow. You now understand what you're building. You've done the apprenticeship. The marble is ready.
