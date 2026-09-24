# B1 — SOURCE ANATOMY OF THE FOUR UNRESOLVED BODIES: `ulna`, `ulna_l`, `hand_r`, `hand_l`

**Agent:** B1 evidence agent · **Date:** 2026-09-24 · **Wave:** 2 (D2 authorized) · **Mode:** read-only evidence + isolated tooling, per the architect's wave-2 laws.
**Baseline:** `E:/PythonChimera/forearm_package/baseline_snapshot/` — untouched (criterion 5 below).
**Preregistration:** frozen in `brief.md` before measurement. Verdict on it: **PARTIALLY FALSIFIED** (letter) / core confirmed (spirit) — see §6. Honest reporting per the law: the falsifier's second prong fired.

---

## 0. ACCEPTANCE-CRITERION VERDICTS

| # | Criterion | Verdict |
|---|---|---|
| 1 | Four per-body dossiers complete (source joints/sites/inertial/hierarchy + target geometry/joints/ownership, with numbers) | **PASS** (with stated measurement limits, §5) |
| 2 | Unresolved reason per body quoted from code/reports | **PASS** (§3) |
| 3 | G/I/U classification per body with deciding quotes | **PASS** (§4) |
| 4 | Per-body resolution-need statement (evidence vs authorization) | **PASS** (§4.2) |
| 5 | Baseline integrity — `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` empty | **PASS** (empty at start and re-verified empty at end; §7) |

---

## 1. SOURCE SIDE (per-body dossier from `baseline_snapshot/source_xml/chimanoid.xml`, 154,835 bytes, sha256 `675e00d0…`, == live `.tmp/chimanoid.xml`)

### 1.0 Hierarchy measured (the brief's question answered directly)

The arm is a strict **CHAIN, not siblings**: `humerus → ulna → radius → hand_r` (left mirrored under `humerus_l`). `ulna` is the ONLY child of `humerus`; `radius` is a CHILD of `ulna`; `hand_r` is a CHILD of `radius`. 19 bodies total (matches DERIVATION §2). Receipt: `receipts/source_anatomy.txt`.

Chain origin distances (measured from XML `pos` accumulations, quat all identity `1 0 0 0`):

| edge | distance | note |
|---|---|---|
| humerus → ulna | **0.3487 m** | the ulna origin IS the elbow (shoulder-to-elbow) |
| ulna → radius | **0.0231 m** | the "2.3 cm elbow-head piece" (session-2: 0.023) |
| radius → hand_r | **0.2920 m** | the forearm length carried by the radius body |
| humerus_l → ulna_l | 0.3488 m | mirror |
| ulna_l → radius_l | 0.0231 m | mirror |
| radius_l → hand_l | 0.2920 m | mirror |

### 1.1 `ulna` (RIGHT, unsuffixed)

