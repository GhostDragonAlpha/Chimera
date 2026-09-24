# C3 — INDEPENDENT CHALLENGE: circularity, orientation uniqueness, decision skeleton, supersession proposal

**Agent:** C3 (adversarial challenge, wave 3) · **Date:** 2026-09-24
**Baseline (READ-ONLY):** `E:/PythonChimera/forearm_package/baseline_snapshot/` — untouched; git-clean start and end (§10).
**Binding laws honored:** architect 2026-09-24 verbatim: "An attachment site such as ECU-P2 cannot independently validate a fit if that same site was used to construct it. Likewise, a palm-plane reference needs independently identified anatomical points." No candidate chosen; anatomical validity only; freeze-before-comparison (evidence, uncertainty, acceptance criteria, falsifiers frozen in `brief.md` before any measurement ran); all rejected/unresolved alternatives preserved; zero moment-arm or tendon-utility computation (T6 discipline, B4 protocol §3-T6); no fit, production mapping, or supersession executed.
**Deliverables:** this report · `decision_table.md` (the I6 skeleton) · `receipts/` (exact commands + outputs) · `scripts/` · `work/` (module copy only).

---

## 0. ACCEPTANCE-CRITERIA VERDICTS

| # | criterion | verdict |
|---|---|---|
| 1 | Circularity tables complete for all 5 candidates + roll candidates, every circular use flagged | **PASS** (§2; U-STR, U-ANA, H-LEN, H-ASP, H-BODY, R-ulna ×3, R-hand ×2; circular uses flagged: U-ANA/ECU-P4 anchor-falsifier, H-LEN/H-ASP paddle-anchored scale, H-BODY manufactured P_d, every roll ref for its own DOF, the shared elbow-band witness) |
| 2 | Orientation-uniqueness verdicts per body with measured margins, both ulna-axis directions treated | **PASS** (§3: ulna = AMBIGUOUS — roll LINE measurable at ±8–11° and a signed camber at ±5°, but the 180° sign/anatomical label is undecidable on current assets; §4: hand = AMBIGUOUS — palm-plane line determined to ±2–3° with construction ⊥ validation achieved, same 180° sign gap; both ulna-axis directions ±a are magnitude-invariant by construction, stated and used) |
| 3 | Decision-table skeleton complete, all alternatives preserved | **PASS** (`decision_table.md`: 11 rows incl. the REJECTED 5-site-plane construction and the undeclared target-roll-witness row; every cell cited) |
| 4 | Radius-supersession proposal exact and cited, marked NOT AUTHORIZED | **PASS** (§6 — exact record set, mechanism with code lines, necessity, non-effects; NOT AUTHORIZED banner) |
| 5 | Smallest-missing-measurement list per unresolved cell | **PASS** (§8) |
| 6 | Baseline integrity — porcelain status of baseline_snapshot empty | **PASS** (§10, empty at start and end) |

**Preregistration verdict (frozen in brief.md): the FALSIFIER FIRED — honestly, on its second prong.**
- PREDICTION "no candidate passes independent validation on ALL columns": **holds** — no row reaches VERDICT-READY (decision_table.md); falsifier prong 1 not fired.
- PREDICTION "ulna roll is the weakest link: a near-symmetric skin tube cannot distinguish dorsal/volar": **FALSIFIED AS WRITTEN** — the tube is NOT near-symmetric: eccentricity 1.16–1.40 (bootstrap IQR e.g. [1.24, 1.58] at t=4 mm), a principal eccentricity line stable at azimuth ≈ −112° ± 10°, and a camber (section-centroid offset) of 6.6–7.7 mm at a signed azimuth −174° ± 5°, both mirror-consistent L/R (§3). Falsifier prong 2 ("report if ulna cross-sections DO carry a discrimination margin above measurement noise"): **FIRED** — margins are 2–5× the noise floor (§3.2).
- PREDICTION "hand orientation is the strongest (skeleton-plane construction ⊥ site validation achievable)": **CONFIRMED** (§4).
- PREDICTION "scale constructible but not independently validable for U-ANA (its anchor is its own construction)": **CONFIRMED** (§2.2, §2.4).

---

## 1. METHOD AND INPUTS

