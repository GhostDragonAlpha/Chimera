# O2 — HAND ORIENTATION: resolve the PALM FACE (source + target) and the hand roll SIGN

**Agent:** O2 (evidence agent, wave 4) · **Date:** 2026-09-24 (resumed after a transient provider failure; brief and preregistration recovered byte-intact)
**Brief (frozen preregistration):** `audits/O2_hand_orientation/brief.md` — read first, followed exactly; thresholds and stop rule untouched.
**Baseline (READ-ONLY):** `E:/PythonChimera/forearm_package/baseline_snapshot/` — untouched (§7); input hashes asserted equal to MANIFEST before every measurement (`birth 550a5b3e…`, `pack 74b3ab04…`).
**Scope discipline (architect, binding):** ORIENTATION ONLY. Hand SCALE, ASSEMBLY correspondence, and PRODUCTION mapping remain BLOCKED and were NOT touched — no scale, correspondence, or production quantity was computed anywhere in this audit (§6).
**Headline result:** **UNRESOLVED SIGN = BLOCKER — independently on BOTH prongs.** The source palm sign fails the frozen compartment-split test (mixed signs), and the target paddle fails the frozen curvature test in every reading (the nominally-exceeding number is a thickness lens + tip rim, not resting-flexion bending; its sign nomination is convex-palm). Per the frozen STOP RULE everything was recorded and the sign was NOT forced.

---

## 0. ACCEPTANCE-CRITERIA VERDICTS (the brief's six)

| # | criterion | verdict |
|---|---|---|
| 1 | per-site signed-offset table with CLEAN flexor/extensor split | **FAIL — recorded.** Table complete (§2.1), construction reproduced from C3 to 0.000e+00 m, but the split is MIXED: FCR-P3 (flexor) lies on the extensor side of the 27-geom plane (−1.99 mm). Falsifier fired → stop rule → source sign UNRESOLVED. |
| 2 | explicit-axis figures (Agg, stated) | **PASS.** `figures/o2_source_plane_views.png` (A: view along +n27, B: view along −n27, view directions printed in the titles; compartments colored; C: signed offsets vs plane with the frozen verdict banner; D: raw-z diagnostic) and `figures/o2_target_paddle_profiles.png` (R/L face + mid-line profiles with chords, frozen window shaded, thickness panels). All matplotlib with `matplotlib.use("Agg")` before pyplot import (stated per receipt). |
| 3 | target palm face identified with curvature numbers + frozen threshold, and/or a cited existing image | **FAIL — recorded.** Full curvature numbers measured (§3): frozen-window sagitta difference D1 = +7.226 mm nominally > 1 mm, BUT (i) the two faces bow APART (+2.12 / −5.11 mm) — a thickness lens, not a bend; (ii) D1's own sign rule nominates the MORE CONVEX face as palm → convex-palm falsifier FIRED; (iii) the bend-consistent mid-line nomination leaves palm-face concavity 0.95 mm < 1 mm (wrong-signed by max-dev); (iv) trimmed-window D1 = −0.31 mm (the nominal number is rim-dominated). Existing images: 4 distinct monkey renders exist, INSUFFICIENT (§4). |
| 4 | the roll SIGN stated as a definite mapping | **FAIL — BLOCKER (not stated, per stop rule).** Both ends of the required mapping (source palm direction ↔ target face) are unresolved independently; no definite mapping exists to state. §5. |
| 5 | explicit statement that scale/assembly/production were untouched | **PASS.** §6: no scale, no assembly-correspondence, no production-mapping quantity was computed or cited as evidence; every measurement above is orientation-only. |
| 6 | integrity receipt | **PASS.** §7: baseline porcelain empty at start and end; input SHA-256s match MANIFEST; module copy byte-identical (SHA `268f139a…`) verified BEFORE reuse; all writes confined to `audits/O2_hand_orientation/`; no git writes; no `__pycache__`. |

