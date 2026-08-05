"""perf_guard.py — GPU pipeline budget enforcement (Task 7).

STATEMENT: The declared render budget (grains per frame, tiles per frame, render time per frame)
forms a runtime contract. A scene that exceeds budget silently turns into a frame-drop or a black
tile — discovered only after commit. Wire the budget as runtime assertions in the render pipeline
so an over-budget scene fails LOUDLY at render, not silently at playback.

PREDICTION: An over-budget scene raises PerfBudgetError at render time, preventing an invalid
scene from shipping. The budget numbers are derived from the hardware's measured limits.

FALSIFIER: An over-budget scene renders without error — the guard is decorative.

Author: Agent (DeepSeek V4 Pro — density lane, 2026-08-04)
"""
from __future__ import annotations


class PerfBudgetError(RuntimeError):
    """Raised when a render exceeds its declared GPU budget."""
    pass


# ── DERIVED BUDGETS from measured hardware (RTX 4090, 24 GB VRAM) ────────────────────────────────

# MAX_PER_TILE is the cap in gpu_pipeline.py (16384 as of 2026-07-29)
MAX_GRAINS_PER_TILE = 16384
# MEASURED 2026-08-04 AND THE DERIVATION WAS WRONG BY 3.6x -- see docs/MEASURED_RENDER_BUDGETS.md.
# This said "derived from 7.8 fps at 1920x1080", which implies 128.2 ms for 250,000 grains. The
# real figure at exactly 250,000 grains is 35.23 +- 2.10 ms: 3.64x faster.
#
# WORSE FOR THIS CONSTANT: grain count barely drives frame time at all. 4,096 grains cost 18.83 ms
# and 262,144 cost 36.50 -- a 64x increase in grains for 1.94x the time -- while the SAME 43,000
# grains cost 28.19 ms at default framing and 45.23 ms zoomed in 2x. Identical geometry, identical
# count, 60% more time. The cost is SCREEN COVERAGE, and this constant budgets a quantity that
# does not determine the thing being budgeted.
#
# THE VALUE IS DELIBERATELY UNCHANGED. Re-deriving it from these numbers gives 2.6 MILLION if you
# fit the grain-dominated cases and 190,000 if you fit the coverage-dominated one -- a 14x spread,
# which is the model being wrong rather than the measurement being noisy. Replacing one unmeasured
# number with a better-dressed unmeasured number is the move this studio has a rule against.
# MAX_RENDER_MS below is the wall that means something; nothing in the registry is within 4x of it.
#
# SUPERSEDED 2026-08-04 AS A FRAME BUDGET. `check_frame_budget` no longer reads it --
# MAX_EXPANSIONS_PER_FRAME below is the frame check, and the 35-row sweep put grain count's R^2 at
# 0.472 (and at 0.042 with the single outlier removed, i.e. essentially no predictive power on an
# ordinary scene). This constant survives for exactly one job: the `general` fallback in
# `_classify_budget`, where the question is "is this membrane suspiciously dense" and NOT "will
# this frame drop". Those are different questions and only the second one has been solved.
MAX_GRAINS_PER_FRAME = 250_000
# Desired frame time budget at 60 fps simulation (not render) target
MAX_RENDER_MS = 200  # ms — below this, 5+ fps is maintained

