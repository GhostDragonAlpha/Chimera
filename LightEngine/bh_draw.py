"""
Barnes-Hut treecode for the LightEngine DRAW force.

DRAW in LightEngine.kernel is a direct O(N^2) softened inverse-square sum over
all pairs.  This module implements a theta-parameterized octree approximation
on the GPU using numba.cuda, with the identical force law (same G, EPS) and a
CPU reference path for validation.  It is delivered standalone; the kernel is
not modified.
"""

from __future__ import annotations

import math
import numpy as np
from numba import cuda, njit

from LightEngine.constants import G, EPS

# Softening squared, exactly as the pairwise kernel uses it.
EPS2 = float(EPS * EPS)

# Default theta chosen by validation (N=4096 jittered lattice, leaf_size=16,
# rel err <= 1e-3).
DEFAULT_THETA = 0.3


# ═══════════════════════════════════════════════════════════════════════════════
#  CPU octree build
# ═══════════════════════════════════════════════════════════════════════════════
def _pad_bounds(bmin: np.ndarray, bmax: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Add a tiny pad so boundary particles stay inside the cell."""
    eps_pad = 1e-6 * max(1.0, float(np.max(bmax - bmin)))
    return bmin - eps_pad, bmax + eps_pad


@njit(cache=True)
def _compute_com_mass(pos: np.ndarray, order: np.ndarray,
                      cell_is_leaf: np.ndarray,
                      cell_leaf_start: np.ndarray, cell_leaf_count: np.ndarray,
                      cell_child: np.ndarray,
                      cell_com: np.ndarray, cell_mass: np.ndarray):
    """Bottom-up computation of cell centers of mass and total mass."""
    n_cells = cell_is_leaf.shape[0]
    for c in range(n_cells - 1, -1, -1):
        if cell_is_leaf[c]:
            start = cell_leaf_start[c]
            end = start + cell_leaf_count[c]
            if end > start:
                sx = sy = sz = 0.0
                for k in range(start, end):
                    p = order[k]
                    sx += pos[p, 0]
                    sy += pos[p, 1]
                    sz += pos[p, 2]
                m = float(end - start)
                cell_com[c, 0] = sx / m
                cell_com[c, 1] = sy / m
                cell_com[c, 2] = sz / m
                cell_mass[c] = m
        else:
            sx = sy = sz = 0.0
            total = 0.0
            for k in range(8):
                child = cell_child[c, k]
                if child >= 0:
                    m = cell_mass[child]
                    sx += m * cell_com[child, 0]
                    sy += m * cell_com[child, 1]
                    sz += m * cell_com[child, 2]
                    total += m
            if total > 0.0:
                cell_com[c, 0] = sx / total
                cell_com[c, 1] = sy / total
                cell_com[c, 2] = sz / total
                cell_mass[c] = total


@njit(cache=True)
def _partition_and_bounds(pos: np.ndarray, order: np.ndarray, start: int, end: int,
                          mid: np.ndarray, child_starts: np.ndarray,
                          child_ends: np.ndarray, child_mins: np.ndarray,
                          child_maxs: np.ndarray):
    """
    In-place counting-sort partition of order[start:end] into 8 octants.

    Also computes tight bounding boxes for each child and writes child ranges.
    """
    n = end - start
    codes = np.empty(n, dtype=np.int32)
    for i in range(n):
        p = order[start + i]
        x = pos[p, 0]
        y = pos[p, 1]
        z = pos[p, 2]
        code = 0
        if x >= mid[0]:
            code |= 4
        if y >= mid[1]:
            code |= 2
        if z >= mid[2]:
            code |= 1
        codes[i] = code

    counts = np.zeros(8, dtype=np.int32)
    for i in range(n):
        counts[codes[i]] += 1

    prefix0 = np.zeros(9, dtype=np.int32)
    for k in range(8):
        prefix0[k + 1] = prefix0[k] + counts[k]

    out = np.empty(n, dtype=np.int32)
    prefix = prefix0.copy()
    for i in range(n):
        code = codes[i]
        out[prefix[code]] = order[start + i]
        prefix[code] += 1

    for i in range(n):
        order[start + i] = out[i]

    child_mins[:, :] = np.inf
    child_maxs[:, :] = -np.inf
    for i in range(n):
        p = order[start + i]
        x = pos[p, 0]
        y = pos[p, 1]
        z = pos[p, 2]
        code = 0
        if x >= mid[0]:
            code |= 4
        if y >= mid[1]:
            code |= 2
        if z >= mid[2]:
            code |= 1
        if x < child_mins[code, 0]:
            child_mins[code, 0] = x
        if x > child_maxs[code, 0]:
            child_maxs[code, 0] = x
        if y < child_mins[code, 1]:
            child_mins[code, 1] = y
        if y > child_maxs[code, 1]:
            child_maxs[code, 1] = y
        if z < child_mins[code, 2]:
            child_mins[code, 2] = z
        if z > child_maxs[code, 2]:
            child_maxs[code, 2] = z

    for k in range(8):
        child_starts[k] = start + prefix0[k]
        child_ends[k] = start + prefix0[k + 1]


def build_octree(positions: np.ndarray, leaf_size: int = 1) -> dict:
    """
    Build a CPU octree and return flat arrays for the GPU kernel.

    Uses an iterative BFS build with in-place octant partitioning.  Particles
    are reordered by cell occupancy; leaves store their contiguous range in this
    order array so the kernel can perform direct summation without depending on
    leaf_size being 1.
    """
    pos = np.asarray(positions, dtype=np.float32)
    n = pos.shape[0]
    leaf_size = max(1, leaf_size)

    if n == 0:
        return {
            "cell_min": np.zeros((1, 3), dtype=np.float32),
            "cell_max": np.zeros((1, 3), dtype=np.float32),
            "cell_com": np.zeros((1, 3), dtype=np.float32),
            "cell_mass": np.zeros(1, dtype=np.float32),
            "cell_child": np.full((1, 8), -1, dtype=np.int32),
            "cell_is_leaf": np.zeros(1, dtype=np.int32),
            "cell_leaf_start": np.full(1, -1, dtype=np.int32),
            "cell_leaf_count": np.zeros(1, dtype=np.int32),
            "sorted_pos": np.zeros((0, 3), dtype=np.float32),
            "sorted_idx": np.empty(0, dtype=np.int32),
            "order": np.empty(0, dtype=np.int32),
            "n_cells": 1,
        }

    order = np.arange(n, dtype=np.int32)

    # Per-cell data accumulated during BFS.
    cell_min = []
    cell_max = []
    cell_child = []
    cell_is_leaf = []
    cell_leaf_start = []
    cell_leaf_count = []
    cell_particle_start = []
    cell_particle_end = []

    # Root.
    bmin = pos.min(axis=0).astype(np.float32)
    bmax = pos.max(axis=0).astype(np.float32)
    bmin, bmax = _pad_bounds(bmin, bmax)

    cell_min.append(bmin)
    cell_max.append(bmax)
    cell_child.append(np.full(8, -1, dtype=np.int32))
    cell_is_leaf.append(False)
    cell_leaf_start.append(-1)
    cell_leaf_count.append(0)
    cell_particle_start.append(0)
    cell_particle_end.append(n)

    queue = [0]
    head = 0
    while head < len(queue):
        c = queue[head]
        head += 1
        start = cell_particle_start[c]
        end = cell_particle_end[c]
        m = end - start

        if m <= leaf_size:
            cell_is_leaf[c] = True
            cell_leaf_start[c] = int(start)
            cell_leaf_count[c] = int(m)
            continue

        mid = 0.5 * (cell_min[c] + cell_max[c])
        child_starts = np.empty(8, dtype=np.int32)
        child_ends = np.empty(8, dtype=np.int32)
        child_mins = np.full((8, 3), np.inf, dtype=np.float32)
        child_maxs = np.full((8, 3), -np.inf, dtype=np.float32)
        _partition_and_bounds(pos, order, start, end, mid,
                              child_starts, child_ends, child_mins, child_maxs)

        for code in range(8):
            child_start = int(child_starts[code])
            child_end = int(child_ends[code])
            if child_start == child_end:
                continue
            child_bmin = child_mins[code].copy()
            child_bmax = child_maxs[code].copy()
            child_bmin, child_bmax = _pad_bounds(child_bmin, child_bmax)

            child_id = len(cell_min)
            cell_min.append(child_bmin)
            cell_max.append(child_bmax)
            cell_child.append(np.full(8, -1, dtype=np.int32))
            cell_is_leaf.append(False)
            cell_leaf_start.append(-1)
            cell_leaf_count.append(0)
            cell_particle_start.append(child_start)
            cell_particle_end.append(child_end)

            cell_child[c][code] = child_id
            queue.append(child_id)

    n_cells = len(cell_min)

    # Compute COM and mass bottom-up (children are created before parents).
    cell_com = np.zeros((n_cells, 3), dtype=np.float32)
    cell_mass = np.zeros(n_cells, dtype=np.float32)
    out_is_leaf_arr = np.array(cell_is_leaf, dtype=np.int32)
    out_leaf_start_arr = np.array(cell_leaf_start, dtype=np.int32)
    out_leaf_count_arr = np.array(cell_leaf_count, dtype=np.int32)
    out_child_arr = np.array(cell_child, dtype=np.int32)
    _compute_com_mass(pos, order, out_is_leaf_arr, out_leaf_start_arr,
                      out_leaf_count_arr, out_child_arr, cell_com, cell_mass)

    sorted_pos = pos[order]
    sorted_idx = order

    # Flatten to output arrays.
    out_min = np.zeros((n_cells, 3), dtype=np.float32)
    out_max = np.zeros((n_cells, 3), dtype=np.float32)
    out_com = np.zeros((n_cells, 3), dtype=np.float32)
    out_mass = np.zeros(n_cells, dtype=np.float32)
    out_child = np.full((n_cells, 8), -1, dtype=np.int32)
    out_is_leaf = np.zeros(n_cells, dtype=np.int32)
    out_leaf_start = np.full(n_cells, -1, dtype=np.int32)
    out_leaf_count = np.zeros(n_cells, dtype=np.int32)
    for i in range(n_cells):
        out_min[i] = cell_min[i]
        out_max[i] = cell_max[i]
        out_com[i] = cell_com[i]
        out_mass[i] = cell_mass[i]
        out_child[i] = cell_child[i]
        out_is_leaf[i] = 1 if cell_is_leaf[i] else 0
        out_leaf_start[i] = cell_leaf_start[i]
        out_leaf_count[i] = cell_leaf_count[i]

    return {
        "cell_min": out_min,
        "cell_max": out_max,
        "cell_com": out_com,
        "cell_mass": out_mass,
        "cell_child": out_child,
        "cell_is_leaf": out_is_leaf,
        "cell_leaf_start": out_leaf_start,
        "cell_leaf_count": out_leaf_count,
        "sorted_pos": sorted_pos,
        "sorted_idx": sorted_idx,
        "order": order,
        "n_cells": n_cells,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  CPU reference Barnes-Hut (for validation)
# ═══════════════════════════════════════════════════════════════════════════════
@njit(cache=True)
def _bh_cpu(pos: np.ndarray, sorted_pos: np.ndarray, sorted_idx: np.ndarray,
            cell_min: np.ndarray, cell_max: np.ndarray,
            cell_com: np.ndarray, cell_mass: np.ndarray,
            cell_child: np.ndarray, cell_is_leaf: np.ndarray,
            cell_leaf_start: np.ndarray, cell_leaf_count: np.ndarray,
            theta: float, G: float, eps2: float, out: np.ndarray):
    """CPU reference BH traversal using an explicit stack."""
    n = pos.shape[0]
    n_cells = cell_min.shape[0]
    stack = np.empty(n_cells, dtype=np.int32)
    for i in range(n):
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        ax = 0.0
        ay = 0.0
        az = 0.0
        sp = 0
        stack[sp] = 0
        sp += 1
        while sp > 0:
            sp -= 1
            c = stack[sp]
            if cell_is_leaf[c]:
                start = cell_leaf_start[c]
                end = start + cell_leaf_count[c]
                for k in range(start, end):
                    if sorted_idx[k] == i:
                        continue
                    dx = sorted_pos[k, 0] - xi
                    dy = sorted_pos[k, 1] - yi
                    dz = sorted_pos[k, 2] - zi
                    r2 = dx * dx + dy * dy + dz * dz + eps2
                    inv_r3 = 1.0 / (r2 * math.sqrt(r2))
                    f = G * inv_r3
                    ax += f * dx
                    ay += f * dy
                    az += f * dz
                continue

            dx = cell_com[c, 0] - xi
            dy = cell_com[c, 1] - yi
            dz = cell_com[c, 2] - zi
            d2 = dx * dx + dy * dy + dz * dz
            d = math.sqrt(d2)

            sx = cell_max[c, 0] - cell_min[c, 0]
            sy = cell_max[c, 1] - cell_min[c, 1]
            sz = cell_max[c, 2] - cell_min[c, 2]
            s = max(sx, max(sy, sz))

            if s < theta * d:
                r2 = d2 + eps2
                inv_r3 = 1.0 / (r2 * math.sqrt(r2))
                f = G * cell_mass[c] * inv_r3
                ax += f * dx
                ay += f * dy
                az += f * dz
            else:
                for k in range(8):
                    child = cell_child[c, k]
                    if child >= 0:
                        stack[sp] = child
                        sp += 1
        out[i, 0] = ax
        out[i, 1] = ay
        out[i, 2] = az


def compute_draw_bh_cpu(positions: np.ndarray, theta: float | None = None,
                        G_val: float | None = None,
                        eps_val: float | None = None,
                        leaf_size: int = 16) -> np.ndarray:
    """CPU reference Barnes-Hut DRAW acceleration."""
    if theta is None:
        theta = DEFAULT_THETA
    if G_val is None:
        G_val = G
    if eps_val is None:
        eps_val = EPS
    positions = np.asarray(positions, dtype=np.float32)
    n = positions.shape[0]
    tree = build_octree(positions, leaf_size=leaf_size)
    out = np.empty((n, 3), dtype=np.float32)
    _bh_cpu(positions, tree["sorted_pos"], tree["sorted_idx"],
            tree["cell_min"], tree["cell_max"],
            tree["cell_com"], tree["cell_mass"], tree["cell_child"],
            tree["cell_is_leaf"], tree["cell_leaf_start"], tree["cell_leaf_count"],
            float(theta), float(G_val), float(eps_val * eps_val), out)
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  CUDA Barnes-Hut
# ═══════════════════════════════════════════════════════════════════════════════
_STACK_SIZE = 64


@cuda.jit(cache=True)
def _bh_cuda(pos, sorted_pos, sorted_idx, out, cell_min, cell_max, cell_com,
             cell_mass, cell_child, cell_is_leaf, cell_leaf_start,
             cell_leaf_count, theta, G, eps2, n):
    """GPU Barnes-Hut DRAW acceleration with explicit per-thread stack."""
    i = cuda.grid(1)
    if i >= n:
        return

    stack = cuda.local.array(_STACK_SIZE, dtype=np.int32)
    xi = pos[i, 0]
    yi = pos[i, 1]
    zi = pos[i, 2]
    ax = 0.0
    ay = 0.0
    az = 0.0
    sp = 0
    stack[sp] = 0
    sp += 1

    while sp > 0:
        sp -= 1
        c = stack[sp]

        if cell_is_leaf[c]:
            start = cell_leaf_start[c]
            end = start + cell_leaf_count[c]
            for k in range(start, end):
                if sorted_idx[k] == i:
                    continue
                dx = sorted_pos[k, 0] - xi
                dy = sorted_pos[k, 1] - yi
                dz = sorted_pos[k, 2] - zi
                r2 = dx * dx + dy * dy + dz * dz + eps2
                inv_r3 = 1.0 / (r2 * math.sqrt(r2))
                f = G * inv_r3
                ax += f * dx
                ay += f * dy
                az += f * dz
            continue

        dx = cell_com[c, 0] - xi
        dy = cell_com[c, 1] - yi
        dz = cell_com[c, 2] - zi
        d2 = dx * dx + dy * dy + dz * dz
        d = math.sqrt(d2)

        sx = cell_max[c, 0] - cell_min[c, 0]
        sy = cell_max[c, 1] - cell_min[c, 1]
        sz = cell_max[c, 2] - cell_min[c, 2]
        s = sx
        if sy > s:
            s = sy
        if sz > s:
            s = sz

        if s < theta * d:
            r2 = d2 + eps2
            inv_r3 = 1.0 / (r2 * math.sqrt(r2))
            f = G * cell_mass[c] * inv_r3
            ax += f * dx
            ay += f * dy
            az += f * dz
        else:
            for k in range(8):
                child = cell_child[c, k]
                if child >= 0:
                    if sp >= _STACK_SIZE:
                        # Stack overflow: mark as NaN and bail.
                        out[i, 0] = float("nan")
                        out[i, 1] = float("nan")
                        out[i, 2] = float("nan")
                        return
                    stack[sp] = child
                    sp += 1

    out[i, 0] = ax
    out[i, 1] = ay
    out[i, 2] = az


def compute_draw_bh(positions: np.ndarray, theta: float | None = None,
                    G_val: float | None = None, eps_val: float | None = None,
                    tree: dict | None = None,
                    leaf_size: int = 16) -> np.ndarray:
    """
    GPU Barnes-Hut DRAW acceleration.

    Parameters
    ----------
    positions : (N, 3) float32 array
    theta : opening angle (default set by validation)
    G_val : gravitational strength (defaults to constants.G)
    eps_val : softening length (defaults to constants.EPS)
    tree : optional prebuilt octree from ``build_octree``
    leaf_size : particles per leaf when building a new tree

    Returns
    -------
    out : (N, 3) float32 array of accelerations
    """
    if theta is None:
        theta = DEFAULT_THETA
    if G_val is None:
        G_val = G
    if eps_val is None:
        eps_val = EPS
    positions = np.asarray(positions, dtype=np.float32)
    n = positions.shape[0]
    if n == 0:
        return np.empty((0, 3), dtype=np.float32)

    if tree is None:
        tree = build_octree(positions, leaf_size=leaf_size)

    cell_min = cuda.to_device(tree["cell_min"])
    cell_max = cuda.to_device(tree["cell_max"])
    cell_com = cuda.to_device(tree["cell_com"])
    cell_mass = cuda.to_device(tree["cell_mass"])
    cell_child = cuda.to_device(tree["cell_child"])
    cell_is_leaf = cuda.to_device(tree["cell_is_leaf"])
    cell_leaf_start = cuda.to_device(tree["cell_leaf_start"])
    cell_leaf_count = cuda.to_device(tree["cell_leaf_count"])
    d_sorted_pos = cuda.to_device(tree["sorted_pos"])
    d_sorted_idx = cuda.to_device(tree["sorted_idx"])
    d_pos = cuda.to_device(positions)
    d_out = cuda.device_array((n, 3), dtype=np.float32)

    threads = 256
    blocks = (n + threads - 1) // threads
    _bh_cuda[blocks, threads](
        d_pos, d_sorted_pos, d_sorted_idx, d_out, cell_min, cell_max, cell_com,
        cell_mass, cell_child, cell_is_leaf, cell_leaf_start, cell_leaf_count,
        float(theta), float(G_val), float(eps_val * eps_val), n,
    )
    cuda.synchronize()
    out = d_out.copy_to_host()

    # Detect stack overflow or NaN.
    if not np.all(np.isfinite(out)):
        raise RuntimeError("Barnes-Hut kernel produced non-finite output; "
                           "increase _STACK_SIZE or reduce theta.")
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers for validation / integration
# ═══════════════════════════════════════════════════════════════════════════════
def relative_error(a: np.ndarray, b: np.ndarray) -> float:
    """Maximum relative L2 error over particles."""
    denom = np.linalg.norm(b, axis=1)
    denom = np.where(denom == 0, 1.0, denom)
    errs = np.linalg.norm(a - b, axis=1) / denom
    return float(np.max(errs))


def set_default_theta(theta: float):
    """Allow tests/benchmarks to publish the validated default theta."""
    global DEFAULT_THETA
    DEFAULT_THETA = float(theta)
