# Spine v1 Lane-A.1 Final Report

## Task
Build `LightEngine/spine_structures.py`, `LightEngine/demo_spine.py`, and `LightEngine/tests/test_spine.py`; run 8000-tick main and control simulations; report derived dimensions, end-stops, gate trace, settled behavior, load gains, capture-gap ranges, rope fractions, sacrum tilt, the seven falsifier verdicts, and the pytest count.

## Files created
- `LightEngine/spine_structures.py` — builder + full-arc gate for the spine assembly.
- `LightEngine/demo_spine.py` — standalone CLI mirroring the leg-print log format.
- `LightEngine/tests/test_spine.py` — 8 pytest cases covering builder, gate, and capture geometry.

## Derived capture dimensions
| Quantity | Value |
|----------|-------|
| `d_eq` | 0.04840 lu |
| `contact_x` (main) | 0.18700 lu |
| `contact_x` (control) | 0.07500 lu |
| `well_floor_z` | 0.29840 lu |
| `droplet_apex_z` | 0.49680 lu |
| `lintel_bottom_z` | 0.88502 lu |
| `corner_rise` | 0.04142 lu |
| `n_rope` | 7 grains |

## End-stops
| Run | `theta_stop_muscle` | `theta_stop_load` |
|-----|---------------------|-------------------|
| main | `+16.02°` | `-15.60°` |
| control | `+43.47°` | `-120.00°` |

## Gate trace
Both runs used `route=full-arc` and passed the gate registration step (`gate_passed=True`).
- Main: `R_true(0) = 1.311`
- Control: `R_true(0) = 0.967`

## Main run (`spine_v1`)
- **Settled angle (last 20% of samples):** `-13.51°` (sign `-1`)
- **Predicted settle sign from `R_true(0)`:** `+1` (since `1.311 > 1`)
- **Max load_gain:** `-0.0000` at tick 0 — far end never rose
- **Capture gaps:** min `0.0244`, max `0.2304`
- **Sacrum tilt:** max `12.471°`; base migration `0.0000`
- **Cluster counts (sacrum/saddle/lumbar/droplet/rope/load):** `2/1/1/1/1/1`
- **Rope sign fractions:** tension 0.61, slack 0.24, compression 0.15; max compression magnitude 88.57

## Control run (`spine_v1_control`)
- **Settled angle (last 20% of samples):** `+37.86°` (sign `+1`)
- **Predicted settle sign from `R_true(0)`:** `-1` (since `0.967 < 1`)
- **Max load_gain:** `+0.0087` at tick 200
- **Capture gaps:** min `0.0199`, max `0.2759`
- **Sacrum tilt:** max `3.292°`; base migration `0.0000`
- **Cluster counts (sacrum/saddle/lumbar/droplet/rope/load):** `2/1/1/1/1/1`
- **Rope sign fractions:** tension 0.65, slack 0.33, compression 0.02; max compression magnitude 72.69

## Seven falsifier verdicts
| Falsifier | Bar / criterion | Main | Control |
|-----------|-----------------|------|---------|
| (a) LIFT | main far-end rise ≥ 0.10 lu | **FAIL** (-0.0000) | skipped |
| (b) HOLD | control far-end rise ≤ 0.05 lu | skipped | **PASS** (+0.0087) |
| (c) BALANCE | settled sign matches `sign(R_true(0) - 1)` | **FAIL** (-1 vs +1) | **FAIL** (+1 vs -1) |
| (d) INTEGRITY | one cluster each; pins hold | **FAIL** (sacrum splits) | **FAIL** (sacrum splits) |
| (e) SLACK | rope compression > 20% samples | **PASS** (15%) | **PASS** (2%) |
| (f) FRAME | sacrum tilt ≤ 2°; base migration < 0.5·d_eq | **FAIL** (12.471°) | **FAIL** (3.292°) |
| (g) CAPTURE-CLOSED | every gap in `[S_WALL=0.0250, 2·d_eq=0.0968]` | **FAIL** (0.0244–0.2304) | **FAIL** (0.0199–0.2759) |

## Pytest count
```
python -m pytest LightEngine/tests/test_spine.py -q
8 passed in 23.08s
```

## Render outputs
Begin/end frames were written by the ParticleEngine renderer:
- `LightEngine/output/spine_v1spine_v1_begin.png`
- `LightEngine/output/spine_v1spine_v1_end.png`
- `LightEngine/output/spine_v1spine_v1_control_begin.png`
- `LightEngine/output/spine_v1spine_v1_control_end.png`

## Verification notes
`tools/verify_run.py` was run against both print logs. LIFT/HOLD/BALANCE/INTEGRITY/SLACK verdicts recomputed by `verify_run` agree with the printed verdicts. FRAME is not recomputed by `verify_run` because it has no tick-table bar. Rope sign fractions printed in the logs are the mean fraction of links per sample; `verify_run` recomputes fractions by counting samples that contain any taut/compression/slack link, so the two formats differ numerically but both support the same PASS/FAIL conclusion.

## Design interpretation noted
Spec item 1 described the rope attaching to the "lumbar far-end underside," but the derived muscle-side stop in section 3 and the LIFT falsifier require the muscle to pull the near/sacrum-side end down so the far end rises. The implementation placed the rope at the muscle-side (near) end and treated the lumbar far end as the load-side stop. This report reflects that interpretation.
