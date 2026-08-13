# SPIACE — Complete Remaining Work (Phase 10 + Tracks A/B/C/T/D/E Complete)

## Context: What is Already Built

You are the lead developer on SPIACE, a first-principles space RPG engine. The following is complete and verified (committed as `cbb1545`):

**Phases 0–10:** Full WebGPU splat renderer, GPU Barnes-Hut N-body with universal kernel translation layer (5 kernels: gravity + light + electromagnetism + heat + acoustic via .chimera DSL), Lorentz force post-tree correction, multi-planet star system with 4 dynamic planets. All falsifiers green at 60 fps in GPU mode.

**All Tracks A–E groundwork:**
- Track A1/A2: Planet terrain → splats, real Earth DEM option
- Tracks C1/C2: Picking + highlight
- Tracks B/T: Scale-relative flight camera + LOD of time
- Track D1/D2: LOD port to v2 renderer + surface fracture (infinite detail)
- Track E1/E2/E3: Character standing/walking on planet with ground query + local-frame controller

**Key architecture in spiace_phase6.html (~3945 lines):**
- 5 kernels in DSL (kernel_dsl.py): gravity(mass), light(lum), EM(charge), heat(heat_source), acoustic(pressure)
- Quantity packing: mass/lum/charge/heat in ONE vec4f quants buffer; acoustic in its own f32 pressures buffer; field outputs in fields vec4f. Total: 8 storage buffers = WebGPU default limit exactly.
- Node size: 144 B (64 base + 5×16 per kernel)
- 4 planets orbiting one star, all dynamic tree particles with Keplerian velocities
- Multi-membrane context: nearestPlanetTo drives activeMembrane; character reframes per-planet
- Character controller: ground query via heightAt(lat,lon), local-frame WASD walking, gap witness <0.01m at rest
- LOD: N = 0.35·r_px² trained law, mip pyramid + fracture shell, MAX_PARTICLES=1M (no practical cap)
- Tree cache: rebuilds only when particles move >1e6 m since last build
- Target resolution: 4K UHD (3840×2160), DPR-scaled canvas

**Files to modify:**
- `engine/spiace_phase6.html` — the single HTML file (~3945 lines), no external dependencies
- `engine/test_phase6.py` — Playwright headed-mode test harness (all existing assertions must stay green)
- `engine/SPIACE_RPG_PLAN.md` — update with new phases

**DO NOT modify:**
- `engine/kernel_dsl.py` — the DSL already spans both 1/d² and 1/d Green's functions; new physics enters via declarations, not code changes

---

## PHASE 10.5: TILE ARTIFACT ELIMINATION (Renderer Quality)

### The Problem
The tile-based splat rasterizer (`sh-raster` WGSL fragment shader) produces visible seams and artifacts at tile boundaries:

1. **TILE_SIZE=16 is too large** — At 4K, ~32,400 tiles each independently accumulate splat contributions into local `occ`. Wide splats spanning multiple tiles cause per-tile accumulation divergence → visible seams on high-contrast terrain edges.

2. **Per-tile sort divergence** — Each tile sorts its own splat list back-to-front using center depth (`cw`). A single wide splat gets sorted independently in each adjacent tile; since `cw` varies across the splat's extent, two overlapping splats can reverse order between tiles → "splat A on top here, B on top there" seams.

3. **MAX_PTILE=64 hard cap** — Each tile processes at most 64 contributions per pixel. At high density (7K+ fracture splats), busy pixels skip contributions that neighbors include → staircase pattern in dense regions.

### What to Fix
1. **TILE_SIZE**: Evaluate 8 vs 16 vs 32. Smaller tiles = less per-tile divergence but more tiles. Recommend TILE_SIZE=8 for 4K.
2. **Sort consistency**: Make `sorted_idx` a true global sort (computed once on CPU, not per-tile). The current code already sorts within each tile independently — change to compute one global back-to-front order and use it in every tile.
3. **MAX_PTILE**: Raise from 64 to 256. GPU fragment shaders have plenty of registers; this eliminates the hard cap that causes missing contributions.
4. **Binning oversize**: Extend tile binning by 1 pixel on each side so splats near edges are included in ALL tiles they touch, not just those whose center falls in the bin.

