# I7 — THE CONSOLIDATED RECEIPT (wave 4, returned for architectural decision)

**Per the architect's instruction (2026-09-24, fifth decision):** "Return one receipt: the three evidence results, B4 outcome, exact proposed radius change, and any remaining contradiction. Preserve the old radius record and all failed alternatives."
**Nothing here executes anything.** The frozen baseline is untouched; no fit session, production mapping, or radius supersession has been run. All failed alternatives are preserved in the audits and on the board.

---

## 1. The three evidence results

### O1 — Ulna orientation: **RESOLVED (no blocker)**
The U-STR roll SIGN is fixed: **source volar +x ↔ target volar +z (section azimuth +90°)**; the surviving 180° flip is refuted unanimously across all three declared roll candidates (ECU-P2 / ANC-P2 / TRIlat-P5; residuals 63.61° / 17.55° / 0.15°). Witness law for any future declared roll pair: `az_target(q) = az_source(s) + 90° (mod 360°)`. Target dorsal identified by olecranon protrusion (D = +3.29 ± 0.73 mm at t = +6 mm; > 2 mm across the elbow zone; L/R mirror-exact); C3's camber is thereby relabeled LATERAL (radius side), not dorsal. Evidence upgrade: a vendor ulna bone (`vendor/myo_sim/meshes/ulna.stl`) exists in-repo — C1's "smallest missing measurement" is resolved — spanning 297 of the 305.8 mm forearm, with BRA-P4 placed on the bone's volar face by surface proximity (the frozen all-10 anchor rule fired on one site class and is preserved). Cross-correction preserved: C3's elbow-band extreme-vertex statistic was paw skin (superseded by exact sections; both receipts kept). [audits/O1_ulna_orientation/ — all six scripts coordinator-re-run]

### O2 — Hand orientation: **BLOCKER (unresolved sign, independently on both prongs; nothing forced)**
- SOURCE prong FAILED its frozen test: the 27-geom plane is tilted ~10° by the asymmetric digital fan; signed offsets mix compartments (FCR −1.99 mm on the extensor side vs FCU +5.40 volar) — falsifier fired; only 1/27 jackknife refits split cleanly. Construction-free raw local-z splits cleanly 3/2 (extensors +8.2/+10.8/+1.0; flexors −1.9/−5.2) — recorded as diagnostic ONLY, not used.
- TARGET prong FAILED its frozen test: the paddle's faces bow APART (mid-window thickness ~3.4 mm above the endpoint chord; uniform-bend arithmetic predicts 0.33 mm) — a thickness lens, not resting flexion; the convex-palm falsifier fired; the mid-line nomination leaves palm concavity 0.95 mm < the frozen 1 mm; the trimmed window flips sign (−0.31 mm). Left side is the exact anti-mirror (measurement valid, interpretation blocked).
- Existing-image lane: four monkey renders found in `Saved/vision_trial/` — insufficient (animated poses, no camera-to-mesh mapping, asset identity unestablishable).
- **Smallest paths forward (recorded, not chosen):** a labeled target render (known camera + palm face visible) closes the target prong; a source-side palm identifier independent of the digital fan (e.g., a palmar surface mesh or an author-declared palm landmark) closes the source prong.
[audits/O2_hand_orientation/ — scripts coordinator-re-run; Agg-only figures; integrity clean]

