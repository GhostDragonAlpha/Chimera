# Chimera — Dev Log

> A running record of development: what changed, **why**, the commit, and its status. Newest first.
> Kept by the working agent, appended every session. Not a substitute for the git history — this is
> the *narrative* of the build, so a human (or a future agent) can read the arc without spelunking diffs.
> Status legend: **DONE** (shipped) · **VERIFIED** (shipped + proven, e.g. dyad/test) · **WIP** · **HELD**.

---

## 2026-07-25 — the appearance dyad, the live viewer, and "the story is the single knob"

**The through-line today:** make the visual proof loop real (a Gaussian-splat render judged by an
independent vision model), then make the operator's theory true — *to add game detail, you change only
the STORY* — on both the declaration layer and the render layer.

### THE_STORY.md grown to the full feature spec — mining, farming, controls, archive · *pending commit* · **DONE**
- Added 15 terms to the decomposition (`gen_decl.py`: 44 → 59): `theMining` (planetary excavation, under
  `theInterior`), `theFarming` → `thePlanetaryFarm`/`theLunarFarm`/`theOrbitalFarm` (under `theGarden`),
  seven `theShip` systems (`theFlight`/`theShipPower`/`theShipCombat`/`theShields`/`theWarpDrive`/
  `theShipView`/`theSalvage`), and `theShoot`/`theMelee`/`theEVA` under `theVerbs`.
- Folded the operator's **Frostbound Protocol** control narrative into a new "The Verbs in Play" section
  (their Acts I–VI preserved verbatim + woven-in additions: a SCAN verb, melee, visor vision modes,
  slide/mantle, tactical ping, bipod, ice traction/winch, flight-assist, station economy, survey/refine,
  photo/log) and wrote two new Acts — **VII Planetary Excavation** (`theMining`) and **VIII Cultivation**
  (`theFarming`, planetary/lunar/orbital).
- Established the **archive protocol**: a `chimera-archive` "Holding Bay" block (inert — `gen_decl.py`
  parses only `chimera-terms`). Features move there when set aside, kept + restorable, never deleted.
- *Why:* the operator's model — the story is the single source; adding features = editing the story.

### Composition wired in as the DEFAULT for composite terms · `beb33c2` · **VERIFIED**
- `theSolarSystem` now renders from its PROVEN children (real `theStar` + real `aPlanet` marble on orbits)
  everywhere — stills, live viewer, engine — not hand-drawn dots. Dyad held at **1.0**.
- *Why:* closes the operator's theory on the render layer — prove a planet, it appears on an orbit.

### Appearance from decomposition — foundation · `ebe9353` · **DONE**
- `splat_appearance.compose_buffer(term)` builds a parent's render from its children's own `scene_buffer`s
  (LOD-of-meaning; layout = structure, appearance derives from the child's matter — no aesthetic pass).

### Engine reconciles the story into a saved ledger · `a6a66a7` · **VERIFIED**
- **Bug fixed:** `_load` returned a saved `engine_state.json` verbatim and only built the tree from the
  story on FIRST creation, so a saved ledger froze the old hierarchy and story edits silently did nothing.
  Now `_reconcile`s — rebuild the shape from the story, carry saved proven/decided status, keep records.
- *Proven end-to-end:* add `theCore` under `theStar` → a fresh Engine on the real ledger shows it while
  the four membranes stay proven.

### Live interactive viewer in the gallery HTTP server · `f78283b` · **VERIFIED**
- `live_viewer.py` + `gallery.py` → `127.0.0.1:8765/live`: the term's settled splat scene rendered LIVE
  (one GPU render thread, MJPEG to an `<img>`), auto-spins (the movie plays), mouse-drag orbits, term
  buttons switch scenes. Renders only while a viewer is connected (frees the shared 4090 for LM Studio).
- *Verified in-browser:* aPlanet + theSolarSystem stream live, rotate, respond to drag.

### thePlanets + theSolarSystem: real scenes (were stale-proven blobs) · `87da561` · **VERIFIED**
- Rebuilt both from diffuse blobs into real scenes: thePlanets = six worlds in a hot→cold row;
  theSolarSystem = star + orbit rings + planets. Both dyad **1.0**.

### aPlanet renders as a real habitable world + stale-scene render fix · `027177d` · **VERIFIED**
- aPlanet was a blue dust blob (the star recipe misapplied). Rebuilt as a blue marble (ocean/land/ice +
  atmosphere) on a Fibonacci shell; calibrated a measured ~2× splat over-accumulation. Dyad **1.0** (a
  blind vision model read it as "the planet Earth with oceans, continents, ice caps").
- **Bug fixed:** `engine_state._appearance` now `importlib.reload`s the scene module each render — the
  long-lived MCP server was serving pre-edit code (kept re-rendering the old blob).

### Onboarding footer corrected · `b44caf9` · **DONE**
- The single onboarding (`ChimeraEngine/ONBOARDING.md`) footer claimed the splat-movie dyad was "not
  wired"; corrected — it was wired in `f2b0c88`.

### Open threads
- **Reload the `chimera-engine` MCP server** — all of today's engine/scene code is on disk but the running
  server holds pre-edit code; a session reload makes it live in the MCP tools, then re-`prove` the terms.
- **Sound** — design pending: a `sonify(term)` twin of `splat_appearance` (matter → pressure); dyad is
  HUMAN-ONLY (no audio-recognition AI). Generation unbuilt; do not improvise.
- **Scale-dependent calibration** — composed children (e.g. a shrunk star) over/under-accumulate; tune.
