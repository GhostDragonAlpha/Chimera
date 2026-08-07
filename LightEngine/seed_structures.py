"""
THE PRINTER — authored seed structures for the LightEngine kernel.

Each generator returns ``(positions, velocities)`` as float32 (N,3) arrays.
Velocities are derived from the same force laws that judge the run; geometry is
authored, constants are not.
"""

from __future__ import annotations

import math
import numpy as np

from LightEngine import kernel
from LightEngine.constants import G, R_WALL, R_BOND, R_C, K_BOND, EPS, S_WALL


# Cushion equilibrium spacing measured in theCushionLaw lattice8eq print
# (a 2^3 cube crushed to its stable corner-force root, ~0.0484 lu).
TENDON_D_EQ = 0.0484


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


def tendon(side: int = 4,
           n_len: int = 8,
           spacing: float = 0.05,
           preload_frac: float = 0.0,
           foot_side: int = 0,
           seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                   np.ndarray, float, float]:
    """
    THE TENDON print: a 2×2×n_len cushion rod seated between two pinned
    anchor plates, acting as a 1-D force router.

    The rod is printed as a simple-cubic lattice at ``spacing`` (cushion
    spacing), centered on the x-axis.  By default (``preload_frac=0.0``,
    ``foot_side=0``) the rod end faces sit at cushion equilibrium distance
    ``d_eq`` from the plates, giving

        s0 = rod_span + 2 * d_eq,   rod_span = (n_len - 1) * spacing.

    With ``preload_frac > 0`` the ends are pushed deeper into the cushion band
    by ``preload_frac * d_eq`` on each side, so the seat gap becomes
    ``d_eq * (1 - preload_frac)`` and

        s0 = rod_span + 2 * d_eq * (1 - preload_frac).

    With ``foot_side > 0`` a ``foot_side × foot_side`` foot layer (one point
    thick, plane normal to x) sits at each end plane IN PLACE OF the shaft's
    terminal 2×2 layer.  The shaft interior is therefore ``2 × 2 × (n_len - 2)``
    and the feet provide the end-face area that grips the plate.  ``rod_span``
    and ``s0`` remain unchanged from the no-foot case.

    For the default ``n_len=8`` and ``spacing=0.05``:
      - ``preload_frac=0.0, foot_side=0`` gives ``rod_span = 0.3500`` and
        ``s0 = 0.4468``.
      - ``preload_frac=0.5`` gives ``s0 = 0.3984``.
      - ``foot_side=4`` gives a 2×2×6 shaft (24 grains) plus two 4×4 feet
        (32 grains) for a total rod of 56 grains (N = 88 with the plates).

    Returns ``(positions, velocities, pin_mask, grain_ids, s0, rod_span)``:
      - ``positions`` / ``velocities`` are float32 (N, 3) arrays.
      - ``pin_mask`` is length-N bool; both plates are pinned.
      - ``grain_ids`` is length-N int32; plates are -1, rod is 0.
      - ``s0`` and ``rod_span`` are the derived router numbers.

    The default point count is ``4 * n_len + 2 * side**2``; with feet it is
    ``(4 * (n_len - 2) + 2 * foot_side**2) + 2 * side**2``.
    """
    rng = np.random.default_rng(seed)
    s = int(side)
    if s < 2:
        raise ValueError("side must be at least 2")
    l = int(n_len)
    if l < 2:
        raise ValueError("n_len must be at least 2")
    d = float(spacing)
    p = float(preload_frac)
    f = int(foot_side)

    n_plate = s * s

    d_eq = TENDON_D_EQ
    rod_span = (l - 1) * d
    seat_gap = d_eq * (1.0 - p)
    s0 = rod_span + 2.0 * seat_gap

    # Shaft: 2 x 2 x l cubic lattice along x, centered on the axis.
    # With feet, the terminal shaft layers are replaced by the foot layers,
    # so the interior shaft has l - 2 layers.
    shaft_len = l if f == 0 else max(2, l - 2)
    x_off = (np.arange(shaft_len, dtype=np.float64) - (shaft_len - 1) / 2.0) * d
    y_off = (np.arange(2, dtype=np.float64) - 0.5) * d
    z_off = (np.arange(2, dtype=np.float64) - 0.5) * d
    gx, gy, gz = np.meshgrid(x_off, y_off, z_off, indexing="ij")
    shaft_pos = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)
    # The shaft (or shaft interior, when feet replace the terminals) is
    # centered in the same overall rod_span, so the shift is unchanged.
    shaft_pos[:, 0] += seat_gap + rod_span / 2.0

    rod_parts = [shaft_pos]
    if f > 0:
        if l < 4:
            raise ValueError("n_len must be at least 4 when foot_side > 0")
        # Feet: one f x f layer at each end, replacing the terminal shaft layer.
        foot_off = (np.arange(f, dtype=np.float64) - (f - 1) / 2.0) * d
        fy, fz = np.meshgrid(foot_off, foot_off, indexing="ij")
        foot_yz = np.stack([fy.ravel(), fz.ravel()], axis=1)
        left_foot = np.hstack([
            np.full((f * f, 1), seat_gap),
            foot_yz,
        ])
        right_foot = np.hstack([
            np.full((f * f, 1), seat_gap + rod_span),
            foot_yz,
        ])
        rod_parts = [left_foot, shaft_pos, right_foot]

    rod_pos = np.vstack(rod_parts)
    n_rod = rod_pos.shape[0]

    # Print law: no two grains may share a position.
    pos_check = rod_pos.astype(np.float64)
    diff = pos_check[:, None, :] - pos_check[None, :, :]
    r2 = (diff * diff).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    min_pair_dist = float(np.sqrt(r2.min()))
    if min_pair_dist <= 1e-6:
        raise RuntimeError(
            f"tendon print law violated: minimum pair distance {min_pair_dist} "
            f"<= 1e-6 (foot_side={f}, preload_frac={p})")

    # Plates: s x s lattices perpendicular to x.
    p_off = (np.arange(s, dtype=np.float64) - (s - 1) / 2.0) * d
    py, pz = np.meshgrid(p_off, p_off, indexing="ij")
    plate_yz = np.stack([py.ravel(), pz.ravel()], axis=1)
    left_plate = np.hstack([np.zeros((n_plate, 1)), plate_yz])
    right_plate = np.hstack([np.full((n_plate, 1), s0), plate_yz])

    pos = np.vstack([left_plate, rod_pos, right_plate]).astype(np.float64)
    vel = np.zeros((pos.shape[0], 3), dtype=np.float64)

    pin_mask = np.zeros(pos.shape[0], dtype=bool)
    pin_mask[:n_plate] = True
    pin_mask[n_plate + n_rod:] = True

    grain_ids = np.empty(pos.shape[0], dtype=np.int32)
    grain_ids[:n_plate] = -1
    grain_ids[n_plate:n_plate + n_rod] = 0
    grain_ids[n_plate + n_rod:] = -1

    # Tiny positional jitter to break exact lattice degeneracy (<< R_WALL).
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pos.shape)
    pos += jitter

    return pos.astype(np.float32), vel.astype(np.float32), pin_mask, grain_ids, s0, rod_span


def joint(spacing: float = 0.05,
          seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                  np.ndarray, dict]:
    """
    THE JOINT print: a pinned ground plate, a vertical bone A (pillar), a
    horizontal bone B (limb), and a muscle droplet that pulls B's far half.

    Geometry (all lengths in lu, derived from ``spacing`` and ``d_eq``):
      - ground plate: 6×6 lattice in the z=0 plane, spacing ``spacing``;
      - bone A: 4×4×16 column vertical along z, base seated ``d_eq`` above the
        plate (grain_ids = 1);
      - bone B: 4×4×16 column horizontal along x, joint-end face seated
        ``d_eq`` above A's top face, cantilevered in +x (grain_ids = 2);
      - muscle droplet: 4³ cube, bottom face seated ``d_eq`` above the plate,
        offset along x under B's far half (grain_ids = 0).

    The A-top / B-bottom cushion contact is the joint fulcrum.  No two grains
    share a position; the builder raises if the print law is violated.

    Returns ``(positions, velocities, pin_mask, grain_ids, derived)``:
      - ``positions`` / ``velocities`` are float32 (N, 3) arrays.
      - ``pin_mask`` is length-N bool; only the ground plate is pinned.
      - ``grain_ids`` is length-N int32; plate = -1, droplet = 0, A = 1, B = 2.
      - ``derived`` is a dict with the joint contact point, B's weight W
        (pairwise DRAW magnitude B × plate), the muscle pull F_m (pairwise
        DRAW magnitude B × droplet), and the print constants ``d_eq`` and
        ``r_c``.
    """
    rng = np.random.default_rng(seed)
    d = float(spacing)
    d_eq = TENDON_D_EQ

    # Ground plate: 6×6 at z = 0.
    plate_side = 6
    n_plate = plate_side * plate_side
    plate_off = (np.arange(plate_side, dtype=np.float64)
                 - (plate_side - 1) / 2.0) * d
    px, py = np.meshgrid(plate_off, plate_off, indexing="ij")
    plate_pos = np.stack([px.ravel(), py.ravel(), np.zeros(n_plate)], axis=1)

    # Muscle droplet: 4³, bottom at z = d_eq, centered under B's far half.
    drop_side = 4
    n_drop = drop_side ** 3
    drop_off = (np.arange(drop_side, dtype=np.float64)
                - (drop_side - 1) / 2.0) * d
    # B spans x in [0, (B_l - 1) * d] = [0, 0.75]; far half is [0.375, 0.75].
    drop_x_center = 0.5625  # midpoint of B's far half
    drop_x = drop_off + drop_x_center
    drop_y = drop_off
    drop_z = np.arange(drop_side, dtype=np.float64) * d + d_eq
    gx, gy, gz = np.meshgrid(drop_x, drop_y, drop_z, indexing="ij")
    drop_pos = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    # Bone A: 4×4×16 vertical pillar, base at z = d_eq.
    A_w, A_h, A_l = 4, 4, 16
    n_A = A_w * A_h * A_l
    A_x_off = (np.arange(A_w, dtype=np.float64)
               - (A_w - 1) / 2.0) * d
    A_y_off = (np.arange(A_h, dtype=np.float64)
               - (A_h - 1) / 2.0) * d
    A_z_off = np.arange(A_l, dtype=np.float64) * d + d_eq
    gx, gy, gz = np.meshgrid(A_x_off, A_y_off, A_z_off, indexing="ij")
    A_pos = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    # Bone B: 4×4×16 horizontal limb, joint end seated d_eq above A's top face.
    A_top_z = d_eq + (A_l - 1) * d
    B_w, B_h, B_l = 4, 4, 16
    n_B = B_w * B_h * B_l
    B_x_off = np.arange(B_l, dtype=np.float64) * d  # joint-end face at x = 0
    B_y_off = (np.arange(B_w, dtype=np.float64)
               - (B_w - 1) / 2.0) * d
    B_z_off = np.arange(B_h, dtype=np.float64) * d + A_top_z + d_eq
    gx, gy, gz = np.meshgrid(B_x_off, B_y_off, B_z_off, indexing="ij")
    B_pos = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    pos = np.vstack([plate_pos, drop_pos, A_pos, B_pos]).astype(np.float64)

    # Print law: no two grains may share a position.
    diff = pos[:, None, :] - pos[None, :, :]
    r2 = (diff * diff).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    min_pair_dist = float(np.sqrt(r2.min()))
    if min_pair_dist <= 1e-6:
        raise RuntimeError(
            f"joint print law violated: minimum pair distance {min_pair_dist} "
            f"<= 1e-6")

    # Tiny positional jitter to break exact lattice degeneracy (<< R_WALL).
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pos.shape)
    pos += jitter

    N = pos.shape[0]
    vel = np.zeros((N, 3), dtype=np.float64)

    pin_mask = np.zeros(N, dtype=bool)
    pin_mask[:n_plate] = True

    grain_ids = np.empty(N, dtype=np.int32)
    grain_ids[:n_plate] = -1
    grain_ids[n_plate:n_plate + n_drop] = 0
    grain_ids[n_plate + n_drop:n_plate + n_drop + n_A] = 1
    grain_ids[n_plate + n_drop + n_A:] = 2

    # Derived quantities (computed from the cold print geometry).
    joint_contact_point = np.array([0.0, 0.0, A_top_z], dtype=np.float64)

    def _draw_force_magnitude(src: np.ndarray, dst: np.ndarray) -> float:
        """Magnitude of the pairwise softened-DRAW force on ``dst`` from ``src``."""
        # Attractive DRAW: force on dst is G * (src - dst) / r^3.
        dpos = src[:, None, :] - dst[None, :, :]  # (n_src, n_dst, 3)
        r2 = (dpos * dpos).sum(axis=2) + EPS ** 2
        # z-component of force on dst (negative when src is below dst, i.e.
        # the attractive pull is downward).
        fz = G * dpos[:, :, 2] / (r2 ** 1.5)
        # Downward pull magnitude = -sum(fz) over all source-destination pairs.
        return float(np.maximum(-fz.sum(), 0.0))

    W = _draw_force_magnitude(plate_pos, B_pos)
    F_m = _draw_force_magnitude(drop_pos, B_pos)

    derived = {
        "joint_contact_point": joint_contact_point,
        "W": W,
        "F_m": F_m,
        "d_eq": d_eq,
        "r_c": R_C,
        "A_top_z": A_top_z,
        "B_length": (B_l - 1) * d,
    }

    return pos.astype(np.float32), vel.astype(np.float32), pin_mask, grain_ids, derived


