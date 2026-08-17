# Render Pipeline Data Flow — Audit

## Purpose
Read-only audit tracing the data flow from story membranes → splat buffers → GPU rendering,
with identified issues, budgets, and unit-system hazards.

## Data Flow Path

```
Chimera/core/grow.py
  |  derive(parent_nums, free) -> numbers.json
  |  emit(nums, t) -> (N, 28) float32 buffer (local units, radius ~1)
  |
  v
story/marbleMaze/physics.py (per membrane)
  ├─ derive()   — produces numbers.json with extent_m, scale, etc.
  ├─ emit()     — produces (N, 28) float32 numpy array
  └─ SIZE col = 20 (grain size in local units)

ChimeraEngine/splat_appearance.py
  |  scene_terms() / membrane_terms()  — discover all emit-capable membranes
  |  membrane_buffer(term, t)          — call emit(), validate (N, 28), cache
  |  scene_buffer(term)                — alias for t=1.0, cached
  |  scene_cam_distance(term)          — extent_m * 2.8 (world metres!)
  |  SIZE = 20                         — matches gpu_pipeline.SIZE

ChimeraEngine/lod.py
  |  params()           — load rho=0.45, beta=2.5 from lod.trained.json
  |  lod_count(r_px, n_base, p) — N = rho * r_px² (pixel-budget law)
  |  body_radius(buf)   — max |position| (world units of buffer)
  |  build_mips()       — precompute mip pyramid with spatially-averaged colors
  |  select()           — pick coarsest mip level with enough grains

ChimeraEngine/perf_guard.py
  |  check_frame_budget(n)      — raises if > 250,000 grains/frame
  |  check_surface_budget(term, n) — raises if > per-type budget
  |  check_tile_budget(tiles, per_tile) — raises if > 16,384 per tile

ParticleEngine/gpu_pipeline.py
  |  FullGPUPipeline.upload(data, term="") — copies (N,28) to GPU
  |     ├─ check_frame_budget + check_surface_budget if term set
  |     └─ _grow(n) — allocate GPU arrays
  |  step_particles(dt, cvars) — sim kernels (gravity, wind, boundary, attractors)
  |  render_from_gpu(camera, params) — full pipeline: sim + project + cull + composite
  |  render_splats(...) — pre-computed splats path (Nanite clusters)

ChimeraEngine/live_viewer.py
  |  _loop() thread:
  |     1. FullGPUPipeline created once
  |     2. camera = FirstPersonCamera or orbit camera
  |     3. On (re)load: membrane_buffer() -> build_mips() -> upload(data, term)
  |     4. LOD select() every frame, upload only on level change
  |     5. render_from_gpu(cam, params) -> MJPEG publish
  |     6. Walk mode: scene_around() -> np.concatenate -> upload (untagged)
```

## Buffer Layout (N, 28 float32)

Column indices (NCOLS=28):

| Col | Name | Meaning |
|-----|------|---------|
| 0-2 | PX,PY,PZ | Position (local units) |
| 3-5 | VX,VY,VZ | Velocity |
| 6-8 | AX,AY,AZ | Acceleration |
| 9 | MASS | Particle mass |
| 10 | LIFE | Lifetime |
| 11 | TYPE | Particle type code |
| 12-15 | PROP0-PROP3 | Generic properties (material, emissiveness, etc.) |
| 16-18 | CR,CG,CB | Color (0-1) |
| 19 | ALPHA | Opacity |
| 20 | SIZE | Grain size (local units) |
| 21-23 | NX,NY,NZ | Surface normal (0,0,0 = no backface cull) |

## Budget Thresholds (perf_guard.py)

| Budget | Value | Source |
|--------|-------|--------|
| MAX_PER_TILE | 16,384 | gpu_pipeline.py:36 |
| MAX_GRAINS_PER_FRAME | 250,000 | Derived (7.8 fps @ 1920×1080 on RTX 4090) |
| MAX_RENDER_MS | 200 ms | perf_guard.py:30 |
| BUDGET_TERRAIN | 20,000 | perf_guard.py:36 |
| BUDGET_ROCK | 8,000 | perf_guard.py:38 |
| BUDGET_SAND | 12,000 | perf_guard.py:40 |
| BUDGET_VEGETATION | 16,000 | perf_guard.py:42 |
| BUDGET_ATMOSPHERE | 30,000 | perf_guard.py:44 |
| BUDGET_STELLAR | 50,000 | perf_guard.py:46 |
| BUDGET_BODY | 12,000 | perf_guard.py:48 |

