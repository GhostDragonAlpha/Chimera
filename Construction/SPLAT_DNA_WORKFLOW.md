# Splat-DNA — Scan → Object Genome → Game

> Turn a real 3D Gaussian-splat scan into **labeled, isolated, re-composable objects** by reading their **DNA**, and reverse the same pipeline to build worlds.
> **HONEST STATUS is marked on every claim.** `PROVEN` = verified this session on real data or known ground truth. `DESIGNED` = coherent but not built. `FRONTIER` = genuinely hard / open research.
>
> **GPU IS MANDATORY.** Rendering, segmentation, and recovery run on the GPU (torch/CUDA on the 4090). Do **not** run these on CPU — it is not what a professional does and it will time out. Only file I/O and small bookkeeping belong on CPU.

---

## 1. The one idea

An object's identity is a **genome** with two independent axes:

- **Morphology-DNA (shape)** — *what shape is it.* PCA dimensionality (linearity/planarity/scatter), **taper**, **radial symmetry**, **fractal dimension**, **aspect**, verticality. Separates trunk vs post vs bucket vs foliage vs wall vs rock.
- **Material-DNA (substance)** — *what is it made of.* **The splat configuration**: the joint *distribution* of the splats' **size**, **shape (anisotropy)**, **angle (orientation)**, **color**, and **opacity**. Separates bark vs moss vs ground.

Two load-bearing corrections learned this session:
1. **The DNA is in the configuration, not the averages.** A material's identity is how its splats are sized/shaped/angled/arranged — the thing you destroy by averaging into one PBR number.
2. **The DNA is a distribution (a range), not a value.** Oak varies plank to plank; you sample *many* known specimens and the genome is the mean **and the spread**. The spread is what defines a membrane's boundary.

Recognized genomes get **serial numbers** — a **codebook**. The scene then compresses to `{codebook: serial# → genome distribution}` + `{map: membrane → serial#}`. That codebook does triple duty: **compress, identify, regenerate.** This is "compression is intelligence," made literal (it is vector quantization / a texton dictionary).

**You can only serial-number what you can tell apart** — which is why the DNA-distinguishability result had to come first.

---

## 2. Honest status ledger (this session)

**PROVEN — verified on real data or known ground truth:**
| Capability | Evidence | Code |
|---|---|---|
| `.ksplat` decoder (pos, color, opacity, scale, rotation) | byte-budget matched exactly; 3.06M splats loaded, finite | `ksplat_io.py` |
| GPU torch rasterization on the 4090 | 9 orbit views in ~120 ms | `gpu_render_torch.py` |
| SAM 2 segmentation (via ultralytics) | segments a view in ~0.8 s on `cuda:0` | `multiview_sam_lift.py` |
| Multi-view SAM lift (render→segment→back-project→vote→3D) | 107k-splat object lifted, cached | `multiview_sam_lift.py` |
| Morphology signatures | 6/6 on synthetic trunk/post/bucket/foliage/wall/rock | `morphology_signatures.py` |
| Material-DNA recovery (differentiable inverse rendering) | recovered known oak & copper {albedo,roughness,metal} to ~1%, incl. metal 0.04 vs 0.97 | `material_dna.py` |
| Splat-configuration DNA | bark / moss / ground are distinguishable signatures; **wood grain measured as aligned splat long-axes** | `take_dna.py` |

**DESIGNED — coherent, not yet built:**
- The **serial-number codebook** (cluster regions → genomes → IDs → compress/identify/regenerate).
- **Full distributions** (not means) for material-DNA — the "range, not a value."
- **Re-composition** — placing extracted objects into a new scene (the game half; same pipeline reversed).

