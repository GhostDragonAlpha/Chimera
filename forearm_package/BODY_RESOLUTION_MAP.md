# I5 — PROPOSED BODY-RESOLUTION MAP (ulna, ulna_l, hand_r, hand_l)

**Status: PROPOSAL — NOT EVALUATED, NOT APPROVED, NOT WIRED INTO ANYTHING.**
**Laws binding this document (architect, 2026-09-24, verbatim):** "Preregister before any candidate mapping is evaluated: the claimed correspondence, supporting landmarks, numerical tolerances, uniqueness criteria, and falsifier. A mapping fails if it contradicts source evidence, requires an unexplained transform, or leaves multiple equally supported owners. Never choose ownership because it produces useful moment arms."
**T6 attestation:** no tendon length, moment arm, or transmission quantity was computed or consulted in assembling this map. Every number below is geometry, provenance, or mass-closed-form — no utility.
**Evidence base:** B1–B4 (all receipts coordinator-re-verified) + wave-1 verified facts. Baseline untouched throughout.

---

## 1. WHAT THE EVIDENCE SUPPORTS (measured, receipted)

| fact | number | receipt |
|---|---|---|
| source chain | `humerus → ulna → radius → hand(_r/_l)`; ulna origin = elbow | B1 |
| source ulna segment length | 0.02307 m (elbow-head piece); radius carries 0.29203 m to the hand origin | B1 + coordinator re-measure |
| source ulna sites (10/side) | spread \|p\| 0.0155–0.1028 m from the ulna origin (ECU-P4 farthest, perp-off-axis 0.1015 m) | coordinator measure, this pass |
| source hand | 5 sites/side, \|p\| 0.0299–0.0428 m; 27 welded skeleton geoms (8 carpals, 5 metacarpals, 14 phalanges), distalmost `3distph` at \|p\| ≈ 0.1554 m; ZERO digit joints; mass 0.4575 kg | B1 receipts |
| source masses | ulna 0.729 kg, hand 0.4575 kg (inertials present) | B1 |
| laterality | source left/right exact z-mirrors (origins, site locals — coordinator re-measure; ulna body-y 5.0e-5 m the only arm-frame asymmetry, B4) | B4 + coordinator |
| target joints | 28; elbow_L/R and wrist_L/R exist; fitted elbow/wrist origins equal the pack joints exactly (anchor gap 0.0 m) | B3, B4 |
| target forearm | elbow→wrist 0.064745 m both sides | B3 |
| target hand skin | connected paddle 0.1113–0.1114 m distal of each wrist; far end 47.1 × 18.1 mm; single 8-mm-voxel component; tri-ownership 445 triangles/side laterality-consistent 1154/1154 | B1 (v2/v3 receipts), B4 |
| unresolved cause | the four bodies are AUTHORED anchor-only (`prox == dist`, `axial_unresolved=True`, refusals 0) — class **(I) missing identifiers**: the pack declares no distal endpoint for them | B1; fit packet reason strings ("no fitted scale (endpoints not declared)") |
| body scale (radius, known-good) | s = 0.221707; factor-2 neighbor band [0.114, 0.458] (context metric per B4 amendment; the gate is resolution-consistency) | A4, B4 |
| correspondence schema | name→landmark map (`corr.landmarks`); segments reference landmark NAMES; vocabulary observed: `body_origin:X`, `site:X` | correspondence.py:121-129, B4 rebuild |

## 2. THE PROPOSED MAP — per body, preregistered candidates

Both hands/ulnae are exact mirrors in the source; every candidate below is stated for the right side and **mirrored for the left** (T3 laterality gate applies as-is; pack tri-ownership is laterality-consistent 1154/1154).

### 2.1 `ulna` (right; `ulna_l` mirrored)

**P (proximal):** `body_origin:ulna` ↔ target `elbow_R`. Anchor measured, gap 0.0 m. *(No choice needed — the pack joint exists and the fit already places the elbow there.)*

**P_d (distal) — TWO coherent authorings; this is F-2 in concrete numbers. Astra picks:**

