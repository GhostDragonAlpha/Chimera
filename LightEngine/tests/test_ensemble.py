"""
EnsembleVerlet tests.

Prediction (docs/THE_ENSEMBLE.md): batching W worlds on one CUDA context
produces the same trajectories as running each world solo, because the force
kernels are per-point independent and the batched kernels preserve the exact
operation sequence.
"""

import numpy as np
import pytest

from LightEngine import kernel
from LightEngine.demo_seed import structureless_start, BOX, VEL_SIGMA


N_EQUIV = 64
TICKS_EQUIV = 1000


@pytest.fixture(scope="module")
def cuda_only():
    if not kernel.cuda_is_available():
        pytest.skip("CUDA not available")


def _solo_run(pos, vel, ticks):
    """Run a solo VelocityVerlet CUDA simulation and return final state."""
    sim = kernel.VelocityVerlet(pos.shape[0], use_cuda=True)
    sim.set_state(pos, vel)
    sim.compute_acceleration()
    for _ in range(ticks):
        sim.step()
    return sim


def _ensemble_run(worlds, velocities, ticks):
    """Run a batched EnsembleVerlet simulation and return final state."""
    W, N = worlds.shape[0], worlds.shape[1]
    ens = kernel.EnsembleVerlet(W, N)
    for w in range(W):
        ens.set_state(w, worlds[w], velocities[w])
    ens.compute_acceleration()
    for _ in range(ticks):
        ens.step()
    ens.sync_from_device()
    return ens


def test_ensemble_matches_solo(cuda_only):
    """Two different starts: ensemble positions must match solo bitwise."""
    pos_a, vel_a = structureless_start(N_EQUIV, BOX, VEL_SIGMA, 20260806)
    pos_b, vel_b = structureless_start(N_EQUIV, BOX, VEL_SIGMA, 7)

    solo_a = _solo_run(pos_a, vel_a, TICKS_EQUIV)
    solo_b = _solo_run(pos_b, vel_b, TICKS_EQUIV)

    worlds = np.stack([pos_a, pos_b], axis=0)
    vels = np.stack([vel_a, vel_b], axis=0)
    ens = _ensemble_run(worlds, vels, TICKS_EQUIV)

    # bitwise position equivalence
    assert np.array_equal(ens.pos[0], solo_a.pos), (
        f"world 0 diverged from solo after {TICKS_EQUIV} ticks")
    assert np.array_equal(ens.pos[1], solo_b.pos), (
        f"world 1 diverged from solo after {TICKS_EQUIV} ticks")

    # radiated energy within 1e-3 relative (device float32 accumulation vs host float64)
    for w, solo in enumerate((solo_a, solo_b)):
        rel = abs(ens.radiated_energy[w] - solo.radiated_energy) / (
            abs(solo.radiated_energy) + 1e-12)
        assert rel < 1e-3, (
            f"world {w} radiated energy mismatch: ensemble={ens.radiated_energy[w]}, "
            f"solo={solo.radiated_energy}, rel={rel}")


def test_world_isolation(cuda_only):
    """A violent world must not leak into a quiet world."""
    N = 64
    # world A: tight cluster at origin
    rng_a = np.random.default_rng(123)
    pos_a = rng_a.uniform(-0.01, 0.01, (N, 3)).astype(np.float32)
    vel_a = np.zeros_like(pos_a)

    # world B: one close pair far from everything else
    pos_b = np.full((N, 3), 1e6, dtype=np.float32)
    pos_b[0] = [100.0, 0.0, 0.0]
    pos_b[1] = [100.01, 0.0, 0.0]
    vel_b = np.zeros_like(pos_b)

    solo_b = _solo_run(pos_b, vel_b, 200)

    ens = _ensemble_run(np.stack([pos_a, pos_b]),
                        np.stack([vel_a, vel_b]), 200)

    assert np.array_equal(ens.pos[1], solo_b.pos), (
        "world B diverged from its solo twin — cross-world leakage detected")


def test_ensemble_determinism(cuda_only):
    """Same ensemble run twice must be bitwise identical."""
    N = 64
    rng = np.random.default_rng(99)
    worlds = rng.normal(0, 0.1, (2, N, 3)).astype(np.float32)

    vels = np.zeros_like(worlds)
    ens1 = _ensemble_run(worlds, vels, 500)
    ens2 = _ensemble_run(worlds, vels, 500)

    assert np.array_equal(ens1.pos, ens2.pos)
    assert np.array_equal(ens1.vel, ens2.vel)
    assert np.allclose(ens1.radiated_energy, ens2.radiated_energy, rtol=1e-6)
