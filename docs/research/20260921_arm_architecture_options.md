# FORELIMB MUSCLE ARCHITECTURE — RESEARCH MEMO (2026-09-21)

Lane: `agent/arm-architecture-research-20260921` (research-only; no engine/scene code).
Branch base: `origin/agent/muscle-data-research-20260920` @ `fc45106c`. Agent: GLM 5.3.

The named successor of the parametric muscle layer's next gap: the **FORELIMB muscle
architecture**. The hindlimb has the Guimaraes 2026 batch (36 muscles, measured mass /
PCSA / FL / pennation, admitted CC BY 4.0); **the arm has only the arm model's Fmax
39/39 — no PCSA, no muscle mass, no fiber length; geometry is impossible from it.**
This memo finds what measured forelimb architecture exists, inventories what the 39
Fmax values actually are and their provenance, states the honesty class of the
interim Fmax→PCSA bootstrap, and hands off exact sources. It cites the first memo's
pattern throughout: `docs/research/20260920_adult_and_muscle_data_options.md`
(Rule-0 pre-registration, lettered criteria, honest-tension notes, human doors).

---

## RULE 0 — PRE-REGISTRATION (stated before the ranking)

**STATEMENT (a theory, disagreeable):** Measured per-muscle forelimb architecture
(mass, PCSA, fascicle length, pennation) for macaques exists ONLY inside journal
papers — there is NO openly licensed (CC) dataset deposit of it on Figshare/Zenodo —
and the measured data splits in two halves that must be bought at two different
doors: **shoulder+elbow = Cheng & Scott 2000** (J Morphol, paywalled Wiley), the same
measured source the arm model's Fmax descends from; **forearm+hand = the Vereecke
lab's own forelimb companion, Vanhoof 2020/2021** (J Anat, free on PMC), the only
freely downloadable per-muscle measured M. mulatta forelimb source in existence.

