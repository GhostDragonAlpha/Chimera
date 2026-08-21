"""cut_patches.py -- cut flat reference-plane training patches from donor genomes.

A patch is a TRUE 3D splat field re-based onto one shared plane: the seed core
point's tangent frame is the ground floor (h=0) and every splat floats at its
measured relief with its full 14-variable record. The generator learns the
relief PATTERN (elevation is geometry, not paint); the wrapper drapes the
generated sheet over any CAD part.

"Flat" = same plane, not 2D representation (operator, 2026-08-21).

Per-splat feature vector (14): [u, v, h, r, g, b, alpha, log_sx, log_sy,
log_sz, qw, qx, qy, qz] -- u,v,h in METERS in the seed plane frame; quats are
core-frame-relative (q_local), canonicalized to w>=0.

Usage:
  .venv-gs/Scripts/python.exe tools/cut_patches.py --shells models/co3d/bear34_shells.npz \
      --genomes models/co3d/genomes --regions head ear_L ear_R snout paw_L foot_L foot_R \
      --out models/co3d/corpus/fur.npz
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from extract_genomes import core_frames  # noqa: E402
from train_material import tip_line  # noqa: E402

PATCH_HALF = 0.020   # 40 mm square window
STRIDE = 0.020       # overlapping seeds
N_PTS = 512          # fixed patch cardinality (pad/subsample)
H_MIN, H_MAX = -0.003, 0.015


def decode_world(genome: dict, shells) -> np.ndarray:
    """Lossless genome decode (extract_genomes' falsifier proved this path)."""
    inner = shells["inner"].astype(np.float64)
    _, frames = core_frames(shells)
    ci = genome["core_idx"]
    fr = frames[ci]
    return (inner[ci] + genome["h"][:, None] * fr[:, :, 2]
            + genome["u"][:, None] * fr[:, :, 0]
            + genome["v"][:, None] * fr[:, :, 1])


def rebase(pos: np.ndarray, seed: np.ndarray, frame: np.ndarray) -> np.ndarray:
    rel = pos - seed
    return np.stack([rel @ frame[:, 0], rel @ frame[:, 1], rel @ frame[:, 2]], 1)


def membrane_plane(inner: np.ndarray, idx: np.ndarray, seed: np.ndarray,
                   frame: np.ndarray):
    """Robust local plane through the MEMBRANE points of the window: this plane
    is the patch zero (the thin sheet), flattening curvature/slope so relief is
    learned around the material's own surface."""
    P = inner[idx]
    c = P.mean(0)
    _, _, Vt = np.linalg.svd(P - c, full_matrices=False)
    n = Vt[2]
    if n @ frame[:, 2] < 0:
        n = -n
    t1 = frame[:, 0] - (frame[:, 0] @ n) * n
    t1 /= np.linalg.norm(t1)
    t2 = np.cross(n, t1)
    return c, np.stack([t1, t2, n], 1)


def patches_from_region(genome: dict, shells, rng) -> np.ndarray:
    inner = shells["inner"].astype(np.float64)
    _, frames = core_frames(shells)
    ci = genome["core_idx"]
    pos = decode_world(genome, shells)

    # seed grid: core points covered by this region, thinned to the stride
    seeds_all = np.unique(ci)
    picked, seen = [], set()
    for s in seeds_all:
        cell = tuple((inner[s] / STRIDE).astype(int))
        if cell not in seen:
            seen.add(cell)
            picked.append(s)
    out = []
    from scipy.spatial import cKDTree
    itree = cKDTree(inner)
    for s in picked:
        midx = itree.query_ball_point(inner[s], PATCH_HALF * 1.5)
        if len(midx) < 5:
            continue
        c0, plane = membrane_plane(inner, midx, inner[s], frames[s])
        uvz = rebase(pos, c0, plane)
        m = (np.abs(uvz[:, 0]) <= PATCH_HALF) & (np.abs(uvz[:, 1]) <= PATCH_HALF) & \
            (uvz[:, 2] >= H_MIN) & (uvz[:, 2] <= H_MAX)
        if m.sum() < 64:
            continue
        idx = np.nonzero(m)[0]
        if len(idx) > N_PTS:
            idx = rng.choice(idx, size=N_PTS, replace=False)
        feat = np.zeros((N_PTS, 14), dtype=np.float32)
        feat[:len(idx), 0:3] = uvz[idx]
        feat[:len(idx), 3:6] = genome["rgb"][idx]
        feat[:len(idx), 6] = genome["alpha"][idx]
        feat[:len(idx), 7:10] = np.log(np.clip(genome["scale"][idx], 1e-6, None))
        q = genome["q_local"][idx].copy()
        q[q[:, 0] < 0] *= -1  # canonical hemisphere
        feat[:len(idx), 10:14] = q
        feat[len(idx):, 6] = 0.0  # padding: alpha 0 -> invisible, harmless
        out.append(feat)
    return np.stack(out) if out else np.zeros((0, N_PTS, 14), np.float32)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--shells", required=True)
    ap.add_argument("--genomes", required=True)
    ap.add_argument("--regions", nargs="+", required=True)
    ap.add_argument("--material", default="fur_brown", help="corpus label")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    shells = np.load(a.shells)
    rng = np.random.default_rng(0)
    all_p = []
    for reg in a.regions:
        g = dict(np.load(Path(a.genomes) / f"{reg}.npz"))
        # 14-var provenance gate (operator: mandatory)
        need = {"core_idx", "h", "u", "v", "q_local", "scale", "rgb", "alpha"}
        if need - set(g):
            raise SystemExit(f"REFUSED: {reg} genome missing {sorted(need - set(g))}")
        tip = tip_line(g["h"])  # density cutoff: fur ends, floaters begin
        keep = g["h"] <= tip
        g = {k: (v[keep] if isinstance(v, np.ndarray) and len(v) == len(keep) else v)
             for k, v in g.items()}
        print(f"{reg:9s} tip line {tip*1000:5.1f}mm, dropped {int((~keep).sum())} floaters")
        p = patches_from_region(g, shells, rng)
        print(f"{reg:9s} genome n={len(g['rgb']):6d} -> {len(p):4d} patches")
        all_p.append(p)
    P = np.concatenate(all_p)
    occ = (P[:, :, 6] > 0).sum(1)
    print(f"total {len(P)} patches, splats/patch p10/p50/p90: "
          f"{np.percentile(occ, [10, 50, 90]).astype(int)}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, patches=P, material=a.material,
                        feature_names=np.array(["u", "v", "h", "r", "g", "b", "alpha",
                                                "log_sx", "log_sy", "log_sz",
                                                "qw", "qx", "qy", "qz"]))
    print("->", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
