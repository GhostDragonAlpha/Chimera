"""Export RECOVERED material genomes to a machine-readable file the trainer can consume.

This is the wire between the two halves of the system:

    Construction/  (measure reality)  ->  recovered_genomes.json  ->  train_splat_compositions.py

Until now `train_splat_compositions.py` scored a composition by KEYWORD-MATCHING the English
text of a 40-questions document ("if the answer contains 'fiber', it should use fiber splats").
That is the studio's own named failure mode -- grading an adjective. This replaces it with the
measured splat-configuration distribution of real material, recovered from a real scan.

The feature set is identical to Construction/take_dna_full.py, so the numbers are comparable:

    size    = sorted(scale)[1]                 middle principal axis
    aniso   = 1 - sorted(scale)[0]/sorted(scale)[2]    0 = blob, 1 = flat/elongated
    R,G,B   = colour
    opacity

Each is reported as mean + [p10 .. p90] -- a genome is a DISTRIBUTION, never an average,
and it is a RANGE, not a value.

Usage:
    python Construction/export_genome.py <scan.splat|.ksplat|.ply> --clusters 8
    python Construction/export_genome.py <scan> --name-map bark=wood,ground=sand
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Construction.ksplat_io import load_any  # noqa: E402

FEATURES = ["size", "aniso", "R", "G", "B", "opacity"]
OUT_DEFAULT = Path(__file__).resolve().parents[1] / "Chimera/docs/matter/recovered_genomes.json"


def config_features(scale: np.ndarray, rgb: np.ndarray, opac: np.ndarray) -> dict:
    """The splat-configuration feature set. Identical maths to take_dna_full.py."""
    ss = np.sort(scale, 1)
    return {
        "size": ss[:, 1],
        "aniso": 1.0 - ss[:, 0] / (ss[:, 2] + 1e-9),
        "R": rgb[:, 0], "G": rgb[:, 1], "B": rgb[:, 2],
        "opacity": opac,
    }


def distribution(values: np.ndarray) -> dict:
    """A feature's genome: mean plus the p10..p90 range that actually names it."""
    return {
        "mean": float(np.mean(values)),
        "p10": float(np.percentile(values, 10)),
        "p90": float(np.percentile(values, 90)),
        "std": float(np.std(values)),
    }


def cluster_genomes(path: str, k: int = 8, sample: int = 400_000, seed: int = 0) -> dict:
    """Split a scan into k material clusters and report each one's genome."""
    pos, rgb, opac, scale, _quat = load_any(path, full=True)
    rng = np.random.default_rng(seed)

    solid = np.where(opac > 0.5)[0]          # opaque SURFACE splats -- haze is not a material
    if len(solid) == 0:
        solid = np.arange(len(opac))
    idx = rng.choice(solid, min(sample, len(solid)), replace=False)

    feat = config_features(scale[idx], rgb[idx], opac[idx])
    raw = np.stack([np.log(feat["size"] + 1e-6), feat["aniso"],
                    feat["R"], feat["G"], feat["B"], feat["opacity"]], 1).astype(np.float32)
    Z = (raw - raw.mean(0)) / (raw.std(0) + 1e-9)

    # k-means (numpy; the GPU path lives in codebook.py for whole-scene work)
    C = Z[rng.choice(len(Z), k, replace=False)].copy()
    for _ in range(40):
        d = ((Z[:, None, :] - C[None, :, :]) ** 2).sum(2)
        lab = d.argmin(1)
        for j in range(k):
            m = lab == j
            if m.any():
                C[j] = Z[m].mean(0)

    genomes = {}
    for j in range(k):
        m = lab == j
        if m.sum() < 200:
            continue
        genomes[f"cluster_{j:02d}"] = {
            "n_splats": int(m.sum()),
            "fraction": float(m.mean()),
            "features": {f: distribution(feat[f][m]) for f in FEATURES},
        }
    return genomes


