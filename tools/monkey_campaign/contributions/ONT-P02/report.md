# ONT-P02 CORRECTION REPORT - visible_static qualification capture

Attempt b248ac961ccb44b3b4b141c5878e9bd5 (agent arrival-cf4d4f8e72d94ad9b73185eb402ff1bd)
Criteria 5c0720b4451b8b9ea22360575461968667496000220c8cba645e1d3e28f252ef (unchanged)
Date 2026-09-26. python -B CPU-only throughout; no GPU; no engine process.

## 1. Scope of this correction

Lead CHANGES_REQUIRED on PR #144 (head 8c7ed8c27d9e27d1210a7754cb17831bd4ec1532):
the lineage-map records leg is verified and PRESERVED (reviewer PASS 152 checks /
23 pins; falsifier 23/23); the only missing item is the visible_static
qualification capture. This candidate therefore:

- bases on the preserved head (candidate parent == 8c7ed8c2; the four
  records-leg files are untouched, byte-identical, hash-checked at checkout);
- adds ONLY the visible-static capture deliverables under
  contributions/ONT-P02/ (nothing else in the tree changes);
- updates the qualification receipt draft with NEW visual+camera evidence and
  REUSED records legs by reference + hash.

## 2. Subject

tools/playable_slice/standing_body.obj @ 33e7a444 (blob ef6f3530..., sha256
bc9033bfc6c54db0220364821ee19028bf2ac6f740dc70f4c1e9be5f02089111, 18469042 B,
249743 verts / 499976 tris) - the runtime_body render leg pinned by
monkey_lineage_map.json (ev_standing_body). Extracted with read-only git
plumbing into the attempt scratch only; sha256+bytes asserted before parse.
All measurement predictions frozen in PREREGISTRATION.md section 2 were
re-derived at build and in tests: bbox, scene contact band (230 verts,
centroid (-0.079259, -0.131367, 0.258219), owners {b02: 169, b06: 61}),
contiguous per-bone segmentation (25 blocks, sums == pinned per-bone counts,
every face block indexes only its own vertex block), hind chain "a" centroids
and the b02-b06 joint proxy.

## 3. What was built

- evidence/capture.png - ONE hashed 2120x840 deterministic CPU contact sheet,
  6 pixel_rectangle rows: whole-creature overview, local attachment close-up,
  orthogonal side and oblique views (one view, two declared bookmarks: tick 0
  side + tick 1 oblique panels), each diagnostic+clean. Clean panels are own
  panels with ZERO annotations (depth-tested envelope only); diagnostic panels
  are declared xray: envelope ghost pass + per-bone pass (hind chain "a"
  highlighted: b02 femur, b06 tibia, b20 fibula, b15/b22/b25 foot_class; sides
  never assigned), frame-axes triad, anchored callout labels with leader lines,
  and the owner-mapping panel (visual=standing_body.obj bc9033bf.., physics=
  membrane creature default 13824.5 kg, binding=RENDER_BINDING, ports none /
  connection_ids []) including the explicit ABSENT inventory for muscle/tendon
  paths (no muscle lineage pinned for the runtime body; MSK model
  KEPT_SEPARATE - nothing invented).
- evidence/capture_manifest.json - chimera.visual_capture_manifest.v1,
  profile anatomy, tick_interval [0,1], all declared camera fields, state_bound
  to the pinned subject bytes (constant across all rows: view toggles preserve
  the physical state hash).
