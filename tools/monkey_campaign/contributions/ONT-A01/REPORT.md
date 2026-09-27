# ONT-A01 REPORT — ulna volar-side orientation evidence (attempt d7edda352388470092b17a35e17391ba)

Arrival `arrival-b0f76bd3017e49caa70b678b6c8be270`, card ONT-A01 (planning id A01),
criteria sha256 `2bcf59fa0b786b009b30711334e38fe374d9a2a2bdefdba9566a4018c4a9c775`.
Preregistration frozen and committed BEFORE any probe (commit `00c54861`, attempt
`fb552e4136ef4bfdaaa93686fb063e78`); this attempt is a VISUAL-ONLY correction of
that attempt's candidate (PR #164) and changes no measurement, threshold or
anatomy (see "Correction" below).

## done_when

> Independent anatomical evidence determines roll sign or records ambiguity

**Outcome: satisfied via the records-ambiguity arm — `AMBIGUITY_RECORDED`
(fired F2/F4), with the sign itself reproducing the record exactly.**

## Correction (review 21f80a5b CHANGES_REQUIRED — visual only)

The independent review reproduced a visual falsifier against the previous head:
the V3 whole-bone panels CLIPPED their declared subject (anterior 21/211 and
posterior 21/211 ulna vertices outside the panel, max py = 371.908 px on 360 px
panels; oblique 2/211, max py = 361.144; superior 0), and V2's declared ECU
tendon course waypoint ECU-P4 exited its panel (py = 372.7) — firing the
anatomy profile's own "clipped/occluded subject fails". Fix, per the review:

- `ota01_render_views.fit_camera`: every camera is now framed from the
  PROJECTED BOUNDS of its view's declared subject point set
  (`declared_subject_points`, same pinned geometry, no hand-tuned spans):
  the target is re-centered on the projected-bounds midpoint and the
  orthographic span is the fitted extent x (1 + `FRAME_MARGIN`), with
  `FRAME_MARGIN = 0.08` the single uniform framing margin. V1/V2 keep their
  review-approved view directions; V3 keeps its four bookmarks and one common
  span (the largest fitted), each bookmark re-centered on its own bounds.
- V2 stays the preregistered close-up: its framed subject set is the six
  labeled sites + ECU course waypoints + volar/dorsal arrow tips (the mesh is
  the backdrop; partial mesh framing is declared close-up semantics). V3
  frames ALL 211 pinned ulna vertices + 4 axis-arrow tips per bookmark.
- `assert_in_bounds` runs at generation time; `TestAllBookmarkSubjectBounds`
  in `test_ota01_roll_sign.py` is the all-bookmark bounds regression: every
  declared subject point of EVERY view/bookmark in the COMMITTED manifest must
  project inside its panel with the margin. It FAILED first on the uncorrected
  evidence (V2 ECU-P4 at py = 372.660; V3 anterior/posterior py to 371.908)
  and passes on the regenerated capture (all insets >= 13.333 px).
- Two consistency repairs found while reframing (no anatomy/threshold change):
  screen-space label offsets now flip deterministically to stay inside the
  panel (`label_offset_inside`; the reframe had pushed the TRIlat-P5 label
  off-panel), and the V2/V3 overlay arrows are now drawn in the same
  bottom-up axes as their labels (py -> H - py, the V1 triad convention);
  previously the arrows were vertically mirrored relative to their own labels
  (pre-existing defect in the reviewed capture, visible as the V3 "+y" arrow
  pointing down).
- Numerical evidence is untouched: `state_snapshot.json` and
  `numerical_receipt.json` regenerate byte-identical EXCEPT the attempt_id
  provenance field (this correction attempt); P1/P2/P3 values, fired F2/F4 and
  `AMBIGUITY_RECORDED` are identical (verified value-by-value against the
  previous head). PREREGISTRATION.md is unchanged (frozen bytes). Capture,
  manifest, context, provenance and qualification receipts are regenerated
  and re-validated (canonical `visual_capture.validate_manifest` and
  `visual_gate.verify`: structurally_valid, 6 views). Rasterization stays the
  honestly-labeled deterministic CPU z-buffer rasterizer; no native frames,
  no GPU. Test suite: 26 CPU tests (was 24; +2 bounds regression), all pass.

## Reconcile-first: what existed (reused, pinned — nothing repeated)

- The O1 audit (`O1_ulna_orientation`) on play lane `forearm-package-20260924`,
  integrated at `c3255f74`, already RESOLVED the U-STR roll sign: source volar +x
  ↔ target volar +z (anterior), azimuth law +90°, 180° flip refuted unanimously
  (ECU-P2 / ANC-P2 / TRIlat-P5). Its own brief.md froze its predictions first.
