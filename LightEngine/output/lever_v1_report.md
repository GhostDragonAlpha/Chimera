# theLever v1 print-run report

Runs:
```bash
python -u LightEngine/demo_seed.py --structure lever --lever-ticks 8000 --tag lever_v1
python -u LightEngine/demo_seed.py --structure lever --lever-control --lever-ticks 8000 --tag lever_v1_control
```

Output logs:
- `LightEngine/output/print_lever_v1_log.txt`
- `LightEngine/output/print_lever_v1_control_log.txt`

Frames:
- `LightEngine/output/lever_v1_lever_begin.png`, `lever_v1_lever_end.png`
- `LightEngine/output/lever_v1_control_lever_control_begin.png`, `lever_v1_control_lever_control_end.png`

## 1. Construction

- `seed_structures.lever(control=False|True, spacing=0.05, seed=...)` builds a pinned 6×6 ground plate, a 4×4×4 cushion fulcrum, a 4×4×16 bone lever laid horizontally, a 4³ muscle droplet under the lever’s left end, and a 4³ load block on the lever’s right end.
- In `control=True` the fulcrum is shifted left by `L/4`, halving the muscle arm `a_m` and increasing the load arm `a_l` while keeping the droplet and load positions unchanged.
- The droplet’s right-face x-position is derived by bisection so the main-run static balance ratio `R = F_m·a_m / (W_L·a_l)` lands near 2.0.
- Only the ground plate is pinned; everything else free-evolves under the Velocity-Verlet kernel.

## 2. Derived parameters

| parameter | main | control |
|-----------|------|---------|
| `d_eq`    | 0.04840 | 0.04840 |
| `a_m`     | 0.37500 | 0.18750 |
| `a_l`     | 0.37502 | 0.56252 |
| `F_m`     | 89.883 | 89.883 |
| `W_L`     | 44.960 | 44.960 |
| `R`       | **1.999** | **0.666** |

The printed ratios satisfy the static spec (`R ≥ 1.8` main, `R ≤ 1.1` control).

## 3. Verbatim verdict blocks

### Main run (`lever_v1`)

```
[lever] LEVER FALSIFIERS:
  (a) LIFT      : FAIL  max load_gain=0.0190 at tick=200 (bar 0.1000) recovery_ok=True
  (b) HOLD      : skipped (main)
  (c) BALANCE   : PASS  liftoff tick=0 F_m*a_m/(W_L*a_l)=1.333 (band [0.500, 2.000])
  (d) INTEGRITY : PASS  max clusters droplet/fulcrum/lever/load=1/1/1/1 plate_drift=0.000000
```

### Control run (`lever_v1_control`)

```
[lever_control] LEVER FALSIFIERS:
  (a) LIFT      : skipped (control)
  (b) HOLD      : PASS  max load_gain=0.0263 at tick=200 (bar 0.0500)
  (c) BALANCE   : skipped (control)
  (d) INTEGRITY : FAIL  max clusters droplet/fulcrum/lever/load=2/1/1/1 plate_drift=0.000000
```

## 4. Load-end height trajectories

### Main run

| tick | load_gain (lu) | angle (deg) | fulcrum_gap | plate_F | contact_ratio | clusters (drop/fulcrum/lever/load) |
|------|----------------|-------------|-------------|---------|---------------|-------------------------------------|
| 0    | +0.0000        | -0.02       | 0.0686      | 937.82  | -24.852       | 1/1/1/1 |
| 200  | **+0.0190**    | 4.39        | 0.0520      | 1143.08 | -3.332        | 1/1/1/1 |
| 400  | -0.0997        | -7.93       | 0.0724      | 1540.68 | 21.966        | 1/1/1/1 |
| 1000 | -0.3186        | 23.00       | 0.0635      | 2498.18 | 18.814        | 1/1/1/1 |
| 2000 | -0.3332        | 36.09       | 0.0476      | 284.85  | 5.936         | 1/1/1/1 |
| 4000 | -0.3325        | 33.72       | 0.0500      | 302.63  | 6.003         | 1/1/1/1 |
| 6000 | -0.3337        | 34.57       | 0.0502      | 198.18  | 6.976         | 1/1/1/1 |
| 8000 | -0.3332        | 34.17       | 0.0503      | 113.85  | 6.845         | 1/1/1/1 |

