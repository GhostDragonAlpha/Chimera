# SPIACE Track B + T - Scale-Relative Flight + LOD of Time

## Context: What is Already Built (Updated by bionic)

You are the lead developer on SPIACE, a first-principles space RPG engine. The following is already complete and verified:

**Phases 0-6:** Full WebGPU splat renderer (preprocess -> tile raster -> bloom -> tonemap), GPU Barnes-Hut N-body with universal kernel translation layer (gravity + light + electromagnetism via .chimera DSL), energy/thermal/falsifier verification all green.

**Track A1 (completed by bionic):** Planet terrain connected to splats - 300 surface splats on Fibonacci lattice, FBM noise elevation + bimodal hypsometry transfer, height-band coloring (ocean/beach/forest/rock/snow). Terrain particles are fixed membrane anchors (exert gravity, do not move). Camera frames planet at ~4 planetary radii.

**Track A2/C1/C2 groundwork (completed by bionic just now):**
- spawnPlanet() accepts an optional equirectangular DEM parameter (same interface as PlanetOnion.from_topo_grid()) - real Earth data can be dropped in without code changes
- generateSyntheticDEM() pre-builds a 180x360 equirectangular grid from the same noise pipeline
- Track C1 picking state: selectedParticleIdx tracks cursor-click selection, PICK_RADIUS_SQ=9px
- displayColor() has isSelected highlight overlay (white boost) for Track C2

**The file you will modify:** engine/spiace_phase6.html -- single standalone HTML file, no external dependencies, WebGPU via script type module. (~2100 lines now)

**Test harness:** engine/test_phase6.py -- Playwright headed-mode, runs kernel_dsl.py --verify first, then asserts particle count, tree stats, charge fields, thermal equilibrium (<1% error), energy drift (<1%), deflection (>10m), mode switching, renderer type. All currently passing.

**Key architecture:**
- Particles carry per-kernel quantities: mass, lum, charge
- Barnes-Hut tree aggregates one (center, quantity) pair per kernel per node
- Rendering: WebGPU Gaussian splats, CPU cull+bin+sort, GPU tile raster
- Camera currently: fixed orbit view at [0, 2.5e7, 1.5e7], WASD movement at 5e9 m/s
- Planet: fixed anchor at origin, R = 6.371e6 m, 300 terrain splats
- Orbitals: ~199 bodies at 5e10-3.5e11 m from star
- Terrain particles marked with _terrainCol and _origPos (fixed anchors)


## TRACK B - Scale-Relative Flight Camera

### Thesis (Rule 0)
Statement: A fly camera whose speed is derived from the distance to the nearest membrane surface (not a slider) automatically produces correct-feeling navigation at every scale - slow near rocks, fast between planets - without any user input.

Prediction: With speed = k * dist_to_surface, the camera will feel right at all scales without tuning, and the membrane depth number simultaneously drives LOD selection.

Falsifier: If speed ever exceeds 10x local escape velocity or drops below 1 m/s near a surface, the derivation is wrong.

### B1: Scale-Relative Flight
Replace the fixed-speed WASD with:
speed = k * min_distance_to_surface
where min_distance_to_surface is the distance from camPos to the nearest terrain splat (or any membrane surface). Derive k from physical constraints: at 1 planetary radius above surface, speed should be ~100 m/s (walk pace); at 1 AU from star, speed should be ~1e6 m/s (orbital pace). This gives a single k that works everywhere.

WASD still controls direction, but now in the camera local frame (forward/right/up relative to where you are looking), not world axes.

### B2: Membrane Traversal
As the camera approaches/retreats from objects, its current membrane depth changes:
- Far from everything -> depth 0 (system scale, star + orbitals visible)
- Approaching planet -> depth increases (planet surface detail resolves)
- On surface -> maximum depth (terrain cells visible)

This depth number drives:
1. LOD selection - which splat resolution to use
2. Speed scaling - the k in B1 is depth-dependent
3. Local up - up becomes the local surface normal when on a planet, world +Y in void

The traversal is simple: find the nearest membrane object, compute distance / object extent = depth proxy. No tree descent needed for camera - just distance comparison.

### B3: Orientation HUD
Replace the current plain text HUD with membrane-native info:
- Current membrane path (serial string, e.g., system->planet)
- Altitude above surface (or in void when no surface nearby)
- Speed in sensible units per scale (m/s near planet, km/s between planets)
- Local-up indicator (arrow showing which way is up from current position)
- Axis gizmo (small 3D axis in corner)

### B4: Focus/Frame
Pressing F on a particle (or clicking it) smoothly flies the camera to a framing distance and locks onto it. The framing distance is derived from the object render radius: frame_dist = max(renderRadius * 5, 1000).
---

## TRACK T - LOD of Time (Per-Membrane Tick Rate)

