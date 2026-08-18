# THE BEAR WORKFLOW — the step-by-step series

Single entry point. Do the steps **in order**; each has a **GATE** that must pass before the
next. Detailed docs are *pointed to*, not duplicated. A step is not "done" until its gate
passes — "looks okay" is not a pass.

## The checklist

### 1. SOURCE a valid bear
- **What:** a bear with 2 NORMAL arms (not two fused into one per side), front and back
  identical in texture and color.
- **How:** SDXL-Turbo image → TripoSplat `.splat` (see `THE_BEAR_PIPELINE.md` §1–2).
- **GATE:** the eye reports exactly 2 arms AND front texture == back texture.
- **STATUS (2026-08-18): FAILED** — arms melded (2 fused per side); single-image has no depth.

### 2. VERIFY (static)
- **What:** the eye produces a defect report (limb count, proportions, front/back consistency).
- **How:** `ChimeraEngine/native/skeleton.py analyze` (render N views + vision-describe).
- **GATE:** no duplicated limbs, no front/back mismatch.
- **STATUS:** caught the 4-arms + color/texture mismatch. The eye perceives; the code agent
  analyzes physics (verifies the defect in the data).

### 3. EXTRACT materials
- **What:** the eye marks materials (labels + where); extract each material's **color genome**
  (RGB) AND **texture genome** (`log_size`, `aniso`, `opacity` from splat `scale`) AND
  **region** (spatial location).
- **How:** `senses` (eye) marks; `harvest_material.py` principle (cluster on *chromaticity*,
  not raw RGB); texture read from the `.splat` 14-float `scale` (the thing `harvest_material.py`
  could not read from 2D frames).
- **GATE:** the codebook separates into distinct materials with distinct regions.
- **STATUS:** DONE — 6 materials, `ChimeraEngine/native/teddy_materials.json`. Region is still
  color-cluster bbox (approximate); spatial region outlining is the next refinement.

### 4. REAPPLY
- **What:** recolor every splat to its material's average color, and rescale to its material's
  mean size (preserving anisotropy) — "paint" the surface with the extracted averages.
- **How:** classify each splat to nearest material by chromaticity; set `color = avg`,
  `scale = mean_mag * (scale / |scale|)`.
- **GATE:** front and back agree in color AND in `log_size`/opacity distribution.
- **STATUS:** color DONE, texture DONE (front/back `log_size` converged −6.629 vs −6.628).

### 5. RIG
- **What:** mark joints → triangulate → assign bones.
- **How:** `ChimeraEngine/native/skeleton.py mark | triangulate | assign`.
- **GATE:** static verification (2 normal arms, coherent limb assignment).
- **STATUS:** not started (blocked on step 1).

### 6. DRIVE
- **What:** the CA/force dynamics — gravity is a *field*, muscles are CA forces, contact acts
  through the feet; the pose (stand/walk) **emerges**, never assigned.
- **See:** `THE_RENDERER_DECISION.md` NEXT MEMBRANE.

## Where each doc lives

| topic | doc / tool |
|---|---|
| renderer (14-float 3DGS, Vulkan engine) | `docs/THE_RENDERER_DECISION.md` |
| splat format, generation, verification, series | `docs/THE_BEAR_PIPELINE.md` |
| workflow tool (analyze/mark/triangulate/assign) | `ChimeraEngine/native/skeleton.py` |
| material harvest (chromaticity clustering) | `tools/harvest_material.py` |
| material labeling (serial numbers) | `ChimeraEngine/vision/vision_pattern_labeler.py` |
| vision backend (the eye) | `ChimeraEngine/senses.py` |

Agent: Kilo (chimera-code)
