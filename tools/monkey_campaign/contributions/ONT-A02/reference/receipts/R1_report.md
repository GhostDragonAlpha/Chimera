# R1 — RADIOULNAR EVIDENCE: what the source's 7.5 % measures, primary anatomical comparison, and the verdict on the radius re-anchoring

**Agent:** R1 evidence agent (wave 4) · **Date:** 2026-09-24
**Scope honored:** no candidate chosen; no fit session; no supersession executed; no moment arms or tendon utility computed; baseline READ-ONLY throughout (integrity receipt §6, clean at start and end); all writes confined to `audits/R1_radioulnar_evidence/`; WebSearch/web fetches were the primary-tool lane.
**Inputs:** `baseline_snapshot/source_xml/chimanoid.xml` (sha `675e00d0…`, read verbatim at L593/608/629/596/611) · `baseline_snapshot/code/DERIVATION.md` (§1 FreeMusco provenance, §2 conventions) · `baseline_snapshot/MANIFEST.json` + session_reports (campaign = "grasp qualification (monkey)") · wave receipts `audits/C1_ulna_evidence/report.md`, `audits/C3_independent_challenge/report.md` (read, not modified) · external primary sources via NCBI eutils / arXiv / GitHub raw (citations + arithmetic in `receipts/`).

---

## 0. ACCEPTANCE-CRITERION VERDICTS (the six)

| # | criterion | verdict |
|---|---|---|
| 1 | Species determination stated with confidence | **PASS** — UNDECLARED in the XML; provenance = FreeMusco's **fictional** "Chimanoid" (modified Humanoid, arms ×1.2, legs ×0.7); determination and confidence in §2. C1's passing "full-size macaque model" aside is refuted by provenance and by the file's own 56.88 kg mass. |
| 2 | ≥ 2 primary sources, or explicit inapplicability finding per candidate | **PASS** — 3 APPLICABLE primary sources (London 1981 n=8; Brownhill et al. 2009 n=12; Hollister et al. 1994, fresh specimens — §4) + 5 INAPPLICABILITY findings, each with the reason and the search trail (`receipts/citations.md` §B, `receipts/search_trail.md`). |
| 3 | Like-for-like transformation table with uncertainty | **PASS** — §5: every published figure and the authored 7.5 % expressed in ONE definition (D_axial / D_total), with uncertainty bands; quantities that cannot be transformed are recorded INAPPLICABLE, never forced. |
| 4 | Verdict on re-anchoring support, with numbers | **REFUTED as an anatomical claim** — primary evidence places the radial head center ON the elbow flexion axis and AT the proximal terminus of the forearm rotation axis (≈ 0 % of forearm length distal to the hinge, ±~1 %), far outside the frozen 4–12 % band (margin ≥ 3.0 points). The re-anchoring's true basis is kinematic (it preserves the source author's joint-frame offset exactly and mechanically; 7.546 % → 7.901 %, drift +0.356 pts fully explained, §5.3) — it has **no primary-anatomical support** as a radial-head placement, and the anatomical evidence independently supports C1's kinematic-fragment verdict. Numbers in §6. |
| 5 | Exact statement of what the 7.5 % measures | **PASS** — §3: numerator = |(0.0004, −0.011503, 0.019999)| m = 23.0746 mm, the ulna-frame position of the RADIUS BODY ORIGIN (a kinematic joint-frame offset: 14.324 mm distal + 18.088 mm lateral + 0.301 mm dorsal, 51.63° oblique); denominator = |elbow→hand_r origin| straight-line = 305.7922 mm, the authored elbow→wrist chain distance; quotient = 7.5459 % — computed in the AUTHORED REST POSE (all quats identity, joints at ref 0); it is not motion-invariant and is not a bone-landmark distance. |
| 6 | Baseline integrity | **PASS** — `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` → **empty**, run after the brief copy and re-run after all work (§6). No git writes. |

