"""Paint-by-assignment: color a settled coat from a target splat cloud.

The operator's rule: the generator's front is real; its back is a blended
average — so we REPLACE the back with an assignment. Front-facing settled
splats sample their nearest same-part target splats directly; back-facing
splats sample the MIRROR of the front within the same part (z mirrored about
the part centroid). Face parts (muzzle, eyes) only ever sample their own
label, so features never wrap around the head.

Sparse-part fallback: a part with <50 target samples borrows its opposite-side
twin (x mirrored about the spine), then its parent, then the global cloud.

Usage: python tools/paint_from_splat.py target.splat coat.splat out.splat
"""
import json
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\ChimeraEngine")
sys.path.insert(0, r"E:\PythonChimera\tools")
import cpp_bridge as cb  # noqa: E402
import teddy_catalog as tc  # noqa: E402

K = 4          # IDW neighbors
MIN_POOL = 50  # sparse-part threshold


def main(target_path, coat_path, out_path, parts_json=None):
    from scipy.spatial import cKDTree

    T = cb.load_splat(target_path)
    T = T[T[:, 6] >= 0.5]
    TP, TC = T[:, 0:3], T[:, 3:6]

    buf = cb.load_splat(coat_path)
    meta = np.load(coat_path.replace(".splat", ".meta.npz"))
    pid = meta["part_id"]
    P = buf[:, 0:3]

    if parts_json is None:
        parts_json = coat_path.replace(".splat", "").replace("authbear5_coat", "") or None
    names = [p["name"] for p in tc.assemble()]

    # label the target cloud by nearest settled splat (coat is in target frame)
    coat_tree = cKDTree(P)
    dist, idx = coat_tree.query(TP, k=1)
    TL = pid[idx]
    ok = dist < 0.10

    # part centroids (from the settled coat) for the front/back mirror
    cents = np.array([P[pid == i].mean(0) if (pid == i).any() else np.zeros(3)
                      for i in range(len(names))])

    # opposite-side twin for sparse fallback
    spine_x = np.median(TP[:, 0])
    twin = {}
    for i, n in enumerate(names):
        if n.endswith("_L") and n[:-2] + "_R" in names:
            twin[i] = names.index(n[:-2] + "_R")
        elif n.endswith("_R") and n[:-2] + "_L" in names:
            twin[i] = names.index(n[:-2] + "_L")

    global_tree = cKDTree(TP)
    out_rgb = np.zeros((len(P), 3))

    # parts whose back must NOT be z-mirrored onto the front: the face lives
    # on the front of the head, so mirroring head splats paints eyes/muzzle
    # colors onto the back of the skull. These sample their pool directly.
    NO_MIRROR = {"head", "muzzle", "eye_L", "eye_R"}

    stats = {"direct": 0, "mirror_back": 0, "twin": 0, "global": 0}
    for i, name in enumerate(names):
        m = pid == i
        if not m.any():
            continue
        pool = (TL == i) & ok
        use_twin = False
        if pool.sum() < MIN_POOL and i in twin and ((TL == twin[i]) & ok).sum() >= MIN_POOL:
            pool = (TL == twin[i]) & ok
            use_twin = True
            stats["twin"] += 1
        if pool.sum() < MIN_POOL:
            # global fallback: nearest target splats regardless of label
            d, j = global_tree.query(P[m], k=K)
            w = 1.0 / np.maximum(d, 1e-4)
            out_rgb[m] = (TC[j] * w[..., None]).sum(1) / w.sum(1, keepdims=True)
            stats["global"] += 1
            continue
        Q, QC = TP[pool], TC[pool]
        tree = cKDTree(Q)
        zc = cents[i][2]
        Pm = P[m].copy()
        if use_twin:  # borrowed twin pool: mirror the query in x
            Pm[:, 0] = 2 * spine_x - Pm[:, 0]
        back = (Pm[:, 2] < zc) & (name not in NO_MIRROR)
        stats["direct"] += int((~back).sum())
        stats["mirror_back"] += int(back.sum())
        Pm[back, 2] = 2 * zc - Pm[back, 2]  # the assignment: back samples front
        d, j = tree.query(Pm, k=K)
        w = 1.0 / np.maximum(d, 1e-4)
        out_rgb[m] = (QC[j] * w[..., None]).sum(1) / w.sum(1, keepdims=True)

    buf[:, 3:6] = np.clip(out_rgb, 0.0, 1.0)
    buf[:, 6] = 0.95
    buf[:, 7:10] *= 1.35  # grow splats: closes settle gaps at part seams
    cb.save_splat(out_path, buf)
    print(f"painted {len(P)} splats: {stats}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3],
         sys.argv[4] if len(sys.argv) > 4 else None)
