# ONT-P02 PREREGISTRATION - visible_static CORRECTION (attempt b248ac961ccb44b3b4b141c5878e9bd5)

Frozen BEFORE any capture build step. 2026-09-26. Criteria sha256
5c0720b4451b8b9ea22360575461968667496000220c8cba645e1d3e28f252ef (unchanged).
Scope sha256 01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6.

## 1. Statement (correction scope)

The lead's CHANGES_REQUIRED finding on PR #144 (head 8c7ed8c27d9e27d1210a7754cb17831bd4ec1532)
PRESERVED the lineage-map records leg (reviewer PASS: 152 checks / 23 pins, falsifier
23/23) and requires exactly ONE missing item: the visible_static qualification capture
(camera-pinned anatomy evidence per visual_capture manifest schema) over the
lineage-pinned subject. The map is NOT re-derived; the records leg is reused by
reference at the verified bytes.

Prediction: adding the capture + visual/camera evidence entries to the qualification
receipt, with the records legs byte-identical to the verified PR #144 head, satisfies
the card's visible_static profile validation (visual_capture.validate_manifest +
visual_gate.verify) and leaves every verified number unchanged.

## 2. Subject pin (the lineage-pinned runtime render body)

- File: tools/playable_slice/standing_body.obj at commit 33e7a444fe7b4c35aa99afe7ef898046877025b4
- Git blob: ef6f35302e1c00287b4c13c8cfbf276c7f3879d0
- sha256: bc9033bfc6c54db0220364821ee19028bf2ac6f740dc70f4c1e9be5f02089111
- Bytes: 18469042; 249743 verts; 499976 tris (import payload in body_manifest.json
  chimera.real_body.v1 @ 6d0328ce..., pin ev_standing_body in monkey_lineage_map.json
  @ 6a9d4ac8...)
- Extraction: read-only git plumbing (git cat-file blob) into the attempt scratch
  directory only; sha256 asserted after extraction. ZERO writes to any source
  repository, the play worktree, or other attempts.

Derived (measured from the pinned bytes BEFORE this freeze; frozen as predictions,
re-asserted by the build and by test_capture_build.py):

- bbox min = (-0.159165, -0.134714, -0.153386), max = (0.102051, 0.134568, 0.451770)
- scene contact band (verts with y <= ymin + 0.005): 230 verts, centroid
  (-0.079259, -0.131367, 0.258219), owners {bone 02: 169, bone 06: 61}
- per-bone vertex blocks are contiguous in manifest order (bone_01..bone_25);
  per-bone decimation.verts/faces sums == 249743/499976; every face block indexes
  only its own vertex block
- hind chain "a" members (bone_identification_v3 specimen 000875604, sides never
  assigned): 2=femur, 6=tibia, 20=fibula, 15/22/25=foot_class; centroids measured,
  joint proxies = midpoints of consecutive member centroids (PROXIES - no joint
  anatomy is pinned; never presented as resolved joints)

## 3. Frame and owner mapping (falsifier: wrong owner/frame fails)

- frame_id: playable_slice_scene_yup_m (the committed compose's declaration: scene
  metres, Y-up, right-handed; pads' mean plane y=0 per the committed OBJ header and
  scene_boot.build_standing_layer); coordinate_unit m; handedness right.
- Owner mapping rendered in every diagnostic panel: VISUAL = standing_body.obj
  (bc9033bf..) CT-derived render body; PHYSICS = the slice membrane creature
  (default mass 13824.5 kg; separate inventory lineage, NEVER-INTERCHANGED);
  binding = RENDER_BINDING; ports = none declared (P02 ontology connection_ids []).
- Orientation convention: quaternion_wxyz_camera_to_frame, forward +Z, up +Y.

## 4. Views, layers, clean pairs (frozen profile strings)

Profile anatomy / visible_static; all three profile views, each as a diagnostic+clean
pair (clean_view_required true):

1. "whole-creature overview" - perspective, vertical_fov 40 deg, eye =
   center + (0.62, 0.30, 0.18) [AMENDED v3; v2 was (0.32, 0.24, -0.60), v1
   was (0.55, 0.42, -1.05)], target = bbox center, distance_to_target =
   |eye-target| (computed exactly), near 0.05 far 10, 640x420.
