# RESEARCH 2026-08-22 — local 2D texture/UV generation for the material pipeline

Commissioned by the operator under the scoped doctrine amendment recorded in
`../SESSION_LOG_2026-08-22.md`: the no-AI line is suspended for researching 2D
AI-generated UVs (material images we EXTRACT parameters from). Same extraction
methodology as the splat era, carrier = triangles, not splats. Constraint, his
words: **local solutions only** — everything below must run on the dev box:
RTX 4090 (24 GB VRAM), 128 GB RAM, i9-13900K. No cloud APIs.

## What we actually need (the shape of the answer)

The pipeline slot being filled: an untextured CAD part (triangles + UVs) plus a
material intent ("dark brown plush fur", "green knit sweater") → a texture
(albedo minimum; PBR set ideal) that our extraction layer then reduces to
statistical parameters per labeled region. Two ways models deliver that:

1. **Flat material sheets** (text → tileable texture / SVBRDF maps). Simplest;
   the UV layout is ours (evolved, per the settled term), the model only fills
   the sheet.
2. **Mesh-aware painting** (text + mesh + UVs → texture fitted to the surface).
   Handles seams and region placement itself, at the cost of a heavier stack.

## Tier 1 — runs on the 4090 today, code + weights public

- **Text2Tex** (ICCV 2023) — text-driven texture synthesis on a given mesh via
  inpainting diffusion over rendered views. Authors state a 12 GB GPU
  suffices; 24 GB is comfortable. Generation ~500 s + refinement ~360 s per
  asset. Mesh-aware (tier 1, category 2). https://github.com/daveredrum/Text2Tex
- **DreamMat** (SIGGRAPH 2024) — text → full PBR material (albedo, metallic,
  roughness, normal) distilled onto a given mesh, geometry- and light-aware,
  designed to avoid baked-in shadows (the exact contamination we fought in the
  splat patches). Authors document the pre-render step at ~15 min **on a
  4090** — sized for our card by their own measurement. Known weakness from
  user reports: the metallic map can be wrong for dielectrics (a banana came
  out metallic) — our extraction layer would clamp metallic≈0 for plush/knit
  anyway. https://github.com/zzzyuqing/DreamMat
- **Stable Diffusion family as flat-sheet generators** — SDXL (8 GB class) and
  SD 3.5 Medium (the operator already holds HF access) both run natively;
  seamless/tileable output is a solved workflow (tiling flag / seamless LoRAs),
  with community pipelines going SDXL → 4K PBR sets via map-extraction tools.
  Category 1. https://cprimozic.net/notes/posts/generating-textures-for-3d-using-stable-diffusion/

## Tier 2 — runs locally with quantization/offload, heavier

- **FLUX.1 dev** — 12B params; FP16 needs ~24 GB (offload, tight), FP8 ~13 GB
  (comfortable), GGUF 4-bit builds 18–24 GB. Best-in-class photoreal flat
  imagery if SD3.5's material detail disappoints.
  https://willitrunai.com/can-run/flux-1-dev-on-rtx-4090-24gb
- **ReflectanceFusion** — diffusion text→SVBRDF maps (2D sheet, category 1
  with true PBR output). Architecture published; verify code/weights release
  before scheduling. https://arxiv.org/html/2406.14565v1

## Tier 3 — watchlist (capability right, local feasibility unverified)

- **Make-A-Texture** (Meta, WACV 2025) — shape-aware texture maps in ~3 s.
  Paper public; code/weights release status must be confirmed before it counts.
  https://openaccess.thecvf.com/content/WACV2025/papers/Gorelik_Make-A-Texture_Fast_Shape-Aware_3D_Texture_Generation_in_3_Seconds_WACV_2025_paper.pdf
- **FlexPainter** (2025) — flexible multi-modal multi-view-consistent texture
  generation; new, release status unverified. https://arxiv.org/html/2506.02620v1
- **FlashTex** — fast relightable mesh texturing with LightControlNet; the
  relightable property is exactly our no-baked-shadow requirement.
  https://arxiv.org/pdf/2402.13251
- **FabricGen** (CVPR 2026) — microstructure-aware woven fabric generation.
  If the sweater matters more than the fur, this is the specialist.
  https://openaccess.thecvf.com/content/CVPR2026/papers/Tang_FabricGen_Microstructure-Aware_Woven_Fabric_Generation_CVPR_2026_paper.pdf

## Recommendation (to be tested, not yet a decision)

Start at Tier 1 in the order: **DreamMat** (true PBR, mesh-aware, 4090-sized,
shadow-free by construction) for the mesh-fitted route, and **SD 3.5 Medium
flat sheets** (access already granted, zero new stack) for the evolved-UV
route where we control layout ourselves. Both are local, both feed the same
extraction layer. Text2Tex is the fallback if DreamMat's Blender dependency
fights the toolchain. FLUX.1 dev FP8 is the quality escalator for stubborn
materials. Nothing here requires a network call at generation time once
weights are on disk.

Open verification items before any build: confirm license terms per model
(SD 3.5 Medium is gated-but-granted; DreamMat/Text2Tex are research code),
confirm Make-A-Texture/FlexPainter release status, and check DreamMat's exact
VRAM peak during distillation (the 15-min figure is the pre-render, not the
full run).
