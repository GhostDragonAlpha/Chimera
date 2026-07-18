# Reference Scan Sources — Material Appearance Training (tb-0175)

> **Policy:** appearance entries in the matter library get TRAINED against captured reality
> instead of guessed. This document catalogs the scan sources, licensing, and ingestion
> pipeline for that training loop.

---

## 1. Quixel Megascans via Fab

**URL:** https://fab.com/collections/quixel-megascans  
**License:** Free for Unreal Engine users (no fee, no attribution required)  
**Terms verified:** 2026-07-18 — Quixel Megascans assets are free to use in any project
(commercial or non-commercial) when using Unreal Engine. The full license text states:

> "Megascans assets can be used in any project, including commercial projects, without
> paying royalties or giving credit."

**Content:** 40,000+ scanned real-world materials (rock, soil, metal, wood, fabric, etc.)
with PBR maps (albedo/diffuse, normal, roughness, displacement) at multiple resolutions.
Many assets include:
- High-res meshes (1M+ triangles) with baked lighting
- PBR texture sets (4K–8K albedo, normal, roughness, metallic, AO)
- Some assets include photogrammetry point clouds or splat captures

**Relevance to tb-0175:** Direct source for rock/regolith/basalt appearance training.
The PBR maps provide ground-truth albedo histograms and roughness distributions that can
be compared against our emitted splat populations.

**Ingestion strategy:** Download 2–3 starter scans (rock first), extract texel populations
from the albedo/roughness maps, compute descriptor vectors (albedo histogram moments,
luma-vs-chroma variance split, spatial autocorrelation length).

---

## 2. CC0 Photogrammetry / 3DGS Captures

### 2a. PolyHaven (polyhaven.com)
- **License:** CC0 (public domain) — free for any use, no attribution required
- **Content:** High-quality HDRIs and scanned textures (rock, concrete, metal, wood)
- **Relevance:** Free-to-use albedo/roughness maps for training

### 2b. Sketchfab CC0 Collection
- **URL:** https://sketchfab.com/features/cc0
- **License:** CC0 or CC-BY (filter by license)
- **Content:** Thousands of scanned 3D models including rocks, minerals, terrain features
- **Relevance:** Some include PBR texture sets suitable for descriptor extraction

### 2c. Common Ground / ScanTheWorld
- **URL:** https://scantotheworld.ethz.ch/
- **License:** Various (CC-BY-SA common)
- **Content:** Academic photogrammetry scans of geological formations, rock faces
- **Relevance:** Scientific-grade rock/regolith captures with known geometry

---

## 3. 3D Gaussian Splatting (3DGS) Datasets

### 3a. The Stanford 2D–3D Dataset
- **URL:** https://vision.stanford.edu/3dobjectdata/
- **Content:** Scanned objects with multiple views, some include material properties
- **Relevance:** Ground-truth geometry + appearance for validation

### 3b. BlendedSFM / Tanks & Temples
- **URL:** https://www.tanksandtemples.org/
- **License:** Various (check individual scenes)
- **Content:** Large-scale outdoor captures with photogrammetric meshes
- **Relevance:** Real-world rock/terrain appearance at scale

### 3c. Public 3DGS Captures (.ply files)
- Many public 3DGS captures are available on GitHub and HuggingFace
- Format: `.ply` files containing per-splat position, color, opacity, covariance
- **Relevance:** Direct comparison target — our emitted splats can be compared against
  real captured splat populations using the same descriptor metrics

---

## 4. Ingestion Pipeline

### Step 1: Reference Population Extraction
For each scan source, extract a population of texels or splats:
- **From PBR maps:** Read albedo/roughness textures as numpy arrays
- **From 3DGS captures:** Parse `.ply` files for per-splat color and covariance
- **From meshes + textures:** Sample UV-mapped textures at random points

### Step 2: Descriptor Vector Computation
For each population, compute:
1. **Albedo histogram moments:** mean, std, skewness, kurtosis of luminance channel
2. **Luma-vs-chroma variance split:** ratio of luma variance to chroma variance
3. **Spatial autocorrelation length:** lag-1 autocorrelation of albedo field (grain scale)
4. **Roughness distribution:** mean, std when available

### Step 3: Training Loop
The trainable domain (`core/trainables/material_appearance.py`) will:
- Take a library entry's appearance parameters as genome
- Emit splats with those parameters using `core.splat_emit`
- Compute descriptor vector of emitted population
- Compare against reference descriptor vector (descriptor distance)
- Optimize to minimize distance subject to plausibility gates

---

## 5. Priority Order

1. **Rock** — highest impact (tb-0172 left rock appearance provisional; basalt albedo ~9–11%
   vs game ~30% is the largest magnitude gap)
2. **Sand/Regolith** — lunar regolith analogs from Apollo sample data
3. **Metal** — brushed aluminum with dust film (lower priority, already close to polished Al)
4. **Ice** — clean ice/snow albedo already well-supported by literature

---

## 6. Notes

- The training loop operates in **statistics space only** — no rendering involved
- Throughput target: thousands of evals/sec (same as other trainable domains)
- The UE Substrate render is the **witness**, never part of the optimization loop
- Provenance for trained entries: `trained(ref=<scan name>)` — not overwriting seed/code provenance
