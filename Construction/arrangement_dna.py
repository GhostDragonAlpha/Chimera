"""arrangement_dna — measure HOW PIECES SIT from a real scan.

The other half of making form trainable. core/trainables/arrangement.py can emit any
arrangement and report facts about it, but a domain without a target trains against
nothing. This measures the SAME facts from real material, so an emitted arrangement and a
photographed one are compared on identical numbers.

That identity is the whole point, and it is the same discipline that made material
composition honest: when the composition trainer scored candidates by keyword-matching
English answers it was grading an adjective; when it scored them against a measured
splat-configuration distribution it started finding real material. Arrangement gets the
same treatment or it will drift into taste.

WHAT IS MEASURED (identical keys to the domain's _facts):
    aspect         vertical extent / horizontal extent
    verticality    how much the pieces' long axes point up
    alignment      how parallel neighbouring pieces are to the local mean
    clustering     nearest-neighbour spacing vs uniform scattering (Clark-Evans)
    ground_contact fraction of mass in the lowest slice
    hollowness     fraction of mass out near the shell
    spread_ratio   the inverse of aspect, kept because objectives read more clearly with it

A splat's DIRECTION is its longest principal axis -- the eigenvector of its covariance
with the largest eigenvalue. That is the same quantity the material genome calls
anisotropy, seen as a vector rather than a ratio.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Construction.ksplat_io import load_any  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / 'Chimera/docs/matter/arrangement_targets.json'


def directions_from_scales(scale: np.ndarray, quat: np.ndarray) -> np.ndarray:
    """Each splat's long axis in world space, from its scale and rotation."""
    s = np.asarray(scale, dtype=np.float64)
    q = np.asarray(quat, dtype=np.float64)
    q = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-12)
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - w * z); R[:, 0, 2] = 2 * (x * z + w * y)
    R[:, 1, 0] = 2 * (x * y + w * z); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - w * x)
    R[:, 2, 0] = 2 * (x * z - w * y); R[:, 2, 1] = 2 * (y * z + w * x); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    longest = np.argmax(s, axis=1)                      # which local axis is longest
    return np.take_along_axis(R, longest[:, None, None].repeat(3, 1), axis=2)[:, :, 0]


def arrangement_facts(pos: np.ndarray, dirs: np.ndarray, sample: int = 900,
                      seed: int = 0) -> dict:
    """The same statistics core/trainables/arrangement._facts reports. Identical keys."""
    rng = np.random.default_rng(seed)
    if len(pos) > sample:                                # the NN matrix is O(n^2)
        i = rng.choice(len(pos), sample, replace=False)
        pos, dirs = pos[i], dirs[i]

    ext = pos.max(0) - pos.min(0)
    ext_xy = float(max(ext[0], ext[1]))
    ext_z = float(ext[2])

    d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    nn = d.min(1)
    vol = max(ext_xy * ext_xy * max(ext_z, 1e-6), 1e-12)
    uniform_nn = 0.554 * (vol / len(pos)) ** (1 / 3)

    centred = pos - pos.mean(0)
    radial = np.linalg.norm(centred, axis=1)
    mean_dir = dirs.mean(0)
    return {
        'aspect': float(ext_z / max(ext_xy, 1e-6)),
        'verticality': float(np.abs(dirs[:, 2]).mean()),
        'alignment': float(np.abs(dirs @ mean_dir / (np.linalg.norm(mean_dir) + 1e-9)).mean()),
        'clustering': float(uniform_nn / max(nn.mean(), 1e-9)),
        'ground_contact': float((pos[:, 2] < pos[:, 2].min() + 0.12 * max(ext_z, 1e-6)).mean()),
        'hollowness': float((radial > 0.6 * radial.max()).mean()),
        'spread_ratio': float(ext_xy / max(ext_z, 1e-6)),
        'n_splats': int(len(pos)),
    }


def measure_scan(path: str, k: int = 6, sample: int = 900, seed: int = 0) -> dict:
    """Split a scan into spatial regions and report each region's arrangement.

    Regions, not the whole scan: arrangement is a LOCAL property. The statistics of a
    whole hillside are not the statistics of the grass on it, and training against the
    average of everything would produce matter that resembles nothing.
    """
    pos, rgb, opac, scale, quat = load_any(path, full=True)
    rng = np.random.default_rng(seed)

    solid = np.where(opac > 0.5)[0]
    if len(solid) == 0:
        solid = np.arange(len(opac))
    idx = rng.choice(solid, min(120_000, len(solid)), replace=False)
    P, S, Q = pos[idx], scale[idx], quat[idx]
    D = directions_from_scales(S, Q)

    Z = (P - P.mean(0)) / (P.std(0) + 1e-9)              # spatial k-means
    C = Z[rng.choice(len(Z), k, replace=False)].copy()
    for _ in range(25):
        lab = ((Z[:, None, :] - C[None, :, :]) ** 2).sum(2).argmin(1)
        for j in range(k):
            m = lab == j
            if m.any():
                C[j] = Z[m].mean(0)

    out = {}
    for j in range(k):
        m = lab == j
        if m.sum() < 200:
            continue
        out[f'region_{j:02d}'] = arrangement_facts(P[m], D[m], sample, seed)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scan')
    ap.add_argument('--name', default='', help='label these targets, e.g. stump')
    ap.add_argument('--regions', type=int, default=6)
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()

    print(f'reading {a.scan}')
    regions = measure_scan(a.scan, k=a.regions)
    label = a.name or Path(a.scan).stem

    print(f'\n{"region":12}{"aspect":>9}{"vert":>8}{"align":>8}{"cluster":>9}'
          f'{"hollow":>8}{"splats":>9}')
    for name, f in regions.items():
        print(f'  {name:10}{f["aspect"]:>9.3f}{f["verticality"]:>8.3f}{f["alignment"]:>8.3f}'
              f'{f["clustering"]:>9.3f}{f["hollowness"]:>8.3f}{f["n_splats"]:>9}')

    out = Path(a.out)
    payload = json.loads(out.read_text()) if out.exists() else {'targets': {}}
    payload.setdefault('targets', {})[label] = regions
    payload['_provenance'] = 'MEASURED arrangement statistics from real scans'
    payload['_note'] = ('Identical keys to core/trainables/arrangement._facts, so an '
                        'emitted arrangement and a photographed one are compared on the '
                        'same numbers. Regions are local because arrangement is local.')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    print(f'\nwrote {out}')


if __name__ == '__main__':
    main()
