# DATABASE HUNT — MOTION / SHAPE / OBSERVATIONS

Worker: dbhunt_motion · 2026-09-17 · read-only hunt, no graph writes, no code changes.
Method: every candidate probed live today (HTTP via curl/WebFetch/API), licenses quoted from the
hosting page or machine-readable API, download mechanisms exercised where possible. Artifacts
downloaded during verification sit in this directory (`guimaraes_suppl/`, `oku_suppl/`,
`wildprimate_kin.csv`, saved page HTMLs).

---

## FALSIFIER VERDICT FIRST

**Prediction tested:** "At least three verifiable, downloadable, license-clear datasets exist
that close named motion/shape/observation gaps."

**VERDICT: SUPPORTED.**

Named gaps closed with margin:
1. **MOTION / muscle architecture (Gap 1)** — Guimarães et al. 2026 (CC BY 4.0): per-muscle
   PCSA, fascicle length, pennation, tendon lengths for 48 hindlimb muscles × 9 primate
   species **including Macaca mulatta**. Downloaded and content-inspected today.
2. **OBSERVATIONS / macaque gait kinematics (Gap 3)** — Higurashi & Kumakura, Dryad
   `10.5061/dryad.fj6q573tc` (CC0): 3D kinematic gait parameters of Japanese macaques,
   terrestrial + arboreal (pole). License verified via Dryad API.
3. **OBSERVATIONS / primate joint kinematics + functional ranges (Gaps 3+4)** — Janisch et al.
   2024 figshare `10.6084/m9.figshare.23231366` (CC BY 4.0): 387 strides × 14 wild primate
   species, per-joint angles at touchdown/mid-stance/liftoff + excursions. Downloaded and
   content-inspected today.
Plus two more license-clear (CC0): Granatosky tetrapod gait database (Dryad, 2.1 GB) and
Gordon/Daley guinea fowl in vivo EMG+muscle force (Zenodo).

**Weakest family: SHAPE.** No new license-clear anatomical-geometry dataset was found beyond
the already-connected MorphoSource/BodyParts3D/SimTK geometry. Joint MORPHOLOGY (axes/centers)
for macaque limbs remains an open problem — closest new material is functional (ROM ranges),
not morphological.

---

## VERIFIED CANDIDATES — DOSSIERS

### C1. Guimarães, Vereecke & Wiseman 2026 — primate hindlimb muscle architecture (incl. rhesus macaque)

- **Gap:** 1 (muscle architecture: PCSA, fascicle length, pennation, tendon lengths/masses)
- **URL:** article https://pmc.ncbi.nlm.nih.gov/articles/PMC13425262/ ; data file
  `AJPA-190-e70329-s001.xlsx` (314 KB)
- **License (quoted):** "This is an open access article under the terms of the
  http://creativecommons.org/licenses/by/4.0/ License" (CC BY 4.0, © 2026 The Author(s),
  Wiley Periodicals LLC). Data availability: "Measured dissection parameters are provided in
  the Supporting Information."
- **Auth:** none.
- **Format/size:** xlsx, 314 KB (S1 dataset), + S2 docx homology notes + S3 tif.
- **Download mechanism (probed):** PMC bin links exist but NCBI serves a bot-check page to
  curl (HTTP 200, text/html 1817 bytes = interstitial). **Scriptable path verified:**
  `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13425262/supplementaryFiles` →
  HTTP 200, `application/zip`, `Content-Disposition: PMC13425262_SupplementaryFiles.zip`.
