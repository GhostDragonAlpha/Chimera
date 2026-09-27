# I7 — ISOLATED U-STR B4 DIAGNOSTIC (completion-map item A02, authorized)

**Agent:** M-A02diag · **Date:** 2026-09-24 · **Branch:** `forearm-package-20260924` (HEAD at start `b04a3acd`)
**Authorization executed (handoff memo §5, verbatim):** "Authorize the isolated U-STR B4 diagnostic without requiring the hand-scoped O2 gate to pass. This authorization is for source-kinematic fidelity diagnostics only. Retain the anatomical falsifier outcome from R1; do not relabel source convention as anatomical evidence. No production radius supersession, hand fit, or training-body change is authorized by that diagnostic. Preserve old radius and all failed alternatives. Return the existing B4 criteria, exact proposed radius effects and resulting defined/undefined tendon coverage. A diagnostic PASS does not close A03 or authorize mechanically qualified grasp."
**Scope honored:** CPU-only; preregistration frozen BEFORE evaluation; no fitting search; no production mapping; no supersession execution; no training-body change; no moment-arm/path-length computation as evidence (T6). Writes ONLY inside `audits/I7_ustr_diagnostic/` plus the append-only addendum to `USTR_DIAGNOSTIC_RECEIPT.md`. The I7 receipt's "B4 outcome: NOT RUN — gate blocked" history is PRESERVED verbatim; this run replaces the OUTCOME, not the history.

---

## 0. ACCEPTANCE VERDICTS (the brief's six)

