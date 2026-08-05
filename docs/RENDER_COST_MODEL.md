# THE RENDER COST MODEL — what a frame costs

> **STATEMENT.** A frame's cost is set by **tile expansions** — the number of `(splat, tile)` pairs
> the pipeline produces — and not by grain count or by pixel coverage.
>
> **PREDICTION.** Across 7 surface classes × 5 zoom levels, expansions predict frame time with
> R² > 0.9 while grain count and coverage each stay under 0.5. A scene with few large splats costs
> more than a scene with many small ones at equal grain count.
>
> **FALSIFIER (named before the sweep).** Expansions R² drops below 0.9 on the full 35-row set.
>
> **RESULT: did not fire. R² = 0.9923, n = 35** — and this is the *fourth* time it did not fire.
> The first fit was made while LOD was flattening every membrane's splat size, so it measured a
> world where splat size did not vary. That is fixed; the model was refitted on honest data and
> **got more robust** (§5a). §3 and §5 are where this document argues against itself.

Measured 2026-08-04, RTX 4090, 1920×1080, `TILE_SIZE = 32` (2,040 tiles).
Data: [`pipeline_benchmark.csv`](pipeline_benchmark.csv) (35 rows) ·
[`pipeline_terms.csv`](pipeline_terms.csv) (47 terms).
Regenerate: `python ChimeraEngine/benchmark_pipeline.py` and `--audit`.

---

## 1. What the pipeline is billed for

A **tile expansion** is one `(splat, tile)` pair. `_build_tiles_gpu` computes each visible splat's
screen footprint and emits one pair per tile it touches:

```
n_x = ⌈(px + FOOTPRINT·r)/32⌉ − ⌊(px − FOOTPRINT·r)/32⌋    expansions_for_this_splat = n_x · n_y

                       FOOTPRINT = 1.2390, derived in §8 (was a hand-written 1.5)
```

Summed over visible splats, that is the frame's expansion count. It is already computed on the
live path — the zero-check needs it on the host — so reading it costs **no additional
device→host transfer**. `pipe.expansion_count()` returns it for the frame just rendered.

**Two scenes of the same grain count can differ by 300×.** `theMining` at 0.25× zoom draws 8,157
visible splats into 804,771 expansions (99 tiles each); `aTerrain` at 5× zoom draws 2,098 into
8,320 (4 tiles each). Grain count sees 4× between them. The pipeline pays 97×.

## 2. The equation

```
render_ms ≈ 3.6085e-05 × expansions + 14.413            n = 35, R² = 0.9923
```

Coefficients live in `ChimeraEngine/perf_guard.py` as `MS_PER_EXPANSION` and `FIXED_MS`, and the
frame budget is the equation **inverted**, never a chosen number:

```python
MAX_EXPANSIONS_PER_FRAME = expansions_for_ms(MAX_RENDER_MS)   # (200 − 14.413) / 3.6085e-05
```

| frame-time wall | derived cap | rows firing (of 35) |
|---|---:|---:|
| 200 ms (5 fps) — **declared** | 5,143,051 | 1 |
| 33 ms (30 fps) | 523,403 | — |
| 16.7 ms (60 fps) | 63,378 | — |

**60 fps became arithmetically expressible during this work.** On the previous sweep the 16.7 ms
cap came out at literally **0** — the fitted floor exceeded a 60 fps frame, so no scene could reach
it. It is now 84,089. Do not read that as an 8 ms speedup: an empty frame has zero expansions, so
nothing in §7 or §8 could have moved the floor. The measured empty-frame cost read 9.4–9.8 ms then
and 7.7–7.9 ms now, and the difference is what else the shared 4090 was doing. **Quote the floor as
a range, and never read a change in it as a change in the renderer.**

> **The one lever.** To make the guard stricter, change `MAX_RENDER_MS`; everything else moves with
> it. **A derived cap also moves when the world does** — fixing the LOD size flattening changed
> what scenes cost (most fell 38–64%, one rose 61%) and the cap tracked from 6.15M to 4.64M with
> nobody choosing anything. A cap set as "the measured scene × 1.5" would have needed a human to
> notice and re-measure.