| | **U-STR (structural)** | **U-ANA (anatomical)** |
|---|---|---|
| claim | ulna is what the source tree says: a 2.31 cm elbow segment | ulna is what the source SITES say: a forearm-length strip (anatomy-like) |
| P_d source ref | `body_origin:radius` (\|D−A\| = 0.02307 m) | `site:ECU-P4` (\|D−A\| = 0.10276 m) |
| P_d target ref | elbow_R + 0.005116 m along the elbow→wrist axis (authored named landmark; no pack joint exists there) | `wrist_R` (pack joint, anchor gap 0.0) |
| implied s_a | 0.2217 — on the body scale, in-band | 0.630 — 2.8× body scale, off-band (flagged, not auto-fail) |
| mass (m·\|det\|) | 0.729 × 0.2217³ ≈ **0.0080 kg** | 0.729 × 0.630³ ≈ **0.182 kg** |
| geometric consequence | the 10 ulna sites hang 0.016–0.103 m off a 0.023 m axis — frame extrapolation ≈ 4.4× the bone length; roll/scale error amplifies into ECU-P4's placement | ulna and radius frames then span the SAME elbow→wrist segment (overlap; the F-2 partition question) |
| uncertainty | (U)-split: structurally faithful, anatomically extrapolated | (U)-split: anatomically faithful, structurally re-partitioned |

**Roll ref Q (both authorings):** declare one of the measured off-axis sites — candidates `site:ECU-P2` (perp 0.0448 m), `site:ANC-P2` (0.0260 m), `site:TRIlat-P5` (0.0243 m); all ≫ ROLL_EPS 1e-9. **Astra picks** (or accepts the map's default proposal: `site:ECU-P2`, largest stable offset).

**Tolerances / uniqueness / falsifier (both):** B4 protocol T1–T6 as written (ROLL_EPS = JOINT_EPS = 1e-9; reconstruction ≤ 1e-6 m; orthogonality 1e-12; chirality +1; uniqueness by resolution-consistency count = 1). Entry-specific falsifier: if the fitted ECU-P4 lands outside the forearm/hand skin loops (loop authority, diagnostic side-check), the chosen authoring's frame extrapolation is refuted for site placement.

### 2.2 `hand_r` (left mirrored)

**P (proximal):** `body_origin:hand_r` ↔ target `wrist_R`. Closure-clean (wrist already equals `radius.P_d`; anchor gap 0.0). *(No choice needed.)*

**P_d (distal) + scale policy — THREE coherent authorings. Astra picks:**

| | **H-LEN (length-matched, uniform)** | **H-ASP (length+aspect)** | **H-BODY (body-scale)** |
|---|---|---|---|
| claim | the hand maps onto the whole paddle, uniform scale | length matches the paddle; width/thickness match the paddle cross-section | the hand keeps the body-wide scale |
| P_d source ref | `3distph` geom (0.1554 m) | `3distph` (0.1554 m) | any ref at 0.0344 m distal (e.g., authored knuckle-line landmark — the image of the fingertip under body scale) |
| P_d target ref | paddle far-end point (0.1113 m; B1 v3 max-extent voxel) | same | authored point 0.0344 m distal of wrist along the axis |
| implied scales | s = 0.716 uniform (3.2× body scale — flagged) | s_a ≈ 0.716; s_b ≈ 0.0471/0.061 ≈ 0.77; s_c ≈ 0.0181/0.020 ≈ 0.90 — locally coherent ~0.72–0.90 | s = 0.2217 uniform |
| mass (0.4575·\|det\|) | ≈ 0.168 kg | ≈ 0.227 kg | ≈ 0.0050 kg |
| site placement (sites at 0.030–0.043 m) | 2.1–3.1 cm past the wrist — mid-paddle | 2.2–3.9 cm (anisotropic) | 0.7–0.9 cm past the wrist — proximal paddle |
| uncertainty | target-hand proportion is 3.2× the source's (paddle 111 mm on a 64.7 mm forearm vs source 155 mm on a 315 mm forearm) — honest mismatch, stated not hidden | same + width landmarks are paddle-derived approximations of palm homologs | fitted hand occupies only the proximal third of the paddle; terminal tendon sites sit near the wrist |

**Roll ref Q:** the palm-plane normal — target: the paddle's flat normal (18.1 mm thickness direction, measurable from B1's voxel receipt); source: the metacarpal/phalanx spread plane (measurable from the 27 geoms; sites alone also span a plane: the 5 hand sites are near-coplanar). **Declared homolog: paddle-flat ↔ source palm-plane.** Astra may substitute; any pick passes T2 (offsets ≫ 1e-9).

