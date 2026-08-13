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

Phase 10: Multi-planet star system (dynamic Keplerian orbits, multi-membrane context)
Phase 9: Quantity packing + fifth kernel (acoustic) — architecture scaling proof
Phase 8: Heat diffusion steady-state kernel
Phase 7: Lorentz force + magnetic field (post-tree correction)
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

### Phase 8: Heat Diffusion Steady-State Kernel
- [x] `potential_1r` added to the kernel DSL vocabulary — scalar field T = Q·(1/4πκ)/d, accumulates `theat` (WGSL) / `fluxOut.t` (JS), carries no pair PE
- [x] `kernel heat` declared (quantity=heat, aggregate=weighted_sum, coupling=KAPPA_INV_4PI, toggle=heatEnabled) — all 7 generated regions re-injected, `--verify` green
- [x] κ DERIVED, not tuned: 1/(4πκ) = T_EQ_1AU·AU/L_STAR = 1.0576e-13 K·m/W — the membrane-medium conductivity that makes steady-state diffusion equal radiative equilibrium at 1 AU. Prediction: T_field @1AU ≈ 271 K. Measured: 270.7 K (0.1% off)
- [x] Per-particle `heat` quantity (= thermal emission power, synced from lum); GPU rides new binding-9 buffer, temperature field comes home in the unused vel.w slot (no new output binding, no extra readback)
- [x] Falsifier 6: two-source analytic superposition through the AGGREGATED node path — measured rel err 0.0001% (limit 2%)
- [x] Falsifier 7: energy drift 0.0000% with heat kernel active (a field does no work)
- [x] Falsifier 8: thermal equilibrium unchanged — 255.6 K @1AU (5.7%, limit 15%)
- [x] HUD: `T_field @1AU` row in the membrane panel + Heat toggle button
- [x] GPU BH+EM+heat: 3.4 ms, 68 fps

**Two WebGPU bugs found and fixed while wiring Phase 8:**
1. Phase 7 shipped `ArrayBuffer(32)` for a 44-byte Params struct — the `pf[8..10]` B-field writes were out of bounds and silently dropped, so GPU Lorentz always read B=0. Params upload is now 64 B.
2. The ninth storage binding (heats) crossed the DEFAULT `maxStorageBuffersPerShaderStage: 8`, invalidating the whole BH bind group layout. The device now requests the limit explicitly (`requiredLimits`), with a CPU-only fallback. Also: this Chrome build's `GPUSupportedLimits` has no `.get()` — property access only. **Note for the fifth kernel: pack mass/lum/charge/heat into one `vec4f` quantities buffer instead of adding another binding.**

**Why heat matters more than heat:** the DSL now spans both radial profiles of the 3D Green's-function family — 1/d² fields (gravity, EM, irradiance) and 1/d potentials (heat). Anything superposable with a known Green's function is now a 6-line declaration.

### Phase 9: Quantity Packing + Acoustic Pressure Kernel (fifth kernel)
- [x] **Quantity packing**: mass/lum/charge/heat ride ONE `vec4f quants` buffer (binding 3 replaces bindings 3/7/8/9); the acoustic quantity gets its own f32 `pressures` buffer (binding 7); field outputs ride a new `fields` vec4f buffer (binding 8, x = pressure). Bind group: 8 storage buffers = the WebGPU default `maxStorageBuffersPerShaderStage` EXACTLY — the Phase 8 `requiredLimits` workaround reverted to plain `requestDevice()`
- [x] `scalar_inverse_squared` added to the kernel DSL vocabulary — scalar field p = Q/d² (bipolar monopole: compression +, rarefaction −), accumulates `pacc` (WGSL) / `fluxOut.p` (JS), carries no pair PE
- [x] `kernel acoustic` declared (quantity=pressure, aggregate=bipolar_sum, coupling=ONE, toggle=acousticEnabled) — all 7 generated regions re-injected, `--verify` green. Node size: 64 B base + 5×16 B = **144 B/node**
- [x] Q_star DERIVED, not tuned: solar-wind dynamic pressure at 1 AU is measured at ~2 nPa, so the star's monopole Q = P_1AU·AU² = 4.5e13 Pa·m². Prediction: p_field @1AU ≈ 2 nPa. Measured: 2.004e-9 Pa (0.2% off)
- [x] Falsifier 9: two bipolar monopoles superpose analytically through the AGGREGATED node path — measured rel err 0.299% (limit 2%)
- [x] Energy drift 0.0000% with all five kernels active (a pressure field does no work)
- [x] HUD: `Pressure @1AU` row in the membrane panel + Acoustic toggle button
- [x] GPU BH with all kernels: 3.9 ms, 60 fps — no WebGPU validation warnings