## 3. The mechanism — and the part of it that was assumed wrong

The expected story was: *the binner allocates each pair, the sorter sorts them, the compositor
blends them; all three scale with expansions.* **Two of those three are right, and the one that is
wrong is the one that dominates.** Per-stage timing, medians of 3, syncs between stages:

| scene | expansions | BIN + SORT | **COMPOSITE** |
|---|---:|---:|---:|
| aTerrain 0.25× | 7,945,093 | 14.1 ms (6%) | **215.0 ms (90%)** |
| theMining 0.25× | 804,771 | 6.4 ms (18%) | **24.6 ms (69%)** |
| aBlueWorld 0.25× | 553,530 | 6.4 ms (22%) | **17.0 ms (59%)** |
| theZero @ d=1.0 | 100,000 | 6.2 ms (17%) | **27.4 ms (73%)** |
| theZero @ d=2.8e-6 | 8,160,000 | 15.0 ms (72%) | **1.6 ms (8%)** |

*(measured before §8; the stage ratios hold, the absolute numbers are ~10% lower now)*

**Binning and sorting are 6–35% of the frame.** The compositor is 59–90%, and it does not walk
expansions — it walks *pixels*, and per pixel walks that pixel's tile list:

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

— **expansions × 1024, truncated per tile by opacity saturation**. Expansions predict well
whenever saturation depth is roughly constant across a scene, which is true of ordinary surfaces.

**The last row is the model failing, on purpose.** `theZero` has `body_radius = 0`, so the framing
rule `2.8 × max(R, 1e-6)` puts the camera 2.8 µm away and every splat covers all 2,040 tiles: 8.16M
expansions, 33× more than any other term. It composites in **1.6 ms**, because every pixel
saturates after ~2 splats and breaks. The same term at `d = 1.0` produces 82× *fewer* expansions
and costs **17× more** to composite. Expansions are wrong by ~1000× there.

> **Trust it** on ordinary surfaces, where splats are semi-transparent and a pixel walks most of
> its list. **Do not** on scenes whose splats are large *and* opaque enough to saturate at once.
> The tell is `expansions_per_splat` above ~1000.

## 4. The practical rule

**To speed up a slow scene, shrink the largest splats. Reducing grain count may do nothing.**
`theMining` at 0.25× costs 37 ms with 9,000 grains; `aBlueWorld` at 0.5× costs 36 ms with 43,000.

```bash
python ChimeraEngine/benchmark_pipeline.py --audit
```

1. `pipe.expansions_per_splat()` — tiles per visible splat. **The number to act on.**
2. `CHIMERA_SPLAT_SIZE_DIAG=1` — is the SIZE column broadly large, or is there a tail?
3. `CHIMERA_TILE_DIAG=1` — which tiles, and are any over `MAX_PER_TILE` (an eviction = something
   not drawn).

**Check the framing before editing an `emit()`.** A large `expansions_per_splat` has two causes
that look identical — grains too large, or a camera too close for the body's extent — and
`theZero`, the only term tripping the half-screen warning, is the second kind: its SIZE is 0.03,
among the *smallest* of all 47 membranes. `_report_expansions` reports the measured projected
radius so the two can be told apart.

**A size clamp is a real lever now, and it costs physics.** `CHIMERA_CLAMP_SPLAT_SIZE=1` caps SIZE
at 2× the buffer's mean. On `aYellowStar` that hits 5,000 splats and saves **67.6% of expansions
and 47.5% of render time** (52.8 → 27.7 ms) — but the 5,000 splats it clamps *are the corona*, so
it buys that time by re-introducing the exact defect §7 describes. On `theMining` and `thePlanets`
it changes nothing (0 splats over 2× mean). It is a lens, not a fix.

## 5. What is wrong with this model

**(a) One point carries the R², and this is the third sweep where that is true.**
Drop `aTerrain @ 0.25×` (7.95M expansions, 324 ms):

| | full (n=35) | outlier removed (n=34) |
|---|---:|---:|
| expansions | 0.9923 | **0.8860** |
| coverage | 0.1455 | 0.4375 |
| grain count | 0.4827 | **0.0613** |

