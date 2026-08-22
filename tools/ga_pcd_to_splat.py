"""Convert a colored point cloud PLY to a .splat for debugging Lane G.

Reads vertices and vertex colors, assigns a fixed isotropic size and opaque alpha.
The output layout is (N,14) [x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz] and is written
via cpp_bridge.save_splat so the Spark viewer shows it upright with orient=1.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ply", help="Input colored PLY")
    parser.add_argument("--out", required=True)
    parser.add_argument("--size", type=float, default=0.015)
    parser.add_argument("--alpha", type=float, default=1.0)
    args = parser.parse_args()

    mesh = trimesh.load(args.ply)
    xyz = np.asarray(mesh.vertices, dtype=np.float64)
    colors = np.asarray(mesh.visual.vertex_colors, dtype=np.float64)
    rgb = colors[:, :3] / 255.0
    n = xyz.shape[0]

    opacity = np.full((n, 1), args.alpha, dtype=np.float64)
    scales = np.full((n, 3), args.size, dtype=np.float64)
    quat = np.tile(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64), (n, 1))

    buf14 = np.concatenate([xyz, rgb, opacity, scales, quat], axis=1)
    cb.save_splat(args.out, buf14)
    print(f"Wrote {n} points to {args.out}")


if __name__ == "__main__":
    main()
