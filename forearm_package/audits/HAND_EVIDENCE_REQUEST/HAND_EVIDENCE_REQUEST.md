# HAND_EVIDENCE_REQUEST — identity-pinned view/landmark request for hand evidence

**Status:** DRAFT for coordinator promotion · **Author:** M-handreq (request authoring only) · **Date:** 2026-09-24
**Governing directive (handoff memo §5, verbatim):** *"For the hand, first produce an identity-pinned view/landmark request with known camera and independent source-palm evidence. Orientation does not establish same assembly, dimensions, digit structure or force capacity. No repeated reinterpretation of failed proxies."*
**Laws honored:** request authoring only — no new measurements (zero scripts run against any mesh in this audit); no mapping choice; no utility computation; every requested item names WHAT it closes and WHY no existing asset supplies it (cited). CPU-only; writes confined to `audits/HAND_EVIDENCE_REQUEST/`.

---

## §0. THE BOUNDARY (quoted, binding on every fulfillment)

> *"Orientation does not establish same assembly, dimensions, digit structure or force capacity."* — handoff memo §5

Four separate fronts, deliberately not conflated:

| front | question | owner of the open state | what THIS request does |
|---|---|---|---|
| **Orientation** | which face of the source hand / target paddle is PALM (the sign) | O2 blocker (both prongs failed independently) | **§R1, §R2 request the two closing artifacts** |
| **Same assembly** | does the target's wrist-distal region correspond to the source hand AT ALL | C2: UNDECIDABLE-WITH-CURRENT-ASSETS | **§R3 requests the correspondence artifact — SEPARATELY** |
| **Dimensions** | scale policy (H-LEN 0.716 / H-ASP 0.72–0.90 / H-BODY 0.2217), the 3.4–3.5× proportion mismatch | deferred (DR-C), pending same-assembly | **NOT requested here.** No scale, length, width or mass number appears in any request below |
| **Digit structure / force capacity** | sub-sampling digit grooves; transmission | C2 §5 (resolution-limited) / untouched (T6) | **NOT requested here.** |

A fulfilled §R1+§R2 closes the orientation sign. It does NOT make the paddle a hand (§R3 decides that), set its size, count its digits, or price its grip.

---

## §0.1 THE FAILED PROXIES — closed, referenced as recorded numbers only

| proxy | receipt | outcome | status in this request |
|---|---|---|---|
| 27-geom skeleton plane as palm-sign boundary (site test) | `audits/O2_hand_orientation/report.md` §2.1 | FALSIFIER FIRED — mixed compartment signs (flexor FCR-P3 −1.99 mm on extensor side; FCU-P4 +5.40 mm); digital-fan tilt ~10.0° moves site offsets ±1.0–5.6 mm at their 31–43 mm lever arm; 1/27 jackknife refits clean | **CLOSED.** Not re-run, not re-interpreted. Its recorded numbers (site positions, offsets) are cited as frozen context only |
| Paddle distal-half curvature (sagitta/thickness lens) | O2 §3 | FALSIFIER FIRED — faces bow apart (+2.12/−5.11 mm; uniform-bend arithmetic predicts 0.33 mm); D1 rim-dominated (trimmed −0.31 mm); mid-line nomination leaves palm concavity 0.95 mm < frozen 1 mm | **CLOSED.** §R1 replaces the curvature DECISION with a labeled view; no new curvature number is requested |
| Paddle lobation / splits / voxel tests | `audits/C2_hand_evidence/report.md` §2.2 controls | splits and dips proven sampling artifacts (proximal control splits 4/9; dips are 7–9-vertex slabs; 2 mm fragmentation) | **CLOSED at current sampling.** Not re-run |
| Existing-image lane (4 monkey renders) | O2 §4 | exists, INSUFFICIENT (no camera, wrong pose, unestablishable identity) | **CITED as the reason §R1 exists** (§R1.3) |

---

# §R1. TARGET-SIDE — identity-pinned view of the target hand region (KNOWN CAMERA)

## R1.1 What this closes

**O2's TARGET prong: the palm-face identification that curvature could not make.** The frozen curvature test failed because the distal paddle is a thickness lens on a linear taper, not a resting-flexion bend — every branch of the frozen decision tree landed on UNRESOLVED (O2 §3.2). A **labeled view decides palm-vs-dorsum by identification, not by curvature inference**: O2's own smallest-path statement — *"ONE visual identification of the paddle's palm face in a KNOWN birth-pose/camera frame … read by the operator/vision terminal — this alone closes the target end"* (O2 §5.1; restated in `forearm_package/USTR_DIAGNOSTIC_RECEIPT.md` §1 O2). The two faces are recorded as measurably DIFFERENT (palm-nominal +T face concave 0.95 mm; −T face the more convex lens face) — the view asks a human to say which difference is the palm, ending the 180° flip C3 proved is the only remaining freedom (*"line determined; sign undetermined"* — `audits/C3_independent_challenge/report.md` §4 HAND VERDICT).

