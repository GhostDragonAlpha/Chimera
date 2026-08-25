"""B2 candidate A -- LEVEL-SYNCHRONOUS prange octree build, BYTE-IDENTICAL to bh_draw.build_octree.

Continuation-13 Phase B' step B2 (candidate A per §B2 PRE-REGISTERED): the single-njit BFS of
``bh_octree_njit`` is restructured into LEVEL-SYNCHRONOUS form so each level's cell partitions
run under numba ``prange`` across cores -- NO Python dispatch (v1 mt's failure mode was
per-cell *Python* njit dispatch overhead; prange stays compiled).

BYTE-IDENTITY ARGUMENT (induction, recorded before build):
  FIFO BFS with append-at-tail dequeues in CREATION order == level order: all depth-d cells
  before depth-(d+1), parents within a level in ascending id. Children of parent c are created
  in octant-code order (0..7, empty skipped). So the global child-id sequence at level L+1 is
  exactly: concatenate over parents in id-order their non-empty codes in code-ascending order.
  This build does precisely that: pass 1 (prange) partitions each parent's DISJOINT range and
  counts its children; pass 2 prefix-sums the counts -> base ids; pass 3 (prange) commits
  child cid = base[parent] + local j into the global arrays. Same compiled
  ``_partition_and_bounds`` on byte-identical ranges (induction: every range's contents are
  determined by its path of deterministic partitions) => same bounds, same pad
  (f64-multiply-then-cast eps), same final order array => BYTE-IDENTICAL to build_octree.

bh_draw.py is NOT modified (referee). Reuses the referee's njit _partition_and_bounds +
_compute_com_mass -- no hand-rolled partition/sort.
"""
from __future__ import annotations

import numpy as np
from numba import njit, prange

from LightEngine.bh_draw import _partition_and_bounds, _compute_com_mass


