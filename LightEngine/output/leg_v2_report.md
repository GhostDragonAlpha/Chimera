# theLeg v2 report

## What changed from v1

v1 failed because the free droplet muscle was pulled up into the lever tip,
reversing the opening torque.  v2 makes three structural changes:

1. **Anchor the droplet.**  The `4^3` droplet is now pinned to the well floor
   (`grain_id=0` grains are in `pin_mask`).  It acts as a fixed anchor rather
   than a free muscle mass.
2. **Derive the well depth.**  The well floor is chosen by bisection so that
   the rotating muscle end of the lever stays at least `d_eq = 0.0484` lu away
   from the anchored droplet over the whole allowed arc `[0, theta_stop]`.
3. **Lengthen the tendon rod.**  The rod is a free `2x2` shaft whose top face
   sits `d_eq` below the arm-tip underside and whose bottom face sits `d_eq`
   above the droplet apex.  Its layer count is derived from the well depth.
4. **Arc gate.**  The cold static gate is replaced by sampling the kernel
   static torque ratio `R_true(theta)` over `[0, theta_stop]`, pricing in
   **taut** (rod transmits the droplet pull) and **slack** (rod grains moved
   far away, no transmission).

## Geometry derivation

- `d_eq = 0.04840`, spacing `d = 0.05`.
- Lever: 13-ring `4x4` hollow tube, muscle tip at `x = -0.30`.
- Fulcrum top at `z = 0.1984`; lever underside at `z = 0.2468`.
- Well-floor bisection used the conservative rightmost contact
  (`contact_x = load_end_x - 0.10 = 0.20`) because it produces the largest
  arc swing.  The shallowest valid well floor was `z = -0.10` (v1 depth), with
  a minimum arc clearance of `0.0543` lu (just above `d_eq`).
- With this well floor the droplet apex is at `z = 0.0984`, so the target rod
  span is only two lattice steps; the rod is `2x2x2` (`n_rod = 8`).

## Arc gate

For each candidate `contact_x` in `[muscle_end + tube_half_width, load_end - 0.10]`:

- `theta_stop` is derived from the tip underside reaching `droplet_apex + d_eq`.
- The lever and load are rotated clockwise about the fulcrum contact.
- **Taut:** rod grains are placed evenly along the straight line from the fixed
  droplet anchor to the rotated arm-tip underside.
- **Slack:** rod grains are moved to `(0, 0, 1e6)`.
- `_R_true_at_print` is called for both prices at each theta sample.

Selection:

- **Main:** leftmost `contact_x` with `min(R_taut) >= 1.0`.
- **Control:** leftmost `contact_x` with `R_slack(0) in [0.5, 1.0]` and
  `max(R_slack) <= 1.0`.

Derived contacts:

| run     | contact_x | R_true(theta=0) | theta_stop |
|---------|-----------|-----------------|------------|
| main    | -0.09750  | 1.003 (taut)    | 27.79 deg  |
| control | -0.15488  | 0.620 (slack)   | 38.16 deg  |

## Test results

`python -m pytest LightEngine/tests -q`:

```
130 passed, 6 warnings in 252.94s
```

Leg-specific tests updated/added:

- droplet is pinned
- well depth is derived (no longer hard-coded to `-2d`)
- rod spans from arm-tip underside to droplet apex
- main arc trace satisfies `min(R_taut) >= 1.0`
- control arc trace satisfies `R_slack(0) in [0.5, 1.0]` and `max(R_slack) <= 1.0`
- arc trace dict contains `theta_stop`, `thetas`, `R_taut`, `R_slack`

## 8000-tick dynamics

Commands:

```bash
python LightEngine/demo_seed.py --structure leg --tag leg_v2
python LightEngine/demo_seed.py --structure leg --leg-control --tag leg_v2
```

Logs:

- `LightEngine/output/print_leg_v2_log.txt`
- `LightEngine/output/print_leg_v2_control_log.txt`
- PNG frames: `leg_v2_begin.png`, `leg_v2_end.png`,
  `leg_v2_control_begin.png`, `leg_v2_control_end.png`.

### Main run verdict

```
(a) LIFT    : FAIL  max load_gain=0.0017 at tick=200 (bar 0.1000)
(b) HOLD    : skipped (main)
(c) BALANCE : FAIL  R_true=1.003 settled_angle_sign=-1 predicted=1
(d) INTEGRITY: PASS
(e) SAG     : not detected
(f) SLACK   : PASS  rod_slack_frac=0.00
```

The lever transiently reached `+17.07` deg (muscle-side-down) but settled at
`-8.18` deg (load-side-down).  The load end dropped `0.28` lu.  The rod stayed
mostly in tension (`tension=0.95`), so the new SLACK falsifier passes, but the
margin on the arc gate is too thin: a cold `R_true` of `1.003` is not enough to
overcome the transient dynamics and settle muscle-side-down.

### Control run verdict

```
(a) LIFT    : skipped (control)
(b) HOLD    : PASS  max load_gain=0.0053 at tick=200 (bar 0.0500)
(c) BALANCE : PASS  R_true=0.620 settled_angle_sign=-1 predicted=-1
(d) INTEGRITY: PASS
(e) SAG     : skipped (control)
(f) SLACK   : skipped (control)
```

The control lever settled load-side-down at `-38.62` deg, matching the slack
prediction.  HOLD passes.

## Interpretation

- Pinning the droplet fixed the v1 failure mode: droplet apex stayed constant
  at `z = 0.0995` for the entire run.
- The arc gate was implemented exactly as specified and produced a valid
  two-sided pair of contacts.
- The main criterion `min_R_taut >= 1.0` is insufficient in practice; the
  dynamics settles load-side-down despite the static ratio being barely above
  unity.  A stronger arc-gate threshold (e.g. `min_R_taut >= 1.2`) or a longer,
  softer tendon rod (requiring a deeper well) is likely needed for a passing
  main run.
- The SLACK falsifier is operational and correctly reports that the main rod
  remains engaged (`rod_slack_frac = 0.00`).

## Files touched

- `LightEngine/seed_structures.py` — rewrote `leg()` for v2 geometry, derived
  well depth, anchored droplet, lengthened rod, arc gate.
- `LightEngine/demo_seed.py` — updated `_run_leg`, `_print_leg_verdict`,
  `leg_main`, and `--leg-control/--leg-ticks` help for v2 telemetry and the
  SLACK falsifier.
- `LightEngine/tests/test_structures.py` — updated leg tests for v2 counts,
  pinned droplet, derived depth, rod span, and arc-gate traces.
- `LightEngine/output/print_leg_v2_log.txt`
- `LightEngine/output/print_leg_v2_control_log.txt`
- `LightEngine/output/leg_v2_report.md`
- `LightEngine/output/leg_v2_begin.png`
- `LightEngine/output/leg_v2_end.png`
- `LightEngine/output/leg_v2_control_begin.png`
- `LightEngine/output/leg_v2_control_end.png`

No git commit was made.
