"""Fit the parametric CAD bear to a real captured point cloud (CO3D).

For each body part, the target cluster gives: centroid, principal axis,
axis span, perpendicular radius. Limbs rotate about their authored joint
pivot to align the rest-pose axis to the measured axis (the joint system
doing its first real work); head/torso translate + rescale (axis-aligned
ellipsoids stay axis-aligned — the real bear is upright); children inherit
parent rotations (forearm follows upper arm).

Cluster labels below were hand-assigned from .tmp/co3d_clusters.png for
sequence 34_1479_4753 (k=10 k-means).
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\tools")
import teddy_catalog as tc  # noqa: E402
from co3d_to_views import load_ply_points  # noqa: E402

# part slot -> list of cluster ids (sequence 34_1479_4753, k=10)
# Labeled by projecting cluster centroids onto photo frame 1
# (.tmp/cluster_on_photo.png): this world's head sits at -y.
CLUSTER_MAP = {
    "head": [8, 4, 2],       # left head/ear, crown-right, forehead
    "muzzle": [5],           # muzzle/cheek front
    "torso": [9, 6],         # chest + belly
    "upper_arm_L": [0],      # world -x arm (viewer-left paw)
    "upper_arm_R": [1],      # world +x arm
    "thigh_L": [7],          # world -x leg -> foot
    "thigh_R": [3],          # world +x leg -> foot
}
# slots that follow a parent's fit instead of their own cluster
FOLLOWS = {"forearm_L": "upper_arm_L", "forearm_R": "upper_arm_R",
           "shin_L": "thigh_L", "shin_R": "thigh_R",
           "ear_L": "head", "ear_R": "head"}


def pca_stats(P):
    c = P.mean(0)
    cov = np.cov((P - c).T)
    vals, vecs = np.linalg.eigh(cov)
    o = np.argsort(-vals)
    axis = vecs[:, o[0]]
    sig = np.sqrt(np.maximum(vals[o], 0))
    along = (P - c) @ axis
    span = np.percentile(np.abs(along - np.median(along)), 90) * 2
    perp = (P - c) - np.outer((P - c) @ axis, axis)
    rad = float(np.percentile(np.linalg.norm(perp, axis=1), 90))
    return c, axis, float(span), rad, sig


def shortest_arc(u, v):
    """Quaternion (wxyz) rotating unit u onto unit v."""
    u = u / np.linalg.norm(u)
    v = v / np.linalg.norm(v)
    w = np.cross(u, v)
    q = np.array([1.0 + u @ v, *w])
    n = np.linalg.norm(q)
    if n < 1e-8:
        a = np.array([1.0, 0, 0]) if abs(u[0]) < 0.9 else np.array([0, 1.0, 0])
        w = np.cross(u, a)
        return np.array([0.0, *w / np.linalg.norm(w)])
    return q / n


def quat_rot(q, p):
    """Rotate points p (...,3) by quaternion wxyz q."""
    w, x, y, z = q
    R = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    return p @ R.T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cloud", default="capture/co3d/teddybear/34_1479_4753/pointcloud.ply")
    ap.add_argument("--out", default=".tmp/fitted_parts.json")
    ap.add_argument("--overlay", default=".tmp/fit_overlay.png")
    args = ap.parse_args()

    from sklearn.cluster import KMeans
    P = load_ply_points(args.cloud)
    rng = np.random.default_rng(0)
    S = P[rng.choice(len(P), 40000, replace=False)]
    km = KMeans(n_clusters=10, n_init=4, random_state=0).fit(S)
    # assign full cloud to nearest centroid (chunked)
    lab_full = np.empty(len(P), dtype=int)
    C = km.cluster_centers_
    for s in range(0, len(P), 100000):
        d = ((P[s:s + 100000, None, :] - C[None]) ** 2).sum(-1)
        lab_full[s:s + 100000] = d.argmin(1)

    parts = tc.assemble()
    by_name = {p["name"]: p for p in parts}

    # target stats per slot
    tgt = {}
    for slot, cl in CLUSTER_MAP.items():
        m = np.isin(lab_full, cl)
        tgt[slot] = pca_stats(P[m])
        c, axis, span, rad, _ = tgt[slot]
        print(f"{slot:12s} n={m.sum():6d} c=({c[0]:+.2f},{c[1]:+.2f},{c[2]:+.2f}) "
              f"axis=({axis[0]:+.2f},{axis[1]:+.2f},{axis[2]:+.2f}) span={span:.2f} rad={rad:.2f}")

    # global scale anchor: head height. CAD head r_y=0.165 vs measured head span
    mh = np.isin(lab_full, CLUSTER_MAP["head"])
    hy = np.percentile(P[mh, 1], [5, 95])
    scale = ((hy[1] - hy[0]) / 2) / by_name["head"]["r"][1]
    print(f"global scale (head): {scale:.3f}")

    fitted = []
    for p in parts:
        p = dict(p)
        name = p["name"]
        if name in tgt:
            c, axis, span, rad, _ = tgt[name]
            if p["prim"] == "capsule":
                # centroid-anchored: direction + length from the cluster, placed
                # at the measured centroid (pivot scaling assumed equal
                # proportions, which a different bear violates)
                u = axis / np.linalg.norm(axis)
                L = span * 0.8  # capsule core; caps add radius on both ends
                p["a"] = (c - u * L / 2).tolist()
                p["b"] = (c + u * L / 2).tolist()
                p["r"] = [float(rad * 0.95)] * 3
            else:  # ellipsoid / sphere: per-axis percentile fit
                m2 = np.isin(lab_full, CLUSTER_MAP[name])
                Q = P[m2]
                lo, hi = np.percentile(Q, 5, axis=0), np.percentile(Q, 95, axis=0)
                p["c"] = ((lo + hi) / 2).tolist()
                p["r"] = list(((hi - lo) / 2 * 0.9).astype(float))
        fitted.append(p)

    # children follow: limb segments continue along the parent's measured axis
    # from its distal end; head children keep their relative offset (per-axis)
    torso_c = np.array(next(x for x in fitted if x["name"] == "torso")["c"])
    for p in fitted:
        par = FOLLOWS.get(p["name"])
        if not par:
            continue
        parent_new = next(x for x in fitted if x["name"] == par)
        parent_old = by_name[par]
        p_orig = by_name[p["name"]]
        if parent_new["prim"] == "capsule" and p["prim"] == "capsule":
            a, b = np.array(parent_new["a"]), np.array(parent_new["b"])
            u = b - a
            u = u / np.linalg.norm(u)
            if np.dot(b - torso_c, u) < np.dot(a - torso_c, u):
                u = -u
                distal = a
            else:
                distal = b
            old_len = np.linalg.norm(np.array(p_orig["b"]) - np.array(p_orig["a"]))
            p["a"] = distal.tolist()
            p["b"] = (distal + u * old_len * scale).tolist()
            p["r"] = [r * scale for r in p_orig["r"]]
        else:  # ellipsoid parent (head): keep relative offset, per-axis ratio
            off = np.array(p_orig["c"], float) - np.array(parent_old["c"], float)
            ratio = np.array(parent_new["r"]) / np.array(parent_old["r"], float)
            p["c"] = (np.array(parent_new["c"]) + off * ratio).tolist()
            p["r"] = list((np.array(p_orig["r"]) * ratio).astype(float))

    with open(args.out, "w") as f:
        json.dump(fitted, f, indent=2)
    print(f"wrote {args.out}")

    # overlay: fitted surface samples vs real cloud
    sys.path.insert(0, r"E:\PythonChimera\tools")
    import teddy_body as tb
    tb.PARTS = fitted
    Q, _, _ = tb.sample_surface(n_per_part=2000, seed=0)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 7))
    ax[0].scatter(P[::20, 0], P[::20, 1], s=0.3, c="0.75")
    ax[0].scatter(Q[:, 0], Q[:, 1], s=0.8, c="tab:blue")
    ax[0].set_aspect("equal"); ax[0].set_title("front x-y")
    ax[1].scatter(P[::20, 2], P[::20, 1], s=0.3, c="0.75")
    ax[1].scatter(Q[:, 2], Q[:, 1], s=0.8, c="tab:blue")
    ax[1].set_aspect("equal"); ax[1].set_title("side z-y")
    plt.tight_layout(); plt.savefig(args.overlay, dpi=90)
    print(f"wrote {args.overlay}")


if __name__ == "__main__":
    main()