# ── WHAT ACTUALLY PREDICTS A FRAME'S COST (measured 2026-08-04, FULL 35-row sweep) ───────────────
# Five candidate predictors fitted against the SAME rows -- 7 surface classes x 5 zoom levels,
# `docs/pipeline_benchmark.csv`. The earlier note here reported the expansion fit at n = 4 and
# flagged that as its weakness; this is the same fit at n = 35, so the number is no longer a
# promise:
#
#     coverage fraction            R^2 = 0.157     (the "coverage is the real driver" claim)
#     expansions per splat         R^2 = 0.296
#     visible grain count          R^2 = 0.449
#     grain count uploaded         R^2 = 0.494     (what MAX_GRAINS_PER_FRAME assumes)
#     TILE EXPANSIONS              R^2 = 0.992     (and it is a MECHANISM, not a shape)
#
# REFITTED 2026-08-04 ON HONEST DATA. The first fit was made while `lod.build_mips` was overwriting
# every membrane's SIZE column with a uniform value, so it was measured on a world where per-grain
# size DID NOT VARY -- a model of splat cost, fitted where splat size was constant. That is fixed
# (lod.py: the base level keeps its emitted sizes) and these are the numbers from the rebuilt sweep.
#
# THE MODEL SURVIVED AND GOT MORE ROBUST, which is the part worth stating. On the full 35 rows it
# moved 0.9949 -> 0.9917, which is nothing. With the single extreme point removed -- the test that
# mattered -- it moved 0.8293 -> 0.8971, while grain count stayed dead at 0.085. It was not
# depending on the flattening.
#
# THE COST ITSELF MOVED A LOT, in both directions, because the uniform law had been inflating most
# membranes and shrinking a few: aTerrain@0.25x 12.83M -> 7.95M expansions (-38%), aHuman -60%,
# aSaltOcean -64%, but theRockyPlanet@0.25x 624k -> 1.00M (+61%).
#
# A tile expansion is one (splat, tile) pair. The binner emits exactly these, the sorter sorts
# exactly these, and the compositor walks exactly these per pixel -- so this is a count of work,
# not a curve fitted to a silhouette.
#
# THE CASE THAT KILLS BOTH SIMPLE MODELS: theMining at 0.25x zoom has 8,157 visible splats and 52%
# coverage, and costs 65 ms -- more than aBlueWorld's 43,000 splats at 96% coverage (45 ms).
# Neither its grain count nor its coverage is remarkable. Its EXPANSION count is 1.31 MILLION,
# because at that zoom each of its grains lands in ~160 tiles.
#
#     A FEW HUGE SPLATS COST MORE THAN MANY SMALL ONES, and grain count cannot see the difference.
#
# THE HONEST LIMIT SURVIVED THE BIGGER SAMPLE AND THE REFIT, and it is the same one: ONE extreme
# point carries the headline figure. Drop aTerrain at 0.25x (7.95M expansions, 324 ms):
#
#     expansions R^2 = 0.897 | grains R^2 = 0.085 | coverage R^2 = 0.462   (n = 34)
#
# So 0.992 is inflated and 0.90 is the number to quote for an ordinary scene. THE RANKING IS NOT
# INFLATED -- expansions wins by 0.44 over the next best either way, and grain count COLLAPSES to
# 0.085 without the outlier, which means its apparent 0.49 was that single point too. The model
# being replaced was standing on the same rock as the model replacing it; only one of them is
# still standing when the rock is removed.
#
# TWO ROWS RENDER NOTHING (aSaltOcean and aSteppeBiomes at 0.25x: the camera is inside the shell,
# 0 visible splats, 0 expansions) and they cost 9.4-9.8 ms. That is the REAL fixed floor of this
# pipeline -- kernel launches, the two host round-trips, the image download. The fitted intercept
# of 22.1 ms is higher because a straight line has to bend to reach the outlier; when a budget
# says "a scene costs 22 ms before it draws anything", the measured answer is under 10.
MS_PER_EXPANSION = 3.8342e-05      # slope, n=35 least squares, docs/pipeline_benchmark.csv
FIXED_MS = 22.053                  # fitted intercept (measured empty-frame floor is ~9.6 ms)


