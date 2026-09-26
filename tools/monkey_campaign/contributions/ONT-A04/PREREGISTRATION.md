# PREREGISTRATION — ONT-A04 hand assembly identity and palm orientation (anatomy profile)

Card `ONT-A04` (planning A04, verification profile `anatomy`, kind **visible_static**),
attempt `86b87bfe23b14059ac8ed516104340bf`, agent
`arrival-32436e70ed1e4866a25a29940db1789c`, criteria
`bf8583ae76c4930f726c4c71861ab9219cdac65eb3913cb29ab6131671505570`, scope
`01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`,
definition `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`.
Written and frozen **before** any probe of this attempt ran. Every predicted number
below is taken from the prior verified receipts listed under RECONCILE (the
reconcile phase read them; nothing was re-measured before this freeze). The probe
re-measures each one from pinned bytes and records ANY mismatch as a FIRED
deviation in `evidence/numerical_receipt.json.prediction_deviations` — never smoothed.

## DONE_WHEN being qualified (the ONLY clause)

"Source and target assembly correspondence is evidenced, including palm sign and
geometry coverage" — calculation contracts C01 ("One unambiguous frame chain and
independently checked transforms"; verification: round-trip, handedness, landmark
and independent-orientation checks) and C16 (identity leg only: "Reachable grasp
placements with valid identities" — the reach/ROM leg is downstream grasp-skill
scope and is NOT claimed here). Dependency ONT-P02: DONE (merged winner
`8c7ed8c2`, review/ONT-P02; its lineage map governs — see RECONCILE).

## RECONCILE (records reused, not duplicated; read-only git pins, drifted worktree)

- **ONT-P02 (merged, qualified):** `tools/monkey_campaign/contributions/ONT-P02/`
  `MONKEY_LINEAGE_MAP.md` + `monkey_lineage_map.json` @ `8c7ed8c2`. Governing
  relations: Chimanoid MSK model `SOURCE_OF` forearm/paddle assets; forearm/paddle
  assets `KEPT_SEPARATE` from runtime/training bodies (analysis-only, counted mass
  0.0); myo_sim vendor `KEPT_SEPARATE` (grab/foot science lanes, Apache-2.0).
- **HAND_SOURCE_EVIDENCE (handsrc, `70c9ff41` on `forearm-package-20260924`,
  on-disk `E:/PythonChimera/forearm_package/audits/HAND_SOURCE_EVIDENCE/receipts/`):
  SOURCE prong CLOSED** — 27 vendor hand STLs identity-tested at the R2-A3 anchor
  class (4 anchor sites 0.06–0.80 mm; extents 155.285 vs 155.29 mm; rays
  66.99/96.42/100.17/89.10/78.61 vs 67.0/96.4/100.2/89.1/78.6 mm), frozen
  pisiform-signed palm-plate palm normal
  `n_palm = (+0.128427, −0.168691, −0.977266)` (hand_r local, 12.24° from −ẑ),
  compartment split 5/5 clean both hands, exact L/R XML z-mirror. Its stricter
  frozen 19-link rule FIRED (preserved, diagnosed as link-construction artifact).
  Receipts extracted byte-exact from the git pin into this attempt's
  `reference/` (hashes asserted at probe import).
- **HAND_TARGET_VIEWS (handtgt, `57beb8b2`): TARGET face-identification instrument
  DELIVERED, human verdict NOT yet recorded.** Face-on ±T_R pair (A = +T_R-side
  broad face, B = −T_R-side) of the hash-pinned birth-mesh right distal band;
  `LABELING_CARD.md` explicitly reserves the A/B answer to the HUMAN terminal
  ("a bare model answer is another claim, not a verdict"). **No A/B answer exists
  anywhere in the record** (searched: forearm_package, docs, agent_logs, git log).