- **Content verified (downloaded + unzipped + sharedStrings inspected):** specimen table
  (FR2101100017-K Sigean; Blijdorp; Planckendael; KU Leuven #127 = *Macaca mulatta*; etc.),
  species = Pan troglodytes, Gorilla gorilla, Pongo abelii, Hylobates lar, Symphalangus
  syndactylus, **Macaca mulatta** + human (from Charles 2019 DTI); per-muscle columns:
  `FL_m` (fascicle length), `PCSA_m2`, `musc_LENGTH_m`, `musc_MASS_kg`, `belly_LENGTH_m`,
  `belly_MASS_kg`, `tendon_LENGTH_m`, `tendon_MASS_kg`, `avg_penn_deg`, limb side. 48 muscles
  per hind limb; pennation from 217 observations × 19 homologous muscles.
- **sha256 (S1 xlsx as retrieved):** `08ead4a901a53f97e136c709a7804b9d04b4b903107e873c01f3b9b5b9eb8678`
- **Classification: DOWNLOADABLE_NOW** — closes Gap 1 outright, far beyond the arm model's 39.

### C2. Higurashi & Kumakura — Japanese macaque gait kinematics, terrestrial + arboreal (Dryad)

- **Gap:** 3 (macaque gait kinematics; ground AND pole = matches our arboreal interest)
- **URL:** https://datadryad.org/dataset/doi:10.5061/dryad.fj6q573tc
  (related paper: https://doi.org/10.1007/s10329-021-00937-3 , *Primates*)
- **License (verified via Dryad API v2 dataset record):** `https://spdx.org/licenses/CC0-1.0.html`
- **Auth:** none for website download; Dryad API bulk endpoint requires a (free) bearer token.
- **Format/size:** 33,614 bytes total; files `gait.xlsx` + full-dataset zip
  (`doi_10_5061_dryad_fj6q573tc__v20210730.zip`), served at
  `https://datadryad.org/downloads/file_stream/855229` and `/855230` (extracted from page HTML).
- **Content (from deposit abstract):** 3D videography of 2 Japanese macaques walking on
  terrestrial substrate vs horizontal pole; temporal-spatial gait variables, compliant-walking
  parameters, shoulder/hip height, max hand/hip/foot clearance per stride.
- **Probed evidence:** Dryad API returned title/author/license/pubdate (2021-07-30).
  File-stream URLs return **HTTP 403 to curl** (bot wall) — browser download works (page
  renders links; Dryad site permits authless downloads). For the intake pipeline: use a
  browser, or register a free Dryad API token for scripted bulk download.
- **Classification: DOWNLOADABLE_NOW (authless via browser; scripted access needs a free
  API token or cookie hop).** Closes the macaque half of Gap 3.

### C3. Janisch et al. 2024 — wild primate limb joint kinematics (figshare, CC BY)

- **Gaps:** 3 (joint angles over stride) and 4-partial (per-joint reference ranges)
- **URL:** https://figshare.com/articles/dataset/.../23231366 — API:
  `https://api.figshare.com/v2/articles/23231366`
- **License (quoted from figshare API):** "CC BY 4.0" (`https://creativecommons.org/licenses/by/4.0/`)
- **Auth:** none. **Format/size:** 287 KB — `new_mergedkinematicdata.csv` (229 KB),
  `BRMSanalysis.R`, `ExcursionSpeciesSummaries.R`, `RDA_VarPart_Analysis.R`,
  `consensusTree_10kTrees_Primates_Version3.nex`.
- **Download mechanism (probed):** direct `ndownloader.figshare.com/files/40942022` → HTTP 200,
  scriptable.
- **Content verified (downloaded, parsed):** 387 strides, 14 species — Alouatta_palliata (37),
  Cebus_capucinus (41), Cercopithecus_lhoesti (15), Chlorocebus_aethiops (43),
  Eulemur_rubriventer (18), Eulemur_rufifrons (14), Hapalemur_aureus (13),
  Lagothrix_lagotricha (12), Lemur_catta (33), Lophocebus_albigena (58), Papio_anubis (29),
  Piliocolobus_badius (42), Plecturocebus_discolor (20), Saimiri_sciureus (11).
  Columns: hip/knee/ankle/hindlimb + shoulder/elbow/wrist/forelimb angles at TD/MID/LO,
  mean joint angles, joint excursions and yields, substrate diameter/orientation/height/
  compliance, body mass, sex/age. (Note: the "companion" Zenodo/Plazi record 14277654 is
  metadata-only with restricted files — use the figshare deposit, not the Zenodo mirror.)
- **Classification: DOWNLOADABLE_NOW.** Includes true quadruped cercopithecoids
  (Papio, Chlorocebus, Cercopithecus, Lophocebus) — best license-clear joint-angle observation
  set found for primates outside macaque.

### C4. Wimberly, Slater & Granatosky 2021 — tetrapod quadrupedal gait database (Dryad, CC0)

- **Gap:** 3 (gait parameter space across quadrupeds incl. primates) + raw gait video corpus
- **URL:** https://datadryad.org/dataset/doi:10.5061/dryad.z08kprrd5
  (paper: Proc R Soc B 10.1098/rspb.2021.0937; R code: Zenodo 5167673, MIT — verified via API)
- **License (verified via Dryad API v2):** `https://spdx.org/licenses/CC0-1.0.html`
- **Auth:** none via website; scripted bulk needs free API token (same 403 bot wall as C2).
- **Format/size:** 2,102,715,562 bytes (~2.1 GB, almost all `Gait_Videos.zip` 2.10 GB) +
  11 small analytic files: `mammal_gait.txt`, `tetrapod_gait.txt`, `non_mammal_gait.txt`,
  `event_data.txt`, `asinPhase.txt`, `Phasecontrol.txt`, `mcmc_out.txt`, `ReadMe.txt`,
  3 tree files. File→stream-ID mapping extracted (e.g. mammal_gait.txt = stream 863884).
- **Content:** duty factor / limb-phase / speed style gait metrics compiled from literature +
  internet-video scoring across tetrapods (mammals and non-mammals); primates included per
  paper (row-level primate coverage NOT independently verified — download blocked by 403).
- **Classification: DOWNLOADABLE_NOW (browser).** Heavy intake only for videos; analytic
  files are KB-scale.

### C5. Gordon, Gordon, Daley et al. — guinea fowl in vivo EMG + muscle force + kinematics (Zenodo, CC0)

- **Gap:** 5 (EMG activation timing) — avian biped, NOT a quadruped mammal; nearest
  license-clear, openly-scriptable EMG+force locomotion dataset found
- **URL:** https://zenodo.org/records/3962201 (API-verified)
- **License (quoted from API):** `cc-zero`
- **Auth:** none. **Format/size:** ~2.3 GB — `3_Intact.zip` (1.36 GB), `4_Reinnervated.zip`
  (0.93 GB) raw video; `5_matFiles.zip`; `6_Gordon_etal_Daley_LG_MuscleData.csv` (662 KB);
  `1_morphologySummaryData.csv`; `2_metaDataTable.csv`; `0_Gordon_etal_DataReadMe.pdf`.
- **Content (from API description):** lateral gastrocnemius of *Numida meleagris* — in vivo
  muscle force, EMG activation phase, sonomicrometry fascicle length, ankle kinematics during
  steady and perturbed locomotion.
- **Download mechanism:** direct Zenodo file endpoints (`/records/3962201/files/...?download=1`),
  scriptable, checksums hosted.
- **Classification: DOWNLOADABLE_NOW.**

### C6. SimTK — 3-D Musculoskeletal Model of the Chimpanzee Pelvis and Hind Limb (+ 2015 chimp walking kinematics)

- **Gaps:** MOTION (ape muscle+joint model — closest legal analog for building the macaque
  body plan); tiny OBSERVATIONS bonus (chimp bipedal walking group-mean joint angles)
- **URL:** https://simtk.org/projects/chimphindlimb ; downloads at
  https://simtk.org/frs/?group_id=900
- **Contents (via page reads):** (a) chimp pelvis/hindlimb OpenSim model `.osim` + geometry
  (~1 MB, O'Neill et al. 2013 *J Exp Biol*; muscle paths from dissections, architecture from
  literature); (b) "JHE 2015 Kinematics" 37 KB file — group-mean 3D pelvis+hindlimb joint
  kinematics for chimpanzee bipedal walking vs human (O'Neill et al. 2015 *J Hum Evol*).
- **License (quoted):** a "View License" link exists on the downloads page; license TEXT could
  not be retrieved without login (SimTK serves HTTP 403 to bots).
- **Auth:** free SimTK account required to download files (standard SimTK FRS behavior).
- **Classification: FREE_ACCOUNT / license text UNVERIFIABLE today.** One human login away.

### C7 (bench). Oku, Ide & Ogihara 2021 — macaque bipedal simulation time series (supplementary)

- **Gap:** 3-adjacent (macaque joint angles/torques + muscle activations + GRF, from forward
  dynamics of the 2009 macaque model) — usable as a reference trajectory set
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7940622/ ; supplementary via
  `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7940622/supplementaryFiles`
  (verified 200, downloaded today)
- **Content verified (sharedStrings):** columns IL, GMED, VAS, TA, SOL, RF, BIFl, GAS, EDL,
  FDL (activations), `GRF h`, `GRF v`, `knee angle`, `ankle angle`, `MP angle`, `hip angle`,
  hip/knee/ankle/MP torques.
- **Model files themselves:** paper states data/code "available from the corresponding author
  on reasonable request" — **confirms the known ON_REQUEST status of the Ogihara macaque model**;
  no GitHub/SimTK/Zenodo deposit exists.
- **License:** article is in PMC OA subset (Communications Biology, CC BY 4.0 by journal
  policy — confirm exact license line at intake).
- **Classification: DOWNLOADABLE_NOW (supplementary only); model = ON_REQUEST.**

---

## VERIFIED BUT LICENSE-RESTRICTED (NC / unclear)

| Candidate | Where | License (quoted) | Size | Verdict |
|---|---|---|---|---|
| SuperAnimal-Quadruped-80K (pose keypoints+masks; dogs/cats/horses/rodents/cheetahs) | zenodo.org/records/14016777 | "Modified MIT … academic, non-commercial purposes only … may not be used to harm any animal deliberately" | 45.9 GB tar.gz, direct, md5 | DOWNLOADABLE_NOW (NC) |
| macaque3Dpose training dataset (multi-monkey 3D pose: nose/ears/shoulders/elbows/wrists/hips/knees/ankles; Matsumoto et al. 2025 Sci Adv) | zenodo.org/records/15195510 + github.com/PrimatoModelling/macaque3Dpose (code MIT) | "Creative Commons Attribution Non Commercial 4.0 International" | dataset.zip 2.1 GB, direct | DOWNLOADABLE_NOW (NC) |
| AcinoSet (cheetah, 119,490 high-speed multiview frames, 7,588 annotated, 3D triangulated) | github.com/African-Robotics-Unit/AcinoSet → Dropbox | NO license stated anywhere (only "kindly cite") | GB-scale, Dropbox folders | DOWNLOADABLE_NOW but license UNVERIFIABLE — risk |
| Schoonaert et al. 2007 — chimpanzee segment inertial properties (53 chimps × 8 segments: mass, COM%, Ix, Iy, radii of gyration, whole-limb inertia) | pmc.ncbi.nlm.nih.gov/articles/PMC2375742 (J Anat) | free-to-read, NOT CC: "© 2007 The Authors Journal compilation © 2007 Anatomical Society of Great Britain and Ireland" | tables in-paper (Tables 1-3) | PAPER_TABLES — closes Gap 2 functionally (beyond Vilensky), no redistribution license |
| Nishizaki et al. 2026 (eLife reviewed preprint 109826) — macaque gait transition: 200 fps kinematics (20 landmarks) + implanted EMG (13 muscles) | elifesciences.org/reviewed-preprints/109826 | CC BY 4.0 article; data: "The data will be made available upon acceptance of the manuscript." | TBD | PENDING / ON_REQUEST — recheck; would close Gaps 3+5 if released |

---

## LEADS CHECKED AND CLOSED / DEAD

- **"CanidGait"** — a zebris commercial treadmill product, NOT a dataset. Kills the banked rumor.
- **"HorseSym"** — 0 hits on Zenodo API; not verifiable under this name.
- **KUPRI Digital Morphology Museum** (pri.kyoto-u.ac.jp/dmm/, /digital-morphology/) — 404 /
  dead host → DEAD_LINK (SHAPE loss).
- **Digimorph macaque specimen pages** — 404 → DEAD_LINK.
- **Dryad sweeps** "rat locomotion electromyography", "dog ground reaction force", "canine
  gait", "quadruped GRF" — no relevant hits. Open quadruped-mammal force-plate datasets were
  NOT found; best adjacent: Zenodo 4975751 "The crouching of the shrew: mechanical
  consequences of limb posture in small mammals" (cc-zero, API-verified title+license; contents
  unverified — lead).
- **DANDI** — locomotion search returns ephys-oriented dandisets; no clear gait-EMG fit.
- **amathislab/musclemimic_models** — human-only models (Apache 2.0), no macaque.
- **Oku/Ogihara macaque model on GitHub/SimTK** — does not exist; only on-request.

---

## RANKED TOP-5 INTAKE PROPOSAL

Rank = closes a named gap × license-clear × authless/scriptable.

1. **Guimarães 2026 S1 xlsx** — Gap 1 (muscle architecture; MACACA MULATTA rows) — CC BY 4.0 —
   scriptable, verified, sha256 recorded. Parse xlsx → per specimen×muscle records; the single
   highest-value intake of this hunt.
2. **Higurashi Dryad `fj6q573tc` (macaque gait kinematics, ground+pole)** — Gap 3 — CC0 —
   authless browser download; scripted path needs a free Dryad token or cookie hop (403 bot
   wall). Smallest dataset on the list (33 KB) and the only one with OUR species.
3. **Janisch figshare `23231366` (wild primate joint kinematics)** — Gaps 3+4 (ROM reference
   ranges, quadruped cercopithecoids) — CC BY 4.0 — direct ndownloader, fully scriptable,
   verified.
4. **Granatosky Dryad `z08kprrd5` (tetrapod gait database)** — Gap 3 — CC0 — take the KB-scale
   analytic tables first (`mammal_gait.txt` etc.); the 2.1 GB `Gait_Videos.zip` is a separate
   decision. Browser-authless; scripted via API token.
5. **Gordon/Daley Zenodo `3962201` (guinea fowl EMG + in vivo muscle force)** — Gap 5 — CC0 —
   direct Zenodo file URLs, fully scriptable. Avian biped, not quadruped mammal — flag that in
   the record.

Bench (do not batch-intake yet): SimTK chimp model + 2015 kinematics (needs one human SimTK
login + license text read); Oku 2021 supp xlsx (macaque simulation reference, scriptable —
cheap second intake); macaque3Dpose + SuperAnimal-80K (NC licenses — legal review before
intake); Schoonaert 2007 tables (manual transcription, facts only).

---

## EXPLICIT UNKNOWNS

1. **Joint morphology (axes/centers/limits) for macaque limb joints: NOT FOUND license-clear.**
   Closest: functional ROM ranges (C3), SimTK chimp model joint definitions (login), known
   MorphoSource CT route. The open problem stands.
2. **Quadruped mammal EMG:** nothing license-clear and open found today. Best future shot is
   Nishizaki 2026 eLife (13 macaque muscles) promised "upon acceptance" — needs a recheck.
3. **SimTK license text** for chimp model/kinematics files unverified (login wall) — a human
   with a free account must read "View License" before intake.
4. **Dryad scripted downloads** are bot-walled (403); sha256 pinning requires browser download
   or a free API token. Not an intake blocker, but the pipeline must not assume plain curl.
5. **Primate rows in Granatosky `mammal_gait.txt`** not row-verified (download blocked); paper
   covers mammals broadly and primates are in scope, but verify after download.
6. **Oku 2021 article license line** not captured verbatim (journal is CC BY 4.0 by default);
   confirm the string on the PMC page at intake time.
7. **Segment inertia (Gap 2)** has no open deposit — only PAPER_TABLES sources beyond Vilensky
   (Schoonaert 2007 chimps; Druelle 2018 bonobos in J Anat, same paper-tables class). If the
   engine needs machine-readable primate inertia, transcription or CT-derived computation is
   the path.
