"""Crop an AnySplat PLY to the subject using the predicted camera orbit.

AnySplat reconstructs the whole scene, including the video's background as a giant
dark ring far outside the orbit. The cameras all point at the subject, so:
  orbit_center = centroid of camera positions (world2cam extrinsic -> cam pos = -R^T t)
  keep splats with dist(pos, orbit_center) < frac * median(camera-orbit radius)

Writes a new PLY with the same properties, rows masked.
"""
import argparse
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ChimeraEngine", "native"))
sys.path.insert(0, os.path.join(_HERE, "..", "ChimeraEngine"))

from plyfile import PlyData, PlyElement  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ply")
    ap.add_argument("--extrinsic", required=True, help="<name>_extrinsic.npy from anysplat_recon.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--frac", type=float, default=0.6,
                    help="keep radius as a fraction of the median camera orbit radius")
    args = ap.parse_args()

    ext = np.load(args.extrinsic)  # (K,3,4) or (K,4,4)
    R = ext[:, :3, :3].astype(np.float64)
    t = ext[:, :3, 3].astype(np.float64)
    # Convention auto-detect: an orbit is a tight ring, so the correct reading of the
    # extrinsic has the LOWEST relative spread of camera distances from their centroid.
    #   cam2world: camera position = t
    #   world2cam: camera position = -R^T t
    cands = {
        "cam2world": t,
        "world2cam": -np.einsum("kij,ki->kj", R.transpose(0, 2, 1), t),
    }
    best, best_cv = None, None
    for name, cp in cands.items():
        r = np.linalg.norm(cp - cp.mean(0), axis=1)
        cv = float(r.std() / max(np.median(r), 1e-9))
        print(f"[crop] {name}: orbitR med {np.median(r):.3f} spread {r.std():.3f} (cv {cv:.3f})")
        if best_cv is None or cv < best_cv:
            best, best_cv = cp, cv
    campos = best
    center = campos.mean(0)
    med_r = float(np.median(np.linalg.norm(campos - center, axis=1)))
    keep_r = args.frac * med_r
    print(f"[crop] orbit center {np.round(center, 3)}, keep radius {keep_r:.3f}")

    ply = PlyData.read(args.ply)
    verts = ply["vertex"].data
    pos = np.stack([verts["x"], verts["y"], verts["z"]], axis=1).astype(np.float64)
    d = np.linalg.norm(pos - center, axis=1)
    mask = d < keep_r
    print(f"[crop] {len(mask)} -> {int(mask.sum())} splats")
    if mask.sum() == 0:
        raise SystemExit("crop killed everything — check the extrinsic convention")

    out_verts = verts[mask]
    el = PlyElement.describe(out_verts, "vertex")
    PlyData([el], text=False).write(args.out)
    print(f"[crop] wrote {args.out}")


if __name__ == "__main__":
    main()
