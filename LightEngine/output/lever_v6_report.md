# theLever v6 Report

**Run tags:** `lever_v6` / `lever_v6_control`  
**Seed:** `20260806`  
**Ticks:** 8000 each, sequential  
**Output frames:**
- `LightEngine/output/lever_v6_begin.png`
- `LightEngine/output/lever_v6_end.png`
- `LightEngine/output/lever_v6_control_begin.png`
- `LightEngine/output/lever_v6_control_end.png`

## 1. Print geometry

| body | count | notes |
|------|-------|-------|
| ground plate | 36 | 6×6, pinned |
| muscle droplet | 64 | 4³, seated on plate |
| fulcrum block | 64 | 4×4×4, pinned |
| fulcrum cheeks | 24 | two 4×1×3 walls, pinned (12 grains each) |
| **fulcrum total** | **88** | block + cheeks |
| lever tube | 156 | 13 rings × 12 grains, 4×4 hollow (1-grain shell, 2×2 void) |
| load block | 64 | 4³, resting on lever load end |
| **total** | **408** | |

Cheek dimensions:
- one-grain-thick walls centered at `y = ±(0.10 + d_eq + d/2) = ±0.1734` lu
- `x` span = 4 lattice steps, `z` span = 3 layers starting at the fulcrum top
- inner cheek face at `y = ±0.1484` lu, leaving a cushion gap to the tube side

## 2. Insertion-fraction derivation

`alpha` is re-derived by bisection on kernel static-torque quantities (no sweep).

- Stage 1: bisect `max_R_offedge(alpha) - 2.0 = 0` → `alpha_low = 0.042472`
- Stage 2: bisect weaker-arm deficit on `[alpha_low, 0.12]` → `alpha = 0.079211`
- `alpha_method = bisection`

Derived contacts:

| run | contact x (lu) | R_true | margin to load end (lu) | a_m (lu) | a_l (lu) |
|-----|----------------|--------|--------------------------|----------|----------|
| main    | -0.12125 | 1.913 | 0.42125 | 0.17897 | 0.42140 |
| control | -0.12500 | 1.050 | 0.42500 | 0.17522 | 0.42515 |

The control contact is muscle-ward of the main contact (`a_m_ctrl < a_m_main`, `a_l_ctrl > a_l_main`).

## 3. 8000-tick dynamics summary

### Main run (`lever_v6`)

- `max load_gain = +0.0224` at tick 200
- settled load_gain ≈ `-0.2164` (last 8/41 samples)
- settled lever angle ≈ `-13.10°` (load-side-down)
- fulcrum gap: min `0.0391`, max `0.0814`, mean `0.0567`, final `0.0562` lu
- all bodies remained 1 cluster; plate pins held

### Control run (`lever_v6_control`)

- `max load_gain = +0.0227` at tick 200
- settled load_gain ≈ `-0.2145` (last 8/41 samples)
- settled lever angle ≈ `-24.48°` (load-side-down)
- fulcrum gap: min `0.0480`, max `0.0770`, mean `0.0738`, final `0.0759` lu
- all bodies remained 1 cluster; plate pins held

## 4. Verdicts

| falsifier | main | control |
|-----------|------|---------|
| (a) LIFT    | **FAIL** — max gain 0.0224 < 0.10 | skipped |
| (b) HOLD    | skipped | **PASS** — max gain 0.0227 < 0.05 |
| (c) BALANCE | **FAIL** — R_true=1.913 predicts muscle-down, settled angle -13.10° is load-down | **FAIL** — R_true=1.050 predicts muscle-down, settled angle -24.48° is load-down |
| (d) INTEGRITY | **PASS** — 1/1/1/1 clusters, plate drift 0.0 | **PASS** — 1/1/1/1 clusters, plate drift 0.0 |
| (e) SAG     | not detected | skipped |

## 5. Conclusion

The v6 captured saddle keeps every body intact and the plate pins hold, but it does **not** make the machine follow the static torque prediction. Both runs settle load-side-down despite `R_true > 1`, and the load end never lifts. The signature is the same slip-and-settle failure seen in v5: the tube rotates about a side contact rather than tipping muscle-down through the saddle.

The v6 falsifier **(e) CAPTURE** has therefore fired: the saddle cheeks alone do not constrain the arm to the intended degree of freedom. The next membrane in the dependency chain — the tendon — must anchor the muscle droplet so its pull is routed through a captured path rather than acting as a free bulk beside the machine.

## 6. Validation

- `python -m pytest LightEngine/tests -q`: **118 passed, 6 warnings**
- `test_lever_counts` confirms `n_fulcrum = 88`, `lever_len = 13`, `n_lever = 156`, and `alpha_method == "bisection"`.
- `test_lever_main_ratio`, `test_lever_control_ratio`, `test_lever_control_weaker_arm`, and `test_lever_cushion_contacts` all pass.
