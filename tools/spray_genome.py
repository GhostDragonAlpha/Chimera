"""spray_genome.py -- grow a bear from genomes: the reconstruction test.

For every inner-core point carrying region label L, splats from region L's
genome are re-emitted in that core point's LOCAL FRAME (height along the
outward normal, lateral offset in the tangent plane, rotation re-based from
the genome's local frame). Genome entries are DEALT to the region's core
points (shuffled, each entry used once): the donor's exact splat->core-point
mapping is destroyed, so this is NOT replay -- it tests whether the labeled
frames + population statistics alone regenerate the object.

Falsifier (THE_SECTIONING_METHOD gate): render the sprayed result next to the
donor; if it does not read as the same object, the genome/frame machinery is
wrong -- stop and fix before any novel body.

Usage:
  .venv-gs/Scripts/python.exe tools/spray_genome.py --shells models/co3d/bear34_shells.npz \
      --labels models/co3d/bear34_labels.json --genomes models/co3d/genomes \
      --out models/co3d/bear34_sprayed.splat [--seed 0]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402
from extract_genomes import core_frames, frame_quat, quat_mul  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--shells", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--genomes", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--deal", choices=["random", "nearest"], default="random",
                    help="random = destroy mapping (level-1 machinery test); "
                         "nearest = each genome entry goes to the target core point "
                         "nearest its donor position (level-2: does the relative "
                         "encoding preserve fine arrangement?)")
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    lab = json.loads(Path(a.labels).read_text())
    names = lab["regions"]
    core_lab = np.array(lab["core_labels"])
    shells = np.load(a.shells)
    inner = shells["inner"].astype(np.float64)
    normals, frames = core_frames(shells)
    fq = frame_quat(frames)

    out = []
    for i, name in enumerate(names):
        gp = Path(a.genomes) / f"{name}.npz"
        if not gp.exists():
            continue
        g = np.load(gp)
        n_g = len(g["h"])
        tgt = np.where(core_lab == i)[0]
        if len(tgt) == 0:
            print(f"{name}: NO core points -- skipped")
            continue
        # deal genome entries to core points of this region
        if a.deal == "nearest":
            from scipy.spatial import cKDTree
            src = inner[g["core_idx"]]
            tgt_pick = tgt[cKDTree(inner[tgt]).query(src)[1]]
        else:
            tgt_pick = tgt[rng.integers(0, len(tgt), n_g)]
        fr = frames[tgt_pick]
        pos = (inner[tgt_pick]
               + g["h"][:, None] * fr[:, :, 2]
               + g["u"][:, None] * fr[:, :, 0]
               + g["v"][:, None] * fr[:, :, 1])
        q = quat_mul(fq[tgt_pick], g["q_local"])
        q /= np.linalg.norm(q, axis=1, keepdims=True)
        n_out = len(pos)
        buf = np.zeros((n_out, 14), dtype=np.float32)
        buf[:, 0:3] = pos
        buf[:, 3:6] = g["rgb"]
        buf[:, 6] = g["alpha"]
        buf[:, 7:10] = g["scale"]
        buf[:, 10:14] = q
        out.append(buf)
        print(f"{name}: {n_g} splats onto {len(tgt)} core points")

    allb = np.concatenate(out)
    cb.save_splat(a.out, allb)
    print(f"sprayed {len(allb)} splats -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
