"""splat_denoise.py -- clean a trained 3DGS cloud: kill floaters, chads, and haze.

WHY (operator directive, 2026-08-20): "use a high-detailed quality model that has lots of
noise; find a program that gets rid of the noise or develop specialized techniques
ourselves." Trained 3DGS clouds (movie pipeline teddyloop/genbear, LGM-class outputs)
carry detail AND noise: floaters (isolated splats far from the body), chads (stretched
slivers hanging off the silhouette), haze (low-alpha dust). The generator's job is detail;
this tool's job is cleanup. They are separate membranes.

RULE 0:
  STATEMENT  — the noise classes are geometrically separable from the body: floaters are
               distance outliers, chads are anisotropy outliers, haze is opacity outliers.
               The bear is none of those.
  PREDICTION — after filtering, the 6-angle judge structure score rises (or holds) while
               splat count drops by the noise fraction.
  FALSIFIER  — if the cleaned cloud loses bear surface (holes, missing limbs) or the
               judge score does not improve, the classes are NOT separable by these
               statistics and this tool reports that honestly.

FILTERS (applied in order, each reports its kill count):
  1. opacity floor    — alpha < --alpha-min
  2. elongation clamp — max(scale)/min(scale) > --max-aniso (chads; legit fur disks are
                        ~10:1, chads measure 50-200:1). With --clamp-aniso the splat is
                        RESHAPED instead of deleted: the longest axis is capped at
                        shortest*value, keeping coverage while de-needling.
  3. giant clamp      — max(scale) > median + --giant-sigma * MAD (blobs bigger than any
                        real surface patch)
  4. SOR              — kNN mean-distance z-score > --sor-std (floaters; classic
                        statistical outlier removal from point-cloud practice)
  5. blob keep        — connected components on a radius graph (radius = --blob-r x
                        median NN distance); keep components covering >= --blob-min of
                        remaining splats (default: keep largest only)

Usage:
  .venv-gs/Scripts/python.exe tools/splat_denoise.py <in.ply|in.splat> --out <out.splat> [flags]
Prints a per-filter report; writes <out>.denoise.json with the numbers.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
sys.path.insert(0, str(ROOT / "ChimeraEngine" / "native"))

import cpp_bridge as cb  # noqa: E402
from ply_to_splat import load_3dgs_ply  # noqa: E402


def load_any(path: str) -> np.ndarray:
    if path.endswith(".splat"):
        return cb.load_splat(path)
    return load_3dgs_ply(path)


def denoise(buf: np.ndarray, a) -> tuple[np.ndarray, dict]:
    report = {"in": int(len(buf)), "filters": {}}
    keep = np.ones(len(buf), dtype=bool)

    def apply(name: str, bad: np.ndarray) -> None:
        nonlocal keep
        killed = int((keep & bad).sum())
        report["filters"][name] = killed
        keep &= ~bad

    # 1. opacity floor
    apply("opacity", buf[:, 6] < a.alpha_min)

    # 2. elongation: either RESHAPE (clamp long axis, keeps coverage) or delete
    sc = buf[:, 7:10]
    aniso = sc.max(axis=1) / np.maximum(sc.min(axis=1), 1e-12)
    if a.clamp_aniso is not None:
        idx = np.where(aniso > a.clamp_aniso)[0]
        for i in idx:  # cap the longest axis at shortest*clamp (coverage kept)
            row = buf[i, 7:10].copy()
            buf[i, 7 + int(np.argmax(row))] = row.min() * a.clamp_aniso
        report["filters"]["elongation_clamped"] = int(len(idx))
    else:
        apply("elongation", aniso > a.max_aniso)

    # 3. giant clamp
    smax = sc.max(axis=1)
    med = np.median(smax)
    mad = np.median(np.abs(smax - med)) + 1e-12
    apply("giant", smax > med + a.giant_sigma * mad)

    if not keep.any():
        return buf[:0], report

    # 4. SOR: kNN mean distance outliers
    from scipy.spatial import cKDTree
    live = buf[keep]
    tree = cKDTree(live[:, 0:3])
    k = min(a.sor_k + 1, len(live))
    dists, _ = tree.query(live[:, 0:3], k=k)
    md = dists[:, 1:].mean(axis=1)  # exclude self
    mu, sd = md.mean(), md.std() + 1e-12
    bad_live = md > mu + a.sor_std * sd
    bad = np.zeros(len(buf), dtype=bool)
    bad[np.where(keep)[0][bad_live]] = True
    apply("sor", bad)
    report["sor_threshold"] = float(mu + a.sor_std * sd)
    report["sor_median_nn"] = float(np.median(md))

    # 5. blob keep
    if a.blob_keep and keep.any():
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        live_idx = np.where(keep)[0]
        pts = buf[live_idx, 0:3]
        tree = cKDTree(pts)
        r = a.blob_r * float(np.median(md))
        pairs = tree.query_pairs(r, output_type="ndarray")
        if len(pairs) == 0:
            apply("blob", np.zeros(len(buf), dtype=bool))
        else:
            g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])),
                           shape=(len(pts), len(pts)))
            n_comp, labels = connected_components(g, directed=False)
            sizes = np.bincount(labels, minlength=n_comp)
            keep_labels = set(np.where(sizes >= max(2, a.blob_min * len(pts)))[0].tolist())
            if not keep_labels:
                keep_labels = {int(np.argmax(sizes))}
            bad_live = np.array([l not in keep_labels for l in labels])
            bad = np.zeros(len(buf), dtype=bool)
            bad[live_idx[bad_live]] = True
            apply("blob", bad)
            report["blob_radius"] = r
            report["blob_components"] = int(n_comp)
            report["blob_kept"] = sorted([int(sizes[l]) for l in keep_labels], reverse=True)[:5]

    report["out"] = int(keep.sum())
    return buf[keep], report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--alpha-min", type=float, default=0.08)
    ap.add_argument("--max-aniso", type=float, default=30.0)
    ap.add_argument("--clamp-aniso", type=float, default=None,
                    help="reshape instead of delete: cap longest axis at shortest*value")
    ap.add_argument("--giant-sigma", type=float, default=12.0)
    ap.add_argument("--sor-k", type=int, default=12)
    ap.add_argument("--sor-std", type=float, default=2.0)
    ap.add_argument("--blob-keep", action="store_true")
    ap.add_argument("--blob-r", type=float, default=4.0,
                    help="graph radius as multiple of median NN distance")
    ap.add_argument("--blob-min", type=float, default=0.0,
                    help="min component size as fraction of live splats (0 = keep largest)")
    a = ap.parse_args()

    buf = load_any(a.src)
    out, report = denoise(buf, a)
    print(json.dumps(report, indent=1))
    if len(out) == 0:
        print("REFUSED: filter chain killed everything -- loosen parameters")
        return 1
    cb.save_splat(a.out, out)
    Path(a.out + ".denoise.json").write_text(json.dumps(report, indent=1))
    print(f"saved {a.out}: {len(out)} splats ({100.0*len(out)/report['in']:.1f}% kept)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
