"""bh_sfc.py -- SFC-keyed parallel octree build for the LightEngine DRAW force (T13).

build_octree (LightEngine/bh_draw.py) is a single-core BFS pinned on one CPU core -- the
visible "one core" the operator keeps seeing. This module builds an octree with the
operator's verbatim algorithm, composed from LightEngine.parlib (off-the-shelf sort/scan;
do NOT hand-roll them):

    map points -> integer grid coords -> 3D Z-order (Morton) key
    (1) parallel stable radix sort of the keys          (parlib.stable_sort_by_key)
    (2) run-detect / prefix to carve the leaf cells     (contiguous runs in sorted order)
    (3) link leaves upward into internal nodes           (bottom-up, vectorized per level)

Output is the SAME dict format build_octree returns so compute_draw_bh consumes it UNCHANGED.

CONSTRUCTION CORRECTNESS (the previous BFS version stranded points):
  * The grid resolution B starts at G^3 >= N (enough cells for every point) and refines
    until occupancy plateaus or <= leaf_size -- DERIVED from the data, never a picked number.
  * Leaves are the maximal constant-cell runs of the SFC-sorted permutation, so they tile
    [0,n) EXACTLY: every point is in exactly one leaf (no dead-end internal node possible).
  * Internal nodes are the occupied ancestors up to root; each has >=1 child by construction.
  * Root is cell index 0 (the kernel hard-codes start=0).

COINCIDENT-POINT CONTRACT (matches build_octree's own guard): a leaf may exceed leaf_size
ONLY when its points are mutually coincident -- the referee makes exactly this oversized
leaf via its ``n_nonempty == 1`` guard, because subdividing identical points recurses forever.
No octree can split coincident points into <= leaf_size leaves; that is a property of the
data, not a builder defect. The gate checks this refined invariant (see tools/gate_octree_sfc.py).

The sort composes from parlib (on-GPU stable radix sort); a numpy fallback keeps it
deterministic on CPU-only hosts. The bottom-up hierarchy assembly is a graph op parlib does
not cover and is done in vectorized numpy (no per-node python loops except the tiny <=16-pt
leaf bbox pass).

Gate: tools/gate_octree_sfc.py -- forces <= 1% rel vs build_octree on cad_bear AND the exact
THE_MILLION uniform scene, plus nesting / com-mass / coincident-leaf invariants.
"""
from __future__ import annotations

import math

import numpy as np


# ────────────────────────────────────────────────────────────────────────────────
def _zorder_key(ix: np.ndarray, iy: np.ndarray, iz: np.ndarray, B: int) -> np.ndarray:
    """Interleave B bits of each axis into one int64 Morton/Z-order key (injective)."""
    n = ix.shape[0]
    key = np.zeros(n, dtype=np.int64)
    for p in range(B):
        key |= (((ix >> p) & 1).astype(np.int64)) << (3 * p)
        key |= (((iy >> p) & 1).astype(np.int64)) << (3 * p + 1)
        key |= (((iz >> p) & 1).astype(np.int64)) << (3 * p + 2)
    return key


def _start_B(n: int) -> int:
    """Smallest B with G^3 >= N (enough fine cells for every point to be alone)."""
    if n <= 0:
        return 1
    B = max(1, int(math.ceil(math.log2(max(1, n)) / 3.0)))
    while (8 ** B) < n:      # guard against float rounding at the boundary
        B += 1
    return B


def _stable_argsort(key: np.ndarray) -> np.ndarray:
    """Stable ascending argsort of int64 keys. GPU via parlib when available, else numpy."""
    try:
        import cupy as cp
        from LightEngine import parlib
        perm_dev = parlib.stable_sort_by_key(cp.asarray(key, dtype=np.int64))[0]
        return np.ascontiguousarray(perm_dev.get(), dtype=np.int32)
    except Exception:
        return np.argsort(key, kind="stable").astype(np.int32)


