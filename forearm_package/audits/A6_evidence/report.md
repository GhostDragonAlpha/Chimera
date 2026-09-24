# A6 — Anatomical Support Audit for the 32 Forearm Attachment Sites

**Agent:** A6 (audit) · **Date:** 2026-09-24 · **Scope:** evidence only; no decisions. Baseline untouched.
**Audit dir:** `E:/PythonChimera/forearm_package/audits/A6_evidence/` (brief.md, report.md, table.md, table.csv, scripts/, receipts/)
**Question:** for each of the 32 forearm sites — what is source-evidenced, what is fit-added assumption, and what does containment prove and not prove?

---

## 0. Verdicts per acceptance criterion

| # | criterion | verdict |
|---|---|---|
| 1 | complete 32-row table | **PASS** — `table.md` + `table.csv`, 32 rows (16 radius / 16 radius_l), every requested column populated with row-specific values |
| 2 | three-way distinction stated with quotes (DERIVATION §1/§12, report-05 §6) | **PASS** — §2 below, verbatim quotes with file+line |
| 3 | special-site notes for all outside/tight/ambiguous sites | **PASS** — §3 below covers 7+7 outside, PT-P3/PT_l-P3 tight, ECRB/ECRL P3 both sides ambiguous (18 sites), each with the required divergence statement and report-05 §6 language |
| 4 | adjacent-body context stated | **PASS** — §4 below |
| 5 | probative-claim scan result | **PASS** — §5 below: 697 raw hits triaged to 74 distinct statement contexts; **zero falsifier hits** (no language claiming attachment measurement/qualification beyond XML+fit); 3 borderline usages documented |
| 6 | baseline integrity (porcelain empty) | **PASS** — paste in §7 |

Preregistered prediction held: every row resolves to source evidence = coordinates + membership + role; fit-added = transform + scale + landmarks; containment = geometric only; zero rows carry measured-anatomy attachment evidence; scan falsifier not fired. Evidence: `receipts/a6_verify_receipt.json` (checks C1–C7), `receipts/a6_claim_scan.json`.

---

## 1. What was independently re-derived (all green)

Script `scripts/a6_verify.py` re-parses the raw XML (stdlib ElementTree + line scan) and cross-checks the packet:

