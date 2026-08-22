# Koala (*Phascolarctos cinereus*) skeletal anatomy — research report for rigging

**Scope:** read-only web research; no code written. Measurements are cited with URLs. Values that are interpolated or estimated are flagged.

---

## 1. Proportion table

| Measurement | Value | Ratio / index | Source |
|---|---|---|---|
| Humerus length (adult mean) | **114.3 mm** (95% CI 107.3–121.3) | — | Hawkins et al. 2022, *Morphometric description of the koala humerus* ([PMC9613986](https://pmc.ncbi.nlm.nih.gov/articles/PMC9613986/)) |
| Radius length (single specimen) | **117.2 mm** | radius / humerus = **1.11** | Black et al. 2012, Table S1 citing Finch & Freedman 1988 ([PLOS ONE supp.](https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0048213.s004)) |
| Femur length (single specimen) | **128.6 mm** | — | Black et al. 2012, Table S1 |
| Tibia length (single specimen) | **101.6 mm** | tibia / femur = **0.79** | Black et al. 2012, Table S1 |
| Ulna length | **≈123 mm** (estimated, see below) | ulna / radius ≈ **1.05** | Estimated from Black et al. 2012 Fig. 4 koala radius/ulna image ([figure](https://journals.plos.org/plosone/article/figure/image?download&size=original&id=10.1371/journal.pone.0048213.g004)) |
| Vertebral column length (C1–last lumbar) | **346.6 mm** | — | Black et al. 2012, Table S1 |
| Forelimb index (humerus+radius / VC) | **64.3** | — | Black et al. 2012, Table 1 |
| Hindlimb index (femur+tibia / VC) | **66.4** | — | Black et al. 2012, Table 1 |
| Intermembral index ((humerus+radius)/(femur+tibia) ×100) | **96.8** | forelimb ≈ 97% of hindlimb length | Black et al. 2012, Table 1 |

### Scaling note
The Finch & Freedman specimen is a single individual and its humerus (105.7 mm) is smaller than the Hawkins 2022 mean (114.3 mm). To apply Hawkins’ more representative adult scale while preserving Finch’s proportions, multiply the Finch bone lengths by 114.3/105.7 ≈ **1.08**:

| Bone | Scaled to Hawkins humerus mean |
|---|---|
| Radius | ≈126.7 mm |
| Femur | ≈139.0 mm |
| Tibia | ≈109.8 mm |
| Ulna (estimated) | ≈133.0 mm |

The **intermembral index stays 96.8** regardless of absolute scale; the forelimb remains just slightly shorter than the hindlimb.

### Critical take-aways for rigging
- **Forelimb and hindlimb are nearly equal in length** (IMI ≈ 97), confirming the “front and hind limbs are nearly equal in length” statement from AKF ([source](https://savethekoala.com/about-koalas/physical-characteristics-koala/)).
- The **radius is longer than the humerus** (≈1.11×), a classic arboreal adaptation for reaching and grasping.
- The **tibia is markedly shorter than the femur** (≈0.79×), unlike cursorial mammals.

### Derived rigging ratios (used by `ChimeraEngine/native/stickfigure_quad.py` `LEG_MID_FRAC`)
The skeleton's leg column runs foot-joint → shoulder/hip (paw included in the column).
Mid-joint fraction from the FOOT up the column:
- **front (elbow):** radius / (humerus + radius) = 126.7 / 241.0 ≈ **0.526**
- **back (knee):** tibia / (femur + tibia) = 109.8 / 248.8 ≈ **0.441**

---

## 2. Spine and girdles

### Vertebral formula
- Most common koala formula: **C7, T11, L7, S3** ([PMC13255766](https://pmc.ncbi.nlm.nih.gov/articles/PMC13255766/)).
- Variation exists: 25/26 CT-scanned koalas had C7, T11, L8; sacral count varied between 3 and 4 ([PMC13255766](https://pmc.ncbi.nlm.nih.gov/articles/PMC13255766/)).
- Tail is vestigial (reduced caudal vertebrae, hidden by fur).

### Scapula, pelvis, ribcage
- **Trunk posture is orthograde** (upright relative to pronograde quadrupeds) ([Grand & Barboza 2001](https://repository.si.edu/bitstream/handle/10088/337/Grand2001.pdf)).
- **Scapula**: vertebral border lies parallel to the upper thoracic spines; glenoid cavity points **laterad and craniad**; scapular spine is at ~90° to the vertebral border. This positions the forelimb for abduction/reaching rather than parasagittal cursorial striding.
- **Pelvis**: standard marsupial pelvis; no specific published length measurement was found for koala.
- **Ribcage**: standard mammalian thoracic cage of 11 thoracic vertebrae/ribs. Grand & Barboza note a relatively large head (6.1 ± 1.6% of total body mass) and a broad, rounded thorax/abdomen. Exact anterior/posterior ribcage limits as a fraction of trunk length are not published; riggers should place the ribcage over **T1–T11**, with the diaphragm/lung region roughly T3–T9.

### Caution
No published koala-specific scapula length, pelvis length, or ribcage-in-trunk fraction was located. If exact fractions are required, they must be measured from a museum CT model (e.g., the Sketchfab Evans EvoMorph Lab koala long-bones model, specimens SAMM21451 / NMVC22285).

---

## 3. Standing posture summary

Based on Grand & Barboza 2001 ([PDF](https://repository.si.edu/bitstream/handle/10088/337/Grand2001.pdf)) and Richards et al. 2021/2023:

- **Trunk**: orthograde; spine relatively vertical when sitting or standing quadrupedally.
- **Head**: carried forward-flexed on the neck; large, heavy skull (≈6% body mass).
- **Forelimb**:
  - Shoulders abducted (directed laterally/cranially), not tucked under the body like a cursor.
  - Glenoid faces laterad and craniad.
  - Elbow highly mobile; olecranon short, allowing full extension and reaching.
  - **Forearm supinated** in resting/climbing posture — palms face **medially**.
  - Wrist highly mobile, digits I–II oppose III–V (schizodactyly/forcipate hand).
- **Hindlimb**:
  - Hip mobile; femur can abduct/externally rotate for branch-hugging.
  - Knee flexed in climbing; on the ground the gait is bounding.
  - Pes inverted; hallux semi-opposable; digits II–III syndactylous.
- **Feet**: soles face medially (inverted), consistent with gripping vertical trunks.

This is **not** a cursorial “legs-under-body” posture. It is an arboreal quadruped posture with abducted, mobile limbs and grasping extremities.

---

## 4. Locomotion summary

Ground and arboreal data are from Gaschk et al. 2019 (*Journal of Experimental Biology* 222:jeb207506, [PubMed](https://pubmed.ncbi.nlm.nih.gov/31848216/); press summary [Nature World News](https://www.natureworldnews.com/articles/42977/20191217/koalas-climb-like-apes-but-bound-on-the-ground-like-marsupials.htm)).

| Context | Gait | Speed | Notes |
|---|---|---|---|
| **Ground** | Bounding (marsupial-like, hind feet synchronized) | top **2.78 m/s** (≈10 km/h), mean **1.20 m/s** | Speed increased by equal changes in stride length and stride frequency. |
| **Arboreal (narrow beam)** | Diagonally coupled / diagonal-sequence gait | top **0.7 m/s** | Diagonally opposed hand+foot (e.g., right hand + left foot) stay in contact for stability — a primate-like strategy. |
| **Leaping / suspensory** | — | — | Observed leaps >1 m between branches; can hang and move using forelimbs only. |

Additional behavioral context from Queensland KSD Guideline ([PDF](https://www.planning.qld.gov.au/__data/assets/pdf_file/0018/82170/Koala-Sensitive-Design-Guideline.pdf)):
- Adult can extend forelimbs **>90 cm** from the ground.
- Can jump **up to 1.2 m** vertically from the ground.
- Predominantly nocturnal; change trees by descending and walking across ground.

### Biomechanics
- Muscle mass is evenly split between fore- and hindlimbs (≈32–33% of total muscle mass each) ([Grand & Barboza 2001](https://repository.si.edu/bitstream/handle/10088/337/Grand2001.pdf)).
- This matches the near-equal limb lengths: koalas are not specialized for speed but for controlled, powerful climbing and short-distance ground movement.

---

## 5. Body measurements for mesh scaling

| Measurement | Value | Source |
|---|---|---|
| Head-body length | **60–85 cm** (600–850 mm) | San Diego Zoo Global fact sheet ([LibGuides](https://ielc.libguides.com/sdzg/factsheets/koala/characteristics)) |
| Head-body length (southern males) | avg **78 cm** | ADW / MacDonald 1984 ([animaldiversity.org](https://animaldiversity.org/accounts/Phascolarctos_cinereus/)) |
| Head-body length (southern females) | avg **72 cm** | ADW / MacDonald 1984 |
| Shoulder height | **38–58 cm** | Dimensions.com ([link](https://www.dimensions.com/element/koala)) |
| Adult mass | **4–15 kg**, avg ~11 kg | AKF / San Diego Zoo Global ([AKF](https://savethekoala.com/about-koalas/physical-characteristics-koala/), [LibGuides](https://ielc.libguides.com/sdzg/factsheets/koala/characteristics)) |
| Adult mass (cadaveric mean) | **6.0 ± 0.9 kg** (n=10) | Grand & Barboza 2001 ([PDF](https://repository.si.edu/bitstream/handle/10088/337/Grand2001.pdf)) |
| Head mass | **6.1 ± 1.6% of body mass** | Grand & Barboza 2001 |
| Forelimb reach | >90 cm from ground | Queensland Koala-Sensitive Design Guideline ([PDF](https://www.planning.qld.gov.au/__data/assets/pdf_file/0018/82170/Koala-Sensitive-Design-Guideline.pdf)) |
| Tail | Vestigial, hidden by fur | Multiple sources |

### Mesh check suggestion
For a standing adult koala of head-body length 75 cm, use the Finch & Freedman/Hawkins-scaled limb lengths:
- Forelimb total ≈ 24 cm (humerus ~11.4 cm + radius ~12.7 cm)
- Hindlimb total ≈ 24.9 cm (femur ~13.9 cm + tibia ~11.0 cm)

These are ~32–33% of head-body length per limb, which fits the compact, stocky-yet-long-limbed koala silhouette.

---

## 6. Best primary sources

1. **Hawkins, B., Beatty, J., Nagy, L., & Johnson, K. (2022).** “Morphometric description of the koala humerus using micro-computed tomography.” *BMC Veterinary Research* 18, 429. [PMC free article](https://pmc.ncbi.nlm.nih.gov/articles/PMC9613986/) — only peer-reviewed koala long-bone CT morphometry; gives mean adult humerus length.
2. **Black, K. H., Camens, A. B., Archer, M., & Hand, S. J. (2012).** “Herds Overhead: *Nimbadon lavarackorum* (Diprotodontidae), heavyweight marsupial herbivores in the Miocene forests of Australia.” *PLOS ONE* 7(11): e48213. [Article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0048213) — supplementary Table S1 reproduces Finch & Freedman 1988 koala radius/femur/tibia/VC lengths and IMI.
3. **Finch, M. E., & Freedman, L. (1988).** “Functional morphology of the limbs of *Thylacoleo carnifex* Owen (Thylacoleonidae, Marsupialia).” *Australian Journal of Zoology* 36: 251–272. [DOI](https://doi.org/10.1071/ZO9880251) — original source of the koala limb measurements used in Black et al.; paywalled, but reproduced in Black et al. supplementary data.
4. **Grand, T. I., & Barboza, P. S. (2001).** “Anatomy and development of the koala, *Phascolarctos cinereus*: an evolutionary perspective on the superfamily Vombatoidea.” *Anatomy and Embryology* 203: 211–223. [DOI](https://doi.org/10.1007/s004290000153); [Smithsonian PDF](https://repository.si.edu/bitstream/handle/10088/337/Grand2001.pdf) — the classic reference for koala posture, muscle distribution, and comparative anatomy with wombats/sloths.
5. **Gaschk, J. L., Frère, C. H., & Clemente, C. J. (2019).** “Quantifying koala locomotion strategies: implications for the evolution of arborealism in marsupials.” *Journal of Experimental Biology* 222: jeb207506. [PubMed](https://pubmed.ncbi.nlm.nih.gov/31848216/) — ground/arboreal gait speeds and primate-like diagonal gait.
6. **Richards, H. L., Adams, J. W., & Evans, A. R. (2021).** “Low elbow mobility indicates unique forelimb posture and function in a giant extinct marsupial.” *Journal of Anatomy* 238: 1092–1113. [PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC8128769/) — comparative elbow ROM data including koala, confirms high mobility.
7. **Koala kyphoscoliosis imaging paper (2025).** [PMC13255766](https://pmc.ncbi.nlm.nih.gov/articles/PMC13255766/) — vertebral formula and regional spine anatomy.
8. **Queensland Government (2022).** *Koala-Sensitive Design Guideline*. [PDF](https://www.planning.qld.gov.au/__data/assets/pdf_file/0018/82170/Koala-Sensitive-Design-Guideline.pdf) — reach and jump numbers.

---

## 7. Honest gaps

- **Published koala ulna length** was not found; the value above is an image-based estimate derived from the relative pixel lengths of radius and ulna in Black et al. 2012 Figure 4.
- **Published koala fibula, scapula, and pelvis lengths** were not located. If a museum CT scan is needed, the Evans EvoMorph Lab Sketchfab model lists koala specimens **SAMM21451** (humerus/femur/tibia) and **NMVC22285** (fibula/radius/ulna) ([Sketchfab](https://sketchfab.com/3d-models/marsupial-long-bones-koala-vs-wombat-c871507d8e0049c782ad4be4f0417fb5)).
- **Exact ribcage-in-trunk fraction** and **scapula/pelvis position as % of trunk length** are not published; use the vertebral formula and qualitative descriptions above as a starting point.

If exact numbers for ulna/fibula/scapula/pelvis become critical, the next step is to contact Museums Victoria (NMVC22285) or the South Australian Museum (SAMM21451) for the 3D scan measurements, or measure the publicly available Sketchfab/CT models directly.