Quote **0.89** for an ordinary scene, not 0.99. The *ranking* is not inflated — expansions win by
≥0.43 either way, and grain count collapsing to 0.085 shows its apparent 0.49 was that same single
point. **The refit is the interesting part:** on the old flattened-size data the outlier-free R²
was 0.8293; on honest data it is 0.8971. The model was not living off the flattening.

**(b) The fitted intercept is not the real floor, and the floor is not a constant.** Two rows
render nothing (`aSaltOcean` and `aSteppeBiomes` at 0.25× — camera inside the shell, 0 visible
splats). Across four sweeps they cost **9.4–9.8**, then **7.7–7.9**, then **8.7–9.1 ms**, with zero
expansions every time — that spread is contention, not code. The fitted 14.4 ms is a line bending
toward the outlier.

**The slope is noisy the same way, and it is the honest limit on every coefficient here.** §9's
device-side depth sort made all 47 terms faster when measured interleaved, and the refitted slope
still went *up* (3.15e-05 → 3.61e-05) because the two sweeps ran under different contention. Trust
the fit for **ranking predictors** and for an order-of-magnitude cap. Do not read a 15% move in
either coefficient between sweeps as meaning anything.

**(c) It is calibrated on bursts and the live viewer is slower.** The benchmark times 3 frames
after 2 warm-ups. Under the viewer's sustained loop the same work runs **1.7–4.9× slower** than
predicted. Part is environmental — this box shares its 4090, measured at 17.1 GB VRAM held and 27%
utilisation by other processes while idle — and part is unexplained. **Do not use `predicted_ms` as
a performance claim.** It is on `/stats` beside the measured time so the disagreement stays visible.

**(d) Frame time has a large noise floor.** Renders with *identical* work measured −13.6%/+11.2% on
two scenes; small frames (10–30 ms) swung up to ±44%. Treat any single-frame difference under ~15%
as noise, and under ~45% for sub-30 ms frames.

**(e) It says nothing about correctness.** A frame inside budget can still be wrong: `MAX_PER_TILE`
evicts far splats in an overfull tile — a visual defect with no cost signature.
`tile_expansion_ratio` on `/stats` tracks it.

## 6. The superseded models, with their evidence

| model | R² (n=35) | R² without outlier | verdict |
|---|---:|---:|---|
| **tile expansions** | **0.9923** | **0.8860** | in use — `MAX_EXPANSIONS_PER_FRAME` |
| grain count (`n_lod`) | 0.4827 | 0.0613 | **superseded.** `MAX_GRAINS_PER_FRAME = 250,000` |
| visible grain count | 0.4311 | — | never shipped |
| expansions per splat | 0.3187 | — | a *diagnostic*, not a predictor of total cost |
| pixel coverage | 0.1455 | 0.4375 | **refuted** as the dominant driver |

Correlation against `render_ms`: expansions **0.996** · n_lod 0.695 · n_vis 0.657 ·
expansions/splat 0.565 · coverage 0.381.

**The per-class grain budgets rank the classes wrongly, and honest sizes made it worse: 7 of 7
classes now misrank** (it was 5 of 7 on flattened data). `terrain` holds the largest allowance
(300,000) and ranks 4th in cost; `general` holds 250,000 and ranks 1st; `body` holds the smallest
(20,000) and ranks 5th. Rescaling by `exp_per_grain` is the mechanical fix. The honest one is that
a grain budget answers a density question and cannot be made into a cost budget.

## 7. RESOLVED — LOD was discarding every membrane's emitted splat size

**Found while building these diagnostics; fixed 2026-08-04; this section is the record.**

`lod.build_mips` overwrote the SIZE column with `β·2R/√N` at every level **including the base**.
For coarse levels that law is correct — a level of N resampled points must have grains that tile
the surface. Applied to the full-detail level it discarded what `emit()` wrote. **44 of 47 terms
reached the GPU with one unique SIZE value.**

The fix: the base level keeps its emitted sizes; coarse mips keep the law. `lod.py`, one line.

**The disagreement it was hiding spans 0.50× to 23.15×**, in both directions:

| term | law | emit (mean) | law/emit | what the law was doing |
|---|---:|---:|---:|---|
| `thePlanets` | 0.3441 | 0.0149 | **23.15×** | nine planets of nine sizes merged into one bar |
| `theThrust` | 0.0739 | 0.0056 | 13.23× | a labelled physics diagram rendered as an orange blob |
| `theGrip` | 0.1163 | 0.0119 | 9.80× | — |
| `aRockyPlanet` | 0.1058 | 0.0155 | 6.81× | magnetic field lines 7× too thick, smeared together |
| `theGround` | 0.0437 | 0.0069 | 6.30× | 17,344 distinct emitted sizes flattened to one |
| `theMining` | 0.0528 | 0.0299 | 1.77× | terrace steps smoothed off the silhouette |
| `aYellowStar` | 0.0440 | 0.0784 | **0.56×** | corona shrunk 7.5× → disintegrated into speckle |
| `theCloud` | 0.0507 | 0.1020 | 0.50× | — |

**Verified by A/B over all 47 terms at 1920×1080** (`ab_hd.json`, both variants rendered in one
process from the same buffers):

- **24 of 46 base-selecting terms now upload a real size distribution.** `aYellowStar` reads two
  bins (26,000 core at 0.03, 5,000 corona at 0.33; `std` 0 → 0.110). `theGround` has 17,344
  distinct sizes, `theEye` 57, `theHand` 12.
- **Nothing disintegrated.** 0 of 45 terms fragmented; 42 of 45 have zero enclosed background
  before and after. The three flagged (`aRockyPlanet`, `theGrip`, `theThrust`) are thin-structure
  membranes where enclosed background is the correct topology, confirmed by looking at them.
- **Coverage fell on 23 terms and it is not damage.** It falls when bloat is removed and rises
  when disintegration is repaired — both are improvements, so coverage cannot detect holes and
  the topology metrics above were used instead.
- 47/47 pass `test_render_pipeline.py`; no term dimmed >50% or lost >20% of its grains.

**Bakes are unaffected** — `bake_splats.py` reads `sa.scene_buffer()` directly and never touches
the LOD path.

> **The lesson for the cost model:** it was fitted on a world where splat size was constant, which
> is the one condition under which "count the pairs" and "count the grains" are hardest to tell
> apart. It survived being refitted on a world where size varies by 23× within a single membrane.

## 8. The binner was expanding 21% further than the compositor can use

**Derived, not swept. Fixed 2026-08-04. `gpu_pipeline.FOOTPRINT`.**

`_inv_radii` sets `rad = 3.0·√eig_max` — **3σ** on the major axis. The binner expanded each splat's
tile footprint to `1.5·rad` = **4.5σ**. But `_composite` drops a splat the moment its Gaussian
weight falls under 0.001:

```
wgt = exp(−0.5·ge) < 0.001   ⟹   ge > −2·ln(0.001) = 13.8155   ⟹   3.7169 σ
```

So every `(splat, tile)` pair between 3.717σ and 4.5σ was binned, sorted, and walked per pixel —
then discarded by a test it could never pass. The required multiplier is `3.7169/3 = 1.2390`, and
the constant is written as that derivation so it tracks if either input changes:

```python
WGT_CUTOFF   = 0.001                                  # _composite's own threshold
_SIGMA_REACH = math.sqrt(-2.0 * math.log(WGT_CUTOFF)) # 3.7169
_RAD_IN_SIGMA = 3.0                                   # _inv_radii: rad = 3*sqrt(eig)
FOOTPRINT = _SIGMA_REACH / _RAD_IN_SIGMA              # 1.2390  (was a hand-written 1.5)
```

**The falsifier was bit-identity, and it did not fire.** If 3.717σ is the true reach, the discarded
pairs contribute nothing and every frame must be unchanged. Measured across **all 47 terms: worst
pixel difference 0.** At the boundary a splat contributes `opacity × 0.001` — under 0.25 of a
0–255 step, below quantisation.

**Measured, interleaved A/B in one process** (variants alternated so contention drift hits both):

