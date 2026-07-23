# Chimera

**A space game, and the asset pipeline that makes it buildable by one person.**

The pipeline takes real 3D Gaussian-splat scans and authored 3D assets and extracts
**object genomes** — morphology-DNA (shape) plus material-DNA (substance) — assigns them
**serial numbers**, and re-composes them into game content.

The idea in one line: *compression is intelligence, made literal.* A material is not a
texture; it is a **distribution** — the joint statistics of splat size, shape, angle,
colour and opacity. Recognise the distribution, give it a serial number, and you can
compress it, identify it anywhere, and regenerate it onto new geometry.

---

## Start here

| | |
|---|---|
| **`CLAUDE.md`** | Project manual — goal, pipeline status, hardware traps, conventions |
| **`Construction/SPLAT_DNA_WORKFLOW.md`** | The pipeline itself, with `PROVEN` / `DESIGNED` / `FRONTIER` marked per stage |
| **`docs/EXPERIMENTAL_METHOD.md`** | How to diagnose a live system without fooling yourself |
| **`docs/GLM_52_DEEP_MODEL.md`** | The local 744B model — read the speed section before calling it |

---

## What works today

- **Splat decoding** — `.ksplat`, `.splat`, `.ply`, verified byte-exact
- **GPU rasterisation** — 9 orbit views of 48k splats in 120 ms, pure torch (no `gsplat`)
- **SAM 2 multi-view lift** — segment in 2D, back-project, vote, isolate in 3D
- **Morphology signatures** — taper / aspect / radial symmetry / fractal dimension
- **Material recovery** — differentiable inverse rendering, recovers known albedo,
  roughness and metalness to ~1% (including metal 0.04 vs 0.97)
- **Splat-config DNA** — classifies held-out splats at 82.5% against 33% chance
- **Serial-number codebook** — GPU k-means over a scene into labelled material genomes
- **Format calibration** — a regression test that caught a real colour-decode bug

## What doesn't yet

- **Relighting** — joint material-and-light recovery is ill-posed. Structural DNA
  (size/shape/angle) is lighting-clean and usable now; **colour DNA is contaminated by
  baked capture light.**
- **Completing unseen geometry** — the back and underside no camera saw. Generative, not
  geometric.
- **Emissive genomes** — lasers and engine glow *emit* rather than reflect, so PBR
  material-DNA is meaningless for them. Designed, not built.

Status is marked honestly per stage in the workflow doc. Negative results are recorded
rather than quietly dropped.

---

## Requirements

- **NVIDIA GPU is mandatory** — rendering, segmentation and DNA recovery never run on CPU
- Python 3.14, `torch` with CUDA, `ultralytics` (SAM 2), `numpy`
- The corpus (~35 GB of scans, models and CC objects) is **gitignored** — it is data, not source

---

## History

This repository previously hosted a **DSL-driven Unreal Engine 5 game-generation
orchestrator**. That work is retired as of 2026-07-23 and archived under
**`archive/unreal-era/`** — preserved, not deleted, but no longer current. Nothing in it
should be treated as instructions.
