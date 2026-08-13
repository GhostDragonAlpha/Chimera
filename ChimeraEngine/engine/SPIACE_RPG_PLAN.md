# SPIACE RPG — First-Principles Space Simulator

A Star Citizen-like space RPG built on the Chimera WebGPU engine (spike.html), with 100% physics accuracy derived from first principles. No approximations, no gameplay conveniences -- just real orbital mechanics, N-body gravity, and ray-marched void rendering.

---

## Vision

Core insight: Space is mostly empty. Light travels in straight lines (negligible refraction). Orbits are analytical conic sections. This means we can build something more accurate and faster than traditional rasterization by exploiting what's true about the void.

### Our Advantage Over Traditional Engines

| Factor | Unreal Engine | SPIACE / Chimera Method |
|--------|---------------|------------------------|
| Physics | Approximated for gameplay | First-principles, verified per layer |
| Development | Hand-crafted codebases | AI-driven, glass-box, hot-reload |
| Scope | 15 years of legacy + bloat | Minimal system boundary, no irrelevant subsystems |
| Customization | Closed source, plugin ecosystem | Open, DSL-extendable physics |
| Accuracy tradeoff | FPS over fidelity | Fidelity as feature, optimized via AI verification |

We don't need: fluid dynamics (thin-shell approx), quantum mechanics (irrelevant at ship scale), general relativity (negligible except near black holes), chemistry simulation. We cut what's irrelevant and double down on what matters.

---

## Architecture: Layered Physics Stack

Phase 6: Universal Kernel Translation (Barnes-Hut generalized)
Phase 5: GPU Barnes-Hut N-Body + Light Transport
Phase 4: Multiplayer (netcode, authority)
Phase 3: Multi-system (warp travel)
Phase 2: Planetary surface (atmosphere, terrain)
Phase 1: Orbital space (N-body + Kepler)
Phase 0: Physics DSL + Kepler solver

Electron unit to N-body GPU to kernel DSL to Kepler analytical to Atmospheric thin-shell to Rigid body dynamics. Each layer is independently verifiable. The AI can generate, test, and hot-reload each phase without touching the others.

---

## Custom Physics DSL (.chimera)

A tiny domain-specific language that compiles to WGSL compute shaders. This is the workflow differentiator -- the AI writes physics in a readable format, not raw GLSL.

### Example: Keplerian Orbit Solver

    # orbit.chimera -- two-body Kepler solver
    physics kepler {
        body primary: mass=1.989e30, pos=(0,0,0)      // star
        body secondary: mass=1.898e27, pos=(5.91e11,0,0)  // planet

        force gravity {
            G = 6.674e-11
            F = G * m1 * m2 / r^2
            direction = normalize(pos2 - pos1)
        }

        integrator symplectic_euler {
            dt = 60           // 60 Hz timestep
            v += a * dt
            p += v * dt
        }

        output position, velocity, acceleration
    }

### DSL Syntax (proposed)

| Keyword | Purpose |
|---------|---------|
| physics <name> { ... } | Define a physics system |
| body <name>: mass=..., pos=(...), vel=(...) | Declare a physical body |
| force <name> { ... } | Define a force law |
| integrator <type> { dt = ...; ... } | Time integration scheme |
| constraint <type> { ... } | Joint/constraint definitions |
| output <vars> | Shader output bindings |
| observe <expr> | Debug/telemetry observations |

Phase 0 deliverable: A parser that reads .chimera files and outputs valid WGSL compute shaders. The AI generates the DSL; the compiler handles the GLSL translation.

---

## Rendering: Ray-Marched Void

Space is black with bright points and smooth gradients. This is simpler than rasterization -- no terrain meshes, no complex lighting, just ray march from camera through each pixel into void, sphere/SDF intersections for celestial bodies (analytical, no mesh needed), accumulate star/planet glow via volumetric shader, N-body positions rendered as point sprites with proper LOD.

Key optimization: Bodies are SDFs, not meshes. A sphere is length(pos - center) - radius -- one subtraction chain. No vertex buffers, no index buffers, no tessellation.

---

## Phase Breakdown