**Tolerances / uniqueness / falsifier:** B4 T1–T6 as written. Entry-specific falsifiers: (a) if the paddle principal axis deviates > 15° from the elbow→wrist axis, the length anchor is not a hand-length homolog — H-LEN/H-ASP refuted for that purpose; (b) if any fitted hand site lands outside the paddle skin loop (diagnostic side-check), the authoring's placement is refuted.

### 2.3 Ownership identities (T1 — no candidates, facts)

Site ownership is fixed by the XML and NOT re-authorable: ulna keeps its 10 sites (incl. ECU-P2/3/4), hands keep their 5 each (ECRB/ECRL/FCU/ECU terminals), radius keeps its 16, thorax keeps the BIC origins. No mapping in this document reassigns any site. The only question is each body's FRAME, above.

## 3. SMALLEST IMPLEMENTATION CHANGE (upon approval)

1. **Authoring deltas only** in the correspondence: upgrade the four anchor-only entries to declared edges (proximal/distal/roll refs per the picks above) + add the required named landmarks (ulna-U-STR's derived point; hand P_d points; palm/knuckle refs). The name→landmark schema (`corr.landmarks`, correspondence.py:121-129) is native; **one verification item**: if the landmark VALUE vocabulary accepts only pack resolutions (`body_origin:`/`site:`), adding an explicit-coordinate or `mesh:`-derived resolution is a one-file extension — the single candidate for a code change, Astra-approved.
2. **One new fit session** under the unchanged falsifier regime (F1–F7, S1–S14 + B4 T1–T6 run on the declared map first) — as a NEW append-only revision with its own hashes. The frozen session-5 baseline is not modified.
3. **Supersession discipline (F-4):** ulna resolution re-anchors `radius.P` by first-child closure (JOINT_EPS 1e-9) — the A4-verified radius record is superseded by the new revision; the old record stays in the frozen baseline with its receipts. Requires Astra's explicit acceptance (this is F-2's mechanical consequence).

## 4. EXPLICIT BLOCKERS (no defensible mapping)

- **Digits — permanently out of scope** (F-1): zero digit joints in the source (27 welded bones, no articulation), zero digit joints in the 28-joint pack, paddle-only hand skin. No correspondence can create digit transmission; any digit claim is architectural invention.
- **U-STR vs U-ANA and the hand policy are Astra's picks** — the evidence supports all candidate authorings without deciding between them (that is reported as the decision, not as a blocker we may resolve).
- **Hand representation uncertainty (U-class, permanent):** the target is a paddle; the source is an articulated skeleton. Whatever policy lands, terminal tendon sites' positions represent paddle-interior points, not anatomical phalangeal attachments — the evidence ladder caps those claims at fitted geometry (A6 taxonomy applies unchanged).

## 5. WHAT HAPPENS ON APPROVAL (order, all gated)

1. Astra picks: U-STR/U-ANA · H-LEN/H-ASP/H-BODY · roll refs (or accepts defaults: ECU-P2; H-ASP with palm-plane roll).
2. Preregistration is FROZEN as chosen; B4 T1–T6 runs on the declared map (gate: all pass).
3. New fit session (append-only revision); S-suite green; superseded radius record documented per F-4.
4. T6/T7 evaluation for the 12 D2-unblocked tendons (and BRD's elbow arms) — measurement, reporting, no qualification claims without the full T-set.

## 6. EVIDENCE INDEX

B1 `audits/B1_source_anatomy/` (source dossiers, paddle measurements, correspondence digest rebuild) · B2 `audits/B2_ownership_chain/` (earliest breakers, unlock arithmetic 12/16) · B3 `audits/B3_mech_requirements/` (requirements sheets, F-1..F-4 flags, anchor-gap 0.0) · B4 `audits/B4_correspondence_challenge/` (protocol T1–T6, known-good ALL PASS, implicit-evidence inventory) · coordinator measurements this pass (site offsets, hand-geom extents — reproducible from the snapshot XML with the inline script logged in RECOVERY.md T14).