### What NOT to Touch
- kernel_dsl.py, test harness (except fixing broken assertions), tree construction, N-body integration, HDR bloom pipeline

---

## PHASE 11: SHIP-TO-FOOT NARRATIVE ARC WITH ATMOSPHERIC RE-ENTRY

### What to Build

**1. Ship Physics — Tsiolkovsky Rocket Equation**
- The flight camera becomes a ship with mass, fuel, and thrust
- Δv = I_sp · g₀ · ln(m₀/m_f) — verify as falsifier
- Fuel burns reduce ship mass; I_sp configurable (default 300 s chemical)
- Thrust follows camera facing; fuel gauge in HUD
- When out of fuel → passive ballistic projectile (N-body gravity only)

**2. Atmospheric Re-entry Heating**
- Each planet has an atmospheric thin-shell model (scale height per planet, already partially built in Track A2)
- Density profile: ρ(h) = ρ₀ · exp(−h/H)
- Convective heat flux: q̇ ∝ ρ · v³ — ship temperature rises during entry
- HUD shows: atmospheric thickness, altitude, airspeed, dynamic pressure (q = ½ρv²), skin temperature
- Thermal limits: if skin temp exceeds threshold → fuel system failure or structural damage

**3. Complete Narrative Arc**
- Start on Planet A surface (character mode — already working)
- Take off: transition character → ship at launch pad
- Burn to orbit: reach altitude where atmosphere is negligible, circularize
- Fly to Planet B: interplanetary transfer (HUD already shows distance/Δv/time-to-CA)
- Enter Planet B atmosphere: re-entry heating visible in HUD, deceleration from drag
- Land on Planet B surface: transition ship → character mode
- Walk around Planet B

**4. Membrane Depth Extensions**
- Current: depth 0 = void, 1 = planet atmosphere, 2 = surface
- Add depth −1 = "in ship" (above atmosphere but in gravitational well)
- Transitions with appropriate physics switches:
  - Depth 2 → ship controls available (thrust, fuel)
  - Depth 1 → atmospheric effects active (drag, heating)
  - Depth 0 → pure N-body gravity

### Falsifiers
- **F14:** Tsiolkovsky Δv budget — orbit insertion with predicted remaining fuel within 5%
- **F15:** Re-entry heating — peak skin temp matches analytic q̇ ∝ ρ₀·exp(−h/H)·v³ estimate within 10%
- **F16:** Complete arc success — character lands on Planet B, gap < 0.01m at rest
- **F17:** Energy conservation — total energy (KE + grav PE + fuel chemical energy) conserved to < 2%

---

## PHASE 12: KERNEL TRANSLATION EXPANSION — WHAT ELSE CAN WE MAP?

### Context
The kernel DSL already handles gravity, light, EM, heat diffusion, and acoustics. The question (from operator) is what other physical phenomena can be expressed as point-source interactions through the Barnes-Hut tree.

### What to Build
1. **Full electromagnetic force** — not just Coulomb's law but:
   - Biot-Savart law for current-carrying particles (magnetic field from moving charge)
   - Full Lorentz force F = q(E + v×B) as a kernel, not just the post-tree uniform-B correction from Phase 7
   - This requires adding a velocity-dependent near-field term alongside the far-field tree traversal

2. **Gravitational radiation reaction** (optional bonus):
   - Post-Newtonian corrections for binary systems
   - Energy loss via gravitational waves for close massive binaries
   - Expressed as a 1/d³ kernel through the tree (higher-order multipole)

3. **Drag / collisional friction** as a near-field correction:
   - Not a superposable force, but can be expressed as per-particle damping proportional to local density
   - Local density estimate via the tree's leaf-level particle count

### DSL Declaration Examples
```
kernel mag_field {
    quantity = current;      // I = q * v / dt (effective)
    aggregate = weighted_sum; // center-of-current
    kernel_fn = dipole_1d3;   // 1/d³ falloff for magnetic field
    sign = none;              // vector direction handled by cross-product
}
```

---

## PHASE 13: C++ PORT OF THE KERNEL LAYER

### What to Port
The proven physics and rendering logic from `spiace_phase6.html` into native C++ for desktop distribution. This is a translation layer — the algorithms are already verified, just need to be re-implemented in C++.

