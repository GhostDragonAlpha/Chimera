# Myobody walk policy vs CMU mocap (35_01 walk) — A/B report

**Policy:** `output/myobody_walk_directional_policy.pt` (PPO, 290-muscle MyoSuite myobody; recovered rollout contract)
**Reference:** CMU MoCap subject 35 walk, 120 Hz — see `mocap_walk_reference.json`
**Method:** 5 randomized starts x 10 s, WORST-of-N scoring (project rule), contact dyad
(MuJoCo truth vs geometric proxy, 95.5% agreement at 0.2 cm).

## Reference (real human, measured)

| metric | value |
|---|---|
| cadence | 106.5 steps/min |
| stride length | 1.464 m (1.716 leg lengths) |
| stride time | 1.127 s |
| duty factor | 0.596 |
| speed | 1.285 m/s |

## Policy (measured, worst of 5)

| metric | value |
|---|---|
| classification | NOT A GAIT — periodicity 0.18: there is no repeating cycle here. This is thrashing that happens to travel. |
| periodicity | 0.18 (walk needs >= ~0.6) |
| duty factor | 0.43 (human 0.55-0.65) |
| survival | 3.7 - 9.4 s of 10 s |
| forward distance | 2.06 - 5.47 m |
| cadence | 201.21951219512195 steps/min |

## Verdict

GAP IS LARGE — the policy does not sustain a measurable gait.

Per-seed detail and angle phase errors: `gait_vs_mocap_report.json`.