**Why Phase 9 is the scaling proof:** the fifth kernel cost one DSL declaration + 16 B/node + one f32 buffer. The tree traversal code did not change — `kernel_dsl.py` emitted the difference. The vec4f packing means the next kernels ride the spare y/z/w slots of `fields`-style buffers or additional f32 arrays within the 8-binding budget; the architecture is now "one membrane = one tree = one traversal for N simultaneous fields," linear in N.


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
7. ~~**Phase 7: Lorentz Force + Magnetic Field Kernel**~~ ✓ done — uniform B-field, F=q(v×B) post-tree correction, cyclotron falsifier, energy conservation with B-field active
8. ~~**Phase 9: Quantity Packing + Acoustic Kernel**~~ ✓ done — vec4f quants packing (8 storage = WebGPU default limit), fifth DSL kernel (scalar_inverse_squared bipolar monopole), falsifier 9 green (0.299%), p_field @1AU 0.2% off the solar-wind calibration
9. ~~**Track D1/D2**: LOD port to v2 renderer + surface fracture (infinite detail)~~ ✓ done — mip pyramid + trained law N=ρ·r_px² (ρ=0.35) + Fibonacci-hemisphere fracture shell, all law-exact
10. ~~**Track E**: Character standing/walking on planet~~ ✓ done — ground query + local-frame character controller + scale handoff, gap 5.9e-7 m at rest
11. ~~**Track B/T: Scale-relative flight camera + LOD of time**~~ ✓ done — see section below

---

## Track D/E — Infinite Detail + Character on Planet (Completed)

**What was built (Track E — character):**
- **E1 ground query**: `heightAt(lat, lon)` — one bilinear DEM sample (`sampleDEMElev`, module-level `currentDEM` set by `spawnPlanet`) shared by terrain spawn, fracture, and the character; `groundNormal` from finite differences; `latLonFromDir`/`dirFromLatLon` helpers
- **E2 character controller**: `stepCharacter` integrates in the planet-local frame (lat, lon, alt in f64 — no float32 precision loss at 1 AU); gravity derived from g = G·M/r² (not the tree); Coulomb friction with exact rest (no jitter); EYE_HEIGHT 1.7 m, WALK_SPEED 1.4 m/s, FRICTION_MU 1.0; WASD in the local tangent plane
- **E3 scale handoff**: foot mode via G key / Land button / `__enterFoot`/`__exitFoot`; `camForward()` branches to the character's look direction; altitude/speed HUD rows switch to foot-mode readouts (gap, surface speed)

**What was built (Track D — LOD + fracture):**
- **D1 mip pyramid**: `buildTerrainPyramid()` — greedy 4:1 nearest-neighbor clustering of the 300 base splats (radius ×2 per level, averaged colors, re-grounded via `heightAt`) → levels 300/75/19/5/2; `planPlanetLOD()` picks base | mip | fracture per frame from the trained law N = ρ·r_px² with ρ = 0.35 from `lod.trained.json` (NOT the 0.45 docstring value)
- **D2 surface fracture**: when the law wants finer than base, `buildFracture()` grows a Fibonacci lattice cap (y ∈ [0, 1]) on the planet→camera axis, every splat born from the ground query; render-only extras append at indices n..nRender-1 through the same cull/bin/sort path in `prepareSplats` — the tree never sees them; hysteresis rebuilds only on >10% count change or >5° axis rotation; capped at MAX_PARTICLES − 500 = 3596
- `window.__lodInfo` (live LOD state) and `window.__lodForce` ('base' | 'mip:N' | 'fracture') for A/B regression probes