def merge_specimens(specimens: list, name: str) -> dict:
    """Combine N scans of the SAME KIND of thing into one class genome.

    THE POINT (operator, 2026-07-23): "we'll have to go out and get like two versions of
    everything in order for variants to show up."

    One specimen gives you WITHIN-object variation -- blade to blade on a single tuft.
    What makes a class read as a class is BETWEEN-specimen variation: this tuft is taller,
    that one yellower, this one sparser. With one scan you cannot separate "this
    individual happens to be like this" from "members of this class differ like this",
    so every child comes out a rearrangement of the same individual.

    Total variance = within + between (law of total variance). We record both, so a child
    can be drawn from the class rather than from one lucky specimen.
    """
    if len(specimens) < 2:
        raise ValueError(f'{name}: need >= 2 specimens to measure between-specimen '
                         f'variation, got {len(specimens)}')

    feats = {}
    for f in FEATURES:
        means = np.array([s['features'][f]['mean'] for s in specimens], dtype=float)
        within = np.array([s['features'][f]['std'] for s in specimens], dtype=float)
        w = np.array([s['n_splats'] for s in specimens], dtype=float)
        w = w / w.sum()

        grand = float((means * w).sum())
        between_var = float((w * (means - grand) ** 2).sum())
        within_var = float((w * within ** 2).sum())
        total_std = float(np.sqrt(within_var + between_var))

        feats[f] = {
            'mean': grand,
            'std': total_std,
            'p10': grand - 1.2816 * total_std,
            'p90': grand + 1.2816 * total_std,
            'within_std': float(np.sqrt(within_var)),
            'between_std': float(np.sqrt(between_var)),
            'specimen_means': [round(float(m), 5) for m in means],
        }

    ratio = np.mean([feats[f]['between_std'] / (feats[f]['within_std'] + 1e-9)
                     for f in FEATURES])
    return {
        'n_specimens': len(specimens),
        'n_splats': int(sum(s['n_splats'] for s in specimens)),
        'features': feats,
        'between_within_ratio': float(ratio),
        '_provenance': f'CLASS genome merged from {len(specimens)} specimens',
        '_note': ('between_std is the variation that makes siblings look like different '
                  'individuals rather than rearrangements of one. A ratio near zero means '
                  'the specimens were nearly identical and more varied samples are needed.'),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scan", help="path to a .splat / .ksplat / .ply scan")
    ap.add_argument("--clusters", type=int, default=8)
    ap.add_argument("--sample", type=int, default=400_000)
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--name-map", default="",
                    help="cluster_00=rock,cluster_03=sand -- map clusters to matter-library names")
    args = ap.parse_args()

    print(f"reading {args.scan}")
    genomes = cluster_genomes(args.scan, args.clusters, args.sample)
    print(f"  recovered {len(genomes)} material genomes")

    if args.name_map:
        for pair in args.name_map.split(","):
            if "=" not in pair:
                continue
            src, dst = (s.strip() for s in pair.split("=", 1))
            if src in genomes:
                genomes[dst] = genomes.pop(src)
                print(f"  {src} -> {dst}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {}
    if out.exists():
        try:
            payload = json.loads(out.read_text())
        except Exception:
            payload = {}
    payload.setdefault("genomes", {}).update(genomes)
    payload["_provenance"] = "MEASURED from a real scan by Construction/export_genome.py"
    payload["_features"] = FEATURES
    payload["_note"] = ("Each feature is mean + p10..p90. A genome is a DISTRIBUTION, not an "
                        "average, and a RANGE, not a value. Consumed by "
                        "core/train_splat_compositions.py as the optical target.")
    out.write_text(json.dumps(payload, indent=2))
    print(f"wrote {out}")

    for name, g in list(genomes.items())[:12]:
        f = g["features"]
        print(f"  {name:14} {g['fraction']*100:5.1f}%  "
              f"size {f['size']['mean']:.4f}  aniso {f['aniso']['mean']:.2f}  "
              f"rgb [{f['R']['mean']:.2f} {f['G']['mean']:.2f} {f['B']['mean']:.2f}]")


if __name__ == "__main__":
    main()