| scene | expansions | render_ms | fps |
|---|---:|---:|---|
| aTerrain 0.25× | −9.2% | −9.7% | 3.9 → 4.3 |
| theRockyPlanet 0.25× | −20.3% | −8.8% | 18.8 → 20.6 |
| theMining 0.25× | −12.8% | −10.5% | 23.9 → 26.7 |
| aBlueWorld 0.50× | −25.5% | −7.3% | 25.6 → 27.6 |
| aHuman 0.25× | −26.0% | −7.4% | 46.4 → 50.2 |
| aYellowStar 1.00× | −28.6% | −14.2% | 13.3 → 15.5 |

Across all 47 terms at default framing: **−18.1% expansions, −6.5% median frame time.** The sign is
consistent on every scene, which is what separates it from the ±13% noise floor — noise flips sign.

**Why 18% and not the 31.8% the area ratio predicts:** `(1.5/1.239)² = 1.466` is the *asymptote*,
true only for splats spanning many tiles. A splat covering 1–4 tiles is dominated by the `⌈⌉`
quantisation and the `+1`, and shrinking its radius changes nothing. The saving scales with how
large the splats already are — which is the same thing the whole cost model has been saying.

**Also found:** `_sort_tiles` (gpu_pipeline.py:438) is dead code — never called since the CuPy
binner sorts on device. And the `ge > 20.0` test in `_composite` is unreachable: `wgt < 0.001`
fires first, at ge = 13.82.

## 9. The depth sort left the GPU every frame

**Fixed 2026-08-04. `_visible_prefix` / `_depth_order` in `gpu_pipeline.py`.**

`render_from_gpu` left the device twice mid-frame:

1. download `n` visibility bools → `np.cumsum` on the host → upload `n` int32
2. download `nv` depths → **`np.argsort` of up to 262,144 floats on one CPU core** → upload `nv` int32

The second is the expensive one, and the cost is not the transfer — it is a full CPU sort inside a
GPU pipeline, every frame. This project already has the rule written down (*nothing reads back from
the GPU inside the loop*; the attempt that ignored it ran 300× slower than the CPU) and the render
path had been quietly breaking it.

Both are CuPy one-liners, and CuPy is already a hard dependency of the tile binner. **Exactly one
sync survives, and it must:** `nv` sizes every later kernel launch, so it is now read as the last
element of the inclusive prefix sum — **4 bytes instead of `n` bools**.

**Measured** (per-term, all 47 at default framing; the one apparent regression, `aTerrain` at
+18%, was cross-run contention and measured **−3.7%** when interleaved):

| | |
|---|---|
| median frame time | **−12.2%** |
| terms faster | **46 of 47** (47/47 interleaved) |
| the 14 terms over 100k expansions | **−13.8%** median |
| expansion counts changed | **0** — this touches no geometry |

### The falsifier fired, and what it caught was already broken

Bit-identity was the named falsifier. **12 of 47 terms changed.** The correlation with tied depths
is exact:

| term | tied depths | pixels changed | max diff |
|---|---:|---:|---:|
| aBlueWorld | 0.2% | **0** | 0 |
| theMining | 0.1% | **0** | 0 |
| theClock | 0.2% | 46 | 1 |
| aTerrain | 98.4% | 48,498 | 39 |
| theGrip / theLoad / theThrust | **100%** | up to 7,528 | up to 174 |

Every term with ~no ties was bit-identical; every term that changed had ties. `theGrip`, `theLoad`
and `theThrust` have **one unique depth across all their splats** — they are flat diagrams, so
their compositing order never had a defined answer.

**And CuPy was not the culprit.** `cp.argsort` default and `kind="stable"` agree on all 47 terms —
all 12 differences trace to **numpy's** default `quicksort`, which is unstable. The committed
behaviour was the arbitrary one: tie order decided by introsort internals.

So both paths now use `kind="stable"`, which tie-breaks on original index = **emit order**, the
membrane's own layering. Verified: numpy-stable and cupy-stable produce identical permutations on a
50%-tied array, so a machine without CuPy renders the same pixels as one with it — which was *not*
true of the unstable pair. And it is **cheaper than the unstable default** (0.109 ms vs 0.133 ms at
n=31,581); there was no trade to make.

> The change did not introduce an arbitrary ordering and then contain it. It **removed** one that
> had been in the render all along, on every membrane with coplanar splats.