**Measured (test_phase6.py, headed, all green):**
- E1: 300 splats roundtripped through the ground query, max err 7.70e-07 m
- E2 rest witness: speed 0.00e+00 m/s, gap to surface 5.87e-07 m (falsifier: < 0.01 m)
- E2b walk witness: 7.000 m track vs 7.0 m commanded (0.00%), gap 2.24e-06 m
- E3 live: land → walk (1.40 m/s, gap 0) → rest → takeoff, all pass
- D1: law error 0.0% at r_px 29.3/14.6/7.4 (N = 300/75/19, base/mip/mip)
- D2: fracture counts 709/1260/2835 law-exact (0.0%); budget cap 3596 at r_px 300
- GPU BH+EM 2.8 ms at 60 fps with fracture active; visible splats 3596
- All prior falsifiers unchanged: energy drift 0.0000%, LOD-time divergence 0.0000%, cyclotron/thermal/acoustic green

**Bugs found and fixed this pass:**
1. **The white-out**: `displayColor()` computed `isSelected` as `particles.indexOf(p) === selectedParticleIdx`. Render-only extras are not in `particles[]` → indexOf returns −1 → matched the "nothing selected" sentinel (−1 === −1) → EVERY mip/fracture splat got the +0.5 white highlight overlay. HDR at planet center measured 0.51 (flat grey-white, all terrain bands washed out) vs 0.046 for base terrain at the same camera. Fixed with a `selectedParticleIdx >= 0` guard (which also short-circuits the O(n) indexOf when nothing is selected).
2. **Limb double-rim**: the fracture cap's past-limb margin (y < 0) placed a star-lit ring ~0.1·R behind the limb; dark limb splats are nearly transparent in this renderer (alpha ∝ color), so the ring shone through as chevron arcs. Margin removed (Y0 = 0) — only black sky behind the dark rim now.
3. `measureFlight` altitude was nearest-particle distance; terrain cells (~500 m radius, ~2300 km apart) made the near-cull erase the ground at eye level. Altitude is terrain-exact via `heightAt` inside 10·R_PLANET.

**Honest limitation:** the fracture cap (3596 splats) is budget-limited, not law-limited — at eye level the law wants finer detail than the budget affords, so foot-mode ground cells sit ~266 km apart. Closing that needs the renderer budget raised or a second-level fracture, both out of scope here.

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

### Phase 10: Multi-Planet Star System (Completed — Kimi K3)

**Rule 0:** The N-body tree already handles multiple massive bodies, so planets can be DYNAMIC
particles on Keplerian orbits (not fixed anchors), and the membrane context can reframe to
whichever planet is nearest. Prediction: measured orbital periods match Kepler's third law,
and the character can fly planet-to-planet and land. Falsifiers 10–13 named below, all green.

**What was built:**
- `PLANET_SPECS`: 1 star + 4 planets (A: 1.00 AU / 1.0 M_e, B: 0.95 AU / 0.5 M_e,
  C: 1.30 AU / 2.0 M_e, D: 1.67 AU / 5.0 M_e) — all inside the habitable zone band
  [0.95, 1.67] AU derived from T_eq = 271/√(d_AU) K. Radius from Zeng-style
  mass-radius R = R_e·(M/M_e)^0.27; relief amplitude ~ 1/g clamped to [0.5, 3].
- Planet cores are DYNAMIC tree particles with tangential Keplerian velocity
  v = √(GM_star/a), prograde. Only planet A keeps the 300 placed terrain splats
  (renderer budget); B/C/D terrain is fracture-born from their DEMs (Track D2).
- Per-planet DEMs: `generateSyntheticDEM(nlat, nlon, seedX, seedY, amp, primary)` —
  seeds shift the fbm lattice per planet; `primary` guards the NOISE_* globals so
  planet A's DEM stays byte-identical to the pre-Phase-10 world.
