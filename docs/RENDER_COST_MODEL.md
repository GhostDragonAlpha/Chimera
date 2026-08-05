# THE RENDER COST MODEL — what a frame actually costs

> **STATEMENT.** A frame's cost is set by **tile expansions** — the number of `(splat, tile)` pairs
> the pipeline produces — and not by grain count or by pixel coverage.
>
> **PREDICTION.** Across the 7 surface classes at 5 zoom levels, expansions predict frame time with
> R² > 0.9, while grain count and coverage each stay under 0.5. A scene with few large splats costs
> more than a scene with many small ones at equal grain count.
>
> **FALSIFIER (named before the sweep).** Expansions R² drops below 0.9 on the full 35-row set —
> the 4-row proof does not generalise.
>
> **RESULT: the falsifier did not fire. R² = 0.9949, n = 35.** It is also not the whole story, and
> §5 is where this document argues against itself.

Measured 2026-08-04 on an RTX 4090 at 1920×1080, `TILE_SIZE = 32` (2,040 tiles).
Data: [`pipeline_benchmark.csv`](pipeline_benchmark.csv) (35 rows) ·
[`pipeline_terms.csv`](pipeline_terms.csv) (47 terms).
Regenerate: `python ChimeraEngine/benchmark_pipeline.py` and `--audit`.

---

## 1. What the pipeline is billed for

A **tile expansion** is one `(splat, tile)` pair. `_build_tiles_gpu` computes each visible splat's
screen footprint and emits one pair per tile that footprint touches:

```
n_x = ⌈(px + 1.5r)/32⌉ − ⌊(px − 1.5r)/32⌋       expansions_for_this_splat = n_x · n_y
```

Summed over visible splats, that is the frame's expansion count. It is already computed on the
live path — the zero-check needs it on the host — so reading it costs **no additional
device→host transfer**. `pipe.expansion_count()` returns it for the frame just rendered.

**Two grains of the same count can differ by 400× here.** `theMining` at 0.25× zoom draws 8,157
visible splats into 1,307,982 expansions (160 tiles each); `aTerrain` at 5× zoom draws 2,098 into
8,320 (4 tiles each). Grain count sees 4× between them. The pipeline pays 157×.

## 2. The equation

```
render_ms ≈ 2.9083e-05 × expansions + 21.002              n = 35, R² = 0.9949
```

Coefficients live in `ChimeraEngine/perf_guard.py` as `MS_PER_EXPANSION` and `FIXED_MS`, and the
frame budget is the equation **inverted**, never a chosen number:

```python
MAX_EXPANSIONS_PER_FRAME = expansions_for_ms(MAX_RENDER_MS)   # (200 − 21.002) / 2.9083e-05
```

| frame-time wall | derived cap | rows firing (of 35) | false positives |
|---|---:|---:|---:|
| 200 ms (5 fps) — **declared** | 6,154,729 | 1 | 0 |
| 33 ms (30 fps) | 422,858 | 8 | 2 |
| 16.7 ms (60 fps) | **0** | 35 | — |

That last row is a finding, not a formatting accident: **the measured fixed floor exceeds a 60 fps
frame**, so 60 fps at 1920×1080 is unreachable by any scene in this project, empty ones included.
It is a statement about the pipeline, not about any membrane.

> **The one lever.** To make the guard stricter, change `MAX_RENDER_MS`. Everything else moves with
> it. Nothing in this model is set by taste.

## 3. The mechanism — and the part of it that was assumed wrong

The expected story was: *the binner allocates each pair, the sorter sorts them, the compositor
blends them; all three scale with expansions.* **Two of those three are right, and the one that is
wrong is the one that dominates.** Per-stage timing, medians of 3, syncs between stages:

| scene | expansions | BIN + SORT | **COMPOSITE** |
|---|---:|---:|---:|
| theMining 0.25× | 1,307,982 | 7.7 ms (6%) | **105.2 ms (89%)** |
| aTerrain 0.25× | 12,834,678 | 28.0 ms (6%) | **397.2 ms (91%)** |
| aBlueWorld 0.25× | 520,905 | 3.4 ms (13%) | **19.5 ms (73%)** |
| theZero @ d=1.0 | 100,000 | 5.2 ms (14%) | **28.0 ms (75%)** |
| theZero @ d=2.8e-6 | 8,160,000 | 16.0 ms (73%) | **2.6 ms (12%)** |

