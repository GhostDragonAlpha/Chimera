# theLever v3 report

Run tags: `lever_v3` (main) and `lever_v3_control` (control).  
Tracked logs:
- `LightEngine/output/print_lever_v3_log.txt`
- `LightEngine/output/print_lever_v3_control_log.txt`

## v3 design change

The fulcrum block is now **pinned to the ground plate** (grain id 1 is part of
the pin_mask).  The static torque ratio `R_true` is therefore computed only
over the free grains: lever, droplet, and load.  The pinned fulcrum is the
skeletal pivot, matching the joint v2 pillar precedent.

## Print geometry

| body | dimensions | notes |
|---|---|---|
| ground plate | 6 x 6 | pinned at z = 0 |
| fulcrum | 4 x 4 x 4 | pinned, seated d_eq above plate |
| lever | 2 x 1 x 18 | L = 0.85 lu |
| muscle droplet | 4^3 | centered at x = muscle_end + 0.30 L |
| load block | 4^3 | centered on the load (right) end of the lever |

## Route decision

The standard 4^3 droplet was tried first.  The bisection for `R_true = 2.0`
landed at:

```text
main final: contact_x=0.263492  R_true=2.0026
load-end margin = 0.16151 (derived bar = 0.10000)
route: STANDARD (4^3 droplet) -- contact clears the bracket edge by the derived margin
```

The contact point is **0.1615 lu** from the load end, well above the 2-lattice-
step (0.10 lu) bar, so the heavy-muscle (5^3) route was **not** needed.

## Derived numbers at print

### Main

```text
d_eq                 = 0.04840
contact_x            = 0.26349
a_m                  = 0.68951
a_l                  = 0.16136
F_m                  = 335.438
W_L                  = 48.742
R_static             = 29.408
R_true               = 2.003
margin_to_load_end   = 0.16151
```

### Control

```text
d_eq                 = 0.04840
contact_x            = -0.35000
a_m                  = 0.07602
a_l                  = 0.77485
F_m                  = 335.438
W_L                  = 48.742
R_static             = 0.675
R_true               = 0.912
margin_to_load_end   = 0.16151
```

## Run parameters

```text
N = 264
seed = 20260806
dt   = 0.0005
ticks = 8000
```

## Results

### Main (`lever_v3`)

Verdict block (verbatim):

```text
[lever] LEVER FALSIFIERS:
  (a) LIFT      : FAIL  max load_gain=0.0000 at tick=0 (bar 0.1000) recovery_ok=True
  (b) HOLD      : skipped (main)
  (c) BALANCE   : FAIL  R_true=2.003 early_angle_sign=-1 predicted=1 band=[1.800, 2.200]
  (d) INTEGRITY : PASS  max clusters droplet/fulcrum/lever/load=1/1/1/1 plate_drift=0.000000
```

Load-end trajectory:

```text
tick    load_gain    angle
   0    +0.0000      +0.03 deg
 200    -0.0119      +0.95 deg
 400    -0.1449      -2.26 deg
 600    -0.1724      -5.61 deg
 800    -0.1731      -3.67 deg
1000    -0.1715      +5.64 deg
1200    -0.1626     +26.54 deg
2000    -0.1612     +23.54 deg
4000    -0.1661     +20.41 deg
8000    -0.1661     +20.13 deg
```

### Control (`lever_v3_control`)

Verdict block (verbatim):

```text
[lever_control] LEVER FALSIFIERS:
  (a) LIFT      : skipped (control)
  (b) HOLD      : PASS  max load_gain=0.0216 at tick=200 (bar 0.0500)
  (c) BALANCE   : FAIL  R_true=0.912 early_angle_sign=1 predicted=-1 band=[0.500, 1.050]
  (d) INTEGRITY : PASS  max clusters droplet/fulcrum/lever/load=1/1/1/1 plate_drift=0.000000
```

Load-end trajectory:

```text
tick    load_gain    angle
   0    +0.0000      +0.03 deg
 200    +0.0216      +2.13 deg
 400    -0.0074      +2.68 deg
 600    -0.0807      +7.17 deg
 800    -0.2123     -31.26 deg
1000    -0.3112     -62.67 deg
2000    -0.2113    -170.23 deg
4000    -0.2108    -158.74 deg
8000    -0.2193    -149.34 deg
```

## Test status

```bash
python -m pytest LightEngine/tests -q
```

```text
118 passed, 16 warnings in 9.26s
```

New/updated tests:
- `test_lever_pinned_bodies`: plate and fulcrum pinned, nothing else.
- `test_lever_main_contact_margin`: main contact clears the lever end by
  >= 2 lattice steps (or records the heavy-muscle route).
- `test_lever_counts` tolerates either 4^3 or 5^3 droplet counts.

## Diagnosis

### Does the anchored pivot make the main LIFT?

**No.**  With the fulcrum pinned, the lever does settle into a sustained
muscle-down rotation (angle ~ +20°), which is the direction `R_true > 1`
predicts.  However, the load-end **absolute z** still falls by ~0.166 lu.  The
rotation is therefore not converted into an absolute lift of the load.

What absorbs the rotation:

1. **The thin lever bends under the load block.**  The load face of the lever
   is the measurement point for `load_gain`.  Even though the load face tilts
   upward relative to the muscle face, its absolute z drops because the lever
   sags between the pinned fulcrum and the load.
2. **The fulcrum gap stays seated (~0.041 lu).**  There is no fulcrum roll or
   sink in v3, so the load-end drop is not caused by pivot migration.  The
   lever simply does not behave as a rigid bar: a 2×1 grain cross-section is
   too compliant to transfer the muscle torque into a load-end rise without
   large elastic deformation.
3. **The load block remains in contact** (`contact_ratio` stays positive,
   ~6–7), so the load is being carried; it is not falling off.  The load and
   the load face of the lever move down together.

In short: the pivot is now anchored, the static torque correctly predicts the
*settled* rotation direction, but the 2×1 lever is not stiff enough to lift
the load in absolute z.  The machine twists instead of lifting.

### Does the control HOLD?

**Yes.**  `max load_gain = 0.0216` is below the 0.05 bar.  After a short
positive-angle transient, the control settles into a sustained load-side-down
rotation (~ -150°), which is the direction `R_true < 1` predicts.

### BALANCE failures

Both BALANCE verdicts fail on the **first-600-tick median** criterion:

- Main: the median angle in the first 600 ticks is negative (load-down)
  because the load block presses the thin lever down before the muscle
  droplet's pull dominates.  The sustained direction after ~1000 ticks is
  positive (muscle-down).
- Control: the median angle in the first 600 ticks is positive (muscle-down)
  because the droplet's initial pull acts before the long load arm wins.  The
  sustained direction after ~800 ticks is negative (load-down).

Thus the static torque predicts the **settled** tip direction in both cases,
but not the first transient captured by the 600-tick window.

## Files produced

```text
LightEngine/output/print_lever_v3_log.txt
LightEngine/output/print_lever_v3_control_log.txt
LightEngine/output/lever_v3_lever_begin.png
LightEngine/output/lever_v3_lever_end.png
LightEngine/output/lever_v3_control_lever_control_begin.png
LightEngine/output/lever_v3_control_lever_control_end.png
LightEngine/output/lever_v3_report.md
```

## Suggested next steps

- The v3 law is confirmed in one direction: **a pinned fulcrum removes the
  rolling-pivot failure** and the kernel torque predicts the settled rotation.
- The remaining failure is mechanical: the 2×1 lever is too compliant.  The
  next derived step is to increase lever bending stiffness (e.g. 2×2 or 3×2
  cross-section, or a shorter span) **without** changing the muscle size or
  arm length until the standard-muscle route is exhausted.
- If a stiffer lever still cannot meet the 0.10 absolute lift bar, the bar
  itself may need to be re-derived from the actual arc geometry of the chosen
  lever, rather than fixed at two lattice steps.
