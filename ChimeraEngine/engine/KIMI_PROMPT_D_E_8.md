# SPIACE Tracks D/E + Phase 9 — The Next Leap

## Context: What is Already Built (Updated by bionic + Kimi)

You are the lead developer on SPIACE, a first-principles space RPG engine. The following is complete and verified:

**Phases 0-8:** Full WebGPU splat renderer, GPU Barnes-Hut N-body with universal kernel translation layer (4 kernels: gravity + light + electromagnetism + heat via .chimera DSL), Lorentz force post-tree correction. All falsifiers green.

**All Tracks A-E groundwork:**
- **Track A1/A2:** Planet terrain → splats, real Earth DEM option
- **Tracks C1/C2:** Picking + highlight
- **Tracks B/T:** Scale-relative flight camera + LOD of time

**Key architecture:**
- 4 kernels in DSL: gravity (mass), light (lum), electromagnetism (charge), heat (heat_source)
- Node size: 128 B (64 base + 4×16 per kernel)
- Rendering: WebGPU Gaussian splats, CPU cull+bin+sort, GPU tile raster
- Planet: fixed anchor at 1 AU, R = 6.371e6 m, 300 terrain splats (fixed anchors)
- Orbitals: ~199 bodies, masses 1e10–1e12 kg, charges ±1e3–1e6 C
- B-field: uniform global field, toggleable, Lorentz post-tree correction
- GPU mode: 3.4 ms at 68 fps with all kernels active

**CRITICAL CONSTRAINT (discovered during Phase 8):**
WebGPU default `maxStorageBuffersPerShaderStage: 8`. The BH bind group already uses bindings 0-8 (9 storage buffers). Adding a fifth kernel as another binding would exceed this limit. **The solution:** pack mass/lum/charge/heat into one `vec4f` quantities buffer instead of separate per-kernel buffers. This frees 3 bindings and allows the 5th+ kernels to ride additional uniform or storage bindings that don't count against the storage limit (e.g., uniform buffers).

**The file you will modify:** `engine/spiace_phase6.html` — single standalone HTML, no external dependencies, WebGPU. (~2900 lines)

**Test harness:** `engine/test_phase6.py` — Playwright headed-mode, all assertions passing (kernel DSL verify, 500 particles, tree stats, all 4 kernels present, thermal equilibrium <15%, energy drift <1%, deflection >10m, cyclotron check, flight bounds, LOD witness <1%, renderer check, visible splats >0).

---

## THE CONCEPTUAL OPPORTUNITY (Phase 9 + Tracks D/E)

### The Architecture Question: How Many Trees?

The universal kernel insight proves that ONE tree can carry ANY number of position-only superposable fields. The cost is linear in the number of kernels (16 B/node each), not exponential. With the vec4f packing fix, we can have 5+ kernels on a single tree without hitting WebGPU binding limits.

This means: **one membrane = one tree = one traversal that computes gravity, EM, heat, and any future kernel simultaneously.** The Barnes-Hut approximation is not per-force — it's per-membrane. This is the scaling breakthrough.

### Phase 9: Quantity Packing + Fifth Kernel Demo

**What to build:**
1. Pack mass/lum/charge/heat into a single `vec4f` quantities buffer (binding 3 replaces bindings 3-6)
2. Add a fifth kernel to demonstrate the packing works — candidate: **acoustic pressure waves** (scalar field, inverse_squared kernel_fn like gravity but with repulsive sign for rarefaction)
   - quantity = "pressure" (Pa·m³, monopole strength)
   - aggregate = weighted_sum
   - kernel_fn = inverse_squared
   - sign = bipolar (compression vs rarefaction)
   - coupling = "ONE" (just 1/d² pressure amplitude)
3. Verify: acoustic superposition falsifier — two sources at midpoint match analytic sum within 2%

**Why this matters:** The packing proves the architecture scales. Each new kernel is a DSL declaration + 16 B/node, with no binding overhead. The tree becomes a true universal field solver.

### Track D: INFINITE DETAIL (D1 + D2)

#### D1: Port the Trained LOD Law to v2 Renderer

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

#### D2: Surface Fracture

When a membrane's projected size exceeds its budget, fracture into child patches and generate splats from the terrain function at screen-needed resolution. Retreat → coalesce.

**Falsifier:** Flying toward a planet smoothly increases splat count without popping. At max zoom, local splat density matches the trained law.

### Track E: CHARACTER STANDING ON PLANET (The North Star)

**NORTH STAR:** A character stands on a planet and walks around, and you flew there from orbit without a loading screen.

#### E1: Ground Query
`height_at(lat, lon)` from PlanetOnion — returns elevation + normal. Cheap, exact, no rendering.

#### E2: Character Controller
- Gravity toward membrane center (local "down")
- Up = local surface normal
- Walk on height field with WASD in local tangent plane
- Contact detection: raycast down to terrain surface
- **Witness:** report gap distance each frame (< 0.01 m at rest)

#### E3: Scale Handoff
Ship → orbit → descent → foot, membrane depth drives transition. Float32 precision solved by membrane-local frame re-centering (already built for Track B).

**Falsifier:** Character at rest on surface stays at rest (velocity = 0 after 1s no-input). Gap to surface < 0.01 m.

---

## RECOMMENDED ORDER

**Do Phase 9 first** (quantity packing + fifth kernel). It's a clean architectural proof that takes ~half a day, has clear falsifiers, and unblocks all future kernels without binding overhead. It also fixes the critical WebGPU limitation discovered in Phase 8.

**Then hand off Tracks D/E** to another session — they're more interactive/visual and benefit from fresh context.

---

## CONSTRAINTS

- Single standalone HTML file — no external dependencies
- Non-headless Playwright testing only (`--enable-unsafe-webgpu`)
- `kernel_dsl.py --verify` must pass after any DSL changes
- All existing falsifiers (1-8) must remain green
- **Storage buffer limit:** do NOT add more than 8 storage buffers per shader stage. Pack quantities into vec4f.
- Rule 0 applies: state the theory, make a prediction, name the falsifier BEFORE running

## FILES TO MODIFY

- `engine/kernel_dsl.py` — add fifth kernel, potentially restructure quantity packing
- `engine/spiace_phase6.html` — vec4f quantities buffer, Phase 9 kernel code, HUD updates
- `engine/test_phase6.py` — new assertions for Phase 9

## WHAT SUCCESS LOOKS LIKE

After your work:
1. `python kernel_dsl.py --verify spiace_phase6.html` exits 0
2. `python test_phase6.py` passes ALL assertions including new Phase 9 ones
3. The HUD shows all kernel toggles + fifth kernel stats
4. Measured numbers reported in test output (not just pass/fail)
5. No WebGPU validation warnings about buffer limits

Document version target: 2.1 | Status target: Phases 0-9 + Tracks A1/A2/C1/C2/B/T complete
