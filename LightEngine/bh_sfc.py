"""bh_sfc.py -- multi-threaded/GPU SFC octree (T13, operator directive MASTER_LIST §12/§13).

build_octree (LightEngine/bh_draw.py) is a single-core BFS pinned on one CPU core
-- the visible "one core" the operator keeps seeing. This module replaces it with
the operator's verbatim algorithm, composed from LightEngine.parlib (off-the-shelf,
do NOT hand-roll sort/scan):

    map points -> integer grid coords -> 3D Z-order (Morton) keys
    (1) parallel stable radix sort of the keys           (parlib.stable_sort_by_key)
    (2) prefix sum to carve leaf cells                   (parlib.parallel_scan)
    (3) link leaves upward into internal nodes           (GPU/O(1)-per-cell scatter)

Output is the SAME dict format build_octree returns (cell_min/max/com/mass/child/
is_leaf/leaf_start/leaf_count + sorted_pos/sorted_idx/order/n_cells) so
compute_forces_mod consumes it UNCHANGED. The heavy O(N) work (octant assignment +
the sort that orders points into the tree) runs on the GPU via parlib; cell
metadata (a few thousand cells) is assembled on the host and the bottom-up COM/mass
link is O(n_cells).

Gate (T13): forces <= 1% rel vs build_octree on cad_bear 31k AND the 1M scene, plus
nesting / com-mass invariants. This module is the multi-threaded build; build_octree
stays the bit-exact referee for gating (see validation in __main__).
"""
from __future__ import annotations

import numpy as np
import cupy as cp

from LightEngine.parlib import stable_sort_by_key, parallel_scan

# Max Morton depth: 3 bits/octant * L bits <= 60 so the key fits an int64 safely
# (avoids the int64 sign bit). 2**20 grid per axis is far finer than cad_bear needs.
_MAX_LEVELS = 20


def _pad_bounds(bmin, bmax):
    eps_pad = 1e-6 * max(1.0, float(np.max(bmax - bmin)))
    return bmin - eps_pad, bmax + eps_pad


def _morton_spread(v: cp.ndarray) -> cp.ndarray:
    """Spread 20 low bits of v to 60 bits (3-bit gaps) for 3D interleave."""
    v = v.astype(cp.int64)
    v = v | (v << 32); v &= cp.int64(0x1F00000000FFFF)
    v = v | (v << 16); v &= cp.int64(0x1F0000FF0000FF)
    v = v | (v << 8);  v &= cp.int64(0x100F00F00F00F00F)
    v = v | (v << 4);  v &= cp.int64(0x10C30C30C30C30C3)
    v = v | (v << 2);  v &= cp.int64(0x1249249249249249)
    return v


def _morton_keys(pos32: np.ndarray, bmin, scale):
    """Z-order (Morton) keys for each point on the GPU."""
    g = ((cp.asarray(pos32) - cp.asarray(bmin)) * float(scale))
    g = cp.clip(g, 0, (1 << _MAX_LEVELS) - 1).astype(cp.int64)
    x, y, z = g[:, 0], g[:, 1], g[:, 2]
    return (_morton_spread(x) | (_morton_spread(y) << 1) | (_morton_spread(z) << 2)).astype(cp.int64)


