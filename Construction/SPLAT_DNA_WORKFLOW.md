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
| Material-DNA as **full distributions** + identify | genome = mean + range; classify held-out splats at **82.5%** (chance 33%) — the range names it | `take_dna_full.py` |
| Serial-number **codebook** | whole scene → **8 material genomes** with serial numbers; 3.06M splats → codebook + one serial# per splat | `codebook.py` |
| **Format calibration** (`.ply` ↔ `.splat`) | same model loaded from both containers **found and fixed a real colour bug** (sigmoid vs SH-DC); all channels now agree to 4 dp | `calibrate_formats.py` |
| **Hull material library** (space game) | 10 opaque surface genomes from truck/train/bicycle; **splat SHAPE separates smooth panel from rough corrosion** at equal brightness | `space_materials.py` |
| **Corpus farmed** (2026-07-22/23) | **35 GB, license-clean**: 28 splat scans + 39 INRIA trained models (13 scenes) + **489 CC objects across 20 categories** + 4D emissive FX + **611 camera poses** | `objaverse_fetch.py` |

**REFUTED — tested, did not work (recorded, not buried):**
- **Spatial voting (membranes)** — smoothing each splat's genome vote across its neighbourhood moved identify **82.5% → 82.8%**: flat. Diagnosis: the bark/ground confusion is **genuine material-DNA overlap, not spatial noise**, so no amount of spatial smoothing can repair it. The real lever is *richer features* (rung 9.6 — grain/orientation coherence separated bark 0.53 from ground 0.39 and was never actually in the classifier). `spatial_vote.py`

**DESIGNED — coherent, not yet built:**
- **Emissive genome class** (§10) — lasers / engine glow / explosions; `flame.splatv` is real captured ground truth on disk.
- **Regenerate** — sample a genome's distribution onto a fresh membrane.
- **Re-composition** — placing extracted objects into a new scene (the game half; same pipeline reversed).
- **Authored-asset intake** (§8) — read PBR maps straight off the 489 GLBs; no inverse rendering needed.

