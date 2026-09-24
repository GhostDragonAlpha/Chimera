# I6 — ANATOMICAL DECISION TABLE (ulna + hand correspondence determination)

**Status: EVIDENCE COMPLETE — DECISION REQUESTED. No candidate is chosen here; no fit, production mapping, or supersession is authorized or executed.**
**Laws honored (architect, 2026-09-24):** anatomical validity is the only selection criterion (scale/mass/tendon-coverage convenience cannot choose); construction inputs never validate; evidence/uncertainty/criteria/falsifiers were frozen before comparison (each agent's brief.md); all rejected and unresolved alternatives preserved; zero moment-arm or utility numbers computed anywhere in wave 3.
**Evidence base:** C1 (ulna), C2 (hand), C3 (challenge) — every receipt coordinator-re-verified; baseline integrity clean throughout.

---

## 1. THE DECISION TABLE

### Ulna edge

| | **U-STR (structural)** | **U-ANA (anatomical span)** |
|---|---|---|
| **candidate definition** | P `body_origin:ulna` ↔ `elbow_R`; P_d `body_origin:radius` ↔ authored point 5.116 mm along elbow→wrist (s_a = 0.2217) | P same; P_d `site:ECU-P4` (0.10276 m) ↔ `wrist_R` (s_a = 0.630) |
| **source evidence** | verbatim chain: ulna pos `0.0061 -0.34845 -0.0123`; ulna→radius +14.32 mm axial / +18.09 mm lateral (23.07 mm, **51.63° oblique, coronal**); the 2.31 cm segment is a **kinematic fragment** (elbow-hinge piece; forearm length carried by radius→hand 292 mm; ulna inertial CoM at 120.5 mm — **byte-identical to radius's: source copy-paste defect**) [C1] | same geometry, read as anatomical span; **but ECU-P4 is an interior tendon waypoint 32 % down the forearm, not a distal endpoint** [C1] |
| **target evidence** | `elbow_R` anchor gap 0.0 [B3/B4]; distal point is authored (no pack joint there — schema explicit-coordinate check pending) | `wrist_R` anchor gap 0.0 [B3/B4] |
| **scale derivation** | s = 0.005116/0.02307 = 0.2217 by construction. **Consequence (C3): forces radius re-anchor to s = 0.20418** | s = 0.064745/0.10276 = 0.630 (2.8× body scale). **Consequence (C3): forces radius span → 0 — axial-degenerate REFUSAL (`compiler.py:159-167`) — the known-good radius record is ELIMINATED, not re-anchored** |
| **roll derivation** | candidates materially distinct (46.06°/63.46° azimuth separations) [C3]; corrected offsets: ECU-P2 axis perps 0.0196/0.0188 m (map's 0.0448 was wrong); **target-side roll witness UNDECLARED for every candidate** — the only machinery (elbow-band vertex) is the radius edge's own construction input (DEPENDENT) [C3] | same witness gap |
| **independent validation** | **10/10 PASS** (all 10 sites independent — construction uses body origins only): every site in anatomical region, layout reproduced ≤ 8.8 points of forearm length [C1]; TRI*≡olecranon, BRA≡tuberosity, ANC≡proximal-posterior, PT≡coronoid, ECU≡monotone distal 11.5→32.1 % | **6/9 FAIL** (+7 to +42 points out of region) [C1]; the anchor itself is circular as validation [C3]; the map's own ulna falsifier was circular for U-ANA as written [C3] |
| **remaining ambiguity** | roll SIGN (the tube is not symmetric — eccentricity 1.16–1.40, camber 6.6–7.7 mm, L/R mirror-exact — but no source- or target-internal dorsal/volar labeling exists; a 180° flip remains) [C3]; radius-supersession acceptance (s → 0.20418) | closes only if new evidence contradicts C1's region analysis; on current evidence this candidate is **REJECTED on three independent grounds** (region failures, circular anchor, radius-record elimination) — preserved as an alternative, revivable by evidence |
| **status** | **VERDICT-READY PENDING ROLL SIGN** + supersession acceptance | **REJECTED on current evidence** (Astra's call) |

### Hand edge

| | **H-LEN (length-matched)** | **H-ASP (length+aspect)** | **H-BODY (body scale)** |
|---|---|---|---|
| **candidate definition** | paddle far-end = `3distph` fingertip homolog; uniform s = 0.716 | H-LEN + paddle far-end cross-section = palm-cross-section homolog; s = (0.716, 0.77, 0.90) | region-homology only; P_d authored at 34.4 mm = 155.29 × 0.2217; uniform s = 0.2217 |
| **source evidence** | hand length 155.29 mm (27 geoms, distalmost `3distph`); palm 60.89 × 20.19 mm; thumb divergence 41.7° [C2] | + palm measured from 5mc→thumbprox extent (internal tension: paddle far-end 47.1 × 18.1 mm ≠ palm 60.9 × 20.2 — stated, unresolved [C2]) | same source facts |
| **target evidence** | paddle 111.3/111.4 mm, far end 47.1 × 18.1 mm, single component [B1/C2]; width profile = mid-length bulge (max 76.4 mm @48 mm) then constant 44–47 mm — **not a taper**; PCA axis 10.3° from forearm axis (map's 15° falsifier passes) [C2] | same | same |
| **scale derivation** | 0.1113/0.15529 = 0.716; mass 0.16844/0.16854 kg | det = 0.716×0.77×0.90; mass 0.22738 kg | P_d manufactured from the scale it would validate — **circular** [C3]; mass 0.004986 kg. **All masses = m·\|det S\| under `requires_density_validation`; the 45.5× spread is pure policy; current evidence prefers NO mass** [C2]; rejected 4th alternative 0.312 kg preserved |
| **roll derivation** | palm-plane: construction from the 27-geom skeleton plane (jackknife ±1.7°) ⊥ validation by the 5 sites (8.88 mm rms ≤ plane's own 10.66 mm) — **the one construction⊥validation pair that works**; reverse direction refuted (skeleton about site-plane: 54.1 mm rms = 25.4×); paddle-flat measured to ±0.7–1.1° [C3] | same | same |
| **independent validation** | **same-assembly UNDECIDABLE with current assets**: source hand:forearm 0.4928/0.5078 vs paddle:forearm 1.7184 (3.4–3.5× mismatch); zero digit structure (apparent grooves proven sampling artifacts) [C2] — the length anchor is not independently validable until assembly is settled [C3] | same + the cross-section homolog tension | circular by construction [C3] |
| **remaining ambiguity** | same-assembly (smallest missing measurements below); roll SIGN (palm face identification); mass unsettable pending density validation | same | same |
| **status** | **UNRESOLVED — blocked on same-assembly evidence** | **UNRESOLVED — blocked + internal tension** | **REJECTED on circularity** (Astra's call; preserved) |

### Orientation (roll) rows

| body | verdict | evidence | closes with |
|---|---|---|---|
| ulna | **AMBIGUOUS — sign only** | tube NOT near-symmetric (C3's own prediction falsified honestly): eccentricity 1.16–1.40 (bootstrap IQR > 1), principal line −112° ± 10°, camber 6.6–7.7 mm at −174° ± 5°, L/R mirror-exact; but no dorsal/volar labeling exists in source or target | ONE visual identification of the forearm's volar side |
| hand | **AMBIGUOUS — sign only** | palm-plane construction⊥validation PASSES (skeleton-plane ↔ sites, 8.88 mm rms; reverse refuted 25.4×) | ONE visual identification of the paddle's palm face |

## 2. CORRECTIONS TO I5 (my own map — honest accounting, additive)

- The map's ulna roll-table "perp" numbers were **|p| relabels** (ANC-P2 0.0260 = |p| 0.026047; TRIlat-P5 0.0243 = |p| 0.024283) and **ECU-P2's "0.0448" matched nothing measurable** (real axis perps 0.0196/0.0188) [C3]. ECU-P4's "0.1015" perp measured 0.0694 to the U-STR axis [C3]; C1's anatomical decomposition (69.4 mm axial-dominant / 30.1 mm) is the corrected reading. The 4.4× figure is 4.4535 kinematic / **4.258 axial / 1.304 transverse** [C1].
- The map's ulna entry falsifier ("ECU-P4 lands outside skin loops") was **circular for U-ANA** — ECU-P4 is U-ANA's construction input [C3]. Void for U-ANA; valid for U-STR (where ECU-P4 is independent).
- TRIlat-P5 ≡ TRIlong-P5 ≡ TRImed-P5 — one authored point serves three triceps heads [C3].
- The brief's PT cell ("mid-distal") was wrong — the ulnar origin of pronator teres is the coronoid (proximal); source geometry agrees with the corrected external fact [C1].

## 3. THE EXACT PROPOSED RADIUS-RECORD SUPERSESSION (NOT AUTHORIZED — proposal only)

**Records superseded in any future authorized revision:** `radius`/`radius_l` `local_to_world` (R, t), `max_world_reconstruction_error_m`, the experiment step-A mirror table, and the A4/B4 receipt set — which remain valid HISTORY for the frozen session-5 baseline (nothing is edited there).
**Mechanism:** first-child joint closure (`compiler.py:399-423`; `JOINT_EPS` 1e-9 at `:47`; refusal at `:422-423`; closure currently SKIPPED only because the parent ulna is unresolved, `:414-417`). Declaring the ulna edge fixes the shared joint point from ulna-side landmarks; the radius record must re-close within 1e-9 — the hierarchy law (F1) leaves no alternative. **Why necessary:** without it, a resolved ulna and the existing radius record would place the same physical joint at two points — a direct F1 violation.
**Consequences by candidate (C3):** U-STR → radius re-anchors at s = 0.20418 (was 0.2217; a 7.9 % change with downstream reconstruction/mirror receipts re-issued in the new revision). U-ANA → radius span collapses to zero → `axial-degenerate` refusal → **the radius record is eliminated**, and with it the only known-good correspondence. This asymmetry is a consequence inventory, not a preference.

## 4. SMALLEST MISSING MEASUREMENTS (everything C3 can see; two upgrade items from C1/C2)

1. **One visual identification of the forearm's volar side** (render/inspect the existing target mesh near the forearm) — fixes the ulna roll sign.
2. **One visual identification of the paddle's palm face** — fixes the hand roll sign.
3. **One external proportion citation** — proximal radioulnar offset as a fraction of forearm length (source = 23.07/305.79 = 7.5 %) — confirms/refutes the oblique-axis geometry against published norms.
4. (Upgrade) **The source ulna mesh asset's distal extent** (one external file) — upgrades the kinematic-fragment verdict to direct bone-surface evidence [C1].
5. (Upgrade) **A render/visual inspection of the distal blob** — the first step of the same-assembly determination [C2].

Items 1–3 are sufficient to make U-STR verdict-ready (with the supersession consequence stated) and leave only the hand's same-assembly question, which item 5 begins.

## 5. WHAT THE EVIDENCE WEIGHS (reported, not decided)

- **U-STR** is the only ulna candidate that survives every independent test on current evidence (10/10 regions; no circularity; supersession is a re-anchor, not an elimination). Its two open items are the roll sign (measurement 1) and the radius-supersession acceptance (an Astra ruling on a 7.9 % scale change).
- **U-ANA** fails on three independent grounds; it is preserved, not erased.
- **Hand scale** is blocked on same-assembly (undecidable with current assets) — no policy can be anatomically validated yet; **no mass is preferred by any current evidence**.
- **Orientation** is one visual pass away for both bodies (construction⊥validation already works for the hand).
- **Digits**: unmappable under the current assets and correspondence contract; structure conditional on better assets, articulation closed under any asset (zero digit joints source+target) [C2].
- Resolving ulna+hand under any surviving candidate makes **12 of 16** grasp-critical tendons evaluable [B2] — partial progress toward grasp, as the architect's ruling counts it.

**Decision requested:** ulna candidate (evidence favors U-STR; U-ANA rejected on current evidence) · accept/decline the radius-supersession consequence · authorize (or decline) the three smallest measurements · hand policy deferred pending same-assembly evidence, or Astra rules on the assembly question directly.