### Control run

| tick | load_gain (lu) | angle (deg) | fulcrum_gap | plate_F | contact_ratio | clusters (drop/fulcrum/lever/load) |
|------|----------------|-------------|-------------|---------|---------------|-------------------------------------|
| 0    | +0.0000        | -0.02       | 0.0604      | 798.59  | -23.741       | 1/1/1/1 |
| 200  | **+0.0263**    | 7.70        | 0.0416      | 1022.46 | 4.342         | 1/1/1/1 |
| 400  | -0.0786        | -4.44       | 0.0257      | 1510.97 | 63.995        | 1/1/1/1 |
| 1000 | -0.3278        | 10.32       | 0.0267      | 1958.35 | 16.636        | 1/1/1/1 |
| 2000 | -0.3351        | 61.20       | 0.0660      | 89.69   | 4.233         | 2/1/1/1 |
| 4000 | -0.3350        | 51.21       | 0.0572      | 72.19   | 2.242         | 1/1/1/1 |
| 6000 | -0.3349        | 49.65       | 0.0571      | 51.22   | 3.373         | 2/1/1/1 |
| 8000 | -0.3356        | 48.80       | 0.0555      | 144.61  | 3.054         | 1/1/1/1 |

Key observations:
- **Main never lifts.** The largest upward excursion is `+0.0190` at tick 200, far below the `0.10` bar. After tick 400 the load end is always below its print height and settles near `-0.333` lu.
- **Control holds.** The largest upward excursion is `+0.0263` at tick 200, below the `0.05` bar. The load end also settles near `-0.335` lu.
- The lever rotates in both runs (main settles near 34°, control near 50°), but the rotation is dominated by the muscle end sinking; the absolute height of the load end decreases, not increases.
- The fulcrum gap collapses to roughly `0.05` lu and stays there, so the fulcrum contact neither loses nor recovers—it simply compresses.

## 5. Two-sided result

The falsifier pair is **partially satisfied**:

- `HOLD` (control) → **PASS**.
- `LIFT` (main) → **FAIL**.

This is the measured outcome. The static ratio `R = 2.0` is correctly derived, but the dynamic run does not realize the predicted load-end rise.

## 6. Surprises

1. **The whole lever sinks rather than pivots.** The muscle droplet pulls the left end down, the fulcrum compresses, and the entire lever-load assembly subsides. The load end ends ~0.33 lu lower than its print height in both configurations.
2. **The muscle droplet splits in the control run.** Cluster counts show the droplet as two clusters for much of the run (e.g., ticks 1200–2200, 2800–3600, 4400–5000, 6000–6400, 7200–7600). The load block, lever, and fulcrum remain single clusters; the plate pins hold.
3. **`BALANCE` passes trivially at tick 0.** The static ratio at the print configuration is `1.333`, inside the `[0.5, 2.0]` band, but this check does not correspond to a liftoff event during motion.
4. **Rendered frames are unresolved.** The saved begin/end PNGs are small, low-contrast blobs; the default viewport scale does not resolve the lever geometry.

## 7. Diagnosis

The v1 implementation encodes the correct static mechanical-advantage numbers, but the dynamic response refutes the lifting prediction. The failure mode is not “insufficient muscle force” or “load too heavy” in the static sense—`R = 2.0` gives adequate static leverage. Instead, the lever behaves like a soft beam on a compressible fulcrum: the muscle contraction is absorbed by fulcrum compression and sag rather than by a clean pivot, so the load end never rises.

The control run behaves as a stiffer, more steeply rotated version of the same failure, which is why `HOLD` passes. The droplet splitting is a secondary integrity issue caused by shear between the muscle droplet and the lever.

## 8. Follow-up questions

- Can the fulcrum be made stiff enough to act as a true pivot without the whole lever sinking?
- Should the prediction be revised from “load end rises absolutely” to “load end rises relative to the muscle end / ground” once sinking is accounted for?
- Does the droplet need additional cohesion or a different placement to avoid splitting in the control configuration?
