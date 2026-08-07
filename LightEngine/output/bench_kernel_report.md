# LightEngine kernel scaling verdict

Machine: NVIDIA GeForce RTX 4090, numba.cuda, Python 3.14.3.

## 1. Kernel architecture

- **Library**: numba + numba.cuda (jitted kernels, CUDA when available).
- **DRAW**: naive O(N^2) softened inverse-square over **all pairs**; infinite
  range, no cutoff.  Per-step each thread reads the entire position array.
- **RESISTANCE**: naive O(N^2) pairwise loop with early skip beyond `R_C = 0.30`;
  wall branch (`r < R_WALL`) includes contact damping, bond branch
  (`R_WALL <= r <= R_BOND`) is repulsion-only.
- **Integrator**: velocity Verlet with fixed `DT = 5e-4`.
- **Memory traffic per step**: positions + velocities uploaded once, then each
  of the N threads reads all N positions in DRAW and again in RESISTANCE;
  writes one acceleration vector per particle.  Total pair work is ~2 N^2
  distance evaluations per tick.
- **No neighbor list / Barnes-Hut / grid is wired into the kernel yet.**
  `LightEngine/kernel.py` does contain a grid-based *neighbor count* helper,
  but the force kernels ignore it.

## 2. Benchmark method

`tools/bench_kernel.py` places N grains on a cubic lattice with spacing 0.05
(non-overlapping), runs 2 warmup + 10 timed velocity-Verlet ticks on CUDA, and
reports steps/sec.  Tested sizes: 512, 1024, 2048, 4096, 8192, 16384.

## 3. Timing table

| N       | steps/sec | ms/step |
|--------:|----------:|--------:|
| 512     | 365.84    | 2.73    |
| 1024    | 237.43    | 4.21    |
| 2048    | 169.78    | 5.89    |
| 4096    | 109.13    | 9.16    |
| 8192    | 60.42     | 16.55   |
| 16384   | 32.50     | 30.77   |

Log-log fit over all points: `steps/sec = 2.880e+04 * N^(-0.686)`.

## 4. Verdict table (one 8000-tick print)

| N       | predicted steps/sec | wall-clock |
|--------:|--------------------:|-----------:|
| 30 000  | 24.35               | 329 s      |
| 50 000  | 17.15               | 467 s      |

**Verdict: feasible as-is for a single 8000-tick print on the RTX 4090.**

A 50k-grain print is predicted to finish in under 8 minutes.  The main caveat
is that the scaling exponent (-0.686) is better than pure O(N^2) because the
GPU is still gaining occupancy/efficiency in this range; if memory bandwidth
or occupancy saturation changes the exponent above ~50k, the cost could climb.

## 5. Neighbor list (for the resistance pass)

Because the kernel is naive pairwise, a spatial-grid neighbor list was built
and validated, but **it was NOT integrated into the kernel** (integration is a
separate decision).

- New file: `LightEngine/neighbor.py`
- Uniform grid, cell size = `R_C = 0.30`, 27-cell stencil.
- Returns flat neighbor index array + per-particle offsets.
- Provides `compute_resistance_grid(pos, vel)` matching the kernel's public
  resistance interface.

Validation (`python -m pytest LightEngine/tests/test_neighbor.py -v`):

```
6 passed in 2.72s
```

For N = 2048 random grains:
- max |F_grid - F_pairwise| / max(|F_pairwise|, 1) = within 1e-5 relative.
- neighbor counts match brute-force counts exactly.

## 6. What still limits scale

The neighbor list only accelerates the **RESISTANCE** pass (cutoff R_C).  The
**DRAW** pass is infinite-range softened gravity, so a spatial grid cannot help
it without changing the force law.  To push far beyond 50k grains or to much
longer prints, DRAW needs either:

- a Barnes-Hut tree, or
- an authored cutoff on DRAW (requires changing `LightEngine/constants.py`,
  which was declared frozen for this task).

Bottom line: the existing kernel survives a 30k-50k grain skeleton print today
on this GPU, but the long-term scaling ceiling is DRAW's O(N^2) summation.