# Cache for the 2-D in-plane equilibrium spacing derived below.
_D_EQ_2D_CACHE: float | None = None


def derive_sheet_equilibrium_spacing(sheet_side: int = 16,
                                     a_lo: float = 0.03,
                                     a_hi: float = 0.10,
                                     tol: float = 1e-5,
                                     max_iter: int = 50,
                                     verbose: bool = True) -> float:
    """
    Derive the 2-D in-plane equilibrium spacing d_eq_2D for a finite square
    sheet from the kernel forces.

    Derivation:
      - Interior grains of a uniform lattice feel zero net in-plane force by
        symmetry; the equilibrium lives at the BOUNDARY.
      - For a side×side flat patch at spacing ``a``, every edge grain feels a
        net inward DRAW from the sheet plus outward cushion/wall repulsion from
        its in-plane neighbors.
      - d_eq_2D is the zero-crossing of F_edge(a), the mean inward-signed
        in-plane force on the perimeter grains, computed with
        ``kernel.compute_forces`` on a static patch (zero velocity).
      - Bisection bracket [a_lo, a_hi] = [0.03, 0.10] lu: the cushion band is
        [R_WALL, R_BOND] = [0.05, 0.15] and the 3-D droplet equilibrium sits
        just under R_WALL at ~0.0484 lu.  The 2-D root is expected to differ,
        so the bracket is intentionally wide and the measurement is allowed to
        find the root without bias.

    Returns d_eq_2D to the requested tolerance.  The result is cached so the
    expensive O(N^2) root find is evaluated only once per process.
    """
    global _D_EQ_2D_CACHE
    if _D_EQ_2D_CACHE is not None:
        return _D_EQ_2D_CACHE

    def _edge_force(a: float) -> float:
        """Mean inward-signed in-plane force on the patch perimeter."""
        off = (np.arange(sheet_side, dtype=np.float64)
               - (sheet_side - 1) / 2.0) * a
        sx, sy = np.meshgrid(off, off, indexing="ij")
        pos = np.stack([
            sx.ravel(),
            sy.ravel(),
            np.zeros(sheet_side * sheet_side, dtype=np.float64),
        ], axis=1).astype(np.float32)
        vel = np.zeros_like(pos)
        acc = kernel.compute_forces(pos, vel, use_cuda=False)

        k = np.arange(sheet_side * sheet_side)
        x_idx = k // sheet_side
        y_idx = k % sheet_side
        edge = (
            (x_idx == 0) |
            (x_idx == sheet_side - 1) |
            (y_idx == 0) |
            (y_idx == sheet_side - 1)
        )

        # Inward radial unit vector in the sheet plane.
        r_xy = pos[edge, :2]
        norms = np.linalg.norm(r_xy, axis=1, keepdims=True)
        norms = np.where(norms < 1e-12, 1.0, norms)
        inward = -r_xy / norms

        f_in = np.einsum("ij,ij->i", acc[edge, :2], inward)
        return float(f_in.mean())

    f_lo = _edge_force(a_lo)
    f_hi = _edge_force(a_hi)
    if f_lo * f_hi > 0:
        raise RuntimeError(
            f"derive_sheet_equilibrium_spacing: bracket does not straddle a "
            f"root (F({a_lo})={f_lo:.4f}, F({a_hi})={f_hi:.4f}). "
            f"Widen [a_lo, a_hi].")

    if verbose:
        print("[derive d_eq_2D] bracket rationale: cushion band is "
              f"[R_WALL, R_BOND] = [{R_WALL:.2f}, {R_BOND:.2f}] lu; "
              f"3-D droplet d_eq = {TENDON_D_EQ:.5f} lu sits just under R_WALL.")
        print("[derive d_eq_2D] bisecting F_edge(a) = 0 on the 16x16 patch:")
        print(f"  iter 0: a={a_lo:.5f} F={f_lo:+.6f}")
        print(f"  iter 0: a={a_hi:.5f} F={f_hi:+.6f}")

    a_mid = 0.5 * (a_lo + a_hi)
    f_mid = _edge_force(a_mid)
    for i in range(max_iter):
        if f_lo * f_mid <= 0.0:
            a_hi, f_hi = a_mid, f_mid
        else:
            a_lo, f_lo = a_mid, f_mid
        a_mid = 0.5 * (a_lo + a_hi)
        f_mid = _edge_force(a_mid)
        if verbose:
            print(f"  iter {i + 1}: a={a_mid:.5f} F={f_mid:+.6f}  "
                  f"bracket=[{a_lo:.5f}, {a_hi:.5f}]")
        if abs(a_hi - a_lo) <= tol:
            break

    d_eq_2d = float(a_mid)
    _D_EQ_2D_CACHE = d_eq_2d
    if verbose:
        print(f"[derive d_eq_2D] root d_eq_2D = {d_eq_2d:.5f} lu "
              f"(tol={tol:.1e}, iters={i + 1})")
    return d_eq_2d


