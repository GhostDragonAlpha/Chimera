# B2 — Ownership Chain Audit (wave 2, D2 scope)

**Role:** evidence agent B2. **Date:** 2026-09-24. **Mode:** read-only + diagnostics; no baseline changes, no fitting, no production ownership, no mechanical qualification.
**Inputs (all read-only, hash-verified):** `baseline_snapshot/source_xml/chimanoid.xml` (sha256 `675e00d0…`, MANIFEST match), `runs/actual_monkey_fit.json` (sha256 `a4475550…`), `runs/admission_actual_monkey.json`, `runs/attachment_candidates.json`, `code/{intake,compiler,experiment_transverse_fit}.py`, `code/DERIVATION.md` §7–8.
**Method:** modules copied byte-identical into `work/`; enumeration re-derived from the XML via the snapshot's own `intake.load_source` (its count assertions 19 bodies / 39 coords / 468 path sites / 120 tendons / 120 muscles all held — intake.py:274-281), cross-checked against the fit packet and the frozen experiment output.

---

## 0. VERDICT SUMMARY

| # | Criterion | Verdict |
|---|---|---|
| 1 | Verified 16-tendon enumeration with full site→owner→fitted-status tables | **PASS** |
| 2 | Earliest-unresolved-dependency complete per tendon with path indices | **PASS** |
| 3 | D2-scope vs out-of-scope split exact with counts | **PASS** (12 in / 4 out) |
| 4 | Partial-evaluation inventory per tendon | **PASS** |
| 5 | Minimal-unlock-set statement with counts | **PASS** |
| 6 | Baseline integrity (`git status --porcelain -- baseline_snapshot` empty) | **PASS** (empty; 44/44 MANIFEST hashes match) |

**Preregistration verdict: CONFIRMED on all three predictions; no falsifier triggered** (details §2).

---

## 1. The ownership chain, stated mechanically

Per DERIVATION §7–8 and its implementation:

1. **Site → owner:** a site's owning body is its direct `<body>` parent in the XML (intake.py:133-139). Packet match: `site_owner_intake_vs_packet_match = true` for all 468 sites.
2. **Owner → fitted position:** a site gets a finite `fitted_pos_global` iff its owning segment is resolved (compiler.py:470-499); sites on the 9 unresolved bodies are `NaN` → exported `null` (strict JSON). Measured: 168 packet sites unresolved, owned by exactly the 9 admission bodies (`hand_l, hand_r, talus_l, talus_r, thorax, toes_l, toes_r, ulna, ulna_l` — admission_actual_monkey.json:31-41; packet/admission body lists match exactly).
3. **Positions → length:** rest length `L₀ = Σ|s_{j+1}−s_j|` is finite iff **every** path site is finite (comparability; compiler.py:508-512; experiment_transverse_fit.py:388-395). Otherwise `L₀ = null`.
4. **Length → moment arms:** `∂L/∂q` per coordinate requires (a) chain complete AND (b) the coordinate's owning body resolved (compiler.py:520-524). Exception: the 6 root `pelvis_*` coordinates get arm `0.0` **by definition, before the completeness gate** (compiler.py:514-519). Subtree rule for nonzero arms: site must lie in the jointed body's subtree (compiler.py:87-103, 905-932; DERIVATION §8.2).

**The 9 unresolved bodies own exactly 17 of the 39 coordinates:** `ankle_angle_{r,l}×3` (talus), `mtp_angle_{r,l}` (toes), `lumbar_rotation` (thorax), `elbow_flexion` (ulna), `elbow_flexion_l` (ulna_l), `wrist_dev/flex/3_r` (hand_r), `wrist_dev/flex/3_l` (hand_l). Packet joint statuses confirm: 30 `kinematically_preserved`, 9 `unresolved_body`.

---

## 2. Preregistration (frozen 2026-09-24) — measured verdict

