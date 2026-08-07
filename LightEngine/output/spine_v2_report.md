# Spine v2 Lane-A.1 Final Report

## Task
Implement spine v2: replace the v1 uniform hollow-tube sacrum with a tapered solid-base column derived from the cantilever bending moment. Keep all other v1 geometry frozen. Run 8000-tick main and control simulations; report the taper derivation, gate trace, cluster history, frame metrics, capture gaps, rope telemetry, the seven falsifier verdicts, and the pytest count.

## Files modified
- `LightEngine/spine_structures.py` — tapered sacrum builder + full-arc gate.
- `LightEngine/demo_spine.py` — v2 header, droplet=4^3 fix, PNG-name fix, taper print block, CUDA-oom retry.
- `LightEngine/tests/test_spine.py` — taper-profile test + updated sacrum counts.

## Taper derivation
For a vertical cantilever torqued at the top, `M(z) = F_tip * (H - z)`.

| Quantity | Main | Control |
|----------|------|---------|
| lumbar+load weight `W` | 79.9291 | 79.9291 |
| lumbar+load COM `x` | 0.2450 | 0.2450 |
| contact_x | 0.18700 | 0.07500 |
| moment arm `x - contact_x` | 0.0580 | 0.1700 |
| sacrum height `H` | 0.4000 | 0.4000 |
| derived `F_tip` | 11.5897 | 33.9698 |
| derived `M_max` | 4.6359 | 13.5879 |
| cushion force scale `K_WALL/R_WALL` | 20.0000 | 20.0000 |
| extra grains needed at base | 1.1590 | 3.3970 |
| ring grain counts (base -> top) | 16/16/15/14/14/14/13/12 | 16/16/15/14/14/14/13/12 |

The profile maps `M(z)/M_max` linearly onto the available grain-count range [12, 16]: solid 4x4 at the base, hollow shell at the free top. Total sacrum grains = 114 (vs 96 in v1).

## Gate trace
Both runs used `route=full-arc` and passed the gate (`gate_passed=True`).
- Main: `contact_x = 0.18700`, `R_true(0) = 1.311`, `theta_stop_muscle = +16.02°`, `theta_stop_load = -15.60°`.
- Control: `contact_x = 0.07500`, `R_true(0) = 0.967`, `theta_stop_muscle = +43.47°`, `theta_stop_load = -120.00°`.

## Main run (`spine_v2`)
- **Cluster history (sacrum/saddle/lumbar/droplet/rope/load):**
  - ticks 0–400: `1/1/1/1/1/1`
  - tick 600 onwards: `2/1/1/1/1/1` — sacrum tears just above the pinned base
- **Settled angle (last 20%):** `+5.25°` (sign `+1`, matches predicted `+1`) — BALANCE PASS
- **Max load_gain:** `+0.0000` at tick 0 — LIFT FAIL
- **Capture gaps:** min `0.0267`, max `0.2580`
- **Sacrum tilt:** max `12.323°`; base migration `0.0000`
- **Rope sign fractions:** tension 0.63, slack 0.33, compression 0.04; max compression magnitude 190.46

## Control run (`spine_v2_control`)
- **Cluster history (sacrum/saddle/lumbar/droplet/rope/load):**
  - ticks 0–400: `1/1/1/1/1/1`
  - tick 600 onwards: `2/1/1/1/1/1` — sacrum tears just above the pinned base
- **Settled angle (last 20%):** `+66.69°` (sign `+1`, opposite predicted `-1`) — BALANCE FAIL
- **Max load_gain:** `+0.0066` at tick 200 — HOLD PASS
- **Capture gaps:** min `0.0210`, max `0.2801`
- **Sacrum tilt:** max `3.599°`; base migration `0.0000`
- **Rope sign fractions:** tension 0.43, slack 0.47, compression 0.10; max compression magnitude 162.25

## Seven falsifier verdicts
| Falsifier | Bar / criterion | Main | Control |
|-----------|-----------------|------|---------|
| (a) LIFT | main far-end rise >= 0.10 lu | **FAIL** (+0.0000) | skipped |
| (b) HOLD | control far-end rise <= 0.05 lu | skipped | **PASS** (+0.0066) |
| (c) BALANCE | settled sign matches `sign(R_true(0) - 1)` | **PASS** (+1 vs +1) | **FAIL** (+1 vs -1) |
| (d) INTEGRITY | one cluster each | **FAIL** (sacrum splits) | **FAIL** (sacrum splits) |
| (e) SLACK | rope compression > 20% samples | **PASS** (4%) | **PASS** (10%) |
| (f) FRAME | sacrum tilt <= 2°; base migration < 0.5·d_eq | **FAIL** (12.323°) | **FAIL** (3.599°) |
| (g) CAPTURE-CLOSED | every gap in `[S_WALL=0.0250, 2·d_eq=0.0968]` | **FAIL** (0.0267–0.2580) | **FAIL** (0.0210–0.2801) |

## Theory falsifier
The tapered solid-base sacrum **still tore at tick 600 in both runs**, exactly where v1 tore. Increasing the base solidity (16 grains/ring vs 12) did not prevent the tear; the failure mode is unchanged. This fires the v2 theory-falsifier: **the cushion kernel has no bending membrane at the single-bone scale**, and the moment must be distributed across **two supports** (the pelvis branches — a branched-chain membrane). Recorded, not patched.

## Pytest count
```
python -m pytest LightEngine/tests/test_spine.py -q
9 passed in 7.81s
```

## Render outputs
Begin/end frames written by the ParticleEngine renderer:
- `LightEngine/output/spine_v2_begin.png`
- `LightEngine/output/spine_v2_end.png`
- `LightEngine/output/spine_v2_control_begin.png`
- `LightEngine/output/spine_v2_control_end.png`

## Verification notes
`python tools/verify_run.py LightEngine/output/print_spine_v2_log.txt LightEngine/output/print_spine_v2_control_log.txt` reports AGREE on all recomputed verdicts it checks ((a), (c), (d), (e), (b) for control). FRAME is UNCHECKED by `verify_run` because it has no tick-table bar. Rope sign fractions disagree with `verify_run`'s recomputation because `verify_run` counts samples that contain any taut/compression/slack link, while the logs print the mean fraction of links per sample; both support the same PASS/FAIL conclusion.

## Metering fixes from v1
- Header now prints `droplet=4^3` (was `droplet=64^3`).
- PNG filenames are `spine_v2_*` and `spine_v2_control_*` (was `spine_v1spine_v1_*`).