- ONT-P02 lineage map (`8c7ed8c2`): identities and kept-separate relations reused;
  this card fuses nothing.
- Membrane ontology rev 2: `bones` gap "individual bone membership must be
  imported from a pinned source and anatomically resolved" — this evidence feeds
  that gap for one bone, evidence-only; all touched membranes remain
  `binding: unresolved`, `physics: not_qualified`.
- CT MorphoSource 000875604: `bone_identification_v3` labels forearm bones only
  `forearm_class`, `side_rule: "sides never assigned (the curl jumbles them)"` —
  the CT cannot yet re-decide radius-vs-ulna or volar side. Recorded as an
  explicit unresolved item; NOT invented around.

## What this attempt built (the genuinely missing, task-owned work)

1. `ota01_roll_sign.py` — re-measurement from pins with hash assertions
   (`monkey_birth.bin` 550a5b3e…, `monkey_joints.bin` 74b3ab04…, `ulna.stl`
   71026415…; extracted references byte-preserved, `reference/EXTRACTION.json`).
   Section code carried over VERBATIM from the pinned O1 script; method identity
   asserted by comparing the recomputed axis/basis to the pinned receipt
   (matches to 1e-9) BEFORE any verdict.
2. Numerical receipt (`evidence/numerical_receipt.json`): measured vs receipt
   side by side, frozen tolerances, falsifier bookkeeping.
3. Anatomy-profile visual capture (`evidence/capture_sheet.png` +
   `capture_manifest.json`): 3 declared views × diagnostic/clean pairs, all
   profile camera fields, honest deterministic-CPU render label (numpy z-buffer
   software raster + Agg text; NOT native engine frames). Clean rows: true
   z-buffer depth-tested, no diagnostics. Diagnostic rows: occlusion 'mixed'
   (overlays intentionally unoccluded). Validated by the canonical
   `visual_capture.validate_manifest` and `visual_gate.verify`.
4. Qualification receipt (`evidence/qualification_receipt.json`) in the
   `ontology_queue.qualification` shape: absolute evidence paths + recomputed
   sha256 for source / numerical / independent_review / visual / camera,
   capture_context, `head_sha: null` with binding note (reviewer pins it to the
   reviewed PR head).
5. `test_ota01_roll_sign.py` — 26 CPU-only tests (python -B), all passing
   (24 original + all-bookmark bounds regression per review 21f80a5b).

## The measurement result (both readings preserved)

- P1 source bone: olecranon is the extreme −x feature, x = −28.321 mm (matches
  receipt to 0.000); distal y = −297.095 mm (matches to 0.000). VERIFIED.
- P2 target olecranon test: best station t = +6 mm, D = +3.2891597453 mm —
  IDENTICAL to the pinned receipt (Δ = 0.000); bootstrap std reproduced (0.733 mm,
  seed-0). VERIFIED at the record's preregistered best-station criterion.
- P3 sign law: unanimous NO-FLIP across all three witnesses; TRIlat-P5 no-flip
  error 0.149° (frozen tolerance ±1.0°); law az_target = az_source + 90°. VERIFIED.
- FROZEN STRICT ZONE (my P2 phrasing): "D > 2 mm for every station t ∈ [−2,+12]"
  FAILED at t = +8 mm: D = +1.8135108487 mm, BYTE-IDENTICAL to the pinned
  receipt's own table, where +8 is likewise unmarked. This is a transcription
  over-strictness in MY frozen prediction, not measurement drift and not a
  contradiction with the record. Per the frozen rules (no tuning, no dropping
  dissenters) F2/F4 fired and the outcome is AMBIGUITY_RECORDED. The ambiguity
  is precisely located: the zone-shape claim; the volar/dorsal identification and
  the roll sign remain over-determined by P1 + P3 + the best-station test.

## Honesty notes

- Capture is component/records evidence for an anatomy evidence subject; no
  behavior claim about the real application is made; render backend labeled
  deterministic CPU (no GPU, no network, no native frames).
- A quaternion conversion bug (trace>0 branch divided by 4s instead of 2s) was
  introduced and CAUGHT by the round-trip test; capture and receipts were fully
  regenerated afterwards and the suite passes (24/24).
- Zero writes outside the attempt workspace; E:/PythonChimera and the play
  worktree only read.

## Files

- PREREGISTRATION.md (frozen first), REPORT.md (this file)
- ota01_roll_sign.py, ota01_render_views.py, make_qualification_receipt.py,
  _make_extraction.py, test_ota01_roll_sign.py
- reference/ (EXTRACTION.json + byte-preserved pins), evidence/ (state, numerical,
  independent_review, capture manifest/context/sheet, visual provenance,
  qualification receipt)