| Prediction | Measured | Verdict |
|---|---|---|
| (i) ECRB/ECRL/FCR/FCU per side: earliest = HAND site at terminal index | ECRB idx3/4, ECRL idx3/4, FCU idx3/4, FCR idx2/3 — all terminal, owner hand_r/hand_l | **CONFIRMED** |
| (i) ECU: ULNA site mid-chain | ECU idx1 of 6 (`ECU-P2`, owner ulna) | **CONFIRMED** (and ECU carries a second blocker, hand, at terminal idx5) |
| (i) PT: ULNA site | PT idx1 (`PT-P2`, owner ulna); ulna is PT's ONLY blocker | **CONFIRMED** |
| (ii) BIClong/BICshort blocked EARLIEST on THORAX (proximal origin); D2 alone cannot unblock | earliest idx **0** (`BIClong-P1`/`BICshort-P1`, owner thorax, declared in the thorax body block, XML line 484; thorax body line 420, humerus line 534). BIC chains contain **no D2-owned sites at all** — thorax-only blockers | **CONFIRMED** |
| (iii) hand_r/hand_l + ulna/ulna_l ⇒ 12 of 16 fully comparable | measured **12** (counterfactual, §7) | **CONFIRMED** |

**FALSIFIER not triggered.** The one prediction gap worth recording: the prediction named ECU's breaker as "an ULNA site" without the terminal hand blocker; the measured chain has **both** (`ulna` idx1-3, `hand_r` idx5), so ulna-only resolution does NOT complete ECU (§7 marginals).

---

## 3. Criterion 1 — the grasp-critical set, self-enumerated

**The "32 forearm sites"** = the 32 attachment-candidate sites the packet carries: `runs/attachment_candidates.json` covers exactly `radius` (16 candidates) and `radius_l` (16), all position-resolved. Union with the ulna-side sites (10+10) gives 52 forearm-body sites touched by 28 tendons — the ulna-only tendons (ANC, BRA, TRIlat, TRImed ×2) have **zero radius sites** and are NOT in the wave-1 set.

**Tendons touching ≥1 of the 32 radius-side sites: exactly 18** — `{BRD, ECRB, ECRL, ECU, FCR, FCU, PT, BIClong, BICshort} × {right, left}`. **A7's enumeration VERIFIED**: 18 touch, BRD/BRD_l comparable (packet L₀ `0.08883103763879713` / `0.0888363641039056` m — matches wave-1's 0.088831/0.088836), remaining **16 non-comparable**.

**Full ordered paths, owner from intake, fitted status from actual_monkey_fit.json** (`fin` = finite coordinates; `NULL` = unresolved owner; index = path position 0-based; XML line numbers for the right-side spatial blocks: BIClong 1384, BICshort 1396, BRD 1411, ECRL 1416, ECRB 1422, ECU 1428, FCR 1436, FCU 1441, PT 1447):

| tendon | path (idx: site@owner status) | break |
|---|---|---|
| ECRB_tendon | 0: ECRB-P1@humerus fin · 1: ECRB-P2@radius fin · 2: ECRB-P3@radius fin · 3: ECRB-P4@hand_r **NULL** | idx3 |
| ECRL_tendon | 0: ECRL-P1@humerus fin · 1: ECRL-P2@radius fin · 2: ECRL-P3@radius fin · 3: ECRL-P4@hand_r **NULL** | idx3 |
| ECU_tendon | 0: ECU-P1@humerus fin · 1: ECU-P2@ulna **NULL** · 2: ECU-P3@ulna **NULL** · 3: ECU-P4@ulna **NULL** · 4: ECU-P5@radius fin · 5: ECU-P6@hand_r **NULL** | idx1 |
| FCR_tendon | 0: FCR-P1@humerus fin · 1: FCR-P2@radius fin · 2: FCR-P3@hand_r **NULL** | idx2 |
| FCU_tendon | 0: FCU-P1@humerus fin · 1: FCU-P2@radius fin · 2: FCU-P3@radius fin · 3: FCU-P4@hand_r **NULL** | idx3 |
| PT_tendon | 0: PT-P1@humerus fin · 1: PT-P2@ulna **NULL** · 2: PT-P3@radius fin · 3: PT-P5@radius fin | idx1 |
| BIClong_tendon | 0: BIClong-P1@thorax **NULL** · 1: BIClong-P2@thorax **NULL** · 2-7: BIClong-P3..P8@humerus fin · 8: BIClong-P9@radius fin · 9: BIClong-P11@radius fin | idx0 |
| BICshort_tendon | 0: BICshort-P1@thorax **NULL** · 1: BICshort-P2@thorax **NULL** · 2-4: BICshort-P3..P5@humerus fin · 5: BICshort-P6@radius fin · 6: BICshort-P8@radius fin | idx0 |
| ECRB_l / ECRL_l / FCR_l / FCU_l | identical shape; terminal site owner **hand_l** | idx3/3/2/3 |
| ECU_l | identical shape; ulna_l idx1-3, hand_l idx5 | idx1 |
| PT_l | identical shape; ulna_l idx1 | idx1 |
| BIClong_l / BICshort_l | identical shape; thorax idx0-1 | idx0 |

