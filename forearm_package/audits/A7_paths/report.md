# A7 — Tendon-path and length audit (report)

**Auditor:** A7 (audit agent; evidence only — decisions belong to the architect)
**Date:** 2026-09-24
**Baseline (read-only):** `E:/PythonChimera/forearm_package/baseline_snapshot/`
**Brief:** `E:/PythonChimera/forearm_package/audits/A7_paths/brief.md` (verbatim copy of the task)
**Boundary compliance:** baseline never written; Candidate C never re-run, re-fit, or extended — its recorded (db, dc) were used only to recompute the same quantities the record itself computed (`experiment_transverse_fit.py` lines 373-408); no recommendation is made anywhere in this report.

---

## VERDICT SUMMARY

| # | Criterion | Verdict |
|---|---|---|
| 1 | Per-tendon L0 table (stored vs recomputed, max rel dev) | **PASS** — 42/42 recomputable chains bit-identical; max relative deviation exactly **0.0** |
| 2 | Comparability census (42 verified + 78 enumerated by reason) | **PASS** — 42/120 reproduced independently; all 78 enumerated in 13 categories; 120/120 flags match the record |
| 3 | Candidate Δ verification (max + top-10 table) | **PASS** — recorded max 0.90164 mm at BRD confirmed; all 42 recorded deltas recomputed bit-identically (max abs diff 0.0) |
| 4 | Baseline consequence table with separation-of-claims statements | **PASS** (facts tabulated; no recommendations) |
| 5 | Baseline integrity (git status empty) | **PASS** — `git status --porcelain` output empty; 14/14 pinned sha256 re-measured match MANIFEST |

**Preregistration outcome (frozen):** PREDICTION held on all three heads — L0 recomputation matched **exactly** (0.0 relative, tighter than the ≤1e-9 bound); 42/120 confirmed; 0.90 mm BRD confirmed (0.90164 mm). FALSIFIER **not tripped** — no deviation beyond rounding was found; no packet internal inconsistency.

---

## 1. Per-tendon L0 verification — PASS

**Law under test.** `baseline_snapshot/code/DERIVATION.md` §7: "A tendon path is an ordered list of site refs → an ordered list of fitted global points `s₀..s_K`. Rest length `L₀ = Σ_{j<K} |s_{j+1} − s_j|`." Reference implementation `baseline_snapshot/code/compiler.py` lines 80-81 (`_pl`); rest length assigned at compile time at lines 505-513 (`rest_length=_pl(pts) if complete else float("nan")`, where `complete` = no NaN point). Export is exact: `schema.py` lines 422-451 export raw doubles (no rounding; non-finite → null), `write_json` line 462 uses strict JSON. Recomputation from the exported points is therefore expected to be exact, and it is.

**Method.** `scripts/step1_L0_verify.py` (pure JSON + NumPy; `_pl` reimplemented with identical left-to-right summation order). Receipts: `receipts/step1_L0_receipt.json`, `receipts/step1_L0_table.csv`.

**Results (all 120 tendons):**
- status `derived`: 42; `rest_length` null (path incomplete): 78.
- Recomputed L0 from packet points: **42/42 bit-identical to stored; max relative deviation = 0.0** (not merely ≤1e-9 — exact, per determinism law S4).
- Consistency: every tendon's `points` equal the corresponding sites' `fitted_pos_global` records (checked pairwise exact equality) — true for all 120.