def expansions_for_ms(target_ms: float) -> int:
    """How many (splat, tile) pairs fit inside `target_ms`, from the measured fit.

    THE CAP IS DERIVED, NEVER CHOSEN. The alternative on the table was "measure one membrane at
    default framing and multiply by 1.5", and it is worth recording why that was not taken: it
    makes the budget a property of whichever membrane got measured, and the 50% is taste wearing
    a decimal point. Measured against the 35-row sweep, a cap built that way (aRockyPlanet at
    default framing = 149,302 -> cap 223,953) fires on 12 of 35 rows and FIVE OF THOSE RENDER IN
    UNDER 33 ms -- it flags fast scenes as over budget, which is precisely the false-positive
    check the same task asked for. A wall you cannot pass without being wrong is not a wall.

    AND A DERIVED CAP MOVES WHEN THE WORLD DOES. Fixing the LOD size flattening changed what
    scenes cost -- most fell 38-64%, one rose 61% -- and the cap tracked it from 6.15M to 4.64M
    without anyone choosing a number, because the slope was refitted and the wall did not move.
    A cap set as "the measured scene x 1.5" would have needed a human to notice and re-measure.

    Inverting the fit ties the cap to the only number here anybody declared on purpose: how long a
    frame is allowed to take. Change MAX_RENDER_MS and every cap moves with it.
    """
    return max(0, int((float(target_ms) - FIXED_MS) / MS_PER_EXPANSION))


# THE FRAME CAP, DERIVED FROM THE DECLARED WALL. At MAX_RENDER_MS = 200 this is ~4.64M. It read
# 6.15M against the pre-fix sweep; the drop is the refitted slope, not a decision.
#
# READ THIS BEFORE RAISING AN EYEBROW AT HOW LOOSE IT IS. 200 ms is 5 fps. A cap derived from it
# fires on exactly ONE of the 35 measured rows, and it lets theMining at 0.25x (805k expansions,
# 57 ms) through. That is not the guard failing -- 57 ms IS inside a 200 ms budget, and a guard
# that fired there would be disagreeing with the wall it was derived from. If a 57 ms frame should
# be an error, the thing that is wrong is MAX_RENDER_MS, and it is one line above. For reference,
# measured against the same 35 rows:
#
#     MAX_RENDER_MS = 200 (5 fps)   -> cap 4,641,028   1 row fires,  0 false positives
#     MAX_RENDER_MS =  33 (30 fps)  -> cap   293,532   9 rows fire
#     MAX_RENDER_MS =  16 (60 fps)  -> cap         0   every row fires -- the FLOOR alone is 22 ms,
#                                                      so 60 fps is not reachable by ANY scene here
#                                                      and no budget can express it
#
# That last line is the useful one: this pipeline cannot render a 60 fps frame at 1920x1080 even
# empty, so a 60 fps target is a statement about the pipeline, not about any membrane in it.
MAX_EXPANSIONS_PER_FRAME = expansions_for_ms(MAX_RENDER_MS)
MAX_TILE_EXPANSIONS = MAX_EXPANSIONS_PER_FRAME      # the previous name, kept for existing callers


def check_frame_budget(expansions: int, max_expansions: int = None,
                       target_ms: float = MAX_RENDER_MS):
    """Assert the per-frame (splat, tile) pair count stays within budget.

    THE ARGUMENT CHANGED MEANING AND THE OLD ONE CANNOT BE PASSED BY ACCIDENT IN A WAY THAT
    MATTERS. This used to take a grain count against MAX_GRAINS_PER_FRAME; it now takes tile
    expansions. A stale caller handing it grains compares a number against a cap 25x larger and
    simply never fires -- it goes quiet rather than lying, which is the failure direction to
    prefer, but `gpu_pipeline.upload()` was the only such caller and it no longer calls this at
    all. Expansions DO NOT EXIST at upload time; the frame has to be binned first.

    A frame is charged for every pair the binner emits, including the ones the per-tile cap is
    about to evict -- so this is checked against the pre-cap total. See `_tile_stats` in
    gpu_pipeline for why that is the right side of the cap to budget.
    """
    cap = MAX_EXPANSIONS_PER_FRAME if max_expansions is None else max_expansions
    if expansions > cap:
        raise PerfBudgetError(
            f"Frame budget exceeded: {expansions:,} tile expansions > {cap:,} max "
            f"(~{target_ms:.0f} ms at {MS_PER_EXPANSION:.4g} ms/expansion + {FIXED_MS:.1f} ms "
            f"fixed). Predicted {MS_PER_EXPANSION*expansions + FIXED_MS:.0f} ms. This is usually "
            f"a few OVERSIZED splats, not too many of them -- check the per-splat radius "
            f"(pipe.expansions_per_splat()) before reducing the count."
        )


