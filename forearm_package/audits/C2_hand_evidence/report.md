# C2 — HAND ANATOMICAL EVIDENCE: candidate definitions, same-assembly, geometry vs density, mass spread

**Agent:** C2 evidence agent · **Date:** 2026-09-24 · **Wave:** 3 (hand evidence) · **Mode:** read-only evidence + isolated scripts, per the architect's wave-3 laws (BODY_RESOLUTION_MAP ADDENDUM: no candidate chosen, no new fit, no supersession).
**Baseline:** `E:/PythonChimera/forearm_package/baseline_snapshot/` — untouched (§7).
**Brief:** frozen at `audits/C2_hand_evidence/brief.md` (verbatim copy, first action). Preregistration and its verdict: §6.
**Bounded:** no ulna work (C1), no protocol work (C3). Light external search kept separate in §9.

---

## 0. ACCEPTANCE-CRITERION VERDICTS

| # | Criterion | Verdict |
|---|---|---|
| 1 | Three precise anatomical definitions quoted/cited | **PASS** (§1) |
| 2 | Source-hand + target-paddle measurement tables with numbers | **PASS** (§2) |
| 3 | Same-assembly verdict + deciding evidence (or smallest missing measurement) | **PASS** — UNDECIDABLE-WITH-CURRENT-ASSETS, deciding numbers + smallest missing measurement stated (§3) |
| 4 | Mass-spread arithmetic shown exactly, no preference stated | **PASS** (§4) |
| 5 | Digits-reclassification assessment | **PASS** (§5) |
| 6 | Baseline integrity — git status on baseline_snapshot empty | **PASS** (§7) |

---

## 1. THE THREE CANDIDATES AS PRECISE ANATOMICAL CLAIMS (criterion 1)

Quoted from `BODY_RESOLUTION_MAP.md` §2.2 (the candidate table; emphases mine). Common to all three: **P (proximal): "`body_origin:hand_r` ↔ target `wrist_R`. Closure-clean (wrist already equals `radius.P_d`; anchor gap 0.0). (No choice needed.)"** — so every candidate is a claim about the DISTAL anchor + scale policy only.

### 1.1 H-LEN (length-matched, uniform)

Map, verbatim: claim — **"the hand maps onto the whole paddle, uniform scale"**; P_d source ref — "`3distph` geom (0.1554 m)"; P_d target ref — "paddle far-end point (0.1113 m; B1 v3 max-extent voxel)"; implied scales — "s = 0.716 uniform (3.2× body scale — flagged)".

**Anatomical content:** (i) the paddle's far end IS the homolog of the source's distalmost fingertip bone-anchor (`3distph`); (ii) ONE isotropic scale (s = 0.716) relates source hand and target paddle, i.e. every internal structure of the source hand (carpal rows, metacarpal rows, four splayed fingers, opposable thumb — 27 distinct bones) is asserted to have a corresponding structure in the paddle at 0.716× its source offset from the wrist. The map's own uncertainty row states the cost: "target-hand proportion is 3.2× the source's (paddle 111 mm on a 64.7 mm forearm vs source 155 mm on a 315 mm forearm) — honest mismatch, stated not hidden."

### 1.2 H-ASP (length + aspect)

Map, verbatim: claim — **"length matches the paddle; width/thickness match the paddle cross-section"**; same source ref `3distph` (0.1554 m) and same length scale s_a ≈ 0.716 as H-LEN, plus "s_b ≈ 0.0471/0.061 ≈ 0.77; s_c ≈ 0.0181/0.020 ≈ 0.90 — locally coherent ~0.72–0.90".

**Anatomical content:** (i) same distal assertion as H-LEN (far end ↔ fingertip homolog, for LENGTH); (ii) ADDITIONALLY, the paddle's far-end transverse cross-section (47.1 mm × 18.1 mm, B1 v3) is asserted to be the homolog of the source PALM cross-section (61 mm width × 20 mm thickness) — the width homolog pair is (paddle far-end slab, source palm at the metacarpal row). The map itself flags this: "width landmarks are paddle-derived approximations of palm homologs." Note the internal tension, stated not resolved: the length anchor puts a FINGERTIP at the far end while the width anchor puts PALM cross-section there; the candidate is coherent only under the reading that the paddle's distal slab is palm-like in width (i.e., the mapping treats the paddle as palm-dominated), which is an anatomical claim about the paddle's contents, not a measurement of them.

