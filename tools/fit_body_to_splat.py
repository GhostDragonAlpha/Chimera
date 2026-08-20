"""Fit the parametric CAD bear to a static splat cloud (e.g. teddy.splat).

Label source: TRANSFER from the settled coat (authbear4_coat.splat + .meta.npz)
— every settled splat already carries a part_id, so nearest-neighbor transfer
labels the target cloud with no hand-drawn cluster map. Then per-part refit:
capsules get centroid-anchored PCA axis/span/radius; ellipsoids get per-axis
percentile fits; ears/eyes FOLLOW the head. Margin = symmetric chamfer
(target->surface + surface->target), reported as mean/p90/max.

Usage: python tools/fit_body_to_splat.py [target.splat] [--coat coat.splat]
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\ChimeraEngine")
sys.path.insert(0, r"E:\PythonChimera\tools")
import cpp_bridge as cb  # noqa: E402
import teddy_catalog as tc  # noqa: E402
import teddy_body as tb  # noqa: E402
from fit_body_to_cloud import pca_stats  # noqa: E402

FOLLOWS = {"ear_L": "head", "ear_R": "head", "eye_L": "head", "eye_R": "head"}


def coarse_align(P_tgt, P_coat):
    """Scale+translate the coat onto the target (both head-at-+y frames).
    Returns (scale, shift) mapping coat -> target."""
    def frame(P):
        lo, hi = np.percentile(P, [2, 98], axis=0)
        return (lo + hi) / 2, hi - lo
    c_t, e_t = frame(P_tgt)
    c_c, e_c = frame(P_coat)
    scale = float(np.median(e_t / e_c))
    shift = c_t - c_c * scale
    return scale, shift


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", default=r"models\triposplat\static\viewer\teddy.splat")
    ap.add_argument("--coat", default=r"models\triposplat\static\viewer\authbear4_coat.splat")
    ap.add_argument("--out", default=".tmp/fitted_teddy_parts.json")
    ap.add_argument("--overlay", default=".tmp/fit_teddy_overlay.png")
    args = ap.parse_args()

    from scipy.spatial import cKDTree

    # target cloud: solid splats only
    T = cb.load_splat(args.target)
    T = T[T[:, 6] >= 0.5]
    TP = T[:, 0:3]
    print(f"target: {len(TP)} solid splats from {args.target}")

    # settled coat + labels
    C = cb.load_splat(args.coat)
    meta = np.load(args.coat.replace(".splat", ".meta.npz"))
    CP, CL = C[:, 0:3], meta["part_id"]

    # coarse-align the coat onto the target, then transfer labels
    scale, shift = coarse_align(TP, CP)
    Ca = CP * scale + shift
    print(f"coarse align: scale {scale:.3f} shift ({shift[0]:+.3f},{shift[1]:+.3f},{shift[2]:+.3f})")
    tree = cKDTree(Ca)
    dist, idx = tree.query(TP, k=1)
    TL = CL[idx]
    ok = dist < 0.10 * scale  # trust transfer only near the coat
    print(f"label transfer: {ok.sum()}/{len(TP)} within tolerance")

    parts = tc.assemble()
    by_name = {p["name"]: p for p in parts}
    names = [p["name"] for p in parts]

    # per-slot target stats
    tgt = {}
    for i, name in enumerate(names):
        m = (TL == i) & ok
        if m.sum() < 100:
            continue
        c, axis, span, rad, _ = pca_stats(TP[m])
        tgt[name] = (c, axis, span, rad, m)
        print(f"{name:12s} n={m.sum():6d} c=({c[0]:+.2f},{c[1]:+.2f},{c[2]:+.2f}) span={span:.2f} rad={rad:.2f}")

    fitted = []
    for p in parts:
        p = dict(p)
        name = p["name"]
        if name in tgt and name not in FOLLOWS:
            c, axis, span, rad, m = tgt[name]
            if p["prim"] == "capsule":
                u = axis / np.linalg.norm(axis)
                L = span * 0.8
                p["a"] = (c - u * L / 2).tolist()
                p["b"] = (c + u * L / 2).tolist()
                p["r"] = [float(rad * 0.95)] * 3
            else:
                Q = TP[m]
                lo, hi = np.percentile(Q, 5, axis=0), np.percentile(Q, 95, axis=0)
                p["c"] = ((lo + hi) / 2).tolist()
                p["r"] = list(((hi - lo) / 2 * 0.9).astype(float))
        fitted.append(p)

    # ears/eyes follow the head (relative offset, per-axis ratio)
    for p in fitted:
        par = FOLLOWS.get(p["name"])
        if not par:
            continue
        parent_new = next(x for x in fitted if x["name"] == par)
        parent_old = by_name[par]
        p_orig = by_name[p["name"]]
        off = np.array(p_orig["c"], float) - np.array(parent_old["c"], float)
        ratio = np.array(parent_new["r"]) / np.array(parent_old["r"], float)
        p["c"] = (np.array(parent_new["c"]) + off * ratio).tolist()
        p["r"] = list((np.array(p_orig["r"]) * ratio).astype(float))

    # refresh pivots: elbow/knee = child start; shoulder/hip = parent start
    for p in fitted:
        if p["prim"] == "capsule":
            p["pivot"] = list(p["a"])

    with open(args.out, "w") as f:
        json.dump(fitted, f, indent=2)

    # ---- margin: symmetric chamfer -----------------------------------------
    tb.PARTS = fitted
    S, _, _ = tb.sample_surface(n_per_part=3000, seed=0)
    # target -> fitted SDF surface
    sub = TP[np.random.default_rng(0).choice(len(TP), min(40000, len(TP)), replace=False)]
    d_t2s = np.abs(tb.sdf(sub))
    # fitted surface -> target cloud
    tt = cKDTree(TP)
    d_s2t, _ = tt.query(S, k=1)
    for tag, d in [("target->cad", d_t2s), ("cad->target", d_s2t)]:
        print(f"margin {tag}: mean {d.mean():.4f}  p90 {np.percentile(d, 90):.4f}  max {d.max():.4f}")
    margin = float(max(np.percentile(d_t2s, 90), np.percentile(d_s2t, 90)))
    print(f"FIT MARGIN (p90 symmetric): {margin:.4f} scene units "
          f"({margin / np.ptp(np.percentile(TP, [2, 98], axis=0), axis=0)[1] * 100:.1f}% of bear height)")

    # overlay
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 7))
    ax[0].scatter(TP[::5, 0], TP[::5, 1], s=0.3, c="0.75")
    ax[0].scatter(S[:, 0], S[:, 1], s=0.8, c="tab:blue")
    ax[0].set_aspect("equal"); ax[0].set_title("front x-y (grey=target, blue=CAD)")
    ax[1].scatter(TP[::5, 2], TP[::5, 1], s=0.3, c="0.75")
    ax[1].scatter(S[:, 2], S[:, 1], s=0.8, c="tab:blue")
    ax[1].set_aspect("equal"); ax[1].set_title("side z-y")
    plt.tight_layout(); plt.savefig(args.overlay, dpi=90)
    print(f"wrote {args.out} and {args.overlay}")


if __name__ == "__main__":
    main()