2. "local attachment close-up" - perspective, vertical_fov 40 deg, eye =
   contact_centroid + (-0.20, 0.06, -0.14), target = contact_centroid
   (-0.079259, -0.131367, 0.258219), near 0.02 far 5, 640x420.
3. "orthogonal side and oblique views" - ONE view row, TWO camera bookmarks:
   tick 0 = side (orthographic, span 0.80 m, eye = center + (1.2, 0, 0),
   target = center), tick 1 = oblique (orthographic, span 0.80 m, eye =
   center + (0.85, 0.55, -0.85), target = center); near 0.05 far 10, 420x420 per
   bookmark panel; sample_mode sampled_trajectory, interpolation
   linear_position_target_slerp_orientation. The row's image rectangle is the
   two-bookmark contact pair (side panel left, oblique panel right).

All views: fixed_bookmark rows carry the SAME pose at tick 0 and tick 1
(tick_interval [0,1] globally). Aspect_ratio == width/height exactly.

Diagnostic layers per view (union must cover the six profile layers):

- overview + side/oblique: ["outer envelope", "selected bones/joints",
  "muscle/tendon paths", "attachment sites", "frame axes", "stable 3D labels"]
- close-up: all of the above except "frame axes" (the origin triad is outside a
  0.25 m close-up frame; it is not claimed there)

Clean pairs: envelope only, occlusion_mode depth_tested, zero diagnostic pixels
(clean panels rendered as their own panels).

## 5. Layer render inventory (task-owned subset; absent parts inventoried)

- outer envelope: the pinned mesh, shaded; xray-ghost tone in diagnostic panels.
- selected bones/joints: per-bone blocks (verified segmentation); hind chain "a"
  members highlighted + labeled (#hindchain_a_femur_b02, #hindchain_a_tibia_b06,
  #hindchain_a_fibula_b20, #hindchain_a_foot_b15, #hindchain_a_foot_b22,
  #hindchain_a_foot_b25); remaining bones muted. Labels carry bone number + class
  only (sides never assigned per identification v3).
- muscle/tendon paths: ABSENT - no muscle/tendon lineage is pinned for the runtime
  body (FreeMusco Chimanoid MSK is KEPT_SEPARATE analysis-only). Rendered ONLY as
  the explicit inventory line + label #absent_muscle_tendon in diagnostic panels.
  No muscle geometry is invented (card step: never invent missing anatomy).
- attachment sites: #attach_contact_patch (measured scene contact band centroid,
  owner: scene placement y=0 plane declaration), #attach_joint_b02_b06 (DECLARED
  centroid-midpoint proxy for the 2-6 touching edge, gap 2.91 mm per identification
  v3 - never a resolved joint), #owner_membrane (physics owner binding label at
  body center), #ghost_overlay (ghost_standing.obj same-compose overlay binding).
- frame axes: +X/-X/+Y/-Y/+Z/-Z triad at origin (0.2 m arms, X red, Y green, Z blue),
  labeled #frame_axes_world (overview + side/oblique diagnostics only).
- stable 3D labels: every label_id above; each bound to exactly one subject_id;
  occlusion_mode xray in diagnostic panels (bones must be visible through the
  envelope; that is the declared xray diagnostic), depth_tested in clean panels.
  [AMENDED v2] 3D-anchored labels are drawn as anchored callouts: a marker dot
  at the projected anchor plus a thin leader line to the label text stacked at
  a fixed panel-edge column (deterministic order = declared binding order), so
  labels never overlap each other (label-ambiguity falsifier).
  #frame_axes_world stays at the triad; the absent-inventory label stays
  panel-anchored text.

## 6. Falsifier probes (all asserted at build; failures recorded, never silenced)

- P1 wrong owner/frame fails: frame_id + owner mapping line rendered in every
  diagnostic panel; manifest camera frame_id == declared; unit m.
