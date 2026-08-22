"""extract_materials.py — EXTRACT step: material genomes from a 3DGS .splat bear.

THE DYAD'S DIVISION OF LABOR (THE_BEAR_PIPELINE.md §3):
  - The EYE (senses.py) decides what materials EXIST — it watched the orbit movie and
    named them (that count k and those names are passed in, never derived here).
  - The CODE extracts the genomes: cluster every splat by chromaticity (harvest_material's
    principle — never raw RGB, shading moves raw RGB), then measure per cluster:
      color    = mean linear RGB
      log_size = mean ln(geomean(sx,sy,sz))   (texture genome: splat scale)
      aniso    = mean(max(s)/min(s))          (texture genome: ellipsoid stretch)
      opacity  = mean alpha                   (texture genome: see-through-ness)
      bbox     = [min xyz, max xyz]           (region — approximate, the eye refines)

A material genome contains NO positions beyond that bbox (harvest_material.py's law):
distributions that can be repainted onto any geometry.

  python ChimeraEngine/native/extract_materials.py <splat> --k 3 --out <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))


def kmeans(features: np.ndarray, k: int, seed: int = 0, iters: int = 25,
           fit_n: int = 40_000):
    """k-means with kmeans++ init, fit on a random subset, then assign ALL points.
    Features are z-scored on the fit subset (whitening is DERIVED from the data — it is
    what lets a brightness difference like cream-vs-tan compete with a hue difference
    like fur-vs-nose without a hand-picked weight)."""
    rng = np.random.default_rng(seed)
    fit_idx = rng.choice(len(features), size=min(fit_n, len(features)), replace=False)
    mu = features[fit_idx].mean(0)
    sd = features[fit_idx].std(0) + 1e-12
    X = ((features[fit_idx] - mu) / sd).astype(np.float64)
    # kmeans++ seeding
    cent = [X[rng.integers(len(X))]]
    for _ in range(k - 1):
        d = np.min(((X[:, None, :] - np.array(cent)[None]) ** 2).sum(-1), axis=1)
        cent.append(X[rng.choice(len(X), p=d / d.sum())])
    cent = np.array(cent)
    for _ in range(iters):
        lab = ((X[:, None, :] - cent[None]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            if (lab == j).any():
                cent[j] = X[lab == j].mean(0)
    F = ((features - mu) / sd).astype(np.float64)
    return ((F[:, None, :] - cent[None]) ** 2).sum(-1).argmin(1).astype(np.int32), cent


def extract(splat_path: str, k: int) -> dict:
    import cpp_bridge as cb

    buf = cb.load_splat(splat_path)
    pos, rgb, alpha = buf[:, 0:3].astype(np.float64), buf[:, 3:6].astype(np.float64), buf[:, 6]
    scale = buf[:, 7:10].astype(np.float64)

    # chromaticity direction (rgb/|rgb|) + log intensity: hue separates fur from the
    # black nose; intensity separates the cream pads from the tan plush (same hue,
    # different value — pure chromaticity cannot see it, measured 2026-08-18).
    nrm = np.linalg.norm(rgb, axis=1, keepdims=True)
    feat = np.hstack([rgb / np.maximum(nrm, 1e-9), np.log(np.maximum(nrm, 1e-9))])
    labels, _ = kmeans(feat, k)

    out = {}
    for j in range(k):
        sel = labels == j
        if not sel.any():
            continue
        s = scale[sel]
        geo = np.cbrt(s[:, 0] * s[:, 1] * s[:, 2])
        out[f"cluster_{j}"] = {
            "i": int(j),
            "n": int(sel.sum()),
            "color": rgb[sel].mean(0).tolist(),
            "log_size": float(np.log(np.maximum(geo, 1e-12)).mean()),
            "aniso": float((s.max(1) / np.maximum(s.min(1), 1e-12)).mean()),
            "opacity": float(alpha[sel].mean()),
            "bbox": (pos[sel].min(0).tolist(), pos[sel].max(0).tolist()),
        }
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("splat")
    ap.add_argument("--k", type=int, required=True, help="material count — the EYE's call")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    mats = extract(args.splat, args.k)
    Path(args.out).write_text(json.dumps(mats, indent=1), encoding="utf-8")
    for name, m in mats.items():
        c = [round(x, 3) for x in m["color"]]
        print(f"{name}: n={m['n']} color={c} log_size={m['log_size']:.3f} "
              f"aniso={m['aniso']:.2f} opacity={m['opacity']:.3f}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