### 1.3 H-BODY (body-scale)

Map, verbatim: claim — **"the hand keeps the body-wide scale"**; P_d source ref — "any ref at 0.0344 m distal (e.g., authored knuckle-line landmark — the image of the fingertip under body scale)"; P_d target ref — "authored point 0.0344 m distal of wrist along the axis"; s = 0.2217 uniform.

**Anatomical content:** the WEAKEST claim — it asserts only that source hand and target paddle are homolog AS WRIST-DISTAL REGIONS, and makes NO claim identifying any paddle structure: the fitted hand ends at an AUTHORED point (0.0344 m, verified = 155.29 mm × 0.2217 = 34.4 mm, receipt `mass_arithmetic.txt`), explicitly "the image of the fingertip under body scale", not a measured paddle feature. The paddle's far end is left ANATOMICALLY UNIDENTIFIED. The map's uncertainty row: "fitted hand occupies only the proximal third of the paddle; terminal tendon sites sit near the wrist."

**Roll ref (all three, verbatim):** "the palm-plane normal — target: the paddle's flat normal (18.1 mm thickness direction...); source: the metacarpal/phalanx spread plane... **Declared homolog: paddle-flat ↔ source palm-plane.**" — my §2 measurements qualify this declared homolog (source palm is near-planar, RMS 5.0 mm, but the full 27-point skeleton is NOT, RMS 10.7 mm).

---

## 2. SAME-ASSEMBLY EVIDENCE, BOTH SIDES (criterion 2)

All numbers measured this audit; receipts in `receipts/` (exact commands §8). Source limit stated up front (B1 §5.4, confirmed): the 27 skeleton MESH assets are external; every source length below is bounded by authored geom POS anchors, not mesh surfaces.

### 2.1 SOURCE — the 27-geom welded hand (`hand_r`; hand_l exact mirror per B4)