**PREDICTION (was unmeasured before this lane's runs):** (i) the arm model's 39 Fmax
records are NOT 39 measurements — the wrist/digit muscles carry template defaults:
at least 9 records share one identical Fmax value and at least 8 share one identical
`optimal_fiber_length`; (ii) the Figshare and Zenodo API sweeps (queries recorded in
§4.8) return ZERO CC-licensed per-muscle cercopithecine forelimb architecture
deposits.

**FALSIFIER (named before the run):** (i) the in-repo dump below reproducible from
`tools/science_funnel/data/macaque_arm/monkeyArm_current.osim` shows continuously
varying, never-repeated Fmax / fiber lengths — then the "template default" reading
dies and the bootstrap honesty class rises; (ii) a CC-licensed per-muscle forelimb
(or whole forelimb) architecture dataset for any cercopithecine exists on
Figshare/Zenodo/any repository the sweeps missed — then the ranking in §5 changes;
(iii) Vanhoof Part II's supplementary tables do NOT carry per-muscle raw values —
then rank 1 falls. Any one of the three falsifies the recommendation.

### Pre-registered evaluation criteria (applied in §5, in this order)

- **A1 STAGE VERIFICATION (admission-required, like sha256 — mirrors C1).** Adult
  must mean adult-confirmed from collection/publication records. Under L1 (stage
  consistency law, first memo §6.1), measured forelimb architecture attaches ONLY to
  the adult creature line — adult numbers on the infant creature are an L1 violation
  the gate must refuse, not a style choice.
- **A2 SPECIES MATCH.** M. mulatta exact > M. fuscata (within-genus declared
  substitution, the Oku-inertials precedent under L3) > other Macaca > other
  cercopithecine > hominoid (method template only, never merged).
- **A3 FIELD COVERAGE.** All four wanted fields (mass, PCSA, fascicle length,
  pennation). Measured-PCSA > mass+FL (PCSA derivable from them) > PCSA-only.
  Pennation is the rarest field — carry it where it exists.
- **A4 LICENSE.** CC BY 4.0 > free-access-with-license-to-pin (PMC-hosted, © held)
  > paywalled proprietary (table transcription through institutional access is the
  OPERATOR's door — reported, never waived silently; same tension the first memo
  recorded for our infant bones).
- **A5 ACQUISITION.** API/bulk download > manual download of open files > manual
  transcription from paywalled tables.
- **A6 HONESTY CLASS.** measured per-muscle > derived-by-a-stated-law (PROVISIONAL)
  > hand-set default (EXCLUDED from every force claim). A record without a stated
  provenance is class-3, no matter how physiological it looks.
- **A7 PIPELINE FIT.** Admittable through the batch connectors (sha256 receipt,
  idempotent replay) and mappable per muscle NAME onto the 39 arm records via a
  homology table (the Guimaraes S2 docx pattern).

---

## 1. IN-REPO INVENTORY — what the arm model's 39 Fmax records actually are (measured, this lane)

Source: `tools/science_funnel/data/macaque_arm/monkeyArm_current.osim`
(limblab/monkeyArmModel @ `4fb7ddde…`, MIT; receipt-pinned; 39 ×
`Schutte1993Muscle_Deprecated`), parsed this lane. One `<Thelen2003Muscle
name="default">` template element sits in the file's `<defaults>` block
(max_isometric_force 546 — a human-scaled OpenSim default, not a muscle).

| muscle | Fmax (N) | opt fiber L (m) | tendon slack L (m) | pennation (rad) | note |
|---|---|---|---|---|---|
| abd_poll_longus | 30 | 0.089754 | 0.0285 | 0 | default-Fmax |
| anconeus | 30 | 0.010206 | 0.019627 | 0 | default-Fmax |
| bicep_lh | 58.2 | 0.122492 | 0.070845 | 0.12217305 | |
| bicep_sh | 38.7 | 0.122492 | 0.042526 | 0 | |
| brachialis | 135.6 | 0.057 | 0.03502 | 0 | |
| brachioradialis | 38.7 | 0.122492 | 0.04335 | 0 | dup of bicep_sh |
| coracobrachialis | 38.7 | 0.085942 | 0.002 | 0.2268928 | |
| deltoid_ant | 135.6 | 0.0455 | 0.002 | 0 | dup of brachialis |
| deltoid_med | 116.1 | 0.051036 | 0.002 | 0.34906585 | |
| deltoid_pos | 406.5 | 0.06898635 | 0.002 | 0 | |
| dorsoepitrochlearis | 44.8 | 0.122492 | 0.039172 | 0 | |
| ext_carpi_rad_longus | 72 | 0.1173 | 0.055 | 0.1553343 | |
| ext_carp_rad_brevis | 30 | 0.1225 | 0.0365 | 0.01745329 | default-Fmax |
| ext_carpi_ulnaris | 30 | 0.122492 | 0.050385 | 0.06108652 | default-Fmax |
| ext_digitorum | 30 | 0.122492 | 0.0457 | 0.05235988 | default-Fmax |
| ext_digiti | 30 | 0.122492 | 0.0603 | 0.04537856 | default-Fmax |
| ext_indicis | 30 | 0.044047 | 0.030981 | 0.10995574 | default-Fmax |
| flex_carpi_radialis | 60 | 0.122492 | 0.042532 | 0.05410521 | |
| flex_carpi_ulnaris | 96 | 0.044632 | 0.122492 | 0.21118484 | tendonL = ceiling |
| flex_digit_profundus | 30 | 0.06132958 | 0.04029373 | 0.12042772 | default-Fmax |
| flex_digit_superficialis | 30 | 0.122492 | 0.072174 | 0.09599311 | default-Fmax |
| flex_poll_longus | 30 | 0.028065 | 0.060818 | 0.12095132 | default-Fmax |
| infraspinatus | 174.3 | 0.049413 | 0.002 | 0.26179939 | |
| lat_dorsi_sup | 129 | 0.122492 | 0.002 | 0 | |
| lat_dorsi_cen | 129 | 0.1119 | 0.002 | 0 | |
| lat_dorsi_inf | 129 | 0.1225 | 0.0087 | 0 | |
| palmaris_longus | 27 | 0.122492 | 0.023407 | 0.06108652 | |
| pectoralis_sup | 154.8 | 0.0541 | 0.002 | 0 | |
| pectoralis_inf | 116.1 | 0.0648 | 0.002 | 0 | |
| pronator_quad | 33.3 | 0.025284 | 0.002 | 0.1727876 | |
| pronator_teres | 48.3 | 0.0416 | 0.01254 | 0.2268928 | |
| subscapularis | 290.4 | 0.05239 | 0.008831 | 0.38397244 | |
| supinator | 30 | 0.045107 | 0.002 | 0.29670597 | default-Fmax |
| supraspinatus | 135 | 0.069278 | 0.002 | 0.26179939 | |
| teres_major | 77.4 | 0.0815 | 0.002 | 0.2443461 | |
| teres_minor | 174 | 0.04029481 | 0.002 | 0.20943951 | |
| tricep_lat | 135.6 | 0.122492 | 0.018409 | 0.36651914 | dup of brachialis |
| tricep_lon | 116.1 | 0.106152 | 0.036031 | 0.54105207 | |
| tricep_sho | 135.6 | 0.093578 | 0.010198 | 0.31415927 | dup of brachialis |

Sum Fmax = 3575.8 N. **The prediction's patterns, measured:**

1. **11 of 39 Fmax are exactly 30.0 N** (marked default-Fmax) — ten of the eleven
   are antebrachial/hand muscles. 30 N is a floor value, not a measurement.
2. **`optimal_fiber_length` = 0.122492 m repeats 9× (plus 0.1225 twice)** — a shared
   ceiling constant, not per-muscle fiber measurements. `flex_carpi_ulnaris` even
   carries it as TENDON slack length — a slot swap no measurement would produce.
3. **Fmax duplicates cluster:** 38.7 ×3, 135.6 ×4, 129 ×3, 116.1 ×3 — plausible for
   symmetric heads, implausible for independently measured antagonists sharing a
   value to 0.1 N.
4. **The fields carried are exactly Cheng & Scott Part I's five-parameter set minus
   the two measured parents** — the model has optimal fiber length, tendon slack
   length, pennation, and a derived Fmax, but NOT muscle mass and NOT PCSA (the two
   quantities Cheng & Scott measured first).

### 1.1 The provenance chain (measured, this lane)

- `download_receipt.json`: limblab/monkeyArmModel @ `4fb7ddde…`, MIT; the repo's own
  README: **"based on Chan and Moran 2008"** (the computational macaque arm model).
- **Chan SS, Moran DW (2006).** "Computational model of a primate arm: from hand
  position to joint angles, joint torques and muscle forces." J Neural Eng
  3(4):327-337, DOI 10.1088/1741-2560/3/4/010 — 3D 7-DOF macaque arm model.
  **Paywalled** (IOP; not in PMC; Europe PMC `isOpenAccess: N`).
- **Chowdhury RH, Glaser JI, Miller LE (2020)**, eLife 9:e48198 (PMC6977965, CC BY)
  — the paper `macaque_anatomy.py` cites as the model's "publication" — actually the
  USING paper: "derived from the length of the 39 modeled muscles (Chan and Moran,
  2006)", model shared at github.com/limblab/monkeyArmModel. It documents NO muscle
  parameter values. The intake record itself flags `unknowns: "source XML credits
  are placeholders"`.