**Tendons touching the 32 forearm sites: 18** (fit-packet scan and the candidates packet's `tendon_membership` agree exactly: 18 = 18, no difference in either direction — `membership_cross` in the receipt). Per side: BIClong, BICshort, BRD, ECRB, ECRL, ECU, FCR, FCU, PT.

Stored vs recomputed L0 for the 18 (full table in `receipts/step1_L0_table.csv`):

| tendon | path bodies (ordered) | stored L0 [m] | recomputed [m] | rel dev |
|---|---|---|---|---|
| BRD_tendon | humerus, radius, radius | 0.08883103763879713 | 0.08883103763879713 | 0.0 |
| BRD_l_tendon | humerus_l, radius_l, radius_l | 0.0888363641039056 | 0.0888363641039056 | 0.0 |
| BIClong_tendon / _l | thorax×2, humerus(_l)×6, radius(_l)×2 | null (thorax unresolved) | — | — |
| BICshort_tendon / _l | thorax×2, humerus(_l)×3, radius(_l)×2 | null (thorax unresolved) | — | — |
| ECRB_tendon / _l | humerus(_l), radius(_l)×2, hand(_r/_l) | null (hand unresolved) | — | — |
| ECRL_tendon / _l | humerus(_l), radius(_l)×2, hand(_r/_l) | null (hand unresolved) | — | — |
| ECU_tendon / _l | humerus(_l), ulna(_l)×3, radius(_l), hand(_r/_l) | null (hand + ulna unresolved) | — | — |
| FCR_tendon / _l | humerus(_l), radius(_l), hand(_r/_l) | null (hand unresolved) | — | — |
| FCU_tendon / _l | humerus(_l), radius(_l)×2, hand(_r/_l) | null (hand unresolved) | — | — |
| PT_tendon / _l | humerus(_l), ulna(_l), radius(_l)×2 | null (ulna unresolved) | — | — |

16 of the 18 carry **no stored L0 at all**; only the BRD pair has a claimed rest length. This is a packet-internal fact, not a defect introduced by this audit.

---

## 2. Comparability census — PASS (42/120 verified; 78 enumerated)

**The rule**, read from `baseline_snapshot/code/experiment_transverse_fit.py` lines 382-408: iterating a tendon's ordered sites, a site contributes only if `site_fit[sn]` exists and is all-finite; **`ok_chain` (the record's `comparable`) is True iff EVERY site of the path is finite**; unresolved sites are skipped and the summed length bridges from the last resolved point, but a non-finite site forces `comparable: false` and `path_length_delta_m: null`.

**Independent verification** (`scripts/step2_census.py`, receipt `receipts/step2_census_receipt.json`):
- Comparable recomputed from the packet alone: **42**; non-comparable: **78**. The record's claim "42/120 tendons have fully-resolved comparable chains" is **CONFIRMED**.
- Flag-by-flag cross-check vs `experiment_transverse_candidate.json.tendon_deltas`: **0 mismatches on all 120**; the null-Δ pattern also matches exactly (every comparable has a recorded Δ, every non-comparable has null).
- The packet's per-site `unresolved` flag agrees with the admission ledger's unresolved-body list for all 468 sites (0 disagreements). Unresolved bodies (9): `hand_l, hand_r, talus_l, talus_r, thorax, toes_l, toes_r, ulna, ulna_l`.
- The 42 and 78 sets are disjoint (overlap empty).

**The 78, enumerated by reason** (exact set of unresolved bodies in the chain; full tendon list in the receipt):

| unresolved bodies in chain | tendons |
|---|---|
| thorax only | 40 |
| ulna only | 5 (ANC, BRA, PT, TRIlat, TRImed — each +_l) |
| hand only | 4/side (ECRB, ECRL, FCR, FCU) → 8 |
| hand + ulna | 1/side (ECU) → 2 |
| thorax + ulna | 1/side (TRIlong) → 2 |
| talus only | 5/side (med_gas, per_long, soleus, tib_ant, tib_post) → 10 |
| talus + toes | 3/side (ext_dig, flex_dig, flex_hal) → 6 |

Exact counts (`category_counts_by_unresolved_body_set`): `thorax` 40 · `ulna` 5 · `ulna_l` 5 · `hand_r` 4 · `hand_l` 4 · `hand_r+ulna` 1 · `hand_l+ulna_l` 1 · `thorax+ulna` 1 · `thorax+ulna_l` 1 · `talus_r` 5 · `talus_l` 5 · `talus_r+toes_r` 3 · `talus_l+toes_l` 3 — **sum 78**.
Per-body incidence: thorax 42 · ulna 7 · ulna_l 7 · hand_r 5 · hand_l 5 · talus_r 8 · talus_l 8 · toes_r 3 · toes_l 3 (a tendon can touch more than one unresolved body, so these sum to more than 78).