- P2 hidden/outside placement fails: every required subject anchor projects INSIDE
  its viewport with margin >= 2 px, camera-space z within [near, far], in both
  panels of its pair. Required ids: overview + side/oblique = [env_standing_body]
  (ALL 249743 verts in frustum for these full views); close-up =
  [attach_contact_patch, attach_joint_b02_b06] plus the close-up label anchors
  (#hindchain_a_femur_b02, #hindchain_a_tibia_b06).
- P3 clipped/occluded subject fails: P2 in-frustum check on the full vertex set;
  clean panels depth_tested envelope only; no near-plane intersection (all
  camera-space z > near by >= 0.01).
- P4 label ambiguity fails: label_ids unique, one binding each, binding label set ==
  declared label set (validator-enforced), and each drawn label text == its label_id.
- P5 view toggles preserve the physical state hash: every view row's state_binding
  is {kind: state, sha256: bc9033bf..9111} - the pinned subject bytes; diagnostic
  and clean pairs share camera AND binding (validator-enforced). No view or layer
  toggle changes the state bytes.
- P6 numerical: section 2 constants re-derived from the pinned blob at build and in
  tests; any mismatch FAILS the build.

## 7. Determinism prediction

numpy fixed-order float math + stable argsort (tiebreak by triangle index) + PIL
ImageDraw PNG (no timestamps) reproduce a byte-identical capture.png on rebuild.
Manifest capture_sha256 == sha256(capture.png) at write time; visual_gate.verify
re-run in-process passes (structurally_valid true, visual_acceptance false - the
gate is structural; independent review remains a gate).

## 8. Honest boundary

Deterministic CPU software rendering (numpy + PIL painter's algorithm) of the pinned
mesh bytes. NOT native engine frames; no GPU; python -B CPU-only; no engine process.
This is the declared deterministic-CPU honest label per the lead's correction.

## 9. Deliverables and budget

contributions/ONT-P02/: PREREGISTRATION.md (this file, byte-identical copy of the
frozen workspace-root original), card_task.json (contract extracted verbatim from
the live packet), capture_build.py, test_capture_build.py, evidence/capture.png
(single hashed contact sheet, all 6 rows' rectangles), evidence/capture_manifest.json
(chimera.visual_capture_manifest.v1), evidence/capture_receipt.json,
evidence/numerical_receipt.json, qualification_receipt.json (updated: visual+camera
= new evidence; numerical/source/independent_review = reused verified PR #144 legs
by reference + hash), report.md. Workspace root: receipt.json (submission record).
Total request artifacts <= 16 MiB (capture.png target < 4 MiB).

## 10. Deviation rule

If any frozen probe fails at build, the build FAILS; cameras may only be changed by
amending this preregistration BEFORE the retry, with the deviation recorded in
report.md. Predictions are never edited after evidence exists.

## 11. Amendment log

- v1 (sha256 f6f241444808733f41c107d2549497bff6adc7891c0b5e6ec9e6db52b5929b0a):
  original freeze before the first build. The first build rendered and PASSED
  the structural gate, but visual inspection showed two evidence-quality
  defects: (a) the overview framing was too loose (the body's long axis is
  nearly parallel to the view direction, so the subject occupied ~25% of the
  panel) and (b) 3D labels whose anchors sit within a few centimetres
  overlapped into unreadable text - a label-ambiguity falsifier risk. No
  evidence was submitted or declared from v1.
- v2 (sha256 of this file's v2 state recorded in report.md): overview eye
  offset (0.55, 0.42, -1.05) -> (0.32, 0.24, -0.60) (same target, FOV,
  clipping, resolution; the all-vertex in-frustum probe still asserts every
  vert stays inside with margin); labels drawn as anchored callouts with
  leader lines (section 5); diagnostic alphas raised for legibility (envelope
  ghost 80/255, bones 230/255). All other freezes (subject, views, layers,
  cameras 2/3, probes, deliverables) unchanged.
- v3: the v2 build's all-vertex frustum probe PASSED and the structural gate
  PASSED, but visual inspection showed the v2 overview looks down the body's
  long axis from the tail end: the near pelvis balloons ~2.3x relative to the
  skull and occludes the body (a clipped/occluded-subject legibility defect),
  so the panel reads as one blob. v3 moves the overview eye to
  center + (0.62, 0.30, 0.18): a side-perspective view (eye roughly along +X,
  slightly above, mildly head-side) under the same target, FOV, clipping and
  resolution; the body's 0.605 m long axis is then transverse to the view.
  The all-vertex in-frustum probe still gates the build. No other freeze
  changes.
