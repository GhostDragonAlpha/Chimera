# Chimera Engine — Vulkan N-Body Renderer

A standalone C++ proof-of-concept renderer built with **Vulkan 1.2** and a GPU compute shader for real-time gravitational N-body simulation. Designed as the foundation for a future WebGPU/WGSL replacement path (see [RENDERER_V2.md](../RENDERER_V2.md)).

---

## What It Does

Simulates **1,200 particles** interacting via Newtonian gravity with contact resistance and spring-bond forces, renders them as soft Gaussian splats on a dark sky background — all in real time at 60 fps.

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Validation layers (debug report callback) | ✅ Complete |
| 2 | GPU compute dispatch for N-body forces | ✅ Complete |
| 3 | Persistent buffer residency (dirty-flag upload) | ✅ Complete |
| 4 | Mouse/keyboard camera input | ✅ Complete |

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     Main Loop (60 fps)                        │
│                                                               │
│   particles[] (CPU)                                           │
│        │                                                      │
│        ▼ push_state()                                         │
│   GPU: pos_buf_ ─┐                                            │
│            vel_buf_  │                                        │
│                   ▼                                        │
│           dispatch_compute()                               │
│         compute.glsl (O(n²) on GPU, 256-thread groups)     │
│                  ▲   │                                       │
│                  │   ▼ readback staging                      │
│            acc_buf_ ← new velocities                        │
│                   │                                          │
│        CPU: integrate positions (Euler step)                │
│                   │                                          │
│                   ▼ frame()                                 │
│   GPU: render.vert → render.frag (Gaussian splat points)    │
│                   │                                          │
│                   ▼ present                                  │
│            Win32 swapchain                                 │
└───────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **Hybrid compute/CPU integration**: The GPU dispatches forces and updates velocities via the Verlet-style shader; CPU reads back velocities, integrates positions, then re-uploads. This avoids complex storage-buffer readback synchronization.
- **Dirty-flag residency**: Position buffers are only reallocated when particle count or configuration changes — not every frame. Velocity data uploads on first call or count change.
- **No external dependencies**: Win32 native windowing; no GLFW, no ImGui, no assimp. Only the Vulkan SDK is required.
- **Single command pool** for staging uploads; per-frame descriptor sets in a pool.

---

## Controls

| Input | Action |
|-------|--------|
| **Left-mouse drag** | Orbit camera around target point |
| **Scroll wheel** | Zoom in / out |
| **Right-mouse drag** | Pan view offset |
| **WASD / Arrow keys** | Move look-at target |
| **Q / E** | Move target vertically (down/up) |
| **Space (hold)** | Zoom out smoothly |
| **Ctrl (hold)** | Zoom in smoothly |
| **R** | Reset camera to default position |

---

## Building

### Prerequisites