---

## 3. RECORDED EFFECTS OF A FAILED, UNAPPLIED CANDIDATE

> **Label stands for this whole section.** Candidate C was fit once, evaluated, and **rejected** (`passed = false` on both sides; `runs/experiment_transverse_candidate.json`). Everything below VERIFIES the record; nothing here is an applied or proposed change. The candidate stays dead (frozen boundary).

**Recorded optimum** (from the record, not re-run): right `db=+6.24 mm, dc=+2.02 mm`; left `db=+6.24 mm, dc=−2.02 mm` (mirror-symmetric, independently fitted); `passed=false` both sides (`fitting_sections_ok=false` — a ~41 µm shortfall per report 05 §4-C; `loop_authority_ok=false` because the two ambiguous wrist sections remain ambiguous; `bounds_ok=true`; `additional_sections_ok=true`); max site displacement 6.558811 mm.

**V1 record census:** 120 delta records; 42 comparable; zero census violations (no non-comparable with non-null Δ, no comparable with null Δ).

**V2 recorded max |Δ path length|:** **BRD_tendon, −0.00090164 m = 0.90164 mm** — confirms the recorded "max |Δ path length| = 0.90 mm (BRD)" (report 05 §4-C) and the campaign figure.

**V3 top-10 recorded Δ table** (largest first; the candidate's path-length effect on the comparable set is confined to the two BRD chains — every other comparable tendon records exactly 0.0):

| # | tendon | recorded Δ [m] | \|Δ\| [mm] |
|---|---|---|---|
| 1 | BRD_tendon | −0.00090164 | 0.90164 |
| 2 | BRD_l_tendon | −0.000901337 | 0.901337 |
| 3-10 | glut_med1/2/3_r, bifemlh_r, bifemsh_r, sar_r, add_mag2_r, tfl_r | 0.0 | 0.0 |

**V4 independence:** the 40 comparable tendons with no site among the 32 all record Δ = 0.0 exactly (0 violations). Consistent with the candidate moving only the 32 forearm sites.

**V5 recomputation of the same quantities** (`scripts/step3_candidate_effects.py`, receipt `receipts/step3_candidate_effects_receipt.json`): using the frozen baseline packet points, the record's own (rounded) db/dc, and the side envelope frames rebuilt deterministically exactly as `experiment_transverse_fit._side_frames` does (joint positions elbow/wrist from the target pack — read-only loads of the snapshot's byte-identical `inputs/*.bin` copies — plus `_band_roll` [actual_target_fit.py lines 89-97] and `onb_from_points` [compiler.py lines 58-68]): **all 42 recomputed Δ match the recorded values exactly (max abs difference 0.0 m)**; recomputed max = BRD_tendon −0.90164 mm, same winner.

**Recorded moment-arm effect:** max |Δ moment arm| over comparable chains = **0.0** in the record (their rounding floor 1e-12; report 05 §4-C: "≈ 0 (1e-12 rounding floor) — a straight tendon has zero moment arm about any joint, which the shift preserves"). Verified as recorded; consistent with the rigid-shift geometry.

**What the record does NOT establish (negative finding, preserved):** the 78 non-comparable chains carry **no recorded Δ at all** (null by the comparability rule). The candidate's path-length effect on those chains is not measured anywhere in the record, because their paths run through unresolved bodies whose candidate coordinates are undefined. "No recorded effect" for those 78 is a limit of the record, not a measured zero.

---

## 4. Baseline grasp consequences (facts only)

Data: `scripts/step4_grasp_consequences.py`, receipt `receipts/step4_grasp_consequences_receipt.json`.

**4a. All 32 sites are resolved in both packets** (16/16 per side; `fitted_pos_global` finite, `unresolved=false`, `fitted.resolved=true`). Therefore **every polyline through the 32 sites is well-defined and its length is computable** — including for the 16 touching tendons whose full chains are incomplete.

**4b. Containment classes of the 32 sites** (loop authority = FINAL per report 05 §4-B; hull sampling retained only as a diagnostic):

