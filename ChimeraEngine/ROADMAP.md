# CHIMERA ENGINE — the road to a game

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
