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

> **REFITTED 2026-08-04 after the LOD size fix.** The previous run of this sweep was measured while
> `lod.build_mips` overwrote every membrane's SIZE column with a uniform value, so it described a
> world where per-grain size did not vary. These numbers are from the rebuilt sweep. See
> "What the fix changed" below — most terms got 38–64% cheaper and one got 61% dearer.

---

## The finding

**Expansions is the dominant predictor (R² = 0.9917), superseding the earlier grain-count and
coverage models.** Every fit is on the same 35 rows:

| predictor | fit | R² |
|---|---|---:|
| **tile expansions** | `render_ms = 3.8342e-05·x + 22.053` | **0.9917** |
| grain count (`n_lod`) | `render_ms = 6.1699e-04·x + 14.215` | 0.4940 |
| visible grains (`n_vis`) | `render_ms = 1.3336e-03·x + 17.149` | 0.4489 |
| expansions per splat | `render_ms = 1.0752e+00·x + 17.919` | 0.2962 |
| coverage fraction | `render_ms = 6.1374e+01·x + 21.256` | 0.1568 |

### Correlation matrix (Pearson r, n = 35)

|                        |   n_lod |   n_vis | coverage | expansions | exp/splat | render_ms |
|------------------------|--------:|--------:|---------:|-----------:|----------:|----------:|
| **n_lod**              |   1.000 |   0.977 |    0.283 |      0.696 |     0.245 |     0.703 |
| **n_vis**              |   0.977 |   1.000 |    0.203 |      0.657 |     0.193 |     0.670 |
| **coverage_frac**      |   0.283 |   0.203 |    1.000 |      0.345 |     0.606 |     0.396 |
| **expansions**         |   0.696 |   0.657 |    0.345 |      1.000 |     0.514 | **0.996** |
| **expansions_per_splat** | 0.245 |   0.193 |    0.606 |      0.514 |     1.000 |     0.544 |
| **render_ms**          |   0.703 |   0.670 |    0.396 |  **0.996** |     0.544 |     1.000 |

`n_lod ↔ n_vis` at 0.977 says uploaded and visible counts are nearly the same variable, so nothing
is gained by budgeting one over the other. `coverage ↔ expansions/splat` at 0.606 is the only place
coverage carries real signal — it tracks how *big* the splats are, not how much work they cause.

## Read this before quoting 0.9917

**One row carries it.** `aTerrain @ 0.25×` is 7.95M expansions and 324 ms; the next-largest is
1.00M. Refit without it:

| predictor | n = 35 | n = 34 (outlier removed) |
|---|---:|---:|
| expansions | 0.9917 | **0.8971** |
| coverage | 0.1568 | 0.4624 |
| grain count | 0.4940 | **0.0848** |

**Quote 0.90 for an ordinary scene.** The ranking survives — expansions win by ≥0.43 either way,
and grain count collapsing to 0.085 shows its apparent 0.49 was the same single point.

**The refit is the real test and the model passed it.** On the previous, flattened-size sweep the
outlier-free R² was 0.8293. On honest data it is **0.8971**. A cost model for splats was not
depending on splat size being constant.

**Two rows render nothing.** `aSaltOcean` and `aSteppeBiomes` at 0.25× have the camera inside the
shell: 0 visible splats, 0 expansions, 9.4–9.8 ms. That is the pipeline's true fixed floor; the
fitted intercept of 22.1 ms is a line bending toward the outlier.

**Worst residuals:**

| term | zoom | expansions | actual | predicted | error |
|---|---:|---:|---:|---:|---:|
| aSaltOcean | 0.25× | 0 | 9.36 ms | 22.05 ms | −135.5% |
| aSteppeBiomes | 0.25× | 0 | 9.84 ms | 22.05 ms | −124.2% |
| aBlueWorld | 0.50× | 385,997 | 46.50 ms | 36.85 ms | +20.7% |
| theRockyPlanet | 0.50× | 362,071 | 45.17 ms | 35.94 ms | +20.5% |
| theRockyPlanet | 0.25× | 1,002,290 | 70.08 ms | 60.48 ms | +13.7% |

The two −100% rows are the empty frames the intercept cannot represent. The rest sit inside ±21%,
against a measured noise floor of ±13% on this box (the 4090 is shared) — worse for small frames.

## What the LOD size fix changed

`lod.build_mips` had been overwriting the base level's SIZE with `β·2R/√N`. Removing that changed
what scenes cost, in both directions, because the uniform law was inflating most membranes and
shrinking a few:

| term | zoom | expansions before | after | change |
|---|---:|---:|---:|---:|
| aSaltOcean | 0.50× | 321,675 | 117,278 | **−63.5%** |
| aSteppeBiomes | 0.50× | 321,383 | 117,261 | −63.5% |
| aHuman | 0.25× | 568,425 | 228,414 | −59.8% |
| aTerrain | 0.50× | 774,065 | 363,186 | −53.1% |
| theMining | 0.25× | 1,307,982 | 804,771 | −38.5% |
| aTerrain | 0.25× | 12,834,678 | 7,945,093 | −38.1% |
| aBlueWorld | 0.25× | 520,905 | 553,530 | +6.3% |
| theRockyPlanet | 0.25× | 624,060 | 1,002,290 | **+60.6%** |

The derived budget tracked it automatically: `MAX_EXPANSIONS_PER_FRAME` moved 6,154,819 → 4,641,046
because the slope was refitted, not because anyone chose a number.

## The case that motivated the sweep

| term | zoom | grains drawn | coverage | expansions | /splat | ms |
|---|---:|---:|---:|---:|---:|---:|
| `theMining` | 0.25× | 9,000 | 49.5% | **804,771** | 98.7 | **57.1** |
| `aBlueWorld` | 0.50× | 43,000 | 95.7% | 385,997 | 27.2 | 46.5 |

theMining draws **4.8× fewer grains at half the coverage and costs 23% more.** Neither superseded
model can express that; the expansion count is 2.1× higher and says exactly why.

## Method notes

- **The camera aims at the origin** via `pos → yaw/pitch`, not `atan2(-pos[1], pos[0])`, which is
  correct only at `pos[0] == 0` and renders bare background elsewhere. A benchmark timing an empty
  frame reports the clear-screen cost as the render cost.
- **Coverage is measured off the rendered image**, not predicted from geometry.
- **The heaviest term per class**, not a median member — the budget question is about the worst case.
- **Expansions are read from the frame that was just timed** (`pipe.tile_stats()`), not recomputed.
- **No `sand` class row.** No term classifies as `sand` with a non-empty buffer; the sweep covers
  the 7 classes that exist, not the 8 `_classify_type` can return.
- **Resolution matters more than it looks.** An earlier A/B of the LOD fix ran at 960×540, where
  `lod_count = ρ·r_px²` quarters and 20 of 47 terms select a coarse mip — those terms reported 0.0%
  change and read as evidence of safety when the case under test had simply never run.