## 0.1 PREREGISTRATION VERDICT (frozen in `brief.md` before any search or evaluation)

| item | outcome | numbers |
|---|---|---|
| PREDICTION: "primary osteometric data exists for macaque (or the declared species) forearm proportions" | **PARTIALLY FALSIFIED** | For the DECLARED species: none can exist (the species is fictional — §2), so the prediction was misaimed at authoring time. For MACAQUE: primary forelimb morphometry EXISTS (Cheng & Scott 2000, n=6 *M. mulatta* + 3 *M. fascicularis*; Graham & Scott 2003) but measures muscle/inertial/moment-arm quantities — **no transformable radial-head position** ⇒ INAPPLICABLE (citations.md I1–I2). |
| PREDICTION: "the authored 7.5 % falls inside the published range" | **FALSIFIED** | The only applicable primary measurements place the radial head at ≈ 0 % (±~1 %) of forearm length distal to the humeroulnar hinge (§4, §5); the authored D_axial is 4.68 % (axial part) / 7.55 % (full oblique offset). The authored fraction is outside the published band. |
| FALSIFIER: "primary data placing the radial head outside 4–12 % of forearm length refutes the authored geometry's plausibility" | **FIRED — reported, not tuned** | Measured primary fractions ≈ 0–1 % (three independent sources, three specimen sets). Outside the frozen band by ≥ 3.0 points. The honest reading (§6.2): the fired falsifier refutes reading the authored 7.5 % as radial-head ANATOMY; it does not refute the re-anchoring as kinematic bookkeeping — that distinction is the report's core finding. |

---

## 1. WHAT THIS AUDIT WAS ASKED (binding architect decision, 2026-09-24)

"find primary anatomical evidence relevant to the modeled species and measurement definition. State exactly what the reported source 7.5 % measures. Compare like quantities, record uncertainty, and explain whether it supports the proposed radius re-anchoring. A citation mentioning a similar percentage is insufficient." C3 (§8) had already identified this exact datum as "the only ulna-length evidence that is not circular" for the U-STR vs U-ANA separation and had assumed "macaque" as the taxon. The species finding below is why that assumption had to be tested before any citation could count.

## 2. SPECIES DETERMINATION (criterion 1) — HIGH CONFIDENCE

