"""
splat_lod — spatial LOD merger for the fractal splat pipeline (CPU, numpy).

Groups nearby splats into clusters when camera distance exceeds threshold,
averaging their attributes into aggregate Gaussians. The merged output feeds
the existing tile-batch rasterizer.

The fractal property: at distance, many splats become one. Zoom in, they
resolve. The merge is a weighted average — LOD of meaning, not decimation.

Algorithm:
  1. Bin splats into a 3D grid (cell size grows with distance)
  2. For each cell with >1 splat, compute weighted mean of attributes
     (weight = alpha, so transparent splats contribute less)
  3. Output the merged list — fewer splats, same visual appearance
  4. Pass through non-array fields (tissue, counts) unmodified

Usage:
    from core.splat_lod import merge
    merged = merge(splats, camera_distance)
"""
from __future__ import annotations

import math
import numpy as np

# Fields that get merged by weighted average
_MERGE_KEYS = {
    "pos", "normal", "albedo", "alpha", "subsurface",
    "roughness", "metallic", "t1", "t2", "r1", "r2",
}

# Fields that need special handling
_COV_KEY = "cov"  # 3x3 per splat


def merge(splats: dict, distance: float, base_cell_size: float = 5.0,
          min_splats: int = 2) -> dict:
    """Merge nearby splats into aggregate Gaussians.

    Uses EXPONENTIAL distance-to-LOD mapping so splats at extreme range
    (e.g. 50km) don't collapse to a single cell.  Cell size doubles every
    `min_dist` units of distance instead of growing linearly.

    Parameters
    ----------
    splats : dict
        Splat dictionary from emit_limb().
    distance : float
        Camera distance (determines cell size).
    base_cell_size : float
        Cell size at reference distance. Grows exponentially with distance.
    min_splats : int
        Minimum splats per cell to merge (2 = always merge).

    Returns
    -------
    dict
        Merged splat dictionary with same keys as input.
    """
    n = len(splats["pos"])
    if n == 0:
        return dict(splats)

    # Exponential LOD: lod_level doubles cell size every `min_dist` units
    min_dist = 10.0  # reference distance where LOD level = 0
    lod_level = int(math.log2(max(max(distance, 1.0) / min_dist, 1.0)))
    cell_size = base_cell_size * (2.0 ** lod_level)
    pos = splats["pos"].astype(np.float64)

    # Assign each splat to a cell
    cell = np.floor(pos / max(cell_size, 1e-8))
    cell_id = ((cell[:, 0] + 2**20).astype(np.int64) << 42 |
               (cell[:, 1] + 2**20).astype(np.int64) << 21 |
               (cell[:, 2] + 2**20).astype(np.int64))
    perm = np.argsort(cell_id, kind="stable")
    cell_sorted = cell_id[perm]

    # Find cell boundaries
    change = np.diff(cell_sorted, prepend=cell_sorted[0] - 1) != 0
    starts = np.where(change)[0]
    ends = np.concatenate([starts[1:], [n]])
    n_cells = len(starts)

    # Build output
    out = {}
    idx_dtype = splats["pos"].dtype  # preserve pos dtype (int64)

    for k in splats:
        v = splats[k]
        if isinstance(v, np.ndarray):
            # Determine shape: for 1D arrays like alpha, after merge shape is (n_cells,)
            # For 2D like pos (n,3), after merge shape is (n_cells, 3)
            new_shape = (n_cells,) + v.shape[1:]
            out[k] = np.empty(new_shape, dtype=np.float64)
        else:
            out[k] = v  # pass through non-array fields (tissue, counts)

    alphas = splats["alpha"]
    for i, (s, e) in enumerate(zip(starts, ends)):
        idx = perm[s:e]
        count = e - s

        if count < min_splats:
            # Single splat — pass through (cast to float64 for consistency)
            for k in _MERGE_KEYS:
                if k in splats:
                    out[k][i] = splats[k][idx[0]].astype(np.float64)
            if _COV_KEY in splats:
                out[_COV_KEY][i] = splats[_COV_KEY][idx[0]].astype(np.float64)
        else:
            # Weighted merge (weight by alpha)
            w = alphas[idx].astype(np.float64)
            w /= max(w.sum(), 1e-10)
            for k in _MERGE_KEYS:
                if k in splats:
                    vals = splats[k][idx].astype(np.float64)
                    if vals.ndim == 2:
                        out[k][i] = vals.T @ w
                    else:
                        out[k][i] = (vals * w).sum()
            if _COV_KEY in splats:
                covs = splats[_COV_KEY][idx].astype(np.float64)
                out[_COV_KEY][i] = np.einsum('nij,n->ij', covs, w)

    return out