- **Windows 10+** with a Vulkan-capable GPU
- **[Vulkan SDK 1.4.328.1](https://vulkan.lunarg.com/sdk/home)** installed at `C:/VulkanSDK/1.4.328.1` (or adjust `VULKAN_SDK` in CMake)
- **MSVC 19.44** (Visual Studio 2022 Build Tools)
- **CMake 3.20+**

### Commands

```bash
cd e:\PythonChimera\ChimeraEngine\engine\build

cmake .. -G "Visual Studio 17 2022" -A x64   # first-time setup
cmake --build . --config Release              # build
```

The `glslangValidator` from the SDK compiles GLSL shaders to SPIR-V at build time. Shaders are copied alongside the executable on post-build.

### Output

| Artifact | Path |
|----------|------|
| Executable | `build/Release/chimera_engine.exe` |
| Vertex shader | `shaders/render.vert.spv` |
| Fragment shader | `shaders/render.frag.spv` |
| Compute shader | `shaders/compute.spv` |

---

## Shader Reference

### `compute.glsl` — N-body force kernel

```glsl
layout(local_size_x = 256, local_size_y = 1, local_size_z = 1) in;

// Bindings: pos_in (read), vel_in (read), acc_out (write), Params (uniform)
```

Each workgroup item processes one particle. Computes gravitational attraction plus contact resistance (wall repulsion + bond springs), then performs a velocity Verlet step writing new velocities to `acc_out`.

### `render.vert` — Gaussian splat billboard

Expands each point into a screen-space quad; outputs color, alpha, and local UV coordinates for the fragment shader.

### `render.frag` — Radial Gaussian falloff

Evaluates a 2D Gaussian envelope over the billboard; discards fragments with alpha < 0.004. Multiplies particle color by the envelope for soft blending.

---

## HTTP Server

A minimal embedded HTTP server listens on **port 8080**:

| Endpoint | Method | Response |
|----------|--------|----------|
| `/state` | GET | `{"n":1200}` — particle count |
| `/control` | POST | `{"ok":true}` — accept control commands |

A Python shim can query state or send commands via this interface. Shared memory ring buffers are also available for higher-throughput IPC (see `shared_mem.hpp`).

---

## File Overview

| File | Role |
|------|------|
| `engine.cpp` / `engine.hpp` | Core Vulkan engine — instance, device, pipelines, buffers, render loop |
| `main.cpp` | Bootstrap, main loop, HTTP server setup |
| `physics.cpp` / `physics.hpp` | CPU physics simulation (fallback path; GPU compute replaces the O(n²) loop) |
| `shared_mem.hpp` | Windows shared-memory ring buffer for engine ↔ Python shim IPC |
| `http_server.cpp` / `http_server.hpp` | Minimal Winsock2 HTTP server |
| `shaders/compute.glsl` | N-body force + Verlet integration compute shader |
| `shaders/render.vert` | Gaussian splat vertex shader (billboard expansion) |
| `shaders/render.frag` | Soft-point fragment shader (radial Gaussian falloff) |
| `CMakeLists.txt` | Build configuration — Vulkan SDK path, shader compilation, target linking |

---

## WebGPU Spike Engine (`spike.html`)

A single-file, zero-dependency WebGPU/WGSL engine running entirely in the browser. This is the **AI-driven development platform** — glass-box, hot-reload, procedural-first.

### Status: 178/178 features complete (CHECKLIST.md)

| Category | Items |
|---|---|
| Core Architecture | Entity/Component system, hot reload pipeline, live inspection layer |
| Rendering | Tile rasterizer, PBR materials, full post-processing stack (bloom, SSAO, DOF, chromatic aberration, vignette, motion blur, film grain) |
| Physics | N-body gravity, spring-damper, hinge joints, AABB broadphase, SAT collision, impulse resolution |
| Procedural World Building | Heightmap terrain, texture splatting, LOD generation, procedural scatterer, constraint-based placement, chunk-based terrain, erosion simulation, mesh boolean ops |
| Debug & Dev Tools | Frame budget breakdown, GPU buffer tracking, shader source viewer, uniform buffer dumper, component heatmap, wireframe/depth/velocity overlays |
| Save / Load | IndexedDB persistence, timestamped saves, clipboard copy/paste, git-based save format with diff support |
| AI Development Interfaces | World state API, entity query, constraint language parser, prompt-to-scene pipeline, A/B test runner, parameter sweep, regression detection |
| Input & Interaction | WASD + mouse orbit, selection box, right-click menu, smooth camera, multi-input (gamepad) |
| Platform | Performance tier detection, touch controls, reduced feature mode, battery awareness |
| Testing & QA | Shader compile tests, determinism test, energy conservation test, stress test, reference screenshot capture, pixel-perfect comparison |
| Documentation | Component auto-docs, shader param docs, interactive tutorial, API reference panel, code examples |

### Key APIs (all on `window.__`)

```javascript
// World
window.__world              // Entity/Component world
window.__runSystems()       // Run all systems
window.__hotReloadSystem(name, fn)  // Replace system at runtime
window.__ai.getPerformanceMetrics()  // FPS, entities, resolution
window.__ai.spawnFromDefinition(def)  // Spawn from JSON definition

// Physics
window.__physics            // Sleep threshold, sub-steps, friction
window.__addHingeJoint(a,b,axis,pivot)  // Rotational constraint
window.__addForceField(type,pos,str,len)  // Custom force fields

// Procedural
window.__voronoi            // Voronoi diagram / distance field
window.__particleEmitters   // Particle emitter system
window.__generationParams   // Live noise freq, terrain height scale
window.__meshBooleanOps     // Union/intersection/subtraction
window.__chunkTerrain       // Chunk-based terrain LOD
window.__erosionSim         // Thermal + hydraulic erosion
window.__terrainEditor      // Raise/lower/flatten terrain
window.__proceduralScatterer  // Density-based object placement
window.__constraintPlacement  // Snap-to-surface, min-distance rules
window.__lodGenerator       // Auto-generate LOD levels
window.__templateRegistry   // Template inheritance hierarchy

// Debug / Save
window.__saveSystem         // IndexedDB save/load
window.__timestampedSaves   // Timestamped saves with rollback
window.__gitSaveFormat      // Clean JSON for diffing
window.__changeTracker      // Log additions/deletions since last save
window.__uniformBufferDumper  // Readback uniform buffer contents
window.__stressTest         // Spawn N entities, verify no crash

// AI / Experiment
window.__abTestRunner       // Parallel simulation comparison
window.__paramSweep         // Systematic parameter variation
window.__regressionDetector  // Auto-detect behavioral regressions
window.__experimentHistory  // Replay past experiments

// Input / Camera
window.__inputStateSnapshot  // Capture full input per frame
window.__multiInput         // Gamepad + keyboard + mouse
window.__toggleSmoothCamera  // Lerped camera movement
window.__selectionBox       // Drag-select multiple entities
window.__rightClickMenu     // Context menu for entities
window.__replaySystem       // Record and replay input streams

// Platform
window.__performanceTier    // Auto-detect GPU tier (high/medium/low)
window.__touchControls      // Virtual joystick overlay
window.__reducedFeatureMode  // Disable expensive effects on low-power devices
window.__batteryAwareness   // Reduce update rate on battery power

// Testing / Docs
window.__referenceScreenshots  // Capture baseline screenshots
window.__pixelPerfectComparison  // Diff current vs reference render
window.__componentAutoDocs     // Generate docs from component signatures
window.__shaderParamDocs       // Hover tooltips for shader uniforms
```

### Running

Open `spike.html` directly in Chrome 113+/Edge 113+ with `--enable-unsafe-webgpu`. No build step, no dependencies — just double-click.

## Future Work

- **Vulkan → WebGPU full migration** — port the production rendering pipeline from C++/Vulkan to the WebGPU spike
- **Multiplayer** — WebSocket server integration on top of existing networking stubs
- **Mouse/keyboard camera polish** — smooth damping, edge scrolling, FOV adjustment
- **Full `/state` API** — stream full particle state as JSON or binary
- **Parameter hot-reload** — change G, dt, stiffness via HTTP without restart
- **Multi-GPU / compute queue isolation** — separate graphics and transfer queues for reduced stall

---

*Built with ❤️ using Vulkan 1.2, MSVC 2022, and a lot of patience.*
