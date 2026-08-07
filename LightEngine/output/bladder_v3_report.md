# Bladder v3 (anti-jam neck) print-run report

Run: `python -m LightEngine.demo_seed --structure bladder --bladder-fill fill --bladder-neck antijam --tag bladder_v3`
Output log: `LightEngine/output/print_bladder_v3_log.txt`
Frames: `LightEngine/output/bladder_v3_bladder_begin.png`, `bladder_v3_bladder_end.png`

## 1. Construction

- `seed_structures.bladder(seed, fill="fill", neck="antijam")` builds the v2 filled shell and replaces the v1/v2 one-grain neck at the +z pole with a derived anti-jam neck.
- Neck derivation (granular arching over an orifice):
  - an arch needs at least 2 grains abreast to span (2 spacings),
  - a stable arch can close up to 3 spacings,
  - therefore the neck opens at **4 spacings** — the smallest hole no cushion arch can close.
  - With `muscle_spacing = 0.05`, `neck_diameter = 4 * 0.05 = 0.20`.
- The neck is centered on the +x point of the sphere, facing the right squeeze plate, so the pressure gradient should point through it:
  - `neck_center = (center_x + r_b, 0, 0) = (0.4484, 0, 0)`
  - `neck_axis = (1, 0, 0)`
- The derived neck-corridor tolerance for falsifier (c) is `neck_radius + 1 spacing = 0.10 + 0.05 = 0.15`.
- Resulting counts: N=357, shell=202, content=123, plates=4x4.

## 2. Derived parameters

```
r_b             = 0.20000
d_eq            = 0.04840
s0              = 0.49680
F_hold          = 674.18
2 * F_hold      = 1348.37
Min separation  = 0.10000
Neck diameter   = 0.20000
Neck corridor   = 0.15000
Neck center     = (0.4484, 0.0000, 0.0000)
Neck axis       = (1.0000, 0.0000, 0.0000)
```

## 3. Verbatim verdict

```
[bladder] BLADDER FALSIFIERS:
  (a) SEAL      : PASS  force<F_hold samples=43 escapes=0 shell_clust max=1
  (b) YIELD     : FAIL  at tick=15888 force=766.92 sep=0.09999 escapes=0/61 shell_clust max=1
  (c) NECK      : FAIL  escaped=0 in_neck=0 out_neck=0 first_escape=none (bar 0.1500 from axis)
  (d) INTEGRITY : FAIL  post-yield shell_clust max=1 max disp=0.1890 (bar 0.1000)
```

## 4. Trajectory

| Phase | tick | separation | plate force | shell_disp | escapes | shell_clust |
|-------|------|-----------|-------------|------------|---------|-------------|
| init | 0 | 0.49698 | 631.56 | 0.0000 | 0 | 1 |
| converge | 500 | 0.48448 | 729.01 | 0.1352 | 0 | 1 |
| converge | 1000 | 0.47199 | 833.07 | 0.1765 | 0 | 1 |
| converge | 2000 | 0.44700 | 571.68 | 0.1787 | 0 | 1 |
| converge | 3000 | 0.42202 | 520.61 | 0.1811 | 0 | 1 |
| converge | 4000 | 0.39703 | 614.43 | 0.1980 | 0 | 1 |
| converge | 5000 | 0.37205 | 826.46 | 0.1749 | 0 | 1 |
| converge | 7000 | 0.32207 | 1198.70 | 0.1379 | 0 | 1 |
| converge | 10000 | 0.24710 | 425.17 | 0.1376 | 0 | 1 |
| converge | 13000 | 0.17213 | 557.77 | 0.1426 | 0 | 1 |
| converge | 15500 | 0.10966 | 719.75 | 0.1585 | 0 | 1 |
| converge | 15888 | 0.09999 | 766.92 | 0.1645 | 0 | 1 |
| release | 16000 | 0.10279 | 461.01 | 0.1649 | 0 | 1 |
| release | 20000 | 0.20274 | 595.21 | 0.1519 | 0 | 1 |
| release | 25000 | 0.32769 | 1189.38 | 0.1538 | 0 | 1 |
| release | 31769 | 0.49680 | 340.68 | 0.1856 | 0 | 1 |
| hold | 32000 | 0.49680 | 312.11 | 0.1864 | 0 | 1 |
| hold | 32500 | 0.49680 | 381.78 | 0.1890 | 0 | 1 |
| hold | 32769 | 0.49680 | 360.71 | 0.1884 | 0 | 1 |

Key observations:
- **No content grains escaped at any sampled tick.** First escape: none.
- Shell displacement exceeds the 0.10 integrity bar immediately at tick 500 (0.1352) and remains roughly 0.14–0.19 for the entire run.
- Plate force peaks at 1198.70 during release, still below `2*F_hold = 1348.37`.
- Shell cluster count remained 1 throughout.
- SEAL passes: zero escapes while force < F_hold (43 samples).

## 5. Neck-corridor accounting

- Total escaped grains: 0
- In-neck: 0, out-of-neck: 0
- Corridor bar: 0.15 from the +x neck axis.

## 6. Diagnosis

The v3 design changed the neck geometry correctly — a 4-spacing hole on the squeeze axis, too large for a cushion arch — but the underlying failure mode persists.

- **SEAL passed**: the shell stayed one connected cluster and no content escaped while plate force was below `F_hold`.
- **YIELD failed**: by the geometric minimum separation (`sep = 0.09999` at tick 15888), zero of the 61 half-content quota had escaped. The run never reached `2*F_hold`.
- **NECK failed** trivially: no grains escaped, so there were zero in-neck and zero out-of-neck events.
- **INTEGRITY failed**: although the shell remained one cluster, shell grains were permanently displaced from their print positions, ending at max disp 0.1890 (> 0.10).

**What the escape-vs-force curve says**: escapes are flat at 0 for the entire 32,769-tick run. This is not a slow leak, not a jammed flow that never reaches 32 escapes, and not contents migrating as a plug. The contents never begin to move through the neck at all.

**What killed it**: the same crumpling-membrane behavior as v2. The shell wall buckles and folds as soon as the plates engage, so global shell displacement crosses the integrity bar within the first 500 ticks. Because the wall collapses inward rather than translating uniformly, the pressure gradient does not drive the interior contents toward the neck; the anti-jam opening is simply never accessed. A larger hole cannot fix a pathway that is never pressurized. The closed mat container still EXISTS and SEALS; the yield pathway remains refuted.
