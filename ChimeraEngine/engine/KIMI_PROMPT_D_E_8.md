# SPIACE Tracks D/E — The Next Leap (Phase 9 Complete)

## Context: What is Already Built

You are the lead developer on SPIACE, a first-principles space RPG engine. The following is complete and verified:

**Phases 0-9:** Full WebGPU splat renderer, GPU Barnes-Hut N-body with universal kernel translation layer (5 kernels: gravity + light + electromagnetism + heat + acoustic via .chimera DSL), Lorentz force post-tree correction. All falsifiers green.

**All Tracks A-E groundwork:**
- **Track A1/A2:** Planet terrain → splats, real Earth DEM option
- **Tracks C1/C2:** Picking + highlight
- **Tracks B/T:** Scale-relative flight camera + LOD of time

**Key architecture:**
- 5 kernels in DSL: gravity (mass), light (lum), electromagnetism (charge), heat (heat_source), acoustic (pressure)
- Quantity packing: mass/lum/charge/heat in one `vec4f quants` buffer; acoustic has its own f32 `pressures` buffer; field outputs in `fields` vec4f. Total: 8 storage buffers = WebGPU default limit exactly.
- Node size: 144 B (64 base + 5×16 per kernel)
- Rendering: WebGPU Gaussian splats, CPU cull+bin+sort, GPU tile raster
- Planet: fixed anchor at 1 AU, R = 6.371e6 m, 300 terrain splats (fixed anchors)
- Orbitals: ~199 bodies, masses 1e10–1e12 kg, charges ±1e3–1e6 C
- B-field: uniform global field, toggleable, Lorentz post-tree correction
- GPU mode: 3.9 ms at 60 fps with all kernels active

**The file you will modify:** `engine/spiace_phase6.html` — single standalone HTML, no external dependencies, WebGPU. (~3100 lines)

**Test harness:** `engine/test_phase6.py` — Playwright headed-mode, all assertions passing (kernel DSL verify, 500 particles, tree stats, all 5 kernels present, thermal equilibrium <15%, energy drift <1%, deflection >10m, cyclotron check, flight bounds, LOD witness <1%, acoustic superposition <2%, pressure calibration <15%, renderer check, visible splats >0).

---

## TRACK D: INFINITE DETAIL (D1 + D2)

### D1: Port the Trained LOD Law to v2 Renderer

The law from `lod.py`:
```python
N = ρ · r_px²    # grains for a body of projected radius r_px
```
with ρ = 0.45, β = 2.5 from `lod.trained.json`.

What needs to happen:
1. The v2 renderer currently renders every splat at full resolution regardless of distance
2. Port LOD selection: per-frame, compute each body's projected radius in pixels, select the appropriate mip level
3. Bake a mip pyramid into the splat data (coarser levels = averaged colors)

**Falsifier:** At 3 scales (close, mid, far), visible splat count per planet matches N = ρ·r_px² within 20%. Total grain work bounded by screen area.

### D2: Surface Fracture

When a membrane's projected size exceeds its budget, fracture into child patches and generate splats from the terrain function at screen-needed resolution. Retreat → coalesce.

**Falsifier:** Flying toward a planet smoothly increases splat count without popping. At max zoom, local splat density matches the trained law.

---

## TRACK E: CHARACTER STANDING ON PLANET (The North Star)

**NORTH STAR:** A character stands on a planet and walks around, and you flew there from orbit without a loading screen.

### E1: Ground Query
`height_at(lat, lon)` from PlanetOnion — returns elevation + normal. Cheap, exact, no rendering.

### E2: Character Controller
- Gravity toward membrane center (local "down")
- Up = local surface normal
- Walk on height field with WASD in local tangent plane
- Contact detection: raycast down to terrain surface
- **Witness:** report gap distance each frame (< 0.01 m at rest)

### E3: Scale Handoff
Ship → orbit → descent → foot, membrane depth drives transition. Float32 precision solved by membrane-local frame re-centering (already built for Track B).

**Falsifier:** Character at rest on surface stays at rest (velocity = 0 after 1s no-input). Gap to surface < 0.01 m.

---

## RECOMMENDED ORDER

**Do Track E first** — it's the north star and the most visually impactful. It combines ground query, contact dynamics, and scale-precise local frames into something you can actually stand on. The physics is simple (gravity + surface normal + tangent-plane walking), but the precision challenge (float32 at planetary scales) makes it a genuine engineering problem worth solving well.

**Then Track D1/D2** — the infinite detail promise. More mechanical, benefits from having a character to walk around on.

---

## CONSTRAINTS

- Single standalone HTML file — no external dependencies
- Non-headless Playwright testing only (`--enable-unsafe-webgpu`)
- `kernel_dsl.py --verify` must pass after any DSL changes (none expected for D/E)
- All existing falsifiers (1-9) must remain green
- Rule 0 applies: state the theory, make a prediction, name the falsifier BEFORE running

## FILES TO MODIFY

- `engine/spiace_phase6.html` — character controller, ground query, LOD/fracture logic
- `engine/test_phase6.py` — new assertions for Tracks D/E
- (No changes to kernel_dsl.py expected)

## WHAT SUCCESS LOOKS LIKE

After your work:
1. `python kernel_dsl.py --verify spiace_phase6.html` exits 0
2. `python test_phase6.py` passes ALL assertions including new Track D/E ones
3. A character can be placed on the planet surface and stays there
4. WASD moves the character along the terrain in the local tangent plane
5. Measured numbers reported in test output (gap distance, velocity at rest, LOD counts)

Document version target: 2.2 | Status target: Phases 0-9 + Tracks A1/A2/C1/C2/B/T/D/E complete
