# SPIACE Phase 8 + Tracks D/E — The Next Leap

## Context: What is Already Built (Updated by bionic)

You are the lead developer on SPIACE, a first-principles space RPG engine. The following is complete and verified:

**Phases 0-7:** Full WebGPU splat renderer, GPU Barnes-Hut N-body with universal kernel translation layer (gravity + light + electromagnetism via .chimera DSL), Lorentz force post-tree correction (F = q(v×B)), energy/thermal/cyclotron falsifier verification all green.

**All Tracks A-E groundwork:**
- **Track A1:** Planet terrain → splats connection (300 Fibonacci-lattice surface splats, FBM noise elevation, height-band coloring)
- **Track A2:** Real Earth DEM option via `from_topo_grid()`
- **Tracks C1/C2:** Picking + highlight
- **Tracks B/T:** Scale-relative flight camera + LOD of time

**The file you will modify:** `engine/spiace_phase6.html` — single standalone HTML, no external dependencies, WebGPU. (~2736 lines)

**Test harness:** `engine/test_phase6.py` — Playwright headed-mode, all assertions passing (kernel DSL verify, 500 particles, tree stats, EM fields, thermal equilibrium <15%, energy drift <1%, deflection >10m, flight bounds, LOD witness <1%, renderer check, visible splats >0).

**Key architecture:**
- Particles carry per-kernel quantities: mass, lum, charge
- Barnes-Hut tree aggregates one (center, quantity) pair per kernel per node (112 B/node: 64 base + 3×16 per kernel)
- Rendering: WebGPU Gaussian splats, CPU cull+bin+sort, GPU tile raster
- Planet: fixed anchor at 1 AU, R = 6.371e6 m, 300 terrain splats (fixed, exert gravity)
- Orbitals: ~199 bodies at 5e10–3.5e11 m from star, masses 1e10–1e12 kg, charges ±1e3–1e6 C
- B-field: uniform global field, toggleable, applied as post-tree Lorentz correction

---

## THE CONCEPTUAL OPPORTUNITY (Phase 8)

Your task is to extend the universal kernel translation layer with a **third physics kernel** that demonstrates the deepest insight from Phases 5-7:

### The Insight: All These Forces Share the Same Math

The steady-state heat equation ∇²T = −Q/κ has the SAME Green's function as gravity: 1/r potential. Temperature from a point heat source Q at distance r is:

    T(r) = Q / (4πκr)

This is structurally identical to gravitational potential Φ = −GM/r and electrostatic potential V = kQ/r. The Barnes-Hut tree doesn't care WHAT it aggregates — it only needs:
- A scalar quantity per particle
- An aggregate rule (weighted_sum for positive-only quantities)
- A far-field kernel function (inverse_squared for the FIELD, not the potential)

### What to Build: Heat Diffusion Steady-State Kernel

Add a `heat` kernel to the DSL that:
1. Each particle carries a `heat_source` value (Watts) — stars are huge sources, planets are sinks (they absorb and re-radiate)
2. The tree aggregates total heat per node + center-of-heat (mass-weighted? no — heat-weighted)
3. The far-field kernel computes temperature contribution: T = Q / (4πκ d²) ... wait, let me derive this properly.

Actually, the steady-state temperature from a point source in 3D satisfies ∇²T = −Qδ(r)/κ. The solution is T(r) = Q/(4πκr). The TEMPERATURE gradient (heat flux) is:

    ∇T = −Q/(4πκr²) r̂

So the "force-like" quantity is the temperature GRADIENT, which falls off as 1/r² — the same as gravity's acceleration. But we want to aggregate TEMPERATURE (a scalar field), not flux.

For the kernel translation:
- **quantity**: `heat_source` (Watts per particle)
- **aggregate**: `weighted_sum` (total Q = ΣQ_i, center = Q-weighted COM)
- **kernel_fn**: `potential_1r` (T = Q/(4πκd), not force — this is a field value, not an acceleration)
- **sign**: `attractive` (positive sources raise temperature)
- **coupling**: `ONE_OVER_FOUR_PI_KAPPA` where κ is thermal conductivity

Wait — but the tree traversal currently returns acceleration (vec3). We need to also return temperature as a scalar field. Currently, the GPU accumulator returns `acc: vec4f` where xyz = acceleration and w = irradiance (from the light kernel). We can extend this: add temperature accumulation alongside irradiance.

Actually, let me think about what's most impactful vs. most complex:

**Option A: Temperature as a scalar field (extends flux accumulator)**
- Add T accumulation to the tree traversal (like flux already works)
- Each particle's temperature is influenced by all heat sources via the tree
- Radiative equilibrium becomes self-consistent: particles heat from starlight AND from nearby hot bodies
- This creates emergent thermal behavior (hot orbitals warm their neighbors)

**Option B: Heat flux as a force-like quantity**
- Treat temperature gradient like acceleration
- Particles "flow" from hot to cold regions
- More novel, but less physically grounded for this context

I recommend Option A because:
1. It's verifiable (steady-state has known analytic solutions)
2. It connects directly to existing thermal physics (blackbody emission, radiative equilibrium)
3. It creates emergent behavior without new complexity in the tree
4. It proves the "universal kernel" insight: heat transport rides the same tree as gravity and EM

### Falsifiers (named before the run, per Rule 0):

