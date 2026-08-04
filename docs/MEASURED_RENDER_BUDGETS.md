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