def _empty_tree() -> dict:
    return {
        "cell_min": np.zeros((1, 3), dtype=np.float32),
        "cell_max": np.zeros((1, 3), dtype=np.float32),
        "cell_com": np.zeros((1, 3), dtype=np.float32),
        "cell_mass": np.zeros(1, dtype=np.float32),
        "cell_child": np.full((1, 8), -1, dtype=np.int32),
        "cell_is_leaf": np.ones(1, dtype=np.int32),
        "cell_leaf_start": np.zeros(1, dtype=np.int32),
        "cell_leaf_count": np.zeros(1, dtype=np.int32),
        "sorted_pos": np.zeros((0, 3), dtype=np.float32),
        "sorted_idx": np.empty(0, dtype=np.int32),
        "order": np.empty(0, dtype=np.int32),
        "n_cells": 1,
    }


def _grid(pos: np.ndarray, B: int):
    """Map pos into a G^3 grid at resolution B; return (ix,iy,iz,key) int64 arrays."""
    G = 1 << B
    lo = pos.min(axis=0).astype(np.float64)
    hi = pos.max(axis=0).astype(np.float64)
    span = np.maximum(hi - lo, 1e-30)
    f = (pos.astype(np.float64) - lo[None]) / span[None] * float(G)
    ix = np.clip(np.floor(f[:, 0]).astype(np.int64), 0, G - 1)
    iy = np.clip(np.floor(f[:, 1]).astype(np.int64), 0, G - 1)
    iz = np.clip(np.floor(f[:, 2]).astype(np.int64), 0, G - 1)
    key = _zorder_key(ix, iy, iz, B)
    return ix, iy, iz, key


