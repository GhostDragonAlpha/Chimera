# MAT2-F04 — source-bound qualification receipt: ground and trunk contact geometry, frozen cases

**Verdict: BUILT AND SELF-CONSISTENT.** The combined F02 terrain asset and F03 trunk asset were bound to the unmodified M06 shared contact path and exercised with frozen crossing, impact, seam and rest trajectories over FULL tick intervals: every CCD-on first contact is pre-overlap (worst penetration 0 m against the frozen 1e-4 bar), every support impulse is a real per-tick ledger record (worst residual 3.04e-17), the collision bodies are element-identical to the rendered assets (exact array equality; trunk radial gap 3.67e-07 m), all seven falsifier arms bite fail-first, each against its own passing clean control, and the contact-motion capture is structurally valid under the REGISTRY profile with a single gate-bound video artifact and committed stills. Visual acceptance itself belongs to the independent visual reviewer.

- card: MAT2-F04; planning id F04; attempt c4064f0e999c40b3a9b18892b034f83c; arrival arrival-a6cc16fce0954ee789086633f911e1a3; criteria sha256 4c0a901840d34736a3bcd4dee6a70e750b731a83ef4152a573b99e2dae6b7669; scope sha256 cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097; base revision 459ab80136c1491138dece91ebbbf62ab8349cb1 (branch-3 fast-forwarded to the sealed tip; F02/F03 merged).
- done_when (verbatim): "No unacceptable tunnelling, ghost support, interpenetration or visual/collision disagreement in frozen cases".
- discipline: PREREGISTRATION.md committed BEFORE implementation at d71c7d8a805f2d734b881ac2d15657fb4fe061bc; Amendments A1-A6 are separate commits (56de4e44875296ac0176395eab39420731e383f2, 6d116eaa62e4bc8061f43f39f37987b9ed40bb0f, 43fc9e3abd5ece19cc3e9512887eb92c54402b87, f5f26e8c19197f35542a159c2754d832c8806806, a35874d602f52bdf611bbc8eb97caa3dad529dc9, 11a9ecf42727e259595ed19156dde2dfb29fa0f1), all before the implementation commit and the first completed build. This report is GENERATED from evidence/checks.json and evidence/determinism.json — no observed value is hand-transcribed.

## 1. Reconcile-first (reused published bytes only)

Pins asserted by raw sha256 at every run (see `pins` in evidence/checks.json): F02's tied terrain asset + query surface + F01 render law, F03's trunk declaration/mesh, M06's byte-identical local_contact module and contact law. No physics constant is new: ground mu 0.9/0.65 thickness 0.002 (F02), trunk mu 0.6/0.6 thickness 0.0 solid (F03, friction remains the declared UNEVIDENCED-PLACEHOLDER, G04 debt), probes mass_tetra 0.12 kg mu 0.6/0.4 (F02/M06).

## 2. P0 — combined instantiation is REFUSED by the pinned law

Solving ground + trunk together is refused (`nonfinite_state`): the trunk base ring touches the ground plane at exactly 0.0 m, so the pinned law sees a both-pinned exact-contact pair (zero inverse-mass sum). F03's A3 heritage, now measured at the ground/trunk seam. Dynamic scenarios therefore instantiate exactly the static parts they touch (declared per scenario); asset identity (P1) is always measured on the FULL pinned bodies. No seam support is invented by composition.

## 3. P1/P2 — the collision assets ARE the rendered assets, through the shared path

- P1 ground: 9600 vertices, arrays_exact_equal=True, surface_id monkey_clearing_ground, contact extent 20 m == rendered half width 20 m.
- P1 trunk: 130 vertices, arrays_exact_equal=True, worst radial gap to the analytic cylinder 3.671e-07 m (declared tolerance 0.0002), worst outside-solid 3.671e-07 m, partition {"trunk_01.base_cap": 32, "trunk_01.lateral": 64, "trunk_01.top_cap": 32}.
- P2: 1103 contact records across all scenarios, every one a chimera.local_contact.v1 record of the byte-identical M06 module; worst per-tick ledger residual 3.04e-17 (bar 1e-12); declarations match contact_law.json: True.

## 4. P3/P4/P6 — no tunnelling, no interpenetration, contact geometry

| metric | measured | bar |
|---|---|---|
| episode-first contacts pre-overlap (kind ccd, gap > 0) | True | required |
| worst penetration over ALL ticks of all CCD-on runs | 0 m | <= 1e-4 m |
| worst ground contact point plane error | 0 m | <= 1e-9 m |
| worst trunk contact point radial error | 9.65e-16 m | <= 2e-4 m |
| seam impact altitude | 0.006972 m | in [0, 0.15] m |
| G_HIGH rest min corner separation | 0.00201 m | in [0.0015, 0.0025] m, stopped True |
| G_SEAM_REST (seam approach) rest | 0.00201 m | in [0.0015, 0.0025] m, trunk clearance 0.5937 m |
| TRUNK_TOP_REST displacement | 1e-05 m | <= 2e-3 m, cap contact True |

