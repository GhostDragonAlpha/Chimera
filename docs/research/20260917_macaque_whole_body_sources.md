# Report — work.creature.macaque_whole_body_sources (web research + intake proposal)

Date: 2026-09-17 · Base commit a6e6acf26dacb37be9f42c2589f4417ae38247d5 (read-only; worker scratch only)
Method note: two corrections to the assignment surfaced during research — (1) s42003 is
**Communications Biology**, not Scientific Reports; (2) the Sketchfab "rhesus macaque"
full-skeleton scan is from the **Natural History Museum, University of Pisa**, not Oslo.

---

## 0. FALSIFIER VERDICT (stated first)

Prediction tested: "at least one fully downloadable, license-clear, metric macaque skeletal
source exists beyond the cranium."

**REFUTED in its strict form.** The only fully downloadable, permissively licensed
(“CC0 … without contacting the Smithsonian”), metrically calibrated macaque skeletal assets
found anywhere are the **Smithsonian USNM 15259 cranium + mandible pair** — both head
elements. Everything beyond the head is either:

- downloadable but **non-commercial-only** (CC BY-NC: MorphoSource Primate Phenotypes,
  Copes 2016) — the graph record's own rule ("Do not incorporate noncommercial-only meshes
  into a commercial game without separate authorization") makes these NOT license-clear
  for shipping; or
- **ON_REQUEST** (Ogihara/Kyoto whole-body model; Kyoto PrINTEG PRICT CT; Pisa whole
  skeleton); or
- **PAPER_ONLY** (Oku 2021 Table 1; Vilensky 1979 tables).

The closest thing to the prediction is MorphoSource project **00000C706 "Primate
Phenotypes"**: downloadable (free account), metric CT, 9 Macaca individuals incl.
postcranial/articulated material — but CC BY-NC. So: *downloadable exists; license-clear
does not.* Request paths are given in §3.

---

## 1. LEAD DOSSIERS (5 pinned + 5 discovered)

Classification vocabulary: DOWNLOADABLE_NOW / ON_REQUEST / PAPER_ONLY / DEAD_LINK.

