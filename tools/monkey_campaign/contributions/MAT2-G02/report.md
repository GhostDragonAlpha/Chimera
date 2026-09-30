# MAT2-G02 report - Qualify finite-area anatomical attachments

Attempt 983a9a8b1be54457a6aa516319290aa1, agent zcode-glm-mat2-g02-a1, criteria sha256 03ee207b7b2c701ff189bf1ee9133ada87eea7a1bd760fe4cb24525fcc5e4c45. Isolated attempt-workspace checkout of E:/PythonChimera; candidate branch codex/monkey-mat2-g02-983a9a8b1b on the sealed line tip f6cbf7a9 (= origin/astra/gait-capture). Composed against CARD_STARTER.md v2; house standards IMPLEMENTER_CHECKLIST.md (G1-G9) and TOOLKIT.md (P1-P9) cited at the candidate commit.

## done_when clause map (executed on the exact candidate revision)

| clause | execution | result |
| --- | --- | --- |
| Actual patch geometry ... meet declared physical requirements | T1/T2/T4/T5 exact probes + X1 closed-form agreement (worst rel 0.0) | PASS |
| Finite-area attachment forces and moments enter both connected material states | T3 reciprocity (bitwise force pairs, summed torque 1.890166565551713e-07 N*m ledger class; interface force sums bitwise zero; per-body received moments recorded in the trace) | PASS |
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

- FFV1 level 3 g 1 with -fflags +bitexact (mkv); sha256 d20a9174cbf143a17c8b958a3ede4d48a2d011d3398368245b3882637ea677e6; ffmpeg: ffmpeg version 8.1.1-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers.
- validate_manifest (tools/monkey_campaign/visual_capture.py, registry profile read read-only): structurally_valid True, 6 view rows (3 registry views x diagnostic+clean pairs); subject sha256 e594336599cf0a78b12660f3f305417256230276d85795f1ba6a3cd70599016f; state binding = trace 259b731d40191fcfb968675e67c91f816dc4bd3ed0bad699125954fce753960b.
- Full registry camera record on every row (frame_id, coordinate_unit, position, orientation_convention_and_values, target, distance_to_target, projection, vertical_fov, near_far_planes, aspect_ratio, viewport_resolution, sample mode/sequence, visibility, labels, occlusion, state interval); fixed bookmarks; clean pairs share the exact camera and the exact physical state; state hash preserved across view toggles: True.
- Honest limit: validate_manifest is structural only; independent image/physics review (the Sergeant gate) remains mandatory and is owned by the Lieutenant.

## regression

- Upstream suite (MAT2-M05 test_interface_exchange.py, pinned) re-run unmodified on this revision: exit 0, green: True.

## amendments and repairs (full disclosure)

- Amendment A1 (a39a946e, pre-implementation): T2 per-triangle tension literals repaired (three decades; patch total, ratio and windows unchanged). No experiment had run.
- Amendment A2 (951c963e, pre-experiment): damping-ratio formula corrected (zeta = c_v/(2*m*omega_t); the declared c_v = 2.0 overdamped the soft patch at zeta 9.4017 -> c_v = 0.02, zeta 0.0940); schedule amended to a quasi-static squeeze ramp + settle + bind at rest + release at the derived oscillation peak; T8 windows re-derived from the corrected closed form; ledger bookkeeping statement added (midpoint displacement identity, damping booked as Q, elastic contact in W_contact, E_diss_release in Q at the release tick). Element laws 1-9 untouched.
- Reference repair (8cbcd91b, recorded with the first receipts): the three attempt commits were rewritten on the UNPUBLISHED sole-owner attempt branch to separate the Agent: trailer into a proper trailer block; TREES UNCHANGED; identities recorded in PREREGISTRATION.md.
- Receipt-index repair (this revision): the T8 receipt block indexed trace rows by tick instead of by row index (rows[i] holds tick i+1); the bound M01 document is now captured while still bound; the released document is emitted after the release tick executes.

## file identities at freeze

- PREREGISTRATION.md: fa30fe5c472c32266b5b1ea121d0c4d86e5e7b649572c42ef470a8df3532435c
- attachment_patch.py: 63a31e9c3a83d2ae94939a6e8bcf99fe14dc8891224abfe9a1b9eac2cb353ff8
- run_experiments.py: 162cd556004b62e57188dd400ce50346b0ebe36310cc901ffaab6ce75b8d0a4f
- test_attachment_fixture.py: 130ebc84dd730d727e670b5a918f9dd9d5944d05880a9f0d8f2325e20f582d0b
- lint_report_numbers.py: 49e8e52e3518c50a07caac0494235f252364963dd40885e8c5a181b157756c93
- render_run.py: 4a86f23092df864385c7c49d666a1b4018c88314210043df5f125e28930b5bea
- make_capture.py: 1b14480d85f1ad7085f576c8733aa3aaea0982fae813d3f33b2d903e60291125
- make_report.py: f3dcfd68a9f249028db6e4f96e30b1c3885346589b3128382d05d009f54221cf
- KNOWN_SKIPS.md: 6cae2da6477ffd9ea0c82d2ea831b99d78352993a2e21496fe893f96cda6c2ce
- .gitattributes: 705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da
- experiment_receipt.json: e594336599cf0a78b12660f3f305417256230276d85795f1ba6a3cd70599016f
- experiment_trace.json: 259b731d40191fcfb968675e67c91f816dc4bd3ed0bad699125954fce753960b
- experiment_receipt_rerun2.json: cbf5618444b07c46b5d2cc70965ae2af3f1c1047f53676b35c8ec48217234409
- experiment_trace_rerun2.json: 259b731d40191fcfb968675e67c91f816dc4bd3ed0bad699125954fce753960b
- determinism_receipt.json: 5f987e16b78cc9f6123ef142ffb6efd51632a3c761eb90e70ca2a7a5018b9d13
- falsifier_receipt.json: 006dce6a8109a293ebf98c60981baaee43b31e820e37007652b22cefaf5d32e9
- regression_receipt.json: 25280220142e18a11ac8e5213dee4c7e8414d613c26fce6df8a00940bb775bea
- capture_manifest.json: 45d96627a55d9cb256fc70a3b2ef044708c003fa5aa2f751896cc6404426aa37
- capture_context.json: c816f0e9638c746f1b441d3ee995fff54d3240f707afd1f4bfd81ff36e9037bc
- capture_validation_receipt.json: 5277a25910c25d5b403fcb0a10210a40a6b959cccf1f388ffdfa91e9503ebd24

## honest limits

- Offline CPU experiment executable over pinned inputs; no GPU submission (the scope is a 356-tick two-body fixture; prereg law 12).
- experiment_profile.json is the single DECLARED live-field file (wall-clock x1_wall_seconds); it is excluded from byte identity by declaration and from the pinned file list above; every other artifact regenerates byte-identically.
- The fixture constants are declared placeholders with the derivation recorded; they do NOT qualify the biological ports; the biological C17 debt remains explicitly-unresolved pending a separately authorized measurement (A07 gate).
- No fitting experiment was run; no friction constant was introduced; no lambda_min appears in any artifact.