**FRONTIER — genuinely hard / open:**
- **Relighting / joint material-and-light inverse rendering** — ill-posed (a wrong material + wrong light fakes the same pixels). The **structural** DNA (size/shape/angle) is lighting-independent and readable *now*; the **color** DNA is contaminated by baked capture-light (hidden in the splats' view-dependent SH color).
- **Completing unseen geometry** — the back/underside the cameras never saw (your "membrane"); a generative, not geometric, problem.
- **Quaternion convention** — orientation/grain features assume `wxyz`; verify before trusting the grain signal absolutely.

**ENVIRONMENT:**
- Python 3.14, torch 2.13+cu126, RTX 4090 (25.8 GB).
- `gsplat` 1.5.3 installed but its CUDA kernels **won't JIT here** (needs ninja; also a torch-2.13 incompatibility) → the *trained* identity-encoding path (Gaussian Grouping / SAGA) is blocked; we use torch rasterization + explicit multi-view voting instead.
- The `.ksplat` files **lost their original COLMAP camera poses** → we render *novel* views rather than reuse posed captures. **RESOLVED for 3 scenes (2026-07-23):** `dylanebert/3dgs` ships `cameras.json` — **611 real poses** (bonsai 292, bicycle 194, stump 125), restoring true 2D↔3D correspondence. **bicycle is therefore the first real multi-view target for material recovery** (§12).

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
| 7 | Material-DNA (splat-config signature, full distributions) | splat-configuration distributions | `take_dna.py`, `take_dna_full.py` · PROVEN (82.5% identify) |
| 8 | Material recovery (from a known sample) | analysis-by-synthesis / inverse rendering | `material_dna.py` · PROVEN (synthetic GT) |
| 9 | Serial-number codebook | vector quantization / texton dictionary | `codebook.py` · PROVEN (8 genomes) |
| 9.5 | Spatial voting (membranes) | neighbourhood label smoothing | `spatial_vote.py` · TRIED — flat (82.8%); bottleneck is feature overlap, not spatial noise |
| 9.6 | Richer DNA features (grain/orientation) | add local orientation coherence | · DESIGNED (real next lever) |
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

DONE this session: the **codebook** (`codebook.py` — 8 genomes, scene painted by serial#) and **full distributions + identify** (`take_dna_full.py` — genome = mean+range, 82.5% classification).

**TRIED: spatial voting (`spatial_vote.py`) — it did NOT sharpen identify** (82.5% → 82.8%, flat). Honest diagnosis: it *helped* GROUND (92→95%) but *hurt* the sparse MOSS (99→92%), and left BARK stuck at 65%. The bottleneck is **not spatial noise** — BARK and GROUND have genuinely **overlapping material-DNA** (their distribution ranges overlap on nearly every feature), a *systematic* confusion label-smoothing cannot fix.

**NEXT (the real lever, data-driven): richer DNA features.** The one feature that *did* separate bark from ground — **grain / orientation coherence** (bark 0.53 vs ground 0.39, measured in `take_dna.py`) — was left OUT of the classifier's vector (`take_dna_full.py` used only size/aniso/colour/opacity). Add **per-splat local orientation coherence** to the genome and re-test. (The irony: the *neighbourhood* does matter — but as a discriminating **feature** (local grain), not as label-voting.) Then **regenerate** → **re-compose** (the game half).

## 7. Sibling pipeline (alignment)

Construction/ now holds **two** related pipelines; do not confuse them:
- **Photo → textured 3D tree** — `REFERENCE_TO_NOUN.md` (build a stylized object *from a 2D photo* via the CROSS: markers × photo patches).
- **3DGS scan → object DNA** — *this doc* (decompose a *real 3D scan* into material genomes).

They share the DNA vocabulary: the photo pipeline's **patches** are a hand-cut appearance library; this pipeline's **serial-numbered genomes** are the *measured, distributional* version of the same idea. Morphology is shared by both (`MORPHOLOGY.md` = the told concepts; `morphology_signatures.py` = the measured shape-DNA).

---

## 7.5 FILE INVENTORY — every script, what it is, whether to use it

> Added 2026-07-23 after an audit found working code with no doc entry. If you add a
> script, add its row. **An undocumented script gets rewritten by the next agent.**

### The DNA pipeline (this document)
| File | Role | Status |
|---|---|---|
| `ksplat_io.py` | Decode `.ksplat` / `.splat` / `.ply`; `load_any()` dispatches | **PROVEN** |
| `calibrate_formats.py` | Regression test: same model from two containers must agree | **PROVEN** — caught the SH-DC colour bug |
| `gpu_render_torch.py` | Pure-torch CUDA splat rasteriser | **PROVEN** — 9 views / 120 ms |
| `gpu_render.py` | Same job via `gsplat` | **SUPERSEDED — do not use.** `gsplat`'s CUDA kernels will not JIT here (no ninja + torch-2.13 API break). Kept only to document the attempt. |
| `multiview_render.py` | Orbit-camera view generation | PROVEN |
| `multiview_sam_lift.py` | SAM 2 segment → back-project → vote → 3D mask | **PROVEN** |
| `lift.py` | 2D → 3D lift primitives shared by the above | PROVEN |
| `morphology_signatures.py` | Shape-DNA: taper / aspect / radial symmetry / fractal dim | **PROVEN** — 6/6 synthetic |
| **`decompose_scene.py`** | **Whole-scene decomposition by morphological signature.** Iterative RANSAC extracts planes (wall/ground/path — their signature is planarity); the remainder clusters into blobs; each element gets a PCA shape signature (linearity/planarity/scatter). | **PROVEN** — this is the scene-level entry point to everything else |
| `material_dna.py` | GGX inverse rendering: recover albedo / roughness / metalness | **PROVEN** on known oak + copper |
| `take_dna.py` | Splat-config DNA sampler (means) | PROVEN |
| `take_dna_full.py` | Full distributions + identify | **PROVEN** — 82.5% vs 33% chance |
| `codebook.py` | GPU k-means → material genomes with serial numbers | **PROVEN** — 8 genomes |
| `space_materials.py` | Hull material library from the metal-bearing scans | **PROVEN** — 10 surface genomes |
| `spatial_vote.py` | Neighbourhood smoothing of genome votes | **REFUTED** — 82.5% → 82.8%, flat. Kept as the record of a dead end (see §2). |
| `objaverse_fetch.py` | Pull CC objects by LVIS category from Objaverse | PROVEN — 489 objects |
| `gsplat_fit.py` | Splat fitting | PROVEN |
| `export_web.py` | Honest probe: how much of a scan is actually plant? Isolates foliage by colour, traces the largest connected green mass | PROVEN — a *measurement*, not an exporter (despite the name) |
| `web_export.py` | Writes `web/object.json` for the browser viewer | PROVEN |

### The noun/verb construction pipeline (`DESIGN.md`, `REFERENCE_TO_NOUN.md`)
Separate from DNA extraction: this *authors* geometry rather than recovering it.
`DESIGN.md` explains the concepts; these are the files that implement them.

| File | Role |
|---|---|
| `noun.py` | **The noun constructor** — photo-authorable 2D seed → 3D noun. `construct()` is the whole decode: skeleton → flatten → lift by the golden rule → shape the crown |
| `scene.py` | Renderer-agnostic scene model + the anchor / axis / dial mechanism (`DESIGN` §3: *difference = dimension*) |
| `tree.py` | Tree skeleton + `pose()` (the wind verb) |
| `cross.py` | **The CROSS** — template markers × real photo patches |
| `photo_to_tree.py` | The end-to-end recipe. **Run this; don't improvise** (`REFERENCE_TO_NOUN.md`) |
| `backend_3d.py` | 3D backend (the product surface) → ParticleEngine on the GPU |
| `backend_html.py` | HTML backend (the development surface) — same scene model, AI-legible, fast |
| `viewer3d.py` | Orbitable perspective 3D dev viewer (drag to orbit) |
| `viewer_nv.py` | Noun + verb viewer — fixed noun, wind verb applied live |
| `demo_lift.py` | Demo: flat 2D picture → 3D, orbit stills proving real volume |
| `demo_compose.py` | Demo: `blow(construct(picture))` — noun composed with verb |
| `demo_tree_wind.py` | Walking skeleton: one scene model, one wind axis, both backends |

**Two backends, one scene model, on purpose.** The HTML backend is the *development*
surface (fast, legible, checkable); the 3D backend is the *product* surface. They read
the same model and the same anchors, so a disagreement between them is a real bug, not a
rendering difference.

---

## 8. TWO INTAKE METHODS — measured vs authored (and "stylized")

**A genome does not have to come from a scan.** The genome *format* is identical either way; only the source of the numbers differs — and **both land in the same codebook under the same serial numbers.**

| Method | Source | Difficulty | What it captures |
|---|---|---|---|
| **Measured** | scans (3DGS / photogrammetry) | **HARD** — inverse rendering, baked lighting, ill-posed | *reality*: "what weathered steel physically **is**" |
| **Authored** | GLB / OBJ / USD carrying PBR maps | **EASY** — the maps are already light-separated | *an artist*: "what someone **decided** steel looks like" |

Reading DNA off an authored asset is **easier than off a scan**: no inverse rendering, no baked-sunlight problem, no ill-posed optimization. PBR texture maps *are* material-DNA, pre-separated from lighting — that is what makes them PBR.

**"Authored" is not automatically "stylized."** A Quixel-grade PBR material is authored *and* photoreal. **Stylized** is the sub-case where the authoring carries artistic intent over physical fidelity.

> **THE STYLIZED METHOD IS THE VALUABLE ONE.** Harvest material-DNA across a *curated* set of assets that share a look, and the resulting distribution **IS your art direction, as a measurable genome** — not a mood board, but an enforceable distribution you can sample from and reproduce forever. That is exactly the consistency a solo dev cannot otherwise hold across thousands of assets.

**CRITICAL CONSEQUENCE:** because both intakes feed one codebook, **an uncalibrated container forks the same material into two serial numbers.** See §9.

---

## 9. FORMAT CALIBRATION — the genome must never depend on the container

**PROVEN BUG, FOUND AND FIXED.** Loading the *same model* (bonsai @7k, 1,157,141 splats) as `.ply` and as `.splat` exposed that `splat_io.load_ply` applied `sigmoid()` to colour — but INRIA 3DGS stores colour as the spherical-harmonic DC coefficient:

```
rgb = 0.5 + C0 * f_dc          C0 = 0.28209479177387814      (NOT sigmoid)
```

Sigmoid squashes the range and can never reach 0 or 1 (p10 came out **0.143** instead of the true **0.000**), so **the same material produced a different colour genome depending on which file it was loaded from.** Regression test: `calibrate_formats.py`.

After the fix every channel agrees to 4 dp across formats:
`scale 0.0233 | R 0.3704 | G 0.3843 | B 0.4269 | opacity 0.2715`

**KNOWN GAP:** position/axis conventions still differ (`.ply` bbox `[44.53, 43.43, 48.5]` vs `.splat` `[44.53, 26.47, 60.84]`). Rotation-invariant DNA (scale, colour, opacity, anisotropy) is format-safe; **orientation-dependent features (verticality, grain-vs-gravity) still need per-format axis handling.**

**THE SAME BUG CLASS LIVES IN MESHES.** Classic `.mtl` is **Blinn-Phong, not PBR**: `Ns` is *shininess*, not roughness (`roughness ≈ √(2/(Ns+2))`), and there is **no metalness at all**. Import an `.obj` unconverted and the same steel forks into a second serial number — identical failure, different container.

### Format ranking for DNA harvesting
| Format | Material model | Verdict |
|---|---|---|
| **GLB / glTF** | PBR native, textures **embedded** | ⭐ **best** — self-contained (what Objaverse ships) |
| USD / USDZ | PBR native | excellent |
| FBX | PBR-ish, game-pipeline standard | fine, messier |
| OBJ + MTL | Blinn-Phong; PBR only via `Pr`/`Pm`/`Ke` extensions; **external** textures | usable, lossier, **needs conversion** |
| PLY | vertex colours only | splats/geometry only |
| STL | nothing | useless for DNA |

---

## 10. THE EMISSIVE GENOME — light is not matter

A laser blast, engine glow or explosion **emits** light; it does not reflect it. PBR material-DNA is **meaningless** for it — there is no albedo, no roughness, no metalness on a thing that is its own light source. It needs a separate genome class:

```
emissive genome = { colour, intensity, radial falloff (sigma),
                    elongation (length:width), core-to-edge gradient, lifetime }
```

**A Gaussian splat is already the correct primitive.** An anisotropic 3D blob with soft falloff *is* the shape of a plasma bolt. A laser = a handful of emissive Gaussians stretched along the travel axis, additive, unlit.

**GROUND TRUTH IS ON DISK:** `flame.splatv` and `sear.splatv` (4D/dynamic splats) are **real captured emissive volumes**. Measure their splat configuration → a real fire genome → stretch along one axis and recolour → a laser derived from *photographed combustion* instead of a guessed shader. Fire and plasma are physical cousins.

---

## 11. THE CORPUS + THE GATING MAP  (farmed 2026-07-22/23, ~30 GB, license-clean)

Downloads live in `/WorldModel/training_data/downloads/` and are **gitignored** (they will otherwise block the push — a 154 MB weights file did exactly that once).

| Source | Contents | Gate |
|---|---|---|
| `cakewalk/splat-data` | 9 scenes/objects `.splat` (nike, plush, truck, train, stump, garden, bicycle, treehill, room) | **open** |
| `dylanebert/3dgs` | scenes as `.ply` **and** `.splat` (**format-calibration pairs**) + **`cameras.json` poses** + 4D `.splatv` FX | **open** |
| `keijiro-tk/splat-data` | ChristmasTree `.ply` (isolated object) | **open** |
| `Voxel51/gaussian_splatting` | Deep Blending / Tanks&Temples as `.ply` | **open** |
| **INRIA `repo-sam`** | **13 scenes × 39 trained `.ply`** (7k + 30k), 14.7 GB | **open, no account** |
| **`allenai/objaverse`** | **~800k CC objects; 1,156 LVIS categories / 46,207 labelled** | **open (`gated:false`)** |
| `ShapeSplats/*`, `ShapeNet/ShapeSplatsV1` | 12k–51k labelled object splats | **gated** (auto / manual) |
| `DL3DV-10K`, `GaussianWorld/scene_splat_*` | 10,510 scenes / 49k indoor scenes | **gated** (auto) |

**GATING LESSON:** nearly every *large* splat corpus on HuggingFace is `gated: auto` — instant approval, but it requires a signed-in account. **There is no ungated mirror; I looked.** The unlock is one `huggingface-cli login`. **Objaverse and INRIA are the significant exceptions and carry the most value per byte.**

**CAMERA POSES OBTAINED: 611** (bonsai 292, bicycle 194, stump 125). These restore the proper 2D↔3D correspondence the SAM-lift pipeline is built around (a `.ksplat` discards it), and make **bicycle the first real multi-view target for inverse material recovery.**

---

## 12. SPACE-GAME ASSET STRATEGY (four tracks)

| Need | Source | Status |
|---|---|---|
| **Materials** (hull plate, rust, chrome, glass, rubber) | scans — **truck / train / bicycle are a sci-fi material vocabulary wearing civilian clothes** | ✅ 10 genomes (`space_materials.py`) |
| **Objects / greebles** (shuttles, antennas, pipes, canisters, crates, radar, armor) | **Objaverse** — ungated, CC, LVIS-labelled | ✅ `objaverse_fetch.py` |
| **Ship hulls** | `WorldModel/clay.py` `SHIP_PARAMS` — 24 params (taper, nose, engines, wing sweep, greeble density, hardpoints, wear) | ✅ already existed |
| **Lasers / engine glow** | **emissive genome** (§10) + `flame.splatv` reference | ⚠️ designed, not built |

**You cannot scan a spaceship — but you can scan what one is made of.** Cross procedural hull *morphology* (`clay.py`) with scanned *material-DNA* and the result looks real because its surfaces came from reality. **Greebles are what sell sci-fi:** a hull is a shape until 175 antennas, 36 pipes and 40 canisters are bolted to it.

**HULL LIBRARY RESULT** (`space_materials.py` — joint GPU codebook over truck/train/bicycle):
- **Filter to OPAQUE splats first.** Unfiltered, 63% of genomes were low-opacity edge haze. *Haze is not a material.*
- 10 surface genomes: **#0** smooth bright panel (large **flat** splats), **#2** mid-grey steel, **#8** dark paint/rubber, **#1/#4** rough corroded (**blobby**, aniso 0.57–0.61), **#9** fine trim detail.
- **Splat SHAPE carries material identity** — #0 and #1 share brightness but differ flat-vs-blobby.
- **HONEST LIMIT:** these are *appearance* genomes (capture lighting baked in), **not** full PBR. Converting them needs the inverse recovery — for which bicycle's 194 poses are now the first real target.
