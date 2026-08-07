"""
Tests for LightEngine/seed_structures.py.

These verify the three canonical prints obey the derivations in docs/THE_PRINTER.md:
determinism, geometry, derived velocities, and momentum removal.
"""

import numpy as np
import pytest

from LightEngine import seed_structures, demo_seed
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


def test_tendon_default_unchanged():
    """preload_frac=0.0 (the default) reproduces the v1 derived s0."""
    pos_default, _, _, _, s0_default, _ = seed_structures.tendon(
        side=4, n_len=8, spacing=0.05, seed=11)
    pos_explicit, _, _, _, s0_explicit, _ = seed_structures.tendon(
        side=4, n_len=8, spacing=0.05, preload_frac=0.0, seed=11)
    np.testing.assert_array_equal(pos_default, pos_explicit)
    assert s0_default == pytest.approx(s0_explicit, rel=1e-12)
    assert s0_default == pytest.approx(
        (8 - 1) * 0.05 + 2.0 * seed_structures.TENDON_D_EQ, rel=1e-12)


def test_tendon_preload_geometry():
    """preload_frac=0.5 halves the seat gap and s0."""
    spacing = 0.05
    d_eq = seed_structures.TENDON_D_EQ
    pos, _, _, grain_ids, s0, rod_span = seed_structures.tendon(
        side=4, n_len=8, spacing=spacing, preload_frac=0.5, seed=0)

    assert rod_span == pytest.approx((8 - 1) * spacing, rel=1e-12)
    assert s0 == pytest.approx(rod_span + d_eq, rel=1e-12)

    rod = pos[grain_ids == 0]
    plates = pos[grain_ids == -1]
    left_plate = plates[plates[:, 0] < rod[:, 0].min()]
    right_plate = plates[plates[:, 0] > rod[:, 0].max()]

    left_gap = np.linalg.norm(
        left_plate[:, None, :] - rod[None, :, :], axis=2).min()
    right_gap = np.linalg.norm(
        right_plate[:, None, :] - rod[None, :, :], axis=2).min()
    assert abs(left_gap - d_eq / 2.0) < 0.01
    assert abs(right_gap - d_eq / 2.0) < 0.01