- **Cheng EJ, Scott SH (2000).** "Morphometry of Macaca mulatta forelimb. I.
  Shoulder and elbow muscles and segment inertial parameters." J Morphol
  245(3):206-224, PMID 10972970, DOI
  10.1002/1097-4687(200009)245:3<206::AID-JMOR3>3.0.CO;2-U — **21 muscles spanning
  shoulder and/or elbow of 6 M. mulatta + 3 M. fascicularis; five parameters:
  optimal fascicle length, tendon slack length, PCSA, pennation angle, muscle
  mass** + segment inertials. Paywalled Wiley.
  **The last hop — Chan & Moran's Fmax ← Cheng & Scott's PCSA — is INFERENCE, not
  documentation:** nothing we can open states it. But the correspondence is tight:
  the model's 22 shoulder/elbow muscles ≈ Part I's 21 (+ the monkey-specific
  dorsoepitrochlearis); the carried field set is Part I's minus mass/PCSA; and
  Scott's lab produced both papers (Queen's Univ / WashU). Fmax/30 N/cm² gives
  physiological PCSAs (e.g. bicep_lh 58.2 N → 1.94 cm²) consistent with the rhesus
  range the literature reports.
- Series companions (same team, J Morphol): **Part II Singh, Melis, Richmond, Scott
  (2002)**, fiber-type composition, 251(3):323-332, DOI 10.1002/jmor.1092;
  **Part III Graham, Scott (2003)**, moment arms, 255(3):301-314, DOI
  10.1002/jmor.10064 (moment arms we already hold as model paths).
- **Antebrachial gap:** Part I measured ONLY shoulder/elbow-spanning muscles. The
  model's 17 antebrachial muscles have NO measured architecture source anywhere in
  the chain — and 11 of them are exactly the default-30 records. The remaining 6
  non-default antebrachial Fmax values (72, 96, 60, 27, 48.3, 33.3) have UNKNOWN
  provenance (other literature or scaled estimates — unverifiable from open text).

**Verdict (A6 applied):** of 39 records — **22 provisional-derived** (shoulder/
elbow, measured parentage in the paywalled literature), **6 unknown-provenance**,
**11 hand-set defaults** (not data). The intake adapter already records
`force_runtime_ready: false` for all 39 — consistent, and still true after this memo.

---

## 2. THE σ LAW AND THE FMAX-BOOTSTRAP — honesty class of the interim

`PCSA_i = Fmax_i / σ` — a one-line derivation, and the ONLY route to forelimb
architecture from in-repo data today. The σ candidates:

- **In-repo law:** `docs/research/muscle_physiology_reference.md` — vertebrate
  skeletal average **25–32 N/cm²** ("the myobody value"); the posture-cap lane used
  **σ = 0.3 MPa (30 N/cm²)** as the external constant. Mid-band.
