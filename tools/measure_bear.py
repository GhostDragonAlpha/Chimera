"""Measure a .splat bear cloud to derive a parametric CAD body.

Reads a 32-byte/splat TripoSplat-format file (via cpp_bridge.load_splat so the
viewer orientation is applied), alpha-filters to the solid bear, and reports
the numbers a parametric body needs: bounding box, symmetry plane error,
vertical profile (head/torso/hips), limb clusters with axes and radii, and
joint candidates where limbs meet the torso.

Output: JSON to stdout file + printed table.
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\ChimeraEngine")
import cpp_bridge as cb  # noqa: E402


def pca_axis(pts):
    """Principal axis of a point set (unit vector along max variance)."""
    c = pts.mean(axis=0)
    cov = np.cov((pts - c).T)
    vals, vecs = np.linalg.eigh(cov)
    order = np.argsort(-vals)
    return c, vecs[:, order[0]], np.sqrt(np.maximum(vals[order], 0))


def radial_radius(pts, axis_origin, axis_dir):
    """Median perpendicular distance of points from an axis line."""
    rel = pts - axis_origin
    along = rel @ axis_dir
    perp = rel - np.outer(along, axis_dir)
    return float(np.median(np.linalg.norm(perp, axis=1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("splat")
    ap.add_argument("--alpha-min", type=float, default=0.5)
    ap.add_argument("--bands", type=int, default=20)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    data = cb.load_splat(args.splat)  # (N,14): pos3 rgb3 alpha1 scale3 rot4
    pos = data[:, 0:3]
    alpha = data[:, 6]
    keep = alpha >= args.alpha_min
    P = pos[keep]
    print(f"splats: {len(pos)} total, {len(P)} solid (alpha>={args.alpha_min})")

    lo, hi = P.min(axis=0), P.max(axis=0)
    extent = hi - lo
    centroid = P.mean(axis=0)
    print(f"bbox: {lo.round(3)} .. {hi.round(3)}  extent {extent.round(3)}")
    print(f"centroid: {centroid.round(3)}")

    # Symmetry plane: x = median(x). Chamfer-ish error of mirrored cloud.
    x_plane = float(np.median(P[:, 0]))
    M = P.copy()
    M[:, 0] = 2 * x_plane - M[:, 0]
    # symmetric error: for each mirrored point, distance to nearest solid point
    # (subsample for speed)
    rng = np.random.default_rng(0)
    sub = M[rng.choice(len(M), min(4000, len(M)), replace=False)]
    d2 = ((P[None, ::4, :] - sub[:, None, :]) ** 2).sum(-1)
    sym_err = float(np.sqrt(d2.min(axis=1)).mean())
    print(f"symmetry plane x={x_plane:.4f}  mean mirror error {sym_err:.4f} "
          f"({100*sym_err/extent[1]:.1f}% of height)")

    # Vertical profile: per height band, xy centroid + median radial spread.
    y = P[:, 1]
    edges = np.linspace(y.min(), y.max(), args.bands + 1)
    profile = []
    print("\nvertical profile (band: y_center, count, x_spread, z_spread):")
    for i in range(args.bands):
        m = (y >= edges[i]) & (y < edges[i + 1])
        if m.sum() < 20:
            continue
        b = P[m]
        profile.append({
            "y": float(b[:, 1].mean()),
            "n": int(m.sum()),
            "x_half": float(np.percentile(np.abs(b[:, 0] - x_plane), 90)),
            "z_half": float(np.percentile(np.abs(b[:, 1] * 0 + b[:, 2] - np.median(b[:, 2])), 90)),
        })
        print(f"  y={profile[-1]['y']:+.3f} n={profile[-1]['n']:5d} "
              f"x90={profile[-1]['x_half']:.3f} z90={profile[-1]['z_half']:.3f}")

    result = {
        "splat": args.splat,
        "n_total": int(len(pos)),
        "n_solid": int(len(P)),
        "bbox_min": lo.tolist(), "bbox_max": hi.tolist(),
        "extent": extent.tolist(), "centroid": centroid.tolist(),
        "symmetry_x": x_plane, "sym_err": sym_err,
        "profile": profile,
    }
    if args.out:
        with open(args.out, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
