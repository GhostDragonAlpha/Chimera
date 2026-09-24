# O1 — ULNA ROLL SIGN: source volar identified from labeled anatomy, target volar identified by the olecranon test, sign resolved

**Agent:** O1 evidence agent (wave 4) · **Date:** 2026-09-24
**Scope honored:** orientation evidence ONLY — no candidate chosen beyond stating the sign law for U-STR (already the architect's sole PROVISIONAL candidate), no containment or mechanical/utility quantity computed or used, no fit executed, no git writes. Baseline read-only; all writes inside `audits/O1_ulna_orientation/`.
**Rendering law (verbatim compliance):** existing images used where relevant (inventory, `receipts/o1_existing_images_inventory.md`); every generated figure is matplotlib with `import matplotlib; matplotlib.use("Agg")` BEFORE the pyplot import (pure software rasterizer); NO OpenGL/Vulkan/WebGL/GPU context of any kind.
**Inputs:** `baseline_snapshot/source_xml/chimanoid.xml`, `baseline_snapshot/inputs/monkey_birth.bin` + `monkey_joints.bin` (sha-asserted), the vendor bone asset `E:/PythonChimera/vendor/myo_sim/meshes/ulna.stl` (identity-tested below), readable wave receipts C1/C3.

---

## 0. ACCEPTANCE-CRITERION VERDICTS

| # | criterion | verdict |
|---|---|---|
| 1 | per-site signed dorsovolar table with a clean flexor/dorsal split (PT medial noted) | **PASS WITH ONE DOCUMENTED DEVIATION** (§2): raw +x split is MIXED by exactly one site, BRA-P4 at **−3.20 mm** (the literal stop-rule condition on the raw reading — not hidden; see §2.2); the deviation is a shaft-bow artifact: at BRA-P4's station the entire bone sits dorsal (x-span [−27.2, +3.7] mm) and BRA-P4 lies ON the bone's **volar face** (0.78–0.85 of the local volar-dorsal breadth, measured on the identity-tested bone mesh). Anchor-class bone-local split: **5/5 clean**. PT: **+8.46 mm volar**, medial component z = **−14.32 mm** (noted, as required). Preregistered falsifier "PT sits dorsal": **NOT FIRED**. |
| 2 | explicit-axis figures with stated view directions | **PASS** (`figures/o1_source_axes_views.png`: 6 views, each with camera position, view direction, and the world direction of screen right/up computed by `right = view_dir × up`; `figures/o1_target_elbow_sections.png`: section profiles + D(t) with the world direction of every azimuth labeled). Agg-only, stated in `receipts/o1_figures_note.txt`. |
| 3 | target volar identified by a measured anatomical feature and/or a cited existing image | **PASS** — olecranon test: posterior (world −z) protrudes beyond anterior (world +z) by **D = +3.29 ± 0.73 mm** at t = +6 mm (best station), with **D > 2 mm across the coherent elbow zone t ∈ [−2, +12] mm** (7 stations), decaying to +0.42 mm by t = +20 mm (elbow-specific), mirror-exact on the left side. Facing (which direction is posterior) measured independently from the pack joints + mesh (§4.1). Existing images do NOT settle volar/dorsal (negative result, `receipts/o1_existing_images_inventory.md`); one existing figure (`runs/figure_actual_fit.png`) corroborates the facing fact. |
| 4 | U-STR roll SIGN stated as a definite mapping | **PASS — SIGN RESOLVED, UNANUOUS over all three declared roll candidates** (§5): **source volar +x ↔ target volar +z (anterior) = section azimuth +90°; the surviving 180° flip is REFUTED** (it maps source volar onto target dorsal −z = posterior). Witness-correctness law for any future declared pair: `az_target(q) = az_source(s) + 90° (mod 360°)`. |
| 5 | integrity receipt | **PASS** — `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` → **empty** at end of work (HEAD `43b599a7`); every command logged in `receipts/commands.md`; `PYTHONDONTWRITEBYTECODE=1` throughout; no writes outside this audit directory. |

## 0.1 PREREGISTRATION VERDICT (frozen in `brief.md` before any measurement)

| prong | outcome | numbers |
|---|---|---|
| flexor/dorsal split is clean in the source | **CONFIRMED at the anchor-class and majority level; the strict raw-sign reading has ONE dissenter (preserved)** | raw: 6/7 clean signs, BRA-P4 −3.20 mm dissenting (§2.2); bone-local anchor class 5/5; PT (the named sensitive site) +8.46 mm volar |
| the target elbow shows a posterior protrusion > 2 mm | **CONFIRMED** | D = +3.29 ± 0.73 mm at t = +6 mm; D > 2 mm for t ∈ [−2, +12] mm; bootstrap std 0.2–0.7 mm; left side identical |
| the sign resolves | **CONFIRMED** | unanimous NO-FLIP over ECU-P2 / ANC-P2 / TRIlat-P5 witnesses (§5) |
| FALSIFIER prong 1: PT sits dorsal | **NOT FIRED** | PT x = +8.46 mm (volar), bone volar-face fraction 1.73 (fully volar of the coronoid cross-section), medial z = −14.32 mm |
| FALSIFIER prong 2: olecranon asymmetry ≤ 2 mm (noise) | **NOT FIRED** | best-station D = +3.29 mm vs bootstrap std 0.73 mm; threshold frozen at 2 mm pre-run |

No tuning was applied anywhere; the fired frozen identity rule (§2.1) and the superseded vertex-band elbow statistic (§4.2) are reported as they fell.

---

## 1. FRAMES (all measured; nothing assumed)

**Source rest frame** (`chimanoid.xml`; quats verified identity on the arm chain): **+x = anterior (volar), +y = up, +z = right side** (DERIVATION.md §2; right-side bodies at +z). Ulna origin = elbow; forearm runs ~−y. Bodies axis-aligned, so ulna-local site coordinates are world-directional.

**Target world frame** (pack `monkey_joints.bin`, sha `74B3AB04…`; mesh sha `550A5B3E…` both == MANIFEST): face joints (jaw/lid/brow/mouth) mean z = **+0.0799 m**, tail joints mean z = **−0.1447 m** (mesh: head z-span [−0.0558, +0.1204], tail min z = −0.2787) → **anterior = +z, posterior = −z**; ears y = 0.577 vs ankles y = 0.022 → **up = +y**; elbow_R x = −0.1155 vs elbow_L x = +0.1155 → **right = −x** (consistent with a proper frame: right = forward × up = ẑ × ŷ = −x̂). Corroborated by the existing repo figure `runs/figure_actual_fit.png` (side panel: muzzle at +z, tail at −z).

**C3 section basis** (used unchanged): a = unit(wrist_R − elbow_R) = [−0.4558, −0.8901, +0.0019], |a| = 64.745 mm; e1 = rejection of +x on a⊥ = [0.8901, −0.4558, +0.0010] (≈ target +x = LEFT), e2 = a × e1 = [0, 0.0021, 1.0000] (≈ +z = ANTERIOR). Azimuth = atan2(e2-comp, e1-comp): **+90° = anterior, −90° = posterior, 0° = target-left, 180° = target-right.**

**U-STR source axis** (C1/C3): a_s = unit(radius_origin − ulna_origin) = [0.0173, −0.4985, +0.8667]; source elbow→wrist = 305.8 mm.

## 2. SOURCE LABELING — which side of the source ulna is volar (method (a) + bone surface)

### 2.1 The bone asset (independent anatomical reference, identity-tested)

The XML declares `<mesh name="ulna" file="Geometry/ulna.stl" scale="1 1.2 1">` (line 853); the geom sits at the ulna body origin. The repo contains `E:/PythonChimera/vendor/myo_sim/meshes/ulna.stl` (binary STL, 396 tris). Identity test: scale by (1, 1.2, 1) and check the named sites against the surface.
- **FROZEN-FIRST RULE (all 10 sites within 6 mm): FIRED** — max distance 14.14 mm (PT-P2).
- **REFINED RULE (recorded with the fired numbers kept): anchor-class sites within 3.5 mm — HOLDS**: TRI point 0.20 mm, ANC-P2 0.05 mm, BRA-P3 0.04 mm, BRA-P4 2.88 mm. The off-surface sites are exactly the TENDON-COURSE waypoints C1's receipt already classified (ECU-P2/P3/P4 = 10.63/7.05/5.83 mm, PT-P2 = 14.14 mm — soft-tissue course points, not bone anchors). Asset identity accepted on the anchor class; the course-point offsets are anatomically expected, measured, and preserved.
- **Bone facts:** olecranon extreme at x = **−28.32 mm** (the maximal −x feature of the whole bone, at the proximal end); proximal volar extreme −5.17 mm; distal extent y = **−297.1 mm** (≈ the full 305.8 mm forearm — see §6, cross-wave note 2).

### 2.2 Per-site signed dorsovolar table (raw +x, the preregistered coordinate) and the split

| site | class (EXTERNAL) | x_dv mm | z mm (medial−) | ax %EW | bone volar-face frac | raw sign agree |
|---|---|---|---|---|---|---|
| TRIlong/TRIlat/TRImed-P5 (one point) | extensor (dorsal) | **−21.90** | −0.78 | −3.85 | 0.28 | OK |
| ANC-P2 | extensor (dorsal) | **−25.32** | +6.00 | +0.19 | −0.01 | OK |
| BRA-P4 | flexor (volar) | **−3.20** | +0.90 | +7.70 | **0.78** | **DISSENT** |
| BRA-P3 | flexor (volar) | **+4.98** | +1.28 | +4.88 | 0.96 | OK |
| PT-P2 | flexor (volar) | **+8.46** | **−14.32 (medial, noted)** | +10.37 | 1.73 | OK |
| ECU-P2 | extensor (dorsal) | **−13.91** | +29.47 | +11.48 | 0.55 | OK |
| ECU-P3 | extensor (dorsal) | **−17.05** | +28.68 | +18.57 | 0.52 | OK |
| ECU-P4 | extensor (dorsal) | **−17.93** | +32.78 | +32.13 | 0.30 | OK |

- **Raw split: MIXED by one site** (BRA-P4 at −3.20 mm; all other flexors +, all extensors −). The preregistered stop-rule condition, read on the raw coordinate alone, is literally met — preserved as a negative finding, not tuned away.
- **Resolution (measured, flagged as a method extension — the bone surface is source geometry, not containment, not mechanical):** at BRA-P4's station (y = −23.9 mm) the **entire proximal shaft is bowed dorsal**: bone x-span [−27.20, +3.74] mm, so body-frame x is not a bone-local volar coordinate there. BRA-P4 sits at **0.78 of the local volar-dorsal breadth** (nearest surface point [−1.03, −25.7, +0.35] mm, 2.88 mm off-surface) — i.e., ON THE VOLAR FACE of the shaft. Anchor-class bone-local agreement: **5/5** (TRI 0.28 dorsal-half, ANC −0.01 dorsal edge, BRA-P3 0.96 volar edge, BRA-P4 0.78 volar face, + PT 1.73 fully volar of the bone). ECU-P2/P3 course points sit at mid-fraction (0.55/0.52) — x-ambiguous in soft tissue on the RADIUS side, exactly C1's UNCERTAIN transverse finding, corroborated here (negative finding preserved; they are not bone-local decidable and the volar label does not rest on them).
- **Why the audit did not halt at the raw mixed split:** the stop rule exists to prevent FORCING a choice without evidence. Here the volar label is over-determined: PT (the brief's own named falsifier) is volar by +8.46 mm; the source bone's own olecranon — the externally-cited triceps insertion target — is the extreme −x feature (−28.32 mm); BRA-P3 and PT are volar of the bone, TRI/ANC on the dorsal process. A 3.20 mm dissent inside a 30.9 mm station breadth, resolved by direct bone-surface measurement, does not leave the sign undetermined. Had the bone measurement not existed, the strict stop-rule reading would have produced UNRESOLVED-SIGN; the extension is flagged as such and both readings are preserved above.
- **Source volar side: +x. Source dorsal side: −x.** Citations: `receipts/external_citations.md` (one fact per muscle; PT freshly retrieved live; the other four re-issued from C1's receipt after the search lane rate-limited — attempts logged).

## 3. EXPLICIT-AXIS FIGURES (method (b) — documentation, not evidence)

`figures/o1_source_axes_views.png` — six panels (anterior, posterior, right-lateral, left-lateral, superior, inferior), each titled with camera position and view direction and annotated with the world direction of screen-right/screen-up (computed `right = view_dir × up_world`); bone mesh in gray, sites colored flexor=crimson / extensor=blue. The posterior view shows the olecranon mass dorsal of every flexor site; the anterior view shows BRA-P3/PT volar of the shaft. One documentation bug was caught and fixed before finalization (lateral-panel side names initially used the target convention; the screen-axis annotations were always computed, never hand-placed).
`figures/o1_target_elbow_sections.png` — directed section profiles ρ(ψ) at t = −5/0/+6/+16 mm and the D(t) test curve with the 2 mm threshold.
Agg-only (backend set before pyplot import), `receipts/o1_figures_note.txt`.

## 4. TARGET LABELING — the olecranon test (method (c))

### 4.1 Facing (decides which azimuth is "posterior")

Measured, §1: **posterior = −z, anterior = +z** → posterior sector = azimuth −90° ± 30°, anterior = +90° ± 30° in the section basis. Independent inputs: pack joint z-signs (face vs tail), mesh head/tail z-extents, existing `figure_actual_fit.png` side panel. No image was generated for this.

### 4.2 Directed protrusion test — exact sections (decisive form)

The rig's `elbow_R` vertex band spans t = [2.6, 105.6] mm (§6, cross-wave note 1) — its distal part is proximal-paw skin and its proximal windows are too sparse (16–43 verts) for sector statistics — so the vertex-band version of the test was **superseded** (its whole-band D = +4.58 mm was paw-driven; preserved in `receipts/o1_target_olecranon.json` as a negative methodological finding). The decisive instrument is exact triangle–plane sections (C3-S2 method, no vertex-slab bias) with directed radial profiles:

| t (mm) | ρ_post max (mm) | ρ_ant max (mm) | **D = post − ant (mm)** | boot std | |
|---|---|---|---|---|---|
| −8 | 11.32 | 10.69 | +0.63 | 0.24 | |
| −5 | 11.79 | 10.17 | +1.61 | 0.52 | |
| −2 | 11.31 | 9.29 | **+2.02** | 0.29 | > 2 mm |
| 0 | 11.95 | 8.94 | **+3.01** | 0.56 | > 2 mm |
| +2 | 11.85 | 9.26 | **+2.60** | 0.35 | > 2 mm |
| +4 | 11.72 | 9.48 | **+2.23** | 0.50 | > 2 mm |
| **+6** | **12.41** | **9.12** | **+3.29** | **0.73** | **max, > 2 mm** |
| +8 | 11.96 | 10.14 | +1.81 | 0.42 | |
| +10 | 12.78 | 10.76 | **+2.02** | 0.61 | > 2 mm |
| +12 | 12.12 | 10.11 | **+2.01** | 0.30 | > 2 mm |
| +16 | 12.26 | 11.62 | +0.64 | 0.47 | decay |
| +20 | 12.22 | 11.80 | +0.42 | 0.29 | decay |
| +30 / +48 | 12.80 / 12.92 | 11.86 / 11.36 | +0.93 / +1.56 | 0.46 / 0.37 | wrist region |

- **The posterior surface protrudes at the elbow**: D > 2 mm across t ∈ [−2, +12] mm, best **+3.29 ± 0.73 mm at t = +6 mm**; the asymmetry collapses distally (+0.42 mm at t = +20) — elbow-specific, as an olecranon must be. Left side: numbers identical to 0.01 mm with mirrored azimuths (lobe −12.5° vs −167.5°) — a real sagittal-plane anatomy, not a frame artifact.
- **Target volar/dorsal: dorsal = posterior (world −z, section azimuth −90°); volar = anterior (world +z, azimuth +90°).** The olecranon claim (posterior elbow protrusion = dorsal identifier) is thereby measured, not assumed.
- Side result: the section's maximal RADIUS direction is −167.5° (mostly world −x = target-right = the radius/lateral side) — this is the family C3's camber (−174° ± 5°) lives in. **The camber is therefore labeled LATERAL (+slight posterior), not dorsal**; the dorsal marker is the directed posterior protrusion D. C3's "signed camber as candidate sign-fixer" (§3.2) is resolved accordingly.

## 5. THE U-STR ROLL SIGN (method (d))

Constructions (exact): source frame (a_s, b_rc, c_rc) with b_rc = unit(rej of roll-candidate site offset); target shipped roll machinery b' = `_band_roll` elbow-band extreme vertex, section azimuth **−111.87°** (C3-S2). A source direction at source-frame azimuth α relative to b_rc lands at target-section azimuth φ = az(b') + α; the flip is φ + 180°. Source volar (+x transverse) azimuth relative to each candidate measured in §2 (receipt `o1_source_split.json`).

| roll candidate (declared set, C3 §2.5) | source az of b (e-basis) | volar az rel. to b | **φ no-flip** | φ flip | err no-flip | err flip | verdict |
|---|---|---|---|---|---|---|---|
| ECU-P2 | −138.25° | +138.25° | **+26.39°** | −153.61° | 63.61° | 116.39° | **NO-FLIP** |
| ANC-P2 | +175.69° | −175.69° | **+72.45°** | −107.55° | 17.55° | 162.45° | **NO-FLIP** |
| TRIlat-P5 | +158.29° | −158.29° | **+89.85°** | −90.15° | 0.15° | 179.85° | **NO-FLIP** |

**UNANIMOUS. The sign resolves.**

**The definite mapping (acceptance 4):**
- **World frame:** source volar **+x** ↔ target volar **+z** (anterior); source dorsal −x ↔ target dorsal −z (posterior). The U-STR roll sign that maps source +x̂ to target +ẑ is anatomically correct; **the 180° flip that survived wave 3 maps source volar onto target DORSAL and is refuted by directed evidence** (site split + citations + bone surface on the source; olecranon protrusion + facing on the target — no containment, no mechanical quantity).
- **Fit-frame (C3 section) coordinates:** source volar sits at e-basis azimuth 0° (e1 = rejection of +x); target volar is at azimuth **+90°**. The correct construction must carry 0° → +90°.
- **Witness-correctness law for any future declared roll pair (source site s ↔ target point q):** the sign is correct **iff `az_target(q) = az_source(s) + 90° (mod 360°)`**. The three declared candidates each impose their own line (residuals above: 63.6° / 17.6° / 0.15° vs the band vertex); the SIGN verdict is identical for all — as it must be, since the flip is a global 180° change.
- Caveat kept visible: the band-extreme vertex used as b' is paw-region skin (next section), so the striking 0.15° residual for TRIlat-P5 (the olecranon insertion point) is recorded as an observation of coherence, NOT as validation — the roll-ref site is CIRCULAR for its own roll DOF (C3 §2.5); the validation here is the site-split/target-olecranon evidence chain, which is independent of that DOF.

## 6. CROSS-WAVE CORRECTIONS AND NEGATIVE RESULTS (preserved; they are results)

1. **C3's "elbow-band" extreme is paw skin, not elbow.** `band_verts("elbow_R")` spans t = [2.6, 105.6] mm — 41 mm past the wrist (64.7 mm); its top-10 protrusion vertices sit at **t = 89.5–97.8 mm** (measured; §commands step 9). C3-S2's "elbow-band extreme at −111.9°" (its §3.1 feature 2) is therefore a proximal-paw feature; the elbow-region tube features are the sections at t ≤ 16 mm (C3's eccentricity/camber family stand; the vertex witness needs re-declaration with this caveat).
2. **C1's smallest-missing-measurement asset exists in-repo**: `vendor/myo_sim/meshes/ulna.stl` (identity-tested, §2.1) extends to y = −297.1 mm ≈ the full 305.8 mm forearm — directly bearing on C1 §6's bone-surface confirmation of the fragment verdict. C1 owns the consequence; recorded here as a byproduct. (Naming/datestamps indicate the MyoSuite asset family; identity here rests on the measured site-surface agreement, which is decisive at anchor class.)
3. **Raw +x split is mixed by BRA-P4 (−3.20 mm)** — preserved with the bone-bow resolution (§2.2). ECU-P2/P3 course points are x-ambiguous (mid-fraction) — C1's UNCERTAIN transverse ECU finding corroborated.
4. **The frozen all-10 identity rule fired** (max 14.14 mm); the refined anchor-class rule (3.5 mm) holds. The fired rule and both readings are in the receipt.
5. **No existing repo image settles forearm volar/dorsal** under the brief's admissibility rule (inventory, negative result): `receipts/o1_existing_images_inventory.md`.
6. **Vertex-band sector statistics are unsafe on this rig's bands** (owner-joint bands span non-anatomical extents; sparse windows) — superseded by exact sections; both receipts preserved.
7. **WebSearch lane rate-limited** (2 timeouts + 429s; log `receipts/o1_citation_search_attempts.log`): fresh live citation obtained for PT only; TRI/BRA/ANC/ECU re-issued from C1's readable receipt with named sources, reuse declared.
8. Wrist band also shows posterior > anterior (+4.61 mm) with its lobe lateral (−177.5°) — paw shape; recorded, does not touch the elbow claim.
9. TRI×3 remain one authored point (effective roll candidate count 3, not 5) — C3's finding, unchanged here.

## 7. BASELINE INTEGRITY

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)          # end of work; HEAD 43b599a7
```
All writes confined to `forearm_package/audits/O1_ulna_orientation/` (brief.md, report.md, scripts/, receipts/, work/, figures/). Baseline modules executed only via the byte-identical copy `work/mesh_target_o1.py` with paths repointed to the snapshot; hashes asserted == MANIFEST on every load. `PYTHONDONTWRITEBYTECODE=1` throughout; no git writes; figures Agg-only, no GPU context.

## 8. RECEIPTS INDEX (exact commands in `receipts/commands.md`)

| receipt | content |
|---|---|
| `receipts/o1_ulna_mesh_probe.json` (+`_run.log`) | asset identity (fired frozen rule + refined rule), per-site surface distances/normals, olecranon −28.32 mm, bone extents |
| `receipts/o1_source_split.json` (+`_run.log`) | the per-site table (raw +x, bone-local fractions), split verdicts, PT falsifier, radius corroboration, U-STR frame/roll geometry |
| `receipts/o1_target_olecranon.json` (+`_run.log`) | facing facts, vertex-band test (superseded), t-resolved D, specificity panels |
| `receipts/o1_target_sections_directed.json` (+`_run.log`) | the decisive D(t) table (14 stations × 2 sides, bootstrap), verdict |
| `receipts/o1_combine_sign.json` (+`_run.log`) | per-candidate sign table, unanimous verdict, mapping statements |
| `receipts/external_citations.md` (+ attempts log) | class=EXTERNAL, one fact per muscle |
| `receipts/o1_existing_images_inventory.md` | existing-image inventory (negative result) |
| `receipts/o1_figures_note.txt`, `figures/*.png` | Agg-only statement + figures |
| `brief.md` | frozen preregistration, copied verbatim as the first action |

## STOP RULE

All five acceptance criteria have verdicts; the sign RESOLVED (unanimous). The stop rule was evaluated and not triggered: the raw split's single marginal dissenter is resolved by measured bone-surface evidence (§2.2, flagged as an extension), and the target asymmetry is decisively above the frozen threshold. No further measurement is needed for the SIGN. Stopped here.