| # | criterion | verdict | evidence |
|---|---|---|---|
| 1 | Frozen candidate declaration (roll choice cited to O1) | **PASS** | `receipts/00_candidate_declaration.json`, written before any test ran (§1 below) |
| 2 | T1–T6 verdicts with receipts | **PASS — 12/12 side-test verdicts + T6 process PASS** (§2) | `receipts/01..07_*.json`, console `receipts/gate_run_console.txt` |
| 3 | Before/after radius comparison (endpoints, frame, scale + mechanism, C1's 10/10 re-placed, preservation proof) | **PASS** (§3, §4) | `receipts/08_radius_before_after.json`, `receipts/09_c1_replacement.json` |
| 4 | Coverage table (defined/undefined with reasons, BRD repair note) | **PASS** (§5) | `receipts/10_coverage_topology.json` (XML topology; B2 marginals reproduced) |
| 5 | Receipt addendum, append-only, NOT RUN history preserved | **PASS** | `USTR_DIAGNOSTIC_RECEIPT.md` — ADDENDUM 1 appended; §2 "NOT RUN" text untouched |
| 6 | Baseline integrity | **PASS** | `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` → **empty** (below, §7) |

**Preregistration outcome:** the frozen PREDICTION ("the declared candidate passes the existing B4 gate T1–T6 unchanged") is **CONFIRMED**. No preregistered falsifier fired. One diagnostic finding against my own procedure is recorded honestly in §6 (two C1 boundary sites needed explicit receipted-verdict handling in the T4 leg — handled by reproducing C1's receipted test, not by moving any threshold).

---

## 1. THE FROZEN CANDIDATE (preregistered before evaluation)

**Identity:** U-STR exactly as I6 defined it (ANATOMICAL_DECISION_TABLE.md §1, U-STR column), WITH the now-resolved roll:

| landmark | source resolution | target | provenance |
|---|---|---|---|
| P | `body_origin:ulna` | `elbow_R` (packet joint origin; anchor gap 0.0 exactly) | B4-E6 |
| P_d | `body_origin:radius` | elbow_R + **5.1158 mm** along unit(elbow→wrist), toward the wrist | I6 authored derived point; direction per C1 §1.4 (distal); 5.1158 = \|ulna→radius\| 23.0746 mm × body scale 0.22170679566544982 |
| roll Q (source) | `site:TRIlat-P5` (ulna-owned) | global [−0.1134, 0.84501, +0.15692] | XML/intake |
| roll Q (target) | — | the shipped `_band_roll` extreme vertex [−0.16961277, 0.23864266, −0.03463515] — the known-good radius edge's own declared roll target, reused EXACTLY | B4 `receipts/01_known_good_records.json` |
| parent / policy / handedness | `humerus` / `uniform` / `preserve` | coords `elbow_flexion` | XML; authored-uniform precedent (atf:239-259); left = `ulna_l` mirrored per the +90° law |

**The roll choice is a derivation, not a taste pick** (Rule 1; frozen in the declaration):
- **Law (O1, frozen):** `az_target(q) = az_source(s) + 90° (mod 360°)` — a declared pair (source site s, target witness q) carries the correct sign iff this holds.
- **Given:** (a) the frozen candidate set {ECU-P2, ANC-P2, TRIlat-P5} (I6/C3 §2.5); (b) the law; (c) the only existing target-side roll machinery — the `_band_roll` extreme vertex at measured azimuth −111.8652° (O1 receipt `o1_combine_sign.json`) — the law **demands** `az_source(s) = −111.8652° − 90° = +158.1348°`.
- **Measured residuals (mine, reproducing O1's receipted error_no_flip column exactly):** ECU-P2 **63.61°**, ANC-P2 **17.55°**, **TRIlat-P5 0.15°** (right side; left side 0.15° mirrored). Exactly ONE declared candidate lies within the ±10° tube-line precision (C3-S2). The chain closes; no free number was invented.
- **What the residual is NOT:** independent validation. The roll-ref site is CIRCULAR for its own roll DOF (C3 §2.5; O1's caveat verbatim: the striking 0.15° for TRIlat-P5 is "an observation of coherence, NOT as validation"). The SIGN (no-flip) is unanimous over all three candidates and rests on the independent evidence chain (source site split + bone surface; target olecranon test) — O1 §2/§4/§5.
- **Declared dependency:** the target witness is DEPENDENT by reuse (the radius edge consumes the same witness; C3 §2.5) — declared, not hidden. The alternative (an authored target point at the law-demanded azimuth) was rejected because it invents a new free parameter with no evidence chain.
- **Shared-point bookkeeping (C1 negative finding 4):** TRIlat-P5 ≡ TRIlong-P5 ≡ TRImed-P5 — one authored point; the roll consumes the single TRI point, leaving 8 independent validator points over 10 site records.

**Frozen falsifier set:** F-T1 provenance; F-T2 landmark floors (ROLL_EPS 1e-9 etc.); F-T3 chirality/side; F-T4 construction laws + neighbor band + C1's independent 10/10 reproduction; F-T5 uniqueness count == 1; F-T6 utility ban; **F-ANAT (RETAINED, not re-litigated): R1's refutation stands — the re-anchor this candidate forces carries NO primary-anatomical support; its basis is source-kinematic convention only.**
**Stop rule:** any fired falsifier stops the diagnostic and is reported with numbers; no tolerance weakened, no candidate repaired, no alternative searched.
**Acceptance criteria:** the EXISTING B4 T1–T6 protocol unchanged (challenge_protocol.md §2–§4, amendments A1–A5).

---

## 2. GATE RESULTS — T1–T6 on the declared candidate (protocol tolerances unchanged)

```
test                                     ulna         ulna_l   key numbers
T1 source-provenance                     PASS         PASS     parent=humerus(_l)==XML; site set == XML 10/10; dist=body_origin:radius(_l); roll site owner=ulna(_l) ∈ legal {body, parent, child}
T2 landmark-sufficiency                  PASS         PASS     |src_D−src_A|=0.023075 m; |P_d−P|=0.005116 m; roll witnesses src=0.023459 m, tgt=0.030953 m >> ROLL_EPS 1e-9; policy=uniform
T3 laterality                            PASS         PASS     right→right (elbow_R, P.x=−0.1155); left→left (elbow_L, P.x=+0.1155); det(Q constructed)=+1.000000000000000; preserve; no negative scale; mirror_normal=None
T4 transform-explainability              PASS         PASS     orthonormality 4.1e-16 (≤1e-12); det(Q)=+1 (≤1e-12); det(L)=s³; anchor gap 0.0 (≤1e-9 packet tier); edge ON the elbow→wrist line (0.00e+00 deg); s=0.221706795665 in humerus neighbor band [0.1145, 0.4581] and aspect [0.2, 5.0]; C1's independent 10/10 reproduced (worst delta 0.004 pts); axial placements roll-independent to 4.5e-17 m
T5 uniqueness (primary, A5)              PASS         PASS     resolution-consistency count = 1 exactly: supporters=['ulna'] / ['ulna_l']
T6 utility-ban (process)                 PASS (whole run)      12 scripts scanned, 0 banned-evidence occurrences; packet tendon/moment data untouched
CANDIDATE GATE: ALL PASS
```

Adaptations (invocation only; every tolerance inherited from `b4_common` unchanged):
- **T1a packet leg:** the candidate bodies sit in `unresolved_segments` (anchor-only; no fitted-segment parent field) — the leg asserts the packet record's presence and its no-fabricated-transform reason string.
- **T3 chirality leg:** the packet `chirality_det` (0.9999999999999998) records the RECORDED fit; the gate leg is the constructed det(Q) at the same 1e-12 tolerance; the packet value recorded as context.
- **T4 packet-comparison legs:** recorded N/A — no packet transform exists for an anchor-only body (asserted absent: nothing undeclared exists to contradict the map). In their place, the packet-tier anchor law (declared P == packet elbow joint origin, gap 0.0) and the decisive explainability leg: **C1's independent 10/10 region test reproduced under the declared frame** (below). No falsifier was weakened.
- **T5:** the factor-2 scale table is recorded context only (per amendment A5 the known-good itself fails that metric under bilateral symmetry — the contralateral twin `ulna_l`/`ulna` shows s identical to 12 digits and is NOT a competing owner: its own resolution names its own body). The gate is the resolution-consistency count = 1.

---

## 3. BEFORE/AFTER RADIUS (the I7 spec) — CLOSED FORM ONLY, NOTHING EXECUTED

| record | BEFORE (frozen session-5 packet) | AFTER (candidate's forced closure, computed) |
|---|---|---|
| proximal endpoint P | `elbow_R` = (−0.115480984, 0.319109077, −0.006076556) | `ulna.P_d` = (−0.117812991, 0.314555715, −0.006067057) — the derived 5.1158 mm point |
| distal endpoint P_d | `wrist_R` = (−0.144994540, 0.261482370, −0.005956329) | UNCHANGED (`wrist_R`; the hand edge's P is unaffected) |
| fitted span | 64.7449 mm | **59.6291 mm** (64.7449 − 5.1158) |
| scale s (uniform) | 0.22170679566544982 | **0.204188680010** = 59.6291/292.029 (source span radius→hand 292.0294 mm) — **−7.9015 %** |
| det(full map L) = s³ | 0.0108977544 | **0.0085132421** |
| rigid part G (`rotation` field) | det +1 | **UNCHANGED** — max \|ΔG\| = 2.22e-16 (right) / 6.66e-16 (left): same edge line, same roll witness (R1/C3's prediction `rotation` survives: CONFIRMED) |
| translation t | P − G·A (A4-verified) | recomputed `t_new = P_new − G·A` (receipt 08; full float list) |
| radius site placements | 16+16 globals (A4 reconstruction 5.6e-17 m) | 16+16 globals recompute in closed form; **max displacement 4.9510 mm (BICshort-P6)** / 4.9484 mm (BIClong_l-P9); source locals source-verbatim and UNTOUCHED |
| `max_world_reconstruction_error_m`, experiment step-A mirror table, A4/B4 receipts | valid for the recorded fit | would be superseded IN A FUTURE AUTHORIZED REVISION ONLY — preserved as history here; nothing was edited |

**The mechanism (why the re-anchor is FORCED, not chosen):** first-child shared-joint closure — `compiler.py:399-423`, `JOINT_EPS = 1e-9` at `:47`, refusal `shared_joint_separation` at `:422-423`, skipped ONLY while the parent is unresolved (`:414-417`). Measured on the frozen record: **‖radius.P(packet) − ulna.P_d(candidate)‖ = 5.1158 mm ≫ 1e-9** — with ulna declared, the shipped radius record is machine-refused; the re-anchor is the only legal continuation. (Packet `residuals.shared_joint_max_separation_m` = 0.0 today precisely because closure is skipped while ulna is unresolved.)

**Fraction bookkeeping (R1 §5.3 law, re-verified):** derived point 5.1158 mm = **7.9015 %** of the 64.7449 mm target forearm; source authored 23.0746/305.7922 = **7.5459 %**; drift ×1.04713 = k_rad/axis-ratio, exactly. 
*Correction recorded:* the I7 receipt §3's "a −7.93 % change" is a transcription slip; the exact change is **−7.9015 %** (0.204189/0.221707 − 1). Its s = 0.204189 and all other I7 numbers reproduce.

---

## 4. INDEPENDENT VALIDATION — C1's 10/10 set re-placed under the candidate frame

The U-STR construction consumes body origins only, so all 10 ulna-owned sites are independent validators (C1 §5 independence split). Re-placed in closed form under the DECLARED frame (resolved roll included):

| site | axial % of 64.7449 mm (C1 receipted) | Δ pts | transverse mm | region verdict |
|---|---|---|---|---|
| TRIlong/TRIlat/TRImed-P5 (one point) | −2.1471 (−2.15) | 0.003 | 5.201 | olecranon/process [−6, +3] — IN |
| ANC-P2 | +1.8421 (+1.84) | 0.002 | 5.651 | olecranon/process — IN |
| BRA-P3 | +2.9069 (+2.91) | 0.003 | 2.877 | tuberosity/coronoid (+3, +15] — **boundary** (receipted "in" @2.91; 0.093 pts / 0.06 mm below the +3 boundary) |
| BRA-P4 | +4.3280 (+4.33) | 0.002 | 4.557 | tuberosity/coronoid — IN |
| PT-P2 | +1.5581 (+1.56) | 0.002 | 8.277 | coronoid band — **receipted band-marginal** ("compressed to the hinge, direction right"; C1 §4c mechanism: transverse feeds axial at sin 51.63° = 0.784) |
| ECU-P2 | +14.1281 (+14.13) | 0.002 | 4.347 | shaft course, proximal-to-mid — IN |
| ECU-P3 | +17.6766 (+17.68) | 0.003 | 8.280 | shaft course — IN |
| ECU-P4 | +25.9640 (+25.96) | 0.004 | **15.378** | shaft course, interior (not wrist) — IN |

- **10/10 reproduced**: every computed axial fraction matches C1's receipted value to ≤ 0.004 points (C1's table is receipted at 2 decimals); max transverse 15.378 mm equals C1's receipted 15.38 mm and sits inside the session-3 skin-envelope medians (b 20.2 / c 22.9 mm).
- **Strict-band count 8/10 — reported, not hidden:** BRA-P3 and PT-P2 sit at/below the +3 % boundary of the tuberosity/coronoid band. C1's receipted verdicts count both as in-region ("in" and "band-marginal, direction right" respectively); the gate leg reproduces C1's RECEIPTED test. No threshold was moved: a site failing its strict band WITHOUT a receipted verdict would have fired F-T4.
- **Roll-DOF independence re-verified:** axial placements shift ≤ 4.5e-17 m under the alternative declared roll candidates (C1's closed form is roll-independent, as claimed).
- **L/R mirror:** the declared pair's left-side placements are mirror-exact (max deviation < 0.0001 mm; the source ulna-y 5.0e-5 m asymmetry cancels in the source-verbatim locals).

---

## 5. TENDON COVERAGE TABLE — under the diagnostic's ulna resolution

Topology verified from the source XML (site ownership + path membership; B2's gate law) — `receipts/10_coverage_topology.json`. "DEFINED" = chain complete (every path site's owner resolved ⇒ L₀ finite) with the grasp-relevant coordinate ownership resolved. **This table is a coverage statement, not a utility measurement** — no moment arm or length was computed (T6).

| tendon (16 grasp-critical) | blocker(s) at baseline | under THIS diagnostic (ulna+ulna_l resolved) |
|---|---|---|
| **PT_tendon, PT_l_tendon** | ulna (PT-P2 @ulna, idx1) — ulna is PT's ONLY blocker (B2 §4) | **DEFINED (the 2 newly unblocked)** — chain complete; `elbow_flexion(_l)` ownership resolved by the same act |
| **BRD_tendon, BRD_l_tendon** | chains already complete; `elbow_flexion(_l)` arms null **solely on ulna ownership** (B2 §5/§9) | **ARM REPAIR (side effect):** BRD's elbow arms become finite — the coordinate owner (ulna/ulna_l) is what the diagnostic resolves; no chain change needed |
| ECRB, ECRL, FCR, FCU ×2 (8) | terminal **hand** sites (ECRB-P4/ECRL-P4/FCR-P3/FCU-P4 @hand_r/l) | **UNDEFINED** — hand bodies unresolved; waits on A04/A05 |
| ECU_tendon, ECU_l_tendon (2) | **double-blocked**: ulna mid-chain (ECU-P2/P3/P4) AND hand terminal (ECU-P6) | **UNDEFINED** — the ulna half is now placed by this diagnostic; the terminal hand site keeps the chain open until A04/A05 |
| BIClong, BICshort ×2 (4) | **thorax** at idx0 (BIC×P1/P2 proximal origins; thorax-only blockers; zero D2-owned sites in chain) | **UNDEFINED** — thorax resolution is a separate scope item (B2: the thorax-only bucket holds 40 of 78 non-comparable records; campaign-level decision) |

**Arithmetic:** with ulna ONLY → **2 of the 16 newly DEFINED (PT ×2) + BRD's elbow-arm repair**. Context only (NOT this run, NOT authorized by it): adding hand_r/hand_l gives B2's **12/16** (+ the BRD pair complete = 14 complete chains, measured in receipt 10); the BIC ×4 remain thorax-blocked under any D2 subset. The frozen session-5 baseline records are unchanged: 42/120 comparable census intact.

---

## 6. VERDICT — honestly bounded

**B4 gate: PASS — 12/12 side-test verdicts + T6 process PASS, on the EXISTING protocol, tolerances unchanged.**

**This PASS is a SOURCE-KINEMATIC FIDELITY statement ONLY, and the receipt must carry its bounds:**

1. **R1's refutation is RETAINED, not relabeled** (R1 §6.1/§6.2): primary human evidence (London 1981; Brownhill 2009; Hollister 1994) places the radial head center ON the elbow axes — ≈ 0 % ± ~1 % of forearm length — far outside the re-anchored 7.9015 % (falsifier fired, margin ≥ 3.0 points, un-tuned). The re-anchor "preserves the source author's joint-frame convention exactly (+0.356 pt drift, mechanism identified) but carries **no primary-anatomical support**". Per the memo: *"Retain the anatomical falsifier outcome from R1; do not relabel source convention as anatomical evidence."* The model's radius ANATOMY does not start at its body origin (R1's tuberosity corroboration at 8.02 %); nothing in this diagnostic changes that.
2. **No production consequences are authorized or executed** (memo, verbatim): *"No production radius supersession, hand fit, or training-body change is authorized by that diagnostic. Preserve old radius and all failed alternatives."* The section-3 AFTER column is a CLOSED-FORM CONSEQUENCE MAP. The old radius record, the frozen session-5 baseline, U-ANA (rejected), H-BODY (rejected), every fired falsifier and negative finding remain preserved exactly as they were.
3. **A03 boundary (memo, verbatim):** *"A diagnostic PASS does not close A03 or authorize mechanically qualified grasp."* The anatomical-justification question I7 raised (DR-B: kinematic-convention fidelity vs new evidence vs declining the distal declaration) remains open exactly as I7 left it; "twelve tendons evaluable" remains what the architect ruled it — "a proposed intermediate result to test, not grasp qualification".
4. **What the diagnostic does establish:** the U-STR candidate as declared (I6 definition + the O1-resolved roll pair TRIlat-P5 ↔ the shipped band witness, residual 0.1535°) is CONSISTENT with every source-provenance, constructibility, laterality, transform-explainability (including C1's independent 10/10 landmark set), and uniqueness test the existing gate defines, on both sides. Source-kinematic fidelity is now MEASURED, not assumed.

---

## 7. INTEGRITY

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty; exit 0)                 # run at start (before any work) and re-run at end
```
- Baseline MANIFEST re-hash: **44/44 files byte-identical** (receipt 08).
- Tracked modifications under `forearm_package/`: **NONE** (the only forearm_package writes are this audit dir + the append-only receipt addendum).
- Repo-wide worktree dirt (213 paths: Chimera/, ChimeraEngine/, story/, tools/, Saved/, …) PRE-DATES this diagnostic and belongs to other sessions/lanes; one FOREIGN untracked lane (`forearm_package/audits/HAND_EVIDENCE_REQUEST/`, created 17:01 by a concurrent agent) was observed mid-session and LEFT UNTOUCHED — recorded so the worktree state is honestly attributable.
- No git writes; no network; no GPU; `PYTHONDONTWRITEBYTECODE=1` throughout.

## 8. RECEIPTS INDEX (all under `audits/I7_ustr_diagnostic/`)

| receipt | content |
|---|---|
| `brief.md` | the brief, copied verbatim as the first action |
| `receipts/00_candidate_declaration.json` | the FROZEN declaration: landmarks, roll derivation (O1 law + witness + residuals), preregistration, falsifier set, stop rule |
| `receipts/01..06_*.json` | T1–T6 per-test receipts (adapted invocations documented inline) |
| `receipts/07_gate_table.json` | consolidated candidate gate table + baseline integrity |
| `receipts/08_radius_before_after.json` | before/after radius records, closure mechanism, fraction drift law, preservation (44/44 hashes, scoped worktree audit) |
| `receipts/09_c1_replacement.json` | C1's 10/10 set re-placed (full 3D table, L/R mirror) |
| `receipts/10_coverage_topology.json` | the 16-tendon coverage scenarios from XML topology + BRD repair |
| `receipts/gate_run_console.txt` | the full gate run console log |
| `USTR_DIAGNOSTIC_RECEIPT.md` → ADDENDUM 1 | the append-only outcome record (NOT RUN history preserved) |

**STOP:** all six acceptance criteria have verdicts. The diagnostic is complete; nothing remains authorized to execute.
