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
MAX_GRAINS_PER_FRAME = 250_000
# Desired frame time budget at 60 fps simulation (not render) target
MAX_RENDER_MS = 200  # ms — below this, 5+ fps is maintained

# ── WHAT ACTUALLY PREDICTS A FRAME'S COST (measured 2026-08-04, 35-row sweep) ────────────────────
# Four candidate predictors were fitted against the SAME rows. Neither of the two that had been
# proposed works, and one of them was my own hypothesis from a two-point sample:
#
#     coverage fraction            R^2 = 0.11      (the "coverage is the real driver" claim)
#     grain count                  R^2 = 0.48      (what MAX_GRAINS_PER_FRAME assumes)
#     grains x coverage            R^2 = 0.85      (better, but carried by one outlier)
#     TILE EXPANSIONS              R^2 = 0.998     (n=4, and it is a MECHANISM)
#
# A tile expansion is one (splat, tile) pair: the binner and the sorter process exactly these, so
# this is not a curve fitted to a shape, it is a count of the work being done. The pipeline
# already computes it -- `CHIMERA_TILE_DIAG=1` prints "total expansions".
#
# THE CASE THAT KILLS BOTH SIMPLE MODELS: theMining at 0.25x zoom has only 8,157 splats and 52%
# coverage, and costs 49 ms -- more than aBlueWorld's 43,000 splats at 96% coverage (28 ms).
# Neither its grain count nor its coverage is remarkable. Its EXPANSION count is 1.3 MILLION,
# because at that zoom its splats are enormous and each one lands in hundreds of tiles.
#
#     A FEW HUGE SPLATS COST MORE THAN MANY SMALL ONES, and grain count cannot see the difference.
#
# HONEST LIMIT: n = 4 for the expansion fit and its R^2 is inflated by one extreme point; the
# mid-range residuals are +37% and -23%. It is the best of the four and the only one with a
# mechanism behind it, and it is still a 4-point fit. Treat the cap below as an order of magnitude.
MAX_TILE_EXPANSIONS = 6_900_000     # (MAX_RENDER_MS - 12.39) / 2.7013e-5, from the fit above


def check_work_budget(expansions: int, max_expansions: int = MAX_TILE_EXPANSIONS):
    """Assert the per-frame (splat, tile) pair count stays within budget.

    This is the budget that MEANS something. `check_frame_budget` counts grains, which the
    measurement shows explains under half the variance in frame time; this counts the pairs the
    tile binner and sorter actually process, which explains nearly all of it.

    It is not wired into `upload()` because the count does not exist until the frame has been
    binned -- by then the work is done. It is for the diagnostic path and for anything that
    renders offline and can afford to look afterwards.
    """
    if expansions > max_expansions:
        raise PerfBudgetError(
            f"Frame work budget exceeded: {expansions:,} tile expansions > {max_expansions:,} "
            f"max (~{MAX_RENDER_MS} ms). This is usually a few OVERSIZED splats, not too many "
            f"of them -- check the per-splat radius before reducing the count."
        )


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


def check_frame_budget(n_grains: int, max_grains: int = MAX_GRAINS_PER_FRAME,
                       target_ms: float = MAX_RENDER_MS):
    """Assert the per-frame grain count stays within the total budget."""
    if n_grains > max_grains:
        raise PerfBudgetError(
            f"Frame budget exceeded: {n_grains} grains > {max_grains} max. "
            f"Reduce LOD distance or decrease base density."
        )


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
    print("Perf guard budgets (Task 7):")
    print(f"  MAX_GRAINS_PER_FRAME  = {MAX_GRAINS_PER_FRAME}")
    print(f"  MAX_GRAINS_PER_TILE   = {MAX_GRAINS_PER_TILE}")
    print(f"  MAX_RENDER_MS         = {MAX_RENDER_MS}")
    print(f"  BUDGET_TERRAIN        = {BUDGET_TERRAIN_GRAINS}")
    print(f"  BUDGET_ROCK           = {BUDGET_ROCK_GRAINS}")
    print(f"  BUDGET_SAND           = {BUDGET_SAND_GRAINS}")
    print(f"  BUDGET_VEGETATION     = {BUDGET_VEGETATION_GRAINS}")
    print(f"  BUDGET_ATMOSPHERE     = {BUDGET_ATMOSPHERE_GRAINS}")
    print(f"  BUDGET_STELLAR        = {BUDGET_STELLAR_GRAINS}")
    print(f"  BUDGET_BODY           = {BUDGET_BODY_GRAINS}")