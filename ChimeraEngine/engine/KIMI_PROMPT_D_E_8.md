# SPIACE Phase 10.5 — Tile Artifact Elimination (Phase 10 Complete)

## Context: What is Already Built

You are the lead developer on SPIACE, a first-principles space RPG engine. The following is complete and verified (committed as `cbb1545`):

**Phases 0–10:** Full WebGPU splat renderer, GPU Barnes-Hut N-body with universal kernel translation layer (5 kernels), multi-planet star system with 4 dynamic planets. All falsifiers green at 60 fps in GPU mode.

**All Tracks A–E groundwork:**
- Track A1/A2: Planet terrain → splats, real Earth DEM option
- Tracks C1/C2: Picking + highlight
- Tracks B/T: Scale-relative flight camera + LOD of time
- Track D1/D2: LOD port to v2 renderer + surface fracture (infinite detail)
- Track E1/E2/E3: Character standing/walking on planet with ground query + local-frame controller

**Key architecture in spiace_phase6.html (~3945 lines):**
- 5 kernels in DSL (kernel_dsl.py): gravity(mass), light(lum), EM(charge), heat(heat_source), acoustic(pressure)
- Quantity packing: mass/lum/charge/heat in ONE vec4f quants buffer; acoustic in its own f32 pressures buffer; field outputs in fields vec4f. Total: 8 storage buffers = WebGPU default limit exactly.
- Node size: 144 B (64 base + 5×16 per kernel)
- 4 planets orbiting one star, all dynamic tree particles with Keplerian velocities
- Multi-membrane context: nearestPlanetTo drives activeMembrane; character reframes per-planet
- Character controller: ground query via heightAt(lat,lon), local-frame WASD walking, gap witness <0.01m at rest
- LOD: N = 0.35·r_px² trained law, mip pyramid + fracture shell, MAX_PARTICLES=1M (no practical cap)
- Tree cache: rebuilds only when particles move >1e6 m since last build

**Current renderer bottleneck — TILE ARTIFACTS:**
The tile-based splat rasterizer (`sh-raster` WGSL fragment shader) is producing visible seams and artifacts at tile boundaries. This is the single biggest visual quality issue in the current render.

### The Problem: Three Root Causes

1. **TILE_SIZE=16 is too large** — At 4K resolution (3840×2160), there are ~240×135 = 32,400 tiles. Each tile independently accumulates splat contributions into its local `occ` (opacity coverage) variable. When a splat spans multiple adjacent tiles, each tile computes slightly different accumulation order and clipping, causing visible seams at tile edges — especially noticeable on high-contrast terrain boundaries.

2. **Per-tile sort divergence** — Each tile sorts its own list of overlapping splats back-to-front independently. A single wide splat that spans 4 adjacent tiles gets sorted separately in each tile's local list. The sort uses clip-space depth (`cw`), which varies slightly across the splat's extent, so the relative order of two overlapping splats can differ between neighboring tiles. This causes one pixel to show "splat A on top" while its neighbor shows "splat B on top" — a visible seam.

3. **MAX_PTILE=64 hard cap** — Each tile processes at most 64 splat contributions per pixel. At high density (close-up terrain with 7K+ fracture splats), some pixels in busy tiles hit this cap and skip contributions that adjacent tiles include. This creates a "staircase" pattern where dense regions look different from sparse ones even for the same visual content.

### Files to Modify
- `engine/spiace_phase6.html` — the WGSL rasterizer shader + CPU binning logic
- (No changes expected to kernel_dsl.py or test harness)

## SPECIFICATION: Fix Tile Artifacts

### What to Build / Change

**1. Reduce TILE_SIZE or eliminate tiles for correctness-critical paths**
   - Current: 16×16 pixel tiles, 32K tile grid at 4K
   - Options to evaluate and implement:
     - **TILE_SIZE=8**: Doubles tile count but reduces per-tile work. Better coherence between neighbors since each tile covers less screen area. Smaller `occ` divergence at boundaries.
     - **TILE_SIZE=32**: Halves tile count, larger per-tile work, more divergence. Only consider if performance is an issue (current GPU mode is 60fps with headroom).
     - **Hybrid approach**: Small tiles for close-up/high-density regions, skip tiling entirely when total visible splats < some threshold (simple overdraw sort instead of tile-bin-sort).

