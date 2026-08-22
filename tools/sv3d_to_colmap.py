"""sv3d_to_colmap.py — SV3D ring frames + known orbit -> COLMAP-format gsplat dataset.

WHY: COLMAP fails on SV3D frames (black background, synthetic texture — "no good initial
pair" live, 2026-08-20), but we don't need it: SV3D_p orbits are COMMANDED, so the camera
path is known exactly. Exact poses remove the pose-estimation ghosting that produced the
"shadow bear" in the video-capture trainings.

RULE 0:
  STATEMENT  — SV3D's effective focal length is recoverable from the data: with the
               relative rotation between two equatorial frames KNOWN (commanded Δaz),
               matched features triangulate consistently only at the true focal.
  PREDICTION — the ray-mismatch curve over candidate f has a sharp interior minimum
               (not at a grid edge), and the dataset built with f* trains to a bear
               with correct proportions.
  FALSIFIER  — a flat/monotone mismatch curve (poses wrong or matches garbage) or a
               minimum at a grid boundary. Reported honestly either way.

CONVENTIONS:
  World: y-up, object at origin, height ~1. Camera at azimuth az, elevation el:
      C = r * (cos(el) sin(az), sin(el), cos(el) cos(az))
  so az=0, el=0 puts the camera on +Z looking at the bear's front (anchor view).
  COLMAP cameras: x right, y down, z forward (world2cam rows [x; y; z]).

Usage:
  .venv-gs/Scripts/python.exe tools/sv3d_to_colmap.py --src capture/sv3d_bear --out capture/sv3d_bear/data
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def cam_center(r: float, elev: float, az: float) -> np.ndarray:
    return r * np.array([math.cos(elev) * math.sin(az),
                         math.sin(elev),
                         math.cos(elev) * math.cos(az)])


def world2cam(C: np.ndarray) -> np.ndarray:
    """3x3 world->cam rotation (x right, y down, z forward) looking at the origin."""
    f = -C / np.linalg.norm(C)                      # z_cam
    x = np.cross(f, np.array([0.0, 1.0, 0.0]))      # right
    x /= np.linalg.norm(x)
    y = np.cross(f, x)                              # down
    return np.stack([x, y, f], axis=0)


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
    q[1 + j] = (R[j, i] + R[i, j]) / s
    q[1 + k] = (R[k, i] + R[i, k]) / s
    return tuple(q)


def calibrate_focal(src: Path, res: int, h_px: float) -> tuple[float, list[dict]]:
    """Grid-search f (px) minimizing triangulated reprojection error over adjacent
    eq-ring pairs. For each candidate f the orbit radius follows the gauge r=f/h_px,
    so the relative pose (R,t) is fully determined; correct f minimizes the
    reprojection error of midpoint-triangulated SIFT matches."""
    import cv2

    sift = cv2.SIFT_create(nfeatures=4000)
    frames = sorted((src / "ring_eq").glob("frame_*.png"))
    azimuths = np.linspace(0.0, 360.0, len(frames), endpoint=False)
    daz = math.radians(float(azimuths[1] - azimuths[0]))

    pairs = []
    ims = [cv2.imread(str(p), cv2.IMREAD_GRAYSCALE) for p in frames]
    kps, des = [], []
    for im in ims:
        k, d = sift.detectAndCompute(im, None)
        kps.append(k)
        des.append(d)
    bf = cv2.BFMatcher()
    for i in range(len(frames)):
        j = (i + 1) % len(frames)
        m = bf.knnMatch(des[i], des[j], k=2)
        good = [x for x, b in m if x.distance < 0.75 * b.distance]
        if len(good) >= 12:
            p1 = np.float64([kps[i][g.queryIdx].pt for g in good])
            p2 = np.float64([kps[j][g.trainIdx].pt for g in good])
            pairs.append((p1, p2))

    c = res / 2.0
    curve = []
    for f in np.arange(300.0, 1501.0, 25.0):
        r = f / h_px  # gauge: bear height = 1 world unit
        C1 = cam_center(r, 0.0, 0.0)
        C2 = cam_center(r, 0.0, daz)
        R1, R2 = world2cam(C1), world2cam(C2)
        t1, t2 = -R1 @ C1, -R2 @ C2
        R_rel = R2 @ R1.T
        t_rel = t2 - R_rel @ t1
        errs = []
        for p1, p2 in pairs:
            x1 = np.stack([(p1[:, 0] - c) / f, (p1[:, 1] - c) / f, np.ones(len(p1))], 1)
            x2 = np.stack([(p2[:, 0] - c) / f, (p2[:, 1] - c) / f, np.ones(len(p2))], 1)
            # midpoint triangulation: X = C1 + d1 * R1^T x1  s.t. both rays' midpoint
            d1r = x1                       # cam1 rays (cam1 = reference)
            d2r = (R_rel.T @ x2.T).T       # cam2 rays expressed in cam1 frame
            t2_in_1 = -R_rel.T @ t_rel     # cam2 center in cam1 frame
            # closed-form midpoint solve: d1*(u) - d2*(v) ≈ b with unit rays u, v
            b = np.broadcast_to(t2_in_1, (len(p1), 3))
            un = d1r / np.linalg.norm(d1r, axis=1, keepdims=True)
            vn = d2r / np.linalg.norm(d2r, axis=1, keepdims=True)
            uv = (un * vn).sum(1)
            ub = (un * b).sum(1)
            vb = (vn * b).sum(1)
            det = np.maximum(1e-9, 1.0 - uv * uv)
            d1 = (ub - uv * vb) / det
            X1 = d1[:, None] * un                              # (m,3) in cam1
            X2 = (R_rel @ X1.T).T + t_rel                        # into cam2
            rp1 = X1[:, :2] / np.maximum(X1[:, 2:3], 1e-9)
            rp2 = X2[:, :2] / np.maximum(X2[:, 2:3], 1e-9)
            e = 0.5 * (np.linalg.norm(rp1 - (x1[:, :2]), axis=1) * f
                       + np.linalg.norm(rp2 - (x2[:, :2]), axis=1) * f)
            valid = (X1[:, 2] > 0.05) & (X2[:, 2] > 0.05)
            if valid.sum() >= 8:
                errs.append(np.median(e[valid]))
        curve.append({"f": float(f),
                      "median_reproj_err_px": float(np.median(errs)) if errs else 1e9})
    best = min(curve, key=lambda d: d["median_reproj_err_px"])
    print(f"focal calibration: {len(pairs)} pairs, best f={best['f']:.0f}px "
          f"(median reprojection {best['median_reproj_err_px']:.2f}px)")
    edge = best["f"] in (curve[0]["f"], curve[-1]["f"])
    if edge:
        print("WARNING: minimum at grid edge — FALSIFIER territory, inspect the curve")
    return best["f"], curve


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=str(ROOT / "capture" / "sv3d_bear"))
    ap.add_argument("--out", default=str(ROOT / "capture" / "sv3d_bear" / "data"))
    ap.add_argument("--res", type=int, default=576)
    ap.add_argument("--focal", type=float, default=None, help="skip calibration, force f (px)")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)

    poses = json.loads((src / "poses.json").read_text())["poses"]

    # gauge first: bear height = 1.0 world unit from the anchor's non-black extent
    import cv2
    im0 = cv2.imread(str(src / "ring_eq" / "frame_00.png"), cv2.IMREAD_GRAYSCALE)
    ys, _ = np.where(im0 > 24)
    h_px = float(ys.max() - ys.min())

    f = a.focal if a.focal else calibrate_focal(src, a.res, h_px)[0]
    r = f * 1.0 / h_px
    print(f"bear height {h_px:.0f}px -> orbit radius r={r:.3f} world units")

    # images/
    img_out = out / "images"
    if img_out.exists():
        shutil.rmtree(img_out)
    img_out.mkdir(parents=True)
    names = []
    for k, p in enumerate(poses):
        name = f"{k + 1:04d}.png"
        shutil.copy(src / p["frame_filename"], img_out / name)
        names.append(name)

    # sparse/0/
    sparse = out / "sparse" / "0"
    sparse.mkdir(parents=True, exist_ok=True)
    (sparse / "cameras.txt").write_text(
        f"# CAMERAS\n1 PINHOLE {a.res} {a.res} {f:.6f} {f:.6f} {a.res / 2} {a.res / 2}\n")
    lines = ["# IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID NAME"]
    for k, p in enumerate(poses):
        el, az = math.radians(p["elevation_deg"]), math.radians(p["azimuth_deg"])
        C = cam_center(r, el, az)
        R = world2cam(C)
        q = matrix_to_quat_wxyz(R)
        t = -R @ C
        lines.append(f"{k + 1} {q[0]:.9f} {q[1]:.9f} {q[2]:.9f} {q[3]:.9f} "
                     f"{t[0]:.9f} {t[1]:.9f} {t[2]:.9f} 1 {names[k]}\n")
    (sparse / "images.txt").write_text("\n".join(lines) + "\n")

    rng = np.random.default_rng(a.seed)
    n = 50_000
    pts = rng.standard_normal((n, 3))
    pts *= 0.55 / np.linalg.norm(pts, axis=1, keepdims=True) * rng.random((n, 1)) ** (1 / 3)
    cols = rng.integers(96, 160, (n, 3))
    plines = ["# POINT3D_ID X Y Z R G B ERROR TRACK[]"]
    for i in range(n):
        plines.append(f"{i + 1} {pts[i, 0]:.6f} {pts[i, 1]:.6f} {pts[i, 2]:.6f} "
                      f"{cols[i, 0]} {cols[i, 1]} {cols[i, 2]} 1.0")
    (sparse / "points3D.txt").write_text("\n".join(plines) + "\n")
    (sparse / "cameras.bin").unlink(missing_ok=True)  # force txt parsing
    print(f"dataset -> {out} ({len(names)} images, f={f:.0f}px, r={r:.3f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
