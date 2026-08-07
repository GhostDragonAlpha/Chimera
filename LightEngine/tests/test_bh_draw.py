"""
Tests for LightEngine.bh_draw Barnes-Hut DRAW acceleration.

Validates that the GPU treecode matches the pairwise DRAW reference within the
chosen theta budget, is deterministic, and preserves octree invariants.
"""

import math
import numpy as np
import pytest

from LightEngine import bh_draw, kernel
from LightEngine.constants import G, EPS

TOL_REL = 1e-3
VALIDATION_N = 4096
VALIDATION_SEED = 20260807


def _jittered_lattice(n: int, spacing: float = 0.05,
                      jitter_frac: float = 0.2, seed: int = 42) -> np.ndarray:
    """Non-overlapping grains: cubic lattice plus small jitter."""
    rng = np.random.default_rng(seed)
    side = int(math.ceil(n ** (1.0 / 3.0)))
    pos = []
    for idx in range(n):
        ix = idx % side
        iy = (idx // side) % side
        iz = idx // (side * side)
        p = np.array([ix - side / 2.0, iy - side / 2.0, iz - side / 2.0],
                     dtype=np.float32)
        p += rng.uniform(-jitter_frac, jitter_frac, size=3)
        pos.append(p)
    pos = np.array(pos, dtype=np.float32) * spacing
    pos -= pos.mean(axis=0)
    return pos


def _relative_max_error(a: np.ndarray, b: np.ndarray) -> float:
    """Max relative L2 error over particles."""
    denom = np.linalg.norm(b, axis=1)
    denom = np.where(denom == 0, 1.0, denom)
    errs = np.linalg.norm(a - b, axis=1) / denom
    return float(np.max(errs))


def test_theta_trace_and_default_selection():
    """
    Measure BH accuracy for the required theta set and choose the default.
    The default is the largest theta whose max relative error is <= 1e-3.
    """
    pos = _jittered_lattice(VALIDATION_N, seed=VALIDATION_SEED)
    tree = bh_draw.build_octree(pos, leaf_size=16)
    a_pair = kernel.compute_draw(pos, use_cuda=False)

    trace = {}
    for theta in (0.3, 0.5, 0.7, 1.0):
        a_bh = bh_draw.compute_draw_bh(pos, theta=theta, tree=tree, leaf_size=16)
        trace[theta] = _relative_max_error(a_bh, a_pair)

    # With leaf_size=16, theta=0.3 already meets the 1e-3 budget; record the
    # finer trace for completeness.
    candidate_thetas = [0.20, 0.15, 0.12, 0.10, 0.08, 0.05]
    for theta in candidate_thetas:
        a_bh = bh_draw.compute_draw_bh(pos, theta=theta, tree=tree, leaf_size=16)
        trace[theta] = _relative_max_error(a_bh, a_pair)

    # Publish the largest theta with error <= 1e-3.
    valid = [(t, e) for t, e in trace.items() if e <= TOL_REL]
    assert valid, f"no theta achieved rel err <= {TOL_REL}; trace = {trace}"
    valid.sort(key=lambda x: x[0])
    chosen_theta, chosen_err = valid[-1]

    print(f"\nBH theta trace (N={VALIDATION_N}):")
    for t in sorted(trace):
        mark = " <-- DEFAULT" if t == chosen_theta else ""
        print(f"  theta={t:.2f}  rel_err={trace[t]:.6f}{mark}")

    bh_draw.set_default_theta(chosen_theta)
    assert chosen_err <= TOL_REL


def test_accuracy_at_default_theta():
    """GPU BH at the validated default theta is within 1e-3 of pairwise."""
    pos = _jittered_lattice(VALIDATION_N, seed=VALIDATION_SEED)
    a_pair = kernel.compute_draw(pos, use_cuda=False)
    a_bh = bh_draw.compute_draw_bh(pos)
    rel_err = _relative_max_error(a_bh, a_pair)
    assert rel_err <= TOL_REL, f"rel_err={rel_err:.6e} > {TOL_REL}"


def test_gpu_matches_cpu_reference():
    """GPU kernel agrees with the CPU reference implementation."""
    pos = _jittered_lattice(1024, seed=7)
    for theta in (0.1, 0.5):
        a_cpu = bh_draw.compute_draw_bh_cpu(pos, theta=theta)
        a_gpu = bh_draw.compute_draw_bh(pos, theta=theta)
        rel_err = _relative_max_error(a_gpu, a_cpu)
        assert rel_err <= 1e-6, f"theta={theta} GPU/CPU rel_err={rel_err:.3e}"


def test_determinism():
    """Same positions and theta produce bitwise-identical output."""
    pos = _jittered_lattice(2048, seed=99)
    a1 = bh_draw.compute_draw_bh(pos, theta=0.1)
    a2 = bh_draw.compute_draw_bh(pos, theta=0.1)
    np.testing.assert_array_equal(a1, a2)


def test_tree_mass_conservation():
    """Every particle's mass is counted exactly once up the cell chain."""
    pos = _jittered_lattice(2048, seed=11)
    tree = bh_draw.build_octree(pos)
    n = pos.shape[0]

    # Root must hold the total mass.
    assert tree["cell_mass"][0] == float(n)

    # Leaf cells cover disjoint ranges in the order array and sum to N.
    leaf_total = 0
    for c in range(tree["n_cells"]):
        if tree["cell_is_leaf"][c]:
            leaf_total += tree["cell_leaf_count"][c]
            assert tree["cell_mass"][c] == float(tree["cell_leaf_count"][c])
    assert leaf_total == n

    # For every internal cell, its mass equals the sum of its children's masses.
    for c in range(tree["n_cells"]):
        if tree["cell_is_leaf"][c]:
            continue
        child_mass = 0.0
        for k in range(8):
            child = tree["cell_child"][c, k]
            if child >= 0:
                child_mass += tree["cell_mass"][child]
        assert abs(tree["cell_mass"][c] - child_mass) < 1e-6


def test_tree_com_conservation():
    """Internal-cell COM equals the mass-weighted mean of child COMs."""
    pos = _jittered_lattice(2048, seed=22)
    tree = bh_draw.build_octree(pos)

    for c in range(tree["n_cells"]):
        if tree["cell_is_leaf"][c]:
            continue
        weighted_com = np.zeros(3, dtype=np.float64)
        total_mass = 0.0
        for k in range(8):
            child = tree["cell_child"][c, k]
            if child >= 0:
                m = tree["cell_mass"][child]
                weighted_com += m * tree["cell_com"][child]
                total_mass += m
        expected = weighted_com / total_mass
        np.testing.assert_allclose(tree["cell_com"][c], expected, rtol=1e-5, atol=1e-6)


def test_force_law_matches_kernel_constants():
    """The BH module uses the same G and EPS as the frozen constants."""
    assert bh_draw.G == G
    assert bh_draw.EPS == EPS
    assert bh_draw.EPS2 == pytest.approx(EPS * EPS)


def test_empty_and_small_inputs():
    """BH handles empty and trivial inputs without error."""
    empty = np.zeros((0, 3), dtype=np.float32)
    out = bh_draw.compute_draw_bh(empty, theta=0.1)
    assert out.shape == (0, 3)

    two = np.array([[0.0, 0.0, 0.0], [0.1, 0.0, 0.0]], dtype=np.float32)
    out = bh_draw.compute_draw_bh(two, theta=0.5)
    ref = kernel.compute_draw(two, use_cuda=False)
    np.testing.assert_allclose(out, ref, rtol=1e-5, atol=1e-6)
