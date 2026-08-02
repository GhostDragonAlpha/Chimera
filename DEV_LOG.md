# Chimera — Dev Log

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> A running record of development: what changed, **why**, the commit, and its status. Newest first.
> Kept by the working agent, appended every session. Not a substitute for the git history — this is
> the *narrative* of the build, so a human (or a future agent) can read the arc without spelunking diffs.
> Status legend: **DONE** (shipped) · **VERIFIED** (shipped + proven, e.g. dyad/test) · **WIP** · **HELD**.

---

## 2026-07-26 — the renderer, 22× faster (1.6 → 36 fps), profiled end to end

**The through-line:** the operator's mandate was *"this has to render faster than anything else."* Attacked
it the project way — MEASURE first, then cut the biggest number — through five measured levers, each verified
(marker test for inside-out, dyad for appearance, pixel-diff for correctness). Baseline aPlanet @1152x864
was **1.6 fps**; it is now **36 fps** (event-timed 43). The live viewer moved to **1920x1080** and streams a
clean blue marble.

### The five levers (each committed, each measured)
1. **Small opaque grains** (`6106e94`, **VERIFIED** dyad 0.8) — the wall was OVERDRAW: aPlanet grains projected
   to ~42px over 32px tiles => ~26 splats stacked per pixel (~400x the area needed for coverage). SIZE 9->3.5,
   alpha 0.5->0.92, count 26k->40k. Overdraw ~8x down; colours recalibrated per-channel (err 0). 1.6 -> 6.6 fps.
2. **GPU tile binning** (`e5e6fed`, **VERIFIED** pixel-diff 0) — the 41ms/frame CPU sort existed only because
   numba-cuda has no GPU sort. Installed `cupy-cuda12x` (RTX 4090, CUDA 12.8); `_build_tiles_gpu` does the same
   (tile,depth) radix sort on-device, wrapping numba arrays zero-copy via `__cuda_array_interface__`. Deletes
   the sort AND 3 downloads + 2 uploads. 6.6 -> 11.9 fps.
