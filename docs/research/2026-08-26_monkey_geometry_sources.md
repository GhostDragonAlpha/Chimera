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

---

## RESULTS — 2026-08-27 Objaverse monkey shortlist + staging run

Method: queried the original Objaverse LVIS annotations (`objaverse.load_lvis_annotations()`) for categories `monkey` and `baboon`, giving 99 downloadable UIDs.  Per-model license verified from the Objaverse annotation (sourced from the Sketchfab API), not the dataset-level CC-BY-4.0. 12 candidates were downloaded via `objaverse.load_objects()` into `.tmp/monkey_assets/raw/`, inspected with `trimesh`, repaired with `trimesh.repair.fill_holes/fix_winding/fix_inversion`, then exported as **single-mesh, multi-primitive GLBs** into `.tmp/monkey_assets/staged/`. Each primitive carries the original geometry name on its material, matching the consumption shape of `tools/cad_sample.py::load_glb_triangles`. All staged files were verified to load through that function.

### License verification

All Objaverse/Sketchfab candidates in this run carried per-model `license: "by"`, which Sketchfab maps to **Creative Commons Attribution 4.0 International (CC-BY-4.0)**.  Evidence is the Objaverse annotation record (itself pulled from the Sketchfab API) and the live Sketchfab model page.  Two non-CC-BY candidates (`by-nc-sa`, `by-nc`) were present in the 99-UID pool and were excluded from download.

### Staged survivors (5)

| # | Objaverse UID | Sketchfab name | Author | Per-model license | Source URL | Staged GLB | Total tris | # parts |
|---|---------------|----------------|--------|-------------------|------------|------------|------------|---------|
| 1 | `22d1626853964fc995cda04814792ae5` | Cymbal Monkey | muneto_bm | CC-BY-4.0 | https://sketchfab.com/3d-models/22d1626853964fc995cda04814792ae5 | `.tmp/monkey_assets/staged/22d1626853964fc995cda04814792ae5.glb` | 54,234 | 22 |
| 2 | `8955fb5b9c9b4e169456ccbae7c465f7` | MONKEY | dinesdiabolik | CC-BY-4.0 | https://sketchfab.com/3d-models/8955fb5b9c9b4e169456ccbae7c465f7 | `.tmp/monkey_assets/staged/8955fb5b9c9b4e169456ccbae7c465f7.glb` | 34,176 | 2 |
| 3 | `1534c1b10378454697ea2f2aa888270c` | King Monkey | TdoubleU8 | CC-BY-4.0 | https://sketchfab.com/3d-models/1534c1b10378454697ea2f2aa888270c | `.tmp/monkey_assets/staged/1534c1b10378454697ea2f2aa888270c.glb` | 42,511 | 2 |
| 4 | `9906e5863a89474da4ee4e178a2daa28` | Monkey | saranav | CC-BY-4.0 | https://sketchfab.com/3d-models/9906e5863a89474da4ee4e178a2daa28 | `.tmp/monkey_assets/staged/9906e5863a89474da4ee4e178a2daa28.glb` | 8,436 | 9 |
| 5 | `f4783633129a433abf0d2b313db86f43` | Monkey scan with improvements | gooseman | CC-BY-4.0 | https://sketchfab.com/3d-models/f4783633129a433abf0d2b313db86f43 | `.tmp/monkey_assets/staged/f4783633129a433abf0d2b313db86f43.glb` | 147,229 | 2 |

Attribution text (same form for all five): `<Model Name> by <Author> on Sketchfab, licensed under CC-BY-4.0`.

### Per-part counts from `load_glb_triangles`