def sheet(mode: str = "flat",
          spacing: float | None = None,
          framed: bool = False,
          seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                  np.ndarray, dict]:
    """
    THE SHEET print: a 16×16 sheet one grain thick.

    Modes:
      - "flat":  sheet printed d_eq + one lattice step above a pinned 6×6
                 plate (unless ``framed``).
      - "bump":  a 4×4×4 block sits on the plate under the sheet's center;
                 the sheet is printed d_eq + one step above the block top.
      - "free":  the sheet alone in space, same initial height as flat
                 (anti-falsifier: it must ball up under self-DRAW).
      - "tear":  flat print with two opposite y-edge rows pinned and pulled
                 apart in the driver (unless ``framed``).

    ``spacing`` is the in-plane lattice step.  If ``None``, the 2-D in-plane
    equilibrium spacing d_eq_2D is derived from the kernel via
    ``derive_sheet_equilibrium_spacing``.  The explicit ``spacing=0.05`` path
    is preserved for v1/v2 reproducibility.

    ``framed`` (v3): the four border rows of the sheet (60 grains) are pinned
    in their print positions and the plate is omitted.  The frame itself is
    the membrane that holds the plane.  In framed tear mode, two opposite
    border rows serve as the moving grips.

    Grain ids: plate = -1, sheet = 0, block = 1.

    Returns ``(positions, velocities, pin_mask, grain_ids, derived)``:
      - ``positions`` / ``velocities`` are float32 (N, 3) arrays.
      - ``pin_mask`` is length-N bool; plate / frame pinned as described above.
      - ``derived`` carries d_eq, d_eq_2D, spacing, the cushion band, sheet
        width, frame count, and mode-specific derived numbers.
    """
    rng = np.random.default_rng(seed)
    d_eq = TENDON_D_EQ
    if spacing is None:
        d = derive_sheet_equilibrium_spacing(sheet_side=16, verbose=True)
    else:
        d = float(spacing)
    d_eq_2d = float(d)
    cushion_band = (d_eq - 0.02, d_eq + 0.05)
    sheet_side = 16
    n_sheet = sheet_side * sheet_side
    sheet_width = (sheet_side - 1) * d

    if mode not in ("bump", "flat", "free", "tear"):
        raise ValueError(f"unknown sheet mode: {mode}")

    # Sheet grid in x-y, centered at the origin.
    off = (np.arange(sheet_side, dtype=np.float64)
           - (sheet_side - 1) / 2.0) * d
    sx, sy = np.meshgrid(off, off, indexing="ij")
    sx = sx.ravel()
    sy = sy.ravel()

    if mode == "bump":
        # 4×4×4 block centered under the sheet, bottom seated d_eq above plate.
        block_side = 4
        block_off = (np.arange(block_side, dtype=np.float64)
                     - (block_side - 1) / 2.0) * d
        bx, by = np.meshgrid(block_off, block_off, indexing="ij")
        bx = np.repeat(bx.ravel(), block_side)
        by = np.repeat(by.ravel(), block_side)
        bz = np.tile(np.arange(block_side, dtype=np.float64) * d + d_eq,
                     block_side * block_side)
        block_pos = np.stack([bx, by, bz], axis=1)
        block_top_z = d_eq + (block_side - 1) * d
        sheet_z = block_top_z + d_eq + d
    else:
        block_pos = np.zeros((0, 3), dtype=np.float64)
        block_top_z = 0.0
        sheet_z = d_eq + d

    sheet_pos = np.stack([
        sx,
        sy,
        np.full(n_sheet, sheet_z, dtype=np.float64),
    ], axis=1)

    if framed:
        # v3: the frame itself is the membrane; no substrate plate.
        plate_pos = np.zeros((0, 3), dtype=np.float64)
        n_plate = 0
    elif mode == "free":
        # No plate, no block.
        plate_pos = np.zeros((0, 3), dtype=np.float64)
        n_plate = 0
    else:
        # Pinned 6×6 ground plate at z = 0.
        plate_side = 6
        n_plate = plate_side * plate_side
        p_off = (np.arange(plate_side, dtype=np.float64)
                 - (plate_side - 1) / 2.0) * d
        px, py = np.meshgrid(p_off, p_off, indexing="ij")
        plate_pos = np.stack([
            px.ravel(), py.ravel(), np.zeros(n_plate, dtype=np.float64)
        ], axis=1)

    pos = np.vstack([plate_pos, sheet_pos, block_pos]).astype(np.float64)
    N = pos.shape[0]
    vel = np.zeros((N, 3), dtype=np.float64)

    grain_ids = np.empty(N, dtype=np.int32)
    grain_ids[:n_plate] = -1
    grain_ids[n_plate:n_plate + n_sheet] = 0
    grain_ids[n_plate + n_sheet:] = 1

    # Local lattice indices for the sheet grains.
    x_indices = np.arange(n_sheet) // sheet_side
    y_indices = np.arange(n_sheet) % sheet_side
    frame_mask = (
        (x_indices == 0) |
        (x_indices == sheet_side - 1) |
        (y_indices == 0) |
        (y_indices == sheet_side - 1)
    )

    pin_mask = np.zeros(N, dtype=bool)
    if n_plate > 0:
        pin_mask[:n_plate] = True

    sheet_start = n_plate
    if framed:
        # Pin all four border rows (the frame).
        pin_mask[sheet_start:sheet_start + n_sheet] = frame_mask
    elif mode == "tear":
        # Pin the two y-edge rows (y-index 0 and y-index sheet_side-1).
        top_row = y_indices == 0
        bottom_row = y_indices == (sheet_side - 1)
        pin_mask[sheet_start:sheet_start + n_sheet] = (top_row | bottom_row)

    # Print law: no two grains share a position.
    diff = pos[:, None, :] - pos[None, :, :]
    r2 = (diff * diff).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    min_pair_dist = float(np.sqrt(r2.min()))
    if min_pair_dist <= 1e-6:
        raise RuntimeError(
            f"sheet print law violated: minimum pair distance {min_pair_dist} "
            f"<= 1e-6 (mode={mode})")

    # Tiny positional jitter to break exact lattice degeneracy (<< R_WALL).
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pos.shape)
    pos += jitter

    derived = {
        "d_eq": d_eq,
        "d_eq_2D": d_eq_2d,
        "spacing": d,
        "cushion_band": cushion_band,
        "sheet_width": sheet_width,
        "sheet_side": sheet_side,
        "sheet_z": sheet_z,
        "block_top_z": block_top_z,
        "n_plate": n_plate,
        "n_sheet": n_sheet,
        "n_block": block_pos.shape[0],
        "mode": mode,
        "framed": bool(framed),
        "frame": int(frame_mask.sum()),
    }
    if mode == "tear":
        # Rows are pulled apart along y.  Print separation of the pinned rows.
        derived["pinned_row_separation"] = sheet_width
        derived["max_separation"] = 4.0 * sheet_width
        if framed:
            derived["n_pinned"] = int(frame_mask.sum())
        else:
            derived["n_pinned"] = int(top_row.sum() + bottom_row.sum())

    return pos.astype(np.float32), vel.astype(np.float32), pin_mask, grain_ids, derived


def skin(spacing: float = 0.05,
         seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                  np.ndarray, float, float, dict]:
    """
    THE SKIN print: a 16×16 mat at d_eq_2D draped conformal to the muscle bulk.

    Builds the settled muscle print (two pinned 4×4 plates + 4³ droplet bridge)
    and then prints a 16×16 mat one lattice step (d_eq_2D) above the droplet's
    top face, centered over the droplet.  The mat is unpinned; it is held to
    the muscle only by the muscle's DRAW.

    Returns ``(positions, velocities, pin_mask, grain_ids, s0, R_droplet,
    derived)``:
      - grain ids: -1 = plates, 0 = droplet, 1 = mat.
      - ``derived`` carries d_eq_2D, the conform band (cushion band union the
        wall-seat band from joint v2), droplet surface-grain indices, and
        counts needed by the driver.
    """
    rng = np.random.default_rng(seed)
    muscle_spacing = float(spacing)

    # Parent membrane: the settled muscle print.
    pos_m, vel_m, pin_mask_m, grain_ids_m, s0, R_droplet = muscle(
        side=4, spacing=muscle_spacing, seed=seed)
    n_plate = int((grain_ids_m == -1).sum())
    n_droplet = int((grain_ids_m == 0).sum())
    drop_idx_global = np.flatnonzero(grain_ids_m == 0)
    droplet_pos = pos_m[drop_idx_global].astype(np.float64)

    # Mat: 16×16 sheet printed at the derived 2-D equilibrium spacing.
    d_eq_2d = derive_sheet_equilibrium_spacing(verbose=False)
    pos_s, vel_s, pin_mask_s, grain_ids_s, sheet_derived = sheet(
        mode="free", spacing=d_eq_2d, seed=seed)
    n_mat = pos_s.shape[0]

    # Center the mat over the droplet, one lattice step above its top face.
    droplet_com = droplet_pos.mean(axis=0)
    droplet_top_z = float(droplet_pos[:, 2].max())
    target_z = droplet_top_z + d_eq_2d
    shift = np.array([
        droplet_com[0],
        droplet_com[1],
        target_z - sheet_derived["sheet_z"],
    ], dtype=np.float64)
    pos_s = pos_s.astype(np.float64) + shift
    vel_s = vel_s.astype(np.float64)

    # Combine the two prints.
    pos = np.vstack([pos_m, pos_s]).astype(np.float64)
    vel = np.vstack([vel_m, vel_s]).astype(np.float64)
    pin_mask = np.concatenate([pin_mask_m, pin_mask_s])
    grain_ids = np.concatenate([
        grain_ids_m,
        np.full(n_mat, 1, dtype=np.int32),
    ])

    # Droplet surface grains: grains with no neighbor above them within
    # 1.5 lattice steps.  A surface grain has a neighbor-free +z side so the
    # mat can band to it.  The criterion is derived from the muscle spacing.
    surface_local = []
    for i, p in enumerate(droplet_pos):
        dz = droplet_pos[:, 2] - p[2]
        above = dz > 0.0
        if not above.any():
            surface_local.append(i)
            continue
        dists = np.linalg.norm(droplet_pos[above] - p, axis=1)
        if not (dists <= 1.5 * muscle_spacing).any():
            surface_local.append(i)
    surface_local = np.array(surface_local, dtype=np.int32)

    # Print law: no two grains shared a position across the whole assembly.
    diff = pos[:, None, :] - pos[None, :, :]
    r2 = (diff * diff).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    min_pair_dist = float(np.sqrt(r2.min()))
    if min_pair_dist <= 1e-6:
        raise RuntimeError(
            f"skin print law violated: minimum pair distance {min_pair_dist} "
            f"<= 1e-6")

    d_eq = TENDON_D_EQ
    # Conform band: union of cushion band around the droplet's d_eq and the
    # wall-seat band [S_WALL - 0.01, S_WALL + 0.01] measured from joint v2.
    conform_lo = min(d_eq - 0.02, S_WALL - 0.01)
    conform_hi = d_eq + 0.05

    derived = {
        "d_eq_2D": d_eq_2d,
        "muscle_spacing": muscle_spacing,
        "s0": s0,
        "R_droplet": R_droplet,
        "conform_band": (conform_lo, conform_hi),
        "surface_grains": surface_local,
        "n_plate": n_plate,
        "n_droplet": n_droplet,
        "n_mat": n_mat,
        "slide_bar": 2.0 * muscle_spacing,
        "droplet_top_z": droplet_top_z,
    }

    return (pos.astype(np.float32), vel.astype(np.float32), pin_mask,
            grain_ids, s0, R_droplet, derived)


def _draw_force_z(src: np.ndarray, dst: np.ndarray, eps: float = EPS) -> float:
    """
    Sum the z-component of the softened-DRAW force that ``src`` exerts on
    ``dst``.  Negative means ``dst`` is pulled downward (toward a src below it).
    """
    dpos = src[:, None, :] - dst[None, :, :]
    r2 = (dpos * dpos).sum(axis=2) + eps * eps
    fz = G * dpos[:, :, 2] / (r2 ** 1.5)
    return float(fz.sum())


def _downward_draw_magnitude(src: np.ndarray, dst: np.ndarray,
                             eps: float = EPS) -> float:
    """Downward pull magnitude of ``src`` on ``dst`` (non-negative)."""
    return float(np.maximum(-_draw_force_z(src, dst, eps), 0.0))


def _R_true_at_print(pos: np.ndarray,
                     grain_ids: np.ndarray,
                     contact_point: np.ndarray,
                     pin_mask: np.ndarray) -> tuple[float, float, float]:
    """
    Kernel torque ratio about the fulcrum contact point at the cold print.

    The kernel is asked for the static force on every grain (zero velocity,
    current positions).  Only FREE grains are summed: every pinned body is a
    support and is excluded (ground plate in all versions; the fulcrum block in
    the pinned-fulcrum v3).  The moving bodies --- lever, droplet, load --- are
    the ones that generate torque about the fulcrum.

    Sign convention: muscle-side-down torque is positive.  For a grain at
    position r relative to the contact point and force F = a (mass = 1),
    the signed z-torque is r_x * F_z - r_z * F_x.

    Returns (R_true, tau_pos, tau_neg) where R_true = tau_pos / tau_neg and
    tau_pos / tau_neg are the absolute totals of muscle-side-down and
    load-side-down torques.
    """
    acc = kernel.compute_forces(
        pos.astype(np.float32),
        np.zeros_like(pos, dtype=np.float32),
        use_cuda=False)

    pos64 = np.asarray(pos, dtype=np.float64)
    acc64 = np.asarray(acc, dtype=np.float64)
    cp = np.asarray(contact_point, dtype=np.float64)

    free = (grain_ids != -1) & (~pin_mask)
    r = pos64[free] - cp
    F = acc64[free]
    tau_z = r[:, 0] * F[:, 2] - r[:, 2] * F[:, 0]

    tau_pos = float(np.maximum(tau_z, 0.0).sum())
    tau_neg = float(np.maximum(-tau_z, 0.0).sum())
    if tau_neg <= 0.0:
        R_true = float("inf")
    else:
        R_true = tau_pos / tau_neg
    return R_true, tau_pos, tau_neg


