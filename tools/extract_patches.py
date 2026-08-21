"""extract_patches.py -- trained 3DGS PLY -> patch genome library.

Cuts the surface into ~2cm discs (metric when --height-m is given or a
<name>.space.json sidecar exists) and records, per patch, the full splat
population plus a context key: bbox-relative position, tone, planarity,
and nap direction (dominant in-plane splat major-axis). The library is the
COAT genome: the spray step samples patch DISTRIBUTIONS keyed by context,
never a global average.

Usage (from the repo root):
  .venv-gs/Scripts/python.exe tools/extract_patches.py \
      --ply capture/sv3d_real/train_eq_pinned/ply/point_cloud_29999.ply \
      --source-id sv3d_real --height-m 0.35
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT / "ChimeraEngine" / "native"))
from ply_to_splat import load_3dgs_ply  # noqa: E402


def quat_to_rotmat(q: np.ndarray) -> np.ndarray:
    """(n,4) wxyz -> (n,3,3)."""
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    n = np.sqrt(w * w + x * x + y * y + z * z) + 1e-12
    w, x, y, z = w / n, x / n, y / n, z / n
    R = np.empty((len(q), 3, 3), dtype=np.float64)
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - w * z); R[:, 0, 2] = 2 * (x * z + w * y)
    R[:, 1, 0] = 2 * (x * y + w * z); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - w * x)
    R[:, 2, 0] = 2 * (x * z - w * y); R[:, 2, 1] = 2 * (y * z + w * x); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R


def knn_normals(pts: np.ndarray, k: int = 16) -> tuple[np.ndarray, np.ndarray]:
    """PCA normal + planarity per point from its k-NN. Returns (n,3), (n,)."""
    from scipy.spatial import cKDTree
    tree = cKDTree(pts)
    _, idx = tree.query(pts, k=k + 1)
    normals = np.empty_like(pts)
    planarity = np.empty(len(pts))
    for i in range(len(pts)):
        nb = pts[idx[i, 1:]] - pts[i]
        cov = nb.T @ nb / len(nb)
        w, V = np.linalg.eigh(cov)  # ascending
        normals[i] = V[:, 0]
        planarity[i] = 1.0 - w[0] / (w.sum() + 1e-12)
    return normals, planarity


def farthest_centers(pts: np.ndarray, spacing: float, max_centers: int = 4000) -> np.ndarray:
    """Greedy farthest-point sampling; returns center indices."""
    rng = np.random.default_rng(0)
    centers = [int(rng.integers(len(pts)))]
    d = np.linalg.norm(pts - pts[centers[0]], axis=1)
    while len(centers) < max_centers:
        i = int(np.argmax(d))
        if d[i] < spacing:
            break
        centers.append(i)
        d = np.minimum(d, np.linalg.norm(pts - pts[i], axis=1))
    return np.array(centers)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ply", required=True)
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--out", default=str(ROOT / "models" / "patch_library"))
    ap.add_argument("--height-m", type=float, default=None,
                    help="declared object height in meters; rescales the cloud to metric")
    ap.add_argument("--patch-radius-m", type=float, default=0.01, help="2cm discs")
    ap.add_argument("--alpha-min", type=float, default=0.5, help="surface splats only")
    args = ap.parse_args()

    if args.ply.endswith(".splat"):
        sys.path.insert(0, str(ROOT / "ChimeraEngine"))
        import cpp_bridge as cb
        splats = cb.load_splat(args.ply).astype(np.float64)
    else:
        splats = load_3dgs_ply(args.ply).astype(np.float64)  # (n,14): xyz rgb a sxsy sz q
    pos = splats[:, 0:3].astype(np.float64)
    height = float(pos[:, 1].max() - pos[:, 1].min())
    scale = 1.0
    if args.height_m:
        scale = args.height_m / height
        pos *= scale
        print(f"rescaled to metric: raw height {height:.4f} -> {args.height_m} m (x{scale:.4f})")

    keep = splats[:, 6] >= args.alpha_min
    idx_surf = np.nonzero(keep)[0]
    surf = pos[keep]
    print(f"{len(splats)} splats, {len(surf)} at alpha>={args.alpha_min}")

    normals, planarity = knn_normals(surf)
    centers = farthest_centers(surf, args.patch_radius_m)
    cpos = surf[centers]
    print(f"{len(centers)} patch centers (spacing {args.patch_radius_m * 1000:.0f} mm)")

    from scipy.spatial import cKDTree
    tree = cKDTree(surf)
    # assign every surface splat to its nearest center
    _, assign = tree.query(cpos, k=1)
    _, nearest_center = cKDTree(cpos).query(surf, k=1)

    # splat major axes in world (for nap direction)
    R = quat_to_rotmat(splats[:, 10:14].astype(np.float64))
    sc = splats[:, 7:10].astype(np.float64) * scale
    major = np.take_along_axis(R, sc.argmax(1)[:, None, None], axis=2)[:, :, 0]  # (n,3)

    bbox_min, bbox_max = pos.min(0), pos.max(0)
    bbox_span = np.maximum(bbox_max - bbox_min, 1e-9)

    patches = []
    for ci in range(len(centers)):
        members = np.nonzero(nearest_center == ci)[0]
        if len(members) < 5:
            continue
        gi = idx_surf[members]  # back to full-cloud indices
        n = normals[members]
        normal = n.mean(0); normal /= (np.linalg.norm(normal) + 1e-12)
        # nap: project member major axes onto the tangent plane, circular mean of angles
        mj = major[gi]
        mj = mj - (mj @ normal)[:, None] * normal[None, :]
        lens = np.linalg.norm(mj, axis=1)
        ok = lens > 1e-9
        if ok.any():
            t1 = np.cross(normal, [0, 0, 1.0])
            if np.linalg.norm(t1) < 1e-6:
                t1 = np.cross(normal, [0, 1.0, 0])
            t1 /= np.linalg.norm(t1); t2 = np.cross(normal, t1)
            ang = np.arctan2(mj[ok] @ t2, mj[ok] @ t1)
            nap_ang = 0.5 * np.arctan2(np.sin(2 * ang).mean(), np.cos(2 * ang).mean())
            nap = np.cos(nap_ang) * t1 + np.sin(nap_ang) * t2
            anisotropy = float(np.mean(sc[gi].max(1) / (sc[gi].min(1) + 1e-12)))
        else:
            nap = [0.0, 0.0, 0.0]; anisotropy = 1.0
        rgb = splats[gi, 3:6]
        rel = (cpos[ci] - bbox_min) / bbox_span
        patches.append({
            "center": [round(float(v), 6) for v in cpos[ci]],
            "normal": [round(float(v), 6) for v in normal],
            "nap": [round(float(v), 4) for v in nap],
            "key": {
                "rel_pos": [round(float(v), 3) for v in rel],
                "tone": [round(float(v), 3) for v in rgb.mean(0)],
                "planarity": round(float(planarity[members].mean()), 3),
                "anisotropy": round(anisotropy, 2),
            },
            "count": int(len(gi)),
            "indices": gi.tolist(),
        })

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    lib = {
        "source_id": args.source_id,
        "ply": args.ply,
        "metric_scale": scale,
        "patch_radius_m": args.patch_radius_m,
        "n_splats": int(len(splats)),
        "n_patches": len(patches),
        "patches": patches,
    }
    path = out_dir / f"{args.source_id}.json"
    path.write_text(json.dumps(lib))
    counts = np.array([p["count"] for p in patches])
    print(f"library -> {path} ({len(patches)} patches, splats/patch median {int(np.median(counts))}, "
          f"p5 {int(np.percentile(counts, 5))}, p95 {int(np.percentile(counts, 95))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
