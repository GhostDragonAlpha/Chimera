# CHIMERA ENGINE — the road to a game

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

> Written 2026-07-26, after the renderer stopped being the bottleneck (2560×1440 at ~190 fps,
> GPU ~5 ms of an 8.3 ms budget). This is the plan for turning a proven renderer into a thing
> you can fly through, inspect, and eventually stand on.
>
> **NORTH STAR: a character stands on a planet and walks around, and you flew there from orbit
> without a loading screen.** Everything below is ordered by how directly it serves that.

---

## 1. The thesis: don't copy Unreal's editor — Unreal doesn't have membranes

Unreal's viewport, outliner, gizmos and fly-speed slider all exist to help a human inspect a
**flat scene graph at one scale**. Chimera's world is not that. It is a **membrane hierarchy**,
where scale *is* the tree — and that hierarchy is already built (`core/membranes.py`). So the
editor primitives should be **membrane-native**, and most of them then come out for free:

| Unreal concept | Chimera's version | already exists? |
|---|---|---|
| Scene outliner | the membrane tree / the story's term hierarchy | **yes** — `Membrane.add/path` |
| Object address | `Membrane.path()` — the SERIAL is the address | **yes** |
| LOD level | `Membrane.depth()` — depth *is* level of detail | **yes** |
| Fly-speed slider | speed **derived** from the current membrane's extent — never a slider | no |
| "Which way is up" | up is the membrane's own normal (on a sphere there is no global +Z) | partly |
| Streaming / World Partition | coalesce / fracture across membrane depth | design exists |
| Time dilation, per-region tick | `Membrane.clock_rate()` / `tick()` | **yes**, unused |
| Blueprint interaction | `Verb` + `Gate` + `State` with `reachable()` | **yes**, unused |

**The point:** a scale-relative camera and membrane-path selection are *better* than Unreal's
equivalents for this world, and they are less work because the substrate is already there.

---

## 2. Honest inventory — what is actually built

**Solid, proven:**
- v2 WebGPU renderer: preprocess → GPU radix sort → tile raster, no host in the frame loop.
  Normalized surface splatting + depth window (opaque, order-independent, artifact-free).
- `lod.py` — the TRAINED pixel-budget law `N = ρ·r_px²` + mip pyramid, working in v1 composition.
- `PlanetOnion` — Earth-like spherical-harmonic terrain, layered, `truncate_lod(max_degree)`,
  `uplift()`, and `from_topo_grid()` to drop in **real Earth elevation data**.
- `Membrane` / `Port` / `Verb` / `Gate` — the hierarchy, addressing, depth, ports, gated verbs.
- The bake seam (`bake_splats.py`) — Python generates, the GPU renders, nothing per-frame in Python.
- The story → terms → engine pipeline, the dyad/proof gates.

**Missing (the actual work):**
- Terrain is not *rendered* — `PlanetOnion` exists but `aPlanet`'s splats are still fbm colour on a
  smooth sphere. **Nothing connects the two.** ← this is the single biggest gap.
- No detail *below* the base splat set: flying closer cannot reveal what was never generated.
- Camera is orbit-only. No flight, no scale-relative speed, no membrane traversal.
- No picking, no selection, no highlight, no orientation readout.
- No collision/contact, so nothing can stand on anything.

---

## 3. The tracks, in priority order

### TRACK A — **Make it Earth** (unblocks everything visual)
The gap is a single missing connection, and both ends already exist.

- **A1. Terrain → splats.** Sample `PlanetOnion.elevation_grid()` when building `aPlanet`: place
  each surface splat at `R + elevation`, and colour it from elevation + latitude (sea below sea
  level, beach/forest/rock/snow bands above, ice by latitude). Replaces the fbm-colour sphere with
  a real height field. *This alone makes it read as Earth.*
- **A2. Real Earth option.** `from_topo_grid()` with an ETOPO/SRTM grid → the actual Earth.
  Keep the generated one as the default (procedural worlds are the game); real Earth is the
  calibration reference — the dyad can be asked "is this Earth?" and answer honestly.
- **A3. Shading.** The star as a real light: `N·L` terminator, day/night, specular on water.
  Currently every splat is flat-lit, which is most of why it looks like a painted ball.

> **Framing note (added 2026-07-26):** see `THE_RELATIVE_ENGINE.md`. Track B is not camera code with
> a speed slider -- membrane depth already unifies LOD, local up, precision, camera speed AND clock
> rate into one number. Build B on the membrane clock, not beside it. It also adds a track:

### TRACK B — **Navigation** (what you asked for, and what makes it usable)
- **B1. Scale-relative flight.** 6-DoF fly camera where **speed = k · (distance to the nearest
  membrane surface)**, so it is automatically slow near a rock and fast between planets. No slider.
  This is the single highest-value control and it is ~half a day.
- **B2. Membrane traversal.** As you approach, the camera's "current membrane" descends the tree
  (system → planet → region → ground); as you retreat it ascends. Drives LOD, speed, and the
  local frame together, because they are the same number (`depth()`).
