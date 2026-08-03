# Chimera Engine Rendering Pipeline

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

## Identity and Purpose

**Near-term**: Chimera Engine is a **standalone research viewer** for 3D Gaussian splatting, and an **asset/data source** feeding UE5 (via GLB/PLY export).

**Not yet**: A shipping game engine. Input, audio, save systems, packaging are explicitly deferred to keep focus on the core rendering pipeline.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Quality Gates                            │
│  Performance | Determinism | Golden Image | LOD Conservation│
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Renderer Layer                             │
│         GPUSplatRasterizer (GPU-resident, budgeted)        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      LOD Layer                              │
│    ClusterTree + BudgetedCut (screen-space error, pixel    │
│                    budget ceiling)                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   Format Layer                              │
│         GaussianSplatCloud (canonical 3DGS format)         │
│                  SplatPool (GPU-resident)                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Innovations

### 1. Budgeted LOD Selection (Nanite-style)
Instead of distance-based LOD, we select clusters based on **screen-space error** with a **global pixel budget**. This gives:
- Hard frame-cost ceiling (e.g., 1024 pixels = ~60 FPS at 1080p)
- Fixes close-range bug (540ms → ≤16.6ms) by culling excess splats
- Fixes far-range bug (1 visible splat at 50km) by maintaining detail where needed

### 2. GPU-Resident Splat Pool
Upload splat data **once**, keep it on device. Eliminate per-frame CPU↔GPU syncs that killed performance in the old stack.

### 3. Quality Gates
Four essential tests matching studio culture:
- **Performance**: ≤16.6ms at 1080p (60 FPS budget)
- **Determinism**: Same seed → byte-identical output
- **Golden Image**: Visual regression detection via SSIM
- **LOD Conservation**: "LOD of meaning" - opacity-weighted mass preserved

## Quick Start

### Basic Usage

```python
from ChimeraEngine.core.gaussian_splat_cloud import GaussianSplatCloud, SplatPool, Camera
from ChimeraEngine.loD.cluster_tree import build_cluster_tree
from ChimeraEngine.loD.budgeted_cut import select_clusters_budgeted
from ChimeraEngine.renderers.gpu_rasterizer import GPUSplatRasterizer

# Load splat cloud (3DGS .ply format)
cloud = load_ply("path/to/splat.ply")  # From ChimeraEngine.formats.gaussian_splat_format

# Build cluster tree for LOD
clusters = build_cluster_tree(cloud, max_depth=4)

# Create camera
camera = Camera(
    position=np.array([0.0, 0.0, 5.0]),
    target=np.array([0.0, 0.0, 0.0]),
    up=np.array([0.0, 1.0, 0.0])
)

# Setup rasterizer and upload splat pool once
rasterizer = GPUSplatRasterizer()
rasterizer.splat_pool.upload(cloud)

# Select clusters under pixel budget (budgeted cut)
frustum = create_default_frustum(camera, fov=np.radians(60))
selected = select_clusters_budgeted(
    clusters, camera.position, 1080, np.radians(60),
    budget_pixels=1024, frustum_planes=frustum
)

# Render (only selected clusters are sent to GPU)
image = rasterizer.render(cloud, camera, clusters=clusters)
```

### Running Tests

```bash
# Run all quality gates
pytest ChimeraEngine/tests/test_rendering_pipeline.py -v

# Run specific gate tests
pytest ChimeraEngine/tests/test_rendering_pipeline.py::TestRenderingPipeline::test_performance_1080p -v
pytest ChimeraEngine/tests/test_rendering_pipeline.py::TestRenderingPipeline::test_determinism -v
```

### Profiling Performance

```bash
# Measure current performance baseline
python ChimeraEngine/benchmarks/performance_profile.py

# Compare before/after consolidation
```

## File Structure

```
ChimeraEngine/
├── core/
│   └── gaussian_splat_cloud.py      # Canonical format, SplatPool, Camera
├── formats/
│   └── gaussian_splat_format.py     # 3DGS .ply I/O (from WorldModel/splat_io.py)
├── loD/
│   ├── cluster_tree.py              # Cluster tree construction
│   └── budgeted_cut.py              # Screen-space error budgeting
├── renderers/
│   └── gpu_rasterizer.py            # Unified GPU rasterizer (from ParticleEngine/rasterizer_gpu.py)
├── memory/
│   ├── splat_pool.py                # GPU residency management
│   └── async_transfer.py            # Async CUDA operations
├── gates/
│   ├── performance_gate.py          # 16.6ms budget check
│   ├── determinism_gate.py          # Same seed → same output
│   ├── golden_image_gate.py         # Visual regression detection
│   └── lod_conservative_gate.py     # LOD fidelity assertion
├── tests/
│   ├── test_rendering_pipeline.py   # Main test suite
│   ├── conftest.py                  # Pytest configuration
│   └── golden/                      # Reference images
└── benchmarks/
    └── performance_profile.py       # Performance baseline tool
```

## Performance Targets

| Metric | Target | Current (Before) | Notes |
|--------|--------|------------------|-------|
| Frame time at 1080p | ≤16.6ms | 540ms (close range) | 60 FPS budget |
| CPU↔GPU syncs per frame | 0 | ~14 arrays every frame | Upload once, keep on device |
| LOD selection | Budgeted cut | Distance-based | Screen-space error, not distance |
| Splat format | Standard 3DGS .ply | Multiple incompatible | Ecosystem compatibility |

## Known Limitations (Deferred)

- **Input system**: Not implemented - use external viewer for interaction
- **Audio**: Not implemented - focus on visual rendering only
- **Save/load**: Basic .ply I/O only; no custom binary formats yet
- **Packaging**: Standalone Python script, not distributed as compiled engine
- **Multi-threading**: Single-threaded CPU side (LOD selection)

## Migration from Old Stacks

If you have code using the old rendering stacks:

```python
# OLD (deprecated):
from Chimera.core.splat_gpu import SplatState
from Chimera.core.splat_lod import merge as cpu_merge_lod
from ParticleEngine.rasterizer_gpu import GPUSplatRasterizer  # Old version

# NEW (recommended):
from ChimeraEngine.core.gaussian_splat_cloud import GaussianSplatCloud, SplatPool
from ChimeraEngine.loD.budgeted_cut import select_clusters_budgeted
from ChimeraEngine.renderers.gpu_rasterizer import GPUSplatRasterizer
```

## Contributing

### Adding a New Quality Gate

1. Create gate module in `ChimeraEngine/gates/`
2. Implement `check_XXX()` function returning `GateResult`
3. Add test in `ChimeraEngine/tests/test_rendering_pipeline.py`
4. Document in this README

### Performance Optimization Checklist

- [ ] Eliminate per-frame CPU↔GPU syncs
- [ ] Use GPU-resident splat pool
- [ ] Implement budgeted LOD selection
- [ ] Profile with `performance_profile.py`
- [ ] Verify against 16.6ms gate at 1080p

## References

- **Original analysis**: See project documentation for the four-bug diagnosis and consolidation plan
- **Nanite inspiration**: UE5 Nanite cluster tree selection (screen-space error, not distance)
- **3DGS ecosystem**: Compatible with nerfstudio/polycam .ply files via `gaussian_splat_format.py`

## License

Part of Chimera Engine research codebase. See main repository LICENSE for details.

---

*This engine is a research tool focused on solving the splat rendering/LOD problem. It is not yet a general-purpose game engine.*