3. **Back-face culling** (`380f96f`, **VERIFIED** dyad 0.8) — the opaque surface still let its FAR side bleed
   through (alpha 0.92 + Gaussian falloff never fully saturates), so **67% of grains were hidden geometry** the
   pipeline still paid for (the operator's "light filtering through overlaps"). Grains carry an optional normal
   (cols 21-23); `_project` culls any facing away BEFORE bin/gather/composite. Gain re-measured with culling on
   (over-accum 3.0x->2.4x). 11.9 -> 14.1 fps.
4. **Composite writes uint8 directly** (`dd0f0f8`, **VERIFIED** same colour mean) — the biggest surprise: event
   timing said 18fps but wall-clock was 14. The gap was **~40ms/frame of NUMPY** — `np.stack`+`np.clip`+`*255`
   +`astype` on a 3M-element float image + 3 separate downloads, every frame. Composite now clamps+scales
   in-kernel and writes one uint8 (h,w,3) image; host does ONE `copy_to_host`. **14 -> 36 fps.** (Lesson: profile
   the whole pipeline, not just the kernels — the host glue was the wall.)
5. **Live viewer @ 1920x1080** (16:9, ~36 fps; native 2560x1440 available at ~24 fps). Verified end-to-end: the
   render thread streams a clean blue marble (lit fraction 0.23).

### The honest dead-ends (recorded, per the method)
- **Shared-memory tiled composite** (the textbook 3DGS trick) and a **pre-gather packed composite** BOTH lost to
  the simple kernel. The compositor is **warp-divergence-bound**, not coalescing-bound: once some pixels in a warp
  hit the opaque early-out and others don't, the grain reads scatter and no prefetch/broadcast helps. Reverted.
- Remaining bottleneck (event-timed @1152): composite ~16.7ms (71%), binning ~4.3ms, rest ~2.3ms. The next real
  lever is fewer grains (LOD by distance) or attacking divergence — not more kernel cleverness.

### Open blemish
- A faint grain **lattice** shows in the ocean where the shell faces the camera dead-on (clean at the limb where
  foreshortening overlaps grains). Subtle, dyad still passes; a small size/count bump closes it at minor speed cost.

## 2026-07-25 — the appearance dyad, the live viewer, and "the story is the single knob"

**The through-line today:** make the visual proof loop real (a Gaussian-splat render judged by an
independent vision model), then make the operator's theory true — *to add game detail, you change only
the STORY* — on both the declaration layer and the render layer.

### Senses unified on the omni server; sound dyad built; AI ear MEASURED unreliable · *pending commit* · **VERIFIED**
- **#3 unify the senses:** `senses.py` — one Omni model on llama-server is the dyad's eye + ear + movie.
  `human_messenger` repointed from LM Studio to `senses` (omni); the appearance dyad is consistent at ~0.8
  over 4 runs (one 0.5 outlier). LM Studio is freed for the operator's dev agent. `serve_senses.py` launches
  it; the `reload` tool now refreshes the perception + sound modules live (no restart).
- **#1 the sound dyad:** `sound_messenger.py` (the ear twin of human_messenger) — sonify → hear → align →
  verdict; operator `human_override` authoritative. The redo-loop fired for real: theStar's first synthesis
  leaked a hiss; fixed with a 170 Hz low-pass.
- **AI ear MEASURED unreliable (the honest result):** the ear hallucinated a "high-pitched hum" in theStar's
  sonification — which is measured **100% below 170 Hz, centroid 30 Hz** (a pure rumble), 3× identically. So
  the AI ear can't be a verdict gate → the **OPERATOR is the primary/authoritative ear**, the AI a logged
  second opinion. `SOUND_DESIGN.md` §2 amended. (Vision is fine; the weakness is llama.cpp's experimental audio.)
- **Built (activates on next restart):** (a) the eye now WATCHES the MOVIE — `human_messenger.watch` via
  `senses.watch`; the engine judges `[begin, end]` as an ordered sequence (tested PASS 0.8, the eye read the
  unfolding). (b) `Engine.hear` + the `hear` MCP tool wire the sound dyad in, OPERATOR-primary: `hear(term,
  reading, aligns)` is authoritative (tested → PASS 1.0); bare `hear(term)` runs the AI ear but logs it as
  untrusted (tested → the hallucination, clearly flagged, never a gate). Sound is ADDITIVE — it does not block `prove`.

### AI ear + Omni "all senses" proven via llama-server; `sonify.py` built · `eac95fc` · **VERIFIED**
- The audio dyad's ear works — but through **llama-server direct, not LM Studio**. Chased it down: qwen2-audio
  had no audio encoder downloaded at all (deaf, hallucinated from the prompt); qwen2.5-omni's `mmproj-F32`
  HAS the audio tower (`clip.has_audio_encoder`); but LM Studio loads it for VISION only (never wires audio —
  a known llama.cpp manual-load gap). `llama-server --mmproj --no-mmproj-offload` runs `init_audio` and hears.
- **ONE Omni model = eye + ear + movie:** nailed the marble (vision), heard `theStar`'s sonification as
  *"a deep, rumbling bass"* (audio, matches the physics), and read an ordered 2-frame sequence as video with a
  transition (→ the appearance dyad can judge the MOVIE, not just the end still). Quality is "experimental" →
  **HYBRID** design confirmed (AI advisory ear/eye, operator authoritative).
- `sonify.py` built (twin of `splat_appearance`): matter→pressure, deterministic, CPU. `theStar` (rumble +
  convective hum) passes the ear; `aPlanet` (wind + ocean) needs synthesis tuning — the redo-loop, for sound.
- Serving: a dedicated `llama-server` on `127.0.0.1:1235` (omni GGUF on GPU, 5.3 GB projector on CPU).

### Sound system DESIGNED — matter's second projection · `1ca2166` · **DESIGN**
- `ChimeraEngine/SOUND_DESIGN.md`: the full architecture, mirroring the appearance system so it "sits right
  in" — `sonify(term)` (matter→pressure, the twin of `splat_appearance`; deterministic; CPU, no GPU; on the
  same movie timeline), a HUMAN-ONLY dyad (`sound_messenger`; no audio-recognition AI, so the operator is the
  sole ear — the permanent `human_override`), an `AUDITORY MESSENGER` gate, `compose_sound` (the music of the
  spheres from proven children's orbital periods), and an audio channel in the live viewer.
- Not built. First PoC proposed: sonify `theStar` → serve to `/live` → the operator hears + rules.

### Session restarted → engine at 59 terms, four terms re-proven through the boundary · **VERIFIED**
- The operator restarted the session; the fresh `chimera-engine` server loaded today's code (the `reload`
  tool is present, `_reconcile` grew the LIVE tree to 59 terms, all five proofs preserved — the reconcile
  survived a real restart, not just a test).
- Re-rendered + re-`prove`d all four through the MCP tools — boundary crossed, each dyad on its current
  (good / composed) render: **aPlanet 0.950, theStar 0.850, thePlanets 1.000, theSolarSystem 1.000
  (composed — the vision model saw the real marble on an orbit)**. The ledger is now honest (aPlanet's
  stale 0.100 blob record is gone; theSolarSystem now records the composed render, not the old hand-drawn).
- Engine NEXT: `theTerrain` (setting-first under aPlanet); the 15 new terms await proving.

### OpenLevel — hot-reload the world into the running engine (`reload` tool) · `539aa0e` · **DONE / ACTIVE**
- The MCP server holds ONE `Engine` built at session start, so a changed *story* (new terms) and the
  engine's own code do not hot-load — only scenes do (they `importlib.reload` per render). The operator
  named this exactly: it is Unreal's `OpenLevel`, and we're building the equivalent.
- `Engine.reload_world()` + the `reload` MCP tool: re-read the story (`terms_data`), rebuild the seed
  hierarchy, reconcile the ledger (proofs kept), reload the scene renderer. *Verified:* reloads to 59
  terms, all 5 proofs preserved, the 15 new terms live.
- **Limit (honest):** changes to the engine's OWN logic (`engine_state.py`) still need one session
  restart — you cannot hot-swap the running class. So ONE more manual restart activates all of today's
  engine code (incl. `reload` itself); after that, story/scene changes load via `reload`, no restart.
- I cannot restart the server from inside the session (Claude Code launches it from `.mcp.json`) — that
  one restart is the operator's. Then re-prove the terms via the MCP tools (refreshes the stale ledger
  dyads — e.g. aPlanet's record is still the old-blob 0.100 FAIL until re-rendered through the engine).

### THE_STORY.md grown to the full feature spec — mining, farming, controls, archive · `670905f` · **DONE**
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
- **Prove the 15 new terms** — theMining, theFarming (+3 farms), the 7 theShip systems, theShoot/theMelee/
  theEVA. Engine NEXT points at `theTerrain` (setting-first). Each is a full frame→question→classify→
  render→prove cycle; many need a scene authored in `splat_appearance` (or composition from children).
- **Scale-dependent calibration** — composed children (e.g. a shrunk star) over/under-accumulate; tune.

### Discussion queue (operator-raised, deferred — "let's discuss after")
- **Sound — DESIGNED** (`ChimeraEngine/SOUND_DESIGN.md`). Matter's second projection; `sonify` twin;
  HUMAN-ONLY dyad; music-of-the-spheres composition. Next: build the theStar PoC + the operator listens.
- **Film-grammar for detail.** Research/contemplate movie-editing & script-editing concepts (timelines,
  scenes, cuts, shot lists, script beats) as a way to author game detail — a natural fit with the
  splat-MOVIE + the story-as-timeline model.
- **Movie generation as synthetic data.** Actual video/movie generation could produce artificial training
  data. Constraint the operator set: EVERY model must be able to use the system — it should NOT require
  specializing in movie generation (though some specialization may prove unavoidable — open question).
- **"OpenLevel" is the frame.** We are building the equivalent of an engine loading a new level/world;
  today's `reload` is the first piece. Keep designing toward a clean load-the-world operation.