# ────────────────────────────────────────────────────────────────────────────────
def build_octree_sfc(positions: np.ndarray, leaf_size: int = 16) -> dict:
    """Build an SFC-keyed octree in the exact ``build_octree`` dict format."""
    pos = np.ascontiguousarray(np.asarray(positions), dtype=np.float32)
    n = pos.shape[0]
    if n == 0:
        return _empty_tree()

    # (a) grid resolution: start at G^3 >= N, refine until occupancy plateaus or <= leaf_size.
    #     Plateau = residual over-occupancy is true coincidence (no finer grid separates it),
    #     which the referee also keeps in one oversized leaf. Deterministic, no free number.
    B = _start_B(n)
    ix, iy, iz, key = _grid(pos, B)
    _, occ = np.unique(key, return_counts=True)      # distinct-cell max count
    prev_occ = int(occ.max())
    while True:
        B += 1
        ix, iy, iz, key = _grid(pos, B)
        _, occ = np.unique(key, return_counts=True)
        cur_occ = int(occ.max())
        if cur_occ <= leaf_size or cur_occ == prev_occ:   # good enough OR plateaued (coincidence floor)
            break
        prev_occ = cur_occ

    G = 1 << B
    pos_o = np.ascontiguousarray(pos[order := _stable_argsort(key).astype(np.int32)], dtype=np.float32)

    # (c) run-detect leaf cells: same-cell points are contiguous in `order`.
    cid = iz * (G * G) + iy * G + ix                   # unique int per fine cell
    cid_s = cid[order]
    change = np.empty(n, dtype=bool); change[0] = True; change[1:] = cid_s[1:] != cid_s[:-1]
    starts = np.flatnonzero(change).astype(np.int32)
    counts = (np.diff(np.append(starts, n))).astype(np.int32)
    M_B = int(starts.shape[0])

    first_pt = order[starts]                           # each run's first point index
    leaf_ix = ix[first_pt].astype(np.int64); leaf_iy = iy[first_pt].astype(np.int64)
    leaf_iz = iz[first_pt].astype(np.int64)

    # (d) bottom-up hierarchy: leaves (level B) -> root (level 0). Local ids per level.
    lvl_coords = [None] * (B + 1)                      # (M_l,3) int64 coords at each level
    lvl_children = [None] * (B + 1)                   # (M_l,8) local child ids, -1 empty
    lvl_coords[B] = np.stack([leaf_ix, leaf_iy, leaf_iz], axis=1).astype(np.int64)

    for P in range(B - 1, -1, -1):                    # parent level P from children at P+1
        cx, cy, cz = lvl_coords[P + 1][:, 0], lvl_coords[P + 1][:, 1], lvl_coords[P + 1][:, 2]
        Gp = 1 << P                                   # parent grid size at level P (2^P)
        px, py, pz = cx >> 1, cy >> 1, cz >> 1       # child -> parent coords
        paddr = (pz * (Gp * Gp) + py * Gp + px).astype(np.int64)
        uniq_p, inv = np.unique(paddr, return_inverse=True)   # child -> parent local id
        M_l = int(uniq_p.shape[0])
        lvl_coords[P] = np.stack([
            (uniq_p % Gp).astype(np.int64),
            ((uniq_p // Gp) % Gp).astype(np.int64),
            (uniq_p // (Gp * Gp)).astype(np.int64)], axis=1)
        child_local = np.arange(lvl_coords[P + 1].shape[0], dtype=np.int32)
        octant = ((cx & 1).astype(np.int64) * 4 | (cy & 1).astype(np.int64) * 2
                  | (cz & 1).astype(np.int64)).astype(np.int32)   # x=4,y=2,z=1 (referee convention)
        ch = np.full((M_l, 8), -1, dtype=np.int32)
        ch[inv.astype(np.int32), octant] = child_local          # unique (parent,octant) -> safe scatter
        lvl_children[P] = ch

    # Global ids: root (level 0) MUST be index 0; levels concatenated after it.
    M_per_lvl = [int(lvl_coords[ell].shape[0]) for ell in range(B + 1)]
    offset = np.concatenate([[0], np.cumsum(M_per_lvl[:-1])]).astype(np.int64)   # offset[level]
    n_cells = int(offset[-1] + M_per_lvl[-1])

    cell_min = np.zeros((n_cells, 3), dtype=np.float32)
    cell_max = np.zeros((n_cells, 3), dtype=np.float32)
    cell_com = np.zeros((n_cells, 3), dtype=np.float32)
    cell_mass = np.zeros(n_cells, dtype=np.float32)
    cell_child = np.full((n_cells, 8), -1, dtype=np.int32)
    cell_is_leaf = np.zeros(n_cells, dtype=np.int32)
    cell_leaf_start = np.full(n_cells, -1, dtype=np.int32)
    cell_leaf_count = np.zeros(n_cells, dtype=np.int32)

    # Child links (global ids).
    for P in range(B - 1, -1, -1):
        par_g = offset[P] + np.arange(M_per_lvl[P], dtype=np.int64)
        chd_g = offset[P + 1] + lvl_children[P].astype(np.int64)          # (M_P,8), -1 stays
        for o in range(8):
            sel = lvl_children[P][:, o] >= 0
            if sel.any():
                cell_child[par_g[sel].astype(np.int32), o] = chd_g[sel, o].astype(np.int32)

    # Leaf ranges (global ids).
    leaf_g = offset[B] + np.arange(M_B, dtype=np.int64)
    cell_is_leaf[leaf_g.astype(np.int32)] = 1
    cell_leaf_start[leaf_g.astype(np.int32)] = starts
    cell_leaf_count[leaf_g.astype(np.int32)] = counts

    # (e) com / mass / min / max, bottom-up (children already filled when parent reads).
    for j in range(M_B):                                   # leaves (level B)
        seg = pos_o[starts[j]:starts[j] + counts[j]]
        g = int(leaf_g[j])
        cell_com[g, 0] = float(seg[:, 0].mean()); cell_com[g, 1] = float(seg[:, 1].mean())
        cell_com[g, 2] = float(seg[:, 2].mean()); cell_mass[g] = float(counts[j])
        cell_min[g, 0] = float(seg[:, 0].min()); cell_max[g, 0] = float(seg[:, 0].max())
        cell_min[g, 1] = float(seg[:, 1].min()); cell_max[g, 1] = float(seg[:, 1].max())
        cell_min[g, 2] = float(seg[:, 2].min()); cell_max[g, 2] = float(seg[:, 2].max())

    for P in range(B - 1, -1, -1):                        # internal nodes (level P from children at P+1)
        g = offset[P] + np.arange(M_per_lvl[P], dtype=np.int64)          # global ids this level
        chd_g = offset[P + 1] + lvl_children[P].astype(np.int64)       # (M_P,8) local->global
        sx = np.zeros(M_per_lvl[P]); sy = np.zeros(M_per_lvl[P]); sz = np.zeros(M_per_lvl[P])
        tm = np.zeros(M_per_lvl[P])
        mn = np.full((M_per_lvl[P], 3), np.inf); mx = np.full((M_per_lvl[P], 3), -np.inf)
        for o in range(8):
            sel = lvl_children[P][:, o] >= 0
            if not sel.any():
                continue
            par = np.nonzero(sel)[0]                                  # parent local ids (this level)
            chg = chd_g[sel, o].astype(np.int64)                     # child global ids
            cm = cell_mass[chg]; ccx = cell_com[chg, 0]; ccy = cell_com[chg, 1]; ccz = cell_com[chg, 2]
            np.add.at(sx, par, cm * ccx); np.add.at(sy, par, cm * ccy); np.add.at(sz, par, cm * ccz)
            np.add.at(tm, par, cm)
            for ax in range(3):
                np.minimum.at(mn[:, ax], par, cell_min[chg, ax])
                np.maximum.at(mx[:, ax], par, cell_max[chg, ax])
        nz = tm > 0
        idx = np.where(nz)[0]                    # LOCAL parent ids (scratch arrays are local-indexed)
        gidx = g[idx]                          # -> GLOBAL ids for the cell_* writes
        cell_com[gidx, 0] = (sx[nz] / tm[nz]).astype(np.float32)
        cell_com[gidx, 1] = (sy[nz] / tm[nz]).astype(np.float32)
        cell_com[gidx, 2] = (sz[nz] / tm[nz]).astype(np.float32)
        cell_mass[gidx] = tm[nz].astype(np.float32)
        cell_min[gidx] = mn[nz].astype(np.float32); cell_max[gidx] = mx[nz].astype(np.float32)

    # Tiny pad (mirror referee _pad_bounds) so boundary points stay inside their cell.
    ext = np.maximum(cell_max - cell_min, 0.0)
    pad = (1e-6 * np.maximum(1.0, ext.max(axis=1)))[:, None]
    cell_min -= pad; cell_max += pad

    return {
        "cell_min": cell_min.astype(np.float32),
        "cell_max": cell_max.astype(np.float32),
        "cell_com": cell_com,
        "cell_mass": cell_mass,
        "cell_child": cell_child,
        "cell_is_leaf": cell_is_leaf,
        "cell_leaf_start": cell_leaf_start,
        "cell_leaf_count": cell_leaf_count,
        "sorted_pos": pos_o.astype(np.float32),
        "sorted_idx": order.astype(np.int32),
        "order": order.astype(np.int32),
        "n_cells": n_cells,
    }


if __name__ == "__main__":
    # Fast self-check (no model needed): SFC tree vs build_octree on a small uniform scene.
    from LightEngine.bh_draw import build_octree, compute_draw_bh, relative_error

    rng = np.random.default_rng(0)
    for n in (2048, 50_003):
        p = rng.uniform(0.0, 1.0, (n, 3)).astype(np.float32)
        t_ref = build_octree(p, leaf_size=16)
        t_sfc = build_octree_sfc(p, leaf_size=16)
        a_ref = compute_draw_bh(p, tree=t_ref, leaf_size=16)
        a_sfc = compute_draw_bh(p, tree=t_sfc, leaf_size=16)
        rel = relative_error(a_sfc, a_ref)
        part = int(t_sfc["cell_leaf_count"][t_sfc["cell_is_leaf"] == 1].sum())
        print(f"n={n}  ref_cells={t_ref['n_cells']} sfc_cells={t_sfc['n_cells']} "
              f"partition={part}/{n} rel_err={rel*100:.4f}% gate(<=1%)={rel <= 0.01}")