**FRONTIER — genuinely hard / open:**
- **Relighting / joint material-and-light inverse rendering** — ill-posed (a wrong material + wrong light fakes the same pixels). The **structural** DNA (size/shape/angle) is lighting-independent and readable *now*; the **color** DNA is contaminated by baked capture-light (hidden in the splats' view-dependent SH color).
- **Completing unseen geometry** — the back/underside the cameras never saw (your "membrane"); a generative, not geometric, problem.
- **Quaternion convention** — orientation/grain features assume `wxyz`; verify before trusting the grain signal absolutely.

**ENVIRONMENT:**
- Python 3.14, torch 2.13+cu126, RTX 4090 (25.8 GB).
- `gsplat` 1.5.3 installed but its CUDA kernels **won't JIT here** (needs ninja; also a torch-2.13 incompatibility) → the *trained* identity-encoding path (Gaussian Grouping / SAGA) is blocked; we use torch rasterization + explicit multi-view voting instead.
- The `.ksplat` files **lost their original COLMAP camera poses** → we render *novel* views rather than reuse posed captures.

---

## 3. The pipeline (stage → grounded method → proven code)

| # | Stage | Real method it maps to | Code / status |
|---|---|---|---|
| 0 | Decode the scan | INRIA 3DGS / GaussianSplats3D `.ksplat` | `ksplat_io.py` · PROVEN |
| 1 | Orient (up from ground plane) | RANSAC dominant plane | in each script · PROVEN |
| 2 | Lock-on / crop tight | promptable segmentation (SAGA, Click-Gaussian) | by-eye framing · PROVEN |
| 3 | Render novel views + ID buffer | GPU rasterization (gsplat family) | `gpu_render_torch.py`, `multiview_render.py` · PROVEN |
| 4 | Segment in 2D | **SAM 2** (Grounded-SAM for text) | `multiview_sam_lift.py` · PROVEN |
| 5 | Lift to 3D (back-project + vote) | 2D-mask lifting; **Gaussian Grouping** (trained ver. blocked) | `multiview_sam_lift.py` · PROVEN (voting) |
| 6 | Morphology-DNA (shape signature) | PCA descriptors + taper/fractal/aspect | `morphology_signatures.py` · PROVEN (synthetic) |
| 7 | Material-DNA (splat-config signature) | splat-configuration distributions | `take_dna.py` · PROVEN (distinguishable) |
| 8 | Material recovery (from a known sample) | analysis-by-synthesis / inverse rendering | `material_dna.py` · PROVEN (synthetic GT) |
| 9 | Serial-number codebook | vector quantization / texton dictionary | `codebook.py` · **BUILDING** |
| 10 | Mesh for an engine | **SuGaR** / 2DGS | · DESIGNED |
| 11 | Re-compose the game | 3DGS editing (Gaussian Grouping, 3DitScene, FreeInsert) | · DESIGNED |

---

## 4. Grounded methods (the real papers)

- **Gaussian Grouping** — per-Gaussian identity encoding trained from SAM masks: [arXiv 2312.00732](https://arxiv.org/abs/2312.00732), [code](https://github.com/lkeab/gaussian-grouping)
- **SAGA — Segment Any 3D Gaussians** (promptable, 4 ms): [arXiv 2312.00860](https://arxiv.org/abs/2312.00860), [code](https://github.com/Jumpat/SegAnyGAussians)
- **SAM2Object** — view-consistent 2D→3D lifting: [code](https://github.com/jihuaizhaohd/SAM2Object)
- **SuGaR** — mesh from splats: [arXiv 2311.12775](https://arxiv.org/abs/2311.12775)
- **Survey** — segmentation/editing/generation: [arXiv 2508.09977](https://arxiv.org/pdf/2508.09977)
- **PBR foundation** — the rendering equation (Kajiya 1986); Cook-Torrance GGX BRDF (1982); relightable-GS: GS-IR, Relightable 3DGS, GaussianShader.

---

## 5. The material math (recovery uses this forwards *and* backwards)

Forward (authoring) and inverse (recovery) share ONE model — the renderer. Recovery = run the forward model in a loop until its render matches a known sample (analysis-by-synthesis = your trainer paradigm).

```
color_to_eye(view) = Σlights [ BRDF(light,view) · light_color · intensity · cos(normal, light) ]
BRDF = albedo/π                                   (diffuse)
     + D(roughness)·F(metal,view)·G(roughness) / (4·(n·v)·(n·l))   (specular)
```
Material genome = {albedo, roughness, metalness, normal} **+ the splat-configuration distributions + their ranges**. Structural config is lighting-clean; color needs relighting (FRONTIER).

---

## 6. Next rung (proceed)

**Build the codebook** (`codebook.py`): cluster the scene's splats into K material genomes by their configuration features, assign each a **serial number**, report each genome's coverage of the scene, and paint the scene by serial number. Then: full distributions (not means), then identify/regenerate, then re-compose.