- **C2_hand_evidence + B1_source_anatomy (`target_paddle_measures.txt`,
  `source_hand_measures.txt`, `target_hand_region_v3.txt`):** source hand length
  155.29 mm, palm 60.89 × 20.19 mm; target band 111.3/111.4 mm along elbow→wrist,
  far-end 47.1 × 18.1 mm, single connected component (8-mm voxels [165]),
  paddle:forearm 1.7184 vs source hand:forearm 0.4928/0.5078.
- **I6 ANATOMICAL_DECISION_TABLE + architect addendum:** hand scale candidates
  H-LEN (s=0.716) / H-ASP UNRESOLVED (blocked on same-assembly evidence), H-BODY
  REJECTED as circular; hand roll sign "one visual identification away";
  production mapping NOT authorized. The sealed A04 observation records exactly
  this: "H-LEN/H-ASP unresolved; H-BODY circular; orientation alone does not set scale".

**Missing task-owned work this card adds (and the only work built):**
(i) ONE machine-readable correspondence measurement binding source and target
into an unambiguous frame chain with independently checked transforms (C01);
(ii) an independent re-derivation of the source palm SIGN from pinned bytes
(previously derived once by another author);
(iii) an explicit geometry-COVERAGE inventory (which source components have target
geometry coverage; which are absent) with the scale alternatives recorded as
UNRESOLVED (never decided here);
(iv) the anatomy-profile camera-pinned capture of the pinned source and fitted
target geometry (previously only two separate single-prong figure sets existed;
no capture manifest, no paired clean/diagnostic views, no unified correspondence view).

## SUBJECT (identity pinned before execution)

The pinned INPUT SET, hashed into `evidence/state_snapshot.json` (the capture
`state_binding` target and `subject_sha256`):

| pin | identity | expected sha256 |
|---|---|---|
| source XML | git blob `forearm-package-20260924:forearm_package/baseline_snapshot/source_xml/chimanoid.xml` extracted read-only to `reference/chimanoid.xml` | `7caa32c6e31e319876ea21625b662c5c00e736038f542b38ce6b0cb81aadc8a5` |
| vendor STLs | `E:/PythonChimera/vendor/myo_sim/meshes/<bone>.stl`, 27 files, per-bone hashes asserted against `reference/s1_inventory.json` pins | (27 × per-bone) |
| target mesh | `E:/PythonChimera/Saved/meshes/monkey_birth.bin` (verified == branch blob) | `550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c` |
| target rig | `E:/PythonChimera/Saved/meshes/monkey_joints.bin` (verified == branch blob) | `74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662` |
| prior receipts | the 12 files in `reference/` | asserted at probe import |

`.tmp/chimanoid.xml` on the drifted worktree is byte-DIFFERENT (675e00d0…) from the
pinned blob and is NOT used. All reads elsewhere are read-only; ALL writes stay in
this attempt workspace.

## FROZEN NUMERICAL PROBE (a04_correspondence_probe.py; CPU-only, stdlib+numpy)

Checks (each: expected from the receipts above, measured from pinned bytes,
deviation recorded FIRED if outside tolerance):

- **C1 pins:** XML blob hash `7caa32c6…`; 27 right + 27 left mesh geoms; 27/27
  vendor `<bone>.stl` present with per-bone sha256 == s1 pins; all mesh-asset
  scales exactly `[1,1,1]`.
- **C2 frame chain (C01):** hand_r world origin == `(-0.0731, 0.532647, 0.202699)`
  m (R2-A4 pin, tol 1e-9 reproduced, tol 5e-7 recorded); every body quat in the
  chain identity; rigid law `x_world = R x_local + t` with R = I round-trips every
  anchor and site; det(R) = +1 (right-handed); assembled extents ==
  anchor-derived record: distal 3distph 155.285 vs 155.29 mm, rays
  66.99/96.42/100.17/89.10/78.61 vs 67.0/96.4/100.2/89.1/78.6 mm.
