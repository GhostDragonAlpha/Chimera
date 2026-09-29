# MAT2-F07 — source-bound qualification receipt: forest obstacles and scene boundaries

**Verdict: BUILT AND SELF-CONSISTENT.** SEVEN explicit material obstacles (rocks, fallen logs, dense stands) were authored onto the merged F02/F03/F04 clearing as declared data whose render sections and pinned collision bodies carry the SAME vertex arrays; the boundary vocabulary is fully DECLARED (the extent rule with its rendered post ring, the slope rule, one solid_obstacle record per obstacle): the walkability mask attributes every blocked cell to a declared record (zero invisible walls), BFS from the spawn reaches all 12 frozen destinations with measured clearance and slope, every obstacle stops an aimed probe through the unmodified M06 law with pre-overlap first contact, mesh-exact penetration 0.0 m and no crossing, all 7 falsifier arms bite fail-first each against its own passing clean control, and the forest/visible_static capture is structurally valid under the REGISTRY profile with a single gate-bound artifact and committed stills. Visual acceptance itself belongs to the independent visual reviewer.

- card: MAT2-F07; planning id F07; attempt 7f734268b7ee4a9887f794f9f620175e; arrival arrival-c7445b4a9e9640a8a821006fff1fd3b0; criteria sha256 20eb25ac4401eea15fc28ad475c88a7d7b2798aad3a0bed36ecc4aa3fb56320b; scope sha256 cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097; base revision d62c56f67f7524222839c1ebf31f0dbc6fe9ea31 (branch-1 fast-forwarded to the sealed line tip; F01-F04/B06 merged).
- done_when (verbatim): "The clearing offers traversable routes; no invisible walls masquerade as physical obstacles".
- discipline: PREREGISTRATION.md committed BEFORE implementation at bb52ec61927065773bbdac4ecfa4f3907cda7148; amendments A1-A5 are separate commits (10c20035f141caa4c98ac6cd43b0b92e45f70dbb, 0b2169fe581dad3868d22d16e52e82e386c06973), all before the implementation commit and the first completed build. This report is GENERATED from evidence/checks.json and the sibling receipts — no observed value is hand-transcribed.

## 1. Reconcile-first (reused published bytes only)

All 11 pins asserted by raw sha256 at every run (`f07_pin_*` refusals): F02's tied terrain asset + query surface + F01 render law + clearing recipe/declaration + trunk declaration, F04's contact machinery (imported, never forked), M06's byte-identical local_contact module and contact law, F03's trunk mesh. No physics constant is new: obstacle matter `wood_trunk_01` mu 0.6/0.6 (F03's declared UNEVIDENCED-PLACEHOLDER, G04 debt), probes `mass_tetra` 0.12 kg mu 0.6/0.4 (F02/M06), the M06 law constants including slop/margin 1e-05 m (A5's per-side slack is that declared constant).

## 2. The declared scene vocabulary (assets/obstacle_declaration.json)

- declaration sha256 `7164eaf7ef110a8259572526eed0f9e1a5433f95d585cd953c3411634669b81b`; 7 obstacles in the frozen splitmix64 order (seed 4600823): rock_01, rock_02, rock_03, log_01, log_02, stand_01, stand_02.
- P0 (measured per A3): ground + obstacle co-instantiation is REFUSED by the pinned law for ALL 7 obstacles (`nonfinite_state`, exact base contact); the impact runs instantiate exactly the struck obstacle (declared composition scope, F04 heritage).
- P1 tied assets: render sections == collision surfaces bidirectionally (true); every obstacle's shipped vertex table equals the declaration exactly; the pinned post ring: {"edge_samples": 3204, "post_bases": 80, "post_vertex_band_m": 0.05, "within_declared_gap": true, "worst_gap_to_post_m": 1.0}.

## 3. Routes and the invisible-wall audit (P3/P4) — measured, not asserted

- mask 81x81 at 0.5 m; blocked cells 363; attribution: {"extent_rule": 320, "log_01": 10, "log_02": 4, "rock_01": 6, "rock_02": 4, "rock_03": 4, "stand_01": 7, "stand_02": 7, "trunk_01": 1}.
- P4 invisible-wall audit: unattributed blocked cells = 0 (every blocked cell names its declared record; the FB1 injection proves the detector has teeth).
- P2 stop-declaration coverage: 1.0; declared records: extent_rule, log_01, log_02, rock_01, rock_02, rock_03, stand_01, stand_02, terrain_slope_rule, trunk_01.
- P3 routes: all 12 destinations reached. Per-route reached / hops / length m / min clearance m / max slope:

| route | reached | hops | length m | min clearance m | max slope |
|---|---|---|---|---|---|
| D_E | true | 39 | 19.5 | 0.280824 | 0.0 |
| D_N | true | 39 | 19.5 | 3.854647 | 0.0 |
| D_S | true | 39 | 19.5 | 1.772217 | 0.0 |
| D_W | true | 39 | 19.5 | 3.854647 | 0.0 |
| D_log_01 | true | 53 | 26.5 | 0.280824 | 0.015226 |
| D_log_02 | true | 10 | 5.0 | 0.280824 | 0.0 |
| D_rock_01 | true | 53 | 26.5 | 0.300054 | 0.026054 |
| D_rock_02 | true | 53 | 26.5 | 0.257478 | 5e-05 |
| D_rock_03 | true | 48 | 24.0 | 0.412169 | 0.010758 |
| D_stand_01 | true | 46 | 23.0 | 0.32211 | 0.0 |
| D_stand_02 | true | 31 | 15.5 | 0.280824 | 0.0 |
| D_trunk | true | 25 | 12.5 | 0.280824 | 0.0 |

