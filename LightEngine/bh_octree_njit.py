"""B1 -- de-Pythoned single-njit adaptive octree build, BYTE-IDENTICAL to bh_draw.build_octree.

Continuation-12 Phase B' step B1: move the whole BFS out of Python into ONE @njit function so
the ~2398 ms of per-cell Python orchestration (numba dispatch + list appends + scratch allocs)
becomes C-speed. Reuses the referee's EXACT njit ``_partition_and_bounds`` and ``_compute_com_mass``,
so output is BYTE-IDENTICAL to ``build_octree`` by construction: same partition, same com/mass,
same FIFO BFS order (root=0, children in parent-id x code order), same pad formula.

bh_draw.py is NOT modified (referee; T4 measured on it) -- we import from it. No hand-rolled
partition/sort: the counting sort and bottom-up com/mass are the referee's own compiled fns.
"""
from __future__ import annotations

import numpy as np
from numba import njit

from LightEngine.bh_draw import _partition_and_bounds, _compute_com_mass


@njit(cache=True)
def _build_core(pos, order, leaf_size, max_cells,
                cell_min, cell_max, cell_child, cell_is_leaf,
                cell_leaf_start, cell_leaf_count, pstart, pend,
                cs, ce, cm, cx):
    """Compiled BFS mirroring build_octree exactly. Returns the number of cells created."""
    n = pos.shape[0]

    # -- root (id 0): exact min/max over all points + pad (mirrors _pad_bounds) ---------
    bmin = np.full(3, np.inf, dtype=np.float32); bmax = np.full(3, -np.inf, dtype=np.float32)
    for i in range(n):
        for d in range(3):
            v = pos[i, d]
            if v < bmin[d]:
                bmin[d] = v
            if v > bmax[d]:
                bmax[d] = v
    span = 0.0
    for d in range(3):
        dd = bmax[d] - bmin[d]
        if dd > span:
            span = dd
    # f64 multiply then cast: mirrors numpy value-based casting in _pad_bounds exactly
    eps = np.float32(np.float64(1e-6) * (np.float64(1.0) if span < 1.0 else np.float64(span)))
    for d in range(3):
        cell_min[0, d] = bmin[d] - eps
        cell_max[0, d] = bmax[d] + eps
    for k in range(8):
        cell_child[0, k] = -1
    cell_is_leaf[0] = 0; cell_leaf_start[0] = -1; cell_leaf_count[0] = 0
    pstart[0] = 0; pend[0] = n

    queue = np.empty(max_cells, dtype=np.int64)
    head = 0; tail = 1; queue[0] = 0
    ncells = 1
    mid = np.empty(3, dtype=np.float32)

    while head < tail:
        c = queue[head]; head += 1
        start = pstart[c]; end = pend[c]; m = end - start
        if m <= leaf_size:
            cell_is_leaf[c] = 1; cell_leaf_start[c] = int(start); cell_leaf_count[c] = int(m)
            continue

        for d in range(3):
            mid[d] = np.float32(0.5) * (cell_min[c, d] + cell_max[c, d])
        # Reuse ONE scratch set across cells: _partition_and_bounds resets cm/cx and writes all
        # of cs/ce each call, so this is race-free and allocation-free per cell.
        _partition_and_bounds(pos, order, start, end, mid, cs, ce, cm, cx)

        n_nonempty = 0
        for code in range(8):
            if cs[code] != ce[code]:
                n_nonempty += 1
        if n_nonempty == 1:                       # coincident guard (single point)
            cell_is_leaf[c] = 1; cell_leaf_start[c] = int(start); cell_leaf_count[c] = int(m)
            continue

        for code in range(8):
            s = cs[code]; e = ce[code]
            if s == e:
                continue
            # child bounds + pad (mirrors _pad_bounds on cm/cx[code])
            cbmin0 = cm[code, 0]; cbmin1 = cm[code, 1]; cbmin2 = cm[code, 2]
            cbmax0 = cx[code, 0]; cbmax1 = cx[code, 1]; cbmax2 = cx[code, 2]
            cspan = 0.0
            dd0 = cbmax0 - cbmin0; dd1 = cbmax1 - cbmin1; dd2 = cbmax2 - cbmin2
            if dd0 > cspan:
                cspan = dd0
            if dd1 > cspan:
                cspan = dd1
            if dd2 > cspan:
                cspan = dd2
            # f64 multiply then cast: mirrors numpy value-based casting in _pad_bounds exactly
            ceps = np.float32(np.float64(1e-6) * (np.float64(1.0) if cspan < 1.0 else np.float64(cspan)))

            cid = ncells; ncells += 1
            cell_min[cid, 0] = cbmin0 - ceps; cell_max[cid, 0] = cbmax0 + ceps
            cell_min[cid, 1] = cbmin1 - ceps; cell_max[cid, 1] = cbmax1 + ceps
            cell_min[cid, 2] = cbmin2 - ceps; cell_max[cid, 2] = cbmax2 + ceps
            for k in range(8):
                cell_child[cid, k] = -1
            cell_is_leaf[cid] = 0; cell_leaf_start[cid] = -1; cell_leaf_count[cid] = 0
            pstart[cid] = s; pend[cid] = e
            cell_child[c, code] = cid
            queue[tail] = cid; tail += 1

    return ncells