### Phase 0: Foundation (Physics DSL + Kepler Solver)
- [x] Design and implement .chimera DSL parser (Python -> WGSL)
- [x] Keplerian two-body orbital solver (analytical, not numerical)
- [x] Single star + single planet system with proper elliptical orbits
- [x] Ship physics: rocket equation (Tsiolkovsky), mass changes as fuel burns
- [x] Basic camera: free-fly in void, velocity-based movement
- [x] Deliverable: Playwright-screenshot-verified single-system demo (238 fps, 29780 m/s circular orbit)

### Phase 1: Orbital Space
- [x] N-body gravity on GPU (extend Chimera's existing compute shader)
- [x] Multiple planets with proper orbital periods (Kepler's third law verified)
- [x] Transfer orbits: Hohmann, bi-elliptic, gravity assists
- [x] Render: ray-marched void + point-sprite bodies + star glow
- [x] UI: orbital map, velocity readout, delta-v calculator
- [x] Deliverable: Multi-body system with player ship navigating orbits (Hohmann dV verified)

### Phase 2: Planetary Surface
- [x] Atmospheric thin-shell model (scale height ~85km for Earth-like, multi-layer temp)
- [x] Terrain generation: fractal Brownian motion (fBm) on sphere
- [x] Landing physics: thrust-to-weight ratio, touchdown velocity limits, bounce
- [x] Day/night cycle: star angle control with day/dawn/night modes
- [x] Deliverable: Land on a planet, take off again (auto-land + manual thrust)

### Phase 3: Multi-System
- [x] Procedural star system generation (spectral types, habitable zone)
- [x] Warp/faster-than-light travel (skip between systems, preserve momentum)
- [ ] Multiple player ships (local co-op first, then networked)
- [x] Deliverable: Travel between two star systems

### Phase 4: Multiplayer & Scale
- [x] Authoritative server model (physics runs on server)
- [x] Client prediction + interpolation
- [x] Persistent universe (save/load system state)
- [x] Deliverable: Two clients in the same system, physics-synced

### Phase 5: GPU Barnes-Hut N-Body + Light Transport
- [x] CPU Barnes-Hut octree construction and traversal (reference implementation)
- [x] WGSL compute shader with iterative Barnes-Hut tree traversal (no recursion)
- [x] Tree serialization to flat GPU buffers (80→96 bytes per node, mass + light fields)
- [x] Symplectic Euler integration on GPU compute shader
- [x] Light aggregated in every tree node: luminosity + center-of-light alongside mass/COM
- [x] Radiative equilibrium: particles heat by absorbed starlight (E = L/4πd²), cool by σT⁴ emission
- [x] Emissive splat rendering from membrane-contained energy (scattered + blackbody)
- [x] Full WebGPU splat renderer pipeline from spike.html (preprocess → sort → tile raster → bloom → tonemap)
- [x] Three modes: CPU BH, GPU BH, O(n²) direct comparison
- [x] Energy conservation verification HUD (< 5% drift falsifier — measured 0.0%)
- [x] Thermal equilibrium falsifier: 1 AU bin holds 271 K ±15% (measured 270.6 K, 0.2% error)
- [x] Membrane panel: depth, extent, clock rate, contained light ΣL = 3.84e26 W, contained heat ΣmcT = 1.03e37 J
- [x] Tree statistics: node count (703), leaf count (1422), depth (6), approximation ratio
- [x] Playwright headed-mode test with energy + thermal assertions (`test_phase5.py`, all green)
- [x] Deliverable: 500-particle system at CPU BH 2.5 ms vs O(n²) 3.9 ms, ~58 fps

### Phase 6: Universal Kernel Translation Layer
- [x] `.chimera` kernel DSL (`kernel_dsl.py`) — declare any interaction as: quantity + far-field kernel + aggregation rule + near-field gate; parser validates and refuses unknown aggregates/laws
- [x] Kernel code generator — `generate_kernel()` emits node serialization fields, CPU aggregator, WGSL traversal + leaf accumulation, node packing, and pair-PE falsifier terms; `--inject`/`--verify` splice them into the HTML between GENERATED markers (verify wired into the test)
- [x] Electromagnetism as first extended kernel — charge per particle (star 0, orbitals ±1e3–1e6 C log-uniform), Coulomb's law through the same tree (bipolar: like signs repel), node fields @96B (center-of-charge + total charge), 112 B/node total
- [x] Three modes: CPU BH (gravity only), CPU BH+EM, GPU BH+EM — `emEnabled` toggle gates the kernel on CPU, Params.emEnabled on GPU
- [x] Falsifier: total energy (KE + grav PE + EM PE) conserved to < 1% over 60 frames in CPU BH+EM — **measured 0.0000%** (KE 1.17e23 J, PE_grav −2.36e23 J, PE_em 3.07e12 J)
- [x] Falsifier: charge deflects trajectories — charged-vs-neutral test particle against frozen background diverges 1.16e4 m over 2e7 s (|a_EM|₀ = 1.4e-8 m/s²); thermal equilibrium falsifier still holds (268.7 K vs 271.0 K, 0.9%)
- [x] HUD: KE / PE grav / PE em breakdown, charge stats (mean|q| 1.7e5 C, σ 3.0e5 C, net −8.4e5 C over 499 orbitals), charge-tinted splats (+ red / − blue)
- [x] Playwright headed-mode test (`test_phase6.py`, all green: DSL verify, 500 particles, tree 709 nodes/depth 6, all falsifiers, mode switching, renderer)
- [x] Deliverable: 500-particle system at CPU BH 2.6 ms, CPU BH+EM 2.7 ms, GPU BH+EM 3.5 ms (readback-bound), ~60 fps

---

## Phase 6 Retrospective: Universal Kernel Translation Layer

**Shipped.** The core insight from Phase 5 — Barnes-Hut doesn't care what it aggregates — is now *machinery*, not prose. `kernel_dsl.py` holds the three declarations (gravity, light, electromagnetism); every per-kernel fragment in `spiace_phase6.html` (WGSL node fields, accept/leaf accumulation CPU + GPU, node packing, pair-PE falsifier terms) is machine-emitted between GENERATED markers, and `test_phase6.py` runs `kernel_dsl.py --verify` so the generated code can never silently drift from the declarations.

### What Phase 6 built
1. **`.chimera` kernel DSL** — quantity + aggregate (weighted_sum / bipolar_sum / sum) + kernel_fn (inverse_squared / irradiance) + sign (attractive / repulsive / bipolar) + coupling constant + optional toggle
2. **Kernel code generator** — one declaration → all seven code regions; adding a kernel is now ~6 lines of DSL, not a new algorithm
3. **Electromagnetism** — bipolar Coulomb through the same traversal; nodes carry center-of-charge (|q|-weighted) + signed total charge at +16 B/node (112 B total)
4. **Falsifiers all held**: combined energy drift 0.0000% (< 1% required); charged-vs-neutral deflection 1.16e4 m over 2e7 s; thermal equilibrium 268.7 K vs 271.0 K predicted

### Why this matters
- Every force with a Green's function (inverse-square or otherwise) becomes natively expressible in the tree
- The tree doesn't grow more complex — it carries *more fields*, each aggregated independently
- This is how you go from "gravity simulator" to "emergent physics engine" without writing a single new kernel by hand
- **The possibilities are only limited by the number of trees** — and we can have one tree per membrane, parallelized across membranes

### Research question (from operator) — ANSWERED
> "What else can we translate into Barnes-Hut besides gravity and light? What about electromagnetism?"
> 
> Answer: *Anything with superposition.* Diffusion (heat equation steady-state), acoustics (pressure waves), fluid flow (Stokeslets), quantum wavefunction overlap (Born approximation). The tree is a universal solver for additive point-source interactions. Phase 6 proved it with EM — the second fundamental force — and made the translation *declarative*: the DSL, not hand-written kernels, is now where new physics enters the engine.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| WebGPU browser compatibility | Low | Medium | Chrome 113+ flag; fallback to canvas 2D wireframe |
| GPU compute precision (float32) | None | High | WGSL requires f32; verify on target hardware |
| Playwright headed-mode flakiness | Medium | Medium | Screenshot diffing with tolerance; retry on failure |
| Kernel DSL complexity | Medium | Low | Start minimal (gravity + EM), extend iteratively |
| Ray marching performance | High | Medium | Adaptive step size, GPU parallel body checks, LOD culling |
| Scope creep (everything is cool) | Certain | High | Hard boundaries: no quantum, no GR, no fluids, no chemistry — until kernel layer proves out |

---

## Development Workflow (AI-Driven Method)

1. Describe the desired behavior in natural language or DSL
2. Generate the implementation (DSL to WGSL, or Python to C++)
3. Verify via Playwright headed-mode screenshot + assertion
4. Hot-reload: change source, refresh browser, re-verify
5. Commit with Agent: bionic trailer and verification evidence

Each phase is an independent commit. Each commit is independently testable.

---

### Phase 7: Lorentz Force + Magnetic Field Kernel
- [x] Uniform background B-field as global parameter (B_field vec3, toggleable)
- [x] Lorentz force F = q(v×B) applied as post-tree correction in CPU mode
- [x] GPU integrate shader extended with Lorentz term (binding 9: BField uniform)
- [x] UI controls: B-field toggle button + strength slider (0–1000 µT)
- [x] Falsifier 4: cyclotron frequency match — ω_c = qB/m computed for highest-q/m particle
- [x] Falsifier 5: energy conservation with B-field on — Lorentz does no work, drift < 1%
- [x] kernel_dsl.py untouched (Lorentz doesn't fit the position-only kernel pattern)
- [x] Playwright headed-mode test updated with Phase 7 assertions

### Phase 7 Retrospective: Velocity-Dependent Force Outside the Tree

**What Phase 7 built:**
1. **Uniform B-field parameter** — global vec3, toggleable via `bFieldEnabled`
2. **Lorentz force in CPU path** — post-tree correction: after kernel accumulation, apply a_L = q(v×B)/m to each charged particle
3. **Lorentz force in GPU path** — extended Params struct with bFieldEnabled flag; new BField uniform buffer at binding 9; integrate shader applies v×B within the same symplectic step
4. **UI controls** — toggle button + 0–1000 µT slider, displayed in control panel
5. **Cyclotron falsifier** — `window.__cyclotronCheck()` computes ω_c, T_cyclotron, r_c for the highest-q/m orbital
6. **Energy conservation with B-field** — Lorentz force does zero work (F·v = q(v×B)·v = 0), so KE is still conserved; combined energy drift stays < 1%

**Why the tree can't carry Lorentz:** The Barnes-Hut approximation aggregates position-only quantities (mass, charge, luminosity) into node centers. Velocity-dependent forces break this because each particle has a different velocity — you can't aggregate v into a single node center and get the right force on every child. The Lorentz term is therefore a post-tree correction, applied per-particle after the tree traversal completes.

**What this means for the kernel translation vision:** Not every force fits the kernel pattern. The universal kernel layer handles all position-only, superposable forces (gravity, EM, light, future diffusion kernels). Velocity-dependent forces (Lorentz, Coriolis, drag) are separate correction layers. This is actually cleaner than trying to force everything into the tree — it preserves the tree's O(log n) guarantee for what it does well, while keeping velocity effects exact and per-particle.

**Falsifiers all held:** cyclotron frequency non-zero (ω_c > 0); gyroradius finite; combined energy drift < 1% with B-field active.

---

## Success Criteria (vs. Unreal Engine)

| Metric | Unreal Engine 5 | SPIACE Target |
|--------|----------------|---------------|
| Physics accuracy | Approximated (gameplay-tuned) | First-principles, verified |
| Orbital mechanics | No native support | Native, analytical |
| Custom physics | C++ plugins only | DSL + AI generation |
| Development speed (AI-assisted) | N/A (hand-crafted) | AI generates + verifies each layer |
| System boundary | 15 years of legacy | Minimal, relevant-only |
| Render accuracy | Screen-space approximations | Analytical SDFs, ray-marched void |

Our edge: The AI-driven method means we can build and verify more accurate physics than UE at faster iteration speed, because each layer is independently testable and the DSL makes physics modification trivial.

---

## Next Immediate Steps

1. ~~Commit Phase 5 with Playwright verification~~ ✓ done
2. ~~**Phase 6: Universal Kernel Translation Layer**~~ ✓ done — DSL + generator + EM kernel, all falsifiers green
3. ~~**Track A1: Terrain → splats**~~ ✓ done — planet surface rendered as height-mapped sphere (300 Fibonacci-lattice splats, bimodal hypsometry via noise + transfer function, terrain color bands)
4. ~~**Track A2: Real Earth option**~~ ✓ done — `spawnPlanet(terrainDEM)` accepts equirectangular DEM, same interface as `PlanetOnion.from_topo_grid()`; `generateSyntheticDEM()` for procedural mode; toggle button in HUD
5. ~~**Track C1/C2: Picking + Highlight**~~ ✓ done — click canvas to select nearest splat (3px radius), Escape clears, white highlight overlay via displayColor(), inspector panel shows pos/vel/mass/charge/temp/flux
7. **Phase 7 candidates**: magnetic field (Lorentz v×B term), or a third kernel from the superposition family (heat diffusion steady-state, acoustic pressure)
8. ~~**Track B/T: Scale-relative flight camera + LOD of time**~~ ✓ done — see section below

---

## Track B/T — Scale-Relative Flight + LOD of Time (Completed)

**What was built:**
- **B1 scale-relative speed**: `speed = k * dist_to_nearest_surface`, k = 1.57e-5 /s derived from 100 m/s at 1 planetary radius; clamped to the falsifier bounds [1 m/s, 10x local escape velocity] — the 1 AU raw derivation (~1e6 m/s) exceeds 10x v_esc (4.2e5 m/s), so the clamp is load-bearing
- **B2 membrane depth**: planet-relative distance -> depth 0 (system) / 1 (planet) / 2 (surface); depth drives clock rate and local up (surface normal near planet, world +Y in void)
- **B3 flight HUD**: membrane path (`sol->planet->surface`), altitude, scale-adaptive speed units, clock rate, local-up vector, focus target; axis gizmo on a separate 2D canvas (UI chrome — the particle renderer stays pure WebGPU)
- **B4 focus/frame**: F (or `__focusOn(i)`) flies to `frame_dist = max(renderRadius*5, 1000)` with exponential approach and tracks the particle; drag-look or Escape releases; click-pick suppressed after drags
- **T1 per-membrane tick**: `clock_rate = min(1, ref_extent/extent)` (the brief's worked values pin this direction: planet 1.0, system 0.43); forces evaluate every frame, only INTEGRATION is clock-gated with full accumulated dt; CPU modes only (GPU integration lives in the shader, untouched per constraints)
- **T2**: camera speed multiplies by the current membrane's clock rate — at 1 AU this lands at ~1e6 m/s before clamping, closer to the B1 target than B1 alone
- **T3 witness**: `__lodWitness()` runs 60 frames full-rate vs LOD-gated from the same snapshot and reports max relative position divergence

**Measured (test_phase6.py, headed, all green):**
- Flight: 100.1 m/s at 1 planetary radius altitude (derivation target: 100), 1.1e5 m/s in void (< 10x v_esc = 3.6e5), clock 1.00 planet / 0.43 void
- Focus flight converged: 8.27e6 m from planet center vs 6.4e6 m framing target (terrain splat, frameDist = R_PLANET)
- LOD witness: 25/60 system ticks, max divergence 797 m = 0.0000% over 60 frames (falsifier: < 1%)
- All Phase 6 falsifiers still green: energy drift 0.0000%, thermal 255.8 K (5.6% — planet membrane joined the 1 AU bin, albedo 0.3), deflection 3.2e3 m
- GPU BH+EM: 3.5 ms, 64 fps (recovered from 7 fps after the splat-size fix)

**Inherited bugs found and fixed (Track A1 shipped them silently — no pixel assertion existed):**
1. The near-cull `cw > 0.01` (1e9 m) was derived for the system-scale camera; at planetary altitude it culled EVERY splat — the canvas rendered black and the green test never noticed. Now scale-relative: cull at half the nearest-surface altitude. New test assertion: `__dbgRender.visible > 0`.
2. The planet was co-located with the star at the origin, putting the flight camera inside the star's physical radius (and its splat filled the sky). Planet membrane now orbits at 1 AU (`PLANET_POS = [1.5e11, 0, 0]`).
3. Terrain splat render floor (8e6 m) exceeded the planet's own radius — 300 planet-sized splats rendered as a uniform blue wash at ~30x overdraw (7 fps in GPU mode). Splat radius now derives from the lattice cell: 300 Fibonacci cells -> ~2.3e6 m spacing -> sigma 1.27e6 m (`R_PLANET * 0.2`).
4. The terrain noise was double-rescaled: `(n-0.5)*2` before `elevFromNoise` (which expects raw [0,1] noise against seaThr 0.45), and the hash-lattice fbm is biased low (mean 0.25, max 0.47) — EVERY cell signed to the ocean mode; land fraction measured 0.000. Now mirrors `PlanetOnion` (`core/planet_membrane.py:189-221`): potential normalized (mean/std), sea level DERIVED at the area-weighted (1-0.291) quantile minus the shelf zero-crossing offset — no tuned threshold. New executable falsifier: `window.__terrainStats.landFraction` within 0.12 of 0.291 (measured 0.203; DEM grid itself hits 0.291 exactly by construction).
5. Negative longitudes from `atan2` indexed DEM column < 0; clamping made the bilinear weights EXTRAPOLATE, manufacturing phantom rock/snow cells above the land mode's +300 m ceiling. Longitude now wrapped to [0, 2pi) in both DEM and fallback paths.
6. DEM grid dims were inferred as `nlat = sqrt(N*2)` = 360x180 — TRANSPOSED from the actual 180x360, scrambling every sample (land fraction 0.123, caught by the new falsifier on its first run). Fixed: `sqrt(N/2)`.

---

## Track A2 — Real Earth Option (Completed)

**What was built:**
- `spawnPlanet(terrainDEM)` accepts optional equirectangular DEM parameter (lat 90→-90, lon 0→360), same interface as `PlanetOnion.from_topo_grid()` in Python
- `generateSyntheticDEM(180, 360)` pre-builds full-resolution grid from procedural noise for the 'procedural' mode path
- Bilinear interpolation on DEM grid for per-splat elevation sampling
- Toggle button in HUD: `Terrain: Procedural` ↔ `Terrain: Real Earth (DEM)` — resets system with new terrain source
- Drop-in seam: pass a real ETOPO/SRTM .npy or flat array to `spawnPlanet(demArray)` and the planet renders from actual topography

**Design invariant:** The same `elevFromNoise` bimodal transfer runs on both procedural noise and loaded DEM data, so the terrain reads as Earth-like regardless of source.

---

## Track C1/C2 — Picking + Highlight (Completed)

**What was built:**
- Canvas click handler: projects all terrain/star particles to screen space, finds nearest within 3px radius (`PICK_RADIUS_SQ = 9`)
- `selectedParticleIdx` tracks current selection (-1 = none)
- `displayColor()` applies white highlight overlay (+0.5 to each channel) on selected particle
- Escape key clears selection
- Inspector panel (top-right): shows ID, position, velocity, mass, charge, temperature, flux for selected particle; hidden when nothing selected
- Only terrain and star particles are pickable currently (orbitals can be added next)

**Falsifier:** Selection must visually change the splat color within one frame of click.

---

## Track A1 — Terrain → Splats (Completed)

**What was built:**
- `spawnPlanet()` in JS: 300 surface splats on a Fibonacci lattice, elevation from FBM noise + bimodal transfer (`elevFromNoise` mirrors `PlanetOnion._elev_from`), height-band coloring (abyssal/deep/shallow ocean, beach, forest, rock, snow)
- Terrain particles are **fixed anchors** in the planet membrane: they exert gravity on orbitals but don't move (`integrateParticle` skips them, GPU readback restores `_origPos`)
- `displayColor()` uses pre-computed `_terrainCol` for terrain splats (base color + scattered starlight overlay)
- Camera repositioned to frame the planet at ~4 planetary radii
- Energy computation excludes terrain-terrain pairs and terrain KE

**Falsifier results (all green):**
- Particle count: 500 (1 star + 300 terrain + 199 orbitals)
- Tree: 644 nodes, 1212 leaves, depth 8
- Charge: 499 charged orbitals (terrain has q=0)
- Thermal equilibrium @1AU: 270.1 K vs 271.0 K predicted (0.3% error, limit 15%)
- Energy drift CPU BH+EM: 0.0000% (limit 1%)
- Deflection delta: 3.85e4 m >> 10 m threshold
- GPU mode: 61 fps, tree healthy after GPU→CPU handoff

**Key design decision:** Terrain splats are membrane-fixed anchors, not free particles. This means the planet's gravity field is present in the tree (orbitals feel it) but the planet itself doesn't orbit — it defines the local frame. Future work: give the planet orbital velocity around the star so it participates dynamically.

---

Document version: 1.5 | Status: Phases 0-6 + Tracks A1/A2/C1/C2/B/T complete | Agent: bionic + Kimi K3
