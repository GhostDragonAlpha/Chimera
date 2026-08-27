# RESEARCH 2026-08-26 — real monkey geometry sources for the CAD body

Commissioned by the operator: replace the procedural sphere/capsule monkey in
`tools/split_creature.py::build_monkey()` with geometry that actually looks like a
monkey, better than spheres. The pipeline slot being filled is
`tools/cad_sample.py::load_glb_triangles`, which consumes **watertight triangle
meshes** — the reference bear (`models/cad_bear/cad_bear.glb`) is 59,712 tris /
~30.8k verts as **19 separate watertight per-part shells with UVs**. Physics
mass/inertia come from those triangles; "regions" (paint/labels) are named
predicates over `(part_id, uv)`. So the ideal source is a watertight, UV'd,
per-part primate mesh in GLB/OBJ/FBX at ~5k–200k tris under an open license.

Species note: macaque / marmoset / any clearly-identifiable primate is acceptable;
each candidate below states its species or "unspecified."

## What we actually need (the shape of the answer)

Three distinct categories, and they are NOT interchangeable:

1. **(A) Ready-to-use meshes** — watertight triangles + UVs, drop into
   `load_glb_triangles` after at most a trimesh cleanup pass. This is what would
   actually replace `build_monkey()`.
2. **(B) Real-capture scans needing cleanup** — museum / photogrammetry captures.
   Highest fidelity "real" geometry, but skeletal or raw-scan: needs decimation,
   hole-filling, UV unwrap, and part splitting before it is pipeline-legal.
3. **(C) Skeletal / proportion references only** — musculoskeletal models that give
   skeleton + joint placement + segment proportions. No surface mesh; useful for a
   *parametric rebuild* of `build_monkey()` with correct macaque proportions, not as
   a drop-in asset.

## Ranked candidate table

| # | Source | Category | Species | License (exact) | Format | Poly count | Per-part? | UVs | Friction | Verdict for our pipeline |
|---|--------|----------|---------|-----------------|--------|-----------|-----------|-----|----------|--------------------------|
| 1 | **Objaverse / Objaverse-XL** (HuggingFace) | A | mixed/unspecified | Dataset CC-BY-4.0; individual models keep original licenses — must check per asset | GLB/OBJ/FBX/STL | varies, many in sweet spot | often yes (game assets) | usually yes | HF account + `huggingface_hub`; text search via CLIP embeddings | **Best ready-to-use pool.** Large monkey population, but no single verified "the" model; per-asset license must be checked. |
| 2 | **Sketchfab** (search "monkey"/"macaque", CC0/CC-BY filter) | A | mixed/unspecified | Per-model: CC0 or CC-BY (filterable); some all-rights-reserved | GLB/OBJ/FBX (viewer + download) | varies, many in sweet spot | often yes | usually yes | Web UI; account needed for downloads; no bulk API without key | **Best human-curated browsing.** Could not verify specific model URLs this session — search page returned generic content. |
| 3 | **TurboSquid free section** | A (benchmark) | mixed/unspecified | Per-model, mostly all-rights-reserved / paid; a small free subset | OBJ/FBX | varies | often yes | usually yes | Web UI; account for downloads | Quality benchmark only — what "good" looks like. 32 free OBJ monkeys noted earlier; not verified live this session. |
| 4 | **Primate Phenotypes** (MorphoSource, AMNH et al.) | B/C | great apes + African/Asian/South American monkeys | Free on MorphoSource (NSF-funded open repo); per-deposit terms apply — verify before use | CT series + surface meshes (OBJ-class) | high-res scans; needs decimation to our range | skeletal elements, not soft-tissue body parts | no (raw scan) | MorphoSource account required | **Highest-fidelity real capture**, but it is *skeletal* morphology (bones/CT), not a soft-body monkey. Great for proportions/joints (C); wrong shape for a drop-in body mesh (A). |
| 5 | **Smithsonian Human Origins 3D Collection** | B | primates (incl. monkeys) | Non-commercial use only — NOT CC0; attribution required | STL/OBJ-class scans | varies | per-specimen | no | Web download; page noted "temporarily unavailable" as of Jan 2021 — **status unverified this session** | Real primate captures, but non-commercial license is a hard flag for anything we ship. |
| 6 | **OpenSim Japanese-macaque bipedal model** (Oku, Ide & Ogihara, *Commun Biol* 2021) | C | Japanese macaque (*Macaca fuscata*) | Open access paper; model files in supplementary — verify exact terms | segment/stick model (no surface mesh) | n/a (segments) | full skeleton + joints | no | Paper PDF direct; supplementary data link on article page | **Best proportion/joint reference** for a parametric rebuild. No surface geometry at all. |
| 7 | **Academic macaque head CT/MRI** | B/C (partial) | rhesus/Japanese macaque | varies per dataset, often CC-BY or restricted | NIfTI / DICOM / STL | head only | head only | no | per-dataset | Head-only; partial. Useful for skull/face proportions, not a body. |

