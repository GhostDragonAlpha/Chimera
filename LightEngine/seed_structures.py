"""
THE PRINTER — authored seed structures for the LightEngine kernel.

Each generator returns ``(positions, velocities)`` as float32 (N,3) arrays.
Velocities are derived from the same force laws that judge the run; geometry is
authored, constants are not.
"""

from __future__ import annotations

import math
import numpy as np

from LightEngine.constants import G, R_WALL, R_BOND, R_C, K_BOND


def _remove_net_momentum(vel: np.ndarray) -> np.ndarray:
    """Subtract mean velocity so the whole system has zero net momentum."""
    vel = vel.copy()
    vel -= vel.mean(axis=0)
    return vel


def _uniform_in_ball(n: int, radius: float, rng: np.random.Generator) -> np.ndarray:
    """Return ``n`` points uniformly distributed in a ball of ``radius``."""
    u = rng.random(n)
    r = radius * u ** (1.0 / 3.0)
    cos_theta = rng.uniform(-1.0, 1.0, n)
    theta = np.arccos(cos_theta)
    phi = rng.uniform(0.0, 2.0 * math.pi, n)
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return np.stack([x, y, z], axis=1)


def _ball_radius_for_bond_spacing(n: int, spacing: float) -> float:
    """
    Radius of a ball containing ``n`` points at volume per point = spacing^3.
    This makes the typical nearest-neighbor distance ~ ``spacing``.
    """
    if n <= 0:
        return 0.0
    volume = n * spacing ** 3
    return ((3.0 * volume) / (4.0 * math.pi)) ** (1.0 / 3.0)


def _azimuthal_unit_vector(pos: np.ndarray) -> np.ndarray:
    """Unit vector e_phi = (-y, x, 0) / sqrt(x^2+y^2); tangent to z-rotation."""
    xy = np.linalg.norm(pos[:, :2], axis=1, keepdims=True)
    xy = np.where(xy < 1e-12, 1.0, xy)  # guard the pole; value is irrelevant there
    e_phi = np.stack([-pos[:, 1], pos[:, 0], np.zeros(pos.shape[0])], axis=1)
    return e_phi / xy


def _jitter_in_plane(vel: np.ndarray, e_u: np.ndarray, e_v: np.ndarray,
                     jitter_frac: float, rng: np.random.Generator) -> np.ndarray:
    """
    Add ``jitter_frac * |vel|`` of random velocity in the (e_u, e_v) plane.
    Both basis vectors must be unit and orthogonal to the position vector so the
    velocity stays perpendicular to the radius vector.
    """
    speed = np.linalg.norm(vel, axis=1, keepdims=True)
    a = rng.normal(0.0, 1.0, size=(vel.shape[0], 1))
    b = rng.normal(0.0, 1.0, size=(vel.shape[0], 1))
    return vel + jitter_frac * speed * (a * e_u + b * e_v)


