# B3 — Mechanical Requirements Sheet: ulna, ulna_l, hand_r, hand_l

**Agent:** B3 (requirements; read-only + spec writing) · **Date:** 2026-09-24
**Baseline (READ-ONLY):** `E:/PythonChimera/forearm_package/baseline_snapshot/` (MANIFEST git head `c70b7a6c`)
**Governing contract:** `baseline_snapshot/code/DERIVATION.md` (membrane v1) + its implementing code (`schema.py`, `correspondence.py`, `compiler.py`).
**Citations:** `DER.md §x / Lnnn` = baseline DERIVATION.md line; `file.py:Lnnn` = baseline code lines; `XML Lnnn` = baseline source_xml/chimanoid.xml lines. Wave-1 receipts cited as `A2/A4/A8 report §x` under `forearm_package/audits/`.

---

## 0. Verified inputs (this audit)

| input | sha256 (head) | check |
|---|---|---|
| inputs/monkey_birth.bin | `550A5B3E…AABFA3C` | == MANIFEST.json:153 == A4 method header |
| inputs/monkey_joints.bin | `74B3AB04…50C1662` | == MANIFEST.json:158 == A4 method header |
| runs/actual_monkey_fit.json | `A4475550…` (via MANIFEST) | packet records quoted below |
| source_xml/chimanoid.xml | `675E00D0…` | == MANIFEST.json:248 |

My read receipts: `receipts/b3_pack_read.txt` (JNT3 pack enumeration), `receipts/b3_fit_packet_extract.txt` (fit-packet records for the four bodies). Baseline untouched (§9).

---

## 1. The three contract sources of mechanical requirements

Every requirement below derives from exactly three mechanisms of the existing contract. Stated once here; per-body sheets cite them.