| measure | value | note |
|---|---|---|
| mesh geoms parsed | 27 (+3 capsules skipped) | 8 carpals, 5 mc, 14 phalanges |
| hand length (wrist→distalmost anchor) | **155.29 mm** (`3distph` at \|p\|=155.29) | frozen evidence ≈0.1554 m ✓ |
| distal anchors \|p\| | 155.29 / 152.00 / 145.36 / 130.65 mm (rays 3/2/4/5); thumb 103.80 | fingers splay in a fan |
| palm width (H-ASP s_b denominator) | **60.89 mm** (x-extent 5mc→thumbprox = −17.90..+42.98) | map's "0.061" ✓; 5mc-only extent is 44.39 mm; ALL-27 x-extent 84.64 mm |
| palm thickness (H-ASP s_c denominator) | **20.19 mm** (mc-row z-extent) | map's "0.020" ✓ |
| thumb vs finger axis | **41.7°** (wrist→thumbdist vs mean wrist→{2..5}distph); ray-axis divergence 36.0° vs ray 3 | thumb is strongly divergent; rays fan 7.0°/8.8°/15.6° (2/4/5 vs 3) |
| best-fit plane, ALL 27 pts | RMS residual **10.66 mm**, max 28.61 mm | the full skeleton is NOT planar |
| best-fit plane, carpals+mc (13 pts) | RMS **4.99 mm**, max 8.72 mm | the PALM proper is near-planar |
| best-fit plane, 14 phalanges | RMS 11.95 mm, max 23.40 mm | phalangeal anchors arch off-plane |
| 5 hand sites plane | RMS **2.13 mm**, max 3.41 mm | map's "5 hand sites are near-coplanar" ✓ |
| digit-ray lengths (mc→dist anchor chain) | thumb 67.0; 2: 96.4; 3: 100.2; 4: 89.1; 5: 78.6 mm | 5 DISTINCT ray lengths — digit-differentiated structure on the source side |
| forearm elbow→hand origin | **0.30579 m** straight-line; **0.31510 m** chain-sum (0.02307+0.29203) | both brief values reconciled: 0.306 = straight-line, 315 = chain-sum (map's usage) |
| authored mass | 0.4575 kg (inertial pos 0 −0.068095 0) | ✓ frozen evidence |

### 2.2 TARGET — the paddle (`monkey_birth.bin`, baseline copy; B1's loader)

Side R measured; side L numerically identical (exact mirror — all 29 slab rows match to 0.1 mm with z-sign flip).

| measure | value | note |
|---|---|---|
| forearm elbow→wrist | **64.745 mm** | ✓ frozen evidence |
| paddle length | **111.3 mm** (r<25 mm tube) / **111.4 mm** (r<40 mm) | ✓ B1 v3 (111.3–111.4) |
| paddle:forearm ratio | **1.7184 / 1.7198** | prereg's 1.72 ✓ |
| width profile along axis (b1 extent) | 23 mm @wrist → 35 @16-20 → 46 @28 → 61 @36 → **max 76.4 @48** → 74 @56 → step down to **49 @60** → 44–47 CONSTANT 60–108 mm → 41.9 @108 | NOT a gradual taper: mid-length bulge, then a constant-width distal band over ~48 mm |
| thickness profile (c1 extent) | 18–20 mm proximal half → 12–14 @72-96 → 6.9 @108 | monotone-ish thinning toward the far end |
| far-end (80–115 mm) transverse extents | **47.1 × 18.1 mm** | ✓ B1 v3 exactly |
| cross-section asymmetry | centroid b-offset −17..+16 mm (side-biased: −8..−9 mm through the distal band), c-offset +0.7..+14 mm | mild, smooth, no alternating lobes; mirror-consistent on L |
| paddle PCA axis vs elbow→wrist axis | **10.3°** | map falsifier (a) threshold 15° — NOT fired |
| lobation (ii) angular r(θ) grooves, distal half (55–115 mm, 24 bins, 12 slabs) | **persistent (≥20 mm span) angular minima: NONE** | prereg falsifier "≥2 grooves consistent over ≥20 mm" NOT fired |
| lobation (i) width-profile minima | 3 minima; best persistence 52 mm is a broad flat band (44.6 mm @74), NOT a groove; the sharp dip @84-86 mm spans <8 mm | see controls below |
| lobation (iii) cross-section splits @6 mm gap | 9/14 distal slabs "split" | **UNINFORMATIVE: control (a) below** |
| voxel components (axial>30, r<35) | 8 mm: 1 component (165 voxels, ✓B1); 4 mm: 1 (490); 2 mm: 61+53+43+... fragmented | 2 mm fragmentation = vertex-sampling artifact, not anatomy (surface cloud, not watertight volume) |

**Controls (`target_paddle_controls.txt`) — three apparent-structure candidates tested and rejected:**

1. **Split-test control:** the SAME 6 mm-gap split test on the PROXIMAL half (15–50 mm — certainly single-bodied) splits **4/9 slabs**. Slab vertex spacing is 12–24 mm median, i.e. coarser than the 6 mm threshold → the distal "splits" are sampling artifacts. At 10 mm gap: 1/14; at 14 mm: 0/14. No persistent deep cleft exists.
2. **The 84 mm "groove":** fine 2 mm slabs show n=7–9 verts in the dip slabs vs n=45–47 in neighbors — 7–9 points cannot represent a 47 mm-wide cross-section. Sparse-slab artifact, not a groove.
3. **2 mm voxel fragmentation:** vertex-cloud occupancy below ~4 mm is below sampling density; fragmentation is a resolution artifact (B1 §5.3 already flagged this class).

### 2.3 Proportions (step 2c)

| ratio | value |
|---|---|
| source hand:forearm (155.29 / 315.10 chain-sum) | **0.4928** |
| source hand:forearm (155.29 / 305.79 straight-line) | 0.5078 |
| paddle:forearm (111.3 / 64.745) | **1.7184** |
| ratio-of-ratios | **3.49×** (chain-sum) / 3.38× (straight-line) |

Preregistration's "0.49 and 1.72, ~3.5×" — CONFIRMED (0.49 is the chain-sum reading; the map's "155 on 315" matches).

---

## 3. SAME-ASSEMBLY VERDICT (criterion 3)

**Verdict: UNDECIDABLE-WITH-CURRENT-ASSETS.**

