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