def lever(control: bool = False,
          spacing: float = 0.05,
          seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                  np.ndarray, dict]:
    """
    THE LEVER v6 print: captured fulcrum saddle, 13-ring hollow tube,
    plate-seated muscle droplet, insertion fraction derived by bisection.

    Grain ids:
      - plate   = -1 (pinned)
      - droplet = 0  (muscle)
      - fulcrum = 1  (pinned block + cheeks)
      - lever   = 2
      - load    = 3

    Geometry (all numbers derived from ``spacing`` and ``d_eq``):
      - 6x6 ground plate at z = 0.
      - 4x4x4 fulcrum block seated d_eq above the plate and pinned to it.
      - One-grain-thick cheeks on each side of the block (4x1x3 grains),
        centered at y = +/-(0.10 + d_eq + d/2) and rising from the block
        top, forming a captured saddle that allows only rotation.
      - 4x4 hollow tube lever (1-grain shell, 2x2 void), fixed at 13 rings
        (12 grains per ring, 156 total).
      - 4^3 standard muscle droplet seated on the plate at the arm tip;
        the insertion fraction alpha is re-derived by bisection on kernel
        static-torque quantities (no parameter sweep).
      - 4^3 load block resting on the lever's load (right) end, d_eq above
        the lever top face.

    STATIC GATE: alpha is derived in two bisection stages on the cold-print
    kernel torque ratio R_true(cx) sampled over the off-edge contact bracket.
      1. Find alpha_low such that max_R_offedge(alpha_low) = 2.0.
      2. Refine upward on [alpha_low, 0.12] until the control contact is
         muscle-ward of the main contact (a_m_ctrl < a_m_main).
    The main run uses the leftmost off-edge contact with R_true = 2.0 +/- 0.1;
    the control run uses the leftmost off-edge contact with R_true in
    [0.5, 1.05].

    Returns ``(positions, velocities, pin_mask, grain_ids, derived)``.
    """
    rng = np.random.default_rng(seed)
    d = float(spacing)
    d_eq = TENDON_D_EQ

    # Plate: 6x6 at z = 0.
    plate_side = 6
    n_plate = plate_side * plate_side
    p_off = (np.arange(plate_side, dtype=np.float64)
             - (plate_side - 1) / 2.0) * d
    px, py = np.meshgrid(p_off, p_off, indexing="ij")
    plate_pos = np.stack([px.ravel(), py.ravel(),
                          np.zeros(n_plate, dtype=np.float64)], axis=1)

    # Fulcrum block: 4x4x4, bottom at z = d_eq.
    fulcrum_side = 4
    n_fulcrum_block = fulcrum_side ** 3
    f_off = (np.arange(fulcrum_side, dtype=np.float64)
             - (fulcrum_side - 1) / 2.0) * d
    fulcrum_z = np.arange(fulcrum_side, dtype=np.float64) * d + d_eq
    fulcrum_top_z = d_eq + (fulcrum_side - 1) * d
    fulcrum_half_width = (fulcrum_side - 1) / 2.0 * d

    # v6 cheeks: captured saddle. One grain thick, centered at y = +/-0.1734,
    # rising 3 layers above the fulcrum top (top layer 0.10 lu above perch).
    cheek_y_center = 0.10 + d_eq + d / 2.0
    n_cheek_z = 3
    cheek_x = f_off
    cheek_z = np.arange(n_cheek_z, dtype=np.float64) * d + fulcrum_top_z
    cxg, cyg, czg = np.meshgrid(
        cheek_x, np.array([cheek_y_center]), cheek_z, indexing="ij")
    cheek_pos_plus = np.stack(
        [cxg.ravel(), cyg.ravel(), czg.ravel()], axis=1)
    cheek_pos_minus = cheek_pos_plus.copy()
    cheek_pos_minus[:, 1] = -cheek_y_center
    cheek_pos = np.vstack([cheek_pos_plus, cheek_pos_minus])
    n_cheek = cheek_pos.shape[0]
    n_fulcrum = n_fulcrum_block + n_cheek

    # Load block is always 4^3.
    load_side = 4
    n_load = load_side ** 3
    load_off = f_off
    load_y = f_off

    # Muscle droplet: 4^3, seated on the plate.
    drop_side = 4
    n_drop = drop_side ** 3
    drop_off = (np.arange(drop_side, dtype=np.float64)
                - (drop_side - 1) / 2.0) * d
    drop_z = np.arange(drop_side, dtype=np.float64) * d + d_eq

    # Lever: fixed 13-ring 4x4 hollow tube (12 grains per ring).
    length = 13
    s = 4
    x_off = (np.arange(length, dtype=np.float64)
             - (length - 1) / 2.0) * d
    yz_off = (np.arange(s, dtype=np.float64)
              - (s - 1) / 2.0) * d
    gy, gz = np.meshgrid(yz_off, yz_off, indexing="ij")
    inner = (np.abs(gy) <= 0.5 * d + 1e-12) & (np.abs(gz) <= 0.5 * d + 1e-12)
    shell = ~inner
    y_shell = gy[shell]
    z_shell = gz[shell]
    n_ring = int(y_shell.size)  # 12
    x_all = np.repeat(x_off, n_ring)
    y_all = np.tile(y_shell, length)
    z_all = np.tile(z_shell, length)
    lever_pos = np.stack([x_all, y_all, z_all], axis=1)
    n_lever = lever_pos.shape[0]
    L = (length - 1) * d

    lever_bottom_z = fulcrum_top_z + d_eq
    lever_top_z = lever_bottom_z + (fulcrum_side - 1) * d
    lever_pos = lever_pos.copy()
    lever_pos[:, 2] += lever_bottom_z + fulcrum_half_width

    muscle_end_x = float(x_off[0])
    load_end_x = float(x_off[-1])
    tube_half_width = (s - 1) / 2.0 * d

    # Fixed grain ids and pin mask (independent of alpha / contact point).
    n_total = n_plate + n_drop + n_fulcrum + n_lever + n_load
    grain_ids = np.empty(n_total, dtype=np.int32)
    grain_ids[:n_plate] = -1
    grain_ids[n_plate:n_plate + n_drop] = 0
    grain_ids[n_plate + n_drop:n_plate + n_drop + n_fulcrum] = 1
    grain_ids[n_plate + n_drop + n_fulcrum:
              n_plate + n_drop + n_fulcrum + n_lever] = 2
    grain_ids[n_plate + n_drop + n_fulcrum + n_lever:] = 3

    pin_mask = np.zeros(n_total, dtype=bool)
    pin_mask[:n_plate] = True
    # v6: fulcrum block + cheeks are pinned to the plate.
    pin_mask[n_plate + n_drop:n_plate + n_drop + n_fulcrum] = True

    def _build_no_jitter(alpha: float, contact_x: float) -> np.ndarray:
        """Assemble all grains without jitter; contact_x shifts the fulcrum."""
        insertion_x = muscle_end_x + alpha * L
        drop_x = drop_off + insertion_x
        dx, dy, dz = np.meshgrid(drop_x, drop_off, drop_z, indexing="ij")
        droplet_pos = np.stack([dx.ravel(), dy.ravel(), dz.ravel()], axis=1)

        load_z = np.arange(load_side, dtype=np.float64) * d + lever_top_z + d_eq
        load_x = load_off + load_end_x
        lx, ly2, lz2 = np.meshgrid(load_x, load_y, load_z, indexing="ij")
        load_pos = np.stack([lx.ravel(), ly2.ravel(), lz2.ravel()], axis=1)

        fx = f_off + contact_x
        fxg, fyg, fzg = np.meshgrid(fx, f_off, fulcrum_z, indexing="ij")
        block_pos = np.stack([fxg.ravel(), fyg.ravel(), fzg.ravel()],
                             axis=1)

        # Cheeks translate with the fulcrum block in x.
        cheek_pos_shifted = cheek_pos.copy()
        cheek_pos_shifted[:, 0] += contact_x

        pos = np.vstack([plate_pos, droplet_pos, block_pos,
                         cheek_pos_shifted, lever_pos, load_pos]).astype(np.float64)
        return pos

    # Jitter is generated once and reused for every alpha/contact probe so the
    # bisection sees the same cold print.
    tmp_pos = _build_no_jitter(0.5, 0.0)
    jitter = rng.normal(0.0, R_WALL * 0.01, size=tmp_pos.shape)

    def _assemble(alpha: float, contact_x: float) -> np.ndarray:
        pos = _build_no_jitter(alpha, contact_x)
        pos += jitter
        return pos

    def _R_for(alpha: float, contact_x: float) -> float:
        """Kernel R_true for a given alpha and fulcrum contact_x."""
        pos = _assemble(alpha, contact_x)
        cp = np.array([float(contact_x), 0.0, fulcrum_top_z], dtype=np.float64)
        R_true, _, _ = _R_true_at_print(pos, grain_ids, cp, pin_mask)
        return float(R_true)

    def _sample_R(alpha: float, n_samples: int = 401) -> tuple[np.ndarray, np.ndarray]:
        """Sample R_true across the off-edge fulcrum bracket."""
        cx_min = muscle_end_x + tube_half_width
        cx_max = load_end_x - tube_half_width
        margin = 2.0 * d
        lo = cx_min + margin
        hi = cx_max - margin
        xs = np.linspace(lo, hi, n_samples)
        Rs = np.array([_R_for(alpha, x) for x in xs])
        return xs, Rs

    # --- STAGE 1: bisect max_R_offedge(alpha) - 2.0 = 0 ---
    def _phi(alpha: float) -> float:
        _, Rs = _sample_R(alpha)
        return float(Rs.max()) - 2.0

    a_lo, a_hi = 0.0, 0.5
    f_lo, f_hi = _phi(a_lo), _phi(a_hi)
    if f_lo * f_hi > 0.0:
        raise RuntimeError(
            f"lever v6 stage-1 bracket [{a_lo}, {a_hi}] does not straddle "
            f"max_R_offedge=2.0 (phi={f_lo:.4f}..{f_hi:.4f}).")
    for _ in range(40):
        a_mid = 0.5 * (a_lo + a_hi)
        if _phi(a_mid) > 0.0:
            a_hi = a_mid
        else:
            a_lo = a_mid
    alpha_low = float(a_hi)
    print(f"[lever] v6 stage-1 alpha_low (max_R_offedge=2.0) = {alpha_low:.6f}")

    # --- STAGE 2: bisect weaker-arm deficit on [alpha_low, 0.12] ---
    def _contacts(alpha: float):
        """Return leftmost feasible (cx_main, R_main, cx_ctrl, R_ctrl)."""
        xs, Rs = _sample_R(alpha, n_samples=401)
        main_idx = np.flatnonzero(np.abs(Rs - 2.0) <= 0.1)
        if main_idx.size == 0:
            return None
        cx_main = float(xs[main_idx[0]])
        R_main = float(Rs[main_idx[0]])
        ctrl_idx = np.flatnonzero((Rs >= 0.5) & (Rs <= 1.05))
        if ctrl_idx.size == 0:
            return None
        cx_ctrl = float(xs[ctrl_idx[0]])
        R_ctrl = float(Rs[ctrl_idx[0]])
        return cx_main, R_main, cx_ctrl, R_ctrl

    def _psi(alpha: float) -> float:
        """Weaker-arm deficit: positive when control is not muscle-ward."""
        c = _contacts(alpha)
        if c is None:
            return 1.0
        cx_main, _, cx_ctrl, _ = c
        return float(cx_ctrl - cx_main)

    hi = 0.12
    if _psi(alpha_low) <= 0.0:
        alpha = alpha_low
    else:
        if _psi(hi) > 0.0:
            raise RuntimeError(
                "lever v6 weaker-arm deficit does not become negative on "
                f"[{alpha_low:.6f}, {hi}].")
        lo = alpha_low
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if _psi(mid) <= 0.0:
                hi = mid
            else:
                lo = mid
        alpha = float(hi)
    print(f"[lever] v6 stage-2 derived alpha = {alpha:.6f}")

    contacts = _contacts(alpha)
    if contacts is None:
        raise RuntimeError(
            f"lever v6 could not find feasible contacts at alpha={alpha:.6f}")
    cx_main, R_main, cx_ctrl, R_ctrl = contacts
    contact_x = float(cx_ctrl if control else cx_main)
    R_true_final = float(R_ctrl if control else R_main)

    # Final print positions at the derived alpha and contact point.
    pos = _assemble(alpha, contact_x)

    # Component positions after jitter.
    plate_pos_j = pos[:n_plate]
    droplet_pos_j = pos[n_plate:n_plate + n_drop]
    fulcrum_pos_j = pos[n_plate + n_drop:n_plate + n_drop + n_fulcrum]
    lever_pos_j = pos[n_plate + n_drop + n_fulcrum:
                      n_plate + n_drop + n_fulcrum + n_lever]
    load_pos_j = pos[n_plate + n_drop + n_fulcrum + n_lever:]

    # Print law: no two grains share a position.
    diff = pos[:, None, :] - pos[None, :, :]
    r2 = (diff * diff).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    min_pair_dist = float(np.sqrt(r2.min()))
    if min_pair_dist <= 1e-6:
        raise RuntimeError(
            f"lever v6 print law violated: minimum pair distance "
            f"{min_pair_dist} <= 1e-6 (control={control})")

    # Fixed indices from the cold print.
    lever_order = np.argsort(lever_pos_j[:, 0])
    face_count = n_ring
    muscle_face = lever_order[:face_count].astype(np.int32)
    load_face = lever_order[-face_count:].astype(np.int32)

    # The fulcrum top face is the original block top, not the cheeks, so the
    # cushion-contact test stays well-defined.  Cheeks are in the same fulcrum
    # grain id but at higher z and larger |y|; restricting to the block grains
    # (the first n_fulcrum_block points) is enough.
    block_pos_j = fulcrum_pos_j[:n_fulcrum_block]
    block_top_z = float(block_pos_j[:, 2].max())
    fulcrum_top_face = np.flatnonzero(np.isclose(block_pos_j[:, 2], block_top_z))

    lever_contact_local = np.flatnonzero(
        np.abs(lever_pos_j[:, 0] - contact_x) <= tube_half_width + 1e-9)

    muscle_c = lever_pos_j[muscle_face].mean(axis=0)
    load_c = lever_pos_j[load_face].mean(axis=0)
    a_m = float(contact_x - muscle_c[0])
    a_l = float(load_c[0] - contact_x)

    # Diagnostic pairwise draw magnitudes (static two-force estimate, not R_true).
    F_m = _downward_draw_magnitude(droplet_pos_j, lever_pos_j)
    W_L = _downward_draw_magnitude(plate_pos_j, load_pos_j)
    R_static = float(F_m * a_m / (W_L * a_l)) if W_L > 0.0 and a_l > 0.0 else 0.0

    R_true_check, tau_pos_final, tau_neg_final = _R_true_at_print(
        pos, grain_ids,
        np.array([float(contact_x), 0.0, fulcrum_top_z], dtype=np.float64),
        pin_mask)

    if control:
        if not (0.5 <= R_true_final <= 1.05):
            raise RuntimeError(
                f"lever v6 control print R_true={R_true_final:.3f} outside "
                f"[0.5, 1.05]")
        if not (a_m < (cx_main - muscle_c[0])):
            raise RuntimeError(
                "lever v6 control contact is not muscle-ward of main contact")
    else:
        if not (1.9 <= R_true_final <= 2.1):
            raise RuntimeError(
                f"lever v6 main print R_true={R_true_final:.3f} outside "
                f"[1.9, 2.1]")

    margin_to_load_end = float(load_end_x - contact_x)
    if margin_to_load_end < 2.0 * d:
        raise RuntimeError(
            f"lever v6 contact too close to load end: margin="
            f"{margin_to_load_end:.4f} < {2.0*d:.4f}")

    fulcrum_contact_point = np.array([float(contact_x), 0.0, fulcrum_top_z],
                                     dtype=np.float64)

    derived = {
        "control": bool(control),
        "route": "standard",
        "droplet_side": drop_side,
        "d_eq": d_eq,
        "spacing": d,
        "lever_len": length,
        "n_plate": n_plate,
        "n_droplet": n_drop,
        "n_fulcrum": n_fulcrum,
        "n_cheek": n_cheek,
        "n_lever": n_lever,
        "n_load": n_load,
        "alpha": float(alpha),
        "alpha_method": "bisection",
        "fulcrum_contact_point": fulcrum_contact_point,
        "muscle_face": muscle_face,
        "load_face": load_face,
        "fulcrum_top_face": fulcrum_top_face,
        "lever_contact_local": lever_contact_local,
        "a_m": a_m,
        "a_l": a_l,
        "F_m": F_m,
        "W_L": W_L,
        "R_static": R_static,
        "R_true": float(R_true_final),
        "tau_pos": float(tau_pos_final),
        "tau_neg": float(tau_neg_final),
        "margin_to_load_end": margin_to_load_end,
        "plate_pos0": plate_pos_j.copy(),
        "load_end_z0": float(load_c[2]),
    }

    return pos.astype(np.float32), np.zeros_like(pos, dtype=np.float32), \
        pin_mask, grain_ids, derived


