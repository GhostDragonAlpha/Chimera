"""train_material.py -- learn the CONCEPT of a material from a donor genome, at library scale.

Two-stage, merging the project's two prior lessons:
  1. SELECT what is being sampled by chromaticity + log-intensity clustering
     (extract_materials.py: never raw RGB -- shading moves raw RGB; chroma IS the
     material's identity). This replaces hand-tuned luminance bands: the clusters
     ARE "lit fur", "shadow fur", "cream muzzle", "printed decal" -- and we train
     only the one we name. The operator/eye identifies; the code extracts.
  2. LEARN the selected cluster as a Gaussian mixture over [rgb, log scale, h, alpha]
     and synthesize fresh splats from it. A LIKELIHOOD FLOOR (reject below the p1
     score of the training data) means off-concept colors (green/purple/turquoise
     specks, tags, dye) can never be emitted -- zero density under the concept.

Every trained material is registered in <outdir>/library.json with provenance
(source genome, cluster, donor count) -- the systematic material list. Spray with
spray_parts.py --material <name>.

Usage:
  # 1. see what materials a genome contains
  .venv-gs/Scripts/python.exe tools/train_material.py --genome models/co3d/genomes/head.npz \
      --clusters 8 --outdir models/co3d/materials
  # 2. train the one you name
  .venv-gs/Scripts/python.exe tools/train_material.py --genome models/co3d/genomes/head.npz \
      --clusters 8 --pick 0 --name fur_brown --outdir models/co3d/materials
  # 3. train from an eye-QUALIFIED patch corpus (the littlebear lane -- the patch
  #    frame IS the membrane frame: h = relief above the backing floor, q_local =
  #    frame-relative fiber tilt; no chroma clustering, the region already selected)
  .venv-gs/Scripts/python.exe tools/train_material.py --corpus models/littlebear/corpus/fur_qualified.npz \
      --name fur_brown --outdir models/littlebear/materials
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from native.extract_materials import kmeans  # noqa: E402


def tip_line(h: np.ndarray, frac: float = 0.02) -> float:
    """The material's fur-tip elevation: scan the h histogram down from the top;
    where density collapses below `frac` of peak, fur has ended and what is
    above is floaters. Fallback: p99.5."""
    hist, edges = np.histogram(h, bins=60)
    peak = hist.max()
    for i in range(len(hist) - 1, int(hist.argmax()), -1):
        if hist[i] >= frac * peak:
            return float(edges[i + 1])
    return float(np.percentile(h, 99.5))


def chroma_features(rgb: np.ndarray) -> np.ndarray:
    """extract_materials' selection space: chromaticity direction + log intensity."""
    nrm = np.linalg.norm(rgb, axis=1, keepdims=True)
    return np.hstack([rgb / np.maximum(nrm, 1e-9), np.log(np.maximum(nrm, 1e-9))])


