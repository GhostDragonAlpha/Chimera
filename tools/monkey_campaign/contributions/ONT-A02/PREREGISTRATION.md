# ONT-A02 preregistration — radioulnar definition, independent evidence, B4 result, before/after radius mapping

Task `ONT-A02`; planning item `A02`; attempt `b4a2b12b8c854e55bc400c64a502c85c`;
arrival `arrival-e20cc96d4f8a4a1894424fcae60e422a`; criteria SHA-256
`ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1`;
attempt checkout base/head `c525b82c7c3ce0128565424764293a3c85811ab3`, branch `branch-5`.

## Sequence disclosure (explicit, made before any new probe ran)

Before this freeze, read-only reconciliation had already: (a) read the pinned historical
receipts (O1 at `c3255f74`, R1 at `d02af013`, I7 at `f1023853`), the prior same-card
attempt `81687b20b3804a689114857234c28838` (reconciliation-only, `NOT_QUALIFIED`), and
the accepted ONT-A01 winner pattern; (b) extracted the byte-pinned input files listed in
`reference/EXTRACTION.json`. NO new numerical recomputation, no coverage re-derivation,
and no render had been executed by this attempt at freeze time. The predictions below
were authored from the pinned receipts' numbers; their independent recomputation is
exactly what this attempt tests. Any mismatch is reported as it falls; nothing is tuned.

## Exact scope

`done_when` is conjunctive: "Radioulnar definition, independent evidence, B4 result and
before/after radius mapping are presented". This attempt presents all four, bound to the
declared U-STR candidate (I7 receipt 00), and re-derives the numerical content from the
byte-pinned inputs with this attempt's own code (C01 round-trip/handedness/landmark
checks; C16 coverage topology). It does NOT: select a production mapping, execute any
fit or supersession, modify the frozen radius record, change anatomy or constants,
re-run the B4 gate itself (the receipted I7 run stands as history), or claim mechanical
grasp/runtime qualification. R1's anatomical refutation is retained, never relabeled.

## Statement (frozen)

The evidence supports only this bounded result: the radioulnar offset is a kinematic
joint-frame offset (source radius body origin in the ulna frame, 23.0746 mm, 51.63
degrees oblique, = 7.5459 pct of the authored 305.7922 mm elbow-to-hand distance) with
NO primary-anatomical support as a radial-head placement (R1 falsifier FIRED: primary
band ~0-1 pct, frozen plausibility band [4,12] pct missed by >= 3.0 pts); the isolated
U-STR B4 diagnostic (I7) passed the existing T1-T6 protocol 12/12 side verdicts + T6
process PASS as a SOURCE-KINEMATIC FIDELITY statement only; declaring the ulna
machine-forces a radius re-anchor (shared-joint closure gap 5.1158 mm >> JOINT_EPS
1e-9, refusal `shared_joint_separation`), whose closed-form consequence is the
before/after radius map below (uniform scale 0.22170679566544982 -> 0.20418868001006546,
-7.901478889180636 pct, det(L)=s^3, rigid part G unchanged). The after-map remains an
UNAUTHORIZED, UNEXECUTED production supersession candidate; PT(x2) become chain-defined
and BRD(x2) elbow arms repair under the diagnostic-only ulna resolution; hand- and
thorax-blocked chains stay open.

## Predictions for the post-freeze probes (frozen tolerances)

Tolerances are frozen BEFORE any probe ran. Reproduction means this attempt's own code,
from raw pinned inputs, NOT copying receipt floats.

- P1 source radioulnar identity (C01): XML-derived global body origins (rest pose walk)
  match the declared candidate source landmarks to 1e-12 m; |radius_origin - ulna_origin|
  = 23.0746 mm within 5e-4 mm; |hand_r_origin - ulna_origin| = 305.7922 mm within 1e-3 mm;
  |hand_r_origin - radius_origin| = 292.0294 mm within 1e-3 mm; offset fraction =
  7.5459 pct within 1e-3 pts; obliquity to the forearm axis = 51.63 deg within 0.05 deg.
- P2 owner discrimination (falsifier FE): the ulna-frame offset reproduces P1; computing
  the same norm from the WRONG owners (humerus-origin, hand_r-origin, radius-frame
  radius->hand distance) must NOT reproduce it. The wrong-owner norms are recorded.
- P3 target before/after map: |elbow_R -> wrist_R| = 64.7449 mm within 5e-4 mm
  (independent sources: target pack joints AND known-good record landmarks agree to
  1e-12 m); derived distal point d = 23.0746 mm x 0.22170679566544982 = 5.1158 mm within
  5e-4 mm; declared ulna.P_d lies ON the elbow->wrist line within 1e-9 deg; span_after =
  59.6291 mm within 1e-3 mm; s_after = span_after/span_src = 0.20418868001006546 within
  5e-15; scale change = -7.901478889180636 pct within 5e-13; det(L_after) = s_after^3
  within 1e-12 relative; max|G_after - G_packet| <= 1e-12 both sides; left/right mirror
  agreement within 1e-9 m / 1e-12 for unitless fields.
