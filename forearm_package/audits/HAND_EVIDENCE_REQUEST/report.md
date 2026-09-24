# M-handreq — REPORT: identity-pinned view/landmark request for hand evidence

**Agent:** M-handreq (request authoring) · **Date:** 2026-09-24
**Deliverables:** `brief.md` (verbatim copy, first action) · `HAND_EVIDENCE_REQUEST.md` (the specification, for coordinator promotion) · this report.
**Inputs read (read-only):** `audits/O2_hand_orientation/report.md` · `audits/C2_hand_evidence/report.md` · `audits/C3_independent_challenge/report.md` · `audits/B1_source_anatomy/receipts/target_hand_region.txt` + `_v3.txt` · `forearm_package/USTR_DIAGNOSTIC_RECEIPT.md` §1 O2 · `audits/R1_radioulnar_evidence/report.md` (provenance) · `audits/O1_ulna_orientation/report.md` (vendor identity protocol) · `baseline_snapshot/code/DERIVATION.md` §1 (revision pin) · `baseline_snapshot/MANIFEST.json` (hashes) · `baseline_snapshot/source_xml/chimanoid.xml` (mesh declarations L855–881, hand_r geoms L635–661, sites L663–667) · `vendor/myo_sim/meshes/` listing (215 files) · `Saved/vision_trial/` listing.

---

## 0. ACCEPTANCE-CRITERIA VERDICTS

| # | criterion | verdict |
|---|---|---|
| 1 | Three request sections complete with identity pins and acceptance/falsifier each | **PASS.** §R1 target view (pins R1.4: mesh/joint/loader hashes, unit convention, frame, camera defaults; acceptance R1.5 ×5; falsifiers R1.6 ×3) · §R2 source palm, forms A+B (pins R2.3-A1/A2: 27 named STLs, upstream revision `e021d5d9…`, scale declaration, O1-class 3.5 mm anchor rule; acceptance R2.4 ×3; falsifiers R2.5 ×3) · §R3 assembly, forms A+B (pins R3.4: region frame, ownership bands, hashes; acceptance R3.5 ×3; falsifiers R3.6 ×2) |
| 2 | Every "closes X because Y" tied to the cited failed-prong receipt | **PASS.** R1.1 → O2 §3/§3.2 + §5.1 + USTR §1 O2 + C3 §4 verdict (line-determined/sign-undetermined); R1.2 → O2 §4 (three quoted failure grounds, per-render); R2.1 → O2 §2.1/§2.2 (fan tilt ~10.0°, tilt terms ±1.0–5.6 mm, jackknife 1/27) + USTR quote; R2.2 → C2 §2.1 (anchor-only source), O1 §2.1/§8.2 (identity established for ulna.stl ONLY), C3 §4.3 (no sign in record), O2 §2.2/§5.2 (diagnostics non-adoptable); R3.1 → C2 §3 verdict + ownership anomaly B1 §2.2/§5.1 |
| 3 | Zero re-measurement of failed proxies (self-check) | **PASS — statement below (§2)** |
| 4 | Memo boundary quoted | **PASS.** §0 of the request quotes handoff memo §5 verbatim and tabulates the four fronts; §R3.6 explicitly fences dimensions/digit structure/force capacity |
| 5 | Integrity — writes only in own dir; baseline porcelain empty | **PASS.** §3 below (git status pasted, empty at start and end); all three files under `audits/HAND_EVIDENCE_REQUEST/`; no other path written |

## 1. WHAT THE REQUEST SPECIFIES (one paragraph)

Three separable artifacts: **(§R1)** a two-view (opposed) orthographic render pair of the hash-pinned `monkey_birth.bin` hand region with fully declared/reproducible camera extrinsics — both broad faces photographed so the unresolved ± sign of the face normal never enters; a human (terminal-law-compliant) reader states which face is palm, closing O2's target prong by identification where the curvature lens could not decide; the ≥ 600 px visibility bar is derived as ≈ 8× O2's recorded 60–80 px failure point (the only number chosen in this request, with its derivation stated). **(§R2)** independent source-palm evidence in either of two forms: the 27 hand bone STLs the XML already declares (`Geometry/*.stl` L855–881) with upstream provenance, scale declaration, an O1-class anchor identity test, and a fan-independent signed palm normal read from carpal anatomy — or an author-declared palm landmark list independent of the 5 test sites; closure = clean compartment split on the FROZEN site table (no re-measurement). Notably, same-named STLs already sit in `vendor/myo_sim/meshes/` — the request can be satisfied by pinning and identity-testing them; what is missing today is any identity tie for the hand (O1 tested ulna.stl only) and any palmar sign in the record. **(§R3)** same-assembly correspondence evidence — a vendor/author construction statement dispositioning each skin-ownership band (the 41–111.4 mm anomaly) or an external labeled reference of the depicted creature's actual hand — explicitly fenced from orientation, dimensions, digit structure and force capacity.