## 10. TILE_SIZE: 32 is the optimum, and both my prediction and my first measurement were wrong

**Swept 2026-08-04. Result: no change. `TILE_SIZE` stays 32.**

A legitimate sweep, and the distinction matters: `FOOTPRINT` (§8) came out of the compositor's own
cutoff and searching for it would have been an admission. A tile size answers to the hardware, not
the world — nothing in the physics of this game knows what 32 means.

**Prediction, made before the run.** Compositor work ≈ `expansions × T²`. For r >> T,
`expansions ≈ (2·FOOTPRINT·r/T)²` so work ≈ `(2.478r)²`, *independent of T*; for r << T,
expansions = 1 and work = T², so small tiles win. Against that, `_composite` uses 16×16 thread
blocks, so at T = 8 a warp straddles two tiles and diverges. **⟹ T=16 should win.**

**Measured** — 12 cases spanning heavy/light/flat/degenerate, one process and one isolated numba
cache per value:

| | T=8 | T=16 | **T=32** | T=64 |
|---|---:|---:|---:|---:|
| median vs T=32 | 1.60× | 1.27× | **1.00×** | 1.34× |
| geomean | 1.77× | 1.41× | **1.00×** | 1.34× |
| screen tiles | 32,400 | 8,160 | 2,040 | 510 |
| aTerrain@0.25 expansions | 107,389,864 | 27,579,055 | 7,210,490 | 1,996,797 |

**32 wins on both averages and on every case but one** (`theZero`, the degenerate r=0 framing where
every splat covers the screen, prefers T=64 at 0.67×). Both directions lose for opposite reasons:
smaller tiles quadruple expansions per halving and the binner and sorter pay for every pair; larger
tiles make the compositor test each splat against 4× more pixels.

**The prediction was refuted, and the error is instructive: the binner and sorter scale with
expansions ALONE, not `expansions × T²`.** §3 measured them at 6–35% of the frame — but that was
*at T=32*. At T=8 expansions are 15× higher and that stage dominates. **A stage share measured at
one setting is not a constant of the pipeline.**

**The falsifier — the picture must not change, since tiling is a work partition — did not fire.**
Output is identical across all four tile sizes on all 12 cases.

### The first run of this sweep was measured with a broken instrument

Recorded because it produced two confident, wrong findings and nearly shipped both.

`@cuda.jit(cache=True)` keys its on-disk cache on the function source and signature, **not on the
values of the module globals the kernel closed over.** `TILE_SIZE` is one of those — `_composite`
bakes it in at compile time — so a process running a swept value wrote a kernel built for the wrong
tile grid into the *shared* cache, and the next process at the default silently loaded it. The
binner is pure CuPy and honours the real value, so the two halves of the pipeline disagreed.

What the poisoned sweep reported, and what is actually true:

| claim from the poisoned run | truth |
|---|---|
| "the render depends on TILE_SIZE" — 12 of 12 cases differed, correlating exactly with splats over 1000 px | **entirely the artifact.** Output is identical across all T |
| T=64 is **8% faster** on geomean | T=64 is **34% slower** |
| T=8 is 2.21× slower | 1.77× slower |

**A control ran and could not see it.** Rendering the *same* TILE_SIZE twice in two processes gave
0 pixel difference on all five cases — because both runs shared the same poisoned kernel. What
caught it was `test_render_pipeline.py`: the very next run had membranes rendering **NOTHING**,
which is exactly the regression the baseline was added to detect. *A control that cannot express
the failure is not a control; the guard that had no idea what it was looking for is what worked.*

**Fixed so it cannot recur:** a non-default `TILE_SIZE` now compiles `_composite` with
`cache=False`. It costs a recompile per process — what a measurement run should pay — and makes a
sweep unable to corrupt the default. Verified: a `TILE_SIZE=64` run followed by a default run
passes 47/47.

**Also found and fixed:** `self._tf`/`self._to` back an `n_tiles + 1` array and were sized
`max(20000, n_particles)` — a number about the wrong quantity. At T=32 that is 8,161 and the 20,000
floor happened to cover it; at T=8 it is 32,401 and a scene with fewer grains would have written
past the end. Now derived from the tile grid at 4K.