Per-scenario shape (from the receipt): G_HIGH 30 ticks, first contact 21, 261 records; G_SEAM_REST 40 ticks, first contact 19, 210 records; SEAM_HIGH 32 ticks, first contact 28, 32 records; TRUNK_TOP_REST 40 ticks, first contact 0, 440 records; T_CROSS 30 ticks, first contact 10, 160 records.

## 5. P5 — no ghost support

Every support impulse appears as a reciprocal local_contact.v1 record with the per-tick ledger identity enforced by the unmodified module (worst residual 3.04e-17 <= 1e-12); both rests land inside their frozen windows; the combined-instantiation refusal (P0) means composition invents no seam support. FB3/FB4 prove the detectors have teeth (below).

## 6. P7 — no visual/collision disagreement (pure ray/geometry)

Marker classify per view (markers never read pixels):

| marker | V1_clearing_overview | V2_seam_closeup | V3_opposite_oblique |
|---|---|---|
| marker_cap_rest | OCCLUDED | OFF_FRAME | OFF_FRAME |
| marker_ground_impact | VISIBLE_EXACT | OFF_FRAME | OFF_FRAME |
| marker_seam_impact | VISIBLE_EXACT | VISIBLE_EXACT | OCCLUDED |
| marker_seam_rest | OCCLUDED | OCCLUDED | OCCLUDED |
| marker_trunk_impact | VISIBLE_EXACT | VISIBLE_EXACT | OCCLUDED |
| marker_trunk_top | OCCLUDED | OFF_FRAME | OCCLUDED |
| subject_trunk | VISIBLE_EXACT | VISIBLE_EXACT | VISIBLE_EXACT |