**Preregistration verdict (frozen in brief.md): the PREDICTION FAILED — honestly, on BOTH prongs.**
- PREDICTION "clean 2-flexor vs 3-extensor split": **FALSIFIED** — measured 4/1 about the fitted plane (§2.1), jackknife-clean in only 1/27 refits.
- PREDICTION "paddle shows volar concavity > 1 mm (resting flexion)": **FALSIFIED** — the distal slab is a lens/wedge; the palm-nominal face's concavity is 0.95 mm (quadfit) and wrong-signed (+2.12 mm) by classic max-deviation; the frozen difference is driven by the tip rim (trimmed −0.31 mm).
- FALSIFIERS: "any extensor site on the palm side or vice versa (source)" — FIRED (FCR-P3, flexor, on the extensor side; and under the opposite palm assignment FCU-P4 violates at +5.40 mm with ECRL/ECRB on the palm side at −12.3/−14.4 mm). "A convex-palm/flat result (target)" — FIRED (every reading: convex-palm under D1's own sign rule; sub-threshold/flat under the mid-line nomination). Numbers in §2–§4.
- STOP RULE: "mixed compartment signs … → UNRESOLVED SIGN = BLOCKER; record everything; do not force" — **APPLIED.** Both prongs recorded; nothing forced.

---

## 1. RESUMPTION HYGIENE

The dead attempt left `brief.md` and `work/mesh_target_o2.py`. `brief.md` was verified to BE the frozen preregistration (verbatim; thresholds, falsifier, stop rule intact) and was followed unedited. `work/mesh_target_o2.py` was diffed against `baseline_snapshot/code/mesh_target.py`: byte-identical, SHA-256 `268f139a9e90e561f4a5f8ab02553f0d87f51633f635139e6cec6f5c9cfa19a0` on both — **reused**, with paths repointed to the read-only snapshot at construction time (never modified). Everything else was created fresh under `scripts/`, `receipts/`, `figures/`.

## 2. METHOD (a) — SOURCE palm sign (27-geom plane, site-independent; compartment semantics EXTERNAL)

Construction semantics replicated exactly from the C3 receipt (intake walk; centroid + SVD plane; normal = last right singular vector, undirected; lunate has no `pos` attr → origin). Cross-check: per-site offsets equal C3's `c3_source_geometry.json` to **0.000e+00 m** and |cos(n27_O2, n27_C3)| = 1.000000000000 (`receipts/c3_crosscheck.log`); `hand_r` world origin reproduces C3/A4's (−0.0731, 0.532647, 0.202699). The 5 sites enter no construction (C3 direction A: rms 8.88 mm ≤ the plane's own 10.66 mm).

External compartment evidence (one citation each, class=EXTERNAL, fetched live 2026-09-24, quoted in `receipts/commands.md` §4): **FCR** anterior compartment, anterior base of 2nd MC · **FCU** anterior compartment, pisiform/hamate/anterior base 5th MC · **ECRL** posterior compartment, dorsal base 2nd MC · **ECRB** posterior compartment, dorsal base 3rd MC · **ECU** posterior side of forearm, base 5th MC (ulnar side).

### 2.1 The FROZEN test — signed offsets along n27 = (−0.132643, −0.111185, −0.984908) (hand_r local)

| site | compartment | offset along n27 | z-term | tilt-term | vs palm-13 plane (diagnosis) | raw local z (diagnosis) |
|---|---|---:|---:|---:|---:|---:|
| ECRL-P4 | extensor | **−12.33 mm** | −6.71 | −5.62 | −7.39 | +8.16 |
| ECRB-P4 | extensor | **−14.43 mm** | −9.33 | −5.10 | −11.23 | +10.82 |
| ECU-P6 | extensor | **−0.86 mm** | +0.30 | −1.16 | +0.02 | +1.05 |
| FCR-P3 | **flexor** | **−1.99 mm** | +3.15 | −5.14 | +2.22 | −1.85 |
| FCU-P4 | **flexor** | **+5.40 mm** | +6.44 | −1.04 | +6.71 | −5.19 |

**FROZEN clean-split criterion: FALSE — mixed compartment signs** (flexors split: −1.99 vs +5.40).

Falsifier evaluation, both palm assignments:
- palm := +n27 side (FCU's side): violations = **FCR-P3 −1.99 mm** (flexor on the extensor side). No extensor violates.
- palm := −n27 side: violations = **FCU-P4 +5.40 mm** (flexor on the dorsal side) **and** the dorsal extensors ECRL/ECRB land ON the palm side at −12.33/−14.43 mm (the two largest offsets in the table). Strictly worse.

Either assignment violates the compartment semantics → **falsifier FIRED → STOP RULE → source sign UNRESOLVED = BLOCKER.** The direction with strictly fewer and smaller violations (+n27 side = FCU's side) is RECORDED AS A DIAGNOSTIC, not adopted: it does not meet the frozen criterion, and adopting it would be an authoring decision (the human terminal), not an O2 measurement.

### 2.2 Why the frozen test fails — diagnosis (measured, not tuned)

1. **The sites are all far from the plane's centroid along the length axis** (centroid y = −0.0675 m; sites y = −0.026…−0.036 m → 31–43 mm proximal), while **n27 is tilted ~10.0° off the −z axis** (n_z = −0.9849). Every site therefore carries a **tilt term of −1.0 to −5.6 mm** — the same order as the flexors' entire raw volar separations (−1.85, −5.19 mm).
2. **The tilt is the digital fan, not the palm**: digits 2/3 curl to +z (+11.0/+18.3/+19.5 mm proxph/midph/distph) while digit 5 curls to −z (−3.4/−6.3/−8.5 mm) — an asymmetric phalange fan that tilts the 27-geom plane and gives it its 10.66 mm rms / 28.61 mm max residual. The palm's own bones do not carry this tilt: the 13 carpals+metacarpals plane sits 6.39° from n27.
3. **Construction instability at the sites' lever arm**: leave-one-geom-out jackknife (27 refits) swings ECRL/ECRB offsets across **±12–15 mm** (ranges in `receipts/commands.md`) and yields a clean split in only **1/27 refits**. The frozen test's boundary crosses FCR-P3 within the plane's own construction noise.
4. **Construction-free cross-check (diagnostic only): raw local z splits CLEANLY 3/2** — extensors +8.16/+10.82/+1.05, flexors −1.85/−5.19 — and the L/R mirror symmetry of the XML (hand_l = hand_r with every z negated exactly; my hand_l offsets are bit-identical with z flipped, same verdict) proves local z IS the palmar-dorsal axis. The 13-geom palm-subset plane (diagnosis) is near-clean: flexors +2.22/+6.71, radial extensors −7.39/−11.23, ECU +0.02 dead on the plane (anatomically expected for the ulnar-border extensor; still not a strict clean split by sign). **All of this is recorded as diagnosis; per the stop rule it does not override the failed frozen criterion.**

## 3. METHOD (b) — TARGET palm sign (paddle curvature; frozen threshold: sagitta difference > 1 mm over the distal half)

Frame: origin `wrist_R` = (−0.144995, 0.261482, −0.005956) m; stationing along a = unit(wrist−elbow) = (−0.455844, −0.890058, 0.001857) (the C2/C3 axis; paddle PCA axis measured 6.4° off it over 776 verts at r<25 mm — C2's 10.3° used a different selection; both far under the 15° falsifier). +T = e1 by the fixed rule "rejection of global +x on the plane ⊥ a": **+T_R = (0.890060, −0.455843, 0.000951)**, +T_L = (0.890060, +0.455843, −0.000951). Sections are exact triangle-plane intersections (no slab bias, no bridging), 72 stations at 1 mm. Frozen window: distal half [55.65, 111.3] mm of the 111.3 mm paddle (C2).

### 3.1 The frozen-window numbers (side R; L is the exact anti-mirror — validity check)

| readout | classic sagitta (max signed dev from chord) | quadratic-fit sagitta |
|---|---:|---:|
| mid-line (section centroid) | **−3.392 mm** @ t=83 | −3.288 mm |
| +T face | **+2.117 mm** @ t=106 | −0.950 mm |
| −T face | **−5.109 mm** @ t=94 | −4.512 mm |
| **D1 = sag(+T face) − sag(−T face)** | **+7.226 mm** | +3.561 mm |
| D1 over the trimmed window [55.65, 103.3] (rim excluded) | **−0.31 mm** | — |

Thickness profile: 16.46 mm @56 (window start) → ~13.1 @76–84 → 10.56 @104 → **2.92 @111**; mid-window thickness exceeds its endpoint chord by ~3.4 mm (12.94 actual vs 9.57 chord @ t=84).

### 3.2 What the numbers say — the falsifier fires in every reading

1. **The two faces bow APART** (+2.12 vs −5.11): a constant-thickness bend requires same-sign sagittae differing only by th·(1−cosθ). At the measured mid-line bow (3.3 mm over a ~28 mm half-window, R ≈ 119 mm) that difference is **≈ 0.33 mm**; measured 3.56–7.23 mm, i.e. **10–20× too large**. The slab is a **thickness lens on a linear taper** (16.5→10.6 mm over 56–104 mm), not a resting-flexion bend.
2. **The frozen D1 (+7.226 mm) is tip-rim-dominated**: excluding the last 8 mm (where thickness collapses 10.6→2.9 mm) gives **D1 = −0.31 mm**.
3. **D1's own sign rule nominates the WRONG face**: D1 > 0 nominates the −T face as palm — but that face is measured to be the **MORE CONVEX** one (|−5.11| > |+2.12|; it carries the lens's outward bulge). A convex "palm" → **convex-palm falsifier FIRED**.
4. **The bend-consistent mid-line nomination** (mid-line bows −T → convex face = −T → palm = +T face): the +T face's concavity is **0.95 mm (quadfit)** — **below the frozen 1 mm threshold** — and **wrong-signed (+2.12 mm) by classic max-deviation**. **Below-threshold → stop rule.**

Every branch of the frozen decision tree lands on UNRESOLVED: the sagitta difference either nominates a convex palm (falsifier) or the palm face is flat/sub-threshold (stop rule). **TARGET palm face UNRESOLVED = BLOCKER.** Side L confirms the measurement (exact anti-mirror: mid +3.392, faces +5.109@94 / −2.117@106, D1 +7.226, trimmed −0.31), not the sign.

## 4. EXISTING-IMAGE INVENTORY (secondary lane) — exists, INSUFFICIENT

- **Found:** four distinct renders of the target character: `Saved/vision_trial/{A_front_rest, B_leftside_rest, C_threeq_rest, D_front_elbowL50}.png` (2560×1440; md5s all distinct; hand crops in `figures/inventory_zoom_*.png`).
- **Ruled out:** `Saved/mesh_view/*`, `docs/evidence/shape_dyad_correction/*`, `docs/evidence/v04/*` — teddy renders (`mesh_view/judgments.jsonl` names "a solid brown teddy-bear-shaped triangle mesh"); `baseline_snapshot/runs/figure_*.png` — point-cloud fit projections with no shading (palm/dorsum not decidable).
- **Why the four monkey renders fail the preregistered bar** ("visually decidable AND knowable orientation"): (i) hands are ~60–80 px wide — palm/dorsum is at the edge of decidability even for a human; (ii) poses are ANIMATED (D shows the left elbow flexed 50°), not the birth pose, and no camera-to-mesh mapping exists anywhere in the repo — the observed facing cannot be transformed into birth-mesh coordinates; (iii) asset identity with the baseline birth mesh is not establishable from images (the renders show separated digits and a thumb; C2 proved the birth paddle has zero digit-distinguishable structure at its sampling). Recorded as a lane that exists but cannot settle the sign. It does not rescue the blocker.

## 5. METHOD (c) — COMBINATION: NOT POSSIBLE (the blocker)

The hand roll SIGN is the mapping **source palm direction ↔ target face**. Measured: source palm direction UNRESOLVED (§2 — mixed compartment signs about the frozen plane), target palm face UNRESOLVED (§3 — falsifier/sub-threshold). With both ends open, **no roll SIGN mapping is stated**; the only honest O2 output is:

> **UNRESOLVED SIGN = BLOCKER (both prongs independently).** Per the frozen stop rule, everything was recorded and the sign was not forced.

For the record, the diagnostics that POINT at a consistent direction but do NOT meet the frozen bar (an authoring decision above O2): source palm ≈ the −z side of `hand_r` local (= the +n27 side, FCU's side); target convex face ≈ −T_R with the +T_R face = (0.890060, −0.455843, 0.000951) as the palm-nominal face. These are recorded in the receipts with their failing margins (source: FCR −1.99 mm, jackknife 1/27; target: palm concavity 0.95 mm < 1 mm, wrong-signed max-dev +2.12 mm, trimmed D1 −0.31 mm).

**Smallest measurements that would close the blockers** (C3 §8 lane, unchanged, now with exact failing margins):
1. Target: ONE visual identification of the paddle's palm face in a KNOWN birth-pose/camera frame (a single GPU-brokered render through the frozen channel, or an authored declaration), read by the operator/vision terminal — this alone closes the target end (the curvature lane is measured and its margin recorded).
2. Source: an architect's authoring of the palm-side boundary for the site test (the frozen 27-geom plane fails as the boundary: its tilt moves site offsets by up to ±5.6 mm at the sites' 31–43 mm lever arm, and 1/27 jackknife refits are clean), OR acceptance of the raw-z/palm-13 diagnostic as the boundary by authoring. Both are authoring, not measurement — O2 records, does not choose.

## 6. SCOPE DISCIPLINE — scale / assembly / production UNTOUCHED

No hand scale was computed or evaluated (no paddle-length scale claim, no 0.716/0.77/0.90 arithmetic); no assembly correspondence was constructed or challenged (no landmark pairings, no H-LEN/H-ASP/H-BODY analysis); no production mapping was computed. Every quantity above is a signed offset or a profile curvature used for the orientation sign only. T6 discipline: no moment arm, path length, or transmission quantity was computed anywhere.

## 7. INTEGRITY RECEIPT

- `git status --porcelain -- forearm_package/baseline_snapshot` → **empty** at start and end; HEAD `5db981cb`; no git writes.
- Input hashes asserted before runs: `monkey_birth.bin 550a5b3ec927ea13…` (661,076 B), `monkey_joints.bin 74b3ab044b7adaed…` (296,589 B) — equal to MANIFEST.
- Module reuse: `work/mesh_target_o2.py` ≡ `baseline_snapshot/code/mesh_target.py`, SHA-256 `268f139a9e90e561f4a5f8ab02553f0d87f51633f635139e6cec6f5c9cfa19a0`, verified before the first run; executed with paths repointed to the snapshot only.
- C3 construction reproduced to 0.000e+00 m (`receipts/c3_crosscheck.log`) — my source numbers are the frozen C3 construct, not a re-authoring.
- Gaming-safety: all figures are matplotlib with `matplotlib.use("Agg")` BEFORE pyplot import (stated per receipt); CPU-only; NO GPU/OpenGL/Vulkan/WebGL contexts; no new renders of the mesh (the only images read are pre-existing repo files, listed in §4).
- `PYTHONDONTWRITEBYTECODE=1` throughout; no `__pycache__`/`.pyc` under the audit dir.
- All writes confined to `forearm_package/audits/O2_hand_orientation/` (report.md, scripts/, receipts/, work/, figures/; brief.md recovered intact from the dead attempt).
- Commands and key outputs: `receipts/commands.md`; receipts JSON: `receipts/o2_source_sign.json`, `receipts/o2_target_curvature.json`.

## 8. PRESERVED NEGATIVES AND DIAGNOSTICS (they are results)

1. The 27-geom plane as a palm-sign boundary: **fails** — tilt-driven contamination at the sites' lever arm (this is a property of the frozen construct at the sites' position, not of the sites).
2. Raw local z (construction-free) clean 3/2 split and the 13-geom palm plane near-clean split: recorded as diagnostics only; they do not meet the frozen criterion.
3. The paddle's distal half is a **lens/wedge slab** (thickness bulge ~3.4 mm above its endpoint chord mid-window; rim collapse in the last ~7 mm): the resting-flexion prediction does not describe this geometry.
4. The four vision_trial monkey renders: exist, inspected, INSUFFICIENT for the sign (pose/camera/asset-identity gaps) — preserved as the smallest missing lane's raw material.
5. L/R anti-mirror exactness of the paddle profiles (fixed +x rule) and the bit-exact z-mirror of the source hands: measurement-validity facts, recorded.
6. WebSearch was rate-limited (HTTP 429); the compartment citations were fetched live from the canonical Wikipedia pages instead (URLs + quoted sentences in `receipts/commands.md` §4).

STOP RULE honored: everything recorded; nothing forced; stopping here.