def leg(control: bool = False,
        spacing: float = 0.05,
        seed: int = 0,
        drop_side: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                               np.ndarray, dict]:
    """
    THE LEG v3 print: anchored droplet, single-file rope tendon, full-arc gate.

    v2 failed because the tendon was a rigid rod that props the arm-tip away
    from the droplet; the rod could transmit compression, so it acted as a
    strut and the machine settled against it.  v3 replaces the rod with a
    single-file rope chain from the anchored droplet apex to the arm-tip
    underside.  A rope can pull but not push; when the muscle wins it stays
    taut, and when it goes slack it must crumple into the well rather than
    prop the lever.

    The FULL-ARC gate prices the kernel static torque ratio R_true(theta) on
    the whole reachable interval [-theta_load, +theta_muscle], not just the
    muscle side.  The main print demands min_R_taut >= 1 everywhere, so the
    muscle-side stop is the unique attractor.  The control print demands
    R_slack(0) in [0.5, 1.0] and max_R_slack <= 1 everywhere, so the load
    side can descend.

    If the strict gate cannot be satisfied, the derived knob is the droplet
    side {4,5,6} (muscle strength).  If still no contact passes, the builder
    records the failure honestly and falls back to a best-effort contact so
    that dynamics can still be run for the falsifier.

    Grain ids:
      - plate   = -1 (pinned)
      - droplet = 0  (anchored muscle, pinned)
      - fulcrum = 1  (pinned block + cheeks)
      - lever   = 2  (13-ring 4x4 hollow tube)
      - load    = 3  (free)
      - rope    = 4  (single-file tendon chain, free)

    Returns ``(positions, velocities, pin_mask, grain_ids, derived)``.
    """
    rng = np.random.default_rng(seed)
    d = float(spacing)
    d_eq = TENDON_D_EQ

    # --- Shared geometry constants ---
    plate_nx, plate_ny = 18, 6
    fulcrum_side = 4
    length = 13
    s = 4
    load_side = 4
    margin = 0.10
    theta_max = math.radians(120.0)

    muscle_tip_x = float(-(length - 1) / 2.0 * d)
    load_end_x = float((length - 1) / 2.0 * d)
    muscle_end_x = muscle_tip_x
    tube_half_width = (s - 1) / 2.0 * d

    # --- Pinned ground plate + well ---
    n_plate_flat = plate_nx * plate_ny
    px_off = (np.arange(plate_nx, dtype=np.float64)
              - (plate_nx - 1) / 2.0) * d
    py_off = (np.arange(plate_ny, dtype=np.float64)
              - (plate_ny - 1) / 2.0) * d
    pxg, pyg = np.meshgrid(px_off, py_off, indexing="ij")
    plate_flat = np.stack([pxg.ravel(), pyg.ravel(),
                           np.zeros(n_plate_flat, dtype=np.float64)], axis=1)
    hole = ((np.abs(plate_flat[:, 0] - muscle_tip_x) <= 0.15 + 1e-9) &
            (np.abs(plate_flat[:, 1]) <= 0.15 + 1e-9))
    plate_flat = plate_flat[~hole]

    well_nx, well_ny, well_nz = 6, 6, 5
    wx_off = muscle_tip_x + (np.arange(well_nx, dtype=np.float64)
                             - (well_nx - 1) / 2.0) * d
    wy_off = (np.arange(well_ny, dtype=np.float64)
              - (well_ny - 1) / 2.0) * d

    def _make_well(well_floor_z: float) -> np.ndarray:
        wz_off = np.arange(well_nz, dtype=np.float64) * d + well_floor_z
        wxg, wyg, wzg = np.meshgrid(wx_off, wy_off, wz_off, indexing="ij")
        well_box = np.stack([wxg.ravel(), wyg.ravel(), wzg.ravel()], axis=1)
        in_cavity_xy = ((np.abs(well_box[:, 0] - muscle_tip_x) <= 0.075 + 1e-9) &
                        (np.abs(well_box[:, 1]) <= 0.075 + 1e-9))
        is_bottom = np.isclose(well_box[:, 2], well_floor_z)
        cavity = in_cavity_xy & (~is_bottom)
        return well_box[~cavity]

    # --- Fulcrum block + cheeks (v6) ---
    n_fulcrum_block = fulcrum_side ** 3
    f_off = (np.arange(fulcrum_side, dtype=np.float64)
             - (fulcrum_side - 1) / 2.0) * d
    fulcrum_z = np.arange(fulcrum_side, dtype=np.float64) * d + d_eq
    fulcrum_top_z = d_eq + (fulcrum_side - 1) * d
    fulcrum_half_width = (fulcrum_side - 1) / 2.0 * d

    cheek_y_center = 0.10 + d_eq + d / 2.0
    n_cheek_z = 3
    cheek_x = f_off
    cheek_z = np.arange(n_cheek_z, dtype=np.float64) * d + fulcrum_top_z
    cxg, cyg, czg = np.meshgrid(
        cheek_x, np.array([cheek_y_center]), cheek_z, indexing="ij")
    cheek_pos_plus = np.stack([cxg.ravel(), cyg.ravel(), czg.ravel()], axis=1)
    cheek_pos_minus = cheek_pos_plus.copy()
    cheek_pos_minus[:, 1] = -cheek_y_center
    cheek_pos = np.vstack([cheek_pos_plus, cheek_pos_minus])
    n_cheek = cheek_pos.shape[0]

    # --- Lever: v6 13-ring 4x4 hollow tube ---
    x_off = (np.arange(length, dtype=np.float64)
             - (length - 1) / 2.0) * d
    yz_off = (np.arange(s, dtype=np.float64)
              - (s - 1) / 2.0) * d
    gy, gz = np.meshgrid(yz_off, yz_off, indexing="ij")
    inner = (np.abs(gy) <= 0.5 * d + 1e-12) & (np.abs(gz) <= 0.5 * d + 1e-12)
    shell = ~inner
    y_shell = gy[shell]
    z_shell = gz[shell]
    n_ring = int(y_shell.size)
    x_all = np.repeat(x_off, n_ring)
    y_all = np.tile(y_shell, length)
    z_all = np.tile(z_shell, length)
    lever_pos_template = np.stack([x_all, y_all, z_all], axis=1)
    n_lever = lever_pos_template.shape[0]

    lever_bottom_z = fulcrum_top_z + d_eq
    lever_top_z = lever_bottom_z + (fulcrum_side - 1) * d
    lever_pos_template[:, 2] += lever_bottom_z + fulcrum_half_width

    # --- Load block ---
    n_load = load_side ** 3
    load_off = f_off
    load_y = f_off
    load_z = np.arange(load_side, dtype=np.float64) * d + lever_top_z + d_eq

    # --- Helper: assemble full cold pose without jitter ---
    def _build_no_jitter(contact_x: float, well_floor_z: float,
                         drop_side_i: int) -> np.ndarray:
        """Assemble all grains without jitter."""
        # plate + well
        plate_pos = np.vstack([plate_flat, _make_well(well_floor_z)])

        # droplet (anchored, seated on well floor)
        drop_off_i = (np.arange(drop_side_i, dtype=np.float64)
                      - (drop_side_i - 1) / 2.0) * d
        drop_x = drop_off_i + muscle_tip_x
        drop_z = np.arange(drop_side_i, dtype=np.float64) * d + well_floor_z + d_eq
        dx, dy, dz = np.meshgrid(drop_x, drop_off_i, drop_z, indexing="ij")
        droplet_pos = np.stack([dx.ravel(), dy.ravel(), dz.ravel()], axis=1)

        # fulcrum block + cheeks
        fx = f_off + contact_x
        fxg, fyg, fzg = np.meshgrid(fx, f_off, fulcrum_z, indexing="ij")
        block_pos = np.stack([fxg.ravel(), fyg.ravel(), fzg.ravel()], axis=1)
        cheek_pos_shifted = cheek_pos.copy()
        cheek_pos_shifted[:, 0] += contact_x
        fulcrum_pos = np.vstack([block_pos, cheek_pos_shifted])

        # load
        load_x = load_off + load_end_x
        lx, ly2, lz2 = np.meshgrid(load_x, load_y, load_z, indexing="ij")
        load_pos = np.stack([lx.ravel(), ly2.ravel(), lz2.ravel()], axis=1)

        # rope: single-file chain from droplet apex (+d_eq) to arm-tip underside (-d_eq)
        droplet_apex = well_floor_z + d_eq + (drop_side_i - 1) * d
        anchor_z = droplet_apex + d_eq
        attach_z = lever_bottom_z - d_eq
        span = attach_z - anchor_z
        n_chain = max(1, int(np.floor(span / d)) + 1)
        chain_z = np.linspace(anchor_z, attach_z, n_chain)
        chain_pos = np.column_stack([
            np.full(n_chain, muscle_tip_x, dtype=np.float64),
            np.zeros(n_chain, dtype=np.float64),
            chain_z,
        ])

        return np.vstack([
            plate_pos, droplet_pos, fulcrum_pos, lever_pos_template,
            load_pos, chain_pos,
        ]).astype(np.float64)

    # --- Grain ids / pin mask depend on well_floor_z and drop_side ---
    def _make_masks(well_floor_z: float, drop_side_i: int):
        droplet_apex = well_floor_z + d_eq + (drop_side_i - 1) * d
        anchor_z = droplet_apex + d_eq
        attach_z = lever_bottom_z - d_eq
        span = attach_z - anchor_z
        n_chain = max(1, int(np.floor(span / d)) + 1)

        plate_pos = np.vstack([plate_flat, _make_well(well_floor_z)])
        n_plate = plate_pos.shape[0]
        n_drop = drop_side_i ** 3
        n_fulcrum = n_fulcrum_block + n_cheek

        n_total = n_plate + n_drop + n_fulcrum + n_lever + n_load + n_chain
        grain_ids = np.empty(n_total, dtype=np.int32)
        grain_ids[:n_plate] = -1
        grain_ids[n_plate:n_plate + n_drop] = 0
        grain_ids[n_plate + n_drop:n_plate + n_drop + n_fulcrum] = 1
        grain_ids[n_plate + n_drop + n_fulcrum:
                  n_plate + n_drop + n_fulcrum + n_lever] = 2
        grain_ids[n_plate + n_drop + n_fulcrum + n_lever:
                  n_plate + n_drop + n_fulcrum + n_lever + n_load] = 3
        grain_ids[n_plate + n_drop + n_fulcrum + n_lever + n_load:] = 4

        pin_mask = np.zeros(n_total, dtype=bool)
        pin_mask[:n_plate] = True
        pin_mask[n_plate:n_plate + n_drop] = True  # anchored droplet
        pin_mask[n_plate + n_drop:n_plate + n_drop + n_fulcrum] = True
        return grain_ids, pin_mask, n_plate, n_drop, n_fulcrum, n_chain

    # --- Minimum tip-to-droplet distance over the muscle-side arc ---
    def _min_arc_distance(contact_x: float, well_floor_z: float,
                          drop_side_i: int, n_theta: int = 21) -> tuple[float, float]:
        pos = _build_no_jitter(contact_x, well_floor_z, drop_side_i)
        grain_ids_m, pin_mask_m, n_plate, n_drop, n_fulcrum, n_chain = \
            _make_masks(well_floor_z, drop_side_i)
        theta_stop = _derive_theta_muscle(contact_x, well_floor_z, drop_side_i)

        lever_idx = np.arange(n_plate + n_drop + n_fulcrum,
                              n_plate + n_drop + n_fulcrum + n_lever)
        drop_idx = np.arange(n_plate, n_plate + n_drop)

        lever_x = pos[lever_idx, 0]
        tip_local = lever_idx[lever_x <= muscle_tip_x + 1e-9]
        tip_grains = pos[tip_local].astype(np.float64)
        drop_grains = pos[drop_idx].astype(np.float64)

        cp = np.array([float(contact_x), 0.0, fulcrum_top_z], dtype=np.float64)
        rel_tip = tip_grains - cp[None, :]
        rel_drop = drop_grains - cp[None, :]

        thetas = np.linspace(0.0, theta_stop, n_theta)
        min_dist = float("inf")
        for theta in thetas:
            c = math.cos(theta)
            s = math.sin(theta)
            rot = rel_tip.copy()
            rot[:, 0] = rel_tip[:, 0] * c - rel_tip[:, 2] * s
            rot[:, 2] = rel_tip[:, 0] * s + rel_tip[:, 2] * c
            dpos = rot[:, None, :] - rel_drop[None, :, :]
            r2 = (dpos * dpos).sum(axis=2)
            min_dist = min(min_dist, float(np.sqrt(r2.min())))
        return theta_stop, min_dist

    # --- Derive muscle-side stop (arm-tip underside reaches droplet apex + d_eq) ---
    def _derive_theta_muscle(contact_x: float, well_floor_z: float,
                             drop_side_i: int) -> float:
        droplet_apex = well_floor_z + d_eq + (drop_side_i - 1) * d
        target = droplet_apex + d_eq
        rel_x = muscle_tip_x - contact_x
        rel_z = lever_bottom_z - fulcrum_top_z  # = d_eq

        def z_tip(theta: float) -> float:
            return fulcrum_top_z + rel_x * math.sin(theta) + rel_z * math.cos(theta)

        if z_tip(theta_max) > target:
            return theta_max
        lo, hi = 0.0, theta_max
        for _ in range(50):
            mid = (lo + hi) / 2.0
            if z_tip(mid) > target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2.0

    # --- Derive load-side stop (load bottom reaches ground + d_eq) ---
    def _derive_theta_load(contact_x: float) -> float:
        load_bottom_z0 = load_z.min()
        target = d_eq
        rel_x = load_end_x - contact_x
        rel_z = load_bottom_z0 - fulcrum_top_z

        def z_load(theta: float) -> float:
            return fulcrum_top_z + rel_x * math.sin(theta) + rel_z * math.cos(theta)

        if z_load(-theta_max) < target:
            return -theta_max
        lo, hi = -theta_max, 0.0
        for _ in range(50):
            mid = (lo + hi) / 2.0
            if z_load(mid) < target:
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2.0

    # --- Derive well_floor_z by bisection (clear arm-tip arc from droplet) ---
    def _derive_well_floor(contact_x_for_depth: float, drop_side_i: int) -> float:
        lo = -10.0 * d
        hi = -2.0 * d
        _, d_lo = _min_arc_distance(contact_x_for_depth, lo, drop_side_i)
        _, d_hi = _min_arc_distance(contact_x_for_depth, hi, drop_side_i)
        if d_hi >= d_eq:
            return hi
        if d_lo < d_eq:
            raise RuntimeError(
                f"leg v3 well depth bisection failed: even well_floor_z={lo} "
                f"gives min arc distance {d_lo:.4f} < d_eq={d_eq:.4f}")
        for _ in range(30):
            mid = (lo + hi) / 2.0
            _, d_mid = _min_arc_distance(contact_x_for_depth, mid, drop_side_i)
            if d_mid >= d_eq:
                lo = mid
            else:
                hi = mid
        return lo

    # --- Full-arc gate: R_true(theta) for taut and slack rope ---
    def _full_arc_R_true(contact_x: float, well_floor_z: float, drop_side_i: int,
                         n_theta: int = 25) -> dict:
        pos0 = _build_no_jitter(contact_x, well_floor_z, drop_side_i)
        grain_ids_m, pin_mask_m, n_plate, n_drop, n_fulcrum, n_chain = \
            _make_masks(well_floor_z, drop_side_i)
        theta_muscle = _derive_theta_muscle(contact_x, well_floor_z, drop_side_i)
        theta_load = _derive_theta_load(contact_x)
        thetas = np.linspace(theta_load, theta_muscle, n_theta)
        cp = np.array([float(contact_x), 0.0, fulcrum_top_z], dtype=np.float64)

        plate_end = n_plate
        drop_end = plate_end + n_drop
        fulcrum_end = drop_end + n_fulcrum
        lever_end = fulcrum_end + n_lever
        load_end = lever_end + n_load

        lever_idx = np.arange(fulcrum_end, lever_end)
        load_idx = np.arange(lever_end, load_end)
        rope_idx = np.arange(load_end, pos0.shape[0])

        droplet_apex = well_floor_z + d_eq + (drop_side_i - 1) * d
        anchor = np.array([float(muscle_tip_x), 0.0,
                           float(droplet_apex + d_eq)], dtype=np.float64)

        R_taut = np.empty(n_theta, dtype=np.float64)
        R_slack = np.empty(n_theta, dtype=np.float64)

        for i, theta in enumerate(thetas):
            pos = pos0.copy()
            c = math.cos(theta)
            s = math.sin(theta)

            # rotate lever+load about cp
            for idx in (lever_idx, load_idx):
                rel = pos[idx] - cp[None, :]
                rot = rel.copy()
                rot[:, 0] = rel[:, 0] * c - rel[:, 2] * s
                rot[:, 2] = rel[:, 0] * s + rel[:, 2] * c
                pos[idx] = rot + cp[None, :]

            # arm-tip underside attachment point
            rel_attach = np.array([float(muscle_tip_x - contact_x), 0.0,
                                   float(lever_bottom_z - d_eq - fulcrum_top_z)])
            attach = np.array([
                cp[0] + rel_attach[0] * c - rel_attach[2] * s,
                0.0,
                cp[2] + rel_attach[0] * s + rel_attach[2] * c,
            ], dtype=np.float64)

            # TAUT: place rope grains along anchor->attach
            if n_chain >= 2:
                axis = attach - anchor
                L_rope = float(np.linalg.norm(axis))
                if L_rope < 1e-9:
                    L_rope = 1e-9
                for li in range(n_chain):
                    t = li / (n_chain - 1.0)
                    pos[rope_idx[li]] = anchor + t * axis
            else:
                # single grain sits at anchor
                pos[rope_idx[0]] = anchor.copy()

            R_taut[i], _, _ = _R_true_at_print(pos, grain_ids_m, cp, pin_mask_m)

            # SLACK: rope grains moved far away so they transmit no pull
            pos_slack = pos.copy()
            pos_slack[rope_idx] = np.array([0.0, 0.0, 1e6], dtype=np.float64)
            R_slack[i], _, _ = _R_true_at_print(pos_slack, grain_ids_m, cp, pin_mask_m)

        return {
            "theta_load": theta_load,
            "theta_muscle": theta_muscle,
            "thetas": thetas,
            "R_taut": R_taut,
            "R_slack": R_slack,
        }

    # --- Scan contact_x and droplet size for strict gate ---
    cx_min = muscle_end_x + tube_half_width
    cx_max = load_end_x - margin
    n_contact = 201
    xs = np.linspace(cx_min, cx_max, n_contact)

    # Droplet-size knob; explicit value bypasses the knob.
    all_drop_sizes = [4, 5, 6]
    drop_sizes = [drop_side] if drop_side is not None else all_drop_sizes

    # Pre-derive well depth for each drop size using rightmost contact (largest arc).
    well_floor_by_drop = {}
    for ds in drop_sizes:
        well_floor_by_drop[ds] = _derive_well_floor(cx_max, ds)
    # Also derive for the full knob set so best-effort can compare honestly.
    for ds in all_drop_sizes:
        if ds not in well_floor_by_drop:
            well_floor_by_drop[ds] = _derive_well_floor(cx_max, ds)

    def _strict_main_ok(trace: dict) -> bool:
        return float(np.min(trace["R_taut"])) >= 1.0

    def _strict_control_ok(trace: dict) -> bool:
        R0 = float(trace["R_slack"][0])
        return (0.5 <= R0 <= 1.0) and float(np.max(trace["R_slack"])) <= 1.0

    strict_ok = False
    chosen_drop = None
    chosen_cx = None
    chosen_trace = None
    chosen_route = None

    for ds in drop_sizes:
        wfz = well_floor_by_drop[ds]
        for i, cx in enumerate(xs):
            trace = _full_arc_R_true(cx, wfz, ds)
            if control:
                if _strict_control_ok(trace):
                    strict_ok = True
                    chosen_drop = ds
                    chosen_cx = float(cx)
                    chosen_trace = trace
                    chosen_route = "full-arc"
                    break
            else:
                if _strict_main_ok(trace):
                    strict_ok = True
                    chosen_drop = ds
                    chosen_cx = float(cx)
                    chosen_trace = trace
                    chosen_route = "full-arc"
                    break
        if strict_ok:
            break

    # If strict gate failed, choose the least-bad contact honestly.
    # The search space is the full knob set unless the caller pinned a size.
    if not strict_ok:
        search_sizes = all_drop_sizes if drop_side is None else [drop_side]
        best_candidates = []
        for ds in search_sizes:
            wfz = well_floor_by_drop[ds]
            # Rope must be long enough to transmit tension; otherwise it is a prop.
            droplet_apex_i = wfz + d_eq + (ds - 1) * d
            span_i = lever_bottom_z - droplet_apex_i - 2.0 * d_eq
            n_chain_i = max(1, int(np.floor(span_i / d)) + 1)
            if n_chain_i < 2:
                # Cannot pull; skip this droplet size.
                continue
            traces = [_full_arc_R_true(cx, wfz, ds) for cx in xs]
            if control:
                costs = []
                for tr in traces:
                    R0 = float(tr["R_slack"][0])
                    Rmax = float(np.max(tr["R_slack"]))
                    theta_m = float(tr["theta_muscle"])
                    cost = abs(R0 - 0.75)
                    if Rmax > 1.0:
                        cost += (Rmax - 1.0) * 10.0
                    if R0 < 0.5:
                        cost += (0.5 - R0) * 5.0
                    if theta_m < math.radians(5.0):
                        cost += 10.0
                    costs.append(cost)
            else:
                costs = []
                for tr in traces:
                    Rmin = float(np.min(tr["R_taut"]))
                    theta_m = float(tr["theta_muscle"])
                    cost = 1.0 - min(1.0, Rmin)
                    if theta_m < math.radians(5.0):
                        cost += 10.0
                    costs.append(cost)
            best_i = int(np.argmin(costs))
            best_candidates.append((costs[best_i], ds, xs[best_i], traces[best_i], wfz))

        if not best_candidates:
            # Last resort: ignore tension-length filter and take the least-bad.
            for ds in search_sizes:
                wfz = well_floor_by_drop[ds]
                traces = [_full_arc_R_true(cx, wfz, ds) for cx in xs]
                if control:
                    costs = []
                    for tr in traces:
                        R0 = float(tr["R_slack"][0])
                        Rmax = float(np.max(tr["R_slack"]))
                        cost = abs(R0 - 0.75)
                        if Rmax > 1.0:
                            cost += (Rmax - 1.0) * 10.0
                        if R0 < 0.5:
                            cost += (0.5 - R0) * 5.0
                        costs.append(cost)
                else:
                    costs = [1.0 - min(1.0, float(np.min(tr["R_taut"]))) for tr in traces]
                best_i = int(np.argmin(costs))
                best_candidates.append((costs[best_i], ds, xs[best_i], traces[best_i], wfz))

        best = min(best_candidates, key=lambda x: x[0])
        chosen_drop = int(best[1])
        chosen_cx = float(best[2])
        chosen_trace = best[3]
        chosen_route = "best-effort"

    if chosen_drop is None:
        # Should not happen because best-effort always produces a candidate.
        raise RuntimeError("leg v3 gate failed and best-effort fallback also failed.")

    drop_side = chosen_drop
    contact_x = chosen_cx
    trace_final = chosen_trace
    well_floor_z = well_floor_by_drop[drop_side]

    # Final masks and base arrays.
    grain_ids, pin_mask, n_plate, n_drop, n_fulcrum, n_chain = \
        _make_masks(well_floor_z, drop_side)
    droplet_apex = well_floor_z + d_eq + (drop_side - 1) * d

    # Jitter sized to the fixed geometry.
    tmp_pos = _build_no_jitter(contact_x, well_floor_z, drop_side)
    jitter = rng.normal(0.0, R_WALL * 0.01, size=tmp_pos.shape)

    def _assemble(contact_x_a: float) -> np.ndarray:
        pos = _build_no_jitter(contact_x_a, well_floor_z, drop_side)
        pos += jitter
        return pos

    pos = _assemble(contact_x)

    # --- Component positions after jitter ---
    plate_pos_j = pos[:n_plate]
    droplet_pos_j = pos[n_plate:n_plate + n_drop]
    fulcrum_pos_j = pos[n_plate + n_drop:n_plate + n_drop + n_fulcrum]
    lever_pos_j = pos[n_plate + n_drop + n_fulcrum:
                      n_plate + n_drop + n_fulcrum + n_lever]
    load_pos_j = pos[n_plate + n_drop + n_fulcrum + n_lever:
                     n_plate + n_drop + n_fulcrum + n_lever + n_load]
    rope_pos_j = pos[n_plate + n_drop + n_fulcrum + n_lever + n_load:]

    # --- Print law ---
    diff = pos[:, None, :] - pos[None, :, :]
    r2 = (diff * diff).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    min_pair_dist = float(np.sqrt(r2.min()))
    if min_pair_dist <= 1e-6:
        raise RuntimeError(
            f"leg v3 print law violated: minimum pair distance {min_pair_dist} "
            f"<= 1e-6 (control={control})")

    # --- Fixed indices and derived quantities ---
    lever_order = np.argsort(lever_pos_j[:, 0])
    muscle_face = lever_order[:n_ring].astype(np.int32)
    load_face = lever_order[-n_ring:].astype(np.int32)

    block_pos_j = fulcrum_pos_j[:n_fulcrum_block]
    block_top_z = float(block_pos_j[:, 2].max())
    fulcrum_top_face = np.flatnonzero(np.isclose(block_pos_j[:, 2], block_top_z))

    lever_contact_local = np.flatnonzero(
        np.abs(lever_pos_j[:, 0] - contact_x) <= tube_half_width + 1e-9)

    muscle_c = lever_pos_j[muscle_face].mean(axis=0)
    load_c = lever_pos_j[load_face].mean(axis=0)
    a_m = float(contact_x - muscle_c[0])
    a_l = float(load_c[0] - contact_x)

    # Rope chain indices ordered from bottom (droplet side) to top (lever side)
    rope_order = np.argsort(rope_pos_j[:, 2])
    rope_bottom = rope_order[:1].astype(np.int32)
    rope_top = rope_order[-1:].astype(np.int32)
    rope_chain = rope_order.astype(np.int32)

    fulcrum_contact_point = np.array([float(contact_x), 0.0, fulcrum_top_z],
                                     dtype=np.float64)

    R_true_final = float(trace_final["R_taut"][0] if not control
                         else trace_final["R_slack"][0])

    if chosen_route == "full-arc":
        if control:
            if not (0.5 <= R_true_final <= 1.0):
                raise RuntimeError(
                    f"leg v3 control print R_true={R_true_final:.3f} outside [0.5, 1.0]")
        else:
            if R_true_final < 1.0:
                raise RuntimeError(
                    f"leg v3 main print cold R_true={R_true_final:.3f} < 1.0")

    margin_to_load_end = float(load_end_x - contact_x)
    if margin_to_load_end < margin:
        raise RuntimeError(
            f"leg v3 contact too close to load end: margin="
            f"{margin_to_load_end:.4f} < {margin:.4f}")

    theta_stop_muscle = float(trace_final["theta_muscle"])
    theta_stop_load = float(trace_final["theta_load"])

    derived = {
        "control": bool(control),
        "route": chosen_route,
        "droplet_side": drop_side,
        "d_eq": d_eq,
        "spacing": d,
        "lever_len": length,
        "n_plate": n_plate,
        "n_droplet": n_drop,
        "n_fulcrum": n_fulcrum,
        "n_cheek": n_cheek,
        "n_lever": n_lever,
        "n_load": n_load,
        "n_rope": n_chain,
        "well_floor_z": well_floor_z,
        "droplet_apex": droplet_apex,
        "muscle_tip_x": muscle_tip_x,
        "fulcrum_contact_point": fulcrum_contact_point,
        "muscle_face": muscle_face,
        "load_face": load_face,
        "fulcrum_top_face": fulcrum_top_face,
        "lever_contact_local": lever_contact_local,
        "rope_bottom": rope_bottom,
        "rope_top": rope_top,
        "rope_chain": rope_chain,
        "a_m": a_m,
        "a_l": a_l,
        "R_true": float(R_true_final),
        "theta_stop_muscle": theta_stop_muscle,
        "theta_stop_load": theta_stop_load,
        "arc_trace": trace_final,
        "margin_to_load_end": margin_to_load_end,
        "plate_pos0": plate_pos_j.copy(),
        "load_end_z0": float(load_c[2]),
        "gate_passed": strict_ok,
    }

    return pos.astype(np.float32), np.zeros_like(pos, dtype=np.float32), \
        pin_mask, grain_ids, derived


