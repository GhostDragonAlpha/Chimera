"""
Tests for LightEngine/seed_structures.py.

These verify the three canonical prints obey the derivations in docs/THE_PRINTER.md:
determinism, geometry, derived velocities, and momentum removal.
"""

import numpy as np
import pytest

from LightEngine import seed_structures
from LightEngine.constants import G, R_WALL, R_BOND, R_C, K_BOND


def _nearest_neighbor_distances(pos: np.ndarray) -> np.ndarray:
    """Direct O(N^2) nearest-neighbor distances; fine for the small test counts."""
    pos64 = np.asarray(pos, dtype=np.float64)
    diff = pos64[:, None, :] - pos64[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    return np.sqrt(r2.min(axis=1))


@pytest.mark.parametrize("gen,kwargs", [
    (seed_structures.core_shell, {"n": 512}),
    (seed_structures.disk, {"n": 512}),
    (seed_structures.lattice, {}),
])
def test_determinism(gen, kwargs):
    """Same seed must produce identical positions and velocities."""
    p1, v1 = gen(**kwargs, seed=42)
    p2, v2 = gen(**kwargs, seed=42)
    np.testing.assert_array_equal(p1, p2)
    np.testing.assert_array_equal(v1, v2)


def test_core_shell_orbital_velocity():
    """Shell points orbit with v = sqrt(G * M_enc / r_shell) and v ⟂ r."""
    n = 1024
    f_core = 0.5
    r_shell = 4.0
    pos, vel = seed_structures.core_shell(n, f_core=f_core,
                                          r_shell=r_shell, seed=7)
    n_core = int(f_core * n)
    shell_pos = pos[n_core:]
    shell_vel = vel[n_core:]

    radii = np.linalg.norm(shell_pos, axis=1)
    m_enc = float(n_core)
    expected_speed = np.sqrt(G * m_enc / r_shell)
    speeds = np.linalg.norm(shell_vel, axis=1)

    # mean speed within 2% of derived value
    assert speeds.mean() == pytest.approx(expected_speed, rel=0.02)

    # velocity perpendicular to radius vector (to 1e-3 in cosine)
    r_hat = shell_pos / radii[:, None]
    cosines = np.einsum("ij,ij->i", shell_vel, r_hat)
    assert np.max(np.abs(cosines)) < 1e-3


def test_disk_differential_rotation():
    """Disk points orbit azimuthally with speed v(r) = sqrt(G*M_enc/r)."""
    n = 512
    f_core = 0.5
    r_disk = 4.0
    pos, vel = seed_structures.disk(n, f_core=f_core, r_disk=r_disk, seed=11)
    n_core = int(f_core * n)
    disk_pos = pos[n_core:]
    disk_vel = vel[n_core:]

    r_xy = np.linalg.norm(disk_pos[:, :2], axis=1)
    m_enc = float(n_core)
    expected = np.sqrt(G * m_enc / r_xy)
    speeds = np.linalg.norm(disk_vel, axis=1)
    # allow 5% scatter from jitter and finite-N momentum removal
    assert np.allclose(speeds, expected, rtol=0.05)


def test_lattice_nearest_neighbor():
    """Interior lattice points have nearest neighbor at exactly R_BOND."""
    pos, vel = seed_structures.lattice(seed=3)
    nn = _nearest_neighbor_distances(pos)
    # all lattice sites have at least one neighbor at R_BOND
    np.testing.assert_allclose(nn, R_BOND, rtol=1e-5)
    # velocities are thermal, not zero
    sigma = 0.01 * np.sqrt(K_BOND * R_BOND)
    assert vel.std() == pytest.approx(sigma, rel=0.15)


def test_core_blob_spacing():
    """The central blob's typical nearest-neighbor distance is ~ R_BOND."""
    n = 256
    pos, vel = seed_structures.core_shell(n, f_core=0.5, seed=13)
    n_core = int(0.5 * n)
    nn = _nearest_neighbor_distances(pos[:n_core])
    median_nn = float(np.median(nn))
    assert 0.5 * R_BOND <= median_nn <= 2.0 * R_BOND, (
        f"core median NN distance {median_nn} not ~ R_BOND ({R_BOND})")


def test_lattice_bond_retention_initial():
    """Initial lattice has bond retention near unity."""
    pos, _ = seed_structures.lattice(seed=5)
    nn = _nearest_neighbor_distances(pos)
    retention = float(((nn >= R_WALL) & (nn <= R_C)).mean())
    assert retention > 0.95


@pytest.mark.parametrize("gen,kwargs", [
    (seed_structures.core_shell, {"n": 512}),
    (seed_structures.disk, {"n": 512}),
    (seed_structures.lattice, {}),
])
def test_net_momentum_removed(gen, kwargs):
    """Every generator removes net linear momentum."""
    _, vel = gen(**kwargs, seed=19)
    net = vel.mean(axis=0)
    np.testing.assert_allclose(net, 0.0, atol=1e-5)


def test_bone_determinism():
    """bone() is deterministic for a fixed seed."""
    a = seed_structures.bone(n=1024, grain_side=6, seed=3)
    b = seed_structures.bone(n=1024, grain_side=6, seed=3)
    for x, y in zip(a, b):
        np.testing.assert_array_equal(x, y)


def test_bone_geometry():
    """bone() builds a rod along x with pinned plates and bonded grains."""
    pos, vel, pin_mask, grain_ids = seed_structures.bone(n=1024, grain_side=6, seed=0)
    s = 6
    pts_per_grain = s ** 3
    n_grains = pos.shape[0] // pts_per_grain  # approximate

    # plates are pinned
    n_plate = s * s
    assert pin_mask[:n_plate].all()
    assert pin_mask[-n_plate:].all()
    assert not pin_mask[n_plate:-n_plate].any()

    # rod points carry grain ids, plates are -1
    assert (grain_ids[:n_plate] == -1).all()
    assert (grain_ids[-n_plate:] == -1).all()
    assert (grain_ids[n_plate:-n_plate] >= 0).all()

    # rod is elongated along x
    extents = pos.max(axis=0) - pos.min(axis=0)
    assert extents[0] > extents[1]
    assert extents[0] > extents[2]

    # no velocities
    np.testing.assert_allclose(vel, 0.0, atol=1e-6)


def test_bone_grains_bonded():
    """Adjacent grains in bone() have face points within R_BOND."""
    pos, _, _, grain_ids = seed_structures.bone(n=1024, grain_side=6, seed=0)
    n_grains = int(grain_ids.max()) + 1
    for g in range(n_grains - 1):
        mask_a = grain_ids == g
        mask_b = grain_ids == g + 1
        dists = np.linalg.norm(pos[mask_a][:, None] - pos[mask_b][None], axis=2)
        assert dists.min() <= R_BOND * 1.01, f"grain {g}-{g+1} not bonded"