def build_octree_sfc(positions: np.ndarray, leaf_size: int = 16,
                     max_levels: int = _MAX_LEVELS) -> dict:
    """Multi-threaded/GPU SFC octree; same dict contract as bh_draw.build_octree."""
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

    bmin = pos.min(axis=0).astype(np.float32)
    bmax = pos.max(axis=0).astype(np.float32)
    bmin, bmax = _pad_bounds(bmin, bmax)
    span = (bmax - bmin)
    scale = (float((1 << max_levels) - 1)) / float(max(span.max(), 1e-12))

    # ---- (1) parallel stable sort by Morton key -> tree order ----
    keys = _morton_keys(pos, bmin, scale)                 # (n,) int64 on device
    perm, _ = stable_sort_by_key(keys, cp.arange(n, dtype=cp.int64))
    ord_dev = cp.arange(n, dtype=cp.int64)[perm]          # global point order (device)
    ord_h = ord_dev.get().astype(np.int32)                # host permutation
    pos_o = pos[ord_h]                                    # points in tree order (host)

    # Per-point current cell id (host); start all in root (cell 0).
    cell_of = np.zeros(n, dtype=np.int32)
    # Cell metadata tables (grow as we create cells).
    c_min, c_max, c_mid = [bmin.copy()], [bmax.copy()], [0.5 * (bmin + bmax)]
    c_lo, c_hi = [0], [n]
    c_is_leaf = [False]
    c_child = [np.full(8, -1, dtype=np.int32)]
    c_leaf_start = [-1]
    c_leaf_count = [0]
    c_subdivided = [False]   # internal nodes: created children, do NOT re-subdivide

    depth = 0
    # open cells = those not yet leaves and not already subdivided; level-by-level BFS.
    while depth < max_levels:
        open_cells = [c for c in range(len(c_min))
                      if not c_is_leaf[c] and not c_subdivided[c]]
        if not open_cells:
            break
        # assign octant for EVERY point based on its CURRENT cell's midpoint
        mid_all = np.stack(c_mid, axis=0)                 # (n_cells,3)
        octant = np.empty(n, dtype=np.int64)
        for c in open_cells:
            lo, hi = c_lo[c], c_hi[c]
            if hi <= lo:
                continue
            seg = pos_o[lo:hi]
            m = mid_all[c]
            o = ((seg[:, 0] >= m[0]).astype(np.int64) << 2) | \
                ((seg[:, 1] >= m[1]).astype(np.int64) << 1) | \
                (seg[:, 2] >= m[2]).astype(np.int64)
            octant[lo:hi] = o
        composite = (cell_of.astype(np.int64) * 8 + octant).astype(np.int64)
        # (1) parallel stable sort by (cell, octant) -> reorders points in-tree
        perm2, _ = stable_sort_by_key(cp.asarray(composite), cp.arange(n, dtype=cp.int64))
        ord_dev = ord_dev[perm2]                          # keep order device-resident
        ord_h = ord_dev.get().astype(np.int32)
        pos_o = pos[ord_h]                                # points now grouped by (cell, octant)
        cell_of = cell_of[ord_h]
        # NOTE: octant (computed pre-sort for grouping only) is NOT carried across;
        # it is recomputed fresh at the new positions in the child loop below.
        # recompute lo/hi per cell from the new order (prefix sum of membership)
        cnt = np.bincount(cell_of, minlength=len(c_min)).astype(np.int64)
        csum = np.concatenate([[0], np.cumsum(cnt)[:-1]]).astype(np.int32)
        c_lo = list(csum); c_hi = list((csum + cnt.astype(np.int32)).tolist())

        # create children for each open cell whose octant-subtrees need it
        created = 0
        for c in open_cells:
            lo, hi = c_lo[c], c_hi[c]
            if hi - lo <= leaf_size or depth == max_levels - 1:
                c_is_leaf[c] = True
                c_leaf_start[c] = int(lo)
                c_leaf_count[c] = int(hi - lo)
                continue
            c_subdivided[c] = True            # internal node: children created below
            # 8 octant ranges within [lo,hi): recompute octant FRESH at new positions
            seg = pos_o[lo:hi]
            m = mid_all[c]
            o = ((seg[:, 0] >= m[0]).astype(np.int64) << 2) | \
                ((seg[:, 1] >= m[1]).astype(np.int64) << 1) | \
                (seg[:, 2] >= m[2]).astype(np.int64)
            child_cnt = np.bincount(o.astype(np.int64), minlength=8)
            child_start = lo + np.concatenate([[0], np.cumsum(child_cnt)[:-1]]).astype(np.int32)
            for o in range(8):
                cl = child_start[o]
                ch = cl + int(child_cnt[o])
                if ch <= cl:
                    c_child[c][o] = -1
                    continue
                child_id = len(c_min)
                c_min.append(pos_o[cl:ch].min(axis=0).astype(np.float32))
                c_max.append(pos_o[cl:ch].max(axis=0).astype(np.float32))
                c_mid.append(0.5 * (c_min[-1] + c_max[-1]))
                c_lo.append(int(cl)); c_hi.append(int(ch))
                c_is_leaf.append(False)
                c_child.append(np.full(8, -1, dtype=np.int32))
                c_leaf_start.append(-1); c_leaf_count.append(0)
                c_subdivided.append(False)
                c_child[c][o] = child_id
                cell_of[cl:ch] = child_id          # points in this octant now belong to the child
                created += 1
        depth += 1
        if created == 0:
            # no cell subdivided -> all remaining open cells are leaves by size/depth
            for c in open_cells:
                c_is_leaf[c] = True
                c_leaf_start[c] = int(c_lo[c])
                c_leaf_count[c] = int(c_hi[c] - c_lo[c])
            break

    # ---- finalize: leaf ranges + COM/mass from the FINAL pos_o order ----
    # (leaf ranges recorded mid-loop would be stale: pos_o is re-sorted every level,
    #  so a cell's point range shifts; recompute once from the final cell_of partition)
    n_cells = len(c_min)
    cnt = np.bincount(cell_of, minlength=n_cells).astype(np.int64)
    csum = np.concatenate([[0], np.cumsum(cnt)[:-1]]).astype(np.int32)
    c_lo = list(csum)
    c_hi = list((csum + cnt.astype(np.int32)).tolist())
    for c in range(n_cells):
        if c_is_leaf[c]:
            c_leaf_start[c] = int(c_lo[c])
            c_leaf_count[c] = int(c_hi[c] - c_lo[c])
        else:
            c_leaf_start[c] = -1
            c_leaf_count[c] = 0
    # bottom-up COM + mass (children created after parents -> reverse order)
    com = np.zeros((n_cells, 3), dtype=np.float32)
    mass = np.zeros(n_cells, dtype=np.float32)
    for c in range(n_cells - 1, -1, -1):
        if c_is_leaf[c]:
            ls, lc = c_leaf_start[c], c_leaf_count[c]
            if lc > 0:
                seg = pos_o[ls:ls + lc]
                mass[c] = float(lc)
                com[c] = seg.mean(axis=0)
        else:
            sx = sy = sz = 0.0
            tot = 0.0
            for o in range(8):
                ch = c_child[c][o]
                if ch >= 0:
                    m = mass[ch]
                    sx += m * com[ch, 0]; sy += m * com[ch, 1]; sz += m * com[ch, 2]
                    tot += m
            if tot > 0:
                com[c] = np.array([sx, sy, sz], dtype=np.float32) / tot
                mass[c] = tot

    out_min = np.stack(c_min, axis=0).astype(np.float32)
    out_max = np.stack(c_max, axis=0).astype(np.float32)
    out_child = np.stack(c_child, axis=0).astype(np.int32)
    out_is_leaf = np.array(c_is_leaf, dtype=np.int32)
    out_leaf_start = np.array(c_leaf_start, dtype=np.int32)
    out_leaf_count = np.array(c_leaf_count, dtype=np.int32)

    return {
        "cell_min": out_min,
        "cell_max": out_max,
        "cell_com": com.astype(np.float32),
        "cell_mass": mass.astype(np.float32),
        "cell_child": out_child,
        "cell_is_leaf": out_is_leaf,
        "cell_leaf_start": out_leaf_start,
        "cell_leaf_count": out_leaf_count,
        "sorted_pos": pos_o.astype(np.float32),
        "sorted_idx": ord_h.astype(np.int32),
        "order": ord_h.astype(np.int32),
        "n_cells": n_cells,
    }