**Scope:**
- Barnes-Hut tree construction and traversal (CPU + GPU compute shader via Vulkan/DX12)
- Kernel DSL parser (`.chimera` → WGSL or native C++ compute shaders)
- Splat renderer pipeline (WebGPU equivalent in Vulkan/DX12, or keep WebGL for web build)
- Character controller with ground query and local-frame walking
- Multi-membrane context system

**Not in scope for this phase:**
- The browser/Playwright test harness
- The HTML/CSS HUD overlay
- Atmospheric re-entry (Phase 11 — port that separately after it ships)

### Architecture Decision Needed
Choose between:
- **Vulkan + GLSL**: Cross-platform, mature, better GPU compute support
- **DX12 + HLSL**: Windows-focused but simpler for the target audience
- **WGPU (WebGPU native)**: Reuse the WGSL shaders with minimal changes; Rust-based

### What NOT to Port Yet
- The full Phase 11 ship-to-foot narrative arc
- Multiplayer/netcode (Phase 4 was browser-only)
- The kernel DSL generator itself (keep it as a Python build tool)

---

## PHASE 14: MULTI-SHIP CO-OP + PERSISTENT UNIVERSE

### What to Build
Phase 3/4 were started but not completed for the multi-planet context. Now that we have multiple planets, this becomes meaningful:

1. **Multi-ship local co-op** (2 players on same machine):
   - Player 1: keyboard (WASD flight) + Player 2: arrow keys or gamepad
   - Shared N-body tree; each ship is a separate dynamic body in the tree
   - Camera split-screen or shared camera with toggle

2. **Persistent universe save/load**:
   - Serialize the full system state (all particle positions, velocities, charges, masses) to JSON
   - Load restores exact state — character can walk back to where they left off on Planet B
   - Falsifier: saved and reloaded state has 0% position divergence vs original

3. **Mission system** (lightweight):
   - Simple waypoint-based navigation: "Fly from Planet A to Planet B"
   - Progress tracking in HUD
   - Trigger events: "landed on target planet" → mission complete

---

## CONSTRAINTS
- Single standalone HTML for the browser build — no external dependencies
- Non-headless Playwright testing only (`--enable-unsafe-webgpu`)
- `kernel_dsl.py --verify` must pass after any changes
- All existing falsifiers 1–17 must remain green (Phases 6–10 + Tracks D/E)
- Rule 0 applies: state the theory, make a prediction, name the falsifier BEFORE running

## RECOMMENDED ORDER
1. **Phase 10.5 first** — fix tile artifacts so the renderer quality is solid before adding more features on top
2. **Phase 11 second** — the ship-to-foot arc is the core gameplay experience; it builds directly on Phase 10's multi-planet system
3. **Phase 12 third** — kernel expansion is conceptual work; do it after the game loop is stable
4. **Phase 13 fourth** — C++ port is a separate codebase; keep it clean and independent
5. **Phase 14 last** — co-op and persistence are nice-to-have; they depend on everything above being solid

## SUCCESS CRITERIA (Per Phase)

### Phase 10.5:
- No visible tile seams at any zoom level (orbit → surface)
- Wide splats render consistently across all tiles — no staircase pattern
- GPU mode ≥ 50 fps at 4K with all kernels active

### Phase 11:
- Complete arc works: surface A → orbit → Planet B landing → character walks around
- All falsifiers 14–17 pass
- HUD shows meaningful telemetry throughout (fuel, Δv, skin temp, dynamic pressure)

### Phase 12:
- New kernel(s) declared in DSL and verified via `kernel_dsl.py --verify`
- At least one new falsifier added and passing
- Tree traversal handles the new kernel without breaking existing ones

### Phase 13:
- C++ binary runs on desktop (Windows target first)
- Same physics results as the browser version (falsifiers match within numerical tolerance)
- DSL parser produces identical output to the JS version

### Phase 14:
- Two ships visible and controllable simultaneously
- Save/load roundtrip with 0% position divergence
- At least one mission sequence completes end-to-end

## DOCUMENTATION
Update `SPIACE_RPG_PLAN.md` v3.0 with all new phases, measured numbers, and falsifier results.

Document version target: 3.0 | Status target: Phases 0–14 complete + Tracks A/B/C/T/D/E complete