def test_tendon_foot_geometry():
    """foot_side=4 replaces terminal shaft layers with 4x4 feet (v4)."""
    spacing = 0.05
    d_eq = seed_structures.TENDON_D_EQ
    pos, vel, pin_mask, grain_ids, s0, rod_span = seed_structures.tendon(
        side=4, n_len=8, spacing=spacing, foot_side=4, seed=0)

    n_plate = 4 * 4
    n_shaft = 4 * 6          # 2x2x6 interior shaft
    n_foot = 2 * 4 * 4       # two 4x4 foot layers
    assert pos.shape[0] == n_shaft + n_foot + 2 * n_plate

    # plates pinned, rod free
    assert pin_mask[:n_plate].all()
    assert pin_mask[-n_plate:].all()
    assert not pin_mask[n_plate:n_plate + n_shaft + n_foot].any()

    # grain ids: plates -1, rod (shaft + feet) 0
    assert (grain_ids[:n_plate] == -1).all()
    assert (grain_ids[-n_plate:] == -1).all()
    assert (grain_ids[n_plate:n_plate + n_shaft + n_foot] == 0).all()

    # s0 and rod_span unchanged from the no-foot v1 case
    assert s0 == pytest.approx((8 - 1) * spacing + 2.0 * d_eq, rel=1e-12)
    assert rod_span == pytest.approx((8 - 1) * spacing, rel=1e-12)

    # cold print: zero velocity
    np.testing.assert_allclose(vel, 0.0, atol=1e-6)

    # print law: no two grains share a position
    rod = pos[grain_ids == 0]
    diff = rod[:, None, :] - rod[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    assert np.sqrt(r2.min()) > 1e-6

    plates = pos[grain_ids == -1]
    left_plate = plates[plates[:, 0] < rod[:, 0].min()]
    right_plate = plates[plates[:, 0] > rod[:, 0].max()]

    # plate separation matches s0
    left_x = float(left_plate[:, 0].mean())
    right_x = float(right_plate[:, 0].mean())
    assert abs(right_x - left_x - s0) < 0.01

    # end gaps measured from the foot outer face are approximately d_eq
    left_gap = np.linalg.norm(
        left_plate[:, None, :] - rod[None, :, :], axis=2).min()
    right_gap = np.linalg.norm(
        right_plate[:, None, :] - rod[None, :, :], axis=2).min()
    assert abs(left_gap - d_eq) < 0.01
    assert abs(right_gap - d_eq) < 0.01


def test_tendon_foot_default_unchanged():
    """foot_side=0 (the default) reproduces the v1/v2 builder exactly."""
    pos_default, _, _, _, s0_default, _ = seed_structures.tendon(
        side=4, n_len=8, spacing=0.05, seed=13)
    pos_explicit, _, _, _, s0_explicit, _ = seed_structures.tendon(
        side=4, n_len=8, spacing=0.05, foot_side=0, seed=13)
    np.testing.assert_array_equal(pos_default, pos_explicit)
    assert s0_default == pytest.approx(s0_explicit, rel=1e-12)


def test_joint_determinism():
    """joint() is deterministic for a fixed seed."""
    a = seed_structures.joint(seed=5)
    b = seed_structures.joint(seed=5)
    for x, y in zip(a, b):
        if isinstance(x, dict):
            assert x.keys() == y.keys()
            for k in x:
                if isinstance(x[k], np.ndarray):
                    np.testing.assert_array_equal(x[k], y[k])
                else:
                    assert x[k] == pytest.approx(y[k])
        else:
            np.testing.assert_array_equal(x, y)


def test_joint_counts():
    """joint() builds the expected point counts: plate + droplet + A + B."""
    pos, vel, pin_mask, grain_ids, derived = seed_structures.joint(seed=0)
    n_plate = 6 * 6
    n_drop = 4 ** 3
    n_A = 4 * 4 * 16
    n_B = 4 * 4 * 16
    assert pos.shape[0] == n_plate + n_drop + n_A + n_B
    assert vel.shape[0] == pos.shape[0]
    assert pin_mask.shape[0] == pos.shape[0]
    assert grain_ids.shape[0] == pos.shape[0]
    assert int((grain_ids == -1).sum()) == n_plate
    assert int((grain_ids == 0).sum()) == n_drop
    assert int((grain_ids == 1).sum()) == n_A
    assert int((grain_ids == 2).sum()) == n_B


def test_joint_pin_mask():
    """Only the ground plate is pinned."""
    pos, _, pin_mask, grain_ids, _ = seed_structures.joint(seed=0)
    n_plate = int((grain_ids == -1).sum())
    assert pin_mask[:n_plate].all()
    assert not pin_mask[n_plate:].any()


def test_joint_no_shared_positions():
    """No two grains share a position in the joint print."""
    pos, _, _, _, _ = seed_structures.joint(seed=0)
    pos64 = np.asarray(pos, dtype=np.float64)
    diff = pos64[:, None, :] - pos64[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    assert np.sqrt(r2.min()) > 1e-6


def test_joint_bone_orientations():
    """Bone A is vertical along z and bone B is horizontal along x."""
    pos, _, _, grain_ids, _ = seed_structures.joint(seed=0)
    A = pos[grain_ids == 1]
    B = pos[grain_ids == 2]
    A_extents = A.max(axis=0) - A.min(axis=0)
    B_extents = B.max(axis=0) - B.min(axis=0)
    # A is tallest in z.
    assert A_extents[2] > A_extents[0]
    assert A_extents[2] > A_extents[1]
    # B is longest in x.
    assert B_extents[0] > B_extents[1]
    assert B_extents[0] > B_extents[2]


def test_joint_gap():
    """B's joint-end face sits approximately d_eq above A's top face."""
    pos, _, _, grain_ids, derived = seed_structures.joint(seed=0)
    A = pos[grain_ids == 1]
    B = pos[grain_ids == 2]
    # Joint-end face: the 16 points (4×4 cross-section) with smallest x.
    joint_face = B[np.argsort(B[:, 0])[:16]]
    # A's top face: the 16 points with largest z.
    A_top = A[np.argsort(A[:, 2])[-16:]]
    gap = np.linalg.norm(
        joint_face[:, None, :] - A_top[None, :, :], axis=2).min()
    assert abs(gap - derived["d_eq"]) < 0.01


def test_joint_control_drops_droplet():
    """Removing the droplet drops exactly 64 grains."""
    pos, vel, pin_mask, grain_ids, _ = seed_structures.joint(seed=0)
    keep = grain_ids != 0
    pos_c = pos[keep]
    grain_ids_c = grain_ids[keep]
    assert pos_c.shape[0] == pos.shape[0] - 64
    assert int((grain_ids_c == 0).sum()) == 0


def test_joint_fixed_angle_metric():
    """
    The fixed-index θ metric must read a rigid rotation honestly, including
    past the 45° face-swap regime that broke the v1 x-sort metric.
    """
    pos, _, _, grain_ids, derived = seed_structures.joint(seed=0)
    B = pos[grain_ids == 2].copy()
    contact = derived["joint_contact_point"]
    joint_face, far_face = demo_seed._B_end_faces(B, contact)

    # Initial print angle from the fixed face centroids (slightly non-zero
    # because the face-centroid line is not perfectly horizontal).
    theta0 = demo_seed._B_angle(pos, grain_ids, joint_face, far_face)

    # Rigidly rotate B about the contact point in the x-z plane.
    angle_deg = 60.0
    angle = np.radians(angle_deg)
    c, s = np.cos(angle), np.sin(angle)
    B_rot = B.copy()
    rel = B - contact[None, :]
    B_rot[:, 0] = contact[0] + rel[:, 0] * c + rel[:, 2] * s
    B_rot[:, 2] = contact[2] - rel[:, 0] * s + rel[:, 2] * c

    pos_rot = pos.copy()
    pos_rot[grain_ids == 2] = B_rot
    theta = demo_seed._B_angle(pos_rot, grain_ids, joint_face, far_face)
    # The metric should report the actual rotation increment, not be offset
    # by the initial face-centroid tilt.
    assert np.degrees(theta - theta0) == pytest.approx(angle_deg, abs=1.0)


@pytest.mark.parametrize("mode", ["bump", "flat", "free", "tear"])
def test_sheet_determinism(mode):
    """sheet() is deterministic for a fixed seed and mode."""
    a = seed_structures.sheet(mode=mode, spacing=0.05, seed=11)
    b = seed_structures.sheet(mode=mode, spacing=0.05, seed=11)
    for x, y in zip(a, b):
        if isinstance(x, dict):
            assert x.keys() == y.keys()
            for k in x:
                if isinstance(x[k], np.ndarray):
                    np.testing.assert_array_equal(x[k], y[k])
                else:
                    assert x[k] == pytest.approx(y[k])
        else:
            np.testing.assert_array_equal(x, y)


@pytest.mark.parametrize("mode,n_expected", [
    ("flat", 292),
    ("bump", 356),
    ("free", 256),
    ("tear", 292),
])
def test_sheet_counts(mode, n_expected):
    """sheet() builds the expected total point counts per mode."""
    pos, vel, pin_mask, grain_ids, derived = seed_structures.sheet(
        mode=mode, spacing=0.05, seed=0)
    assert pos.shape[0] == n_expected
    assert vel.shape[0] == n_expected
    assert pin_mask.shape[0] == n_expected
    assert grain_ids.shape[0] == n_expected
    assert derived["n_sheet"] == 16 * 16
    if mode != "free":
        assert derived["n_plate"] == 6 * 6
        assert int((grain_ids == -1).sum()) == 6 * 6
    else:
        assert derived["n_plate"] == 0
        assert int((grain_ids == -1).sum()) == 0
    if mode == "bump":
        assert derived["n_block"] == 4 * 4 * 4
        assert int((grain_ids == 1).sum()) == 4 * 4 * 4
    else:
        assert derived["n_block"] == 0


def test_sheet_no_shared_positions():
    """No two grains share a position in any sheet print."""
    for mode in ["bump", "flat", "free", "tear"]:
        pos, _, _, _, _ = seed_structures.sheet(mode=mode, spacing=0.05, seed=0)
        pos64 = np.asarray(pos, dtype=np.float64)
        diff = pos64[:, None, :] - pos64[None, :, :]
        r2 = np.einsum("ijk,ijk->ij", diff, diff)
        np.fill_diagonal(r2, np.inf)
        assert np.sqrt(r2.min()) > 1e-6, f"mode={mode} print law violated"


def test_sheet_bump_height():
    """In bump mode the sheet center is d_eq + 0.05 above the block top."""
    pos, _, _, grain_ids, derived = seed_structures.sheet(
        mode="bump", spacing=0.05, seed=0)
    sheet = pos[grain_ids == 0]
    # Use the derived nominal block top; the sheet center already includes
    # the tiny print jitter, so allow a small tolerance.
    block_top_z = derived["block_top_z"]
    sheet_center_z = sheet[:, 2].mean()
    expected = derived["d_eq"] + 0.05
    assert abs((sheet_center_z - block_top_z) - expected) < 1e-4


def test_sheet_tear_pins():
    """tear mode pins exactly the two y-edge rows (32 grains)."""
    pos, _, pin_mask, grain_ids, derived = seed_structures.sheet(
        mode="tear", spacing=0.05, seed=0)
    sheet_idx = np.flatnonzero(grain_ids == 0)
    pinned = pin_mask[sheet_idx]
    assert pinned.sum() == 32
    # All pinned grains sit near one of the two extreme y values.
    y = pos[sheet_idx][pinned, 1]
    y_target = derived["sheet_width"] / 2.0
    assert np.all(np.abs(np.abs(y) - y_target) < 0.01)


def test_sheet_zero_velocity():
    """Cold sheet prints have zero velocity."""
    for mode in ["bump", "flat", "free", "tear"]:
        _, vel, _, _, _ = seed_structures.sheet(mode=mode, spacing=0.05, seed=0)
        np.testing.assert_allclose(vel, 0.0, atol=1e-6)


def test_sheet_derived_spacing():
    """spacing=None triggers the derived 2-D equilibrium spacing d_eq_2D."""
    d_eq_2d = seed_structures.derive_sheet_equilibrium_spacing(verbose=False)
    pos, _, _, _, derived = seed_structures.sheet(
        mode="flat", spacing=None, seed=0)
    assert derived["spacing"] == pytest.approx(d_eq_2d, abs=1e-4)
    assert derived["d_eq_2D"] == pytest.approx(d_eq_2d, abs=1e-4)
    # The derived spacing should be smaller than the 3-D droplet d_eq:
    # fewer in-plane neighbors mean weaker inward DRAW, so the 2-D patch must
    # sit closer to the wall where cushion repulsion is stronger.
    assert d_eq_2d < seed_structures.TENDON_D_EQ


def test_sheet_explicit_spacing_unchanged():
    """An explicit spacing overrides the derivation and is recorded verbatim."""
    pos, _, _, _, derived = seed_structures.sheet(
        mode="flat", spacing=0.05, seed=0)
    assert derived["spacing"] == pytest.approx(0.05, abs=1e-12)
    assert derived["d_eq_2D"] == pytest.approx(0.05, abs=1e-12)


def test_sheet_derived_counts():
    """Derived-spacing builds keep the same structural counts as v1."""
    for mode, n_expected in [
        ("flat", 292),
        ("bump", 356),
        ("free", 256),
        ("tear", 292),
    ]:
        pos, _, _, _, _ = seed_structures.sheet(mode=mode, spacing=None, seed=3)
        assert pos.shape[0] == n_expected


def test_sheet_framed_pins_border():
    """Framed sheet pins exactly the 60 border grains and omits the plate."""
    pos, _, pin_mask, grain_ids, derived = seed_structures.sheet(
        mode="flat", spacing=None, framed=True, seed=0)
    assert derived["framed"] is True
    assert derived["frame"] == 60
    assert derived["n_plate"] == 0
    assert (grain_ids == -1).sum() == 0
    assert pin_mask.sum() == 60
    # Every pinned grain is a sheet grain.
    assert (grain_ids[pin_mask] == 0).all()


def test_sheet_framed_spacing_derived():
    """Framed sheet with spacing=None uses the derived d_eq_2D."""
    d_eq_2d = seed_structures.derive_sheet_equilibrium_spacing(verbose=False)
    _, _, _, _, derived = seed_structures.sheet(
        mode="flat", spacing=None, framed=True, seed=0)
    assert derived["spacing"] == pytest.approx(d_eq_2d, abs=1e-4)


def test_sheet_framed_tear_grips():
    """Framed tear pins the full frame; two opposite y-rows are the grips."""
    pos, _, pin_mask, grain_ids, derived = seed_structures.sheet(
        mode="tear", spacing=None, framed=True, seed=0)
    sheet_idx = np.flatnonzero(grain_ids == 0)
    local_pinned = np.arange(sheet_idx.size)[pin_mask[sheet_idx]]
    assert local_pinned.size == 60

    # Local lattice indices: x changes slowest, y changes fastest.
    side = derived["sheet_side"]
    x_idx = local_pinned // side
    y_idx = local_pinned % side
    # Pinned grains are exactly the border grains (x=0 or x=15 or y=0 or y=15).
    on_border = ((x_idx == 0) | (x_idx == side - 1) |
                 (y_idx == 0) | (y_idx == side - 1))
    assert on_border.all()

    # The two y-edge rows (top and bottom) are fully pinned.
    top = sheet_idx[(np.arange(side * side) % side) == 0]
    bottom = sheet_idx[(np.arange(side * side) % side) == (side - 1)]
    assert pin_mask[top].all()
    assert pin_mask[bottom].all()


def test_skin_determinism():
    """skin() is deterministic for a fixed seed."""
    a = seed_structures.skin(seed=5)
    b = seed_structures.skin(seed=5)
    for x, y in zip(a, b):
        if isinstance(x, dict):
            assert x.keys() == y.keys()
            for k in x:
                if isinstance(x[k], np.ndarray):
                    np.testing.assert_array_equal(x[k], y[k])
                else:
                    assert x[k] == pytest.approx(y[k])
        else:
            np.testing.assert_array_equal(x, y)


def test_skin_counts():
    """skin() builds a 4³ muscle droplet + two 4×4 plates + a 16×16 mat."""
    pos, vel, pin_mask, grain_ids, s0, R_droplet, derived = seed_structures.skin(
        spacing=0.05, seed=0)
    n_plate = 2 * 4 * 4
    n_drop = 4 ** 3
    n_mat = 16 * 16
    assert pos.shape[0] == n_plate + n_drop + n_mat
    assert vel.shape[0] == pos.shape[0]
    assert pin_mask.shape[0] == pos.shape[0]
    assert grain_ids.shape[0] == pos.shape[0]
    assert int((grain_ids == -1).sum()) == n_plate
    assert int((grain_ids == 0).sum()) == n_drop
    assert int((grain_ids == 1).sum()) == n_mat
    assert derived["n_plate"] == n_plate
    assert derived["n_droplet"] == n_drop
    assert derived["n_mat"] == n_mat


def test_skin_only_plates_pinned():
    """Only the muscle anchor plates are pinned; droplet and mat are free."""
    pos, _, pin_mask, grain_ids, _, _, _ = seed_structures.skin(seed=0)
    plate_mask = grain_ids == -1
    assert pin_mask[plate_mask].all()
    assert not pin_mask[~plate_mask].any()


def test_skin_mat_height():
    """The mat is printed one 2-D lattice step above the droplet top face."""
    pos, _, _, grain_ids, _, _, derived = seed_structures.skin(seed=0)
    droplet_top = pos[grain_ids == 0, 2].max()
    mat = pos[grain_ids == 1]
    mat_center_z = mat[:, 2].mean()
    expected = droplet_top + derived["d_eq_2D"]
    assert abs(mat_center_z - expected) < 1e-5


def test_skin_no_shared_positions():
    """No two grains share a position in the skin print."""
    pos, _, _, _, _, _, _ = seed_structures.skin(seed=0)
    pos64 = np.asarray(pos, dtype=np.float64)
    diff = pos64[:, None, :] - pos64[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    assert np.sqrt(r2.min()) > 1e-6


def test_skin_surface_grains_exist():
    """The droplet has surface grains and a non-empty conform band."""
    _, _, _, _, _, _, derived = seed_structures.skin(seed=0)
    assert derived["surface_grains"].size > 0
    lo, hi = derived["conform_band"]
    assert lo < hi


def test_bladder_determinism():
    """bladder() is deterministic for a fixed seed."""
    a = seed_structures.bladder(seed=7)
    b = seed_structures.bladder(seed=7)
    for x, y in zip(a, b):
        if isinstance(x, dict):
            assert x.keys() == y.keys()
            for k in x:
                if isinstance(x[k], np.ndarray):
                    np.testing.assert_array_equal(x[k], y[k])
                else:
                    assert x[k] == pytest.approx(y[k])
        else:
            np.testing.assert_array_equal(x, y)


def test_bladder_counts():
    """bladder() builds two 4x4 plates, a derived shell, and 4^3 contents."""
    pos, _, pin_mask, grain_ids, s0, derived = seed_structures.bladder(seed=0)
    n_plate = 2 * 4 * 4
    n_content = 4 ** 3
    assert pos.shape[0] == n_plate + derived["n_shell"] + n_content
    assert int((grain_ids == -1).sum()) == n_plate
    assert int((grain_ids == 2).sum()) == n_content
    assert int((grain_ids == 1).sum()) == derived["n_shell"]
    # shell count is derived from surface area / d_eq^2
    expected_shell = int(round(4.0 * np.pi * derived["r_b"] ** 2
                               / derived["d_eq"] ** 2))
    assert 0.95 * expected_shell <= derived["n_shell"] <= 1.05 * expected_shell


def test_bladder_only_plates_pinned():
    """Only the squeeze plates are pinned; shell and contents are free."""
    _, _, pin_mask, grain_ids, _, _ = seed_structures.bladder(seed=0)
    plate_mask = grain_ids == -1
    assert pin_mask[plate_mask].all()
    assert not pin_mask[~plate_mask].any()


def test_bladder_neck_hole():
    """No shell grain sits inside the derived neck exclusion zone."""
    pos, _, _, grain_ids, _, derived = seed_structures.bladder(seed=0)
    shell = pos[grain_ids == 1]
    dist = np.linalg.norm(shell - derived["neck_center"], axis=1)
    assert dist.min() > 0.8 * derived["d_eq"]


def test_bladder_no_shared_positions():
    """No two grains share a position in the bladder print."""
    pos, _, _, _, _, _ = seed_structures.bladder(seed=0)
    pos64 = np.asarray(pos, dtype=np.float64)
    diff = pos64[:, None, :] - pos64[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    assert np.sqrt(r2.min()) > 1e-6


def test_bladder_plate_separation():
    """Plate separation matches the derived s0."""
    pos, _, _, grain_ids, s0, _ = seed_structures.bladder(seed=0)
    plates = pos[grain_ids == -1]
    left_x = float(plates[plates[:, 0] < plates[:, 0].mean(), 0].mean())
    right_x = float(plates[plates[:, 0] > plates[:, 0].mean(), 0].mean())
    assert abs((right_x - left_x) - s0) < 0.01


def test_bladder_F_hold_positive():
    """The derived hold force is positive."""
    _, _, _, _, _, derived = seed_structures.bladder(seed=0)
    assert derived["F_hold"] > 0.0


def test_bladder_narrow_mode_unchanged():
    """neck='narrow' reproduces the default builder exactly."""
    pos_default, _, _, _, _, derived_default = seed_structures.bladder(seed=13)
    pos_narrow, _, _, _, _, derived_narrow = seed_structures.bladder(
        seed=13, neck="narrow")
    np.testing.assert_array_equal(pos_default, pos_narrow)
    assert derived_default["neck"] == "narrow"
    assert derived_narrow["neck"] == "narrow"
    assert derived_default["neck_diameter"] == pytest.approx(
        derived_narrow["neck_diameter"], rel=1e-12)
    np.testing.assert_allclose(
        derived_default["neck_axis"], derived_narrow["neck_axis"], atol=1e-12)


def test_bladder_antijam_neck_axis():
    """antijam neck is centered on the +x sphere point with axis +x."""
    pos, _, _, _, _, derived = seed_structures.bladder(
        seed=0, fill="fill", neck="antijam")
    assert derived["neck"] == "antijam"
    expected_center = np.array([
        derived["center_x"] + derived["r_b"], 0.0, 0.0])
    np.testing.assert_allclose(
        derived["neck_center"], expected_center, atol=1e-5)
    np.testing.assert_allclose(
        derived["neck_axis"], np.array([1.0, 0.0, 0.0]), atol=1e-12)


def test_bladder_antijam_neck_hole():
    """antijam neck is a 4-spacing hole: no shell grain within 2 spacings."""
    pos, _, _, grain_ids, _, derived = seed_structures.bladder(
        seed=0, fill="fill", neck="antijam")
    shell = pos[grain_ids == 1]
    dist = np.linalg.norm(shell - derived["neck_center"], axis=1)
    # The hole radius is 2 lattice spacings; after print jitter allow a small
    # margin and require no shell grain inside the nominal hole.
    assert dist.min() > 0.09, (
        f"shell grain inside anti-jam neck at dist {dist.min():.4f}")
    assert derived["neck_diameter"] == pytest.approx(4.0 * 0.05, rel=1e-12)


def test_lever_determinism():
    """lever() is deterministic for a fixed seed and control flag."""
    a = seed_structures.lever(control=False, seed=7)
    b = seed_structures.lever(control=False, seed=7)
    for x, y in zip(a, b):
        if isinstance(x, dict):
            assert x.keys() == y.keys()
            for k in x:
                if isinstance(x[k], np.ndarray):
                    np.testing.assert_array_equal(x[k], y[k])
                else:
                    assert x[k] == pytest.approx(y[k])
        else:
            np.testing.assert_array_equal(x, y)


def test_lever_counts():
    """lever() builds the expected point counts."""
    pos, _, pin_mask, grain_ids, derived = seed_structures.lever(
        control=False, seed=0)
    n_plate = 6 * 6
    # v6 fulcrum is the 4x4x4 block plus two 4x1x3 cheeks.
    n_fulcrum = 4 ** 3 + 2 * 4 * 3
    n_load = 4 ** 3
    n_drop = 4 ** 3
    n_lever = derived["n_lever"]
    lever_len = derived["lever_len"]
    assert lever_len == 13
    assert n_lever == lever_len * 12  # 12 grains per tube ring
    assert pos.shape[0] == n_plate + n_drop + n_fulcrum + n_lever + n_load
    assert int((grain_ids == -1).sum()) == n_plate
    assert int((grain_ids == 0).sum()) == n_drop
    assert int((grain_ids == 1).sum()) == n_fulcrum
    assert int((grain_ids == 2).sum()) == n_lever
    assert int((grain_ids == 3).sum()) == n_load
    assert derived["n_plate"] == n_plate
    assert derived["n_fulcrum"] == n_fulcrum
    assert derived["n_cheek"] == 2 * 4 * 3
    assert derived["n_load"] == n_load
    assert derived["alpha_method"] == "bisection"


def test_lever_pinned_bodies():
    """The ground plate and the fulcrum block are pinned; nothing else is."""
    pos, _, pin_mask, grain_ids, _ = seed_structures.lever(control=False, seed=0)
    pinned_mask = (grain_ids == -1) | (grain_ids == 1)
    assert pin_mask[pinned_mask].all()
    assert not pin_mask[~pinned_mask].any()


def test_lever_no_shared_positions():
    """No two grains share a position in the lever print."""
    pos, _, _, _, _ = seed_structures.lever(control=False, seed=0)
    pos64 = np.asarray(pos, dtype=np.float64)
    diff = pos64[:, None, :] - pos64[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    assert np.sqrt(r2.min()) > 1e-6


def test_lever_main_ratio():
    """Main lever print derives kernel R_true = 2.0 +/- 0.1."""
    _, _, _, _, derived = seed_structures.lever(control=False, seed=0)
    assert 1.9 <= derived["R_true"] <= 2.1


def test_lever_main_contact_margin():
    """Main fulcrum contact clears the lever end by at least 2 lattice steps."""
    _, _, _, _, derived = seed_structures.lever(control=False, seed=0)
    assert derived["route"] == "standard"
    assert derived["margin_to_load_end"] >= 2.0 * derived["spacing"]


def test_lever_control_ratio():
    """Control lever print derives kernel R_true in [0.5, 1.05]."""
    _, _, _, _, derived = seed_structures.lever(control=True, seed=0)
    assert 0.5 <= derived["R_true"] <= 1.05


def test_lever_control_weaker_arm():
    """Control run moves the fulcrum toward the muscle end."""
    _, _, _, _, derived_main = seed_structures.lever(control=False, seed=0)
    _, _, _, _, derived_ctrl = seed_structures.lever(control=True, seed=0)
    assert derived_ctrl["a_m"] < derived_main["a_m"]
    assert derived_ctrl["a_l"] > derived_main["a_l"]


def test_lever_cushion_contacts():
    """Initial lever-fulcrum and load-lever gaps are approximately d_eq."""
    pos, _, _, grain_ids, derived = seed_structures.lever(control=False, seed=0)
    fulcrum = pos[grain_ids == 1]
    lever = pos[grain_ids == 2]
    load = pos[grain_ids == 3]
    fulcrum_top = fulcrum[derived["fulcrum_top_face"]]
    lever_contact = lever[derived["lever_contact_local"]]
    d_eq = derived["d_eq"]
    d = derived["spacing"]

    # Vertical cushion gap: consider only pairs whose horizontal offset is
    # small (within two lattice steps), because a thin lever's diagonal
    # corner-to-corner distance is not the contact gap.
    def _vertical_gap(src: np.ndarray, dst: np.ndarray) -> float:
        delta = src[:, None, :] - dst[None, :, :]
        r_xy = np.linalg.norm(delta[:, :, :2], axis=2)
        dz = np.abs(delta[:, :, 2])
        close = r_xy <= 2.0 * d
        if not close.any():
            return float(np.sqrt((delta * delta).sum(axis=2).min()))
        return float(dz[close].min())

    fulcrum_gap = _vertical_gap(fulcrum_top, lever_contact)
    load_lever_gap = _vertical_gap(load, lever)
    assert abs(fulcrum_gap - d_eq) < 0.01
    assert abs(load_lever_gap - d_eq) < 0.01


def test_bladder_gap_mode_unchanged():
    """fill='gap' reproduces the v1 content count exactly."""
    pos, _, _, grain_ids, _, derived = seed_structures.bladder(
        seed=0, fill="gap")
    assert derived["fill"] == "gap"
    assert derived["n_content"] == 4 ** 3
    assert int((grain_ids == 2).sum()) == 4 ** 3


def test_bladder_fill_mode_count():
    """fill='fill' derives a content count from the interior sphere."""
    pos, _, _, grain_ids, _, derived = seed_structures.bladder(
        seed=0, fill="fill")
    assert derived["fill"] == "fill"
    assert derived["n_content"] != 4 ** 3
    assert int((grain_ids == 2).sum()) == derived["n_content"]
    # v2 expected ~113-123 grains for r_in = 0.1516 at spacing 0.05
    assert 90 <= derived["n_content"] <= 140


def test_bladder_fill_mode_cushion_contact():
    """fill='fill' places contents in cushion contact with the shell wall."""
    pos, _, _, grain_ids, _, derived = seed_structures.bladder(
        seed=0, fill="fill")
    shell = pos[grain_ids == 1]
    content = pos[grain_ids == 2]
    d = np.linalg.norm(
        content[:, None, :] - shell[None, :, :], axis=2)
    min_dist = float(d.min())
    d_eq = derived["d_eq"]
    assert 0.8 * d_eq <= min_dist <= 1.5 * d_eq, (
        f"min content-shell distance {min_dist} not in "
        f"[{0.8*d_eq:.4f}, {1.5*d_eq:.4f}]")


def test_leg_determinism():
    """leg() is deterministic for a fixed seed and control flag."""
    a = seed_structures.leg(control=False, seed=7)
    b = seed_structures.leg(control=False, seed=7)
    for x, y in zip(a, b):
        if isinstance(x, dict):
            assert x.keys() == y.keys()
            for k in x:
                if isinstance(x[k], np.ndarray):
                    np.testing.assert_array_equal(x[k], y[k])
                elif k == "arc_trace":
                    # dict of arrays: compare elementwise
                    assert y[k].keys() == x[k].keys()
                    for kk in x[k]:
                        np.testing.assert_array_equal(x[k][kk], y[k][kk])
                else:
                    assert x[k] == pytest.approx(y[k])
        else:
            np.testing.assert_array_equal(x, y)


def test_leg_counts():
    """leg() builds the expected point counts."""
    pos, _, pin_mask, grain_ids, derived = seed_structures.leg(
        control=False, seed=0)
    # 18x6 flat plate minus 6x6 hole = 72; well box 6x6x5 with 4x4x4 cavity
    # above a solid bottom layer = 36 + 4*(36-16) = 116; total plate = 188.
    n_plate = 188
    n_fulcrum = 4 ** 3 + 2 * 4 * 3
    n_load = 4 ** 3
    n_drop = 4 ** 3
    n_lever = derived["n_lever"]
    n_rod = derived["n_rod"]
    n_rod_layers = derived["n_rod_layers"]
    lever_len = derived["lever_len"]
    assert lever_len == 13
    assert n_lever == lever_len * 12
    assert n_rod == 4 * n_rod_layers
    assert pos.shape[0] == n_plate + n_drop + n_fulcrum + n_lever + n_load + n_rod
    assert int((grain_ids == -1).sum()) == n_plate
    assert int((grain_ids == 0).sum()) == n_drop
    assert int((grain_ids == 1).sum()) == n_fulcrum
    assert int((grain_ids == 2).sum()) == n_lever
    assert int((grain_ids == 3).sum()) == n_load
    assert int((grain_ids == 4).sum()) == n_rod
    assert derived["n_plate"] == n_plate
    assert derived["n_fulcrum"] == n_fulcrum
    assert derived["n_cheek"] == 2 * 4 * 3
    assert derived["n_load"] == n_load
    assert derived["n_rod"] == n_rod


def test_leg_pinned_bodies():
    """The ground plate, droplet and fulcrum block are pinned; rod/lever/load free."""
    pos, _, pin_mask, grain_ids, _ = seed_structures.leg(control=False, seed=0)
    pinned_mask = (grain_ids == -1) | (grain_ids == 0) | (grain_ids == 1)
    assert pin_mask[pinned_mask].all()
    assert not pin_mask[~pinned_mask].any()


def test_leg_no_shared_positions():
    """No two grains share a position in the leg print."""
    pos, _, _, _, _ = seed_structures.leg(control=False, seed=0)
    pos64 = np.asarray(pos, dtype=np.float64)
    diff = pos64[:, None, :] - pos64[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    assert np.sqrt(r2.min()) > 1e-6


def test_leg_well_depth():
    """The well floor depth is derived and the droplet sits on it."""
    pos, _, _, grain_ids, derived = seed_structures.leg(control=False, seed=0)
    well_floor_z = derived["well_floor_z"]
    plate = pos[grain_ids == -1]
    min_plate_z = float(plate[:, 2].min())
    # Print jitter lets the lowest well-floor grain sit slightly below nominal.
    assert abs(min_plate_z - well_floor_z) < 0.005
    droplet = pos[grain_ids == 0]
    assert droplet[:, 2].min() > well_floor_z - 1e-3


def test_leg_droplet_anchored():
    """The droplet grains are pinned to the well floor."""
    pos, _, pin_mask, grain_ids, derived = seed_structures.leg(
        control=False, seed=0)
    drop_idx = np.flatnonzero(grain_ids == 0)
    assert pin_mask[drop_idx].all()


def test_leg_main_ratio():
    """Main leg print derives cold R_true >= 1.0 (arc gate taut price)."""
    _, _, _, _, derived = seed_structures.leg(control=False, seed=0)
    assert derived["R_true"] >= 1.0
    trace = derived["arc_trace"]
    assert np.min(trace["R_taut"]) >= 1.0


def test_leg_main_contact_margin():
    """Main fulcrum contact clears the lever load end by at least 0.10 lu."""
    _, _, _, _, derived = seed_structures.leg(control=False, seed=0)
    assert derived["margin_to_load_end"] >= 0.10


def test_leg_control_ratio():
    """Control leg print derives cold R_true in [0.5, 1.0] (arc gate slack price)."""
    _, _, _, _, derived = seed_structures.leg(control=True, seed=0)
    assert 0.5 <= derived["R_true"] <= 1.0
    trace = derived["arc_trace"]
    assert 0.5 <= trace["R_slack"][0] <= 1.0
    assert np.max(trace["R_slack"]) <= 1.0


def test_leg_control_weaker_arm():
    """Control run moves the fulcrum toward the muscle end."""
    _, _, _, _, derived_main = seed_structures.leg(control=False, seed=0)
    _, _, _, _, derived_ctrl = seed_structures.leg(control=True, seed=0)
    assert derived_ctrl["a_m"] < derived_main["a_m"]
    assert derived_ctrl["a_l"] > derived_main["a_l"]


def test_leg_rod_spans_well():
    """The tendon rod spans from the arm tip underside to the droplet apex."""
    pos, _, _, grain_ids, derived = seed_structures.leg(control=False, seed=0)
    lever = pos[grain_ids == 2]
    rod = pos[grain_ids == 4]
    droplet = pos[grain_ids == 0]
    muscle_tip_x = derived["muscle_tip_x"]
    d_eq = derived["d_eq"]
    # Rod is centered on the muscle tip in x/y.
    assert abs(rod[:, 0].mean() - muscle_tip_x) < 0.05
    assert abs(rod[:, 1].mean()) < 0.05
    # Rod top sits d_eq below the lever underside.
    lever_bottom_z = lever[:, 2].min()
    rod_top_z = rod[:, 2].max()
    assert rod_top_z < lever_bottom_z
    assert abs(lever_bottom_z - rod_top_z - d_eq) < 0.01
    # Rod bottom sits at or above droplet_apex + d_eq.
    rod_bottom_z = rod[:, 2].min()
    droplet_apex = float(droplet[:, 2].max())
    assert rod_bottom_z >= droplet_apex + d_eq - 1e-3


def test_leg_arc_trace():
    """The arc gate returns a theta_stop and sampled R_true traces."""
    _, _, _, _, derived = seed_structures.leg(control=False, seed=0)
    trace = derived["arc_trace"]
    assert "theta_stop" in trace
    assert "thetas" in trace
    assert "R_taut" in trace
    assert "R_slack" in trace
    assert trace["theta_stop"] > 0.0
    assert trace["thetas"][0] == 0.0
    assert trace["thetas"][-1] == pytest.approx(trace["theta_stop"])
    assert len(trace["thetas"]) == len(trace["R_taut"]) == len(trace["R_slack"])