**Binning and sorting are 6–14% of the frame.** The compositor is 73–91%, and it does not walk
expansions — it walks *pixels*, and for each pixel walks that pixel's tile list:

```python
for si in range(start, end):        # gpu_pipeline.py:467 — the tile's splat list
    ...
    trans *= (1.0 - al)
    if trans < 0.01: break          # gpu_pipeline.py:488 — THE OPACITY EARLY-OUT
```

So the real currency is

```
compositor_cost  ≈  Σ over tiles [ 1024 px × min(len(tile_list), splats_until_opaque) ]
```

which is **expansions × 1024, truncated per tile by opacity saturation**. Expansions predict well
whenever saturation depth is roughly constant across a scene — which is true of ordinary surfaces,
and is why R² is what it is.

**The last row of the table is the model failing, on purpose.** `theZero` has `body_radius = 0`, so
the framing rule `2.8 × max(R, 1e-6)` puts the camera 2.8 µm away and every splat covers all 2,040
tiles: 8.16M expansions, more than any other term by 33×. It costs **2.6 ms to composite**, because
every pixel saturates after ~2 splats and breaks. The same term framed at `d = 1.0` produces 82×
*fewer* expansions and costs **11× more** to composite. Expansions are wrong by ~1000× there.

> **When the model can be trusted:** ordinary surfaces, where the splats are semi-transparent and a
> pixel walks most of its list. **When it cannot:** any scene whose splats are large *and* opaque
> enough to saturate immediately. The tell is `expansions_per_splat` above ~1000 — at that point a
> splat covers most of the screen and the early-out is doing the work the count cannot see.

## 4. The practical rule

**To speed up a slow scene, shrink the largest splats. Reducing grain count may do nothing.**
`theMining` at 0.25× costs 65 ms with 9,000 grains; `aBlueWorld` costs 39 ms with 43,000. Deleting
grains from theMining moves the count and barely moves the cost, because each surviving grain still
covers 160 tiles.

Diagnose in this order:

```bash
python ChimeraEngine/benchmark_pipeline.py --audit
```

1. `pipe.expansions_per_splat()` — tiles touched per visible splat. **This is the number to act on.**
2. `CHIMERA_SPLAT_SIZE_DIAG=1` — is the SIZE column broadly large, or is there a tail?
3. `CHIMERA_TILE_DIAG=1` — which tiles, and are any over `MAX_PER_TILE` (an eviction = something
   not drawn).

**And check the framing before editing an `emit()`.** A large `expansions_per_splat` has two causes
that look identical — grains that are too large, or a camera too close for the body's extent — and
`theZero`, the only term that trips the half-screen warning, is the second kind. Its SIZE is 0.03,
among the *smallest* of all 47 membranes. The warning at `gpu_pipeline._report_expansions` now
reports the measured projected radius so the two can be told apart.

## 5. What is wrong with this model

**(a) One point carries the R².** Drop `aTerrain @ 0.25×` (12.8M expansions, 393 ms) and:

| | full (n=35) | outlier removed (n=34) |
|---|---:|---:|
| expansions | 0.9949 | **0.8293** |
| coverage | 0.1273 | 0.4493 |
| grain count | 0.4717 | **0.0419** |

Quote **0.83** for an ordinary scene, not 0.995. The *ranking* is not inflated — expansions win by
≥0.38 either way, and grain count collapses to 0.04, meaning its apparent 0.47 was that same single
point. The superseded model was standing on the same rock as the model replacing it; only one is
still standing when the rock is removed.

**(b) The fitted intercept is not the real floor.** Two rows render nothing at all (`aSaltOcean` and
`aSteppeBiomes` at 0.25× — camera inside the shell, 0 visible splats) and cost **10.1–10.3 ms**.
That is the true fixed cost. The fitted 21.0 ms is a straight line bending to reach the outlier.