## 4. Obstacles stop physically (P5, STOP law of A1/A5)

| run | first contact | pre-overlap | worst pen m | min approach m | struck plane err m | struck analytic err m (bar m) | pair sep m | ledger |
|---|---|---|---|---|---|---|---|---|
| rock_01 | tick 14 ccd | true | 0.0 | 0.459311 | 0.0 | 0.0 (1e-09) | 0.00101 | 3.469446951953614e-18 |
| rock_02 | tick 14 ccd | true | 0.0 | 0.45814 | 0.0 | 0.0 (1e-09) | 0.00101 | 3.469446951953614e-18 |
| rock_03 | tick 14 ccd | true | 0.0 | 0.406776 | 0.0 | 0.0 (1e-09) | 0.00101 | 2.7755575615628914e-17 |
| log_01 | tick 14 ccd | true | 0.0 | 0.08171 | 0.0 | 0.00121 (0.0012197660428522215) | 0.00101 | 4.336808689942018e-18 |
| log_02 | tick 14 ccd | true | 0.0 | 0.068888 | 0.0 | 0.001099 (0.0011091309901383373) | 0.00101 | 7.806255641895632e-18 |
| stand_01 | tick 14 ccd | true | 0.0 | 0.610497 | 0.0 | 0.000512 (0.0005233093175713771) | 0.00101 | 2.7755575615628914e-17 |
| stand_02 | tick 14 ccd | true | 0.0 | 0.610497 | 0.0 | 0.000512 (0.0005233093175713771) | 0.00101 | 2.7755575615628914e-17 |

Every run: first contact pre-overlap (ccd, gap > 0), mesh-exact penetration within the frozen 0.0001 m bar, the probe centre's approach coordinate never crosses the struck body's mid-plane/axis, the struck side's contact point lies EXACTLY on its render triangle (plane error 0.0 against the 1e-9 bar), the struck-side analytic identity holds within the chord sagitta + the pinned 1e-05 m slop (A5), and the ledger residual stays under 1e-12.

## 5. Visual/collision correspondence (P7, pure ray/geometry)

- 12 marker rows across the three profile views; zero UNRENDERED required subjects; every subject's frozen outcome met; VISIBLE_BUT_MISMATCH count 0.
- capture: profile `forest` (kind visible_static) read READ-ONLY from the registry (canonical sha256 3348d00194c8d920abe3c5902c36a0f23088838bd293172f10f65a3de2670852); visual_capture.validate_manifest structurally_valid=true; visual_gate.verify structurally_valid=true; single gate-bound artifact evidence/frame_V1_clearing_overview_clean.bmp; capture_sha256 6c9316279e1b231b5dd0352b4a10a1b191d7391ffb03895714bd953814a58b87.
- transform-list gate: applicability not_applicable_static_image_capture (static image capture — no video frames exist; identity decode/re-encode matches byte-exactly and the flipped transform is refused).

## 6. Falsifier proof (run FIRST; all 7 bite fail-first)

| arm | bites | clean control |
|---|---|---|
| FB1_invisible_wall_in_mask | true | real scene mask attribution |
| FB2_ghost_obstacle_collision_without_render | true | same-form marker on real rock_01 |
| FB3_phantom_obstacle_render_without_collision | true | same-form impact on real stand_01 |
| FB4_undeclared_stop_event | true | full record set coverage |
| FB5_route_metric_teeth | true | real scene BFS |
| FB6_off_frame_probe_subject | true | camera-facing trunk subject in the same V2 view |
| FB7_render_collision_decouple | true | classify on the UNPERTURBED render, same ray |

Full observed records in checks.json (falsifier_bites). Every arm carries its own clean control and the bite is credited only when that control passes (named `f07_fb*_premature` guards). A non-biting arm refuses the whole build (`f07_falsifier_did_not_bite`).

## 7. Determinism (P8)

Two full builds produced byte-identical artifacts: 13; identical=true.

## 8. Honest boundaries

- CPU-only (stdlib); no engine run, no native change, no GPU, no training, no runtime or playable-build acceptance.
- The obstacle impact runs instantiate exactly one static body each (P0 refusal heritage); a probe supported by the ground WHILE touching an obstacle is NOT demonstrated (F04's open seam composition).
- Obstacle friction is F03's declared UNEVIDENCED-PLACEHOLDER (G04 debt); rock matter reuses the probe material values (no separately acquired rock matter).
- Traversal is verified on the declared 0.5 m walkability mask with the declared 0.25 m body envelope; continuous-space motion planning is NOT claimed (card observation: player steering needs no general autonomous pathfinding).
- The extent rule is the DECLARED refusal in the mask/vocabulary (citing earth_environment.hpp:118); no native out_of_patch run is claimed.
- The V1 overview renders the obstacles at sub-2-px scale (disclosed, F03's own form for the trunk); the resolvable scene, trunk, post ring and the five diagnostic layers are verified in the V2/V3 frames, and every obstacle surface's visibility is established by the pure ray/geometry marker classify (markers never read pixels).
- Structural capture validity only: visual acceptance belongs to the independent visual reviewer.

## 9. Exact commands (from this directory, Python 3.14, CPU only)

    python -B implementation.py bites    # 7/7 fail-first, each with a passing clean control
    python -B implementation.py build    # receipt + declaration + frames
    python -B implementation.py verify   # P8 double-run determinism
    python -B make_report.py             # this file, from receipts
    python -B lint_report_numbers.py --selftest
                                         # report numbers traceable
    python -B -m unittest test_implementation -v
