# MAT2-F08 — source-bound qualification receipt: verify repeatable forest loading

**Verdict: BUILT AND SELF-CONSISTENT.** The scene seed/configuration
(`assets/scene_configuration.json`, 12 pinned assets, seeds
4598321 / 4600823) reproduces the full sealed-line scene: the terrain
declaration, terrain bundle and obstacle declaration regenerate BYTE-EXACT
from their seeds; the frozen seven-run dynamics trace re-derives the PUBLISHED
F07 contact_trace.json byte-exact; all six rendered frames re-derive the
PUBLISHED F07 capture bytes byte-exact; the materialized scene state (assets +
collision state + initial state, 260046 bytes, fingerprint `657765d78be1749203bcf77901c58d579ae2e29278ed15304ad108fc850aa62c`)
is byte-identical across 3 fresh subprocess instantiations and the
in-process one; and every missing/corrupt/silent-default/seed-drift/
float-drift arm fails CLEARLY with a named refusal (6/6 falsifier arms bite
fail-first, each against its own passing clean control). Visual acceptance
itself belongs to the independent visual reviewer.

- card: MAT2-F08; planning id F08; attempt d8a71eabe827417f90de09cd1f7048c3; arrival arrival-961642204b8c4a478a4457af12fbfdbb;
  criteria sha256 8063e7175f9b9a638809b348606636d280a56d9165245a9f91ced21abb55fcd7; scope sha256 cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097; base revision edd5ae079d5f0f64ae498e055a1b11bc5adab013
  (branch-1 fast-forwarded to the sealed line tip; F01-F07/B06 merged).
- done_when (verbatim): "Scene seed/configuration reproduces assets, collision and initial state with clear failures for missing assets".
- discipline: PREREGISTRATION.md committed BEFORE implementation at
  `32df1e4d2d7ff78b135468ba97c88ee894e00bf7`; amendments A1 (raw vs self sha256 pin correction) and A2
  (per-card profile object canonical sha) are separate commits
  (9f4c91ec, 4a166287), both before the implementation commit and before any
  evidence artifact existed. This report is GENERATED from
  evidence/checks.json and the sibling receipts — no observed value is
  hand-transcribed.

## 1. Reconcile-first (reused published bytes only)

All 12 pins asserted by raw sha256 at every load (`f08_pin_*` refusals
name the asset): F02's terrain asset/query/bundle modules + clearing
recipe/declaration + trunk declaration, M06's byte-identical local_contact
module and contact law, F03's trunk mesh, F04's contact machinery (imported,
never forked), F07's scene module (imported, never forked: seeded placement,
contact bodies, render/classify law) and F07's published obstacle declaration.
No physics constant is new. The reproduction TARGETS are published merged
evidence (F07 trace + six frames), pinned by raw sha256.

## 2. Seed -> asset reproduction (P1, measured)

| asset | source | published sha256 (16) | regenerated (16) | byte_equal |
|---|---|---|---|---|
| `clearing_declaration_json` | {"seed": 4598321} | `18dd2ff65410cd1c` | `18dd2ff65410cd1c` | true |
| `terrain_bundle_json` | {"regenerated_declaration_sha256": "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1"} | `446ed3fbd0f50205` | `446ed3fbd0f50205` | true |
| `f07_obstacle_declaration_json` | {"seed": 4600823} | `73525a3de022d5b8` | `73525a3de022d5b8` | true |

## 3. Published-evidence reproduction (P2, measured)

- dynamics trace: re-derived `710bfd1993894bd82c496c7c1c095d4201842ba1bebb248776f79392b925f0f7` == published `710bfd1993894bd82c496c7c1c095d4201842ba1bebb248776f79392b925f0f7`;
  byte_equal true. Worst ledger residual over all seven runs:
  2.7755575615628914e-17 (bar 1e-12).
- frames: all six reproduced frames equal the published F07 capture bytes:

| frame | published sha256 (16) | byte_equal |
|---|---|---|
| frame_V1_clearing_overview_clean.bmp | `6c9316279e1b231b` | true |
| frame_V1_clearing_overview_diagnostic.bmp | `e241729012d1238a` | true |
| frame_V2_seam_closeup_clean.bmp | `360e7eac5e1f0a0f` | true |
| frame_V2_seam_closeup_diagnostic.bmp | `6d4e64117e43ad86` | true |
| frame_V3_side_depth_clean.bmp | `407fd44a22ebcfbb` | true |
| frame_V3_side_depth_diagnostic.bmp | `539888a720705d6b` | true |

## 4. Cross-instantiation reproduction (P3/P4, measured)

Scene state document: 260046 bytes, fingerprint `657765d78be1749203bcf77901c58d579ae2e29278ed15304ad108fc850aa62c`.
Fresh subprocess instantiations: 3 (plus the in-process one) — all
byte-identical:

| instantiation | scene state sha256 |
|---|---|
| in_process | `657765d78be1749203bcf77901c58d579ae2e29278ed15304ad108fc850aa62c` |
| subprocess_1 | `657765d78be1749203bcf77901c58d579ae2e29278ed15304ad108fc850aa62c` |
| subprocess_2 | `657765d78be1749203bcf77901c58d579ae2e29278ed15304ad108fc850aa62c` |
| subprocess_3 | `657765d78be1749203bcf77901c58d579ae2e29278ed15304ad108fc850aa62c` |

The collision-state section (ground/trunk/obstacle M06 bodies with the pinned
law constants, ground co-instantiation re-measured per obstacle: F04's P0
refusal heritage) and the initial-state section (declared spawn/cameras/
schedule + derived impact starts + tick-0 solver states) are INSIDE this
document, so their reproduction is the document's byte-identity — measured,
not asserted.

## 5. Clear failures for missing assets (P5, measured; 6/6 arms bite)

| arm | bites | clean control |
|---|---|---|
| FB1_missing_asset_refusal | true | complete sandbox materializes the production scene state |
| FB2_corrupt_asset_refusal | true | pristine sandbox copy loads (FB1 clean control) |
| FB3_silent_default_detected | true | the complete sandbox (nothing substituted) materializes the production scene state |
| FB4_seed_perturbation_detected | true | unperturbed seed regenerates byte-exact (P1, in-scene) |
| FB5_float_gate_teeth | true | two unperturbed fresh instantiations compare byte-identical |
| FB6_off_frame_probe_subject | true | camera-facing trunk subject in the same V2 view |

Refusal codes name the missing/corrupt asset (`f08_pin_missing`,
`f08_pin_hash_mismatch`), the drifted seed (`f08_seed_reproduction_mismatch`),
the substituted scene (`f08_scene_state_mismatch` with the differing
sections). The lenient-default hazard is demonstrated and then caught by BOTH
enforcement layers (hash gate + fingerprint gate). 28 named refusal
codes are declared in checks.json, all `f08_`-namespaced.

## 6. Visual correspondence (P6)

- 12 marker rows across the three profile views against F07's frozen
  marker table; VISIBLE_BUT_MISMATCH count 0; zero UNRENDERED required
  subjects.
- capture: profile `forest` (kind visible_static) read READ-ONLY from the
  registry (canonical sha256 2c9d0ab3e2af5f18b89704f0265850f94c341d2290da2a62b1197bea8f1a206b); visual_capture.validate_manifest
  structurally_valid=true; visual_gate.verify
  structurally_valid=true; single gate-bound artifact evidence/frame_V1_clearing_overview_clean.bmp;
  capture_sha256 `6c9316279e1b231b5dd0352b4a10a1b191d7391ffb03895714bd953814a58b87` (byte-equal to the published F07 gate
  artifact — the capture re-produces the merged line's still exactly).
- transform-list gate: applicability not_applicable_static_image_capture (static image
  capture — no video frames exist; identity decode/re-encode matches
  byte-exactly and the flipped transform is refused).

## 7. Determinism (P7)

Two full builds produced byte-identical evidence artifacts:
12; identical=true.

## 8. Honest boundaries

- CPU-only (stdlib); no engine run, no native change, no GPU, no training, no
  runtime or playable-build acceptance. The collision path is the pinned M06
  law through unmodified vendored bytes — no new physics.
- The trunk mesh and its declaration are PUBLISHED F03 bytes (hash-pinned,
  loaded, not seed-regenerated — F03 published no generator); the trunk
  layer's reproducibility claim is byte-identity of the loaded published
  bytes inside the materialized scene state.
- Cross-instantiation equality is measured on ONE host/interpreter (the
  attempt's Python 3.14); cross-platform/cross-version bit-identity is NOT
  claimed (asset bytes sit on the pinned generators' 1e-6 grid; M06 trace
  floats are compared at full repr on this host only).
- The world-build-20260928 lane (WORLD_SEED 20260928, GPU splat world) was
  read for reconciliation only; its recorded hashes live in
  PREREGISTRATION.md section 9; nothing from that lane enters this build.
- Structural capture validity only: visual acceptance belongs to the
  independent visual reviewer.

## 9. Exact commands (from this directory, Python 3.14, CPU only)

    python -B implementation.py bites    # 6/6 fail-first, each with a passing clean control
    python -B implementation.py build    # receipt + scene state + frames
    python -B implementation.py verify   # P7 double-run determinism
    python -B make_report.py             # this file, from receipts
    python -B lint_report_numbers.py --selftest
                                         # report numbers traceable
    python -B -m unittest test_implementation -v