**(c) It is calibrated on bursts and the live viewer is slower.** The benchmark times 3 frames after
2 warm-ups. Under the viewer's sustained loop the same work runs **1.7–4.9× slower** than predicted
(theZero: 116 ms measured against 24 ms predicted at identical expansion count). Part is
environmental — this box shares its 4090, measured at 17.1 GB VRAM held and 27% utilisation by
other processes while idle — and part is not yet explained. **Do not use `predicted_ms` as a
performance claim.** It is on `/stats` beside the measured time so the disagreement stays visible.

**(d) Frame time here has a ±13% noise floor.** Clamping splat sizes changed expansions by exactly
0.00% and moved measured time by −13.6% and +11.2% on two scenes. Any single-frame timing
difference under ~15% is noise.

**(e) It says nothing about correctness.** A frame inside budget can still be wrong: `MAX_PER_TILE`
evicts the far splats in an overfull tile, and that is a *visual* defect (hard-edged black
rectangles on the tile grid) with no cost signature. `tile_expansion_ratio` on `/stats` tracks it.

## 6. The superseded models, with their evidence

| model | R² (n=35) | R² without outlier | verdict |
|---|---:|---:|---|
| **tile expansions** | **0.9949** | **0.8293** | in use — `MAX_EXPANSIONS_PER_FRAME` |
| grain count (`n_lod`) | 0.4717 | 0.0419 | **superseded.** `MAX_GRAINS_PER_FRAME = 250,000` |
| visible grain count | 0.4295 | — | never shipped |
| expansions per splat | 0.3072 | — | a *diagnostic*, not a predictor of total cost |
| pixel coverage | 0.1273 | 0.4493 | **refuted** as the dominant driver |

Correlation matrix against `render_ms`: expansions **0.997** · n_lod 0.687 · n_vis 0.655 ·
expansions/splat 0.554 · coverage 0.357.

**The grain-count budget was wrong twice over.** Its stated derivation ("7.8 fps at 1920×1080",
implying 128 ms for 250,000 grains) was off by 3.64× — the real figure is 35.23 ± 2.10 ms — and it
budgeted a quantity that does not determine the thing being budgeted. It survives in `perf_guard`
for one job only: the `general` fallback in `_classify_budget`, where the question is "is this
membrane suspiciously dense", which is a density question and not a cost one.

**The per-class grain budgets rank the classes wrongly.** 5 of 7 classes rank differently under
grain budget than under measured expansions (`benchmark_pipeline.py --audit`): `terrain` holds the
largest allowance (300,000) and ranks 2nd in cost; `general` holds 250,000 and ranks 1st; `body`
holds the smallest (20,000) yet ranks 5th of 7 while carrying the highest expansions-per-grain of
any class (20.0 against terrain's 3.66). Rescaling by `exp_per_grain` is the mechanical fix. The
honest one is that a grain budget cannot be made into a cost budget.

## 7. Related finding — LOD discards the emitted splat size

Not part of the cost model, found while building its diagnostics, and load-bearing for anyone who
tries to shrink splats:

**`lod.build_mips` overwrites the SIZE column with `β·2R/√N` at every level — including the base.**
For the coarse levels that is the surface-grain law doing real work. Applied to the full-detail
level it discards whatever `emit()` decided:

| term | emitted sizes | uploaded |
|---|---|---|
| `aYellowStar` | {0.03, 0.33} — hot core, soft corona, 11× | single **0.044** |
| `theGalaxy` | {0.0075, 0.06} | single **0.0267** |
| `aRockyPlanet` | 4 values, max 0.0347 | single **0.1058** — 3× its own largest grain |

**44 of 47 terms reach the GPU with exactly one unique SIZE value.** Consequences: a star's corona
is not rendered as a corona; any size-tail diagnostic reads a single spike; and a clamp of the form
"cap outliers at 2× the mean" is a no-op, which is what was measured (0.00% change in expansions on
both `theMining` and `aBlueWorld`). This is reported, not fixed — changing it alters every rendered
frame in the project and wants an explicit decision.