- **C3 palm SIGN re-derivation (frozen method, independent re-implementation):
  pisiform-signed palm-plate plane** — plate = 12 bones (pisiform, lunate,
  scaphoid, triquetrum, hamate, capitate, trapezoid, trapezium, 2mc, 3mc, 4mc,
  5mc) at XML anchors, identity scale, zero phalanges, zero thumb, zero sites;
  unsigned normal = smallest-eigenvalue eigenvector of the union vertex covariance
  (sign-oriented for display); sign rule: palm side = the side the pisiform
  protrudes toward. Predicted: `n_hat ≈ (−0.128427, +0.168691, +0.977266)`;
  pisiform dot ≈ −6.9659 mm; **n_palm ≈ (+0.128427, −0.168691, −0.977266)**;
  angle to −ẑ ≈ 12.2404°; plate rms ≈ 5.8819 mm. Acceptance split on the frozen
  site table (plane through c_all, palm positive): FCR-P3 ≈ +5.2869, FCU-P4 ≈
  +4.3611, ECRL-P4 ≈ −3.2637, ECRB-P4 ≈ −9.0956, ECU-P6 ≈ −2.6272 mm — 5/5 clean.
  Left mirror exactness re-checked from the XML (z-mirror of anchors, max |Δ| = 0).
- **C4 anchor-class landmarks:** ECRL-P4→2mc, ECRB-P4→3mc, FCR-P3→2mc at
  0.06–0.81 mm (anchor class, tol 3.5 mm bar); FCU-P4→pisiform ≈ 16.83 mm recorded
  as COURSE class (enumerated, not identity-decisive); CMC surface gaps ≈ 0.00 mm
  (5 pairs); the stricter 19-link rule is NOT the governing bar (its fired state is
  preserved, re-recorded if it fires again).
- **C5 target geometry:** birth+joints pins; `MESH_UNIT_TO_M = 0.065` (authored);
  wrist_R/elbow_R == recorded (±1e-4) `(-0.144995, 0.261482, -0.005956)` /
  `(-0.1155, 0.3191, -0.0061)`; band extents 111.3 mm (r<25 mm) / 111.4 mm
  (r<40 mm); far-end (80–115 mm, r<40 mm) transverse extents 47.1 × 18.1 mm;
  single connected component (8-mm voxels, one component) in region axial>30 mm
  r<35 mm; L/R wrists exact x-mirrors.
- **C6 correspondence + coverage inventory (C16 identity leg):** identity table
  complete = 27 source bone IDs + 5 source port IDs + 1 target band region ID +
  2 target anchors; coverage: carpals+metacarpals (13 bones) covered by the target
  band region; **14 phalanges + thumb ray have ZERO target geometry coverage**
  (single-component target band, no digit structure — sampling grooves refuted by
  C2); scale alternatives RECORDED, NOT DECIDED: H-LEN s=0.716 (mass 0.16844 kg
  under |det S| policy), H-ASP (0.716, 0.77, 0.90), H-BODY s=0.2217 REJECTED
  circular; source:target proportion mismatch 3.4–3.5× recorded as the same-assembly
  blocker. "Orientation alone does not set scale" is a FROZEN refusal: no scale
  number is promoted from any orientation result.
- **C7 palm-sign statement:** SOURCE sign CLOSED when C3 is green;
  TARGET sign = instrument exists (±T_R face pair), **human verdict MISSING →
  named unresolved item**, FALSIFIER: this card FAILS if it anywhere claims the
  target palm face is decided.

## FROZEN VISUAL CAPTURE (capture_build.py; CPU-only matplotlib Agg + numpy z-buffer)

One root capture `evidence/capture_a04.png` (contact sheet, ~1600 × ~2200 px,
deterministic byte-identical on rerun), six panels = 3 profile view_ids ×
(diagnostic, clean). `chimera.visual_capture_manifest.v1` manifest validated
in-process against the exact card profile via the campaign's
`visual_capture.validate_manifest` + `visual_gate`. tick_interval `[0, 0]`;
every camera `fixed_bookmark`, orthographic, coordinate_unit m, sample tick 0.

