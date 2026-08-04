# MEASURED RENDER BUDGETS — what a frame actually costs

**2026-08-04, RTX 4090, 1920×1080, `FullGPUPipeline`.** `perf_guard.py` declares
`MAX_GRAINS_PER_FRAME = 250_000`, derived "from 7.8 fps at 1920×1080". That is a claim about this
machine and nobody had run it. This is the run.

Method: 12 renders per case, **first two discarded** — the first pass through a numba-CUDA kernel
pays JIT compilation, and timing it reports the compiler rather than the renderer. Mean ± σ of the
remaining ten.

## THE MEASUREMENTS

| scene | grains | ms (mean ± σ) | fps | over 200 ms? |
|---|---:|---:|---:|---|
| aBlueWorld, default framing, full base | 43,000 | **28.19** ± 1.87 | 35.5 | no |
| aBlueWorld, **0.5× zoom**, LOD | 43,000 | **45.23** ± 2.70 | 22.1 | no |
| aBlueWorld, 5.0× zoom, LOD (coarse mip) | 4,096 | **18.83** ± 1.66 | 53.1 | no |
| aTerrain, full base — heaviest in the registry | 262,144 | **36.50** ± 5.88 | 27.4 | no |
| aTerrain, default framing **with LOD** | 65,536 | **33.49** ± 5.07 | 29.9 | no |
| synthetic 250,000 — perf_guard's declared cap | 250,000 | **35.23** ± 2.10 | 28.4 | no |

## THE FALSIFIER DID NOT FIRE — the derivation was wrong by 3.6×

> *"The measured time for the heaviest scene is within 10% of the derived estimate — the
> derivation was accurate without measurement."*

The derived figure implies 250,000 grains at 7.8 fps = **128.2 ms**. Measured at exactly 250,000
grains: **35.23 ms**. The real renderer is **3.64× faster** than the number the budget was built
on — 264% out, against a 10% bar.

## THE FINDING THAT MATTERS: A GRAIN COUNT IS THE WRONG UNIT

Grain count barely moves the frame time:

    4,096 grains ->  18.83 ms
   43,000 grains ->  28.19 ms
  250,000 grains ->  35.23 ms
  262,144 grains ->  36.50 ms

**A 64× increase in grains costs 1.94× the time.** The cost is dominated by a fixed per-frame
overhead — rasterising 1920×1080 and launching the kernels — not by per-splat work.

And the decisive pair, which shares a grain count and differs only in camera:

| | grains | ms |
|---|---:|---:|
| aBlueWorld, default framing | 43,000 | 28.19 |
| aBlueWorld, **0.5× zoom** | 43,000 | **45.23** |

**Identical geometry, identical count, 60% more time.** Zooming in makes each splat cover more
pixels, and pixels are what the pipeline actually pays for.

    THE FRAME COST IS DRIVEN BY SCREEN COVERAGE, NOT BY GRAIN COUNT.
    `MAX_GRAINS_PER_FRAME` budgets a quantity that does not determine the thing being budgeted.

> ### ⚠ THE FIRST HALF OF THAT SENTENCE IS WRONG — see **PART TWO** below.
> The 35-row sweep puts **coverage at R² = 0.115 and grain count at R² = 0.481**: grains beat
> coverage by ΔR² = 0.37, the opposite of what is claimed here. The conclusion above was drawn
> from **two data points** and it did not survive the fuller measurement. What actually predicts
> the cost is **tile expansions** — the `(splat, tile)` pairs the binner processes — at R² = 0.998.
> The *second* half of the sentence stands: a grain count is still the wrong unit.

## WHY `MAX_GRAINS_PER_FRAME` WAS **NOT** REPLACED WITH A NEW NUMBER

The obvious move is to re-derive the cap from these numbers. It cannot be done honestly, and the
reason is the point:

- Extrapolate from the **grain-dominated** cases (18.83 ms at 4k → 36.50 ms at 262k) and the
  200 ms wall sits near **2.6 million grains**.
- Extrapolate from the **coverage-dominated** case (45.23 ms at 43,000 zoomed in) and the same
  wall sits near **190,000** — *below* the current cap.

A **14× spread** depending on which case you fit. That is not a measurement problem; it is the
model being wrong. Replacing one unmeasured number with another, better-dressed unmeasured number
is exactly the move this project has a rule against, so the constant is left alone and this
document is what it now points at.

**`MAX_RENDER_MS = 200` is the wall that means something**, because it measures the thing that
hurts. Nothing in the registry approaches it: the worst case measured is **45 ms**, a 4.4× margin.
`live_viewer`'s `/stats` reports `over_time` alongside `over_budget` for this reason — a scene can
sit inside the grain cap and still be too slow, and only one of those is what a viewer feels.

## WHAT THIS SAYS ABOUT THE RAISED BUDGETS

A concurrent change raised every per-surface budget (terrain 20,000 → 300,000, rock 8,000 →
50,000, body 12,000 → 20,000, and the rest), which took the 42-term report from twelve violations
to zero. These measurements neither support nor refute those numbers: **per-surface budgets are
about legibility and memory, not frame time**, and frame time is all this instrument measured. The
grain counts in the registry are between 4× and 60× below anything that costs a frame here.

## LOD, MEASURED