**2. Fix per-tile sort divergence**
   - The root cause: each tile sorts its own independent list using the splat's center depth (`cw`). But `cw` varies across a wide splat, so two splats A and B might have A.beforeB in one tile and B.beforeA in another.
   - Fix options:
     - **Shared sort key**: Compute a global sort order (by back-to-front centroid depth) once on CPU, store it in `sorted_idx`, and use the SAME ordering in every tile. The `sorted_idx` already exists — ensure it's a true global sort, not per-tile.
     - **Depth-harmonized accumulation**: In the raster shader, when two splats overlap, use their center-to-camera distance as a consistent tiebreaker across all tiles that both splats touch.

**3. Remove or raise MAX_PTILE hard cap**
   - Current: `MAX_PTILE = 64u` — each tile processes at most 64 splats per pixel
   - At high density, this causes missing contributions in busy pixels while neighbors include them → visible seams
   - Options:
     - **Raise MAX_PTILE to 256** — GPU fragment shaders have plenty of registers for a loop counter. The cost is more instructions per pixel but eliminates the cap entirely.
     - **Dynamic tiling with overflow**: If a tile has >MAX_PTILE splats, spill the extras into a separate buffer and process them in a second pass (more complex).
     - **Adaptive MAX_PTILE**: Set based on tile density — if average splats/tile < 64, use 64; otherwise raise proportionally.

**4. Improve the accumulation at tile boundaries**
   - The `occ` variable tracks accumulated opacity per-pixel within a tile. When a pixel is processed in two adjacent tiles (because a wide splat spans them), each tile independently computes its contribution from scratch — but they use different local accumulators, so the final blend differs slightly.
   - Fix: Ensure the accumulation formula is **idempotent and commutative** across tiles. The current Gaussian accumulation `r += col * alpha * occ; occ *= (1 - alpha)` IS mathematically correct per-pixel — the issue is that different pixels in adjacent tiles see slightly different splat subsets due to binning boundaries.
   - Additional fix: Extend tile binning by 1 pixel on each side (oversized bins) so splats near tile edges are included in ALL tiles they touch, not just those whose center falls within the bin.

### What NOT to Change
- The kernel DSL (`kernel_dsl.py`) — no new physics needed
- The test harness (`test_phase6.py`) — all existing falsifiers must stay green; do NOT add new falsifier assertions unless a previously-green one breaks (in which case fix it)
- The tree construction or N-body integration
- The HDR bloom pipeline, tonemap, or post-processing

## RULES
- Single standalone HTML — no external dependencies
- Non-headless Playwright testing only (`--enable-unsafe-webgpu`)
- `kernel_dsl.py --verify` must pass after any changes
- All existing falsifiers 1–13 must remain green
- Rule 0 applies: state the theory, make a prediction, name the falsifier BEFORE running

## WHAT SUCCESS LOOKS LIKE

After your work:
1. No visible tile seams at any zoom level (orbit → surface)
2. Wide splats render consistently across all tiles they span — no "staircase" pattern in dense regions
3. GPU mode still ≥ 50 fps at 4K with all kernels active (current baseline: 60 fps)
4. CPU mode still functional and fast enough for the test harness (~2-3 ms per tree build + traversal)

## MEASURED NUMBERS TO REPORT
- TILE_SIZE before/after
- MAX_PTILE before/after
- Visible splat count at close range (planet surface, r_px > 100)
- FPS in GPU mode with all kernels active
- FPS in CPU mode
- Any new artifact patterns observed during testing

## DOCUMENTATION
Update `SPIACE_RPG_PLAN.md` v2.5 with Phase 10.5 section including measured numbers and next steps (Phase 11: ship-to-foot narrative arc).

Document version target: 2.5 | Status target: Phases 0–10.5 + Tracks A/B/C/T/D/E complete