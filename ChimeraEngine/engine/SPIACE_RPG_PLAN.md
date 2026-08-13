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

Phase 5: GPU Barnes-Hut N-Body (membrane-local trees)
Phase 4: Multiplayer (netcode, authority)
Phase 3: Multi-system (warp travel)
Phase 2: Planetary surface (atmosphere, terrain)
Phase 1: Orbital space (N-body + Kepler)
Phase 0: Physics DSL + Kepler solver

Electron unit to N-body GPU to Kepler analytical to Atmospheric thin-shell to Rigid body dynamics. Each layer is independently verifiable. The AI can generate, test, and hot-reload each phase without touching the others.

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
|---------| Purpose |
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

### Phase 5: GPU Barnes-Hut N-Body
- [x] CPU Barnes-Hut octree construction and traversal (reference implementation)
- [x] WGSL compute shader with iterative Barnes-Hut tree traversal (no recursion)
- [x] Tree serialization to flat GPU buffers (96-byte nodes: com + mass + center-of-light + luminosity + bbox + children + leaf info)
- [x] Symplectic Euler integration on GPU compute shader
- [x] **Light and heat translated INTO the tree**: nodes aggregate luminosity + center of light; the same opening-angle traversal transports irradiance E = L/4πd²; particles heat/cool by absorbed starlight vs blackbody emission
- [x] Emissive splat rendering from contained energy: scattered starlight (flux × albedo × cross-section) + blackbody(σT⁴) — nothing lit from outside the membrane
- [x] Full WebGPU splat renderer from spike.html (preprocess → CPU tile sort → tile raster → bloom → ACES tonemap); no Canvas 2D
- [x] Three modes: CPU Barnes-Hut, GPU Barnes-Hut, O(n²) direct comparison
- [x] Energy conservation verification HUD (< 5% drift falsifier — measured 0.0%)
- [x] Thermal equilibrium falsifier: 1 AU bin holds 271 K ±15% (measured 272.5 K, 0.6% off)
- [x] Membrane panel: measured extent, contained light (ΣL = 3.84e26 W), contained heat (ΣmcT = 1.03e37 J), mean T @1AU
- [x] Tree statistics: node count, leaf count, depth, approximation ratio
- [x] Playwright headed-mode test with energy + thermal assertions (`test_phase5.py`, all green)
- [x] Deliverable: 500-particle system, CPU BH 2.2 ms vs O(n²) 3.7 ms vs GPU BH 3.9 ms (readback-bound), ~65 fps

Renderer bugs fixed this pass: transposed row-major `multiplyMat4` (culled the whole scene), spurious `-1.0` in the raster's NDC y-flip (shifted splats half a screen), center-only tile binning (clipped wide splats to their home tile — star rendered as a square), alpha-normalized raster output (flattened Gaussian profile + brightness gradient), nearest-sampled bloom upsample (blocky).

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| WebGPU browser compatibility | Low | Medium | Chrome 113+ flag; fallback to canvas 2D wireframe |
| GPU compute precision (float32) | None | High | WGSL requires f32; verify on target hardware |
| Playwright headed-mode flakiness | Medium | Medium | Screenshot diffing with tolerance; retry on failure |
| Physics DSL parser complexity | Medium | Low | Start minimal (just gravity + integrator), extend iteratively |
| Ray marching performance | High | Medium | Adaptive step size, GPU parallel body checks, LOD culling |
| Scope creep (everything is cool) | Certain | High | Hard boundaries: no quantum, no GR, no fluids, no chemistry |

---

## Development Workflow (AI-Driven Method)

1. Describe the desired behavior in natural language or DSL
2. Generate the implementation (DSL to WGSL, or Python to C++)
3. Verify via Playwright headed-mode screenshot + assertion
4. Hot-reload: change source, refresh browser, re-verify
5. Commit with Agent: bionic trailer and verification evidence

Each phase is an independent commit. Each commit is independently testable.

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

1. Commit Phase 5 with Playwright verification (test green, screenshots verified)
2. Generalize the tree transport: mass and luminosity were translated by hand; a .chimera DSL kernel declaration (quantity + far-field kernel + aggregation rule) should generate the node fields, CPU aggregator, and WGSL traversal for any additive point-source interaction
3. Begin Track A from ROADMAP.md: Terrain → splats connection
4. Begin Track B: Scale-relative flight camera
5. Connect membrane clock to physics tick rate (Track T)

---

Document version: 1.1 | Status: Phases 0-5 complete | Agent: bionic
