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


def lattice(n: int = 4096, seed: int = 0, spacing: float = R_BOND) -> tuple[np.ndarray, np.ndarray]:
    """
    Simple cubic crystal print.

    Returns ``(positions, velocities)`` for ``side^3`` points where
    ``side = ceil(n^(1/3))``; the actual count is therefore ``side^3``.

    Derivation:
      - Grid spacing defaults to ``R_BOND``.  After the 2026-08-06 crush
        series (8..4096 all collapse from a bond-spaced start) the spacing is
        a PRINT GEOMETRY parameter: the resistance is repulsion-only (a
        cushion on [r_wall, r_bond], nothing beyond), so the only stable
        prints are at the cushion equilibrium spacing (2^3 cube: d_eq ~
        0.048, kernel-exact corner-force root).  Printing at the derived
        equilibrium tests theCushionLaw (docs/THE_HIERARCHY.md).
      - Thermal velocities with ``sigma = 0.01 * sqrt(K_BOND * R_BOND)``
        (bond energy scale).  Net momentum removed.
    """
    rng = np.random.default_rng(seed)
    side = int(math.ceil(n ** (1.0 / 3.0)))

    indices = np.arange(side, dtype=np.float64)
    offsets = (indices - (side - 1) / 2.0) * spacing
    x, y, z = np.meshgrid(offsets, offsets, offsets, indexing="ij")
    pos = np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1).astype(np.float64)

    sigma = 0.01 * math.sqrt(K_BOND * R_BOND)
    vel = rng.normal(0.0, sigma, size=pos.shape)
    vel = _remove_net_momentum(vel)

    return pos.astype(np.float32), vel.astype(np.float32)


