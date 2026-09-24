# R1 — SPECIES PROVENANCE RECEIPT (verbatim quotes + file-identity evidence)

## 1. The XML itself (baseline_snapshot/source_xml/chimanoid.xml, sha256 675e00d0…)

- Line 2: `<mujoco model="fullbody">` — the model's only declared name. **No species, taxon, or animal name is declared anywhere in the file** (exhaustive case-insensitive grep for species/monkey|macaque|macaca|rhesus|chimp|pan |ape|baboon|primate|human → zero active-line hits).
- The only animal word in the entire file is a stray commented material note "above base below ostrich" (asset section) — a leftover from an ostrich model, not a species declaration (the FreeMusco repo separately contains a real ostrich model under Data/Muscle/Animal/ostrich/).
- Anatomy is named with standard HUMAN nomenclature: bodies `humerus/ulna/radius/hand_r`, muscles `TRIlong/TRIlat/TRImed, ANC, BRA, BIClong/BICshort, BRD, ECRL/ECRB/ECU, FCR/FCU, PT`; carpal set `pisiform, lunate, scaphoid, triquetrum, hamate, capitate, trapezoid, trapezium`.
- Scale (active inertial elements only, n = 18): total mass **56.88 kg**; shoulder→elbow 348.7 mm; elbow→hand 305.8 mm. Human-scale, NOT macaque-scale (adult rhesus ≈ 6–12 kg).

**Determination from the file: SPECIES UNDECLARED.** That is itself a result.

## 2. Provenance — the FreeMusco project (primary provenance sources)

Repo: github.com/palkan21/FreeMusco (Hanyang Univ., cgrhyu lab). The git tree contains **`Data/Muscle/Fullbody/chimanoid.xml`** alongside `Data/Muscle/Fullbody/fullbody.xml` and an `Animal/ostrich/` model family.

**File identity (our baseline = that repo's chimanoid.xml family):** the repo file's right-side bodies, fetched raw:
- `ulna`   `pos="  0.0061  -0.34845  -0.0123"`  — byte-identical to baseline L593
- `radius` `pos="  0.0004 -0.011503 0.019999"`  — byte-identical to baseline L608
- `hand_r` `pos="   0.018   -0.2904    0.025"`  — byte-identical to baseline L629
- model attribute `model="fullbody"` — identical to baseline L2; ulna/radius inertial `mass="0.729"` (commented alternative 0.6075) — identical to baseline L596/L610–611.
- Structure matches DERIVATION §2's measured counts: paper says the character has **120 muscles**; baseline measures 120 spatial tendons / 121 actuators / 19 bodies.

**The authors' own description (arXiv:2511.14205, Kim & Lee 2025, SIGGRAPH Asia 2025) — verbatim:**
> "Chimanoid: A fictional 120-muscle character created by modifying the Humanoid model, with changes such as elongated arms and shortened legs." (§3)

> "A key result highlighting the morphology-adaptive nature of our framework is observed in Chimanoid—a humanoid variant with elongated arms (1.2×) and shortened legs (0.7×), resembling a chimpanzee-like morphology." (§4.2)

> "The Chimanoid is a fictional character designed by modifying the Humanoid model to exhibit chimpanzee-like proportions." (Appendix B)

> Abstract: "The framework generalizes across human, non-human, and synthetic morphologies, where distinct energy-efficient strategies naturally appear—for example, quadrupedal gaits in Chimanoid versus bipedal gaits in Humanoid."

## 3. Determination (with confidence)

1. The source models **NO real species** — the XML declares none, and the authors state it is a **fictional character derived from the HUMAN Humanoid model by scaling arms ×1.2 and legs ×0.7** ("chimpanzee-like proportions" as a look, not as anatomy). Confidence: **HIGH** (file-internal evidence + authors' own Appendix B statement + repo file match on 3 pos strings + masses + muscle count).
2. Therefore **no primary species-specific osteometric evidence can exist for "the modeled species"** — there is no specimen. The applicable primary-anatomy lane is the **HUMAN base anatomy** (the direct provenance); Pan (name-target) and Macaca (campaign-target family, species itself undeclared in the baseline inputs `monkey_birth.bin`/`monkey_joints.bin`) are context taxa at stated taxonomic distance (Human↔Pan: Homininae, ~7–13 Ma; Human↔Macaca: Cercopithecoidea↔Hominoidea, ~25–30 Ma).
3. **C1 §1.2's passing claim "a full-size macaque model" is REFUTED by provenance and by the file's own scale** (57 kg fictional humanoid vs a 6–12 kg macaque). C1's units point ("meters, SI") stands; only the species aside is wrong.
4. Internal consistency check (model arithmetic, no citation needed): elbow→hand / shoulder→elbow = 305.79/348.72 = 0.877 — a human-like ~0.78 base ratio inflated by the paper's declared ×1.2 arm elongation ⇒ consistent with the provenance story, inconsistent with any measured great ape or macaque as the underlying anatomy.
