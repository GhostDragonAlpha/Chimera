"""
Tests for LightEngine.neighbor spatial-grid neighbor list.

Validates that the grid-based resistance force and neighbor counts match the
pairwise reference implementation in LightEngine.kernel.
"""

import numpy as np
import pytest

from LightEngine import kernel, neighbor
from LightEngine.constants import R_WALL, R_BOND, R_C

TOL_REL = 1e-5


def _relative_max_error(a: np.ndarray, b: np.ndarray) -> float:
    """Max over particles of |a-b| / max(|b|, 1)."""
    denom = np.maximum(np.linalg.norm(b, axis=1), 1.0)
    errs = np.linalg.norm(a - b, axis=1) / denom
    return float(np.max(errs))


def test_empty_positions():
    """Neighbor list must handle the empty point set gracefully."""
    pos = np.zeros((0, 3), dtype=np.float32)
    vel = np.zeros((0, 3), dtype=np.float32)
    offsets, neighbors = neighbor.build_neighbor_list(pos, R_C)
    assert offsets.shape == (1,)
    assert neighbors.shape == (0,)
    acc = neighbor.compute_resistance_grid(pos, vel, offsets, neighbors)
    assert acc.shape == (0, 3)


def test_neighbor_counts_match_brute():
    """Grid neighbor counts must equal the brute-force definition."""
    rng = np.random.default_rng(123)
    n = 500
    pos = rng.uniform(-2.0, 2.0, (n, 3)).astype(np.float32)
    grid_counts = neighbor.neighbor_counts(pos, R_C)
    brute_counts = kernel.brute_neighbor_counts(pos, R_C)
    np.testing.assert_array_equal(grid_counts, brute_counts)


def test_neighbor_list_contains_same_pairs():
    """Every grid-listed pair must be within R_C and no in-range pair may be missing."""
    rng = np.random.default_rng(456)
    n = 300
    pos = rng.normal(0, 0.5, (n, 3)).astype(np.float32)
    offsets, neighbors = neighbor.build_neighbor_list(pos, R_C)

    # build reference adjacency
    rc2 = R_C * R_C
    ref_counts = np.zeros(n, dtype=np.int32)
    for i in range(n):
        c = 0
        for j in range(n):
            if i == j:
                continue
            d2 = np.sum((pos[j] - pos[i]) ** 2)
            if d2 <= rc2:
                c += 1
        ref_counts[i] = c

    grid_counts = offsets[1:] - offsets[:-1]
    np.testing.assert_array_equal(grid_counts, ref_counts)

    # verify every listed pair is in range and no duplicates for a given i
    for i in range(n):
        seen = set()
        for k in range(offsets[i], offsets[i + 1]):
            j = int(neighbors[k])
            assert j != i
            assert j not in seen
            seen.add(j)
            d2 = np.sum((pos[j] - pos[i]) ** 2)
            assert d2 <= rc2 + 1e-6


def test_resistance_grid_matches_pairwise_2048():
    """
    Core validation: grid-based resistance force equals pairwise resistance
    for 2048 random grains within relative tolerance 1e-5.
    """
    rng = np.random.default_rng(20260807)
    n = 2048
    pos = rng.uniform(-3.0, 3.0, (n, 3)).astype(np.float32)
    vel = rng.normal(0, 0.1, (n, 3)).astype(np.float32)

    a_pair = kernel.compute_resistance(pos, vel, use_cuda=False)
    a_grid = neighbor.compute_resistance_grid(pos, vel)

    rel_err = _relative_max_error(a_grid, a_pair)
    assert rel_err <= TOL_REL, f"relative max error {rel_err:.3e} > {TOL_REL}"


def test_resistance_grid_wall_and_bond_branches():
    """Grid resistance must match pairwise for wall-overlap and bond-zone pairs."""
    # wall overlap
    pos_w = np.array([[0.0, 0.0, 0.0], [0.02, 0.0, 0.0]], dtype=np.float32)
    vel_w = np.array([[0.5, 0.0, 0.0], [-0.5, 0.0, 0.0]], dtype=np.float32)
    a_pair_w = kernel.compute_resistance(pos_w, vel_w, use_cuda=False)
    a_grid_w = neighbor.compute_resistance_grid(pos_w, vel_w)
    np.testing.assert_allclose(a_grid_w, a_pair_w, rtol=1e-5, atol=1e-6)

    # bond zone
    pos_b = np.array([[0.0, 0.0, 0.0], [0.12, 0.0, 0.0]], dtype=np.float32)
    vel_b = np.zeros_like(pos_b)
    a_pair_b = kernel.compute_resistance(pos_b, vel_b, use_cuda=False)
    a_grid_b = neighbor.compute_resistance_grid(pos_b, vel_b)
    np.testing.assert_allclose(a_grid_b, a_pair_b, rtol=1e-5, atol=1e-6)


def test_resistance_grid_with_prebuilt_list():
    """Passing prebuilt offsets/neighbors must reproduce the same force."""
    rng = np.random.default_rng(789)
    n = 1024
    pos = rng.uniform(-2.0, 2.0, (n, 3)).astype(np.float32)
    vel = rng.normal(0, 0.05, (n, 3)).astype(np.float32)

    offsets, neighbors = neighbor.build_neighbor_list(pos, R_C)
    a1 = neighbor.compute_resistance_grid(pos, vel)
    a2 = neighbor.compute_resistance_grid(pos, vel, offsets, neighbors)
    np.testing.assert_allclose(a1, a2, rtol=1e-7, atol=1e-7)
