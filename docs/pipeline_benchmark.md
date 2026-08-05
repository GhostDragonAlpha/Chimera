# Pipeline benchmark — the 35-row sweep

The heaviest term in each of 7 surface classes, at 5 zoom levels, 1920×1080, RTX 4090.
3 timed frames after 2 warm-ups. Data: [`pipeline_benchmark.csv`](pipeline_benchmark.csv).
The model built on it: [`RENDER_COST_MODEL.md`](RENDER_COST_MODEL.md).

```bash
python ChimeraEngine/benchmark_pipeline.py
```

`--quick` runs 3 classes. `--audit` runs every renderable term at default framing instead
(→ [`pipeline_terms.csv`](pipeline_terms.csv), 47 rows) and reports the per-class budget audit.

**Zoom is a distance multiplier: `dist = 2.8 × body_radius × zoom`. 0.25× is CLOSE, 5× is far.**

---

## The finding

**Expansions is the dominant predictor (R² = 0.9949), superseding the earlier grain-count and
coverage models.** Every fit is on the same 35 rows:

| predictor | fit | R² |
|---|---|---:|
| **tile expansions** | `render_ms = 2.9083e-05·x + 21.002` | **0.9949** |
| grain count (`n_lod`) | `render_ms = 7.3501e-04·x + 11.194` | 0.4717 |
| visible grains (`n_vis`) | `render_ms = 1.5902e-03·x + 14.667` | 0.4295 |
| expansions per splat | `render_ms = 9.4439e-01·x + 13.789` | 0.3072 |
| coverage fraction | `render_ms = 6.6613e+01·x + 20.657` | 0.1273 |

### Correlation matrix (Pearson r, n = 35)

|                        |   n_lod |   n_vis | coverage | expansions | exp/splat | render_ms |
|------------------------|--------:|--------:|---------:|-----------:|----------:|----------:|
| **n_lod**              |   1.000 |   0.977 |    0.281 |      0.703 |     0.260 |     0.687 |
| **n_vis**              |   0.977 |   1.000 |    0.206 |      0.669 |     0.224 |     0.655 |
| **coverage_frac**      |   0.281 |   0.206 |    1.000 |      0.328 |     0.658 |     0.357 |
| **expansions**         |   0.703 |   0.669 |    0.328 |      1.000 |     0.535 | **0.997** |
| **expansions_per_splat** | 0.260 |   0.224 |    0.658 |      0.535 |     1.000 |     0.554 |
| **render_ms**          |   0.687 |   0.655 |    0.357 |  **0.997** |     0.554 |     1.000 |

Two rows worth reading sideways: `n_lod ↔ n_vis` at 0.977 says uploaded and visible counts are
nearly the same variable, so nothing is gained by budgeting one over the other. And
`coverage ↔ expansions/splat` at 0.658 is the only place coverage carries real signal — coverage
tracks how *big* the splats are, not how much work they cause.

## Read this before quoting 0.9949

**One row carries it.** `aTerrain @ 0.25×` is 12.8M expansions and 393 ms; the next-largest row is
1.3M. Refit without it:

| predictor | n = 35 | n = 34 (outlier removed) |
|---|---:|---:|
| expansions | 0.9949 | **0.8293** |
| coverage | 0.1273 | 0.4493 |
| grain count | 0.4717 | **0.0419** |

**Quote 0.83 for an ordinary scene.** The ranking survives — expansions win by ≥0.38 either way,
and grain count collapsing to 0.042 shows its apparent 0.47 was the same single point.

**Two rows render nothing.** `aSaltOcean` and `aSteppeBiomes` at 0.25× have the camera inside the
shell: 0 visible splats, 0 expansions, 10.1–10.3 ms. That is the pipeline's true fixed floor. The
fitted intercept of 21.0 ms is higher because a line must bend toward the outlier.

**Worst residuals of the n=35 fit:**

| term | zoom | expansions | actual | predicted | error |
|---|---:|---:|---:|---:|---:|
| aBlueWorld | 0.50× | 417,732 | 44.95 ms | 33.15 ms | +26.3% |
| aSteppeBiomes | 0.25× | 0 | 10.09 ms | 21.00 ms | −108.1% |
| aSaltOcean | 0.25× | 0 | 10.27 ms | 21.00 ms | −104.4% |
| theRockyPlanet | 0.25× | 624,060 | 47.88 ms | 39.15 ms | +18.2% |
| aTerrain | 0.50× | 774,065 | 34.83 ms | 43.51 ms | −24.9% |
| theMining | 0.25× | 1,307,982 | 65.56 ms | 59.04 ms | +9.9% |

The two −100% rows are the empty frames the intercept cannot represent. The rest sit inside ±26%,
against a **measured run-to-run noise floor of ±13%** on this box (the 4090 is shared).

## The case that motivated the whole sweep

| term | zoom | grains drawn | coverage | expansions | /splat | ms |
|---|---:|---:|---:|---:|---:|---:|
| `theMining` | 0.25× | 9,000 | 52.3% | **1,307,982** | 160.4 | **65.6** |
| `aBlueWorld` | 0.50× | 43,000 | 95.9% | 417,732 | 29.4 | 45.0 |

theMining draws **4.8× fewer grains at half the coverage and costs 46% more.** Neither superseded
model can express that; the expansion count is 3.1× higher and says exactly why.

## Method notes

- **The camera aims at the origin** via `pos → yaw/pitch`, not `atan2(-pos[1], pos[0])`. That
  expression is correct only at `pos[0] == 0` and renders bare background elsewhere — a benchmark
  timing an empty frame reports the clear-screen cost as the render cost.
- **Coverage is measured off the rendered image**, not predicted from geometry, so it cannot
  disagree with what was drawn.
- **The heaviest term per class**, not a median member — the budget question is about the worst
  case, and a median-member benchmark says everything is fine.
- **Expansions are read from the frame that was just timed** (`pipe.tile_stats()`), not recomputed,
  so predictor and predicted come from the same render.
- **No `sand` class row.** No term classifies as `sand` with a non-empty buffer; the sweep covers
  the 7 classes that exist, not the 8 `_classify_type` can return.