- **B3. Orientation HUD.** Current membrane path (the serial), altitude above the surface, speed
  in sensible units per scale, a local-up indicator, and an axis gizmo.
- **B4. Focus/frame.** Select a term → smoothly fly to a framing distance. The "F" key of any editor.

### TRACK C — **Inspection** (the human-workflow features)
- **C1. Picking.** Click → read back the splat id under the cursor → resolve to its **membrane
  path**. The renderer already has everything needed (one extra buffer written in the raster).
- **C2. Highlight.** Outline/tint the selected membrane's splats.
- **C3. Inspector panel.** For the picked membrane: its path, depth, ports, proof status, and the
  physics numbers behind it. This is where the engine's own proof model becomes *visible* —
  something no other engine has.
- **C4. Time controls.** `Membrane.clock_rate()` already exists; expose pause / step / rate so the
  movie timeline is scrubbable.

### TRACK D — **Infinite detail** (the "fly in and it keeps resolving" promise)
- **D1. Port the trained LOD to v2.** Bake the mip pyramid into the `.chsplat` format; select the
  level per body per frame. Mechanical — the law is already trained.
- **D2. Surface fracture.** When a membrane's projected size exceeds its budget, **fracture** it
  into child patches and generate each patch's splats from the terrain function at the resolution
  the screen needs. Retreat → coalesce. This is the real answer to "more and more detail", and it
  is the same coalesce/fracture the design has always called for.
- **D3. Streaming budget.** A fixed splat budget per frame; patches generated asynchronously and
  cached by membrane path.

### TRACK T — **Time is relative too** (nearly free; `membranes.py` already has the law)
- **T1. Per-membrane tick.** Advance each membrane at its own `tick()` rate: the planet underfoot at
  full rate, the outer system in coarse steps. **LOD of TIME** -- how a whole solar system stays
  simulated without costing everything. A handful of lines; the function exists.
- **T2. Derive camera speed from the clock.** `k · C_LIGHT / scale` -- deletes the speed slider (B1).
- **T3. Show it, then witness it.** Clock rate in the HUD beside the membrane path; then two clocks
  at different depths run N steps and the divergence REPORTED AS A NUMBER, per the project's rule.
- **T4. (Optional, gameplay) Time dilation as a mechanic.** Return from a deep gravity well and the
  world has moved on. Falls out of T1; no new physics.

### TRACK S — **The actuated membrane** (see `THE_ACTUATED_MEMBRANE.md`)
Matter that DOES something: an actuator attains a STATE and pushes at its PORT, in the frame of
whatever it is attached to. A thruster and a leg muscle are THE SAME OBJECT -- if they end up as
two systems the architecture was got wrong. Nothing is animated; a stumble is what happens when
the forces do not work out. Most of this exists already (Port, Verb/State, rig.py's one skeleton
for physics+flesh+render, mjcf.py's actuators, the trained brain, the gait witness); the gap is a
RUNTIME physics loop and expressing actuators through Membrane+Port.
- **S1-S3. Thruster first** -- free body, actuator at a port, then WITNESS BALANCE: fire off-axis
  and measure that angular acceleration matches tau = r x F (Centre of Thrust vs Centre of Gravity).
- **S4-S5. Joints, then muscle** -- the same Verb, producing torque about the joint it spans.
- **S6-S7. Nervous system in the loop, then terrain contact** -- stumble and recovery, unauthored.

### TRACK E — **Standing on it** (the north star)
- **E1. Ground query.** `height_at(lat, lon)` from the onion — cheap, exact, no rendering involved.
- **E2. Character controller.** Gravity toward the membrane centre, up = local normal, walk on the
  height field. The project's own rule applies: **contact must be witnessed**, not asserted.
- **E3. Scale handoff.** Ship → orbit → descent → foot, with the camera's membrane depth driving
  the transition. The hard part is precision, and the membrane-local frame already solves it.

---

## 4. What to do first — the recommended order

1. **A1 terrain → splats.** Biggest visual jump per unit work; both halves already exist.
2. **B1 scale-relative flight + B3 HUD.** Turns the viewer into something you can *explore*.
3. **C1/C2 picking + highlight.** Cheap once the renderer writes one more buffer.
4. **A3 lighting.** The other half of "looks real".
5. **D1 LOD port, then D2 fracture.** The detail promise, in the right order.
6. **E character.** Once there is terrain to stand on and a way to fly to it.

**Sequencing logic:** A1 and B1 are independent and both immediately visible — do them first.
Everything in D depends on A1 (there is no detail to stream until terrain exists). E depends on
both A1 and D2.

---

## 5. Non-goals (deliberately)

- **Not** rebuilding Unreal. No material graph, no blueprint VM, no asset browser. The generator
  *is* the content pipeline; the story *is* the level format.
- **Not** a general-purpose editor. Tools exist to serve this game and the human building it.
- **Not** chasing the last renderer artifact. The remaining faint limb line is colour-dependent
  (stronger over ocean than land), so it belongs to the atmosphere/lighting model — it will be
  addressed by A3, not by more rasterizer work.
