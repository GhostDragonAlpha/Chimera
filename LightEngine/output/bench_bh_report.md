# LightEngine Barnes-Hut DRAW scaling verdict

Machine: NVIDIA GeForce RTX 4090, numba.cuda, Python 3.14.3.

## 1. What was built

- `LightEngine/bh_draw.py`: theta-parameterized octree Barnes-Hut for the DRAW
  force only.  It reproduces the kernel's softened inverse-square law with the
  same frozen `G = 0.01` and `EPS = 0.02`.
- GPU traversal uses an explicit per-thread stack (numba CUDA); the octree is
  built on the CPU and flattened to device arrays.
- CPU reference path (`compute_draw_bh_cpu`) validates the GPU kernel.
- `LightEngine/tests/test_bh_draw.py`: theta sweep, accuracy assertion,
  determinism, and octree mass/COM invariants.
- `tools/bench_bh.py`: scaling benchmark, log, and projection script.

## 2. Validated theta

For N=4096 non-overlapping grains (jittered cubic lattice, spacing 0.05) the
measured max relative error vs pairwise DRAW is:

| theta | rel err (leaf_size=16) |
|------:|-----------------------:|
| 0.30  | 0.000343               |
| 0.50  | 0.006658               |
| 0.70  | 0.022370               |
| 1.00  | 0.767861               |

The largest theta meeting the 1e-3 budget is **theta = 0.30** (used with
`leaf_size = 16`).  All tests pass:

```
python -m pytest LightEngine/tests/test_bh_draw.py -v
8 passed
```

## 3. Benchmark method

`tools/bench_bh.py` places N grains on a cubic lattice with spacing 0.05 and a
small random jitter, then times one full BH DRAW evaluation including CPU tree
build and GPU traversal.  Three timed runs are averaged after one warmup run;
per-size timeout is 60s.  The pairwise reference is the Lane K extrapolation
`steps/sec = 2.88e4 * N^-0.686`.

## 4. Timing table

| N       | BH steps/sec | Pairwise extrap | Speedup |
|--------:|-------------:|----------------:|--------:|
| 16 384  | 12.31        | 37.01           | 0.33x   |
| 65 536  | 2.94         | 14.30           | 0.21x   |
| 262 144 | 1.36         | 5.52            | 0.25x   |
| 1 048 576 | 0.22       | 2.13            | 0.10x   |
| 2 097 152 | 0.16       | 1.33            | 0.12x   |

BH log-log fit over measured points: `steps/sec = 8.47e4 * N^-0.911`.

Crossover where the fit predicts BH equals the pairwise extrapolation:
**N ~ 120**.  This crossover is driven by the fit and is not directly measured;
measured BH remains slower than the pairwise extrapolation up to N = 2M.

N = 4 194 304 exceeded the 60s timeout (96s for three runs) and is omitted.

## 5. Projected wall-clock for an 8000-tick print (DRAW-only)

| N       | BH steps/sec | 8000-tick print |
|--------:|-------------:|----------------:|
| 500 000 | 0.54         | 4.10 h          |
| 6 400 000 | 0.05       | 41.9 h          |

These projections assume DRAW is the dominant cost and ignore resistance and
integration overhead.

## 6. Verdict and blockers

**The BH module is delivered and validated, but it is not yet a practical
speed win over the naive pairwise kernel on this GPU in the 16k-2M range.**

Blockers for the 6.4M full-fidelity skeleton target:

1. **Wall-clock time**: ~42 hours for DRAW alone at 6.4M grains.  Adding the
   resistance pass and velocity-Verlet integration would make a full print
   substantially longer.
2. **CPU tree build**: the build is a large fraction of each step (e.g. ~2s of
   the ~4.6s per step at N=1M).  It is done on the host and must be repeated
   every tick as particles move.
3. **GPU traversal overhead**: the per-thread stack traversal in numba CUDA has
   warp-divergence and memory-access overheads that keep it slower than the
   highly vectorized naive pairwise kernel up to at least N = 2M.

Memory is **not** a blocker: the octree plus particle arrays for 6.4M grains
fit comfortably in the RTX 4090's 24 GB VRAM and in host RAM.

Theta accuracy is **not** a blocker at depth: BH approximation error improves as
cells become smaller relative to distances, so the chosen theta=0.30 remains
safe at 6.4M.

**Bottom line**: the code path exists and scales to millions of grains, but a
single 8000-tick 6.4M-grain print would take days with this first BH
implementation.  To reach production viability the next step is either a GPU
octree build or a more GPU-friendly traversal (warp-cooperative, stackless, or
bottom-up), not a larger theta.