- every view has >= 1 VISIBLE_EXACT trunk surface subject (`subject_trunk`, F03's frozen-probe pattern: the camera-facing facet at mid-facet azimuth, exactly on the facet chord).
- zero VISIBLE_BUT_MISMATCH anywhere; the seam impact marker is VISIBLE_EXACT in V2 with frame margin 0.3905 (required >= 0.03 per side).
- V3's opposite-side markers are OCCLUDED exactly when the analytic cylinder silhouette predicts it (depth ordering verified from the opposite side); OFF_FRAME markers are outside the V3 frustum by geometry.
- FB6 proves the decouple detector has teeth (below).

## 7. Falsifier proof (run FIRST; all seven bite fail-first)

| arm | bites | observed |
|---|---|---|
| FB1_ccd_off_ground_tunnels | True | `{"clean_control": {"first_contact": {"gap_m": 1.0000000000004797e-05, "jn_Ns": 0.6094920000000007, "jt_Ns": 0.0, "kind": "ccd", "matter_a": "clearing_ground_...` |
| FB2_ccd_off_trunk_tunnels | True | `{"clean_control": {"first_contact": {"gap_m": 1.0000000698951773e-05, "jn_Ns": 0.4800000000000035, "jt_Ns": 0.06474599999997362, "kind": "ccd", "matter_a": "...` |
| FB3_ghost_support_ground | True | `{"clean_control": {"guard": "f04_fb3_premature", "in_window_and_stopped": true, "min_corner_separation_m": 0.0020100000000000057, "run": "G_HIGH clean (FB1 c...` |
| FB4_ghost_support_trunk | True | `{"clean_control": {"guard": "f04_fb4_premature", "metric_scope": "P1 form: cap-centre vertices (i >= 128) excluded", "within_tolerance": true, "worst_vertex_...` |
| FB5_forced_interpenetration | True | `{"clean_control": {"guard": "f04_fb5_premature", "no_interpenetration": true, "run": "T_CROSS clean, CCD on (FB2 control run)", "worst_radial_clearance_m": 0...` |
| FB6_visual_collision_decouple | True | `{"clean_control": {"guard": "bit requires the clean control VISIBLE_EXACT", "outcome": "VISIBLE_EXACT", "run": "classify on the UNPERTURBED render, same ray ...` |
| FB7_off_frame_probe_subject | True | `{"clean_control": {"guard": "f04_fb7_premature", "outcome": "VISIBLE_EXACT", "run": "trunk_subject_probe in the same V2 view", "visible_exact": true}, "off_a...` |

Full observed records in evidence/bites.json inside checks.json (falsifier_bites). Every arm carries its own clean control and the bite is credited only when that control passes (F03 heritage premature guards, named f04_fb*_premature). A non-biting arm refuses the whole build (`f04_falsifier_did_not_bite`).

## 8. Capture (REGISTRY profile contact-motion, kind motion)

- profile read READ-ONLY from E:\ChimeraWork\monkey-coordination\agent_slots.sqlite3 (read_only); profile canonical sha256 94d7faecda34a87d0b4ca24103c957b6741af6f0ddf5201bf5edd8ecfedbe4ac; attempt state PR_SUBMITTED.
- task_id `F04` (SHORT form); run_id mat2-f04-contact-20260928-c4064f0e; tick_interval [0, 101] (Amendment A6: measured replay length).
- single gate-bound artifact: E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-F04\c4064f0e999c40b3a9b18892b034f83c\checkout\capture-evidence-20260928\mat2_f04_contact_motion.avi sha256 10a96b4f5a9e69ef085afc25881bf40948be66b3d183e03a25ed122a8d2deede (328 lossless FFV1 frames, ffprobe-verified: {"avg_frame_rate": "1/1", "codec_name": "ffv1", "height": 540, "nb_read_packets": "328", "width": 960}); rows bind state_binding kind=trace to evidence/contact_trace.json (sha256 397103e43af9b95ca1e03db247922a18e21829cea4509c61ec1986034639898a).
- committed stills (hash-listed supplementary, one per row at the impact tick): V1/clearing_overview_clean = 9db2c288d5697392...; V1/clearing_overview_diagnostic = 67b4ac4985f209e9...; V2/seam_closeup_clean = bce13076af34672b...; V2/seam_closeup_diagnostic = 1da035fee2120bbd...; V3/opposite_oblique_clean = 0571793dde844c70...; V3/opposite_oblique_diagnostic = 438f621c2d0f273d....
- stills/video row order: each committed still is pixel-identical to its decoded video frame under the identity transform ONLY (the capture-gate test evaluates explicit identity/vflip/hflip transforms and requires identity to match with zero differing pixels -- the video plays the bound camera convention, no flip).
- visual_capture.validate_manifest: structurally_valid=True (CAMERA_METADATA_STRUCTURE_ONLY, profile_id contact-motion, view_count 6, capture_kind video); visual_gate.verify: structurally_valid=True. visual_acceptance=False BY DESIGN — independent visual review remains mandatory.
- honest visual note: the V1 overview renders the trunk at sub-2-px scale (F03's own disclosure); the visually resolvable trunk, probe arrest and the three diagnostic layers (render/collision wireframes, probe trajectory polyline, cyan contact normals + yellow tick-ID markers) are verified in the V2 seam close-up frames; V3 carries the opposite-side depth check (the trunk partially occludes the far-side probe).

## 9. Determinism (P8)

Two full builds produced byte-identical artifacts: 12 evidence artifacts + the video, identical=True; video sha256 10a96b4f5a9e69ef085afc25881bf40948be66b3d183e03a25ed122a8d2deede. No RNG, no wall-clock anywhere in the build. (FFV1 is encoded in a deterministic AVI container; MKV measured nondeterministic and was rejected.)

## 10. Honest boundaries

- the pinned M06 law refuses a full ground+trunk co-instantiation at the seam (P0): the seam crossing is a declared phased composition (ballistic approach -> trunk phase, handover tick 28); a static seam solve (probe supported by the ground WHILE touching the trunk) is NOT demonstrated and is recorded as an unresolved upstream component for the integrator.
- SEAM_HIGH's trunk phase runs without the ground body; the post-arrest unsupported sink inside the frozen tail is measured PER PHASE (never by scanning heterogeneous states): phase-B min ground clearance 0.0055 m (phase-B min radial clearance to the trunk 0.06998 m; phase-A min ground clearance 0.01043 m) and disclosed as a composition artifact, excluded from the interpenetration bar by the declared instantiation scope.
- CPU-only (stdlib + ffmpeg encode); no engine run, no native change, no GPU, no training, no runtime or playable-build acceptance.
- trunk friction 0.6/0.6 is F03's declared UNEVIDENCED-PLACEHOLDER (acquisition is G04's).
- structural capture validity only: visual acceptance belongs to the independent visual reviewer.

## 11. Exact commands (from this directory, Python 3.14, CPU only)

    python -B implementation.py bites    # 7/7 fail-first, each with a passing clean control
    python -B implementation.py build    # receipt + frames + video
    python -B implementation.py verify   # P8 double-run determinism
    python -B make_report.py             # this file, from receipts
    python -B lint_report_numbers.py --selftest
                                         # report numbers traceable
    python -B -m unittest test_implementation -v