Packet `status` strings independently name the same blockers (e.g. `path_incomplete:unresolved_bodies ['hand_r']`, `['hand_r','ulna']`, `['ulna']`, `['thorax']`). Site order in the packet equals XML order for all 120 tendons (census matched packet records by site-list identity). Path site labels skip candidate numbers (PT has no P4; BIClong no P10; BICshort no P7) — candidate names, not path positions.

**Whole-census cross-check (wave-1 fact reproduced):** 42/120 comparable, 78 not; breakdown by unresolved multiset: thorax-only 40, ulna-only 10 (5+5), hand-only 8 (4+4), hand+ulna 2 (ECU_tendon `hand_r+ulna`, ECU_l_tendon `hand_l+ulna_l`), thorax+ulna 2 (TRIlong ×2), talus-only 10, talus+toes 6. The frozen `experiment_transverse_candidate.json` independently records `comparable: false` for all 16 and 42/120 overall — third agreement.

---

## 4. Criterion 2 — earliest unresolved dependency (complete column)

| tendon (16) | first unresolved idx | site at break | breaker body | ALL unresolved bodies in chain | D2-scope? |
|---|---|---|---|---|---|
| ECRB_tendon | 3 (terminal) | ECRB-P4 | **hand_r** | hand_r | yes |
| ECRL_tendon | 3 (terminal) | ECRL-P4 | **hand_r** | hand_r | yes |
| FCR_tendon | 2 (terminal) | FCR-P3 | **hand_r** | hand_r | yes |
| FCU_tendon | 3 (terminal) | FCU-P4 | **hand_r** | hand_r | yes |
| ECRB_l_tendon | 3 (terminal) | ECRB_l-P4 | **hand_l** | hand_l | yes |
| ECRL_l_tendon | 3 (terminal) | ECRL_l-P4 | **hand_l** | hand_l | yes |
| FCR_l_tendon | 2 (terminal) | FCR_l-P3 | **hand_l** | hand_l | yes |
| FCU_l_tendon | 3 (terminal) | FCU_l-P4 | **hand_l** | hand_l | yes |
| ECU_tendon | 1 (mid) | ECU-P2 | **ulna** | ulna, hand_r | yes (both D2) |
| ECU_l_tendon | 1 (mid) | ECU_l-P2 | **ulna_l** | ulna_l, hand_l | yes (both D2) |
| PT_tendon | 1 (mid) | PT-P2 | **ulna** | ulna only | yes |
| PT_l_tendon | 1 (mid) | PT_l-P2 | **ulna_l** | ulna_l only | yes |
| BIClong_tendon | **0** (proximal origin) | BIClong-P1 | **thorax** | thorax only | **NO — out of D2 scope** |
| BICshort_tendon | **0** (proximal origin) | BICshort-P1 | **thorax** | thorax only | **NO — out of D2 scope** |
| BIClong_l_tendon | **0** | BIClong_l-P1 | **thorax** | thorax only | **NO** |
| BICshort_l_tendon | **0** | BICshort_l-P1 | **thorax** | thorax only | **NO** |

Earliest-breaker census: hand_r 4, hand_l 4, ulna 2 (PT), ulna_l 2 (PT_l), thorax 4 (BIC pair both sides).

---

## 5. Criterion 3 — partial evaluation existing TODAY, per tendon

| tendon | longest finite subchain | packet L₀ | source authored rest length (XML polyline, rest pose) | finite arms in packet |
|---|---|---|---|---|
| ECRB_tendon | idx0-2 (humerus→radius→radius), 3 sites | null | 0.389941285 | 6 (pelvis zeros only) |
| ECRL_tendon | idx0-2, 3 | null | 0.432611250 | 6 |
| ECU_tendon | 1 (idx0 isolated; idx4 ECU-P5 isolated between unresolved runs) | null | 0.393906477 | 6 |
| FCR_tendon | idx0-1, 2 | null | 0.412890892 | 6 |
| FCU_tendon | idx0-2, 3 | null | 0.412192799 | 6 |
| PT_tendon | idx2-3 (PT-P3→PT-P5, radius), 2 | null | 0.211828079 | 6 |
| BIClong_tendon | idx2-9 (humerus×6 + radius×2), 8 | null | 0.484639283 | 6 |
| BICshort_tendon | idx2-6, 5 | null | 0.404161857 | 6 |
| left-side 8 | mirror-identical shapes | null | mirror values in receipt (e.g. ECRB_l 0.389990855) | 6 each |