| view_id | panels | diagnostic overlays (layers) |
|---|---|---|
| `whole-creature overview` | LEFT: source 27-bone assembly in full (all rays), 3/4 view. RIGHT: target distal band in full with elbow→wrist axis + stations. | bones, tendon paths, attachment sites, frame axes, stable 3D labels, outer envelope |
| `local attachment close-up` | LEFT: source carpal row + anchor-class port sites, anchor distances annotated, pisiform + n_palm arrow. RIGHT: target wrist_R anchor + 55 mm band boundary + region box. | same six |
| `orthogonal side and oblique views` | LEFT pair: source orthogonal dorsal side + oblique palm view (n_palm vs −ẑ 12.24°). RIGHT pair: target ±T_R opposed faces (A/B instrument) + orthogonal side view. | same six |

Honest labels on the sheet itself: source/target tagged on every panel; A/B
letters carry "labels FACES, not anatomy — palm verdict NOT claimed"; the overview
is labeled "whole OWNED subject (hand assemblies) — runtime creature body is
P02-kept-separate, not this card's subject".

- Clean panels: same camera, same state, shaded geometry ONLY, depth-tested,
  zero overlays/labels (validator: `clean_view_contains_diagnostics` must hold).
- Camera fields (all 16 required): frame_id (`chimanoid_world_m` /
  `monkey_birth_world_m`), coordinate_unit m, handedness right, orientation
  convention `quaternion_wxyz_camera_to_frame` (forward −Z, up +Y), near/far
  planes, viewport_resolution, aspect_ratio == resolution ratio, projection
  orthographic + `orthographic_span`, sample_mode `fixed_bookmark`, samples with
  position/target/distance_to_target (== measured, rel 1e-9)/unit quaternion,
  camera_motion_or_bookmark_sequence ("fixed_bookmark, single sample"),
  visibility layers + label_ids, occlusion_mode depth_tested,
  state_or_tick_interval `[0,0]`.
- `required_subject_ids` per view: the subjects the falsifier needs visible
  (triads, wrist anchor, band, labeled bones/sites); `missing_subject_ids` = []
  asserted from the render masks (a required subject whose mask is empty FIRES).
- View toggles preserve the state hash: both modes of a pair share one
  `state_binding` (sha256 of `evidence/state_snapshot.json`) — physical state
  identical by construction; the falsifier "view toggles must preserve the
  physical state hash" is enforced by the validator's pair equality rules.

## FALSIFIERS (frozen; any firing is recorded, never retried into passing)

- **F-A (identity):** any vendor STL hash or XML pin mismatch, any extent-record
  reproduction failure, or any site leaving its anchor class → identity leg FAILS.
- **F-B (palm sign):** re-derived n_palm disagreeing with the receipt beyond
  1e-6 per component, OR the compartment split not 5/5 clean → source sign FAILS.
- **F-C (frame chain):** round-trip residual > 1e-12 m on any anchor/site, wrong
  hand_r origin, non-identity chain quat, or det(R) ≠ +1 → C01 FAILS.
- **F-D (coverage honesty):** any claim of target digit coverage, any decided
  scale number, or any target-palm-verdict claim → card FAILS (these are the
  named unresolved items).
- **F-E (capture):** manifest structurally invalid, clean panel containing any
  diagnostic pixel, required subject with empty visibility mask, non-byte-identical
  rebuild, or camera distance/resolution/aspect inconsistency → capture FAILS.

## SCOPE DISCIPLINE

No anatomy invented; no constant authored (MESH_UNIT_TO_M consumed as the
authored value, cited); no production mapping stated; no scale decided; no
utility/grasp-reach quantity; no runtime/native behavior claimed (the profile's
applicability boundary: static source+target inspection only; checkpoint-free);
no writes outside this attempt workspace; CPU-only (no GPU/OpenGL/Vulkan/CUDA);
tests run `python -B`, CPU only.
