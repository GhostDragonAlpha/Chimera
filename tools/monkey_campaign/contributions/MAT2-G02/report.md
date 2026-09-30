# MAT2-G02 report - Qualify finite-area anatomical attachments

Attempt 983a9a8b1be54457a6aa516319290aa1, agent zcode-glm-mat2-g02-a1, criteria sha256 03ee207b7b2c701ff189bf1ee9133ada87eea7a1bd760fe4cb24525fcc5e4c45. Isolated attempt-workspace checkout of E:/PythonChimera; candidate lineage branch codex/monkey-mat2-g02-983a9a8b1b (unsquashed in the attempt workspace); the r3 publication is ONE fresh trailered commit on the sealed line tip 66f193c4 (= origin/astra/gait-capture after the merged MAT2-M12 and agent-memory-backup PRs; the r1/r2 publications sat on the earlier tip f6cbf7a9). Composed against CARD_STARTER.md v3; house standards IMPLEMENTER_CHECKLIST.md (G1-G9) and TOOLKIT.md (P1-P9) cited at the candidate commit.

## done_when clause map (executed on the exact candidate revision)

| clause | execution | result |
| --- | --- | --- |
| Actual patch geometry ... meet declared physical requirements | T1/T2/T4/T5 exact probes + X1 closed-form agreement (worst rel 0.0) | PASS |
| Finite-area attachment forces and moments enter both connected material states | T3 reciprocity (bitwise force pairs; worst summed torque 0.0 N*m against the frozen 1e-15 bound (receipt element_probes T3 block); interface force sums bitwise zero; per-body received moments recorded in the trace) | PASS |
| Physical bond/removal semantics match the limb experiment | T6 release gate: bitwise post-release zero, E_diss_release == U(233) (0.002427747544017641 J), M01 documents bond 1 -> 0 with contact persisting, separation demonstrated (0.09958591295534305 m > gap(234) 0.09269256284395062 m), re-contact at tick 275 with no patch | PASS |

## declared physical requirements (the C17 law)

- The fixture constants are DECLARED placeholders (provenance class declared_placeholder, never biological): areal densities derived from the sealed MAT2-M05 carrier (kA_t = 60/0.0175, kA_s = 40/0.0175, kA_theta = 0.8/0.0175 N units per the prereg laws 3-4); patch quad 20 mm x 10 mm with UNEQUAL triangles (A1 = 1.0e-4 m^2, A2 = 6.5e-5 m^2) so area scaling is falsifiable; distribution weights w1 = 0.6060606060606061, w2 = 0.3939393939393939; owner-body-local frames carried verbatim with authored port ids iface:fixture-patch-p1/p2.
- The BIOLOGICAL attachment ports (26 attachment_interface connections carried from the sealed A09 package, c17_status carried_open) close EXPLICITLY-UNRESOLVED: no measured or separately-authorized source exists; the sealed A07 gate requires authorization BEFORE any fitting experiment and none is recorded; no synthetic lambda_min appears anywhere in this card (the term does not occur in any artifact).
- Adjacent debt, NOT this card's scope: the G04 friction study records no lawful measured friction pin exists (mu_s 0.6 / mu_k 0.4 remain NAMED placeholders; the elementwise_min pair rule is two-sided). This fixture uses the sealed M05 frictionless normal-penalty contact and introduces no friction constant.

## X-gates

- X1 element-vs-oracle agreement: worst relative diff 0.0 (window 1e-15); probe series T1/T2/T3/T4/T5/T7/T9 all pass: True.
- X2 scoped determinism: trace byte-identical (True); receipt delta scoped to ['p_gates_declared']; pass: True.
- Dynamic fixture (Amendment A2 schedule, 355 ticks): gap(233) = 0.09264418957867045 m in [0.055, 0.13]; U(233) = 0.002427747544017641 J in [0.0009, 0.0048]; worst ledger residual 1.890166565551713e-07 J (frozen bound); min penetration -0.009911115805560491 m within [-0.015, 0.0]; T8_pass: True.