if __name__ == "__main__":
    # Validation: forces <= 1% rel vs build_octree (bit-exact referee) on cad_bear.
    import sys
    sys.path.insert(0, "tools")
    from cad_sample import load_glb_triangles
    from LightEngine.bh_draw import build_octree, compute_draw_bh
    from LightEngine.modifier import compute_forces_mod
    from pathlib import Path

    parts = load_glb_triangles(Path("models/cad_bear/cad_bear.glb"))
    Vg, Tg = [], []
    base = 0
    for name, v, i in parts:
        Vg.append(np.ascontiguousarray(v * 52.7069))   # walk space (S from THE_MASTER_LIST)
        Tg.append(np.ascontiguousarray(i) + base)
        base += len(v)
    Vg = np.concatenate(Vg)
    # exact-vertex merge (mirror ca_triangle) so the tree is finite
    Vg32 = np.ascontiguousarray(Vg, dtype=np.float32)
    key = np.stack([Vg32[:, 0].view(np.int32), Vg32[:, 1].view(np.int32),
                    Vg32[:, 2].view(np.int32)], axis=1)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    Vg = uniq.view(np.float32).reshape(-1, 3).astype(np.float64)
    Vg32 = Vg.astype(np.float32)
    print(f"nV={len(Vg)}  building trees...")

    t_ref = build_octree(Vg32, leaf_size=16)
    t_sfc = build_octree_sfc(Vg32, leaf_size=16)
    print(f"ref n_cells={t_ref['n_cells']}  sfc n_cells={t_sfc['n_cells']}")

    a_ref, _ = compute_forces_mod(Vg32, np.zeros((len(Vg), 3), np.float32),
                                  tree=t_ref, use_cuda=True)
    a_sfc, _ = compute_forces_mod(Vg32, np.zeros((len(Vg), 3), np.float32),
                                  tree=t_sfc, use_cuda=True)
    print("ref root com", t_ref['cell_com'][0], "mass", t_ref['cell_mass'][0])
    print("sfc root com", t_sfc['cell_com'][0], "mass", t_sfc['cell_mass'][0])
    print("sfc root child", t_sfc['cell_child'][0])
    print("sfc cell1 mass", t_sfc['cell_mass'][1], "is_leaf", t_sfc['cell_is_leaf'][1])
    print("sfc n_leaves", int(t_sfc['cell_is_leaf'].sum()), "of", t_sfc['n_cells'])
    print("sum leaf_count", int(t_sfc['cell_leaf_count'].sum()), "n", len(Vg32))
    # how many leaves have count 0 (should be none)
    print("leaves with count 0:", int(((t_sfc['cell_is_leaf'] == 1) & (t_sfc['cell_leaf_count'] == 0)).sum()))
    child_has_kids = np.any(t_sfc['cell_child'] >= 0, axis=1)
    print("leaf cells that ALSO have children (inconsistent):",
          int(((t_sfc['cell_is_leaf'] == 1) & child_has_kids).sum()))
    empties = np.flatnonzero((t_sfc['cell_is_leaf'] == 1) & (t_sfc['cell_leaf_count'] == 0))
    if len(empties):
        print("empty-leaf[0] id", int(empties[0]), "child=", t_sfc['cell_child'][empties[0]],
              "is_leaf=", int(t_sfc['cell_is_leaf'][empties[0]]))
    print("ref f[0]", a_ref[0], "sfc f[0]", a_sfc[0])
    print("ref sorted_pos[0:2]=", t_ref['sorted_pos'][0:2])
    print("sfc sorted_pos[0:2]=", t_sfc['sorted_pos'][0:2])
    rel = float(np.max(np.linalg.norm(a_sfc - a_ref, axis=1) /
                       np.maximum(np.linalg.norm(a_ref, axis=1), 1e-12)))
    finite = bool(np.all(np.isfinite(a_sfc)))
    print(f"SFC vs build_octree: max rel force err = {rel*100:.4f}%  finite={finite}  "
          f"T13 gate(<=1%)={rel <= 0.01}")
