"""
Spatial-grid neighbor list for the LightEngine resistance force.

The resistance force in LightEngine.kernel has a hard cutoff ``R_C`` and is
currently evaluated by looping over all pairs.  This module builds an exact
uniform-grid neighbor list (cell size = ``r_cut``) and evaluates the resistance
force from that list.  It does NOT alter the DRAW force; DRAW remains a direct
O(N^2) softened inverse-square summation because it has no cutoff.

The public API mirrors the kernel's resistance interface so the list can drop
in later without changing callers:

    from LightEngine.neighbor import compute_resistance_grid
    acc = compute_resistance_grid(positions, velocities)
"""

from __future__ import annotations

import math
import numpy as np
from numba import njit

from LightEngine.constants import (
    R_WALL, R_BOND, R_C, P_WALL, K_WALL, K_BOND, GAMMA_W, S_WALL,
)


@njit(cache=True)
def _cell_key(ix: int, iy: int, iz: int, ny: int, nz: int) -> int:
    """Flatten 3-D cell indices to a 1-D key."""
    return (ix * ny + iy) * nz + iz


@njit(cache=True)
def _build_grid(pos: np.ndarray, r_cut: float):
    """
    Build a uniform grid and return sorted-particle arrays.

    Returns
    -------
    nx, ny, nz : int
        Grid dimensions.
    xmin, ymin, zmin : float
        Grid origin.
    cell_start : (n_cells + 1,) int32
        Prefix-sum start index of each cell in ``order``.
    order : (N,) int32
        Particle indices sorted by cell.
    """
    n = pos.shape[0]
    if n == 0:
        return 0, 0, 0, 0.0, 0.0, 0.0, np.empty(1, dtype=np.int32), np.empty(0, dtype=np.int32)

    cell_size = r_cut

    xmin = ymin = zmin = float("inf")
    xmax = ymax = zmax = float("-inf")
    for i in range(n):
        x = pos[i, 0]
        y = pos[i, 1]
        z = pos[i, 2]
        if x < xmin:
            xmin = x
        if x > xmax:
            xmax = x
        if y < ymin:
            ymin = y
        if y > ymax:
            ymax = y
        if z < zmin:
            zmin = z
        if z > zmax:
            zmax = z

    nx = int(math.ceil((xmax - xmin) / cell_size)) + 1
    ny = int(math.ceil((ymax - ymin) / cell_size)) + 1
    nz = int(math.ceil((zmax - zmin) / cell_size)) + 1
    n_cells = nx * ny * nz

    cell_pop = np.zeros(n_cells, dtype=np.int32)
    cell_idx = np.empty(n, dtype=np.int32)
    for i in range(n):
        ix = int(math.floor((pos[i, 0] - xmin) / cell_size))
        iy = int(math.floor((pos[i, 1] - ymin) / cell_size))
        iz = int(math.floor((pos[i, 2] - zmin) / cell_size))
        key = _cell_key(ix, iy, iz, ny, nz)
        cell_idx[i] = key
        cell_pop[key] += 1

    cell_start = np.zeros(n_cells + 1, dtype=np.int32)
    s = 0
    for k in range(n_cells):
        cell_start[k] = s
        s += cell_pop[k]
    cell_start[n_cells] = s

    cursor = cell_start.copy()
    order = np.empty(n, dtype=np.int32)
    for i in range(n):
        key = cell_idx[i]
        idx = cursor[key]
        order[idx] = i
        cursor[key] = idx + 1

    return nx, ny, nz, xmin, ymin, zmin, cell_start, order


