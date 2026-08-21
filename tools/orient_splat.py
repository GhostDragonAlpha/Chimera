"""orient_splat.py — trained 3DGS PLY (+ carve/crop) -> oriented, normalized .splat.

The export stage of the capture pipeline (video_to_splat -> silhouette_carve -> THIS).
Takes the raw trained PLY (gsplat normalized world frame), optionally applies a keep-mask
from tools/silhouette_carve.py, crops low-alpha splats, then orients the cloud:

  1. PCA on positions: largest eigenvector = the figure's long axis -> maps to +Y (up).
     The next two span the horizontal plane; the one with the larger spread maps to X
     (arms), the smaller to Z (front/back depth).
  2. Sign ambiguities are NOT decidable from geometry alone (head vs feet, front vs back),
     so --flip-up / --flip-front are explicit, decided by an eye-check render through the
     engine after the first export.
  3. Recenters on the cloud centroid and scales so height (Y extent) = --height.

Usage (from the repo root, pipeline venv):
    .venv/Scripts/python.exe tools/orient_splat.py capture/genbear2/train_out/ply/point_cloud_29999.ply \
        --mask capture/genbear2/carve_keep.npy --out models/genbear2/genbear2.splat
    # eye-check render, then if needed:
    ... --flip-up --flip-front
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine" / "native"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from ply_to_splat import load_3dgs_ply  # noqa: E402
import cpp_bridge as cb  # noqa: E402


def quat_rotate_matrix(q: np.ndarray) -> np.ndarray:
    """(n,4) [w,x,y,z] quats -> (n,3,3) rotation matrices."""
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    R = np.stack([
        1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
        2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
        2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y),
    ], axis=1).reshape(-1, 3, 3)
    return R


def matrix_to_quat(R: np.ndarray) -> np.ndarray:
    """(n,3,3) -> (n,4) [w,x,y,z], normalized."""
    n = len(R)
    q = np.zeros((n, 4), dtype=np.float64)
    tr = R[:, 0, 0] + R[:, 1, 1] + R[:, 2, 2]
    for i in range(n):
        m = R[i]
        if tr[i] > 0:
            s = np.sqrt(tr[i] + 1.0) * 2
            q[i] = [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
        elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
            q[i] = [(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s]
        elif m[1, 1] > m[2, 2]:
            s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
            q[i] = [(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s]
        else:
            s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
            q[i] = [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s]
    return q / np.linalg.norm(q, axis=1, keepdims=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ply", help="trained 3DGS .ply (gsplat normalized world frame)")
    ap.add_argument("--out", required=True, help="output .splat")
    ap.add_argument("--mask", help="keep-mask .npy from silhouette_carve.py (PLY row order)")
    ap.add_argument("--alpha-min", type=float, default=0.1, help="crop splats below this alpha")
    ap.add_argument("--height", type=float, default=1.0, help="target Y extent after normalization")
    ap.add_argument("--flip-up", action="store_true", help="rotate 180 deg about Z (head/feet swap)")
    ap.add_argument("--flip-front", action="store_true", help="rotate 180 deg about Y (front/back swap)")
    ap.add_argument("--no-envelope", action="store_true", help="skip the teddy-envelope junk filter")
    ap.add_argument("--max-aniso", type=float, default=50.0, help="envelope: max scale anisotropy (teddy max is 47)")
    ap.add_argument("--max-size-frac", type=float, default=0.01, help="envelope: max splat size as a fraction of the diagonal")
    ap.add_argument("--opacity-raw", action="store_true", help="PLY stores raw alpha, not a logit (AnySplat exports)")
    ap.add_argument("--lum-min", type=float, default=0.0, help="crop splats darker than this mean RGB (kills black-background reconstruction)")
    ap.add_argument("--rx", type=float, default=0.0, help="extra rotation about X in degrees, applied after PCA (PCA puts the widest axis up — wrong for a T-pose)")
    ap.add_argument("--ry", type=float, default=0.0, help="extra rotation about Y in degrees")
    ap.add_argument("--rz", type=float, default=0.0, help="extra rotation about Z in degrees")
    ap.add_argument("--density-k", type=int, default=1, help="keep only splats in voxels with >= k splats (kills isolated debris; 1 = off)")
    ap.add_argument("--density-cell", type=float, default=0.02, help="density voxel size as a fraction of the bbox diagonal")
    ap.add_argument("--extrinsic-up", help="AnySplat *_extrinsic.npy: take world-up from the camera ring (gravity) instead of trusting PCA's longest axis")
    ap.add_argument("--pinned", action="store_true", help="THE SPACE: the cloud is already in the commanded canonical frame (+Y up, +Z front). No PCA, no rotation -- recenter + metric scale only, and write a space.json sidecar.")
    ap.add_argument("--radial-keep", type=float, default=0.0, help="keep splats within K x the 90th-percentile distance from the median center (kills sparse far debris)")
    ap.add_argument("--blob-keep", action="store_true", help="keep only the largest 26-connected voxel blob (operator's smart-clip: latch the main blob, drop disconnected junk)")
    ap.add_argument("--blob-cell", type=float, default=0.03, help="blob voxel size as a fraction of the bbox diagonal")
    a = ap.parse_args()

    if a.ply.endswith(".splat"):
        buf = cb.load_splat(a.ply).astype(np.float64)
    else:
        buf = load_3dgs_ply(a.ply, opacity_raw=a.opacity_raw).astype(np.float64)
    if a.lum_min > 0:
        n_pre = len(buf)
        buf = buf[buf[:, 3:6].mean(1) >= a.lum_min]
        print(f"lum>={a.lum_min}: {n_pre} -> {len(buf)}")
    n0 = len(buf)
    if a.mask:
        keep = np.load(a.mask)
        assert len(keep) == n0, f"mask {len(keep)} != ply {n0}"
        buf = buf[keep]
    n_mask = len(buf)
    buf = buf[buf[:, 6] >= a.alpha_min]
    print(f"{n0} -> mask {n_mask} -> alpha>={a.alpha_min} {len(buf)}")

    # TEDDY ENVELOPE (measured 2026-08-19 on models/triposplat/static/viewer/teddy.splat,
    # the known-good cloud): a healthy 3DGS plush has max anisotropy 47 (99% under 11) and
    # 99% of splats smaller than 1% of the object diagonal. AI-video-trained clouds grow
    # needles at aniso 150+ and oversized billboards — OUTSIDE the envelope, i.e. junk by
    # definition. Cut them BEFORE PCA, or they steer the eigenvectors (the flat-pancake bug).
    if not a.no_envelope:
        s3 = buf[:, 7:10]
        aniso = s3.max(1) / np.maximum(s3.min(1), 1e-12)
        diag = np.linalg.norm(buf[:, 0:3].max(0) - buf[:, 0:3].min(0))
        bad = (aniso > a.max_aniso) | (s3.max(1) > a.max_size_frac * diag)
        buf = buf[~bad]
        print(f"envelope (aniso>{a.max_aniso:g}, size>{a.max_size_frac:g}x diag): cut {int(bad.sum())} -> {len(buf)}")

    pos = buf[:, 0:3]
    if a.density_k > 1:
        # voxel-density cut: the subject is a dense blob; reconstruction debris is isolated
        diag_d = np.linalg.norm(pos.max(0) - pos.min(0))
        cell = max(a.density_cell * diag_d, 1e-9)
        vox = np.floor(pos / cell).astype(np.int64)
        _, inv, cnt = np.unique(vox, axis=0, return_inverse=True, return_counts=True)
        keep = cnt[inv] >= a.density_k
        print(f"density (k>={a.density_k}, cell {cell:.4f}): cut {int((~keep).sum())} -> {int(keep.sum())}")
        buf = buf[keep]
        pos = buf[:, 0:3]
    if a.blob_keep:
        # largest-blob smart-clip: union-find over occupied voxels (26-connectivity).
        diag_b = np.linalg.norm(pos.max(0) - pos.min(0))
        cell_b = max(a.blob_cell * diag_b, 1e-9)
        keys, inv = np.unique(np.floor(pos / cell_b).astype(np.int64), axis=0, return_inverse=True)
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
        print(f"blob (largest of {len(cnt)} components, cell {cell_b:.4f}): cut {int((~keep).sum())} -> {int(keep.sum())}")
        buf = buf[keep]
        pos = buf[:, 0:3]
    if a.radial_keep > 0:
        center_r = np.median(pos, axis=0)
        d = np.linalg.norm(pos - center_r, axis=1)
        lim = a.radial_keep * np.quantile(d, 0.9)
        keep = d <= lim
        print(f"radial (<={lim:.3f}): cut {int((~keep).sum())} -> {int(keep.sum())}")
        buf = buf[keep]
        pos = buf[:, 0:3]
    # robust core for centering: junk that survives the envelope still must not steer it
    lo, hi = np.percentile(pos, [2, 98], axis=0)
    core = pos[(pos >= lo).all(1) & (pos <= hi).all(1)]
    centroid = core.mean(0)
    centered = pos - centroid
    if a.pinned:
        # THE SPACE: orientation comes from the capture rig's commanded poses, which the
        # cloud already sits in. Rotation is identity; we only recenter and scale.
        R = np.eye(3)
        print("pinned frame: R = identity (commanded orbit is the frame; no PCA)")
    else:
        eigval, eigvec = np.linalg.eigh(np.cov(core - centroid, rowvar=False))
        order = eigval.argsort()[::-1]              # large -> small
        V = eigvec[:, order]                        # columns: long-axis, mid, small
        if np.linalg.det(V) < 0:
            V[:, 2] *= -1
        if a.extrinsic_up:
            # gravity up from the camera ring: world up = mean of -camera_y (OpenCV y-down).
            # Then the bear's up is anatomy, not "whichever PCA axis was longest" (a T-pose's
            # arm-span beats its height and tips the whole cloud over).
            ext = np.load(a.extrinsic_up).astype(np.float64)
            up = -ext[:, :3, 1].mean(0)
            up /= np.linalg.norm(up)
            x = V[:, 0] - (V[:, 0] @ up) * up
            if np.linalg.norm(x) < 1e-6:
                x = V[:, 1] - (V[:, 1] @ up) * up
            x /= np.linalg.norm(x)
            z = np.cross(x, up)
            z /= np.linalg.norm(z)
            R = np.stack([x, up, z], axis=0)  # world = R @ cloud; rows: X, Y=up, Z
            print(f"extrinsic-up: world up = {np.round(up, 3)}")
        else:
            # rows of R map cloud axes -> world: long -> +Y, mid -> +X, small -> +Z
            R = np.stack([V[:, 1], V[:, 0], V[:, 2]], axis=0)  # world = R @ cloud
            if np.linalg.det(R) < 0:
                R[2] *= -1

    if a.flip_up:
        R = np.array([[-1.0, 0, 0], [0, -1.0, 0], [0, 0, 1.0]]) @ R
    if a.flip_front:
        R = np.array([[-1.0, 0, 0], [0, 1.0, 0], [0, 0, -1.0]]) @ R
    if a.rx:
        c, s_ = np.cos(np.radians(a.rx)), np.sin(np.radians(a.rx))
        R = np.array([[1.0, 0, 0], [0, c, -s_], [0, s_, c]]) @ R
    if a.ry:
        c, s_ = np.cos(np.radians(a.ry)), np.sin(np.radians(a.ry))
        R = np.array([[c, 0, s_], [0, 1.0, 0], [-s_, 0, c]]) @ R
    if a.rz:
        c, s_ = np.cos(np.radians(a.rz)), np.sin(np.radians(a.rz))
        R = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1.0]]) @ R

    pos_o = centered @ R.T
    yspan = pos_o[:, 1].max() - pos_o[:, 1].min()
    s = a.height / yspan
    pos_o *= s
    pos_o[:, 1] -= (pos_o[:, 1].max() + pos_o[:, 1].min()) / 2   # center vertically
    pos_o[:, 0] -= (pos_o[:, 0].max() + pos_o[:, 0].min()) / 2
    pos_o[:, 2] -= (pos_o[:, 2].max() + pos_o[:, 2].min()) / 2

    splat = buf.copy()
    splat[:, 0:3] = pos_o
    splat[:, 7:10] *= s                                          # scales shrink with the cloud
    Rs = quat_rotate_matrix(buf[:, 10:14])
    Rs_o = np.einsum("ij,njk->nik", R, Rs)
    splat[:, 10:14] = matrix_to_quat(Rs_o)

    cb.save_splat(a.out, splat.astype(np.float32))
    print(f"oriented: height {yspan:.3f} -> {a.height}, scale x{s:.4f}, {len(splat)} splats -> {a.out}")
    if a.pinned:
        import json
        sidecar = {
            "units": "meters",
            "up": [0, 1, 0],
            "front": [0, 0, 1],
            "height_m": a.height,
            "transform_to_canonical": ("identity" if not (a.flip_up or a.flip_front or a.rx or a.ry or a.rz)
                                       else "R=" + ",".join(f"{v:.6f}" for v in R.flatten())),
            "provenance": ["orient_splat --pinned", str(a.ply)],
        }
        side_path = Path(a.out).with_suffix(".space.json")
        side_path.write_text(json.dumps(sidecar, indent=2))
        print(f"sidecar -> {side_path}")
    else:
        print("eye-check it through the engine; re-run with --flip-up/--flip-front if wrong")
    return 0


if __name__ == "__main__":
    sys.exit(main())