## 2. SELF-CHECK — zero re-measurement of failed proxies

**Statement:** no measurement, script, or computation against any mesh or source asset was performed in this audit. The only operations were: directory listings, reading of prior audit reports/receipts/XML lines, sha256 reads of four existing PNGs (identity pinning of a cited inventory, not a measurement), and arithmetic on already-recorded numbers (the `n_t = a × T_R` cross product and the camera defaults in R1.4, derived from O2 §3's recorded vectors; the 600 px bar, derived from O2 §4's recorded 60–80 px). The 27-geom plane sign test, the paddle curvature profiles, the lobation/split/voxel tests, and the site-table evaluation were NOT re-run — the request cites them as frozen numbers and, in §4, declares re-runs of each NON-FULFILLING if submitted.

## 3. INTEGRITY RECEIPT

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)                                   <- run at start and re-run after all writes
HEAD: b04a3acd
```

Writes confined to `forearm_package/audits/HAND_EVIDENCE_REQUEST/` (brief.md, HAND_EVIDENCE_REQUEST.md, report.md). CPU-only: no render, no GPU context, no network fetch. `PYTHONDONTWRITEBYTECODE` irrelevant (no python executed). No git writes.

## 4. RECEIPTS (values recorded this audit, read-only)

- sha256 of the four existing renders (O2 §4's inventory, pinned at request time):
  - `A_front_rest.png` `1e1d663e830247fcd878f438fa33438ef8073c70aaa2237b829aa31d2421cbc4`
  - `B_leftside_rest.png` `3e13ed75f6c04bed7316297aef02596ef6f083120ebbe8e040554868433ceb31`
  - `C_threeq_rest.png` `55f862fdef8174d64fc25beafdeedba334be7c93552f8988fe06792f6d0a3332`
  - `D_front_elbowL50.png` `bb6bfb017096e603820c18c28204904cc32bb0ea41680a935ba0e74cb922f859`
- Vendor inventory: `E:/PythonChimera/vendor/myo_sim/meshes/` = 215 STLs, including same-named hand bones (`pisiform.stl` … `5distph.stl`, `arm_r_*` variants, `_lvs/_rvs` variants) — UNVERIFIED for the hand (cited in request §R2.2.2).
- Identity pins asserted from MANIFEST crosscheck: `chimanoid.xml` `675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1`; `monkey_birth.bin` `550a5b3e…aabfa3c`; `monkey_joints.bin` `74b3ab04…50c1662`; FreeMusco revision `e021d5d9d1698dafea93c0dcf34b4bc8ce1530e7` (DERIVATION.md §1 L64–66).

## 5. PRESERVED NOTES (for the coordinator)

1. **The §R2 fallback decision is NOT made here.** O2 §5.2 recorded that accepting the raw-z/palm-13 diagnostic is an AUTHORING act; the request surfaces it as Form B's zero-cost variant and explicitly does not choose it.
2. **§R1's camera defaults are executable as-is** (numbers in R1.4, world meters, loader-pinned); the acceptance criterion is reproducibility, not those numbers — the operator may render through any channel (including the engine's frozen render path) provided extrinsics are declared per R1.3-C.
3. **Cross-links:** §R1's views double as C2 §3's smallest-missing #1 (blob inspection) but do NOT decide correspondence (§R3 exists for that); §R2's closure test consumes only the frozen site table; §R3's falsifier F-R3a can moot §R1's sign for mapping purposes — sequencing is the coordinator's.
4. No falsifier of my own was fired: this audit predicted nothing about the world; it specifies requests. Each request carries its own falsifier against the assumption it encodes (R1.6, R2.5, R3.6).

STOP: acceptance verdicted (5/5 PASS). Stopping.