**The source declares NO species.** `<mujoco model="fullbody">` is the only declared name; an exhaustive grep finds no species/taxon words in any active line (the sole animal word in the file is a stray commented "ostrich" material note — an import leftover from FreeMusco's ostrich model).

**Provenance (primary provenance sources, verbatim quotes in `receipts/provenance_quotes.md`):**
- DERIVATION.md §1: the source is "the FreeMusco `chimanoid.xml` at revision `e021d5d9…`".
- The FreeMusco repo (github.com/palkan21/FreeMusco) contains `Data/Muscle/Fullbody/chimanoid.xml`, and the raw file **matches our baseline byte-for-byte on the decisive strings**: ulna `pos="0.0061 -0.34845 -0.0123"` (L593), radius `pos="0.0004 -0.011503 0.019999"` (L608), hand_r `pos="0.018 -0.2904 0.025"` (L629), `model="fullbody"`, ulna/radius `mass="0.729"`, and the 120-muscle count.
- The authors (Kim & Lee, arXiv:2511.14205, SIGGRAPH Asia 2025) state: **"Chimanoid: A fictional 120-muscle character created by modifying the Humanoid model, with changes such as elongated arms and shortened legs"** (§3); **"a humanoid variant with elongated arms (1.2×) and shortened legs (0.7×), resembling a chimpanzee-like morphology"** (§4.2); **"The Chimanoid is a fictional character designed by modifying the Humanoid model to exhibit chimpanzee-like proportions"** (Appendix B).

**Determination:** the modeled species is **no real species** — it is a fictional character derived from a HUMAN musculoskeletal model by limb-length rescaling. Confidence **HIGH** (file-internal + authors' own statement + repo file match). Consequences:
1. **No primary species-specific osteometric evidence can exist for "the modeled species"** — there is no specimen. The applicable primary-anatomy lane is the **human base anatomy** (direct provenance); Pan (name) and Macaca (campaign target family; the target's own species is undeclared in the baseline inputs) are context taxa — Human↔Pan ≈ Homininae (~7–13 Ma), Human↔Macaca ≈ Cercopithecoidea/Hominoidea (~25–30 Ma).
2. **C1 §1.2's passing "a full-size macaque model" is wrong** as a species claim: 56.88 kg total mass and a 348.7 mm upper arm are macaque-inconsistent, and the authors call it fictional. C1's units finding (meters, SI) is unaffected.
3. Model-internal consistency check: elbow→hand / shoulder→elbow = 305.79/348.72 = 0.877 ≈ human base (~0.78) × the paper's declared 1.2 arm factor — consistent with provenance, inconsistent with any measured ape or macaque as the underlying skeleton.

## 3. WHAT THE 7.5 % MEASURES — EXACTLY (criterion 5)

- **Numerator:** |(0.0004, −0.011503, 0.019999)| m = **23.0746 mm** — the `radius` body's frame origin in the `ulna` body's frame (XML L608). Per DERIVATION §2 ("every body origin = its proximal joint") this is a **kinematic joint-frame offset**: the distance the source author placed the radius BODY ORIGIN from the ulna body origin (the elbow hinge, `elbow_flexion` at the ulna origin). Decomposed in C1's anatomical frame (reproduced here to 3 decimals): **14.324 mm distal + 18.088 mm lateral + 0.301 mm dorsal, oblique at 51.63° to the forearm axis.**
- **Denominator:** |elbow→hand_r origin| straight-line = **305.7922 mm** (authored rest pose; verified from the additive chain).
- **Quotient:** 23.0746/305.7922 = **7.5459 %** ("the 7.5 %"). Per-edge denominator variant (chain-sum 315.1040 mm): 7.3229 %.
- **Rest-pose caveat:** both numerator and denominator are authored REST-POSE quantities (all arm-chain quats `1 0 0 0`, joints at `ref=0`). The parent-child offset (numerator) is fixed by the tree; the elbow→hand distance (denominator) changes under elbow flexion. The 7.5 % is therefore a pose-specific authoring constant, not a motion-invariant anatomical index.
- **It is NOT a bone-landmark distance.** In particular it is NOT "where the radial head is": C1 independently proved the 2.31 cm axis is a kinematic fragment (sites reach 4.26× its length; the body's own CoM sits 5.22× along; the anatomical ulna/radius lengths are carried by the site distribution and the radius→hand edge). This audit's primary evidence (§4) confirms the same conclusion from outside the model.

## 4. PRIMARY EVIDENCE (criterion 2) — what the applicable primary literature measures

All applicable primary sources are HUMAN elbow/forearm kinematics — the correct lane, since the modeled character IS a modified human model (§2). Citations with specimen counts in `receipts/citations.md`; the Macaca/Pan lanes and every failed candidate are recorded there with inapplicability findings.

**S1 · London 1981 (JBJS Am 63:529–535; 8 elbows, true-lateral roentgenography):** flexion occurs about a **single axis through the centers of the arcs of the trochlear sulcus and the capitellar periphery**. The humeroulnar and humeroradial articular surfaces are coaxial; the radius, articulating with the capitellum and rotating about this axis, has its center AT the elbow joint.

**S2 · Brownhill et al. 2009 (J Biomech Eng 131:021005; 12 cadaveric specimens):** of five ways to define the ulnar flexion-extension axis, the anatomic technique that uses **the guiding ridge of the greater sigmoid notch (the humeroulnar surface) together with the radial head** most accurately replicates the elbow's screw displacement axis (p < 0.05). The radial head is a defining landmark OF the hinge axis — its center lies on the hinge.

**S3 · Hollister et al. 1994 (Clin Orthop 298:272–276; fresh anatomic specimens):** the forearm's rotation axis is constant and **runs from the center of the radial head to the center of the distal ulna**. The radial head center IS the proximal terminus of the forearm's longitudinal axis: anatomically, the forearm segment begins at the radial head. There is no positive fraction of forearm length between the elbow joint and the radial head along that axis.

**Convergent finding (three sources, three specimen sets, three methods):** the radial head center is **coaxial with the humeroulnar hinge** (axial offset ≈ 0) and defines the proximal end of the forearm. The radial head's offset from the hinge is TRANSVERSE (the radius sits lateral), not distal.

**INAPPLICABLE sources (recorded, never forced):** Cheng & Scott 2000 and Graham & Scott 2003 (primary *Macaca* forelimb morphometry — muscle/inertial/moment-arm quantities, no radial-head position); Rose 1988 comparative anthropoid elbow (no transformable number extracted; paywalled; NOT cited as a "similar percentage"); the radial-tuberosity screening set (measures interosseous space/nerve zones); FreeMusco 2025 itself (provenance, not anatomy). Full findings: `receipts/citations.md` §B.

## 5. LIKE-FOR-LIKE TRANSFORMATION (criterion 3)

**Common definition D:** fraction = (distance from the humeroulnar elbow hinge to the radius's proximal anchor) / (elbow→wrist distance), rest pose. Two sub-forms: **D_axial** (offset projected on the forearm axis — the form in which the re-anchored target anchor is placed and the claim is worded: "sits X % of forearm length DISTAL to the elbow") and **D_total** (full 3D offset).

### 5.1 Transformation table

| row | quantity (definition used) | value | D_axial | D_total |
|---|---|---|---|---|
| SOURCE (authored) | \|ulna→radius offset\| vs elbow→hand straight-line | 23.0746 / 305.7922 mm | **4.684 %** (14.324 mm axial) | **7.546 %** ("the 7.5 %") |
| SOURCE (per-edge denominator) | same numerator / chain-sum 315.1040 mm | 23.0746/315.1040 | 4.546 % | 7.323 % |
| TARGET (re-anchored, U-STR) | elbow_R → derived point (authored ALONG elbow→wrist) vs \|elbow_R→wrist_R\| = 64.7449 mm | 5.1158 / 64.7449 mm | **7.901 %** | 7.901 % (collinear by authoring) |
| HUMAN primary (S1+S2+S3) | radial head CENTER vs humeroulnar hinge | ≈ 0 mm axial (coaxial) | **≈ 0 % ± ~1 %** | transverse-dominated; no primary mm number for the hinge-to-head center distance located ⇒ recorded unmeasured, NOT estimated for the verdict |
| Model-internal support (uncited, qualitative) | radius-frame biceps-tuberosity site (BIClong-P9, radius-local y=−0.0102) | 24.524 mm axial from elbow = 8.020 % | consistent with the proximal-forearm tuberosity band ⇒ the model's radius ANATOMY does not start at its body origin | — |

**Uncertainty:** source and target rows are exact authored floats (no measurement error — their uncertainty is SEMANTIC, i.e. what they mean, addressed in §6). Human rows: radial-head-center-on-axis is established at millimeter technique precision (S1 radiographic; S2 vs screw-displacement axis, p<0.05); 2 mm over a ~250 mm human forearm ≈ 0.8 % ⇒ band ≈ 0–1 %. The frozen falsifier band 4–12 % is cleared by ≥ 3.0 points.

### 5.2 Note on "straight-line vs per-edge" (requested by the brief)

The source fraction depends on the denominator definition: 7.546 % (straight-line 305.7922) vs 7.323 % (per-edge chain 315.1040) — the two offsets are not collinear (51.63° obliquity; C1's root finding). In the TARGET the re-anchored anchor is authored ON the elbow→wrist line, so per-edge and straight-line coincide (7.901 %). The campaign's "the re-anchoring preserves this fraction" is therefore exact in MECHANISM (the same authoring rule, scaled) but not numerically identical under either definition.

### 5.3 Why 7.546 % → 7.901 % and not 7.546 % (arithmetic receipt `receipts/arithmetic.txt`)

The target anchor distance scales the source offset by the RADIUS EDGE's scale (k_rad = 0.22170680, giving 5.1158 mm) while the target forearm scales by the elbow→wrist RATIO (64.7449/305.7922 = 0.211728). The two scale factors differ by exactly k_rad/ratio = 1.04713, and 7.5459 % × 1.04713 = **7.9015 %** — the target value, exactly. C3's mechanics re-derived independently: fitted span 64.7449 − 5.1158 = 59.6291 mm; s = 59.6291/292.0294 = **0.204189** ✓ (C3: 0.20418). Also recorded: the campaign brief's "chain-sum 315.14 mm" is a transcription slip for C1's receipt value 0.315104 m (315.104 mm) — immaterial to any fraction.

## 6. VERDICT (criterion 4): does the primary evidence support the re-anchoring?

### 6.1 The verdict sentence

**REFUTED as an anatomical claim.** The claim embedded in reading the re-anchoring as anatomy — "the radius's proximal anchor (the radial head) sits ~7.5–7.9 % of forearm length distal to the elbow joint" — is contradicted by all three applicable primary sources: the radial head center lies ON the elbow flexion axis (S1, S2) and is the proximal terminus of the forearm rotation axis (S3), i.e. **≈ 0 % (±~1 %) of forearm length distal to the humeroulnar hinge**, far outside the frozen 4–12 % plausibility band. The falsifier FIRED; the numbers are reported above, un-tuned.

### 6.2 What the refutation refutes — and what it does not

- **Refuted:** any claim that 7.5–7.9 % distal placement is the ANATOMICAL position of the radial head in the modeled species (or in its human base anatomy, or in Pan, or in Macaca — the humeroradial joint is at the elbow in all of them, and the primary evidence quantifies it for the base taxon). The authored 23.07 mm offset is a **kinematic joint-frame offset** (62 % lateral / 38 % distal in the anatomical frame), exactly as C1 concluded from source-internal evidence; this audit confirms it from outside the model. The model's own biceps-tuberosity site at 8.02 % of forearm from the elbow sits where the real tuberosity band is — corroborating that the model's radius ANATOMY is not anchored at its body origin.
- **Not refuted (outside this audit's lane):** the re-anchoring as a KINEMATIC act. C3 proved it is machine-forced under closure the moment the ulna edge is resolved, and this audit shows it preserves the source author's offset fraction to +0.356 points (drift fully explained, §5.3). What primary anatomy removes is any ANATOMICAL justification for that preserved fraction — it is convention inheritance, not anatomy. Any decision table row claiming "the 7.9 % target anchor matches primate anatomy" is false and should not be written; a row claiming "it matches the source authoring's kinematic convention (7.546 % → 7.901 %)" is true.
- **Anatomical guidance for a future authoring (stated, not chosen):** if the radius body origin were ever to be placed ANATOMICALLY, primary evidence places the radial head center at ≈ 0 % axial from the hinge, offset TRANSVERSELY (laterally) — i.e. the anatomically-motivated authoring differs from both the source's oblique 7.5 % and the re-anchored pure-axial 7.9 %.
- **Blocker status:** no blocker fires. An inapplicable-source blocker was the risk for the MACAQUE lane (recorded: primary morphometry exists but measures other quantities), but the applicable HUMAN lane exists because the provenance is a modified human model — the comparison is like-for-like on the base anatomy, and it produced a decisive refutation instead of silence. Had the species lane been forced to macaque, the report would have been a blocker; it is not.

### 6.3 Verdict table

| question | answer | numbers |
|---|---|---|
| What does the 7.5 % measure? | elbow-hinge → radius BODY-FRAME origin, authored rest pose (kinematic offset; 51.63° oblique) | 23.0746 mm / 305.7922 mm = 7.546 % (axial part 4.684 %) |
| Primary anatomical position of the radial anchor | ON the elbow axes (coaxial with the hinge; proximal terminus of the forearm axis) | ≈ 0 % ± ~1 % of forearm length, distal component (S1–S3) |
| Falsifier (frozen band 4–12 %) | **FIRED** | 0–1 % ∉ [4, 12] %; margin ≥ 3.0 pts |
| Does primary evidence support the re-anchoring as anatomy? | **No — refuted** | 7.901 % target vs ≈ 0–1 % primary |
| Does it support the re-anchoring as kinematics? | Preserves the source convention exactly (drift +0.356 pts, mechanism identified); support is mechanical (C3 closure), not anatomical | 7.546 % × 1.04713 = 7.901 %; s = 0.204189 |

## 7. RECEIPTS

| receipt | content |
|---|---|
| `brief.md` | the brief, copied verbatim as the first action; preregistration frozen before any search |
| `receipts/arithmetic.txt` | exact-float python 3.14 recomputation of every campaign number: 23.0746 mm / 292.0294 mm / 315.1040 mm / 305.7922 mm / 7.5459 % / 7.3229 % / 14.324+18.088+0.301 mm @ 51.63° / 5.1158 mm / 59.6291 mm / s = 0.20418868 / 7.9015 % / drift ×1.04713 / BIC site 8.020 % |
| `receipts/citations.md` | the citation list (3 APPLICABLE with specimen counts; 5 INAPPLICABLE findings) + the common definition D |
| `receipts/provenance_quotes.md` | verbatim Chimanoid quotes (arXiv:2511.14205 §3, §4.2, App. B), repo file-identity evidence, species determination with confidence, C1 correction |
| `receipts/search_trail.md` | every query including rate-limits, timeouts, zero-hits, paywalls; the explicit negative result |

## 8. BASELINE INTEGRITY (criterion 6)

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)
```
Run after the brief copy (first work action) and re-run after all work: **empty both times.** HEAD at receipt time: `5db981cb`. No git writes; no baseline writes; `PYTHONDONTWRITEBYTECODE=1`; all writes inside `audits/R1_radioulnar_evidence/`; no rendering; no utility quantities computed.

## 9. NULL / NEGATIVE RESULTS (preserved — they are results)

1. **The modeled species is fictional** — the campaign's "modeled species" premise (and C3 §8's "macaque" assumption) has no referent; the applicable lane is the human base anatomy, with Pan/Macaca as distant context. Any future evidence audit must name its taxon deliberately.
2. **No primary source in any taxon located places the radial head 4–12 % of forearm length distal to the humeroulnar joint** (search_trail §"Explicit negative result").
3. **No primary mm number for the human hinge-to-radial-head-center TOTAL distance** was located — the verdict rests on the axial form D_axial, which is the form the re-anchored anchor is placed in and the claim is worded in; D_total is recorded unmeasured rather than filled with an estimate.
4. **No primary tuberosity-to-elbow number** located ⇒ the model's 8.02 % tuberosity site is used only as qualitative corroboration, never as a cited figure.
5. The campaign brief's chain-sum "315.14 mm" is a transcription slip for 315.104 mm (C1 receipt correct); recorded in §5.3 and the arithmetic receipt.

## STOP RULE

All six acceptance criteria have verdicts; the falsifier outcome (fired) is reported with its numbers either way, as required. No dependency is missing; the anatomical question this audit owned is closed: **the primary evidence refutes the anatomical reading of the 7.5 %/7.9 % fraction and leaves the re-anchoring standing only on kinematic grounds (C3's closure mechanics), with no anatomical support.** Stopped here. No candidate selection, no supersession execution, no hand-side or ulna-orientation work (owned by C2/O-waves).