### R1 — Radioulnar relationship: **FALSIFIER FIRED — the re-anchoring's anatomical claim is REFUTED; kinematic-convention basis only**
- Species: the source model is FreeMusco **Chimanoid — a fictional 120-muscle human-based character** (arms ×1.2, legs ×0.7, "chimpanzee-like proportions" as a look; 56.88 kg). No species-specific primary evidence can exist; the applicable lane is HUMAN base anatomy. (C1's passing "full-size macaque" mention is corrected.)
- What the 7.5 % measures: the source's KINEMATIC joint-frame offset — radius body-origin in the ulna frame, 14.324 mm distal + 18.088 mm lateral + 0.301 mm dorsal at 51.63° — over the elbow→hand straight-line 305.79 mm = 7.5459 %, rest-pose-specific. Not a bone-landmark distance.
- Primary human evidence (London 1981; Brownhill et al. 2009; Hollister et al. 1994): the radial head center lies ON the elbow axes — ≈ 0 % ± ~1 % of forearm length — **outside the frozen 4–12 % band** (margin ≥ 3.0 points, un-tuned). Macaque morphometry exists but measures other quantities — INAPPLICABLE, recorded not forced.
- Consequence: the re-anchor preserves the source author's joint-frame convention exactly (+0.356 pt drift, mechanism identified) but carries **no primary-anatomical support**. Independently confirming of C1's kinematic-fragment verdict.
[audits/R1_radioulnar_evidence/ — citations, arithmetic, and the full search trail incl. 5 inapplicability findings]

## 2. B4 outcome: **NOT RUN — gate blocked**

The architect's authorization was conditional: "If those gates pass: run B4 on an isolated U-STR candidate…" The gate set did not fully pass (O2 = blocker). Under the strictest reading the condition is unmet, so the isolated B4 run was **not executed** — reported rather than forced, per the ambiguity law. *For the architect's decision:* the blocked gate is HAND-scoped (orientation of the hand edge); U-STR is the ULNA candidate, whose own orientation gate (O1) passed and whose anatomical-support gate (R1) returned a refutation-with-kinematic-basis. Whether U-STR's B4 run may proceed without the hand sign is exactly the decision reserved.

## 3. The exact proposed radius change (C3's derivation, NOT applied)

- **Mechanism:** declaring the U-STR ulna edge fixes the shared elbow-region joint point such that the radius edge's proximal anchor moves to the ulna's derived distal point, 5.1158 mm from the elbow along the elbow→wrist axis. The radius fitted span becomes 64.7449 − 5.1158 = **59.6291 mm** against the source span 292.03 mm.
- **Scale:** s = 59.6291 / 292.029 = **0.204189** (vs current 0.221707; a −7.93 % change). Per-edge fraction 5.1158/64.7449 = 7.90 %, exactly the source-authored 7.5459 % × the k_rad/forearm ratio (R1 verified).
- **Records that would be superseded in an authorized revision** (frozen baseline untouched): radius/radius_l `local_to_world` (R, t), `max_world_reconstruction_error_m`, the experiment step-A mirror table, the A4/B4 receipt set — all preserved as history.
- **Why necessary:** F1 first-child closure (JOINT_EPS 1e-9) leaves no alternative once the ulna edge is declared — otherwise the same physical joint exists at two points.
- **Justification status (the contradiction, stated plainly):** R1 refuted the anatomical reading; the change's ONLY current basis is preservation of the source's kinematic convention. The architect's bar ("anatomical justification") is NOT met on current evidence.

## 4. Remaining contradictions (consolidated)

1. **R1 vs the re-anchor:** primary anatomy places the radial head at ~0 %; the source authored 7.55 %. The re-anchor faithfully preserves the latter and thereby diverges from the former. Kinematic fidelity and anatomical fidelity are in direct tension; which one the package serves is an architectural decision.
2. **O2's blocker:** the hand sign is unresolvable with current assets on both prongs — hand edge orientation (and everything downstream of it) cannot proceed on existing evidence.
3. **C1↔C3 cross-corrections already folded in:** camber = lateral (not dorsal); elbow-band vertex = paw skin; PT cell corrected; the map's circular falsifier voided for U-ANA. All preserved with receipts.

## 5. Decision requests (this receipt)

- **DR-A:** Proceed with, or decline, the isolated B4 run on U-STR given the hand-scoped gate block (U-STR's own gates: O1 pass, R1 kinematic-only).
- **DR-B:** Rule on the re-anchor's basis: accept kinematic-convention fidelity as sufficient, or require new evidence (e.g., a source-convention study or an anatomically-derived anchor), or decline U-STR's distal declaration entirely.
- **DR-C (standing from I6):** the hand policy set (H-LEN/H-ASP/H-BODY) remains deferred pending same-assembly; O2's blocker adds the orientation prerequisite and its two smallest paths.

**Everything is preserved:** the old radius record (frozen baseline + A4 receipts), all failed alternatives (U-ANA rejected; H-BODY circular; the fourth mass; every preserved negative finding), and the full audit trail under forearm_package/audits/ with coordinator-re-verified receipts.

---

# ADDENDUM 1 — B4 outcome: RUN (isolated U-STR diagnostic; authorized) — APPEND-ONLY, 2026-09-24

**Nothing above is edited; §2's "NOT RUN — gate blocked" stands as history.** This addendum records the outcome of the architect's authorization (handoff memo §5, verbatim): "Authorize the isolated U-STR B4 diagnostic without requiring the hand-scoped O2 gate to pass. This authorization is for source-kinematic fidelity diagnostics only. Retain the anatomical falsifier outcome from R1; do not relabel source convention as anatomical evidence. No production radius supersession, hand fit, or training-body change is authorized by that diagnostic. Preserve old radius and all failed alternatives. Return the existing B4 criteria, exact proposed radius effects and resulting defined/undefined tendon coverage. A diagnostic PASS does not close A03 or authorize mechanically qualified grasp." Executed by M-A02diag; full report + receipts: `audits/I7_ustr_diagnostic/` (report.md; receipts/00–10; brief.md frozen before evaluation).

## 1. Frozen candidate (preregistered before any test)

U-STR exactly as I6 defined it (P `body_origin:ulna`↔`elbow_R`, anchor gap 0.0; P_d `body_origin:radius`↔derived 5.1158 mm point on the elbow→wrist axis; s_a = 0.2217 by construction; uniform; preserve) **WITH the resolved roll**: declared pair = **source `site:TRIlat-P5` ↔ the shipped `_band_roll` extreme vertex** (the known-good radius edge's own witness, reused EXACTLY; DEPENDENT by reuse, declared). **Choice derived, not picked:** O1's witness law `az_target(q) = az_source(s) + 90°` + the witness azimuth −111.8652° demand az_source = +158.1348°; residuals over the frozen candidate set: ECU-P2 63.61° / ANC-P2 17.55° / **TRIlat-P5 0.15°** (left side 0.15° mirrored) — exactly one candidate within the ±10° tube precision. The residual SELECTS the pair and is NOT validation (the roll-ref site is circular for its own DOF — C3 §2.5); the SIGN is O1's unanimous independent verdict. Falsifier set frozen incl. **F-ANAT: R1's refutation RETAINED**; stop rule: any fire stops the run, no tolerance weakened.

## 2. B4 outcome (existing T1–T6 protocol unchanged): **PASS — source-kinematic fidelity only**

12/12 side-test verdicts PASS + T6 process PASS (0 banned-evidence occurrences). Key numbers: T1 parent=humerus(_l)==XML, site sets 10/10==XML, dist=`body_origin:radius(_l)`, roll site owner=ulna(_l) ∈ legal set; T2 spans 0.023075 m / 0.005116 m, roll witnesses 0.023459 m (src) / 0.030953 m (tgt) ≫ 1e-9; T3 right↔elbow_R / left↔elbow_L (monkey right = −x), det(Q constructed) = +1.000000000000000; T4 orthonormality 4.1e-16, det(L) = s³, anchor gap 0.0, edge on the elbow→wrist line exactly, s = 0.221706795665 inside the humerus neighbor band [0.1145, 0.4581] and aspect [0.2, 5.0], **C1's independent 10/10 landmark set reproduced under the declared frame (worst delta 0.004 pts; max transverse 15.378 mm == C1's receipted 15.38)**, axial placements roll-independent to 4.5e-17 m; T5 resolution-consistency count = 1 exactly (supporters = ['ulna'] / ['ulna_l']). T4/T5 adaptations are recorded in the report (no packet record exists for an anchor-only body; the A5 primary metric is the gate; the scale table is context).

## 3. Exact proposed radius effects (CLOSED FORM ONLY — nothing executed)

| record | before (frozen) | after (forced by first-child closure, `compiler.py:399-423`, JOINT_EPS 1e-9) |
|---|---|---|
| radius.P | `elbow_R` = (−0.115480984, 0.319109077, −0.006076556) | ulna.P_d = (−0.117812991, 0.314555715, −0.006067057) |
| radius.P_d | `wrist_R` | unchanged |
| span | 64.7449 mm | 59.6291 mm |
| s (uniform) | 0.22170679566544982 | **0.204188680010** (−7.9015 %; corrects §3's "−7.93 %" transcription slip) |
| det(L) = s³ | 0.0108977544 | 0.0085132421 |
| rigid G (`rotation`) | det +1 | unchanged (max \|ΔG\| 2.22e-16) — `rotation` survives, as §3 predicted |
| 16+16 radius site globals | A4-verified | recompute; max displacement 4.9510 mm (BICshort-P6) / 4.9484 mm (BIClong_l-P9); locals untouched |

Mechanism measured on the frozen record: ‖radius.P − ulna.P_d‖ = 5.1158 mm ≫ 1e-9 ⇒ with ulna declared the shipped radius record is machine-refused (`shared_joint_separation`) and the re-anchor is forced, not chosen. Fraction bookkeeping re-verified (R1 §5.3): 5.1158/64.7449 = 7.9015 % = 7.5459 % × 1.04713. **In an authorized revision only**, the superseded set would be §3's record list (radius local_to_world, reconstruction-error record, step-A mirror table, A4/B4 receipt set → historical); here EVERYTHING stayed frozen (MANIFEST 44/44; baseline porcelain empty).

## 4. Resulting tendon coverage (under ulna+ulna_l resolution ONLY)

**DEFINED (2 of 16 newly): PT_tendon, PT_l_tendon** — ulna was their only blocker; chain completes and `elbow_flexion(_l)` ownership resolves in the same act. **ARM REPAIR: BRD/BRD_l** — chains already complete; their null elbow arms are repaired by ulna ownership alone (B2 §5). **UNDEFINED:** ECRB/ECRL/FCR/FCU ×2 (8) — terminal hand sites, wait on A04/A05; ECU ×2 (2) — double-blocked, ulna half placed, terminal ECU-P6@hand still open; BIClong/BICshort ×2 (4) — thorax-blocked at idx0 (no D2-owned sites; thorax = campaign-level scope). Context only (NOT this run): +hand gives B2's 12/16 (+BRD pair = 14 complete). Baseline census 42/120 unchanged.

## 5. The verdict's bounds (binding language)

- The B4 PASS is a **SOURCE-KINEMATIC FIDELITY statement ONLY**. R1's retained refutation stands: primary anatomy places the radial head at ≈ 0 % ± 1 % of forearm length; the re-anchored 7.9015 % preserves the source author's kinematic convention (drift +0.356 pts, mechanism identified) and carries **no primary-anatomical support**; the source convention is NOT relabeled as anatomical evidence.
- **No production radius supersession, hand fit, or training-body change is authorized or executed by this diagnostic.** The old radius record and all failed alternatives (U-ANA; H-BODY; every fired falsifier) remain preserved in the frozen baseline and audits.
- **A diagnostic PASS does not close A03 or authorize mechanically qualified grasp** (memo, verbatim). DR-B (the re-anchor's basis) and DR-C (hand policy) remain exactly as this receipt's §5 left them.
- What the diagnostic does establish: the declared U-STR candidate is consistent with every test the existing gate defines — the source-kinematic fidelity of the correspondence is now MEASURED, not assumed.

## 6. Integrity

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty; exit 0)          # start and end of the diagnostic
```
MANIFEST re-hash 44/44; no tracked modification under `forearm_package/` outside this addendum; writes confined to `audits/I7_ustr_diagnostic/` + this addendum. One foreign untracked lane (`audits/HAND_EVIDENCE_REQUEST/`, created 17:01 by a concurrent agent) was observed and left untouched. CPU-only; no network; no git writes.