**(a) GEOMETRY — per-edge fitted frame.** Each source body with a parent is an EDGE fitted from three authored target landmarks: proximal `P` (= the body's fitted origin), distal `P_d`, roll reference `Q`:
> "Per-edge recursion: given the fitted parent origin, each child edge's **proximal anchor `P` = fitted proximal-landmark; distal `P_d` = fitted distal-landmark**. The child origin IS `P` (shared joint). `P` and `P_d` come from target landmarks expressed in target world (after global_scale)." (DER.md §4, L125-128)
> ONB: `a = normalize(P₁−P₀)`; `t = (Q−P₀) − a·(a·(Q−P₀))`; `b = t/|t|`; `c = a×b`; "No roll-ref, or `|t| < ε` (`axis_parallel_roll`), ⇒ refusal" (DER.md §5.1, L153-167; `compiler.py:58-68`, `ROLL_EPS = 1e-9` at `compiler.py:48`).
> Scale: `s_a = |P_d − P| / |D − A|`; policy `uniform` (default) sets `s_b = s_c = s_a` — an AUTHORED assumption, never evidence (DER.md §4.3 L129-131; `compiler.py:229-235`).
> A segment is RESOLVED only when every axis is sourced by evidence or authored assumption; otherwise it is UNRESOLVED: sites get NaN, joint axes get NaN (`compiler.py:239-243`, `425-463`, `467-499`; DER.md §11 `insufficient_landmarks` L293).

**(b) COORDINATES — one owner edge per coordinate; arm evaluation.**
> "Each coordinate `q` is authored on one edge (a direct `<joint>` of that edge's child body), carrying source axis `ω̂_src`... Fitted axis `ω̂ = G·ω̂_src`; fitted hinge center `J` = fitted child origin." (DER.md §8.1, L215-221)
> Subtree rule: `∂s/∂q = ω̂ × (s − J)` for sites owned by bodies in the joint's subtree, else 0 (DER.md §8.2, L230-233; `compiler.py:905-932`; subtree verified A8 §0: `subtree(ulna) = {ulna, radius, hand_r}`).
> Coordinate ownership is FIXED BY THE SOURCE: intake records DIRECT joint children only (`schema.py:68`), each coordinate may be claimed by exactly one correspondence segment (`correspondence.py:165-170` `duplicate_coord`), and every non-root coordinate must be claimed (`correspondence.py:172-175` `unassigned_coords`). Joint ranges are carried verbatim (DER.md §2 L98-99, §12 `kinematically_preserved`; verified A8 §4 for all 8 forearm coordinates).

**(c) OWNERSHIP SEMANTICS — sites, tendon paths, shared joints.**
> "Every `SourceSite` (468) is owned by one segment (its direct child body)... fitted local `x'_loc = S · x_loc`, fitted global `x' = P + B'eff·x'_loc`." (DER.md §7, L205-207) A tendon path is its ordered site refs' fitted global points; rest length = polyline sum (DER.md §7 L208-209).
> Shared joints are structural: "the compiler verifies `|P_edge_parent_distal − P_edge_child_proximal| < 1e-9`" (`JOINT_EPS = 1e-9`, `compiler.py:47`); the check applies to each parent's FIRST child (`compiler.py:399-423`), refusal `shared_joint_separation` (L422-423). A path with any unplaced site is `path_incomplete` (no rest length, NaN arms); a coordinate whose owner body is unresolved has NaN axis and NaN arms (`compiler.py:503-531`).

---

## 2. Existence mapping (what EXISTS today)

### 2.1 Source tree and coordinate ownership (chimanoid.xml — measured)

```
thorax
└─ humerus   [shoulder_elv, shoulder_rot, elv_angle]        (XML L534, J L589-591)
   └─ ulna   [elbow_flexion]        10 sites                (XML L593, J L607, sites L597-606)
      └─ radius      (NO joint) 17 sites                (XML L608, sites L612-627)
         └─ hand_r [wrist_dev_r, wrist_flex_r, wrist_3_r]  5 sites + 31 static hand/finger geoms
                   (XML L629, J L668-670, sites L663-667, geoms L632-661)
humerus_l → ulna_l [elbow_flexion_l] → radius_l (no joint) → hand_l [wrist_dev_l, wrist_flex_l, wrist_3_l]
(XML L675 / 733 / 747 / 748 / 769 / 806-808)
```

- Focal fact: `hand_r` is a child of **radius**, and `radius` is a child of **ulna**. Three internal shared points per arm: elbow (humerus/ulna), the proximal radioulnar point (ulna/radius; source distance ulna origin → radius origin = 0.02307 m — the "2.3 cm elbow-head piece"), and the wrist (radius/hand; source radius origin → hand origin = 0.29203 m).
- `radius`/`radius_l` own ZERO coordinates (no direct `<joint>`); they are pure geometry/site carriers.
- Fingers exist in the source ONLY as static geoms inside hand_r/hand_l (28 bone meshes + 3 capsules each; XML L632-661 / 770-799) — no digit bodies, no digit joints.

### 2.2 Target pack (monkey_joints.bin JNT3 + monkey_birth.bin — my receipt `b3_pack_read.txt`)

- **28 joints total; none distal of the wrist on either arm**: `FK children of wrist_R: NONE`, `FK children of wrist_L: NONE`; `digit-like joint names: NONE`.
- Forearm anchors exist: `elbow_R (−0.1155, 0.3191, −0.0061) m`, `elbow_L (+0.1155, …)`, `wrist_R (−0.1450, 0.2615, −0.0060) m`, `wrist_L (+0.1450, …)`; FK chain `shoulder→elbow→wrist`; measured spans `|elbow−shoulder| = 79.868 mm`, `|wrist−elbow| = 64.745 mm` (both sides; matches A2 §5.4 wrist axial 64.745 mm).
- Mesh: 18 459 verts / 36 630 tris; bbox y ∈ [−0.0013, 0.6481] m. Joint vertex bands: elbow 318 primary-owner verts, wrist 263 (per side). A wrist-crease seam fold persists distal of 51.1220 mm (A2 §4: 1 255 duplicated-coordinate vertices; sweep to 80 mm still 2 loops; distal end unmeasured).
- One reproducible mesh measurement exists distal of the wrist: `tips["hand_tip"]` = centroid of the 30 vertices farthest beyond `wrist_L` (`mesh_target.py:139-161`, specifically L156) — machinery, not a pack joint.

### 2.3 Recorded fit state for the four bodies (`actual_monkey_fit.json`; my receipt `b3_fit_packet_extract.txt`)

- Authored correspondence: `ulna/ulna_l` anchored at `elbow_R/L` and `hand_r/hand_l` at `wrist_R/L` with `distal == proximal` and `axial_unresolved = True` — "no pack distal joint; coord anchor (not a fitted length)" (`actual_target_fit.py:155-161, 183-199`; tables L24-33).
- Fit result: all four bodies in `unresolved_segments` — "no fitted scale (axis source missing; not silently repaired)".
- Joint records: `elbow_flexion(_l)` origin **== target elbow_R/L exactly**; wrist triples' origin **== target wrist_R/L exactly**; `axis: null`, `status: "unresolved_body"`, reason `"body ulna: no fitted scale (endpoints not declared); axis not claimed"`.
- Sites unplaced (NaN): ulna 10/10, ulna_l 10/10, hand_r 5/5, hand_l 5/5 — 30 sites.
- Tendon impact (right; left mirrors): `PT` blocked by `['ulna']`; `ECRL/ECRB/FCR/FCU` by `['hand_r']`; `ECU` by `['hand_r','ulna']`; `BRD` derived (complete) (packet tendons; A8 §5).
- Arm census (A8 §2): 562/702 scoped pairs NaN (306 unresolved-owner + 256 path-incomplete); the grasp coordinates `elbow_flexion(_l)` + 6 wrist coords are **UNDEFINED, not dead** (E-2, A8 finding C).
- Resolved forearm reference: radius/radius_l uniform scale s = 0.22170679566544982, det(Q)=+1, det(R)=s³ (A4 §1) — anchored `elbow_R/L → wrist_R/L` with roll `site:PT-P2`/`PT_l-P2` (A4 §1).

### 2.4 Schema capacity — can a ulna/hand entry be authored today?

**YES — demonstrated by the shipped baseline itself.** The four bodies are ALREADY correspondence segments (`source_body`, `parent`, `proximal_landmark`, `distal_landmark`, `roll_ref`, `coords`, scale policy fields — `schema.py:124-151`), authored through the exact validation path (`correspondence.py:106-184`) and accepted green by the fit with `coords` declared. Upgrading them to resolved entries = changing their landmark values / dropping `axial_unresolved` / declaring the scale policy. **No schema field, refusal code, or validation rule is missing.** The only hard guards that constrain authoring: `chain_conflict` — a segment's `parent` must equal the intake parent (`correspondence.py:113-117`), so coordinate ownership and tree parentage CANNOT be re-authored; and the first-child shared-joint closure (`compiler.py:399-423`).

### 2.5 Assumptions stated (light mesh read; B1's dossier is not duplicated)

- A-1: The birth mesh has a well-posed skin in the hand region (distal of wrist) from which an off-axis roll witness and a distal hand landmark are measurable. Support: A2 swept axials to 80 mm (mesh measures fine; crease persistent), `hand_tip` machinery exists; NOT independently verified by B1's full dossier — B1 to confirm.
- A-2: Bilateral near-symmetry (A4 §3: max pair deviation 0.6306 mm) supports authoring `ulna_l`/`hand_l` as mirrored images of the right-side evidence; each side remains individually authored landmarks (the contract has no automatic mirroring of segments).
- A-3: Mesh extent suffices for landmark evidence classes already in use (joint bands, band roll witness, tip centroid) — the same classes that resolved radius/radius_l.

---

## 3. Per-body requirements sheets

Legend for gap class: **SWEC** = SATISFIABLE-WITH-EXISTING-CONTRACTS · **NNE** = NEEDS-NEW-EVIDENCE (new landmark/measurement to author; no contract change) · **ARCH** = ARCHITECTURAL (cannot be met by authored landmarks under the existing schema — architect ruling required).

---

### 3.1 ULNA (right) — the elbow edge

Source facts: body `ulna`, parent `humerus` (XML L593); owns coordinate `elbow_flexion` (hinge, axis (0,0,1) local, range [0, 2.26893], XML L607); owns 10 sites (TRIlong-P5, TRIlat-P5, TRImed-P5, ANC-P2, BRA-P4, BRA-P3, ECU-P2/P3/P4, PT-P2; XML L597-606); has child `radius` (its first and only child; source proximal radioulnar offset 0.02307 m). Subtree for arm evaluation: `{ulna, radius, hand_r}` (A8 §0).

| id | requirement | contract cite | exists? | deciding evidence/quote | class |
|---|---|---|---|---|---|
| ULN-G1 | Proximal landmark P = elbow point (becomes fitted origin and the elbow hinge center J) | DER §4 L125-128; §8.1 L218-220 | **YES** — `elbow_R` (pack joint); already authored as ulna's anchor | Packet: `elbow_flexion.origin == (−0.11548, 0.31911, −0.00608)` == `elbow_R` (my extract; pack read) | **SWEC** |
| ULN-G2 | Distal landmark P_d = the ulna/radius SHARED joint (a point ≈7.9 % of the elbow→wrist span distal of the elbow if the recorded forearm scale is taken as the feasibility ratio — arithmetic from recorded values, NOT an authored landmark) | DER §4 L125-128 + L135-140 (shared joint one point) | **NO** — no pack joint there; today `P_d := P` (zero span, `axial_unresolved`) | `actual_target_fit.py:76-79` UNRESOLVED set; :67 "the source ULNA is a 2.3 cm elbow-head piece the pack does not declare - ulna is UNRESOLVED"; my pack read: only elbow/wrist exist on the arm chain | **NNE** (new mesh-measurable landmark X per side) |
| ULN-G3 | Roll reference Q with off-axis witness (\|t\| > 1e-9) for the elbow→X axis | DER §5.1 L153-167; refusal `axis_parallel_roll` | **NO** (today's Q is a fixed offset from the degenerate anchor) | Machinery exists: band roll witness over the 318-vertex elbow band (`actual_target_fit.py:89-97` `_band_roll`) | **NNE** |
| ULN-G4 | Scale policy declared with all three axes sourced (axial = \|X−elbow\|/\|D−A\|; b/c = uniform-authored at axial, radius-edge precedent) | DER §4.3 L129-131; §11 `bad_scale_policy`; `compiler.py:229-235` | **NO** — follows G2/G3 | Precedent: radius b/c authored "uniform transverse assumed = axial for the forearm" (tables L17-22) | **NNE** |
| ULN-C1 | Coordinate `elbow_flexion` stays authored on the ulna edge; axis carried `kinematically_preserved`, rotated by G once the frame resolves | DER §8.1 L215-221; §12 L302-303; schema `coords` (`schema.py:130`); `correspondence.py:165-170` | **YES** — ownership + range verbatim already in packet; axis is a pure function of G1–G4 | Packet: elbow_flexion range [0, 2.26893] carried; `axis: null` pending frame; A8 §4 q-range check | **SWEC** (contingent on G1–G4) |
| ULN-C2 | Arm evaluation inputs: J = fitted origin (= elbow_R), ω̂ = G·(0,0,1), subtree {ulna, radius, hand_r} | DER §8.1-8.2 L215-233; `compiler.py:905-932` | Machinery exists and is F1/F5-verified (A8 §3 FD crosscheck) | A8 §0 (subtree), §2 (arms NaN today purely because owner unresolved) | **SWEC** (contingent) |
| ULN-O1 | 10 sites placed (fitted global) → completes PT path (PT-P2) and ECU path (with hand site) → elbow arms become finite for every tendon crossing the elbow boundary (BRD today; PT, ECU, BIC* once their other sites land) | DER §7 L205-209; §8.2 L230-233; `compiler.py:467-501, 503-531` | **NO** — 10/10 NaN today | Packet: `PT_tendon status: path_incomplete:unresolved_bodies ['ulna']`; A8 §5 | **NNE** (contingent on G2–G4) |
| ULN-O2 | Mass/inertia carriage rides the same fitted frame (S, P) | DER §9 L253-265 | rides G1–G4 | §9 closed forms; tables show TRANSPORT only for resolved bodies | **NNE** (contingent) |

**Ulna structural tension (the preregistered one — measured, not chosen):** because `radius` is ulna's first child, the closure rule demands `|radius.P − ulna.P_d| < 1e-9` the moment ulna is RESOLVED (`compiler.py:408-423`: closure is skipped only while the parent is unresolved). The shipped correspondence authors `radius.P = elbow_R` (`actual_target_fit.py:72`). Therefore authoring `ulna.P_d = X ≠ elbow_R` while keeping `radius.P = elbow_R` produces `shared_joint_separation` — measured machinery behavior, the partition of the single elbow→wrist span between the two serial edges is ENFORCED, not optional. Consequences are enumerated in §6 (flag F-2); choosing between them is the architect's D2 ruling, not B3's.

---

### 3.2 ULNA_L (left) — mirror of §3.1

Identical requirement set with: P = `elbow_L` (+0.11548, 0.31911, −0.00608; exists); coordinate `elbow_flexion_l` (XML L747, range [0, 2.26893], A8 §4); 10 `_l` sites (XML L737-746); subtree `{ulna_l, radius_l, hand_l}`; tendon impact: `PT_l` blocked by `['ulna_l']`, `ECU_l` by `['hand_l','ulna_l']`. Same classes: G1 **SWEC**, G2–G4, O1–O2 **NNE**; same structural tension via `radius_l` (first child of `ulna_l`, currently anchored `elbow_L`; `actual_target_fit.py:72, 77`).

---

### 3.3 HAND_R (right) — the wrist edge

Source facts: body `hand_r`, parent `radius` (XML L629); owns coordinates `wrist_dev_r`, `wrist_flex_r`, `wrist_3_r` (hinges; source axes (−0.819,−0.136,−0.557), (0.956,−0.252,0.147), (0,1,0); ranges [−0.436332, 0.610865], [−0.610864, 0.610864], [−1.22173, 1.22173]; XML L668-670); owns 5 sites (ECRL-P4, ECBR-P4, ECU-P6, FCR-P3, FCU-P4; XML L663-667) + 31 static hand/finger geoms (L632-661); leaf (no children) ⇒ subtree = `{hand_r}`.

| id | requirement | contract cite | exists? | deciding evidence/quote | class |
|---|---|---|---|---|---|
| HAN-G1 | Proximal landmark P = wrist point (= fitted origin = all three wrist hinge centers J) | DER §4 L125-128; §8.1 L218-220 | **YES** — `wrist_R`; already authored as hand_r's anchor; ALSO already `radius.P_d` → F1 closure satisfied with **zero re-anchoring** | Packet: wrist triple origins == wrist_R exactly (my extract); closure: `hand.P == radius.P_d == wrist_R`, sep 0 | **SWEC** |
| HAN-G2 | Distal landmark P_d = a hand distal reference (leaf: source-side precedent is the farthest referenced site; target side has NO pack joint — FK children of wrist: NONE) | DER §4 L125-128; leaf-distal machinery `actual_target_fit.py:172-177`; `synthetic_fixtures.py:39-43` | **NO** — today `P_d := P` | My pack read: no joint distal of wrist; machinery exists: `hand_tip` = 30-vertex centroid beyond wrist (`mesh_target.py:156`) | **NNE** |
| HAN-G3 | Roll reference Q off the wrist→P_d axis (\|t\| > 1e-9 else `axis_parallel_roll`) | DER §5.1 L153-167 | **NO** (today: fixed offset from degenerate anchor) | Machinery: `_band_roll` on the 263-vertex wrist band; A-1 assumption (hand-region skin, B1 to confirm) | **NNE** |
| HAN-G4 | Scale policy: axial = \|P_d−P\|/\|D−A\| (source leaf ref = farthest referenced site); b/c sourced (uniform-authored precedent, or aspect with width landmarks if authored) | DER §4.3 L129-131; §11 `bad_scale_policy` L294 | **NO** — follows G2/G3 | Schema accepts either policy (`correspondence.py:127-130`) | **NNE** |
| HAN-C1 | Three wrist coordinates stay authored on the hand edge; axes rotated by G_hand when the frame resolves; ranges verbatim | DER §8.1 L215-221; `schema.py:68,130`; `correspondence.py:165-170` | **YES** — ownership + ranges already carried; axes are functions of G1–G4 | Packet: wrist axes null pending; ranges verified A8 §4 | **SWEC** (contingent) |
| HAN-C2 | Arm evaluation: J = fitted hand origin (= wrist_R); ω̂_i = G·ω̂_src,i (three NON-axis-aligned source axes); subtree = {hand_r} ⇒ ONLY the 5 hand-owned sites move under wrist motion; finite arm requires a path crossing the wrist boundary (forearm site + hand site) | DER §8.1-8.2 L215-233; `compiler.py:905-932` | Machinery verified (A8 §3 FD); boundary-crossing structure already measured: entry bends 20–65° at the elbow (A8 §2) | My tendon census: ECRL/ECRB/FCR/FCU paths need ONLY hand sites to complete (their other sites are humerus/radius = resolved); ECU additionally needs ulna | **SWEC** (contingent) |
| HAN-O1 | 5 sites placed → completes ECRL/ECRB/FCR/FCU paths immediately (wrist arms finite for 4 of 5 wrist motors with hand resolution ALONE); completes ECU only together with ulna | DER §7 L205-209; `compiler.py:503-531` | **NO** — 5/5 NaN today | Packet statuses quoted §2.3: `['hand_r']` ×4, `['hand_r','ulna']` ×1 | **NNE** (contingent on G2–G4) |
| HAN-O2 | Static finger/hand geoms ride the hand edge transform (§5: "body meshes scale by S in segment coordinates") — placement of finger GEOMETRY (not joints) arrives with the fitted frame | DER §5 L147-149 | rides G1–G4 | XML: 31 geoms are children of hand_r | **NNE** (contingent) |
| HAN-O3 | Mass/inertia carriage (hand mass 0.4575 kg source) rides the fitted frame | DER §9 | rides G1–G4 | tables: hand absent from TRANSPORT list today | **NNE** (contingent) |

**Measured dependency facts for D2 (stated, not decided):**
- Wrist transmission ⇔ hand edge resolved. Its P is conflict-free (already the radius edge's recorded distal landmark). The ONLY new evidence is distal: P_d + roll witness.
- Elbow transmission ⇔ ulna edge resolved. Its P is conflict-free; the conflict is at its DISTAL end (ULN tension), because the radius edge sits between ulna and hand in the source tree and today claims the whole elbow→wrist span.
- No authoring action can move a coordinate between bodies: `elbow_flexion` rides `ulna`, wrist triples ride `hand_r`/`hand_l`, permanently (`correspondence.py:113-117` chain_conflict; `schema.py:68` direct-children intake). "Hand/ulna body ownership" therefore concerns SITE/GEOMETRY/frame ownership and landmark partitioning — never coordinate ownership.

---

### 3.4 HAND_L (left) — mirror of §3.3

Identical requirement set with: P = `wrist_L` (+0.14499, 0.26148, −0.00596; exists; already `radius_l.P_d`); coordinates `wrist_dev_l`, `wrist_flex_l`, `wrist_3_l` (XML L806-808; ranges as right); 5 `_l` sites (XML L801-805); subtree `{hand_l}`; tendon impact: `ECRL_l/ECRB_l/FCR_l/FCU_l` blocked by `['hand_l']`, `ECU_l` by `['hand_l','ulna_l']`. Same classes: G1 **SWEC**; G2–G4, O1–O3 **NNE**.

---

## 4. DIGITS — the architectural fact, stated precisely

- **Source:** articulated fingers are `absent_in_source` — "tail / neck-head / articulated fingers: nothing matched such anatomy in the source; recorded under `unsupported`, never fabricated" (DER §12, L308-309). The XML contains NO digit bodies and NO digit joints: the fingers are 28 static `<geom>` meshes inside `hand_r`/`hand_l` (XML L642-661, L780-799). There is no coordinate to carry a moment arm, so DIGIT transmission is not authorable under any correspondence.
- **Target:** the JNT3 pack has 28 joints; none is digit-like (`digit-like joint names: NONE`, my receipt), and the FK chain terminates at wrist: `FK children of wrist_R/L: NONE`.
- **Consequence:** DIGIT transmission is ARCHITECTURALLY OUT OF SCOPE for this package. The evaluatable target is WRIST transmission (three coordinates per side, §3.3/§3.4) and ELBOW transmission (§3.1/§3.2), i.e. tension→torque at the two joints the contracts actually own.
- **Beyond that (flagged, not scoped):** any grasp qualification that requires finger JOINTS (wrap contact, phalanx torque) would require inventing anatomy absent from both source and target — prohibited by §12. What IS in scope after D2: wrist/elbow moment arms + static finger geometry placed by the hand frame (HAN-O2), which a downstream consumer may use for contact studies at its own risk. A pathology note: the hand-region skin carries an unwelded crease seam (A2 §4), so any mesh-based hand evidence inherits that topology.

---

## 5. Summary matrix (requirement × body × classification)

| requirement | ulna | ulna_l | hand_r | hand_l |
|---|---|---|---|---|
| G1 proximal landmark P (= hinge center J) | SWEC (elbow_R) | SWEC (elbow_L) | SWEC (wrist_R) | SWEC (wrist_L) |
| G2 distal landmark P_d | **NNE** (new X; ulna/radius shared joint) | **NNE** (X_l) | **NNE** (hand distal ref) | **NNE** (hand distal ref) |
| G3 roll ref Q (\|t\|>ε) | **NNE** | **NNE** | **NNE** | **NNE** |
| G4 scale policy (all axes sourced) | **NNE** | **NNE** | **NNE** | **NNE** |
| C1 coordinate ownership + verbatim range | SWEC | SWEC | SWEC | SWEC |
| C2 arm-evaluation inputs (J, ω̂, subtree) | SWEC* | SWEC* | SWEC* | SWEC* |
| O1 site placement → tendon path completion | **NNE*** | **NNE*** | **NNE*** | **NNE*** |
| O2 mass/inertia + static geom carriage | **NNE*** | **NNE*** | **NNE*** | **NNE*** |

`\*` = machinery exists and is falsifier-verified (A8 §3); the GAP is purely that the owning segment is unresolved today — each `NNE` row is filled by authoring landmarks, and every downstream `*` row follows deterministically (no contract change). Structural tension: ulna/ulna_l G2 drags `radius(_l).P` re-authoring with it (§6, F-2). Hand G2/G3 drags nothing (§3.3).

---

## 6. ARCHITECTURAL FLAGS (anything not satisfiable within existing contracts)

- **F-1 · DIGIT transmission — ARCHITECTURAL (out of scope).** Articulated fingers absent in source (DER §12 L308-309: `absent_in_source`), no digit joints in the pack (28 joints; FK terminates at wrist). Nothing to author; wrist transmission is the evaluatable target. Any finger-joint grasp mechanics would be new anatomy — §12 prohibits fabrication.
- **F-2 · The elbow/wrist anchor partition (the preregistered structural tension) — needs an ARCHITECT RULING, not a design choice.** Measured: the target offers exactly one point (elbow) where the source tree has two serial origins (ulna at the elbow; radius 0.02307 m distal), and the closure law (`compiler.py:399-423`, `JOINT_EPS = 1e-9`) makes the two edges PARTITION the elbow→wrist span once ulna is resolved: ulna (elbow→X) + radius re-anchored (X→wrist). The shipped radius record (A4 §1: s = 0.22170679566544982 anchored elbow→wrist) would be SUPERSEDED — a new fit record for radius/radius_l follows deterministically from the re-authored landmarks. Alternatives an architect might rule between, all inside or outside the contract, stated neutrally: (i) two-edge partition with new landmark X (inside contracts; NNE + radius record supersession); (ii) ulna permanently unresolved (inside contracts; elbow+wrist+PT+ECU transmission stays UNDEFINED — today's state). **Per the Wave-2 laws, B3 does not choose, and no choice was made on the basis of useful moment arms.** What is NOT available without changing the source intake: moving `elbow_flexion` off ulna, moving wrist triples off the hands, re-parenting radius (chain_conflict, `correspondence.py:113-117`).
- **F-3 · Hand-region landmark evidence rides an unverified-by-B1 assumption (A-1).** The hand edge's P_d/roll witness need mesh measurements distal of the wrist crease seam (A2: fold persistent to >80 mm; 1 255 duplicated-coordinate vertices). The measurement MACHINERY exists (`mesh_target.py:139-161`); whether the hand skin yields an unambiguous landmark is B1's dossier question. Flagged as a dependency, not a defect.
- **F-4 · Baseline-record supersession (documentation-level).** Any D2 resolution that authors new landmarks for these four bodies changes the shipped correspondence and hence the fit packet, tables, admission ledger, and the A4-verified radius transforms. Existing wave-1 receipts remain valid FOR THE RECORDED FIT; they cease to describe the live fit once D2 lands. Append-only errata discipline (ERRATA.md law) applies.

---

## 7. Preregistration verdict (frozen in brief.md — tested, not rewritten)

| prediction | measured result | verdict |
|---|---|---|
| All four bodies' GEOMETRY requirements satisfiable within existing contracts given new landmark evidence (NNE, not ARCH) | Every G-row is fillable by authored landmarks under `schema.py:124-151` + `correspondence.py` validation as-is; the schema already carries these four bodies as segments (tables L24-33) | **CONFIRMED** |
| Exactly one structural tension: elbow/wrist target joints anchor at most one edge each; source parentage decides whether ulna and hand can both claim anchors without a ruling | Hand CAN: its P (wrist) is already `radius.P_d` — closure-clean. Ulna CANNOT claim a distal anchor without re-anchoring `radius.P` (first-child closure, `compiler.py:408-423`). One tension, located at the ulna edge, exactly as predicted | **CONFIRMED** |
| DIGIT transmission ARCHITECTURAL (absent in source) | DER §12 `absent_in_source`; 28 pack joints, none distal of wrist; no digit bodies/joints in XML | **CONFIRMED** |
| FALSIFIER: any requirement that cannot be met by authored landmarks under the existing schema (forced contract change) | None found: all gaps are landmark-evidence gaps; F-2 is a ruling about WHICH authored landmarks, not about schema capacity | **NOT FIRED** |

---

## 8. Receipts (this audit)

- `receipts/b3_pack_read.txt` — JNT3 pack enumeration: 28 joints w/ positions, axes, ROM, FK parents; digit-name scan NONE; FK children of wrist NONE; span measurements; band vertex counts; mesh bbox. Script: `work/mesh_target_b3.py` (baseline `mesh_target.py` logic verbatim, input paths repointed to the read-only snapshot; hashes printed and matched §0).
- `receipts/b3_fit_packet_extract.txt` — fit-packet records: elbow/wrist joint origins == target joints, axes null, unresolved ledger rows, 30 unplaced sites, per-tendon blocking bodies. Extraction: inline python over `runs/actual_monkey_fit.json` (read-only).
- Wave-1 receipts relied on: A4 `report.md` §1 (radius/radius_l transforms + recorded correspondence anchors), A8 `report.md` §0/§2/§3/§5 (subtrees, 562/702 census, FD, transmission statement), A2 `report.md` §3-5 (wrist axial 64.745 mm, seam forensics), ERRATA.md E-2.

## 9. Baseline integrity

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)
```
All B3 writes confined to `forearm_package/audits/B3_mech_requirements/` (brief.md, requirements_sheet.md, report.md, receipts/, work/). Reads of the binary inputs went through hash-printing copies (`work/mesh_target_b3.py`); no baseline file opened for writing.
