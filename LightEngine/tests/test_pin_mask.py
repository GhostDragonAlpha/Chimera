"""
Pinned-point mask tests.

A pinned point still exerts forces on the world, but the integrator never moves it.
"""

import numpy as np
import pytest

from LightEngine import kernel


def _wall_pair():
    """Two points inside the wall radius; they repel strongly."""
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.02, 0.0, 0.0]], dtype=np.float32)
    vel = np.zeros_like(pos)
    return pos, vel


@pytest.mark.parametrize("use_cuda", [False, True])
def test_pinned_point_does_not_move(use_cuda):
    """Point 0 pinned; point 1 free. Only point 1 moves."""
    if use_cuda and not kernel.cuda_is_available():
        pytest.skip("CUDA not available")

    pos, vel = _wall_pair()
    sim = kernel.VelocityVerlet(2, use_cuda=use_cuda)
    sim.set_state(pos, vel)
    sim.set_pin_mask(np.array([True, False], dtype=bool))
    sim.compute_acceleration()

    p0_before = sim.pos[0].copy()
    for _ in range(10):
        sim.step()

    np.testing.assert_array_equal(sim.pos[0], p0_before)
    assert not np.allclose(sim.pos[1], pos[1])


@pytest.mark.parametrize("use_cuda", [False, True])
def test_unpinned_pair_moves(use_cuda):
    """Same start with no pins: both points move apart."""
    if use_cuda and not kernel.cuda_is_available():
        pytest.skip("CUDA not available")

    pos, vel = _wall_pair()
    sim = kernel.VelocityVerlet(2, use_cuda=use_cuda)
    sim.set_state(pos, vel)
    sim.compute_acceleration()
    for _ in range(10):
        sim.step()

    assert not np.allclose(sim.pos, pos)


def test_ensemble_pin_mask():
    """EnsembleVerlet respects per-world pin masks."""
    if not kernel.cuda_is_available():
        pytest.skip("CUDA not available")

    pos, vel = _wall_pair()
    worlds = np.stack([pos, pos], axis=0)
    vels = np.stack([vel, vel], axis=0)
    masks = np.array([[True, False], [False, False]], dtype=bool)

    ens = kernel.EnsembleVerlet(2, 2)
    ens.set_all(worlds, vels)
    ens.set_all_pin_masks(masks)
    ens.compute_acceleration()
    for _ in range(10):
        ens.step()
    ens.sync_from_device()

    # world 0: point 0 pinned
    np.testing.assert_array_equal(ens.pos[0, 0], pos[0])
    assert not np.allclose(ens.pos[0, 1], pos[1])
    # world 1: no pins
    assert not np.allclose(ens.pos[1], pos)