| check | result |
|---|---|
| C1 — XML `pos` == packet `source_pos_local`, all 32 | PASS (float-identical; e.g. BRD-P2 XML line 616 `pos="0.03577 -0.12742 0.02315"` == packet verbatim) |
| C2 — XML tendon membership/index/path_length/role == packet `tendon_membership`, all 32 | PASS (32/32 exact) |
| C3 — role⇔index law: first_endpoint⇔index 0, last_endpoint⇔index K−1, waypoint⇔interior | PASS (32/32) |
| C4 — `fitted_pos_global == t + R @ source_pos_local`, packet's own R,t | PASS, max err **9.14e-10 m** (bound 1e-6; report-05 §4A recorded 1.15e-9) |
| C5 — loop containment tally vs admission lists vs brief baseline | PASS: per side **6 inside / 1 tight / 7 outside / 2 ambiguous**; name-set equality with `admission.envelope.{radius,radius_l}.loop_*` |
| C6 — left/right SOURCE coordinates as exact z-mirrors | **14 of 16 pairs exact mirrors; 2 are not**: BICshort-P6↔BICshort_l-P6 (max delta **2.732 mm**), FCU-P2↔FCU_l-P2 (max delta **1.030 mm**) — a SOURCE-authorship fact (the XML authors did not mirror these two pairs); independent of the fit (the fit's own bilateral-symmetry residual is separately reported at max 0.63 mm, report-05 §4A) |
| C7 — ownership + fit resolution of ALL sites on the 9 tendons per side | see §4 |

Roles measured from the XML and confirmed identical to the packet fields: per side **4 last_endpoints** (BIClong-P11, BICshort-P8, BRD-P3, PT-P5), **0 first_endpoints**, **12 waypoints**; no site carries more than one tendon membership (16 memberships per side). Totals across both sides: 8 last_endpoints / 24 waypoints — these are the numbers report-05 §3 quotes ("8 last-endpoints … 24 waypoints"), though its "per side" placement is loose (see finding F1 below). All counts are path positions, not anatomy.

---

## 2. The three-way distinction, with quotes

### (a) ANATOMICAL ATTACHMENT EVIDENCE = XML-authored tendon-site membership semantics ONLY — author modeling

The XML alone establishes: the site exists, at authored coordinates, in an owning body, and at an authored position (terminus or interior) in an authored polyline. Nothing in the baseline measures where a real tendon attaches.

- `DERIVATION.md` §1 (lines 67–69): *"**Input B — correspondence**: a human-authored (or fixture-authored) mapping from source segments to target landmarks, joint-landmark map, per-segment roll references, and per-segment scale policy. The correspondence is the ONLY place taste may enter."*
- `DERIVATION.md` §1 (lines 75–77): *"**Terminals**: everything reduces to (a) the authored correspondence landmarks (numeric, human-supplied) and (b) the source geometry as authored in the XML. The compiler adds no free constants."*
- `attachment_candidates.json` line 8 (`port_vs_waypoint_rule`): *"a site is a FIRST/LAST ENDPOINT of tendon X only when it is the first/last entry of X's ordered site_names; intermediate entries are waypoints and never endpoints for that tendon. **Endpoint roles are NOT mechanical qualifications**: every site ships mechanical_qualification=false."*
- `attachment_candidates.json`, every site (×32), `mechanical_qualification_note`: *"resolved coordinates and tendon endpoint membership do NOT qualify a membrane attachment port; qualification requires independent anatomical evidence not present in this packet."*
- A terminus site says the modeled path ends there — nothing more. Report-05 §3 (line 29): *"Roles renamed `proximal_candidate`/`distal_candidate` → `first_endpoint`/`last_endpoint` (**the packet does not establish anatomical proximal/distal orientation**)."*

### (b) GEOMETRIC CONTAINMENT = where the FITTED point sits relative to the FITTED target skin envelope

Loop/hull verdicts are signed distances of fitted points against the target mesh's sampled skin sections. They are not attachment evidence in either direction.

- `fit.json` `measurements.outer_envelope.radius.note`: *"skin (outer) envelope cross-section widths measured on interior sections of the elbow->wrist axis, away from wrist/palm and elbow. **An outer-envelope constraint only — NOT internal (bone/tissue) anatomy evidence.**"*
- `fit.json` segment `radius.assumption_notes.b` (and `.c`, both sides): *"uniform transverse assumed = axial for the forearm; the outer (skin) envelope of interior cross-sections is measured by the bounded forearm-envelope estimator (target_envelope.py) and is an **OUTER-ENVELOPE CONSTRAINT only — skin width is NOT evidence for internal (bone/tissue) cross-section scaling**"*
- `DERIVATION.md` §13 row S5: *"bounded forearm envelope estimator (interior sections; **never internal anatomy**)"*
- The packet's internal word "evidence" (in `scale_provenance: ["evidence","assumption","assumption"]` and report-04 line 37 *"the radius axial scale `[0.2217]³` is pack-joint evidence"*) means **derived from target landmark pairs** (fit-taxonomy evidence vs authored assumption) — it is NOT anatomical evidence. Stated here to prevent that word migrating.

### (c) FITTED ASSUMPTIONS (the fit-added stack, per DERIVATION §1/§4/§5/§9/§10/§12)

1. **Correspondence landmarks** — the declared taste axis (§1 quote above; sha256 `52c92fe0d207a59971d9765d10009fc4f1d94e0f0e38e2eea59a1d64be4a7df8` recorded in `fit.meta` provenance; the landmark VALUES are not in the baseline snapshot — see §8 uncertainty U1).
2. **Scale policy** — radius/radius_l `scale = [0.22170679566544982]×3`, `scale_provenance = ["evidence","assumption","assumption"]`: axial from the elbow→wrist landmark pair (`axial_pair_length`); **both transverse axes authored assumption** (`axis_sources b,c = assumption`). Report-02 §3 records the earlier transverse values were a fired falsifier (aspect 11.9 > 6.0) — the forearm transverse scale is not measurable from the pack.
3. **Roll reference** — authored `roll_ref_point` per segment (§5.1: *"This is the single axis of taste and it is fully declared, never inferred"*); `roll_residual_deg = −90.0` on both radii.
4. **Uniform-density mass carriage** — `DERIVATION.md` §9: *"**Uniform-density assumption** (explicit flag `requires_density_validation: true`) · `m' = m · |det L| = m · det S`"*; radius physiology record: `mass 0.007944462945010423 kg = mass_src 0.729 kg × det_scale 0.010897754382730348`, `status: requires_density_validation`. Admission: `physically_admitted: 0` (*"no body is physically admitted because no validated material/mass source was supplied and none is invented"*).
5. **lengthrange rebaseline** — `DERIVATION.md` §10: *"`lengthrange` is **rebaselined** by the path-length ratio `λ = L'_rest / L_rest` … `range' = λ·range`. Flag `assumption: homogeneous_path_scaling`."* (BRD muscle: `lengthrange_src "0.2193 0.3919"` → `lengthrange_fitted [0.05026, 0.08982]`.)
6. **force/timeconst NOT carried as fitted** — `DERIVATION.md` §10: *"`force`, `timeconst` are **physiology, not geometry**, and are **never scaled**. They are carried `ingested_unchanged` with status `not_geometric → requires_physiological_rerun`. **A downstream consumer must NOT treat them as fitted.**"* Status ledger §12 (lines 304–306): *"`ingested_unchanged` — force/timeconst carried with no geometric claim. · `requires_density_validation` / `requires_physiological_rerun` — flags attached to mass-family / muscle-force-family outputs."* Measured: 42/120 muscles carry `requires_physiological_rerun`; 9/9 physiology records carry `requires_density_validation`.

**The anchor for what the packet does NOT establish — `anatomy_compiler_05.md` §6 "What is NOT claimed", verbatim (lines 51–56):**

> - The candidate's pass/fail is against the DECLARED criteria; a ~41 µm shortfall is still a fail, and the two ambiguous wrist sections were not resolved by choosing a loop.
> - Even a passing candidate would have remained authored transverse geometry under declared bounds — not recovered anatomy, not measured attachment, not mechanical qualification. It did not pass.
> - `mechanical_qualification` is false for every site in the packet; endpoint roles are path positions only.
> - No material inference, no training changes, no production wiring; the packet's fitted geometry is bit-identical to session 4 except the ADDED measurement records.

---

## 3. Special-site notes (outside ×14, tight ×2, ambiguous ×4)

**Universal statement (applies to every site below):** outside-ness / tightness / ambiguity is a **geometric divergence between the source-authored coordinates as placed by the fit and the target skin envelope** — NOT evidence the anatomy is wrong, NOT evidence it is right. The divergence can come from the author's site placement, the correspondence landmarks (taste axis), the authored transverse scale, the target mesh itself, or the section geometry — this audit cannot apportion between those causes, and the packet does not claim to.

Carried verbatim from report-05 §6 into every one of these rows: *"not recovered anatomy, not measured attachment, not mechanical qualification"* and *"`mechanical_qualification` is false for every site in the packet; endpoint roles are path positions only."*

### Loop-outside, right (7): loop signed distance (hull diagnostic where resolved)

| site | loop d (m) | hull d (m) |
|---|---|---|
| BIClong-P9 | +0.001505 | unresolved (no sampled band) |
| BICshort-P6 | +0.000878 | unresolved |
| BRD-P2 | +0.005074 | +0.004626 (t=0.5) |
| BRD-P3 | +0.003937 | +0.003712 (t=0.65) |
| ECRB-P2 | +0.003752 | +0.003348 (t=0.5) |
| ECRL-P2 | +0.004597 | +0.004261 (t=0.5) |
| PT-P5 | +0.003463 | +0.003294 (t=0.35) |

### Loop-outside, left (7): BIClong_l-P9 (+0.001505), BICshort_l-P6 (+0.001505), BRD_l-P2 (+0.005074), BRD_l-P3 (+0.003937), ECRB_l-P2 (+0.003752), ECRL_l-P2 (+0.004597), PT_l-P5 (+0.003463). Mirror-symmetric to ~1e-5 m; hull diagnostic likewise.

Note the loop authority SHARPENED the session-4 hull findings (report-05 §4B): *"The loop authority SHARPENS session-4 (5 hull-outside → 7 loop-outside: BIClong-P9 and BICshort-P6 are measured outside at axials the bands never sampled) and reclassifies PT-P3 as inside-but-tight."* — here "measured outside" is a containment measurement (class (b)), not an anatomical claim.

### Tight (1/side): PT-P3 / PT_l-P3
`inside_insufficient_clearance`, d = −0.000780 m / −0.000780 m, reason: *"inside the skin loop but clearance below the required margin"* (1 mm margin). A margin statement about the fitted point only.

### Ambiguous (2/side): ECRB-P3, ECRL-P3 / ECRB_l-P3, ECRL_l-P3
Loop verdict `unresolved`, `dist_to_loop_m: null`, reason (identical all four): *"ambiguous_section: 4 closed loop(s) (2 identified as this limb's skin by pack ownership) + 0 open chain(s) at this axial position; no bridging, no repair, no proximity choice"*. The packet REFUSES to resolve the wrist-level section by choice; report-05 §6 line 53: *"the two ambiguous wrist sections were not resolved by choosing a loop."* No containment claim of any kind exists for these four sites.

---

## 4. Adjacent-body context (hand_l/hand_r, ulna/ulna_l UNRESOLVED)

Admission (`admission_actual_monkey.json` lines 19–40): `geometrically_resolved` includes `radius, radius_l`; `unresolved` includes `hand_l, hand_r, ulna, ulna_l` (reason, `fit.unresolved_segments`: *"no fitted scale (axis source missing; not silently repaired)"*).

**What it DOES imply:**
- All 32 audited sites are owned by radius/radius_l (C7: XML ownership verified), which are resolved — each site's fitted coordinate is resolved and moves with its own segment. The unresolved neighbors do NOT undermine the 32 fitted positions.
- The 9 forearm tendon chains per side are mostly NOT fully resolved, because chains run through the unresolved bodies (C7, fit tendon statuses — rest_length `null` = *"never a fabricated value"*, report-02 §4):
  - `BRD_tendon/BRD_l_tendon` — fully resolved (`status: derived`, rest_length 0.08883/0.08836 m). The only one of the 18.
  - `BIClong*/BICshort*` — `path_incomplete:unresolved_bodies ['thorax']` (path P1,P2 authored on the thorax body — a source-authorship fact; terminus P11/P8 on radius, resolved).
  - `ECRB*/ECRL*/FCR*/FCU*` — `path_incomplete:unresolved_bodies ['hand_*']` (paths END on the unresolved hand: ECRB-P4, ECRL-P4, FCR-P3, FCU-P4). Their radius sites are therefore waypoints of an incomplete chain, not ports of a resolved one — exactly the packet's reading (report-04 §4: *"paths begin on humerus; ECRL/FCR/FCU-class paths end on the unresolved hand, so their radius sites are correctly waypoints, NOT ports"*).
  - `ECU*` — `path_incomplete:unresolved_bodies ['hand_*','ulna*']` (4 unresolved sites: ECU-P2/P3/P4 on ulna, ECU-P6 on hand).
  - `PT*` — `path_incomplete:unresolved_bodies ['ulna*']` (PT-P2 on ulna unresolved; terminus PT-P5 on radius resolved).
- The two AMBIGUOUS containment verdicts (ECRB/ECRL P3) sit at wrist-level axial positions where the hand meets the forearm — the section-identification ambiguity and the unresolved hand body are consistent limitations, and neither is resolved by this packet.

**What it does NOT imply:** it does not downgrade the resolved coordinates of the 32 sites, does not invalidate the containment measurements taken at sampled forearm sections, and does not mean the sites' roles are wrong — roles are authored path positions (class (a)) and are independent of fit resolution.

---

## 5. Probative-claim scan (criterion 5)

**Method:** `scripts/a6_claim_scan.py` — case-insensitive term scan (`measured, measur, qualified, qualification, verified, verify, anatom, validated, validation, confirmed, proven, evidence, attachment, attach`) over all `runs/*.json`, all `session_reports/*.md`, `code/DERIVATION.md`, `MANIFEST.json`. Raw hits: **697** (dominated by repeated boilerplate fields: `mechanical_qualification: false` ×32 + note ×32, `scale_provenance`, `requires_*` flags, status strings). Distinct statement contexts after normalization: **74** (`receipts/a6_claim_scan.json`).

**Classification result:**
- **CLAIMS of anatomical attachment measurement/qualification: ZERO.** The preregistered falsifier did not fire.
- Every "qualification" hit is a NEGATION: `mechanical_qualification: false` ×32 with the spelled-out reason; report-05 §6 ×2.
- Every "measured" hit is (i) source-XML counting (DERIVATION §2 *"Source model (measured from the real file)"*; report-01 §1 *"Source facts (measured, XML, not assumed)"*), (ii) geometric envelope measurement (`outer_envelope` notes; report-05 §4B *"measured outside"* = containment class), or (iii) deterministic-output bookkeeping (report-01 §3, report-02 §4).
- Every "verified" hit is a mechanical check (hash identity report-01:5; serialization report-03:21; spine height alignment report-02:41; example run report-04:43) — none verifies an attachment.
- "evidence" hits are the fit-taxonomy sense (landmark-derived vs authored) or negations (*"NOT internal (bone/tissue) anatomy evidence"*).

**Borderline usages documented (honest triage, none rises to the falsifier):**
1. `session_reports/anatomy_compiler_02.md:36` — heading *"Actual-target correspondence (measured, nothing invented)"*: the body (§3) shows "measured" refers to measuring source segment lengths and pack joint positions that INFORMED the authored correspondence (e.g. *"Source `ulna→radius` = 0.023 m … the corrected radius fits at 0.222×"*). DERIVATION §1 nonetheless classes the correspondence itself as authored taste. The heading compresses this; the packet's controlling documents (DERIVATION §1, report-05 §6, `mechanical_qualification: false`) do not.
2. `MANIFEST.json:2` — campaign name *"forearm anatomy package - grasp qualification (monkey)"*: a GOAL name, not a claim that the packet achieved qualification.
3. `actual_monkey_fit.json:51230` (×1+variants) — measurement record `"claim": "per-section 2D containment in the measured (b,c) hull …"`: "measured" = the skin hull geometry (class (b)); the word "claim" here labels a geometric law, not anatomy.

---

## 6. Per-row resolution (summary of `table.md`)

All 32 rows resolve identically, as preregistered. Representative row (BRD-P2, full rows in `table.md`/`table.csv`):

- **XML pos verbatim:** line 616 `pos="0.03577 -0.12742 0.02315"` — owning body `radius` (line 608).
- **Tendon + index:** `BRD_tendon` entry 1 of 3 (0-based; spatial line 1411, ref line 1413) — role `waypoint`.
- **SOURCE EVIDENCE:** existence + authored coordinates + authored membership/order (interior waypoint of the authored polyline). AUTHOR MODELING, not measured anatomy.
- **FIT-ADDED:** fitted_pos_global (−0.122806, 0.290253, −0.007068) m = t (−0.115481, 0.319109, −0.006077) + R@x; R from correspondence landmarks (taste axis, sha 52c92fe0…) + uniform scale 0.22170680 (axial evidence / transverse assumption) + authored roll_ref (−90.0°); recon err 3.9e-10 m.
- **CONTAINMENT:** loop `outside` d=+0.005074 m (n_loops 4); hull `outside` d=+0.004626 m — geometric only.
- **PROVEN:** the row's XML facts, the arithmetic, and the geometric verdict. **ASSUMED:** everything anatomical (attachment function, transverse scale, density, physiology carriage, containment→attachment inference).

**Technical caveat (fact, not a defect):** the candidates field `R_source_local_to_target` is NOT a rotation — det(R) = 0.010897754383 = det(S) = 0.2217068³ on both sides, max|RᵀR−I| = 0.951. It is the full linear map L = Bp·diag(scale)·Bᵀ, exactly as its `composition` string declares. The identity `fitted_pos_global = t + R @ source_pos_local` holds regardless (C4) because source bodies are authored axis-aligned at rest (pos-only, DERIVATION §2). Consumers must not read this field as SO(3).

---

## 7. Baseline integrity (criterion 6)

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)
```
Measured twice during the audit (first: HEAD 0ad24b027cfbea3c4364c82d383f7b2ca5824fab; final: HEAD d43b6b00150cbee198e727a6e946a4fc893fc164 — the repo moved under other sessions; the baseline path stayed clean both times). The snapshot is git-TRACKED (45 files, `git ls-files`), NOT ignored (`git check-ignore` exit 1), so empty porcelain = tracked-clean.

SHA256 cross-check vs MANIFEST (all match): `source_xml/chimanoid.xml` (675e00d0…), `runs/actual_monkey_fit.json` (a4475550…), `runs/attachment_candidates.json` (854f7097…), `runs/admission_actual_monkey.json` (833ca65b…), `code/DERIVATION.md` (cba8b8a1…), `session_reports/anatomy_compiler_05.md` (ed6e333c…). No writes to the baseline at any point.

## 8. Uncertainties and limits (explicit)

- **U1** — The correspondence landmark VALUES are not in the snapshot; only sha256 `52c92fe0…` and downstream effects. R/t cannot be re-derived from first principles here; what IS proven is internal consistency (C4: packet R,t reproduce every exported fitted point to ≤9.2e-10 m) and properness facts (§6 caveat).
- **U2** — Containment verdicts are relative to the SAMPLED target mesh sections (t = 0.35/0.5/0.65, band ±8 mm, ±25% variants). Unsampled axials produced the `unresolved` hull diagnostics and the wrist ambiguity; the loop authority's outside verdicts at unsampled axials (BIClong-P9, BICshort-P6) rest on the section-cut method, not bands.
- **U3** — This audit does not judge whether the source XML's site placements are anatomically correct (out of scope; no external anatomy consulted per brief).
- **U4** — HEAD moved during the audit (other sessions committing); the integrity paste is per-instant. MANIFEST sha256 matches are the stronger integrity anchor.

## 9. Findings and negative results preserved

- **F1 (numeric prose/packet discrepancy, non-probative)** — report-05 §3 (line 29) states *"Measured law unchanged: **8 last-endpoints per side**, 0 first-endpoints …, 24 waypoints."* The v5 packet fields measure **4 last_endpoints per side** (8 total) and **12 waypoints per side** (24 total), 0 first_endpoints; the quoted 8/24 are the both-sides totals, so the "per side" placement is a wording error (and report-04 §4's session-4 phrasing "8 distal candidates per forearm" is inconsistent with the v5 fields' 4 per forearm). The packet FIELDS are internally consistent (C2/C3 pass 32/32); the discrepancy is prose-level. It does not create a probative overclaim in the data, but a reader trusting the prose per-side count would overcount endpoints by 2×.
- N1 — No packet field or doc line claims anatomical attachment measurement or mechanical qualification; the scan's 74 distinct contexts are all negations, geometric measurements, or fit-taxonomy wording.
- N2 — 14 of 16 left/right source coordinate pairs ARE exact z-mirrors; 2 are not (BICshort-P6 pair, delta 2.732 mm; FCU-P2 pair, delta 1.030 mm) — the source author did not fully mirror the anatomy. No packet field records this asymmetry; it is established here by C6.
- N3 — BIClong/BICshort path origins (P1,P2) are authored on the `thorax` body, which is unresolved — so the biceps chains are `path_incomplete` even though their radius termini are resolved.
- N4 — `R_source_local_to_target` is not a rotation (det = det(S) = 0.010897754383); naming caveat only, the exported identity holds.

## 10. PROPOSALS-FOR-ASTRA (decisions — NOT made by this audit)

- P1 — Rename or re-document `R_source_local_to_target` (e.g. `L_source_local_to_target`) or add a per-body note that the matrix carries the scale (N4).
- P2 — Consider recording the C6 source-side mirror asymmetry (2/16 pairs) as a packet field, since consumers may assume symmetry.
- P3 — If downstream qualification ever proceeds, it requires the independent anatomical evidence the packet itself says is missing (`mechanical_qualification_note`), plus density validation and a physiological rerun; `physically_admitted = 0` is the current state.
- P4 — Finding F1 (report-05 §3 "8 last-endpoints per side" vs packet 4/side): if any future doc revision touches that report, correct the per-side/total wording (session reports are historical records; this audit does not edit them).

## Receipts

- `receipts/a6_verify_receipt.json` — C1–C7 machine results, per-row reconstruction errors, containment tallies, chain ownership/resolution.
- `receipts/a6_claim_scan.json` — all 697 raw scan hits with terms + negation markers.
- `receipts/baseline_integrity.txt` — git porcelain paste (empty) + HEADs.
- `table.md`, `table.csv` — the 32-row evidence table.
- `scripts/a6_verify.py`, `scripts/a6_claim_scan.py`, `scripts/a6_make_table.py` — rerunnable.