def bone(n: int = 1024,
         grain_side: int = 6,
         seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    BONE print: a rod of bonded lattice grains with two pinned anchor plates.

    Each grain is a simple-cubic lattice chunk of ``grain_side^3`` points at
    spacing ``R_BOND``.  Grains are placed along the x-axis so that the face
    atoms of neighboring grains are ``R_BOND`` apart, producing face-to-face
    bonds.  Two square lattice plates (pinned) cap the ends of the rod and are
    spaced one bond length from the terminal grain faces.

    Returns ``(positions, velocities, pin_mask, grain_ids)``:
      - ``positions`` / ``velocities`` are float32 (N, 3) arrays.
      - ``pin_mask`` is a length-N bool array; plate points are True.
      - ``grain_ids`` is a length-N int32 array; plate points are -1 and rod
        points carry their grain index.

    The actual point count is ``2 * grain_side^2 + n_grains * grain_side^3``
    where ``n_grains = max(1, n // grain_side^3)``.
    """
    rng = np.random.default_rng(seed)
    s = int(grain_side)
    if s < 2:
        raise ValueError("grain_side must be at least 2")
    pts_per_grain = s ** 3
    n_grains = max(1, n // pts_per_grain)

    # base cubic grain centered at origin
    offsets = (np.arange(s, dtype=np.float64) - (s - 1) / 2.0) * R_BOND
    gx, gy, gz = np.meshgrid(offsets, offsets, offsets, indexing="ij")
    base_grain = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    # rod: grains spaced by s*R_BOND so face points bond at R_BOND
    grain_positions = []
    grain_ids = []
    for g in range(n_grains):
        grain = base_grain.copy()
        grain[:, 0] += g * s * R_BOND
        grain_positions.append(grain)
        grain_ids.extend([g] * pts_per_grain)
    rod_pos = np.vstack(grain_positions)

    # anchor plates: s x s square lattices perpendicular to x
    plate_offsets = (np.arange(s, dtype=np.float64) - (s - 1) / 2.0) * R_BOND
    px, py = np.meshgrid(plate_offsets, plate_offsets, indexing="ij")
    plate_base = np.stack([px.ravel(), py.ravel(), np.zeros(s * s)], axis=1)

    left_plate = plate_base.copy()
    left_plate[:, 0] = -(s + 1) / 2.0 * R_BOND
    right_plate = plate_base.copy()
    right_plate[:, 0] = (n_grains * s - (s - 1) / 2.0 + (s + 1) / 2.0) * R_BOND
    # simplify: right terminal grain center = (n_grains-1)*s*R; its right face
    # at (n_grains-1)*s*R + (s-1)/2*R; plate one bond beyond that:
    right_plate[:, 0] = (n_grains - 1) * s * R_BOND + (s + 1) / 2.0 * R_BOND

    pos = np.vstack([left_plate, rod_pos, right_plate]).astype(np.float64)

    # center the whole assembly at the origin
    mid_x = (pos[:, 0].min() + pos[:, 0].max()) / 2.0
    pos[:, 0] -= mid_x

    n_total = pos.shape[0]
    vel = np.zeros((n_total, 3), dtype=np.float64)
    pin_mask = np.zeros(n_total, dtype=bool)
    n_plate = s * s
    pin_mask[:n_plate] = True
    pin_mask[n_plate + len(rod_pos):] = True

    ids = np.empty(n_total, dtype=np.int32)
    ids[:n_plate] = -1
    ids[n_plate:n_plate + len(rod_pos)] = np.array(grain_ids, dtype=np.int32)
    ids[n_plate + len(rod_pos):] = -1

    # tiny random jitter to break exact lattice degeneracy (<< R_WALL)
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pos.shape)
    pos += jitter

    return pos.astype(np.float32), vel.astype(np.float32), pin_mask, ids


def bone2(width: int = 4,
          height: int = 4,
          length: int = 16,
          spacing: float = 0.05,
          plate_gap: float | None = None,
          seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    BONE v2 print: a preloaded compression column (theCushionLaw).

    The column is printed ORDERED at cushion ``spacing`` (default 0.05) with a
    ``width × height`` cross-section and ``length`` layers along x.  Two pinned
    anchor plates (``width × height``) sit one ``plate_gap`` beyond the terminal
    layers; ``plate_gap`` defaults to ``spacing`` so the plates are in cushion
    contact.  Velocities are zero (cold print) apart from a tiny positional
    jitter to break degeneracy.

    Returns ``(positions, velocities, pin_mask, grain_ids)``:
      - ``positions`` / ``velocities`` are float32 (N, 3) arrays.
      - ``pin_mask`` is a length-N bool array; plate points are True.
      - ``grain_ids`` is a length-N int32 array; plate points are -1 and the
        single ordered column carries grain index 0.

    The point count is ``width * height * (length + 2)``.
    """
    rng = np.random.default_rng(seed)
    if plate_gap is None:
        plate_gap = spacing
    w = int(width)
    h = int(height)
    l = int(length)
    d = float(spacing)
    g = float(plate_gap)
    if w < 2 or h < 2 or l < 2:
        raise ValueError("width, height, and length must be at least 2")

    n_col = w * h * l
    n_plate = w * h

    # column grid centered at the origin
    x_off = (np.arange(l, dtype=np.float64) - (l - 1) / 2.0) * d
    y_off = (np.arange(w, dtype=np.float64) - (w - 1) / 2.0) * d
    z_off = (np.arange(h, dtype=np.float64) - (h - 1) / 2.0) * d
    gx, gy, gz = np.meshgrid(x_off, y_off, z_off, indexing="ij")
    col_pos = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    # plates perpendicular to x, in cushion contact with the terminal layers
    py, pz = np.meshgrid(y_off, z_off, indexing="ij")
    plate_yz = np.stack([py.ravel(), pz.ravel()], axis=1)
    left_plate = np.hstack([
        np.full((n_plate, 1), x_off[0] - g),
        plate_yz,
    ])
    right_plate = np.hstack([
        np.full((n_plate, 1), x_off[-1] + g),
        plate_yz,
    ])

    pos = np.vstack([left_plate, col_pos, right_plate]).astype(np.float64)

    vel = np.zeros((pos.shape[0], 3), dtype=np.float64)
    pin_mask = np.zeros(pos.shape[0], dtype=bool)
    pin_mask[:n_plate] = True
    pin_mask[n_plate + n_col:] = True

    grain_ids = np.empty(pos.shape[0], dtype=np.int32)
    grain_ids[:n_plate] = -1
    grain_ids[n_plate:n_plate + n_col] = 0
    grain_ids[n_plate + n_col:] = -1

    # tiny positional jitter to break exact lattice degeneracy (<< R_WALL)
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pos.shape)
    pos += jitter

    return pos.astype(np.float32), vel.astype(np.float32), pin_mask, grain_ids


def muscle(side: int = 4,
           spacing: float = 0.05,
           seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                   np.ndarray, float, float]:
    """
    THE MUSCLE print: a ``side³`` cushion droplet seated on a pinned left
    anchor plate, with a second pinned right plate at derived separation ``s₀``.

    The droplet is printed as a simple-cubic lattice at ``spacing`` (cushion
    spacing), left face in cushion contact with the left plate.  The right
    plate is placed at ``s₀ = 2 * R_droplet`` (plate-inner-face to
    plate-inner-face), where ``R_droplet`` is the radius of a ball with the
    same volume as ``side³`` points at ``spacing``.  This leaves a small
    cushion gap between the droplet's right face and the right plate so the
    bridge is pulling, not touching.

    Returns ``(positions, velocities, pin_mask, grain_ids, s0, R_droplet)``:
      - ``positions`` / ``velocities`` are float32 (N, 3) arrays.
      - ``pin_mask`` is length-N bool; both plates are pinned.
      - ``grain_ids`` is length-N int32; plates are -1, droplet is 0.
      - ``s0`` and ``R_droplet`` are the derived bridge numbers.

    The point count is ``side³ + 2 * side²``.
    """
    rng = np.random.default_rng(seed)
    s = int(side)
    if s < 2:
        raise ValueError("side must be at least 2")
    d = float(spacing)

    n_droplet = s ** 3
    n_plate = s * s

    # Droplet: s x s x s cubic lattice at cushion spacing.
    offsets = (np.arange(s, dtype=np.float64) - (s - 1) / 2.0) * d
    gx, gy, gz = np.meshgrid(offsets, offsets, offsets, indexing="ij")
    drop_pos = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    # Equivalent spherical radius from the droplet volume.
    R_droplet = _ball_radius_for_bond_spacing(n_droplet, d)
    s0 = 2.0 * R_droplet

    # Plates: s x s lattices perpendicular to x.
    py, pz = np.meshgrid(offsets, offsets, indexing="ij")
    plate_yz = np.stack([py.ravel(), pz.ravel()], axis=1)

    # Left plate inner face at x = 0; droplet left face at x = d.
    left_plate = np.hstack([np.zeros((n_plate, 1)), plate_yz])
    drop_pos[:, 0] += d + (s - 1) / 2.0 * d

    # Right plate inner face at x = s0.
    right_plate = np.hstack([np.full((n_plate, 1), s0), plate_yz])

    pos = np.vstack([left_plate, drop_pos, right_plate]).astype(np.float64)
    vel = np.zeros((pos.shape[0], 3), dtype=np.float64)

    pin_mask = np.zeros(pos.shape[0], dtype=bool)
    pin_mask[:n_plate] = True
    pin_mask[n_plate + n_droplet:] = True

    grain_ids = np.empty(pos.shape[0], dtype=np.int32)
    grain_ids[:n_plate] = -1
    grain_ids[n_plate:n_plate + n_droplet] = 0
    grain_ids[n_plate + n_droplet:] = -1

    # Tiny positional jitter to break exact lattice degeneracy (<< R_WALL).
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pos.shape)
    pos += jitter

    return pos.astype(np.float32), vel.astype(np.float32), pin_mask, grain_ids, s0, R_droplet
