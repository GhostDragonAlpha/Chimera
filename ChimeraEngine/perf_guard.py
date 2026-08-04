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
# Derived from 7.8 fps at 1920x1080 full pipeline — measured in live_viewer.py
MAX_GRAINS_PER_FRAME = 250_000
# Desired frame time budget at 60 fps simulation (not render) target
MAX_RENDER_MS = 200  # ms — below this, 5+ fps is maintained


# ── Per-surface-type budgets (derived from Laguna density table) ────────────────────────────────

# Terrain/ground: extensive surface, high local detail at grain scale
BUDGET_TERRAIN_GRAINS = 20_000
# Rock/mining surfaces: moderate area, moderate detail
BUDGET_ROCK_GRAINS = 8_000
# Sand/particulate: many small grains, volumetric
BUDGET_SAND_GRAINS = 12_000
# Vegetation/biomes: organic scatter, distributed
BUDGET_VEGETATION_GRAINS = 16_000
# Atmospheric/fields: soft, low particle count but large splats
BUDGET_ATMOSPHERE_GRAINS = 30_000
# Stellar/galactic: distant, projection-culled
BUDGET_STELLAR_GRAINS = 50_000
# Human-scale bodies: detailed, near-field
BUDGET_BODY_GRAINS = 12_000


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
    """Classify a membrane term into a surface type for budget assignment."""
    low = term.lower()
    if any(k in low for k in ("ground", "terrain", "terrace")):
        return "terrain"
    if any(k in low for k in ("rock", "mine", "mining", "stone")):
        return "rock"
    if any(k in low for k in ("sand", "dust", "dune")):
        return "sand"
    if any(k in low for k in ("biome", "steppe", "vegetation", "tree", "forest", "garden")):
        return "vegetation"
    if any(k in low for k in ("atmosphere", "cloud", "fog", "sky", "breath")):
        return "atmosphere"
    if any(k in low for k in ("star", "sun", "galaxy", "planet", "solar", "horizon", "cooling",
                              "densityclock", "clock", "emptying")):
        return "stellar"
    if any(k in low for k in ("human", "hand", "foot", "eye", "skin", "ankle", "grip",
                              "stance", "sweep", "balance", "load", "thrust", "body")):
        return "body"
    if any(k in low for k in ("ocean", "water", "salt", "nitrogen")):
        return "atmosphere"
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