## Per-candidate detail (verified URLs + licenses)

### 1. Objaverse / Objaverse-XL — HuggingFace  *(Category A)*
- URL: https://huggingface.co/datasets/all-objaverse/all-objaverse-v2 (and the XL successor). Dataset card states **CC-BY-4.0 for the dataset**; individual models retain their original licenses, so a specific monkey asset's license must be checked before use.
- Query path: text search ("monkey") is done via CLIP-style embeddings over model renders; download is `huggingface_hub` snapshot / per-file by SHA1. Requires an HF account (free).
- Species: mixed and largely unspecified in metadata — you get a *population* of monkey models, not one canonical macaque.
- Poly count / UVs / per-part: varies asset to asset; game-style assets frequently have UVs and separate meshes for head/torso/limbs, which is exactly our shape. Many fall in the 5k–200k tri sweet spot after decimation.
- **Honesty:** I did NOT identify or verify a specific monkey asset ID this session (that requires running the embedding search against the live index). The dataset's existence, license model, and query mechanism are established; the specific "best monkey" is an unverified selection step.

### 2. Sketchfab — CC0/CC-BY monkey models  *(Category A)*
- URL: https://sketchfab.com/search/models?q=monkey&licenses=cc0 (and `q=macaque`, `q=marmoset`). License filter is a first-class UI control; downloadable models are marked.
- Species: mixed/unspecified per model page.
- Format / poly / UVs / per-part: stated on each model page; GLB/OBJ/FBX export for downloadable items; game assets often per-part + UV'd.
- Friction: web browsing is open, but **downloading requires a free account**; there is no bulk text-search API without an API key.
- **Honesty:** the search page fetched this session returned generic site chrome, not specific model cards (Sketchfab renders results client-side). I could NOT verify any individual monkey model URL, poly count, or license from the fetch. Treat every Sketchfab candidate as "browse and confirm on-page" — do not cite a specific model here without opening it.

### 3. TurboSquid free section  *(Category A benchmark)*
- URL: https://www.turbosquid.com/Search/3D-Models/monkey (free filter). Earlier context noted ~32 free OBJ monkeys; **not re-verified live this session.**
- License: per-model, predominantly all-rights-reserved / paid; the free subset is a small minority and each has its own terms.
- Role here: a **quality benchmark** for what "good" looks like (topology, UVs, part splits), not a recommended source — most are paid or restricted.

### 4. Primate Phenotypes — MorphoSource / AMNH et al.  *(Category B/C)*
- Paper: *Primate Phenotypes: A Multi-Institution Collection of 3D Morphological Data Housed in MorphoSource*, Scientific Data (2024). https://www.nature.com/articles/s41597-024-04261-5 (PDF confirmed live via search this session).
- Repository: MorphoSource — https://github.com/MorphoSource/MorphoSource (repo confirmed live) and the project pages on morphosource.org. AMNH news page confirms "scans of nearly 400 individual specimens ranging from great apes to monkeys from Africa, Asia, and South America," now available worldwide on MorphoSource.
- Content: **>6,000 3D scans (media) representing skeletal morphologies of 386 individual primate specimens** — surface scans + CT image series of *bones*, not soft-tissue bodies.
- License: free access via the NSF-funded open repository; per-deposit terms apply and should be checked before any redistribution. **Account required.**
- Fit: this is the highest-fidelity "real capture" option, but it is **skeletal** — wrong shape for a drop-in soft-body monkey (A), excellent as a proportion/joint reference (C). If we want a *real* macaque's actual bone proportions to drive a parametric rebuild, this is the source.

### 5. Smithsonian Human Origins 3D Collection  *(Category B)*
- URL: https://humanorigins.si.edu/evidence/3d-collection — primate 3D models "available for download, but only for non-commercial use."
- **License flag:** non-commercial-only is a hard constraint if anything we build ships or is published. Not CC0.
- **Honesty:** the page noted the primate 3D collection was "temporarily unavailable" as of Jan 12, 2021; I did NOT verify current availability this session.

