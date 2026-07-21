# Chimera Engine

**Standalone GPU particle physics + Gaussian splat rendering engine.**  
Zero external engine dependencies. Python for design, CUDA for runtime.

```
200K splats @ 139 FPS  |  5 particle types  |  Full 3DGS projection
```

---

## Quickstart

```bash
# Interactive object viewer (rainbow sphere, ring, wireframe)
python -m ParticleEngine.debug_viewer

# Fly through a particle world (WASD + mouse)
python -m ParticleEngine.viewer --particles 15000

# Full development cycle (Council → Beats → Helm)
python -m ChimeraEngine fullcycle

# Run beat scripts through verification gates
python -m ChimeraEngine witness --beats ChimeraEngine/beats/chimera_survival.beats.json --record

# Analyze simulation state, surface design questions
python -m ChimeraEngine analyze

# Gap analysis between design intent and reality
python -m ChimeraEngine helm
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Chimera Engine                      │
├─────────────────────┬───────────────────────────────┤
│  ChimeraEngine/      │  ParticleEngine/              │
│  (workflow layer)    │  (GPU runtime)                │
├─────────────────────┼───────────────────────────────┤
│  cli.py              │  gpu_pipeline.py  13 kernels  │
│  beats.py            │  viewer.py        flythrough  │
│  gates.py            │  debug_viewer.py  object view │
│  helm.py             │  camera.py        3DGS proj   │
│  council.py          │  splat.py         p→s convert │
│  world.py            │  reflect.py       physics     │
│  beats/              │  control_vars.py  DSL         │
└─────────────────────┴───────────────────────────────┘
```

### GPU Pipeline (13 CUDA Kernels)

```
Upload particles ─→ _sim_gravity ─→ _sim_wind ─→ _sim_boundary
(N×28 float32)     _sim_accumulate ─→ _sim_attract ─→ _sim_integrate
                                         │
                   _p2s (particle→splat)  │
                   _project (3DGS Jacobian)
                   _cull ─→ _inv_radii ─→ _compact
                   _gather ─→ _tiles_count ─→ _tile_offsets
                   _tiles_write ─→ _composite ─→ Download image
```

### Particle Types

| Type | ID | Behavior |
|------|----|----------|
| `dust` | 0 | Gravity, accumulation on surfaces |
| `sand` | 1 | Anisotropic splats, wind drift |
| `atmosphere` | 5 | Large low-opacity volumetric haze |
| `social` | 3 | Flows toward NPC attractors |
| `resource` | 4 | Flows toward trade post attractors |
| `water` | 2 | Reserved |
| `shellmite` | 6 | Reserved for specimens |
| `weapon_glint` | 7 | Reserved for tools |

### Control Variables

Named, typed, bounded parameters govern all behavior. Beat scripts and
the dialectical design engine tune these to observe emergent behavior.

| Variable | Type | Default | Range |
|----------|------|---------|-------|
| `gravity` | vec3 | (0,0,-981) | ±5000 |
| `wind_vector` | vec3 | (0,0,0) | ±10000 |
| `wind_strength` | float | 1.0 | 0-10 |
| `boundary_min` | vec3 | (-5000,-5000,-1000) | — |
| `boundary_max` | vec3 | (5000,5000,5000) | — |
| `boundary_restitution` | float | 0.4 | 0-1 |
| `restitution` | float | 0.3 | 0-1 |
| `accumulation_threshold` | float | 5.0 | 0-100 |
| `accumulation_rate` | float | 0.05 | 0-1 |
| `ambient_temperature` | float | 20.0 | -273–10000 |

---

## Dialectical Workflow

The Chimera methodology ported from Unreal Engine to the particle engine:

```
Council Q&A  →  Beat Scripts  →  GPU Simulation  →  Gates  →  Helm
(design)         (spec)           (runtime)          (verify)   (steer)
```

### Commands

```bash
python -m ChimeraEngine fullcycle     # Council → Beats → Helm in one pass
python -m ChimeraEngine witness ...   # Run beats, record evidence
python -m ChimeraEngine verify ...    # Witness + Verify gates
python -m ChimeraEngine analyze       # Council surfaces design questions
python -m ChimeraEngine helm          # Gap analysis
```

### Beat Script Format

```json
{
  "demo": "test_name",
  "loop": 0,
  "settle_s": 3,
  "beats": [{
    "name": "beat_name",
    "features": ["Feature_Name"],
    "actions": [
      {"set_var": {"gravity": [0, 0, -981]}},
      {"wait": 2.0}
    ],
    "expects": [
      {"particle_count": {"type": "dust", "min": 500}},
      {"prop_gt": {"type": "dust", "prop": 0, "value": 0.05}},
      {"speed_mean": {"type": "sand", "max_mag": 50}}
    ]
  }]
}
```

---

## Performance

| Particles | FPS @ 400×300 | FPS @ 1024×768 |
|-----------|---------------|----------------|
| 10K | 200+ | 120+ |
| 50K | 200 | 80 |
| 100K | 178 | 60 |
| 200K | 139 | 40 |
| 500K | 77 | 27 |

NVIDIA GPU required. Tested on consumer hardware.

---

## Project Structure

```
E:\PythonChimera\
├── ChimeraEngine/          Workflow layer (beats, gates, helm, council)
│   ├── cli.py              Unified command line
│   ├── beats.py            Beat script executor
│   ├── gates.py            Witness + Verify gates
│   ├── helm.py             Gap analysis
│   ├── council.py          Dialectical Q&A
│   ├── world.py            World config (spawn zones, attractors)
│   ├── render_scene.py     Cinematic scene renderer
│   └── beats/              .beats.json specs (3 files, all passing)
├── ParticleEngine/         GPU runtime (13 CUDA kernels)
│   ├── gpu_pipeline.py     Full GPU pipeline (sim → splat → project → composite)
│   ├── viewer.py           Interactive flythrough (matplotlib)
│   ├── debug_viewer.py     Object debug viewer (camera locked on target)
│   ├── camera.py           First-person camera + 3DGS projection
│   ├── splat.py            Particle → Gaussian splat converter
│   ├── reflect.py          Reflection physics + Gaussian scatter
│   ├── control_vars.py     Named/bounded variable DSL
│   ├── core.py             CPU particle simulator (reference)
│   ├── publisher.py        Python → JIT-native compiler
│   ├── rasterizer_gpu.py   GPU rasterizer (Numba CUDA)
│   ├── rasterizer.py       CPU rasterizer (reference)
│   ├── standalone.py       Batch render demo
│   ├── kernels/standard.py Physics kernels
│   ├── bridge/             Unreal Engine bridge (reference only)
│   └── output/             Rendered frames
└── Chimera/                Original Unreal Engine project (archived)
```

---

## Key Heuristics (from original Chimera methodology)

- **H-14**: Verified-by-injection is not playable. Real input drives verification.
- **H-21**: A verb needs behavior, not metadata. Assert world-state changes.
- **H-29**: Attribute rejection to the failing expect's subsystem.
- **H-2**: Capture from actual render pipeline, not desktop screenshots.
- **H-32**: When telemetry returns defaults, check backend attachment first.

---

## Requirements

- Python 3.14+
- NumPy, Numba (CUDA), Matplotlib
- NVIDIA GPU with CUDA toolkit
- Pillow (for image save)

---

## License

Proprietary — GhostDragonAlpha/Chimera
