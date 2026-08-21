"""donor_corpus.py -- one command per donor: splat -> shells -> whole-genome.

For TEXTURE corpus purposes a donor does not need chalk sectioning: the fur
is found by chroma clustering afterward (train_material --clusters). This
runs shell_fit, fabricates a single-region labels file (every kept splat is
region 0), and extracts the genome, leaving a donor ready for clustering
and patch cutting.

  .venv-gs/Scripts/python.exe tools/donor_corpus.py --splat models/co3d/co3d_187.splat \
      --name bear187
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
PY = sys.executable


def run(*args: str) -> None:
    r = subprocess.run([str(PY), *args], cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(args)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--splat", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--outdir", default=str(ROOT / "models/co3d/donors"))
    a = ap.parse_args()

    out = Path(a.outdir) / a.name
    out.mkdir(parents=True, exist_ok=True)
    shells = out / "shells.npz"

    import cpp_bridge as cb
    buf = cb.load_splat(a.splat).astype(np.float64)
    if buf.shape[1] != 14:
        raise SystemExit(f"REFUSED: {a.splat} has {buf.shape[1]} columns, not 14 "
                         f"(mandatory 14-variable gate)")
    sc = buf[:, 7:10]
    if (np.abs(sc[:, 0] - sc[:, 1]) < 1e-9).all() and (np.abs(sc[:, 1] - sc[:, 2]) < 1e-9).all():
        raise SystemExit(f"REFUSED: {a.splat} is isotropic -- not a 14-variable sample")

    run(str(ROOT / "tools/shell_fit.py"), a.splat, "--out", str(shells))

    buf = buf[buf[:, 6] >= 0.5]
    from scipy.spatial import cKDTree
    sh = np.load(shells)
    keep = cKDTree(sh["outer"]).query(buf[:, 0:3])[0] <= 0.04
    buf = buf[keep]
    labels = {"regions": ["all"], "hierarchy": {}, "shells": str(shells),
              "denoise": 0.04, "splat_labels": [0] * len(buf)}
    lpath = out / "labels.json"
    lpath.write_text(json.dumps(labels))

    run(str(ROOT / "tools/extract_genomes.py"), "--splat", a.splat,
        "--shells", str(shells), "--labels", str(lpath),
        "--outdir", str(out / "genomes"))
    print(f"\ndonor {a.name}: {len(buf)} splats -> {out}/genomes/all.npz")
    print(f"next: tools/train_material.py --genome {out}/genomes/all.npz "
          f"--clusters 10 --outdir {out}/materials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