### 6. OpenSim Japanese-macaque bipedal model  *(Category C)*
- Paper: Oku, Ide & Ogihara, *Forward dynamic simulation of Japanese macaque bipedal locomotion…*, Communications Biology 4:308 (2021). https://www.nature.com/articles/s42003-021-01831-w — **confirmed live and open access this session.**
- Content: a **two-dimensional neuromusculoskeletal model** of *Macaca fuscata* — segments, joints, muscle paths. It gives skeleton + joint placement + segment proportions validated against measured gait data (cycle 0.71 s, stride 0.72 m, etc.).
- **No surface mesh.** Model files are in the paper's supplementary data; exact file format/terms should be confirmed on the article page before use.
- Fit: the best *proportion/joint* reference for rebuilding `build_monkey()` parametrically with real macaque limb ratios and joint centers — but it cannot feed `load_glb_triangles` directly.

### 7. Academic macaque head CT/MRI  *(Category B/C, partial)*
- Head-only volumetric scans of rhesus/Japanese macaques exist in several academic datasets (NIfTI/DICOM; some STL exports). License varies per dataset (often CC-BY or restricted). **Head only** — useful for skull/face proportions, not a body. No specific URL verified this session; treat as "locate the exact dataset before relying on it."

## RECOMMENDATION

Ranked picks, with integration path:

1. **Objaverse / Objaverse-XL (HuggingFace)** — *primary ready-to-use source.*
   Integration: run a CLIP text search for "monkey"/"macaque," shortlist 3–5 assets that are watertight + UV'd + per-part in the 5k–200k tri band, **check each asset's individual license** (dataset is CC-BY-4.0 but models keep original licenses), download via `huggingface_hub`, then run a trimesh cleanup pass (merge verts, fill small holes, decimate to target) and emit per-part shells as GLB into the same shape `load_glb_triangles` already consumes — i.e., replace the body of `build_monkey()` in `tools/split_creature.py` with a loader that reads the chosen asset's parts instead of synthesizing spheres/capsules. This is the only category-A source with a large enough monkey population to actually find something good, and it is scriptable (no manual browsing).

2. **Sketchfab CC0/CC-BY** — *best human-curated fallback / quality check.*
   Integration: browse `q=monkey&licenses=cc0`, pick a downloadable per-part UV'd model, download with a free account, same trimesh cleanup + GLB emit as above. Use it to sanity-check that the Objaverse pick is genuinely "looks like a monkey," and as the source if a specific CC0 model clearly beats everything in Objaverse. (No specific model URL is cited here because none was verified this session.)

3. **OpenSim Japanese-macaque model + Primate Phenotypes** — *proportion/joint references, not drop-in assets.*
   Integration: use the Oku et al. macaque segment lengths and joint centers (and, if we want real bone proportions, a specific specimen from Primate Phenotypes) to **tune the parametric `build_monkey()`** so that even our procedural fallback has correct macaque limb ratios and joint placement. This is complementary to picks 1–2, not a replacement for them.

Single best recommendation: **Objaverse / Objaverse-XL via HuggingFace**, because it is the only source that (a) actually contains many monkey meshes, (b) is scriptable end-to-end without manual browsing or purchase, (c) frequently ships UVs + per-part shells matching our exact pipeline shape, and (d) sits under a CC-BY-4.0 dataset license with per-asset licenses we can verify before committing. The one non-negotiable gate: **verify the individual asset's license** — the dataset license does not override it.

## What I could NOT verify this session

- **No specific Sketchfab monkey model URL, poly count, or license.** The search page rendered client-side and returned only site chrome; every Sketchfab candidate must be confirmed on its own model page before citation.
- **No specific Objaverse monkey asset ID / SHA1.** Identifying the best individual asset requires running the live CLIP embedding search against the index — that is a selection step, not yet done. The dataset's existence, CC-BY-4.0 license model, and query/download mechanism are established; the specific pick is unverified.
- **TurboSquid free-monkey count (32) was from earlier context**, not re-fetched live this session.
- **Smithsonian Human Origins 3D Collection current availability** — page historically flagged "temporarily unavailable" (Jan 2021); not confirmed up or down today.
- **Exact file format and license terms of the Oku et al. supplementary model files** — paper is open access, but the supplementary data's specific terms were not opened this session.
- **Primate Phenotypes per-deposit license terms** — repository is free/open (NSF-funded), but individual deposit terms should be checked before redistribution.
- **Academic macaque head CT/MRI** — no specific dataset URL verified; listed as a category, not a confirmed source.
