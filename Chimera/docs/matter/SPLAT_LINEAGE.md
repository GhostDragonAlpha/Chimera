# Splat stack lineage & IP posture — the fold-inside-out, on the record

> The human, 2026-07-18: *"Remember we're taking this idea and basically folding it
> inside out — that way it's our idea."* This document makes that instinct precise,
> durable, and safe: what is inherited science (cited), what is encumbered code
> (NEVER touched), and what is genuinely this studio's own invention (the inversion).

## 1. The three layers, kept distinct

1. **Published science (free to implement, cited):** representing scenes as
   anisotropic Gaussians composited front-to-back is EWA splatting — Zwicker et al.
   2001 — and the modern formulation is Kerbl et al. 2023, "3D Gaussian Splatting
   for Real-Time Radiance Field Rendering" (the public paper). Implementing math
   from a paper is standard practice; this studio's rasterizers
   (`core/splat_gpu.py` per-pixel + tiled, `core/matter_items.py` CPU reference)
   were written from the published math and from first principles. **Zero lines,
   kernels, or files from any reference implementation were read or used.**
2. **Encumbered code (NEVER use):** `graphdeco-inria/gaussian-splatting` and its
   CUDA rasterizer (`diff-gaussian-rasterization`) carry a **non-commercial,
   research-only license** (commercial use requires an Inria license). STANDING
   RULE for every agent: do not vendor, copy, pip-install, or "reference while
   writing" that repository or its kernels — a game is a commercial artifact.
   If a mature external rasterizer is ever genuinely needed, **`gsplat`
   (nerfstudio, Apache-2.0) is the licensed alternative** — and even then, prefer
   our own Warp implementation, which already exists and is parity-proven.
3. **This studio's own invention (the inversion):** everything below.

## 2. The fold-inside-out, precisely

Inria's method is **reconstruction**: photograph reality, then run a
differentiable optimizer *backwards* until millions of Gaussians reproduce the
captured radiance. The lighting of the capture moment is baked into every splat —
which is exactly why relighting captured splats is an open research problem, and
why their optimizer IS their contribution.

This studio's method is **emission**: matter grown by the studio's own systems
(adhesion, L-systems, the matter library's provenance-tagged materials) *emits*
its Gaussians forward — position and orientation from the grown geometry, albedo
and roughness from the library's distributions ("an average, not a surface").
Nothing is reconstructed, so **the reconstruction optimizer — the heart of the
paper — is absent from this pipeline because nothing needs solving.** Splats
carry MATERIAL, never baked light; the ENGINE lights them (Substrate slabs,
proven live: `lit_vc_REAL.png`, the muscle-in-skin anatomy render).

| axis | reconstruction (theirs) | emission (ours) |
|---|---|---|
| direction | photos → optimize backward | known matter → emit forward |
| splat payload | radiance (light entangled) | material (light-free) |
| relighting | open research problem | free — the engine's job |
| input data | multi-view captures + SfM | the matter model itself |
| optimizer | the core contribution | not used, not needed |
| double use | display only | same primitive drives physics (the substrate engine) |

The last row is the part with no analogue in the reconstruction world at all:
Part II of `THE_COMPOSITIONAL_WORLD_MODEL.md` makes the splat the SAME primitive
the physics runs on — "a physics engine and a rendering engine that are the same
engine." That is not a variation on 3DGS; it is a different machine that happens
to share a rendering primitive with it, the way two engines share the triangle.

## 3. Honest boundaries

- Attribution is kept BECAUSE the position is strong: citing Zwicker/Kerbl for
  the primitive costs nothing and makes the delta unmistakable. "It's our idea"
  is TRUE for the inversion and the substrate engine; claiming the primitive
  itself would be false and would weaken the true claim.
- Patents were NOT researched here (only the code license was). If this ships
  commercially, a live patent check on Gaussian-splat rendering is a
  due-diligence task for that day — recorded as an open item, not assumed away.
- `tb-0175`'s scan-training may one day fit materials against real captured
  splats; if those captures are produced by third-party reconstruction TOOLS,
  each tool's license is checked at ingestion (the harvester's provenance-per-
  region rule already demands the source be recorded).