@njit(cache=True)
def _count_neighbors(pos: np.ndarray, r_cut: float, nx: int, ny: int, nz: int,
                     xmin: float, ymin: float, zmin: float,
                     cell_start: np.ndarray, order: np.ndarray) -> np.ndarray:
    """Return the number of neighbors per particle (within r_cut, excluding self)."""
    n = pos.shape[0]
    counts = np.zeros(n, dtype=np.int32)
    if n == 0:
        return counts
    cell_size = r_cut
    rc2 = r_cut * r_cut
    for i in range(n):
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        ci = int(math.floor((xi - xmin) / cell_size))
        cj = int(math.floor((yi - ymin) / cell_size))
        ck = int(math.floor((zi - zmin) / cell_size))
        c = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    nxi = ci + dx
                    nyi = cj + dy
                    nzi = ck + dz
                    if nxi < 0 or nxi >= nx:
                        continue
                    if nyi < 0 or nyi >= ny:
                        continue
                    if nzi < 0 or nzi >= nz:
                        continue
                    key = _cell_key(nxi, nyi, nzi, ny, nz)
                    start = cell_start[key]
                    end = cell_start[key + 1]
                    for t in range(start, end):
                        j = order[t]
                        if i == j:
                            continue
                        ddx = pos[j, 0] - xi
                        ddy = pos[j, 1] - yi
                        ddz = pos[j, 2] - zi
                        r2 = ddx * ddx + ddy * ddy + ddz * ddz
                        if r2 <= rc2:
                            c += 1
        counts[i] = c
    return counts


@njit(cache=True)
def _fill_neighbors(pos: np.ndarray, r_cut: float, nx: int, ny: int, nz: int,
                    xmin: float, ymin: float, zmin: float,
                    cell_start: np.ndarray, order: np.ndarray,
                    offsets: np.ndarray, neighbors: np.ndarray):
    """Fill the flat neighbor list using precomputed offsets."""
    n = pos.shape[0]
    if n == 0:
        return
    cell_size = r_cut
    rc2 = r_cut * r_cut
    cursor = offsets.copy()
    for i in range(n):
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        ci = int(math.floor((xi - xmin) / cell_size))
        cj = int(math.floor((yi - ymin) / cell_size))
        ck = int(math.floor((zi - zmin) / cell_size))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    nxi = ci + dx
                    nyi = cj + dy
                    nzi = ck + dz
                    if nxi < 0 or nxi >= nx:
                        continue
                    if nyi < 0 or nyi >= ny:
                        continue
                    if nzi < 0 or nzi >= nz:
                        continue
                    key = _cell_key(nxi, nyi, nzi, ny, nz)
                    start = cell_start[key]
                    end = cell_start[key + 1]
                    for t in range(start, end):
                        j = order[t]
                        if i == j:
                            continue
                        ddx = pos[j, 0] - xi
                        ddy = pos[j, 1] - yi
                        ddz = pos[j, 2] - zi
                        r2 = ddx * ddx + ddy * ddy + ddz * ddz
                        if r2 <= rc2:
                            neighbors[cursor[i]] = j
                            cursor[i] += 1


@njit(cache=True)
def _resistance_from_neighbors(pos: np.ndarray, vel: np.ndarray,
                               offsets: np.ndarray, neighbors: np.ndarray,
                               rw: float, rb: float, p: float, kw: float,
                               kb: float, gamma_w: float, s_wall: float,
                               out: np.ndarray):
    """
    Compute resistance accelerations from a precomputed neighbor list.

    Force law is identical to ``LightEngine.kernel._resist_cpu``:
      - r < rw        : wall repulsion + radial contact damping
      - rw <= r <= rb : bond spring (repulsive only)
      - r > R_C       : zero (already filtered by neighbor list)
    """
    n = pos.shape[0]
    for i in range(n):
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        vxi = vel[i, 0]
        vyi = vel[i, 1]
        vzi = vel[i, 2]
        ax = 0.0
        ay = 0.0
        az = 0.0
        start = offsets[i]
        end = offsets[i + 1]
        for k in range(start, end):
            j = neighbors[k]
            dx = pos[j, 0] - xi
            dy = pos[j, 1] - yi
            dz = pos[j, 2] - zi
            r2 = dx * dx + dy * dy + dz * dz
            if r2 < 1e-18:
                continue
            r = math.sqrt(r2)
            if r < rw:
                inv_r = 1.0 / r
                ux_ij = dx * inv_r
                uy_ij = dy * inv_r
                uz_ij = dz * inv_r
                r_eff = math.sqrt(r2 + s_wall * s_wall)
                f = kw * ((rw / r_eff) ** p) / r_eff
                ax += f * (-ux_ij)
                ay += f * (-uy_ij)
                az += f * (-uz_ij)
                dvx = vel[j, 0] - vxi
                dvy = vel[j, 1] - vyi
                dvz = vel[j, 2] - vzi
                v_rad = dvx * ux_ij + dvy * uy_ij + dvz * uz_ij
                damp = gamma_w * v_rad
                ax += damp * ux_ij
                ay += damp * uy_ij
                az += damp * uz_ij
            elif r <= rb:
                f = kb * (r - rb) / (rb * r)
                ax += f * dx
                ay += f * dy
                az += f * dz
        out[i, 0] = ax
        out[i, 1] = ay
        out[i, 2] = az


