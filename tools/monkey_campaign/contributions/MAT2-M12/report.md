# MAT2-M12 qualification report — mechanical detail and render detail independently

Generated from the committed receipts (zero hand-typed numbers). Composed against CARD_STARTER v2; PREREGISTRATION.md + Amendments A1/A2. Criteria sha256 chain: receipt 1e98a4f4465d4a50 == registry card == attempt == PREREGISTRATION.md (asserted by the named checks)....

## Result

- all_gates_green: true (Y1=true Y2=true Y3=true Y4=true Y5=true Y6=true Y7=true Y8=true)
- falsifier arms FB1-FB6 all bit with clean controls first: true
- determinism (two fresh runs per resolution, scoped dynamic subtree byte-identity): true
- trace sha256: c2bf7bd16371469249b987d138fe64bd0e6678ea47476372465fe40ac3d62c1b

## The comparison (mechanical LOD)

| quantity | coarse (6x6) | reference (12x12) | window | within |
|---|---|---|---|---|
| T1 at bound hold (N) | 4.1928e-01 | 4.1105e-01 | 3.0529e-02 | true |
| foot contact at hold (N) | 8.9368e-02 | 9.7596e-02 | 1.4903e-02 | true |
| settled p=0 foot gap (m) | 1.9956e-04 | 1.7554e-04 | 1.0000e-03 | true |
| transverse inertia at static hang (kg m^2) | 2.7284e-07 | 2.7880e-07 | rel <= 1.0000e-01 | true |
| recovery |gap(loaded)-gap(off)| coarse (m) | 4.2813e-07 | 1.0000e-03 | true |
| recovery |gap(loaded)-gap(off)| reference (m) | 6.2400e-06 | 1.0000e-03 | true |

Per-resolution statics identities (Y4a whole-system; every declared window):

| resolution | window | residual (N) | bound (N) | within |
|---|---|---|---|---|
| coarse | HOLD | -2.6159e-08 | 1.5900e-01 | true |
| coarse | OFF | -2.8895e-07 | 1.5900e-01 | true |
| coarse | P0 | 1.5111e-03 | 1.5900e-01 | true |
| reference | HOLD | 7.5346e-08 | 1.5900e-01 | true |
| reference | OFF | -1.2200e-05 | 1.5900e-01 | true |
| reference | P0 | 1.1730e-03 | 1.5900e-01 | true |

Control meaning (Y6, both resolutions): T1 drop at the T2 release == W(ulna)+W(radius), released T2 bitwise 0, distal landing within 1.0e-4 m of contact rest heights, departure bite, double-release refusal:

| resolution | T1 drop (N) | W_ur (N) | max departure (m) | T2 bitwise 0 | drop within | refused |
|---|---|---|---|---|---|---|
| coarse | 1.9854e-01 | 1.8985e-01 | 2.0195e-02 | true | true | true |
| reference | 1.9030e-01 | 1.8985e-01 | 2.0086e-02 | true | true | true |

Render mapping attached under large motion (Y7): the binding audit over the released runs' snapshots is bitwise 0 at every rendered tick; max motion realized from rest: coarse 8.3885e-03 m, reference 1.3054e-02 m (the record is large motion; the gate is not vacuous).

## Cost table and selection (the recorded frame-time/VRAM limits)

| quantity | coarse | reference | declared limit | within limit |
|---|---|---|---|---|
| sim seconds/tick coarse | 8.779385e-03 | | 3.333333e-03 | false |
| sim seconds/tick reference | 1.580645e-02 | | 3.333333e-03 | false |
| VRAM payload (computed demand, B) | 923376 | 928560 | formula (prereg section 3) | recorded |
| peak process working set (B) | 45912064 | 59437056 | measured | recorded |

Selection rule (prereg section 5, frozen): argmin over QUALIFIED of sim_seconds_per_tick, ties by vram_payload_bytes. Qualified: coarse, reference. Ranking (all): coarse -> reference. SELECTED: coarse.

The recorded tick budgets are OVER the declared 300 Hz real-time budget for BOTH resolutions (within_limit false in the receipts): this lane is the offline numpy research stack, not the real-time engine; the limits are recorded disclosures, not pass/fail gates (prereg section 5-Y8). The COST RANKING is monotone and drives the selection.

## Falsifier arms (clean control first)

| arm | clean control value | tampered value | bite | bit |
|---|---|---|---|---|
| FB1 stale render | 0.0000e+00 m (bitwise 0) | 8.0763e-03 m | >= 1.0000e-03 m | true |
| FB2 dropped-ring remap | coverage identity | render_vertex_coverage_refused:coarse | refusal fires | true |
| FB3 undeclared strength | 0.0000e+00 m^2 split error | 1.0530e-03 m^2 | audit refuses | true |
| FB4 silent mass drift | totals bitwise 2.0e-3 kg | 5.2055e-04 kg tampered total | != declaration | true |
| FB5 area-independent forces | worst ratio 4.4583e-16 | 5.8498e-01 | >= 1.0e-6 | true |
| FB6 unaccounted energy | law dev 0.0000e+00 N (bitwise 0) | 5.2394e-01 N | >= 2.0529e-02 N | true |