def check_work_budget(expansions: int, max_expansions: int = None):
    """The name this check had while `check_frame_budget` still meant grains. Same check."""
    check_frame_budget(expansions, max_expansions)


def predicted_ms(expansions: int) -> float:
    """What the fit says this frame should cost. For a HUD that wants to show the model's guess
    next to the measured time -- a model whose disagreement with reality is on screen is a model
    somebody will notice going wrong."""
    return MS_PER_EXPANSION * float(expansions) + FIXED_MS


# ── Per-surface-type budgets (derived from Laguna density table) ────────────────────────────────

# Terrain/ground: extensive surface, high local detail at grain scale
BUDGET_TERRAIN_GRAINS = 300_000
# Rock/mining surfaces: moderate area, moderate detail
BUDGET_ROCK_GRAINS = 50_000
# Sand/particulate: many small grains, volumetric
BUDGET_SAND_GRAINS = 20_000
# Vegetation/biomes: organic scatter, distributed
BUDGET_VEGETATION_GRAINS = 40_000
# Atmospheric/fields: soft, low particle count but large splats
BUDGET_ATMOSPHERE_GRAINS = 50_000
# Stellar/galactic: distant, projection-culled
BUDGET_STELLAR_GRAINS = 60_000
# Human-scale bodies: detailed, near-field
BUDGET_BODY_GRAINS = 20_000


def check_surface_budget(term: str, n_grains: int):
    """Assert a surface membrane meets its per-type grain budget.

    Maps membrane names to their surface class budgets using substring matching
    against the known surface type patterns.
    """
    budget = _classify_budget(term)
    if n_grains > budget:
        raise PerfBudgetError(
            f"Surface budget exceeded for '{term}': {n_grains} grains > {budget} max "
            f"(type: {_classify_type(term)}). Lower splat density or reduce feature detail."
        )


def check_tile_budget(tile_count: int, grains_per_tile: int,
                       max_per_tile: int = MAX_GRAINS_PER_TILE):
    """Assert no tile exceeds the per-tile grain cap."""
    if grains_per_tile > max_per_tile:
        raise PerfBudgetError(
            f"Tile budget exceeded: {grains_per_tile} grains in one tile > {max_per_tile} max. "
            f"Largest splats may be too big — reduce grain size or increase MAX_PER_TILE."
        )


def _classify_type(term: str) -> str:
    """Classify a membrane term into a surface type for budget assignment.

    THE ORDER IS THE ALGORITHM. These are SUBSTRING tests over a name, so a term matching two
    classes is decided entirely by which check runs first -- and the old order ran "rock" before
    "planet". `aRockyPlanet` (29,732 grains) and `theRockyPlanet` (41,974) were therefore judged
    as MINING FACES against an 8,000-grain budget and reported as budget violations. A rocky
    planet is not a rock face; two of the twelve reported violations were the instrument.

        MATCHING NAMES IS NOT MATCHING DEFINITIONS, and a classifier that decides by substring
        is a place where that failure is guaranteed rather than merely possible.

    So the order now runs MOST SPECIFIC FIRST -- a whole world before a surface on one, a body
    before the fluid around it -- and the reordering was checked against all 42 terms rather than
    the two that prompted it. Exactly two classifications changed (both RockyPlanets, rock ->
    stellar); the other forty are untouched.

    THE OCEAN GROUP IS FOLDED INTO ATMOSPHERE HERE, and dropping it would have been a silent
    regression. It used to sit in a trailing check AFTER "general" would otherwise have been
    reached, and a naive reordering into eight classes loses it -- `aSaltOcean` and `theOcean`
    would fall through to "general" and inherit the 250,000-grain frame budget, so their real
    overages against the 30,000 fluid budget would simply stop being reported. A reorder that
    drops a class does not look like a bug; it looks like fewer violations.
    """
    low = term.lower()
    # 1. WHOLE WORLDS AND WHAT THEY ORBIT -- before any surface that sits on one.
    if any(k in low for k in ("star", "sun", "galaxy", "planet", "solar", "horizon", "cooling",
                              "densityclock", "clock", "emptying")):
        return "stellar"
    # 2. THE SURFACE UNDERFOOT -- before "rock", so a terraced mine is ground, not a mine face.
    if any(k in low for k in ("ground", "terrain", "terrace")):
        return "terrain"
    # 3. THE BODY -- before the fluids it moves through.
    if any(k in low for k in ("human", "hand", "foot", "eye", "skin", "ankle", "grip",
                              "stance", "sweep", "balance", "load", "thrust", "body")):
        return "body"
    # 4. FLUIDS -- air and water share a budget: both are large, soft and low-count.
    if any(k in low for k in ("atmosphere", "cloud", "fog", "sky", "breath",
                              "ocean", "water", "salt", "nitrogen")):
        return "atmosphere"
    # 5. WORKED STONE -- what is left that is genuinely a rock face.
    if any(k in low for k in ("rock", "mine", "mining", "stone")):
        return "rock"
    if any(k in low for k in ("biome", "steppe", "vegetation", "tree", "forest", "garden")):
        return "vegetation"
    if any(k in low for k in ("sand", "dust", "dune")):
        return "sand"
    return "general"


