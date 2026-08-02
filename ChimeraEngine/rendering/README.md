# Chimera Engine

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

**One engine. One rule. Physics governs all.**

```
Parameters → Physics → Splats → GPU Render
   (clay)     (kiln)   (form)    (view)
```

## Quickstart

```bash
python -m ParticleEngine.oak_demo        # Oak tree viewer
python -m ParticleEngine.debug_viewer    # Object debug viewer  
python -m ParticleEngine.viewer          # Fly through world
python -m ChimeraEngine fullcycle        # Council → Beats → Helm
python -m ChimeraEngine witness --beats <path> --record
```

## Architecture

```
ChimeraEngine/     Workflow (beats, gates, helm, council)
ParticleEngine/    GPU runtime (13 CUDA kernels, 200K @ 139 FPS)
WorldModel/        ML + Physics + Nanite + Infinite
  ├── clay.py           Moldable parameter system
  ├── warp_train.py     GPU data gen (Warp) + VAE training
  ├── physics_tree.py   Physics-informed tree generator  
  ├── nanite.py         Hierarchical cluster LOD
  ├── infinite.py       Spatial hashing + region streaming
  ├── splat_io.py       Standard 3DGS .ply I/O
  ├── model.py          SplatVAE architecture
  └── universe.py       Modular physical laws
```

## The Clay System

Every object is defined by a parameter vector. Physics fills in the details. VAE learns parameter distributions.

```
Tree = 17 params → Physics → Splats → GPU Render
Ship = 24 params → Physics → Splats → GPU Render
```

Mold the parameters, physics does the rest.

## Dialectical Workflow

```
50 images → 17 questions → Parameter VAE → Generated tree → GPU render
    │              │               │               │
  Wallhaven    Image→param     Learned dist    New objects
  Any source   extraction     8d latent       World seed
```

## Performance

| Particles | FPS @ 400×300 | FPS @ 1024×768 |
|-----------|---------------|----------------|
| 10K | 200+ | 120+ |
| 50K | 200 | 80 |
| 100K | 178 | 60 |
| 200K | 139 | 40 |

NVIDIA RTX 4090, CUDA 12.9.

## Data Sources

- Wallhaven API: 545 images × 10 categories
- HuggingFace Voxel51: 3DGS scenes (truck, garden, playroom)
- Inria 3DGS: Garden, treehill, bicycle scenes
- Polycam/Sketchfab: Individual object captures

## Requirements

Python 3.14+, NumPy, Numba CUDA, Matplotlib, Pillow
PyTorch 2.13+ CUDA, Warp 1.15+, scipy, requests
NVIDIA GPU with CUDA 12.9+
