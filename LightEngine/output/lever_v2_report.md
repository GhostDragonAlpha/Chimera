# theLever v2 report

Run tags: `lever_v2` (main) and `lever_v2_control` (control).  
Generated: 2026-08-07 from `LightEngine/demo_seed.py --structure lever`.

## Print geometry

| body | dimensions | notes |
|---|---|---|
| ground plate | 6 x 6 | pinned at z = 0 |
| fulcrum | 4 x 4 x 4 | cushion-seated on plate, x-center derived by bisection |
| lever | 2 x 1 x 18 | light rod, bottom face d_eq above fulcrum top; L = 0.85 lu |
| muscle droplet | 4^3 | centered at x = muscle_end + 0.30 L |
| load block | 4^3 | centered on the load (right) end of the lever |

The droplet offset was moved from L/3 to **0.30 L** after torque scans showed it
gives a usable R_true ceiling (~2.0) while still clearing the fulcrum in the
control placement.

## Derivation: kernel torque ratio R_true

`seed_structures.lever()` bisects the fulcrum contact x-position until the full
kernel static torque about the fulcrum contact point is R_true = tau_muscle /
tau_load ~= 2.0.

For seed `20260806`:

```text
bracket cx=-0.350000 -> R_true=0.8635
bracket cx=+0.350000 -> R_true=1.9819
main final: contact_x=+0.350000  R_true=1.9819
control clearance: contact_x=-0.350000  R_true=0.8635
```

## Derived numbers at print

### Main

```text
d_eq      = 0.04840
a_m       = 0.77602
a_l       = 0.07485
F_m       = 335.438
W_L       = 48.742
R_static  = 71.348
R_true    = 1.982
```

### Control

```text
d_eq      = 0.04840
a_m       = 0.07602
a_l       = 0.77485
F_m       = 335.438
W_L       = 48.742
R_static  = 0.675
R_true    = 0.864
```

## Run parameters

```text
N = 264
seed = 20260806
dt   = 0.0005
ticks = 8000
```

## Results

### Main (`lever_v2`)

The muscle side tips down as predicted by R_true > 1.  The lever remains a
single cluster and the fulcrum contact stays near the seated band after an
initial transient.  The load end, however, does **not** rise in absolute height:
`max load_gain = 0.0000` (bar 0.1000).

Final state at tick 8000:

```text
load_gain = -0.2373
angle     =  57.62 deg (muscle end down)
gap       =  0.0672
clusters  =  1/1/1/1
```

Verdicts:

| falsifier | result | note |
|---|---|---|
| (a) LIFT | **FAIL** | load end never rises >= 0.10 lu |
| (c) BALANCE | **PASS** | R_true=1.982, early angle sign = +1 matches prediction |
| (d) INTEGRITY | **PASS** | all bodies one cluster, plate pins hold |

### Control (`lever_v2_control`)

The control run holds the load end within the allowed 0.05 lu rise
(`max load_gain = 0.0216`), but the early tip direction is muscle-side-down
instead of the load-side-down predicted by R_true < 1.

Final state at tick 8000:

```text
load_gain = -0.1585
angle     =  88.85 deg (muscle end down)
gap       =  0.0648
clusters  =  1/1/1/1
```

Verdicts:

| falsifier | result | note |
|---|---|---|
| (b) HOLD | **PASS** | max load_gain = 0.0216 <= 0.05 |
| (c) BALANCE | **FAIL** | R_true=0.864 predicts -1, early angle sign = +1 |
| (d) INTEGRITY | **PASS** | all bodies one cluster, plate pins hold |

## Test status

`python -m pytest LightEngine/tests -q`

```text
117 passed, 15 warnings in 9.10s
```

The structure tests were updated for the new point count
(`2 * 1 * 18 = 36` lever grains) and for the thin-lever cushion-gap
measurement.

## Observations

1. **R_true predicts the main direction correctly.**  With R_true ~2 the
   muscle side goes down and the load side rises relative to the lever center.
2. **The main does not lift the load in absolute z.**  Because R_true = 2 is
   reached with the fulcrum very close to the load end, the load arm is only
   ~0.075 lu.  The lever rotates about a point near the load, so the load end
   moves in a tight arc and the whole lever also sinks under the droplet pull.
3. **The control tips muscle-side-down, contradicting R_true < 1.**  The
   fulcrum is placed at the leftmost allowed position (clearing the droplet by
   d_eq).  The static torque says load-side-down should win, but the free
   fulcrum block rolls/translate under the lever and the dynamics settle with
   the muscle end down.  This suggests the current control placement does not
   produce a clean quasi-static balance; the fulcrum is not acting as a fixed
   pivot.
4. **No fragmentation.**  The 2 x 1 cross-section survives 8000 ticks as one
   cluster in both runs.

## Files produced

```text
LightEngine/output/lever_v2.log
LightEngine/output/lever_v2_control.log
LightEngine/output/lever_v2_lever_begin.png
LightEngine/output/lever_v2_lever_end.png
LightEngine/output/lever_v2_control_lever_control_begin.png
LightEngine/output/lever_v2_control_lever_control_end.png
```

## Suggested next steps

- Decide whether the LIFT bar should stay at 0.10 lu for this geometry, or
  whether the v2 prediction should be reframed in terms of relative angle /
  load-end-rise-above-muscle-end rather than absolute z.
- Investigate the control dynamics: pin the fulcrum or move the control
  fulcrum/contact to a position where the load-side torque actually dominates
  the transient (may require a smaller droplet, larger load, or a different
  muscle insertion point).
- If the 2 x 1 lever is accepted, the BALANCE falsifier for the control needs
  either a different early-window definition or a geometry change so that
  `R_true < 1` reliably produces a load-side-down first-sustained tip.