- **Parent:** `humerus`. **Children:** [`radius`]. **Siblings:** none (only child).
- **Authored pos** (rel. humerus): `0.0061 -0.34845 -0.0123`, quat `1 0 0 0` (axis-aligned, per DERIVATION §2).
- **Direct `<joint>` children: 1** — `elbow_flexion`, type `hinge`, pos `0 0 0` (body origin = proximal joint = the elbow), axis `0 0 1`, range `[0, 2.26893]`, limited.
- **Sites: 10, ALL tendon-referenced** (30/30 across the four bodies): `TRIlong-P5`, `TRIlat-P5`, `TRImed-P5` (each LAST in its triceps tendon, 5/5), `ANC-P2` (LAST, 2/2), `BRA-P3` (interior 3/4), `BRA-P4` (LAST 4/4), `ECU-P2` (interior 2/6), `ECU-P3` (interior 3/6), `ECU-P4` (interior 4/6), `PT-P2` (interior 2/4). ECU carries 3 of its 6 sites on ulna (+1 on hand = wave-1 A6's "4 unresolved ECU sites on ulna+hand" per side). Receipt: `receipts/tendon_membership.txt`.
- **`<inertial>`: PRESENT** — pos `0 -0.120525 0`, mass **0.729 kg**, fullinertia `0.002962 0.000618 0.003213 0 0 0`.
- **Geom:** 1 mesh.
- **Descendant joints:** `elbow_flexion` + the three wrist coords `wrist_dev_r / wrist_flex_r / wrist_3_r` (owned by descendants, not by ulna directly — the packet's coords field correctly carries only `elbow_flexion`).

### 1.2 `ulna_l` (LEFT)

Mirror of §1.1 in every number: parent `humerus_l`, child `radius_l`, pos `0.0061 -0.3485 0.0123` (z sign flipped), joint `elbow_flexion_l` hinge axis `0 0 1` range `[0, 2.26893]`, 10 sites (all `_l`), inertial mass 0.729 kg identical.

### 1.3 `hand_r`

- **Parent:** `radius`. **Children: NONE** (leaf).
- **Authored pos** (rel. radius): `0.018 -0.2904 0.025`, quat identity.
- **Direct `<joint>` children: 3** (all at pos `0 0 0` = wrist):
  - `wrist_dev_r`, hinge, axis `-0.819064 -0.135611 -0.557444` (NOT axis-aligned), range `[-0.436332, 0.610865]`
  - `wrist_flex_r`, hinge, axis `0.956427 -0.252207 0.147104`, range `[-0.610864, 0.610864]`
  - `wrist_3_r`, hinge, axis `0 1 0`, range `[-1.22173, 1.22173]`
- **Sites: 5, ALL tendon-referenced, ALL terminal (LAST) in their tendons:** `ECRL-P4` (4/4), `ECRB-P4` (4/4), `ECU-P6` (6/6), `FCR-P3` (3/3), `FCU-P4` (4/4). Confirms wave-1 A7: ECRB/ECRL/FCR/FCU terminate on the unresolved hand body.
- **`<inertial>`: PRESENT** — pos `0 -0.068095 0`, mass **0.4575 kg**, fullinertia `0.000892 0.000547 0.00134 0 0 0`.
- **Geoms: 30** = 3 capsules (`r_hand1..3`) + **27 meshes: 8 carpals (pisiform, lunate, scaphoid, triquetrum, hamate, capitate, trapezoid, trapezium), 5 metacarpals (`1mc..5mc`), 2 thumb phalanges (`thumbprox`, `thumbdist`), 12 finger phalanges (`2/3/4/5` × `prox/mid/dist`ph)** — a COMPLETE hand skeleton welded RIGID to one body.
- **Digit joints: ZERO.** Measured over the whole XML: digit-like joint names (finger/digit/thumb/mcp/pip/dip/prox/dist) = **[]**. DERIVATION §12's `absent_in_source` for "articulated fingers" is a statement about JOINTS, not geometry: **finger geometry exists, finger articulation does not.**

### 1.4 `hand_l`

Mirror of §1.3: parent `radius_l`, pos `0.018 -0.2904 -0.025`, joints `wrist_dev_l / wrist_flex_l / wrist_3_l` (same axes/ranges; `wrist_3_l` axis `0 1 0`), 5 mirror sites all terminal, mass 0.4575 kg, same 27-mesh hand skeleton with `_l` names.

### 1.5 Source-side note on the packet's records

The shipped fit packet (`runs/actual_monkey_fit.json`, 1,346,469 bytes) carries for the four bodies: **30 owned sites, all `unresolved=True`**, every one with reason `'owning segment <b> unresolved: no fitted scale (endpoints not declared)'`; **8 joints** (`elbow_flexion` on ulna; 3 wrist coords on each hand) all `status='unresolved_body'`, axis `null`, ranges preserved verbatim; **22 tendons cross these bodies (11 per side), all `rest_length=null`** with `path_incomplete:unresolved_bodies [...]` statuses (TRIlong/lat/med, ANC, BRA, PT → ulna; ECRL, ECRB, FCR, FCU → hand; ECU → hand+ulna; mirrors `_l`). E-2 (ERRATA) already records the consequence: arm bends "sit on unresolved-owner coordinates (`elbow_flexion` owned by unresolved `ulna`; wrist triples by unresolved `hand_r`/`hand_l`), so those arms are NaN rather than zero."

---

## 2. TARGET SIDE (per-body dossier from `baseline_snapshot/inputs/monkey_birth.bin` + `monkey_joints.bin`)

**Input identity:** baseline inputs sha256 `550a5b3e…` (661,076 bytes) and `74b3ab04…` (296,589 bytes) — byte-identical to the live `Saved/meshes/` files the loader points at. Mesh: **18,459 verts / 36,630 tris**; pack: **28 joints**; authored scale `MESH_UNIT_TO_M = 0.065`. Loader: baseline `mesh_target.py` copied to `work/` (never executed in place).

### 2.0 Joint set (full list in `receipts/target_hand_region.txt`)

28 joints: `neck, jaw, spine_upper, spine_mid, spine_lower, tail_base, tail_mid, tail_tip, shoulder_L/R, elbow_L/R, wrist_L/R, hip_L/R, knee_L/R, ankle_L/R, ear_L/R, lid_L/R, brow_L/R, mouth_L/R`.
- **Nothing hand-distal.** Digit-like names: only `tail_tip`. **Ulna-specific joint names: []** (measured).
- `wrist_L = [0.145, 0.2615, -0.006]`, `wrist_R = [-0.145, 0.2615, -0.006]` (exact mirrors); `|elbow→wrist| = 0.0647 m` both sides.
- Wrist bands (pack `assign` primary owner): **263 verts each**, transverse extent **20.0 mm**.
- KEY negative fact: **only 7 of the 263 wrist-owned verts lie distal of the wrist plane, reaching ≤ 1.8 mm** — the wrist joint's own band is forearm skin, not hand.

### 2.1 Is there hand surface distal to the wrist? YES (falsifier prong 1 does NOT fire)

Measured along the elbow→wrist axis continued distally (radius < 25 mm about the axis line), L side (R numerically identical — exact mirror):

- **Skin exists continuously from the wrist plane to 111.4 mm distal** (1.72× the elbow→wrist length), in per-5mm slabs of ~23–135 verts, no gap.
- **One connected component** at 8 mm voxel resolution (165/165 voxels, 26-neighborhood BFS) over the region axial>30 mm, r<35 mm — a single paddle/mitt surface; no digit-like separations resolvable at 8 mm.
- Far end (80–115 mm distal, r<40 mm): n=420 verts, bbox x [184.6, 199.3], y [162.0, 194.0], z [−37.9, 9.2] mm; transverse extents **47.1 × 18.1 mm** — a flattened paddle.
- Nearest-joint field: **1,246 verts have `wrist_L` as their NEAREST pack joint AND lie distal of it.**

### 2.2 Who owns that skin? (the ownership anomaly — negative finding preserved)

Per-5mm slab owner census along the distal axis (`receipts/target_hand_region_v3.txt`):

| distal slab | owners |
|---|---|
| 0–40 mm | **`elbow_L`** exclusively (n=190; the forearm segment's joint owns skin up to 40.8 mm past the wrist) |
| 40.6–103.4 mm | **`tail_base`** (n=194) and **`spine_lower`** (n=411, reaching 111.3 mm) |
| `wrist_L` itself | only 7 verts, ≤ 1.8 mm distal |

The pack has **no joint that owns the hand skin**; from ~41 mm outward the smooth birth mesh's primary binding hands the region to lower-spine/tail joints even though those joints sit at x≈0 (the blob sits at x≈168–199 mm, far lateral — spatially separate from tail/leg geometry). I did not determine the skinning-tool cause (not recorded in the pack); the FACT is measured and quoted above.

### 2.3 The rig's own `hand_tip` law is BROKEN on this mesh (negative finding, preserved)

`mesh_target.py:156` `out["hand_tip"] = beyond("wrist_L", "elbow_L", 30, 1.2)` selects verts with dist-to-elbow < 1.2·|elbow→wrist| and dist-to-wrist > |elbow→wrist|, then takes the 30 farthest from the WRIST. Measured: its 223 candidates' top-30 centroid is **0.1351 m from the wrist on the PROXIMAL side at `[0.0708, 0.3743, -0.0006]`, owned 30/30 by `shoulder_L`** — it measures upper-arm skin, not a hand. Any D2 work must not inherit this "tip" as hand evidence.

---

## 3. THE UNRESOLVED REASON, QUOTED (criterion 2)

### 3.1 The admission rule chain

- `code/actual_target_fit.py:75-79`:
  ```
  # segments the pack does NOT declare endpoints for -> UNRESOLVED (no fabricated length)
  UNRESOLVED = {
      "thorax", "ulna", "ulna_l", "hand_r", "hand_l",
      "talus_r", "talus_l", "toes_r", "toes_l",
  }
  ```
- `code/actual_target_fit.py:6-8` (module docstring): "Segments whose endpoints the pack DOES NOT declare (hands: no finger joints; feet: no digit joints) stay UNRESOLVED - their muscle sites remain ORDERED but unplaced, their shared measured joints remain preserved."
- `code/actual_target_fit.py:66-67`: "The source FOREARM bone is the RADIUS (its head articulates at the elbow); the source ULNA is a 2.3 cm elbow-head piece the pack does not declare - ulna is UNRESOLVED."
- `code/actual_target_fit.py:202`: resolved path requires `pk = SEG_EVIDENCE[body]` — `SEG_EVIDENCE` (lines 68-74) has keys `femur_r/l, tibia_r/l, humerus, humerus_l, radius, radius_l, thorax_dummy` only. **No entry for ulna/ulna_l/hand_r/hand_l** → they cannot take the measured path.
- `code/compiler.py:170-172` (the per-axis law): "An axis with neither source is AXIS_UNRESOLVED; unless every axis is sourced the segment is not fitted (never silently inheritance of a neighbour's length)."
- `code/schema.py:135-137`: "Every fitted scale axis must be sourced by EXACTLY ONE of: an explicit pair (AXIS_EVIDENCE) or an authored value (AXIS_ASSUMED). An axis with neither is AXIS_UNRESOLVED; a segment with any unresolved axis is not 'repaired'…"
- Packet record (all four bodies, `runs/actual_monkey_fit.json` → `unresolved_segments`): `"reason": "no fitted scale (axis source missing; not silently repaired)"`, `"axial": "declared_unresolved"` — the `declared_` prefix is exact: the correspondence itself asserts it.
- Session 2 membrane amendment (`session_reports/anatomy_compiler_02.md:4`): "segments whose endpoints the target does not declare stay **UNRESOLVED** (never a silently inherited length)". Session 2 §7: "The trunk (`thorax`), elbow-head (`ulna`), hands and feet scale is **unknown** from the pack: no target joint declares their endpoints. Leaving them unresolved is the law's answer, not a stall."

### 3.2 What IS authored for the four bodies (live receipt — this is the part the frozen preregistration got wrong)

`correspondence.py` (189 lines) contains **only validation** (`collect_refusals`) and frame/chirality machinery — zero body names. The authored correspondence is CONSTRUCTED in `actual_target_fit.py::_build`, and it DOES author entries for all four bodies, via `ANCHOR` (lines 155-161: `"ulna": "elbow_R", "ulna_l": "elbow_L", "hand_r": "wrist_R", "hand_l": "wrist_L"`) and the `body in UNRESOLVED` branch (lines 183-199).

Live rebuild from module copies (digest **`52c92fe0d207a5997…7df8` MATCHES the shipped packet's `correspondence_sha256`** — byte-identical correspondence; receipt `receipts/correspondence_receipt.txt`):

- 18 segments, 79 landmarks, `collect_refusals -> 0 refusals` (the anchor-only authorship is ACCEPTED by the validator).
- Every one of the four: `proximal_landmark == distal_landmark` (e.g. `ulna.prox` and `ulna.dist` both = elbow_R `[−0.1155, 0.3191, −0.0061]`; `|prox − dist| = 0.000000e+00 m`), `axial_unresolved=True`, `axis_evidence={}`, `axis_assumptions={}`, coords carried (`['elbow_flexion']` / `['wrist_dev_r','wrist_flex_r','wrist_3_r']` / mirrors), and note field: **`"no pack distal joint; coord anchor elbow_R (not a fitted length)"`** (ulna), `… wrist_R …` (hand_r), mirrors `_l`.
- Hand roll refs are the fabricated offset `P + [0.05, 0, 0.05]` (line 191) — used only to carry coords, never a length claim.

**So the failing precondition per body is exactly one: no entry in `SEG_EVIDENCE` because the pack declares no distal endpoint joint for the segment — NOT a missing correspondence entry, and NOT a validator refusal (refusals are 0).**

### 3.3 Decision trail (reports 02–04)

- Session 2 (§3, correction 1): "First mapping attached it to `ulna` and produced the absurd fitted ulna 2.81×; the corrected radius fits at **0.222×**" — the elbow→wrist pack pair was assigned to the RADIUS by measurement; the ulna was left with no pair.
- Session 2 (§2): `axial_unresolved` introduced as an author-declared field; `build_segments` returns unresolved bodies "reported, not refused".
- Session 3 (§8): "Trunk, hands, feet, elbow-head scales remain unresolved (no declared endpoints) — never invented."
- Session 4: admission split; nothing re-opens the four bodies.
- ERRATA E-2 (2026-09-24) re-confirms the ownership chain (ulna owns `elbow_flexion`; hands own the wrist triples) in its corrected causal account.

---

## 4. CLASSIFICATION (criterion 3) + RESOLUTION NEEDS (criterion 4)

### 4.1 Per body

**`ulna` and `ulna_l` — class (I): missing identifiers, with a genuine (U) anatomy-decision component. NOT (G).**
- Deciding quote (pack): ulna-specific joint names in the 28-joint pack: **[]** (measured, §2.0).
- Deciding quote (code): "the source ULNA is a 2.3 cm elbow-head piece **the pack does not declare** - ulna is UNRESOLVED" (actual_target_fit.py:67); `SEG_EVIDENCE` has no ulna key.
- Geometry exists (forearm skin is measured — session-3 envelope medians b 20.2 mm / c 22.9 mm; my wrist-band census) → not (G).
- The (U) component: even with unlimited evidence gathering, no pack measurement can locate a 2.3 cm bone piece INSIDE the forearm skin — DERIVATION §5/session-3 law: the skin envelope "is NOT internal anatomy" evidence. And which segment owns elbow→wrist was ALREADY a measured taste call ("First mapping attached it to `ulna`… corrected radius fits at 0.222×", report-02 §3). Un-splitting that pair for the ulna is anatomy judgment, not measurement.
- Resolution need: **architect authorization** (an authored axial decision for the ulna piece — the membrane permits authored axes, e.g. thorax_dummy's identity and the forearms' authored transverse; what is missing is the CONTRACT's permission for THESE bodies, see §4.3) — evidence gathering alone cannot close it.

**`hand_r` and `hand_l` — class (I) dominant (pack declares no distal anchor), with a real (U) extent/boundary component; NOT (G).**
- Deciding quote (pack): nothing distal to `wrist_L/R` among the 28 joints (§2.0); the note field authored at runtime: **"no pack distal joint; coord anchor wrist_R (not a fitted length)"**.
- Geometry EXISTS → not (G): connected skin 0→111.4 mm distal of each wrist (§2.1). The preregistration's "target CONTAINS usable wrist-region geometry and joint anchors (elbow_L/R, wrist_L/R)" is CONFIRMED with numbers.
- The (U) component (measured, honest): (a) the distal skin's OWNERSHIP leaves the arm entirely at ~41 mm (tail_base/spine_lower, §2.2) — the pack gives no hand-owned region at all; (b) the rig's own hand-tip law fails on this mesh (§2.3); (c) the blob's length (111 mm = 1.72× forearm) cannot be validated against a source hand length (source hand piece 0.0428 m, session-2 trace; scale unresolved) — "where does the hand end" is genuinely undetermined by current identifiers; (d) digits: **articulated digits are `absent_in_source`** (DERIVATION §12; measured: zero digit joints in the XML while 27 hand-skeleton meshes sit welded on the hand bodies) — a permanent source-side absence no target evidence can change.
- Resolution need: **architect authorization for an authored palm anchor + extent policy** (taste), optionally preceded by bounded evidence-gathering (a better hand-boundary estimator than the broken tip law — legal diagnostic work). Digit articulation: would require INVENTING anatomy — forbidden; stays `absent_in_source`.

### 4.2 Summary table

| body | class | deciding evidence | resolution needs |
|---|---|---|---|
| `ulna` | **(I)** + (U) component | no ulna pack joint ([]); SEG_EVIDENCE lacks it; 2.3 cm source piece; skin-only target evidence | AUTHORIZATION (authored anchor/split decision); evidence cannot locate it |
| `ulna_l` | **(I)** + (U) | mirror of ulna | same |
| `hand_r` | **(I)** dominant + (U) extent | no distal pack joint; anchor-only segment authored; skin blob exists (111.4 mm) but is owned by tail_base/spine_lower past 41 mm; rig tip law broken | AUTHORIZATION (palm anchor + extent policy); optional bounded boundary estimator first; digits = `absent_in_source`, never resolvable |
| `hand_l` | **(I)** dominant + (U) | mirror | same |

### 4.3 The precise D2 lever (for the architect)

The machinery can already express a resolution: `axis_assumptions` with `provenance: authored` is first-class (schema.py:135-137; thorax_dummy and both forearms already ship authored axes). The four bodies stay unresolved ONLY because the session-2 membrane amendment declared that missing pack endpoints ⇒ UNRESOLVED (report-02 line 4), implemented as the `UNRESOLVED` set + `axial_unresolved=True`. Changing the outcome is therefore a CONTRACT/AUTHORIZATION change (which bodies may carry authored axial assumptions and at what anchored values), not a capability gap and not a data-availability gap for the palm region. Per the wave-2 laws I made no such assignment and no fitting search; the numbers above are the evidence an authorization would rest on.

---

## 5. UNCERTAINTY (what I could NOT determine)

1. **Anatomical identity of the distal blob.** I measured it numerically (connected, paddle-shaped, 47.1 × 18.1 mm far-end cross-section, 111.4 mm long) but could not visually inspect the mesh (no image rendering in this audit). It is consistent with palm+minit digits of a hanging macaque, but I cannot rule out that part of the 40–111 mm range is non-hand skin mis-bound by the rigger (the ownership anomaly is a warning).
2. **Cause of the ownership anomaly** (tail_base/spine_lower primary-binding skin at x≈0.17–0.20 m): the JNT3 pack format records `assign` indices but no provenance for them; the skinning-tool behavior is outside the baseline.
3. **Fine digit structure:** at 8 mm voxels, digit-scale protrusions (~8 mm) could merge into one component; absence of resolvable digit separation is resolution-limited, not proven.
4. **Source hand mesh extent:** the 27 hand-skeleton geom meshes are external assets (not in the baseline), so the source hand's full skeletal LENGTH is bounded only by geom `pos` (e.g. `5distph` at y=−0.127) plus unknown mesh sizes; I cite the session-2 measured site span 0.0428 m instead.
5. **R-side independent verification:** R numbers are identical to L because the mesh is exactly x-mirrored (all censuses returned identical counts); I verified symmetry numerically, not by separate cluster analysis.

## 6. PREREGISTRATION VERDICT (frozen text in `brief.md`)

- PREDICTION component "no authored landmarks for them in correspondence.py": **FALSIFIED AS WRITTEN.** correspondence.py holds only validation; the run's correspondence authors anchor-only landmarks for all four (prox=dist=anchor, `axial_unresolved=True`), and `collect_refusals` returns 0 — the rebuild digest matches the shipped packet (`52c92fe0…`).
- FALSIFIER prong 2 ("the correspondence DOES contain ulna/hand entries that fail on data (not authoring)"): **FIRED.** The entries exist; they fail because `SEG_EVIDENCE` has no key for them — the pack declares no distal endpoint joint (a pack-data absence).
- PREDICTION component "the target actually CONTAINS usable wrist-region geometry and joint anchors (elbow_L/R, wrist_L/R) — class (I) dominates, not (G)": **CONFIRMED.** Wrist anchors exist (both sides, 263-vert bands); connected skin exists 111.4 mm distal of each wrist; no criterion-1 dossier found missing target geometry for these regions. (I) does dominate — with the precision that the missing identifiers are pack joint anchors, not authored mapping entries.
- "articulated digits genuinely absent in source per DERIVATION §12": **CONFIRMED** (zero digit joints in the XML; 27 welded hand-skeleton meshes per hand body).

## 7. BASELINE INTEGRITY (criterion 5)

Command run first action and re-run after all work:

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)
```

Both runs: **empty output — baseline untouched.** All module executions used copies in `audits/B1_source_anatomy/work/` with `PYTHONDONTWRITEBYTECODE=1`; the live `.tmp/chimanoid.xml` and `Saved/meshes/*` were read/hashed only (hash-equality to baseline recorded in §1/§2). No git write commands, no network, no files written outside `audits/B1_source_anatomy/`.

## 8. RECEIPTS (exact commands + key outputs; full logs in `receipts/`)

| receipt | command | key output |
|---|---|---|
| `source_anatomy.txt` (+ `_run.log`) | `PYTHONDONTWRITEBYTECODE=1 python scripts/b1_source_anatomy.py` | 19-body tree; per-body joints/sites/inertial (§1); 120 spatial tendons / 468 referenced sites (matches DERIVATION §2); digit-joint search `[]` |
| `tendon_membership.txt` | inline XML query (§3 of run log) | all 30 sites tendon-referenced; per-site tendon, index/len, terminal-vs-interior |
| `target_hand_region.txt` | `python scripts/b1_target_anatomy.py` | 28-joint list; wrist bands 263 verts / 20.0 mm; first-cut (contaminated) cylinder census |
| `target_hand_region_v2.txt` | `python scripts/b1_target_hand_v2.py` | ball ownership census; nearest-joint field n=1246; **rig tip-law failure** (top-30 = shoulder_L-owned, 0.1351 m proximal) |
| `target_hand_region_v3.txt` | `python scripts/b1_target_hand_v3.py` | per-5mm slab owner census (elbow_L 0–40.8 mm; tail_base/spine_lower 40.6–111.3 mm); far-end bbox + 47.1×18.1 mm; single 8-mm-voxel component |
| `correspondence_receipt.txt` | `python scripts/b1_correspondence_receipt.py` (module copies in `work/`) | 18 segments; 0 refusals; per-body anchor-only authorship with `|prox−dist|=0.0`, note "no pack distal joint; …" |
| digest match | inline `atf._correspondence_digest(corr)` on the rebuild | `52c92fe0d207a59971d9765d10009fc4f1d94e0f0e38e2eea59a1d64be4a7df8` == shipped `admission_actual_monkey.json.meta.correspondence_sha256` |
| chain distances | inline XML pos accumulation | 0.3487 / 0.0231 / 0.2920 m (matches report-02's 0.023/0.292) |
| input identity | `sha256sum` baseline vs live | all four files pairwise identical |
| baseline integrity | `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` | empty (start and end) |

## 9. NULL / NEGATIVE RESULTS (preserved, they are results)

1. No digit joints exist anywhere in the source XML (search over all 141 joint elements, digit-like name filter: empty).
2. No ulna-specific joint in the 28-joint target pack; nothing distal to wrist_L/R.
3. No hand-owned skin in the pack: the wrist joint's own band is forearm skin (7 distal verts, ≤1.8 mm); past ~41 mm the binding leaves the arm (tail_base/spine_lower).
4. The rig's `hand_tip` measurement law returns upper-arm skin, not a hand — unusable as hand evidence.
5. `correspondence.py` contains no body names at all — it is pure validation; body-specific authoring lives only in `actual_target_fit.py`.
6. No refusal is raised for the four bodies: the validator ACCEPTS the anchor-only authorship; "unresolved" is a declared contract state, not an error state.