def phys_features(g: dict) -> np.ndarray:
    """What the mixture learns: color, size, relief, opacity (h in mm for scale parity)."""
    scale = np.clip(g["scale"], 1e-6, None)
    return np.column_stack([g["rgb"], np.log(scale), g["h"] * 1000.0, g["alpha"]]).astype(np.float64)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--genome", default=None)
    ap.add_argument("--corpus", default=None,
                        help="eye-qualified patch corpus npz (the littlebear lane); "
                             "mutually exclusive with --genome, needs no --clusters/--pick")
    ap.add_argument("--clusters", type=int, default=None)
    ap.add_argument("--pick", type=int, default=None, help="cluster index to train")
    ap.add_argument("--name", default=None)
    ap.add_argument("--components", type=int, default=12)
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()

    if bool(a.genome) == bool(a.corpus):
        raise SystemExit("REFUSED: exactly one of --genome / --corpus")
    if not a.name:
        raise SystemExit("REFUSED: training needs --name (a material is a named thing)")

    from sklearn.mixture import GaussianMixture

    if a.corpus:
        # corpus rows: [u, v, h, r, g, b, alpha, log_sx, log_sy, log_sz, qw..qz]
        # (padding rows have alpha 0). The patch frame IS the membrane frame:
        # h = meters above the backing floor; q_local = frame-relative fiber tilt.
        d = np.load(a.corpus)
        P = d["patches"].reshape(-1, 14).astype(np.float64)
        P = P[P[:, 6] > 0]
        X = np.column_stack([P[:, 3:6], P[:, 7:10], P[:, 2] * 1000.0, P[:, 6]])
        scale = np.exp(P[:, 7:10])
        h = P[:, 2]
        q_local = P[:, 10:14]
        source, region, cluster, n0 = a.corpus, Path(a.corpus).stem, None, len(P)
    else:
        g = dict(np.load(a.genome))
        region = Path(a.genome).stem
        n0 = len(g["rgb"])
        labels, _ = kmeans(chroma_features(g["rgb"].astype(np.float64)), a.clusters)

        table = []
        for j in range(a.clusters):
            sel = labels == j
            if not sel.any():
                continue
            c = g["rgb"][sel].mean(0)
            lum = float(c @ np.array([0.299, 0.587, 0.114]))
            table.append({"cluster": int(j), "n": int(sel.sum()), "color": [float(x) for x in c],
                          "luminance": lum})
        table.sort(key=lambda e: -e["n"])
        print(f"{region}: {n0} splats -> {len(table)} clusters (chroma + log intensity)")
        for e in table:
            c = [round(x, 2) for x in e["color"]]
            print(f"  [{e['cluster']}] n={e['n']:6d}  rgb={c}  lum={e['luminance']:.2f}")

        if a.pick is None:
            print("\n--pick <cluster> --name <material> to train one")
            return 0
        sel = labels == a.pick
        gs = {k: (v[sel] if isinstance(v, np.ndarray) and len(v) == len(sel) else v)
              for k, v in g.items()}
        tip = tip_line(gs["h"])
        above = gs["h"] <= tip
        print(f"tip line: {tip*1000:.1f}mm -- dropping {int((~above).sum())} floaters above it")
        gs = {k: (v[above] if isinstance(v, np.ndarray) and len(v) == len(above) else v)
              for k, v in gs.items()}
        X = phys_features(gs)
        scale = np.clip(gs["scale"], 1e-6, None)
        h = gs["h"]
        q_local = gs["q_local"]
        source, cluster = a.genome, a.pick

    gm = GaussianMixture(n_components=a.components, covariance_type="full",
                         reg_covar=1e-6, max_iter=500, random_state=0)
    gm.fit(X)
    floor = float(np.percentile(gm.score_samples(X), 1))

    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cap = float(np.percentile(scale.max(1), 99))  # real fiber-length bound
    rgb_lo = np.percentile(X[:, 0:3], 1, axis=0)   # the material's real color box:
    rgb_hi = np.percentile(X[:, 0:3], 99, axis=0)  # synthesized colors never leave it
    np.savez_compressed(
        outdir / f"{a.name}.npz",
        weights=gm.weights_, means=gm.means_, covariances=gm.covariances_,
        floor=np.array([floor]), scale_cap=np.array([cap]),
        rgb_lo=rgb_lo, rgb_hi=rgb_hi,
        h_lo=np.array([np.percentile(h, 1)]), h_tip=np.array([np.percentile(h, 99.5)]),
        q_local=q_local,  # real fiber-tilt quats, bootstrapped at spray time
        feature_names=np.array(["r", "g", "b", "log_sx", "log_sy", "log_sz", "h_mm", "alpha"]),
    )
    rec = {
        "name": a.name, "source": source, "source_region": region,
        "cluster": cluster, "donor_count": int(n0), "n_train": int(len(X)),
        "components": a.components, "floor_loglik": floor,
        "mean_color": [float(x) for x in X[:, 0:3].mean(0)],
        "trained_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (outdir / f"{a.name}.json").write_text(json.dumps(rec, indent=2))
    lib_p = outdir / "library.json"
    lib = json.loads(lib_p.read_text()) if lib_p.exists() else {"materials": []}
    lib["materials"] = [m for m in lib["materials"] if m["name"] != a.name] + [rec]
    lib_p.write_text(json.dumps(lib, indent=2))
    print(f"{a.name}: trained on {len(X)} splats, floor={floor:.1f}, "
          f"mean color={[round(float(x),2) for x in rec['mean_color']]}")
    print(f"-> {outdir / (a.name + '.npz')} + registered in library.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
