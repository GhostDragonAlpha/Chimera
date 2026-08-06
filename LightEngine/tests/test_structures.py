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


def test_bone2_determinism():
    """bone2() is deterministic for a fixed seed."""
    a = seed_structures.bone2(seed=5)
    b = seed_structures.bone2(seed=5)
    for x, y in zip(a, b):
        np.testing.assert_array_equal(x, y)


def test_bone2_geometry():
    """bone2() builds a cushion-spaced column with pinned plates."""
    pos, vel, pin_mask, grain_ids = seed_structures.bone2(
        width=4, height=4, length=16, spacing=0.05, seed=0)
    n_plate = 4 * 4
    n_col = 4 * 4 * 16
    assert pos.shape[0] == n_col + 2 * n_plate

    # plates pinned, column free
    assert pin_mask[:n_plate].all()
    assert pin_mask[-n_plate:].all()
    assert not pin_mask[n_plate:n_plate + n_col].any()

    # grain ids: plates -1, column 0
    assert (grain_ids[:n_plate] == -1).all()
    assert (grain_ids[-n_plate:] == -1).all()
    assert (grain_ids[n_plate:n_plate + n_col] == 0).all()

    # column is elongated along x
    extents = pos.max(axis=0) - pos.min(axis=0)
    assert extents[0] > extents[1]
    assert extents[0] > extents[2]

    # cold print: zero velocity
    np.testing.assert_allclose(vel, 0.0, atol=1e-6)


def test_bone2_cushion_gap():
    """bone2() plates sit one cushion spacing from the terminal column layers."""
    spacing = 0.05
    pos, _, _, grain_ids = seed_structures.bone2(
        width=4, height=4, length=16, spacing=spacing, seed=0)
    col = pos[grain_ids >= 0]
    plates = pos[grain_ids == -1]
    left_plate = plates[plates[:, 0] < col[:, 0].min()]
    right_plate = plates[plates[:, 0] > col[:, 0].max()]

    left_gap = np.linalg.norm(
        left_plate[:, None, :] - col[None, :, :], axis=2).min()
    right_gap = np.linalg.norm(
        right_plate[:, None, :] - col[None, :, :], axis=2).min()

    # gap is approximately one spacing, within the tiny jitter tolerance
    assert abs(left_gap - spacing) < 0.01
    assert abs(right_gap - spacing) < 0.01


def test_muscle_determinism():
    """muscle() is deterministic for a fixed seed."""
    a = seed_structures.muscle(side=4, seed=7)
    b = seed_structures.muscle(side=4, seed=7)
    for x, y in zip(a, b):
        np.testing.assert_array_equal(x, y)


def test_muscle_geometry():
    """muscle() builds a 4³ droplet on a pinned left plate with a right plate at s₀."""
    pos, vel, pin_mask, grain_ids, s0, R_droplet = seed_structures.muscle(
        side=4, spacing=0.05, seed=0)
    n_plate = 4 * 4
    n_drop = 4 ** 3
    assert pos.shape[0] == n_drop + 2 * n_plate

    # both plates pinned, droplet free
    assert pin_mask[:n_plate].all()
    assert pin_mask[-n_plate:].all()
    assert not pin_mask[n_plate:n_plate + n_drop].any()

    # grain ids: plates -1, droplet 0
    assert (grain_ids[:n_plate] == -1).all()
    assert (grain_ids[-n_plate:] == -1).all()
    assert (grain_ids[n_plate:n_plate + n_drop] == 0).all()

    # cold print: zero velocity
    np.testing.assert_allclose(vel, 0.0, atol=1e-6)

    # derived numbers are positive and consistent
    assert R_droplet > 0.0
    assert s0 == pytest.approx(2.0 * R_droplet, rel=1e-12)


def test_muscle_seated_on_left_plate():
    """The droplet's left face sits at one cushion spacing from the left plate."""
    spacing = 0.05
    pos, _, _, grain_ids, s0, _ = seed_structures.muscle(
        side=4, spacing=spacing, seed=0)
    drop = pos[grain_ids == 0]
    left_plate = pos[grain_ids == -1]
    left_plate = left_plate[left_plate[:, 0] < drop[:, 0].min()]

    gap = np.linalg.norm(
        left_plate[:, None, :] - drop[None, :, :], axis=2).min()
    assert abs(gap - spacing) < 0.01

    # right plate is farther than the droplet right face
    right_plate = pos[grain_ids == -1]
    right_plate = right_plate[right_plate[:, 0] > drop[:, 0].max()]
    right_gap = np.linalg.norm(
        right_plate[:, None, :] - drop[None, :, :], axis=2).min()
    assert right_gap > 0.0
    # plate separation matches s0
    left_x = float(pos[:len(left_plate), 0].mean())
    right_x = float(pos[-len(right_plate):, 0].mean())
    assert abs(right_x - left_x - s0) < 0.01


def test_tendon_determinism():
    """tendon() is deterministic for a fixed seed."""
    a = seed_structures.tendon(side=4, n_len=8, seed=7)
    b = seed_structures.tendon(side=4, n_len=8, seed=7)
    for x, y in zip(a, b):
        np.testing.assert_array_equal(x, y)


def test_tendon_geometry():
    """tendon() builds a 2x2x8 rod between two pinned 4x4 plates."""
    pos, vel, pin_mask, grain_ids, s0, rod_span = seed_structures.tendon(
        side=4, n_len=8, spacing=0.05, seed=0)
    n_plate = 4 * 4
    n_rod = 4 * 8
    assert pos.shape[0] == n_rod + 2 * n_plate

    # both plates pinned, rod free
    assert pin_mask[:n_plate].all()
    assert pin_mask[-n_plate:].all()
    assert not pin_mask[n_plate:n_plate + n_rod].any()

    # grain ids: plates -1, rod 0
    assert (grain_ids[:n_plate] == -1).all()
    assert (grain_ids[-n_plate:] == -1).all()
    assert (grain_ids[n_plate:n_plate + n_rod] == 0).all()

    # cold print: zero velocity
    np.testing.assert_allclose(vel, 0.0, atol=1e-6)

    # derived numbers are positive and consistent
    assert rod_span == pytest.approx((8 - 1) * 0.05, rel=1e-12)
    assert s0 == pytest.approx(rod_span + 2.0 * seed_structures.TENDON_D_EQ,
                               rel=1e-12)


def test_tendon_centered_and_seated():
    """The rod is centered on the x-axis and seated d_eq from each plate."""
    spacing = 0.05
    d_eq = seed_structures.TENDON_D_EQ
    pos, _, _, grain_ids, s0, _ = seed_structures.tendon(
        side=4, n_len=8, spacing=spacing, seed=0)
    rod = pos[grain_ids == 0]
    plates = pos[grain_ids == -1]

    # rod COM lies on the x-axis
    com = rod.mean(axis=0)
    assert abs(com[1]) < 0.01
    assert abs(com[2]) < 0.01

    # plate separation matches s0
    left_plate = plates[plates[:, 0] < rod[:, 0].min()]
    right_plate = plates[plates[:, 0] > rod[:, 0].max()]
    left_x = float(left_plate[:, 0].mean())
    right_x = float(right_plate[:, 0].mean())
    assert abs(right_x - left_x - s0) < 0.01

    # end gaps are approximately d_eq
    left_gap = np.linalg.norm(
        left_plate[:, None, :] - rod[None, :, :], axis=2).min()
    right_gap = np.linalg.norm(
        right_plate[:, None, :] - rod[None, :, :], axis=2).min()
    assert abs(left_gap - d_eq) < 0.01
    assert abs(right_gap - d_eq) < 0.01
