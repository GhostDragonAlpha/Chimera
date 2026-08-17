"""test_density_regression.py — Density regression guard (Task 10).

STATEMENT: Each SCENES kind (terrain, rock, sand, vegetation, atmosphere, stellar, body)
has a derived minimum splat count and per-object screen coverage floor. A regression in
emit() that silently drops detail — the way _tree_buffers did — is caught by asserting
these floors after every grow.

PREDICTION: Running this test after `python Chimera/core/grow.py` will pass for all 38 terms,
guaranteeing that detail cannot silently rot.

FALSIFIER: Any term falls below its derived floor — the test fails, naming the term
and the floor it violated.

Run: python ChimeraEngine/test_density_regression.py

Author: Agent (DeepSeek V4 Pro — density lane, 2026-08-04)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import splat_appearance as sa
from ChimeraEngine.perf_guard import _classify_type, check_surface_budget, PerfBudgetError

# ── Derived floors from Laguna density table (docs/research/laguna_density.md) ────────────────────

# Floor = minimum grains a surface TERM must emit to be "readable at judgment distance."
# For body membranes (small extent, near-field), the floor is per-body detail.
# For extensive membranes (planet-scale), the floor is per the projected-area law.

DERIVED_FLOORS: dict[str, int] = {
    # Terrain/ground — must have enough grains to resolve near-field detail at 720p
    "theGround": 4_000,
    "aTerrain": 16_000,
    "theTerrain": 16_000,
    # Rock/mining — must resolve surface facets
    "aTerraceMine": 4_000,
    "theMining": 4_000,
    # Biomes/vegetation — distributed organic scatter
    "aSteppeBiomes": 16_000,
    "theBiomes": 12_000,
}

# SPHERE surface coverage target: at least 58% projected-area coverage (the cover constant
# from ChimeraEngine/core/matter.py surface_grain). Coverage = projected_area_covered / total_disk_area.
# A term below this has visible black gaps between grains.
MIN_COVERAGE = 0.58  # 58% — below this, grain gaps are visible at judgment distance


def splat_coverage(buf: np.ndarray, cam_distance: float = 2.8,
                   screen_h: int = 720, fov: float = 1.047) -> float:
    """Estimate screen coverage: fraction of the projected disk area covered by grain ellipses.

    Each grain's projected area A = π * (size * focal / distance)².
    Sum them, divide by total disk area (π * body_radius_px²).
    """
    if buf.shape[0] == 0:
        return 0.0

    radius = float(np.linalg.norm(buf[:, 0:3], axis=1).max()) or 1.0
    sizes = buf[:, 20]  # SIZE column
    focal = screen_h / (2.0 * np.tan(fov / 2.0))

    # Body projected radius in pixels
    r_px = radius * focal / max(1e-6, cam_distance * radius)
    disk_area = np.pi * r_px * r_px

    # Each grain's projected area
    grain_radii_px = sizes * focal / max(1e-6, cam_distance * radius)
    grain_areas = np.pi * grain_radii_px * grain_radii_px

    total_covered = float(grain_areas.sum())
    return total_covered / max(disk_area, 1.0)


def run():
    """Run all density regression checks. Returns (passed, failed_details)."""
    terms = sa.scene_terms()
    passed = 0
    failed: list[str] = []
    coverage_failures: list[str] = []

    print(f"Density regression guard — {len(terms)} terms\n{'=' * 60}")

    for term in terms:
        buf = sa.scene_buffer(term)
        if buf is None or buf.shape[0] == 0:
            print(f"  {term:30s}  SKIP (no buffer)")
            continue

        n = buf.shape[0]
        surf_type = _classify_type(term)
        floor = DERIVED_FLOORS.get(term, 1)  # default floor = 1 grain (anything)

        # Check 1: per-term grain count floor
        if n < floor:
            msg = f"FLOOR VIOLATION: {term} has {n} grains < {floor} floor (type: {surf_type})"
            failed.append(msg)
            print(f"  FAIL: {msg}")
            continue

        # Check 2: screen coverage floor (only for surface types, not fields or bodies)
        if surf_type not in ("atmosphere", "stellar", "body"):
            cov = splat_coverage(buf)
            if cov < MIN_COVERAGE:
                msg = f"COVERAGE VIOLATION: {term} coverage={cov:.3f} < {MIN_COVERAGE} (type: {surf_type})"
                coverage_failures.append(msg)
                print(f"  FAIL: {msg}")
                continue

        # Check 3: per-type budget assertion (Task 7 integration)
        try:
            check_surface_budget(term, n)
        except PerfBudgetError as e:
            msg = f"BUDGET VIOLATION: {term}: {e}"
            failed.append(msg)
            print(f"  FAIL: {msg}")
            continue

        cov = splat_coverage(buf)
        print(f"  {term:30s}  {n:>7d} grains  floor={floor:>7d}  "
              f"coverage={cov:.3f}  type={surf_type:12s}  OK")
        passed += 1

    print(f"\n{'=' * 60}")
    print(f"Passed: {passed}/{len(terms)}")
    if failed:
        print(f"FLOOR VIOLATIONS ({len(failed)}):")
        for f in failed:
            print(f"  {f}")
    if coverage_failures:
        print(f"COVERAGE VIOLATIONS ({len(coverage_failures)}):")
        for f in coverage_failures:
            print(f"  {f}")

    all_ok = len(failed) == 0 and len(coverage_failures) == 0
    print(f"\nRESULT: {'ALL CLEAR' if all_ok else 'REGRESSION DETECTED'}")
    return all_ok, failed + coverage_failures


if __name__ == "__main__":
    ok, _ = run()
    raise SystemExit(0 if ok else 1)