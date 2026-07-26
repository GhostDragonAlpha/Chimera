# THE RENDERER, v2 — a rebuild, and why

> **Status: DESIGN.** Nothing here is built yet. Written 2026-07-26 after measuring v1's ceiling.
> v1 = `ParticleEngine/gpu_pipeline.py` (numba-CUDA + CuPy, Python frame loop, MJPEG to the browser).
> It is not slow because of a bad kernel. It is slow because of its **shape**.

---

## 1. Why rebuild — the measured ceiling

One session of honest optimization took aPlanet from **1.6 → 36 fps** (22×) through five real levers:
small opaque grains, GPU tile binning (CuPy radix), back-face culling, a uint8-direct composite, and
dynamic resolution. Every one was measured; none were guesses. Then it stopped.

**Where the frame actually goes** (2560×1440, planet filling the view — the interactive case):

| stage | ms | share |
|---|---|---|
| composite (per-pixel splat blending) | 47.0 | 84% |
| tile binning (CuPy, ~13 kernel launches) | 5.5 | 10% |
| everything else (project/cull/compact/gather) | 3.4 | 6% |
| **GPU total** | **56** | → **18 fps** |
| *plus* host: download → PIL JPEG → HTTP → browser decode | *not in the 56* | |

**Target: 120 fps @ 2560×1440 = 8.3 ms/frame.** We need ~7×. Three structural walls block it:

1. **Python is in the frame loop.** Kernel launches, CuPy's ~13 element-wise passes per bin, per-frame
   `device_array` allocs, a blocking `int(counts.sum())` sync. Measured earlier this session: ~40 ms/frame
   of pure numpy glue (`np.stack`/`np.clip`/`*255`/`astype`) — removing it alone was 14→36 fps. There is
   more of that class left, and it is inherent to orchestrating per-frame work from Python.
2. **The pixels take the long way home.** Render on GPU → download → JPEG-encode → HTTP → browser decodes
   → `<img>`. The display is on the same machine as the GPU. This entire round trip is waste.
3. **The composite is warp-divergence-bound.** Proven, not assumed: I implemented the textbook
   shared-memory tiled rasterizer *and* a pre-gathered packed variant. **Both lost to the naive kernel**
   (49 ms and 51 ms vs 44 ms). Once some pixels in a warp hit the opaque early-out and others don't, the
   reads scatter and no prefetch trick helps. In numba-CUDA I have no subgroup/wave intrinsics to fix that.

**Meanwhile, reference WebGPU 3DGS renderers hit ~200 fps on a 3090 and ~2.1 ms/frame** (0.58 ms sort +
1.52 ms preprocess/draw). The gap is not the GPU. It is the architecture.

**Verified on this machine (2026-07-26), in-browser:** WebGPU present, adapter `nvidia / lovelace` (the real
4090), with `subgroups`, `shader-f16`, `timestamp-query`, `float32-blendable`, 32 KB workgroup storage,
1024 invocations/workgroup, 2 GB max buffer. Every capability the fast path needs.

---

## 2. The architecture — one seam, drawn in the right place

The project already has the right idea in `THE_MATTER_MODEL.md`: **generate-then-bake** (bricks =
GENOTYPE, the renderable = PHENOTYPE). v1 blurred it by regenerating and re-orchestrating per frame.
v2 draws the seam hard:

```
  PYTHON (keeps everything that is the magic sauce)          |   RENDERER (owns the frame loop)
  ---------------------------------------------------------- | -------------------------------------
  story -> terms -> membranes -> genomes                      |   persistent splat buffers in VRAM
  matter model, trainers, objectives, the dyad/proofs         |   GPU: cull -> project -> sort -> raster
  splat_appearance (matter -> splats), LOD law, mip pyramid   |   direct to the display surface
                        |                                     |            ^
                        +------> BAKE: .chsplat buffer -------+------------+
                                 (upload once, not per frame)
```

**Python never touches a frame.** It produces baked splat buffers (and hot-reloads them when the story
changes — the `reload` tool still works, it just re-bakes). The renderer is a persistent GPU program.

### Where the renderer runs — recommendation: **browser WebGPU first (WGSL), native `wgpu` later if needed**

- It **deletes wall #2 entirely** — pixels are produced where they are displayed. No download, no JPEG,
  no HTTP per frame. This is the single biggest measured win available.
- The live viewer is *already* a browser page. This is a drop-in replacement for the MJPEG `<img>`, and
  the gallery server keeps its job (serve the page + the baked buffers).
- **It is a distribution channel.** The goal is to ship a game that earns. A WebGPU build is a link —
  no install, no store gatekeeper. That matters more here than 10% of peak throughput.