### Thesis (Rule 0)
Statement: Different membrane depths should tick at different rates - deep (surface) at full rate, shallow (system) in coarse steps - because the physics that matters at each scale has different time constants.

Prediction: A particle at 1 AU will have its position updated every frame (full rate), while a distant star position only needs updating every N frames because its orbital period is much longer than the local dynamics.

Falsifier: If advancing two membranes at different rates for 60 frames produces position divergence > 1% from what a single full-rate simulation would produce, the clock rate derivation is wrong.

### T1: Per-Membrane Tick
Each membrane has a clock_rate derived from its extent:
clock_rate = min(1.0, extent / (k_time * ref_extent))
where ref_extent is a reference scale (e.g., 1 AU = 1.5e11 m) and k_time tunes the aggressiveness.

- Planet surface membrane: extent ~R_earth = 6.371e6 m -> clock_rate approx 1.0 (full tick)
- System membrane: extent ~3.5e11 m -> clock_rate approx 0.43 (tick every ~2.3 frames)

The CPU Barnes-Hut already runs every frame. For Track T, we add a frame-skipping layer: each particle group (star, planet anchors, orbitals) only integrates when its membrane tick counter fires.

### T2: Derive Camera Speed from Clock
Instead of B1 speed = k * dist, derive speed from the current membrane clock rate:
speed = k_speed * clock_rate * (distance_to_target)
This means: when you are deep in a gravity well (high clock rate), you move fast. When you are in interplanetary space (low clock rate), you move slowly - matching the feel of B1 but derived from first principles.

### T3: Show It, Then Witness It
HUD displays current membrane clock rate alongside the path. Add a witness test: run two simulations for 60 frames - one at full rate everywhere, one with per-membrane ticking - and report the position divergence as a number. This is the falsifier.

### T4: (Optional) Time Dilation as Mechanic
Return from deep gravity well - world has moved on. Falls out of T1 naturally; no new physics needed.
---

## Combined B+T Implementation Plan

Step 1: Derive k for scale-relative speed
- At planet surface (r approx 6.371e6 m), want ~100 m/s with WASD
- At 1 AU (r approx 1.5e11 m), want ~1e6 m/s
- Solve: speed = k * dist_to_nearest_surface
- k approx 100 / 6.371e6 approx 1.57e-5 (near surface)
- Check at 1 AU: 1.57e-5 * 1.5e11 approx 2.36e6 m/s - close enough to target

Step 2: Implement membrane depth detection
- For each frame, compute distance from camPos to nearest object
- Map distance to depth level (0 = system, 1 = planet, 2 = surface)
- Use thresholds based on object extents

Step 3: Implement per-membrane ticking
- Add tickCounter and clockRate per particle group
- Skip integration when counter < 1/clockRate
- Accumulate fractional time

Step 4: HUD overhaul
- Replace current panels with membrane-native display
- Show path, altitude, speed, clock rate, local up

Step 5: Camera controls
- WASD in local camera frame
- F to focus/frame on clicked particle
- Mouse for look direction (pointer lock or drag)

---

## Constraints

1. Single HTML file - no external dependencies
2. Non-headless testing only - Playwright headed mode with --enable-unsafe-webgpu
3. All existing falsifiers must continue to pass - energy drift <1%, thermal equilibrium within 15%, deflection >10m
4. MAX_PARTICLES = 4096 - do not exceed
5. Do not break the kernel DSL - kernel_dsl.py --verify must still pass
6. Physics stays in real units (meters) - rendering divides by WORLD_SCALE

---

## What NOT to Build

- Do not rebuild Unreal editor primitives
- Do not add a speed slider (B1 derives speed, no user input needed)
- Do not add collision detection (that is Track E)
- Do not add picking/hit detection beyond F focus (that is Track C)
- Do not modify the kernel DSL or WGSL shaders
- Do not change the renderer pipeline

---

## Deliverable

A modified spiace_phase6.html where:
1. Camera flies scale-relatively (fast in void, slow near surfaces)
2. HUD shows membrane path, altitude, speed, clock rate
3. Per-membrane ticking is active and measurable
4. All Phase 6 falsifiers still pass
5. New falsifier: position divergence between full-rate and LOD-of-time simulations < 1% over 60 frames

Run python test_phase6.py (headed) to verify. If new assertions are needed, add them to the test file.

---

## Key Files

- Main: engine/spiace_phase6.html (2039 lines, single HTML + JS + WGSL)
- Test: engine/test_phase6.py (Playwright headed)
- DSL: engine/kernel_dsl.py (do NOT modify - just verify it still passes)
- Plan: engine/SPIACE_RPG_PLAN.md
- Roadmap: ROADMAP.md

Agent bionic handed off. You are Kimi K3. The planet is already rendered as terrain splats - make it flyable.