"""shell_fit.py -- any 3DGS blob -> INNER core + OUTER membrane (two CAD shells).

Generic by construction: no object knowledge, only geometry. The splat cloud is a
porous surface layer; the body underneath is the volume the layer encloses.

  OUTER    = occupied voxels (largest connected blob only), dilated by
             --outer-mm so fur pores seal, then flood-filled: a TRUE solid at
             membrane level, just outside the fur tips.
  INNER    = that solid eroded by (outer-mm + inner-mm): a smooth generalized
             core -- an offset surface of a sealed solid, so no sponge holes
             (measured 2026-08-21: opening a porous shell hollows the torso).
  MARGIN   = distance from each core surface point to the membrane surface:
             the recorded material thickness field.

Outputs an .npz with both surface point sets + the solid grid metadata, and
(optionally) two .splat visualizations (inner = solid gray, outer = faint shell)
so the membranes can be eye-checked in the viewer like anything else.

Usage (from the repo root):
  .venv-gs/Scripts/python.exe tools/shell_fit.py models/co3d/co3d_34.splat \
      --out models/co3d/bear34_shells.npz --viz models/co3d/bear34
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402


def surface_points(mask: np.ndarray, cell: float, lo: np.ndarray) -> np.ndarray:
    """Surface voxels of a binary volume -> world-space point cloud."""
    from scipy import ndimage
    surf = mask & (ndimage.binary_dilation(mask) ^ mask | ndimage.binary_erosion(mask) ^ mask)
    return (np.argwhere(surf) + 0.5) * cell + lo


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("splat")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cell", type=float, default=0.002, help="voxel size, meters")
    ap.add_argument("--amin", type=float, default=0.3, help="splats below this alpha are not body")
    ap.add_argument("--inner-mm", type=float, default=2.0, help="core sits this far inside the surface")
    ap.add_argument("--outer-mm", type=float, default=10.0, help="membrane sits this far outside (>= p95 margin)")
    ap.add_argument("--viz", default=None, help="write <viz>_inner.splat / <viz>_outer.splat")
    a = ap.parse_args()

    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= a.amin]
    pos = buf[:, 0:3]
    print(f"{len(buf)} body splats at alpha>={a.amin}")

    lo = pos.min(0) - 8 * a.cell
    vox = np.floor((pos - lo) / a.cell).astype(np.int64)
    dims = tuple((vox.max(0) + 16).tolist())
    occ = np.zeros(dims, dtype=bool)
    occ[tuple(vox.T)] = True

    from scipy import ndimage
    struct = ndimage.generate_binary_structure(3, 1)

    # drop disconnected floaters before anything seals them in. The porous shell
    # fragments at voxel level (arms/legs detach from the torso), so keep every
    # component with real mass (>=5% of the largest) -- true debris is tiny.
    lab, nlab = ndimage.label(occ, structure=ndimage.generate_binary_structure(3, 3))
    if nlab > 1:
        sizes = ndimage.sum(occ, lab, range(1, nlab + 1))
        keep_ids = np.nonzero(sizes >= 0.05 * sizes.max())[0] + 1
        occ = np.isin(lab, keep_ids)
        print(f"component keep: {len(keep_ids)} of {nlab} (sizes {sorted(sizes.astype(int), reverse=True)[:6]}...)")

    # outer membrane: dilate (seals fur pores), then flood-fill its interior ->
    # a TRUE solid at membrane level. Eroding that solid by the full margin
    # (r_out + r_in) yields a smooth generalized core in one step -- an offset
    # surface of a sealed solid cannot have the sponge holes that opening a
    # porous shell produced.
    r_out = max(1, round(a.outer_mm / 1000 / a.cell))
    r_in = max(1, round(a.inner_mm / 1000 / a.cell))
    dilated = ndimage.binary_dilation(occ, structure=struct, iterations=r_out)
    border = np.zeros(dims, dtype=bool)
    border[0, :, :] = border[-1, :, :] = True
    border[:, 0, :] = border[:, -1, :] = True
    border[:, :, 0] = border[:, :, -1] = True
    outside = ndimage.binary_propagation(border & ~dilated, mask=~dilated)
    outer_solid = dilated | ~outside
    core = ndimage.binary_erosion(outer_solid, structure=struct, iterations=r_out + r_in)
    if not core.any():
        print("WARN: core vanished under erosion; halving the inner step")
        core = ndimage.binary_erosion(outer_solid, structure=struct, iterations=r_out)
    print(f"grid {dims}, occupied {int(occ.sum())}, outer_solid {int(outer_solid.sum())}, "
          f"core {int(core.sum())} (r_out {r_out} vox, r_in {r_in} vox)")

    inner_pts = surface_points(core, a.cell, lo)
    outer_pts = surface_points(dilated, a.cell, lo)
    print(f"core surface {len(inner_pts)} pts, membrane surface {len(outer_pts)} pts")

    # margin field: distance from each core surface point to the membrane surface
    from scipy.spatial import cKDTree
    d, _ = cKDTree(outer_pts).query(inner_pts)
    print(f"margin (mm): med {np.median(d) * 1000:.1f} p05 {np.percentile(d, 5) * 1000:.1f} "
          f"p95 {np.percentile(d, 95) * 1000:.1f}")

    np.savez_compressed(a.out, inner=inner_pts, outer=outer_pts, margin=d,
                        cell=a.cell, lo=lo, solid=outer_solid)
    print(f"shells -> {a.out}")

    if a.viz:
        def to_splat(pts, rgb, alpha, scale):
            n = len(pts)
            buf = np.zeros((n, 14), dtype=np.float32)
            buf[:, 0:3] = pts
            buf[:, 3:6] = rgb
            buf[:, 6] = alpha
            buf[:, 7:10] = scale
            buf[:, 10] = 1.0  # identity quaternion
            return buf
        cb.save_splat(f"{a.viz}_inner.splat", to_splat(inner_pts, [0.55, 0.55, 0.6], 1.0, a.cell * 1.2))
        cb.save_splat(f"{a.viz}_outer.splat", to_splat(outer_pts, [0.2, 0.5, 0.9], 0.25, a.cell * 1.2))
        print(f"viz -> {a.viz}_inner.splat / {a.viz}_outer.splat (orient=1 in the viewer)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
