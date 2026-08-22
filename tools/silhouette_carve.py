"""silhouette_carve.py — photogrammetry trim: carve a 3DGS cloud with the source silhouettes.

WHY (operator directive, 2026-08-19): trim the object "by outlining shape to within ~5mm".
Every training view is a registered camera (COLMAP) plus a frame whose background is
(near-)black. A splat that projects OUTSIDE the object's silhouette in a view cannot be
real — that is the visual-hull constraint, and it is stronger than any colour/length
heuristic (clean_splat.py): it removes the dense dark shell and billboard fakes that
attribute filters cannot separate from fur, WITHOUT touching fur inside the outline
(the 2026-08-19 box-cut amputated the crown/face from head-on views; the hull does not).

THEORY (Rule 0):
  STATEMENT  — junk splats live outside the true visual hull; fur lives inside it.
  PREDICTION — carved cloud keeps >= 60% of splats, drops the shell/ember/billboard
               populations, and renders the SAME front view as the uncarved cloud.
  FALSIFIER  — if a rendered carved view loses real anatomy (face, ears, limbs) that the
               uncarved view shows, the masks are wrong (threshold/margin), not the idea:
               re-run with --show-frames to inspect masks before trusting the carve.

Frames: works on the UNDISTORTED trainer layout (<dir>/data/images + <dir>/data/sparse,
PINHOLE). Input cloud must be in the COLMAP world frame: the raw trained PLY (pre-orient,
pre-crop). Output is a keep-mask .npy aligned with PLY row order; apply it in the same
script that loads the PLY (load_3dgs_ply), BEFORE orient/normalize.

Runs under .venv-gs (needs pycolmap + cv2):
    .venv-gs/Scripts/python.exe tools/silhouette_carve.py --dir capture/genbear2 \
        --ply capture/genbear2/train_out/ply/splat_29999.ply --out capture/genbear2/carve_keep.npy
    # inspect the masks first:
    ... --show-frames 12        # writes .tmp/carve_mask_*.png contact sheets
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine" / "native"))
from ply_to_splat import load_3dgs_ply  # noqa: E402


def foreground_mask(img_bgr: np.ndarray, threshold: int, margin_px: int) -> np.ndarray:
    """Near-black background -> foreground bool mask, dilated by margin (~'5mm')."""
    gray = img_bgr.max(axis=2)                      # any channel above black
    fg = (gray > threshold).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))  # seal fur gaps
    if margin_px > 0:
        fg = cv2.dilate(fg, np.ones((2 * margin_px + 1,) * 2, np.uint8))
    return fg.astype(bool)


def background_is_bright(img_bgr: np.ndarray, threshold: int) -> bool:
    """True if the frame's background is NOT dark (e.g. the white-studio opening frames an
    image-to-video model inherits from a light-background anchor still). Such frames carry
    no silhouette information — the whole frame reads as foreground — so skip the view."""
    h, w = img_bgr.shape[:2]
    corners = np.concatenate([img_bgr[: h // 10, : w // 10].reshape(-1, 3),
                              img_bgr[: h // 10, -w // 10:].reshape(-1, 3),
                              img_bgr[-h // 10:, : w // 10].reshape(-1, 3),
                              img_bgr[-h // 10:, -w // 10:].reshape(-1, 3)])
    return float(corners.max(axis=1).mean()) > 2.0 * threshold


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", required=True, help="capture workdir holding data/images + data/sparse")
    ap.add_argument("--ply", help="trained 3DGS .ply in the COLMAP world frame")
    ap.add_argument("--out", help="output keep-mask .npy (PLY row order)")
    ap.add_argument("--threshold", type=int, default=25, help="foreground if any channel > this (0-255)")
    ap.add_argument("--margin-px", type=int, default=6, help="dilate mask this many px (~5mm slack)")
    ap.add_argument("--min-frac", type=float, default=0.9,
                    help="keep a splat if inside the mask in >= this fraction of views that see it")
    ap.add_argument("--min-seen", type=int, default=10,
                    help="splats seen by fewer views are KEPT (not enough evidence to cut)")
    ap.add_argument("--show-frames", type=int, default=0,
                    help="write N mask contact sheets to .tmp/ and stop (no carve)")
    a = ap.parse_args()

    workdir = Path(a.dir)
    images_dir = workdir / "data" / "images"
    sparse_dir = workdir / "data" / "sparse"

    import pycolmap
    rec = pycolmap.Reconstruction(str(sparse_dir))

    # gsplat's trainer runs ColmapParser with normalize_world_space=True (default): the
    # trained PLY lives in the NORMALIZED frame points' = (T3? @ T2 @ T1) @ points, NOT the
    # raw COLMAP world frame. Projecting PLY points with raw cameras misses everything
    # (observed 2026-08-19: keep 25/121665). Replicate the parser's transform chain exactly
    # (tools/gsplat/examples/datasets/colmap.py:150-248) and use the TRANSFORMED cameras.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gsplat_normalize", ROOT / "tools" / "gsplat" / "examples" / "datasets" / "normalize.py")
    gsn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gsn)

    images = sorted(rec.images.values(), key=lambda im: im.name)
    bottom = np.array([0, 0, 0, 1]).reshape(1, 4)
    w2c = []
    for img in images:
        cfw = img.cam_from_world()
        rot = np.asarray(cfw.rotation.matrix())
        trans = np.asarray(cfw.translation).reshape(3, 1)
        w2c.append(np.concatenate([np.concatenate([rot, trans], 1), bottom], axis=0))
    camtoworlds = np.linalg.inv(np.stack(w2c, axis=0))
    sfm_points = np.stack([p.xyz for p in rec.points3D.values()], axis=0).astype(np.float32) \
        if len(rec.points3D) else np.zeros((0, 3), np.float32)

    T1 = gsn.similarity_from_cameras(camtoworlds)
    camtoworlds = gsn.transform_cameras(T1, camtoworlds)
    sfm_points = gsn.transform_points(T1, sfm_points)
    T2 = gsn.align_principal_axes(sfm_points)
    camtoworlds = gsn.transform_cameras(T2, camtoworlds)
    sfm_points = gsn.transform_points(T2, sfm_points)
    if np.median(sfm_points[:, 2]) > np.mean(sfm_points[:, 2]):
        T3 = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0],
                       [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
        camtoworlds = gsn.transform_cameras(T3, camtoworlds)
    w2c_norm = np.linalg.inv(camtoworlds)

    views = []   # (name, R, t, fx, fy, cx, cy, w, h)
    for img, w2c_i in zip(images, w2c_norm):
        cam = rec.cameras[img.camera_id]
        R = w2c_i[:3, :3]
        t = w2c_i[:3, 3]
        p = cam.params
        if cam.model.name == "PINHOLE":
            fx, fy, cx, cy = p[0], p[1], p[2], p[3]
        elif cam.model.name == "SIMPLE_PINHOLE":
            fx = fy = p[0]; cx, cy = p[1], p[2]
        else:
            raise SystemExit(f"unexpected camera model {cam.model.name} — run on undistorted data")
        views.append((img.name, R, t, fx, fy, cx, cy, cam.width, cam.height))
    print(f"{len(views)} registered views from {sparse_dir} (normalized-frame cameras)")

    if a.show_frames:
        out = ROOT / ".tmp"
        out.mkdir(exist_ok=True)
        for i, (name, *_rest) in enumerate(views[: a.show_frames]):
            img = cv2.imread(str(images_dir / name))
            m = foreground_mask(img, a.threshold, a.margin_px)
            vis = img.copy()
            vis[~m] = (vis[~m] * 0.25).astype(np.uint8)   # dim what the carve would cut
            cv2.imwrite(str(out / f"carve_mask_{i:03d}_{Path(name).stem}.png"), vis)
        print(f"wrote {min(a.show_frames, len(views))} mask previews to .tmp/ — eye-check them")
        return 0

    if not a.ply or not a.out:
        print("nothing to do: pass --ply and --out (or --show-frames)")
        return 1

    pts = load_3dgs_ply(a.ply)[:, 0:3].astype(np.float64)
    n = len(pts)
    seen = np.zeros(n, dtype=np.int32)
    inside = np.zeros(n, dtype=np.int32)
    skipped = 0
    for k, (name, R, t, fx, fy, cx, cy, w, h) in enumerate(views):
        img = cv2.imread(str(images_dir / name))
        if background_is_bright(img, a.threshold):
            skipped += 1
            continue
        mask = foreground_mask(img, a.threshold, a.margin_px)
        pc = pts @ R.T + t
        z = pc[:, 2]
        ok = z > 1e-6
        u = np.full(n, -1, dtype=np.int64)
        v = np.full(n, -1, dtype=np.int64)
        u[ok] = (fx * pc[ok, 0] / z[ok] + cx).astype(np.int64)
        v[ok] = (fy * pc[ok, 1] / z[ok] + cy).astype(np.int64)
        ok &= (u >= 0) & (u < w) & (v >= 0) & (v < h)
        seen += ok
        hit = np.zeros(n, dtype=bool)
        hit[ok] = mask[v[ok], u[ok]]
        inside += hit
        if (k + 1) % 50 == 0:
            print(f"  {k + 1}/{len(views)} views")

    frac = inside / np.maximum(seen, 1)
    keep = (frac >= a.min_frac) | (seen < a.min_seen)
    np.save(a.out, keep)
    print(f"carve: keep {int(keep.sum())} / {n} "
          f"(cut {int((~keep).sum())}; {int((seen < a.min_seen).sum())} kept on low evidence)")
    print(f"mask -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