LOD's saving is real but small in TIME on this hardware, because time is not grain-bound:
aTerrain full base 36.50 ms → with LOD 33.49 ms, an **8% saving for a 4× grain reduction**. Its
value is in memory, upload bandwidth and legibility at distance — not in frame rate. Claiming LOD
as a frame-rate optimisation on this machine would be claiming something the measurement does not
show.

## REPRODUCING

The instrument is a throwaway (scratchpad `measure_budgets.py`); the numbers above are what it
printed. To re-run, bench `pipe.render_from_gpu` over 12 frames per case, discard two, and place
the camera with the aim-at-origin formula — the `atan2(-pos[1], pos[0])` form found in
`orbit_proof.py` and `demo.py` points away from the object at most angles and will silently time
an empty frame.

---

# PART TWO — THE FULL SWEEP, AND WHICH QUANTITY ACTUALLY PREDICTS THE COST

**2026-08-04, second pass.** Part One measured one body at three zoom levels and concluded that
*"the frame cost is driven by screen coverage, not by grain count."* **That conclusion was formed
from two data points and the full sweep refutes it.** This is the correction.

`ChimeraEngine/benchmark_pipeline.py` — heaviest term per surface class × 5 zoom levels,
5 renders each with 2 discarded as warm-up. **35 rows**, in `docs/pipeline_benchmark.csv`.

## FOUR MODELS, ONE SET OF ROWS

| model | R² | |
|---|---:|---|
| `render_ms ~ a·coverage + b` | **0.115** | the hypothesis from Part One |
| `render_ms ~ a·grains + b` | **0.481** | what `MAX_GRAINS_PER_FRAME` assumes |
| `render_ms ~ a·(grains × coverage) + b` | **0.850** | better, but see below |
| `render_ms ~ a·(tile expansions) + b` | **0.998** | and it is a *mechanism* |

**The falsifier fired as written:** both named models are below R² = 0.5, so the pipeline has no
simple cost predictor in either of the terms that were proposed. And the ordering is the opposite
of Part One's claim — **grain count beats coverage by ΔR² = 0.37.**

## WHAT DOES PREDICT IT: TILE EXPANSIONS

A **tile expansion** is one `(splat, tile)` pair. The binner and the sorter process exactly these,
so this is not a curve fitted to a shape — it is a count of the work being done. The pipeline
already computes it; `CHIMERA_TILE_DIAG=1` prints it as `total expansions`.

| scene | grains | coverage | **expansions** | ms |
|---|---:|---:|---:|---:|
| aBlueWorld 0.5× | 43,000 | 95.9% | 417,732 | 30.94 |
| aTerrain 0.5× | 262,144 | 23.5% | 774,065 | 24.29 |
| **theMining 0.25×** | **8,157** | 52.3% | **1,307,982** | **49.32** |
| aTerrain 0.25× | 262,144 | 74.4% | 12,834,678 | 359.24 |

**The row that kills both simple models is theMining.** It has the *fewest* grains in the table
and unremarkable coverage, and it costs more than aBlueWorld's 43,000 splats at 96% coverage. Its
expansion count is 1.3 million, because at 0.25× zoom its splats are enormous and each lands in
hundreds of tiles.

    A FEW HUGE SPLATS COST MORE THAN MANY SMALL ONES,
    and neither a grain count nor a coverage fraction can see the difference.

    render_ms = 2.7013e-05 × expansions + 12.39        R² = 0.998

At `MAX_RENDER_MS = 200` that gives **≈ 6.9 million expansions**, now in `perf_guard` as
`MAX_TILE_EXPANSIONS` with `check_work_budget()`.

## HONEST LIMITS

- **n = 4 for the expansion fit**, and its R² is inflated by the single 359 ms point. The
  mid-range residuals are **+37%** and **−23%**. It is the best of the four models and the only
  one with a mechanism behind it, and it is still a four-point fit. The cap is an order of
  magnitude, not a threshold.
- **Drop the one outlier and nothing predicts well**: coverage 0.41, grains 0.08,
  grains×coverage 0.28. In the ordinary regime — everything under 100 ms — the frame cost is
  dominated by fixed per-frame work that none of these terms names.
- `check_work_budget()` is **not** wired into `upload()`, because the expansion count does not
  exist until the frame has been binned — by which point the work is already done. It is for the
  diagnostic path and for offline renders that can afford to look afterwards.

## `MAX_GRAINS_PER_FRAME` STAYS, AND STAYS LABELLED

Coverage did **not** beat grains, so it does not replace it. Grains explain under half the
variance, so the constant is not promoted either. It remains a coarse sanity net with its
measurement recorded beside it, and `MAX_RENDER_MS` remains the wall that means something.

## LOD, RE-MEASURED ACROSS THE SWEEP

LOD's value shows up clearly here in a way Part One's single body could not show — at 2× and 5×
zoom every class drops to the 16,384 or 4,096 mip, and aTerrain falls from 262,144 to 4,096:

| aTerrain | grains | ms |
|---|---:|---:|
| 0.25× | 262,144 | 341.33 |
| 1.00× | 65,536 | 18.03 |
| 5.00× | 4,096 | 8.98 |

The 341 ms frame is the only measurement in the whole sweep that breaches `MAX_RENDER_MS`, and it
is the one case where LOD is *not* engaged — at 0.25× the body fills the frame and correctly
selects its base level. **The worst frame in the registry is the one LOD is right not to help.**
