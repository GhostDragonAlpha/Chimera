# theLeg v1 — tendon-routed muscle in a well

## Membrane statement

A captured muscle-bone machine routes the muscle pull through a vertical
2×2 tendon rod that hangs from the arm tip into a well, so the bone never
intersects the free droplet muscle.  The fulcrum contact is derived from the
kernel's own static torque about the pinned fulcrum contact point.

## Prediction

With kernel-verified `R_true = 2.0 ± 0.1` (main) the captured arm tips
muscle-side-down and the load end lifts through at least two lattice steps.
With `R_true ∈ [0.5, 1.0]` (control) the load end tips load-side-down and
never rises more than one lattice step.

## Derived geometry

| Quantity | Value |
|----------|-------|
| Well floor `z` | `-0.10000` lu (`-2d`, `d = 0.05` lu) |
| Tendon rod layers | `2` |
| Rod span | `0.05000` lu (`(2-1)·d`) |
| Rod top `z` | `0.19840` lu (`d_eq` below arm-tip underside) |
| Rod bottom `z` | `0.14840` lu |
| Droplet top `z` (print) | `0.09840` lu |
| Rod-droplet print gap | `0.05000` lu |
| Ground plate + well grains | `188` pinned |
| Droplet grains | `64` (`4³`) |
| Fulcrum grains | `88` (`4³` block + `2×4×1×3` cheeks) |
| Lever grains | `156` (`13` rings × `12` grains) |
| Load grains | `64` (`4³`) |
| Rod grains | `8` (`2×2×2`) |
| Total `N` | `568` |

## Static gate

The off-edge bracket is `[muscle_end + tube_half_width, load_end - tube_half_width]`
= `[-0.225, 0.225]` lu.  The load-end margin constraint is `load_end - contact_x >= 0.10`.

| Run | `contact_x` | `a_m` | `a_l` | `margin_to_load_end` | `R_true` |
|-----|-------------|-------|-------|----------------------|----------|
| main | `-0.21863` | `0.08105` | `0.51846` | `0.51863` | `2.016` |
| control | `-0.22500` | `0.07467` | `0.52484` | `0.52500` | `0.548` |

Both contacts are muscle-ward (`a_m_ctrl < a_m_main`) and the margin constraint is
satisfied with a large safety margin.

## Dynamics summary (`seed = 20260806`, `dt = 0.0005`, `ticks = 8000`)

### Main run

- Initial small muscle-down swing: angle reaches `+14.33°` at tick 200,
  `load_gain` peaks at `+0.0075`.
- System overshoots and settles load-side-down: final angle `≈ -71.76°`,
  final `load_gain ≈ -0.3312`.
- Droplet apex rises from print `0.0995` lu to max `0.1750` lu, then stabilizes
  around `0.1352` lu; minimum arm-tip-to-droplet distance `0.0267` lu.
- Tendon rod is in tension for `93%` of samples after the transient; final rod
  internal force `+5.23` (tension).

### Control run

- Same initial swing, then settles load-side-down: final angle `≈ -80.02°`,
  final `load_gain ≈ -0.3369`.
- Droplet apex range `[0.0995, 0.1744]` lu; minimum arm-tip-to-droplet distance
  `0.0292` lu.
- Tendon rod is in tension for `98%` of samples; final rod internal force
  `+60.65` (tension).

## Falsifier verdicts

### Main

| Falsifier | Result | Notes |
|-----------|--------|-------|
| (a) LIFT | **FAIL** | max `load_gain = +0.0075` at tick 200 (bar `0.1000`) |
| (b) HOLD | skipped | main run |
| (c) BALANCE | **FAIL** | `R_true = 2.016` predicts muscle-down, settled sign is load-down (`-1`) |
| (d) INTEGRITY | **PASS** | all five bodies stay 1 cluster; plate/fulcrum pins hold |
| (e) SAG | not detected | settled sign is load-down |

### Control

| Falsifier | Result | Notes |
|-----------|--------|-------|
| (a) LIFT | skipped | control run |
| (b) HOLD | **PASS** | max `load_gain = +0.0078` (bar `0.0500`) |
| (c) BALANCE | **PASS** | `R_true = 0.548` predicts load-down, settled sign is load-down (`-1`) |
| (d) INTEGRITY | **PASS** | all five bodies stay 1 cluster |
| (e) SAG | skipped | control run |

## Why the main run failed

The kernel static torque at the cold print correctly calls an initial
muscle-side-down opening move, but the chosen contact (`contact_x ≈ -0.2186`)
places the fulcrum extremely close to the muscle end.  The lever is then an
inverted pendulum with a very short muscle arm (`a_m ≈ 0.081`) and a long load
arm (`a_l ≈ 0.518`).  The muscle torque is large enough to start rotation, but
once the arm passes the vertical it is captured by the load-side-down
configuration and does not recover.  The tendon rod stays in tension (the route
works), but the geometry does not provide a stable muscle-down equilibrium.

The static gate therefore needs to move the main contact load-ward enough that
`R_true = 2.0` corresponds to a stable muscle-down settle, not merely an initial
opening move.

## Test suite

```bash
python -m pytest LightEngine/tests -q
```

Result: **128 passed, 6 warnings**.

New leg-specific tests added to `LightEngine/tests/test_structures.py`:

- `test_leg_determinism`
- `test_leg_counts`
- `test_leg_pinned_bodies`
- `test_leg_no_shared_positions`
- `test_leg_well_depth`
- `test_leg_main_ratio`
- `test_leg_main_contact_margin`
- `test_leg_control_ratio`
- `test_leg_control_weaker_arm`
- `test_leg_rod_under_arm_tip`

## Files touched

- `LightEngine/seed_structures.py` — added `leg()` builder.
- `LightEngine/demo_seed.py` — added `_rod_internal_force_z`, `_run_leg`,
  `_print_leg_verdict`, `leg_main()`, and `--leg-control` / `--leg-ticks`
  arguments.
- `LightEngine/tests/test_structures.py` — added ten leg tests.
- `LightEngine/output/print_leg_v1_log.txt` — main run log.
- `LightEngine/output/print_leg_v1_control_log.txt` — control run log.
- `LightEngine/output/leg_v1_begin.png`, `leg_v1_end.png`,
  `leg_v1_control_begin.png`, `leg_v1_control_end.png` — render frames.

## Next step for v2

Move the main fulcrum contact load-ward until the muscle-down settle is stable
while keeping `R_true ∈ [1.9, 2.1]`.  This likely requires reducing the
muscle-to-load torque ratio at small `a_m` (e.g. by increasing the droplet-rod
gap or reducing droplet size) so the same kernel `R_true` is achieved with a
longer muscle arm and shorter load arm.