**Falsifier 6:** Two point heat sources in isolation must produce temperature at a mid-point that matches the analytic superposition T = Q1/(4πκr1) + Q2/(4πκr2) within 2%.

**Falsifier 7:** Adding the heat kernel must not break energy conservation — total energy drift stays < 1% (heat is a field, not a force; it doesn't do work on particles).

**Falsifier 8:** The thermal equilibrium @1AU bin must remain within 15% of predicted T_eq (the existing falsifier still holds with the heat kernel active).

---

## TRACK D: INFINITE DETAIL (D1 + D2)

### D1: Port the Trained LOD Law to v2 Renderer

The law is already trained in `lod.py`:
```python
N = ρ · r_px²    # grains for a body of projected radius r_px
```
with ρ = 0.45, β = 2.5 from `lod.trained.json`.

What needs to happen:
1. The v1 renderer already composes LOD levels by switching between mip levels of the splat buffer
2. The v2 renderer (current) does NOT do LOD — every splat is rendered at full resolution regardless of distance
3. Port the LOD selection logic: per-frame, compute each body's projected radius in pixels, select the appropriate mip level from the pre-baked pyramid
4. The mip pyramid must be baked into the `.chsplat` format (or equivalent in the JS splat data)

**Falsifier:** At 3 scales (close, mid, far), the visible splat count per planet must match N = ρ·r_px² within 20%. The total grain work must be bounded by screen area (no blow-up when zooming in).

### D2: Surface Fracture

When a membrane's projected size exceeds its budget, fracture it into child patches and generate splats from the terrain function at the resolution the screen needs. Retreat → coalesce.

This is the "infinite detail" promise. The algorithm:
1. Each membrane has a `budget` (max splats it can contribute)
2. If projected size × density > budget, split into 4 child patches (quadrants in lat/lon)
3. Each child generates its own splats from the terrain function
4. When retreating, merge children back into parent

**Falsifier:** Flying toward a planet must smoothly increase splat count without popping. At maximum zoom, the local splat density must match the trained law.

---

## TRACK E: CHARACTER STANDING ON PLANET (The North Star)

**NORTH STAR:** A character stands on a planet and walks around, and you flew there from orbit without a loading screen.

### E1: Ground Query
`height_at(lat, lon)` from the PlanetOnion — cheap, exact, no rendering involved. Returns elevation + normal.

### E2: Character Controller
- Gravity toward membrane center (local "down")
- Up = local surface normal
- Walk on the height field with WASD in the local tangent plane
- Contact detection: raycast down from character position to terrain surface
- **Witness requirement:** contact must be measured, not asserted. Report the gap distance each frame.

### E3: Scale Handoff
Ship → orbit → descent → foot, with the camera's membrane depth driving the transition. The hard part is precision — at planetary scale, float32 loses sub-meter accuracy. The membrane-local frame (already built for Track B) solves this by re-centering coordinates at each membrane depth.

**Falsifier:** A character placed at rest on the surface must stay at rest (no sliding). Velocity must be exactly zero after 1 second of no input. Measured gap to surface must be < 0.01 m.

---

## YOUR TASK

Choose ONE of these three paths and execute it fully:

### Path 1: Phase 8 — Heat Diffusion Kernel (Recommended)
This is the purest expression of the "universal kernel" insight. It extends `kernel_dsl.py` with a new kernel declaration, regenerates all code regions via `--inject`, updates the HTML to accumulate temperature alongside irradiance, and adds falsifiers 6-8. The tree structure doesn't change — only the per-kernel fields grow by another 16 B/node (128 B total).

### Path 2: Track D1 — LOD Port
Mechanical but essential. Ports the trained `lod.py` law to the v2 renderer. Requires baking a mip pyramid into splat data and selecting levels per-frame based on projected radius.

### Path 3: Track E — Character Controller
The north star. Combines ground query, contact dynamics, and scale-precise local frames. Most visually satisfying but also the most complex.

**My recommendation:** Do Path 1 (Heat Kernel) first — it's a clean conceptual extension that proves the universal kernel vision, takes ~1 day, and has elegant falsifiers. Then hand off Path 3 (Character) to another agent session since it requires more interactive testing.

---

## CONSTRAINTS

- Single standalone HTML file — no external dependencies
- Non-headless Playwright testing only (`--enable-unsafe-webgpu`)
- `kernel_dsl.py --verify` must pass after any DSL changes
- All existing falsifiers (1-5) must remain green
- Rule 0 applies: state the theory, make a prediction, name the falsifier BEFORE running

## FILES TO MODIFY

- `engine/kernel_dsl.py` — add heat kernel declaration (Path 1)
- `engine/spiace_phase6.html` — temperature accumulation + HUD + falsifiers
- `engine/test_phase6.py` — new assertions for Phase 8

For Paths 2/3, the same HTML file is the target, but with different additions.

---

## WHAT SUCCESS LOOKS LIKE

After your work:
1. `python kernel_dsl.py --verify spiace_phase6.html` exits 0
2. `python test_phase6.py` passes ALL assertions including new Phase 8 ones
3. The HUD shows temperature stats alongside energy/charge
4. A new mode toggle enables/disables the heat kernel
5. Measured numbers are reported in the test output (not just pass/fail)

Document version target: 2.0 | Status target: Phases 0-8 + Tracks A1/A2/C1/C2/B/T complete
