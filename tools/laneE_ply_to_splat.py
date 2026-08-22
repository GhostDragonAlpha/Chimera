"""tools/laneE_ply_to_splat.py

Convert the refined PLY (already in the viewer's orient=0 frame) directly to a .splat
without re-PCA-ing. The Lane E refinement initialized from laneD_diffsplat.splat and
froze means, so the refined cloud is already oriented and normalized. Re-running
orient_splat.py would re-align PCA axes and change the viewing orientation.

Applies the same cleaning filters as the requested orient_splat step:
  alpha >= 0.1, mean RGB >= 0.10, density-k >= 3, largest blob keep.
Opacity is raw (0..1) as exported by anysplat_refine.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from plyfile import PlyData

ROOT = Path(__file__).resolve().parent.parent
C0 = 0.28209479177387814


def load_ply_raw(path: str):
    v = PlyData.read(path)["vertex"].data
    pos = np.stack([v["x"], v["y"], v["z"]], axis=1).astype(np.float64)
    rgb = np.clip(0.5 + C0 * np.stack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]], axis=1), 0, 1)
    alpha = np.clip(v["opacity"], 0, 1)
    scale = np.exp(np.stack([v["scale_0"], v["scale_1"], v["scale_2"]], axis=1))
    rot = np.stack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]], axis=1)
    rot = rot / np.linalg.norm(rot, axis=1, keepdims=True)
    return pos, rgb, alpha, scale, rot


def write_splat(path: str, pos, rgb, alpha, scale, rot):
    n = len(pos)
    dt = np.dtype([
        ("pos", "<f4", 3),
        ("scale", "<f4", 3),
        ("rgba", "u1", 4),
        ("rot", "u1", 4),
    ])
    arr = np.zeros(n, dtype=dt)
    arr["pos"] = pos.astype(np.float32)
    arr["scale"] = scale.astype(np.float32)
    arr["rgba"][:, :3] = (np.clip(rgb, 0, 1) * 255).round().astype(np.uint8)
    arr["rgba"][:, 3] = (np.clip(alpha, 0, 1) * 255).round().astype(np.uint8)
    arr["rot"] = (np.clip(rot, -1, 1) * 128 + 128).round().astype(np.uint8)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(arr.tobytes())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ply", default="models/genbear3/laneE_refined.ply")
    ap.add_argument("--out", default="models/genbear3/laneE_enhanced.splat")
    ap.add_argument("--alpha-min", type=float, default=0.1)
    ap.add_argument("--lum-min", type=float, default=0.10)
    ap.add_argument("--density-k", type=int, default=3)
    ap.add_argument("--blob-keep", action="store_true", default=True)
    args = ap.parse_args()

    pos, rgb, alpha, scale, rot = load_ply_raw(args.ply)
    n0 = len(pos)

    keep = alpha >= args.alpha_min
    pos, rgb, alpha, scale, rot = pos[keep], rgb[keep], alpha[keep], scale[keep], rot[keep]
    print(f"alpha>={args.alpha_min}: {n0} -> {len(pos)}")

    keep = rgb.mean(axis=1) >= args.lum_min
    pos, rgb, alpha, scale, rot = pos[keep], rgb[keep], alpha[keep], scale[keep], rot[keep]
    print(f"lum>={args.lum_min}: {len(pos)}")

    if args.density_k > 1:
        diag = np.linalg.norm(pos.max(0) - pos.min(0))
        cell = max(0.03 * diag, 1e-9)
        vox = np.floor(pos / cell).astype(np.int64)
        _, inv, cnt = np.unique(vox, axis=0, return_inverse=True, return_counts=True)
        keep = cnt[inv] >= args.density_k
        pos, rgb, alpha, scale, rot = pos[keep], rgb[keep], alpha[keep], scale[keep], rot[keep]
        print(f"density (k>={args.density_k}, cell {cell:.4f}): {len(pos)}")

    if args.blob_keep:
        diag = np.linalg.norm(pos.max(0) - pos.min(0))
        cell = max(0.03 * diag, 1e-9)
        keys, inv = np.unique(np.floor(pos / cell).astype(np.int64), axis=0, return_inverse=True)
        idx = {tuple(k): i for i, k in enumerate(keys)}
        parent = list(range(len(keys)))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        offs = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)][13:]
        for i, k in enumerate(keys):
            for o in offs:
                j = idx.get((k[0] + o[0], k[1] + o[1], k[2] + o[2]))
                if j is not None:
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        parent[ri] = rj
        from collections import Counter
        cnt = Counter(find(inv[i]) for i in range(len(pos)))
        main = max(cnt, key=cnt.get)
        keep = np.array([find(inv[i]) == main for i in range(len(pos))])
        pos, rgb, alpha, scale, rot = pos[keep], rgb[keep], alpha[keep], scale[keep], rot[keep]
        print(f"blob: {len(pos)}")

    write_splat(args.out, pos, rgb, alpha, scale, rot)
    print(f"wrote {args.out} ({len(pos)} splats)")
    return 0


if __name__ == "__main__":
    import argparse
    raise SystemExit(main())