**Arm verification (A8/E-2 confirmed per-tendon):** every one of the 16 has exactly **6 finite arms = {pelvis_tx/ty/tz/tilt/list/rotation}, each exactly 0.0** — root-coordinate zeros defined before the completeness gate (compiler.py:514-519), uninformative by construction. The remaining 33 arms are `null`. The frozen experiment's `moment_arm_max_abs_delta_m = 0.0` for all 16 is the baseline-vs-candidate **delta** of those defined zeros, not an arm value — exactly ERRATA E-2's corrected causality. Packet-wide negative finding preserved: **all 122 nonzero finite arms in the entire fit packet belong to leg tendons** (hip_flexion/adduction/rotation_r, knee_angle_r); no forearm-relevant coordinate has a finite arm anywhere.

**Becomes evaluable if ONLY D2 bodies resolve** (counterfactual arithmetic on the compiler's gates):
- **12 of 16** (ECRB, ECRL, ECU, FCR, FCU, PT ×2): chain complete → L₀ finite, lengthrange rebaseline live, and arms finite on every resolved-owner coordinate — the grasp-relevant ones being `elbow_flexion(_l)` (ulna-owned; subtree contains the radius/hand sites of all 12) and the wrist triple of the chain's side (`wrist_dev/flex/3_r` for right chains, `_l` for left). Shoulder coords (humerus, resolved) also flip finite, currently gated only by chain incompleteness.
- **BRD/BRD_l (already comparable) additionally gain their `elbow_flexion(_l)` arms** — today null solely because the owner body is unresolved (compiler.py:520), not because of their chains.
- **4 of 16 (BIClong/BICshort ×2) gain NOTHING from D2**: their chains hold no ulna/hand sites; they stay `path_incomplete: ['thorax']`.
- **Thorax additionally needed for:** BIClong_tendon, BICshort_tendon, BIClong_l_tendon, BICshort_l_tendon (named explicitly). Thorax resolution completes those chains and finite-izes `lumbar_rotation` arms; their shoulder arms flip through chain completion alone.

---

## 6. Criterion 4 — resolution mapping per earliest-breaker body

What each body's resolution must supply, per the compiler's own demands (a resolved segment = proximal+distal landmark pair + roll ref + an evidence/assumption source per scale axis, compiler.py:170-243; sites then transported by `world = P + Bp·S·Bᵀ·x_loc`, compiler.py:488-490; joint axis `K·ω_src` finite only for resolved bodies, compiler.py:438-446):

| body | SITES needing positions only (finite coords for chain completion) | COORDINATES needing ownership (moment arms) | which tendons wait on it |
|---|---|---|---|
| **hand_r** | ECRB-P4, ECRL-P4, FCU-P4, FCR-P3 (all terminal), ECU-P6 (terminal) | `wrist_dev_r`, `wrist_flex_r`, `wrist_3_r` — the grasp wrist DOFs; terminal site of each right wrist chain sits in hand_r's subtree (ECRB idx3, ECRL idx3, FCR idx2, FCU idx3, ECU idx5) | ECRB, ECRL, FCR, FCU, ECU (right) |
| **hand_l** | ECRB_l-P4, ECRL_l-P4, FCU_l-P4, FCR_l-P3, ECU_l-P6 | `wrist_dev_l`, `wrist_flex_l`, `wrist_3_l` | ECRB_l, ECRL_l, FCR_l, FCU_l, ECU_l |
| **ulna** | ECU-P2, ECU-P3, ECU-P4 (idx1-3, mid-chain), PT-P2 (idx1) | `elbow_flexion` — subtree {ulna, radius, hand} contains sites of **all 12 D2-scope chains**; also unlocks BRD's elbow arm | PT (chain completion alone), ECU (with hand_r), arm-gate for all right-side chains |
| **ulna_l** | ECU_l-P2/P3/P4, PT_l-P2 | `elbow_flexion_l` | PT_l, ECU_l, arm-gate left |
| **thorax** (OUT of D2 scope) | BIClong-P1, BIClong-P2, BICshort-P1, BICshort-P2 (idx0-1, proximal origin; per side) | `lumbar_rotation` (thorax-owned); BIC shoulder arms (`shoulder_elv/rot/elv_angle`, humerus, resolved) flip via chain completion alone | BIClong/BICshort ×2 — nothing else in the 16 |

Positions-only vs coordinates: chain completion (L₀, comparability) needs **positions only**; moment arms additionally need the **coordinate owner resolved**. For PT, ulna supplies both roles; for ECRB/ECRL/FCR/FCU the hand supplies the terminal position and the wrist-triple ownership.

---

## 7. Criterion 5 — minimal unlock set (measured marginals)

| resolved set (counterfactual) | of the 16 become comparable | which |
|---|---|---|
| hand_r + hand_l only | 8 | ECRB, ECRL, FCR, FCU ×2 |
| ulna + ulna_l only | 2 | PT ×2 |
| thorax only | 4 | BIClong, BICshort ×2 |
| **D2 = hand_r, hand_l, ulna, ulna_l** | **12** | all except the BIC pair |
| D2 + thorax | 16 | all |
| all nine | 16 | all (16 is the cap for this set) |

**Minimal set unblocking the most grasp tendons = exactly the D2 bodies {hand_r, hand_l, ulna, ulna_l} → 12/16**; the BIC pair is unreachable without thorax, which is a separate scope item (and its blast radius is large: the thorax-only census bucket holds 40 of the 78 non-comparable records — shoulder/trunk muscles — so thorax resolution is a campaign-level decision, not a grasp-mechanics one).

---

## 8. Criterion 6 — baseline integrity

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty; exit 0)
```
MANIFEST re-hash: **44/44 files match** declared sha256 (zero drift). No writes were made into `baseline_snapshot/`.

---

## 9. Structural negative findings (preserved)

- **No pronosupination coordinate exists.** The 39 coordinates contain no radioulnar DOF; `radius`/`radius_l` own **zero** joints (ownership = direct `<joint>` children, intake.py:104-131). Even post-D2, forearm-tendon arms exist only about `elbow_flexion(_l)`, the three wrist coords per side, and (as zeros or via thorax sites) trunk coords. This is a source-model property, not a D2 gap.
- **ECU is double-blocked within D2 scope** (ulna mid-chain AND hand terminal) — resolving ulna alone leaves it incomplete (marginals above).
- **Prediction (i) underspecified ECU's second blocker**; recorded in §2, table measured as found.
- **BRD/BRD_l's elbow arms are null today** despite comparable chains — gated purely on ulna's unresolved ownership; D2 repairs this as a side effect.
- **Longest-subchain "lengths" are not lengths**: e.g. ECU's finite sites are two isolated points (idx0, idx4); only PT/BIClong/BICshort have multi-site runs, and none constitutes a comparable chain measurement.

## 10. Uncertainties (explicit)

- The wave-1 phrase "32 forearm sites" was reconstructed as the 32 radius/radius_l attachment-candidate sites (`attachment_candidates.json` carries exactly those two bodies; the 18-tendon consequence matches A7 exactly). Under any alternative definition of "forearm sites" the 16-tendon list itself is unchanged (it was verified directly from the 18 families), so no verdict above depends on the reconstruction.
- "Resolution must supply" is stated as what the **compiler demands** (landmark pair + roll ref + per-axis scale source → finite positions and joint axes), not as a prescription of where that evidence should come from — that choice is the architect's/human terminal (taste is never chosen because it produces useful moment arms).
- Counterfactual "becomes comparable" columns are derived from the compiler's own gates re-evaluated set-theoretically; no refit was run (forbidden by wave-2 laws). The gate logic itself is executed code verified by the packet (every `null`/finite pattern in actual_monkey_fit.json matches the rule).

## 11. Receipts

- `scripts/b2_enumerate.py` — full enumeration (sha256 `0e39fe1d…`)
- `receipts/b2_ownership_receipt.json` — all tables, census, counterfactuals, meaningful-coordinate maps (sha256 `2f6584ec…`)
- `receipts/b2_enumerate_console.txt` — run log; `receipts/b2_receipt_hashes.txt` — hashes
- `work/` — byte-identical copies of intake.py / schema.py / correspondence.py / compiler.py used (baseline untouched)
- Primary-source XML lines cited inline (§3, §4); packet fields: `runs/actual_monkey_fit.json` tendons[].status/sites/points/moment_arms; `runs/admission_actual_monkey.json` admission.bodies.unresolved; `runs/experiment_transverse_candidate.json` tendon_deltas.