- Source side: `baseline_snapshot/source_xml/chimanoid.xml` parsed with the exact intake semantics (`world = parent_world + parent_rot @ pos`, quats verified identity on the arm chain). My walk reproduces A4's quoted origins exactly (`radius` (−0.0911, 0.823047, 0.177699), `hand_r` (−0.0731, 0.532647, 0.202699)) — receipt `receipts/c3_source_geometry.json` (C3-S1).
- Target side: `baseline_snapshot/inputs/monkey_birth.bin` + `monkey_joints.bin` through a byte-identical module copy (`work/mesh_target_c3.py` = baseline `mesh_target.py`, paths repointed to the snapshot); sha256 printed by the module and asserted equal to MANIFEST (`550a5b3e…`, `74b3ab04…`). Receipt `receipts/c3_target_sections.json` (C3-S2).
- Sections are EXACT triangle–plane intersection segment endpoints (no vertex-slab bias, no bridging); principal azimuths reported mod 180°; bootstrap = 200 point resamples per station.
- Both ulna-axis DIRECTIONS: every quantity C3-S2 reports (per-line distances, eccentricities, mod-180 lines) is invariant under a → −a; the direction ambiguity (C1's open question) enters nowhere as an assumption. C3-S1 additionally records the source-axis fact: ulna→radius = (0.0004, −0.011503, 0.019999), |v| = 0.023075 m, **62.10° off the humerus→ulna limb axis (axial 10.8 mm, transverse 20.4 mm — mostly LATERAL)**, supporting C1's lateral-fragment reading; recorded as context, not decided here.
- T6: no moment arm, path length, or transmission quantity was computed or cited. Mesh/joint distances and cross-section moments are declared-landmark-class geometry (B4 T6 exemption clause).

---

## 2. STEP 1 — CIRCULARITY AUDIT

Classification law (per brief): **INDEPENDENT** = not used in the candidate's construction · **DEPENDENT** = same dataset/region, different measurement (correlated, not fully independent) · **CIRCULAR** = a construction input reused in the validation role for the same claim.

### 2.1 U-STR (construction inputs: source `body_origin:ulna`, `body_origin:radius`; target `elbow_R`, authored derived point ±5.116 mm; target roll witness UNDECLARED)

| validation item | class | reason |
|---|---|---|
| 10 ulna sites' fitted placement (skin loops, anatomical ordering) | **INDEPENDENT (9/10)** | no site is a construction input of U-STR; minus the one chosen as source roll ref |
| the roll-ref site's own fitted placement | **CIRCULAR** (roll DOF) | the architect's named pattern: it defines the roll it would validate |
| ECU-P4 fitted-position/skin-loop falsifier (MAP §2.1) | **INDEPENDENT** | ECU-P4 not used by U-STR |
| scale "in-band at 0.2217 = body scale" | **DEPENDENT** | the 5.116 mm point is 0.023075 × (radius's measured scale): the scale claim IS the radius edge's elbow→wrist evidence re-used; "in-band" is self-referential, not confirmation |
| elbow/wrist anchor gap 0.0 (B3/B4 E6) | construction input | not validation |
| F1 closure at ulna.P_d | structural consequence | forces radius re-anchor (§6), not evidence |
| laterality mirror (T3) | process check | not placement evidence |
| skin-tube roll line (§3) | **INDEPENDENT** | tube never enters construction; can cross-check the roll DOF |

### 2.2 U-ANA (construction inputs: source `body_origin:ulna`, **`site:ECU-P4`**; target `elbow_R`, `wrist_R`; target roll witness UNDECLARED)

| validation item | class | reason |
|---|---|---|
| the other 9 sites' placement | **INDEPENDENT (8/9)** | minus the roll-ref site |
| the roll-ref site's placement | **CIRCULAR** (roll DOF) | as above |
| **ECU-P4's fitted position / skin-loop falsifier (MAP §2.1)** | **CIRCULAR (axial claim)** | **ECU-P4 IS the source distal landmark: its \|D−A\| = 0.102765 m sets the scale and its identity sets the axis. Reusing its fitted position to refute or confirm the authoring is the exact pattern the architect prohibited (ECU-P4 in ECU-P2's role). The MAP's entry falsifier is void as written for U-ANA.** |
| scale plausibility (0.630 = 2.84× body scale; outside T4 neighbor band [0.1145, 0.4581], inside aspect envelope [0.2, 5.0]) | flagged, not validation | T4's band is a refusal screen, not support |
| `wrist_R` anchor gap 0.0 | construction input | the distal target landmark itself |
| skin-tube roll line (§3) | **INDEPENDENT** | as U-STR |
| mass 0.182 kg | arithmetic | m·det(S), DER §9 — carries `requires_density_validation`, not evidence |

### 2.3 H-LEN / H-ASP (construction inputs: source `body_origin:hand_r`, geom `3distph`; target `wrist_R`, paddle far-end point [and, H-ASP, the 47.1 × 18.1 mm cross-section]; roll = palm-plane/paddle-flat)

| validation item | H-LEN | H-ASP | reason |
|---|---|---|---|
| 5 sites' fitted placement vs paddle interior | **INDEPENDENT (sites)** / DEPENDENT (paddle side) | same | sites enter no construction (roll is skeleton-based, §4); the paddle region they are checked against supplied P_d — the check is site-fresh but paddle-correlated |
| paddle principal axis vs elbow→wrist (MAP falsifier (a); measured ~1.6°, C3-S2) | DEPENDENT | DEPENDENT | same paddle family that produced P_d/width landmarks |
| paddle cross-section vs s_b/s_c | n/a | **CIRCULAR** | the 47.1 × 18.1 mm measurement IS the b/c evidence |
| skeleton-plane ⊥ 5-site validation (direction A, §4.2) | **INDEPENDENT** | **INDEPENDENT** | 27 geoms construct; sites validate; neither set is the other's input |
| mass 0.168 / 0.227 kg | arithmetic | arithmetic | det(S) family |
| scale claim s = 0.716 (or s_a) | **not independently validable** | same | anchor and evidence are the same paddle extent — CIRCULAR for the length claim |

### 2.4 H-BODY (construction inputs: source `body_origin:hand_r` + a manufactured distal ref at 0.0344 m; target `wrist_R` + authored point)

| validation item | class | reason |
|---|---|---|
| the scale claim s = 0.2217 | **CIRCULAR by construction** | P_d is DEFINED as the image of the source fingertip under the claimed scale; the "distal landmark" is the claim wearing a landmark's clothes. Nothing can independently validate it |
| paddle placement of the 5 sites (7–9 mm past wrist, proximal third) | **INDEPENDENT** (genuinely — the paddle enters no H-BODY construction input) | and it does not refute; it exposes the coverage mismatch MAP already states |
| mass 0.005 kg | arithmetic | det(S) |

### 2.5 Roll candidates

**Ulna (source roll ref ∈ {ECU-P2, ANC-P2, TRIlat-P5}):**
- The chosen site is a **construction input**: CIRCULAR for the roll DOF by the architect's ruling, verbatim. The remaining 9 sites (8 under U-ANA) are the independent validators, plus the skin-tube line (§3.2).
- T1-legality: all three are ulna-owned, inside the legal set {body, parent, chain_child} (B4 protocol T1.4).
- T2-legality: measured per-line roll witnesses (m) — ECU-P2 0.01961 (U-STR axis) / 0.01877 (U-ANA); ANC-P2 0.02549 / 0.02495; TRIlat-P5 0.02346 / 0.02348. All ≫ ROLL_EPS 1e-9; T2 passes under both authorings and both axis directions.
- The three candidates are NOT interchangeable: their imposed b-azimuths differ by **46.06° (ANC-P2) and 63.46° (TRIlat-P5) from ECU-P2** under the U-STR axes (C3-S1). Roll choice swings every site's transverse placement by tens of degrees.
- **TRIlat-P5 ≡ TRIlong-P5 ≡ TRImed-P5 (one authored point)** — the "candidate" consumes one point that terminates three tendons (C3-S1).
- **The MAP's target-side roll witness is UNDECLARED** for every candidate: a roll ref needs BOTH a source resolution and a target landmark; the MAP names only source sites. The only existing target machinery is `_band_roll` (atf:89-97) on the elbow band — the very witness the resolved radius edge already consumes (B3 §2.3), i.e. **DEPENDENT** if reused, and skin-unlabeled if re-measured (§3.3).

**Hand (palm-plane ↔ paddle-flat):**
- Source plane constructed from the 27 skeleton geoms is **site-independent** (the architect's "independently identified anatomical points" exist: named carpals/metacarpals). Direction A (geoms construct, sites validate) PASSES (§4.2) — no circularity.
- Direction B (5 sites construct, skeleton validates) is **REFUTED** (§4.2) and is preserved as the rejected alternative.
- The target paddle-flat normal is DEPENDENT for H-LEN/H-ASP (same skin region that anchors P_d and widths) and INDEPENDENT for H-BODY.
- The declared homolog itself (paddle-flat ↔ palm-plane) is an authoring, not a measurement — it remains Astra's to accept.

---

## 3. STEP 2a — ULNA ORIENTATION UNIQUENESS (both axis directions treated)

All numbers from C3-S2 (right side; left is the exact azimuth mirror — e.g. band extreme −111.87° ↔ −68.13°, camber −174.55° ↔ −5.45° — confirming measurement validity). Stations are mm from `elbow_R` along a = unit(wrist_R − elbow_R); t = −5 covers the PROXIMAL direction (the live ± axis direction of U-STR).

### 3.1 What the skin tube measures

| station t (mm) | ecc λ1/λ2 (boot IQR) | principal line az (mod 180°) | boot circstd | camber (mm) | camber az (signed) | boot circstd |
|---|---|---|---|---|---|---|
| −5 | 1.19 [1.18, 1.40] | 59.7° | 26.7° | 6.93 | −174.6° | 4.98° |
| 4 | 1.40 [1.32, 1.58] | 63.6° | 12.7° | 7.72 | −168.6° | 4.75° |
| 8 | 1.30 [1.24, 1.46] | 69.7° | 17.3° | 7.47 | −171.5° | 5.14° |
| 12 | 1.29 [1.25, 1.47] | 74.4° | 17.6° | 7.49 | −171.1° | 5.23° |
| 16 | 1.35 [1.28, 1.49] | 76.3° | 12.9° | 7.17 | −173.2° | 4.89° |
| 20 | 1.30 [1.22, 1.50] | 76.2° | 18.1° | 6.91 | −176.3° | 5.90° |
| 24 | 1.26 [1.20, 1.47] | 75.1° | 20.7° | 6.77 | −176.8° | 6.12° |
| 28 | 1.22 [1.18, 1.37] | 72.4° | 21.7° | 6.93 | −177.8° | 6.31° |
| 32 | 1.18 [1.16, 1.39] | 70.7° | 28.5° | 6.58 | −176.9° | 6.32° |
| 40 | 1.24 [1.18, 1.44] | 70.8° | 21.1° | 6.99 | −176.2° | 6.50° |
| 48 | 1.16 [1.15, 1.35] | 50.2° | 31.9° | 7.55 | −171.9° | 5.09° |

Three independent features of the same tube agree on ONE transverse line:
1. **Eccentricity major line**: azimuth −120°…−104° (mod-180 values above), drift ±10° over 53 mm — mean ≈ **−112° ± 10°**.
2. **Elbow-band extreme (the `_band_roll` family the resolved radius uses)**: top-10 off-axis band vertices span az −104.8°…−126.1° (a coherent bulge, ±11°); top perp 30.95 mm at −111.9°. The top-2 gap ratio is 1.001 — the argmax VERTEX is a coin-flip inside the bulge, but the bulge DIRECTION is stable. The band extreme lies ON the eccentricity line (−112 ≈ −116…−104).
3. **Camber (signed)**: section centroid offset 6.58–7.72 mm at az −168.6°…−177.8° (spread ±4.6°, noise floor ±4.8–6.5°) — a stable DIRECTED feature, roughly perpendicular-ish to the bulge line (59° away).

### 3.2 Discrimination margins (the falsifier question)

- Eccentricity 1.16–1.40 with bootstrap IQRs bounded well above 1.0 — the tube is measurably NON-circular at every station.
- Roll-candidate separations are 46.1°/63.5° (C3-S1). Against the line precision (±10° drift; ±13–32° bootstrap circstd), the tube line can arbitrate among the three candidates at roughly 1.5–5σ — marginal at 46°, adequate at 63.5°. The signed camber (±5–6°) is the sharpest transverse feature and is a candidate sign-fixer.
- **Verdict: the tube DOES carry a discrimination margin above measurement noise** (preregistered falsifier prong 2 FIRED; the "near-symmetric tube" prediction is dead).

### 3.3 What the tube cannot do — the verdict

No source-internal or target-internal evidence LABELS any of these directions. Which side of the tube is dorsal, volar, ulnar, or radial is absent from the record: B1 could not visually inspect the mesh (B1 §5.1), the hand-region ownership anomaly (B1 §2.2) warns that skin regions can be mis-bound, and the source sites carry no authored dorsal/volar tag that survives into the target. The roll DOF is therefore fixed by target-internal geometry only up to the 180° flip (bulge line, eccentricity) with a signed candidate (camber) whose anatomical name is unknown.

**ULNA VERDICT: AMBIGUOUS.** The remaining symmetry is the 180° sign/anatomical-label flip, not a free roll: orientation is determined as a LINE to ±10° (and a signed direction to ±5–6° exists), but its anatomical orientation is UNDETERMINED on current assets. Both ± axis directions leave every number above unchanged (per-line distances and mod-180 lines are direction-invariant by construction); no roll analysis here assumed C1's pending direction resolution.

---

## 4. STEP 2b — HAND ORIENTATION UNIQUENESS (both construction directions tested)

All numbers from C3-S1 (hand_r local frame; left mirrors).

### 4.1 The two candidate palm-planes are DIFFERENT planes

| set | n | normal (unit, undirected) | σ (mm) | σ2/σ3 | residual rms / max (mm) | jackknife normal spread (mean/max) | angle to length axis (90° = axis in plane) |
|---|---|---|---|---|---|---|---|
| 27 skeleton geoms | 27 | (−0.133, −0.111, −0.985) | 251.8 / 109.3 / 55.4 | 1.97 | 10.66 / 28.61 | 1.67° / 13.81° | **88.79°** |
| 13 carpals+metacarpals (palm subset) | 13 | — | — | 2.72 | 5.08 / 7.94 | 2.75° / 8.13° | 87.21° |
| 5 tendon sites | 5 | (0.170, 0.870, −0.463) | 37.7 / 12.2 / 4.8 | 2.55 | 2.13 / 3.41 | **11.05° / 25.99°** | **24.20°** |

- The 27-geom plane and the palm subset agree to **6.39°** — the skeleton palm-plane is one coherent construct, determined to a few degrees, and it CONTAINS the hand length axis (88.8° ≈ 90°), as a palm plane must.
- The 5 sites' plane is a different object: 70.33° from the skeleton plane, weakly determined (jackknife ±11°/±26°), and nearly TRANSVERSE — the length axis is 24.2° from its NORMAL, i.e. it is a carpal-ring cross-section plane. MAP's parenthetical "the 5 hand sites are near-coplanar" is true and irrelevant: near-coplanar yes, palm-plane no.

### 4.2 The two directions

- **Direction A — construct from the 27 geoms, validate with the 5 sites: PASSES.** Sites about the skeleton plane: rms 8.88 mm, max 14.43 mm (per-site −12.33, −14.43, −0.86, −1.99, +5.40 mm) — INSIDE the plane's own residual band (10.66 / 28.61 mm; ratio 0.83). Construction ⊥ validation is achieved: the geoms never touch the sites, the sites never enter the construction. This is the acceptable direction under the architect's law, and the construction side is anatomically identified (named carpals/metacarpals).
- **Direction B — construct from the 5 sites, validate against the 27 geoms: REFUTED.** The skeleton lies 54.13 mm rms (max 113.31 mm) off the sites' plane = **25.4× the sites' own residual** (2.13 mm). The 5-site plane is dead as a palm-plane construction. Preserved as a rejected alternative with these numbers (freeze law).

### 4.3 Target side and the pairing

The paddle's flat normal (thickness principal line) is measured at stations 75–110 mm distal of the wrist: azimuth 86.5–87.7° mod 180 with bootstrap circstd **±0.7–1.1°**, eccentricity 14–31 — an extremely stable line. Pairing skeleton-palm-plane ↔ paddle-flat therefore fixes the hand roll LINE to ~±2–3°.

**HAND VERDICT: AMBIGUOUS (line determined; sign undetermined) — the strongest body, as predicted.** The remaining freedom is exactly the 180° flip: every plane normal is undirected, and no source-internal or target-internal evidence says which face of the skeleton (or of the paddle) is the palm. The paddle camber does not rescue the sign: its azimuth drifts monotonically (−138.9° → −89.9° over 75→110 mm, drifting ~50°) — not a stable signed feature. The site dorsal/volar split (ECRL/ECRB at local z > 0, FCR/FCU at z < 0, ECU mid) labels the SOURCE side only after the very sign in question is chosen — it cannot self-validate.

---

## 5. PREREGISTRATION VERDICT

See §0. Summary: main prediction HOLDS (no candidate independently validable on all columns); the ulna-tube sub-prediction is honestly FALSIFIED with numbers (the tube carries 2–5σ transverse structure); the hand prediction CONFIRMED; the U-ANA scale prediction CONFIRMED. Per the freeze law the fired prong changes no prior artifact — it is reported and the decision table carries the measured margins.

---

## 6. STEP 4 — PROPOSED RADIUS-RECORD SUPERSESSION (TEXT ONLY — **NOT AUTHORIZED**)

> **Banner (binding):** MAP Addendum §1 and TASK_BOARD wave-3: "No new fit session, production mapping, or radius supersession is authorized." This section is a PROPOSAL TEXT for I6/Astra. Nothing below has been executed; the frozen session-5 baseline is untouched and must remain so.

### 6.1 The exact records that would be superseded

Upon any future revision that resolves `ulna`/`ulna_l` with a DECLARED edge (P_d = X ≠ elbow_R/L):

1. `runs/attachment_candidates.json` → `bodies["radius"]` / `bodies["radius_l"]`: the exported `local_to_world` composition `R = B'·diag(s)·Bᵀ` (R at 12 decimals, `attachment_candidates.py:180`) and `t` (9 decimals, :179) — today s = 0.22170679566544982, t = (∓0.115480984, 0.319109077, −0.006076556), det(R) = s³ = 0.0108977544 (A4 §1).
2. The same records' `max_world_reconstruction_error_m` (today 0.0 at export precision; full precision 5.6e-17 m, A4 §2/Cross-check) and all 16+16 radius site `fitted_pos_global`/`fitted_pos_local` exports (the globals recompute; locals are source-verbatim and untouched, S13).
3. `runs/experiment_transverse_candidate.json` → `step_A_verification` mirror table: `reconstruction_max_err_m` = 1.1525314521376605e-09, `sagittal_plane_x_m` = 0.0, and the 16-pair table (max pair 0.6306 mm BICshort-P6) — all recomputed under the new fit (the plane law is data-derived from the pack spine joints and does not move).
4. The A4 receipt set (`audits/A4_transforms/receipts/a4_audit_run1.txt`, `work/a4_results.json`) and B4's known-good records (`receipts/01…09`) — they remain VALID FOR THE RECORDED FIT and become historical descriptions of the superseded revision (B3 F-4; ERRATA.md append-only discipline).
5. Cascade (same revision): the fit packet's admission ledger, tables, provenance hashes (correspondence digest and packet sha change), and the E6 anchor records; the hand edge's P (= wrist_R = radius.P_d) is unaffected.

### 6.2 The mechanism (why supersession is FORCED, not chosen)

- Closure law: DER §4 L135-140 ("shared joints are one point") + `compiler.py:399-423`: the check applies to each parent's FIRST child; `radius` is `ulna`'s first (and only) child; `sep = ‖radius.P − ulna.P_d‖` (L419) must be < `JOINT_EPS` = 1e-9 (`compiler.py:47`), else refusal `shared_joint_separation` (L422-423). The check is skipped ONLY while the parent is unresolved (`if parent not in seg_by_body`, L414-417; `seg_by_body` holds resolved segments only, L265-267/373-376). **The moment ulna declares a fitted edge, radius's proximal anchor is machine-enforced to ulna.P_d.**
- The shipped correspondence authors `radius: (elbow_R, wrist_R)` (`actual_target_fit.py:72`) and `chain_conflict` forbids re-parenting (`correspondence.py:113-117`); coordinate ownership is untouchable. Hence the ONLY ways to run a fit with a resolved ulna are re-authorings of radius's landmarks:
  - **U-STR** (X = elbow_R + 5.116 mm toward wrist, direction per C1): radius re-anchors to X→wrist_R. New span 0.064745 − 0.005116 = 0.059629 m; new s = 0.059629/0.292029 = **0.20418**; det(R) = s³ = 0.008513; mass transport 0.729 × 0.008513 = 0.006206 kg (from 0.007944 kg) — closed forms DER §9. The rigid part G is unchanged (the axis direction is the same line; the roll witness family is unchanged), so `rotation` survives and `scale`/`t`/site globals change.
  - **U-ANA** (ulna.P_d = wrist_R): closure demands `radius.P := wrist_R`; then `‖radius.P_d − radius.P‖ = 0` → the axial-degenerate branch (`compiler.py:159-167`): the radius loses its fitted scale entirely — 16+16 radius sites unplaced, the packet's only fully-resolved functional forearm chain (BRD; TASK_BOARD A7 fact) re-breaks, and the known-good record reverts to unresolved-class. If radius keeps `elbow_R`, the fit REFUSES outright (sep 6.47e-2 m ≫ 1e-9). There is no pack joint distal of the wrist to re-anchor radius.P_d to (B3 §2.2, E5).
- **Why necessary:** the hierarchy law leaves no alternative — this is B3's F-2 partition ("the two edges PARTITION the elbow→wrist span once ulna is resolved", B3 §6 F-2) and F-4's supersession discipline, now with the exact code path and the per-candidate arithmetic. Not executing the supersession is not an option under a resolved ulna; it is the same fact as F1.

### 6.3 What it does NOT change

- The frozen session-5 baseline (`baseline_snapshot/`, MANIFEST `c70b7a6c` head) stays byte-identical, forever, as history; supersession exists only in a FUTURE append-only revision with its own hashes (B1 §3.2 digest discipline; ERRATA law).
- Wave-1/2 receipts remain true statements about the recorded fit ("valid FOR THE RECORDED FIT", B3 F-4).
- Site ownership (T1), coordinate ownership, tree parentage, the admission split's class law, and the 28-joint pack are untouched.
- **Authorization status: NOT AUTHORIZED.** Per the addendum this proposal requires Astra's explicit acceptance BEFORE any revision exists; until then it is a consequence map, not a plan of action.

---

## 7. FINDINGS AGAINST THE MAP (independent-challenge results)

1. **Roll-table "perp" numbers are |p| relabels (REPRODUCIBILITY GAP).** MAP §2.1: ECU-P2 "perp 0.0448", ANC-P2 "0.0260", TRIlat-P5 "0.0243". Measured: ANC-P2 0.026047 and TRIlat-P5 0.024283 ARE the sites' |p| from the ulna origin (4-decimal matches); ECU-P2's |p| = 0.045679 matches neither the map's 0.0448 nor any axis perp (0.0196/0.0188). §1's "ECU-P4 perp-off-axis 0.1015 m" is likewise unreproduced under every natural axis (measured: 0.0694 to the U-STR axis; 0 by definition to its own; 0.0301 to the ulna→hand line). T2 is unaffected (all true witnesses ≫ 1e-9), but the table's column label is wrong and one number matches nothing measurable in the snapshot. Corrected values are in `decision_table.md` and C3-S1.
2. **The MAP's target-side roll witness is undeclared for the ulna edge** (all candidates): a roll ref needs a target landmark; none is named. The only existing machinery (elbow-band vertex) is already the radius edge's construction input — reusable only as DEPENDENT evidence (§2.5).
3. **The MAP's ulna entry falsifier is void for U-ANA as written**: it fires on ECU-P4's fitted placement, which is U-ANA's own construction input (§2.2) — the architect's prohibition, encountered at ECU-P4 exactly as at ECU-P2.
4. **U-ANA's mechanical consequence is more drastic than "overlap"**: it forces the radius edge to zero span (refusal or axial-degenerate; §6.2) — the known-good radius record is not merely re-anchored under U-ANA, it is eliminated. Stated as a mechanical consequence inventory (freeze law); per T6 it is NOT a preference and must not be used as one.
5. **The 5-site "palm-plane" alternative is measured-dead** (70.3° / 54.1 mm rms refutation, §4.2) — preserved as rejected.
6. Minor: the C2/C3 briefs' "ECBR-P4" is a typo for `ECRB-P4` (XML L664); no artifact affected.

---

## 8. STEP 5 — SMALLEST MISSING MEASUREMENTS (per unresolved cell)

| gap (owner) | smallest measurement that closes it | class |
|---|---|---|
| Ulna roll SIGN / anatomical label (both authorings) | ONE anatomical identification of the target forearm: which transverse side is volar (or hairy/padded) at one axial — a single rendered image of the elbow→mid-forearm region read by the operator/vision terminal; pairs with the measured camber (−174° ± 5°) or bulge line (−112° ± 10°) to kill the 180° flip | EXTERNAL (visual), one fact |
| Ulna target roll witness declaration (map gap) | one authored declaration naming the target Q (band-vertex family accepted as authored skin evidence), or the visual identification above converted to a named mesh point | authoring + EXTERNAL |
| U-STR axis direction (C1 owns; C3 parameterized) | C1's verbatim-axis resolution (already scoped: the source vector is 62.1° lateral, C3-S1) | source-internal |
| U-STR vs U-ANA separation | an external proportion fact: macaque proximal radioulnar offset as a fraction of forearm length, compared to the source's 0.023075/0.30579 = 7.5 % (elbow→hand, C3-S1) — the only ulna-length evidence that is not circular, since no target measurement can see inside the skin (B1 §4.1) | EXTERNAL (cited), one fact |
| U-ANA scale independence | nothing measurable in the target; same external proportion fact as above is the only non-circular referent | EXTERNAL |
| Hand roll SIGN | one visual identification of the paddle's palm face (image of the paw region), or acceptance of an authored sign | EXTERNAL (visual), one fact |
| H-LEN/H-ASP scale independence | an external macaque hand-length proportion (paddle:forearm vs source skeleton:forearm); C2's EXTERNAL lane already scopes this | EXTERNAL (cited) |
| H-ASP width homolog | C2's source-palm ↔ paddle-width identification (its step-2 table) | C2 |
| Paddle same-assembly (frames H-LEN/H-ASP/H-BODY equally) | C2's lobation/segmentation measurement | C2 |

Total: TWO visual identifications (forearm side, paddle face) + ONE external proportion citation close every orientation/validation gap that C3 can see; everything else is authoring acceptance (Astra's).

---

## 9. RECEIPTS (exact commands; full logs in `receipts/`)

| receipt | command | key output |
|---|---|---|
| `c3_source_geometry.json` + `_run.log` | `cd …/C3_independent_challenge && PYTHONDONTWRITEBYTECODE=1 python scripts/c3_source_geometry.py` | \|ulna→radius\| 0.023075 m at 62.10° to the limb axis; roll witnesses 0.0196/0.0255/0.0235 (U-STR) · 0.0188/0.0250/0.0235 (U-ANA); roll azimuth separations 46.06°/63.46°; TRI triplet identical; hand planes: 70.33° between 27-geom and 5-site normals; direction A rms 8.88 ≤ 10.66 mm; direction B 54.13 mm = 25.4×; jackknife 1.67°/11.05°; origins reproduce A4 exactly |
| `c3_target_sections.json` + `_run.log` | `PYTHONDONTWRITEBYTECODE=1 python scripts/c3_target_sections.py` | input hashes == MANIFEST (birth 550a5b3e…, pack 74b3ab04…); tube ecc 1.16–1.40 (boot IQR > 1); principal line −112° ± 10°; camber 6.6–7.7 mm at −174° ± 5° (boot ±4.8–6.5°); band extreme −111.9° (top-10 span ±11°, top-2 gap 1.001); paddle flat line ±0.7–1.1°, ecc 14–31; L/R exact mirrors |
| `brief.md` | copied verbatim as the first action | frozen preregistration (prediction + falsifier) predates all runs |

## 10. BASELINE INTEGRITY

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)                                    <- run at start (after brief.md copy) and at end
HEAD: 276db875
```
All C3 writes confined to `forearm_package/audits/C3_independent_challenge/` (brief.md, report.md, decision_table.md, scripts/, receipts/, work/). Baseline modules executed only via the byte-identical copy `work/mesh_target_c3.py` with paths repointed to the read-only snapshot; `PYTHONDONTWRITEBYTECODE=1` throughout; no git writes; no network.

## 11. PRESERVED ALTERNATIVES AND NEGATIVE RESULTS (they are results)

1. R-hand-B (5-site palm-plane construction): REJECTED on measurement (§4.2) — preserved with numbers.
2. The ulna tube's signed camber as a sign-fixer: measured, stable, but anatomically UNLABELED — preserved as a candidate determinant awaiting the one visual fact (§8), not adopted.
3. The band-vertex roll witness: coherent bulge direction (±11°) but argmax knife-edge (gap 1.001) and skin-unlabeled; already DEPENDENT for the ulna edge (consumed by radius) — preserved as rejected for independent-validation duty.
4. H-BODY's independent paddle test: PASSES placement and still validates nothing about its scale (circular by construction) — preserved.
5. No moment arm, tendon length, or transmission quantity was computed anywhere in this audit (T6 discipline); the mass numbers quoted are the map's/DER §9 closed-form det(S) arithmetic, cited not recomputed as evidence.
6. STOP RULE: all six acceptance criteria have verdicts; no dependency missing (C1's direction question was parameterized around, not blocked on). Stopping here.
