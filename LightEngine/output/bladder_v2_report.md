# Bladder v2 (fill mode) print-run report

Run: `python -m LightEngine.demo_seed --structure bladder --bladder-fill fill`
Output log: `LightEngine/output/print_bladder_v2_log.txt`
Frames: `LightEngine/output/bladder_v2_bladder_begin.png`, `bladder_v2_bladder_end.png`

## 1. Construction

- `seed_structures.bladder(seed, fill="fill")` carves a 0.05 cubic lattice of content grains inside the radius `r_in = r_b - d_eq` (`r_b = 0.20`, `d_eq = 0.04840`), giving 123 content grains pressed against the inner shell wall.
- Shell: 211 grains, one grain thick.
- Plates: two 4x4 pinned plates.
- Total grains `N = 366`.

## 2. Derived parameters

```
r_b        = 0.20000
d_eq       = 0.04840
s0         = 0.49680
F_hold     = 679.33
2*F_hold   = 1358.67
Min sep    = 0.10000
Neck center = (0.2484, 0.0000, 0.2000)
Neck axis   = (0.0000, 0.0000, 1.0000)
```

## 3. Verbatim verdict

```
[bladder] BLADDER FALSIFIERS:
  (a) SEAL      : PASS  force<F_hold samples=32 escapes=0 shell_clust max=1
  (b) YIELD     : FAIL  at tick=15888 force=664.02 sep=0.09999 escapes=0/61 shell_clust max=1
  (c) NECK      : FAIL  escaped=0 in_neck=0 out_neck=0 (bar 0.1000 from axis)
  (d) INTEGRITY : FAIL  post-yield shell_clust max=1 max disp=0.1876 (bar 0.1000)
```

## 4. Shell-displacement trajectory

| Phase | tick | separation | plate force | shell_disp | escapes | cluster |
|-------|------|-----------|-------------|------------|---------|---------|
| init | 0 | 0.49698 | 679.44 | 0.0000 | 0 | 1 |
| converge | 500 | 0.48448 | 795.32 | 0.1167 | 0 | 1 |
| converge | 1000 | 0.47199 | 851.48 | 0.1357 | 0 | 1 |
| converge | 2000 | 0.44700 | 890.38 | 0.1502 | 0 | 1 |
| converge | 3000 | 0.42202 | 323.47 | 0.1825 | 0 | 1 |
| converge | 5000 | 0.37205 | 780.70 | 0.1801 | 0 | 1 |
| converge | 10000 | 0.24710 | 457.33 | 0.1583 | 0 | 1 |
| converge | 15000 | 0.12215 | 624.00 | 0.1507 | 0 | 1 |
| converge | 15888 | 0.09999 | 664.02 | 0.1598 | 0 | 1 |
| release | 16000 | 0.10279 | 354.27 | 0.1603 | 0 | 1 |
| release | 20000 | 0.20274 | 644.85 | 0.1585 | 0 | 1 |
| release | 25000 | 0.32769 | 1243.40 | 0.1565 | 0 | 1 |
| release | 31769 | 0.49680 | 371.21 | 0.1840 | 0 | 1 |
| hold | 32500 | 0.49680 | 390.73 | 0.1876 | 0 | 1 |
| hold | 32769 | 0.49680 | 364.19 | 0.1860 | 0 | 1 |

Key observations:
- Shell displacement exceeds the 0.10 integrity bar immediately at tick 500 (`0.1167`) and remains roughly 0.15-0.19 for the remainder of the run.
- Plate force never reaches `2*F_hold = 1358.67`; peak is `1243.40` during release, well below threshold, but the geometric minimum separation (`0.09999`) triggers the YIELD falsifier before that.
- Zero content grains escaped at any time.
- Shell cluster count remained 1 throughout.

## 5. Diagnosis

The v2 design (filled interior in cushion contact with the shell wall) did not fix the failure mode seen in v1.

- **SEAL passed**: the shell remained one connected cluster and no content escaped while plate force was below `F_hold`.
- **YIELD failed**: by the time the plates reached the geometric minimum separation (`sep = 0.09999` at tick 15888), zero of the 61 content-grain quota had escaped. The shell did not open a neck under the applied load.
- **NECK failed**: with no escaped grains, there were zero in-neck and zero out-of-neck events.
- **INTEGRITY failed**: although the shell stayed one cluster, shell grains were permanently displaced from their print positions. Displacement crossed the 0.10 bar immediately during convergence and ended at `0.1860`, indicating the shell did not spring back to its print neighborhood after release.

**What killed it**: the cushion-splinted spherical shell behaves as a crumpling membrane rather than an elastic pressure vessel. The wall grains buckle inward/outward as soon as the plates are engaged, so the global displacement exceeds the integrity bar before any pressure can build to drive contents through a neck. Adding interior fill grains changes the mass budget but does not create the localized stiff ring or active neck mechanism needed for controlled yielding. The structure needs a mechanism that either (a) keeps the shell wall near its print shape until a threshold pressure is reached, or (b) pre-forms a compliant neck that opens under plate compression rather than requiring uniform wall expansion.