## R1.2 Why no existing image qualifies (O2's inventory, §4)

Four distinct renders exist — `Saved/vision_trial/A_front_rest.png`, `B_leftside_rest.png`, `C_threeq_rest.png`, `D_front_elbowL50.png` (2560×1440; md5s all distinct per O2; sha256 recorded in this audit's `report.md` §4) — and ALL fail the preregistered bar ("visually decidable AND knowable orientation") on three independent grounds, quoted from O2 §4:

1. **Resolution:** hands are ~60–80 px wide — palm/dorsum at the edge of decidability even for a human.
2. **Pose + no camera:** poses are ANIMATED (D shows the left elbow flexed 50°), not the birth pose, and **no camera-to-mesh mapping exists anywhere in the repo** — the observed facing cannot be transformed into birth-mesh coordinates.
3. **Asset identity:** identity of the rendered character with the baseline birth mesh is not establishable from images — the renders show separated digits and a thumb, while C2 proved the birth paddle has **zero digit-distinguishable structure** at its sampling (`audits/C2_hand_evidence/report.md` §5).

Ruled-out families (O2 §4): `Saved/mesh_view/*` and `docs/evidence/*` are teddy renders; `runs/figure_*.png` are unshaded point-cloud projections. No existing artifact is a birth-mesh render with a known camera. That is the gap §R1 fills.

## R1.3 Requested artifact (exact form)

**Deliverable:** ≥ 2 PNG renders (+1 recommended) of the **hash-pinned birth mesh** with **declared camera extrinsics**, plus a sidecar JSON and an answer file.

**A. Images.**
- **View 1 (anterior-facing side):** camera on the +n_t side of the hand region, view direction −n_t.
- **View 2 (posterior-facing side):** camera on the −n_t side, view direction +n_t. *(The ± flip is deliberate and sufficient: both broad faces are photographed, each image's side is declared by its extrinsics, so the unresolved anatomical sign of n_t never enters — the human's answer creates it.)*
- **View 3 (recommended, not required):** axial view down the paddle (view direction −a, from 0.30 m proximal of the band center) showing the far-end cross-section outline (recorded 47.1 × 18.1 mm) — helps the reader see the lens/wedge shape O2 measured.
- Orthographic projection (no perspective distortion between the two face views); the distal band (55–111.4 mm axial) fills the frame.

**B. Annotations (on-image, machine-drawn not hand-placed):** wrist_R origin marker; axial ruler ticks at 0 / 48 / 55 / 80 / 111 mm along a (projected onto the mesh); each image titled with camera position, view direction, up vector and projection; faces labeled by their world side ("+n_t-side view" / "−n_t-side view"). Guidance line for the reader, from O2's recorded diagnostics: *"one broad face is the flatter/slightly cupped one, the other carries the outward lens bulge — state which is the palm/volar face."*

**C. Sidecar JSON** (one per render), fields: `eye`, `look_at`, `up`, `view_direction`, `projection` (ortho half-width in m), `image_size_px`, `mesh_sha256`, `joints_sha256`, `loader_sha256`, `mesh_unit_to_m`, renderer/channel name, exact script invocation, and — if any intermediate mesh repair/resampling was needed — its description and the repaired asset's sha256.

**D. Answer file** (plain text): which face is palm/volar; the visible feature the identification rests on; the reader's identity. Per the terminals law (*"No reference, no verdict"* — `AGENTS.md`; *"an LLM is never a terminal"*), the identification must be authored by the human terminal (operator, or operator-designated vision judgment **endorsed** by the human) — a bare model answer is another claim, not a verdict.

## R1.4 Identity pins (all pre-verified this audit; fulfiller re-asserts before rendering)

| pin | value | source |
|---|---|---|
| target mesh | `monkey_birth.bin` sha256 `550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c` (661,076 B) | MANIFEST crosscheck; `audits/B1_source_anatomy/receipts/target_hand_region.txt` L1; O2 §7 |
| joint pack | `monkey_joints.bin` sha256 `74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662` (296,589 B) | same |
| loader module | `baseline_snapshot/code/mesh_target.py` sha256 `268f139a9e90e561f4a5f8ab02553f0d87f51633f635139e6cec6f5c9cfa19a0` (byte-identical copy verified by O2 §1) | O2 §1, §7 |
| unit convention | `mesh_unit_to_m = 0.065` (authored); all camera numbers below in WORLD METERS via the loader's frame | B1 receipt L3 |
| frame (measured, O1 §frame) | target world: anterior = +z, up = +y, right = −x | `audits/O1_ulna_orientation/report.md` §1 |

**Reference frame and camera defaults (all numbers from frozen receipts; arithmetic only):**
- `wrist_R = (−0.144995, 0.261482, −0.005956)` m · `elbow_R = (−0.1155, 0.3191, −0.0061)` m (B1 joint list)
- paddle axis `a = unit(wrist_R − elbow_R) = (−0.455844, −0.890058, 0.001857)` (O2 §3)
- broad-face normal `n_t = a × T_R = (0.000000, 0.002086, 1.000000)` ≈ world +z (arithmetic on O2 §3's recorded `T_R = (0.890060, −0.455843, 0.000951)`); C3-S2's measured thickness principal line (azimuth 86.5–87.7° mod 180, bootstrap ±0.7–1.1°, stations 75–110 mm) is the refinement if used — its 180° ambiguity is irrelevant under the two-view design
- band center `look_at = wrist_R + 0.083·a = (−0.182830, 0.187607, −0.005802)`; `eye₁ = look_at + 0.30·n_t`, `eye₂ = look_at − 0.30·n_t`; `up = a`; ortho half-width 0.040 m; 2048×2048.
These defaults are **executable as-is**; any deviation is acceptable if fully declared in the sidecar (the requirement is REPRODUCIBILITY, not these numbers).

## R1.5 Acceptance criteria (all must hold to close the target prong)

1. **Identity:** render inputs hash-assert equal to the pins in R1.4 before rendering; the rendered surface derives from the pinned file (any repair declared + hashed in the sidecar).
2. **Reproducibility:** re-running the declared invocation on the pinned inputs reproduces the view (pixel-identical, or equivalent within the declared renderer nondeterminism).
3. **Visibility (derived bar):** the 47.1 mm broad face spans **≥ 600 px** in the frame. Derivation: O2 §4 recorded the existing renders failing at 60–80 px hand width; 600 px is ≈ 8× that recorded failure point (≥ ~12 px/mm on the face) — margin to move palm/dorsum from "edge of decidability" to plainly decidable. No other number in this request is tuned.
4. **Decisiveness:** the answer file names ONE face as palm/volar, cites the visible feature, and names the reader (human, or human-endorsed vision judgment).
5. **Recording:** images + sidecar + answer land in the coordinator-designated returns directory with sha256 of each file recorded by the fulfiller.

## R1.6 Falsifiers (what would REFUTE the assumption this request encodes)

- **F-R1a (visibility assumption):** if both broad faces are visually indistinguishable to the reader at the ≥ 600 px bar (no flat/cupped vs bulged asymmetry a human can name), the assumption *"the palm/dorsal distinction is visible in the birth-mesh surface"* is **REFUTED** — the target sign remains unresolved at this asset resolution and O2's lens/flat reading stands as the visual truth. The blocker survives; the failure is recorded, not retried with a re-framed camera (that would be proxy re-interpretation).
- **F-R1b (identity assumption):** hash mismatch, or an undeclared mesh modification — artifact rejected outright, no reinterpretation.
- **F-R1c (region assumption, cross-feeds §R3):** if the views reveal the wrist-distal blob reads as NON-hand anatomy (e.g., limb/tail skin mass), the same-assembly premise is refuted — escalate to §R3 before any palm sign is consumed.

---

# §R2. SOURCE-SIDE — independent source-palm evidence (fan-independent palm normal)

## R2.1 What this closes

**O2's SOURCE prong.** The frozen 27-geom plane failed as the palm-sign boundary because the asymmetric digital fan (digits 2/3 curl to +z up to +19.5 mm; digit 5 to −z down to −8.5 mm) tilts it ~10.0°, contaminating every site offset by −1.0 to −5.6 mm at the sites' 31–43 mm lever arm; jackknife refits split cleanly only 1/27 (O2 §2.2). What closes the prong is a **palm identifier independent of the phalange fan** — USTR §1 O2, verbatim: *"a source-side palm identifier independent of the digital fan (e.g., a palmar surface mesh or an author-declared palm landmark) closes the source prong."* With a signed source palm direction in hand, the hand roll SIGN mapping (source palm ↔ §R1's identified target face) becomes stateable — the exact deliverable O2 criterion 4 could not produce (*"no definite mapping exists to state"*, O2 §0).

## R2.2 Why no existing asset supplies it

1. **The source record is anchor-only.** All 27 hand bones are mesh geoms, but every source length and plane in the record is bounded by authored geom POS anchors, not surfaces — *"the 27 skeleton MESH assets are external; every source length below is bounded by authored geom POS anchors, not mesh surfaces"* (C2 §2.1). The XML declares the meshes (`Geometry/pisiform.stl` … `Geometry/5distph.stl`, chimanoid.xml L855–881, right hand; L885+ left mirrors; hand meshes at `scale="1 1 1"`, unlike the ulna's `scale="1 1.2 1"`) but the baseline snapshot contains no Geometry/ directory.
2. **In-repo vendor candidates are UNVERIFIED for the hand.** `E:/PythonChimera/vendor/myo_sim/meshes/` holds 215 STLs including same-named files (`pisiform.stl`, `1mc.stl`, … `5distph.stl`, plus `arm_r_*` variants) — but identity has been established for **exactly one** file, `ulna.stl`, by O1's measured site-surface test (*"identity here rests on the measured site-surface agreement, which is decisive at anchor class"* — O1 §2.1, §8.2). R1 pinned the provenance of the **XML** (FreeMusco `chimanoid.xml` revision `e021d5d9d1698dafea93c0dcf34b4bc8ce1530e7`; byte-match on decisive strings), **not** of the vendor mesh directory. No record ties the hand STLs to the chimanoid's hand, and no palmar sign exists anywhere in the record: *"no source-internal or target-internal evidence says which face of the skeleton … is the palm"* (C3 §4.3).
3. **The near-clean diagnostics are not adoptable.** The raw local-z 3/2 split and the 13-geom palm-subset plane are recorded as DIAGNOSTICS ONLY — adopting either is authoring, which O2 was forbidden to do (O2 §2.2, §5.2). They are therefore either (a) superseded by §R2-form-A evidence, or (b) adopted by the authoring terminal under §R2-form-B.

## R2.3 Requested artifact — two acceptable forms (either closes the prong)

**Form A — the hand mesh assets + identity test + anatomical palmar reading.**
- **A1. Files:** the 27 right-hand bone STLs matching the XML declarations — `pisiform, lunate, scaphoid, triquetrum, hamate, capitate, trapezoid, trapezium, 1mc, 2mc, 3mc, 4mc, 5mc, thumbprox, thumbdist, 2proxph, 2midph, 2distph, 3proxph, 3midph, 3distph, 4proxph, 4midph, 4distph, 5proxph, 5midph, 5distph` (.stl) — from the FreeMusco revision `e021d5d9d1698dafea93c0dcf34b4bc8ce1530e7` (`Data/Muscle/Fullbody/Geometry/`, repo github.com/palkan21/FreeMusco) **or** pinned from the in-repo vendor directory **if** the identity test of A3 passes. Left-hand mirrors optional.
- **A2. Units/scale convention (mandatory declaration):** per-file sha256; upstream provenance (repo + revision/tag); the scale convention the files embody, stated against the XML's per-mesh `scale` attribute (hand meshes `"1 1 1"` — the fulfiller states whether the delivered files are pre-scaled or carry the attribute; the ulna precedent is scale-then-test, O1 §2.1).
- **A3. Identity test (O1-class protocol, anchor class):** assemble the 27 meshes at the XML geom pos anchors (chimanoid.xml L635–661) and show anchor-class agreement — the acceptance bar is the O1 rule as refined there: anchor-class landmarks within **3.5 mm** of the tested surface, with tendon-course-type deviations separately enumerated (O1 §2.1: anchor class 5/5 at ≤ 2.88 mm; the frozen all-sites rule fired at 14.14 mm and was recorded, not hidden). For the hand, the anchor class is the geom-anchor skeleton itself: assembled chain extents must reproduce the anchor-derived record (distalmost `3distph` 155.29 mm; ray chains 67.0/96.4/100.2/89.1/78.6 mm) within the stated tolerance class.
- **A4. Palmar reading:** from the identity-tested assembly, a **signed unit palm normal in `hand_r` local coordinates** (hand_r world origin `(−0.0731, 0.532647, 0.202699)`; local frame axis-aligned per O1 §1), identified from PALM structures — carpal anatomy (pisiform protuberance, hamate hook side) and/or the metacarpal row — NOT from the phalange fan. Named feature + rationale required; human terminal per R1.3-D.

**Form B — author-declared palm landmark list (the authoring path O2 §5.2 already scoped).**
- A text/JSON declaration by the authoring terminal: ≥ 3 named palm-side landmarks in `hand_r` local coordinates (or one palm point + declared normal), each inside the hand's anchor hull, **none of them the 5 tendon sites** (those are the test set — independence), plus the declared sign stated in words ("the palm is the −z/+z side because …"). Alternative zero-cost variant already scoped by O2 §5.2: explicit authoring ACCEPTANCE of the recorded raw local-z / 13-geom-palm diagnostic as the boundary — that is a decision of the authoring terminal, recorded as such; it is not evidence and this request does not make it.
- **Closure test (same for both forms, recorded numbers only):** the declared/derived palm normal must produce a **clean flexor/extensor split on the frozen site table** (sites at chimanoid.xml L663–667; O2 §2.1's recorded offsets as the reference outcome). A clean split closes the source prong.

## R2.4 Acceptance criteria

1. Form A: files hash-pinned with upstream revision; units/scale declared; identity test passes at the anchor class with per-point numbers recorded; palmar normal signed, fan-independent, feature-named. — Form B: landmarks named, in-frame, independent of the 5 sites, sign declared with rationale.
2. Either form yields a clean compartment split on the frozen site table.
3. The declared/derived normal is recorded in `hand_r` local coordinates so the roll-sign mapping to §R1's identified target face can be stated (closing O2 criterion 4).

## R2.5 Falsifiers

- **F-R2a (asset-identity assumption):** the identity test fails (assembled vendor/upstream hand inconsistent with the pos anchors beyond the anchor-class rule, or the files prove to be a different family's geometry, e.g. the `myohand` set) → the assumption *"the XML pos anchors and the referenced Geometry/*.stl assets describe the same hand"* is **REFUTED**; escalate to an upstream vendor statement (FreeMusco/MyoSuite) or fall back to Form B.
- **F-R2b (tilt-artifact assumption):** the declared/derived palm normal, applied to the frozen site table, still leaves a flexor on the extensor side → the assumption *"the failed split was an artifact of the plane's fan tilt"* is **REFUTED**; the sites' compartment semantics and the palm declaration are in direct contradiction — escalated to the architect, not resolved here.
- **F-R2c (fan-independence):** a submitted "palm" definition built from phalangeal/fan members is non-fulfilling by construction (it re-encodes the failed proxy) — rejected without measurement.

---

# §R3. ASSEMBLY — same-assembly correspondence evidence (SEPARATE FRONT)

## R3.1 What this closes

**C2's same-assembly verdict: UNDECIDABLE-WITH-CURRENT-ASSETS** (`audits/C2_hand_evidence/report.md` §3). The deciding refusals were: proportions differ **3.4–3.5×** (source hand:forearm 0.4928 vs paddle:forearm 1.7184); the paddle exhibits **zero digit-distinguishable structure** at current sampling; the source side is anchor-bounded; and the pack itself does not claim the region — past ~41 mm the skin binds to `tail_base`/`spine_lower` (B1 §2.2) and B1 §5.1 could not exclude non-hand skin inside 40–111 mm. What is missing is not another measurement of the paddle — it is **evidence about correspondence**: author intent or species reference. The in-repo render of the blob (C2 §3, smallest-missing #1) is expected as a **byproduct of §R1's views** — but a render can only show the blob is a mitt-shaped region; it cannot show it CORRESPONDS to the source's hand. Hence this separate request.

## R3.2 Why no existing asset supplies it

The baseline is a mesh + joint pack with no authoring provenance for the hand region; the ownership anomaly (`target_hand_region.txt`: of the 1109 distal verts, `spine_lower` 510 / `tail_base` 377 / `elbow_R` 215 / `wrist_R` 7) means even "which band is hand" is undeclared; and the source is a FICTIONAL model (FreeMusco Chimanoid, R1 §2) — so no species-normative correspondence argument exists for the source side either. Neither C2 nor B1 could render; no text in the pack asserts the region's anatomy.

## R3.3 Requested artifact — either form

**Form A — vendor/author construction statement** for the target mesh: a signed text file (author/vendor identity + revision/hash reference) declaring, for the region pinned below: (i) what the wrist-distal blob depicts (the creature's hand? hand + mis-bound skin? other limb/tail skin?); (ii) the construction intent for the distal band (fused-digit mitt vs featureless slab); (iii) whether the author asserts or denies correspondence to a five-ray hand skeleton; (iv) the disposition of each ownership band named in R3.4.

**Form B — external labeled reference of the depicted creature's actual hand:** photograph / CT-scan view / dissection plate of the hand of the animal the mesh depicts, anatomically labeled (palmar, dorsal, digit rays), WITH the specimen-to-mesh provenance declared (the target's species is undeclared in the baseline inputs — recorded at B1/R1 — so the reference must carry its own provenance; note R1 proved the SOURCE is fictional Chimanoid, so this reference speaks to the TARGET creature only).

## R3.4 Identity pins (the region being asked about)

- Region: verts distal of `wrist_R = (−0.144995, 0.261482, −0.005956)` m within the r < 42 mm cap along `a` (values per R1.4): 1109 verts, axial extent **111.4 mm**, far end (80–115 mm) transverse extents **47.1 × 18.1 mm** (`audits/B1_source_anatomy/receipts/target_hand_region.txt`, `_v3.txt`).
- Ownership bands to be dispositioned: `elbow_R` reach ≤ 40.8 mm · `tail_base` 40.6–103.4 mm · `spine_lower` 41.2–111.4 mm · `wrist_R` ≤ 1.8 mm (same receipt).
- Mesh/pack hashes per R1.4. Source-side context pins: `chimanoid.xml` sha256 `675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1`; FreeMusco revision `e021d5d9d1698dafea93c0dcf34b4bc8ce1530e7`; 27 welded hand geoms, zero digit joints (B1 §1.3); distalmost anchor `3distph` 0.1554 m (frozen evidence; 155.29 mm measured, C2 §2.1).

## R3.5 Acceptance criteria

1. Form A: statement dispositioned band-by-band (hand vs non-hand for each ownership band), correspondence asserted or denied in words, author/vendor identified, revision referenced. — Form B: plate labeled, specimen provenance declared.
2. The statement/plate addresses the 41–111.4 mm band specifically (the anomalous zone), not just the wrist.
3. It changes C2's verdict class: correspondence DECIDED (supported or refuted), or explicitly declined (which is itself a recordable answer that keeps UNDECIDABLE standing).

## R3.6 Falsifiers

- **F-R3a:** a statement that the distal blob is NOT (entirely) the creature's hand → **REFUTES the same-assembly premise** underlying H-LEN/H-ASP/H-BODY; the hand policy set's premise voids, and a palm/dorsal sign on a non-hand region (§R1) becomes moot for mapping purposes.
- **F-R3b:** a statement "the paddle is the hand with permanently fused digits" → refutes the no-correspondence reading and hands the digit-structure front its premise — but does NOT measure digit structure (sub-sampling grooves stay C2 §5's open lane), does NOT set any dimension (the 3.4–3.5× proportion mismatch stands as the dimensions front's fact), and says nothing about force capacity (T6-untouched).

---

## §4. EXPLICIT NON-REQUESTS (the "no repeated reinterpretation" clause, enforced)

This request does NOT ask for, and will reject as non-fulfilling:
1. New curvature/sagitta/thickness profiles of the paddle (O2 §3 proxy — closed).
2. Re-fits, re-tilts or re-interpretations of the 27-geom plane's sign test (O2 §2.1 proxy — closed; its table is cited as frozen numbers only).
3. New lobation/split/voxel/resolution sweeps of the paddle (C2 §2.2 — closed as artifactual at current sampling).
4. Any choice among H-LEN/H-ASP/H-BODY, any scale/mass/dimension number, any mapping (DR-C — architect's).
5. Any moment-arm, path-length, transmission or utility quantity (T6).
6. Re-runs of the four existing renders with new crops or zooms (their failure causes — pose, camera, identity — are not curable by re-reading; O2 §4).

## §5. FULFILLMENT AND RETURNS

Returned artifacts land in a coordinator-designated returns directory (proposed: `forearm_package/audits/HAND_EVIDENCE_REQUEST/returns/`), each file's sha256 recorded by the fulfiller alongside the answer file. Every returned artifact re-asserts the R1.4/R3.4 hashes before use. Fulfillment of §R1 + §R2 closes O2's both-prong blocker and lets the hand roll SIGN mapping be stated (O2 criterion 4). §R3 is tracked separately against C2's verdict and DR-C; it gates the same-assembly-dependent policy set, not the orientation sign.