### L1+L2 (pinned) — Oku, Ide & Ogihara 2021, *Communications Biology* 4, art. s42003-021-01831-w (+ its Table 1)
- What it contains: forward-dynamic simulation of Japanese macaque bipedal walking. A
  9-link 2D musculoskeletal model ("The model consists of nine links representing the
  head, forelimbs, and trunk (HAT), thighs, shanks, and feet… two parts—a tarsometatarsal
  and a phalangeal part") derived from the Ogihara 3D whole-body model; 10 principal
  muscles. **Table 1 "Dimensions and inertial parameters of the limb segments"** (fetched,
  verified):
  - HAT: mass 8.184 kg, length 0.482 m, COM 52 %, I = 2.07E−02 kgm²
  - Thigh: 0.557 kg, 0.163 m, COM 41 %, 1.61E−03
  - Shank: 0.269 kg, 0.182 m, COM 40 %, 7.01E−04
  - Foot: 0.080 kg, 0.074 m, COM 62 %, 5.49E−05
  - Phalanges: 0.021 kg, 0.045 m, COM 50 %, 6.26E−06
  Units: kg / m / kgm² (metric, SI). Implied whole body ≈ 10.0 kg. NOTE: forelimbs are
  folded into HAT — Table 1 does NOT give arm segments; hindlimb + HAT only. One specimen,
  one species (**Macaca fuscata**), same animal as Ogihara 2009 lineage.
- License: paper CC BY 4.0 — quote: "Creative Commons Attribution 4.0 International
  License, which permits use, sharing, adaptation, distribution and reproduction in any
  medium or format, as long as you give appropriate credit…". Dataset: "The datasets
  generated during and/or analysed during the current study are available from the
  corresponding author on reasonable request." Code likewise. **Paper license ≠ dataset
  license — exactly the record's rule.**
- Asset status: **PAPER_ONLY** (data ON_REQUEST; no deposited model).
- Resolution/format: tables in HTML; no geometry.
- Fitness: (a) whole-skeleton geometry — no. (b) segment mass/inertia — YES (hindlimb +
  HAT, 1 specimen, M. fuscata). (c) joint references — indirect (figures only).
- URLs: https://www.nature.com/articles/s42003-021-01831-w · /tables/1

### L3 (pinned) — Ogihara et al. 2009, *Am J Phys Anthropol* 139(3):323–338, PMID 19115360
- "Development of an anatomically based whole-body musculoskeletal model of the Japanese
  macaque (Macaca fuscata)" — "constructed… based on computed tomography and dissection of
  a cadaver"; "The skeleton was modeled as a chain of 20 bone segments connected by
  joints"; "Joint centers and rotational axes were estimated by joint morphology"
  (quadric fits); muscle mass/fascicle length/PCSA recorded; muscle paths as line
  segments. Adult male, ~10 kg (specimen details confirmed via the same group's Saito
  2021 hand-model paper).
- License: paper paywalled (Wiley, DOI 10.1002/ajpa.20986). No dataset deposited; no
  license for the model exists because no asset exists publicly.
- Asset status: **PAPER_ONLY / ON_REQUEST**. Corroborating data statement from the same
  group (Saito et al. 2021, PMC8693514): "The raw data supporting the conclusions of this
  article are available by the authors upon reasonable request."
- Fitness: (a) no public geometry (CT exists privately). (b) YES if released — the single
  best whole-body inertial dataset for any macaque. (c) YES — 20-segment joint
  centers/axes, the best joint-morphology reference in existence for M. fuscata.
- URL: https://pubmed.ncbi.nlm.nih.gov/19115360/

### L4 (pinned) — Kyoto University PRI/EHUB PrINTEG, PRICT sub-database
- What it contains: catalog of **CT scans of dry bone specimens**, individual-ID linked
  (PRISK skeletal collection). Fetched page 1 (db=prict): 79 macaque rows — Macaca fuscata
  (48), M. cyclopis (15), M. cyclopis×fuscata (14), M. sinica (1), M. silenus (1); parts:
  Cranium (44), Mandible (37), plus scattered long bones (scapula/fibula/tibia/femur/
  radius/ulna/humerus — some rows are ape, not macaque). Voxel resolutions ~0.195–0.274 mm,
  slice thickness 0.1–0.3 mm, DICOM-class CT. Institution column: Gunma Museum of Natural
  History / Primate Research Institute, Kyoto University.
- License/terms: none automated. EHUB resource page: "please first consult with an EHUB
  faculty member… it is necessary to apply the Cooperative Research Program (Resource Use)
  and obtain permission in advance… we also ask that you acknowledge and agree to the terms
  and conditions of use and the fees for use." → formal joint-research application, fees.
- Asset status: **ON_REQUEST** (database is ONLINE and reachable; data are not).
- Companion note: the older KUPRI Digital Morphology Museum (dmm.pri.kyoto-u.ac.jp) did
  not respond at all today (connection timeout, HTTP 000) → **DEAD_LINK** as of 2026-09-17;
  PrINTEG appears to be its living successor.
- Fitness: (a) partial — excellent metric head CTs, a few long bones; (b) no; (c) yes.
- URLs: https://www2.ehub.kyoto-u.ac.jp/databases/printeg_view/printeg.php?db=prict ·
  https://www.ehub-kyoto-u.com/en/about/resourse

### L5 (pinned) — Smithsonian 3D, *Macaca sinica* cranium (+ discovered companion mandible)
- Object: dry-bone surface scan (photogrammetry), NMNH Vertebrate Zoology – Mammals Div.,
  specimen **USNM 15259**, *Macaca sinica* (toque macaque). Verified via the Voyager
  document JSON (https://3d-api.si.edu/content/document/fb42ecf6-2756-4b6f-bbb0-eb91f31964e5/document.json):
  - units **mm**; cranium mesh "USNM15259_cranium_-300_dec", bbox 79.2 × 62.6 × 125.6 mm
    (adult toque macaque skull — metric sanity check passes);
  - downloadable derivatives: GLB 150k faces / 4096 tex, 5,841,904 bytes (high),
    2,450,324 (medium), 1,351,908 (low);
  - **mandible** (object uuid 8105e6f9-c724-46f1-8fd5-d550f8171e49, verified via its
    document.json), file
    "USNM15259_mandible_-300-150k-4096-high.glb", 2,426,480 bytes, bbox 67.6 × 43.5 × 80.8 mm;
    object URL: https://3d.si.edu/object/3d/macaca-sinica-mandible:8105e6f9-c724-46f1-8fd5-d550f8171e49
- License: object pages carry the CC0 dedication; indexed page text: **"You can copy,
  modify, and distribute this work without contacting the Smithsonian."** CAVEAT to record:
  the package document.json embeds `"copyright": "(c) Smithsonian Institution. All rights
  reserved."` — a default metadata string that conflicts with the CC0 mark; snapshot the
  object page and quote both at intake. Also note "Macaca cyclopis: Cranium" exists in the
  same NMNH series.
- Asset status: **DOWNLOADABLE_NOW** (the only license-clear one).
- Fitness: (a) head geometry only — but license-clean and metric; (b) no; (c) TMJ region
  only.

### A1 (discovered — strongest new lead) — "Primate Phenotypes", MorphoSource project 00000C706
- Almécija et al. 2024, *Scientific Data* 11 (PMC11655552, PubMed 39695181): 6,192 3D
  media, 386 specimens, 47 genera; scanned at AMNH, NMNH, RMCA (Belgium), CMNH, Stony
  Brook; **Table 1: Macaca = 9 individuals / 238 media (3.84 %)**; coverage spans crania,
  long bones, hands, feet, and articulated skeletons (medical CT, e.g. a juvenile skeleton
  in articulation is figured for Pan). "All digital specimens are available in the project
  'Primate Phenotypes' (Project ID 00000C706) hosted in the online repository MorphoSource."
- License: **CC BY-NC** — quotes: "all data in this project can be freely downloaded and
  used under a CC BY-NC Creative Commons license"; "the data can be downloaded and reused
  for any non-commercial purposes with the proper attribution"; download requires a free
  MorphoSource account; per-media DOIs must be cited.
- Asset status: **DOWNLOADABLE_NOW** (non-commercial). Operational note: MorphoSource is
  bot-walled (Anubis challenge) — enumeration and download are MANUAL, not scriptable.
- Resolution/format: CT stacks + meshes; voxel sizes per media record (paper's pipeline:
  medical CT and microCT; exact per-specimen values on each DOI page).
- Fitness: (a) YES — the only downloadable, specimen-traceable macaque POSTCRANIAL
  geometry found; (b) no (geometry, not inertia; specimen body masses may ride along in
  records); (c) YES for CT-segmented material.

### A2 (discovered) — Copes et al. 2016, *Scientific Data* 3:160061, NHP microCT collection
- 489 microCT datasets of primate **crania and mandibles** ("and certain postcranial
  elements"), includes **Macaca fascicularis** and **Macaca mulatta**; "cubic voxel
  dimensions ranged from 18 microns… to 125 microns for the largest (e.g., Pongo)"; DICOM,
  zipped.
- License: **CC BY-NC** — quote: "The files associated with the current project can be
  downloaded with open access and are tagged with creative commons copyright license of
  CC BY-NC as dictated by the copyright holder, the MCZ. This means the data can be
  downloaded and re-used for non-commercial academic purposes. These limitations are
  maintained as a component of the non-negotiable terms of the MCZ…"
- Asset status: **DOWNLOADABLE_NOW** (NC). Fitness: (a) heads only; (b) no; (c) excellent.
- URL: https://www.nature.com/articles/sdata20161

### A3 (discovered) — Vilensky 1979, *Am J Phys Anthropol* 50(1), PMID 104631
- "Masses, centers-of-gravity, and moments-of-inertia of the body segments of the rhesus
  monkey (Macaca mulatta)": "Seven male and eight female adult rhesus monkey cadavers were
  dismembered in order to determine segmental parameters"; CG as mean % of proximal–distal
  joint distance; **regression equations** to estimate mass/inertia from body weight.
- Asset status: **PAPER_ONLY** (Wiley paywall; no dataset). Fitness: (b) YES — the
  standard population-level inertia dataset for M. mulatta (matches the species of the
  already-imported rhesus arm model — valuable cross-check); (a) no; (c) joint-center
  conventions implied by segment definitions.
- URL: https://pubmed.ncbi.nlm.nih.gov/104631/

### A4 (discovered) — Natural History Museum, University of Pisa, Sketchfab "Rhesus macaque"
- "3D scan of a skeleton of rhesus macaque (Macaca mulatta)", specimen **C 1549**, Artec
  Spider (metric scanner class), 2.5 M triangles / 1.25 M vertices, published 2024-02-19.
- Sketchfab API (api.sketchfab.com/v3/models/8d013971b252478caac9aeeee3620572):
  **isDownloadable: False**, license field empty. → **VIEW_ONLY / ON_REQUEST** (email the
  museum for the mesh + terms). Scale likely true (Artec), but unverified.
- Fitness: (a) whole skeleton if ever released; (b) no; (c) no.
- URL: https://sketchfab.com/3d-models/rhesus-macaque-8d013971b252478caac9aeeee3620572

### A5 (discovered) — BigMaQ / MacAction rhesus body-surface datasets
- BigMaQ (ICLR 2026, arXiv 2602.19874): 8 male *M. mulatta*; "Subject-specific textured
  body surface meshes (high-poly and low-poly)"; "The code and data are publicly available
  at https://martinivis.github.io/BigMaQ/." Dataset-file license NOT stated on arXiv —
  verify before any use. MacAction (PLOS Biology 2025): realistic macaque avatar is
  **proprietary, not shared** — excluded.
- Fitness: skin/fat layer reference only — NOT bone, NOT a substitute for any of the
  above (record's rule: never relabel a skin surface as scanned bone).

---

## 2. RANKED INTAKE PROPOSAL

### RANK 1 — MorphoSource "Primate Phenotypes" 00000C706 (manual, account-gated)
The only postcranial macaque geometry on earth that is downloadable today. NC license is
acceptable for **reference/calibration intake** under a separately tagged asset class; it
must never ship as game content.
Intake record must contain: project URL (https://www.morphosource.org/projects/00000C706/)
+ paper (PMC11655552); for EACH downloaded Macaca media: media DOI + version, holding
institution + catalog number + species/specimen qualifier, modality (CT vs surface), voxel
size or scan metadata, license quote on the media page ("CC BY-NC"), SHA-256 + byte size of
every ZIP/GLB, HTML snapshot of the media page, MorphoSource account identity used, and a
use tag: `reference_only_NC`. Known holes: which of the 9 individuals are which Macaca
species; whether any individual carries tail/caudal or full axial series; per-specimen
scale metadata.

### RANK 2 — Smithsonian USNM 15259 cranium + mandible (download today; license-clean)
Intake record: both object URLs (uuids fb42ecf6-2756-4b6f-bbb0-eb91f31964e5 and
8105e6f9-c724-46f1-8fd5-d550f8171e49); document.json URLs; direct GLB URIs
(https://3d-api.si.edu/content/document/{uuid}/{filename}); expected byte sizes (5,841,904
cranium high; 2,426,480 mandible high); SHA-256 of each; units mm + bbox sanity record;
license quotes (CC0 page sentence + the conflicting embedded "(c) Smithsonian" string);
specimen qualifier USNM 15259 *Macaca sinica*. Also snapshot the "Macaca cyclopis:
Cranium" sibling object seen in the explore list. Known holes: SI has no postcrania.

### RANK 3 — Request path: Ogihara whole-body model (M. fuscata)
Email the corresponding author of Oku 2021 (Naomichi Ogihara, Kyoto University; address in
the paper) citing "available from the corresponding author on reasonable request", asking
for: whole-body model files (geometry + joint coordinates/axes + muscle paths), the
segment inertial parameters, and whether any CT can be shared; state purpose honestly
(anatomical reference for a game-physics creature; ask what license they can grant; NC
acceptance noted). Record request date/response as evidence nodes.

### RANK 4 — Vilensky 1979 table digitization (M. mulatta inertia)
Obtain the PDF (Wiley/library), digitize Tables (segment masses, CG %, moments of inertia,
regression equations), pin with PMID 104631 + DOI 10.1002/ajpa.1330500109. This pairs with
the rhesus arm model already imported (same species) and gives population-level inertia
independent of any download.

### RANK 5 — PrINTEG PRICT via EHUB Cooperative Research Program (ON_REQUEST)
Only if head CTs finer than SI's photogrammetry or macaque long-bone CTs are needed.
Intake record must quote the EHUB terms sentence and record the application, fees, and the
granted license; per-dataset: PRICT ID, individual ID, species, part, resolution (mm),
FOV, institution.

### RANK 6 (optional) — Copes 2016 skulls (CC BY-NC, fine-detail heads);
Pisa C 1549 (email museum for mesh + license — could become the one whole-skeleton
license-clear win if they say yes); BigMaQ project-page license check (skin layer only).

### Species/specimen discipline (record rule: no silent fusion)
- M. sinica — SI USNM 15259 (head only)
- M. fuscata — Ogihara/Oku lineage (single ~10 kg adult male cadaver)
- M. mulatta — Vilensky 1979 (15 cadavers); Primate Phenotypes individuals (species split
  unconfirmed); Pisa C 1549; BigMaQ (8 live males)
- M. fascicularis / M. cyclopis / hybrids — PRICT, Copes
Each asset class keeps its species tag; any fitted/analogous mapping (e.g. fuscata inertia
onto mulatta geometry) must be an explicit declared mapping with scale factors, never a
silent merge.

### Checksums to capture on every download
`sha256sum` + byte size + filename for: SI GLBs (and document.json files), every
MorphoSource ZIP/GLB/DICOM bundle, any emailed model archives, plus HTML/PDF snapshots of
every license page quoted above.

---

## 3. REQUEST-EMAIL PATHS (since most value is on-request)

1. **Ogihara (Kyoto U)** — the whole-body model: cite Oku et al. 2021 Communications
   Biology data statement; ask for model files, joint coordinates, inertia table, CT terms.
2. **EHUB Kyoto** — PrINTEG/PRICT CT: "apply the Cooperative Research Program (Resource
   Use) and obtain permission in advance" (https://www.ehub-kyoto-u.com/en/about/resourse);
   expect consultation with an EHUB faculty member + fees.
3. **Museo di Storia Naturale, Univ. Pisa** (https://www.msn.unipi.it/it/) — mesh of
   specimen C 1549 + written license; if granted permissively, this becomes the only
   license-clear whole macaque skeleton.
4. **Museums behind NC licenses** (MCZ for Copes; AMNH/NMNH/RMCA/CMNH/SBU for Primate
   Phenotypes media) — only if any NC mesh is ever to ship commercially: separate written
   authorization per the record's licensing rule.

## 4. EXPLICIT UNKNOWNS (not guessed)

1. Species breakdown and per-individual coverage (tail? full axial column?) of the 9 Macaca
   individuals in 00000C706 — MorphoSource blocks scripted search; must be enumerated
   manually at intake.
2. Whether every Primate Phenotypes media record is individually CC BY-NC as the paper
   states (per-record license quote to capture).
3. SI mandible page's own CC0 sentence (presumed identical to cranium; API embeds the
   conflicting "(c) Smithsonian" default string — snapshot at download).
4. Full macaque postcranial inventory of PRICT beyond page 1 (pagination not traversed).
5. Whether Ogihara will release anything, and under what license.
6. BigMaQ dataset-file license (arXiv silent; project page to check).
7. Vilensky 1979 exact table values (paywalled; to be digitized).
8. Pisa C 1549 metric scale verification (scanner is metric-class; page states no scale).
9. AMBIGUITY FLAGGED, NOT RESOLVED: whether "CC BY-NC" counts as license-clear for
   internal reference/calibration inside a commercial project (derive-own-geometry vs
   distribute-NC-mesh). That is a legal judgment outside this research task; the proposal
   above conservatively treats NC as reference-only.
