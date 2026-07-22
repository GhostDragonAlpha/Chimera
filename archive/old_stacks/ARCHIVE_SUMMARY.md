# Chimera Engine Rendering Pipeline - Old Stacks Archive

## Summary

This directory contains the old, fragmented rendering stacks that were consolidated into a unified system. The consolidation was necessary because:

1. **Four separate splat stacks** existed with incompatible formats
2. **CPU↔GPU syncs every frame** killed performance (540ms at close range)
3. **Distance-based LOD** instead of screen-space error caused bugs at both close and far ranges
4. **Zero tests** for the engine itself

## Archived Files

### 1. `Chimera/core/splat_gpu.py`
- **Purpose**: Original GPU rasterizer implementation (Numba CUDA)
- **Why archived**: Functionality merged into unified `ChimeraEngine/renderers/gpu_rasterizer.py`
- **Key improvements in new version**:
  - GPU-resident splat pool (upload once, not every frame)
  - Integrated with cluster tree for budgeted LOD selection
  - Eliminated per-frame CPU↔GPU syncs

### 2. `Chimera/core/splat_lod.py`
- **Purpose**: CPU-based spatial LOD merger using exponential distance mapping
- **Why archived**: Replaced by screen-space error-based budgeted cut in `ChimeraEngine/loD/budgeted_cut.py`
- **Key improvements in new version**:
  - Hard frame-cost ceiling via pixel budget (not unbounded)
  - Fixes both close-range (540ms) and far-range (1 splat at 50km) bugs
  - Integrates with cluster tree for hierarchical LOD

### 3. `ParticleEngine/splat.py`
- **Purpose**: Particle → SplatState conversion utilities
- **Why archived**: Format incompatible with canonical `GaussianSplatCloud`; functionality merged into unified format system
- **Key improvements in new version**:
  - Single canonical format (`ChimeraEngine/core/gaussian_splat_cloud.py`)
  - Compatible with standard 3DGS .ply ecosystem

### 4. `ChimeraEngine/renderer.py`
- **Purpose**: Basic camera/render params (not actual splat rendering)
- **Why archived**: Redundant; replaced by unified renderer architecture
- **Key improvements in new version**:
  - Clear separation of concerns: format, LOD, rasterizer, gates

## New Architecture

The consolidated system has four clear layers:

1. **Format Layer** (`ChimeraEngine/core/gaussian_splat_cloud.py`)
   - Canonical `GaussianSplatCloud` data structure
   - GPU-resident `SplatPool` for efficient memory management

2. **LOD Layer** (`ChimeraEngine/loD/cluster_tree.py`, `budgeted_cut.py`)
   - Nanite-style cluster tree construction
   - Budgeted cut algorithm with global pixel budget

3. **Renderer Layer** (`ChimeraEngine/renderers/gpu_rasterizer.py`)
   - Unified GPU rasterizer using Numba CUDA
   - Integrates LOD selection and GPU residency

4. **Quality Gates** (`ChimeraEngine/gates/`)
   - Performance gate (16.6ms at 1080p)
   - Determinism gate (same seed → same output)
   - Golden image gate (visual regression detection)
   - LOD conservation gate (LOD of meaning assertion)

## Migration Guide

If you need to use the old stacks for legacy compatibility:

```python
# Old splat format conversion
from archive.old_stacks.splat_gpu import SplatState  # Not recommended
from ChimeraEngine.core.gaussian_splat_cloud import GaussianSplatCloud  # Use this instead

# Convert old format to new
cloud = GaussianSplatCloud(
    positions=old_splats["pos"],
    colors=old_splats["albedo"],
    opacities=old_splats["alpha"],
    scales=old_splats["scale"],
    rotations=old_splats["rotation"],
    covariances_3x3=None  # Build from scales/rotations
)
```

## Performance Baseline

Before consolidation:
- Close range (1-5m): 540ms/frame (614K splats all rendered)
- Far range (50km): 1 visible splat (LOD swallowed everything)

After consolidation (target):
- All ranges: ≤16.6ms/frame (60 FPS at 1080p)
- Hard frame-cost ceiling via pixel budget
- Consistent visual fidelity across distances

## Next Steps

1. Complete the unified renderer implementation
2. Run performance profile benchmark (`ChimeraEngine/benchmarks/performance_profile.py`)
3. Implement test suite with quality gates
4. Archive this directory after verification that new system works correctly

---

*This archive is kept for historical reference and migration purposes only. The new unified system should be used exclusively.*
