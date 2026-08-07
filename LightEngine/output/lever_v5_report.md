# The Lever v5 — Implementation & Validation Report

## 1. What was requested

- Hollow 4×4 tube arm (1-grain shell, 2×2 void, 192 grains at the default 16-ring length).
- Standard 4³ muscle droplet only — no heavy-muscle contingency.
- Static gate: `R_true = tau_muscle / tau_load` must reach `2.0 ± 0.1` at a fulcrum contact at least `0.10 lu` off the bracket edge.
- If the 16-ring tube fails, shorten the arm while keeping the tube cross-section until the gate passes, and report both sweep traces.
- If the gate passes, run main + control 8000-tick dynamics sequentially and log to:
  - `LightEngine/output/print_lever_v5_log.txt`
  - `LightEngine/output/print_lever_v5_control_log.txt`
- Deliver `lever_v5_report.md`.

## 2. Geometry changes made

| Item | v5 value | Notes |
|------|----------|-------|
| Tube cross-section | 4×4 with 2×2 void | 12 grains per ring |
| Default length | 16 rings (192 grains) | Shortened automatically by the gate if needed |
| Muscle droplet | 4³ standard | seated on the ground plate |
| Muscle insertion | `x = muscle_end + 0.625 · L` | Derived from a sweep so that both main (`R≈2`) and control (`R≈0.75`) are reachable off-edge |
| Vertical seating | Tube bottom face at `fulcrum_top_z + d_eq` | Fixes the initial lever-fulcrum and load-lever cushion gaps to `d_eq` |

The insertion point was moved from the previous `0.30 L` to `0.625 L` because, with the tube correctly seated, the old position left the control ratio above `1.0` for every integer length. A parameter sweep over insertion fraction `α ∈ [0,1]` and length `6…16` showed feasible two-sided gates around `α ≈ 0.6`; `0.625` was chosen as a stable derived value.

## 3. Static gate result (demo seed = 20260806)

The gate sweeps lengths from 16 down to 6. The 16-, 15-, and 14-ring tubes could not reach `R = 2.0`. The 13-ring tube passed:

```text
[lever] v5 static gate: tube length=16 rings, L=0.750 lu, bracket=[-0.300000, 0.300000]
  bracket cx=-0.300000 -> R_true=0.6675
  bracket cx=0.300000 -> R_true=1.6299
  [fail] bracket R range [0.6675, 1.6299] cannot reach 1.90

[lever] v5 static gate: tube length=15 rings, L=0.700 lu, bracket=[-0.275000, 0.275000]
  bracket cx=-0.275000 -> R_true=0.6327
  bracket cx=0.275000 -> R_true=1.5779
  [fail] bracket R range [0.6327, 1.5779] cannot reach 1.90

[lever] v5 static gate: tube length=14 rings, L=0.650 lu, bracket=[-0.250000, 0.250000]
  bracket cx=-0.250000 -> R_true=0.6060
  bracket cx=0.250000 -> R_true=0.5916
  [fail] bracket R range [0.5916, 0.6060] cannot reach 1.90

[lever] v5 static gate: tube length=13 rings, L=0.600 lu, bracket=[-0.225000, 0.225000]
  bracket cx=-0.225000 -> R_true=0.5767
  bracket cx=0.225000 -> R_true=4.9436
  candidate contact_x=0.050177 R_true=2.0000 margin_to_load_end=0.24982
  [pass] static gate passed at length=13
```

Control placement on the same 13-ring geometry:

```text
[lever] v5 control sweep: R(cx_min)=0.5767, R(cx_max)=4.9436
[lever] v5 control final: contact_x=-0.052225 R_true=0.7500
  margin_to_load_end=0.35222 margin_to_muscle_end=0.24778
```

Both main and control contacts clear the bracket edges by more than `0.10 lu`.

## 4. Unit-test verification

```bash
python -m pytest LightEngine/tests -q
```

Result: **118 passed, 16 warnings**.

All lever-specific tests pass:
- `test_lever_counts`
- `test_lever_pinned_bodies`
- `test_lever_no_shared_positions`
- `test_lever_main_ratio`
- `test_lever_main_contact_margin`
- `test_lever_control_ratio`
- `test_lever_control_weaker_arm`
- `test_lever_cushion_contacts`
- `test_lever_determinism`

## 5. 8000-tick dynamics

The static gate passed, so main and control were run sequentially in the background:

```bash
python LightEngine/demo_seed.py --structure lever
python LightEngine/demo_seed.py --structure lever --lever-control
```

Logs:
- `LightEngine/output/print_lever_v5_log.txt`
- `LightEngine/output/print_lever_v5_control_log.txt`

### 5.1 Main run (`R_true = 2.000`)

The load end did **not** lift. The settled lever angle is negative (load-side-down), opposite to the static-torque prediction:

```text
[lever] LEVER FALSIFIERS:
  (a) LIFT      : FAIL  max load_gain=0.0000 at tick=0 (bar 0.1000) recovery_ok=True
  (b) HOLD      : skipped (main)
  (c) BALANCE   : FAIL  R_true=2.000 settled_angle_sign=-1 predicted=1 (last 8/41 samples)
  (d) INTEGRITY : PASS  max clusters droplet/fulcrum/lever/load=1/1/1/1 plate_drift=0.000000
  (e) SAG       : not detected  settled_sign=-1 max_load_gain=0.0000
```

Interpretation: the cold-print torque ratio reaches `2.0`, but during free evolution the load side still drops. The tube stays in one piece and the plate pins hold, so the failure is in the muscle/load balance, not structural integrity.

### 5.2 Control run (`R_true = 0.750`)

Control behaved as predicted: the load end stayed low and the settled angle matched `sign(R_true - 1)`.

```text
[lever_control] LEVER FALSIFIERS:
  (a) LIFT      : skipped (control)
  (b) HOLD      : PASS  max load_gain=0.0000 at tick=0 (bar 0.0500)
  (c) BALANCE   : PASS  R_true=0.750 settled_angle_sign=-1 predicted=-1 (last 8/41 samples)
  (d) INTEGRITY : PASS  max clusters droplet/fulcrum/lever/load=1/1/1/1 plate_drift=0.000000
  (e) SAG       : skipped (control)
```

## 6. Files touched

- `LightEngine/seed_structures.py`
  - `lever()` rewritten for the v5 hollow tube.
  - Static gate shortens the arm from 16 rings downward.
  - Standard 4³ droplet only; heavy-muscle route removed.
  - Insertion fraction set to `0.625 L`.
  - Tube seated so its bottom face is `d_eq` above the fulcrum top.
  - Direction-aware bisection for `R_true`.
- `LightEngine/demo_seed.py`
  - v5 header and SAG falsifier retained/updated.
  - `_print_lever_verdict` reports SAG detection.
- `LightEngine/tests/test_structures.py`
  - Lever tests updated for tube grain count (`n_lever = lever_len * 12`), standard route, off-edge margin, and `R_true` ranges.
- `lever_v5_report.md` (this file).

## 7. Conclusion

- The v5 static gate is implemented and passes for the demo seed at **13 rings**.
- Unit tests pass.
- The 8000-tick **control** run passes all applicable falsifiers.
- The 8000-tick **main** run fails the LIFT and BALANCE falsifiers: the static `R_true = 2.0` is reachable, but the free-evolution lever tips load-side-down and the load end does not rise. This is the honest measured result; no further ad-hoc tuning was performed.