## falsifier proof (each arm: clean control FIRST, named guard, discriminator)

- FB1_stale_tension_survives_release: clean control 0.0 (within tolerance: True); tampered 0.052215428571428565; bites: True; discriminating: True.
- FB2_area_independent_force: clean control 1.5384615384615385 (within tolerance: True); tampered 1.0; bites: True; discriminating: True.
- FB3_one_sided_state_entry: clean control 0.0 (within tolerance: True); tampered 0.02999982857142857; bites: True; discriminating: True.
- FB4_unaccounted_release_energy: clean control True (within tolerance: True); tampered ledger_residual_exceeded; bites: True; discriminating: True.
- FB5_auto_bond_on_proximity: clean control 0 (within tolerance: True); tampered 2; bites: True; discriminating: True.
- F_all_green: True (vacuous guard selftest: True).

## capture identity (attachment-fixture/motion profile)

- FFV1 level 3 g 1 with -fflags +bitexact (mkv); sha256 49d2023ccd78ae26d3c87ebf39041039629b4e3b9a42a77d16bbe8fd1eaa948d; ffmpeg: ffmpeg version 8.1.1-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers.
- validate_manifest (tools/monkey_campaign/visual_capture.py, registry profile read read-only): structurally_valid True, 6 view rows (3 registry views x diagnostic+clean pairs); subject sha256 e594336599cf0a78b12660f3f305417256230276d85795f1ba6a3cd70599016f; state binding = trace 259b731d40191fcfb968675e67c91f816dc4bd3ed0bad699125954fce753960b.
- Full registry camera record on every row (frame_id, coordinate_unit, position, orientation_convention_and_values, target, distance_to_target, projection, vertical_fov, near_far_planes, aspect_ratio, viewport_resolution, sample mode/sequence, visibility, labels, occlusion, state interval); fixed bookmarks; clean pairs share the exact camera and the exact physical state; state hash preserved across view toggles: True.
- Pixel-presence grounding (round-1 fix): draw_viewport() is called for all six viewports; every visibility claim is measured per frame in capture_pixel_presence.json (min tile non-bg pixels 2777, footer trace-inset line min 1264 px, reprojection-oracle max delta 0.985 px); check_capture_pixels.py re-measures the committed frames against the manifest (GREEN) and REDs on both preserved pre-fix captures (controls, measured on this revision: the pre-round-1 capture 420 violations, five of six tiles at zero non-background pixels; the r2 capture 35 violations of which the caption-only inset fails the inset signature gates - the r2 blocker can no longer pass).
- Declared oblique picture-in-picture inset (pair-2:diagnostic, round-2 fix): rendered at its declared 288x76 resolution by the SAME draw_viewport() with the target-surface dimensions bound as parameters (the r2 revision projected with module viewport constants, so every inset geometry pixel landed outside the 288x76 surface and PIL clipped it to a caption-only rect); the inset camera is in-frame-gated and consistency-oracled in the INSET coordinate space; exact-color geometry signatures measured INSIDE the declared rect [344, 6, 632, 82] (minima over the 7 frames: body_a 110, body_b 436, patch 4, seam 37, stand 92; caption chip min 44 px, inset non-bg min 1082 px); tile stats are measured POST-paste so the manifest describes the committed pixels; the paste occludes at most 304 primary geometry px per frame (measured and disclosed - the inset hides no subject POINT, verified by the tile-space hide gate, and the r2 caption-only state measured 0 geometry px at this rect).
- Honest limit: validate_manifest is structural only; independent image/physics review (the Sergeant gate) remains mandatory and is owned by the Lieutenant.

## regression

- Upstream suite (MAT2-M05 test_interface_exchange.py, pinned) re-run unmodified on this revision: exit 0, green: True.

## amendments and repairs (full disclosure)