## Capture bindings

- ONE video artifact (FFV1 -level 3 -g 1 -fflags +bitexact; ffmpeg ffmpeg version 8.1.1-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers): capture sha256 a99d661df675d5d79262a3a9b348bedd7475d510848d6bdc93782f85abe335cf
- manifest == context == receipt capture_sha256 (disk hash); state_binding = whole-file trace sha c2bf7bd16371469249b987d138fe64bd0e6678ea47476372465fe40ac3d62c1b; the per-resolution canonical subtree shas: coarse 066d3c2535793b52bf1b0d3e5d479295b98337c4b9ac4644670f41dd09420fca, reference 10aff9217dee50722713c839bc9eb42fcfc9c080b8b087c4ad2454fef3954ec0 (view toggles preserve the physical state hash; asserted by the named checks)
- validator: tools/monkey_campaign/visual_capture.py validate_manifest | structurally_valid: true | views: 6
- unbound-media refusal: a manifest bound to a wrong trace/capture sha is refused by validate_manifest (capture_identity_mismatch; named check)
- camera-consistency: 4 committed stills, signed row-order checks consistent; zero cross-viewport leakage; per-layer pixel presence present for all 5 declared layers at BOTH resolutions
- visual_acceptance stays false: independent image review is the Lieutenant's (Sergeant review requested through the Lieutenant).

## Amendments and disclosures

- Amendment A1: the coarse erection offset is probe-derived (1.0929e-03 m, 1500-tick pole-sag probe, trail recorded); the first foot-gap-based probe metric was REJECTED with its values recorded (the sealed chain placement settles through P0).
- Amendment A2: two gate-MECHANICS corrections from the probe-class bank pass (Y2c static-hang inertia referent; Y1b digest scope). Physics bytes unchanged: the trace sha256 is byte-identical across both bank passes (c2bf7bd16371469249b987d138fe64bd0e6678ea47476372465fe40ac3d62c1b).
- The named-check suite ran 16 executed, 0 skipped (G12 accounting; the gate output records the counts).
- Honesty limits carry over from prereg section 10: engineering actuator bladder; point-mass bones with real masses; the elbow bond and the hand terminal stay explicitly unresolved (B04/B05 ledgers carried); the VRAM number is a computed demand formula, NOT a measured GPU allocation (this lane allocates no GPU surface).

## Artifact pins

| artifact | sha256 |
|---|---|
| experiment_receipt.json | db516434a1034d0703a362aaecfd7b983b9a38d36dbcd390b31d2e15f1b4c589 |
| experiment_trace.json | c2bf7bd16371469249b987d138fe64bd0e6678ea47476372465fe40ac3d62c1b |
| experiment_trace_rerun.json | 79f295481084540c2c55a4b6ed4215e464b35cb8d92b5bc8fdbd8574fd809b4d |
| falsifier_receipt.json | f42004d6320cb54ffa167a95ab555d78af8bdf6f88e55b481467e8cc5632766c |
| determinism_receipt.json | a18c46fcbc92fec2d286541f5a59e49c80ac9ea63c39109ab3cfdc69cd9b6500 |
| capture_manifest.json | 0ea48c70af67b9336a3b95ca03a5a6ad0ccdad7a0d80db1e77c6dffff8139d40 |
| capture_context.json | d776caf802ab843477625061ad9afc98c466bf9adfb646804c4d64d8607b5e10 |
| capture_validation_receipt.json | d46efc82bb4b85115a8c67ac3df70dccae271da1478d5c8963aab2cb98e60d27 |
| capture/capture_mat2_m12_lod.mkv | a99d661df675d5d79262a3a9b348bedd7475d510848d6bdc93782f85abe335cf |
| PREREGISTRATION.md | ec5fe398fa626e24668c5802b0d614db2d406ebabd16856d551315911a0561d3 |
| m12_lod.py | f08fd1d2e24f8b72b9833936d49db23cae9d5ef8c3bbedd1bdc2b9ec792849cc |
| run_experiments.py | ba37aab505c6685be2ad6c5b9d7ba04026d4758e121d735c48910549ec16a12e |
| test_lod.py | ff1f152f6e2ac6f911d498aadfe903a72ada0f94e4410cff42f4908c92e0da3c |
| render_run.py | 46b963ee09a3ecfa2e807be76fbd2a715ab10c88dd604db4e4125467e4639197 |
| make_capture.py | bad748663b7fe1b9e9d64c521356b2b80d7a5bba2029e10584d74860c51002fd |
| make_report.py | e12bb1b48c641babe2deccc27ed82eef7454ab95b4c9953810ee690c709239cc |
| lint_report_numbers.py | 1b04410c20ff6eb2c73cc0cf5cc3e3564a5075ed2af012045456d31e5e650d6b |

