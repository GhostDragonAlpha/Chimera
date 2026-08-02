# Myobody walk policy vs CMU mocap (35_01 walk) � A/B report

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

**Policy:** `output/myobody_walk_directional_policy.pt` (PPO, 290-muscle MyoSuite myobody; recovered rollout contract)
**Reference:** CMU MoCap subject 35 walk, 120 Hz � see `mocap_walk_reference.json`
**Method:** 5 randomized starts x 10 s, WORST-of-N scoring (project rule), contact dyad
(MuJoCo truth vs geometric proxy, 94.8% agreement at 0.2 cm).

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
| classification | NOT A GAIT � periodicity 0.15: there is no repeating cycle here. This is thrashing that happens to travel. |
| periodicity | 0.15 (walk needs >= ~0.6) |
| duty factor | 0.54 (human 0.55-0.65) |
| survival | 8.9 - 10.0 s of 10 s |
| forward distance | 1.69 - 3.15 m |
| cadence | 132.3529411764706 steps/min |

## Verdict

GAP IS LARGE � the policy does not sustain a measurable gait.

Per-seed detail and angle phase errors: `gait_vs_mocap_report.json`.