- Amendment A1 (a39a946e, pre-implementation): T2 per-triangle tension literals repaired (three decades; patch total, ratio and windows unchanged). No experiment had run.
- Amendment A2 (951c963e, pre-experiment): damping-ratio formula corrected (zeta = c_v/(2*m*omega_t); the declared c_v = 2.0 overdamped the soft patch at zeta 9.4017 -> c_v = 0.02, zeta 0.0940); schedule amended to a quasi-static squeeze ramp + settle + bind at rest + release at the derived oscillation peak; T8 windows re-derived from the corrected closed form; ledger bookkeeping statement added (midpoint displacement identity, damping booked as Q, elastic contact in W_contact, E_diss_release in Q at the release tick). Element laws 1-9 untouched.
- Reference repair (8cbcd91b, recorded with the first receipts): the three attempt commits were rewritten on the UNPUBLISHED sole-owner attempt branch to separate the Agent: trailer into a proper trailer block; TREES UNCHANGED; identities recorded in PREREGISTRATION.md.
- Receipt-index repair (this revision): the T8 receipt block indexed trace rows by tick instead of by row index (rows[i] holds tick i+1); the bound M01 document is now captured while still bound; the released document is emitted after the release tick executes.
- Round-1 corrections (review sgt-pr281-r1, CHANGES_REQUIRED): the published capture had draw_viewport() defined with ZERO call sites - five of six viewports were uniform background while the manifest claimed all subjects observed. Fixed: draw_viewport() called for all six tiles (diagnostic rows with overlays and port labels; clean rows geometry-only); cameras re-derived with an in-frame gate (every declared subject point of the camera framing scope must project inside the viewport, checked per frame); the camera record made mathematically true (right-handed camera frame +X right/+Y up/-Z forward; quaternion = camera-to-frame rotation; an independent reprojection oracle reproduces drawn anchors from the serialized record alone); visibility rows are MEASURED (capture_pixel_presence.json, per-frame exact-color evidence) and make_capture refuses the build if any required subject lacks pixels; the sheet gained a declared footer band so the trace inset no longer overlaps a clean viewport. The physics chain is UNCHANGED: all receipts regenerate byte-identically (trace 259b731d..., experiment/determinism/falsifier/regression receipts identical; only the declared live-field experiment_profile.json differs, by declaration).
- Round-2 corrections (review sgt-pr281-r2, CHANGES_REQUIRED on ONE blocker): the declared oblique picture-in-picture inset (288x76) contained ZERO geometry pixels - 354 non-bg px of caption text only - because draw_viewport() projected with the MODULE CONSTANTS VP_W/VP_H regardless of the target surface, every inset geometry pixel landed outside the 288x76 image and PIL clipped it silently, while assert_in_frame(secondary) checked the 640x240 tile space and the pip content gate (nonbg > 100) was satisfied by the caption text. Fixed: draw_viewport() (and every projection-space gate: assert_in_frame, draw_labels, ground_subjects) now takes the TARGET surface dimensions as parameters - the inset renders at its declared 288x76 with its own oblique camera; the secondary in-frame gate runs in the inset coordinate space; the inset content gate is EXACT-COLOR (every declared geometry signature must have > 0 measured px inside the declared rect - caption text alone cannot pass; the caption carries an exact-color chip); check_capture_pixels.py gained the same inset gates plus an inset-space seam-centroid consistency bound, and its clean-row styling list gained PATCH_DIAGONAL and SEAM_DIAG (review R2N2); tiles are measured POST-paste so manifest pixel counts describe the committed pixels (review R2N1), with the pre-paste occlusion of primary geometry under the inset measured and disclosed per frame (review R2O1). The physics chain is UNCHANGED: all receipts regenerate byte-identically (trace 259b731d...).
- Refusals disclosure (review finding F6): the submit-time coordination record (LIEUTENANT_RESUME_v2.json, 2026-09-30 15:4x CDT entry) states "4 named refusals disclosed" for development of this attempt. No durable artifact of this attempt records their names or triggers (verified by the r1 reviewer across report.md, PREREGISTRATION.md, KNOWN_SKIPS.md, commit messages, the PR body and the attempt workspace; re-verified by this corrections pass). Their content is therefore recorded as UNRECOVERABLE - no names are invented. Durable process record: development-time refusals must be written into report.md or KNOWN_SKIPS.md when they happen, not left in a coordination log.

