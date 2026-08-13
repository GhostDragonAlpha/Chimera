# SPIACE Phase 10 — Multi-Planet Star System (Phase 9 + Tracks A/B/C/T/D/E Complete)

## Context: What is Already Built

You are the lead developer on SPIACE, a first-principles space RPG engine. The following is complete and verified (committed as 2206f9e):

**Phases 0–9:** Full WebGPU splat renderer, GPU Barnes-Hut N-body with universal kernel translation layer (5 kernels: gravity + light + electromagnetism + heat + acoustic via .chimera DSL), Lorentz force post-tree correction. All falsifiers green at 60 fps in GPU mode.

**All Tracks A–E groundwork:**
- Track A1/A2: Planet terrain → splats, real Earth DEM option
- Tracks C1/C2: Picking + highlight
- Tracks B/T: Scale-relative flight camera + LOD of time
- Track D1/D2: LOD port to v2 renderer + surface fracture (infinite detail)
- Track E1/E2/E3: Character standing/walking on planet with ground query + local-frame controller

**Key architecture in spiace_phase6.html (~3500 lines):**
- 5 kernels in DSL (kernel_dsl.py): gravity(mass), light(lum), EM(charge), heat(heat_source), acoustic(pressure)
- Quantity packing: mass/lum/charge/heat in ONE vec4f quants buffer; acoustic in its own f32 pressures buffer; field outputs in fields vec4f. Total: 8 storage buffers = WebGPU default limit exactly.
- Node size: 144 B (64 base + 5×16 per kernel)
- Planet: currently a SINGLE fixed anchor at PLANET_POS=[1.5e11,0,0] (1 AU), R_PLANET=6.371e6 m, 300 terrain splats (fixed anchors), ~199 orbitals
- Character controller: ground query via heightAt(lat,lon), local-frame WASD walking, gap witness <0.01m at rest
- LOD: N = 0.35·r_px² trained law, mip pyramid + fracture shell, capped at MAX_PARTICLES−500=3596
- Scale handoff: Track B membrane depth (0=system/void, 1=planet atmosphere, 2=surface) with clock-rate gating and local-up vector

**Files to modify:**
- `engine/spiace_phase6.html` — the single HTML file (~3500 lines), no external dependencies
- `engine/test_phase6.py` — Playwright headed-mode test harness (all existing assertions must stay green)
- `engine/SPIACE_RPG_PLAN.md` — update with Phase 10 section

**DO NOT modify:**
- `engine/kernel_dsl.py` — no new kernels needed; the existing 5 already span both 1/d² and 1/d Green's functions. The N-body tree naturally supports multiple massive bodies.

## PHASE 10 SPECIFICATION: Multiple Planet System / Star System Generation

### What to Build

**1. PROCEDURAL STAR SYSTEM GENERATION**
- Generate a star system with 1 star + 3–5 planets (procedural)
- Each planet placed at a habitable-zone-appropriate orbital distance using T_eq = T_star·sqrt(R_star/2d) — inner edge ~0.95 AU, outer edge ~1.67 AU for a solar-type star
- Orbital periods follow Kepler's third law: T = 2π·sqrt(a³/GM_star) — verify as falsifier
- Planets orbit the star dynamically (currently they are fixed anchors; make them participate in N-body gravity)
- Each planet gets procedural terrain parameterized by its mass/radius for realistic geology
- Planet masses: super-Earth to mini-Neptune range (0.1–10 M_earth), radii scaled accordingly

**2. MULTI-MEMBRANE CONTEXT SYSTEM**
- Currently the character lives in a single planetary membrane with PLANET_POS hardcoded everywhere
- Extend so each planet has its own membrane context:
  - `planets[]` array holding {pos, vel, mass, radius, terrainDEM, splats[], _origPos}
  - Active membrane index tracks which planet the character is currently associated with
  - When flying close enough to another planet (within ~10 R_planet), auto-transition membrane context
  - Local up vector, gravity direction, and terrain height query all reframe to the active planet's center
- Scale handoff: when crossing between planetary membranes, coordinate frame shifts from star-centric to planet-centric without losing float64 precision (reuse Track B's membrane-local re-centering)

**3. INTERPLANETARY FLIGHT**
- Character can fly from Planet A surface → orbit → trajectory to Planet B → landing on Planet B
- HUD shows orbital transfer info: distance to next planet, relative velocity, time-to-closest-approach
- The N-body tree already handles multiple massive bodies — this is free once planets are dynamic particles in the tree

**4. FALSIFIERS (all must pass; all existing Phases 6–9 falsifiers stay green)**
- **Falsifier 10:** Two+ planets orbit one star, both with proper Keplerian periods — measured period ratio matches (a₁/a₂)^(3/2) within 5%
- **Falsifier 11:** Character lands on a second planet after flying from the first — gap < 0.01m at rest, no NaN/infinity in position
- **Falsifier 12:** Energy drift (KE + grav PE + EM PE) still < 1% over 60 frames with multiple dynamic planets
- **Falsifier 13:** Thermal equilibrium at each planet's distance from star — T_eq predicted by radiative balance, measured within 15%
- **Witness:** `window.__systemStats` reports planet count, orbital periods (seconds), semi-major axes, and membrane depth transitions during flight

### Measured Numbers to Report in Test Output
- Planet count, masses (kg), radii (m), orbital distances (m), computed orbital periods (s)
- Period ratio vs Kepler prediction: measured / predicted = ? (target: 1.0 ± 0.05)
- Character landing sequence: frames from takeoff on Planet A to rest on Planet B
- Energy drift with multi-planet tree: total ΔE/E over 60 frames (%)
- Membrane depth transitions logged per frame during interplanetary flight
- FPS in GPU mode with multi-planet tree

### Test Harness Update (test_phase6.py)
Add a Phase 10 assertion block after the existing Track D/E block:
- Poll `window.__systemStats` for planet count ≥ 3
- Verify orbital period ratio within 5% of Kepler prediction
- Run character landing sequence on second planet, assert gap < 0.01m and velocity → 0
- Assert energy drift < 1% with multi-planet tree
- Assert thermal equilibrium at each planet's distance within 15%

### Documentation
Update `SPIACE_RPG_PLAN.md` v2.3 with Phase 10 section including all measured numbers, falsifier results, and "Next Steps" pointing to Phase 11 (ship-to-foot narrative arc with atmospheric re-entry) or C++ port.

## Constraints
- Single standalone HTML — no external dependencies
- Non-headless Playwright testing only (`--enable-unsafe-webgpu`)
- `kernel_dsl.py --verify` must pass after any changes
- All existing falsifiers 1–9 must remain green
- Rule 0 applies: state the theory, make a prediction, name the falsifier BEFORE running

## What Success Looks Like
1. `python kernel_dsl.py --verify spiace_phase6.html` exits 0
2. `python test_phase6.py` passes ALL assertions including new Phase 10 ones
3. Three or more planets orbit one star with verified Keplerian periods
4. Character can fly from one planet's surface to another and land successfully
5. All falsifiers report measured numbers, all green

Document version target: 2.3 | Status target: Phases 0–10 + Tracks A/B/C/T/D/E complete