def bladder(seed: int = 0,
            fill: str = "gap",
            neck: str = "narrow") -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                            np.ndarray, float, dict]:
    """
    THE BLADDER print: a closed spherical shell (grain_id=1) packed with a
    condensed content droplet (grain_id=2), squeezed by two pinned 4x4 muscle
    plates, with one derived neck opening.

    The shell is one grain thick at cushion equilibrium spacing d_eq = 0.0484
    on a sphere of radius r_b = 0.20 lu.  Its point count is derived from the
    sphere's surface area divided by the shell spacing squared.

    ``fill="gap"`` (v1): the contents are a 4^3 droplet at the muscle's 0.05
    lattice step, centered inside the shell — this leaves a gap and the shell
    crumples.

    ``fill="fill"`` (v2): the contents are derived to fill the shell interior at
    cushion contact.  A cubic lattice at muscle spacing is carved to fit inside
    radius ``r_in = r_b - d_eq``; the outermost content grains sit ~d_eq from the
    shell wall, providing the cushion splint that holds the wall at print.

    ``neck="narrow"`` (v1/v2): a hole of diameter 2*d_eq at the +z pole, the
    smallest opening that passes one grain.

    ``neck="antijam"`` (v3): the neck is derived from granular arching.  An arch
    needs at least 2 grains abreast to span (2 spacings) and is stable up to 3
    spacings, so the opening is set to 4 spacings — the smallest hole no cushion
    arch can close.  The neck is centered on the +x point of the sphere, facing
    the right squeeze plate, so the pressure gradient points through it:

        neck_diameter = 4 * muscle_spacing = 0.20 lu
        neck_center   = (center_x + r_b, 0, 0)
        neck_axis     = (+1, 0, 0)

    The plates are the muscle's pinned 4x4 anchors, placed so each plate face
    sits at cushion distance d_eq from the shell surface:

        s0 = 2 * (r_b + d_eq)

    Returns ``(positions, velocities, pin_mask, grain_ids, s0, derived)``:
      - ``positions`` / ``velocities`` are float32 (N, 3) arrays.
      - ``pin_mask`` is length-N bool; only the two plates are pinned.
      - ``grain_ids`` is length-N int32; plates=-1, shell=1, contents=2.
      - ``derived`` carries r_b, d_eq, n_shell, n_content, fill mode, neck
        mode, neck_diameter, neck geometry, center_x, and F_hold (the derived
        hold force from the kernel at print).
    """
    if fill not in ("gap", "fill"):
        raise ValueError("fill must be 'gap' or 'fill'")
    if neck not in ("narrow", "antijam"):
        raise ValueError("neck must be 'narrow' or 'antijam'")

    rng = np.random.default_rng(seed)
    muscle_spacing = 0.05
    d_eq = TENDON_D_EQ
    r_b = 0.20

    # Muscle anchor plates: 4x4, pinned, perpendicular to x.
    side = 4
    n_plate = side * side
    offsets = (np.arange(side, dtype=np.float64) - (side - 1) / 2.0) * muscle_spacing
    py, pz = np.meshgrid(offsets, offsets, indexing="ij")
    plate_yz = np.stack([py.ravel(), pz.ravel()], axis=1)

    s0 = 2.0 * (r_b + d_eq)
    center_x = s0 / 2.0

    left_plate = np.hstack([np.zeros((n_plate, 1)), plate_yz])
    right_plate = np.hstack([np.full((n_plate, 1), s0), plate_yz])

    # Spherical shell: count derived from surface area / shell spacing^2.
    shell_area = 4.0 * math.pi * r_b * r_b
    n_shell_target = int(round(shell_area / (d_eq * d_eq)))
    n_shell_target = max(4, n_shell_target)

    # Deterministic Fibonacci sphere on the r_b sphere, z-axis as pole.
    indices = np.arange(n_shell_target, dtype=np.float64)
    cos_phi = 1.0 - 2.0 * indices / (n_shell_target - 1)
    sin_phi = np.sqrt(np.maximum(1.0 - cos_phi * cos_phi, 0.0))
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    theta = golden_angle * indices
    sx = sin_phi * np.cos(theta)
    sy = sin_phi * np.sin(theta)
    sz = cos_phi
    shell_pos = r_b * np.stack([sx, sy, sz], axis=1)
    shell_pos[:, 0] += center_x

    # Neck geometry: derived from the requested neck mode.
    if neck == "narrow":
        # v1/v2: one-grain hole at the +z pole, diameter 2*d_eq.
        neck_radius = d_eq
        neck_diameter = 2.0 * d_eq
        neck_center = np.array([center_x, 0.0, r_b], dtype=np.float64)
        neck_axis = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    else:
        # v3: anti-jam hole on the squeeze axis, diameter = 4 lattice spacings.
        # Arching over an orifice: an arch needs >= 2 grains abreast to span
        # (2 spacings), stable arches form up to 3 spacings, so the opening is
        # 4 spacings — the smallest hole no cushion arch can close.
        neck_radius = 2.0 * muscle_spacing
        neck_diameter = 4.0 * muscle_spacing
        neck_center = np.array([center_x + r_b, 0.0, 0.0], dtype=np.float64)
        neck_axis = np.array([1.0, 0.0, 0.0], dtype=np.float64)

    dist_to_neck = np.linalg.norm(shell_pos - neck_center, axis=1)
    shell_pos = shell_pos[dist_to_neck > neck_radius]
    n_shell = shell_pos.shape[0]

    # Contents.
    if fill == "gap":
        # v1: 4^3 simple-cubic droplet at muscle spacing, centered.
        n_content = side ** 3
        offsets_c = (np.arange(side, dtype=np.float64) - (side - 1) / 2.0) * muscle_spacing
        gx, gy, gz = np.meshgrid(offsets_c, offsets_c, offsets_c, indexing="ij")
        content_pos = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)
        content_pos[:, 0] += center_x
    else:
        # v2: fill the interior up to r_in = r_b - d_eq at muscle spacing.
        r_in = r_b - d_eq
        n_grid = max(1, int(math.ceil(r_in / muscle_spacing)))
        grid_idx = np.arange(-n_grid, n_grid + 1)
        gx, gy, gz = np.meshgrid(grid_idx, grid_idx, grid_idx, indexing="ij")
        cand = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1) * muscle_spacing
        # keep points inside the interior sphere
        keep = np.linalg.norm(cand, axis=1) <= r_in + 1e-9
        content_pos = cand[keep].copy()
        content_pos[:, 0] += center_x
        n_content = content_pos.shape[0]

    # Assemble: plates first, then shell, then contents.
    pos = np.vstack([left_plate, right_plate, shell_pos, content_pos]).astype(np.float64)
    vel = np.zeros_like(pos)

    pin_mask = np.zeros(pos.shape[0], dtype=bool)
    pin_mask[:n_plate] = True
    pin_mask[n_plate:2 * n_plate] = True

    grain_ids = np.empty(pos.shape[0], dtype=np.int32)
    grain_ids[:n_plate] = -1
    grain_ids[n_plate:2 * n_plate] = -1
    grain_ids[2 * n_plate:2 * n_plate + n_shell] = 1
    grain_ids[2 * n_plate + n_shell:] = 2

    # Tiny deterministic jitter to break exact degeneracies (<< R_WALL).
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pos.shape)
    pos += jitter

    # Print law: no two grains occupy the same position across the assembly.
    diff = pos[:, None, :] - pos[None, :, :]
    r2 = (diff * diff).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    min_pair_dist = float(np.sqrt(r2.min()))
    if min_pair_dist <= 1e-6:
        raise RuntimeError(
            f"bladder print law violated: minimum pair distance {min_pair_dist} "
            f"<= 1e-6")

    # Derived hold force: the x-reaction the left plate must supply to hold the
    # shell+contents at the cold print geometry.  This is the muscle end-weight
    # form: sum the x-acceleration on the left plate from the kernel's force
    # evaluation on the zero-velocity print (resistance is zero at print, so the
    # result is pure DRAW + static cushion; for the hold threshold we take the
    # magnitude).
    acc = kernel.compute_forces(pos.astype(np.float32), vel.astype(np.float32),
                                use_cuda=False)
    F_hold = float(np.abs(acc[:n_plate, 0].sum()))

    derived = {
        "r_b": r_b,
        "d_eq": d_eq,
        "muscle_spacing": muscle_spacing,
        "fill": fill,
        "n_plate": 2 * n_plate,
        "n_shell": n_shell,
        "n_content": n_content,
        "s0": s0,
        "center_x": center_x,
        "neck": neck,
        "neck_diameter": neck_diameter,
        "neck_radius": neck_radius,
        "neck_center": neck_center,
        "neck_axis": neck_axis,
        "F_hold": F_hold,
    }

    return pos.astype(np.float32), vel.astype(np.float32), pin_mask, grain_ids, s0, derived