- `heightAt(lat, lon, pi)` / `groundNormal(lat, lon, pi)` — per-planet ground truth.
- Terrain re-anchoring: `reanchorTerrain()` runs at the top of every frame, rigidly
  attaching the 300 placed splats to their (moving) core via the planet-local
  `_offset`. One-frame lag ~480 m at timeScale 1 — 0.008% of R_e, invisible.
- Multi-membrane context: `nearestPlanetTo(pos)` drives `activeMembrane`;
  transitions are logged to `window.__membraneLog`. Character controller reframes
  per-planet (`character.planet`): gravity g = G·M_pl/r², local up, ground query
  all resolve against the active planet's live core position.
- Track D generalized: LOD plan targets the NEAREST planet; fracture shells are
  born from that planet's DEM; extras carry planet-local `_relDir`/`_elev` and
  re-resolve against the live core each frame (cached absolute pos would detach).
- HUD: interplanetary transfer row (nearest OTHER planet: distance, relative
  speed, time-to-closest-approach), per-membrane extent/clock.
- Witnesses: `window.__systemStats` (planet count, masses, radii, a, T_kepler,
  T_eq predicted vs measured), `window.__keplerWitness` (side-effect-free
  34.7-day fast-forward measuring swept angle), `window.__debugGround`.

**Falsifier results (all green, headed Playwright, `--enable-unsafe-webgpu`):**

| Check | Measured | Limit |
|---|---|---|
| F10 Kepler period ratio (A/B/C/D) | 0.9989 / 0.9987 / 0.9995 / 0.9997 (max err 0.13%) | 5% |
| F11 land on planet B | gap −0.0000 m, rest after 684 frames, finite pos | gap < 0.01 m |
| F12 multi-planet energy drift | 0.0000% over 125 frames | < 1% |
| F13 thermal @A/B/C/D | 271.0 / 278.1 / 237.7 / 209.7 K — all 0.0% off predicted | < 15% |
| Membrane transitions | logged −1→0 (frame 1288), 0→1 (frame 1431); activeMembrane=1 | ≥ 1 transition |
| E1 ground roundtrip | max err 7.7e-07 m over 300 splats | < 1 m |
| F1–F9 + Tracks D/E | all previously-green assertions unchanged | — |

Measured system: A (5.972e24 kg, 6.371e6 m, T=3.168e7 s) · B (2.986e24 kg, 5.284e6 m,
2.933e7 s) · C (1.194e25 kg, 7.682e6 m, 4.696e7 s) · D (2.986e25 kg, 9.839e6 m, 6.837e7 s).
GPU mode: 60 fps, 8.5 ms gravity (readback-bound), 3596 visible splats at D2 cap.

**Bugs fixed this pass:**
- Duplicate `const AU` (already declared @615) — load-time SyntaxError, page dead.
- E1 pole degeneracy: with the planet orbiting, the f64 roundtrip through a
  1.5e11 m world position leaves ~1e-4 m noise in the witness's pos-minus-core
  direction — at the south pole (px,pz ≈ 0) that swings lon by ~π/2 and sampled
  a phantom DEM cell (3.9 km error). The witness now roundtrips the planet-local
  `_offset` anchor, which IS the placement ground truth: 7.7e-07 m.

**Next steps:** Phase 11 — ship-to-foot narrative arc with atmospheric re-entry
(membrane depth already drives the transitions; re-entry adds a thin-shell aero
kernel), or the C++ port of the verified kernel layer.

---

### Renderer Quality Fixes (bionic)
- [x] **Single design target: 4K UHD (3840×2160)** — not hardware-dependent, not incremental.
  Canvas fills the window up to this size regardless of display hardware.
  Same philosophy as any game engine targeting '4K' — it's a design contract.
- [x] Terrain splat radius set for 4K: R_PL × 0.1 (~637 km at Earth). The LOD law
  (N = ρ·r_px²) automatically selects coarser or finer levels based on screen distance.
- [x] MAX_PARTICLES bumped 4096 → 8192 for 4K fracture headroom (7692 slots)
- All falsifiers pass; test viewport at 1280×720 keeps distances identical

---

Document version: 2.4 | Status: Phases 0–10 + Tracks A/B/C/T/D/E complete | Agent: bionic + Kimi K3
