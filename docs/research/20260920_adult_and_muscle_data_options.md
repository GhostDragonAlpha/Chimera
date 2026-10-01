# ADULT MACAQUE DATA + MUSCLE GEOMETRY — RESEARCH MEMO (2026-09-20)

Lane: `agent/muscle-data-research-20260920` (research-only; no engine/scene code).
Branch base: `origin/master` @ `32105f18`. Agent: GLM 5.3.

The operator's question, verbatim intent: the infant macaque bones are good, but
**"we NEED ADULT macaque data. If we can't find adult macaque data, maybe there is
some other species of monkey. Or, if we are limited by our data, then we need to
reconsider the architectural methodology of development."** Plus the standing gap:
muscle GEOMETRY (shape/volume/attachment extents) for a macaque that looks muscled,
not skeletal. Plus the new law: biological mixing rules with checkpoints
("does this biologically check out?" becomes a command, not a judgment call), and
the reality/fantasy classification ("we get reality FIRST, because then everything
else becomes fantasy BY DEFAULT").

---

## RULE 0 — PRE-REGISTRATION (stated before the ranking)

**STATEMENT (a theory, disagreeable):** Accessible adult macaque whole-body imaging
exists publicly, but NONE of it carries a commercial-OK license — the adult whole-body
data that exists is either non-commercial, permission-gated, or request-by-email —
while license-OK adult data exists only as regional (hindlimb muscle architecture,
CC BY 4.0) and skull (CC BY-NC) sets. The bottle neck is LICENSE + STAGE together,
not existence.

**PREDICTION (was unmeasured before this memo):** an exhaustive API sweep of
MorphoSource (the only public repository we know to carry primate whole-body CT)
returns **zero** full-body Macaca media records with `permits_commercial_use =
CommercialUsePermitted`, and every full-body Macaca record that is open carries
copyright "Undetermined" + `CommercialUseNotPermitted`.

**FALSIFIER (named before the run):** (i) the sweep below is reproducible from the
MorphoSource API and returns a materially different license distribution, or (ii) a
commercial-OK adult whole-body macaque dataset exists that the sweep and the lead
verification missed — either one falsifies the ranking in §7 and the recommendation.

### Pre-registered evaluation criteria (applied in §7, in this order)

- **C1 STAGE VERIFICATION (admission-required, like sha256).** Adult must mean
  ADULT-CONFIRMED from collection/publication records (age in years, dentition, or
  known-age colony record) — never "unlabeled, presumed." A dataset without stage
  metadata ranks DOWN and is inadmissible for the adult creature until labeled.
- **C2 COVERAGE.** Whole-body > substantial postcranial > regional (limb) > skull-only.
- **C3 LICENSE.** Commercial-OK (CC BY 4.0 standard) > open-with-conditions
  (copyright Undetermined / MorphoSource standard / CC BY-NC) > permission-gated.
  HONEST TENSION, recorded: our current infant bones are ALREADY
  `CommercialUseNotPermitted` + copyright Undetermined (`tools/science_funnel/data/
  morphosource_ct/download_receipt.json`, pinned usage PDF `ms_usage_std_comm_no_
  rearc_ms_3d_yes.pdf`). The repo has accepted non-commercial MorphoSource standard
  terms once. Whether that bar stays closed for the adult set is THE OPERATOR'S CALL —
  this memo reports where it fails and never waives it silently.
- **C4 ACQUISITION.** API/bulk > manual download (MorphoSource is permanently
  manual-only for us, by law of experience) > email request / certification.
- **C5 FORMAT.** **Mesh-with-triangles ranks UP** (operator doctrine: "If we find
  data that's in mesh form and it has triangles, that's most likely all we need" —
  intake is a translation of triangles into the project format). Volumes are fine
  (the pipeline owns volume→marching-cubes); a segmented label-volume is best of both.
- **C6 DUAL ANSWER BONUS.** A source answering BOTH the adult-body question AND the
  muscle-geometry question gets credit for both (an adult MRI/CT with muscle contrast
  does exactly this).
- **C7 PIPELINE FIT.** science_funnel intake + graph admission (batch connectors,
  sha256 receipts, idempotent replay) must be able to admit it.

### Layer roadmap framing (operator doctrine)

Bones are DONE (infant specimen, 160 µm). **Muscles are the current gap.** Skin is
eventual. All three are membrane outlines defined by triangles, so a source that
ships multiple layers as meshes (segmented-mesh datasets, OpenSim-derived surface
meshes) is especially valuable; §5 calls these out where they apply. The canonical
workflow checklist is now `docs/THE_CHECKLIST.md` (branch
`agent/workflow-checklist-20260920`, commit `e9c8b394`) — this memo's intake
recommendations defer to its data-intake gates (stage labels admission-required,
license pinned, sha256 provenance, reality/fantasy classification).

---

## 1. INVENTORY — what we already hold (all in-repo, all cited)

**Branching note (measured, not assumed):** `origin/master` @ `32105f18` does NOT
contain the muscle-intake batches; they live on the lane branches (the repo default
`origin/HEAD` = `origin/agent/skeleton-movie-20260919` carries them; intake commit
`46ed85a3` on 2026-09-17; MorphoSource CT commit `6946f3b9` on 2026-09-19). Paths
below were verified on `origin/agent/skeleton-movie-20260919`.

### 1.1 Muscle NUMBERS (the PHYSICS side)

- **Guimaraes 2026 hindlimb architecture** — `tools/science_funnel/data/guimaraes_arch/`
  (`AJPA-190-e70329-s001.xlsx` + S2 homology docx + PMC13425262 fulltext XML +
  `download_receipt.json`); connector `tools/science_funnel/connectors_muscle.py`,
  adapter `tools/science_funnel/adapters_muscle.py`; validation receipt
  `tools/science_funnel/validation/batch_muscle_20260917/receipt.json` (**1908
  records admitted / 49 quarantined**, count identity closed; store after merge:
  9916 objects / 14527 relations; graph hash `4aa3e223…`). License **CC BY 4.0**
  (receipt-pinned; S1 member sha256 `08ead4a9…` cross-verified against the dbhunt
  dossier C1).
  **Coverage, measured directly from the xlsx (this lane, 2026-09-20):** the
  workbook's `Macaca mulatta` sheet holds **36 data rows = 36 distinct hindlimb
  muscles** (AB, AL, AM, BFL, BFS, EDL, EHL, FDL, FHL, GMax, GMed, GMin, GRA,
  GemInf, GemSup, ILI, LG, MG, ObtExt, ObtInt, PB, PECT, PIRI, PL, PLANT, POP, RF,
  SAR, SM, SOL, ST, TA, TP, VI, VL, VM) — single specimen, right limb. (The assembly
  doc's "30" is the count that lane used; the SOURCE sheet holds 36.)
  **Specimen/stage (read from the `Information` sheet):** specimen **"127 [KU Leuven,
  Belgium]" — Macaca mulatta, MALE, "Age at death (yrs)" = "Adult", 8 kg, right
  limb dissected.** Stage is labeled at source, but only as the word "Adult", not a
  numeric age — adult-CONFIRMED per the source record, with that caveat carried.
  **Fields:** FL (m), PCSA (m²), muscle length, muscle mass, belly length/mass,
  tendon length/mass, pennation angle (°), limb. **HINDLIMB ONLY — NO FORELIMB.**
  6 primate species total (Pan, Gorilla, Pongo, Hylobates, Symphalangus, Macaca).
- **Oku 2021** — `tools/science_funnel/data/oku_bipedal/`; 40 series records
  (batch `oku_bipedal`); segmental masses/lengths/COM/inertia (Table 1: HAT 7.372 kg,
  thigh/shank/foot/phalanges) + bipedal angle/GRF/torque/muscle-force series —
  **forward-dynamics SIMULATION of a planar nine-link model**, M. fuscata ~10 kg male.
  CC BY 4.0.
- **Arm model Fmax** — `tools/science_funnel/data/macaque_arm/monkeyArm_current.osim`
  (limblab/monkeyArmModel @ `4fb7ddee`, **MIT**), admitted as `model.anatomy.macaque_arm`:
  11 bodies, 7 coordinates, **39 musculotendon records with max_isometric_force
  (Fmax 39/39)**, 30 wrap surfaces, 1 conditional via point, 7 bone geometry VTPs
  (clavicle, scapula, humerus, radius, ulna, hand, sternum). M. mulatta.
  **No PCSA, no volumes** — `macaque_anatomy.py` records muscles
  `force_runtime_ready: false` and scope-excludes "muscle volume, skin/fat geometry".
- **Human references (prior art of the intake pattern)** — `docs/MUSCLE_ATLAS.md`
  (Rajagopal2016 80 MTUs + gait2392 92 + Arm26 6, all Apache-2.0, sha-pinned,
  line-provenant extraction by `tools/extract_muscle_atlas.py`);
  `tools/reference_data/data/reference_store.json` (OpenSim leg6dof9musc import);
  `docs/research/muscle_physiology_reference.md` (Hill model, specific tension
  25–32 N/cm²).

### 1.2 Muscle PATHS / moment arms

- **Muscle-path lane 2026-09-18** — deliverable
  `tools/science_funnel/validation/muscle_paths_20260918/muscle_path_geometry.json`
  (schema `chimera.muscle_path_geometry.v1`), derivation
  `docs/research/20260918_muscle_path_derivation.md` (lane branch). Arm membrane
  HELD (worst |r_geo − r_fd| = 4.3e-10 m over 39×7×2 poses); hindlimb straight-line
  paths from Oku segment lengths + Guimaraes groups: hip/knee-flexion/ankle ratios
  held, **knee extension and MTP flexion FALSIFIED (ratio 0.00)** — no patella / no
  plantar pulleys in a straight-line proxy; those two directions are barred from
  force claims until via-pulley paths are derived.
- **Whole-body assembly tables** — `docs/research/20260918_monkey_assembly_derivation.md`
  (lane branch): the input map (arm chain + Oku HAT/hindlimb + USNM 15259 head
  geometry + terrain), the 69/31 fore/hind load prediction, and the species
  discipline note (arm+architecture = M. mulatta; inertial table = M. fuscata; head
  = M. sinica — every cross-species substitution DECLARED, never merged).

### 1.3 Bone geometry

- **Infant full-body CT (the good data)** — `tools/science_funnel/data/
  morphosource_ct/download_receipt.json`: MorphoSource media **000875599**
  (USNM 497135) and **000875604** (USNM 497136-3), full-body M. mulatta at 160 µm,
  X-Ray CT, ~400 MB TIFF each (pinned by receipt; bytes gitignored). License:
  copyright **Undetermined**, MorphoSource Standard, **CommercialUseNotPermitted**,
  3D printing permitted. Creator Mormile/Smithsonian NMNH, NSF 2341137.
  Commit message carries the stage label: "infant specimens — adult scaling from
  Guimaraes/Oku does not apply directly; bone geometry reference only."
- **Head** — Smithsonian USNM 15259 cranium+mandible decoded geometry (bundle
  `smithsonian.usnm15259`; CC0 with a conflicting Smithsonian copyright string,
  carried per intake record). M. sinica.
- **Arm bones** — the 7 VTPs in the arm model (above).

### 1.4 What is MISSING for a whole-body musculature

1. **Adult whole-body geometry** of any kind (bones AND soft tissue) — we hold no
   adult imaging at all; the skeleton we render is a curled infant.
2. **Muscle geometry** — shape/volume/attachment extents. We hold numbers (PCSA,
   masses) and straight-line path estimates, not 3D muscle surfaces. Forelimb
   muscles have paths + Fmax but no PCSA; hindlimb muscles have PCSA but only
   derived straight-line paths with two falsified directions.
3. **Axial/neck/trunk/face musculature** — nothing. The 36+39 records cover hindlimb
   + forelimb only; the trunk rides inside "HAT".
4. **Skin/fat surface** — nothing (explicitly out of scope of every current record).
5. **Adult inertials in the same species** — the inertial table is M. fuscata, the
   muscles M. mulatta (declared substitution, still a gap to close someday).

---

## 2. TIER 1 — accessible ADULT macaque whole-body (or substantial postcranial) data

### 2.1 The leads, verified

**(a) Copes et al. 2016, Scientific Data 3:160001** (DOI 10.1038/sdata.2016.1,
PMCID PMC4736502, CC BY 4.0 article) — 489 microCT scans / 431 specimens / 59 primate
species from the Harvard MCZ, on MorphoSource. **VERIFIED: includes macaques — but
only 6 scans, all SKULLS: M. fascicularis ×4 (MCZ-12758, 22277, 23812, 23813),
M. mulatta ×2 (MCZ-26475, 30384).** A femur+humerus were scanned for some
individuals — none of the macaques. No whole-body. Data tagged "MCZ – CC BY-NC"
(**non-commercial** — fails the operator's commercial-OK bar). Age: collection-level
policy only ("adult and juvenile", adulthood by full M3/canine eruption); the table
carries no per-specimen stage field. VERDICT: skull resource; fails C1 (per-specimen
stage), C2, C3.

**(b) Museum of Primatology (MOP), CARTA/UCSD** — VERIFIED via
`https://carta.anthropogeny.org/museum/collections`: skeletal collections of
chimpanzees (Primate Foundation of Arizona) and **macaques (M. mulatta)**; the
earlier lead's number is real — **444 CT volumes, 1–15 bones per scan, >5000 bones**
(disarticulated ELEMENTS, not whole bodies), plus digital radiographs (1,618).
Access: "extensive cataloging and 3D digitizing … currently underway", DICOM
download links on detail pages; **no stated license**; no age-class metadata
verified. VERDICT: bones-only, in-progress, license-unstated — fails C1, C3, C5;
a possible future skull/postcranial-element source, not a body source.

**(c) Li, Zhang 2017, QIMS 7(2):267-275** — "Whole body MRI of the non-human primate
using a clinical 3T scanner: initial experiences" (DOI 10.21037/qims.2017.04.03,
PMCID PMC5418147). VERIFIED: **4 ADULT female rhesus (7–11 y, 8.5–10.5 kg)**,
whole-body T1/T2 + head/neck MRA at 4 mm slice thickness, head-to-toe ~100 cm on a
clinical 3T. **No data availability statement; article "All rights reserved";
no public download anywhere.** VERDICT: PROOF that adult whole-body macaque MRI is
feasible and exists — but the DATA is not accessible. Fails C4 fatally (request
dead-end unless the operator emails Emory). Cited as feasibility evidence, not a
candidate.

**(d) UNC-Wisconsin Rhesus Macaque Neurodevelopment Database** — VERIFIED on Zenodo
(DOIs 10.5281/zenodo.233682, 233662, 233670 and siblings): **open access, CC BY 4.0**,
NIfTI T1/T2 structural volumes, 34 typically developing monkeys, longitudinal
**2 weeks → ~3 years**. Neuro-focused: head/brain FOV, not whole-body; **all
specimens immature** (that is the point of the database). VERDICT: license-OK and
API-able, but wrong stage (infant/juvenile) and wrong coverage (head). It is a
candidate for the BABY creature's head soft-tissue, never for the adult.

**(e) DigiMorph** — skull-CT archive (UT Austin); no Macaca specimen page confirmed
(specimen list not machine-readable from this environment; fetch blocked). VERDICT:
unconfirmed, skull-focused, low priority. KUPRI Digital Morphology Museum (Kyoto):
historic CT database incl. Japanese macaques — **unreachable from this environment
(timeouts); status uncertain after the PRI restructuring; license historically
academic-only.** Not ranked.

### 2.2 The MorphoSource sweep (measured, this lane, via the public API — search only)

Swept ALL Macaca media (query `Macaca`, 17 pages, **1,671 media records**, saved to
`E:/ChimeraWork/muscle_research_ms_macaca.json` during research):

- **Taxonomy:** 866 M. mulatta · 431 M. fascicularis (incl. subspp.) · 63 M.
  nemestrina · 58 M. arctoides · 39 M. sylvanus · 33 Macaca sp. · 21 M. fuscata ·
  remainder other Macaca + a few mislabeled Cercocebus.
- **License:** **1,623 CommercialUseNotPermitted vs 48 CommercialUsePermitted —
  and ALL 48 commercial-OK records are skulls (NMNH crania/mandibles).** Zero
  commercial-OK postcrania or bodies.
- **Full-body CT: exactly 18 records for the whole genus.**
  - 14 × **UC Davis Department of Anthropology** ("Full body scan", microCT,
    M. mulatta): media **000069177** (ucd:37163 F), **000069518** (ucd:37177 F),
    **000073328** (ucd:37477 F), **000073364** (ucd:38328 F), **000073365**
    (ucd:38341 F), **000073366** (ucd:38465 F), **000073367** (ucd:39242 F),
    **000073368** (ucd:39026 F), **000073369** (ucd:39374 F), **000073370**
    (ucd:39481 F), **000077648** (ucd:39512 M), **000078098** (ucd:39612 F),
    **000078187** (ucd:39650 M), **000078191** (ucd:39882 F) — 12 F / 2 M.
    Visibility: **`restricted_download`** (account + permission request).
    `CommercialUseNotPermitted`, 3D printing limited. Sex recorded; **age class NOT
    recorded in the API** (the UC Davis primate collection is advertised as
    known-aged/known-sex — stage confirmation must come from the collection at
    request time).
  - 4 × **Smithsonian NMNH** (Mormile, MILabs U-CT, "Full body"): **000875599**
    (USNM 497135, M. mulatta, infant — ALREADY IN REPO), **000875604** (USNM
    497136-3, M. mulatta, infant — ALREADY IN REPO), **000875609** (USNM 267307,
    M. fascicularis, sex unknown, **open** download), **000875614** (USNM 268003,
    M. fascicularis, sex unknown, **open** download). All: copyright Undetermined,
    CommercialUseNotPermitted, 3D printing permitted. **Stage: NOT CONFIRMED for
    the two fascicularis** (NMNH catalog unreachable from this environment);
    they must be visually stage-checked (skull sutures/epiphyses in-scan) before
    any admission — under the new law, unlabeled = unadmittable.

**The prediction holds: zero full-body Macaca records are commercial-OK.** Every
whole-body adult candidate is non-commercial, restricted, or both.

### 2.3 Adjacent confirmed sources (adult full-body CT of rhesus, outside the sweep)

- **Buck & Katz 2021** ("Effects of hybridization on pelvic morphology: A macaque
  model", **138 full-body medical CT scans of ADULT CNPRC rhesus, 94 F / 44 M**,
  per the NSF PAR record; scan data said to be "available via MorphoSource") +
  **Buck et al. 2025** follow-up on body size/shape from CTs of living monkeys.
  The 14 UC Davis restricted full-body records are plausibly (but NOT confirmed to
  be) a posted subset of this material. VERDICT: the strongest evidence that an
  adult full-body rhesus CT network exists at CNPRC/UC Davis — but access is
  permission-gated (C3/C4 fail; C1 confirmed only at publication level).
- **"Rise of the Visible Monkey", Chung et al. 2019, J Korean Med Sci**
  (DOI 10.3346/jkms.2019.34.e70, PMCID PMC6393759; article CC BY-NC 4.0):
  **whole-body cadaver rhesus, FEMALE, 93 months (7.75 y — ADULT), 4.3 kg, 758 mm**;
  serial sectioned images at 0.05 mm (head) / 0.5 mm (body) — 2,967 images at
  8688×5792, 0.024 mm pixel, 48-bit — **plus paired 3T MRI (T1/T2) and CT of the
  same specimen**. Data: "will be provided to any requesting researcher free of
  charge" by EMAIL to the corresponding author (park93@dongguk.ac.kr); no data
  license stated. Segmentation in the 2019 paper: head skin + brain only.
  Companion: **"Dawn of the Visible Monkey"** (Kim et al. 2020, PMCID PMC7167398):
  **839 segmented images of 167 whole-body structures** (skeletal, articular,
  muscular, organ systems, integumentary), 3D **STL** surface models (Mimics 17.01)
  + an Adobe-PDF model assembly; download "after user certification by the
  Electronics and Telecommunications Research Institute" (ETRI). **Muscles are
  segmented as ONE merged structure** — no individual muscles. Article CC BY-NC 4.0;
  dataset license unstated. VERDICT: the only adult whole-body multi-modal rhesus
  that is genuinely obtainable (email/certification); the STL set gives
  skin+skeleton+merged-muscle membranes as triangles (C5 strong, C6 strong), but
  C3 (non-commercial/unstated) and C4 (certification) are its costs.

---

## 3. TIER 2 — other monkey species (only if Tier 1 fails)

Measured, same sweep method: **Papio (baboon): 2,495 MorphoSource media — ZERO
full-body records.** Distribution is skull/element-dominant (724 element CT series,
713 element meshes, 158 cranium-with-mandible, 133 inner ears, 70 cranium surface
scans…). The commercial-OK subset is again NMNH skulls only.

Conclusion (measured, not assumed): **no other monkey genus on MorphoSource carries
better whole-body coverage than Macaca.** The best Tier-2 fallback inside Macaca is
**M. fascicularis** (431 media incl. the two OPEN full-body CTs 000875609/000875614),
then M. nemestrina/M. arctoides (skulls/elements only). Beyond MorphoSource, no
open adult whole-body CT/MRI of any cercopithecine was found in this search; the
Visible Monkey (rhesus) remains the only obtainable adult whole-body dataset of ANY
monkey. Tier 2 therefore reduces to: *same repositories, same license wall, worse
coverage* — and if Tier 1 is exhausted, the binding constraint is not species
choice but the acquisition route (§4).

---

## 4. TIER 3 — "reconsider the architectural methodology" (OPTIONS, never a decision)

The operator asked for these as OPTIONS. They come back as a recommendation, chosen
by the operator, never made in-lane.

- **Option A — parametric anatomy from measurement tables.** Build muscle membranes
  as capsules/ellipsoid envelopes driven by the numbers we hold (36 Guimaraes
  hindlimb volumes + 39 arm paths/Fmax) attached to whatever skeleton the stage
  supplies. PRO: license-clean (CC BY 4.0 / MIT), fully pipeline-admittable today,
  biological stage-true IF attached to a same-stage skeleton. CON: shape is
  envelope-true, not specimen-true; the falsified straight-line knee/MTP directions
  show the limit of proxies.
- **Option B — allometric scaling of the infant.** Stretch the infant to adult size.
  **MEASURED FAILURE MODE: the mounting lane already measured per-bone 3.8–8.8×
  stretch factors — cranium vs limb grow on different curves, so one stretch cannot
  fit all bones; the operator cites this as the proof that faking it fails.** A
  stage-aware variant (separate per-region growth laws) is biology modeling, not
  scaling — it is Option C by another name. CON: violates L2 below if done as a
  single stretch; it manufactures an animal that never lived.
- **Option C — character-agnostic aliveness path.** Keep the creature visually
  abstract; push the aliveness/motion/neuromechanics line (which is stage-true by
  construction wherever it uses same-stage numbers) and defer species fidelity
  until adult data lands. PRO: no biological law is bent. CON: the "muscled macaque
  that looks real" goal is postponed, not served.
- **Option D (the upstream fix, listed for completeness) — request adult data
  through the two gated doors that exist** (UC Davis/MorphoSource permission for
  the 14 full-body adult CTs; Dongguk/ETRI for the Visible Monkey set). This is
  the hand-download list (§8). It is an option because the gates are human, and
  the operator is the legal terminal for human doors.

---

## 5. MUSCLE GEOMETRY — candidates for the secondary question (the current gap)

1. **Wiseman, Bollmann van Beesel & Vereecke 2026, Royal Society Open Science
   13: rsos.260107** (DOI 10.1098/rsos.260107, published 2026-04-29, **CC BY 4.0**
   per Crossref license feed): "Comparative analysis of primate hind limb muscle
   moment arms using subject-specific three-dimensional musculoskeletal models" —
   **OpenSim 4.5 hindlimb MSK models across seven NHP species including a
   cercopithecoid (macaque)**, built on a human hindlimb base. Verified on Figshare
   (API-able, both **CC BY 4.0**):
   - SI 1 (muscle homology, docx) — DOI 10.6084/m9.figshare.32017187.v1, file
     `rsos260107_si_001.docx`, download id 63739721;
   - SI 2 (peak moment arms + joint excursions, xlsx) — DOI
     10.6084/m9.figshare.32017184.v1, file `rsos260107_si_002.xlsx`, download id
     63739718.
   **The .osim model files themselves were NOT located** (RSOS article page and PDF
   are bot-blocked from this environment; the data-availability statement on that
   page — and the Cambridge Apollo deposit — is the operator's manual follow-up).
   Same lab network as our Guimaraes batch (Vereecke) — homology tables should map
   1:1 onto the 36 admitted muscles. If the model files ship with bone surface
   meshes + muscle path points, this is hindlimb muscle GEOMETRY under CC BY 4.0 —
   the best license-clean muscle-geometry candidate found. Format: OpenSim paths
   + (likely) meshes — C5 good, C7 perfect.
2. **Dawn of the Visible Monkey STL set** (see §2.3): whole-body STL membranes —
   skin, skeleton, and a merged-muscle layer — of an ADULT female rhesus. Not
   per-muscle, but it is a triangle-mesh soft-tissue outer boundary + a muscle
   envelope; C6 strong (answers adult body + a coarse muscle layer at once);
   C3/C4 cost: ETRI certification, license unstated.
3. **MRI route (assessment, honest):** clinical-T1/T1-weighted MRI gives
   soft-tissue contrast sufficient for muscle segmentation (Li 2017 proves adult
   whole-body macaque MRI works at 4 mm on a 3T). But NO adult whole-body macaque
   MRI is publicly deposited (Li's data unshared; PRIME-DE/PRIME-RE are brain;
   the Japan Monkey Centre repository is postmortem BRAIN MRI). MRI segmentation
   of muscles would be our own labor on requested data — a project, not a download.
4. **CT route (assessment, honest):** published individually-segmented macaque
   muscle CT datasets: **none found.** The closest are the Visible Monkey STLs
   (muscles merged) and the Buck 2021 pelvis work (bones). Any per-muscle CT
   segmentation of an adult macaque would be novel labor on the §8 data.
5. **Cadaver/dissection atlases (assessment):** no public 3D-digitized macaque
   dissection atlas was found (the Visible Monkey cadaver set IS the digitized
   cadaver, and it is gated); eSkeletons/brain atlases (Scalable Brain Atlas,
   MacBNA, EBRAINS) are osteological or neural — no muscle geometry.
6. **X-ray (the operator's suggestion — honest assessment):** plain radiography is
   a 2D projection: it bounds silhouettes and bone positions but cannot give 3D
   muscle geometry. Biplanar X-ray reconstruction (XROMM-style, xromm.org) recovers
   3D bone motion from calibrated views with implanted markers — a lab-specific
   method producing motion data, not a public muscle-geometry dataset. Verdict:
   X-ray is a validation instrument, not an acquisition route for us. The operator's
   instinct that "actual CT scan" beats X-ray is correct.

---

## 6. BIOLOGICAL MIXING RULES — the checkpoint spec (founding document, Rule-0 pre-registration)

> Stated as laws BEFORE being applied to any ranking, per Rule 0. These are the
> rules the admission gates must enforce; "does this biologically check out" becomes
> a COMMAND in the repeatable MCP/tooling surface the operator has directed — not a
> judgment call. Think like a biologist: a baby macaque is the way it is for
> biological reasons (large head-to-body ratio, relatively long forelimbs and flexed
> clinging posture, grasp-ready hands — adaptations to clinging to its mother); life
> is different at every stage; you CANNOT mix stages. Adult arms on a baby's back
> are not a style choice — they are a biological contradiction and must be REFUSED
> by the gate, not argued down by taste.

### 6.1 The laws

- **L1 STAGE CONSISTENCY — one creature, one life stage.** All anatomy records
  bound to one creature instance must carry the SAME stage label
  (neonate/infant/juvenile/subadult/adult), sourced from collection or publication
  records (numeric age, dentition, or known-age colony). Assembling across stages
  is refused outright (the adult-arms-on-baby case). Stage label is
  admission-required metadata, the same class of requirement as sha256.
- **L2 ALLOMETRIC COHERENCE — proportions follow the stage's scaling law.** Within
  a stage, segment proportions obey known growth allometry (infant: head large
  relative to body, forelimb-dominant, flexed resting posture — adaptive, not
  noise; adult: different ratio band). An assembled creature whose segment
  proportions violate its declared stage's allometry is refused — this is exactly
  the measured failure of the single-stretch route (3.8–8.8× per-bone spread):
  the spread is the signal of a stage mix, not noise to be tuned away.
- **L3 TAXONOMIC COHERENCE — declared substitutions only, at bounded distance.**
  Cross-species assembly (only if Tier 2 ever forces it) must declare every
  substitution with its taxonomic distance and scale statement (the assembly doc
  already does this: mulatta arm + fuscata inertials + sinica head, each DECLARED,
  never merged). Within-genus species substitution requires a declared mapping;
  cross-genus substitution requires the operator.
- **L4 PHYSICS — the standing laws still hold.** Mass, inertia, lever laws, load
  capacity: the existing physics gates keep their vote; a biologically-passing
  creature that violates physics is still refused (and vice versa).

### 6.2 The gate output: CLASSIFY, don't just refuse

The operator's taxonomy completes the design: a user may build a half-adult
half-baby macaque with machine guns — but they must UNDERSTAND that this violates
the laws of nature. So the gate does not merely refuse; it CLASSIFIES:

```
gate_output = {
  "category": "reality" | "fantasy",
  "violations": [ {law: "L1_stage", detail: "...", records: [...] }, ... ],
  "stage_label": "...", "stage_evidence": "...",
}
```

- **reality**: passes L1–L4 → the default admission path.
- **fantasy**: fails any law → quarantined to the FANTASY category with an
  itemized VIOLATION MANIFEST (which laws, which records). Fantasy creatures are
  constructed only through an explicit developer-driven mode that REQUIRES
  acknowledging the manifest — the violation is never silent, never accidental
  (explicit construction, not accidental data mixing).

**Derivation order (the operator gave it):** reality must be established FIRST —
the reference creature — and fantasy is then defined as DEVIATION FROM the
reference. This is the same pattern as the repo's standing law: no reference, no
verdict. Today the baby IS a valid reality creature (stage-true infant: infant CT +
infant-appropriate numbers). The adult is a SECOND valid reality creature awaiting
adult data. Both can exist; **neither mixes.**

### 6.3 Commands (the spec for tooling, named here so the gates are buildable)

- `bio.stage <record|creature>` → prints the stage label + evidence, or FAILS the
  record as unadmittable (missing stage = failed, like a missing sha256).
- `bio.check <creature>` → runs L1 (stage agreement across all bound records),
  L2 (proportion/allometry band check per stage), L3 (substitution declarations
  present and within distance), L4 (delegates to the physics gates) → prints
  `{category, violations}`. This is the "does this biologically check out" command.
- `bio.fantasy acknowledge <manifest>` → the developer-driven construction mode:
  records the manifest acknowledgment and only then admits to the fantasy category.
- All four belong in the repeatable MCP/command surface the operator has directed,
  with results admitted through the batch/intake machinery like any other verdict.

---

## 7. RANKING (criteria applied — C1 stage, C2 coverage, C3 license, C4 acquisition, C5 format, C6 dual answer, C7 pipeline fit)

| rank | candidate | C1 stage | C2 coverage | C3 license | C4 acquisition | C5 format | C6 dual | verdict |
|---|---|---|---|---|---|---|---|---|
| **1** | **Visible Monkey** (Chung 2019 sections + paired MRI/CT; Kim 2020 STL set) | **ADULT-CONFIRMED** (93 mo female, published) | whole-body, 3 modalities | article CC BY-NC; **data license unstated**, free by request | **email + ETRI certification** (manual) | STL triangles (skin/skeleton/merged muscle) + 24-bit sections + MRI/CT volumes | **YES — body AND muscle-layer AND skin roadmap** | **TOP. The only obtainable adult whole-body macaque of any kind; multi-layer membranes in triangles; costs are human doors + unstated data license** |
| **2** | **UC Davis full-body adult CT ×14** (media 000069177…000078191; Buck 2021 network) | adult via publication network; **per-specimen age to confirm at request** | whole-body CT | `CommercialUseNotPermitted`, `restricted_download` | MorphoSource permission request (**manual**) | CT volume (marching-cubes proven) | partial (soft tissue in medical-adjacent microCT — resolution to verify) | **RUNNER-UP. Species-exact rhesus, 14 specimens, sex-known; blocked on two human doors (permission + license), same as the infant bones already accepted** |
| 3 | Wiseman 2026 RSOS hindlimb MSK models + SIs | adult per paper (moment-arm study, subject-specific) | hindlimb only | **CC BY 4.0 (SIs verified)** | Figshare API-able; model files manual | OpenSim paths + likely meshes | muscle-geometry ONLY | best license-clean MUSCLE geometry; complements 1–2; model-file location is the open action |
| 4 | NMNH M. fascicularis full-body ×2 (000875609/000875614) | **UNCONFIRMED** (fails C1 until stage-checked in-scan) | whole-body | Undetermined + non-commercial | **open download** | CT volume | partial | only OPEN whole-body macaques besides our infants; Tier-2 species fallback; stage-gate first |
| 5 | our infant NMNH CT ×2 (000875599/000875604) | infant (labeled) | whole-body | Undetermined + non-commercial | in-repo | CT volume | — | reality creature #1 (baby); done |
| 6 | UNC-W neurodevelopment MRI | immature only | head/brain FOV | CC BY 4.0, open | API | NIfTI volume | head only | baby's future head soft-tissue; never the adult |
| 7 | Guimaraes 2026 + Oku 2021 + arm model (in-repo) | adult (labeled "Adult", 8 kg) / adult / adult | numbers + paths, no geometry | CC BY 4.0 / CC BY 4.0 / MIT | in-repo | tables + osim | numbers only | already admitted; feeds Options A/C |
| 8 | Copes 2016 macaque skulls | mixed, unlabeled per specimen | skull | CC BY-NC | manual | volume/mesh | no | skull resource at best |
| — | Li 2017 QIMS | adult-confirmed | whole-body | all rights reserved | **dead end** | — | — | feasibility proof only |
| — | MOP/CARTA, DigiMorph, KUPRI DMM | unverified | bones/skulls | unstated/unreachable | manual/unknown | — | no | watch-list only |

**Recommendation (top):** pursue **rank 1 (Visible Monkey)** and **rank 2 (UC Davis
adult CTs)** through their human doors in that order — rank 1 for the multi-layer
triangle membranes (skin + skeleton + muscle envelope of an adult, with the pairing
MRI/CT volumes for real segmentation work), rank 2 for species-exact adult rhesus
volumes; **in parallel, take rank 3 (Wiseman 2026)** as the immediate license-clean
muscle-geometry intake (CC BY 4.0, Figshare API-able, same lab/homology as the
admitted Guimaraes batch). Tier 2 (other species) measured worse everywhere —
the license wall, not the species list, is the binding constraint, so the honest
Tier-3 recommendation if the human doors stay shut is Option C (stage-true
aliveness) with Option A (parametric muscles from admitted numbers) as the muscle
interim — and Option B (single-stretch adultization) is biologically REFUSED
under L2, with the mounting lane's measured 3.8–8.8× spread as the evidence.

---

## 8. THE OPERATOR HAND-DOWNLOAD LIST (TIER-1 deliverable — exact links, in order)

**Priority 1 — Visible Monkey (adult female rhesus, whole body, sections+MRI+CT):**
1. Paper (read first): https://pmc.ncbi.nlm.nih.gov/articles/PMC6393759/
2. Request the sectioned images + paired MRI/CT by email: park93@dongguk.ac.kr
   ("will be provided to any requesting researcher free of charge" — ask for the
   DICOM sectioned images, the MRI and CT series, and the license statement in
   writing).
3. Companion segmentation set (167 structures, STL): https://pmc.ncbi.nlm.nih.gov/
   articles/PMC7167398/ — request ETRI user certification for the segmented STL
   download (ask for per-structure file list + license).

**Priority 2 — UC Davis adult full-body rhesus CT ×14 (MorphoSource; MANUAL, by
law — the operator downloads by hand; an account with download permission is
required because visibility is `restricted_download`):**
- https://www.morphosource.org/concern/media/000069177 (ucd:37163, F)
- https://www.morphosource.org/concern/media/000069518 (ucd:37177, F)
- https://www.morphosource.org/concern/media/000073328 (ucd:37477, F)
- https://www.morphosource.org/concern/media/000073364 (ucd:38328, F)
- https://www.morphosource.org/concern/media/000073365 (ucd:38341, F)
- https://www.morphosource.org/concern/media/000073366 (ucd:38465, F)
- https://www.morphosource.org/concern/media/000073367 (ucd:39242, F)
- https://www.morphosource.org/concern/media/000073368 (ucd:39026, F)
- https://www.morphosource.org/concern/media/000073369 (ucd:39374, F)
- https://www.morphosource.org/concern/media/000073370 (ucd:39481, F)
- https://www.morphosource.org/concern/media/000077648 (ucd:39512, M)
- https://www.morphosource.org/concern/media/000078098 (ucd:39612, F)
- https://www.morphosource.org/concern/media/000078187 (ucd:39650, M)
- https://www.morphosource.org/concern/media/000078191 (ucd:39882, F)
- At request time ALSO: ask UC Davis/the collection for per-specimen AGE records
  (stage verification under the new law) and note the license PDF each page shows.
- Suggested first two downloads (one per sex): 000077648 (M), 000073364 (F).

**Priority 3 — Wiseman 2026 hindlimb models (license-clean muscle geometry):**
1. SI 1 (homology, CC BY 4.0): https://doi.org/10.6084/m9.figshare.32017187
2. SI 2 (moment arms, CC BY 4.0): https://doi.org/10.6084/m9.figshare.32017184
3. Manual follow-up: fetch the article PDF and its data-availability statement
   (https://doi.org/10.1098/rsos.260107 — the publisher blocks agents) and locate
   the deposited OpenSim model files (Cambridge Apollo candidate; request if
   unlisted).

**Priority 4 (fallback, stage-gated) — the only OPEN whole-body macaques besides
our infants:**
- https://www.morphosource.org/concern/media/000875609 (USNM 267307, M. fascicularis)
- https://www.morphosource.org/concern/media/000875614 (USNM 268003, M. fascicularis)
- DOWNLOAD IS OPEN, but admission is blocked until stage is verified in-scan or
  from the NMNH catalog (unlabeled = unadmittable).

---

## 9. SOURCES

- Copes LE, Lucas MM, Thostenson JO, Hoekstra HE, Boyer DM (2016). A collection of
  non-human primate computed tomography scans housed in MorphoSource. Sci Data
  3:160001. https://doi.org/10.1038/sdata.2016.1 (PMCID PMC4736502)
- Li CX, Zhang X (2017). Whole body MRI of the non-human primate using a clinical
  3T scanner: initial experiences. QIMS 7(2):267-275. https://doi.org/10.21037/qims.2017.04.03
  (PMCID PMC5418147)
- Young JT et al. (2017). UNC-Wisconsin Rhesus Macaque Neurodevelopment Database.
  Front Neurosci; data: https://doi.org/10.5281/zenodo.233682 (CC BY 4.0)
- Museum of Primatology (MOP), CARTA UCSD: https://carta.anthropogeny.org/museum/collections
- Chung BS, Jeon CY, Huh JW, Jeong KJ, Har D, Kwack HH, Park JS (2019). Rise of the
  Visible Monkey: Sectioned Images of Rhesus Monkey. J Korean Med Sci 34:e70.
  https://doi.org/10.3346/jkms.2019.34.e70 (PMCID PMC6393759)
- Kim CY, Lee AK, Choi HD, Park JS (2020). Dawn of the Visible Monkey: Segmentation
  of the Rhesus Monkey for 2D and 3D Applications. J Korean Med Sci 35:e71.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7167398/
- Buck LT, Katz DC (2021). Effects of hybridization on pelvic morphology: A macaque
  model. (138 full-body CTs of adult CNPRC rhesus; NSF PAR record; data via
  MorphoSource.) + Buck et al. (2025) body size/shape follow-up.
- Wiseman AL, Bollmann van Beesel J, Vereecke E (2026). Comparative analysis of
  primate hind limb muscle moment arms using subject-specific three-dimensional
  musculoskeletal models. R Soc Open Sci 13:rsos.260107. https://doi.org/10.1098/rsos.260107
  (CC BY 4.0); SIs: https://doi.org/10.6084/m9.figshare.32017187 ,
  https://doi.org/10.6084/m9.figshare.32017184
- Guimarães E, Vereecke E, Wiseman AL (2026). Functional Differences in Muscle
  Architecture Across the Pelvis and Hind Limb of Primates. Am J Phys Anthropol
  (AJPA-190-e70329), PMC13425262 (admitted batch `guimaraes_arch`, CC BY 4.0)
- Oku Y, Ide N, Ogihara N (2021). Commun Biol 4:1831, PMC7940622 (admitted batch
  `oku_bipedal`, CC BY 4.0)
- limblab/monkeyArmModel @ `4fb7dddeec06a0df9525c18f37234a824cb1b5b1` (MIT)
- MorphoSource REST API (search): https://morphosource.stoplight.io ; sweep data
  collected 2026-09-20 this lane (1,671 Macaca + 2,495 Papio media records)
- XROMM (biplanar X-ray reconstruction): https://xromm.org
- In-repo (branch `origin/agent/skeleton-movie-20260919` unless noted):
  `tools/science_funnel/data/guimaraes_arch/`, `tools/science_funnel/data/oku_bipedal/`,
  `tools/science_funnel/data/macaque_arm/`, `tools/science_funnel/data/morphosource_ct/`,
  `tools/science_funnel/validation/batch_muscle_20260917/receipt.json`,
  `tools/science_funnel/validation/muscle_paths_20260918/`,
  `docs/research/20260918_muscle_path_derivation.md`,
  `docs/research/20260918_monkey_assembly_derivation.md`,
  `docs/MUSCLE_ATLAS.md`, `docs/research/muscle_physiology_reference.md`,
  `tools/extract_muscle_atlas.py`, `tools/science_funnel/macaque_anatomy.py`;
  on `origin/master`: `docs/research/muscle_physiology_reference.md`,
  `research_references/human/MUSCLE_INVENTORY.md`. Checklist:
  `docs/THE_CHECKLIST.md` @ branch `agent/workflow-checklist-20260920` (`e9c8b394`).