- **Literature precedent, same act:** Saito 2021 (macaque hand model, CC BY,
  PMC8693514) computes maximum force = PCSA × **23 N/cm²** (cat soleus, Spector et
  al. 1980) — "applied to primate hand muscles without validation," by the paper's
  own wording. The literature bootstraps the same way we would, and says so out
  loud.
- **The unknown that breaks the round trip:** if Chan & Moran derived Fmax from
  Cheng & Scott's PCSA, they used SOME σ. It is not stated in anything we can open.
  Deriving PCSA = Fmax/σ with OUR σ therefore does not recover the MEASURED PCSA —
  it recovers the measured PCSA scaled by σ_original/σ_ours. The number is derived,
  not measured, and not even round-trip-stable.

**HONESTY CLASS (the answer to the mission's question): the Fmax-bootstrap interim
is PROVISIONAL — derived-not-measured under the biological laws — with three
sub-classes that must be admitted per record, never as one batch:**

- **22 shoulder/elbow records: `derived-provisional`** — measured parentage
  (Cheng & Scott PCSA) upstream, but inverted through an unknown σ. Admittable for
  envelope geometry and provisional force work; force claims stay
  `force_runtime_ready: false` until upgraded from a measured source.
- **6 antebrachial non-default records: `provenance-unknown`** — same handling as
  provisional but with the unknown declared on the record.
- **11 default-30 records: `default-excluded`** — PCSA = 30/σ would be a derivation
  on a placeholder; doubly fake. Excluded from every force and volume claim (the
  H-21 discipline: a verb needs behavior, not metadata).

PROVISIONAL is also the ceiling for another reason: σ itself carries no per-specimen
stage and no per-muscle fiber-type weighting (Part II's fiber-type composition is
exactly the refinement a future measured upgrade would add). The upgrade path off
PROVISIONAL is rank 1 + rank 2 of §4 — both exist, both are enumerated below.

---

## 3. THE OTHER HALF — what the measured forelimb literature holds

### 3.1 Forearm + hand: the Vereecke lab's forelimb companion (the mission's target)

**Vanhoof MJM, van Leeuwen T, Vereecke EE (2020); Vanhoof MJM, van Leeuwen T,
Galletta L, Vereecke EE (2021).** "The forearm and hand musculature of
semi-terrestrial rhesus macaques (Macaca mulatta) and arboreal gibbons (fam.
Hylobatidae)." Part I: Description and comparison of the muscle configuration —
J Anat 237(4), DOI 10.1111/joa.13222, PMC7495296. Part II: **Quantitative
analysis** — J Anat 238(2), DOI 10.1111/joa.13314, **PMC7812139**.

- **Specimens: 7 ADULT M. mulatta** (Mm1–Mm7; Mm2 female, Mm6 male, rest unknown),
  opportunistic cadavers via Ghent University; funded KU Leuven C14/16/082. Adult
  status labeled at source (A1 pass).
- **Variables per muscle: muscle mass, muscle volume, MTU length, fascicle length,
  external + internal tendon length; PCSA derived** (the authors deliberately omit
  pennation from the PCSA equation — so NO pennation field exists here; A3 partial).
- **Coverage: ~40+ muscles/heads** — upper-arm, forearm, and intrinsic hand — the
  exact complement of Cheng & Scott's shoulder/elbow. Together they tile the whole
  forelimb.
- **Raw data: supplementary Tables S1 and S2** — as two large TIFF images hosted on
  PMC (`JOA-238-321-s001.tif` 10.3 MB, `JOA-238-321-s002.tif` 6.2 MB under
  PMC7812139). Free to download, but tables-as-images ⇒ manual transcription (A5
  manual; a real but bounded cost — two tables).
- **License: NOT CONFIRMED.** PMC page carries "© 2020 Anatomical Society" and NO
  CC statement; Crossref license field = Wiley T&C only; Europe PMC `isOpenAccess:
  N`. Same honesty treatment as our accepted infant bones (copyright Undetermined):
  free to READ and download via PMC; the reuse license must be PINNED by the
  operator from the Wiley landing page at download time (A4 middle tier, recorded
  tension, operator's call).
- **Same lab network as the admitted Guimaraes batch** (Vereecke) — the homology
  table style of Guimaraes S2 should map these names onto the 39 arm records (A7).

### 3.2 Shoulder + elbow: the paywalled classic

**Cheng & Scott 2000** (full citation §1.1): 21 shoulder/elbow muscles, 6 M.
mulatta + 3 M. fascicularis, ALL FOUR wanted fields (mass, PCSA, fascicle length,
pennation — A3 full pass), adult lab animals, body-mass regressions included.
Access: Wiley paywall — institutional access + manual table transcription through
the operator's door (A4/A5 low, A3+A2+A1 top). Part II (Singh 2002) adds fiber-type
composition per muscle — the σ-refinement data.

### 3.3 The hand, measured, one specimen

**Oishi M, Ogihara N, Endo H, Ichihara N (2012).** "Muscle dimensions in the
Japanese macaque hand." Primates 53, DOI 10.1007/s10329-012-0309-3 — measured hand
muscle dimensions of ONE M. fuscata (springer paywall). This is the specimen
("Macaque A") whose PCSAs feed Saito 2021's hand model.

**Saito T et al. (2021).** "Musculoskeletal Modeling and Inverse Dynamic Analysis
of Precision Grip in the Japanese Macaque." Front Syst Neurosci 15:774596, DOI
10.3389/fnsys.2021.774596, PMC8693514, **CC BY** — 23-muscle hand model from a CT
of an adult male ~10 kg M. fuscata; **Table 2 = per-muscle PCSA and Fmax**
(σ = 23 N/cm² declared). A2 = within-genus declared substitution (L3, the Oku
precedent); openly readable; a self-consistent worked example of exactly the
bootstrap our §2 describes.

### 3.4 Geometry-lane feeders (CC BY, MDPI — attachments, not architecture)

- **Casteleyn C et al. (2024).** "Hand Musculature of the Rhesus Monkey (Macaca
  mulatta): An Anatomical Study." Anatomia 3(3), DOI 10.3390/anatomia3030013
  (MDPI, CC BY).
- **Casteleyn C et al. (2023).** "Topographical Anatomy of the Rhesus Monkey
  (Macaca mulatta) — Part I: Thoracic Limb." Vet Sci 10(2):164, DOI
  10.3390/vetsci10020164 (MDPI, CC BY; Part II covers the pelvic limb). Descriptive
  dissection anatomy — origins/insertions/spatial relations — feeds the muscle
  GEOMETRY question (the first memo's §5 gap), not the architecture numbers.

### 3.5 Companion (not architecture)

**Taitano RI, Yakovenko S, Gritsenko V (2024).** "Muscle anatomy is reflected in
the spatial organization of the spinal motoneuron pools." Commun Biol 7, DOI
10.1038/s42003-023-05742-w, PMC10789783, CC BY 4.0 — Chan & Moran model extended
with 8 forelimb muscles (atlas: Berringer, Browning & Schroeder 1968) + CMC/MCP/IP
joints (27 DOF); data at Figshare DOI 10.6084/m9.figshare.24291232.v2 (CC BY).
Motoneuron coordinates, not architecture tables. Useful later for neural-drive
work; not a candidate here.

### 3.6 Method templates (paywalled, comparative — how the field does it)

- Carlson KJ (2006). "Muscle architecture of the common chimpanzee (Pan
  troglodytes)…" Primates 47, DOI 10.1007/s10329-005-0166-4 — the chimpanzee
  forelimb architecture template.
- Myatt JP et al. (2012). "Functional adaptations in the forelimb muscles of
  non-human great apes." J Anat 220, DOI 10.1111/j.1469-7580.2011.01443.x.
- Leischner CL, Crouch M, Allen KL, Marchi D, Pastor F, Hartstone-Rose A (2018).
  "Scaling of Primate Forelimb Muscle Architecture as It Relates to Locomotion and
  Posture." Anat Rec 301(3):484-495, DOI 10.1002/ar.23747 — 44 species / 55
  specimens, forearm muscles, mass+PCSA+RPCSA+FL; the allometric-scaling reference
  for cross-body-mass sanity checks.
- Deane AS et al. (2024), Anat Rec — comparative forelimb PCSA (Vereecke coauthor).
- Van Beesel, Melillo, Vereecke (2025), J Anat, DOI 10.1111/joa.14199 — 3D shoulder
  muscle reconstruction in HOMINOIDS (attachment-area ↔ volume correlations).

### 3.7 The watch item (a human door, not a download)

The admitted Guimaraes hindlimb specimen **"127 [KU Leuven]"** (the 8-kg adult male
M. mulatta) belongs to the SAME lab that produced Vanhoof's forearm/hand series.
The Guimaraes fulltext (in-repo, PMC13425262) records that some specimens' "upper
limb and torso had been dissected for previous studies (Van Beesel et al. 2025)"
— a hominoid-shoulder paper, so whether specimen 127's forelimb architecture is
already IN HAND at KU Leuven is unknown from here. **One email to the
Wiseman/Vereecke lab** — asking for a forelimb companion to the Guimaraes hindlimb
dataset (same 36-muscle format) — could land the whole forelimb as one CC BY batch
in the admitted batch's own shape. This is the highest-leverage human door on the
board and costs one message.

### 3.8 Negative results (measured, this lane)

- **Figshare API** (`api.figshare.com/v2/articles/search`): `primate muscle
  architecture forelimb` → 0 results; `"muscle architecture" macaque OR primate
  PCSA` → noise (unrelated). **Zenodo API** (`zenodo.org/api/records`):
  `"muscle architecture" primate` → marmoset fMRI, Papionini mitogenomics,
  JARVIS-MoCap grasping — nothing per-muscle; `"PCSA" forelimb` → koala myology
  figures (license `notspecified`), Dryad muscle-CT roadmap. **No CC-licensed
  per-muscle cercopithecine forelimb architecture deposit exists on either
  repository.** The measured data lives in papers, full stop.
- MorphoSource is osteological for our purposes (first memo's sweep, 1,671 Macaca
  media) — no muscle architecture there by construction.

---

## 4. RANKING (criteria applied — A1 stage, A2 species, A3 fields, A4 license, A5 acquisition, A6 honesty, A7 pipeline fit)

| rank | candidate | A1 | A2 | A3 | A4 | A5 | A7 | verdict |
|---|---|---|---|---|---|---|---|---|
| **1** | **Vanhoof 2020 Part I + 2021 Part II (J Anat, PMC7495296 + PMC7812139)** | adult-labeled ×7 | **M. mulatta exact** | mass/volume/FL/MTU/tendon + PCSA (no pennation) | free via PMC; **license to pin** | manual download + 2-TIFF transcription | homology maps onto 39 names (same lab style) | **TOP. The only freely downloadable measured M. mulatta forelimb architecture; tiles the forearm+hand half exactly where Cheng & Scott stops; covers 14 of the 17 antebrachial model muscles' territory** |
| **2** | **Cheng & Scott 2000 Part I (+ Part II fiber types 2002)** | adult lab animals | mulatta + fascicularis | **all four fields incl. pennation** | paywalled Wiley | institutional access + table transcription (operator door) | names match model 1:1 (shoulder/elbow 22) | **RUNNER-UP. The measured parent of the model's Fmax; upgrades the 22 provisional records to measured and pins the σ round trip; also delivers the segment inertials for the forelimb** |
| 3 | Wiseman/Vereecke-lab forelimb companion email (specimen 127) | adult (127 = 8 kg male) | mulatta exact | would match Guimaraes format | CC BY 4.0 (if it lands like the hindlimb) | one email | perfect (their own S2 homology style) | **highest leverage per cost; outcome uncertain — human door** |
| 4 | Saito 2021 hand model Table 2 (+ Oishi 2012 behind it) | adult male | M. fuscata (declared, L3) | PCSA+Fmax per muscle (23 hand muscles) | **CC BY** | open PMC read | name-mapping needed | best license-clean HAND numbers; species-substitution declared, never merged |
| 5 | Casteleyn MDPI set (Anatomia 2024 hand; Vet Sci 2023 thoracic limb) | adult | mulatta exact | descriptive (no architecture) | **CC BY** | open | geometry lane | feeds muscle GEOMETRY (attachments), not architecture numbers |
| 6 | σ-bootstrap from in-repo Fmax (§2) | n/a (adult-chain) | mulatta (chain) | derived only | MIT (in-repo) | in-repo | existing connector | **PROVISIONAL interim — runs today, tagged per §2's three sub-classes; never reality-class until 1–3 land** |
| 7 | Taitano 2024 Commun Biol + Figshare 24291232 | adult | mulatta/fascicularis | none (MN maps) | CC BY 4.0 | API-able | later neural lane | companion, not architecture |
| 8 | Method templates (Carlson 2006; Myatt 2012; Leischner 2018; Deane 2024; Van Beesel 2025) | mixed | non-macaque | reference standards | paywalled/varied | manual | templates only | how-to + allometric sanity checks; never merged (L3) |

**Recommendation (top):** run the lanes in this order — **(1)** hand-download the
Vanhoof set (below), transcribe S1/S2, and admit as batch `vanhoof_forearm` with
per-record honesty tags; **(2)** send the ONE email to the Vereecke/Wiseman lab
about a forelimb companion to the Guimaraes dataset (cheapest possible
whole-forelimb win, CC BY, same-format); **(3)** put Cheng & Scott 2000 on the
operator's institutional-access door and transcribe the 21 shoulder/elbow tables —
this is the record-level upgrade of the model's own ancestry; **(4)** until 1–3
land, the σ-bootstrap (§2) runs as the declared PROVISIONAL interim with its three
sub-classes, exactly as the posture-cap lane ran σ as a declared external constant.

---

## 5. THE OPERATOR HAND-DOWNLOAD LIST (in order)

**Priority 1 — Vanhoof forearm/hand architecture (free, browser):**
1. Part II (quantitative): https://pmc.ncbi.nlm.nih.gov/articles/PMC7812139/ — PDF
   + supplementary tables:
   - https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s001.tif (Table S1, 10.3 MB)
   - https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s002.tif (Table S2, 6.2 MB)
   (PMC serves these to browsers; CLI fetch is blocked — hence hand-download.)
2. Part I (configuration/anatomy, for the homology mapping):
   https://pmc.ncbi.nlm.nih.gov/articles/PMC7495296/
3. AT DOWNLOAD TIME: open https://doi.org/10.1111/joa.13314 and
   https://doi.org/10.1111/joa.13222 — pin the reuse license the Wiley page states
   into the batch receipt (expect CC BY-NC or similar from the Anatomical Society
   era; unconfirmed from this environment). If the license is non-commercial, the
   batch rides the SAME tension the infant bones ride — recorded, never waived
   silently.

**Priority 2 — the one email (human door, highest leverage):**
- To: Wiseman AL / Vereecke EE (KU Leuven) — ask: (a) is a FORELIMB companion to
  the Guimaraes 2026 hindlimb architecture dataset available or in preparation
  (ideally incl. specimen "127", the 8-kg adult male M. mulatta)? (b) may the
  per-muscle forelimb architecture values be shared/deposited CC BY? One message;
  the hindlimb batch's existence proves the format.

**Priority 3 — Cheng & Scott 2000 (institutional access; the model's own parent):**
- https://doi.org/10.1002/(SICI)1097-4687(200009)245:3<206::AID-JMOR3>3.0.CO;2-U
  (J Morphol 245(3):206-224) — transcribe Tables: 21 muscles × (mass, L0, LsT,
  PCSA, pennation) × 9 specimens (6 mulatta + 3 fascicularis) + the segment
  inertial tables. Optional companion: Part II (10.1002/jmor.1092, fiber types).

**Priority 4 (open, no door needed):**
- Saito 2021 Table 2 (CC BY): https://pmc.ncbi.nlm.nih.gov/articles/PMC8693514/
- Casteleyn 2024 hand (CC BY): https://doi.org/10.3390/anatomia3030013
- Casteleyn 2023 thoracic limb (CC BY): https://doi.org/10.3390/vetsci10020164

---

## 6. COMPATIBILITY NOTE — the parametric-muscle lane (the arm-frame transform gap)

The architecture numbers do not float free; they must ride the SAME bridge the
paths already ride:

1. **Frame gap.** The 39 muscle paths live in the arm model's OpenSim frame (7 VTP
   bones, 7 coordinates, 30 wrap surfaces). The parametric lane's muscle PATHS are
   already bridged by `tools/science_funnel/validation/muscle_paths_20260918/
   muscle_path_geometry.json` (schema `chimera.muscle_path_geometry.v1`; worst
   |r_geo − r_fd| = 4.3e-10 m over 39×7×2 poses — the arm membrane HELD) and bound
   to the creature through the body-binding intake. **Architecture numbers (mass,
   PCSA, FL, pennation) must attach per muscle NAME in the same frame, transform
   with the same body binding — never re-derived in creature coordinates.**
2. **Name gap.** Vanhoof/Saito/Cheng names (and any Guimaraes-forelimb future
   batch) need a homology table onto the 39 model names — the Guimaraes S2 docx is
   the established pattern. Watch the known synonyms: ext_digiti (minimi) vs
   model's `ext_digiti`; dorsoepitrochlearis exists only in the monkey papers.
3. **Stage gap (L1).** Vanhoof's 7 specimens and Cheng & Scott's animals are
   ADULT; Saito/Oishi's specimen is an adult ~10 kg M. fuscata. These numbers
   belong to the ADULT creature line. Attaching adult forelimb architecture to the
   infant creature is the adult-arms-on-a-baby case — L1 REFUSES it, and the gate
   classifies, not excuses. (Cheng & Scott's body-mass regressions are the legal
   instrument if a stage-consistent interpolation is ever justified — that is a
   derivation to be pre-registered, not a scale slider.)
4. **Species gap (L3).** Any M. fuscata numbers (Saito/Oishi/Oku-side) ride as
   DECLARED within-genus substitutions on the record, never merged into mulatta
   claims.
5. **Volume law.** Envelope geometry from muscle mass needs a density constant
   (literature standard ≈ 1.06 g/cm³) — that constant needs its own
   admission-grade citation (source + sha + license) BEFORE first use; this memo
   flags it, it does not admit it.
6. **Force law.** Everything in §2's PROVISIONAL classes keeps
   `force_runtime_ready: false` until a measured source lands; the σ value used,
   its citation, and the sub-class tag go on every derived record.

---

## 7. SOURCES

- Cheng EJ, Scott SH (2000). Morphometry of Macaca mulatta forelimb. I. Shoulder
  and elbow muscles and segment inertial parameters. J Morphol 245(3):206-224.
  PMID 10972970, DOI 10.1002/1097-4687(200009)245:3<206::AID-JMOR3>3.0.CO;2-U
- Singh K, Melis EH, Richmond FJR, Scott SH (2002). Morphometry of Macaca mulatta
  forelimb. II. Fiber-type composition. J Morphol 251(3):323-332. DOI
  10.1002/jmor.1092
- Graham KM, Scott SH (2003). Morphometry of Macaca mulatta forelimb. III. Moment
  arm. J Morphol 255(3):301-314. DOI 10.1002/jmor.10064
- Vanhoof MJM, van Leeuwen T, Vereecke EE (2020). The forearm and hand musculature
  of semi-terrestrial rhesus macaques and arboreal gibbons. Part I. J Anat 237(4).
  DOI 10.1111/joa.13222, PMC7495296
- Vanhoof MJM, van Leeuwen T, Galletta L, Vereecke EE (2021). … Part II.
  Quantitative analysis. J Anat 238(2). DOI 10.1111/joa.13314, PMC7812139
  (supplementary tables JOA-238-321-s001.tif, JOA-238-321-s002.tif)
- Chan SS, Moran DW (2006). Computational model of a primate arm. J Neural Eng
  3(4):327-337. DOI 10.1088/1741-2560/3/4/010
- Chowdhury RH, Glaser JI, Miller LE (2020). Area 2 of primary somatosensory
  cortex encodes kinematics of the whole arm. eLife 9:e48198, PMC6977965 (CC BY)
- Oishi M, Ogihara N, Endo H, Ichihara N (2012). Muscle dimensions in the Japanese
  macaque hand. Primates 53. DOI 10.1007/s10329-012-0309-3
- Saito T et al. (2021). Musculoskeletal Modeling and Inverse Dynamic Analysis of
  Precision Grip in the Japanese Macaque. Front Syst Neurosci 15:774596,
  PMC8693514 (CC BY)
- Taitano RI, Yakovenko S, Gritsenko V (2024). Muscle anatomy is reflected in the
  spatial organization of the spinal motoneuron pools. Commun Biol 7, PMC10789783
  (CC BY 4.0); data: https://doi.org/10.6084/m9.figshare.24291232.v2
- Casteleyn C et al. (2024). Hand Musculature of the Rhesus Monkey. Anatomia 3(3).
  DOI 10.3390/anatomia3030013 (CC BY); Casteleyn C et al. (2023). Topographical
  Anatomy of the Rhesus Monkey, Part I: Thoracic Limb. Vet Sci 10(2):164. DOI
  10.3390/vetsci10020164 (CC BY)
- Carlson KJ (2006). Muscle architecture of the common chimpanzee. Primates 47.
  DOI 10.1007/s10329-005-0166-4; Myatt JP et al. (2012). J Anat 220. DOI
  10.1111/j.1469-7580.2011.01443.x; Leischner CL, …, Hartstone-Rose A (2018).
  Anat Rec 301(3):484-495. DOI 10.1002/ar.23747; Deane AS et al. (2024). Anat Rec;
  Bollmann van Beesel J, Melillo S, Vereecke EE (2025). J Anat. DOI
  10.1111/joa.14199
- Guimarães E, Vereecke E, Wiseman AL (2026). Functional Differences in Muscle
  Architecture Across the Pelvis and Hind Limb of Primates. AJPA, PMC13425262
  (admitted batch `guimaraes_arch`, CC BY 4.0; fulltext XML in-repo — the
  "Van Beesel et al. 2025" specimen note)
- Spector SA et al. (1980) cat soleus specific tension, as applied by Saito 2021;
  in-repo σ law: `docs/research/muscle_physiology_reference.md`
- In-repo (this branch unless noted): `tools/science_funnel/data/macaque_arm/`
  (osim + receipt), `tools/science_funnel/macaque_anatomy.py`,
  `tools/science_funnel/validation/muscle_paths_20260918/` (lane branch),
  `docs/research/20260920_adult_and_muscle_data_options.md` (the pattern memo),
  Guimaraes batch on `origin/agent/skeleton-movie-20260919`
- API sweeps (2026-09-21, this lane, queries in §3.8): api.figshare.com/v2,
  zenodo.org/api, eutils.ncbi.nlm.nih.gov, api.crossref.org,
  pmc.ncbi.nlm.nih.gov idconv/utils