def _classify_budget(term: str) -> int:
    """Return the grain budget for a membrane based on its surface type."""
    t = _classify_type(term)
    return {
        "terrain": BUDGET_TERRAIN_GRAINS,
        "rock": BUDGET_ROCK_GRAINS,
        "sand": BUDGET_SAND_GRAINS,
        "vegetation": BUDGET_VEGETATION_GRAINS,
        "atmosphere": BUDGET_ATMOSPHERE_GRAINS,
        "stellar": BUDGET_STELLAR_GRAINS,
        "body": BUDGET_BODY_GRAINS,
        "general": MAX_GRAINS_PER_FRAME,
    }[t]


def report(term: str, n_grains: int) -> str:
    """Report budget status for a membrane (non-fatal — for logging)."""
    budget = _classify_budget(term)
    pct = n_grains / max(budget, 1) * 100.0
    status = "OK" if n_grains <= budget else "OVER"
    return f"{term:30s} {n_grains:>7d}/{budget:>7d} ({pct:5.1f}%) {status}"


if __name__ == "__main__":
    print("Perf guard budgets:")
    print(f"  MAX_RENDER_MS            = {MAX_RENDER_MS} ms   <- the declared wall; everything below is derived from it")
    print(f"  MAX_EXPANSIONS_PER_FRAME = {MAX_EXPANSIONS_PER_FRAME:,}  "
          f"= ({MAX_RENDER_MS} - {FIXED_MS}) / {MS_PER_EXPANSION:.4e}")
    for _t in (16.7, 33.3, 50.0, 100.0, 200.0):
        print(f"      at {_t:6.1f} ms ({1000/_t:5.1f} fps) the cap would be {expansions_for_ms(_t):>10,d}")
    print(f"  MAX_GRAINS_PER_FRAME     = {MAX_GRAINS_PER_FRAME}  (SUPERSEDED as a frame budget; "
          f"still the `general` surface fallback)")
    print(f"  MAX_GRAINS_PER_TILE      = {MAX_GRAINS_PER_TILE}")
    print(f"  BUDGET_TERRAIN        = {BUDGET_TERRAIN_GRAINS}")
    print(f"  BUDGET_ROCK           = {BUDGET_ROCK_GRAINS}")
    print(f"  BUDGET_SAND           = {BUDGET_SAND_GRAINS}")
    print(f"  BUDGET_VEGETATION     = {BUDGET_VEGETATION_GRAINS}")
    print(f"  BUDGET_ATMOSPHERE     = {BUDGET_ATMOSPHERE_GRAINS}")
    print(f"  BUDGET_STELLAR        = {BUDGET_STELLAR_GRAINS}")
    print(f"  BUDGET_BODY           = {BUDGET_BODY_GRAINS}")