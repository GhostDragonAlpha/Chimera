"""Multi-core adaptive octree build -- option (a): make build_octree's OWN construction
parallel instead of swapping trees (THE_TRIANGLE_CARRIER §PARALLEL OCTREE, continuation-11).

Produces a tree BYTE-IDENTICAL to serial LightEngine.bh_draw.build_octree: same cells, same
com/mass/min/max/child structure, same leaf memberships. So _bh_cuda / compute_forces_mod
consume it UNCHANGED and the force is 0.0% vs the referee BY CONSTRUCTION (not "<=1%").

Why identical (the load-bearing argument):
  * Each cell's partition is the referee's exact njit ``_partition_and_bounds`` run on its own
    disjoint ``order[start:end]``. A cell's fate (leaf / coincident-guard / children) depends
    only on ITS points, so cells at one BFS level are independent and can be partitioned in
    parallel without a race (disjoint ranges).
  * Children are created in parent-id x code order == serial BFS dequeue order, so global cell
    ids match exactly; bottom-up com/mass reuses the referee's ``_compute_com_mass``.
  * Numba ``@njit`` releases the GIL during compiled execution, so a thread pool of workers
    each calling ``_partition_and_bounds`` on disjoint ranges runs truly in parallel (shared
    memory, no pickling). This is the "build-once + reuse" layer for the adaptive build.

Honest residual (v1): level-0 (the root, one cell) and the bottom-up ``_compute_com_mass`` are
still single-core -- measured as the named residual; within-cell parallel partition is the
Phase-B membrane if that residual is significant. No free parameter: workers = os.cpu_count().
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from LightEngine.bh_draw import (
    _partition_and_bounds,
    _compute_com_mass,
    _pad_bounds,
)


def build_octree_mt(positions: np.ndarray, leaf_size: int = 16, workers: int | None = None) -> dict:
    """Multi-core build of the SAME adaptive octree as ``bh_draw.build_octree``.

    Returns a dict with exactly the same keys/values as ``build_octree`` (byte-identical).
    ``workers`` defaults to ``os.cpu_count()``; pass 1 for a serial A/B baseline.
    """
    pos = np.asarray(positions, dtype=np.float32)
    n = pos.shape[0]
    leaf_size = max(1, leaf_size)
    W = int(workers if workers else (os.cpu_count() or 4))

    if n == 0:
        # Delegate the empty case to the referee so output is identical.
        from LightEngine.bh_draw import build_octree
        return build_octree(pos, leaf_size=leaf_size)

    order = np.arange(n, dtype=np.int32)

    cell_min, cell_max, cell_child = [], [], []
    cell_is_leaf, cell_leaf_start, cell_leaf_count = [], [], []
    pstart, pend = [0], [n]                       # per-cell particle range in `order`

    bmin = pos.min(axis=0).astype(np.float32)
    bmax = pos.max(axis=0).astype(np.float32)
    bmin, bmax = _pad_bounds(bmin, bmax)
    cell_min.append(bmin); cell_max.append(bmax)
    cell_child.append(np.full(8, -1, dtype=np.int32))
    cell_is_leaf.append(False); cell_leaf_start.append(-1); cell_leaf_count.append(0)

    def _work(c):
        """Partition one cell (or mark it a leaf). Reads shared state by id; writes only its
        disjoint ``order`` range. Returns (c, part) where part is None for a small/leaf cell."""
        start, end = pstart[c], pend[c]
        m = end - start
        if m <= leaf_size:
            return c, None
        mid = 0.5 * (cell_min[c] + cell_max[c])
        cs = np.empty(8, dtype=np.int32); ce = np.empty(8, dtype=np.int32)
        cm = np.full((8, 3), np.inf, dtype=np.float32)
        cx = np.full((8, 3), -np.inf, dtype=np.float32)
        _partition_and_bounds(pos, order, start, end, mid, cs, ce, cm, cx)
        return c, (cs, ce, cm, cx)

    def _run_chunk(chunk):
        out = []
        for c in chunk:
            out.append(_work(c))
        return out

    level = [0]
    pool = ThreadPoolExecutor(max_workers=W) if W > 1 else None
    try:
        while level:
            # -- parallel partition of every cell in this level (disjoint ranges) --------
            if pool is None or len(level) <= 1:
                results = [_work(c) for c in level]
            else:
                # Static chunking across W workers amortizes per-task Python overhead; each
                # worker grinds its slice of cells serially (njit releases the GIL -> parallel).
                k = min(W, len(level))
                size = (len(level) + k - 1) // k
                chunks = [level[i:i + size] for i in range(0, len(level), size)]
                futs = [pool.submit(_run_chunk, ch) for ch in chunks]
                results = []
                for f in futs:                       # chunk order == level id-ascending order
                    results.extend(f.result())

            # -- deterministic child creation: parent-id x code order (== serial BFS) ----
            next_level = []
            for c, part in results:
                if part is None:                     # small cell -> leaf
                    cell_is_leaf[c] = True
                    cell_leaf_start[c] = int(pstart[c]); cell_leaf_count[c] = int(pend[c] - pstart[c])
                    continue
                cs, ce, cm, cx = part
                n_nonempty = 0
                for code in range(8):
                    if cs[code] != ce[code]:
                        n_nonempty += 1
                if n_nonempty == 1:                 # coincident guard (single point)
                    cell_is_leaf[c] = True
                    cell_leaf_start[c] = int(pstart[c]); cell_leaf_count[c] = int(pend[c] - pstart[c])
                    continue
                for code in range(8):
                    s, e = int(cs[code]), int(ce[code])
                    if s == e:
                        continue
                    cbmin, cbmax = _pad_bounds(cm[code].copy(), cx[code].copy())
                    cid = len(cell_min)
                    cell_min.append(cbmin); cell_max.append(cbmax)
                    cell_child.append(np.full(8, -1, dtype=np.int32))
                    cell_is_leaf.append(False); cell_leaf_start.append(-1); cell_leaf_count.append(0)
                    pstart.append(s); pend.append(e)
                    cell_child[c][code] = cid
                    next_level.append(cid)
            level = next_level
    finally:
        if pool is not None:
            pool.shutdown()

    n_cells = len(cell_min)

    # -- bottom-up com/mass, EXACTLY as the referee -------------------------------------
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

    # -- flatten to the referee's output arrays ---------------------------------------
    out_min = np.zeros((n_cells, 3), dtype=np.float32)
    out_max = np.zeros((n_cells, 3), dtype=np.float32)
    out_com = np.zeros((n_cells, 3), dtype=np.float32)
    out_mass = np.zeros(n_cells, dtype=np.float32)
    out_child = np.full((n_cells, 8), -1, dtype=np.int32)
    out_is_leaf = np.zeros(n_cells, dtype=np.int32)
    out_leaf_start = np.full(n_cells, -1, dtype=np.int32)
    out_leaf_count = np.zeros(n_cells, dtype=np.int32)
    for i in range(n_cells):
        out_min[i] = cell_min[i]; out_max[i] = cell_max[i]
        out_com[i] = cell_com[i]; out_mass[i] = cell_mass[i]
        out_child[i] = cell_child[i]
        out_is_leaf[i] = 1 if cell_is_leaf[i] else 0
        out_leaf_start[i] = cell_leaf_start[i]; out_leaf_count[i] = cell_leaf_count[i]

    return {
        "cell_min": out_min, "cell_max": out_max, "cell_com": out_com,
        "cell_mass": out_mass, "cell_child": out_child,
        "cell_is_leaf": out_is_leaf, "cell_leaf_start": out_leaf_start,
        "cell_leaf_count": out_leaf_count,
        "sorted_pos": sorted_pos, "sorted_idx": sorted_idx, "order": order,
        "n_cells": n_cells,
    }
