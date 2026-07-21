# Chimera Engine

**GPU particle physics + Gaussian splat rendering + ML world model.**

```
python -m ParticleEngine.oak_demo        # Procedural oak tree
python -m ParticleEngine.debug_viewer    # Object debug viewer  
python -m ParticleEngine.viewer          # Fly through particle world
python -m ChimeraEngine fullcycle        # Council → Beats → Helm
```

---

## Quickstart

```bash
# Viewers
python -m ParticleEngine.debug_viewer     # Rainbow sphere + ring + cube
python -m ParticleEngine.oak_demo         # Physics-informed oak tree
python -m ParticleEngine.viewer           # WASD flythrough

# Development workflow
python -m ChimeraEngine fullcycle         # Full verify cycle (3/3 beats passing)
python -m ChimeraEngine witness --beats <path> --record
python -m ChimeraEngine analyze           # Council design questions
python -m ChimeraEngine helm              # Gap analysis

# ML pipeline (requires PyTorch + CUDA + Warp)
python WorldModel/warp_train.py 500       # GPU: generate 500 trees, train VAE, sample
```

---

## Architecture

```
ChimeraEngine/          Workflow layer (beats, gates, helm, council)
ParticleEngine/         GPU runtime (13 CUDA kernels, 200K @ 139 FPS)
WorldModel/             ML training + Nanite LOD + infinite worlds
  ├── warp_train.py     GPU data generation (Warp) + VAE training (PyTorch)
  ├── physics_tree.py   Physics-informed tree generator
  ├── nanite.py         Hierarchical cluster LOD tree
  ├── infinite.py       Spatial hashing + region streaming
  ├── splat_io.py       .ply file I/O (standard 3DGS format)
  ├── model.py          SplatVAE architecture
  └── universe.py       Modular physical laws
```

### GPU Pipeline (13 CUDA Kernels)

```
Upload → gravity → wind → boundary → accumulate → attract → integrate
   │
   ├→ particle→splat → project (3DGS Jacobian) → cull → inv_radii
   └→ compact → gather → tiles_count → tile_offsets → tiles_write → composite
                                                                        │
                                                                   Download image
```

---

## Getting Real 3DGS Training Data

To get photorealistic results, download real 3D Gaussian splat captures:

### 1. Inria 3DGS Scenes (650MB — contains garden, treehill with real trees)
```
https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/
→ Click "Scenes" → Download → Extract .ply files
```

### 2. Polycam Free Captures (individual tree .ply files)
```
https://poly.cam/explore
→ Search "tree", "oak", "forest" → Download as .ply
```

### 3. Sketchfab 3DGS Models
```
https://sketchfab.com/search?q=gaussian+splat+tree&type=models
→ Filter by downloadable → Download .ply
```

### 4. Box.com Free CC0 Dataset (real 3DGS captures, no restrictions)
```
https://app.box.com/s/itozvq23jh4av2a5hg08d7qevdbi93ii
→ Download individual .ply files
```

### 5. Capture Your Own
- Install **Postshot** (free) or **Polycam** (phone app)
- Take 50-100 photos of a real tree from all angles
- Process → export as .ply
- Feed into `WorldModel/splat_io.load_ply()`

### Using the data
```python
from WorldModel.splat_io import load_ply, normalize_cloud, save_ply

cloud = load_ply("real_oak.ply")           # Load real capture
cloud = normalize_cloud(cloud)              # Center and scale
# Train VAE on multiple real tree clouds...
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

NVIDIA RTX 4090, CUDA 12.9. Numba CUDA + Warp + PyTorch.

---

## Particle Types

| Type | Behavior |
|------|----------|
| `dust` (0) | Gravity, surface accumulation |
| `sand` (1) | Anisotropic splats, wind drift |
| `atmosphere` (5) | Large low-opacity volumetric haze |
| `social` (3) | Flows toward NPC attractors |
| `resource` (4) | Flows toward trade post attractors |

## Control Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `gravity` | vec3 | (0,0,-981) | Gravity vector (cm/s²) |
| `wind_vector` | vec3 | (0,0,0) | Wind direction/magnitude |
| `wind_strength` | float | 1.0 | Wind force multiplier |
| `boundary_restitution` | float | 0.4 | Bounce energy retention |
| `accumulation_rate` | float | 0.05 | Dust/sand settling rate |
| `ambient_temperature` | float | 20.0 | Thermal equilibrium |

---

## Requirements

- Python 3.14+, NumPy, Numba (CUDA), Matplotlib, Pillow
- PyTorch 2.13+ with CUDA (for ML training)
- Warp 1.15+ (NVIDIA GPU compute)
- NVIDIA GPU with CUDA 12.9+ (RTX 4090 tested)