- P4 mechanism: gap = |radius.P_packet - ulna.P_d| = 5.1158 mm > JOINT_EPS 1e-9
  (refusal `shared_joint_separation` would fire with ulna declared; re-anchor forced).
- P5 C01 round-trip and landmarks: with the map law x_world = P + L x_loc (L = s*G for
  the AFTER construction, composed Bp*diag(s)*B^T): L_after maps the source landmarks
  (radius origin local 0, hand_r origin local src_D-A) exactly onto ulna.P_d and
  wrist_R within 1e-12 m; L_before (packet scale/rotation) reproduces every packet
  fitted_pos_global of the 16+16 radius sites within the protocol's own RECON_TOL_M
  1e-6 m; det of both ONBs = +1 within 1e-12 (handedness preserved); round-trip
  L^-1 L = I within 1e-12.
- P6 C16 coverage topology (XML-derived): baseline complete = 2 (BRD pair);
  diagnostic-ulna-only complete = 4 (adds PT pair); plus-hand context = 14; hand-blocked
  = 8; ECU pair double-blocked (ulna mid-chain + hand terminal); BIC x4 thorax-blocked;
  `elbow_flexion(_l)` coordinate owner = ulna/ulna_l in the XML. All counts must equal
  the pinned receipt 10 categories.
- P7 R1 drift law: 7.5459 pct x (k_rad / (64.7449 mm/305.7922 mm)) = 7.9015 pct within
  1e-6 pts; anatomical falsifier remains FIRED: 7.9015 pct outside [4,12] pct and
  outside the primary band (receipted as ~0-1 pct); the receipt records
  `anatomical_support: false` and preserves both readings.
- P8 visual capture (anatomy profile): three declared views (whole-creature overview;
  local attachment close-up; orthogonal side and oblique views), each with a
  diagnostic+clean pair; all 15 camera_required_fields per manifest row; every declared
  subject point strictly inside its framed panel with the uniform 8 pct frame margin
  (generation-time guard + regression); the state snapshot sha256 is byte-identical
  before and after rendering all view toggles; the canonical campaign validator
  (visual_capture.validate_manifest) returns structurally_valid true.

## Falsifiers (frozen refusal rules)

- FA: any P1-P8 prediction failing beyond its frozen tolerance. Fired falsifiers are
  reported with numbers and both readings preserved; no tolerance is moved post hoc.
- FB: any presentation of the after-map as executed, authorized, anatomically
  supported, or production-accepted; any changed historical radius/baseline value.
- FC: clipped/occluded declared subject, label ambiguity, a missing camera field, or a
  state-hash change across view toggles (the anatomy profile's own falsifier).
- FD: relabeling the B4 source-kinematic PASS as anatomical evidence, or omitting R1's
  refutation from the presented radioulnar definition.
- FE: wrong owner/frame identification (offset attributed to or computed from the wrong
  body/frame). The owner-discrimination probe (P2) must separate them numerically.
- FG: any test invocation exceeding 120 s wall or 16 MiB new output; any GPU, network,
  native build, or source-checkout write.

## Frozen probes and views

Probes: (i) XML rest-pose global walk + owner maps; (ii) target pack joint positions
(hash-pinned loader); (iii) closed-form before/after map construction from the declared
candidate + packet radius records (own implementation of the DERIVATION 5.1 ONB law);
(iv) landmark round-trip oracles; (v) XML tendon-path ownership coverage classification
under three resolved-body scenarios; (vi) deterministic CPU z-buffer render of the three
views with diagnostic/clean pairs; (vii) canonical validator + bounds + state-hash
regressions. Views frozen:

- V1 whole-creature overview (target world frame, m): pack mesh, frame triad, forearm
  region box, elbow_R/wrist_R labels, BEFORE/AFTER radius anchor markers.
- V2 local attachment close-up (target frame, mm scale): elbow->wrist edge, BEFORE vs
  AFTER proximal anchors with the 5.1158 mm gap, all 16 radius site globals before
  (filled) and after (open), PT tendon course (the newly-defined chain) before/after.
- V3 orthogonal side and oblique views (source rest frame, mm): source ulna, 4 bookmarks
  (anterior, posterior, left-lateral oblique, superior), radius-body-origin offset vector
  with 23.0746 mm / 51.63 deg annotation, volar/dorsal axes.

Diagnostic rows: occlusion 'mixed' (mesh depth-tested; overlays intentionally unoccluded
= xray semantics). Clean rows: 'depth_tested' (true z-buffer). HONESTY: CPU software
rasterizer + Agg compose; NOT native engine frames; no application run is claimed.