def core_shell(n: int = 4096,
               f_core: float = 0.5,
               r_shell: float = 4.0,
               seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """
    Core+shell "solar system" print.

    Returns ``(positions, velocities)`` where core points occupy indices
    ``[0, n_core)`` and shell points occupy ``[n_core, n)``.

    Derivation:
      - ``n_core = int(f_core * n)`` points fill a ball whose radius is set by
        volume per point ``~ R_BOND^3``.
      - The remaining ``n - n_core`` points orbit on a thin shell of radius
        ``r_shell`` (thickness ``~ R_BOND``) with orbital speed
        ``v = sqrt(G * M_enc / r_shell)`` and ``M_enc = n_core``.
      - Velocity is azimuthal around the z-axis (common spin); 1% tangential
        jitter breaks perfect symmetry.  Net momentum is removed.
    """
    rng = np.random.default_rng(seed)
    n_core = max(1, min(int(f_core * n), n - 1))
    n_shell = n - n_core

    pos = np.empty((n, 3), dtype=np.float64)

    # core blob
    r_core = _ball_radius_for_bond_spacing(n_core, R_BOND)
    pos[:n_core] = _uniform_in_ball(n_core, r_core, rng)

    # shell: nearly uniform Fibonacci sphere plus thin radial jitter
    indices = np.arange(n_shell, dtype=np.float64)
    y = 1.0 - 2.0 * indices / max(n_shell - 1, 1)
    radius_at_y = np.sqrt(np.maximum(1.0 - y * y, 0.0))
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    theta = golden_angle * indices
    x = radius_at_y * np.cos(theta)
    z = radius_at_y * np.sin(theta)
    directions = np.stack([x, y, z], axis=1)
    dr = rng.normal(0.0, R_BOND / 3.0, size=n_shell)
    radii = r_shell + dr
    radii = np.maximum(radii, R_BOND)  # keep shell outside the core region
    pos[n_core:] = directions * radii[:, None]

    # velocities: core at rest, shell in circular orbit around z
    vel = np.zeros((n, 3), dtype=np.float64)
    m_enc = float(n_core)
    v_orb = math.sqrt(G * m_enc / r_shell)
    shell_pos = pos[n_core:]
    e_phi = _azimuthal_unit_vector(shell_pos)
    # second tangent vector on the sphere: e_theta = normalize(r_hat x e_phi)
    r_hat = shell_pos / np.linalg.norm(shell_pos, axis=1, keepdims=True)
    e_theta = np.cross(r_hat, e_phi)
    e_theta_norm = np.linalg.norm(e_theta, axis=1, keepdims=True)
    e_theta_norm = np.where(e_theta_norm < 1e-12, 1.0, e_theta_norm)
    e_theta /= e_theta_norm
    vel[n_core:] = v_orb * e_phi
    vel[n_core:] = _jitter_in_plane(vel[n_core:], e_phi, e_theta, 0.01, rng)

    vel = _remove_net_momentum(vel)
    return pos.astype(np.float32), vel.astype(np.float32)


def disk(n: int = 4096,
         f_core: float = 0.5,
         r_disk: float = 4.0,
         seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """
    Flat disk print.

    Returns ``(positions, velocities)`` where core points occupy indices
    ``[0, n_core)`` and disk points occupy ``[n_core, n)``.

    Derivation:
      - Same core blob as ``core_shell``.
      - Disk points are uniform in area from ``4 * R_BOND`` to ``r_disk``,
        with Gaussian z-thickness ``~ R_BOND``.
      - Each radius has its own circular speed ``v(r) = sqrt(G * M_enc / r)``
        (differential rotation), azimuthal around z.
      - 1% in-plane tangential jitter and net-momentum removal.
    """
    rng = np.random.default_rng(seed)
    n_core = max(1, min(int(f_core * n), n - 1))
    n_disk = n - n_core

    pos = np.empty((n, 3), dtype=np.float64)

    # core blob
    r_core = _ball_radius_for_bond_spacing(n_core, R_BOND)
    pos[:n_core] = _uniform_in_ball(n_core, r_core, rng)

    # disk
    r_inner = 4.0 * R_BOND
    radii = np.sqrt(rng.uniform(r_inner * r_inner, r_disk * r_disk, n_disk))
    theta = rng.uniform(0.0, 2.0 * math.pi, n_disk)
    z = rng.normal(0.0, R_BOND / 3.0, n_disk)
    pos[n_core:, 0] = radii * np.cos(theta)
    pos[n_core:, 1] = radii * np.sin(theta)
    pos[n_core:, 2] = z

    # velocities: core at rest, disk in differential rotation
    vel = np.zeros((n, 3), dtype=np.float64)
    m_enc = float(n_core)
    disk_pos = pos[n_core:]
    e_phi = _azimuthal_unit_vector(disk_pos)
    r_xy = np.linalg.norm(disk_pos[:, :2], axis=1, keepdims=True)
    r_xy_safe = np.where(r_xy < 1e-12, 1.0, r_xy)
    # radial unit vector in the disk plane
    e_rad = disk_pos.copy()
    e_rad[:, 2] = 0.0
    e_rad /= r_xy_safe
    v_orb = np.sqrt(G * m_enc / r_xy_safe)
    vel[n_core:] = v_orb * e_phi
    vel[n_core:] = _jitter_in_plane(vel[n_core:], e_phi, e_rad, 0.01, rng)

    vel = _remove_net_momentum(vel)
    return pos.astype(np.float32), vel.astype(np.float32)


def lattice(n: int = 4096, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """
    Simple cubic crystal print.

    Returns ``(positions, velocities)`` for ``side^3`` points where
    ``side = ceil(n^(1/3))``; the actual count is therefore ``side^3``.

    Derivation:
      - Grid spacing ``= R_BOND``; side chosen so at least ``n`` sites are
        available.  Points are centered at the origin.
      - Thermal velocities with ``sigma = 0.01 * sqrt(K_BOND * R_BOND)``
        (bond energy scale).  Net momentum removed.
    """
    rng = np.random.default_rng(seed)
    side = int(math.ceil(n ** (1.0 / 3.0)))

    indices = np.arange(side, dtype=np.float64)
    offsets = (indices - (side - 1) / 2.0) * R_BOND
    x, y, z = np.meshgrid(offsets, offsets, offsets, indexing="ij")
    pos = np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1).astype(np.float64)

    sigma = 0.01 * math.sqrt(K_BOND * R_BOND)
    vel = rng.normal(0.0, sigma, size=pos.shape)
    vel = _remove_net_momentum(vel)

    return pos.astype(np.float32), vel.astype(np.float32)
