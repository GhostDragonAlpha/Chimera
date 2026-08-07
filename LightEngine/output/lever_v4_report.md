# theLever v4 Report

**Date:** 2026-08-07
**Driver:** `LightEngine/demo_seed.py --structure lever`
**Logs:**
- `LightEngine/output/print_lever_v4_log.txt`
- `LightEngine/output/print_lever_v4_control_log.txt`

## What v4 changed

- Restored the lever arm to **4×4×16** (bone-class v1 cross-section).
- Kept the pinned **4×4×4** fulcrum.
- Kept the free-grain `R_true` bisection; added the **5³ muscle-droplet** contingency when the main contact lands within **2 lattice steps** of a bracket edge.
- Changed the **BALANCE** falsifier from the first-600-tick window to the **settled direction**: sign of the mean lever angle over the last 20 % of samples must match `sign(R_true - 1)`.
- Kept LIFT, HOLD, and INTEGRITY unchanged.

## Print-time derivation

Both main and control used the same printed geometry (seed=20260806):

| quantity | value |
|---|---|
| plate | 6×6 (pinned) |
| fulcrum | 4×4×4 (pinned) |
| lever | 4×4×16 = 256 grains |
| load | 4³ = 64 grains |
| muscle droplet | 5³ = 125 grains (heavy-muscle route) |
| total N | 545 |
| d_eq | 0.04840 lu |
| spacing d | 0.05 lu |

### Main

- Standard 4³ bisection target `R_true = 2.0` could not be reached; bracket was `[0.8902, 1.4643]`, so bisection clamped to the load-end edge.
- `margin_to_load_end = 0.07500 lu < 0.10000 lu` → switched to **heavy muscle (5³)** once.
- Heavy-muscle bracket: `[0.7941, 1.4093]`; also below 2.0, so bisection clamped to `contact_x = +0.300000`.
- Final main `R_true = 1.409` (> 1.0, muscle-side-down in the static kernel torque sense).
- `a_m = 0.67493`, `a_l = 0.07510`.

### Control

- Used the same heavy-muscle geometry.
- Clearance-limited fulcrum position `cx = -0.300000`.
- Final control `R_true = 0.794` (< 1.0, load-side-down in the static sense).
- `a_m = 0.07493`, `a_l = 0.67510`.

## 8000-tick free-evolution results

### Main run

- `load_gain` remained **negative** for the entire run (load end dropped).
- Max `load_gain = 0.0000` at tick 0; final `load_gain ≈ -0.320`.
- Settled lever angle ≈ **-61.8°** (negative = load-side-down / muscle-side-up).
- Fulcrum gap opened from the print gap (~0.048) to a steady ~0.108 lu; never exceeded `r_c`, so `recovery_ok = True`.
- All bodies stayed single-cluster; plate drift = 0.

### Control run

- Max `load_gain = 0.0198` at tick 200, well below the 0.05 bar; final `load_gain ≈ -0.276`.
- Settled lever angle ≈ **-64.6°** (negative = load-side-down).
- Fulcrum gap stayed small (~0.035 lu).
- All bodies stayed single-cluster; plate drift = 0.

## Falsifier verdicts

| falsifier | main | control |
|---|---|---|
| (a) LIFT — main load gain ≥ 0.10 | **FAIL** (max 0.0000) | skipped |
| (b) HOLD — control load gain ≤ 0.05 | skipped | **PASS** (max 0.0198) |
| (c) BALANCE — settled sign matches `sign(R_true - 1)` | **FAIL** | **PASS** |
| (d) INTEGRITY — one cluster each | PASS | PASS |

### BALANCE detail

- **Main:** `R_true = 1.409` predicts positive settled angle (muscle-side-down). Observed settled sign = **-1**. Falsified.
- **Control:** `R_true = 0.794` predicts negative settled angle (load-side-down). Observed settled sign = **-1**. Passed.

## Honest assessment

The v4 implementation is faithful to the requested protocol: the 4×4×16 arm was restored, the heavy-muscle contingency fired exactly once, and the new BALANCE metric was applied. However, the **main-run theory is falsified**.

The static kernel torque ratio `R_true = 1.409` does **not** predict the dynamic settled direction. Both main and control settled with the load side down (negative angle), even though main had `R_true > 1`. The lever did not lift the load; the load end dropped by ~0.32 lu and stayed there. INTEGRITY and HOLD are satisfied, but LIFT and BALANCE fail for the main run.

This is the expected honest outcome given the geometry: the 4×4×16 arm is heavy, the 5³ droplet still cannot push `R_true` near the original 2.0 target, and the dynamic settling is dominated by effects not captured by the cold-print static torque ratio.

## Artifacts produced

- `LightEngine/output/print_lever_v4_log.txt`
- `LightEngine/output/print_lever_v4_control_log.txt`
- Render frames (if rendering succeeded): `lever_v4lever_begin.png`, `lever_v4lever_end.png`, `lever_v4_controllever_control_begin.png`, `lever_v4_controllever_control_end.png`

## Test status

```bash
python -m pytest LightEngine/tests -q
# 118 passed, 17 warnings in 10.31s
```