@njit(cache=True)
def _build_core_prange(pos, order, leaf_size, max_cells,
                      cell_min, cell_max, cell_child, cell_is_leaf,
                      cell_leaf_start, cell_leaf_count, pstart, pend):
    """Level-synchronous prange BFS mirroring build_octree exactly. Returns #cells created."""
    n = pos.shape[0]

    # -- root (id 0), serial: exact min/max over all points + pad (mirrors _pad_bounds) ----
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

    # Two FIXED-SIZE parent buffers (a later level can be wider than an earlier one).
    parents = np.empty(max_cells, dtype=np.int64); nxt_buf = np.empty(max_cells, dtype=np.int64)
    nL = 1; parents[0] = 0
    ncells = 1

    while nL > 0:
        # ---- PASS 1 (prange): partition each parent's disjoint range; count children -------
        kcnt = np.empty(nL, dtype=np.int32)
        stg_min = np.empty((nL * 8, 3), dtype=np.float32)
        stg_max = np.empty((nL * 8, 3), dtype=np.float32)
        stg_s = np.empty(nL * 8, dtype=np.int64); stg_e = np.empty(nL * 8, dtype=np.int64)
        stg_code = np.empty(nL * 8, dtype=np.int32)
        for i in prange(nL):
            c = parents[i]
            start = pstart[c]; end = pend[c]; m = end - start
            if m <= leaf_size:
                cell_is_leaf[c] = 1; cell_leaf_start[c] = int(start); cell_leaf_count[c] = int(m)
                kcnt[i] = 0
                continue
            mid = np.empty(3, dtype=np.float32)
            for d in range(3):
                mid[d] = np.float32(0.5) * (cell_min[c, d] + cell_max[c, d])
            cs = np.empty(8, dtype=np.int32); ce = np.empty(8, dtype=np.int32)
            cm = np.full((8, 3), np.inf, dtype=np.float32); cx = np.full((8, 3), -np.inf, dtype=np.float32)
            _partition_and_bounds(pos, order, start, end, mid, cs, ce, cm, cx)
            n_nonempty = 0
            for code in range(8):
                if cs[code] != ce[code]:
                    n_nonempty += 1
            if n_nonempty == 1:                       # coincident guard (single point)
                cell_is_leaf[c] = 1; cell_leaf_start[c] = int(start); cell_leaf_count[c] = int(m)
                kcnt[i] = 0
                continue
            j = 0
            for code in range(8):
                s = cs[code]; e = ce[code]
                if s == e:
                    continue
                r = i * 8 + j                     # per-parent staging row (threads race otherwise)
                stg_min[r, 0] = cm[code, 0]; stg_min[r, 1] = cm[code, 1]; stg_min[r, 2] = cm[code, 2]
                stg_max[r, 0] = cx[code, 0]; stg_max[r, 1] = cx[code, 1]; stg_max[r, 2] = cx[code, 2]
                stg_s[r] = s; stg_e[r] = e; stg_code[r] = code
                j += 1
            kcnt[i] = j

        # ---- PASS 2: prefix sum over child counts -> base id per parent (serial, tiny) -----
        base = np.empty(nL + 1, dtype=np.int64); base[0] = ncells
        for i in range(nL):
            base[i + 1] = base[i] + kcnt[i]

        # ---- PASS 3 (prange): commit children at cid = base[parent] + local j --------------
        nnew = int(base[nL] - base[0])            # total new cells this level
        next_parents = nxt_buf
        for i in prange(nL):
            if kcnt[i] == 0:
                continue
            c = parents[i]
            off = int(base[i] - base[0])          # level-relative offset of parent i's block
            for j in range(kcnt[i]):
                r = i * 8 + j
                cbmin0 = stg_min[r, 0]; cbmin1 = stg_min[r, 1]; cbmin2 = stg_min[r, 2]
                cbmax0 = stg_max[r, 0]; cbmax1 = stg_max[r, 1]; cbmax2 = stg_max[r, 2]
                cspan = 0.0
                dd0 = cbmax0 - cbmin0; dd1 = cbmax1 - cbmin1; dd2 = cbmax2 - cbmin2
                if dd0 > cspan:
                    cspan = dd0
                if dd1 > cspan:
                    cspan = dd1
                if dd2 > cspan:
                    cspan = dd2
                # f64 multiply then cast (mirrors _pad_bounds exactly)
                ceps = np.float32(np.float64(1e-6) * (np.float64(1.0) if cspan < 1.0 else np.float64(cspan)))
                cid = base[i] + j
                cell_min[cid, 0] = cbmin0 - ceps; cell_max[cid, 0] = cbmax0 + ceps
                cell_min[cid, 1] = cbmin1 - ceps; cell_max[cid, 1] = cbmax1 + ceps
                cell_min[cid, 2] = cbmin2 - ceps; cell_max[cid, 2] = cbmax2 + ceps
                for k in range(8):
                    cell_child[cid, k] = -1
                cell_is_leaf[cid] = 0; cell_leaf_start[cid] = -1; cell_leaf_count[cid] = 0
                pstart[cid] = stg_s[r]; pend[cid] = stg_e[r]
                cell_child[c, stg_code[r]] = cid
                next_parents[off + j] = cid

        ncells = base[nL]
        tmp = parents; parents = nxt_buf; nxt_buf = tmp   # swap fixed-size buffers
        nL = nnew                                          # total children this level

    return ncells


def build_octree_prange(positions: np.ndarray, leaf_size: int = 16) -> dict:
    """Level-synchronous prange adaptive octree build, byte-identical to ``build_octree``.

    Returns a dict with exactly the same keys/values as ``build_octree`` (see bh_draw).
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
    cell_leaf_start = np.full(max_cells, -1, np.int32); cell_leaf_count = np.zeros(max_cells, np.int32)
    pstart = np.zeros(max_cells, np.int64); pend = np.zeros(max_cells, np.int64)

    ncells = _build_core_prange(pos, order, leaf_size, max_cells, cell_min, cell_max, cell_child,
                                cell_is_leaf, cell_leaf_start, cell_leaf_count, pstart, pend)

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