def build_neighbor_list(positions: np.ndarray, r_cut: float = R_C) -> tuple[np.ndarray, np.ndarray]:
    """
    Build a uniform-grid neighbor list with cell size = r_cut.

    Parameters
    ----------
    positions : (N, 3) float32 array
    r_cut : float, optional
        Cutoff distance (defaults to ``LightEngine.constants.R_C``).

    Returns
    -------
    offsets : (N + 1,) int32 array
        Start index of each particle's neighbors in ``neighbors``.
    neighbors : (M,) int32 array
        Flat list of neighbor indices.  Each particle's neighbors are the
        distinct other particles within ``r_cut``.
    """
    positions = np.asarray(positions, dtype=np.float32)
    n = positions.shape[0]
    if n == 0:
        return np.zeros(1, dtype=np.int32), np.empty(0, dtype=np.int32)

    nx, ny, nz, xmin, ymin, zmin, cell_start, order = _build_grid(positions, float(r_cut))
    counts = _count_neighbors(positions, float(r_cut), nx, ny, nz, xmin, ymin, zmin,
                              cell_start, order)
    offsets = np.zeros(n + 1, dtype=np.int32)
    offsets[1:] = np.cumsum(counts)
    neighbors = np.empty(offsets[-1], dtype=np.int32)
    _fill_neighbors(positions, float(r_cut), nx, ny, nz, xmin, ymin, zmin,
                    cell_start, order, offsets, neighbors)
    return offsets, neighbors


def compute_resistance_grid(positions: np.ndarray,
                            velocities: np.ndarray,
                            offsets: np.ndarray | None = None,
                            neighbors: np.ndarray | None = None,
                            out: np.ndarray | None = None,
                            r_cut: float = R_C) -> np.ndarray:
    """
    Compute resistance accelerations using a uniform-grid neighbor list.

    If ``offsets`` and ``neighbors`` are not supplied they are built from
    ``positions``.  The returned acceleration matches the pairwise reference
    to within floating-point summation order.
    """
    positions = np.asarray(positions, dtype=np.float32)
    velocities = np.asarray(velocities, dtype=np.float32)
    n = positions.shape[0]
    if out is None:
        out = np.empty((n, 3), dtype=np.float32)
    else:
        out = np.asarray(out, dtype=np.float32)

    if offsets is None or neighbors is None:
        offsets, neighbors = build_neighbor_list(positions, float(r_cut))

    _resistance_from_neighbors(
        positions, velocities, offsets, neighbors,
        float(R_WALL), float(R_BOND), float(P_WALL),
        float(K_WALL), float(K_BOND), float(GAMMA_W), float(S_WALL),
        out,
    )
    return out


def neighbor_counts(positions: np.ndarray, r_cut: float = R_C) -> np.ndarray:
    """Return the number of neighbors within ``r_cut`` for every particle."""
    positions = np.asarray(positions, dtype=np.float32)
    n = positions.shape[0]
    if n == 0:
        return np.zeros(0, dtype=np.int32)
    nx, ny, nz, xmin, ymin, zmin, cell_start, order = _build_grid(positions, float(r_cut))
    return _count_neighbors(positions, float(r_cut), nx, ny, nz, xmin, ymin, zmin,
                            cell_start, order)