```
22d1626853964fc995cda04814792ae5.glb (Cymbal Monkey) — 22 parts, 54,234 tris
  pSphere42_lambert5_0: 2,247 verts, 4,262 tris
  polySurface5_blinn1_0: 2,188 verts, 4,224 tris
  pSphere25_blinn11_0: 3,237 verts, 6,400 tris
  polySurface9_blinn1_0: 1,146 verts, 2,232 tris
  pCube14_blinn3_0: 1,255 verts, 2,480 tris
  pSphere40_blinn10_0: 2,282 verts, 4,560 tris
  pCube12_blinn4_0: 991 verts, 1,952 tris
  pSphere43_blinn10_0: 2,282 verts, 4,560 tris
  pCube23_blinn3_0: 1,255 verts, 2,480 tris
  pCube13_lambert2_0: 448 verts, 896 tris
  pSphere35_lambert4_0: 725 verts, 1,344 tris
  r_ear_helix3_lambert7_0: 1,998 verts, 3,884 tris
  pSphere36_blinn6_0: 1,369 verts, 2,400 tris
  pSphere36_blinn9_0: 740 verts, 1,120 tris
  pSphere36_lambert6_0: 42 verts, 48 tris
  pSphere30_lambert4_0: 2,575 verts, 4,960 tris
  pSphere33_blinn12_0: 356 verts, 704 tris
  pCube21_blinn4_0: 991 verts, 1,952 tris
  pSphere27_lambert6_0: 164 verts, 324 tris
  pCube22_lambert2_0: 448 verts, 896 tris
  pSphere28_lambert6_0: 164 verts, 324 tris
  polySurface10_blinn1_0: 1,146 verts, 2,232 tris

8955fb5b9c9b4e169456ccbae7c465f7.glb (MONKEY) — 2 parts, 34,176 tris
  SALLY_body_0: 16,154 verts, 32,128 tris
  SALLY_EYES_0: 1,050 verts, 2,048 tris

1534c1b10378454697ea2f2aa888270c.glb (King Monkey) — 2 parts, 42,511 tris
  Object_0: 17,776 verts, 35,257 tris
  Object_1: 3,615 verts, 7,254 tris

9906e5863a89474da4ee4e178a2daa28.glb (Monkey) — 9 parts, 8,436 tris
  Object_0: 2,115 verts, 4,040 tris
  Object_1: 39 verts, 64 tris
  Object_2: 876 verts, 1,704 tris
  Object_3: 70 verts, 96 tris
  Object_4: 472 verts, 920 tris
  Object_5: 28 verts, 36 tris
  Object_6: 469 verts, 910 tris
  Object_7: 32 verts, 42 tris
  Object_8: 377 verts, 624 tris

f4783633129a433abf0d2b313db86f43.glb (Monkey scan with improvements) — 2 parts, 147,229 tris
  Object_0: 62,229 verts, 118,313 tris
  Object_1: 20,096 verts, 28,916 tris
```

### Rejections (7)

| UID | Name | Reason |
|-----|------|--------|
| `c488eebd284a49178c764d9cad0c0ecb` | Rafiki the baboon | 1,042,436 tris — exceeds 200 k tri budget |
| `6805de96391f4ad7b1933c041d756d27` | Japanese Monkey | 438,519 tris — exceeds 200 k tri budget |
| `ec43bd941ecc447e86a89b442a1f344a` | Free Base Chimp | Chimp, not monkey/macaque; superseded by `f478...` real-monkey scan |
| `a7005fad11824d4199b952f45384d226` | Monkey- Free | Single-part mesh, 6,826 tris; poor part separation |
| `059ddf8d773748a0aa32c778897e711e` | Kako | 2,736 tris — below 5 k tri minimum |
| `b7cd9d66f1fd446ba47bf43b9b2fb9ec` | Big monkey | 95,826 tris but single-part mesh; not per-part/segmentable |
| `8bf18c30f52142c58229728492f58016` | Baboon | 507,202 tris — exceeds 200 k tri budget |

### Watertight / repairability note

Repair was attempted on every geometry with `trimesh.repair.fill_holes`, `fix_winding`, and `fix_inversion`. A follow-up pass with `pymeshlab` `meshing_close_holes` was also tried on the Cymbal Monkey. **No body-sized shell became fully watertight.** A few small accessory parts did (e.g., `pSphere40_blinn10_0`, `pCube13_lambert2_0` in Cymbal Monkey; `Object_1` in King Monkey), but the main body shells retain boundary edges and are not watertight. This is typical for Sketchfab game-character exports and photogrammetry scans. The staged GLBs are therefore pipeline-loadable and per-part, but **not yet physics-legal for `cad_sample.py` volume sampling** without a more aggressive reconstruction step (e.g., Poisson / SDF shrink-wrap or manual re-topo). This was reported honestly rather than fabricating watertight status.

### Files on disk

- Raw downloads: `.tmp/monkey_assets/raw/*.glb` (5 files)
- Staged per-part GLBs: `.tmp/monkey_assets/staged/*.glb` (5 files)
- Machine-readable stage report: `.tmp/monkey_assets/staged/_stage_results.json`
