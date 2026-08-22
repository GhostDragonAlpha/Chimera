"""Convert GaussianAnything 2D-surfel .npy output to .splat format.

The .npy array has shape (1, N, 13) or (N, 13):
  [0:3]  means3D (x, y, z)
  [3:4]  opacity
  [4:6]  2D scales (scale_x, scale_y)
  [6:10] rotation quaternion (w, x, y, z)
  [10:13] RGB

We re-pack it into the (N, 14) layout expected by ChimeraEngine's save_splat:
  [x, y, z, r, g, b, a, sx, sy, sz, qw, qx, qy, qz]
For 2D surfels the third scale is set to a small value so the viewer renders
an ellipsoid instead of a flat disk.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("npy", help="Input .npy file from GaussianAnything stage-2")
    parser.add_argument("--out", required=True, help="Output .splat file")
    parser.add_argument("--z-scale", type=float, default=0.01,
                        help="Third scale component for 2D surfels")
    parser.add_argument("--flip-yz", action="store_true",
                        help="Apply the same x-90/y-180 orientation used by GA gradio")
    args = parser.parse_args()

    data = np.load(args.npy, allow_pickle=True)
    if data.ndim == 3:
        data = data[0]
    N = data.shape[0]

    xyz = data[:, 0:3].astype(np.float64)
    opacity = np.clip(data[:, 3:4].astype(np.float64), 0, 1)
    scales = data[:, 4:6].astype(np.float64)
    rotations = data[:, 6:10].astype(np.float64)
    rgb = np.clip(data[:, 10:13].astype(np.float64), 0, 1)

    if args.flip_yz:
        # Match GA gradio: rotation_matrix_x(-90) then rotation_matrix_y(pi)
        xyz = np.stack([xyz[:, 0], xyz[:, 2], -xyz[:, 1]], axis=1)
        xyz = np.stack([-xyz[:, 0], xyz[:, 1], -xyz[:, 2]], axis=1)

    # Normalize quaternions.
    rot_norm = np.linalg.norm(rotations, axis=1, keepdims=True)
    rot_norm = np.where(rot_norm == 0, 1, rot_norm)
    rotations = rotations / rot_norm

    scale_z = np.minimum(scales[:, 0:1], scales[:, 1:2]) * args.z_scale
    scales_3d = np.concatenate([scales, scale_z], axis=1)

    # Build (N, 14) buffer: x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz
    buf14 = np.concatenate([xyz, rgb, opacity, scales_3d, rotations], axis=1)

    cb.save_splat(args.out, buf14)
    print(f"Wrote {N} surfels to {args.out}")


if __name__ == "__main__":
    main()
