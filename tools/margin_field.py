"""margin_field.py -- measure the splat shell's thickness around a 3DGS blob.

The blob is a surface layer with an empty interior. To place the INNER core and
OUTER membrane (the two CAD shells that encapsulate the material), measure the
alpha-weighted distribution of splats vs. signed distance from the occupancy
surface: positive = outside the body (fur tips), negative = inside (skin side).

Method: voxelize alpha>=amin splats at --cell meters; the occupancy surface is
occupied voxels touching air; outside air is flood-filled from the volume border
so enclosed voids count as INSIDE. Each splat's signed distance = distance to the
nearest surface voxel face, signed by whether its voxel is outside-air.

Usage (from the repo root):
  .venv-gs/Scripts/python.exe tools/margin_field.py models/co3d/co3d_34.splat
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("splat")
    ap.add_argument("--cell", type=float, default=0.002, help="voxel size, meters")
    ap.add_argument("--amin", type=float, default=0.5)
    ap.add_argument("--out", default=None, help="write signed distances .npy")
    a = ap.parse_args()

    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= a.amin]
    pos, alpha = buf[:, 0:3], buf[:, 6]
    print(f"{len(buf)} splats at alpha>={a.amin}")

    lo = pos.min(0) - 4 * a.cell
    vox = np.floor((pos - lo) / a.cell).astype(np.int64)
    dims = vox.max(0) + 8
    occ = np.zeros(dims, dtype=bool)
    occ[tuple(vox.T)] = True
    print(f"grid {tuple(dims)} ({dims.prod() / 1e6:.1f}M voxels), occupied {occ.sum()}")

    from scipy import ndimage
    # outside air: flood from the border through NON-occupied voxels
    outside = np.zeros(dims, dtype=bool)
    border = np.zeros(dims, dtype=bool)
    border[0, :, :] = border[-1, :, :] = True
    border[:, 0, :] = border[:, -1, :] = True
    border[:, :, 0] = border[:, :, -1] = True
    seed = border & ~occ
    outside = ndimage.binary_propagation(seed, mask=~occ)
    inside_void = ~occ & ~outside

    # occupancy surface: occupied voxels adjacent to any non-occupied voxel
    surf = occ & (ndimage.binary_dilation(occ) ^ occ | ndimage.binary_erosion(occ) ^ occ)
    surf_pts = np.argwhere(surf)
    print(f"surface voxels {len(surf_pts)}, interior void voxels {int(inside_void.sum())}")

    from scipy.spatial import cKDTree
    tree = cKDTree(surf_pts)
    d, _ = tree.query(vox)
    d = d * a.cell
    sign = np.where(outside[tuple(vox.T)], 1.0, -1.0)  # splat voxel in outside air = outside
    # splats sitting IN occupied voxels: sign ambiguous; use sub-voxel offset later.
    in_occ = occ[tuple(vox.T)]
    sign = np.where(in_occ, 0.0, sign)
    sd = d * np.where(sign == 0, 1.0, sign)  # occupied splats keep unsigned distance

    for name, sel in [("outside", sign > 0), ("occupied", sign == 0), ("inside-void", sign < 0)]:
        w = alpha[sel]
        if len(w) == 0:
            continue
        dd = sd[sel]
        print(f"{name:12s}: {sel.sum():7d} splats, alpha-mass {w.sum():9.1f}, "
              f"dist p05 {np.percentile(dd, 5) * 1000:6.1f}mm med {np.median(dd) * 1000:6.1f}mm "
              f"p95 {np.percentile(dd, 95) * 1000:6.1f}mm")

    if a.out:
        np.save(a.out, np.concatenate([pos, sd[:, None], alpha[:, None]], axis=1))
        print(f"saved {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
