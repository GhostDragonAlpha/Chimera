"""tools/laneE_compute_poses.py

Extract the EXACT camera math from models/triposplat/static/viewer/viewer.html and write
cam2world extrinsics + normalized intrinsics for the Lane E view grid.

Camera convention (viewer.html lines 86, 122-123):
  - PerspectiveCamera(45, W/H, 0.01, 1000)
  - eye = (r*cos(el)*sin(az), r*sin(el), r*cos(el)*cos(az))
  - target = (0,0,0), up = (0,1,0)
  - right-handed, +Y up, camera looks toward -Z in its local frame.

Writes:
  capture/genbear3/laneE_extrinsic.npy  (N,4,4) cam2world
  capture/genbear3/laneE_intrinsic.npy  (N,3,3) normalized by W/H
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

WIDTH = 1280
HEIGHT = 720
FOV_DEG = 45.0
RADIUS = 1.825


def camera_c2w(az: float, el: float, r: float) -> np.ndarray:
    eye = np.array([
        r * math.cos(el) * math.sin(az),
        r * math.sin(el),
        r * math.cos(el) * math.cos(az),
    ])
    z_cam = eye / np.linalg.norm(eye)          # camera +Z points away from target
    up_world = np.array([0.0, 1.0, 0.0])
    if abs(np.dot(z_cam, up_world)) > 0.9999:
        up_world = np.array([0.0, 0.0, -1.0])  # fallback for pole-on views
    x_cam = np.cross(up_world, z_cam)
    x_cam /= np.linalg.norm(x_cam)
    y_cam = np.cross(z_cam, x_cam)
    y_cam /= np.linalg.norm(y_cam)
    c2w = np.eye(4, dtype=np.float64)
    c2w[:3, 0] = x_cam
    c2w[:3, 1] = y_cam
    c2w[:3, 2] = z_cam
    c2w[:3, 3] = eye
    return c2w


def normalized_intrinsics(w: int, h: int, fov_deg: float) -> np.ndarray:
    aspect = w / h
    tan_half = math.tan(math.radians(fov_deg) / 2.0)
    fx = 1.0 / (2.0 * aspect * tan_half)
    fy = 1.0 / (2.0 * tan_half)
    K = np.array([
        [fx, 0.0, 0.5],
        [0.0, fy, 0.5],
        [0.0, 0.0, 1.0],
    ], dtype=np.float64)
    return K


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", default="capture/genbear3/laneE_views/laneE_views.json")
    ap.add_argument("--out-dir", default="capture/genbear3")
    args = ap.parse_args()

    meta_path = Path(args.meta)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = json.loads(meta_path.read_text())
    N = len(meta)
    extrinsic = np.empty((N, 4, 4), dtype=np.float64)
    for i, m in enumerate(meta):
        extrinsic[i] = camera_c2w(m["az"], m["el"], m["r"])

    intrinsic = np.tile(normalized_intrinsics(WIDTH, HEIGHT, FOV_DEG), (N, 1, 1))

    np.save(out_dir / "laneE_extrinsic.npy", extrinsic)
    np.save(out_dir / "laneE_intrinsic.npy", intrinsic)

    # Print az=0 diagnostic to confirm view direction.
    idx0 = next(i for i, m in enumerate(meta) if abs(m["az"]) < 1e-6)
    print(f"az=0 view: eye = {extrinsic[idx0, :3, 3]}")
    print(f"az=0 view: camera +Z axis = {extrinsic[idx0, :3, 2]}")
    print(f"wrote {out_dir / 'laneE_extrinsic.npy'}  shape {extrinsic.shape}")
    print(f"wrote {out_dir / 'laneE_intrinsic.npy'} shape {intrinsic.shape}")
    print(f"fx_norm={intrinsic[0,0,0]:.6f} fy_norm={intrinsic[0,1,1]:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