- **The shader work is portable.** WGSL runs unchanged on native `wgpu` (Rust). If browser memory limits
  (~2 GB/buffer) or filesystem access become the binding constraint for a full planetary world, the
  compute kernels move to native without a rewrite. (`web-splat` ships both from one codebase.)

Honest risk: browser memory ceilings and asset streaming are real constraints for a *whole solar system*.
The mitigation is the same thing the game needs anyway — LOD, HLOD, and paging (Tier 2 below).

---

## 3. The feature list

Tiered by what unblocks what. **Tier 0 buys the framerate; Tier 1 fixes what you can see; Tier 2 is what a
space game specifically demands; Tier 3–4 make it a game rather than a viewer.**

### Tier 0 — the frame loop (this is the 7×)
| # | feature | why |
|---|---|---|
| 0.1 | **Persistent GPU residency** | splats uploaded once, live in VRAM across frames. v1 re-derives per frame. |
| 0.2 | **No host in the per-frame path** | the whole frame is GPU passes + one present. Kills the Python tax. |
| 0.3 | **Direct-to-surface presentation** | no readback/encode/stream. Kills wall #2. |
| 0.4 | **GPU radix sort** by `(tile, depth)` | the proven approach; ~0.58 ms in reference impls. `subgroups` available. |
| 0.5 | **Fused preprocess pass** | cull + project + 2D covariance + tile-touch count in ONE compute dispatch. |
| 0.6 | **Tile rasterizer, one workgroup per tile** | with 32 KB shared-memory batching + **subgroup ballot for early-out** — the thing v1 could not express, and the reason its two tiled attempts lost. |
| 0.7 | **Indirect dispatch** | GPU decides its own workload sizes; no host round-trip to read counts. |
| 0.8 | **Double/triple buffering + frame pacing** | overlap CPU/GPU; stable 120 Hz cadence rather than bursty. |
| 0.9 | **`timestamp-query` instrumentation** | per-pass GPU timings, built in. No more attributing time by guesswork. |

### Tier 1 — correctness and quality (the artifacts you are seeing)
| # | feature | why |
|---|---|---|
| 1.1 | **Mip-Splatting anti-aliasing** — 3D smoothing filter (clamp each Gaussian to the **Nyquist limit** of its sampling rate) + **2D Mip filter** (box-filter approximation) replacing 2D dilation | **This is the named, published fix for the dancing dots.** The artifact is scale-dependent aliasing: grains crossing pixel boundaries as distance/focal changes. v1's `1.5*rad` footprint *is* an ad-hoc 2D dilation, and v1 has **no** frequency constraint on grain size at all. |
| 1.2 | **HDR accumulation + tonemap** | blend in linear HDR, tonemap once at the end. **This deletes an entire bug class**: every "white blowout" and every hand-calibrated `_PLANET_GAIN` / `_SURFACE_GAIN` re-measurement I have done this session exists only because there is no exposure stage. |
| 1.3 | **Spherical-harmonic view-dependent colour** | real 3DGS carries SH per splat; v1 has flat colour, which is why surfaces read as *painted* rather than *lit*. Also the honest home for the scan-recovered material DNA. |
| 1.4 | **TAA + motion vectors** | temporal accumulation; belt-and-braces stability while moving, and near-free supersampling. |
| 1.5 | **Correct front-to-back alpha in linear space** | with the early-out expressed as a subgroup ballot (see 0.6). |

### Tier 2 — scale (what a space game actually demands)
| # | feature | why |
|---|---|---|
| 2.1 | **Camera-relative rendering / origin rebasing** | float32 disintegrates at planetary/system distances. Non-negotiable for orbit→surface. |
| 2.2 | **Membrane-local coordinate frames** | the project already has this primitive (`core/membranes.py`: "a coordinate cannot exceed its membrane's extent"). The renderer should consume it directly — precision stops being a problem by construction. |
| 2.3 | **Reversed-Z depth** | precision where it matters, for the same reason. |
| 2.4 | **GPU frustum culling** | don't preprocess what is off-screen. |
| 2.5 | **Screen-space LOD** (`N = ρ·r_px²`) | **already trained** (`lod.py`, `lod.trained.json`) — port the law, keep the trained constants. |
| 2.6 | **HLOD / hierarchical coalescing** | a whole system collapses to one splat when far. The operator's coalesce/fracture, and the fractal LOD-of-meaning. |
| 2.7 | **Impostors / billboards** | a distant star is one quad, not 7,000 grains. |
| 2.8 | **Streaming & paging** | load/evict splat chunks by membrane as you fly (World Partition equivalent). The answer to browser memory limits. |
| 2.9 | **Instancing** | one planet genome, many instances — upload once, draw many. |

