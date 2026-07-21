# Chimera Particle Engine

Python-native particle simulation + Unreal Engine rendering bridge.

**Compute in Python. Render in Unreal.** This is a modular extension
to the Chimera project — the existing Unreal Engine setup stays intact
in `E:\PythonChimera\Chimera\`. The particle engine lives in `ParticleEngine\`
and connects to Unreal via the MCP automation bridge.

## Architecture

```
  ┌──────────────────────┐       MCP / socket       ┌──────────────────┐
  │  ParticleEngine/      │ ←──────────────────────→ │  Unreal Engine   │
  │                        │                          │                  │
  │  core.py  — simulator  │   particle positions,    │  Instanced mesh  │
  │  kernels/ — physics    │   colors, types, props   │  Splat renderer  │
  │  control_vars.py — DSL │                          │  Viewport camera │
  │  bridge/  — transport  │                          │                  │
  └──────────────────────┘                          └──────────────────┘
```

## Quickstart (headless test, no Unreal needed)

```bash
cd E:\PythonChimera
python -m ParticleEngine.demo
```

This runs 300 frames of dust + sand particle simulation with gravity,
wind, ground collision, and surface accumulation. Prints stats every
30 frames.

## Core Concepts

### Particle State
Every particle is a 28-float record:
- Position (x,y,z), Velocity, Acceleration
- Mass, Lifetime, Type
- 4 writable control variables (props)
- Color (r,g,b), Alpha, Size

### Simulation Kernels
Kernels are vectorized NumPy functions that transform the particle
buffer in-place. They compose into a pipeline:

```python
sim = ParticleSimulator(max_particles=100_000)
sim.add_kernel(gravity_kernel, "gravity")
sim.add_kernel(wind_kernel, "wind")
sim.add_kernel(accumulation_kernel, "accumulation")
sim.step(dt=1/60, control_vars={"gravity": (0,0,-162), "wind_vector": (30,10,5)})
```

### Control Variables
Named, typed, bounded parameters that kernels read. Beat scripts,
the dialectical design Council, and the emergent workflow engine can
tune these to observe system behavior:

```python
reg = default_physics_registry()
reg.set("gravity", (0, 0, -162))          # Moon
reg.set("wind_strength", 2.5)              # Storm
reg.set("accumulation_rate", 0.2)          # Fast dust buildup
cvars = reg.snapshot()
sim.step(dt, cvars)
```

### Particle Types
| Type       | Use Case                                    |
|------------|---------------------------------------------|
| `dust`     | Surface accumulation, atmospheric haze      |
| `sand`     | Regolith, erosion, footstep particles       |
| `water`    | Fluids, splashes                            |
| `social`   | NPC relationship / intent flow              |
| `resource` | Economy / trade flow particles              |
| `atmosphere` | Volumetric cloud/fog particles            |
| `shellmite`  | Erisaid educational specimen particles     |

## Integration with Unreal Engine

1. Ensure the Unreal Editor is running with the MCP bridge active.
2. Set bridge mode to `"mcp"`:
   ```python
   bridge = UEBridge(BridgeConfig(mode="mcp"))
   bridge.send(sim.snapshot())
   ```
3. The bridge sends particle positions, colors, and types as MCP calls
   to `manage_tools update_particle_batch`.

For the Unreal side, you need a custom actor/C++ handler that receives
`update_particle_batch` payloads and renders particles as instanced
static meshes or Niagara sprites.

## Roadmap

- [x] Core particle simulator (NumPy-vectorized)
- [x] Physics kernels (gravity, wind, collision, accumulation)
- [x] Control variable DSL with bounds and serialisation
- [x] MCP bridge for UE communication
- [x] Headless test mode
- [ ] Taichi GPU kernel acceleration
- [ ] Niagara sprite emitter integration (UE side)
- [ ] Gaussian splat renderer
- [ ] Beat script integration (drive sim from beats.json)
- [ ] Social/resource particle emergent behavior
