# C1 — ULNA ANATOMICAL EVIDENCE: endpoints, units, coverage, scale derivations, and the entire-vs-fragment verdict on the 2.31 cm axis

**Agent:** C1 evidence agent · **Date:** 2026-09-24 · **Wave:** 3 (architect-ordered, bounded)
**Scope honored:** no candidate chosen; no new fit session; no production mapping; no radius supersession; no moment arms or tendon utility computed (packet tendon records read for site MEMBERSHIP only). Baseline read-only throughout; all execution used direct XML/JSON reads from a script in this audit dir (no baseline module was executed in place; nothing was written outside `audits/C1_ulna_evidence/`).
**Inputs:** `baseline_snapshot/source_xml/chimanoid.xml` (sha `675e00d0…`), `baseline_snapshot/runs/actual_monkey_fit.json` (sha `a4475550…`), wave-2 receipts B1/B4 (read), `baseline_snapshot/code/{DERIVATION.md, actual_target_fit.py, correspondence.py, mesh_target.py}` (read, not executed).

---

## 0. ACCEPTANCE-CRITERION VERDICTS

| # | criterion | verdict |
|---|---|---|
| 1 | verbatim endpoint/axis table + open direction question resolved with numbers | **PASS** (§1: axis = 14.324 mm axial + 18.088 mm lateral + 0.301 mm dorsovolar; 51.63° off the forearm axis) |
| 2 | per-site anatomical-region table (source-internal + EXTERNAL-cited, classes separate) | **PASS** (§2: 9/10 axial-region agreements; ECU transverse sign UNCERTAIN; brief's PT cell corrected) |
| 3 | entire-vs-fragment verdict with deciding evidence | **PASS — (b) KINEMATIC FRAGMENT** (§3: four independent deciding numbers) |
| 4 | 4.4× extrapolation explained in the anatomical frame with the corrected factor | **PASS** (§4: 4.4535× is the kinematic-frame reading; anatomical-frame factors 4.258× axial / 6.860× vs the axis's own axial extent; mechanism and ECU-P4 uncertainty quantified) |
| 5 | U-STR/U-ANA independent-validation assessment with independence split stated | **PASS** (§5: U-STR 10/10 validators consistent to ≤8.8 points of forearm length; U-ANA 9/9 validators, 6 displaced out of region by +7 to +42 points) |
| 6 | smallest missing measurement if indistinguishable | **ANSWERED — the candidates are NOT indistinguishable on the independent-site test; the smallest missing measurement for the remaining question (direct bone-surface confirmation of the fragment verdict) is the `ulna` mesh asset's distal extent, one file, external to the baseline** (§6) |
| 7 | baseline integrity | **PASS** (§7: `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` → empty, run at start and re-run at end) |

## 0.1 PREREGISTRATION VERDICT (frozen in `brief.md` before measurement)

| sub-claim | outcome | numbers |
|---|---|---|
| ulna→radius axis is mostly LATERAL | **CONFIRMED, with a measured precision the prediction lacked** | 78.4% of the offset is transverse (18.09 of 23.07 mm) and the transverse part is 100% lateral (coronal plane) — but the axis is OBLIQUE at 51.63°, carrying a 14.32 mm distal co-component (62.1%). Both extreme readings ("pure lateral", "along the forearm") are false. |
| 2.31 cm segment is a KINEMATIC FRAGMENT, not the anatomical ulna | **CONFIRMED** | §3: attachments lie 4.26× the axis length beyond the origin axially; the body's own inertial CoM sits 120.5 mm distal (5.22× the axis); elbow_flexion is the body's direct hinge; the chain hands forearm length to radius (292.03 mm) and wrist to hand_r. |
| site distribution spans the anatomical forearm coherently, TRI/BRA/ANC proximal, ECU distal | **PARTIALLY FALSIFIED** | Distribution spans only **−3.85% to +32.13%** of the source forearm (proximal third + olecranon) — it does NOT span the forearm. TRI/BRA/ANC proximal ✓ (with numbers); PT proximal ✓ (at 10.37% — the brief's own "mid-distal ulna" cell is what is wrong); ECU "distal" only relative to the ulna set — its distal course is carried by radius site ECU-P5 (74%) and hand site ECU-P6 (terminal). Coherent: yes, within the proximal third. |
| U-STR structurally faithful but anatomically silent about distal placement; U-ANA captures the anatomical span via a single non-independent anchor | **PARTIALLY FALSIFIED** | U-STR is NOT anatomically silent: it reproduces the source layout to within ≤8.8 points of forearm length (worst: PT-P2 10.37% → 1.56%). U-ANA does NOT capture an anatomical span: to put ECU-P4 (an interior tendon waypoint, 4 of 6, whose source position is 32% down the forearm) on the wrist it displaces 6 of 9 independent sites out of their regions by +7 to +42 points (§5). The "anatomical span" attributed to U-ANA does not exist in the source distribution. |

The falsifier ("any of the four sub-claims failing") **fired on sub-claims 3 and 4** as written; the measured numbers are reported above and detailed below, whichever way they point. No tuning was applied to make them fit.

---

## 1. VERBATIM GEOMETRY AND THE DIRECTION QUESTION (criterion 1)

All bodies axis-aligned (`quat="1.0 0.0 0.0 0.0"` verified for all four), so offsets compose additively and ulna-local site coordinates are world-directional.

### 1.1 Verbatim endpoints (XML `pos` strings, exact)

| body | verbatim `pos` (m) | |offset| (m) | meaning |
|---|---|---|---|
| `humerus` (right) | `" -0.0176   -0.007     0.17"` | — | shoulder frame (parent of ulna) |
| `ulna` | `"  0.0061  -0.34845  -0.0123"` | **0.348720379** | ulna origin = ELBOW (humerus→ulna) |
| `radius` | `"  0.0004 -0.011503 0.019999"` | **0.023074640** | **THE 2.31 cm AXIS** (ulna→radius) |
| `hand_r` | `"   0.018   -0.2904    0.025"` | **0.292029382** | radius→wrist |

Frozen evidence cross-check: |ulna→radius| = 0.02307 ✓, |radius→hand| = 0.29203 ✓, |elbow→hand| = 0.305792 ≈ 0.306 ✓. Note the chain-sum 0.315104 ≠ |elbow→hand| 0.305792 — the two offsets are NOT collinear (this is the geometric root of everything below).

Direct joints (verbatim): `ulna`: `elbow_flexion` hinge `pos="0 0 0"` `axis="0 0 1"` range `[0, 2.26893]` — the ulna body's origin is the hinge; the +z axis is the source RIGHT/lateral direction (a transverse elbow-swing axis, anatomically correct). `hand_r`: the three wrist hinges at `pos="0 0 0"`. Sites: exactly 10 on `ulna` (verbatim list in `receipts/c1_geometry.txt` §1), all tendon-referenced (receipt §1: TRIlong/TRIlat/TRImed-P5 terminal 5/5; ANC-P2 terminal; BRA-P3 interior, BRA-P4 terminal; ECU-P2/P3/P4 interior 2,3,4 of 6; PT-P2 interior).

### 1.2 UNITS

- **Source XML: meters (SI).** Bone spans 23–349 mm — a full-size macaque model. (S13 unit-identity receipt in DERIVATION §13: source coordinates export verbatim.)
- **Target: native mesh units × `MESH_UNIT_TO_M = 0.065`** (`mesh_target.py:10`: "prototype scale, not a biological measurement"); the packet's target joint coordinates are in meters (§1.3). The 0.065 factor never touches source coordinates (S13).
- **No unit error exists in the 2.31 cm axis** — it is 23.07 mm of a 305.79 mm forearm in the same meters the target's 64.74 mm forearm is measured in.

### 1.3 Target anchors (packet, exact floats)

- `elbow_R` (packet `elbow_flexion` origin) = [−0.115480983853340158, 0.319109077453613277, −0.006076556332409382]
- `wrist_R` (packet wrist-triple origin) = [−0.144994540214538586, 0.261482369899749767, −0.005956328995525837]
- |elbow_R→wrist_R| = **0.064744899 m**; anchor gap 0.0 (packet `unresolved_body` joints sit exactly on the pack joints — B4 E6). Known-good radius scale = 0.22170679566544982 (uniform), and 0.292029 × 0.221707 = 0.0647449 ✓. Source→target forearm ratio = 0.211728 (≠ the radius scale — see §4d).

### 1.4 The open direction question — RESOLVED

Anatomical frame derived from the chain: **â** = unit(elbow→wrist) = [0.060172, −0.987281, 0.147155]; **l̂** = source-right (+z, DERIVATION §2) orthogonalized against â; **p̂** = â×l̂ ≈ −x̂ = posterior. det = +1.

The ulna→radius vector decomposes as:

| component | value | share of 23.075 mm |
|---|---|---|
| **axial** (along elbow→wrist, distal) | **+14.324 mm** | 62.1% |
| **lateral** (toward +z, the side the radius body sits on) | **+18.088 mm** | 78.4% |
| posterior | +0.301 mm | 1.3% |

Angle to the forearm axis **51.63°**; the offset lies in the coronal plane (99.9% of the transverse part is lateral).

**Verdict:** the axis is **oblique, perpendicular-dominant, lateral+distal** — the radius body's frame is pinned beside the ulna origin and slightly down the forearm, i.e. a radioulnar JOINT-FRAME offset, exactly as the preregistration's first branch anticipated (perpendicular-dominant, 78.4%). Consequence for the sites: since the frame axis is NOT along the forearm, the sites' large offsets are free to be mostly AXIAL — and they are (§2). The anatomically coherent branch of the open question is the one that holds.

## 2. THE 10 SITES IN THE ANATOMICAL FRAME + REGION TEST (criterion 2)

Source-internal geometry (receipt §3); region classification = muscle semantics verified class=EXTERNAL (`receipts/external_citations.md`, one fact per muscle, no blending). Fractions are of the source forearm |elbow→wrist| = 305.792 mm. Bands used for the region test: olecranon/process region [−6%, +3%]; tuberosity/coronoid (proximal) region (+3%, +15%]; ulnar shaft course: monotone progression, posterior-biased, interior waypoints not at the wrist.

| site | axial mm (ax %EW) | lateral mm (+radial side) | posterior mm | region demanded (EXTERNAL) | agreement (source-internal) |
|---|---|---|---|---|---|
| TRIlong-P5 | −11.760 (−3.85%) | +0.96 | +21.22 | common tendon on posterior/proximal olecranon | **AGREE — strong**: 3.85% proximal + 21.2 mm posterior = the olecranon process behind/above the hinge. (All three TRI sites share one identical authored point — one common insertion ✓.) |
| TRIlat-P5 | (same point) | | | same | **AGREE** (identical) |
| TRImed-P5 | (same point) | | | same | **AGREE** (identical) |
| ANC-P2 | +0.584 (+0.19%) | +5.98 | +25.35 | lateral olecranon + superior posterior ulna | **AGREE — strong**: at the hinge level, 25.4 mm posterior, lateral side |
| BRA-P3 | +14.932 (+4.88%) | −0.93 | −4.08 (anterior) | coronoid/ulnar tuberosity, anterior proximal ulna | **AGREE — strong**: proximal + anterior |
| BRA-P4 | +23.536 (+7.70%) | −2.59 | +4.65 | broad brachialis footprint (Kamineni 2015) | **AGREE — good**: still proximal fifth |
| PT-P2 | +31.703 (+10.37%) | −19.19 (medial/ulnar side) | −6.39 (anterior) | **coronoid process, medial side** (EXTERNAL: Kenhub/StatPearls) | **AGREE — good**: proximal third + medial + anterior. NOTE: this refutes the BRIEF's own table cell ("PT → mid-distal ulna"): the standard ulnar origin is the coronoid (proximal); source geometry agrees with the EXTERNAL fact, not with the brief's cell |
| ECU-P2 | +35.103 (+11.48%) | +24.57 | +15.83 | posterior border of ulna, course distally | **AGREE (axial)**: first course point, posterior-biased |
| ECU-P3 | +56.784 (+18.57%) | +20.55 | +20.32 | same course | **AGREE (axial)**: monotone 11.5% → 18.6% |
| ECU-P4 | +98.257 (+32.13%) | +18.52 | +23.72 | course toward the distal ulna/wrist | **AGREE (axial)**: monotone 18.6% → 32.1%, still a proximal-third-to-mid shaft point; the distal course is carried by ECU-P5 (radius, 74%) and ECU-P6 (hand, terminal) — the model's site split mirrors the muscle's course |

**Agreement summary: 10/10 sites agree on the axial region test** (the primary, species-robust test). **One sub-test UNCERTAIN:** the ECU sites' transverse position sits 18–25 mm on the RADIUS side of the elbow→wrist axis line; on human analogy ECU runs on the ulnar side. The transverse sign test is interpretation-limited for a quadruped rest pose (the model's own forearm axis runs elbow→CARPUS, and the radius shaft itself starts 18.1 mm on that same side) — recorded as UNCERTAIN, not as disagreement. No site's axial placement disagrees with its externally-verified region.

## 3. VERDICT ON THE AXIS: KINEMATIC FRAGMENT, NOT THE ANATOMICAL ULNA (criterion 3)

**(b) The 2.31 cm segment is a kinematic fragment** — the elbow-hinge body piece — and the anatomical ulna's length is carried by the SITE DISTRIBUTION (and by the radius body structurally). Four independent deciding numbers, all source-internal:

1. **Attachments lie 4.26× beyond the axis, axially.** ECU-P4 sits 98.257 mm down the forearm from the ulna origin = 4.258× the whole axis length (and 6.860× the axis's own axial extent of 14.324 mm). A 23.075 mm bone cannot carry an attachment 98 mm away; muscle sites/authored waypoints lie on or wrap the bone they belong to. The body-to-body offset is a JOINT-FRAME distance, not a bone length (DERIVATION §2: "Every body origin = its proximal joint").
2. **The body's own mass distribution contradicts a 23 mm bone.** The ulna `<inertial pos="0 -0.120525 0">` puts the body's center of mass 120.525 mm from its origin (5.22× the axis; 119.0 mm axially = 38.9% down the forearm, 17.7 mm on the MEDIAL/ulnar side — where a full-length ulna shaft runs). Caveat recorded: the radius body carries the byte-identical inertial (`pos 0 -0.120525 0, mass 0.729`, lines 596/611) — a probable source authoring copy-paste; either way the author treated the ulna body as a forearm-length piece, never as a 23 mm one.
3. **The ulna body is the hinge carrier.** `elbow_flexion` (axis +z = lateral/transverse — a correct elbow swing axis) is its only direct joint, at its origin. It is the moving piece at the elbow, which is what a kinematic fragment IS.
4. **The structural forearm length bypasses the ulna.** `hand_r` (the wrist, owning the wrist triples) is a child of `radius` at 292.03 mm; the ulna body has no distal landmark of its own (its only child is `radius`, at 23.075 mm — the radial head beside the elbow: 18.09 mm lateral + 14.32 mm distal in the coronal plane). The anatomical ulna (which spans elbow→wrist alongside the radius in a real forearm) is represented distally by NOTHING on the ulna body.

Rejected alternative (preserved): reading (a) "the 2.31 cm axis is the anatomical ulna entire" requires a 23 mm ulna in a 306 mm forearm with attachments at 4.26× its length and a CoM at 5.22× its length — refuted numerically, not by taste.

## 4. THE "4.4× EXTRAPOLATION" EXPLAINED (criterion 4)

**(a) What the number actually is.** 4.4535× = max |site| / |axis| = 102.763 / 23.075 mm — the largest site distance from the origin divided by the kinematic-axis length (ECU-P4). It is a property of the SOURCE layout: the frame built on the 23 mm axis must place sites up to 4.45× the axis length away. It survives the map 1:1 under any uniform scale — it is NOT created or cured by fitting.

**(b) Corrected factor in the anatomical frame.** The resolved axis direction (§1.4) shows the extrapolation is mostly AXIAL, not transverse: max axial reach / |axis| = 98.257/23.075 = **4.258×**; max axial reach / the axis's own axial extent = 98.257/14.324 = **6.860×**; max transverse reach / |axis| = 30.096/23.075 = **1.304×**. The coordinator measure "perp-off-axis 0.1015 m" (BODY_RESOLUTION_MAP §1) was **NOT REPRODUCED** under any frame attempted: perp to the kinematic axis = 69.363 mm, perp to the forearm axis = 30.096 mm; 101.5 mm would leave only 16.1 mm axial, matching no constructed frame. The map's row should read: sites reach 4.46× the axis length from the origin, of which the dominant part is along-forearm.

**(c) The mechanism that makes it dangerous (and quantifies ECU-P4's uncertainty).** Because the frame axis is 51.63° off the anatomical axis, a site's mapped AXIAL position = s·[(p·â)·cos 51.63° + (p·l̂)·sin 51.63° + small p̂ term] — transverse position feeds axial placement with weight sin 51.63° = 0.784. For ECU-P4 under U-STR, 3.220 mm of its 16.810 mm fitted axial position (19%) comes from its 18.5 mm lateral offset alone. Any roll or scale error in the short frame therefore displaces ECU-P4 axially with 0.784 gain on its transverse error — that is the precise content of "roll/scale error amplifies into ECU-P4's placement."

**(d) Do not conflate two different numbers.** The cross-animal scale ratio |EW_target|/|EW_source| = 0.211728, and 1/0.221707 = 4.510, are a DIFFERENT quantity from the 4.4535× intra-source frame extrapolation; they coincide in magnitude by accident.

## 5. U-STR AND U-ANA AGAINST INDEPENDENT LANDMARKS (criterion 5)

**Independence split (architect's circularity law):** U-STR's construction inputs are body origins only (`body_origin:ulna` → elbow_R; `body_origin:radius` → derived point 5.116 mm along elbow→wrist) ⇒ **all 10 sites are independent validators**. U-ANA's construction uses `site:ECU-P4` ⇒ **the other 9 are validators** (and note: ECU-P4 is an INTERIOR tendon waypoint — 4 of 6 in `ECU_tendon`, terminal is ECU-P6 on hand_r — not an attachment and not a bone endpoint; using it as the distal anchor re-reads a path point as a skeletal landmark).

Closed-form, roll-independent predicted axial placements (a′ = wrist direction by construction, so fitted_axial = s·(p·â_frame) exactly; geometry only — no fitting run, receipt §5):

| site | source ax %EW | U-STR fitted (% of 64.745 mm) | Δ pts | U-ANA fitted | Δ pts | demanded region (target frame) |
|---|---|---|---|---|---|---|
| TRI×3 | −3.85 | −2.15% (−1.39 mm) | +1.7 | −6.01% (−3.89 mm) | −2.2 | at/just proximal of the hinge (olecranon) — both OK |
| ANC-P2 | +0.19 | +1.84% | +1.7 | +7.29% | **+7.1** | at the hinge, posterior — U-STR ok; U-ANA pushed distal |
| BRA-P3 | +4.88 | +2.91% | −2.0 | +12.81% | **+7.9** | tuberosity/coronoid band (+3,+15%] — U-STR in; U-ANA in but far high |
| BRA-P4 | +7.70 | +4.33% | −3.4 | +22.49% | **+14.8** | same band — U-STR in; **U-ANA out (mid-shaft)** |
| PT-P2 | +10.37 | +1.56% | **−8.8** | +24.70% | **+14.3** | coronoid band — U-STR compressed to the hinge (band-marginal, direction right); **U-ANA out** |
| ECU-P2 | +11.48 | +14.13% | +2.7 | +40.53% | **+29.1** | shaft course, proximal-to-mid — U-STR ok; **U-ANA out of source region** |
| ECU-P3 | +18.57 | +17.68% | −0.9 | +61.00% | **+42.4** | same — U-STR ok; **U-ANA far out** |
| ECU-P4 | +32.13 | +25.96% | −6.2 | +100.00% (=wrist) | +67.9 | shaft waypoint — **U-ANA's placement IS its construction input (non-independent, validates nothing)** |
| (transverse, max) | — | 15.38 mm | — | 17.49 mm | — | both inside the session-3 forearm-envelope medians (b 20.2 / c 22.9 mm, B1 §4.1) — no placement falls outside the skin envelope |

**Assessment.** Where the independent sites' regions demand they land: all of TRI/BRA/ANC/PT in the proximal quarter of the target forearm; ECU-P2/P3 as proximal-to-mid shaft course points; NONE of the 10 (which are all ulna-owned) anatomically demands the wrist — the only wrist-region sites are hand-owned (ECU-P6, FCU-P4, …), which C2 owns.

- **U-STR's frame is CONSISTENT with all 10 independent validators**: every site stays in its demanded region; the layout is reproduced to within 8.8 points of forearm length (worst case PT-P2, compressed toward the hinge, direction preserved; mechanism = §4c). U-STR is structurally faithful AND regionally faithful — what it cannot represent is a target-side ulna SHAFT longer than 5.116 mm (its distal landmark is the radius origin; the radius then re-partitions to 92.1% of the forearm by closure).
- **U-ANA's frame is INCONSISTENT with 6 of its 9 independent validators** (+7.1 to +42.4 points, all displaced distally; BRA-P4 and PT-P2 leave their coronoid/tuberosity bands entirely). It places a proximal-third tendon waypoint on the wrist by construction and pays for it with every other site. The prediction's "U-ANA captures the anatomical span" is refuted: there is no anatomical span to capture — the source distribution ends at 32% of the forearm.
- **Per the architect's law I choose neither candidate**; the evidence statement is: on the independent-site anatomical test, U-STR's frame passes and U-ANA's frame fails, and U-ANA's single apparent success is its own construction input. Mass note (closed form, no preference): m′ = 0.729·s³ gives 0.007944 kg (U-STR) vs 0.182320 kg (U-ANA), ratio 22.95× — and BOTH inherit the suspect shared-with-radius inertial (§3.2), so neither mass is cleaner than the other at the source.

## 6. SMALLEST MISSING MEASUREMENT (criterion 6)

The candidates are NOT indistinguishable — §5 separates them on already-frozen evidence. What remains unmeasured is the DIRECT (bone-surface) confirmation of the §3 fragment verdict:

**Smallest missing measurement: the distal extent of the source `ulna` mesh asset** (the geom `<mesh="ulna">` surface — does the drawn bone reach ~the wrist, ~306 mm from the origin, or stop near the 23 mm offset?). One file, referenced by the XML but **external to the baseline** (B1 §5.4: geom meshes are external assets), measurable in minutes with the mesh in hand. If it confirms a full-length bone surface, the fragment verdict upgrades from inference (sites + CoM) to direct evidence, and U-STR's 5.116 mm partition of the target forearm is exposed as a pure kinematic bookkeeping choice — the information needed to authorize or reject it would then be complete. A target-side companion (an independently identified medial-wrist/ulnar-styloid-homolog landmark, identified without any site or body origin) would be the smallest TARGET-side separator of the two authorings' distal claims — but target-side internal anatomy is measurement-blocked by the envelope law (skin is not internal anatomy, DERIVATION §5/session-3), so the source mesh is genuinely the smallest.

## 7. BASELINE INTEGRITY (criterion 7)

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)
```
Run after the brief copy (first work action beyond reads) and re-run after all work: **empty both times — baseline untouched.** No git writes; all writes inside `audits/C1_ulna_evidence/`; `PYTHONDONTWRITEBYTECODE=1` throughout.

## 8. RECEIPTS, NULL/NEGATIVE RESULTS, PRESERVED ALTERNATIVES

Receipts in this directory: `brief.md` (frozen preregistration) · `receipts/c1_geometry.txt` (full measurement dump) · `receipts/c1_geometry_run.log` · `receipts/external_citations.md` (class=EXTERNAL) · `scripts/c1_geometry.py` (exact commands inside; single run reproduces every number in this report).

Null / negative results (preserved):
1. No ulna-specific or distal-ulna landmark exists in the 28-joint target pack — no target measurement can locate the ulna's distal end (B1 §2.0 stands; envelope law blocks internal inference).
2. The map's "perp-off-axis 0.1015 m" (BODY_RESOLUTION_MAP §1) was not reproduced under any frame attempted (§4b) — recorded as unreconciled; superseded here by the two measured values.
3. The brief's own PT region cell ("mid-distal ulna") is contradicted by the EXTERNAL standard (coronoid, proximal); the source agrees with the external fact — the brief's cell, not the source, was wrong.
4. TRIlong/TRIlat/TRImed share one identical authored insertion point (common tendon ✓) — also means the three "sites" carry no independent spatial information (effective validator count for TRI = 1 point, not 3).
5. The ulna and radius inertials are byte-identical (copy-paste suspicion) — both candidates' mass derivations inherit a suspect source value.
6. The three wrist hinge axes are non-axis-aligned (wrist_dev/flex) while elbow_flexion is exactly (0,0,1) — the ulna frame was authored in the source world axes, the hand frame was not; relevant to any future roll-ref discussion (C3's territory).

Rejected alternatives preserved: entire-ulna reading (a) — refuted §3; "4.4× = cross-animal scale" conflation — rejected §4d; "U-ANA captures the anatomical span" — refuted §5.

## STOP RULE

All seven criteria have verdicts; no dependency is missing. Stopped here. No hand-side work (C2), no protocol work (C3), no candidate selection.