- evidence/capture_receipt.json, evidence/numerical_receipt.json,
  qualification_receipt.json (draft; visual+camera NEW, source/numerical/
  independent_review reuse the verified PR #144 legs), card_task.json
  (contract extracted verbatim from the live packet), capture_build.py,
  test_capture_build.py, PREREGISTRATION.md.

## 4. Validation (all in-process, this machine)

- visual_capture.validate_manifest + visual_gate.verify against card_task.json:
  structurally_valid TRUE, 6 views, image kind, profile anatomy
  (visual_acceptance false by design - structural gate only; independent
  review remains the acceptance gate).
- test_capture_build: 11/11 OK (subject identity, frozen predictions,
  manifest+gate, view/layer coverage, clean-view purity, state-binding
  constancy, label binding 1:1, rects inside sheet, full-view all-vertex
  frustum, close-up anchors, fixed-bookmark identity).
- Records leg re-verified at the candidate tree: verify_monkey_lineage.py
  --expected-criteria ... outcome PASS, 152 checks, 23 pins;
  test_verify_monkey_lineage 23/23 OK in 23.3 s.
- Frozen falsifier probes at build: all-vertex in-frustum (margin >= 2 px,
  z in [near+0.01, far]) for overview/side/oblique - 249743/249743 each;
  close-up anchors in frame 4/4. Frame/owner mapping rendered in every
  diagnostic panel; every label_id drawn and bound 1:1.

## 5. Preregistration discipline and deviations

PREREGISTRATION.md v1 (sha256 f6f241444808733f41c107d2549497bff6adc7891c0b5e6
ec9e6db52b5929b0a) was frozen BEFORE the first build. Amendments (section 11):

- v2: overview eye (0.55, 0.42, -1.05) -> (0.32, 0.24, -0.60); anchored callout
  labels; brighter diagnostic alphas. Reason: the v1 build rendered and passed
  the structural gate, but visual inspection showed a too-loose overview
  framing and overlapping label text (label-ambiguity falsifier risk). No
  evidence was declared from v1.
- v3: overview eye -> (0.62, 0.30, 0.18) (side-perspective). Reason: the v2
  all-vertex frustum probe and gate PASSED but the view looked down the body's
  long axis from the tail end, ballooning the near pelvis ~2.3x and occluding
  the body (occluded-subject legibility defect). All other freezes unchanged in
  both amendments; every amendment happened BEFORE the retry build, per the
  frozen deviation rule.

Incidents (recorded honestly):
1. First build crashed AFTER writing capture.png: the gate import path pointed
   into the sparse attempt checkout where visual_gate.py is not materialized;
   fixed by resolving the canonical campaign validators
   (E:/PythonChimera/tools/monkey_campaign) with an in-tree fallback. No
   invalid artifact was consumed or declared.
2. A manifest precheck failure (numpy-scalar quaternion rejected by the
   validator's type check) was fixed by converting samples to Python floats
   BEFORE any gate run; the earlier precheck ran against a fake capture hash
   and was re-run clean.
3. A whole-file rewrite of capture_build.py normalized line endings (CRLF->LF)
   during the v3 edit; content-neutral, asserted by the final test run.

## 6. Artifact hashes (this candidate)

- evidence/capture.png 127e18fce08e55ea2a4c767da3c7f9e733a02d8e72a051160b7193bbde52c31b (263219 B)
- evidence/capture_manifest.json 116fe870e8411333f546b050b5a47a7244b3d7ba08d30d7592f09e6a70ec4efc
- evidence/capture_receipt.json a1b145e1f4117fc703bcf4720d3d0abcfa6add68b267a9637d89483f926d08de
- evidence/numerical_receipt.json 56087a767f60033f710ea5dea6d22bc6a42d2912b00560fbfeed641fe73fde7d
- qualification_receipt.json (see file; hashed in receipt.json)
- card_task.json 17b9d035ca134f9c69d8a35fba6c7c7dce16afd8197a16330ba03fd25f8afc12
- PREREGISTRATION.md b2b38be739b7cd9c2648211a35a670e4c83a04c109c94d99a1350a95049cd156
- capture_build.py b057ced4fe0e7de1a846af5d5422a379eec907353c993f235a8e1a2f51ffe8ab
- test_capture_build.py cb82d0ecdb42ac50b1e5e715641dbb8b0535b7f93a1913a725f4d0947033fe18

Determinism: rebuild with the committed capture_build.py reproduces the same
capture.png bytes (numpy fixed-order math, stable argsort, PIL PNG
compress_level=6, no timestamps). Budget: total request artifacts ~0.4 MiB
(<< 16 MiB); capture.png 257 KiB.

## 7. Remaining gates (unchanged ownership)

1. Independent review of this correction candidate (auto-queued).
2. Lead publication to review/ONT-P02 on top of 8c7ed8c2.
3. Operator MorphoSource ship-asset decision (distribution gate).
4. W04 owner: new CoT-denominator registration (D-W04 section 7).