## file identities at freeze

- PREREGISTRATION.md: fa30fe5c472c32266b5b1ea121d0c4d86e5e7b649572c42ef470a8df3532435c
- attachment_patch.py: 63a31e9c3a83d2ae94939a6e8bcf99fe14dc8891224abfe9a1b9eac2cb353ff8
- run_experiments.py: 162cd556004b62e57188dd400ce50346b0ebe36310cc901ffaab6ce75b8d0a4f
- test_attachment_fixture.py: 130ebc84dd730d727e670b5a918f9dd9d5944d05880a9f0d8f2325e20f582d0b
- lint_report_numbers.py: 83ead5c577fbf0c083811c8efea971b7a9dbd0e2ca283a027fcfc65406643d80
- render_run.py: 8f5d35e7156a445f58a9d9dabcdab27143966cd55de0eec656d365d153e58943
- make_capture.py: e4d4036b8b51d1a501429d8176ab2e0f74723070195d30926e4a03e7c39c6057
- make_report.py: 9e83104b92a48fc30e7b3609fdeee048380c85f0dc0b697651f8cab36d756b6e
- check_capture_pixels.py: 6ae3dc9a4c6d44500eb36af389a40166503dd3b368f6cce8651456e571d82727
- KNOWN_SKIPS.md: 6cae2da6477ffd9ea0c82d2ea831b99d78352993a2e21496fe893f96cda6c2ce
- .gitattributes: 705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da
- experiment_receipt.json: e594336599cf0a78b12660f3f305417256230276d85795f1ba6a3cd70599016f
- experiment_trace.json: 259b731d40191fcfb968675e67c91f816dc4bd3ed0bad699125954fce753960b
- experiment_receipt_rerun2.json: cbf5618444b07c46b5d2cc70965ae2af3f1c1047f53676b35c8ec48217234409
- experiment_trace_rerun2.json: 259b731d40191fcfb968675e67c91f816dc4bd3ed0bad699125954fce753960b
- determinism_receipt.json: 5f987e16b78cc9f6123ef142ffb6efd51632a3c761eb90e70ca2a7a5018b9d13
- falsifier_receipt.json: 006dce6a8109a293ebf98c60981baaee43b31e820e37007652b22cefaf5d32e9
- regression_receipt.json: 25280220142e18a11ac8e5213dee4c7e8414d613c26fce6df8a00940bb775bea
- capture_manifest.json: f3c1d2a5a569e5afb33fe24c21d4bad62c9287db1bd8cd1d5da9004e4091c6d1
- capture_context.json: 908e4f814033c689775ae43ca2e8da303070dcb853b94d34de7c9deee31fa771
- capture_validation_receipt.json: 9f824524e20e7ec49112fd69211c4d99808c21ab91c3676b0ba2df634b2a56dd
- capture_pixel_presence.json: 7110aa9a1f6d760f8be04a53c8ca5ff27717067d1ecf9212505a7a04819babf9

## honest limits

- Offline CPU experiment executable over pinned inputs; no GPU submission (the scope is a 356-tick two-body fixture; prereg law 12).
- experiment_profile.json is the single DECLARED live-field file (wall-clock x1_wall_seconds); it is excluded from byte identity by declaration and from the pinned file list above; every other artifact regenerates byte-identically.
- The fixture constants are declared placeholders with the derivation recorded; they do NOT qualify the biological ports; the biological C17 debt remains explicitly-unresolved pending a separately authorized measurement (A07 gate).
- No fitting experiment was run; no friction constant was introduced; no lambda_min appears in any artifact.