## Surface Type Classification (perf_guard.py:85)

Membranes are classified by substring matching on their term name:

| Surface Type | Keywords | Budget |
|-------------|----------|--------|
| terrain | ground, terrain, terrace | 20,000 |
| rock | rock, mine, mining, stone | 8,000 |
| sand | sand, dust, dune | 12,000 |
| vegetation | biome, steppe, vegetation, tree, forest, garden | 16,000 |
| atmosphere | atmosphere, cloud, fog, sky, breath, ocean, water, salt, nitrogen | 30,000 |
| stellar | star, sun, galaxy, planet, solar, horizon, cooling, densityclock, clock, emptying | 50,000 |
| body | human, hand, foot, eye, skin, ankle, grip, stance, sweep, balance, load, thrust, body | 12,000 |
| general | (fallback) | 250,000 |

## Critical Issues Found

### Issue 1: Unit System Mismatch (live_viewer.py:307-314)
**Severity:** CRITICAL
**Statement:** The camera distance from `scene_cam_distance()` is in world metres, but the
buffer from `membrane_buffer()` is in local units (radius ~1).
**Falsifier:** A planet with body_radius=1.03 and cam_distance=1.47e7 produces r_px = 0.0000655,
collapsing ALL body splats to the coarsest mip (1 grain). No error is raised.
**Status:** Documented in code comments as a "FOLD/BOND MISFOLD." LOD selection is now
keyed to `_radius / _radius0` (unit-free ratio) instead of feeding world-metre distance
to `projected_radius_px()`.

### Issue 2: Budget Enforcement is Opt-In by Term (gpu_pipeline.py:665)
**Severity:** MEDIUM
**Statement:** `pipe.upload()` only calls `check_frame_budget` and `check_surface_budget`
when `term` is passed. Walk-mode uploads (ground+body+touchables) are deliberately untagged.
**Falsifier:** A corrupted membrane emit() that produces 1e6 grains in walk mode would
render without warning (only MAX_PER_TILE=16384 would fire as a black tile).
**Status:** Intentional design per code comments — composites belong to no single membrane.

### Issue 3: MAX_PER_TILE Cap (gpu_pipeline.py:22)
**Severity:** LOW
**Statement:** Raised from 4096 to 16384 on 2026-07-29 due to soft-field splats spanning
many tiles. Not all overruns are fixed by raising the cap — some are emit() bugs.
**Falsifier:** Soft-field membranes (theGalaxy, theSolarSystem) producing >144 tiles per
splat still cause black rectangles if tile count exceeds MAX_PER_TILE.
**Status:** CHIMERA_TILE_DIAG=1 exists to diagnose.

### Issue 4: Unreachable Code After Return (gpu_pipeline.py:881-882)
**Severity:** LOW
**Statement:** Lines 881-882 after `return out.copy_to_host()` in `_finish_render_path`
are dead code — `step_particles` and `render_from_gpu` are unreachable.
**Falsifier:** N/A — these lines never execute.
**Status:** Dead code; likely a refactor artifact.

### Issue 5: LOD Build Cost (lod.py:124)
**Severity:** LOW
**Statement:** `lod_switch()` calls `build_mips()` every invocation, which is expensive.
The live_viewer correctly builds mips once per reload, but the standalone `lod_switch()`
function would rebuild every call.
**Falsifier:** Calling `lod_switch()` on a 100k-grain buffer repeatedly causes O(n) rebuilds.
**Status:** `lod_switch()` is not called from the hot path; live_viewer uses `build_mips` +
`select` directly.

## Kernel Sequence (render_from_gpu)

1. `_p2s`  — Particle → splat (covariance, color, opacity from per-particle props)
2. `_project` — World → screen space projection (view × projection)
3. `_cull` — Frustum + far-plane culling (back-face if normal present)
4. `_inv_radii` — Invert covariance for disk rendering
5. CPU sort (`np.argsort`) — Depth order (nearest-first for front-to-back compositing)
6. `_compact` — Gather visible particles into contiguous array
7. `_gather` — Sort by depth rank (CPU sort → GPU gather)
8. `_build_tiles_*` — Bin splats into 32×32 px tiles (CuPy or NumPy fallback)
9. `_composite` — Per-tile splat rendering with alpha blending

## Falsifier
This audit is complete when the data flow can be traced end-to-end without a single
undocumented branch. All five issues above have explicit falsifier tests or are
marked as intentional design. The remaining gap: no automated test asserts the
unit-system contract at the live_viewer/lod.py interface.
