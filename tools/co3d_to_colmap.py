"""co3d_to_colmap.py -- CO3D sequence (known cameras + masks + real pointcloud)
-> gsplat COLMAP-format dataset. THE SPACE: cameras are MEASURED (validated 99.5%
mask-hit in co3d_to_views.py), the init points are the real SfM cloud, and the
background is masked to black so the trainer spends its gaussians on the bear.

Usage (from the repo root):
  .venv/Scripts/python.exe tools/co3d_to_colmap.py --seq 34_1479_4753 \
      --out capture/co3d/data/34_1479_4753
"""
from __future__ import annotations

import argparse
import math
import shutil
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT / "tools"))
from co3d_to_views import load_sequence  # noqa: E402

META = ROOT / "capture" / "co3d" / "meta" / "teddybear" / "frame_annotations.jgz"
IMAGES_ROOT = ROOT / "capture" / "co3d"  # annotation paths already carry the category dir


def matrix_to_quat_wxyz(R: np.ndarray) -> tuple[float, float, float, float]:
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return (0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s)
    i = int(np.argmax(np.diag(R)))
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(max(1e-12, 1.0 + R[i, i] - R[j, j] - R[k, k])) * 2
    q = [0.0, 0.0, 0.0, 0.0]
    q[0] = (R[k, j] - R[j, k]) / s
    q[1 + i] = 0.25 * s
    q[1 + j] = (R[j, i] + R[i, k]) / s
    q[1 + k] = (R[k, i] + R[i, k]) / s
    return tuple(q)


def read_pointcloud(path: Path, max_points: int, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    with open(path, "rb") as fh:
        header = b""
        while not header.endswith(b"end_header\n"):
            header += fh.readline()
        n = int([l for l in header.decode().splitlines() if l.startswith("element vertex")][0].split()[-1])
        raw = np.fromfile(fh, dtype=np.uint8).reshape(n, 15)  # 3 f32 + 3 u8
    pts = raw[:, :12].copy().view(np.float32).reshape(n, 3).astype(np.float64)
    cols = raw[:, 12:15]
    if n > max_points:
        idx = np.random.default_rng(seed).choice(n, max_points, replace=False)
        pts, cols = pts[idx], cols[idx]
    return pts, cols


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seq", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-points", type=int, default=100_000)
    a = ap.parse_args()
    out = Path(a.out)

    views = load_sequence(str(META), str(IMAGES_ROOT), a.seq)
    print(f"{len(views)} views for {a.seq}")

    # images: masked onto black
    import cv2
    img_out = out / "images"
    if img_out.exists():
        shutil.rmtree(img_out)
    img_out.mkdir(parents=True)
    names = []
    for k, v in enumerate(views):
        name = f"{k + 1:04d}.png"
        img = cv2.imread(v["image"], cv2.IMREAD_COLOR)
        mask = cv2.imread(v["mask"], cv2.IMREAD_GRAYSCALE)
        img[mask < 128] = 0
        cv2.imwrite(str(img_out / name), img)
        names.append(name)

    # cameras.txt: dedupe intrinsics
    sparse = out / "sparse" / "0"
    sparse.mkdir(parents=True, exist_ok=True)
    cams, cam_ids = {}, []
    for v in views:
        K = v["K"]
        key = (v["W"], v["H"], round(K[0][0], 3), round(K[1][1], 3), round(K[0][2], 3), round(K[1][2], 3))
        if key not in cams:
            cams[key] = len(cams) + 1
        cam_ids.append(cams[key])
    (sparse / "cameras.txt").write_text("# CAMERAS\n" + "".join(
        f"{cid} PINHOLE {k[0]} {k[1]} {k[2]:.6f} {k[3]:.6f} {k[4]:.6f} {k[5]:.6f}\n"
        for k, cid in cams.items()))

    # images.txt: world2cam from c2w
    lines = ["# IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID NAME"]
    for k, v in enumerate(views):
        c2w = np.array(v["c2w"])
        w2c = np.linalg.inv(c2w)
        q = matrix_to_quat_wxyz(w2c[:3, :3])
        t = w2c[:3, 3]
        lines.append(f"{k + 1} {q[0]:.9f} {q[1]:.9f} {q[2]:.9f} {q[3]:.9f} "
                     f"{t[0]:.9f} {t[1]:.9f} {t[2]:.9f} {cam_ids[k]} {names[k]}\n")
    (sparse / "images.txt").write_text("\n".join(lines) + "\n")

    # points3D.txt: the REAL SfM cloud (subsampled), not a random ball
    seq_dir = IMAGES_ROOT / "teddybear" / a.seq
    pts, cols = read_pointcloud(seq_dir / "pointcloud.ply", a.max_points)
    plines = ["# POINT3D_ID X Y Z R G B ERROR TRACK[]"]
    for i in range(len(pts)):
        plines.append(f"{i + 1} {pts[i, 0]:.6f} {pts[i, 1]:.6f} {pts[i, 2]:.6f} "
                      f"{cols[i, 0]} {cols[i, 1]} {cols[i, 2]} 1.0")
    (sparse / "points3D.txt").write_text("\n".join(plines) + "\n")
    (sparse / "cameras.bin").unlink(missing_ok=True)
    print(f"dataset -> {out} ({len(names)} masked images, {len(cams)} cameras, {len(pts)} real init points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