**Deciding numbers.** Supporting common identity: both assemblies are single continuous wrist-distal structures (source: 27 bones welded in ONE rigid body, zero digit joints; target: one connected component at 8 mm and 4 mm voxels), both axial (paddle PCA 10.3° from the forearm axis — within the map's own 15° falsifier), both wrist-anchored with gap 0.0 (B3/B4). Contradicting/refusing decision: (i) proportions differ **3.4–3.5×** (1.718 vs 0.493–0.508) — under ANY single scale the paddle is proportionally far longer than a hand; (ii) the paddle exhibits **zero digit-distinguishable structure** at current sampling (no ≥20 mm angular grooves; splits and dips proven artifactual by controls) — so the presence of 5 fused rays CANNOT be confirmed; (iii) the source side cannot be measured beyond geom anchors (mesh assets absent — true hand length, palm width as a SURFACE, unknown); (iv) the pack itself does not claim the region: past ~41 mm the skin binds to tail_base/spine_lower (B1 §2.2), and B1 §5.1 could not exclude non-hand skin inside 40–111 mm.

**Smallest missing measurements** (each sufficient, in increasing effort):
1. **One imaging fact — render/inspect the wrist-distal blob.** A single visual inspection of the existing mesh region (0–111 mm distal, the blob at x≈0.168–0.199 m) would establish whether it is visually a hand/mitt (palm pad + fused digit masses) or includes mis-bound non-hand skin. Neither B1 nor C2 could render images; this is the single cheapest decisive observation and it uses ONLY current assets.
2. The source hand MESH assets (carpals/metacarpals/phalanges surfaces) — would convert every source measure from anchor-bounded to true-surface, fixing the source hand length the 155.29 mm anchor only bounds.
3. A watertight (voxelized-volume) or higher-vertex resolution of the target region — would make the digit-lobation tests decisive in the NEGATIVE direction too (current absence of grooves is sampling-limited, not proven; median slab vertex spacing 12–24 mm vs digit-groove scales ~2–8 mm).

---

## 4. MASS SPREAD — GEOMETRY SEPARATED FROM DENSITY (criterion 4)

Receipt: `mass_arithmetic.txt` (exact reproduction below). Closed form, DERIVATION §9 verbatim: **"m' = m · |det L| = m · det S (proper rotations have det +1)"**; uniform check: "Uniform `S = s·I₃`: `m' = s³ m`".

| candidate | S (inputs, all measured) | det S | m′ = 0.4575·det S |
|---|---|---|---|
| H-LEN | s = 0.1113/0.15529 = 0.716724 (uniform) | s³ = 0.368176 | **0.16844 kg → 0.168** |
| H-LEN (map's frozen rounding) | s = 0.1114/0.1554 = 0.716860 | 0.368386 | **0.16854 kg → 0.169** |
| H-ASP | diag(0.716724, 0.0471/0.06089 = 0.773526, 0.0181/0.02019 = 0.896483) | 0.497014 | **0.22738 kg → 0.227** |
| H-ASP (map's rounding 0.716×0.77×0.90) | | 0.496188 | 0.22701 kg → 0.227 |
| H-BODY | s = 0.221707 (uniform; map rounding 0.2217 identical to 4 dp) | s³ = 0.0108978 | **0.004986 kg → 0.0050** |

- **Zero residual:** each reported value (0.0050 / 0.169 / 0.227 kg) equals m·|det S| under its candidate's S to the printed precision; the only deviations are the map's own 2–3-decimal roundings of s (e.g. 0.716 vs 0.71686 → 0.1679 vs 0.1685). The 0.168-vs-0.169 difference between the map table and this audit is solely the 0.1113-vs-0.1114 paddle-length choice — bookkeeping, not discrepancy.
- **The spread is pure scale-policy:** max/min = 0.2270/0.0050 = **45.5×**; the corresponding det ratio 0.496188/0.0108968 = **45.5×** — identical to the last digit. H-ASP/H-LEN = 1.347 = s_b·s_c/s². No density, no material, no target-mesh mass enters anywhere.
- **None is a measurement.** The shipped packet carries NO hand mass at all: `unresolved_segments[hand_r] = {"body": "hand_r", "reason": "no fitted scale (axis source missing; not silently repaired)", "axes": {"axial": "declared_unresolved", "b": "none", "c": "none"}}` — no mass field. The three numbers exist only in BODY_RESOLUTION_MAP §2.2 as PROSPECTIVE authoring outcomes.
- **All would carry the density flag.** Quoted verbatim from `runs/admission_actual_monkey.json` → `admission.mass_admission`: assumption `uniform_constant_density_scale`, kind `source_effective_x_det_scale`, `requires_density_validation: true`, `density_validated: false`, note: **"a transported mass is the source effective mass scaled by |det D| under a RECORDED constant-density assumption. Geometry resolution alone does NOT discharge requires_density_validation; no body is physically admitted because no validated material/mass source was supplied and none is invented."** Counts: `physically_admitted: 0`; hand_r/l in `unresolved: 9`.
- Cross-checks of the map's other arithmetic rows (same receipt): fingertip image 155.29×0.2217 = 34.4 mm = map's "0.0344 m" ✓; sites 0.0299–0.0428 m → 0.0214–0.0307 (H-LEN, map "2.1–3.1 cm") ✓ and 0.0066–0.0095 m (H-BODY, map "0.7–0.9 cm") ✓.

**STATEMENT, PLAIN: current evidence prefers NO mass.** All three values are the same authored 0.4575 kg pushed through three different scale POLICIES under one unvalidated density assumption; nothing measured in this audit (nor in the baseline) distinguishes their plausibility as masses. (Falsifier check: no current-evidence basis for preferring one mass was found — expected none; none exists.)

---

## 5. DIGITS RECLASSIFICATION ASSESSMENT (criterion 5)

Measured answer: **the paddle's geometry contains NO digit-distinguishable structure resolvable with current assets.** Quantified: 0 angular minima persistent ≥20 mm in the distal half (the preregistered falsifier for digit lobation); width "grooves" do not survive controls (proximal-half control splits too; dips are 7–9-vertex slabs; splits vanish at 10–14 mm gaps); single component at 8 mm AND 4 mm voxels. The distal band is a constant-width (44–47 mm), gradually thinning (13→7 mm) slab — a mitt, not separated or grooved rays.

Implication, conditional language only, no mapping proposed:
- The architect's reclassification — "permanently unmappable" → **"unmappable under the current assets and correspondence contract"** — is CORRECTLY supported by this evidence, and the conditionality is load-bearing on BOTH sides of the "under":
  - **Better TARGET assets could change the structure answer.** IF a higher-resolution or watertight rendition of the same region were supplied, the lobation tests above become decisive in BOTH directions: digit-distinguishable structure, if it exists below current ~12–24 mm sampling, would show as ≥2 grooves stable over ≥20 mm (the frozen falsifier) and the paddle could then be assessed as hand-with-fused-rays rather than featureless mitt. Current evidence cannot assert that absence is anatomical (it is resolution-limited), which is exactly why "unmappable under current assets" (not "permanent") is the right class.
  - **No asset change can change the articulation answer.** Zero digit joints exist in the source (27 welded bones; B1 §1.3) AND zero in the 28-joint pack — `absent_in_source` for articulation is asset-independent. Better meshes can reveal SHAPE structure; they cannot create transmission.

---

## 6. PREREGISTRATION VERDICT (frozen in `brief.md` before any measurement)

| prediction | outcome |
|---|---|
| same-assembly UNDECIDABLE with current assets | **CONFIRMED** (§3) |
| proportions differ ~3.5× (source 0.49, paddle 1.72) | **CONFIRMED** — 0.4928 (chain-sum) / 0.5078 (straight-line); 1.7184; ratio 3.38–3.49× |
| mass spread fully accounted by det(S) arithmetic, zero residual | **CONFIRMED** — spread 45.5× = det ratio 45.5×, exact to rounding (§4) |
| paddle shows at most gradual taper without digit structure | **CONFIRMED with one refinement** — the profile is NOT a gradual taper: mid-length bulge (76.4 mm @48 mm) then constant-width distal band (44–47 mm over ~48 mm); still zero digit structure |
| FALSIFIER: stable digit-like lobation (≥2 grooves ≥20 mm) ⇒ report supported-with-structure | **NOT FIRED** — 0 persistent angular grooves; apparent splits/dips proven artifactual by controls (§2.2) |
| FALSIFIER: any current-evidence basis for preferring one mass | **NOT FIRED** — none exists (§4) |

---

## 7. BASELINE INTEGRITY (criterion 6)

Run first action and re-run after all work:

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)
```

Empty both times. All scripts read the snapshot read-only; module copies live in `audits/C2_hand_evidence/work/`; `PYTHONDONTWRITEBYTECODE=1` throughout; no git writes; all outputs inside `audits/C2_hand_evidence/`.

---

## 8. RECEIPTS (exact commands + key outputs; logs in `receipts/`)

| receipt | command | key output |
|---|---|---|
| `source_hand_measures.txt` | `PYTHONDONTWRITEBYTECODE=1 python scripts/c2_source_hand.py` | 27 geoms; 155.29 mm; 60.89/20.19 mm denominators; 41.7° thumb; plane RMS 10.66/4.99/2.13 mm; forearm 0.30579/0.31510 m; ratios 0.4928/0.5078 |
| `target_paddle_measures.txt` | `PYTHONDONTWRITEBYTECODE=1 python scripts/c2_target_paddle.py` | 64.745 mm forearm; 111.3/111.4 mm; 1.7184 ratio; slab profiles; PCA 10.3°; 0 persistent grooves; voxel components 1/1/fragmented; far end 47.1×18.1 mm; L-side identical (mirror) |
| `target_paddle_controls.txt` | `PYTHONDONTWRITEBYTECODE=1 python scripts/c2_paddle_controls.py` | control splits 4/9 proximal; 9/14→1/14→0/14 at 6/10/14 mm; 84 mm dip n=7–9; slab nn spacing 12–24 mm |
| `mass_arithmetic.txt` | `PYTHONDONTWRITEBYTECODE=1 python scripts/c2_mass_arithmetic.py` | 0.16844/0.16854/0.22738/0.004986 kg; spread 45.5× = det ratio; admission note quoted; packet hand_r record (no mass) |

## 9. EXTERNAL CONTEXT (class EXTERNAL — kept separate; NOT source-internal evidence)

Light WebSearch for macaque hand-proportion facts returned only QUALITATIVE context; no numeric hand:forearm ratio was obtainable within the light budget (PubMed abstract blocked by cookie wall) — null result recorded: — macaques' hands are described as "more 'human-like', with short fingers and a relatively long opposable thumb" (Vanhoof et al. 2020, [PMC](https://pmc.ncbi.nlm.nih.gov)); rhesus hand musculature "largely parallels human anatomy" (Casteleyn 2024, [MDPI](https://www.mdpi.com)); related: [Almécija et al. 2015](https://www.nature.com). No EXTERNAL number enters any verdict above; the proportion anomaly (§2.3) stands on source-internal numbers alone.

## 10. REJECTED / UNRESOLVED ALTERNATIVES (preserved per the freeze law)

- **H-ASP denominator alternative (rejected as NOT the map's reading, recorded for sensitivity):** if palm width were the 5mc-only x-extent (44.39 mm), s_b = 1.061, det = 0.683, m′ = 0.312 kg — a FOURTH value; the map's 0.227 requires the mc+thumb-column reading (60.89 mm ✓). The H-ASP mass is denominator-sensitive; another reason it is policy, not measurement.
- **Forearm-definition alternative:** 0.30579 straight-line vs 0.31510 chain-sum — both preserved; ratios 0.508/0.493; does not affect any verdict.
- **84 mm groove (rejected as artifact):** control (c), §2.2.
- **6 mm-gap cross-section splits as digit evidence (rejected as sampling artifact):** control (a), §2.2.
- **2 mm voxel fragmentation as digit separation (rejected as sampling artifact):** §2.2; consistent with B1 §5.3's resolution caveat.
- **UNRESOLVED (carried forward):** anatomical identity of the 40–111 mm blob (needs §3 measurement 1); true source hand mesh extents (needs §3 measurement 2); cause of the pack's distal ownership anomaly (B1 §5.2, outside baseline); whether the paddle's true surface contains sub-sampling digit grooves (needs §3 measurement 3).

**STOP RULE:** all six criteria have verdicts; no dependency missing. Stopping.

Sources: [Vanhoof et al. 2020 (PMC)](https://pmc.ncbi.nlm.nih.gov) · [Casteleyn 2024 (MDPI)](https://www.mdpi.com) · [Almécija et al. 2015 (Nature)](https://www.nature.com)