| loop verdict | count (R+L) | sites |
|---|---|---|
| inside | 12 | BIClong-P11, BICshort-P8, ECU-P5, FCR-P2, FCU-P2, FCU-P3 (+_l twins) |
| outside | 14 | BRD-P2/P3, ECRB-P2, ECRL-P2, PT-P5, BIClong-P9, BICshort-P6 (+_l twins) |
| tight (`inside_insufficient_clearance`) | 2 | PT-P3, PT_l-P3 |
| ambiguous (`unresolved` — multiple ownership-identified loops at wrist-level sections) | 4 | ECRB-P3, ECRL-P3 (+_l twins) |

Hull-diagnostic classes (separate, weaker authority): 6 inside / 10 outside / 16 unresolved. The two authorities disagree in coverage, not in any re-verified measurement; the loop authority is the FINAL one per report 05 §4-B and its verdicts are byte-identical in the candidates packet and the experiment record (0 mismatches; my recount of step_B gives 6 inside / 1 tight / 7 outside / 2 ambiguous per side, matching the record's own counts and report 05 §4-B). Right/left verdict columns are mirror-identical.

**4c. What containment class does and does NOT mean (separation of claims, anchored on report 05 §6 "What is NOT claimed"):**
- It DOES claim a skin-position verdict at the site's exact axial section under the loop authority (`inside` = within the identified skin loop with ≥1 mm margin; `outside` = beyond it; `tight` = inside but <1 mm; `ambiguous` = the section identification itself failed, not the placement).
- It does NOT qualify a mechanical port: `mechanical_qualification: false` on every one of the 32 sites (candidates packet v5; report 05 §3, §6). Endpoint roles are path positions only.
- It says NOTHING about path validity: the polyline and its length are well-defined regardless of containment class (4a). BRD-P2/P3 are loop-outside AND their tendon has the only fully-derived L0 in the forearm set — the two facts live in different ledgers and neither modifies the other.
- Even the rejected candidate would have remained "authored transverse geometry … never recovered anatomy, not measured attachment, not mechanical qualification" (report 05 §6). No claim in this report upgrades any site.

**4d. Wrist-relevant forearm set — baseline table** (L0 from §1; containment from 4b; statuses verbatim packet fields):

| tendon (per side) | L0 [m] | forearm sites among 32 (loop class) | crosses to unresolved body |
|---|---|---|---|
| BRD / BRD_l | 0.08883103763879713 / 0.0888363641039056 | P2, P3 (outside, outside) | — (fully derived; only one) |
| ECRB / ECRB_l | null | P2 (outside), P3 (ambiguous) | hand_r / hand_l |
| ECRL / ECRL_l | null | P2 (outside), P3 (ambiguous) | hand_r / hand_l |
| ECU / ECU_l | null | P5 (inside) | hand_r/_l AND ulna/ulna_l |
| PT / PT_l | null | P3 (tight), P5 (outside) | ulna / ulna_l |
| FCR / FCR_l | null | P2 (inside) | hand_r / hand_l |
| FCU / FCU_l | null | P2, P3 (inside, inside) | hand_r / hand_l |
| BIClong / BIClong_l | null | P9 (outside), P11 (inside) | thorax (proximal end) |
| BICshort / BICshort_l | null | P6 (outside), P8 (inside) | thorax (proximal end) |

**4e. What the unresolved crossings limit (packet fields, not inference):**
- 10 of the 18 touching tendons (ECRB, ECRL, ECU, FCR, FCU × 2 sides) end on `hand_r`/`hand_l` — bodies with no fitted scale (admission ledger). For all 10: `rest_length` null, muscle `status = path_incomplete:unresolved_bodies [...]`, muscle `rest_length` null.
- Moment arms: for every incomplete chain, all NON-root arms are null with `matched=false` (compiler.py lines 514-524); the only finite entries are the root pelvis coordinates' identically-zero arms (verified for ECRB: 6 finite = pelvis zeros; 33 null). BRD (derived): 22/39 arms finite, all `matched=true`. Net: **the baseline claims no functional moment arm for any wrist flexor/extensor** — wrist-to-hand transmission is outside what the packet establishes.
- PT's chain hits unresolved `ulna` despite being otherwise forearm-local: the ulna's absence (not the hand's) is what blocks PT. Same mechanism blocks ANC, BRA, TRIlat, TRImed (§2 categories).
- BRD is the ONLY wrist-set tendon with a claimed L0 and matched moment arms, and its status carries `physiology:requires_physiological_rerun` — no muscle physiology claim rides on it.
- Consequence for the grasp question, stated as fact: the packet resolves WHERE the 32 forearm waypoints sit and HOW LONG two BRD chains are, and measures skin containment at 32 sections; it does not yet establish path lengths, moment arms, or muscle excursions for the tendons that cross the wrist into the digits, because the hand and ulna bodies are unresolved.

---

## 5. Baseline integrity — PASS

- `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` → **empty output** (0 lines; run twice, start and end of audit; receipt `step5_integrity_receipt.json`).
- sha256 re-measured today for all 15 consumed files: **14/14 pinned entries match MANIFEST.json exactly; 0 mismatches** (MANIFEST.json does not pin itself).
- Note (expected, not a discrepancy): MANIFEST pins `git_head_at_snapshot: c70b7a6c`; current repo HEAD is `d43b6b00`. The snapshot's integrity anchor is its own byte hashes, which all match.

---

## Uncertainties, limits, negative findings (preserved)

1. **Non-findings are findings here:** all three prediction heads held exactly; there is no discrepancy to report. The falsifier ("any deviation beyond rounding — packet internal inconsistency") did not fire.
2. The record's Δ=0 rows for the 40 untouched comparable tendons are exact recorded zeros, verified consistent (V4) and reproduced exactly (V5). The 78 non-comparable chains have NO recorded candidate Δ — unknowable from stored artifacts alone; stated as a limit in §3.
3. V5 exactness rests on reproducing the record's own arithmetic (it too used the rounded `db_m`/`dc_m` it exported — `experiment_transverse_fit.py` lines 373-378). A recomputation against the unrounded optimizer output is impossible without re-running the (dead) optimization, which the frozen boundary forbids.
4. The brief's step-4 tendon list ("ECRB, ECRL, ECU, BRD, PT, and any others touching the 32 sites") resolves to 9 families × 2 sides = 18 tendons; BIClong, BICshort, FCR, FCU are the "others" (membership cross-checked two independent ways, §1).
5. This audit ran under Python 3.14.3 + NumPy 2.2.6; the packet was produced under a session-5 environment not recorded in MANIFEST. Bit-exact agreement of every recomputed float makes version drift empirically irrelevant for the quantities checked.

## Receipts (exact commands, run from `E:/PythonChimera`)

```
PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/A7_paths/scripts/step1_L0_verify.py
  -> max_rel_dev 0.0 over 42 recomputable; 18 touching; membership cross clean
PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/A7_paths/scripts/step2_census.py
  -> count_verified true; 0 flag mismatches on 120; 78 enumerated
PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/A7_paths/scripts/step3_candidate_effects.py
  -> V2 max 0.90164 mm BRD_tendon; V5 max_abs_diff_vs_record_m 0.0 over 42
PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/A7_paths/scripts/step4_grasp_consequences.py
  -> step_B recount 6/1/7/2 per side; 0 verdict mismatches; 32/32 resolved
PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/A7_paths/scripts/step5_integrity.py
  -> I1_empty true; I2 0 sha mismatches / 14 pinned
git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot   # empty
```

Receipt files: `receipts/step1_L0_receipt.json`, `receipts/step1_L0_table.csv`, `receipts/step2_census_receipt.json`, `receipts/step3_candidate_effects_receipt.json`, `receipts/step4_grasp_consequences_receipt.json`, `receipts/step5_integrity_receipt.json`.
Scripts: `scripts/step1_L0_verify.py` … `scripts/step5_integrity.py`. Copied module: `work/mesh_target.py` (byte-identical copy of `baseline_snapshot/code/mesh_target.py`, imported only with snapshot `inputs/` paths, read-only).
