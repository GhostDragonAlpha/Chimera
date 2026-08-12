# Chimera Engine — WebGPU Spike (`spike.html`)

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.

## Overview

`spike.html` is a single-file, zero-dependency WebGPU engine (~256KB, ~5,200 lines). It runs entirely in the browser with no build step — just open the file in Chrome 113+ / Edge 113+.

**Design philosophy:** AI-driven development. Glass-box (every system inspectable), hot-reload (edit code and see changes instantly), procedural-first (everything generated, nothing hand-crafted).

## Feature Status: 178/178 complete

See [CHECKLIST.md](CHECKLIST.md) for the full breakdown. Every item across all 12 categories is checked off.

### Architecture Highlights

- **Entity/Component System** — integer ID pool, struct-of-arrays storage, filter-by-type queries
- **Hot Reload Pipeline** — shader recompile on change, system replacement at runtime, entity state preserved
- **Live Inspection** — click any entity to inspect components, edit values live, toggle systems on/off
- **GPU Rendering** — tile-based rasterizer, GPU frustum culling, dynamic resolution scaling
- **Post-Processing Stack** — bloom, SSAO, chromatic aberration, vignette, depth of field, motion blur, film grain, lens distortion
- **N-body Physics** — gravitational simulation with contact resistance, spring constraints, hinge joints
- **Procedural Generation** — noise functions (Perlin, Simplex, Worley), heightmap terrain, texture splatting, Voronoi diagrams, L-systems
- **Debug Tools** — wireframe/depth/velocity overlays, component heatmap, draw call counter, GPU timestamp report, uniform buffer dumper
- **Save System** — IndexedDB persistence, timestamped saves with rollback, clipboard copy/paste, git-compatible JSON format with diff support
- **AI Interface** — world state API, entity queries, constraint language parser, A/B test runner, parameter sweep, regression detection
- **Platform Support** — performance tier detection, touch controls, reduced feature mode, battery awareness

## Quick Start

```bash
# Open in Chrome/Edge with WebGPU enabled
chrome --enable-unsafe-webgpu spike.html
# or edge --enable-unsafe-webgpu spike.html
```

### Keyboard Controls

| Key | Action |
|---|---|
| `WASD` / Arrows | Move camera |
| Mouse drag | Orbit camera |
| Scroll | Zoom in/out |
| `T` | Enter spawn mode |
| `P` | Toggle parameter panel |
| `D` | Toggle debug panel |
| `H` | Show API reference |
| `Shift+G` | Entity graph view |
| `Shift+T` | Interactive tutorial |
| `Space` | Pause simulation |
| `>` / `<` | Step forward/backward |
| `Ctrl+S` | Save scene |
| `Ctrl+L` | Load scene |

### API Console Access

Everything is exposed on `window.__` for AI consumption:

```javascript
// Get performance metrics
const m = window.__ai.getPerformanceMetrics();
console.log(m.fps, m.entities, m.resolution);

// Spawn a cluster of particles
window.__ai.spawnFromDefinition({type:'cluster', count:100, radius:10});

// Save current scene
await window.__saveSystem.save('my_scene');

// Run physics stress test
const result = await window.__stressTest.run(10000, 5000);
console.log(result.spawned, result.frames, result.survived);

// Generate terrain LODs from a mesh
const lods = window.__lodGenerator.generate(myMesh, 3);

// Record input for replay
window.__replaySystem.startRecording();
// ... play around ...
window.__replaySystem.stopRecording();
console.log('Recorded', window.__replaySystem.getFrameCount(), 'frames');
```

## File Structure

| Part | Lines | Purpose |
|---|---|---|
| HTML/CSS | ~150 | Canvas, HUD panels, controls |
| WGSL Shaders (~12) | ~400 | Compute, render, post-process passes |
| Core Engine | ~800 | Entity/Component system, world, systems |
| Physics | ~600 | N-body gravity, constraints, collision |
| Rendering Pipeline | ~700 | GPU buffers, pipelines, draw calls |
| Post-Processing | ~500 | Bloom, SSAO, DOF, chromatic aberration, etc. |
| Procedural Generation | ~400 | Noise, terrain, scatterer, LOD, booleans |
| AI Interface | ~300 | World state API, queries, prompt parsing |
| Save/Load | ~200 | IndexedDB, clipboard, git format, change tracking |
| Platform Features | ~400 | Touch, battery, performance tier, replay |
| Debug/UI | ~300 | Panels, inspectors, documentation |
| Tests | ~150 | Shader compile, determinism, energy tests |

## Verification

- **JS syntax**: All brackets/braces/parens balanced across all `<script>` blocks
- **Engine tests**: 9/9 passing (`tests/test_engine_gates.py`)
- **All features exposed on `window.__`** and documented in CHECKLIST.md

---

*Built as a single self-contained HTML file. No build step, no dependencies, no server required.*