def build_octree_njit(positions: np.ndarray, leaf_size: int = 16) -> dict:
    """Single-njit adaptive octree build, byte-identical to ``bh_draw.build_octree``.

    Returns a dict with exactly the same keys/values as ``build_octree``. The whole BFS runs in
    one compiled function (no per-cell Python); scratch is preallocated once (not per cell).
    """
    pos = np.asarray(positions, dtype=np.float32)
    n = pos.shape[0]
    if n == 0:
        from LightEngine.bh_draw import build_octree
        return build_octree(pos, leaf_size=leaf_size)

    order = np.arange(n, dtype=np.int32)
    max_cells = 2 * n   # universal bound (#cells <= 2N-1); one batch alloc, not per-cell

    cell_min = np.zeros((max_cells, 3), np.float32); cell_max = np.zeros((max_cells, 3), np.float32)
    cell_child = np.full((max_cells, 8), -1, np.int32)
    cell_is_leaf = np.zeros(max_cells, np.int32)
    cell_leaf_start = np.full(max_cells, -1, np.int32)
    cell_leaf_count = np.zeros(max_cells, np.int32)
    pstart = np.zeros(max_cells, np.int64); pend = np.zeros(max_cells, np.int64)
    cs = np.empty(8, np.int32); ce = np.empty(8, np.int32)
    cm = np.full((8, 3), np.inf, np.float32); cx = np.full((8, 3), -np.inf, np.float32)

    ncells = _build_core(pos, order, leaf_size, max_cells, cell_min, cell_max, cell_child,
                         cell_is_leaf, cell_leaf_start, cell_leaf_count, pstart, pend, cs, ce, cm, cx)

    # com/mass via the referee's njit on the exact slice (byte-identical by construction).
    com = np.zeros((ncells, 3), np.float32); mass = np.zeros(ncells, np.float32)
    _compute_com_mass(pos, order, cell_is_leaf[:ncells], cell_leaf_start[:ncells],
                      cell_leaf_count[:ncells], cell_child[:ncells], com, mass)

    sorted_pos = pos[order]
    return {
        "cell_min": cell_min[:ncells].copy(), "cell_max": cell_max[:ncells].copy(),
        "cell_com": com, "cell_mass": mass, "cell_child": cell_child[:ncells].copy(),
        "cell_is_leaf": cell_is_leaf[:ncells].copy(), "cell_leaf_start": cell_leaf_start[:ncells].copy(),
        "cell_leaf_count": cell_leaf_count[:ncells].copy(),
        "sorted_pos": sorted_pos, "sorted_idx": order, "order": order, "n_cells": ncells,
    }