### Tier 3 — game rendering
| # | feature | why |
|---|---|---|
| 3.1 | **Star as a real light source** | terminator, day/night, phase — currently baked flat into grain colour. |
| 3.2 | **Shadows** | splat shadow maps or ray-marched; ships casting onto terrain. |
| 3.3 | **Atmosphere / scattering** | physical, replacing the fake halo shell. |
| 3.4 | **Emissive genome** | already specced in `SPLAT_DNA_WORKFLOW.md`: engines, lasers, plasma — `{colour, intensity, falloff, elongation, lifetime}`. A splat *is* the right primitive. |
| 3.5 | **Picking / selection** | click → which splat → which object. Needed for mining, EVA, targeting. |
| 3.6 | **Depth/GBuffer readback** | interaction, collision proxies, contact. |
| 3.7 | **Particle & VFX integration** | the existing `ParticleEngine` sim feeds splats directly. |
| 3.8 | **UI/HUD compositing** | a layer over the splat pass. |
| 3.9 | **Post: bloom, exposure adaptation, motion blur** | stars *should* bloom; exposure should adapt entering a shadow. |

### Tier 4 — production discipline
| # | feature | why |
|---|---|---|
| 4.1 | **Dynamic resolution** | prototyped in v1's live viewer; keep it, drive it off a real frame-time budget. |
| 4.2 | **Determinism** | same seed → same frame. The project's proof model depends on it. |
| 4.3 | **Capture (screenshot + movie)** | the **dyad** needs frames to judge. This is a first-class renderer feature here, not a nicety. |
| 4.4 | **Fallback path** | WebGL2 or a reduced path when WebGPU is absent, so the shipped game still runs. |

---

## 4. What we KEEP (most of the work is not thrown away)

**Keep — this is the value, and none of it is the renderer:**
- `splat_appearance.py` — matter → splats, the generator, and appearance-from-decomposition
- `lod.py` + `lod.trained.json` — the trained pixel-budget law and mip pyramid
- the story → terms → membranes hierarchy, `gen_decl.py`, the `reload` path
- every trainer, objective, genome, and the matter model
- the dyad / two-messenger proof system, the gates, CAPCOM
- `gallery.py` — it becomes the page + baked-buffer server

**Replace:**
- `ParticleEngine/gpu_pipeline.py` — the numba/CuPy rasterizer (v1)
- `live_viewer.py`'s MJPEG render thread and its per-frame streaming
- all per-frame Python orchestration

**Add:**
- a **bake step**: `splat_appearance` → a compact `.chsplat` buffer (f16 where it pays, per Mip-Splatting-clamped sizes)
- the WGSL renderer: preprocess → sort → rasterize → tonemap → present
- a thin control channel (camera, term selection, reload) — the *only* thing Python says to the renderer per frame

---

## 5. The plan — de-risk before committing

**Spike first (small, decisive).** One page, one baked aPlanet buffer, WGSL: preprocess → radix sort →
tile raster → present. No LOD, no story, no UI. Measure with `timestamp-query` at 2560×1440.
- **Pass:** ≤8.3 ms/frame (120 fps) → the architecture is right, build it out in tier order.
- **Fail:** report the real number and *which pass* ate it, then decide (native `wgpu`, or reduce scope).

This is the honest experiment: it either validates the rebuild or kills it cheaply, before any of the
content pipeline is touched.

**Then, in order:** Tier 0 complete → Tier 1.1 + 1.2 (the visible artifacts) → port the trained LOD (2.5)
→ camera-relative + membranes (2.1/2.2) → HLOD (2.6) → the game tiers.

---

## 6. References

- Reference WebGPU 3DGS performance (~200 fps @ 3090; 2.1 ms/frame incl. 0.58 ms GPU radix sort):
  [web-splat (WebGPU/Rust)](https://github.com/KeKsBoTer/web-splat) ·
  [gaussian-splatting-webgpu](https://github.com/Scthe/gaussian-splatting-webgpu) ·
  [SuperSplat WebGPU + streaming](https://blog.playcanvas.com/new-in-supersplat-webgpu-and-streaming-bring-huge-performance-wins/)
- The dancing-dots fix: [Mip-Splatting: Alias-free 3D Gaussian Splatting (CVPR 2024)](https://arxiv.org/abs/2311.16493) ·
  [project page](https://niujinshuchong.github.io/mip-splatting/)
- Artifact-free rendering, further: [AAA-Gaussians](https://arxiv.org/pdf/2504.12811)
- v1's measured ceiling and the two failed tiled-composite attempts: `DEV_LOG.md`, 2026-07-26.
